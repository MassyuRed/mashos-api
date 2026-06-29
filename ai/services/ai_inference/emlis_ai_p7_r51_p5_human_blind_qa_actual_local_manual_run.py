# -*- coding: utf-8 -*-
"""P7-R51 P5 Human Blind QA actual local-only manual-run helpers.

R51-0 refreezes the current local source and the completed R50 handoff before
any actual local-only human review work is allowed to proceed.

R51-1 freezes validation evidence and the R49 wildcard-timeout handling rule.
It accepts R49 only as split-matrix green evidence, keeps the wildcard timeout
visible as unclassified evidence uncertainty, and forbids claiming wildcard
bulk green.

This module intentionally implements R51-0 through R51-20.  R51-2
freezes local root / explicit allow / purge-plan preflight, R51-3 creates a
body-free actual review session envelope, R51-4 freezes the inherited 24-case
manifest, R51-5 creates only a body-free local-only body-full packet generation
request, R51-6 checks body-free packet-completeness/export-denylist evidence,
R51-7 freezes the reviewer instruction/rating form, R51-8 captures sanitized
actual human review selections, R51-9 normalizes body-free rating rows, R51-10
separates readfeel blockers from execution blockers, R51-11 normalizes
body-free question-need observation rows, R51-12 guards rating/question
consistency so P5 weakness cannot be hidden by question candidates, and R51-13
freezes pause / abort / expiration protocol.  R51-14 captures body-free purge
verification for local-only body-full packets / reviewer forms / reviewer notes,
R51-15 builds/verifies a body-free disposal receipt, R51-16 builds the body-free
post-review summary, R51-17 separates P5 confirmed candidate / repair return
/ inconclusive, R51-18 creates the P6 limited human readfeel candidate handoff,
and R51-19 creates the P8 question design material candidate handoff.  R51-20
validates the final body-free/no-question-text/no-touch boundary before any
post-R51 decision material is consumed.  It does
not write body-full packets, persist reviewer notes,
expose paths or hashes, create schema files, change API/DB/RN contracts, start
P8, complete P7, or claim release readiness.
"""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import (
    P7_GIT_CHECKED,
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
from emlis_ai_p7_r47_local_review_packet_policy import (
    P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS,
    P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
    P7_R47_EXPORT_DENYLIST_PATTERNS,
    P7_R47_EXPORT_DENYLIST_POLICY_SCHEMA_VERSION,
    P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR,
    P7_R47_LOCAL_REVIEW_STORAGE_ROOT_POLICY_SCHEMA_VERSION,
    P7_R47_P5_FIRST_FORMAL_MINIMUMS,
    P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
    P7_R47_STORAGE_ROOT_REF,
    assert_p7_r47_export_denylist_policy_contract,
    assert_p7_r47_local_review_storage_root_policy_contract,
    build_p7_r47_export_denylist_policy,
    build_p7_r47_local_review_storage_root_policy,
    p7_r47_export_candidate_deny_reasons,
)
from emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet import (
    P7_R48_P5_BOUNDARY_FAMILY_REFS,
    P7_R48_P5_CASE_ROLE_REFS,
    P7_R48_P5_BLOCKER_KINDS,
    P7_R48_P5_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
    P7_R48_P5_BLOCKER_STATUSES,
    P7_R48_P5_CASE_MATRIX_ROW_FIELD_REFS,
    P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION,
    P7_R48_P5_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
    P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION,
    P7_R48_P5_POSITIVE_CASE_ROLE_REFS,
    P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION,
    P7_R48_P5_REVIEWABLE_VERDICTS,
    P7_R48_READFEEL_BLOCKER_ID_REFS,
    P7_R48_SANITIZED_REASON_ID_REFS,
    assert_p7_r48_p5_first_formal_review_case_matrix_contract,
    build_p7_r48_p5_first_formal_review_case_matrix,
)
from emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution import (
    P7_R49_RN_CONTRACT_OPTIONAL_NO_TOUCH_TEST_REFS,
    P7_R49_VALIDATION_DISPLAY_API_TEST_FILE_REFS,
    P7_R49_VALIDATION_P5_CORE_TEST_FILE_REFS,
    P7_R49_VALIDATION_R46_HANDOFF_TEST_FILE_REFS,
    P7_R49_VALIDATION_R47_REGRESSION_TEST_FILE_REFS,
    P7_R49_VALIDATION_R48_REGRESSION_TEST_FILE_REFS,
    P7_R49_VALIDATION_R49_TARGET_TEST_FILE_REFS,
)
from emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision import (
    P5_HUMAN_BLIND_QA_RATING_AXES,
    P5_HUMAN_BLIND_QA_TARGETS,
    P7_R50_AMBIGUITY_KIND_REFS,
    P7_R50_ONE_QUESTION_FIT_REFS,
    P7_R50_EXPLICIT_NO_TOUCH_AREA_REFS,
    P7_R50_EXPLICIT_NO_TOUCH_FILE_REFS,
    P7_R50_PACKET_KIND,
    P7_R50_PLAN_CANDIDATE_FLAG_REFS,
    P7_R50_QUESTION_NEED_OBSERVATION_STAGE_REF,
    P7_R50_QUESTION_NEED_PRIMARY_CLASS_REFS,
    P7_R50_RATING_CAPTURE_ROW_BODYFREE_REQUIRED_FIELD_REFS,
    P7_R50_RATING_FORM_VERSION,
    P7_R50_RATING_VERDICT_REFS,
    P7_R50_REPAIR_REQUIRED_REF_REFS,
    P7_R50_REQUIRED_CASE_COUNT,
    P7_R50_REQUIRED_REVIEWER_CHECK_LABEL_REFS,
    P7_R50_REVIEWER_CHECK_ITEM_REFS,
    P7_R50_REVIEWER_HIDDEN_FIELD_REFS,
    P7_R50_REVIEWER_INSTRUCTION_VERSION,
    P7_R50_REVIEWER_VISIBLE_FIELD_REFS,
    P7_R50_REVIEW_KIND,
    P7_R50_R20_IMPLEMENTED_STEPS,
    P7_R50_R20_NEXT_REQUIRED_STEP_REF,
    P7_R50_R20_NOT_YET_IMPLEMENTED_STEPS,
    P7_R50_SCOPE,
    P7_R50_STEP,
    P7_R50_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION,
    P7_R50_VALIDATION_R50_TARGET_TEST_FILE_REFS,
    assert_p7_r50_touch_candidate_no_touch_boundary_freeze_contract,
    build_p7_r50_touch_candidate_no_touch_boundary_freeze,
)

P7_R51_CURRENT_SOURCE_R50_HANDOFF_REFREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r51.current_source_r50_handoff_refreeze.bodyfree.v1"
)
P7_R51_VALIDATION_EVIDENCE_R49_TIMEOUT_HANDLING_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r51.validation_evidence_r49_timeout_handling_freeze.bodyfree.v1"
)

P7_R51_LOCAL_ROOT_EXPLICIT_ALLOW_PURGE_PLAN_PREFLIGHT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r51.local_root_explicit_allow_purge_plan_preflight.bodyfree.v1"
)
P7_R51_ACTUAL_REVIEW_SESSION_ENVELOPE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r51.actual_review_session_envelope.bodyfree.v1"
)
P7_R51_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r51.24_case_manifest_freeze.bodyfree.v1"
)
P7_R51_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r51.local_only_body_full_packet_generation_request.bodyfree.v1"
)
P7_R51_BODY_FULL_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r51.body_full_reviewer_packet.local_only.v1"
)
P7_R51_BODY_FULL_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r51.body_full_packet_completeness_export_denylist_scan.bodyfree.v1"
)
P7_R51_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r51.reviewer_instruction_rating_form_freeze.bodyfree.v1"
)
P7_R51_ACTUAL_HUMAN_REVIEW_RUN_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r51.actual_human_review_run.bodyfree.v1"
)
P7_R51_RATING_ROW_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r51.rating_row.bodyfree.v1"
)
P7_R51_RATING_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r51.rating_row_normalizer.bodyfree.v1"
)
P7_R51_READFEEL_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r51.readfeel_blocker_row.bodyfree.v1"
)
P7_R51_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r51.execution_blocker_row.bodyfree.v1"
)
P7_R51_READFEEL_EXECUTION_BLOCKER_INGESTION_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r51.readfeel_execution_blocker_ingestion.bodyfree.v1"
)
P7_R51_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r51.question_need_observation_row.bodyfree.v1"
)
P7_R51_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r51.question_need_observation_row_normalizer.bodyfree.v1"
)
P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r51.rating_question_observation_consistency_guard.bodyfree.v1"
)
P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_ROW_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r51.rating_question_observation_consistency_issue_row.bodyfree.v1"
)
P7_R51_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r51.pause_abort_expiration_protocol.bodyfree.v1"
)
P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_BODYFREE_SCHEMA_VERSION: Final = (
    P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_SCHEMA_VERSION
)
P7_R51_PAUSE_ABORT_EXPIRATION_PROTOCOL_BODYFREE_SCHEMA_VERSION: Final = (
    P7_R51_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION
)
P7_R51_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r51.body_full_packet_reviewer_notes_purge.bodyfree.v1"
)
P7_R51_PURGE_EVIDENCE_ROW_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r51.purge_evidence_row.bodyfree.v1"
)
P7_R51_DISPOSAL_RECEIPT_BUILDER_VERIFIER_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r51.disposal_receipt_builder_verifier.bodyfree.v1"
)
P7_R51_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r51.disposal_receipt.bodyfree.v1"
)

P7_R51_STEP: Final = "R51_P5HumanBlindQAActualLocalOnlyManualRun_20260620"
P7_R51_SCOPE: Final = "p5_human_blind_qa_actual_local_only_manual_run"
P7_R51_POLICY_KIND: Final = "p5_human_blind_qa_actual_local_only_manual_run_policy"
P7_R51_PACKET_KIND: Final = P7_R50_PACKET_KIND
P7_R51_REVIEW_KIND: Final = P7_R50_REVIEW_KIND
P7_R51_REQUIRED_CASE_COUNT: Final = P7_R50_REQUIRED_CASE_COUNT
P7_R51_DEFAULT_REVIEW_SESSION_ID: Final = "p7_r51_p5_human_blind_qa_actual_local_manual_run_session"
P7_R51_FIRST_NEXT_WORK_REF: Final = "p5_human_blind_qa_actual_local_only_manual_run"

P7_R51_R0_NEXT_REQUIRED_STEP_REF: Final = "R51-1_validation_evidence_r49_timeout_handling_freeze"
P7_R51_R1_NEXT_REQUIRED_STEP_REF: Final = "R51-2_local_root_explicit_allow_purge_plan_preflight"
P7_R51_R1_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R51-1_validation_evidence_before_R51-2_preflight"

P7_R51_R2_NEXT_REQUIRED_STEP_REF: Final = "R51-3_actual_review_session_envelope"
P7_R51_R2_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R51-2_local_root_explicit_allow_purge_plan_preflight"
P7_R51_R3_NEXT_REQUIRED_STEP_REF: Final = "R51-4_24_case_manifest_freeze"
P7_R51_R3_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R51-2_preflight_before_R51-3_envelope"
P7_R51_R4_NEXT_REQUIRED_STEP_REF: Final = "R51-5_local_only_body_full_packet_generation_request"
P7_R51_R4_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R51-3_envelope_before_R51-4_manifest_freeze"
P7_R51_R5_NEXT_REQUIRED_STEP_REF: Final = "R51-6_body_full_packet_completeness_export_denylist_scan"
P7_R51_R5_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R51-4_manifest_before_R51-5_packet_generation_request"
P7_R51_R6_NEXT_REQUIRED_STEP_REF: Final = "R51-7_reviewer_instruction_rating_form_freeze"
P7_R51_R6_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R51-5_packet_generation_request_or_local_packet_completion_before_R51-7"
P7_R51_R7_NEXT_REQUIRED_STEP_REF: Final = "R51-8_actual_human_review_run"
P7_R51_R7_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R51-6_packet_completeness_scan_before_R51-8_review"
P7_R51_R8_NEXT_REQUIRED_STEP_REF: Final = "R51-9_rating_row_normalization"
P7_R51_R8_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R51-7_reviewer_instruction_rating_form_before_R51-8_review"
P7_R51_R9_NEXT_REQUIRED_STEP_REF: Final = "R51-10_readfeel_blocker_execution_blocker_ingestion"
P7_R51_R9_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R51-8_actual_human_review_run_before_R51-9_rating_row_normalization"
P7_R51_R10_NEXT_REQUIRED_STEP_REF: Final = "R51-11_question_need_observation_row_normalization"
P7_R51_R10_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R51-9_rating_row_normalization_before_R51-10_blocker_ingestion"
P7_R51_R11_NEXT_REQUIRED_STEP_REF: Final = "R51-12_rating_question_observation_consistency_guard"
P7_R51_R11_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R51-10_blocker_ingestion_before_R51-11_question_observation_normalization"
P7_R51_R12_NEXT_REQUIRED_STEP_REF: Final = "R51-13_pause_abort_expiration_protocol"
P7_R51_R12_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R51-12_rating_question_observation_consistency_before_R51-13_pause_abort_expiration_protocol"
P7_R51_R13_NEXT_REQUIRED_STEP_REF: Final = "R51-14_body_full_packet_reviewer_notes_purge"
P7_R51_R13_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R51-12_consistency_guard_before_R51-13_pause_abort_expiration_protocol"
P7_R51_R13_PAUSED_NEXT_REQUIRED_STEP_REF: Final = "resume_or_abort_paused_R51-13_local_review_before_retention_deadline"
P7_R51_R14_NEXT_REQUIRED_STEP_REF: Final = "R51-15_disposal_receipt_builder_verifier"
P7_R51_R14_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R51-14_body_full_packet_reviewer_notes_purge_before_R51-15_receipt"
P7_R51_R14_PAUSED_OR_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R51-13_pause_abort_expiration_before_R51-14_purge"
P7_R51_R15_NEXT_REQUIRED_STEP_REF: Final = "R51-16_body_free_post_review_summary_builder"
P7_R51_R15_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R51-15_disposal_receipt_verification_before_R51-16_summary"

P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_ENV_VAR: Final = (
    "COCOLON_EMLIS_P7_R51_ALLOW_ACTUAL_LOCAL_MANUAL_RUN"
)
P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_TOKEN_REF: Final = (
    "LOCAL_ONLY_ACTUAL_REVIEW_CONFIRMED"
)
P7_R51_REVIEW_PROMPT_VERSION: Final = "p7_r51_p5_human_blind_qa_actual_review_prompt_v1"
P7_R51_R50_HANDOFF_REF: Final = (
    "P7_R50_R20_boundary_next_required_step_P5_human_blind_qa_actual_review_local_only_manual_run_after_R50_boundary_freeze"
)
P7_R51_DEFAULT_REVIEWER_REF: Final = "pseudonymous_reviewer_r51_local_manual_run"

P7_R51_SOURCE_SNAPSHOT_REFS: Final[dict[str, str]] = {
    "premise_zip_ref": "Cocolon_前提資料(241).zip",
    "implemented_materials_zip_ref": "EmlisAIの実装済み資料(73).zip",
    "rn_zip_ref": "Cocolon(246).zip",
    "backend_zip_ref": "mashos-api(159).zip",
    "roadmap_ref": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619(3).md",
    "pre_design_memo_ref": "Cocolon_EmlisAI_P7_R51_P5HumanBlindQA_LocalOnlyManualRun_PreDesignMemo_20260620.md",
    "detailed_design_ref": "Cocolon_EmlisAI_P7_R51_P5HumanBlindQA_LocalOnlyManualRun_DetailedDesign_ImplementationOrder_20260620.md",
}

P7_R51_R0_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R51-0_current_source_r50_handoff_refreeze",
)
P7_R51_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R51_R0_IMPLEMENTED_STEPS,
    "R51-1_validation_evidence_r49_timeout_handling_freeze",
)
P7_R51_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R51-2_local_root_explicit_allow_purge_plan_preflight",
    "R51-3_actual_review_session_envelope",
    "R51-4_24_case_manifest_freeze",
    "R51-5_local_only_body_full_packet_generation_request",
    "R51-6_body_full_packet_completeness_export_denylist_scan",
    "R51-7_reviewer_instruction_rating_form_freeze",
    "R51-8_actual_human_review_run",
    "R51-9_rating_row_normalization",
    "R51-10_readfeel_blocker_execution_blocker_ingestion",
    "R51-11_question_need_observation_row_normalization",
    "R51-12_rating_question_observation_consistency_guard",
    "R51-13_pause_abort_expiration_protocol",
    "R51-14_body_full_packet_reviewer_notes_purge",
    "R51-15_disposal_receipt_builder_verifier",
    "R51-16_body_free_post_review_summary_builder",
    "R51-17_p5_confirmed_repair_return_inconclusive_decision",
    "R51-18_p6_limited_human_readfeel_candidate_handoff",
    "R51-19_p8_question_design_material_candidate_handoff",
    "R51-20_no_body_leak_no_question_text_no_touch_validation",
)
P7_R51_R0_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R51-1_validation_evidence_r49_timeout_handling_freeze",
    *P7_R51_NOT_YET_IMPLEMENTED_STEPS,
)

P7_R51_R2_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R51_IMPLEMENTED_STEPS,
    "R51-2_local_root_explicit_allow_purge_plan_preflight",
)
P7_R51_R2_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R51-3_actual_review_session_envelope",
    "R51-4_24_case_manifest_freeze",
    "R51-5_local_only_body_full_packet_generation_request",
    "R51-6_body_full_packet_completeness_export_denylist_scan",
    "R51-7_reviewer_instruction_rating_form_freeze",
    "R51-8_actual_human_review_run",
    "R51-9_rating_row_normalization",
    "R51-10_readfeel_blocker_execution_blocker_ingestion",
    "R51-11_question_need_observation_row_normalization",
    "R51-12_rating_question_observation_consistency_guard",
    "R51-13_pause_abort_expiration_protocol",
    "R51-14_body_full_packet_reviewer_notes_purge",
    "R51-15_disposal_receipt_builder_verifier",
    "R51-16_body_free_post_review_summary_builder",
    "R51-17_p5_confirmed_repair_return_inconclusive_decision",
    "R51-18_p6_limited_human_readfeel_candidate_handoff",
    "R51-19_p8_question_design_material_candidate_handoff",
    "R51-20_no_body_leak_no_question_text_no_touch_validation",
)
P7_R51_R3_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R51_R2_IMPLEMENTED_STEPS,
    "R51-3_actual_review_session_envelope",
)
P7_R51_R3_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R51_R2_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R51_R4_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R51_R3_IMPLEMENTED_STEPS,
    "R51-4_24_case_manifest_freeze",
)
P7_R51_R4_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R51_R3_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R51_R5_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R51_R4_IMPLEMENTED_STEPS,
    "R51-5_local_only_body_full_packet_generation_request",
)
P7_R51_R5_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R51_R4_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R51_R6_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R51_R5_IMPLEMENTED_STEPS,
    "R51-6_body_full_packet_completeness_export_denylist_scan",
)
P7_R51_R6_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R51_R5_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R51_R7_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R51_R6_IMPLEMENTED_STEPS,
    "R51-7_reviewer_instruction_rating_form_freeze",
)
P7_R51_R7_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R51_R6_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R51_R8_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R51_R7_IMPLEMENTED_STEPS,
    "R51-8_actual_human_review_run",
)
P7_R51_R8_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R51_R7_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R51_R9_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R51_R8_IMPLEMENTED_STEPS,
    "R51-9_rating_row_normalization",
)
P7_R51_R9_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R51_R8_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R51_R10_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R51_R9_IMPLEMENTED_STEPS,
    "R51-10_readfeel_blocker_execution_blocker_ingestion",
)
P7_R51_R10_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R51_R9_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R51_R11_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R51_R10_IMPLEMENTED_STEPS,
    "R51-11_question_need_observation_row_normalization",
)
P7_R51_R11_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R51_R10_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R51_R12_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R51_R11_IMPLEMENTED_STEPS,
    "R51-12_rating_question_observation_consistency_guard",
)
P7_R51_R12_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R51_R11_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R51_R13_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R51_R12_IMPLEMENTED_STEPS,
    "R51-13_pause_abort_expiration_protocol",
)
P7_R51_R13_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R51_R12_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R51_R14_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R51_R13_IMPLEMENTED_STEPS,
    "R51-14_body_full_packet_reviewer_notes_purge",
)
P7_R51_R14_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R51_R13_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R51_R15_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R51_R14_IMPLEMENTED_STEPS,
    "R51-15_disposal_receipt_builder_verifier",
)
P7_R51_R15_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R51_R14_NOT_YET_IMPLEMENTED_STEPS[1:]

P7_R51_QUESTION_IMPLEMENTATION_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    "question_api_implemented",
    "question_db_schema_implemented",
    "question_rn_ui_implemented",
    "question_response_key_implemented",
    "question_trigger_logic_implemented",
    "question_storage_schema_implemented",
    "question_answer_persistence_implemented",
    "question_plan_guard_implemented",
    "p8_implementation_spec_finalized_here",
)
P7_R51_REVIEW_RELEASE_CLOSED_KEY_REFS: Final[tuple[str, ...]] = (
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "actual_body_full_packet_generated_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "body_full_writer_created_here",
    "local_reviewer_payload_materialized_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_question_need_observation_summary_materialized_here",
    "actual_reviewer_notes_materialized_here",
    "actual_disposal_run_here",
    "actual_disposal_receipt_materialized_here",
    "post_review_summary_materialized_here",
    "p5_human_blind_qa_confirmed",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_repair_return_candidate",
    "p5_review_inconclusive",
    "p6_limited_human_readfeel_start_allowed",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p8_question_design_material_candidate",
    "p7_complete",
    "p8_start_allowed",
    "release_allowed",
    "hold004_close_allowed",
    "full_backend_suite_green_confirmed",
    "release_readiness_claim_allowed",
    "p7_completion_claim_allowed",
    "p8_start_claim_allowed",
)
P7_R51_SCHEMA_MATERIALIZATION_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    "json_schema_file_created_here",
    "schema_files_materialized_here",
    "api_db_rn_response_key_changed_here",
    "runtime_changed_here",
    "api_route_changed_here",
    "db_schema_changed_here",
    "db_migration_changed_here",
    "rn_visible_contract_changed_here",
    "public_response_top_level_key_added_here",
)
P7_R51_R0_R1_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    *P7_R51_QUESTION_IMPLEMENTATION_FALSE_KEY_REFS,
    *P7_R51_REVIEW_RELEASE_CLOSED_KEY_REFS,
    *P7_R51_SCHEMA_MATERIALIZATION_FALSE_KEY_REFS,
)
P7_R51_ACTUAL_REVIEW_RESULT_INPUT_FORBIDDEN_KEY_REFS: Final[tuple[str, ...]] = (
    "raw_input",
    "raw_answer",
    "comment_text",
    "comment_text_body",
    "returned_emlis_surface",
    "bounded_owned_history_review_surface",
    "current_input_review_surface",
    "reviewer_free_text",
    "reviewer_note",
    "reviewer_notes",
    "question_text",
    "draft_question_text",
    "question_body",
    "local_absolute_path",
    "body_content_hash",
    "packet_content_hash",
    "terminal_output",
    "stdout",
    "stderr",
    "traceback",
)

P7_R51_EXECUTION_BLOCKER_ID_REFS: Final[tuple[str, ...]] = (
    "r51_missing_r50_handoff",
    "r51_missing_r50_target_green_evidence",
    "r51_missing_r49_split_green_evidence",
    "r51_r49_wildcard_timeout_unclassified",
    "r51_missing_r48_regression_green_evidence",
    "r51_missing_r47_regression_green_evidence",
    "r51_missing_r46_display_p5_core_green_evidence",
    "r51_missing_rn_contract_green_evidence",
    "r51_missing_backend_collect_only_evidence",
    "r51_validation_evidence_not_ready",
    "r51_local_review_root_missing",
    "r51_local_review_root_invalid",
    "r51_explicit_allow_missing",
    "r51_disposal_plan_missing",
    "r51_body_full_packet_export_violation",
    "r51_case_material_missing",
    "r51_case_manifest_incomplete",
    "r51_blind_case_id_case_ref_boundary_violation",
    "r51_reviewer_facing_manifest_leak_detected",
    "r51_body_full_packet_generation_request_blocked",
    "r51_body_full_packet_generation_failed",
    "r51_rating_rows_incomplete",
    "r51_question_need_observation_rows_incomplete",
    "r51_rating_question_observation_inconsistent",
    "r51_disposal_receipt_missing",
    "r51_disposal_failed",
    "r51_disposal_not_verified",
    "r51_scope_drift_detected",
    "r51_body_free_leak_detected",
)
P7_R51_EXECUTION_BLOCKER_STATUS_REFS: Final[tuple[str, ...]] = ("OPEN", "TRIAGED", "RESOLVED", "CLOSED")

P7_R51_VALIDATION_EVIDENCE_GROUP_REFS: Final[tuple[str, ...]] = (
    "r51_r0_current_source_r50_handoff",
    "r50_target",
    "r49_split_matrix",
    "r49_wildcard_bulk",
    "r48_regression",
    "r47_regression",
    "r46_display_p5_core_subset",
    "backend_collect_only",
    "rn_no_touch_optional",
)
P7_R51_VALIDATION_EVIDENCE_REQUIRED_GROUP_REFS: Final[tuple[str, ...]] = (
    "r51_r0_current_source_r50_handoff",
    "r50_target",
    "r49_split_matrix",
    "r48_regression",
    "r47_regression",
    "r46_display_p5_core_subset",
    "backend_collect_only",
    "rn_no_touch_optional",
)
P7_R51_R49_WILDCARD_BULK_TEST_FILE_REFS: Final[tuple[str, ...]] = (
    "tests/test_emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution_*.py",
)

P7_R51_CURRENT_SOURCE_R50_HANDOFF_REFREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "source_snapshot_refs",
    "review_session_id",
    "required_case_count",
    "r50_handoff",
    "p7_p8_bridge_rule",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r50_handoff_refrozen",
    "r1_validation_evidence_r49_timeout_handling_frozen",
    "p5_actual_review_still_not_run",
    "local_root_preflight_required_later",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r51_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R51_R0_R1_FALSE_KEY_REFS,
)
P7_R51_R50_HANDOFF_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "r50_handoff_required",
    "r50_step",
    "r50_scope",
    "r50_schema_version",
    "r50_review_kind",
    "r50_packet_kind",
    "r50_required_case_count",
    "r50_completed_steps",
    "r50_not_yet_implemented_steps",
    "r50_next_required_step",
    "r50_touch_boundary_status",
    "r50_validation_matrix_status",
    "r50_boundary_freeze_ready",
    "r50_manual_run_boundary_finished",
    "r50_actual_review_completed",
    "r50_actual_human_review_run",
    "r50_body_full_packet_generated",
    "r50_rating_rows_materialized",
    "r50_question_need_observation_rows_materialized",
    "r50_disposal_receipt_materialized",
    "r50_p5_human_blind_qa_confirmed",
    "r50_p5_human_blind_qa_confirmed_candidate",
    "r50_p6_limited_human_readfeel_start_allowed",
    "r50_p8_start_allowed",
    "r50_release_allowed",
)
P7_R51_BRIDGE_RULE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "p7_bridge_only",
    "r51_is_p5_actual_local_only_manual_run",
    "r51_r0_r1_are_pre_review_freezes_only",
    "question_need_observation_memo_only",
    "question_need_observation_body_free_required",
    "p8_design_material_candidate_allowed_later",
    "p8_detail_design_allowed_here",
    "question_api_implemented",
    "question_db_schema_implemented",
    "question_rn_ui_implemented",
    "question_response_key_implemented",
    "question_trigger_logic_implemented",
    "raw_input_or_comment_text_allowed_in_bridge_material",
    "returned_surface_allowed_in_bridge_material",
    "reviewer_free_text_allowed_in_bridge_material",
    "question_text_allowed_in_bridge_material",
    "p7_completion_condition_relaxed",
    "p8_start_allowed",
    "release_allowed",
)
P7_R51_VALIDATION_EVIDENCE_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "evidence_group_ref",
    "evidence_status_ref",
    "evidence_present",
    "passed_count",
    "collected_count",
    "warning_count",
    "timeout_unclassified",
    "required_for_r51_2_preflight",
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
P7_R51_VALIDATION_EVIDENCE_R49_TIMEOUT_HANDLING_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "required_case_count",
    "r0_refreeze_schema_version",
    "r0_refreeze_material_ref",
    "validation_evidence_group_refs",
    "validation_evidence_rows",
    "validation_evidence_row_count",
    "validation_evidence_required_group_refs",
    "validation_evidence_required_groups_present",
    "r50_target_green_evidence_present",
    "r49_split_matrix_green_evidence_present",
    "r49_split_matrix_green_required_for_r51",
    "r49_split_matrix_green_required_for_r51_2_preflight",
    "r49_wildcard_bulk_timeout_unclassified",
    "r49_wildcard_green_claim_allowed",
    "r49_wildcard_green_claimed",
    "r49_wildcard_bulk_required_for_r51_2_preflight",
    "r49_timeout_handling_claim_boundary_ref",
    "r48_regression_green_evidence_present",
    "r47_regression_green_evidence_present",
    "r46_display_p5_core_green_evidence_present",
    "rn_contract_green_evidence_present",
    "backend_collect_only_evidence_present",
    "full_backend_suite_green_confirmed",
    "collect_only_claimed_as_full_backend_green",
    "rn_contract_claimed_as_real_device_modal_readfeel",
    "validation_commands_executed_here",
    "command_result_body_stored_here",
    "terminal_output_stored_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "r0_current_source_r50_handoff_refrozen",
    "r1_validation_evidence_r49_timeout_handling_frozen",
    "validation_evidence_ready_for_r51_2_preflight",
    "execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r51_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R51_R0_R1_FALSE_KEY_REFS,
)

P7_R51_PREFLIGHT_STATUS_REFS: Final[tuple[str, ...]] = ("PASSED", "BLOCKED")
P7_R51_REVIEW_SESSION_STATUS_REFS: Final[tuple[str, ...]] = (
    "PRECHECK_BLOCKED",
    "READY_FOR_ACTUAL_REVIEW_SESSION_ENVELOPE",
    "ACTUAL_REVIEW_SESSION_ENVELOPE_READY",
    "R51_24_CASE_MANIFEST_READY",
    "R51_BODY_FULL_PACKET_GENERATION_REQUEST_READY",
    "R51_BODY_FULL_PACKET_COMPLETENESS_SCAN_READY",
    "R51_REVIEWER_INSTRUCTION_RATING_FORM_READY",
    "R51_ACTUAL_HUMAN_REVIEW_RUN_CAPTURED_BODYFREE",
    "R51_RATING_ROWS_NORMALIZED_BODYFREE",
    "R51_READFEEL_EXECUTION_BLOCKERS_INGESTED_BODYFREE",
    "R51_QUESTION_NEED_OBSERVATION_ROWS_NORMALIZED_BODYFREE",
    "R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_READY",
    "R51_PAUSE_ABORT_EXPIRATION_PROTOCOL_READY",
    "R51_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE_VERIFIED_BODYFREE",
    "R51_DISPOSAL_RECEIPT_VERIFIED_BODYFREE",
)
P7_R51_MANIFEST_STATUS_REFS: Final[tuple[str, ...]] = (
    "READY_FOR_LOCAL_ONLY_PACKET_GENERATION_REQUEST",
    "BLOCKED_BY_R51_3_ENVELOPE",
    "BLOCKED_BY_CASE_MATRIX_CONTRACT",
)
P7_R51_PACKET_GENERATION_REQUEST_STATUS_REFS: Final[tuple[str, ...]] = (
    "READY_FOR_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION",
    "BLOCKED_BY_R51_4_MANIFEST",
)
P7_R51_PACKET_COMPLETENESS_SCAN_STATUS_REFS: Final[tuple[str, ...]] = (
    "READY_FOR_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE",
    "BLOCKED_BY_R51_5_GENERATION_REQUEST",
    "BLOCKED_BY_PACKET_COMPLETENESS_OR_EXPORT_DENYLIST",
)
P7_R51_PACKET_COMPLETION_SCAN_ROW_STATUS_REFS: Final[tuple[str, ...]] = (
    "PACKET_PRESENT_LOCAL_ONLY",
    "PACKET_MISSING",
    "PACKET_INCOMPLETE",
    "PACKET_EXPORT_DENYLIST_VIOLATION",
)
P7_R51_REVIEWER_INSTRUCTION_RATING_FORM_STATUS_REFS: Final[tuple[str, ...]] = (
    "READY_FOR_ACTUAL_HUMAN_REVIEW_RUN",
    "BLOCKED_BY_R51_6_PACKET_COMPLETENESS_SCAN",
)
P7_R51_ACTUAL_HUMAN_REVIEW_RUN_STATUS_REFS: Final[tuple[str, ...]] = (
    "READY_FOR_RATING_ROW_NORMALIZATION",
    "BLOCKED_BY_R51_7_REVIEWER_INSTRUCTION_RATING_FORM",
    "BLOCKED_BY_ACTUAL_REVIEW_RESULT_ROWS",
)
P7_R51_RATING_ROW_NORMALIZER_STATUS_REFS: Final[tuple[str, ...]] = (
    "READY_FOR_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION",
    "BLOCKED_BY_R51_8_ACTUAL_HUMAN_REVIEW_RUN",
    "BLOCKED_BY_RATING_ROW_VALIDATION",
)
P7_R51_READFEEL_EXECUTION_BLOCKER_INGESTION_STATUS_REFS: Final[tuple[str, ...]] = (
    "READY_FOR_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION",
    "BLOCKED_BY_R51_9_RATING_ROW_NORMALIZER",
)
P7_R51_QUESTION_OBSERVATION_NORMALIZER_STATUS_REFS: Final[tuple[str, ...]] = (
    "READY_FOR_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD",
    "BLOCKED_BY_R51_10_BLOCKER_INGESTION",
    "BLOCKED_BY_R51_8_ACTUAL_HUMAN_REVIEW_RUN",
    "BLOCKED_BY_QUESTION_OBSERVATION_ROW_VALIDATION",
)
P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_STATUS_REFS: Final[tuple[str, ...]] = (
    "READY_FOR_PAUSE_ABORT_EXPIRATION_PROTOCOL",
    "BLOCKED_BY_R51_9_RATING_ROW_NORMALIZER",
    "BLOCKED_BY_R51_10_BLOCKER_INGESTION",
    "BLOCKED_BY_R51_11_QUESTION_OBSERVATION_NORMALIZER",
    "BLOCKED_BY_RATING_QUESTION_OBSERVATION_INCONSISTENCY",
)
P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_ID_REFS: Final[tuple[str, ...]] = (
    "r51_pass_rating_with_not_question_repair",
    "r51_red_or_repair_required_routed_to_question_candidate",
    "r51_repair_required_not_question_without_repair_ref",
    "r51_insufficient_material_observation_without_execution_blocker",
    "r51_creepy_or_boundary_blocker_routed_to_question_candidate",
    "r51_current_input_overridden_by_history_routed_to_question_candidate",
    "r51_rating_question_case_set_mismatch",
    "r51_missing_rating_row_for_question_observation",
    "r51_missing_question_observation_row_for_rating",
)
P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_KIND_REFS: Final[tuple[str, ...]] = (
    "RATING_VERDICT",
    "REPAIR_REF",
    "BLOCKER_ESCAPE",
    "EXECUTION_BLOCKER_MATCH",
    "CASE_SET",
)
P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_SEVERITY_REFS: Final[tuple[str, ...]] = (
    "BLOCKING",
)
P7_R51_PAUSE_ABORT_EXPIRATION_ACTION_REFS: Final[tuple[str, ...]] = (
    "CONTINUE_TO_R51_14_PURGE",
    "PAUSE_LOCAL_ONLY_REVIEW",
    "ABORT_LOCAL_ONLY_REVIEW",
    "EXPIRE_LOCAL_ONLY_REVIEW",
)
P7_R51_REVIEW_LIFECYCLE_STATUS_REFS: Final[tuple[str, ...]] = (
    "REVIEW_COMPLETED",
    "REVIEW_PAUSED",
    "REVIEW_ABORTED",
    "REVIEW_EXPIRED",
)
P7_R51_PAUSE_ABORT_EXPIRATION_PROTOCOL_STATUS_REFS: Final[tuple[str, ...]] = (
    "READY_FOR_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE",
    "PAUSED_RETENTION_CLOCK_STILL_RUNNING",
    "ABORTED_PURGE_REQUIRED",
    "EXPIRED_PURGE_REQUIRED",
    "BLOCKED_BY_R51_12_CONSISTENCY_GUARD",
)
P7_R51_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE_STATUS_REFS: Final[tuple[str, ...]] = (
    "READY_FOR_DISPOSAL_RECEIPT_BUILDER_VERIFIER",
    "BLOCKED_BY_R51_13_PAUSE_OR_BLOCKED_PROTOCOL",
    "BLOCKED_BY_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE",
)
P7_R51_PURGE_EVIDENCE_ROW_STATUS_REFS: Final[tuple[str, ...]] = (
    "REMOVED_AND_VERIFIED",
    "NOT_REQUIRED_NOT_GENERATED",
    "PURGE_FAILED",
    "PURGE_NOT_VERIFIED",
)
P7_R51_DISPOSAL_STATUS_REFS: Final[tuple[str, ...]] = (
    "NOT_GENERATED",
    "GENERATION_BLOCKED",
    "GENERATED_LOCAL_ONLY",
    "REVIEW_IN_PROGRESS",
    "RATINGS_EXTRACTED",
    "PURGE_REQUIRED",
    "BODY_PURGED",
    "DISPOSAL_VERIFIED",
    "DISPOSAL_FAILED",
    "EXPIRED_PURGED",
)
P7_R51_DISPOSAL_RECEIPT_VERIFIER_STATUS_REFS: Final[tuple[str, ...]] = (
    "READY_FOR_BODY_FREE_POST_REVIEW_SUMMARY_BUILDER",
    "BLOCKED_BY_R51_14_PURGE",
    "BLOCKED_BY_DISPOSAL_RECEIPT_VERIFICATION",
)
P7_R51_EXECUTION_BLOCKER_KIND_REFS: Final[tuple[str, ...]] = (
    "HANDOFF",
    "VALIDATION",
    "LOCAL_ROOT",
    "EXPLICIT_ALLOW",
    "DISPOSAL",
    "GENERATION",
    "REVIEW",
    "RATING",
    "QUESTION_OBSERVATION",
    "MANIFEST",
    "BOUNDARY",
    "BODY_FREE_LEAK",
    "SCOPE",
)
P7_R51_MANUAL_RUN_DECISION_REFS: Final[tuple[str, ...]] = (
    "GO_FOR_LOCAL_MANUAL_REVIEW",
    "NO_GO_TARGET_OR_REGRESSION_EVIDENCE_MISSING",
    "NO_GO_LOCAL_ROOT_UNSAFE",
    "NO_GO_EXPLICIT_ALLOW_MISSING",
    "NO_GO_DISPOSAL_PLAN_UNSAFE",
    "NO_GO_BODY_FREE_LEAK_RISK",
    "BLOCKED_BY_EXECUTION_BLOCKER",
)
P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS: Final[tuple[str, ...]] = (
    "body_full_packets.local_only",
    "reviewer_forms.local_only",
    "reviewer_notes.local_only",
)
P7_R51_PURGE_PLAN_REQUIRED_TRUE_FIELD_REFS: Final[tuple[str, ...]] = (
    "body_full_packet_purge_required",
    "reviewer_forms_purge_required",
    "reviewer_notes_purge_required",
    "disposal_receipt_required",
    "retention_deadline_defined",
    "review_abort_purge_required",
    "expiration_purge_required",
)
P7_R51_SESSION_CONTROLLER_MATERIAL_REF_REFS: Final[tuple[str, ...]] = (
    "controller_admission_envelope_bodyfree",
    "controller_validation_evidence_note_bodyfree",
    "controller_r49_timeout_note_bodyfree",
    "controller_local_root_preflight_bodyfree",
    "controller_session_envelope_bodyfree",
)
P7_R51_REVIEWER_BLIND_POLICY_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "reviewer_faces_blind_case_id_only",
    "family_hidden_from_reviewer",
    "subscription_tier_hidden_from_reviewer",
    "expected_boundary_hidden_from_reviewer",
    "db_record_id_hidden_from_reviewer",
    "raw_user_id_hidden_from_reviewer",
    "question_text_created_here",
    "reviewer_free_text_export_allowed",
    "body_free",
)

P7_R51_LOCAL_ROOT_EXPLICIT_ALLOW_PURGE_PLAN_PREFLIGHT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "review_session_status",
    "r1_validation_evidence_schema_version",
    "r1_validation_evidence_ref",
    "validation_evidence_ready_for_r51_2_preflight",
    "required_case_count",
    "r47_local_review_root_env_var",
    "r47_local_review_storage_root_policy_schema_version",
    "r47_export_denylist_policy_schema_version",
    "r47_storage_root_policy_ref",
    "r47_export_denylist_policy_ref",
    "local_review_root_source",
    "local_review_root_configured",
    "local_review_root_status",
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
    "body_full_packet_retention_max_hours",
    "reviewer_notes_retention_after_rating_finalized_max_hours",
    "delete_trigger_refs",
    "local_packet_exported_allowed",
    "content_hash_of_body_stored_allowed",
    "export_denylist_patterns",
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
    "manual_run_decision",
    "preflight_status",
    "preflight_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "r0_current_source_r50_handoff_refrozen",
    "r1_validation_evidence_r49_timeout_handling_frozen",
    "r2_local_root_explicit_allow_purge_plan_preflight_built",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r51_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R51_R0_R1_FALSE_KEY_REFS,
)

P7_R51_ACTUAL_REVIEW_SESSION_ENVELOPE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "review_session_status",
    "envelope_status",
    "envelope_reason_refs",
    "source_snapshot_refs",
    "r50_handoff_ref",
    "r1_validation_evidence_schema_version",
    "r1_validation_evidence_ref",
    "r2_preflight_schema_version",
    "r2_preflight_ref",
    "preflight_status",
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
    "disposal_plan_ref",
    "disposal_plan_ready",
    "session_controller_material_refs",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "actual_review_session_envelope_created_here",
    "p5_actual_review_still_not_run",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "r0_current_source_r50_handoff_refrozen",
    "r1_validation_evidence_r49_timeout_handling_frozen",
    "r2_local_root_explicit_allow_purge_plan_preflight_built",
    "r3_actual_review_session_envelope_created",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r51_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R51_R0_R1_FALSE_KEY_REFS,
)



P7_R51_24_CASE_MANIFEST_ROW_FIELD_REFS: Final[tuple[str, ...]] = (
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
    "family",
    "case_role",
    "subscription_tier_ref",
    "controller_only",
    "reviewer_facing_identifier_policy",
    "reviewer_receives_blind_case_id",
    "reviewer_receives_case_ref_id",
    "reviewer_receives_family",
    "reviewer_receives_subscription_tier",
    "reviewer_receives_expected_result",
    "reviewer_receives_gate_result",
    "blind_case_id_derived_from_body_or_record_hash",
    "body_full_packet_materialized_here",
    "local_reviewer_payload_materialized_here",
    "body_free",
)
P7_R51_REVIEWER_FACING_CASE_INDEX_ROW_FIELD_REFS: Final[tuple[str, ...]] = (
    "blind_case_id",
    "reviewer_identifier_kind",
    "case_ref_hidden",
    "family_hidden",
    "tier_hidden",
    "expected_result_hidden",
    "gate_result_hidden",
    "derived_from_body_or_record_hash",
    "body_free",
)
P7_R51_24_CASE_MANIFEST_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "review_session_status",
    "manifest_status",
    "manifest_reason_refs",
    "r3_envelope_schema_version",
    "r3_envelope_ref",
    "envelope_status",
    "r48_case_matrix_schema_version",
    "r48_case_matrix_ref",
    "matrix_kind",
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
    "reviewer_facing_family_exposed",
    "reviewer_facing_tier_exposed",
    "reviewer_facing_expected_result_exposed",
    "controller_keeps_family_tier_expected_refs",
    "reviewer_receives_blind_case_id_only",
    "body_full_packet_materialized_here",
    "local_reviewer_payload_materialized_here",
    "body_full_packet_generated_here",
    "actual_human_review_run_here",
    "p5_actual_review_still_not_run",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "r0_current_source_r50_handoff_refrozen",
    "r1_validation_evidence_r49_timeout_handling_frozen",
    "r2_local_root_explicit_allow_purge_plan_preflight_built",
    "r3_actual_review_session_envelope_created",
    "r4_24_case_manifest_freeze_built",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r51_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R51_R0_R1_FALSE_KEY_REFS,
)

P7_R51_PACKET_GENERATION_REQUEST_ROW_FIELD_REFS: Final[tuple[str, ...]] = (
    "blind_case_id",
    "case_ref_id",
    "packet_ref_id",
    "packet_kind",
    "review_kind",
    "request_status_ref",
    "local_only_required",
    "must_not_export",
    "disposal_required",
    "body_full_packet_materialized_here",
    "local_file_written_here",
    "local_absolute_path_included",
    "body_content_hash_stored_here",
    "body_free",
)
P7_R51_BODY_FULL_PACKET_LOCAL_ONLY_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "blind_case_id",
    "packet_ref_id",
    "review_kind",
    "review_prompt_version",
    "local_only",
    "must_not_export",
    "disposal_required",
    "current_input_review_surface",
    "returned_emlis_surface",
    "bounded_owned_history_review_surface",
    "reviewer_rating_form",
    "question_need_observation_selection_form",
    "disposal_reminder",
)
P7_R51_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "review_session_status",
    "generation_request_status",
    "generation_request_reason_refs",
    "r4_manifest_schema_version",
    "r4_manifest_ref",
    "manifest_status",
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
    "review_prompt_version",
    "reviewer_visible_field_refs",
    "reviewer_hidden_field_refs",
    "local_root_ref",
    "root_path_exposed",
    "local_absolute_path_included",
    "disposal_plan_ref",
    "disposal_plan_ready",
    "body_full_packet_retention_max_hours",
    "reviewer_notes_retention_after_rating_finalized_max_hours",
    "local_only_required",
    "must_not_export",
    "disposal_required",
    "local_only_body_full_generation_allowed",
    "local_only_body_full_packet_generation_request_created_here",
    "body_full_packet_generation_request_created_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "local_file_ops_helper_created_here",
    "body_full_packet_writer_created_here",
    "body_full_packet_local_only_schema_file_created_here",
    "generation_event_bodyfree_only",
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
    "r0_current_source_r50_handoff_refrozen",
    "r1_validation_evidence_r49_timeout_handling_frozen",
    "r2_local_root_explicit_allow_purge_plan_preflight_built",
    "r3_actual_review_session_envelope_created",
    "r4_24_case_manifest_freeze_built",
    "r5_local_only_body_full_packet_generation_request_built",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r51_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R51_R0_R1_FALSE_KEY_REFS,
)


P7_R51_PACKET_COMPLETENESS_SCAN_ROW_FIELD_REFS: Final[tuple[str, ...]] = (
    "blind_case_id",
    "case_ref_id",
    "packet_ref_id",
    "packet_kind",
    "review_kind",
    "completion_status_ref",
    "packet_present_local_only",
    "required_field_refs_present",
    "local_only_marker_present",
    "must_not_export_marker_present",
    "disposal_required_marker_present",
    "body_full_packet_materialized_here",
    "body_full_packet_body_copied_here",
    "local_absolute_path_included",
    "body_content_hash_stored_here",
    "export_candidate_detected",
    "export_denylist_violation_detected",
    "body_free",
)
P7_R51_BODY_FULL_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "review_session_status",
    "packet_completeness_scan_status",
    "packet_completeness_scan_reason_refs",
    "r5_generation_request_schema_version",
    "r5_generation_request_ref",
    "generation_request_status",
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
    "r0_current_source_r50_handoff_refrozen",
    "r1_validation_evidence_r49_timeout_handling_frozen",
    "r2_local_root_explicit_allow_purge_plan_preflight_built",
    "r3_actual_review_session_envelope_created",
    "r4_24_case_manifest_freeze_built",
    "r5_local_only_body_full_packet_generation_request_built",
    "r6_body_full_packet_completeness_export_denylist_scan_built",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r51_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R51_R0_R1_FALSE_KEY_REFS,
)
P7_R51_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "review_session_status",
    "r6_packet_completeness_scan_schema_version",
    "r6_packet_completeness_scan_ref",
    "packet_completeness_scan_status",
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
    "r7_reviewer_instruction_rating_form_freeze_built",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "r0_current_source_r50_handoff_refrozen",
    "r1_validation_evidence_r49_timeout_handling_frozen",
    "r2_local_root_explicit_allow_purge_plan_preflight_built",
    "r3_actual_review_session_envelope_created",
    "r4_24_case_manifest_freeze_built",
    "r5_local_only_body_full_packet_generation_request_built",
    "r6_body_full_packet_completeness_export_denylist_scan_built",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r51_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R51_R0_R1_FALSE_KEY_REFS,
)


P7_R51_ACTUAL_REVIEW_RESULT_CAPTURE_ROW_FIELD_REFS: Final[tuple[str, ...]] = (
    "review_session_id",
    "packet_ref_id",
    "blind_case_id",
    "case_ref_id",
    "family",
    "case_role",
    "review_kind",
    "reviewer_ref",
    "reviewed_at",
    "axis_scores",
    "verdict",
    "sanitized_reason_ids",
    "blocker_ids",
    "question_need_primary_class",
    "ambiguity_kind_refs",
    "one_question_fit_ref",
    "repair_required_refs",
    "reviewer_free_text_included",
    "question_text_included",
    "draft_question_text_included",
    "machine_auto_score_used",
    "machine_metrics_used_for_readfeel",
    "body_removed",
    "body_free",
)
P7_R51_ACTUAL_HUMAN_REVIEW_RUN_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "review_session_status",
    "r7_reviewer_instruction_rating_form_schema_version",
    "r7_reviewer_instruction_rating_form_ref",
    "instruction_form_status",
    "instruction_form_ready_for_actual_review",
    "r4_manifest_schema_version",
    "r4_manifest_ref",
    "manifest_status",
    "required_case_count",
    "manifest_case_count",
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
    "r0_current_source_r50_handoff_refrozen",
    "r1_validation_evidence_r49_timeout_handling_frozen",
    "r2_local_root_explicit_allow_purge_plan_preflight_built",
    "r3_actual_review_session_envelope_created",
    "r4_24_case_manifest_freeze_built",
    "r5_local_only_body_full_packet_generation_request_built",
    "r6_body_full_packet_completeness_export_denylist_scan_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_actual_human_review_run_recorded",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r51_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R51_R0_R1_FALSE_KEY_REFS,
)
P7_R51_RATING_ROW_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "packet_ref_id",
    "blind_case_id",
    "case_ref_id",
    "family",
    "case_role",
    "review_kind",
    "reviewer_ref",
    "reviewed_at",
    "axis_scores",
    "verdict",
    "sanitized_reason_ids",
    "blocker_ids",
    "reviewer_free_text_included",
    "body_removed",
    "body_free",
)
P7_R51_RATING_ROW_NORMALIZER_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "review_session_status",
    "r8_actual_human_review_run_schema_version",
    "r8_actual_human_review_run_ref",
    "actual_review_run_status",
    "actual_review_run_ready_for_rating_normalization",
    "rating_row_normalizer_status",
    "rating_row_normalizer_reason_refs",
    "required_case_count",
    "review_result_capture_row_count",
    "rating_row_count",
    "rating_rows",
    "rating_row_schema_version",
    "r48_rating_row_schema_version_ref",
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
    "r0_current_source_r50_handoff_refrozen",
    "r1_validation_evidence_r49_timeout_handling_frozen",
    "r2_local_root_explicit_allow_purge_plan_preflight_built",
    "r3_actual_review_session_envelope_created",
    "r4_24_case_manifest_freeze_built",
    "r5_local_only_body_full_packet_generation_request_built",
    "r6_body_full_packet_completeness_export_denylist_scan_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_actual_human_review_run_recorded",
    "r9_rating_row_normalizer_built",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r51_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R51_R0_R1_FALSE_KEY_REFS,
)

def _false_flags() -> dict[str, bool]:
    return {key: False for key in P7_R51_R0_R1_FALSE_KEY_REFS}


def _safe_bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return bool(value)


def _safe_non_negative_int(value: Any) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return 0
    return max(number, 0)


def _safe_review_session_id(value: Any) -> str:
    return clean_identifier(value, default=P7_R51_DEFAULT_REVIEW_SESSION_ID, max_length=140)


def _safe_snapshot_refs(snapshot_refs: Mapping[str, Any] | None) -> dict[str, str]:
    refs = dict(P7_R51_SOURCE_SNAPSHOT_REFS)
    for key, value in safe_mapping(snapshot_refs).items():
        if key in refs:
            refs[key] = clean_identifier(value, default=refs[key], max_length=220)
    return refs


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
    if data.get("schema_version") != schema_version:
        raise ValueError(f"{source} schema version changed")
    if data.get("phase") != P7_PHASE:
        raise ValueError(f"{source} phase changed")
    if data.get("step") != P7_R51_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R51_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must be body-free")
    assert_false_markers(data.get("public_contract") or {}, source=f"{source}.public_contract")
    assert_false_markers(data.get("body_free_markers") or {}, source=f"{source}.body_free_markers")
    allowed = set(allowed_true_false_key_refs)
    for false_key in P7_R51_R0_R1_FALSE_KEY_REFS:
        if false_key in allowed:
            continue
        if data.get(false_key) is not False:
            raise ValueError(f"{source} must keep {false_key}=False")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)


def _r50_boundary(r50_handoff_boundary: Mapping[str, Any] | None) -> dict[str, Any]:
    boundary = (
        safe_mapping(r50_handoff_boundary)
        if r50_handoff_boundary is not None
        else build_p7_r50_touch_candidate_no_touch_boundary_freeze()
    )
    assert_p7_r50_touch_candidate_no_touch_boundary_freeze_contract(boundary)
    return boundary


def _build_r50_handoff(r50_boundary: Mapping[str, Any]) -> dict[str, Any]:
    data = safe_mapping(r50_boundary)
    if tuple(data.get("implemented_steps") or ()) != P7_R50_R20_IMPLEMENTED_STEPS:
        raise ValueError("R51 R0 requires the complete R50-0..R50-20 handoff")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_R20_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R51 R0 requires R50 not_yet_implemented_steps to be empty")
    if data.get("next_required_step") != P7_R50_R20_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R51 R0 requires R50 next_required_step to point to actual local-only manual run")
    for closed_key in (
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "actual_body_full_packet_generated_here",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "p5_human_blind_qa_confirmed",
        "p5_human_blind_qa_confirmed_candidate",
        "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed",
        "release_allowed",
        "p7_complete",
    ):
        if data.get(closed_key) is not False:
            raise ValueError(f"R51 R0 cannot inherit R50 handoff with {closed_key}=True")
    touch_ready = data.get("touch_boundary_status") == "TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FROZEN"
    validation_ready = data.get("validation_matrix_status") == "VALIDATION_COMMAND_MATRIX_READY"
    return {
        "r50_handoff_required": True,
        "r50_step": clean_identifier(data.get("step"), default=P7_R50_STEP, max_length=140),
        "r50_scope": clean_identifier(data.get("scope"), default=P7_R50_SCOPE, max_length=180),
        "r50_schema_version": P7_R50_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION,
        "r50_review_kind": P7_R51_REVIEW_KIND,
        "r50_packet_kind": P7_R51_PACKET_KIND,
        "r50_required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "r50_completed_steps": list(P7_R50_R20_IMPLEMENTED_STEPS),
        "r50_not_yet_implemented_steps": list(P7_R50_R20_NOT_YET_IMPLEMENTED_STEPS),
        "r50_next_required_step": P7_R50_R20_NEXT_REQUIRED_STEP_REF,
        "r50_touch_boundary_status": clean_identifier(data.get("touch_boundary_status"), default="UNKNOWN", max_length=120),
        "r50_validation_matrix_status": clean_identifier(data.get("validation_matrix_status"), default="UNKNOWN", max_length=120),
        "r50_boundary_freeze_ready": touch_ready and validation_ready,
        "r50_manual_run_boundary_finished": touch_ready and validation_ready,
        "r50_actual_review_completed": False,
        "r50_actual_human_review_run": False,
        "r50_body_full_packet_generated": False,
        "r50_rating_rows_materialized": False,
        "r50_question_need_observation_rows_materialized": False,
        "r50_disposal_receipt_materialized": False,
        "r50_p5_human_blind_qa_confirmed": False,
        "r50_p5_human_blind_qa_confirmed_candidate": False,
        "r50_p6_limited_human_readfeel_start_allowed": False,
        "r50_p8_start_allowed": False,
        "r50_release_allowed": False,
    }


def _assert_r50_handoff(data: Mapping[str, Any]) -> None:
    _assert_required_fields(data, required=P7_R51_R50_HANDOFF_REQUIRED_FIELD_REFS, source="p7_r51_r50_handoff")
    if data.get("r50_handoff_required") is not True:
        raise ValueError("R51 R50 handoff must be required")
    if tuple(data.get("r50_completed_steps") or ()) != P7_R50_R20_IMPLEMENTED_STEPS:
        raise ValueError("R51 R50 handoff completed steps changed")
    if tuple(data.get("r50_not_yet_implemented_steps") or ()) != P7_R50_R20_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R51 R50 handoff not-yet steps must be empty")
    if data.get("r50_next_required_step") != P7_R50_R20_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R51 R50 handoff next step changed")
    for false_key in (
        "r50_actual_review_completed",
        "r50_actual_human_review_run",
        "r50_body_full_packet_generated",
        "r50_rating_rows_materialized",
        "r50_question_need_observation_rows_materialized",
        "r50_disposal_receipt_materialized",
        "r50_p5_human_blind_qa_confirmed",
        "r50_p5_human_blind_qa_confirmed_candidate",
        "r50_p6_limited_human_readfeel_start_allowed",
        "r50_p8_start_allowed",
        "r50_release_allowed",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R51 R50 handoff must keep {false_key}=False")


def _build_p7_p8_bridge_rule() -> dict[str, bool]:
    return {
        "p7_bridge_only": True,
        "r51_is_p5_actual_local_only_manual_run": True,
        "r51_r0_r1_are_pre_review_freezes_only": True,
        "question_need_observation_memo_only": True,
        "question_need_observation_body_free_required": True,
        "p8_design_material_candidate_allowed_later": True,
        "p8_detail_design_allowed_here": False,
        "question_api_implemented": False,
        "question_db_schema_implemented": False,
        "question_rn_ui_implemented": False,
        "question_response_key_implemented": False,
        "question_trigger_logic_implemented": False,
        "raw_input_or_comment_text_allowed_in_bridge_material": False,
        "returned_surface_allowed_in_bridge_material": False,
        "reviewer_free_text_allowed_in_bridge_material": False,
        "question_text_allowed_in_bridge_material": False,
        "p7_completion_condition_relaxed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
    }


def _assert_p7_p8_bridge_rule(data: Mapping[str, Any]) -> None:
    _assert_required_fields(data, required=P7_R51_BRIDGE_RULE_REQUIRED_FIELD_REFS, source="p7_r51_p7_p8_bridge_rule")
    for true_key in (
        "p7_bridge_only",
        "r51_is_p5_actual_local_only_manual_run",
        "r51_r0_r1_are_pre_review_freezes_only",
        "question_need_observation_memo_only",
        "question_need_observation_body_free_required",
        "p8_design_material_candidate_allowed_later",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R51 bridge rule must keep {true_key}=True")
    for false_key in set(P7_R51_BRIDGE_RULE_REQUIRED_FIELD_REFS) - {
        "p7_bridge_only",
        "r51_is_p5_actual_local_only_manual_run",
        "r51_r0_r1_are_pre_review_freezes_only",
        "question_need_observation_memo_only",
        "question_need_observation_body_free_required",
        "p8_design_material_candidate_allowed_later",
    }:
        if data.get(false_key) is not False:
            raise ValueError(f"R51 bridge rule must keep {false_key}=False")


def build_p7_r51_current_source_r50_handoff_refreeze(
    *,
    snapshot_refs: Mapping[str, Any] | None = None,
    r50_handoff_boundary: Mapping[str, Any] | None = None,
    review_session_id: Any = P7_R51_DEFAULT_REVIEW_SESSION_ID,
    material_id: Any = "p7_r51_current_source_r50_handoff_refreeze",
) -> dict[str, Any]:
    """Build the R51-0 body-free current-source/R50-handoff refreeze."""

    r50_handoff = _build_r50_handoff(_r50_boundary(r50_handoff_boundary))
    refreeze = {
        "schema_version": P7_R51_CURRENT_SOURCE_R50_HANDOFF_REFREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R51_STEP,
        "scope": P7_R51_SCOPE,
        "policy_kind": P7_R51_POLICY_KIND,
        "policy_section": "R51-0_current_source_r50_handoff_refreeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r51_current_source_r50_handoff_refreeze", max_length=180),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": P7_GIT_CHECKED,
        "source_snapshot_refs": _safe_snapshot_refs(snapshot_refs),
        "review_session_id": _safe_review_session_id(review_session_id),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "r50_handoff": r50_handoff,
        "p7_p8_bridge_rule": _build_p7_p8_bridge_rule(),
        "implemented_steps": list(P7_R51_R0_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R51_R0_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r50_handoff_refrozen": True,
        "r1_validation_evidence_r49_timeout_handling_frozen": False,
        "p5_actual_review_still_not_run": True,
        "local_root_preflight_required_later": True,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "first_next_work_ref": P7_R51_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R51_R0_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r51_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r51_current_source_r50_handoff_refreeze_contract(refreeze)
    return refreeze


def assert_p7_r51_current_source_r50_handoff_refreeze_contract(refreeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(refreeze)
    _assert_required_fields(
        data,
        required=P7_R51_CURRENT_SOURCE_R50_HANDOFF_REFREEZE_REQUIRED_FIELD_REFS,
        source="p7_r51_r0_current_source_r50_handoff_refreeze",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R51_CURRENT_SOURCE_R50_HANDOFF_REFREEZE_SCHEMA_VERSION,
        source="p7_r51_r0_current_source_r50_handoff_refreeze",
    )
    if data.get("policy_section") != "R51-0_current_source_r50_handoff_refreeze":
        raise ValueError("R51 R0 policy section changed")
    if data.get("source_mode") != P7_SOURCE_MODE or data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError("R51 R0 must remain local snapshot without Git check")
    _assert_r50_handoff(safe_mapping(data.get("r50_handoff")))
    _assert_p7_p8_bridge_rule(safe_mapping(data.get("p7_p8_bridge_rule")))
    if tuple(data.get("implemented_steps") or ()) != P7_R51_R0_IMPLEMENTED_STEPS:
        raise ValueError("R51 R0 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R51_R0_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R51 R0 not-yet steps changed")
    if data.get("next_required_step") != P7_R51_R0_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R51 R0 must point to R51-1")
    for true_key in ("r0_current_source_r50_handoff_refrozen", "p5_actual_review_still_not_run", "local_root_preflight_required_later"):
        if data.get(true_key) is not True:
            raise ValueError(f"R51 R0 must keep {true_key}=True")
    if data.get("r1_validation_evidence_r49_timeout_handling_frozen") is not False:
        raise ValueError("R51 R0 must not claim R51-1")
    return True


def _evidence_row(
    *,
    evidence_group_ref: str,
    evidence_status_ref: str,
    evidence_present: bool,
    passed_count: int = 0,
    collected_count: int = 0,
    warning_count: int = 0,
    timeout_unclassified: bool = False,
    required_for_r51_2_preflight: bool = True,
    optional: bool = False,
    test_file_refs: Sequence[Any] = (),
    evidence_source_ref: str = "p7_r51_validation_evidence_freeze",
    claim_boundary_ref: str = "validation evidence only",
) -> dict[str, Any]:
    row = {
        "evidence_group_ref": clean_identifier(evidence_group_ref, default="unknown_evidence_group", max_length=120),
        "evidence_status_ref": clean_identifier(evidence_status_ref, default="UNKNOWN", max_length=100),
        "evidence_present": bool(evidence_present),
        "passed_count": _safe_non_negative_int(passed_count),
        "collected_count": _safe_non_negative_int(collected_count),
        "warning_count": _safe_non_negative_int(warning_count),
        "timeout_unclassified": bool(timeout_unclassified),
        "required_for_r51_2_preflight": bool(required_for_r51_2_preflight),
        "optional": bool(optional),
        "test_file_refs": dedupe_identifiers(test_file_refs, limit=80, max_length=260),
        "evidence_source_ref": clean_identifier(evidence_source_ref, default="p7_r51_validation_evidence_freeze", max_length=220),
        "claim_boundary_ref": clean_identifier(claim_boundary_ref, default="validation evidence only", max_length=260),
        "evidence_created_here": False,
        "validation_commands_executed_here": False,
        "command_result_body_stored_here": False,
        "terminal_output_stored_here": False,
        "body_free": True,
    }
    assert_p7_r51_validation_evidence_row_contract(row)
    return row


def _default_validation_evidence_rows() -> list[dict[str, Any]]:
    return [
        _evidence_row(
            evidence_group_ref="r51_r0_current_source_r50_handoff",
            evidence_status_ref="REFROZEN_BODYFREE",
            evidence_present=True,
            passed_count=0,
            test_file_refs=("tests/test_emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run_r0_r1_20260620.py",),
            evidence_source_ref="R51_current_local_implementation",
            claim_boundary_ref="R51-0 handoff refreeze only; not actual review or product value",
        ),
        _evidence_row(
            evidence_group_ref="r50_target",
            evidence_status_ref="PASSED",
            evidence_present=True,
            passed_count=99,
            test_file_refs=P7_R50_VALIDATION_R50_TARGET_TEST_FILE_REFS,
            evidence_source_ref="R51_pre_design_memo_20260620_prior_local_validation",
            claim_boundary_ref="R50 target helper only; not P5 actual human review completion",
        ),
        _evidence_row(
            evidence_group_ref="r49_split_matrix",
            evidence_status_ref="PASSED_BY_SPLIT_EXECUTION",
            evidence_present=True,
            passed_count=76,
            test_file_refs=P7_R49_VALIDATION_R49_TARGET_TEST_FILE_REFS,
            evidence_source_ref="R51_pre_design_memo_20260620_prior_local_validation",
            claim_boundary_ref="R49 split matrix green only; wildcard bulk green is not claimed",
        ),
        _evidence_row(
            evidence_group_ref="r49_wildcard_bulk",
            evidence_status_ref="TIMEOUT_UNCLASSIFIED",
            evidence_present=True,
            passed_count=22,
            timeout_unclassified=True,
            required_for_r51_2_preflight=False,
            test_file_refs=P7_R51_R49_WILDCARD_BULK_TEST_FILE_REFS,
            evidence_source_ref="R51_pre_design_memo_20260620_prior_local_validation",
            claim_boundary_ref="wildcard bulk timeout is visible uncertainty; not green evidence and not erased by split green",
        ),
        _evidence_row(
            evidence_group_ref="r48_regression",
            evidence_status_ref="PASSED",
            evidence_present=True,
            passed_count=82,
            test_file_refs=P7_R49_VALIDATION_R48_REGRESSION_TEST_FILE_REFS,
            evidence_source_ref="R51_pre_design_memo_20260620_prior_local_validation",
            claim_boundary_ref="R48 review-packet regression only; not P5 confirmed",
        ),
        _evidence_row(
            evidence_group_ref="r47_regression",
            evidence_status_ref="PASSED",
            evidence_present=True,
            passed_count=275,
            test_file_refs=P7_R49_VALIDATION_R47_REGRESSION_TEST_FILE_REFS,
            evidence_source_ref="R51_pre_design_memo_20260620_prior_local_validation",
            claim_boundary_ref="R47 local-only/body-free policy regression only",
        ),
        _evidence_row(
            evidence_group_ref="r46_display_p5_core_subset",
            evidence_status_ref="PASSED_WITH_KNOWN_WARNING",
            evidence_present=True,
            passed_count=94,
            warning_count=1,
            test_file_refs=(
                *P7_R49_VALIDATION_R46_HANDOFF_TEST_FILE_REFS,
                *P7_R49_VALIDATION_DISPLAY_API_TEST_FILE_REFS,
                *P7_R49_VALIDATION_P5_CORE_TEST_FILE_REFS,
            ),
            evidence_source_ref="R51_pre_design_memo_20260620_prior_local_validation",
            claim_boundary_ref="R46/display/P5 core subset only; not real-device modal readfeel or full backend suite green",
        ),
        _evidence_row(
            evidence_group_ref="backend_collect_only",
            evidence_status_ref="COLLECT_ONLY_PASSED_WITH_KNOWN_WARNING",
            evidence_present=True,
            collected_count=3466,
            warning_count=1,
            test_file_refs=("pytest --collect-only -q",),
            evidence_source_ref="R51_pre_design_memo_20260620_prior_local_validation",
            claim_boundary_ref="collect-only only; must not be claimed as full backend suite execution green",
        ),
        _evidence_row(
            evidence_group_ref="rn_no_touch_optional",
            evidence_status_ref="PASSED_OPTIONAL_NO_TOUCH",
            evidence_present=True,
            passed_count=36,
            optional=True,
            test_file_refs=P7_R49_RN_CONTRACT_OPTIONAL_NO_TOUCH_TEST_REFS,
            evidence_source_ref="R51_pre_design_memo_20260620_prior_local_validation",
            claim_boundary_ref="RN contract only; not real-device modal readfeel",
        ),
    ]


def _validation_evidence_rows_with_overrides(overrides: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    rows = _default_validation_evidence_rows()
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
            "required_for_r51_2_preflight",
            "optional",
            "test_file_refs",
            "evidence_source_ref",
            "claim_boundary_ref",
        ):
            if key in patch:
                merged[key] = patch[key]
        out.append(
            _evidence_row(
                evidence_group_ref=group_ref,
                evidence_status_ref=clean_identifier(merged.get("evidence_status_ref"), default="UNKNOWN", max_length=100),
                evidence_present=_safe_bool(merged.get("evidence_present")),
                passed_count=_safe_non_negative_int(merged.get("passed_count")),
                collected_count=_safe_non_negative_int(merged.get("collected_count")),
                warning_count=_safe_non_negative_int(merged.get("warning_count")),
                timeout_unclassified=_safe_bool(merged.get("timeout_unclassified")),
                required_for_r51_2_preflight=_safe_bool(merged.get("required_for_r51_2_preflight"), default=True),
                optional=_safe_bool(merged.get("optional")),
                test_file_refs=merged.get("test_file_refs") if isinstance(merged.get("test_file_refs"), Sequence) else row["test_file_refs"],
                evidence_source_ref=clean_identifier(merged.get("evidence_source_ref"), default="p7_r51_validation_evidence_freeze", max_length=220),
                claim_boundary_ref=clean_identifier(merged.get("claim_boundary_ref"), default="validation evidence only", max_length=260),
            )
        )
    return out


def _validation_flags(rows: Sequence[Mapping[str, Any]]) -> dict[str, bool]:
    by_group = {str(row.get("evidence_group_ref")): row for row in rows}
    required_present = all(
        by_group.get(group_ref, {}).get("evidence_present") is True
        for group_ref in P7_R51_VALIDATION_EVIDENCE_REQUIRED_GROUP_REFS
    )
    return {
        "validation_evidence_required_groups_present": required_present,
        "r50_target_green_evidence_present": by_group.get("r50_target", {}).get("evidence_present") is True,
        "r49_split_matrix_green_evidence_present": by_group.get("r49_split_matrix", {}).get("evidence_present") is True,
        "r49_wildcard_bulk_timeout_unclassified": by_group.get("r49_wildcard_bulk", {}).get("timeout_unclassified") is True,
        "r48_regression_green_evidence_present": by_group.get("r48_regression", {}).get("evidence_present") is True,
        "r47_regression_green_evidence_present": by_group.get("r47_regression", {}).get("evidence_present") is True,
        "r46_display_p5_core_green_evidence_present": by_group.get("r46_display_p5_core_subset", {}).get("evidence_present") is True,
        "rn_contract_green_evidence_present": by_group.get("rn_no_touch_optional", {}).get("evidence_present") is True,
        "backend_collect_only_evidence_present": by_group.get("backend_collect_only", {}).get("evidence_present") is True,
        "full_backend_suite_green_confirmed": False,
        "collect_only_claimed_as_full_backend_green": False,
        "rn_contract_claimed_as_real_device_modal_readfeel": False,
    }


def _validation_execution_blockers(flags: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    if flags.get("r50_target_green_evidence_present") is not True:
        blockers.append("r51_missing_r50_target_green_evidence")
    if flags.get("r49_split_matrix_green_evidence_present") is not True:
        blockers.append("r51_missing_r49_split_green_evidence")
    if flags.get("r48_regression_green_evidence_present") is not True:
        blockers.append("r51_missing_r48_regression_green_evidence")
    if flags.get("r47_regression_green_evidence_present") is not True:
        blockers.append("r51_missing_r47_regression_green_evidence")
    if flags.get("r46_display_p5_core_green_evidence_present") is not True:
        blockers.append("r51_missing_r46_display_p5_core_green_evidence")
    if flags.get("backend_collect_only_evidence_present") is not True:
        blockers.append("r51_missing_backend_collect_only_evidence")
    if flags.get("rn_contract_green_evidence_present") is not True:
        blockers.append("r51_missing_rn_contract_green_evidence")
    return blockers


def assert_p7_r51_validation_evidence_row_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R51_VALIDATION_EVIDENCE_ROW_REQUIRED_FIELD_REFS, source="p7_r51_validation_evidence_row")
    if data.get("evidence_group_ref") not in P7_R51_VALIDATION_EVIDENCE_GROUP_REFS:
        raise ValueError("R51 evidence group ref is not canonical")
    for int_key in ("passed_count", "collected_count", "warning_count"):
        if not isinstance(data.get(int_key), int) or data[int_key] < 0:
            raise ValueError(f"R51 evidence row must keep non-negative {int_key}")
    for bool_key in (
        "evidence_present",
        "timeout_unclassified",
        "required_for_r51_2_preflight",
        "optional",
        "evidence_created_here",
        "validation_commands_executed_here",
        "command_result_body_stored_here",
        "terminal_output_stored_here",
        "body_free",
    ):
        if not isinstance(data.get(bool_key), bool):
            raise ValueError(f"R51 evidence row {bool_key} must be boolean")
    for false_key in ("evidence_created_here", "validation_commands_executed_here", "command_result_body_stored_here", "terminal_output_stored_here"):
        if data.get(false_key) is not False:
            raise ValueError(f"R51 evidence row must keep {false_key}=False")
    if data.get("body_free") is not True:
        raise ValueError("R51 evidence row must be body-free")
    if data.get("evidence_group_ref") == "r49_wildcard_bulk":
        if data.get("timeout_unclassified") is not True:
            raise ValueError("R51 R49 wildcard bulk row must preserve timeout_unclassified=True")
        if data.get("required_for_r51_2_preflight") is not False:
            raise ValueError("R51 R49 wildcard bulk timeout must not be required for R51-2 preflight")
        if data.get("evidence_status_ref") != "TIMEOUT_UNCLASSIFIED":
            raise ValueError("R51 R49 wildcard bulk status must remain TIMEOUT_UNCLASSIFIED")
    else:
        if data.get("timeout_unclassified") is not False:
            raise ValueError("R51 non-wildcard rows must not carry timeout_unclassified")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r51_validation_evidence_row")
    return True


def build_p7_r51_validation_evidence_r49_timeout_handling_freeze(
    *,
    current_source_r50_handoff_refreeze: Mapping[str, Any] | None = None,
    r0_current_source_r50_handoff_refreeze: Mapping[str, Any] | None = None,
    validation_evidence_overrides: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r51_validation_evidence_r49_timeout_handling_freeze",
) -> dict[str, Any]:
    """Build R51-1 validation evidence and R49 wildcard-timeout handling freeze."""

    if current_source_r50_handoff_refreeze is not None and r0_current_source_r50_handoff_refreeze is not None:
        raise ValueError("provide only one R51-0 refreeze value")
    r0 = (
        safe_mapping(current_source_r50_handoff_refreeze)
        if current_source_r50_handoff_refreeze is not None
        else safe_mapping(r0_current_source_r50_handoff_refreeze)
        if r0_current_source_r50_handoff_refreeze is not None
        else build_p7_r51_current_source_r50_handoff_refreeze()
    )
    assert_p7_r51_current_source_r50_handoff_refreeze_contract(r0)

    rows = _validation_evidence_rows_with_overrides(validation_evidence_overrides)
    flags = _validation_flags(rows)
    blockers = _validation_execution_blockers(flags)
    ready_for_preflight = flags["validation_evidence_required_groups_present"] and not blockers
    freeze = {
        "schema_version": P7_R51_VALIDATION_EVIDENCE_R49_TIMEOUT_HANDLING_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R51_STEP,
        "scope": P7_R51_SCOPE,
        "policy_kind": P7_R51_POLICY_KIND,
        "policy_section": "R51-1_validation_evidence_r49_timeout_handling_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r51_validation_evidence_r49_timeout_handling_freeze", max_length=180),
        "review_session_id": clean_identifier(r0.get("review_session_id"), default=P7_R51_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "r0_refreeze_schema_version": P7_R51_CURRENT_SOURCE_R50_HANDOFF_REFREEZE_SCHEMA_VERSION,
        "r0_refreeze_material_ref": clean_identifier(r0.get("material_id"), default="p7_r51_current_source_r50_handoff_refreeze", max_length=180),
        "validation_evidence_group_refs": list(P7_R51_VALIDATION_EVIDENCE_GROUP_REFS),
        "validation_evidence_rows": rows,
        "validation_evidence_row_count": len(rows),
        "validation_evidence_required_group_refs": list(P7_R51_VALIDATION_EVIDENCE_REQUIRED_GROUP_REFS),
        "validation_evidence_required_groups_present": flags["validation_evidence_required_groups_present"],
        "r50_target_green_evidence_present": flags["r50_target_green_evidence_present"],
        "r49_split_matrix_green_evidence_present": flags["r49_split_matrix_green_evidence_present"],
        "r49_split_matrix_green_required_for_r51": True,
        "r49_split_matrix_green_required_for_r51_2_preflight": True,
        "r49_wildcard_bulk_timeout_unclassified": flags["r49_wildcard_bulk_timeout_unclassified"],
        "r49_wildcard_green_claim_allowed": False,
        "r49_wildcard_green_claimed": False,
        "r49_wildcard_bulk_required_for_r51_2_preflight": False,
        "r49_timeout_handling_claim_boundary_ref": "split_matrix_green_required_wildcard_bulk_timeout_visible_not_green_claim",
        "r48_regression_green_evidence_present": flags["r48_regression_green_evidence_present"],
        "r47_regression_green_evidence_present": flags["r47_regression_green_evidence_present"],
        "r46_display_p5_core_green_evidence_present": flags["r46_display_p5_core_green_evidence_present"],
        "rn_contract_green_evidence_present": flags["rn_contract_green_evidence_present"],
        "backend_collect_only_evidence_present": flags["backend_collect_only_evidence_present"],
        "full_backend_suite_green_confirmed": False,
        "collect_only_claimed_as_full_backend_green": False,
        "rn_contract_claimed_as_real_device_modal_readfeel": False,
        "validation_commands_executed_here": False,
        "command_result_body_stored_here": False,
        "terminal_output_stored_here": False,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "r0_current_source_r50_handoff_refrozen": True,
        "r1_validation_evidence_r49_timeout_handling_frozen": True,
        "validation_evidence_ready_for_r51_2_preflight": ready_for_preflight,
        "execution_blocker_ids": blockers,
        "implemented_steps": list(P7_R51_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R51_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R51_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R51_R1_NEXT_REQUIRED_STEP_REF if ready_for_preflight else P7_R51_R1_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r51_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r51_validation_evidence_r49_timeout_handling_freeze_contract(freeze)
    return freeze


def assert_p7_r51_validation_evidence_r49_timeout_handling_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_required_fields(
        data,
        required=P7_R51_VALIDATION_EVIDENCE_R49_TIMEOUT_HANDLING_FREEZE_REQUIRED_FIELD_REFS,
        source="p7_r51_r1_validation_evidence_r49_timeout_handling_freeze",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R51_VALIDATION_EVIDENCE_R49_TIMEOUT_HANDLING_FREEZE_SCHEMA_VERSION,
        source="p7_r51_r1_validation_evidence_r49_timeout_handling_freeze",
    )
    if data.get("policy_section") != "R51-1_validation_evidence_r49_timeout_handling_freeze":
        raise ValueError("R51 R1 policy section changed")
    rows = data.get("validation_evidence_rows")
    if not isinstance(rows, list) or len(rows) != len(P7_R51_VALIDATION_EVIDENCE_GROUP_REFS):
        raise ValueError("R51 R1 evidence rows changed")
    for row in rows:
        assert_p7_r51_validation_evidence_row_contract(safe_mapping(row))
    if [row.get("evidence_group_ref") for row in rows] != list(P7_R51_VALIDATION_EVIDENCE_GROUP_REFS):
        raise ValueError("R51 R1 evidence row order changed")
    flags = _validation_flags([safe_mapping(row) for row in rows])
    for key, value in flags.items():
        if data.get(key) is not value:
            raise ValueError(f"R51 R1 top-level flag mismatch for {key}")
    if data.get("r49_split_matrix_green_required_for_r51") is not True:
        raise ValueError("R51 R1 must require R49 split matrix green")
    if data.get("r49_split_matrix_green_required_for_r51_2_preflight") is not True:
        raise ValueError("R51 R1 must require R49 split matrix green before R51-2")
    if data.get("r49_wildcard_green_claim_allowed") is not False:
        raise ValueError("R51 R1 must forbid R49 wildcard green claim")
    if data.get("r49_wildcard_green_claimed") is not False:
        raise ValueError("R51 R1 must not claim R49 wildcard green")
    if data.get("r49_wildcard_bulk_required_for_r51_2_preflight") is not False:
        raise ValueError("R51 R1 must not require R49 wildcard bulk for R51-2 while split green is available")
    for false_key in (
        "full_backend_suite_green_confirmed",
        "collect_only_claimed_as_full_backend_green",
        "rn_contract_claimed_as_real_device_modal_readfeel",
        "validation_commands_executed_here",
        "command_result_body_stored_here",
        "terminal_output_stored_here",
        "actual_manual_review_run_here",
        "body_full_packet_generated_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R51 R1 must keep {false_key}=False")
    for true_key in ("r0_current_source_r50_handoff_refrozen", "r1_validation_evidence_r49_timeout_handling_frozen"):
        if data.get(true_key) is not True:
            raise ValueError(f"R51 R1 must keep {true_key}=True")
    blockers = _validation_execution_blockers(flags)
    if tuple(data.get("execution_blocker_ids") or ()) != tuple(blockers):
        raise ValueError("R51 R1 execution blockers do not match validation flags")
    ready = flags["validation_evidence_required_groups_present"] and not blockers
    if data.get("validation_evidence_ready_for_r51_2_preflight") is not ready:
        raise ValueError("R51 R1 evidence readiness does not match required evidence")
    if ready:
        if data.get("next_required_step") != P7_R51_R1_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R1 ready evidence must point to R51-2")
    else:
        if data.get("next_required_step") != P7_R51_R1_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R1 blocked evidence must point to evidence resolution")
    if tuple(data.get("implemented_steps") or ()) != P7_R51_IMPLEMENTED_STEPS:
        raise ValueError("R51 R1 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R51_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R51 R1 not-yet steps changed")
    return True



def _explicit_allow_present_r51(explicit_allow_token: Any) -> bool:
    token = clean_identifier(
        explicit_allow_token if explicit_allow_token is not None else os.environ.get(P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_ENV_VAR),
        default="",
        max_length=160,
    )
    return token == P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_TOKEN_REF


def _export_candidate_sequence(value: Sequence[Any] | Any | None) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (str, bytes, bytearray)):
        return [value]
    if isinstance(value, Mapping):
        return list(value.values())
    if isinstance(value, Sequence):
        return list(value)
    return [value]


def _export_denylist_summary_r51(export_candidate_refs: Sequence[Any] | Any | None) -> tuple[int, int, list[str]]:
    candidates = _export_candidate_sequence(export_candidate_refs)
    violation_refs: list[str] = []
    denied_count = 0
    for candidate_ref in candidates:
        reasons = p7_r47_export_candidate_deny_reasons(candidate_ref)
        if reasons:
            denied_count += 1
            violation_refs.extend(reasons)
    return len(candidates), denied_count, dedupe_identifiers(violation_refs, limit=30, max_length=140)


def build_p7_r51_default_local_only_purge_plan_bodyfree(
    *,
    purge_plan_ref: Any = "p7_r51_local_only_actual_review_purge_plan",
) -> dict[str, Any]:
    """Return a body-free purge plan descriptor; this does not create files."""

    plan = {
        "purge_plan_ref": clean_identifier(purge_plan_ref, default="p7_r51_local_only_actual_review_purge_plan", max_length=180),
        "body_full_packet_purge_required": True,
        "reviewer_forms_purge_required": True,
        "reviewer_notes_purge_required": True,
        "disposal_receipt_required": True,
        "retention_deadline_defined": True,
        "review_abort_purge_required": True,
        "expiration_purge_required": True,
        "delete_target_refs": list(P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS),
        "body_full_packet_retention_max_hours": P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
        "reviewer_notes_retention_after_rating_finalized_max_hours": P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "body_free": True,
    }
    assert_p7_no_body_payload_or_contract_mutation(plan, source="p7_r51_default_local_only_purge_plan_bodyfree")
    return plan


def _purge_plan_summary_r51(purge_plan: Mapping[str, Any] | None) -> dict[str, Any]:
    if purge_plan is None:
        return {
            "purge_plan_ref": "missing_purge_plan",
            "purge_plan_present": False,
            "purge_plan_status": "MISSING",
            "purge_plan_ready": False,
            "purge_plan_reason_refs": ["purge_plan_missing"],
            "purge_plan_delete_target_refs": [],
            "purge_plan_required_delete_target_refs": list(P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS),
            "body_full_packet_retention_max_hours": P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
            "reviewer_notes_retention_after_rating_finalized_max_hours": P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
            "delete_trigger_refs": list(P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS),
            "local_packet_exported_allowed": False,
            "content_hash_of_body_stored_allowed": False,
        }

    data = safe_mapping(purge_plan)
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r51_purge_plan_input")
    reasons: list[str] = []
    if data.get("body_free") is not True:
        reasons.append("purge_plan_not_body_free")
    for key in P7_R51_PURGE_PLAN_REQUIRED_TRUE_FIELD_REFS:
        if data.get(key) is not True:
            reasons.append(f"{key}_missing_or_false")
    delete_targets = dedupe_identifiers(data.get("delete_target_refs") or [], limit=20, max_length=160)
    missing_targets = [target for target in P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS if target not in delete_targets]
    if missing_targets:
        reasons.append("purge_plan_delete_targets_incomplete")
    if _safe_non_negative_int(data.get("body_full_packet_retention_max_hours")) != P7_R47_BODY_FULL_PACKET_RETENTION_HOURS:
        reasons.append("body_full_packet_retention_window_changed")
    if (
        _safe_non_negative_int(data.get("reviewer_notes_retention_after_rating_finalized_max_hours"))
        != P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS
    ):
        reasons.append("reviewer_notes_retention_window_changed")
    if data.get("local_packet_exported") is not False:
        reasons.append("purge_plan_allows_local_packet_export")
    if data.get("content_hash_of_body_stored") is not False:
        reasons.append("purge_plan_allows_body_content_hash_storage")

    ready = not reasons
    return {
        "purge_plan_ref": clean_identifier(data.get("purge_plan_ref"), default="p7_r51_local_only_actual_review_purge_plan", max_length=180),
        "purge_plan_present": True,
        "purge_plan_status": "READY" if ready else "INCOMPLETE",
        "purge_plan_ready": ready,
        "purge_plan_reason_refs": [] if ready else dedupe_identifiers(reasons, limit=20, max_length=140),
        "purge_plan_delete_target_refs": delete_targets,
        "purge_plan_required_delete_target_refs": list(P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS),
        "body_full_packet_retention_max_hours": P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
        "reviewer_notes_retention_after_rating_finalized_max_hours": P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
        "delete_trigger_refs": list(P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS),
        "local_packet_exported_allowed": False,
        "content_hash_of_body_stored_allowed": False,
    }


def _r2_preflight_status_and_reasons(
    *,
    r1: Mapping[str, Any],
    local_root_valid: bool,
    local_root_configured: bool,
    explicit_allow_present: bool,
    purge_plan_ready: bool,
    export_denylist_violation_refs: Sequence[Any],
) -> tuple[str, list[str], list[str]]:
    reason_refs: list[str] = []
    blocker_ids: list[str] = []
    if r1.get("validation_evidence_ready_for_r51_2_preflight") is not True:
        reason_refs.append("validation_evidence_not_ready_for_r51_2_preflight")
        blocker_ids.extend(dedupe_identifiers(r1.get("execution_blocker_ids") or ["r51_validation_evidence_not_ready"], limit=20, max_length=140))
    if not local_root_configured:
        reason_refs.append("local_review_root_missing")
        blocker_ids.append("r51_local_review_root_missing")
    elif not local_root_valid:
        reason_refs.append("local_review_root_invalid")
        blocker_ids.append("r51_local_review_root_invalid")
    if explicit_allow_present is not True:
        reason_refs.append("explicit_allow_token_missing_or_invalid")
        blocker_ids.append("r51_explicit_allow_missing")
    if purge_plan_ready is not True:
        reason_refs.append("purge_plan_missing_or_incomplete")
        blocker_ids.append("r51_disposal_plan_missing")
    if export_denylist_violation_refs:
        reason_refs.append("export_denylist_violation_detected")
        blocker_ids.append("r51_body_full_packet_export_violation")
    if reason_refs:
        return "BLOCKED", dedupe_identifiers(reason_refs, limit=30, max_length=140), dedupe_identifiers(blocker_ids, limit=30, max_length=140)
    return "PASSED", ["local_root_explicit_allow_purge_plan_preflight_passed"], []


def _manual_run_decision_from_r2_blockers(blocker_ids: Sequence[Any]) -> str:
    blockers = set(dedupe_identifiers(blocker_ids, limit=40, max_length=140))
    if not blockers:
        return "GO_FOR_LOCAL_MANUAL_REVIEW"
    if blockers & {
        "r51_missing_r50_target_green_evidence",
        "r51_missing_r49_split_green_evidence",
        "r51_missing_r48_regression_green_evidence",
        "r51_missing_r47_regression_green_evidence",
        "r51_missing_r46_display_p5_core_green_evidence",
        "r51_missing_rn_contract_green_evidence",
        "r51_missing_backend_collect_only_evidence",
        "r51_validation_evidence_not_ready",
    }:
        return "NO_GO_TARGET_OR_REGRESSION_EVIDENCE_MISSING"
    if blockers & {"r51_local_review_root_missing", "r51_local_review_root_invalid"}:
        return "NO_GO_LOCAL_ROOT_UNSAFE"
    if "r51_explicit_allow_missing" in blockers:
        return "NO_GO_EXPLICIT_ALLOW_MISSING"
    if "r51_disposal_plan_missing" in blockers:
        return "NO_GO_DISPOSAL_PLAN_UNSAFE"
    if blockers & {"r51_body_full_packet_export_violation", "r51_body_free_leak_detected"}:
        return "NO_GO_BODY_FREE_LEAK_RISK"
    return "BLOCKED_BY_EXECUTION_BLOCKER"


def _safe_reviewer_ref(value: Any) -> str:
    ref = clean_identifier(value, default=P7_R51_DEFAULT_REVIEWER_REF, max_length=120)
    if ref.lower() in {"", "mash", "user", "raw_user", "real_user"}:
        return P7_R51_DEFAULT_REVIEWER_REF
    return ref


def _reviewer_blind_policy() -> dict[str, bool]:
    return {
        "reviewer_faces_blind_case_id_only": True,
        "family_hidden_from_reviewer": True,
        "subscription_tier_hidden_from_reviewer": True,
        "expected_boundary_hidden_from_reviewer": True,
        "db_record_id_hidden_from_reviewer": True,
        "raw_user_id_hidden_from_reviewer": True,
        "question_text_created_here": False,
        "reviewer_free_text_export_allowed": False,
        "body_free": True,
    }


def _assert_reviewer_blind_policy(data: Mapping[str, Any]) -> None:
    _assert_required_fields(data, required=P7_R51_REVIEWER_BLIND_POLICY_REQUIRED_FIELD_REFS, source="p7_r51_r3_reviewer_blind_policy")
    for key in (
        "reviewer_faces_blind_case_id_only",
        "family_hidden_from_reviewer",
        "subscription_tier_hidden_from_reviewer",
        "expected_boundary_hidden_from_reviewer",
        "db_record_id_hidden_from_reviewer",
        "raw_user_id_hidden_from_reviewer",
    ):
        if data.get(key) is not True:
            raise ValueError(f"R51 R3 reviewer blind policy must keep {key}=True")
    for key in ("question_text_created_here", "reviewer_free_text_export_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"R51 R3 reviewer blind policy must keep {key}=False")
    if data.get("body_free") is not True:
        raise ValueError("R51 R3 reviewer blind policy must be body-free")


def build_p7_r51_local_root_explicit_allow_purge_plan_preflight(
    *,
    validation_evidence_r49_timeout_handling_freeze: Mapping[str, Any] | None = None,
    r1_validation_evidence_r49_timeout_handling_freeze: Mapping[str, Any] | None = None,
    local_review_root: Any = None,
    repo_roots: Sequence[Any] | None = None,
    export_roots: Sequence[Any] | None = None,
    explicit_allow_token: Any = None,
    purge_plan: Mapping[str, Any] | None = None,
    export_candidate_refs: Sequence[Any] | Any | None = None,
    material_id: Any = "p7_r51_local_root_explicit_allow_purge_plan_preflight",
) -> dict[str, Any]:
    """Build the R51-2 body-free local root / allow / purge-plan preflight.

    This authorizes only a later local-only generation request.  It never
    writes packets, stores local paths, stores allow token values, or exports
    body-full material.
    """

    if validation_evidence_r49_timeout_handling_freeze is not None and r1_validation_evidence_r49_timeout_handling_freeze is not None:
        raise ValueError("provide only one R51-1 validation freeze value")
    r1 = (
        safe_mapping(validation_evidence_r49_timeout_handling_freeze)
        if validation_evidence_r49_timeout_handling_freeze is not None
        else safe_mapping(r1_validation_evidence_r49_timeout_handling_freeze)
        if r1_validation_evidence_r49_timeout_handling_freeze is not None
        else build_p7_r51_validation_evidence_r49_timeout_handling_freeze()
    )
    assert_p7_r51_validation_evidence_r49_timeout_handling_freeze_contract(r1)

    storage_policy = build_p7_r47_local_review_storage_root_policy(
        local_review_root=local_review_root,
        repo_roots=repo_roots,
        export_roots=export_roots,
        material_id="p7_r51_r2_r47_storage_root_preflight",
    )
    assert_p7_r47_local_review_storage_root_policy_contract(storage_policy)
    export_policy = build_p7_r47_export_denylist_policy(material_id="p7_r51_r2_r47_export_denylist_preflight")
    assert_p7_r47_export_denylist_policy_contract(export_policy)

    root_configured = storage_policy.get("local_review_root_configured") is True
    root_valid = storage_policy.get("local_review_root_status") == "valid" and storage_policy.get("local_body_packet_generation_allowed") is True
    allow_present = _explicit_allow_present_r51(explicit_allow_token)
    purge_summary = _purge_plan_summary_r51(purge_plan)
    checked_count, denied_count, deny_refs = _export_denylist_summary_r51(export_candidate_refs)
    preflight_status, reason_refs, blocker_ids = _r2_preflight_status_and_reasons(
        r1=r1,
        local_root_valid=root_valid,
        local_root_configured=root_configured,
        explicit_allow_present=allow_present,
        purge_plan_ready=purge_summary["purge_plan_ready"],
        export_denylist_violation_refs=deny_refs,
    )
    ready = preflight_status == "PASSED"
    preflight = {
        "schema_version": P7_R51_LOCAL_ROOT_EXPLICIT_ALLOW_PURGE_PLAN_PREFLIGHT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R51_STEP,
        "scope": P7_R51_SCOPE,
        "policy_kind": P7_R51_POLICY_KIND,
        "policy_section": "R51-2_local_root_explicit_allow_purge_plan_preflight",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r51_local_root_explicit_allow_purge_plan_preflight", max_length=180),
        "review_session_id": clean_identifier(r1.get("review_session_id"), default=P7_R51_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_session_status": "READY_FOR_ACTUAL_REVIEW_SESSION_ENVELOPE" if ready else "PRECHECK_BLOCKED",
        "r1_validation_evidence_schema_version": P7_R51_VALIDATION_EVIDENCE_R49_TIMEOUT_HANDLING_FREEZE_SCHEMA_VERSION,
        "r1_validation_evidence_ref": clean_identifier(r1.get("material_id"), default="p7_r51_validation_evidence_r49_timeout_handling_freeze", max_length=180),
        "validation_evidence_ready_for_r51_2_preflight": r1.get("validation_evidence_ready_for_r51_2_preflight") is True,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "r47_local_review_root_env_var": P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR,
        "r47_local_review_storage_root_policy_schema_version": P7_R47_LOCAL_REVIEW_STORAGE_ROOT_POLICY_SCHEMA_VERSION,
        "r47_export_denylist_policy_schema_version": P7_R47_EXPORT_DENYLIST_POLICY_SCHEMA_VERSION,
        "r47_storage_root_policy_ref": clean_identifier(storage_policy.get("material_id"), default="p7_r51_r2_r47_storage_root_preflight", max_length=180),
        "r47_export_denylist_policy_ref": clean_identifier(export_policy.get("material_id"), default="p7_r51_r2_r47_export_denylist_preflight", max_length=180),
        "local_review_root_source": clean_identifier(storage_policy.get("local_review_root_source"), default="missing", max_length=80),
        "local_review_root_configured": root_configured,
        "local_review_root_status": clean_identifier(storage_policy.get("local_review_root_status"), default="missing", max_length=40),
        "local_review_root_valid": root_valid,
        "storage_root_ref": P7_R47_STORAGE_ROOT_REF if root_valid else "not_configured_or_invalid",
        "root_path_exposed": False,
        "local_absolute_path_included": False,
        "explicit_allow_env_var": P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_ENV_VAR,
        "explicit_allow_token_ref": P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_TOKEN_REF,
        "explicit_allow_present": allow_present,
        "explicit_allow_token_body_stored_here": False,
        **purge_summary,
        "purge_plan_required_before_body_full_generation": True,
        "export_denylist_patterns": list(P7_R47_EXPORT_DENYLIST_PATTERNS),
        "export_candidate_refs_checked_count": checked_count,
        "export_denylist_violation_refs": deny_refs,
        "denied_export_candidate_count": denied_count,
        "export_candidate_refs_stored_here": False,
        "export_candidate_body_stored_here": False,
        "body_full_packet_export_allowed": False,
        "reviewer_notes_export_allowed": False,
        "body_full_packet_zip_inclusion_allowed": False,
        "premise_or_implemented_docs_inclusion_allowed": False,
        "local_only_body_full_generation_allowed_before_preflight": False,
        "local_only_body_full_generation_allowed_after_preflight": ready,
        "local_only_body_full_generation_allowed": ready,
        "manual_run_decision": _manual_run_decision_from_r2_blockers(blocker_ids),
        "preflight_status": preflight_status,
        "preflight_reason_refs": reason_refs,
        "execution_blocker_ids": blocker_ids,
        "open_execution_blocker_ids": blocker_ids,
        "r0_current_source_r50_handoff_refrozen": True,
        "r1_validation_evidence_r49_timeout_handling_frozen": True,
        "r2_local_root_explicit_allow_purge_plan_preflight_built": True,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "implemented_steps": list(P7_R51_R2_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R51_R2_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R51_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R51_R2_NEXT_REQUIRED_STEP_REF if ready else P7_R51_R2_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r51_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r51_local_root_explicit_allow_purge_plan_preflight_contract(preflight)
    return preflight


def assert_p7_r51_local_root_explicit_allow_purge_plan_preflight_contract(preflight: Mapping[str, Any]) -> bool:
    data = safe_mapping(preflight)
    _assert_required_fields(
        data,
        required=P7_R51_LOCAL_ROOT_EXPLICIT_ALLOW_PURGE_PLAN_PREFLIGHT_REQUIRED_FIELD_REFS,
        source="p7_r51_r2_local_root_explicit_allow_purge_plan_preflight",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R51_LOCAL_ROOT_EXPLICIT_ALLOW_PURGE_PLAN_PREFLIGHT_SCHEMA_VERSION,
        source="p7_r51_r2_local_root_explicit_allow_purge_plan_preflight",
    )
    if data.get("policy_section") != "R51-2_local_root_explicit_allow_purge_plan_preflight":
        raise ValueError("R51 R2 policy section changed")
    if data.get("review_session_status") not in P7_R51_REVIEW_SESSION_STATUS_REFS:
        raise ValueError("R51 R2 review session status changed")
    if data.get("required_case_count") != P7_R51_REQUIRED_CASE_COUNT:
        raise ValueError("R51 R2 must keep required_case_count=24")
    if data.get("r47_local_review_root_env_var") != P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR:
        raise ValueError("R51 R2 local review root env var changed")
    if data.get("r47_local_review_storage_root_policy_schema_version") != P7_R47_LOCAL_REVIEW_STORAGE_ROOT_POLICY_SCHEMA_VERSION:
        raise ValueError("R51 R2 storage root policy schema ref changed")
    if data.get("r47_export_denylist_policy_schema_version") != P7_R47_EXPORT_DENYLIST_POLICY_SCHEMA_VERSION:
        raise ValueError("R51 R2 export denylist schema ref changed")
    if tuple(data.get("export_denylist_patterns") or ()) != P7_R47_EXPORT_DENYLIST_PATTERNS:
        raise ValueError("R51 R2 export denylist patterns changed")
    for false_key in (
        "root_path_exposed",
        "local_absolute_path_included",
        "explicit_allow_token_body_stored_here",
        "local_packet_exported_allowed",
        "content_hash_of_body_stored_allowed",
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
            raise ValueError(f"R51 R2 must keep {false_key}=False")
    if data.get("explicit_allow_env_var") != P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_ENV_VAR:
        raise ValueError("R51 R2 explicit allow env var changed")
    if data.get("explicit_allow_token_ref") != P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_TOKEN_REF:
        raise ValueError("R51 R2 explicit allow token ref changed")
    if data.get("purge_plan_required_before_body_full_generation") is not True:
        raise ValueError("R51 R2 must require purge plan before body-full generation")
    if tuple(data.get("purge_plan_required_delete_target_refs") or ()) != P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS:
        raise ValueError("R51 R2 purge target refs changed")
    if data.get("body_full_packet_retention_max_hours") != P7_R47_BODY_FULL_PACKET_RETENTION_HOURS:
        raise ValueError("R51 R2 body-full retention window changed")
    if data.get("reviewer_notes_retention_after_rating_finalized_max_hours") != P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS:
        raise ValueError("R51 R2 reviewer notes retention window changed")
    if tuple(data.get("delete_trigger_refs") or ()) != P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS:
        raise ValueError("R51 R2 delete trigger refs changed")
    status = data.get("preflight_status")
    if status not in P7_R51_PREFLIGHT_STATUS_REFS:
        raise ValueError("R51 R2 preflight status changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R51 R2 open blockers must match execution blockers")
    unknown_blockers = sorted(set(blockers) - set(P7_R51_EXECUTION_BLOCKER_ID_REFS))
    if unknown_blockers:
        raise ValueError(f"R51 R2 execution blocker ids are not canonical: {unknown_blockers[:4]}")
    expected_decision = _manual_run_decision_from_r2_blockers(blockers)
    if data.get("manual_run_decision") != expected_decision:
        raise ValueError("R51 R2 manual run decision does not match blockers")
    ready = status == "PASSED"
    if data.get("local_only_body_full_generation_allowed_after_preflight") is not ready:
        raise ValueError("R51 R2 after-preflight authorization must match status")
    if data.get("local_only_body_full_generation_allowed") is not ready:
        raise ValueError("R51 R2 generation authorization must match status")
    if ready:
        for true_key in (
            "validation_evidence_ready_for_r51_2_preflight",
            "local_review_root_configured",
            "local_review_root_valid",
            "explicit_allow_present",
            "purge_plan_present",
            "purge_plan_ready",
        ):
            if data.get(true_key) is not True:
                raise ValueError(f"R51 R2 PASSED requires {true_key}=True")
        if data.get("storage_root_ref") != P7_R47_STORAGE_ROOT_REF:
            raise ValueError("R51 R2 PASSED must expose only the abstract storage root ref")
        if data.get("denied_export_candidate_count") != 0 or data.get("export_denylist_violation_refs"):
            raise ValueError("R51 R2 PASSED must have no export denylist violations")
        if blockers:
            raise ValueError("R51 R2 PASSED must not carry blockers")
        if data.get("manual_run_decision") != "GO_FOR_LOCAL_MANUAL_REVIEW":
            raise ValueError("R51 R2 PASSED must produce GO decision")
        if data.get("review_session_status") != "READY_FOR_ACTUAL_REVIEW_SESSION_ENVELOPE":
            raise ValueError("R51 R2 PASSED must be ready for R51-3 envelope")
        if data.get("next_required_step") != P7_R51_R2_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R2 PASSED must point to R51-3")
    else:
        if not data.get("preflight_reason_refs") or not blockers:
            raise ValueError("R51 R2 BLOCKED must carry reasons and blockers")
        if data.get("review_session_status") != "PRECHECK_BLOCKED":
            raise ValueError("R51 R2 BLOCKED must use PRECHECK_BLOCKED")
        if data.get("next_required_step") != P7_R51_R2_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R2 BLOCKED must point to blocker resolution")
    if tuple(data.get("implemented_steps") or ()) != P7_R51_R2_IMPLEMENTED_STEPS:
        raise ValueError("R51 R2 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R51_R2_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R51 R2 not-yet steps changed")
    return True


def build_p7_r51_actual_review_session_envelope_bodyfree(
    *,
    local_root_explicit_allow_purge_plan_preflight: Mapping[str, Any] | None = None,
    r2_local_root_explicit_allow_purge_plan_preflight: Mapping[str, Any] | None = None,
    snapshot_refs: Mapping[str, Any] | None = None,
    reviewer_ref: Any = P7_R51_DEFAULT_REVIEWER_REF,
    material_id: Any = "p7_r51_actual_review_session_envelope_bodyfree",
) -> dict[str, Any]:
    """Build R51-3 body-free actual-review session envelope.

    A ready envelope is created only after R51-2 passes.  A blocked envelope is
    still body-free and carries the R51-2 blocker ids.  No body-full packet,
    reviewer rating, question observation row, or disposal receipt is created.
    """

    if local_root_explicit_allow_purge_plan_preflight is not None and r2_local_root_explicit_allow_purge_plan_preflight is not None:
        raise ValueError("provide only one R51-2 preflight value")
    r2 = (
        safe_mapping(local_root_explicit_allow_purge_plan_preflight)
        if local_root_explicit_allow_purge_plan_preflight is not None
        else safe_mapping(r2_local_root_explicit_allow_purge_plan_preflight)
        if r2_local_root_explicit_allow_purge_plan_preflight is not None
        else build_p7_r51_local_root_explicit_allow_purge_plan_preflight()
    )
    assert_p7_r51_local_root_explicit_allow_purge_plan_preflight_contract(r2)
    ready = r2.get("preflight_status") == "PASSED"
    blockers = dedupe_identifiers(r2.get("execution_blocker_ids") or [], limit=40, max_length=140)
    envelope = {
        "schema_version": P7_R51_ACTUAL_REVIEW_SESSION_ENVELOPE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R51_STEP,
        "scope": P7_R51_SCOPE,
        "policy_kind": P7_R51_POLICY_KIND,
        "policy_section": "R51-3_actual_review_session_envelope",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r51_actual_review_session_envelope_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r2.get("review_session_id"), default=P7_R51_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_session_status": "ACTUAL_REVIEW_SESSION_ENVELOPE_READY" if ready else "PRECHECK_BLOCKED",
        "envelope_status": "READY_FOR_24_CASE_MANIFEST_FREEZE" if ready else "BLOCKED_BY_R51_2_PREFLIGHT",
        "envelope_reason_refs": ["actual_review_session_envelope_ready"] if ready else ["r51_2_preflight_not_passed"],
        "source_snapshot_refs": _safe_snapshot_refs(snapshot_refs),
        "r50_handoff_ref": P7_R51_R50_HANDOFF_REF,
        "r1_validation_evidence_schema_version": P7_R51_VALIDATION_EVIDENCE_R49_TIMEOUT_HANDLING_FREEZE_SCHEMA_VERSION,
        "r1_validation_evidence_ref": clean_identifier(r2.get("r1_validation_evidence_ref"), default="p7_r51_validation_evidence_r49_timeout_handling_freeze", max_length=180),
        "r2_preflight_schema_version": P7_R51_LOCAL_ROOT_EXPLICIT_ALLOW_PURGE_PLAN_PREFLIGHT_SCHEMA_VERSION,
        "r2_preflight_ref": clean_identifier(r2.get("material_id"), default="p7_r51_local_root_explicit_allow_purge_plan_preflight", max_length=180),
        "preflight_status": clean_identifier(r2.get("preflight_status"), default="BLOCKED", max_length=40),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "review_prompt_version": P7_R51_REVIEW_PROMPT_VERSION,
        "reviewer_ref": _safe_reviewer_ref(reviewer_ref),
        "reviewer_ref_pseudonymous": True,
        "reviewer_blind_policy": _reviewer_blind_policy(),
        "reviewer_visible_field_refs": list(P7_R50_REVIEWER_VISIBLE_FIELD_REFS),
        "reviewer_hidden_field_refs": list(P7_R50_REVIEWER_HIDDEN_FIELD_REFS),
        "local_root_ref": P7_R47_STORAGE_ROOT_REF if r2.get("local_review_root_valid") is True else "not_configured_or_invalid",
        "root_path_exposed": False,
        "local_absolute_path_included": False,
        "body_full_generation_allowed": ready,
        "local_only_body_full_generation_allowed": ready,
        "disposal_plan_ref": clean_identifier(r2.get("purge_plan_ref"), default="missing_purge_plan", max_length=180),
        "disposal_plan_ready": r2.get("purge_plan_ready") is True,
        "session_controller_material_refs": list(P7_R51_SESSION_CONTROLLER_MATERIAL_REF_REFS),
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "actual_review_session_envelope_created_here": True,
        "p5_actual_review_still_not_run": True,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "r0_current_source_r50_handoff_refrozen": True,
        "r1_validation_evidence_r49_timeout_handling_frozen": True,
        "r2_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r3_actual_review_session_envelope_created": True,
        "implemented_steps": list(P7_R51_R3_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R51_R3_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R51_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R51_R3_NEXT_REQUIRED_STEP_REF if ready else P7_R51_R3_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r51_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r51_actual_review_session_envelope_bodyfree_contract(envelope)
    return envelope


def assert_p7_r51_actual_review_session_envelope_bodyfree_contract(envelope: Mapping[str, Any]) -> bool:
    data = safe_mapping(envelope)
    _assert_required_fields(
        data,
        required=P7_R51_ACTUAL_REVIEW_SESSION_ENVELOPE_REQUIRED_FIELD_REFS,
        source="p7_r51_r3_actual_review_session_envelope_bodyfree",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R51_ACTUAL_REVIEW_SESSION_ENVELOPE_SCHEMA_VERSION,
        source="p7_r51_r3_actual_review_session_envelope_bodyfree",
    )
    if data.get("policy_section") != "R51-3_actual_review_session_envelope":
        raise ValueError("R51 R3 policy section changed")
    if data.get("review_session_status") not in P7_R51_REVIEW_SESSION_STATUS_REFS:
        raise ValueError("R51 R3 review session status changed")
    if data.get("required_case_count") != P7_R51_REQUIRED_CASE_COUNT:
        raise ValueError("R51 R3 must keep required_case_count=24")
    if data.get("r50_handoff_ref") != P7_R51_R50_HANDOFF_REF:
        raise ValueError("R51 R3 R50 handoff ref changed")
    if data.get("r2_preflight_schema_version") != P7_R51_LOCAL_ROOT_EXPLICIT_ALLOW_PURGE_PLAN_PREFLIGHT_SCHEMA_VERSION:
        raise ValueError("R51 R3 preflight schema ref changed")
    if data.get("review_prompt_version") != P7_R51_REVIEW_PROMPT_VERSION:
        raise ValueError("R51 R3 review prompt version changed")
    _assert_reviewer_blind_policy(safe_mapping(data.get("reviewer_blind_policy")))
    if tuple(data.get("session_controller_material_refs") or ()) != P7_R51_SESSION_CONTROLLER_MATERIAL_REF_REFS:
        raise ValueError("R51 R3 controller material refs changed")
    if tuple(data.get("reviewer_visible_field_refs") or ()) != P7_R50_REVIEWER_VISIBLE_FIELD_REFS:
        raise ValueError("R51 R3 reviewer visible fields changed")
    if tuple(data.get("reviewer_hidden_field_refs") or ()) != P7_R50_REVIEWER_HIDDEN_FIELD_REFS:
        raise ValueError("R51 R3 reviewer hidden fields changed")
    for false_key in (
        "root_path_exposed",
        "local_absolute_path_included",
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "body_full_packet_generated_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R51 R3 must keep {false_key}=False")
    if data.get("actual_review_session_envelope_created_here") is not True:
        raise ValueError("R51 R3 must mark only the body-free envelope as created")
    if data.get("p5_actual_review_still_not_run") is not True:
        raise ValueError("R51 R3 must not claim P5 actual review ran")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R51 R3 open blockers must match execution blockers")
    unknown_blockers = sorted(set(blockers) - set(P7_R51_EXECUTION_BLOCKER_ID_REFS))
    if unknown_blockers:
        raise ValueError(f"R51 R3 execution blocker ids are not canonical: {unknown_blockers[:4]}")
    ready = data.get("preflight_status") == "PASSED"
    if data.get("body_full_generation_allowed") is not ready:
        raise ValueError("R51 R3 body-full generation authorization must match preflight")
    if data.get("local_only_body_full_generation_allowed") is not ready:
        raise ValueError("R51 R3 local-only generation authorization must match preflight")
    if ready:
        if data.get("review_session_status") != "ACTUAL_REVIEW_SESSION_ENVELOPE_READY":
            raise ValueError("R51 R3 ready envelope status changed")
        if data.get("envelope_status") != "READY_FOR_24_CASE_MANIFEST_FREEZE":
            raise ValueError("R51 R3 ready envelope must point to manifest freeze")
        if data.get("local_root_ref") != P7_R47_STORAGE_ROOT_REF:
            raise ValueError("R51 R3 ready envelope must expose only abstract local root ref")
        if data.get("disposal_plan_ready") is not True:
            raise ValueError("R51 R3 ready envelope requires ready disposal plan")
        if blockers:
            raise ValueError("R51 R3 ready envelope must not carry blockers")
        if data.get("next_required_step") != P7_R51_R3_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R3 ready envelope must point to R51-4")
    else:
        if data.get("review_session_status") != "PRECHECK_BLOCKED":
            raise ValueError("R51 R3 blocked envelope must use PRECHECK_BLOCKED")
        if data.get("envelope_status") != "BLOCKED_BY_R51_2_PREFLIGHT":
            raise ValueError("R51 R3 blocked envelope status changed")
        if data.get("next_required_step") != P7_R51_R3_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R3 blocked envelope must point to preflight resolution")
    if tuple(data.get("implemented_steps") or ()) != P7_R51_R3_IMPLEMENTED_STEPS:
        raise ValueError("R51 R3 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R51_R3_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R51 R3 not-yet steps changed")
    return True



def _r51_count_by(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = clean_identifier(safe_mapping(row).get(key), default="unknown", max_length=160)
        counts[value] = counts.get(value, 0) + 1
    return counts


def _r51_case_refs(rows: Sequence[Mapping[str, Any]], key: str) -> list[str]:
    return [clean_identifier(safe_mapping(row).get(key), default="", max_length=180) for row in rows]


def _r51_unique_non_empty(values: Sequence[Any]) -> bool:
    refs = [clean_identifier(value, default="", max_length=180) for value in values]
    return bool(refs) and all(refs) and len(set(refs)) == len(refs)


def _r51_manifest_minimums_satisfied(rows: Sequence[Mapping[str, Any]]) -> bool:
    minimums = safe_mapping(P7_R47_P5_FIRST_FORMAL_MINIMUMS)
    family_counts = _r51_count_by(rows, "family")
    role_counts = _r51_count_by(rows, "case_role")
    if len(rows) != P7_R51_REQUIRED_CASE_COUNT:
        return False
    if len(rows) < _safe_non_negative_int(minimums.get("minimum_total_cases")):
        return False
    for family, expected_count, _case_role in P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION:
        if family_counts.get(family, 0) != expected_count:
            return False
    owned_positive = sum(role_counts.get(role, 0) for role in P7_R48_P5_POSITIVE_CASE_ROLE_REFS)
    if owned_positive < _safe_non_negative_int(minimums.get("minimum_owned_history_positive_cases")):
        return False
    block_minimums = safe_mapping(minimums.get("minimum_block_boundary_cases"))
    for family, count in block_minimums.items():
        if family_counts.get(str(family), 0) < int(count):
            return False
    return True


def _assert_r51_case_row(row: Mapping[str, Any]) -> None:
    data = safe_mapping(row)
    _assert_required_fields(data, required=tuple(P7_R48_P5_CASE_MATRIX_ROW_FIELD_REFS), source="p7_r51_r4_case_row")
    if data.get("body_free") is not True:
        raise ValueError("R51 R4 case row must be body-free")
    if data.get("controller_only") is not True:
        raise ValueError("R51 R4 case row must remain controller-only")
    for false_key in (
        "reviewer_facing_family_exposed",
        "reviewer_facing_tier_exposed",
        "body_full_packet_materialized_here",
        "local_reviewer_payload_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R51 R4 case row must keep {false_key}=False")
    for required_key in ("case_ref_id", "blind_case_id", "packet_ref_id", "family", "case_role", "subscription_tier_ref"):
        if not clean_identifier(data.get(required_key), default="", max_length=180):
            raise ValueError(f"R51 R4 case row missing {required_key}")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r51_r4_case_row")


def _controller_manifest_rows_from_r51_case_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row_raw in rows:
        row = safe_mapping(row_raw)
        out.append(
            {
                "case_ref_id": clean_identifier(row.get("case_ref_id"), default="case_ref", max_length=160),
                "blind_case_id": clean_identifier(row.get("blind_case_id"), default="blind_case", max_length=160),
                "packet_ref_id": clean_identifier(row.get("packet_ref_id"), default="packet_ref", max_length=160),
                "family": clean_identifier(row.get("family"), default="unknown", max_length=160),
                "case_role": clean_identifier(row.get("case_role"), default="unknown", max_length=120),
                "subscription_tier_ref": clean_identifier(row.get("subscription_tier_ref"), default="unknown", max_length=80),
                "controller_only": True,
                "reviewer_facing_identifier_policy": "blind_case_id_only",
                "reviewer_receives_blind_case_id": True,
                "reviewer_receives_case_ref_id": False,
                "reviewer_receives_family": False,
                "reviewer_receives_subscription_tier": False,
                "reviewer_receives_expected_result": False,
                "reviewer_receives_gate_result": False,
                "blind_case_id_derived_from_body_or_record_hash": False,
                "body_full_packet_materialized_here": False,
                "local_reviewer_payload_materialized_here": False,
                "body_free": True,
            }
        )
    return out


def _reviewer_facing_case_index_rows_from_r51_case_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row_raw in rows:
        row = safe_mapping(row_raw)
        out.append(
            {
                "blind_case_id": clean_identifier(row.get("blind_case_id"), default="blind_case", max_length=160),
                "reviewer_identifier_kind": "blind_case_id_only",
                "case_ref_hidden": True,
                "family_hidden": True,
                "tier_hidden": True,
                "expected_result_hidden": True,
                "gate_result_hidden": True,
                "derived_from_body_or_record_hash": False,
                "body_free": True,
            }
        )
    return out


def _assert_r51_controller_manifest_row(row: Mapping[str, Any]) -> None:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R51_24_CASE_MANIFEST_ROW_FIELD_REFS, source="p7_r51_r4_controller_manifest_row")
    for true_key in ("controller_only", "reviewer_receives_blind_case_id", "body_free"):
        if data.get(true_key) is not True:
            raise ValueError(f"R51 R4 controller row must keep {true_key}=True")
    for false_key in (
        "reviewer_receives_case_ref_id",
        "reviewer_receives_family",
        "reviewer_receives_subscription_tier",
        "reviewer_receives_expected_result",
        "reviewer_receives_gate_result",
        "blind_case_id_derived_from_body_or_record_hash",
        "body_full_packet_materialized_here",
        "local_reviewer_payload_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R51 R4 controller row must keep {false_key}=False")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r51_r4_controller_manifest_row")


def _assert_r51_reviewer_facing_case_index_row(row: Mapping[str, Any]) -> None:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R51_REVIEWER_FACING_CASE_INDEX_ROW_FIELD_REFS, source="p7_r51_r4_reviewer_case_index_row")
    for true_key in ("case_ref_hidden", "family_hidden", "tier_hidden", "expected_result_hidden", "gate_result_hidden", "body_free"):
        if data.get(true_key) is not True:
            raise ValueError(f"R51 R4 reviewer index row must keep {true_key}=True")
    if data.get("derived_from_body_or_record_hash") is not False:
        raise ValueError("R51 R4 reviewer index row must not derive ids from body or record hash")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r51_r4_reviewer_case_index_row")


def _r51_r4_matrix_from_input(
    *,
    envelope: Mapping[str, Any],
    case_matrix: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if case_matrix is not None:
        matrix = safe_mapping(case_matrix)
        assert_p7_r48_p5_first_formal_review_case_matrix_contract(matrix)
        return matrix
    if envelope.get("envelope_status") != "READY_FOR_24_CASE_MANIFEST_FREEZE":
        return None
    matrix = build_p7_r48_p5_first_formal_review_case_matrix(
        review_session_id=envelope.get("review_session_id"),
        session_short_ref="r51s000",
        material_id="p7_r51_r4_inherited_r48_24_case_matrix_source",
    )
    assert_p7_r48_p5_first_formal_review_case_matrix_contract(matrix)
    return matrix


def build_p7_r51_24_case_manifest_freeze_bodyfree(
    *,
    actual_review_session_envelope: Mapping[str, Any] | None = None,
    r3_actual_review_session_envelope: Mapping[str, Any] | None = None,
    case_matrix: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r51_24_case_manifest_freeze_bodyfree",
) -> dict[str, Any]:
    """Build R51-4 body-free 24-case manifest freeze.

    This freezes controller rows and a reviewer-facing blind index only.  It
    never writes body-full packets, reviewer forms, paths, hashes, or review
    results.
    """

    if actual_review_session_envelope is not None and r3_actual_review_session_envelope is not None:
        raise ValueError("provide only one R51-3 envelope value")
    r3 = (
        safe_mapping(actual_review_session_envelope)
        if actual_review_session_envelope is not None
        else safe_mapping(r3_actual_review_session_envelope)
        if r3_actual_review_session_envelope is not None
        else build_p7_r51_actual_review_session_envelope_bodyfree()
    )
    assert_p7_r51_actual_review_session_envelope_bodyfree_contract(r3)
    envelope_ready = r3.get("envelope_status") == "READY_FOR_24_CASE_MANIFEST_FREEZE"
    matrix = _r51_r4_matrix_from_input(envelope=r3, case_matrix=case_matrix)
    raw_rows = [safe_mapping(row) for row in (safe_mapping(matrix).get("case_rows") if matrix else [])]
    matrix_ready = bool(matrix) and _r51_manifest_minimums_satisfied(raw_rows)
    ids_ready = matrix_ready and _r51_unique_non_empty(_r51_case_refs(raw_rows, "blind_case_id")) and _r51_unique_non_empty(_r51_case_refs(raw_rows, "case_ref_id")) and _r51_unique_non_empty(_r51_case_refs(raw_rows, "packet_ref_id"))
    separated = ids_ready and set(_r51_case_refs(raw_rows, "blind_case_id")).isdisjoint(set(_r51_case_refs(raw_rows, "case_ref_id")))
    ready = envelope_ready and matrix_ready and ids_ready and separated

    blockers = dedupe_identifiers(r3.get("execution_blocker_ids") or [], limit=40, max_length=140)
    reason_refs: list[str] = []
    if not envelope_ready:
        reason_refs.append("r51_3_session_envelope_not_ready")
    if envelope_ready and not matrix_ready:
        reason_refs.append("r51_24_case_manifest_incomplete")
        blockers.append("r51_case_manifest_incomplete")
    if envelope_ready and matrix_ready and not ids_ready:
        reason_refs.append("r51_24_case_ids_not_unique")
        blockers.append("r51_case_manifest_incomplete")
    if envelope_ready and matrix_ready and ids_ready and not separated:
        reason_refs.append("r51_blind_case_id_case_ref_not_separated")
        blockers.append("r51_blind_case_id_case_ref_boundary_violation")
    blockers = dedupe_identifiers(blockers, limit=40, max_length=140)
    rows = raw_rows if ready else []
    family_counts = _r51_count_by(rows, "family")
    role_counts = _r51_count_by(rows, "case_role")
    tier_counts = _r51_count_by(rows, "subscription_tier_ref")
    blind_ids = _r51_case_refs(rows, "blind_case_id")
    case_refs = _r51_case_refs(rows, "case_ref_id")
    packet_refs = _r51_case_refs(rows, "packet_ref_id")
    manifest = {
        "schema_version": P7_R51_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R51_STEP,
        "scope": P7_R51_SCOPE,
        "policy_kind": P7_R51_POLICY_KIND,
        "policy_section": "R51-4_24_case_manifest_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r51_24_case_manifest_freeze_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r3.get("review_session_id"), default=P7_R51_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_session_status": "R51_24_CASE_MANIFEST_READY" if ready else "PRECHECK_BLOCKED",
        "manifest_status": "READY_FOR_LOCAL_ONLY_PACKET_GENERATION_REQUEST" if ready else ("BLOCKED_BY_CASE_MATRIX_CONTRACT" if envelope_ready else "BLOCKED_BY_R51_3_ENVELOPE"),
        "manifest_reason_refs": ["r51_24_case_manifest_frozen"] if ready else dedupe_identifiers(reason_refs, limit=20, max_length=140),
        "r3_envelope_schema_version": P7_R51_ACTUAL_REVIEW_SESSION_ENVELOPE_SCHEMA_VERSION,
        "r3_envelope_ref": clean_identifier(r3.get("material_id"), default="p7_r51_actual_review_session_envelope_bodyfree", max_length=180),
        "envelope_status": clean_identifier(r3.get("envelope_status"), default="BLOCKED_BY_R51_2_PREFLIGHT", max_length=80),
        "r48_case_matrix_schema_version": P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION,
        "r48_case_matrix_ref": clean_identifier(safe_mapping(matrix).get("material_id"), default="not_frozen", max_length=180),
        "matrix_kind": "p5_24_case_first_formal_review_matrix" if ready else "not_frozen",
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "case_count": len(rows),
        "case_rows": rows,
        "controller_manifest_rows": _controller_manifest_rows_from_r51_case_rows(rows),
        "reviewer_facing_case_index_rows": _reviewer_facing_case_index_rows_from_r51_case_rows(rows),
        "family_case_counts": family_counts,
        "case_role_counts": role_counts,
        "subscription_tier_ref_counts": tier_counts,
        "owned_history_positive_case_count": sum(role_counts.get(role, 0) for role in P7_R48_P5_POSITIVE_CASE_ROLE_REFS),
        "boundary_case_count": sum(family_counts.get(family, 0) for family in P7_R48_P5_BOUNDARY_FAMILY_REFS),
        "low_information_boundary_case_count": family_counts.get("low_information_history_not_eligible", 0),
        "free_tier_boundary_case_count": family_counts.get("free_tier_history_present_not_allowed", 0),
        "minimums_satisfied": ready and _r51_manifest_minimums_satisfied(rows),
        "blind_case_ids_unique": ready and _r51_unique_non_empty(blind_ids),
        "case_ref_ids_unique": ready and _r51_unique_non_empty(case_refs),
        "packet_ref_ids_unique": ready and _r51_unique_non_empty(packet_refs),
        "blind_case_id_case_ref_separated": ready and set(blind_ids).isdisjoint(set(case_refs)),
        "reviewer_facing_family_exposed": False,
        "reviewer_facing_tier_exposed": False,
        "reviewer_facing_expected_result_exposed": False,
        "controller_keeps_family_tier_expected_refs": ready,
        "reviewer_receives_blind_case_id_only": ready,
        "body_full_packet_materialized_here": False,
        "local_reviewer_payload_materialized_here": False,
        "body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "p5_actual_review_still_not_run": True,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "r0_current_source_r50_handoff_refrozen": True,
        "r1_validation_evidence_r49_timeout_handling_frozen": True,
        "r2_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r3_actual_review_session_envelope_created": True,
        "r4_24_case_manifest_freeze_built": ready,
        "implemented_steps": list(P7_R51_R4_IMPLEMENTED_STEPS) if ready else list(P7_R51_R3_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R51_R4_NOT_YET_IMPLEMENTED_STEPS) if ready else list(P7_R51_R3_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R51_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R51_R4_NEXT_REQUIRED_STEP_REF if ready else P7_R51_R4_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r51_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r51_24_case_manifest_freeze_bodyfree_contract(manifest)
    return manifest


def assert_p7_r51_24_case_manifest_freeze_bodyfree_contract(manifest: Mapping[str, Any]) -> bool:
    data = safe_mapping(manifest)
    _assert_required_fields(data, required=P7_R51_24_CASE_MANIFEST_FREEZE_REQUIRED_FIELD_REFS, source="p7_r51_r4_24_case_manifest_freeze_bodyfree")
    _assert_body_free_common(data, schema_version=P7_R51_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION, source="p7_r51_r4_24_case_manifest_freeze_bodyfree")
    if data.get("policy_section") != "R51-4_24_case_manifest_freeze":
        raise ValueError("R51 R4 policy section changed")
    if data.get("manifest_status") not in P7_R51_MANIFEST_STATUS_REFS:
        raise ValueError("R51 R4 manifest status changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R51 R4 open blockers must match execution blockers")
    unknown_blockers = sorted(set(blockers) - set(P7_R51_EXECUTION_BLOCKER_ID_REFS))
    if unknown_blockers:
        raise ValueError(f"R51 R4 execution blocker ids are not canonical: {unknown_blockers[:4]}")
    rows = [safe_mapping(row) for row in (data.get("case_rows") or [])]
    ready = data.get("manifest_status") == "READY_FOR_LOCAL_ONLY_PACKET_GENERATION_REQUEST"
    for false_key in ("reviewer_facing_family_exposed", "reviewer_facing_tier_exposed", "reviewer_facing_expected_result_exposed", "body_full_packet_materialized_here", "local_reviewer_payload_materialized_here", "body_full_packet_generated_here", "actual_human_review_run_here"):
        if data.get(false_key) is not False:
            raise ValueError(f"R51 R4 must keep {false_key}=False")
    if data.get("p5_actual_review_still_not_run") is not True:
        raise ValueError("R51 R4 must not claim actual P5 review ran")
    if ready:
        if data.get("review_session_status") != "R51_24_CASE_MANIFEST_READY":
            raise ValueError("R51 R4 ready status changed")
        if len(rows) != P7_R51_REQUIRED_CASE_COUNT or data.get("case_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R51 R4 ready manifest must freeze exactly 24 cases")
        for row in rows:
            _assert_r51_case_row(row)
        controller_rows = [safe_mapping(row) for row in (data.get("controller_manifest_rows") or [])]
        reviewer_rows = [safe_mapping(row) for row in (data.get("reviewer_facing_case_index_rows") or [])]
        if len(controller_rows) != P7_R51_REQUIRED_CASE_COUNT or len(reviewer_rows) != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R51 R4 manifest rows must match 24 cases")
        for row in controller_rows:
            _assert_r51_controller_manifest_row(row)
        for row in reviewer_rows:
            _assert_r51_reviewer_facing_case_index_row(row)
        blind_ids = _r51_case_refs(rows, "blind_case_id")
        case_refs = _r51_case_refs(rows, "case_ref_id")
        packet_refs = _r51_case_refs(rows, "packet_ref_id")
        for key, values in (("blind_case_ids_unique", blind_ids), ("case_ref_ids_unique", case_refs), ("packet_ref_ids_unique", packet_refs)):
            if data.get(key) is not True or not _r51_unique_non_empty(values):
                raise ValueError(f"R51 R4 {key} failed")
        if data.get("blind_case_id_case_ref_separated") is not True or not set(blind_ids).isdisjoint(set(case_refs)):
            raise ValueError("R51 R4 blind ids and case refs must be separated")
        if data.get("family_case_counts") != _r51_count_by(rows, "family"):
            raise ValueError("R51 R4 family counts changed")
        if data.get("case_role_counts") != _r51_count_by(rows, "case_role"):
            raise ValueError("R51 R4 role counts changed")
        if data.get("subscription_tier_ref_counts") != _r51_count_by(rows, "subscription_tier_ref"):
            raise ValueError("R51 R4 tier counts changed")
        for family, expected_count, _case_role in P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION:
            if data["family_case_counts"].get(family, 0) != expected_count:
                raise ValueError("R51 R4 family distribution changed")
        if data.get("boundary_case_count") != 4 or data.get("low_information_boundary_case_count") != 2 or data.get("free_tier_boundary_case_count") != 2:
            raise ValueError("R51 R4 boundary cases changed")
        if data.get("minimums_satisfied") is not True or not _r51_manifest_minimums_satisfied(rows):
            raise ValueError("R51 R4 ready manifest minimums not satisfied")
        if data.get("controller_keeps_family_tier_expected_refs") is not True:
            raise ValueError("R51 R4 controller must keep family/tier refs body-free")
        if data.get("reviewer_receives_blind_case_id_only") is not True:
            raise ValueError("R51 R4 reviewer must receive blind_case_id only")
        if blockers:
            raise ValueError("R51 R4 ready manifest must not carry blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R51_R4_IMPLEMENTED_STEPS:
            raise ValueError("R51 R4 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R51_R4_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R51 R4 not-yet steps changed")
        if data.get("next_required_step") != P7_R51_R4_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R4 ready manifest must point to R51-5")
    else:
        if rows or data.get("case_count") != 0:
            raise ValueError("R51 R4 blocked manifest must not freeze case rows")
        if data.get("r4_24_case_manifest_freeze_built") is not False:
            raise ValueError("R51 R4 blocked manifest must not claim R51-4 built")
        if not data.get("manifest_reason_refs"):
            raise ValueError("R51 R4 blocked manifest must carry reasons")
        if data.get("next_required_step") != P7_R51_R4_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R4 blocked manifest must point to envelope/manifest resolution")
    return True


def _packet_request_rows_from_r51_manifest(manifest: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row_raw in safe_mapping(manifest).get("case_rows") or []:
        row = safe_mapping(row_raw)
        rows.append(
            {
                "blind_case_id": clean_identifier(row.get("blind_case_id"), default="blind_case", max_length=160),
                "case_ref_id": clean_identifier(row.get("case_ref_id"), default="case_ref", max_length=160),
                "packet_ref_id": clean_identifier(row.get("packet_ref_id"), default="packet_ref", max_length=160),
                "packet_kind": P7_R51_PACKET_KIND,
                "review_kind": P7_R51_REVIEW_KIND,
                "request_status_ref": "REQUEST_READY_NOT_GENERATED",
                "local_only_required": True,
                "must_not_export": True,
                "disposal_required": True,
                "body_full_packet_materialized_here": False,
                "local_file_written_here": False,
                "local_absolute_path_included": False,
                "body_content_hash_stored_here": False,
                "body_free": True,
            }
        )
    return rows


def _assert_r51_packet_request_row(row: Mapping[str, Any]) -> None:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R51_PACKET_GENERATION_REQUEST_ROW_FIELD_REFS, source="p7_r51_r5_packet_generation_request_row")
    for true_key in ("local_only_required", "must_not_export", "disposal_required", "body_free"):
        if data.get(true_key) is not True:
            raise ValueError(f"R51 R5 packet request row must keep {true_key}=True")
    for false_key in ("body_full_packet_materialized_here", "local_file_written_here", "local_absolute_path_included", "body_content_hash_stored_here"):
        if data.get(false_key) is not False:
            raise ValueError(f"R51 R5 packet request row must keep {false_key}=False")
    if data.get("packet_kind") != P7_R51_PACKET_KIND or data.get("review_kind") != P7_R51_REVIEW_KIND:
        raise ValueError("R51 R5 packet request row refs changed")
    if data.get("request_status_ref") != "REQUEST_READY_NOT_GENERATED":
        raise ValueError("R51 R5 packet request row must not claim generation")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r51_r5_packet_generation_request_row")


def build_p7_r51_local_only_body_full_packet_generation_request_bodyfree(
    *,
    case_manifest_freeze: Mapping[str, Any] | None = None,
    r4_24_case_manifest_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r51_local_only_body_full_packet_generation_request_bodyfree",
) -> dict[str, Any]:
    """Build R51-5 body-free generation request.

    This is only a controller request for a later local-only packet generator.
    It does not materialize body-full packet files, paths, hashes, reviewer
    forms, reviewer notes, review ratings, or question observation rows.
    """

    if case_manifest_freeze is not None and r4_24_case_manifest_freeze is not None:
        raise ValueError("provide only one R51-4 manifest value")
    r4 = (
        safe_mapping(case_manifest_freeze)
        if case_manifest_freeze is not None
        else safe_mapping(r4_24_case_manifest_freeze)
        if r4_24_case_manifest_freeze is not None
        else build_p7_r51_24_case_manifest_freeze_bodyfree()
    )
    assert_p7_r51_24_case_manifest_freeze_bodyfree_contract(r4)
    manifest_ready = r4.get("manifest_status") == "READY_FOR_LOCAL_ONLY_PACKET_GENERATION_REQUEST"
    rows = _packet_request_rows_from_r51_manifest(r4) if manifest_ready else []
    blockers = dedupe_identifiers(r4.get("execution_blocker_ids") or [], limit=40, max_length=140)
    if not manifest_ready and "r51_body_full_packet_generation_request_blocked" not in blockers:
        blockers = dedupe_identifiers([*blockers, "r51_body_full_packet_generation_request_blocked"], limit=40, max_length=140)
    blind_ids = _r51_case_refs(rows, "blind_case_id")
    case_refs = _r51_case_refs(rows, "case_ref_id")
    packet_refs = _r51_case_refs(rows, "packet_ref_id")
    ready = manifest_ready and len(rows) == P7_R51_REQUIRED_CASE_COUNT and _r51_unique_non_empty(blind_ids) and _r51_unique_non_empty(case_refs) and _r51_unique_non_empty(packet_refs)
    if manifest_ready and not ready and "r51_case_material_missing" not in blockers:
        blockers = dedupe_identifiers([*blockers, "r51_case_material_missing"], limit=40, max_length=140)

    request = {
        "schema_version": P7_R51_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R51_STEP,
        "scope": P7_R51_SCOPE,
        "policy_kind": P7_R51_POLICY_KIND,
        "policy_section": "R51-5_local_only_body_full_packet_generation_request",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r51_local_only_body_full_packet_generation_request_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r4.get("review_session_id"), default=P7_R51_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_session_status": "R51_BODY_FULL_PACKET_GENERATION_REQUEST_READY" if ready else "PRECHECK_BLOCKED",
        "generation_request_status": "READY_FOR_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION" if ready else "BLOCKED_BY_R51_4_MANIFEST",
        "generation_request_reason_refs": ["r51_local_only_body_full_packet_generation_request_ready_not_generated"] if ready else ["r51_4_manifest_not_ready_for_generation_request"],
        "r4_manifest_schema_version": P7_R51_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION,
        "r4_manifest_ref": clean_identifier(r4.get("material_id"), default="p7_r51_24_case_manifest_freeze_bodyfree", max_length=180),
        "manifest_status": clean_identifier(r4.get("manifest_status"), default="BLOCKED_BY_R51_3_ENVELOPE", max_length=100),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "case_count": r4.get("case_count") if ready else 0,
        "packet_generation_request_case_count": len(rows),
        "packet_generation_request_row_count": len(rows),
        "packet_generation_request_rows": rows,
        "requested_packet_ref_count": len(packet_refs),
        "blind_case_id_count": len(blind_ids),
        "packet_ref_ids_unique": ready and _r51_unique_non_empty(packet_refs),
        "case_ref_ids_unique": ready and _r51_unique_non_empty(case_refs),
        "body_full_reviewer_packet_local_only_schema_version_ref": P7_R51_BODY_FULL_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION,
        "body_full_packet_local_only_required_field_refs": list(P7_R51_BODY_FULL_PACKET_LOCAL_ONLY_REQUIRED_FIELD_REFS),
        "review_prompt_version": P7_R51_REVIEW_PROMPT_VERSION,
        "reviewer_visible_field_refs": list(P7_R50_REVIEWER_VISIBLE_FIELD_REFS),
        "reviewer_hidden_field_refs": list(P7_R50_REVIEWER_HIDDEN_FIELD_REFS),
        "local_root_ref": P7_R47_STORAGE_ROOT_REF if ready else "not_authorized",
        "root_path_exposed": False,
        "local_absolute_path_included": False,
        "disposal_plan_ref": "carried_from_r51_3_session_envelope_via_r51_4_manifest" if ready else "not_ready",
        "disposal_plan_ready": ready,
        "body_full_packet_retention_max_hours": P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
        "reviewer_notes_retention_after_rating_finalized_max_hours": P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
        "local_only_required": ready,
        "must_not_export": ready,
        "disposal_required": ready,
        "local_only_body_full_generation_allowed": ready,
        "local_only_body_full_packet_generation_request_created_here": ready,
        "body_full_packet_generation_request_created_here": ready,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "local_file_ops_helper_created_here": False,
        "body_full_packet_writer_created_here": False,
        "body_full_packet_local_only_schema_file_created_here": False,
        "generation_event_bodyfree_only": True,
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
        "r0_current_source_r50_handoff_refrozen": True,
        "r1_validation_evidence_r49_timeout_handling_frozen": True,
        "r2_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r3_actual_review_session_envelope_created": True,
        "r4_24_case_manifest_freeze_built": r4.get("r4_24_case_manifest_freeze_built") is True,
        "r5_local_only_body_full_packet_generation_request_built": ready,
        "implemented_steps": list(P7_R51_R5_IMPLEMENTED_STEPS) if ready else list(P7_R51_R4_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R51_R5_NOT_YET_IMPLEMENTED_STEPS) if ready else list(P7_R51_R4_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R51_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R51_R5_NEXT_REQUIRED_STEP_REF if ready else P7_R51_R5_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r51_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r51_local_only_body_full_packet_generation_request_bodyfree_contract(request)
    return request


def assert_p7_r51_local_only_body_full_packet_generation_request_bodyfree_contract(request: Mapping[str, Any]) -> bool:
    data = safe_mapping(request)
    _assert_required_fields(data, required=P7_R51_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_REQUIRED_FIELD_REFS, source="p7_r51_r5_local_only_body_full_packet_generation_request_bodyfree")
    _assert_body_free_common(data, schema_version=P7_R51_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION, source="p7_r51_r5_local_only_body_full_packet_generation_request_bodyfree")
    if data.get("policy_section") != "R51-5_local_only_body_full_packet_generation_request":
        raise ValueError("R51 R5 policy section changed")
    if data.get("generation_request_status") not in P7_R51_PACKET_GENERATION_REQUEST_STATUS_REFS:
        raise ValueError("R51 R5 generation request status changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R51 R5 open blockers must match execution blockers")
    unknown_blockers = sorted(set(blockers) - set(P7_R51_EXECUTION_BLOCKER_ID_REFS))
    if unknown_blockers:
        raise ValueError(f"R51 R5 execution blocker ids are not canonical: {unknown_blockers[:4]}")
    rows = [safe_mapping(row) for row in (data.get("packet_generation_request_rows") or [])]
    ready = data.get("generation_request_status") == "READY_FOR_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION"
    for false_key in (
        "root_path_exposed",
        "local_absolute_path_included",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
        "local_file_ops_helper_created_here",
        "body_full_packet_writer_created_here",
        "body_full_packet_local_only_schema_file_created_here",
        "local_packet_exported_allowed",
        "content_hash_of_body_stored_allowed",
        "export_candidate_refs_stored_here",
        "export_candidate_body_stored_here",
        "question_text_created_here",
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R51 R5 must keep {false_key}=False")
    if data.get("generation_event_bodyfree_only") is not True or data.get("p5_actual_review_still_not_run") is not True:
        raise ValueError("R51 R5 must stay body-free and pre-review")
    if data.get("body_full_reviewer_packet_local_only_schema_version_ref") != P7_R51_BODY_FULL_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION:
        raise ValueError("R51 R5 packet schema ref changed")
    if tuple(data.get("body_full_packet_local_only_required_field_refs") or ()) != P7_R51_BODY_FULL_PACKET_LOCAL_ONLY_REQUIRED_FIELD_REFS:
        raise ValueError("R51 R5 local-only packet field refs changed")
    if tuple(data.get("reviewer_visible_field_refs") or ()) != P7_R50_REVIEWER_VISIBLE_FIELD_REFS:
        raise ValueError("R51 R5 reviewer visible field refs changed")
    if tuple(data.get("reviewer_hidden_field_refs") or ()) != P7_R50_REVIEWER_HIDDEN_FIELD_REFS:
        raise ValueError("R51 R5 reviewer hidden field refs changed")
    if data.get("body_full_packet_retention_max_hours") != P7_R47_BODY_FULL_PACKET_RETENTION_HOURS:
        raise ValueError("R51 R5 body-full retention window changed")
    if data.get("reviewer_notes_retention_after_rating_finalized_max_hours") != P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS:
        raise ValueError("R51 R5 reviewer notes retention window changed")
    if ready:
        if data.get("review_session_status") != "R51_BODY_FULL_PACKET_GENERATION_REQUEST_READY":
            raise ValueError("R51 R5 ready status changed")
        if len(rows) != P7_R51_REQUIRED_CASE_COUNT or data.get("packet_generation_request_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R51 R5 ready request must contain 24 request rows")
        for row in rows:
            _assert_r51_packet_request_row(row)
        blind_ids = _r51_case_refs(rows, "blind_case_id")
        case_refs = _r51_case_refs(rows, "case_ref_id")
        packet_refs = _r51_case_refs(rows, "packet_ref_id")
        if data.get("blind_case_id_count") != len(blind_ids) or data.get("requested_packet_ref_count") != len(packet_refs):
            raise ValueError("R51 R5 id counts must match request rows")
        if data.get("packet_ref_ids_unique") is not True or not _r51_unique_non_empty(packet_refs):
            raise ValueError("R51 R5 packet refs must be unique")
        if data.get("case_ref_ids_unique") is not True or not _r51_unique_non_empty(case_refs):
            raise ValueError("R51 R5 case refs must be unique")
        for true_key in (
            "disposal_plan_ready",
            "local_only_required",
            "must_not_export",
            "disposal_required",
            "local_only_body_full_generation_allowed",
            "local_only_body_full_packet_generation_request_created_here",
            "body_full_packet_generation_request_created_here",
            "r4_24_case_manifest_freeze_built",
            "r5_local_only_body_full_packet_generation_request_built",
        ):
            if data.get(true_key) is not True:
                raise ValueError(f"R51 R5 ready request requires {true_key}=True")
        if data.get("local_root_ref") != P7_R47_STORAGE_ROOT_REF:
            raise ValueError("R51 R5 ready request must expose only abstract local root ref")
        if blockers:
            raise ValueError("R51 R5 ready request must not carry blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R51_R5_IMPLEMENTED_STEPS:
            raise ValueError("R51 R5 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R51_R5_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R51 R5 not-yet steps changed")
        if data.get("next_required_step") != P7_R51_R5_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R5 ready request must point to R51-6")
    else:
        if rows or data.get("packet_generation_request_row_count") != 0:
            raise ValueError("R51 R5 blocked request must not create packet request rows")
        if data.get("local_only_body_full_packet_generation_request_created_here") is not False:
            raise ValueError("R51 R5 blocked request must not create generation request")
        if data.get("next_required_step") != P7_R51_R5_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R5 blocked request must point to manifest resolution")
    return True



def _packet_completion_scan_rows_from_r51_request(request: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row_raw in safe_mapping(request).get("packet_generation_request_rows") or []:
        row = safe_mapping(row_raw)
        rows.append(
            {
                "blind_case_id": clean_identifier(row.get("blind_case_id"), default="blind_case", max_length=160),
                "case_ref_id": clean_identifier(row.get("case_ref_id"), default="case_ref", max_length=160),
                "packet_ref_id": clean_identifier(row.get("packet_ref_id"), default="packet_ref", max_length=160),
                "packet_kind": P7_R51_PACKET_KIND,
                "review_kind": P7_R51_REVIEW_KIND,
                "completion_status_ref": "PACKET_PRESENT_LOCAL_ONLY",
                "packet_present_local_only": True,
                "required_field_refs_present": True,
                "local_only_marker_present": True,
                "must_not_export_marker_present": True,
                "disposal_required_marker_present": True,
                "body_full_packet_materialized_here": False,
                "body_full_packet_body_copied_here": False,
                "local_absolute_path_included": False,
                "body_content_hash_stored_here": False,
                "export_candidate_detected": False,
                "export_denylist_violation_detected": False,
                "body_free": True,
            }
        )
    return rows


def _normalize_packet_completion_scan_rows(rows: Sequence[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row_raw in rows or []:
        row = safe_mapping(row_raw)
        packet_present = _safe_bool(row.get("packet_present_local_only"))
        required_fields = _safe_bool(row.get("required_field_refs_present"))
        local_only_marker = _safe_bool(row.get("local_only_marker_present"))
        must_not_export = _safe_bool(row.get("must_not_export_marker_present"))
        disposal_required = _safe_bool(row.get("disposal_required_marker_present"))
        export_violation = _safe_bool(row.get("export_denylist_violation_detected")) or _safe_bool(row.get("export_candidate_detected"))
        if not packet_present:
            status = "PACKET_MISSING"
        elif export_violation:
            status = "PACKET_EXPORT_DENYLIST_VIOLATION"
        elif not (required_fields and local_only_marker and must_not_export and disposal_required):
            status = "PACKET_INCOMPLETE"
        else:
            status = "PACKET_PRESENT_LOCAL_ONLY"
        normalized.append(
            {
                "blind_case_id": clean_identifier(row.get("blind_case_id"), default="blind_case", max_length=160),
                "case_ref_id": clean_identifier(row.get("case_ref_id"), default="case_ref", max_length=160),
                "packet_ref_id": clean_identifier(row.get("packet_ref_id"), default="packet_ref", max_length=160),
                "packet_kind": P7_R51_PACKET_KIND,
                "review_kind": P7_R51_REVIEW_KIND,
                "completion_status_ref": status,
                "packet_present_local_only": packet_present,
                "required_field_refs_present": required_fields,
                "local_only_marker_present": local_only_marker,
                "must_not_export_marker_present": must_not_export,
                "disposal_required_marker_present": disposal_required,
                "body_full_packet_materialized_here": False,
                "body_full_packet_body_copied_here": False,
                "local_absolute_path_included": False,
                "body_content_hash_stored_here": False,
                "export_candidate_detected": _safe_bool(row.get("export_candidate_detected")),
                "export_denylist_violation_detected": export_violation,
                "body_free": True,
            }
        )
    return normalized


def _assert_r51_packet_completion_scan_row(row: Mapping[str, Any]) -> None:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R51_PACKET_COMPLETENESS_SCAN_ROW_FIELD_REFS, source="p7_r51_r6_packet_completion_scan_row")
    if data.get("body_free") is not True:
        raise ValueError("R51 R6 packet scan row must be body-free")
    if data.get("completion_status_ref") not in P7_R51_PACKET_COMPLETION_SCAN_ROW_STATUS_REFS:
        raise ValueError("R51 R6 packet scan row status changed")
    if data.get("packet_kind") != P7_R51_PACKET_KIND or data.get("review_kind") != P7_R51_REVIEW_KIND:
        raise ValueError("R51 R6 packet scan row refs changed")
    for false_key in (
        "body_full_packet_materialized_here",
        "body_full_packet_body_copied_here",
        "local_absolute_path_included",
        "body_content_hash_stored_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R51 R6 packet scan row must keep {false_key}=False")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r51_r6_packet_completion_scan_row")


def build_p7_r51_body_full_packet_completeness_export_denylist_scan_bodyfree(
    *,
    local_only_body_full_packet_generation_request: Mapping[str, Any] | None = None,
    r5_local_only_body_full_packet_generation_request: Mapping[str, Any] | None = None,
    packet_completion_rows: Sequence[Mapping[str, Any]] | None = None,
    export_candidate_refs: Sequence[Any] | Any | None = None,
    material_id: Any = "p7_r51_body_full_packet_completeness_export_denylist_scan_bodyfree",
) -> dict[str, Any]:
    """Build R51-6 body-free completeness/export-denylist scan evidence.

    This scan validates abstract local-only packet evidence.  It does not read,
    copy, hash, write, export, or include body-full packet contents or local
    paths.
    """

    if local_only_body_full_packet_generation_request is not None and r5_local_only_body_full_packet_generation_request is not None:
        raise ValueError("provide only one R51-5 packet generation request value")
    r5 = (
        safe_mapping(local_only_body_full_packet_generation_request)
        if local_only_body_full_packet_generation_request is not None
        else safe_mapping(r5_local_only_body_full_packet_generation_request)
        if r5_local_only_body_full_packet_generation_request is not None
        else build_p7_r51_local_only_body_full_packet_generation_request_bodyfree()
    )
    assert_p7_r51_local_only_body_full_packet_generation_request_bodyfree_contract(r5)
    request_ready = r5.get("generation_request_status") == "READY_FOR_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION"
    raw_rows = (
        _normalize_packet_completion_scan_rows(packet_completion_rows)
        if packet_completion_rows is not None
        else _packet_completion_scan_rows_from_r51_request(r5)
        if request_ready
        else []
    )
    for row in raw_rows:
        _assert_r51_packet_completion_scan_row(row)

    expected_request_rows = [safe_mapping(row) for row in (r5.get("packet_generation_request_rows") or [])] if request_ready else []
    expected_packet_refs = _r51_case_refs(expected_request_rows, "packet_ref_id")
    expected_case_refs = _r51_case_refs(expected_request_rows, "case_ref_id")
    expected_blind_ids = _r51_case_refs(expected_request_rows, "blind_case_id")
    present_rows = [row for row in raw_rows if row.get("packet_present_local_only") is True]
    present_packet_refs = _r51_case_refs(present_rows, "packet_ref_id")
    scan_packet_refs = _r51_case_refs(raw_rows, "packet_ref_id")
    scan_case_refs = _r51_case_refs(raw_rows, "case_ref_id")
    scan_blind_ids = _r51_case_refs(raw_rows, "blind_case_id")
    expected_ref_set = set(expected_packet_refs)
    present_ref_set = set(present_packet_refs)
    missing_ref_count = len(expected_ref_set - present_ref_set) if request_ready else 0
    incomplete_rows = [
        row for row in raw_rows
        if row.get("completion_status_ref") in {"PACKET_MISSING", "PACKET_INCOMPLETE"}
    ]
    row_export_violation_count = sum(1 for row in raw_rows if row.get("export_denylist_violation_detected") is True)
    checked_count, denied_count, violation_refs = _export_denylist_summary_r51(export_candidate_refs)
    blockers = dedupe_identifiers(r5.get("execution_blocker_ids") or [], limit=40, max_length=140)
    reason_refs: list[str] = []
    if not request_ready:
        reason_refs.append("r51_5_generation_request_not_ready")
        if "r51_body_full_packet_generation_request_blocked" not in blockers:
            blockers.append("r51_body_full_packet_generation_request_blocked")
    if request_ready and len(raw_rows) != P7_R51_REQUIRED_CASE_COUNT:
        reason_refs.append("r51_packet_scan_row_count_not_24")
        blockers.append("r51_body_full_packet_generation_failed")
    if request_ready and missing_ref_count:
        reason_refs.append("r51_required_packet_refs_missing")
        blockers.append("r51_case_material_missing")
    if request_ready and incomplete_rows:
        reason_refs.append("r51_packet_required_fields_or_markers_incomplete")
        blockers.append("r51_body_full_packet_generation_failed")
    if request_ready and (denied_count or row_export_violation_count):
        reason_refs.append("r51_body_full_packet_export_denylist_violation")
        blockers.append("r51_body_full_packet_export_violation")
    blockers = dedupe_identifiers(blockers, limit=40, max_length=140)

    unique_packet_refs = _r51_unique_non_empty(scan_packet_refs)
    unique_case_refs = _r51_unique_non_empty(scan_case_refs)
    unique_blind_ids = _r51_unique_non_empty(scan_blind_ids)
    all_present = request_ready and len(raw_rows) == P7_R51_REQUIRED_CASE_COUNT and missing_ref_count == 0 and set(scan_packet_refs) == expected_ref_set
    all_required_fields = all(row.get("required_field_refs_present") is True for row in raw_rows) and bool(raw_rows)
    all_local_only = all(row.get("local_only_marker_present") is True for row in raw_rows) and bool(raw_rows)
    all_must_not_export = all(row.get("must_not_export_marker_present") is True for row in raw_rows) and bool(raw_rows)
    all_disposal = all(row.get("disposal_required_marker_present") is True for row in raw_rows) and bool(raw_rows)
    ready = (
        request_ready
        and len(raw_rows) == P7_R51_REQUIRED_CASE_COUNT
        and unique_packet_refs
        and unique_case_refs
        and unique_blind_ids
        and all_present
        and all_required_fields
        and all_local_only
        and all_must_not_export
        and all_disposal
        and denied_count == 0
        and row_export_violation_count == 0
        and not blockers
    )
    scan = {
        "schema_version": P7_R51_BODY_FULL_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R51_STEP,
        "scope": P7_R51_SCOPE,
        "policy_kind": P7_R51_POLICY_KIND,
        "policy_section": "R51-6_body_full_packet_completeness_export_denylist_scan",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r51_body_full_packet_completeness_export_denylist_scan_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r5.get("review_session_id"), default=P7_R51_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_session_status": "R51_BODY_FULL_PACKET_COMPLETENESS_SCAN_READY" if ready else "PRECHECK_BLOCKED",
        "packet_completeness_scan_status": "READY_FOR_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE" if ready else ("BLOCKED_BY_R51_5_GENERATION_REQUEST" if not request_ready else "BLOCKED_BY_PACKET_COMPLETENESS_OR_EXPORT_DENYLIST"),
        "packet_completeness_scan_reason_refs": ["r51_body_full_packet_completeness_and_export_denylist_verified_bodyfree"] if ready else dedupe_identifiers(reason_refs, limit=30, max_length=140),
        "r5_generation_request_schema_version": P7_R51_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION,
        "r5_generation_request_ref": clean_identifier(r5.get("material_id"), default="p7_r51_local_only_body_full_packet_generation_request_bodyfree", max_length=180),
        "generation_request_status": clean_identifier(r5.get("generation_request_status"), default="BLOCKED_BY_R51_4_MANIFEST", max_length=120),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "request_row_count": len(expected_request_rows),
        "packet_scan_row_count": len(raw_rows),
        "packet_scan_rows": raw_rows if request_ready else [],
        "expected_packet_ref_count": len(expected_packet_refs),
        "present_packet_ref_count": len(present_packet_refs),
        "missing_packet_ref_count": missing_ref_count,
        "incomplete_packet_ref_count": len(incomplete_rows),
        "required_packet_refs_count": len(expected_packet_refs),
        "present_packet_refs_count": len(present_packet_refs),
        "blind_case_id_count": len(scan_blind_ids),
        "case_ref_id_count": len(scan_case_refs),
        "packet_ref_ids_unique": unique_packet_refs if request_ready else False,
        "case_ref_ids_unique": unique_case_refs if request_ready else False,
        "blind_case_ids_unique": unique_blind_ids if request_ready else False,
        "all_required_packets_present": all_present,
        "all_required_fields_present": all_required_fields,
        "all_local_only_markers_present": all_local_only,
        "all_must_not_export_markers_present": all_must_not_export,
        "all_disposal_required_markers_present": all_disposal,
        "body_full_packet_completeness_verified": ready,
        "export_denylist_patterns": list(P7_R47_EXPORT_DENYLIST_PATTERNS),
        "export_candidate_refs_checked_count": checked_count,
        "denied_export_candidate_count": denied_count,
        "export_denylist_violation_refs": violation_refs,
        "row_export_denylist_violation_count": row_export_violation_count,
        "body_full_packet_export_violation_detected": bool(denied_count or row_export_violation_count),
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
        "r0_current_source_r50_handoff_refrozen": True,
        "r1_validation_evidence_r49_timeout_handling_frozen": True,
        "r2_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r3_actual_review_session_envelope_created": True,
        "r4_24_case_manifest_freeze_built": r5.get("r4_24_case_manifest_freeze_built") is True,
        "r5_local_only_body_full_packet_generation_request_built": r5.get("r5_local_only_body_full_packet_generation_request_built") is True,
        "r6_body_full_packet_completeness_export_denylist_scan_built": ready,
        "implemented_steps": list(P7_R51_R6_IMPLEMENTED_STEPS) if ready else list(P7_R51_R5_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R51_R6_NOT_YET_IMPLEMENTED_STEPS) if ready else list(P7_R51_R5_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R51_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R51_R6_NEXT_REQUIRED_STEP_REF if ready else P7_R51_R6_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r51_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r51_body_full_packet_completeness_export_denylist_scan_bodyfree_contract(scan)
    return scan


def assert_p7_r51_body_full_packet_completeness_export_denylist_scan_bodyfree_contract(scan: Mapping[str, Any]) -> bool:
    data = safe_mapping(scan)
    _assert_required_fields(data, required=P7_R51_BODY_FULL_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_REQUIRED_FIELD_REFS, source="p7_r51_r6_body_full_packet_completeness_export_denylist_scan_bodyfree")
    _assert_body_free_common(data, schema_version=P7_R51_BODY_FULL_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION, source="p7_r51_r6_body_full_packet_completeness_export_denylist_scan_bodyfree")
    if data.get("policy_section") != "R51-6_body_full_packet_completeness_export_denylist_scan":
        raise ValueError("R51 R6 policy section changed")
    if data.get("packet_completeness_scan_status") not in P7_R51_PACKET_COMPLETENESS_SCAN_STATUS_REFS:
        raise ValueError("R51 R6 scan status changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R51 R6 open blockers must match execution blockers")
    unknown_blockers = sorted(set(blockers) - set(P7_R51_EXECUTION_BLOCKER_ID_REFS))
    if unknown_blockers:
        raise ValueError(f"R51 R6 execution blocker ids are not canonical: {unknown_blockers[:4]}")
    rows = [safe_mapping(row) for row in (data.get("packet_scan_rows") or [])]
    for row in rows:
        _assert_r51_packet_completion_scan_row(row)
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
            raise ValueError(f"R51 R6 must keep {false_key}=False")
    ready = data.get("packet_completeness_scan_status") == "READY_FOR_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE"
    if ready:
        if data.get("review_session_status") != "R51_BODY_FULL_PACKET_COMPLETENESS_SCAN_READY":
            raise ValueError("R51 R6 ready status changed")
        if len(rows) != P7_R51_REQUIRED_CASE_COUNT or data.get("packet_scan_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R51 R6 ready scan must contain 24 scan rows")
        for true_key in (
            "packet_ref_ids_unique",
            "case_ref_ids_unique",
            "blind_case_ids_unique",
            "all_required_packets_present",
            "all_required_fields_present",
            "all_local_only_markers_present",
            "all_must_not_export_markers_present",
            "all_disposal_required_markers_present",
            "body_full_packet_completeness_verified",
            "p5_actual_review_still_not_run",
            "r5_local_only_body_full_packet_generation_request_built",
            "r6_body_full_packet_completeness_export_denylist_scan_built",
        ):
            if data.get(true_key) is not True:
                raise ValueError(f"R51 R6 ready scan requires {true_key}=True")
        if data.get("body_full_packet_export_violation_detected") is not False or data.get("denied_export_candidate_count") != 0:
            raise ValueError("R51 R6 ready scan must have no export violation")
        if blockers:
            raise ValueError("R51 R6 ready scan must not carry blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R51_R6_IMPLEMENTED_STEPS:
            raise ValueError("R51 R6 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R51_R6_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R51 R6 not-yet steps changed")
        if data.get("next_required_step") != P7_R51_R6_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R6 ready scan must point to R51-7")
    else:
        if data.get("body_full_packet_completeness_verified") is not False:
            raise ValueError("R51 R6 blocked scan cannot verify completeness")
        if data.get("r6_body_full_packet_completeness_export_denylist_scan_built") is not False:
            raise ValueError("R51 R6 blocked scan cannot claim R51-6 built")
        if data.get("next_required_step") != P7_R51_R6_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R6 blocked scan must point to packet scan resolution")
    return True


def build_p7_r51_reviewer_instruction_rating_form_freeze_bodyfree(
    *,
    body_full_packet_completeness_export_denylist_scan: Mapping[str, Any] | None = None,
    r6_body_full_packet_completeness_export_denylist_scan: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r51_reviewer_instruction_rating_form_freeze_bodyfree",
) -> dict[str, Any]:
    """Build R51-7 body-free reviewer instruction/rating-form freeze.

    The freeze contains only static/body-free instruction and scoring metadata;
    it does not expose case bodies, write reviewer forms, run review, or create
    rating/question observation rows.
    """

    if body_full_packet_completeness_export_denylist_scan is not None and r6_body_full_packet_completeness_export_denylist_scan is not None:
        raise ValueError("provide only one R51-6 packet scan value")
    r6 = (
        safe_mapping(body_full_packet_completeness_export_denylist_scan)
        if body_full_packet_completeness_export_denylist_scan is not None
        else safe_mapping(r6_body_full_packet_completeness_export_denylist_scan)
        if r6_body_full_packet_completeness_export_denylist_scan is not None
        else build_p7_r51_body_full_packet_completeness_export_denylist_scan_bodyfree()
    )
    assert_p7_r51_body_full_packet_completeness_export_denylist_scan_bodyfree_contract(r6)
    scan_ready = r6.get("packet_completeness_scan_status") == "READY_FOR_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE"
    blockers = dedupe_identifiers(r6.get("execution_blocker_ids") or [], limit=40, max_length=140)
    ready = scan_ready and not blockers
    freeze = {
        "schema_version": P7_R51_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R51_STEP,
        "scope": P7_R51_SCOPE,
        "policy_kind": P7_R51_POLICY_KIND,
        "policy_section": "R51-7_reviewer_instruction_rating_form_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r51_reviewer_instruction_rating_form_freeze_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r6.get("review_session_id"), default=P7_R51_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_session_status": "R51_REVIEWER_INSTRUCTION_RATING_FORM_READY" if ready else "PRECHECK_BLOCKED",
        "r6_packet_completeness_scan_schema_version": P7_R51_BODY_FULL_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION,
        "r6_packet_completeness_scan_ref": clean_identifier(r6.get("material_id"), default="p7_r51_body_full_packet_completeness_export_denylist_scan_bodyfree", max_length=180),
        "packet_completeness_scan_status": clean_identifier(r6.get("packet_completeness_scan_status"), default="BLOCKED_BY_R51_5_GENERATION_REQUEST", max_length=120),
        "instruction_form_status": "READY_FOR_ACTUAL_HUMAN_REVIEW_RUN" if ready else "BLOCKED_BY_R51_6_PACKET_COMPLETENESS_SCAN",
        "instruction_form_reason_refs": ["r51_reviewer_instruction_rating_form_frozen_without_running_review"] if ready else ["r51_6_packet_completeness_scan_not_ready"],
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "packet_scan_row_count": _safe_non_negative_int(r6.get("packet_scan_row_count")),
        "review_prompt_version": P7_R51_REVIEW_PROMPT_VERSION,
        "reviewer_instruction_version": P7_R50_REVIEWER_INSTRUCTION_VERSION,
        "rating_form_version": P7_R50_RATING_FORM_VERSION,
        "reviewer_check_item_refs": list(P7_R50_REVIEWER_CHECK_ITEM_REFS),
        "required_reviewer_check_label_refs": list(P7_R50_REQUIRED_REVIEWER_CHECK_LABEL_REFS),
        "reviewer_visible_field_refs": list(P7_R50_REVIEWER_VISIBLE_FIELD_REFS),
        "reviewer_hidden_field_refs": list(P7_R50_REVIEWER_HIDDEN_FIELD_REFS),
        "rating_row_schema_version_ref": P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION,
        "rating_row_required_field_refs": list(P7_R50_RATING_CAPTURE_ROW_BODYFREE_REQUIRED_FIELD_REFS),
        "rating_axis_refs": list(P5_HUMAN_BLIND_QA_RATING_AXES),
        "rating_axis_target_refs": dict(P5_HUMAN_BLIND_QA_TARGETS),
        "rating_axis_count": len(P5_HUMAN_BLIND_QA_RATING_AXES),
        "rating_score_min": 0.0,
        "rating_score_max": 1.0,
        "rating_score_canonical_refs": ["1.00", "0.75", "0.50", "0.00"],
        "extra_rating_axis_allowed": False,
        "machine_auto_score_allowed": False,
        "rating_row_required_for_each_case": True,
        "verdict_refs": list(P7_R50_RATING_VERDICT_REFS),
        "readfeel_blocker_id_refs": list(P7_R48_READFEEL_BLOCKER_ID_REFS),
        "red_or_repair_requires_blocker": True,
        "execution_blocker_is_not_readfeel_verdict": True,
        "question_need_observation_selection_required": True,
        "question_need_primary_class_refs": list(P7_R50_QUESTION_NEED_PRIMARY_CLASS_REFS),
        "ambiguity_kind_refs": list(P7_R50_AMBIGUITY_KIND_REFS),
        "one_question_fit_refs": list(P7_R50_ONE_QUESTION_FIT_REFS),
        "repair_required_ref_refs": list(P7_R50_REPAIR_REQUIRED_REF_REFS),
        "question_text_required": False,
        "draft_question_text_allowed": False,
        "reviewer_free_text_local_only": True,
        "reviewer_free_text_bodyfree_export_allowed": False,
        "reviewer_free_text_to_sanitized_reason_ids_required": True,
        "p5_weakness_must_not_be_hidden_by_question_candidate": True,
        "body_full_reader_protocol_local_only": True,
        "blind_case_id_required": True,
        "case_ref_hidden_from_reviewer": True,
        "family_hidden_from_reviewer": True,
        "subscription_tier_hidden_from_reviewer": True,
        "controller_expected_result_hidden_from_reviewer": True,
        "gate_expected_result_hidden_from_reviewer": True,
        "p5_confirmed_conditions_hidden_from_reviewer": True,
        "p8_material_candidate_conditions_hidden_from_reviewer": True,
        "reviewer_instruction_materialized_for_actual_review_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "body_full_packet_completeness_verified": r6.get("body_full_packet_completeness_verified") is True,
        "local_only_body_full_generation_allowed": ready,
        "p5_actual_review_still_not_run": True,
        "r7_reviewer_instruction_rating_form_freeze_built": ready,
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        "r0_current_source_r50_handoff_refrozen": True,
        "r1_validation_evidence_r49_timeout_handling_frozen": True,
        "r2_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r3_actual_review_session_envelope_created": True,
        "r4_24_case_manifest_freeze_built": r6.get("r4_24_case_manifest_freeze_built") is True,
        "r5_local_only_body_full_packet_generation_request_built": r6.get("r5_local_only_body_full_packet_generation_request_built") is True,
        "r6_body_full_packet_completeness_export_denylist_scan_built": r6.get("r6_body_full_packet_completeness_export_denylist_scan_built") is True,
        "implemented_steps": list(P7_R51_R7_IMPLEMENTED_STEPS) if ready else list(r6.get("implemented_steps") or P7_R51_R5_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R51_R7_NOT_YET_IMPLEMENTED_STEPS) if ready else list(r6.get("not_yet_implemented_steps") or P7_R51_R5_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R51_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R51_R7_NEXT_REQUIRED_STEP_REF if ready else P7_R51_R7_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r51_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r51_reviewer_instruction_rating_form_freeze_bodyfree_contract(freeze)
    return freeze


def assert_p7_r51_reviewer_instruction_rating_form_freeze_bodyfree_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_required_fields(data, required=P7_R51_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_REQUIRED_FIELD_REFS, source="p7_r51_r7_reviewer_instruction_rating_form_freeze_bodyfree")
    _assert_body_free_common(data, schema_version=P7_R51_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION, source="p7_r51_r7_reviewer_instruction_rating_form_freeze_bodyfree")
    if data.get("policy_section") != "R51-7_reviewer_instruction_rating_form_freeze":
        raise ValueError("R51 R7 policy section changed")
    if data.get("instruction_form_status") not in P7_R51_REVIEWER_INSTRUCTION_RATING_FORM_STATUS_REFS:
        raise ValueError("R51 R7 instruction/rating form status changed")
    if data.get("required_case_count") != P7_R51_REQUIRED_CASE_COUNT:
        raise ValueError("R51 R7 required case count changed")
    if tuple(data.get("reviewer_check_item_refs") or ()) != P7_R50_REVIEWER_CHECK_ITEM_REFS:
        raise ValueError("R51 R7 reviewer check items changed")
    if tuple(data.get("required_reviewer_check_label_refs") or ()) != P7_R50_REQUIRED_REVIEWER_CHECK_LABEL_REFS:
        raise ValueError("R51 R7 reviewer check labels changed")
    if tuple(data.get("reviewer_visible_field_refs") or ()) != P7_R50_REVIEWER_VISIBLE_FIELD_REFS:
        raise ValueError("R51 R7 reviewer visible refs changed")
    if tuple(data.get("reviewer_hidden_field_refs") or ()) != P7_R50_REVIEWER_HIDDEN_FIELD_REFS:
        raise ValueError("R51 R7 reviewer hidden refs changed")
    if data.get("rating_row_schema_version_ref") != P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R51 R7 rating row schema ref changed")
    if tuple(data.get("rating_row_required_field_refs") or ()) != P7_R50_RATING_CAPTURE_ROW_BODYFREE_REQUIRED_FIELD_REFS:
        raise ValueError("R51 R7 rating row required field refs changed")
    if tuple(data.get("rating_axis_refs") or ()) != P5_HUMAN_BLIND_QA_RATING_AXES:
        raise ValueError("R51 R7 rating axes changed")
    if safe_mapping(data.get("rating_axis_target_refs")) != dict(P5_HUMAN_BLIND_QA_TARGETS):
        raise ValueError("R51 R7 rating targets changed")
    if data.get("rating_axis_count") != len(P5_HUMAN_BLIND_QA_RATING_AXES):
        raise ValueError("R51 R7 must keep six rating axes")
    if data.get("rating_score_min") != 0.0 or data.get("rating_score_max") != 1.0:
        raise ValueError("R51 R7 score bounds changed")
    if tuple(data.get("verdict_refs") or ()) != P7_R50_RATING_VERDICT_REFS:
        raise ValueError("R51 R7 verdict refs changed")
    if tuple(data.get("readfeel_blocker_id_refs") or ()) != P7_R48_READFEEL_BLOCKER_ID_REFS:
        raise ValueError("R51 R7 readfeel blocker refs changed")
    for refs_key, expected_refs in (
        ("question_need_primary_class_refs", P7_R50_QUESTION_NEED_PRIMARY_CLASS_REFS),
        ("ambiguity_kind_refs", P7_R50_AMBIGUITY_KIND_REFS),
        ("one_question_fit_refs", P7_R50_ONE_QUESTION_FIT_REFS),
        ("repair_required_ref_refs", P7_R50_REPAIR_REQUIRED_REF_REFS),
    ):
        if tuple(data.get(refs_key) or ()) != expected_refs:
            raise ValueError(f"R51 R7 {refs_key} changed")
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
            raise ValueError(f"R51 R7 must keep {true_key}=True")
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
            raise ValueError(f"R51 R7 must keep {false_key}=False")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R51 R7 open blockers must match execution blockers")
    unknown_blockers = sorted(set(blockers) - set(P7_R51_EXECUTION_BLOCKER_ID_REFS))
    if unknown_blockers:
        raise ValueError(f"R51 R7 execution blocker ids are not canonical: {unknown_blockers[:4]}")
    ready = data.get("instruction_form_status") == "READY_FOR_ACTUAL_HUMAN_REVIEW_RUN"
    if ready:
        if data.get("packet_completeness_scan_status") != "READY_FOR_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE":
            raise ValueError("R51 R7 ready form requires ready R51-6 scan")
        if data.get("review_session_status") != "R51_REVIEWER_INSTRUCTION_RATING_FORM_READY":
            raise ValueError("R51 R7 ready status changed")
        if data.get("body_full_packet_completeness_verified") is not True:
            raise ValueError("R51 R7 ready form requires packet completeness verified")
        if data.get("local_only_body_full_generation_allowed") is not True:
            raise ValueError("R51 R7 ready form must preserve local-only generation permission")
        if data.get("r7_reviewer_instruction_rating_form_freeze_built") is not True:
            raise ValueError("R51 R7 ready form must be built")
        if blockers:
            raise ValueError("R51 R7 ready form must not carry blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R51_R7_IMPLEMENTED_STEPS:
            raise ValueError("R51 R7 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R51_R7_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R51 R7 not-yet steps changed")
        if data.get("next_required_step") != P7_R51_R7_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R7 ready form must point to R51-8")
    else:
        if data.get("local_only_body_full_generation_allowed") is not False:
            raise ValueError("R51 R7 blocked form must not preserve generation permission")
        if data.get("r7_reviewer_instruction_rating_form_freeze_built") is not False:
            raise ValueError("R51 R7 blocked form cannot claim built")
        if data.get("next_required_step") != P7_R51_R7_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R7 blocked form must point to R51-6 resolution")
    return True



def _allowed_identifier_sequence_r51(
    value: Sequence[Any] | Any | None,
    *,
    source: str,
    allowed_refs: Sequence[str] | frozenset[str] | None = None,
    limit: int = 12,
    max_length: int = 160,
) -> list[str]:
    if value is None:
        raw_values: list[Any] = []
    elif isinstance(value, str):
        raw_values = [value]
    elif isinstance(value, Sequence):
        raw_values = list(value)
    else:
        raise ValueError(f"{source} must be a sequence of identifiers")
    refs = dedupe_identifiers(raw_values, limit=limit, max_length=max_length)
    if allowed_refs is not None:
        unknown = sorted(set(refs) - set(allowed_refs))
        if unknown:
            raise ValueError(f"{source} contains non-canonical refs: {unknown[:4]}")
    return refs


def _reject_r51_actual_review_result_forbidden_keys(value: Mapping[str, Any], *, source: str) -> None:
    forbidden = sorted(set(value) & set(P7_R51_ACTUAL_REVIEW_RESULT_INPUT_FORBIDDEN_KEY_REFS))
    if forbidden:
        raise ValueError(f"{source} contains body payload, local path, question text, or reviewer note keys: {forbidden[:4]}")


def _normalize_axis_scores_r51(value: Any) -> dict[str, float]:
    raw = safe_mapping(value)
    if set(raw) != set(P5_HUMAN_BLIND_QA_RATING_AXES):
        raise ValueError("R51 R9 rating row requires all and only six P5 axes")
    normalized: dict[str, float] = {}
    for axis in P5_HUMAN_BLIND_QA_RATING_AXES:
        score = raw.get(axis)
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise ValueError("R51 R9 axis scores must be numeric")
        score_float = float(score)
        if not 0.0 <= score_float <= 1.0:
            raise ValueError("R51 R9 axis scores must be between 0.0 and 1.0")
        normalized[axis] = score_float
    return normalized


def _assert_r51_verdict_score_blocker_consistency(
    *,
    verdict: str,
    axis_scores: Mapping[str, float],
    blocker_ids: Sequence[str],
    sanitized_reason_ids: Sequence[str],
) -> None:
    if verdict == "PASS":
        below_target = [
            axis
            for axis, target in P5_HUMAN_BLIND_QA_TARGETS.items()
            if float(axis_scores.get(axis, 0.0)) < float(target)
        ]
        if below_target:
            raise ValueError("R51 R9 PASS rating rows must meet P5 axis targets")
        if blocker_ids:
            raise ValueError("R51 R9 PASS rating rows must not carry readfeel blockers")
    if verdict in {"RED", "REPAIR_REQUIRED"}:
        if not blocker_ids:
            raise ValueError("R51 R9 RED/REPAIR_REQUIRED rows must carry blocker ids")
        if not sanitized_reason_ids:
            raise ValueError("R51 R9 RED/REPAIR_REQUIRED rows must carry sanitized reason ids")


def _case_index_from_r51_manifest(manifest: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    rows = [safe_mapping(row) for row in safe_mapping(manifest).get("case_rows") or []]
    index: dict[str, dict[str, Any]] = {}
    for row in rows:
        _assert_r51_case_row(row)
        blind_case_id = clean_identifier(row.get("blind_case_id"), default="", max_length=160)
        if not blind_case_id:
            raise ValueError("R51 R8 manifest row missing blind_case_id")
        if blind_case_id in index:
            raise ValueError("R51 R8 manifest has duplicated blind_case_id")
        index[blind_case_id] = row
    return index


def _review_result_input_index(rows: Sequence[Mapping[str, Any]] | None) -> dict[str, Mapping[str, Any]]:
    index: dict[str, Mapping[str, Any]] = {}
    for row_raw in rows or []:
        row = safe_mapping(row_raw)
        _reject_r51_actual_review_result_forbidden_keys(row, source="p7_r51_r8_review_result_input_row")
        assert_p7_no_body_payload_or_contract_mutation(row, source="p7_r51_r8_review_result_input_row")
        blind_case_id = clean_identifier(row.get("blind_case_id"), default="", max_length=160)
        if not blind_case_id:
            raise ValueError("R51 R8 review result row missing blind_case_id")
        if blind_case_id in index:
            raise ValueError("R51 R8 review result rows duplicate blind_case_id")
        index[blind_case_id] = row
    return index


def _normalize_actual_review_capture_row_r51(
    *,
    case_row: Mapping[str, Any],
    review_result: Mapping[str, Any],
    review_session_id: Any,
    reviewer_ref: Any,
    reviewed_at: Any,
) -> dict[str, Any]:
    result = safe_mapping(review_result)
    _reject_r51_actual_review_result_forbidden_keys(result, source="p7_r51_r8_review_result")
    assert_p7_no_body_payload_or_contract_mutation(result, source="p7_r51_r8_review_result")
    if result.get("reviewer_free_text_included") is True:
        raise ValueError("R51 R8 reviewer free text must stay local-only and out of body-free capture")
    if result.get("question_text_included") is True or result.get("draft_question_text_included") is True:
        raise ValueError("R51 R8 question text/draft question text must not be captured")
    if result.get("machine_auto_score_used") is True or result.get("machine_metrics_used_for_readfeel") is True:
        raise ValueError("R51 R8 human readfeel ratings must not be machine-auto-scored")

    case = safe_mapping(case_row)
    axis_scores = _normalize_axis_scores_r51(result.get("axis_scores"))
    verdict = clean_identifier(result.get("verdict"), default="", max_length=60)
    if verdict not in P7_R50_RATING_VERDICT_REFS or verdict not in P7_R48_P5_REVIEWABLE_VERDICTS:
        raise ValueError("R51 R8 verdict must be PASS/YELLOW/REPAIR_REQUIRED/RED")
    sanitized_reason_ids = _allowed_identifier_sequence_r51(
        result.get("sanitized_reason_ids") or [],
        source="p7_r51_r8_review_result.sanitized_reason_ids",
        allowed_refs=P7_R48_SANITIZED_REASON_ID_REFS,
        limit=12,
    )
    blocker_ids = _allowed_identifier_sequence_r51(
        result.get("blocker_ids") or [],
        source="p7_r51_r8_review_result.blocker_ids",
        allowed_refs=P7_R48_READFEEL_BLOCKER_ID_REFS,
        limit=12,
    )
    _assert_r51_verdict_score_blocker_consistency(
        verdict=verdict,
        axis_scores=axis_scores,
        blocker_ids=blocker_ids,
        sanitized_reason_ids=sanitized_reason_ids,
    )
    primary_class = clean_identifier(result.get("question_need_primary_class"), default="", max_length=120)
    if primary_class not in P7_R50_QUESTION_NEED_PRIMARY_CLASS_REFS:
        raise ValueError("R51 R8 question need primary class changed")
    ambiguity_refs = _allowed_identifier_sequence_r51(
        result.get("ambiguity_kind_refs") or [],
        source="p7_r51_r8_review_result.ambiguity_kind_refs",
        allowed_refs=P7_R50_AMBIGUITY_KIND_REFS,
        limit=12,
    )
    one_question_fit = clean_identifier(result.get("one_question_fit_ref"), default="", max_length=120)
    if one_question_fit not in P7_R50_ONE_QUESTION_FIT_REFS:
        raise ValueError("R51 R8 one question fit ref changed")
    repair_refs = _allowed_identifier_sequence_r51(
        result.get("repair_required_refs") or [],
        source="p7_r51_r8_review_result.repair_required_refs",
        allowed_refs=P7_R50_REPAIR_REQUIRED_REF_REFS,
        limit=6,
    )
    if not repair_refs:
        raise ValueError("R51 R8 repair_required_refs must be explicit")
    row = {
        "review_session_id": clean_identifier(review_session_id, default=P7_R51_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "packet_ref_id": clean_identifier(case.get("packet_ref_id"), default="packet_ref", max_length=160),
        "blind_case_id": clean_identifier(case.get("blind_case_id"), default="blind_case", max_length=160),
        "case_ref_id": clean_identifier(case.get("case_ref_id"), default="case_ref", max_length=160),
        "family": clean_identifier(case.get("family"), default="family", max_length=160),
        "case_role": clean_identifier(case.get("case_role"), default="case_role", max_length=160),
        "review_kind": P7_R51_REVIEW_KIND,
        "reviewer_ref": clean_identifier(reviewer_ref, default=P7_R51_DEFAULT_REVIEWER_REF, max_length=120),
        "reviewed_at": clean_identifier(result.get("reviewed_at") or reviewed_at, default="reviewed_at_unset", max_length=120),
        "axis_scores": axis_scores,
        "verdict": verdict,
        "sanitized_reason_ids": sanitized_reason_ids,
        "blocker_ids": blocker_ids,
        "question_need_primary_class": primary_class,
        "ambiguity_kind_refs": ambiguity_refs,
        "one_question_fit_ref": one_question_fit,
        "repair_required_refs": repair_refs,
        "reviewer_free_text_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "machine_auto_score_used": False,
        "machine_metrics_used_for_readfeel": False,
        "body_removed": bool(result.get("body_removed", False)),
        "body_free": True,
    }
    _assert_r51_actual_review_capture_row(row)
    return row


def _assert_r51_actual_review_capture_row(row: Mapping[str, Any]) -> None:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R51_ACTUAL_REVIEW_RESULT_CAPTURE_ROW_FIELD_REFS, source="p7_r51_r8_actual_review_capture_row")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r51_r8_actual_review_capture_row")
    if data.get("body_free") is not True:
        raise ValueError("R51 R8 capture rows must be body-free")
    if data.get("review_kind") != P7_R51_REVIEW_KIND:
        raise ValueError("R51 R8 capture row review kind changed")
    if data.get("family") not in {row[0] for row in P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION}:
        raise ValueError("R51 R8 capture row family changed")
    if data.get("case_role") not in P7_R48_P5_CASE_ROLE_REFS:
        raise ValueError("R51 R8 capture row case_role changed")
    _normalize_axis_scores_r51(data.get("axis_scores"))
    if data.get("verdict") not in P7_R50_RATING_VERDICT_REFS:
        raise ValueError("R51 R8 capture row verdict changed")
    _allowed_identifier_sequence_r51(data.get("sanitized_reason_ids"), source="p7_r51_r8_capture.sanitized_reason_ids", allowed_refs=P7_R48_SANITIZED_REASON_ID_REFS)
    _allowed_identifier_sequence_r51(data.get("blocker_ids"), source="p7_r51_r8_capture.blocker_ids", allowed_refs=P7_R48_READFEEL_BLOCKER_ID_REFS)
    if data.get("question_need_primary_class") not in P7_R50_QUESTION_NEED_PRIMARY_CLASS_REFS:
        raise ValueError("R51 R8 capture row question primary class changed")
    _allowed_identifier_sequence_r51(data.get("ambiguity_kind_refs"), source="p7_r51_r8_capture.ambiguity_kind_refs", allowed_refs=P7_R50_AMBIGUITY_KIND_REFS)
    if data.get("one_question_fit_ref") not in P7_R50_ONE_QUESTION_FIT_REFS:
        raise ValueError("R51 R8 capture row one question fit changed")
    _allowed_identifier_sequence_r51(data.get("repair_required_refs"), source="p7_r51_r8_capture.repair_required_refs", allowed_refs=P7_R50_REPAIR_REQUIRED_REF_REFS)
    for false_key in (
        "reviewer_free_text_included",
        "question_text_included",
        "draft_question_text_included",
        "machine_auto_score_used",
        "machine_metrics_used_for_readfeel",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R51 R8 capture row must keep {false_key}=False")
    if not isinstance(data.get("body_removed"), bool):
        raise ValueError("R51 R8 capture row body_removed must be boolean")


def build_p7_r51_actual_human_review_run_bodyfree(
    *,
    reviewer_instruction_rating_form_freeze: Mapping[str, Any] | None = None,
    r7_reviewer_instruction_rating_form_freeze: Mapping[str, Any] | None = None,
    case_manifest_freeze: Mapping[str, Any] | None = None,
    r4_24_case_manifest_freeze: Mapping[str, Any] | None = None,
    review_result_rows: Sequence[Mapping[str, Any]] | None = None,
    reviewer_ref: Any = P7_R51_DEFAULT_REVIEWER_REF,
    reviewed_at: Any = "reviewed_at_unset",
    material_id: Any = "p7_r51_actual_human_review_run_bodyfree",
) -> dict[str, Any]:
    """Build R51-8 body-free actual review run capture from sanitized human selections.

    The body-full reading happens outside this helper in the local-only review root.
    This helper only accepts already-sanitized body-free selections and never stores
    current input, returned surface, local paths, hashes, question text, or reviewer
    free text.
    """

    if reviewer_instruction_rating_form_freeze is not None and r7_reviewer_instruction_rating_form_freeze is not None:
        raise ValueError("provide only one R51-7 reviewer instruction/rating form value")
    r7 = (
        safe_mapping(reviewer_instruction_rating_form_freeze)
        if reviewer_instruction_rating_form_freeze is not None
        else safe_mapping(r7_reviewer_instruction_rating_form_freeze)
        if r7_reviewer_instruction_rating_form_freeze is not None
        else build_p7_r51_reviewer_instruction_rating_form_freeze_bodyfree()
    )
    assert_p7_r51_reviewer_instruction_rating_form_freeze_bodyfree_contract(r7)
    if case_manifest_freeze is not None and r4_24_case_manifest_freeze is not None:
        raise ValueError("provide only one R51-4 manifest value")
    r4 = (
        safe_mapping(case_manifest_freeze)
        if case_manifest_freeze is not None
        else safe_mapping(r4_24_case_manifest_freeze)
        if r4_24_case_manifest_freeze is not None
        else build_p7_r51_24_case_manifest_freeze_bodyfree()
    )
    assert_p7_r51_24_case_manifest_freeze_bodyfree_contract(r4)
    r7_ready = r7.get("instruction_form_status") == "READY_FOR_ACTUAL_HUMAN_REVIEW_RUN" and not r7.get("execution_blocker_ids")
    manifest_ready = r4.get("manifest_status") == "READY_FOR_LOCAL_ONLY_PACKET_GENERATION_REQUEST"
    blockers = dedupe_identifiers([*(r7.get("execution_blocker_ids") or []), *(r4.get("execution_blocker_ids") or [])], limit=40, max_length=140)
    capture_rows: list[dict[str, Any]] = []
    reason_refs: list[str] = []
    case_index = _case_index_from_r51_manifest(r4) if manifest_ready else {}
    result_index = _review_result_input_index(review_result_rows)
    if not r7_ready:
        blockers = dedupe_identifiers([*blockers, "r51_rating_rows_incomplete"], limit=40, max_length=140)
        reason_refs.append("r51_7_reviewer_instruction_rating_form_not_ready")
    if not manifest_ready:
        blockers = dedupe_identifiers([*blockers, "r51_case_manifest_incomplete"], limit=40, max_length=140)
        reason_refs.append("r51_4_manifest_not_ready")
    if len(result_index) != P7_R51_REQUIRED_CASE_COUNT:
        blockers = dedupe_identifiers([*blockers, "r51_rating_rows_incomplete"], limit=40, max_length=140)
        reason_refs.append("r51_actual_review_result_rows_not_complete")
    missing_blind_ids = sorted(set(case_index) - set(result_index))
    extra_blind_ids = sorted(set(result_index) - set(case_index))
    if missing_blind_ids or extra_blind_ids:
        blockers = dedupe_identifiers([*blockers, "r51_rating_rows_incomplete"], limit=40, max_length=140)
        reason_refs.append("r51_actual_review_result_case_set_mismatch")
    if r7_ready and manifest_ready and not missing_blind_ids and not extra_blind_ids and len(result_index) == P7_R51_REQUIRED_CASE_COUNT:
        for blind_case_id in sorted(case_index):
            capture_rows.append(
                _normalize_actual_review_capture_row_r51(
                    case_row=case_index[blind_case_id],
                    review_result=result_index[blind_case_id],
                    review_session_id=r7.get("review_session_id"),
                    reviewer_ref=reviewer_ref,
                    reviewed_at=reviewed_at,
                )
            )
    ready = len(capture_rows) == P7_R51_REQUIRED_CASE_COUNT and not blockers
    if ready:
        status = "READY_FOR_RATING_ROW_NORMALIZATION"
        reason_refs = ["r51_actual_human_review_run_captured_bodyfree"]
    else:
        status = "BLOCKED_BY_R51_7_REVIEWER_INSTRUCTION_RATING_FORM" if not r7_ready else "BLOCKED_BY_ACTUAL_REVIEW_RESULT_ROWS"
        if not reason_refs:
            reason_refs = ["r51_actual_review_run_not_ready"]
    blind_ids = _r51_case_refs(capture_rows, "blind_case_id")
    case_refs = _r51_case_refs(capture_rows, "case_ref_id")
    packet_refs = _r51_case_refs(capture_rows, "packet_ref_id")
    actual_true_keys = ("actual_human_review_run_here", "actual_manual_review_run_here") if ready else ()
    review_run = {
        **_false_flags(),
        "schema_version": P7_R51_ACTUAL_HUMAN_REVIEW_RUN_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R51_STEP,
        "scope": P7_R51_SCOPE,
        "policy_kind": P7_R51_POLICY_KIND,
        "policy_section": "R51-8_actual_human_review_run",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r51_actual_human_review_run_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r7.get("review_session_id"), default=P7_R51_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_session_status": "R51_ACTUAL_HUMAN_REVIEW_RUN_CAPTURED_BODYFREE" if ready else "PRECHECK_BLOCKED",
        "r7_reviewer_instruction_rating_form_schema_version": P7_R51_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION,
        "r7_reviewer_instruction_rating_form_ref": clean_identifier(r7.get("material_id"), default="p7_r51_reviewer_instruction_rating_form_freeze_bodyfree", max_length=180),
        "instruction_form_status": clean_identifier(r7.get("instruction_form_status"), default="BLOCKED_BY_R51_6_PACKET_COMPLETENESS_SCAN", max_length=120),
        "instruction_form_ready_for_actual_review": bool(r7_ready),
        "r4_manifest_schema_version": P7_R51_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION,
        "r4_manifest_ref": clean_identifier(r4.get("material_id"), default="p7_r51_24_case_manifest_freeze_bodyfree", max_length=180),
        "manifest_status": clean_identifier(r4.get("manifest_status"), default="BLOCKED_BY_R51_3_ENVELOPE", max_length=120),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "manifest_case_count": _safe_non_negative_int(r4.get("case_count")),
        "actual_review_run_status": status,
        "actual_review_run_reason_refs": dedupe_identifiers(reason_refs, limit=20, max_length=160),
        "review_prompt_version": P7_R51_REVIEW_PROMPT_VERSION,
        "reviewer_instruction_version": P7_R50_REVIEWER_INSTRUCTION_VERSION,
        "rating_form_version": P7_R50_RATING_FORM_VERSION,
        "reviewer_ref": clean_identifier(reviewer_ref, default=P7_R51_DEFAULT_REVIEWER_REF, max_length=120),
        "reviewed_at_ref": clean_identifier(reviewed_at, default="reviewed_at_unset", max_length=120),
        "review_result_capture_row_field_refs": list(P7_R51_ACTUAL_REVIEW_RESULT_CAPTURE_ROW_FIELD_REFS),
        "review_result_capture_rows": capture_rows,
        "review_result_capture_row_count": len(capture_rows),
        "reviewed_blind_case_id_count": len(blind_ids),
        "reviewed_case_ref_id_count": len(case_refs),
        "reviewed_packet_ref_id_count": len(packet_refs),
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
        "r0_current_source_r50_handoff_refrozen": True,
        "r1_validation_evidence_r49_timeout_handling_frozen": True,
        "r2_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r3_actual_review_session_envelope_created": True,
        "r4_24_case_manifest_freeze_built": True,
        "r5_local_only_body_full_packet_generation_request_built": True,
        "r6_body_full_packet_completeness_export_denylist_scan_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": bool(r7_ready),
        "r8_actual_human_review_run_recorded": ready,
        "implemented_steps": list(P7_R51_R8_IMPLEMENTED_STEPS if ready else P7_R51_R7_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R51_R8_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R51_R7_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R51_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R51_R8_NEXT_REQUIRED_STEP_REF if ready else P7_R51_R8_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r51_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r51_actual_human_review_run_bodyfree_contract(review_run, allowed_true_false_key_refs=actual_true_keys)
    return review_run


def assert_p7_r51_actual_human_review_run_bodyfree_contract(
    review_run: Mapping[str, Any],
    *,
    allowed_true_false_key_refs: Sequence[str] | None = None,
) -> bool:
    data = safe_mapping(review_run)
    _assert_required_fields(data, required=P7_R51_ACTUAL_HUMAN_REVIEW_RUN_REQUIRED_FIELD_REFS, source="p7_r51_r8_actual_human_review_run")
    allowed = tuple(allowed_true_false_key_refs or ("actual_human_review_run_here", "actual_manual_review_run_here"))
    _assert_body_free_common_allowing(
        data,
        schema_version=P7_R51_ACTUAL_HUMAN_REVIEW_RUN_SCHEMA_VERSION,
        source="p7_r51_r8_actual_human_review_run",
        allowed_true_false_key_refs=allowed,
    )
    if data.get("policy_section") != "R51-8_actual_human_review_run":
        raise ValueError("R51 R8 policy section changed")
    if data.get("actual_review_run_status") not in P7_R51_ACTUAL_HUMAN_REVIEW_RUN_STATUS_REFS:
        raise ValueError("R51 R8 status changed")
    for row in data.get("review_result_capture_rows") or []:
        _assert_r51_actual_review_capture_row(safe_mapping(row))
    for true_key in ("body_full_reader_protocol_local_only", "reviewer_free_text_local_only"):
        if data.get(true_key) is not True:
            raise ValueError(f"R51 R8 must keep {true_key}=True")
    for false_key in (
        "reviewer_free_text_bodyfree_export_allowed",
        "reviewer_free_text_included",
        "question_text_included",
        "draft_question_text_included",
        "raw_input_or_returned_surface_included",
        "machine_auto_score_allowed",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_reviewer_notes_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R51 R8 must keep {false_key}=False")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R51 R8 open blockers must match execution blockers")
    unknown = sorted(set(blockers) - set(P7_R51_EXECUTION_BLOCKER_ID_REFS))
    if unknown:
        raise ValueError(f"R51 R8 execution blockers are not canonical: {unknown[:4]}")
    ready = data.get("actual_review_run_status") == "READY_FOR_RATING_ROW_NORMALIZATION"
    if ready:
        if data.get("review_result_capture_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R51 R8 ready run must contain 24 capture rows")
        if data.get("all_24_cases_reviewed") is not True:
            raise ValueError("R51 R8 ready run must mark all cases reviewed")
        if data.get("actual_human_review_run_here") is not True or data.get("actual_manual_review_run_here") is not True:
            raise ValueError("R51 R8 ready run must mark actual review run captured")
        if data.get("actual_review_result_rows_captured_here") is not True:
            raise ValueError("R51 R8 ready run must capture body-free rows")
        if data.get("p5_actual_review_still_not_run") is not False:
            raise ValueError("R51 R8 ready run must not say actual review is still unrun")
        if blockers:
            raise ValueError("R51 R8 ready run must not carry open blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R51_R8_IMPLEMENTED_STEPS:
            raise ValueError("R51 R8 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R51_R8_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R51 R8 not-yet steps changed")
        if data.get("next_required_step") != P7_R51_R8_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R8 ready run must point to R51-9")
    else:
        if data.get("actual_human_review_run_here") is not False or data.get("actual_manual_review_run_here") is not False:
            raise ValueError("R51 R8 blocked run must not mark actual review complete")
        if data.get("actual_review_result_rows_captured_here") is not False:
            raise ValueError("R51 R8 blocked run must not capture rows")
        if data.get("p5_actual_review_still_not_run") is not True:
            raise ValueError("R51 R8 blocked run must keep actual review as unrun")
        if data.get("next_required_step") != P7_R51_R8_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R8 blocked run must point to R51-7 resolution")
    return True


def normalize_p7_r51_rating_row_bodyfree(*, review_capture_row: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize one R51 body-free review capture row into a rating row."""

    capture = safe_mapping(review_capture_row)
    _assert_r51_actual_review_capture_row(capture)
    row = {
        "schema_version": P7_R51_RATING_ROW_BODYFREE_SCHEMA_VERSION,
        "review_session_id": clean_identifier(capture.get("review_session_id"), default=P7_R51_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "packet_ref_id": clean_identifier(capture.get("packet_ref_id"), default="packet_ref", max_length=160),
        "blind_case_id": clean_identifier(capture.get("blind_case_id"), default="blind_case", max_length=160),
        "case_ref_id": clean_identifier(capture.get("case_ref_id"), default="case_ref", max_length=160),
        "family": clean_identifier(capture.get("family"), default="family", max_length=160),
        "case_role": clean_identifier(capture.get("case_role"), default="case_role", max_length=160),
        "review_kind": P7_R51_REVIEW_KIND,
        "reviewer_ref": clean_identifier(capture.get("reviewer_ref"), default=P7_R51_DEFAULT_REVIEWER_REF, max_length=120),
        "reviewed_at": clean_identifier(capture.get("reviewed_at"), default="reviewed_at_unset", max_length=120),
        "axis_scores": _normalize_axis_scores_r51(capture.get("axis_scores")),
        "verdict": clean_identifier(capture.get("verdict"), default="", max_length=60),
        "sanitized_reason_ids": _allowed_identifier_sequence_r51(capture.get("sanitized_reason_ids") or [], source="p7_r51_rating_row.sanitized_reason_ids", allowed_refs=P7_R48_SANITIZED_REASON_ID_REFS),
        "blocker_ids": _allowed_identifier_sequence_r51(capture.get("blocker_ids") or [], source="p7_r51_rating_row.blocker_ids", allowed_refs=P7_R48_READFEEL_BLOCKER_ID_REFS),
        "reviewer_free_text_included": False,
        "body_removed": bool(capture.get("body_removed", False)),
        "body_free": True,
    }
    assert_p7_r51_rating_row_bodyfree_contract(row)
    return row


def assert_p7_r51_rating_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R51_RATING_ROW_BODYFREE_REQUIRED_FIELD_REFS, source="p7_r51_rating_row_bodyfree")
    if data.get("schema_version") != P7_R51_RATING_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R51 rating row schema changed")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r51_rating_row_bodyfree")
    if data.get("body_free") is not True:
        raise ValueError("R51 rating row must be body-free")
    if data.get("family") not in {row[0] for row in P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION}:
        raise ValueError("R51 rating row family changed")
    if data.get("case_role") not in P7_R48_P5_CASE_ROLE_REFS:
        raise ValueError("R51 rating row case_role changed")
    if data.get("review_kind") != P7_R51_REVIEW_KIND:
        raise ValueError("R51 rating row review kind changed")
    axis_scores = _normalize_axis_scores_r51(data.get("axis_scores"))
    verdict = clean_identifier(data.get("verdict"), default="", max_length=60)
    if verdict not in P7_R50_RATING_VERDICT_REFS or verdict not in P7_R48_P5_REVIEWABLE_VERDICTS:
        raise ValueError("R51 rating row verdict enum changed")
    reasons = _allowed_identifier_sequence_r51(data.get("sanitized_reason_ids"), source="p7_r51_rating_row.sanitized_reason_ids", allowed_refs=P7_R48_SANITIZED_REASON_ID_REFS)
    blockers = _allowed_identifier_sequence_r51(data.get("blocker_ids"), source="p7_r51_rating_row.blocker_ids", allowed_refs=P7_R48_READFEEL_BLOCKER_ID_REFS)
    _assert_r51_verdict_score_blocker_consistency(verdict=verdict, axis_scores=axis_scores, blocker_ids=blockers, sanitized_reason_ids=reasons)
    if data.get("reviewer_free_text_included") is not False:
        raise ValueError("R51 rating row must not include reviewer free text")
    if not isinstance(data.get("body_removed"), bool):
        raise ValueError("R51 rating row body_removed must be boolean")
    return True


def _verdict_counts_r51(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = {verdict: 0 for verdict in P7_R50_RATING_VERDICT_REFS}
    for row in rows:
        verdict = clean_identifier(safe_mapping(row).get("verdict"), default="", max_length=60)
        if verdict not in counts:
            raise ValueError("R51 rating row verdict changed")
        counts[verdict] += 1
    return counts


def build_p7_r51_rating_row_normalizer_bodyfree(
    *,
    actual_human_review_run: Mapping[str, Any] | None = None,
    r8_actual_human_review_run: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r51_rating_row_normalizer_bodyfree",
) -> dict[str, Any]:
    """Build R51-9 body-free normalized rating rows from R51-8 capture rows."""

    if actual_human_review_run is not None and r8_actual_human_review_run is not None:
        raise ValueError("provide only one R51-8 actual review run value")
    r8 = (
        safe_mapping(actual_human_review_run)
        if actual_human_review_run is not None
        else safe_mapping(r8_actual_human_review_run)
        if r8_actual_human_review_run is not None
        else build_p7_r51_actual_human_review_run_bodyfree()
    )
    assert_p7_r51_actual_human_review_run_bodyfree_contract(r8)
    r8_ready = r8.get("actual_review_run_status") == "READY_FOR_RATING_ROW_NORMALIZATION" and not r8.get("execution_blocker_ids")
    blockers = dedupe_identifiers(r8.get("execution_blocker_ids") or [], limit=40, max_length=140)
    rating_rows: list[dict[str, Any]] = []
    reason_refs: list[str] = []
    if r8_ready:
        rating_rows = [normalize_p7_r51_rating_row_bodyfree(review_capture_row=safe_mapping(row)) for row in r8.get("review_result_capture_rows") or []]
    else:
        blockers = dedupe_identifiers([*blockers, "r51_rating_rows_incomplete"], limit=40, max_length=140)
        reason_refs.append("r51_8_actual_review_run_not_ready")
    review_case_refs = set(_r51_case_refs([safe_mapping(row) for row in r8.get("review_result_capture_rows") or []], "case_ref_id"))
    rating_case_refs = set(_r51_case_refs(rating_rows, "case_ref_id"))
    complete = len(rating_rows) == P7_R51_REQUIRED_CASE_COUNT and review_case_refs == rating_case_refs and r8_ready and not blockers
    if not complete and r8_ready:
        blockers = dedupe_identifiers([*blockers, "r51_rating_rows_incomplete"], limit=40, max_length=140)
        reason_refs.append("r51_rating_rows_not_complete")
    ready = complete and not blockers
    if ready:
        status = "READY_FOR_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION"
        reason_refs = ["r51_rating_rows_normalized_bodyfree"]
    else:
        status = "BLOCKED_BY_R51_8_ACTUAL_HUMAN_REVIEW_RUN" if not r8_ready else "BLOCKED_BY_RATING_ROW_VALIDATION"
        if not reason_refs:
            reason_refs = ["r51_rating_row_normalizer_not_ready"]
    actual_true_keys = (
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "actual_rating_rows_materialized_here",
    ) if ready else ()
    normalizer = {
        **_false_flags(),
        "schema_version": P7_R51_RATING_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R51_STEP,
        "scope": P7_R51_SCOPE,
        "policy_kind": P7_R51_POLICY_KIND,
        "policy_section": "R51-9_rating_row_normalization",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r51_rating_row_normalizer_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r8.get("review_session_id"), default=P7_R51_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_session_status": "R51_RATING_ROWS_NORMALIZED_BODYFREE" if ready else "PRECHECK_BLOCKED",
        "r8_actual_human_review_run_schema_version": P7_R51_ACTUAL_HUMAN_REVIEW_RUN_SCHEMA_VERSION,
        "r8_actual_human_review_run_ref": clean_identifier(r8.get("material_id"), default="p7_r51_actual_human_review_run_bodyfree", max_length=180),
        "actual_review_run_status": clean_identifier(r8.get("actual_review_run_status"), default="BLOCKED_BY_R51_7_REVIEWER_INSTRUCTION_RATING_FORM", max_length=120),
        "actual_review_run_ready_for_rating_normalization": bool(r8_ready),
        "rating_row_normalizer_status": status,
        "rating_row_normalizer_reason_refs": dedupe_identifiers(reason_refs, limit=20, max_length=160),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "review_result_capture_row_count": _safe_non_negative_int(r8.get("review_result_capture_row_count")),
        "rating_row_count": len(rating_rows),
        "rating_rows": rating_rows,
        "rating_row_schema_version": P7_R51_RATING_ROW_BODYFREE_SCHEMA_VERSION,
        "r48_rating_row_schema_version_ref": P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION,
        "rating_row_required_field_refs": list(P7_R51_RATING_ROW_BODYFREE_REQUIRED_FIELD_REFS),
        "rating_axis_refs": list(P5_HUMAN_BLIND_QA_RATING_AXES),
        "rating_axis_target_refs": dict(P5_HUMAN_BLIND_QA_TARGETS),
        "rating_score_min": 0.0,
        "rating_score_max": 1.0,
        "missing_axis_scores_pass_allowed": False,
        "extra_rating_axis_allowed": False,
        "machine_auto_score_allowed": False,
        "machine_metrics_used_for_readfeel_allowed": False,
        "reviewer_free_text_bodyfree_allowed": False,
        "sanitized_reason_ids_only": True,
        "blocker_ids_only": True,
        "allowed_verdict_refs": list(P7_R50_RATING_VERDICT_REFS),
        "readfeel_blocker_id_refs": list(P7_R48_READFEEL_BLOCKER_ID_REFS),
        "blocked_or_not_reviewable_must_use_execution_blocker_row": True,
        "red_or_repair_requires_blocker": True,
        "pass_requires_targets_and_no_blockers": True,
        "body_removed_may_be_false_before_disposal": True,
        "rating_rows_are_bodyfree": True,
        "all_required_rating_rows_present": ready,
        "rating_case_ref_sets_match_review_capture": bool(review_case_refs == rating_case_refs and len(review_case_refs) == P7_R51_REQUIRED_CASE_COUNT) if ready else False,
        "verdict_counts": _verdict_counts_r51(rating_rows),
        "blocker_row_candidate_count": sum(1 for row in rating_rows if safe_mapping(row).get("blocker_ids")),
        "execution_blocker_row_candidate_count": 0 if ready else len(blockers),
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "actual_human_review_run_here": ready,
        "actual_manual_review_run_here": ready,
        "actual_rating_rows_materialized_here": ready,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "p5_actual_review_still_not_run": not ready,
        "r0_current_source_r50_handoff_refrozen": True,
        "r1_validation_evidence_r49_timeout_handling_frozen": True,
        "r2_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r3_actual_review_session_envelope_created": True,
        "r4_24_case_manifest_freeze_built": True,
        "r5_local_only_body_full_packet_generation_request_built": True,
        "r6_body_full_packet_completeness_export_denylist_scan_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": bool(r8.get("r7_reviewer_instruction_rating_form_freeze_built")),
        "r8_actual_human_review_run_recorded": bool(r8_ready),
        "r9_rating_row_normalizer_built": ready,
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        "implemented_steps": list(P7_R51_R9_IMPLEMENTED_STEPS if ready else P7_R51_R8_IMPLEMENTED_STEPS if r8_ready else P7_R51_R7_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R51_R9_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R51_R8_NOT_YET_IMPLEMENTED_STEPS if r8_ready else P7_R51_R7_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R51_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R51_R9_NEXT_REQUIRED_STEP_REF if ready else P7_R51_R9_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r51_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r51_rating_row_normalizer_bodyfree_contract(normalizer, allowed_true_false_key_refs=actual_true_keys)
    return normalizer


def assert_p7_r51_rating_row_normalizer_bodyfree_contract(
    normalizer: Mapping[str, Any],
    *,
    allowed_true_false_key_refs: Sequence[str] | None = None,
) -> bool:
    data = safe_mapping(normalizer)
    _assert_required_fields(data, required=P7_R51_RATING_ROW_NORMALIZER_BODYFREE_REQUIRED_FIELD_REFS, source="p7_r51_r9_rating_row_normalizer")
    allowed = tuple(allowed_true_false_key_refs or ("actual_human_review_run_here", "actual_manual_review_run_here", "actual_rating_rows_materialized_here"))
    _assert_body_free_common_allowing(
        data,
        schema_version=P7_R51_RATING_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION,
        source="p7_r51_r9_rating_row_normalizer",
        allowed_true_false_key_refs=allowed,
    )
    if data.get("policy_section") != "R51-9_rating_row_normalization":
        raise ValueError("R51 R9 policy section changed")
    if data.get("rating_row_normalizer_status") not in P7_R51_RATING_ROW_NORMALIZER_STATUS_REFS:
        raise ValueError("R51 R9 normalizer status changed")
    if data.get("rating_row_schema_version") != P7_R51_RATING_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R51 R9 rating row schema ref changed")
    if data.get("r48_rating_row_schema_version_ref") != P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R51 R9 R48 rating row schema ref changed")
    if tuple(data.get("rating_row_required_field_refs") or ()) != P7_R51_RATING_ROW_BODYFREE_REQUIRED_FIELD_REFS:
        raise ValueError("R51 R9 rating row required fields changed")
    if tuple(data.get("rating_axis_refs") or ()) != P5_HUMAN_BLIND_QA_RATING_AXES:
        raise ValueError("R51 R9 rating axes changed")
    if safe_mapping(data.get("rating_axis_target_refs")) != dict(P5_HUMAN_BLIND_QA_TARGETS):
        raise ValueError("R51 R9 rating targets changed")
    if data.get("rating_score_min") != 0.0 or data.get("rating_score_max") != 1.0:
        raise ValueError("R51 R9 score bounds changed")
    if tuple(data.get("allowed_verdict_refs") or ()) != P7_R50_RATING_VERDICT_REFS:
        raise ValueError("R51 R9 allowed verdict refs changed")
    if tuple(data.get("readfeel_blocker_id_refs") or ()) != P7_R48_READFEEL_BLOCKER_ID_REFS:
        raise ValueError("R51 R9 blocker refs changed")
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
            raise ValueError(f"R51 R9 must keep {true_key}=True")
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
            raise ValueError(f"R51 R9 must keep {false_key}=False")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R51 R9 open blockers must match execution blockers")
    unknown = sorted(set(blockers) - set(P7_R51_EXECUTION_BLOCKER_ID_REFS))
    if unknown:
        raise ValueError(f"R51 R9 execution blockers are not canonical: {unknown[:4]}")
    ready = data.get("rating_row_normalizer_status") == "READY_FOR_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION"
    if ready:
        if data.get("rating_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R51 R9 ready normalizer must carry 24 rating rows")
        if data.get("all_required_rating_rows_present") is not True:
            raise ValueError("R51 R9 ready normalizer must mark all rating rows present")
        if data.get("rating_case_ref_sets_match_review_capture") is not True:
            raise ValueError("R51 R9 ready normalizer must match R8 case refs")
        if data.get("actual_human_review_run_here") is not True or data.get("actual_manual_review_run_here") is not True:
            raise ValueError("R51 R9 ready normalizer must preserve R8 actual review evidence")
        if data.get("actual_rating_rows_materialized_here") is not True:
            raise ValueError("R51 R9 ready normalizer must materialize body-free rating rows")
        if data.get("p5_actual_review_still_not_run") is not False:
            raise ValueError("R51 R9 ready normalizer must not say actual review is still unrun")
        if blockers:
            raise ValueError("R51 R9 ready normalizer must not carry open blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R51_R9_IMPLEMENTED_STEPS:
            raise ValueError("R51 R9 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R51_R9_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R51 R9 not-yet steps changed")
        if data.get("next_required_step") != P7_R51_R9_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R9 ready normalizer must point to R51-10")
    else:
        if data.get("actual_rating_rows_materialized_here") is not False:
            raise ValueError("R51 R9 blocked normalizer must not materialize rating rows")
        if data.get("r9_rating_row_normalizer_built") is not False:
            raise ValueError("R51 R9 blocked normalizer must not claim built")
        if data.get("next_required_step") != P7_R51_R9_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R9 blocked normalizer must point to R51-8 resolution")
    return True

# ---------------------------------------------------------------------------
# R51-10 / R51-11: blocker ingestion and question-need observation rows
# ---------------------------------------------------------------------------

P7_R51_READFEEL_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "packet_ref_id",
    "blind_case_id",
    "case_ref_id",
    "family",
    "case_role",
    "review_kind",
    "blocker_id",
    "blocker_kind",
    "blocker_status",
    "sanitized_reason_ids",
    "reviewer_free_text_included",
    "body_removed",
    "body_free",
)
P7_R51_EXECUTION_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "packet_ref_id",
    "blind_case_id",
    "case_ref_id",
    "family",
    "review_kind",
    "execution_blocker_id",
    "execution_blocker_kind",
    "execution_blocker_status",
    "readfeel_verdict_not_assigned",
    "body_free",
)
P7_R51_READFEEL_EXECUTION_BLOCKER_INGESTION_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "review_session_status",
    "r9_rating_row_normalizer_schema_version",
    "r9_rating_row_normalizer_ref",
    "rating_row_normalizer_status",
    "blocker_ingestion_status",
    "blocker_ingestion_reason_refs",
    "required_case_count",
    "rating_row_count",
    "readfeel_blocker_row_schema_version",
    "r48_blocker_row_schema_version_ref",
    "execution_blocker_row_schema_version",
    "r48_execution_blocker_row_schema_version_ref",
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
    "r0_current_source_r50_handoff_refrozen",
    "r1_validation_evidence_r49_timeout_handling_frozen",
    "r2_local_root_explicit_allow_purge_plan_preflight_built",
    "r3_actual_review_session_envelope_created",
    "r4_24_case_manifest_freeze_built",
    "r5_local_only_body_full_packet_generation_request_built",
    "r6_body_full_packet_completeness_export_denylist_scan_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_actual_human_review_run_recorded",
    "r9_rating_row_normalizer_built",
    "r10_readfeel_blocker_execution_blocker_ingestion_built",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r51_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R51_R0_R1_FALSE_KEY_REFS,
)
P7_R51_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "packet_ref_id",
    "blind_case_id",
    "case_ref_id",
    "family",
    "case_role",
    "review_kind",
    "observation_stage",
    "question_need_primary_class",
    "ambiguity_kind_refs",
    "one_question_fit_ref",
    "plan_candidate_flags",
    "repair_required_refs",
    "sanitized_reason_ids",
    "question_text_included",
    "draft_question_text_included",
    "reviewer_free_text_included",
    "body_removed",
    "body_free",
)
P7_R51_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "review_session_status",
    "r10_blocker_ingestion_schema_version",
    "r10_blocker_ingestion_ref",
    "blocker_ingestion_status",
    "r8_actual_human_review_run_schema_version",
    "r8_actual_human_review_run_ref",
    "actual_review_run_status",
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
    "row_case_ref_sets_match_review_capture",
    "row_case_ref_sets_match_rating_rows",
    "all_required_question_need_observation_rows_present",
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
    "r0_current_source_r50_handoff_refrozen",
    "r1_validation_evidence_r49_timeout_handling_frozen",
    "r2_local_root_explicit_allow_purge_plan_preflight_built",
    "r3_actual_review_session_envelope_created",
    "r4_24_case_manifest_freeze_built",
    "r5_local_only_body_full_packet_generation_request_built",
    "r6_body_full_packet_completeness_export_denylist_scan_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_actual_human_review_run_recorded",
    "r9_rating_row_normalizer_built",
    "r10_readfeel_blocker_execution_blocker_ingestion_built",
    "r11_question_need_observation_row_normalizer_built",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r51_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R51_R0_R1_FALSE_KEY_REFS,
)


def _r51_family_refs() -> frozenset[str]:
    return frozenset(row[0] for row in P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION)


def _r51_case_identity(row: Mapping[str, Any]) -> tuple[Any, Any, Any, Any, Any]:
    data = safe_mapping(row)
    return (
        data.get("review_session_id"),
        data.get("packet_ref_id"),
        data.get("blind_case_id"),
        data.get("case_ref_id"),
        data.get("family"),
    )


def _r51_execution_blocker_kind(execution_blocker_id: str) -> str:
    if execution_blocker_id == "r51_missing_r50_handoff":
        return "HANDOFF"
    if "green_evidence" in execution_blocker_id or "validation" in execution_blocker_id or "wildcard_timeout" in execution_blocker_id:
        return "VALIDATION"
    if execution_blocker_id in {"r51_local_review_root_missing", "r51_local_review_root_invalid"}:
        return "LOCAL_ROOT"
    if execution_blocker_id == "r51_explicit_allow_missing":
        return "EXPLICIT_ALLOW"
    if execution_blocker_id in {"r51_disposal_plan_missing", "r51_disposal_receipt_missing", "r51_disposal_failed", "r51_disposal_not_verified"}:
        return "DISPOSAL"
    if execution_blocker_id in {"r51_body_full_packet_generation_request_blocked", "r51_body_full_packet_generation_failed", "r51_body_full_packet_export_violation", "r51_case_material_missing"}:
        return "GENERATION"
    if execution_blocker_id in {"r51_rating_rows_incomplete"}:
        return "RATING"
    if execution_blocker_id in {"r51_question_need_observation_rows_incomplete", "r51_rating_question_observation_inconsistent"}:
        return "QUESTION_OBSERVATION"
    if execution_blocker_id in {"r51_case_manifest_incomplete"}:
        return "MANIFEST"
    if execution_blocker_id in {"r51_blind_case_id_case_ref_boundary_violation", "r51_reviewer_facing_manifest_leak_detected"}:
        return "BOUNDARY"
    if execution_blocker_id == "r51_body_free_leak_detected":
        return "BODY_FREE_LEAK"
    if execution_blocker_id == "r51_scope_drift_detected":
        return "SCOPE"
    return "REVIEW"


def _r51_readfeel_blocker_kind_from_verdict(verdict: Any) -> str:
    return "READFEEL_RED" if clean_identifier(verdict, default="", max_length=60) == "RED" else "REPAIR_REQUIRED"


def build_p7_r51_readfeel_blocker_row_bodyfree(
    *,
    rating_row: Mapping[str, Any],
    blocker_id: Any,
    blocker_kind: Any | None = None,
    blocker_status: Any = "OPEN",
    sanitized_reason_ids: Sequence[Any] | None = None,
    body_removed: bool | None = None,
) -> dict[str, Any]:
    """Build one body-free R51 readfeel blocker row from a normalized rating row."""

    rating = safe_mapping(rating_row)
    assert_p7_r51_rating_row_bodyfree_contract(rating)
    blocker = clean_identifier(blocker_id, default="", max_length=160)
    if blocker not in P7_R48_READFEEL_BLOCKER_ID_REFS:
        raise ValueError("R51 R10 readfeel blocker row requires a canonical P5 readfeel blocker id")
    kind = clean_identifier(blocker_kind, default=_r51_readfeel_blocker_kind_from_verdict(rating.get("verdict")), max_length=80)
    if kind not in P7_R48_P5_BLOCKER_KINDS or kind == "EXECUTION_BLOCKER":
        raise ValueError("R51 R10 readfeel blocker row must not use execution blocker kind")
    status = clean_identifier(blocker_status, default="OPEN", max_length=80)
    if status not in P7_R48_P5_BLOCKER_STATUSES:
        raise ValueError("R51 R10 readfeel blocker status enum changed")
    reasons = _allowed_identifier_sequence_r51(
        sanitized_reason_ids if sanitized_reason_ids is not None else (rating.get("sanitized_reason_ids") or [blocker]),
        source="p7_r51_readfeel_blocker_row.sanitized_reason_ids",
        allowed_refs=P7_R48_SANITIZED_REASON_ID_REFS,
        limit=12,
    )
    if not reasons:
        reasons = [blocker]
    row = {
        "schema_version": P7_R51_READFEEL_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "review_session_id": clean_identifier(rating.get("review_session_id"), default=P7_R51_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "packet_ref_id": clean_identifier(rating.get("packet_ref_id"), default="packet_ref", max_length=160),
        "blind_case_id": clean_identifier(rating.get("blind_case_id"), default="blind_case", max_length=160),
        "case_ref_id": clean_identifier(rating.get("case_ref_id"), default="case_ref", max_length=160),
        "family": clean_identifier(rating.get("family"), default="family", max_length=160),
        "case_role": clean_identifier(rating.get("case_role"), default="case_role", max_length=160),
        "review_kind": P7_R51_REVIEW_KIND,
        "blocker_id": blocker,
        "blocker_kind": kind,
        "blocker_status": status,
        "sanitized_reason_ids": reasons,
        "reviewer_free_text_included": False,
        "body_removed": bool(rating.get("body_removed") if body_removed is None else body_removed),
        "body_free": True,
    }
    assert_p7_r51_readfeel_blocker_row_bodyfree_contract(row)
    return row


def assert_p7_r51_readfeel_blocker_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R51_READFEEL_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS, source="p7_r51_readfeel_blocker_row_bodyfree")
    if data.get("schema_version") != P7_R51_READFEEL_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R51 readfeel blocker row schema changed")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r51_readfeel_blocker_row_bodyfree")
    if data.get("body_free") is not True:
        raise ValueError("R51 readfeel blocker row must be body-free")
    if data.get("family") not in _r51_family_refs():
        raise ValueError("R51 readfeel blocker row family changed")
    if data.get("case_role") not in P7_R48_P5_CASE_ROLE_REFS:
        raise ValueError("R51 readfeel blocker row case_role changed")
    if data.get("review_kind") != P7_R51_REVIEW_KIND:
        raise ValueError("R51 readfeel blocker row review kind changed")
    if data.get("blocker_id") not in P7_R48_READFEEL_BLOCKER_ID_REFS:
        raise ValueError("R51 readfeel blocker row must carry a readfeel blocker id")
    if data.get("blocker_kind") not in P7_R48_P5_BLOCKER_KINDS or data.get("blocker_kind") == "EXECUTION_BLOCKER":
        raise ValueError("R51 readfeel blocker row must not mix execution blocker kind")
    if data.get("blocker_status") not in P7_R48_P5_BLOCKER_STATUSES:
        raise ValueError("R51 readfeel blocker row status enum changed")
    _allowed_identifier_sequence_r51(data.get("sanitized_reason_ids"), source="p7_r51_readfeel_blocker_row.sanitized_reason_ids", allowed_refs=P7_R48_SANITIZED_REASON_ID_REFS)
    if data.get("reviewer_free_text_included") is not False:
        raise ValueError("R51 readfeel blocker row must not include reviewer free text")
    if not isinstance(data.get("body_removed"), bool):
        raise ValueError("R51 readfeel blocker row must carry boolean body_removed")
    return True


def build_p7_r51_execution_blocker_row_bodyfree(
    *,
    execution_blocker_id: Any,
    case_row: Mapping[str, Any] | None = None,
    review_session_id: Any = P7_R51_DEFAULT_REVIEW_SESSION_ID,
    execution_blocker_status: Any = "OPEN",
) -> dict[str, Any]:
    """Build a body-free R51 execution blocker row without assigning readfeel verdict."""

    case = safe_mapping(case_row)
    blocker = clean_identifier(execution_blocker_id, default="", max_length=160)
    if blocker not in P7_R51_EXECUTION_BLOCKER_ID_REFS:
        raise ValueError("R51 R10 execution blocker id changed")
    status = clean_identifier(execution_blocker_status, default="OPEN", max_length=80)
    if status not in P7_R51_EXECUTION_BLOCKER_STATUS_REFS:
        raise ValueError("R51 R10 execution blocker status enum changed")
    row = {
        "schema_version": P7_R51_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "review_session_id": clean_identifier(case.get("review_session_id") or review_session_id, default=P7_R51_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "packet_ref_id": clean_identifier(case.get("packet_ref_id"), default="session_level_packet_ref", max_length=160),
        "blind_case_id": clean_identifier(case.get("blind_case_id"), default="session_level_blind_case_ref", max_length=160),
        "case_ref_id": clean_identifier(case.get("case_ref_id"), default="session_level_case_ref", max_length=160),
        "family": clean_identifier(case.get("family"), default="session_level_execution_blocker", max_length=160),
        "review_kind": P7_R51_REVIEW_KIND,
        "execution_blocker_id": blocker,
        "execution_blocker_kind": _r51_execution_blocker_kind(blocker),
        "execution_blocker_status": status,
        "readfeel_verdict_not_assigned": True,
        "body_free": True,
    }
    assert_p7_r51_execution_blocker_row_bodyfree_contract(row)
    return row


def assert_p7_r51_execution_blocker_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R51_EXECUTION_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS, source="p7_r51_execution_blocker_row_bodyfree")
    if data.get("schema_version") != P7_R51_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R51 execution blocker row schema changed")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r51_execution_blocker_row_bodyfree")
    if data.get("body_free") is not True:
        raise ValueError("R51 execution blocker row must be body-free")
    if data.get("review_kind") != P7_R51_REVIEW_KIND:
        raise ValueError("R51 execution blocker row review kind changed")
    family = clean_identifier(data.get("family"), default="", max_length=160)
    if family not in _r51_family_refs() and family != "session_level_execution_blocker":
        raise ValueError("R51 execution blocker row family changed")
    blocker = clean_identifier(data.get("execution_blocker_id"), default="", max_length=160)
    if blocker not in P7_R51_EXECUTION_BLOCKER_ID_REFS:
        raise ValueError("R51 execution blocker row id changed")
    if data.get("execution_blocker_kind") not in P7_R51_EXECUTION_BLOCKER_KIND_REFS:
        raise ValueError("R51 execution blocker kind changed")
    if data.get("execution_blocker_kind") != _r51_execution_blocker_kind(blocker):
        raise ValueError("R51 execution blocker kind must match blocker id classification")
    if data.get("execution_blocker_status") not in P7_R51_EXECUTION_BLOCKER_STATUS_REFS:
        raise ValueError("R51 execution blocker status changed")
    if data.get("readfeel_verdict_not_assigned") is not True:
        raise ValueError("R51 execution blocker rows must not assign readfeel verdicts")
    return True


def _r51_count_identifier_values(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = clean_identifier(safe_mapping(row).get(key), default="unknown", max_length=160)
        counts[value] = counts.get(value, 0) + 1
    return counts


def build_p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree(
    *,
    rating_row_normalizer_bodyfree: Mapping[str, Any] | None = None,
    r9_rating_row_normalizer_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree",
) -> dict[str, Any]:
    """Build R51-10 body-free readfeel/execution blocker ingestion rows."""

    if rating_row_normalizer_bodyfree is not None and r9_rating_row_normalizer_bodyfree is not None:
        raise ValueError("provide only one R51-9 rating row normalizer value")
    r9 = (
        safe_mapping(rating_row_normalizer_bodyfree)
        if rating_row_normalizer_bodyfree is not None
        else safe_mapping(r9_rating_row_normalizer_bodyfree)
        if r9_rating_row_normalizer_bodyfree is not None
        else build_p7_r51_rating_row_normalizer_bodyfree()
    )
    assert_p7_r51_rating_row_normalizer_bodyfree_contract(r9)
    r9_ready = r9.get("rating_row_normalizer_status") == "READY_FOR_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION" and not r9.get("execution_blocker_ids")
    blockers = dedupe_identifiers(r9.get("execution_blocker_ids") or [], limit=40, max_length=140)
    rating_rows = [safe_mapping(row) for row in r9.get("rating_rows") or []]
    readfeel_rows: list[dict[str, Any]] = []
    execution_rows: list[dict[str, Any]] = []
    reason_refs: list[str] = []

    if r9_ready:
        for rating_row in rating_rows:
            assert_p7_r51_rating_row_bodyfree_contract(rating_row)
            for blocker_id in rating_row.get("blocker_ids") or []:
                readfeel_rows.append(
                    build_p7_r51_readfeel_blocker_row_bodyfree(
                        rating_row=rating_row,
                        blocker_id=blocker_id,
                    )
                )
        status = "READY_FOR_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION"
        reason_refs = ["r51_rating_rows_available_readfeel_execution_blockers_separated"]
    else:
        status = "BLOCKED_BY_R51_9_RATING_ROW_NORMALIZER"
        reason_refs = ["r51_9_rating_row_normalizer_not_ready"]
        for blocker_id in blockers or ["r51_rating_rows_incomplete"]:
            execution_rows.append(
                build_p7_r51_execution_blocker_row_bodyfree(
                    execution_blocker_id=blocker_id,
                    review_session_id=r9.get("review_session_id"),
                )
            )
        blockers = dedupe_identifiers([row["execution_blocker_id"] for row in execution_rows], limit=40, max_length=140)

    ready = status == "READY_FOR_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION"
    actual_true_keys = (
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
    ) if ready else ()
    ingestion = {
        **_false_flags(),
        "schema_version": P7_R51_READFEEL_EXECUTION_BLOCKER_INGESTION_BODYFREE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R51_STEP,
        "scope": P7_R51_SCOPE,
        "policy_kind": P7_R51_POLICY_KIND,
        "policy_section": "R51-10_readfeel_blocker_execution_blocker_ingestion",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r9.get("review_session_id"), default=P7_R51_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_session_status": "R51_READFEEL_EXECUTION_BLOCKERS_INGESTED_BODYFREE" if ready else "PRECHECK_BLOCKED",
        "r9_rating_row_normalizer_schema_version": P7_R51_RATING_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION,
        "r9_rating_row_normalizer_ref": clean_identifier(r9.get("material_id"), default="p7_r51_rating_row_normalizer_bodyfree", max_length=180),
        "rating_row_normalizer_status": clean_identifier(r9.get("rating_row_normalizer_status"), default="BLOCKED_BY_R51_8_ACTUAL_HUMAN_REVIEW_RUN", max_length=120),
        "blocker_ingestion_status": status,
        "blocker_ingestion_reason_refs": reason_refs,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "rating_row_count": len(rating_rows),
        "readfeel_blocker_row_schema_version": P7_R51_READFEEL_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "r48_blocker_row_schema_version_ref": P7_R48_P5_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "execution_blocker_row_schema_version": P7_R51_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "r48_execution_blocker_row_schema_version_ref": P7_R48_P5_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "readfeel_blocker_row_required_field_refs": list(P7_R51_READFEEL_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS),
        "execution_blocker_row_required_field_refs": list(P7_R51_EXECUTION_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS),
        "readfeel_blocker_id_refs": list(P7_R48_READFEEL_BLOCKER_ID_REFS),
        "execution_blocker_id_refs": list(P7_R51_EXECUTION_BLOCKER_ID_REFS),
        "readfeel_blocker_kind_refs": list(P7_R48_P5_BLOCKER_KINDS),
        "readfeel_blocker_status_refs": list(P7_R48_P5_BLOCKER_STATUSES),
        "execution_blocker_kind_refs": list(P7_R51_EXECUTION_BLOCKER_KIND_REFS),
        "execution_blocker_status_refs": list(P7_R51_EXECUTION_BLOCKER_STATUS_REFS),
        "readfeel_blocker_rows": readfeel_rows,
        "execution_blocker_rows": execution_rows,
        "readfeel_blocker_row_count": len(readfeel_rows),
        "execution_blocker_row_count": len(execution_rows),
        "open_readfeel_blocker_count": sum(1 for row in readfeel_rows if row.get("blocker_status") == "OPEN"),
        "open_execution_blocker_count": sum(1 for row in execution_rows if row.get("execution_blocker_status") == "OPEN"),
        "readfeel_blocker_counts": _r51_count_identifier_values(readfeel_rows, "blocker_id"),
        "execution_blocker_counts": _r51_count_identifier_values(execution_rows, "execution_blocker_id"),
        "readfeel_and_execution_blockers_separated": True,
        "execution_blockers_do_not_assign_readfeel_verdict": True,
        "execution_blocker_cases_do_not_create_rating_rows": True,
        "rating_missing_maps_to_execution_blocker_not_red": True,
        "local_root_missing_maps_to_execution_blocker_not_red": True,
        "disposal_failed_maps_to_execution_blocker_not_red": True,
        "body_free_leak_maps_to_execution_blocker_not_red": True,
        "readfeel_blocker_row_builder_ready": ready,
        "execution_blocker_row_builder_ready": ready,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "actual_human_review_run_here": bool(ready and r9.get("actual_human_review_run_here") is True),
        "actual_manual_review_run_here": bool(ready and r9.get("actual_manual_review_run_here") is True),
        "actual_rating_rows_materialized_here": bool(ready and r9.get("actual_rating_rows_materialized_here") is True),
        "actual_blocker_rows_materialized_here": ready,
        "actual_execution_blocker_rows_materialized_here": ready,
        "actual_question_need_observation_rows_materialized_here": False,
        "p5_actual_review_still_not_run": not ready,
        "r0_current_source_r50_handoff_refrozen": True,
        "r1_validation_evidence_r49_timeout_handling_frozen": True,
        "r2_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r3_actual_review_session_envelope_created": True,
        "r4_24_case_manifest_freeze_built": True,
        "r5_local_only_body_full_packet_generation_request_built": True,
        "r6_body_full_packet_completeness_export_denylist_scan_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": bool(r9.get("r7_reviewer_instruction_rating_form_freeze_built")),
        "r8_actual_human_review_run_recorded": bool(r9.get("r8_actual_human_review_run_recorded")),
        "r9_rating_row_normalizer_built": bool(r9.get("r9_rating_row_normalizer_built")),
        "r10_readfeel_blocker_execution_blocker_ingestion_built": ready,
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        "implemented_steps": list(P7_R51_R10_IMPLEMENTED_STEPS if ready else P7_R51_R9_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R51_R10_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R51_R9_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R51_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R51_R10_NEXT_REQUIRED_STEP_REF if ready else P7_R51_R10_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r51_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(ingestion, allowed_true_false_key_refs=actual_true_keys)
    return ingestion


def build_p7_r51_readfeel_blocker_execution_blocker_ingestion(**kwargs: Any) -> dict[str, Any]:
    return build_p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree(**kwargs)


def assert_p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(
    ingestion: Mapping[str, Any],
    *,
    allowed_true_false_key_refs: Sequence[str] | None = None,
) -> bool:
    data = safe_mapping(ingestion)
    _assert_required_fields(data, required=P7_R51_READFEEL_EXECUTION_BLOCKER_INGESTION_BODYFREE_REQUIRED_FIELD_REFS, source="p7_r51_r10_readfeel_execution_blocker_ingestion")
    allowed = tuple(
        allowed_true_false_key_refs
        or (
            "actual_human_review_run_here",
            "actual_manual_review_run_here",
            "actual_rating_rows_materialized_here",
            "actual_blocker_rows_materialized_here",
            "actual_execution_blocker_rows_materialized_here",
        )
    )
    _assert_body_free_common_allowing(
        data,
        schema_version=P7_R51_READFEEL_EXECUTION_BLOCKER_INGESTION_BODYFREE_SCHEMA_VERSION,
        source="p7_r51_r10_readfeel_execution_blocker_ingestion",
        allowed_true_false_key_refs=allowed,
    )
    if data.get("policy_section") != "R51-10_readfeel_blocker_execution_blocker_ingestion":
        raise ValueError("R51 R10 policy section changed")
    if data.get("blocker_ingestion_status") not in P7_R51_READFEEL_EXECUTION_BLOCKER_INGESTION_STATUS_REFS:
        raise ValueError("R51 R10 blocker ingestion status changed")
    if data.get("readfeel_blocker_row_schema_version") != P7_R51_READFEEL_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R51 R10 readfeel blocker row schema changed")
    if data.get("execution_blocker_row_schema_version") != P7_R51_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R51 R10 execution blocker row schema changed")
    if tuple(data.get("readfeel_blocker_row_required_field_refs") or ()) != P7_R51_READFEEL_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS:
        raise ValueError("R51 R10 readfeel blocker row fields changed")
    if tuple(data.get("execution_blocker_row_required_field_refs") or ()) != P7_R51_EXECUTION_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS:
        raise ValueError("R51 R10 execution blocker row fields changed")
    if tuple(data.get("readfeel_blocker_id_refs") or ()) != P7_R48_READFEEL_BLOCKER_ID_REFS:
        raise ValueError("R51 R10 readfeel blocker ids changed")
    if tuple(data.get("execution_blocker_id_refs") or ()) != P7_R51_EXECUTION_BLOCKER_ID_REFS:
        raise ValueError("R51 R10 execution blocker ids changed")
    if tuple(data.get("execution_blocker_kind_refs") or ()) != P7_R51_EXECUTION_BLOCKER_KIND_REFS:
        raise ValueError("R51 R10 execution blocker kinds changed")
    if tuple(data.get("execution_blocker_status_refs") or ()) != P7_R51_EXECUTION_BLOCKER_STATUS_REFS:
        raise ValueError("R51 R10 execution blocker statuses changed")
    for row in data.get("readfeel_blocker_rows") or []:
        assert_p7_r51_readfeel_blocker_row_bodyfree_contract(safe_mapping(row))
    for row in data.get("execution_blocker_rows") or []:
        assert_p7_r51_execution_blocker_row_bodyfree_contract(safe_mapping(row))
    if data.get("readfeel_blocker_row_count") != len(data.get("readfeel_blocker_rows") or []):
        raise ValueError("R51 R10 readfeel blocker row count mismatch")
    if data.get("execution_blocker_row_count") != len(data.get("execution_blocker_rows") or []):
        raise ValueError("R51 R10 execution blocker row count mismatch")
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
            raise ValueError(f"R51 R10 must keep {true_key}=True")
    for false_key in (
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
        "actual_question_need_observation_rows_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R51 R10 must keep {false_key}=False")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R51 R10 open blockers must match execution blockers")
    unknown = sorted(set(blockers) - set(P7_R51_EXECUTION_BLOCKER_ID_REFS))
    if unknown:
        raise ValueError(f"R51 R10 execution blockers are not canonical: {unknown[:4]}")
    ready = data.get("blocker_ingestion_status") == "READY_FOR_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION"
    if ready:
        if data.get("rating_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R51 R10 ready ingestion requires 24 rating rows")
        if data.get("readfeel_blocker_row_builder_ready") is not True or data.get("execution_blocker_row_builder_ready") is not True:
            raise ValueError("R51 R10 ready ingestion requires row builders ready")
        if data.get("actual_human_review_run_here") is not True or data.get("actual_manual_review_run_here") is not True:
            raise ValueError("R51 R10 ready ingestion must preserve actual review evidence")
        if data.get("actual_rating_rows_materialized_here") is not True:
            raise ValueError("R51 R10 ready ingestion must preserve rating row materialization")
        if data.get("actual_blocker_rows_materialized_here") is not True or data.get("actual_execution_blocker_rows_materialized_here") is not True:
            raise ValueError("R51 R10 ready ingestion must materialize body-free blocker rows")
        if data.get("p5_actual_review_still_not_run") is not False:
            raise ValueError("R51 R10 ready ingestion must not say actual review is still unrun")
        if blockers:
            raise ValueError("R51 R10 ready ingestion must not carry open execution blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R51_R10_IMPLEMENTED_STEPS:
            raise ValueError("R51 R10 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R51_R10_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R51 R10 not-yet steps changed")
        if data.get("next_required_step") != P7_R51_R10_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R10 ready ingestion must point to R51-11")
    else:
        if data.get("readfeel_blocker_row_builder_ready") is not False or data.get("execution_blocker_row_builder_ready") is not False:
            raise ValueError("R51 R10 blocked ingestion must disable row builders")
        if data.get("actual_blocker_rows_materialized_here") is not False or data.get("actual_execution_blocker_rows_materialized_here") is not False:
            raise ValueError("R51 R10 blocked ingestion must not materialize blocker rows")
        if data.get("r10_readfeel_blocker_execution_blocker_ingestion_built") is not False:
            raise ValueError("R51 R10 blocked ingestion must not claim built")
        if data.get("next_required_step") != P7_R51_R10_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R10 blocked ingestion must point to R51-9 resolution")
    return True


def _default_one_question_fit_for_primary_r51(primary_class: str) -> str:
    mapping = {
        "no_question_needed_emlis_can_observe": "not_needed",
        "question_may_reduce_overread_risk": "fits_one_question",
        "question_would_make_immediate_observation_heavy": "would_delay_immediate_observation",
        "not_question_emlis_readfeel_repair_required": "repair_required_not_question",
        "not_question_p5_surface_repair_required": "repair_required_not_question",
        "not_question_gate_boundary_required": "repair_required_not_question",
        "plus_single_question_candidate_later": "fits_one_question",
        "premium_deep_dive_candidate_later": "needs_more_than_one_question_not_p7",
        "insufficient_material_execution_blocker": "insufficient_material",
    }
    if primary_class not in mapping:
        raise ValueError("R51 R11 question observation primary class must use the frozen enum")
    return mapping[primary_class]


def _default_repair_refs_for_primary_r51(primary_class: str) -> list[str]:
    if primary_class == "not_question_emlis_readfeel_repair_required":
        return ["emlis_readfeel_repair_required"]
    if primary_class == "not_question_p5_surface_repair_required":
        return ["p5_surface_repair_required"]
    if primary_class == "not_question_gate_boundary_required":
        return ["gate_boundary_repair_required"]
    return ["no_repair_required"]


def _normalize_plan_candidate_flags_r51(primary_class: str, raw_flags: Any) -> list[str]:
    if isinstance(raw_flags, Mapping):
        supplied = [clean_identifier(key, default="", max_length=120) for key, value in raw_flags.items() if bool(value)]
    elif raw_flags is None:
        supplied = []
    else:
        supplied = _allowed_identifier_sequence_r51(
            raw_flags,
            source="p7_r51_question_observation.plan_candidate_flags",
            allowed_refs=P7_R50_PLAN_CANDIDATE_FLAG_REFS,
            limit=10,
            max_length=120,
        )
    supplied = dedupe_identifiers(supplied, limit=10, max_length=120)
    unknown = sorted(set(supplied) - set(P7_R50_PLAN_CANDIDATE_FLAG_REFS))
    if unknown:
        raise ValueError(f"R51 R11 plan candidate flags are outside the frozen enum: {unknown[:4]}")
    p8_material_primary_classes = {
        "no_question_needed_emlis_can_observe",
        "question_may_reduce_overread_risk",
        "question_would_make_immediate_observation_heavy",
        "plus_single_question_candidate_later",
        "premium_deep_dive_candidate_later",
    }
    repair_or_execution_primary_classes = {
        "not_question_emlis_readfeel_repair_required",
        "not_question_p5_surface_repair_required",
        "not_question_gate_boundary_required",
        "insufficient_material_execution_blocker",
    }
    flags = set(supplied)
    if primary_class == "plus_single_question_candidate_later":
        flags.add("plus_single_question_candidate_later")
    elif "plus_single_question_candidate_later" in flags:
        raise ValueError("R51 R11 plus question candidate flag must match plus primary class")
    if primary_class == "premium_deep_dive_candidate_later":
        flags.add("premium_deep_dive_candidate_later")
    elif "premium_deep_dive_candidate_later" in flags:
        raise ValueError("R51 R11 premium deep-dive flag must match premium primary class")
    if primary_class in p8_material_primary_classes:
        flags.add("p8_design_material_candidate")
    if primary_class in repair_or_execution_primary_classes and flags:
        raise ValueError("R51 R11 repair/execution observations must not be marked as P8 question candidates")
    return [ref for ref in P7_R50_PLAN_CANDIDATE_FLAG_REFS if ref in flags]


def _matching_execution_blocker_for_question_observation_r51(qrow: Mapping[str, Any], execution_blocker_rows: Sequence[Mapping[str, Any]] | None) -> bool:
    if not execution_blocker_rows:
        return False
    qid = _r51_case_identity(qrow)
    for raw in execution_blocker_rows:
        erow = safe_mapping(raw)
        if not erow:
            continue
        assert_p7_r51_execution_blocker_row_bodyfree_contract(erow)
        if _r51_case_identity(erow) == qid:
            return True
    return False


def _validate_question_observation_semantics_r51(
    row: Mapping[str, Any],
    *,
    execution_blocker_rows: Sequence[Mapping[str, Any]] | None = None,
    require_execution_blocker_match: bool = False,
) -> None:
    data = safe_mapping(row)
    primary = clean_identifier(data.get("question_need_primary_class"), default="", max_length=160)
    one_fit = clean_identifier(data.get("one_question_fit_ref"), default="", max_length=160)
    repairs = tuple(data.get("repair_required_refs") or ())
    ambiguity = tuple(data.get("ambiguity_kind_refs") or ())
    plan_flags = tuple(data.get("plan_candidate_flags") or ())
    if primary not in P7_R50_QUESTION_NEED_PRIMARY_CLASS_REFS:
        raise ValueError("R51 question observation primary class must use the frozen enum")
    if one_fit not in P7_R50_ONE_QUESTION_FIT_REFS:
        raise ValueError("R51 question observation one_question_fit_ref must use the frozen enum")
    if one_fit != _default_one_question_fit_for_primary_r51(primary):
        raise ValueError("R51 question observation primary class and one-question fit are inconsistent")
    if not repairs:
        raise ValueError("R51 question observation repair_required_refs must be explicit")
    if "no_repair_required" in repairs and len(repairs) > 1:
        raise ValueError("R51 question observation no_repair_required must not mix with repair refs")
    for ref in repairs:
        if ref not in P7_R50_REPAIR_REQUIRED_REF_REFS:
            raise ValueError("R51 question observation repair refs must use the frozen enum")
    for ref in ambiguity:
        if ref not in P7_R50_AMBIGUITY_KIND_REFS:
            raise ValueError("R51 question observation ambiguity refs must use the frozen enum")
    for ref in plan_flags:
        if ref not in P7_R50_PLAN_CANDIDATE_FLAG_REFS:
            raise ValueError("R51 question observation plan flags must use the frozen enum")
    if primary.startswith("not_question_"):
        required = set(_default_repair_refs_for_primary_r51(primary))
        if not required <= set(repairs):
            raise ValueError("R51 repair primary classes require the matching repair ref")
        if plan_flags:
            raise ValueError("R51 repair primary classes must not become P8 question material candidates")
    if primary == "insufficient_material_execution_blocker":
        if one_fit != "insufficient_material":
            raise ValueError("R51 insufficient-material observation must use insufficient_material one-question fit")
        if repairs != ("no_repair_required",):
            raise ValueError("R51 insufficient-material observation must not carry repair refs")
        if plan_flags:
            raise ValueError("R51 insufficient-material observation must not become P8 question material")
        if require_execution_blocker_match and not _matching_execution_blocker_for_question_observation_r51(data, execution_blocker_rows):
            raise ValueError("R51 insufficient-material question observation requires a matching execution blocker row")
    if primary == "no_question_needed_emlis_can_observe":
        if repairs != ("no_repair_required",):
            raise ValueError("R51 no-question-needed observation must not carry repair refs")
        if set(ambiguity) != {"no_material_ambiguity"}:
            raise ValueError("R51 no-question-needed observation must carry only no_material_ambiguity")
    question_candidate_primary_classes = {
        "question_may_reduce_overread_risk",
        "question_would_make_immediate_observation_heavy",
        "plus_single_question_candidate_later",
        "premium_deep_dive_candidate_later",
    }
    if primary in question_candidate_primary_classes:
        if not ambiguity or "no_material_ambiguity" in ambiguity:
            raise ValueError("R51 question candidate observations require a concrete body-free ambiguity kind")
        if repairs != ("no_repair_required",):
            raise ValueError("R51 question candidate observations must not carry repair refs")
        if "p8_design_material_candidate" not in plan_flags:
            raise ValueError("R51 question candidate observations must be P8 design material candidates")
    if primary == "plus_single_question_candidate_later" and "plus_single_question_candidate_later" not in plan_flags:
        raise ValueError("R51 plus-single-question observations require the plus overlay flag")
    if primary == "premium_deep_dive_candidate_later" and "premium_deep_dive_candidate_later" not in plan_flags:
        raise ValueError("R51 premium-deep-dive observations require the premium overlay flag")


def normalize_p7_r51_question_need_observation_row_bodyfree(
    *,
    review_capture_row: Mapping[str, Any],
    plan_candidate_flags: Sequence[Any] | Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize one sanitized R51 review capture row into a question-need row."""

    capture = safe_mapping(review_capture_row)
    _assert_r51_actual_review_capture_row(capture)
    primary = clean_identifier(capture.get("question_need_primary_class"), default="", max_length=160)
    if primary not in P7_R50_QUESTION_NEED_PRIMARY_CLASS_REFS:
        raise ValueError("R51 R11 question observation primary class must use the frozen enum")
    ambiguity_default = ["no_material_ambiguity"] if primary == "no_question_needed_emlis_can_observe" else []
    ambiguity_refs = _allowed_identifier_sequence_r51(
        capture.get("ambiguity_kind_refs") if capture.get("ambiguity_kind_refs") is not None else ambiguity_default,
        source="p7_r51_question_observation.ambiguity_kind_refs",
        allowed_refs=P7_R50_AMBIGUITY_KIND_REFS,
        limit=12,
    )
    one_question_fit_ref = clean_identifier(
        capture.get("one_question_fit_ref"),
        default=_default_one_question_fit_for_primary_r51(primary),
        max_length=160,
    )
    if one_question_fit_ref not in P7_R50_ONE_QUESTION_FIT_REFS:
        raise ValueError("R51 R11 question observation one_question_fit_ref must use the frozen enum")
    repair_refs = _allowed_identifier_sequence_r51(
        capture.get("repair_required_refs") if capture.get("repair_required_refs") is not None else _default_repair_refs_for_primary_r51(primary),
        source="p7_r51_question_observation.repair_required_refs",
        allowed_refs=P7_R50_REPAIR_REQUIRED_REF_REFS,
        limit=6,
    )
    if not repair_refs:
        repair_refs = _default_repair_refs_for_primary_r51(primary)
    flags_source = plan_candidate_flags if plan_candidate_flags is not None else capture.get("plan_candidate_flags")
    plan_flags = _normalize_plan_candidate_flags_r51(primary, flags_source)
    sanitized_reason_ids = dedupe_identifiers([primary], limit=12, max_length=160)
    row = {
        "schema_version": P7_R51_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION,
        "review_session_id": clean_identifier(capture.get("review_session_id"), default=P7_R51_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "packet_ref_id": clean_identifier(capture.get("packet_ref_id"), default="packet_ref", max_length=160),
        "blind_case_id": clean_identifier(capture.get("blind_case_id"), default="blind_case", max_length=160),
        "case_ref_id": clean_identifier(capture.get("case_ref_id"), default="case_ref", max_length=160),
        "family": clean_identifier(capture.get("family"), default="family", max_length=160),
        "case_role": clean_identifier(capture.get("case_role"), default="case_role", max_length=160),
        "review_kind": P7_R51_REVIEW_KIND,
        "observation_stage": P7_R50_QUESTION_NEED_OBSERVATION_STAGE_REF,
        "question_need_primary_class": primary,
        "ambiguity_kind_refs": ambiguity_refs,
        "one_question_fit_ref": one_question_fit_ref,
        "plan_candidate_flags": plan_flags,
        "repair_required_refs": repair_refs,
        "sanitized_reason_ids": sanitized_reason_ids,
        "question_text_included": False,
        "draft_question_text_included": False,
        "reviewer_free_text_included": False,
        "body_removed": bool(capture.get("body_removed", False)),
        "body_free": True,
    }
    assert_p7_r51_question_need_observation_row_bodyfree_contract(row)
    return row


def assert_p7_r51_question_need_observation_row_bodyfree_contract(
    row: Mapping[str, Any],
    *,
    execution_blocker_rows: Sequence[Mapping[str, Any]] | None = None,
    require_execution_blocker_match: bool = False,
) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R51_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_REQUIRED_FIELD_REFS, source="p7_r51_question_need_observation_row_bodyfree")
    if data.get("schema_version") != P7_R51_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R51 question observation row schema changed")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r51_question_need_observation_row_bodyfree")
    if data.get("body_free") is not True:
        raise ValueError("R51 question observation row must be body-free")
    if data.get("family") not in _r51_family_refs():
        raise ValueError("R51 question observation row family changed")
    if data.get("case_role") not in P7_R48_P5_CASE_ROLE_REFS:
        raise ValueError("R51 question observation row case_role changed")
    if data.get("review_kind") != P7_R51_REVIEW_KIND:
        raise ValueError("R51 question observation row review kind changed")
    if data.get("observation_stage") != P7_R50_QUESTION_NEED_OBSERVATION_STAGE_REF:
        raise ValueError("R51 question observation stage changed")
    _allowed_identifier_sequence_r51(data.get("ambiguity_kind_refs"), source="p7_r51_question_observation.ambiguity_kind_refs", allowed_refs=P7_R50_AMBIGUITY_KIND_REFS)
    _allowed_identifier_sequence_r51(data.get("repair_required_refs"), source="p7_r51_question_observation.repair_required_refs", allowed_refs=P7_R50_REPAIR_REQUIRED_REF_REFS)
    _allowed_identifier_sequence_r51(data.get("plan_candidate_flags"), source="p7_r51_question_observation.plan_candidate_flags", allowed_refs=P7_R50_PLAN_CANDIDATE_FLAG_REFS)
    _allowed_identifier_sequence_r51(data.get("sanitized_reason_ids"), source="p7_r51_question_observation.sanitized_reason_ids", allowed_refs=None, limit=40)
    _validate_question_observation_semantics_r51(
        data,
        execution_blocker_rows=execution_blocker_rows,
        require_execution_blocker_match=require_execution_blocker_match,
    )
    for false_key in ("question_text_included", "draft_question_text_included", "reviewer_free_text_included"):
        if data.get(false_key) is not False:
            raise ValueError(f"R51 question observation row must keep {false_key}=False")
    if not isinstance(data.get("body_removed"), bool):
        raise ValueError("R51 question observation row body_removed must be boolean")
    return True


def _sequence_count_refs_r51(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row_raw in rows:
        row = safe_mapping(row_raw)
        values = row.get(key) or []
        for ref in dedupe_identifiers(values, limit=20, max_length=160):
            counts[ref] = counts.get(ref, 0) + 1
    return counts


def build_p7_r51_question_need_observation_row_normalizer_bodyfree(
    *,
    readfeel_blocker_execution_blocker_ingestion_bodyfree: Mapping[str, Any] | None = None,
    r10_readfeel_blocker_execution_blocker_ingestion_bodyfree: Mapping[str, Any] | None = None,
    actual_human_review_run: Mapping[str, Any] | None = None,
    r8_actual_human_review_run: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r51_question_need_observation_row_normalizer_bodyfree",
) -> dict[str, Any]:
    """Build R51-11 body-free question-need observation rows from R51-8 selections."""

    if readfeel_blocker_execution_blocker_ingestion_bodyfree is not None and r10_readfeel_blocker_execution_blocker_ingestion_bodyfree is not None:
        raise ValueError("provide only one R51-10 blocker ingestion value")
    if actual_human_review_run is not None and r8_actual_human_review_run is not None:
        raise ValueError("provide only one R51-8 actual review run value")
    r10 = (
        safe_mapping(readfeel_blocker_execution_blocker_ingestion_bodyfree)
        if readfeel_blocker_execution_blocker_ingestion_bodyfree is not None
        else safe_mapping(r10_readfeel_blocker_execution_blocker_ingestion_bodyfree)
        if r10_readfeel_blocker_execution_blocker_ingestion_bodyfree is not None
        else build_p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree()
    )
    assert_p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(r10)
    r8 = (
        safe_mapping(actual_human_review_run)
        if actual_human_review_run is not None
        else safe_mapping(r8_actual_human_review_run)
        if r8_actual_human_review_run is not None
        else build_p7_r51_actual_human_review_run_bodyfree()
    )
    assert_p7_r51_actual_human_review_run_bodyfree_contract(r8)

    r10_ready = r10.get("blocker_ingestion_status") == "READY_FOR_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION" and not r10.get("execution_blocker_ids")
    r8_ready = r8.get("actual_review_run_status") == "READY_FOR_RATING_ROW_NORMALIZATION" and not r8.get("execution_blocker_ids")
    question_rows: list[dict[str, Any]] = []
    reason_refs: list[str] = []
    blockers = dedupe_identifiers([*(r10.get("execution_blocker_ids") or []), *(r8.get("execution_blocker_ids") or [])], limit=40, max_length=140)
    if r10_ready and r8_ready:
        try:
            question_rows = [
                normalize_p7_r51_question_need_observation_row_bodyfree(review_capture_row=safe_mapping(row))
                for row in r8.get("review_result_capture_rows") or []
            ]
        except ValueError:
            status = "BLOCKED_BY_QUESTION_OBSERVATION_ROW_VALIDATION"
            reason_refs = ["r51_question_need_observation_row_validation_failed"]
            blockers = dedupe_identifiers([*blockers, "r51_question_need_observation_rows_incomplete"], limit=40, max_length=140)
        else:
            status = "READY_FOR_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD"
            reason_refs = ["r51_question_need_observation_rows_normalized_bodyfree"]
    else:
        question_rows = []
        if not r10_ready:
            status = "BLOCKED_BY_R51_10_BLOCKER_INGESTION"
            reason_refs.append("r51_10_blocker_ingestion_not_ready")
        else:
            status = "BLOCKED_BY_R51_8_ACTUAL_HUMAN_REVIEW_RUN"
            reason_refs.append("r51_8_actual_human_review_run_not_ready")
        if not blockers:
            blockers = ["r51_question_need_observation_rows_incomplete"]

    ready = status == "READY_FOR_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD" and len(question_rows) == P7_R51_REQUIRED_CASE_COUNT and not blockers
    review_case_refs = _r51_case_refs([safe_mapping(row) for row in r8.get("review_result_capture_rows") or []], "case_ref_id") if r8_ready else []
    question_case_refs = _r51_case_refs(question_rows, "case_ref_id")
    row_case_match_review = bool(review_case_refs == question_case_refs and len(question_case_refs) == P7_R51_REQUIRED_CASE_COUNT) if ready else False
    row_case_match_rating = bool(r10.get("rating_row_count") == len(question_rows) == P7_R51_REQUIRED_CASE_COUNT) if ready else False
    actual_true_keys = (
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
    ) if ready else ()
    normalizer = {
        **_false_flags(),
        "schema_version": P7_R51_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R51_STEP,
        "scope": P7_R51_SCOPE,
        "policy_kind": P7_R51_POLICY_KIND,
        "policy_section": "R51-11_question_need_observation_row_normalization",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r51_question_need_observation_row_normalizer_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r10.get("review_session_id") or r8.get("review_session_id"), default=P7_R51_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_session_status": "R51_QUESTION_NEED_OBSERVATION_ROWS_NORMALIZED_BODYFREE" if ready else "PRECHECK_BLOCKED",
        "r10_blocker_ingestion_schema_version": P7_R51_READFEEL_EXECUTION_BLOCKER_INGESTION_BODYFREE_SCHEMA_VERSION,
        "r10_blocker_ingestion_ref": clean_identifier(r10.get("material_id"), default="p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree", max_length=180),
        "blocker_ingestion_status": clean_identifier(r10.get("blocker_ingestion_status"), default="BLOCKED_BY_R51_9_RATING_ROW_NORMALIZER", max_length=120),
        "r8_actual_human_review_run_schema_version": P7_R51_ACTUAL_HUMAN_REVIEW_RUN_SCHEMA_VERSION,
        "r8_actual_human_review_run_ref": clean_identifier(r8.get("material_id"), default="p7_r51_actual_human_review_run_bodyfree", max_length=180),
        "actual_review_run_status": clean_identifier(r8.get("actual_review_run_status"), default="BLOCKED_BY_ACTUAL_REVIEW_RESULT_ROWS", max_length=120),
        "question_observation_normalizer_status": status,
        "question_observation_normalizer_reason_refs": dedupe_identifiers(reason_refs, limit=20, max_length=160),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "review_result_capture_row_count": _safe_non_negative_int(r8.get("review_result_capture_row_count")),
        "rating_row_count": _safe_non_negative_int(r10.get("rating_row_count")),
        "question_observation_row_count": len(question_rows),
        "question_need_observation_rows": question_rows,
        "question_need_observation_row_schema_version": P7_R51_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION,
        "question_need_observation_row_required_field_refs": list(P7_R51_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_REQUIRED_FIELD_REFS),
        "question_need_observation_row_forbidden_field_refs": list(P7_R51_ACTUAL_REVIEW_RESULT_INPUT_FORBIDDEN_KEY_REFS),
        "question_need_primary_class_refs": list(P7_R50_QUESTION_NEED_PRIMARY_CLASS_REFS),
        "ambiguity_kind_refs": list(P7_R50_AMBIGUITY_KIND_REFS),
        "one_question_fit_refs": list(P7_R50_ONE_QUESTION_FIT_REFS),
        "plan_candidate_flag_refs": list(P7_R50_PLAN_CANDIDATE_FLAG_REFS),
        "repair_required_ref_refs": list(P7_R50_REPAIR_REQUIRED_REF_REFS),
        "question_need_observation_stage_ref": P7_R50_QUESTION_NEED_OBSERVATION_STAGE_REF,
        "review_kind": P7_R51_REVIEW_KIND,
        "question_need_observation_rows_must_be_bodyfree": True,
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
        "row_case_ref_sets_match_review_capture": row_case_match_review,
        "row_case_ref_sets_match_rating_rows": row_case_match_rating,
        "all_required_question_need_observation_rows_present": ready,
        "question_need_primary_class_counts": _r51_count_identifier_values(question_rows, "question_need_primary_class"),
        "ambiguity_kind_counts": _sequence_count_refs_r51(question_rows, "ambiguity_kind_refs"),
        "one_question_fit_counts": _r51_count_identifier_values(question_rows, "one_question_fit_ref"),
        "repair_required_counts": _sequence_count_refs_r51(question_rows, "repair_required_refs"),
        "plan_candidate_flag_counts": _sequence_count_refs_r51(question_rows, "plan_candidate_flags"),
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "actual_human_review_run_here": bool(ready and r8.get("actual_human_review_run_here") is True),
        "actual_manual_review_run_here": bool(ready and r8.get("actual_manual_review_run_here") is True),
        "actual_rating_rows_materialized_here": bool(ready and r10.get("actual_rating_rows_materialized_here") is True),
        "actual_blocker_rows_materialized_here": bool(ready and r10.get("actual_blocker_rows_materialized_here") is True),
        "actual_execution_blocker_rows_materialized_here": bool(ready and r10.get("actual_execution_blocker_rows_materialized_here") is True),
        "actual_question_need_observation_rows_materialized_here": ready,
        "actual_question_need_observation_summary_materialized_here": False,
        "p5_actual_review_still_not_run": not ready,
        "r0_current_source_r50_handoff_refrozen": True,
        "r1_validation_evidence_r49_timeout_handling_frozen": True,
        "r2_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r3_actual_review_session_envelope_created": True,
        "r4_24_case_manifest_freeze_built": True,
        "r5_local_only_body_full_packet_generation_request_built": True,
        "r6_body_full_packet_completeness_export_denylist_scan_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": bool(r8.get("r7_reviewer_instruction_rating_form_freeze_built")),
        "r8_actual_human_review_run_recorded": bool(r8.get("r8_actual_human_review_run_recorded")),
        "r9_rating_row_normalizer_built": bool(r10.get("r9_rating_row_normalizer_built")),
        "r10_readfeel_blocker_execution_blocker_ingestion_built": bool(r10.get("r10_readfeel_blocker_execution_blocker_ingestion_built")),
        "r11_question_need_observation_row_normalizer_built": ready,
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        "implemented_steps": list(P7_R51_R11_IMPLEMENTED_STEPS if ready else P7_R51_R10_IMPLEMENTED_STEPS if r10_ready else P7_R51_R9_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R51_R11_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R51_R10_NOT_YET_IMPLEMENTED_STEPS if r10_ready else P7_R51_R9_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R51_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R51_R11_NEXT_REQUIRED_STEP_REF if ready else P7_R51_R11_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r51_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r51_question_need_observation_row_normalizer_bodyfree_contract(normalizer, allowed_true_false_key_refs=actual_true_keys)
    return normalizer


def build_p7_r51_question_need_observation_row_normalizer(**kwargs: Any) -> dict[str, Any]:
    return build_p7_r51_question_need_observation_row_normalizer_bodyfree(**kwargs)


def assert_p7_r51_question_need_observation_row_normalizer_bodyfree_contract(
    normalizer: Mapping[str, Any],
    *,
    allowed_true_false_key_refs: Sequence[str] | None = None,
) -> bool:
    data = safe_mapping(normalizer)
    _assert_required_fields(data, required=P7_R51_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_BODYFREE_REQUIRED_FIELD_REFS, source="p7_r51_r11_question_need_observation_row_normalizer")
    allowed = tuple(
        allowed_true_false_key_refs
        or (
            "actual_human_review_run_here",
            "actual_manual_review_run_here",
            "actual_rating_rows_materialized_here",
            "actual_blocker_rows_materialized_here",
            "actual_execution_blocker_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
        )
    )
    _assert_body_free_common_allowing(
        data,
        schema_version=P7_R51_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION,
        source="p7_r51_r11_question_need_observation_row_normalizer",
        allowed_true_false_key_refs=allowed,
    )
    if data.get("policy_section") != "R51-11_question_need_observation_row_normalization":
        raise ValueError("R51 R11 policy section changed")
    if data.get("question_observation_normalizer_status") not in P7_R51_QUESTION_OBSERVATION_NORMALIZER_STATUS_REFS:
        raise ValueError("R51 R11 normalizer status changed")
    if data.get("question_need_observation_row_schema_version") != P7_R51_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R51 R11 question observation row schema changed")
    if tuple(data.get("question_need_observation_row_required_field_refs") or ()) != P7_R51_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_REQUIRED_FIELD_REFS:
        raise ValueError("R51 R11 question observation row fields changed")
    for ref_name, expected in (
        ("question_need_primary_class_refs", P7_R50_QUESTION_NEED_PRIMARY_CLASS_REFS),
        ("ambiguity_kind_refs", P7_R50_AMBIGUITY_KIND_REFS),
        ("one_question_fit_refs", P7_R50_ONE_QUESTION_FIT_REFS),
        ("plan_candidate_flag_refs", P7_R50_PLAN_CANDIDATE_FLAG_REFS),
        ("repair_required_ref_refs", P7_R50_REPAIR_REQUIRED_REF_REFS),
    ):
        if tuple(data.get(ref_name) or ()) != expected:
            raise ValueError(f"R51 R11 {ref_name} changed")
    if data.get("question_need_observation_stage_ref") != P7_R50_QUESTION_NEED_OBSERVATION_STAGE_REF:
        raise ValueError("R51 R11 question observation stage changed")
    for row in data.get("question_need_observation_rows") or []:
        assert_p7_r51_question_need_observation_row_bodyfree_contract(safe_mapping(row))
    for true_key in ("question_need_observation_rows_must_be_bodyfree",):
        if data.get(true_key) is not True:
            raise ValueError(f"R51 R11 must keep {true_key}=True")
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
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R51 R11 must keep {false_key}=False")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R51 R11 open blockers must match execution blockers")
    unknown = sorted(set(blockers) - set(P7_R51_EXECUTION_BLOCKER_ID_REFS))
    if unknown:
        raise ValueError(f"R51 R11 execution blockers are not canonical: {unknown[:4]}")
    ready = data.get("question_observation_normalizer_status") == "READY_FOR_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD"
    if ready:
        if data.get("question_observation_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R51 R11 ready normalizer must carry 24 question rows")
        if data.get("row_case_ref_sets_match_review_capture") is not True:
            raise ValueError("R51 R11 ready normalizer must match R8 capture case refs")
        if data.get("row_case_ref_sets_match_rating_rows") is not True:
            raise ValueError("R51 R11 ready normalizer must match R9 rating row count")
        if data.get("all_required_question_need_observation_rows_present") is not True:
            raise ValueError("R51 R11 ready normalizer must mark all question rows present")
        if data.get("actual_human_review_run_here") is not True or data.get("actual_manual_review_run_here") is not True:
            raise ValueError("R51 R11 ready normalizer must preserve actual review evidence")
        if data.get("actual_rating_rows_materialized_here") is not True:
            raise ValueError("R51 R11 ready normalizer must preserve rating rows")
        if data.get("actual_question_need_observation_rows_materialized_here") is not True:
            raise ValueError("R51 R11 ready normalizer must materialize question observation rows")
        if data.get("p5_actual_review_still_not_run") is not False:
            raise ValueError("R51 R11 ready normalizer must not say actual review is still unrun")
        if blockers:
            raise ValueError("R51 R11 ready normalizer must not carry open execution blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R51_R11_IMPLEMENTED_STEPS:
            raise ValueError("R51 R11 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R51_R11_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R51 R11 not-yet steps changed")
        if data.get("next_required_step") != P7_R51_R11_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R11 ready normalizer must point to R51-12")
    else:
        if data.get("actual_question_need_observation_rows_materialized_here") is not False:
            raise ValueError("R51 R11 blocked normalizer must not materialize question rows")
        if data.get("r11_question_need_observation_row_normalizer_built") is not False:
            raise ValueError("R51 R11 blocked normalizer must not claim built")
        if data.get("next_required_step") != P7_R51_R11_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R11 blocked normalizer must point to blocker ingestion resolution")
    return True


# ---------------------------------------------------------------------------
# R51-12 / R51-13: consistency guard and pause / abort / expiration protocol
# ---------------------------------------------------------------------------

P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_ROW_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "packet_ref_id",
    "blind_case_id",
    "case_ref_id",
    "family",
    "case_role",
    "review_kind",
    "consistency_issue_id",
    "consistency_issue_kind",
    "consistency_issue_status",
    "rating_verdict_ref",
    "question_need_primary_class",
    "blocker_ids",
    "plan_candidate_flags",
    "repair_required_refs",
    "sanitized_reason_ids",
    "p5_repair_return_required",
    "p8_question_candidate_blocked",
    "body_free",
)
P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "review_session_status",
    "r9_rating_row_normalizer_schema_version",
    "r9_rating_row_normalizer_ref",
    "rating_row_normalizer_status",
    "r10_blocker_ingestion_schema_version",
    "r10_blocker_ingestion_ref",
    "blocker_ingestion_status",
    "r11_question_observation_normalizer_schema_version",
    "r11_question_observation_normalizer_ref",
    "question_observation_normalizer_status",
    "rating_question_consistency_guard_status",
    "consistency_guard_reason_refs",
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
    "p5_weakness_not_hidden_by_question_candidate",
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
    "r0_current_source_r50_handoff_refrozen",
    "r1_validation_evidence_r49_timeout_handling_frozen",
    "r2_local_root_explicit_allow_purge_plan_preflight_built",
    "r3_actual_review_session_envelope_created",
    "r4_24_case_manifest_freeze_built",
    "r5_local_only_body_full_packet_generation_request_built",
    "r6_body_full_packet_completeness_export_denylist_scan_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_actual_human_review_run_recorded",
    "r9_rating_row_normalizer_built",
    "r10_readfeel_blocker_execution_blocker_ingestion_built",
    "r11_question_need_observation_row_normalizer_built",
    "r12_rating_question_observation_consistency_guard_built",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r51_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R51_R0_R1_FALSE_KEY_REFS,
)
P7_R51_PAUSE_ABORT_EXPIRATION_PROTOCOL_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "review_session_status",
    "r12_consistency_guard_schema_version",
    "r12_consistency_guard_ref",
    "rating_question_consistency_guard_status",
    "pause_abort_expiration_protocol_status",
    "pause_abort_expiration_reason_refs",
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
    "r0_current_source_r50_handoff_refrozen",
    "r1_validation_evidence_r49_timeout_handling_frozen",
    "r2_local_root_explicit_allow_purge_plan_preflight_built",
    "r3_actual_review_session_envelope_created",
    "r4_24_case_manifest_freeze_built",
    "r5_local_only_body_full_packet_generation_request_built",
    "r6_body_full_packet_completeness_export_denylist_scan_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_actual_human_review_run_recorded",
    "r9_rating_row_normalizer_built",
    "r10_readfeel_blocker_execution_blocker_ingestion_built",
    "r11_question_need_observation_row_normalizer_built",
    "r12_rating_question_observation_consistency_guard_built",
    "r13_pause_abort_expiration_protocol_built",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r51_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R51_R0_R1_FALSE_KEY_REFS,
)


# ---------------------------------------------------------------------------
# R51-14 / R51-15: local-only purge verification and disposal receipt
# ---------------------------------------------------------------------------

P7_R51_PURGE_EVIDENCE_ROW_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "purge_target_ref",
    "purge_target_kind",
    "purge_required",
    "purge_attempted",
    "removed",
    "removed_count",
    "verification_status_ref",
    "local_absolute_path_included",
    "body_content_hash_included",
    "deleted_body_preview_included",
    "terminal_output_included",
    "body_free",
)
P7_R51_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "review_session_status",
    "r13_pause_abort_expiration_protocol_schema_version",
    "r13_pause_abort_expiration_protocol_ref",
    "pause_abort_expiration_protocol_status",
    "review_lifecycle_status",
    "purge_status",
    "purge_reason_refs",
    "required_case_count",
    "purge_required_before_summary",
    "body_full_packet_purge_required",
    "reviewer_forms_purge_required",
    "reviewer_notes_purge_required",
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
    "disposal_status",
    "body_removed",
    "reviewer_forms_removed",
    "reviewer_notes_removed",
    "body_full_packets_removed",
    "local_packet_exported",
    "content_hash_of_body_stored",
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
    "r0_current_source_r50_handoff_refrozen",
    "r1_validation_evidence_r49_timeout_handling_frozen",
    "r2_local_root_explicit_allow_purge_plan_preflight_built",
    "r3_actual_review_session_envelope_created",
    "r4_24_case_manifest_freeze_built",
    "r5_local_only_body_full_packet_generation_request_built",
    "r6_body_full_packet_completeness_export_denylist_scan_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_actual_human_review_run_recorded",
    "r9_rating_row_normalizer_built",
    "r10_readfeel_blocker_execution_blocker_ingestion_built",
    "r11_question_need_observation_row_normalizer_built",
    "r12_rating_question_observation_consistency_guard_built",
    "r13_pause_abort_expiration_protocol_built",
    "r14_body_full_packet_reviewer_notes_purge_built",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r51_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R51_R0_R1_FALSE_KEY_REFS,
)
P7_R51_DISPOSAL_RECEIPT_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "packet_kind",
    "case_count",
    "deleted_file_count",
    "purge_started_at_ref",
    "purge_completed_at_ref",
    "disposal_status",
    "body_removed",
    "reviewer_forms_removed",
    "reviewer_notes_removed",
    "local_packet_exported",
    "content_hash_of_body_stored",
    "local_absolute_path_included",
    "body_content_hash_included",
    "deleted_body_preview_included",
    "terminal_output_included",
    "receipt_contains_body_full_material",
    "release_allowed",
    "p7_complete",
    "p8_start_allowed",
    "hold004_close_allowed",
    "body_free",
)
P7_R51_DISPOSAL_RECEIPT_BUILDER_VERIFIER_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "review_session_status",
    "r14_purge_schema_version",
    "r14_purge_ref",
    "purge_status",
    "disposal_receipt_verifier_status",
    "disposal_receipt_reason_refs",
    "required_case_count",
    "packet_kind",
    "disposal_receipt_schema_version",
    "disposal_receipt_required_field_refs",
    "disposal_receipt",
    "disposal_status",
    "body_removed",
    "reviewer_forms_removed",
    "reviewer_notes_removed",
    "local_packet_exported",
    "content_hash_of_body_stored",
    "receipt_contains_body_full_material",
    "local_absolute_path_included",
    "body_content_hash_included",
    "deleted_body_preview_included",
    "terminal_output_included",
    "deleted_file_count",
    "purge_started_at_ref",
    "purge_completed_at_ref",
    "disposal_verified",
    "disposal_failed",
    "disposal_receipt_missing",
    "summary_finalize_allowed",
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
    "r0_current_source_r50_handoff_refrozen",
    "r1_validation_evidence_r49_timeout_handling_frozen",
    "r2_local_root_explicit_allow_purge_plan_preflight_built",
    "r3_actual_review_session_envelope_created",
    "r4_24_case_manifest_freeze_built",
    "r5_local_only_body_full_packet_generation_request_built",
    "r6_body_full_packet_completeness_export_denylist_scan_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_actual_human_review_run_recorded",
    "r9_rating_row_normalizer_built",
    "r10_readfeel_blocker_execution_blocker_ingestion_built",
    "r11_question_need_observation_row_normalizer_built",
    "r12_rating_question_observation_consistency_guard_built",
    "r13_pause_abort_expiration_protocol_built",
    "r14_body_full_packet_reviewer_notes_purge_built",
    "r15_disposal_receipt_builder_verifier_built",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r51_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R51_R0_R1_FALSE_KEY_REFS,
)


def _r51_identity_index(rows: Sequence[Mapping[str, Any]]) -> dict[tuple[Any, Any, Any, Any, Any], Mapping[str, Any]]:
    return {_r51_case_identity(safe_mapping(row)): safe_mapping(row) for row in rows}


def _is_r51_question_candidate_observation(row: Mapping[str, Any]) -> bool:
    primary = clean_identifier(row.get("question_need_primary_class"), default="", max_length=160)
    plan_flags = set(dedupe_identifiers(row.get("plan_candidate_flags") or [], limit=10, max_length=160))
    return primary in {
        "question_may_reduce_overread_risk",
        "question_would_make_immediate_observation_heavy",
        "plus_single_question_candidate_later",
        "premium_deep_dive_candidate_later",
    } or bool(plan_flags & {"plus_single_question_candidate_later", "premium_deep_dive_candidate_later", "p8_design_material_candidate"})


def _r51_question_escape_blocker_refs() -> frozenset[str]:
    return frozenset(
        {
            "p5_history_creepy_or_surveillance_feeling",
            "p5_history_scope_overclaim",
            "p5_history_line_self_blame_amplification",
            "p5_free_tier_history_boundary_violation",
            "p5_low_information_history_overread",
            "p5_current_input_overridden_by_history",
            "p5_boundary_history_line_leak_suspected",
        }
    )


def build_p7_r51_rating_question_observation_consistency_issue_row_bodyfree(
    *,
    rating_row: Mapping[str, Any] | None = None,
    question_observation_row: Mapping[str, Any] | None = None,
    consistency_issue_id: Any,
    consistency_issue_kind: Any,
    sanitized_reason_ids: Sequence[Any] | None = None,
) -> dict[str, Any]:
    rating = safe_mapping(rating_row)
    question = safe_mapping(question_observation_row)
    source = rating or question
    issue_id = clean_identifier(consistency_issue_id, default="r51_rating_question_case_set_mismatch", max_length=160)
    issue_kind = clean_identifier(consistency_issue_kind, default="CASE_SET", max_length=120)
    blockers = _allowed_identifier_sequence_r51(
        rating.get("blocker_ids") or [],
        source="p7_r51_r12_consistency_issue.blocker_ids",
        allowed_refs=P7_R48_READFEEL_BLOCKER_ID_REFS,
        limit=20,
    )
    plan_flags = _allowed_identifier_sequence_r51(
        question.get("plan_candidate_flags") or [],
        source="p7_r51_r12_consistency_issue.plan_candidate_flags",
        allowed_refs=P7_R50_PLAN_CANDIDATE_FLAG_REFS,
        limit=10,
    )
    repair_refs = _allowed_identifier_sequence_r51(
        question.get("repair_required_refs") or [],
        source="p7_r51_r12_consistency_issue.repair_required_refs",
        allowed_refs=P7_R50_REPAIR_REQUIRED_REF_REFS,
        limit=10,
    )
    reason_ids = dedupe_identifiers([*(sanitized_reason_ids or []), issue_id], limit=20, max_length=160)
    row = {
        "schema_version": P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_ROW_BODYFREE_SCHEMA_VERSION,
        "review_session_id": clean_identifier(source.get("review_session_id"), default=P7_R51_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "packet_ref_id": clean_identifier(source.get("packet_ref_id"), default="r51_consistency_case_set", max_length=160),
        "blind_case_id": clean_identifier(source.get("blind_case_id"), default="r51_consistency_case_set", max_length=160),
        "case_ref_id": clean_identifier(source.get("case_ref_id"), default="r51_consistency_case_set", max_length=160),
        "family": clean_identifier(source.get("family"), default="history_line_eligible_input", max_length=160),
        "case_role": clean_identifier(source.get("case_role"), default="positive_history_line", max_length=160),
        "review_kind": P7_R51_REVIEW_KIND,
        "consistency_issue_id": issue_id,
        "consistency_issue_kind": issue_kind,
        "consistency_issue_status": "OPEN",
        "rating_verdict_ref": clean_identifier(rating.get("verdict"), default="UNAVAILABLE", max_length=80),
        "question_need_primary_class": clean_identifier(question.get("question_need_primary_class"), default="UNAVAILABLE", max_length=160),
        "blocker_ids": blockers,
        "plan_candidate_flags": plan_flags,
        "repair_required_refs": repair_refs,
        "sanitized_reason_ids": reason_ids,
        "p5_repair_return_required": True,
        "p8_question_candidate_blocked": True,
        "body_free": True,
    }
    assert_p7_r51_rating_question_observation_consistency_issue_row_bodyfree_contract(row)
    return row


def assert_p7_r51_rating_question_observation_consistency_issue_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(
        data,
        required=P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_ROW_BODYFREE_REQUIRED_FIELD_REFS,
        source="p7_r51_r12_consistency_issue_row",
    )
    if data.get("schema_version") != P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R51 R12 consistency issue row schema changed")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r51_r12_consistency_issue_row")
    if data.get("body_free") is not True:
        raise ValueError("R51 R12 consistency issue row must be body-free")
    if data.get("family") not in _r51_family_refs():
        raise ValueError("R51 R12 consistency issue row family changed")
    if data.get("case_role") not in P7_R48_P5_CASE_ROLE_REFS:
        raise ValueError("R51 R12 consistency issue row case role changed")
    if data.get("review_kind") != P7_R51_REVIEW_KIND:
        raise ValueError("R51 R12 consistency issue row review kind changed")
    if data.get("consistency_issue_id") not in P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_ID_REFS:
        raise ValueError("R51 R12 consistency issue id changed")
    if data.get("consistency_issue_kind") not in P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_KIND_REFS:
        raise ValueError("R51 R12 consistency issue kind changed")
    if data.get("consistency_issue_status") != "OPEN":
        raise ValueError("R51 R12 consistency issue status must remain OPEN")
    _allowed_identifier_sequence_r51(data.get("blocker_ids"), source="p7_r51_r12_consistency_issue.blocker_ids", allowed_refs=P7_R48_READFEEL_BLOCKER_ID_REFS, limit=20)
    _allowed_identifier_sequence_r51(data.get("plan_candidate_flags"), source="p7_r51_r12_consistency_issue.plan_candidate_flags", allowed_refs=P7_R50_PLAN_CANDIDATE_FLAG_REFS, limit=10)
    _allowed_identifier_sequence_r51(data.get("repair_required_refs"), source="p7_r51_r12_consistency_issue.repair_required_refs", allowed_refs=P7_R50_REPAIR_REQUIRED_REF_REFS, limit=10)
    _allowed_identifier_sequence_r51(data.get("sanitized_reason_ids"), source="p7_r51_r12_consistency_issue.sanitized_reason_ids", allowed_refs=None, limit=20)
    for key in ("p5_repair_return_required", "p8_question_candidate_blocked"):
        if data.get(key) is not True:
            raise ValueError(f"R51 R12 consistency issue row must keep {key}=True")
    return True


def _r51_matching_execution_blocker_exists(
    question_row: Mapping[str, Any],
    execution_blocker_rows: Sequence[Mapping[str, Any]],
) -> bool:
    case_ref = safe_mapping(question_row).get("case_ref_id")
    for raw in execution_blocker_rows:
        row = safe_mapping(raw)
        if row.get("case_ref_id") == case_ref or row.get("blind_case_id") == question_row.get("blind_case_id"):
            return True
    return False


def _r51_consistency_issue_rows_for_pair(
    rating_row: Mapping[str, Any],
    question_row: Mapping[str, Any],
    *,
    execution_blocker_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rating = safe_mapping(rating_row)
    question = safe_mapping(question_row)
    assert_p7_r51_rating_row_bodyfree_contract(rating)
    assert_p7_r51_question_need_observation_row_bodyfree_contract(question)
    issues: list[dict[str, Any]] = []
    verdict = clean_identifier(rating.get("verdict"), default="", max_length=80)
    primary = clean_identifier(question.get("question_need_primary_class"), default="", max_length=160)
    one_fit = clean_identifier(question.get("one_question_fit_ref"), default="", max_length=160)
    repair_refs = set(dedupe_identifiers(question.get("repair_required_refs") or [], limit=10, max_length=160))
    blocker_ids = set(dedupe_identifiers(rating.get("blocker_ids") or [], limit=20, max_length=160))
    is_candidate = _is_r51_question_candidate_observation(question)

    if verdict == "PASS" and primary.startswith("not_question_"):
        issues.append(
            build_p7_r51_rating_question_observation_consistency_issue_row_bodyfree(
                rating_row=rating,
                question_observation_row=question,
                consistency_issue_id="r51_pass_rating_with_not_question_repair",
                consistency_issue_kind="RATING_VERDICT",
            )
        )
    if verdict in {"RED", "REPAIR_REQUIRED"} and is_candidate:
        issues.append(
            build_p7_r51_rating_question_observation_consistency_issue_row_bodyfree(
                rating_row=rating,
                question_observation_row=question,
                consistency_issue_id="r51_red_or_repair_required_routed_to_question_candidate",
                consistency_issue_kind="RATING_VERDICT",
            )
        )
    if one_fit == "repair_required_not_question" and repair_refs == {"no_repair_required"}:
        issues.append(
            build_p7_r51_rating_question_observation_consistency_issue_row_bodyfree(
                rating_row=rating,
                question_observation_row=question,
                consistency_issue_id="r51_repair_required_not_question_without_repair_ref",
                consistency_issue_kind="REPAIR_REF",
            )
        )
    escape_blockers = blocker_ids & _r51_question_escape_blocker_refs()
    if is_candidate and escape_blockers:
        issue_id = (
            "r51_current_input_overridden_by_history_routed_to_question_candidate"
            if "p5_current_input_overridden_by_history" in escape_blockers
            else "r51_creepy_or_boundary_blocker_routed_to_question_candidate"
        )
        issues.append(
            build_p7_r51_rating_question_observation_consistency_issue_row_bodyfree(
                rating_row=rating,
                question_observation_row=question,
                consistency_issue_id=issue_id,
                consistency_issue_kind="BLOCKER_ESCAPE",
                sanitized_reason_ids=sorted(escape_blockers),
            )
        )
    if primary == "insufficient_material_execution_blocker" and not _r51_matching_execution_blocker_exists(question, execution_blocker_rows):
        issues.append(
            build_p7_r51_rating_question_observation_consistency_issue_row_bodyfree(
                rating_row=rating,
                question_observation_row=question,
                consistency_issue_id="r51_insufficient_material_observation_without_execution_blocker",
                consistency_issue_kind="EXECUTION_BLOCKER_MATCH",
            )
        )
    return issues


def build_p7_r51_rating_question_observation_consistency_guard_bodyfree(
    *,
    rating_row_normalizer_bodyfree: Mapping[str, Any] | None = None,
    r9_rating_row_normalizer_bodyfree: Mapping[str, Any] | None = None,
    readfeel_blocker_execution_blocker_ingestion_bodyfree: Mapping[str, Any] | None = None,
    r10_readfeel_blocker_execution_blocker_ingestion_bodyfree: Mapping[str, Any] | None = None,
    question_need_observation_row_normalizer_bodyfree: Mapping[str, Any] | None = None,
    r11_question_need_observation_row_normalizer_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r51_rating_question_observation_consistency_guard_bodyfree",
) -> dict[str, Any]:
    """Build R51-12 body-free guard against using question candidates as a P5 repair escape."""

    if rating_row_normalizer_bodyfree is not None and r9_rating_row_normalizer_bodyfree is not None:
        raise ValueError("provide only one R51-9 rating normalizer value")
    if readfeel_blocker_execution_blocker_ingestion_bodyfree is not None and r10_readfeel_blocker_execution_blocker_ingestion_bodyfree is not None:
        raise ValueError("provide only one R51-10 blocker ingestion value")
    if question_need_observation_row_normalizer_bodyfree is not None and r11_question_need_observation_row_normalizer_bodyfree is not None:
        raise ValueError("provide only one R51-11 question normalizer value")

    r9 = (
        safe_mapping(rating_row_normalizer_bodyfree)
        if rating_row_normalizer_bodyfree is not None
        else safe_mapping(r9_rating_row_normalizer_bodyfree)
        if r9_rating_row_normalizer_bodyfree is not None
        else build_p7_r51_rating_row_normalizer_bodyfree()
    )
    assert_p7_r51_rating_row_normalizer_bodyfree_contract(r9)
    r10 = (
        safe_mapping(readfeel_blocker_execution_blocker_ingestion_bodyfree)
        if readfeel_blocker_execution_blocker_ingestion_bodyfree is not None
        else safe_mapping(r10_readfeel_blocker_execution_blocker_ingestion_bodyfree)
        if r10_readfeel_blocker_execution_blocker_ingestion_bodyfree is not None
        else build_p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree(rating_row_normalizer_bodyfree=r9)
    )
    assert_p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(r10)
    r11 = (
        safe_mapping(question_need_observation_row_normalizer_bodyfree)
        if question_need_observation_row_normalizer_bodyfree is not None
        else safe_mapping(r11_question_need_observation_row_normalizer_bodyfree)
        if r11_question_need_observation_row_normalizer_bodyfree is not None
        else build_p7_r51_question_need_observation_row_normalizer_bodyfree(readfeel_blocker_execution_blocker_ingestion_bodyfree=r10)
    )
    assert_p7_r51_question_need_observation_row_normalizer_bodyfree_contract(r11)

    r9_ready = r9.get("rating_row_normalizer_status") == "READY_FOR_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION" and not r9.get("execution_blocker_ids")
    r10_ready = r10.get("blocker_ingestion_status") == "READY_FOR_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION" and not r10.get("execution_blocker_ids")
    r11_ready = r11.get("question_observation_normalizer_status") == "READY_FOR_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD" and not r11.get("execution_blocker_ids")

    rating_rows = [safe_mapping(row) for row in r9.get("rating_rows") or []]
    question_rows = [safe_mapping(row) for row in r11.get("question_need_observation_rows") or []]
    readfeel_rows = [safe_mapping(row) for row in r10.get("readfeel_blocker_rows") or []]
    execution_rows = [safe_mapping(row) for row in r10.get("execution_blocker_rows") or []]
    rating_index = _r51_identity_index(rating_rows)
    question_index = _r51_identity_index(question_rows)
    rating_keys = set(rating_index)
    question_keys = set(question_index)
    case_sets_match = rating_keys == question_keys

    issues: list[dict[str, Any]] = []
    for key in sorted(rating_keys | question_keys, key=lambda item: str(item)):
        rating = safe_mapping(rating_index.get(key) or {})
        question = safe_mapping(question_index.get(key) or {})
        if not rating or not question:
            issues.append(
                build_p7_r51_rating_question_observation_consistency_issue_row_bodyfree(
                    rating_row=rating,
                    question_observation_row=question,
                    consistency_issue_id=(
                        "r51_missing_rating_row_for_question_observation" if question and not rating else "r51_missing_question_observation_row_for_rating"
                    ),
                    consistency_issue_kind="CASE_SET",
                )
            )
            continue
        issues.extend(_r51_consistency_issue_rows_for_pair(rating, question, execution_blocker_rows=execution_rows))

    blockers = dedupe_identifiers([*(r9.get("execution_blocker_ids") or []), *(r10.get("execution_blocker_ids") or []), *(r11.get("execution_blocker_ids") or [])], limit=50, max_length=140)
    if not r9_ready:
        status = "BLOCKED_BY_R51_9_RATING_ROW_NORMALIZER"
        blockers = dedupe_identifiers([*blockers, "r51_rating_rows_incomplete"], limit=50, max_length=140)
    elif not r10_ready:
        status = "BLOCKED_BY_R51_10_BLOCKER_INGESTION"
        blockers = dedupe_identifiers([*blockers, "r51_rating_rows_incomplete"], limit=50, max_length=140)
    elif not r11_ready:
        status = "BLOCKED_BY_R51_11_QUESTION_OBSERVATION_NORMALIZER"
        blockers = dedupe_identifiers([*blockers, "r51_question_need_observation_rows_incomplete"], limit=50, max_length=140)
    elif issues:
        status = "BLOCKED_BY_RATING_QUESTION_OBSERVATION_INCONSISTENCY"
        blockers = dedupe_identifiers([*blockers, "r51_rating_question_observation_inconsistent"], limit=50, max_length=140)
    else:
        status = "READY_FOR_PAUSE_ABORT_EXPIRATION_PROTOCOL"

    ready = status == "READY_FOR_PAUSE_ABORT_EXPIRATION_PROTOCOL"
    issue_ids = _r51_count_identifier_values(issues, "consistency_issue_id")
    issue_kinds = _r51_count_identifier_values(issues, "consistency_issue_kind")
    candidate_count = sum(1 for row in question_rows if _is_r51_question_candidate_observation(row))
    repair_required = bool(readfeel_rows) or any(safe_mapping(row).get("verdict") in {"RED", "REPAIR_REQUIRED"} for row in rating_rows) or any(
        str(safe_mapping(row).get("question_need_primary_class", "")).startswith("not_question_") for row in question_rows
    )
    actual_true_keys = (
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
    ) if r9_ready and r10_ready and r11_ready else ()
    guard = {
        **_false_flags(),
        "schema_version": P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R51_STEP,
        "scope": P7_R51_SCOPE,
        "policy_kind": P7_R51_POLICY_KIND,
        "policy_section": "R51-12_rating_question_observation_consistency_guard",
        "current_phase": "P7_Product_Quality_Runner",
        "material_id": clean_identifier(material_id, default="p7_r51_rating_question_observation_consistency_guard_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r11.get("review_session_id") or r9.get("review_session_id"), default=P7_R51_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_session_status": "R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_READY" if ready else "R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_BLOCKED",
        "r9_rating_row_normalizer_schema_version": P7_R51_RATING_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION,
        "r9_rating_row_normalizer_ref": clean_identifier(r9.get("material_id"), default="p7_r51_rating_row_normalizer_bodyfree", max_length=180),
        "rating_row_normalizer_status": clean_identifier(r9.get("rating_row_normalizer_status"), default="BLOCKED_BY_RATING_ROW_VALIDATION", max_length=120),
        "r10_blocker_ingestion_schema_version": P7_R51_READFEEL_EXECUTION_BLOCKER_INGESTION_BODYFREE_SCHEMA_VERSION,
        "r10_blocker_ingestion_ref": clean_identifier(r10.get("material_id"), default="p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree", max_length=180),
        "blocker_ingestion_status": clean_identifier(r10.get("blocker_ingestion_status"), default="BLOCKED_BY_R51_9_RATING_ROW_NORMALIZER", max_length=120),
        "r11_question_observation_normalizer_schema_version": P7_R51_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION,
        "r11_question_observation_normalizer_ref": clean_identifier(r11.get("material_id"), default="p7_r51_question_need_observation_row_normalizer_bodyfree", max_length=180),
        "question_observation_normalizer_status": clean_identifier(r11.get("question_observation_normalizer_status"), default="BLOCKED_BY_QUESTION_OBSERVATION_ROW_VALIDATION", max_length=120),
        "rating_question_consistency_guard_status": status,
        "consistency_guard_reason_refs": ["rating_question_observation_consistency_guard_passed"] if ready else dedupe_identifiers([*blockers, *issue_ids.keys()], limit=60, max_length=160),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "rating_row_count": len(rating_rows),
        "question_observation_row_count": len(question_rows),
        "readfeel_blocker_row_count": len(readfeel_rows),
        "execution_blocker_row_count": len(execution_rows),
        "open_readfeel_blocker_count": _safe_non_negative_int(r10.get("open_readfeel_blocker_count")),
        "open_execution_blocker_count": _safe_non_negative_int(r10.get("open_execution_blocker_count")),
        "rating_question_case_ref_sets_match": case_sets_match,
        "all_required_rows_present": len(rating_rows) == P7_R51_REQUIRED_CASE_COUNT and len(question_rows) == P7_R51_REQUIRED_CASE_COUNT,
        "consistency_issue_row_schema_version": P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_ROW_BODYFREE_SCHEMA_VERSION,
        "consistency_issue_row_required_field_refs": list(P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_ROW_BODYFREE_REQUIRED_FIELD_REFS),
        "consistency_issue_id_refs": list(P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_ID_REFS),
        "consistency_issue_kind_refs": list(P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_KIND_REFS),
        "consistency_issue_rows": issues,
        "consistency_issue_count": len(issues),
        "consistency_issue_id_counts": issue_ids,
        "consistency_issue_kind_counts": issue_kinds,
        "no_red_or_repair_routed_to_p8_question_candidate": "r51_red_or_repair_required_routed_to_question_candidate" not in issue_ids,
        "no_creepy_or_boundary_blocker_routed_to_p8_question_candidate": not ({"r51_creepy_or_boundary_blocker_routed_to_question_candidate", "r51_current_input_overridden_by_history_routed_to_question_candidate"} & set(issue_ids)),
        "no_pass_rating_with_not_question_repair": "r51_pass_rating_with_not_question_repair" not in issue_ids,
        "no_repair_required_not_question_without_repair_ref": "r51_repair_required_not_question_without_repair_ref" not in issue_ids,
        "insufficient_material_observations_have_execution_blocker": "r51_insufficient_material_observation_without_execution_blocker" not in issue_ids,
        "p5_weakness_not_hidden_by_question_candidate": ready,
        "p5_repair_return_required_by_consistency": bool(repair_required and not issues),
        "p8_question_material_candidate_allowed_by_consistency": bool(ready and candidate_count and not repair_required),
        "question_candidate_allowed_case_count": candidate_count if ready and not repair_required else 0,
        "p8_question_material_candidate_case_count": candidate_count if ready else 0,
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
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "actual_human_review_run_here": bool(r9_ready and r10_ready and r11_ready and r11.get("actual_human_review_run_here") is True),
        "actual_manual_review_run_here": bool(r9_ready and r10_ready and r11_ready and r11.get("actual_manual_review_run_here") is True),
        "actual_rating_rows_materialized_here": bool(r9_ready and r10_ready and r11_ready and r11.get("actual_rating_rows_materialized_here") is True),
        "actual_blocker_rows_materialized_here": bool(r9_ready and r10_ready and r11_ready and r11.get("actual_blocker_rows_materialized_here") is True),
        "actual_execution_blocker_rows_materialized_here": bool(r9_ready and r10_ready and r11_ready and r11.get("actual_execution_blocker_rows_materialized_here") is True),
        "actual_question_need_observation_rows_materialized_here": bool(r9_ready and r10_ready and r11_ready and r11.get("actual_question_need_observation_rows_materialized_here") is True),
        "actual_question_need_observation_summary_materialized_here": False,
        "p5_actual_review_still_not_run": not (r9_ready and r10_ready and r11_ready),
        "p5_human_blind_qa_confirmed_candidate": False,
        "p5_repair_return_candidate": False,
        "p5_review_inconclusive": False,
        "p6_limited_human_readfeel_start_allowed_candidate": False,
        "p8_question_design_material_candidate": False,
        "r0_current_source_r50_handoff_refrozen": True,
        "r1_validation_evidence_r49_timeout_handling_frozen": True,
        "r2_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r3_actual_review_session_envelope_created": True,
        "r4_24_case_manifest_freeze_built": True,
        "r5_local_only_body_full_packet_generation_request_built": True,
        "r6_body_full_packet_completeness_export_denylist_scan_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": bool(r11.get("r7_reviewer_instruction_rating_form_freeze_built")),
        "r8_actual_human_review_run_recorded": bool(r11.get("r8_actual_human_review_run_recorded")),
        "r9_rating_row_normalizer_built": bool(r11.get("r9_rating_row_normalizer_built")),
        "r10_readfeel_blocker_execution_blocker_ingestion_built": bool(r11.get("r10_readfeel_blocker_execution_blocker_ingestion_built")),
        "r11_question_need_observation_row_normalizer_built": bool(r11.get("r11_question_need_observation_row_normalizer_built")),
        "r12_rating_question_observation_consistency_guard_built": ready,
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        "implemented_steps": list(P7_R51_R12_IMPLEMENTED_STEPS if ready else P7_R51_R11_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R51_R12_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R51_R11_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R51_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R51_R12_NEXT_REQUIRED_STEP_REF if ready else P7_R51_R12_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r51_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r51_rating_question_observation_consistency_guard_bodyfree_contract(guard, allowed_true_false_key_refs=actual_true_keys)
    return guard


def build_p7_r51_rating_question_observation_consistency_guard(**kwargs: Any) -> dict[str, Any]:
    return build_p7_r51_rating_question_observation_consistency_guard_bodyfree(**kwargs)


def assert_p7_r51_rating_question_observation_consistency_guard_bodyfree_contract(
    guard: Mapping[str, Any],
    *,
    allowed_true_false_key_refs: Sequence[str] | None = None,
) -> bool:
    data = safe_mapping(guard)
    _assert_required_fields(data, required=P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_BODYFREE_REQUIRED_FIELD_REFS, source="p7_r51_r12_rating_question_observation_consistency_guard")
    allowed = tuple(
        allowed_true_false_key_refs
        or (
            "actual_human_review_run_here",
            "actual_manual_review_run_here",
            "actual_rating_rows_materialized_here",
            "actual_blocker_rows_materialized_here",
            "actual_execution_blocker_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
        )
    )
    _assert_body_free_common_allowing(
        data,
        schema_version=P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        source="p7_r51_r12_rating_question_observation_consistency_guard",
        allowed_true_false_key_refs=allowed,
    )
    if data.get("policy_section") != "R51-12_rating_question_observation_consistency_guard":
        raise ValueError("R51 R12 policy section changed")
    if data.get("rating_question_consistency_guard_status") not in P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_STATUS_REFS:
        raise ValueError("R51 R12 consistency guard status changed")
    if data.get("consistency_issue_row_schema_version") != P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R51 R12 consistency issue schema changed")
    if tuple(data.get("consistency_issue_row_required_field_refs") or ()) != P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_ROW_BODYFREE_REQUIRED_FIELD_REFS:
        raise ValueError("R51 R12 consistency issue row fields changed")
    if tuple(data.get("consistency_issue_id_refs") or ()) != P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_ID_REFS:
        raise ValueError("R51 R12 consistency issue ids changed")
    if tuple(data.get("consistency_issue_kind_refs") or ()) != P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_KIND_REFS:
        raise ValueError("R51 R12 consistency issue kinds changed")
    for row in data.get("consistency_issue_rows") or []:
        assert_p7_r51_rating_question_observation_consistency_issue_row_bodyfree_contract(safe_mapping(row))
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
            raise ValueError(f"R51 R12 must keep {false_key}=False")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=50, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R51 R12 open blockers must match execution blockers")
    unknown = sorted(set(blockers) - set(P7_R51_EXECUTION_BLOCKER_ID_REFS))
    if unknown:
        raise ValueError(f"R51 R12 execution blockers are not canonical: {unknown[:4]}")
    ready = data.get("rating_question_consistency_guard_status") == "READY_FOR_PAUSE_ABORT_EXPIRATION_PROTOCOL"
    if ready:
        if data.get("consistency_issue_count") != 0:
            raise ValueError("R51 R12 ready guard must not carry consistency issues")
        if data.get("rating_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R51 R12 ready guard must carry 24 rating rows")
        if data.get("question_observation_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R51 R12 ready guard must carry 24 question rows")
        for true_key in (
            "rating_question_case_ref_sets_match",
            "all_required_rows_present",
            "no_red_or_repair_routed_to_p8_question_candidate",
            "no_creepy_or_boundary_blocker_routed_to_p8_question_candidate",
            "no_pass_rating_with_not_question_repair",
            "no_repair_required_not_question_without_repair_ref",
            "insufficient_material_observations_have_execution_blocker",
            "p5_weakness_not_hidden_by_question_candidate",
            "actual_human_review_run_here",
            "actual_manual_review_run_here",
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "r12_rating_question_observation_consistency_guard_built",
        ):
            if data.get(true_key) is not True:
                raise ValueError(f"R51 R12 ready guard must keep {true_key}=True")
        if blockers:
            raise ValueError("R51 R12 ready guard must not carry execution blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R51_R12_IMPLEMENTED_STEPS:
            raise ValueError("R51 R12 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R51_R12_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R51 R12 not-yet steps changed")
        if data.get("next_required_step") != P7_R51_R12_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R12 ready guard must point to R51-13")
    else:
        if data.get("r12_rating_question_observation_consistency_guard_built") is not False:
            raise ValueError("R51 R12 blocked guard must not claim built")
        if data.get("p5_weakness_not_hidden_by_question_candidate") is not False:
            raise ValueError("R51 R12 blocked guard must not claim P5 weakness is not hidden")
        if data.get("next_required_step") != P7_R51_R12_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R12 blocked guard must point to consistency resolution")
    return True


def _safe_non_negative_float_r51(value: Any) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return 0.0
    return parsed if parsed >= 0 else 0.0


def build_p7_r51_pause_abort_expiration_protocol_bodyfree(
    *,
    rating_question_observation_consistency_guard_bodyfree: Mapping[str, Any] | None = None,
    r12_rating_question_observation_consistency_guard_bodyfree: Mapping[str, Any] | None = None,
    review_lifecycle_status: Any = "REVIEW_COMPLETED",
    body_full_packet_age_hours: Any = 0,
    reviewer_notes_age_hours: Any = 0,
    rating_rows_finalized: Any | None = None,
    question_observation_rows_finalized: Any | None = None,
    material_id: Any = "p7_r51_pause_abort_expiration_protocol_bodyfree",
) -> dict[str, Any]:
    """Build R51-13 body-free pause / abort / expiration protocol evidence."""

    if rating_question_observation_consistency_guard_bodyfree is not None and r12_rating_question_observation_consistency_guard_bodyfree is not None:
        raise ValueError("provide only one R51-12 consistency guard value")
    r12 = (
        safe_mapping(rating_question_observation_consistency_guard_bodyfree)
        if rating_question_observation_consistency_guard_bodyfree is not None
        else safe_mapping(r12_rating_question_observation_consistency_guard_bodyfree)
        if r12_rating_question_observation_consistency_guard_bodyfree is not None
        else build_p7_r51_rating_question_observation_consistency_guard_bodyfree()
    )
    assert_p7_r51_rating_question_observation_consistency_guard_bodyfree_contract(r12)
    r12_ready = r12.get("rating_question_consistency_guard_status") == "READY_FOR_PAUSE_ABORT_EXPIRATION_PROTOCOL" and not r12.get("execution_blocker_ids")
    lifecycle = clean_identifier(review_lifecycle_status, default="REVIEW_COMPLETED", max_length=120)
    if lifecycle not in P7_R51_REVIEW_LIFECYCLE_STATUS_REFS:
        raise ValueError("R51 R13 lifecycle status must be canonical")
    packet_age = _safe_non_negative_float_r51(body_full_packet_age_hours)
    notes_age = _safe_non_negative_float_r51(reviewer_notes_age_hours)
    packet_expired = packet_age >= float(P7_R47_BODY_FULL_PACKET_RETENTION_HOURS) or lifecycle == "REVIEW_EXPIRED"
    notes_expired = notes_age >= float(P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS)
    rating_finalized = _safe_bool(rating_rows_finalized, default=bool(r12_ready and r12.get("actual_rating_rows_materialized_here") is True))
    question_finalized = _safe_bool(question_observation_rows_finalized, default=bool(r12_ready and r12.get("actual_question_need_observation_rows_materialized_here") is True))

    if not r12_ready:
        protocol_status = "BLOCKED_BY_R51_12_CONSISTENCY_GUARD"
        reason_refs = dedupe_identifiers([*(r12.get("execution_blocker_ids") or []), "r51_rating_question_observation_inconsistent"], limit=50, max_length=160)
    elif lifecycle == "REVIEW_PAUSED" and not packet_expired:
        protocol_status = "PAUSED_RETENTION_CLOCK_STILL_RUNNING"
        reason_refs = ["review_paused_retention_clock_still_running"]
    elif lifecycle == "REVIEW_ABORTED":
        protocol_status = "ABORTED_PURGE_REQUIRED"
        reason_refs = ["review_aborted_purge_required"]
    elif packet_expired:
        protocol_status = "EXPIRED_PURGE_REQUIRED"
        reason_refs = ["review_expired_purge_required"]
    else:
        protocol_status = "READY_FOR_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE"
        reason_refs = ["review_completed_purge_required_before_summary"]
    purge_required = protocol_status in {"READY_FOR_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE", "ABORTED_PURGE_REQUIRED", "EXPIRED_PURGE_REQUIRED"}
    protocol_built = r12_ready
    if protocol_status == "PAUSED_RETENTION_CLOCK_STILL_RUNNING":
        next_step = P7_R51_R13_PAUSED_NEXT_REQUIRED_STEP_REF
    elif purge_required:
        next_step = P7_R51_R13_NEXT_REQUIRED_STEP_REF
    else:
        next_step = P7_R51_R13_BLOCKED_NEXT_REQUIRED_STEP_REF
    implemented_steps = P7_R51_R13_IMPLEMENTED_STEPS if protocol_built else P7_R51_R12_IMPLEMENTED_STEPS
    not_yet_steps = P7_R51_R13_NOT_YET_IMPLEMENTED_STEPS if protocol_built else P7_R51_R12_NOT_YET_IMPLEMENTED_STEPS
    blockers = [] if r12_ready else dedupe_identifiers([*(r12.get("execution_blocker_ids") or []), "r51_rating_question_observation_inconsistent"], limit=50, max_length=140)
    actual_true_keys = (
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
    ) if r12_ready else ()
    protocol = {
        **_false_flags(),
        "schema_version": P7_R51_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R51_STEP,
        "scope": P7_R51_SCOPE,
        "policy_kind": P7_R51_POLICY_KIND,
        "policy_section": "R51-13_pause_abort_expiration_protocol",
        "current_phase": "P7_Product_Quality_Runner",
        "material_id": clean_identifier(material_id, default="p7_r51_pause_abort_expiration_protocol_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r12.get("review_session_id"), default=P7_R51_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_session_status": "R51_PAUSE_ABORT_EXPIRATION_PROTOCOL_READY" if protocol_built else "R51_PAUSE_ABORT_EXPIRATION_PROTOCOL_BLOCKED",
        "r12_consistency_guard_schema_version": P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        "r12_consistency_guard_ref": clean_identifier(r12.get("material_id"), default="p7_r51_rating_question_observation_consistency_guard_bodyfree", max_length=180),
        "rating_question_consistency_guard_status": clean_identifier(r12.get("rating_question_consistency_guard_status"), default="BLOCKED_BY_RATING_QUESTION_OBSERVATION_INCONSISTENCY", max_length=120),
        "pause_abort_expiration_protocol_status": protocol_status,
        "pause_abort_expiration_reason_refs": reason_refs,
        "review_lifecycle_status": lifecycle,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "rating_row_count": _safe_non_negative_int(r12.get("rating_row_count")),
        "question_observation_row_count": _safe_non_negative_int(r12.get("question_observation_row_count")),
        "retention_clock_stops_on_pause": False,
        "review_pause_does_not_stop_retention_deadline": True,
        "review_abort_requires_purge": True,
        "expired_requires_purge_even_when_rating_incomplete": True,
        "body_removed_priority_over_rating_completion_when_expired": bool(packet_expired),
        "body_full_packet_retention_max_hours": P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
        "reviewer_notes_retention_after_rating_finalized_max_hours": P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
        "body_full_packet_age_hours": packet_age,
        "reviewer_notes_age_hours": notes_age,
        "body_full_packet_retention_expired": bool(packet_expired),
        "reviewer_notes_retention_expired": bool(notes_expired),
        "rating_rows_finalized": rating_finalized,
        "question_observation_rows_finalized": question_finalized,
        "body_full_packet_purge_required": bool(purge_required),
        "reviewer_forms_purge_required": bool(purge_required),
        "reviewer_notes_purge_required": bool(purge_required or notes_expired or rating_finalized),
        "purge_required_before_summary": bool(purge_required),
        "body_removed": False,
        "reviewer_notes_removed": False,
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "aborted_or_expired_blocks_p5_confirmed_candidate": lifecycle in {"REVIEW_ABORTED", "REVIEW_EXPIRED"} or packet_expired,
        "p5_confirmed_candidate_allowed_after_protocol": False,
        "p5_repair_return_candidate_allowed_after_protocol": False,
        "p5_review_inconclusive_candidate_after_protocol": lifecycle in {"REVIEW_ABORTED", "REVIEW_EXPIRED"} or packet_expired or not r12_ready,
        "disposal_receipt_materialized_here": False,
        "actual_disposal_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "post_review_summary_materialized_here": False,
        "p8_question_implementation_spec_finalized_here": False,
        "question_trigger_logic_implemented_here": False,
        "api_db_rn_response_key_changed_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "actual_human_review_run_here": bool(r12_ready and r12.get("actual_human_review_run_here") is True),
        "actual_manual_review_run_here": bool(r12_ready and r12.get("actual_manual_review_run_here") is True),
        "actual_rating_rows_materialized_here": bool(r12_ready and r12.get("actual_rating_rows_materialized_here") is True),
        "actual_blocker_rows_materialized_here": bool(r12_ready and r12.get("actual_blocker_rows_materialized_here") is True),
        "actual_execution_blocker_rows_materialized_here": bool(r12_ready and r12.get("actual_execution_blocker_rows_materialized_here") is True),
        "actual_question_need_observation_rows_materialized_here": bool(r12_ready and r12.get("actual_question_need_observation_rows_materialized_here") is True),
        "actual_question_need_observation_summary_materialized_here": False,
        "p5_actual_review_still_not_run": not r12_ready,
        "p5_human_blind_qa_confirmed_candidate": False,
        "p5_repair_return_candidate": False,
        "p5_review_inconclusive": False,
        "p6_limited_human_readfeel_start_allowed_candidate": False,
        "p8_question_design_material_candidate": False,
        "r0_current_source_r50_handoff_refrozen": True,
        "r1_validation_evidence_r49_timeout_handling_frozen": True,
        "r2_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r3_actual_review_session_envelope_created": True,
        "r4_24_case_manifest_freeze_built": True,
        "r5_local_only_body_full_packet_generation_request_built": True,
        "r6_body_full_packet_completeness_export_denylist_scan_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": bool(r12.get("r7_reviewer_instruction_rating_form_freeze_built")),
        "r8_actual_human_review_run_recorded": bool(r12.get("r8_actual_human_review_run_recorded")),
        "r9_rating_row_normalizer_built": bool(r12.get("r9_rating_row_normalizer_built")),
        "r10_readfeel_blocker_execution_blocker_ingestion_built": bool(r12.get("r10_readfeel_blocker_execution_blocker_ingestion_built")),
        "r11_question_need_observation_row_normalizer_built": bool(r12.get("r11_question_need_observation_row_normalizer_built")),
        "r12_rating_question_observation_consistency_guard_built": bool(r12.get("r12_rating_question_observation_consistency_guard_built")),
        "r13_pause_abort_expiration_protocol_built": protocol_built,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "implemented_steps": list(implemented_steps),
        "not_yet_implemented_steps": list(not_yet_steps),
        "first_next_work_ref": P7_R51_FIRST_NEXT_WORK_REF,
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "r51_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r51_pause_abort_expiration_protocol_bodyfree_contract(protocol, allowed_true_false_key_refs=actual_true_keys)
    return protocol


def build_p7_r51_pause_abort_expiration_protocol(**kwargs: Any) -> dict[str, Any]:
    return build_p7_r51_pause_abort_expiration_protocol_bodyfree(**kwargs)


def assert_p7_r51_pause_abort_expiration_protocol_bodyfree_contract(
    protocol: Mapping[str, Any],
    *,
    allowed_true_false_key_refs: Sequence[str] | None = None,
) -> bool:
    data = safe_mapping(protocol)
    _assert_required_fields(data, required=P7_R51_PAUSE_ABORT_EXPIRATION_PROTOCOL_BODYFREE_REQUIRED_FIELD_REFS, source="p7_r51_r13_pause_abort_expiration_protocol")
    allowed = tuple(
        allowed_true_false_key_refs
        or (
            "actual_human_review_run_here",
            "actual_manual_review_run_here",
            "actual_rating_rows_materialized_here",
            "actual_blocker_rows_materialized_here",
            "actual_execution_blocker_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
        )
    )
    _assert_body_free_common_allowing(
        data,
        schema_version=P7_R51_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION,
        source="p7_r51_r13_pause_abort_expiration_protocol",
        allowed_true_false_key_refs=allowed,
    )
    if data.get("policy_section") != "R51-13_pause_abort_expiration_protocol":
        raise ValueError("R51 R13 policy section changed")
    if data.get("pause_abort_expiration_protocol_status") not in P7_R51_PAUSE_ABORT_EXPIRATION_PROTOCOL_STATUS_REFS:
        raise ValueError("R51 R13 protocol status changed")
    if data.get("review_lifecycle_status") not in P7_R51_REVIEW_LIFECYCLE_STATUS_REFS:
        raise ValueError("R51 R13 lifecycle status changed")
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
            raise ValueError(f"R51 R13 must keep {false_key}=False")
    for true_key in (
        "review_pause_does_not_stop_retention_deadline",
        "review_abort_requires_purge",
        "expired_requires_purge_even_when_rating_incomplete",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R51 R13 must keep {true_key}=True")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=50, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R51 R13 open blockers must match execution blockers")
    unknown = sorted(set(blockers) - set(P7_R51_EXECUTION_BLOCKER_ID_REFS))
    if unknown:
        raise ValueError(f"R51 R13 execution blockers are not canonical: {unknown[:4]}")
    status = data.get("pause_abort_expiration_protocol_status")
    if status == "BLOCKED_BY_R51_12_CONSISTENCY_GUARD":
        if data.get("r13_pause_abort_expiration_protocol_built") is not False:
            raise ValueError("R51 R13 blocked protocol must not claim built")
        if data.get("next_required_step") != P7_R51_R13_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R13 blocked protocol must point to protocol resolution")
    else:
        if data.get("r13_pause_abort_expiration_protocol_built") is not True:
            raise ValueError("R51 R13 ready protocol must be built")
        if tuple(data.get("implemented_steps") or ()) != P7_R51_R13_IMPLEMENTED_STEPS:
            raise ValueError("R51 R13 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R51_R13_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R51 R13 not-yet steps changed")
    if status == "PAUSED_RETENTION_CLOCK_STILL_RUNNING":
        if data.get("retention_clock_stops_on_pause") is not False:
            raise ValueError("R51 R13 pause must not stop retention clock")
        if data.get("body_full_packet_purge_required") is not False:
            raise ValueError("R51 R13 non-expired pause must not require purge yet")
        if data.get("next_required_step") != P7_R51_R13_PAUSED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R13 paused protocol must remain in R51-13")
    if status in {"READY_FOR_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE", "ABORTED_PURGE_REQUIRED", "EXPIRED_PURGE_REQUIRED"}:
        for true_key in ("body_full_packet_purge_required", "reviewer_forms_purge_required", "reviewer_notes_purge_required", "purge_required_before_summary"):
            if data.get(true_key) is not True:
                raise ValueError(f"R51 R13 purge path must keep {true_key}=True")
        if data.get("next_required_step") != P7_R51_R13_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R13 purge path must point to R51-14")
    if status in {"ABORTED_PURGE_REQUIRED", "EXPIRED_PURGE_REQUIRED"}:
        if data.get("aborted_or_expired_blocks_p5_confirmed_candidate") is not True:
            raise ValueError("R51 R13 aborted/expired must block P5 confirmed candidate")
    if status == "EXPIRED_PURGE_REQUIRED" and data.get("body_removed_priority_over_rating_completion_when_expired") is not True:
        raise ValueError("R51 R13 expired protocol must prioritize body removal")
    return True


def build_p7_r51_purge_evidence_row_bodyfree(
    *,
    review_session_id: Any = P7_R51_DEFAULT_REVIEW_SESSION_ID,
    purge_target_ref: Any,
    purge_target_kind: Any | None = None,
    purge_required: bool = True,
    purge_attempted: bool = True,
    removed: bool = True,
    removed_count: Any = 1,
    verification_status_ref: Any | None = None,
) -> dict[str, Any]:
    """Build one body-free R51-14 purge evidence row.

    The row is a sanitized receipt of local-only deletion verification.  It
    never carries file paths, packet bodies, reviewer notes, hashes, deleted
    previews, terminal output, or raw local command output.
    """

    target_ref = clean_identifier(purge_target_ref, default="unknown_purge_target", max_length=160)
    target_kind = clean_identifier(purge_target_kind, default=target_ref, max_length=160)
    if verification_status_ref is None:
        if not purge_required and not removed:
            status = "NOT_REQUIRED_NOT_GENERATED"
        elif removed:
            status = "REMOVED_AND_VERIFIED"
        elif purge_attempted:
            status = "PURGE_FAILED"
        else:
            status = "PURGE_NOT_VERIFIED"
    else:
        status = clean_identifier(verification_status_ref, default="PURGE_NOT_VERIFIED", max_length=160)
    row = {
        "schema_version": P7_R51_PURGE_EVIDENCE_ROW_BODYFREE_SCHEMA_VERSION,
        "review_session_id": _safe_review_session_id(review_session_id),
        "purge_target_ref": target_ref,
        "purge_target_kind": target_kind,
        "purge_required": bool(purge_required),
        "purge_attempted": bool(purge_attempted),
        "removed": bool(removed),
        "removed_count": _safe_non_negative_int(removed_count) if removed else 0,
        "verification_status_ref": status,
        "local_absolute_path_included": False,
        "body_content_hash_included": False,
        "deleted_body_preview_included": False,
        "terminal_output_included": False,
        "body_free": True,
    }
    assert_p7_r51_purge_evidence_row_bodyfree_contract(row)
    return row


def assert_p7_r51_purge_evidence_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R51_PURGE_EVIDENCE_ROW_BODYFREE_REQUIRED_FIELD_REFS, source="p7_r51_purge_evidence_row_bodyfree")
    if data.get("schema_version") != P7_R51_PURGE_EVIDENCE_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R51 R14 purge evidence row schema version changed")
    if data.get("verification_status_ref") not in P7_R51_PURGE_EVIDENCE_ROW_STATUS_REFS:
        raise ValueError("R51 R14 purge evidence row must use a canonical verification status")
    if data.get("body_free") is not True:
        raise ValueError("R51 R14 purge evidence row must be body-free")
    for false_key in (
        "local_absolute_path_included",
        "body_content_hash_included",
        "deleted_body_preview_included",
        "terminal_output_included",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R51 R14 purge evidence row must keep {false_key}=False")
    if data.get("removed") is True and data.get("removed_count", 0) < 1:
        raise ValueError("R51 R14 removed purge target must carry a non-zero removed count")
    if data.get("removed") is False and data.get("verification_status_ref") == "REMOVED_AND_VERIFIED":
        raise ValueError("R51 R14 unremoved target cannot be verified removed")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r51_purge_evidence_row_bodyfree")
    return True


def _default_purge_evidence_rows_r51(*, review_session_id: Any) -> list[dict[str, Any]]:
    return [
        build_p7_r51_purge_evidence_row_bodyfree(
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


def _normalize_purge_evidence_rows_r51(
    raw_rows: Sequence[Mapping[str, Any]] | None,
    *,
    review_session_id: Any,
) -> list[dict[str, Any]]:
    # R51-14 must not invent purge evidence.  The helper verifies sanitized
    # body-free purge rows supplied by the local-only controller; absence of
    # rows remains a disposal-not-verified blocker.
    if raw_rows is None:
        return []
    rows: list[dict[str, Any]] = []
    for raw in raw_rows:
        data = safe_mapping(raw)
        if data.get("schema_version") == P7_R51_PURGE_EVIDENCE_ROW_BODYFREE_SCHEMA_VERSION:
            assert_p7_r51_purge_evidence_row_bodyfree_contract(data)
            rows.append(dict(data))
            continue
        rows.append(
            build_p7_r51_purge_evidence_row_bodyfree(
                review_session_id=review_session_id,
                purge_target_ref=data.get("purge_target_ref"),
                purge_target_kind=data.get("purge_target_kind"),
                purge_required=_safe_bool(data.get("purge_required"), default=True),
                purge_attempted=_safe_bool(data.get("purge_attempted"), default=True),
                removed=_safe_bool(data.get("removed"), default=False),
                removed_count=data.get("removed_count", 0),
                verification_status_ref=data.get("verification_status_ref"),
            )
        )
    return rows


def _purge_target_state_r51(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    by_target = {clean_identifier(row.get("purge_target_ref"), default="", max_length=160): safe_mapping(row) for row in rows}
    missing = [target for target in P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS if target not in by_target]
    failed: list[str] = []
    not_verified: list[str] = []
    verified_count = 0
    deleted_count = 0
    for target in P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS:
        row = by_target.get(target)
        if row is None:
            continue
        status = clean_identifier(row.get("verification_status_ref"), default="PURGE_NOT_VERIFIED", max_length=160)
        if row.get("removed") is True and status == "REMOVED_AND_VERIFIED":
            verified_count += 1
            deleted_count += _safe_non_negative_int(row.get("removed_count"))
        elif status == "PURGE_FAILED" or row.get("removed") is False:
            failed.append(target)
        else:
            not_verified.append(target)
    return {
        "purge_target_count": len(P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS),
        "verified_purge_target_count": verified_count,
        "missing_purge_target_refs": missing,
        "failed_purge_target_refs": failed,
        "not_verified_purge_target_refs": not_verified,
        "deleted_file_count": deleted_count,
        "all_verified": verified_count == len(P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS) and not missing and not failed and not not_verified,
    }


def build_p7_r51_body_full_packet_reviewer_notes_purge_bodyfree(
    *,
    pause_abort_expiration_protocol_bodyfree: Mapping[str, Any] | None = None,
    r13_pause_abort_expiration_protocol_bodyfree: Mapping[str, Any] | None = None,
    purge_evidence_rows: Sequence[Mapping[str, Any]] | None = None,
    purge_started_at_ref: Any = "r51_local_only_purge_started_at_local_controller",
    purge_completed_at_ref: Any = "r51_local_only_purge_completed_at_local_controller",
    material_id: Any = "p7_r51_body_full_packet_reviewer_notes_purge",
) -> dict[str, Any]:
    """Build R51-14 body-free purge verification material.

    This function records sanitized local-only purge evidence.  It does not
    delete files itself and it does not expose paths, hashes, packet bodies,
    reviewer note bodies, or terminal output.
    """

    if pause_abort_expiration_protocol_bodyfree is not None and r13_pause_abort_expiration_protocol_bodyfree is not None:
        raise ValueError("Provide either pause_abort_expiration_protocol_bodyfree or r13_pause_abort_expiration_protocol_bodyfree, not both")
    r13 = safe_mapping(
        pause_abort_expiration_protocol_bodyfree
        if pause_abort_expiration_protocol_bodyfree is not None
        else r13_pause_abort_expiration_protocol_bodyfree
        if r13_pause_abort_expiration_protocol_bodyfree is not None
        else build_p7_r51_pause_abort_expiration_protocol_bodyfree()
    )
    assert_p7_r51_pause_abort_expiration_protocol_bodyfree_contract(r13)

    review_session_id = _safe_review_session_id(r13.get("review_session_id"))
    r13_status = clean_identifier(r13.get("pause_abort_expiration_protocol_status"), default="", max_length=180)
    r13_allows_purge = r13_status in {
        "READY_FOR_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE",
        "ABORTED_PURGE_REQUIRED",
        "EXPIRED_PURGE_REQUIRED",
    }

    rows = _normalize_purge_evidence_rows_r51(
        purge_evidence_rows if r13_allows_purge else [],
        review_session_id=review_session_id,
    )
    for row in rows:
        assert_p7_r51_purge_evidence_row_bodyfree_contract(row)
    target_state = _purge_target_state_r51(rows)
    purge_verified = bool(r13_allows_purge and target_state["all_verified"])
    if not r13_allows_purge:
        status = "BLOCKED_BY_R51_13_PAUSE_OR_BLOCKED_PROTOCOL"
        reason_refs = ["r51_13_protocol_not_ready_for_purge"]
        blockers = ["r51_disposal_not_verified"]
    elif purge_verified:
        status = "READY_FOR_DISPOSAL_RECEIPT_BUILDER_VERIFIER"
        reason_refs = ["body_full_packet_reviewer_notes_purged_bodyfree_verified"]
        blockers = []
    else:
        status = "BLOCKED_BY_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE"
        reason_refs = ["body_full_packet_or_reviewer_notes_purge_not_verified"]
        blockers = ["r51_disposal_failed"] if target_state["failed_purge_target_refs"] else ["r51_disposal_not_verified"]
        if target_state["missing_purge_target_refs"]:
            blockers = ["r51_disposal_not_verified"]
    body_removed = purge_verified
    reviewer_forms_removed = purge_verified
    reviewer_notes_removed = purge_verified
    material = {
        **_false_flags(),
        "schema_version": P7_R51_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R51_STEP,
        "scope": P7_R51_SCOPE,
        "policy_kind": P7_R51_POLICY_KIND,
        "policy_section": "R51-14_body_full_packet_reviewer_notes_purge",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r51_body_full_packet_reviewer_notes_purge", max_length=180),
        "review_session_id": review_session_id,
        "review_session_status": "R51_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE_VERIFIED_BODYFREE" if purge_verified else "R51_PAUSE_ABORT_EXPIRATION_PROTOCOL_READY",
        "r13_pause_abort_expiration_protocol_schema_version": P7_R51_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION,
        "r13_pause_abort_expiration_protocol_ref": clean_identifier(r13.get("material_id"), default="p7_r51_pause_abort_expiration_protocol", max_length=180),
        "pause_abort_expiration_protocol_status": r13_status,
        "review_lifecycle_status": clean_identifier(r13.get("review_lifecycle_status"), default="REVIEW_COMPLETED", max_length=160),
        "purge_status": status,
        "purge_reason_refs": dedupe_identifiers(reason_refs, limit=12, max_length=160),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "purge_required_before_summary": r13.get("purge_required_before_summary") is True,
        "body_full_packet_purge_required": r13.get("body_full_packet_purge_required") is True,
        "reviewer_forms_purge_required": r13.get("reviewer_forms_purge_required") is True,
        "reviewer_notes_purge_required": r13.get("reviewer_notes_purge_required") is True,
        "required_purge_target_refs": list(P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS),
        "purge_evidence_row_schema_version": P7_R51_PURGE_EVIDENCE_ROW_BODYFREE_SCHEMA_VERSION,
        "purge_evidence_row_required_field_refs": list(P7_R51_PURGE_EVIDENCE_ROW_BODYFREE_REQUIRED_FIELD_REFS),
        "purge_evidence_rows": rows,
        "purge_evidence_row_count": len(rows),
        "purge_target_count": target_state["purge_target_count"],
        "verified_purge_target_count": target_state["verified_purge_target_count"],
        "missing_purge_target_refs": list(target_state["missing_purge_target_refs"]),
        "failed_purge_target_refs": list(target_state["failed_purge_target_refs"]),
        "not_verified_purge_target_refs": list(target_state["not_verified_purge_target_refs"]),
        "deleted_file_count": target_state["deleted_file_count"] if purge_verified else 0,
        "purge_started_at_ref": clean_identifier(purge_started_at_ref, default="r51_local_only_purge_started_at_local_controller", max_length=160),
        "purge_completed_at_ref": clean_identifier(purge_completed_at_ref, default="r51_local_only_purge_completed_at_local_controller", max_length=160),
        "disposal_status": "BODY_PURGED" if purge_verified else "DISPOSAL_FAILED" if r13_allows_purge else "PURGE_REQUIRED",
        "body_removed": body_removed,
        "reviewer_forms_removed": reviewer_forms_removed,
        "reviewer_notes_removed": reviewer_notes_removed,
        "body_full_packets_removed": body_removed,
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "local_absolute_path_included": False,
        "body_content_hash_included": False,
        "deleted_body_preview_included": False,
        "terminal_output_included": False,
        "local_file_delete_ops_executed_by_helper": False,
        "actual_disposal_run_here": purge_verified or (r13_allows_purge and bool(rows)),
        "disposal_receipt_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "post_review_summary_materialized_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "actual_human_review_run_here": r13.get("actual_human_review_run_here") is True,
        "actual_manual_review_run_here": r13.get("actual_manual_review_run_here") is True,
        "actual_rating_rows_materialized_here": r13.get("actual_rating_rows_materialized_here") is True,
        "actual_blocker_rows_materialized_here": r13.get("actual_blocker_rows_materialized_here") is True,
        "actual_execution_blocker_rows_materialized_here": r13.get("actual_execution_blocker_rows_materialized_here") is True,
        "actual_question_need_observation_rows_materialized_here": r13.get("actual_question_need_observation_rows_materialized_here") is True,
        "actual_question_need_observation_summary_materialized_here": False,
        "p5_actual_review_still_not_run": False if r13.get("actual_human_review_run_here") is True else bool(r13.get("p5_actual_review_still_not_run", False)),
        "p5_human_blind_qa_confirmed_candidate": False,
        "p5_repair_return_candidate": False,
        "p5_review_inconclusive": False,
        "p6_limited_human_readfeel_start_allowed_candidate": False,
        "p8_question_design_material_candidate": False,
        "r0_current_source_r50_handoff_refrozen": True,
        "r1_validation_evidence_r49_timeout_handling_frozen": True,
        "r2_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r3_actual_review_session_envelope_created": True,
        "r4_24_case_manifest_freeze_built": True,
        "r5_local_only_body_full_packet_generation_request_built": True,
        "r6_body_full_packet_completeness_export_denylist_scan_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": True,
        "r8_actual_human_review_run_recorded": r13.get("actual_human_review_run_here") is True,
        "r9_rating_row_normalizer_built": r13.get("actual_rating_rows_materialized_here") is True,
        "r10_readfeel_blocker_execution_blocker_ingestion_built": True,
        "r11_question_need_observation_row_normalizer_built": r13.get("actual_question_need_observation_rows_materialized_here") is True,
        "r12_rating_question_observation_consistency_guard_built": r13.get("r12_rating_question_observation_consistency_guard_built") is True,
        "r13_pause_abort_expiration_protocol_built": r13.get("r13_pause_abort_expiration_protocol_built") is True,
        "r14_body_full_packet_reviewer_notes_purge_built": purge_verified,
        "execution_blocker_ids": dedupe_identifiers(blockers, limit=20, max_length=140),
        "open_execution_blocker_ids": dedupe_identifiers(blockers, limit=20, max_length=140),
        "implemented_steps": list(P7_R51_R14_IMPLEMENTED_STEPS) if purge_verified else list(P7_R51_R13_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R51_R14_NOT_YET_IMPLEMENTED_STEPS) if purge_verified else list(P7_R51_R13_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R51_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R51_R14_NEXT_REQUIRED_STEP_REF if purge_verified else (P7_R51_R14_PAUSED_OR_BLOCKED_NEXT_REQUIRED_STEP_REF if not r13_allows_purge else P7_R51_R14_BLOCKED_NEXT_REQUIRED_STEP_REF),
        "public_contract": public_contract_flags(),
        "r51_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r51_body_full_packet_reviewer_notes_purge_bodyfree_contract(material)
    return material


def assert_p7_r51_body_full_packet_reviewer_notes_purge_bodyfree_contract(
    purge: Mapping[str, Any],
    *,
    allowed_true_false_key_refs: Sequence[str] | None = None,
) -> bool:
    data = safe_mapping(purge)
    _assert_required_fields(data, required=P7_R51_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE_BODYFREE_REQUIRED_FIELD_REFS, source="p7_r51_r14_body_full_packet_reviewer_notes_purge")
    allowed = tuple(
        allowed_true_false_key_refs
        or (
            "actual_human_review_run_here",
            "actual_manual_review_run_here",
            "actual_rating_rows_materialized_here",
            "actual_blocker_rows_materialized_here",
            "actual_execution_blocker_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_run_here",
        )
    )
    _assert_body_free_common_allowing(
        data,
        schema_version=P7_R51_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE_SCHEMA_VERSION,
        source="p7_r51_r14_body_full_packet_reviewer_notes_purge",
        allowed_true_false_key_refs=allowed,
    )
    if data.get("policy_section") != "R51-14_body_full_packet_reviewer_notes_purge":
        raise ValueError("R51 R14 policy section changed")
    if data.get("purge_status") not in P7_R51_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE_STATUS_REFS:
        raise ValueError("R51 R14 purge status changed")
    if data.get("disposal_status") not in P7_R51_DISPOSAL_STATUS_REFS:
        raise ValueError("R51 R14 disposal status changed")
    rows = data.get("purge_evidence_rows")
    if not isinstance(rows, list):
        raise ValueError("R51 R14 purge evidence rows must be a list")
    for row in rows:
        assert_p7_r51_purge_evidence_row_bodyfree_contract(safe_mapping(row))
    if tuple(data.get("purge_evidence_row_required_field_refs") or ()) != P7_R51_PURGE_EVIDENCE_ROW_BODYFREE_REQUIRED_FIELD_REFS:
        raise ValueError("R51 R14 purge evidence row contract changed")
    if tuple(data.get("required_purge_target_refs") or ()) != P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS:
        raise ValueError("R51 R14 required purge targets changed")
    for false_key in (
        "local_packet_exported",
        "content_hash_of_body_stored",
        "local_absolute_path_included",
        "body_content_hash_included",
        "deleted_body_preview_included",
        "terminal_output_included",
        "local_file_delete_ops_executed_by_helper",
        "disposal_receipt_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "post_review_summary_materialized_here",
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
            raise ValueError(f"R51 R14 must keep {false_key}=False")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=20, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R51 R14 open blockers must match execution blockers")
    unknown = sorted(set(blockers) - set(P7_R51_EXECUTION_BLOCKER_ID_REFS))
    if unknown:
        raise ValueError(f"R51 R14 execution blockers are not canonical: {unknown[:4]}")
    status = data.get("purge_status")
    if status == "READY_FOR_DISPOSAL_RECEIPT_BUILDER_VERIFIER":
        for true_key in ("body_removed", "reviewer_forms_removed", "reviewer_notes_removed", "body_full_packets_removed", "actual_disposal_run_here", "r14_body_full_packet_reviewer_notes_purge_built"):
            if data.get(true_key) is not True:
                raise ValueError(f"R51 R14 verified purge must keep {true_key}=True")
        if data.get("disposal_status") != "BODY_PURGED":
            raise ValueError("R51 R14 verified purge must have BODY_PURGED disposal status")
        if data.get("missing_purge_target_refs") or data.get("failed_purge_target_refs") or data.get("not_verified_purge_target_refs"):
            raise ValueError("R51 R14 verified purge must not carry unresolved purge targets")
        if tuple(data.get("implemented_steps") or ()) != P7_R51_R14_IMPLEMENTED_STEPS:
            raise ValueError("R51 R14 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R51_R14_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R51 R14 not-yet steps changed")
        if data.get("next_required_step") != P7_R51_R14_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R14 verified purge must point to R51-15")
    else:
        for false_key in ("body_removed", "reviewer_forms_removed", "reviewer_notes_removed", "body_full_packets_removed", "r14_body_full_packet_reviewer_notes_purge_built"):
            if data.get(false_key) is not False:
                raise ValueError(f"R51 R14 blocked purge must keep {false_key}=False")
        if tuple(data.get("implemented_steps") or ()) != P7_R51_R13_IMPLEMENTED_STEPS:
            raise ValueError("R51 R14 blocked purge must not advance implemented steps")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R51_R13_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R51 R14 blocked purge must retain R13 not-yet steps")
        if status == "BLOCKED_BY_R51_13_PAUSE_OR_BLOCKED_PROTOCOL":
            if data.get("next_required_step") != P7_R51_R14_PAUSED_OR_BLOCKED_NEXT_REQUIRED_STEP_REF:
                raise ValueError("R51 R14 R13-blocked purge must point back to R51-13 resolution")
        elif data.get("next_required_step") != P7_R51_R14_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R14 purge verification failure must point to R51-14 resolution")
    return True


def _build_p7_r51_disposal_receipt_bodyfree(*, purge: Mapping[str, Any]) -> dict[str, Any]:
    data = safe_mapping(purge)
    disposal_status = "DISPOSAL_VERIFIED" if data.get("purge_status") == "READY_FOR_DISPOSAL_RECEIPT_BUILDER_VERIFIER" else "DISPOSAL_FAILED"
    receipt = {
        "schema_version": P7_R51_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION,
        "review_session_id": _safe_review_session_id(data.get("review_session_id")),
        "packet_kind": P7_R51_PACKET_KIND,
        "case_count": P7_R51_REQUIRED_CASE_COUNT,
        "deleted_file_count": _safe_non_negative_int(data.get("deleted_file_count")),
        "purge_started_at_ref": clean_identifier(data.get("purge_started_at_ref"), default="r51_local_only_purge_started_at_local_controller", max_length=160),
        "purge_completed_at_ref": clean_identifier(data.get("purge_completed_at_ref"), default="r51_local_only_purge_completed_at_local_controller", max_length=160),
        "disposal_status": disposal_status,
        "body_removed": data.get("body_removed") is True,
        "reviewer_forms_removed": data.get("reviewer_forms_removed") is True,
        "reviewer_notes_removed": data.get("reviewer_notes_removed") is True,
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "local_absolute_path_included": False,
        "body_content_hash_included": False,
        "deleted_body_preview_included": False,
        "terminal_output_included": False,
        "receipt_contains_body_full_material": False,
        "release_allowed": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "hold004_close_allowed": False,
        "body_free": True,
    }
    assert_p7_r51_disposal_receipt_bodyfree_contract(receipt)
    return receipt


def assert_p7_r51_disposal_receipt_bodyfree_contract(receipt: Mapping[str, Any]) -> bool:
    data = safe_mapping(receipt)
    _assert_required_fields(data, required=P7_R51_DISPOSAL_RECEIPT_BODYFREE_REQUIRED_FIELD_REFS, source="p7_r51_disposal_receipt_bodyfree")
    if data.get("schema_version") != P7_R51_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R51 R15 disposal receipt schema version changed")
    if data.get("disposal_status") not in P7_R51_DISPOSAL_STATUS_REFS:
        raise ValueError("R51 R15 disposal receipt status changed")
    if data.get("body_free") is not True:
        raise ValueError("R51 R15 disposal receipt must be body-free")
    for false_key in (
        "local_packet_exported",
        "content_hash_of_body_stored",
        "local_absolute_path_included",
        "body_content_hash_included",
        "deleted_body_preview_included",
        "terminal_output_included",
        "receipt_contains_body_full_material",
        "release_allowed",
        "p7_complete",
        "p8_start_allowed",
        "hold004_close_allowed",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R51 R15 disposal receipt must keep {false_key}=False")
    if data.get("disposal_status") == "DISPOSAL_VERIFIED":
        for true_key in ("body_removed", "reviewer_forms_removed", "reviewer_notes_removed"):
            if data.get(true_key) is not True:
                raise ValueError(f"R51 R15 verified receipt must keep {true_key}=True")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r51_disposal_receipt_bodyfree")
    return True


def build_p7_r51_disposal_receipt_builder_verifier_bodyfree(
    *,
    body_full_packet_reviewer_notes_purge_bodyfree: Mapping[str, Any] | None = None,
    r14_body_full_packet_reviewer_notes_purge_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r51_disposal_receipt_builder_verifier",
) -> dict[str, Any]:
    """Build and verify the R51-15 body-free disposal receipt."""

    if body_full_packet_reviewer_notes_purge_bodyfree is not None and r14_body_full_packet_reviewer_notes_purge_bodyfree is not None:
        raise ValueError("Provide either body_full_packet_reviewer_notes_purge_bodyfree or r14_body_full_packet_reviewer_notes_purge_bodyfree, not both")
    r14 = safe_mapping(
        body_full_packet_reviewer_notes_purge_bodyfree
        if body_full_packet_reviewer_notes_purge_bodyfree is not None
        else r14_body_full_packet_reviewer_notes_purge_bodyfree
        if r14_body_full_packet_reviewer_notes_purge_bodyfree is not None
        else build_p7_r51_body_full_packet_reviewer_notes_purge_bodyfree()
    )
    assert_p7_r51_body_full_packet_reviewer_notes_purge_bodyfree_contract(r14)

    receipt = _build_p7_r51_disposal_receipt_bodyfree(purge=r14)
    purge_ready = r14.get("purge_status") == "READY_FOR_DISPOSAL_RECEIPT_BUILDER_VERIFIER"
    receipt_verified = (
        purge_ready
        and receipt.get("disposal_status") == "DISPOSAL_VERIFIED"
        and receipt.get("body_removed") is True
        and receipt.get("reviewer_forms_removed") is True
        and receipt.get("reviewer_notes_removed") is True
        and receipt.get("local_packet_exported") is False
        and receipt.get("content_hash_of_body_stored") is False
        and receipt.get("receipt_contains_body_full_material") is False
    )
    if receipt_verified:
        status = "READY_FOR_BODY_FREE_POST_REVIEW_SUMMARY_BUILDER"
        reasons = ["disposal_receipt_bodyfree_verified"]
        blockers: list[str] = []
    elif not purge_ready:
        status = "BLOCKED_BY_R51_14_PURGE"
        reasons = ["r51_14_purge_not_verified"]
        blockers = dedupe_identifiers(r14.get("execution_blocker_ids") or ["r51_disposal_not_verified"], limit=20, max_length=140)
    else:
        status = "BLOCKED_BY_DISPOSAL_RECEIPT_VERIFICATION"
        reasons = ["disposal_receipt_bodyfree_verification_failed"]
        blockers = ["r51_disposal_not_verified"]
    material = {
        **_false_flags(),
        "schema_version": P7_R51_DISPOSAL_RECEIPT_BUILDER_VERIFIER_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R51_STEP,
        "scope": P7_R51_SCOPE,
        "policy_kind": P7_R51_POLICY_KIND,
        "policy_section": "R51-15_disposal_receipt_builder_verifier",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r51_disposal_receipt_builder_verifier", max_length=180),
        "review_session_id": _safe_review_session_id(r14.get("review_session_id")),
        "review_session_status": (
            "R51_DISPOSAL_RECEIPT_VERIFIED_BODYFREE"
            if receipt_verified
            else "R51_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE_VERIFIED_BODYFREE"
            if purge_ready
            else "R51_PAUSE_ABORT_EXPIRATION_PROTOCOL_READY"
        ),
        "r14_purge_schema_version": P7_R51_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE_SCHEMA_VERSION,
        "r14_purge_ref": clean_identifier(r14.get("material_id"), default="p7_r51_body_full_packet_reviewer_notes_purge", max_length=180),
        "purge_status": clean_identifier(r14.get("purge_status"), default="BLOCKED_BY_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE", max_length=180),
        "disposal_receipt_verifier_status": status,
        "disposal_receipt_reason_refs": dedupe_identifiers(reasons, limit=12, max_length=160),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "packet_kind": P7_R51_PACKET_KIND,
        "disposal_receipt_schema_version": P7_R51_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION,
        "disposal_receipt_required_field_refs": list(P7_R51_DISPOSAL_RECEIPT_BODYFREE_REQUIRED_FIELD_REFS),
        "disposal_receipt": receipt,
        "disposal_status": clean_identifier(receipt.get("disposal_status"), default="DISPOSAL_FAILED", max_length=160),
        "body_removed": receipt.get("body_removed") is True,
        "reviewer_forms_removed": receipt.get("reviewer_forms_removed") is True,
        "reviewer_notes_removed": receipt.get("reviewer_notes_removed") is True,
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "receipt_contains_body_full_material": False,
        "local_absolute_path_included": False,
        "body_content_hash_included": False,
        "deleted_body_preview_included": False,
        "terminal_output_included": False,
        "deleted_file_count": _safe_non_negative_int(receipt.get("deleted_file_count")),
        "purge_started_at_ref": clean_identifier(receipt.get("purge_started_at_ref"), default="r51_local_only_purge_started_at_local_controller", max_length=160),
        "purge_completed_at_ref": clean_identifier(receipt.get("purge_completed_at_ref"), default="r51_local_only_purge_completed_at_local_controller", max_length=160),
        "disposal_verified": receipt_verified,
        "disposal_failed": not receipt_verified,
        "disposal_receipt_missing": False,
        "summary_finalize_allowed": receipt_verified,
        "actual_disposal_run_here": r14.get("actual_disposal_run_here") is True,
        "disposal_receipt_materialized_here": True,
        "actual_disposal_receipt_materialized_here": True,
        "post_review_summary_materialized_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "actual_human_review_run_here": r14.get("actual_human_review_run_here") is True,
        "actual_manual_review_run_here": r14.get("actual_manual_review_run_here") is True,
        "actual_rating_rows_materialized_here": r14.get("actual_rating_rows_materialized_here") is True,
        "actual_blocker_rows_materialized_here": r14.get("actual_blocker_rows_materialized_here") is True,
        "actual_execution_blocker_rows_materialized_here": r14.get("actual_execution_blocker_rows_materialized_here") is True,
        "actual_question_need_observation_rows_materialized_here": r14.get("actual_question_need_observation_rows_materialized_here") is True,
        "actual_question_need_observation_summary_materialized_here": False,
        "p5_actual_review_still_not_run": False if r14.get("actual_human_review_run_here") is True else bool(r14.get("p5_actual_review_still_not_run", False)),
        "p5_human_blind_qa_confirmed_candidate": False,
        "p5_repair_return_candidate": False,
        "p5_review_inconclusive": False,
        "p6_limited_human_readfeel_start_allowed_candidate": False,
        "p8_question_design_material_candidate": False,
        "r0_current_source_r50_handoff_refrozen": True,
        "r1_validation_evidence_r49_timeout_handling_frozen": True,
        "r2_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r3_actual_review_session_envelope_created": True,
        "r4_24_case_manifest_freeze_built": True,
        "r5_local_only_body_full_packet_generation_request_built": True,
        "r6_body_full_packet_completeness_export_denylist_scan_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": True,
        "r8_actual_human_review_run_recorded": r14.get("actual_human_review_run_here") is True,
        "r9_rating_row_normalizer_built": r14.get("actual_rating_rows_materialized_here") is True,
        "r10_readfeel_blocker_execution_blocker_ingestion_built": r14.get("r10_readfeel_blocker_execution_blocker_ingestion_built") is True,
        "r11_question_need_observation_row_normalizer_built": r14.get("actual_question_need_observation_rows_materialized_here") is True,
        "r12_rating_question_observation_consistency_guard_built": r14.get("r12_rating_question_observation_consistency_guard_built") is True,
        "r13_pause_abort_expiration_protocol_built": r14.get("r13_pause_abort_expiration_protocol_built") is True,
        "r14_body_full_packet_reviewer_notes_purge_built": r14.get("r14_body_full_packet_reviewer_notes_purge_built") is True,
        "r15_disposal_receipt_builder_verifier_built": receipt_verified,
        "execution_blocker_ids": dedupe_identifiers(blockers, limit=20, max_length=140),
        "open_execution_blocker_ids": dedupe_identifiers(blockers, limit=20, max_length=140),
        "implemented_steps": list(P7_R51_R15_IMPLEMENTED_STEPS) if receipt_verified else list(P7_R51_R14_IMPLEMENTED_STEPS if purge_ready else P7_R51_R13_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R51_R15_NOT_YET_IMPLEMENTED_STEPS) if receipt_verified else list(P7_R51_R14_NOT_YET_IMPLEMENTED_STEPS if purge_ready else P7_R51_R13_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R51_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R51_R15_NEXT_REQUIRED_STEP_REF if receipt_verified else P7_R51_R15_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r51_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r51_disposal_receipt_builder_verifier_bodyfree_contract(material)
    return material


def assert_p7_r51_disposal_receipt_builder_verifier_bodyfree_contract(
    verifier: Mapping[str, Any],
    *,
    allowed_true_false_key_refs: Sequence[str] | None = None,
) -> bool:
    data = safe_mapping(verifier)
    _assert_required_fields(data, required=P7_R51_DISPOSAL_RECEIPT_BUILDER_VERIFIER_BODYFREE_REQUIRED_FIELD_REFS, source="p7_r51_r15_disposal_receipt_builder_verifier")
    allowed = tuple(
        allowed_true_false_key_refs
        or (
            "actual_human_review_run_here",
            "actual_manual_review_run_here",
            "actual_rating_rows_materialized_here",
            "actual_blocker_rows_materialized_here",
            "actual_execution_blocker_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_run_here",
            "disposal_receipt_materialized_here",
            "actual_disposal_receipt_materialized_here",
        )
    )
    _assert_body_free_common_allowing(
        data,
        schema_version=P7_R51_DISPOSAL_RECEIPT_BUILDER_VERIFIER_SCHEMA_VERSION,
        source="p7_r51_r15_disposal_receipt_builder_verifier",
        allowed_true_false_key_refs=allowed,
    )
    if data.get("policy_section") != "R51-15_disposal_receipt_builder_verifier":
        raise ValueError("R51 R15 policy section changed")
    if data.get("disposal_receipt_verifier_status") not in P7_R51_DISPOSAL_RECEIPT_VERIFIER_STATUS_REFS:
        raise ValueError("R51 R15 verifier status changed")
    if data.get("disposal_status") not in P7_R51_DISPOSAL_STATUS_REFS:
        raise ValueError("R51 R15 disposal status changed")
    receipt = safe_mapping(data.get("disposal_receipt"))
    assert_p7_r51_disposal_receipt_bodyfree_contract(receipt)
    if tuple(data.get("disposal_receipt_required_field_refs") or ()) != P7_R51_DISPOSAL_RECEIPT_BODYFREE_REQUIRED_FIELD_REFS:
        raise ValueError("R51 R15 receipt contract changed")
    for false_key in (
        "local_packet_exported",
        "content_hash_of_body_stored",
        "receipt_contains_body_full_material",
        "local_absolute_path_included",
        "body_content_hash_included",
        "deleted_body_preview_included",
        "terminal_output_included",
        "post_review_summary_materialized_here",
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
            raise ValueError(f"R51 R15 must keep {false_key}=False")
    for true_key in ("disposal_receipt_materialized_here", "actual_disposal_receipt_materialized_here"):
        if data.get(true_key) is not True:
            raise ValueError(f"R51 R15 must materialize the body-free receipt flag {true_key}")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=20, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R51 R15 open blockers must match execution blockers")
    unknown = sorted(set(blockers) - set(P7_R51_EXECUTION_BLOCKER_ID_REFS))
    if unknown:
        raise ValueError(f"R51 R15 execution blockers are not canonical: {unknown[:4]}")
    status = data.get("disposal_receipt_verifier_status")
    if status == "READY_FOR_BODY_FREE_POST_REVIEW_SUMMARY_BUILDER":
        for true_key in ("body_removed", "reviewer_forms_removed", "reviewer_notes_removed", "disposal_verified", "summary_finalize_allowed", "actual_disposal_run_here", "r14_body_full_packet_reviewer_notes_purge_built", "r15_disposal_receipt_builder_verifier_built"):
            if data.get(true_key) is not True:
                raise ValueError(f"R51 R15 verified receipt must keep {true_key}=True")
        if data.get("disposal_status") != "DISPOSAL_VERIFIED":
            raise ValueError("R51 R15 verified receipt must have DISPOSAL_VERIFIED status")
        if tuple(data.get("implemented_steps") or ()) != P7_R51_R15_IMPLEMENTED_STEPS:
            raise ValueError("R51 R15 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R51_R15_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R51 R15 not-yet steps changed")
        if data.get("next_required_step") != P7_R51_R15_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R15 verified receipt must point to R51-16")
    else:
        if data.get("disposal_verified") is not False or data.get("summary_finalize_allowed") is not False:
            raise ValueError("R51 R15 blocked receipt must not allow summary finalize")
        if data.get("r15_disposal_receipt_builder_verifier_built") is not False:
            raise ValueError("R51 R15 blocked receipt must not claim verified builder")
        if data.get("next_required_step") != P7_R51_R15_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R15 blocked receipt must point to disposal receipt resolution")
    return True

def build_p7_r51_r0_r7_reviewer_instruction_rating_form_chain(
    *,
    local_review_root: Any,
    explicit_allow_token: Any,
    purge_plan: Mapping[str, Any] | None = None,
    export_candidate_refs: Sequence[Any] | Any | None = None,
    reviewer_ref: Any = P7_R51_DEFAULT_REVIEWER_REF,
) -> dict[str, Any]:
    """Build and validate R51-0..R51-7, returning the R51-7 freeze."""

    request = build_p7_r51_r0_r5_packet_generation_request_chain(
        local_review_root=local_review_root,
        explicit_allow_token=explicit_allow_token,
        purge_plan=purge_plan,
        export_candidate_refs=export_candidate_refs,
        reviewer_ref=reviewer_ref,
    )
    scan = build_p7_r51_body_full_packet_completeness_export_denylist_scan_bodyfree(
        local_only_body_full_packet_generation_request=request,
        export_candidate_refs=export_candidate_refs,
    )
    return build_p7_r51_reviewer_instruction_rating_form_freeze_bodyfree(
        body_full_packet_completeness_export_denylist_scan=scan,
    )

def build_p7_r51_r0_r5_packet_generation_request_chain(
    *,
    local_review_root: Any,
    explicit_allow_token: Any,
    purge_plan: Mapping[str, Any] | None = None,
    export_candidate_refs: Sequence[Any] | Any | None = None,
    reviewer_ref: Any = P7_R51_DEFAULT_REVIEWER_REF,
) -> dict[str, Any]:
    """Build and validate R51-0..R51-5, returning the R51-5 request."""

    envelope = build_p7_r51_r0_r3_preflight_session_envelope_chain(
        local_review_root=local_review_root,
        explicit_allow_token=explicit_allow_token,
        purge_plan=purge_plan,
        export_candidate_refs=export_candidate_refs,
        reviewer_ref=reviewer_ref,
    )
    manifest = build_p7_r51_24_case_manifest_freeze_bodyfree(actual_review_session_envelope=envelope)
    return build_p7_r51_local_only_body_full_packet_generation_request_bodyfree(case_manifest_freeze=manifest)

def build_p7_r51_r0_r3_preflight_session_envelope_chain(
    *,
    local_review_root: Any,
    explicit_allow_token: Any,
    purge_plan: Mapping[str, Any] | None = None,
    export_candidate_refs: Sequence[Any] | Any | None = None,
    reviewer_ref: Any = P7_R51_DEFAULT_REVIEWER_REF,
) -> dict[str, Any]:
    """Build and validate R51-0..R51-3, returning the R51-3 envelope."""

    r0 = build_p7_r51_current_source_r50_handoff_refreeze()
    r1 = build_p7_r51_validation_evidence_r49_timeout_handling_freeze(current_source_r50_handoff_refreeze=r0)
    r2 = build_p7_r51_local_root_explicit_allow_purge_plan_preflight(
        validation_evidence_r49_timeout_handling_freeze=r1,
        local_review_root=local_review_root,
        explicit_allow_token=explicit_allow_token,
        purge_plan=purge_plan if purge_plan is not None else build_p7_r51_default_local_only_purge_plan_bodyfree(),
        export_candidate_refs=export_candidate_refs,
    )
    return build_p7_r51_actual_review_session_envelope_bodyfree(
        local_root_explicit_allow_purge_plan_preflight=r2,
        reviewer_ref=reviewer_ref,
    )


def build_p7_r51_r0_r1_current_source_validation_evidence_freeze(
    *,
    current_source_r50_handoff_refreeze: Mapping[str, Any] | None = None,
    validation_evidence_r49_timeout_handling_freeze: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the R51-1 material after validating the R51-0/R51-1 chain."""

    r0 = (
        safe_mapping(current_source_r50_handoff_refreeze)
        if current_source_r50_handoff_refreeze is not None
        else build_p7_r51_current_source_r50_handoff_refreeze()
    )
    assert_p7_r51_current_source_r50_handoff_refreeze_contract(r0)
    r1 = (
        safe_mapping(validation_evidence_r49_timeout_handling_freeze)
        if validation_evidence_r49_timeout_handling_freeze is not None
        else build_p7_r51_validation_evidence_r49_timeout_handling_freeze(
            current_source_r50_handoff_refreeze=r0,
        )
    )
    assert_p7_r51_validation_evidence_r49_timeout_handling_freeze_contract(r1)
    if r1.get("r0_refreeze_material_ref") != r0.get("material_id"):
        raise ValueError("R51 R0/R1 chain material refs do not match")
    return r1

# ---------------------------------------------------------------------------
# R51-16 / R51-17: body-free post-review summary and P5 decision candidate.
# ---------------------------------------------------------------------------

P7_R51_BODY_FREE_POST_REVIEW_SUMMARY_BUILDER_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r51.body_free_post_review_summary_builder.bodyfree.v1"
)
P7_R51_P5_CONFIRMED_REPAIR_RETURN_INCONCLUSIVE_DECISION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r51.p5_confirmed_repair_return_inconclusive_decision.bodyfree.v1"
)

P7_R51_R16_NEXT_REQUIRED_STEP_REF: Final = "R51-17_p5_confirmed_repair_return_inconclusive_decision"
P7_R51_R16_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R51-16_body_free_post_review_summary_before_R51-17_decision"
P7_R51_R17_CONFIRMED_NEXT_REQUIRED_STEP_REF: Final = "R51-18_p6_limited_human_readfeel_candidate_handoff"
P7_R51_R17_REPAIR_RETURN_NEXT_REQUIRED_STEP_REF: Final = "return_to_P5_repair_before_R51-18_candidate_handoff"
P7_R51_R17_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF: Final = "resolve_R51-17_inconclusive_before_P6_P8_candidate_handoff"

P7_R51_R16_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R51_R15_IMPLEMENTED_STEPS,
    "R51-16_body_free_post_review_summary_builder",
)
P7_R51_R16_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R51_R15_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R51_R17_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R51_R16_IMPLEMENTED_STEPS,
    "R51-17_p5_confirmed_repair_return_inconclusive_decision",
)
P7_R51_R17_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R51_R16_NOT_YET_IMPLEMENTED_STEPS[1:]

P7_R51_POST_REVIEW_SUMMARY_STATUS_REFS: Final[tuple[str, ...]] = (
    "READY_FOR_P5_CONFIRMED_REPAIR_RETURN_INCONCLUSIVE_DECISION",
    "BLOCKED_BY_POST_REVIEW_SUMMARY_REQUIREMENTS",
)
P7_R51_P5_DECISION_STATUS_REFS: Final[tuple[str, ...]] = (
    "P5_CONFIRMED_CANDIDATE",
    "P5_REPAIR_RETURN_CANDIDATE",
    "P5_REVIEW_INCONCLUSIVE",
)
P7_R51_CRITICAL_REPAIR_BLOCKER_REFS: Final[tuple[str, ...]] = (
    "p5_history_creepy_or_surveillance_feeling",
    "p5_history_scope_overclaim",
    "p5_history_line_self_blame_amplification",
    "p5_free_tier_history_boundary_violation",
    "p5_low_information_history_overread",
    "p5_current_input_overridden_by_history",
    "p5_boundary_history_line_leak_suspected",
)
P7_R51_REPAIR_OBSERVATION_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = (
    "not_question_emlis_readfeel_repair_required",
    "not_question_p5_surface_repair_required",
    "not_question_gate_boundary_required",
)

P7_R51_BODY_FREE_POST_REVIEW_SUMMARY_BUILDER_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "review_session_status",
    "r15_disposal_receipt_builder_verifier_schema_version",
    "r15_disposal_receipt_builder_verifier_ref",
    "disposal_receipt_verifier_status",
    "r9_rating_row_normalizer_schema_version",
    "r9_rating_row_normalizer_ref",
    "rating_row_normalizer_status",
    "r10_blocker_ingestion_schema_version",
    "r10_blocker_ingestion_ref",
    "blocker_ingestion_status",
    "r11_question_observation_normalizer_schema_version",
    "r11_question_observation_normalizer_ref",
    "question_observation_normalizer_status",
    "r12_consistency_guard_schema_version",
    "r12_consistency_guard_ref",
    "rating_question_consistency_guard_status",
    "post_review_summary_status",
    "post_review_summary_reason_refs",
    "required_case_count",
    "review_session_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "readfeel_blocker_row_count",
    "execution_blocker_row_count",
    "open_readfeel_blocker_count",
    "open_execution_blocker_count",
    "all_24_cases_reviewed",
    "all_rating_rows_complete",
    "all_question_observation_rows_complete",
    "rating_question_case_ref_sets_match",
    "rating_question_consistency_guard_ready",
    "disposal_status",
    "disposal_verified",
    "body_removed",
    "reviewer_forms_removed",
    "reviewer_notes_removed",
    "local_packet_exported",
    "content_hash_of_body_stored",
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
    "plan_candidate_flag_counts",
    "red_count",
    "repair_required_count",
    "yellow_count",
    "pass_count",
    "boundary_violation_blocker_count",
    "creepy_or_surveillance_blocker_count",
    "overclaim_blocker_count",
    "self_blame_amplification_blocker_count",
    "p5_surface_or_gate_repair_observation_count",
    "emlis_readfeel_repair_observation_count",
    "p5_confirmed_requirements_met_by_summary",
    "p5_repair_return_indicators_present",
    "p5_review_inconclusive_indicators_present",
    "r49_wildcard_bulk_timeout_unclassified",
    "r49_wildcard_green_claim_allowed",
    "wildcard_timeout_does_not_block_summary_by_itself",
    "body_free_summary_contains_only_counts_and_refs",
    "question_text_included_allowed",
    "draft_question_text_included_allowed",
    "reviewer_free_text_included_allowed",
    "raw_input_allowed",
    "returned_surface_allowed",
    "local_path_allowed",
    "body_hash_allowed",
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
    "r0_current_source_r50_handoff_refrozen",
    "r1_validation_evidence_r49_timeout_handling_frozen",
    "r2_local_root_explicit_allow_purge_plan_preflight_built",
    "r3_actual_review_session_envelope_created",
    "r4_24_case_manifest_freeze_built",
    "r5_local_only_body_full_packet_generation_request_built",
    "r6_body_full_packet_completeness_export_denylist_scan_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_actual_human_review_run_recorded",
    "r9_rating_row_normalizer_built",
    "r10_readfeel_blocker_execution_blocker_ingestion_built",
    "r11_question_need_observation_row_normalizer_built",
    "r12_rating_question_observation_consistency_guard_built",
    "r13_pause_abort_expiration_protocol_built",
    "r14_body_full_packet_reviewer_notes_purge_built",
    "r15_disposal_receipt_builder_verifier_built",
    "r16_body_free_post_review_summary_builder_built",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r51_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R51_R0_R1_FALSE_KEY_REFS,
)

P7_R51_P5_DECISION_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "review_session_status",
    "r16_post_review_summary_schema_version",
    "r16_post_review_summary_ref",
    "post_review_summary_status",
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
    "r0_current_source_r50_handoff_refrozen",
    "r1_validation_evidence_r49_timeout_handling_frozen",
    "r2_local_root_explicit_allow_purge_plan_preflight_built",
    "r3_actual_review_session_envelope_created",
    "r4_24_case_manifest_freeze_built",
    "r5_local_only_body_full_packet_generation_request_built",
    "r6_body_full_packet_completeness_export_denylist_scan_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_actual_human_review_run_recorded",
    "r9_rating_row_normalizer_built",
    "r10_readfeel_blocker_execution_blocker_ingestion_built",
    "r11_question_need_observation_row_normalizer_built",
    "r12_rating_question_observation_consistency_guard_built",
    "r13_pause_abort_expiration_protocol_built",
    "r14_body_full_packet_reviewer_notes_purge_built",
    "r15_disposal_receipt_builder_verifier_built",
    "r16_body_free_post_review_summary_builder_built",
    "r17_p5_confirmed_repair_return_inconclusive_decision_built",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r51_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R51_R0_R1_FALSE_KEY_REFS,
)


def _r51_count_identifier_list(values: Sequence[Any], *, allowed_refs: Sequence[str] | None = None) -> dict[str, int]:
    allowed = set(allowed_refs or ())
    counts: dict[str, int] = {}
    for value in values:
        ref = clean_identifier(value, default="", max_length=180)
        if not ref:
            continue
        if allowed and ref not in allowed:
            continue
        counts[ref] = counts.get(ref, 0) + 1
    return counts


def _r51_count_sequence_field(
    rows: Sequence[Mapping[str, Any]],
    field_ref: str,
    *,
    allowed_refs: Sequence[str] | None = None,
) -> dict[str, int]:
    values: list[Any] = []
    for row in rows:
        value = safe_mapping(row).get(field_ref)
        if isinstance(value, (list, tuple, set)):
            values.extend(value)
        elif value is not None:
            values.append(value)
    return _r51_count_identifier_list(values, allowed_refs=allowed_refs)


def _r51_axis_score_averages(rating_rows: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    averages: dict[str, float] = {}
    for axis in P5_HUMAN_BLIND_QA_RATING_AXES:
        values: list[float] = []
        for row in rating_rows:
            scores = safe_mapping(safe_mapping(row).get("axis_scores"))
            try:
                values.append(float(scores.get(axis)))
            except (TypeError, ValueError):
                continue
        averages[axis] = round(sum(values) / len(values), 4) if values else 0.0
    return averages


def _r51_axis_target_met_refs(averages: Mapping[str, Any]) -> tuple[list[str], list[str], bool]:
    met: list[str] = []
    missed: list[str] = []
    targets = safe_mapping(P5_HUMAN_BLIND_QA_TARGETS)
    for axis in P5_HUMAN_BLIND_QA_RATING_AXES:
        try:
            actual = float(averages.get(axis, 0.0))
        except (TypeError, ValueError):
            actual = 0.0
        try:
            target = float(targets.get(axis, 1.0))
        except (TypeError, ValueError):
            target = 1.0
        if actual >= target:
            met.append(axis)
        else:
            missed.append(axis)
    return met, missed, not missed


def _r51_repair_observation_count(primary_counts: Mapping[str, int]) -> int:
    return sum(int(primary_counts.get(ref, 0)) for ref in P7_R51_REPAIR_OBSERVATION_PRIMARY_CLASS_REFS)


def _r51_critical_repair_blocker_count(blocker_counts: Mapping[str, int]) -> int:
    return sum(int(blocker_counts.get(ref, 0)) for ref in P7_R51_CRITICAL_REPAIR_BLOCKER_REFS)


def build_p7_r51_body_free_post_review_summary_builder_bodyfree(
    *,
    disposal_receipt_builder_verifier_bodyfree: Mapping[str, Any] | None = None,
    r15_disposal_receipt_builder_verifier_bodyfree: Mapping[str, Any] | None = None,
    rating_row_normalizer_bodyfree: Mapping[str, Any] | None = None,
    r9_rating_row_normalizer_bodyfree: Mapping[str, Any] | None = None,
    readfeel_blocker_execution_blocker_ingestion_bodyfree: Mapping[str, Any] | None = None,
    r10_readfeel_blocker_execution_blocker_ingestion_bodyfree: Mapping[str, Any] | None = None,
    question_need_observation_row_normalizer_bodyfree: Mapping[str, Any] | None = None,
    r11_question_need_observation_row_normalizer_bodyfree: Mapping[str, Any] | None = None,
    rating_question_observation_consistency_guard_bodyfree: Mapping[str, Any] | None = None,
    r12_rating_question_observation_consistency_guard_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r51_body_free_post_review_summary_builder_bodyfree",
) -> dict[str, Any]:
    """Build R51-16 body-free post-review summary from finalized rows and receipt."""

    if disposal_receipt_builder_verifier_bodyfree is not None and r15_disposal_receipt_builder_verifier_bodyfree is not None:
        raise ValueError("provide only one R51-15 disposal receipt verifier value")
    if rating_row_normalizer_bodyfree is not None and r9_rating_row_normalizer_bodyfree is not None:
        raise ValueError("provide only one R51-9 rating normalizer value")
    if readfeel_blocker_execution_blocker_ingestion_bodyfree is not None and r10_readfeel_blocker_execution_blocker_ingestion_bodyfree is not None:
        raise ValueError("provide only one R51-10 blocker ingestion value")
    if question_need_observation_row_normalizer_bodyfree is not None and r11_question_need_observation_row_normalizer_bodyfree is not None:
        raise ValueError("provide only one R51-11 question observation normalizer value")
    if rating_question_observation_consistency_guard_bodyfree is not None and r12_rating_question_observation_consistency_guard_bodyfree is not None:
        raise ValueError("provide only one R51-12 consistency guard value")

    r9 = safe_mapping(
        rating_row_normalizer_bodyfree
        if rating_row_normalizer_bodyfree is not None
        else r9_rating_row_normalizer_bodyfree
        if r9_rating_row_normalizer_bodyfree is not None
        else build_p7_r51_rating_row_normalizer_bodyfree()
    )
    assert_p7_r51_rating_row_normalizer_bodyfree_contract(r9)
    r10 = safe_mapping(
        readfeel_blocker_execution_blocker_ingestion_bodyfree
        if readfeel_blocker_execution_blocker_ingestion_bodyfree is not None
        else r10_readfeel_blocker_execution_blocker_ingestion_bodyfree
        if r10_readfeel_blocker_execution_blocker_ingestion_bodyfree is not None
        else build_p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree(rating_row_normalizer_bodyfree=r9)
    )
    assert_p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(r10)
    r11 = safe_mapping(
        question_need_observation_row_normalizer_bodyfree
        if question_need_observation_row_normalizer_bodyfree is not None
        else r11_question_need_observation_row_normalizer_bodyfree
        if r11_question_need_observation_row_normalizer_bodyfree is not None
        else build_p7_r51_question_need_observation_row_normalizer_bodyfree(readfeel_blocker_execution_blocker_ingestion_bodyfree=r10)
    )
    assert_p7_r51_question_need_observation_row_normalizer_bodyfree_contract(r11)
    r12 = safe_mapping(
        rating_question_observation_consistency_guard_bodyfree
        if rating_question_observation_consistency_guard_bodyfree is not None
        else r12_rating_question_observation_consistency_guard_bodyfree
        if r12_rating_question_observation_consistency_guard_bodyfree is not None
        else build_p7_r51_rating_question_observation_consistency_guard_bodyfree(
            r9_rating_row_normalizer_bodyfree=r9,
            r10_readfeel_blocker_execution_blocker_ingestion_bodyfree=r10,
            r11_question_need_observation_row_normalizer_bodyfree=r11,
        )
    )
    assert_p7_r51_rating_question_observation_consistency_guard_bodyfree_contract(r12)
    r15 = safe_mapping(
        disposal_receipt_builder_verifier_bodyfree
        if disposal_receipt_builder_verifier_bodyfree is not None
        else r15_disposal_receipt_builder_verifier_bodyfree
        if r15_disposal_receipt_builder_verifier_bodyfree is not None
        else build_p7_r51_disposal_receipt_builder_verifier_bodyfree()
    )
    assert_p7_r51_disposal_receipt_builder_verifier_bodyfree_contract(r15)

    rating_rows = [safe_mapping(row) for row in r9.get("rating_rows") or []]
    question_rows = [safe_mapping(row) for row in r11.get("question_need_observation_rows") or []]
    readfeel_rows = [safe_mapping(row) for row in r10.get("readfeel_blocker_rows") or []]
    execution_rows = [safe_mapping(row) for row in r10.get("execution_blocker_rows") or []]
    verdict_counts = _r51_count_identifier_list((row.get("verdict") for row in rating_rows), allowed_refs=P7_R50_RATING_VERDICT_REFS)
    axis_averages = _r51_axis_score_averages(rating_rows)
    axis_met, axis_missed, all_axis_targets_met = _r51_axis_target_met_refs(axis_averages)
    readfeel_blocker_counts = _r51_count_sequence_field(rating_rows, "blocker_ids", allowed_refs=P7_R48_READFEEL_BLOCKER_ID_REFS)
    if not readfeel_blocker_counts:
        readfeel_blocker_counts = dict(safe_mapping(r10.get("readfeel_blocker_counts")))
    execution_blocker_counts = dict(safe_mapping(r10.get("execution_blocker_counts")))
    question_primary_counts = _r51_count_identifier_list(
        (row.get("question_need_primary_class") for row in question_rows),
        allowed_refs=P7_R50_QUESTION_NEED_PRIMARY_CLASS_REFS,
    )
    ambiguity_counts = _r51_count_sequence_field(question_rows, "ambiguity_kind_refs", allowed_refs=P7_R50_AMBIGUITY_KIND_REFS)
    one_question_fit_counts = _r51_count_identifier_list(
        (row.get("one_question_fit_ref") for row in question_rows),
        allowed_refs=P7_R50_ONE_QUESTION_FIT_REFS,
    )
    repair_required_counts = _r51_count_sequence_field(question_rows, "repair_required_refs", allowed_refs=P7_R50_REPAIR_REQUIRED_REF_REFS)
    plan_candidate_counts = _r51_count_sequence_field(question_rows, "plan_candidate_flags", allowed_refs=P7_R50_PLAN_CANDIDATE_FLAG_REFS)

    r9_blockers = dedupe_identifiers(r9.get("execution_blocker_ids") or [], limit=20, max_length=140)
    r10_blockers = dedupe_identifiers(r10.get("execution_blocker_ids") or [], limit=20, max_length=140)
    r11_blockers = dedupe_identifiers(r11.get("execution_blocker_ids") or [], limit=20, max_length=140)
    r12_blockers = dedupe_identifiers(r12.get("execution_blocker_ids") or [], limit=20, max_length=140)
    r15_blockers = dedupe_identifiers(r15.get("execution_blocker_ids") or [], limit=20, max_length=140)
    blockers = dedupe_identifiers([*r9_blockers, *r10_blockers, *r11_blockers, *r12_blockers, *r15_blockers], limit=40, max_length=140)

    red_count = int(verdict_counts.get("RED", 0))
    repair_required_count = int(verdict_counts.get("REPAIR_REQUIRED", 0))
    yellow_count = int(verdict_counts.get("YELLOW", 0))
    pass_count = int(verdict_counts.get("PASS", 0))
    critical_repair_blocker_count = _r51_critical_repair_blocker_count(readfeel_blocker_counts)
    boundary_violation_blocker_count = sum(
        int(readfeel_blocker_counts.get(ref, 0))
        for ref in (
            "p5_free_tier_history_boundary_violation",
            "p5_low_information_history_overread",
            "p5_current_input_overridden_by_history",
            "p5_boundary_history_line_leak_suspected",
        )
    )
    p5_surface_or_gate_repair_observation_count = int(question_primary_counts.get("not_question_p5_surface_repair_required", 0)) + int(question_primary_counts.get("not_question_gate_boundary_required", 0))
    emlis_repair_observation_count = int(question_primary_counts.get("not_question_emlis_readfeel_repair_required", 0))
    repair_observation_count = _r51_repair_observation_count(question_primary_counts)

    rating_complete = len(rating_rows) == P7_R51_REQUIRED_CASE_COUNT and bool(r9.get("all_required_rating_rows_present"))
    question_complete = len(question_rows) == P7_R51_REQUIRED_CASE_COUNT and bool(r11.get("all_required_question_need_observation_rows_present"))
    case_sets_match = bool(r12.get("rating_question_case_ref_sets_match"))
    consistency_ready = r12.get("rating_question_consistency_guard_status") == "READY_FOR_PAUSE_ABORT_EXPIRATION_PROTOCOL"
    disposal_verified = r15.get("disposal_receipt_verifier_status") == "READY_FOR_BODY_FREE_POST_REVIEW_SUMMARY_BUILDER" and r15.get("disposal_verified") is True
    execution_open = _safe_non_negative_int(r10.get("open_execution_blocker_count")) + len(blockers)
    ready = bool(rating_complete and question_complete and case_sets_match and consistency_ready and disposal_verified and execution_open == 0)

    if not rating_complete:
        blockers = dedupe_identifiers([*blockers, "r51_rating_rows_incomplete"], limit=40, max_length=140)
    if not question_complete:
        blockers = dedupe_identifiers([*blockers, "r51_question_need_observation_rows_incomplete"], limit=40, max_length=140)
    if not consistency_ready or not case_sets_match:
        blockers = dedupe_identifiers([*blockers, "r51_rating_question_observation_inconsistent"], limit=40, max_length=140)
    if not disposal_verified:
        status_ref = clean_identifier(r15.get("disposal_status"), default="DISPOSAL_FAILED", max_length=80)
        blockers = dedupe_identifiers([*blockers, "r51_disposal_not_verified" if status_ref != "DISPOSAL_FAILED" else "r51_disposal_failed"], limit=40, max_length=140)
    unknown_blockers = sorted(set(blockers) - set(P7_R51_EXECUTION_BLOCKER_ID_REFS))
    if unknown_blockers:
        blockers = dedupe_identifiers([ref for ref in blockers if ref in P7_R51_EXECUTION_BLOCKER_ID_REFS], limit=40, max_length=140)

    repair_indicators = bool(
        red_count
        or repair_required_count
        or critical_repair_blocker_count
        or readfeel_blocker_counts
        or not all_axis_targets_met
        or repair_observation_count
    )
    inconclusive_indicators = bool(not ready or yellow_count or blockers)
    confirmed_requirements = bool(ready and not repair_indicators and not inconclusive_indicators and pass_count == P7_R51_REQUIRED_CASE_COUNT)
    actual_true_keys = (
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
    ) if ready else ()
    material = {
        **_false_flags(),
        "schema_version": P7_R51_BODY_FREE_POST_REVIEW_SUMMARY_BUILDER_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R51_STEP,
        "scope": P7_R51_SCOPE,
        "policy_kind": P7_R51_POLICY_KIND,
        "policy_section": "R51-16_body_free_post_review_summary_builder",
        "current_phase": "P7_Product_Quality_Runner",
        "material_id": clean_identifier(material_id, default="p7_r51_body_free_post_review_summary_builder_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r15.get("review_session_id") or r12.get("review_session_id") or r11.get("review_session_id"), default=P7_R51_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_session_status": "R51_BODY_FREE_POST_REVIEW_SUMMARY_READY" if ready else "R51_BODY_FREE_POST_REVIEW_SUMMARY_BLOCKED",
        "r15_disposal_receipt_builder_verifier_schema_version": P7_R51_DISPOSAL_RECEIPT_BUILDER_VERIFIER_SCHEMA_VERSION,
        "r15_disposal_receipt_builder_verifier_ref": clean_identifier(r15.get("material_id"), default="p7_r51_disposal_receipt_builder_verifier", max_length=180),
        "disposal_receipt_verifier_status": clean_identifier(r15.get("disposal_receipt_verifier_status"), default="BLOCKED_BY_R51_14_PURGE", max_length=160),
        "r9_rating_row_normalizer_schema_version": P7_R51_RATING_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION,
        "r9_rating_row_normalizer_ref": clean_identifier(r9.get("material_id"), default="p7_r51_rating_row_normalizer_bodyfree", max_length=180),
        "rating_row_normalizer_status": clean_identifier(r9.get("rating_row_normalizer_status"), default="BLOCKED_BY_RATING_ROW_VALIDATION", max_length=160),
        "r10_blocker_ingestion_schema_version": P7_R51_READFEEL_EXECUTION_BLOCKER_INGESTION_BODYFREE_SCHEMA_VERSION,
        "r10_blocker_ingestion_ref": clean_identifier(r10.get("material_id"), default="p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree", max_length=180),
        "blocker_ingestion_status": clean_identifier(r10.get("blocker_ingestion_status"), default="BLOCKED_BY_R51_9_RATING_ROW_NORMALIZER", max_length=160),
        "r11_question_observation_normalizer_schema_version": P7_R51_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION,
        "r11_question_observation_normalizer_ref": clean_identifier(r11.get("material_id"), default="p7_r51_question_need_observation_row_normalizer_bodyfree", max_length=180),
        "question_observation_normalizer_status": clean_identifier(r11.get("question_observation_normalizer_status"), default="BLOCKED_BY_QUESTION_OBSERVATION_ROW_VALIDATION", max_length=160),
        "r12_consistency_guard_schema_version": P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        "r12_consistency_guard_ref": clean_identifier(r12.get("material_id"), default="p7_r51_rating_question_observation_consistency_guard_bodyfree", max_length=180),
        "rating_question_consistency_guard_status": clean_identifier(r12.get("rating_question_consistency_guard_status"), default="BLOCKED_BY_RATING_QUESTION_OBSERVATION_INCONSISTENCY", max_length=160),
        "post_review_summary_status": "READY_FOR_P5_CONFIRMED_REPAIR_RETURN_INCONCLUSIVE_DECISION" if ready else "BLOCKED_BY_POST_REVIEW_SUMMARY_REQUIREMENTS",
        "post_review_summary_reason_refs": ["body_free_post_review_summary_ready"] if ready else dedupe_identifiers(blockers or ["r51_disposal_not_verified"], limit=40, max_length=160),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "review_session_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "rating_row_count": len(rating_rows),
        "question_observation_row_count": len(question_rows),
        "readfeel_blocker_row_count": len(readfeel_rows),
        "execution_blocker_row_count": len(execution_rows),
        "open_readfeel_blocker_count": _safe_non_negative_int(r10.get("open_readfeel_blocker_count")),
        "open_execution_blocker_count": _safe_non_negative_int(r10.get("open_execution_blocker_count")) + len(blockers),
        "all_24_cases_reviewed": len(rating_rows) == P7_R51_REQUIRED_CASE_COUNT and len(question_rows) == P7_R51_REQUIRED_CASE_COUNT,
        "all_rating_rows_complete": rating_complete,
        "all_question_observation_rows_complete": question_complete,
        "rating_question_case_ref_sets_match": case_sets_match,
        "rating_question_consistency_guard_ready": consistency_ready,
        "disposal_status": clean_identifier(r15.get("disposal_status"), default="DISPOSAL_FAILED", max_length=80),
        "disposal_verified": bool(disposal_verified),
        "body_removed": bool(r15.get("body_removed") is True),
        "reviewer_forms_removed": bool(r15.get("reviewer_forms_removed") is True),
        "reviewer_notes_removed": bool(r15.get("reviewer_notes_removed") is True),
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "verdict_counts": verdict_counts,
        "axis_score_averages": axis_averages,
        "axis_target_refs": dict(safe_mapping(P5_HUMAN_BLIND_QA_TARGETS)),
        "axis_target_met_refs": axis_met,
        "axis_target_missed_refs": axis_missed,
        "all_axis_targets_met": all_axis_targets_met,
        "readfeel_blocker_counts": readfeel_blocker_counts,
        "execution_blocker_counts": execution_blocker_counts,
        "question_need_primary_class_counts": question_primary_counts,
        "ambiguity_kind_counts": ambiguity_counts,
        "one_question_fit_counts": one_question_fit_counts,
        "repair_required_counts": repair_required_counts,
        "plan_candidate_flag_counts": plan_candidate_counts,
        "red_count": red_count,
        "repair_required_count": repair_required_count,
        "yellow_count": yellow_count,
        "pass_count": pass_count,
        "boundary_violation_blocker_count": boundary_violation_blocker_count,
        "creepy_or_surveillance_blocker_count": int(readfeel_blocker_counts.get("p5_history_creepy_or_surveillance_feeling", 0)),
        "overclaim_blocker_count": int(readfeel_blocker_counts.get("p5_history_scope_overclaim", 0)),
        "self_blame_amplification_blocker_count": int(readfeel_blocker_counts.get("p5_history_line_self_blame_amplification", 0)),
        "p5_surface_or_gate_repair_observation_count": p5_surface_or_gate_repair_observation_count,
        "emlis_readfeel_repair_observation_count": emlis_repair_observation_count,
        "p5_confirmed_requirements_met_by_summary": confirmed_requirements,
        "p5_repair_return_indicators_present": repair_indicators,
        "p5_review_inconclusive_indicators_present": inconclusive_indicators,
        "r49_wildcard_bulk_timeout_unclassified": True,
        "r49_wildcard_green_claim_allowed": False,
        "wildcard_timeout_does_not_block_summary_by_itself": True,
        "body_free_summary_contains_only_counts_and_refs": True,
        "question_text_included_allowed": False,
        "draft_question_text_included_allowed": False,
        "reviewer_free_text_included_allowed": False,
        "raw_input_allowed": False,
        "returned_surface_allowed": False,
        "local_path_allowed": False,
        "body_hash_allowed": False,
        "actual_disposal_run_here": bool(ready and r15.get("actual_disposal_run_here") is True),
        "disposal_receipt_materialized_here": bool(ready and r15.get("disposal_receipt_materialized_here") is True),
        "actual_disposal_receipt_materialized_here": bool(ready and r15.get("actual_disposal_receipt_materialized_here") is True),
        "post_review_summary_materialized_here": ready,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "actual_human_review_run_here": bool(ready and r12.get("actual_human_review_run_here") is True),
        "actual_manual_review_run_here": bool(ready and r12.get("actual_manual_review_run_here") is True),
        "actual_rating_rows_materialized_here": bool(ready and r12.get("actual_rating_rows_materialized_here") is True),
        "actual_blocker_rows_materialized_here": bool(ready and r12.get("actual_blocker_rows_materialized_here") is True),
        "actual_execution_blocker_rows_materialized_here": bool(ready and r12.get("actual_execution_blocker_rows_materialized_here") is True),
        "actual_question_need_observation_rows_materialized_here": bool(ready and r12.get("actual_question_need_observation_rows_materialized_here") is True),
        "actual_question_need_observation_summary_materialized_here": ready,
        "p5_actual_review_still_not_run": not ready,
        "p5_human_blind_qa_confirmed_candidate": False,
        "p5_repair_return_candidate": False,
        "p5_review_inconclusive": False,
        "p6_limited_human_readfeel_start_allowed_candidate": False,
        "p8_question_design_material_candidate": False,
        "r0_current_source_r50_handoff_refrozen": True,
        "r1_validation_evidence_r49_timeout_handling_frozen": True,
        "r2_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r3_actual_review_session_envelope_created": True,
        "r4_24_case_manifest_freeze_built": True,
        "r5_local_only_body_full_packet_generation_request_built": True,
        "r6_body_full_packet_completeness_export_denylist_scan_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": bool(ready and r12.get("r7_reviewer_instruction_rating_form_freeze_built")),
        "r8_actual_human_review_run_recorded": bool(ready and r12.get("r8_actual_human_review_run_recorded")),
        "r9_rating_row_normalizer_built": bool(ready and r12.get("r9_rating_row_normalizer_built")),
        "r10_readfeel_blocker_execution_blocker_ingestion_built": bool(ready and r12.get("r10_readfeel_blocker_execution_blocker_ingestion_built")),
        "r11_question_need_observation_row_normalizer_built": bool(ready and r12.get("r11_question_need_observation_row_normalizer_built")),
        "r12_rating_question_observation_consistency_guard_built": bool(ready and r12.get("r12_rating_question_observation_consistency_guard_built")),
        "r13_pause_abort_expiration_protocol_built": bool(ready and r15.get("r14_body_full_packet_reviewer_notes_purge_built")),
        "r14_body_full_packet_reviewer_notes_purge_built": bool(ready and r15.get("r14_body_full_packet_reviewer_notes_purge_built")),
        "r15_disposal_receipt_builder_verifier_built": bool(ready and r15.get("r15_disposal_receipt_builder_verifier_built")),
        "r16_body_free_post_review_summary_builder_built": ready,
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        "implemented_steps": list(P7_R51_R16_IMPLEMENTED_STEPS if ready else P7_R51_R15_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R51_R16_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R51_R15_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R51_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R51_R16_NEXT_REQUIRED_STEP_REF if ready else P7_R51_R16_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r51_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r51_body_free_post_review_summary_builder_bodyfree_contract(
        material,
        allowed_true_false_key_refs=actual_true_keys,
    )
    return material


def build_p7_r51_body_free_post_review_summary_builder(**kwargs: Any) -> dict[str, Any]:
    return build_p7_r51_body_free_post_review_summary_builder_bodyfree(**kwargs)


def assert_p7_r51_body_free_post_review_summary_builder_bodyfree_contract(
    summary: Mapping[str, Any],
    *,
    allowed_true_false_key_refs: Sequence[str] | None = None,
) -> bool:
    data = safe_mapping(summary)
    _assert_required_fields(
        data,
        required=P7_R51_BODY_FREE_POST_REVIEW_SUMMARY_BUILDER_BODYFREE_REQUIRED_FIELD_REFS,
        source="p7_r51_r16_body_free_post_review_summary_builder",
    )
    allowed = tuple(
        allowed_true_false_key_refs
        or (
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
        )
    )
    _assert_body_free_common_allowing(
        data,
        schema_version=P7_R51_BODY_FREE_POST_REVIEW_SUMMARY_BUILDER_SCHEMA_VERSION,
        source="p7_r51_r16_body_free_post_review_summary_builder",
        allowed_true_false_key_refs=allowed,
    )
    if data.get("policy_section") != "R51-16_body_free_post_review_summary_builder":
        raise ValueError("R51 R16 policy section changed")
    if data.get("post_review_summary_status") not in P7_R51_POST_REVIEW_SUMMARY_STATUS_REFS:
        raise ValueError("R51 R16 post-review summary status changed")
    for false_key in (
        "question_text_included_allowed",
        "draft_question_text_included_allowed",
        "reviewer_free_text_included_allowed",
        "raw_input_allowed",
        "returned_surface_allowed",
        "local_path_allowed",
        "body_hash_allowed",
        "local_packet_exported",
        "content_hash_of_body_stored",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
        "p5_human_blind_qa_confirmed_candidate",
        "p5_repair_return_candidate",
        "p5_review_inconclusive",
        "p6_limited_human_readfeel_start_allowed_candidate",
        "p8_question_design_material_candidate",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R51 R16 must keep {false_key}=False")
    if tuple(data.get("axis_score_averages") or {}) != P5_HUMAN_BLIND_QA_RATING_AXES:
        raise ValueError("R51 R16 axis averages must cover the P5 axes in order")
    if set(safe_mapping(data.get("axis_target_refs"))) != set(P5_HUMAN_BLIND_QA_RATING_AXES):
        raise ValueError("R51 R16 axis target refs changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R51 R16 open blockers must match execution blockers")
    unknown = sorted(set(blockers) - set(P7_R51_EXECUTION_BLOCKER_ID_REFS))
    if unknown:
        raise ValueError(f"R51 R16 execution blockers are not canonical: {unknown[:4]}")
    status = data.get("post_review_summary_status")
    if status == "READY_FOR_P5_CONFIRMED_REPAIR_RETURN_INCONCLUSIVE_DECISION":
        for true_key in (
            "disposal_verified",
            "body_removed",
            "reviewer_forms_removed",
            "reviewer_notes_removed",
            "all_24_cases_reviewed",
            "all_rating_rows_complete",
            "all_question_observation_rows_complete",
            "rating_question_case_ref_sets_match",
            "rating_question_consistency_guard_ready",
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
            "r16_body_free_post_review_summary_builder_built",
        ):
            if data.get(true_key) is not True:
                raise ValueError(f"R51 R16 ready summary must keep {true_key}=True")
        if data.get("execution_blocker_ids") != []:
            raise ValueError("R51 R16 ready summary must have no execution blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R51_R16_IMPLEMENTED_STEPS:
            raise ValueError("R51 R16 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R51_R16_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R51 R16 not-yet steps changed")
        if data.get("next_required_step") != P7_R51_R16_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R16 ready summary must point to R51-17")
    else:
        for false_key in (
            "disposal_verified",
            "post_review_summary_materialized_here",
            "actual_question_need_observation_summary_materialized_here",
            "r16_body_free_post_review_summary_builder_built",
            "p5_confirmed_requirements_met_by_summary",
        ):
            if data.get(false_key) is not False:
                raise ValueError(f"R51 R16 blocked summary must keep {false_key}=False")
        if data.get("next_required_step") != P7_R51_R16_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R16 blocked summary must point to summary resolution")
    return True


def build_p7_r51_p5_confirmed_repair_return_inconclusive_decision_bodyfree(
    *,
    body_free_post_review_summary_builder_bodyfree: Mapping[str, Any] | None = None,
    r16_body_free_post_review_summary_builder_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r51_p5_confirmed_repair_return_inconclusive_decision_bodyfree",
) -> dict[str, Any]:
    """Build R51-17 body-free P5 candidate / repair / inconclusive decision."""

    if body_free_post_review_summary_builder_bodyfree is not None and r16_body_free_post_review_summary_builder_bodyfree is not None:
        raise ValueError("provide only one R51-16 summary value")
    r16 = safe_mapping(
        body_free_post_review_summary_builder_bodyfree
        if body_free_post_review_summary_builder_bodyfree is not None
        else r16_body_free_post_review_summary_builder_bodyfree
        if r16_body_free_post_review_summary_builder_bodyfree is not None
        else build_p7_r51_body_free_post_review_summary_builder_bodyfree()
    )
    assert_p7_r51_body_free_post_review_summary_builder_bodyfree_contract(r16)

    verdict_counts = dict(safe_mapping(r16.get("verdict_counts")))
    axis_averages = dict(safe_mapping(r16.get("axis_score_averages")))
    axis_missed = dedupe_identifiers(r16.get("axis_target_missed_refs") or [], limit=20, max_length=160)
    readfeel_blocker_counts = dict(safe_mapping(r16.get("readfeel_blocker_counts")))
    execution_blocker_counts = dict(safe_mapping(r16.get("execution_blocker_counts")))
    question_primary_counts = dict(safe_mapping(r16.get("question_need_primary_class_counts")))
    repair_required_counts = dict(safe_mapping(r16.get("repair_required_counts")))
    red_count = _safe_non_negative_int(r16.get("red_count"))
    repair_required_count = _safe_non_negative_int(r16.get("repair_required_count"))
    yellow_count = _safe_non_negative_int(r16.get("yellow_count"))
    pass_count = _safe_non_negative_int(r16.get("pass_count"))
    critical_repair_blocker_count = _r51_critical_repair_blocker_count(readfeel_blocker_counts)
    repair_observation_count = _r51_repair_observation_count(question_primary_counts)
    open_execution_blockers = dedupe_identifiers(r16.get("open_execution_blocker_ids") or [], limit=40, max_length=140)
    r16_ready = r16.get("post_review_summary_status") == "READY_FOR_P5_CONFIRMED_REPAIR_RETURN_INCONCLUSIVE_DECISION"
    summary_complete = bool(
        r16_ready
        and r16.get("all_rating_rows_complete") is True
        and r16.get("all_question_observation_rows_complete") is True
        and r16.get("rating_question_case_ref_sets_match") is True
        and r16.get("disposal_verified") is True
        and r16.get("body_removed") is True
        and r16.get("reviewer_notes_removed") is True
        and not open_execution_blockers
    )
    repair_requirements_met = bool(
        summary_complete
        and (
            red_count
            or repair_required_count
            or critical_repair_blocker_count
            or readfeel_blocker_counts
            or axis_missed
            or repair_observation_count
        )
    )
    inconclusive_requirements_met = bool(not summary_complete or yellow_count)
    confirmed_requirements_met = bool(
        summary_complete
        and not repair_requirements_met
        and not inconclusive_requirements_met
        and pass_count == P7_R51_REQUIRED_CASE_COUNT
        and r16.get("all_axis_targets_met") is True
    )

    if confirmed_requirements_met:
        decision_status = "P5_CONFIRMED_CANDIDATE"
        reason_refs = ["p5_confirmed_candidate_requirements_met_bodyfree"]
        blocker_refs: list[str] = []
        next_step = P7_R51_R17_CONFIRMED_NEXT_REQUIRED_STEP_REF
    elif repair_requirements_met:
        decision_status = "P5_REPAIR_RETURN_CANDIDATE"
        reason_refs = dedupe_identifiers(
            [
                "p5_repair_return_indicators_present",
                *("red_verdict_present" for _ in range(1) if red_count),
                *("repair_required_verdict_present" for _ in range(1) if repair_required_count),
                *("critical_readfeel_blocker_present" for _ in range(1) if critical_repair_blocker_count),
                *("axis_target_missed" for _ in range(1) if axis_missed),
                *("not_question_repair_observation_present" for _ in range(1) if repair_observation_count),
            ],
            limit=20,
            max_length=160,
        )
        blocker_refs = dedupe_identifiers([*axis_missed, *readfeel_blocker_counts.keys()], limit=40, max_length=160)
        next_step = P7_R51_R17_REPAIR_RETURN_NEXT_REQUIRED_STEP_REF
    else:
        decision_status = "P5_REVIEW_INCONCLUSIVE"
        reason_refs = dedupe_identifiers(
            [
                "p5_review_inconclusive_requirements_met",
                *("post_review_summary_not_ready" for _ in range(1) if not r16_ready),
                *("execution_blocker_open" for _ in range(1) if open_execution_blockers),
                *("yellow_verdict_present" for _ in range(1) if yellow_count),
                *("disposal_not_verified" for _ in range(1) if r16.get("disposal_verified") is not True),
            ],
            limit=20,
            max_length=160,
        )
        blocker_refs = dedupe_identifiers(open_execution_blockers, limit=40, max_length=160)
        next_step = P7_R51_R17_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF

    actual_true_keys = (
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
    )
    decision = {
        **_false_flags(),
        "schema_version": P7_R51_P5_CONFIRMED_REPAIR_RETURN_INCONCLUSIVE_DECISION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R51_STEP,
        "scope": P7_R51_SCOPE,
        "policy_kind": P7_R51_POLICY_KIND,
        "policy_section": "R51-17_p5_confirmed_repair_return_inconclusive_decision",
        "current_phase": "P7_Product_Quality_Runner",
        "material_id": clean_identifier(material_id, default="p7_r51_p5_confirmed_repair_return_inconclusive_decision_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r16.get("review_session_id"), default=P7_R51_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_session_status": "R51_P5_DECISION_CANDIDATE_BUILT_BODYFREE",
        "r16_post_review_summary_schema_version": P7_R51_BODY_FREE_POST_REVIEW_SUMMARY_BUILDER_SCHEMA_VERSION,
        "r16_post_review_summary_ref": clean_identifier(r16.get("material_id"), default="p7_r51_body_free_post_review_summary_builder_bodyfree", max_length=180),
        "post_review_summary_status": clean_identifier(r16.get("post_review_summary_status"), default="BLOCKED_BY_POST_REVIEW_SUMMARY_REQUIREMENTS", max_length=160),
        "p5_decision_status": decision_status,
        "p5_decision_reason_refs": reason_refs,
        "p5_decision_blocker_refs": blocker_refs,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "rating_row_count": _safe_non_negative_int(r16.get("rating_row_count")),
        "question_observation_row_count": _safe_non_negative_int(r16.get("question_observation_row_count")),
        "open_execution_blocker_count": len(open_execution_blockers),
        "open_readfeel_blocker_count": _safe_non_negative_int(r16.get("open_readfeel_blocker_count")),
        "execution_blocker_ids": list(open_execution_blockers),
        "open_execution_blocker_ids": list(open_execution_blockers),
        "verdict_counts": verdict_counts,
        "axis_score_averages": axis_averages,
        "axis_target_refs": dict(safe_mapping(r16.get("axis_target_refs"))),
        "axis_target_met_refs": list(r16.get("axis_target_met_refs") or []),
        "axis_target_missed_refs": axis_missed,
        "all_axis_targets_met": bool(r16.get("all_axis_targets_met")),
        "readfeel_blocker_counts": readfeel_blocker_counts,
        "execution_blocker_counts": execution_blocker_counts,
        "question_need_primary_class_counts": question_primary_counts,
        "repair_required_counts": repair_required_counts,
        "red_count": red_count,
        "repair_required_count": repair_required_count,
        "yellow_count": yellow_count,
        "pass_count": pass_count,
        "critical_repair_blocker_count": critical_repair_blocker_count,
        "repair_observation_count": repair_observation_count,
        "disposal_verified": bool(r16.get("disposal_verified") is True),
        "body_removed": bool(r16.get("body_removed") is True),
        "reviewer_notes_removed": bool(r16.get("reviewer_notes_removed") is True),
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "p5_confirmed_candidate_requirements_met": confirmed_requirements_met,
        "p5_repair_return_requirements_met": repair_requirements_met,
        "p5_review_inconclusive_requirements_met": decision_status == "P5_REVIEW_INCONCLUSIVE",
        "p5_decision_candidate_only": True,
        "p5_human_blind_qa_confirmed": False,
        "p5_human_blind_qa_confirmed_candidate": decision_status == "P5_CONFIRMED_CANDIDATE",
        "p5_repair_return_candidate": decision_status == "P5_REPAIR_RETURN_CANDIDATE",
        "p5_review_inconclusive": decision_status == "P5_REVIEW_INCONCLUSIVE",
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_start_allowed_candidate": False,
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
        "actual_human_review_run_here": bool(r16.get("actual_human_review_run_here")),
        "actual_manual_review_run_here": bool(r16.get("actual_manual_review_run_here")),
        "actual_rating_rows_materialized_here": bool(r16.get("actual_rating_rows_materialized_here")),
        "actual_blocker_rows_materialized_here": bool(r16.get("actual_blocker_rows_materialized_here")),
        "actual_execution_blocker_rows_materialized_here": bool(r16.get("actual_execution_blocker_rows_materialized_here")),
        "actual_question_need_observation_rows_materialized_here": bool(r16.get("actual_question_need_observation_rows_materialized_here")),
        "actual_question_need_observation_summary_materialized_here": bool(r16.get("actual_question_need_observation_summary_materialized_here")),
        "actual_disposal_run_here": bool(r16.get("actual_disposal_run_here")),
        "disposal_receipt_materialized_here": bool(r16.get("disposal_receipt_materialized_here")),
        "actual_disposal_receipt_materialized_here": bool(r16.get("actual_disposal_receipt_materialized_here")),
        "post_review_summary_materialized_here": bool(r16.get("post_review_summary_materialized_here")),
        "p5_actual_review_still_not_run": not summary_complete,
        "r0_current_source_r50_handoff_refrozen": True,
        "r1_validation_evidence_r49_timeout_handling_frozen": True,
        "r2_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r3_actual_review_session_envelope_created": True,
        "r4_24_case_manifest_freeze_built": True,
        "r5_local_only_body_full_packet_generation_request_built": True,
        "r6_body_full_packet_completeness_export_denylist_scan_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": bool(r16.get("r7_reviewer_instruction_rating_form_freeze_built")),
        "r8_actual_human_review_run_recorded": bool(r16.get("r8_actual_human_review_run_recorded")),
        "r9_rating_row_normalizer_built": bool(r16.get("r9_rating_row_normalizer_built")),
        "r10_readfeel_blocker_execution_blocker_ingestion_built": bool(r16.get("r10_readfeel_blocker_execution_blocker_ingestion_built")),
        "r11_question_need_observation_row_normalizer_built": bool(r16.get("r11_question_need_observation_row_normalizer_built")),
        "r12_rating_question_observation_consistency_guard_built": bool(r16.get("r12_rating_question_observation_consistency_guard_built")),
        "r13_pause_abort_expiration_protocol_built": bool(r16.get("r13_pause_abort_expiration_protocol_built")),
        "r14_body_full_packet_reviewer_notes_purge_built": bool(r16.get("r14_body_full_packet_reviewer_notes_purge_built")),
        "r15_disposal_receipt_builder_verifier_built": bool(r16.get("r15_disposal_receipt_builder_verifier_built")),
        "r16_body_free_post_review_summary_builder_built": bool(r16.get("r16_body_free_post_review_summary_builder_built")),
        "r17_p5_confirmed_repair_return_inconclusive_decision_built": True,
        "implemented_steps": list(P7_R51_R17_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R51_R17_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R51_FIRST_NEXT_WORK_REF,
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "r51_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r51_p5_confirmed_repair_return_inconclusive_decision_bodyfree_contract(
        decision,
        allowed_true_false_key_refs=actual_true_keys,
    )
    return decision


def build_p7_r51_p5_confirmed_repair_return_inconclusive_decision(**kwargs: Any) -> dict[str, Any]:
    return build_p7_r51_p5_confirmed_repair_return_inconclusive_decision_bodyfree(**kwargs)


def assert_p7_r51_p5_confirmed_repair_return_inconclusive_decision_bodyfree_contract(
    decision: Mapping[str, Any],
    *,
    allowed_true_false_key_refs: Sequence[str] | None = None,
) -> bool:
    data = safe_mapping(decision)
    _assert_required_fields(
        data,
        required=P7_R51_P5_DECISION_BODYFREE_REQUIRED_FIELD_REFS,
        source="p7_r51_r17_p5_confirmed_repair_return_inconclusive_decision",
    )
    allowed = tuple(
        allowed_true_false_key_refs
        or (
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
        )
    )
    _assert_body_free_common_allowing(
        data,
        schema_version=P7_R51_P5_CONFIRMED_REPAIR_RETURN_INCONCLUSIVE_DECISION_SCHEMA_VERSION,
        source="p7_r51_r17_p5_confirmed_repair_return_inconclusive_decision",
        allowed_true_false_key_refs=allowed,
    )
    if data.get("policy_section") != "R51-17_p5_confirmed_repair_return_inconclusive_decision":
        raise ValueError("R51 R17 policy section changed")
    if data.get("p5_decision_status") not in P7_R51_P5_DECISION_STATUS_REFS:
        raise ValueError("R51 R17 decision status changed")
    for false_key in (
        "p5_human_blind_qa_confirmed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_limited_human_readfeel_start_allowed_candidate",
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
            raise ValueError(f"R51 R17 must keep {false_key}=False")
    true_candidate_count = sum(
        1
        for key in ("p5_human_blind_qa_confirmed_candidate", "p5_repair_return_candidate", "p5_review_inconclusive")
        if data.get(key) is True
    )
    if true_candidate_count != 1:
        raise ValueError("R51 R17 must set exactly one P5 candidate/repair/inconclusive flag")
    status = data.get("p5_decision_status")
    if status == "P5_CONFIRMED_CANDIDATE":
        if data.get("p5_human_blind_qa_confirmed_candidate") is not True:
            raise ValueError("R51 R17 confirmed candidate status must set confirmed candidate flag")
        if data.get("p5_confirmed_candidate_requirements_met") is not True:
            raise ValueError("R51 R17 confirmed candidate must meet candidate requirements")
        if data.get("next_required_step") != P7_R51_R17_CONFIRMED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R17 confirmed candidate must point to R51-18 candidate handoff")
    elif status == "P5_REPAIR_RETURN_CANDIDATE":
        if data.get("p5_repair_return_candidate") is not True:
            raise ValueError("R51 R17 repair return status must set repair candidate flag")
        if data.get("p5_repair_return_requirements_met") is not True:
            raise ValueError("R51 R17 repair return must have repair requirements")
        if data.get("next_required_step") != P7_R51_R17_REPAIR_RETURN_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R17 repair return must point back to P5 repair")
    else:
        if data.get("p5_review_inconclusive") is not True:
            raise ValueError("R51 R17 inconclusive status must set inconclusive flag")
        if data.get("p5_review_inconclusive_requirements_met") is not True:
            raise ValueError("R51 R17 inconclusive must have inconclusive requirements")
        if data.get("next_required_step") != P7_R51_R17_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R17 inconclusive must point to inconclusive resolution")
    if tuple(data.get("implemented_steps") or ()) != P7_R51_R17_IMPLEMENTED_STEPS:
        raise ValueError("R51 R17 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R51_R17_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R51 R17 not-yet steps changed")
    return True


# ---------------------------------------------------------------------------
# R51-18 / R51-19: P6 and P8 candidate handoff materials.
# ---------------------------------------------------------------------------

P7_R51_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r51.p6_limited_human_readfeel_candidate_handoff.bodyfree.v1"
)
P7_R51_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r51.p8_question_design_material_candidate_handoff.bodyfree.v1"
)

P7_R51_R18_NEXT_REQUIRED_STEP_REF: Final = "R51-19_p8_question_design_material_candidate_handoff"
P7_R51_R18_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R51-18_p6_candidate_handoff_before_R51-19_p8_material_handoff"
P7_R51_R19_NEXT_REQUIRED_STEP_REF: Final = "R51-20_no_body_leak_no_question_text_no_touch_boundary_validation"
P7_R51_R19_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R51-19_p8_question_design_material_candidate_before_R51-20_validation"

P7_R51_R18_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R51_R17_IMPLEMENTED_STEPS,
    "R51-18_p6_limited_human_readfeel_candidate_handoff",
)
P7_R51_R18_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R51_R17_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R51_R19_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R51_R18_IMPLEMENTED_STEPS,
    "R51-19_p8_question_design_material_candidate_handoff",
)
P7_R51_R19_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R51_R18_NOT_YET_IMPLEMENTED_STEPS[1:]

P7_R51_P6_CANDIDATE_HANDOFF_STATUS_REFS: Final[tuple[str, ...]] = (
    "P6_LIMITED_HUMAN_READFEEL_CANDIDATE_READY",
    "P6_LIMITED_HUMAN_READFEEL_CANDIDATE_BLOCKED_BY_P5_DECISION",
)
P7_R51_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_STATUS_REFS: Final[tuple[str, ...]] = (
    "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_READY",
    "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_BLOCKED_BY_P5_OR_BODYFREE_REQUIREMENTS",
)

P7_R51_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "review_session_status",
    "r17_p5_decision_schema_version",
    "r17_p5_decision_ref",
    "p5_decision_status",
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
    "r0_current_source_r50_handoff_refrozen",
    "r1_validation_evidence_r49_timeout_handling_frozen",
    "r2_local_root_explicit_allow_purge_plan_preflight_built",
    "r3_actual_review_session_envelope_created",
    "r4_24_case_manifest_freeze_built",
    "r5_local_only_body_full_packet_generation_request_built",
    "r6_body_full_packet_completeness_export_denylist_scan_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_actual_human_review_run_recorded",
    "r9_rating_row_normalizer_built",
    "r10_readfeel_blocker_execution_blocker_ingestion_built",
    "r11_question_need_observation_row_normalizer_built",
    "r12_rating_question_observation_consistency_guard_built",
    "r13_pause_abort_expiration_protocol_built",
    "r14_body_full_packet_reviewer_notes_purge_built",
    "r15_disposal_receipt_builder_verifier_built",
    "r16_body_free_post_review_summary_builder_built",
    "r17_p5_confirmed_repair_return_inconclusive_decision_built",
    "r18_p6_limited_human_readfeel_candidate_handoff_built",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r51_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R51_R0_R1_FALSE_KEY_REFS,
)

P7_R51_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "review_session_status",
    "r18_p6_candidate_handoff_schema_version",
    "r18_p6_candidate_handoff_ref",
    "p6_candidate_handoff_status",
    "r16_post_review_summary_schema_version",
    "r16_post_review_summary_ref",
    "post_review_summary_status",
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
    "question_implementation_not_started",
    "p8_question_design_material_candidate_requirements_met",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_repair_return_candidate",
    "p5_review_inconclusive",
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
    "r0_current_source_r50_handoff_refrozen",
    "r1_validation_evidence_r49_timeout_handling_frozen",
    "r2_local_root_explicit_allow_purge_plan_preflight_built",
    "r3_actual_review_session_envelope_created",
    "r4_24_case_manifest_freeze_built",
    "r5_local_only_body_full_packet_generation_request_built",
    "r6_body_full_packet_completeness_export_denylist_scan_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_actual_human_review_run_recorded",
    "r9_rating_row_normalizer_built",
    "r10_readfeel_blocker_execution_blocker_ingestion_built",
    "r11_question_need_observation_row_normalizer_built",
    "r12_rating_question_observation_consistency_guard_built",
    "r13_pause_abort_expiration_protocol_built",
    "r14_body_full_packet_reviewer_notes_purge_built",
    "r15_disposal_receipt_builder_verifier_built",
    "r16_body_free_post_review_summary_builder_built",
    "r17_p5_confirmed_repair_return_inconclusive_decision_built",
    "r18_p6_limited_human_readfeel_candidate_handoff_built",
    "r19_p8_question_design_material_candidate_handoff_built",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r51_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R51_R0_R1_FALSE_KEY_REFS,
)


def _r51_bodyfree_actual_material_allowed_true_refs(*, include_p6_candidate: bool = False, include_p8_candidate: bool = False) -> tuple[str, ...]:
    refs = [
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
    ]
    if include_p6_candidate:
        refs.append("p6_limited_human_readfeel_start_allowed_candidate")
    if include_p8_candidate:
        refs.append("p8_question_design_material_candidate")
    return tuple(refs)


def build_p7_r51_p6_limited_human_readfeel_candidate_handoff_bodyfree(
    *,
    p5_confirmed_repair_return_inconclusive_decision_bodyfree: Mapping[str, Any] | None = None,
    r17_p5_confirmed_repair_return_inconclusive_decision_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r51_p6_limited_human_readfeel_candidate_handoff_bodyfree",
) -> dict[str, Any]:
    """Build R51-18 body-free P6 limited human readfeel candidate handoff."""

    if p5_confirmed_repair_return_inconclusive_decision_bodyfree is not None and r17_p5_confirmed_repair_return_inconclusive_decision_bodyfree is not None:
        raise ValueError("provide only one R51-17 decision value")
    r17 = safe_mapping(
        p5_confirmed_repair_return_inconclusive_decision_bodyfree
        if p5_confirmed_repair_return_inconclusive_decision_bodyfree is not None
        else r17_p5_confirmed_repair_return_inconclusive_decision_bodyfree
        if r17_p5_confirmed_repair_return_inconclusive_decision_bodyfree is not None
        else build_p7_r51_p5_confirmed_repair_return_inconclusive_decision_bodyfree()
    )
    assert_p7_r51_p5_confirmed_repair_return_inconclusive_decision_bodyfree_contract(r17)

    open_execution_blockers = dedupe_identifiers(r17.get("open_execution_blocker_ids") or [], limit=40, max_length=140)
    p5_confirmed_candidate = bool(r17.get("p5_decision_status") == "P5_CONFIRMED_CANDIDATE" and r17.get("p5_human_blind_qa_confirmed_candidate") is True)
    no_repair_or_inconclusive = bool(r17.get("p5_repair_return_candidate") is False and r17.get("p5_review_inconclusive") is False)
    disposal_verified = bool(r17.get("disposal_verified") is True and r17.get("body_removed") is True and r17.get("reviewer_notes_removed") is True)
    rows_complete = bool(
        _safe_non_negative_int(r17.get("rating_row_count")) == P7_R51_REQUIRED_CASE_COUNT
        and _safe_non_negative_int(r17.get("question_observation_row_count")) == P7_R51_REQUIRED_CASE_COUNT
    )
    no_open_blockers = not open_execution_blockers and _safe_non_negative_int(r17.get("open_execution_blocker_count")) == 0
    all_axis_targets_met = bool(r17.get("all_axis_targets_met") is True)
    no_yellow = _safe_non_negative_int(r17.get("yellow_count")) == 0
    no_red_or_repair = _safe_non_negative_int(r17.get("red_count")) == 0 and _safe_non_negative_int(r17.get("repair_required_count")) == 0
    no_repair_observation = _safe_non_negative_int(r17.get("repair_observation_count")) == 0
    no_critical_repair_blocker = _safe_non_negative_int(r17.get("critical_repair_blocker_count")) == 0
    p6_candidate_requirements_met = bool(
        p5_confirmed_candidate
        and no_repair_or_inconclusive
        and disposal_verified
        and rows_complete
        and no_open_blockers
        and all_axis_targets_met
        and no_yellow
        and no_red_or_repair
        and no_repair_observation
        and no_critical_repair_blocker
    )

    missing_requirement_refs = dedupe_identifiers(
        [
            *([] if p5_confirmed_candidate else ["p5_confirmed_candidate_required"]),
            *([] if no_repair_or_inconclusive else ["p5_repair_or_inconclusive_must_be_resolved_before_p6_candidate"]),
            *([] if disposal_verified else ["disposal_verified_required"]),
            *([] if rows_complete else ["complete_24_case_rating_and_question_observation_rows_required"]),
            *([] if no_open_blockers else ["open_execution_blockers_must_be_zero"]),
            *([] if all_axis_targets_met else ["all_axis_targets_must_be_met"]),
            *([] if no_yellow else ["yellow_verdict_must_be_resolved_before_p6_candidate"]),
            *([] if no_red_or_repair else ["red_or_repair_required_must_be_zero"]),
            *([] if no_repair_observation else ["not_question_repair_observations_must_be_zero"]),
            *([] if no_critical_repair_blocker else ["critical_readfeel_blockers_must_be_zero"]),
        ],
        limit=40,
        max_length=160,
    )
    status = "P6_LIMITED_HUMAN_READFEEL_CANDIDATE_READY" if p6_candidate_requirements_met else "P6_LIMITED_HUMAN_READFEEL_CANDIDATE_BLOCKED_BY_P5_DECISION"
    reason_refs = ["p6_limited_human_readfeel_candidate_requirements_met_bodyfree"] if p6_candidate_requirements_met else ["p6_candidate_blocked_until_p5_decision_is_confirmed_without_repair_or_inconclusive"]
    blocker_refs = [] if p6_candidate_requirements_met else missing_requirement_refs
    next_step = P7_R51_R18_NEXT_REQUIRED_STEP_REF if p6_candidate_requirements_met else P7_R51_R18_BLOCKED_NEXT_REQUIRED_STEP_REF

    actual_true_keys = _r51_bodyfree_actual_material_allowed_true_refs(
        include_p6_candidate=p6_candidate_requirements_met,
        include_p8_candidate=False,
    )
    handoff = {
        **_false_flags(),
        "schema_version": P7_R51_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R51_STEP,
        "scope": P7_R51_SCOPE,
        "policy_kind": P7_R51_POLICY_KIND,
        "policy_section": "R51-18_p6_limited_human_readfeel_candidate_handoff",
        "current_phase": "P7_Product_Quality_Runner",
        "material_id": clean_identifier(material_id, default="p7_r51_p6_limited_human_readfeel_candidate_handoff_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r17.get("review_session_id"), default=P7_R51_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_session_status": "R51_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_BUILT_BODYFREE",
        "r17_p5_decision_schema_version": P7_R51_P5_CONFIRMED_REPAIR_RETURN_INCONCLUSIVE_DECISION_SCHEMA_VERSION,
        "r17_p5_decision_ref": clean_identifier(r17.get("material_id"), default="p7_r51_p5_confirmed_repair_return_inconclusive_decision_bodyfree", max_length=180),
        "p5_decision_status": clean_identifier(r17.get("p5_decision_status"), default="P5_REVIEW_INCONCLUSIVE", max_length=120),
        "p6_candidate_handoff_status": status,
        "p6_candidate_reason_refs": reason_refs,
        "p6_candidate_blocker_refs": blocker_refs,
        "missing_requirement_refs": missing_requirement_refs,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "rating_row_count": _safe_non_negative_int(r17.get("rating_row_count")),
        "question_observation_row_count": _safe_non_negative_int(r17.get("question_observation_row_count")),
        "open_execution_blocker_count": len(open_execution_blockers),
        "open_readfeel_blocker_count": _safe_non_negative_int(r17.get("open_readfeel_blocker_count")),
        "execution_blocker_ids": list(open_execution_blockers),
        "open_execution_blocker_ids": list(open_execution_blockers),
        "p5_human_blind_qa_confirmed_candidate": bool(r17.get("p5_human_blind_qa_confirmed_candidate")),
        "p5_repair_return_candidate": bool(r17.get("p5_repair_return_candidate")),
        "p5_review_inconclusive": bool(r17.get("p5_review_inconclusive")),
        "p5_decision_candidate_only": bool(r17.get("p5_decision_candidate_only")),
        "p5_weakness_not_hidden_by_p6": p6_candidate_requirements_met,
        "p5_repair_not_compensated_by_p6": p6_candidate_requirements_met,
        "p6_limited_family_scope_only": True,
        "p6_candidate_uses_bodyfree_summary_only": True,
        "p6_limited_human_readfeel_start_candidate_requirements_met": p6_candidate_requirements_met,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_start_allowed_candidate": p6_candidate_requirements_met,
        "p8_question_design_material_candidate": False,
        "disposal_verified": bool(r17.get("disposal_verified")),
        "body_removed": bool(r17.get("body_removed")),
        "reviewer_notes_removed": bool(r17.get("reviewer_notes_removed")),
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "red_count": _safe_non_negative_int(r17.get("red_count")),
        "repair_required_count": _safe_non_negative_int(r17.get("repair_required_count")),
        "yellow_count": _safe_non_negative_int(r17.get("yellow_count")),
        "pass_count": _safe_non_negative_int(r17.get("pass_count")),
        "critical_repair_blocker_count": _safe_non_negative_int(r17.get("critical_repair_blocker_count")),
        "repair_observation_count": _safe_non_negative_int(r17.get("repair_observation_count")),
        "axis_target_missed_refs": list(r17.get("axis_target_missed_refs") or []),
        "all_axis_targets_met": bool(r17.get("all_axis_targets_met")),
        "readfeel_blocker_counts": dict(safe_mapping(r17.get("readfeel_blocker_counts"))),
        "question_need_primary_class_counts": dict(safe_mapping(r17.get("question_need_primary_class_counts"))),
        "p5_actual_review_still_not_run": bool(r17.get("p5_actual_review_still_not_run")),
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
        "actual_human_review_run_here": bool(r17.get("actual_human_review_run_here")),
        "actual_manual_review_run_here": bool(r17.get("actual_manual_review_run_here")),
        "actual_rating_rows_materialized_here": bool(r17.get("actual_rating_rows_materialized_here")),
        "actual_blocker_rows_materialized_here": bool(r17.get("actual_blocker_rows_materialized_here")),
        "actual_execution_blocker_rows_materialized_here": bool(r17.get("actual_execution_blocker_rows_materialized_here")),
        "actual_question_need_observation_rows_materialized_here": bool(r17.get("actual_question_need_observation_rows_materialized_here")),
        "actual_question_need_observation_summary_materialized_here": bool(r17.get("actual_question_need_observation_summary_materialized_here")),
        "actual_disposal_run_here": bool(r17.get("actual_disposal_run_here")),
        "disposal_receipt_materialized_here": bool(r17.get("disposal_receipt_materialized_here")),
        "actual_disposal_receipt_materialized_here": bool(r17.get("actual_disposal_receipt_materialized_here")),
        "post_review_summary_materialized_here": bool(r17.get("post_review_summary_materialized_here")),
        "r0_current_source_r50_handoff_refrozen": True,
        "r1_validation_evidence_r49_timeout_handling_frozen": True,
        "r2_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r3_actual_review_session_envelope_created": True,
        "r4_24_case_manifest_freeze_built": True,
        "r5_local_only_body_full_packet_generation_request_built": True,
        "r6_body_full_packet_completeness_export_denylist_scan_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": bool(r17.get("r7_reviewer_instruction_rating_form_freeze_built")),
        "r8_actual_human_review_run_recorded": bool(r17.get("r8_actual_human_review_run_recorded")),
        "r9_rating_row_normalizer_built": bool(r17.get("r9_rating_row_normalizer_built")),
        "r10_readfeel_blocker_execution_blocker_ingestion_built": bool(r17.get("r10_readfeel_blocker_execution_blocker_ingestion_built")),
        "r11_question_need_observation_row_normalizer_built": bool(r17.get("r11_question_need_observation_row_normalizer_built")),
        "r12_rating_question_observation_consistency_guard_built": bool(r17.get("r12_rating_question_observation_consistency_guard_built")),
        "r13_pause_abort_expiration_protocol_built": bool(r17.get("r13_pause_abort_expiration_protocol_built")),
        "r14_body_full_packet_reviewer_notes_purge_built": bool(r17.get("r14_body_full_packet_reviewer_notes_purge_built")),
        "r15_disposal_receipt_builder_verifier_built": bool(r17.get("r15_disposal_receipt_builder_verifier_built")),
        "r16_body_free_post_review_summary_builder_built": bool(r17.get("r16_body_free_post_review_summary_builder_built")),
        "r17_p5_confirmed_repair_return_inconclusive_decision_built": True,
        "r18_p6_limited_human_readfeel_candidate_handoff_built": True,
        "implemented_steps": list(P7_R51_R18_IMPLEMENTED_STEPS if p6_candidate_requirements_met else P7_R51_R17_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R51_R18_NOT_YET_IMPLEMENTED_STEPS if p6_candidate_requirements_met else P7_R51_R17_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R51_FIRST_NEXT_WORK_REF,
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "r51_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r51_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract(
        handoff,
        allowed_true_false_key_refs=actual_true_keys,
    )
    return handoff


def build_p7_r51_p6_limited_human_readfeel_candidate_handoff(**kwargs: Any) -> dict[str, Any]:
    return build_p7_r51_p6_limited_human_readfeel_candidate_handoff_bodyfree(**kwargs)


def assert_p7_r51_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract(
    handoff: Mapping[str, Any],
    *,
    allowed_true_false_key_refs: Sequence[str] | None = None,
) -> bool:
    data = safe_mapping(handoff)
    _assert_required_fields(
        data,
        required=P7_R51_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_BODYFREE_REQUIRED_FIELD_REFS,
        source="p7_r51_r18_p6_limited_human_readfeel_candidate_handoff",
    )
    allowed = tuple(
        allowed_true_false_key_refs
        or _r51_bodyfree_actual_material_allowed_true_refs(
            include_p6_candidate=bool(data.get("p6_limited_human_readfeel_start_allowed_candidate")),
            include_p8_candidate=False,
        )
    )
    _assert_body_free_common_allowing(
        data,
        schema_version=P7_R51_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        source="p7_r51_r18_p6_limited_human_readfeel_candidate_handoff",
        allowed_true_false_key_refs=allowed,
    )
    if data.get("policy_section") != "R51-18_p6_limited_human_readfeel_candidate_handoff":
        raise ValueError("R51 R18 policy section changed")
    if data.get("p6_candidate_handoff_status") not in P7_R51_P6_CANDIDATE_HANDOFF_STATUS_REFS:
        raise ValueError("R51 R18 P6 candidate handoff status changed")
    if data.get("p6_limited_human_readfeel_start_allowed") is not False:
        raise ValueError("R51 R18 must not allow P6 start")
    for false_key in (
        "p5_human_blind_qa_confirmed",
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
            raise ValueError(f"R51 R18 must keep {false_key}=False")
    blockers = dedupe_identifiers(data.get("open_execution_blocker_ids") or [], limit=40, max_length=140)
    if data.get("execution_blocker_ids") != blockers:
        raise ValueError("R51 R18 execution blockers must match open blockers")
    if data.get("open_execution_blocker_count") != len(blockers):
        raise ValueError("R51 R18 open execution blocker count changed")
    status = data.get("p6_candidate_handoff_status")
    if status == "P6_LIMITED_HUMAN_READFEEL_CANDIDATE_READY":
        for true_key in (
            "p5_human_blind_qa_confirmed_candidate",
            "p5_decision_candidate_only",
            "p5_weakness_not_hidden_by_p6",
            "p5_repair_not_compensated_by_p6",
            "p6_limited_family_scope_only",
            "p6_candidate_uses_bodyfree_summary_only",
            "p6_limited_human_readfeel_start_candidate_requirements_met",
            "p6_limited_human_readfeel_start_allowed_candidate",
            "disposal_verified",
            "body_removed",
            "reviewer_notes_removed",
            "all_axis_targets_met",
            "r18_p6_limited_human_readfeel_candidate_handoff_built",
        ):
            if data.get(true_key) is not True:
                raise ValueError(f"R51 R18 ready handoff must keep {true_key}=True")
        if data.get("p5_repair_return_candidate") is not False or data.get("p5_review_inconclusive") is not False:
            raise ValueError("R51 R18 ready handoff must not have P5 repair/inconclusive")
        if data.get("missing_requirement_refs"):
            raise ValueError("R51 R18 ready handoff must not have missing requirements")
        if tuple(data.get("implemented_steps") or ()) != P7_R51_R18_IMPLEMENTED_STEPS:
            raise ValueError("R51 R18 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R51_R18_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R51 R18 not-yet steps changed")
        if data.get("next_required_step") != P7_R51_R18_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R18 ready handoff must point to R51-19")
    else:
        if data.get("p6_limited_human_readfeel_start_allowed_candidate") is not False:
            raise ValueError("R51 R18 blocked handoff must not set P6 candidate")
        if not data.get("missing_requirement_refs"):
            raise ValueError("R51 R18 blocked handoff must explain missing requirements")
        if data.get("next_required_step") != P7_R51_R18_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R18 blocked handoff must point to R51-18 resolution")
    return True


def build_p7_r51_p8_question_design_material_candidate_handoff_bodyfree(
    *,
    p6_limited_human_readfeel_candidate_handoff_bodyfree: Mapping[str, Any] | None = None,
    r18_p6_limited_human_readfeel_candidate_handoff_bodyfree: Mapping[str, Any] | None = None,
    body_free_post_review_summary_builder_bodyfree: Mapping[str, Any] | None = None,
    r16_body_free_post_review_summary_builder_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r51_p8_question_design_material_candidate_handoff_bodyfree",
) -> dict[str, Any]:
    """Build R51-19 body-free P8 question design material candidate handoff."""

    if p6_limited_human_readfeel_candidate_handoff_bodyfree is not None and r18_p6_limited_human_readfeel_candidate_handoff_bodyfree is not None:
        raise ValueError("provide only one R51-18 handoff value")
    if body_free_post_review_summary_builder_bodyfree is not None and r16_body_free_post_review_summary_builder_bodyfree is not None:
        raise ValueError("provide only one R51-16 summary value")
    r18 = safe_mapping(
        p6_limited_human_readfeel_candidate_handoff_bodyfree
        if p6_limited_human_readfeel_candidate_handoff_bodyfree is not None
        else r18_p6_limited_human_readfeel_candidate_handoff_bodyfree
        if r18_p6_limited_human_readfeel_candidate_handoff_bodyfree is not None
        else build_p7_r51_p6_limited_human_readfeel_candidate_handoff_bodyfree()
    )
    assert_p7_r51_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract(r18)
    r16 = safe_mapping(
        body_free_post_review_summary_builder_bodyfree
        if body_free_post_review_summary_builder_bodyfree is not None
        else r16_body_free_post_review_summary_builder_bodyfree
        if r16_body_free_post_review_summary_builder_bodyfree is not None
        else {}
    )
    r16_provided = bool(r16)
    if r16_provided:
        assert_p7_r51_body_free_post_review_summary_builder_bodyfree_contract(r16)

    question_primary_counts = dict(safe_mapping(r16.get("question_need_primary_class_counts"))) if r16_provided else dict(safe_mapping(r18.get("question_need_primary_class_counts")))
    ambiguity_counts = dict(safe_mapping(r16.get("ambiguity_kind_counts"))) if r16_provided else {}
    one_question_counts = dict(safe_mapping(r16.get("one_question_fit_counts"))) if r16_provided else {}
    repair_required_counts = dict(safe_mapping(r16.get("repair_required_counts"))) if r16_provided else {}
    plan_candidate_flag_counts = dict(safe_mapping(r16.get("plan_candidate_flag_counts"))) if r16_provided else {}

    rows_complete = _safe_non_negative_int(r18.get("question_observation_row_count")) == P7_R51_REQUIRED_CASE_COUNT
    counts_available = bool(question_primary_counts and ambiguity_counts and one_question_counts and repair_required_counts)
    p5_not_repair_or_inconclusive = bool(r18.get("p5_repair_return_candidate") is False and r18.get("p5_review_inconclusive") is False)
    p5_confirmed_candidate = bool(r18.get("p5_human_blind_qa_confirmed_candidate") is True)
    p6_handoff_ready = r18.get("p6_candidate_handoff_status") == "P6_LIMITED_HUMAN_READFEEL_CANDIDATE_READY"
    repair_required_not_question_count = _r51_repair_observation_count(question_primary_counts)
    repair_required_not_question_clear = repair_required_not_question_count == 0
    no_local_or_body_risk = bool(
        r18.get("local_packet_exported") is False
        and r18.get("content_hash_of_body_stored") is False
        and r18.get("disposal_verified") is True
        and r18.get("body_removed") is True
        and r18.get("reviewer_notes_removed") is True
    )
    p8_candidate_requirements_met = bool(
        p5_confirmed_candidate
        and p5_not_repair_or_inconclusive
        and p6_handoff_ready
        and rows_complete
        and counts_available
        and repair_required_not_question_clear
        and no_local_or_body_risk
    )
    missing_requirement_refs = dedupe_identifiers(
        [
            *([] if p5_confirmed_candidate else ["p5_confirmed_candidate_required_for_p8_material"]),
            *([] if p5_not_repair_or_inconclusive else ["p5_repair_or_inconclusive_must_not_feed_p8_material"]),
            *([] if p6_handoff_ready else ["p6_candidate_handoff_must_be_ready_or_explicitly_resolved"]),
            *([] if rows_complete else ["complete_24_question_observation_rows_required"]),
            *([] if counts_available else ["bodyfree_question_observation_counts_required"]),
            *([] if repair_required_not_question_clear else ["repair_required_not_question_must_not_be_classified_as_p8_material"]),
            *([] if no_local_or_body_risk else ["disposal_and_bodyfree_boundary_required"]),
        ],
        limit=40,
        max_length=180,
    )
    status = "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_READY" if p8_candidate_requirements_met else "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_BLOCKED_BY_P5_OR_BODYFREE_REQUIREMENTS"
    reason_refs = ["p8_question_design_material_candidate_bodyfree_requirements_met"] if p8_candidate_requirements_met else ["p8_question_design_material_candidate_blocked_until_p5_and_bodyfree_material_are_clean"]
    blocker_refs = [] if p8_candidate_requirements_met else missing_requirement_refs
    next_step = P7_R51_R19_NEXT_REQUIRED_STEP_REF if p8_candidate_requirements_met else P7_R51_R19_BLOCKED_NEXT_REQUIRED_STEP_REF

    actual_true_keys = _r51_bodyfree_actual_material_allowed_true_refs(
        include_p6_candidate=bool(r18.get("p6_limited_human_readfeel_start_allowed_candidate")),
        include_p8_candidate=p8_candidate_requirements_met,
    )
    handoff = {
        **_false_flags(),
        "schema_version": P7_R51_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R51_STEP,
        "scope": P7_R51_SCOPE,
        "policy_kind": P7_R51_POLICY_KIND,
        "policy_section": "R51-19_p8_question_design_material_candidate_handoff",
        "current_phase": "P7_Product_Quality_Runner",
        "material_id": clean_identifier(material_id, default="p7_r51_p8_question_design_material_candidate_handoff_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r18.get("review_session_id"), default=P7_R51_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_session_status": "R51_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_BUILT_BODYFREE",
        "r18_p6_candidate_handoff_schema_version": P7_R51_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        "r18_p6_candidate_handoff_ref": clean_identifier(r18.get("material_id"), default="p7_r51_p6_limited_human_readfeel_candidate_handoff_bodyfree", max_length=180),
        "p6_candidate_handoff_status": clean_identifier(r18.get("p6_candidate_handoff_status"), default="P6_LIMITED_HUMAN_READFEEL_CANDIDATE_BLOCKED_BY_P5_DECISION", max_length=160),
        "r16_post_review_summary_schema_version": P7_R51_BODY_FREE_POST_REVIEW_SUMMARY_BUILDER_SCHEMA_VERSION if r16_provided else "not_provided_bodyfree_summary_required_for_ready_material",
        "r16_post_review_summary_ref": clean_identifier(r16.get("material_id"), default="missing_r16_body_free_post_review_summary", max_length=180),
        "post_review_summary_status": clean_identifier(r16.get("post_review_summary_status"), default="BLOCKED_BY_POST_REVIEW_SUMMARY_REQUIREMENTS", max_length=160),
        "p8_question_design_material_candidate_status": status,
        "p8_question_design_material_candidate_reason_refs": reason_refs,
        "p8_question_design_material_candidate_blocker_refs": blocker_refs,
        "missing_requirement_refs": missing_requirement_refs,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "rating_row_count": _safe_non_negative_int(r18.get("rating_row_count")),
        "question_observation_row_count": _safe_non_negative_int(r18.get("question_observation_row_count")),
        "question_need_primary_class_counts": question_primary_counts,
        "ambiguity_kind_counts": ambiguity_counts,
        "one_question_fit_counts": one_question_counts,
        "repair_required_counts": repair_required_counts,
        "plan_candidate_flag_counts": plan_candidate_flag_counts,
        "question_observation_rows_complete": rows_complete,
        "body_free_question_observation_material_available": counts_available,
        "question_text_absent": True,
        "draft_question_text_absent": True,
        "raw_input_absent": True,
        "returned_surface_absent": True,
        "reviewer_free_text_absent": True,
        "local_path_absent": True,
        "body_hash_absent": True,
        "repair_required_not_question_misclassified_as_p8_candidate": False,
        "p5_repair_return_material_mixed_into_p8_candidate": False,
        "question_implementation_not_started": True,
        "p8_question_design_material_candidate_requirements_met": p8_candidate_requirements_met,
        "p5_human_blind_qa_confirmed_candidate": bool(r18.get("p5_human_blind_qa_confirmed_candidate")),
        "p5_repair_return_candidate": bool(r18.get("p5_repair_return_candidate")),
        "p5_review_inconclusive": bool(r18.get("p5_review_inconclusive")),
        "p6_limited_human_readfeel_start_allowed_candidate": bool(r18.get("p6_limited_human_readfeel_start_allowed_candidate")),
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_question_design_material_candidate": p8_candidate_requirements_met,
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
        "actual_human_review_run_here": bool(r18.get("actual_human_review_run_here")),
        "actual_manual_review_run_here": bool(r18.get("actual_manual_review_run_here")),
        "actual_rating_rows_materialized_here": bool(r18.get("actual_rating_rows_materialized_here")),
        "actual_blocker_rows_materialized_here": bool(r18.get("actual_blocker_rows_materialized_here")),
        "actual_execution_blocker_rows_materialized_here": bool(r18.get("actual_execution_blocker_rows_materialized_here")),
        "actual_question_need_observation_rows_materialized_here": bool(r18.get("actual_question_need_observation_rows_materialized_here")),
        "actual_question_need_observation_summary_materialized_here": bool(r18.get("actual_question_need_observation_summary_materialized_here")),
        "actual_disposal_run_here": bool(r18.get("actual_disposal_run_here")),
        "disposal_receipt_materialized_here": bool(r18.get("disposal_receipt_materialized_here")),
        "actual_disposal_receipt_materialized_here": bool(r18.get("actual_disposal_receipt_materialized_here")),
        "post_review_summary_materialized_here": bool(r18.get("post_review_summary_materialized_here")),
        "p5_actual_review_still_not_run": bool(r18.get("p5_actual_review_still_not_run")),
        "r0_current_source_r50_handoff_refrozen": True,
        "r1_validation_evidence_r49_timeout_handling_frozen": True,
        "r2_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r3_actual_review_session_envelope_created": True,
        "r4_24_case_manifest_freeze_built": True,
        "r5_local_only_body_full_packet_generation_request_built": True,
        "r6_body_full_packet_completeness_export_denylist_scan_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": bool(r18.get("r7_reviewer_instruction_rating_form_freeze_built")),
        "r8_actual_human_review_run_recorded": bool(r18.get("r8_actual_human_review_run_recorded")),
        "r9_rating_row_normalizer_built": bool(r18.get("r9_rating_row_normalizer_built")),
        "r10_readfeel_blocker_execution_blocker_ingestion_built": bool(r18.get("r10_readfeel_blocker_execution_blocker_ingestion_built")),
        "r11_question_need_observation_row_normalizer_built": bool(r18.get("r11_question_need_observation_row_normalizer_built")),
        "r12_rating_question_observation_consistency_guard_built": bool(r18.get("r12_rating_question_observation_consistency_guard_built")),
        "r13_pause_abort_expiration_protocol_built": bool(r18.get("r13_pause_abort_expiration_protocol_built")),
        "r14_body_full_packet_reviewer_notes_purge_built": bool(r18.get("r14_body_full_packet_reviewer_notes_purge_built")),
        "r15_disposal_receipt_builder_verifier_built": bool(r18.get("r15_disposal_receipt_builder_verifier_built")),
        "r16_body_free_post_review_summary_builder_built": bool(r18.get("r16_body_free_post_review_summary_builder_built")),
        "r17_p5_confirmed_repair_return_inconclusive_decision_built": bool(r18.get("r17_p5_confirmed_repair_return_inconclusive_decision_built")),
        "r18_p6_limited_human_readfeel_candidate_handoff_built": bool(r18.get("r18_p6_limited_human_readfeel_candidate_handoff_built")),
        "r19_p8_question_design_material_candidate_handoff_built": True,
        "implemented_steps": list(P7_R51_R19_IMPLEMENTED_STEPS if p8_candidate_requirements_met else P7_R51_R18_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R51_R19_NOT_YET_IMPLEMENTED_STEPS if p8_candidate_requirements_met else P7_R51_R18_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R51_FIRST_NEXT_WORK_REF,
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "r51_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r51_p8_question_design_material_candidate_handoff_bodyfree_contract(
        handoff,
        allowed_true_false_key_refs=actual_true_keys,
    )
    return handoff


def build_p7_r51_p8_question_design_material_candidate_handoff(**kwargs: Any) -> dict[str, Any]:
    return build_p7_r51_p8_question_design_material_candidate_handoff_bodyfree(**kwargs)


def assert_p7_r51_p8_question_design_material_candidate_handoff_bodyfree_contract(
    handoff: Mapping[str, Any],
    *,
    allowed_true_false_key_refs: Sequence[str] | None = None,
) -> bool:
    data = safe_mapping(handoff)
    _assert_required_fields(
        data,
        required=P7_R51_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_BODYFREE_REQUIRED_FIELD_REFS,
        source="p7_r51_r19_p8_question_design_material_candidate_handoff",
    )
    allowed = tuple(
        allowed_true_false_key_refs
        or _r51_bodyfree_actual_material_allowed_true_refs(
            include_p6_candidate=bool(data.get("p6_limited_human_readfeel_start_allowed_candidate")),
            include_p8_candidate=bool(data.get("p8_question_design_material_candidate")),
        )
    )
    _assert_body_free_common_allowing(
        data,
        schema_version=P7_R51_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        source="p7_r51_r19_p8_question_design_material_candidate_handoff",
        allowed_true_false_key_refs=allowed,
    )
    if data.get("policy_section") != "R51-19_p8_question_design_material_candidate_handoff":
        raise ValueError("R51 R19 policy section changed")
    if data.get("p8_question_design_material_candidate_status") not in P7_R51_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_STATUS_REFS:
        raise ValueError("R51 R19 P8 material candidate status changed")
    for true_key in (
        "question_text_absent",
        "draft_question_text_absent",
        "raw_input_absent",
        "returned_surface_absent",
        "reviewer_free_text_absent",
        "local_path_absent",
        "body_hash_absent",
        "question_implementation_not_started",
        "r19_p8_question_design_material_candidate_handoff_built",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R51 R19 must keep {true_key}=True")
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
            raise ValueError(f"R51 R19 must keep {false_key}=False")
    status = data.get("p8_question_design_material_candidate_status")
    if status == "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_READY":
        for true_key in (
            "p5_human_blind_qa_confirmed_candidate",
            "p6_limited_human_readfeel_start_allowed_candidate",
            "question_observation_rows_complete",
            "body_free_question_observation_material_available",
            "p8_question_design_material_candidate_requirements_met",
            "p8_question_design_material_candidate",
        ):
            if data.get(true_key) is not True:
                raise ValueError(f"R51 R19 ready material must keep {true_key}=True")
        if data.get("p5_repair_return_candidate") is not False or data.get("p5_review_inconclusive") is not False:
            raise ValueError("R51 R19 ready material must not carry P5 repair or inconclusive")
        if data.get("missing_requirement_refs"):
            raise ValueError("R51 R19 ready material must not have missing requirements")
        if tuple(data.get("implemented_steps") or ()) != P7_R51_R19_IMPLEMENTED_STEPS:
            raise ValueError("R51 R19 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R51_R19_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R51 R19 not-yet steps changed")
        if data.get("next_required_step") != P7_R51_R19_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R19 ready material must point to R51-20")
    else:
        if data.get("p8_question_design_material_candidate") is not False:
            raise ValueError("R51 R19 blocked material must not set P8 material candidate")
        if not data.get("missing_requirement_refs"):
            raise ValueError("R51 R19 blocked material must explain missing requirements")
        if data.get("next_required_step") != P7_R51_R19_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R19 blocked material must point to R51-19 resolution")
    return True


# ---------------------------------------------------------------------------
# R51-20: no body leak / no question text / no-touch boundary validation.
# ---------------------------------------------------------------------------

P7_R51_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_BOUNDARY_VALIDATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r51.no_body_leak_no_question_text_no_touch_boundary_validation.bodyfree.v1"
)

P7_R51_R20_NEXT_REQUIRED_STEP_REF: Final = (
    "R51_body_free_handoff_material_ready_for_P6_P8_start_decision_without_auto_allow"
)
P7_R51_R20_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "resolve_R51-20_no_body_leak_no_question_text_no_touch_boundary_validation"
)
P7_R51_R20_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R51_R19_IMPLEMENTED_STEPS,
    "R51-20_no_body_leak_no_question_text_no_touch_boundary_validation",
)
P7_R51_R20_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = ()

P7_R51_R20_EXPECTED_TOUCHED_FILE_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run.py",
    "tests/test_emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run_r20_20260621.py",
)
P7_R51_R20_ALLOWED_ACTUAL_TOUCHED_FILE_REFS: Final[tuple[str, ...]] = P7_R51_R20_EXPECTED_TOUCHED_FILE_REFS
P7_R51_R20_EXPLICIT_NO_TOUCH_FILE_REFS: Final[tuple[str, ...]] = (
    *P7_R50_EXPLICIT_NO_TOUCH_FILE_REFS,
    "services/ai_inference/emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision.py",
    "services/ai_inference/emlis_ai_p7_r51_local_review_file_ops.py",
    "services/ai_inference/api_emotion_submit.py",
    "services/ai_inference/emotion_submit_service.py",
    "services/ai_inference/emlis_ai_reply_service.py",
    "services/ai_inference/emlis_ai_public_feedback_meta.py",
    "services/ai_inference/emlis_ai_user_label_connection_material.py",
    "services/ai_inference/emlis_ai_user_label_connection_candidate.py",
    "services/ai_inference/emlis_ai_user_label_connection_gate.py",
    "services/ai_inference/emlis_ai_user_label_connection_surface.py",
    "services/ai_inference/emlis_ai_user_label_connection_public_meta.py",
)
P7_R51_R20_EXPLICIT_NO_TOUCH_AREA_REFS: Final[tuple[str, ...]] = (
    *P7_R50_EXPLICIT_NO_TOUCH_AREA_REFS,
    "r51_local_file_ops_helper",
    "r51_body_full_packet_artifacts",
    "r51_reviewer_notes_artifacts",
)

P7_R51_NO_BODY_LEAK_FORBIDDEN_KEY_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        (
            *P7_R51_ACTUAL_REVIEW_RESULT_INPUT_FORBIDDEN_KEY_REFS,
            "current_input",
            "currentInput",
            "history_raw_text",
            "historyRawText",
            "memo",
            "memo_action",
            "candidate_body",
            "surface_body",
            "visible_surface",
            "surface_for_reviewer",
            "current_input_for_reviewer",
            "history_summary_for_reviewer",
            "review_surface",
            "deleted_body_preview",
            "body_full_file_content_hash",
            "raw_text_hash",
            "comment_text_hash",
            "local_path",
            "local_file_path",
            "body_hash",
            "content_hash",
        )
    )
)
P7_R51_NO_BODY_LEAK_FORBIDDEN_TRUE_FLAG_REFS: Final[tuple[str, ...]] = (
    "raw_input_included",
    "history_raw_text_included",
    "comment_text_body_included",
    "returned_surface_included",
    "review_surface_included",
    "reviewer_free_text_included",
    "question_text_included",
    "draft_question_text_included",
    "question_body_included",
    "local_path_included",
    "body_hash_included",
    "local_path_or_body_hash_included",
    "body_full_packet_exported",
    "local_packet_exported",
    "content_hash_of_body_stored",
    "terminal_output_included",
    "command_output_stored_here",
    "terminal_output_stored_here",
)
P7_R51_NO_TOUCH_MUTATION_TRUE_FLAG_REFS: Final[tuple[str, ...]] = (
    "rn_contract_changed_here",
    "rn_production_files_touched_here",
    "rn_contract_test_files_touched_here",
    "rn_visible_contract_changed_here",
    "api_route_changed_here",
    "db_schema_changed_here",
    "db_migration_changed_here",
    "emlis_reply_runtime_changed_here",
    "user_label_connection_runtime_changed_here",
    "p5_runtime_changed_here",
    "p5_gate_relaxed_here",
    "runtime_changed_here",
    "release_material_changed_here",
    "public_response_shape_changed_here",
    "api_response_shape_changed_here",
    "public_response_top_level_key_added_here",
    "request_key_changed_here",
    "p8_question_implementation_spec_finalized_here",
    "p8_question_detail_design_started_here",
    "question_trigger_logic_implemented_here",
    "question_api_implemented",
    "question_db_schema_implemented",
    "question_rn_ui_implemented",
    "question_response_key_implemented",
    "question_response_key_added",
    "question_answer_persistence_implemented",
)
P7_R51_R20_BOUNDARY_STATUS_REFS: Final[tuple[str, ...]] = (
    "R51_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_BOUNDARY_VALIDATED",
    "BLOCKED_BY_R51_BODY_LEAK_OR_NO_TOUCH_BOUNDARY_VIOLATION",
)

P7_R51_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_BOUNDARY_VALIDATION_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "r19_p8_question_design_material_candidate_handoff_schema_version",
    "r19_p8_question_design_material_candidate_handoff_ref",
    "r19_p8_question_design_material_candidate_status",
    "boundary_validation_status",
    "boundary_validation_reason_refs",
    "missing_requirement_refs",
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
    "r0_current_source_r50_handoff_refrozen",
    "r1_validation_evidence_r49_timeout_handling_frozen",
    "r2_local_root_explicit_allow_purge_plan_preflight_built",
    "r3_actual_review_session_envelope_created",
    "r4_24_case_manifest_freeze_built",
    "r5_local_only_body_full_packet_generation_request_built",
    "r6_body_full_packet_completeness_export_denylist_scan_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_actual_human_review_run_recorded",
    "r9_rating_row_normalizer_built",
    "r10_readfeel_blocker_execution_blocker_ingestion_built",
    "r11_question_need_observation_row_normalizer_built",
    "r12_rating_question_observation_consistency_guard_built",
    "r13_pause_abort_expiration_protocol_built",
    "r14_body_full_packet_reviewer_notes_purge_built",
    "r15_disposal_receipt_builder_verifier_built",
    "r16_body_free_post_review_summary_builder_built",
    "r17_p5_confirmed_repair_return_inconclusive_decision_built",
    "r18_p6_limited_human_readfeel_candidate_handoff_built",
    "r19_p8_question_design_material_candidate_handoff_built",
    "r20_no_body_leak_no_question_text_no_touch_boundary_validation_built",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r51_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R51_R0_R1_FALSE_KEY_REFS,
)


def _r51_find_forbidden_key_paths(
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
            paths.extend(_r51_find_forbidden_key_paths(child, forbidden_keys=forbidden_keys, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_r51_find_forbidden_key_paths(child, forbidden_keys=forbidden_keys, path=f"{path}[{index}]"))
    return paths


def _r51_find_forbidden_true_flag_paths(
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
            paths.extend(_r51_find_forbidden_true_flag_paths(child, forbidden_flags=forbidden_flags, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_r51_find_forbidden_true_flag_paths(child, forbidden_flags=forbidden_flags, path=f"{path}[{index}]"))
    return paths


def _r51_r20_materials_to_scan(
    r19: Mapping[str, Any],
    additional_body_free_materials: Sequence[Mapping[str, Any]] | Any | None,
) -> list[dict[str, Any]]:
    materials = [safe_mapping(r19)]
    if additional_body_free_materials is None:
        return materials
    if isinstance(additional_body_free_materials, Mapping):
        raw_values = [additional_body_free_materials]
    elif isinstance(additional_body_free_materials, Sequence) and not isinstance(additional_body_free_materials, (str, bytes, bytearray)):
        raw_values = list(additional_body_free_materials)
    else:
        raise ValueError("R51 R20 additional body-free materials must be mappings")
    for item in raw_values:
        mapped = safe_mapping(item)
        if not mapped:
            raise ValueError("R51 R20 additional body-free material must be a mapping")
        materials.append(mapped)
    return materials


def _r51_r20_material_refs(materials: Sequence[Mapping[str, Any]]) -> list[str]:
    refs: list[str] = []
    for index, material in enumerate(materials):
        refs.append(clean_identifier(material.get("material_id"), default=f"r51_bodyfree_material_{index}", max_length=180))
    return dedupe_identifiers(refs, limit=80, max_length=180)


def _r51_r20_no_touch_scan(actual_touched_file_refs: Sequence[Any] | Any | None) -> tuple[list[str], list[str], list[str]]:
    touched = dedupe_identifiers(
        actual_touched_file_refs if actual_touched_file_refs is not None else P7_R51_R20_EXPECTED_TOUCHED_FILE_REFS,
        limit=240,
        max_length=260,
    )
    allowed = set(P7_R51_R20_ALLOWED_ACTUAL_TOUCHED_FILE_REFS)
    no_touch = set(P7_R51_R20_EXPLICIT_NO_TOUCH_FILE_REFS)
    touched_set = set(touched)
    forbidden_touched = sorted(touched_set & no_touch)
    not_allowed = sorted(touched_set - allowed)
    return touched, forbidden_touched, not_allowed


def _r51_r20_reason_refs(
    *,
    r19_ready: bool,
    no_body_leak_scan_passed: bool,
    no_touch_boundary_validated: bool,
) -> list[str]:
    if r19_ready and no_body_leak_scan_passed and no_touch_boundary_validated:
        return ["r51_20_bodyfree_no_question_text_no_touch_boundary_validated"]
    reasons: list[str] = []
    if not r19_ready:
        reasons.append("r19_p8_material_handoff_not_ready")
    if not no_body_leak_scan_passed:
        reasons.append("bodyfree_material_leak_or_question_text_detected")
    if not no_touch_boundary_validated:
        reasons.append("actual_touched_refs_or_no_touch_boundary_not_validated")
    return reasons


def build_p7_r51_no_body_leak_no_question_text_no_touch_boundary_validation_bodyfree(
    *,
    p8_question_design_material_candidate_handoff_bodyfree: Mapping[str, Any] | None = None,
    r19_p8_question_design_material_candidate_handoff_bodyfree: Mapping[str, Any] | None = None,
    additional_body_free_materials: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None = None,
    actual_touched_file_refs: Sequence[Any] | Any | None = None,
    material_id: Any = "p7_r51_no_body_leak_no_question_text_no_touch_boundary_validation_bodyfree",
) -> dict[str, Any]:
    """Build the final R51-20 body-free/no-question/no-touch validation material.

    This is a metadata validation helper.  It does not inspect git, delete files,
    write local packets, create question text, start P8, complete P7, or decide
    release readiness.  Callers may pass the touched-file refs they observed;
    absent that, the helper validates the expected R51-20 patch refs only.
    """

    if p8_question_design_material_candidate_handoff_bodyfree is not None and r19_p8_question_design_material_candidate_handoff_bodyfree is not None:
        raise ValueError("provide only one R51-19 P8 material handoff value")
    r19 = safe_mapping(
        p8_question_design_material_candidate_handoff_bodyfree
        if p8_question_design_material_candidate_handoff_bodyfree is not None
        else r19_p8_question_design_material_candidate_handoff_bodyfree
        if r19_p8_question_design_material_candidate_handoff_bodyfree is not None
        else build_p7_r51_p8_question_design_material_candidate_handoff_bodyfree()
    )
    assert_p7_r51_p8_question_design_material_candidate_handoff_bodyfree_contract(r19)

    materials = _r51_r20_materials_to_scan(r19, additional_body_free_materials)
    key_paths: list[str] = []
    true_flag_paths: list[str] = []
    for index, material in enumerate(materials):
        key_paths.extend(
            _r51_find_forbidden_key_paths(
                material,
                forbidden_keys=P7_R51_NO_BODY_LEAK_FORBIDDEN_KEY_REFS,
                path=f"body_free_materials[{index}]",
            )
        )
        true_flag_paths.extend(
            _r51_find_forbidden_true_flag_paths(
                material,
                forbidden_flags=P7_R51_NO_BODY_LEAK_FORBIDDEN_TRUE_FLAG_REFS,
                path=f"body_free_materials[{index}]",
            )
        )
        true_flag_paths.extend(
            _r51_find_forbidden_true_flag_paths(
                material,
                forbidden_flags=P7_R51_NO_TOUCH_MUTATION_TRUE_FLAG_REFS,
                path=f"body_free_materials[{index}]",
            )
        )

    touched_refs, forbidden_touched, not_allowed_touched = _r51_r20_no_touch_scan(actual_touched_file_refs)
    no_body_keys = not key_paths
    no_forbidden_true_flags = not true_flag_paths
    no_touch_boundary_validated = bool(touched_refs and not forbidden_touched and not not_allowed_touched)
    no_body_leak_scan_passed = no_body_keys and no_forbidden_true_flags
    r19_ready = r19.get("p8_question_design_material_candidate_status") == "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_READY"
    ready = bool(r19_ready and no_body_leak_scan_passed and no_touch_boundary_validated)
    status = (
        "R51_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_BOUNDARY_VALIDATED"
        if ready
        else "BLOCKED_BY_R51_BODY_LEAK_OR_NO_TOUCH_BOUNDARY_VIOLATION"
    )
    next_step = P7_R51_R20_NEXT_REQUIRED_STEP_REF if ready else P7_R51_R20_BLOCKED_NEXT_REQUIRED_STEP_REF
    reason_refs = _r51_r20_reason_refs(
        r19_ready=r19_ready,
        no_body_leak_scan_passed=no_body_leak_scan_passed,
        no_touch_boundary_validated=no_touch_boundary_validated,
    )
    missing_requirements = [] if ready else reason_refs
    actual_true_keys = _r51_bodyfree_actual_material_allowed_true_refs(
        include_p6_candidate=bool(r19.get("p6_limited_human_readfeel_start_allowed_candidate")),
        include_p8_candidate=bool(r19.get("p8_question_design_material_candidate")),
    )

    validation = {
        "schema_version": P7_R51_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_BOUNDARY_VALIDATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R51_STEP,
        "scope": P7_R51_SCOPE,
        "policy_kind": P7_R51_POLICY_KIND,
        "policy_section": "R51-20_no_body_leak_no_question_text_no_touch_boundary_validation",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r51_no_body_leak_no_question_text_no_touch_boundary_validation_bodyfree", max_length=180),
        **_false_flags(),
        "review_session_id": clean_identifier(r19.get("review_session_id"), default=P7_R51_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "r19_p8_question_design_material_candidate_handoff_schema_version": P7_R51_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        "r19_p8_question_design_material_candidate_handoff_ref": clean_identifier(r19.get("material_id"), default="p7_r51_p8_question_design_material_candidate_handoff_bodyfree", max_length=180),
        "r19_p8_question_design_material_candidate_status": clean_identifier(r19.get("p8_question_design_material_candidate_status"), default="unknown_r19_status", max_length=120),
        "boundary_validation_status": status,
        "boundary_validation_reason_refs": reason_refs,
        "missing_requirement_refs": missing_requirements,
        "body_free_material_refs_scanned": _r51_r20_material_refs(materials),
        "body_free_material_count_scanned": len(materials),
        "forbidden_body_key_refs": list(P7_R51_NO_BODY_LEAK_FORBIDDEN_KEY_REFS),
        "forbidden_true_flag_refs": list((*P7_R51_NO_BODY_LEAK_FORBIDDEN_TRUE_FLAG_REFS, *P7_R51_NO_TOUCH_MUTATION_TRUE_FLAG_REFS)),
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
        "allowed_actual_touched_file_refs": list(P7_R51_R20_ALLOWED_ACTUAL_TOUCHED_FILE_REFS),
        "expected_touched_file_refs": list(P7_R51_R20_EXPECTED_TOUCHED_FILE_REFS),
        "explicit_no_touch_file_refs": list(P7_R51_R20_EXPLICIT_NO_TOUCH_FILE_REFS),
        "explicit_no_touch_area_refs": list(P7_R51_R20_EXPLICIT_NO_TOUCH_AREA_REFS),
        "forbidden_actual_touched_file_refs": forbidden_touched,
        "not_allowed_actual_touched_file_refs": not_allowed_touched,
        "actual_touched_file_refs_checked_here": True,
        "actual_touched_file_refs_verified_here": no_touch_boundary_validated,
        "actual_touched_file_refs_materialized_here": False,
        "forbidden_actual_touched_refs_detected_here": bool(forbidden_touched or not_allowed_touched),
        "allowed_refs_do_not_include_no_touch_refs": not (set(P7_R51_R20_ALLOWED_ACTUAL_TOUCHED_FILE_REFS) & set(P7_R51_R20_EXPLICIT_NO_TOUCH_FILE_REFS)),
        "expected_touched_refs_are_allowed": set(P7_R51_R20_EXPECTED_TOUCHED_FILE_REFS).issubset(set(P7_R51_R20_ALLOWED_ACTUAL_TOUCHED_FILE_REFS)),
        "no_touch_boundary_validated": no_touch_boundary_validated,
        "rn_no_touch_preserved": not any(ref.startswith("Cocolon/screens/") or ref.startswith("Cocolon/tests/") for ref in touched_refs),
        "api_no_touch_preserved": "services/ai_inference/api_emotion_submit.py" not in touched_refs and "services/ai_inference/emotion_submit_service.py" not in touched_refs,
        "db_no_touch_preserved": not any("migration" in ref or ref.endswith(".sql") for ref in touched_refs),
        "runtime_no_touch_preserved": not any(ref in P7_R51_R20_EXPLICIT_NO_TOUCH_FILE_REFS for ref in touched_refs),
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
        "actual_disposal_run_here": bool(r19.get("actual_disposal_run_here")),
        "actual_disposal_receipt_materialized_here": bool(r19.get("actual_disposal_receipt_materialized_here")),
        "post_review_summary_materialized_here": bool(r19.get("post_review_summary_materialized_here")),
        "actual_human_review_run_here": bool(r19.get("actual_human_review_run_here")),
        "actual_manual_review_run_here": bool(r19.get("actual_manual_review_run_here")),
        "actual_rating_rows_materialized_here": bool(r19.get("actual_rating_rows_materialized_here")),
        "actual_blocker_rows_materialized_here": bool(r19.get("actual_blocker_rows_materialized_here")),
        "actual_execution_blocker_rows_materialized_here": bool(r19.get("actual_execution_blocker_rows_materialized_here")),
        "actual_question_need_observation_rows_materialized_here": bool(r19.get("actual_question_need_observation_rows_materialized_here")),
        "actual_question_need_observation_summary_materialized_here": bool(r19.get("actual_question_need_observation_summary_materialized_here")),
        "p5_human_blind_qa_confirmed_candidate": bool(r19.get("p5_human_blind_qa_confirmed_candidate")),
        "p5_repair_return_candidate": bool(r19.get("p5_repair_return_candidate")),
        "p5_review_inconclusive": bool(r19.get("p5_review_inconclusive")),
        "p6_limited_human_readfeel_start_allowed_candidate": bool(r19.get("p6_limited_human_readfeel_start_allowed_candidate")),
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_question_design_material_candidate": bool(r19.get("p8_question_design_material_candidate")) if ready else False,
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
        "r0_current_source_r50_handoff_refrozen": True,
        "r1_validation_evidence_r49_timeout_handling_frozen": True,
        "r2_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r3_actual_review_session_envelope_created": True,
        "r4_24_case_manifest_freeze_built": True,
        "r5_local_only_body_full_packet_generation_request_built": True,
        "r6_body_full_packet_completeness_export_denylist_scan_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": bool(r19.get("r7_reviewer_instruction_rating_form_freeze_built")),
        "r8_actual_human_review_run_recorded": bool(r19.get("r8_actual_human_review_run_recorded")),
        "r9_rating_row_normalizer_built": bool(r19.get("r9_rating_row_normalizer_built")),
        "r10_readfeel_blocker_execution_blocker_ingestion_built": bool(r19.get("r10_readfeel_blocker_execution_blocker_ingestion_built")),
        "r11_question_need_observation_row_normalizer_built": bool(r19.get("r11_question_need_observation_row_normalizer_built")),
        "r12_rating_question_observation_consistency_guard_built": bool(r19.get("r12_rating_question_observation_consistency_guard_built")),
        "r13_pause_abort_expiration_protocol_built": bool(r19.get("r13_pause_abort_expiration_protocol_built")),
        "r14_body_full_packet_reviewer_notes_purge_built": bool(r19.get("r14_body_full_packet_reviewer_notes_purge_built")),
        "r15_disposal_receipt_builder_verifier_built": bool(r19.get("r15_disposal_receipt_builder_verifier_built")),
        "r16_body_free_post_review_summary_builder_built": bool(r19.get("r16_body_free_post_review_summary_builder_built")),
        "r17_p5_confirmed_repair_return_inconclusive_decision_built": bool(r19.get("r17_p5_confirmed_repair_return_inconclusive_decision_built")),
        "r18_p6_limited_human_readfeel_candidate_handoff_built": bool(r19.get("r18_p6_limited_human_readfeel_candidate_handoff_built")),
        "r19_p8_question_design_material_candidate_handoff_built": bool(r19.get("r19_p8_question_design_material_candidate_handoff_built")),
        "r20_no_body_leak_no_question_text_no_touch_boundary_validation_built": ready,
        "implemented_steps": list(P7_R51_R20_IMPLEMENTED_STEPS if ready else P7_R51_R19_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R51_R20_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R51_R19_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R51_FIRST_NEXT_WORK_REF,
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "r51_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r51_no_body_leak_no_question_text_no_touch_boundary_validation_bodyfree_contract(
        validation,
        allowed_true_false_key_refs=actual_true_keys,
    )
    return validation


def build_p7_r51_no_body_leak_no_question_text_no_touch_boundary_validation(**kwargs: Any) -> dict[str, Any]:
    return build_p7_r51_no_body_leak_no_question_text_no_touch_boundary_validation_bodyfree(**kwargs)


def assert_p7_r51_no_body_leak_no_question_text_no_touch_boundary_validation_bodyfree_contract(
    validation: Mapping[str, Any],
    *,
    allowed_true_false_key_refs: Sequence[str] | None = None,
) -> bool:
    data = safe_mapping(validation)
    _assert_required_fields(
        data,
        required=P7_R51_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_BOUNDARY_VALIDATION_BODYFREE_REQUIRED_FIELD_REFS,
        source="p7_r51_r20_no_body_leak_no_question_text_no_touch_boundary_validation",
    )
    allowed = tuple(
        allowed_true_false_key_refs
        or _r51_bodyfree_actual_material_allowed_true_refs(
            include_p6_candidate=bool(data.get("p6_limited_human_readfeel_start_allowed_candidate")),
            include_p8_candidate=bool(data.get("p8_question_design_material_candidate")),
        )
    )
    _assert_body_free_common_allowing(
        data,
        schema_version=P7_R51_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_BOUNDARY_VALIDATION_SCHEMA_VERSION,
        source="p7_r51_r20_no_body_leak_no_question_text_no_touch_boundary_validation",
        allowed_true_false_key_refs=allowed,
    )
    self_key_paths = _r51_find_forbidden_key_paths(
        data,
        forbidden_keys=P7_R51_NO_BODY_LEAK_FORBIDDEN_KEY_REFS,
        path="p7_r51_r20_validation",
    )
    if self_key_paths:
        raise ValueError(f"R51 R20 material contains forbidden body/question/local/hash keys: {self_key_paths[:4]}")
    self_true_flags = _r51_find_forbidden_true_flag_paths(
        data,
        forbidden_flags=(*P7_R51_NO_BODY_LEAK_FORBIDDEN_TRUE_FLAG_REFS, *P7_R51_NO_TOUCH_MUTATION_TRUE_FLAG_REFS),
        path="p7_r51_r20_validation",
    )
    if self_true_flags:
        raise ValueError(f"R51 R20 material contains forbidden true flags: {self_true_flags[:4]}")
    if data.get("policy_section") != "R51-20_no_body_leak_no_question_text_no_touch_boundary_validation":
        raise ValueError("R51 R20 policy section changed")
    if data.get("boundary_validation_status") not in P7_R51_R20_BOUNDARY_STATUS_REFS:
        raise ValueError("R51 R20 boundary validation status changed")
    if tuple(data.get("forbidden_body_key_refs") or ()) != P7_R51_NO_BODY_LEAK_FORBIDDEN_KEY_REFS:
        raise ValueError("R51 R20 forbidden body key refs changed")
    if tuple(data.get("allowed_actual_touched_file_refs") or ()) != P7_R51_R20_ALLOWED_ACTUAL_TOUCHED_FILE_REFS:
        raise ValueError("R51 R20 allowed touched refs changed")
    if tuple(data.get("expected_touched_file_refs") or ()) != P7_R51_R20_EXPECTED_TOUCHED_FILE_REFS:
        raise ValueError("R51 R20 expected touched refs changed")
    if tuple(data.get("explicit_no_touch_file_refs") or ()) != P7_R51_R20_EXPLICIT_NO_TOUCH_FILE_REFS:
        raise ValueError("R51 R20 explicit no-touch file refs changed")
    if tuple(data.get("explicit_no_touch_area_refs") or ()) != P7_R51_R20_EXPLICIT_NO_TOUCH_AREA_REFS:
        raise ValueError("R51 R20 explicit no-touch area refs changed")
    actual_touched = tuple(dedupe_identifiers(data.get("actual_touched_file_refs") or [], limit=240, max_length=260))
    allowed_touched = set(P7_R51_R20_ALLOWED_ACTUAL_TOUCHED_FILE_REFS)
    no_touch = set(P7_R51_R20_EXPLICIT_NO_TOUCH_FILE_REFS)
    if not actual_touched:
        raise ValueError("R51 R20 actual touched refs must be present")
    status = data.get("boundary_validation_status")
    not_allowed = sorted(set(actual_touched) - allowed_touched)
    if status == "R51_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_BOUNDARY_VALIDATED":
        if set(actual_touched) & no_touch:
            raise ValueError("R51 R20 actual touched refs include explicit no-touch refs")
        if not_allowed:
            raise ValueError(f"R51 R20 actual touched refs are outside allowed R51-20 patch: {not_allowed[:6]}")
    if set(P7_R51_R20_ALLOWED_ACTUAL_TOUCHED_FILE_REFS) & no_touch:
        raise ValueError("R51 R20 allowed refs overlap no-touch refs")
    if not set(P7_R51_R20_EXPECTED_TOUCHED_FILE_REFS).issubset(allowed_touched):
        raise ValueError("R51 R20 expected touched refs must be allowed")
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
        "actual_touched_file_refs_verified_here",
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
    ):
        if data.get("boundary_validation_status") == "R51_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_BOUNDARY_VALIDATED" and data.get(true_key) is not True:
            raise ValueError(f"R51 R20 ready validation must keep {true_key}=True")
    for false_key in (
        "actual_touched_file_refs_materialized_here",
        "forbidden_actual_touched_refs_detected_here",
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
        if (
            false_key == "forbidden_actual_touched_refs_detected_here"
            and status != "R51_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_BOUNDARY_VALIDATED"
        ):
            continue
        if data.get(false_key) is not False:
            raise ValueError(f"R51 R20 must keep {false_key}=False")
    status = data.get("boundary_validation_status")
    if status == "R51_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_BOUNDARY_VALIDATED":
        if data.get("r19_p8_question_design_material_candidate_status") != "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_READY":
            raise ValueError("R51 R20 ready validation requires R51-19 ready material")
        if data.get("detected_forbidden_body_key_paths") or data.get("detected_forbidden_true_flag_paths"):
            raise ValueError("R51 R20 ready validation must have no leak paths")
        if data.get("forbidden_actual_touched_file_refs") or data.get("not_allowed_actual_touched_file_refs"):
            raise ValueError("R51 R20 ready validation must have no touched-ref violations")
        if data.get("r20_no_body_leak_no_question_text_no_touch_boundary_validation_built") is not True:
            raise ValueError("R51 R20 ready validation must mark R20 built")
        if tuple(data.get("implemented_steps") or ()) != P7_R51_R20_IMPLEMENTED_STEPS:
            raise ValueError("R51 R20 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R51_R20_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R51 R20 not-yet steps changed")
        if data.get("next_required_step") != P7_R51_R20_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R20 ready next step changed")
    else:
        if data.get("r20_no_body_leak_no_question_text_no_touch_boundary_validation_built") is not False:
            raise ValueError("R51 R20 blocked validation must not mark R20 built")
        if not data.get("missing_requirement_refs"):
            raise ValueError("R51 R20 blocked validation must explain missing requirements")
        if tuple(data.get("implemented_steps") or ()) != P7_R51_R19_IMPLEMENTED_STEPS:
            raise ValueError("R51 R20 blocked validation must not advance implemented steps")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R51_R19_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R51 R20 blocked validation must preserve R19 not-yet steps")
        if data.get("next_required_step") != P7_R51_R20_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R51 R20 blocked next step changed")
    return True
