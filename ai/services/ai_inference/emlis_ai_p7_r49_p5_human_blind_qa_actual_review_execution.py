# -*- coding: utf-8 -*-
"""P7-R49 P5 Human Blind QA actual review execution helpers.

R49-0 refreezes the current local source, the completed R48 handoff, and the
P7/P8 Bridge rule that question-need observations are collected as body-free
review material without implementing observation questions in P7.

R49-1 fixes only the R49 scope, schema-version constants, review-session status
enum, and question-need observation enum refs.
R49-2 validates the R48 24-case matrix handoff as body-free controller
material without exposing reviewer-hidden controller refs.
R49-3 performs the local-only actual packet generation preflight without
materializing body-full packets.
R49-4 builds the body-free actual-review session protocol.
R49-5 connects sanitized rating ingestion to the existing R48 body-free
rating-row normalizer.
R49-6 connects blocker / execution-blocker ingestion to the existing R48
body-free row builders while keeping readfeel blockers and execution blockers
separate.
R49-7 freezes the body-free question-need observation row schema/enum refs
without creating question text, question triggers, question rows, API/DB/RN
changes, P8 start permission, or release permission.
R49-8 normalizes sanitized question-need observation selections into body-free
rows while still treating actual human review rows as not materialized here.
R49-9 guards rating rows against question-need observations being used to hide
P5 readfeel, surface, or gate-boundary repair requirements.
R49-10 builds body-free question-need observation summaries for later P8
design material without starting P8 or materializing actual review summaries.
R49-11 connects R49 to the R48 body-free disposal receipt schema while
keeping actual disposal execution and body-full packet handling out of scope.
R49-12 builds a body-free review handoff summary by reusing the R48 summary
shape and adding question-observation/disposal state.
R49-13 connects that handoff to the R48 P5 confirmed-candidate gate while
requiring question-observation completeness and keeping P6/P7/P8/release closed.
R49-14 builds a P6 limited-human-readfeel start-candidate handoff without
promoting the candidate into P6 start permission.
R49-15 builds a P8 question-design material candidate handoff without starting
P8, finalizing question design, or implementing question trigger/API/DB/RN work.
R49-16 freezes a no-body-leak/no-question-text guard over the R49 body-free
materials and refuses body-full, reviewer-free-text, or question-text keys.
R49-17 builds a validation command matrix as body-free reference material without
executing commands or converting collect-only/RN contract checks into release claims.
R49-18 freezes the R49 touch-candidate/no-touch boundary so the work does not
spread into runtime, RN, API, DB, public-meta, P8, or release areas.
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
from emlis_ai_p7_r46_p5_p6_human_readfeel_handoff_material import (
    P5_HUMAN_BLIND_QA_FAMILIES,
    P5_HUMAN_BLIND_QA_RATING_AXES,
    P5_HUMAN_BLIND_QA_TARGETS,
    P6_LIMITED_HUMAN_READFEEL_HOLD_REF,
    P6_LIMITED_HUMAN_READFEEL_RETURN_HOLD_REF,
    P6_LIMITED_READFEEL_REVIEW_FAMILIES,
    P6_NO_CONNECT_FAMILIES,
    P6_LIMITED_READFEEL_RATING_AXES,
    P6_LIMITED_READFEEL_TARGETS,
    P7_R46_P6_LIMITED_HUMAN_READFEEL_HANDOFF_SCHEMA_VERSION,
    assert_p6_limited_human_readfeel_handoff_material_contract,
    build_p6_limited_human_readfeel_handoff_material,
)
from emlis_ai_p7_r47_local_review_packet_policy import (
    P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
    P7_R47_DISPOSAL_STATUSES,
    P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR,
    P7_R47_P5_FIRST_FORMAL_MINIMUMS,
    P7_R47_P5_REVIEWER_FACING_ALLOWED_FIELD_REFS,
    P7_R47_P5_REVIEWER_FACING_FORBIDDEN_FIELD_REFS,
    P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
    p7_r47_export_candidate_deny_reasons,
)
from emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet import (
    P7_R48_P5_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
    P7_R48_P5_BLOCKER_KINDS,
    P7_R48_P5_BLOCKER_ROW_REQUIRED_FIELD_REFS,
    P7_R48_P5_BLOCKER_STATUSES,
    P7_R48_BODY_FULL_PACKET_MATERIALIZATION_GUARD_SCHEMA_VERSION,
    P7_R48_BLOCKER_EXECUTION_BLOCKER_ROW_BUILDER_SCHEMA_VERSION,
    P7_R48_EXECUTION_BLOCKER_ID_REFS,
    P7_R48_EXECUTION_BLOCKER_KIND_REFS,
    P7_R48_EXECUTION_BLOCKER_STATUS_REFS,
    P7_R48_P5_CASE_MATRIX_ROW_FIELD_REFS,
    P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION,
    P7_R48_P5_CONFIRMED_CANDIDATE_REQUIRED_CONDITION_REFS,
    P7_R48_P5_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION,
    P7_R48_DISPOSAL_RECEIPT_BUILDER_SCHEMA_VERSION,
    P7_R48_P5_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS,
    P7_R48_P5_DISPOSAL_RECEIPT_FORBIDDEN_FIELD_REFS,
    P7_R48_P5_CONFIRMED_ALLOWED_DISPOSAL_STATUS_REFS,
    P7_R48_P5_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
    P7_R48_P5_EXECUTION_BLOCKER_ROW_REQUIRED_FIELD_REFS,
    P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION,
    P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION,
    P7_R48_P5_RATING_BLOCKER_FORBIDDEN_FIELD_REFS,
    P7_R48_P5_RATING_ROW_REQUIRED_FIELD_REFS,
    P7_R48_P5_REVIEW_QUESTION_REFS,
    P7_R48_P5_REVIEWABLE_VERDICTS,
    P7_R48_P5_REVIEWER_PACKET_BODY_FIELD_REFS,
    P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_CONTROL_FIELD_REFS,
    P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_FORBIDDEN_FIELD_REFS,
    P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_REQUIRED_FIELD_REFS,
    P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION,
    P7_R48_P5_REVIEWER_PACKET_REVIEWER_VISIBLE_FIELD_REFS,
    P7_R48_P5_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION,
    P7_R48_R2_R3_LOCAL_STORAGE_CASE_MATRIX_FREEZE_SCHEMA_VERSION,
    P7_R48_PACKET_KIND,
    P7_R48_RATING_ROW_NORMALIZER_SCHEMA_VERSION,
    P7_R48_READFEEL_BLOCKER_ID_REFS,
    P7_R48_REQUIRED_UNRESOLVED_HOLD_REFS,
    P7_R48_REVIEW_KIND,
    P7_R48_REVIEW_PROMPT_VERSION,
    P7_R48_SANITIZED_REASON_ID_REFS,
    P7_R48_SCOPE,
    P7_R48_STEP,
    P7_R48_R18_IMPLEMENTED_STEPS,
    P7_R48_R18_NEXT_REQUIRED_STEP_REF,
    P7_R48_R18_NOT_YET_IMPLEMENTED_STEPS,
    P7_R48_R48_TARGET_TEST_REFS,
    P7_R48_R47_TARGET_REGRESSION_TEST_REFS,
    P7_R48_R46_HANDOFF_REGRESSION_TEST_REFS,
    P7_R48_DISPLAY_CONTRACT_REGRESSION_TEST_REFS,
    P7_R48_P5_CORE_SUBSET_REGRESSION_TEST_REFS,
    P7_R48_RN_CONTRACT_OPTIONAL_TEST_REFS,
    P7_R48_RN_CONTRACT_COMMAND_REFS,
    P7_R48_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION,
    assert_p7_r48_body_full_packet_materialization_guard_contract,
    assert_p7_r48_blocker_execution_blocker_row_builder_policy_contract,
    assert_p7_r48_p5_first_formal_review_case_matrix_contract,
    assert_p7_r48_p5_blocker_row_bodyfree_contract,
    assert_p7_r48_p5_execution_blocker_row_bodyfree_contract,
    assert_p7_r48_p5_rating_row_bodyfree_contract,
    assert_p7_r48_p5_disposal_receipt_bodyfree_contract,
    assert_p7_r48_rating_row_normalizer_policy_contract,
    assert_p7_r48_r2_r3_local_storage_case_matrix_freeze_contract,
    assert_p7_r48_touch_candidate_no_touch_boundary_freeze_contract,
    build_p7_r48_body_full_packet_materialization_guard,
    build_p7_r48_blocker_execution_blocker_row_builder_policy,
    build_p7_r48_rating_row_normalizer_policy,
    build_p7_r48_p5_blocker_row_bodyfree,
    build_p7_r48_p5_execution_blocker_row_bodyfree,
    build_p7_r48_p5_disposal_receipt_bodyfree,
    build_p7_r48_p5_review_handoff_summary_bodyfree,
    build_p7_r48_p5_confirmed_candidate_gate_bodyfree,
    build_p7_r48_r2_r3_local_storage_case_matrix_freeze,
    build_p7_r48_touch_candidate_no_touch_boundary_freeze,
    normalize_p7_r48_p5_rating_row_bodyfree,
    P7_R48_P5_REVIEW_HANDOFF_SUMMARY_REQUIRED_FIELD_REFS,
    P7_R48_P5_CONFIRMED_CANDIDATE_GATE_SCHEMA_VERSION,
    P7_R48_P5_CONFIRMED_CANDIDATE_GATE_REQUIRED_FIELD_REFS,
    assert_p7_r48_p5_review_handoff_summary_bodyfree_contract,
    assert_p7_r48_p5_confirmed_candidate_gate_bodyfree_contract,
)

P7_R49_CURRENT_SOURCE_R48_HANDOFF_BRIDGE_REFREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r49.current_source_r48_handoff_bridge_refreeze.v1"
)
P7_R49_REVIEW_SESSION_ENVELOPE_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r49.review_session_envelope.bodyfree.v1"
)
P7_R49_R0_R1_SCOPE_STATUS_FREEZE_SCHEMA_VERSION: Final = "cocolon.emlis.p7_r49.r0_r1_scope_status_freeze.v1"
P7_R49_R0_R1_SCOPE_STATUS_ENUM_FREEZE_SCHEMA_VERSION: Final = P7_R49_R0_R1_SCOPE_STATUS_FREEZE_SCHEMA_VERSION
P7_R49_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r49.question_need_observation_row.bodyfree.v1"
)
P7_R49_QUESTION_NEED_OBSERVATION_SUMMARY_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r49.question_need_observation_summary.bodyfree.v1"
)
P7_R49_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r49.review_handoff_summary.bodyfree.v1"
)
P7_R49_R48_CASE_MATRIX_HANDOFF_VALIDATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r49.r48_case_matrix_handoff_validation.bodyfree.v1"
)
P7_R49_LOCAL_ONLY_ACTUAL_PACKET_GENERATION_PREFLIGHT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r49.local_only_actual_packet_generation_preflight.bodyfree.v1"
)
P7_R49_R2_R3_CASE_MATRIX_PREFLIGHT_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r49.r2_r3_case_matrix_preflight_freeze.bodyfree.v1"
)
P7_R49_ACTUAL_REVIEW_SESSION_PROTOCOL_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r49.actual_review_session_protocol.bodyfree.v1"
)
P7_R49_RATING_ROW_INGESTION_R48_NORMALIZER_CONNECTION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r49.rating_row_ingestion_r48_normalizer_connection.bodyfree.v1"
)
P7_R49_R4_R5_PROTOCOL_RATING_CONNECTION_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r49.r4_r5_protocol_rating_connection_freeze.bodyfree.v1"
)
P7_R49_BLOCKER_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r49.blocker_execution_blocker_ingestion.bodyfree.v1"
)
P7_R49_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_ENUM_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r49.question_need_observation_row_schema_enum_freeze.bodyfree.v1"
)
P7_R49_R6_R7_BLOCKER_QUESTION_SCHEMA_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r49.r6_r7_blocker_question_schema_freeze.bodyfree.v1"
)
P7_R49_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r49.question_need_observation_row_normalizer.bodyfree.v1"
)
P7_R49_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r49.rating_question_observation_consistency_guard.bodyfree.v1"
)
P7_R49_R8_R9_QUESTION_NORMALIZER_CONSISTENCY_GUARD_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r49.r8_r9_question_normalizer_consistency_guard_freeze.bodyfree.v1"
)
P7_R49_DISPOSAL_RECEIPT_CONNECTION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r49.disposal_receipt_connection.bodyfree.v1"
)
P7_R49_R10_R11_QUESTION_SUMMARY_DISPOSAL_CONNECTION_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r49.r10_r11_question_summary_disposal_connection_freeze.bodyfree.v1"
)
P7_R49_P5_CONFIRMED_CANDIDATE_GATE_CONNECTION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r49.p5_confirmed_candidate_gate_connection.bodyfree.v1"
)
P7_R49_R12_R13_REVIEW_HANDOFF_P5_GATE_CONNECTION_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r49.r12_r13_review_handoff_p5_gate_connection_freeze.bodyfree.v1"
)
P7_R49_P6_LIMITED_HUMAN_READFEEL_START_CANDIDATE_HANDOFF_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r49.p6_limited_human_readfeel_start_candidate_handoff.bodyfree.v1"
)
P7_R49_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r49.p8_question_design_material_candidate_handoff.bodyfree.v1"
)
P7_R49_R14_R15_P6_P8_CANDIDATE_HANDOFF_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r49.r14_r15_p6_p8_candidate_handoff_freeze.bodyfree.v1"
)
P7_R49_NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r49.no_body_leak_no_question_text_guard.bodyfree.v1"
)
P7_R49_VALIDATION_COMMAND_MATRIX_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r49.validation_command_matrix.bodyfree.v1"
)
P7_R49_R16_R17_NO_BODY_LEAK_VALIDATION_COMMAND_MATRIX_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r49.r16_r17_no_body_leak_validation_command_matrix_freeze.bodyfree.v1"
)
P7_R49_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r49.touch_candidate_no_touch_boundary_freeze.bodyfree.v1"
)

P7_R49_STEP: Final = "R49_P5HumanBlindQAActualReviewExecution_QuestionNeedObservation_20260619"
P7_R49_SCOPE: Final = "p5_human_blind_qa_actual_review_execution_question_need_observation_capture"
P7_R49_POLICY_KIND: Final = "p5_human_blind_qa_actual_review_execution_question_need_observation_policy"
P7_R49_PACKET_KIND: Final = P7_R48_PACKET_KIND
P7_R49_REVIEW_KIND: Final = P7_R48_REVIEW_KIND
P7_R49_REQUIRED_TOTAL_CASES: Final = 24
P7_R49_DEFAULT_REVIEW_SESSION_ID: Final = "p7_r49_p5_actual_review_question_observation_session"
P7_R49_REVIEW_SESSION_DEFAULT_REF: Final = P7_R49_DEFAULT_REVIEW_SESSION_ID
P7_R49_FIRST_NEXT_WORK_REF: Final = "p5_human_blind_qa_actual_review_execution_question_need_observation_capture"
P7_R49_R0_NEXT_REQUIRED_STEP_REF: Final = "R49-1_scope_schema_version_status_enum_freeze"
P7_R49_R1_NEXT_REQUIRED_STEP_REF: Final = "R49-2_r48_case_matrix_handoff_validation"

P7_R49_R0_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = ("R49-0_current_source_r48_handoff_bridge_rule_refreeze",)
P7_R49_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R49-0_current_source_r48_handoff_bridge_rule_refreeze",
    "R49-1_scope_schema_version_status_enum_freeze",
)
P7_R49_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R2_r48_case_matrix_handoff_validation",
    "R3_local_only_actual_packet_generation_preflight",
    "R4_actual_review_session_protocol_builder",
    "R5_rating_row_ingestion_r48_normalizer_connection",
    "R6_blocker_execution_blocker_ingestion",
    "R7_question_need_observation_row_schema_enum_freeze",
    "R8_question_need_observation_row_normalizer",
    "R9_rating_vs_question_observation_consistency_guard",
    "R10_question_need_observation_summary_builder",
    "R11_disposal_receipt_connection",
    "R12_review_handoff_summary_builder",
    "R13_p5_confirmed_candidate_gate_connection",
    "R14_p6_limited_human_readfeel_start_candidate_handoff",
    "R15_p8_question_design_material_candidate_handoff",
    "R16_no_body_leak_no_question_text_guard",
    "R17_validation_command_matrix",
    "R18_touch_candidate_no_touch_boundary_freeze",
)
P7_R49_R0_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R49-1_scope_schema_version_status_enum_freeze",
    *P7_R49_NOT_YET_IMPLEMENTED_STEPS,
)
P7_R49_R2_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R49_IMPLEMENTED_STEPS,
    "R2_r48_case_matrix_handoff_validation",
)
P7_R49_R2_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R3_local_only_actual_packet_generation_preflight",
    "R4_actual_review_session_protocol_builder",
    "R5_rating_row_ingestion_r48_normalizer_connection",
    "R6_blocker_execution_blocker_ingestion",
    "R7_question_need_observation_row_schema_enum_freeze",
    "R8_question_need_observation_row_normalizer",
    "R9_rating_vs_question_observation_consistency_guard",
    "R10_question_need_observation_summary_builder",
    "R11_disposal_receipt_connection",
    "R12_review_handoff_summary_builder",
    "R13_p5_confirmed_candidate_gate_connection",
    "R14_p6_limited_human_readfeel_start_candidate_handoff",
    "R15_p8_question_design_material_candidate_handoff",
    "R16_no_body_leak_no_question_text_guard",
    "R17_validation_command_matrix",
    "R18_touch_candidate_no_touch_boundary_freeze",
)
P7_R49_R2_R3_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R49_R2_IMPLEMENTED_STEPS,
    "R3_local_only_actual_packet_generation_preflight",
)
P7_R49_R2_R3_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R49_R2_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R49_R2_NEXT_REQUIRED_STEP_REF: Final = "R49-3_local_only_actual_packet_generation_preflight"
P7_R49_R3_NEXT_REQUIRED_STEP_REF: Final = "R49-4_actual_review_session_protocol_builder"
P7_R49_R4_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R49_R2_R3_IMPLEMENTED_STEPS,
    "R4_actual_review_session_protocol_builder",
)
P7_R49_R4_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R49_R2_R3_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R49_R5_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R49_R4_IMPLEMENTED_STEPS,
    "R5_rating_row_ingestion_r48_normalizer_connection",
)
P7_R49_R5_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R49_R4_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R49_R4_NEXT_REQUIRED_STEP_REF: Final = "R49-5_rating_row_ingestion_r48_normalizer_connection"
P7_R49_R5_NEXT_REQUIRED_STEP_REF: Final = "R49-6_blocker_execution_blocker_ingestion"
P7_R49_R6_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R49_R5_IMPLEMENTED_STEPS,
    "R6_blocker_execution_blocker_ingestion",
)
P7_R49_R6_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R49_R5_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R49_R7_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R49_R6_IMPLEMENTED_STEPS,
    "R7_question_need_observation_row_schema_enum_freeze",
)
P7_R49_R7_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R49_R6_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R49_R6_NEXT_REQUIRED_STEP_REF: Final = "R49-7_question_need_observation_row_schema_enum_freeze"
P7_R49_R7_NEXT_REQUIRED_STEP_REF: Final = "R49-8_question_need_observation_row_normalizer"
P7_R49_R8_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R49_R7_IMPLEMENTED_STEPS,
    "R8_question_need_observation_row_normalizer",
)
P7_R49_R8_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R49_R7_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R49_R9_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R49_R8_IMPLEMENTED_STEPS,
    "R9_rating_vs_question_observation_consistency_guard",
)
P7_R49_R9_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R49_R8_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R49_R8_NEXT_REQUIRED_STEP_REF: Final = "R49-9_rating_vs_question_observation_consistency_guard"
P7_R49_R9_NEXT_REQUIRED_STEP_REF: Final = "R49-10_question_need_observation_summary_builder"
P7_R49_R10_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R49_R9_IMPLEMENTED_STEPS,
    "R10_question_need_observation_summary_builder",
)
P7_R49_R10_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R49_R9_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R49_R11_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R49_R10_IMPLEMENTED_STEPS,
    "R11_disposal_receipt_connection",
)
P7_R49_R11_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R49_R10_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R49_R10_NEXT_REQUIRED_STEP_REF: Final = "R49-11_disposal_receipt_connection"
P7_R49_R11_NEXT_REQUIRED_STEP_REF: Final = "R49-12_review_handoff_summary_builder"
P7_R49_R12_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R49_R11_IMPLEMENTED_STEPS,
    "R12_review_handoff_summary_builder",
)
P7_R49_R12_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R49_R11_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R49_R13_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R49_R12_IMPLEMENTED_STEPS,
    "R13_p5_confirmed_candidate_gate_connection",
)
P7_R49_R13_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R49_R12_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R49_R12_NEXT_REQUIRED_STEP_REF: Final = "R49-13_p5_confirmed_candidate_gate_connection"
P7_R49_R13_NEXT_REQUIRED_STEP_REF: Final = "R49-14_p6_limited_human_readfeel_start_candidate_handoff"
P7_R49_R14_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R49_R13_IMPLEMENTED_STEPS,
    "R14_p6_limited_human_readfeel_start_candidate_handoff",
)
P7_R49_R14_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R49_R13_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R49_R15_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R49_R14_IMPLEMENTED_STEPS,
    "R15_p8_question_design_material_candidate_handoff",
)
P7_R49_R15_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R49_R14_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R49_R14_NEXT_REQUIRED_STEP_REF: Final = "R49-15_p8_question_design_material_candidate_handoff"
P7_R49_R15_NEXT_REQUIRED_STEP_REF: Final = "R49-16_no_body_leak_no_question_text_guard"
P7_R49_R16_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R49_R15_IMPLEMENTED_STEPS,
    "R16_no_body_leak_no_question_text_guard",
)
P7_R49_R16_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R49_R15_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R49_R17_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R49_R16_IMPLEMENTED_STEPS,
    "R17_validation_command_matrix",
)
P7_R49_R17_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R49_R16_NOT_YET_IMPLEMENTED_STEPS[1:]
P7_R49_R16_NEXT_REQUIRED_STEP_REF: Final = "R49-17_validation_command_matrix"
P7_R49_R17_NEXT_REQUIRED_STEP_REF: Final = "R49-18_touch_candidate_no_touch_boundary_freeze"
P7_R49_R18_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R49_R17_IMPLEMENTED_STEPS,
    "R18_touch_candidate_no_touch_boundary_freeze",
)
P7_R49_R18_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = ()
P7_R49_R18_NEXT_REQUIRED_STEP_REF: Final = "P5_human_blind_qa_actual_review_manual_run_decision"
P7_R49_R18_POST_FREEZE_NEXT_WORK_REF: Final = P7_R49_R18_NEXT_REQUIRED_STEP_REF

P7_R49_REVIEW_SESSION_STATUS_REFS: Final[tuple[str, ...]] = (
    "NOT_STARTED",
    "PRECHECK_BLOCKED",
    "LOCAL_PACKETS_READY",
    "REVIEW_IN_PROGRESS",
    "RATINGS_CAPTURED_BODYFREE",
    "QUESTION_OBSERVATIONS_CAPTURED_BODYFREE",
    "DISPOSAL_PENDING",
    "DISPOSAL_VERIFIED",
    "SUMMARY_FINALIZED",
    "BLOCKED",
)
P7_R49_INITIAL_REVIEW_SESSION_STATUS_REF: Final = "NOT_STARTED"

P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = (
    "no_question_needed_emlis_can_observe",
    "question_may_reduce_overread_risk",
    "question_would_make_immediate_observation_heavy",
    "not_question_emlis_readfeel_repair_required",
    "not_question_p5_surface_repair_required",
    "not_question_gate_boundary_required",
    "plus_single_question_candidate_later",
    "premium_deep_dive_candidate_later",
    "insufficient_material_execution_blocker",
)
P7_R49_AMBIGUITY_KIND_REFS: Final[tuple[str, ...]] = (
    "no_material_ambiguity",
    "missing_target",
    "missing_time_scope",
    "missing_emotion_intensity",
    "missing_relation_context",
    "missing_action_intention",
    "conflicting_current_and_history_signal",
    "low_information_current_input",
    "boundary_or_tier_unclear",
    "history_connection_basis_unclear",
    "self_blame_or_safety_boundary_unclear",
)
P7_R49_ONE_QUESTION_FIT_REFS: Final[tuple[str, ...]] = (
    "not_needed",
    "fits_one_question",
    "needs_more_than_one_question_not_p7",
    "would_delay_immediate_observation",
    "unsafe_or_boundary_not_question",
    "repair_required_not_question",
    "insufficient_material",
)
P7_R49_REPAIR_REQUIRED_REF_REFS: Final[tuple[str, ...]] = (
    "emlis_readfeel_repair_required",
    "p5_surface_repair_required",
    "gate_boundary_repair_required",
    "no_repair_required",
)
P7_R49_PLAN_CANDIDATE_FLAG_REFS: Final[tuple[str, ...]] = (
    "plus_single_question_candidate_later",
    "premium_deep_dive_candidate_later",
    "p8_design_material_candidate",
    "p8_implementation_spec_finalized_here",
)
P7_R49_EXECUTION_BLOCKER_ID_REFS: Final[tuple[str, ...]] = (
    "r49_review_session_blocked_missing_r48_handoff",
    "r49_review_session_blocked_case_matrix_missing",
    "r49_review_session_blocked_case_matrix_count_mismatch",
    "r49_review_session_blocked_missing_local_root",
    "r49_review_session_blocked_invalid_local_root",
    "r49_review_session_blocked_missing_explicit_allow",
    "r49_review_session_blocked_body_full_packet_export_violation",
    "r49_rating_rows_missing",
    "r49_question_need_observation_rows_missing",
    "r49_disposal_receipt_missing",
    "r49_disposal_failed",
    "r49_body_free_leak_detected",
)
P7_R49_TO_R48_EXECUTION_BLOCKER_ID_MAP: Final[dict[str, str]] = {
    "r49_review_session_blocked_missing_r48_handoff": "review_case_material_missing",
    "r49_review_session_blocked_case_matrix_missing": "review_case_material_missing",
    "r49_review_session_blocked_case_matrix_count_mismatch": "review_case_matrix_minimum_not_met",
    "r49_review_session_blocked_missing_local_root": "review_packet_generation_blocked_missing_local_root",
    "r49_review_session_blocked_invalid_local_root": "review_packet_generation_blocked_invalid_local_root",
    "r49_review_session_blocked_missing_explicit_allow": "review_packet_generation_blocked_missing_explicit_allow",
    "r49_review_session_blocked_body_full_packet_export_violation": "body_full_packet_export_violation",
    "r49_rating_rows_missing": "rating_row_incomplete",
    "r49_question_need_observation_rows_missing": "review_case_material_missing",
    "r49_disposal_receipt_missing": "body_purge_not_verified",
    "r49_disposal_failed": "body_purge_failed",
    "r49_body_free_leak_detected": "body_full_packet_export_violation",
}
P7_R49_QUESTION_NEED_OBSERVATION_STAGE_REF: Final = "p7_p8_bridge_question_need_observation"
P7_R49_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
P7_R49_QUESTION_NEED_OBSERVATION_ROW_FORBIDDEN_FIELD_REFS: Final[tuple[str, ...]] = (
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
)
P7_R49_LOCAL_ONLY_PREFLIGHT_STATUS_REFS: Final[tuple[str, ...]] = (
    "READY_FOR_LOCAL_ONLY_PACKET_GENERATION",
    "BLOCKED",
)
P7_R49_R48_CASE_MATRIX_HANDOFF_ROW_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "body_full_packet_materialized_here",
    "local_reviewer_payload_materialized_here",
    "body_free",
)

P7_R49_RECEIVED_LOCAL_SNAPSHOT_REFS: Final[dict[str, str]] = {
    "premise_zip_ref": "Cocolon_前提資料(237).zip",
    "implemented_materials_zip_ref": "EmlisAIの実装済み資料(71).zip",
    "rn_zip_ref": "Cocolon(244).zip",
    "backend_zip_ref": "mashos-api(157).zip",
    "roadmap_ref": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619(1).md",
    "pre_design_memo_ref": "Cocolon_EmlisAI_P7_R49_P5HumanBlindQA_QuestionNeedObservation_PreDesignMemo_20260619.md",
    "detailed_design_ref": "Cocolon_EmlisAI_P7_R49_P5HumanBlindQA_QuestionNeedObservation_詳細設計書_実装順_20260619.md",
}
P7_R49_REQUIRED_UNRESOLVED_HOLD_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys((*P7_R48_REQUIRED_UNRESOLVED_HOLD_REFS, P6_LIMITED_HUMAN_READFEEL_HOLD_REF))
)

P7_R49_QUESTION_IMPLEMENTATION_FALSE_KEYS: Final[tuple[str, ...]] = (
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
P7_R49_RELEASE_CLOSED_KEYS: Final[tuple[str, ...]] = (
    "p5_human_blind_qa_confirmed",
    "p6_limited_human_readfeel_start_allowed",
    "p6_limited_human_readfeel_confirmed",
    "real_device_modal_review_start_allowed",
    "real_device_modal_review_confirmed",
    "p7_complete",
    "p8_start_allowed",
    "release_allowed",
    "hold004_close_allowed",
    "full_backend_suite_green_confirmed",
    "release_readiness_claim_allowed",
    "p7_completion_claim_allowed",
    "p8_start_claim_allowed",
    "full_backend_suite_green_claim_allowed",
)
P7_R49_R0_R1_FALSE_KEYS: Final[tuple[str, ...]] = (
    *P7_R49_QUESTION_IMPLEMENTATION_FALSE_KEYS,
    *P7_R49_RELEASE_CLOSED_KEYS,
    "json_schema_file_created_here",
    "schema_files_materialized_here",
    "actual_case_matrix_materialized_here",
    "body_full_packet_materialized_here",
    "actual_body_full_packet_generated_here",
    "body_full_writer_created_here",
    "local_reviewer_payload_materialized_here",
    "actual_human_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_reviewer_notes_materialized_here",
    "actual_disposal_run_here",
    "actual_disposal_receipt_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_question_need_observation_summary_materialized_here",
    "p5_human_blind_qa_confirmed_candidate",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p8_question_design_material_candidate",
)
P7_R49_R0_R1_FALSE_KEY_REFS: Final[tuple[str, ...]] = P7_R49_R0_R1_FALSE_KEYS

P7_R49_BODY_FREE_FORBIDDEN_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "traceback",
)

P7_R49_NO_BODY_LEAK_GUARD_MARKER_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    "question_text_included",
    "draft_question_text_included",
    "reviewer_free_text_included",
    "raw_input_or_comment_text_included",
    "returned_surface_included",
    "local_path_or_body_hash_included",
    "question_trigger_logic_implemented_here",
    "api_db_rn_response_key_changed_here",
    "body_full_packet_materialized_here",
    "actual_body_full_packet_generated_here",
    "actual_human_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_question_need_observation_summary_materialized_here",
    "actual_disposal_run_here",
    "actual_disposal_receipt_materialized_here",
)
P7_R49_QUESTION_TEXT_FORBIDDEN_FIELD_REFS: Final[tuple[str, ...]] = (
    "question_text",
    "draft_question_text",
    "question_body",
)
P7_R49_VALIDATION_R49_TARGET_TEST_FILE_REFS: Final[tuple[str, ...]] = (
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
P7_R49_VALIDATION_R48_REGRESSION_TEST_FILE_REFS: Final[tuple[str, ...]] = (
    "tests/test_emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet_r0_r1_20260618.py",
    "tests/test_emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet_r2_r3_20260618.py",
    "tests/test_emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet_r4_r5_20260618.py",
    "tests/test_emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet_r6_r7_20260618.py",
    "tests/test_emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet_r8_r9_20260618.py",
    "tests/test_emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet_r10_r11_20260619.py",
    "tests/test_emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet_r12_r13_20260619.py",
    "tests/test_emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet_r14_r15_20260619.py",
    "tests/test_emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet_r16_r17_20260619.py",
    "tests/test_emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet_r18_20260619.py",
)
P7_R49_VALIDATION_R47_REGRESSION_TEST_FILE_REFS: Final[tuple[str, ...]] = (
    "tests/test_emlis_ai_p7_r47_local_review_packet_policy_r0_r1_20260618.py",
    "tests/test_emlis_ai_p7_r47_local_review_packet_policy_r2_r3_20260618.py",
    "tests/test_emlis_ai_p7_r47_local_review_packet_policy_r4_r5_20260618.py",
    "tests/test_emlis_ai_p7_r47_local_review_packet_policy_r6_r7_20260618.py",
    "tests/test_emlis_ai_p7_r47_local_review_packet_policy_r8_r9_20260618.py",
    "tests/test_emlis_ai_p7_r47_local_review_packet_policy_r10_r11_20260618.py",
    "tests/test_emlis_ai_p7_r47_local_review_packet_policy_r12_r13_20260618.py",
    "tests/test_emlis_ai_p7_r47_local_review_packet_policy_r14_r15_20260618.py",
)
P7_R49_VALIDATION_R46_HANDOFF_TEST_FILE_REFS: Final[tuple[str, ...]] = (
    "tests/test_emlis_ai_p7_r46_p5_p6_human_readfeel_handoff_material_r10_r11_20260617.py",
    "tests/test_emlis_ai_p7_r46_real_device_modal_review_closed_validation_r12_r13_20260617.py",
    "tests/test_emlis_ai_p7_r46_next_decision_handoff_ledger_r14_20260617.py",
)
P7_R49_VALIDATION_DISPLAY_API_TEST_FILE_REFS: Final[tuple[str, ...]] = (
    "tests/contract/test_emlis_ai_contracts.py",
    "tests/test_emlis_ai_display_contract.py",
    "tests/test_emotion_submit_two_stage_reception_e2e.py",
)
P7_R49_VALIDATION_P5_CORE_TEST_FILE_REFS: Final[tuple[str, ...]] = (
    "tests/test_emlis_ai_user_label_connection_material.py",
    "tests/test_emlis_ai_user_label_connection_candidate.py",
    "tests/test_emlis_ai_user_label_connection_gate.py",
    "tests/test_emlis_ai_user_label_connection_surface.py",
    "tests/test_emlis_ai_user_label_connection_public_boundary.py",
    "tests/test_emlis_ai_user_label_connection_e2e_contract.py",
)
P7_R49_VALIDATION_COMMAND_GROUP_REFS: Final[tuple[str, ...]] = (
    "syntax_import",
    "r49_target",
    "r48_regression",
    "r47_regression",
    "r46_handoff_regression",
    "display_api_contract",
    "p5_core_subset",
    "p6_subset_optional",
    "backend_collect_only",
    "rn_no_touch_optional",
)

P7_R49_PRODUCTION_TOUCH_CANDIDATE_FILE_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution.py",
)
P7_R49_OPTIONAL_TOUCH_CANDIDATE_FILE_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r49_local_review_session_file_ops.py",
)
P7_R49_ALLOWED_PRODUCTION_TOUCH_FILE_REFS: Final[tuple[str, ...]] = (
    *P7_R49_PRODUCTION_TOUCH_CANDIDATE_FILE_REFS,
    *P7_R49_OPTIONAL_TOUCH_CANDIDATE_FILE_REFS,
)
P7_R49_ALLOWED_TEST_TOUCH_FILE_REFS: Final[tuple[str, ...]] = P7_R49_VALIDATION_R49_TARGET_TEST_FILE_REFS
P7_R49_ALLOWED_ACTUAL_TOUCHED_FILE_REFS: Final[tuple[str, ...]] = (
    *P7_R49_ALLOWED_PRODUCTION_TOUCH_FILE_REFS,
    *P7_R49_ALLOWED_TEST_TOUCH_FILE_REFS,
)
P7_R49_RN_PRODUCTION_NO_TOUCH_FILE_REFS: Final[tuple[str, ...]] = (
    "Cocolon/screens/InputScreen.js",
    "Cocolon/screens/input/useInputFeedbackModal.js",
    "Cocolon/screens/input/inputFeedbackModel.js",
    "Cocolon/screens/input/InputFeedbackReplyModal.js",
)
P7_R49_RN_CONTRACT_OPTIONAL_NO_TOUCH_TEST_REFS: Final[tuple[str, ...]] = (
    "Cocolon/tests/rn-screen-contracts.test.js",
)
P7_R49_EXPLICIT_NO_TOUCH_FILE_REFS: Final[tuple[str, ...]] = (
    *P7_R49_RN_PRODUCTION_NO_TOUCH_FILE_REFS,
    *P7_R49_RN_CONTRACT_OPTIONAL_NO_TOUCH_TEST_REFS,
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
    "services/ai_inference/emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet.py",
    "services/ai_inference/emlis_ai_p7_r47_local_review_packet_policy.py",
    "services/ai_inference/emlis_ai_p7_r46_p5_p6_human_readfeel_handoff_material.py",
)
P7_R49_EXPLICIT_NO_TOUCH_AREA_REFS: Final[tuple[str, ...]] = (
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
    "release_material_files",
    "existing_user_facing_surface_composer_runtime",
)
P7_R49_R18_CURRENT_PATCH_EXPECTED_TOUCHED_FILE_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution.py",
    "tests/test_emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution_r18_20260619.py",
)

P7_R49_RATING_INGESTION_FORBIDDEN_REVIEW_RESULT_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R49_BODY_FREE_FORBIDDEN_FIELD_REFS,
    "question_need_primary_class",
    "ambiguity_kind_refs",
    "one_question_fit_ref",
    "plan_candidate_flags",
    "repair_required_refs",
    "question_observation_note",
    "question_observation_free_text",
    "machine_metric_score",
    "machine_readfeel_score",
    "machine_metrics_used_for_readfeel",
    "machine_metric",
    "machine_metrics",
    "auto_score",
    "auto_scores",
)

P7_R49_BRIDGE_RULE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "bridge_rule_ref",
    "bridge_rule_source_ref",
    "p7_bridge_only",
    "question_need_observation_capture_required",
    "question_need_observation_memo_only",
    "question_need_observation_body_free_required",
    "question_need_observation_bodyfree_required",
    "question_need_observation_during_p5_p6_real_device_review_only",
    "emlis_readfeel_weakness_must_not_be_hidden_by_questions",
    "p5_surface_weakness_must_not_be_hidden_by_questions",
    "gate_boundary_weakness_must_not_be_hidden_by_questions",
    "p8_design_material_candidate_allowed_later",
    "question_text_allowed_here",
    "draft_question_text_allowed_here",
    "p8_detail_design_allowed_here",
    "api_db_rn_response_key_change_allowed_here",
    "question_trigger_logic_allowed_here",
    "raw_input_or_comment_text_allowed_in_bridge_material",
    "returned_surface_allowed_in_bridge_material",
    "reviewer_free_text_allowed_in_bridge_material",
    "question_text_allowed_in_bridge_material",
    "p7_completion_condition_relaxed",
    "p8_start_allowed",
    "release_allowed",
    "body_free",
    *P7_R49_QUESTION_IMPLEMENTATION_FALSE_KEYS,
)
P7_R49_R48_HANDOFF_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "r48_handoff_required",
    "r48_handoff_schema_version",
    "r48_step",
    "r48_scope",
    "r48_packet_kind",
    "r48_review_kind",
    "r48_completed_steps",
    "r48_implemented_steps",
    "r48_not_yet_implemented_steps",
    "r48_next_required_step",
    "r48_actual_review_packet_footing_ready",
    "r48_actual_review_packet_preparation_finished",
    "r48_actual_review_executed",
    "r48_actual_human_review_run",
    "r48_body_full_packet_generated",
    "r48_body_full_writer_created",
    "r48_rating_rows_materialized",
    "r48_blocker_rows_materialized",
    "r48_execution_blocker_rows_materialized",
    "r48_disposal_executed",
    "r48_disposal_run",
    "r48_disposal_receipt_materialized",
    "p5_human_blind_qa_confirmed",
    "r48_p5_human_blind_qa_confirmed",
    "p6_limited_human_readfeel_start_allowed",
    "r48_p6_limited_human_readfeel_start_allowed",
    "real_device_modal_review_confirmed",
    "r48_real_device_modal_review_confirmed",
    "p7_complete",
    "r48_p7_complete",
    "p8_start_allowed",
    "r48_p8_start_allowed",
    "release_allowed",
    "r48_release_allowed",
    "r48_no_touch_boundary_frozen",
    "body_free",
)
P7_R49_CURRENT_SOURCE_R48_HANDOFF_BRIDGE_REFREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r48_handoff",
    "p7_p8_bridge_rule",
    "implemented_steps",
    "not_yet_implemented_steps",
    "r0_current_source_r48_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "question_need_observation_capture_required",
    "question_need_observation_rows_required_later",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r49_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R49_R0_R1_FALSE_KEYS,
)
P7_R49_REVIEW_SESSION_ENVELOPE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r0_bridge_refreeze_schema_version",
    "r0_bridge_refreeze_material_ref",
    "r48_handoff_required",
    "r48_case_matrix_required",
    "required_total_cases",
    "review_session_status",
    "review_session_status_refs",
    "question_need_primary_class_refs",
    "ambiguity_kind_refs",
    "one_question_fit_refs",
    "repair_required_ref_refs",
    "plan_candidate_flag_refs",
    "schema_version_refs",
    "r49_review_session_envelope_schema_version",
    "question_need_observation_row_bodyfree_schema_version",
    "question_need_observation_summary_bodyfree_schema_version",
    "review_handoff_summary_bodyfree_schema_version",
    "r48_case_matrix_schema_version",
    "r48_reviewer_packet_local_only_schema_version",
    "r48_rating_row_bodyfree_schema_version",
    "r48_blocker_row_bodyfree_schema_version",
    "r48_execution_blocker_row_bodyfree_schema_version",
    "r48_disposal_receipt_bodyfree_schema_version",
    "r48_review_handoff_summary_bodyfree_schema_version",
    "r48_p5_confirmed_candidate_required_condition_refs",
    "r48_p5_first_formal_case_distribution",
    "r48_readfeel_blocker_id_refs",
    "r47_local_review_root_env_var",
    "r47_disposal_status_refs",
    "r47_body_full_packet_retention_hours",
    "r47_reviewer_notes_retention_after_rating_hours",
    "r47_p5_first_formal_minimums",
    "r47_p5_reviewer_facing_allowed_field_refs",
    "r47_p5_reviewer_facing_forbidden_field_refs",
    "p5_human_blind_qa_families",
    "p5_human_blind_qa_rating_axes",
    "p5_human_blind_qa_target_thresholds",
    "r49_scope_fixed",
    "r49_schema_versions_fixed",
    "review_session_status_enum_fixed",
    "question_need_observation_enum_fixed",
    "scope_fixed",
    "schema_versions_fixed",
    "status_enum_fixed",
    "question_need_enum_refs_fixed",
    "body_full_packet_materialized_here",
    "actual_human_review_run_here",
    "question_need_observation_required",
    "question_need_observation_rows_required",
    "question_text_required",
    "reviewer_free_text_bodyfree_export_allowed",
    "r49_is_p8_question_detail_design",
    "question_api_db_rn_response_key_in_scope",
    "question_trigger_logic_in_scope",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "r0_current_source_r48_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "public_contract",
    "r49_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R49_R0_R1_FALSE_KEYS,
)
P7_R49_R0_R1_SCOPE_STATUS_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "r0_current_source_r48_handoff_bridge_refreeze",
    "r1_review_session_envelope",
    "implemented_steps",
    "not_yet_implemented_steps",
    "review_session_status",
    "review_session_status_refs",
    "question_need_primary_class_refs",
    "packet_kind",
    "review_kind",
    "question_need_observation_required",
    "question_need_observation_rows_required",
    "first_next_work_ref",
    "next_required_step",
    "r0_current_source_r48_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "public_contract",
    "r49_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R49_R0_R1_FALSE_KEYS,
)
P7_R49_R48_CASE_MATRIX_HANDOFF_VALIDATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r1_review_session_envelope_schema_version",
    "r1_review_session_envelope_ref",
    "r48_case_matrix_handoff_required",
    "r48_case_matrix_handoff_validated",
    "r48_case_matrix_schema_version",
    "r48_r2_r3_case_matrix_freeze_schema_version",
    "r48_case_matrix_material_ref",
    "r48_case_matrix_row_field_refs",
    "required_total_cases",
    "case_count",
    "case_manifest_row_count",
    "case_manifest_rows",
    "family_case_counts",
    "case_role_counts",
    "subscription_tier_ref_counts",
    "owned_history_positive_case_count",
    "minimums_satisfied",
    "family_coverage_satisfied",
    "case_ref_id_count",
    "blind_case_id_count",
    "packet_ref_id_count",
    "blind_case_id_case_ref_separated",
    "packet_ref_id_present_for_all_cases",
    "controller_manifest_keeps_case_ref_family_tier",
    "reviewer_facing_identifier_policy",
    "reviewer_receives_blind_case_id",
    "reviewer_receives_case_ref_id",
    "reviewer_receives_family",
    "reviewer_receives_subscription_tier",
    "reviewer_receives_expected_result",
    "reviewer_receives_gate_result",
    "body_free_case_matrix_ready",
    "actual_case_matrix_materialized_here",
    "body_full_packet_materialized_here",
    "local_reviewer_payload_materialized_here",
    "actual_body_full_packet_generated_here",
    "actual_human_review_run_here",
    "question_need_observation_required",
    "question_need_observation_rows_required_later",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "r0_current_source_r48_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_r48_case_matrix_handoff_validated",
    "r3_local_only_actual_packet_generation_preflight_done",
    "public_contract",
    "r49_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R49_R0_R1_FALSE_KEYS,
)
P7_R49_LOCAL_ONLY_ACTUAL_PACKET_GENERATION_PREFLIGHT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r2_case_matrix_handoff_validation_schema_version",
    "r2_case_matrix_handoff_validation_ref",
    "r49_r48_case_matrix_handoff_validation",
    "r48_body_full_packet_materialization_guard_schema_version",
    "r48_body_full_packet_materialization_guard_ref",
    "r48_guard_preflight_used",
    "preflight_status",
    "review_session_status",
    "required_total_cases",
    "preflight_case_count",
    "local_review_root_env_var",
    "local_review_root_source",
    "local_review_root_status",
    "local_review_root_valid",
    "explicit_body_full_generation_allow",
    "root_path_exposed",
    "local_absolute_path_included",
    "body_full_generation_requires_env_root",
    "body_full_generation_requires_explicit_allow",
    "local_only_packet_generation_preflight_passed",
    "local_only_packet_generation_allowed_by_preflight",
    "body_full_packet_materialization_allowed_by_preflight",
    "body_full_packet_materialization_block_reason_ids",
    "export_candidate_refs_checked",
    "export_violation_reason_ids",
    "execution_blocker_ids",
    "execution_blocker_count",
    "local_packet_output_ref_is_abstract",
    "body_full_packet_output_dir_ref",
    "body_full_packet_output_file_ref_template",
    "local_packet_export_allowed",
    "body_full_packet_export_allowed",
    "body_full_packet_git_tracking_allowed",
    "body_full_packet_zip_inclusion_allowed",
    "release_material_body_full_allowed",
    "p7_scorecard_body_full_material_allowed",
    "public_meta_body_full_material_allowed",
    "body_content_hash_storage_allowed",
    "body_full_file_content_hash_storage_allowed",
    "generated_local_packet_must_set_local_only",
    "generated_local_packet_must_set_must_not_export",
    "generated_local_packet_must_set_disposal_required",
    "generated_local_packet_schema_version",
    "generated_local_packet_allowed_field_refs",
    "generated_local_packet_forbidden_field_refs",
    "body_free_material_can_include_local_packet_payload",
    "body_free_material_can_include_body_hash",
    "preflight_does_not_generate_packet",
    "json_schema_file_created_here",
    "body_full_packet_materialized_here",
    "local_reviewer_payload_materialized_here",
    "actual_body_full_packet_generated_here",
    "body_full_writer_created_here",
    "actual_human_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_reviewer_notes_materialized_here",
    "actual_disposal_run_here",
    "actual_disposal_receipt_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "body_free_case_matrix_ready",
    "question_need_observation_required",
    "question_need_observation_rows_required_later",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "r0_current_source_r48_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_r48_case_matrix_handoff_validated",
    "r3_local_only_actual_packet_generation_preflight_done",
    "public_contract",
    "r49_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R49_R0_R1_FALSE_KEYS,
)
P7_R49_R2_R3_CASE_MATRIX_PREFLIGHT_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r2_case_matrix_handoff_validation",
    "r3_local_only_actual_packet_generation_preflight",
    "implemented_steps",
    "not_yet_implemented_steps",
    "preflight_status",
    "execution_blocker_ids",
    "local_only_packet_generation_allowed_by_preflight",
    "body_full_packet_materialized_here",
    "actual_body_full_packet_generated_here",
    "actual_human_review_run_here",
    "question_need_observation_required",
    "question_need_observation_rows_required_later",
    "first_next_work_ref",
    "next_required_step",
    "r0_current_source_r48_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_r48_case_matrix_handoff_validated",
    "r3_local_only_actual_packet_generation_preflight_done",
    "public_contract",
    "r49_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R49_R0_R1_FALSE_KEYS,
)


P7_R49_ACTUAL_REVIEW_SESSION_PROTOCOL_CASE_ROW_FIELD_REFS: Final[tuple[str, ...]] = (
    "reviewer_case_order",
    "blind_case_id",
    "packet_ref_id",
    "reviewer_visible_identifier_policy",
    "reviewer_receives_blind_case_id",
    "reviewer_receives_case_ref_id",
    "reviewer_receives_family",
    "reviewer_receives_subscription_tier",
    "reviewer_receives_expected_result",
    "reviewer_receives_gate_result",
    "case_ref_hidden",
    "family_hidden",
    "subscription_tier_hidden",
    "expected_result_hidden",
    "gate_result_hidden",
    "packet_ref_id_visible_to_reviewer",
    "rating_row_required",
    "question_need_observation_row_required",
    "question_text_required",
    "reviewer_free_text_bodyfree_export_allowed",
    "body_full_packet_materialized_here",
    "actual_human_review_run_here",
    "body_free",
)
P7_R49_ACTUAL_REVIEW_SESSION_PROTOCOL_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r3_local_only_preflight_schema_version",
    "r3_local_only_preflight_ref",
    "r49_local_only_actual_packet_generation_preflight",
    "r48_reviewer_packet_schema_version",
    "r48_review_prompt_version",
    "review_prompt_version",
    "required_case_count",
    "protocol_case_count",
    "protocol_case_rows",
    "reviewer_visible_field_refs",
    "reviewer_hidden_field_refs",
    "reviewer_visible_identifier_policy",
    "reviewer_reads_blind_case_id_units",
    "reviewer_receives_blind_case_id",
    "reviewer_receives_case_ref_id",
    "reviewer_receives_family",
    "reviewer_receives_subscription_tier",
    "reviewer_receives_expected_result",
    "reviewer_receives_gate_result",
    "packet_ref_id_visible_to_reviewer",
    "local_only_packet_required_flag_refs",
    "local_only_packet_control_field_refs",
    "local_only_packet_required_field_refs",
    "local_only_packet_forbidden_field_refs",
    "local_only_body_field_refs",
    "review_question_refs",
    "rating_axes",
    "rating_axis_target_thresholds",
    "allowed_verdict_refs",
    "sanitized_reason_id_refs",
    "readfeel_blocker_id_refs",
    "rating_row_required",
    "blocker_row_required_when_repair_or_red",
    "execution_blocker_separate_from_readfeel",
    "question_need_observation_required",
    "question_need_observation_row_required_per_case",
    "question_need_observation_stage_ref",
    "question_need_primary_class_refs",
    "ambiguity_kind_refs",
    "one_question_fit_refs",
    "repair_required_ref_refs",
    "plan_candidate_flag_refs",
    "question_text_required",
    "question_text_allowed",
    "draft_question_text_allowed",
    "reviewer_free_text_local_only_allowed",
    "reviewer_free_text_bodyfree_export_allowed",
    "machine_metric_rating_allowed",
    "readfeel_auto_rating_allowed",
    "protocol_ready_for_later_local_only_review",
    "protocol_blocked_by_preflight",
    "review_session_status",
    "local_only_packet_generation_allowed_by_preflight",
    "body_full_packet_materialized_here",
    "local_reviewer_payload_materialized_here",
    "actual_body_full_packet_generated_here",
    "actual_human_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "r0_current_source_r48_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_r48_case_matrix_handoff_validated",
    "r3_local_only_actual_packet_generation_preflight_done",
    "r4_actual_review_session_protocol_built",
    "public_contract",
    "r49_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R49_R0_R1_FALSE_KEYS,
)
P7_R49_RATING_ROW_INGESTION_R48_NORMALIZER_CONNECTION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r4_protocol_schema_version",
    "r4_protocol_ref",
    "r49_actual_review_session_protocol",
    "r48_rating_row_normalizer_schema_version",
    "r48_rating_row_normalizer_policy_ref",
    "r48_rating_row_normalizer_policy",
    "r48_rating_row_bodyfree_schema_version",
    "r48_rating_row_normalizer_function_ref",
    "r48_rating_row_contract_ref",
    "r48_rating_row_required_field_refs",
    "rating_row_ingestion_ready",
    "rating_rows_must_be_r48_bodyfree",
    "r48_normalizer_connection_fixed",
    "r49_does_not_define_independent_rating_axes",
    "r49_uses_r48_rating_axes",
    "rating_axes",
    "axis_target_thresholds",
    "allowed_verdict_refs",
    "sanitized_reason_id_refs",
    "readfeel_blocker_id_refs",
    "missing_axis_scores_pass_allowed",
    "extra_axis_scores_allowed",
    "machine_metrics_used_for_readfeel",
    "readfeel_auto_estimation_allowed",
    "reviewer_free_text_included_allowed",
    "reviewer_free_text_bodyfree_allowed",
    "blocked_or_not_reviewable_must_use_execution_blocker_row",
    "rating_rows_present_for_all_cases_required_later",
    "synthetic_or_actual_review_result_required_before_row",
    "body_removed_required_before_p5_candidate",
    "question_need_observation_required",
    "question_need_observation_rows_required_later",
    "question_observation_ingestion_done_here",
    "body_full_packet_materialized_here",
    "local_reviewer_payload_materialized_here",
    "actual_body_full_packet_generated_here",
    "actual_human_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_reviewer_notes_materialized_here",
    "actual_disposal_run_here",
    "actual_disposal_receipt_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "r0_current_source_r48_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_r48_case_matrix_handoff_validated",
    "r3_local_only_actual_packet_generation_preflight_done",
    "r4_actual_review_session_protocol_built",
    "r5_rating_row_ingestion_r48_normalizer_connected",
    "public_contract",
    "r49_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R49_R0_R1_FALSE_KEYS,
)
P7_R49_R4_R5_PROTOCOL_RATING_CONNECTION_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r4_actual_review_session_protocol",
    "r5_rating_row_ingestion_r48_normalizer_connection",
    "implemented_steps",
    "not_yet_implemented_steps",
    "protocol_ready_for_later_local_only_review",
    "rating_row_ingestion_ready",
    "r48_normalizer_connection_fixed",
    "body_full_packet_materialized_here",
    "actual_body_full_packet_generated_here",
    "actual_human_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "question_need_observation_required",
    "question_need_observation_rows_required_later",
    "first_next_work_ref",
    "next_required_step",
    "r0_current_source_r48_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_r48_case_matrix_handoff_validated",
    "r3_local_only_actual_packet_generation_preflight_done",
    "r4_actual_review_session_protocol_built",
    "r5_rating_row_ingestion_r48_normalizer_connected",
    "public_contract",
    "r49_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R49_R0_R1_FALSE_KEYS,
)


P7_R49_BLOCKER_EXECUTION_BLOCKER_INGESTION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r5_rating_ingestion_schema_version",
    "r5_rating_ingestion_ref",
    "r49_rating_row_ingestion_r48_normalizer_connection",
    "r48_blocker_execution_blocker_row_builder_schema_version",
    "r48_blocker_execution_blocker_row_builder_policy_ref",
    "r48_blocker_execution_blocker_row_builder_policy",
    "r48_blocker_row_bodyfree_schema_version",
    "r48_execution_blocker_row_bodyfree_schema_version",
    "r48_blocker_row_builder_function_ref",
    "r48_execution_blocker_row_builder_function_ref",
    "r48_blocker_row_contract_ref",
    "r48_execution_blocker_row_contract_ref",
    "r48_blocker_row_required_field_refs",
    "r48_execution_blocker_row_required_field_refs",
    "readfeel_blocker_id_refs",
    "r49_execution_blocker_id_refs",
    "r48_execution_blocker_id_refs",
    "r49_to_r48_execution_blocker_id_map",
    "blocker_kind_refs",
    "blocker_status_refs",
    "execution_blocker_kind_refs",
    "execution_blocker_status_refs",
    "forbidden_field_refs",
    "blocker_execution_ingestion_ready",
    "blocker_rows_must_be_r48_bodyfree",
    "execution_blocker_rows_must_be_r48_bodyfree",
    "r48_builder_connection_fixed",
    "readfeel_and_execution_blockers_separated",
    "execution_blockers_do_not_assign_readfeel_verdict",
    "review_execution_blockers_do_not_create_p5_readfeel_red",
    "local_preflight_blockers_map_to_execution_blocker_rows",
    "rating_rows_missing_maps_to_execution_blocker_rows",
    "question_observation_rows_missing_maps_to_execution_blocker_rows",
    "disposal_missing_or_failed_maps_to_execution_blocker_rows",
    "body_free_leak_maps_to_execution_blocker_rows",
    "reviewer_free_text_included_allowed",
    "reviewer_free_text_bodyfree_allowed",
    "question_observation_ingestion_done_here",
    "body_full_packet_materialized_here",
    "local_reviewer_payload_materialized_here",
    "actual_body_full_packet_generated_here",
    "actual_human_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_reviewer_notes_materialized_here",
    "actual_disposal_run_here",
    "actual_disposal_receipt_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "question_need_observation_required",
    "question_need_observation_rows_required_later",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "r0_current_source_r48_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_r48_case_matrix_handoff_validated",
    "r3_local_only_actual_packet_generation_preflight_done",
    "r4_actual_review_session_protocol_built",
    "r5_rating_row_ingestion_r48_normalizer_connected",
    "r6_blocker_execution_blocker_ingestion_connected",
    "public_contract",
    "r49_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R49_R0_R1_FALSE_KEYS,
)
P7_R49_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_ENUM_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r6_blocker_ingestion_schema_version",
    "r6_blocker_ingestion_ref",
    "r49_blocker_execution_blocker_ingestion",
    "question_need_observation_row_schema_version",
    "question_need_observation_summary_schema_version",
    "observation_stage_ref",
    "question_need_observation_row_required_field_refs",
    "question_need_observation_row_forbidden_field_refs",
    "question_need_primary_class_refs",
    "ambiguity_kind_refs",
    "one_question_fit_refs",
    "repair_required_ref_refs",
    "plan_candidate_flag_refs",
    "enum_refs_unique",
    "primary_class_refs_cover_repair_and_execution_boundaries",
    "plan_candidate_flags_are_overlay_not_primary_required",
    "question_text_allowed",
    "draft_question_text_allowed",
    "reviewer_free_text_allowed",
    "raw_input_allowed",
    "raw_answer_allowed",
    "comment_text_body_allowed",
    "returned_surface_allowed",
    "local_path_allowed",
    "body_hash_allowed",
    "question_need_observation_row_schema_enum_fixed",
    "question_need_observation_row_bodyfree_contract_ready",
    "question_need_observation_row_normalizer_implemented_here",
    "question_need_observation_row_instances_materialized_here",
    "p8_question_implementation_spec_finalized_here",
    "p8_start_allowed",
    "release_allowed",
    "body_full_packet_materialized_here",
    "actual_body_full_packet_generated_here",
    "actual_human_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_question_need_observation_summary_materialized_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "r0_current_source_r48_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_r48_case_matrix_handoff_validated",
    "r3_local_only_actual_packet_generation_preflight_done",
    "r4_actual_review_session_protocol_built",
    "r5_rating_row_ingestion_r48_normalizer_connected",
    "r6_blocker_execution_blocker_ingestion_connected",
    "r7_question_need_observation_row_schema_enum_fixed",
    "public_contract",
    "r49_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R49_R0_R1_FALSE_KEYS,
)
P7_R49_R6_R7_BLOCKER_QUESTION_SCHEMA_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r6_blocker_execution_blocker_ingestion",
    "r7_question_need_observation_row_schema_enum_freeze",
    "implemented_steps",
    "not_yet_implemented_steps",
    "blocker_execution_ingestion_ready",
    "readfeel_and_execution_blockers_separated",
    "question_need_observation_row_schema_enum_fixed",
    "question_need_observation_required",
    "question_need_observation_rows_required_later",
    "body_full_packet_materialized_here",
    "actual_body_full_packet_generated_here",
    "actual_human_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "question_need_observation_row_normalizer_implemented_here",
    "first_next_work_ref",
    "next_required_step",
    "r0_current_source_r48_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_r48_case_matrix_handoff_validated",
    "r3_local_only_actual_packet_generation_preflight_done",
    "r4_actual_review_session_protocol_built",
    "r5_rating_row_ingestion_r48_normalizer_connected",
    "r6_blocker_execution_blocker_ingestion_connected",
    "r7_question_need_observation_row_schema_enum_fixed",
    "public_contract",
    "r49_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R49_R0_R1_FALSE_KEYS,
)


P7_R49_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r7_question_schema_enum_freeze_schema_version",
    "r7_question_schema_enum_freeze_ref",
    "r49_question_need_observation_row_schema_enum_freeze",
    "question_need_observation_row_schema_version",
    "question_need_observation_row_normalizer_function_ref",
    "question_need_observation_row_contract_ref",
    "question_need_observation_row_required_field_refs",
    "question_need_observation_row_forbidden_field_refs",
    "question_need_primary_class_refs",
    "ambiguity_kind_refs",
    "one_question_fit_refs",
    "repair_required_ref_refs",
    "plan_candidate_flag_refs",
    "normalizer_ready",
    "question_need_observation_rows_must_be_bodyfree",
    "body_removed_required_for_question_observation_row",
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
    "question_need_observation_row_normalizer_implemented_here",
    "question_need_observation_row_instances_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "body_full_packet_materialized_here",
    "actual_body_full_packet_generated_here",
    "actual_human_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "r0_current_source_r48_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_r48_case_matrix_handoff_validated",
    "r3_local_only_actual_packet_generation_preflight_done",
    "r4_actual_review_session_protocol_built",
    "r5_rating_row_ingestion_r48_normalizer_connected",
    "r6_blocker_execution_blocker_ingestion_connected",
    "r7_question_need_observation_row_schema_enum_fixed",
    "r8_question_need_observation_row_normalizer_connected",
    "public_contract",
    "r49_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R49_R0_R1_FALSE_KEYS,
)
P7_R49_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r8_question_need_observation_row_normalizer_schema_version",
    "r8_question_need_observation_row_normalizer_ref",
    "r49_question_need_observation_row_normalizer",
    "r5_rating_ingestion_schema_version",
    "r6_blocker_ingestion_schema_version",
    "r48_rating_row_bodyfree_schema_version",
    "r49_question_row_bodyfree_schema_version",
    "r48_execution_blocker_row_bodyfree_schema_version",
    "rating_question_consistency_guard_ready",
    "p5_weakness_must_not_be_hidden_by_questions",
    "rating_and_question_observation_ids_must_match",
    "pass_rating_forbids_not_question_repair_primary_class",
    "repair_or_red_rating_forbids_question_candidate_primary_only",
    "repair_required_not_question_requires_repair_ref",
    "insufficient_material_requires_execution_blocker_row",
    "question_candidate_cannot_clear_readfeel_blocker",
    "consistency_guard_function_ref",
    "question_need_observation_required",
    "question_need_observation_rows_required_later",
    "body_full_packet_materialized_here",
    "actual_body_full_packet_generated_here",
    "actual_human_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_question_need_observation_summary_materialized_here",
    "p8_start_allowed",
    "release_allowed",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "r0_current_source_r48_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_r48_case_matrix_handoff_validated",
    "r3_local_only_actual_packet_generation_preflight_done",
    "r4_actual_review_session_protocol_built",
    "r5_rating_row_ingestion_r48_normalizer_connected",
    "r6_blocker_execution_blocker_ingestion_connected",
    "r7_question_need_observation_row_schema_enum_fixed",
    "r8_question_need_observation_row_normalizer_connected",
    "r9_rating_question_observation_consistency_guard_connected",
    "public_contract",
    "r49_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R49_R0_R1_FALSE_KEYS,
)
P7_R49_R8_R9_QUESTION_NORMALIZER_CONSISTENCY_GUARD_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r8_question_need_observation_row_normalizer",
    "r9_rating_question_observation_consistency_guard",
    "implemented_steps",
    "not_yet_implemented_steps",
    "question_need_observation_row_normalizer_implemented_here",
    "rating_question_consistency_guard_ready",
    "p5_weakness_must_not_be_hidden_by_questions",
    "question_need_observation_required",
    "question_need_observation_rows_required_later",
    "body_full_packet_materialized_here",
    "actual_body_full_packet_generated_here",
    "actual_human_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_question_need_observation_summary_materialized_here",
    "first_next_work_ref",
    "next_required_step",
    "r0_current_source_r48_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_r48_case_matrix_handoff_validated",
    "r3_local_only_actual_packet_generation_preflight_done",
    "r4_actual_review_session_protocol_built",
    "r5_rating_row_ingestion_r48_normalizer_connected",
    "r6_blocker_execution_blocker_ingestion_connected",
    "r7_question_need_observation_row_schema_enum_fixed",
    "r8_question_need_observation_row_normalizer_connected",
    "r9_rating_question_observation_consistency_guard_connected",
    "public_contract",
    "r49_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R49_R0_R1_FALSE_KEYS,
)

P7_R49_QUESTION_NEED_OBSERVATION_SUMMARY_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r9_rating_question_observation_consistency_guard_schema_version",
    "r9_rating_question_observation_consistency_guard_ref",
    "r49_rating_question_observation_consistency_guard",
    "question_need_observation_summary_schema_version",
    "question_observation_summary_builder_ready",
    "question_observation_rows_must_be_bodyfree",
    "question_observation_rows_required_total_cases",
    "total_case_count",
    "question_observation_row_count",
    "question_observation_rows_complete",
    "unique_case_ref_id_count",
    "unique_blind_case_id_count",
    "unique_packet_ref_id_count",
    "primary_class_counts",
    "ambiguity_kind_counts",
    "one_question_fit_counts",
    "repair_required_counts",
    "plan_candidate_flag_counts",
    "p8_design_material_candidate_row_count",
    "plus_single_question_candidate_later_count",
    "premium_deep_dive_candidate_later_count",
    "not_question_repair_required_count",
    "insufficient_material_execution_blocker_count",
    "p8_question_design_material_candidate",
    "p8_start_allowed",
    "p8_implementation_spec_finalized_here",
    "question_trigger_logic_implemented_here",
    "api_db_rn_response_key_changed_here",
    "actual_human_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_question_need_observation_summary_materialized_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "r0_current_source_r48_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_r48_case_matrix_handoff_validated",
    "r3_local_only_actual_packet_generation_preflight_done",
    "r4_actual_review_session_protocol_built",
    "r5_rating_row_ingestion_r48_normalizer_connected",
    "r6_blocker_execution_blocker_ingestion_connected",
    "r7_question_need_observation_row_schema_enum_fixed",
    "r8_question_need_observation_row_normalizer_connected",
    "r9_rating_question_observation_consistency_guard_connected",
    "r10_question_need_observation_summary_built",
    "public_contract",
    "r49_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R49_R0_R1_FALSE_KEYS,
)
P7_R49_DISPOSAL_RECEIPT_CONNECTION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r10_question_need_observation_summary_schema_version",
    "r10_question_need_observation_summary_ref",
    "r49_question_need_observation_summary",
    "r48_disposal_receipt_builder_schema_version",
    "r48_disposal_receipt_schema_version",
    "r48_disposal_receipt_required_field_refs",
    "r48_disposal_receipt_forbidden_field_refs",
    "r47_disposal_status_refs",
    "r48_disposal_receipt_builder_function_ref",
    "r48_disposal_receipt_contract_ref",
    "question_observation_rows_complete_required_before_disposal_pending",
    "question_observation_rows_complete",
    "question_observation_row_count",
    "required_total_cases",
    "disposal_receipt_connection_ready",
    "disposal_pending_allowed_by_question_observation_summary",
    "disposal_receipt_bodyfree",
    "disposal_receipt",
    "disposal_status",
    "disposal_verified_for_candidate",
    "review_session_status",
    "body_removed",
    "reviewer_notes_removed",
    "local_packet_exported",
    "content_hash_of_body_stored",
    "execution_blocker_ids",
    "execution_blocker_count",
    "body_path_hash_forbidden",
    "receipt_does_not_delete_files_here",
    "actual_disposal_run_here",
    "actual_cleanup_run_here",
    "actual_disposal_receipt_materialized_here",
    "actual_body_full_packet_generated_here",
    "actual_human_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_question_need_observation_summary_materialized_here",
    "p8_start_allowed",
    "release_allowed",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "r0_current_source_r48_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_r48_case_matrix_handoff_validated",
    "r3_local_only_actual_packet_generation_preflight_done",
    "r4_actual_review_session_protocol_built",
    "r5_rating_row_ingestion_r48_normalizer_connected",
    "r6_blocker_execution_blocker_ingestion_connected",
    "r7_question_need_observation_row_schema_enum_fixed",
    "r8_question_need_observation_row_normalizer_connected",
    "r9_rating_question_observation_consistency_guard_connected",
    "r10_question_need_observation_summary_built",
    "r11_disposal_receipt_connection_fixed",
    "public_contract",
    "r49_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R49_R0_R1_FALSE_KEYS,
)
P7_R49_R10_R11_QUESTION_SUMMARY_DISPOSAL_CONNECTION_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r10_question_need_observation_summary",
    "r11_disposal_receipt_connection",
    "implemented_steps",
    "not_yet_implemented_steps",
    "question_observation_summary_builder_ready",
    "question_observation_rows_complete",
    "disposal_receipt_connection_ready",
    "disposal_receipt_bodyfree",
    "disposal_pending_allowed_by_question_observation_summary",
    "actual_disposal_run_here",
    "actual_disposal_receipt_materialized_here",
    "actual_human_review_run_here",
    "actual_body_full_packet_generated_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_question_need_observation_summary_materialized_here",
    "p8_question_design_material_candidate",
    "p8_start_allowed",
    "release_allowed",
    "first_next_work_ref",
    "next_required_step",
    "r0_current_source_r48_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_r48_case_matrix_handoff_validated",
    "r3_local_only_actual_packet_generation_preflight_done",
    "r4_actual_review_session_protocol_built",
    "r5_rating_row_ingestion_r48_normalizer_connected",
    "r6_blocker_execution_blocker_ingestion_connected",
    "r7_question_need_observation_row_schema_enum_fixed",
    "r8_question_need_observation_row_normalizer_connected",
    "r9_rating_question_observation_consistency_guard_connected",
    "r10_question_need_observation_summary_built",
    "r11_disposal_receipt_connection_fixed",
    "public_contract",
    "r49_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R49_R0_R1_FALSE_KEYS,
)


P7_R49_QUESTION_OBSERVATION_GATE_REQUIRED_CONDITION_REFS: Final[tuple[str, ...]] = (
    "r49_review_handoff_summary_finalized",
    "question_observation_rows_complete",
    "question_observation_repair_required_zero",
    "question_observation_execution_blocker_zero",
    "r48_p5_confirmed_candidate_gate_passed",
)
P7_R49_P5_CONFIRMED_CANDIDATE_REQUIRED_CONDITION_REFS: Final[tuple[str, ...]] = (
    *P7_R48_P5_CONFIRMED_CANDIDATE_REQUIRED_CONDITION_REFS,
    *P7_R49_QUESTION_OBSERVATION_GATE_REQUIRED_CONDITION_REFS,
)
P7_R49_REVIEW_HANDOFF_SUMMARY_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r10_r11_freeze_schema_version",
    "r10_r11_freeze_ref",
    "r10_r11_question_summary_disposal_connection_freeze",
    "r48_review_handoff_summary_schema_version",
    "r48_review_handoff_summary_required_field_refs",
    "r48_review_handoff_summary_function_ref",
    "r48_review_handoff_summary_contract_ref",
    "r48_review_handoff_summary",
    "r49_question_need_observation_summary",
    "r49_disposal_receipt_connection",
    "required_total_cases",
    "case_count",
    "reviewed_case_count",
    "rating_row_count",
    "blocker_row_count",
    "execution_blocker_row_count",
    "question_observation_row_count",
    "question_observation_rows_complete",
    "rating_rows_complete",
    "family_coverage_satisfied",
    "axis_averages",
    "axis_targets_satisfied",
    "red_case_count",
    "repair_required_case_count",
    "open_blocker_ids",
    "open_execution_blocker_ids",
    "boundary_violation_blocker_ids",
    "question_observation_repair_required_count",
    "question_observation_execution_blocker_count",
    "question_observation_blocks_p5_candidate",
    "disposal_status",
    "disposal_verified_for_candidate",
    "body_removed",
    "reviewer_notes_removed",
    "local_packet_exported",
    "content_hash_of_body_stored",
    "review_session_status",
    "r48_review_session_status",
    "r48_handoff_summary_candidate_claim",
    "r48_p6_candidate_claim",
    "p5_human_blind_qa_confirmed_candidate",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p5_human_blind_qa_confirmed",
    "p6_limited_human_readfeel_start_allowed",
    "p6_limited_human_readfeel_confirmed",
    "real_device_modal_review_start_allowed",
    "real_device_modal_review_confirmed",
    "actual_review_handoff_summary_materialized_here",
    "actual_human_review_run_here",
    "actual_body_full_packet_generated_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_question_need_observation_summary_materialized_here",
    "actual_disposal_run_here",
    "actual_disposal_receipt_materialized_here",
    "p8_question_design_material_candidate",
    "p8_start_allowed",
    "release_allowed",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "r0_current_source_r48_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_r48_case_matrix_handoff_validated",
    "r3_local_only_actual_packet_generation_preflight_done",
    "r4_actual_review_session_protocol_built",
    "r5_rating_row_ingestion_r48_normalizer_connected",
    "r6_blocker_execution_blocker_ingestion_connected",
    "r7_question_need_observation_row_schema_enum_fixed",
    "r8_question_need_observation_row_normalizer_connected",
    "r9_rating_question_observation_consistency_guard_connected",
    "r10_question_need_observation_summary_built",
    "r11_disposal_receipt_connection_fixed",
    "r12_review_handoff_summary_built",
    "public_contract",
    "r49_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R49_R0_R1_FALSE_KEYS,
)
P7_R49_P5_CONFIRMED_CANDIDATE_GATE_CONNECTION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r12_review_handoff_summary_schema_version",
    "r12_review_handoff_summary_ref",
    "r49_review_handoff_summary",
    "r48_p5_confirmed_candidate_gate_schema_version",
    "r48_p5_confirmed_candidate_gate_required_field_refs",
    "r48_p5_confirmed_candidate_gate_function_ref",
    "r48_p5_confirmed_candidate_gate_contract_ref",
    "r48_p5_confirmed_candidate_gate",
    "required_condition_refs",
    "missing_requirement_refs",
    "failed_requirement_count",
    "review_session_status",
    "required_total_cases",
    "case_count",
    "reviewed_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "question_observation_rows_complete",
    "question_observation_repair_required_count",
    "question_observation_execution_blocker_count",
    "family_coverage_satisfied",
    "axis_targets_satisfied",
    "red_case_count",
    "repair_required_case_count",
    "open_blocker_ids",
    "open_execution_blocker_ids",
    "boundary_violation_blocker_ids",
    "disposal_status",
    "disposal_verified_for_candidate",
    "body_removed",
    "reviewer_notes_removed",
    "local_packet_exported",
    "content_hash_of_body_stored",
    "r48_p5_confirmed_candidate_gate_passed",
    "question_observation_completeness_connected_to_gate",
    "question_observation_repair_required_blocks_candidate",
    "question_observation_execution_blocker_blocks_candidate",
    "p5_confirmed_candidate_gate_connection_ready",
    "p5_confirmed_candidate_gate_passed",
    "p5_human_blind_qa_confirmed_candidate",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p6_candidate_handoff_deferred_to_r14",
    "p5_human_blind_qa_confirmed",
    "p6_limited_human_readfeel_start_allowed",
    "p6_limited_human_readfeel_confirmed",
    "real_device_modal_review_start_allowed",
    "real_device_modal_review_confirmed",
    "actual_p5_confirmed_candidate_gate_materialized_here",
    "actual_human_review_run_here",
    "actual_body_full_packet_generated_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_run_here",
    "actual_disposal_receipt_materialized_here",
    "p8_question_design_material_candidate",
    "p8_start_allowed",
    "release_allowed",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "r0_current_source_r48_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_r48_case_matrix_handoff_validated",
    "r3_local_only_actual_packet_generation_preflight_done",
    "r4_actual_review_session_protocol_built",
    "r5_rating_row_ingestion_r48_normalizer_connected",
    "r6_blocker_execution_blocker_ingestion_connected",
    "r7_question_need_observation_row_schema_enum_fixed",
    "r8_question_need_observation_row_normalizer_connected",
    "r9_rating_question_observation_consistency_guard_connected",
    "r10_question_need_observation_summary_built",
    "r11_disposal_receipt_connection_fixed",
    "r12_review_handoff_summary_built",
    "r13_p5_confirmed_candidate_gate_connected",
    "public_contract",
    "r49_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R49_R0_R1_FALSE_KEYS,
)
P7_R49_R12_R13_REVIEW_HANDOFF_P5_GATE_CONNECTION_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r12_review_handoff_summary",
    "r13_p5_confirmed_candidate_gate_connection",
    "implemented_steps",
    "not_yet_implemented_steps",
    "review_handoff_summary_ready",
    "p5_confirmed_candidate_gate_connected",
    "question_observation_completeness_connected_to_gate",
    "p5_human_blind_qa_confirmed_candidate",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p6_candidate_handoff_deferred_to_r14",
    "p8_question_design_material_candidate",
    "p8_start_allowed",
    "release_allowed",
    "actual_human_review_run_here",
    "actual_body_full_packet_generated_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_run_here",
    "actual_disposal_receipt_materialized_here",
    "first_next_work_ref",
    "next_required_step",
    "r0_current_source_r48_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_r48_case_matrix_handoff_validated",
    "r3_local_only_actual_packet_generation_preflight_done",
    "r4_actual_review_session_protocol_built",
    "r5_rating_row_ingestion_r48_normalizer_connected",
    "r6_blocker_execution_blocker_ingestion_connected",
    "r7_question_need_observation_row_schema_enum_fixed",
    "r8_question_need_observation_row_normalizer_connected",
    "r9_rating_question_observation_consistency_guard_connected",
    "r10_question_need_observation_summary_built",
    "r11_disposal_receipt_connection_fixed",
    "r12_review_handoff_summary_built",
    "r13_p5_confirmed_candidate_gate_connected",
    "public_contract",
    "r49_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R49_R0_R1_FALSE_KEYS,
)


P7_R49_P6_START_CANDIDATE_REQUIRED_CONDITION_REFS: Final[tuple[str, ...]] = (
    "p5_human_blind_qa_confirmed_candidate",
    "review_session_status_summary_finalized",
    "rating_rows_complete",
    "question_observation_rows_complete",
    "family_coverage_satisfied",
    "axis_targets_satisfied",
    "red_case_count_zero",
    "repair_required_case_count_zero",
    "open_blocker_ids_empty",
    "open_execution_blocker_ids_empty",
    "question_observation_repair_required_zero",
    "question_observation_execution_blocker_zero",
    "disposal_verified_for_candidate",
    "body_removed",
    "reviewer_notes_removed",
    "local_packet_not_exported",
    "content_hash_of_body_not_stored",
    "p6_handoff_material_ready",
    "p6_handoff_does_not_hide_p5_unresolved",
)
P7_R49_P6_LIMITED_HUMAN_READFEEL_START_CANDIDATE_HANDOFF_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r13_p5_gate_connection_schema_version",
    "r13_p5_gate_connection_ref",
    "r49_p5_confirmed_candidate_gate_connection",
    "r46_p6_limited_human_readfeel_handoff_schema_version",
    "r46_p6_limited_human_readfeel_handoff_function_ref",
    "r46_p6_limited_human_readfeel_handoff_contract_ref",
    "r46_p6_limited_human_readfeel_handoff_material",
    "required_condition_refs",
    "missing_requirement_refs",
    "failed_requirement_count",
    "review_session_status",
    "required_total_cases",
    "case_count",
    "reviewed_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "rating_rows_complete",
    "question_observation_rows_complete",
    "family_coverage_satisfied",
    "axis_targets_satisfied",
    "red_case_count",
    "repair_required_case_count",
    "open_blocker_ids",
    "open_execution_blocker_ids",
    "boundary_violation_blocker_ids",
    "question_observation_repair_required_count",
    "question_observation_execution_blocker_count",
    "disposal_status",
    "disposal_verified_for_candidate",
    "body_removed",
    "reviewer_notes_removed",
    "local_packet_exported",
    "content_hash_of_body_stored",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_human_blind_qa_confirmed",
    "p6_limited_human_readfeel_start_candidate_handoff_ready",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "p6_limited_human_readfeel_confirmed",
    "p6_review_families",
    "p6_no_connect_families",
    "p6_rating_axes",
    "p6_target_thresholds",
    "p6_hold_refs_preserved",
    "p6_unresolved_hold_refs",
    "p6_handoff_does_not_hide_p5_unresolved",
    "p6_handoff_missing_requirements_visible",
    "full_backend_suite_green_claim_used_for_p6_start_allowed",
    "p6_start_permission_granted_here",
    "real_device_modal_review_start_allowed",
    "real_device_modal_review_confirmed",
    "p7_complete",
    "p8_question_design_material_candidate",
    "p8_start_allowed",
    "release_allowed",
    "actual_p6_handoff_materialized_here",
    "actual_human_review_run_here",
    "actual_body_full_packet_generated_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_run_here",
    "actual_disposal_receipt_materialized_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "r0_current_source_r48_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_r48_case_matrix_handoff_validated",
    "r3_local_only_actual_packet_generation_preflight_done",
    "r4_actual_review_session_protocol_built",
    "r5_rating_row_ingestion_r48_normalizer_connected",
    "r6_blocker_execution_blocker_ingestion_connected",
    "r7_question_need_observation_row_schema_enum_fixed",
    "r8_question_need_observation_row_normalizer_connected",
    "r9_rating_question_observation_consistency_guard_connected",
    "r10_question_need_observation_summary_built",
    "r11_disposal_receipt_connection_fixed",
    "r12_review_handoff_summary_built",
    "r13_p5_confirmed_candidate_gate_connected",
    "r14_p6_limited_human_readfeel_start_candidate_handoff_built",
    "public_contract",
    "r49_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R49_R0_R1_FALSE_KEYS,
)
P7_R49_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r14_p6_handoff_schema_version",
    "r14_p6_handoff_ref",
    "r49_p6_limited_human_readfeel_start_candidate_handoff",
    "question_need_observation_summary_schema_version",
    "question_need_observation_summary_ref",
    "r49_question_need_observation_summary",
    "p8_question_design_material_candidate_handoff_ready",
    "p8_question_design_material_candidate",
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
    "p8_design_material_candidate_row_count",
    "primary_class_counts",
    "ambiguity_kind_counts",
    "one_question_fit_counts",
    "repair_required_counts",
    "plan_candidate_flag_counts",
    "p8_start_blocker_refs",
    "p8_pre_design_repair_required_before_start",
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
    "p5_human_blind_qa_confirmed_candidate",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "p6_limited_human_readfeel_confirmed",
    "p7_complete",
    "p8_start_allowed",
    "release_allowed",
    "actual_p8_design_material_handoff_materialized_here",
    "actual_human_review_run_here",
    "actual_body_full_packet_generated_here",
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
    "r0_current_source_r48_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_r48_case_matrix_handoff_validated",
    "r3_local_only_actual_packet_generation_preflight_done",
    "r4_actual_review_session_protocol_built",
    "r5_rating_row_ingestion_r48_normalizer_connected",
    "r6_blocker_execution_blocker_ingestion_connected",
    "r7_question_need_observation_row_schema_enum_fixed",
    "r8_question_need_observation_row_normalizer_connected",
    "r9_rating_question_observation_consistency_guard_connected",
    "r10_question_need_observation_summary_built",
    "r11_disposal_receipt_connection_fixed",
    "r12_review_handoff_summary_built",
    "r13_p5_confirmed_candidate_gate_connected",
    "r14_p6_limited_human_readfeel_start_candidate_handoff_built",
    "r15_p8_question_design_material_candidate_handoff_built",
    "public_contract",
    "r49_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R49_R0_R1_FALSE_KEYS,
)
P7_R49_R14_R15_P6_P8_CANDIDATE_HANDOFF_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r14_p6_limited_human_readfeel_start_candidate_handoff",
    "r15_p8_question_design_material_candidate_handoff",
    "implemented_steps",
    "not_yet_implemented_steps",
    "p5_human_blind_qa_confirmed_candidate",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "p6_limited_human_readfeel_confirmed",
    "p8_question_design_material_candidate",
    "p8_detail_design_allowed_here",
    "p8_implementation_spec_finalized_here",
    "question_trigger_logic_implemented_here",
    "api_db_rn_response_key_changed_here",
    "p7_complete",
    "p8_start_allowed",
    "release_allowed",
    "actual_human_review_run_here",
    "actual_body_full_packet_generated_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_run_here",
    "actual_disposal_receipt_materialized_here",
    "first_next_work_ref",
    "next_required_step",
    "r0_current_source_r48_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_r48_case_matrix_handoff_validated",
    "r3_local_only_actual_packet_generation_preflight_done",
    "r4_actual_review_session_protocol_built",
    "r5_rating_row_ingestion_r48_normalizer_connected",
    "r6_blocker_execution_blocker_ingestion_connected",
    "r7_question_need_observation_row_schema_enum_fixed",
    "r8_question_need_observation_row_normalizer_connected",
    "r9_rating_question_observation_consistency_guard_connected",
    "r10_question_need_observation_summary_built",
    "r11_disposal_receipt_connection_fixed",
    "r12_review_handoff_summary_built",
    "r13_p5_confirmed_candidate_gate_connected",
    "r14_p6_limited_human_readfeel_start_candidate_handoff_built",
    "r15_p8_question_design_material_candidate_handoff_built",
    "public_contract",
    "r49_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R49_R0_R1_FALSE_KEYS,
)


P7_R49_NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r15_p6_p8_candidate_handoff_freeze_schema_version",
    "r15_p6_p8_candidate_handoff_freeze_ref",
    "material_scanned_refs",
    "forbidden_field_refs",
    "question_text_forbidden_field_refs",
    "guard_marker_false_key_refs",
    "forbidden_key_path_refs",
    "forbidden_key_count",
    "forbidden_marker_true_path_refs",
    "forbidden_marker_true_count",
    "body_free_material_guard_passed",
    "no_body_leak_guard_passed",
    "no_question_text_guard_passed",
    "no_reviewer_free_text_guard_passed",
    "no_local_path_or_hash_guard_passed",
    "no_terminal_output_traceback_guard_passed",
    "question_text_included",
    "draft_question_text_included",
    "reviewer_free_text_included",
    "raw_input_or_comment_text_included",
    "returned_surface_included",
    "local_path_or_body_hash_included",
    "question_trigger_logic_implemented_here",
    "api_db_rn_response_key_changed_here",
    "body_full_material_leak_detected",
    "question_text_leak_detected",
    "reviewer_free_text_leak_detected",
    "local_path_or_hash_leak_detected",
    "terminal_output_or_traceback_leak_detected",
    "p5_human_blind_qa_confirmed_candidate",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p8_question_design_material_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "p6_limited_human_readfeel_confirmed",
    "p8_detail_design_allowed_here",
    "p8_implementation_spec_finalized_here",
    "p7_complete",
    "p8_start_allowed",
    "release_allowed",
    "actual_human_review_run_here",
    "actual_body_full_packet_generated_here",
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
    "r0_current_source_r48_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_r48_case_matrix_handoff_validated",
    "r3_local_only_actual_packet_generation_preflight_done",
    "r4_actual_review_session_protocol_built",
    "r5_rating_row_ingestion_r48_normalizer_connected",
    "r6_blocker_execution_blocker_ingestion_connected",
    "r7_question_need_observation_row_schema_enum_fixed",
    "r8_question_need_observation_row_normalizer_connected",
    "r9_rating_question_observation_consistency_guard_connected",
    "r10_question_need_observation_summary_built",
    "r11_disposal_receipt_connection_fixed",
    "r12_review_handoff_summary_built",
    "r13_p5_confirmed_candidate_gate_connected",
    "r14_p6_limited_human_readfeel_start_candidate_handoff_built",
    "r15_p8_question_design_material_candidate_handoff_built",
    "r16_no_body_leak_no_question_text_guard_built",
    "public_contract",
    "r49_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R49_R0_R1_FALSE_KEYS,
)
P7_R49_VALIDATION_COMMAND_MATRIX_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r16_no_body_leak_no_question_text_guard_schema_version",
    "r16_no_body_leak_no_question_text_guard_ref",
    "validation_command_group_refs",
    "validation_command_matrix_rows",
    "validation_command_count",
    "r49_target_test_file_refs",
    "r48_regression_test_file_refs",
    "r47_regression_test_file_refs",
    "r46_handoff_regression_test_file_refs",
    "display_api_contract_test_file_refs",
    "p5_core_test_file_refs",
    "p6_subset_optional_command_ref",
    "backend_collect_only_command_ref",
    "rn_no_touch_optional_command_ref",
    "syntax_import_required",
    "r49_target_required",
    "r48_regression_required",
    "r47_regression_required",
    "r46_handoff_regression_required",
    "display_api_contract_required",
    "p5_core_required",
    "p6_subset_optional",
    "backend_collect_only_required",
    "rn_no_touch_optional",
    "validation_commands_reference_only",
    "validation_commands_executed_here",
    "command_output_stored_here",
    "terminal_output_stored_here",
    "full_backend_suite_execution_claimed_here",
    "collect_only_claimed_as_full_backend_green",
    "rn_contract_claimed_as_real_device_modal_readfeel",
    "release_readiness_claim_allowed",
    "p5_human_blind_qa_confirmed_candidate",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p8_question_design_material_candidate",
    "p5_human_blind_qa_confirmed",
    "p6_limited_human_readfeel_start_allowed",
    "p6_limited_human_readfeel_confirmed",
    "p7_complete",
    "p8_start_allowed",
    "release_allowed",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "r0_current_source_r48_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_r48_case_matrix_handoff_validated",
    "r3_local_only_actual_packet_generation_preflight_done",
    "r4_actual_review_session_protocol_built",
    "r5_rating_row_ingestion_r48_normalizer_connected",
    "r6_blocker_execution_blocker_ingestion_connected",
    "r7_question_need_observation_row_schema_enum_fixed",
    "r8_question_need_observation_row_normalizer_connected",
    "r9_rating_question_observation_consistency_guard_connected",
    "r10_question_need_observation_summary_built",
    "r11_disposal_receipt_connection_fixed",
    "r12_review_handoff_summary_built",
    "r13_p5_confirmed_candidate_gate_connected",
    "r14_p6_limited_human_readfeel_start_candidate_handoff_built",
    "r15_p8_question_design_material_candidate_handoff_built",
    "r16_no_body_leak_no_question_text_guard_built",
    "r17_validation_command_matrix_built",
    "public_contract",
    "r49_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R49_R0_R1_FALSE_KEYS,
)
P7_R49_R16_R17_NO_BODY_LEAK_VALIDATION_COMMAND_MATRIX_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r16_no_body_leak_no_question_text_guard_schema_version",
    "r16_no_body_leak_no_question_text_guard_ref",
    "r17_validation_command_matrix_schema_version",
    "r17_validation_command_matrix_ref",
    "implemented_steps",
    "not_yet_implemented_steps",
    "body_free_material_guard_passed",
    "validation_command_matrix_built",
    "validation_commands_executed_here",
    "command_output_stored_here",
    "terminal_output_stored_here",
    "p5_human_blind_qa_confirmed_candidate",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p8_question_design_material_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "p6_limited_human_readfeel_confirmed",
    "p7_complete",
    "p8_start_allowed",
    "release_allowed",
    "first_next_work_ref",
    "next_required_step",
    "r0_current_source_r48_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_r48_case_matrix_handoff_validated",
    "r3_local_only_actual_packet_generation_preflight_done",
    "r4_actual_review_session_protocol_built",
    "r5_rating_row_ingestion_r48_normalizer_connected",
    "r6_blocker_execution_blocker_ingestion_connected",
    "r7_question_need_observation_row_schema_enum_fixed",
    "r8_question_need_observation_row_normalizer_connected",
    "r9_rating_question_observation_consistency_guard_connected",
    "r10_question_need_observation_summary_built",
    "r11_disposal_receipt_connection_fixed",
    "r12_review_handoff_summary_built",
    "r13_p5_confirmed_candidate_gate_connected",
    "r14_p6_limited_human_readfeel_start_candidate_handoff_built",
    "r15_p8_question_design_material_candidate_handoff_built",
    "r16_no_body_leak_no_question_text_guard_built",
    "r17_validation_command_matrix_built",
    "public_contract",
    "r49_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R49_R0_R1_FALSE_KEYS,
)
P7_R49_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "r16_r17_no_body_leak_validation_command_matrix_freeze_schema_version",
    "r16_r17_no_body_leak_validation_command_matrix_freeze_ref",
    "touch_boundary_freeze_required",
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
    "production_touch_candidate_is_r49_helper_only",
    "optional_touch_candidate_is_local_file_ops_only",
    "test_touch_candidate_is_r49_target_only",
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
    "actual_body_full_packet_generated_here",
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
    "post_r18_next_work_ref",
    "r0_current_source_r48_handoff_bridge_refrozen",
    "r1_scope_schema_status_enum_fixed",
    "r2_r48_case_matrix_handoff_validated",
    "r3_local_only_actual_packet_generation_preflight_done",
    "r4_actual_review_session_protocol_built",
    "r5_rating_row_ingestion_r48_normalizer_connected",
    "r6_blocker_execution_blocker_ingestion_connected",
    "r7_question_need_observation_row_schema_enum_fixed",
    "r8_question_need_observation_row_normalizer_connected",
    "r9_rating_question_observation_consistency_guard_connected",
    "r10_question_need_observation_summary_built",
    "r11_disposal_receipt_connection_fixed",
    "r12_review_handoff_summary_built",
    "r13_p5_confirmed_candidate_gate_connected",
    "r14_p6_limited_human_readfeel_start_candidate_handoff_built",
    "r15_p8_question_design_material_candidate_handoff_built",
    "r16_no_body_leak_no_question_text_guard_built",
    "r17_validation_command_matrix_built",
    "r18_touch_candidate_no_touch_boundary_frozen",
    "public_contract",
    "r49_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R49_R0_R1_FALSE_KEYS,
)


def _contains_r49_forbidden_body_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(
            str(key) in P7_R49_BODY_FREE_FORBIDDEN_FIELD_REFS or _contains_r49_forbidden_body_key(child)
            for key, child in value.items()
        )
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_r49_forbidden_body_key(child) for child in value)
    return False


def _assert_r49_body_free(value: Any, *, source: str) -> None:
    if _contains_r49_forbidden_body_key(value):
        raise ValueError(f"{source} contains local-only body, reviewer free text, or question text keys")
    assert_p7_no_body_payload_or_contract_mutation(value, source=source)


def _body_free_markers() -> dict[str, bool]:
    markers = body_free_flags(include_history=True, include_reviewer=True, include_terminal=True)
    markers.update(
        {
            "question_text_included": False,
            "draft_question_text_included": False,
            "question_answer_included": False,
        }
    )
    return markers


def _false_flags() -> dict[str, bool]:
    return {key: False for key in P7_R49_R0_R1_FALSE_KEYS}


def _public_no_touch_contract() -> dict[str, bool]:
    return {
        "api_route_changed": False,
        "request_key_changed": False,
        "api_response_shape_changed": False,
        "public_response_top_level_key_added": False,
        "public_response_key_changed": False,
        "db_schema_changed": False,
        "db_write_path_changed": False,
        "db_migration_changed": False,
        "rn_visible_contract_changed": False,
        "rn_production_files_touched": False,
        "emlis_reply_runtime_changed": False,
        "p5_runtime_changed": False,
        "p5_gate_relaxed": False,
        "release_material_changed": False,
    }


def _safe_snapshot_refs(snapshot_refs: Mapping[str, Any] | None) -> dict[str, str]:
    merged: dict[str, str] = dict(P7_R49_RECEIVED_LOCAL_SNAPSHOT_REFS)
    if snapshot_refs is None:
        return merged
    _assert_r49_body_free(snapshot_refs, source="p7_r49.snapshot_refs")
    for key, value in safe_mapping(snapshot_refs).items():
        clean_key = clean_identifier(key, default="snapshot_ref", max_length=120)
        if clean_key:
            merged[clean_key] = clean_identifier(value, default="unknown", max_length=180)
    return merged


def _r48_boundary(r48_handoff: Mapping[str, Any] | None) -> dict[str, Any]:
    boundary = safe_mapping(r48_handoff) if r48_handoff is not None else build_p7_r48_touch_candidate_no_touch_boundary_freeze()
    assert_p7_r48_touch_candidate_no_touch_boundary_freeze_contract(boundary)
    _assert_r49_body_free(boundary, source="p7_r49.r48_handoff")
    return boundary


def _build_r48_handoff(boundary: Mapping[str, Any]) -> dict[str, Any]:
    data = safe_mapping(boundary)
    if data.get("schema_version") != P7_R48_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION:
        raise ValueError("R49 R0 requires the R48 R18 touch/no-touch boundary freeze handoff")
    if tuple(data.get("implemented_steps") or ()) != P7_R48_R18_IMPLEMENTED_STEPS:
        raise ValueError("R49 R0 requires the full R48 R18 implemented-step handoff")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R48_R18_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R49 R0 requires the R48 handoff to have no remaining R48 implementation steps")
    for key in (
        "actual_human_review_run_here",
        "actual_body_full_packet_generated_here",
        "body_full_writer_created_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_disposal_run_here",
        "actual_disposal_receipt_materialized_here",
        "p5_human_blind_qa_confirmed",
        "p6_limited_human_readfeel_start_allowed",
        "real_device_modal_review_confirmed",
        "p7_complete",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"R49 R0 requires R48 handoff to keep {key}=False")
    if data.get("touch_candidate_boundary_frozen") is not True or data.get("no_touch_boundary_frozen") is not True:
        raise ValueError("R49 R0 requires the R48 no-touch boundary to be frozen")

    return {
        "r48_handoff_required": True,
        "r48_handoff_schema_version": P7_R48_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION,
        "r48_step": P7_R48_STEP,
        "r48_scope": P7_R48_SCOPE,
        "r48_packet_kind": P7_R48_PACKET_KIND,
        "r48_review_kind": P7_R48_REVIEW_KIND,
        "r48_completed_steps": list(P7_R48_R18_IMPLEMENTED_STEPS),
        "r48_implemented_steps": list(P7_R48_R18_IMPLEMENTED_STEPS),
        "r48_not_yet_implemented_steps": list(P7_R48_R18_NOT_YET_IMPLEMENTED_STEPS),
        "r48_next_required_step": P7_R48_R18_NEXT_REQUIRED_STEP_REF,
        "r48_actual_review_packet_footing_ready": True,
        "r48_actual_review_packet_preparation_finished": True,
        "r48_actual_review_executed": False,
        "r48_actual_human_review_run": False,
        "r48_body_full_packet_generated": False,
        "r48_body_full_writer_created": False,
        "r48_rating_rows_materialized": False,
        "r48_blocker_rows_materialized": False,
        "r48_execution_blocker_rows_materialized": False,
        "r48_disposal_executed": False,
        "r48_disposal_run": False,
        "r48_disposal_receipt_materialized": False,
        "p5_human_blind_qa_confirmed": False,
        "r48_p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "r48_p6_limited_human_readfeel_start_allowed": False,
        "real_device_modal_review_confirmed": False,
        "r48_real_device_modal_review_confirmed": False,
        "p7_complete": False,
        "r48_p7_complete": False,
        "p8_start_allowed": False,
        "r48_p8_start_allowed": False,
        "release_allowed": False,
        "r48_release_allowed": False,
        "r48_no_touch_boundary_frozen": True,
        "body_free": True,
    }


def _schema_version_refs() -> dict[str, str]:
    return {
        "r49_review_session_envelope_bodyfree": P7_R49_REVIEW_SESSION_ENVELOPE_BODYFREE_SCHEMA_VERSION,
        "r49_question_need_observation_row_bodyfree": P7_R49_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION,
        "r49_question_need_observation_summary_bodyfree": P7_R49_QUESTION_NEED_OBSERVATION_SUMMARY_BODYFREE_SCHEMA_VERSION,
        "r49_review_handoff_summary_bodyfree": P7_R49_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION,
        "r49_r48_case_matrix_handoff_validation_bodyfree": P7_R49_R48_CASE_MATRIX_HANDOFF_VALIDATION_SCHEMA_VERSION,
        "r49_local_only_actual_packet_generation_preflight_bodyfree": P7_R49_LOCAL_ONLY_ACTUAL_PACKET_GENERATION_PREFLIGHT_SCHEMA_VERSION,
        "r49_r2_r3_case_matrix_preflight_freeze_bodyfree": P7_R49_R2_R3_CASE_MATRIX_PREFLIGHT_FREEZE_SCHEMA_VERSION,
        "r49_actual_review_session_protocol_bodyfree": P7_R49_ACTUAL_REVIEW_SESSION_PROTOCOL_SCHEMA_VERSION,
        "r49_rating_row_ingestion_r48_normalizer_connection_bodyfree": P7_R49_RATING_ROW_INGESTION_R48_NORMALIZER_CONNECTION_SCHEMA_VERSION,
        "r49_r4_r5_protocol_rating_connection_freeze_bodyfree": P7_R49_R4_R5_PROTOCOL_RATING_CONNECTION_FREEZE_SCHEMA_VERSION,
        "r49_blocker_execution_blocker_ingestion_bodyfree": P7_R49_BLOCKER_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION,
        "r49_question_need_observation_row_schema_enum_freeze_bodyfree": P7_R49_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_ENUM_FREEZE_SCHEMA_VERSION,
        "r49_r6_r7_blocker_question_schema_freeze_bodyfree": P7_R49_R6_R7_BLOCKER_QUESTION_SCHEMA_FREEZE_SCHEMA_VERSION,
        "r49_question_need_observation_row_normalizer_bodyfree": P7_R49_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_SCHEMA_VERSION,
        "r49_rating_question_observation_consistency_guard_bodyfree": P7_R49_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        "r49_r8_r9_question_normalizer_consistency_guard_freeze_bodyfree": P7_R49_R8_R9_QUESTION_NORMALIZER_CONSISTENCY_GUARD_FREEZE_SCHEMA_VERSION,
        "r49_disposal_receipt_connection_bodyfree": P7_R49_DISPOSAL_RECEIPT_CONNECTION_SCHEMA_VERSION,
        "r49_r10_r11_question_summary_disposal_connection_freeze_bodyfree": P7_R49_R10_R11_QUESTION_SUMMARY_DISPOSAL_CONNECTION_FREEZE_SCHEMA_VERSION,
        "r49_p5_confirmed_candidate_gate_connection_bodyfree": P7_R49_P5_CONFIRMED_CANDIDATE_GATE_CONNECTION_SCHEMA_VERSION,
        "r49_r12_r13_review_handoff_p5_gate_connection_freeze_bodyfree": P7_R49_R12_R13_REVIEW_HANDOFF_P5_GATE_CONNECTION_FREEZE_SCHEMA_VERSION,
        "r49_p6_limited_human_readfeel_start_candidate_handoff_bodyfree": P7_R49_P6_LIMITED_HUMAN_READFEEL_START_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        "r49_p8_question_design_material_candidate_handoff_bodyfree": P7_R49_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        "r49_r14_r15_p6_p8_candidate_handoff_freeze_bodyfree": P7_R49_R14_R15_P6_P8_CANDIDATE_HANDOFF_FREEZE_SCHEMA_VERSION,
        "r49_no_body_leak_no_question_text_guard_bodyfree": P7_R49_NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_SCHEMA_VERSION,
        "r49_validation_command_matrix_bodyfree": P7_R49_VALIDATION_COMMAND_MATRIX_SCHEMA_VERSION,
        "r49_r16_r17_no_body_leak_validation_command_matrix_freeze_bodyfree": P7_R49_R16_R17_NO_BODY_LEAK_VALIDATION_COMMAND_MATRIX_FREEZE_SCHEMA_VERSION,
        "r48_case_matrix_bodyfree": P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION,
        "r48_r2_r3_local_storage_case_matrix_freeze": P7_R48_R2_R3_LOCAL_STORAGE_CASE_MATRIX_FREEZE_SCHEMA_VERSION,
        "r48_body_full_packet_materialization_guard": P7_R48_BODY_FULL_PACKET_MATERIALIZATION_GUARD_SCHEMA_VERSION,
        "r48_reviewer_packet_local_only": P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION,
        "r48_rating_row_bodyfree": P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION,
        "r48_blocker_row_bodyfree": P7_R48_P5_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "r48_execution_blocker_row_bodyfree": P7_R48_P5_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "r48_disposal_receipt_bodyfree": P7_R48_P5_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION,
        "r48_review_handoff_summary_bodyfree": P7_R48_P5_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION,
    }



def _count_by(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = clean_identifier(safe_mapping(row).get(key), default="unknown", max_length=120)
        counts[value] = counts.get(value, 0) + 1
    return counts


def _case_matrix_handoff_rows_from_r48_matrix(matrix: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row_raw in safe_mapping(matrix).get("case_rows") or []:
        row = safe_mapping(row_raw)
        rows.append(
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
                "body_full_packet_materialized_here": False,
                "local_reviewer_payload_materialized_here": False,
                "body_free": True,
            }
        )
    return rows


def _r49_family_coverage_satisfied(rows: Sequence[Mapping[str, Any]]) -> bool:
    family_counts = _count_by(rows, "family")
    minimum_per_family = int(safe_mapping(P7_R47_P5_FIRST_FORMAL_MINIMUMS).get("minimum_per_family") or 0)
    return all(family_counts.get(family, 0) >= minimum_per_family for family in P5_HUMAN_BLIND_QA_FAMILIES)


def _case_matrix_freeze(
    r48_case_matrix_handoff: Mapping[str, Any] | None,
    *,
    review_session_id: str,
) -> dict[str, Any]:
    freeze = (
        safe_mapping(r48_case_matrix_handoff)
        if r48_case_matrix_handoff is not None
        else build_p7_r48_r2_r3_local_storage_case_matrix_freeze(review_session_id=review_session_id)
    )
    assert_p7_r48_r2_r3_local_storage_case_matrix_freeze_contract(freeze)
    if r48_case_matrix_handoff is not None:
        _assert_r49_body_free(freeze, source="p7_r49.r48_case_matrix_handoff")
    return freeze


def _execution_blocker_ids_from_preflight(
    *,
    local_review_root_status: str,
    guard_block_reasons: Sequence[Any],
    export_violation_reasons: Sequence[Any],
) -> list[str]:
    blockers: list[str] = []
    reasons = set(dedupe_identifiers(guard_block_reasons, limit=40, max_length=160))
    if local_review_root_status == "missing" or "review_packet_generation_blocked_missing_local_root" in reasons:
        blockers.append("r49_review_session_blocked_missing_local_root")
    if local_review_root_status == "invalid" or "review_packet_generation_blocked_invalid_local_root" in reasons or "review_packet_generation_blocked_repo_or_artifact_root" in reasons:
        blockers.append("r49_review_session_blocked_invalid_local_root")
    if "review_packet_generation_blocked_missing_explicit_allow" in reasons:
        blockers.append("r49_review_session_blocked_missing_explicit_allow")
    if "body_full_packet_export_violation" in reasons or export_violation_reasons:
        blockers.append("r49_review_session_blocked_body_full_packet_export_violation")
    return dedupe_identifiers(blockers, limit=20, max_length=160)


def _export_violation_reason_ids(candidate_export_refs: Sequence[Any] | None) -> list[str]:
    reasons: list[str] = []
    for candidate in candidate_export_refs or ():
        reasons.extend(p7_r47_export_candidate_deny_reasons(candidate))
    return dedupe_identifiers(reasons, limit=20, max_length=160)


def _local_review_root_source_from_r48_guard(guard: Mapping[str, Any]) -> str:
    """Return the body-free root source ref from the nested R48 guard material."""

    r4_r5 = safe_mapping(safe_mapping(guard).get("r4_r5_reviewer_packet_schema_freeze"))
    r2_r3 = safe_mapping(r4_r5.get("r2_r3_local_storage_case_matrix_freeze"))
    local_storage_policy = safe_mapping(r2_r3.get("local_storage_policy"))
    return clean_identifier(
        local_storage_policy.get("local_review_root_source"),
        default="bodyfree_preflight",
        max_length=80,
    )


def _build_p7_p8_bridge_rule() -> dict[str, Any]:
    bridge = {
        "bridge_rule_ref": "p7_p8_bridge_question_need_observation_20260619",
        "bridge_rule_source_ref": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619",
        "p7_bridge_only": True,
        "question_need_observation_capture_required": True,
        "question_need_observation_memo_only": True,
        "question_need_observation_body_free_required": True,
        "question_need_observation_bodyfree_required": True,
        "question_need_observation_during_p5_p6_real_device_review_only": True,
        "emlis_readfeel_weakness_must_not_be_hidden_by_questions": True,
        "p5_surface_weakness_must_not_be_hidden_by_questions": True,
        "gate_boundary_weakness_must_not_be_hidden_by_questions": True,
        "p8_design_material_candidate_allowed_later": True,
        "question_text_allowed_here": False,
        "draft_question_text_allowed_here": False,
        "p8_detail_design_allowed_here": False,
        "api_db_rn_response_key_change_allowed_here": False,
        "question_trigger_logic_allowed_here": False,
        "raw_input_or_comment_text_allowed_in_bridge_material": False,
        "returned_surface_allowed_in_bridge_material": False,
        "reviewer_free_text_allowed_in_bridge_material": False,
        "question_text_allowed_in_bridge_material": False,
        "p7_completion_condition_relaxed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "body_free": True,
    }
    bridge.update({key: False for key in P7_R49_QUESTION_IMPLEMENTATION_FALSE_KEYS})
    return bridge


def _safe_review_session_id(value: Any) -> str:
    session_id = clean_identifier(value, default=P7_R49_DEFAULT_REVIEW_SESSION_ID, max_length=140)
    if not session_id:
        raise ValueError("R49 review_session_id must be non-empty")
    return session_id


def _safe_review_session_status(value: Any) -> str:
    status = clean_identifier(value, default=P7_R49_INITIAL_REVIEW_SESSION_STATUS_REF, max_length=80)
    if status not in P7_R49_REVIEW_SESSION_STATUS_REFS:
        raise ValueError("R49 review session status is not in the frozen enum")
    if status != P7_R49_INITIAL_REVIEW_SESSION_STATUS_REF:
        raise ValueError("R49 R0/R1 can only build a NOT_STARTED review session envelope")
    return status


def _assert_required_fields(data: Mapping[str, Any], *, required: Sequence[str], source: str) -> None:
    if set(data) != set(required):
        missing = sorted(set(required) - set(data))
        extra = sorted(set(data) - set(required))
        raise ValueError(f"{source} fields changed; missing={missing[:6]} extra={extra[:6]}")


def _assert_false_flags(
    data: Mapping[str, Any],
    *,
    source: str,
    allowed_true_keys: Sequence[str] = (),
) -> None:
    allowed = set(allowed_true_keys)
    for key in P7_R49_R0_R1_FALSE_KEYS:
        if key in allowed:
            continue
        if key in data and data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=False during R49-0/R49-1")


def _assert_common(
    data: Mapping[str, Any],
    *,
    schema_version: str,
    source: str,
    allowed_true_keys: Sequence[str] = (),
) -> None:
    if data.get("schema_version") != schema_version:
        raise ValueError(f"{source} schema version changed")
    if data.get("phase") != P7_PHASE:
        raise ValueError(f"{source} phase changed")
    if data.get("step") != P7_R49_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R49_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("policy_kind") != P7_R49_POLICY_KIND:
        raise ValueError(f"{source} policy_kind changed")
    if data.get("current_phase") != "P7":
        raise ValueError(f"{source} must remain in P7")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must be body_free=True")
    _assert_false_flags(data, source=source, allowed_true_keys=allowed_true_keys)
    _assert_r49_body_free(data, source=source)
    assert_false_markers(safe_mapping(data.get("public_contract")), source=f"{source}.public_contract")
    assert_false_markers(safe_mapping(data.get("r49_public_no_touch_contract")), source=f"{source}.r49_public_no_touch_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source=f"{source}.body_free_markers")


def build_p7_r49_current_source_r48_handoff_bridge_refreeze(
    *,
    snapshot_refs: Mapping[str, Any] | None = None,
    r48_handoff: Mapping[str, Any] | None = None,
    r48_handoff_boundary: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r49_current_source_r48_handoff_bridge_refreeze",
) -> dict[str, Any]:
    """Build the R49-0 body-free source/R48-handoff/P7-P8-Bridge refreeze."""

    if r48_handoff is not None and r48_handoff_boundary is not None:
        raise ValueError("provide only one R48 handoff value")
    r48 = _r48_boundary(r48_handoff if r48_handoff is not None else r48_handoff_boundary)
    refreeze = {
        "schema_version": P7_R49_CURRENT_SOURCE_R48_HANDOFF_BRIDGE_REFREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R49_STEP,
        "scope": P7_R49_SCOPE,
        "policy_kind": P7_R49_POLICY_KIND,
        "policy_section": "R49-0_current_source_r48_handoff_bridge_rule_refreeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r49_current_source_r48_handoff_bridge_refreeze", max_length=180),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": P7_GIT_CHECKED,
        "source_snapshot_refs": _safe_snapshot_refs(snapshot_refs),
        "r48_handoff": _build_r48_handoff(r48),
        "p7_p8_bridge_rule": _build_p7_p8_bridge_rule(),
        "implemented_steps": list(P7_R49_R0_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R49_R0_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_r48_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": False,
        "question_need_observation_capture_required": True,
        "question_need_observation_rows_required_later": True,
        "first_next_work_ref": P7_R49_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R49_R0_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r49_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r49_current_source_r48_handoff_bridge_refreeze_contract(refreeze)
    return refreeze


def build_p7_r49_review_session_envelope(
    *,
    review_session_id: Any = P7_R49_DEFAULT_REVIEW_SESSION_ID,
    review_session_status: Any = P7_R49_INITIAL_REVIEW_SESSION_STATUS_REF,
    current_source_refreeze: Mapping[str, Any] | None = None,
    current_source_r48_handoff_bridge_refreeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r49_review_session_envelope",
) -> dict[str, Any]:
    """Build the R49-1 body-free review session envelope and enum freeze."""

    if current_source_refreeze is not None and current_source_r48_handoff_bridge_refreeze is not None:
        raise ValueError("provide only one R49-0 refreeze value")
    r0 = (
        safe_mapping(current_source_refreeze)
        if current_source_refreeze is not None
        else safe_mapping(current_source_r48_handoff_bridge_refreeze)
        if current_source_r48_handoff_bridge_refreeze is not None
        else build_p7_r49_current_source_r48_handoff_bridge_refreeze()
    )
    assert_p7_r49_current_source_r48_handoff_bridge_refreeze_contract(r0)
    if current_source_refreeze is not None or current_source_r48_handoff_bridge_refreeze is not None:
        _assert_r49_body_free(r0, source="p7_r49.r0_refreeze")

    schema_refs = _schema_version_refs()
    envelope = {
        "schema_version": P7_R49_REVIEW_SESSION_ENVELOPE_BODYFREE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R49_STEP,
        "scope": P7_R49_SCOPE,
        "policy_kind": P7_R49_POLICY_KIND,
        "policy_section": "R49-1_scope_schema_version_status_enum_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r49_review_session_envelope", max_length=180),
        "review_session_id": _safe_review_session_id(review_session_id),
        "review_kind": P7_R49_REVIEW_KIND,
        "packet_kind": P7_R49_PACKET_KIND,
        "r0_schema_version": P7_R49_CURRENT_SOURCE_R48_HANDOFF_BRIDGE_REFREEZE_SCHEMA_VERSION,
        "r0_bridge_refreeze_schema_version": P7_R49_CURRENT_SOURCE_R48_HANDOFF_BRIDGE_REFREEZE_SCHEMA_VERSION,
        "r0_bridge_refreeze_material_ref": clean_identifier(r0.get("material_id"), default="p7_r49_current_source_r48_handoff_bridge_refreeze", max_length=180),
        "r48_handoff_required": True,
        "r48_case_matrix_required": True,
        "required_total_cases": P7_R49_REQUIRED_TOTAL_CASES,
        "review_session_status": _safe_review_session_status(review_session_status),
        "review_session_status_refs": list(P7_R49_REVIEW_SESSION_STATUS_REFS),
        "question_need_primary_class_refs": list(P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS),
        "ambiguity_kind_refs": list(P7_R49_AMBIGUITY_KIND_REFS),
        "one_question_fit_refs": list(P7_R49_ONE_QUESTION_FIT_REFS),
        "repair_required_ref_refs": list(P7_R49_REPAIR_REQUIRED_REF_REFS),
        "plan_candidate_flag_refs": list(P7_R49_PLAN_CANDIDATE_FLAG_REFS),
        "schema_version_refs": schema_refs,
        "r49_review_session_envelope_schema_version": P7_R49_REVIEW_SESSION_ENVELOPE_BODYFREE_SCHEMA_VERSION,
        "question_need_observation_row_bodyfree_schema_version": P7_R49_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION,
        "question_need_observation_summary_bodyfree_schema_version": P7_R49_QUESTION_NEED_OBSERVATION_SUMMARY_BODYFREE_SCHEMA_VERSION,
        "review_handoff_summary_bodyfree_schema_version": P7_R49_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION,
        "r48_case_matrix_schema_version": P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION,
        "r48_reviewer_packet_local_only_schema_version": P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION,
        "r48_rating_row_bodyfree_schema_version": P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION,
        "r48_blocker_row_bodyfree_schema_version": P7_R48_P5_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "r48_execution_blocker_row_bodyfree_schema_version": P7_R48_P5_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "r48_disposal_receipt_bodyfree_schema_version": P7_R48_P5_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION,
        "r48_review_handoff_summary_bodyfree_schema_version": P7_R48_P5_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION,
        "r48_p5_confirmed_candidate_required_condition_refs": list(P7_R48_P5_CONFIRMED_CANDIDATE_REQUIRED_CONDITION_REFS),
        "r48_p5_first_formal_case_distribution": [list(row) for row in P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION],
        "r48_readfeel_blocker_id_refs": list(P7_R48_READFEEL_BLOCKER_ID_REFS),
        "r47_local_review_root_env_var": P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR,
        "r47_disposal_status_refs": list(P7_R47_DISPOSAL_STATUSES),
        "r47_body_full_packet_retention_hours": P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
        "r47_reviewer_notes_retention_after_rating_hours": P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
        "r47_p5_first_formal_minimums": dict(P7_R47_P5_FIRST_FORMAL_MINIMUMS),
        "r47_p5_reviewer_facing_allowed_field_refs": list(P7_R47_P5_REVIEWER_FACING_ALLOWED_FIELD_REFS),
        "r47_p5_reviewer_facing_forbidden_field_refs": list(P7_R47_P5_REVIEWER_FACING_FORBIDDEN_FIELD_REFS),
        "p5_human_blind_qa_families": list(P5_HUMAN_BLIND_QA_FAMILIES),
        "p5_human_blind_qa_rating_axes": list(P5_HUMAN_BLIND_QA_RATING_AXES),
        "p5_human_blind_qa_target_thresholds": dict(P5_HUMAN_BLIND_QA_TARGETS),
        "r49_scope_fixed": True,
        "r49_schema_versions_fixed": True,
        "review_session_status_enum_fixed": True,
        "question_need_observation_enum_fixed": True,
        "scope_fixed": True,
        "schema_versions_fixed": True,
        "status_enum_fixed": True,
        "question_need_enum_refs_fixed": True,
        "body_full_packet_materialized_here": False,
        "actual_human_review_run_here": False,
        "question_need_observation_required": True,
        "question_need_observation_rows_required": True,
        "question_text_required": False,
        "reviewer_free_text_bodyfree_export_allowed": False,
        "r49_is_p8_question_detail_design": False,
        "question_api_db_rn_response_key_in_scope": False,
        "question_trigger_logic_in_scope": False,
        "implemented_steps": list(P7_R49_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R49_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R49_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R49_R1_NEXT_REQUIRED_STEP_REF,
        "r0_current_source_r48_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "public_contract": public_contract_flags(),
        "r49_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r49_review_session_envelope_contract(envelope)
    return envelope


def build_p7_r49_r0_r1_scope_status_freeze(
    *,
    snapshot_refs: Mapping[str, Any] | None = None,
    r48_handoff: Mapping[str, Any] | None = None,
    r48_handoff_boundary: Mapping[str, Any] | None = None,
    review_session_id: Any = P7_R49_DEFAULT_REVIEW_SESSION_ID,
    review_session_status: Any = P7_R49_INITIAL_REVIEW_SESSION_STATUS_REF,
    material_id: Any = "p7_r49_r0_r1_scope_status_freeze",
) -> dict[str, Any]:
    """Build a compact body-free combined R49-0/R49-1 freeze."""

    if r48_handoff is not None and r48_handoff_boundary is not None:
        raise ValueError("provide only one R48 handoff value")
    r0 = build_p7_r49_current_source_r48_handoff_bridge_refreeze(
        snapshot_refs=snapshot_refs,
        r48_handoff=r48_handoff if r48_handoff is not None else r48_handoff_boundary,
    )
    r1 = build_p7_r49_review_session_envelope(
        review_session_id=review_session_id,
        review_session_status=review_session_status,
        current_source_refreeze=r0,
    )
    combined = {
        "schema_version": P7_R49_R0_R1_SCOPE_STATUS_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R49_STEP,
        "scope": P7_R49_SCOPE,
        "policy_kind": P7_R49_POLICY_KIND,
        "policy_section": "R49-0_R49-1_scope_status_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r49_r0_r1_scope_status_freeze", max_length=180),
        "r0_current_source_r48_handoff_bridge_refreeze": r0,
        "r1_review_session_envelope": r1,
        "implemented_steps": list(P7_R49_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R49_NOT_YET_IMPLEMENTED_STEPS),
        "review_session_status": r1["review_session_status"],
        "review_session_status_refs": list(P7_R49_REVIEW_SESSION_STATUS_REFS),
        "question_need_primary_class_refs": list(P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS),
        "packet_kind": P7_R49_PACKET_KIND,
        "review_kind": P7_R49_REVIEW_KIND,
        "question_need_observation_required": True,
        "question_need_observation_rows_required": True,
        "first_next_work_ref": P7_R49_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R49_R1_NEXT_REQUIRED_STEP_REF,
        "r0_current_source_r48_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "public_contract": public_contract_flags(),
        "r49_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r49_r0_r1_scope_status_freeze_contract(combined)
    return combined



def build_p7_r49_r48_case_matrix_handoff_validation(
    *,
    review_session_envelope: Mapping[str, Any] | None = None,
    r1_review_session_envelope: Mapping[str, Any] | None = None,
    r48_case_matrix_handoff: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r49_r48_case_matrix_handoff_validation",
) -> dict[str, Any]:
    """Validate the R48 24-case matrix handoff without creating body-full material."""

    if review_session_envelope is not None and r1_review_session_envelope is not None:
        raise ValueError("provide only one R49 R1 envelope value")
    envelope = (
        safe_mapping(review_session_envelope)
        if review_session_envelope is not None
        else safe_mapping(r1_review_session_envelope)
        if r1_review_session_envelope is not None
        else build_p7_r49_review_session_envelope()
    )
    assert_p7_r49_review_session_envelope_contract(envelope)
    if review_session_envelope is not None or r1_review_session_envelope is not None:
        _assert_r49_body_free(envelope, source="p7_r49.r1_review_session_envelope")

    review_session_id = _safe_review_session_id(envelope.get("review_session_id"))
    r48_freeze = _case_matrix_freeze(r48_case_matrix_handoff, review_session_id=review_session_id)
    matrix = safe_mapping(r48_freeze.get("p5_case_matrix"))
    assert_p7_r48_p5_first_formal_review_case_matrix_contract(matrix)
    rows = _case_matrix_handoff_rows_from_r48_matrix(matrix)
    case_ref_ids = [row["case_ref_id"] for row in rows]
    blind_case_ids = [row["blind_case_id"] for row in rows]
    packet_ref_ids = [row["packet_ref_id"] for row in rows]
    unique_case_ref_count = len(set(case_ref_ids))
    unique_blind_case_count = len(set(blind_case_ids))
    unique_packet_ref_count = len(set(packet_ref_ids))
    separated = all(case_ref and blind and case_ref != blind for case_ref, blind in zip(case_ref_ids, blind_case_ids))
    packet_refs_present = all(packet_ref_ids)
    family_counts = _count_by(rows, "family")
    role_counts = _count_by(rows, "case_role")

    validation = {
        "schema_version": P7_R49_R48_CASE_MATRIX_HANDOFF_VALIDATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R49_STEP,
        "scope": P7_R49_SCOPE,
        "policy_kind": P7_R49_POLICY_KIND,
        "policy_section": "R49-2_r48_case_matrix_handoff_validation",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r49_r48_case_matrix_handoff_validation", max_length=180),
        "review_session_id": review_session_id,
        "review_kind": P7_R49_REVIEW_KIND,
        "packet_kind": P7_R49_PACKET_KIND,
        "r1_review_session_envelope_schema_version": P7_R49_REVIEW_SESSION_ENVELOPE_BODYFREE_SCHEMA_VERSION,
        "r1_review_session_envelope_ref": clean_identifier(envelope.get("material_id"), default="p7_r49_review_session_envelope", max_length=180),
        "r48_case_matrix_handoff_required": True,
        "r48_case_matrix_handoff_validated": True,
        "r48_case_matrix_schema_version": P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION,
        "r48_r2_r3_case_matrix_freeze_schema_version": P7_R48_R2_R3_LOCAL_STORAGE_CASE_MATRIX_FREEZE_SCHEMA_VERSION,
        "r48_case_matrix_material_ref": clean_identifier(matrix.get("material_id"), default="p7_r48_p5_first_formal_review_case_matrix", max_length=180),
        "r48_case_matrix_row_field_refs": list(P7_R48_P5_CASE_MATRIX_ROW_FIELD_REFS),
        "required_total_cases": P7_R49_REQUIRED_TOTAL_CASES,
        "case_count": len(rows),
        "case_manifest_row_count": len(rows),
        "case_manifest_rows": rows,
        "family_case_counts": family_counts,
        "case_role_counts": role_counts,
        "subscription_tier_ref_counts": _count_by(rows, "subscription_tier_ref"),
        "owned_history_positive_case_count": role_counts.get("positive_history_line", 0) + role_counts.get("positive_owned_history", 0),
        "minimums_satisfied": matrix.get("minimums_satisfied") is True,
        "family_coverage_satisfied": _r49_family_coverage_satisfied(rows),
        "case_ref_id_count": unique_case_ref_count,
        "blind_case_id_count": unique_blind_case_count,
        "packet_ref_id_count": unique_packet_ref_count,
        "blind_case_id_case_ref_separated": separated,
        "packet_ref_id_present_for_all_cases": packet_refs_present,
        "controller_manifest_keeps_case_ref_family_tier": True,
        "reviewer_facing_identifier_policy": "blind_case_id_only",
        "reviewer_receives_blind_case_id": True,
        "reviewer_receives_case_ref_id": False,
        "reviewer_receives_family": False,
        "reviewer_receives_subscription_tier": False,
        "reviewer_receives_expected_result": False,
        "reviewer_receives_gate_result": False,
        "body_free_case_matrix_ready": True,
        "actual_case_matrix_materialized_here": False,
        "body_full_packet_materialized_here": False,
        "local_reviewer_payload_materialized_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "question_need_observation_required": True,
        "question_need_observation_rows_required_later": True,
        "implemented_steps": list(P7_R49_R2_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R49_R2_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R49_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R49_R2_NEXT_REQUIRED_STEP_REF,
        "r0_current_source_r48_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_r48_case_matrix_handoff_validated": True,
        "r3_local_only_actual_packet_generation_preflight_done": False,
        "public_contract": public_contract_flags(),
        "r49_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r49_r48_case_matrix_handoff_validation_contract(validation)
    return validation


def build_p7_r49_local_only_actual_packet_generation_preflight(
    *,
    r49_r48_case_matrix_handoff_validation: Mapping[str, Any] | None = None,
    r2_case_matrix_handoff_validation: Mapping[str, Any] | None = None,
    local_review_root: Any = None,
    repo_roots: Sequence[Any] | None = None,
    export_roots: Sequence[Any] | None = None,
    explicit_body_full_generation_allow: bool = False,
    candidate_export_refs: Sequence[Any] | None = None,
    material_id: Any = "p7_r49_local_only_actual_packet_generation_preflight",
) -> dict[str, Any]:
    """Preflight local-only packet generation without materializing packet bodies."""

    if r49_r48_case_matrix_handoff_validation is not None and r2_case_matrix_handoff_validation is not None:
        raise ValueError("provide only one R49 R2 validation value")
    r2 = (
        safe_mapping(r49_r48_case_matrix_handoff_validation)
        if r49_r48_case_matrix_handoff_validation is not None
        else safe_mapping(r2_case_matrix_handoff_validation)
        if r2_case_matrix_handoff_validation is not None
        else build_p7_r49_r48_case_matrix_handoff_validation()
    )
    assert_p7_r49_r48_case_matrix_handoff_validation_contract(r2)
    if r49_r48_case_matrix_handoff_validation is not None or r2_case_matrix_handoff_validation is not None:
        _assert_r49_body_free(r2, source="p7_r49.r2_case_matrix_handoff_validation")

    review_session_id = _safe_review_session_id(r2.get("review_session_id"))
    guard = build_p7_r48_body_full_packet_materialization_guard(
        local_review_root=local_review_root,
        repo_roots=repo_roots,
        export_roots=export_roots,
        explicit_body_full_generation_allow=explicit_body_full_generation_allow,
    )
    assert_p7_r48_body_full_packet_materialization_guard_contract(guard)
    _assert_r49_body_free(guard, source="p7_r49.r48_body_full_packet_materialization_guard")

    export_violations = _export_violation_reason_ids(candidate_export_refs)
    root_status = clean_identifier(guard.get("local_review_root_status"), default="missing", max_length=40)
    guard_block_reasons = dedupe_identifiers(guard.get("body_full_packet_materialization_block_reason_ids"), limit=40, max_length=160)
    blocker_ids = _execution_blocker_ids_from_preflight(
        local_review_root_status=root_status,
        guard_block_reasons=guard_block_reasons,
        export_violation_reasons=export_violations,
    )
    preflight_passed = guard.get("body_full_packet_materialization_allowed_by_guard") is True and not blocker_ids
    preflight_status = "READY_FOR_LOCAL_ONLY_PACKET_GENERATION" if preflight_passed else "BLOCKED"
    review_status = "NOT_STARTED" if preflight_passed else "PRECHECK_BLOCKED"

    preflight = {
        "schema_version": P7_R49_LOCAL_ONLY_ACTUAL_PACKET_GENERATION_PREFLIGHT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R49_STEP,
        "scope": P7_R49_SCOPE,
        "policy_kind": P7_R49_POLICY_KIND,
        "policy_section": "R49-3_local_only_actual_packet_generation_preflight",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r49_local_only_actual_packet_generation_preflight", max_length=180),
        "review_session_id": review_session_id,
        "review_kind": P7_R49_REVIEW_KIND,
        "packet_kind": P7_R49_PACKET_KIND,
        "r2_case_matrix_handoff_validation_schema_version": P7_R49_R48_CASE_MATRIX_HANDOFF_VALIDATION_SCHEMA_VERSION,
        "r2_case_matrix_handoff_validation_ref": clean_identifier(r2.get("material_id"), default="p7_r49_r48_case_matrix_handoff_validation", max_length=180),
        "r49_r48_case_matrix_handoff_validation": r2,
        "r48_body_full_packet_materialization_guard_schema_version": P7_R48_BODY_FULL_PACKET_MATERIALIZATION_GUARD_SCHEMA_VERSION,
        "r48_body_full_packet_materialization_guard_ref": clean_identifier(guard.get("material_id"), default="p7_r48_body_full_packet_materialization_guard", max_length=180),
        "r48_guard_preflight_used": True,
        "preflight_status": preflight_status,
        "review_session_status": review_status,
        "required_total_cases": P7_R49_REQUIRED_TOTAL_CASES,
        "preflight_case_count": int(r2.get("case_count") or 0),
        "local_review_root_env_var": P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR,
        "local_review_root_source": _local_review_root_source_from_r48_guard(guard),
        "local_review_root_status": root_status,
        "local_review_root_valid": guard.get("local_review_root_valid") is True,
        "explicit_body_full_generation_allow": guard.get("explicit_body_full_generation_allow") is True,
        "root_path_exposed": False,
        "local_absolute_path_included": False,
        "body_full_generation_requires_env_root": True,
        "body_full_generation_requires_explicit_allow": True,
        "local_only_packet_generation_preflight_passed": preflight_passed,
        "local_only_packet_generation_allowed_by_preflight": preflight_passed,
        "body_full_packet_materialization_allowed_by_preflight": preflight_passed,
        "body_full_packet_materialization_block_reason_ids": guard_block_reasons,
        "export_candidate_refs_checked": len(candidate_export_refs or ()),
        "export_violation_reason_ids": export_violations,
        "execution_blocker_ids": blocker_ids,
        "execution_blocker_count": len(blocker_ids),
        "local_packet_output_ref_is_abstract": True,
        "body_full_packet_output_dir_ref": "p7_r49/body_full_packets.local_only",
        "body_full_packet_output_file_ref_template": "p7_r49/body_full_packets.local_only/{blind_case_id}.p5_review_packet.local_only.json",
        "local_packet_export_allowed": False,
        "body_full_packet_export_allowed": False,
        "body_full_packet_git_tracking_allowed": False,
        "body_full_packet_zip_inclusion_allowed": False,
        "release_material_body_full_allowed": False,
        "p7_scorecard_body_full_material_allowed": False,
        "public_meta_body_full_material_allowed": False,
        "body_content_hash_storage_allowed": False,
        "body_full_file_content_hash_storage_allowed": False,
        "generated_local_packet_must_set_local_only": True,
        "generated_local_packet_must_set_must_not_export": True,
        "generated_local_packet_must_set_disposal_required": True,
        "generated_local_packet_schema_version": P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION,
        "generated_local_packet_allowed_field_refs": list(P7_R47_P5_REVIEWER_FACING_ALLOWED_FIELD_REFS),
        "generated_local_packet_forbidden_field_refs": list(P7_R47_P5_REVIEWER_FACING_FORBIDDEN_FIELD_REFS),
        "body_free_material_can_include_local_packet_payload": False,
        "body_free_material_can_include_body_hash": False,
        "preflight_does_not_generate_packet": True,
        "json_schema_file_created_here": False,
        "body_full_packet_materialized_here": False,
        "local_reviewer_payload_materialized_here": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_reviewer_notes_materialized_here": False,
        "actual_disposal_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "body_free_case_matrix_ready": True,
        "question_need_observation_required": True,
        "question_need_observation_rows_required_later": True,
        "implemented_steps": list(P7_R49_R2_R3_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R49_R2_R3_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R49_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R49_R3_NEXT_REQUIRED_STEP_REF,
        "r0_current_source_r48_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_r48_case_matrix_handoff_validated": True,
        "r3_local_only_actual_packet_generation_preflight_done": True,
        "public_contract": public_contract_flags(),
        "r49_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r49_local_only_actual_packet_generation_preflight_contract(preflight)
    return preflight


def build_p7_r49_r2_r3_case_matrix_preflight_freeze(
    *,
    review_session_envelope: Mapping[str, Any] | None = None,
    r48_case_matrix_handoff: Mapping[str, Any] | None = None,
    local_review_root: Any = None,
    repo_roots: Sequence[Any] | None = None,
    export_roots: Sequence[Any] | None = None,
    explicit_body_full_generation_allow: bool = False,
    candidate_export_refs: Sequence[Any] | None = None,
    material_id: Any = "p7_r49_r2_r3_case_matrix_preflight_freeze",
) -> dict[str, Any]:
    """Build a compact body-free R49-2/R49-3 freeze."""

    r2 = build_p7_r49_r48_case_matrix_handoff_validation(
        review_session_envelope=review_session_envelope,
        r48_case_matrix_handoff=r48_case_matrix_handoff,
    )
    r3 = build_p7_r49_local_only_actual_packet_generation_preflight(
        r49_r48_case_matrix_handoff_validation=r2,
        local_review_root=local_review_root,
        repo_roots=repo_roots,
        export_roots=export_roots,
        explicit_body_full_generation_allow=explicit_body_full_generation_allow,
        candidate_export_refs=candidate_export_refs,
    )
    freeze = {
        "schema_version": P7_R49_R2_R3_CASE_MATRIX_PREFLIGHT_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R49_STEP,
        "scope": P7_R49_SCOPE,
        "policy_kind": P7_R49_POLICY_KIND,
        "policy_section": "R49-2_R49-3_case_matrix_preflight_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r49_r2_r3_case_matrix_preflight_freeze", max_length=180),
        "review_session_id": r2["review_session_id"],
        "review_kind": P7_R49_REVIEW_KIND,
        "packet_kind": P7_R49_PACKET_KIND,
        "r2_case_matrix_handoff_validation": r2,
        "r3_local_only_actual_packet_generation_preflight": r3,
        "implemented_steps": list(P7_R49_R2_R3_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R49_R2_R3_NOT_YET_IMPLEMENTED_STEPS),
        "preflight_status": r3["preflight_status"],
        "execution_blocker_ids": list(r3["execution_blocker_ids"]),
        "local_only_packet_generation_allowed_by_preflight": r3["local_only_packet_generation_allowed_by_preflight"],
        "body_full_packet_materialized_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "question_need_observation_required": True,
        "question_need_observation_rows_required_later": True,
        "first_next_work_ref": P7_R49_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R49_R3_NEXT_REQUIRED_STEP_REF,
        "r0_current_source_r48_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_r48_case_matrix_handoff_validated": True,
        "r3_local_only_actual_packet_generation_preflight_done": True,
        "public_contract": public_contract_flags(),
        "r49_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r49_r2_r3_case_matrix_preflight_freeze_contract(freeze)
    return freeze


def assert_p7_r49_current_source_r48_handoff_bridge_refreeze_contract(refreeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(refreeze)
    _assert_required_fields(
        data,
        required=P7_R49_CURRENT_SOURCE_R48_HANDOFF_BRIDGE_REFREEZE_REQUIRED_FIELD_REFS,
        source="p7_r49_r0_refreeze",
    )
    _assert_common(
        data,
        schema_version=P7_R49_CURRENT_SOURCE_R48_HANDOFF_BRIDGE_REFREEZE_SCHEMA_VERSION,
        source="p7_r49_r0_refreeze",
    )
    if data.get("policy_section") != "R49-0_current_source_r48_handoff_bridge_rule_refreeze":
        raise ValueError("R49 R0 policy section changed")
    if data.get("source_mode") != P7_SOURCE_MODE:
        raise ValueError("R49 R0 must remain local snapshot source mode")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError("R49 R0 must not require or claim Git checking")
    r48 = safe_mapping(data.get("r48_handoff"))
    _assert_required_fields(r48, required=P7_R49_R48_HANDOFF_REQUIRED_FIELD_REFS, source="p7_r49_r0.r48_handoff")
    if tuple(r48.get("r48_completed_steps") or ()) != P7_R48_R18_IMPLEMENTED_STEPS:
        raise ValueError("R49 R0 must preserve R48 R18 completed steps")
    if tuple(r48.get("r48_implemented_steps") or ()) != P7_R48_R18_IMPLEMENTED_STEPS:
        raise ValueError("R49 R0 must preserve R48 R18 implemented steps")
    if tuple(r48.get("r48_not_yet_implemented_steps") or ()) != P7_R48_R18_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R49 R0 must preserve completed R48 handoff state")
    for true_key in (
        "r48_handoff_required",
        "r48_actual_review_packet_footing_ready",
        "r48_actual_review_packet_preparation_finished",
        "r48_no_touch_boundary_frozen",
        "body_free",
    ):
        if r48.get(true_key) is not True:
            raise ValueError(f"R49 R0 R48 handoff must keep {true_key}=True")
    for false_key in (
        "r48_actual_review_executed",
        "r48_actual_human_review_run",
        "r48_body_full_packet_generated",
        "r48_body_full_writer_created",
        "r48_rating_rows_materialized",
        "r48_blocker_rows_materialized",
        "r48_execution_blocker_rows_materialized",
        "r48_disposal_executed",
        "r48_disposal_run",
        "r48_disposal_receipt_materialized",
        "p5_human_blind_qa_confirmed",
        "r48_p5_human_blind_qa_confirmed",
        "p6_limited_human_readfeel_start_allowed",
        "r48_p6_limited_human_readfeel_start_allowed",
        "real_device_modal_review_confirmed",
        "r48_real_device_modal_review_confirmed",
        "p7_complete",
        "r48_p7_complete",
        "p8_start_allowed",
        "r48_p8_start_allowed",
        "release_allowed",
        "r48_release_allowed",
    ):
        if r48.get(false_key) is not False:
            raise ValueError(f"R49 R0 R48 handoff must keep {false_key}=False")
    bridge = safe_mapping(data.get("p7_p8_bridge_rule"))
    _assert_required_fields(bridge, required=P7_R49_BRIDGE_RULE_REQUIRED_FIELD_REFS, source="p7_r49_r0.bridge_rule")
    for true_key in (
        "p7_bridge_only",
        "question_need_observation_capture_required",
        "question_need_observation_memo_only",
        "question_need_observation_body_free_required",
        "question_need_observation_bodyfree_required",
        "question_need_observation_during_p5_p6_real_device_review_only",
        "emlis_readfeel_weakness_must_not_be_hidden_by_questions",
        "p5_surface_weakness_must_not_be_hidden_by_questions",
        "gate_boundary_weakness_must_not_be_hidden_by_questions",
        "p8_design_material_candidate_allowed_later",
        "body_free",
    ):
        if bridge.get(true_key) is not True:
            raise ValueError(f"R49 R0 bridge rule must keep {true_key}=True")
    for false_key in (
        *P7_R49_QUESTION_IMPLEMENTATION_FALSE_KEYS,
        "question_text_allowed_here",
        "draft_question_text_allowed_here",
        "p8_detail_design_allowed_here",
        "api_db_rn_response_key_change_allowed_here",
        "question_trigger_logic_allowed_here",
        "raw_input_or_comment_text_allowed_in_bridge_material",
        "returned_surface_allowed_in_bridge_material",
        "reviewer_free_text_allowed_in_bridge_material",
        "question_text_allowed_in_bridge_material",
        "p7_completion_condition_relaxed",
        "p8_start_allowed",
        "release_allowed",
    ):
        if bridge.get(false_key) is not False:
            raise ValueError(f"R49 R0 bridge rule must keep {false_key}=False")
    if data.get("implemented_steps") != list(P7_R49_R0_IMPLEMENTED_STEPS):
        raise ValueError("R49 R0 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R49_R0_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R49 R0 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R49_R0_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R49 R0 must point to R49-1 next")
    if data.get("r0_current_source_r48_handoff_bridge_refrozen") is not True:
        raise ValueError("R49 R0 marker must be true")
    if data.get("r1_scope_schema_status_enum_fixed") is not False:
        raise ValueError("R49 R0 must not mark R1 as fixed")
    if data.get("question_need_observation_capture_required") is not True:
        raise ValueError("R49 R0 must require question need observation capture later")
    if data.get("question_need_observation_rows_required_later") is not True:
        raise ValueError("R49 R0 must require question need observation rows later")
    return True


def assert_p7_r49_review_session_envelope_contract(envelope: Mapping[str, Any]) -> bool:
    data = safe_mapping(envelope)
    _assert_required_fields(
        data,
        required=P7_R49_REVIEW_SESSION_ENVELOPE_REQUIRED_FIELD_REFS,
        source="p7_r49_r1_review_session_envelope",
    )
    _assert_common(
        data,
        schema_version=P7_R49_REVIEW_SESSION_ENVELOPE_BODYFREE_SCHEMA_VERSION,
        source="p7_r49_r1_review_session_envelope",
    )
    if data.get("policy_section") != "R49-1_scope_schema_version_status_enum_freeze":
        raise ValueError("R49 R1 policy section changed")
    if data.get("r0_schema_version") != P7_R49_CURRENT_SOURCE_R48_HANDOFF_BRIDGE_REFREEZE_SCHEMA_VERSION:
        raise ValueError("R49 R1 must reference R0 schema")
    if data.get("review_kind") != P7_R49_REVIEW_KIND or data.get("packet_kind") != P7_R49_PACKET_KIND:
        raise ValueError("R49 R1 packet/review kind changed")
    if data.get("required_total_cases") != P7_R49_REQUIRED_TOTAL_CASES:
        raise ValueError("R49 R1 required total case count must remain 24")
    if data.get("review_session_status") != P7_R49_INITIAL_REVIEW_SESSION_STATUS_REF:
        raise ValueError("R49 R1 review session must remain NOT_STARTED")
    if tuple(data.get("review_session_status_refs") or ()) != P7_R49_REVIEW_SESSION_STATUS_REFS:
        raise ValueError("R49 R1 review session status enum changed")
    if tuple(data.get("question_need_primary_class_refs") or ()) != P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS:
        raise ValueError("R49 R1 question need primary class refs changed")
    if tuple(data.get("ambiguity_kind_refs") or ()) != P7_R49_AMBIGUITY_KIND_REFS:
        raise ValueError("R49 R1 ambiguity kind refs changed")
    if tuple(data.get("one_question_fit_refs") or ()) != P7_R49_ONE_QUESTION_FIT_REFS:
        raise ValueError("R49 R1 one-question fit refs changed")
    if tuple(data.get("repair_required_ref_refs") or ()) != P7_R49_REPAIR_REQUIRED_REF_REFS:
        raise ValueError("R49 R1 repair-required refs changed")
    if tuple(data.get("plan_candidate_flag_refs") or ()) != P7_R49_PLAN_CANDIDATE_FLAG_REFS:
        raise ValueError("R49 R1 plan candidate flags changed")
    if safe_mapping(data.get("schema_version_refs")) != _schema_version_refs():
        raise ValueError("R49 R1 schema version refs changed")
    expected_direct_versions = {
        "r49_review_session_envelope_schema_version": P7_R49_REVIEW_SESSION_ENVELOPE_BODYFREE_SCHEMA_VERSION,
        "question_need_observation_row_bodyfree_schema_version": P7_R49_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION,
        "question_need_observation_summary_bodyfree_schema_version": P7_R49_QUESTION_NEED_OBSERVATION_SUMMARY_BODYFREE_SCHEMA_VERSION,
        "review_handoff_summary_bodyfree_schema_version": P7_R49_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION,
        "r48_case_matrix_schema_version": P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION,
        "r48_reviewer_packet_local_only_schema_version": P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION,
        "r48_rating_row_bodyfree_schema_version": P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION,
        "r48_blocker_row_bodyfree_schema_version": P7_R48_P5_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "r48_execution_blocker_row_bodyfree_schema_version": P7_R48_P5_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "r48_disposal_receipt_bodyfree_schema_version": P7_R48_P5_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION,
        "r48_review_handoff_summary_bodyfree_schema_version": P7_R48_P5_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION,
    }
    for key, expected in expected_direct_versions.items():
        if data.get(key) != expected:
            raise ValueError(f"R49 R1 {key} changed")
    if tuple(data.get("r48_p5_confirmed_candidate_required_condition_refs") or ()) != P7_R48_P5_CONFIRMED_CANDIDATE_REQUIRED_CONDITION_REFS:
        raise ValueError("R49 R1 R48 confirmed-candidate required refs changed")
    if tuple(tuple(row) for row in data.get("r48_p5_first_formal_case_distribution") or ()) != P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION:
        raise ValueError("R49 R1 R48 case distribution changed")
    if tuple(data.get("r48_readfeel_blocker_id_refs") or ()) != P7_R48_READFEEL_BLOCKER_ID_REFS:
        raise ValueError("R49 R1 R48 readfeel blocker refs changed")
    if data.get("r47_local_review_root_env_var") != P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR:
        raise ValueError("R49 R1 R47 local review root env var changed")
    if tuple(data.get("r47_disposal_status_refs") or ()) != P7_R47_DISPOSAL_STATUSES:
        raise ValueError("R49 R1 R47 disposal status refs changed")
    if safe_mapping(data.get("r47_p5_first_formal_minimums")) != dict(P7_R47_P5_FIRST_FORMAL_MINIMUMS):
        raise ValueError("R49 R1 R47 P5 first formal minimums changed")
    if list(data.get("r47_p5_reviewer_facing_allowed_field_refs") or []) != list(P7_R47_P5_REVIEWER_FACING_ALLOWED_FIELD_REFS):
        raise ValueError("R49 R1 reviewer-facing allowed refs changed")
    if list(data.get("r47_p5_reviewer_facing_forbidden_field_refs") or []) != list(P7_R47_P5_REVIEWER_FACING_FORBIDDEN_FIELD_REFS):
        raise ValueError("R49 R1 reviewer-facing forbidden refs changed")
    if tuple(data.get("p5_human_blind_qa_families") or ()) != P5_HUMAN_BLIND_QA_FAMILIES:
        raise ValueError("R49 R1 P5 family refs changed")
    if tuple(data.get("p5_human_blind_qa_rating_axes") or ()) != P5_HUMAN_BLIND_QA_RATING_AXES:
        raise ValueError("R49 R1 P5 rating axes changed")
    if safe_mapping(data.get("p5_human_blind_qa_target_thresholds")) != dict(P5_HUMAN_BLIND_QA_TARGETS):
        raise ValueError("R49 R1 P5 target thresholds changed")
    for true_key in (
        "r48_handoff_required",
        "r48_case_matrix_required",
        "r49_scope_fixed",
        "r49_schema_versions_fixed",
        "review_session_status_enum_fixed",
        "question_need_observation_enum_fixed",
        "scope_fixed",
        "schema_versions_fixed",
        "status_enum_fixed",
        "question_need_enum_refs_fixed",
        "question_need_observation_required",
        "question_need_observation_rows_required",
        "r0_current_source_r48_handoff_bridge_refrozen",
        "r1_scope_schema_status_enum_fixed",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R49 R1 must keep {true_key}=True")
    for false_key in (
        "body_full_packet_materialized_here",
        "actual_human_review_run_here",
        "question_text_required",
        "reviewer_free_text_bodyfree_export_allowed",
        "r49_is_p8_question_detail_design",
        "question_api_db_rn_response_key_in_scope",
        "question_trigger_logic_in_scope",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R49 R1 must keep {false_key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R49_IMPLEMENTED_STEPS:
        raise ValueError("R49 R1 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R49_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R49 R1 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R49_R1_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R49 R1 must point to R49-2 next")
    return True


def assert_p7_r49_r0_r1_scope_status_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_required_fields(
        data,
        required=P7_R49_R0_R1_SCOPE_STATUS_FREEZE_REQUIRED_FIELD_REFS,
        source="p7_r49_r0_r1_scope_status_freeze",
    )
    _assert_common(
        data,
        schema_version=P7_R49_R0_R1_SCOPE_STATUS_FREEZE_SCHEMA_VERSION,
        source="p7_r49_r0_r1_scope_status_freeze",
    )
    if data.get("policy_section") != "R49-0_R49-1_scope_status_freeze":
        raise ValueError("R49 R0/R1 policy section changed")
    assert_p7_r49_current_source_r48_handoff_bridge_refreeze_contract(
        safe_mapping(data.get("r0_current_source_r48_handoff_bridge_refreeze"))
    )
    assert_p7_r49_review_session_envelope_contract(safe_mapping(data.get("r1_review_session_envelope")))
    if tuple(data.get("implemented_steps") or ()) != P7_R49_IMPLEMENTED_STEPS:
        raise ValueError("R49 R0/R1 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R49_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R49 R0/R1 not-yet implemented steps changed")
    if data.get("review_session_status") != P7_R49_INITIAL_REVIEW_SESSION_STATUS_REF:
        raise ValueError("R49 R0/R1 review session must remain NOT_STARTED")
    if tuple(data.get("review_session_status_refs") or ()) != P7_R49_REVIEW_SESSION_STATUS_REFS:
        raise ValueError("R49 R0/R1 review session status enum changed")
    if tuple(data.get("question_need_primary_class_refs") or ()) != P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS:
        raise ValueError("R49 R0/R1 question need primary class refs changed")
    if data.get("packet_kind") != P7_R49_PACKET_KIND or data.get("review_kind") != P7_R49_REVIEW_KIND:
        raise ValueError("R49 R0/R1 packet or review kind changed")
    if data.get("question_need_observation_required") is not True or data.get("question_need_observation_rows_required") is not True:
        raise ValueError("R49 R0/R1 must require question need observation rows later")
    if data.get("r0_current_source_r48_handoff_bridge_refrozen") is not True:
        raise ValueError("R49 R0/R1 must preserve R0 marker")
    if data.get("r1_scope_schema_status_enum_fixed") is not True:
        raise ValueError("R49 R0/R1 must preserve R1 marker")
    if data.get("next_required_step") != P7_R49_R1_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R49 R0/R1 must point to R49-2 next")
    return True


def assert_p7_r49_r48_case_matrix_handoff_validation_contract(validation: Mapping[str, Any]) -> bool:
    data = safe_mapping(validation)
    _assert_required_fields(
        data,
        required=P7_R49_R48_CASE_MATRIX_HANDOFF_VALIDATION_REQUIRED_FIELD_REFS,
        source="p7_r49_r2_r48_case_matrix_handoff_validation",
    )
    _assert_common(
        data,
        schema_version=P7_R49_R48_CASE_MATRIX_HANDOFF_VALIDATION_SCHEMA_VERSION,
        source="p7_r49_r2_r48_case_matrix_handoff_validation",
    )
    if data.get("policy_section") != "R49-2_r48_case_matrix_handoff_validation":
        raise ValueError("R49 R2 policy section changed")
    if data.get("review_session_id") == "":
        raise ValueError("R49 R2 review session id must be non-empty")
    if data.get("review_kind") != P7_R49_REVIEW_KIND or data.get("packet_kind") != P7_R49_PACKET_KIND:
        raise ValueError("R49 R2 packet/review kind changed")
    if data.get("r48_case_matrix_schema_version") != P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION:
        raise ValueError("R49 R2 R48 case matrix schema version changed")
    if data.get("r48_r2_r3_case_matrix_freeze_schema_version") != P7_R48_R2_R3_LOCAL_STORAGE_CASE_MATRIX_FREEZE_SCHEMA_VERSION:
        raise ValueError("R49 R2 R48 R2/R3 freeze schema version changed")
    if tuple(data.get("r48_case_matrix_row_field_refs") or ()) != tuple(P7_R48_P5_CASE_MATRIX_ROW_FIELD_REFS):
        raise ValueError("R49 R2 R48 row-field refs changed")
    rows = [safe_mapping(row) for row in data.get("case_manifest_rows") or []]
    if data.get("required_total_cases") != P7_R49_REQUIRED_TOTAL_CASES:
        raise ValueError("R49 R2 required total case count changed")
    if data.get("case_count") != P7_R49_REQUIRED_TOTAL_CASES or len(rows) != P7_R49_REQUIRED_TOTAL_CASES:
        raise ValueError("R49 R2 requires exactly 24 R48 handoff cases")
    if data.get("case_manifest_row_count") != len(rows):
        raise ValueError("R49 R2 case manifest row count mismatch")
    for row in rows:
        _assert_required_fields(row, required=P7_R49_R48_CASE_MATRIX_HANDOFF_ROW_FIELD_REFS, source="p7_r49_r2.case_manifest_row")
        if row.get("body_free") is not True or row.get("controller_only") is not True:
            raise ValueError("R49 R2 rows must remain body-free controller rows")
        if not row.get("case_ref_id") or not row.get("blind_case_id") or not row.get("packet_ref_id"):
            raise ValueError("R49 R2 case refs must be non-empty")
        if row.get("case_ref_id") == row.get("blind_case_id"):
            raise ValueError("R49 R2 blind_case_id must be separated from case_ref_id")
        for false_key in (
            "reviewer_receives_case_ref_id",
            "reviewer_receives_family",
            "reviewer_receives_subscription_tier",
            "reviewer_receives_expected_result",
            "reviewer_receives_gate_result",
            "body_full_packet_materialized_here",
            "local_reviewer_payload_materialized_here",
        ):
            if row.get(false_key) is not False:
                raise ValueError(f"R49 R2 row must keep {false_key}=False")
        if row.get("reviewer_receives_blind_case_id") is not True:
            raise ValueError("R49 R2 reviewer may only receive blind case ids")
    if data.get("case_ref_id_count") != P7_R49_REQUIRED_TOTAL_CASES:
        raise ValueError("R49 R2 case_ref_id uniqueness count mismatch")
    if data.get("blind_case_id_count") != P7_R49_REQUIRED_TOTAL_CASES:
        raise ValueError("R49 R2 blind_case_id uniqueness count mismatch")
    if data.get("packet_ref_id_count") != P7_R49_REQUIRED_TOTAL_CASES:
        raise ValueError("R49 R2 packet_ref_id uniqueness count mismatch")
    for true_key in (
        "r48_case_matrix_handoff_required",
        "r48_case_matrix_handoff_validated",
        "minimums_satisfied",
        "family_coverage_satisfied",
        "blind_case_id_case_ref_separated",
        "packet_ref_id_present_for_all_cases",
        "controller_manifest_keeps_case_ref_family_tier",
        "reviewer_receives_blind_case_id",
        "body_free_case_matrix_ready",
        "question_need_observation_required",
        "question_need_observation_rows_required_later",
        "r0_current_source_r48_handoff_bridge_refrozen",
        "r1_scope_schema_status_enum_fixed",
        "r2_r48_case_matrix_handoff_validated",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R49 R2 must keep {true_key}=True")
    for false_key in (
        "reviewer_receives_case_ref_id",
        "reviewer_receives_family",
        "reviewer_receives_subscription_tier",
        "reviewer_receives_expected_result",
        "reviewer_receives_gate_result",
        "actual_case_matrix_materialized_here",
        "body_full_packet_materialized_here",
        "local_reviewer_payload_materialized_here",
        "actual_body_full_packet_generated_here",
        "actual_human_review_run_here",
        "r3_local_only_actual_packet_generation_preflight_done",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R49 R2 must keep {false_key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R49_R2_IMPLEMENTED_STEPS:
        raise ValueError("R49 R2 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R49_R2_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R49 R2 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R49_R2_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R49 R2 must point to R49-3 next")
    return True


def assert_p7_r49_local_only_actual_packet_generation_preflight_contract(preflight: Mapping[str, Any]) -> bool:
    data = safe_mapping(preflight)
    _assert_required_fields(
        data,
        required=P7_R49_LOCAL_ONLY_ACTUAL_PACKET_GENERATION_PREFLIGHT_REQUIRED_FIELD_REFS,
        source="p7_r49_r3_local_only_actual_packet_generation_preflight",
    )
    _assert_common(
        data,
        schema_version=P7_R49_LOCAL_ONLY_ACTUAL_PACKET_GENERATION_PREFLIGHT_SCHEMA_VERSION,
        source="p7_r49_r3_local_only_actual_packet_generation_preflight",
    )
    if data.get("policy_section") != "R49-3_local_only_actual_packet_generation_preflight":
        raise ValueError("R49 R3 policy section changed")
    assert_p7_r49_r48_case_matrix_handoff_validation_contract(
        safe_mapping(data.get("r49_r48_case_matrix_handoff_validation"))
    )
    if data.get("r2_case_matrix_handoff_validation_schema_version") != P7_R49_R48_CASE_MATRIX_HANDOFF_VALIDATION_SCHEMA_VERSION:
        raise ValueError("R49 R3 R2 schema version changed")
    if data.get("r48_body_full_packet_materialization_guard_schema_version") != P7_R48_BODY_FULL_PACKET_MATERIALIZATION_GUARD_SCHEMA_VERSION:
        raise ValueError("R49 R3 R48 guard schema version changed")
    if data.get("r48_guard_preflight_used") is not True:
        raise ValueError("R49 R3 must use the R48 guard")
    if data.get("preflight_status") not in P7_R49_LOCAL_ONLY_PREFLIGHT_STATUS_REFS:
        raise ValueError("R49 R3 preflight status is outside the frozen enum")
    if data.get("review_session_status") not in P7_R49_REVIEW_SESSION_STATUS_REFS:
        raise ValueError("R49 R3 review-session status is outside the frozen enum")
    if data.get("required_total_cases") != P7_R49_REQUIRED_TOTAL_CASES or data.get("preflight_case_count") != P7_R49_REQUIRED_TOTAL_CASES:
        raise ValueError("R49 R3 preflight must cover the 24 R48 handoff cases")
    if data.get("local_review_root_env_var") != P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR:
        raise ValueError("R49 R3 local review root env var changed")
    blocker_ids = tuple(data.get("execution_blocker_ids") or ())
    if any(blocker_id not in P7_R49_EXECUTION_BLOCKER_ID_REFS for blocker_id in blocker_ids):
        raise ValueError("R49 R3 execution blocker id is outside the frozen enum")
    if data.get("execution_blocker_count") != len(blocker_ids):
        raise ValueError("R49 R3 execution blocker count mismatch")
    preflight_passed = data.get("preflight_status") == "READY_FOR_LOCAL_ONLY_PACKET_GENERATION"
    if preflight_passed:
        if blocker_ids:
            raise ValueError("R49 R3 ready preflight must not retain blockers")
        if data.get("review_session_status") != "NOT_STARTED":
            raise ValueError("R49 R3 ready preflight must not claim packets are ready or review started")
        if data.get("local_only_packet_generation_allowed_by_preflight") is not True:
            raise ValueError("R49 R3 ready preflight must allow later local-only generation")
    else:
        if not blocker_ids:
            raise ValueError("R49 R3 blocked preflight must explain the execution blocker")
        if data.get("review_session_status") != "PRECHECK_BLOCKED":
            raise ValueError("R49 R3 blocked preflight must mark PRECHECK_BLOCKED")
        if data.get("local_only_packet_generation_allowed_by_preflight") is not False:
            raise ValueError("R49 R3 blocked preflight must not allow local-only generation")
    for true_key in (
        "root_path_exposed",
        "local_absolute_path_included",
        "local_packet_export_allowed",
        "body_full_packet_export_allowed",
        "body_full_packet_git_tracking_allowed",
        "body_full_packet_zip_inclusion_allowed",
        "release_material_body_full_allowed",
        "p7_scorecard_body_full_material_allowed",
        "public_meta_body_full_material_allowed",
        "body_content_hash_storage_allowed",
        "body_full_file_content_hash_storage_allowed",
        "body_free_material_can_include_local_packet_payload",
        "body_free_material_can_include_body_hash",
        "json_schema_file_created_here",
        "body_full_packet_materialized_here",
        "local_reviewer_payload_materialized_here",
        "actual_body_full_packet_generated_here",
        "body_full_writer_created_here",
        "actual_human_review_run_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_reviewer_notes_materialized_here",
        "actual_disposal_run_here",
        "actual_disposal_receipt_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
    ):
        if data.get(true_key) is not False:
            raise ValueError(f"R49 R3 must keep {true_key}=False")
    for required_true in (
        "body_full_generation_requires_env_root",
        "body_full_generation_requires_explicit_allow",
        "local_packet_output_ref_is_abstract",
        "generated_local_packet_must_set_local_only",
        "generated_local_packet_must_set_must_not_export",
        "generated_local_packet_must_set_disposal_required",
        "preflight_does_not_generate_packet",
        "body_free_case_matrix_ready",
        "question_need_observation_required",
        "question_need_observation_rows_required_later",
        "r0_current_source_r48_handoff_bridge_refrozen",
        "r1_scope_schema_status_enum_fixed",
        "r2_r48_case_matrix_handoff_validated",
        "r3_local_only_actual_packet_generation_preflight_done",
    ):
        if data.get(required_true) is not True:
            raise ValueError(f"R49 R3 must keep {required_true}=True")
    if data.get("generated_local_packet_schema_version") != P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION:
        raise ValueError("R49 R3 generated local packet schema version changed")
    if list(data.get("generated_local_packet_allowed_field_refs") or []) != list(P7_R47_P5_REVIEWER_FACING_ALLOWED_FIELD_REFS):
        raise ValueError("R49 R3 generated local packet allowed refs changed")
    if list(data.get("generated_local_packet_forbidden_field_refs") or []) != list(P7_R47_P5_REVIEWER_FACING_FORBIDDEN_FIELD_REFS):
        raise ValueError("R49 R3 generated local packet forbidden refs changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R49_R2_R3_IMPLEMENTED_STEPS:
        raise ValueError("R49 R3 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R49_R2_R3_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R49 R3 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R49_R3_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R49 R3 must point to R49-4 next")
    return True


def assert_p7_r49_r2_r3_case_matrix_preflight_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_required_fields(
        data,
        required=P7_R49_R2_R3_CASE_MATRIX_PREFLIGHT_FREEZE_REQUIRED_FIELD_REFS,
        source="p7_r49_r2_r3_case_matrix_preflight_freeze",
    )
    _assert_common(
        data,
        schema_version=P7_R49_R2_R3_CASE_MATRIX_PREFLIGHT_FREEZE_SCHEMA_VERSION,
        source="p7_r49_r2_r3_case_matrix_preflight_freeze",
    )
    if data.get("policy_section") != "R49-2_R49-3_case_matrix_preflight_freeze":
        raise ValueError("R49 R2/R3 freeze policy section changed")
    assert_p7_r49_r48_case_matrix_handoff_validation_contract(safe_mapping(data.get("r2_case_matrix_handoff_validation")))
    assert_p7_r49_local_only_actual_packet_generation_preflight_contract(
        safe_mapping(data.get("r3_local_only_actual_packet_generation_preflight"))
    )
    if tuple(data.get("implemented_steps") or ()) != P7_R49_R2_R3_IMPLEMENTED_STEPS:
        raise ValueError("R49 R2/R3 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R49_R2_R3_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R49 R2/R3 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R49_R3_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R49 R2/R3 must point to R49-4 next")
    if data.get("body_full_packet_materialized_here") is not False or data.get("actual_body_full_packet_generated_here") is not False:
        raise ValueError("R49 R2/R3 freeze must not materialize body-full packets")
    if data.get("actual_human_review_run_here") is not False:
        raise ValueError("R49 R2/R3 freeze must not run human review")
    for true_key in (
        "question_need_observation_required",
        "question_need_observation_rows_required_later",
        "r0_current_source_r48_handoff_bridge_refrozen",
        "r1_scope_schema_status_enum_fixed",
        "r2_r48_case_matrix_handoff_validated",
        "r3_local_only_actual_packet_generation_preflight_done",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R49 R2/R3 must keep {true_key}=True")
    return True



def _protocol_case_rows_from_r2(r2: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, raw_row in enumerate(safe_mapping(r2).get("case_manifest_rows") or [], start=1):
        row = safe_mapping(raw_row)
        rows.append(
            {
                "reviewer_case_order": index,
                "blind_case_id": clean_identifier(row.get("blind_case_id"), default="blind_case", max_length=160),
                "packet_ref_id": clean_identifier(row.get("packet_ref_id"), default="packet_ref", max_length=160),
                "reviewer_visible_identifier_policy": "blind_case_id_only",
                "reviewer_receives_blind_case_id": True,
                "reviewer_receives_case_ref_id": False,
                "reviewer_receives_family": False,
                "reviewer_receives_subscription_tier": False,
                "reviewer_receives_expected_result": False,
                "reviewer_receives_gate_result": False,
                "case_ref_hidden": True,
                "family_hidden": True,
                "subscription_tier_hidden": True,
                "expected_result_hidden": True,
                "gate_result_hidden": True,
                "packet_ref_id_visible_to_reviewer": False,
                "rating_row_required": True,
                "question_need_observation_row_required": True,
                "question_text_required": False,
                "reviewer_free_text_bodyfree_export_allowed": False,
                "body_full_packet_materialized_here": False,
                "actual_human_review_run_here": False,
                "body_free": True,
            }
        )
    return rows


def _case_manifest_row_for_rating(case_manifest_row: Mapping[str, Any], *, review_session_id: Any) -> dict[str, Any]:
    row = safe_mapping(case_manifest_row)
    _assert_r49_body_free(row, source="p7_r49.case_manifest_row_for_rating")
    return {
        "review_session_id": _safe_review_session_id(review_session_id),
        "packet_ref_id": clean_identifier(row.get("packet_ref_id"), default="packet_ref", max_length=160),
        "blind_case_id": clean_identifier(row.get("blind_case_id"), default="blind_case", max_length=160),
        "case_ref_id": clean_identifier(row.get("case_ref_id"), default="case_ref", max_length=160),
        "family": clean_identifier(row.get("family"), default="unknown", max_length=160),
        "case_role": clean_identifier(row.get("case_role"), default="unknown", max_length=120),
    }


def _validate_r49_rating_review_result(review_result: Mapping[str, Any]) -> None:
    result = safe_mapping(review_result)
    _assert_r49_body_free(result, source="p7_r49.rating_review_result")
    if any(key in result for key in P7_R49_RATING_INGESTION_FORBIDDEN_REVIEW_RESULT_FIELD_REFS):
        raise ValueError("R49 R5 rating ingestion input must not include body, question-observation, reviewer text, or machine metric fields")
    if result.get("machine_metrics_used_for_readfeel") is True or result.get("reviewer_free_text_included") is True:
        raise ValueError("R49 R5 rating ingestion must remain human-readfeel/body-free without reviewer free text")


def build_p7_r49_actual_review_session_protocol(
    *,
    r49_local_only_actual_packet_generation_preflight: Mapping[str, Any] | None = None,
    local_only_actual_packet_generation_preflight: Mapping[str, Any] | None = None,
    review_session_id: Any = P7_R49_DEFAULT_REVIEW_SESSION_ID,
    material_id: Any = "p7_r49_actual_review_session_protocol",
) -> dict[str, Any]:
    """Build the body-free R49-4 reviewer protocol without generating packets or running review."""

    if r49_local_only_actual_packet_generation_preflight is not None and local_only_actual_packet_generation_preflight is not None:
        raise ValueError("provide only one R49 R3 local-only preflight value")
    requested_session_id = _safe_review_session_id(review_session_id)
    preflight = (
        safe_mapping(r49_local_only_actual_packet_generation_preflight)
        if r49_local_only_actual_packet_generation_preflight is not None
        else safe_mapping(local_only_actual_packet_generation_preflight)
        if local_only_actual_packet_generation_preflight is not None
        else build_p7_r49_local_only_actual_packet_generation_preflight()
    )
    assert_p7_r49_local_only_actual_packet_generation_preflight_contract(preflight)
    _assert_r49_body_free(preflight, source="p7_r49.r3_preflight_for_protocol")
    preflight_ready = preflight.get("preflight_status") == "READY_FOR_LOCAL_ONLY_PACKET_GENERATION"
    protocol_rows = _protocol_case_rows_from_r2(safe_mapping(preflight.get("r49_r48_case_matrix_handoff_validation")))
    protocol = {
        "schema_version": P7_R49_ACTUAL_REVIEW_SESSION_PROTOCOL_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R49_STEP,
        "scope": P7_R49_SCOPE,
        "policy_kind": P7_R49_POLICY_KIND,
        "policy_section": "R49-4_actual_review_session_protocol_builder",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r49_actual_review_session_protocol", max_length=160),
        "review_session_id": _safe_review_session_id(preflight.get("review_session_id") or requested_session_id),
        "review_kind": P7_R49_REVIEW_KIND,
        "packet_kind": P7_R49_PACKET_KIND,
        "r3_local_only_preflight_schema_version": P7_R49_LOCAL_ONLY_ACTUAL_PACKET_GENERATION_PREFLIGHT_SCHEMA_VERSION,
        "r3_local_only_preflight_ref": clean_identifier(preflight.get("material_id"), default="p7_r49_local_only_actual_packet_generation_preflight", max_length=160),
        "r49_local_only_actual_packet_generation_preflight": preflight,
        "r48_reviewer_packet_schema_version": P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION,
        "r48_review_prompt_version": P7_R48_REVIEW_PROMPT_VERSION,
        "review_prompt_version": P7_R48_REVIEW_PROMPT_VERSION,
        "required_case_count": P7_R49_REQUIRED_TOTAL_CASES,
        "protocol_case_count": len(protocol_rows),
        "protocol_case_rows": protocol_rows,
        "reviewer_visible_field_refs": list(P7_R48_P5_REVIEWER_PACKET_REVIEWER_VISIBLE_FIELD_REFS),
        "reviewer_hidden_field_refs": ["case_ref_id", "family", "subscription_tier_ref", "expected_result_ref", "gate_result_ref", "controller_only_refs"],
        "reviewer_visible_identifier_policy": "blind_case_id_only",
        "reviewer_reads_blind_case_id_units": True,
        "reviewer_receives_blind_case_id": True,
        "reviewer_receives_case_ref_id": False,
        "reviewer_receives_family": False,
        "reviewer_receives_subscription_tier": False,
        "reviewer_receives_expected_result": False,
        "reviewer_receives_gate_result": False,
        "packet_ref_id_visible_to_reviewer": False,
        "local_only_packet_required_flag_refs": ["local_only", "must_not_export", "disposal_required"],
        "local_only_packet_control_field_refs": list(P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_CONTROL_FIELD_REFS),
        "local_only_packet_required_field_refs": list(P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_REQUIRED_FIELD_REFS),
        "local_only_packet_forbidden_field_refs": list(P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_FORBIDDEN_FIELD_REFS),
        "local_only_body_field_refs": list(P7_R48_P5_REVIEWER_PACKET_BODY_FIELD_REFS),
        "review_question_refs": list(P7_R48_P5_REVIEW_QUESTION_REFS),
        "rating_axes": list(P5_HUMAN_BLIND_QA_RATING_AXES),
        "rating_axis_target_thresholds": dict(P5_HUMAN_BLIND_QA_TARGETS),
        "allowed_verdict_refs": list(P7_R48_P5_REVIEWABLE_VERDICTS),
        "sanitized_reason_id_refs": list(P7_R48_SANITIZED_REASON_ID_REFS),
        "readfeel_blocker_id_refs": list(P7_R48_READFEEL_BLOCKER_ID_REFS),
        "rating_row_required": True,
        "blocker_row_required_when_repair_or_red": True,
        "execution_blocker_separate_from_readfeel": True,
        "question_need_observation_required": True,
        "question_need_observation_row_required_per_case": True,
        "question_need_observation_stage_ref": "p7_p8_bridge_question_need_observation",
        "question_need_primary_class_refs": list(P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS),
        "ambiguity_kind_refs": list(P7_R49_AMBIGUITY_KIND_REFS),
        "one_question_fit_refs": list(P7_R49_ONE_QUESTION_FIT_REFS),
        "repair_required_ref_refs": list(P7_R49_REPAIR_REQUIRED_REF_REFS),
        "plan_candidate_flag_refs": list(P7_R49_PLAN_CANDIDATE_FLAG_REFS),
        "question_text_required": False,
        "question_text_allowed": False,
        "draft_question_text_allowed": False,
        "reviewer_free_text_local_only_allowed": True,
        "reviewer_free_text_bodyfree_export_allowed": False,
        "machine_metric_rating_allowed": False,
        "readfeel_auto_rating_allowed": False,
        "protocol_ready_for_later_local_only_review": preflight_ready,
        "protocol_blocked_by_preflight": not preflight_ready,
        "review_session_status": "NOT_STARTED" if preflight_ready else "PRECHECK_BLOCKED",
        "local_only_packet_generation_allowed_by_preflight": bool(preflight.get("local_only_packet_generation_allowed_by_preflight")),
        "body_full_packet_materialized_here": False,
        "local_reviewer_payload_materialized_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "implemented_steps": list(P7_R49_R4_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R49_R4_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R49_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R49_R4_NEXT_REQUIRED_STEP_REF,
        "r0_current_source_r48_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_r48_case_matrix_handoff_validated": True,
        "r3_local_only_actual_packet_generation_preflight_done": True,
        "r4_actual_review_session_protocol_built": True,
        "public_contract": public_contract_flags(),
        "r49_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r49_actual_review_session_protocol_contract(protocol)
    return protocol


def normalize_p7_r49_p5_rating_row_via_r48_bodyfree(
    *,
    review_result: Mapping[str, Any],
    case_manifest_row: Mapping[str, Any],
    review_session_id: Any = P7_R49_DEFAULT_REVIEW_SESSION_ID,
    reviewer_ref: Any = "local_reviewer_ref",
    reviewed_at: Any = "reviewed_at_unset",
    body_removed: bool = False,
) -> dict[str, Any]:
    """Normalize a sanitized reviewer rating through the R48 body-free rating normalizer."""

    _validate_r49_rating_review_result(review_result)
    case_row = _case_manifest_row_for_rating(case_manifest_row, review_session_id=review_session_id)
    row = normalize_p7_r48_p5_rating_row_bodyfree(
        review_result=review_result,
        case_row=case_row,
        reviewer_ref=reviewer_ref,
        reviewed_at=reviewed_at,
        body_removed=body_removed,
    )
    assert_p7_r48_p5_rating_row_bodyfree_contract(row)
    _assert_r49_body_free(row, source="p7_r49.r5_normalized_rating_row")
    return row


def build_p7_r49_rating_row_ingestion_r48_normalizer_connection(
    *,
    r49_actual_review_session_protocol: Mapping[str, Any] | None = None,
    actual_review_session_protocol: Mapping[str, Any] | None = None,
    r48_rating_row_normalizer_policy: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r49_rating_row_ingestion_r48_normalizer_connection",
) -> dict[str, Any]:
    """Freeze R49-5 to the existing R48 body-free rating row normalizer."""

    if r49_actual_review_session_protocol is not None and actual_review_session_protocol is not None:
        raise ValueError("provide only one R49 R4 protocol value")
    protocol = (
        safe_mapping(r49_actual_review_session_protocol)
        if r49_actual_review_session_protocol is not None
        else safe_mapping(actual_review_session_protocol)
        if actual_review_session_protocol is not None
        else build_p7_r49_actual_review_session_protocol()
    )
    assert_p7_r49_actual_review_session_protocol_contract(protocol)
    _assert_r49_body_free(protocol, source="p7_r49.r4_protocol_for_rating_connection")
    r48_policy = safe_mapping(r48_rating_row_normalizer_policy) if r48_rating_row_normalizer_policy is not None else build_p7_r48_rating_row_normalizer_policy()
    assert_p7_r48_rating_row_normalizer_policy_contract(r48_policy)
    _assert_r49_body_free(r48_policy, source="p7_r49.r48_rating_row_normalizer_policy")
    connection = {
        "schema_version": P7_R49_RATING_ROW_INGESTION_R48_NORMALIZER_CONNECTION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R49_STEP,
        "scope": P7_R49_SCOPE,
        "policy_kind": P7_R49_POLICY_KIND,
        "policy_section": "R49-5_rating_row_ingestion_r48_normalizer_connection",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r49_rating_row_ingestion_r48_normalizer_connection", max_length=160),
        "review_session_id": clean_identifier(protocol.get("review_session_id"), default=P7_R49_DEFAULT_REVIEW_SESSION_ID, max_length=160),
        "review_kind": P7_R49_REVIEW_KIND,
        "packet_kind": P7_R49_PACKET_KIND,
        "r4_protocol_schema_version": P7_R49_ACTUAL_REVIEW_SESSION_PROTOCOL_SCHEMA_VERSION,
        "r4_protocol_ref": clean_identifier(protocol.get("material_id"), default="p7_r49_actual_review_session_protocol", max_length=160),
        "r49_actual_review_session_protocol": protocol,
        "r48_rating_row_normalizer_schema_version": P7_R48_RATING_ROW_NORMALIZER_SCHEMA_VERSION,
        "r48_rating_row_normalizer_policy_ref": clean_identifier(r48_policy.get("material_id"), default="p7_r48_rating_row_normalizer_policy", max_length=160),
        "r48_rating_row_normalizer_policy": r48_policy,
        "r48_rating_row_bodyfree_schema_version": P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION,
        "r48_rating_row_normalizer_function_ref": "normalize_p7_r48_p5_rating_row_bodyfree",
        "r48_rating_row_contract_ref": "assert_p7_r48_p5_rating_row_bodyfree_contract",
        "r48_rating_row_required_field_refs": list(P7_R48_P5_RATING_ROW_REQUIRED_FIELD_REFS),
        "rating_row_ingestion_ready": True,
        "rating_rows_must_be_r48_bodyfree": True,
        "r48_normalizer_connection_fixed": True,
        "r49_does_not_define_independent_rating_axes": True,
        "r49_uses_r48_rating_axes": True,
        "rating_axes": list(P5_HUMAN_BLIND_QA_RATING_AXES),
        "axis_target_thresholds": dict(P5_HUMAN_BLIND_QA_TARGETS),
        "allowed_verdict_refs": list(P7_R48_P5_REVIEWABLE_VERDICTS),
        "sanitized_reason_id_refs": list(P7_R48_SANITIZED_REASON_ID_REFS),
        "readfeel_blocker_id_refs": list(P7_R48_READFEEL_BLOCKER_ID_REFS),
        "missing_axis_scores_pass_allowed": False,
        "extra_axis_scores_allowed": False,
        "machine_metrics_used_for_readfeel": False,
        "readfeel_auto_estimation_allowed": False,
        "reviewer_free_text_included_allowed": False,
        "reviewer_free_text_bodyfree_allowed": False,
        "blocked_or_not_reviewable_must_use_execution_blocker_row": True,
        "rating_rows_present_for_all_cases_required_later": True,
        "synthetic_or_actual_review_result_required_before_row": True,
        "body_removed_required_before_p5_candidate": True,
        "question_need_observation_required": True,
        "question_need_observation_rows_required_later": True,
        "question_observation_ingestion_done_here": False,
        "body_full_packet_materialized_here": False,
        "local_reviewer_payload_materialized_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_reviewer_notes_materialized_here": False,
        "actual_disposal_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "implemented_steps": list(P7_R49_R5_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R49_R5_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R49_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R49_R5_NEXT_REQUIRED_STEP_REF,
        "r0_current_source_r48_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_r48_case_matrix_handoff_validated": True,
        "r3_local_only_actual_packet_generation_preflight_done": True,
        "r4_actual_review_session_protocol_built": True,
        "r5_rating_row_ingestion_r48_normalizer_connected": True,
        "public_contract": public_contract_flags(),
        "r49_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r49_rating_row_ingestion_r48_normalizer_connection_contract(connection)
    return connection


def build_p7_r49_r4_r5_protocol_rating_connection_freeze(
    *,
    r49_local_only_actual_packet_generation_preflight: Mapping[str, Any] | None = None,
    local_only_actual_packet_generation_preflight: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r49_r4_r5_protocol_rating_connection_freeze",
) -> dict[str, Any]:
    protocol = build_p7_r49_actual_review_session_protocol(
        r49_local_only_actual_packet_generation_preflight=r49_local_only_actual_packet_generation_preflight,
        local_only_actual_packet_generation_preflight=local_only_actual_packet_generation_preflight,
    )
    connection = build_p7_r49_rating_row_ingestion_r48_normalizer_connection(
        r49_actual_review_session_protocol=protocol,
    )
    freeze = {
        "schema_version": P7_R49_R4_R5_PROTOCOL_RATING_CONNECTION_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R49_STEP,
        "scope": P7_R49_SCOPE,
        "policy_kind": P7_R49_POLICY_KIND,
        "policy_section": "R49-4_R49-5_protocol_rating_connection_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r49_r4_r5_protocol_rating_connection_freeze", max_length=160),
        "review_session_id": protocol["review_session_id"],
        "review_kind": P7_R49_REVIEW_KIND,
        "packet_kind": P7_R49_PACKET_KIND,
        "r4_actual_review_session_protocol": protocol,
        "r5_rating_row_ingestion_r48_normalizer_connection": connection,
        "implemented_steps": list(P7_R49_R5_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R49_R5_NOT_YET_IMPLEMENTED_STEPS),
        "protocol_ready_for_later_local_only_review": protocol["protocol_ready_for_later_local_only_review"],
        "rating_row_ingestion_ready": True,
        "r48_normalizer_connection_fixed": True,
        "body_full_packet_materialized_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "question_need_observation_required": True,
        "question_need_observation_rows_required_later": True,
        "first_next_work_ref": P7_R49_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R49_R5_NEXT_REQUIRED_STEP_REF,
        "r0_current_source_r48_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_r48_case_matrix_handoff_validated": True,
        "r3_local_only_actual_packet_generation_preflight_done": True,
        "r4_actual_review_session_protocol_built": True,
        "r5_rating_row_ingestion_r48_normalizer_connected": True,
        "public_contract": public_contract_flags(),
        "r49_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r49_r4_r5_protocol_rating_connection_freeze_contract(freeze)
    return freeze


def assert_p7_r49_actual_review_session_protocol_contract(protocol: Mapping[str, Any]) -> bool:
    data = safe_mapping(protocol)
    _assert_required_fields(
        data,
        required=P7_R49_ACTUAL_REVIEW_SESSION_PROTOCOL_REQUIRED_FIELD_REFS,
        source="p7_r49_r4_actual_review_session_protocol",
    )
    _assert_common(
        data,
        schema_version=P7_R49_ACTUAL_REVIEW_SESSION_PROTOCOL_SCHEMA_VERSION,
        source="p7_r49_r4_actual_review_session_protocol",
    )
    if data.get("policy_section") != "R49-4_actual_review_session_protocol_builder":
        raise ValueError("R49 R4 policy section changed")
    assert_p7_r49_local_only_actual_packet_generation_preflight_contract(
        safe_mapping(data.get("r49_local_only_actual_packet_generation_preflight"))
    )
    preflight_ready = safe_mapping(data.get("r49_local_only_actual_packet_generation_preflight")).get("preflight_status") == "READY_FOR_LOCAL_ONLY_PACKET_GENERATION"
    if data.get("protocol_ready_for_later_local_only_review") is not preflight_ready:
        raise ValueError("R49 R4 protocol readiness must mirror R3 preflight readiness")
    if data.get("protocol_blocked_by_preflight") is not (not preflight_ready):
        raise ValueError("R49 R4 protocol blocked marker must mirror R3 preflight readiness")
    if data.get("review_session_status") != ("NOT_STARTED" if preflight_ready else "PRECHECK_BLOCKED"):
        raise ValueError("R49 R4 must not claim LOCAL_PACKETS_READY or REVIEW_IN_PROGRESS")
    if data.get("protocol_case_count") != P7_R49_REQUIRED_TOTAL_CASES or len(data.get("protocol_case_rows") or []) != P7_R49_REQUIRED_TOTAL_CASES:
        raise ValueError("R49 R4 protocol must cover the 24 handoff cases")
    for row in data.get("protocol_case_rows") or []:
        _assert_required_fields(safe_mapping(row), required=P7_R49_ACTUAL_REVIEW_SESSION_PROTOCOL_CASE_ROW_FIELD_REFS, source="p7_r49_r4.protocol_case_row")
        _assert_r49_body_free(row, source="p7_r49_r4.protocol_case_row")
        for hidden_key in ("reviewer_receives_case_ref_id", "reviewer_receives_family", "reviewer_receives_subscription_tier", "reviewer_receives_expected_result", "reviewer_receives_gate_result", "packet_ref_id_visible_to_reviewer", "question_text_required", "reviewer_free_text_bodyfree_export_allowed", "body_full_packet_materialized_here", "actual_human_review_run_here"):
            if safe_mapping(row).get(hidden_key) is not False:
                raise ValueError(f"R49 R4 protocol case row must keep {hidden_key}=False")
    for true_key in (
        "reviewer_reads_blind_case_id_units",
        "reviewer_receives_blind_case_id",
        "rating_row_required",
        "blocker_row_required_when_repair_or_red",
        "execution_blocker_separate_from_readfeel",
        "question_need_observation_required",
        "question_need_observation_row_required_per_case",
        "reviewer_free_text_local_only_allowed",
        "r0_current_source_r48_handoff_bridge_refrozen",
        "r1_scope_schema_status_enum_fixed",
        "r2_r48_case_matrix_handoff_validated",
        "r3_local_only_actual_packet_generation_preflight_done",
        "r4_actual_review_session_protocol_built",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R49 R4 must keep {true_key}=True")
    for false_key in (
        "reviewer_receives_case_ref_id",
        "reviewer_receives_family",
        "reviewer_receives_subscription_tier",
        "reviewer_receives_expected_result",
        "reviewer_receives_gate_result",
        "packet_ref_id_visible_to_reviewer",
        "question_text_required",
        "question_text_allowed",
        "draft_question_text_allowed",
        "reviewer_free_text_bodyfree_export_allowed",
        "machine_metric_rating_allowed",
        "readfeel_auto_rating_allowed",
        "body_full_packet_materialized_here",
        "local_reviewer_payload_materialized_here",
        "actual_body_full_packet_generated_here",
        "actual_human_review_run_here",
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R49 R4 must keep {false_key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R49_R4_IMPLEMENTED_STEPS:
        raise ValueError("R49 R4 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R49_R4_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R49 R4 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R49_R4_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R49 R4 must point to R49-5 next")
    _assert_r49_body_free(data, source="p7_r49_r4_actual_review_session_protocol")
    return True


def assert_p7_r49_rating_row_ingestion_r48_normalizer_connection_contract(connection: Mapping[str, Any]) -> bool:
    data = safe_mapping(connection)
    _assert_required_fields(
        data,
        required=P7_R49_RATING_ROW_INGESTION_R48_NORMALIZER_CONNECTION_REQUIRED_FIELD_REFS,
        source="p7_r49_r5_rating_row_ingestion_r48_normalizer_connection",
    )
    _assert_common(
        data,
        schema_version=P7_R49_RATING_ROW_INGESTION_R48_NORMALIZER_CONNECTION_SCHEMA_VERSION,
        source="p7_r49_r5_rating_row_ingestion_r48_normalizer_connection",
    )
    if data.get("policy_section") != "R49-5_rating_row_ingestion_r48_normalizer_connection":
        raise ValueError("R49 R5 policy section changed")
    assert_p7_r49_actual_review_session_protocol_contract(safe_mapping(data.get("r49_actual_review_session_protocol")))
    assert_p7_r48_rating_row_normalizer_policy_contract(safe_mapping(data.get("r48_rating_row_normalizer_policy")))
    if data.get("r48_rating_row_normalizer_schema_version") != P7_R48_RATING_ROW_NORMALIZER_SCHEMA_VERSION:
        raise ValueError("R49 R5 R48 normalizer schema changed")
    if data.get("r48_rating_row_bodyfree_schema_version") != P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R49 R5 R48 rating row schema changed")
    if data.get("r48_rating_row_normalizer_function_ref") != "normalize_p7_r48_p5_rating_row_bodyfree":
        raise ValueError("R49 R5 must connect to R48 normalizer")
    if data.get("r48_rating_row_contract_ref") != "assert_p7_r48_p5_rating_row_bodyfree_contract":
        raise ValueError("R49 R5 must keep the R48 rating-row contract")
    if tuple(data.get("r48_rating_row_required_field_refs") or ()) != P7_R48_P5_RATING_ROW_REQUIRED_FIELD_REFS:
        raise ValueError("R49 R5 R48 required fields changed")
    if tuple(data.get("rating_axes") or ()) != P5_HUMAN_BLIND_QA_RATING_AXES:
        raise ValueError("R49 R5 rating axes changed")
    if safe_mapping(data.get("axis_target_thresholds")) != dict(P5_HUMAN_BLIND_QA_TARGETS):
        raise ValueError("R49 R5 rating targets changed")
    if tuple(data.get("allowed_verdict_refs") or ()) != P7_R48_P5_REVIEWABLE_VERDICTS:
        raise ValueError("R49 R5 allowed verdict refs changed")
    if tuple(data.get("sanitized_reason_id_refs") or ()) != P7_R48_SANITIZED_REASON_ID_REFS:
        raise ValueError("R49 R5 sanitized reason refs changed")
    if tuple(data.get("readfeel_blocker_id_refs") or ()) != P7_R48_READFEEL_BLOCKER_ID_REFS:
        raise ValueError("R49 R5 blocker refs changed")
    for true_key in (
        "rating_row_ingestion_ready",
        "rating_rows_must_be_r48_bodyfree",
        "r48_normalizer_connection_fixed",
        "r49_does_not_define_independent_rating_axes",
        "r49_uses_r48_rating_axes",
        "blocked_or_not_reviewable_must_use_execution_blocker_row",
        "rating_rows_present_for_all_cases_required_later",
        "synthetic_or_actual_review_result_required_before_row",
        "body_removed_required_before_p5_candidate",
        "question_need_observation_required",
        "question_need_observation_rows_required_later",
        "r0_current_source_r48_handoff_bridge_refrozen",
        "r1_scope_schema_status_enum_fixed",
        "r2_r48_case_matrix_handoff_validated",
        "r3_local_only_actual_packet_generation_preflight_done",
        "r4_actual_review_session_protocol_built",
        "r5_rating_row_ingestion_r48_normalizer_connected",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R49 R5 must keep {true_key}=True")
    for false_key in (
        "missing_axis_scores_pass_allowed",
        "extra_axis_scores_allowed",
        "machine_metrics_used_for_readfeel",
        "readfeel_auto_estimation_allowed",
        "reviewer_free_text_included_allowed",
        "reviewer_free_text_bodyfree_allowed",
        "question_observation_ingestion_done_here",
        "body_full_packet_materialized_here",
        "local_reviewer_payload_materialized_here",
        "actual_body_full_packet_generated_here",
        "actual_human_review_run_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_reviewer_notes_materialized_here",
        "actual_disposal_run_here",
        "actual_disposal_receipt_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R49 R5 must keep {false_key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R49_R5_IMPLEMENTED_STEPS:
        raise ValueError("R49 R5 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R49_R5_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R49 R5 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R49_R5_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R49 R5 must point to R49-6 next")
    _assert_r49_body_free(data, source="p7_r49_r5_rating_row_ingestion_r48_normalizer_connection")
    return True


def assert_p7_r49_r4_r5_protocol_rating_connection_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_required_fields(
        data,
        required=P7_R49_R4_R5_PROTOCOL_RATING_CONNECTION_FREEZE_REQUIRED_FIELD_REFS,
        source="p7_r49_r4_r5_protocol_rating_connection_freeze",
    )
    _assert_common(
        data,
        schema_version=P7_R49_R4_R5_PROTOCOL_RATING_CONNECTION_FREEZE_SCHEMA_VERSION,
        source="p7_r49_r4_r5_protocol_rating_connection_freeze",
    )
    if data.get("policy_section") != "R49-4_R49-5_protocol_rating_connection_freeze":
        raise ValueError("R49 R4/R5 freeze policy section changed")
    protocol = safe_mapping(data.get("r4_actual_review_session_protocol"))
    connection = safe_mapping(data.get("r5_rating_row_ingestion_r48_normalizer_connection"))
    assert_p7_r49_actual_review_session_protocol_contract(protocol)
    assert_p7_r49_rating_row_ingestion_r48_normalizer_connection_contract(connection)
    if tuple(data.get("implemented_steps") or ()) != P7_R49_R5_IMPLEMENTED_STEPS:
        raise ValueError("R49 R4/R5 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R49_R5_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R49 R4/R5 not-yet implemented steps changed")
    if data.get("protocol_ready_for_later_local_only_review") is not protocol.get("protocol_ready_for_later_local_only_review"):
        raise ValueError("R49 R4/R5 protocol readiness mismatch")
    if data.get("rating_row_ingestion_ready") is not True or data.get("r48_normalizer_connection_fixed") is not True:
        raise ValueError("R49 R4/R5 must keep R5 connection ready")
    for false_key in (
        "body_full_packet_materialized_here",
        "actual_body_full_packet_generated_here",
        "actual_human_review_run_here",
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R49 R4/R5 must keep {false_key}=False")
    for true_key in (
        "question_need_observation_required",
        "question_need_observation_rows_required_later",
        "r0_current_source_r48_handoff_bridge_refrozen",
        "r1_scope_schema_status_enum_fixed",
        "r2_r48_case_matrix_handoff_validated",
        "r3_local_only_actual_packet_generation_preflight_done",
        "r4_actual_review_session_protocol_built",
        "r5_rating_row_ingestion_r48_normalizer_connected",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R49 R4/R5 must keep {true_key}=True")
    if data.get("next_required_step") != P7_R49_R5_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R49 R4/R5 must point to R49-6 next")
    _assert_r49_body_free(data, source="p7_r49_r4_r5_protocol_rating_connection_freeze")
    return True



def _validate_r49_blocker_mapping() -> None:
    if set(P7_R49_TO_R48_EXECUTION_BLOCKER_ID_MAP) != set(P7_R49_EXECUTION_BLOCKER_ID_REFS):
        raise ValueError("R49 execution blocker map must cover every R49 execution blocker id")
    unmapped = [value for value in P7_R49_TO_R48_EXECUTION_BLOCKER_ID_MAP.values() if value not in P7_R48_EXECUTION_BLOCKER_ID_REFS]
    if unmapped:
        raise ValueError(f"R49 execution blocker map points outside R48 ids: {unmapped[:3]}")


def _enum_unique(values: Sequence[Any], *, source: str) -> bool:
    cleaned = [clean_identifier(value, default="", max_length=180) for value in values]
    if len(cleaned) != len(set(cleaned)):
        raise ValueError(f"{source} enum refs must be unique")
    return True


def normalize_p7_r49_p5_readfeel_blocker_row_via_r48_bodyfree(
    *,
    case_manifest_row: Mapping[str, Any],
    blocker_id: Any,
    review_session_id: Any = P7_R49_DEFAULT_REVIEW_SESSION_ID,
    blocker_kind: Any = "REPAIR_REQUIRED",
    blocker_status: Any = "OPEN",
    sanitized_reason_ids: Sequence[Any] | None = None,
    body_removed: bool = False,
) -> dict[str, Any]:
    """Normalize a readfeel blocker row through the R48 body-free blocker builder."""

    blocker = clean_identifier(blocker_id, default="", max_length=160)
    if blocker in P7_R49_EXECUTION_BLOCKER_ID_REFS or blocker in P7_R48_EXECUTION_BLOCKER_ID_REFS:
        raise ValueError("R49 R6 readfeel blocker ingestion must not receive execution blocker ids")
    if blocker not in P7_R48_READFEEL_BLOCKER_ID_REFS:
        raise ValueError("R49 R6 readfeel blocker id must be an R48 P5 readfeel blocker id")
    case_row = _case_manifest_row_for_rating(case_manifest_row, review_session_id=review_session_id)
    row = build_p7_r48_p5_blocker_row_bodyfree(
        case_row=case_row,
        blocker_id=blocker,
        blocker_kind=blocker_kind,
        blocker_status=blocker_status,
        sanitized_reason_ids=sanitized_reason_ids,
        body_removed=body_removed,
    )
    assert_p7_r48_p5_blocker_row_bodyfree_contract(row)
    _assert_r49_body_free(row, source="p7_r49.r6_normalized_readfeel_blocker_row")
    return row


def normalize_p7_r49_execution_blocker_row_via_r48_bodyfree(
    *,
    case_manifest_row: Mapping[str, Any],
    execution_blocker_id: Any,
    review_session_id: Any = P7_R49_DEFAULT_REVIEW_SESSION_ID,
    execution_blocker_status: Any = "OPEN",
) -> dict[str, Any]:
    """Normalize an R49 execution blocker row through the R48 body-free execution blocker builder."""

    _validate_r49_blocker_mapping()
    blocker = clean_identifier(execution_blocker_id, default="", max_length=160)
    if blocker in P7_R48_READFEEL_BLOCKER_ID_REFS:
        raise ValueError("R49 R6 execution blocker ingestion must not receive P5 readfeel blocker ids")
    if blocker not in P7_R49_EXECUTION_BLOCKER_ID_REFS:
        raise ValueError("R49 R6 execution blocker id must be in the frozen R49 execution blocker enum")
    case_row = _case_manifest_row_for_rating(case_manifest_row, review_session_id=review_session_id)
    r48_blocker = P7_R49_TO_R48_EXECUTION_BLOCKER_ID_MAP[blocker]
    row = build_p7_r48_p5_execution_blocker_row_bodyfree(
        case_row=case_row,
        execution_blocker_id=r48_blocker,
        execution_blocker_status=execution_blocker_status,
    )
    assert_p7_r48_p5_execution_blocker_row_bodyfree_contract(row)
    _assert_r49_body_free(row, source="p7_r49.r6_normalized_execution_blocker_row")
    return row


def build_p7_r49_blocker_execution_blocker_ingestion(
    *,
    r49_rating_row_ingestion_r48_normalizer_connection: Mapping[str, Any] | None = None,
    rating_row_ingestion_r48_normalizer_connection: Mapping[str, Any] | None = None,
    r48_blocker_execution_blocker_row_builder_policy: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r49_blocker_execution_blocker_ingestion",
) -> dict[str, Any]:
    """Freeze R49-6 blocker / execution-blocker ingestion without materializing rows."""

    if r49_rating_row_ingestion_r48_normalizer_connection is not None and rating_row_ingestion_r48_normalizer_connection is not None:
        raise ValueError("provide only one R49 R5 rating-ingestion connection value")
    connection = (
        safe_mapping(r49_rating_row_ingestion_r48_normalizer_connection)
        if r49_rating_row_ingestion_r48_normalizer_connection is not None
        else safe_mapping(rating_row_ingestion_r48_normalizer_connection)
        if rating_row_ingestion_r48_normalizer_connection is not None
        else build_p7_r49_rating_row_ingestion_r48_normalizer_connection()
    )
    assert_p7_r49_rating_row_ingestion_r48_normalizer_connection_contract(connection)
    _assert_r49_body_free(connection, source="p7_r49.r5_connection_for_blocker_ingestion")
    r48_policy = (
        safe_mapping(r48_blocker_execution_blocker_row_builder_policy)
        if r48_blocker_execution_blocker_row_builder_policy is not None
        else build_p7_r48_blocker_execution_blocker_row_builder_policy(
            rating_row_normalizer_policy=safe_mapping(connection.get("r48_rating_row_normalizer_policy"))
        )
    )
    assert_p7_r48_blocker_execution_blocker_row_builder_policy_contract(r48_policy)
    _assert_r49_body_free(r48_policy, source="p7_r49.r48_blocker_execution_policy")
    _validate_r49_blocker_mapping()
    ingestion = {
        "schema_version": P7_R49_BLOCKER_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R49_STEP,
        "scope": P7_R49_SCOPE,
        "policy_kind": P7_R49_POLICY_KIND,
        "policy_section": "R49-6_blocker_execution_blocker_ingestion",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r49_blocker_execution_blocker_ingestion", max_length=160),
        "review_session_id": clean_identifier(connection.get("review_session_id"), default=P7_R49_DEFAULT_REVIEW_SESSION_ID, max_length=160),
        "review_kind": P7_R49_REVIEW_KIND,
        "packet_kind": P7_R49_PACKET_KIND,
        "r5_rating_ingestion_schema_version": P7_R49_RATING_ROW_INGESTION_R48_NORMALIZER_CONNECTION_SCHEMA_VERSION,
        "r5_rating_ingestion_ref": clean_identifier(connection.get("material_id"), default="p7_r49_rating_row_ingestion_r48_normalizer_connection", max_length=160),
        "r49_rating_row_ingestion_r48_normalizer_connection": connection,
        "r48_blocker_execution_blocker_row_builder_schema_version": P7_R48_BLOCKER_EXECUTION_BLOCKER_ROW_BUILDER_SCHEMA_VERSION,
        "r48_blocker_execution_blocker_row_builder_policy_ref": clean_identifier(r48_policy.get("material_id"), default="p7_r48_blocker_execution_blocker_row_builder_policy", max_length=160),
        "r48_blocker_execution_blocker_row_builder_policy": r48_policy,
        "r48_blocker_row_bodyfree_schema_version": P7_R48_P5_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "r48_execution_blocker_row_bodyfree_schema_version": P7_R48_P5_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "r48_blocker_row_builder_function_ref": "build_p7_r48_p5_blocker_row_bodyfree",
        "r48_execution_blocker_row_builder_function_ref": "build_p7_r48_p5_execution_blocker_row_bodyfree",
        "r48_blocker_row_contract_ref": "assert_p7_r48_p5_blocker_row_bodyfree_contract",
        "r48_execution_blocker_row_contract_ref": "assert_p7_r48_p5_execution_blocker_row_bodyfree_contract",
        "r48_blocker_row_required_field_refs": list(P7_R48_P5_BLOCKER_ROW_REQUIRED_FIELD_REFS),
        "r48_execution_blocker_row_required_field_refs": list(P7_R48_P5_EXECUTION_BLOCKER_ROW_REQUIRED_FIELD_REFS),
        "readfeel_blocker_id_refs": list(P7_R48_READFEEL_BLOCKER_ID_REFS),
        "r49_execution_blocker_id_refs": list(P7_R49_EXECUTION_BLOCKER_ID_REFS),
        "r48_execution_blocker_id_refs": list(P7_R48_EXECUTION_BLOCKER_ID_REFS),
        "r49_to_r48_execution_blocker_id_map": dict(P7_R49_TO_R48_EXECUTION_BLOCKER_ID_MAP),
        "blocker_kind_refs": list(P7_R48_P5_BLOCKER_KINDS),
        "blocker_status_refs": list(P7_R48_P5_BLOCKER_STATUSES),
        "execution_blocker_kind_refs": list(P7_R48_EXECUTION_BLOCKER_KIND_REFS),
        "execution_blocker_status_refs": list(P7_R48_EXECUTION_BLOCKER_STATUS_REFS),
        "forbidden_field_refs": list(P7_R48_P5_RATING_BLOCKER_FORBIDDEN_FIELD_REFS),
        "blocker_execution_ingestion_ready": True,
        "blocker_rows_must_be_r48_bodyfree": True,
        "execution_blocker_rows_must_be_r48_bodyfree": True,
        "r48_builder_connection_fixed": True,
        "readfeel_and_execution_blockers_separated": True,
        "execution_blockers_do_not_assign_readfeel_verdict": True,
        "review_execution_blockers_do_not_create_p5_readfeel_red": True,
        "local_preflight_blockers_map_to_execution_blocker_rows": True,
        "rating_rows_missing_maps_to_execution_blocker_rows": True,
        "question_observation_rows_missing_maps_to_execution_blocker_rows": True,
        "disposal_missing_or_failed_maps_to_execution_blocker_rows": True,
        "body_free_leak_maps_to_execution_blocker_rows": True,
        "reviewer_free_text_included_allowed": False,
        "reviewer_free_text_bodyfree_allowed": False,
        "question_observation_ingestion_done_here": False,
        "body_full_packet_materialized_here": False,
        "local_reviewer_payload_materialized_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_reviewer_notes_materialized_here": False,
        "actual_disposal_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "question_need_observation_required": True,
        "question_need_observation_rows_required_later": True,
        "implemented_steps": list(P7_R49_R6_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R49_R6_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R49_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R49_R6_NEXT_REQUIRED_STEP_REF,
        "r0_current_source_r48_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_r48_case_matrix_handoff_validated": True,
        "r3_local_only_actual_packet_generation_preflight_done": True,
        "r4_actual_review_session_protocol_built": True,
        "r5_rating_row_ingestion_r48_normalizer_connected": True,
        "r6_blocker_execution_blocker_ingestion_connected": True,
        "public_contract": public_contract_flags(),
        "r49_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r49_blocker_execution_blocker_ingestion_contract(ingestion)
    return ingestion


def build_p7_r49_question_need_observation_row_schema_enum_freeze(
    *,
    r49_blocker_execution_blocker_ingestion: Mapping[str, Any] | None = None,
    blocker_execution_blocker_ingestion: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r49_question_need_observation_row_schema_enum_freeze",
) -> dict[str, Any]:
    """Freeze R49-7 question-need observation row schema/enum refs without creating rows."""

    if r49_blocker_execution_blocker_ingestion is not None and blocker_execution_blocker_ingestion is not None:
        raise ValueError("provide only one R49 R6 blocker-ingestion value")
    ingestion = (
        safe_mapping(r49_blocker_execution_blocker_ingestion)
        if r49_blocker_execution_blocker_ingestion is not None
        else safe_mapping(blocker_execution_blocker_ingestion)
        if blocker_execution_blocker_ingestion is not None
        else build_p7_r49_blocker_execution_blocker_ingestion()
    )
    assert_p7_r49_blocker_execution_blocker_ingestion_contract(ingestion)
    _assert_r49_body_free(ingestion, source="p7_r49.r6_ingestion_for_question_schema_freeze")
    for enum_ref, values in (
        ("primary_class", P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS),
        ("ambiguity_kind", P7_R49_AMBIGUITY_KIND_REFS),
        ("one_question_fit", P7_R49_ONE_QUESTION_FIT_REFS),
        ("repair_required", P7_R49_REPAIR_REQUIRED_REF_REFS),
        ("plan_candidate_flags", P7_R49_PLAN_CANDIDATE_FLAG_REFS),
    ):
        _enum_unique(values, source=f"p7_r49.r7.{enum_ref}")
    freeze = {
        "schema_version": P7_R49_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_ENUM_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R49_STEP,
        "scope": P7_R49_SCOPE,
        "policy_kind": P7_R49_POLICY_KIND,
        "policy_section": "R49-7_question_need_observation_row_schema_enum_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r49_question_need_observation_row_schema_enum_freeze", max_length=160),
        "review_session_id": clean_identifier(ingestion.get("review_session_id"), default=P7_R49_DEFAULT_REVIEW_SESSION_ID, max_length=160),
        "review_kind": P7_R49_REVIEW_KIND,
        "packet_kind": P7_R49_PACKET_KIND,
        "r6_blocker_ingestion_schema_version": P7_R49_BLOCKER_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION,
        "r6_blocker_ingestion_ref": clean_identifier(ingestion.get("material_id"), default="p7_r49_blocker_execution_blocker_ingestion", max_length=160),
        "r49_blocker_execution_blocker_ingestion": ingestion,
        "question_need_observation_row_schema_version": P7_R49_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION,
        "question_need_observation_summary_schema_version": P7_R49_QUESTION_NEED_OBSERVATION_SUMMARY_BODYFREE_SCHEMA_VERSION,
        "observation_stage_ref": P7_R49_QUESTION_NEED_OBSERVATION_STAGE_REF,
        "question_need_observation_row_required_field_refs": list(P7_R49_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS),
        "question_need_observation_row_forbidden_field_refs": list(P7_R49_QUESTION_NEED_OBSERVATION_ROW_FORBIDDEN_FIELD_REFS),
        "question_need_primary_class_refs": list(P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS),
        "ambiguity_kind_refs": list(P7_R49_AMBIGUITY_KIND_REFS),
        "one_question_fit_refs": list(P7_R49_ONE_QUESTION_FIT_REFS),
        "repair_required_ref_refs": list(P7_R49_REPAIR_REQUIRED_REF_REFS),
        "plan_candidate_flag_refs": list(P7_R49_PLAN_CANDIDATE_FLAG_REFS),
        "enum_refs_unique": True,
        "primary_class_refs_cover_repair_and_execution_boundaries": True,
        "plan_candidate_flags_are_overlay_not_primary_required": True,
        "question_text_allowed": False,
        "draft_question_text_allowed": False,
        "reviewer_free_text_allowed": False,
        "raw_input_allowed": False,
        "raw_answer_allowed": False,
        "comment_text_body_allowed": False,
        "returned_surface_allowed": False,
        "local_path_allowed": False,
        "body_hash_allowed": False,
        "question_need_observation_row_schema_enum_fixed": True,
        "question_need_observation_row_bodyfree_contract_ready": True,
        "question_need_observation_row_normalizer_implemented_here": False,
        "question_need_observation_row_instances_materialized_here": False,
        "p8_question_implementation_spec_finalized_here": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "body_full_packet_materialized_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_question_need_observation_summary_materialized_here": False,
        "implemented_steps": list(P7_R49_R7_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R49_R7_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R49_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R49_R7_NEXT_REQUIRED_STEP_REF,
        "r0_current_source_r48_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_r48_case_matrix_handoff_validated": True,
        "r3_local_only_actual_packet_generation_preflight_done": True,
        "r4_actual_review_session_protocol_built": True,
        "r5_rating_row_ingestion_r48_normalizer_connected": True,
        "r6_blocker_execution_blocker_ingestion_connected": True,
        "r7_question_need_observation_row_schema_enum_fixed": True,
        "public_contract": public_contract_flags(),
        "r49_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r49_question_need_observation_row_schema_enum_freeze_contract(freeze)
    return freeze


def build_p7_r49_r6_r7_blocker_question_schema_freeze(
    *,
    r49_blocker_execution_blocker_ingestion: Mapping[str, Any] | None = None,
    r49_question_need_observation_row_schema_enum_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r49_r6_r7_blocker_question_schema_freeze",
) -> dict[str, Any]:
    """Combine the R49-6/R49-7 freezes without advancing to R49-8."""

    ingestion = safe_mapping(r49_blocker_execution_blocker_ingestion) if r49_blocker_execution_blocker_ingestion is not None else build_p7_r49_blocker_execution_blocker_ingestion()
    assert_p7_r49_blocker_execution_blocker_ingestion_contract(ingestion)
    freeze = (
        safe_mapping(r49_question_need_observation_row_schema_enum_freeze)
        if r49_question_need_observation_row_schema_enum_freeze is not None
        else build_p7_r49_question_need_observation_row_schema_enum_freeze(r49_blocker_execution_blocker_ingestion=ingestion)
    )
    assert_p7_r49_question_need_observation_row_schema_enum_freeze_contract(freeze)
    combined = {
        "schema_version": P7_R49_R6_R7_BLOCKER_QUESTION_SCHEMA_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R49_STEP,
        "scope": P7_R49_SCOPE,
        "policy_kind": P7_R49_POLICY_KIND,
        "policy_section": "R49-6_R49-7_blocker_question_schema_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r49_r6_r7_blocker_question_schema_freeze", max_length=160),
        "review_session_id": clean_identifier(freeze.get("review_session_id") or ingestion.get("review_session_id"), default=P7_R49_DEFAULT_REVIEW_SESSION_ID, max_length=160),
        "review_kind": P7_R49_REVIEW_KIND,
        "packet_kind": P7_R49_PACKET_KIND,
        "r6_blocker_execution_blocker_ingestion": ingestion,
        "r7_question_need_observation_row_schema_enum_freeze": freeze,
        "implemented_steps": list(P7_R49_R7_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R49_R7_NOT_YET_IMPLEMENTED_STEPS),
        "blocker_execution_ingestion_ready": True,
        "readfeel_and_execution_blockers_separated": True,
        "question_need_observation_row_schema_enum_fixed": True,
        "question_need_observation_required": True,
        "question_need_observation_rows_required_later": True,
        "body_full_packet_materialized_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "question_need_observation_row_normalizer_implemented_here": False,
        "first_next_work_ref": P7_R49_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R49_R7_NEXT_REQUIRED_STEP_REF,
        "r0_current_source_r48_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_r48_case_matrix_handoff_validated": True,
        "r3_local_only_actual_packet_generation_preflight_done": True,
        "r4_actual_review_session_protocol_built": True,
        "r5_rating_row_ingestion_r48_normalizer_connected": True,
        "r6_blocker_execution_blocker_ingestion_connected": True,
        "r7_question_need_observation_row_schema_enum_fixed": True,
        "public_contract": public_contract_flags(),
        "r49_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r49_r6_r7_blocker_question_schema_freeze_contract(combined)
    return combined



def _default_one_question_fit_for_primary(primary_class: str) -> str:
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
    return mapping[primary_class]


def _default_repair_refs_for_primary(primary_class: str) -> list[str]:
    if primary_class == "not_question_emlis_readfeel_repair_required":
        return ["emlis_readfeel_repair_required"]
    if primary_class == "not_question_p5_surface_repair_required":
        return ["p5_surface_repair_required"]
    if primary_class == "not_question_gate_boundary_required":
        return ["gate_boundary_repair_required"]
    return ["no_repair_required"]


def _normalize_r49_plan_candidate_flags(primary_class: str, raw_flags: Any) -> dict[str, bool]:
    flags = {ref: False for ref in P7_R49_PLAN_CANDIDATE_FLAG_REFS}
    supplied = safe_mapping(raw_flags)
    for key, value in supplied.items():
        clean_key = clean_identifier(key, default="", max_length=120)
        if clean_key not in flags:
            raise ValueError("R49 R8 question observation plan_candidate_flags contains an unknown flag")
        flags[clean_key] = bool(value)
    if flags.get("p8_implementation_spec_finalized_here") is True:
        raise ValueError("R49 R8 question observation must not finalize P8 implementation spec")
    if primary_class == "plus_single_question_candidate_later":
        flags["plus_single_question_candidate_later"] = True
    if primary_class == "premium_deep_dive_candidate_later":
        flags["premium_deep_dive_candidate_later"] = True
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
    if primary_class in p8_material_primary_classes:
        flags["p8_design_material_candidate"] = True
    if primary_class in repair_or_execution_primary_classes and flags.get("p8_design_material_candidate") is True:
        raise ValueError("R49 R8 repair/execution observations must not be marked as P8 question design candidates")
    flags["p8_implementation_spec_finalized_here"] = False
    return flags


def _identifier_refs(value: Any, *, source: str, allowed_refs: Sequence[str], default: Sequence[str] | None = None) -> list[str]:
    values = dedupe_identifiers(value if value is not None else default or (), limit=40, max_length=160)
    unknown = [ref for ref in values if ref not in allowed_refs]
    if unknown:
        raise ValueError(f"{source} contains refs outside the frozen enum")
    return values


def _validate_question_observation_semantics(row: Mapping[str, Any], *, execution_blocker_rows: Sequence[Mapping[str, Any]] | None = None) -> None:
    data = safe_mapping(row)
    primary = clean_identifier(data.get("question_need_primary_class"), default="", max_length=160)
    one_fit = clean_identifier(data.get("one_question_fit_ref"), default="", max_length=160)
    repairs = tuple(data.get("repair_required_refs") or ())
    ambiguity = tuple(data.get("ambiguity_kind_refs") or ())
    flags = safe_mapping(data.get("plan_candidate_flags"))
    if primary not in P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS:
        raise ValueError("R49 question observation primary class must use the frozen enum")
    if one_fit not in P7_R49_ONE_QUESTION_FIT_REFS:
        raise ValueError("R49 question observation one_question_fit_ref must use the frozen enum")
    if one_fit != _default_one_question_fit_for_primary(primary):
        raise ValueError("R49 question observation primary class and one-question fit are inconsistent")
    if not repairs:
        raise ValueError("R49 question observation repair_required_refs must be explicit")
    if "no_repair_required" in repairs and len(repairs) > 1:
        raise ValueError("R49 question observation no_repair_required must not be mixed with repair refs")
    if primary.startswith("not_question_"):
        required = tuple(_default_repair_refs_for_primary(primary))
        if not set(required) <= set(repairs):
            raise ValueError("R49 question observation repair primary class requires the matching repair ref")
    if primary.startswith("not_question_") and flags.get("p8_design_material_candidate") is True:
        raise ValueError("R49 question observation repair rows must not become P8 question design candidates")
    if primary == "insufficient_material_execution_blocker":
        if one_fit != "insufficient_material":
            raise ValueError("R49 insufficient-material question observation must use insufficient_material one-question fit")
        matching_execution_rows = []
        for raw in execution_blocker_rows or ():
            erow = safe_mapping(raw)
            if not erow:
                continue
            assert_p7_r48_p5_execution_blocker_row_bodyfree_contract(erow)
            if (
                erow.get("review_session_id") == data.get("review_session_id")
                and erow.get("packet_ref_id") == data.get("packet_ref_id")
                and erow.get("blind_case_id") == data.get("blind_case_id")
                and erow.get("case_ref_id") == data.get("case_ref_id")
            ):
                matching_execution_rows.append(erow)
        if execution_blocker_rows is not None and not matching_execution_rows:
            raise ValueError("R49 insufficient-material question observation requires a matching execution blocker row")
    if primary == "no_question_needed_emlis_can_observe":
        if repairs != ("no_repair_required",):
            raise ValueError("R49 no-question-needed observation must not carry repair refs")
        if ambiguity and set(ambiguity) != {"no_material_ambiguity"}:
            raise ValueError("R49 no-question-needed observation must not carry material ambiguity refs")
    if primary in {"question_may_reduce_overread_risk", "plus_single_question_candidate_later"}:
        if "no_material_ambiguity" in ambiguity or not ambiguity:
            raise ValueError("R49 one-question candidate observations require a body-free ambiguity kind")
        if repairs != ("no_repair_required",):
            raise ValueError("R49 one-question candidate observations must not carry repair refs")
        if flags.get("p8_design_material_candidate") is not True:
            raise ValueError("R49 one-question candidate observations must be P8 design material candidates")
    if primary == "premium_deep_dive_candidate_later":
        if repairs != ("no_repair_required",):
            raise ValueError("R49 premium deep-dive candidate observations must not carry repair refs")
        if flags.get("premium_deep_dive_candidate_later") is not True:
            raise ValueError("R49 premium deep-dive candidate observations require the premium overlay flag")
    for flag_ref in P7_R49_PLAN_CANDIDATE_FLAG_REFS:
        if flag_ref not in flags:
            raise ValueError("R49 question observation plan_candidate_flags must contain every frozen flag")
    if flags.get("p8_implementation_spec_finalized_here") is not False:
        raise ValueError("R49 question observation must not finalize P8 implementation spec")


def _validate_r49_question_observation_result(result: Mapping[str, Any]) -> None:
    data = safe_mapping(result)
    _assert_r49_body_free(data, source="p7_r49.question_observation_result")
    if any(key in data for key in P7_R49_QUESTION_NEED_OBSERVATION_ROW_FORBIDDEN_FIELD_REFS):
        raise ValueError("R49 R8 question observation input must not include body, reviewer text, local path, hash, or question text fields")
    for flag_key in ("question_text_included", "draft_question_text_included", "reviewer_free_text_included"):
        if data.get(flag_key) is True:
            raise ValueError("R49 R8 question observation input must keep text-included flags false")


def normalize_p7_r49_question_need_observation_row_bodyfree(
    *,
    question_observation_result: Mapping[str, Any],
    case_manifest_row: Mapping[str, Any],
    review_session_id: Any = P7_R49_DEFAULT_REVIEW_SESSION_ID,
    body_removed: bool = True,
) -> dict[str, Any]:
    """Normalize a sanitized reviewer question-need selection into one body-free R49 row."""

    _validate_r49_question_observation_result(question_observation_result)
    result = safe_mapping(question_observation_result)
    if body_removed is not True:
        raise ValueError("R49 R8 question observation row requires body_removed=True")
    case = _case_manifest_row_for_rating(case_manifest_row, review_session_id=review_session_id)
    primary = clean_identifier(result.get("question_need_primary_class"), default="", max_length=160)
    if primary not in P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS:
        raise ValueError("R49 R8 question observation primary class must use the frozen enum")
    ambiguity_default = ["no_material_ambiguity"] if primary == "no_question_needed_emlis_can_observe" else []
    ambiguity_refs = _identifier_refs(
        result.get("ambiguity_kind_refs"),
        source="p7_r49_question_observation.ambiguity_kind_refs",
        allowed_refs=P7_R49_AMBIGUITY_KIND_REFS,
        default=ambiguity_default,
    )
    one_question_fit_ref = clean_identifier(
        result.get("one_question_fit_ref"),
        default=_default_one_question_fit_for_primary(primary),
        max_length=160,
    )
    if one_question_fit_ref not in P7_R49_ONE_QUESTION_FIT_REFS:
        raise ValueError("R49 R8 question observation one_question_fit_ref must use the frozen enum")
    repair_refs = _identifier_refs(
        result.get("repair_required_refs"),
        source="p7_r49_question_observation.repair_required_refs",
        allowed_refs=P7_R49_REPAIR_REQUIRED_REF_REFS,
        default=_default_repair_refs_for_primary(primary),
    )
    if not repair_refs:
        repair_refs = _default_repair_refs_for_primary(primary)
    plan_flags = _normalize_r49_plan_candidate_flags(primary, result.get("plan_candidate_flags"))
    sanitized_reason_ids = dedupe_identifiers(
        result.get("sanitized_reason_ids") or [primary],
        limit=20,
        max_length=160,
    )
    row = {
        "schema_version": P7_R49_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION,
        **case,
        "review_kind": P7_R49_REVIEW_KIND,
        "observation_stage": P7_R49_QUESTION_NEED_OBSERVATION_STAGE_REF,
        "question_need_primary_class": primary,
        "ambiguity_kind_refs": ambiguity_refs,
        "one_question_fit_ref": one_question_fit_ref,
        "plan_candidate_flags": plan_flags,
        "repair_required_refs": repair_refs,
        "sanitized_reason_ids": sanitized_reason_ids,
        "question_text_included": False,
        "draft_question_text_included": False,
        "reviewer_free_text_included": False,
        "body_removed": True,
        "body_free": True,
    }
    assert_p7_r49_question_need_observation_row_bodyfree_contract(row)
    return row


def build_p7_r49_question_need_observation_row_normalizer(
    *,
    r49_question_need_observation_row_schema_enum_freeze: Mapping[str, Any] | None = None,
    question_need_observation_row_schema_enum_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r49_question_need_observation_row_normalizer",
) -> dict[str, Any]:
    """Freeze R49-8 question-need row normalization without claiming actual rows."""

    if r49_question_need_observation_row_schema_enum_freeze is not None and question_need_observation_row_schema_enum_freeze is not None:
        raise ValueError("provide only one R49 R7 question-schema freeze value")
    freeze = (
        safe_mapping(r49_question_need_observation_row_schema_enum_freeze)
        if r49_question_need_observation_row_schema_enum_freeze is not None
        else safe_mapping(question_need_observation_row_schema_enum_freeze)
        if question_need_observation_row_schema_enum_freeze is not None
        else build_p7_r49_question_need_observation_row_schema_enum_freeze()
    )
    assert_p7_r49_question_need_observation_row_schema_enum_freeze_contract(freeze)
    _assert_r49_body_free(freeze, source="p7_r49.r7_freeze_for_question_normalizer")
    normalizer = {
        "schema_version": P7_R49_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R49_STEP,
        "scope": P7_R49_SCOPE,
        "policy_kind": P7_R49_POLICY_KIND,
        "policy_section": "R49-8_question_need_observation_row_normalizer",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r49_question_need_observation_row_normalizer", max_length=160),
        "review_session_id": clean_identifier(freeze.get("review_session_id"), default=P7_R49_DEFAULT_REVIEW_SESSION_ID, max_length=160),
        "review_kind": P7_R49_REVIEW_KIND,
        "packet_kind": P7_R49_PACKET_KIND,
        "r7_question_schema_enum_freeze_schema_version": P7_R49_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_ENUM_FREEZE_SCHEMA_VERSION,
        "r7_question_schema_enum_freeze_ref": clean_identifier(freeze.get("material_id"), default="p7_r49_question_need_observation_row_schema_enum_freeze", max_length=160),
        "r49_question_need_observation_row_schema_enum_freeze": freeze,
        "question_need_observation_row_schema_version": P7_R49_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION,
        "question_need_observation_row_normalizer_function_ref": "normalize_p7_r49_question_need_observation_row_bodyfree",
        "question_need_observation_row_contract_ref": "assert_p7_r49_question_need_observation_row_bodyfree_contract",
        "question_need_observation_row_required_field_refs": list(P7_R49_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS),
        "question_need_observation_row_forbidden_field_refs": list(P7_R49_QUESTION_NEED_OBSERVATION_ROW_FORBIDDEN_FIELD_REFS),
        "question_need_primary_class_refs": list(P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS),
        "ambiguity_kind_refs": list(P7_R49_AMBIGUITY_KIND_REFS),
        "one_question_fit_refs": list(P7_R49_ONE_QUESTION_FIT_REFS),
        "repair_required_ref_refs": list(P7_R49_REPAIR_REQUIRED_REF_REFS),
        "plan_candidate_flag_refs": list(P7_R49_PLAN_CANDIDATE_FLAG_REFS),
        "normalizer_ready": True,
        "question_need_observation_rows_must_be_bodyfree": True,
        "body_removed_required_for_question_observation_row": True,
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
        "question_need_observation_row_normalizer_implemented_here": True,
        "question_need_observation_row_instances_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "body_full_packet_materialized_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "implemented_steps": list(P7_R49_R8_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R49_R8_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R49_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R49_R8_NEXT_REQUIRED_STEP_REF,
        "r0_current_source_r48_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_r48_case_matrix_handoff_validated": True,
        "r3_local_only_actual_packet_generation_preflight_done": True,
        "r4_actual_review_session_protocol_built": True,
        "r5_rating_row_ingestion_r48_normalizer_connected": True,
        "r6_blocker_execution_blocker_ingestion_connected": True,
        "r7_question_need_observation_row_schema_enum_fixed": True,
        "r8_question_need_observation_row_normalizer_connected": True,
        "public_contract": public_contract_flags(),
        "r49_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r49_question_need_observation_row_normalizer_contract(normalizer)
    return normalizer


def _ids_match_between_rating_and_question(rating_row: Mapping[str, Any], question_row: Mapping[str, Any]) -> bool:
    for key in ("review_session_id", "packet_ref_id", "blind_case_id", "case_ref_id", "family", "case_role"):
        if safe_mapping(rating_row).get(key) != safe_mapping(question_row).get(key):
            return False
    return True


def assert_p7_r49_rating_vs_question_observation_consistency(
    *,
    rating_row: Mapping[str, Any] | None = None,
    question_need_observation_row: Mapping[str, Any],
    execution_blocker_rows: Sequence[Mapping[str, Any]] | None = None,
) -> bool:
    """Validate that question-need observations do not hide P5 readfeel repair needs."""

    qrow = safe_mapping(question_need_observation_row)
    assert_p7_r49_question_need_observation_row_bodyfree_contract(qrow)
    primary = clean_identifier(qrow.get("question_need_primary_class"), default="", max_length=160)
    if primary == "insufficient_material_execution_blocker":
        _validate_question_observation_semantics(qrow, execution_blocker_rows=execution_blocker_rows or [])
        if rating_row is not None:
            raise ValueError("R49 R9 insufficient-material execution blockers must not also carry a readfeel rating row")
        return True
    if rating_row is None:
        raise ValueError("R49 R9 consistency guard requires a rating row unless the case is execution-blocked")
    rrow = safe_mapping(rating_row)
    assert_p7_r48_p5_rating_row_bodyfree_contract(rrow)
    _assert_r49_body_free(rrow, source="p7_r49.r9_rating_row")
    if not _ids_match_between_rating_and_question(rrow, qrow):
        raise ValueError("R49 R9 rating row and question observation row must refer to the same body-free case ids")
    verdict = clean_identifier(rrow.get("verdict"), default="", max_length=80)
    blocker_ids = tuple(rrow.get("blocker_ids") or ())
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
        raise ValueError("R49 R9 PASS rating must not carry a not-question repair-required primary class")
    if verdict == "PASS" and primary == "insufficient_material_execution_blocker":
        raise ValueError("R49 R9 PASS rating must not carry execution-blocked question observation")
    if verdict in {"RED", "REPAIR_REQUIRED"} and primary in question_candidate_primary_classes | {"no_question_needed_emlis_can_observe", "question_would_make_immediate_observation_heavy"}:
        raise ValueError("R49 R9 RED/REPAIR_REQUIRED rating must not be explained only as a question candidate")
    if verdict in {"RED", "REPAIR_REQUIRED"} and not blocker_ids:
        raise ValueError("R49 R9 RED/REPAIR_REQUIRED rating requires readfeel blocker ids")
    if qrow.get("one_question_fit_ref") == "repair_required_not_question" and set(qrow.get("repair_required_refs") or ()) <= {"no_repair_required"}:
        raise ValueError("R49 R9 repair_required_not_question requires a non-empty repair ref")
    if primary in question_candidate_primary_classes and blocker_ids:
        raise ValueError("R49 R9 question candidate must not clear or coexist as the only explanation for readfeel blockers")
    _validate_question_observation_semantics(qrow)
    return True


def build_p7_r49_rating_question_observation_consistency_guard(
    *,
    r49_question_need_observation_row_normalizer: Mapping[str, Any] | None = None,
    question_need_observation_row_normalizer: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r49_rating_question_observation_consistency_guard",
) -> dict[str, Any]:
    """Freeze R49-9 rating/question-observation consistency guard without running actual review."""

    if r49_question_need_observation_row_normalizer is not None and question_need_observation_row_normalizer is not None:
        raise ValueError("provide only one R49 R8 question normalizer value")
    normalizer = (
        safe_mapping(r49_question_need_observation_row_normalizer)
        if r49_question_need_observation_row_normalizer is not None
        else safe_mapping(question_need_observation_row_normalizer)
        if question_need_observation_row_normalizer is not None
        else build_p7_r49_question_need_observation_row_normalizer()
    )
    assert_p7_r49_question_need_observation_row_normalizer_contract(normalizer)
    _assert_r49_body_free(normalizer, source="p7_r49.r8_normalizer_for_consistency_guard")
    guard = {
        "schema_version": P7_R49_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R49_STEP,
        "scope": P7_R49_SCOPE,
        "policy_kind": P7_R49_POLICY_KIND,
        "policy_section": "R49-9_rating_vs_question_observation_consistency_guard",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r49_rating_question_observation_consistency_guard", max_length=160),
        "review_session_id": clean_identifier(normalizer.get("review_session_id"), default=P7_R49_DEFAULT_REVIEW_SESSION_ID, max_length=160),
        "review_kind": P7_R49_REVIEW_KIND,
        "packet_kind": P7_R49_PACKET_KIND,
        "r8_question_need_observation_row_normalizer_schema_version": P7_R49_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_SCHEMA_VERSION,
        "r8_question_need_observation_row_normalizer_ref": clean_identifier(normalizer.get("material_id"), default="p7_r49_question_need_observation_row_normalizer", max_length=160),
        "r49_question_need_observation_row_normalizer": normalizer,
        "r5_rating_ingestion_schema_version": P7_R49_RATING_ROW_INGESTION_R48_NORMALIZER_CONNECTION_SCHEMA_VERSION,
        "r6_blocker_ingestion_schema_version": P7_R49_BLOCKER_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION,
        "r48_rating_row_bodyfree_schema_version": P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION,
        "r49_question_row_bodyfree_schema_version": P7_R49_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION,
        "r48_execution_blocker_row_bodyfree_schema_version": P7_R48_P5_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "rating_question_consistency_guard_ready": True,
        "p5_weakness_must_not_be_hidden_by_questions": True,
        "rating_and_question_observation_ids_must_match": True,
        "pass_rating_forbids_not_question_repair_primary_class": True,
        "repair_or_red_rating_forbids_question_candidate_primary_only": True,
        "repair_required_not_question_requires_repair_ref": True,
        "insufficient_material_requires_execution_blocker_row": True,
        "question_candidate_cannot_clear_readfeel_blocker": True,
        "consistency_guard_function_ref": "assert_p7_r49_rating_vs_question_observation_consistency",
        "question_need_observation_required": True,
        "question_need_observation_rows_required_later": True,
        "body_full_packet_materialized_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_question_need_observation_summary_materialized_here": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "implemented_steps": list(P7_R49_R9_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R49_R9_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R49_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R49_R9_NEXT_REQUIRED_STEP_REF,
        "r0_current_source_r48_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_r48_case_matrix_handoff_validated": True,
        "r3_local_only_actual_packet_generation_preflight_done": True,
        "r4_actual_review_session_protocol_built": True,
        "r5_rating_row_ingestion_r48_normalizer_connected": True,
        "r6_blocker_execution_blocker_ingestion_connected": True,
        "r7_question_need_observation_row_schema_enum_fixed": True,
        "r8_question_need_observation_row_normalizer_connected": True,
        "r9_rating_question_observation_consistency_guard_connected": True,
        "public_contract": public_contract_flags(),
        "r49_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r49_rating_question_observation_consistency_guard_contract(guard)
    return guard


def build_p7_r49_r8_r9_question_normalizer_consistency_guard_freeze(
    *,
    r49_question_need_observation_row_schema_enum_freeze: Mapping[str, Any] | None = None,
    r49_question_need_observation_row_normalizer: Mapping[str, Any] | None = None,
    r49_rating_question_observation_consistency_guard: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r49_r8_r9_question_normalizer_consistency_guard_freeze",
) -> dict[str, Any]:
    """Combine the R49-8/R49-9 freezes without advancing to summary/disposal work."""

    normalizer = (
        safe_mapping(r49_question_need_observation_row_normalizer)
        if r49_question_need_observation_row_normalizer is not None
        else build_p7_r49_question_need_observation_row_normalizer(
            r49_question_need_observation_row_schema_enum_freeze=r49_question_need_observation_row_schema_enum_freeze
        )
    )
    assert_p7_r49_question_need_observation_row_normalizer_contract(normalizer)
    guard = (
        safe_mapping(r49_rating_question_observation_consistency_guard)
        if r49_rating_question_observation_consistency_guard is not None
        else build_p7_r49_rating_question_observation_consistency_guard(
            r49_question_need_observation_row_normalizer=normalizer
        )
    )
    assert_p7_r49_rating_question_observation_consistency_guard_contract(guard)
    freeze = {
        "schema_version": P7_R49_R8_R9_QUESTION_NORMALIZER_CONSISTENCY_GUARD_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R49_STEP,
        "scope": P7_R49_SCOPE,
        "policy_kind": P7_R49_POLICY_KIND,
        "policy_section": "R49-8_R49-9_question_normalizer_consistency_guard_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r49_r8_r9_question_normalizer_consistency_guard_freeze", max_length=160),
        "review_session_id": clean_identifier(guard.get("review_session_id") or normalizer.get("review_session_id"), default=P7_R49_DEFAULT_REVIEW_SESSION_ID, max_length=160),
        "review_kind": P7_R49_REVIEW_KIND,
        "packet_kind": P7_R49_PACKET_KIND,
        "r8_question_need_observation_row_normalizer": normalizer,
        "r9_rating_question_observation_consistency_guard": guard,
        "implemented_steps": list(P7_R49_R9_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R49_R9_NOT_YET_IMPLEMENTED_STEPS),
        "question_need_observation_row_normalizer_implemented_here": True,
        "rating_question_consistency_guard_ready": True,
        "p5_weakness_must_not_be_hidden_by_questions": True,
        "question_need_observation_required": True,
        "question_need_observation_rows_required_later": True,
        "body_full_packet_materialized_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_question_need_observation_summary_materialized_here": False,
        "first_next_work_ref": P7_R49_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R49_R9_NEXT_REQUIRED_STEP_REF,
        "r0_current_source_r48_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_r48_case_matrix_handoff_validated": True,
        "r3_local_only_actual_packet_generation_preflight_done": True,
        "r4_actual_review_session_protocol_built": True,
        "r5_rating_row_ingestion_r48_normalizer_connected": True,
        "r6_blocker_execution_blocker_ingestion_connected": True,
        "r7_question_need_observation_row_schema_enum_fixed": True,
        "r8_question_need_observation_row_normalizer_connected": True,
        "r9_rating_question_observation_consistency_guard_connected": True,
        "public_contract": public_contract_flags(),
        "r49_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r49_r8_r9_question_normalizer_consistency_guard_freeze_contract(freeze)
    return freeze

def assert_p7_r49_blocker_execution_blocker_ingestion_contract(ingestion: Mapping[str, Any]) -> bool:
    data = safe_mapping(ingestion)
    _assert_required_fields(
        data,
        required=P7_R49_BLOCKER_EXECUTION_BLOCKER_INGESTION_REQUIRED_FIELD_REFS,
        source="p7_r49_r6_blocker_execution_blocker_ingestion",
    )
    _assert_common(
        data,
        schema_version=P7_R49_BLOCKER_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION,
        source="p7_r49_r6_blocker_execution_blocker_ingestion",
    )
    if data.get("policy_section") != "R49-6_blocker_execution_blocker_ingestion":
        raise ValueError("R49 R6 policy section changed")
    assert_p7_r49_rating_row_ingestion_r48_normalizer_connection_contract(safe_mapping(data.get("r49_rating_row_ingestion_r48_normalizer_connection")))
    assert_p7_r48_blocker_execution_blocker_row_builder_policy_contract(safe_mapping(data.get("r48_blocker_execution_blocker_row_builder_policy")))
    if data.get("r48_blocker_execution_blocker_row_builder_schema_version") != P7_R48_BLOCKER_EXECUTION_BLOCKER_ROW_BUILDER_SCHEMA_VERSION:
        raise ValueError("R49 R6 R48 blocker/execution builder schema changed")
    if data.get("r48_blocker_row_bodyfree_schema_version") != P7_R48_P5_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R49 R6 R48 blocker row schema changed")
    if data.get("r48_execution_blocker_row_bodyfree_schema_version") != P7_R48_P5_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R49 R6 R48 execution blocker row schema changed")
    if tuple(data.get("r48_blocker_row_required_field_refs") or ()) != P7_R48_P5_BLOCKER_ROW_REQUIRED_FIELD_REFS:
        raise ValueError("R49 R6 R48 blocker required fields changed")
    if tuple(data.get("r48_execution_blocker_row_required_field_refs") or ()) != P7_R48_P5_EXECUTION_BLOCKER_ROW_REQUIRED_FIELD_REFS:
        raise ValueError("R49 R6 R48 execution blocker required fields changed")
    if tuple(data.get("readfeel_blocker_id_refs") or ()) != P7_R48_READFEEL_BLOCKER_ID_REFS:
        raise ValueError("R49 R6 readfeel blocker ids changed")
    if tuple(data.get("r49_execution_blocker_id_refs") or ()) != P7_R49_EXECUTION_BLOCKER_ID_REFS:
        raise ValueError("R49 R6 execution blocker ids changed")
    if set(P7_R48_EXECUTION_BLOCKER_ID_REFS) - set(data.get("r48_execution_blocker_id_refs") or ()):
        raise ValueError("R49 R6 lost R48 execution blocker coverage")
    if safe_mapping(data.get("r49_to_r48_execution_blocker_id_map")) != P7_R49_TO_R48_EXECUTION_BLOCKER_ID_MAP:
        raise ValueError("R49 R6 execution blocker map changed")
    _validate_r49_blocker_mapping()
    for true_key in (
        "blocker_execution_ingestion_ready",
        "blocker_rows_must_be_r48_bodyfree",
        "execution_blocker_rows_must_be_r48_bodyfree",
        "r48_builder_connection_fixed",
        "readfeel_and_execution_blockers_separated",
        "execution_blockers_do_not_assign_readfeel_verdict",
        "review_execution_blockers_do_not_create_p5_readfeel_red",
        "local_preflight_blockers_map_to_execution_blocker_rows",
        "rating_rows_missing_maps_to_execution_blocker_rows",
        "question_observation_rows_missing_maps_to_execution_blocker_rows",
        "disposal_missing_or_failed_maps_to_execution_blocker_rows",
        "body_free_leak_maps_to_execution_blocker_rows",
        "question_need_observation_required",
        "question_need_observation_rows_required_later",
        "r0_current_source_r48_handoff_bridge_refrozen",
        "r1_scope_schema_status_enum_fixed",
        "r2_r48_case_matrix_handoff_validated",
        "r3_local_only_actual_packet_generation_preflight_done",
        "r4_actual_review_session_protocol_built",
        "r5_rating_row_ingestion_r48_normalizer_connected",
        "r6_blocker_execution_blocker_ingestion_connected",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R49 R6 must keep {true_key}=True")
    for false_key in (
        "reviewer_free_text_included_allowed",
        "reviewer_free_text_bodyfree_allowed",
        "question_observation_ingestion_done_here",
        "body_full_packet_materialized_here",
        "local_reviewer_payload_materialized_here",
        "actual_body_full_packet_generated_here",
        "actual_human_review_run_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_reviewer_notes_materialized_here",
        "actual_disposal_run_here",
        "actual_disposal_receipt_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R49 R6 must keep {false_key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R49_R6_IMPLEMENTED_STEPS:
        raise ValueError("R49 R6 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R49_R6_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R49 R6 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R49_R6_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R49 R6 must point to R49-7 next")
    _assert_r49_body_free(data, source="p7_r49_r6_blocker_execution_blocker_ingestion")
    return True


def assert_p7_r49_question_need_observation_row_schema_enum_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_required_fields(
        data,
        required=P7_R49_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_ENUM_FREEZE_REQUIRED_FIELD_REFS,
        source="p7_r49_r7_question_need_observation_row_schema_enum_freeze",
    )
    _assert_common(
        data,
        schema_version=P7_R49_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_ENUM_FREEZE_SCHEMA_VERSION,
        source="p7_r49_r7_question_need_observation_row_schema_enum_freeze",
    )
    if data.get("policy_section") != "R49-7_question_need_observation_row_schema_enum_freeze":
        raise ValueError("R49 R7 policy section changed")
    assert_p7_r49_blocker_execution_blocker_ingestion_contract(safe_mapping(data.get("r49_blocker_execution_blocker_ingestion")))
    if data.get("question_need_observation_row_schema_version") != P7_R49_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R49 R7 question row schema changed")
    if data.get("question_need_observation_summary_schema_version") != P7_R49_QUESTION_NEED_OBSERVATION_SUMMARY_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R49 R7 question summary schema changed")
    if data.get("observation_stage_ref") != P7_R49_QUESTION_NEED_OBSERVATION_STAGE_REF:
        raise ValueError("R49 R7 observation stage changed")
    if tuple(data.get("question_need_observation_row_required_field_refs") or ()) != P7_R49_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS:
        raise ValueError("R49 R7 question row required fields changed")
    if tuple(data.get("question_need_observation_row_forbidden_field_refs") or ()) != P7_R49_QUESTION_NEED_OBSERVATION_ROW_FORBIDDEN_FIELD_REFS:
        raise ValueError("R49 R7 question row forbidden fields changed")
    for ref_name, expected in (
        ("question_need_primary_class_refs", P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS),
        ("ambiguity_kind_refs", P7_R49_AMBIGUITY_KIND_REFS),
        ("one_question_fit_refs", P7_R49_ONE_QUESTION_FIT_REFS),
        ("repair_required_ref_refs", P7_R49_REPAIR_REQUIRED_REF_REFS),
        ("plan_candidate_flag_refs", P7_R49_PLAN_CANDIDATE_FLAG_REFS),
    ):
        values = tuple(data.get(ref_name) or ())
        if values != expected:
            raise ValueError(f"R49 R7 {ref_name} changed")
        _enum_unique(values, source=f"p7_r49.r7.{ref_name}")
    for required_ref in (
        "not_question_emlis_readfeel_repair_required",
        "not_question_p5_surface_repair_required",
        "not_question_gate_boundary_required",
        "insufficient_material_execution_blocker",
    ):
        if required_ref not in data.get("question_need_primary_class_refs", ()): 
            raise ValueError("R49 R7 primary classes must cover repair and execution boundaries")
    for true_key in (
        "enum_refs_unique",
        "primary_class_refs_cover_repair_and_execution_boundaries",
        "plan_candidate_flags_are_overlay_not_primary_required",
        "question_need_observation_row_schema_enum_fixed",
        "question_need_observation_row_bodyfree_contract_ready",
        "r0_current_source_r48_handoff_bridge_refrozen",
        "r1_scope_schema_status_enum_fixed",
        "r2_r48_case_matrix_handoff_validated",
        "r3_local_only_actual_packet_generation_preflight_done",
        "r4_actual_review_session_protocol_built",
        "r5_rating_row_ingestion_r48_normalizer_connected",
        "r6_blocker_execution_blocker_ingestion_connected",
        "r7_question_need_observation_row_schema_enum_fixed",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R49 R7 must keep {true_key}=True")
    for false_key in (
        "question_text_allowed",
        "draft_question_text_allowed",
        "reviewer_free_text_allowed",
        "raw_input_allowed",
        "raw_answer_allowed",
        "comment_text_body_allowed",
        "returned_surface_allowed",
        "local_path_allowed",
        "body_hash_allowed",
        "question_need_observation_row_normalizer_implemented_here",
        "question_need_observation_row_instances_materialized_here",
        "p8_question_implementation_spec_finalized_here",
        "p8_start_allowed",
        "release_allowed",
        "body_full_packet_materialized_here",
        "actual_body_full_packet_generated_here",
        "actual_human_review_run_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_question_need_observation_summary_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R49 R7 must keep {false_key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R49_R7_IMPLEMENTED_STEPS:
        raise ValueError("R49 R7 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R49_R7_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R49 R7 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R49_R7_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R49 R7 must point to R49-8 next")
    _assert_r49_body_free(data, source="p7_r49_r7_question_need_observation_row_schema_enum_freeze")
    return True


def assert_p7_r49_r6_r7_blocker_question_schema_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_required_fields(
        data,
        required=P7_R49_R6_R7_BLOCKER_QUESTION_SCHEMA_FREEZE_REQUIRED_FIELD_REFS,
        source="p7_r49_r6_r7_blocker_question_schema_freeze",
    )
    _assert_common(
        data,
        schema_version=P7_R49_R6_R7_BLOCKER_QUESTION_SCHEMA_FREEZE_SCHEMA_VERSION,
        source="p7_r49_r6_r7_blocker_question_schema_freeze",
    )
    if data.get("policy_section") != "R49-6_R49-7_blocker_question_schema_freeze":
        raise ValueError("R49 R6/R7 policy section changed")
    ingestion = safe_mapping(data.get("r6_blocker_execution_blocker_ingestion"))
    question_freeze = safe_mapping(data.get("r7_question_need_observation_row_schema_enum_freeze"))
    assert_p7_r49_blocker_execution_blocker_ingestion_contract(ingestion)
    assert_p7_r49_question_need_observation_row_schema_enum_freeze_contract(question_freeze)
    for true_key in (
        "blocker_execution_ingestion_ready",
        "readfeel_and_execution_blockers_separated",
        "question_need_observation_row_schema_enum_fixed",
        "question_need_observation_required",
        "question_need_observation_rows_required_later",
        "r0_current_source_r48_handoff_bridge_refrozen",
        "r1_scope_schema_status_enum_fixed",
        "r2_r48_case_matrix_handoff_validated",
        "r3_local_only_actual_packet_generation_preflight_done",
        "r4_actual_review_session_protocol_built",
        "r5_rating_row_ingestion_r48_normalizer_connected",
        "r6_blocker_execution_blocker_ingestion_connected",
        "r7_question_need_observation_row_schema_enum_fixed",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R49 R6/R7 must keep {true_key}=True")
    for false_key in (
        "body_full_packet_materialized_here",
        "actual_body_full_packet_generated_here",
        "actual_human_review_run_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "question_need_observation_row_normalizer_implemented_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R49 R6/R7 must keep {false_key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R49_R7_IMPLEMENTED_STEPS:
        raise ValueError("R49 R6/R7 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R49_R7_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R49 R6/R7 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R49_R7_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R49 R6/R7 must point to R49-8 next")
    _assert_r49_body_free(data, source="p7_r49_r6_r7_blocker_question_schema_freeze")
    return True




def assert_p7_r49_question_need_observation_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(
        data,
        required=P7_R49_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS,
        source="p7_r49_question_need_observation_row_bodyfree",
    )
    if set(data) != set(P7_R49_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS):
        raise ValueError("R49 question observation row must contain only the frozen body-free fields")
    if data.get("schema_version") != P7_R49_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R49 question observation row schema version changed")
    if data.get("review_kind") != P7_R49_REVIEW_KIND:
        raise ValueError("R49 question observation row review kind changed")
    if data.get("observation_stage") != P7_R49_QUESTION_NEED_OBSERVATION_STAGE_REF:
        raise ValueError("R49 question observation stage changed")
    if data.get("question_need_primary_class") not in P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS:
        raise ValueError("R49 question observation primary class changed")
    if data.get("one_question_fit_ref") not in P7_R49_ONE_QUESTION_FIT_REFS:
        raise ValueError("R49 question observation one-question fit enum changed")
    for key, refs in (
        ("ambiguity_kind_refs", P7_R49_AMBIGUITY_KIND_REFS),
        ("repair_required_refs", P7_R49_REPAIR_REQUIRED_REF_REFS),
    ):
        values = tuple(data.get(key) or ())
        if len(values) != len(set(values)):
            raise ValueError(f"R49 question observation {key} must be unique")
        if any(value not in refs for value in values):
            raise ValueError(f"R49 question observation {key} contains a ref outside the frozen enum")
    if len(tuple(data.get("sanitized_reason_ids") or ())) != len(set(tuple(data.get("sanitized_reason_ids") or ()))):
        raise ValueError("R49 question observation sanitized reason ids must be unique")
    flags = safe_mapping(data.get("plan_candidate_flags"))
    if set(flags) != set(P7_R49_PLAN_CANDIDATE_FLAG_REFS):
        raise ValueError("R49 question observation plan candidate flags changed")
    if flags.get("p8_implementation_spec_finalized_here") is not False:
        raise ValueError("R49 question observation must not finalize P8 implementation spec")
    for false_key in ("question_text_included", "draft_question_text_included", "reviewer_free_text_included"):
        if data.get(false_key) is not False:
            raise ValueError(f"R49 question observation must keep {false_key}=False")
    if data.get("body_removed") is not True:
        raise ValueError("R49 question observation row requires body_removed=True")
    if data.get("body_free") is not True:
        raise ValueError("R49 question observation row must be body_free")
    for forbidden in P7_R49_QUESTION_NEED_OBSERVATION_ROW_FORBIDDEN_FIELD_REFS:
        if forbidden in data:
            raise ValueError("R49 question observation row contains a forbidden body/question field")
    _validate_question_observation_semantics(data)
    _assert_r49_body_free(data, source="p7_r49_question_need_observation_row_bodyfree")
    return True


def assert_p7_r49_question_need_observation_row_normalizer_contract(normalizer: Mapping[str, Any]) -> bool:
    data = safe_mapping(normalizer)
    _assert_required_fields(
        data,
        required=P7_R49_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_REQUIRED_FIELD_REFS,
        source="p7_r49_r8_question_need_observation_row_normalizer",
    )
    _assert_common(
        data,
        schema_version=P7_R49_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_SCHEMA_VERSION,
        source="p7_r49_r8_question_need_observation_row_normalizer",
    )
    if data.get("policy_section") != "R49-8_question_need_observation_row_normalizer":
        raise ValueError("R49 R8 policy section changed")
    assert_p7_r49_question_need_observation_row_schema_enum_freeze_contract(safe_mapping(data.get("r49_question_need_observation_row_schema_enum_freeze")))
    if data.get("question_need_observation_row_schema_version") != P7_R49_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R49 R8 question row schema changed")
    if data.get("question_need_observation_row_normalizer_function_ref") != "normalize_p7_r49_question_need_observation_row_bodyfree":
        raise ValueError("R49 R8 normalizer function ref changed")
    if tuple(data.get("question_need_observation_row_required_field_refs") or ()) != P7_R49_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS:
        raise ValueError("R49 R8 question row required fields changed")
    if tuple(data.get("question_need_observation_row_forbidden_field_refs") or ()) != P7_R49_QUESTION_NEED_OBSERVATION_ROW_FORBIDDEN_FIELD_REFS:
        raise ValueError("R49 R8 question row forbidden fields changed")
    for ref_name, expected in (
        ("question_need_primary_class_refs", P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS),
        ("ambiguity_kind_refs", P7_R49_AMBIGUITY_KIND_REFS),
        ("one_question_fit_refs", P7_R49_ONE_QUESTION_FIT_REFS),
        ("repair_required_ref_refs", P7_R49_REPAIR_REQUIRED_REF_REFS),
        ("plan_candidate_flag_refs", P7_R49_PLAN_CANDIDATE_FLAG_REFS),
    ):
        if tuple(data.get(ref_name) or ()) != expected:
            raise ValueError(f"R49 R8 {ref_name} changed")
    for true_key in (
        "normalizer_ready",
        "question_need_observation_rows_must_be_bodyfree",
        "body_removed_required_for_question_observation_row",
        "question_need_observation_row_normalizer_implemented_here",
        "r0_current_source_r48_handoff_bridge_refrozen",
        "r1_scope_schema_status_enum_fixed",
        "r2_r48_case_matrix_handoff_validated",
        "r3_local_only_actual_packet_generation_preflight_done",
        "r4_actual_review_session_protocol_built",
        "r5_rating_row_ingestion_r48_normalizer_connected",
        "r6_blocker_execution_blocker_ingestion_connected",
        "r7_question_need_observation_row_schema_enum_fixed",
        "r8_question_need_observation_row_normalizer_connected",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R49 R8 must keep {true_key}=True")
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
        "question_need_observation_row_instances_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "body_full_packet_materialized_here",
        "actual_body_full_packet_generated_here",
        "actual_human_review_run_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R49 R8 must keep {false_key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R49_R8_IMPLEMENTED_STEPS:
        raise ValueError("R49 R8 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R49_R8_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R49 R8 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R49_R8_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R49 R8 must point to R49-9 next")
    _assert_r49_body_free(data, source="p7_r49_r8_question_need_observation_row_normalizer")
    return True


def assert_p7_r49_rating_question_observation_consistency_guard_contract(guard: Mapping[str, Any]) -> bool:
    data = safe_mapping(guard)
    _assert_required_fields(
        data,
        required=P7_R49_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS,
        source="p7_r49_r9_rating_question_observation_consistency_guard",
    )
    _assert_common(
        data,
        schema_version=P7_R49_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        source="p7_r49_r9_rating_question_observation_consistency_guard",
    )
    if data.get("policy_section") != "R49-9_rating_vs_question_observation_consistency_guard":
        raise ValueError("R49 R9 policy section changed")
    assert_p7_r49_question_need_observation_row_normalizer_contract(safe_mapping(data.get("r49_question_need_observation_row_normalizer")))
    if data.get("r48_rating_row_bodyfree_schema_version") != P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R49 R9 R48 rating row schema changed")
    if data.get("r49_question_row_bodyfree_schema_version") != P7_R49_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R49 R9 question row schema changed")
    if data.get("r48_execution_blocker_row_bodyfree_schema_version") != P7_R48_P5_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R49 R9 execution blocker row schema changed")
    for true_key in (
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
        "r0_current_source_r48_handoff_bridge_refrozen",
        "r1_scope_schema_status_enum_fixed",
        "r2_r48_case_matrix_handoff_validated",
        "r3_local_only_actual_packet_generation_preflight_done",
        "r4_actual_review_session_protocol_built",
        "r5_rating_row_ingestion_r48_normalizer_connected",
        "r6_blocker_execution_blocker_ingestion_connected",
        "r7_question_need_observation_row_schema_enum_fixed",
        "r8_question_need_observation_row_normalizer_connected",
        "r9_rating_question_observation_consistency_guard_connected",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R49 R9 must keep {true_key}=True")
    for false_key in (
        "body_full_packet_materialized_here",
        "actual_body_full_packet_generated_here",
        "actual_human_review_run_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_question_need_observation_summary_materialized_here",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R49 R9 must keep {false_key}=False")
    if data.get("consistency_guard_function_ref") != "assert_p7_r49_rating_vs_question_observation_consistency":
        raise ValueError("R49 R9 consistency guard function ref changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R49_R9_IMPLEMENTED_STEPS:
        raise ValueError("R49 R9 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R49_R9_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R49 R9 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R49_R9_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R49 R9 must point to R49-10 next")
    _assert_r49_body_free(data, source="p7_r49_r9_rating_question_observation_consistency_guard")
    return True


def assert_p7_r49_r8_r9_question_normalizer_consistency_guard_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_required_fields(
        data,
        required=P7_R49_R8_R9_QUESTION_NORMALIZER_CONSISTENCY_GUARD_FREEZE_REQUIRED_FIELD_REFS,
        source="p7_r49_r8_r9_question_normalizer_consistency_guard_freeze",
    )
    _assert_common(
        data,
        schema_version=P7_R49_R8_R9_QUESTION_NORMALIZER_CONSISTENCY_GUARD_FREEZE_SCHEMA_VERSION,
        source="p7_r49_r8_r9_question_normalizer_consistency_guard_freeze",
    )
    if data.get("policy_section") != "R49-8_R49-9_question_normalizer_consistency_guard_freeze":
        raise ValueError("R49 R8/R9 policy section changed")
    assert_p7_r49_question_need_observation_row_normalizer_contract(safe_mapping(data.get("r8_question_need_observation_row_normalizer")))
    assert_p7_r49_rating_question_observation_consistency_guard_contract(safe_mapping(data.get("r9_rating_question_observation_consistency_guard")))
    for true_key in (
        "question_need_observation_row_normalizer_implemented_here",
        "rating_question_consistency_guard_ready",
        "p5_weakness_must_not_be_hidden_by_questions",
        "question_need_observation_required",
        "question_need_observation_rows_required_later",
        "r0_current_source_r48_handoff_bridge_refrozen",
        "r1_scope_schema_status_enum_fixed",
        "r2_r48_case_matrix_handoff_validated",
        "r3_local_only_actual_packet_generation_preflight_done",
        "r4_actual_review_session_protocol_built",
        "r5_rating_row_ingestion_r48_normalizer_connected",
        "r6_blocker_execution_blocker_ingestion_connected",
        "r7_question_need_observation_row_schema_enum_fixed",
        "r8_question_need_observation_row_normalizer_connected",
        "r9_rating_question_observation_consistency_guard_connected",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R49 R8/R9 must keep {true_key}=True")
    for false_key in (
        "body_full_packet_materialized_here",
        "actual_body_full_packet_generated_here",
        "actual_human_review_run_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_question_need_observation_summary_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R49 R8/R9 must keep {false_key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R49_R9_IMPLEMENTED_STEPS:
        raise ValueError("R49 R8/R9 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R49_R9_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R49 R8/R9 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R49_R9_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R49 R8/R9 must point to R49-10 next")
    _assert_r49_body_free(data, source="p7_r49_r8_r9_question_normalizer_consistency_guard_freeze")
    return True



def _zero_count_map(refs: Sequence[str]) -> dict[str, int]:
    return {clean_identifier(ref, default="unknown", max_length=180): 0 for ref in refs}


def _increment_count(counts: dict[str, int], ref: Any, *, source: str, allowed_refs: Sequence[str]) -> None:
    clean_ref = clean_identifier(ref, default="", max_length=180)
    if clean_ref not in allowed_refs:
        raise ValueError(f"{source} must use a frozen enum ref")
    counts[clean_ref] = counts.get(clean_ref, 0) + 1


def _non_negative_int_r49(value: Any, *, source: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{source} must be a non-negative integer") from exc
    if number < 0:
        raise ValueError(f"{source} must be a non-negative integer")
    return number


def _question_rows_bodyfree(question_need_observation_rows: Sequence[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in question_need_observation_rows or ():
        row = safe_mapping(raw)
        assert_p7_r49_question_need_observation_row_bodyfree_contract(row)
        _assert_r49_body_free(row, source="p7_r49.r10_question_observation_row")
        rows.append(row)
    return rows


def _ensure_unique_identifier_counts(rows: Sequence[Mapping[str, Any]]) -> tuple[int, int, int]:
    case_ids = [clean_identifier(row.get("case_ref_id"), default="case_ref", max_length=180) for row in rows]
    blind_ids = [clean_identifier(row.get("blind_case_id"), default="blind_case", max_length=180) for row in rows]
    packet_ids = [clean_identifier(row.get("packet_ref_id"), default="packet_ref", max_length=180) for row in rows]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("R49 R10 question summary cannot accept duplicate case_ref_id rows")
    if len(blind_ids) != len(set(blind_ids)):
        raise ValueError("R49 R10 question summary cannot accept duplicate blind_case_id rows")
    if len(packet_ids) != len(set(packet_ids)):
        raise ValueError("R49 R10 question summary cannot accept duplicate packet_ref_id rows")
    return len(set(case_ids)), len(set(blind_ids)), len(set(packet_ids))


def build_p7_r49_question_need_observation_summary_bodyfree(
    *,
    r49_rating_question_observation_consistency_guard: Mapping[str, Any] | None = None,
    rating_question_observation_consistency_guard: Mapping[str, Any] | None = None,
    question_need_observation_rows: Sequence[Mapping[str, Any]] | None = None,
    expected_total_cases: int = P7_R49_REQUIRED_TOTAL_CASES,
    review_session_id: Any = P7_R49_DEFAULT_REVIEW_SESSION_ID,
    material_id: Any = "p7_r49_question_need_observation_summary_bodyfree",
) -> dict[str, Any]:
    """Build the R49-10 body-free question-need observation summary.

    This aggregates sanitized question-observation rows only. It does not claim
    that the actual human review ran, that rows were materialized here, or that
    P8 question implementation can start.
    """

    if r49_rating_question_observation_consistency_guard is not None and rating_question_observation_consistency_guard is not None:
        raise ValueError("provide only one R49 R9 consistency guard value")
    guard = (
        safe_mapping(r49_rating_question_observation_consistency_guard)
        if r49_rating_question_observation_consistency_guard is not None
        else safe_mapping(rating_question_observation_consistency_guard)
        if rating_question_observation_consistency_guard is not None
        else build_p7_r49_rating_question_observation_consistency_guard()
    )
    assert_p7_r49_rating_question_observation_consistency_guard_contract(guard)
    _assert_r49_body_free(guard, source="p7_r49.r9_guard_for_question_summary")
    requested_session_id = _safe_review_session_id(review_session_id or guard.get("review_session_id"))
    total_cases = _non_negative_int_r49(expected_total_cases, source="R49 R10 expected_total_cases")
    rows = _question_rows_bodyfree(question_need_observation_rows)
    for row in rows:
        if row.get("review_session_id") != requested_session_id:
            raise ValueError("R49 R10 question summary requires rows from the same review_session_id")
    unique_case_count, unique_blind_count, unique_packet_count = _ensure_unique_identifier_counts(rows)

    primary_counts = _zero_count_map(P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS)
    ambiguity_counts = _zero_count_map(P7_R49_AMBIGUITY_KIND_REFS)
    one_question_counts = _zero_count_map(P7_R49_ONE_QUESTION_FIT_REFS)
    repair_counts = _zero_count_map(P7_R49_REPAIR_REQUIRED_REF_REFS)
    plan_flag_counts = _zero_count_map(P7_R49_PLAN_CANDIDATE_FLAG_REFS)

    for row in rows:
        _increment_count(
            primary_counts,
            row.get("question_need_primary_class"),
            source="R49 R10 primary_class_counts",
            allowed_refs=P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS,
        )
        for ambiguity_ref in row.get("ambiguity_kind_refs") or ():
            _increment_count(
                ambiguity_counts,
                ambiguity_ref,
                source="R49 R10 ambiguity_kind_counts",
                allowed_refs=P7_R49_AMBIGUITY_KIND_REFS,
            )
        _increment_count(
            one_question_counts,
            row.get("one_question_fit_ref"),
            source="R49 R10 one_question_fit_counts",
            allowed_refs=P7_R49_ONE_QUESTION_FIT_REFS,
        )
        for repair_ref in row.get("repair_required_refs") or ():
            _increment_count(
                repair_counts,
                repair_ref,
                source="R49 R10 repair_required_counts",
                allowed_refs=P7_R49_REPAIR_REQUIRED_REF_REFS,
            )
        flags = safe_mapping(row.get("plan_candidate_flags"))
        for flag_ref in P7_R49_PLAN_CANDIDATE_FLAG_REFS:
            if flags.get(flag_ref) is True:
                plan_flag_counts[flag_ref] = plan_flag_counts.get(flag_ref, 0) + 1

    row_count = len(rows)
    rows_complete = (
        total_cases == P7_R49_REQUIRED_TOTAL_CASES
        and row_count == total_cases
        and unique_case_count == total_cases
        and unique_blind_count == total_cases
        and unique_packet_count == total_cases
    )
    p8_candidate_row_count = plan_flag_counts.get("p8_design_material_candidate", 0)
    p8_question_design_material_candidate = bool(rows_complete and p8_candidate_row_count > 0)
    not_question_repair_required_count = (
        primary_counts.get("not_question_emlis_readfeel_repair_required", 0)
        + primary_counts.get("not_question_p5_surface_repair_required", 0)
        + primary_counts.get("not_question_gate_boundary_required", 0)
    )

    summary = {
        **_false_flags(),
        "schema_version": P7_R49_QUESTION_NEED_OBSERVATION_SUMMARY_BODYFREE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R49_STEP,
        "scope": P7_R49_SCOPE,
        "policy_kind": P7_R49_POLICY_KIND,
        "policy_section": "R49-10_question_need_observation_summary_builder",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r49_question_need_observation_summary_bodyfree", max_length=160),
        "review_session_id": requested_session_id,
        "review_kind": P7_R49_REVIEW_KIND,
        "packet_kind": P7_R49_PACKET_KIND,
        "r9_rating_question_observation_consistency_guard_schema_version": P7_R49_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        "r9_rating_question_observation_consistency_guard_ref": clean_identifier(guard.get("material_id"), default="p7_r49_rating_question_observation_consistency_guard", max_length=160),
        "r49_rating_question_observation_consistency_guard": guard,
        "question_need_observation_summary_schema_version": P7_R49_QUESTION_NEED_OBSERVATION_SUMMARY_BODYFREE_SCHEMA_VERSION,
        "question_observation_summary_builder_ready": True,
        "question_observation_rows_must_be_bodyfree": True,
        "question_observation_rows_required_total_cases": P7_R49_REQUIRED_TOTAL_CASES,
        "total_case_count": total_cases,
        "question_observation_row_count": row_count,
        "question_observation_rows_complete": rows_complete,
        "unique_case_ref_id_count": unique_case_count,
        "unique_blind_case_id_count": unique_blind_count,
        "unique_packet_ref_id_count": unique_packet_count,
        "primary_class_counts": primary_counts,
        "ambiguity_kind_counts": ambiguity_counts,
        "one_question_fit_counts": one_question_counts,
        "repair_required_counts": repair_counts,
        "plan_candidate_flag_counts": plan_flag_counts,
        "p8_design_material_candidate_row_count": p8_candidate_row_count,
        "plus_single_question_candidate_later_count": plan_flag_counts.get("plus_single_question_candidate_later", 0),
        "premium_deep_dive_candidate_later_count": plan_flag_counts.get("premium_deep_dive_candidate_later", 0),
        "not_question_repair_required_count": not_question_repair_required_count,
        "insufficient_material_execution_blocker_count": primary_counts.get("insufficient_material_execution_blocker", 0),
        "p8_question_design_material_candidate": p8_question_design_material_candidate,
        "p8_start_allowed": False,
        "p8_implementation_spec_finalized_here": False,
        "question_trigger_logic_implemented_here": False,
        "api_db_rn_response_key_changed_here": False,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_question_need_observation_summary_materialized_here": False,
        "implemented_steps": list(P7_R49_R10_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R49_R10_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R49_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R49_R10_NEXT_REQUIRED_STEP_REF,
        "r0_current_source_r48_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_r48_case_matrix_handoff_validated": True,
        "r3_local_only_actual_packet_generation_preflight_done": True,
        "r4_actual_review_session_protocol_built": True,
        "r5_rating_row_ingestion_r48_normalizer_connected": True,
        "r6_blocker_execution_blocker_ingestion_connected": True,
        "r7_question_need_observation_row_schema_enum_fixed": True,
        "r8_question_need_observation_row_normalizer_connected": True,
        "r9_rating_question_observation_consistency_guard_connected": True,
        "r10_question_need_observation_summary_built": True,
        "public_contract": public_contract_flags(),
        "r49_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r49_question_need_observation_summary_bodyfree_contract(summary)
    return summary


def _assert_count_keys(data: Mapping[str, Any], *, expected_refs: Sequence[str], source: str) -> None:
    if set(data) != set(expected_refs):
        raise ValueError(f"{source} count keys must exactly match the frozen refs")
    for key, value in data.items():
        _non_negative_int_r49(value, source=f"{source}.{key}")


def assert_p7_r49_question_need_observation_summary_bodyfree_contract(summary: Mapping[str, Any]) -> bool:
    data = safe_mapping(summary)
    _assert_required_fields(
        data,
        required=P7_R49_QUESTION_NEED_OBSERVATION_SUMMARY_BODYFREE_REQUIRED_FIELD_REFS,
        source="p7_r49_question_need_observation_summary_bodyfree",
    )
    _assert_common(
        data,
        schema_version=P7_R49_QUESTION_NEED_OBSERVATION_SUMMARY_BODYFREE_SCHEMA_VERSION,
        source="p7_r49_question_need_observation_summary_bodyfree",
        allowed_true_keys=("p8_question_design_material_candidate",),
    )
    if data.get("policy_section") != "R49-10_question_need_observation_summary_builder":
        raise ValueError("R49 R10 summary policy section changed")
    assert_p7_r49_rating_question_observation_consistency_guard_contract(
        safe_mapping(data.get("r49_rating_question_observation_consistency_guard"))
    )
    _assert_count_keys(safe_mapping(data.get("primary_class_counts")), expected_refs=P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS, source="R49 R10 primary_class_counts")
    _assert_count_keys(safe_mapping(data.get("ambiguity_kind_counts")), expected_refs=P7_R49_AMBIGUITY_KIND_REFS, source="R49 R10 ambiguity_kind_counts")
    _assert_count_keys(safe_mapping(data.get("one_question_fit_counts")), expected_refs=P7_R49_ONE_QUESTION_FIT_REFS, source="R49 R10 one_question_fit_counts")
    _assert_count_keys(safe_mapping(data.get("repair_required_counts")), expected_refs=P7_R49_REPAIR_REQUIRED_REF_REFS, source="R49 R10 repair_required_counts")
    _assert_count_keys(safe_mapping(data.get("plan_candidate_flag_counts")), expected_refs=P7_R49_PLAN_CANDIDATE_FLAG_REFS, source="R49 R10 plan_candidate_flag_counts")
    total_cases = _non_negative_int_r49(data.get("total_case_count"), source="R49 R10 total_case_count")
    row_count = _non_negative_int_r49(data.get("question_observation_row_count"), source="R49 R10 question row count")
    if row_count != sum(safe_mapping(data.get("primary_class_counts")).values()):
        raise ValueError("R49 R10 primary_class_counts must sum to the question row count")
    for count_key in ("unique_case_ref_id_count", "unique_blind_case_id_count", "unique_packet_ref_id_count"):
        count_value = _non_negative_int_r49(data.get(count_key), source=f"R49 R10 {count_key}")
        if count_value > row_count:
            raise ValueError("R49 R10 unique identifier counts must not exceed row count")
    if data.get("question_observation_rows_complete") is True:
        if total_cases != P7_R49_REQUIRED_TOTAL_CASES or row_count != total_cases:
            raise ValueError("R49 R10 complete summary requires all 24 question observation rows")
        if data.get("unique_case_ref_id_count") != total_cases or data.get("unique_blind_case_id_count") != total_cases or data.get("unique_packet_ref_id_count") != total_cases:
            raise ValueError("R49 R10 complete summary requires unique case/blind/packet refs for all cases")
    else:
        if data.get("p8_question_design_material_candidate") is not False:
            raise ValueError("R49 R10 incomplete question summary cannot become a P8 design material candidate")
    if data.get("p8_question_design_material_candidate") is True:
        if data.get("question_observation_rows_complete") is not True:
            raise ValueError("R49 R10 P8 material candidate requires complete question rows")
        if _non_negative_int_r49(data.get("p8_design_material_candidate_row_count"), source="R49 R10 p8 row count") <= 0:
            raise ValueError("R49 R10 P8 material candidate requires at least one candidate row")
    for false_key in (
        "p8_start_allowed",
        "p8_implementation_spec_finalized_here",
        "question_trigger_logic_implemented_here",
        "api_db_rn_response_key_changed_here",
        "actual_human_review_run_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_question_need_observation_summary_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R49 R10 must keep {false_key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R49_R10_IMPLEMENTED_STEPS:
        raise ValueError("R49 R10 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R49_R10_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R49 R10 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R49_R10_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R49 R10 must point to R49-11 next")
    _assert_r49_body_free(data, source="p7_r49_question_need_observation_summary_bodyfree")
    return True


def _default_disposal_status_for_summary(summary: Mapping[str, Any]) -> str:
    if safe_mapping(summary).get("question_observation_rows_complete") is True:
        return "PURGE_REQUIRED"
    return "GENERATION_BLOCKED"


def _receipt_status_allows_disposal_pending(status: str) -> bool:
    return status in {
        "PURGE_REQUIRED",
        "BODY_PURGED",
        "DISPOSAL_VERIFIED",
        "EXPIRED_PURGED",
        "DISPOSAL_FAILED",
    }


def build_p7_r49_disposal_receipt_connection(
    *,
    r49_question_need_observation_summary: Mapping[str, Any] | None = None,
    question_need_observation_summary: Mapping[str, Any] | None = None,
    disposal_result: Mapping[str, Any] | None = None,
    disposal_receipt: Mapping[str, Any] | None = None,
    disposal_status: Any | None = None,
    deleted_file_count: int = 0,
    body_removed: bool = False,
    reviewer_notes_removed: bool = False,
    purge_started_at: Any = "purge_started_at_unset",
    purge_completed_at: Any = "purge_completed_at_unset",
    material_id: Any = "p7_r49_disposal_receipt_connection",
) -> dict[str, Any]:
    """Connect R49-11 to the R48 disposal receipt schema without deleting files."""

    if r49_question_need_observation_summary is not None and question_need_observation_summary is not None:
        raise ValueError("provide only one R49 R10 question summary value")
    if disposal_result is not None and disposal_receipt is not None:
        raise ValueError("provide only one disposal_result/disposal_receipt value")
    summary = (
        safe_mapping(r49_question_need_observation_summary)
        if r49_question_need_observation_summary is not None
        else safe_mapping(question_need_observation_summary)
        if question_need_observation_summary is not None
        else build_p7_r49_question_need_observation_summary_bodyfree()
    )
    assert_p7_r49_question_need_observation_summary_bodyfree_contract(summary)
    _assert_r49_body_free(summary, source="p7_r49.r10_summary_for_disposal_connection")
    rows_complete = summary.get("question_observation_rows_complete") is True
    requested_status = clean_identifier(disposal_status, default="", max_length=80) if disposal_status is not None else ""
    if not requested_status:
        requested_status = _default_disposal_status_for_summary(summary)
    if requested_status not in P7_R47_DISPOSAL_STATUSES:
        raise ValueError("R49 R11 disposal status must reuse the frozen R47/R48 disposal enum")
    if not rows_complete and _receipt_status_allows_disposal_pending(requested_status):
        raise ValueError("R49 R11 cannot move disposal pending before question observation rows are complete")

    result_payload = safe_mapping(disposal_result) if disposal_result is not None else safe_mapping(disposal_receipt) if disposal_receipt is not None else None
    if result_payload is not None:
        result_status = clean_identifier(result_payload.get("disposal_status"), default=requested_status, max_length=80)
        if not rows_complete and _receipt_status_allows_disposal_pending(result_status):
            raise ValueError("R49 R11 cannot accept a purge/verified receipt before question rows are complete")
    receipt = build_p7_r48_p5_disposal_receipt_bodyfree(
        disposal_result=result_payload,
        review_session_id=summary.get("review_session_id"),
        case_count=_non_negative_int_r49(summary.get("total_case_count"), source="R49 R11 receipt case_count"),
        deleted_file_count=deleted_file_count,
        disposal_status=requested_status,
        body_removed=body_removed,
        reviewer_notes_removed=reviewer_notes_removed,
        purge_started_at=purge_started_at,
        purge_completed_at=purge_completed_at,
    )
    assert_p7_r48_p5_disposal_receipt_bodyfree_contract(receipt)
    _assert_r49_body_free(receipt, source="p7_r49.r11_r48_disposal_receipt")

    receipt_status = clean_identifier(receipt.get("disposal_status"), default="NOT_GENERATED", max_length=80)
    disposal_verified = (
        receipt_status in P7_R48_P5_CONFIRMED_ALLOWED_DISPOSAL_STATUS_REFS
        and receipt.get("body_removed") is True
        and receipt.get("reviewer_notes_removed") is True
        and receipt.get("local_packet_exported") is False
        and receipt.get("content_hash_of_body_stored") is False
    )
    execution_blockers: list[str] = []
    if not rows_complete:
        execution_blockers.append("r49_question_need_observation_rows_missing")
    if receipt_status == "DISPOSAL_FAILED":
        execution_blockers.append("r49_disposal_failed")
    if receipt_status in {"NOT_GENERATED", "GENERATION_BLOCKED"} and rows_complete:
        execution_blockers.append("r49_disposal_receipt_missing")
    execution_blockers = dedupe_identifiers(execution_blockers, limit=20, max_length=160)
    review_session_status = "DISPOSAL_VERIFIED" if disposal_verified else "DISPOSAL_PENDING" if rows_complete else "BLOCKED"

    connection = {
        **_false_flags(),
        "schema_version": P7_R49_DISPOSAL_RECEIPT_CONNECTION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R49_STEP,
        "scope": P7_R49_SCOPE,
        "policy_kind": P7_R49_POLICY_KIND,
        "policy_section": "R49-11_disposal_receipt_connection",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r49_disposal_receipt_connection", max_length=160),
        "review_session_id": clean_identifier(summary.get("review_session_id"), default=P7_R49_DEFAULT_REVIEW_SESSION_ID, max_length=160),
        "review_kind": P7_R49_REVIEW_KIND,
        "packet_kind": P7_R49_PACKET_KIND,
        "r10_question_need_observation_summary_schema_version": P7_R49_QUESTION_NEED_OBSERVATION_SUMMARY_BODYFREE_SCHEMA_VERSION,
        "r10_question_need_observation_summary_ref": clean_identifier(summary.get("material_id"), default="p7_r49_question_need_observation_summary_bodyfree", max_length=160),
        "r49_question_need_observation_summary": summary,
        "r48_disposal_receipt_builder_schema_version": P7_R48_DISPOSAL_RECEIPT_BUILDER_SCHEMA_VERSION,
        "r48_disposal_receipt_schema_version": P7_R48_P5_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION,
        "r48_disposal_receipt_required_field_refs": list(P7_R48_P5_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS),
        "r48_disposal_receipt_forbidden_field_refs": list(P7_R48_P5_DISPOSAL_RECEIPT_FORBIDDEN_FIELD_REFS),
        "r47_disposal_status_refs": list(P7_R47_DISPOSAL_STATUSES),
        "r48_disposal_receipt_builder_function_ref": "build_p7_r48_p5_disposal_receipt_bodyfree",
        "r48_disposal_receipt_contract_ref": "assert_p7_r48_p5_disposal_receipt_bodyfree_contract",
        "question_observation_rows_complete_required_before_disposal_pending": True,
        "question_observation_rows_complete": rows_complete,
        "question_observation_row_count": _non_negative_int_r49(summary.get("question_observation_row_count"), source="R49 R11 question row count"),
        "required_total_cases": P7_R49_REQUIRED_TOTAL_CASES,
        "disposal_receipt_connection_ready": True,
        "disposal_pending_allowed_by_question_observation_summary": rows_complete,
        "disposal_receipt_bodyfree": True,
        "disposal_receipt": receipt,
        "disposal_status": receipt_status,
        "disposal_verified_for_candidate": disposal_verified,
        "review_session_status": review_session_status,
        "body_removed": receipt.get("body_removed") is True,
        "reviewer_notes_removed": receipt.get("reviewer_notes_removed") is True,
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "execution_blocker_ids": execution_blockers,
        "execution_blocker_count": len(execution_blockers),
        "body_path_hash_forbidden": True,
        "receipt_does_not_delete_files_here": True,
        "actual_disposal_run_here": False,
        "actual_cleanup_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_question_need_observation_summary_materialized_here": False,
        "p8_question_design_material_candidate": summary.get("p8_question_design_material_candidate") is True,
        "p8_start_allowed": False,
        "release_allowed": False,
        "implemented_steps": list(P7_R49_R11_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R49_R11_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R49_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R49_R11_NEXT_REQUIRED_STEP_REF,
        "r0_current_source_r48_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_r48_case_matrix_handoff_validated": True,
        "r3_local_only_actual_packet_generation_preflight_done": True,
        "r4_actual_review_session_protocol_built": True,
        "r5_rating_row_ingestion_r48_normalizer_connected": True,
        "r6_blocker_execution_blocker_ingestion_connected": True,
        "r7_question_need_observation_row_schema_enum_fixed": True,
        "r8_question_need_observation_row_normalizer_connected": True,
        "r9_rating_question_observation_consistency_guard_connected": True,
        "r10_question_need_observation_summary_built": True,
        "r11_disposal_receipt_connection_fixed": True,
        "public_contract": public_contract_flags(),
        "r49_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r49_disposal_receipt_connection_contract(connection)
    return connection


def assert_p7_r49_disposal_receipt_connection_contract(connection: Mapping[str, Any]) -> bool:
    data = safe_mapping(connection)
    _assert_required_fields(
        data,
        required=P7_R49_DISPOSAL_RECEIPT_CONNECTION_REQUIRED_FIELD_REFS,
        source="p7_r49_disposal_receipt_connection",
    )
    _assert_common(
        data,
        schema_version=P7_R49_DISPOSAL_RECEIPT_CONNECTION_SCHEMA_VERSION,
        source="p7_r49_disposal_receipt_connection",
        allowed_true_keys=("p8_question_design_material_candidate",),
    )
    if data.get("policy_section") != "R49-11_disposal_receipt_connection":
        raise ValueError("R49 R11 disposal connection policy section changed")
    summary = safe_mapping(data.get("r49_question_need_observation_summary"))
    receipt = safe_mapping(data.get("disposal_receipt"))
    assert_p7_r49_question_need_observation_summary_bodyfree_contract(summary)
    assert_p7_r48_p5_disposal_receipt_bodyfree_contract(receipt)
    _assert_r49_body_free(receipt, source="p7_r49_disposal_receipt_connection.receipt")
    if data.get("r48_disposal_receipt_builder_schema_version") != P7_R48_DISPOSAL_RECEIPT_BUILDER_SCHEMA_VERSION:
        raise ValueError("R49 R11 R48 disposal builder schema changed")
    if data.get("r48_disposal_receipt_schema_version") != P7_R48_P5_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R49 R11 R48 disposal receipt schema changed")
    if tuple(data.get("r48_disposal_receipt_required_field_refs") or ()) != tuple(P7_R48_P5_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS):
        raise ValueError("R49 R11 R48 receipt required refs changed")
    if tuple(data.get("r48_disposal_receipt_forbidden_field_refs") or ()) != tuple(P7_R48_P5_DISPOSAL_RECEIPT_FORBIDDEN_FIELD_REFS):
        raise ValueError("R49 R11 R48 receipt forbidden refs changed")
    if set(data.get("r47_disposal_status_refs") or ()) != set(P7_R47_DISPOSAL_STATUSES):
        raise ValueError("R49 R11 disposal status refs changed")
    rows_complete = data.get("question_observation_rows_complete") is True
    if rows_complete != (summary.get("question_observation_rows_complete") is True):
        raise ValueError("R49 R11 question row completeness mismatch")
    if data.get("question_observation_row_count") != summary.get("question_observation_row_count"):
        raise ValueError("R49 R11 question row count mismatch")
    status = clean_identifier(data.get("disposal_status"), default="NOT_GENERATED", max_length=80)
    if status != receipt.get("disposal_status"):
        raise ValueError("R49 R11 disposal status must match nested R48 receipt")
    if not rows_complete:
        if data.get("disposal_pending_allowed_by_question_observation_summary") is not False:
            raise ValueError("R49 R11 incomplete question rows cannot allow disposal pending")
        if "r49_question_need_observation_rows_missing" not in set(data.get("execution_blocker_ids") or []):
            raise ValueError("R49 R11 incomplete question rows require the missing-question-row execution blocker")
        if data.get("review_session_status") != "BLOCKED":
            raise ValueError("R49 R11 incomplete question rows must keep session blocked")
    else:
        if data.get("disposal_pending_allowed_by_question_observation_summary") is not True:
            raise ValueError("R49 R11 complete question rows must allow disposal-pending status")
        if "r49_question_need_observation_rows_missing" in set(data.get("execution_blocker_ids") or []):
            raise ValueError("R49 R11 complete question rows must not carry missing-question-row blocker")
    if status in P7_R48_P5_CONFIRMED_ALLOWED_DISPOSAL_STATUS_REFS:
        if data.get("disposal_verified_for_candidate") is not True or data.get("review_session_status") != "DISPOSAL_VERIFIED":
            raise ValueError("R49 R11 verified R48 receipt must produce verified disposal connection status")
        if data.get("body_removed") is not True or data.get("reviewer_notes_removed") is not True:
            raise ValueError("R49 R11 verified disposal requires body and reviewer notes removed")
    else:
        if data.get("disposal_verified_for_candidate") is not False:
            raise ValueError("R49 R11 non-verified receipt cannot be a verified disposal candidate")
    if status == "DISPOSAL_FAILED" and "r49_disposal_failed" not in set(data.get("execution_blocker_ids") or []):
        raise ValueError("R49 R11 disposal failure requires the disposal-failed execution blocker")
    if data.get("execution_blocker_count") != len(data.get("execution_blocker_ids") or []):
        raise ValueError("R49 R11 execution blocker count mismatch")
    for false_key in (
        "local_packet_exported",
        "content_hash_of_body_stored",
        "actual_disposal_run_here",
        "actual_cleanup_run_here",
        "actual_disposal_receipt_materialized_here",
        "actual_body_full_packet_generated_here",
        "actual_human_review_run_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_question_need_observation_summary_materialized_here",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R49 R11 must keep {false_key}=False")
    if data.get("body_path_hash_forbidden") is not True or data.get("receipt_does_not_delete_files_here") is not True:
        raise ValueError("R49 R11 must keep body/path/hash forbidden and must not delete files itself")
    if tuple(data.get("implemented_steps") or ()) != P7_R49_R11_IMPLEMENTED_STEPS:
        raise ValueError("R49 R11 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R49_R11_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R49 R11 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R49_R11_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R49 R11 must point to R49-12 next")
    _assert_r49_body_free(data, source="p7_r49_disposal_receipt_connection")
    return True


def build_p7_r49_r10_r11_question_summary_disposal_connection_freeze(
    *,
    r49_question_need_observation_summary: Mapping[str, Any] | None = None,
    r49_disposal_receipt_connection: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r49_r10_r11_question_summary_disposal_connection_freeze",
) -> dict[str, Any]:
    """Combine R49-10 and R49-11 without claiming review/disposal completion."""

    summary = (
        safe_mapping(r49_question_need_observation_summary)
        if r49_question_need_observation_summary is not None
        else build_p7_r49_question_need_observation_summary_bodyfree()
    )
    assert_p7_r49_question_need_observation_summary_bodyfree_contract(summary)
    connection = (
        safe_mapping(r49_disposal_receipt_connection)
        if r49_disposal_receipt_connection is not None
        else build_p7_r49_disposal_receipt_connection(r49_question_need_observation_summary=summary)
    )
    assert_p7_r49_disposal_receipt_connection_contract(connection)
    if connection.get("review_session_id") != summary.get("review_session_id"):
        raise ValueError("R49 R10/R11 freeze requires matching review_session_id")
    freeze = {
        **_false_flags(),
        "schema_version": P7_R49_R10_R11_QUESTION_SUMMARY_DISPOSAL_CONNECTION_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R49_STEP,
        "scope": P7_R49_SCOPE,
        "policy_kind": P7_R49_POLICY_KIND,
        "policy_section": "R49-10_R49-11_question_summary_disposal_connection_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r49_r10_r11_question_summary_disposal_connection_freeze", max_length=160),
        "review_session_id": clean_identifier(summary.get("review_session_id"), default=P7_R49_DEFAULT_REVIEW_SESSION_ID, max_length=160),
        "review_kind": P7_R49_REVIEW_KIND,
        "packet_kind": P7_R49_PACKET_KIND,
        "r10_question_need_observation_summary": summary,
        "r11_disposal_receipt_connection": connection,
        "implemented_steps": list(P7_R49_R11_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R49_R11_NOT_YET_IMPLEMENTED_STEPS),
        "question_observation_summary_builder_ready": True,
        "question_observation_rows_complete": summary.get("question_observation_rows_complete") is True,
        "disposal_receipt_connection_ready": True,
        "disposal_receipt_bodyfree": True,
        "disposal_pending_allowed_by_question_observation_summary": connection.get("disposal_pending_allowed_by_question_observation_summary") is True,
        "actual_disposal_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "actual_human_review_run_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_question_need_observation_summary_materialized_here": False,
        "p8_question_design_material_candidate": summary.get("p8_question_design_material_candidate") is True,
        "p8_start_allowed": False,
        "release_allowed": False,
        "first_next_work_ref": P7_R49_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R49_R11_NEXT_REQUIRED_STEP_REF,
        "r0_current_source_r48_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_r48_case_matrix_handoff_validated": True,
        "r3_local_only_actual_packet_generation_preflight_done": True,
        "r4_actual_review_session_protocol_built": True,
        "r5_rating_row_ingestion_r48_normalizer_connected": True,
        "r6_blocker_execution_blocker_ingestion_connected": True,
        "r7_question_need_observation_row_schema_enum_fixed": True,
        "r8_question_need_observation_row_normalizer_connected": True,
        "r9_rating_question_observation_consistency_guard_connected": True,
        "r10_question_need_observation_summary_built": True,
        "r11_disposal_receipt_connection_fixed": True,
        "public_contract": public_contract_flags(),
        "r49_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r49_r10_r11_question_summary_disposal_connection_freeze_contract(freeze)
    return freeze


def assert_p7_r49_r10_r11_question_summary_disposal_connection_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_required_fields(
        data,
        required=P7_R49_R10_R11_QUESTION_SUMMARY_DISPOSAL_CONNECTION_FREEZE_REQUIRED_FIELD_REFS,
        source="p7_r49_r10_r11_question_summary_disposal_connection_freeze",
    )
    _assert_common(
        data,
        schema_version=P7_R49_R10_R11_QUESTION_SUMMARY_DISPOSAL_CONNECTION_FREEZE_SCHEMA_VERSION,
        source="p7_r49_r10_r11_question_summary_disposal_connection_freeze",
        allowed_true_keys=("p8_question_design_material_candidate",),
    )
    if data.get("policy_section") != "R49-10_R49-11_question_summary_disposal_connection_freeze":
        raise ValueError("R49 R10/R11 freeze policy section changed")
    summary = safe_mapping(data.get("r10_question_need_observation_summary"))
    connection = safe_mapping(data.get("r11_disposal_receipt_connection"))
    assert_p7_r49_question_need_observation_summary_bodyfree_contract(summary)
    assert_p7_r49_disposal_receipt_connection_contract(connection)
    if data.get("question_observation_rows_complete") is not (summary.get("question_observation_rows_complete") is True):
        raise ValueError("R49 R10/R11 freeze question completeness mismatch")
    if data.get("disposal_pending_allowed_by_question_observation_summary") is not (connection.get("disposal_pending_allowed_by_question_observation_summary") is True):
        raise ValueError("R49 R10/R11 freeze disposal-pending flag mismatch")
    if data.get("p8_question_design_material_candidate") is not (summary.get("p8_question_design_material_candidate") is True):
        raise ValueError("R49 R10/R11 freeze P8 material candidate flag mismatch")
    for false_key in (
        "actual_disposal_run_here",
        "actual_disposal_receipt_materialized_here",
        "actual_human_review_run_here",
        "actual_body_full_packet_generated_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_question_need_observation_summary_materialized_here",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R49 R10/R11 freeze must keep {false_key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R49_R11_IMPLEMENTED_STEPS:
        raise ValueError("R49 R10/R11 freeze implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R49_R11_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R49 R10/R11 freeze not-yet steps changed")
    if data.get("next_required_step") != P7_R49_R11_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R49 R10/R11 freeze must point to R49-12 next")

    _assert_r49_body_free(data, source="p7_r49_r10_r11_question_summary_disposal_connection_freeze")
    return True


def _r48_rating_rows_bodyfree(rating_rows: Sequence[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in rating_rows or ():
        row = safe_mapping(raw)
        assert_p7_r48_p5_rating_row_bodyfree_contract(row)
        _assert_r49_body_free(row, source="p7_r49.r12_rating_row")
        rows.append(row)
    return rows


def _r48_blocker_rows_bodyfree(blocker_rows: Sequence[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in blocker_rows or ():
        row = safe_mapping(raw)
        assert_p7_r48_p5_blocker_row_bodyfree_contract(row)
        _assert_r49_body_free(row, source="p7_r49.r12_blocker_row")
        rows.append(row)
    return rows


def _r48_execution_blocker_rows_bodyfree(execution_blocker_rows: Sequence[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in execution_blocker_rows or ():
        row = safe_mapping(raw)
        assert_p7_r48_p5_execution_blocker_row_bodyfree_contract(row)
        _assert_r49_body_free(row, source="p7_r49.r12_execution_blocker_row")
        rows.append(row)
    return rows


def _r49_r48_status_for_handoff(*, rating_rows_complete: bool, question_rows_complete: bool, disposal_verified: bool) -> str:
    if rating_rows_complete and question_rows_complete and disposal_verified:
        return "FINALIZED"
    if rating_rows_complete or question_rows_complete:
        return "IN_PROGRESS"
    return "NOT_STARTED"


def _r49_status_for_handoff(*, rating_rows_complete: bool, question_rows_complete: bool, disposal_verified: bool) -> str:
    if rating_rows_complete and question_rows_complete and disposal_verified:
        return "SUMMARY_FINALIZED"
    if rating_rows_complete and question_rows_complete:
        return "DISPOSAL_PENDING"
    return "BLOCKED"


def build_p7_r49_review_handoff_summary_bodyfree(
    *,
    r10_r11_question_summary_disposal_connection_freeze: Mapping[str, Any] | None = None,
    r49_r10_r11_question_summary_disposal_connection_freeze: Mapping[str, Any] | None = None,
    rating_rows: Sequence[Mapping[str, Any]] | None = None,
    blocker_rows: Sequence[Mapping[str, Any]] | None = None,
    execution_blocker_rows: Sequence[Mapping[str, Any]] | None = None,
    material_id: Any = "p7_r49_review_handoff_summary_bodyfree",
) -> dict[str, Any]:
    """Build the R49-12 body-free review handoff summary.

    R49 does not define a new P5 scoring system here. It reuses the R48
    body-free P5 review handoff summary and adds question-observation
    completeness/repair counts before the R49 P5 confirmed-candidate gate.
    """

    if r10_r11_question_summary_disposal_connection_freeze is not None and r49_r10_r11_question_summary_disposal_connection_freeze is not None:
        raise ValueError("provide only one R49 R10/R11 freeze value")
    freeze = (
        safe_mapping(r10_r11_question_summary_disposal_connection_freeze)
        if r10_r11_question_summary_disposal_connection_freeze is not None
        else safe_mapping(r49_r10_r11_question_summary_disposal_connection_freeze)
        if r49_r10_r11_question_summary_disposal_connection_freeze is not None
        else build_p7_r49_r10_r11_question_summary_disposal_connection_freeze()
    )
    assert_p7_r49_r10_r11_question_summary_disposal_connection_freeze_contract(freeze)
    _assert_r49_body_free(freeze, source="p7_r49.r10_r11_freeze_for_review_handoff")
    question_summary = safe_mapping(freeze.get("r10_question_need_observation_summary"))
    disposal_connection = safe_mapping(freeze.get("r11_disposal_receipt_connection"))
    assert_p7_r49_question_need_observation_summary_bodyfree_contract(question_summary)
    assert_p7_r49_disposal_receipt_connection_contract(disposal_connection)

    ratings = _r48_rating_rows_bodyfree(rating_rows)
    blockers = _r48_blocker_rows_bodyfree(blocker_rows)
    execution_blockers = _r48_execution_blocker_rows_bodyfree(execution_blocker_rows)
    requested_session_id = clean_identifier(freeze.get("review_session_id"), default=P7_R49_DEFAULT_REVIEW_SESSION_ID, max_length=160)
    for row in [*ratings, *blockers, *execution_blockers]:
        if clean_identifier(row.get("review_session_id"), default=requested_session_id, max_length=160) != requested_session_id:
            raise ValueError("R49 R12 handoff summary requires all review rows to share review_session_id")

    rating_rows_complete = len(ratings) >= P7_R49_REQUIRED_TOTAL_CASES
    question_rows_complete = question_summary.get("question_observation_rows_complete") is True
    disposal_verified = disposal_connection.get("disposal_verified_for_candidate") is True
    r49_status = _r49_status_for_handoff(
        rating_rows_complete=rating_rows_complete,
        question_rows_complete=question_rows_complete,
        disposal_verified=disposal_verified,
    )
    r48_status = _r49_r48_status_for_handoff(
        rating_rows_complete=rating_rows_complete,
        question_rows_complete=question_rows_complete,
        disposal_verified=disposal_verified,
    )
    r48_summary = build_p7_r48_p5_review_handoff_summary_bodyfree(
        rating_rows=ratings,
        blocker_rows=blockers,
        execution_blocker_rows=execution_blockers,
        disposal_receipt=safe_mapping(disposal_connection.get("disposal_receipt")),
        review_session_id=requested_session_id,
        review_session_status=r48_status,
        case_count=P7_R49_REQUIRED_TOTAL_CASES,
    )
    assert_p7_r48_p5_review_handoff_summary_bodyfree_contract(r48_summary)
    _assert_r49_body_free(r48_summary, source="p7_r49.r12_r48_review_handoff_summary")

    question_repair_count = _non_negative_int_r49(
        question_summary.get("not_question_repair_required_count"),
        source="R49 R12 question repair-required count",
    )
    question_execution_count = _non_negative_int_r49(
        question_summary.get("insufficient_material_execution_blocker_count"),
        source="R49 R12 question execution-blocker count",
    )
    summary = {
        **_false_flags(),
        "schema_version": P7_R49_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R49_STEP,
        "scope": P7_R49_SCOPE,
        "policy_kind": P7_R49_POLICY_KIND,
        "policy_section": "R49-12_review_handoff_summary_builder",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r49_review_handoff_summary_bodyfree", max_length=160),
        "review_session_id": requested_session_id,
        "review_kind": P7_R49_REVIEW_KIND,
        "packet_kind": P7_R49_PACKET_KIND,
        "r10_r11_freeze_schema_version": P7_R49_R10_R11_QUESTION_SUMMARY_DISPOSAL_CONNECTION_FREEZE_SCHEMA_VERSION,
        "r10_r11_freeze_ref": clean_identifier(freeze.get("material_id"), default="p7_r49_r10_r11_question_summary_disposal_connection_freeze", max_length=160),
        "r10_r11_question_summary_disposal_connection_freeze": freeze,
        "r48_review_handoff_summary_schema_version": P7_R48_P5_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION,
        "r48_review_handoff_summary_required_field_refs": list(P7_R48_P5_REVIEW_HANDOFF_SUMMARY_REQUIRED_FIELD_REFS),
        "r48_review_handoff_summary_function_ref": "build_p7_r48_p5_review_handoff_summary_bodyfree",
        "r48_review_handoff_summary_contract_ref": "assert_p7_r48_p5_review_handoff_summary_bodyfree_contract",
        "r48_review_handoff_summary": r48_summary,
        "r49_question_need_observation_summary": question_summary,
        "r49_disposal_receipt_connection": disposal_connection,
        "required_total_cases": P7_R49_REQUIRED_TOTAL_CASES,
        "case_count": _non_negative_int_r49(r48_summary.get("case_count"), source="R49 R12 case_count"),
        "reviewed_case_count": _non_negative_int_r49(r48_summary.get("reviewed_case_count"), source="R49 R12 reviewed_case_count"),
        "rating_row_count": _non_negative_int_r49(r48_summary.get("rating_row_count"), source="R49 R12 rating_row_count"),
        "blocker_row_count": _non_negative_int_r49(r48_summary.get("blocker_row_count"), source="R49 R12 blocker_row_count"),
        "execution_blocker_row_count": _non_negative_int_r49(r48_summary.get("execution_blocker_row_count"), source="R49 R12 execution_blocker_row_count"),
        "question_observation_row_count": _non_negative_int_r49(question_summary.get("question_observation_row_count"), source="R49 R12 question_observation_row_count"),
        "question_observation_rows_complete": question_rows_complete,
        "rating_rows_complete": rating_rows_complete,
        "family_coverage_satisfied": r48_summary.get("family_coverage_satisfied") is True,
        "axis_averages": safe_mapping(r48_summary.get("axis_averages")),
        "axis_targets_satisfied": r48_summary.get("axis_targets_satisfied") is True,
        "red_case_count": _non_negative_int_r49(r48_summary.get("red_case_count"), source="R49 R12 red_case_count"),
        "repair_required_case_count": _non_negative_int_r49(r48_summary.get("repair_required_case_count"), source="R49 R12 repair_required_case_count"),
        "open_blocker_ids": list(r48_summary.get("open_blocker_ids") or []),
        "open_execution_blocker_ids": list(r48_summary.get("open_execution_blocker_ids") or []),
        "boundary_violation_blocker_ids": list(r48_summary.get("boundary_violation_blocker_ids") or []),
        "question_observation_repair_required_count": question_repair_count,
        "question_observation_execution_blocker_count": question_execution_count,
        "question_observation_blocks_p5_candidate": bool(question_repair_count or question_execution_count or not question_rows_complete),
        "disposal_status": clean_identifier(disposal_connection.get("disposal_status"), default="NOT_GENERATED", max_length=80),
        "disposal_verified_for_candidate": disposal_verified,
        "body_removed": disposal_connection.get("body_removed") is True,
        "reviewer_notes_removed": disposal_connection.get("reviewer_notes_removed") is True,
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "review_session_status": r49_status,
        "r48_review_session_status": r48_status,
        "r48_handoff_summary_candidate_claim": r48_summary.get("p5_human_blind_qa_confirmed_candidate") is True,
        "r48_p6_candidate_claim": r48_summary.get("p6_limited_human_readfeel_start_allowed_candidate") is True,
        "p5_human_blind_qa_confirmed_candidate": False,
        "p6_limited_human_readfeel_start_allowed_candidate": False,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "real_device_modal_review_start_allowed": False,
        "real_device_modal_review_confirmed": False,
        "actual_review_handoff_summary_materialized_here": False,
        "actual_human_review_run_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_question_need_observation_summary_materialized_here": False,
        "actual_disposal_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "p8_question_design_material_candidate": question_summary.get("p8_question_design_material_candidate") is True,
        "p8_start_allowed": False,
        "release_allowed": False,
        "implemented_steps": list(P7_R49_R12_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R49_R12_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R49_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R49_R12_NEXT_REQUIRED_STEP_REF,
        "r0_current_source_r48_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_r48_case_matrix_handoff_validated": True,
        "r3_local_only_actual_packet_generation_preflight_done": True,
        "r4_actual_review_session_protocol_built": True,
        "r5_rating_row_ingestion_r48_normalizer_connected": True,
        "r6_blocker_execution_blocker_ingestion_connected": True,
        "r7_question_need_observation_row_schema_enum_fixed": True,
        "r8_question_need_observation_row_normalizer_connected": True,
        "r9_rating_question_observation_consistency_guard_connected": True,
        "r10_question_need_observation_summary_built": True,
        "r11_disposal_receipt_connection_fixed": True,
        "r12_review_handoff_summary_built": True,
        "public_contract": public_contract_flags(),
        "r49_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r49_review_handoff_summary_bodyfree_contract(summary)
    return summary


def assert_p7_r49_review_handoff_summary_bodyfree_contract(summary: Mapping[str, Any]) -> bool:
    data = safe_mapping(summary)
    _assert_required_fields(
        data,
        required=P7_R49_REVIEW_HANDOFF_SUMMARY_BODYFREE_REQUIRED_FIELD_REFS,
        source="p7_r49_review_handoff_summary_bodyfree",
    )
    _assert_common(
        data,
        schema_version=P7_R49_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION,
        source="p7_r49_review_handoff_summary_bodyfree",
        allowed_true_keys=("p8_question_design_material_candidate",),
    )
    if data.get("policy_section") != "R49-12_review_handoff_summary_builder":
        raise ValueError("R49 R12 handoff summary policy section changed")
    assert_p7_r49_r10_r11_question_summary_disposal_connection_freeze_contract(
        safe_mapping(data.get("r10_r11_question_summary_disposal_connection_freeze"))
    )
    r48_summary = safe_mapping(data.get("r48_review_handoff_summary"))
    question_summary = safe_mapping(data.get("r49_question_need_observation_summary"))
    disposal_connection = safe_mapping(data.get("r49_disposal_receipt_connection"))
    assert_p7_r48_p5_review_handoff_summary_bodyfree_contract(r48_summary)
    assert_p7_r49_question_need_observation_summary_bodyfree_contract(question_summary)
    assert_p7_r49_disposal_receipt_connection_contract(disposal_connection)
    if data.get("review_session_status") not in {"SUMMARY_FINALIZED", "DISPOSAL_PENDING", "BLOCKED"}:
        raise ValueError("R49 R12 handoff status must stay within finalized/pending/blocked summary states")
    if data.get("rating_rows_complete") is not (data.get("rating_row_count") >= P7_R49_REQUIRED_TOTAL_CASES):
        raise ValueError("R49 R12 rating completeness mismatch")
    if data.get("question_observation_rows_complete") is not (question_summary.get("question_observation_rows_complete") is True):
        raise ValueError("R49 R12 question observation completeness mismatch")
    if data.get("disposal_verified_for_candidate") is not (disposal_connection.get("disposal_verified_for_candidate") is True):
        raise ValueError("R49 R12 disposal verified flag mismatch")
    expected_status = _r49_status_for_handoff(
        rating_rows_complete=data.get("rating_rows_complete") is True,
        question_rows_complete=data.get("question_observation_rows_complete") is True,
        disposal_verified=data.get("disposal_verified_for_candidate") is True,
    )
    if data.get("review_session_status") != expected_status:
        raise ValueError("R49 R12 review_session_status does not match review/question/disposal state")
    expected_r48_status = _r49_r48_status_for_handoff(
        rating_rows_complete=data.get("rating_rows_complete") is True,
        question_rows_complete=data.get("question_observation_rows_complete") is True,
        disposal_verified=data.get("disposal_verified_for_candidate") is True,
    )
    if data.get("r48_review_session_status") != expected_r48_status or r48_summary.get("review_session_status") != expected_r48_status:
        raise ValueError("R49 R12 R48 summary status mismatch")
    if data.get("question_observation_repair_required_count") != question_summary.get("not_question_repair_required_count"):
        raise ValueError("R49 R12 question repair count mismatch")
    if data.get("question_observation_execution_blocker_count") != question_summary.get("insufficient_material_execution_blocker_count"):
        raise ValueError("R49 R12 question execution blocker count mismatch")
    if data.get("question_observation_blocks_p5_candidate") is not bool(
        data.get("question_observation_repair_required_count")
        or data.get("question_observation_execution_blocker_count")
        or data.get("question_observation_rows_complete") is not True
    ):
        raise ValueError("R49 R12 question-observation blocker flag mismatch")
    if data.get("r48_handoff_summary_candidate_claim") is not (r48_summary.get("p5_human_blind_qa_confirmed_candidate") is True):
        raise ValueError("R49 R12 R48 P5 candidate claim mismatch")
    if data.get("r48_p6_candidate_claim") is not (r48_summary.get("p6_limited_human_readfeel_start_allowed_candidate") is True):
        raise ValueError("R49 R12 R48 P6 candidate claim mismatch")
    for false_key in (
        "p5_human_blind_qa_confirmed_candidate",
        "p6_limited_human_readfeel_start_allowed_candidate",
        "p5_human_blind_qa_confirmed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_limited_human_readfeel_confirmed",
        "real_device_modal_review_start_allowed",
        "real_device_modal_review_confirmed",
        "actual_review_handoff_summary_materialized_here",
        "actual_human_review_run_here",
        "actual_body_full_packet_generated_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_question_need_observation_summary_materialized_here",
        "actual_disposal_run_here",
        "actual_disposal_receipt_materialized_here",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R49 R12 handoff summary must keep {false_key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R49_R12_IMPLEMENTED_STEPS:
        raise ValueError("R49 R12 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R49_R12_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R49 R12 not-yet steps changed")
    if data.get("next_required_step") != P7_R49_R12_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R49 R12 must point to R49-13 next")
    _assert_r49_body_free(data, source="p7_r49_review_handoff_summary_bodyfree")
    return True


def _r49_p5_candidate_gate_missing_requirement_refs(summary: Mapping[str, Any], r48_gate: Mapping[str, Any]) -> list[str]:
    missing: list[str] = []
    missing.extend(clean_identifier(ref, default="missing_requirement", max_length=160) for ref in r48_gate.get("missing_requirement_refs") or [])
    if r48_gate.get("p5_confirmed_candidate_gate_passed") is not True:
        missing.append("r48_p5_confirmed_candidate_gate_passed")
    if summary.get("review_session_status") != "SUMMARY_FINALIZED":
        missing.append("r49_review_handoff_summary_finalized")
    if summary.get("question_observation_rows_complete") is not True:
        missing.append("question_observation_rows_complete")
    if _non_negative_int_r49(summary.get("question_observation_repair_required_count"), source="R49 R13 question repair count") != 0:
        missing.append("question_observation_repair_required_zero")
    if _non_negative_int_r49(summary.get("question_observation_execution_blocker_count"), source="R49 R13 question execution blocker count") != 0:
        missing.append("question_observation_execution_blocker_zero")
    return [ref for ref in P7_R49_P5_CONFIRMED_CANDIDATE_REQUIRED_CONDITION_REFS if ref in set(missing)]


def build_p7_r49_p5_confirmed_candidate_gate_connection(
    *,
    r49_review_handoff_summary: Mapping[str, Any] | None = None,
    review_handoff_summary: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r49_p5_confirmed_candidate_gate_connection",
) -> dict[str, Any]:
    """Connect R49-13 to the R48 P5 confirmed-candidate gate.

    The R48 gate must pass, and the R49 question-observation layer must be
    complete with no repair-required or execution-blocker question observations.
    P6 start candidate handoff remains deferred to R49-14.
    """

    if r49_review_handoff_summary is not None and review_handoff_summary is not None:
        raise ValueError("provide only one R49 R12 review handoff summary")
    summary = (
        safe_mapping(r49_review_handoff_summary)
        if r49_review_handoff_summary is not None
        else safe_mapping(review_handoff_summary)
        if review_handoff_summary is not None
        else build_p7_r49_review_handoff_summary_bodyfree()
    )
    assert_p7_r49_review_handoff_summary_bodyfree_contract(summary)
    _assert_r49_body_free(summary, source="p7_r49.r12_handoff_for_p5_gate")
    r48_gate = build_p7_r48_p5_confirmed_candidate_gate_bodyfree(
        handoff_summary=safe_mapping(summary.get("r48_review_handoff_summary"))
    )
    assert_p7_r48_p5_confirmed_candidate_gate_bodyfree_contract(r48_gate)
    _assert_r49_body_free(r48_gate, source="p7_r49.r13_r48_p5_gate")
    missing = _r49_p5_candidate_gate_missing_requirement_refs(summary, r48_gate)
    gate_passed = not missing
    connection = {
        **_false_flags(),
        "schema_version": P7_R49_P5_CONFIRMED_CANDIDATE_GATE_CONNECTION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R49_STEP,
        "scope": P7_R49_SCOPE,
        "policy_kind": P7_R49_POLICY_KIND,
        "policy_section": "R49-13_p5_confirmed_candidate_gate_connection",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r49_p5_confirmed_candidate_gate_connection", max_length=160),
        "review_session_id": clean_identifier(summary.get("review_session_id"), default=P7_R49_DEFAULT_REVIEW_SESSION_ID, max_length=160),
        "review_kind": P7_R49_REVIEW_KIND,
        "packet_kind": P7_R49_PACKET_KIND,
        "r12_review_handoff_summary_schema_version": P7_R49_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION,
        "r12_review_handoff_summary_ref": clean_identifier(summary.get("material_id"), default="p7_r49_review_handoff_summary_bodyfree", max_length=160),
        "r49_review_handoff_summary": summary,
        "r48_p5_confirmed_candidate_gate_schema_version": P7_R48_P5_CONFIRMED_CANDIDATE_GATE_SCHEMA_VERSION,
        "r48_p5_confirmed_candidate_gate_required_field_refs": list(P7_R48_P5_CONFIRMED_CANDIDATE_GATE_REQUIRED_FIELD_REFS),
        "r48_p5_confirmed_candidate_gate_function_ref": "build_p7_r48_p5_confirmed_candidate_gate_bodyfree",
        "r48_p5_confirmed_candidate_gate_contract_ref": "assert_p7_r48_p5_confirmed_candidate_gate_bodyfree_contract",
        "r48_p5_confirmed_candidate_gate": r48_gate,
        "required_condition_refs": list(P7_R49_P5_CONFIRMED_CANDIDATE_REQUIRED_CONDITION_REFS),
        "missing_requirement_refs": missing,
        "failed_requirement_count": len(missing),
        "review_session_status": clean_identifier(summary.get("review_session_status"), default="BLOCKED", max_length=80),
        "required_total_cases": P7_R49_REQUIRED_TOTAL_CASES,
        "case_count": _non_negative_int_r49(summary.get("case_count"), source="R49 R13 case_count"),
        "reviewed_case_count": _non_negative_int_r49(summary.get("reviewed_case_count"), source="R49 R13 reviewed_case_count"),
        "rating_row_count": _non_negative_int_r49(summary.get("rating_row_count"), source="R49 R13 rating_row_count"),
        "question_observation_row_count": _non_negative_int_r49(summary.get("question_observation_row_count"), source="R49 R13 question row count"),
        "question_observation_rows_complete": summary.get("question_observation_rows_complete") is True,
        "question_observation_repair_required_count": _non_negative_int_r49(summary.get("question_observation_repair_required_count"), source="R49 R13 question repair count"),
        "question_observation_execution_blocker_count": _non_negative_int_r49(summary.get("question_observation_execution_blocker_count"), source="R49 R13 question execution blocker count"),
        "family_coverage_satisfied": summary.get("family_coverage_satisfied") is True,
        "axis_targets_satisfied": summary.get("axis_targets_satisfied") is True,
        "red_case_count": _non_negative_int_r49(summary.get("red_case_count"), source="R49 R13 red_case_count"),
        "repair_required_case_count": _non_negative_int_r49(summary.get("repair_required_case_count"), source="R49 R13 repair_required_case_count"),
        "open_blocker_ids": list(summary.get("open_blocker_ids") or []),
        "open_execution_blocker_ids": list(summary.get("open_execution_blocker_ids") or []),
        "boundary_violation_blocker_ids": list(summary.get("boundary_violation_blocker_ids") or []),
        "disposal_status": clean_identifier(summary.get("disposal_status"), default="NOT_GENERATED", max_length=80),
        "disposal_verified_for_candidate": summary.get("disposal_verified_for_candidate") is True,
        "body_removed": summary.get("body_removed") is True,
        "reviewer_notes_removed": summary.get("reviewer_notes_removed") is True,
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "r48_p5_confirmed_candidate_gate_passed": r48_gate.get("p5_confirmed_candidate_gate_passed") is True,
        "question_observation_completeness_connected_to_gate": True,
        "question_observation_repair_required_blocks_candidate": True,
        "question_observation_execution_blocker_blocks_candidate": True,
        "p5_confirmed_candidate_gate_connection_ready": True,
        "p5_confirmed_candidate_gate_passed": gate_passed,
        "p5_human_blind_qa_confirmed_candidate": gate_passed,
        "p6_limited_human_readfeel_start_allowed_candidate": False,
        "p6_candidate_handoff_deferred_to_r14": True,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "real_device_modal_review_start_allowed": False,
        "real_device_modal_review_confirmed": False,
        "actual_p5_confirmed_candidate_gate_materialized_here": False,
        "actual_human_review_run_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_disposal_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "p8_question_design_material_candidate": summary.get("p8_question_design_material_candidate") is True,
        "p8_start_allowed": False,
        "release_allowed": False,
        "implemented_steps": list(P7_R49_R13_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R49_R13_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R49_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R49_R13_NEXT_REQUIRED_STEP_REF,
        "r0_current_source_r48_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_r48_case_matrix_handoff_validated": True,
        "r3_local_only_actual_packet_generation_preflight_done": True,
        "r4_actual_review_session_protocol_built": True,
        "r5_rating_row_ingestion_r48_normalizer_connected": True,
        "r6_blocker_execution_blocker_ingestion_connected": True,
        "r7_question_need_observation_row_schema_enum_fixed": True,
        "r8_question_need_observation_row_normalizer_connected": True,
        "r9_rating_question_observation_consistency_guard_connected": True,
        "r10_question_need_observation_summary_built": True,
        "r11_disposal_receipt_connection_fixed": True,
        "r12_review_handoff_summary_built": True,
        "r13_p5_confirmed_candidate_gate_connected": True,
        "public_contract": public_contract_flags(),
        "r49_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r49_p5_confirmed_candidate_gate_connection_contract(connection)
    return connection


def assert_p7_r49_p5_confirmed_candidate_gate_connection_contract(connection: Mapping[str, Any]) -> bool:
    data = safe_mapping(connection)
    _assert_required_fields(
        data,
        required=P7_R49_P5_CONFIRMED_CANDIDATE_GATE_CONNECTION_REQUIRED_FIELD_REFS,
        source="p7_r49_p5_confirmed_candidate_gate_connection",
    )
    _assert_common(
        data,
        schema_version=P7_R49_P5_CONFIRMED_CANDIDATE_GATE_CONNECTION_SCHEMA_VERSION,
        source="p7_r49_p5_confirmed_candidate_gate_connection",
        allowed_true_keys=("p5_human_blind_qa_confirmed_candidate", "p8_question_design_material_candidate"),
    )
    if data.get("policy_section") != "R49-13_p5_confirmed_candidate_gate_connection":
        raise ValueError("R49 R13 P5 gate policy section changed")
    summary = safe_mapping(data.get("r49_review_handoff_summary"))
    r48_gate = safe_mapping(data.get("r48_p5_confirmed_candidate_gate"))
    assert_p7_r49_review_handoff_summary_bodyfree_contract(summary)
    assert_p7_r48_p5_confirmed_candidate_gate_bodyfree_contract(r48_gate)
    if data.get("r48_p5_confirmed_candidate_gate_passed") is not (r48_gate.get("p5_confirmed_candidate_gate_passed") is True):
        raise ValueError("R49 R13 R48 gate pass flag mismatch")
    missing = _r49_p5_candidate_gate_missing_requirement_refs(summary, r48_gate)
    if data.get("missing_requirement_refs") != missing:
        raise ValueError("R49 R13 missing requirement refs mismatch")
    if data.get("failed_requirement_count") != len(missing):
        raise ValueError("R49 R13 failed requirement count mismatch")
    gate_passed = not missing
    if data.get("p5_confirmed_candidate_gate_passed") is not gate_passed:
        raise ValueError("R49 R13 final gate pass flag mismatch")
    if data.get("p5_human_blind_qa_confirmed_candidate") is not gate_passed:
        raise ValueError("R49 R13 P5 candidate flag must equal gate result")
    if data.get("p6_limited_human_readfeel_start_allowed_candidate") is not False:
        raise ValueError("R49 R13 must defer P6 start candidate to R49-14")
    if data.get("p6_candidate_handoff_deferred_to_r14") is not True:
        raise ValueError("R49 R13 must explicitly defer P6 candidate handoff to R49-14")
    if gate_passed:
        for true_key in (
            "r48_p5_confirmed_candidate_gate_passed",
            "question_observation_rows_complete",
            "disposal_verified_for_candidate",
            "body_removed",
            "reviewer_notes_removed",
        ):
            if data.get(true_key) is not True:
                raise ValueError(f"R49 R13 candidate requires {true_key}=True")
        if data.get("review_session_status") != "SUMMARY_FINALIZED":
            raise ValueError("R49 R13 candidate requires SUMMARY_FINALIZED status")
        if data.get("question_observation_repair_required_count") != 0 or data.get("question_observation_execution_blocker_count") != 0:
            raise ValueError("R49 R13 candidate requires no question-observation repair/execution blockers")
    for false_key in (
        "p5_human_blind_qa_confirmed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_limited_human_readfeel_confirmed",
        "real_device_modal_review_start_allowed",
        "real_device_modal_review_confirmed",
        "actual_p5_confirmed_candidate_gate_materialized_here",
        "actual_human_review_run_here",
        "actual_body_full_packet_generated_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_disposal_run_here",
        "actual_disposal_receipt_materialized_here",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R49 R13 P5 gate connection must keep {false_key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R49_R13_IMPLEMENTED_STEPS:
        raise ValueError("R49 R13 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R49_R13_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R49 R13 not-yet steps changed")
    if data.get("next_required_step") != P7_R49_R13_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R49 R13 must point to R49-14 next")
    _assert_r49_body_free(data, source="p7_r49_p5_confirmed_candidate_gate_connection")
    return True


def build_p7_r49_r12_r13_review_handoff_p5_gate_connection_freeze(
    *,
    r49_review_handoff_summary: Mapping[str, Any] | None = None,
    r49_p5_confirmed_candidate_gate_connection: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r49_r12_r13_review_handoff_p5_gate_connection_freeze",
) -> dict[str, Any]:
    """Combine R49-12 and R49-13 while keeping P6/P8/release closed."""

    summary = (
        safe_mapping(r49_review_handoff_summary)
        if r49_review_handoff_summary is not None
        else build_p7_r49_review_handoff_summary_bodyfree()
    )
    assert_p7_r49_review_handoff_summary_bodyfree_contract(summary)
    gate = (
        safe_mapping(r49_p5_confirmed_candidate_gate_connection)
        if r49_p5_confirmed_candidate_gate_connection is not None
        else build_p7_r49_p5_confirmed_candidate_gate_connection(r49_review_handoff_summary=summary)
    )
    assert_p7_r49_p5_confirmed_candidate_gate_connection_contract(gate)
    if gate.get("review_session_id") != summary.get("review_session_id"):
        raise ValueError("R49 R12/R13 freeze requires matching review_session_id")
    freeze = {
        **_false_flags(),
        "schema_version": P7_R49_R12_R13_REVIEW_HANDOFF_P5_GATE_CONNECTION_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R49_STEP,
        "scope": P7_R49_SCOPE,
        "policy_kind": P7_R49_POLICY_KIND,
        "policy_section": "R49-12_R49-13_review_handoff_p5_gate_connection_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r49_r12_r13_review_handoff_p5_gate_connection_freeze", max_length=160),
        "review_session_id": clean_identifier(summary.get("review_session_id"), default=P7_R49_DEFAULT_REVIEW_SESSION_ID, max_length=160),
        "review_kind": P7_R49_REVIEW_KIND,
        "packet_kind": P7_R49_PACKET_KIND,
        "r12_review_handoff_summary": summary,
        "r13_p5_confirmed_candidate_gate_connection": gate,
        "implemented_steps": list(P7_R49_R13_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R49_R13_NOT_YET_IMPLEMENTED_STEPS),
        "review_handoff_summary_ready": True,
        "p5_confirmed_candidate_gate_connected": True,
        "question_observation_completeness_connected_to_gate": True,
        "p5_human_blind_qa_confirmed_candidate": gate.get("p5_human_blind_qa_confirmed_candidate") is True,
        "p6_limited_human_readfeel_start_allowed_candidate": False,
        "p6_candidate_handoff_deferred_to_r14": True,
        "p8_question_design_material_candidate": summary.get("p8_question_design_material_candidate") is True,
        "p8_start_allowed": False,
        "release_allowed": False,
        "actual_human_review_run_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_disposal_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "first_next_work_ref": P7_R49_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R49_R13_NEXT_REQUIRED_STEP_REF,
        "r0_current_source_r48_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_r48_case_matrix_handoff_validated": True,
        "r3_local_only_actual_packet_generation_preflight_done": True,
        "r4_actual_review_session_protocol_built": True,
        "r5_rating_row_ingestion_r48_normalizer_connected": True,
        "r6_blocker_execution_blocker_ingestion_connected": True,
        "r7_question_need_observation_row_schema_enum_fixed": True,
        "r8_question_need_observation_row_normalizer_connected": True,
        "r9_rating_question_observation_consistency_guard_connected": True,
        "r10_question_need_observation_summary_built": True,
        "r11_disposal_receipt_connection_fixed": True,
        "r12_review_handoff_summary_built": True,
        "r13_p5_confirmed_candidate_gate_connected": True,
        "public_contract": public_contract_flags(),
        "r49_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r49_r12_r13_review_handoff_p5_gate_connection_freeze_contract(freeze)
    return freeze


def assert_p7_r49_r12_r13_review_handoff_p5_gate_connection_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_required_fields(
        data,
        required=P7_R49_R12_R13_REVIEW_HANDOFF_P5_GATE_CONNECTION_FREEZE_REQUIRED_FIELD_REFS,
        source="p7_r49_r12_r13_review_handoff_p5_gate_connection_freeze",
    )
    _assert_common(
        data,
        schema_version=P7_R49_R12_R13_REVIEW_HANDOFF_P5_GATE_CONNECTION_FREEZE_SCHEMA_VERSION,
        source="p7_r49_r12_r13_review_handoff_p5_gate_connection_freeze",
        allowed_true_keys=("p5_human_blind_qa_confirmed_candidate", "p8_question_design_material_candidate"),
    )
    if data.get("policy_section") != "R49-12_R49-13_review_handoff_p5_gate_connection_freeze":
        raise ValueError("R49 R12/R13 freeze policy section changed")
    summary = safe_mapping(data.get("r12_review_handoff_summary"))
    gate = safe_mapping(data.get("r13_p5_confirmed_candidate_gate_connection"))
    assert_p7_r49_review_handoff_summary_bodyfree_contract(summary)
    assert_p7_r49_p5_confirmed_candidate_gate_connection_contract(gate)
    if data.get("p5_human_blind_qa_confirmed_candidate") is not (gate.get("p5_human_blind_qa_confirmed_candidate") is True):
        raise ValueError("R49 R12/R13 freeze P5 candidate flag mismatch")
    if data.get("p6_limited_human_readfeel_start_allowed_candidate") is not False:
        raise ValueError("R49 R12/R13 freeze must keep P6 candidate deferred")
    if data.get("p6_candidate_handoff_deferred_to_r14") is not True:
        raise ValueError("R49 R12/R13 freeze must mark P6 handoff deferred")
    if data.get("p8_question_design_material_candidate") is not (summary.get("p8_question_design_material_candidate") is True):
        raise ValueError("R49 R12/R13 freeze P8 design material flag mismatch")
    for false_key in (
        "p8_start_allowed",
        "release_allowed",
        "actual_human_review_run_here",
        "actual_body_full_packet_generated_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_disposal_run_here",
        "actual_disposal_receipt_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R49 R12/R13 freeze must keep {false_key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R49_R13_IMPLEMENTED_STEPS:
        raise ValueError("R49 R12/R13 freeze implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R49_R13_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R49 R12/R13 freeze not-yet steps changed")
    if data.get("next_required_step") != P7_R49_R13_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R49 R12/R13 freeze must point to R49-14 next")
    _assert_r49_body_free(data, source="p7_r49_r12_r13_review_handoff_p5_gate_connection_freeze")
    return True


def _r49_p6_start_candidate_missing_requirement_refs(
    gate: Mapping[str, Any],
    p6_handoff_material: Mapping[str, Any],
) -> list[str]:
    missing: set[str] = set()
    summary = safe_mapping(gate.get("r49_review_handoff_summary"))
    if gate.get("p5_human_blind_qa_confirmed_candidate") is not True:
        missing.add("p5_human_blind_qa_confirmed_candidate")
    if gate.get("review_session_status") != "SUMMARY_FINALIZED":
        missing.add("review_session_status_summary_finalized")
    if _non_negative_int_r49(gate.get("rating_row_count"), source="R49 R14 rating row count") < P7_R49_REQUIRED_TOTAL_CASES:
        missing.add("rating_rows_complete")
    if gate.get("question_observation_rows_complete") is not True:
        missing.add("question_observation_rows_complete")
    if gate.get("family_coverage_satisfied") is not True:
        missing.add("family_coverage_satisfied")
    if gate.get("axis_targets_satisfied") is not True:
        missing.add("axis_targets_satisfied")
    if _non_negative_int_r49(gate.get("red_case_count"), source="R49 R14 red case count") != 0:
        missing.add("red_case_count_zero")
    if _non_negative_int_r49(gate.get("repair_required_case_count"), source="R49 R14 repair-required case count") != 0:
        missing.add("repair_required_case_count_zero")
    if gate.get("open_blocker_ids"):
        missing.add("open_blocker_ids_empty")
    if gate.get("open_execution_blocker_ids"):
        missing.add("open_execution_blocker_ids_empty")
    if _non_negative_int_r49(gate.get("question_observation_repair_required_count"), source="R49 R14 question repair count") != 0:
        missing.add("question_observation_repair_required_zero")
    if _non_negative_int_r49(gate.get("question_observation_execution_blocker_count"), source="R49 R14 question execution blocker count") != 0:
        missing.add("question_observation_execution_blocker_zero")
    if gate.get("disposal_verified_for_candidate") is not True:
        missing.add("disposal_verified_for_candidate")
    if gate.get("body_removed") is not True:
        missing.add("body_removed")
    if gate.get("reviewer_notes_removed") is not True:
        missing.add("reviewer_notes_removed")
    if gate.get("local_packet_exported") is not False:
        missing.add("local_packet_not_exported")
    if gate.get("content_hash_of_body_stored") is not False:
        missing.add("content_hash_of_body_not_stored")
    if p6_handoff_material.get("p6_limited_human_readfeel_review_ready") is not True:
        missing.add("p6_handoff_material_ready")
    if summary.get("question_observation_blocks_p5_candidate") is True or gate.get("p5_confirmed_candidate_gate_passed") is not True:
        missing.add("p6_handoff_does_not_hide_p5_unresolved")
    return [ref for ref in P7_R49_P6_START_CANDIDATE_REQUIRED_CONDITION_REFS if ref in missing]


def build_p7_r49_p6_limited_human_readfeel_start_candidate_handoff(
    *,
    r49_p5_confirmed_candidate_gate_connection: Mapping[str, Any] | None = None,
    p5_confirmed_candidate_gate_connection: Mapping[str, Any] | None = None,
    r12_r13_review_handoff_p5_gate_connection_freeze: Mapping[str, Any] | None = None,
    r49_r12_r13_review_handoff_p5_gate_connection_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r49_p6_limited_human_readfeel_start_candidate_handoff",
) -> dict[str, Any]:
    """Build the R49-14 P6 start-candidate handoff without starting P6."""

    supplied = [
        value is not None
        for value in (
            r49_p5_confirmed_candidate_gate_connection,
            p5_confirmed_candidate_gate_connection,
            r12_r13_review_handoff_p5_gate_connection_freeze,
            r49_r12_r13_review_handoff_p5_gate_connection_freeze,
        )
    ]
    if sum(supplied) > 1:
        raise ValueError("provide only one R49 R13 gate or R12/R13 freeze value")
    if r12_r13_review_handoff_p5_gate_connection_freeze is not None or r49_r12_r13_review_handoff_p5_gate_connection_freeze is not None:
        freeze = safe_mapping(
            r12_r13_review_handoff_p5_gate_connection_freeze
            if r12_r13_review_handoff_p5_gate_connection_freeze is not None
            else r49_r12_r13_review_handoff_p5_gate_connection_freeze
        )
        assert_p7_r49_r12_r13_review_handoff_p5_gate_connection_freeze_contract(freeze)
        gate = safe_mapping(freeze.get("r13_p5_confirmed_candidate_gate_connection"))
    else:
        gate = (
            safe_mapping(r49_p5_confirmed_candidate_gate_connection)
            if r49_p5_confirmed_candidate_gate_connection is not None
            else safe_mapping(p5_confirmed_candidate_gate_connection)
            if p5_confirmed_candidate_gate_connection is not None
            else build_p7_r49_p5_confirmed_candidate_gate_connection()
        )
    assert_p7_r49_p5_confirmed_candidate_gate_connection_contract(gate)
    _assert_r49_body_free(gate, source="p7_r49.r13_gate_for_p6_candidate_handoff")

    summary = safe_mapping(gate.get("r49_review_handoff_summary"))
    question_summary = safe_mapping(summary.get("r49_question_need_observation_summary"))
    p6_handoff_material = build_p6_limited_human_readfeel_handoff_material()
    assert_p6_limited_human_readfeel_handoff_material_contract(p6_handoff_material)
    _assert_r49_body_free(p6_handoff_material, source="p7_r49.r46_p6_handoff_material")

    missing = _r49_p6_start_candidate_missing_requirement_refs(gate, p6_handoff_material)
    candidate = not missing
    handoff = {
        **_false_flags(),
        "schema_version": P7_R49_P6_LIMITED_HUMAN_READFEEL_START_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R49_STEP,
        "scope": P7_R49_SCOPE,
        "policy_kind": P7_R49_POLICY_KIND,
        "policy_section": "R49-14_p6_limited_human_readfeel_start_candidate_handoff",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r49_p6_limited_human_readfeel_start_candidate_handoff", max_length=160),
        "review_session_id": clean_identifier(gate.get("review_session_id"), default=P7_R49_DEFAULT_REVIEW_SESSION_ID, max_length=160),
        "review_kind": P7_R49_REVIEW_KIND,
        "packet_kind": P7_R49_PACKET_KIND,
        "r13_p5_gate_connection_schema_version": P7_R49_P5_CONFIRMED_CANDIDATE_GATE_CONNECTION_SCHEMA_VERSION,
        "r13_p5_gate_connection_ref": clean_identifier(gate.get("material_id"), default="p7_r49_p5_confirmed_candidate_gate_connection", max_length=160),
        "r49_p5_confirmed_candidate_gate_connection": gate,
        "r46_p6_limited_human_readfeel_handoff_schema_version": P7_R46_P6_LIMITED_HUMAN_READFEEL_HANDOFF_SCHEMA_VERSION,
        "r46_p6_limited_human_readfeel_handoff_function_ref": "build_p6_limited_human_readfeel_handoff_material",
        "r46_p6_limited_human_readfeel_handoff_contract_ref": "assert_p6_limited_human_readfeel_handoff_material_contract",
        "r46_p6_limited_human_readfeel_handoff_material": p6_handoff_material,
        "required_condition_refs": list(P7_R49_P6_START_CANDIDATE_REQUIRED_CONDITION_REFS),
        "missing_requirement_refs": missing,
        "failed_requirement_count": len(missing),
        "review_session_status": clean_identifier(gate.get("review_session_status"), default="BLOCKED", max_length=80),
        "required_total_cases": P7_R49_REQUIRED_TOTAL_CASES,
        "case_count": _non_negative_int_r49(gate.get("case_count"), source="R49 R14 case count"),
        "reviewed_case_count": _non_negative_int_r49(gate.get("reviewed_case_count"), source="R49 R14 reviewed case count"),
        "rating_row_count": _non_negative_int_r49(gate.get("rating_row_count"), source="R49 R14 rating row count"),
        "question_observation_row_count": _non_negative_int_r49(gate.get("question_observation_row_count"), source="R49 R14 question row count"),
        "rating_rows_complete": _non_negative_int_r49(gate.get("rating_row_count"), source="R49 R14 rating row count") >= P7_R49_REQUIRED_TOTAL_CASES,
        "question_observation_rows_complete": gate.get("question_observation_rows_complete") is True,
        "family_coverage_satisfied": gate.get("family_coverage_satisfied") is True,
        "axis_targets_satisfied": gate.get("axis_targets_satisfied") is True,
        "red_case_count": _non_negative_int_r49(gate.get("red_case_count"), source="R49 R14 red case count"),
        "repair_required_case_count": _non_negative_int_r49(gate.get("repair_required_case_count"), source="R49 R14 repair-required case count"),
        "open_blocker_ids": list(gate.get("open_blocker_ids") or []),
        "open_execution_blocker_ids": list(gate.get("open_execution_blocker_ids") or []),
        "boundary_violation_blocker_ids": list(gate.get("boundary_violation_blocker_ids") or []),
        "question_observation_repair_required_count": _non_negative_int_r49(gate.get("question_observation_repair_required_count"), source="R49 R14 question repair count"),
        "question_observation_execution_blocker_count": _non_negative_int_r49(gate.get("question_observation_execution_blocker_count"), source="R49 R14 question execution count"),
        "disposal_status": clean_identifier(gate.get("disposal_status"), default="NOT_GENERATED", max_length=80),
        "disposal_verified_for_candidate": gate.get("disposal_verified_for_candidate") is True,
        "body_removed": gate.get("body_removed") is True,
        "reviewer_notes_removed": gate.get("reviewer_notes_removed") is True,
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "p5_human_blind_qa_confirmed_candidate": gate.get("p5_human_blind_qa_confirmed_candidate") is True,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_candidate_handoff_ready": True,
        "p6_limited_human_readfeel_start_allowed_candidate": candidate,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "p6_review_families": list(P6_LIMITED_READFEEL_REVIEW_FAMILIES),
        "p6_no_connect_families": list(P6_NO_CONNECT_FAMILIES),
        "p6_rating_axes": list(P6_LIMITED_READFEEL_RATING_AXES),
        "p6_target_thresholds": dict(P6_LIMITED_READFEEL_TARGETS),
        "p6_hold_refs_preserved": True,
        "p6_unresolved_hold_refs": [P6_LIMITED_HUMAN_READFEEL_HOLD_REF, P6_LIMITED_HUMAN_READFEEL_RETURN_HOLD_REF],
        "p6_handoff_does_not_hide_p5_unresolved": True,
        "p6_handoff_missing_requirements_visible": True,
        "full_backend_suite_green_claim_used_for_p6_start_allowed": False,
        "p6_start_permission_granted_here": False,
        "real_device_modal_review_start_allowed": False,
        "real_device_modal_review_confirmed": False,
        "p7_complete": False,
        "p8_question_design_material_candidate": question_summary.get("p8_question_design_material_candidate") is True,
        "p8_start_allowed": False,
        "release_allowed": False,
        "actual_p6_handoff_materialized_here": False,
        "actual_human_review_run_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_disposal_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "implemented_steps": list(P7_R49_R14_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R49_R14_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R49_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R49_R14_NEXT_REQUIRED_STEP_REF,
        "r0_current_source_r48_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_r48_case_matrix_handoff_validated": True,
        "r3_local_only_actual_packet_generation_preflight_done": True,
        "r4_actual_review_session_protocol_built": True,
        "r5_rating_row_ingestion_r48_normalizer_connected": True,
        "r6_blocker_execution_blocker_ingestion_connected": True,
        "r7_question_need_observation_row_schema_enum_fixed": True,
        "r8_question_need_observation_row_normalizer_connected": True,
        "r9_rating_question_observation_consistency_guard_connected": True,
        "r10_question_need_observation_summary_built": True,
        "r11_disposal_receipt_connection_fixed": True,
        "r12_review_handoff_summary_built": True,
        "r13_p5_confirmed_candidate_gate_connected": True,
        "r14_p6_limited_human_readfeel_start_candidate_handoff_built": True,
        "public_contract": public_contract_flags(),
        "r49_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r49_p6_limited_human_readfeel_start_candidate_handoff_contract(handoff)
    return handoff


def assert_p7_r49_p6_limited_human_readfeel_start_candidate_handoff_contract(handoff: Mapping[str, Any]) -> bool:
    data = safe_mapping(handoff)
    _assert_required_fields(
        data,
        required=P7_R49_P6_LIMITED_HUMAN_READFEEL_START_CANDIDATE_HANDOFF_REQUIRED_FIELD_REFS,
        source="p7_r49_p6_limited_human_readfeel_start_candidate_handoff",
    )
    _assert_common(
        data,
        schema_version=P7_R49_P6_LIMITED_HUMAN_READFEEL_START_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        source="p7_r49_p6_limited_human_readfeel_start_candidate_handoff",
        allowed_true_keys=(
            "p5_human_blind_qa_confirmed_candidate",
            "p6_limited_human_readfeel_start_allowed_candidate",
            "p8_question_design_material_candidate",
        ),
    )
    if data.get("policy_section") != "R49-14_p6_limited_human_readfeel_start_candidate_handoff":
        raise ValueError("R49 R14 P6 handoff policy section changed")
    gate = safe_mapping(data.get("r49_p5_confirmed_candidate_gate_connection"))
    p6_material = safe_mapping(data.get("r46_p6_limited_human_readfeel_handoff_material"))
    assert_p7_r49_p5_confirmed_candidate_gate_connection_contract(gate)
    assert_p6_limited_human_readfeel_handoff_material_contract(p6_material)
    missing = _r49_p6_start_candidate_missing_requirement_refs(gate, p6_material)
    if data.get("missing_requirement_refs") != missing:
        raise ValueError("R49 R14 P6 candidate missing requirement refs mismatch")
    if data.get("failed_requirement_count") != len(missing):
        raise ValueError("R49 R14 failed requirement count mismatch")
    candidate = not missing
    if data.get("p6_limited_human_readfeel_start_allowed_candidate") is not candidate:
        raise ValueError("R49 R14 P6 start candidate flag mismatch")
    if data.get("required_condition_refs") != list(P7_R49_P6_START_CANDIDATE_REQUIRED_CONDITION_REFS):
        raise ValueError("R49 R14 required condition refs changed")
    if data.get("r46_p6_limited_human_readfeel_handoff_schema_version") != P7_R46_P6_LIMITED_HUMAN_READFEEL_HANDOFF_SCHEMA_VERSION:
        raise ValueError("R49 R14 R46 P6 handoff schema changed")
    if tuple(data.get("p6_review_families") or ()) != P6_LIMITED_READFEEL_REVIEW_FAMILIES:
        raise ValueError("R49 R14 P6 review families changed")
    if tuple(data.get("p6_no_connect_families") or ()) != P6_NO_CONNECT_FAMILIES:
        raise ValueError("R49 R14 P6 no-connect families changed")
    if tuple(data.get("p6_rating_axes") or ()) != P6_LIMITED_READFEEL_RATING_AXES:
        raise ValueError("R49 R14 P6 rating axes changed")
    if safe_mapping(data.get("p6_target_thresholds")) != dict(P6_LIMITED_READFEEL_TARGETS):
        raise ValueError("R49 R14 P6 target thresholds changed")
    hold_refs = set(dedupe_identifiers(data.get("p6_unresolved_hold_refs"), limit=20, max_length=80))
    if {P6_LIMITED_HUMAN_READFEEL_HOLD_REF, P6_LIMITED_HUMAN_READFEEL_RETURN_HOLD_REF} - hold_refs:
        raise ValueError("R49 R14 must preserve P6 unresolved hold refs")
    if data.get("p5_human_blind_qa_confirmed_candidate") is not (gate.get("p5_human_blind_qa_confirmed_candidate") is True):
        raise ValueError("R49 R14 P5 candidate flag mismatch")
    if data.get("p8_question_design_material_candidate") is not (
        safe_mapping(safe_mapping(gate.get("r49_review_handoff_summary")).get("r49_question_need_observation_summary")).get("p8_question_design_material_candidate") is True
    ):
        raise ValueError("R49 R14 P8 material candidate context mismatch")
    for false_key in (
        "p5_human_blind_qa_confirmed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_limited_human_readfeel_confirmed",
        "full_backend_suite_green_claim_used_for_p6_start_allowed",
        "p6_start_permission_granted_here",
        "real_device_modal_review_start_allowed",
        "real_device_modal_review_confirmed",
        "p7_complete",
        "p8_start_allowed",
        "release_allowed",
        "actual_p6_handoff_materialized_here",
        "actual_human_review_run_here",
        "actual_body_full_packet_generated_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_disposal_run_here",
        "actual_disposal_receipt_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R49 R14 P6 handoff must keep {false_key}=False")
    for true_key in (
        "p6_limited_human_readfeel_start_candidate_handoff_ready",
        "p6_hold_refs_preserved",
        "p6_handoff_does_not_hide_p5_unresolved",
        "p6_handoff_missing_requirements_visible",
        "r14_p6_limited_human_readfeel_start_candidate_handoff_built",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R49 R14 P6 handoff must keep {true_key}=True")
    if tuple(data.get("implemented_steps") or ()) != P7_R49_R14_IMPLEMENTED_STEPS:
        raise ValueError("R49 R14 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R49_R14_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R49 R14 not-yet steps changed")
    if data.get("next_required_step") != P7_R49_R14_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R49 R14 must point to R49-15 next")
    _assert_r49_body_free(data, source="p7_r49_p6_limited_human_readfeel_start_candidate_handoff")
    return True


def _question_summary_from_r14_handoff(handoff: Mapping[str, Any]) -> dict[str, Any]:
    gate = safe_mapping(handoff.get("r49_p5_confirmed_candidate_gate_connection"))
    summary = safe_mapping(gate.get("r49_review_handoff_summary"))
    question_summary = safe_mapping(summary.get("r49_question_need_observation_summary"))
    assert_p7_r49_question_need_observation_summary_bodyfree_contract(question_summary)
    return question_summary


def _p8_design_material_missing_requirement_refs(question_summary: Mapping[str, Any]) -> list[str]:
    missing: list[str] = []
    if question_summary.get("question_observation_rows_complete") is not True:
        missing.append("question_observation_rows_complete")
    if question_summary.get("p8_question_design_material_candidate") is not True:
        missing.append("p8_question_design_material_candidate")
    if _non_negative_int_r49(question_summary.get("p8_design_material_candidate_row_count"), source="R49 R15 p8 candidate row count") <= 0:
        missing.append("p8_design_material_candidate_row_present")
    return missing


def build_p7_r49_p8_question_design_material_candidate_handoff(
    *,
    r49_p6_limited_human_readfeel_start_candidate_handoff: Mapping[str, Any] | None = None,
    p6_limited_human_readfeel_start_candidate_handoff: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r49_p8_question_design_material_candidate_handoff",
) -> dict[str, Any]:
    """Build the R49-15 P8 question-design material candidate handoff."""

    if r49_p6_limited_human_readfeel_start_candidate_handoff is not None and p6_limited_human_readfeel_start_candidate_handoff is not None:
        raise ValueError("provide only one R49 R14 P6 handoff value")
    r14 = (
        safe_mapping(r49_p6_limited_human_readfeel_start_candidate_handoff)
        if r49_p6_limited_human_readfeel_start_candidate_handoff is not None
        else safe_mapping(p6_limited_human_readfeel_start_candidate_handoff)
        if p6_limited_human_readfeel_start_candidate_handoff is not None
        else build_p7_r49_p6_limited_human_readfeel_start_candidate_handoff()
    )
    assert_p7_r49_p6_limited_human_readfeel_start_candidate_handoff_contract(r14)
    _assert_r49_body_free(r14, source="p7_r49.r14_p6_handoff_for_p8_material")
    question_summary = _question_summary_from_r14_handoff(r14)
    primary_counts = safe_mapping(question_summary.get("primary_class_counts"))
    repair_counts = safe_mapping(question_summary.get("repair_required_counts"))
    missing = _p8_design_material_missing_requirement_refs(question_summary)
    not_question_repair = _non_negative_int_r49(question_summary.get("not_question_repair_required_count"), source="R49 R15 not-question repair count")
    p8_start_blockers = ["p8_start_not_allowed_in_r49"]
    if question_summary.get("question_observation_rows_complete") is not True:
        p8_start_blockers.append("question_observation_rows_incomplete")
    if not_question_repair:
        p8_start_blockers.append("not_question_repair_required_before_p8_start")
    if r14.get("p6_limited_human_readfeel_start_allowed_candidate") is not True:
        p8_start_blockers.append("p6_limited_human_readfeel_candidate_not_ready")

    handoff = {
        **_false_flags(),
        "schema_version": P7_R49_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R49_STEP,
        "scope": P7_R49_SCOPE,
        "policy_kind": P7_R49_POLICY_KIND,
        "policy_section": "R49-15_p8_question_design_material_candidate_handoff",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r49_p8_question_design_material_candidate_handoff", max_length=160),
        "review_session_id": clean_identifier(r14.get("review_session_id"), default=P7_R49_DEFAULT_REVIEW_SESSION_ID, max_length=160),
        "review_kind": P7_R49_REVIEW_KIND,
        "packet_kind": P7_R49_PACKET_KIND,
        "r14_p6_handoff_schema_version": P7_R49_P6_LIMITED_HUMAN_READFEEL_START_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        "r14_p6_handoff_ref": clean_identifier(r14.get("material_id"), default="p7_r49_p6_limited_human_readfeel_start_candidate_handoff", max_length=160),
        "r49_p6_limited_human_readfeel_start_candidate_handoff": r14,
        "question_need_observation_summary_schema_version": P7_R49_QUESTION_NEED_OBSERVATION_SUMMARY_BODYFREE_SCHEMA_VERSION,
        "question_need_observation_summary_ref": clean_identifier(question_summary.get("material_id"), default="p7_r49_question_need_observation_summary_bodyfree", max_length=160),
        "r49_question_need_observation_summary": question_summary,
        "p8_question_design_material_candidate_handoff_ready": question_summary.get("question_observation_rows_complete") is True,
        "p8_question_design_material_candidate": question_summary.get("p8_question_design_material_candidate") is True,
        "p8_design_material_candidate_missing_requirement_refs": missing,
        "p8_design_material_candidate_failed_requirement_count": len(missing),
        "p8_design_material_bodyfree": True,
        "total_case_count": _non_negative_int_r49(question_summary.get("total_case_count"), source="R49 R15 total case count"),
        "question_observation_row_count": _non_negative_int_r49(question_summary.get("question_observation_row_count"), source="R49 R15 question row count"),
        "question_observation_rows_complete": question_summary.get("question_observation_rows_complete") is True,
        "no_question_needed_count": _non_negative_int_r49(primary_counts.get("no_question_needed_emlis_can_observe"), source="R49 R15 no question count"),
        "question_may_reduce_overread_risk_count": _non_negative_int_r49(primary_counts.get("question_may_reduce_overread_risk"), source="R49 R15 question reduce risk count"),
        "question_would_make_immediate_observation_heavy_count": _non_negative_int_r49(primary_counts.get("question_would_make_immediate_observation_heavy"), source="R49 R15 question heavy count"),
        "not_question_repair_required_count": not_question_repair,
        "emlis_readfeel_repair_required_count": _non_negative_int_r49(primary_counts.get("not_question_emlis_readfeel_repair_required"), source="R49 R15 emlis repair count"),
        "p5_surface_repair_required_count": _non_negative_int_r49(primary_counts.get("not_question_p5_surface_repair_required"), source="R49 R15 p5 surface repair count"),
        "gate_boundary_repair_required_count": _non_negative_int_r49(primary_counts.get("not_question_gate_boundary_required"), source="R49 R15 gate repair count"),
        "plus_single_question_candidate_later_count": _non_negative_int_r49(question_summary.get("plus_single_question_candidate_later_count"), source="R49 R15 plus count"),
        "premium_deep_dive_candidate_later_count": _non_negative_int_r49(question_summary.get("premium_deep_dive_candidate_later_count"), source="R49 R15 premium count"),
        "p8_design_material_candidate_row_count": _non_negative_int_r49(question_summary.get("p8_design_material_candidate_row_count"), source="R49 R15 p8 row count"),
        "primary_class_counts": primary_counts,
        "ambiguity_kind_counts": safe_mapping(question_summary.get("ambiguity_kind_counts")),
        "one_question_fit_counts": safe_mapping(question_summary.get("one_question_fit_counts")),
        "repair_required_counts": repair_counts,
        "plan_candidate_flag_counts": safe_mapping(question_summary.get("plan_candidate_flag_counts")),
        "p8_start_blocker_refs": p8_start_blockers,
        "p8_pre_design_repair_required_before_start": not_question_repair > 0,
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
        "p5_human_blind_qa_confirmed_candidate": r14.get("p5_human_blind_qa_confirmed_candidate") is True,
        "p6_limited_human_readfeel_start_allowed_candidate": r14.get("p6_limited_human_readfeel_start_allowed_candidate") is True,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "actual_p8_design_material_handoff_materialized_here": False,
        "actual_human_review_run_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_question_need_observation_summary_materialized_here": False,
        "actual_disposal_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "implemented_steps": list(P7_R49_R15_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R49_R15_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R49_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R49_R15_NEXT_REQUIRED_STEP_REF,
        "r0_current_source_r48_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_r48_case_matrix_handoff_validated": True,
        "r3_local_only_actual_packet_generation_preflight_done": True,
        "r4_actual_review_session_protocol_built": True,
        "r5_rating_row_ingestion_r48_normalizer_connected": True,
        "r6_blocker_execution_blocker_ingestion_connected": True,
        "r7_question_need_observation_row_schema_enum_fixed": True,
        "r8_question_need_observation_row_normalizer_connected": True,
        "r9_rating_question_observation_consistency_guard_connected": True,
        "r10_question_need_observation_summary_built": True,
        "r11_disposal_receipt_connection_fixed": True,
        "r12_review_handoff_summary_built": True,
        "r13_p5_confirmed_candidate_gate_connected": True,
        "r14_p6_limited_human_readfeel_start_candidate_handoff_built": True,
        "r15_p8_question_design_material_candidate_handoff_built": True,
        "public_contract": public_contract_flags(),
        "r49_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r49_p8_question_design_material_candidate_handoff_contract(handoff)
    return handoff


def assert_p7_r49_p8_question_design_material_candidate_handoff_contract(handoff: Mapping[str, Any]) -> bool:
    data = safe_mapping(handoff)
    _assert_required_fields(
        data,
        required=P7_R49_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_REQUIRED_FIELD_REFS,
        source="p7_r49_p8_question_design_material_candidate_handoff",
    )
    _assert_common(
        data,
        schema_version=P7_R49_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        source="p7_r49_p8_question_design_material_candidate_handoff",
        allowed_true_keys=(
            "p5_human_blind_qa_confirmed_candidate",
            "p6_limited_human_readfeel_start_allowed_candidate",
            "p8_question_design_material_candidate",
        ),
    )
    if data.get("policy_section") != "R49-15_p8_question_design_material_candidate_handoff":
        raise ValueError("R49 R15 P8 material policy section changed")
    r14 = safe_mapping(data.get("r49_p6_limited_human_readfeel_start_candidate_handoff"))
    question_summary = safe_mapping(data.get("r49_question_need_observation_summary"))
    assert_p7_r49_p6_limited_human_readfeel_start_candidate_handoff_contract(r14)
    assert_p7_r49_question_need_observation_summary_bodyfree_contract(question_summary)
    missing = _p8_design_material_missing_requirement_refs(question_summary)
    if data.get("p8_design_material_candidate_missing_requirement_refs") != missing:
        raise ValueError("R49 R15 P8 material missing requirement refs mismatch")
    if data.get("p8_design_material_candidate_failed_requirement_count") != len(missing):
        raise ValueError("R49 R15 P8 material failed requirement count mismatch")
    if data.get("p8_question_design_material_candidate") is not (question_summary.get("p8_question_design_material_candidate") is True):
        raise ValueError("R49 R15 P8 material candidate flag mismatch")
    primary_counts = safe_mapping(question_summary.get("primary_class_counts"))
    if data.get("no_question_needed_count") != primary_counts.get("no_question_needed_emlis_can_observe"):
        raise ValueError("R49 R15 no-question count mismatch")
    if data.get("question_may_reduce_overread_risk_count") != primary_counts.get("question_may_reduce_overread_risk"):
        raise ValueError("R49 R15 question-risk count mismatch")
    if data.get("question_would_make_immediate_observation_heavy_count") != primary_counts.get("question_would_make_immediate_observation_heavy"):
        raise ValueError("R49 R15 heavy-question count mismatch")
    if data.get("emlis_readfeel_repair_required_count") != primary_counts.get("not_question_emlis_readfeel_repair_required"):
        raise ValueError("R49 R15 Emlis repair count mismatch")
    if data.get("p5_surface_repair_required_count") != primary_counts.get("not_question_p5_surface_repair_required"):
        raise ValueError("R49 R15 P5 surface repair count mismatch")
    if data.get("gate_boundary_repair_required_count") != primary_counts.get("not_question_gate_boundary_required"):
        raise ValueError("R49 R15 gate repair count mismatch")
    if data.get("not_question_repair_required_count") != question_summary.get("not_question_repair_required_count"):
        raise ValueError("R49 R15 not-question repair count mismatch")
    if data.get("p8_pre_design_repair_required_before_start") is not (data.get("not_question_repair_required_count") > 0):
        raise ValueError("R49 R15 repair-before-start flag mismatch")
    if "p8_start_not_allowed_in_r49" not in set(data.get("p8_start_blocker_refs") or []):
        raise ValueError("R49 R15 must always keep P8 start blocked in R49")
    for false_key in (
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
        "p6_limited_human_readfeel_start_allowed",
        "p6_limited_human_readfeel_confirmed",
        "p7_complete",
        "p8_start_allowed",
        "release_allowed",
        "actual_p8_design_material_handoff_materialized_here",
        "actual_human_review_run_here",
        "actual_body_full_packet_generated_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_question_need_observation_summary_materialized_here",
        "actual_disposal_run_here",
        "actual_disposal_receipt_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R49 R15 P8 material handoff must keep {false_key}=False")
    for true_key in (
        "p8_design_material_bodyfree",
        "r14_p6_limited_human_readfeel_start_candidate_handoff_built",
        "r15_p8_question_design_material_candidate_handoff_built",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R49 R15 P8 material handoff must keep {true_key}=True")
    if tuple(data.get("implemented_steps") or ()) != P7_R49_R15_IMPLEMENTED_STEPS:
        raise ValueError("R49 R15 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R49_R15_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R49 R15 not-yet steps changed")
    if data.get("next_required_step") != P7_R49_R15_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R49 R15 must point to R49-16 next")
    _assert_r49_body_free(data, source="p7_r49_p8_question_design_material_candidate_handoff")
    return True


def build_p7_r49_r14_r15_p6_p8_candidate_handoff_freeze(
    *,
    r49_p6_limited_human_readfeel_start_candidate_handoff: Mapping[str, Any] | None = None,
    r49_p8_question_design_material_candidate_handoff: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r49_r14_r15_p6_p8_candidate_handoff_freeze",
) -> dict[str, Any]:
    """Combine R49-14 and R49-15 while keeping P6/P8/release permissions closed."""

    r14 = (
        safe_mapping(r49_p6_limited_human_readfeel_start_candidate_handoff)
        if r49_p6_limited_human_readfeel_start_candidate_handoff is not None
        else build_p7_r49_p6_limited_human_readfeel_start_candidate_handoff()
    )
    assert_p7_r49_p6_limited_human_readfeel_start_candidate_handoff_contract(r14)
    r15 = (
        safe_mapping(r49_p8_question_design_material_candidate_handoff)
        if r49_p8_question_design_material_candidate_handoff is not None
        else build_p7_r49_p8_question_design_material_candidate_handoff(
            r49_p6_limited_human_readfeel_start_candidate_handoff=r14
        )
    )
    assert_p7_r49_p8_question_design_material_candidate_handoff_contract(r15)
    if r14.get("review_session_id") != r15.get("review_session_id"):
        raise ValueError("R49 R14/R15 freeze requires matching review_session_id")
    freeze = {
        **_false_flags(),
        "schema_version": P7_R49_R14_R15_P6_P8_CANDIDATE_HANDOFF_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R49_STEP,
        "scope": P7_R49_SCOPE,
        "policy_kind": P7_R49_POLICY_KIND,
        "policy_section": "R49-14_R49-15_p6_p8_candidate_handoff_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r49_r14_r15_p6_p8_candidate_handoff_freeze", max_length=160),
        "review_session_id": clean_identifier(r14.get("review_session_id"), default=P7_R49_DEFAULT_REVIEW_SESSION_ID, max_length=160),
        "review_kind": P7_R49_REVIEW_KIND,
        "packet_kind": P7_R49_PACKET_KIND,
        "r14_p6_limited_human_readfeel_start_candidate_handoff": r14,
        "r15_p8_question_design_material_candidate_handoff": r15,
        "implemented_steps": list(P7_R49_R15_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R49_R15_NOT_YET_IMPLEMENTED_STEPS),
        "p5_human_blind_qa_confirmed_candidate": r14.get("p5_human_blind_qa_confirmed_candidate") is True,
        "p6_limited_human_readfeel_start_allowed_candidate": r14.get("p6_limited_human_readfeel_start_allowed_candidate") is True,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "p8_question_design_material_candidate": r15.get("p8_question_design_material_candidate") is True,
        "p8_detail_design_allowed_here": False,
        "p8_implementation_spec_finalized_here": False,
        "question_trigger_logic_implemented_here": False,
        "api_db_rn_response_key_changed_here": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "actual_human_review_run_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_disposal_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "first_next_work_ref": P7_R49_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R49_R15_NEXT_REQUIRED_STEP_REF,
        "r0_current_source_r48_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_r48_case_matrix_handoff_validated": True,
        "r3_local_only_actual_packet_generation_preflight_done": True,
        "r4_actual_review_session_protocol_built": True,
        "r5_rating_row_ingestion_r48_normalizer_connected": True,
        "r6_blocker_execution_blocker_ingestion_connected": True,
        "r7_question_need_observation_row_schema_enum_fixed": True,
        "r8_question_need_observation_row_normalizer_connected": True,
        "r9_rating_question_observation_consistency_guard_connected": True,
        "r10_question_need_observation_summary_built": True,
        "r11_disposal_receipt_connection_fixed": True,
        "r12_review_handoff_summary_built": True,
        "r13_p5_confirmed_candidate_gate_connected": True,
        "r14_p6_limited_human_readfeel_start_candidate_handoff_built": True,
        "r15_p8_question_design_material_candidate_handoff_built": True,
        "public_contract": public_contract_flags(),
        "r49_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r49_r14_r15_p6_p8_candidate_handoff_freeze_contract(freeze)
    return freeze


def assert_p7_r49_r14_r15_p6_p8_candidate_handoff_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_required_fields(
        data,
        required=P7_R49_R14_R15_P6_P8_CANDIDATE_HANDOFF_FREEZE_REQUIRED_FIELD_REFS,
        source="p7_r49_r14_r15_p6_p8_candidate_handoff_freeze",
    )
    _assert_common(
        data,
        schema_version=P7_R49_R14_R15_P6_P8_CANDIDATE_HANDOFF_FREEZE_SCHEMA_VERSION,
        source="p7_r49_r14_r15_p6_p8_candidate_handoff_freeze",
        allowed_true_keys=(
            "p5_human_blind_qa_confirmed_candidate",
            "p6_limited_human_readfeel_start_allowed_candidate",
            "p8_question_design_material_candidate",
        ),
    )
    if data.get("policy_section") != "R49-14_R49-15_p6_p8_candidate_handoff_freeze":
        raise ValueError("R49 R14/R15 freeze policy section changed")
    r14 = safe_mapping(data.get("r14_p6_limited_human_readfeel_start_candidate_handoff"))
    r15 = safe_mapping(data.get("r15_p8_question_design_material_candidate_handoff"))
    assert_p7_r49_p6_limited_human_readfeel_start_candidate_handoff_contract(r14)
    assert_p7_r49_p8_question_design_material_candidate_handoff_contract(r15)
    if data.get("p6_limited_human_readfeel_start_allowed_candidate") is not (r14.get("p6_limited_human_readfeel_start_allowed_candidate") is True):
        raise ValueError("R49 R14/R15 P6 candidate flag mismatch")
    if data.get("p8_question_design_material_candidate") is not (r15.get("p8_question_design_material_candidate") is True):
        raise ValueError("R49 R14/R15 P8 candidate flag mismatch")
    for false_key in (
        "p6_limited_human_readfeel_start_allowed",
        "p6_limited_human_readfeel_confirmed",
        "p8_detail_design_allowed_here",
        "p8_implementation_spec_finalized_here",
        "question_trigger_logic_implemented_here",
        "api_db_rn_response_key_changed_here",
        "p7_complete",
        "p8_start_allowed",
        "release_allowed",
        "actual_human_review_run_here",
        "actual_body_full_packet_generated_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_disposal_run_here",
        "actual_disposal_receipt_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R49 R14/R15 freeze must keep {false_key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R49_R15_IMPLEMENTED_STEPS:
        raise ValueError("R49 R14/R15 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R49_R15_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R49 R14/R15 not-yet steps changed")
    if data.get("next_required_step") != P7_R49_R15_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R49 R14/R15 must point to R49-16 next")
    _assert_r49_body_free(data, source="p7_r49_r14_r15_p6_p8_candidate_handoff_freeze")
    return True


def _r49_forbidden_path_refs(value: Any, *, source: str) -> list[str]:
    paths: list[str] = []

    def walk(node: Any, path: str) -> None:
        if isinstance(node, Mapping):
            for key, child in node.items():
                key_ref = str(key)
                child_path = f"{path}.{key_ref}" if path else key_ref
                if key_ref in P7_R49_BODY_FREE_FORBIDDEN_FIELD_REFS:
                    paths.append(child_path)
                walk(child, child_path)
        elif isinstance(node, Sequence) and not isinstance(node, (str, bytes, bytearray)):
            for index, child in enumerate(node):
                walk(child, f"{path}[{index}]")

    walk(value, source)
    return paths


def _r49_marker_true_path_refs(value: Any, *, source: str) -> list[str]:
    paths: list[str] = []

    def walk(node: Any, path: str) -> None:
        if isinstance(node, Mapping):
            for key, child in node.items():
                key_ref = str(key)
                child_path = f"{path}.{key_ref}" if path else key_ref
                if key_ref in P7_R49_NO_BODY_LEAK_GUARD_MARKER_FALSE_KEY_REFS and child is True:
                    paths.append(child_path)
                walk(child, child_path)
        elif isinstance(node, Sequence) and not isinstance(node, (str, bytes, bytearray)):
            for index, child in enumerate(node):
                walk(child, f"{path}[{index}]")

    walk(value, source)
    return paths


def _r49_compact_r14_r15_p6_p8_candidate_handoff_reference() -> dict[str, Any]:
    return {
        "schema_version": P7_R49_R14_R15_P6_P8_CANDIDATE_HANDOFF_FREEZE_SCHEMA_VERSION,
        "material_id": "p7_r49_r14_r15_p6_p8_candidate_handoff_reference_bodyfree",
        "review_session_id": P7_R49_DEFAULT_REVIEW_SESSION_ID,
        "p5_human_blind_qa_confirmed_candidate": False,
        "p6_limited_human_readfeel_start_allowed_candidate": False,
        "p8_question_design_material_candidate": False,
        "body_free": True,
        "body_removed": True,
        "reviewer_free_text_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
    }


def build_p7_r49_no_body_leak_no_question_text_guard(
    *,
    r49_r14_r15_p6_p8_candidate_handoff_freeze: Mapping[str, Any] | None = None,
    r14_r15_p6_p8_candidate_handoff_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r49_no_body_leak_no_question_text_guard",
) -> dict[str, Any]:
    """Build the R49-16 guard that refuses body-full/question-text leakage."""

    if r49_r14_r15_p6_p8_candidate_handoff_freeze is not None and r14_r15_p6_p8_candidate_handoff_freeze is not None:
        raise ValueError("provide only one R49 R14/R15 freeze value")
    r15_freeze = (
        safe_mapping(r49_r14_r15_p6_p8_candidate_handoff_freeze)
        if r49_r14_r15_p6_p8_candidate_handoff_freeze is not None
        else safe_mapping(r14_r15_p6_p8_candidate_handoff_freeze)
        if r14_r15_p6_p8_candidate_handoff_freeze is not None
        else _r49_compact_r14_r15_p6_p8_candidate_handoff_reference()
    )

    forbidden_paths = _r49_forbidden_path_refs(r15_freeze, source="r49_r14_r15_p6_p8_candidate_handoff_freeze")
    marker_true_paths = _r49_marker_true_path_refs(r15_freeze, source="r49_r14_r15_p6_p8_candidate_handoff_freeze")
    if forbidden_paths or marker_true_paths:
        raise ValueError(
            "R49-16 detected body-full, reviewer-free-text, local-path/hash, "
            f"terminal-output, or question-text leakage; forbidden_paths={forbidden_paths[:4]} "
            f"marker_true_paths={marker_true_paths[:4]}"
        )

    guard = {
        **_false_flags(),
        "schema_version": P7_R49_NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R49_STEP,
        "scope": P7_R49_SCOPE,
        "policy_kind": P7_R49_POLICY_KIND,
        "policy_section": "R49-16_no_body_leak_no_question_text_guard",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r49_no_body_leak_no_question_text_guard", max_length=160),
        "review_session_id": clean_identifier(r15_freeze.get("review_session_id"), default=P7_R49_DEFAULT_REVIEW_SESSION_ID, max_length=160),
        "review_kind": P7_R49_REVIEW_KIND,
        "packet_kind": P7_R49_PACKET_KIND,
        "r15_p6_p8_candidate_handoff_freeze_schema_version": P7_R49_R14_R15_P6_P8_CANDIDATE_HANDOFF_FREEZE_SCHEMA_VERSION,
        "r15_p6_p8_candidate_handoff_freeze_ref": clean_identifier(r15_freeze.get("material_id"), default="p7_r49_r14_r15_p6_p8_candidate_handoff_freeze", max_length=160),
        "material_scanned_refs": [
                    "r14_p6_limited_human_readfeel_start_candidate_handoff",
            "r15_p8_question_design_material_candidate_handoff",
            "r49_public_no_touch_contract",
            "body_free_markers",
        ],
        "forbidden_field_refs": list(P7_R49_BODY_FREE_FORBIDDEN_FIELD_REFS),
        "question_text_forbidden_field_refs": list(P7_R49_QUESTION_TEXT_FORBIDDEN_FIELD_REFS),
        "guard_marker_false_key_refs": list(P7_R49_NO_BODY_LEAK_GUARD_MARKER_FALSE_KEY_REFS),
        "forbidden_key_path_refs": [],
        "forbidden_key_count": 0,
        "forbidden_marker_true_path_refs": [],
        "forbidden_marker_true_count": 0,
        "body_free_material_guard_passed": True,
        "no_body_leak_guard_passed": True,
        "no_question_text_guard_passed": True,
        "no_reviewer_free_text_guard_passed": True,
        "no_local_path_or_hash_guard_passed": True,
        "no_terminal_output_traceback_guard_passed": True,
        "question_text_included": False,
        "draft_question_text_included": False,
        "reviewer_free_text_included": False,
        "raw_input_or_comment_text_included": False,
        "returned_surface_included": False,
        "local_path_or_body_hash_included": False,
        "question_trigger_logic_implemented_here": False,
        "api_db_rn_response_key_changed_here": False,
        "body_full_material_leak_detected": False,
        "question_text_leak_detected": False,
        "reviewer_free_text_leak_detected": False,
        "local_path_or_hash_leak_detected": False,
        "terminal_output_or_traceback_leak_detected": False,
        "p5_human_blind_qa_confirmed_candidate": r15_freeze.get("p5_human_blind_qa_confirmed_candidate") is True,
        "p6_limited_human_readfeel_start_allowed_candidate": r15_freeze.get("p6_limited_human_readfeel_start_allowed_candidate") is True,
        "p8_question_design_material_candidate": r15_freeze.get("p8_question_design_material_candidate") is True,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "p8_detail_design_allowed_here": False,
        "p8_implementation_spec_finalized_here": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "actual_human_review_run_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_question_need_observation_summary_materialized_here": False,
        "actual_disposal_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "implemented_steps": list(P7_R49_R16_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R49_R16_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R49_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R49_R16_NEXT_REQUIRED_STEP_REF,
        "r0_current_source_r48_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_r48_case_matrix_handoff_validated": True,
        "r3_local_only_actual_packet_generation_preflight_done": True,
        "r4_actual_review_session_protocol_built": True,
        "r5_rating_row_ingestion_r48_normalizer_connected": True,
        "r6_blocker_execution_blocker_ingestion_connected": True,
        "r7_question_need_observation_row_schema_enum_fixed": True,
        "r8_question_need_observation_row_normalizer_connected": True,
        "r9_rating_question_observation_consistency_guard_connected": True,
        "r10_question_need_observation_summary_built": True,
        "r11_disposal_receipt_connection_fixed": True,
        "r12_review_handoff_summary_built": True,
        "r13_p5_confirmed_candidate_gate_connected": True,
        "r14_p6_limited_human_readfeel_start_candidate_handoff_built": True,
        "r15_p8_question_design_material_candidate_handoff_built": True,
        "r16_no_body_leak_no_question_text_guard_built": True,
        "public_contract": public_contract_flags(),
        "r49_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r49_no_body_leak_no_question_text_guard_contract(guard)
    return guard


def _r49_command_row(
    *,
    command_group_ref: str,
    command: str,
    required_for_r49_acceptance: bool,
    optional: bool = False,
    claim_boundary_ref: str,
) -> dict[str, Any]:
    return {
        "command_group_ref": command_group_ref,
        "command": command,
        "required_for_r49_acceptance": required_for_r49_acceptance,
        "optional": optional,
        "claim_boundary_ref": claim_boundary_ref,
        "commands_executed_here": False,
        "command_output_stored_here": False,
        "terminal_output_stored_here": False,
        "body_free": True,
    }


def _r49_validation_command_rows() -> list[dict[str, Any]]:
    r49_targets = " ".join(P7_R49_VALIDATION_R49_TARGET_TEST_FILE_REFS)
    r48_targets = " ".join(P7_R49_VALIDATION_R48_REGRESSION_TEST_FILE_REFS)
    r47_targets = " ".join(P7_R49_VALIDATION_R47_REGRESSION_TEST_FILE_REFS)
    r46_targets = " ".join(P7_R49_VALIDATION_R46_HANDOFF_TEST_FILE_REFS)
    display_api = " ".join(P7_R49_VALIDATION_DISPLAY_API_TEST_FILE_REFS)
    p5_core = " ".join(P7_R49_VALIDATION_P5_CORE_TEST_FILE_REFS)
    return [
        _r49_command_row(
            command_group_ref="syntax_import",
            command="PYTHONPATH=services/ai_inference python -m py_compile services/ai_inference/emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution.py",
            required_for_r49_acceptance=True,
            claim_boundary_ref="syntax/import only; not product readfeel confirmation",
        ),
        _r49_command_row(
            command_group_ref="r49_target",
            command=f"PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q {r49_targets}",
            required_for_r49_acceptance=True,
            claim_boundary_ref="R49 helper contract only; not actual human review execution",
        ),
        _r49_command_row(
            command_group_ref="r48_regression",
            command=f"PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q {r48_targets}",
            required_for_r49_acceptance=True,
            claim_boundary_ref="R48 packet footing regression only; not P5 confirmed",
        ),
        _r49_command_row(
            command_group_ref="r47_regression",
            command=f"PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q {r47_targets}",
            required_for_r49_acceptance=True,
            claim_boundary_ref="local-only/body-free policy regression only",
        ),
        _r49_command_row(
            command_group_ref="r46_handoff_regression",
            command=f"PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q {r46_targets}",
            required_for_r49_acceptance=True,
            claim_boundary_ref="P5/P6 handoff regression only; not P6 start permission",
        ),
        _r49_command_row(
            command_group_ref="display_api_contract",
            command=f"PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q {display_api}",
            required_for_r49_acceptance=True,
            claim_boundary_ref="display/API contract only; not real-device modal readfeel",
        ),
        _r49_command_row(
            command_group_ref="p5_core_subset",
            command=f"PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q {p5_core}",
            required_for_r49_acceptance=True,
            claim_boundary_ref="P5 core subset only; not human blind QA confirmed",
        ),
        _r49_command_row(
            command_group_ref="p6_subset_optional",
            command="PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q tests/test_emlis_ai_structure_insight*.py",
            required_for_r49_acceptance=False,
            optional=True,
            claim_boundary_ref="optional P6 subset only; not P6 limited human readfeel start permission",
        ),
        _r49_command_row(
            command_group_ref="backend_collect_only",
            command="PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest --collect-only -q",
            required_for_r49_acceptance=True,
            claim_boundary_ref="collect-only only; not full backend suite execution green",
        ),
        _r49_command_row(
            command_group_ref="rn_no_touch_optional",
            command="cd ../Cocolon && npm run test:rn-screens --silent",
            required_for_r49_acceptance=False,
            optional=True,
            claim_boundary_ref="RN no-touch optional check only; not real-device modal readfeel",
        ),
    ]


def build_p7_r49_validation_command_matrix(
    *,
    r49_no_body_leak_no_question_text_guard: Mapping[str, Any] | None = None,
    no_body_leak_no_question_text_guard: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r49_validation_command_matrix",
) -> dict[str, Any]:
    """Build the R49-17 validation matrix without executing any command."""

    if r49_no_body_leak_no_question_text_guard is not None and no_body_leak_no_question_text_guard is not None:
        raise ValueError("provide only one R49 R16 no-body-leak guard value")
    guard = (
        safe_mapping(r49_no_body_leak_no_question_text_guard)
        if r49_no_body_leak_no_question_text_guard is not None
        else safe_mapping(no_body_leak_no_question_text_guard)
        if no_body_leak_no_question_text_guard is not None
        else build_p7_r49_no_body_leak_no_question_text_guard()
    )
    assert_p7_r49_no_body_leak_no_question_text_guard_contract(guard)
    rows = _r49_validation_command_rows()
    matrix = {
        **_false_flags(),
        "schema_version": P7_R49_VALIDATION_COMMAND_MATRIX_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R49_STEP,
        "scope": P7_R49_SCOPE,
        "policy_kind": P7_R49_POLICY_KIND,
        "policy_section": "R49-17_validation_command_matrix",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r49_validation_command_matrix", max_length=160),
        "review_session_id": clean_identifier(guard.get("review_session_id"), default=P7_R49_DEFAULT_REVIEW_SESSION_ID, max_length=160),
        "review_kind": P7_R49_REVIEW_KIND,
        "packet_kind": P7_R49_PACKET_KIND,
        "r16_no_body_leak_no_question_text_guard_schema_version": P7_R49_NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_SCHEMA_VERSION,
        "r16_no_body_leak_no_question_text_guard_ref": clean_identifier(guard.get("material_id"), default="p7_r49_no_body_leak_no_question_text_guard", max_length=160),
        "validation_command_group_refs": list(P7_R49_VALIDATION_COMMAND_GROUP_REFS),
        "validation_command_matrix_rows": rows,
        "validation_command_count": len(rows),
        "r49_target_test_file_refs": list(P7_R49_VALIDATION_R49_TARGET_TEST_FILE_REFS),
        "r48_regression_test_file_refs": list(P7_R49_VALIDATION_R48_REGRESSION_TEST_FILE_REFS),
        "r47_regression_test_file_refs": list(P7_R49_VALIDATION_R47_REGRESSION_TEST_FILE_REFS),
        "r46_handoff_regression_test_file_refs": list(P7_R49_VALIDATION_R46_HANDOFF_TEST_FILE_REFS),
        "display_api_contract_test_file_refs": list(P7_R49_VALIDATION_DISPLAY_API_TEST_FILE_REFS),
        "p5_core_test_file_refs": list(P7_R49_VALIDATION_P5_CORE_TEST_FILE_REFS),
        "p6_subset_optional_command_ref": "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q tests/test_emlis_ai_structure_insight*.py",
        "backend_collect_only_command_ref": "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest --collect-only -q",
        "rn_no_touch_optional_command_ref": "cd ../Cocolon && npm run test:rn-screens --silent",
        "syntax_import_required": True,
        "r49_target_required": True,
        "r48_regression_required": True,
        "r47_regression_required": True,
        "r46_handoff_regression_required": True,
        "display_api_contract_required": True,
        "p5_core_required": True,
        "p6_subset_optional": True,
        "backend_collect_only_required": True,
        "rn_no_touch_optional": True,
        "validation_commands_reference_only": True,
        "validation_commands_executed_here": False,
        "command_output_stored_here": False,
        "terminal_output_stored_here": False,
        "full_backend_suite_execution_claimed_here": False,
        "collect_only_claimed_as_full_backend_green": False,
        "rn_contract_claimed_as_real_device_modal_readfeel": False,
        "release_readiness_claim_allowed": False,
        "p5_human_blind_qa_confirmed_candidate": guard.get("p5_human_blind_qa_confirmed_candidate") is True,
        "p6_limited_human_readfeel_start_allowed_candidate": guard.get("p6_limited_human_readfeel_start_allowed_candidate") is True,
        "p8_question_design_material_candidate": guard.get("p8_question_design_material_candidate") is True,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "implemented_steps": list(P7_R49_R17_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R49_R17_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R49_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R49_R17_NEXT_REQUIRED_STEP_REF,
        "r0_current_source_r48_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_r48_case_matrix_handoff_validated": True,
        "r3_local_only_actual_packet_generation_preflight_done": True,
        "r4_actual_review_session_protocol_built": True,
        "r5_rating_row_ingestion_r48_normalizer_connected": True,
        "r6_blocker_execution_blocker_ingestion_connected": True,
        "r7_question_need_observation_row_schema_enum_fixed": True,
        "r8_question_need_observation_row_normalizer_connected": True,
        "r9_rating_question_observation_consistency_guard_connected": True,
        "r10_question_need_observation_summary_built": True,
        "r11_disposal_receipt_connection_fixed": True,
        "r12_review_handoff_summary_built": True,
        "r13_p5_confirmed_candidate_gate_connected": True,
        "r14_p6_limited_human_readfeel_start_candidate_handoff_built": True,
        "r15_p8_question_design_material_candidate_handoff_built": True,
        "r16_no_body_leak_no_question_text_guard_built": True,
        "r17_validation_command_matrix_built": True,
        "public_contract": public_contract_flags(),
        "r49_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r49_validation_command_matrix_contract(matrix)
    return matrix


def build_p7_r49_r16_r17_no_body_leak_validation_command_matrix_freeze(
    *,
    r49_no_body_leak_no_question_text_guard: Mapping[str, Any] | None = None,
    r49_validation_command_matrix: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r49_r16_r17_no_body_leak_validation_command_matrix_freeze",
) -> dict[str, Any]:
    """Combine R49-16 and R49-17 without expanding into R18/no-touch freeze."""

    guard = (
        safe_mapping(r49_no_body_leak_no_question_text_guard)
        if r49_no_body_leak_no_question_text_guard is not None
        else build_p7_r49_no_body_leak_no_question_text_guard()
    )
    assert_p7_r49_no_body_leak_no_question_text_guard_contract(guard)
    matrix = (
        safe_mapping(r49_validation_command_matrix)
        if r49_validation_command_matrix is not None
        else build_p7_r49_validation_command_matrix(r49_no_body_leak_no_question_text_guard=guard)
    )
    assert_p7_r49_validation_command_matrix_contract(matrix)
    if guard.get("review_session_id") != matrix.get("review_session_id"):
        raise ValueError("R49 R16/R17 freeze requires matching review_session_id")
    freeze = {
        **_false_flags(),
        "schema_version": P7_R49_R16_R17_NO_BODY_LEAK_VALIDATION_COMMAND_MATRIX_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R49_STEP,
        "scope": P7_R49_SCOPE,
        "policy_kind": P7_R49_POLICY_KIND,
        "policy_section": "R49-16_R49-17_no_body_leak_validation_command_matrix_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r49_r16_r17_no_body_leak_validation_command_matrix_freeze", max_length=160),
        "review_session_id": clean_identifier(guard.get("review_session_id"), default=P7_R49_DEFAULT_REVIEW_SESSION_ID, max_length=160),
        "review_kind": P7_R49_REVIEW_KIND,
        "packet_kind": P7_R49_PACKET_KIND,
        "r16_no_body_leak_no_question_text_guard_schema_version": P7_R49_NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_SCHEMA_VERSION,
        "r16_no_body_leak_no_question_text_guard_ref": clean_identifier(guard.get("material_id"), default="p7_r49_no_body_leak_no_question_text_guard", max_length=160),
        "r17_validation_command_matrix_schema_version": P7_R49_VALIDATION_COMMAND_MATRIX_SCHEMA_VERSION,
        "r17_validation_command_matrix_ref": clean_identifier(matrix.get("material_id"), default="p7_r49_validation_command_matrix", max_length=160),
        "implemented_steps": list(P7_R49_R17_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R49_R17_NOT_YET_IMPLEMENTED_STEPS),
        "body_free_material_guard_passed": guard.get("body_free_material_guard_passed") is True,
        "validation_command_matrix_built": True,
        "validation_commands_executed_here": False,
        "command_output_stored_here": False,
        "terminal_output_stored_here": False,
        "p5_human_blind_qa_confirmed_candidate": guard.get("p5_human_blind_qa_confirmed_candidate") is True,
        "p6_limited_human_readfeel_start_allowed_candidate": guard.get("p6_limited_human_readfeel_start_allowed_candidate") is True,
        "p8_question_design_material_candidate": guard.get("p8_question_design_material_candidate") is True,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "first_next_work_ref": P7_R49_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R49_R17_NEXT_REQUIRED_STEP_REF,
        "r0_current_source_r48_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_r48_case_matrix_handoff_validated": True,
        "r3_local_only_actual_packet_generation_preflight_done": True,
        "r4_actual_review_session_protocol_built": True,
        "r5_rating_row_ingestion_r48_normalizer_connected": True,
        "r6_blocker_execution_blocker_ingestion_connected": True,
        "r7_question_need_observation_row_schema_enum_fixed": True,
        "r8_question_need_observation_row_normalizer_connected": True,
        "r9_rating_question_observation_consistency_guard_connected": True,
        "r10_question_need_observation_summary_built": True,
        "r11_disposal_receipt_connection_fixed": True,
        "r12_review_handoff_summary_built": True,
        "r13_p5_confirmed_candidate_gate_connected": True,
        "r14_p6_limited_human_readfeel_start_candidate_handoff_built": True,
        "r15_p8_question_design_material_candidate_handoff_built": True,
        "r16_no_body_leak_no_question_text_guard_built": True,
        "r17_validation_command_matrix_built": True,
        "public_contract": public_contract_flags(),
        "r49_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r49_r16_r17_no_body_leak_validation_command_matrix_freeze_contract(freeze)
    return freeze


def assert_p7_r49_no_body_leak_no_question_text_guard_contract(guard: Mapping[str, Any]) -> bool:
    data = safe_mapping(guard)
    _assert_required_fields(
        data,
        required=P7_R49_NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_REQUIRED_FIELD_REFS,
        source="p7_r49_no_body_leak_no_question_text_guard",
    )
    _assert_common(
        data,
        schema_version=P7_R49_NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_SCHEMA_VERSION,
        source="p7_r49_no_body_leak_no_question_text_guard",
        allowed_true_keys=(
            "p5_human_blind_qa_confirmed_candidate",
            "p6_limited_human_readfeel_start_allowed_candidate",
            "p8_question_design_material_candidate",
        ),
    )
    if data.get("policy_section") != "R49-16_no_body_leak_no_question_text_guard":
        raise ValueError("R49 R16 policy section changed")
    if data.get("forbidden_key_path_refs") != [] or data.get("forbidden_key_count") != 0:
        raise ValueError("R49 R16 must not materialize forbidden-key paths in a passing guard")
    if data.get("forbidden_marker_true_path_refs") != [] or data.get("forbidden_marker_true_count") != 0:
        raise ValueError("R49 R16 must not materialize marker-true paths in a passing guard")
    for true_key in (
        "body_free_material_guard_passed",
        "no_body_leak_guard_passed",
        "no_question_text_guard_passed",
        "no_reviewer_free_text_guard_passed",
        "no_local_path_or_hash_guard_passed",
        "no_terminal_output_traceback_guard_passed",
        "r16_no_body_leak_no_question_text_guard_built",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R49 R16 guard must keep {true_key}=True")
    for false_key in (
        "question_text_included",
        "draft_question_text_included",
        "reviewer_free_text_included",
        "raw_input_or_comment_text_included",
        "returned_surface_included",
        "local_path_or_body_hash_included",
        "question_trigger_logic_implemented_here",
        "api_db_rn_response_key_changed_here",
        "body_full_material_leak_detected",
        "question_text_leak_detected",
        "reviewer_free_text_leak_detected",
        "local_path_or_hash_leak_detected",
        "terminal_output_or_traceback_leak_detected",
        "p6_limited_human_readfeel_start_allowed",
        "p6_limited_human_readfeel_confirmed",
        "p8_detail_design_allowed_here",
        "p8_implementation_spec_finalized_here",
        "p7_complete",
        "p8_start_allowed",
        "release_allowed",
        "actual_human_review_run_here",
        "actual_body_full_packet_generated_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_question_need_observation_summary_materialized_here",
        "actual_disposal_run_here",
        "actual_disposal_receipt_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R49 R16 guard must keep {false_key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R49_R16_IMPLEMENTED_STEPS:
        raise ValueError("R49 R16 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R49_R16_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R49 R16 not-yet steps changed")
    if data.get("next_required_step") != P7_R49_R16_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R49 R16 must point to R49-17 next")
    _assert_r49_body_free(data, source="p7_r49_no_body_leak_no_question_text_guard")
    return True


def assert_p7_r49_validation_command_matrix_contract(matrix: Mapping[str, Any]) -> bool:
    data = safe_mapping(matrix)
    _assert_required_fields(
        data,
        required=P7_R49_VALIDATION_COMMAND_MATRIX_REQUIRED_FIELD_REFS,
        source="p7_r49_validation_command_matrix",
    )
    _assert_common(
        data,
        schema_version=P7_R49_VALIDATION_COMMAND_MATRIX_SCHEMA_VERSION,
        source="p7_r49_validation_command_matrix",
        allowed_true_keys=(
            "p5_human_blind_qa_confirmed_candidate",
            "p6_limited_human_readfeel_start_allowed_candidate",
            "p8_question_design_material_candidate",
        ),
    )
    if data.get("policy_section") != "R49-17_validation_command_matrix":
        raise ValueError("R49 R17 policy section changed")
    rows = list(data.get("validation_command_matrix_rows") or [])
    if len(rows) != len(P7_R49_VALIDATION_COMMAND_GROUP_REFS):
        raise ValueError("R49 R17 validation command row count changed")
    if [row.get("command_group_ref") for row in rows] != list(P7_R49_VALIDATION_COMMAND_GROUP_REFS):
        raise ValueError("R49 R17 validation command group order changed")
    if data.get("validation_command_count") != len(rows):
        raise ValueError("R49 R17 validation command count mismatch")
    for row in rows:
        row_map = safe_mapping(row)
        if row_map.get("commands_executed_here") is not False:
            raise ValueError("R49 R17 command rows must not execute commands")
        if row_map.get("command_output_stored_here") is not False or row_map.get("terminal_output_stored_here") is not False:
            raise ValueError("R49 R17 command rows must not store command output")
        if row_map.get("body_free") is not True:
            raise ValueError("R49 R17 command rows must be body_free")
    if tuple(data.get("r49_target_test_file_refs") or ()) != P7_R49_VALIDATION_R49_TARGET_TEST_FILE_REFS:
        raise ValueError("R49 R17 target test refs changed")
    if tuple(data.get("r48_regression_test_file_refs") or ()) != P7_R49_VALIDATION_R48_REGRESSION_TEST_FILE_REFS:
        raise ValueError("R49 R17 R48 regression refs changed")
    if tuple(data.get("r47_regression_test_file_refs") or ()) != P7_R49_VALIDATION_R47_REGRESSION_TEST_FILE_REFS:
        raise ValueError("R49 R17 R47 regression refs changed")
    if tuple(data.get("r46_handoff_regression_test_file_refs") or ()) != P7_R49_VALIDATION_R46_HANDOFF_TEST_FILE_REFS:
        raise ValueError("R49 R17 R46 regression refs changed")
    for true_key in (
        "syntax_import_required",
        "r49_target_required",
        "r48_regression_required",
        "r47_regression_required",
        "r46_handoff_regression_required",
        "display_api_contract_required",
        "p5_core_required",
        "backend_collect_only_required",
        "p6_subset_optional",
        "rn_no_touch_optional",
        "validation_commands_reference_only",
        "r16_no_body_leak_no_question_text_guard_built",
        "r17_validation_command_matrix_built",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R49 R17 matrix must keep {true_key}=True")
    for false_key in (
        "validation_commands_executed_here",
        "command_output_stored_here",
        "terminal_output_stored_here",
        "full_backend_suite_execution_claimed_here",
        "collect_only_claimed_as_full_backend_green",
        "rn_contract_claimed_as_real_device_modal_readfeel",
        "release_readiness_claim_allowed",
        "p5_human_blind_qa_confirmed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_limited_human_readfeel_confirmed",
        "p7_complete",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R49 R17 matrix must keep {false_key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R49_R17_IMPLEMENTED_STEPS:
        raise ValueError("R49 R17 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R49_R17_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R49 R17 not-yet steps changed")
    if data.get("next_required_step") != P7_R49_R17_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R49 R17 must point to R49-18 next")
    _assert_r49_body_free(data, source="p7_r49_validation_command_matrix")
    return True


def assert_p7_r49_r16_r17_no_body_leak_validation_command_matrix_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_required_fields(
        data,
        required=P7_R49_R16_R17_NO_BODY_LEAK_VALIDATION_COMMAND_MATRIX_FREEZE_REQUIRED_FIELD_REFS,
        source="p7_r49_r16_r17_no_body_leak_validation_command_matrix_freeze",
    )
    _assert_common(
        data,
        schema_version=P7_R49_R16_R17_NO_BODY_LEAK_VALIDATION_COMMAND_MATRIX_FREEZE_SCHEMA_VERSION,
        source="p7_r49_r16_r17_no_body_leak_validation_command_matrix_freeze",
        allowed_true_keys=(
            "p5_human_blind_qa_confirmed_candidate",
            "p6_limited_human_readfeel_start_allowed_candidate",
            "p8_question_design_material_candidate",
        ),
    )
    if data.get("policy_section") != "R49-16_R49-17_no_body_leak_validation_command_matrix_freeze":
        raise ValueError("R49 R16/R17 freeze policy section changed")
    if data.get("body_free_material_guard_passed") is not True:
        raise ValueError("R49 R16/R17 freeze requires passing body-free guard")
    if data.get("validation_command_matrix_built") is not True:
        raise ValueError("R49 R16/R17 freeze requires validation matrix")
    for false_key in (
        "validation_commands_executed_here",
        "command_output_stored_here",
        "terminal_output_stored_here",
        "p6_limited_human_readfeel_start_allowed",
        "p6_limited_human_readfeel_confirmed",
        "p7_complete",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R49 R16/R17 freeze must keep {false_key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R49_R17_IMPLEMENTED_STEPS:
        raise ValueError("R49 R16/R17 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R49_R17_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R49 R16/R17 not-yet steps changed")
    if data.get("next_required_step") != P7_R49_R17_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R49 R16/R17 must point to R49-18 next")
    _assert_r49_body_free(data, source="p7_r49_r16_r17_no_body_leak_validation_command_matrix_freeze")
    return True


def build_p7_r49_touch_candidate_no_touch_boundary_freeze(
    *,
    r16_r17_no_body_leak_validation_command_matrix_freeze: Mapping[str, Any] | None = None,
    r49_r16_r17_no_body_leak_validation_command_matrix_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r49_touch_candidate_no_touch_boundary_freeze",
) -> dict[str, Any]:
    """Build the R49-18 body-free touch-candidate/no-touch boundary freeze.

    This fixes the files R49 may touch and the files/areas that remain no-touch.
    It does not inspect git, materialize a touched-file scan, execute validation
    commands, start P5 review, start P8, or claim release readiness.
    """

    if (
        r16_r17_no_body_leak_validation_command_matrix_freeze is not None
        and r49_r16_r17_no_body_leak_validation_command_matrix_freeze is not None
    ):
        raise ValueError("provide only one R49 R16/R17 freeze value")
    r17 = (
        safe_mapping(r49_r16_r17_no_body_leak_validation_command_matrix_freeze)
        if r49_r16_r17_no_body_leak_validation_command_matrix_freeze is not None
        else safe_mapping(r16_r17_no_body_leak_validation_command_matrix_freeze)
        if r16_r17_no_body_leak_validation_command_matrix_freeze is not None
        else build_p7_r49_r16_r17_no_body_leak_validation_command_matrix_freeze()
    )
    assert_p7_r49_r16_r17_no_body_leak_validation_command_matrix_freeze_contract(r17)

    freeze = {
        **_false_flags(),
        "schema_version": P7_R49_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R49_STEP,
        "scope": P7_R49_SCOPE,
        "policy_kind": P7_R49_POLICY_KIND,
        "policy_section": "R49-18_touch_candidate_no_touch_boundary_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r49_touch_candidate_no_touch_boundary_freeze", max_length=160),
        "review_session_id": clean_identifier(r17.get("review_session_id"), default=P7_R49_DEFAULT_REVIEW_SESSION_ID, max_length=160),
        "review_kind": P7_R49_REVIEW_KIND,
        "packet_kind": P7_R49_PACKET_KIND,
        "r16_r17_no_body_leak_validation_command_matrix_freeze_schema_version": P7_R49_R16_R17_NO_BODY_LEAK_VALIDATION_COMMAND_MATRIX_FREEZE_SCHEMA_VERSION,
        "r16_r17_no_body_leak_validation_command_matrix_freeze_ref": clean_identifier(
            r17.get("material_id"),
            default="p7_r49_r16_r17_no_body_leak_validation_command_matrix_freeze",
            max_length=160,
        ),
        "touch_boundary_freeze_required": True,
        "production_touch_candidate_file_refs": list(P7_R49_PRODUCTION_TOUCH_CANDIDATE_FILE_REFS),
        "optional_touch_candidate_file_refs": list(P7_R49_OPTIONAL_TOUCH_CANDIDATE_FILE_REFS),
        "test_touch_candidate_file_refs": list(P7_R49_VALIDATION_R49_TARGET_TEST_FILE_REFS),
        "allowed_production_file_refs": list(P7_R49_ALLOWED_PRODUCTION_TOUCH_FILE_REFS),
        "allowed_test_file_refs": list(P7_R49_ALLOWED_TEST_TOUCH_FILE_REFS),
        "allowed_actual_touched_file_refs": list(P7_R49_ALLOWED_ACTUAL_TOUCHED_FILE_REFS),
        "explicit_no_touch_file_refs": list(P7_R49_EXPLICIT_NO_TOUCH_FILE_REFS),
        "explicit_no_touch_area_refs": list(P7_R49_EXPLICIT_NO_TOUCH_AREA_REFS),
        "forbidden_actual_touched_file_refs": list(P7_R49_EXPLICIT_NO_TOUCH_FILE_REFS),
        "current_patch_expected_touched_file_refs": list(P7_R49_R18_CURRENT_PATCH_EXPECTED_TOUCHED_FILE_REFS),
        "actual_touched_file_refs_checked_here": False,
        "actual_touched_file_refs_verified_here": False,
        "actual_touched_file_refs_materialized_here": False,
        "forbidden_actual_touched_refs_detected_here": False,
        "touch_candidate_boundary_frozen": True,
        "no_touch_boundary_frozen": True,
        "forbidden_actual_touched_refs_rejected": True,
        "no_touch_refs_must_remain_untouched": True,
        "allowed_refs_do_not_include_no_touch_refs": True,
        "production_touch_candidate_is_r49_helper_only": True,
        "optional_touch_candidate_is_local_file_ops_only": True,
        "test_touch_candidate_is_r49_target_only": True,
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
        "question_response_key_added": False,
        "question_text_implemented_here": False,
        "draft_question_text_implemented_here": False,
        "validation_commands_executed_here": False,
        "command_output_stored_here": False,
        "terminal_output_stored_here": False,
        "p5_human_blind_qa_confirmed_candidate": r17.get("p5_human_blind_qa_confirmed_candidate") is True,
        "p6_limited_human_readfeel_start_allowed_candidate": r17.get("p6_limited_human_readfeel_start_allowed_candidate") is True,
        "p8_question_design_material_candidate": r17.get("p8_question_design_material_candidate") is True,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "p8_detail_design_allowed_here": False,
        "p8_implementation_spec_finalized_here": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "actual_human_review_run_here": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "local_reviewer_payload_materialized_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_question_need_observation_summary_materialized_here": False,
        "actual_disposal_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "implemented_steps": list(P7_R49_R18_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R49_R18_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R49_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R49_R18_NEXT_REQUIRED_STEP_REF,
        "post_r18_next_work_ref": P7_R49_R18_POST_FREEZE_NEXT_WORK_REF,
        "r0_current_source_r48_handoff_bridge_refrozen": True,
        "r1_scope_schema_status_enum_fixed": True,
        "r2_r48_case_matrix_handoff_validated": True,
        "r3_local_only_actual_packet_generation_preflight_done": True,
        "r4_actual_review_session_protocol_built": True,
        "r5_rating_row_ingestion_r48_normalizer_connected": True,
        "r6_blocker_execution_blocker_ingestion_connected": True,
        "r7_question_need_observation_row_schema_enum_fixed": True,
        "r8_question_need_observation_row_normalizer_connected": True,
        "r9_rating_question_observation_consistency_guard_connected": True,
        "r10_question_need_observation_summary_built": True,
        "r11_disposal_receipt_connection_fixed": True,
        "r12_review_handoff_summary_built": True,
        "r13_p5_confirmed_candidate_gate_connected": True,
        "r14_p6_limited_human_readfeel_start_candidate_handoff_built": True,
        "r15_p8_question_design_material_candidate_handoff_built": True,
        "r16_no_body_leak_no_question_text_guard_built": True,
        "r17_validation_command_matrix_built": True,
        "r18_touch_candidate_no_touch_boundary_frozen": True,
        "public_contract": public_contract_flags(),
        "r49_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r49_touch_candidate_no_touch_boundary_freeze_contract(freeze)
    return freeze


def assert_p7_r49_touch_candidate_no_touch_boundary_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    if set(data) != set(P7_R49_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS):
        raise ValueError("R49 R18 touch/no-touch boundary fields must exactly match the body-free schema")
    _assert_common(
        data,
        schema_version=P7_R49_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION,
        source="p7_r49_touch_candidate_no_touch_boundary_freeze",
        allowed_true_keys=(
            "p5_human_blind_qa_confirmed_candidate",
            "p6_limited_human_readfeel_start_allowed_candidate",
            "p8_question_design_material_candidate",
        ),
    )
    if data.get("policy_section") != "R49-18_touch_candidate_no_touch_boundary_freeze":
        raise ValueError("R49 R18 policy section changed")
    if data.get("touch_boundary_freeze_required") is not True:
        raise ValueError("R49 R18 must require touch/no-touch boundary freeze")
    if tuple(data.get("production_touch_candidate_file_refs") or ()) != P7_R49_PRODUCTION_TOUCH_CANDIDATE_FILE_REFS:
        raise ValueError("R49 R18 production touch candidate refs changed")
    if tuple(data.get("optional_touch_candidate_file_refs") or ()) != P7_R49_OPTIONAL_TOUCH_CANDIDATE_FILE_REFS:
        raise ValueError("R49 R18 optional touch candidate refs changed")
    if tuple(data.get("test_touch_candidate_file_refs") or ()) != P7_R49_VALIDATION_R49_TARGET_TEST_FILE_REFS:
        raise ValueError("R49 R18 test touch candidate refs changed")
    if tuple(data.get("allowed_production_file_refs") or ()) != P7_R49_ALLOWED_PRODUCTION_TOUCH_FILE_REFS:
        raise ValueError("R49 R18 allowed production refs changed")
    if tuple(data.get("allowed_test_file_refs") or ()) != P7_R49_ALLOWED_TEST_TOUCH_FILE_REFS:
        raise ValueError("R49 R18 allowed test refs changed")
    if tuple(data.get("allowed_actual_touched_file_refs") or ()) != P7_R49_ALLOWED_ACTUAL_TOUCHED_FILE_REFS:
        raise ValueError("R49 R18 allowed actual touched refs changed")
    if tuple(data.get("explicit_no_touch_file_refs") or ()) != P7_R49_EXPLICIT_NO_TOUCH_FILE_REFS:
        raise ValueError("R49 R18 explicit no-touch file refs changed")
    if tuple(data.get("explicit_no_touch_area_refs") or ()) != P7_R49_EXPLICIT_NO_TOUCH_AREA_REFS:
        raise ValueError("R49 R18 explicit no-touch areas changed")
    if tuple(data.get("forbidden_actual_touched_file_refs") or ()) != P7_R49_EXPLICIT_NO_TOUCH_FILE_REFS:
        raise ValueError("R49 R18 forbidden actual touched refs changed")
    if tuple(data.get("current_patch_expected_touched_file_refs") or ()) != P7_R49_R18_CURRENT_PATCH_EXPECTED_TOUCHED_FILE_REFS:
        raise ValueError("R49 R18 expected touched refs changed")

    allowed = set(data.get("allowed_actual_touched_file_refs") or ())
    no_touch = set(data.get("explicit_no_touch_file_refs") or ())
    expected_current = set(data.get("current_patch_expected_touched_file_refs") or ())
    if allowed & no_touch:
        raise ValueError("R49 R18 allowed refs must not overlap explicit no-touch refs")
    if not expected_current or not expected_current.issubset(allowed):
        raise ValueError("R49 R18 current patch expected touched refs must be allowed refs")
    if expected_current & no_touch:
        raise ValueError("R49 R18 current patch expected touched refs must not include no-touch refs")

    for true_key in (
        "touch_candidate_boundary_frozen",
        "no_touch_boundary_frozen",
        "forbidden_actual_touched_refs_rejected",
        "no_touch_refs_must_remain_untouched",
        "allowed_refs_do_not_include_no_touch_refs",
        "production_touch_candidate_is_r49_helper_only",
        "optional_touch_candidate_is_local_file_ops_only",
        "test_touch_candidate_is_r49_target_only",
        "r0_current_source_r48_handoff_bridge_refrozen",
        "r1_scope_schema_status_enum_fixed",
        "r2_r48_case_matrix_handoff_validated",
        "r3_local_only_actual_packet_generation_preflight_done",
        "r4_actual_review_session_protocol_built",
        "r5_rating_row_ingestion_r48_normalizer_connected",
        "r6_blocker_execution_blocker_ingestion_connected",
        "r7_question_need_observation_row_schema_enum_fixed",
        "r8_question_need_observation_row_normalizer_connected",
        "r9_rating_question_observation_consistency_guard_connected",
        "r10_question_need_observation_summary_built",
        "r11_disposal_receipt_connection_fixed",
        "r12_review_handoff_summary_built",
        "r13_p5_confirmed_candidate_gate_connected",
        "r14_p6_limited_human_readfeel_start_candidate_handoff_built",
        "r15_p8_question_design_material_candidate_handoff_built",
        "r16_no_body_leak_no_question_text_guard_built",
        "r17_validation_command_matrix_built",
        "r18_touch_candidate_no_touch_boundary_frozen",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R49 R18 boundary must keep {true_key}=True")

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
        "question_response_key_implemented",
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
        "actual_body_full_packet_generated_here",
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
            raise ValueError(f"R49 R18 boundary must keep {false_key}=False")

    if tuple(data.get("implemented_steps") or ()) != P7_R49_R18_IMPLEMENTED_STEPS:
        raise ValueError("R49 R18 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R49_R18_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R49 R18 not-yet steps changed")
    if data.get("next_required_step") != P7_R49_R18_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R49 R18 next required step changed")
    if data.get("post_r18_next_work_ref") != P7_R49_R18_POST_FREEZE_NEXT_WORK_REF:
        raise ValueError("R49 R18 post-freeze next work ref changed")
    _assert_r49_body_free(data, source="p7_r49_touch_candidate_no_touch_boundary_freeze")
    return True


def assert_p7_r49_touch_candidate_no_touch_actual_touched_file_refs_contract(
    actual_touched_file_refs: Sequence[str] | Any,
    *,
    touch_boundary_freeze: Mapping[str, Any] | None = None,
) -> bool:
    """Validate caller-provided touched refs against the R49 R18 boundary.

    This does not inspect git, write logs, materialize filesystem results, or
    turn the provided refs into an executed validation claim.
    """

    boundary = (
        safe_mapping(touch_boundary_freeze)
        if touch_boundary_freeze is not None
        else build_p7_r49_touch_candidate_no_touch_boundary_freeze()
    )
    assert_p7_r49_touch_candidate_no_touch_boundary_freeze_contract(boundary)
    touched_refs = tuple(dedupe_identifiers(actual_touched_file_refs, limit=200, max_length=240))
    if not touched_refs:
        raise ValueError("R49 R18 actual touched refs must be provided for boundary validation")
    allowed = set(boundary.get("allowed_actual_touched_file_refs") or ())
    no_touch = set(boundary.get("explicit_no_touch_file_refs") or ())
    forbidden = set(boundary.get("forbidden_actual_touched_file_refs") or ())
    touched_set = set(touched_refs)
    if touched_set & no_touch or touched_set & forbidden:
        raise ValueError("R49 R18 actual touched refs include explicit no-touch refs")
    not_allowed = sorted(touched_set - allowed)
    if not_allowed:
        raise ValueError(f"R49 R18 actual touched refs are outside allowed candidates: {not_allowed[:6]}")
    return True

__all__ = [
    "P7_R49_CURRENT_SOURCE_R48_HANDOFF_BRIDGE_REFREEZE_SCHEMA_VERSION",
    "P7_R49_REVIEW_SESSION_ENVELOPE_BODYFREE_SCHEMA_VERSION",
    "P7_R49_R0_R1_SCOPE_STATUS_FREEZE_SCHEMA_VERSION",
    "P7_R49_R0_R1_SCOPE_STATUS_ENUM_FREEZE_SCHEMA_VERSION",
    "P7_R49_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION",
    "P7_R49_QUESTION_NEED_OBSERVATION_SUMMARY_BODYFREE_SCHEMA_VERSION",
    "P7_R49_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION",
    "P7_R49_R48_CASE_MATRIX_HANDOFF_VALIDATION_SCHEMA_VERSION",
    "P7_R49_LOCAL_ONLY_ACTUAL_PACKET_GENERATION_PREFLIGHT_SCHEMA_VERSION",
    "P7_R49_R2_R3_CASE_MATRIX_PREFLIGHT_FREEZE_SCHEMA_VERSION",
    "P7_R49_STEP",
    "P7_R49_SCOPE",
    "P7_R49_POLICY_KIND",
    "P7_R49_PACKET_KIND",
    "P7_R49_REVIEW_KIND",
    "P7_R49_REQUIRED_TOTAL_CASES",
    "P7_R49_DEFAULT_REVIEW_SESSION_ID",
    "P7_R49_REVIEW_SESSION_DEFAULT_REF",
    "P7_R49_REVIEW_SESSION_STATUS_REFS",
    "P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS",
    "P7_R49_AMBIGUITY_KIND_REFS",
    "P7_R49_ONE_QUESTION_FIT_REFS",
    "P7_R49_REPAIR_REQUIRED_REF_REFS",
    "P7_R49_PLAN_CANDIDATE_FLAG_REFS",
    "P7_R49_EXECUTION_BLOCKER_ID_REFS",
    "P7_R49_LOCAL_ONLY_PREFLIGHT_STATUS_REFS",
    "P7_R49_R48_CASE_MATRIX_HANDOFF_ROW_FIELD_REFS",
    "P7_R49_IMPLEMENTED_STEPS",
    "P7_R49_R2_IMPLEMENTED_STEPS",
    "P7_R49_R2_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R49_R2_R3_IMPLEMENTED_STEPS",
    "P7_R49_R2_R3_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R49_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R49_R0_NEXT_REQUIRED_STEP_REF",
    "P7_R49_R1_NEXT_REQUIRED_STEP_REF",
    "P7_R49_R2_NEXT_REQUIRED_STEP_REF",
    "P7_R49_R3_NEXT_REQUIRED_STEP_REF",
    "P7_R49_QUESTION_IMPLEMENTATION_FALSE_KEYS",
    "P7_R49_RELEASE_CLOSED_KEYS",
    "P7_R49_R0_R1_FALSE_KEYS",
    "P7_R49_R0_R1_FALSE_KEY_REFS",
    "P7_R49_REQUIRED_UNRESOLVED_HOLD_REFS",
    "build_p7_r49_current_source_r48_handoff_bridge_refreeze",
    "build_p7_r49_review_session_envelope",
    "build_p7_r49_r0_r1_scope_status_freeze",
    "build_p7_r49_r48_case_matrix_handoff_validation",
    "build_p7_r49_local_only_actual_packet_generation_preflight",
    "build_p7_r49_r2_r3_case_matrix_preflight_freeze",
    "assert_p7_r49_current_source_r48_handoff_bridge_refreeze_contract",
    "assert_p7_r49_review_session_envelope_contract",
    "assert_p7_r49_r0_r1_scope_status_freeze_contract",
    "assert_p7_r49_r48_case_matrix_handoff_validation_contract",
    "assert_p7_r49_local_only_actual_packet_generation_preflight_contract",
    "assert_p7_r49_r2_r3_case_matrix_preflight_freeze_contract",
    "P7_R49_ACTUAL_REVIEW_SESSION_PROTOCOL_SCHEMA_VERSION",
    "P7_R49_RATING_ROW_INGESTION_R48_NORMALIZER_CONNECTION_SCHEMA_VERSION",
    "P7_R49_R4_R5_PROTOCOL_RATING_CONNECTION_FREEZE_SCHEMA_VERSION",
    "P7_R49_R4_IMPLEMENTED_STEPS",
    "P7_R49_R4_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R49_R5_IMPLEMENTED_STEPS",
    "P7_R49_R5_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R49_R4_NEXT_REQUIRED_STEP_REF",
    "P7_R49_R5_NEXT_REQUIRED_STEP_REF",
    "P7_R49_RATING_INGESTION_FORBIDDEN_REVIEW_RESULT_FIELD_REFS",
    "P7_R49_ACTUAL_REVIEW_SESSION_PROTOCOL_CASE_ROW_FIELD_REFS",
    "P7_R49_ACTUAL_REVIEW_SESSION_PROTOCOL_REQUIRED_FIELD_REFS",
    "P7_R49_RATING_ROW_INGESTION_R48_NORMALIZER_CONNECTION_REQUIRED_FIELD_REFS",
    "P7_R49_R4_R5_PROTOCOL_RATING_CONNECTION_FREEZE_REQUIRED_FIELD_REFS",
    "build_p7_r49_actual_review_session_protocol",
    "normalize_p7_r49_p5_rating_row_via_r48_bodyfree",
    "build_p7_r49_rating_row_ingestion_r48_normalizer_connection",
    "build_p7_r49_r4_r5_protocol_rating_connection_freeze",
    "assert_p7_r49_actual_review_session_protocol_contract",
    "assert_p7_r49_rating_row_ingestion_r48_normalizer_connection_contract",
    "assert_p7_r49_r4_r5_protocol_rating_connection_freeze_contract",
    "P7_R49_BLOCKER_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION",
    "P7_R49_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_ENUM_FREEZE_SCHEMA_VERSION",
    "P7_R49_R6_R7_BLOCKER_QUESTION_SCHEMA_FREEZE_SCHEMA_VERSION",
    "P7_R49_R6_IMPLEMENTED_STEPS",
    "P7_R49_R6_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R49_R7_IMPLEMENTED_STEPS",
    "P7_R49_R7_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R49_R6_NEXT_REQUIRED_STEP_REF",
    "P7_R49_R7_NEXT_REQUIRED_STEP_REF",
    "P7_R49_TO_R48_EXECUTION_BLOCKER_ID_MAP",
    "P7_R49_QUESTION_NEED_OBSERVATION_STAGE_REF",
    "P7_R49_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS",
    "P7_R49_QUESTION_NEED_OBSERVATION_ROW_FORBIDDEN_FIELD_REFS",
    "P7_R49_BLOCKER_EXECUTION_BLOCKER_INGESTION_REQUIRED_FIELD_REFS",
    "P7_R49_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_ENUM_FREEZE_REQUIRED_FIELD_REFS",
    "P7_R49_R6_R7_BLOCKER_QUESTION_SCHEMA_FREEZE_REQUIRED_FIELD_REFS",
    "normalize_p7_r49_p5_readfeel_blocker_row_via_r48_bodyfree",
    "normalize_p7_r49_execution_blocker_row_via_r48_bodyfree",
    "build_p7_r49_blocker_execution_blocker_ingestion",
    "build_p7_r49_question_need_observation_row_schema_enum_freeze",
    "build_p7_r49_r6_r7_blocker_question_schema_freeze",
    "assert_p7_r49_blocker_execution_blocker_ingestion_contract",
    "assert_p7_r49_question_need_observation_row_schema_enum_freeze_contract",
    "assert_p7_r49_r6_r7_blocker_question_schema_freeze_contract",
    "P7_R49_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_SCHEMA_VERSION",
    "P7_R49_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_SCHEMA_VERSION",
    "P7_R49_R8_R9_QUESTION_NORMALIZER_CONSISTENCY_GUARD_FREEZE_SCHEMA_VERSION",
    "P7_R49_R8_IMPLEMENTED_STEPS",
    "P7_R49_R8_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R49_R9_IMPLEMENTED_STEPS",
    "P7_R49_R9_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R49_R8_NEXT_REQUIRED_STEP_REF",
    "P7_R49_R9_NEXT_REQUIRED_STEP_REF",
    "P7_R49_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_REQUIRED_FIELD_REFS",
    "P7_R49_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS",
    "P7_R49_R8_R9_QUESTION_NORMALIZER_CONSISTENCY_GUARD_FREEZE_REQUIRED_FIELD_REFS",
    "normalize_p7_r49_question_need_observation_row_bodyfree",
    "assert_p7_r49_rating_vs_question_observation_consistency",
    "build_p7_r49_question_need_observation_row_normalizer",
    "build_p7_r49_rating_question_observation_consistency_guard",
    "build_p7_r49_r8_r9_question_normalizer_consistency_guard_freeze",
    "assert_p7_r49_question_need_observation_row_bodyfree_contract",
    "assert_p7_r49_question_need_observation_row_normalizer_contract",
    "assert_p7_r49_rating_question_observation_consistency_guard_contract",
    "assert_p7_r49_r8_r9_question_normalizer_consistency_guard_freeze_contract",
    "P7_R49_DISPOSAL_RECEIPT_CONNECTION_SCHEMA_VERSION",
    "P7_R49_R10_R11_QUESTION_SUMMARY_DISPOSAL_CONNECTION_FREEZE_SCHEMA_VERSION",
    "P7_R49_R10_IMPLEMENTED_STEPS",
    "P7_R49_R10_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R49_R11_IMPLEMENTED_STEPS",
    "P7_R49_R11_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R49_R10_NEXT_REQUIRED_STEP_REF",
    "P7_R49_R11_NEXT_REQUIRED_STEP_REF",
    "P7_R49_QUESTION_NEED_OBSERVATION_SUMMARY_BODYFREE_REQUIRED_FIELD_REFS",
    "P7_R49_DISPOSAL_RECEIPT_CONNECTION_REQUIRED_FIELD_REFS",
    "P7_R49_R10_R11_QUESTION_SUMMARY_DISPOSAL_CONNECTION_FREEZE_REQUIRED_FIELD_REFS",
    "build_p7_r49_question_need_observation_summary_bodyfree",
    "build_p7_r49_disposal_receipt_connection",
    "build_p7_r49_r10_r11_question_summary_disposal_connection_freeze",
    "assert_p7_r49_question_need_observation_summary_bodyfree_contract",
    "assert_p7_r49_disposal_receipt_connection_contract",
    "assert_p7_r49_r10_r11_question_summary_disposal_connection_freeze_contract",
    "P7_R49_P5_CONFIRMED_CANDIDATE_GATE_CONNECTION_SCHEMA_VERSION",
    "P7_R49_R12_R13_REVIEW_HANDOFF_P5_GATE_CONNECTION_FREEZE_SCHEMA_VERSION",
    "P7_R49_R12_IMPLEMENTED_STEPS",
    "P7_R49_R12_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R49_R13_IMPLEMENTED_STEPS",
    "P7_R49_R13_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R49_R12_NEXT_REQUIRED_STEP_REF",
    "P7_R49_R13_NEXT_REQUIRED_STEP_REF",
    "P7_R49_QUESTION_OBSERVATION_GATE_REQUIRED_CONDITION_REFS",
    "P7_R49_P5_CONFIRMED_CANDIDATE_REQUIRED_CONDITION_REFS",
    "P7_R49_REVIEW_HANDOFF_SUMMARY_BODYFREE_REQUIRED_FIELD_REFS",
    "P7_R49_P5_CONFIRMED_CANDIDATE_GATE_CONNECTION_REQUIRED_FIELD_REFS",
    "P7_R49_R12_R13_REVIEW_HANDOFF_P5_GATE_CONNECTION_FREEZE_REQUIRED_FIELD_REFS",
    "build_p7_r49_review_handoff_summary_bodyfree",
    "build_p7_r49_p5_confirmed_candidate_gate_connection",
    "build_p7_r49_r12_r13_review_handoff_p5_gate_connection_freeze",
    "assert_p7_r49_review_handoff_summary_bodyfree_contract",
    "assert_p7_r49_p5_confirmed_candidate_gate_connection_contract",
    "assert_p7_r49_r12_r13_review_handoff_p5_gate_connection_freeze_contract",
    "P7_R49_P6_LIMITED_HUMAN_READFEEL_START_CANDIDATE_HANDOFF_SCHEMA_VERSION",
    "P7_R49_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION",
    "P7_R49_R14_R15_P6_P8_CANDIDATE_HANDOFF_FREEZE_SCHEMA_VERSION",
    "P7_R49_R14_IMPLEMENTED_STEPS",
    "P7_R49_R14_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R49_R15_IMPLEMENTED_STEPS",
    "P7_R49_R15_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R49_R14_NEXT_REQUIRED_STEP_REF",
    "P7_R49_R15_NEXT_REQUIRED_STEP_REF",
    "P7_R49_P6_START_CANDIDATE_REQUIRED_CONDITION_REFS",
    "P7_R49_P6_LIMITED_HUMAN_READFEEL_START_CANDIDATE_HANDOFF_REQUIRED_FIELD_REFS",
    "P7_R49_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_REQUIRED_FIELD_REFS",
    "P7_R49_R14_R15_P6_P8_CANDIDATE_HANDOFF_FREEZE_REQUIRED_FIELD_REFS",
    "build_p7_r49_p6_limited_human_readfeel_start_candidate_handoff",
    "build_p7_r49_p8_question_design_material_candidate_handoff",
    "build_p7_r49_r14_r15_p6_p8_candidate_handoff_freeze",
    "assert_p7_r49_p6_limited_human_readfeel_start_candidate_handoff_contract",
    "assert_p7_r49_p8_question_design_material_candidate_handoff_contract",
    "assert_p7_r49_r14_r15_p6_p8_candidate_handoff_freeze_contract",
    "P7_R49_NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_SCHEMA_VERSION",
    "P7_R49_VALIDATION_COMMAND_MATRIX_SCHEMA_VERSION",
    "P7_R49_R16_R17_NO_BODY_LEAK_VALIDATION_COMMAND_MATRIX_FREEZE_SCHEMA_VERSION",
    "P7_R49_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION",
    "P7_R49_R16_IMPLEMENTED_STEPS",
    "P7_R49_R16_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R49_R17_IMPLEMENTED_STEPS",
    "P7_R49_R17_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R49_R16_NEXT_REQUIRED_STEP_REF",
    "P7_R49_R17_NEXT_REQUIRED_STEP_REF",
    "P7_R49_R18_IMPLEMENTED_STEPS",
    "P7_R49_R18_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R49_R18_NEXT_REQUIRED_STEP_REF",
    "P7_R49_R18_POST_FREEZE_NEXT_WORK_REF",
    "P7_R49_NO_BODY_LEAK_GUARD_MARKER_FALSE_KEY_REFS",
    "P7_R49_QUESTION_TEXT_FORBIDDEN_FIELD_REFS",
    "P7_R49_VALIDATION_COMMAND_GROUP_REFS",
    "P7_R49_VALIDATION_R49_TARGET_TEST_FILE_REFS",
    "P7_R49_VALIDATION_R48_REGRESSION_TEST_FILE_REFS",
    "P7_R49_VALIDATION_R47_REGRESSION_TEST_FILE_REFS",
    "P7_R49_VALIDATION_R46_HANDOFF_TEST_FILE_REFS",
    "P7_R49_VALIDATION_DISPLAY_API_TEST_FILE_REFS",
    "P7_R49_VALIDATION_P5_CORE_TEST_FILE_REFS",
    "P7_R49_NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_REQUIRED_FIELD_REFS",
    "P7_R49_VALIDATION_COMMAND_MATRIX_REQUIRED_FIELD_REFS",
    "P7_R49_R16_R17_NO_BODY_LEAK_VALIDATION_COMMAND_MATRIX_FREEZE_REQUIRED_FIELD_REFS",
    "P7_R49_PRODUCTION_TOUCH_CANDIDATE_FILE_REFS",
    "P7_R49_OPTIONAL_TOUCH_CANDIDATE_FILE_REFS",
    "P7_R49_ALLOWED_PRODUCTION_TOUCH_FILE_REFS",
    "P7_R49_ALLOWED_TEST_TOUCH_FILE_REFS",
    "P7_R49_ALLOWED_ACTUAL_TOUCHED_FILE_REFS",
    "P7_R49_RN_PRODUCTION_NO_TOUCH_FILE_REFS",
    "P7_R49_RN_CONTRACT_OPTIONAL_NO_TOUCH_TEST_REFS",
    "P7_R49_EXPLICIT_NO_TOUCH_FILE_REFS",
    "P7_R49_EXPLICIT_NO_TOUCH_AREA_REFS",
    "P7_R49_R18_CURRENT_PATCH_EXPECTED_TOUCHED_FILE_REFS",
    "P7_R49_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS",
    "build_p7_r49_no_body_leak_no_question_text_guard",
    "build_p7_r49_validation_command_matrix",
    "build_p7_r49_r16_r17_no_body_leak_validation_command_matrix_freeze",
    "assert_p7_r49_no_body_leak_no_question_text_guard_contract",
    "assert_p7_r49_validation_command_matrix_contract",
    "assert_p7_r49_r16_r17_no_body_leak_validation_command_matrix_freeze_contract",
    "build_p7_r49_touch_candidate_no_touch_boundary_freeze",
    "assert_p7_r49_touch_candidate_no_touch_boundary_freeze_contract",
    "assert_p7_r49_touch_candidate_no_touch_actual_touched_file_refs_contract",

]
