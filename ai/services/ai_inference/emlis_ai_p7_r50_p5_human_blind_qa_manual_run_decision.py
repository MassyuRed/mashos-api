# -*- coding: utf-8 -*-
"""P7-R50 P5 Human Blind QA manual-run decision helpers.

R50-0 refreezes the current local source, the completed R49 handoff, and the
P7/P8 Bridge rule before any manual-review GO/NO-GO decision is made.

R50-1 fixes only the R50 scope, schema-version constants, review-session status
enum, manual-run decision enum refs, and execution-blocker enum refs.
R50-2 adopts prior validation evidence as body-free decision material.
R50-3 builds the manual-review GO/NO-GO decision without generating body-full
packets or running actual human review.
R50-4 fixes the local-only root, explicit allow token, and export denylist
preflight before body-full packet generation can be requested.
R50-5 fixes the 24-case review-session protocol body-free, without generating
packets or letting a reviewer read actual body-full material in this step.
R50-6 creates only the local-only body-full packet generation request; it does
not write packets.
R50-7 freezes the reviewer instruction and rating form; it does not run review
or capture rating rows.
R50-8 normalizes sanitized reviewer rating results into body-free rating rows.
R50-9 separates readfeel blocker rows from execution blocker rows.
R50-10 normalizes question-need observation reviewer selections into body-free rows.
R50-11 freezes and exposes the rating/question-observation consistency guard.
R50-12 fixes pause/abort/expiration handling so retention deadlines do not stop
and aborted/expired sessions cannot become P5 confirmed candidates.
R50-13 builds and verifies body-free disposal receipts without running local
purge operations or storing paths, hashes, body text, or reviewer notes.
R50-14 aggregates only body-free review rows and disposal status into the
post-review summary; it does not materialize a summary file.
R50-15 separates P5 confirmed-candidate, repair-return, and inconclusive
outcomes without promoting P7 completion, P8 start, P6 start, or release.
R50-16 builds the P6 limited human-readfeel candidate handoff only when P5
is confirmed as a candidate; it still does not start P6.
R50-17 builds the P8 question-design material candidate handoff from body-free
question-observation counts only; it still does not start P8 or design questions.
R50-18 freezes a no-body-leak/no-question-text guard over R50 body-free
materials without copying body-full content into the guard artifact.
R50-19 builds a validation command matrix that separates R50 target tests,
R49/R48/R47/R46 regressions, display/P5 core checks, collect-only, and optional
RN no-touch confirmation without executing commands or storing terminal output.
R50-20 freezes the touch-candidate/no-touch boundary so the R50 helper and R50
target tests remain the only regular touch candidates; runtime, RN, API, DB,
public meta, P8 question implementation, and release surfaces remain no-touch.

This module intentionally does not generate local body-full packets, run human
review, capture actual rating/question rows, perform local disposal, create schema
files, change API/DB/RN contracts, start P8, complete P7, or claim release
readiness.
"""

from __future__ import annotations

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
    P7_R47_BODY_FREE_DISPOSAL_RECEIPT_SCHEMA_VERSION,
    P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS,
    P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
    P7_R47_DISPOSAL_STATUSES,
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
from emlis_ai_p7_r46_p5_p6_human_readfeel_handoff_material import (
    P5_HUMAN_BLIND_QA_FAMILIES,
    P5_HUMAN_BLIND_QA_RATING_AXES,
    P5_HUMAN_BLIND_QA_TARGETS,
)
from emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet import (
    P7_R48_P5_BLOCKER_KINDS,
    P7_R48_P5_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
    P7_R48_P5_BLOCKER_STATUSES,
    P7_R48_P5_CASE_ROLE_REFS,
    P7_R48_P5_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION,
    P7_R48_P5_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
    P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION,
    P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION,
    P7_R48_P5_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION,
    P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION,
    P7_R48_P5_RATING_BLOCKER_FORBIDDEN_FIELD_REFS,
    P7_R48_P5_REVIEWABLE_VERDICTS,
    P7_R48_PACKET_KIND,
    P7_R48_READFEEL_BLOCKER_ID_REFS,
    P7_R48_REVIEW_KIND,
    P7_R48_SANITIZED_REASON_ID_REFS,
)
from emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution import (
    P7_R49_AMBIGUITY_KIND_REFS,
    P7_R49_BODY_FREE_FORBIDDEN_FIELD_REFS,
    P7_R49_NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_SCHEMA_VERSION,
    P7_R49_ONE_QUESTION_FIT_REFS,
    P7_R49_PACKET_KIND,
    P7_R49_PLAN_CANDIDATE_FLAG_REFS,
    P7_R49_QUESTION_NEED_OBSERVATION_STAGE_REF,
    P7_R49_P6_LIMITED_HUMAN_READFEEL_START_CANDIDATE_HANDOFF_SCHEMA_VERSION,
    P7_R49_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
    P7_R49_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION,
    P7_R49_QUESTION_NEED_OBSERVATION_SUMMARY_BODYFREE_SCHEMA_VERSION,
    P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS,
    P7_R49_REPAIR_REQUIRED_REF_REFS,
    P7_R49_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION,
    P7_R49_REVIEW_KIND,
    P7_R49_R18_IMPLEMENTED_STEPS,
    P7_R49_R18_NEXT_REQUIRED_STEP_REF,
    P7_R49_R18_NOT_YET_IMPLEMENTED_STEPS,
    P7_R49_VALIDATION_R49_TARGET_TEST_FILE_REFS,
    P7_R49_VALIDATION_R48_REGRESSION_TEST_FILE_REFS,
    P7_R49_VALIDATION_R47_REGRESSION_TEST_FILE_REFS,
    P7_R49_VALIDATION_R46_HANDOFF_TEST_FILE_REFS,
    P7_R49_VALIDATION_DISPLAY_API_TEST_FILE_REFS,
    P7_R49_VALIDATION_P5_CORE_TEST_FILE_REFS,
    P7_R49_RN_CONTRACT_OPTIONAL_NO_TOUCH_TEST_REFS,
    P7_R49_STEP,
    P7_R49_SCOPE,
    P7_R49_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION,
    assert_p7_r49_touch_candidate_no_touch_boundary_freeze_contract,
    build_p7_r49_touch_candidate_no_touch_boundary_freeze,
)

P7_R50_CURRENT_SOURCE_R49_HANDOFF_BRIDGE_REFREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.current_source_r49_handoff_bridge_refreeze.bodyfree.v1"
)
P7_R50_SCOPE_SCHEMA_STATUS_ENUM_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.scope_schema_status_enum_freeze.bodyfree.v1"
)
P7_R50_R0_R1_SCOPE_STATUS_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.r0_r1_scope_status_freeze.bodyfree.v1"
)
P7_R50_PRIOR_VALIDATION_EVIDENCE_ADOPTION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.prior_validation_evidence_adoption.bodyfree.v1"
)
P7_R50_MANUAL_RUN_DECISION_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.manual_run_decision.bodyfree.v1"
)
P7_R50_R2_R3_MANUAL_RUN_DECISION_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.r2_r3_manual_run_decision_freeze.bodyfree.v1"
)
P7_R50_LOCAL_ONLY_ROOT_EXPLICIT_ALLOW_EXPORT_PREFLIGHT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.local_only_root_explicit_allow_export_preflight.bodyfree.v1"
)
P7_R50_REVIEW_SESSION_PROTOCOL_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.review_session_protocol.bodyfree.v1"
)
P7_R50_R4_R5_PREFLIGHT_PROTOCOL_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.r4_r5_preflight_protocol_freeze.bodyfree.v1"
)
P7_R50_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.local_only_body_full_packet_generation_request.bodyfree.v1"
)
P7_R50_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.reviewer_instruction_rating_form_freeze.bodyfree.v1"
)
P7_R50_R6_R7_PACKET_REQUEST_RATING_FORM_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.r6_r7_packet_request_rating_form_freeze.bodyfree.v1"
)
P7_R50_RATING_CAPTURE_ROW_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.rating_capture_row.bodyfree.v1"
)
P7_R50_READFEEL_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.readfeel_blocker_row.bodyfree.v1"
)
P7_R50_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.execution_blocker_row.bodyfree.v1"
)
P7_R50_RATING_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.rating_row_normalizer.bodyfree.v1"
)
P7_R50_READFEEL_EXECUTION_BLOCKER_INGESTION_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.readfeel_blocker_execution_blocker_ingestion.bodyfree.v1"
)
P7_R50_R8_R9_RATING_BLOCKER_INGESTION_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.r8_r9_rating_blocker_ingestion_freeze.bodyfree.v1"
)
P7_R50_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.question_need_observation_row.bodyfree.v1"
)
P7_R50_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.question_need_observation_row_normalizer.bodyfree.v1"
)
P7_R50_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.rating_question_observation_consistency_guard.bodyfree.v1"
)
P7_R50_R10_R11_QUESTION_OBSERVATION_CONSISTENCY_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.r10_r11_question_observation_consistency_freeze.bodyfree.v1"
)
P7_R50_R10_R11_QUESTION_NORMALIZER_CONSISTENCY_GUARD_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.r10_r11_question_normalizer_consistency_guard_freeze.bodyfree.v1"
)
P7_R50_PAUSE_ABORT_EXPIRATION_PROTOCOL_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.pause_abort_expiration_protocol.bodyfree.v1"
)
P7_R50_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.disposal_receipt.bodyfree.v1"
)
P7_R50_DISPOSAL_RECEIPT_BUILDER_VERIFIER_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.disposal_receipt_builder_verifier.bodyfree.v1"
)
P7_R50_R12_R13_DISPOSAL_PROTOCOL_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.r12_r13_disposal_protocol_freeze.bodyfree.v1"
)
P7_R50_BODY_FREE_POST_REVIEW_SUMMARY_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.body_free_post_review_summary.bodyfree.v1"
)
P7_R50_P5_CONFIRMED_REPAIR_INCONCLUSIVE_DECISION_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.p5_confirmed_repair_inconclusive_decision.bodyfree.v1"
)
P7_R50_R14_R15_POST_REVIEW_DECISION_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.r14_r15_post_review_decision_freeze.bodyfree.v1"
)
P7_R50_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.p6_limited_human_readfeel_candidate_handoff.bodyfree.v1"
)
P7_R50_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.p8_question_design_material_candidate_handoff.bodyfree.v1"
)
P7_R50_R16_R17_P6_P8_CANDIDATE_HANDOFF_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.r16_r17_p6_p8_candidate_handoff_freeze.bodyfree.v1"
)
P7_R50_NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.no_body_leak_no_question_text_guard.bodyfree.v1"
)
P7_R50_VALIDATION_COMMAND_MATRIX_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.validation_command_matrix.bodyfree.v1"
)
P7_R50_R18_R19_NO_LEAK_VALIDATION_MATRIX_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.r18_r19_no_leak_validation_matrix_freeze.bodyfree.v1"
)
P7_R50_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r50.touch_candidate_no_touch_boundary_freeze.bodyfree.v1"
)

P7_R50_STEP: Final = "R50_P5HumanBlindQAActualReviewManualRunDecision_20260620"
P7_R50_SCOPE: Final = "p5_human_blind_qa_actual_review_manual_run_decision"
P7_R50_POLICY_KIND: Final = "p5_human_blind_qa_actual_review_manual_run_decision_policy"
P7_R50_PACKET_KIND: Final = P7_R48_PACKET_KIND
P7_R50_REVIEW_KIND: Final = P7_R48_REVIEW_KIND
P7_R50_REQUIRED_CASE_COUNT: Final = 24
P7_R50_DEFAULT_REVIEW_SESSION_ID: Final = "p7_r50_p5_human_blind_qa_manual_run_decision_session"
P7_R50_FIRST_NEXT_WORK_REF: Final = "p5_human_blind_qa_actual_review_manual_run_decision"
P7_R50_R0_NEXT_REQUIRED_STEP_REF: Final = "R50-1_scope_schema_version_status_enum_freeze"
P7_R50_R1_NEXT_REQUIRED_STEP_REF: Final = "R50-2_prior_validation_evidence_adoption"
P7_R50_R2_NEXT_REQUIRED_STEP_REF: Final = "R50-3_manual_run_go_no_go_decision_builder"
P7_R50_R3_NEXT_REQUIRED_STEP_REF: Final = "R50-4_local_only_root_explicit_allow_export_denylist_preflight"
P7_R50_R3_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_manual_run_preconditions_before_R50-4"
P7_R50_R4_NEXT_REQUIRED_STEP_REF: Final = "R50-5_24_case_review_session_protocol_builder"
P7_R50_R4_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R50-4_preflight_before_R50-5"
P7_R50_R5_NEXT_REQUIRED_STEP_REF: Final = "R50-6_local_only_body_full_packet_generation_request"
P7_R50_R5_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R50-4_preflight_before_R50-6"
P7_R50_R6_NEXT_REQUIRED_STEP_REF: Final = "R50-7_reviewer_instruction_rating_form_freeze"
P7_R50_R6_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R50-5_protocol_before_R50-7"
P7_R50_R7_NEXT_REQUIRED_STEP_REF: Final = "R50-8_rating_row_normalizer"
P7_R50_R7_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R50-6_packet_generation_request_before_R50-8"
P7_R50_R8_NEXT_REQUIRED_STEP_REF: Final = "R50-9_readfeel_blocker_execution_blocker_ingestion"
P7_R50_R8_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R50-7_reviewer_instruction_rating_form_before_R50-9"
P7_R50_R9_NEXT_REQUIRED_STEP_REF: Final = "R50-10_question_need_observation_row_normalizer"
P7_R50_R9_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R50-8_rating_row_normalizer_before_R50-10"
P7_R50_R10_NEXT_REQUIRED_STEP_REF: Final = "R50-11_rating_question_observation_consistency_guard"
P7_R50_R10_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R50-9_blocker_ingestion_before_R50-11"
P7_R50_R11_NEXT_REQUIRED_STEP_REF: Final = "R50-12_pause_abort_expiration_protocol"
P7_R50_R11_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R50-10_question_observation_normalizer_before_R50-12"
P7_R50_R12_NEXT_REQUIRED_STEP_REF: Final = "R50-13_disposal_receipt_builder_verifier"
P7_R50_R12_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R50-11_consistency_guard_before_R50-13"
P7_R50_R13_NEXT_REQUIRED_STEP_REF: Final = "R50-14_body_free_post_review_summary_builder"
P7_R50_R13_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R50-12_pause_abort_expiration_protocol_before_R50-14"
P7_R50_R14_NEXT_REQUIRED_STEP_REF: Final = "R50-15_p5_confirmed_repair_return_inconclusive_decision"
P7_R50_R14_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R50-13_disposal_receipt_verifier_before_R50-15"
P7_R50_R15_NEXT_REQUIRED_STEP_REF: Final = "R50-16_p6_limited_human_readfeel_candidate_handoff"
P7_R50_R15_REPAIR_RETURN_NEXT_REQUIRED_STEP_REF: Final = "return_to_P5_repair_before_R50-16"
P7_R50_R15_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF: Final = "resolve_R50_review_inconclusive_before_R50-16"
P7_R50_R15_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R50-14_post_review_summary_before_R50-16"
P7_R50_R16_NEXT_REQUIRED_STEP_REF: Final = "R50-17_p8_question_design_material_candidate_handoff"
P7_R50_R16_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R50-15_p5_decision_before_R50-17"
P7_R50_R17_NEXT_REQUIRED_STEP_REF: Final = "R50-18_no_body_leak_no_question_text_guard"
P7_R50_R17_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R50-16_p6_limited_handoff_before_R50-18"
P7_R50_R18_NEXT_REQUIRED_STEP_REF: Final = "R50-19_validation_command_matrix"
P7_R50_R18_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R50-18_body_free_leak_before_R50-19"
P7_R50_R19_NEXT_REQUIRED_STEP_REF: Final = "R50-20_touch_candidate_no_touch_boundary_freeze"
P7_R50_R19_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R50-18_no_body_leak_guard_before_R50-20"
P7_R50_R20_NEXT_REQUIRED_STEP_REF: Final = "P5_human_blind_qa_actual_review_local_only_manual_run_after_R50_boundary_freeze"
P7_R50_R20_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R50-19_validation_matrix_before_local_manual_review"
P7_R50_R20_POST_FREEZE_NEXT_WORK_REF: Final = P7_R50_R20_NEXT_REQUIRED_STEP_REF
P7_R50_EXPLICIT_BODY_FULL_ALLOW_ENV_VAR: Final = "COCOLON_EMLIS_P7_R50_ALLOW_BODY_FULL_PACKET"
P7_R50_EXPLICIT_BODY_FULL_ALLOW_TOKEN_REF: Final = "LOCAL_ONLY_REVIEW_CONFIRMED"
P7_R50_REVIEW_PROMPT_VERSION: Final = "p7_r50_p5_human_blind_qa_review_prompt_v1"
P7_R50_REVIEWER_INSTRUCTION_VERSION: Final = "p7_r50_p5_human_blind_qa_reviewer_instruction_v1"
P7_R50_RATING_FORM_VERSION: Final = "p7_r50_p5_human_blind_qa_rating_form_v1"

P7_R50_R0_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R50-0_current_source_r49_handoff_p7_p8_bridge_refreeze",
)
P7_R50_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R50_R0_IMPLEMENTED_STEPS,
    "R50-1_scope_schema_version_status_enum_freeze",
)
P7_R50_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R50-2_prior_validation_evidence_adoption",
    "R50-3_manual_run_go_no_go_decision_builder",
    "R50-4_local_only_root_explicit_allow_export_denylist_preflight",
    "R50-5_24_case_review_session_protocol_builder",
    "R50-6_local_only_body_full_packet_generation_request",
    "R50-7_reviewer_instruction_rating_form_freeze",
    "R50-8_rating_row_normalizer",
    "R50-9_readfeel_blocker_execution_blocker_ingestion",
    "R50-10_question_need_observation_row_normalizer",
    "R50-11_rating_question_observation_consistency_guard",
    "R50-12_pause_abort_expiration_protocol",
    "R50-13_disposal_receipt_builder_verifier",
    "R50-14_body_free_post_review_summary_builder",
    "R50-15_p5_confirmed_repair_return_inconclusive_decision",
    "R50-16_p6_limited_human_readfeel_candidate_handoff",
    "R50-17_p8_question_design_material_candidate_handoff",
    "R50-18_no_body_leak_no_question_text_guard",
    "R50-19_validation_command_matrix",
    "R50-20_touch_candidate_no_touch_boundary_freeze",
)
P7_R50_R0_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R50-1_scope_schema_version_status_enum_freeze",
    *P7_R50_NOT_YET_IMPLEMENTED_STEPS,
)
P7_R50_R2_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R50_IMPLEMENTED_STEPS,
    "R50-2_prior_validation_evidence_adoption",
)
P7_R50_R2_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R50_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R50_R2_R3_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R50_R2_IMPLEMENTED_STEPS,
    "R50-3_manual_run_go_no_go_decision_builder",
)
P7_R50_R2_R3_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R50_R2_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R50_R4_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R50_R2_R3_IMPLEMENTED_STEPS,
    "R50-4_local_only_root_explicit_allow_export_denylist_preflight",
)
P7_R50_R4_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R50_R2_R3_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R50_R5_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R50_R4_IMPLEMENTED_STEPS,
    "R50-5_24_case_review_session_protocol_builder",
)
P7_R50_R5_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R50_R4_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R50_R6_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R50_R5_IMPLEMENTED_STEPS,
    "R50-6_local_only_body_full_packet_generation_request",
)
P7_R50_R6_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R50_R5_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R50_R7_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R50_R6_IMPLEMENTED_STEPS,
    "R50-7_reviewer_instruction_rating_form_freeze",
)
P7_R50_R7_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R50_R6_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R50_R8_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R50_R7_IMPLEMENTED_STEPS,
    "R50-8_rating_row_normalizer",
)
P7_R50_R8_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R50_R7_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R50_R9_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R50_R8_IMPLEMENTED_STEPS,
    "R50-9_readfeel_blocker_execution_blocker_ingestion",
)
P7_R50_R9_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R50_R8_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R50_R10_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R50_R9_IMPLEMENTED_STEPS,
    "R50-10_question_need_observation_row_normalizer",
)
P7_R50_R10_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R50_R9_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R50_R11_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R50_R10_IMPLEMENTED_STEPS,
    "R50-11_rating_question_observation_consistency_guard",
)
P7_R50_R11_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R50_R10_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R50_R12_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R50_R11_IMPLEMENTED_STEPS,
    "R50-12_pause_abort_expiration_protocol",
)
P7_R50_R12_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R50_R11_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R50_R13_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R50_R12_IMPLEMENTED_STEPS,
    "R50-13_disposal_receipt_builder_verifier",
)
P7_R50_R13_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R50_R12_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R50_R14_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R50_R13_IMPLEMENTED_STEPS,
    "R50-14_body_free_post_review_summary_builder",
)
P7_R50_R14_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R50_R13_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R50_R15_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R50_R14_IMPLEMENTED_STEPS,
    "R50-15_p5_confirmed_repair_return_inconclusive_decision",
)
P7_R50_R15_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R50_R14_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R50_R16_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R50_R15_IMPLEMENTED_STEPS,
    "R50-16_p6_limited_human_readfeel_candidate_handoff",
)
P7_R50_R16_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R50_R15_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R50_R17_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R50_R16_IMPLEMENTED_STEPS,
    "R50-17_p8_question_design_material_candidate_handoff",
)
P7_R50_R17_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R50_R16_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R50_R18_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R50_R17_IMPLEMENTED_STEPS,
    "R50-18_no_body_leak_no_question_text_guard",
)
P7_R50_R18_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R50_R17_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R50_R19_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R50_R18_IMPLEMENTED_STEPS,
    "R50-19_validation_command_matrix",
)
P7_R50_R19_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R50_R18_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R50_R20_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R50_R19_IMPLEMENTED_STEPS,
    "R50-20_touch_candidate_no_touch_boundary_freeze",
)
P7_R50_R20_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = ()

P7_R50_REVIEW_SESSION_STATUS_REFS: Final[tuple[str, ...]] = (
    "NOT_STARTED",
    "PRECHECK_BLOCKED",
    "READY_FOR_LOCAL_BODY_FULL_PACKET_GENERATION",
    "BODY_FULL_PACKETS_CREATED_LOCAL_ONLY",
    "REVIEW_IN_PROGRESS",
    "REVIEW_PAUSED",
    "REVIEW_ABORTED",
    "RATINGS_CAPTURED_BODYFREE",
    "QUESTION_OBSERVATIONS_CAPTURED_BODYFREE",
    "DISPOSAL_PENDING",
    "DISPOSAL_VERIFIED",
    "SUMMARY_READY",
    "DECISION_FINALIZED",
    "BLOCKED",
)
P7_R50_INITIAL_REVIEW_SESSION_STATUS_REF: Final = "NOT_STARTED"

P7_R50_MANUAL_RUN_DECISION_REFS: Final[tuple[str, ...]] = (
    "GO_FOR_LOCAL_MANUAL_REVIEW",
    "NO_GO_MISSING_R49_HANDOFF",
    "NO_GO_TARGET_OR_REGRESSION_EVIDENCE_MISSING",
    "NO_GO_LOCAL_ROOT_UNSAFE",
    "NO_GO_EXPLICIT_ALLOW_MISSING",
    "NO_GO_DISPOSAL_PLAN_UNSAFE",
    "NO_GO_REVIEWER_UNAVAILABLE",
    "NO_GO_SCOPE_DRIFT",
    "NO_GO_BODY_FREE_LEAK_RISK",
    "BLOCKED_BY_EXECUTION_BLOCKER",
)
P7_R50_EXECUTION_BLOCKER_ID_REFS: Final[tuple[str, ...]] = (
    "r50_missing_r49_handoff",
    "r50_missing_r49_target_green_evidence",
    "r50_missing_r48_regression_green_evidence",
    "r50_missing_r47_regression_green_evidence",
    "r50_missing_r46_regression_green_evidence",
    "r50_missing_display_p5_core_green_evidence",
    "r50_local_review_root_missing",
    "r50_local_review_root_invalid",
    "r50_explicit_allow_missing",
    "r50_disposal_plan_missing",
    "r50_body_full_packet_generation_failed",
    "r50_body_full_packet_export_violation",
    "r50_review_aborted_before_rating",
    "r50_rating_rows_incomplete",
    "r50_question_need_observation_rows_incomplete",
    "r50_body_free_leak_detected",
    "r50_disposal_receipt_missing",
    "r50_disposal_failed",
    "r50_disposal_not_verified",
    "r50_scope_drift_detected",
)
P7_R50_EXECUTION_BLOCKER_STATUS_REFS: Final[tuple[str, ...]] = ("OPEN", "TRIAGED", "RESOLVED", "CLOSED")

P7_R50_QUESTION_NEED_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS
P7_R50_AMBIGUITY_KIND_REFS: Final[tuple[str, ...]] = P7_R49_AMBIGUITY_KIND_REFS
P7_R50_ONE_QUESTION_FIT_REFS: Final[tuple[str, ...]] = P7_R49_ONE_QUESTION_FIT_REFS
P7_R50_REPAIR_REQUIRED_REF_REFS: Final[tuple[str, ...]] = P7_R49_REPAIR_REQUIRED_REF_REFS

P7_R50_REVIEWER_VISIBLE_FIELD_REFS: Final[tuple[str, ...]] = (
    "blind_case_id",
    "current_input_review_surface",
    "returned_emlis_surface",
    "bounded_owned_history_review_surface",
    "rating_axes",
    "question_need_observation_selection_form",
    "disposal_reminder",
)
P7_R50_REVIEWER_HIDDEN_FIELD_REFS: Final[tuple[str, ...]] = (
    "case_ref_id",
    "controller_expected_result",
    "gate_expected_result",
    "exact_family_label",
    "subscription_tier_label",
    "internal_reason_ids",
    "p5_confirmed_candidate_conditions",
    "p8_material_candidate_conditions",
)
P7_R50_REVIEW_SESSION_PROTOCOL_STATUS_REFS: Final[tuple[str, ...]] = (
    "READY_FOR_24_CASE_LOCAL_REVIEW_PROTOCOL",
    "BLOCKED_BY_R50_4_PREFLIGHT",
)
P7_R50_BODY_FULL_PACKET_GENERATION_REQUEST_STATUS_REFS: Final[tuple[str, ...]] = (
    "READY_FOR_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST",
    "BLOCKED_BY_R50_5_PROTOCOL",
)
P7_R50_REVIEWER_INSTRUCTION_RATING_FORM_STATUS_REFS: Final[tuple[str, ...]] = (
    "READY_FOR_REVIEWER_INSTRUCTION_AND_RATING_FORM",
    "BLOCKED_BY_R50_6_PACKET_GENERATION_REQUEST",
)
P7_R50_RATING_ROW_NORMALIZER_STATUS_REFS: Final[tuple[str, ...]] = (
    "READY_FOR_RATING_ROW_NORMALIZATION",
    "BLOCKED_BY_R50_7_REVIEWER_INSTRUCTION_RATING_FORM",
)
P7_R50_BLOCKER_INGESTION_STATUS_REFS: Final[tuple[str, ...]] = (
    "READY_FOR_READFEEL_AND_EXECUTION_BLOCKER_INGESTION",
    "BLOCKED_BY_R50_8_RATING_ROW_NORMALIZER",
)
P7_R50_QUESTION_OBSERVATION_NORMALIZER_STATUS_REFS: Final[tuple[str, ...]] = (
    "READY_FOR_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION",
    "BLOCKED_BY_R50_9_BLOCKER_INGESTION",
)
P7_R50_RATING_QUESTION_CONSISTENCY_GUARD_STATUS_REFS: Final[tuple[str, ...]] = (
    "READY_FOR_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD",
    "BLOCKED_BY_R50_10_QUESTION_OBSERVATION_NORMALIZER",
)
P7_R50_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_STATUS_REFS: Final[tuple[str, ...]] = P7_R50_QUESTION_OBSERVATION_NORMALIZER_STATUS_REFS
P7_R50_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_STATUS_REFS: Final[tuple[str, ...]] = P7_R50_RATING_QUESTION_CONSISTENCY_GUARD_STATUS_REFS
P7_R50_PAUSE_ABORT_EXPIRATION_PROTOCOL_STATUS_REFS: Final[tuple[str, ...]] = (
    "READY_FOR_PAUSE_ABORT_EXPIRATION_PROTOCOL",
    "BLOCKED_BY_R50_11_CONSISTENCY_GUARD",
)
P7_R50_DISPOSAL_RECEIPT_BUILDER_VERIFIER_STATUS_REFS: Final[tuple[str, ...]] = (
    "READY_FOR_DISPOSAL_RECEIPT_BUILDER_VERIFIER",
    "DISPOSAL_RECEIPT_VERIFIED_BODYFREE",
    "DISPOSAL_RECEIPT_PENDING_BODYFREE",
    "BLOCKED_BY_R50_12_PAUSE_ABORT_EXPIRATION_PROTOCOL",
)
P7_R50_DISPOSAL_RECEIPT_VERIFICATION_STATUS_REFS: Final[tuple[str, ...]] = (
    "VERIFIED",
    "PENDING",
    "FAILED",
)
P7_R50_ABORT_EXPIRATION_TERMINAL_STATUS_REFS: Final[tuple[str, ...]] = (
    "REVIEW_ABORTED",
    "EXPIRED_PURGED",
)
P7_R50_DISPOSAL_VERIFIED_FOR_CANDIDATE_STATUS_REFS: Final[tuple[str, ...]] = (
    "DISPOSAL_VERIFIED",
)
P7_R50_POST_REVIEW_SUMMARY_BUILDER_STATUS_REFS: Final[tuple[str, ...]] = (
    "BODYFREE_POST_REVIEW_SUMMARY_READY",
    "BLOCKED_BY_R50_13_DISPOSAL_RECEIPT",
)
P7_R50_P5_CONFIRMED_REPAIR_INCONCLUSIVE_DECISION_STATUS_REFS: Final[tuple[str, ...]] = (
    "P5_CONFIRMED_CANDIDATE",
    "P5_REPAIR_RETURN",
    "P5_REVIEW_INCONCLUSIVE",
    "BLOCKED_BY_R50_14_POST_REVIEW_SUMMARY",
)
P7_R50_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_STATUS_REFS: Final[tuple[str, ...]] = (
    "P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_READY",
    "P6_LIMITED_HUMAN_READFEEL_NOT_CANDIDATE",
    "BLOCKED_BY_R50_15_P5_DECISION",
)
P7_R50_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_STATUS_REFS: Final[tuple[str, ...]] = (
    "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_READY",
    "P8_QUESTION_DESIGN_MATERIAL_NOT_CANDIDATE",
    "BLOCKED_BY_R50_16_P6_HANDOFF",
)
P7_R50_NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_STATUS_REFS: Final[tuple[str, ...]] = (
    "NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_READY",
    "BLOCKED_BY_BODY_FREE_LEAK_OR_QUESTION_TEXT",
    "BLOCKED_BY_R50_17_P8_HANDOFF",
)
P7_R50_VALIDATION_COMMAND_MATRIX_STATUS_REFS: Final[tuple[str, ...]] = (
    "VALIDATION_COMMAND_MATRIX_READY",
    "BLOCKED_BY_R50_18_NO_BODY_LEAK_GUARD",
)
P7_R50_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_STATUS_REFS: Final[tuple[str, ...]] = (
    "TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FROZEN",
    "BLOCKED_BY_R50_19_VALIDATION_MATRIX",
)
P7_R50_VALIDATION_COMMAND_GROUP_REFS: Final[tuple[str, ...]] = (
    "syntax_py_compile",
    "r50_target_tests",
    "r49_regression",
    "r48_regression",
    "r47_regression",
    "r46_handoff_regression",
    "display_contract_p5_core_subset",
    "backend_collect_only",
    "rn_no_touch_optional",
)
P7_R50_VALIDATION_COMMAND_REQUIRED_GROUP_REFS: Final[tuple[str, ...]] = (
    "syntax_py_compile",
    "r50_target_tests",
    "r49_regression",
    "r48_regression",
    "r47_regression",
    "r46_handoff_regression",
    "display_contract_p5_core_subset",
    "backend_collect_only",
)
P7_R50_VALIDATION_COMMAND_OPTIONAL_GROUP_REFS: Final[tuple[str, ...]] = (
    "rn_no_touch_optional",
)
P7_R50_VALIDATION_R50_TARGET_TEST_FILE_REFS: Final[tuple[str, ...]] = (
    "tests/test_emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision_r0_r1_20260620.py",
    "tests/test_emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision_r2_r3_20260620.py",
    "tests/test_emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision_r4_r5_20260620.py",
    "tests/test_emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision_r6_r7_20260620.py",
    "tests/test_emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision_r8_r9_20260620.py",
    "tests/test_emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision_r10_r11_20260620.py",
    "tests/test_emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision_r12_r13_20260620.py",
    "tests/test_emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision_r14_r15_20260620.py",
    "tests/test_emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision_r16_r17_20260620.py",
    "tests/test_emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision_r18_r19_20260620.py",
    "tests/test_emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision_r20_20260620.py",
)
P7_R50_VALIDATION_SYNTAX_FILE_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision.py",
    "tests/test_emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision_r18_r19_20260620.py",
    "tests/test_emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision_r20_20260620.py",
)
P7_R50_PRODUCTION_TOUCH_CANDIDATE_FILE_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision.py",
)
P7_R50_OPTIONAL_TOUCH_CANDIDATE_FILE_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r50_local_review_manual_run_file_ops.py",
)
P7_R50_ALLOWED_PRODUCTION_TOUCH_FILE_REFS: Final[tuple[str, ...]] = (
    *P7_R50_PRODUCTION_TOUCH_CANDIDATE_FILE_REFS,
    *P7_R50_OPTIONAL_TOUCH_CANDIDATE_FILE_REFS,
)
P7_R50_ALLOWED_TEST_TOUCH_FILE_REFS: Final[tuple[str, ...]] = P7_R50_VALIDATION_R50_TARGET_TEST_FILE_REFS
P7_R50_ALLOWED_ACTUAL_TOUCHED_FILE_REFS: Final[tuple[str, ...]] = (
    *P7_R50_ALLOWED_PRODUCTION_TOUCH_FILE_REFS,
    *P7_R50_ALLOWED_TEST_TOUCH_FILE_REFS,
)
P7_R50_RN_PRODUCTION_NO_TOUCH_FILE_REFS: Final[tuple[str, ...]] = (
    "Cocolon/screens/InputScreen.js",
    "Cocolon/screens/input/useInputFeedbackModal.js",
    "Cocolon/screens/input/inputFeedbackModel.js",
    "Cocolon/screens/input/InputFeedbackReplyModal.js",
)
P7_R50_RN_CONTRACT_OPTIONAL_NO_TOUCH_TEST_REFS: Final[tuple[str, ...]] = (
    "Cocolon/tests/rn-screen-contracts.test.js",
)
P7_R50_EXPLICIT_NO_TOUCH_FILE_REFS: Final[tuple[str, ...]] = (
    *P7_R50_RN_PRODUCTION_NO_TOUCH_FILE_REFS,
    *P7_R50_RN_CONTRACT_OPTIONAL_NO_TOUCH_TEST_REFS,
    "services/ai_inference/api_emotion_submit.py",
    "services/ai_inference/emotion_submit_service.py",
    "services/ai_inference/emlis_ai_reply_service.py",
    "services/ai_inference/emlis_ai_public_feedback_meta.py",
    "services/ai_inference/emlis_ai_body_free_public_source_lineage.py",
    "services/ai_inference/emlis_ai_user_label_connection_material.py",
    "services/ai_inference/emlis_ai_user_label_connection_candidate.py",
    "services/ai_inference/emlis_ai_user_label_connection_gate.py",
    "services/ai_inference/emlis_ai_user_label_connection_surface.py",
    "services/ai_inference/emlis_ai_user_label_connection_public_meta.py",
    "services/ai_inference/emlis_ai_user_label_connection_product_quality_qa.py",
    "services/ai_inference/emlis_ai_product_readfeel_long_run_product_gate.py",
    "services/ai_inference/emlis_ai_product_readfeel_rubric.py",
    "services/ai_inference/emlis_ai_p7_contracts.py",
    "services/ai_inference/emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution.py",
    "services/ai_inference/emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet.py",
    "services/ai_inference/emlis_ai_p7_r47_local_review_packet_policy.py",
    "services/ai_inference/emlis_ai_p7_r46_p5_p6_human_readfeel_handoff_material.py",
)
P7_R50_EXPLICIT_NO_TOUCH_AREA_REFS: Final[tuple[str, ...]] = (
    "rn_production_files",
    "rn_contract_test_files",
    "api_route_files",
    "db_schema_migration_files",
    "emlis_reply_runtime",
    "public_feedback_meta",
    "body_free_public_source_lineage",
    "user_label_connection_runtime",
    "runtime_gate_threshold_files",
    "p8_question_trigger_logic",
    "p8_question_api_db_rn_response_key",
    "p8_question_storage_schema",
    "release_material_files",
    "premise_material_files",
    "implemented_material_files",
    "body_full_packet_artifact_files",
    "local_reviewer_payload_artifact_files",
    "existing_user_facing_surface_composer_runtime",
)
P7_R50_R20_CURRENT_PATCH_EXPECTED_TOUCHED_FILE_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision.py",
    "tests/test_emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision_r20_20260620.py",
)
P7_R50_NO_BODY_LEAK_TRUE_FLAG_REFS: Final[tuple[str, ...]] = (
    "question_text_included",
    "draft_question_text_included",
    "reviewer_free_text_included",
    "raw_input_included",
    "comment_text_body_included",
    "returned_surface_included",
    "local_path_or_body_hash_included",
    "content_hash_of_body_stored",
    "local_packet_exported",
    "terminal_output_included",
    "question_trigger_logic_implemented_here",
    "p8_implementation_spec_finalized_here",
    "p8_detail_design_allowed_here",
    "api_db_rn_response_key_changed_here",
)
P7_R50_QUESTION_TEXT_FIELD_REFS: Final[tuple[str, ...]] = (
    "question_text",
    "draft_question_text",
    "question_body",
)
P7_R50_REVIEWER_FREE_TEXT_FIELD_REFS: Final[tuple[str, ...]] = (
    "reviewer_free_text",
    "reviewer_note",
    "reviewer_notes",
)
P7_R50_LOCAL_PATH_HASH_FIELD_REFS: Final[tuple[str, ...]] = (
    "local_absolute_path",
    "body_content_hash",
    "packet_content_hash",
    "body_full_file_content_hash",
    "raw_text_hash",
    "comment_text_hash",
)
P7_R50_TERMINAL_OUTPUT_FIELD_REFS: Final[tuple[str, ...]] = (
    "terminal_output",
    "stdout",
    "stderr",
    "traceback",
)
P7_R50_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_REQUIRED_CONDITION_REFS: Final[tuple[str, ...]] = (
    "p5_confirmed_candidate_true",
    "p5_repair_return_false",
    "p5_review_inconclusive_false",
    "p5_unresolved_material_not_hidden_by_p6",
    "disposal_verified_for_candidate",
    "body_removed_true",
    "reviewer_notes_removed_true",
    "local_packet_not_exported",
    "content_hash_not_stored",
    "execution_blocker_open_count_zero",
    "readfeel_blocker_open_count_zero",
    "axis_targets_met",
)
P7_R50_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_REQUIREMENT_REFS: Final[tuple[str, ...]] = (
    "question_observation_rows_24_complete",
    "question_text_absent",
    "draft_question_text_absent",
    "reviewer_free_text_absent",
    "raw_input_or_comment_text_absent",
    "returned_surface_absent",
    "local_path_or_body_hash_absent",
    "primary_class_counts_present",
    "ambiguity_kind_counts_present",
    "one_question_fit_counts_present",
    "repair_required_counts_present",
    "repair_required_not_question_not_misclassified_as_p8",
    "p5_repair_return_not_mixed_into_p8_material",
    "p8_start_allowed_false",
    "question_implementation_not_started",
)
P7_R50_P5_CONFIRMED_REQUIREMENT_REFS: Final[tuple[str, ...]] = (
    "24_rating_rows_complete",
    "24_question_observation_rows_complete",
    "rating_and_question_case_refs_match",
    "execution_blocker_open_count_zero",
    "disposal_verified_for_candidate",
    "body_removed_true",
    "reviewer_notes_removed_true",
    "local_packet_not_exported",
    "content_hash_not_stored",
    "red_count_zero",
    "repair_required_count_zero",
    "readfeel_blocker_count_zero",
    "repair_question_primary_count_zero",
    "axis_targets_met",
)
P7_R50_REPAIR_RETURN_BLOCKER_ID_REFS: Final[tuple[str, ...]] = (
    "p5_history_connection_too_generic",
    "p5_history_scope_overclaim",
    "p5_history_creepy_or_surveillance_feeling",
    "p5_history_line_self_blame_amplification",
    "p5_history_line_shallow_repeat",
    "p5_history_line_wants_more_input_low",
    "p5_free_tier_history_boundary_violation",
    "p5_low_information_history_overread",
    "p5_current_input_overridden_by_history",
    "p5_boundary_history_line_leak_suspected",
    "p5_review_not_enough_context",
)
P7_R50_REPAIR_RETURN_QUESTION_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = (
    "not_question_emlis_readfeel_repair_required",
    "not_question_p5_surface_repair_required",
    "not_question_gate_boundary_required",
)
P7_R50_REPAIR_RETURN_REPAIR_REQUIRED_REF_REFS: Final[tuple[str, ...]] = (
    "emlis_readfeel_repair_required",
    "p5_surface_repair_required",
    "gate_boundary_repair_required",
)
P7_R50_PLAN_CANDIDATE_FLAG_REFS: Final[tuple[str, ...]] = (
    "plus_single_question_candidate_later",
    "premium_deep_dive_candidate_later",
    "p8_design_material_candidate",
)
P7_R50_QUESTION_NEED_OBSERVATION_STAGE_REF: Final = "p7_p8_bridge_question_need_observation"
P7_R50_RATING_VERDICT_REFS: Final[tuple[str, ...]] = (
    "PASS",
    "YELLOW",
    "REPAIR_REQUIRED",
    "RED",
)
P7_R50_REVIEWER_CHECK_ITEM_REFS: Final[tuple[str, ...]] = (
    "history_line_is_natural",
    "surveillance_feeling_is_absent",
    "overclaim_or_overread_is_absent",
    "self_blame_is_not_amplified",
    "wants_more_input_or_accumulation_is_present",
    "generic_or_shallow_repeat_is_absent",
)
P7_R50_REQUIRED_REVIEWER_CHECK_LABEL_REFS: Final[tuple[str, ...]] = (
    "履歴線は自然か",
    "監視感はないか",
    "決めつけ・過剰読解はないか",
    "自己責めを増幅していないか",
    "またCocolonへ残したい感覚につながるか",
    "汎用追記や浅い復唱に見えないか",
)
P7_R50_EXECUTION_BLOCKER_KIND_REFS: Final[tuple[str, ...]] = (
    "HANDOFF",
    "VALIDATION",
    "LOCAL_ROOT",
    "EXPLICIT_ALLOW",
    "DISPOSAL",
    "GENERATION",
    "REVIEW",
    "RATING",
    "QUESTION_OBSERVATION",
    "BODY_FREE_LEAK",
    "SCOPE",
)
P7_R50_RATING_CAPTURE_ROW_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "packet_ref_id",
    "blind_case_id",
    "case_ref_id",
    "family",
    "case_role",
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
P7_R50_READFEEL_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "packet_ref_id",
    "blind_case_id",
    "case_ref_id",
    "family",
    "case_role",
    "blocker_id",
    "blocker_kind",
    "blocker_status",
    "sanitized_reason_ids",
    "reviewer_free_text_included",
    "body_removed",
    "body_free",
)
P7_R50_EXECUTION_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "packet_ref_id",
    "blind_case_id",
    "case_ref_id",
    "family",
    "execution_blocker_id",
    "execution_blocker_kind",
    "execution_blocker_status",
    "readfeel_verdict_not_assigned",
    "body_free",
)
P7_R50_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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

P7_R50_SOURCE_SNAPSHOT_REFS: Final[dict[str, str]] = {
    "premise_zip_ref": "Cocolon_前提資料(239).zip",
    "implemented_materials_zip_ref": "EmlisAIの実装済み資料(72).zip",
    "rn_zip_ref": "Cocolon(245).zip",
    "backend_zip_ref": "mashos-api(158).zip",
    "roadmap_ref": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619(2).md",
    "pre_design_memo_ref": "Cocolon_EmlisAI_P7_R50_P5HumanBlindQAActualReviewManualRunDecision_PreDesignMemo_20260620.md",
    "detailed_design_ref": "Cocolon_EmlisAI_P7_R50_P5HumanBlindQAActualReviewManualRunDecision_詳細設計書_実装順_20260620.md",
}

P7_R50_QUESTION_IMPLEMENTATION_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
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
P7_R50_REVIEW_RELEASE_CLOSED_KEY_REFS: Final[tuple[str, ...]] = (
    "manual_run_decision_made_here",
    "local_only_body_full_generation_allowed",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "actual_body_full_packet_generated_here",
    "body_full_writer_created_here",
    "local_reviewer_payload_materialized_here",
    "actual_human_review_run_here",
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
    "p6_limited_human_readfeel_start_allowed",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p6_limited_human_readfeel_confirmed",
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
P7_R50_SCHEMA_MATERIALIZATION_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
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
P7_R50_R0_R1_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    *P7_R50_QUESTION_IMPLEMENTATION_FALSE_KEY_REFS,
    *P7_R50_REVIEW_RELEASE_CLOSED_KEY_REFS,
    *P7_R50_SCHEMA_MATERIALIZATION_FALSE_KEY_REFS,
)

P7_R50_BODY_FREE_FORBIDDEN_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R49_BODY_FREE_FORBIDDEN_FIELD_REFS,
    "deleted_body_preview",
    "body_full_file_content_hash",
    "raw_text_hash",
    "comment_text_hash",
    "stdout",
    "stderr",
)

P7_R50_R49_HANDOFF_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "r49_handoff_required",
    "r49_step",
    "r49_scope",
    "r49_packet_kind",
    "r49_review_kind",
    "r49_r18_touch_boundary_schema_version",
    "r49_completed_steps",
    "r49_implemented_steps",
    "r49_not_yet_implemented_steps",
    "r49_next_required_step",
    "r49_actual_review_execution_scaffold_finished",
    "r49_question_need_observation_capture_footing_ready",
    "r49_touch_no_touch_boundary_frozen",
    "r49_actual_review_completed",
    "r49_actual_human_review_run",
    "r49_body_full_packet_generated",
    "r49_rating_rows_materialized",
    "r49_question_need_observation_rows_materialized",
    "r49_question_need_observation_summary_materialized",
    "r49_disposal_run",
    "r49_disposal_receipt_materialized",
    "r49_p5_human_blind_qa_confirmed",
    "r49_p5_human_blind_qa_confirmed_candidate",
    "r49_p6_limited_human_readfeel_start_allowed",
    "r49_p6_limited_human_readfeel_start_allowed_candidate",
    "r49_p8_question_design_material_candidate",
    "r49_p7_complete",
    "r49_p8_start_allowed",
    "r49_release_allowed",
    "body_free",
)
P7_R50_BRIDGE_RULE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "bridge_rule_ref",
    "p7_bridge_only",
    "r50_is_manual_run_decision_preparation",
    "question_need_observation_memo_only",
    "question_need_observation_body_free_required",
    "question_need_observation_during_p5_p6_real_device_review_only",
    "p8_design_material_candidate_allowed_later",
    "p8_detail_design_allowed_here",
    "api_db_rn_response_key_change_allowed_here",
    "question_trigger_logic_allowed_here",
    "question_text_allowed_here",
    "draft_question_text_allowed_here",
    "emlis_readfeel_weakness_must_not_be_hidden_by_questions",
    "p5_surface_weakness_must_not_be_hidden_by_questions",
    "gate_boundary_weakness_must_not_be_hidden_by_questions",
    "raw_input_or_comment_text_allowed_in_bridge_material",
    "returned_surface_allowed_in_bridge_material",
    "reviewer_free_text_allowed_in_bridge_material",
    "question_text_allowed_in_bridge_material",
    "p7_completion_condition_relaxed",
    "p8_start_allowed",
    "release_allowed",
    "body_free",
    *P7_R50_QUESTION_IMPLEMENTATION_FALSE_KEY_REFS,
)

P7_R50_CURRENT_SOURCE_R49_HANDOFF_BRIDGE_REFREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r49_handoff",
    "p7_p8_bridge_rule",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "manual_run_decision_required_later",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R0_R1_FALSE_KEY_REFS,
)
P7_R50_SCOPE_SCHEMA_STATUS_ENUM_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "review_kind",
    "packet_kind",
    "r0_schema_version",
    "r0_refreeze_material_ref",
    "r49_handoff_required",
    "required_case_count",
    "review_session_status",
    "review_session_status_refs",
    "manual_run_decision_refs",
    "execution_blocker_id_refs",
    "execution_blocker_status_refs",
    "question_need_primary_class_refs",
    "ambiguity_kind_refs",
    "one_question_fit_refs",
    "repair_required_ref_refs",
    "schema_version_refs",
    "r49_touch_boundary_schema_version",
    "r49_question_need_observation_row_bodyfree_schema_version",
    "r49_question_need_observation_summary_bodyfree_schema_version",
    "r49_review_handoff_summary_bodyfree_schema_version",
    "r49_no_body_leak_guard_schema_version",
    "r49_p6_candidate_handoff_schema_version",
    "r49_p8_material_candidate_handoff_schema_version",
    "r48_reviewer_packet_local_only_schema_version",
    "r48_rating_row_bodyfree_schema_version",
    "r48_blocker_row_bodyfree_schema_version",
    "r48_execution_blocker_row_bodyfree_schema_version",
    "r48_disposal_receipt_bodyfree_schema_version",
    "r48_review_handoff_summary_bodyfree_schema_version",
    "r48_p5_first_formal_case_distribution",
    "r48_readfeel_blocker_id_refs",
    "r47_local_review_root_env_var",
    "r47_disposal_status_refs",
    "r47_body_full_packet_retention_hours",
    "r47_reviewer_notes_retention_after_rating_hours",
    "r47_p5_first_formal_minimums",
    "scope_fixed",
    "schema_versions_fixed",
    "status_enum_fixed",
    "manual_run_decision_enum_fixed",
    "execution_blocker_enum_fixed",
    "question_need_observation_enum_inherited_from_r49",
    "manual_run_decision_made_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "p8_question_detail_design_in_scope",
    "api_db_rn_response_key_changed_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R0_R1_FALSE_KEY_REFS,
)
P7_R50_R0_R1_SCOPE_STATUS_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "r0_current_source_r49_handoff_bridge_refreeze",
    "r1_scope_schema_status_enum_freeze",
    "review_session_id",
    "review_session_status",
    "review_session_status_refs",
    "manual_run_decision_refs",
    "execution_blocker_id_refs",
    "required_case_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "manual_run_decision_required_later",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R0_R1_FALSE_KEY_REFS,
)

P7_R50_PRIOR_VALIDATION_EVIDENCE_GROUP_REFS: Final[tuple[str, ...]] = (
    "r50_r0_r1_current_implementation",
    "r49_target",
    "r48_regression",
    "r47_regression",
    "r46_handoff_regression",
    "display_p5_core_subset",
    "backend_collect_only",
    "rn_no_touch_optional",
)
P7_R50_PRIOR_VALIDATION_EVIDENCE_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "evidence_group_ref",
    "evidence_status_ref",
    "evidence_present",
    "passed_count",
    "collected_count",
    "warning_count",
    "required_for_manual_run_go",
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
P7_R50_PRIOR_VALIDATION_EVIDENCE_ADOPTION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r1_scope_schema_status_enum_freeze_schema_version",
    "r1_scope_schema_status_enum_freeze_ref",
    "current_working_backend_zip_ref",
    "required_case_count",
    "prior_validation_evidence_group_refs",
    "prior_validation_evidence_rows",
    "prior_validation_evidence_row_count",
    "prior_validation_evidence_adopted",
    "precondition_flags",
    "r50_r0_r1_current_implementation_evidence_present",
    "r49_target_green_evidence_present",
    "r48_regression_green_evidence_present",
    "r47_regression_green_evidence_present",
    "r46_regression_green_evidence_present",
    "display_p5_core_green_evidence_present",
    "rn_contract_green_evidence_present",
    "backend_collect_only_evidence_present",
    "full_backend_suite_green_confirmed",
    "collect_only_claimed_as_full_backend_green",
    "rn_contract_claimed_as_real_device_modal_readfeel",
    "evidence_commands_reference_only",
    "validation_commands_executed_here",
    "command_result_body_stored_here",
    "terminal_output_stored_here",
    "manual_run_decision_made_here",
    "local_only_body_full_generation_allowed",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_prior_validation_evidence_adopted",
    "r3_manual_run_decision_built",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R0_R1_FALSE_KEY_REFS,
)
P7_R50_MANUAL_RUN_PRECONDITION_FLAG_REFS: Final[tuple[str, ...]] = (
    "r49_target_green_evidence_present",
    "r48_regression_green_evidence_present",
    "r47_regression_green_evidence_present",
    "r46_regression_green_evidence_present",
    "display_p5_core_green_evidence_present",
    "rn_contract_green_evidence_present",
    "local_review_root_safe",
    "explicit_allow_present",
    "disposal_plan_ready",
    "body_free_summary_path_ready",
)
P7_R50_R3_ALLOWED_TRUE_KEY_REFS: Final[tuple[str, ...]] = (
    "manual_run_decision_made_here",
    "local_only_body_full_generation_allowed",
)
P7_R50_R3_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    key for key in P7_R50_R0_R1_FALSE_KEY_REFS if key not in P7_R50_R3_ALLOWED_TRUE_KEY_REFS
)
P7_R50_R4_ALLOWED_TRUE_KEY_REFS: Final[tuple[str, ...]] = (
    *P7_R50_R3_ALLOWED_TRUE_KEY_REFS,
    "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
)
P7_R50_R4_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    key for key in P7_R50_R0_R1_FALSE_KEY_REFS if key not in P7_R50_R4_ALLOWED_TRUE_KEY_REFS
)
P7_R50_R5_ALLOWED_TRUE_KEY_REFS: Final[tuple[str, ...]] = (
    *P7_R50_R4_ALLOWED_TRUE_KEY_REFS,
    "r5_24_case_review_session_protocol_built",
)
P7_R50_R5_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    key for key in P7_R50_R0_R1_FALSE_KEY_REFS if key not in P7_R50_R5_ALLOWED_TRUE_KEY_REFS
)
P7_R50_R6_ALLOWED_TRUE_KEY_REFS: Final[tuple[str, ...]] = P7_R50_R5_ALLOWED_TRUE_KEY_REFS
P7_R50_R6_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    key for key in P7_R50_R0_R1_FALSE_KEY_REFS if key not in P7_R50_R6_ALLOWED_TRUE_KEY_REFS
)
P7_R50_R7_ALLOWED_TRUE_KEY_REFS: Final[tuple[str, ...]] = P7_R50_R6_ALLOWED_TRUE_KEY_REFS
P7_R50_R7_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    key for key in P7_R50_R0_R1_FALSE_KEY_REFS if key not in P7_R50_R7_ALLOWED_TRUE_KEY_REFS
)
P7_R50_R8_ALLOWED_TRUE_KEY_REFS: Final[tuple[str, ...]] = P7_R50_R7_ALLOWED_TRUE_KEY_REFS
P7_R50_R8_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    key for key in P7_R50_R0_R1_FALSE_KEY_REFS if key not in P7_R50_R8_ALLOWED_TRUE_KEY_REFS
)
P7_R50_R9_ALLOWED_TRUE_KEY_REFS: Final[tuple[str, ...]] = P7_R50_R8_ALLOWED_TRUE_KEY_REFS
P7_R50_R9_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    key for key in P7_R50_R0_R1_FALSE_KEY_REFS if key not in P7_R50_R9_ALLOWED_TRUE_KEY_REFS
)
P7_R50_R10_ALLOWED_TRUE_KEY_REFS: Final[tuple[str, ...]] = P7_R50_R9_ALLOWED_TRUE_KEY_REFS
P7_R50_R10_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    key for key in P7_R50_R0_R1_FALSE_KEY_REFS if key not in P7_R50_R10_ALLOWED_TRUE_KEY_REFS
)
P7_R50_R11_ALLOWED_TRUE_KEY_REFS: Final[tuple[str, ...]] = P7_R50_R10_ALLOWED_TRUE_KEY_REFS
P7_R50_R11_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    key for key in P7_R50_R0_R1_FALSE_KEY_REFS if key not in P7_R50_R11_ALLOWED_TRUE_KEY_REFS
)
P7_R50_R12_ALLOWED_TRUE_KEY_REFS: Final[tuple[str, ...]] = P7_R50_R11_ALLOWED_TRUE_KEY_REFS
P7_R50_R12_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    key for key in P7_R50_R0_R1_FALSE_KEY_REFS if key not in P7_R50_R12_ALLOWED_TRUE_KEY_REFS
)
P7_R50_R13_ALLOWED_TRUE_KEY_REFS: Final[tuple[str, ...]] = P7_R50_R12_ALLOWED_TRUE_KEY_REFS
P7_R50_R13_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    key for key in P7_R50_R0_R1_FALSE_KEY_REFS if key not in P7_R50_R13_ALLOWED_TRUE_KEY_REFS
)
P7_R50_R14_ALLOWED_TRUE_KEY_REFS: Final[tuple[str, ...]] = P7_R50_R13_ALLOWED_TRUE_KEY_REFS
P7_R50_R14_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    key for key in P7_R50_R0_R1_FALSE_KEY_REFS if key not in P7_R50_R14_ALLOWED_TRUE_KEY_REFS
)
P7_R50_R15_ALLOWED_TRUE_KEY_REFS: Final[tuple[str, ...]] = (
    *P7_R50_R13_ALLOWED_TRUE_KEY_REFS,
    "p5_human_blind_qa_confirmed_candidate",
    "p5_repair_return_candidate",
)
P7_R50_R15_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    key for key in P7_R50_R0_R1_FALSE_KEY_REFS if key not in P7_R50_R15_ALLOWED_TRUE_KEY_REFS
)
P7_R50_R16_ALLOWED_TRUE_KEY_REFS: Final[tuple[str, ...]] = (
    *P7_R50_R15_ALLOWED_TRUE_KEY_REFS,
    "p6_limited_human_readfeel_start_allowed_candidate",
)
P7_R50_R16_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    key for key in P7_R50_R0_R1_FALSE_KEY_REFS if key not in P7_R50_R16_ALLOWED_TRUE_KEY_REFS
)
P7_R50_R17_ALLOWED_TRUE_KEY_REFS: Final[tuple[str, ...]] = (
    *P7_R50_R16_ALLOWED_TRUE_KEY_REFS,
    "p8_question_design_material_candidate",
)
P7_R50_R17_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    key for key in P7_R50_R0_R1_FALSE_KEY_REFS if key not in P7_R50_R17_ALLOWED_TRUE_KEY_REFS
)
P7_R50_R18_ALLOWED_TRUE_KEY_REFS: Final[tuple[str, ...]] = P7_R50_R17_ALLOWED_TRUE_KEY_REFS
P7_R50_R18_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    key for key in P7_R50_R0_R1_FALSE_KEY_REFS if key not in P7_R50_R18_ALLOWED_TRUE_KEY_REFS
)
P7_R50_R19_ALLOWED_TRUE_KEY_REFS: Final[tuple[str, ...]] = P7_R50_R18_ALLOWED_TRUE_KEY_REFS
P7_R50_R19_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    key for key in P7_R50_R0_R1_FALSE_KEY_REFS if key not in P7_R50_R19_ALLOWED_TRUE_KEY_REFS
)
P7_R50_R20_ALLOWED_TRUE_KEY_REFS: Final[tuple[str, ...]] = P7_R50_R19_ALLOWED_TRUE_KEY_REFS
P7_R50_R20_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    key for key in P7_R50_R0_R1_FALSE_KEY_REFS if key not in P7_R50_R20_ALLOWED_TRUE_KEY_REFS
)
P7_R50_MANUAL_RUN_DECISION_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r2_prior_validation_evidence_schema_version",
    "r2_prior_validation_evidence_ref",
    "required_case_count",
    "manual_run_decision",
    "manual_run_decision_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "missing_precondition_refs",
    "precondition_flags",
    "local_only_body_full_generation_allowed",
    "manual_run_decision_made_here",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "api_db_rn_response_key_changed_here",
    "question_api_implemented",
    "question_db_schema_implemented",
    "question_rn_ui_implemented",
    "question_response_key_implemented",
    "question_trigger_logic_implemented",
    "p5_human_blind_qa_confirmed",
    "p5_human_blind_qa_confirmed_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p8_question_design_material_candidate",
    "p7_complete",
    "p8_start_allowed",
    "release_allowed",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_prior_validation_evidence_adopted",
    "r3_manual_run_decision_built",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R3_FALSE_KEY_REFS,
)
P7_R50_R2_R3_MANUAL_RUN_DECISION_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "r2_prior_validation_evidence_adoption",
    "r3_manual_run_decision_bodyfree",
    "review_session_id",
    "manual_run_decision",
    "manual_run_decision_reason_refs",
    "precondition_flags",
    "local_only_body_full_generation_allowed",
    "manual_run_decision_made_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_prior_validation_evidence_adopted",
    "r3_manual_run_decision_built",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R3_FALSE_KEY_REFS,
)
P7_R50_LOCAL_ONLY_ROOT_EXPLICIT_ALLOW_EXPORT_PREFLIGHT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r3_manual_run_decision_schema_version",
    "r3_manual_run_decision_ref",
    "manual_run_decision",
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
    "manual_run_decision_made_here",
    "preflight_status",
    "preflight_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_prior_validation_evidence_adopted",
    "r3_manual_run_decision_built",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R4_FALSE_KEY_REFS,
)
P7_R50_REVIEW_SESSION_PROTOCOL_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r4_preflight_schema_version",
    "r4_preflight_ref",
    "preflight_status",
    "protocol_status",
    "protocol_reason_refs",
    "required_case_count",
    "review_prompt_version",
    "reviewer_visible_field_refs",
    "reviewer_hidden_field_refs",
    "rating_axis_refs",
    "rating_axis_target_refs",
    "readfeel_blocker_id_refs",
    "question_need_primary_class_refs",
    "ambiguity_kind_refs",
    "one_question_fit_refs",
    "repair_required_ref_refs",
    "question_need_observation_required",
    "rating_row_required_for_each_case",
    "execution_blocker_row_required_for_unreviewable_case",
    "question_text_required",
    "draft_question_text_allowed",
    "reviewer_free_text_bodyfree_export_allowed",
    "reviewer_free_text_local_only",
    "body_full_reader_protocol_local_only",
    "protocol_body_full_packet_generation_allowed_here",
    "protocol_human_review_run_allowed_here",
    "first_formal_case_distribution",
    "case_distribution_total",
    "minimum_total_cases",
    "minimum_per_family",
    "minimum_history_line_eligible_input",
    "minimum_owned_history_positive_cases",
    "minimum_block_boundary_cases",
    "blind_case_id_required",
    "case_ref_hidden_from_reviewer",
    "family_hidden_from_reviewer",
    "subscription_tier_hidden_from_reviewer",
    "controller_expected_result_hidden_from_reviewer",
    "gate_expected_result_hidden_from_reviewer",
    "p5_confirmed_conditions_hidden_from_reviewer",
    "p8_material_candidate_conditions_hidden_from_reviewer",
    "local_only_body_full_generation_allowed",
    "manual_run_decision_made_here",
    "r5_24_case_review_session_protocol_built",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_prior_validation_evidence_adopted",
    "r3_manual_run_decision_built",
    "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R5_FALSE_KEY_REFS,
)
P7_R50_R4_R5_PREFLIGHT_PROTOCOL_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "r4_local_only_root_explicit_allow_export_denylist_preflight",
    "r5_review_session_protocol_bodyfree",
    "review_session_id",
    "preflight_status",
    "protocol_status",
    "local_only_body_full_generation_allowed",
    "manual_run_decision_made_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_prior_validation_evidence_adopted",
    "r3_manual_run_decision_built",
    "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
    "r5_24_case_review_session_protocol_built",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R5_FALSE_KEY_REFS,
)
P7_R50_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r5_protocol_schema_version",
    "r5_protocol_ref",
    "preflight_status",
    "protocol_status",
    "request_status",
    "request_reason_refs",
    "required_case_count",
    "case_distribution_total",
    "packet_kind",
    "review_kind",
    "review_prompt_version",
    "local_only_request",
    "local_review_root_ref",
    "explicit_allow_token_ref",
    "storage_root_ref",
    "root_path_exposed",
    "local_absolute_path_included",
    "packet_ref_manifest_expected_count",
    "body_full_packet_retention_max_hours",
    "reviewer_notes_retention_after_rating_hours",
    "disposal_required",
    "disposal_receipt_required",
    "body_free_export_allowed_before_disposal",
    "release_material_inclusion_allowed",
    "artifact_zip_inclusion_allowed",
    "premise_or_implemented_docs_inclusion_allowed",
    "local_packet_exported",
    "content_hash_of_body_stored",
    "local_only_directory_profile_refs",
    "bodyfree_after_purge_directory_profile_refs",
    "reviewer_packet_body_source_refs_stored_here",
    "local_path_stored_here",
    "body_content_hash_stored_here",
    "command_executed_here",
    "file_written_here",
    "body_full_packet_generation_request_created_here",
    "body_full_packet_generation_allowed_for_next_manual_step",
    "body_full_packet_generation_executed_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "body_full_writer_created_here",
    "local_reviewer_payload_materialized_here",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "manual_run_decision_made_here",
    "local_only_body_full_generation_allowed",
    "r6_local_only_body_full_packet_generation_request_built",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_prior_validation_evidence_adopted",
    "r3_manual_run_decision_built",
    "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
    "r5_24_case_review_session_protocol_built",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R6_FALSE_KEY_REFS,
)
P7_R50_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r6_packet_generation_request_schema_version",
    "r6_packet_generation_request_ref",
    "request_status",
    "instruction_form_status",
    "instruction_form_reason_refs",
    "required_case_count",
    "review_prompt_version",
    "reviewer_instruction_version",
    "rating_form_version",
    "reviewer_check_item_refs",
    "required_reviewer_check_label_refs",
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
    "local_only_body_full_generation_allowed",
    "manual_run_decision_made_here",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_prior_validation_evidence_adopted",
    "r3_manual_run_decision_built",
    "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
    "r5_24_case_review_session_protocol_built",
    "r6_local_only_body_full_packet_generation_request_built",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R7_FALSE_KEY_REFS,
)
P7_R50_R6_R7_PACKET_REQUEST_RATING_FORM_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "r6_local_only_body_full_packet_generation_request",
    "r7_reviewer_instruction_rating_form_freeze",
    "review_session_id",
    "request_status",
    "instruction_form_status",
    "local_only_body_full_generation_allowed",
    "manual_run_decision_made_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "actual_rating_rows_materialized_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_prior_validation_evidence_adopted",
    "r3_manual_run_decision_built",
    "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
    "r5_24_case_review_session_protocol_built",
    "r6_local_only_body_full_packet_generation_request_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R7_FALSE_KEY_REFS,
)
P7_R50_RATING_ROW_NORMALIZER_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "normalizer_status",
    "normalizer_reason_refs",
    "required_case_count",
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
    "readfeel_auto_estimation_allowed",
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
    "normalizer_ready",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "local_only_body_full_generation_allowed",
    "manual_run_decision_made_here",
    "r8_rating_row_normalizer_built",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_prior_validation_evidence_adopted",
    "r3_manual_run_decision_built",
    "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
    "r5_24_case_review_session_protocol_built",
    "r6_local_only_body_full_packet_generation_request_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R8_FALSE_KEY_REFS,
)
P7_R50_READFEEL_EXECUTION_BLOCKER_INGESTION_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r8_rating_row_normalizer_schema_version",
    "r8_rating_row_normalizer_ref",
    "normalizer_status",
    "blocker_ingestion_status",
    "blocker_ingestion_reason_refs",
    "required_case_count",
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
    "readfeel_and_execution_blockers_separated",
    "execution_blockers_do_not_assign_readfeel_verdict",
    "execution_blocker_cases_do_not_create_rating_rows",
    "rating_missing_maps_to_execution_blocker_not_red",
    "local_root_missing_maps_to_execution_blocker_not_red",
    "disposal_failed_maps_to_execution_blocker_not_red",
    "body_free_leak_maps_to_execution_blocker_not_red",
    "readfeel_blocker_row_builder_ready",
    "execution_blocker_row_builder_ready",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "local_only_body_full_generation_allowed",
    "manual_run_decision_made_here",
    "r9_readfeel_blocker_execution_blocker_ingestion_built",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_prior_validation_evidence_adopted",
    "r3_manual_run_decision_built",
    "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
    "r5_24_case_review_session_protocol_built",
    "r6_local_only_body_full_packet_generation_request_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_rating_row_normalizer_built",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R9_FALSE_KEY_REFS,
)
P7_R50_R8_R9_RATING_BLOCKER_INGESTION_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "r8_rating_row_normalizer",
    "r9_readfeel_blocker_execution_blocker_ingestion",
    "review_session_id",
    "normalizer_status",
    "blocker_ingestion_status",
    "local_only_body_full_generation_allowed",
    "manual_run_decision_made_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_prior_validation_evidence_adopted",
    "r3_manual_run_decision_built",
    "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
    "r5_24_case_review_session_protocol_built",
    "r6_local_only_body_full_packet_generation_request_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_rating_row_normalizer_built",
    "r9_readfeel_blocker_execution_blocker_ingestion_built",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R9_FALSE_KEY_REFS,
)
P7_R50_QUESTION_OBSERVATION_ROW_NORMALIZER_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r9_blocker_ingestion_schema_version",
    "r9_blocker_ingestion_ref",
    "blocker_ingestion_status",
    "question_observation_normalizer_status",
    "question_observation_normalizer_reason_refs",
    "required_case_count",
    "question_need_observation_row_schema_version",
    "r49_question_need_observation_row_schema_version_ref",
    "question_need_observation_row_required_field_refs",
    "question_need_primary_class_refs",
    "ambiguity_kind_refs",
    "one_question_fit_refs",
    "repair_required_ref_refs",
    "plan_candidate_flag_refs",
    "normalizer_ready",
    "question_need_observation_rows_must_be_bodyfree",
    "body_removed_may_be_false_before_disposal",
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
    "question_need_observation_row_normalizer_built",
    "question_need_observation_row_instances_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "local_only_body_full_generation_allowed",
    "manual_run_decision_made_here",
    "r10_question_need_observation_row_normalizer_built",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_prior_validation_evidence_adopted",
    "r3_manual_run_decision_built",
    "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
    "r5_24_case_review_session_protocol_built",
    "r6_local_only_body_full_packet_generation_request_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_rating_row_normalizer_built",
    "r9_readfeel_blocker_execution_blocker_ingestion_built",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R10_FALSE_KEY_REFS,
)
P7_R50_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r10_question_need_observation_row_normalizer_schema_version",
    "r10_question_need_observation_row_normalizer_ref",
    "question_observation_normalizer_status",
    "r8_rating_row_normalizer_schema_version",
    "r9_blocker_ingestion_schema_version",
    "rating_row_schema_version",
    "question_row_schema_version",
    "execution_blocker_row_schema_version",
    "consistency_guard_status",
    "consistency_guard_reason_refs",
    "rating_question_consistency_guard_ready",
    "p5_weakness_must_not_be_hidden_by_questions",
    "rating_and_question_observation_ids_must_match",
    "pass_rating_forbids_not_question_repair_primary_class",
    "repair_or_red_rating_forbids_question_candidate_primary_only",
    "repair_required_not_question_requires_repair_ref",
    "insufficient_material_requires_execution_blocker_row",
    "question_candidate_cannot_clear_readfeel_blocker",
    "creepy_or_history_override_blocker_forbids_p8_material_candidate",
    "consistency_guard_function_ref",
    "question_need_observation_required",
    "question_need_observation_rows_required_later",
    "actual_question_need_observation_rows_materialized_here",
    "actual_question_need_observation_summary_materialized_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "local_only_body_full_generation_allowed",
    "manual_run_decision_made_here",
    "p8_start_allowed",
    "release_allowed",
    "r11_rating_question_observation_consistency_guard_built",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_prior_validation_evidence_adopted",
    "r3_manual_run_decision_built",
    "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
    "r5_24_case_review_session_protocol_built",
    "r6_local_only_body_full_packet_generation_request_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_rating_row_normalizer_built",
    "r9_readfeel_blocker_execution_blocker_ingestion_built",
    "r10_question_need_observation_row_normalizer_built",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R11_FALSE_KEY_REFS,
)
P7_R50_R10_R11_QUESTION_OBSERVATION_CONSISTENCY_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "r10_question_need_observation_row_normalizer",
    "r11_rating_question_observation_consistency_guard",
    "review_session_id",
    "question_observation_normalizer_status",
    "consistency_guard_status",
    "local_only_body_full_generation_allowed",
    "manual_run_decision_made_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_prior_validation_evidence_adopted",
    "r3_manual_run_decision_built",
    "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
    "r5_24_case_review_session_protocol_built",
    "r6_local_only_body_full_packet_generation_request_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_rating_row_normalizer_built",
    "r9_readfeel_blocker_execution_blocker_ingestion_built",
    "r10_question_need_observation_row_normalizer_built",
    "r11_rating_question_observation_consistency_guard_built",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R11_FALSE_KEY_REFS,
)


P7_R50_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r9_blocker_ingestion_schema_version",
    "r9_blocker_ingestion_ref",
    "blocker_ingestion_status",
    "question_observation_normalizer_status",
    "question_observation_normalizer_reason_refs",
    "required_case_count",
    "question_need_observation_row_schema_version",
    "r49_question_need_observation_row_schema_version_ref",
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
    "normalizer_ready",
    "actual_question_need_observation_rows_materialized_here",
    "actual_question_need_observation_summary_materialized_here",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "local_only_body_full_generation_allowed",
    "manual_run_decision_made_here",
    "r10_question_need_observation_row_normalizer_built",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_prior_validation_evidence_adopted",
    "r3_manual_run_decision_built",
    "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
    "r5_24_case_review_session_protocol_built",
    "r6_local_only_body_full_packet_generation_request_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_rating_row_normalizer_built",
    "r9_readfeel_blocker_execution_blocker_ingestion_built",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R10_FALSE_KEY_REFS,
)
P7_R50_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r10_question_need_observation_row_normalizer_schema_version",
    "r10_question_need_observation_row_normalizer_ref",
    "question_observation_normalizer_status",
    "consistency_guard_status",
    "consistency_guard_reason_refs",
    "required_case_count",
    "rating_row_schema_version",
    "question_need_observation_row_schema_version",
    "execution_blocker_row_schema_version",
    "rating_question_consistency_guard_ready",
    "p5_weakness_must_not_be_hidden_by_questions",
    "rating_and_question_observation_ids_must_match",
    "pass_rating_forbids_not_question_repair_primary_class",
    "repair_or_red_rating_forbids_question_candidate_primary_only",
    "repair_required_not_question_requires_repair_ref",
    "insufficient_material_requires_execution_blocker_row",
    "question_candidate_cannot_clear_readfeel_blocker",
    "question_need_observation_required",
    "question_need_observation_rows_required_later",
    "consistency_guard_function_ref",
    "actual_question_need_observation_rows_materialized_here",
    "actual_question_need_observation_summary_materialized_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "local_only_body_full_generation_allowed",
    "manual_run_decision_made_here",
    "r11_rating_question_observation_consistency_guard_built",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_prior_validation_evidence_adopted",
    "r3_manual_run_decision_built",
    "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
    "r5_24_case_review_session_protocol_built",
    "r6_local_only_body_full_packet_generation_request_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_rating_row_normalizer_built",
    "r9_readfeel_blocker_execution_blocker_ingestion_built",
    "r10_question_need_observation_row_normalizer_built",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R11_FALSE_KEY_REFS,
)
P7_R50_R10_R11_QUESTION_NORMALIZER_CONSISTENCY_GUARD_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "r10_question_need_observation_row_normalizer",
    "r11_rating_question_observation_consistency_guard",
    "review_session_id",
    "question_observation_normalizer_status",
    "consistency_guard_status",
    "local_only_body_full_generation_allowed",
    "manual_run_decision_made_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_prior_validation_evidence_adopted",
    "r3_manual_run_decision_built",
    "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
    "r5_24_case_review_session_protocol_built",
    "r6_local_only_body_full_packet_generation_request_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_rating_row_normalizer_built",
    "r9_readfeel_blocker_execution_blocker_ingestion_built",
    "r10_question_need_observation_row_normalizer_built",
    "r11_rating_question_observation_consistency_guard_built",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R11_FALSE_KEY_REFS,
)

P7_R50_DISPOSAL_RECEIPT_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "packet_kind",
    "case_count",
    "deleted_file_count",
    "purge_started_at",
    "purge_completed_at",
    "disposal_status",
    "body_removed",
    "reviewer_notes_removed",
    "local_packet_exported",
    "content_hash_of_body_stored",
    "p7_material_body_free",
    "body_free",
    "release_allowed",
    "p7_complete",
    "p8_start_allowed",
    "hold004_close_allowed",
)
P7_R50_DISPOSAL_RECEIPT_FORBIDDEN_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(P7_R50_BODY_FREE_FORBIDDEN_FIELD_REFS)
)
P7_R50_PAUSE_ABORT_EXPIRATION_PROTOCOL_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r11_consistency_guard_schema_version",
    "r11_consistency_guard_ref",
    "consistency_guard_status",
    "pause_abort_expiration_protocol_status",
    "protocol_reason_refs",
    "required_case_count",
    "disposal_status_refs",
    "body_full_delete_trigger_refs",
    "body_full_packet_retention_max_hours",
    "reviewer_notes_retention_after_rating_hours",
    "retention_deadline_continues_while_paused",
    "pause_does_not_extend_body_full_retention",
    "review_paused_allows_later_resume",
    "review_paused_keeps_local_only_boundary",
    "review_aborted_requires_purge",
    "review_aborted_forbids_p5_confirmed_candidate",
    "expiration_requires_purge_even_if_rating_incomplete",
    "expired_purged_prioritizes_body_removed",
    "expired_purged_forbids_p5_confirmed_candidate",
    "aborted_or_expired_forbid_p5_confirmed_candidate",
    "rating_incomplete_after_expiration_maps_to_execution_blocker_not_readfeel_red",
    "paused_status_ref",
    "aborted_status_ref",
    "expired_purged_status_ref",
    "disposal_pending_status_ref",
    "disposal_verified_status_ref",
    "local_packet_export_allowed_during_pause_abort_expiration",
    "content_hash_storage_allowed_during_pause_abort_expiration",
    "body_free_summary_finalize_allowed_without_disposal_receipt",
    "p5_confirmed_candidate_allowed_after_aborted_or_expired",
    "actual_pause_abort_run_here",
    "actual_expiration_run_here",
    "actual_disposal_run_here",
    "actual_disposal_receipt_materialized_here",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "local_only_body_full_generation_allowed",
    "manual_run_decision_made_here",
    "r12_pause_abort_expiration_protocol_built",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_prior_validation_evidence_adopted",
    "r3_manual_run_decision_built",
    "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
    "r5_24_case_review_session_protocol_built",
    "r6_local_only_body_full_packet_generation_request_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_rating_row_normalizer_built",
    "r9_readfeel_blocker_execution_blocker_ingestion_built",
    "r10_question_need_observation_row_normalizer_built",
    "r11_rating_question_observation_consistency_guard_built",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R12_FALSE_KEY_REFS,
)
P7_R50_DISPOSAL_RECEIPT_BUILDER_VERIFIER_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r12_pause_abort_expiration_protocol_schema_version",
    "r12_pause_abort_expiration_protocol_ref",
    "pause_abort_expiration_protocol_status",
    "disposal_receipt_builder_status",
    "disposal_receipt_verification_status",
    "builder_reason_refs",
    "verifier_reason_refs",
    "required_case_count",
    "disposal_receipt_schema_version",
    "r48_disposal_receipt_schema_version_ref",
    "r47_disposal_receipt_schema_version_ref",
    "disposal_receipt_required_field_refs",
    "disposal_receipt_forbidden_field_refs",
    "disposal_status_refs",
    "disposal_verified_for_candidate_status_refs",
    "body_removed_required",
    "reviewer_notes_removed_required",
    "local_packet_exported_required_false",
    "content_hash_of_body_required_false",
    "p7_material_body_free_required",
    "body_free_disposal_receipt_required_before_summary",
    "body_free_summary_finalize_allowed_without_disposal_receipt",
    "disposal_receipt_verified_for_summary",
    "disposal_verified_for_candidate",
    "expired_purged_body_removed_but_candidate_forbidden",
    "disposal_failed_blocks_p5_p6_p8_candidates",
    "receipt_builder_function_ref",
    "receipt_verifier_function_ref",
    "disposal_receipt_bodyfree",
    "actual_disposal_run_here",
    "actual_disposal_receipt_materialized_here",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "local_only_body_full_generation_allowed",
    "manual_run_decision_made_here",
    "p5_human_blind_qa_confirmed_candidate",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p8_question_design_material_candidate",
    "p7_complete",
    "p8_start_allowed",
    "release_allowed",
    "r13_disposal_receipt_builder_verifier_built",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_prior_validation_evidence_adopted",
    "r3_manual_run_decision_built",
    "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
    "r5_24_case_review_session_protocol_built",
    "r6_local_only_body_full_packet_generation_request_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_rating_row_normalizer_built",
    "r9_readfeel_blocker_execution_blocker_ingestion_built",
    "r10_question_need_observation_row_normalizer_built",
    "r11_rating_question_observation_consistency_guard_built",
    "r12_pause_abort_expiration_protocol_built",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R13_FALSE_KEY_REFS,
)
P7_R50_R12_R13_DISPOSAL_PROTOCOL_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "r12_pause_abort_expiration_protocol",
    "r13_disposal_receipt_builder_verifier",
    "review_session_id",
    "pause_abort_expiration_protocol_status",
    "disposal_receipt_builder_status",
    "disposal_receipt_verification_status",
    "disposal_receipt_verified_for_summary",
    "local_only_body_full_generation_allowed",
    "manual_run_decision_made_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "actual_disposal_run_here",
    "actual_disposal_receipt_materialized_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_prior_validation_evidence_adopted",
    "r3_manual_run_decision_built",
    "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
    "r5_24_case_review_session_protocol_built",
    "r6_local_only_body_full_packet_generation_request_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_rating_row_normalizer_built",
    "r9_readfeel_blocker_execution_blocker_ingestion_built",
    "r10_question_need_observation_row_normalizer_built",
    "r11_rating_question_observation_consistency_guard_built",
    "r12_pause_abort_expiration_protocol_built",
    "r13_disposal_receipt_builder_verifier_built",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R13_FALSE_KEY_REFS,
)

P7_R50_PAUSE_ABORT_EXPIRATION_PROTOCOL_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R50_PAUSE_ABORT_EXPIRATION_PROTOCOL_BODYFREE_REQUIRED_FIELD_REFS,
)

P7_R50_BODY_FREE_POST_REVIEW_SUMMARY_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r13_disposal_receipt_builder_verifier_schema_version",
    "r13_disposal_receipt_builder_verifier_ref",
    "disposal_receipt_builder_status",
    "disposal_receipt_verification_status",
    "disposal_receipt_verified_for_summary",
    "disposal_verified_for_candidate",
    "post_review_summary_builder_status",
    "summary_reason_refs",
    "required_case_count",
    "case_count",
    "rating_row_count",
    "unique_rating_case_count",
    "question_observation_row_count",
    "unique_question_observation_case_count",
    "rating_and_question_case_ref_sets_match",
    "verdict_counts",
    "axis_score_averages",
    "axis_target_refs",
    "axis_target_met_refs",
    "axis_target_failed_refs",
    "blocker_counts",
    "readfeel_blocker_open_count",
    "execution_blocker_counts",
    "execution_blocker_open_count",
    "inherited_open_execution_blocker_ids",
    "question_need_primary_class_counts",
    "ambiguity_kind_counts",
    "one_question_fit_counts",
    "repair_required_counts",
    "disposal_status",
    "body_removed",
    "reviewer_notes_removed",
    "local_packet_exported",
    "content_hash_of_body_stored",
    "body_free_summary_ready",
    "p5_decision_required_next",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "post_review_summary_materialized_here",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_repair_return_candidate",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p8_question_design_material_candidate",
    "p7_complete",
    "p8_start_allowed",
    "release_allowed",
    "manual_run_decision_made_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_prior_validation_evidence_adopted",
    "r3_manual_run_decision_built",
    "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
    "r5_24_case_review_session_protocol_built",
    "r6_local_only_body_full_packet_generation_request_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_rating_row_normalizer_built",
    "r9_readfeel_blocker_execution_blocker_ingestion_built",
    "r10_question_need_observation_row_normalizer_built",
    "r11_rating_question_observation_consistency_guard_built",
    "r12_pause_abort_expiration_protocol_built",
    "r13_disposal_receipt_builder_verifier_built",
    "r14_body_free_post_review_summary_built",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R14_FALSE_KEY_REFS,
)

P7_R50_P5_CONFIRMED_REPAIR_INCONCLUSIVE_DECISION_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r14_post_review_summary_schema_version",
    "r14_post_review_summary_ref",
    "post_review_summary_builder_status",
    "p5_decision_status",
    "p5_decision_reason_refs",
    "p5_confirmed_requirement_refs",
    "p5_confirmed_candidate_reason_refs",
    "p5_repair_return_reason_refs",
    "p5_inconclusive_reason_refs",
    "required_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "rating_and_question_case_ref_sets_match",
    "execution_blocker_open_count",
    "readfeel_blocker_open_count",
    "verdict_counts",
    "axis_score_averages",
    "axis_target_failed_refs",
    "blocker_counts",
    "question_need_primary_class_counts",
    "repair_required_counts",
    "disposal_status",
    "body_removed",
    "reviewer_notes_removed",
    "local_packet_exported",
    "content_hash_of_body_stored",
    "body_free_summary_ready",
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
    "p7_completion_claim_allowed",
    "p8_start_claim_allowed",
    "release_readiness_claim_allowed",
    "manual_run_decision_made_here",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "post_review_decision_materialized_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_prior_validation_evidence_adopted",
    "r3_manual_run_decision_built",
    "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
    "r5_24_case_review_session_protocol_built",
    "r6_local_only_body_full_packet_generation_request_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_rating_row_normalizer_built",
    "r9_readfeel_blocker_execution_blocker_ingestion_built",
    "r10_question_need_observation_row_normalizer_built",
    "r11_rating_question_observation_consistency_guard_built",
    "r12_pause_abort_expiration_protocol_built",
    "r13_disposal_receipt_builder_verifier_built",
    "r14_body_free_post_review_summary_built",
    "r15_p5_confirmed_repair_return_inconclusive_decision_built",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R15_FALSE_KEY_REFS,
)

P7_R50_R14_R15_POST_REVIEW_DECISION_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "r14_body_free_post_review_summary",
    "r15_p5_confirmed_repair_inconclusive_decision",
    "review_session_id",
    "post_review_summary_builder_status",
    "p5_decision_status",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_repair_return_candidate",
    "p5_review_inconclusive",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p8_question_design_material_candidate",
    "p7_complete",
    "p8_start_allowed",
    "release_allowed",
    "manual_run_decision_made_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_prior_validation_evidence_adopted",
    "r3_manual_run_decision_built",
    "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
    "r5_24_case_review_session_protocol_built",
    "r6_local_only_body_full_packet_generation_request_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_rating_row_normalizer_built",
    "r9_readfeel_blocker_execution_blocker_ingestion_built",
    "r10_question_need_observation_row_normalizer_built",
    "r11_rating_question_observation_consistency_guard_built",
    "r12_pause_abort_expiration_protocol_built",
    "r13_disposal_receipt_builder_verifier_built",
    "r14_body_free_post_review_summary_built",
    "r15_p5_confirmed_repair_return_inconclusive_decision_built",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R15_FALSE_KEY_REFS,
)

P7_R50_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "review_kind",
    "packet_kind",
    "r14_r15_post_review_decision_freeze_schema_version",
    "r14_r15_post_review_decision_freeze_ref",
    "r14_r15_post_review_decision_freeze",
    "r49_p6_handoff_schema_version_ref",
    "p6_candidate_handoff_status",
    "p6_candidate_required_condition_refs",
    "p6_candidate_missing_requirement_refs",
    "p6_candidate_failed_requirement_count",
    "p5_decision_status",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_repair_return_candidate",
    "p5_review_inconclusive",
    "p5_unresolved_material_not_hidden_by_p6",
    "p6_limited_human_readfeel_start_candidate_handoff_ready",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "p6_limited_human_readfeel_confirmed",
    "disposal_status",
    "body_removed",
    "reviewer_notes_removed",
    "local_packet_exported",
    "content_hash_of_body_stored",
    "rating_row_count",
    "question_observation_row_count",
    "rating_and_question_case_ref_sets_match",
    "execution_blocker_open_count",
    "readfeel_blocker_open_count",
    "axis_target_failed_refs",
    "p8_question_design_material_candidate",
    "p7_complete",
    "p8_start_allowed",
    "release_allowed",
    "p6_start_permission_granted_here",
    "actual_p6_handoff_materialized_here",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_prior_validation_evidence_adopted",
    "r3_manual_run_decision_built",
    "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
    "r5_24_case_review_session_protocol_built",
    "r6_local_only_body_full_packet_generation_request_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_rating_row_normalizer_built",
    "r9_readfeel_blocker_execution_blocker_ingestion_built",
    "r10_question_need_observation_row_normalizer_built",
    "r11_rating_question_observation_consistency_guard_built",
    "r12_pause_abort_expiration_protocol_built",
    "r13_disposal_receipt_builder_verifier_built",
    "r14_body_free_post_review_summary_built",
    "r15_p5_confirmed_repair_return_inconclusive_decision_built",
    "r16_p6_limited_human_readfeel_candidate_handoff_built",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R16_FALSE_KEY_REFS,
)

P7_R50_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "review_kind",
    "packet_kind",
    "r16_p6_handoff_schema_version",
    "r16_p6_handoff_ref",
    "r16_p6_limited_human_readfeel_candidate_handoff",
    "r49_p8_handoff_schema_version_ref",
    "p8_candidate_handoff_status",
    "p8_design_material_candidate_requirement_refs",
    "p8_design_material_candidate_missing_requirement_refs",
    "p8_design_material_candidate_failed_requirement_count",
    "p8_design_material_bodyfree",
    "total_case_count",
    "question_observation_row_count",
    "question_observation_rows_complete",
    "no_question_needed_count",
    "question_may_reduce_overread_risk_count",
    "question_would_make_immediate_observation_heavy_count",
    "not_question_repair_required_count",
    "emlis_readfeel_repair_required_count",
    "p5_surface_repair_required_count",
    "gate_boundary_repair_required_count",
    "plus_single_question_candidate_later_count",
    "premium_deep_dive_candidate_later_count",
    "primary_class_counts",
    "ambiguity_kind_counts",
    "one_question_fit_counts",
    "repair_required_counts",
    "p5_decision_status",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_repair_return_candidate",
    "p5_review_inconclusive",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "p6_limited_human_readfeel_confirmed",
    "p8_question_design_material_candidate",
    "question_text_included",
    "draft_question_text_included",
    "reviewer_free_text_included",
    "raw_input_or_comment_text_included",
    "returned_surface_included",
    "local_path_or_body_hash_included",
    "question_trigger_logic_implemented_here",
    "api_db_rn_response_key_changed_here",
    "p8_detail_design_allowed_here",
    "p8_implementation_spec_finalized_here",
    "actual_p8_design_material_handoff_materialized_here",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "p7_complete",
    "p8_start_allowed",
    "release_allowed",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_prior_validation_evidence_adopted",
    "r3_manual_run_decision_built",
    "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
    "r5_24_case_review_session_protocol_built",
    "r6_local_only_body_full_packet_generation_request_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_rating_row_normalizer_built",
    "r9_readfeel_blocker_execution_blocker_ingestion_built",
    "r10_question_need_observation_row_normalizer_built",
    "r11_rating_question_observation_consistency_guard_built",
    "r12_pause_abort_expiration_protocol_built",
    "r13_disposal_receipt_builder_verifier_built",
    "r14_body_free_post_review_summary_built",
    "r15_p5_confirmed_repair_return_inconclusive_decision_built",
    "r16_p6_limited_human_readfeel_candidate_handoff_built",
    "r17_p8_question_design_material_candidate_handoff_built",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R17_FALSE_KEY_REFS,
)

P7_R50_R16_R17_P6_P8_CANDIDATE_HANDOFF_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "r16_p6_limited_human_readfeel_candidate_handoff",
    "r17_p8_question_design_material_candidate_handoff",
    "review_session_id",
    "p6_candidate_handoff_status",
    "p8_candidate_handoff_status",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "p8_question_design_material_candidate",
    "p8_start_allowed",
    "p7_complete",
    "release_allowed",
    "manual_run_decision_made_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_prior_validation_evidence_adopted",
    "r3_manual_run_decision_built",
    "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
    "r5_24_case_review_session_protocol_built",
    "r6_local_only_body_full_packet_generation_request_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_rating_row_normalizer_built",
    "r9_readfeel_blocker_execution_blocker_ingestion_built",
    "r10_question_need_observation_row_normalizer_built",
    "r11_rating_question_observation_consistency_guard_built",
    "r12_pause_abort_expiration_protocol_built",
    "r13_disposal_receipt_builder_verifier_built",
    "r14_body_free_post_review_summary_built",
    "r15_p5_confirmed_repair_return_inconclusive_decision_built",
    "r16_p6_limited_human_readfeel_candidate_handoff_built",
    "r17_p8_question_design_material_candidate_handoff_built",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R17_FALSE_KEY_REFS,
)

P7_R50_NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "r16_r17_p6_p8_candidate_handoff_freeze_schema_version",
    "r16_r17_p6_p8_candidate_handoff_freeze_ref",
    "source_material_schema_version_ref",
    "source_material_policy_section_ref",
    "source_material_contract_checked",
    "source_material_embedded_here",
    "guard_status",
    "guard_reason_refs",
    "required_case_count",
    "body_free_forbidden_field_refs",
    "forbidden_field_refs_detected",
    "forbidden_field_detected_count",
    "forbidden_true_flag_refs",
    "forbidden_true_flag_refs_detected",
    "forbidden_true_flag_detected_count",
    "question_text_field_refs",
    "reviewer_free_text_field_refs",
    "local_path_hash_field_refs",
    "terminal_output_field_refs",
    "body_free_flag_checked",
    "body_free_flag_present",
    "body_field_key_detected",
    "question_text_or_draft_question_text_detected",
    "reviewer_free_text_detected",
    "local_path_or_body_hash_detected",
    "terminal_output_detected",
    "raw_input_or_comment_text_detected",
    "question_implementation_started_here",
    "api_db_rn_response_key_changed_here",
    "no_body_leak_guard_passed",
    "no_question_text_guard_passed",
    "body_free_material_checked_without_copying_body",
    "p6_limited_human_readfeel_start_allowed",
    "p8_question_design_material_candidate",
    "p8_start_allowed",
    "p7_complete",
    "release_allowed",
    "manual_run_decision_made_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_prior_validation_evidence_adopted",
    "r3_manual_run_decision_built",
    "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
    "r5_24_case_review_session_protocol_built",
    "r6_local_only_body_full_packet_generation_request_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_rating_row_normalizer_built",
    "r9_readfeel_blocker_execution_blocker_ingestion_built",
    "r10_question_need_observation_row_normalizer_built",
    "r11_rating_question_observation_consistency_guard_built",
    "r12_pause_abort_expiration_protocol_built",
    "r13_disposal_receipt_builder_verifier_built",
    "r14_body_free_post_review_summary_built",
    "r15_p5_confirmed_repair_return_inconclusive_decision_built",
    "r16_p6_limited_human_readfeel_candidate_handoff_built",
    "r17_p8_question_design_material_candidate_handoff_built",
    "r18_no_body_leak_no_question_text_guard_built",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R18_FALSE_KEY_REFS,
)
P7_R50_VALIDATION_COMMAND_ROW_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "validation_group_ref",
    "command_kind_ref",
    "command_purpose_ref",
    "required_for_r50_validation",
    "optional",
    "command_lines",
    "test_file_refs",
    "claim_boundary_ref",
    "command_executed_here",
    "command_result_body_stored_here",
    "terminal_output_stored_here",
    "body_free",
)
P7_R50_VALIDATION_COMMAND_MATRIX_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "r18_no_body_leak_no_question_text_guard_schema_version",
    "r18_no_body_leak_no_question_text_guard_ref",
    "guard_status",
    "validation_matrix_status",
    "validation_matrix_reason_refs",
    "validation_command_group_refs",
    "required_validation_group_refs",
    "optional_validation_group_refs",
    "validation_command_rows",
    "validation_command_row_count",
    "r50_target_test_file_refs",
    "r49_regression_test_file_refs",
    "r48_regression_test_file_refs",
    "r47_regression_test_file_refs",
    "r46_handoff_regression_test_file_refs",
    "display_contract_p5_core_test_file_refs",
    "rn_no_touch_optional_test_file_refs",
    "validation_commands_reference_only",
    "validation_commands_executed_here",
    "command_result_body_stored_here",
    "terminal_output_stored_here",
    "r50_target_green_confirmed_here",
    "r49_regression_green_confirmed_here",
    "r48_regression_green_confirmed_here",
    "r47_regression_green_confirmed_here",
    "r46_regression_green_confirmed_here",
    "display_p5_core_green_confirmed_here",
    "backend_collect_only_confirmed_here",
    "rn_no_touch_optional_confirmed_here",
    "full_backend_suite_green_confirmed",
    "collect_only_claimed_as_full_backend_green",
    "rn_contract_claimed_as_real_device_modal_readfeel",
    "r50_target_green_claimed_as_p5_product_quality_pass",
    "real_device_modal_readfeel_confirmed",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "p7_complete",
    "p8_start_allowed",
    "release_allowed",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_prior_validation_evidence_adopted",
    "r3_manual_run_decision_built",
    "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
    "r5_24_case_review_session_protocol_built",
    "r6_local_only_body_full_packet_generation_request_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_rating_row_normalizer_built",
    "r9_readfeel_blocker_execution_blocker_ingestion_built",
    "r10_question_need_observation_row_normalizer_built",
    "r11_rating_question_observation_consistency_guard_built",
    "r12_pause_abort_expiration_protocol_built",
    "r13_disposal_receipt_builder_verifier_built",
    "r14_body_free_post_review_summary_built",
    "r15_p5_confirmed_repair_return_inconclusive_decision_built",
    "r16_p6_limited_human_readfeel_candidate_handoff_built",
    "r17_p8_question_design_material_candidate_handoff_built",
    "r18_no_body_leak_no_question_text_guard_built",
    "r19_validation_command_matrix_built",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R19_FALSE_KEY_REFS,
)
P7_R50_R18_R19_NO_LEAK_VALIDATION_MATRIX_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "r18_no_body_leak_no_question_text_guard",
    "r19_validation_command_matrix",
    "review_session_id",
    "guard_status",
    "validation_matrix_status",
    "validation_command_row_count",
    "p7_complete",
    "p8_start_allowed",
    "release_allowed",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_prior_validation_evidence_adopted",
    "r3_manual_run_decision_built",
    "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
    "r5_24_case_review_session_protocol_built",
    "r6_local_only_body_full_packet_generation_request_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_rating_row_normalizer_built",
    "r9_readfeel_blocker_execution_blocker_ingestion_built",
    "r10_question_need_observation_row_normalizer_built",
    "r11_rating_question_observation_consistency_guard_built",
    "r12_pause_abort_expiration_protocol_built",
    "r13_disposal_receipt_builder_verifier_built",
    "r14_body_free_post_review_summary_built",
    "r15_p5_confirmed_repair_return_inconclusive_decision_built",
    "r16_p6_limited_human_readfeel_candidate_handoff_built",
    "r17_p8_question_design_material_candidate_handoff_built",
    "r18_no_body_leak_no_question_text_guard_built",
    "r19_validation_command_matrix_built",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R19_FALSE_KEY_REFS,
)
P7_R50_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "review_kind",
    "packet_kind",
    "r18_r19_no_leak_validation_matrix_freeze_schema_version",
    "r18_r19_no_leak_validation_matrix_freeze_ref",
    "r49_touch_boundary_schema_version",
    "r49_touch_boundary_ref",
    "guard_status",
    "validation_matrix_status",
    "touch_boundary_status",
    "touch_boundary_reason_refs",
    "touch_boundary_freeze_required",
    "touch_boundary_freeze_ready",
    "production_touch_candidate_file_refs",
    "optional_touch_candidate_file_refs",
    "test_touch_candidate_file_refs",
    "allowed_production_file_refs",
    "allowed_test_file_refs",
    "allowed_actual_touched_file_refs",
    "explicit_no_touch_file_refs",
    "explicit_no_touch_area_refs",
    "forbidden_actual_touched_file_refs",
    "current_patch_expected_touched_file_refs",
    "actual_touched_file_refs_checked_here",
    "actual_touched_file_refs_verified_here",
    "actual_touched_file_refs_materialized_here",
    "forbidden_actual_touched_refs_detected_here",
    "touch_candidate_boundary_frozen",
    "no_touch_boundary_frozen",
    "forbidden_actual_touched_refs_rejected",
    "no_touch_refs_must_remain_untouched",
    "allowed_refs_do_not_include_no_touch_refs",
    "current_patch_expected_touched_refs_are_allowed",
    "production_touch_candidate_is_r50_helper_only",
    "optional_touch_candidate_is_local_file_ops_only",
    "test_touch_candidate_is_r50_target_only",
    "production_runtime_spread_allowed",
    "rn_runtime_spread_allowed",
    "api_db_release_spread_allowed",
    "rn_contract_changed_here",
    "rn_production_files_touched_here",
    "rn_contract_test_files_touched_here",
    "rn_visible_contract_changed_here",
    "public_response_shape_changed_here",
    "api_response_shape_changed_here",
    "public_response_top_level_key_added_here",
    "request_key_changed_here",
    "api_route_changed_here",
    "db_schema_changed_here",
    "db_migration_changed_here",
    "emlis_reply_runtime_changed_here",
    "user_label_connection_runtime_changed_here",
    "p5_runtime_changed_here",
    "p5_gate_relaxed_here",
    "release_material_changed_here",
    "question_trigger_logic_implemented_here",
    "question_api_implemented",
    "question_db_schema_implemented",
    "question_rn_ui_implemented",
    "question_response_key_added",
    "question_text_implemented_here",
    "draft_question_text_implemented_here",
    "validation_commands_executed_here",
    "command_output_stored_here",
    "terminal_output_stored_here",
    "p5_human_blind_qa_confirmed_candidate",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p8_question_design_material_candidate",
    "p5_human_blind_qa_confirmed",
    "p6_limited_human_readfeel_start_allowed",
    "p6_limited_human_readfeel_confirmed",
    "p8_detail_design_allowed_here",
    "p8_implementation_spec_finalized_here",
    "p7_complete",
    "p8_start_allowed",
    "release_allowed",
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
    "actual_disposal_run_here",
    "actual_disposal_receipt_materialized_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "post_r20_next_work_ref",
    "r0_current_source_r49_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_prior_validation_evidence_adopted",
    "r3_manual_run_decision_built",
    "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
    "r5_24_case_review_session_protocol_built",
    "r6_local_only_body_full_packet_generation_request_built",
    "r7_reviewer_instruction_rating_form_freeze_built",
    "r8_rating_row_normalizer_built",
    "r9_readfeel_blocker_execution_blocker_ingestion_built",
    "r10_question_need_observation_row_normalizer_built",
    "r11_rating_question_observation_consistency_guard_built",
    "r12_pause_abort_expiration_protocol_built",
    "r13_disposal_receipt_builder_verifier_built",
    "r14_body_free_post_review_summary_built",
    "r15_p5_confirmed_repair_return_inconclusive_decision_built",
    "r16_p6_limited_human_readfeel_candidate_handoff_built",
    "r17_p8_question_design_material_candidate_handoff_built",
    "r18_no_body_leak_no_question_text_guard_built",
    "r19_validation_command_matrix_built",
    "r20_touch_candidate_no_touch_boundary_frozen",
    "public_contract",
    "r50_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R50_R20_FALSE_KEY_REFS,
)


def _safe_snapshot_refs(snapshot_refs: Mapping[str, Any] | None) -> dict[str, str]:
    base = dict(P7_R50_SOURCE_SNAPSHOT_REFS)
    if snapshot_refs:
        for key, value in snapshot_refs.items():
            text = clean_identifier(value, default="", max_length=220)
            if text:
                base[str(key)] = text
    return base


def _false_flags() -> dict[str, bool]:
    return {key: False for key in P7_R50_R0_R1_FALSE_KEY_REFS}


def _body_free_markers() -> dict[str, bool]:
    markers = body_free_flags(include_history=True, include_reviewer=True, include_terminal=True)
    markers.update(
        {
            "question_text_included": False,
            "draft_question_text_included": False,
            "question_body_included": False,
            "local_absolute_path_included": False,
            "body_content_hash_included": False,
            "packet_content_hash_included": False,
        }
    )
    return markers


def _public_no_touch_contract() -> dict[str, bool]:
    return {
        "rn_visible_contract_changed": False,
        "rn_production_files_touched": False,
        "rn_contract_test_changed": False,
        "api_response_key_added": False,
        "api_response_shape_changed": False,
        "public_response_top_level_key_added": False,
        "request_key_changed": False,
        "api_route_changed": False,
        "db_schema_changed": False,
        "db_migration_changed": False,
        "emlis_reply_runtime_changed": False,
        "user_label_connection_runtime_changed": False,
        "p5_gate_relaxed": False,
        "p8_question_trigger_logic_implemented": False,
        "release_material_changed": False,
    }


def _assert_required_fields(data: Mapping[str, Any], *, required: Sequence[str], source: str) -> None:
    if set(data) != set(required):
        missing = sorted(set(required) - set(data))
        extra = sorted(set(data) - set(required))
        raise ValueError(f"{source} fields changed; missing={missing[:8]} extra={extra[:8]}")


def _assert_no_forbidden_body_keys(value: Any, *, source: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in P7_R50_BODY_FREE_FORBIDDEN_FIELD_REFS:
                raise ValueError(f"{source} contains forbidden body-free key: {key}")
            _assert_no_forbidden_body_keys(child, source=f"{source}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _assert_no_forbidden_body_keys(child, source=f"{source}[{index}]")


def _assert_false_flags(data: Mapping[str, Any], *, source: str) -> None:
    for key in P7_R50_R0_R1_FALSE_KEY_REFS:
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=False during R50-0/R50-1")


def _assert_common(data: Mapping[str, Any], *, schema_version: str, source: str) -> None:
    if data.get("schema_version") != schema_version:
        raise ValueError(f"{source} schema version changed")
    if data.get("phase") != P7_PHASE:
        raise ValueError(f"{source} phase changed")
    if data.get("step") != P7_R50_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R50_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("policy_kind") != P7_R50_POLICY_KIND:
        raise ValueError(f"{source} policy kind changed")
    if data.get("current_phase") != "P7":
        raise ValueError(f"{source} must remain in P7")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must be body_free=True")
    _assert_false_flags(data, source=source)
    _assert_no_forbidden_body_keys(data, source=source)
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)
    assert_false_markers(safe_mapping(data.get("public_contract")), source=f"{source}.public_contract")
    assert_false_markers(safe_mapping(data.get("r50_public_no_touch_contract")), source=f"{source}.r50_public_no_touch_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source=f"{source}.body_free_markers")


def _safe_review_session_id(value: Any) -> str:
    session_id = clean_identifier(value, default=P7_R50_DEFAULT_REVIEW_SESSION_ID, max_length=140)
    if not session_id:
        raise ValueError("R50 review_session_id must be non-empty")
    return session_id


def _safe_review_session_status(value: Any) -> str:
    status = clean_identifier(value, default=P7_R50_INITIAL_REVIEW_SESSION_STATUS_REF, max_length=80)
    if status not in P7_R50_REVIEW_SESSION_STATUS_REFS:
        raise ValueError("R50 review session status is not in the frozen enum")
    if status != P7_R50_INITIAL_REVIEW_SESSION_STATUS_REF:
        raise ValueError("R50 R0/R1 can only build a NOT_STARTED review session")
    return status


def _r49_boundary(value: Mapping[str, Any] | None = None) -> dict[str, Any]:
    if value is None:
        boundary = build_p7_r49_touch_candidate_no_touch_boundary_freeze()
    else:
        boundary = safe_mapping(value)
    assert_p7_r49_touch_candidate_no_touch_boundary_freeze_contract(boundary)
    return boundary


def _build_r49_handoff(boundary: Mapping[str, Any]) -> dict[str, Any]:
    r49_boundary = _r49_boundary(boundary)
    handoff = {
        "r49_handoff_required": True,
        "r49_step": P7_R49_STEP,
        "r49_scope": P7_R49_SCOPE,
        "r49_packet_kind": P7_R49_PACKET_KIND,
        "r49_review_kind": P7_R49_REVIEW_KIND,
        "r49_r18_touch_boundary_schema_version": P7_R49_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION,
        "r49_completed_steps": list(P7_R49_R18_IMPLEMENTED_STEPS),
        "r49_implemented_steps": list(P7_R49_R18_IMPLEMENTED_STEPS),
        "r49_not_yet_implemented_steps": list(P7_R49_R18_NOT_YET_IMPLEMENTED_STEPS),
        "r49_next_required_step": P7_R49_R18_NEXT_REQUIRED_STEP_REF,
        "r49_actual_review_execution_scaffold_finished": True,
        "r49_question_need_observation_capture_footing_ready": True,
        "r49_touch_no_touch_boundary_frozen": True,
        "r49_actual_review_completed": False,
        "r49_actual_human_review_run": False,
        "r49_body_full_packet_generated": False,
        "r49_rating_rows_materialized": False,
        "r49_question_need_observation_rows_materialized": False,
        "r49_question_need_observation_summary_materialized": False,
        "r49_disposal_run": False,
        "r49_disposal_receipt_materialized": False,
        "r49_p5_human_blind_qa_confirmed": False,
        "r49_p5_human_blind_qa_confirmed_candidate": False,
        "r49_p6_limited_human_readfeel_start_allowed": False,
        "r49_p6_limited_human_readfeel_start_allowed_candidate": False,
        "r49_p8_question_design_material_candidate": False,
        "r49_p7_complete": False,
        "r49_p8_start_allowed": False,
        "r49_release_allowed": False,
        "body_free": True,
    }
    # Confirm the supplied boundary did not silently promote R49 into actual
    # review completion, P8 start, or release readiness.
    expected_true = {
        "r18_touch_candidate_no_touch_boundary_frozen": True,
        "r17_validation_command_matrix_built": True,
    }
    for key, expected in expected_true.items():
        if r49_boundary.get(key) is not expected:
            raise ValueError(f"R50 R0 requires completed R49 handoff marker {key}=True")
    forbidden_true = (
        "actual_human_review_run_here",
        "actual_body_full_packet_generated_here",
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_question_need_observation_summary_materialized_here",
        "actual_disposal_run_here",
        "actual_disposal_receipt_materialized_here",
        "p5_human_blind_qa_confirmed",
        "p5_human_blind_qa_confirmed_candidate",
        "p6_limited_human_readfeel_start_allowed",
        "p6_limited_human_readfeel_start_allowed_candidate",
        "p8_question_design_material_candidate",
        "p7_complete",
        "p8_start_allowed",
        "release_allowed",
    )
    for key in forbidden_true:
        if r49_boundary.get(key) is True:
            raise ValueError(f"R50 R0 cannot accept R49 handoff with {key}=True")
    assert_p7_r50_r49_handoff_contract(handoff)
    return handoff


def _build_p7_p8_bridge_rule() -> dict[str, Any]:
    bridge = {
        "bridge_rule_ref": "p7_p8_bridge_question_need_observation_20260619_r50_refreeze",
        "p7_bridge_only": True,
        "r50_is_manual_run_decision_preparation": True,
        "question_need_observation_memo_only": True,
        "question_need_observation_body_free_required": True,
        "question_need_observation_during_p5_p6_real_device_review_only": True,
        "p8_design_material_candidate_allowed_later": True,
        "p8_detail_design_allowed_here": False,
        "api_db_rn_response_key_change_allowed_here": False,
        "question_trigger_logic_allowed_here": False,
        "question_text_allowed_here": False,
        "draft_question_text_allowed_here": False,
        "emlis_readfeel_weakness_must_not_be_hidden_by_questions": True,
        "p5_surface_weakness_must_not_be_hidden_by_questions": True,
        "gate_boundary_weakness_must_not_be_hidden_by_questions": True,
        "raw_input_or_comment_text_allowed_in_bridge_material": False,
        "returned_surface_allowed_in_bridge_material": False,
        "reviewer_free_text_allowed_in_bridge_material": False,
        "question_text_allowed_in_bridge_material": False,
        "p7_completion_condition_relaxed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "body_free": True,
    }
    bridge.update({key: False for key in P7_R50_QUESTION_IMPLEMENTATION_FALSE_KEY_REFS})
    assert_p7_r50_p7_p8_bridge_rule_contract(bridge)
    return bridge


def _schema_version_refs() -> dict[str, str]:
    return {
        "r50_current_source_r49_handoff_bridge_refreeze": P7_R50_CURRENT_SOURCE_R49_HANDOFF_BRIDGE_REFREEZE_SCHEMA_VERSION,
        "r50_scope_schema_status_enum_freeze": P7_R50_SCOPE_SCHEMA_STATUS_ENUM_FREEZE_SCHEMA_VERSION,
        "r50_r0_r1_scope_status_freeze": P7_R50_R0_R1_SCOPE_STATUS_FREEZE_SCHEMA_VERSION,
        "r50_prior_validation_evidence_adoption": P7_R50_PRIOR_VALIDATION_EVIDENCE_ADOPTION_SCHEMA_VERSION,
        "r50_manual_run_decision_bodyfree": P7_R50_MANUAL_RUN_DECISION_BODYFREE_SCHEMA_VERSION,
        "r50_r2_r3_manual_run_decision_freeze": P7_R50_R2_R3_MANUAL_RUN_DECISION_FREEZE_SCHEMA_VERSION,
        "r50_local_only_root_explicit_allow_export_preflight": P7_R50_LOCAL_ONLY_ROOT_EXPLICIT_ALLOW_EXPORT_PREFLIGHT_SCHEMA_VERSION,
        "r50_review_session_protocol_bodyfree": P7_R50_REVIEW_SESSION_PROTOCOL_BODYFREE_SCHEMA_VERSION,
        "r50_r4_r5_preflight_protocol_freeze": P7_R50_R4_R5_PREFLIGHT_PROTOCOL_FREEZE_SCHEMA_VERSION,
        "r50_local_only_body_full_packet_generation_request": P7_R50_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION,
        "r50_reviewer_instruction_rating_form_freeze": P7_R50_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION,
        "r50_r6_r7_packet_request_rating_form_freeze": P7_R50_R6_R7_PACKET_REQUEST_RATING_FORM_FREEZE_SCHEMA_VERSION,
        "r50_rating_capture_row_bodyfree": P7_R50_RATING_CAPTURE_ROW_BODYFREE_SCHEMA_VERSION,
        "r50_readfeel_blocker_row_bodyfree": P7_R50_READFEEL_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "r50_execution_blocker_row_bodyfree": P7_R50_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "r50_rating_row_normalizer_bodyfree": P7_R50_RATING_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION,
        "r50_readfeel_execution_blocker_ingestion_bodyfree": P7_R50_READFEEL_EXECUTION_BLOCKER_INGESTION_BODYFREE_SCHEMA_VERSION,
        "r50_r8_r9_rating_blocker_ingestion_freeze": P7_R50_R8_R9_RATING_BLOCKER_INGESTION_FREEZE_SCHEMA_VERSION,
        "r50_question_need_observation_row_bodyfree": P7_R50_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION,
        "r50_question_observation_row_normalizer_bodyfree": P7_R50_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION,
        "r50_rating_question_observation_consistency_guard_bodyfree": P7_R50_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_BODYFREE_SCHEMA_VERSION,
        "r50_r10_r11_question_observation_consistency_freeze": P7_R50_R10_R11_QUESTION_OBSERVATION_CONSISTENCY_FREEZE_SCHEMA_VERSION,
        "r50_r10_r11_question_normalizer_consistency_guard_freeze": P7_R50_R10_R11_QUESTION_NORMALIZER_CONSISTENCY_GUARD_FREEZE_SCHEMA_VERSION,
        "r50_pause_abort_expiration_protocol_bodyfree": P7_R50_PAUSE_ABORT_EXPIRATION_PROTOCOL_BODYFREE_SCHEMA_VERSION,
        "r50_disposal_receipt_bodyfree": P7_R50_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION,
        "r50_disposal_receipt_builder_verifier_bodyfree": P7_R50_DISPOSAL_RECEIPT_BUILDER_VERIFIER_BODYFREE_SCHEMA_VERSION,
        "r50_r12_r13_disposal_protocol_freeze": P7_R50_R12_R13_DISPOSAL_PROTOCOL_FREEZE_SCHEMA_VERSION,
        "r50_body_free_post_review_summary_bodyfree": P7_R50_BODY_FREE_POST_REVIEW_SUMMARY_BODYFREE_SCHEMA_VERSION,
        "r50_p5_confirmed_repair_inconclusive_decision_bodyfree": P7_R50_P5_CONFIRMED_REPAIR_INCONCLUSIVE_DECISION_BODYFREE_SCHEMA_VERSION,
        "r50_r14_r15_post_review_decision_freeze": P7_R50_R14_R15_POST_REVIEW_DECISION_FREEZE_SCHEMA_VERSION,
        "r49_touch_candidate_no_touch_boundary_freeze": P7_R49_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION,
        "r49_question_need_observation_row_bodyfree": P7_R49_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION,
        "r49_question_need_observation_summary_bodyfree": P7_R49_QUESTION_NEED_OBSERVATION_SUMMARY_BODYFREE_SCHEMA_VERSION,
        "r49_review_handoff_summary_bodyfree": P7_R49_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION,
        "r49_no_body_leak_no_question_text_guard": P7_R49_NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_SCHEMA_VERSION,
    }


def assert_p7_r50_r49_handoff_contract(handoff: Mapping[str, Any]) -> bool:
    data = safe_mapping(handoff)
    _assert_required_fields(data, required=P7_R50_R49_HANDOFF_REQUIRED_FIELD_REFS, source="p7_r50.r49_handoff")
    if data.get("r49_handoff_required") is not True:
        raise ValueError("R50 R49 handoff must be required")
    if data.get("r49_step") != P7_R49_STEP or data.get("r49_scope") != P7_R49_SCOPE:
        raise ValueError("R50 R49 handoff step/scope changed")
    if data.get("r49_packet_kind") != P7_R50_PACKET_KIND or data.get("r49_review_kind") != P7_R50_REVIEW_KIND:
        raise ValueError("R50 R49 handoff packet/review kind changed")
    if tuple(data.get("r49_completed_steps") or ()) != P7_R49_R18_IMPLEMENTED_STEPS:
        raise ValueError("R50 R49 handoff must preserve R49 R18 completed steps")
    if tuple(data.get("r49_implemented_steps") or ()) != P7_R49_R18_IMPLEMENTED_STEPS:
        raise ValueError("R50 R49 handoff must preserve R49 R18 implemented steps")
    if tuple(data.get("r49_not_yet_implemented_steps") or ()) != P7_R49_R18_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R49 handoff must preserve empty R49 not-yet list")
    if data.get("r49_next_required_step") != P7_R49_R18_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R50 R49 handoff must point to manual run decision")
    for true_key in (
        "r49_actual_review_execution_scaffold_finished",
        "r49_question_need_observation_capture_footing_ready",
        "r49_touch_no_touch_boundary_frozen",
        "body_free",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R50 R49 handoff must keep {true_key}=True")
    for false_key in (
        "r49_actual_review_completed",
        "r49_actual_human_review_run",
        "r49_body_full_packet_generated",
        "r49_rating_rows_materialized",
        "r49_question_need_observation_rows_materialized",
        "r49_question_need_observation_summary_materialized",
        "r49_disposal_run",
        "r49_disposal_receipt_materialized",
        "r49_p5_human_blind_qa_confirmed",
        "r49_p5_human_blind_qa_confirmed_candidate",
        "r49_p6_limited_human_readfeel_start_allowed",
        "r49_p6_limited_human_readfeel_start_allowed_candidate",
        "r49_p8_question_design_material_candidate",
        "r49_p7_complete",
        "r49_p8_start_allowed",
        "r49_release_allowed",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R50 R49 handoff must keep {false_key}=False")
    return True


def assert_p7_r50_p7_p8_bridge_rule_contract(bridge: Mapping[str, Any]) -> bool:
    data = safe_mapping(bridge)
    _assert_required_fields(data, required=P7_R50_BRIDGE_RULE_REQUIRED_FIELD_REFS, source="p7_r50.p7_p8_bridge_rule")
    for true_key in (
        "p7_bridge_only",
        "r50_is_manual_run_decision_preparation",
        "question_need_observation_memo_only",
        "question_need_observation_body_free_required",
        "question_need_observation_during_p5_p6_real_device_review_only",
        "p8_design_material_candidate_allowed_later",
        "emlis_readfeel_weakness_must_not_be_hidden_by_questions",
        "p5_surface_weakness_must_not_be_hidden_by_questions",
        "gate_boundary_weakness_must_not_be_hidden_by_questions",
        "body_free",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R50 bridge rule must keep {true_key}=True")
    for false_key in (
        *P7_R50_QUESTION_IMPLEMENTATION_FALSE_KEY_REFS,
        "p8_detail_design_allowed_here",
        "api_db_rn_response_key_change_allowed_here",
        "question_trigger_logic_allowed_here",
        "question_text_allowed_here",
        "draft_question_text_allowed_here",
        "raw_input_or_comment_text_allowed_in_bridge_material",
        "returned_surface_allowed_in_bridge_material",
        "reviewer_free_text_allowed_in_bridge_material",
        "question_text_allowed_in_bridge_material",
        "p7_completion_condition_relaxed",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R50 bridge rule must keep {false_key}=False")
    return True


def build_p7_r50_current_source_r49_handoff_bridge_refreeze(
    *,
    snapshot_refs: Mapping[str, Any] | None = None,
    r49_handoff: Mapping[str, Any] | None = None,
    r49_handoff_boundary: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r50_current_source_r49_handoff_bridge_refreeze",
) -> dict[str, Any]:
    """Build the R50-0 body-free current-source/R49-handoff refreeze."""

    if r49_handoff is not None and r49_handoff_boundary is not None:
        raise ValueError("provide only one R49 handoff value")
    boundary = r49_handoff if r49_handoff is not None else r49_handoff_boundary
    r49_handoff_summary = _build_r49_handoff(_r49_boundary(boundary))
    refreeze = {
        "schema_version": P7_R50_CURRENT_SOURCE_R49_HANDOFF_BRIDGE_REFREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R50_STEP,
        "scope": P7_R50_SCOPE,
        "policy_kind": P7_R50_POLICY_KIND,
        "policy_section": "R50-0_current_source_r49_handoff_p7_p8_bridge_refreeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r50_current_source_r49_handoff_bridge_refreeze", max_length=180),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": P7_GIT_CHECKED,
        "source_snapshot_refs": _safe_snapshot_refs(snapshot_refs),
        "r49_handoff": r49_handoff_summary,
        "p7_p8_bridge_rule": _build_p7_p8_bridge_rule(),
        "implemented_steps": list(P7_R50_R0_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R50_R0_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r49_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": False,
        "manual_run_decision_required_later": True,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "first_next_work_ref": P7_R50_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R50_R0_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r50_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r50_current_source_r49_handoff_bridge_refreeze_contract(refreeze)
    return refreeze


def build_p7_r50_current_source_r49_handoff_refreeze(**kwargs: Any) -> dict[str, Any]:
    """Compatibility alias for the R50-0 builder named in the design note."""

    return build_p7_r50_current_source_r49_handoff_bridge_refreeze(**kwargs)


def build_p7_r50_scope_schema_status_enum_freeze(
    *,
    review_session_id: Any = P7_R50_DEFAULT_REVIEW_SESSION_ID,
    review_session_status: Any = P7_R50_INITIAL_REVIEW_SESSION_STATUS_REF,
    current_source_refreeze: Mapping[str, Any] | None = None,
    current_source_r49_handoff_bridge_refreeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r50_scope_schema_status_enum_freeze",
) -> dict[str, Any]:
    """Build the R50-1 body-free scope/schema/status/enum freeze."""

    if current_source_refreeze is not None and current_source_r49_handoff_bridge_refreeze is not None:
        raise ValueError("provide only one R50-0 refreeze value")
    r0 = (
        safe_mapping(current_source_refreeze)
        if current_source_refreeze is not None
        else safe_mapping(current_source_r49_handoff_bridge_refreeze)
        if current_source_r49_handoff_bridge_refreeze is not None
        else build_p7_r50_current_source_r49_handoff_bridge_refreeze()
    )
    assert_p7_r50_current_source_r49_handoff_bridge_refreeze_contract(r0)

    freeze = {
        "schema_version": P7_R50_SCOPE_SCHEMA_STATUS_ENUM_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R50_STEP,
        "scope": P7_R50_SCOPE,
        "policy_kind": P7_R50_POLICY_KIND,
        "policy_section": "R50-1_scope_schema_version_status_enum_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r50_scope_schema_status_enum_freeze", max_length=180),
        "review_session_id": _safe_review_session_id(review_session_id),
        "review_kind": P7_R50_REVIEW_KIND,
        "packet_kind": P7_R50_PACKET_KIND,
        "r0_schema_version": P7_R50_CURRENT_SOURCE_R49_HANDOFF_BRIDGE_REFREEZE_SCHEMA_VERSION,
        "r0_refreeze_material_ref": clean_identifier(r0.get("material_id"), default="p7_r50_current_source_r49_handoff_bridge_refreeze", max_length=180),
        "r49_handoff_required": True,
        "required_case_count": P7_R50_REQUIRED_CASE_COUNT,
        "review_session_status": _safe_review_session_status(review_session_status),
        "review_session_status_refs": list(P7_R50_REVIEW_SESSION_STATUS_REFS),
        "manual_run_decision_refs": list(P7_R50_MANUAL_RUN_DECISION_REFS),
        "execution_blocker_id_refs": list(P7_R50_EXECUTION_BLOCKER_ID_REFS),
        "execution_blocker_status_refs": list(P7_R50_EXECUTION_BLOCKER_STATUS_REFS),
        "question_need_primary_class_refs": list(P7_R50_QUESTION_NEED_PRIMARY_CLASS_REFS),
        "ambiguity_kind_refs": list(P7_R50_AMBIGUITY_KIND_REFS),
        "one_question_fit_refs": list(P7_R50_ONE_QUESTION_FIT_REFS),
        "repair_required_ref_refs": list(P7_R50_REPAIR_REQUIRED_REF_REFS),
        "schema_version_refs": _schema_version_refs(),
        "r49_touch_boundary_schema_version": P7_R49_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION,
        "r49_question_need_observation_row_bodyfree_schema_version": P7_R49_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION,
        "r49_question_need_observation_summary_bodyfree_schema_version": P7_R49_QUESTION_NEED_OBSERVATION_SUMMARY_BODYFREE_SCHEMA_VERSION,
        "r49_review_handoff_summary_bodyfree_schema_version": P7_R49_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION,
        "r49_no_body_leak_guard_schema_version": P7_R49_NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_SCHEMA_VERSION,
        "r49_p6_candidate_handoff_schema_version": P7_R49_P6_LIMITED_HUMAN_READFEEL_START_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        "r49_p8_material_candidate_handoff_schema_version": P7_R49_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        "r48_reviewer_packet_local_only_schema_version": P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION,
        "r48_rating_row_bodyfree_schema_version": P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION,
        "r48_blocker_row_bodyfree_schema_version": P7_R48_P5_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "r48_execution_blocker_row_bodyfree_schema_version": P7_R48_P5_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "r48_disposal_receipt_bodyfree_schema_version": P7_R48_P5_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION,
        "r48_review_handoff_summary_bodyfree_schema_version": P7_R48_P5_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION,
        "r48_p5_first_formal_case_distribution": [list(row) for row in P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION],
        "r48_readfeel_blocker_id_refs": list(P7_R48_READFEEL_BLOCKER_ID_REFS),
        "r47_local_review_root_env_var": P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR,
        "r47_disposal_status_refs": list(P7_R47_DISPOSAL_STATUSES),
        "r47_body_full_packet_retention_hours": P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
        "r47_reviewer_notes_retention_after_rating_hours": P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
        "r47_p5_first_formal_minimums": dict(P7_R47_P5_FIRST_FORMAL_MINIMUMS),
        "scope_fixed": True,
        "schema_versions_fixed": True,
        "status_enum_fixed": True,
        "manual_run_decision_enum_fixed": True,
        "execution_blocker_enum_fixed": True,
        "question_need_observation_enum_inherited_from_r49": True,
        "manual_run_decision_made_here": False,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "p8_question_detail_design_in_scope": False,
        "api_db_rn_response_key_changed_here": False,
        "implemented_steps": list(P7_R50_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R50_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r49_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "first_next_work_ref": P7_R50_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R50_R1_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r50_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r50_scope_schema_status_enum_freeze_contract(freeze)
    return freeze


def build_p7_r50_r0_r1_scope_status_freeze(
    *,
    snapshot_refs: Mapping[str, Any] | None = None,
    r49_handoff: Mapping[str, Any] | None = None,
    r49_handoff_boundary: Mapping[str, Any] | None = None,
    review_session_id: Any = P7_R50_DEFAULT_REVIEW_SESSION_ID,
    review_session_status: Any = P7_R50_INITIAL_REVIEW_SESSION_STATUS_REF,
    material_id: Any = "p7_r50_r0_r1_scope_status_freeze",
) -> dict[str, Any]:
    """Build a compact body-free combined R50-0/R50-1 freeze."""

    if r49_handoff is not None and r49_handoff_boundary is not None:
        raise ValueError("provide only one R49 handoff value")
    r0 = build_p7_r50_current_source_r49_handoff_bridge_refreeze(
        snapshot_refs=snapshot_refs,
        r49_handoff=r49_handoff if r49_handoff is not None else r49_handoff_boundary,
    )
    r1 = build_p7_r50_scope_schema_status_enum_freeze(
        review_session_id=review_session_id,
        review_session_status=review_session_status,
        current_source_refreeze=r0,
    )
    combined = {
        "schema_version": P7_R50_R0_R1_SCOPE_STATUS_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R50_STEP,
        "scope": P7_R50_SCOPE,
        "policy_kind": P7_R50_POLICY_KIND,
        "policy_section": "R50-0_R50-1_scope_status_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r50_r0_r1_scope_status_freeze", max_length=180),
        "r0_current_source_r49_handoff_bridge_refreeze": r0,
        "r1_scope_schema_status_enum_freeze": r1,
        "review_session_id": r1["review_session_id"],
        "review_session_status": r1["review_session_status"],
        "review_session_status_refs": list(P7_R50_REVIEW_SESSION_STATUS_REFS),
        "manual_run_decision_refs": list(P7_R50_MANUAL_RUN_DECISION_REFS),
        "execution_blocker_id_refs": list(P7_R50_EXECUTION_BLOCKER_ID_REFS),
        "required_case_count": P7_R50_REQUIRED_CASE_COUNT,
        "implemented_steps": list(P7_R50_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R50_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r49_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "manual_run_decision_required_later": True,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "first_next_work_ref": P7_R50_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R50_R1_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r50_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r50_r0_r1_scope_status_freeze_contract(combined)
    return combined


def assert_p7_r50_current_source_r49_handoff_bridge_refreeze_contract(refreeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(refreeze)
    _assert_required_fields(
        data,
        required=P7_R50_CURRENT_SOURCE_R49_HANDOFF_BRIDGE_REFREEZE_REQUIRED_FIELD_REFS,
        source="p7_r50_r0_refreeze",
    )
    _assert_common(
        data,
        schema_version=P7_R50_CURRENT_SOURCE_R49_HANDOFF_BRIDGE_REFREEZE_SCHEMA_VERSION,
        source="p7_r50_r0_refreeze",
    )
    if data.get("policy_section") != "R50-0_current_source_r49_handoff_p7_p8_bridge_refreeze":
        raise ValueError("R50 R0 policy section changed")
    if data.get("source_mode") != P7_SOURCE_MODE:
        raise ValueError("R50 R0 must remain local snapshot source mode")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError("R50 R0 must not require or claim Git checking")
    assert_p7_r50_r49_handoff_contract(safe_mapping(data.get("r49_handoff")))
    assert_p7_r50_p7_p8_bridge_rule_contract(safe_mapping(data.get("p7_p8_bridge_rule")))
    if tuple(data.get("implemented_steps") or ()) != P7_R50_R0_IMPLEMENTED_STEPS:
        raise ValueError("R50 R0 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_R0_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R0 not-yet steps changed")
    if data.get("r0_current_source_r49_handoff_bridge_refrozen") is not True:
        raise ValueError("R50 R0 marker must be true")
    if data.get("r1_scope_schema_status_enum_fixed") is not False:
        raise ValueError("R50 R0 must not mark R1 as fixed")
    if data.get("manual_run_decision_required_later") is not True:
        raise ValueError("R50 R0 must leave manual-run decision for later")
    if data.get("actual_manual_review_run_here") is not False:
        raise ValueError("R50 R0 must not run actual manual review")
    if data.get("body_full_packet_generated_here") is not False:
        raise ValueError("R50 R0 must not generate body-full packets")
    if data.get("next_required_step") != P7_R50_R0_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R50 R0 must point to R50-1 next")
    return True


def assert_p7_r50_scope_schema_status_enum_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_required_fields(
        data,
        required=P7_R50_SCOPE_SCHEMA_STATUS_ENUM_FREEZE_REQUIRED_FIELD_REFS,
        source="p7_r50_r1_scope_schema_status_enum_freeze",
    )
    _assert_common(
        data,
        schema_version=P7_R50_SCOPE_SCHEMA_STATUS_ENUM_FREEZE_SCHEMA_VERSION,
        source="p7_r50_r1_scope_schema_status_enum_freeze",
    )
    if data.get("policy_section") != "R50-1_scope_schema_version_status_enum_freeze":
        raise ValueError("R50 R1 policy section changed")
    if data.get("r0_schema_version") != P7_R50_CURRENT_SOURCE_R49_HANDOFF_BRIDGE_REFREEZE_SCHEMA_VERSION:
        raise ValueError("R50 R1 must reference R0 schema")
    if data.get("review_kind") != P7_R50_REVIEW_KIND or data.get("packet_kind") != P7_R50_PACKET_KIND:
        raise ValueError("R50 R1 review/packet kind changed")
    if data.get("required_case_count") != P7_R50_REQUIRED_CASE_COUNT:
        raise ValueError("R50 R1 must keep required_case_count=24")
    if data.get("review_session_status") != P7_R50_INITIAL_REVIEW_SESSION_STATUS_REF:
        raise ValueError("R50 R1 review session must remain NOT_STARTED")
    if tuple(data.get("review_session_status_refs") or ()) != P7_R50_REVIEW_SESSION_STATUS_REFS:
        raise ValueError("R50 R1 review status enum changed")
    if tuple(data.get("manual_run_decision_refs") or ()) != P7_R50_MANUAL_RUN_DECISION_REFS:
        raise ValueError("R50 R1 manual-run decision enum changed")
    if tuple(data.get("execution_blocker_id_refs") or ()) != P7_R50_EXECUTION_BLOCKER_ID_REFS:
        raise ValueError("R50 R1 execution blocker ids changed")
    if tuple(data.get("execution_blocker_status_refs") or ()) != P7_R50_EXECUTION_BLOCKER_STATUS_REFS:
        raise ValueError("R50 R1 execution blocker status enum changed")
    if tuple(data.get("question_need_primary_class_refs") or ()) != P7_R50_QUESTION_NEED_PRIMARY_CLASS_REFS:
        raise ValueError("R50 R1 question need primary class refs changed")
    if tuple(data.get("ambiguity_kind_refs") or ()) != P7_R50_AMBIGUITY_KIND_REFS:
        raise ValueError("R50 R1 ambiguity refs changed")
    if tuple(data.get("one_question_fit_refs") or ()) != P7_R50_ONE_QUESTION_FIT_REFS:
        raise ValueError("R50 R1 one-question fit refs changed")
    if tuple(data.get("repair_required_ref_refs") or ()) != P7_R50_REPAIR_REQUIRED_REF_REFS:
        raise ValueError("R50 R1 repair-required refs changed")
    if safe_mapping(data.get("schema_version_refs")) != _schema_version_refs():
        raise ValueError("R50 R1 schema version refs changed")
    if tuple(tuple(row) for row in data.get("r48_p5_first_formal_case_distribution") or ()) != P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION:
        raise ValueError("R50 R1 R48 first formal case distribution changed")
    if tuple(data.get("r48_readfeel_blocker_id_refs") or ()) != P7_R48_READFEEL_BLOCKER_ID_REFS:
        raise ValueError("R50 R1 R48 readfeel blocker ids changed")
    if data.get("r47_local_review_root_env_var") != P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR:
        raise ValueError("R50 R1 local review root env var changed")
    if tuple(data.get("r47_disposal_status_refs") or ()) != P7_R47_DISPOSAL_STATUSES:
        raise ValueError("R50 R1 disposal status refs changed")
    if safe_mapping(data.get("r47_p5_first_formal_minimums")) != dict(P7_R47_P5_FIRST_FORMAL_MINIMUMS):
        raise ValueError("R50 R1 P5 first formal minimums changed")
    for true_key in (
        "r49_handoff_required",
        "scope_fixed",
        "schema_versions_fixed",
        "status_enum_fixed",
        "manual_run_decision_enum_fixed",
        "execution_blocker_enum_fixed",
        "question_need_observation_enum_inherited_from_r49",
        "r0_current_source_r49_handoff_bridge_refrozen",
        "r1_scope_schema_status_enum_fixed",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R50 R1 must keep {true_key}=True")
    for false_key in (
        "manual_run_decision_made_here",
        "actual_manual_review_run_here",
        "body_full_packet_generated_here",
        "p8_question_detail_design_in_scope",
        "api_db_rn_response_key_changed_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R50 R1 must keep {false_key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R50_IMPLEMENTED_STEPS:
        raise ValueError("R50 R1 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R1 not-yet steps changed")
    if data.get("next_required_step") != P7_R50_R1_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R50 R1 must point to R50-2 next")
    return True


def assert_p7_r50_r0_r1_scope_status_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_required_fields(
        data,
        required=P7_R50_R0_R1_SCOPE_STATUS_FREEZE_REQUIRED_FIELD_REFS,
        source="p7_r50_r0_r1_scope_status_freeze",
    )
    _assert_common(
        data,
        schema_version=P7_R50_R0_R1_SCOPE_STATUS_FREEZE_SCHEMA_VERSION,
        source="p7_r50_r0_r1_scope_status_freeze",
    )
    if data.get("policy_section") != "R50-0_R50-1_scope_status_freeze":
        raise ValueError("R50 R0/R1 policy section changed")
    assert_p7_r50_current_source_r49_handoff_bridge_refreeze_contract(
        safe_mapping(data.get("r0_current_source_r49_handoff_bridge_refreeze"))
    )
    assert_p7_r50_scope_schema_status_enum_freeze_contract(
        safe_mapping(data.get("r1_scope_schema_status_enum_freeze"))
    )
    if tuple(data.get("implemented_steps") or ()) != P7_R50_IMPLEMENTED_STEPS:
        raise ValueError("R50 R0/R1 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R0/R1 not-yet steps changed")
    if data.get("review_session_status") != P7_R50_INITIAL_REVIEW_SESSION_STATUS_REF:
        raise ValueError("R50 R0/R1 review session must remain NOT_STARTED")
    if tuple(data.get("review_session_status_refs") or ()) != P7_R50_REVIEW_SESSION_STATUS_REFS:
        raise ValueError("R50 R0/R1 review status enum changed")
    if tuple(data.get("manual_run_decision_refs") or ()) != P7_R50_MANUAL_RUN_DECISION_REFS:
        raise ValueError("R50 R0/R1 manual run decision enum changed")
    if tuple(data.get("execution_blocker_id_refs") or ()) != P7_R50_EXECUTION_BLOCKER_ID_REFS:
        raise ValueError("R50 R0/R1 execution blocker enum changed")
    if data.get("required_case_count") != P7_R50_REQUIRED_CASE_COUNT:
        raise ValueError("R50 R0/R1 required case count changed")
    if data.get("r0_current_source_r49_handoff_bridge_refrozen") is not True:
        raise ValueError("R50 R0/R1 must keep R0 marker true")
    if data.get("r1_scope_schema_status_enum_fixed") is not True:
        raise ValueError("R50 R0/R1 must keep R1 marker true")
    if data.get("manual_run_decision_required_later") is not True:
        raise ValueError("R50 R0/R1 must require manual run decision later")
    if data.get("actual_manual_review_run_here") is not False:
        raise ValueError("R50 R0/R1 must not run actual manual review")
    if data.get("body_full_packet_generated_here") is not False:
        raise ValueError("R50 R0/R1 must not generate body-full packets")
    if data.get("next_required_step") != P7_R50_R1_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R50 R0/R1 must point to R50-2 next")
    return True


def _false_flags_for(keys: Sequence[str]) -> dict[str, bool]:
    return {key: False for key in keys}


def _assert_false_flags_for(data: Mapping[str, Any], *, false_keys: Sequence[str], source: str) -> None:
    for key in false_keys:
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=False")


def _assert_common_with_false_keys(
    data: Mapping[str, Any], *, schema_version: str, source: str, false_keys: Sequence[str]
) -> None:
    if data.get("schema_version") != schema_version:
        raise ValueError(f"{source} schema version changed")
    if data.get("phase") != P7_PHASE:
        raise ValueError(f"{source} phase changed")
    if data.get("step") != P7_R50_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R50_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("policy_kind") != P7_R50_POLICY_KIND:
        raise ValueError(f"{source} policy kind changed")
    if data.get("current_phase") != "P7":
        raise ValueError(f"{source} must remain in P7")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must be body_free=True")
    _assert_false_flags_for(data, false_keys=false_keys, source=source)
    _assert_no_forbidden_body_keys(data, source=source)
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)
    assert_false_markers(safe_mapping(data.get("public_contract")), source=f"{source}.public_contract")
    assert_false_markers(safe_mapping(data.get("r50_public_no_touch_contract")), source=f"{source}.r50_public_no_touch_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source=f"{source}.body_free_markers")


def _bool_ref(value: Any, *, default: bool = False) -> bool:
    return value if isinstance(value, bool) else default


def _non_negative_int(value: Any, *, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return number if number >= 0 else default


def _evidence_row(
    *,
    evidence_group_ref: str,
    evidence_status_ref: str,
    evidence_present: bool,
    passed_count: int = 0,
    collected_count: int = 0,
    warning_count: int = 0,
    required_for_manual_run_go: bool = True,
    optional: bool = False,
    test_file_refs: Sequence[Any] = (),
    evidence_source_ref: str = "r50_prior_validation_evidence_adoption",
    claim_boundary_ref: str,
) -> dict[str, Any]:
    row = {
        "evidence_group_ref": clean_identifier(evidence_group_ref, default="unknown_validation_group", max_length=120),
        "evidence_status_ref": clean_identifier(evidence_status_ref, default="UNKNOWN", max_length=80),
        "evidence_present": bool(evidence_present),
        "passed_count": _non_negative_int(passed_count),
        "collected_count": _non_negative_int(collected_count),
        "warning_count": _non_negative_int(warning_count),
        "required_for_manual_run_go": bool(required_for_manual_run_go),
        "optional": bool(optional),
        "test_file_refs": dedupe_identifiers(test_file_refs, limit=80, max_length=220),
        "evidence_source_ref": clean_identifier(evidence_source_ref, default="r50_prior_validation_evidence_adoption", max_length=180),
        "claim_boundary_ref": clean_identifier(claim_boundary_ref, default="validation evidence only", max_length=220),
        "evidence_created_here": False,
        "validation_commands_executed_here": False,
        "command_result_body_stored_here": False,
        "terminal_output_stored_here": False,
        "body_free": True,
    }
    assert_p7_r50_prior_validation_evidence_row_contract(row)
    return row


def _default_prior_validation_evidence_rows() -> list[dict[str, Any]]:
    return [
        _evidence_row(
            evidence_group_ref="r50_r0_r1_current_implementation",
            evidence_status_ref="PASSED",
            evidence_present=True,
            passed_count=6,
            test_file_refs=("tests/test_emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision_r0_r1_20260620.py",),
            evidence_source_ref="mashos-api_2(102).zip_current_upload_verified_locally",
            claim_boundary_ref="R50-0/R50-1 helper presence and target only; not manual-review GO or product value",
        ),
        _evidence_row(
            evidence_group_ref="r49_target",
            evidence_status_ref="PASSED_BY_SPLIT_EXECUTION",
            evidence_present=True,
            passed_count=76,
            test_file_refs=P7_R49_VALIDATION_R49_TARGET_TEST_FILE_REFS,
            evidence_source_ref="R50_pre_design_memo_20260620_prior_local_validation",
            claim_boundary_ref="R49 helper contract only; not P5 actual human review completion",
        ),
        _evidence_row(
            evidence_group_ref="r48_regression",
            evidence_status_ref="PASSED",
            evidence_present=True,
            passed_count=82,
            test_file_refs=P7_R49_VALIDATION_R48_REGRESSION_TEST_FILE_REFS,
            evidence_source_ref="R50_pre_design_memo_20260620_prior_local_validation",
            claim_boundary_ref="R48 review-packet regression only; not P5 confirmed",
        ),
        _evidence_row(
            evidence_group_ref="r47_regression",
            evidence_status_ref="PASSED",
            evidence_present=True,
            passed_count=275,
            test_file_refs=P7_R49_VALIDATION_R47_REGRESSION_TEST_FILE_REFS,
            evidence_source_ref="R50_pre_design_memo_20260620_prior_local_validation",
            claim_boundary_ref="R47 local-only/body-free policy regression only",
        ),
        _evidence_row(
            evidence_group_ref="r46_handoff_regression",
            evidence_status_ref="PASSED",
            evidence_present=True,
            passed_count=19,
            test_file_refs=P7_R49_VALIDATION_R46_HANDOFF_TEST_FILE_REFS,
            evidence_source_ref="R50_pre_design_memo_20260620_prior_local_validation",
            claim_boundary_ref="R46 P5/P6 handoff regression only; not P6 start permission",
        ),
        _evidence_row(
            evidence_group_ref="display_p5_core_subset",
            evidence_status_ref="PASSED_WITH_KNOWN_WARNING",
            evidence_present=True,
            passed_count=68,
            warning_count=1,
            test_file_refs=(
                *P7_R49_VALIDATION_DISPLAY_API_TEST_FILE_REFS,
                *P7_R49_VALIDATION_P5_CORE_TEST_FILE_REFS,
            ),
            evidence_source_ref="R50_pre_design_memo_20260620_prior_local_validation",
            claim_boundary_ref="Display/P5 core subset only; not real-device modal readfeel or full backend suite green",
        ),
        _evidence_row(
            evidence_group_ref="backend_collect_only",
            evidence_status_ref="COLLECT_ONLY_PASSED_WITH_KNOWN_WARNING",
            evidence_present=True,
            collected_count=3367,
            warning_count=1,
            required_for_manual_run_go=False,
            test_file_refs=("pytest --collect-only -q",),
            evidence_source_ref="R50_pre_design_memo_20260620_prior_local_validation",
            claim_boundary_ref="collect-only only; must not be claimed as full backend suite execution green",
        ),
        _evidence_row(
            evidence_group_ref="rn_no_touch_optional",
            evidence_status_ref="PASSED_OPTIONAL_NO_TOUCH",
            evidence_present=True,
            passed_count=36,
            optional=True,
            test_file_refs=P7_R49_RN_CONTRACT_OPTIONAL_NO_TOUCH_TEST_REFS,
            evidence_source_ref="R50_pre_design_memo_20260620_prior_local_validation",
            claim_boundary_ref="RN contract only; not real-device modal readfeel",
        ),
    ]


def _prior_validation_rows_with_overrides(overrides: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    rows = _default_prior_validation_evidence_rows()
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
            "required_for_manual_run_go",
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
                evidence_status_ref=clean_identifier(merged.get("evidence_status_ref"), default="UNKNOWN", max_length=80),
                evidence_present=_bool_ref(merged.get("evidence_present")),
                passed_count=_non_negative_int(merged.get("passed_count")),
                collected_count=_non_negative_int(merged.get("collected_count")),
                warning_count=_non_negative_int(merged.get("warning_count")),
                required_for_manual_run_go=_bool_ref(merged.get("required_for_manual_run_go"), default=True),
                optional=_bool_ref(merged.get("optional")),
                test_file_refs=merged.get("test_file_refs") if isinstance(merged.get("test_file_refs"), Sequence) else row["test_file_refs"],
                evidence_source_ref=clean_identifier(merged.get("evidence_source_ref"), default="r50_prior_validation_evidence_adoption", max_length=180),
                claim_boundary_ref=clean_identifier(merged.get("claim_boundary_ref"), default="validation evidence only", max_length=220),
            )
        )
    return out


def _prior_validation_flags(rows: Sequence[Mapping[str, Any]]) -> dict[str, bool]:
    by_group = {str(row.get("evidence_group_ref")): row for row in rows}
    return {
        "r50_r0_r1_current_implementation_evidence_present": by_group.get("r50_r0_r1_current_implementation", {}).get("evidence_present") is True,
        "r49_target_green_evidence_present": by_group.get("r49_target", {}).get("evidence_present") is True,
        "r48_regression_green_evidence_present": by_group.get("r48_regression", {}).get("evidence_present") is True,
        "r47_regression_green_evidence_present": by_group.get("r47_regression", {}).get("evidence_present") is True,
        "r46_regression_green_evidence_present": by_group.get("r46_handoff_regression", {}).get("evidence_present") is True,
        "display_p5_core_green_evidence_present": by_group.get("display_p5_core_subset", {}).get("evidence_present") is True,
        "rn_contract_green_evidence_present": by_group.get("rn_no_touch_optional", {}).get("evidence_present") is True,
        "backend_collect_only_evidence_present": by_group.get("backend_collect_only", {}).get("evidence_present") is True,
        "full_backend_suite_green_confirmed": False,
        "collect_only_claimed_as_full_backend_green": False,
        "rn_contract_claimed_as_real_device_modal_readfeel": False,
    }


def assert_p7_r50_prior_validation_evidence_row_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R50_PRIOR_VALIDATION_EVIDENCE_ROW_REQUIRED_FIELD_REFS, source="p7_r50_prior_validation_evidence_row")
    if data.get("evidence_group_ref") not in P7_R50_PRIOR_VALIDATION_EVIDENCE_GROUP_REFS:
        raise ValueError("R50 R2 evidence group ref is not canonical")
    for int_key in ("passed_count", "collected_count", "warning_count"):
        if not isinstance(data.get(int_key), int) or data[int_key] < 0:
            raise ValueError(f"R50 R2 evidence row must keep non-negative {int_key}")
    for false_key in ("evidence_created_here", "validation_commands_executed_here", "command_result_body_stored_here", "terminal_output_stored_here"):
        if data.get(false_key) is not False:
            raise ValueError(f"R50 R2 evidence row must keep {false_key}=False")
    if data.get("body_free") is not True:
        raise ValueError("R50 R2 evidence row must be body-free")
    _assert_no_forbidden_body_keys(data, source="p7_r50_prior_validation_evidence_row")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r50_prior_validation_evidence_row")
    return True


def build_p7_r50_prior_validation_evidence_adoption(
    *,
    scope_schema_status_enum_freeze: Mapping[str, Any] | None = None,
    r1_scope_schema_status_enum_freeze: Mapping[str, Any] | None = None,
    prior_validation_evidence_overrides: Mapping[str, Any] | None = None,
    current_working_backend_zip_ref: Any = "mashos-api_2(102).zip",
    material_id: Any = "p7_r50_prior_validation_evidence_adoption",
) -> dict[str, Any]:
    """Adopt prior validation evidence as body-free R50-2 decision material."""

    if scope_schema_status_enum_freeze is not None and r1_scope_schema_status_enum_freeze is not None:
        raise ValueError("provide only one R50-1 freeze value")
    r1 = (
        safe_mapping(scope_schema_status_enum_freeze)
        if scope_schema_status_enum_freeze is not None
        else safe_mapping(r1_scope_schema_status_enum_freeze)
        if r1_scope_schema_status_enum_freeze is not None
        else build_p7_r50_scope_schema_status_enum_freeze()
    )
    assert_p7_r50_scope_schema_status_enum_freeze_contract(r1)
    rows = _prior_validation_rows_with_overrides(prior_validation_evidence_overrides)
    flags = _prior_validation_flags(rows)
    adoption = {
        "schema_version": P7_R50_PRIOR_VALIDATION_EVIDENCE_ADOPTION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R50_STEP,
        "scope": P7_R50_SCOPE,
        "policy_kind": P7_R50_POLICY_KIND,
        "policy_section": "R50-2_prior_validation_evidence_adoption",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r50_prior_validation_evidence_adoption", max_length=180),
        "review_session_id": clean_identifier(r1.get("review_session_id"), default=P7_R50_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_session_status": P7_R50_INITIAL_REVIEW_SESSION_STATUS_REF,
        "r1_scope_schema_status_enum_freeze_schema_version": P7_R50_SCOPE_SCHEMA_STATUS_ENUM_FREEZE_SCHEMA_VERSION,
        "r1_scope_schema_status_enum_freeze_ref": clean_identifier(r1.get("material_id"), default="p7_r50_scope_schema_status_enum_freeze", max_length=180),
        "current_working_backend_zip_ref": clean_identifier(current_working_backend_zip_ref, default="mashos-api_2(102).zip", max_length=180),
        "required_case_count": P7_R50_REQUIRED_CASE_COUNT,
        "prior_validation_evidence_group_refs": list(P7_R50_PRIOR_VALIDATION_EVIDENCE_GROUP_REFS),
        "prior_validation_evidence_rows": rows,
        "prior_validation_evidence_row_count": len(rows),
        "prior_validation_evidence_adopted": True,
        "precondition_flags": dict(flags),
        "r50_r0_r1_current_implementation_evidence_present": flags["r50_r0_r1_current_implementation_evidence_present"],
        "r49_target_green_evidence_present": flags["r49_target_green_evidence_present"],
        "r48_regression_green_evidence_present": flags["r48_regression_green_evidence_present"],
        "r47_regression_green_evidence_present": flags["r47_regression_green_evidence_present"],
        "r46_regression_green_evidence_present": flags["r46_regression_green_evidence_present"],
        "display_p5_core_green_evidence_present": flags["display_p5_core_green_evidence_present"],
        "rn_contract_green_evidence_present": flags["rn_contract_green_evidence_present"],
        "backend_collect_only_evidence_present": flags["backend_collect_only_evidence_present"],
        "full_backend_suite_green_confirmed": False,
        "collect_only_claimed_as_full_backend_green": False,
        "rn_contract_claimed_as_real_device_modal_readfeel": False,
        "evidence_commands_reference_only": True,
        "validation_commands_executed_here": False,
        "command_result_body_stored_here": False,
        "terminal_output_stored_here": False,
        "manual_run_decision_made_here": False,
        "local_only_body_full_generation_allowed": False,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "implemented_steps": list(P7_R50_R2_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R50_R2_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r49_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_prior_validation_evidence_adopted": True,
        "r3_manual_run_decision_built": False,
        "first_next_work_ref": P7_R50_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R50_R2_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r50_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r50_prior_validation_evidence_adoption_contract(adoption)
    return adoption


def assert_p7_r50_prior_validation_evidence_adoption_contract(adoption: Mapping[str, Any]) -> bool:
    data = safe_mapping(adoption)
    _assert_required_fields(data, required=P7_R50_PRIOR_VALIDATION_EVIDENCE_ADOPTION_REQUIRED_FIELD_REFS, source="p7_r50_r2_prior_validation_evidence_adoption")
    _assert_common(data, schema_version=P7_R50_PRIOR_VALIDATION_EVIDENCE_ADOPTION_SCHEMA_VERSION, source="p7_r50_r2_prior_validation_evidence_adoption")
    if data.get("policy_section") != "R50-2_prior_validation_evidence_adoption":
        raise ValueError("R50 R2 policy section changed")
    rows = data.get("prior_validation_evidence_rows")
    if not isinstance(rows, list) or len(rows) != len(P7_R50_PRIOR_VALIDATION_EVIDENCE_GROUP_REFS):
        raise ValueError("R50 R2 evidence rows changed")
    for row in rows:
        assert_p7_r50_prior_validation_evidence_row_contract(safe_mapping(row))
    if [row.get("evidence_group_ref") for row in rows] != list(P7_R50_PRIOR_VALIDATION_EVIDENCE_GROUP_REFS):
        raise ValueError("R50 R2 evidence row order changed")
    flags = safe_mapping(data.get("precondition_flags"))
    expected_flags = _prior_validation_flags([safe_mapping(row) for row in rows])
    if flags != expected_flags:
        raise ValueError("R50 R2 precondition flags do not match evidence rows")
    for key, value in expected_flags.items():
        if data.get(key) is not value:
            raise ValueError(f"R50 R2 top-level flag mismatch for {key}")
    for false_key in (
        "full_backend_suite_green_confirmed",
        "collect_only_claimed_as_full_backend_green",
        "rn_contract_claimed_as_real_device_modal_readfeel",
        "validation_commands_executed_here",
        "command_result_body_stored_here",
        "terminal_output_stored_here",
        "manual_run_decision_made_here",
        "local_only_body_full_generation_allowed",
        "actual_manual_review_run_here",
        "body_full_packet_generated_here",
        "r3_manual_run_decision_built",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R50 R2 must keep {false_key}=False")
    for true_key in (
        "prior_validation_evidence_adopted",
        "evidence_commands_reference_only",
        "r0_current_source_r49_handoff_bridge_refrozen",
        "r1_scope_schema_status_enum_fixed",
        "r2_prior_validation_evidence_adopted",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R50 R2 must keep {true_key}=True")
    if tuple(data.get("implemented_steps") or ()) != P7_R50_R2_IMPLEMENTED_STEPS:
        raise ValueError("R50 R2 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_R2_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R2 not-yet steps changed")
    if data.get("next_required_step") != P7_R50_R2_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R50 R2 must point to R50-3 next")
    return True


def _manual_run_precondition_flags(
    *,
    prior_flags: Mapping[str, Any],
    local_review_root_safe: bool,
    explicit_allow_present: bool,
    disposal_plan_ready: bool,
    body_free_summary_path_ready: bool,
    r49_handoff_present: bool,
    reviewer_available: bool,
    scope_drift_detected: bool,
    body_free_leak_risk_detected: bool,
    open_execution_blocker_ids: Sequence[str],
) -> dict[str, bool]:
    return {
        "r49_handoff_present": bool(r49_handoff_present),
        "r49_target_green_evidence_present": prior_flags.get("r49_target_green_evidence_present") is True,
        "r48_regression_green_evidence_present": prior_flags.get("r48_regression_green_evidence_present") is True,
        "r47_regression_green_evidence_present": prior_flags.get("r47_regression_green_evidence_present") is True,
        "r46_regression_green_evidence_present": prior_flags.get("r46_regression_green_evidence_present") is True,
        "display_p5_core_green_evidence_present": prior_flags.get("display_p5_core_green_evidence_present") is True,
        "rn_contract_green_evidence_present": prior_flags.get("rn_contract_green_evidence_present") is True,
        "local_review_root_safe": bool(local_review_root_safe),
        "explicit_allow_present": bool(explicit_allow_present),
        "disposal_plan_ready": bool(disposal_plan_ready),
        "body_free_summary_path_ready": bool(body_free_summary_path_ready),
        "reviewer_available": bool(reviewer_available),
        "scope_drift_absent": not bool(scope_drift_detected),
        "body_free_leak_risk_absent": not bool(body_free_leak_risk_detected),
        "execution_blockers_absent": len(open_execution_blocker_ids) == 0,
        "backend_collect_only_claimed_as_full_backend_green": False,
        "rn_contract_claimed_as_real_device_modal_readfeel": False,
    }


def _manual_run_decision_from_preconditions(flags: Mapping[str, Any], open_execution_blocker_ids: Sequence[str]) -> tuple[str, list[str], list[str]]:
    if flags.get("r49_handoff_present") is not True:
        return "NO_GO_MISSING_R49_HANDOFF", ["missing_r49_handoff"], ["r50_missing_r49_handoff"]
    reasons: list[str] = []
    execution_blocker_ids: list[str] = []
    evidence_pairs = (
        ("r49_target_green_evidence_present", "missing_r49_target_green_evidence", "r50_missing_r49_target_green_evidence"),
        ("r48_regression_green_evidence_present", "missing_r48_regression_green_evidence", "r50_missing_r48_regression_green_evidence"),
        ("r47_regression_green_evidence_present", "missing_r47_regression_green_evidence", "r50_missing_r47_regression_green_evidence"),
        ("r46_regression_green_evidence_present", "missing_r46_regression_green_evidence", "r50_missing_r46_regression_green_evidence"),
        ("display_p5_core_green_evidence_present", "missing_display_p5_core_green_evidence", "r50_missing_display_p5_core_green_evidence"),
    )
    for flag_ref, reason_ref, blocker_ref in evidence_pairs:
        if flags.get(flag_ref) is not True:
            reasons.append(reason_ref)
            execution_blocker_ids.append(blocker_ref)
    if flags.get("rn_contract_green_evidence_present") is not True:
        reasons.append("missing_rn_contract_green_evidence")
    if reasons:
        return "NO_GO_TARGET_OR_REGRESSION_EVIDENCE_MISSING", reasons, execution_blocker_ids
    if flags.get("local_review_root_safe") is not True:
        return "NO_GO_LOCAL_ROOT_UNSAFE", ["local_review_root_not_safe_or_not_confirmed"], ["r50_local_review_root_invalid"]
    if flags.get("explicit_allow_present") is not True:
        return "NO_GO_EXPLICIT_ALLOW_MISSING", ["explicit_local_body_full_allow_missing"], ["r50_explicit_allow_missing"]
    if flags.get("disposal_plan_ready") is not True:
        return "NO_GO_DISPOSAL_PLAN_UNSAFE", ["disposal_plan_missing_or_unsafe"], ["r50_disposal_plan_missing"]
    if flags.get("reviewer_available") is not True:
        return "NO_GO_REVIEWER_UNAVAILABLE", ["reviewer_unavailable_for_24_case_manual_review"], []
    if flags.get("scope_drift_absent") is not True:
        return "NO_GO_SCOPE_DRIFT", ["scope_drift_detected"], ["r50_scope_drift_detected"]
    if flags.get("body_free_summary_path_ready") is not True or flags.get("body_free_leak_risk_absent") is not True:
        return "NO_GO_BODY_FREE_LEAK_RISK", ["body_free_summary_path_not_ready_or_leak_risk_detected"], ["r50_body_free_leak_detected"]
    blocker_ids = dedupe_identifiers(open_execution_blocker_ids, limit=20, max_length=120)
    if blocker_ids:
        return "BLOCKED_BY_EXECUTION_BLOCKER", ["open_execution_blocker_present"], blocker_ids
    return "GO_FOR_LOCAL_MANUAL_REVIEW", ["all_manual_run_preconditions_satisfied_body_full_still_not_generated"], []


def build_p7_r50_manual_run_decision_bodyfree(
    *,
    prior_validation_evidence_adoption: Mapping[str, Any] | None = None,
    r2_prior_validation_evidence_adoption: Mapping[str, Any] | None = None,
    local_review_root_safe: bool = False,
    explicit_allow_present: bool = False,
    disposal_plan_ready: bool = False,
    body_free_summary_path_ready: bool = False,
    r49_handoff_present: bool = True,
    reviewer_available: bool = True,
    scope_drift_detected: bool = False,
    body_free_leak_risk_detected: bool = False,
    open_execution_blocker_ids: Sequence[Any] | None = None,
    material_id: Any = "p7_r50_manual_run_decision_bodyfree",
) -> dict[str, Any]:
    """Build R50-3 manual-review GO/NO-GO body-free decision material."""

    if prior_validation_evidence_adoption is not None and r2_prior_validation_evidence_adoption is not None:
        raise ValueError("provide only one R50-2 evidence adoption value")
    r2 = (
        safe_mapping(prior_validation_evidence_adoption)
        if prior_validation_evidence_adoption is not None
        else safe_mapping(r2_prior_validation_evidence_adoption)
        if r2_prior_validation_evidence_adoption is not None
        else build_p7_r50_prior_validation_evidence_adoption()
    )
    assert_p7_r50_prior_validation_evidence_adoption_contract(r2)
    open_blocker_ids = dedupe_identifiers(open_execution_blocker_ids, limit=20, max_length=120)
    flags = _manual_run_precondition_flags(
        prior_flags=safe_mapping(r2.get("precondition_flags")),
        local_review_root_safe=local_review_root_safe,
        explicit_allow_present=explicit_allow_present,
        disposal_plan_ready=disposal_plan_ready,
        body_free_summary_path_ready=body_free_summary_path_ready,
        r49_handoff_present=r49_handoff_present,
        reviewer_available=reviewer_available,
        scope_drift_detected=scope_drift_detected,
        body_free_leak_risk_detected=body_free_leak_risk_detected,
        open_execution_blocker_ids=open_blocker_ids,
    )
    decision, reason_refs, execution_blocker_ids = _manual_run_decision_from_preconditions(flags, open_blocker_ids)
    local_body_full_allowed = decision == "GO_FOR_LOCAL_MANUAL_REVIEW"
    status = "READY_FOR_LOCAL_BODY_FULL_PACKET_GENERATION" if local_body_full_allowed else "PRECHECK_BLOCKED"
    if decision == "BLOCKED_BY_EXECUTION_BLOCKER":
        status = "BLOCKED"
    missing_preconditions = [key for key, value in flags.items() if value is not True and key not in (
        "backend_collect_only_claimed_as_full_backend_green",
        "rn_contract_claimed_as_real_device_modal_readfeel",
    )]
    decision_body = {
        "schema_version": P7_R50_MANUAL_RUN_DECISION_BODYFREE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R50_STEP,
        "scope": P7_R50_SCOPE,
        "policy_kind": P7_R50_POLICY_KIND,
        "policy_section": "R50-3_manual_run_go_no_go_decision_builder",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r50_manual_run_decision_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r2.get("review_session_id"), default=P7_R50_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_session_status": status,
        "r2_prior_validation_evidence_schema_version": P7_R50_PRIOR_VALIDATION_EVIDENCE_ADOPTION_SCHEMA_VERSION,
        "r2_prior_validation_evidence_ref": clean_identifier(r2.get("material_id"), default="p7_r50_prior_validation_evidence_adoption", max_length=180),
        "required_case_count": P7_R50_REQUIRED_CASE_COUNT,
        "manual_run_decision": decision,
        "manual_run_decision_reason_refs": reason_refs,
        "execution_blocker_ids": execution_blocker_ids,
        "open_execution_blocker_ids": open_blocker_ids,
        "missing_precondition_refs": missing_preconditions,
        "precondition_flags": flags,
        "local_only_body_full_generation_allowed": local_body_full_allowed,
        "manual_run_decision_made_here": True,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "api_db_rn_response_key_changed_here": False,
        "question_api_implemented": False,
        "question_db_schema_implemented": False,
        "question_rn_ui_implemented": False,
        "question_response_key_implemented": False,
        "question_trigger_logic_implemented": False,
        "p5_human_blind_qa_confirmed": False,
        "p5_human_blind_qa_confirmed_candidate": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_start_allowed_candidate": False,
        "p8_question_design_material_candidate": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "implemented_steps": list(P7_R50_R2_R3_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R50_R2_R3_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r49_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_prior_validation_evidence_adopted": True,
        "r3_manual_run_decision_built": True,
        "first_next_work_ref": P7_R50_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R50_R3_NEXT_REQUIRED_STEP_REF if local_body_full_allowed else P7_R50_R3_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r50_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_for(P7_R50_R3_FALSE_KEY_REFS),
    }
    assert_p7_r50_manual_run_decision_bodyfree_contract(decision_body)
    return decision_body


def assert_p7_r50_manual_run_decision_bodyfree_contract(decision: Mapping[str, Any]) -> bool:
    data = safe_mapping(decision)
    _assert_required_fields(data, required=P7_R50_MANUAL_RUN_DECISION_BODYFREE_REQUIRED_FIELD_REFS, source="p7_r50_r3_manual_run_decision_bodyfree")
    _assert_common_with_false_keys(
        data,
        schema_version=P7_R50_MANUAL_RUN_DECISION_BODYFREE_SCHEMA_VERSION,
        source="p7_r50_r3_manual_run_decision_bodyfree",
        false_keys=P7_R50_R3_FALSE_KEY_REFS,
    )
    manual_decision = data.get("manual_run_decision")
    if data.get("policy_section") != "R50-3_manual_run_go_no_go_decision_builder":
        raise ValueError("R50 R3 policy section changed")
    if manual_decision not in P7_R50_MANUAL_RUN_DECISION_REFS:
        raise ValueError("R50 R3 manual decision enum changed")
    if data.get("required_case_count") != P7_R50_REQUIRED_CASE_COUNT:
        raise ValueError("R50 R3 must keep required_case_count=24")
    flags = safe_mapping(data.get("precondition_flags"))
    for flag_ref in P7_R50_MANUAL_RUN_PRECONDITION_FLAG_REFS:
        if flag_ref not in flags:
            raise ValueError(f"R50 R3 missing precondition flag {flag_ref}")
    if flags.get("backend_collect_only_claimed_as_full_backend_green") is not False:
        raise ValueError("R50 R3 must not claim collect-only as full backend suite green")
    if flags.get("rn_contract_claimed_as_real_device_modal_readfeel") is not False:
        raise ValueError("R50 R3 must not claim RN contract as real-device modal readfeel")
    execution_blocker_ids = dedupe_identifiers(data.get("execution_blocker_ids"), limit=20, max_length=120)
    unknown_blockers = sorted(set(execution_blocker_ids) - set(P7_R50_EXECUTION_BLOCKER_ID_REFS))
    if unknown_blockers:
        raise ValueError(f"R50 R3 execution blocker ids are not canonical: {unknown_blockers[:4]}")
    is_go = manual_decision == "GO_FOR_LOCAL_MANUAL_REVIEW"
    if is_go:
        for flag_ref in P7_R50_MANUAL_RUN_PRECONDITION_FLAG_REFS:
            if flags.get(flag_ref) is not True:
                raise ValueError(f"R50 R3 GO requires {flag_ref}=True")
        for flag_ref in ("r49_handoff_present", "reviewer_available", "scope_drift_absent", "body_free_leak_risk_absent", "execution_blockers_absent"):
            if flags.get(flag_ref) is not True:
                raise ValueError(f"R50 R3 GO requires {flag_ref}=True")
        if execution_blocker_ids or data.get("open_execution_blocker_ids"):
            raise ValueError("R50 R3 GO must not have execution blockers")
        if data.get("local_only_body_full_generation_allowed") is not True:
            raise ValueError("R50 R3 GO must allow local-only body-full generation next")
        if data.get("review_session_status") != "READY_FOR_LOCAL_BODY_FULL_PACKET_GENERATION":
            raise ValueError("R50 R3 GO must use READY_FOR_LOCAL_BODY_FULL_PACKET_GENERATION status")
        if data.get("next_required_step") != P7_R50_R3_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R3 GO must point to R50-4")
    else:
        if data.get("local_only_body_full_generation_allowed") is not False:
            raise ValueError("R50 R3 NO-GO/BLOCKED must not allow body-full generation")
        if data.get("review_session_status") not in ("PRECHECK_BLOCKED", "BLOCKED"):
            raise ValueError("R50 R3 NO-GO/BLOCKED status changed")
        if data.get("next_required_step") != P7_R50_R3_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R3 NO-GO/BLOCKED must point to precondition resolution")
    if data.get("manual_run_decision_made_here") is not True:
        raise ValueError("R50 R3 must mark manual decision made")
    for false_key in (
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
        "api_db_rn_response_key_changed_here",
        "question_api_implemented",
        "question_db_schema_implemented",
        "question_rn_ui_implemented",
        "question_response_key_implemented",
        "question_trigger_logic_implemented",
        "p5_human_blind_qa_confirmed",
        "p5_human_blind_qa_confirmed_candidate",
        "p6_limited_human_readfeel_start_allowed",
        "p6_limited_human_readfeel_start_allowed_candidate",
        "p8_question_design_material_candidate",
        "p7_complete",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R50 R3 must keep {false_key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R50_R2_R3_IMPLEMENTED_STEPS:
        raise ValueError("R50 R3 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_R2_R3_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R3 not-yet steps changed")
    for true_key in (
        "r0_current_source_r49_handoff_bridge_refrozen",
        "r1_scope_schema_status_enum_fixed",
        "r2_prior_validation_evidence_adopted",
        "r3_manual_run_decision_built",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R50 R3 must keep {true_key}=True")
    return True


def build_p7_r50_r2_r3_manual_run_decision_freeze(
    *,
    scope_schema_status_enum_freeze: Mapping[str, Any] | None = None,
    prior_validation_evidence_overrides: Mapping[str, Any] | None = None,
    local_review_root_safe: bool = False,
    explicit_allow_present: bool = False,
    disposal_plan_ready: bool = False,
    body_free_summary_path_ready: bool = False,
    r49_handoff_present: bool = True,
    reviewer_available: bool = True,
    scope_drift_detected: bool = False,
    body_free_leak_risk_detected: bool = False,
    open_execution_blocker_ids: Sequence[Any] | None = None,
    material_id: Any = "p7_r50_r2_r3_manual_run_decision_freeze",
) -> dict[str, Any]:
    """Build a compact combined R50-2/R50-3 body-free freeze."""

    r2 = build_p7_r50_prior_validation_evidence_adoption(
        scope_schema_status_enum_freeze=scope_schema_status_enum_freeze,
        prior_validation_evidence_overrides=prior_validation_evidence_overrides,
    )
    r3 = build_p7_r50_manual_run_decision_bodyfree(
        prior_validation_evidence_adoption=r2,
        local_review_root_safe=local_review_root_safe,
        explicit_allow_present=explicit_allow_present,
        disposal_plan_ready=disposal_plan_ready,
        body_free_summary_path_ready=body_free_summary_path_ready,
        r49_handoff_present=r49_handoff_present,
        reviewer_available=reviewer_available,
        scope_drift_detected=scope_drift_detected,
        body_free_leak_risk_detected=body_free_leak_risk_detected,
        open_execution_blocker_ids=open_execution_blocker_ids,
    )
    combined = {
        "schema_version": P7_R50_R2_R3_MANUAL_RUN_DECISION_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R50_STEP,
        "scope": P7_R50_SCOPE,
        "policy_kind": P7_R50_POLICY_KIND,
        "policy_section": "R50-2_R50-3_manual_run_decision_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r50_r2_r3_manual_run_decision_freeze", max_length=180),
        "r2_prior_validation_evidence_adoption": r2,
        "r3_manual_run_decision_bodyfree": r3,
        "review_session_id": r3["review_session_id"],
        "manual_run_decision": r3["manual_run_decision"],
        "manual_run_decision_reason_refs": list(r3["manual_run_decision_reason_refs"]),
        "precondition_flags": dict(r3["precondition_flags"]),
        "local_only_body_full_generation_allowed": r3["local_only_body_full_generation_allowed"],
        "manual_run_decision_made_here": True,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "implemented_steps": list(P7_R50_R2_R3_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R50_R2_R3_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r49_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_prior_validation_evidence_adopted": True,
        "r3_manual_run_decision_built": True,
        "first_next_work_ref": P7_R50_FIRST_NEXT_WORK_REF,
        "next_required_step": r3["next_required_step"],
        "public_contract": public_contract_flags(),
        "r50_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_for(P7_R50_R3_FALSE_KEY_REFS),
    }
    assert_p7_r50_r2_r3_manual_run_decision_freeze_contract(combined)
    return combined


def assert_p7_r50_r2_r3_manual_run_decision_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_required_fields(data, required=P7_R50_R2_R3_MANUAL_RUN_DECISION_FREEZE_REQUIRED_FIELD_REFS, source="p7_r50_r2_r3_manual_run_decision_freeze")
    _assert_common_with_false_keys(
        data,
        schema_version=P7_R50_R2_R3_MANUAL_RUN_DECISION_FREEZE_SCHEMA_VERSION,
        source="p7_r50_r2_r3_manual_run_decision_freeze",
        false_keys=P7_R50_R3_FALSE_KEY_REFS,
    )
    if data.get("policy_section") != "R50-2_R50-3_manual_run_decision_freeze":
        raise ValueError("R50 R2/R3 policy section changed")
    assert_p7_r50_prior_validation_evidence_adoption_contract(safe_mapping(data.get("r2_prior_validation_evidence_adoption")))
    assert_p7_r50_manual_run_decision_bodyfree_contract(safe_mapping(data.get("r3_manual_run_decision_bodyfree")))
    r3 = safe_mapping(data.get("r3_manual_run_decision_bodyfree"))
    if data.get("manual_run_decision") != r3.get("manual_run_decision"):
        raise ValueError("R50 R2/R3 decision does not match R3")
    if data.get("local_only_body_full_generation_allowed") is not r3.get("local_only_body_full_generation_allowed"):
        raise ValueError("R50 R2/R3 local-only permission does not match R3")
    if tuple(data.get("implemented_steps") or ()) != P7_R50_R2_R3_IMPLEMENTED_STEPS:
        raise ValueError("R50 R2/R3 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_R2_R3_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R2/R3 not-yet steps changed")
    if data.get("manual_run_decision_made_here") is not True:
        raise ValueError("R50 R2/R3 must mark decision made")
    if data.get("actual_manual_review_run_here") is not False or data.get("body_full_packet_generated_here") is not False:
        raise ValueError("R50 R2/R3 must not run review or generate body-full packets")
    return True


def _explicit_allow_present(value: Any) -> bool:
    token = clean_identifier(value, default="", max_length=120)
    return token == P7_R50_EXPLICIT_BODY_FULL_ALLOW_TOKEN_REF


def _export_candidate_sequence(value: Sequence[Any] | Any | None) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes, bytearray)):
        return (value,)
    if isinstance(value, Sequence):
        return tuple(value)
    return (value,)


def _export_denylist_summary(export_candidate_refs: Sequence[Any] | Any | None) -> tuple[int, int, list[str]]:
    candidates = _export_candidate_sequence(export_candidate_refs)
    violation_refs: list[str] = []
    denied_count = 0
    for candidate_ref in candidates:
        reasons = p7_r47_export_candidate_deny_reasons(candidate_ref)
        if reasons:
            denied_count += 1
            violation_refs.extend(reasons)
    return len(candidates), denied_count, dedupe_identifiers(violation_refs, limit=30, max_length=120)


def _r4_preflight_status_and_reasons(
    *,
    r3_decision: Mapping[str, Any],
    local_root_valid: bool,
    local_root_configured: bool,
    explicit_allow_present: bool,
    export_denylist_violation_refs: Sequence[Any],
) -> tuple[str, list[str], list[str]]:
    reason_refs: list[str] = []
    execution_blocker_ids: list[str] = []
    if r3_decision.get("manual_run_decision") != "GO_FOR_LOCAL_MANUAL_REVIEW" or r3_decision.get(
        "local_only_body_full_generation_allowed"
    ) is not True:
        reason_refs.append("manual_run_decision_not_go_or_not_allowed")
        execution_blocker_ids.extend(dedupe_identifiers(r3_decision.get("execution_blocker_ids"), limit=20, max_length=120))
    if not local_root_configured:
        reason_refs.append("local_review_root_missing")
        execution_blocker_ids.append("r50_local_review_root_missing")
    elif not local_root_valid:
        reason_refs.append("local_review_root_invalid")
        execution_blocker_ids.append("r50_local_review_root_invalid")
    if explicit_allow_present is not True:
        reason_refs.append("explicit_allow_token_missing_or_invalid")
        execution_blocker_ids.append("r50_explicit_allow_missing")
    if export_denylist_violation_refs:
        reason_refs.append("export_denylist_violation_detected")
        execution_blocker_ids.append("r50_body_full_packet_export_violation")
    if reason_refs:
        return "BLOCKED", dedupe_identifiers(reason_refs, limit=20, max_length=140), dedupe_identifiers(
            execution_blocker_ids, limit=20, max_length=120
        )
    return "PASSED", ["local_only_root_explicit_allow_and_export_denylist_preflight_passed"], []


def build_p7_r50_local_only_root_explicit_allow_export_denylist_preflight(
    *,
    manual_run_decision_bodyfree: Mapping[str, Any] | None = None,
    r3_manual_run_decision_bodyfree: Mapping[str, Any] | None = None,
    local_review_root: Any = None,
    repo_roots: Sequence[Any] | None = None,
    export_roots: Sequence[Any] | None = None,
    explicit_allow_token: Any = None,
    export_candidate_refs: Sequence[Any] | Any | None = None,
    material_id: Any = "p7_r50_local_only_root_explicit_allow_export_denylist_preflight",
) -> dict[str, Any]:
    """Build the R50-4 body-free local-only root/allow/export preflight.

    This helper validates only the preflight contract.  It does not write a
    local packet, does not expose local paths, and does not store candidate
    export refs because those may contain local-only body-full material names.
    """

    if manual_run_decision_bodyfree is not None and r3_manual_run_decision_bodyfree is not None:
        raise ValueError("provide only one R50-3 manual-run decision value")
    r3 = (
        safe_mapping(manual_run_decision_bodyfree)
        if manual_run_decision_bodyfree is not None
        else safe_mapping(r3_manual_run_decision_bodyfree)
        if r3_manual_run_decision_bodyfree is not None
        else build_p7_r50_manual_run_decision_bodyfree()
    )
    assert_p7_r50_manual_run_decision_bodyfree_contract(r3)

    storage_policy = build_p7_r47_local_review_storage_root_policy(
        local_review_root=local_review_root,
        repo_roots=repo_roots,
        export_roots=export_roots,
        material_id="p7_r50_r4_r47_storage_root_preflight",
    )
    assert_p7_r47_local_review_storage_root_policy_contract(storage_policy)
    export_policy = build_p7_r47_export_denylist_policy(material_id="p7_r50_r4_r47_export_denylist_preflight")
    assert_p7_r47_export_denylist_policy_contract(export_policy)

    root_configured = storage_policy.get("local_review_root_configured") is True
    root_valid = storage_policy.get("local_review_root_status") == "valid" and storage_policy.get(
        "local_body_packet_generation_allowed"
    ) is True
    allow_present = _explicit_allow_present(explicit_allow_token)
    checked_count, denied_count, deny_refs = _export_denylist_summary(export_candidate_refs)
    preflight_status, reason_refs, execution_blocker_ids = _r4_preflight_status_and_reasons(
        r3_decision=r3,
        local_root_valid=root_valid,
        local_root_configured=root_configured,
        explicit_allow_present=allow_present,
        export_denylist_violation_refs=deny_refs,
    )
    passed = preflight_status == "PASSED"
    review_session_status = "READY_FOR_LOCAL_BODY_FULL_PACKET_GENERATION" if passed else "PRECHECK_BLOCKED"
    preflight = {
        "schema_version": P7_R50_LOCAL_ONLY_ROOT_EXPLICIT_ALLOW_EXPORT_PREFLIGHT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R50_STEP,
        "scope": P7_R50_SCOPE,
        "policy_kind": P7_R50_POLICY_KIND,
        "policy_section": "R50-4_local_only_root_explicit_allow_export_denylist_preflight",
        "current_phase": "P7",
        "material_id": clean_identifier(
            material_id,
            default="p7_r50_local_only_root_explicit_allow_export_denylist_preflight",
            max_length=180,
        ),
        "review_session_id": clean_identifier(r3.get("review_session_id"), default=P7_R50_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_session_status": review_session_status,
        "r3_manual_run_decision_schema_version": P7_R50_MANUAL_RUN_DECISION_BODYFREE_SCHEMA_VERSION,
        "r3_manual_run_decision_ref": clean_identifier(r3.get("material_id"), default="p7_r50_manual_run_decision_bodyfree", max_length=180),
        "manual_run_decision": clean_identifier(r3.get("manual_run_decision"), default="NO_GO_LOCAL_ROOT_UNSAFE", max_length=100),
        "required_case_count": P7_R50_REQUIRED_CASE_COUNT,
        "r47_local_review_root_env_var": P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR,
        "r47_local_review_storage_root_policy_schema_version": P7_R47_LOCAL_REVIEW_STORAGE_ROOT_POLICY_SCHEMA_VERSION,
        "r47_export_denylist_policy_schema_version": P7_R47_EXPORT_DENYLIST_POLICY_SCHEMA_VERSION,
        "r47_storage_root_policy_ref": clean_identifier(storage_policy.get("material_id"), default="p7_r50_r4_r47_storage_root_preflight", max_length=180),
        "r47_export_denylist_policy_ref": clean_identifier(export_policy.get("material_id"), default="p7_r50_r4_r47_export_denylist_preflight", max_length=180),
        "local_review_root_source": clean_identifier(storage_policy.get("local_review_root_source"), default="missing", max_length=80),
        "local_review_root_configured": root_configured,
        "local_review_root_status": clean_identifier(storage_policy.get("local_review_root_status"), default="missing", max_length=40),
        "local_review_root_valid": root_valid,
        "storage_root_ref": P7_R47_STORAGE_ROOT_REF if root_valid else "not_configured_or_invalid",
        "root_path_exposed": False,
        "local_absolute_path_included": False,
        "explicit_allow_env_var": P7_R50_EXPLICIT_BODY_FULL_ALLOW_ENV_VAR,
        "explicit_allow_token_ref": P7_R50_EXPLICIT_BODY_FULL_ALLOW_TOKEN_REF,
        "explicit_allow_present": allow_present,
        "explicit_allow_token_body_stored_here": False,
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
        "local_only_body_full_generation_allowed_before_preflight": r3.get("local_only_body_full_generation_allowed") is True,
        "local_only_body_full_generation_allowed_after_preflight": passed,
        "local_only_body_full_generation_allowed": passed,
        "manual_run_decision_made_here": True,
        "preflight_status": preflight_status,
        "preflight_reason_refs": reason_refs,
        "execution_blocker_ids": execution_blocker_ids,
        "open_execution_blocker_ids": execution_blocker_ids,
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built": True,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "implemented_steps": list(P7_R50_R4_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R50_R4_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r49_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_prior_validation_evidence_adopted": True,
        "r3_manual_run_decision_built": True,
        "first_next_work_ref": P7_R50_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R50_R4_NEXT_REQUIRED_STEP_REF if passed else P7_R50_R4_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r50_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_for(P7_R50_R4_FALSE_KEY_REFS),
    }
    assert_p7_r50_local_only_root_explicit_allow_export_denylist_preflight_contract(preflight)
    return preflight


def build_p7_r50_local_body_full_generation_preflight(**kwargs: Any) -> dict[str, Any]:
    """Compatibility alias for the R50-4 builder named in the design note."""

    return build_p7_r50_local_only_root_explicit_allow_export_denylist_preflight(**kwargs)


def assert_p7_r50_local_only_root_explicit_allow_export_denylist_preflight_contract(
    preflight: Mapping[str, Any]
) -> bool:
    data = safe_mapping(preflight)
    _assert_required_fields(
        data,
        required=P7_R50_LOCAL_ONLY_ROOT_EXPLICIT_ALLOW_EXPORT_PREFLIGHT_REQUIRED_FIELD_REFS,
        source="p7_r50_r4_local_only_root_explicit_allow_export_denylist_preflight",
    )
    _assert_common_with_false_keys(
        data,
        schema_version=P7_R50_LOCAL_ONLY_ROOT_EXPLICIT_ALLOW_EXPORT_PREFLIGHT_SCHEMA_VERSION,
        source="p7_r50_r4_local_only_root_explicit_allow_export_denylist_preflight",
        false_keys=P7_R50_R4_FALSE_KEY_REFS,
    )
    if data.get("policy_section") != "R50-4_local_only_root_explicit_allow_export_denylist_preflight":
        raise ValueError("R50 R4 policy section changed")
    if data.get("required_case_count") != P7_R50_REQUIRED_CASE_COUNT:
        raise ValueError("R50 R4 must keep required_case_count=24")
    if data.get("r47_local_review_root_env_var") != P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR:
        raise ValueError("R50 R4 local root env var changed")
    if tuple(data.get("export_denylist_patterns") or ()) != P7_R47_EXPORT_DENYLIST_PATTERNS:
        raise ValueError("R50 R4 export denylist patterns changed")
    if data.get("root_path_exposed") is not False or data.get("local_absolute_path_included") is not False:
        raise ValueError("R50 R4 must not expose local paths")
    for false_key in (
        "explicit_allow_token_body_stored_here",
        "export_candidate_refs_stored_here",
        "export_candidate_body_stored_here",
        "body_full_packet_export_allowed",
        "reviewer_notes_export_allowed",
        "body_full_packet_zip_inclusion_allowed",
        "premise_or_implemented_docs_inclusion_allowed",
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R50 R4 must keep {false_key}=False")
    if data.get("manual_run_decision_made_here") is not True:
        raise ValueError("R50 R4 must preserve R3 manual decision as made")
    status = data.get("preflight_status")
    if status not in ("PASSED", "BLOCKED"):
        raise ValueError("R50 R4 preflight status changed")
    if status == "PASSED":
        for true_key in (
            "local_review_root_configured",
            "local_review_root_valid",
            "explicit_allow_present",
            "local_only_body_full_generation_allowed_before_preflight",
            "local_only_body_full_generation_allowed_after_preflight",
            "local_only_body_full_generation_allowed",
        ):
            if data.get(true_key) is not True:
                raise ValueError(f"R50 R4 PASSED requires {true_key}=True")
        if data.get("manual_run_decision") != "GO_FOR_LOCAL_MANUAL_REVIEW":
            raise ValueError("R50 R4 PASSED requires R3 GO decision")
        if data.get("storage_root_ref") != P7_R47_STORAGE_ROOT_REF:
            raise ValueError("R50 R4 PASSED must expose only the abstract storage root ref")
        if data.get("denied_export_candidate_count") != 0 or data.get("export_denylist_violation_refs"):
            raise ValueError("R50 R4 PASSED must have no export denylist violations")
        if data.get("execution_blocker_ids") or data.get("open_execution_blocker_ids"):
            raise ValueError("R50 R4 PASSED must not carry execution blockers")
        if data.get("review_session_status") != "READY_FOR_LOCAL_BODY_FULL_PACKET_GENERATION":
            raise ValueError("R50 R4 PASSED must remain ready for local body-full generation")
        if data.get("next_required_step") != P7_R50_R4_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R4 PASSED must point to R50-5")
    else:
        if data.get("local_only_body_full_generation_allowed_after_preflight") is not False:
            raise ValueError("R50 R4 BLOCKED must not allow generation after preflight")
        if data.get("local_only_body_full_generation_allowed") is not False:
            raise ValueError("R50 R4 BLOCKED must not allow body-full generation")
        if data.get("review_session_status") != "PRECHECK_BLOCKED":
            raise ValueError("R50 R4 BLOCKED must use PRECHECK_BLOCKED")
        if not data.get("preflight_reason_refs") or not data.get("execution_blocker_ids"):
            raise ValueError("R50 R4 BLOCKED must carry reason and execution blocker ids")
        if data.get("next_required_step") != P7_R50_R4_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R4 BLOCKED must point to R50-4 resolution")
    unknown_blockers = sorted(set(data.get("execution_blocker_ids") or ()) - set(P7_R50_EXECUTION_BLOCKER_ID_REFS))
    if unknown_blockers:
        raise ValueError(f"R50 R4 execution blocker ids are not canonical: {unknown_blockers[:4]}")
    if tuple(data.get("implemented_steps") or ()) != P7_R50_R4_IMPLEMENTED_STEPS:
        raise ValueError("R50 R4 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_R4_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R4 not-yet steps changed")
    for true_key in (
        "r0_current_source_r49_handoff_bridge_refrozen",
        "r1_scope_schema_status_enum_fixed",
        "r2_prior_validation_evidence_adopted",
        "r3_manual_run_decision_built",
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R50 R4 must keep {true_key}=True")
    return True


def _case_distribution_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family_ref, case_count, case_role in P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION:
        rows.append(
            {
                "family_ref": clean_identifier(family_ref, default="unknown_family", max_length=160),
                "case_count": _non_negative_int(case_count),
                "case_role": clean_identifier(case_role, default="unknown_case_role", max_length=160),
            }
        )
    return rows


def build_p7_r50_review_session_protocol_bodyfree(
    *,
    local_only_root_explicit_allow_export_preflight: Mapping[str, Any] | None = None,
    r4_local_only_root_explicit_allow_export_denylist_preflight: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r50_review_session_protocol_bodyfree",
) -> dict[str, Any]:
    """Build the R50-5 24-case review-session protocol body-free."""

    if local_only_root_explicit_allow_export_preflight is not None and r4_local_only_root_explicit_allow_export_denylist_preflight is not None:
        raise ValueError("provide only one R50-4 preflight value")
    r4 = (
        safe_mapping(local_only_root_explicit_allow_export_preflight)
        if local_only_root_explicit_allow_export_preflight is not None
        else safe_mapping(r4_local_only_root_explicit_allow_export_denylist_preflight)
        if r4_local_only_root_explicit_allow_export_denylist_preflight is not None
        else build_p7_r50_local_only_root_explicit_allow_export_denylist_preflight()
    )
    assert_p7_r50_local_only_root_explicit_allow_export_denylist_preflight_contract(r4)
    preflight_passed = r4.get("preflight_status") == "PASSED" and r4.get("local_only_body_full_generation_allowed") is True
    protocol_status = "READY_FOR_24_CASE_LOCAL_REVIEW_PROTOCOL" if preflight_passed else "BLOCKED_BY_R50_4_PREFLIGHT"
    protocol_reason_refs = (
        ["twenty_four_case_blind_review_session_protocol_fixed_bodyfree"]
        if preflight_passed
        else ["r50_4_preflight_not_passed_no_review_session_protocol_ready"]
    )
    minimums = safe_mapping(P7_R47_P5_FIRST_FORMAL_MINIMUMS)
    case_distribution = _case_distribution_rows()
    protocol = {
        "schema_version": P7_R50_REVIEW_SESSION_PROTOCOL_BODYFREE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R50_STEP,
        "scope": P7_R50_SCOPE,
        "policy_kind": P7_R50_POLICY_KIND,
        "policy_section": "R50-5_24_case_review_session_protocol_builder",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r50_review_session_protocol_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r4.get("review_session_id"), default=P7_R50_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_session_status": "READY_FOR_LOCAL_BODY_FULL_PACKET_GENERATION" if preflight_passed else "PRECHECK_BLOCKED",
        "r4_preflight_schema_version": P7_R50_LOCAL_ONLY_ROOT_EXPLICIT_ALLOW_EXPORT_PREFLIGHT_SCHEMA_VERSION,
        "r4_preflight_ref": clean_identifier(
            r4.get("material_id"),
            default="p7_r50_local_only_root_explicit_allow_export_denylist_preflight",
            max_length=180,
        ),
        "preflight_status": clean_identifier(r4.get("preflight_status"), default="BLOCKED", max_length=80),
        "protocol_status": protocol_status,
        "protocol_reason_refs": protocol_reason_refs,
        "required_case_count": P7_R50_REQUIRED_CASE_COUNT,
        "review_prompt_version": P7_R50_REVIEW_PROMPT_VERSION,
        "reviewer_visible_field_refs": list(P7_R50_REVIEWER_VISIBLE_FIELD_REFS),
        "reviewer_hidden_field_refs": list(P7_R50_REVIEWER_HIDDEN_FIELD_REFS),
        "rating_axis_refs": list(P5_HUMAN_BLIND_QA_RATING_AXES),
        "rating_axis_target_refs": dict(P5_HUMAN_BLIND_QA_TARGETS),
        "readfeel_blocker_id_refs": list(P7_R48_READFEEL_BLOCKER_ID_REFS),
        "question_need_primary_class_refs": list(P7_R50_QUESTION_NEED_PRIMARY_CLASS_REFS),
        "ambiguity_kind_refs": list(P7_R50_AMBIGUITY_KIND_REFS),
        "one_question_fit_refs": list(P7_R50_ONE_QUESTION_FIT_REFS),
        "repair_required_ref_refs": list(P7_R50_REPAIR_REQUIRED_REF_REFS),
        "question_need_observation_required": True,
        "rating_row_required_for_each_case": True,
        "execution_blocker_row_required_for_unreviewable_case": True,
        "question_text_required": False,
        "draft_question_text_allowed": False,
        "reviewer_free_text_bodyfree_export_allowed": False,
        "reviewer_free_text_local_only": True,
        "body_full_reader_protocol_local_only": True,
        "protocol_body_full_packet_generation_allowed_here": False,
        "protocol_human_review_run_allowed_here": False,
        "first_formal_case_distribution": case_distribution,
        "case_distribution_total": sum(int(row["case_count"]) for row in case_distribution),
        "minimum_total_cases": _non_negative_int(minimums.get("minimum_total_cases")),
        "minimum_per_family": _non_negative_int(minimums.get("minimum_per_family")),
        "minimum_history_line_eligible_input": _non_negative_int(minimums.get("minimum_history_line_eligible_input")),
        "minimum_owned_history_positive_cases": _non_negative_int(minimums.get("minimum_owned_history_positive_cases")),
        "minimum_block_boundary_cases": safe_mapping(minimums.get("minimum_block_boundary_cases")),
        "blind_case_id_required": True,
        "case_ref_hidden_from_reviewer": True,
        "family_hidden_from_reviewer": True,
        "subscription_tier_hidden_from_reviewer": True,
        "controller_expected_result_hidden_from_reviewer": True,
        "gate_expected_result_hidden_from_reviewer": True,
        "p5_confirmed_conditions_hidden_from_reviewer": True,
        "p8_material_candidate_conditions_hidden_from_reviewer": True,
        "local_only_body_full_generation_allowed": preflight_passed,
        "manual_run_decision_made_here": True,
        "r5_24_case_review_session_protocol_built": True,
        "execution_blocker_ids": [] if preflight_passed else dedupe_identifiers(r4.get("execution_blocker_ids"), limit=20, max_length=120),
        "open_execution_blocker_ids": [] if preflight_passed else dedupe_identifiers(r4.get("open_execution_blocker_ids"), limit=20, max_length=120),
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "implemented_steps": list(P7_R50_R5_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R50_R5_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r49_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_prior_validation_evidence_adopted": True,
        "r3_manual_run_decision_built": True,
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built": True,
        "first_next_work_ref": P7_R50_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R50_R5_NEXT_REQUIRED_STEP_REF if preflight_passed else P7_R50_R5_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r50_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_for(P7_R50_R5_FALSE_KEY_REFS),
    }
    assert_p7_r50_review_session_protocol_bodyfree_contract(protocol)
    return protocol


def assert_p7_r50_review_session_protocol_bodyfree_contract(protocol: Mapping[str, Any]) -> bool:
    data = safe_mapping(protocol)
    _assert_required_fields(
        data,
        required=P7_R50_REVIEW_SESSION_PROTOCOL_BODYFREE_REQUIRED_FIELD_REFS,
        source="p7_r50_r5_review_session_protocol_bodyfree",
    )
    _assert_common_with_false_keys(
        data,
        schema_version=P7_R50_REVIEW_SESSION_PROTOCOL_BODYFREE_SCHEMA_VERSION,
        source="p7_r50_r5_review_session_protocol_bodyfree",
        false_keys=P7_R50_R5_FALSE_KEY_REFS,
    )
    if data.get("policy_section") != "R50-5_24_case_review_session_protocol_builder":
        raise ValueError("R50 R5 policy section changed")
    if data.get("protocol_status") not in P7_R50_REVIEW_SESSION_PROTOCOL_STATUS_REFS:
        raise ValueError("R50 R5 protocol status changed")
    if data.get("required_case_count") != P7_R50_REQUIRED_CASE_COUNT or data.get("case_distribution_total") != P7_R50_REQUIRED_CASE_COUNT:
        raise ValueError("R50 R5 must keep a 24-case protocol")
    if data.get("minimum_total_cases") != P7_R50_REQUIRED_CASE_COUNT:
        raise ValueError("R50 R5 minimum total cases must be 24")
    if tuple(data.get("reviewer_visible_field_refs") or ()) != P7_R50_REVIEWER_VISIBLE_FIELD_REFS:
        raise ValueError("R50 R5 reviewer visible fields changed")
    if tuple(data.get("reviewer_hidden_field_refs") or ()) != P7_R50_REVIEWER_HIDDEN_FIELD_REFS:
        raise ValueError("R50 R5 reviewer hidden fields changed")
    if tuple(data.get("rating_axis_refs") or ()) != P5_HUMAN_BLIND_QA_RATING_AXES:
        raise ValueError("R50 R5 rating axes changed")
    if safe_mapping(data.get("rating_axis_target_refs")) != dict(P5_HUMAN_BLIND_QA_TARGETS):
        raise ValueError("R50 R5 rating axis targets changed")
    if tuple(data.get("readfeel_blocker_id_refs") or ()) != P7_R48_READFEEL_BLOCKER_ID_REFS:
        raise ValueError("R50 R5 readfeel blocker ids changed")
    for true_key in (
        "question_need_observation_required",
        "rating_row_required_for_each_case",
        "execution_blocker_row_required_for_unreviewable_case",
        "reviewer_free_text_local_only",
        "body_full_reader_protocol_local_only",
        "blind_case_id_required",
        "case_ref_hidden_from_reviewer",
        "family_hidden_from_reviewer",
        "subscription_tier_hidden_from_reviewer",
        "controller_expected_result_hidden_from_reviewer",
        "gate_expected_result_hidden_from_reviewer",
        "p5_confirmed_conditions_hidden_from_reviewer",
        "p8_material_candidate_conditions_hidden_from_reviewer",
        "manual_run_decision_made_here",
        "r5_24_case_review_session_protocol_built",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R50 R5 must keep {true_key}=True")
    for false_key in (
        "question_text_required",
        "draft_question_text_allowed",
        "reviewer_free_text_bodyfree_export_allowed",
        "protocol_body_full_packet_generation_allowed_here",
        "protocol_human_review_run_allowed_here",
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R50 R5 must keep {false_key}=False")
    if tuple((row.get("family_ref"), row.get("case_count"), row.get("case_role")) for row in data.get("first_formal_case_distribution") or ()) != P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION:
        raise ValueError("R50 R5 first formal case distribution changed")
    if data.get("protocol_status") == "READY_FOR_24_CASE_LOCAL_REVIEW_PROTOCOL":
        if data.get("preflight_status") != "PASSED" or data.get("local_only_body_full_generation_allowed") is not True:
            raise ValueError("R50 R5 ready protocol requires passed R50-4 preflight")
        if data.get("execution_blocker_ids") or data.get("open_execution_blocker_ids"):
            raise ValueError("R50 R5 ready protocol must not carry execution blockers")
        if data.get("next_required_step") != P7_R50_R5_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R5 ready protocol must point to R50-6")
    else:
        if data.get("local_only_body_full_generation_allowed") is not False:
            raise ValueError("R50 R5 blocked protocol must not allow body-full generation")
        if data.get("next_required_step") != P7_R50_R5_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R5 blocked protocol must point to preflight resolution")
    unknown_blockers = sorted(set(data.get("execution_blocker_ids") or ()) - set(P7_R50_EXECUTION_BLOCKER_ID_REFS))
    if unknown_blockers:
        raise ValueError(f"R50 R5 execution blocker ids are not canonical: {unknown_blockers[:4]}")
    if tuple(data.get("implemented_steps") or ()) != P7_R50_R5_IMPLEMENTED_STEPS:
        raise ValueError("R50 R5 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_R5_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R5 not-yet steps changed")
    for true_key in (
        "r0_current_source_r49_handoff_bridge_refrozen",
        "r1_scope_schema_status_enum_fixed",
        "r2_prior_validation_evidence_adopted",
        "r3_manual_run_decision_built",
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R50 R5 must keep {true_key}=True")
    return True


def build_p7_r50_r4_r5_preflight_protocol_freeze(
    *,
    manual_run_decision_bodyfree: Mapping[str, Any] | None = None,
    local_review_root: Any = None,
    repo_roots: Sequence[Any] | None = None,
    export_roots: Sequence[Any] | None = None,
    explicit_allow_token: Any = None,
    export_candidate_refs: Sequence[Any] | Any | None = None,
    material_id: Any = "p7_r50_r4_r5_preflight_protocol_freeze",
) -> dict[str, Any]:
    """Build a compact combined R50-4/R50-5 body-free freeze."""

    r4 = build_p7_r50_local_only_root_explicit_allow_export_denylist_preflight(
        manual_run_decision_bodyfree=manual_run_decision_bodyfree,
        local_review_root=local_review_root,
        repo_roots=repo_roots,
        export_roots=export_roots,
        explicit_allow_token=explicit_allow_token,
        export_candidate_refs=export_candidate_refs,
    )
    r5 = build_p7_r50_review_session_protocol_bodyfree(
        local_only_root_explicit_allow_export_preflight=r4,
    )
    combined = {
        "schema_version": P7_R50_R4_R5_PREFLIGHT_PROTOCOL_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R50_STEP,
        "scope": P7_R50_SCOPE,
        "policy_kind": P7_R50_POLICY_KIND,
        "policy_section": "R50-4_R50-5_preflight_protocol_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r50_r4_r5_preflight_protocol_freeze", max_length=180),
        "r4_local_only_root_explicit_allow_export_denylist_preflight": r4,
        "r5_review_session_protocol_bodyfree": r5,
        "review_session_id": r5["review_session_id"],
        "preflight_status": r4["preflight_status"],
        "protocol_status": r5["protocol_status"],
        "local_only_body_full_generation_allowed": r5["local_only_body_full_generation_allowed"],
        "manual_run_decision_made_here": True,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "implemented_steps": list(P7_R50_R5_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R50_R5_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r49_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_prior_validation_evidence_adopted": True,
        "r3_manual_run_decision_built": True,
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built": True,
        "r5_24_case_review_session_protocol_built": True,
        "first_next_work_ref": P7_R50_FIRST_NEXT_WORK_REF,
        "next_required_step": r5["next_required_step"],
        "public_contract": public_contract_flags(),
        "r50_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_for(P7_R50_R5_FALSE_KEY_REFS),
    }
    assert_p7_r50_r4_r5_preflight_protocol_freeze_contract(combined)
    return combined


def assert_p7_r50_r4_r5_preflight_protocol_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_required_fields(
        data,
        required=P7_R50_R4_R5_PREFLIGHT_PROTOCOL_FREEZE_REQUIRED_FIELD_REFS,
        source="p7_r50_r4_r5_preflight_protocol_freeze",
    )
    _assert_common_with_false_keys(
        data,
        schema_version=P7_R50_R4_R5_PREFLIGHT_PROTOCOL_FREEZE_SCHEMA_VERSION,
        source="p7_r50_r4_r5_preflight_protocol_freeze",
        false_keys=P7_R50_R5_FALSE_KEY_REFS,
    )
    if data.get("policy_section") != "R50-4_R50-5_preflight_protocol_freeze":
        raise ValueError("R50 R4/R5 policy section changed")
    r4 = safe_mapping(data.get("r4_local_only_root_explicit_allow_export_denylist_preflight"))
    r5 = safe_mapping(data.get("r5_review_session_protocol_bodyfree"))
    assert_p7_r50_local_only_root_explicit_allow_export_denylist_preflight_contract(r4)
    assert_p7_r50_review_session_protocol_bodyfree_contract(r5)
    if data.get("preflight_status") != r4.get("preflight_status") or data.get("protocol_status") != r5.get("protocol_status"):
        raise ValueError("R50 R4/R5 status does not match nested materials")
    if data.get("local_only_body_full_generation_allowed") is not r5.get("local_only_body_full_generation_allowed"):
        raise ValueError("R50 R4/R5 local-only permission does not match R5")
    if tuple(data.get("implemented_steps") or ()) != P7_R50_R5_IMPLEMENTED_STEPS:
        raise ValueError("R50 R4/R5 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_R5_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R4/R5 not-yet steps changed")
    if data.get("manual_run_decision_made_here") is not True:
        raise ValueError("R50 R4/R5 must preserve manual decision made")
    if data.get("actual_manual_review_run_here") is not False or data.get("body_full_packet_generated_here") is not False:
        raise ValueError("R50 R4/R5 must not run review or generate body-full packets")
    return True


def _r6_request_status_and_reasons(protocol: Mapping[str, Any]) -> tuple[str, list[str], list[str]]:
    reason_refs: list[str] = []
    execution_blocker_ids: list[str] = []
    if protocol.get("protocol_status") != "READY_FOR_24_CASE_LOCAL_REVIEW_PROTOCOL":
        reason_refs.append("r50_5_protocol_not_ready")
        execution_blocker_ids.extend(dedupe_identifiers(protocol.get("execution_blocker_ids"), limit=20, max_length=120))
    if protocol.get("local_only_body_full_generation_allowed") is not True:
        reason_refs.append("local_only_body_full_generation_not_allowed_by_protocol")
        execution_blocker_ids.extend(dedupe_identifiers(protocol.get("open_execution_blocker_ids"), limit=20, max_length=120))
    if reason_refs:
        return "BLOCKED_BY_R50_5_PROTOCOL", dedupe_identifiers(reason_refs, limit=20, max_length=140), dedupe_identifiers(
            execution_blocker_ids or ["r50_scope_drift_detected"], limit=20, max_length=120
        )
    return "READY_FOR_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST", [
        "local_only_body_full_packet_generation_request_fixed_without_writing_packets"
    ], []


def build_p7_r50_local_only_body_full_packet_generation_request(
    *,
    review_session_protocol_bodyfree: Mapping[str, Any] | None = None,
    r5_review_session_protocol_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r50_local_only_body_full_packet_generation_request",
) -> dict[str, Any]:
    """Build the R50-6 request to generate local-only body-full packets later.

    This is a body-free control envelope.  It creates the request and permission
    boundary for the next manual local step, but it never writes local packets,
    never stores local paths/hashes, and never materializes reviewer payloads.
    """

    if review_session_protocol_bodyfree is not None and r5_review_session_protocol_bodyfree is not None:
        raise ValueError("provide only one R50-5 review-session protocol value")
    r5 = (
        safe_mapping(review_session_protocol_bodyfree)
        if review_session_protocol_bodyfree is not None
        else safe_mapping(r5_review_session_protocol_bodyfree)
        if r5_review_session_protocol_bodyfree is not None
        else build_p7_r50_review_session_protocol_bodyfree()
    )
    assert_p7_r50_review_session_protocol_bodyfree_contract(r5)

    request_status, reason_refs, execution_blocker_ids = _r6_request_status_and_reasons(r5)
    ready = request_status == "READY_FOR_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST"
    request = {
        "schema_version": P7_R50_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R50_STEP,
        "scope": P7_R50_SCOPE,
        "policy_kind": P7_R50_POLICY_KIND,
        "policy_section": "R50-6_local_only_body_full_packet_generation_request",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r50_local_only_body_full_packet_generation_request", max_length=180),
        "review_session_id": clean_identifier(r5.get("review_session_id"), default=P7_R50_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_session_status": "READY_FOR_LOCAL_BODY_FULL_PACKET_GENERATION" if ready else "PRECHECK_BLOCKED",
        "r5_protocol_schema_version": P7_R50_REVIEW_SESSION_PROTOCOL_BODYFREE_SCHEMA_VERSION,
        "r5_protocol_ref": clean_identifier(r5.get("material_id"), default="p7_r50_review_session_protocol_bodyfree", max_length=180),
        "preflight_status": clean_identifier(r5.get("preflight_status"), default="BLOCKED", max_length=80),
        "protocol_status": clean_identifier(r5.get("protocol_status"), default="BLOCKED_BY_R50_4_PREFLIGHT", max_length=100),
        "request_status": request_status,
        "request_reason_refs": reason_refs,
        "required_case_count": P7_R50_REQUIRED_CASE_COUNT,
        "case_distribution_total": _non_negative_int(r5.get("case_distribution_total")),
        "packet_kind": P7_R50_PACKET_KIND,
        "review_kind": P7_R50_REVIEW_KIND,
        "review_prompt_version": P7_R50_REVIEW_PROMPT_VERSION,
        "local_only_request": True,
        "local_review_root_ref": P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR,
        "explicit_allow_token_ref": P7_R50_EXPLICIT_BODY_FULL_ALLOW_TOKEN_REF,
        "storage_root_ref": P7_R47_STORAGE_ROOT_REF if ready else "not_ready",
        "root_path_exposed": False,
        "local_absolute_path_included": False,
        "packet_ref_manifest_expected_count": P7_R50_REQUIRED_CASE_COUNT if ready else 0,
        "body_full_packet_retention_max_hours": P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
        "reviewer_notes_retention_after_rating_hours": P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
        "disposal_required": True,
        "disposal_receipt_required": True,
        "body_free_export_allowed_before_disposal": False,
        "release_material_inclusion_allowed": False,
        "artifact_zip_inclusion_allowed": False,
        "premise_or_implemented_docs_inclusion_allowed": False,
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "local_only_directory_profile_refs": [
            "session_ref/body_full_packets.local_only",
            "session_ref/reviewer_forms.local_only",
            "session_ref/reviewer_notes.local_only",
        ],
        "bodyfree_after_purge_directory_profile_refs": [
            "bodyfree_rows.to_export_after_purge",
            "disposal_receipts.bodyfree",
            "summary.bodyfree",
        ],
        "reviewer_packet_body_source_refs_stored_here": False,
        "local_path_stored_here": False,
        "body_content_hash_stored_here": False,
        "command_executed_here": False,
        "file_written_here": False,
        "body_full_packet_generation_request_created_here": True,
        "body_full_packet_generation_allowed_for_next_manual_step": ready,
        "body_full_packet_generation_executed_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "body_full_writer_created_here": False,
        "local_reviewer_payload_materialized_here": False,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "manual_run_decision_made_here": True,
        "local_only_body_full_generation_allowed": ready,
        "r6_local_only_body_full_packet_generation_request_built": True,
        "execution_blocker_ids": [] if ready else execution_blocker_ids,
        "open_execution_blocker_ids": [] if ready else execution_blocker_ids,
        "implemented_steps": list(P7_R50_R6_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R50_R6_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r49_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_prior_validation_evidence_adopted": True,
        "r3_manual_run_decision_built": True,
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built": True,
        "r5_24_case_review_session_protocol_built": True,
        "first_next_work_ref": P7_R50_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R50_R6_NEXT_REQUIRED_STEP_REF if ready else P7_R50_R6_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r50_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_for(P7_R50_R6_FALSE_KEY_REFS),
    }
    assert_p7_r50_local_only_body_full_packet_generation_request_contract(request)
    return request


def assert_p7_r50_local_only_body_full_packet_generation_request_contract(request: Mapping[str, Any]) -> bool:
    data = safe_mapping(request)
    _assert_required_fields(
        data,
        required=P7_R50_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_REQUIRED_FIELD_REFS,
        source="p7_r50_r6_local_only_body_full_packet_generation_request",
    )
    _assert_common_with_false_keys(
        data,
        schema_version=P7_R50_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION,
        source="p7_r50_r6_local_only_body_full_packet_generation_request",
        false_keys=P7_R50_R6_FALSE_KEY_REFS,
    )
    if data.get("policy_section") != "R50-6_local_only_body_full_packet_generation_request":
        raise ValueError("R50 R6 policy section changed")
    if data.get("request_status") not in P7_R50_BODY_FULL_PACKET_GENERATION_REQUEST_STATUS_REFS:
        raise ValueError("R50 R6 request status changed")
    if data.get("required_case_count") != P7_R50_REQUIRED_CASE_COUNT:
        raise ValueError("R50 R6 required case count changed")
    if data.get("body_full_packet_generation_request_created_here") is not True:
        raise ValueError("R50 R6 must create only the generation request")
    for false_key in (
        "root_path_exposed",
        "local_absolute_path_included",
        "body_free_export_allowed_before_disposal",
        "release_material_inclusion_allowed",
        "artifact_zip_inclusion_allowed",
        "premise_or_implemented_docs_inclusion_allowed",
        "local_packet_exported",
        "content_hash_of_body_stored",
        "reviewer_packet_body_source_refs_stored_here",
        "local_path_stored_here",
        "body_content_hash_stored_here",
        "command_executed_here",
        "file_written_here",
        "body_full_packet_generation_executed_here",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
        "body_full_writer_created_here",
        "local_reviewer_payload_materialized_here",
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R50 R6 must keep {false_key}=False")
    for true_key in (
        "local_only_request",
        "disposal_required",
        "disposal_receipt_required",
        "manual_run_decision_made_here",
        "r6_local_only_body_full_packet_generation_request_built",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R50 R6 must keep {true_key}=True")
    if data.get("body_full_packet_retention_max_hours") != P7_R47_BODY_FULL_PACKET_RETENTION_HOURS:
        raise ValueError("R50 R6 must inherit R47 body-full packet retention hours")
    if data.get("reviewer_notes_retention_after_rating_hours") != P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS:
        raise ValueError("R50 R6 must inherit R47 reviewer notes retention after rating hours")
    if data.get("request_status") == "READY_FOR_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST":
        if data.get("protocol_status") != "READY_FOR_24_CASE_LOCAL_REVIEW_PROTOCOL":
            raise ValueError("R50 R6 ready request requires ready R50-5 protocol")
        if data.get("local_only_body_full_generation_allowed") is not True:
            raise ValueError("R50 R6 ready request must allow the next local manual step")
        if data.get("body_full_packet_generation_allowed_for_next_manual_step") is not True:
            raise ValueError("R50 R6 ready request must set next-step generation permission")
        if data.get("packet_ref_manifest_expected_count") != P7_R50_REQUIRED_CASE_COUNT:
            raise ValueError("R50 R6 ready request must expect 24 packet refs")
        if data.get("execution_blocker_ids") or data.get("open_execution_blocker_ids"):
            raise ValueError("R50 R6 ready request must not carry execution blockers")
        if data.get("next_required_step") != P7_R50_R6_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R6 ready request must point to R50-7")
    else:
        if data.get("local_only_body_full_generation_allowed") is not False:
            raise ValueError("R50 R6 blocked request must not allow generation")
        if data.get("body_full_packet_generation_allowed_for_next_manual_step") is not False:
            raise ValueError("R50 R6 blocked request cannot permit the next local step")
        if data.get("packet_ref_manifest_expected_count") != 0:
            raise ValueError("R50 R6 blocked request must not expect packet refs")
        if data.get("next_required_step") != P7_R50_R6_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R6 blocked request must point to protocol resolution")
    unknown_blockers = sorted(set(data.get("execution_blocker_ids") or ()) - set(P7_R50_EXECUTION_BLOCKER_ID_REFS))
    if unknown_blockers:
        raise ValueError(f"R50 R6 execution blocker ids are not canonical: {unknown_blockers[:4]}")
    if tuple(data.get("implemented_steps") or ()) != P7_R50_R6_IMPLEMENTED_STEPS:
        raise ValueError("R50 R6 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_R6_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R6 not-yet steps changed")
    return True


def _r7_instruction_form_status_and_reasons(request: Mapping[str, Any]) -> tuple[str, list[str], list[str]]:
    reason_refs: list[str] = []
    execution_blocker_ids: list[str] = []
    if request.get("request_status") != "READY_FOR_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST":
        reason_refs.append("r50_6_packet_generation_request_not_ready")
        execution_blocker_ids.extend(dedupe_identifiers(request.get("execution_blocker_ids"), limit=20, max_length=120))
    if request.get("local_only_body_full_generation_allowed") is not True:
        reason_refs.append("local_only_body_full_generation_not_allowed_by_request")
        execution_blocker_ids.extend(dedupe_identifiers(request.get("open_execution_blocker_ids"), limit=20, max_length=120))
    if reason_refs:
        return "BLOCKED_BY_R50_6_PACKET_GENERATION_REQUEST", dedupe_identifiers(reason_refs, limit=20, max_length=140), dedupe_identifiers(
            execution_blocker_ids or ["r50_scope_drift_detected"], limit=20, max_length=120
        )
    return "READY_FOR_REVIEWER_INSTRUCTION_AND_RATING_FORM", [
        "reviewer_instruction_and_rating_form_frozen_without_running_review"
    ], []


def build_p7_r50_reviewer_instruction_rating_form_freeze(
    *,
    local_only_body_full_packet_generation_request: Mapping[str, Any] | None = None,
    r6_local_only_body_full_packet_generation_request: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r50_reviewer_instruction_rating_form_freeze",
) -> dict[str, Any]:
    """Build the R50-7 reviewer instruction and rating-form freeze.

    The freeze contains only body-free/static form metadata.  It does not show a
    reviewer any case body, does not write rating rows, and does not run actual
    human review.
    """

    if local_only_body_full_packet_generation_request is not None and r6_local_only_body_full_packet_generation_request is not None:
        raise ValueError("provide only one R50-6 packet generation request value")
    r6 = (
        safe_mapping(local_only_body_full_packet_generation_request)
        if local_only_body_full_packet_generation_request is not None
        else safe_mapping(r6_local_only_body_full_packet_generation_request)
        if r6_local_only_body_full_packet_generation_request is not None
        else build_p7_r50_local_only_body_full_packet_generation_request()
    )
    assert_p7_r50_local_only_body_full_packet_generation_request_contract(r6)

    instruction_status, reason_refs, execution_blocker_ids = _r7_instruction_form_status_and_reasons(r6)
    ready = instruction_status == "READY_FOR_REVIEWER_INSTRUCTION_AND_RATING_FORM"
    freeze = {
        "schema_version": P7_R50_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R50_STEP,
        "scope": P7_R50_SCOPE,
        "policy_kind": P7_R50_POLICY_KIND,
        "policy_section": "R50-7_reviewer_instruction_rating_form_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r50_reviewer_instruction_rating_form_freeze", max_length=180),
        "review_session_id": clean_identifier(r6.get("review_session_id"), default=P7_R50_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_session_status": "READY_FOR_LOCAL_BODY_FULL_PACKET_GENERATION" if ready else "PRECHECK_BLOCKED",
        "r6_packet_generation_request_schema_version": P7_R50_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION,
        "r6_packet_generation_request_ref": clean_identifier(r6.get("material_id"), default="p7_r50_local_only_body_full_packet_generation_request", max_length=180),
        "request_status": clean_identifier(r6.get("request_status"), default="BLOCKED_BY_R50_5_PROTOCOL", max_length=120),
        "instruction_form_status": instruction_status,
        "instruction_form_reason_refs": reason_refs,
        "required_case_count": P7_R50_REQUIRED_CASE_COUNT,
        "review_prompt_version": P7_R50_REVIEW_PROMPT_VERSION,
        "reviewer_instruction_version": P7_R50_REVIEWER_INSTRUCTION_VERSION,
        "rating_form_version": P7_R50_RATING_FORM_VERSION,
        "reviewer_check_item_refs": list(P7_R50_REVIEWER_CHECK_ITEM_REFS),
        "required_reviewer_check_label_refs": list(P7_R50_REQUIRED_REVIEWER_CHECK_LABEL_REFS),
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
        "local_only_body_full_generation_allowed": ready,
        "manual_run_decision_made_here": True,
        "r7_reviewer_instruction_rating_form_freeze_built": True,
        "execution_blocker_ids": [] if ready else execution_blocker_ids,
        "open_execution_blocker_ids": [] if ready else execution_blocker_ids,
        "implemented_steps": list(P7_R50_R7_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R50_R7_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r49_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_prior_validation_evidence_adopted": True,
        "r3_manual_run_decision_built": True,
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built": True,
        "r5_24_case_review_session_protocol_built": True,
        "r6_local_only_body_full_packet_generation_request_built": True,
        "first_next_work_ref": P7_R50_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R50_R7_NEXT_REQUIRED_STEP_REF if ready else P7_R50_R7_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r50_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_for(P7_R50_R7_FALSE_KEY_REFS),
    }
    assert_p7_r50_reviewer_instruction_rating_form_freeze_contract(freeze)
    return freeze


def assert_p7_r50_reviewer_instruction_rating_form_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_required_fields(
        data,
        required=P7_R50_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_REQUIRED_FIELD_REFS,
        source="p7_r50_r7_reviewer_instruction_rating_form_freeze",
    )
    _assert_common_with_false_keys(
        data,
        schema_version=P7_R50_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION,
        source="p7_r50_r7_reviewer_instruction_rating_form_freeze",
        false_keys=P7_R50_R7_FALSE_KEY_REFS,
    )
    if data.get("policy_section") != "R50-7_reviewer_instruction_rating_form_freeze":
        raise ValueError("R50 R7 policy section changed")
    if data.get("instruction_form_status") not in P7_R50_REVIEWER_INSTRUCTION_RATING_FORM_STATUS_REFS:
        raise ValueError("R50 R7 instruction/rating form status changed")
    if data.get("required_case_count") != P7_R50_REQUIRED_CASE_COUNT:
        raise ValueError("R50 R7 required case count changed")
    if tuple(data.get("reviewer_check_item_refs") or ()) != P7_R50_REVIEWER_CHECK_ITEM_REFS:
        raise ValueError("R50 R7 reviewer check items changed")
    if tuple(data.get("required_reviewer_check_label_refs") or ()) != P7_R50_REQUIRED_REVIEWER_CHECK_LABEL_REFS:
        raise ValueError("R50 R7 reviewer check labels changed")
    if tuple(data.get("rating_axis_refs") or ()) != P5_HUMAN_BLIND_QA_RATING_AXES:
        raise ValueError("R50 R7 rating axes changed")
    if safe_mapping(data.get("rating_axis_target_refs")) != dict(P5_HUMAN_BLIND_QA_TARGETS):
        raise ValueError("R50 R7 rating targets changed")
    if data.get("rating_axis_count") != len(P5_HUMAN_BLIND_QA_RATING_AXES):
        raise ValueError("R50 R7 must keep six rating axes")
    if data.get("rating_score_min") != 0.0 or data.get("rating_score_max") != 1.0:
        raise ValueError("R50 R7 score bounds changed")
    if tuple(data.get("verdict_refs") or ()) != P7_R50_RATING_VERDICT_REFS:
        raise ValueError("R50 R7 verdict refs changed")
    if tuple(data.get("readfeel_blocker_id_refs") or ()) != P7_R48_READFEEL_BLOCKER_ID_REFS:
        raise ValueError("R50 R7 readfeel blocker ids changed")
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
        "manual_run_decision_made_here",
        "r7_reviewer_instruction_rating_form_freeze_built",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R50 R7 must keep {true_key}=True")
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
            raise ValueError(f"R50 R7 must keep {false_key}=False")
    if data.get("instruction_form_status") == "READY_FOR_REVIEWER_INSTRUCTION_AND_RATING_FORM":
        if data.get("request_status") != "READY_FOR_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST":
            raise ValueError("R50 R7 ready form requires ready R50-6 request")
        if data.get("local_only_body_full_generation_allowed") is not True:
            raise ValueError("R50 R7 ready form must preserve local-only generation permission")
        if data.get("execution_blocker_ids") or data.get("open_execution_blocker_ids"):
            raise ValueError("R50 R7 ready form must not carry execution blockers")
        if data.get("next_required_step") != P7_R50_R7_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R7 ready form must point to R50-8")
    else:
        if data.get("local_only_body_full_generation_allowed") is not False:
            raise ValueError("R50 R7 blocked form must not preserve generation permission")
        if data.get("next_required_step") != P7_R50_R7_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R7 blocked form must point to R50-6 resolution")
    unknown_blockers = sorted(set(data.get("execution_blocker_ids") or ()) - set(P7_R50_EXECUTION_BLOCKER_ID_REFS))
    if unknown_blockers:
        raise ValueError(f"R50 R7 execution blocker ids are not canonical: {unknown_blockers[:4]}")
    if tuple(data.get("implemented_steps") or ()) != P7_R50_R7_IMPLEMENTED_STEPS:
        raise ValueError("R50 R7 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_R7_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R7 not-yet steps changed")
    return True


def build_p7_r50_r6_r7_packet_request_rating_form_freeze(
    *,
    review_session_protocol_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r50_r6_r7_packet_request_rating_form_freeze",
) -> dict[str, Any]:
    """Build a compact combined R50-6/R50-7 body-free freeze."""

    r6 = build_p7_r50_local_only_body_full_packet_generation_request(
        review_session_protocol_bodyfree=review_session_protocol_bodyfree
    )
    r7 = build_p7_r50_reviewer_instruction_rating_form_freeze(
        local_only_body_full_packet_generation_request=r6
    )
    combined = {
        "schema_version": P7_R50_R6_R7_PACKET_REQUEST_RATING_FORM_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R50_STEP,
        "scope": P7_R50_SCOPE,
        "policy_kind": P7_R50_POLICY_KIND,
        "policy_section": "R50-6_R50-7_packet_request_rating_form_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r50_r6_r7_packet_request_rating_form_freeze", max_length=180),
        "r6_local_only_body_full_packet_generation_request": r6,
        "r7_reviewer_instruction_rating_form_freeze": r7,
        "review_session_id": r7["review_session_id"],
        "request_status": r6["request_status"],
        "instruction_form_status": r7["instruction_form_status"],
        "local_only_body_full_generation_allowed": r7["local_only_body_full_generation_allowed"],
        "manual_run_decision_made_here": True,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "actual_rating_rows_materialized_here": False,
        "implemented_steps": list(P7_R50_R7_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R50_R7_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r49_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_prior_validation_evidence_adopted": True,
        "r3_manual_run_decision_built": True,
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built": True,
        "r5_24_case_review_session_protocol_built": True,
        "r6_local_only_body_full_packet_generation_request_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": True,
        "first_next_work_ref": P7_R50_FIRST_NEXT_WORK_REF,
        "next_required_step": r7["next_required_step"],
        "public_contract": public_contract_flags(),
        "r50_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_for(P7_R50_R7_FALSE_KEY_REFS),
    }
    assert_p7_r50_r6_r7_packet_request_rating_form_freeze_contract(combined)
    return combined


def assert_p7_r50_r6_r7_packet_request_rating_form_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_required_fields(
        data,
        required=P7_R50_R6_R7_PACKET_REQUEST_RATING_FORM_FREEZE_REQUIRED_FIELD_REFS,
        source="p7_r50_r6_r7_packet_request_rating_form_freeze",
    )
    _assert_common_with_false_keys(
        data,
        schema_version=P7_R50_R6_R7_PACKET_REQUEST_RATING_FORM_FREEZE_SCHEMA_VERSION,
        source="p7_r50_r6_r7_packet_request_rating_form_freeze",
        false_keys=P7_R50_R7_FALSE_KEY_REFS,
    )
    if data.get("policy_section") != "R50-6_R50-7_packet_request_rating_form_freeze":
        raise ValueError("R50 R6/R7 policy section changed")
    r6 = safe_mapping(data.get("r6_local_only_body_full_packet_generation_request"))
    r7 = safe_mapping(data.get("r7_reviewer_instruction_rating_form_freeze"))
    assert_p7_r50_local_only_body_full_packet_generation_request_contract(r6)
    assert_p7_r50_reviewer_instruction_rating_form_freeze_contract(r7)
    if data.get("request_status") != r6.get("request_status"):
        raise ValueError("R50 R6/R7 request status does not match nested request")
    if data.get("instruction_form_status") != r7.get("instruction_form_status"):
        raise ValueError("R50 R6/R7 instruction status does not match nested form")
    if data.get("local_only_body_full_generation_allowed") is not r7.get("local_only_body_full_generation_allowed"):
        raise ValueError("R50 R6/R7 local-only permission mismatch")
    if tuple(data.get("implemented_steps") or ()) != P7_R50_R7_IMPLEMENTED_STEPS:
        raise ValueError("R50 R6/R7 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_R7_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R6/R7 not-yet steps changed")
    if data.get("actual_manual_review_run_here") is not False:
        raise ValueError("R50 R6/R7 must not run actual manual review")
    if data.get("body_full_packet_generated_here") is not False:
        raise ValueError("R50 R6/R7 must not generate body-full packets")
    if data.get("actual_rating_rows_materialized_here") is not False:
        raise ValueError("R50 R6/R7 must not materialize rating rows")
    return True



def _contains_forbidden_key_ref(value: Any, forbidden_refs: set[str]) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in forbidden_refs:
                return True
            if _contains_forbidden_key_ref(child, forbidden_refs):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_key_ref(child, forbidden_refs) for child in value)
    return False



def _assert_identifier_sequence_r50(
    value: Any,
    *,
    source: str,
    allowed_refs: Sequence[str] | None = None,
    limit: int = 120,
) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise ValueError(f"{source} must be a sequence of identifiers")
    original = list(value)
    cleaned = dedupe_identifiers(original, limit=limit, max_length=160)
    if len(cleaned) != len(original):
        raise ValueError(f"{source} must contain unique non-empty identifiers")
    if allowed_refs is not None:
        unknown = sorted(set(cleaned) - set(allowed_refs))
        if unknown:
            raise ValueError(f"{source} contains non-canonical identifiers: {unknown[:4]}")
    return cleaned


def _assert_bodyfree_mapping_input(value: Mapping[str, Any], *, source: str, require_body_free_flag: bool = True) -> None:
    data = safe_mapping(value)
    if require_body_free_flag and data.get("body_free") is not True:
        raise ValueError(f"{source} must be body_free=True before R50 can ingest it")
    _assert_no_forbidden_body_keys(data, source=source)
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)


def _case_ref_fields_r50(case_row: Mapping[str, Any]) -> dict[str, str]:
    row = safe_mapping(case_row)
    _assert_bodyfree_mapping_input(row, source="p7_r50.case_row_for_rating_or_blocker")
    case = {
        "review_session_id": clean_identifier(row.get("review_session_id"), default=P7_R50_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "packet_ref_id": clean_identifier(row.get("packet_ref_id"), default="packet_ref", max_length=160),
        "blind_case_id": clean_identifier(row.get("blind_case_id"), default="blind_case", max_length=160),
        "case_ref_id": clean_identifier(row.get("case_ref_id"), default="case_ref", max_length=160),
        "family": clean_identifier(row.get("family"), default="unknown", max_length=160),
        "case_role": clean_identifier(row.get("case_role"), default="unknown", max_length=120),
    }
    if case["family"] not in P5_HUMAN_BLIND_QA_FAMILIES:
        raise ValueError("R50 rating/blocker row requires a known P5 family")
    if case["case_role"] not in P7_R48_P5_CASE_ROLE_REFS:
        raise ValueError("R50 rating/blocker row requires a known P5 case role")
    if not all(case.values()):
        raise ValueError("R50 rating/blocker row requires complete body-free case identifiers")
    return case


def _normalize_axis_scores_r50(axis_scores: Any) -> dict[str, float]:
    scores = safe_mapping(axis_scores)
    if set(scores) != set(P5_HUMAN_BLIND_QA_RATING_AXES):
        raise ValueError("R50 R8 rating row requires every P5 axis exactly once; extra/missing axes are not allowed")
    normalized: dict[str, float] = {}
    for axis in P5_HUMAN_BLIND_QA_RATING_AXES:
        raw = scores.get(axis)
        if isinstance(raw, bool) or not isinstance(raw, (int, float, str)):
            raise ValueError("R50 R8 axis scores must be explicit numeric reviewer ratings")
        try:
            score = float(raw)
        except ValueError as exc:
            raise ValueError("R50 R8 axis scores must be numeric") from exc
        if not 0.0 <= score <= 1.0:
            raise ValueError("R50 R8 axis scores must stay within 0.0-1.0")
        normalized[axis] = score
    return normalized


def _assert_r50_verdict_score_blocker_consistency(
    *,
    verdict: str,
    axis_scores: Mapping[str, float],
    blocker_ids: Sequence[str],
) -> None:
    if verdict == "PASS":
        if blocker_ids:
            raise ValueError("R50 R8 PASS rating rows must not carry readfeel blocker_ids")
        for axis, target in P5_HUMAN_BLIND_QA_TARGETS.items():
            if float(axis_scores[axis]) < float(target):
                raise ValueError("R50 R8 PASS cannot be assigned when a required axis is below target")
    if verdict in {"RED", "REPAIR_REQUIRED"} and not blocker_ids:
        raise ValueError("R50 R8 RED/REPAIR_REQUIRED rows must carry at least one readfeel blocker_id")


def normalize_p7_r50_rating_capture_row_bodyfree(
    *,
    review_result: Mapping[str, Any],
    case_row: Mapping[str, Any],
    reviewer_ref: Any = "local_reviewer_ref",
    reviewed_at: Any = "reviewed_at_unset",
    body_removed: bool = False,
) -> dict[str, Any]:
    """Normalize sanitized reviewer ratings into one R50 body-free rating row.

    The caller supplies already-sanitized reviewer selections.  This helper does
    not run human review, does not read body-full packets, and does not preserve
    reviewer free text.
    """

    result = safe_mapping(review_result)
    _assert_bodyfree_mapping_input(result, source="p7_r50.rating_row_normalizer.review_result")
    if _contains_forbidden_key_ref(result, set(P7_R48_P5_RATING_BLOCKER_FORBIDDEN_FIELD_REFS)):
        raise ValueError("R50 R8 rating input contains body payload, reviewer text, or forbidden machine fields")
    if result.get("machine_metrics_used_for_readfeel") is True or result.get("machine_auto_score_used") is True:
        raise ValueError("R50 R8 machine metrics/auto score must not supplement human readfeel ratings")
    if result.get("reviewer_free_text_included") is True:
        raise ValueError("R50 R8 reviewer free text must not be retained in body-free rating rows")

    case = _case_ref_fields_r50(case_row)
    axis_scores = _normalize_axis_scores_r50(result.get("axis_scores"))
    verdict = clean_identifier(result.get("verdict"), default="", max_length=60)
    if verdict not in P7_R50_RATING_VERDICT_REFS or verdict not in P7_R48_P5_REVIEWABLE_VERDICTS:
        raise ValueError("R50 R8 verdict must be PASS/YELLOW/REPAIR_REQUIRED/RED only")
    reasons = _assert_identifier_sequence_r50(
        result.get("sanitized_reason_ids") or [],
        source="p7_r50_rating_row.sanitized_reason_ids",
        allowed_refs=P7_R48_SANITIZED_REASON_ID_REFS,
    )
    blockers = _assert_identifier_sequence_r50(
        result.get("blocker_ids") or [],
        source="p7_r50_rating_row.blocker_ids",
        allowed_refs=P7_R48_READFEEL_BLOCKER_ID_REFS,
    )
    _assert_r50_verdict_score_blocker_consistency(verdict=verdict, axis_scores=axis_scores, blocker_ids=blockers)
    if verdict in {"RED", "REPAIR_REQUIRED"} and not reasons:
        raise ValueError("R50 R8 RED/REPAIR_REQUIRED rows must carry sanitized reason ids")
    row = {
        "schema_version": P7_R50_RATING_CAPTURE_ROW_BODYFREE_SCHEMA_VERSION,
        **case,
        "reviewer_ref": clean_identifier(reviewer_ref, default="local_reviewer_ref", max_length=120),
        "reviewed_at": clean_identifier(reviewed_at, default="reviewed_at_unset", max_length=120),
        "axis_scores": axis_scores,
        "verdict": verdict,
        "sanitized_reason_ids": reasons,
        "blocker_ids": blockers,
        "reviewer_free_text_included": False,
        "body_removed": bool(body_removed),
        "body_free": True,
    }
    assert_p7_r50_rating_capture_row_bodyfree_contract(row)
    return row


def assert_p7_r50_rating_capture_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R50_RATING_CAPTURE_ROW_BODYFREE_REQUIRED_FIELD_REFS, source="p7_r50_rating_capture_row_bodyfree")
    if data.get("schema_version") != P7_R50_RATING_CAPTURE_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R50 rating row schema version changed")
    _assert_bodyfree_mapping_input(data, source="p7_r50_rating_capture_row_bodyfree")
    if data.get("family") not in P5_HUMAN_BLIND_QA_FAMILIES:
        raise ValueError("R50 rating row family changed")
    if data.get("case_role") not in P7_R48_P5_CASE_ROLE_REFS:
        raise ValueError("R50 rating row case_role changed")
    axis_scores = safe_mapping(data.get("axis_scores"))
    if set(axis_scores) != set(P5_HUMAN_BLIND_QA_RATING_AXES):
        raise ValueError("R50 rating row requires all and only P5 rating axes")
    for score in axis_scores.values():
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0.0 <= float(score) <= 1.0:
            raise ValueError("R50 rating row axis scores must be numbers from 0.0 to 1.0")
    verdict = clean_identifier(data.get("verdict"), default="", max_length=60)
    if verdict not in P7_R50_RATING_VERDICT_REFS:
        raise ValueError("R50 rating row verdict enum changed")
    reasons = _assert_identifier_sequence_r50(
        data.get("sanitized_reason_ids"),
        source="p7_r50_rating_row.sanitized_reason_ids",
        allowed_refs=P7_R48_SANITIZED_REASON_ID_REFS,
    )
    blockers = _assert_identifier_sequence_r50(
        data.get("blocker_ids"),
        source="p7_r50_rating_row.blocker_ids",
        allowed_refs=P7_R48_READFEEL_BLOCKER_ID_REFS,
    )
    _assert_r50_verdict_score_blocker_consistency(verdict=verdict, axis_scores=axis_scores, blocker_ids=blockers)
    if verdict in {"RED", "REPAIR_REQUIRED"} and not reasons:
        raise ValueError("R50 RED/REPAIR_REQUIRED rating rows must carry sanitized reason ids")
    if data.get("reviewer_free_text_included") is not False:
        raise ValueError("R50 rating row must not include reviewer free text")
    if not isinstance(data.get("body_removed"), bool):
        raise ValueError("R50 rating row must carry boolean body_removed")
    return True


def _r50_execution_blocker_kind(execution_blocker_id: str) -> str:
    if execution_blocker_id == "r50_missing_r49_handoff":
        return "HANDOFF"
    if "green_evidence" in execution_blocker_id:
        return "VALIDATION"
    if execution_blocker_id in {"r50_local_review_root_missing", "r50_local_review_root_invalid"}:
        return "LOCAL_ROOT"
    if execution_blocker_id == "r50_explicit_allow_missing":
        return "EXPLICIT_ALLOW"
    if execution_blocker_id in {
        "r50_disposal_plan_missing",
        "r50_disposal_receipt_missing",
        "r50_disposal_failed",
        "r50_disposal_not_verified",
    }:
        return "DISPOSAL"
    if execution_blocker_id in {
        "r50_body_full_packet_generation_failed",
        "r50_body_full_packet_export_violation",
    }:
        return "GENERATION"
    if execution_blocker_id == "r50_review_aborted_before_rating":
        return "REVIEW"
    if execution_blocker_id == "r50_rating_rows_incomplete":
        return "RATING"
    if execution_blocker_id == "r50_question_need_observation_rows_incomplete":
        return "QUESTION_OBSERVATION"
    if execution_blocker_id == "r50_body_free_leak_detected":
        return "BODY_FREE_LEAK"
    if execution_blocker_id == "r50_scope_drift_detected":
        return "SCOPE"
    return "VALIDATION"


def build_p7_r50_readfeel_blocker_row_bodyfree(
    *,
    case_row: Mapping[str, Any],
    blocker_id: Any,
    blocker_kind: Any = "REPAIR_REQUIRED",
    blocker_status: Any = "OPEN",
    sanitized_reason_ids: Sequence[Any] | None = None,
    body_removed: bool = False,
) -> dict[str, Any]:
    case = _case_ref_fields_r50(case_row)
    blocker = clean_identifier(blocker_id, default="", max_length=160)
    if blocker not in P7_R48_READFEEL_BLOCKER_ID_REFS:
        raise ValueError("R50 R9 readfeel blocker row requires a P5 readfeel blocker_id")
    kind = clean_identifier(blocker_kind, default="REPAIR_REQUIRED", max_length=80)
    if kind not in P7_R48_P5_BLOCKER_KINDS or kind == "EXECUTION_BLOCKER":
        raise ValueError("R50 R9 readfeel blocker row must not use EXECUTION_BLOCKER kind")
    status = clean_identifier(blocker_status, default="OPEN", max_length=80)
    if status not in P7_R48_P5_BLOCKER_STATUSES:
        raise ValueError("R50 R9 readfeel blocker status enum changed")
    reasons = _assert_identifier_sequence_r50(
        sanitized_reason_ids or [blocker],
        source="p7_r50_readfeel_blocker_row.sanitized_reason_ids",
        allowed_refs=P7_R48_SANITIZED_REASON_ID_REFS,
    )
    row = {
        "schema_version": P7_R50_READFEEL_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        **case,
        "blocker_id": blocker,
        "blocker_kind": kind,
        "blocker_status": status,
        "sanitized_reason_ids": reasons,
        "reviewer_free_text_included": False,
        "body_removed": bool(body_removed),
        "body_free": True,
    }
    assert_p7_r50_readfeel_blocker_row_bodyfree_contract(row)
    return row


def assert_p7_r50_readfeel_blocker_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R50_READFEEL_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS, source="p7_r50_readfeel_blocker_row_bodyfree")
    if data.get("schema_version") != P7_R50_READFEEL_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R50 readfeel blocker row schema version changed")
    _assert_bodyfree_mapping_input(data, source="p7_r50_readfeel_blocker_row_bodyfree")
    if data.get("family") not in P5_HUMAN_BLIND_QA_FAMILIES:
        raise ValueError("R50 readfeel blocker row family changed")
    if data.get("case_role") not in P7_R48_P5_CASE_ROLE_REFS:
        raise ValueError("R50 readfeel blocker row case_role changed")
    if data.get("blocker_id") not in P7_R48_READFEEL_BLOCKER_ID_REFS:
        raise ValueError("R50 readfeel blocker row must carry a readfeel blocker id")
    if data.get("blocker_kind") not in P7_R48_P5_BLOCKER_KINDS or data.get("blocker_kind") == "EXECUTION_BLOCKER":
        raise ValueError("R50 readfeel blocker row must not mix execution blocker kind")
    if data.get("blocker_status") not in P7_R48_P5_BLOCKER_STATUSES:
        raise ValueError("R50 readfeel blocker row status enum changed")
    _assert_identifier_sequence_r50(
        data.get("sanitized_reason_ids"),
        source="p7_r50_readfeel_blocker_row.sanitized_reason_ids",
        allowed_refs=P7_R48_SANITIZED_REASON_ID_REFS,
    )
    if data.get("reviewer_free_text_included") is not False:
        raise ValueError("R50 readfeel blocker row must not include reviewer free text")
    if not isinstance(data.get("body_removed"), bool):
        raise ValueError("R50 readfeel blocker row must carry boolean body_removed")
    return True


def build_p7_r50_execution_blocker_row_bodyfree(
    *,
    case_row: Mapping[str, Any],
    execution_blocker_id: Any,
    execution_blocker_status: Any = "OPEN",
) -> dict[str, Any]:
    case = _case_ref_fields_r50(case_row)
    blocker = clean_identifier(execution_blocker_id, default="", max_length=160)
    if blocker not in P7_R50_EXECUTION_BLOCKER_ID_REFS:
        raise ValueError("R50 R9 execution blocker id changed")
    status = clean_identifier(execution_blocker_status, default="OPEN", max_length=80)
    if status not in P7_R50_EXECUTION_BLOCKER_STATUS_REFS:
        raise ValueError("R50 R9 execution blocker status enum changed")
    row = {
        "schema_version": P7_R50_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "review_session_id": case["review_session_id"],
        "packet_ref_id": case["packet_ref_id"],
        "blind_case_id": case["blind_case_id"],
        "case_ref_id": case["case_ref_id"],
        "family": case["family"],
        "execution_blocker_id": blocker,
        "execution_blocker_kind": _r50_execution_blocker_kind(blocker),
        "execution_blocker_status": status,
        "readfeel_verdict_not_assigned": True,
        "body_free": True,
    }
    assert_p7_r50_execution_blocker_row_bodyfree_contract(row)
    return row


def assert_p7_r50_execution_blocker_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R50_EXECUTION_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS, source="p7_r50_execution_blocker_row_bodyfree")
    if data.get("schema_version") != P7_R50_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R50 execution blocker row schema version changed")
    _assert_bodyfree_mapping_input(data, source="p7_r50_execution_blocker_row_bodyfree")
    if data.get("family") not in P5_HUMAN_BLIND_QA_FAMILIES:
        raise ValueError("R50 execution blocker row family changed")
    blocker = clean_identifier(data.get("execution_blocker_id"), default="", max_length=160)
    if blocker not in P7_R50_EXECUTION_BLOCKER_ID_REFS:
        raise ValueError("R50 execution blocker row id changed")
    if data.get("execution_blocker_kind") not in P7_R50_EXECUTION_BLOCKER_KIND_REFS:
        raise ValueError("R50 execution blocker kind changed")
    if data.get("execution_blocker_kind") != _r50_execution_blocker_kind(blocker):
        raise ValueError("R50 execution blocker kind must match blocker id classification")
    if data.get("execution_blocker_status") not in P7_R50_EXECUTION_BLOCKER_STATUS_REFS:
        raise ValueError("R50 execution blocker status changed")
    if data.get("readfeel_verdict_not_assigned") is not True:
        raise ValueError("R50 execution blocker rows must not assign readfeel verdicts")
    return True


def _r8_status_from_r7(r7: Mapping[str, Any]) -> tuple[str, list[str]]:
    if r7.get("instruction_form_status") != "READY_FOR_REVIEWER_INSTRUCTION_AND_RATING_FORM":
        return "BLOCKED_BY_R50_7_REVIEWER_INSTRUCTION_RATING_FORM", ["r7_reviewer_instruction_rating_form_not_ready"]
    return "READY_FOR_RATING_ROW_NORMALIZATION", ["r7_reviewer_instruction_rating_form_ready"]


def build_p7_r50_rating_row_normalizer_bodyfree(
    *,
    reviewer_instruction_rating_form_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r50_rating_row_normalizer_bodyfree",
) -> dict[str, Any]:
    """Build R50-8 rating row normalizer policy material without running review."""

    r7 = safe_mapping(reviewer_instruction_rating_form_freeze) if reviewer_instruction_rating_form_freeze is not None else build_p7_r50_reviewer_instruction_rating_form_freeze()
    assert_p7_r50_reviewer_instruction_rating_form_freeze_contract(r7)
    status, reason_refs = _r8_status_from_r7(r7)
    ready = status == "READY_FOR_RATING_ROW_NORMALIZATION"
    execution_blocker_ids = dedupe_identifiers(r7.get("execution_blocker_ids"), limit=20, max_length=120)
    normalizer = {
        "schema_version": P7_R50_RATING_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R50_STEP,
        "scope": P7_R50_SCOPE,
        "policy_kind": P7_R50_POLICY_KIND,
        "policy_section": "R50-8_rating_row_normalizer",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r50_rating_row_normalizer_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r7.get("review_session_id"), default=P7_R50_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_session_status": "READY_FOR_LOCAL_BODY_FULL_PACKET_GENERATION" if ready else "BLOCKED",
        "r7_reviewer_instruction_rating_form_schema_version": P7_R50_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION,
        "r7_reviewer_instruction_rating_form_ref": clean_identifier(r7.get("material_id"), default="p7_r50_reviewer_instruction_rating_form_freeze", max_length=180),
        "instruction_form_status": r7.get("instruction_form_status"),
        "normalizer_status": status,
        "normalizer_reason_refs": reason_refs,
        "required_case_count": P7_R50_REQUIRED_CASE_COUNT,
        "rating_row_schema_version": P7_R50_RATING_CAPTURE_ROW_BODYFREE_SCHEMA_VERSION,
        "r48_rating_row_schema_version_ref": P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION,
        "rating_row_required_field_refs": list(P7_R50_RATING_CAPTURE_ROW_BODYFREE_REQUIRED_FIELD_REFS),
        "rating_axis_refs": list(P5_HUMAN_BLIND_QA_RATING_AXES),
        "rating_axis_target_refs": dict(P5_HUMAN_BLIND_QA_TARGETS),
        "rating_score_min": 0.0,
        "rating_score_max": 1.0,
        "missing_axis_scores_pass_allowed": False,
        "extra_rating_axis_allowed": False,
        "machine_auto_score_allowed": False,
        "readfeel_auto_estimation_allowed": False,
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
        "normalizer_ready": ready,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "local_only_body_full_generation_allowed": bool(ready and r7.get("local_only_body_full_generation_allowed") is True),
        "manual_run_decision_made_here": True,
        "r8_rating_row_normalizer_built": True,
        "execution_blocker_ids": execution_blocker_ids,
        "open_execution_blocker_ids": dedupe_identifiers(r7.get("open_execution_blocker_ids"), limit=20, max_length=120),
        "implemented_steps": list(P7_R50_R8_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R50_R8_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r49_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_prior_validation_evidence_adopted": True,
        "r3_manual_run_decision_built": True,
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built": True,
        "r5_24_case_review_session_protocol_built": True,
        "r6_local_only_body_full_packet_generation_request_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": True,
        "first_next_work_ref": P7_R50_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R50_R8_NEXT_REQUIRED_STEP_REF if ready else P7_R50_R8_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r50_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_for(P7_R50_R8_FALSE_KEY_REFS),
    }
    assert_p7_r50_rating_row_normalizer_bodyfree_contract(normalizer)
    return normalizer


def build_p7_r50_rating_row_normalizer(**kwargs: Any) -> dict[str, Any]:
    """Compatibility alias for the R50-8 builder named in the design."""

    return build_p7_r50_rating_row_normalizer_bodyfree(**kwargs)


def assert_p7_r50_rating_row_normalizer_bodyfree_contract(normalizer: Mapping[str, Any]) -> bool:
    data = safe_mapping(normalizer)
    _assert_required_fields(data, required=P7_R50_RATING_ROW_NORMALIZER_BODYFREE_REQUIRED_FIELD_REFS, source="p7_r50_r8_rating_row_normalizer")
    _assert_common_with_false_keys(
        data,
        schema_version=P7_R50_RATING_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION,
        source="p7_r50_r8_rating_row_normalizer",
        false_keys=P7_R50_R8_FALSE_KEY_REFS,
    )
    if data.get("policy_section") != "R50-8_rating_row_normalizer":
        raise ValueError("R50 R8 policy section changed")
    if data.get("normalizer_status") not in P7_R50_RATING_ROW_NORMALIZER_STATUS_REFS:
        raise ValueError("R50 R8 normalizer status changed")
    if data.get("rating_row_schema_version") != P7_R50_RATING_CAPTURE_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R50 R8 rating row schema version changed")
    if data.get("r48_rating_row_schema_version_ref") != P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R50 R8 must preserve R48-compatible rating row reference")
    if tuple(data.get("rating_row_required_field_refs") or ()) != P7_R50_RATING_CAPTURE_ROW_BODYFREE_REQUIRED_FIELD_REFS:
        raise ValueError("R50 R8 rating row fields changed")
    if tuple(data.get("rating_axis_refs") or ()) != P5_HUMAN_BLIND_QA_RATING_AXES:
        raise ValueError("R50 R8 axis refs changed")
    if safe_mapping(data.get("rating_axis_target_refs")) != dict(P5_HUMAN_BLIND_QA_TARGETS):
        raise ValueError("R50 R8 axis targets changed")
    if data.get("rating_score_min") != 0.0 or data.get("rating_score_max") != 1.0:
        raise ValueError("R50 R8 rating score range changed")
    if tuple(data.get("allowed_verdict_refs") or ()) != P7_R50_RATING_VERDICT_REFS:
        raise ValueError("R50 R8 verdict refs changed")
    if tuple(data.get("readfeel_blocker_id_refs") or ()) != P7_R48_READFEEL_BLOCKER_ID_REFS:
        raise ValueError("R50 R8 readfeel blocker ids changed")
    for true_key in (
        "sanitized_reason_ids_only",
        "blocker_ids_only",
        "blocked_or_not_reviewable_must_use_execution_blocker_row",
        "red_or_repair_requires_blocker",
        "pass_requires_targets_and_no_blockers",
        "body_removed_may_be_false_before_disposal",
        "rating_rows_are_bodyfree",
        "manual_run_decision_made_here",
        "r8_rating_row_normalizer_built",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R50 R8 must keep {true_key}=True")
    for false_key in (
        "missing_axis_scores_pass_allowed",
        "extra_rating_axis_allowed",
        "machine_auto_score_allowed",
        "readfeel_auto_estimation_allowed",
        "machine_metrics_used_for_readfeel_allowed",
        "reviewer_free_text_bodyfree_allowed",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R50 R8 must keep {false_key}=False")
    if data.get("normalizer_status") == "READY_FOR_RATING_ROW_NORMALIZATION":
        if data.get("normalizer_ready") is not True:
            raise ValueError("R50 R8 ready status must set normalizer_ready=True")
        if data.get("local_only_body_full_generation_allowed") is not True:
            raise ValueError("R50 R8 ready status must preserve local-only generation permission")
        if data.get("execution_blocker_ids") or data.get("open_execution_blocker_ids"):
            raise ValueError("R50 R8 ready status must not carry execution blockers")
        if data.get("next_required_step") != P7_R50_R8_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R8 ready status must point to R50-9")
    else:
        if data.get("normalizer_ready") is not False:
            raise ValueError("R50 R8 blocked status must set normalizer_ready=False")
        if data.get("local_only_body_full_generation_allowed") is not False:
            raise ValueError("R50 R8 blocked status must not preserve generation permission")
        if data.get("next_required_step") != P7_R50_R8_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R8 blocked status must point to R50-7 resolution")
    unknown_blockers = sorted(set(data.get("execution_blocker_ids") or ()) - set(P7_R50_EXECUTION_BLOCKER_ID_REFS))
    if unknown_blockers:
        raise ValueError(f"R50 R8 execution blocker ids are not canonical: {unknown_blockers[:4]}")
    if tuple(data.get("implemented_steps") or ()) != P7_R50_R8_IMPLEMENTED_STEPS:
        raise ValueError("R50 R8 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_R8_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R8 not-yet steps changed")
    return True


def _r9_status_from_r8(r8: Mapping[str, Any]) -> tuple[str, list[str]]:
    if r8.get("normalizer_status") != "READY_FOR_RATING_ROW_NORMALIZATION":
        return "BLOCKED_BY_R50_8_RATING_ROW_NORMALIZER", ["r8_rating_row_normalizer_not_ready"]
    return "READY_FOR_READFEEL_AND_EXECUTION_BLOCKER_INGESTION", ["r8_rating_row_normalizer_ready"]


def build_p7_r50_readfeel_blocker_execution_blocker_ingestion_bodyfree(
    *,
    rating_row_normalizer_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r50_readfeel_blocker_execution_blocker_ingestion_bodyfree",
) -> dict[str, Any]:
    """Build R50-9 blocker ingestion policy without materializing review rows."""

    r8 = safe_mapping(rating_row_normalizer_bodyfree) if rating_row_normalizer_bodyfree is not None else build_p7_r50_rating_row_normalizer_bodyfree()
    assert_p7_r50_rating_row_normalizer_bodyfree_contract(r8)
    status, reason_refs = _r9_status_from_r8(r8)
    ready = status == "READY_FOR_READFEEL_AND_EXECUTION_BLOCKER_INGESTION"
    execution_blocker_ids = dedupe_identifiers(r8.get("execution_blocker_ids"), limit=20, max_length=120)
    ingestion = {
        "schema_version": P7_R50_READFEEL_EXECUTION_BLOCKER_INGESTION_BODYFREE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R50_STEP,
        "scope": P7_R50_SCOPE,
        "policy_kind": P7_R50_POLICY_KIND,
        "policy_section": "R50-9_readfeel_blocker_execution_blocker_ingestion",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r50_readfeel_blocker_execution_blocker_ingestion_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r8.get("review_session_id"), default=P7_R50_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_session_status": "READY_FOR_LOCAL_BODY_FULL_PACKET_GENERATION" if ready else "BLOCKED",
        "r8_rating_row_normalizer_schema_version": P7_R50_RATING_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION,
        "r8_rating_row_normalizer_ref": clean_identifier(r8.get("material_id"), default="p7_r50_rating_row_normalizer_bodyfree", max_length=180),
        "normalizer_status": r8.get("normalizer_status"),
        "blocker_ingestion_status": status,
        "blocker_ingestion_reason_refs": reason_refs,
        "required_case_count": P7_R50_REQUIRED_CASE_COUNT,
        "readfeel_blocker_row_schema_version": P7_R50_READFEEL_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "r48_blocker_row_schema_version_ref": P7_R48_P5_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "execution_blocker_row_schema_version": P7_R50_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "r48_execution_blocker_row_schema_version_ref": P7_R48_P5_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "readfeel_blocker_row_required_field_refs": list(P7_R50_READFEEL_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS),
        "execution_blocker_row_required_field_refs": list(P7_R50_EXECUTION_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS),
        "readfeel_blocker_id_refs": list(P7_R48_READFEEL_BLOCKER_ID_REFS),
        "execution_blocker_id_refs": list(P7_R50_EXECUTION_BLOCKER_ID_REFS),
        "readfeel_blocker_kind_refs": list(P7_R48_P5_BLOCKER_KINDS),
        "readfeel_blocker_status_refs": list(P7_R48_P5_BLOCKER_STATUSES),
        "execution_blocker_kind_refs": list(P7_R50_EXECUTION_BLOCKER_KIND_REFS),
        "execution_blocker_status_refs": list(P7_R50_EXECUTION_BLOCKER_STATUS_REFS),
        "readfeel_and_execution_blockers_separated": True,
        "execution_blockers_do_not_assign_readfeel_verdict": True,
        "execution_blocker_cases_do_not_create_rating_rows": True,
        "rating_missing_maps_to_execution_blocker_not_red": True,
        "local_root_missing_maps_to_execution_blocker_not_red": True,
        "disposal_failed_maps_to_execution_blocker_not_red": True,
        "body_free_leak_maps_to_execution_blocker_not_red": True,
        "readfeel_blocker_row_builder_ready": ready,
        "execution_blocker_row_builder_ready": ready,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "local_only_body_full_generation_allowed": bool(ready and r8.get("local_only_body_full_generation_allowed") is True),
        "manual_run_decision_made_here": True,
        "r9_readfeel_blocker_execution_blocker_ingestion_built": True,
        "execution_blocker_ids": execution_blocker_ids,
        "open_execution_blocker_ids": dedupe_identifiers(r8.get("open_execution_blocker_ids"), limit=20, max_length=120),
        "implemented_steps": list(P7_R50_R9_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R50_R9_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r49_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_prior_validation_evidence_adopted": True,
        "r3_manual_run_decision_built": True,
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built": True,
        "r5_24_case_review_session_protocol_built": True,
        "r6_local_only_body_full_packet_generation_request_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": True,
        "r8_rating_row_normalizer_built": True,
        "first_next_work_ref": P7_R50_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R50_R9_NEXT_REQUIRED_STEP_REF if ready else P7_R50_R9_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r50_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_for(P7_R50_R9_FALSE_KEY_REFS),
    }
    assert_p7_r50_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(ingestion)
    return ingestion


def build_p7_r50_readfeel_blocker_execution_blocker_ingestion(**kwargs: Any) -> dict[str, Any]:
    """Compatibility alias for the R50-9 builder named in the design."""

    return build_p7_r50_readfeel_blocker_execution_blocker_ingestion_bodyfree(**kwargs)


def assert_p7_r50_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(ingestion: Mapping[str, Any]) -> bool:
    data = safe_mapping(ingestion)
    _assert_required_fields(data, required=P7_R50_READFEEL_EXECUTION_BLOCKER_INGESTION_BODYFREE_REQUIRED_FIELD_REFS, source="p7_r50_r9_readfeel_execution_blocker_ingestion")
    _assert_common_with_false_keys(
        data,
        schema_version=P7_R50_READFEEL_EXECUTION_BLOCKER_INGESTION_BODYFREE_SCHEMA_VERSION,
        source="p7_r50_r9_readfeel_execution_blocker_ingestion",
        false_keys=P7_R50_R9_FALSE_KEY_REFS,
    )
    if data.get("policy_section") != "R50-9_readfeel_blocker_execution_blocker_ingestion":
        raise ValueError("R50 R9 policy section changed")
    if data.get("blocker_ingestion_status") not in P7_R50_BLOCKER_INGESTION_STATUS_REFS:
        raise ValueError("R50 R9 blocker ingestion status changed")
    if data.get("readfeel_blocker_row_schema_version") != P7_R50_READFEEL_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R50 R9 readfeel blocker row schema changed")
    if data.get("execution_blocker_row_schema_version") != P7_R50_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R50 R9 execution blocker row schema changed")
    if tuple(data.get("readfeel_blocker_row_required_field_refs") or ()) != P7_R50_READFEEL_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS:
        raise ValueError("R50 R9 readfeel blocker row fields changed")
    if tuple(data.get("execution_blocker_row_required_field_refs") or ()) != P7_R50_EXECUTION_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS:
        raise ValueError("R50 R9 execution blocker row fields changed")
    if tuple(data.get("readfeel_blocker_id_refs") or ()) != P7_R48_READFEEL_BLOCKER_ID_REFS:
        raise ValueError("R50 R9 readfeel blocker ids changed")
    if tuple(data.get("execution_blocker_id_refs") or ()) != P7_R50_EXECUTION_BLOCKER_ID_REFS:
        raise ValueError("R50 R9 execution blocker ids changed")
    if tuple(data.get("execution_blocker_kind_refs") or ()) != P7_R50_EXECUTION_BLOCKER_KIND_REFS:
        raise ValueError("R50 R9 execution blocker kinds changed")
    if tuple(data.get("execution_blocker_status_refs") or ()) != P7_R50_EXECUTION_BLOCKER_STATUS_REFS:
        raise ValueError("R50 R9 execution blocker statuses changed")
    for true_key in (
        "readfeel_and_execution_blockers_separated",
        "execution_blockers_do_not_assign_readfeel_verdict",
        "execution_blocker_cases_do_not_create_rating_rows",
        "rating_missing_maps_to_execution_blocker_not_red",
        "local_root_missing_maps_to_execution_blocker_not_red",
        "disposal_failed_maps_to_execution_blocker_not_red",
        "body_free_leak_maps_to_execution_blocker_not_red",
        "manual_run_decision_made_here",
        "r9_readfeel_blocker_execution_blocker_ingestion_built",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R50 R9 must keep {true_key}=True")
    for false_key in (
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R50 R9 must keep {false_key}=False")
    if data.get("blocker_ingestion_status") == "READY_FOR_READFEEL_AND_EXECUTION_BLOCKER_INGESTION":
        if data.get("readfeel_blocker_row_builder_ready") is not True or data.get("execution_blocker_row_builder_ready") is not True:
            raise ValueError("R50 R9 ready status must enable row builders")
        if data.get("local_only_body_full_generation_allowed") is not True:
            raise ValueError("R50 R9 ready status must preserve local-only generation permission")
        if data.get("execution_blocker_ids") or data.get("open_execution_blocker_ids"):
            raise ValueError("R50 R9 ready status must not carry execution blockers")
        if data.get("next_required_step") != P7_R50_R9_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R9 ready status must point to R50-10")
    else:
        if data.get("readfeel_blocker_row_builder_ready") is not False or data.get("execution_blocker_row_builder_ready") is not False:
            raise ValueError("R50 R9 blocked status must disable row builders")
        if data.get("local_only_body_full_generation_allowed") is not False:
            raise ValueError("R50 R9 blocked status must not preserve generation permission")
        if data.get("next_required_step") != P7_R50_R9_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R9 blocked status must point to R50-8 resolution")
    unknown_blockers = sorted(set(data.get("execution_blocker_ids") or ()) - set(P7_R50_EXECUTION_BLOCKER_ID_REFS))
    if unknown_blockers:
        raise ValueError(f"R50 R9 execution blocker ids are not canonical: {unknown_blockers[:4]}")
    if tuple(data.get("implemented_steps") or ()) != P7_R50_R9_IMPLEMENTED_STEPS:
        raise ValueError("R50 R9 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_R9_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R9 not-yet steps changed")
    return True


def build_p7_r50_r8_r9_rating_blocker_ingestion_freeze(
    *,
    reviewer_instruction_rating_form_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r50_r8_r9_rating_blocker_ingestion_freeze",
) -> dict[str, Any]:
    """Build a compact combined R50-8/R50-9 body-free freeze."""

    r8 = build_p7_r50_rating_row_normalizer_bodyfree(
        reviewer_instruction_rating_form_freeze=reviewer_instruction_rating_form_freeze
    )
    r9 = build_p7_r50_readfeel_blocker_execution_blocker_ingestion_bodyfree(
        rating_row_normalizer_bodyfree=r8
    )
    combined = {
        "schema_version": P7_R50_R8_R9_RATING_BLOCKER_INGESTION_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R50_STEP,
        "scope": P7_R50_SCOPE,
        "policy_kind": P7_R50_POLICY_KIND,
        "policy_section": "R50-8_R50-9_rating_blocker_ingestion_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r50_r8_r9_rating_blocker_ingestion_freeze", max_length=180),
        "r8_rating_row_normalizer": r8,
        "r9_readfeel_blocker_execution_blocker_ingestion": r9,
        "review_session_id": r9["review_session_id"],
        "normalizer_status": r8["normalizer_status"],
        "blocker_ingestion_status": r9["blocker_ingestion_status"],
        "local_only_body_full_generation_allowed": r9["local_only_body_full_generation_allowed"],
        "manual_run_decision_made_here": True,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "implemented_steps": list(P7_R50_R9_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R50_R9_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r49_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_prior_validation_evidence_adopted": True,
        "r3_manual_run_decision_built": True,
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built": True,
        "r5_24_case_review_session_protocol_built": True,
        "r6_local_only_body_full_packet_generation_request_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": True,
        "r8_rating_row_normalizer_built": True,
        "r9_readfeel_blocker_execution_blocker_ingestion_built": True,
        "first_next_work_ref": P7_R50_FIRST_NEXT_WORK_REF,
        "next_required_step": r9["next_required_step"],
        "public_contract": public_contract_flags(),
        "r50_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_for(P7_R50_R9_FALSE_KEY_REFS),
    }
    assert_p7_r50_r8_r9_rating_blocker_ingestion_freeze_contract(combined)
    return combined


def assert_p7_r50_r8_r9_rating_blocker_ingestion_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_required_fields(
        data,
        required=P7_R50_R8_R9_RATING_BLOCKER_INGESTION_FREEZE_REQUIRED_FIELD_REFS,
        source="p7_r50_r8_r9_rating_blocker_ingestion_freeze",
    )
    _assert_common_with_false_keys(
        data,
        schema_version=P7_R50_R8_R9_RATING_BLOCKER_INGESTION_FREEZE_SCHEMA_VERSION,
        source="p7_r50_r8_r9_rating_blocker_ingestion_freeze",
        false_keys=P7_R50_R9_FALSE_KEY_REFS,
    )
    if data.get("policy_section") != "R50-8_R50-9_rating_blocker_ingestion_freeze":
        raise ValueError("R50 R8/R9 policy section changed")
    r8 = safe_mapping(data.get("r8_rating_row_normalizer"))
    r9 = safe_mapping(data.get("r9_readfeel_blocker_execution_blocker_ingestion"))
    assert_p7_r50_rating_row_normalizer_bodyfree_contract(r8)
    assert_p7_r50_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(r9)
    if data.get("normalizer_status") != r8.get("normalizer_status"):
        raise ValueError("R50 R8/R9 normalizer status does not match nested R8")
    if data.get("blocker_ingestion_status") != r9.get("blocker_ingestion_status"):
        raise ValueError("R50 R8/R9 ingestion status does not match nested R9")
    if data.get("local_only_body_full_generation_allowed") is not r9.get("local_only_body_full_generation_allowed"):
        raise ValueError("R50 R8/R9 local-only permission mismatch")
    if tuple(data.get("implemented_steps") or ()) != P7_R50_R9_IMPLEMENTED_STEPS:
        raise ValueError("R50 R8/R9 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_R9_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R8/R9 not-yet steps changed")
    for false_key in (
        "actual_manual_review_run_here",
        "body_full_packet_generated_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R50 R8/R9 must keep {false_key}=False")
    return True




def build_p7_r50_question_need_observation_row_normalizer_bodyfree(
    *,
    readfeel_blocker_execution_blocker_ingestion_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r50_question_need_observation_row_normalizer_bodyfree",
) -> dict[str, Any]:
    """Build R50-10 question-need row normalizer policy without running review."""

    r9 = safe_mapping(readfeel_blocker_execution_blocker_ingestion_bodyfree) if readfeel_blocker_execution_blocker_ingestion_bodyfree is not None else build_p7_r50_readfeel_blocker_execution_blocker_ingestion_bodyfree()
    assert_p7_r50_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(r9)
    status, reason_refs = _r10_status_from_r9(r9)
    ready = status == "READY_FOR_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION"
    execution_blocker_ids = dedupe_identifiers(r9.get("execution_blocker_ids"), limit=20, max_length=120)
    normalizer = {
        "schema_version": P7_R50_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R50_STEP,
        "scope": P7_R50_SCOPE,
        "policy_kind": P7_R50_POLICY_KIND,
        "policy_section": "R50-10_question_need_observation_row_normalizer",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r50_question_need_observation_row_normalizer_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r9.get("review_session_id"), default=P7_R50_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_session_status": "READY_FOR_LOCAL_BODY_FULL_PACKET_GENERATION" if ready else "BLOCKED",
        "r9_blocker_ingestion_schema_version": P7_R50_READFEEL_EXECUTION_BLOCKER_INGESTION_BODYFREE_SCHEMA_VERSION,
        "r9_blocker_ingestion_ref": clean_identifier(r9.get("material_id"), default="p7_r50_readfeel_blocker_execution_blocker_ingestion_bodyfree", max_length=180),
        "blocker_ingestion_status": r9.get("blocker_ingestion_status"),
        "question_observation_normalizer_status": status,
        "question_observation_normalizer_reason_refs": reason_refs,
        "required_case_count": P7_R50_REQUIRED_CASE_COUNT,
        "question_need_observation_row_schema_version": P7_R50_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION,
        "r49_question_need_observation_row_schema_version_ref": P7_R49_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION,
        "question_need_observation_row_required_field_refs": list(P7_R50_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_REQUIRED_FIELD_REFS),
        "question_need_observation_row_forbidden_field_refs": list(P7_R50_BODY_FREE_FORBIDDEN_FIELD_REFS),
        "question_need_primary_class_refs": list(P7_R50_QUESTION_NEED_PRIMARY_CLASS_REFS),
        "ambiguity_kind_refs": list(P7_R50_AMBIGUITY_KIND_REFS),
        "one_question_fit_refs": list(P7_R50_ONE_QUESTION_FIT_REFS),
        "plan_candidate_flag_refs": list(P7_R50_PLAN_CANDIDATE_FLAG_REFS),
        "repair_required_ref_refs": list(P7_R50_REPAIR_REQUIRED_REF_REFS),
        "question_need_observation_stage_ref": P7_R50_QUESTION_NEED_OBSERVATION_STAGE_REF,
        "review_kind": P7_R50_REVIEW_KIND,
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
        "normalizer_ready": ready,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_question_need_observation_summary_materialized_here": False,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "local_only_body_full_generation_allowed": bool(ready and r9.get("local_only_body_full_generation_allowed") is True),
        "manual_run_decision_made_here": True,
        "r10_question_need_observation_row_normalizer_built": True,
        "execution_blocker_ids": execution_blocker_ids,
        "open_execution_blocker_ids": dedupe_identifiers(r9.get("open_execution_blocker_ids"), limit=20, max_length=120),
        "implemented_steps": list(P7_R50_R10_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R50_R10_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r49_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_prior_validation_evidence_adopted": True,
        "r3_manual_run_decision_built": True,
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built": True,
        "r5_24_case_review_session_protocol_built": True,
        "r6_local_only_body_full_packet_generation_request_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": True,
        "r8_rating_row_normalizer_built": True,
        "r9_readfeel_blocker_execution_blocker_ingestion_built": True,
        "first_next_work_ref": P7_R50_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R50_R10_NEXT_REQUIRED_STEP_REF if ready else P7_R50_R10_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r50_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_for(P7_R50_R10_FALSE_KEY_REFS),
    }
    assert_p7_r50_question_need_observation_row_normalizer_bodyfree_contract(normalizer)
    return normalizer


def build_p7_r50_question_need_observation_row_normalizer(
    *,
    readfeel_blocker_execution_blocker_ingestion_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r50_question_need_observation_row_normalizer_bodyfree",
) -> dict[str, Any]:
    return build_p7_r50_question_need_observation_row_normalizer_bodyfree(
        readfeel_blocker_execution_blocker_ingestion_bodyfree=readfeel_blocker_execution_blocker_ingestion_bodyfree,
        material_id=material_id,
    )


def assert_p7_r50_question_need_observation_row_normalizer_bodyfree_contract(normalizer: Mapping[str, Any]) -> bool:
    data = safe_mapping(normalizer)
    _assert_required_fields(
        data,
        required=P7_R50_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_BODYFREE_REQUIRED_FIELD_REFS,
        source="p7_r50_r10_question_need_observation_row_normalizer",
    )
    _assert_common_with_false_keys(
        data,
        schema_version=P7_R50_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION,
        source="p7_r50_r10_question_need_observation_row_normalizer",
        false_keys=P7_R50_R10_FALSE_KEY_REFS,
    )
    if data.get("policy_section") != "R50-10_question_need_observation_row_normalizer":
        raise ValueError("R50 R10 policy section changed")
    if data.get("r9_blocker_ingestion_schema_version") != P7_R50_READFEEL_EXECUTION_BLOCKER_INGESTION_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R50 R10 R9 blocker ingestion schema changed")
    if data.get("question_need_observation_row_schema_version") != P7_R50_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R50 R10 question row schema changed")
    if data.get("r49_question_need_observation_row_schema_version_ref") != P7_R49_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R50 R10 R49 question row schema ref changed")
    if tuple(data.get("question_need_observation_row_required_field_refs") or ()) != P7_R50_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_REQUIRED_FIELD_REFS:
        raise ValueError("R50 R10 question row required fields changed")
    for ref_name, expected in (
        ("question_need_primary_class_refs", P7_R50_QUESTION_NEED_PRIMARY_CLASS_REFS),
        ("ambiguity_kind_refs", P7_R50_AMBIGUITY_KIND_REFS),
        ("one_question_fit_refs", P7_R50_ONE_QUESTION_FIT_REFS),
        ("plan_candidate_flag_refs", P7_R50_PLAN_CANDIDATE_FLAG_REFS),
        ("repair_required_ref_refs", P7_R50_REPAIR_REQUIRED_REF_REFS),
    ):
        if tuple(data.get(ref_name) or ()) != expected:
            raise ValueError(f"R50 R10 {ref_name} changed")
    for true_key in (
        "question_need_observation_rows_must_be_bodyfree",
        "manual_run_decision_made_here",
        "r10_question_need_observation_row_normalizer_built",
        "r0_current_source_r49_handoff_bridge_refrozen",
        "r1_scope_schema_status_enum_fixed",
        "r2_prior_validation_evidence_adopted",
        "r3_manual_run_decision_built",
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
        "r5_24_case_review_session_protocol_built",
        "r6_local_only_body_full_packet_generation_request_built",
        "r7_reviewer_instruction_rating_form_freeze_built",
        "r8_rating_row_normalizer_built",
        "r9_readfeel_blocker_execution_blocker_ingestion_built",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R50 R10 must keep {true_key}=True")
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
        "actual_question_need_observation_rows_materialized_here",
        "actual_question_need_observation_summary_materialized_here",
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R50 R10 must keep {false_key}=False")
    if data.get("question_observation_normalizer_status") == "READY_FOR_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION":
        if data.get("normalizer_ready") is not True or data.get("local_only_body_full_generation_allowed") is not True:
            raise ValueError("R50 R10 ready status must preserve local-only permission")
        if data.get("execution_blocker_ids") or data.get("open_execution_blocker_ids"):
            raise ValueError("R50 R10 ready status must not carry execution blockers")
        if data.get("next_required_step") != P7_R50_R10_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R10 ready status must point to R50-11")
    else:
        if data.get("normalizer_ready") is not False or data.get("local_only_body_full_generation_allowed") is not False:
            raise ValueError("R50 R10 blocked status must not preserve generation permission")
        if data.get("next_required_step") != P7_R50_R10_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R10 blocked status must point to R50-9 resolution")
    if tuple(data.get("implemented_steps") or ()) != P7_R50_R10_IMPLEMENTED_STEPS:
        raise ValueError("R50 R10 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_R10_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R10 not-yet steps changed")
    return True


def _ids_match_between_rating_and_question_r50(rating_row: Mapping[str, Any], question_row: Mapping[str, Any]) -> bool:
    for key in ("review_session_id", "packet_ref_id", "blind_case_id", "case_ref_id", "family", "case_role"):
        if safe_mapping(rating_row).get(key) != safe_mapping(question_row).get(key):
            return False
    return True


def assert_p7_r50_rating_vs_question_observation_consistency(
    *,
    rating_row: Mapping[str, Any] | None = None,
    question_need_observation_row: Mapping[str, Any],
    execution_blocker_rows: Sequence[Mapping[str, Any]] | None = None,
) -> bool:
    """Validate that question-need observations do not hide P5 readfeel repair needs."""

    qrow = safe_mapping(question_need_observation_row)
    assert_p7_r50_question_need_observation_row_bodyfree_contract(qrow)
    primary = clean_identifier(qrow.get("question_need_primary_class"), default="", max_length=160)
    if primary == "insufficient_material_execution_blocker":
        _validate_question_observation_semantics_r50(
            qrow,
            execution_blocker_rows=execution_blocker_rows or [],
            require_execution_blocker_match=True,
        )
        if rating_row is not None:
            raise ValueError("R50 R11 insufficient-material execution blockers must not also carry a readfeel rating row")
        return True
    if rating_row is None:
        raise ValueError("R50 R11 consistency guard requires a rating row unless the case is execution-blocked")
    rrow = safe_mapping(rating_row)
    assert_p7_r50_rating_capture_row_bodyfree_contract(rrow)
    if not _ids_match_between_rating_and_question_r50(rrow, qrow):
        raise ValueError("R50 R11 rating row and question observation row must refer to the same body-free case ids")
    verdict = clean_identifier(rrow.get("verdict"), default="", max_length=80)
    blocker_ids = tuple(rrow.get("blocker_ids") or ())
    plan_flags = tuple(qrow.get("plan_candidate_flags") or ())
    repair_primary_classes = {
        "not_question_emlis_readfeel_repair_required",
        "not_question_p5_surface_repair_required",
        "not_question_gate_boundary_required",
    }
    question_candidate_primary_classes = {
        "question_may_reduce_overread_risk",
        "plus_single_question_candidate_later",
        "premium_deep_dive_candidate_later",
    }
    if verdict == "PASS" and primary in repair_primary_classes:
        raise ValueError("R50 R11 PASS rating must not carry a not-question repair-required primary class")
    if verdict == "PASS" and primary == "insufficient_material_execution_blocker":
        raise ValueError("R50 R11 PASS rating must not carry execution-blocked question observation")
    if verdict in {"RED", "REPAIR_REQUIRED"} and primary in question_candidate_primary_classes | {"no_question_needed_emlis_can_observe", "question_would_make_immediate_observation_heavy"}:
        raise ValueError("R50 R11 RED/REPAIR_REQUIRED rating must not be explained only as a question candidate")
    if verdict in {"RED", "REPAIR_REQUIRED"} and not blocker_ids:
        raise ValueError("R50 R11 RED/REPAIR_REQUIRED rating requires readfeel blocker ids")
    if qrow.get("one_question_fit_ref") == "repair_required_not_question" and set(qrow.get("repair_required_refs") or ()) <= {"no_repair_required"}:
        raise ValueError("R50 R11 repair_required_not_question requires a non-empty repair ref")
    if primary in question_candidate_primary_classes and blocker_ids:
        raise ValueError("R50 R11 question candidate must not clear or coexist as the only explanation for readfeel blockers")
    high_risk_readfeel_blockers = {
        "p5_history_creepy_or_surveillance_feeling",
        "p5_current_input_overridden_by_history",
        "p5_history_scope_overclaim",
        "p5_low_information_history_overread",
        "p5_free_tier_history_boundary_violation",
        "p5_history_line_self_blame_amplification",
    }
    if set(blocker_ids) & high_risk_readfeel_blockers and "p8_design_material_candidate" in plan_flags:
        raise ValueError("R50 R11 high-risk P5 readfeel blockers must not be moved into P8 material candidates")
    _validate_question_observation_semantics_r50(qrow)
    return True


def _r11_status_from_r10(r10: Mapping[str, Any]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if r10.get("question_observation_normalizer_status") != "READY_FOR_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION":
        reasons.append("question_observation_normalizer_not_ready")
    if r10.get("local_only_body_full_generation_allowed") is not True:
        reasons.append("local_only_generation_permission_not_preserved")
    if r10.get("open_execution_blocker_ids"):
        reasons.append("open_execution_blockers_present")
    if reasons:
        return "BLOCKED_BY_R50_10_QUESTION_OBSERVATION_NORMALIZER", dedupe_identifiers(reasons, limit=10, max_length=120)
    return "READY_FOR_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD", []


def build_p7_r50_rating_question_observation_consistency_guard_bodyfree(
    *,
    question_need_observation_row_normalizer_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r50_rating_question_observation_consistency_guard_bodyfree",
) -> dict[str, Any]:
    """Build R50-11 rating/question-observation consistency guard policy."""

    r10 = safe_mapping(question_need_observation_row_normalizer_bodyfree) if question_need_observation_row_normalizer_bodyfree is not None else build_p7_r50_question_need_observation_row_normalizer_bodyfree()
    assert_p7_r50_question_need_observation_row_normalizer_bodyfree_contract(r10)
    status, reason_refs = _r11_status_from_r10(r10)
    ready = status == "READY_FOR_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD"
    execution_blocker_ids = dedupe_identifiers(r10.get("execution_blocker_ids"), limit=20, max_length=120)
    guard = {
        "schema_version": P7_R50_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_BODYFREE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R50_STEP,
        "scope": P7_R50_SCOPE,
        "policy_kind": P7_R50_POLICY_KIND,
        "policy_section": "R50-11_rating_question_observation_consistency_guard",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r50_rating_question_observation_consistency_guard_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r10.get("review_session_id"), default=P7_R50_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_session_status": "READY_FOR_LOCAL_BODY_FULL_PACKET_GENERATION" if ready else "BLOCKED",
        "r10_question_need_observation_row_normalizer_schema_version": P7_R50_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION,
        "r10_question_need_observation_row_normalizer_ref": clean_identifier(r10.get("material_id"), default="p7_r50_question_need_observation_row_normalizer_bodyfree", max_length=180),
        "question_observation_normalizer_status": r10.get("question_observation_normalizer_status"),
        "consistency_guard_status": status,
        "consistency_guard_reason_refs": reason_refs,
        "required_case_count": P7_R50_REQUIRED_CASE_COUNT,
        "rating_row_schema_version": P7_R50_RATING_CAPTURE_ROW_BODYFREE_SCHEMA_VERSION,
        "question_need_observation_row_schema_version": P7_R50_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION,
        "execution_blocker_row_schema_version": P7_R50_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "rating_question_consistency_guard_ready": ready,
        "p5_weakness_must_not_be_hidden_by_questions": True,
        "rating_and_question_observation_ids_must_match": True,
        "pass_rating_forbids_not_question_repair_primary_class": True,
        "repair_or_red_rating_forbids_question_candidate_primary_only": True,
        "repair_required_not_question_requires_repair_ref": True,
        "insufficient_material_requires_execution_blocker_row": True,
        "question_candidate_cannot_clear_readfeel_blocker": True,
        "question_need_observation_required": True,
        "question_need_observation_rows_required_later": True,
        "consistency_guard_function_ref": "assert_p7_r50_rating_vs_question_observation_consistency",
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_question_need_observation_summary_materialized_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "local_only_body_full_generation_allowed": bool(ready and r10.get("local_only_body_full_generation_allowed") is True),
        "manual_run_decision_made_here": True,
        "r11_rating_question_observation_consistency_guard_built": True,
        "execution_blocker_ids": execution_blocker_ids,
        "open_execution_blocker_ids": dedupe_identifiers(r10.get("open_execution_blocker_ids"), limit=20, max_length=120),
        "implemented_steps": list(P7_R50_R11_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R50_R11_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r49_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_prior_validation_evidence_adopted": True,
        "r3_manual_run_decision_built": True,
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built": True,
        "r5_24_case_review_session_protocol_built": True,
        "r6_local_only_body_full_packet_generation_request_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": True,
        "r8_rating_row_normalizer_built": True,
        "r9_readfeel_blocker_execution_blocker_ingestion_built": True,
        "r10_question_need_observation_row_normalizer_built": True,
        "first_next_work_ref": P7_R50_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R50_R11_NEXT_REQUIRED_STEP_REF if ready else P7_R50_R11_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r50_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_for(P7_R50_R11_FALSE_KEY_REFS),
    }
    assert_p7_r50_rating_question_observation_consistency_guard_bodyfree_contract(guard)
    return guard


def build_p7_r50_rating_question_observation_consistency_guard(
    *,
    question_need_observation_row_normalizer_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r50_rating_question_observation_consistency_guard_bodyfree",
) -> dict[str, Any]:
    return build_p7_r50_rating_question_observation_consistency_guard_bodyfree(
        question_need_observation_row_normalizer_bodyfree=question_need_observation_row_normalizer_bodyfree,
        material_id=material_id,
    )


def assert_p7_r50_rating_question_observation_consistency_guard_bodyfree_contract(guard: Mapping[str, Any]) -> bool:
    data = safe_mapping(guard)
    _assert_required_fields(
        data,
        required=P7_R50_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_BODYFREE_REQUIRED_FIELD_REFS,
        source="p7_r50_r11_rating_question_observation_consistency_guard",
    )
    _assert_common_with_false_keys(
        data,
        schema_version=P7_R50_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_BODYFREE_SCHEMA_VERSION,
        source="p7_r50_r11_rating_question_observation_consistency_guard",
        false_keys=P7_R50_R11_FALSE_KEY_REFS,
    )
    if data.get("policy_section") != "R50-11_rating_question_observation_consistency_guard":
        raise ValueError("R50 R11 policy section changed")
    if data.get("r10_question_need_observation_row_normalizer_schema_version") != P7_R50_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R50 R11 R10 question normalizer schema changed")
    if data.get("rating_row_schema_version") != P7_R50_RATING_CAPTURE_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R50 R11 rating row schema changed")
    if data.get("question_need_observation_row_schema_version") != P7_R50_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R50 R11 question row schema changed")
    if data.get("execution_blocker_row_schema_version") != P7_R50_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R50 R11 execution blocker row schema changed")
    for true_key in (
        "p5_weakness_must_not_be_hidden_by_questions",
        "rating_and_question_observation_ids_must_match",
        "pass_rating_forbids_not_question_repair_primary_class",
        "repair_or_red_rating_forbids_question_candidate_primary_only",
        "repair_required_not_question_requires_repair_ref",
        "insufficient_material_requires_execution_blocker_row",
        "question_candidate_cannot_clear_readfeel_blocker",
        "question_need_observation_required",
        "question_need_observation_rows_required_later",
        "manual_run_decision_made_here",
        "r11_rating_question_observation_consistency_guard_built",
        "r0_current_source_r49_handoff_bridge_refrozen",
        "r1_scope_schema_status_enum_fixed",
        "r2_prior_validation_evidence_adopted",
        "r3_manual_run_decision_built",
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
        "r5_24_case_review_session_protocol_built",
        "r6_local_only_body_full_packet_generation_request_built",
        "r7_reviewer_instruction_rating_form_freeze_built",
        "r8_rating_row_normalizer_built",
        "r9_readfeel_blocker_execution_blocker_ingestion_built",
        "r10_question_need_observation_row_normalizer_built",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R50 R11 must keep {true_key}=True")
    for false_key in (
        "actual_question_need_observation_rows_materialized_here",
        "actual_question_need_observation_summary_materialized_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R50 R11 must keep {false_key}=False")
    if data.get("consistency_guard_function_ref") != "assert_p7_r50_rating_vs_question_observation_consistency":
        raise ValueError("R50 R11 consistency guard function ref changed")
    if data.get("consistency_guard_status") == "READY_FOR_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD":
        if data.get("rating_question_consistency_guard_ready") is not True or data.get("local_only_body_full_generation_allowed") is not True:
            raise ValueError("R50 R11 ready status must preserve local-only permission")
        if data.get("execution_blocker_ids") or data.get("open_execution_blocker_ids"):
            raise ValueError("R50 R11 ready status must not carry execution blockers")
        if data.get("next_required_step") != P7_R50_R11_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R11 ready status must point to R50-12")
    else:
        if data.get("rating_question_consistency_guard_ready") is not False or data.get("local_only_body_full_generation_allowed") is not False:
            raise ValueError("R50 R11 blocked status must not preserve generation permission")
        if data.get("next_required_step") != P7_R50_R11_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R11 blocked status must point to R50-10 resolution")
    if tuple(data.get("implemented_steps") or ()) != P7_R50_R11_IMPLEMENTED_STEPS:
        raise ValueError("R50 R11 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_R11_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R11 not-yet steps changed")
    return True


def build_p7_r50_r10_r11_question_normalizer_consistency_guard_freeze(
    *,
    readfeel_blocker_execution_blocker_ingestion_bodyfree: Mapping[str, Any] | None = None,
    question_need_observation_row_normalizer_bodyfree: Mapping[str, Any] | None = None,
    rating_question_observation_consistency_guard_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r50_r10_r11_question_normalizer_consistency_guard_freeze",
) -> dict[str, Any]:
    r10 = safe_mapping(question_need_observation_row_normalizer_bodyfree) if question_need_observation_row_normalizer_bodyfree is not None else build_p7_r50_question_need_observation_row_normalizer_bodyfree(
        readfeel_blocker_execution_blocker_ingestion_bodyfree=readfeel_blocker_execution_blocker_ingestion_bodyfree
    )
    assert_p7_r50_question_need_observation_row_normalizer_bodyfree_contract(r10)
    r11 = safe_mapping(rating_question_observation_consistency_guard_bodyfree) if rating_question_observation_consistency_guard_bodyfree is not None else build_p7_r50_rating_question_observation_consistency_guard_bodyfree(
        question_need_observation_row_normalizer_bodyfree=r10
    )
    assert_p7_r50_rating_question_observation_consistency_guard_bodyfree_contract(r11)
    freeze = {
        "schema_version": P7_R50_R10_R11_QUESTION_NORMALIZER_CONSISTENCY_GUARD_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R50_STEP,
        "scope": P7_R50_SCOPE,
        "policy_kind": P7_R50_POLICY_KIND,
        "policy_section": "R50-10_R50-11_question_normalizer_consistency_guard_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r50_r10_r11_question_normalizer_consistency_guard_freeze", max_length=180),
        "r10_question_need_observation_row_normalizer": r10,
        "r11_rating_question_observation_consistency_guard": r11,
        "review_session_id": r11["review_session_id"],
        "question_observation_normalizer_status": r10["question_observation_normalizer_status"],
        "consistency_guard_status": r11["consistency_guard_status"],
        "local_only_body_full_generation_allowed": r11["local_only_body_full_generation_allowed"],
        "manual_run_decision_made_here": True,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "implemented_steps": list(P7_R50_R11_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R50_R11_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r49_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_prior_validation_evidence_adopted": True,
        "r3_manual_run_decision_built": True,
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built": True,
        "r5_24_case_review_session_protocol_built": True,
        "r6_local_only_body_full_packet_generation_request_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": True,
        "r8_rating_row_normalizer_built": True,
        "r9_readfeel_blocker_execution_blocker_ingestion_built": True,
        "r10_question_need_observation_row_normalizer_built": True,
        "r11_rating_question_observation_consistency_guard_built": True,
        "first_next_work_ref": P7_R50_FIRST_NEXT_WORK_REF,
        "next_required_step": r11["next_required_step"],
        "public_contract": public_contract_flags(),
        "r50_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_for(P7_R50_R11_FALSE_KEY_REFS),
    }
    assert_p7_r50_r10_r11_question_normalizer_consistency_guard_freeze_contract(freeze)
    return freeze


def assert_p7_r50_r10_r11_question_normalizer_consistency_guard_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_required_fields(
        data,
        required=P7_R50_R10_R11_QUESTION_NORMALIZER_CONSISTENCY_GUARD_FREEZE_REQUIRED_FIELD_REFS,
        source="p7_r50_r10_r11_question_normalizer_consistency_guard_freeze",
    )
    _assert_common_with_false_keys(
        data,
        schema_version=P7_R50_R10_R11_QUESTION_NORMALIZER_CONSISTENCY_GUARD_FREEZE_SCHEMA_VERSION,
        source="p7_r50_r10_r11_question_normalizer_consistency_guard_freeze",
        false_keys=P7_R50_R11_FALSE_KEY_REFS,
    )
    if data.get("policy_section") != "R50-10_R50-11_question_normalizer_consistency_guard_freeze":
        raise ValueError("R50 R10/R11 policy section changed")
    r10 = safe_mapping(data.get("r10_question_need_observation_row_normalizer"))
    r11 = safe_mapping(data.get("r11_rating_question_observation_consistency_guard"))
    assert_p7_r50_question_need_observation_row_normalizer_bodyfree_contract(r10)
    assert_p7_r50_rating_question_observation_consistency_guard_bodyfree_contract(r11)
    if data.get("question_observation_normalizer_status") != r10.get("question_observation_normalizer_status"):
        raise ValueError("R50 R10/R11 question normalizer status mismatch")
    if data.get("consistency_guard_status") != r11.get("consistency_guard_status"):
        raise ValueError("R50 R10/R11 consistency guard status mismatch")
    if data.get("local_only_body_full_generation_allowed") is not r11.get("local_only_body_full_generation_allowed"):
        raise ValueError("R50 R10/R11 local-only permission mismatch")
    if tuple(data.get("implemented_steps") or ()) != P7_R50_R11_IMPLEMENTED_STEPS:
        raise ValueError("R50 R10/R11 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_R11_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R10/R11 not-yet steps changed")
    for false_key in (
        "actual_manual_review_run_here",
        "body_full_packet_generated_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R50 R10/R11 must keep {false_key}=False")
    return True



def _r12_status_from_r11(r11: Mapping[str, Any]) -> tuple[str, list[str], list[str]]:
    execution_blocker_ids = dedupe_identifiers(r11.get("execution_blocker_ids"), limit=20, max_length=120)
    if r11.get("consistency_guard_status") != "READY_FOR_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD":
        return "BLOCKED_BY_R50_11_CONSISTENCY_GUARD", ["r11_consistency_guard_not_ready"], execution_blocker_ids
    return "READY_FOR_PAUSE_ABORT_EXPIRATION_PROTOCOL", ["r11_consistency_guard_ready"], execution_blocker_ids


def build_p7_r50_pause_abort_expiration_protocol_bodyfree(
    *,
    rating_question_observation_consistency_guard_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r50_pause_abort_expiration_protocol_bodyfree",
) -> dict[str, Any]:
    """Build R50-12 pause/abort/expiration protocol without touching local files.

    This helper fixes the body-free rules for paused, aborted, and expired
    manual-review sessions. It does not pause a real session, purge files, or
    create a disposal receipt.
    """

    r11 = safe_mapping(rating_question_observation_consistency_guard_bodyfree) if rating_question_observation_consistency_guard_bodyfree is not None else build_p7_r50_rating_question_observation_consistency_guard_bodyfree()
    assert_p7_r50_rating_question_observation_consistency_guard_bodyfree_contract(r11)
    status, reason_refs, execution_blocker_ids = _r12_status_from_r11(r11)
    ready = status == "READY_FOR_PAUSE_ABORT_EXPIRATION_PROTOCOL"
    protocol = {
        "schema_version": P7_R50_PAUSE_ABORT_EXPIRATION_PROTOCOL_BODYFREE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R50_STEP,
        "scope": P7_R50_SCOPE,
        "policy_kind": P7_R50_POLICY_KIND,
        "policy_section": "R50-12_pause_abort_expiration_protocol",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r50_pause_abort_expiration_protocol_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r11.get("review_session_id"), default=P7_R50_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_session_status": "READY_FOR_LOCAL_BODY_FULL_PACKET_GENERATION" if ready else "BLOCKED",
        "r11_consistency_guard_schema_version": P7_R50_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_BODYFREE_SCHEMA_VERSION,
        "r11_consistency_guard_ref": clean_identifier(r11.get("material_id"), default="p7_r50_rating_question_observation_consistency_guard_bodyfree", max_length=180),
        "consistency_guard_status": r11.get("consistency_guard_status"),
        "pause_abort_expiration_protocol_status": status,
        "protocol_reason_refs": reason_refs,
        "required_case_count": P7_R50_REQUIRED_CASE_COUNT,
        "disposal_status_refs": list(P7_R47_DISPOSAL_STATUSES),
        "body_full_delete_trigger_refs": list(P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS),
        "body_full_packet_retention_max_hours": P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
        "reviewer_notes_retention_after_rating_hours": P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
        "retention_deadline_continues_while_paused": True,
        "pause_does_not_extend_body_full_retention": True,
        "review_paused_allows_later_resume": True,
        "review_paused_keeps_local_only_boundary": True,
        "review_aborted_requires_purge": True,
        "review_aborted_forbids_p5_confirmed_candidate": True,
        "expiration_requires_purge_even_if_rating_incomplete": True,
        "expired_purged_prioritizes_body_removed": True,
        "expired_purged_forbids_p5_confirmed_candidate": True,
        "aborted_or_expired_forbid_p5_confirmed_candidate": True,
        "rating_incomplete_after_expiration_maps_to_execution_blocker_not_readfeel_red": True,
        "paused_status_ref": "REVIEW_PAUSED",
        "aborted_status_ref": "REVIEW_ABORTED",
        "expired_purged_status_ref": "EXPIRED_PURGED",
        "disposal_pending_status_ref": "DISPOSAL_PENDING",
        "disposal_verified_status_ref": "DISPOSAL_VERIFIED",
        "local_packet_export_allowed_during_pause_abort_expiration": False,
        "content_hash_storage_allowed_during_pause_abort_expiration": False,
        "body_free_summary_finalize_allowed_without_disposal_receipt": False,
        "p5_confirmed_candidate_allowed_after_aborted_or_expired": False,
        "actual_pause_abort_run_here": False,
        "actual_expiration_run_here": False,
        "actual_disposal_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "local_only_body_full_generation_allowed": bool(ready and r11.get("local_only_body_full_generation_allowed") is True),
        "manual_run_decision_made_here": True,
        "r12_pause_abort_expiration_protocol_built": True,
        "execution_blocker_ids": execution_blocker_ids,
        "open_execution_blocker_ids": dedupe_identifiers(r11.get("open_execution_blocker_ids"), limit=20, max_length=120),
        "implemented_steps": list(P7_R50_R12_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R50_R12_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r49_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_prior_validation_evidence_adopted": True,
        "r3_manual_run_decision_built": True,
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built": True,
        "r5_24_case_review_session_protocol_built": True,
        "r6_local_only_body_full_packet_generation_request_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": True,
        "r8_rating_row_normalizer_built": True,
        "r9_readfeel_blocker_execution_blocker_ingestion_built": True,
        "r10_question_need_observation_row_normalizer_built": True,
        "r11_rating_question_observation_consistency_guard_built": True,
        "first_next_work_ref": P7_R50_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R50_R12_NEXT_REQUIRED_STEP_REF if ready else P7_R50_R12_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r50_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_for(P7_R50_R12_FALSE_KEY_REFS),
    }
    assert_p7_r50_pause_abort_expiration_protocol_bodyfree_contract(protocol)
    return protocol


def assert_p7_r50_pause_abort_expiration_protocol_bodyfree_contract(protocol: Mapping[str, Any]) -> bool:
    data = safe_mapping(protocol)
    _assert_required_fields(
        data,
        required=P7_R50_PAUSE_ABORT_EXPIRATION_PROTOCOL_BODYFREE_REQUIRED_FIELD_REFS,
        source="p7_r50_r12_pause_abort_expiration_protocol",
    )
    _assert_common_with_false_keys(
        data,
        schema_version=P7_R50_PAUSE_ABORT_EXPIRATION_PROTOCOL_BODYFREE_SCHEMA_VERSION,
        source="p7_r50_r12_pause_abort_expiration_protocol",
        false_keys=P7_R50_R12_FALSE_KEY_REFS,
    )
    if data.get("policy_section") != "R50-12_pause_abort_expiration_protocol":
        raise ValueError("R50 R12 policy section changed")
    if data.get("r11_consistency_guard_schema_version") != P7_R50_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R50 R12 R11 consistency guard schema changed")
    if tuple(data.get("disposal_status_refs") or ()) != P7_R47_DISPOSAL_STATUSES:
        raise ValueError("R50 R12 disposal status refs changed")
    if tuple(data.get("body_full_delete_trigger_refs") or ()) != P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS:
        raise ValueError("R50 R12 body-full delete trigger refs changed")
    if data.get("body_full_packet_retention_max_hours") != P7_R47_BODY_FULL_PACKET_RETENTION_HOURS:
        raise ValueError("R50 R12 body-full retention must inherit R47")
    if data.get("reviewer_notes_retention_after_rating_hours") != P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS:
        raise ValueError("R50 R12 reviewer-note retention must inherit R47")
    for true_key in (
        "retention_deadline_continues_while_paused",
        "pause_does_not_extend_body_full_retention",
        "review_paused_allows_later_resume",
        "review_paused_keeps_local_only_boundary",
        "review_aborted_requires_purge",
        "review_aborted_forbids_p5_confirmed_candidate",
        "expiration_requires_purge_even_if_rating_incomplete",
        "expired_purged_prioritizes_body_removed",
        "expired_purged_forbids_p5_confirmed_candidate",
        "aborted_or_expired_forbid_p5_confirmed_candidate",
        "rating_incomplete_after_expiration_maps_to_execution_blocker_not_readfeel_red",
        "manual_run_decision_made_here",
        "r12_pause_abort_expiration_protocol_built",
        "r0_current_source_r49_handoff_bridge_refrozen",
        "r1_scope_schema_status_enum_fixed",
        "r2_prior_validation_evidence_adopted",
        "r3_manual_run_decision_built",
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
        "r5_24_case_review_session_protocol_built",
        "r6_local_only_body_full_packet_generation_request_built",
        "r7_reviewer_instruction_rating_form_freeze_built",
        "r8_rating_row_normalizer_built",
        "r9_readfeel_blocker_execution_blocker_ingestion_built",
        "r10_question_need_observation_row_normalizer_built",
        "r11_rating_question_observation_consistency_guard_built",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R50 R12 must keep {true_key}=True")
    for false_key in (
        "local_packet_export_allowed_during_pause_abort_expiration",
        "content_hash_storage_allowed_during_pause_abort_expiration",
        "body_free_summary_finalize_allowed_without_disposal_receipt",
        "p5_confirmed_candidate_allowed_after_aborted_or_expired",
        "actual_pause_abort_run_here",
        "actual_expiration_run_here",
        "actual_disposal_run_here",
        "actual_disposal_receipt_materialized_here",
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R50 R12 must keep {false_key}=False")
    if data.get("paused_status_ref") != "REVIEW_PAUSED" or data.get("aborted_status_ref") != "REVIEW_ABORTED":
        raise ValueError("R50 R12 pause/abort status refs changed")
    if data.get("expired_purged_status_ref") != "EXPIRED_PURGED":
        raise ValueError("R50 R12 expired-purged status ref changed")
    if data.get("pause_abort_expiration_protocol_status") == "READY_FOR_PAUSE_ABORT_EXPIRATION_PROTOCOL":
        if data.get("local_only_body_full_generation_allowed") is not True:
            raise ValueError("R50 R12 ready status must preserve local-only permission")
        if data.get("execution_blocker_ids") or data.get("open_execution_blocker_ids"):
            raise ValueError("R50 R12 ready status must not carry execution blockers")
        if data.get("next_required_step") != P7_R50_R12_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R12 ready status must point to R50-13")
    else:
        if data.get("pause_abort_expiration_protocol_status") != "BLOCKED_BY_R50_11_CONSISTENCY_GUARD":
            raise ValueError("R50 R12 protocol status must use the frozen enum")
        if data.get("local_only_body_full_generation_allowed") is not False:
            raise ValueError("R50 R12 blocked status must not preserve local-only permission")
        if data.get("next_required_step") != P7_R50_R12_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R12 blocked status must point to R50-11 resolution")
    if tuple(data.get("implemented_steps") or ()) != P7_R50_R12_IMPLEMENTED_STEPS:
        raise ValueError("R50 R12 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_R12_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R12 not-yet steps changed")
    return True


def build_p7_r50_disposal_receipt_bodyfree(
    *,
    disposal_result: Mapping[str, Any] | None = None,
    review_session_id: Any = P7_R50_DEFAULT_REVIEW_SESSION_ID,
    case_count: int = P7_R50_REQUIRED_CASE_COUNT,
    deleted_file_count: int = 0,
    disposal_status: Any = "NOT_GENERATED",
    body_removed: bool = False,
    reviewer_notes_removed: bool = False,
    purge_started_at: Any = "purge_started_at_unset",
    purge_completed_at: Any = "purge_completed_at_unset",
) -> dict[str, Any]:
    """Build one body-free R50 disposal receipt payload without deleting files."""

    if disposal_result is not None:
        payload = safe_mapping(disposal_result)
        _assert_no_forbidden_body_keys(payload, source="p7_r50_disposal_receipt.disposal_result")
        allowed = set(P7_R50_DISPOSAL_RECEIPT_BODYFREE_REQUIRED_FIELD_REFS)
        unknown = set(payload) - allowed
        if unknown:
            raise ValueError("R50 R13 disposal result contains fields outside the body-free receipt schema")
        review_session_id = payload.get("review_session_id", review_session_id)
        case_count = payload.get("case_count", case_count)
        deleted_file_count = payload.get("deleted_file_count", deleted_file_count)
        purge_started_at = payload.get("purge_started_at", purge_started_at)
        purge_completed_at = payload.get("purge_completed_at", purge_completed_at)
        disposal_status = payload.get("disposal_status", disposal_status)
        body_removed = payload.get("body_removed", body_removed) is True
        reviewer_notes_removed = payload.get("reviewer_notes_removed", reviewer_notes_removed) is True
        if payload.get("local_packet_exported") not in (None, False):
            raise ValueError("R50 R13 disposal receipt must keep local_packet_exported=False")
        if payload.get("content_hash_of_body_stored") not in (None, False):
            raise ValueError("R50 R13 disposal receipt must keep content_hash_of_body_stored=False")

    status = clean_identifier(disposal_status, default="NOT_GENERATED", max_length=80)
    receipt = {
        "schema_version": P7_R50_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION,
        "review_session_id": clean_identifier(review_session_id, default=P7_R50_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "packet_kind": P7_R50_PACKET_KIND,
        "case_count": _non_negative_int(case_count, default=P7_R50_REQUIRED_CASE_COUNT),
        "deleted_file_count": _non_negative_int(deleted_file_count, default=0),
        "purge_started_at": clean_identifier(purge_started_at, default="purge_started_at_unset", max_length=120),
        "purge_completed_at": clean_identifier(purge_completed_at, default="purge_completed_at_unset", max_length=120),
        "disposal_status": status,
        "body_removed": bool(body_removed),
        "reviewer_notes_removed": bool(reviewer_notes_removed),
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "p7_material_body_free": True,
        "body_free": True,
        "release_allowed": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "hold004_close_allowed": False,
    }
    assert_p7_r50_disposal_receipt_bodyfree_contract(receipt)
    return receipt


def assert_p7_r50_disposal_receipt_bodyfree_contract(receipt: Mapping[str, Any]) -> bool:
    data = safe_mapping(receipt)
    _assert_required_fields(
        data,
        required=P7_R50_DISPOSAL_RECEIPT_BODYFREE_REQUIRED_FIELD_REFS,
        source="p7_r50_disposal_receipt_bodyfree",
    )
    if data.get("schema_version") != P7_R50_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R50 disposal receipt schema version changed")
    if data.get("packet_kind") != P7_R50_PACKET_KIND:
        raise ValueError("R50 disposal receipt packet kind changed")
    if data.get("disposal_status") not in P7_R47_DISPOSAL_STATUSES:
        raise ValueError("R50 disposal receipt disposal status enum changed")
    for number_key in ("case_count", "deleted_file_count"):
        if not isinstance(data.get(number_key), int) or data.get(number_key) < 0:
            raise ValueError(f"R50 disposal receipt requires non-negative integer {number_key}")
    for bool_key in (
        "body_removed",
        "reviewer_notes_removed",
        "local_packet_exported",
        "content_hash_of_body_stored",
        "p7_material_body_free",
        "body_free",
        "release_allowed",
        "p7_complete",
        "p8_start_allowed",
        "hold004_close_allowed",
    ):
        if not isinstance(data.get(bool_key), bool):
            raise ValueError(f"R50 disposal receipt requires boolean {bool_key}")
    if data.get("local_packet_exported") is not False:
        raise ValueError("R50 disposal receipt must keep local_packet_exported=False")
    if data.get("content_hash_of_body_stored") is not False:
        raise ValueError("R50 disposal receipt must keep content_hash_of_body_stored=False")
    if data.get("p7_material_body_free") is not True or data.get("body_free") is not True:
        raise ValueError("R50 disposal receipt must remain body-free")
    for false_key in ("release_allowed", "p7_complete", "p8_start_allowed", "hold004_close_allowed"):
        if data.get(false_key) is not False:
            raise ValueError(f"R50 disposal receipt must keep {false_key}=False")
    status = data.get("disposal_status")
    if status == "DISPOSAL_VERIFIED":
        if data.get("body_removed") is not True or data.get("reviewer_notes_removed") is not True:
            raise ValueError("R50 DISPOSAL_VERIFIED requires body and reviewer notes removed")
    if status == "EXPIRED_PURGED":
        if data.get("body_removed") is not True or data.get("reviewer_notes_removed") is not True:
            raise ValueError("R50 EXPIRED_PURGED must still confirm local body and reviewer notes removal")
    if status == "DISPOSAL_FAILED":
        if data.get("body_removed") is True and data.get("reviewer_notes_removed") is True:
            raise ValueError("R50 DISPOSAL_FAILED must not look fully removed")
    _assert_no_forbidden_body_keys(data, source="p7_r50_disposal_receipt_bodyfree")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r50_disposal_receipt_bodyfree")
    return True


def _r13_status_from_r12(r12: Mapping[str, Any]) -> tuple[str, list[str], list[str]]:
    execution_blocker_ids = dedupe_identifiers(r12.get("execution_blocker_ids"), limit=20, max_length=120)
    if r12.get("pause_abort_expiration_protocol_status") != "READY_FOR_PAUSE_ABORT_EXPIRATION_PROTOCOL":
        return "BLOCKED_BY_R50_12_PAUSE_ABORT_EXPIRATION_PROTOCOL", ["r12_pause_abort_expiration_protocol_not_ready"], execution_blocker_ids
    return "READY_FOR_DISPOSAL_RECEIPT_BUILDER_VERIFIER", ["r12_pause_abort_expiration_protocol_ready"], execution_blocker_ids


def _r50_disposal_receipt_verification(receipt: Mapping[str, Any] | None) -> tuple[str, bool, bool, list[str], dict[str, Any]]:
    if receipt is None:
        return "PENDING", False, False, ["disposal_receipt_not_supplied_yet"], {}
    data = safe_mapping(receipt)
    assert_p7_r50_disposal_receipt_bodyfree_contract(data)
    status = clean_identifier(data.get("disposal_status"), default="NOT_GENERATED", max_length=80)
    removed = data.get("body_removed") is True and data.get("reviewer_notes_removed") is True
    no_export_or_hash = data.get("local_packet_exported") is False and data.get("content_hash_of_body_stored") is False
    if status == "DISPOSAL_VERIFIED" and removed and no_export_or_hash:
        return "VERIFIED", True, True, ["disposal_receipt_verified"], data
    if status == "EXPIRED_PURGED" and removed and no_export_or_hash:
        return "VERIFIED", True, False, ["expired_purged_body_removed_candidate_forbidden"], data
    if status == "DISPOSAL_FAILED":
        return "FAILED", False, False, ["disposal_failed"], data
    return "PENDING", False, False, ["disposal_receipt_not_verified"], data


def verify_p7_r50_disposal_receipt_bodyfree(receipt: Mapping[str, Any]) -> bool:
    """Compatibility verifier alias for the R50-13 body-free disposal receipt."""

    return assert_p7_r50_disposal_receipt_bodyfree_contract(receipt)


def build_p7_r50_disposal_receipt_builder_verifier_bodyfree(
    *,
    pause_abort_expiration_protocol_bodyfree: Mapping[str, Any] | None = None,
    disposal_receipt_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r50_disposal_receipt_builder_verifier_bodyfree",
) -> dict[str, Any]:
    """Build R50-13 body-free disposal receipt builder/verifier material."""

    r12 = safe_mapping(pause_abort_expiration_protocol_bodyfree) if pause_abort_expiration_protocol_bodyfree is not None else build_p7_r50_pause_abort_expiration_protocol_bodyfree()
    assert_p7_r50_pause_abort_expiration_protocol_bodyfree_contract(r12)
    builder_status, builder_reasons, execution_blocker_ids = _r13_status_from_r12(r12)
    ready = builder_status == "READY_FOR_DISPOSAL_RECEIPT_BUILDER_VERIFIER"
    verification_status, verified_for_summary, verified_for_candidate, verifier_reasons, receipt = _r50_disposal_receipt_verification(disposal_receipt_bodyfree) if ready else ("PENDING", False, False, ["r12_pause_abort_expiration_protocol_not_ready"], {})
    if ready and receipt and verified_for_summary:
        builder_status = "DISPOSAL_RECEIPT_VERIFIED_BODYFREE"
    elif ready and receipt:
        builder_status = "DISPOSAL_RECEIPT_PENDING_BODYFREE"
    verifier = {
        "schema_version": P7_R50_DISPOSAL_RECEIPT_BUILDER_VERIFIER_BODYFREE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R50_STEP,
        "scope": P7_R50_SCOPE,
        "policy_kind": P7_R50_POLICY_KIND,
        "policy_section": "R50-13_disposal_receipt_builder_verifier",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r50_disposal_receipt_builder_verifier_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r12.get("review_session_id"), default=P7_R50_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_session_status": "DISPOSAL_VERIFIED" if verified_for_summary else ("DISPOSAL_PENDING" if ready else "BLOCKED"),
        "r12_pause_abort_expiration_protocol_schema_version": P7_R50_PAUSE_ABORT_EXPIRATION_PROTOCOL_BODYFREE_SCHEMA_VERSION,
        "r12_pause_abort_expiration_protocol_ref": clean_identifier(r12.get("material_id"), default="p7_r50_pause_abort_expiration_protocol_bodyfree", max_length=180),
        "pause_abort_expiration_protocol_status": r12.get("pause_abort_expiration_protocol_status"),
        "disposal_receipt_builder_status": builder_status,
        "disposal_receipt_verification_status": verification_status,
        "builder_reason_refs": builder_reasons,
        "verifier_reason_refs": verifier_reasons,
        "required_case_count": P7_R50_REQUIRED_CASE_COUNT,
        "disposal_receipt_schema_version": P7_R50_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION,
        "r48_disposal_receipt_schema_version_ref": P7_R48_P5_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION,
        "r47_disposal_receipt_schema_version_ref": P7_R47_BODY_FREE_DISPOSAL_RECEIPT_SCHEMA_VERSION,
        "disposal_receipt_required_field_refs": list(P7_R50_DISPOSAL_RECEIPT_BODYFREE_REQUIRED_FIELD_REFS),
        "disposal_receipt_forbidden_field_refs": list(P7_R50_DISPOSAL_RECEIPT_FORBIDDEN_FIELD_REFS),
        "disposal_status_refs": list(P7_R47_DISPOSAL_STATUSES),
        "disposal_verified_for_candidate_status_refs": list(P7_R50_DISPOSAL_VERIFIED_FOR_CANDIDATE_STATUS_REFS),
        "body_removed_required": True,
        "reviewer_notes_removed_required": True,
        "local_packet_exported_required_false": True,
        "content_hash_of_body_required_false": True,
        "p7_material_body_free_required": True,
        "body_free_disposal_receipt_required_before_summary": True,
        "body_free_summary_finalize_allowed_without_disposal_receipt": False,
        "disposal_receipt_verified_for_summary": verified_for_summary,
        "disposal_verified_for_candidate": verified_for_candidate,
        "expired_purged_body_removed_but_candidate_forbidden": True,
        "disposal_failed_blocks_p5_p6_p8_candidates": True,
        "receipt_builder_function_ref": "build_p7_r50_disposal_receipt_bodyfree",
        "receipt_verifier_function_ref": "assert_p7_r50_disposal_receipt_bodyfree_contract",
        "disposal_receipt_bodyfree": receipt,
        "actual_disposal_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "local_only_body_full_generation_allowed": bool(ready and r12.get("local_only_body_full_generation_allowed") is True),
        "manual_run_decision_made_here": True,
        "p5_human_blind_qa_confirmed_candidate": False,
        "p6_limited_human_readfeel_start_allowed_candidate": False,
        "p8_question_design_material_candidate": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "r13_disposal_receipt_builder_verifier_built": True,
        "execution_blocker_ids": execution_blocker_ids,
        "open_execution_blocker_ids": dedupe_identifiers(r12.get("open_execution_blocker_ids"), limit=20, max_length=120),
        "implemented_steps": list(P7_R50_R13_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R50_R13_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r49_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_prior_validation_evidence_adopted": True,
        "r3_manual_run_decision_built": True,
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built": True,
        "r5_24_case_review_session_protocol_built": True,
        "r6_local_only_body_full_packet_generation_request_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": True,
        "r8_rating_row_normalizer_built": True,
        "r9_readfeel_blocker_execution_blocker_ingestion_built": True,
        "r10_question_need_observation_row_normalizer_built": True,
        "r11_rating_question_observation_consistency_guard_built": True,
        "r12_pause_abort_expiration_protocol_built": ready,
        "first_next_work_ref": P7_R50_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R50_R13_NEXT_REQUIRED_STEP_REF if ready else P7_R50_R13_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r50_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_for(P7_R50_R13_FALSE_KEY_REFS),
    }
    assert_p7_r50_disposal_receipt_builder_verifier_bodyfree_contract(verifier)
    return verifier


def assert_p7_r50_disposal_receipt_builder_verifier_bodyfree_contract(verifier: Mapping[str, Any]) -> bool:
    data = safe_mapping(verifier)
    _assert_required_fields(
        data,
        required=P7_R50_DISPOSAL_RECEIPT_BUILDER_VERIFIER_BODYFREE_REQUIRED_FIELD_REFS,
        source="p7_r50_r13_disposal_receipt_builder_verifier",
    )
    _assert_common_with_false_keys(
        data,
        schema_version=P7_R50_DISPOSAL_RECEIPT_BUILDER_VERIFIER_BODYFREE_SCHEMA_VERSION,
        source="p7_r50_r13_disposal_receipt_builder_verifier",
        false_keys=P7_R50_R13_FALSE_KEY_REFS,
    )
    if data.get("policy_section") != "R50-13_disposal_receipt_builder_verifier":
        raise ValueError("R50 R13 policy section changed")
    if data.get("r12_pause_abort_expiration_protocol_schema_version") != P7_R50_PAUSE_ABORT_EXPIRATION_PROTOCOL_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R50 R13 R12 protocol schema changed")
    if data.get("disposal_receipt_schema_version") != P7_R50_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R50 R13 disposal receipt schema changed")
    if data.get("r48_disposal_receipt_schema_version_ref") != P7_R48_P5_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R50 R13 R48 disposal schema ref changed")
    if data.get("r47_disposal_receipt_schema_version_ref") != P7_R47_BODY_FREE_DISPOSAL_RECEIPT_SCHEMA_VERSION:
        raise ValueError("R50 R13 R47 disposal schema ref changed")
    if tuple(data.get("disposal_receipt_required_field_refs") or ()) != P7_R50_DISPOSAL_RECEIPT_BODYFREE_REQUIRED_FIELD_REFS:
        raise ValueError("R50 R13 disposal receipt required fields changed")
    if tuple(data.get("disposal_status_refs") or ()) != P7_R47_DISPOSAL_STATUSES:
        raise ValueError("R50 R13 disposal status refs changed")
    if tuple(data.get("disposal_verified_for_candidate_status_refs") or ()) != P7_R50_DISPOSAL_VERIFIED_FOR_CANDIDATE_STATUS_REFS:
        raise ValueError("R50 R13 candidate verified status refs changed")
    for true_key in (
        "body_removed_required",
        "reviewer_notes_removed_required",
        "local_packet_exported_required_false",
        "content_hash_of_body_required_false",
        "p7_material_body_free_required",
        "body_free_disposal_receipt_required_before_summary",
        "expired_purged_body_removed_but_candidate_forbidden",
        "disposal_failed_blocks_p5_p6_p8_candidates",
        "manual_run_decision_made_here",
        "r13_disposal_receipt_builder_verifier_built",
        "r0_current_source_r49_handoff_bridge_refrozen",
        "r1_scope_schema_status_enum_fixed",
        "r2_prior_validation_evidence_adopted",
        "r3_manual_run_decision_built",
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
        "r5_24_case_review_session_protocol_built",
        "r6_local_only_body_full_packet_generation_request_built",
        "r7_reviewer_instruction_rating_form_freeze_built",
        "r8_rating_row_normalizer_built",
        "r9_readfeel_blocker_execution_blocker_ingestion_built",
        "r10_question_need_observation_row_normalizer_built",
        "r11_rating_question_observation_consistency_guard_built",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R50 R13 must keep {true_key}=True")
    for false_key in (
        "body_free_summary_finalize_allowed_without_disposal_receipt",
        "actual_disposal_run_here",
        "actual_disposal_receipt_materialized_here",
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
        "p5_human_blind_qa_confirmed_candidate",
        "p6_limited_human_readfeel_start_allowed_candidate",
        "p8_question_design_material_candidate",
        "p7_complete",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R50 R13 must keep {false_key}=False")
    receipt = safe_mapping(data.get("disposal_receipt_bodyfree"))
    if receipt:
        assert_p7_r50_disposal_receipt_bodyfree_contract(receipt)
    if data.get("disposal_receipt_builder_status") == "BLOCKED_BY_R50_12_PAUSE_ABORT_EXPIRATION_PROTOCOL":
        if data.get("local_only_body_full_generation_allowed") is not False:
            raise ValueError("R50 R13 blocked status must not preserve local-only permission")
        if data.get("next_required_step") != P7_R50_R13_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R13 blocked status must point to R50-12 resolution")
    else:
        if data.get("pause_abort_expiration_protocol_status") != "READY_FOR_PAUSE_ABORT_EXPIRATION_PROTOCOL":
            raise ValueError("R50 R13 ready status requires R50-12 ready")
        if data.get("local_only_body_full_generation_allowed") is not True:
            raise ValueError("R50 R13 ready status must preserve local-only permission")
        if data.get("next_required_step") != P7_R50_R13_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R13 ready status must point to R50-14")
    verification_status = data.get("disposal_receipt_verification_status")
    if verification_status not in P7_R50_DISPOSAL_RECEIPT_VERIFICATION_STATUS_REFS:
        raise ValueError("R50 R13 verifier status enum changed")
    if data.get("disposal_receipt_verified_for_summary") is True:
        if not receipt:
            raise ValueError("R50 R13 verified summary requires a receipt")
        if receipt.get("body_removed") is not True or receipt.get("reviewer_notes_removed") is not True:
            raise ValueError("R50 R13 verified summary requires removed body and notes")
        if receipt.get("local_packet_exported") is not False or receipt.get("content_hash_of_body_stored") is not False:
            raise ValueError("R50 R13 verified summary forbids export/hash")
    if data.get("disposal_verified_for_candidate") is True:
        if not receipt or receipt.get("disposal_status") != "DISPOSAL_VERIFIED":
            raise ValueError("R50 R13 candidate disposal verification requires DISPOSAL_VERIFIED only")
    if receipt and receipt.get("disposal_status") == "EXPIRED_PURGED" and data.get("disposal_verified_for_candidate") is True:
        raise ValueError("R50 R13 EXPIRED_PURGED must not become P5 candidate disposal verification")
    if tuple(data.get("implemented_steps") or ()) != P7_R50_R13_IMPLEMENTED_STEPS:
        raise ValueError("R50 R13 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_R13_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R13 not-yet steps changed")
    return True


def build_p7_r50_r12_r13_disposal_protocol_freeze(
    *,
    rating_question_observation_consistency_guard_bodyfree: Mapping[str, Any] | None = None,
    pause_abort_expiration_protocol_bodyfree: Mapping[str, Any] | None = None,
    disposal_receipt_builder_verifier_bodyfree: Mapping[str, Any] | None = None,
    disposal_receipt_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r50_r12_r13_disposal_protocol_freeze",
) -> dict[str, Any]:
    r12 = safe_mapping(pause_abort_expiration_protocol_bodyfree) if pause_abort_expiration_protocol_bodyfree is not None else build_p7_r50_pause_abort_expiration_protocol_bodyfree(
        rating_question_observation_consistency_guard_bodyfree=rating_question_observation_consistency_guard_bodyfree
    )
    assert_p7_r50_pause_abort_expiration_protocol_bodyfree_contract(r12)
    r13 = safe_mapping(disposal_receipt_builder_verifier_bodyfree) if disposal_receipt_builder_verifier_bodyfree is not None else build_p7_r50_disposal_receipt_builder_verifier_bodyfree(
        pause_abort_expiration_protocol_bodyfree=r12,
        disposal_receipt_bodyfree=disposal_receipt_bodyfree,
    )
    assert_p7_r50_disposal_receipt_builder_verifier_bodyfree_contract(r13)
    freeze = {
        "schema_version": P7_R50_R12_R13_DISPOSAL_PROTOCOL_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R50_STEP,
        "scope": P7_R50_SCOPE,
        "policy_kind": P7_R50_POLICY_KIND,
        "policy_section": "R50-12_R50-13_disposal_protocol_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r50_r12_r13_disposal_protocol_freeze", max_length=180),
        "r12_pause_abort_expiration_protocol": r12,
        "r13_disposal_receipt_builder_verifier": r13,
        "review_session_id": r13["review_session_id"],
        "pause_abort_expiration_protocol_status": r12["pause_abort_expiration_protocol_status"],
        "disposal_receipt_builder_status": r13["disposal_receipt_builder_status"],
        "disposal_receipt_verification_status": r13["disposal_receipt_verification_status"],
        "disposal_receipt_verified_for_summary": r13["disposal_receipt_verified_for_summary"],
        "local_only_body_full_generation_allowed": r13["local_only_body_full_generation_allowed"],
        "manual_run_decision_made_here": True,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "actual_disposal_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "implemented_steps": list(P7_R50_R13_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R50_R13_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r49_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_prior_validation_evidence_adopted": True,
        "r3_manual_run_decision_built": True,
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built": True,
        "r5_24_case_review_session_protocol_built": True,
        "r6_local_only_body_full_packet_generation_request_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": True,
        "r8_rating_row_normalizer_built": True,
        "r9_readfeel_blocker_execution_blocker_ingestion_built": True,
        "r10_question_need_observation_row_normalizer_built": True,
        "r11_rating_question_observation_consistency_guard_built": True,
        "r12_pause_abort_expiration_protocol_built": True,
        "r13_disposal_receipt_builder_verifier_built": True,
        "first_next_work_ref": P7_R50_FIRST_NEXT_WORK_REF,
        "next_required_step": r13["next_required_step"],
        "public_contract": public_contract_flags(),
        "r50_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_for(P7_R50_R13_FALSE_KEY_REFS),
    }
    assert_p7_r50_r12_r13_disposal_protocol_freeze_contract(freeze)
    return freeze


def assert_p7_r50_r12_r13_disposal_protocol_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_required_fields(
        data,
        required=P7_R50_R12_R13_DISPOSAL_PROTOCOL_FREEZE_REQUIRED_FIELD_REFS,
        source="p7_r50_r12_r13_disposal_protocol_freeze",
    )
    _assert_common_with_false_keys(
        data,
        schema_version=P7_R50_R12_R13_DISPOSAL_PROTOCOL_FREEZE_SCHEMA_VERSION,
        source="p7_r50_r12_r13_disposal_protocol_freeze",
        false_keys=P7_R50_R13_FALSE_KEY_REFS,
    )
    if data.get("policy_section") != "R50-12_R50-13_disposal_protocol_freeze":
        raise ValueError("R50 R12/R13 policy section changed")
    r12 = safe_mapping(data.get("r12_pause_abort_expiration_protocol"))
    r13 = safe_mapping(data.get("r13_disposal_receipt_builder_verifier"))
    assert_p7_r50_pause_abort_expiration_protocol_bodyfree_contract(r12)
    assert_p7_r50_disposal_receipt_builder_verifier_bodyfree_contract(r13)
    if data.get("pause_abort_expiration_protocol_status") != r12.get("pause_abort_expiration_protocol_status"):
        raise ValueError("R50 R12/R13 pause/abort protocol status mismatch")
    if data.get("disposal_receipt_builder_status") != r13.get("disposal_receipt_builder_status"):
        raise ValueError("R50 R12/R13 disposal builder status mismatch")
    if data.get("disposal_receipt_verification_status") != r13.get("disposal_receipt_verification_status"):
        raise ValueError("R50 R12/R13 disposal verifier status mismatch")
    if data.get("disposal_receipt_verified_for_summary") is not r13.get("disposal_receipt_verified_for_summary"):
        raise ValueError("R50 R12/R13 disposal verified mismatch")
    if data.get("local_only_body_full_generation_allowed") is not r13.get("local_only_body_full_generation_allowed"):
        raise ValueError("R50 R12/R13 local-only permission mismatch")
    for false_key in (
        "actual_manual_review_run_here",
        "body_full_packet_generated_here",
        "actual_disposal_run_here",
        "actual_disposal_receipt_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R50 R12/R13 must keep {false_key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R50_R13_IMPLEMENTED_STEPS:
        raise ValueError("R50 R12/R13 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_R13_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R12/R13 not-yet steps changed")
    return True




# ---------------------------------------------------------------------------
# R50-14 / R50-15: body-free post-review summary and P5 decision
# ---------------------------------------------------------------------------


def _r50_case_ref_identity(row: Mapping[str, Any]) -> tuple[str, str, str, str, str]:
    data = safe_mapping(row)
    return (
        clean_identifier(data.get("review_session_id"), default="", max_length=140),
        clean_identifier(data.get("packet_ref_id"), default="", max_length=160),
        clean_identifier(data.get("blind_case_id"), default="", max_length=160),
        clean_identifier(data.get("case_ref_id"), default="", max_length=160),
        clean_identifier(data.get("family"), default="", max_length=120),
    )


def _zero_count_map(refs: Sequence[str]) -> dict[str, int]:
    return {str(ref): 0 for ref in refs}


def _increment_count_map(target: dict[str, int], refs: Sequence[Any], *, allowed_refs: Sequence[str], source: str) -> None:
    allowed = set(allowed_refs)
    for raw_ref in refs or ():
        ref = clean_identifier(raw_ref, default="", max_length=160)
        if ref not in allowed:
            raise ValueError(f"{source} uses a non-canonical ref: {ref}")
        target[ref] += 1


def _rating_rows_for_r50_summary(rows: Sequence[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for raw in rows or ():
        row = dict(safe_mapping(raw))
        assert_p7_r50_rating_capture_row_bodyfree_contract(row)
        normalized.append(row)
    return normalized


def _question_rows_for_r50_summary(rows: Sequence[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for raw in rows or ():
        row = dict(safe_mapping(raw))
        assert_p7_r50_question_need_observation_row_bodyfree_contract(row)
        normalized.append(row)
    return normalized


def _readfeel_blocker_rows_for_r50_summary(rows: Sequence[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for raw in rows or ():
        row = dict(safe_mapping(raw))
        assert_p7_r50_readfeel_blocker_row_bodyfree_contract(row)
        normalized.append(row)
    return normalized


def _execution_blocker_rows_for_r50_summary(rows: Sequence[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for raw in rows or ():
        row = dict(safe_mapping(raw))
        assert_p7_r50_execution_blocker_row_bodyfree_contract(row)
        normalized.append(row)
    return normalized


def _axis_score_averages_for_r50(rows: Sequence[Mapping[str, Any]]) -> dict[str, float | None]:
    averages: dict[str, float | None] = {}
    for axis in P5_HUMAN_BLIND_QA_RATING_AXES:
        values = [float(safe_mapping(row.get("axis_scores")).get(axis, 0.0)) for row in rows]
        averages[axis] = round(sum(values) / len(values), 4) if values else None
    return averages


def _axis_target_flags_for_r50(averages: Mapping[str, Any]) -> tuple[list[str], list[str]]:
    met: list[str] = []
    failed: list[str] = []
    for axis, target in P5_HUMAN_BLIND_QA_TARGETS.items():
        value = averages.get(axis)
        if isinstance(value, (int, float)) and value >= float(target):
            met.append(axis)
        else:
            failed.append(axis)
    return met, failed


def _build_count_maps_for_r50_summary(
    *,
    rating_rows: Sequence[Mapping[str, Any]],
    question_rows: Sequence[Mapping[str, Any]],
    readfeel_blocker_rows: Sequence[Mapping[str, Any]],
    execution_blocker_rows: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, int]]:
    verdict_counts = _zero_count_map(P7_R50_RATING_VERDICT_REFS)
    for row in rating_rows:
        verdict = clean_identifier(row.get("verdict"), default="", max_length=80)
        if verdict not in P7_R50_RATING_VERDICT_REFS:
            raise ValueError("R50 R14 verdict count used a non-canonical verdict")
        verdict_counts[verdict] += 1

    blocker_counts = _zero_count_map(P7_R48_READFEEL_BLOCKER_ID_REFS)
    for row in readfeel_blocker_rows:
        blocker_id = clean_identifier(row.get("blocker_id"), default="", max_length=160)
        if blocker_id not in P7_R48_READFEEL_BLOCKER_ID_REFS:
            raise ValueError("R50 R14 blocker count used a non-canonical readfeel blocker")
        blocker_counts[blocker_id] += 1

    execution_blocker_counts = _zero_count_map(P7_R50_EXECUTION_BLOCKER_ID_REFS)
    for row in execution_blocker_rows:
        blocker_id = clean_identifier(row.get("execution_blocker_id"), default="", max_length=160)
        if blocker_id not in P7_R50_EXECUTION_BLOCKER_ID_REFS:
            raise ValueError("R50 R14 execution blocker count used a non-canonical blocker")
        execution_blocker_counts[blocker_id] += 1

    primary_counts = _zero_count_map(P7_R50_QUESTION_NEED_PRIMARY_CLASS_REFS)
    ambiguity_counts = _zero_count_map(P7_R50_AMBIGUITY_KIND_REFS)
    one_question_fit_counts = _zero_count_map(P7_R50_ONE_QUESTION_FIT_REFS)
    repair_required_counts = _zero_count_map(P7_R50_REPAIR_REQUIRED_REF_REFS)
    for row in question_rows:
        primary = clean_identifier(row.get("question_need_primary_class"), default="", max_length=160)
        if primary not in P7_R50_QUESTION_NEED_PRIMARY_CLASS_REFS:
            raise ValueError("R50 R14 question primary count used a non-canonical enum")
        primary_counts[primary] += 1
        _increment_count_map(
            ambiguity_counts,
            row.get("ambiguity_kind_refs") or (),
            allowed_refs=P7_R50_AMBIGUITY_KIND_REFS,
            source="R50 R14 ambiguity_kind_counts",
        )
        one_fit = clean_identifier(row.get("one_question_fit_ref"), default="", max_length=160)
        if one_fit not in P7_R50_ONE_QUESTION_FIT_REFS:
            raise ValueError("R50 R14 one-question-fit count used a non-canonical enum")
        one_question_fit_counts[one_fit] += 1
        _increment_count_map(
            repair_required_counts,
            row.get("repair_required_refs") or (),
            allowed_refs=P7_R50_REPAIR_REQUIRED_REF_REFS,
            source="R50 R14 repair_required_counts",
        )
    return {
        "verdict_counts": verdict_counts,
        "blocker_counts": blocker_counts,
        "execution_blocker_counts": execution_blocker_counts,
        "question_need_primary_class_counts": primary_counts,
        "ambiguity_kind_counts": ambiguity_counts,
        "one_question_fit_counts": one_question_fit_counts,
        "repair_required_counts": repair_required_counts,
    }


def build_p7_r50_body_free_post_review_summary_bodyfree(
    *,
    disposal_receipt_builder_verifier_bodyfree: Mapping[str, Any] | None = None,
    disposal_receipt_bodyfree: Mapping[str, Any] | None = None,
    rating_rows_bodyfree: Sequence[Mapping[str, Any]] | None = None,
    question_need_observation_rows_bodyfree: Sequence[Mapping[str, Any]] | None = None,
    readfeel_blocker_rows_bodyfree: Sequence[Mapping[str, Any]] | None = None,
    execution_blocker_rows_bodyfree: Sequence[Mapping[str, Any]] | None = None,
    material_id: Any = "p7_r50_body_free_post_review_summary_bodyfree",
) -> dict[str, Any]:
    """Build the R50-14 body-free post-review summary from sanitized rows only."""

    r13 = (
        safe_mapping(disposal_receipt_builder_verifier_bodyfree)
        if disposal_receipt_builder_verifier_bodyfree is not None
        else build_p7_r50_disposal_receipt_builder_verifier_bodyfree(disposal_receipt_bodyfree=disposal_receipt_bodyfree)
    )
    assert_p7_r50_disposal_receipt_builder_verifier_bodyfree_contract(r13)
    receipt = safe_mapping(r13.get("disposal_receipt_bodyfree"))
    rating_rows = _rating_rows_for_r50_summary(rating_rows_bodyfree)
    question_rows = _question_rows_for_r50_summary(question_need_observation_rows_bodyfree)
    readfeel_blocker_rows = _readfeel_blocker_rows_for_r50_summary(readfeel_blocker_rows_bodyfree)
    execution_blocker_rows = _execution_blocker_rows_for_r50_summary(execution_blocker_rows_bodyfree)

    rating_case_refs = {_r50_case_ref_identity(row) for row in rating_rows}
    question_case_refs = {_r50_case_ref_identity(row) for row in question_rows}
    rating_and_question_case_ref_sets_match = bool(rating_case_refs == question_case_refs) if (rating_rows or question_rows) else False
    count_maps = _build_count_maps_for_r50_summary(
        rating_rows=rating_rows,
        question_rows=question_rows,
        readfeel_blocker_rows=readfeel_blocker_rows,
        execution_blocker_rows=execution_blocker_rows,
    )
    axis_averages = _axis_score_averages_for_r50(rating_rows)
    axis_met_refs, axis_failed_refs = _axis_target_flags_for_r50(axis_averages)
    disposal_verified_for_summary = r13.get("disposal_receipt_verified_for_summary") is True
    summary_status = (
        "BODYFREE_POST_REVIEW_SUMMARY_READY"
        if disposal_verified_for_summary
        else "BLOCKED_BY_R50_13_DISPOSAL_RECEIPT"
    )
    summary_reason_refs = (
        ["r13_disposal_receipt_verified_for_summary"]
        if disposal_verified_for_summary
        else ["r13_disposal_receipt_not_verified_for_summary"]
    )
    open_execution_blocker_ids = dedupe_identifiers(
        [row.get("execution_blocker_id") for row in execution_blocker_rows if row.get("execution_blocker_status") == "OPEN"],
        limit=40,
        max_length=160,
    )
    open_readfeel_blocker_count = sum(1 for row in readfeel_blocker_rows if row.get("blocker_status") == "OPEN")
    summary = {
        "schema_version": P7_R50_BODY_FREE_POST_REVIEW_SUMMARY_BODYFREE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R50_STEP,
        "scope": P7_R50_SCOPE,
        "policy_kind": P7_R50_POLICY_KIND,
        "policy_section": "R50-14_body_free_post_review_summary_builder",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r50_body_free_post_review_summary_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r13.get("review_session_id"), default=P7_R50_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_session_status": "SUMMARY_READY" if disposal_verified_for_summary else "BLOCKED",
        "r13_disposal_receipt_builder_verifier_schema_version": P7_R50_DISPOSAL_RECEIPT_BUILDER_VERIFIER_BODYFREE_SCHEMA_VERSION,
        "r13_disposal_receipt_builder_verifier_ref": clean_identifier(r13.get("material_id"), default="p7_r50_disposal_receipt_builder_verifier_bodyfree", max_length=180),
        "disposal_receipt_builder_status": clean_identifier(r13.get("disposal_receipt_builder_status"), default="BLOCKED_BY_R50_12_PAUSE_ABORT_EXPIRATION_PROTOCOL", max_length=120),
        "disposal_receipt_verification_status": clean_identifier(r13.get("disposal_receipt_verification_status"), default="PENDING", max_length=80),
        "disposal_receipt_verified_for_summary": disposal_verified_for_summary,
        "disposal_verified_for_candidate": r13.get("disposal_verified_for_candidate") is True,
        "post_review_summary_builder_status": summary_status,
        "summary_reason_refs": summary_reason_refs,
        "required_case_count": P7_R50_REQUIRED_CASE_COUNT,
        "case_count": len(rating_case_refs | question_case_refs),
        "rating_row_count": len(rating_rows),
        "unique_rating_case_count": len(rating_case_refs),
        "question_observation_row_count": len(question_rows),
        "unique_question_observation_case_count": len(question_case_refs),
        "rating_and_question_case_ref_sets_match": rating_and_question_case_ref_sets_match,
        "verdict_counts": count_maps["verdict_counts"],
        "axis_score_averages": axis_averages,
        "axis_target_refs": dict(P5_HUMAN_BLIND_QA_TARGETS),
        "axis_target_met_refs": axis_met_refs,
        "axis_target_failed_refs": axis_failed_refs,
        "blocker_counts": count_maps["blocker_counts"],
        "readfeel_blocker_open_count": open_readfeel_blocker_count,
        "execution_blocker_counts": count_maps["execution_blocker_counts"],
        "execution_blocker_open_count": len(open_execution_blocker_ids),
        "inherited_open_execution_blocker_ids": open_execution_blocker_ids,
        "question_need_primary_class_counts": count_maps["question_need_primary_class_counts"],
        "ambiguity_kind_counts": count_maps["ambiguity_kind_counts"],
        "one_question_fit_counts": count_maps["one_question_fit_counts"],
        "repair_required_counts": count_maps["repair_required_counts"],
        "disposal_status": clean_identifier(receipt.get("disposal_status"), default="NOT_GENERATED", max_length=80),
        "body_removed": receipt.get("body_removed") is True,
        "reviewer_notes_removed": receipt.get("reviewer_notes_removed") is True,
        "local_packet_exported": receipt.get("local_packet_exported") is True,
        "content_hash_of_body_stored": receipt.get("content_hash_of_body_stored") is True,
        "body_free_summary_ready": disposal_verified_for_summary,
        "p5_decision_required_next": disposal_verified_for_summary,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "post_review_summary_materialized_here": False,
        "p5_human_blind_qa_confirmed_candidate": False,
        "p5_repair_return_candidate": False,
        "p6_limited_human_readfeel_start_allowed_candidate": False,
        "p8_question_design_material_candidate": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "manual_run_decision_made_here": True,
        "implemented_steps": list(P7_R50_R14_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R50_R14_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r49_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_prior_validation_evidence_adopted": True,
        "r3_manual_run_decision_built": True,
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built": True,
        "r5_24_case_review_session_protocol_built": True,
        "r6_local_only_body_full_packet_generation_request_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": True,
        "r8_rating_row_normalizer_built": True,
        "r9_readfeel_blocker_execution_blocker_ingestion_built": True,
        "r10_question_need_observation_row_normalizer_built": True,
        "r11_rating_question_observation_consistency_guard_built": True,
        "r12_pause_abort_expiration_protocol_built": True,
        "r13_disposal_receipt_builder_verifier_built": True,
        "r14_body_free_post_review_summary_built": True,
        "first_next_work_ref": P7_R50_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R50_R14_NEXT_REQUIRED_STEP_REF if disposal_verified_for_summary else P7_R50_R14_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r50_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_for(P7_R50_R14_FALSE_KEY_REFS),
    }
    assert_p7_r50_body_free_post_review_summary_bodyfree_contract(summary)
    return summary


def build_p7_r50_bodyfree_post_review_summary_builder(**kwargs: Any) -> dict[str, Any]:
    """Compatibility alias for the R50-14 summary builder."""

    return build_p7_r50_body_free_post_review_summary_bodyfree(**kwargs)


def assert_p7_r50_body_free_post_review_summary_bodyfree_contract(summary: Mapping[str, Any]) -> bool:
    data = safe_mapping(summary)
    _assert_required_fields(
        data,
        required=P7_R50_BODY_FREE_POST_REVIEW_SUMMARY_BODYFREE_REQUIRED_FIELD_REFS,
        source="p7_r50_body_free_post_review_summary_bodyfree",
    )
    _assert_common_with_false_keys(
        data,
        schema_version=P7_R50_BODY_FREE_POST_REVIEW_SUMMARY_BODYFREE_SCHEMA_VERSION,
        source="p7_r50_body_free_post_review_summary_bodyfree",
        false_keys=P7_R50_R14_FALSE_KEY_REFS,
    )
    if data.get("policy_section") != "R50-14_body_free_post_review_summary_builder":
        raise ValueError("R50 R14 policy section changed")
    if data.get("post_review_summary_builder_status") not in P7_R50_POST_REVIEW_SUMMARY_BUILDER_STATUS_REFS:
        raise ValueError("R50 R14 summary status is not canonical")
    if data.get("rating_row_count") != data.get("unique_rating_case_count"):
        raise ValueError("R50 R14 rating rows must be unique by case ref")
    if data.get("question_observation_row_count") != data.get("unique_question_observation_case_count"):
        raise ValueError("R50 R14 question rows must be unique by case ref")
    if data.get("post_review_summary_builder_status") == "BODYFREE_POST_REVIEW_SUMMARY_READY":
        if data.get("disposal_receipt_verified_for_summary") is not True:
            raise ValueError("R50 R14 ready summary requires disposal receipt verified for summary")
        if data.get("next_required_step") != P7_R50_R14_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R14 ready summary must point to R50-15")
    else:
        if data.get("body_free_summary_ready") is not False:
            raise ValueError("R50 R14 blocked summary cannot be ready")
        if data.get("next_required_step") != P7_R50_R14_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R14 blocked summary must point to R13 resolution")
    for counts_key, allowed_refs in (
        ("verdict_counts", P7_R50_RATING_VERDICT_REFS),
        ("blocker_counts", P7_R48_READFEEL_BLOCKER_ID_REFS),
        ("execution_blocker_counts", P7_R50_EXECUTION_BLOCKER_ID_REFS),
        ("question_need_primary_class_counts", P7_R50_QUESTION_NEED_PRIMARY_CLASS_REFS),
        ("ambiguity_kind_counts", P7_R50_AMBIGUITY_KIND_REFS),
        ("one_question_fit_counts", P7_R50_ONE_QUESTION_FIT_REFS),
        ("repair_required_counts", P7_R50_REPAIR_REQUIRED_REF_REFS),
    ):
        counts = safe_mapping(data.get(counts_key))
        if set(counts) != set(allowed_refs):
            raise ValueError(f"R50 R14 {counts_key} must preserve canonical refs")
        if any(not isinstance(value, int) or value < 0 for value in counts.values()):
            raise ValueError(f"R50 R14 {counts_key} must be non-negative int counts")
    if tuple(data.get("implemented_steps") or ()) != P7_R50_R14_IMPLEMENTED_STEPS:
        raise ValueError("R50 R14 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_R14_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R14 not-yet steps changed")
    return True


def _decision_reasons_from_summary_r50(summary: Mapping[str, Any]) -> tuple[str, list[str], list[str], list[str], list[str], str]:
    verdict_counts = safe_mapping(summary.get("verdict_counts"))
    blocker_counts = safe_mapping(summary.get("blocker_counts"))
    primary_counts = safe_mapping(summary.get("question_need_primary_class_counts"))
    repair_counts = safe_mapping(summary.get("repair_required_counts"))
    axis_failed_refs = dedupe_identifiers(summary.get("axis_target_failed_refs"), limit=20, max_length=120)
    confirmed_reason_refs: list[str] = []
    repair_reason_refs: list[str] = []
    inconclusive_reason_refs: list[str] = []

    complete_24 = summary.get("rating_row_count") == P7_R50_REQUIRED_CASE_COUNT and summary.get("question_observation_row_count") == P7_R50_REQUIRED_CASE_COUNT
    candidate_disposal_ok = (
        summary.get("disposal_verified_for_candidate") is True
        and summary.get("disposal_status") == "DISPOSAL_VERIFIED"
        and summary.get("body_removed") is True
        and summary.get("reviewer_notes_removed") is True
        and summary.get("local_packet_exported") is False
        and summary.get("content_hash_of_body_stored") is False
    )

    if summary.get("post_review_summary_builder_status") != "BODYFREE_POST_REVIEW_SUMMARY_READY":
        inconclusive_reason_refs.append("r14_summary_not_ready")
    if not complete_24:
        inconclusive_reason_refs.append("r50_24_case_rows_incomplete")
    if summary.get("rating_and_question_case_ref_sets_match") is not True:
        inconclusive_reason_refs.append("r50_rating_question_case_refs_do_not_match")
    if summary.get("execution_blocker_open_count") != 0:
        inconclusive_reason_refs.append("r50_open_execution_blockers")
    if not candidate_disposal_ok:
        inconclusive_reason_refs.append("r50_disposal_not_verified_for_candidate")
    if summary.get("body_free_summary_ready") is not True:
        inconclusive_reason_refs.append("r50_body_free_summary_not_ready")

    repair_blockers = [ref for ref in P7_R50_REPAIR_RETURN_BLOCKER_ID_REFS if int(blocker_counts.get(ref, 0)) > 0]
    repair_primary = [ref for ref in P7_R50_REPAIR_RETURN_QUESTION_PRIMARY_CLASS_REFS if int(primary_counts.get(ref, 0)) > 0]
    repair_refs = [ref for ref in P7_R50_REPAIR_RETURN_REPAIR_REQUIRED_REF_REFS if int(repair_counts.get(ref, 0)) > 0]
    if int(verdict_counts.get("RED", 0)) > 0:
        repair_reason_refs.append("red_verdict_present")
    if int(verdict_counts.get("REPAIR_REQUIRED", 0)) > 0:
        repair_reason_refs.append("repair_required_verdict_present")
    repair_reason_refs.extend(f"readfeel_blocker:{ref}" for ref in repair_blockers)
    repair_reason_refs.extend(f"question_primary_repair:{ref}" for ref in repair_primary)
    repair_reason_refs.extend(f"repair_required_ref:{ref}" for ref in repair_refs)
    repair_reason_refs.extend(f"axis_target_failed:{ref}" for ref in axis_failed_refs)

    if not inconclusive_reason_refs and not repair_reason_refs:
        confirmed_reason_refs.extend(P7_R50_P5_CONFIRMED_REQUIREMENT_REFS)
        return "P5_CONFIRMED_CANDIDATE", ["all_p5_confirmed_candidate_requirements_met"], confirmed_reason_refs, [], [], P7_R50_R15_NEXT_REQUIRED_STEP_REF
    if not inconclusive_reason_refs and repair_reason_refs:
        return "P5_REPAIR_RETURN", dedupe_identifiers(repair_reason_refs, limit=80, max_length=180), [], repair_reason_refs, [], P7_R50_R15_REPAIR_RETURN_NEXT_REQUIRED_STEP_REF
    return "P5_REVIEW_INCONCLUSIVE", dedupe_identifiers(inconclusive_reason_refs, limit=80, max_length=180), [], [], inconclusive_reason_refs, P7_R50_R15_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF


def build_p7_r50_p5_confirmed_repair_return_inconclusive_decision_bodyfree(
    *,
    post_review_summary_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r50_p5_confirmed_repair_return_inconclusive_decision_bodyfree",
) -> dict[str, Any]:
    """Build the R50-15 P5 confirmed / repair-return / inconclusive decision."""

    summary = safe_mapping(post_review_summary_bodyfree) if post_review_summary_bodyfree is not None else build_p7_r50_body_free_post_review_summary_bodyfree()
    assert_p7_r50_body_free_post_review_summary_bodyfree_contract(summary)
    if summary.get("post_review_summary_builder_status") != "BODYFREE_POST_REVIEW_SUMMARY_READY":
        decision_status = "BLOCKED_BY_R50_14_POST_REVIEW_SUMMARY"
        decision_reason_refs = ["r14_body_free_post_review_summary_not_ready"]
        confirmed_reason_refs: list[str] = []
        repair_reason_refs: list[str] = []
        inconclusive_reason_refs: list[str] = ["r14_body_free_post_review_summary_not_ready"]
        next_required_step = P7_R50_R15_BLOCKED_NEXT_REQUIRED_STEP_REF
    else:
        decision_status, decision_reason_refs, confirmed_reason_refs, repair_reason_refs, inconclusive_reason_refs, next_required_step = _decision_reasons_from_summary_r50(summary)
    is_confirmed_candidate = decision_status == "P5_CONFIRMED_CANDIDATE"
    is_repair_return = decision_status == "P5_REPAIR_RETURN"
    is_inconclusive = decision_status in {"P5_REVIEW_INCONCLUSIVE", "BLOCKED_BY_R50_14_POST_REVIEW_SUMMARY"}
    decision = {
        "schema_version": P7_R50_P5_CONFIRMED_REPAIR_INCONCLUSIVE_DECISION_BODYFREE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R50_STEP,
        "scope": P7_R50_SCOPE,
        "policy_kind": P7_R50_POLICY_KIND,
        "policy_section": "R50-15_p5_confirmed_repair_return_inconclusive_decision",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r50_p5_confirmed_repair_return_inconclusive_decision_bodyfree", max_length=180),
        "review_session_id": clean_identifier(summary.get("review_session_id"), default=P7_R50_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_session_status": "DECISION_FINALIZED" if decision_status in {"P5_CONFIRMED_CANDIDATE", "P5_REPAIR_RETURN", "P5_REVIEW_INCONCLUSIVE"} else "BLOCKED",
        "r14_post_review_summary_schema_version": P7_R50_BODY_FREE_POST_REVIEW_SUMMARY_BODYFREE_SCHEMA_VERSION,
        "r14_post_review_summary_ref": clean_identifier(summary.get("material_id"), default="p7_r50_body_free_post_review_summary_bodyfree", max_length=180),
        "post_review_summary_builder_status": clean_identifier(summary.get("post_review_summary_builder_status"), default="BLOCKED_BY_R50_13_DISPOSAL_RECEIPT", max_length=120),
        "p5_decision_status": decision_status,
        "p5_decision_reason_refs": dedupe_identifiers(decision_reason_refs, limit=80, max_length=180),
        "p5_confirmed_requirement_refs": list(P7_R50_P5_CONFIRMED_REQUIREMENT_REFS),
        "p5_confirmed_candidate_reason_refs": dedupe_identifiers(confirmed_reason_refs, limit=80, max_length=180),
        "p5_repair_return_reason_refs": dedupe_identifiers(repair_reason_refs, limit=80, max_length=180),
        "p5_inconclusive_reason_refs": dedupe_identifiers(inconclusive_reason_refs, limit=80, max_length=180),
        "required_case_count": P7_R50_REQUIRED_CASE_COUNT,
        "rating_row_count": int(summary.get("rating_row_count") or 0),
        "question_observation_row_count": int(summary.get("question_observation_row_count") or 0),
        "rating_and_question_case_ref_sets_match": summary.get("rating_and_question_case_ref_sets_match") is True,
        "execution_blocker_open_count": int(summary.get("execution_blocker_open_count") or 0),
        "readfeel_blocker_open_count": int(summary.get("readfeel_blocker_open_count") or 0),
        "verdict_counts": dict(safe_mapping(summary.get("verdict_counts"))),
        "axis_score_averages": dict(safe_mapping(summary.get("axis_score_averages"))),
        "axis_target_failed_refs": list(summary.get("axis_target_failed_refs") or []),
        "blocker_counts": dict(safe_mapping(summary.get("blocker_counts"))),
        "question_need_primary_class_counts": dict(safe_mapping(summary.get("question_need_primary_class_counts"))),
        "repair_required_counts": dict(safe_mapping(summary.get("repair_required_counts"))),
        "disposal_status": clean_identifier(summary.get("disposal_status"), default="NOT_GENERATED", max_length=80),
        "body_removed": summary.get("body_removed") is True,
        "reviewer_notes_removed": summary.get("reviewer_notes_removed") is True,
        "local_packet_exported": summary.get("local_packet_exported") is True,
        "content_hash_of_body_stored": summary.get("content_hash_of_body_stored") is True,
        "body_free_summary_ready": summary.get("body_free_summary_ready") is True,
        "p5_human_blind_qa_confirmed": False,
        "p5_human_blind_qa_confirmed_candidate": is_confirmed_candidate,
        "p5_repair_return_candidate": is_repair_return,
        "p5_review_inconclusive": is_inconclusive,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_start_allowed_candidate": False,
        "p8_question_design_material_candidate": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "p7_completion_claim_allowed": False,
        "p8_start_claim_allowed": False,
        "release_readiness_claim_allowed": False,
        "manual_run_decision_made_here": True,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "post_review_decision_materialized_here": False,
        "implemented_steps": list(P7_R50_R15_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R50_R15_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r49_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_prior_validation_evidence_adopted": True,
        "r3_manual_run_decision_built": True,
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built": True,
        "r5_24_case_review_session_protocol_built": True,
        "r6_local_only_body_full_packet_generation_request_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": True,
        "r8_rating_row_normalizer_built": True,
        "r9_readfeel_blocker_execution_blocker_ingestion_built": True,
        "r10_question_need_observation_row_normalizer_built": True,
        "r11_rating_question_observation_consistency_guard_built": True,
        "r12_pause_abort_expiration_protocol_built": True,
        "r13_disposal_receipt_builder_verifier_built": True,
        "r14_body_free_post_review_summary_built": True,
        "r15_p5_confirmed_repair_return_inconclusive_decision_built": True,
        "first_next_work_ref": P7_R50_FIRST_NEXT_WORK_REF,
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "r50_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_for(P7_R50_R15_FALSE_KEY_REFS),
    }
    assert_p7_r50_p5_confirmed_repair_return_inconclusive_decision_bodyfree_contract(decision)
    return decision


def build_p7_r50_p5_review_decision_bodyfree(**kwargs: Any) -> dict[str, Any]:
    """Compatibility alias for the R50-15 P5 review decision."""

    return build_p7_r50_p5_confirmed_repair_return_inconclusive_decision_bodyfree(**kwargs)


def assert_p7_r50_p5_confirmed_repair_return_inconclusive_decision_bodyfree_contract(decision: Mapping[str, Any]) -> bool:
    data = safe_mapping(decision)
    _assert_required_fields(
        data,
        required=P7_R50_P5_CONFIRMED_REPAIR_INCONCLUSIVE_DECISION_BODYFREE_REQUIRED_FIELD_REFS,
        source="p7_r50_p5_confirmed_repair_inconclusive_decision_bodyfree",
    )
    _assert_common_with_false_keys(
        data,
        schema_version=P7_R50_P5_CONFIRMED_REPAIR_INCONCLUSIVE_DECISION_BODYFREE_SCHEMA_VERSION,
        source="p7_r50_p5_confirmed_repair_inconclusive_decision_bodyfree",
        false_keys=P7_R50_R15_FALSE_KEY_REFS,
    )
    if data.get("policy_section") != "R50-15_p5_confirmed_repair_return_inconclusive_decision":
        raise ValueError("R50 R15 policy section changed")
    if data.get("p5_decision_status") not in P7_R50_P5_CONFIRMED_REPAIR_INCONCLUSIVE_DECISION_STATUS_REFS:
        raise ValueError("R50 R15 decision status is not canonical")
    if data.get("p5_human_blind_qa_confirmed") is not False:
        raise ValueError("R50 R15 must not mark actual P5 human blind QA confirmed")
    true_count = sum(1 for key in ("p5_human_blind_qa_confirmed_candidate", "p5_repair_return_candidate", "p5_review_inconclusive") if data.get(key) is True)
    if true_count != 1:
        raise ValueError("R50 R15 must select exactly one candidate/repair/inconclusive outcome")
    if data.get("p5_decision_status") == "P5_CONFIRMED_CANDIDATE":
        if data.get("p5_human_blind_qa_confirmed_candidate") is not True:
            raise ValueError("R50 R15 confirmed decision must set confirmed candidate")
        if data.get("next_required_step") != P7_R50_R15_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R15 confirmed candidate must point to R50-16 candidate handoff")
    elif data.get("p5_decision_status") == "P5_REPAIR_RETURN":
        if data.get("p5_repair_return_candidate") is not True:
            raise ValueError("R50 R15 repair-return decision must set repair candidate")
        if data.get("next_required_step") != P7_R50_R15_REPAIR_RETURN_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R15 repair-return must point back to P5 repair")
    elif data.get("p5_decision_status") == "P5_REVIEW_INCONCLUSIVE":
        if data.get("p5_review_inconclusive") is not True:
            raise ValueError("R50 R15 inconclusive decision must be explicit")
        if data.get("next_required_step") != P7_R50_R15_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R15 inconclusive must point to resolution")
    else:
        if data.get("next_required_step") != P7_R50_R15_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R15 blocked decision must point to R14 resolution")
    for key in ("p6_limited_human_readfeel_start_allowed", "p6_limited_human_readfeel_start_allowed_candidate", "p8_question_design_material_candidate", "p7_complete", "p8_start_allowed", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"R50 R15 must keep {key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R50_R15_IMPLEMENTED_STEPS:
        raise ValueError("R50 R15 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_R15_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R15 not-yet steps changed")
    return True


def build_p7_r50_r14_r15_post_review_decision_freeze(
    *,
    body_free_post_review_summary_bodyfree: Mapping[str, Any] | None = None,
    p5_confirmed_repair_inconclusive_decision_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r50_r14_r15_post_review_decision_freeze",
) -> dict[str, Any]:
    summary = safe_mapping(body_free_post_review_summary_bodyfree) if body_free_post_review_summary_bodyfree is not None else build_p7_r50_body_free_post_review_summary_bodyfree()
    assert_p7_r50_body_free_post_review_summary_bodyfree_contract(summary)
    decision = (
        safe_mapping(p5_confirmed_repair_inconclusive_decision_bodyfree)
        if p5_confirmed_repair_inconclusive_decision_bodyfree is not None
        else build_p7_r50_p5_confirmed_repair_return_inconclusive_decision_bodyfree(post_review_summary_bodyfree=summary)
    )
    assert_p7_r50_p5_confirmed_repair_return_inconclusive_decision_bodyfree_contract(decision)
    freeze = {
        "schema_version": P7_R50_R14_R15_POST_REVIEW_DECISION_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R50_STEP,
        "scope": P7_R50_SCOPE,
        "policy_kind": P7_R50_POLICY_KIND,
        "policy_section": "R50-14_R50-15_post_review_decision_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r50_r14_r15_post_review_decision_freeze", max_length=180),
        "r14_body_free_post_review_summary": summary,
        "r15_p5_confirmed_repair_inconclusive_decision": decision,
        "review_session_id": decision["review_session_id"],
        "post_review_summary_builder_status": summary["post_review_summary_builder_status"],
        "p5_decision_status": decision["p5_decision_status"],
        "p5_human_blind_qa_confirmed_candidate": decision["p5_human_blind_qa_confirmed_candidate"],
        "p5_repair_return_candidate": decision["p5_repair_return_candidate"],
        "p5_review_inconclusive": decision["p5_review_inconclusive"],
        "p6_limited_human_readfeel_start_allowed_candidate": False,
        "p8_question_design_material_candidate": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "manual_run_decision_made_here": True,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "implemented_steps": list(P7_R50_R15_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R50_R15_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r49_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_prior_validation_evidence_adopted": True,
        "r3_manual_run_decision_built": True,
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built": True,
        "r5_24_case_review_session_protocol_built": True,
        "r6_local_only_body_full_packet_generation_request_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": True,
        "r8_rating_row_normalizer_built": True,
        "r9_readfeel_blocker_execution_blocker_ingestion_built": True,
        "r10_question_need_observation_row_normalizer_built": True,
        "r11_rating_question_observation_consistency_guard_built": True,
        "r12_pause_abort_expiration_protocol_built": True,
        "r13_disposal_receipt_builder_verifier_built": True,
        "r14_body_free_post_review_summary_built": True,
        "r15_p5_confirmed_repair_return_inconclusive_decision_built": True,
        "first_next_work_ref": P7_R50_FIRST_NEXT_WORK_REF,
        "next_required_step": decision["next_required_step"],
        "public_contract": public_contract_flags(),
        "r50_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_for(P7_R50_R15_FALSE_KEY_REFS),
    }
    assert_p7_r50_r14_r15_post_review_decision_freeze_contract(freeze)
    return freeze


def assert_p7_r50_r14_r15_post_review_decision_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_required_fields(
        data,
        required=P7_R50_R14_R15_POST_REVIEW_DECISION_FREEZE_REQUIRED_FIELD_REFS,
        source="p7_r50_r14_r15_post_review_decision_freeze",
    )
    _assert_common_with_false_keys(
        data,
        schema_version=P7_R50_R14_R15_POST_REVIEW_DECISION_FREEZE_SCHEMA_VERSION,
        source="p7_r50_r14_r15_post_review_decision_freeze",
        false_keys=P7_R50_R15_FALSE_KEY_REFS,
    )
    summary = safe_mapping(data.get("r14_body_free_post_review_summary"))
    decision = safe_mapping(data.get("r15_p5_confirmed_repair_inconclusive_decision"))
    assert_p7_r50_body_free_post_review_summary_bodyfree_contract(summary)
    assert_p7_r50_p5_confirmed_repair_return_inconclusive_decision_bodyfree_contract(decision)
    if data.get("review_session_id") != decision.get("review_session_id"):
        raise ValueError("R50 R14/R15 freeze review session mismatch")
    if data.get("post_review_summary_builder_status") != summary.get("post_review_summary_builder_status"):
        raise ValueError("R50 R14/R15 freeze summary status mismatch")
    if data.get("p5_decision_status") != decision.get("p5_decision_status"):
        raise ValueError("R50 R14/R15 freeze decision status mismatch")
    if data.get("p5_human_blind_qa_confirmed_candidate") != decision.get("p5_human_blind_qa_confirmed_candidate"):
        raise ValueError("R50 R14/R15 freeze confirmed candidate mismatch")
    if data.get("p5_repair_return_candidate") != decision.get("p5_repair_return_candidate"):
        raise ValueError("R50 R14/R15 freeze repair candidate mismatch")
    if data.get("p5_review_inconclusive") != decision.get("p5_review_inconclusive"):
        raise ValueError("R50 R14/R15 freeze inconclusive mismatch")
    for key in ("p7_complete", "p8_start_allowed", "release_allowed", "p6_limited_human_readfeel_start_allowed_candidate", "p8_question_design_material_candidate"):
        if data.get(key) is not False:
            raise ValueError(f"R50 R14/R15 must keep {key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R50_R15_IMPLEMENTED_STEPS:
        raise ValueError("R50 R14/R15 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_R15_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R14/R15 not-yet steps changed")
    return True

# ---------------------------------------------------------------------------
# R50-16 / R50-17: P6 and P8 body-free candidate handoffs
# ---------------------------------------------------------------------------


def _r50_r14_r15_freeze_for_candidate_handoff(
    value: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    freeze = safe_mapping(value) if value is not None else build_p7_r50_r14_r15_post_review_decision_freeze()
    assert_p7_r50_r14_r15_post_review_decision_freeze_contract(freeze)
    return dict(freeze)


def _p6_candidate_missing_requirement_refs_r50(
    decision: Mapping[str, Any],
) -> list[str]:
    missing: list[str] = []
    axis_failed = dedupe_identifiers(decision.get("axis_target_failed_refs"), limit=20, max_length=120)
    if decision.get("p5_human_blind_qa_confirmed_candidate") is not True:
        missing.append("p5_confirmed_candidate_true")
    if decision.get("p5_repair_return_candidate") is True:
        missing.append("p5_repair_return_false")
    if decision.get("p5_review_inconclusive") is True:
        missing.append("p5_review_inconclusive_false")
    if decision.get("p5_decision_status") != "P5_CONFIRMED_CANDIDATE":
        missing.append("p5_unresolved_material_not_hidden_by_p6")
    if decision.get("disposal_status") != "DISPOSAL_VERIFIED":
        missing.append("disposal_verified_for_candidate")
    if decision.get("body_removed") is not True:
        missing.append("body_removed_true")
    if decision.get("reviewer_notes_removed") is not True:
        missing.append("reviewer_notes_removed_true")
    if decision.get("local_packet_exported") is not False:
        missing.append("local_packet_not_exported")
    if decision.get("content_hash_of_body_stored") is not False:
        missing.append("content_hash_not_stored")
    if int(decision.get("execution_blocker_open_count") or 0) != 0:
        missing.append("execution_blocker_open_count_zero")
    if int(decision.get("readfeel_blocker_open_count") or 0) != 0:
        missing.append("readfeel_blocker_open_count_zero")
    if axis_failed:
        missing.append("axis_targets_met")
    return [ref for ref in P7_R50_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_REQUIRED_CONDITION_REFS if ref in set(missing)]


def build_p7_r50_p6_limited_human_readfeel_candidate_handoff_bodyfree(
    *,
    r14_r15_post_review_decision_freeze: Mapping[str, Any] | None = None,
    post_review_decision_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r50_p6_limited_human_readfeel_candidate_handoff_bodyfree",
) -> dict[str, Any]:
    """Build the R50-16 P6 limited readfeel candidate handoff without starting P6."""

    supplied = [r14_r15_post_review_decision_freeze is not None, post_review_decision_freeze is not None]
    if sum(supplied) > 1:
        raise ValueError("provide only one R50 R14/R15 post-review decision freeze")
    freeze = _r50_r14_r15_freeze_for_candidate_handoff(
        r14_r15_post_review_decision_freeze if r14_r15_post_review_decision_freeze is not None else post_review_decision_freeze
    )
    decision = safe_mapping(freeze.get("r15_p5_confirmed_repair_inconclusive_decision"))
    summary = safe_mapping(freeze.get("r14_body_free_post_review_summary"))
    assert_p7_r50_p5_confirmed_repair_return_inconclusive_decision_bodyfree_contract(decision)
    assert_p7_r50_body_free_post_review_summary_bodyfree_contract(summary)

    missing = _p6_candidate_missing_requirement_refs_r50(decision)
    candidate = not missing
    status = (
        "P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_READY"
        if candidate
        else "BLOCKED_BY_R50_15_P5_DECISION"
        if decision.get("p5_decision_status") != "P5_CONFIRMED_CANDIDATE"
        else "P6_LIMITED_HUMAN_READFEEL_NOT_CANDIDATE"
    )
    handoff = {
        "schema_version": P7_R50_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_BODYFREE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R50_STEP,
        "scope": P7_R50_SCOPE,
        "policy_kind": P7_R50_POLICY_KIND,
        "policy_section": "R50-16_p6_limited_human_readfeel_candidate_handoff",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r50_p6_limited_human_readfeel_candidate_handoff_bodyfree", max_length=180),
        "review_session_id": clean_identifier(decision.get("review_session_id"), default=P7_R50_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_kind": P7_R50_REVIEW_KIND,
        "packet_kind": P7_R50_PACKET_KIND,
        "r14_r15_post_review_decision_freeze_schema_version": P7_R50_R14_R15_POST_REVIEW_DECISION_FREEZE_SCHEMA_VERSION,
        "r14_r15_post_review_decision_freeze_ref": clean_identifier(freeze.get("material_id"), default="p7_r50_r14_r15_post_review_decision_freeze", max_length=180),
        "r14_r15_post_review_decision_freeze": freeze,
        "r49_p6_handoff_schema_version_ref": P7_R49_P6_LIMITED_HUMAN_READFEEL_START_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        "p6_candidate_handoff_status": status,
        "p6_candidate_required_condition_refs": list(P7_R50_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_REQUIRED_CONDITION_REFS),
        "p6_candidate_missing_requirement_refs": missing,
        "p6_candidate_failed_requirement_count": len(missing),
        "p5_decision_status": clean_identifier(decision.get("p5_decision_status"), default="P5_REVIEW_INCONCLUSIVE", max_length=120),
        "p5_human_blind_qa_confirmed_candidate": decision.get("p5_human_blind_qa_confirmed_candidate") is True,
        "p5_repair_return_candidate": decision.get("p5_repair_return_candidate") is True,
        "p5_review_inconclusive": decision.get("p5_review_inconclusive") is True,
        "p5_unresolved_material_not_hidden_by_p6": candidate,
        "p6_limited_human_readfeel_start_candidate_handoff_ready": candidate,
        "p6_limited_human_readfeel_start_allowed_candidate": candidate,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "disposal_status": clean_identifier(decision.get("disposal_status"), default="NOT_GENERATED", max_length=80),
        "body_removed": decision.get("body_removed") is True,
        "reviewer_notes_removed": decision.get("reviewer_notes_removed") is True,
        "local_packet_exported": decision.get("local_packet_exported") is True,
        "content_hash_of_body_stored": decision.get("content_hash_of_body_stored") is True,
        "rating_row_count": int(decision.get("rating_row_count") or 0),
        "question_observation_row_count": int(decision.get("question_observation_row_count") or 0),
        "rating_and_question_case_ref_sets_match": decision.get("rating_and_question_case_ref_sets_match") is True,
        "execution_blocker_open_count": int(decision.get("execution_blocker_open_count") or 0),
        "readfeel_blocker_open_count": int(decision.get("readfeel_blocker_open_count") or 0),
        "axis_target_failed_refs": dedupe_identifiers(decision.get("axis_target_failed_refs"), limit=20, max_length=120),
        "p8_question_design_material_candidate": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "p6_start_permission_granted_here": False,
        "actual_p6_handoff_materialized_here": False,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "implemented_steps": list(P7_R50_R16_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R50_R16_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r49_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_prior_validation_evidence_adopted": True,
        "r3_manual_run_decision_built": True,
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built": True,
        "r5_24_case_review_session_protocol_built": True,
        "r6_local_only_body_full_packet_generation_request_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": True,
        "r8_rating_row_normalizer_built": True,
        "r9_readfeel_blocker_execution_blocker_ingestion_built": True,
        "r10_question_need_observation_row_normalizer_built": True,
        "r11_rating_question_observation_consistency_guard_built": True,
        "r12_pause_abort_expiration_protocol_built": True,
        "r13_disposal_receipt_builder_verifier_built": True,
        "r14_body_free_post_review_summary_built": True,
        "r15_p5_confirmed_repair_return_inconclusive_decision_built": True,
        "r16_p6_limited_human_readfeel_candidate_handoff_built": True,
        "first_next_work_ref": P7_R50_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R50_R16_NEXT_REQUIRED_STEP_REF if candidate else P7_R50_R16_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r50_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_for(P7_R50_R16_FALSE_KEY_REFS),
    }
    assert_p7_r50_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract(handoff)
    return handoff


def build_p7_r50_p6_limited_human_readfeel_candidate_handoff(**kwargs: Any) -> dict[str, Any]:
    """Compatibility alias for the R50-16 P6 candidate handoff."""

    return build_p7_r50_p6_limited_human_readfeel_candidate_handoff_bodyfree(**kwargs)


def assert_p7_r50_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract(handoff: Mapping[str, Any]) -> bool:
    data = safe_mapping(handoff)
    _assert_required_fields(
        data,
        required=P7_R50_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_BODYFREE_REQUIRED_FIELD_REFS,
        source="p7_r50_p6_limited_human_readfeel_candidate_handoff_bodyfree",
    )
    _assert_common_with_false_keys(
        data,
        schema_version=P7_R50_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_BODYFREE_SCHEMA_VERSION,
        source="p7_r50_p6_limited_human_readfeel_candidate_handoff_bodyfree",
        false_keys=P7_R50_R16_FALSE_KEY_REFS,
    )
    if data.get("policy_section") != "R50-16_p6_limited_human_readfeel_candidate_handoff":
        raise ValueError("R50 R16 policy section changed")
    if data.get("p6_candidate_handoff_status") not in P7_R50_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_STATUS_REFS:
        raise ValueError("R50 R16 handoff status is not canonical")
    freeze = safe_mapping(data.get("r14_r15_post_review_decision_freeze"))
    decision = safe_mapping(freeze.get("r15_p5_confirmed_repair_inconclusive_decision"))
    assert_p7_r50_r14_r15_post_review_decision_freeze_contract(freeze)
    missing = _p6_candidate_missing_requirement_refs_r50(decision)
    if data.get("p6_candidate_missing_requirement_refs") != missing:
        raise ValueError("R50 R16 P6 candidate missing requirement refs mismatch")
    if data.get("p6_candidate_failed_requirement_count") != len(missing):
        raise ValueError("R50 R16 P6 candidate failed requirement count mismatch")
    candidate = not missing
    if data.get("p6_limited_human_readfeel_start_allowed_candidate") is not candidate:
        raise ValueError("R50 R16 P6 candidate flag mismatch")
    if data.get("p6_limited_human_readfeel_start_allowed") is not False or data.get("p6_start_permission_granted_here") is not False:
        raise ValueError("R50 R16 must not start P6")
    if data.get("p8_question_design_material_candidate") is not False:
        raise ValueError("R50 R16 must not decide P8 material candidate")
    expected_next = P7_R50_R16_NEXT_REQUIRED_STEP_REF if candidate else P7_R50_R16_BLOCKED_NEXT_REQUIRED_STEP_REF
    if data.get("next_required_step") != expected_next:
        raise ValueError("R50 R16 next step mismatch")
    if tuple(data.get("implemented_steps") or ()) != P7_R50_R16_IMPLEMENTED_STEPS:
        raise ValueError("R50 R16 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_R16_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R16 not-yet steps changed")
    return True


def _not_question_repair_required_count_r50(primary_counts: Mapping[str, Any]) -> int:
    return sum(int(primary_counts.get(ref) or 0) for ref in P7_R50_REPAIR_RETURN_QUESTION_PRIMARY_CLASS_REFS)


def _r50_p8_design_material_missing_requirement_refs(summary: Mapping[str, Any], p6_handoff: Mapping[str, Any]) -> list[str]:
    primary_counts = safe_mapping(summary.get("question_need_primary_class_counts"))
    ambiguity_counts = safe_mapping(summary.get("ambiguity_kind_counts"))
    one_question_fit_counts = safe_mapping(summary.get("one_question_fit_counts"))
    repair_counts = safe_mapping(summary.get("repair_required_counts"))
    missing: list[str] = []
    if int(summary.get("question_observation_row_count") or 0) != P7_R50_REQUIRED_CASE_COUNT:
        missing.append("question_observation_rows_24_complete")
    for counts, canonical_refs, ref in (
        (primary_counts, P7_R50_QUESTION_NEED_PRIMARY_CLASS_REFS, "primary_class_counts_present"),
        (ambiguity_counts, P7_R50_AMBIGUITY_KIND_REFS, "ambiguity_kind_counts_present"),
        (one_question_fit_counts, P7_R50_ONE_QUESTION_FIT_REFS, "one_question_fit_counts_present"),
        (repair_counts, P7_R50_REPAIR_REQUIRED_REF_REFS, "repair_required_counts_present"),
    ):
        if set(counts) != set(canonical_refs):
            missing.append(ref)
    if _not_question_repair_required_count_r50(primary_counts) > 0:
        missing.append("repair_required_not_question_not_misclassified_as_p8")
    if p6_handoff.get("p5_repair_return_candidate") is True or p6_handoff.get("p5_review_inconclusive") is True:
        missing.append("p5_repair_return_not_mixed_into_p8_material")
    if p6_handoff.get("p8_start_allowed") is not False:
        missing.append("p8_start_allowed_false")
    # These are explicit body-free invariants for the R50 handoff; they must remain absent.
    absent_guard_refs = (
        "question_text_absent",
        "draft_question_text_absent",
        "reviewer_free_text_absent",
        "raw_input_or_comment_text_absent",
        "returned_surface_absent",
        "local_path_or_body_hash_absent",
        "question_implementation_not_started",
    )
    # The builder fixes all absence flags to false/absent. Contract tampering is checked separately.
    return [ref for ref in P7_R50_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_REQUIREMENT_REFS if ref in set(missing)]


def build_p7_r50_p8_question_design_material_candidate_handoff_bodyfree(
    *,
    p6_limited_human_readfeel_candidate_handoff_bodyfree: Mapping[str, Any] | None = None,
    p6_candidate_handoff_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r50_p8_question_design_material_candidate_handoff_bodyfree",
) -> dict[str, Any]:
    """Build the R50-17 P8 question-design material candidate handoff without starting P8."""

    supplied = [p6_limited_human_readfeel_candidate_handoff_bodyfree is not None, p6_candidate_handoff_bodyfree is not None]
    if sum(supplied) > 1:
        raise ValueError("provide only one R50 R16 P6 candidate handoff value")
    p6 = safe_mapping(
        p6_limited_human_readfeel_candidate_handoff_bodyfree
        if p6_limited_human_readfeel_candidate_handoff_bodyfree is not None
        else p6_candidate_handoff_bodyfree
        if p6_candidate_handoff_bodyfree is not None
        else build_p7_r50_p6_limited_human_readfeel_candidate_handoff_bodyfree()
    )
    assert_p7_r50_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract(p6)
    freeze = safe_mapping(p6.get("r14_r15_post_review_decision_freeze"))
    summary = safe_mapping(freeze.get("r14_body_free_post_review_summary"))
    assert_p7_r50_body_free_post_review_summary_bodyfree_contract(summary)

    primary_counts = dict(safe_mapping(summary.get("question_need_primary_class_counts")))
    ambiguity_counts = dict(safe_mapping(summary.get("ambiguity_kind_counts")))
    one_question_fit_counts = dict(safe_mapping(summary.get("one_question_fit_counts")))
    repair_counts = dict(safe_mapping(summary.get("repair_required_counts")))
    missing = _r50_p8_design_material_missing_requirement_refs(summary, p6)
    blocked_by_r16 = p6.get("p6_candidate_handoff_status") == "BLOCKED_BY_R50_15_P5_DECISION"
    candidate = (not missing) and not blocked_by_r16
    status = (
        "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_READY"
        if candidate
        else "BLOCKED_BY_R50_16_P6_HANDOFF"
        if blocked_by_r16
        else "P8_QUESTION_DESIGN_MATERIAL_NOT_CANDIDATE"
    )
    not_question_repair_count = _not_question_repair_required_count_r50(primary_counts)
    handoff = {
        "schema_version": P7_R50_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_BODYFREE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R50_STEP,
        "scope": P7_R50_SCOPE,
        "policy_kind": P7_R50_POLICY_KIND,
        "policy_section": "R50-17_p8_question_design_material_candidate_handoff",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r50_p8_question_design_material_candidate_handoff_bodyfree", max_length=180),
        "review_session_id": clean_identifier(p6.get("review_session_id"), default=P7_R50_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_kind": P7_R50_REVIEW_KIND,
        "packet_kind": P7_R50_PACKET_KIND,
        "r16_p6_handoff_schema_version": P7_R50_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_BODYFREE_SCHEMA_VERSION,
        "r16_p6_handoff_ref": clean_identifier(p6.get("material_id"), default="p7_r50_p6_limited_human_readfeel_candidate_handoff_bodyfree", max_length=180),
        "r16_p6_limited_human_readfeel_candidate_handoff": p6,
        "r49_p8_handoff_schema_version_ref": P7_R49_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        "p8_candidate_handoff_status": status,
        "p8_design_material_candidate_requirement_refs": list(P7_R50_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_REQUIREMENT_REFS),
        "p8_design_material_candidate_missing_requirement_refs": missing,
        "p8_design_material_candidate_failed_requirement_count": len(missing),
        "p8_design_material_bodyfree": True,
        "total_case_count": int(summary.get("case_count") or 0),
        "question_observation_row_count": int(summary.get("question_observation_row_count") or 0),
        "question_observation_rows_complete": int(summary.get("question_observation_row_count") or 0) == P7_R50_REQUIRED_CASE_COUNT,
        "no_question_needed_count": int(primary_counts.get("no_question_needed_emlis_can_observe") or 0),
        "question_may_reduce_overread_risk_count": int(primary_counts.get("question_may_reduce_overread_risk") or 0),
        "question_would_make_immediate_observation_heavy_count": int(primary_counts.get("question_would_make_immediate_observation_heavy") or 0),
        "not_question_repair_required_count": not_question_repair_count,
        "emlis_readfeel_repair_required_count": int(primary_counts.get("not_question_emlis_readfeel_repair_required") or 0),
        "p5_surface_repair_required_count": int(primary_counts.get("not_question_p5_surface_repair_required") or 0),
        "gate_boundary_repair_required_count": int(primary_counts.get("not_question_gate_boundary_required") or 0),
        "plus_single_question_candidate_later_count": int(primary_counts.get("plus_single_question_candidate_later") or 0),
        "premium_deep_dive_candidate_later_count": int(primary_counts.get("premium_deep_dive_candidate_later") or 0),
        "primary_class_counts": primary_counts,
        "ambiguity_kind_counts": ambiguity_counts,
        "one_question_fit_counts": one_question_fit_counts,
        "repair_required_counts": repair_counts,
        "p5_decision_status": clean_identifier(p6.get("p5_decision_status"), default="P5_REVIEW_INCONCLUSIVE", max_length=120),
        "p5_human_blind_qa_confirmed_candidate": p6.get("p5_human_blind_qa_confirmed_candidate") is True,
        "p5_repair_return_candidate": p6.get("p5_repair_return_candidate") is True,
        "p5_review_inconclusive": p6.get("p5_review_inconclusive") is True,
        "p6_limited_human_readfeel_start_allowed_candidate": p6.get("p6_limited_human_readfeel_start_allowed_candidate") is True,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "p8_question_design_material_candidate": candidate,
        "question_text_included": False,
        "draft_question_text_included": False,
        "reviewer_free_text_included": False,
        "raw_input_or_comment_text_included": False,
        "returned_surface_included": False,
        "local_path_or_body_hash_included": False,
        "question_trigger_logic_implemented_here": False,
        "api_db_rn_response_key_changed_here": False,
        "p8_detail_design_allowed_here": False,
        "p8_implementation_spec_finalized_here": False,
        "actual_p8_design_material_handoff_materialized_here": False,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "implemented_steps": list(P7_R50_R17_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R50_R17_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r49_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_prior_validation_evidence_adopted": True,
        "r3_manual_run_decision_built": True,
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built": True,
        "r5_24_case_review_session_protocol_built": True,
        "r6_local_only_body_full_packet_generation_request_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": True,
        "r8_rating_row_normalizer_built": True,
        "r9_readfeel_blocker_execution_blocker_ingestion_built": True,
        "r10_question_need_observation_row_normalizer_built": True,
        "r11_rating_question_observation_consistency_guard_built": True,
        "r12_pause_abort_expiration_protocol_built": True,
        "r13_disposal_receipt_builder_verifier_built": True,
        "r14_body_free_post_review_summary_built": True,
        "r15_p5_confirmed_repair_return_inconclusive_decision_built": True,
        "r16_p6_limited_human_readfeel_candidate_handoff_built": True,
        "r17_p8_question_design_material_candidate_handoff_built": True,
        "first_next_work_ref": P7_R50_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R50_R17_BLOCKED_NEXT_REQUIRED_STEP_REF if blocked_by_r16 else P7_R50_R17_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r50_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_for(P7_R50_R17_FALSE_KEY_REFS),
    }
    assert_p7_r50_p8_question_design_material_candidate_handoff_bodyfree_contract(handoff)
    return handoff


def build_p7_r50_p8_question_design_material_candidate_handoff(**kwargs: Any) -> dict[str, Any]:
    """Compatibility alias for the R50-17 P8 material candidate handoff."""

    return build_p7_r50_p8_question_design_material_candidate_handoff_bodyfree(**kwargs)


def assert_p7_r50_p8_question_design_material_candidate_handoff_bodyfree_contract(handoff: Mapping[str, Any]) -> bool:
    data = safe_mapping(handoff)
    _assert_required_fields(
        data,
        required=P7_R50_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_BODYFREE_REQUIRED_FIELD_REFS,
        source="p7_r50_p8_question_design_material_candidate_handoff_bodyfree",
    )
    _assert_common_with_false_keys(
        data,
        schema_version=P7_R50_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_BODYFREE_SCHEMA_VERSION,
        source="p7_r50_p8_question_design_material_candidate_handoff_bodyfree",
        false_keys=P7_R50_R17_FALSE_KEY_REFS,
    )
    if data.get("policy_section") != "R50-17_p8_question_design_material_candidate_handoff":
        raise ValueError("R50 R17 policy section changed")
    if data.get("p8_candidate_handoff_status") not in P7_R50_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_STATUS_REFS:
        raise ValueError("R50 R17 handoff status is not canonical")
    p6 = safe_mapping(data.get("r16_p6_limited_human_readfeel_candidate_handoff"))
    assert_p7_r50_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract(p6)
    freeze = safe_mapping(p6.get("r14_r15_post_review_decision_freeze"))
    summary = safe_mapping(freeze.get("r14_body_free_post_review_summary"))
    missing = _r50_p8_design_material_missing_requirement_refs(summary, p6)
    if data.get("p8_design_material_candidate_missing_requirement_refs") != missing:
        raise ValueError("R50 R17 P8 material missing requirement refs mismatch")
    if data.get("p8_design_material_candidate_failed_requirement_count") != len(missing):
        raise ValueError("R50 R17 P8 material failed requirement count mismatch")
    primary_counts = safe_mapping(data.get("primary_class_counts"))
    if set(primary_counts) != set(P7_R50_QUESTION_NEED_PRIMARY_CLASS_REFS):
        raise ValueError("R50 R17 primary class counts must preserve canonical refs")
    if data.get("not_question_repair_required_count") != _not_question_repair_required_count_r50(primary_counts):
        raise ValueError("R50 R17 not-question repair count mismatch")
    for counts_key, canonical_refs in (
        ("ambiguity_kind_counts", P7_R50_AMBIGUITY_KIND_REFS),
        ("one_question_fit_counts", P7_R50_ONE_QUESTION_FIT_REFS),
        ("repair_required_counts", P7_R50_REPAIR_REQUIRED_REF_REFS),
    ):
        if set(safe_mapping(data.get(counts_key))) != set(canonical_refs):
            raise ValueError(f"R50 R17 {counts_key} must preserve canonical refs")
    for key in (
        "question_text_included",
        "draft_question_text_included",
        "reviewer_free_text_included",
        "raw_input_or_comment_text_included",
        "returned_surface_included",
        "local_path_or_body_hash_included",
        "question_trigger_logic_implemented_here",
        "api_db_rn_response_key_changed_here",
        "p8_detail_design_allowed_here",
        "p8_implementation_spec_finalized_here",
        "p8_start_allowed",
        "p6_limited_human_readfeel_start_allowed",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"R50 R17 must keep {key}=False")
    candidate = (not missing) and data.get("p8_candidate_handoff_status") != "BLOCKED_BY_R50_16_P6_HANDOFF"
    if data.get("p8_question_design_material_candidate") is not candidate:
        raise ValueError("R50 R17 P8 candidate flag mismatch")
    expected_next = P7_R50_R17_BLOCKED_NEXT_REQUIRED_STEP_REF if data.get("p8_candidate_handoff_status") == "BLOCKED_BY_R50_16_P6_HANDOFF" else P7_R50_R17_NEXT_REQUIRED_STEP_REF
    if data.get("next_required_step") != expected_next:
        raise ValueError("R50 R17 next step mismatch")
    if tuple(data.get("implemented_steps") or ()) != P7_R50_R17_IMPLEMENTED_STEPS:
        raise ValueError("R50 R17 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_R17_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R17 not-yet steps changed")
    return True


def build_p7_r50_r16_r17_p6_p8_candidate_handoff_freeze(
    *,
    p6_limited_human_readfeel_candidate_handoff_bodyfree: Mapping[str, Any] | None = None,
    p8_question_design_material_candidate_handoff_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r50_r16_r17_p6_p8_candidate_handoff_freeze",
) -> dict[str, Any]:
    p6 = (
        safe_mapping(p6_limited_human_readfeel_candidate_handoff_bodyfree)
        if p6_limited_human_readfeel_candidate_handoff_bodyfree is not None
        else build_p7_r50_p6_limited_human_readfeel_candidate_handoff_bodyfree()
    )
    assert_p7_r50_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract(p6)
    p8 = (
        safe_mapping(p8_question_design_material_candidate_handoff_bodyfree)
        if p8_question_design_material_candidate_handoff_bodyfree is not None
        else build_p7_r50_p8_question_design_material_candidate_handoff_bodyfree(p6_limited_human_readfeel_candidate_handoff_bodyfree=p6)
    )
    assert_p7_r50_p8_question_design_material_candidate_handoff_bodyfree_contract(p8)
    freeze = {
        "schema_version": P7_R50_R16_R17_P6_P8_CANDIDATE_HANDOFF_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R50_STEP,
        "scope": P7_R50_SCOPE,
        "policy_kind": P7_R50_POLICY_KIND,
        "policy_section": "R50-16_R50-17_p6_p8_candidate_handoff_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r50_r16_r17_p6_p8_candidate_handoff_freeze", max_length=180),
        "r16_p6_limited_human_readfeel_candidate_handoff": p6,
        "r17_p8_question_design_material_candidate_handoff": p8,
        "review_session_id": p8["review_session_id"],
        "p6_candidate_handoff_status": p6["p6_candidate_handoff_status"],
        "p8_candidate_handoff_status": p8["p8_candidate_handoff_status"],
        "p6_limited_human_readfeel_start_allowed_candidate": p6["p6_limited_human_readfeel_start_allowed_candidate"],
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_question_design_material_candidate": p8["p8_question_design_material_candidate"],
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "manual_run_decision_made_here": True,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "implemented_steps": list(P7_R50_R17_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R50_R17_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r49_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_prior_validation_evidence_adopted": True,
        "r3_manual_run_decision_built": True,
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built": True,
        "r5_24_case_review_session_protocol_built": True,
        "r6_local_only_body_full_packet_generation_request_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": True,
        "r8_rating_row_normalizer_built": True,
        "r9_readfeel_blocker_execution_blocker_ingestion_built": True,
        "r10_question_need_observation_row_normalizer_built": True,
        "r11_rating_question_observation_consistency_guard_built": True,
        "r12_pause_abort_expiration_protocol_built": True,
        "r13_disposal_receipt_builder_verifier_built": True,
        "r14_body_free_post_review_summary_built": True,
        "r15_p5_confirmed_repair_return_inconclusive_decision_built": True,
        "r16_p6_limited_human_readfeel_candidate_handoff_built": True,
        "r17_p8_question_design_material_candidate_handoff_built": True,
        "first_next_work_ref": P7_R50_FIRST_NEXT_WORK_REF,
        "next_required_step": p8["next_required_step"],
        "public_contract": public_contract_flags(),
        "r50_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_for(P7_R50_R17_FALSE_KEY_REFS),
    }
    assert_p7_r50_r16_r17_p6_p8_candidate_handoff_freeze_contract(freeze)
    return freeze


def assert_p7_r50_r16_r17_p6_p8_candidate_handoff_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_required_fields(
        data,
        required=P7_R50_R16_R17_P6_P8_CANDIDATE_HANDOFF_FREEZE_REQUIRED_FIELD_REFS,
        source="p7_r50_r16_r17_p6_p8_candidate_handoff_freeze",
    )
    _assert_common_with_false_keys(
        data,
        schema_version=P7_R50_R16_R17_P6_P8_CANDIDATE_HANDOFF_FREEZE_SCHEMA_VERSION,
        source="p7_r50_r16_r17_p6_p8_candidate_handoff_freeze",
        false_keys=P7_R50_R17_FALSE_KEY_REFS,
    )
    p6 = safe_mapping(data.get("r16_p6_limited_human_readfeel_candidate_handoff"))
    p8 = safe_mapping(data.get("r17_p8_question_design_material_candidate_handoff"))
    assert_p7_r50_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract(p6)
    assert_p7_r50_p8_question_design_material_candidate_handoff_bodyfree_contract(p8)
    if data.get("review_session_id") != p8.get("review_session_id"):
        raise ValueError("R50 R16/R17 freeze review session mismatch")
    if data.get("p6_limited_human_readfeel_start_allowed") is not False or data.get("p8_start_allowed") is not False:
        raise ValueError("R50 R16/R17 freeze must not start P6/P8")
    if data.get("p6_limited_human_readfeel_start_allowed_candidate") != p6.get("p6_limited_human_readfeel_start_allowed_candidate"):
        raise ValueError("R50 R16/R17 P6 candidate mismatch")
    if data.get("p8_question_design_material_candidate") != p8.get("p8_question_design_material_candidate"):
        raise ValueError("R50 R16/R17 P8 candidate mismatch")
    if tuple(data.get("implemented_steps") or ()) != P7_R50_R17_IMPLEMENTED_STEPS:
        raise ValueError("R50 R16/R17 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_R17_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R16/R17 not-yet steps changed")
    return True

# ---------------------------------------------------------------------------
# R50-18 / R50-19: no-leak guard and validation command matrix
# ---------------------------------------------------------------------------


def _collect_r50_forbidden_key_refs(value: Any, forbidden_refs: set[str]) -> list[str]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_ref = str(key)
            if key_ref in forbidden_refs:
                found.append(key_ref)
            found.extend(_collect_r50_forbidden_key_refs(child, forbidden_refs))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child in value:
            found.extend(_collect_r50_forbidden_key_refs(child, forbidden_refs))
    return dedupe_identifiers(found, limit=120, max_length=180)


def _collect_r50_forbidden_true_flag_refs(value: Any, flag_refs: set[str]) -> list[str]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_ref = str(key)
            if key_ref in flag_refs and child is True:
                found.append(key_ref)
            found.extend(_collect_r50_forbidden_true_flag_refs(child, flag_refs))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child in value:
            found.extend(_collect_r50_forbidden_true_flag_refs(child, flag_refs))
    return dedupe_identifiers(found, limit=120, max_length=180)


def _r50_detected_intersects(detected: Sequence[str], refs: Sequence[str]) -> bool:
    return bool(set(detected) & set(refs))


def _r50_raw_surface_field_refs() -> tuple[str, ...]:
    return (
        "raw_input",
        "raw_answer",
        "comment_text",
        "comment_text_body",
        "returned_emlis_surface",
        "bounded_owned_history_review_surface",
        "current_input_review_surface",
    )


def _r50_no_leak_scan_reason_refs(
    *,
    body_free_present: bool,
    forbidden_field_refs_detected: Sequence[str],
    forbidden_true_flag_refs_detected: Sequence[str],
    source_contract_invalid: bool,
) -> list[str]:
    reasons: list[str] = []
    if not body_free_present:
        reasons.append("body_free_flag_missing_or_false")
    if forbidden_field_refs_detected:
        reasons.append("forbidden_body_free_field_ref_detected")
    if forbidden_true_flag_refs_detected:
        reasons.append("forbidden_true_flag_detected")
    if source_contract_invalid:
        reasons.append("r16_r17_source_contract_invalid")
    if not reasons:
        reasons.append("body_free_material_passed_no_leak_no_question_text_guard")
    return reasons


def build_p7_r50_no_body_leak_no_question_text_guard_bodyfree(
    *,
    r16_r17_p6_p8_candidate_handoff_freeze: Mapping[str, Any] | None = None,
    source_material_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r50_no_body_leak_no_question_text_guard_bodyfree",
) -> dict[str, Any]:
    """Build the R50-18 no-body-leak/no-question-text guard.

    The scanned material is intentionally not copied into this guard artifact.
    If a caller supplies a leaky material, the guard reports body-free blocker
    refs instead of embedding the leaky payload in the body-free result.
    """

    supplied = [r16_r17_p6_p8_candidate_handoff_freeze is not None, source_material_bodyfree is not None]
    if sum(supplied) > 1:
        raise ValueError("provide only one R50 source material for the no-leak guard")
    if r16_r17_p6_p8_candidate_handoff_freeze is not None:
        source = safe_mapping(r16_r17_p6_p8_candidate_handoff_freeze)
    elif source_material_bodyfree is not None:
        source = safe_mapping(source_material_bodyfree)
    else:
        source = build_p7_r50_r16_r17_p6_p8_candidate_handoff_freeze()

    forbidden_field_refs_detected = _collect_r50_forbidden_key_refs(
        source,
        set(P7_R50_BODY_FREE_FORBIDDEN_FIELD_REFS),
    )
    forbidden_true_flag_refs_detected = _collect_r50_forbidden_true_flag_refs(
        source,
        set(P7_R50_NO_BODY_LEAK_TRUE_FLAG_REFS),
    )
    body_free_present = source.get("body_free") is True
    source_contract_checked = False
    source_contract_invalid = False
    if body_free_present and not forbidden_field_refs_detected and not forbidden_true_flag_refs_detected:
        try:
            assert_p7_r50_r16_r17_p6_p8_candidate_handoff_freeze_contract(source)
            source_contract_checked = True
        except ValueError:
            source_contract_invalid = True

    question_text_detected = _r50_detected_intersects(forbidden_field_refs_detected, P7_R50_QUESTION_TEXT_FIELD_REFS) or _r50_detected_intersects(
        forbidden_true_flag_refs_detected,
        ("question_text_included", "draft_question_text_included"),
    )
    reviewer_free_text_detected = _r50_detected_intersects(forbidden_field_refs_detected, P7_R50_REVIEWER_FREE_TEXT_FIELD_REFS) or _r50_detected_intersects(
        forbidden_true_flag_refs_detected,
        ("reviewer_free_text_included",),
    )
    local_path_or_body_hash_detected = _r50_detected_intersects(forbidden_field_refs_detected, P7_R50_LOCAL_PATH_HASH_FIELD_REFS) or _r50_detected_intersects(
        forbidden_true_flag_refs_detected,
        ("local_path_or_body_hash_included", "content_hash_of_body_stored", "local_packet_exported"),
    )
    terminal_output_detected = _r50_detected_intersects(forbidden_field_refs_detected, P7_R50_TERMINAL_OUTPUT_FIELD_REFS) or _r50_detected_intersects(
        forbidden_true_flag_refs_detected,
        ("terminal_output_included",),
    )
    raw_input_or_comment_text_detected = _r50_detected_intersects(forbidden_field_refs_detected, _r50_raw_surface_field_refs()) or _r50_detected_intersects(
        forbidden_true_flag_refs_detected,
        ("raw_input_included", "comment_text_body_included", "returned_surface_included"),
    )
    question_implementation_started = _r50_detected_intersects(
        forbidden_true_flag_refs_detected,
        (
            "question_trigger_logic_implemented_here",
            "p8_implementation_spec_finalized_here",
            "p8_detail_design_allowed_here",
            "api_db_rn_response_key_changed_here",
        ),
    )
    ready = (
        body_free_present
        and source_contract_checked
        and not source_contract_invalid
        and not forbidden_field_refs_detected
        and not forbidden_true_flag_refs_detected
    )
    status = "NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_READY" if ready else "BLOCKED_BY_BODY_FREE_LEAK_OR_QUESTION_TEXT"
    if source_contract_invalid:
        status = "BLOCKED_BY_R50_17_P8_HANDOFF"
    reason_refs = _r50_no_leak_scan_reason_refs(
        body_free_present=body_free_present,
        forbidden_field_refs_detected=forbidden_field_refs_detected,
        forbidden_true_flag_refs_detected=forbidden_true_flag_refs_detected,
        source_contract_invalid=source_contract_invalid,
    )
    guard = {
        "schema_version": P7_R50_NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_BODYFREE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R50_STEP,
        "scope": P7_R50_SCOPE,
        "policy_kind": P7_R50_POLICY_KIND,
        "policy_section": "R50-18_no_body_leak_no_question_text_guard",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r50_no_body_leak_no_question_text_guard_bodyfree", max_length=180),
        "review_session_id": clean_identifier(source.get("review_session_id"), default=P7_R50_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "r16_r17_p6_p8_candidate_handoff_freeze_schema_version": P7_R50_R16_R17_P6_P8_CANDIDATE_HANDOFF_FREEZE_SCHEMA_VERSION,
        "r16_r17_p6_p8_candidate_handoff_freeze_ref": clean_identifier(source.get("material_id"), default="p7_r50_r16_r17_p6_p8_candidate_handoff_freeze", max_length=180),
        "source_material_schema_version_ref": clean_identifier(source.get("schema_version"), default="unknown_schema_version", max_length=180),
        "source_material_policy_section_ref": clean_identifier(source.get("policy_section"), default="unknown_policy_section", max_length=180),
        "source_material_contract_checked": source_contract_checked,
        "source_material_embedded_here": False,
        "guard_status": status,
        "guard_reason_refs": reason_refs,
        "required_case_count": P7_R50_REQUIRED_CASE_COUNT,
        "body_free_forbidden_field_refs": list(P7_R50_BODY_FREE_FORBIDDEN_FIELD_REFS),
        "forbidden_field_refs_detected": forbidden_field_refs_detected,
        "forbidden_field_detected_count": len(forbidden_field_refs_detected),
        "forbidden_true_flag_refs": list(P7_R50_NO_BODY_LEAK_TRUE_FLAG_REFS),
        "forbidden_true_flag_refs_detected": forbidden_true_flag_refs_detected,
        "forbidden_true_flag_detected_count": len(forbidden_true_flag_refs_detected),
        "question_text_field_refs": list(P7_R50_QUESTION_TEXT_FIELD_REFS),
        "reviewer_free_text_field_refs": list(P7_R50_REVIEWER_FREE_TEXT_FIELD_REFS),
        "local_path_hash_field_refs": list(P7_R50_LOCAL_PATH_HASH_FIELD_REFS),
        "terminal_output_field_refs": list(P7_R50_TERMINAL_OUTPUT_FIELD_REFS),
        "body_free_flag_checked": True,
        "body_free_flag_present": body_free_present,
        "body_field_key_detected": bool(forbidden_field_refs_detected),
        "question_text_or_draft_question_text_detected": question_text_detected,
        "reviewer_free_text_detected": reviewer_free_text_detected,
        "local_path_or_body_hash_detected": local_path_or_body_hash_detected,
        "terminal_output_detected": terminal_output_detected,
        "raw_input_or_comment_text_detected": raw_input_or_comment_text_detected,
        "question_implementation_started_here": question_implementation_started,
        "api_db_rn_response_key_changed_here": False,
        "no_body_leak_guard_passed": ready and not forbidden_field_refs_detected and not forbidden_true_flag_refs_detected,
        "no_question_text_guard_passed": ready and not question_text_detected,
        "body_free_material_checked_without_copying_body": True,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_question_design_material_candidate": source.get("p8_question_design_material_candidate") is True,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "manual_run_decision_made_here": True,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "implemented_steps": list(P7_R50_R18_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R50_R18_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r49_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_prior_validation_evidence_adopted": True,
        "r3_manual_run_decision_built": True,
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built": True,
        "r5_24_case_review_session_protocol_built": True,
        "r6_local_only_body_full_packet_generation_request_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": True,
        "r8_rating_row_normalizer_built": True,
        "r9_readfeel_blocker_execution_blocker_ingestion_built": True,
        "r10_question_need_observation_row_normalizer_built": True,
        "r11_rating_question_observation_consistency_guard_built": True,
        "r12_pause_abort_expiration_protocol_built": True,
        "r13_disposal_receipt_builder_verifier_built": True,
        "r14_body_free_post_review_summary_built": True,
        "r15_p5_confirmed_repair_return_inconclusive_decision_built": True,
        "r16_p6_limited_human_readfeel_candidate_handoff_built": True,
        "r17_p8_question_design_material_candidate_handoff_built": True,
        "r18_no_body_leak_no_question_text_guard_built": True,
        "first_next_work_ref": P7_R50_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R50_R18_NEXT_REQUIRED_STEP_REF if ready else P7_R50_R18_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r50_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_for(P7_R50_R18_FALSE_KEY_REFS),
    }
    assert_p7_r50_no_body_leak_no_question_text_guard_bodyfree_contract(guard)
    return guard


def assert_p7_r50_no_body_leak_no_question_text_guard_bodyfree_contract(guard: Mapping[str, Any]) -> bool:
    data = safe_mapping(guard)
    _assert_required_fields(
        data,
        required=P7_R50_NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_BODYFREE_REQUIRED_FIELD_REFS,
        source="p7_r50_no_body_leak_no_question_text_guard_bodyfree",
    )
    _assert_common_with_false_keys(
        data,
        schema_version=P7_R50_NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_BODYFREE_SCHEMA_VERSION,
        source="p7_r50_no_body_leak_no_question_text_guard_bodyfree",
        false_keys=P7_R50_R18_FALSE_KEY_REFS,
    )
    if data.get("guard_status") not in P7_R50_NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_STATUS_REFS:
        raise ValueError("R50 R18 no-leak guard status is not canonical")
    if data.get("source_material_embedded_here") is not False:
        raise ValueError("R50 R18 must not embed scanned body-free material")
    forbidden_fields = dedupe_identifiers(data.get("forbidden_field_refs_detected"), limit=120, max_length=180)
    forbidden_flags = dedupe_identifiers(data.get("forbidden_true_flag_refs_detected"), limit=120, max_length=180)
    if data.get("forbidden_field_detected_count") != len(forbidden_fields):
        raise ValueError("R50 R18 forbidden field count mismatch")
    if data.get("forbidden_true_flag_detected_count") != len(forbidden_flags):
        raise ValueError("R50 R18 forbidden true flag count mismatch")
    if set(forbidden_fields) - set(P7_R50_BODY_FREE_FORBIDDEN_FIELD_REFS):
        raise ValueError("R50 R18 detected field refs must come from the frozen forbidden list")
    if set(forbidden_flags) - set(P7_R50_NO_BODY_LEAK_TRUE_FLAG_REFS):
        raise ValueError("R50 R18 detected true flag refs must come from the frozen flag list")
    question_detected = _r50_detected_intersects(forbidden_fields, P7_R50_QUESTION_TEXT_FIELD_REFS) or _r50_detected_intersects(
        forbidden_flags,
        ("question_text_included", "draft_question_text_included"),
    )
    if data.get("question_text_or_draft_question_text_detected") is not question_detected:
        raise ValueError("R50 R18 question-text detection mismatch")
    if data.get("guard_status") == "NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_READY":
        if forbidden_fields or forbidden_flags:
            raise ValueError("R50 R18 ready guard cannot have detected forbidden refs")
        if data.get("source_material_contract_checked") is not True:
            raise ValueError("R50 R18 ready guard requires source contract check")
        if data.get("body_free_flag_present") is not True:
            raise ValueError("R50 R18 ready guard requires body_free source")
        if data.get("no_body_leak_guard_passed") is not True or data.get("no_question_text_guard_passed") is not True:
            raise ValueError("R50 R18 ready guard must pass both guard booleans")
        if data.get("next_required_step") != P7_R50_R18_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R18 ready next step mismatch")
    else:
        if data.get("next_required_step") != P7_R50_R18_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R18 blocked next step mismatch")
    for key in (
        "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
        "actual_manual_review_run_here",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
        "api_db_rn_response_key_changed_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"R50 R18 must keep {key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R50_R18_IMPLEMENTED_STEPS:
        raise ValueError("R50 R18 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_R18_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R18 not-yet steps changed")
    return True


def _r50_command_lines_for_group(group_ref: str) -> tuple[str, ...]:
    lines: dict[str, tuple[str, ...]] = {
        "syntax_py_compile": (
            "PYTHONPATH=services/ai_inference python -m py_compile services/ai_inference/emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision.py tests/test_emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision_r18_r19_20260620.py",
        ),
        "r50_target_tests": (
            "PYTHONPATH=services/ai_inference pytest -q " + " ".join(P7_R50_VALIDATION_R50_TARGET_TEST_FILE_REFS),
        ),
        "r49_regression": (
            "PYTHONPATH=services/ai_inference pytest -q " + " ".join(P7_R49_VALIDATION_R49_TARGET_TEST_FILE_REFS),
        ),
        "r48_regression": (
            "PYTHONPATH=services/ai_inference pytest -q " + " ".join(P7_R49_VALIDATION_R48_REGRESSION_TEST_FILE_REFS),
        ),
        "r47_regression": (
            "PYTHONPATH=services/ai_inference pytest -q " + " ".join(P7_R49_VALIDATION_R47_REGRESSION_TEST_FILE_REFS),
        ),
        "r46_handoff_regression": (
            "PYTHONPATH=services/ai_inference pytest -q " + " ".join(P7_R49_VALIDATION_R46_HANDOFF_TEST_FILE_REFS),
        ),
        "display_contract_p5_core_subset": (
            "PYTHONPATH=services/ai_inference pytest -q "
            + " ".join((*P7_R49_VALIDATION_DISPLAY_API_TEST_FILE_REFS, *P7_R49_VALIDATION_P5_CORE_TEST_FILE_REFS)),
        ),
        "backend_collect_only": (
            "PYTHONPATH=services/ai_inference pytest --collect-only -q",
        ),
        "rn_no_touch_optional": (
            "cd Cocolon && npm run test:rn-screens --silent",
        ),
    }
    return lines[group_ref]


def _r50_test_file_refs_for_group(group_ref: str) -> tuple[str, ...]:
    mapping: dict[str, tuple[str, ...]] = {
        "syntax_py_compile": P7_R50_VALIDATION_SYNTAX_FILE_REFS,
        "r50_target_tests": P7_R50_VALIDATION_R50_TARGET_TEST_FILE_REFS,
        "r49_regression": P7_R49_VALIDATION_R49_TARGET_TEST_FILE_REFS,
        "r48_regression": P7_R49_VALIDATION_R48_REGRESSION_TEST_FILE_REFS,
        "r47_regression": P7_R49_VALIDATION_R47_REGRESSION_TEST_FILE_REFS,
        "r46_handoff_regression": P7_R49_VALIDATION_R46_HANDOFF_TEST_FILE_REFS,
        "display_contract_p5_core_subset": (*P7_R49_VALIDATION_DISPLAY_API_TEST_FILE_REFS, *P7_R49_VALIDATION_P5_CORE_TEST_FILE_REFS),
        "backend_collect_only": ("pytest_collect_only_reference",),
        "rn_no_touch_optional": P7_R49_RN_CONTRACT_OPTIONAL_NO_TOUCH_TEST_REFS,
    }
    return mapping[group_ref]


def _r50_validation_claim_boundary_for_group(group_ref: str) -> str:
    boundaries = {
        "syntax_py_compile": "syntax and import check only; no runtime or review execution claim",
        "r50_target_tests": "R50 helper contract target only; not P5 product-value pass",
        "r49_regression": "R49 regression only; not actual review completion",
        "r48_regression": "R48 packet/regression only; not body-full generation in this step",
        "r47_regression": "R47 local review packet policy regression only",
        "r46_handoff_regression": "R46 P5/P6 handoff regression only",
        "display_contract_p5_core_subset": "display and P5 core subset only; not real-device modal readfeel",
        "backend_collect_only": "collect-only is not full backend suite execution green",
        "rn_no_touch_optional": "RN no-touch contract is optional and not real-device modal readfeel",
    }
    return boundaries[group_ref]


def _build_p7_r50_validation_command_row_bodyfree(group_ref: str) -> dict[str, Any]:
    if group_ref not in P7_R50_VALIDATION_COMMAND_GROUP_REFS:
        raise ValueError("R50 R19 validation command group is not canonical")
    optional = group_ref in P7_R50_VALIDATION_COMMAND_OPTIONAL_GROUP_REFS
    row = {
        "validation_group_ref": group_ref,
        "command_kind_ref": "REFERENCE_COMMAND_ONLY",
        "command_purpose_ref": group_ref,
        "required_for_r50_validation": group_ref in P7_R50_VALIDATION_COMMAND_REQUIRED_GROUP_REFS,
        "optional": optional,
        "command_lines": list(_r50_command_lines_for_group(group_ref)),
        "test_file_refs": list(_r50_test_file_refs_for_group(group_ref)),
        "claim_boundary_ref": _r50_validation_claim_boundary_for_group(group_ref),
        "command_executed_here": False,
        "command_result_body_stored_here": False,
        "terminal_output_stored_here": False,
        "body_free": True,
    }
    assert_p7_r50_validation_command_row_bodyfree_contract(row)
    return row


def assert_p7_r50_validation_command_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(
        data,
        required=P7_R50_VALIDATION_COMMAND_ROW_BODYFREE_REQUIRED_FIELD_REFS,
        source="p7_r50_validation_command_row_bodyfree",
    )
    _assert_bodyfree_mapping_input(data, source="p7_r50_validation_command_row_bodyfree")
    group_ref = clean_identifier(data.get("validation_group_ref"), default="", max_length=120)
    if group_ref not in P7_R50_VALIDATION_COMMAND_GROUP_REFS:
        raise ValueError("R50 R19 validation row group is not canonical")
    if not isinstance(data.get("command_lines"), list) or not data.get("command_lines"):
        raise ValueError("R50 R19 validation row requires command lines")
    if not isinstance(data.get("test_file_refs"), list):
        raise ValueError("R50 R19 validation row requires test_file_refs list")
    if data.get("required_for_r50_validation") is not (group_ref in P7_R50_VALIDATION_COMMAND_REQUIRED_GROUP_REFS):
        raise ValueError("R50 R19 validation row required flag mismatch")
    if data.get("optional") is not (group_ref in P7_R50_VALIDATION_COMMAND_OPTIONAL_GROUP_REFS):
        raise ValueError("R50 R19 validation row optional flag mismatch")
    for key in ("command_executed_here", "command_result_body_stored_here", "terminal_output_stored_here"):
        if data.get(key) is not False:
            raise ValueError(f"R50 R19 validation row must keep {key}=False")
    return True


def build_p7_r50_validation_command_matrix_bodyfree(
    *,
    no_body_leak_no_question_text_guard_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r50_validation_command_matrix_bodyfree",
) -> dict[str, Any]:
    """Build the R50-19 validation command matrix without executing commands."""

    guard = (
        safe_mapping(no_body_leak_no_question_text_guard_bodyfree)
        if no_body_leak_no_question_text_guard_bodyfree is not None
        else build_p7_r50_no_body_leak_no_question_text_guard_bodyfree()
    )
    assert_p7_r50_no_body_leak_no_question_text_guard_bodyfree_contract(guard)
    ready = guard.get("guard_status") == "NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_READY"
    rows = [_build_p7_r50_validation_command_row_bodyfree(group_ref) for group_ref in P7_R50_VALIDATION_COMMAND_GROUP_REFS]
    matrix = {
        "schema_version": P7_R50_VALIDATION_COMMAND_MATRIX_BODYFREE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R50_STEP,
        "scope": P7_R50_SCOPE,
        "policy_kind": P7_R50_POLICY_KIND,
        "policy_section": "R50-19_validation_command_matrix",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r50_validation_command_matrix_bodyfree", max_length=180),
        "review_session_id": clean_identifier(guard.get("review_session_id"), default=P7_R50_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "r18_no_body_leak_no_question_text_guard_schema_version": P7_R50_NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_BODYFREE_SCHEMA_VERSION,
        "r18_no_body_leak_no_question_text_guard_ref": clean_identifier(guard.get("material_id"), default="p7_r50_no_body_leak_no_question_text_guard_bodyfree", max_length=180),
        "guard_status": clean_identifier(guard.get("guard_status"), default="BLOCKED_BY_BODY_FREE_LEAK_OR_QUESTION_TEXT", max_length=120),
        "validation_matrix_status": "VALIDATION_COMMAND_MATRIX_READY" if ready else "BLOCKED_BY_R50_18_NO_BODY_LEAK_GUARD",
        "validation_matrix_reason_refs": ["r18_no_body_leak_guard_ready"] if ready else ["r18_no_body_leak_guard_not_ready"],
        "validation_command_group_refs": list(P7_R50_VALIDATION_COMMAND_GROUP_REFS),
        "required_validation_group_refs": list(P7_R50_VALIDATION_COMMAND_REQUIRED_GROUP_REFS),
        "optional_validation_group_refs": list(P7_R50_VALIDATION_COMMAND_OPTIONAL_GROUP_REFS),
        "validation_command_rows": rows,
        "validation_command_row_count": len(rows),
        "r50_target_test_file_refs": list(P7_R50_VALIDATION_R50_TARGET_TEST_FILE_REFS),
        "r49_regression_test_file_refs": list(P7_R49_VALIDATION_R49_TARGET_TEST_FILE_REFS),
        "r48_regression_test_file_refs": list(P7_R49_VALIDATION_R48_REGRESSION_TEST_FILE_REFS),
        "r47_regression_test_file_refs": list(P7_R49_VALIDATION_R47_REGRESSION_TEST_FILE_REFS),
        "r46_handoff_regression_test_file_refs": list(P7_R49_VALIDATION_R46_HANDOFF_TEST_FILE_REFS),
        "display_contract_p5_core_test_file_refs": list((*P7_R49_VALIDATION_DISPLAY_API_TEST_FILE_REFS, *P7_R49_VALIDATION_P5_CORE_TEST_FILE_REFS)),
        "rn_no_touch_optional_test_file_refs": list(P7_R49_RN_CONTRACT_OPTIONAL_NO_TOUCH_TEST_REFS),
        "validation_commands_reference_only": True,
        "validation_commands_executed_here": False,
        "command_result_body_stored_here": False,
        "terminal_output_stored_here": False,
        "r50_target_green_confirmed_here": False,
        "r49_regression_green_confirmed_here": False,
        "r48_regression_green_confirmed_here": False,
        "r47_regression_green_confirmed_here": False,
        "r46_regression_green_confirmed_here": False,
        "display_p5_core_green_confirmed_here": False,
        "backend_collect_only_confirmed_here": False,
        "rn_no_touch_optional_confirmed_here": False,
        "full_backend_suite_green_confirmed": False,
        "collect_only_claimed_as_full_backend_green": False,
        "rn_contract_claimed_as_real_device_modal_readfeel": False,
        "r50_target_green_claimed_as_p5_product_quality_pass": False,
        "real_device_modal_readfeel_confirmed": False,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "implemented_steps": list(P7_R50_R19_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R50_R19_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r49_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_prior_validation_evidence_adopted": True,
        "r3_manual_run_decision_built": True,
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built": True,
        "r5_24_case_review_session_protocol_built": True,
        "r6_local_only_body_full_packet_generation_request_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": True,
        "r8_rating_row_normalizer_built": True,
        "r9_readfeel_blocker_execution_blocker_ingestion_built": True,
        "r10_question_need_observation_row_normalizer_built": True,
        "r11_rating_question_observation_consistency_guard_built": True,
        "r12_pause_abort_expiration_protocol_built": True,
        "r13_disposal_receipt_builder_verifier_built": True,
        "r14_body_free_post_review_summary_built": True,
        "r15_p5_confirmed_repair_return_inconclusive_decision_built": True,
        "r16_p6_limited_human_readfeel_candidate_handoff_built": True,
        "r17_p8_question_design_material_candidate_handoff_built": True,
        "r18_no_body_leak_no_question_text_guard_built": True,
        "r19_validation_command_matrix_built": True,
        "first_next_work_ref": P7_R50_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R50_R19_NEXT_REQUIRED_STEP_REF if ready else P7_R50_R19_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r50_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_for(P7_R50_R19_FALSE_KEY_REFS),
    }
    assert_p7_r50_validation_command_matrix_bodyfree_contract(matrix)
    return matrix


def build_p7_r50_validation_command_matrix(**kwargs: Any) -> dict[str, Any]:
    return build_p7_r50_validation_command_matrix_bodyfree(**kwargs)


def assert_p7_r50_validation_command_matrix_bodyfree_contract(matrix: Mapping[str, Any]) -> bool:
    data = safe_mapping(matrix)
    _assert_required_fields(
        data,
        required=P7_R50_VALIDATION_COMMAND_MATRIX_BODYFREE_REQUIRED_FIELD_REFS,
        source="p7_r50_validation_command_matrix_bodyfree",
    )
    _assert_common_with_false_keys(
        data,
        schema_version=P7_R50_VALIDATION_COMMAND_MATRIX_BODYFREE_SCHEMA_VERSION,
        source="p7_r50_validation_command_matrix_bodyfree",
        false_keys=P7_R50_R19_FALSE_KEY_REFS,
    )
    if data.get("validation_matrix_status") not in P7_R50_VALIDATION_COMMAND_MATRIX_STATUS_REFS:
        raise ValueError("R50 R19 validation matrix status is not canonical")
    rows = data.get("validation_command_rows")
    if not isinstance(rows, list):
        raise ValueError("R50 R19 validation matrix rows must be a list")
    if data.get("validation_command_row_count") != len(rows):
        raise ValueError("R50 R19 validation row count mismatch")
    if [safe_mapping(row).get("validation_group_ref") for row in rows] != list(P7_R50_VALIDATION_COMMAND_GROUP_REFS):
        raise ValueError("R50 R19 validation groups changed or reordered")
    for row in rows:
        assert_p7_r50_validation_command_row_bodyfree_contract(row)
    if data.get("required_validation_group_refs") != list(P7_R50_VALIDATION_COMMAND_REQUIRED_GROUP_REFS):
        raise ValueError("R50 R19 required validation groups changed")
    if data.get("optional_validation_group_refs") != list(P7_R50_VALIDATION_COMMAND_OPTIONAL_GROUP_REFS):
        raise ValueError("R50 R19 optional validation groups changed")
    if data.get("r50_target_test_file_refs") != list(P7_R50_VALIDATION_R50_TARGET_TEST_FILE_REFS):
        raise ValueError("R50 R19 target test refs changed")
    if "tests/test_emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision_r18_r19_20260620.py" not in data.get("r50_target_test_file_refs"):
        raise ValueError("R50 R19 target tests must include the R18/R19 target file")
    for key in (
        "validation_commands_executed_here",
        "command_result_body_stored_here",
        "terminal_output_stored_here",
        "r50_target_green_confirmed_here",
        "full_backend_suite_green_confirmed",
        "collect_only_claimed_as_full_backend_green",
        "rn_contract_claimed_as_real_device_modal_readfeel",
        "r50_target_green_claimed_as_p5_product_quality_pass",
        "real_device_modal_readfeel_confirmed",
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
        "p7_complete",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"R50 R19 validation matrix must keep {key}=False")
    ready = data.get("guard_status") == "NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_READY"
    if ready:
        if data.get("validation_matrix_status") != "VALIDATION_COMMAND_MATRIX_READY":
            raise ValueError("R50 R19 ready matrix requires ready status")
        if data.get("next_required_step") != P7_R50_R19_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R19 ready next step mismatch")
    else:
        if data.get("validation_matrix_status") != "BLOCKED_BY_R50_18_NO_BODY_LEAK_GUARD":
            raise ValueError("R50 R19 blocked matrix requires blocked status")
        if data.get("next_required_step") != P7_R50_R19_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R19 blocked next step mismatch")
    if tuple(data.get("implemented_steps") or ()) != P7_R50_R19_IMPLEMENTED_STEPS:
        raise ValueError("R50 R19 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_R19_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R19 not-yet steps changed")
    return True


def build_p7_r50_r18_r19_no_leak_validation_matrix_freeze(
    *,
    no_body_leak_no_question_text_guard_bodyfree: Mapping[str, Any] | None = None,
    validation_command_matrix_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r50_r18_r19_no_leak_validation_matrix_freeze",
) -> dict[str, Any]:
    guard = (
        safe_mapping(no_body_leak_no_question_text_guard_bodyfree)
        if no_body_leak_no_question_text_guard_bodyfree is not None
        else build_p7_r50_no_body_leak_no_question_text_guard_bodyfree()
    )
    assert_p7_r50_no_body_leak_no_question_text_guard_bodyfree_contract(guard)
    matrix = (
        safe_mapping(validation_command_matrix_bodyfree)
        if validation_command_matrix_bodyfree is not None
        else build_p7_r50_validation_command_matrix_bodyfree(no_body_leak_no_question_text_guard_bodyfree=guard)
    )
    assert_p7_r50_validation_command_matrix_bodyfree_contract(matrix)
    freeze = {
        "schema_version": P7_R50_R18_R19_NO_LEAK_VALIDATION_MATRIX_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R50_STEP,
        "scope": P7_R50_SCOPE,
        "policy_kind": P7_R50_POLICY_KIND,
        "policy_section": "R50-18_R50-19_no_leak_validation_matrix_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r50_r18_r19_no_leak_validation_matrix_freeze", max_length=180),
        "r18_no_body_leak_no_question_text_guard": guard,
        "r19_validation_command_matrix": matrix,
        "review_session_id": matrix["review_session_id"],
        "guard_status": guard["guard_status"],
        "validation_matrix_status": matrix["validation_matrix_status"],
        "validation_command_row_count": matrix["validation_command_row_count"],
        "p7_complete": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "implemented_steps": list(P7_R50_R19_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R50_R19_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r49_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_prior_validation_evidence_adopted": True,
        "r3_manual_run_decision_built": True,
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built": True,
        "r5_24_case_review_session_protocol_built": True,
        "r6_local_only_body_full_packet_generation_request_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": True,
        "r8_rating_row_normalizer_built": True,
        "r9_readfeel_blocker_execution_blocker_ingestion_built": True,
        "r10_question_need_observation_row_normalizer_built": True,
        "r11_rating_question_observation_consistency_guard_built": True,
        "r12_pause_abort_expiration_protocol_built": True,
        "r13_disposal_receipt_builder_verifier_built": True,
        "r14_body_free_post_review_summary_built": True,
        "r15_p5_confirmed_repair_return_inconclusive_decision_built": True,
        "r16_p6_limited_human_readfeel_candidate_handoff_built": True,
        "r17_p8_question_design_material_candidate_handoff_built": True,
        "r18_no_body_leak_no_question_text_guard_built": True,
        "r19_validation_command_matrix_built": True,
        "first_next_work_ref": P7_R50_FIRST_NEXT_WORK_REF,
        "next_required_step": matrix["next_required_step"],
        "public_contract": public_contract_flags(),
        "r50_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_for(P7_R50_R19_FALSE_KEY_REFS),
    }
    assert_p7_r50_r18_r19_no_leak_validation_matrix_freeze_contract(freeze)
    return freeze


def assert_p7_r50_r18_r19_no_leak_validation_matrix_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_required_fields(
        data,
        required=P7_R50_R18_R19_NO_LEAK_VALIDATION_MATRIX_FREEZE_REQUIRED_FIELD_REFS,
        source="p7_r50_r18_r19_no_leak_validation_matrix_freeze",
    )
    _assert_common_with_false_keys(
        data,
        schema_version=P7_R50_R18_R19_NO_LEAK_VALIDATION_MATRIX_FREEZE_SCHEMA_VERSION,
        source="p7_r50_r18_r19_no_leak_validation_matrix_freeze",
        false_keys=P7_R50_R19_FALSE_KEY_REFS,
    )
    guard = safe_mapping(data.get("r18_no_body_leak_no_question_text_guard"))
    matrix = safe_mapping(data.get("r19_validation_command_matrix"))
    assert_p7_r50_no_body_leak_no_question_text_guard_bodyfree_contract(guard)
    assert_p7_r50_validation_command_matrix_bodyfree_contract(matrix)
    if data.get("review_session_id") != matrix.get("review_session_id"):
        raise ValueError("R50 R18/R19 freeze review session mismatch")
    if data.get("guard_status") != guard.get("guard_status"):
        raise ValueError("R50 R18/R19 guard status mismatch")
    if data.get("validation_matrix_status") != matrix.get("validation_matrix_status"):
        raise ValueError("R50 R18/R19 matrix status mismatch")
    if data.get("validation_command_row_count") != matrix.get("validation_command_row_count"):
        raise ValueError("R50 R18/R19 validation row count mismatch")
    for key in ("p7_complete", "p8_start_allowed", "release_allowed", "actual_manual_review_run_here", "body_full_packet_generated_here", "body_full_packets_created_local_only"):
        if data.get(key) is not False:
            raise ValueError(f"R50 R18/R19 must keep {key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R50_R19_IMPLEMENTED_STEPS:
        raise ValueError("R50 R18/R19 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_R19_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R18/R19 not-yet steps changed")
    return True


# ---------------------------------------------------------------------------
# R50-20: touch candidate / no-touch boundary freeze
# ---------------------------------------------------------------------------


def _r50_touch_boundary_reason_refs(*, validation_matrix_ready: bool) -> list[str]:
    if validation_matrix_ready:
        return ["r50_touch_candidate_no_touch_boundary_frozen_after_validation_matrix_ready"]
    return ["r50_19_validation_matrix_not_ready"]


def build_p7_r50_touch_candidate_no_touch_boundary_freeze(
    *,
    r18_r19_no_leak_validation_matrix_freeze: Mapping[str, Any] | None = None,
    r50_r18_r19_no_leak_validation_matrix_freeze: Mapping[str, Any] | None = None,
    r49_touch_candidate_no_touch_boundary_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r50_touch_candidate_no_touch_boundary_freeze",
) -> dict[str, Any]:
    """Build the R50-20 body-free touch/no-touch boundary freeze.

    This fixes the only files R50 may touch and keeps runtime, RN, API, DB,
    public meta, P8 question implementation, and release surfaces out of scope.
    It does not inspect git, materialize a touched-file scan, execute commands,
    start local manual review, generate body-full packets, or claim release.
    """

    if (
        r18_r19_no_leak_validation_matrix_freeze is not None
        and r50_r18_r19_no_leak_validation_matrix_freeze is not None
    ):
        raise ValueError("provide only one R50 R18/R19 freeze value")
    r19 = (
        safe_mapping(r50_r18_r19_no_leak_validation_matrix_freeze)
        if r50_r18_r19_no_leak_validation_matrix_freeze is not None
        else safe_mapping(r18_r19_no_leak_validation_matrix_freeze)
        if r18_r19_no_leak_validation_matrix_freeze is not None
        else build_p7_r50_r18_r19_no_leak_validation_matrix_freeze()
    )
    assert_p7_r50_r18_r19_no_leak_validation_matrix_freeze_contract(r19)
    r49_boundary = _r49_boundary(r49_touch_candidate_no_touch_boundary_freeze)

    validation_matrix_ready = r19.get("validation_matrix_status") == "VALIDATION_COMMAND_MATRIX_READY"
    status = (
        "TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FROZEN"
        if validation_matrix_ready
        else "BLOCKED_BY_R50_19_VALIDATION_MATRIX"
    )
    next_required_step = P7_R50_R20_NEXT_REQUIRED_STEP_REF if validation_matrix_ready else P7_R50_R20_BLOCKED_NEXT_REQUIRED_STEP_REF

    freeze = {
        "schema_version": P7_R50_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R50_STEP,
        "scope": P7_R50_SCOPE,
        "policy_kind": P7_R50_POLICY_KIND,
        "policy_section": "R50-20_touch_candidate_no_touch_boundary_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r50_touch_candidate_no_touch_boundary_freeze", max_length=180),
        "review_session_id": clean_identifier(r19.get("review_session_id"), default=P7_R50_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "review_kind": P7_R50_REVIEW_KIND,
        "packet_kind": P7_R50_PACKET_KIND,
        "r18_r19_no_leak_validation_matrix_freeze_schema_version": P7_R50_R18_R19_NO_LEAK_VALIDATION_MATRIX_FREEZE_SCHEMA_VERSION,
        "r18_r19_no_leak_validation_matrix_freeze_ref": clean_identifier(
            r19.get("material_id"), default="p7_r50_r18_r19_no_leak_validation_matrix_freeze", max_length=180
        ),
        "r49_touch_boundary_schema_version": P7_R49_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION,
        "r49_touch_boundary_ref": clean_identifier(
            r49_boundary.get("material_id"), default="p7_r49_touch_candidate_no_touch_boundary_freeze", max_length=180
        ),
        "guard_status": clean_identifier(r19.get("guard_status"), default="unknown_guard_status", max_length=120),
        "validation_matrix_status": clean_identifier(r19.get("validation_matrix_status"), default="unknown_validation_matrix_status", max_length=120),
        "touch_boundary_status": status,
        "touch_boundary_reason_refs": _r50_touch_boundary_reason_refs(validation_matrix_ready=validation_matrix_ready),
        "touch_boundary_freeze_required": True,
        "touch_boundary_freeze_ready": validation_matrix_ready,
        "production_touch_candidate_file_refs": list(P7_R50_PRODUCTION_TOUCH_CANDIDATE_FILE_REFS),
        "optional_touch_candidate_file_refs": list(P7_R50_OPTIONAL_TOUCH_CANDIDATE_FILE_REFS),
        "test_touch_candidate_file_refs": list(P7_R50_ALLOWED_TEST_TOUCH_FILE_REFS),
        "allowed_production_file_refs": list(P7_R50_ALLOWED_PRODUCTION_TOUCH_FILE_REFS),
        "allowed_test_file_refs": list(P7_R50_ALLOWED_TEST_TOUCH_FILE_REFS),
        "allowed_actual_touched_file_refs": list(P7_R50_ALLOWED_ACTUAL_TOUCHED_FILE_REFS),
        "explicit_no_touch_file_refs": list(P7_R50_EXPLICIT_NO_TOUCH_FILE_REFS),
        "explicit_no_touch_area_refs": list(P7_R50_EXPLICIT_NO_TOUCH_AREA_REFS),
        "forbidden_actual_touched_file_refs": list(P7_R50_EXPLICIT_NO_TOUCH_FILE_REFS),
        "current_patch_expected_touched_file_refs": list(P7_R50_R20_CURRENT_PATCH_EXPECTED_TOUCHED_FILE_REFS),
        "actual_touched_file_refs_checked_here": False,
        "actual_touched_file_refs_verified_here": False,
        "actual_touched_file_refs_materialized_here": False,
        "forbidden_actual_touched_refs_detected_here": False,
        "touch_candidate_boundary_frozen": True,
        "no_touch_boundary_frozen": True,
        "forbidden_actual_touched_refs_rejected": True,
        "no_touch_refs_must_remain_untouched": True,
        "allowed_refs_do_not_include_no_touch_refs": True,
        "current_patch_expected_touched_refs_are_allowed": True,
        "production_touch_candidate_is_r50_helper_only": True,
        "optional_touch_candidate_is_local_file_ops_only": True,
        "test_touch_candidate_is_r50_target_only": True,
        "production_runtime_spread_allowed": False,
        "rn_runtime_spread_allowed": False,
        "api_db_release_spread_allowed": False,
        "rn_contract_changed_here": False,
        "rn_production_files_touched_here": False,
        "rn_contract_test_files_touched_here": False,
        "rn_visible_contract_changed_here": False,
        "public_response_shape_changed_here": False,
        "api_response_shape_changed_here": False,
        "public_response_top_level_key_added_here": False,
        "request_key_changed_here": False,
        "api_route_changed_here": False,
        "db_schema_changed_here": False,
        "db_migration_changed_here": False,
        "emlis_reply_runtime_changed_here": False,
        "user_label_connection_runtime_changed_here": False,
        "p5_runtime_changed_here": False,
        "p5_gate_relaxed_here": False,
        "release_material_changed_here": False,
        "question_trigger_logic_implemented_here": False,
        "question_api_implemented": False,
        "question_db_schema_implemented": False,
        "question_rn_ui_implemented": False,
        "question_response_key_added": False,
        "question_text_implemented_here": False,
        "draft_question_text_implemented_here": False,
        "validation_commands_executed_here": False,
        "command_output_stored_here": False,
        "terminal_output_stored_here": False,
        "p5_human_blind_qa_confirmed_candidate": False,
        "p6_limited_human_readfeel_start_allowed_candidate": False,
        "p8_question_design_material_candidate": False,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "p8_detail_design_allowed_here": False,
        "p8_implementation_spec_finalized_here": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "body_full_writer_created_here": False,
        "local_reviewer_payload_materialized_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_question_need_observation_summary_materialized_here": False,
        "actual_disposal_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "implemented_steps": list(P7_R50_R20_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R50_R20_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R50_FIRST_NEXT_WORK_REF,
        "next_required_step": next_required_step,
        "post_r20_next_work_ref": P7_R50_R20_POST_FREEZE_NEXT_WORK_REF,
        "r0_current_source_r49_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_prior_validation_evidence_adopted": True,
        "r3_manual_run_decision_built": True,
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built": True,
        "r5_24_case_review_session_protocol_built": True,
        "r6_local_only_body_full_packet_generation_request_built": True,
        "r7_reviewer_instruction_rating_form_freeze_built": True,
        "r8_rating_row_normalizer_built": True,
        "r9_readfeel_blocker_execution_blocker_ingestion_built": True,
        "r10_question_need_observation_row_normalizer_built": True,
        "r11_rating_question_observation_consistency_guard_built": True,
        "r12_pause_abort_expiration_protocol_built": True,
        "r13_disposal_receipt_builder_verifier_built": True,
        "r14_body_free_post_review_summary_built": True,
        "r15_p5_confirmed_repair_return_inconclusive_decision_built": True,
        "r16_p6_limited_human_readfeel_candidate_handoff_built": True,
        "r17_p8_question_design_material_candidate_handoff_built": True,
        "r18_no_body_leak_no_question_text_guard_built": True,
        "r19_validation_command_matrix_built": True,
        "r20_touch_candidate_no_touch_boundary_frozen": True,
        "public_contract": public_contract_flags(),
        "r50_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_for(P7_R50_R20_FALSE_KEY_REFS),
    }
    assert_p7_r50_touch_candidate_no_touch_boundary_freeze_contract(freeze)
    return freeze


def assert_p7_r50_touch_candidate_no_touch_boundary_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_required_fields(
        data,
        required=P7_R50_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FREEZE_REQUIRED_FIELD_REFS,
        source="p7_r50_touch_candidate_no_touch_boundary_freeze",
    )
    _assert_common_with_false_keys(
        data,
        schema_version=P7_R50_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION,
        source="p7_r50_touch_candidate_no_touch_boundary_freeze",
        false_keys=P7_R50_R20_FALSE_KEY_REFS,
    )
    if data.get("policy_section") != "R50-20_touch_candidate_no_touch_boundary_freeze":
        raise ValueError("R50 R20 policy section changed")
    if data.get("touch_boundary_status") not in P7_R50_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_STATUS_REFS:
        raise ValueError("R50 R20 touch boundary status is not canonical")
    if data.get("r18_r19_no_leak_validation_matrix_freeze_schema_version") != P7_R50_R18_R19_NO_LEAK_VALIDATION_MATRIX_FREEZE_SCHEMA_VERSION:
        raise ValueError("R50 R20 R18/R19 schema version changed")
    if data.get("r49_touch_boundary_schema_version") != P7_R49_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION:
        raise ValueError("R50 R20 R49 boundary schema version changed")
    if tuple(data.get("production_touch_candidate_file_refs") or ()) != P7_R50_PRODUCTION_TOUCH_CANDIDATE_FILE_REFS:
        raise ValueError("R50 R20 production touch candidate refs changed")
    if tuple(data.get("optional_touch_candidate_file_refs") or ()) != P7_R50_OPTIONAL_TOUCH_CANDIDATE_FILE_REFS:
        raise ValueError("R50 R20 optional touch candidate refs changed")
    if tuple(data.get("test_touch_candidate_file_refs") or ()) != P7_R50_ALLOWED_TEST_TOUCH_FILE_REFS:
        raise ValueError("R50 R20 test touch candidate refs changed")
    if tuple(data.get("allowed_production_file_refs") or ()) != P7_R50_ALLOWED_PRODUCTION_TOUCH_FILE_REFS:
        raise ValueError("R50 R20 allowed production refs changed")
    if tuple(data.get("allowed_test_file_refs") or ()) != P7_R50_ALLOWED_TEST_TOUCH_FILE_REFS:
        raise ValueError("R50 R20 allowed test refs changed")
    if tuple(data.get("allowed_actual_touched_file_refs") or ()) != P7_R50_ALLOWED_ACTUAL_TOUCHED_FILE_REFS:
        raise ValueError("R50 R20 allowed actual touched refs changed")
    if tuple(data.get("explicit_no_touch_file_refs") or ()) != P7_R50_EXPLICIT_NO_TOUCH_FILE_REFS:
        raise ValueError("R50 R20 explicit no-touch file refs changed")
    if tuple(data.get("explicit_no_touch_area_refs") or ()) != P7_R50_EXPLICIT_NO_TOUCH_AREA_REFS:
        raise ValueError("R50 R20 explicit no-touch areas changed")
    if tuple(data.get("forbidden_actual_touched_file_refs") or ()) != P7_R50_EXPLICIT_NO_TOUCH_FILE_REFS:
        raise ValueError("R50 R20 forbidden touched refs changed")
    if tuple(data.get("current_patch_expected_touched_file_refs") or ()) != P7_R50_R20_CURRENT_PATCH_EXPECTED_TOUCHED_FILE_REFS:
        raise ValueError("R50 R20 current patch expected touched refs changed")

    allowed = set(data.get("allowed_actual_touched_file_refs") or ())
    no_touch = set(data.get("explicit_no_touch_file_refs") or ())
    expected = set(data.get("current_patch_expected_touched_file_refs") or ())
    if allowed & no_touch:
        raise ValueError("R50 R20 allowed refs must not overlap explicit no-touch refs")
    if not expected or not expected.issubset(allowed):
        raise ValueError("R50 R20 current patch expected touched refs must be allowed")
    if expected & no_touch:
        raise ValueError("R50 R20 current patch expected touched refs must not include no-touch refs")
    if data.get("current_patch_expected_touched_refs_are_allowed") is not True:
        raise ValueError("R50 R20 must mark current patch expected refs as allowed")

    for true_key in (
        "touch_boundary_freeze_required",
        "touch_candidate_boundary_frozen",
        "no_touch_boundary_frozen",
        "forbidden_actual_touched_refs_rejected",
        "no_touch_refs_must_remain_untouched",
        "allowed_refs_do_not_include_no_touch_refs",
        "production_touch_candidate_is_r50_helper_only",
        "optional_touch_candidate_is_local_file_ops_only",
        "test_touch_candidate_is_r50_target_only",
        "r0_current_source_r49_handoff_bridge_refrozen",
        "r1_scope_schema_status_enum_fixed",
        "r2_prior_validation_evidence_adopted",
        "r3_manual_run_decision_built",
        "r4_local_only_root_explicit_allow_export_denylist_preflight_built",
        "r5_24_case_review_session_protocol_built",
        "r6_local_only_body_full_packet_generation_request_built",
        "r7_reviewer_instruction_rating_form_freeze_built",
        "r8_rating_row_normalizer_built",
        "r9_readfeel_blocker_execution_blocker_ingestion_built",
        "r10_question_need_observation_row_normalizer_built",
        "r11_rating_question_observation_consistency_guard_built",
        "r12_pause_abort_expiration_protocol_built",
        "r13_disposal_receipt_builder_verifier_built",
        "r14_body_free_post_review_summary_built",
        "r15_p5_confirmed_repair_return_inconclusive_decision_built",
        "r16_p6_limited_human_readfeel_candidate_handoff_built",
        "r17_p8_question_design_material_candidate_handoff_built",
        "r18_no_body_leak_no_question_text_guard_built",
        "r19_validation_command_matrix_built",
        "r20_touch_candidate_no_touch_boundary_frozen",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R50 R20 boundary must keep {true_key}=True")
    for false_key in (
        "actual_touched_file_refs_checked_here",
        "actual_touched_file_refs_verified_here",
        "actual_touched_file_refs_materialized_here",
        "forbidden_actual_touched_refs_detected_here",
        "production_runtime_spread_allowed",
        "rn_runtime_spread_allowed",
        "api_db_release_spread_allowed",
        "rn_contract_changed_here",
        "rn_production_files_touched_here",
        "rn_contract_test_files_touched_here",
        "rn_visible_contract_changed_here",
        "public_response_shape_changed_here",
        "api_response_shape_changed_here",
        "public_response_top_level_key_added_here",
        "request_key_changed_here",
        "api_route_changed_here",
        "db_schema_changed_here",
        "db_migration_changed_here",
        "emlis_reply_runtime_changed_here",
        "user_label_connection_runtime_changed_here",
        "p5_runtime_changed_here",
        "p5_gate_relaxed_here",
        "release_material_changed_here",
        "question_trigger_logic_implemented_here",
        "question_api_implemented",
        "question_db_schema_implemented",
        "question_rn_ui_implemented",
        "question_response_key_added",
        "question_text_implemented_here",
        "draft_question_text_implemented_here",
        "validation_commands_executed_here",
        "command_output_stored_here",
        "terminal_output_stored_here",
        "p5_human_blind_qa_confirmed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_limited_human_readfeel_confirmed",
        "p8_detail_design_allowed_here",
        "p8_implementation_spec_finalized_here",
        "p7_complete",
        "p8_start_allowed",
        "release_allowed",
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
        "actual_disposal_run_here",
        "actual_disposal_receipt_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R50 R20 boundary must keep {false_key}=False")
    ready = data.get("validation_matrix_status") == "VALIDATION_COMMAND_MATRIX_READY"
    if ready:
        if data.get("touch_boundary_status") != "TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FROZEN":
            raise ValueError("R50 R20 ready boundary requires frozen status")
        if data.get("touch_boundary_freeze_ready") is not True:
            raise ValueError("R50 R20 ready boundary must set touch_boundary_freeze_ready=True")
        if data.get("next_required_step") != P7_R50_R20_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R20 ready next step mismatch")
        if data.get("post_r20_next_work_ref") != P7_R50_R20_POST_FREEZE_NEXT_WORK_REF:
            raise ValueError("R50 R20 post-freeze next work mismatch")
    else:
        if data.get("touch_boundary_status") != "BLOCKED_BY_R50_19_VALIDATION_MATRIX":
            raise ValueError("R50 R20 blocked boundary requires blocked status")
        if data.get("touch_boundary_freeze_ready") is not False:
            raise ValueError("R50 R20 blocked boundary must set touch_boundary_freeze_ready=False")
        if data.get("next_required_step") != P7_R50_R20_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R50 R20 blocked next step mismatch")
    if tuple(data.get("implemented_steps") or ()) != P7_R50_R20_IMPLEMENTED_STEPS:
        raise ValueError("R50 R20 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R50_R20_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R50 R20 not-yet steps changed")
    return True


def assert_p7_r50_touch_candidate_no_touch_actual_touched_file_refs_contract(
    actual_touched_file_refs: Sequence[str] | Any,
    *,
    touch_boundary_freeze: Mapping[str, Any] | None = None,
) -> bool:
    """Validate caller-provided touched refs against the R50 R20 boundary.

    This helper does not inspect git, write logs, materialize filesystem results,
    or turn touched refs into an executed validation claim.
    """

    boundary = (
        safe_mapping(touch_boundary_freeze)
        if touch_boundary_freeze is not None
        else build_p7_r50_touch_candidate_no_touch_boundary_freeze()
    )
    assert_p7_r50_touch_candidate_no_touch_boundary_freeze_contract(boundary)
    touched_refs = tuple(dedupe_identifiers(actual_touched_file_refs, limit=240, max_length=260))
    if not touched_refs:
        raise ValueError("R50 R20 actual touched refs must be provided for boundary validation")
    allowed = set(boundary.get("allowed_actual_touched_file_refs") or ())
    no_touch = set(boundary.get("explicit_no_touch_file_refs") or ())
    forbidden = set(boundary.get("forbidden_actual_touched_file_refs") or ())
    touched_set = set(touched_refs)
    if touched_set & no_touch or touched_set & forbidden:
        raise ValueError("R50 R20 actual touched refs include explicit no-touch refs")
    not_allowed = sorted(touched_set - allowed)
    if not_allowed:
        raise ValueError(f"R50 R20 actual touched refs are outside allowed candidates: {not_allowed[:6]}")
    return True


def _default_one_question_fit_for_primary_r50(primary_class: str) -> str:
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
        raise ValueError("R50 R10 question observation primary class must use the frozen enum")
    return mapping[primary_class]


def _default_repair_refs_for_primary_r50(primary_class: str) -> list[str]:
    if primary_class == "not_question_emlis_readfeel_repair_required":
        return ["emlis_readfeel_repair_required"]
    if primary_class == "not_question_p5_surface_repair_required":
        return ["p5_surface_repair_required"]
    if primary_class == "not_question_gate_boundary_required":
        return ["gate_boundary_repair_required"]
    return ["no_repair_required"]


def _normalize_plan_candidate_flags_r50(primary_class: str, raw_flags: Any) -> list[str]:
    if isinstance(raw_flags, Mapping):
        supplied = [clean_identifier(key, default="", max_length=120) for key, value in raw_flags.items() if bool(value)]
    elif raw_flags is None:
        supplied = []
    else:
        supplied = _assert_identifier_sequence_r50(
            raw_flags,
            source="p7_r50_question_observation.plan_candidate_flags",
            allowed_refs=P7_R50_PLAN_CANDIDATE_FLAG_REFS,
        )
    supplied = dedupe_identifiers(supplied, limit=10, max_length=120)
    unknown = sorted(set(supplied) - set(P7_R50_PLAN_CANDIDATE_FLAG_REFS))
    if unknown:
        raise ValueError(f"R50 R10 plan candidate flags are outside the frozen enum: {unknown[:4]}")

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
        raise ValueError("R50 R10 plus question candidate flag must match plus primary class")
    if primary_class == "premium_deep_dive_candidate_later":
        flags.add("premium_deep_dive_candidate_later")
    elif "premium_deep_dive_candidate_later" in flags:
        raise ValueError("R50 R10 premium deep-dive flag must match premium primary class")
    if primary_class in p8_material_primary_classes:
        flags.add("p8_design_material_candidate")
    if primary_class in repair_or_execution_primary_classes and flags:
        raise ValueError("R50 R10 repair/execution observations must not be marked as P8 question candidates")
    return [ref for ref in P7_R50_PLAN_CANDIDATE_FLAG_REFS if ref in flags]


def _r50_case_identity(row: Mapping[str, Any]) -> tuple[Any, Any, Any, Any, Any]:
    data = safe_mapping(row)
    return (
        data.get("review_session_id"),
        data.get("packet_ref_id"),
        data.get("blind_case_id"),
        data.get("case_ref_id"),
        data.get("family"),
    )


def _assert_matching_execution_blocker_for_question_observation(
    qrow: Mapping[str, Any],
    execution_blocker_rows: Sequence[Mapping[str, Any]] | None,
) -> None:
    if not execution_blocker_rows:
        raise ValueError("R50 R11 insufficient-material question observation requires a matching execution blocker row")
    qid = _r50_case_identity(qrow)
    for raw in execution_blocker_rows:
        erow = safe_mapping(raw)
        if not erow:
            continue
        assert_p7_r50_execution_blocker_row_bodyfree_contract(erow)
        if _r50_case_identity(erow) == qid:
            return
    raise ValueError("R50 R11 insufficient-material question observation requires a matching execution blocker row")


def _validate_question_observation_semantics_r50(
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
        raise ValueError("R50 question observation primary class must use the frozen enum")
    if one_fit not in P7_R50_ONE_QUESTION_FIT_REFS:
        raise ValueError("R50 question observation one_question_fit_ref must use the frozen enum")
    if one_fit != _default_one_question_fit_for_primary_r50(primary):
        raise ValueError("R50 question observation primary class and one-question fit are inconsistent")
    if not repairs:
        raise ValueError("R50 question observation repair_required_refs must be explicit")
    if "no_repair_required" in repairs and len(repairs) > 1:
        raise ValueError("R50 question observation no_repair_required must not mix with repair refs")
    for ref in repairs:
        if ref not in P7_R50_REPAIR_REQUIRED_REF_REFS:
            raise ValueError("R50 question observation repair refs must use the frozen enum")
    for ref in ambiguity:
        if ref not in P7_R50_AMBIGUITY_KIND_REFS:
            raise ValueError("R50 question observation ambiguity refs must use the frozen enum")
    for ref in plan_flags:
        if ref not in P7_R50_PLAN_CANDIDATE_FLAG_REFS:
            raise ValueError("R50 question observation plan flags must use the frozen enum")
    if primary.startswith("not_question_"):
        required = set(_default_repair_refs_for_primary_r50(primary))
        if not required <= set(repairs):
            raise ValueError("R50 repair primary classes require the matching repair ref")
        if plan_flags:
            raise ValueError("R50 repair primary classes must not become P8 question material candidates")
    if primary == "insufficient_material_execution_blocker":
        if one_fit != "insufficient_material":
            raise ValueError("R50 insufficient-material observation must use insufficient_material one-question fit")
        if repairs != ("no_repair_required",):
            raise ValueError("R50 insufficient-material observation must not carry repair refs")
        if plan_flags:
            raise ValueError("R50 insufficient-material observation must not become P8 question material")
        if require_execution_blocker_match:
            _assert_matching_execution_blocker_for_question_observation(data, execution_blocker_rows)
    if primary == "no_question_needed_emlis_can_observe":
        if repairs != ("no_repair_required",):
            raise ValueError("R50 no-question-needed observation must not carry repair refs")
        if set(ambiguity) != {"no_material_ambiguity"}:
            raise ValueError("R50 no-question-needed observation must carry only no_material_ambiguity")
    question_candidate_primary_classes = {
        "question_may_reduce_overread_risk",
        "question_would_make_immediate_observation_heavy",
        "plus_single_question_candidate_later",
        "premium_deep_dive_candidate_later",
    }
    if primary in question_candidate_primary_classes:
        if not ambiguity or "no_material_ambiguity" in ambiguity:
            raise ValueError("R50 question candidate observations require a concrete body-free ambiguity kind")
        if repairs != ("no_repair_required",):
            raise ValueError("R50 question candidate observations must not carry repair refs")
        if "p8_design_material_candidate" not in plan_flags:
            raise ValueError("R50 question candidate observations must be P8 design material candidates")
    if primary == "plus_single_question_candidate_later" and "plus_single_question_candidate_later" not in plan_flags:
        raise ValueError("R50 plus-single-question observations require the plus overlay flag")
    if primary == "premium_deep_dive_candidate_later" and "premium_deep_dive_candidate_later" not in plan_flags:
        raise ValueError("R50 premium-deep-dive observations require the premium overlay flag")


def _validate_question_observation_result_r50(result: Mapping[str, Any]) -> None:
    data = safe_mapping(result)
    _assert_bodyfree_mapping_input(data, source="p7_r50.question_observation_result")
    if _contains_forbidden_key_ref(data, set(P7_R50_BODY_FREE_FORBIDDEN_FIELD_REFS)):
        raise ValueError("R50 R10 question observation input must not include body, reviewer text, local path, hash, terminal output, or question text")
    for flag_key in ("question_text_included", "draft_question_text_included", "reviewer_free_text_included"):
        if data.get(flag_key) is True:
            raise ValueError("R50 R10 question observation input must keep text-included flags false")
    if data.get("question_trigger_logic_implemented_here") is True or data.get("p8_question_implementation_spec_finalized_here") is True:
        raise ValueError("R50 R10 must not finalize P8 question implementation")


def normalize_p7_r50_question_need_observation_row_bodyfree(
    *,
    question_observation_result: Mapping[str, Any],
    case_row: Mapping[str, Any],
    body_removed: bool = False,
) -> dict[str, Any]:
    """Normalize sanitized reviewer question-need selections into one R50 body-free row.

    The helper records only canonical enum selections.  It does not preserve
    question text, draft question text, reviewer free text, raw input, returned
    surface, local path, or hashes.
    """

    _validate_question_observation_result_r50(question_observation_result)
    result = safe_mapping(question_observation_result)
    case = _case_ref_fields_r50(case_row)
    primary = clean_identifier(result.get("question_need_primary_class"), default="", max_length=160)
    if primary not in P7_R50_QUESTION_NEED_PRIMARY_CLASS_REFS:
        raise ValueError("R50 R10 question observation primary class must use the frozen enum")
    ambiguity_default = ["no_material_ambiguity"] if primary == "no_question_needed_emlis_can_observe" else []
    ambiguity_refs = _assert_identifier_sequence_r50(
        result.get("ambiguity_kind_refs") if result.get("ambiguity_kind_refs") is not None else ambiguity_default,
        source="p7_r50_question_observation.ambiguity_kind_refs",
        allowed_refs=P7_R50_AMBIGUITY_KIND_REFS,
    )
    one_question_fit_ref = clean_identifier(
        result.get("one_question_fit_ref"),
        default=_default_one_question_fit_for_primary_r50(primary),
        max_length=160,
    )
    if one_question_fit_ref not in P7_R50_ONE_QUESTION_FIT_REFS:
        raise ValueError("R50 R10 question observation one_question_fit_ref must use the frozen enum")
    repair_refs = _assert_identifier_sequence_r50(
        result.get("repair_required_refs") if result.get("repair_required_refs") is not None else _default_repair_refs_for_primary_r50(primary),
        source="p7_r50_question_observation.repair_required_refs",
        allowed_refs=P7_R50_REPAIR_REQUIRED_REF_REFS,
    )
    if not repair_refs:
        repair_refs = _default_repair_refs_for_primary_r50(primary)
    plan_flags = _normalize_plan_candidate_flags_r50(primary, result.get("plan_candidate_flags"))
    sanitized_reason_ids = _assert_identifier_sequence_r50(
        result.get("sanitized_reason_ids") if result.get("sanitized_reason_ids") is not None else [primary],
        source="p7_r50_question_observation.sanitized_reason_ids",
        allowed_refs=None,
        limit=40,
    )
    row = {
        "schema_version": P7_R50_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION,
        **case,
        "review_kind": P7_R50_REVIEW_KIND,
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
        "body_removed": bool(body_removed),
        "body_free": True,
    }
    assert_p7_r50_question_need_observation_row_bodyfree_contract(row)
    return row


def assert_p7_r50_question_need_observation_row_bodyfree_contract(
    row: Mapping[str, Any],
    *,
    execution_blocker_rows: Sequence[Mapping[str, Any]] | None = None,
    require_execution_blocker_match: bool = False,
) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R50_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_REQUIRED_FIELD_REFS, source="p7_r50_question_need_observation_row_bodyfree")
    if data.get("schema_version") != P7_R50_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R50 question observation row schema version changed")
    _assert_bodyfree_mapping_input(data, source="p7_r50_question_need_observation_row_bodyfree")
    if data.get("family") not in P5_HUMAN_BLIND_QA_FAMILIES:
        raise ValueError("R50 question observation row family changed")
    if data.get("case_role") not in P7_R48_P5_CASE_ROLE_REFS:
        raise ValueError("R50 question observation row case_role changed")
    if data.get("review_kind") != P7_R50_REVIEW_KIND:
        raise ValueError("R50 question observation review kind changed")
    if data.get("observation_stage") != P7_R50_QUESTION_NEED_OBSERVATION_STAGE_REF:
        raise ValueError("R50 question observation stage changed")
    _assert_identifier_sequence_r50(
        data.get("ambiguity_kind_refs"),
        source="p7_r50_question_observation.ambiguity_kind_refs",
        allowed_refs=P7_R50_AMBIGUITY_KIND_REFS,
    )
    _assert_identifier_sequence_r50(
        data.get("repair_required_refs"),
        source="p7_r50_question_observation.repair_required_refs",
        allowed_refs=P7_R50_REPAIR_REQUIRED_REF_REFS,
    )
    _assert_identifier_sequence_r50(
        data.get("plan_candidate_flags"),
        source="p7_r50_question_observation.plan_candidate_flags",
        allowed_refs=P7_R50_PLAN_CANDIDATE_FLAG_REFS,
    )
    _assert_identifier_sequence_r50(
        data.get("sanitized_reason_ids"),
        source="p7_r50_question_observation.sanitized_reason_ids",
        allowed_refs=None,
        limit=40,
    )
    _validate_question_observation_semantics_r50(
        data,
        execution_blocker_rows=execution_blocker_rows,
        require_execution_blocker_match=require_execution_blocker_match,
    )
    for false_key in ("question_text_included", "draft_question_text_included", "reviewer_free_text_included"):
        if data.get(false_key) is not False:
            raise ValueError(f"R50 question observation row must keep {false_key}=False")
    if not isinstance(data.get("body_removed"), bool):
        raise ValueError("R50 question observation row must carry boolean body_removed")
    return True


def _r10_status_from_r9(r9: Mapping[str, Any]) -> tuple[str, list[str]]:
    if r9.get("blocker_ingestion_status") != "READY_FOR_READFEEL_AND_EXECUTION_BLOCKER_INGESTION":
        return "BLOCKED_BY_R50_9_BLOCKER_INGESTION", ["r9_blocker_ingestion_not_ready"]
    return "READY_FOR_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION", ["r9_blocker_ingestion_ready"]


# ---------------------------------------------------------------------------
# R50-12 / R50-13: pause-abort-expiration protocol and disposal receipt verifier
# ---------------------------------------------------------------------------

__all__ = [
    "P7_R50_CURRENT_SOURCE_R49_HANDOFF_BRIDGE_REFREEZE_SCHEMA_VERSION",
    "P7_R50_SCOPE_SCHEMA_STATUS_ENUM_FREEZE_SCHEMA_VERSION",
    "P7_R50_R0_R1_SCOPE_STATUS_FREEZE_SCHEMA_VERSION",
    "P7_R50_PRIOR_VALIDATION_EVIDENCE_ADOPTION_SCHEMA_VERSION",
    "P7_R50_MANUAL_RUN_DECISION_BODYFREE_SCHEMA_VERSION",
    "P7_R50_R2_R3_MANUAL_RUN_DECISION_FREEZE_SCHEMA_VERSION",
    "P7_R50_LOCAL_ONLY_ROOT_EXPLICIT_ALLOW_EXPORT_PREFLIGHT_SCHEMA_VERSION",
    "P7_R50_REVIEW_SESSION_PROTOCOL_BODYFREE_SCHEMA_VERSION",
    "P7_R50_R4_R5_PREFLIGHT_PROTOCOL_FREEZE_SCHEMA_VERSION",
    "P7_R50_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION",
    "P7_R50_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION",
    "P7_R50_R6_R7_PACKET_REQUEST_RATING_FORM_FREEZE_SCHEMA_VERSION",
    "P7_R50_RATING_CAPTURE_ROW_BODYFREE_SCHEMA_VERSION",
    "P7_R50_READFEEL_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION",
    "P7_R50_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION",
    "P7_R50_RATING_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION",
    "P7_R50_READFEEL_EXECUTION_BLOCKER_INGESTION_BODYFREE_SCHEMA_VERSION",
    "P7_R50_R8_R9_RATING_BLOCKER_INGESTION_FREEZE_SCHEMA_VERSION",
    "P7_R50_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION",
    "P7_R50_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION",
    "P7_R50_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_BODYFREE_SCHEMA_VERSION",
    "P7_R50_R10_R11_QUESTION_NORMALIZER_CONSISTENCY_GUARD_FREEZE_SCHEMA_VERSION",
    "P7_R50_PAUSE_ABORT_EXPIRATION_PROTOCOL_BODYFREE_SCHEMA_VERSION",
    "P7_R50_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION",
    "P7_R50_DISPOSAL_RECEIPT_BUILDER_VERIFIER_BODYFREE_SCHEMA_VERSION",
    "P7_R50_R12_R13_DISPOSAL_PROTOCOL_FREEZE_SCHEMA_VERSION",
    "P7_R50_BODY_FREE_POST_REVIEW_SUMMARY_BODYFREE_SCHEMA_VERSION",
    "P7_R50_P5_CONFIRMED_REPAIR_INCONCLUSIVE_DECISION_BODYFREE_SCHEMA_VERSION",
    "P7_R50_R14_R15_POST_REVIEW_DECISION_FREEZE_SCHEMA_VERSION",
    "P7_R50_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_BODYFREE_SCHEMA_VERSION",
    "P7_R50_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_BODYFREE_SCHEMA_VERSION",
    "P7_R50_R16_R17_P6_P8_CANDIDATE_HANDOFF_FREEZE_SCHEMA_VERSION",
    "P7_R50_NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_BODYFREE_SCHEMA_VERSION",
    "P7_R50_VALIDATION_COMMAND_MATRIX_BODYFREE_SCHEMA_VERSION",
    "P7_R50_R18_R19_NO_LEAK_VALIDATION_MATRIX_FREEZE_SCHEMA_VERSION",
    "P7_R50_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION",
    "P7_R50_STEP",
    "P7_R50_SCOPE",
    "P7_R50_POLICY_KIND",
    "P7_R50_PACKET_KIND",
    "P7_R50_REVIEW_KIND",
    "P7_R50_REQUIRED_CASE_COUNT",
    "P7_R50_DEFAULT_REVIEW_SESSION_ID",
    "P7_R50_FIRST_NEXT_WORK_REF",
    "P7_R50_R0_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R1_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R2_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R3_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R3_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R4_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R4_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R5_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R5_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R6_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R6_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R7_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R7_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R8_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R8_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R9_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R9_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R10_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R10_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R11_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R11_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R12_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R12_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R13_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R13_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R14_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R14_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R15_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R15_REPAIR_RETURN_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R15_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R15_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R16_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R16_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R17_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R17_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R18_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R18_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R19_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R19_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R20_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R20_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R50_R20_POST_FREEZE_NEXT_WORK_REF",
    "P7_R50_EXPLICIT_BODY_FULL_ALLOW_ENV_VAR",
    "P7_R50_EXPLICIT_BODY_FULL_ALLOW_TOKEN_REF",
    "P7_R50_REVIEW_PROMPT_VERSION",
    "P7_R50_REVIEWER_INSTRUCTION_VERSION",
    "P7_R50_RATING_FORM_VERSION",
    "P7_R50_R0_IMPLEMENTED_STEPS",
    "P7_R50_IMPLEMENTED_STEPS",
    "P7_R50_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R50_R0_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R50_R2_IMPLEMENTED_STEPS",
    "P7_R50_R2_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R50_R2_R3_IMPLEMENTED_STEPS",
    "P7_R50_R2_R3_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R50_R4_IMPLEMENTED_STEPS",
    "P7_R50_R4_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R50_R5_IMPLEMENTED_STEPS",
    "P7_R50_R5_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R50_R6_IMPLEMENTED_STEPS",
    "P7_R50_R6_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R50_R7_IMPLEMENTED_STEPS",
    "P7_R50_R7_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R50_R8_IMPLEMENTED_STEPS",
    "P7_R50_R8_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R50_R9_IMPLEMENTED_STEPS",
    "P7_R50_R9_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R50_R10_IMPLEMENTED_STEPS",
    "P7_R50_R10_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R50_R11_IMPLEMENTED_STEPS",
    "P7_R50_R11_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R50_R12_IMPLEMENTED_STEPS",
    "P7_R50_R12_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R50_R13_IMPLEMENTED_STEPS",
    "P7_R50_R13_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R50_R14_IMPLEMENTED_STEPS",
    "P7_R50_R14_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R50_R15_IMPLEMENTED_STEPS",
    "P7_R50_R15_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R50_R16_IMPLEMENTED_STEPS",
    "P7_R50_R16_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R50_R17_IMPLEMENTED_STEPS",
    "P7_R50_R17_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R50_R18_IMPLEMENTED_STEPS",
    "P7_R50_R18_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R50_R19_IMPLEMENTED_STEPS",
    "P7_R50_R19_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R50_R20_IMPLEMENTED_STEPS",
    "P7_R50_R20_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R50_REVIEW_SESSION_STATUS_REFS",
    "P7_R50_INITIAL_REVIEW_SESSION_STATUS_REF",
    "P7_R50_MANUAL_RUN_DECISION_REFS",
    "P7_R50_EXECUTION_BLOCKER_ID_REFS",
    "P7_R50_EXECUTION_BLOCKER_STATUS_REFS",
    "P7_R50_QUESTION_NEED_PRIMARY_CLASS_REFS",
    "P7_R50_AMBIGUITY_KIND_REFS",
    "P7_R50_ONE_QUESTION_FIT_REFS",
    "P7_R50_REPAIR_REQUIRED_REF_REFS",
    "P7_R50_REVIEWER_VISIBLE_FIELD_REFS",
    "P7_R50_REVIEWER_HIDDEN_FIELD_REFS",
    "P7_R50_REVIEW_SESSION_PROTOCOL_STATUS_REFS",
    "P7_R50_BODY_FULL_PACKET_GENERATION_REQUEST_STATUS_REFS",
    "P7_R50_REVIEWER_INSTRUCTION_RATING_FORM_STATUS_REFS",
    "P7_R50_RATING_VERDICT_REFS",
    "P7_R50_RATING_ROW_NORMALIZER_STATUS_REFS",
    "P7_R50_BLOCKER_INGESTION_STATUS_REFS",
    "P7_R50_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_STATUS_REFS",
    "P7_R50_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_STATUS_REFS",
    "P7_R50_PAUSE_ABORT_EXPIRATION_PROTOCOL_STATUS_REFS",
    "P7_R50_DISPOSAL_RECEIPT_BUILDER_VERIFIER_STATUS_REFS",
    "P7_R50_DISPOSAL_RECEIPT_VERIFICATION_STATUS_REFS",
    "P7_R50_ABORT_EXPIRATION_TERMINAL_STATUS_REFS",
    "P7_R50_DISPOSAL_VERIFIED_FOR_CANDIDATE_STATUS_REFS",
    "P7_R50_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_STATUS_REFS",
    "P7_R50_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_STATUS_REFS",
    "P7_R50_NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_STATUS_REFS",
    "P7_R50_VALIDATION_COMMAND_MATRIX_STATUS_REFS",
    "P7_R50_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_STATUS_REFS",
    "P7_R50_VALIDATION_COMMAND_GROUP_REFS",
    "P7_R50_VALIDATION_COMMAND_REQUIRED_GROUP_REFS",
    "P7_R50_VALIDATION_COMMAND_OPTIONAL_GROUP_REFS",
    "P7_R50_PRODUCTION_TOUCH_CANDIDATE_FILE_REFS",
    "P7_R50_OPTIONAL_TOUCH_CANDIDATE_FILE_REFS",
    "P7_R50_ALLOWED_PRODUCTION_TOUCH_FILE_REFS",
    "P7_R50_ALLOWED_TEST_TOUCH_FILE_REFS",
    "P7_R50_ALLOWED_ACTUAL_TOUCHED_FILE_REFS",
    "P7_R50_RN_PRODUCTION_NO_TOUCH_FILE_REFS",
    "P7_R50_RN_CONTRACT_OPTIONAL_NO_TOUCH_TEST_REFS",
    "P7_R50_EXPLICIT_NO_TOUCH_FILE_REFS",
    "P7_R50_EXPLICIT_NO_TOUCH_AREA_REFS",
    "P7_R50_R20_CURRENT_PATCH_EXPECTED_TOUCHED_FILE_REFS",
    "P7_R50_VALIDATION_R50_TARGET_TEST_FILE_REFS",
    "P7_R50_VALIDATION_SYNTAX_FILE_REFS",
    "P7_R50_NO_BODY_LEAK_TRUE_FLAG_REFS",
    "P7_R50_QUESTION_TEXT_FIELD_REFS",
    "P7_R50_REVIEWER_FREE_TEXT_FIELD_REFS",
    "P7_R50_LOCAL_PATH_HASH_FIELD_REFS",
    "P7_R50_TERMINAL_OUTPUT_FIELD_REFS",
    "P7_R50_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_REQUIRED_CONDITION_REFS",
    "P7_R50_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_REQUIREMENT_REFS",
    "P7_R50_REVIEWER_CHECK_ITEM_REFS",
    "P7_R50_REQUIRED_REVIEWER_CHECK_LABEL_REFS",
    "P7_R50_EXECUTION_BLOCKER_KIND_REFS",
    "P7_R50_RATING_CAPTURE_ROW_BODYFREE_REQUIRED_FIELD_REFS",
    "P7_R50_READFEEL_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS",
    "P7_R50_EXECUTION_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS",
    "P7_R50_PLAN_CANDIDATE_FLAG_REFS",
    "P7_R50_QUESTION_NEED_OBSERVATION_STAGE_REF",
    "P7_R50_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_REQUIRED_FIELD_REFS",
    "P7_R50_SOURCE_SNAPSHOT_REFS",
    "P7_R50_R0_R1_FALSE_KEY_REFS",
    "P7_R50_BODY_FREE_FORBIDDEN_FIELD_REFS",
    "P7_R50_R49_HANDOFF_REQUIRED_FIELD_REFS",
    "P7_R50_BRIDGE_RULE_REQUIRED_FIELD_REFS",
    "P7_R50_CURRENT_SOURCE_R49_HANDOFF_BRIDGE_REFREEZE_REQUIRED_FIELD_REFS",
    "P7_R50_SCOPE_SCHEMA_STATUS_ENUM_FREEZE_REQUIRED_FIELD_REFS",
    "P7_R50_R0_R1_SCOPE_STATUS_FREEZE_REQUIRED_FIELD_REFS",
    "P7_R50_PRIOR_VALIDATION_EVIDENCE_GROUP_REFS",
    "P7_R50_PRIOR_VALIDATION_EVIDENCE_ROW_REQUIRED_FIELD_REFS",
    "P7_R50_PRIOR_VALIDATION_EVIDENCE_ADOPTION_REQUIRED_FIELD_REFS",
    "P7_R50_MANUAL_RUN_PRECONDITION_FLAG_REFS",
    "P7_R50_R3_FALSE_KEY_REFS",
    "P7_R50_R4_FALSE_KEY_REFS",
    "P7_R50_R5_FALSE_KEY_REFS",
    "P7_R50_R6_FALSE_KEY_REFS",
    "P7_R50_R7_FALSE_KEY_REFS",
    "P7_R50_R8_FALSE_KEY_REFS",
    "P7_R50_R9_FALSE_KEY_REFS",
    "P7_R50_R10_FALSE_KEY_REFS",
    "P7_R50_R11_FALSE_KEY_REFS",
    "P7_R50_R12_FALSE_KEY_REFS",
    "P7_R50_R13_FALSE_KEY_REFS",
    "P7_R50_R14_FALSE_KEY_REFS",
    "P7_R50_R15_FALSE_KEY_REFS",
    "P7_R50_R16_FALSE_KEY_REFS",
    "P7_R50_R17_FALSE_KEY_REFS",
    "P7_R50_R18_FALSE_KEY_REFS",
    "P7_R50_R19_FALSE_KEY_REFS",
    "P7_R50_R20_ALLOWED_TRUE_KEY_REFS",
    "P7_R50_R20_FALSE_KEY_REFS",
    "P7_R50_MANUAL_RUN_DECISION_BODYFREE_REQUIRED_FIELD_REFS",
    "P7_R50_R2_R3_MANUAL_RUN_DECISION_FREEZE_REQUIRED_FIELD_REFS",
    "P7_R50_LOCAL_ONLY_ROOT_EXPLICIT_ALLOW_EXPORT_PREFLIGHT_REQUIRED_FIELD_REFS",
    "P7_R50_REVIEW_SESSION_PROTOCOL_BODYFREE_REQUIRED_FIELD_REFS",
    "P7_R50_R4_R5_PREFLIGHT_PROTOCOL_FREEZE_REQUIRED_FIELD_REFS",
    "P7_R50_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_REQUIRED_FIELD_REFS",
    "P7_R50_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_REQUIRED_FIELD_REFS",
    "P7_R50_R6_R7_PACKET_REQUEST_RATING_FORM_FREEZE_REQUIRED_FIELD_REFS",
    "P7_R50_RATING_ROW_NORMALIZER_BODYFREE_REQUIRED_FIELD_REFS",
    "P7_R50_READFEEL_EXECUTION_BLOCKER_INGESTION_BODYFREE_REQUIRED_FIELD_REFS",
    "P7_R50_R8_R9_RATING_BLOCKER_INGESTION_FREEZE_REQUIRED_FIELD_REFS",
    "P7_R50_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_BODYFREE_REQUIRED_FIELD_REFS",
    "P7_R50_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_BODYFREE_REQUIRED_FIELD_REFS",
    "P7_R50_R10_R11_QUESTION_NORMALIZER_CONSISTENCY_GUARD_FREEZE_REQUIRED_FIELD_REFS",
    "P7_R50_DISPOSAL_RECEIPT_BODYFREE_REQUIRED_FIELD_REFS",
    "P7_R50_DISPOSAL_RECEIPT_FORBIDDEN_FIELD_REFS",
    "P7_R50_PAUSE_ABORT_EXPIRATION_PROTOCOL_BODYFREE_REQUIRED_FIELD_REFS",
    "P7_R50_DISPOSAL_RECEIPT_BUILDER_VERIFIER_BODYFREE_REQUIRED_FIELD_REFS",
    "P7_R50_R12_R13_DISPOSAL_PROTOCOL_FREEZE_REQUIRED_FIELD_REFS",
    "P7_R50_BODY_FREE_POST_REVIEW_SUMMARY_BODYFREE_REQUIRED_FIELD_REFS",
    "P7_R50_P5_CONFIRMED_REPAIR_INCONCLUSIVE_DECISION_BODYFREE_REQUIRED_FIELD_REFS",
    "P7_R50_R14_R15_POST_REVIEW_DECISION_FREEZE_REQUIRED_FIELD_REFS",
    "P7_R50_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_BODYFREE_REQUIRED_FIELD_REFS",
    "P7_R50_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_BODYFREE_REQUIRED_FIELD_REFS",
    "P7_R50_R16_R17_P6_P8_CANDIDATE_HANDOFF_FREEZE_REQUIRED_FIELD_REFS",
    "P7_R50_NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_BODYFREE_REQUIRED_FIELD_REFS",
    "P7_R50_VALIDATION_COMMAND_ROW_BODYFREE_REQUIRED_FIELD_REFS",
    "P7_R50_VALIDATION_COMMAND_MATRIX_BODYFREE_REQUIRED_FIELD_REFS",
    "P7_R50_R18_R19_NO_LEAK_VALIDATION_MATRIX_FREEZE_REQUIRED_FIELD_REFS",
    "P7_R50_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FREEZE_REQUIRED_FIELD_REFS",
    "P7_R50_PAUSE_ABORT_EXPIRATION_PROTOCOL_REQUIRED_FIELD_REFS",
    "build_p7_r50_current_source_r49_handoff_bridge_refreeze",
    "build_p7_r50_current_source_r49_handoff_refreeze",
    "build_p7_r50_scope_schema_status_enum_freeze",
    "build_p7_r50_r0_r1_scope_status_freeze",
    "build_p7_r50_prior_validation_evidence_adoption",
    "build_p7_r50_manual_run_decision_bodyfree",
    "build_p7_r50_r2_r3_manual_run_decision_freeze",
    "build_p7_r50_local_only_root_explicit_allow_export_denylist_preflight",
    "build_p7_r50_local_body_full_generation_preflight",
    "build_p7_r50_review_session_protocol_bodyfree",
    "build_p7_r50_r4_r5_preflight_protocol_freeze",
    "build_p7_r50_local_only_body_full_packet_generation_request",
    "build_p7_r50_reviewer_instruction_rating_form_freeze",
    "build_p7_r50_r6_r7_packet_request_rating_form_freeze",
    "normalize_p7_r50_rating_capture_row_bodyfree",
    "build_p7_r50_readfeel_blocker_row_bodyfree",
    "build_p7_r50_execution_blocker_row_bodyfree",
    "build_p7_r50_rating_row_normalizer_bodyfree",
    "build_p7_r50_rating_row_normalizer",
    "build_p7_r50_readfeel_blocker_execution_blocker_ingestion_bodyfree",
    "build_p7_r50_readfeel_blocker_execution_blocker_ingestion",
    "build_p7_r50_r8_r9_rating_blocker_ingestion_freeze",
    "normalize_p7_r50_question_need_observation_row_bodyfree",
    "build_p7_r50_question_need_observation_row_normalizer_bodyfree",
    "build_p7_r50_question_need_observation_row_normalizer",
    "build_p7_r50_rating_question_observation_consistency_guard_bodyfree",
    "build_p7_r50_rating_question_observation_consistency_guard",
    "build_p7_r50_r10_r11_question_normalizer_consistency_guard_freeze",
    "build_p7_r50_pause_abort_expiration_protocol_bodyfree",
    "build_p7_r50_disposal_receipt_bodyfree",
    "build_p7_r50_disposal_receipt_builder_verifier_bodyfree",
    "build_p7_r50_r12_r13_disposal_protocol_freeze",
    "build_p7_r50_body_free_post_review_summary_bodyfree",
    "build_p7_r50_bodyfree_post_review_summary_builder",
    "build_p7_r50_p5_confirmed_repair_return_inconclusive_decision_bodyfree",
    "build_p7_r50_p5_review_decision_bodyfree",
    "build_p7_r50_r14_r15_post_review_decision_freeze",
    "build_p7_r50_p6_limited_human_readfeel_candidate_handoff_bodyfree",
    "build_p7_r50_p6_limited_human_readfeel_candidate_handoff",
    "build_p7_r50_p8_question_design_material_candidate_handoff_bodyfree",
    "build_p7_r50_p8_question_design_material_candidate_handoff",
    "build_p7_r50_r16_r17_p6_p8_candidate_handoff_freeze",
    "build_p7_r50_no_body_leak_no_question_text_guard_bodyfree",
    "build_p7_r50_validation_command_matrix_bodyfree",
    "build_p7_r50_validation_command_matrix",
    "build_p7_r50_r18_r19_no_leak_validation_matrix_freeze",
    "build_p7_r50_touch_candidate_no_touch_boundary_freeze",
    "verify_p7_r50_disposal_receipt_bodyfree",
    "assert_p7_r50_prior_validation_evidence_row_contract",
    "assert_p7_r50_prior_validation_evidence_adoption_contract",
    "assert_p7_r50_manual_run_decision_bodyfree_contract",
    "assert_p7_r50_r2_r3_manual_run_decision_freeze_contract",
    "assert_p7_r50_local_only_root_explicit_allow_export_denylist_preflight_contract",
    "assert_p7_r50_review_session_protocol_bodyfree_contract",
    "assert_p7_r50_r4_r5_preflight_protocol_freeze_contract",
    "assert_p7_r50_local_only_body_full_packet_generation_request_contract",
    "assert_p7_r50_reviewer_instruction_rating_form_freeze_contract",
    "assert_p7_r50_r6_r7_packet_request_rating_form_freeze_contract",
    "assert_p7_r50_rating_capture_row_bodyfree_contract",
    "assert_p7_r50_readfeel_blocker_row_bodyfree_contract",
    "assert_p7_r50_execution_blocker_row_bodyfree_contract",
    "assert_p7_r50_rating_row_normalizer_bodyfree_contract",
    "assert_p7_r50_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract",
    "assert_p7_r50_r8_r9_rating_blocker_ingestion_freeze_contract",
    "assert_p7_r50_question_need_observation_row_bodyfree_contract",
    "assert_p7_r50_question_need_observation_row_normalizer_bodyfree_contract",
    "assert_p7_r50_rating_vs_question_observation_consistency",
    "assert_p7_r50_rating_question_observation_consistency_guard_bodyfree_contract",
    "assert_p7_r50_r10_r11_question_normalizer_consistency_guard_freeze_contract",
    "assert_p7_r50_pause_abort_expiration_protocol_bodyfree_contract",
    "assert_p7_r50_disposal_receipt_bodyfree_contract",
    "assert_p7_r50_disposal_receipt_builder_verifier_bodyfree_contract",
    "assert_p7_r50_r12_r13_disposal_protocol_freeze_contract",
    "assert_p7_r50_body_free_post_review_summary_bodyfree_contract",
    "assert_p7_r50_p5_confirmed_repair_return_inconclusive_decision_bodyfree_contract",
    "assert_p7_r50_r14_r15_post_review_decision_freeze_contract",
    "assert_p7_r50_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract",
    "assert_p7_r50_p8_question_design_material_candidate_handoff_bodyfree_contract",
    "assert_p7_r50_r16_r17_p6_p8_candidate_handoff_freeze_contract",
    "assert_p7_r50_no_body_leak_no_question_text_guard_bodyfree_contract",
    "assert_p7_r50_validation_command_row_bodyfree_contract",
    "assert_p7_r50_validation_command_matrix_bodyfree_contract",
    "assert_p7_r50_r18_r19_no_leak_validation_matrix_freeze_contract",
    "assert_p7_r50_touch_candidate_no_touch_boundary_freeze_contract",
    "assert_p7_r50_touch_candidate_no_touch_actual_touched_file_refs_contract",
    "assert_p7_r50_r49_handoff_contract",
    "assert_p7_r50_p7_p8_bridge_rule_contract",
    "assert_p7_r50_current_source_r49_handoff_bridge_refreeze_contract",
    "assert_p7_r50_scope_schema_status_enum_freeze_contract",
    "assert_p7_r50_r0_r1_scope_status_freeze_contract",
]