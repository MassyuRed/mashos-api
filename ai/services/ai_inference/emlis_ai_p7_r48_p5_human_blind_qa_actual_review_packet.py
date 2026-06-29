# -*- coding: utf-8 -*-
"""P7-R48 P5 Human Blind QA actual review packet helpers.

R0 refreezes the current local source, the R47 policy-ready handoff, and the
current HOLD state before any P5 actual review material is created.
R1 fixes only the R48 scope, schema-version constants, packet kind, and review
kind for the P5 Human Blind QA actual review packet lane.
R2 connects the R48 actual packet lane to the R47 external local-only storage
root policy without creating body-full material.
R3 builds the first formal P5 24-case review matrix as body-free controller
material.
R4 separates blind_case_id from controller-only case_ref/family/tier refs.
R5 freezes the reviewer-facing local-only packet schema without materializing
body-full payloads.
R6 fixes the materialization guard so body-full packets remain blocked by
default and require both a valid external local root and explicit allow.
R7 fixes local reviewer notes as local-only material that must be reduced to
body-free reason/blocker identifiers before any handoff material can retain it.
R8 normalizes sanitized human readfeel results into body-free rating rows.
R9 separates readfeel blocker rows from execution blocker rows.
R10 fixes the body-free disposal receipt builder contract without deleting files.
R11 fixes the body-free P5 review handoff summary builder contract without
starting P6, completing P7, opening P8, or permitting release.
R12 fixes the P5 confirmed-candidate gate so ratings alone cannot confirm P5.
R13 fixes the R47 regression and no body-free leak guard boundary.
R14 fixes the R46 handoff regression contract so P5/P6/real-device HOLDs and
next-decision ledger boundaries stay closed.
R15 fixes the P5 core subset regression contract without changing P5 runtime.
R16 fixes the display-contract regression and RN no-touch confirmation boundary.
R17 fixes the validation command matrix while keeping command execution and
green confirmations outside the body-free policy builder.
R18 fixes the production/test touch candidates and explicit no-touch boundary so
R48 remains confined to the review-preparation helper/tests and does not spread
into runtime, RN, API, DB, or release material.

This module intentionally does not create JSON schema files, write body-full
reviewer packets, write reviewer notes, execute human review, execute cleanup,
or export local review body material. It also does not start or confirm P5 human
review, start P6 readfeel, run real-device review, close HOLD-004, complete P7,
open P8, or permit release.
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
from emlis_ai_p7_r46_next_decision_handoff_ledger import (
    P7_R46_NEXT_DECISION_HANDOFF_LEDGER_SCHEMA_VERSION,
    P7_R46_NEXT_DECISION_SUMMARY_SCHEMA_VERSION,
    assert_p7_r46_next_decision_handoff_ledger_contract,
    assert_p7_r46_next_decision_summary_contract,
    build_p7_r46_next_decision_handoff_ledger,
    build_p7_r46_next_decision_summary,
)
from emlis_ai_p7_r46_p5_p6_human_readfeel_handoff_material import (
    P5_HUMAN_BLIND_QA_FAMILIES,
    P5_HUMAN_BLIND_QA_HOLD_REF,
    P5_HUMAN_BLIND_QA_RATING_AXES,
    P5_HUMAN_BLIND_QA_RETURN_HOLD_REF,
    P5_HUMAN_BLIND_QA_TARGETS,
    P6_LIMITED_HUMAN_READFEEL_HOLD_REF,
    P6_LIMITED_HUMAN_READFEEL_RETURN_HOLD_REF,
    P7_R46_P5_HUMAN_BLIND_QA_HANDOFF_SCHEMA_VERSION,
    P7_R46_P5_P6_HUMAN_READFEEL_HANDOFF_SUMMARY_SCHEMA_VERSION,
    P7_R46_P6_LIMITED_HUMAN_READFEEL_HANDOFF_SCHEMA_VERSION,
    assert_p5_human_blind_qa_handoff_material_contract,
    assert_p5_p6_human_readfeel_handoff_summary_contract,
    assert_p6_limited_human_readfeel_handoff_material_contract,
    build_p5_human_blind_qa_handoff_material,
    build_p5_p6_human_readfeel_handoff_summary,
    build_p6_limited_human_readfeel_handoff_material,
)
from emlis_ai_p7_r46_real_device_modal_review_closed_validation import (
    HOLD_DC_FULL_BACKEND_SUITE_REF,
    P7_HOLD_FULL_BACKEND_SUITE_REF,
    P7_HOLD_REAL_DEVICE_MODAL_REF,
    P7_R46_HOLD_RELEASE_P8_CLOSED_VALIDATION_SCHEMA_VERSION,
    P7_R46_REAL_DEVICE_AND_CLOSED_VALIDATION_SUMMARY_SCHEMA_VERSION,
    P7_R46_REAL_DEVICE_MODAL_REVIEW_CHECKLIST_SCHEMA_VERSION,
    P7_RETURN_REAL_DEVICE_HOLD_REF,
    assert_p7_hold_release_p8_closed_validation_contract,
    assert_real_device_and_closed_validation_summary_contract,
    assert_real_device_submit_modal_readfeel_checklist_contract,
    build_p7_hold_release_p8_closed_validation,
    build_real_device_and_closed_validation_summary,
    build_real_device_submit_modal_readfeel_checklist,
)
from emlis_ai_p7_r47_local_review_packet_policy import (
    P7_R47_BODY_FREE_BLOCKER_ROW_SCHEMA_VERSION,
    P7_R47_BODY_FREE_DISPOSAL_RECEIPT_FORBIDDEN_FIELD_REFS,
    P7_R47_BODY_FREE_DISPOSAL_RECEIPT_SCHEMA_VERSION,
    P7_R47_BODY_FREE_RATING_BLOCKER_FORBIDDEN_FIELD_REFS,
    P7_R47_BODY_FREE_RATING_ROW_SCHEMA_VERSION,
    P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
    P7_R47_BLOCKER_KINDS,
    P7_R47_BLOCKER_STATUSES,
    P7_R47_DISPOSAL_STATUSES,
    P7_R47_EXECUTION_BLOCKER_ID_REFS,
    P7_R47_LOCAL_REVIEW_PACKET_POLICY_SCHEMA_VERSION,
    P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR,
    P7_R47_LOCAL_REVIEW_STORAGE_ROOT_POLICY_SCHEMA_VERSION,
    P7_R47_P5_FIRST_FORMAL_MINIMUMS,
    P7_R47_P5_HISTORY_SURFACE_POLICY,
    P7_R47_P5_REVIEW_KIND,
    P7_R47_P5_REVIEWER_FACING_ALLOWED_FIELD_REFS,
    P7_R47_P5_REVIEWER_FACING_FORBIDDEN_FIELD_REFS,
    P7_R47_PACKET_KIND_SET,
    P7_R47_R14_R15_NEXT_REQUIRED_STEP_REF,
    P7_R47_R14_R15_VALIDATION_TOUCH_BOUNDARY_SCHEMA_VERSION,
    P7_R47_REQUIRED_UNRESOLVED_HOLD_REFS,
    P7_R47_REVIEW_VERDICTS,
    P7_R47_REVIEWER_NOTES_LOCAL_ONLY_POLICY_SCHEMA_VERSION,
    P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
    P7_R47_SANITIZED_REASON_ID_REFS,
    P7_R47_STORAGE_MODE_EXTERNAL_LOCAL_ONLY,
    P7_R47_STORAGE_ROOT_REF,
    assert_p7_r47_local_review_storage_root_policy_contract,
    assert_p7_r47_r14_r15_validation_touch_boundary_freeze_contract,
    build_p7_r47_local_review_storage_root_policy,
    build_p7_r47_r14_r15_validation_touch_boundary_freeze,
)

P7_R48_CURRENT_SOURCE_R47_HANDOFF_HOLD_REFREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.current_source_r47_handoff_hold_refreeze.v1"
)
P7_R48_SCOPE_SCHEMA_PACKET_KIND_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.scope_schema_packet_kind_freeze.v1"
)
P7_R48_R0_R1_SCOPE_FREEZE_SCHEMA_VERSION: Final = "cocolon.emlis.p7_r48.r0_r1_scope_freeze.v1"
P7_R48_LOCAL_STORAGE_ROOT_POLICY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.local_storage_root_policy.v1"
)
P7_R48_R2_R3_LOCAL_STORAGE_CASE_MATRIX_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.r2_r3_local_storage_case_matrix_freeze.v1"
)
P7_R48_BLIND_CASE_ID_CASE_REF_SEPARATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.blind_case_id_case_ref_separation.v1"
)
P7_R48_REVIEWER_FACING_LOCAL_PACKET_SCHEMA_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.reviewer_facing_local_packet_schema_freeze.v1"
)
P7_R48_R4_R5_REVIEWER_PACKET_SCHEMA_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.r4_r5_reviewer_packet_schema_freeze.v1"
)
P7_R48_BODY_FULL_PACKET_MATERIALIZATION_GUARD_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.body_full_packet_materialization_guard.v1"
)
P7_R48_LOCAL_REVIEWER_NOTES_POLICY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.local_reviewer_notes_policy.v1"
)
P7_R48_R6_R7_MATERIALIZATION_NOTES_POLICY_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.r6_r7_materialization_notes_policy_freeze.v1"
)
P7_R48_RATING_ROW_NORMALIZER_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.rating_row_normalizer.v1"
)
P7_R48_BLOCKER_EXECUTION_BLOCKER_ROW_BUILDER_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.blocker_execution_blocker_row_builder.v1"
)
P7_R48_R8_R9_RATING_BLOCKER_ROWS_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.r8_r9_rating_blocker_rows_freeze.v1"
)
P7_R48_DISPOSAL_RECEIPT_BUILDER_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.disposal_receipt_builder.v1"
)
P7_R48_P5_REVIEW_HANDOFF_SUMMARY_BUILDER_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.p5_review_handoff_summary_builder.v1"
)
P7_R48_R10_R11_DISPOSAL_HANDOFF_SUMMARY_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.r10_r11_disposal_handoff_summary_freeze.v1"
)
P7_R48_P5_CONFIRMED_CANDIDATE_GATE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.p5_confirmed_candidate_gate.v1"
)
P7_R48_R47_REGRESSION_NO_BODY_FREE_LEAK_GUARD_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.r47_regression_no_body_free_leak_guard.v1"
)
P7_R48_R12_R13_CONFIRMED_GATE_LEAK_GUARD_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.r12_r13_confirmed_gate_leak_guard_freeze.v1"
)
P7_R48_R46_HANDOFF_REGRESSION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.r46_handoff_regression.v1"
)
P7_R48_P5_CORE_SUBSET_REGRESSION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.p5_core_subset_regression.v1"
)
P7_R48_R14_R15_REGRESSION_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.r14_r15_regression_freeze.v1"
)
P7_R48_DISPLAY_CONTRACT_RN_NO_TOUCH_CONFIRMATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.display_contract_rn_no_touch_confirmation.v1"
)
P7_R48_VALIDATION_COMMAND_MATRIX_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.validation_command_matrix.v1"
)
P7_R48_R16_R17_VALIDATION_NO_TOUCH_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.r16_r17_validation_no_touch_freeze.v1"
)
P7_R48_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.touch_candidate_no_touch_boundary_freeze.v1"
)
P7_R48_P5_REVIEW_POLICY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.p5_human_blind_qa_actual_review_policy.v1"
)
P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION: Final = "cocolon.emlis.p7_r48.p5_case_matrix.bodyfree.v1"
P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.p5_reviewer_packet.local_only.v1"
)
P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION: Final = "cocolon.emlis.p7_r48.p5_rating_row.bodyfree.v1"
P7_R48_P5_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION: Final = "cocolon.emlis.p7_r48.p5_blocker_row.bodyfree.v1"
P7_R48_P5_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.p5_execution_blocker_row.bodyfree.v1"
)
P7_R48_P5_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.p5_disposal_receipt.bodyfree.v1"
)
P7_R48_P5_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.p5_review_handoff_summary.bodyfree.v1"
)

P7_R48_STEP: Final = "R48_P5HumanBlindQAActualReviewPacket_20260618"
P7_R48_SCOPE: Final = "p5_human_blind_qa_actual_review_packet_generation_rating_disposal"
P7_R48_POLICY_KIND: Final = "p5_human_blind_qa_actual_review_packet_policy"
P7_R48_PACKET_KIND: Final = "p5_human_blind_qa_local_review_packet"
P7_R48_REVIEW_KIND: Final = "p5_history_line_readfeel"
P7_R48_FIRST_NEXT_WORK_REF: Final = "p5_human_blind_qa_actual_review_packet_generation_rating_disposal"
P7_R48_NEXT_REQUIRED_STEP_REF: Final = "R2_local_storage_root_policy"
P7_R48_R2_R3_NEXT_REQUIRED_STEP_REF: Final = "R4_blind_case_id_case_ref_separation"
P7_R48_R4_NEXT_REQUIRED_STEP_REF: Final = "R5_reviewer_facing_local_packet_schema"
P7_R48_R4_R5_NEXT_REQUIRED_STEP_REF: Final = "R6_body_full_packet_materialization_guard"
P7_R48_R6_NEXT_REQUIRED_STEP_REF: Final = "R7_local_reviewer_notes_policy"
P7_R48_R6_R7_NEXT_REQUIRED_STEP_REF: Final = "R8_rating_row_normalizer"
P7_R48_R8_NEXT_REQUIRED_STEP_REF: Final = "R9_blocker_execution_blocker_row_builder"
P7_R48_R8_R9_NEXT_REQUIRED_STEP_REF: Final = "R10_disposal_receipt_builder"
P7_R48_R10_NEXT_REQUIRED_STEP_REF: Final = "R11_p5_review_handoff_summary_builder"
P7_R48_R10_R11_NEXT_REQUIRED_STEP_REF: Final = "R12_p5_confirmed_candidate_gate"
P7_R48_R12_NEXT_REQUIRED_STEP_REF: Final = "R13_r47_regression_no_body_free_leak_guard"
P7_R48_R12_R13_NEXT_REQUIRED_STEP_REF: Final = "R14_r46_handoff_regression"
P7_R48_R14_NEXT_REQUIRED_STEP_REF: Final = "R15_p5_core_subset_regression"
P7_R48_R14_R15_NEXT_REQUIRED_STEP_REF: Final = "R16_display_contract_rn_no_touch_confirmation"
P7_R48_R16_NEXT_REQUIRED_STEP_REF: Final = "R17_validation_command_matrix"
P7_R48_R16_R17_NEXT_REQUIRED_STEP_REF: Final = "R18_touch_candidate_no_touch_boundary_freeze"
P7_R48_R18_NEXT_REQUIRED_STEP_REF: Final = "P5_human_blind_qa_actual_review_execution_decision"

P7_R48_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R0_current_source_r47_handoff_hold_refreeze",
    "R1_scope_schema_version_packet_kind_freeze",
)
P7_R48_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R2_local_storage_root_policy",
    "R3_p5_24_case_first_formal_review_matrix_builder",
    "R4_blind_case_id_case_ref_separation",
    "R5_reviewer_facing_local_packet_schema",
    "R6_body_full_packet_materialization_guard",
    "R7_local_reviewer_notes_policy",
    "R8_rating_row_normalizer",
    "R9_blocker_execution_blocker_row_builder",
    "R10_disposal_receipt_builder",
    "R11_p5_review_handoff_summary_builder",
    "R12_p5_confirmed_candidate_gate",
    "R13_r47_regression_no_body_free_leak_guard",
    "R14_r46_handoff_regression",
    "R15_p5_core_subset_regression",
    "R16_display_contract_rn_no_touch_confirmation",
    "R17_validation_command_matrix",
    "R18_touch_candidate_no_touch_boundary_freeze",
)
P7_R48_R2_R3_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R48_IMPLEMENTED_STEPS,
    "R2_local_storage_root_policy",
    "R3_p5_24_case_first_formal_review_matrix_builder",
)
P7_R48_R2_R3_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R4_blind_case_id_case_ref_separation",
    "R5_reviewer_facing_local_packet_schema",
    "R6_body_full_packet_materialization_guard",
    "R7_local_reviewer_notes_policy",
    "R8_rating_row_normalizer",
    "R9_blocker_execution_blocker_row_builder",
    "R10_disposal_receipt_builder",
    "R11_p5_review_handoff_summary_builder",
    "R12_p5_confirmed_candidate_gate",
    "R13_r47_regression_no_body_free_leak_guard",
    "R14_r46_handoff_regression",
    "R15_p5_core_subset_regression",
    "R16_display_contract_rn_no_touch_confirmation",
    "R17_validation_command_matrix",
    "R18_touch_candidate_no_touch_boundary_freeze",
)
P7_R48_R4_R5_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R48_R2_R3_IMPLEMENTED_STEPS,
    "R4_blind_case_id_case_ref_separation",
    "R5_reviewer_facing_local_packet_schema",
)
P7_R48_R4_R5_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R6_body_full_packet_materialization_guard",
    "R7_local_reviewer_notes_policy",
    "R8_rating_row_normalizer",
    "R9_blocker_execution_blocker_row_builder",
    "R10_disposal_receipt_builder",
    "R11_p5_review_handoff_summary_builder",
    "R12_p5_confirmed_candidate_gate",
    "R13_r47_regression_no_body_free_leak_guard",
    "R14_r46_handoff_regression",
    "R15_p5_core_subset_regression",
    "R16_display_contract_rn_no_touch_confirmation",
    "R17_validation_command_matrix",
    "R18_touch_candidate_no_touch_boundary_freeze",
)
P7_R48_R6_R7_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R48_R4_R5_IMPLEMENTED_STEPS,
    "R6_body_full_packet_materialization_guard",
    "R7_local_reviewer_notes_policy",
)
P7_R48_R6_R7_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R8_rating_row_normalizer",
    "R9_blocker_execution_blocker_row_builder",
    "R10_disposal_receipt_builder",
    "R11_p5_review_handoff_summary_builder",
    "R12_p5_confirmed_candidate_gate",
    "R13_r47_regression_no_body_free_leak_guard",
    "R14_r46_handoff_regression",
    "R15_p5_core_subset_regression",
    "R16_display_contract_rn_no_touch_confirmation",
    "R17_validation_command_matrix",
    "R18_touch_candidate_no_touch_boundary_freeze",
)
P7_R48_R8_R9_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R48_R6_R7_IMPLEMENTED_STEPS,
    "R8_rating_row_normalizer",
    "R9_blocker_execution_blocker_row_builder",
)
P7_R48_R8_R9_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R10_disposal_receipt_builder",
    "R11_p5_review_handoff_summary_builder",
    "R12_p5_confirmed_candidate_gate",
    "R13_r47_regression_no_body_free_leak_guard",
    "R14_r46_handoff_regression",
    "R15_p5_core_subset_regression",
    "R16_display_contract_rn_no_touch_confirmation",
    "R17_validation_command_matrix",
    "R18_touch_candidate_no_touch_boundary_freeze",
)
P7_R48_R10_R11_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R48_R8_R9_IMPLEMENTED_STEPS,
    "R10_disposal_receipt_builder",
    "R11_p5_review_handoff_summary_builder",
)
P7_R48_R10_R11_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R12_p5_confirmed_candidate_gate",
    "R13_r47_regression_no_body_free_leak_guard",
    "R14_r46_handoff_regression",
    "R15_p5_core_subset_regression",
    "R16_display_contract_rn_no_touch_confirmation",
    "R17_validation_command_matrix",
    "R18_touch_candidate_no_touch_boundary_freeze",
)
P7_R48_R12_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R48_R10_R11_IMPLEMENTED_STEPS,
    "R12_p5_confirmed_candidate_gate",
)
P7_R48_R12_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R13_r47_regression_no_body_free_leak_guard",
    "R14_r46_handoff_regression",
    "R15_p5_core_subset_regression",
    "R16_display_contract_rn_no_touch_confirmation",
    "R17_validation_command_matrix",
    "R18_touch_candidate_no_touch_boundary_freeze",
)
P7_R48_R12_R13_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R48_R12_IMPLEMENTED_STEPS,
    "R13_r47_regression_no_body_free_leak_guard",
)
P7_R48_R12_R13_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R14_r46_handoff_regression",
    "R15_p5_core_subset_regression",
    "R16_display_contract_rn_no_touch_confirmation",
    "R17_validation_command_matrix",
    "R18_touch_candidate_no_touch_boundary_freeze",
)
P7_R48_R14_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R48_R12_R13_IMPLEMENTED_STEPS,
    "R14_r46_handoff_regression",
)
P7_R48_R14_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R15_p5_core_subset_regression",
    "R16_display_contract_rn_no_touch_confirmation",
    "R17_validation_command_matrix",
    "R18_touch_candidate_no_touch_boundary_freeze",
)
P7_R48_R14_R15_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R48_R14_IMPLEMENTED_STEPS,
    "R15_p5_core_subset_regression",
)
P7_R48_R14_R15_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R16_display_contract_rn_no_touch_confirmation",
    "R17_validation_command_matrix",
    "R18_touch_candidate_no_touch_boundary_freeze",
)
P7_R48_R16_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R48_R14_R15_IMPLEMENTED_STEPS,
    "R16_display_contract_rn_no_touch_confirmation",
)
P7_R48_R16_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R17_validation_command_matrix",
    "R18_touch_candidate_no_touch_boundary_freeze",
)
P7_R48_R16_R17_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R48_R16_IMPLEMENTED_STEPS,
    "R17_validation_command_matrix",
)
P7_R48_R16_R17_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R18_touch_candidate_no_touch_boundary_freeze",
)
P7_R48_R18_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R48_R16_R17_IMPLEMENTED_STEPS,
    "R18_touch_candidate_no_touch_boundary_freeze",
)
P7_R48_R18_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = ()

P7_R48_RECEIVED_LOCAL_SNAPSHOT_REFS: Final[dict[str, str]] = {
    "premise_zip_ref": "Cocolon_前提資料(234).zip",
    "implemented_materials_zip_ref": "EmlisAIの実装済み資料(69).zip",
    "rn_zip_ref": "Cocolon(242).zip",
    "backend_zip_ref": "mashos-api(155).zip",
    "roadmap_ref": "Cocolon_EmlisAI_longterm_roadmap_20260608(21).md",
    "pre_design_memo_ref": "Cocolon_EmlisAI_P7_R48_P5HumanBlindQAActualReview_PreDesignMemo_20260618.md",
    "detailed_design_ref": "Cocolon_EmlisAI_P7_R48_P5HumanBlindQAActualReviewPacket_詳細設計書_実装順_20260618.md",
    "r47_handoff_helper_ref": "emlis_ai_p7_r47_local_review_packet_policy.build_p7_r47_r14_r15_validation_touch_boundary_freeze",
}

P7_R48_REQUIRED_UNRESOLVED_HOLD_REFS: Final[tuple[str, ...]] = (
    P5_HUMAN_BLIND_QA_HOLD_REF,
    P5_HUMAN_BLIND_QA_RETURN_HOLD_REF,
    P6_LIMITED_HUMAN_READFEEL_HOLD_REF,
    P6_LIMITED_HUMAN_READFEEL_RETURN_HOLD_REF,
    P7_HOLD_REAL_DEVICE_MODAL_REF,
    P7_RETURN_REAL_DEVICE_HOLD_REF,
    P7_HOLD_FULL_BACKEND_SUITE_REF,
    HOLD_DC_FULL_BACKEND_SUITE_REF,
)

P7_R48_REVIEW_PROMPT_VERSION: Final = "p7_r48_p5_human_blind_qa_review_prompt.v1"
P7_R48_STORAGE_MODE_EXTERNAL_LOCAL_ONLY: Final = P7_R47_STORAGE_MODE_EXTERNAL_LOCAL_ONLY
P7_R48_STORAGE_ROOT_REF: Final = P7_R47_STORAGE_ROOT_REF
P7_R48_REVIEW_SESSION_DEFAULT_REF: Final = "p7_r48_p5_first_formal_review_session"
P7_R48_REVIEW_SESSION_DEFAULT_SHORT_REF: Final = "s000"
P7_R48_EXPLICIT_ALLOW_BLOCK_REASON_REF: Final = "review_packet_generation_blocked_missing_explicit_allow"
P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION: Final[tuple[tuple[str, int, str], ...]] = (
    ("history_line_eligible_input", 4, "positive_history_line"),
    ("standard_state_answer_owned_history", 4, "positive_owned_history"),
    ("self_understanding_owned_history", 3, "positive_owned_history"),
    ("uncertainty_support_owned_history", 3, "positive_owned_history"),
    ("change_future_intention_owned_history", 3, "positive_owned_history"),
    ("relationship_gratitude_recovery_owned_history", 3, "positive_owned_history"),
    ("low_information_history_not_eligible", 2, "boundary_no_history_line"),
    ("free_tier_history_present_not_allowed", 2, "boundary_no_history_line"),
)
P7_R48_P5_POSITIVE_CASE_ROLE_REFS: Final[frozenset[str]] = frozenset(
    {"positive_history_line", "positive_owned_history"}
)
P7_R48_P5_BOUNDARY_FAMILY_REFS: Final[frozenset[str]] = frozenset(
    {"low_information_history_not_eligible", "free_tier_history_present_not_allowed"}
)
P7_R48_P5_CASE_ROLE_REFS: Final[frozenset[str]] = frozenset(
    {"positive_history_line", "positive_owned_history", "boundary_no_history_line"}
)
P7_R48_P5_TIER_REF_REFS: Final[frozenset[str]] = frozenset({"free", "plus", "premium", "unknown"})
P7_R48_P5_CASE_MATRIX_ROW_FIELD_REFS: Final[frozenset[str]] = frozenset(
    {
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
    }
)
P7_R48_CONTROLLER_MANIFEST_ROW_FIELD_REFS: Final[frozenset[str]] = frozenset(
    {
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
        "body_free",
    }
)
P7_R48_REVIEWER_FACING_CASE_INDEX_ROW_FIELD_REFS: Final[frozenset[str]] = frozenset(
    {
        "blind_case_id",
        "reviewer_identifier_kind",
        "case_ref_hidden",
        "family_hidden",
        "tier_hidden",
        "expected_result_hidden",
        "gate_result_hidden",
        "derived_from_body_or_record_hash",
        "body_free",
    }
)
P7_R48_P5_REVIEWER_PACKET_REVIEWER_VISIBLE_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R47_P5_REVIEWER_FACING_ALLOWED_FIELD_REFS,
)
P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_CONTROL_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "local_only",
    "must_not_export",
    "disposal_required",
    "packet_kind",
    "review_session_id",
    "packet_ref_id",
)
P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "local_only",
    "must_not_export",
    "disposal_required",
    "packet_kind",
    "review_kind",
    "review_session_id",
    "packet_ref_id",
    "blind_case_id",
    "review_prompt_version",
    "current_input_review_surface",
    "returned_emlis_surface",
    "bounded_owned_history_review_surface",
    "review_questions",
    "axis_rating_form",
)
P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_FORBIDDEN_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        [
            *P7_R47_P5_REVIEWER_FACING_FORBIDDEN_FIELD_REFS,
            "history_raw_text",
            "reviewer_ref",
            "controller_expected_boundary",
            "reviewer_free_text",
            "reviewer_note",
            "reviewer_notes",
            "raw_text_hash",
            "comment_text_hash",
            "body_content_hash",
            "body_full_file_content_hash",
            "terminal_output",
            "stdout",
            "stderr",
            "traceback",
            "local_absolute_path",
        ]
    )
)
P7_R48_P5_REVIEWER_PACKET_BODY_FIELD_REFS: Final[tuple[str, ...]] = (
    "current_input_review_surface",
    "returned_emlis_surface",
    "bounded_owned_history_review_surface",
)
P7_R48_P5_REVIEW_QUESTION_REFS: Final[tuple[str, ...]] = (
    "history_connection_naturalness",
    "creepy_absence",
    "overclaim_absence",
    "current_input_not_overridden_by_history",
    "self_blame_non_amplification",
    "non_shallow_repeat",
    "wants_more_input_or_accumulation",
    "boundary_history_line_leak_check",
)
P7_R48_LOCAL_REVIEWER_PACKET_REQUIRED_FLAG_REFS: Final[tuple[str, ...]] = (
    "local_only",
    "must_not_export",
    "disposal_required",
)
P7_R48_BODY_FULL_PACKET_MATERIALIZATION_BLOCK_REASON_REFS: Final[tuple[str, ...]] = (
    "review_packet_generation_blocked_missing_local_root",
    "review_packet_generation_blocked_invalid_local_root",
    "review_packet_generation_blocked_repo_or_artifact_root",
    P7_R48_EXPLICIT_ALLOW_BLOCK_REASON_REF,
)
P7_R48_SANITIZED_REASON_ID_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        [
            *P7_R47_SANITIZED_REASON_ID_REFS,
            "p5_current_input_overridden_by_history",
            "p5_boundary_history_line_leak_suspected",
        ]
    )
)
P7_R48_EXECUTION_BLOCKER_ID_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        [
            *P7_R47_EXECUTION_BLOCKER_ID_REFS,
            "review_packet_generation_blocked_repo_or_artifact_root",
            P7_R48_EXPLICIT_ALLOW_BLOCK_REASON_REF,
            "review_case_matrix_minimum_not_met",
            "body_full_packet_export_violation",
        ]
    )
)
P7_R48_P5_REVIEW_VERDICTS: Final[tuple[str, ...]] = P7_R47_REVIEW_VERDICTS
P7_R48_P5_REVIEWABLE_VERDICTS: Final[tuple[str, ...]] = ("PASS", "YELLOW", "REPAIR_REQUIRED", "RED")
P7_R48_READFEEL_BLOCKER_ID_REFS: Final[tuple[str, ...]] = (
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
P7_R48_P5_BLOCKER_KINDS: Final[tuple[str, ...]] = P7_R47_BLOCKER_KINDS
P7_R48_P5_BLOCKER_STATUSES: Final[tuple[str, ...]] = P7_R47_BLOCKER_STATUSES
P7_R48_EXECUTION_BLOCKER_KIND_REFS: Final[tuple[str, ...]] = (
    "GENERATION",
    "MATERIAL",
    "REVIEW",
    "RATING",
    "DISPOSAL",
    "VALIDATION",
)
P7_R48_EXECUTION_BLOCKER_STATUS_REFS: Final[tuple[str, ...]] = ("OPEN", "TRIAGED", "RESOLVED", "CLOSED")
P7_R48_P5_RATING_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
P7_R48_P5_BLOCKER_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
P7_R48_P5_EXECUTION_BLOCKER_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
P7_R48_P5_RATING_BLOCKER_FORBIDDEN_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        [
            *P7_R47_BODY_FREE_RATING_BLOCKER_FORBIDDEN_FIELD_REFS,
            "current_input_review_surface",
            "returned_emlis_surface",
            "bounded_owned_history_review_surface",
            "reviewer_payload",
            "review_form",
            "machine_metrics",
            "machine_metric",
            "auto_score",
            "auto_scores",
            "auto_estimated",
            "readfeel_auto_estimated",
            "machine_metrics_used_for_readfeel",
        ]
    )
)

P7_R48_P5_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
P7_R48_P5_DISPOSAL_RECEIPT_FORBIDDEN_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        [
            *P7_R47_BODY_FREE_DISPOSAL_RECEIPT_FORBIDDEN_FIELD_REFS,
            "current_input_review_surface",
            "returned_emlis_surface",
            "bounded_owned_history_review_surface",
            "reviewer_payload",
            "review_form",
            "reviewer_notes_payload",
            "body_hash",
            "body_content_hash",
            "body_full_file_content_hash",
            "raw_text_hash",
            "comment_text_hash",
            "local_absolute_path",
            "deleted_body_preview",
        ]
    )
)
P7_R48_P5_REVIEW_HANDOFF_SUMMARY_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "review_session_status",
    "review_kind",
    "packet_kind",
    "case_count",
    "reviewed_case_count",
    "rating_row_count",
    "blocker_row_count",
    "execution_blocker_row_count",
    "family_coverage_satisfied",
    "axis_averages",
    "axis_targets_satisfied",
    "red_case_count",
    "repair_required_case_count",
    "open_blocker_ids",
    "open_execution_blocker_ids",
    "boundary_violation_blocker_ids",
    "disposal_status",
    "body_removed",
    "reviewer_notes_removed",
    "local_packet_exported",
    "content_hash_of_body_stored",
    "disposal_verified_for_candidate",
    "p5_human_blind_qa_confirmed_candidate",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "release_allowed",
    "p7_complete",
    "p8_start_allowed",
    "hold004_close_allowed",
    "body_free",
)
P7_R48_REVIEW_SESSION_STATUS_REFS: Final[tuple[str, ...]] = (
    "NOT_STARTED",
    "IN_PROGRESS",
    "FINALIZED",
    "BLOCKED",
)
P7_R48_P5_CONFIRMED_ALLOWED_DISPOSAL_STATUS_REFS: Final[frozenset[str]] = frozenset(
    {"DISPOSAL_VERIFIED", "EXPIRED_PURGED"}
)
P7_R48_P5_BOUNDARY_VIOLATION_BLOCKER_ID_REFS: Final[frozenset[str]] = frozenset(
    {
        "p5_free_tier_history_boundary_violation",
        "p5_low_information_history_overread",
        "p5_boundary_history_line_leak_suspected",
    }
)
P7_R48_P5_CONFIRMED_CANDIDATE_REQUIRED_CONDITION_REFS: Final[tuple[str, ...]] = (
    "review_session_finalized",
    "minimum_total_cases_24",
    "rating_rows_present_for_all_reviewable_cases",
    "family_coverage_satisfied",
    "axis_targets_satisfied",
    "red_case_count_zero",
    "repair_required_case_count_zero",
    "open_readfeel_blockers_zero",
    "open_execution_blockers_zero",
    "boundary_violation_blockers_zero",
    "body_removed",
    "reviewer_notes_removed",
    "disposal_verified_for_candidate",
    "local_packet_not_exported",
    "content_hash_of_body_not_stored",
    "handoff_summary_candidate_claim_true",
    "handoff_summary_p6_candidate_consistent",
)
P7_R48_P5_CONFIRMED_CANDIDATE_GATE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "review_session_id",
    "review_kind",
    "packet_kind",
    "handoff_summary_schema_version",
    "review_session_status",
    "required_total_cases",
    "case_count",
    "reviewed_case_count",
    "rating_row_count",
    "family_coverage_satisfied",
    "axis_targets_satisfied",
    "red_case_count",
    "repair_required_case_count",
    "open_blocker_ids",
    "open_execution_blocker_ids",
    "boundary_violation_blocker_ids",
    "disposal_status",
    "body_removed",
    "reviewer_notes_removed",
    "local_packet_exported",
    "content_hash_of_body_stored",
    "disposal_verified_for_candidate",
    "required_condition_refs",
    "missing_requirement_refs",
    "failed_requirement_count",
    "handoff_summary_candidate_claim",
    "p5_confirmed_candidate_gate_passed",
    "p5_human_blind_qa_confirmed_candidate",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p5_human_blind_qa_confirmed",
    "p6_limited_human_readfeel_start_allowed",
    "p6_limited_human_readfeel_confirmed",
    "real_device_modal_review_start_allowed",
    "real_device_modal_review_confirmed",
    "actual_human_review_run_here",
    "actual_disposal_run_here",
    "actual_disposal_receipt_materialized_here",
    "actual_body_full_packet_generated_here",
    "body_full_writer_created_here",
    "local_reviewer_payload_materialized_here",
    "public_contract",
    "body_free_markers",
    "body_free",
    "release_allowed",
    "p7_complete",
    "p8_start_allowed",
    "hold004_close_allowed",
    "full_backend_suite_green_confirmed",
    "release_readiness_claim_allowed",
    "p7_completion_claim_allowed",
    "p8_start_claim_allowed",
    "full_backend_suite_green_claim_allowed",
)
P7_R48_R47_TARGET_REGRESSION_TEST_REFS: Final[tuple[str, ...]] = (
    "tests/test_emlis_ai_p7_r47_local_review_packet_policy_r0_r1_20260618.py",
    "tests/test_emlis_ai_p7_r47_local_review_packet_policy_r2_r3_20260618.py",
    "tests/test_emlis_ai_p7_r47_local_review_packet_policy_r4_r5_20260618.py",
    "tests/test_emlis_ai_p7_r47_local_review_packet_policy_r6_r7_20260618.py",
    "tests/test_emlis_ai_p7_r47_local_review_packet_policy_r8_r9_20260618.py",
    "tests/test_emlis_ai_p7_r47_local_review_packet_policy_r10_r11_20260618.py",
    "tests/test_emlis_ai_p7_r47_local_review_packet_policy_r12_r13_20260618.py",
    "tests/test_emlis_ai_p7_r47_local_review_packet_policy_r14_r15_20260618.py",
)
P7_R48_R46_HANDOFF_REGRESSION_TEST_REFS: Final[tuple[str, ...]] = (
    "tests/test_emlis_ai_p7_r46_p5_p6_human_readfeel_handoff_material_r10_r11_20260617.py",
    "tests/test_emlis_ai_p7_r46_real_device_modal_review_closed_validation_r12_r13_20260617.py",
    "tests/test_emlis_ai_p7_r46_next_decision_handoff_ledger_r14_20260617.py",
)
P7_R48_P5_CORE_SUBSET_REGRESSION_TEST_REFS: Final[tuple[str, ...]] = (
    "tests/test_emlis_ai_user_label_connection_material.py",
    "tests/test_emlis_ai_user_label_connection_candidate.py",
    "tests/test_emlis_ai_user_label_connection_gate.py",
    "tests/test_emlis_ai_user_label_connection_surface.py",
    "tests/test_emlis_ai_user_label_connection_public_boundary.py",
    "tests/test_emlis_ai_user_label_connection_e2e_contract.py",
)
P7_R48_P5_PRODUCT_QUALITY_QA_OPTIONAL_REGRESSION_TEST_REFS: Final[tuple[str, ...]] = (
    "tests/test_emlis_ai_user_label_connection_product_quality_qa.py",
)
P7_R48_DISPLAY_CONTRACT_REGRESSION_TEST_REFS: Final[tuple[str, ...]] = (
    "tests/test_emlis_ai_display_contract.py",
)
P7_R48_RN_CONTRACT_OPTIONAL_TEST_REFS: Final[tuple[str, ...]] = (
    "Cocolon/tests/rn-screen-contracts.test.js",
)
P7_R48_RN_PRODUCTION_NO_TOUCH_FILE_REFS: Final[tuple[str, ...]] = (
    "Cocolon/screens/InputScreen.js",
    "Cocolon/screens/input/useInputFeedbackModal.js",
    "Cocolon/screens/input/inputFeedbackModel.js",
    "Cocolon/screens/input/InputFeedbackReplyModal.js",
)
P7_R48_RN_CONTRACT_COMMAND_REFS: Final[tuple[str, ...]] = (
    "cd Cocolon && npm run test:rn-screens --silent",
)
P7_R48_PRODUCTION_TOUCH_CANDIDATE_FILE_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet.py",
)
P7_R48_OPTIONAL_TOUCH_CANDIDATE_FILE_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r48_local_review_file_ops.py",
    "docs/Cocolon_EmlisAI_P7_R48_P5HumanBlindQAActualReviewPacket_20260618.md",
)
P7_R48_EXPLICIT_NO_TOUCH_AREA_REFS: Final[tuple[str, ...]] = (
    "rn_production_files",
    "rn_contract_test_files",
    "api_route_files",
    "db_schema_migration_files",
    "emlis_reply_runtime",
    "public_feedback_meta",
    "body_free_public_source_lineage",
    "runtime_gate_threshold_files",
    "release_material_files",
    "existing_user_facing_surface_composer_runtime",
)
P7_R48_EXPLICIT_NO_TOUCH_FILE_REFS: Final[tuple[str, ...]] = (
    *P7_R48_RN_PRODUCTION_NO_TOUCH_FILE_REFS,
    *P7_R48_RN_CONTRACT_OPTIONAL_TEST_REFS,
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
)
P7_R48_R18_CURRENT_PATCH_EXPECTED_TOUCHED_FILE_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet.py",
    "tests/test_emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet_r18_20260619.py",
)
P7_R48_R48_TARGET_TEST_REFS: Final[tuple[str, ...]] = (
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
P7_R48_ALLOWED_PRODUCTION_TOUCH_FILE_REFS: Final[tuple[str, ...]] = (
    *P7_R48_PRODUCTION_TOUCH_CANDIDATE_FILE_REFS,
    *P7_R48_OPTIONAL_TOUCH_CANDIDATE_FILE_REFS,
)
P7_R48_ALLOWED_TEST_TOUCH_FILE_REFS: Final[tuple[str, ...]] = P7_R48_R48_TARGET_TEST_REFS
P7_R48_ALLOWED_ACTUAL_TOUCHED_FILE_REFS: Final[tuple[str, ...]] = (
    *P7_R48_ALLOWED_PRODUCTION_TOUCH_FILE_REFS,
    *P7_R48_ALLOWED_TEST_TOUCH_FILE_REFS,
)
P7_R48_VALIDATION_COMMAND_REFS: Final[tuple[str, ...]] = (
    "py_compile",
    "r48_target_tests",
    "r47_target_regression",
    "r46_handoff_regression",
    "display_contract_regression",
    "p5_core_subset_regression",
    "backend_collect_only",
    "rn_contract_optional",
)
P7_R48_VALIDATION_COMMAND_ROW_FIELD_REFS: Final[tuple[str, ...]] = (
    "validation_ref",
    "validation_group",
    "required",
    "optional",
    "working_dir_ref",
    "command_ref",
    "target_refs",
    "executed_here",
    "green_confirmed_here",
    "green_claim_allowed_here",
    "full_backend_suite_green_confirmation",
    "body_free",
)
P7_R48_DISPLAY_CONTRACT_RN_NO_TOUCH_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "r14_r15_regression_freeze_ref",
    "display_contract_regression_required",
    "display_contract_regression_test_refs",
    "display_contract_regression_executed_here",
    "actual_display_contract_regression_executed_here",
    "display_contract_green_confirmed_here",
    "display_contract_green_claim_allowed",
    "rn_no_touch_confirmation_required",
    "rn_contract_optional",
    "rn_contract_test_refs",
    "rn_contract_command_refs",
    "rn_contract_executed_here",
    "actual_rn_contract_executed_here",
    "rn_contract_green_confirmed_here",
    "rn_production_file_refs",
    "rn_contract_changed_here",
    "rn_production_files_touched_here",
    "rn_visible_contract_changed_here",
    "public_response_shape_changed_here",
    "api_response_shape_changed_here",
    "public_response_top_level_key_added_here",
    "db_schema_changed_here",
    "emlis_reply_runtime_changed_here",
    "p5_runtime_changed_here",
    "p5_gate_relaxed_here",
    "p5_human_blind_qa_confirmed",
    "p6_limited_human_readfeel_start_allowed",
    "p6_limited_human_readfeel_confirmed",
    "real_device_modal_review_start_allowed",
    "real_device_modal_review_confirmed",
    "actual_human_review_run_here",
    "actual_body_full_packet_generated_here",
    "body_full_writer_created_here",
    "local_reviewer_payload_materialized_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "body_free_markers",
    "body_free",
    "release_allowed",
    "p7_complete",
    "p8_start_allowed",
    "hold004_close_allowed",
    "full_backend_suite_green_confirmed",
    "release_readiness_claim_allowed",
    "p7_completion_claim_allowed",
    "p8_start_claim_allowed",
    "full_backend_suite_green_claim_allowed",
)
P7_R48_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "r16_r17_validation_no_touch_freeze_ref",
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
    "api_route_changed_here",
    "db_schema_changed_here",
    "db_migration_changed_here",
    "emlis_reply_runtime_changed_here",
    "p5_runtime_changed_here",
    "p5_gate_relaxed_here",
    "release_material_changed_here",
    "p5_human_blind_qa_confirmed",
    "p6_limited_human_readfeel_start_allowed",
    "p6_limited_human_readfeel_confirmed",
    "real_device_modal_review_start_allowed",
    "real_device_modal_review_confirmed",
    "actual_human_review_run_here",
    "actual_body_full_packet_generated_here",
    "body_full_writer_created_here",
    "local_reviewer_payload_materialized_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_disposal_run_here",
    "actual_disposal_receipt_materialized_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "post_r18_next_work_ref",
    "public_contract",
    "body_free_markers",
    "body_free",
    "release_allowed",
    "p7_complete",
    "p8_start_allowed",
    "hold004_close_allowed",
    "full_backend_suite_green_confirmed",
    "release_readiness_claim_allowed",
    "p7_completion_claim_allowed",
    "p8_start_claim_allowed",
    "full_backend_suite_green_claim_allowed",
)
P7_R48_VALIDATION_COMMAND_MATRIX_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "r16_display_contract_rn_no_touch_ref",
    "validation_command_matrix_required",
    "validation_command_refs",
    "validation_command_rows",
    "validation_commands_executed_here",
    "actual_validation_commands_executed_here",
    "r48_target_tests_green_confirmed_here",
    "r47_target_regression_green_confirmed_here",
    "r46_handoff_regression_green_confirmed_here",
    "display_contract_green_confirmed_here",
    "p5_core_subset_green_confirmed_here",
    "backend_collect_only_executed_here",
    "backend_collect_only_green_confirmed_here",
    "backend_collect_only_claimed_as_full_suite_green",
    "full_backend_suite_executed_here",
    "full_backend_suite_green_confirmed_here",
    "rn_contract_optional",
    "rn_contract_executed_here",
    "rn_contract_green_confirmed_here",
    "collect_only_is_full_backend_suite_green",
    "green_unconfirmed_must_not_be_reported_as_green",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "body_free_markers",
    "body_free",
    "release_allowed",
    "p7_complete",
    "p8_start_allowed",
    "hold004_close_allowed",
    "full_backend_suite_green_confirmed",
    "release_readiness_claim_allowed",
    "p7_completion_claim_allowed",
    "p8_start_claim_allowed",
    "full_backend_suite_green_claim_allowed",
)

_R48_RELEASE_CLOSED_KEYS: Final[tuple[str, ...]] = (
    "release_allowed",
    "p7_complete",
    "p8_start_allowed",
    "hold004_close_allowed",
    "full_backend_suite_green_confirmed",
    "release_readiness_claim_allowed",
    "p7_completion_claim_allowed",
    "p8_start_claim_allowed",
    "full_backend_suite_green_claim_allowed",
)
_R48_R0_R1_FALSE_KEYS: Final[tuple[str, ...]] = (
    "r48_policy_ready",
    "p5_human_blind_qa_actual_review_start_allowed_after_r48_r0_r1",
    "p5_human_blind_qa_confirmed",
    "p6_limited_human_readfeel_start_allowed",
    "p6_limited_human_readfeel_confirmed",
    "real_device_modal_review_start_allowed",
    "real_device_modal_review_confirmed",
    "json_schema_file_created_here",
    "actual_case_matrix_materialized_here",
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
    "p5_human_blind_qa_confirmed_candidate",
    "p6_limited_human_readfeel_start_allowed_candidate",
)
_R48_R2_R3_FALSE_KEYS: Final[tuple[str, ...]] = (
    "r48_policy_ready",
    "p5_human_blind_qa_actual_review_start_allowed_after_r2",
    "p5_human_blind_qa_actual_review_start_allowed_after_r2_r3",
    "p5_human_blind_qa_confirmed",
    "p6_limited_human_readfeel_start_allowed",
    "p6_limited_human_readfeel_confirmed",
    "real_device_modal_review_start_allowed",
    "real_device_modal_review_confirmed",
    "json_schema_file_created_here",
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
    "p5_human_blind_qa_confirmed_candidate",
    "p6_limited_human_readfeel_start_allowed_candidate",
)
_R48_R4_R5_FALSE_KEYS: Final[tuple[str, ...]] = (
    "r48_policy_ready",
    "p5_human_blind_qa_actual_review_start_allowed_after_r4_r5",
    "p5_human_blind_qa_confirmed",
    "p6_limited_human_readfeel_start_allowed",
    "p6_limited_human_readfeel_confirmed",
    "real_device_modal_review_start_allowed",
    "real_device_modal_review_confirmed",
    "json_schema_file_created_here",
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
    "p5_human_blind_qa_confirmed_candidate",
    "p6_limited_human_readfeel_start_allowed_candidate",
)
_R48_R6_R7_FALSE_KEYS: Final[tuple[str, ...]] = (
    "r48_policy_ready",
    "p5_human_blind_qa_actual_review_start_allowed_after_r6_r7",
    "p5_human_blind_qa_confirmed",
    "p6_limited_human_readfeel_start_allowed",
    "p6_limited_human_readfeel_confirmed",
    "real_device_modal_review_start_allowed",
    "real_device_modal_review_confirmed",
    "json_schema_file_created_here",
    "actual_body_full_packet_generated_here",
    "body_full_writer_created_here",
    "local_reviewer_payload_materialized_here",
    "actual_human_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_reviewer_notes_materialized_here",
    "actual_notes_materialized_here",
    "actual_disposal_run_here",
    "actual_disposal_receipt_materialized_here",
    "p5_human_blind_qa_confirmed_candidate",
    "p6_limited_human_readfeel_start_allowed_candidate",
)
_R48_R8_R9_FALSE_KEYS: Final[tuple[str, ...]] = (
    *_R48_R6_R7_FALSE_KEYS,
    "p5_human_blind_qa_actual_review_start_allowed_after_r8_r9",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "p5_human_blind_qa_confirmed_candidate",
    "p6_limited_human_readfeel_start_allowed_candidate",
)
_R48_R10_R11_FALSE_KEYS: Final[tuple[str, ...]] = (
    *_R48_R8_R9_FALSE_KEYS,
    "p5_human_blind_qa_actual_review_start_allowed_after_r10_r11",
    "actual_disposal_run_here",
    "actual_disposal_receipt_materialized_here",
    "actual_review_handoff_summary_materialized_here",
    "p5_human_blind_qa_confirmed",
    "p6_limited_human_readfeel_start_allowed",
    "p6_limited_human_readfeel_confirmed",
)
_R48_R12_R13_FALSE_KEYS: Final[tuple[str, ...]] = (
    *_R48_R10_R11_FALSE_KEYS,
    "p5_human_blind_qa_actual_review_start_allowed_after_r12_r13",
    "actual_p5_confirmed_candidate_gate_materialized_here",
    "actual_r47_regression_executed_here",
    "actual_no_body_free_leak_scan_executed_here",
    "p5_human_blind_qa_confirmed",
    "p6_limited_human_readfeel_start_allowed",
    "p6_limited_human_readfeel_confirmed",
)
_R48_R14_R15_FALSE_KEYS: Final[tuple[str, ...]] = (
    *_R48_R12_R13_FALSE_KEYS,
    "p5_human_blind_qa_actual_review_start_allowed_after_r14",
    "p5_human_blind_qa_actual_review_start_allowed_after_r15",
    "r46_handoff_regression_executed_here",
    "actual_r46_handoff_regression_executed_here",
    "p5_core_subset_regression_executed_here",
    "actual_p5_core_subset_regression_executed_here",
    "p5_core_subset_green_confirmed_here",
    "p5_core_subset_green_claim_allowed",
    "p5_runtime_changed_here",
    "p5_gate_relaxed_here",
    "api_response_shape_changed_here",
    "db_schema_changed_here",
    "emlis_reply_runtime_changed_here",
)
_R48_R16_R17_FALSE_KEYS: Final[tuple[str, ...]] = (
    *_R48_R14_R15_FALSE_KEYS,
    "display_contract_regression_executed_here",
    "actual_display_contract_regression_executed_here",
    "display_contract_green_confirmed_here",
    "display_contract_green_claim_allowed",
    "rn_contract_executed_here",
    "actual_rn_contract_executed_here",
    "rn_contract_green_confirmed_here",
    "rn_contract_changed_here",
    "rn_production_files_touched_here",
    "rn_visible_contract_changed_here",
    "public_response_shape_changed_here",
    "public_response_top_level_key_added_here",
    "validation_commands_executed_here",
    "actual_validation_commands_executed_here",
    "r48_target_tests_green_confirmed_here",
    "r47_target_regression_green_confirmed_here",
    "r46_handoff_regression_green_confirmed_here",
    "backend_collect_only_executed_here",
    "backend_collect_only_green_confirmed_here",
    "backend_collect_only_claimed_as_full_suite_green",
    "full_backend_suite_executed_here",
    "full_backend_suite_green_confirmed_here",
    "collect_only_is_full_backend_suite_green",
)
_R48_R18_FALSE_KEYS: Final[tuple[str, ...]] = (
    *_R48_R16_R17_FALSE_KEYS,
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
    "api_route_changed_here",
    "db_schema_changed_here",
    "db_migration_changed_here",
    "emlis_reply_runtime_changed_here",
    "p5_runtime_changed_here",
    "p5_gate_relaxed_here",
    "release_material_changed_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_disposal_run_here",
    "actual_disposal_receipt_materialized_here",
)
_R48_LOCAL_REVIEW_BODY_KEYS: Final[frozenset[str]] = frozenset(
    {
        "current_input_review_surface",
        "returned_emlis_surface",
        "bounded_owned_history_review_surface",
        "reviewer_free_text",
        "reviewer_note",
        "reviewer_notes",
        "raw_input",
        "comment_text",
        "candidate_body",
        "surface_body",
        "history_raw_text",
        "raw_history_dump",
        "review_surface",
        "visible_surface",
        "terminal_output",
        "stdout",
        "stderr",
        "traceback",
        "body_content_hash",
        "raw_text_hash",
        "comment_text_hash",
        "body_full_file_content_hash",
        "deleted_body_preview",
        "local_absolute_path",
    }
)
P7_R48_BODY_FREE_LEAK_GUARD_FORBIDDEN_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        [
            *_R48_LOCAL_REVIEW_BODY_KEYS,
            "reviewer_packet",
            "local_reviewer_packet",
            "local_only_reviewer_packet",
            "body_full_packet",
            "body_full_packets",
            "reviewer_payload",
            "local_packet_payload",
            "reviewer_notes_payload",
            "review_questions",
            "axis_rating_form",
        ]
    )
)


def _contains_r48_local_review_body_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(
            str(key) in _R48_LOCAL_REVIEW_BODY_KEYS or _contains_r48_local_review_body_key(child)
            for key, child in value.items()
        )
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_r48_local_review_body_key(child) for child in value)
    return False


def _assert_r48_body_free(value: Any, *, source: str) -> None:
    if _contains_r48_local_review_body_key(value):
        raise ValueError(f"{source} contains local-only P5 review body payload keys")
    assert_p7_no_body_payload_or_contract_mutation(value, source=source)


def _body_free_markers() -> dict[str, bool]:
    return body_free_flags(include_history=True, include_reviewer=True, include_terminal=True)


def _release_closed_flags() -> dict[str, bool]:
    return {key: False for key in _R48_RELEASE_CLOSED_KEYS}


def _r0_r1_false_flags() -> dict[str, bool]:
    return {key: False for key in _R48_R0_R1_FALSE_KEYS}


def _r2_r3_false_flags() -> dict[str, bool]:
    return {key: False for key in _R48_R2_R3_FALSE_KEYS}


def _r4_r5_false_flags() -> dict[str, bool]:
    return {key: False for key in _R48_R4_R5_FALSE_KEYS}


def _r6_r7_false_flags() -> dict[str, bool]:
    return {key: False for key in _R48_R6_R7_FALSE_KEYS}


def _r8_r9_false_flags() -> dict[str, bool]:
    return {key: False for key in _R48_R8_R9_FALSE_KEYS}


def _r10_r11_false_flags() -> dict[str, bool]:
    return {key: False for key in _R48_R10_R11_FALSE_KEYS}


def _r12_r13_false_flags() -> dict[str, bool]:
    return {key: False for key in _R48_R12_R13_FALSE_KEYS}


def _r14_r15_false_flags() -> dict[str, bool]:
    return {key: False for key in _R48_R14_R15_FALSE_KEYS}


def _r16_r17_false_flags() -> dict[str, bool]:
    return {key: False for key in _R48_R16_R17_FALSE_KEYS}


def _safe_snapshot_refs(snapshot_refs: Mapping[str, Any] | None) -> dict[str, str]:
    merged: dict[str, str] = dict(P7_R48_RECEIVED_LOCAL_SNAPSHOT_REFS)
    if snapshot_refs is None:
        return merged
    _assert_r48_body_free(snapshot_refs, source="p7_r48.snapshot_refs")
    for key, value in safe_mapping(snapshot_refs).items():
        clean_key = clean_identifier(key, default="snapshot_ref", max_length=120)
        if clean_key:
            merged[clean_key] = clean_identifier(value, default="unknown", max_length=180)
    return merged


def _r47_policy_freeze(r47_policy_freeze: Mapping[str, Any] | None) -> dict[str, Any]:
    freeze = (
        safe_mapping(r47_policy_freeze)
        if r47_policy_freeze is not None
        else build_p7_r47_r14_r15_validation_touch_boundary_freeze()
    )
    assert_p7_r47_r14_r15_validation_touch_boundary_freeze_contract(freeze)
    if r47_policy_freeze is not None:
        _assert_r48_body_free(freeze, source="p7_r48.r47_policy_freeze")
    return freeze


def _r47_handoff(freeze: Mapping[str, Any]) -> dict[str, Any]:
    if freeze.get("r47_policy_ready") is not True:
        raise ValueError("R48 R0 requires R47 policy ready before P5 actual review packet work")
    if freeze.get("p5_human_blind_qa_start_allowed_after_policy") is not True:
        raise ValueError("R48 R0 requires the R47 P5 start-after-policy gate to be open")
    if freeze.get("p5_human_blind_qa_confirmed") is not False:
        raise ValueError("R48 R0 must not receive P5 as already confirmed")
    for key in (
        "p6_limited_human_readfeel_start_allowed",
        "p6_limited_human_readfeel_confirmed",
        "real_device_modal_review_start_allowed",
        "real_device_modal_review_confirmed",
        "release_allowed",
        "p7_complete",
        "p8_start_allowed",
        "hold004_close_allowed",
        "full_backend_suite_execution_green_confirmed",
    ):
        if freeze.get(key) is not False:
            raise ValueError(f"R48 R0 requires R47 handoff to keep {key}=False")
    if freeze.get("next_required_step") != P7_R47_R14_R15_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R48 R0 requires R47 to point to P5 human Blind QA next")

    return {
        "r47_schema_version": clean_identifier(
            freeze.get("schema_version"),
            default=P7_R47_R14_R15_VALIDATION_TOUCH_BOUNDARY_SCHEMA_VERSION,
            max_length=180,
        ),
        "r47_policy_schema_version": P7_R47_LOCAL_REVIEW_PACKET_POLICY_SCHEMA_VERSION,
        "r47_policy_ready": True,
        "local_review_packet_policy_ready": True,
        "policy_ready": True,
        "r47_next_required_step": clean_identifier(freeze.get("next_required_step"), default="unknown", max_length=160),
        "p5_human_blind_qa_start_allowed_after_r47_policy": True,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "real_device_modal_review_start_allowed": False,
        "real_device_modal_review_confirmed": False,
        "release_allowed": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "hold004_close_allowed": False,
        "body_free": True,
    }


def _hold_state() -> dict[str, Any]:
    unresolved = dedupe_identifiers(
        [*P7_R47_REQUIRED_UNRESOLVED_HOLD_REFS, *P7_R48_REQUIRED_UNRESOLVED_HOLD_REFS],
        limit=120,
        max_length=120,
    )
    return {
        "unresolved_hold_refs": unresolved,
        "required_unresolved_hold_refs": list(P7_R48_REQUIRED_UNRESOLVED_HOLD_REFS),
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "real_device_modal_review_start_allowed": False,
        "real_device_modal_review_confirmed": False,
        "full_backend_suite_green_confirmed": False,
        "p7_hold004_close_allowed": False,
        "body_full_review_packet_generated": False,
        "body_free_case_matrix_ready": False,
        "body_free_rating_rows_ready": False,
        "disposal_receipt_verified": False,
        "body_removed_verified": False,
        "release_allowed": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "hold004_close_allowed": False,
        "body_free": True,
    }


def build_p7_r48_current_source_r47_handoff_hold_refreeze(
    *,
    snapshot_refs: Mapping[str, Any] | None = None,
    r47_policy_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r48_current_source_r47_handoff_hold_refreeze",
) -> dict[str, Any]:
    """Build the R48 R0 body-free current-source/R47-handoff/HOLD refreeze."""

    r47 = _r47_policy_freeze(r47_policy_freeze)
    refreeze = {
        "schema_version": P7_R48_CURRENT_SOURCE_R47_HANDOFF_HOLD_REFREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R48_STEP,
        "scope": P7_R48_SCOPE,
        "policy_kind": P7_R48_POLICY_KIND,
        "material_id": clean_identifier(material_id, default="p7_r48_current_source_r47_handoff_hold_refreeze", max_length=160),
        "freeze_kind": "current_source_r47_handoff_hold_refreeze",
        "current_phase": "P7",
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": P7_GIT_CHECKED,
        "source_snapshot_refs": _safe_snapshot_refs(snapshot_refs),
        "r47_handoff": _r47_handoff(r47),
        "hold_state": _hold_state(),
        "first_next_work_ref": P7_R48_FIRST_NEXT_WORK_REF,
        "next_required_step": "R1_scope_schema_version_packet_kind_freeze",
        "r0_current_source_r47_handoff_hold_refrozen": True,
        "r1_scope_schema_packet_kind_fixed": False,
        "p5_human_blind_qa_start_allowed_after_r47_policy": True,
        "p5_human_blind_qa_actual_review_started_here": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
        **_r0_r1_false_flags(),
    }
    assert_p7_r48_current_source_r47_handoff_hold_refreeze_contract(refreeze)
    return refreeze


def _safe_packet_kind(packet_kind: Any | None) -> str:
    value = clean_identifier(packet_kind, default=P7_R48_PACKET_KIND, max_length=120)
    if value != P7_R48_PACKET_KIND:
        raise ValueError("R48 R1 packet_kind must remain p5_human_blind_qa_local_review_packet")
    if value not in P7_R47_PACKET_KIND_SET:
        raise ValueError("R48 R1 packet_kind must remain inherited from the R47 packet kind enum")
    return value


def _safe_review_kind(review_kind: Any | None) -> str:
    value = clean_identifier(review_kind, default=P7_R48_REVIEW_KIND, max_length=120)
    if value != P7_R48_REVIEW_KIND or value != P7_R47_P5_REVIEW_KIND:
        raise ValueError("R48 R1 review_kind must remain p5_history_line_readfeel")
    return value


def build_p7_r48_scope_schema_packet_kind_freeze(
    *,
    packet_kind: Any | None = None,
    review_kind: Any | None = None,
    current_source_refreeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r48_scope_schema_packet_kind_freeze",
) -> dict[str, Any]:
    """Build the R48 R1 body-free scope/schema-version/packet-kind freeze."""

    r0 = (
        safe_mapping(current_source_refreeze)
        if current_source_refreeze is not None
        else build_p7_r48_current_source_r47_handoff_hold_refreeze()
    )
    assert_p7_r48_current_source_r47_handoff_hold_refreeze_contract(r0)
    if current_source_refreeze is not None:
        _assert_r48_body_free(r0, source="p7_r48.current_source_refreeze")

    fixed_packet_kind = _safe_packet_kind(packet_kind)
    fixed_review_kind = _safe_review_kind(review_kind)
    freeze = {
        "schema_version": P7_R48_SCOPE_SCHEMA_PACKET_KIND_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R48_STEP,
        "scope": P7_R48_SCOPE,
        "policy_kind": P7_R48_POLICY_KIND,
        "material_id": clean_identifier(material_id, default="p7_r48_scope_schema_packet_kind_freeze", max_length=160),
        "freeze_kind": "scope_schema_version_packet_kind_freeze",
        "current_phase": "P7",
        "source_mode": clean_identifier(r0.get("source_mode"), default=P7_SOURCE_MODE, max_length=80),
        "git_connection_required": False,
        "git_checked": False,
        "r0_schema_version": P7_R48_CURRENT_SOURCE_R47_HANDOFF_HOLD_REFREEZE_SCHEMA_VERSION,
        "r0_material_ref": clean_identifier(r0.get("material_id"), default="p7_r48_current_source_r47_handoff_hold_refreeze", max_length=160),
        "r47_handoff_schema_version": safe_mapping(r0.get("r47_handoff")).get("r47_schema_version"),
        "r48_policy_schema_version": P7_R48_P5_REVIEW_POLICY_SCHEMA_VERSION,
        "case_matrix_schema_version": P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION,
        "reviewer_packet_local_only_schema_version": P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION,
        "rating_row_bodyfree_schema_version": P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION,
        "execution_blocker_row_bodyfree_schema_version": P7_R48_P5_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "disposal_receipt_bodyfree_schema_version": P7_R48_P5_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION,
        "review_handoff_summary_bodyfree_schema_version": P7_R48_P5_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION,
        "r47_local_review_root_env_var": P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR,
        "r47_p5_first_formal_minimums": dict(P7_R47_P5_FIRST_FORMAL_MINIMUMS),
        "r47_p5_history_surface_policy": dict(P7_R47_P5_HISTORY_SURFACE_POLICY),
        "r47_p5_reviewer_facing_allowed_field_refs": list(P7_R47_P5_REVIEWER_FACING_ALLOWED_FIELD_REFS),
        "r47_p5_reviewer_facing_forbidden_field_refs": list(P7_R47_P5_REVIEWER_FACING_FORBIDDEN_FIELD_REFS),
        "r47_disposal_status_refs": list(P7_R47_DISPOSAL_STATUSES),
        "r47_body_full_packet_retention_hours": P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
        "r47_reviewer_notes_retention_after_rating_hours": P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
        "r47_disposal_receipt_schema_version_ref": P7_R47_BODY_FREE_DISPOSAL_RECEIPT_SCHEMA_VERSION,
        "p5_human_blind_qa_families": list(P5_HUMAN_BLIND_QA_FAMILIES),
        "p5_human_blind_qa_rating_axes": list(P5_HUMAN_BLIND_QA_RATING_AXES),
        "p5_human_blind_qa_target_thresholds": dict(P5_HUMAN_BLIND_QA_TARGETS),
        "r48_scope_fixed": True,
        "r48_schema_versions_fixed": True,
        "packet_kind_fixed": True,
        "review_kind_fixed": True,
        "packet_kind": fixed_packet_kind,
        "review_kind": fixed_review_kind,
        "packet_policy": {
            "packet_kind": fixed_packet_kind,
            "review_kind": fixed_review_kind,
            "p5_actual_review_packet_lane_only": True,
            "p6_limited_human_readfeel_in_scope": False,
            "real_device_modal_review_in_scope": False,
            "release_decision_in_scope": False,
            "local_only_required_later": True,
            "body_full_payload_allowed_only_later_with_valid_local_root_and_explicit_allow": True,
            "materialized_here": False,
            "writer_created_here": False,
            "standard_export_allowed": False,
            "public_meta_material_allowed": False,
            "p7_scorecard_body_full_material_allowed": False,
            "release_material_allowed": False,
            "body_free_result_required_later": True,
            "body_free": True,
        },
        "implemented_steps": list(P7_R48_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R48_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R48_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R48_NEXT_REQUIRED_STEP_REF,
        "r0_current_source_r47_handoff_hold_refrozen": True,
        "r1_scope_schema_packet_kind_fixed": True,
        "p5_human_blind_qa_start_allowed_after_r47_policy": True,
        "p5_human_blind_qa_actual_review_started_here": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
        **_r0_r1_false_flags(),
    }
    assert_p7_r48_scope_schema_packet_kind_freeze_contract(freeze)
    return freeze


def build_p7_r48_r0_r1_scope_freeze(
    *,
    snapshot_refs: Mapping[str, Any] | None = None,
    r47_policy_freeze: Mapping[str, Any] | None = None,
    packet_kind: Any | None = None,
    review_kind: Any | None = None,
    material_id: Any = "p7_r48_r0_r1_scope_freeze",
) -> dict[str, Any]:
    """Build a compact body-free combined R48 R0/R1 summary."""

    r0 = build_p7_r48_current_source_r47_handoff_hold_refreeze(
        snapshot_refs=snapshot_refs,
        r47_policy_freeze=r47_policy_freeze,
    )
    r1 = build_p7_r48_scope_schema_packet_kind_freeze(
        packet_kind=packet_kind,
        review_kind=review_kind,
        current_source_refreeze=r0,
    )
    combined = {
        "schema_version": P7_R48_R0_R1_SCOPE_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R48_STEP,
        "scope": P7_R48_SCOPE,
        "policy_kind": P7_R48_POLICY_KIND,
        "material_id": clean_identifier(material_id, default="p7_r48_r0_r1_scope_freeze", max_length=160),
        "freeze_kind": "r0_r1_scope_freeze",
        "current_phase": "P7",
        "implemented_steps": list(P7_R48_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R48_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_refreeze": r0,
        "r1_scope_schema_packet_kind_freeze": r1,
        "first_next_work_ref": P7_R48_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R48_NEXT_REQUIRED_STEP_REF,
        "packet_kind": P7_R48_PACKET_KIND,
        "review_kind": P7_R48_REVIEW_KIND,
        "r0_current_source_r47_handoff_hold_refrozen": True,
        "r1_scope_schema_packet_kind_fixed": True,
        "p5_human_blind_qa_start_allowed_after_r47_policy": True,
        "p5_human_blind_qa_actual_review_started_here": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
        **_r0_r1_false_flags(),
    }
    assert_p7_r48_r0_r1_scope_freeze_contract(combined)
    return combined


def _r48_generation_block_reason_ids(
    *,
    r47_reasons: Sequence[Any] | None,
    local_root_valid: bool,
    explicit_allow: bool,
) -> list[str]:
    r47_reason_set = set(dedupe_identifiers(r47_reasons, limit=30, max_length=160))
    reasons: list[str] = []
    if not local_root_valid:
        if "local_review_root_not_configured" in r47_reason_set:
            reasons.append("review_packet_generation_blocked_missing_local_root")
        else:
            reasons.append("review_packet_generation_blocked_invalid_local_root")
        if any(
            reason in r47_reason_set
            for reason in (
                "local_review_root_under_repo_root",
                "local_review_root_under_export_root",
                "local_review_root_under_mnt_data_artifact_root",
                "local_review_root_contains_repo_or_git_component",
                "local_review_root_contains_forbidden_name_fragment",
            )
        ):
            reasons.append("review_packet_generation_blocked_repo_or_artifact_root")
    if local_root_valid and not explicit_allow:
        reasons.append(P7_R48_EXPLICIT_ALLOW_BLOCK_REASON_REF)
    return dedupe_identifiers(reasons, limit=12, max_length=160)


def build_p7_r48_local_storage_root_policy(
    *,
    local_review_root: Any = None,
    repo_roots: Sequence[Any] | None = None,
    export_roots: Sequence[Any] | None = None,
    explicit_body_full_generation_allow: bool = False,
    r0_r1_scope_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r48_local_storage_root_policy",
) -> dict[str, Any]:
    """Build the R48 R2 body-free local storage root policy connection."""

    r0_r1 = (
        safe_mapping(r0_r1_scope_freeze)
        if r0_r1_scope_freeze is not None
        else build_p7_r48_r0_r1_scope_freeze()
    )
    assert_p7_r48_r0_r1_scope_freeze_contract(r0_r1)
    if r0_r1_scope_freeze is not None:
        _assert_r48_body_free(r0_r1, source="p7_r48.r0_r1_scope_freeze")

    r47_storage = build_p7_r47_local_review_storage_root_policy(
        local_review_root=local_review_root,
        repo_roots=repo_roots,
        export_roots=export_roots,
    )
    assert_p7_r47_local_review_storage_root_policy_contract(r47_storage)
    _assert_r48_body_free(r47_storage, source="p7_r48.r47_storage_root_policy")

    root_status = clean_identifier(r47_storage.get("local_review_root_status"), default="missing", max_length=40)
    local_root_valid = root_status == "valid" and r47_storage.get("local_body_packet_generation_allowed") is True
    explicit_allow = explicit_body_full_generation_allow is True
    generation_block_reasons = _r48_generation_block_reason_ids(
        r47_reasons=r47_storage.get("generation_block_reason_ids"),
        local_root_valid=local_root_valid,
        explicit_allow=explicit_allow,
    )
    generation_allowed = local_root_valid and explicit_allow

    policy = {
        "schema_version": P7_R48_LOCAL_STORAGE_ROOT_POLICY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R48_STEP,
        "scope": P7_R48_SCOPE,
        "policy_kind": P7_R48_POLICY_KIND,
        "policy_section": "R2_local_storage_root_policy",
        "material_id": clean_identifier(material_id, default="p7_r48_local_storage_root_policy", max_length=160),
        "current_phase": "P7",
        "r0_r1_schema_version": P7_R48_R0_R1_SCOPE_FREEZE_SCHEMA_VERSION,
        "r0_r1_material_ref": clean_identifier(r0_r1.get("material_id"), default="p7_r48_r0_r1_scope_freeze", max_length=160),
        "r47_storage_root_policy_schema_version": P7_R47_LOCAL_REVIEW_STORAGE_ROOT_POLICY_SCHEMA_VERSION,
        "r47_storage_root_policy": r47_storage,
        "storage_mode": P7_R48_STORAGE_MODE_EXTERNAL_LOCAL_ONLY,
        "env_var": P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR,
        "local_review_root_source": clean_identifier(r47_storage.get("local_review_root_source"), default="missing", max_length=80),
        "local_review_root_configured": r47_storage.get("local_review_root_configured") is True,
        "local_review_root_status": root_status,
        "local_review_root_valid": local_root_valid,
        "storage_root_ref": P7_R48_STORAGE_ROOT_REF if local_root_valid else "not_configured_or_invalid",
        "session_storage_ref": "p7_r48_review_session_root" if local_root_valid else "not_configured_or_invalid",
        "root_path_exposed": False,
        "local_absolute_path_included": False,
        "repo_local_storage_allowed": False,
        "artifact_export_path_allowed": False,
        "docs_tests_services_storage_allowed": False,
        "premise_storage_allowed": False,
        "implemented_docs_storage_allowed": False,
        "mnt_data_artifact_storage_allowed": False,
        "git_tracked_path_storage_allowed": False,
        "body_full_generation_requires_env_root": True,
        "body_full_generation_requires_explicit_allow": True,
        "explicit_body_full_generation_allow": explicit_allow,
        "local_root_body_packet_generation_allowed_by_root_policy": local_root_valid,
        "local_body_packet_generation_allowed": generation_allowed,
        "body_full_generation_allowed_after_r2": generation_allowed,
        "generation_block_reason_ids": [] if generation_allowed else generation_block_reasons,
        "recommended_layout_refs": [
            "p7_r48/{review_session_id}/controller_manifest.bodyfree.json",
            "p7_r48/{review_session_id}/case_matrix.bodyfree.json",
            "p7_r48/{review_session_id}/body_full_packets.local_only/{blind_case_id}.p5_review_packet.local_only.json",
            "p7_r48/{review_session_id}/reviewer_notes.local_only/{blind_case_id}.reviewer_notes.local_only.json",
            "p7_r48/{review_session_id}/body_free_results/rating_rows.bodyfree.jsonl",
            "p7_r48/{review_session_id}/body_free_results/blocker_rows.bodyfree.jsonl",
            "p7_r48/{review_session_id}/body_free_results/execution_blocker_rows.bodyfree.jsonl",
            "p7_r48/{review_session_id}/body_free_results/disposal_receipt.bodyfree.json",
            "p7_r48/{review_session_id}/body_free_results/p5_human_blind_qa_handoff_summary.bodyfree.json",
            "p7_r48/{review_session_id}/audit.bodyfree/no_body_payload_scan.bodyfree.json",
        ],
        "body_full_packets_local_only_dir_ref": "body_full_packets.local_only",
        "reviewer_notes_local_only_dir_ref": "reviewer_notes.local_only",
        "body_free_results_dir_ref": "body_free_results",
        "audit_bodyfree_dir_ref": "audit.bodyfree",
        "r0_current_source_r47_handoff_hold_refrozen": True,
        "r1_scope_schema_packet_kind_fixed": True,
        "local_storage_root_policy_connected": True,
        "body_free_case_matrix_ready": False,
        "actual_case_matrix_materialized_here": False,
        "p5_human_blind_qa_start_allowed_after_r47_policy": True,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
        **_r2_r3_false_flags(),
    }
    assert_p7_r48_local_storage_root_policy_contract(policy)
    return policy


def _safe_review_session_id(value: Any) -> str:
    return clean_identifier(value, default=P7_R48_REVIEW_SESSION_DEFAULT_REF, max_length=120)


def _safe_session_short_ref(value: Any) -> str:
    raw = clean_identifier(value, default=P7_R48_REVIEW_SESSION_DEFAULT_SHORT_REF, max_length=48)
    normalized = "".join(ch.lower() if ch.isalnum() else "-" for ch in raw).strip("-")
    normalized = normalized or P7_R48_REVIEW_SESSION_DEFAULT_SHORT_REF
    forbidden_hints = {
        "free",
        "plus",
        "premium",
        "eligible",
        "expected",
        "gate",
        "history",
        "boundary",
        "low-information",
        "low_information",
        "owned",
        "positive",
        "tier",
        *P5_HUMAN_BLIND_QA_FAMILIES,
    }
    lower = normalized.lower()
    if any(hint.lower().replace("_", "-") in lower for hint in forbidden_hints):
        raise ValueError("R48 blind session short ref must not encode family, tier, expected result, or gate status")
    return normalized[:48]


def _tier_for_case(family: str, ordinal: int) -> str:
    if family == "free_tier_history_present_not_allowed":
        return "free"
    return "plus" if ordinal % 2 else "premium"


def _case_material_status_ref(family: str) -> str:
    if family == "low_information_history_not_eligible":
        return "bodyfree_boundary_low_information_no_history_line"
    if family == "free_tier_history_present_not_allowed":
        return "bodyfree_boundary_free_tier_no_history_line"
    return "bodyfree_positive_owned_history_candidate"


def _expected_boundary_audit_ref(family: str, case_role: str) -> str:
    if family == "low_information_history_not_eligible":
        return "history_line_must_not_apply_low_information"
    if family == "free_tier_history_present_not_allowed":
        return "history_line_must_not_apply_free_tier"
    if case_role == "positive_history_line":
        return "history_line_expected_when_existing_gate_passes"
    return "owned_history_line_expected_when_existing_gate_passes"


def _history_evidence_policy_ref(family: str) -> str:
    if family == "free_tier_history_present_not_allowed":
        return "history_present_but_subscription_boundary_blocks_visible_line"
    if family == "low_information_history_not_eligible":
        return "history_present_but_current_surface_low_information_blocks_overread"
    return "minimum_two_owned_history_records_bounded_to_three_surfaces"


def _build_default_case_rows(*, session_short_ref: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    ordinal = 1
    for family, count, case_role in P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION:
        for _ in range(count):
            suffix = f"{ordinal:03d}"
            rows.append(
                {
                    "case_ref_id": f"p7r48-p5-case-{suffix}",
                    "blind_case_id": f"p7r48-p5-bqa-{session_short_ref}-{suffix}",
                    "packet_ref_id": f"p7r48-p5-packet-{session_short_ref}-{suffix}",
                    "family": family,
                    "case_role": case_role,
                    "subscription_tier_ref": _tier_for_case(family, ordinal),
                    "controller_only": True,
                    "reviewer_facing_family_exposed": False,
                    "reviewer_facing_tier_exposed": False,
                    "expected_boundary_audit_ref": _expected_boundary_audit_ref(family, case_role),
                    "case_material_status_ref": _case_material_status_ref(family),
                    "history_evidence_policy_ref": _history_evidence_policy_ref(family),
                    "body_full_packet_materialized_here": False,
                    "local_reviewer_payload_materialized_here": False,
                    "body_free": True,
                }
            )
            ordinal += 1
    return rows


def _count_by(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = clean_identifier(safe_mapping(row).get(key), default="unknown", max_length=120)
        counts[value] = counts.get(value, 0) + 1
    return counts


def _matrix_minimums_satisfied(rows: Sequence[Mapping[str, Any]]) -> bool:
    minimums = safe_mapping(P7_R47_P5_FIRST_FORMAL_MINIMUMS)
    family_counts = _count_by(rows, "family")
    role_counts = _count_by(rows, "case_role")
    total = len(rows)
    if total < int(minimums.get("minimum_total_cases") or 0):
        return False
    minimum_per_family = int(minimums.get("minimum_per_family") or 0)
    for family in P5_HUMAN_BLIND_QA_FAMILIES:
        if family_counts.get(family, 0) < minimum_per_family:
            return False
    if family_counts.get("history_line_eligible_input", 0) < int(minimums.get("minimum_history_line_eligible_input") or 0):
        return False
    owned_positive = sum(role_counts.get(role, 0) for role in P7_R48_P5_POSITIVE_CASE_ROLE_REFS)
    if owned_positive < int(minimums.get("minimum_owned_history_positive_cases") or 0):
        return False
    block_minimums = safe_mapping(minimums.get("minimum_block_boundary_cases"))
    for family, count in block_minimums.items():
        if family_counts.get(str(family), 0) < int(count):
            return False
    return True


def build_p7_r48_p5_first_formal_review_case_matrix(
    *,
    review_session_id: Any = P7_R48_REVIEW_SESSION_DEFAULT_REF,
    session_short_ref: Any = P7_R48_REVIEW_SESSION_DEFAULT_SHORT_REF,
    local_storage_policy: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r48_p5_first_formal_review_case_matrix",
) -> dict[str, Any]:
    """Build the R48 R3 body-free P5 24-case first formal review matrix."""

    storage = (
        safe_mapping(local_storage_policy)
        if local_storage_policy is not None
        else build_p7_r48_local_storage_root_policy()
    )
    assert_p7_r48_local_storage_root_policy_contract(storage)
    if local_storage_policy is not None:
        _assert_r48_body_free(storage, source="p7_r48.local_storage_policy")

    fixed_session_id = _safe_review_session_id(review_session_id)
    fixed_short_ref = _safe_session_short_ref(session_short_ref)
    rows = _build_default_case_rows(session_short_ref=fixed_short_ref)
    family_counts = _count_by(rows, "family")
    role_counts = _count_by(rows, "case_role")
    tier_counts = _count_by(rows, "subscription_tier_ref")
    minimums_satisfied = _matrix_minimums_satisfied(rows)

    matrix = {
        "schema_version": P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R48_STEP,
        "scope": P7_R48_SCOPE,
        "policy_kind": P7_R48_POLICY_KIND,
        "matrix_kind": "p5_24_case_first_formal_review_matrix",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r48_p5_first_formal_review_case_matrix", max_length=160),
        "review_session_id": fixed_session_id,
        "session_short_ref": fixed_short_ref,
        "packet_kind": P7_R48_PACKET_KIND,
        "review_kind": P7_R48_REVIEW_KIND,
        "review_prompt_version": P7_R48_REVIEW_PROMPT_VERSION,
        "r47_minimums_ref": dict(P7_R47_P5_FIRST_FORMAL_MINIMUMS),
        "r47_history_surface_policy_ref": dict(P7_R47_P5_HISTORY_SURFACE_POLICY),
        "local_storage_policy_ref": clean_identifier(storage.get("material_id"), default="p7_r48_local_storage_root_policy", max_length=160),
        "local_review_root_status": clean_identifier(storage.get("local_review_root_status"), default="missing", max_length=40),
        "local_body_packet_generation_allowed": storage.get("local_body_packet_generation_allowed") is True,
        "case_count": len(rows),
        "case_rows": rows,
        "family_case_counts": family_counts,
        "case_role_counts": role_counts,
        "subscription_tier_ref_counts": tier_counts,
        "owned_history_positive_case_count": sum(role_counts.get(role, 0) for role in P7_R48_P5_POSITIVE_CASE_ROLE_REFS),
        "minimums_satisfied": minimums_satisfied,
        "blind_case_id_policy": {
            "format_ref": "p7r48-p5-bqa-{session_short_ref}-{ordinal_3}",
            "family_tier_expected_gate_not_encoded": True,
            "derived_from_record_or_body_hash": False,
            "controller_case_ref_separated": True,
            "reviewer_facing_uses_blind_case_id_only": True,
            "body_free": True,
        },
        "reviewer_facing_family_exposed": False,
        "reviewer_facing_tier_exposed": False,
        "controller_keeps_family_and_tier_refs": True,
        "body_full_packet_materialized_here": False,
        "local_reviewer_payload_materialized_here": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "body_free_case_matrix_ready": True,
        "actual_case_matrix_materialized_here": True,
        "p5_human_blind_qa_start_allowed_after_r47_policy": True,
        "p5_human_blind_qa_actual_review_start_allowed_after_r2_r3": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
        **_r2_r3_false_flags(),
    }
    assert_p7_r48_p5_first_formal_review_case_matrix_contract(matrix)
    return matrix


def build_p7_r48_r2_r3_local_storage_case_matrix_freeze(
    *,
    local_review_root: Any = None,
    repo_roots: Sequence[Any] | None = None,
    export_roots: Sequence[Any] | None = None,
    explicit_body_full_generation_allow: bool = False,
    review_session_id: Any = P7_R48_REVIEW_SESSION_DEFAULT_REF,
    session_short_ref: Any = P7_R48_REVIEW_SESSION_DEFAULT_SHORT_REF,
    r0_r1_scope_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r48_r2_r3_local_storage_case_matrix_freeze",
) -> dict[str, Any]:
    """Build a compact body-free combined R48 R2/R3 summary."""

    r0_r1 = (
        safe_mapping(r0_r1_scope_freeze)
        if r0_r1_scope_freeze is not None
        else build_p7_r48_r0_r1_scope_freeze()
    )
    assert_p7_r48_r0_r1_scope_freeze_contract(r0_r1)
    if r0_r1_scope_freeze is not None:
        _assert_r48_body_free(r0_r1, source="p7_r48.r0_r1_scope_freeze")

    storage = build_p7_r48_local_storage_root_policy(
        local_review_root=local_review_root,
        repo_roots=repo_roots,
        export_roots=export_roots,
        explicit_body_full_generation_allow=explicit_body_full_generation_allow,
        r0_r1_scope_freeze=r0_r1,
    )
    matrix = build_p7_r48_p5_first_formal_review_case_matrix(
        review_session_id=review_session_id,
        session_short_ref=session_short_ref,
        local_storage_policy=storage,
    )
    combined = {
        "schema_version": P7_R48_R2_R3_LOCAL_STORAGE_CASE_MATRIX_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R48_STEP,
        "scope": P7_R48_SCOPE,
        "policy_kind": P7_R48_POLICY_KIND,
        "material_id": clean_identifier(material_id, default="p7_r48_r2_r3_local_storage_case_matrix_freeze", max_length=160),
        "freeze_kind": "r2_r3_local_storage_case_matrix_freeze",
        "current_phase": "P7",
        "implemented_steps": list(P7_R48_R2_R3_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R48_R2_R3_NOT_YET_IMPLEMENTED_STEPS),
        "r0_r1_scope_freeze": r0_r1,
        "local_storage_policy": storage,
        "p5_case_matrix": matrix,
        "first_next_work_ref": P7_R48_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R48_R2_R3_NEXT_REQUIRED_STEP_REF,
        "packet_kind": P7_R48_PACKET_KIND,
        "review_kind": P7_R48_REVIEW_KIND,
        "review_session_id": matrix["review_session_id"],
        "case_count": matrix["case_count"],
        "minimums_satisfied": matrix["minimums_satisfied"],
        "r0_current_source_r47_handoff_hold_refrozen": True,
        "r1_scope_schema_packet_kind_fixed": True,
        "local_storage_root_policy_connected": True,
        "p5_24_case_first_formal_review_matrix_built": True,
        "body_free_case_matrix_ready": True,
        "actual_case_matrix_materialized_here": True,
        "local_body_packet_generation_allowed": storage.get("local_body_packet_generation_allowed") is True,
        "p5_human_blind_qa_start_allowed_after_r47_policy": True,
        "p5_human_blind_qa_actual_review_start_allowed_after_r2_r3": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
        **_r2_r3_false_flags(),
    }
    assert_p7_r48_r2_r3_local_storage_case_matrix_freeze_contract(combined)
    return combined



def _controller_manifest_rows_from_matrix(matrix: Mapping[str, Any]) -> list[dict[str, Any]]:
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
                "blind_case_id_derived_from_body_or_record_hash": False,
                "body_free": True,
            }
        )
    return rows


def _reviewer_facing_case_index_rows_from_matrix(matrix: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row_raw in safe_mapping(matrix).get("case_rows") or []:
        row = safe_mapping(row_raw)
        rows.append(
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
    return rows


def build_p7_r48_blind_case_id_case_ref_separation(
    *,
    r2_r3_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r48_blind_case_id_case_ref_separation",
) -> dict[str, Any]:
    """Build the R48 R4 body-free blind_case_id / case_ref separation."""

    freeze = (
        safe_mapping(r2_r3_freeze)
        if r2_r3_freeze is not None
        else build_p7_r48_r2_r3_local_storage_case_matrix_freeze()
    )
    assert_p7_r48_r2_r3_local_storage_case_matrix_freeze_contract(freeze)
    if r2_r3_freeze is not None:
        _assert_r48_body_free(freeze, source="p7_r48.r2_r3_freeze")

    matrix = safe_mapping(freeze.get("p5_case_matrix"))
    assert_p7_r48_p5_first_formal_review_case_matrix_contract(matrix)
    controller_rows = _controller_manifest_rows_from_matrix(matrix)
    reviewer_rows = _reviewer_facing_case_index_rows_from_matrix(matrix)
    case_ref_count = len({row["case_ref_id"] for row in controller_rows})
    blind_case_count = len({row["blind_case_id"] for row in controller_rows})

    separation = {
        "schema_version": P7_R48_BLIND_CASE_ID_CASE_REF_SEPARATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R48_STEP,
        "scope": P7_R48_SCOPE,
        "policy_kind": P7_R48_POLICY_KIND,
        "separation_kind": "blind_case_id_case_ref_separation",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r48_blind_case_id_case_ref_separation", max_length=160),
        "r2_r3_freeze_ref": clean_identifier(freeze.get("material_id"), default="p7_r48_r2_r3_local_storage_case_matrix_freeze", max_length=160),
        "review_session_id": clean_identifier(freeze.get("review_session_id"), default=P7_R48_REVIEW_SESSION_DEFAULT_REF, max_length=120),
        "packet_kind": P7_R48_PACKET_KIND,
        "review_kind": P7_R48_REVIEW_KIND,
        "case_count": int(freeze.get("case_count") or 0),
        "case_ref_count": case_ref_count,
        "blind_case_id_count": blind_case_count,
        "case_ref_to_blind_case_ref_separated": True,
        "controller_manifest_keeps_case_ref_family_tier": True,
        "reviewer_facing_identifier_policy": "blind_case_id_only",
        "reviewer_facing_uses_blind_case_id_only": True,
        "reviewer_facing_case_ref_id_allowed": False,
        "reviewer_facing_family_allowed": False,
        "reviewer_facing_subscription_tier_allowed": False,
        "reviewer_facing_expected_result_allowed": False,
        "reviewer_facing_gate_result_allowed": False,
        "blind_case_id_family_tier_expected_gate_not_encoded": True,
        "blind_case_id_derived_from_body_or_record_hash": False,
        "blind_case_id_derived_from_record_id_hash": False,
        "controller_manifest_row_field_refs": list(P7_R48_CONTROLLER_MANIFEST_ROW_FIELD_REFS),
        "reviewer_facing_case_index_row_field_refs": list(P7_R48_REVIEWER_FACING_CASE_INDEX_ROW_FIELD_REFS),
        "controller_manifest_rows": controller_rows,
        "reviewer_facing_case_index_rows": reviewer_rows,
        "body_full_packet_materialized_here": False,
        "local_reviewer_payload_materialized_here": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "body_free_case_matrix_ready": True,
        "actual_case_matrix_materialized_here": True,
        "blind_case_id_case_ref_separated": True,
        "reviewer_facing_local_packet_schema_fixed": False,
        "implemented_steps": [*P7_R48_R2_R3_IMPLEMENTED_STEPS, "R4_blind_case_id_case_ref_separation"],
        "not_yet_implemented_steps": ["R5_reviewer_facing_local_packet_schema", *P7_R48_R4_R5_NOT_YET_IMPLEMENTED_STEPS],
        "next_required_step": P7_R48_R4_NEXT_REQUIRED_STEP_REF,
        "p5_human_blind_qa_start_allowed_after_r47_policy": True,
        "p5_human_blind_qa_actual_review_start_allowed_after_r4_r5": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
        **_r4_r5_false_flags(),
    }
    assert_p7_r48_blind_case_id_case_ref_separation_contract(separation)
    return separation


def _reviewer_packet_field_contracts() -> list[dict[str, Any]]:
    field_types = {
        "schema_version": "const_schema_version",
        "local_only": "const_true",
        "must_not_export": "const_true",
        "disposal_required": "const_true",
        "packet_kind": "const_packet_kind",
        "review_kind": "const_review_kind",
        "review_session_id": "string_ref",
        "packet_ref_id": "string_ref",
        "blind_case_id": "blind_identifier",
        "review_prompt_version": "const_review_prompt_version",
        "current_input_review_surface": "local_only_body_string",
        "returned_emlis_surface": "local_only_body_string",
        "bounded_owned_history_review_surface": "local_only_body_string_or_null",
        "review_questions": "local_only_question_list",
        "axis_rating_form": "local_only_rating_form",
    }
    return [
        {
            "field_ref": field_ref,
            "field_kind": field_types[field_ref],
            "required": True,
            "reviewer_visible": field_ref in P7_R48_P5_REVIEWER_PACKET_REVIEWER_VISIBLE_FIELD_REFS,
            "local_only": True,
            "body_free_material_allowed": False,
            "body_free": True,
        }
        for field_ref in P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_REQUIRED_FIELD_REFS
    ]


def build_p7_r48_p5_reviewer_facing_local_packet_schema_freeze(
    *,
    blind_case_id_case_ref_separation: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r48_p5_reviewer_facing_local_packet_schema_freeze",
) -> dict[str, Any]:
    """Build the R48 R5 body-free schema freeze for local-only reviewer packets."""

    separation = (
        safe_mapping(blind_case_id_case_ref_separation)
        if blind_case_id_case_ref_separation is not None
        else build_p7_r48_blind_case_id_case_ref_separation()
    )
    assert_p7_r48_blind_case_id_case_ref_separation_contract(separation)
    if blind_case_id_case_ref_separation is not None:
        _assert_r48_body_free(separation, source="p7_r48.blind_case_id_case_ref_separation")

    schema = {
        "schema_version": P7_R48_REVIEWER_FACING_LOCAL_PACKET_SCHEMA_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R48_STEP,
        "scope": P7_R48_SCOPE,
        "policy_kind": P7_R48_POLICY_KIND,
        "schema_freeze_kind": "p5_reviewer_facing_local_packet_schema_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r48_p5_reviewer_facing_local_packet_schema_freeze", max_length=160),
        "r4_separation_ref": clean_identifier(separation.get("material_id"), default="p7_r48_blind_case_id_case_ref_separation", max_length=160),
        "review_session_id": clean_identifier(separation.get("review_session_id"), default=P7_R48_REVIEW_SESSION_DEFAULT_REF, max_length=120),
        "packet_schema_version": P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION,
        "packet_schema_id": "cocolon.emlis.p7_r48.p5_reviewer_packet.local_only.v1",
        "packet_kind": P7_R48_PACKET_KIND,
        "review_kind": P7_R48_REVIEW_KIND,
        "review_prompt_version": P7_R48_REVIEW_PROMPT_VERSION,
        "reviewer_facing_identifier_policy": "blind_case_id_only",
        "reviewer_visible_field_refs": list(P7_R48_P5_REVIEWER_PACKET_REVIEWER_VISIBLE_FIELD_REFS),
        "local_only_control_field_refs": list(P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_CONTROL_FIELD_REFS),
        "required_field_refs": list(P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_REQUIRED_FIELD_REFS),
        "allowed_payload_field_refs": list(P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_REQUIRED_FIELD_REFS),
        "forbidden_payload_field_refs": list(P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_FORBIDDEN_FIELD_REFS),
        "local_only_body_field_refs": list(P7_R48_P5_REVIEWER_PACKET_BODY_FIELD_REFS),
        "review_question_refs": list(P7_R48_P5_REVIEW_QUESTION_REFS),
        "field_contracts": _reviewer_packet_field_contracts(),
        "axis_rating_form_contract": {
            "score_min": 0.0,
            "score_max": 1.0,
            "required_axis_refs": list(P5_HUMAN_BLIND_QA_RATING_AXES),
            "free_text_allowed_local_only": True,
            "free_text_bodyfree_allowed": False,
            "machine_metrics_used_for_readfeel": False,
            "body_free": True,
        },
        "additional_properties_allowed": False,
        "local_only_required": True,
        "must_not_export_required": True,
        "disposal_required_required": True,
        "family_visible_to_reviewer_allowed": False,
        "subscription_tier_visible_to_reviewer_allowed": False,
        "expected_result_visible_to_reviewer_allowed": False,
        "gate_result_visible_to_reviewer_allowed": False,
        "case_ref_visible_to_reviewer_allowed": False,
        "public_meta_in_reviewer_payload_allowed": False,
        "raw_input_in_reviewer_payload_allowed": False,
        "comment_text_in_reviewer_payload_allowed": False,
        "candidate_body_in_reviewer_payload_allowed": False,
        "surface_body_in_reviewer_payload_allowed": False,
        "controller_expected_boundary_in_reviewer_payload_allowed": False,
        "reviewer_free_text_in_packet_payload_allowed": False,
        "body_free_material_can_include_local_packet_payload": False,
        "json_schema_file_created_here": False,
        "body_full_packet_materialized_here": False,
        "local_reviewer_payload_materialized_here": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "body_free_case_matrix_ready": True,
        "actual_case_matrix_materialized_here": True,
        "blind_case_id_case_ref_separated": True,
        "reviewer_facing_local_packet_schema_fixed": True,
        "implemented_steps": list(P7_R48_R4_R5_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R48_R4_R5_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R48_R4_R5_NEXT_REQUIRED_STEP_REF,
        "p5_human_blind_qa_start_allowed_after_r47_policy": True,
        "p5_human_blind_qa_actual_review_start_allowed_after_r4_r5": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
        **_r4_r5_false_flags(),
    }
    assert_p7_r48_p5_reviewer_facing_local_packet_schema_freeze_contract(schema)
    return schema


def build_p7_r48_r4_r5_reviewer_packet_schema_freeze(
    *,
    r2_r3_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r48_r4_r5_reviewer_packet_schema_freeze",
) -> dict[str, Any]:
    """Build a compact body-free combined R48 R4/R5 summary."""

    r2_r3 = (
        safe_mapping(r2_r3_freeze)
        if r2_r3_freeze is not None
        else build_p7_r48_r2_r3_local_storage_case_matrix_freeze()
    )
    assert_p7_r48_r2_r3_local_storage_case_matrix_freeze_contract(r2_r3)
    if r2_r3_freeze is not None:
        _assert_r48_body_free(r2_r3, source="p7_r48.r2_r3_freeze")
    separation = build_p7_r48_blind_case_id_case_ref_separation(r2_r3_freeze=r2_r3)
    packet_schema = build_p7_r48_p5_reviewer_facing_local_packet_schema_freeze(
        blind_case_id_case_ref_separation=separation
    )
    combined = {
        "schema_version": P7_R48_R4_R5_REVIEWER_PACKET_SCHEMA_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R48_STEP,
        "scope": P7_R48_SCOPE,
        "policy_kind": P7_R48_POLICY_KIND,
        "freeze_kind": "r4_r5_reviewer_packet_schema_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r48_r4_r5_reviewer_packet_schema_freeze", max_length=160),
        "implemented_steps": list(P7_R48_R4_R5_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R48_R4_R5_NOT_YET_IMPLEMENTED_STEPS),
        "r2_r3_local_storage_case_matrix_freeze": r2_r3,
        "blind_case_id_case_ref_separation": separation,
        "reviewer_facing_local_packet_schema_freeze": packet_schema,
        "first_next_work_ref": P7_R48_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R48_R4_R5_NEXT_REQUIRED_STEP_REF,
        "packet_kind": P7_R48_PACKET_KIND,
        "review_kind": P7_R48_REVIEW_KIND,
        "review_session_id": clean_identifier(r2_r3.get("review_session_id"), default=P7_R48_REVIEW_SESSION_DEFAULT_REF, max_length=120),
        "case_count": int(r2_r3.get("case_count") or 0),
        "minimums_satisfied": r2_r3.get("minimums_satisfied") is True,
        "r0_current_source_r47_handoff_hold_refrozen": True,
        "r1_scope_schema_packet_kind_fixed": True,
        "local_storage_root_policy_connected": True,
        "p5_24_case_first_formal_review_matrix_built": True,
        "blind_case_id_case_ref_separated": True,
        "reviewer_facing_local_packet_schema_fixed": True,
        "body_free_case_matrix_ready": True,
        "actual_case_matrix_materialized_here": True,
        "body_full_packet_materialized_here": False,
        "local_reviewer_payload_materialized_here": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "p5_human_blind_qa_start_allowed_after_r47_policy": True,
        "p5_human_blind_qa_actual_review_start_allowed_after_r4_r5": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
        **_r4_r5_false_flags(),
    }
    assert_p7_r48_r4_r5_reviewer_packet_schema_freeze_contract(combined)
    return combined



def _local_storage_policy_from_r4_r5_freeze(freeze: Mapping[str, Any]) -> dict[str, Any]:
    r2_r3 = safe_mapping(freeze.get("r2_r3_local_storage_case_matrix_freeze"))
    assert_p7_r48_r2_r3_local_storage_case_matrix_freeze_contract(r2_r3)
    storage = safe_mapping(r2_r3.get("local_storage_policy"))
    assert_p7_r48_local_storage_root_policy_contract(storage)
    return storage


def build_p7_r48_body_full_packet_materialization_guard(
    *,
    local_review_root: Any = None,
    repo_roots: Sequence[Any] | None = None,
    export_roots: Sequence[Any] | None = None,
    explicit_body_full_generation_allow: bool = False,
    r4_r5_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r48_body_full_packet_materialization_guard",
) -> dict[str, Any]:
    """Build the R48 R6 body-free body-full materialization guard.

    The guard may permit a later local-only writer only when the R2 storage
    policy has a valid external local root and the caller supplied explicit
    allow. This function itself never writes or returns body-full reviewer text.
    """

    if r4_r5_freeze is None:
        r2_r3 = build_p7_r48_r2_r3_local_storage_case_matrix_freeze(
            local_review_root=local_review_root,
            repo_roots=repo_roots,
            export_roots=export_roots,
            explicit_body_full_generation_allow=explicit_body_full_generation_allow,
        )
        r4_r5 = build_p7_r48_r4_r5_reviewer_packet_schema_freeze(r2_r3_freeze=r2_r3)
    else:
        r4_r5 = safe_mapping(r4_r5_freeze)
    assert_p7_r48_r4_r5_reviewer_packet_schema_freeze_contract(r4_r5)
    if r4_r5_freeze is not None:
        _assert_r48_body_free(r4_r5, source="p7_r48.r4_r5_freeze")

    storage = _local_storage_policy_from_r4_r5_freeze(r4_r5)
    root_valid = storage.get("local_review_root_valid") is True
    explicit_allow = storage.get("explicit_body_full_generation_allow") is True
    materialization_allowed = storage.get("local_body_packet_generation_allowed") is True
    block_reason_ids = [] if materialization_allowed else dedupe_identifiers(
        storage.get("generation_block_reason_ids"), limit=20, max_length=160
    )

    guard = {
        "schema_version": P7_R48_BODY_FULL_PACKET_MATERIALIZATION_GUARD_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R48_STEP,
        "scope": P7_R48_SCOPE,
        "policy_kind": P7_R48_POLICY_KIND,
        "policy_section": "R6_body_full_packet_materialization_guard",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r48_body_full_packet_materialization_guard", max_length=160),
        "r4_r5_freeze_ref": clean_identifier(r4_r5.get("material_id"), default="p7_r48_r4_r5_reviewer_packet_schema_freeze", max_length=160),
        "r4_r5_reviewer_packet_schema_freeze": r4_r5,
        "local_storage_policy_ref": clean_identifier(storage.get("material_id"), default="p7_r48_local_storage_root_policy", max_length=160),
        "local_review_root_status": clean_identifier(storage.get("local_review_root_status"), default="missing", max_length=40),
        "local_review_root_valid": root_valid,
        "explicit_body_full_generation_allow": explicit_allow,
        "storage_root_ref": clean_identifier(storage.get("storage_root_ref"), default="not_configured_or_invalid", max_length=120),
        "session_storage_ref": clean_identifier(storage.get("session_storage_ref"), default="not_configured_or_invalid", max_length=120),
        "root_path_exposed": False,
        "local_absolute_path_included": False,
        "body_full_generation_requires_env_root": True,
        "body_full_generation_requires_explicit_allow": True,
        "body_full_packet_materialization_guard_ready": True,
        "body_full_packet_materialization_allowed_by_guard": materialization_allowed,
        "body_full_packet_materialization_permission_allowed": materialization_allowed,
        "local_body_packet_generation_allowed": materialization_allowed,
        "body_full_packet_materialization_block_reason_ids": block_reason_ids,
        "body_full_packet_output_dir_ref": "body_full_packets.local_only",
        "body_full_packet_output_file_ref_template": "body_full_packets.local_only/{blind_case_id}.p5_review_packet.local_only.json",
        "local_packet_output_ref_is_abstract": True,
        "local_packet_export_allowed": False,
        "body_full_packet_export_allowed": False,
        "body_full_packet_git_tracking_allowed": False,
        "body_full_packet_zip_inclusion_allowed": False,
        "release_material_body_full_allowed": False,
        "p7_scorecard_body_full_material_allowed": False,
        "public_meta_body_full_material_allowed": False,
        "body_content_hash_storage_allowed": False,
        "body_full_file_content_hash_storage_allowed": False,
        "generated_local_packet_required_flag_refs": list(P7_R48_LOCAL_REVIEWER_PACKET_REQUIRED_FLAG_REFS),
        "generated_local_packet_must_set_local_only": True,
        "generated_local_packet_must_set_must_not_export": True,
        "generated_local_packet_must_set_disposal_required": True,
        "generated_local_packet_schema_version": P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION,
        "generated_local_packet_schema_contract_ref": "assert_p7_r48_p5_reviewer_packet_local_only_payload_contract",
        "generated_local_packet_forbidden_field_refs": list(P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_FORBIDDEN_FIELD_REFS),
        "generated_local_packet_allowed_field_refs": list(P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_REQUIRED_FIELD_REFS),
        "body_free_material_can_include_local_packet_payload": False,
        "body_free_material_can_include_body_hash": False,
        "default_generation_mode": "blocked_until_valid_external_local_root_and_explicit_allow",
        "dry_run_body_free_default": True,
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
        "body_free_case_matrix_ready": True,
        "actual_case_matrix_materialized_here": True,
        "blind_case_id_case_ref_separated": True,
        "reviewer_facing_local_packet_schema_fixed": True,
        "implemented_steps": [*P7_R48_R4_R5_IMPLEMENTED_STEPS, "R6_body_full_packet_materialization_guard"],
        "not_yet_implemented_steps": ["R7_local_reviewer_notes_policy", *P7_R48_R6_R7_NOT_YET_IMPLEMENTED_STEPS],
        "next_required_step": P7_R48_R6_NEXT_REQUIRED_STEP_REF,
        "p5_human_blind_qa_start_allowed_after_r47_policy": True,
        "p5_human_blind_qa_actual_review_start_allowed_after_r6_r7": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
        **_r6_r7_false_flags(),
    }
    assert_p7_r48_body_full_packet_materialization_guard_contract(guard)
    return guard


def build_p7_r48_local_reviewer_notes_policy(
    *,
    body_full_packet_materialization_guard: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r48_local_reviewer_notes_policy",
) -> dict[str, Any]:
    """Build the R48 R7 local reviewer notes policy as body-free material."""

    guard = (
        safe_mapping(body_full_packet_materialization_guard)
        if body_full_packet_materialization_guard is not None
        else build_p7_r48_body_full_packet_materialization_guard()
    )
    assert_p7_r48_body_full_packet_materialization_guard_contract(guard)
    if body_full_packet_materialization_guard is not None:
        _assert_r48_body_free(guard, source="p7_r48.body_full_packet_materialization_guard")

    policy = {
        "schema_version": P7_R48_LOCAL_REVIEWER_NOTES_POLICY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R48_STEP,
        "scope": P7_R48_SCOPE,
        "policy_kind": P7_R48_POLICY_KIND,
        "policy_section": "R7_local_reviewer_notes_policy",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r48_local_reviewer_notes_policy", max_length=160),
        "r6_guard_ref": clean_identifier(guard.get("material_id"), default="p7_r48_body_full_packet_materialization_guard", max_length=160),
        "r47_reviewer_notes_policy_schema_version_ref": P7_R47_REVIEWER_NOTES_LOCAL_ONLY_POLICY_SCHEMA_VERSION,
        "reviewer_notes_policy_schema_version": P7_R48_LOCAL_REVIEWER_NOTES_POLICY_SCHEMA_VERSION,
        "local_only_notes_policy_fixed": True,
        "reviewer_free_text_policy_fixed": True,
        "local_notes_dir_ref": "reviewer_notes.local_only",
        "local_notes_schema_file_created_here": False,
        "local_notes_standard_export_allowed": False,
        "local_notes_release_material_allowed": False,
        "local_notes_p7_scorecard_material_allowed": False,
        "local_notes_handoff_ledger_material_allowed": False,
        "local_notes_public_meta_material_allowed": False,
        "direct_note_copy_to_p7_allowed": False,
        "raw_quote_to_reason_id_allowed": False,
        "reviewer_free_text_included": False,
        "reviewer_free_text_material_allowed": False,
        "reviewer_free_text_bodyfree_allowed": False,
        "body_free_rating_row_reviewer_free_text_included_required_false": True,
        "body_free_blocker_row_reviewer_free_text_included_required_false": True,
        "rating_rows_body_free_only": True,
        "blocker_rows_body_free_only": True,
        "sanitized_reason_id_required_for_p7_material": True,
        "sanitized_reason_ids_only": True,
        "sanitized_reason_id_refs": list(P7_R48_SANITIZED_REASON_ID_REFS),
        "default_unmapped_reason_id": "reason_id_other_local_note_purged",
        "reason_id_other_local_note_purged": True,
        "execution_blocker_id_refs": list(P7_R48_EXECUTION_BLOCKER_ID_REFS),
        "notes_retention_after_rating_finalized_max_hours": P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
        "notes_purge_required_after_rating_finalized": True,
        "body_full_packet_retention_max_hours": P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
        "body_free_result_can_retain_sanitized_reason_ids": True,
        "body_free_result_can_retain_blocker_ids": True,
        "body_free_result_can_retain_numeric_ratings_later": True,
        "body_free_result_can_retain_disposal_receipt_ref_later": True,
        "local_reviewer_payload_materialized_here": False,
        "actual_notes_materialized_here": False,
        "actual_reviewer_notes_materialized_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "actual_human_review_run_here": False,
        "actual_disposal_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "json_schema_file_created_here": False,
        "body_full_packet_materialization_guard_ready": True,
        "local_reviewer_notes_policy_fixed": True,
        "reviewer_notes_local_only_policy_fixed": True,
        "body_full_packet_materialization_allowed_by_guard": guard.get("body_full_packet_materialization_allowed_by_guard") is True,
        "implemented_steps": [*P7_R48_R4_R5_IMPLEMENTED_STEPS, "R6_body_full_packet_materialization_guard", "R7_local_reviewer_notes_policy"],
        "not_yet_implemented_steps": list(P7_R48_R6_R7_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R48_R6_R7_NEXT_REQUIRED_STEP_REF,
        "p5_human_blind_qa_start_allowed_after_r47_policy": True,
        "p5_human_blind_qa_actual_review_start_allowed_after_r6_r7": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
        **_r6_r7_false_flags(),
    }
    assert_p7_r48_local_reviewer_notes_policy_contract(policy)
    return policy


def build_p7_r48_r6_r7_materialization_notes_policy_freeze(
    *,
    local_review_root: Any = None,
    repo_roots: Sequence[Any] | None = None,
    export_roots: Sequence[Any] | None = None,
    explicit_body_full_generation_allow: bool = False,
    r4_r5_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r48_r6_r7_materialization_notes_policy_freeze",
) -> dict[str, Any]:
    """Build a compact body-free combined R48 R6/R7 freeze."""

    guard = build_p7_r48_body_full_packet_materialization_guard(
        local_review_root=local_review_root,
        repo_roots=repo_roots,
        export_roots=export_roots,
        explicit_body_full_generation_allow=explicit_body_full_generation_allow,
        r4_r5_freeze=r4_r5_freeze,
    )
    notes_policy = build_p7_r48_local_reviewer_notes_policy(body_full_packet_materialization_guard=guard)
    r4_r5 = safe_mapping(guard.get("r4_r5_reviewer_packet_schema_freeze"))
    combined = {
        "schema_version": P7_R48_R6_R7_MATERIALIZATION_NOTES_POLICY_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R48_STEP,
        "scope": P7_R48_SCOPE,
        "policy_kind": P7_R48_POLICY_KIND,
        "freeze_kind": "r6_r7_materialization_notes_policy_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r48_r6_r7_materialization_notes_policy_freeze", max_length=160),
        "implemented_steps": list(P7_R48_R6_R7_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R48_R6_R7_NOT_YET_IMPLEMENTED_STEPS),
        "r4_r5_reviewer_packet_schema_freeze": r4_r5,
        "body_full_packet_materialization_guard": guard,
        "local_reviewer_notes_policy": notes_policy,
        "first_next_work_ref": P7_R48_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R48_R6_R7_NEXT_REQUIRED_STEP_REF,
        "packet_kind": P7_R48_PACKET_KIND,
        "review_kind": P7_R48_REVIEW_KIND,
        "review_session_id": clean_identifier(r4_r5.get("review_session_id"), default=P7_R48_REVIEW_SESSION_DEFAULT_REF, max_length=120),
        "case_count": int(r4_r5.get("case_count") or 0),
        "minimums_satisfied": r4_r5.get("minimums_satisfied") is True,
        "r0_current_source_r47_handoff_hold_refrozen": True,
        "r1_scope_schema_packet_kind_fixed": True,
        "local_storage_root_policy_connected": True,
        "p5_24_case_first_formal_review_matrix_built": True,
        "blind_case_id_case_ref_separated": True,
        "reviewer_facing_local_packet_schema_fixed": True,
        "body_full_packet_materialization_guard_ready": True,
        "local_reviewer_notes_policy_fixed": True,
        "reviewer_notes_local_only_policy_fixed": True,
        "body_full_packet_materialization_allowed_by_guard": guard.get("body_full_packet_materialization_allowed_by_guard") is True,
        "body_free_case_matrix_ready": True,
        "actual_case_matrix_materialized_here": True,
        "body_full_packet_materialized_here": False,
        "local_reviewer_payload_materialized_here": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_reviewer_notes_materialized_here": False,
        "actual_notes_materialized_here": False,
        "actual_disposal_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "p5_human_blind_qa_start_allowed_after_r47_policy": True,
        "p5_human_blind_qa_actual_review_start_allowed_after_r6_r7": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
        **_r6_r7_false_flags(),
    }
    assert_p7_r48_r6_r7_materialization_notes_policy_freeze_contract(combined)
    return combined


def _contains_forbidden_key_ref(value: Any, forbidden_refs: set[str]) -> bool:
    if isinstance(value, Mapping):
        return any(str(key) in forbidden_refs or _contains_forbidden_key_ref(child, forbidden_refs) for key, child in value.items())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_key_ref(child, forbidden_refs) for child in value)
    return False


def _assert_identifier_sequence_r48(value: Any, *, source: str, allowed_refs: Sequence[str] | None = None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise ValueError(f"{source} must be a sequence of identifiers")
    original = list(value)
    cleaned = dedupe_identifiers(original, limit=120, max_length=160)
    if len(cleaned) != len(original):
        raise ValueError(f"{source} must contain unique non-empty identifiers")
    if allowed_refs is not None and set(cleaned) - set(allowed_refs):
        raise ValueError(f"{source} contains identifiers outside the R48 allowed refs")
    return cleaned


def _case_ref_fields(case_row: Mapping[str, Any]) -> dict[str, str]:
    row = safe_mapping(case_row)
    _assert_r48_body_free(row, source="p7_r48.case_row_for_rating_or_blocker")
    case = {
        "review_session_id": clean_identifier(row.get("review_session_id"), default=P7_R48_REVIEW_SESSION_DEFAULT_REF, max_length=120),
        "packet_ref_id": clean_identifier(row.get("packet_ref_id"), default="packet_ref", max_length=160),
        "blind_case_id": clean_identifier(row.get("blind_case_id"), default="blind_case", max_length=160),
        "case_ref_id": clean_identifier(row.get("case_ref_id"), default="case_ref", max_length=160),
        "family": clean_identifier(row.get("family"), default="unknown", max_length=160),
        "case_role": clean_identifier(row.get("case_role"), default="unknown", max_length=120),
    }
    if case["family"] not in P5_HUMAN_BLIND_QA_FAMILIES:
        raise ValueError("R48 rating/blocker row requires a known P5 family")
    if case["case_role"] not in P7_R48_P5_CASE_ROLE_REFS:
        raise ValueError("R48 rating/blocker row requires a known P5 case role")
    if not all(case.values()):
        raise ValueError("R48 rating/blocker row requires complete body-free case identifiers")
    return case


def _case_ref_fields_from_first_row(r6_r7_freeze: Mapping[str, Any]) -> dict[str, str]:
    r4_r5 = safe_mapping(safe_mapping(r6_r7_freeze).get("r4_r5_reviewer_packet_schema_freeze"))
    r2_r3 = safe_mapping(r4_r5.get("r2_r3_local_storage_case_matrix_freeze"))
    matrix = safe_mapping(r2_r3.get("p5_case_matrix"))
    rows = matrix.get("case_rows") or []
    if not rows:
        raise ValueError("R48 R8/R9 requires body-free case matrix rows")
    return _case_ref_fields({**safe_mapping(rows[0]), "review_session_id": r2_r3.get("review_session_id")})


def _normalize_axis_scores(axis_scores: Any) -> dict[str, float]:
    scores = safe_mapping(axis_scores)
    if set(scores) != set(P5_HUMAN_BLIND_QA_RATING_AXES):
        raise ValueError("R48 R8 rating row requires every P5 axis exactly once; missing axes are not pass")
    normalized: dict[str, float] = {}
    for axis in P5_HUMAN_BLIND_QA_RATING_AXES:
        raw = scores.get(axis)
        if isinstance(raw, bool) or not isinstance(raw, (int, float, str)):
            raise ValueError("R48 R8 axis scores must be explicit numeric reviewer ratings")
        try:
            score = float(raw)
        except ValueError as exc:
            raise ValueError("R48 R8 axis scores must be numeric") from exc
        if not 0.0 <= score <= 1.0:
            raise ValueError("R48 R8 axis scores must be normalized into the 0.0-1.0 range")
        normalized[axis] = score
    return normalized


def _assert_pass_verdict_matches_scores_and_blockers(*, verdict: str, axis_scores: Mapping[str, float], blocker_ids: Sequence[str]) -> None:
    if verdict == "PASS":
        if blocker_ids:
            raise ValueError("R48 R8 PASS rating rows must not carry blocker_ids")
        for axis, target in P5_HUMAN_BLIND_QA_TARGETS.items():
            if float(axis_scores[axis]) < float(target):
                raise ValueError("R48 R8 PASS cannot be inferred when a required axis is below target")
    if verdict in {"RED", "REPAIR_REQUIRED"} and not blocker_ids:
        raise ValueError("R48 R8 RED/REPAIR_REQUIRED rows must carry at least one readfeel blocker_id")
    if verdict in {"BLOCKED", "NOT_REVIEWABLE"}:
        raise ValueError("R48 R8 rating row normalizer must not mix execution-blocked cases into readfeel rows")


def normalize_p7_r48_p5_rating_row_bodyfree(
    *,
    review_result: Mapping[str, Any],
    case_row: Mapping[str, Any],
    reviewer_ref: Any = "local_reviewer_ref",
    reviewed_at: Any = "reviewed_at_unset",
    body_removed: bool = False,
) -> dict[str, Any]:
    """Normalize sanitized human review output into one body-free rating row."""

    result = safe_mapping(review_result)
    if _contains_forbidden_key_ref(result, set(P7_R48_P5_RATING_BLOCKER_FORBIDDEN_FIELD_REFS)):
        raise ValueError("R48 R8 rating row input contains reviewer text, body payload, or machine metric fields")
    if result.get("machine_metrics_used_for_readfeel") is True:
        raise ValueError("R48 R8 machine metrics must not supplement human readfeel ratings")
    if result.get("reviewer_free_text_included") is True:
        raise ValueError("R48 R8 reviewer free text must not be retained in body-free rating rows")
    _assert_r48_body_free(result, source="p7_r48.rating_row_normalizer.review_result")

    case = _case_ref_fields(case_row)
    axis_scores = _normalize_axis_scores(result.get("axis_scores"))
    verdict = clean_identifier(result.get("verdict"), default="", max_length=60)
    if verdict not in P7_R48_P5_REVIEW_VERDICTS:
        raise ValueError("R48 R8 verdict enum changed")
    reasons = _assert_identifier_sequence_r48(
        result.get("sanitized_reason_ids") or [],
        source="p7_r48_rating_row.sanitized_reason_ids",
        allowed_refs=P7_R48_SANITIZED_REASON_ID_REFS,
    )
    blockers = _assert_identifier_sequence_r48(
        result.get("blocker_ids") or [],
        source="p7_r48_rating_row.blocker_ids",
        allowed_refs=P7_R48_READFEEL_BLOCKER_ID_REFS,
    )
    _assert_pass_verdict_matches_scores_and_blockers(verdict=verdict, axis_scores=axis_scores, blocker_ids=blockers)
    row = {
        "schema_version": P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION,
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
    assert_p7_r48_p5_rating_row_bodyfree_contract(row)
    return row


def _execution_blocker_kind(execution_blocker_id: str) -> str:
    if execution_blocker_id.startswith("review_packet_generation_blocked"):
        return "GENERATION"
    if execution_blocker_id in {"review_case_material_missing", "review_case_matrix_minimum_not_met"}:
        return "MATERIAL"
    if execution_blocker_id in {"review_timeout_unclassified", "reviewer_not_assigned"}:
        return "REVIEW"
    if execution_blocker_id == "rating_row_incomplete":
        return "RATING"
    if execution_blocker_id in {"body_purge_failed", "body_purge_not_verified"}:
        return "DISPOSAL"
    return "VALIDATION"


def build_p7_r48_p5_blocker_row_bodyfree(
    *,
    case_row: Mapping[str, Any],
    blocker_id: Any,
    blocker_kind: Any = "REPAIR_REQUIRED",
    blocker_status: Any = "OPEN",
    sanitized_reason_ids: Sequence[Any] | None = None,
    body_removed: bool = False,
) -> dict[str, Any]:
    case = _case_ref_fields(case_row)
    blocker = clean_identifier(blocker_id, default="", max_length=160)
    if blocker not in P7_R48_READFEEL_BLOCKER_ID_REFS:
        raise ValueError("R48 R9 readfeel blocker row requires a P5 readfeel blocker_id")
    kind = clean_identifier(blocker_kind, default="REPAIR_REQUIRED", max_length=80)
    if kind not in P7_R48_P5_BLOCKER_KINDS or kind == "EXECUTION_BLOCKER":
        raise ValueError("R48 R9 readfeel blocker row must not use EXECUTION_BLOCKER kind")
    status = clean_identifier(blocker_status, default="OPEN", max_length=80)
    if status not in P7_R48_P5_BLOCKER_STATUSES:
        raise ValueError("R48 R9 readfeel blocker status enum changed")
    reasons = _assert_identifier_sequence_r48(
        sanitized_reason_ids or [blocker],
        source="p7_r48_blocker_row.sanitized_reason_ids",
        allowed_refs=P7_R48_SANITIZED_REASON_ID_REFS,
    )
    row = {
        "schema_version": P7_R48_P5_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        **case,
        "blocker_id": blocker,
        "blocker_kind": kind,
        "blocker_status": status,
        "sanitized_reason_ids": reasons,
        "reviewer_free_text_included": False,
        "body_removed": bool(body_removed),
        "body_free": True,
    }
    assert_p7_r48_p5_blocker_row_bodyfree_contract(row)
    return row


def build_p7_r48_p5_execution_blocker_row_bodyfree(
    *,
    case_row: Mapping[str, Any],
    execution_blocker_id: Any,
    execution_blocker_status: Any = "OPEN",
) -> dict[str, Any]:
    case = _case_ref_fields(case_row)
    blocker = clean_identifier(execution_blocker_id, default="", max_length=160)
    if blocker not in P7_R48_EXECUTION_BLOCKER_ID_REFS:
        raise ValueError("R48 R9 execution blocker id changed")
    status = clean_identifier(execution_blocker_status, default="OPEN", max_length=80)
    if status not in P7_R48_EXECUTION_BLOCKER_STATUS_REFS:
        raise ValueError("R48 R9 execution blocker status enum changed")
    row = {
        "schema_version": P7_R48_P5_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "review_session_id": case["review_session_id"],
        "packet_ref_id": case["packet_ref_id"],
        "blind_case_id": case["blind_case_id"],
        "case_ref_id": case["case_ref_id"],
        "family": case["family"],
        "execution_blocker_id": blocker,
        "execution_blocker_kind": _execution_blocker_kind(blocker),
        "execution_blocker_status": status,
        "readfeel_verdict_not_assigned": True,
        "body_free": True,
    }
    assert_p7_r48_p5_execution_blocker_row_bodyfree_contract(row)
    return row


def build_p7_r48_rating_row_normalizer_policy(
    *,
    r6_r7_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r48_rating_row_normalizer_policy",
) -> dict[str, Any]:
    freeze = safe_mapping(r6_r7_freeze) if r6_r7_freeze is not None else build_p7_r48_r6_r7_materialization_notes_policy_freeze()
    assert_p7_r48_r6_r7_materialization_notes_policy_freeze_contract(freeze)
    if r6_r7_freeze is not None:
        _assert_r48_body_free(freeze, source="p7_r48.r6_r7_freeze")
    policy = {
        "schema_version": P7_R48_RATING_ROW_NORMALIZER_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R48_STEP,
        "scope": P7_R48_SCOPE,
        "policy_kind": P7_R48_POLICY_KIND,
        "policy_section": "R8_rating_row_normalizer",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r48_rating_row_normalizer_policy", max_length=160),
        "r6_r7_freeze_ref": clean_identifier(freeze.get("material_id"), default="p7_r48_r6_r7_materialization_notes_policy_freeze", max_length=160),
        "rating_row_schema_version": P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION,
        "r47_rating_row_schema_version_ref": P7_R47_BODY_FREE_RATING_ROW_SCHEMA_VERSION,
        "required_field_refs": list(P7_R48_P5_RATING_ROW_REQUIRED_FIELD_REFS),
        "axis_refs": list(P5_HUMAN_BLIND_QA_RATING_AXES),
        "axis_target_thresholds": dict(P5_HUMAN_BLIND_QA_TARGETS),
        "axis_scores_range": {"minimum": 0.0, "maximum": 1.0},
        "missing_axis_scores_pass_allowed": False,
        "extra_axis_scores_allowed": False,
        "axis_scores_machine_auto_fill_allowed": False,
        "readfeel_auto_estimation_allowed": False,
        "machine_metrics_used_for_readfeel": False,
        "reviewer_free_text_included": False,
        "reviewer_free_text_material_allowed": False,
        "reviewer_free_text_bodyfree_allowed": False,
        "sanitized_reason_ids_only": True,
        "blocker_ids_only": True,
        "allowed_verdict_refs": list(P7_R48_P5_REVIEWABLE_VERDICTS),
        "blocked_or_not_reviewable_must_use_execution_blocker_row": True,
        "forbidden_field_refs": list(P7_R48_P5_RATING_BLOCKER_FORBIDDEN_FIELD_REFS),
        "normalizer_ready": True,
        "body_free_rating_row_normalizer_ready": True,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_human_review_run_here": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "local_reviewer_payload_materialized_here": False,
        "actual_reviewer_notes_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "implemented_steps": [*P7_R48_R6_R7_IMPLEMENTED_STEPS, "R8_rating_row_normalizer"],
        "not_yet_implemented_steps": ["R9_blocker_execution_blocker_row_builder", *P7_R48_R8_R9_NOT_YET_IMPLEMENTED_STEPS],
        "next_required_step": P7_R48_R8_NEXT_REQUIRED_STEP_REF,
        "p5_human_blind_qa_start_allowed_after_r47_policy": True,
        "p5_human_blind_qa_actual_review_start_allowed_after_r8_r9": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
        **_r8_r9_false_flags(),
    }
    assert_p7_r48_rating_row_normalizer_policy_contract(policy)
    return policy


def build_p7_r48_blocker_execution_blocker_row_builder_policy(
    *,
    rating_row_normalizer_policy: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r48_blocker_execution_blocker_row_builder_policy",
) -> dict[str, Any]:
    r8 = safe_mapping(rating_row_normalizer_policy) if rating_row_normalizer_policy is not None else build_p7_r48_rating_row_normalizer_policy()
    assert_p7_r48_rating_row_normalizer_policy_contract(r8)
    if rating_row_normalizer_policy is not None:
        _assert_r48_body_free(r8, source="p7_r48.rating_row_normalizer_policy")
    policy = {
        "schema_version": P7_R48_BLOCKER_EXECUTION_BLOCKER_ROW_BUILDER_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R48_STEP,
        "scope": P7_R48_SCOPE,
        "policy_kind": P7_R48_POLICY_KIND,
        "policy_section": "R9_blocker_execution_blocker_row_builder",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r48_blocker_execution_blocker_row_builder_policy", max_length=160),
        "r8_normalizer_ref": clean_identifier(r8.get("material_id"), default="p7_r48_rating_row_normalizer_policy", max_length=160),
        "blocker_row_schema_version": P7_R48_P5_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "execution_blocker_row_schema_version": P7_R48_P5_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "r47_blocker_row_schema_version_ref": P7_R47_BODY_FREE_BLOCKER_ROW_SCHEMA_VERSION,
        "blocker_row_required_field_refs": list(P7_R48_P5_BLOCKER_ROW_REQUIRED_FIELD_REFS),
        "execution_blocker_row_required_field_refs": list(P7_R48_P5_EXECUTION_BLOCKER_ROW_REQUIRED_FIELD_REFS),
        "readfeel_blocker_id_refs": list(P7_R48_READFEEL_BLOCKER_ID_REFS),
        "execution_blocker_id_refs": list(P7_R48_EXECUTION_BLOCKER_ID_REFS),
        "blocker_kind_refs": list(P7_R48_P5_BLOCKER_KINDS),
        "blocker_status_refs": list(P7_R48_P5_BLOCKER_STATUSES),
        "execution_blocker_kind_refs": list(P7_R48_EXECUTION_BLOCKER_KIND_REFS),
        "execution_blocker_status_refs": list(P7_R48_EXECUTION_BLOCKER_STATUS_REFS),
        "readfeel_and_execution_blockers_separated": True,
        "execution_blockers_do_not_assign_readfeel_verdict": True,
        "timeout_maps_to_execution_blocker_not_red": True,
        "missing_local_root_maps_to_execution_blocker_not_red": True,
        "material_missing_maps_to_execution_blocker_not_red": True,
        "reviewer_free_text_included": False,
        "reviewer_free_text_bodyfree_allowed": False,
        "forbidden_field_refs": list(P7_R48_P5_RATING_BLOCKER_FORBIDDEN_FIELD_REFS),
        "blocker_row_builder_ready": True,
        "execution_blocker_row_builder_ready": True,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_human_review_run_here": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "local_reviewer_payload_materialized_here": False,
        "actual_reviewer_notes_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "implemented_steps": list(P7_R48_R8_R9_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R48_R8_R9_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R48_R8_R9_NEXT_REQUIRED_STEP_REF,
        "p5_human_blind_qa_start_allowed_after_r47_policy": True,
        "p5_human_blind_qa_actual_review_start_allowed_after_r8_r9": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
        **_r8_r9_false_flags(),
    }
    assert_p7_r48_blocker_execution_blocker_row_builder_policy_contract(policy)
    return policy


def build_p7_r48_r8_r9_rating_blocker_rows_freeze(
    *,
    r6_r7_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r48_r8_r9_rating_blocker_rows_freeze",
) -> dict[str, Any]:
    full_r6_r7 = safe_mapping(r6_r7_freeze) if r6_r7_freeze is not None else build_p7_r48_r6_r7_materialization_notes_policy_freeze()
    assert_p7_r48_r6_r7_materialization_notes_policy_freeze_contract(full_r6_r7)
    r8 = build_p7_r48_rating_row_normalizer_policy(r6_r7_freeze=full_r6_r7)
    r9 = build_p7_r48_blocker_execution_blocker_row_builder_policy(rating_row_normalizer_policy=r8)
    case = _case_ref_fields_from_first_row(full_r6_r7)
    combined = {
        "schema_version": P7_R48_R8_R9_RATING_BLOCKER_ROWS_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R48_STEP,
        "scope": P7_R48_SCOPE,
        "policy_kind": P7_R48_POLICY_KIND,
        "freeze_kind": "r8_r9_rating_blocker_rows_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r48_r8_r9_rating_blocker_rows_freeze", max_length=160),
        "implemented_steps": list(P7_R48_R8_R9_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R48_R8_R9_NOT_YET_IMPLEMENTED_STEPS),
        "rating_row_normalizer_policy": r8,
        "blocker_execution_blocker_row_builder_policy": r9,
        "example_case_ref_bodyfree": case,
        "first_next_work_ref": P7_R48_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R48_R8_R9_NEXT_REQUIRED_STEP_REF,
        "packet_kind": P7_R48_PACKET_KIND,
        "review_kind": P7_R48_REVIEW_KIND,
        "review_session_id": case["review_session_id"],
        "case_count": 24,
        "minimums_satisfied": True,
        "r0_current_source_r47_handoff_hold_refrozen": True,
        "r1_scope_schema_packet_kind_fixed": True,
        "local_storage_root_policy_connected": True,
        "p5_24_case_first_formal_review_matrix_built": True,
        "blind_case_id_case_ref_separated": True,
        "reviewer_facing_local_packet_schema_fixed": True,
        "body_full_packet_materialization_guard_ready": True,
        "local_reviewer_notes_policy_fixed": True,
        "reviewer_notes_local_only_policy_fixed": True,
        "rating_row_normalizer_ready": True,
        "blocker_row_builder_ready": True,
        "execution_blocker_row_builder_ready": True,
        "readfeel_and_execution_blockers_separated": True,
        "body_free_case_matrix_ready": True,
        "actual_case_matrix_materialized_here": True,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "body_full_packet_materialized_here": False,
        "local_reviewer_payload_materialized_here": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "actual_human_review_run_here": False,
        "actual_reviewer_notes_materialized_here": False,
        "actual_notes_materialized_here": False,
        "actual_disposal_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "p5_human_blind_qa_start_allowed_after_r47_policy": True,
        "p5_human_blind_qa_actual_review_start_allowed_after_r8_r9": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
        **_r8_r9_false_flags(),
    }
    assert_p7_r48_r8_r9_rating_blocker_rows_freeze_contract(combined)
    return combined


def _assert_r8_r9_not_ready(data: Mapping[str, Any], *, source: str) -> None:
    for key in _R48_R8_R9_FALSE_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=False during R48 R8/R9")


def assert_p7_r48_p5_rating_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    if data.get("schema_version") != P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("unexpected R48 body-free rating row schema_version")
    if set(data) != set(P7_R48_P5_RATING_ROW_REQUIRED_FIELD_REFS):
        raise ValueError("R48 body-free rating row contains non-body-free or missing fields")
    if data.get("family") not in P5_HUMAN_BLIND_QA_FAMILIES:
        raise ValueError("R48 rating row family changed")
    if data.get("case_role") not in P7_R48_P5_CASE_ROLE_REFS:
        raise ValueError("R48 rating row case_role changed")
    axis_scores = safe_mapping(data.get("axis_scores"))
    if set(axis_scores) != set(P5_HUMAN_BLIND_QA_RATING_AXES):
        raise ValueError("R48 rating row requires all and only P5 rating axes")
    for score in axis_scores.values():
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0.0 <= float(score) <= 1.0:
            raise ValueError("R48 rating row axis scores must be numbers from 0.0 to 1.0")
    verdict = data.get("verdict")
    if verdict not in P7_R48_P5_REVIEWABLE_VERDICTS:
        raise ValueError("R48 rating row must only contain reviewable verdicts; execution blockers are separate")
    reasons = _assert_identifier_sequence_r48(data.get("sanitized_reason_ids"), source="p7_r48_rating_row.sanitized_reason_ids", allowed_refs=P7_R48_SANITIZED_REASON_ID_REFS)
    blockers = _assert_identifier_sequence_r48(data.get("blocker_ids"), source="p7_r48_rating_row.blocker_ids", allowed_refs=P7_R48_READFEEL_BLOCKER_ID_REFS)
    _assert_pass_verdict_matches_scores_and_blockers(verdict=str(verdict), axis_scores=axis_scores, blocker_ids=blockers)
    if verdict in {"RED", "REPAIR_REQUIRED"} and not reasons:
        raise ValueError("R48 RED/REPAIR_REQUIRED rating rows must carry sanitized reason ids")
    if data.get("reviewer_free_text_included") is not False:
        raise ValueError("R48 rating row must not include reviewer free text")
    if not isinstance(data.get("body_removed"), bool):
        raise ValueError("R48 rating row must carry boolean body_removed")
    if data.get("body_free") is not True:
        raise ValueError("R48 rating row must set body_free=True")
    _assert_r48_body_free(data, source="p7_r48_p5_rating_row_bodyfree")
    return True


def assert_p7_r48_p5_blocker_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    if data.get("schema_version") != P7_R48_P5_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("unexpected R48 body-free blocker row schema_version")
    if set(data) != set(P7_R48_P5_BLOCKER_ROW_REQUIRED_FIELD_REFS):
        raise ValueError("R48 body-free blocker row contains non-body-free or missing fields")
    if data.get("family") not in P5_HUMAN_BLIND_QA_FAMILIES:
        raise ValueError("R48 blocker row family changed")
    if data.get("case_role") not in P7_R48_P5_CASE_ROLE_REFS:
        raise ValueError("R48 blocker row case_role changed")
    if data.get("blocker_id") not in P7_R48_READFEEL_BLOCKER_ID_REFS:
        raise ValueError("R48 blocker row must carry a readfeel blocker id")
    if data.get("blocker_kind") not in P7_R48_P5_BLOCKER_KINDS or data.get("blocker_kind") == "EXECUTION_BLOCKER":
        raise ValueError("R48 blocker row must not mix execution blocker kind")
    if data.get("blocker_status") not in P7_R48_P5_BLOCKER_STATUSES:
        raise ValueError("R48 blocker row status enum changed")
    _assert_identifier_sequence_r48(data.get("sanitized_reason_ids"), source="p7_r48_blocker_row.sanitized_reason_ids", allowed_refs=P7_R48_SANITIZED_REASON_ID_REFS)
    if data.get("reviewer_free_text_included") is not False:
        raise ValueError("R48 blocker row must not include reviewer free text")
    if not isinstance(data.get("body_removed"), bool):
        raise ValueError("R48 blocker row must carry boolean body_removed")
    if data.get("body_free") is not True:
        raise ValueError("R48 blocker row must set body_free=True")
    _assert_r48_body_free(data, source="p7_r48_p5_blocker_row_bodyfree")
    return True


def assert_p7_r48_p5_execution_blocker_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    if data.get("schema_version") != P7_R48_P5_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("unexpected R48 body-free execution blocker row schema_version")
    if set(data) != set(P7_R48_P5_EXECUTION_BLOCKER_ROW_REQUIRED_FIELD_REFS):
        raise ValueError("R48 execution blocker row contains non-body-free or missing fields")
    if data.get("family") not in P5_HUMAN_BLIND_QA_FAMILIES:
        raise ValueError("R48 execution blocker row family changed")
    blocker = data.get("execution_blocker_id")
    if blocker not in P7_R48_EXECUTION_BLOCKER_ID_REFS:
        raise ValueError("R48 execution blocker id changed")
    if data.get("execution_blocker_kind") not in P7_R48_EXECUTION_BLOCKER_KIND_REFS:
        raise ValueError("R48 execution blocker kind changed")
    if data.get("execution_blocker_kind") != _execution_blocker_kind(str(blocker)):
        raise ValueError("R48 execution blocker kind must match blocker id classification")
    if data.get("execution_blocker_status") not in P7_R48_EXECUTION_BLOCKER_STATUS_REFS:
        raise ValueError("R48 execution blocker status changed")
    if data.get("readfeel_verdict_not_assigned") is not True:
        raise ValueError("R48 execution blocker rows must not assign readfeel verdicts")
    if data.get("body_free") is not True:
        raise ValueError("R48 execution blocker row must set body_free=True")
    _assert_r48_body_free(data, source="p7_r48_p5_execution_blocker_row_bodyfree")
    return True


def assert_p7_r48_rating_row_normalizer_policy_contract(policy: Mapping[str, Any]) -> bool:
    data = safe_mapping(policy)
    _assert_common(data, schema_version=P7_R48_RATING_ROW_NORMALIZER_SCHEMA_VERSION, source="p7_r48_r8_rating_row_normalizer_policy")
    if data.get("policy_section") != "R8_rating_row_normalizer":
        raise ValueError("R48 R8 policy section changed")
    if data.get("rating_row_schema_version") != P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R48 R8 rating row schema version changed")
    if tuple(data.get("required_field_refs") or ()) != P7_R48_P5_RATING_ROW_REQUIRED_FIELD_REFS:
        raise ValueError("R48 R8 rating row required fields changed")
    if tuple(data.get("axis_refs") or ()) != P5_HUMAN_BLIND_QA_RATING_AXES:
        raise ValueError("R48 R8 axis refs changed")
    if safe_mapping(data.get("axis_target_thresholds")) != dict(P5_HUMAN_BLIND_QA_TARGETS):
        raise ValueError("R48 R8 target thresholds changed")
    for true_key in ("sanitized_reason_ids_only", "blocker_ids_only", "normalizer_ready", "body_free_rating_row_normalizer_ready", "blocked_or_not_reviewable_must_use_execution_blocker_row"):
        if data.get(true_key) is not True:
            raise ValueError(f"R48 R8 must keep {true_key}=True")
    for false_key in ("missing_axis_scores_pass_allowed", "extra_axis_scores_allowed", "axis_scores_machine_auto_fill_allowed", "readfeel_auto_estimation_allowed", "machine_metrics_used_for_readfeel", "reviewer_free_text_included", "reviewer_free_text_material_allowed", "reviewer_free_text_bodyfree_allowed", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_human_review_run_here", "actual_body_full_packet_generated_here", "body_full_writer_created_here", "local_reviewer_payload_materialized_here", "actual_reviewer_notes_materialized_here", "actual_disposal_receipt_materialized_here", "p5_human_blind_qa_actual_review_start_allowed_after_r8_r9"):
        if data.get(false_key) is not False:
            raise ValueError(f"R48 R8 must keep {false_key}=False")
    if tuple(data.get("allowed_verdict_refs") or ()) != P7_R48_P5_REVIEWABLE_VERDICTS:
        raise ValueError("R48 R8 reviewable verdict refs changed")
    if set(P7_R48_P5_RATING_BLOCKER_FORBIDDEN_FIELD_REFS) - set(dedupe_identifiers(data.get("forbidden_field_refs"), limit=260, max_length=160)):
        raise ValueError("R48 R8 forbidden field coverage changed")
    if tuple(data.get("implemented_steps") or ()) != (*P7_R48_R6_R7_IMPLEMENTED_STEPS, "R8_rating_row_normalizer"):
        raise ValueError("R48 R8 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != ("R9_blocker_execution_blocker_row_builder", *P7_R48_R8_R9_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("R48 R8 not-yet-implemented steps changed")
    if data.get("next_required_step") != P7_R48_R8_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R48 R8 must point to R9 next")
    if data.get("p5_human_blind_qa_start_allowed_after_r47_policy") is not True:
        raise ValueError("R48 R8 must preserve the R47 P5 start-allowed handoff")
    _assert_r8_r9_not_ready(data, source="p7_r48_r8_rating_row_normalizer_policy")
    return True


def assert_p7_r48_blocker_execution_blocker_row_builder_policy_contract(policy: Mapping[str, Any]) -> bool:
    data = safe_mapping(policy)
    _assert_common(data, schema_version=P7_R48_BLOCKER_EXECUTION_BLOCKER_ROW_BUILDER_SCHEMA_VERSION, source="p7_r48_r9_blocker_execution_blocker_row_builder_policy")
    if data.get("policy_section") != "R9_blocker_execution_blocker_row_builder":
        raise ValueError("R48 R9 policy section changed")
    if data.get("blocker_row_schema_version") != P7_R48_P5_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R48 R9 blocker row schema changed")
    if data.get("execution_blocker_row_schema_version") != P7_R48_P5_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R48 R9 execution blocker row schema changed")
    if tuple(data.get("blocker_row_required_field_refs") or ()) != P7_R48_P5_BLOCKER_ROW_REQUIRED_FIELD_REFS:
        raise ValueError("R48 R9 blocker row required fields changed")
    if tuple(data.get("execution_blocker_row_required_field_refs") or ()) != P7_R48_P5_EXECUTION_BLOCKER_ROW_REQUIRED_FIELD_REFS:
        raise ValueError("R48 R9 execution blocker row required fields changed")
    if tuple(data.get("readfeel_blocker_id_refs") or ()) != P7_R48_READFEEL_BLOCKER_ID_REFS:
        raise ValueError("R48 R9 readfeel blocker ids changed")
    if set(P7_R48_EXECUTION_BLOCKER_ID_REFS) - set(data.get("execution_blocker_id_refs") or ()):
        raise ValueError("R48 R9 execution blocker ids lost coverage")
    for true_key in ("readfeel_and_execution_blockers_separated", "execution_blockers_do_not_assign_readfeel_verdict", "timeout_maps_to_execution_blocker_not_red", "missing_local_root_maps_to_execution_blocker_not_red", "material_missing_maps_to_execution_blocker_not_red", "blocker_row_builder_ready", "execution_blocker_row_builder_ready"):
        if data.get(true_key) is not True:
            raise ValueError(f"R48 R9 must keep {true_key}=True")
    for false_key in ("reviewer_free_text_included", "reviewer_free_text_bodyfree_allowed", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_human_review_run_here", "actual_body_full_packet_generated_here", "body_full_writer_created_here", "local_reviewer_payload_materialized_here", "actual_reviewer_notes_materialized_here", "actual_disposal_receipt_materialized_here", "p5_human_blind_qa_actual_review_start_allowed_after_r8_r9"):
        if data.get(false_key) is not False:
            raise ValueError(f"R48 R9 must keep {false_key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R48_R8_R9_IMPLEMENTED_STEPS:
        raise ValueError("R48 R9 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R48_R8_R9_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R48 R9 not-yet-implemented steps changed")
    if data.get("next_required_step") != P7_R48_R8_R9_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R48 R9 must point to R10 next")
    if data.get("p5_human_blind_qa_start_allowed_after_r47_policy") is not True:
        raise ValueError("R48 R9 must preserve the R47 P5 start-allowed handoff")
    _assert_r8_r9_not_ready(data, source="p7_r48_r9_blocker_execution_blocker_row_builder_policy")
    return True


def assert_p7_r48_r8_r9_rating_blocker_rows_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_common(data, schema_version=P7_R48_R8_R9_RATING_BLOCKER_ROWS_FREEZE_SCHEMA_VERSION, source="p7_r48_r8_r9_rating_blocker_rows_freeze")
    if data.get("freeze_kind") != "r8_r9_rating_blocker_rows_freeze":
        raise ValueError("R48 R8/R9 freeze kind changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R48_R8_R9_IMPLEMENTED_STEPS:
        raise ValueError("R48 R8/R9 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R48_R8_R9_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R48 R8/R9 not-yet-implemented steps changed")
    assert_p7_r48_rating_row_normalizer_policy_contract(safe_mapping(data.get("rating_row_normalizer_policy")))
    assert_p7_r48_blocker_execution_blocker_row_builder_policy_contract(safe_mapping(data.get("blocker_execution_blocker_row_builder_policy")))
    if data.get("next_required_step") != P7_R48_R8_R9_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R48 R8/R9 must point to R10 next")
    for true_key in ("r0_current_source_r47_handoff_hold_refrozen", "r1_scope_schema_packet_kind_fixed", "local_storage_root_policy_connected", "p5_24_case_first_formal_review_matrix_built", "blind_case_id_case_ref_separated", "reviewer_facing_local_packet_schema_fixed", "body_full_packet_materialization_guard_ready", "local_reviewer_notes_policy_fixed", "reviewer_notes_local_only_policy_fixed", "rating_row_normalizer_ready", "blocker_row_builder_ready", "execution_blocker_row_builder_ready", "readfeel_and_execution_blockers_separated", "body_free_case_matrix_ready", "actual_case_matrix_materialized_here", "minimums_satisfied"):
        if data.get(true_key) is not True:
            raise ValueError(f"R48 R8/R9 must keep {true_key}=True")
    if data.get("case_count") != 24:
        raise ValueError("R48 R8/R9 first formal matrix must contain exactly 24 cases")
    for false_key in ("actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "body_full_packet_materialized_here", "local_reviewer_payload_materialized_here", "actual_body_full_packet_generated_here", "body_full_writer_created_here", "actual_human_review_run_here", "actual_reviewer_notes_materialized_here", "actual_notes_materialized_here", "actual_disposal_run_here", "actual_disposal_receipt_materialized_here", "p5_human_blind_qa_actual_review_start_allowed_after_r8_r9"):
        if data.get(false_key) is not False:
            raise ValueError(f"R48 R8/R9 must keep {false_key}=False")
    if data.get("p5_human_blind_qa_start_allowed_after_r47_policy") is not True:
        raise ValueError("R48 R8/R9 must preserve the R47 P5 start-allowed handoff")
    _assert_r8_r9_not_ready(data, source="p7_r48_r8_r9_rating_blocker_rows_freeze")
    return True



def _assert_r10_r11_not_ready(data: Mapping[str, Any], *, source: str) -> None:
    for key in _R48_R10_R11_FALSE_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=False during R48 R10/R11")


def _assert_r12_r13_not_actualized(data: Mapping[str, Any], *, source: str) -> None:
    for key in _R48_R12_R13_FALSE_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=False during R48 R12/R13")


def _non_negative_int_r48(value: Any, *, source: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{source} must be a non-negative integer")
    return int(value)


def _assert_no_r48_receipt_or_summary_forbidden_fields(
    value: Mapping[str, Any], *, source: str, forbidden_refs: Sequence[str]
) -> None:
    data = safe_mapping(value)
    if _contains_forbidden_key_ref(data, set(forbidden_refs)):
        raise ValueError(f"{source} contains body hash, local path, deleted preview, reviewer note, or body payload fields")
    _assert_r48_body_free(data, source=source)


def _family_coverage_satisfied_from_rating_rows(rows: Sequence[Mapping[str, Any]], *, expected_case_count: int) -> bool:
    if expected_case_count < 24 or len(rows) < expected_case_count:
        return False
    counts: dict[str, int] = {family: 0 for family in P5_HUMAN_BLIND_QA_FAMILIES}
    for row in rows:
        family = clean_identifier(safe_mapping(row).get("family"), default="", max_length=160)
        if family in counts:
            counts[family] += 1
    minimums = safe_mapping(P7_R47_P5_FIRST_FORMAL_MINIMUMS)
    minimum_per_family = int(minimums.get("minimum_per_family") or 2)
    if any(counts[family] < minimum_per_family for family in P5_HUMAN_BLIND_QA_FAMILIES):
        return False
    if counts.get("history_line_eligible_input", 0) < int(minimums.get("minimum_history_line_eligible_input") or 4):
        return False
    boundary = safe_mapping(minimums.get("minimum_block_boundary_cases"))
    if counts.get("low_information_history_not_eligible", 0) < int(boundary.get("low_information_history_not_eligible") or 2):
        return False
    if counts.get("free_tier_history_present_not_allowed", 0) < int(boundary.get("free_tier_history_present_not_allowed") or 2):
        return False
    positive_count = sum(1 for row in rows if safe_mapping(row).get("case_role") in P7_R48_P5_POSITIVE_CASE_ROLE_REFS)
    return positive_count >= int(minimums.get("minimum_owned_history_positive_cases") or 12)


def _axis_averages_from_rating_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, float | None]:
    if not rows:
        return {axis: None for axis in P5_HUMAN_BLIND_QA_RATING_AXES}
    totals = {axis: 0.0 for axis in P5_HUMAN_BLIND_QA_RATING_AXES}
    for row in rows:
        scores = safe_mapping(row.get("axis_scores"))
        if set(scores) != set(P5_HUMAN_BLIND_QA_RATING_AXES):
            raise ValueError("R48 R11 summary requires every P5 axis on rating rows")
        for axis in P5_HUMAN_BLIND_QA_RATING_AXES:
            score = scores[axis]
            if isinstance(score, bool) or not isinstance(score, (int, float)):
                raise ValueError("R48 R11 summary axis scores must stay numeric")
            totals[axis] += float(score)
    return {axis: round(totals[axis] / len(rows), 6) for axis in P5_HUMAN_BLIND_QA_RATING_AXES}


def _axis_targets_satisfied(axis_averages: Mapping[str, Any]) -> bool:
    averages = safe_mapping(axis_averages)
    for axis, target in P5_HUMAN_BLIND_QA_TARGETS.items():
        value = averages.get(axis)
        if value is None or isinstance(value, bool) or not isinstance(value, (int, float)):
            return False
        if float(value) < float(target):
            return False
    return True


def _open_blocker_ids_from_rows(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    opened: list[str] = []
    for row in rows:
        data = safe_mapping(row)
        if data.get("blocker_status") not in {"RESOLVED", "CLOSED"}:
            blocker = clean_identifier(data.get("blocker_id"), default="", max_length=160)
            if blocker:
                opened.append(blocker)
    return dedupe_identifiers(opened, limit=240, max_length=160)


def _open_execution_blocker_ids_from_rows(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    opened: list[str] = []
    for row in rows:
        data = safe_mapping(row)
        if data.get("execution_blocker_status") not in {"RESOLVED", "CLOSED"}:
            blocker = clean_identifier(data.get("execution_blocker_id"), default="", max_length=160)
            if blocker:
                opened.append(blocker)
    return dedupe_identifiers(opened, limit=240, max_length=160)


def build_p7_r48_p5_disposal_receipt_bodyfree(
    *,
    disposal_result: Mapping[str, Any] | None = None,
    review_session_id: Any = P7_R48_REVIEW_SESSION_DEFAULT_REF,
    case_count: int = 0,
    deleted_file_count: int = 0,
    disposal_status: Any = "NOT_GENERATED",
    body_removed: bool = False,
    reviewer_notes_removed: bool = False,
    purge_started_at: Any = "purge_started_at_unset",
    purge_completed_at: Any = "purge_completed_at_unset",
) -> dict[str, Any]:
    """Build one body-free R10 disposal receipt payload without deleting files."""

    if disposal_result is not None:
        payload = safe_mapping(disposal_result)
        _assert_no_r48_receipt_or_summary_forbidden_fields(
            payload,
            source="p7_r48_disposal_receipt.disposal_result",
            forbidden_refs=P7_R48_P5_DISPOSAL_RECEIPT_FORBIDDEN_FIELD_REFS,
        )
        allowed = set(P7_R48_P5_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS)
        unknown = set(payload) - allowed
        if unknown:
            raise ValueError("R48 R10 disposal result contains fields outside the body-free receipt schema")
        review_session_id = payload.get("review_session_id", review_session_id)
        case_count = payload.get("case_count", case_count)
        deleted_file_count = payload.get("deleted_file_count", deleted_file_count)
        purge_started_at = payload.get("purge_started_at", purge_started_at)
        purge_completed_at = payload.get("purge_completed_at", purge_completed_at)
        disposal_status = payload.get("disposal_status", disposal_status)
        body_removed = payload.get("body_removed", body_removed) is True
        reviewer_notes_removed = payload.get("reviewer_notes_removed", reviewer_notes_removed) is True
        if payload.get("local_packet_exported") not in (None, False):
            raise ValueError("R48 R10 disposal receipt must keep local_packet_exported=False")
        if payload.get("content_hash_of_body_stored") not in (None, False):
            raise ValueError("R48 R10 disposal receipt must keep content_hash_of_body_stored=False")

    status = clean_identifier(disposal_status, default="NOT_GENERATED", max_length=80)
    receipt = {
        "schema_version": P7_R48_P5_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION,
        "review_session_id": clean_identifier(review_session_id, default=P7_R48_REVIEW_SESSION_DEFAULT_REF, max_length=120),
        "packet_kind": P7_R48_PACKET_KIND,
        "case_count": _non_negative_int_r48(case_count, source="R48 disposal receipt case_count"),
        "deleted_file_count": _non_negative_int_r48(deleted_file_count, source="R48 disposal receipt deleted_file_count"),
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
    assert_p7_r48_p5_disposal_receipt_bodyfree_contract(receipt)
    return receipt


def build_p7_r48_p5_review_handoff_summary_bodyfree(
    *,
    rating_rows: Sequence[Mapping[str, Any]] | None = None,
    blocker_rows: Sequence[Mapping[str, Any]] | None = None,
    execution_blocker_rows: Sequence[Mapping[str, Any]] | None = None,
    disposal_receipt: Mapping[str, Any] | None = None,
    review_session_id: Any = P7_R48_REVIEW_SESSION_DEFAULT_REF,
    review_session_status: Any = "NOT_STARTED",
    case_count: int = 24,
) -> dict[str, Any]:
    """Build a body-free R11 P5 review handoff summary from sanitized rows."""

    ratings = [safe_mapping(row) for row in (rating_rows or [])]
    blockers = [safe_mapping(row) for row in (blocker_rows or [])]
    execution_blockers = [safe_mapping(row) for row in (execution_blocker_rows or [])]
    for row in ratings:
        assert_p7_r48_p5_rating_row_bodyfree_contract(row)
    for row in blockers:
        assert_p7_r48_p5_blocker_row_bodyfree_contract(row)
    for row in execution_blockers:
        assert_p7_r48_p5_execution_blocker_row_bodyfree_contract(row)

    expected_case_count = _non_negative_int_r48(case_count, source="R48 handoff summary case_count")
    receipt = build_p7_r48_p5_disposal_receipt_bodyfree(
        review_session_id=review_session_id,
        case_count=expected_case_count,
    ) if disposal_receipt is None else safe_mapping(disposal_receipt)
    assert_p7_r48_p5_disposal_receipt_bodyfree_contract(receipt)

    status = clean_identifier(review_session_status, default="NOT_STARTED", max_length=80)
    axis_averages = _axis_averages_from_rating_rows(ratings)
    axis_targets_satisfied = _axis_targets_satisfied(axis_averages)
    open_blockers = _open_blocker_ids_from_rows(blockers)
    open_execution_blockers = _open_execution_blocker_ids_from_rows(execution_blockers)
    boundary_violations = dedupe_identifiers(
        [blocker for blocker in open_blockers if blocker in P7_R48_P5_BOUNDARY_VIOLATION_BLOCKER_ID_REFS],
        limit=40,
        max_length=160,
    )
    family_coverage_satisfied = _family_coverage_satisfied_from_rating_rows(ratings, expected_case_count=expected_case_count)
    red_case_count = sum(1 for row in ratings if row.get("verdict") == "RED")
    repair_required_case_count = sum(1 for row in ratings if row.get("verdict") == "REPAIR_REQUIRED")
    disposal_status = clean_identifier(receipt.get("disposal_status"), default="NOT_GENERATED", max_length=80)
    disposal_verified = (
        disposal_status in P7_R48_P5_CONFIRMED_ALLOWED_DISPOSAL_STATUS_REFS
        and receipt.get("body_removed") is True
        and receipt.get("reviewer_notes_removed") is True
        and receipt.get("local_packet_exported") is False
        and receipt.get("content_hash_of_body_stored") is False
    )
    all_rating_bodies_removed = bool(ratings) and all(row.get("body_removed") is True for row in ratings)
    confirmed_candidate = (
        status == "FINALIZED"
        and expected_case_count >= 24
        and len(ratings) >= expected_case_count
        and family_coverage_satisfied
        and axis_targets_satisfied
        and red_case_count == 0
        and repair_required_case_count == 0
        and not open_blockers
        and not open_execution_blockers
        and not boundary_violations
        and disposal_verified
        and all_rating_bodies_removed
    )
    summary = {
        "schema_version": P7_R48_P5_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION,
        "review_session_id": clean_identifier(review_session_id or receipt.get("review_session_id"), default=P7_R48_REVIEW_SESSION_DEFAULT_REF, max_length=120),
        "review_session_status": status,
        "review_kind": P7_R48_REVIEW_KIND,
        "packet_kind": P7_R48_PACKET_KIND,
        "case_count": expected_case_count,
        "reviewed_case_count": len(ratings),
        "rating_row_count": len(ratings),
        "blocker_row_count": len(blockers),
        "execution_blocker_row_count": len(execution_blockers),
        "family_coverage_satisfied": family_coverage_satisfied,
        "axis_averages": axis_averages,
        "axis_targets_satisfied": axis_targets_satisfied,
        "red_case_count": red_case_count,
        "repair_required_case_count": repair_required_case_count,
        "open_blocker_ids": open_blockers,
        "open_execution_blocker_ids": open_execution_blockers,
        "boundary_violation_blocker_ids": boundary_violations,
        "disposal_status": disposal_status,
        "body_removed": receipt.get("body_removed") is True,
        "reviewer_notes_removed": receipt.get("reviewer_notes_removed") is True,
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "disposal_verified_for_candidate": disposal_verified,
        "p5_human_blind_qa_confirmed_candidate": confirmed_candidate,
        "p6_limited_human_readfeel_start_allowed_candidate": confirmed_candidate,
        "release_allowed": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "hold004_close_allowed": False,
        "body_free": True,
    }
    assert_p7_r48_p5_review_handoff_summary_bodyfree_contract(summary)
    return summary


def build_p7_r48_disposal_receipt_builder_policy(
    *,
    r8_r9_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r48_disposal_receipt_builder_policy",
) -> dict[str, Any]:
    r8_r9 = safe_mapping(r8_r9_freeze) if r8_r9_freeze is not None else build_p7_r48_r8_r9_rating_blocker_rows_freeze()
    assert_p7_r48_r8_r9_rating_blocker_rows_freeze_contract(r8_r9)
    policy = {
        "schema_version": P7_R48_DISPOSAL_RECEIPT_BUILDER_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R48_STEP,
        "scope": P7_R48_SCOPE,
        "policy_kind": P7_R48_POLICY_KIND,
        "policy_section": "R10_disposal_receipt_builder",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r48_disposal_receipt_builder_policy", max_length=160),
        "r8_r9_freeze_ref": clean_identifier(r8_r9.get("material_id"), default="p7_r48_r8_r9_rating_blocker_rows_freeze", max_length=160),
        "disposal_receipt_schema_version": P7_R48_P5_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION,
        "r47_disposal_receipt_schema_version_ref": P7_R47_BODY_FREE_DISPOSAL_RECEIPT_SCHEMA_VERSION,
        "required_field_refs": list(P7_R48_P5_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS),
        "disposal_status_enum": list(P7_R47_DISPOSAL_STATUSES),
        "forbidden_field_refs": list(P7_R48_P5_DISPOSAL_RECEIPT_FORBIDDEN_FIELD_REFS),
        "disposal_receipt_builder_ready": True,
        "body_free_disposal_receipt_required_before_p5_confirmed": True,
        "body_removed_required_before_p5_confirmed": True,
        "reviewer_notes_removed_required_before_p5_confirmed": True,
        "local_packet_exported_required_false": True,
        "content_hash_of_body_required_false": True,
        "body_hash_allowed": False,
        "local_absolute_path_included": False,
        "deleted_body_preview_allowed": False,
        "reviewer_free_text_included": False,
        "actual_disposal_run_here": False,
        "actual_cleanup_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "actual_human_review_run_here": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "local_reviewer_payload_materialized_here": False,
        "implemented_steps": [*P7_R48_R8_R9_IMPLEMENTED_STEPS, "R10_disposal_receipt_builder"],
        "not_yet_implemented_steps": ["R11_p5_review_handoff_summary_builder", *P7_R48_R10_R11_NOT_YET_IMPLEMENTED_STEPS],
        "next_required_step": P7_R48_R10_NEXT_REQUIRED_STEP_REF,
        "p5_human_blind_qa_start_allowed_after_r47_policy": True,
        "p5_human_blind_qa_actual_review_start_allowed_after_r10_r11": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
        **_r10_r11_false_flags(),
    }
    assert_p7_r48_disposal_receipt_builder_policy_contract(policy)
    return policy


def build_p7_r48_p5_review_handoff_summary_builder_policy(
    *,
    r10_policy: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r48_p5_review_handoff_summary_builder_policy",
) -> dict[str, Any]:
    r10 = safe_mapping(r10_policy) if r10_policy is not None else build_p7_r48_disposal_receipt_builder_policy()
    assert_p7_r48_disposal_receipt_builder_policy_contract(r10)
    policy = {
        "schema_version": P7_R48_P5_REVIEW_HANDOFF_SUMMARY_BUILDER_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R48_STEP,
        "scope": P7_R48_SCOPE,
        "policy_kind": P7_R48_POLICY_KIND,
        "policy_section": "R11_p5_review_handoff_summary_builder",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r48_p5_review_handoff_summary_builder_policy", max_length=160),
        "r10_policy_ref": clean_identifier(r10.get("material_id"), default="p7_r48_disposal_receipt_builder_policy", max_length=160),
        "handoff_summary_schema_version": P7_R48_P5_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION,
        "required_field_refs": list(P7_R48_P5_REVIEW_HANDOFF_SUMMARY_REQUIRED_FIELD_REFS),
        "review_session_status_refs": list(P7_R48_REVIEW_SESSION_STATUS_REFS),
        "case_coverage_aggregated": True,
        "axis_averages_aggregated": True,
        "open_blockers_aggregated": True,
        "open_execution_blockers_aggregated": True,
        "disposal_status_checked": True,
        "p5_human_blind_qa_confirmed_candidate_calculated": True,
        "p6_limited_human_readfeel_start_allowed_candidate_calculated": True,
        "rating_only_confirmation_allowed": False,
        "release_allowed_from_r11": False,
        "p7_complete_from_r11": False,
        "p8_start_allowed_from_r11": False,
        "actual_human_review_run_here": False,
        "actual_disposal_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "actual_review_handoff_summary_materialized_here": False,
        "implemented_steps": list(P7_R48_R10_R11_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R48_R10_R11_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R48_R10_R11_NEXT_REQUIRED_STEP_REF,
        "p5_human_blind_qa_start_allowed_after_r47_policy": True,
        "p5_human_blind_qa_actual_review_start_allowed_after_r10_r11": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
        **_r10_r11_false_flags(),
    }
    assert_p7_r48_p5_review_handoff_summary_builder_policy_contract(policy)
    return policy


def build_p7_r48_r10_r11_disposal_handoff_summary_freeze(
    *,
    r8_r9_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r48_r10_r11_disposal_handoff_summary_freeze",
) -> dict[str, Any]:
    r8_r9 = safe_mapping(r8_r9_freeze) if r8_r9_freeze is not None else build_p7_r48_r8_r9_rating_blocker_rows_freeze()
    assert_p7_r48_r8_r9_rating_blocker_rows_freeze_contract(r8_r9)
    r10 = build_p7_r48_disposal_receipt_builder_policy(r8_r9_freeze=r8_r9)
    r11 = build_p7_r48_p5_review_handoff_summary_builder_policy(r10_policy=r10)
    freeze = {
        "schema_version": P7_R48_R10_R11_DISPOSAL_HANDOFF_SUMMARY_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R48_STEP,
        "scope": P7_R48_SCOPE,
        "policy_kind": P7_R48_POLICY_KIND,
        "freeze_kind": "r10_r11_disposal_handoff_summary_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r48_r10_r11_disposal_handoff_summary_freeze", max_length=160),
        "review_kind": P7_R48_REVIEW_KIND,
        "packet_kind": P7_R48_PACKET_KIND,
        "review_session_id": clean_identifier(r8_r9.get("review_session_id"), default=P7_R48_REVIEW_SESSION_DEFAULT_REF, max_length=120),
        "case_count": int(r8_r9.get("case_count") or 0),
        "r8_r9_rating_blocker_rows_freeze": r8_r9,
        "disposal_receipt_builder_policy": r10,
        "p5_review_handoff_summary_builder_policy": r11,
        "disposal_receipt_builder_ready": True,
        "p5_review_handoff_summary_builder_ready": True,
        "r10_disposal_receipt_schema_fixed": True,
        "r11_handoff_summary_schema_fixed": True,
        "p5_human_blind_qa_confirmed_candidate": False,
        "p6_limited_human_readfeel_start_allowed_candidate": False,
        "actual_disposal_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "actual_review_handoff_summary_materialized_here": False,
        "actual_human_review_run_here": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "local_reviewer_payload_materialized_here": False,
        "implemented_steps": list(P7_R48_R10_R11_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R48_R10_R11_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R48_R10_R11_NEXT_REQUIRED_STEP_REF,
        "p5_human_blind_qa_start_allowed_after_r47_policy": True,
        "p5_human_blind_qa_actual_review_start_allowed_after_r10_r11": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
        **_r10_r11_false_flags(),
    }
    assert_p7_r48_r10_r11_disposal_handoff_summary_freeze_contract(freeze)
    return freeze


def assert_p7_r48_p5_disposal_receipt_bodyfree_contract(receipt: Mapping[str, Any]) -> bool:
    data = safe_mapping(receipt)
    if set(data) != set(P7_R48_P5_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS):
        raise ValueError("R48 R10 disposal receipt fields must exactly match the body-free schema")
    if data.get("schema_version") != P7_R48_P5_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION:
        raise ValueError("unexpected R48 disposal receipt schema_version")
    if data.get("packet_kind") != P7_R48_PACKET_KIND:
        raise ValueError("R48 disposal receipt packet kind changed")
    for int_key in ("case_count", "deleted_file_count"):
        _non_negative_int_r48(data.get(int_key), source=f"R48 disposal receipt {int_key}")
    if data.get("disposal_status") not in P7_R47_DISPOSAL_STATUSES:
        raise ValueError("R48 disposal receipt disposal status enum changed")
    for bool_key in ("body_removed", "reviewer_notes_removed", "local_packet_exported", "content_hash_of_body_stored", "p7_material_body_free", "body_free", "release_allowed", "p7_complete", "p8_start_allowed", "hold004_close_allowed"):
        if not isinstance(data.get(bool_key), bool):
            raise ValueError(f"R48 disposal receipt requires boolean {bool_key}")
    if data.get("local_packet_exported") is not False:
        raise ValueError("R48 disposal receipt must keep local_packet_exported=False")
    if data.get("content_hash_of_body_stored") is not False:
        raise ValueError("R48 disposal receipt must keep content_hash_of_body_stored=False")
    if data.get("p7_material_body_free") is not True or data.get("body_free") is not True:
        raise ValueError("R48 disposal receipt must remain body-free P7 material")
    for false_key in ("release_allowed", "p7_complete", "p8_start_allowed", "hold004_close_allowed"):
        if data.get(false_key) is not False:
            raise ValueError(f"R48 disposal receipt must keep {false_key}=False")
    if data.get("disposal_status") in P7_R48_P5_CONFIRMED_ALLOWED_DISPOSAL_STATUS_REFS:
        if data.get("body_removed") is not True or data.get("reviewer_notes_removed") is not True:
            raise ValueError("R48 verified disposal receipt requires body and reviewer notes removed")
    _assert_no_r48_receipt_or_summary_forbidden_fields(
        data,
        source="p7_r48_p5_disposal_receipt_bodyfree",
        forbidden_refs=P7_R48_P5_DISPOSAL_RECEIPT_FORBIDDEN_FIELD_REFS,
    )
    return True


def assert_p7_r48_p5_review_handoff_summary_bodyfree_contract(summary: Mapping[str, Any]) -> bool:
    data = safe_mapping(summary)
    if set(data) != set(P7_R48_P5_REVIEW_HANDOFF_SUMMARY_REQUIRED_FIELD_REFS):
        raise ValueError("R48 R11 handoff summary fields must exactly match the body-free schema")
    if data.get("schema_version") != P7_R48_P5_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION:
        raise ValueError("unexpected R48 handoff summary schema_version")
    if data.get("review_kind") != P7_R48_REVIEW_KIND or data.get("packet_kind") != P7_R48_PACKET_KIND:
        raise ValueError("R48 handoff summary review or packet kind changed")
    if data.get("review_session_status") not in P7_R48_REVIEW_SESSION_STATUS_REFS:
        raise ValueError("R48 handoff summary session status changed")
    for int_key in ("case_count", "reviewed_case_count", "rating_row_count", "blocker_row_count", "execution_blocker_row_count", "red_case_count", "repair_required_case_count"):
        _non_negative_int_r48(data.get(int_key), source=f"R48 handoff summary {int_key}")
    averages = safe_mapping(data.get("axis_averages"))
    if set(averages) != set(P5_HUMAN_BLIND_QA_RATING_AXES):
        raise ValueError("R48 handoff summary must carry all P5 axis averages")
    for value in averages.values():
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not 0.0 <= float(value) <= 1.0):
            raise ValueError("R48 handoff summary axis averages must be null or 0.0-1.0")
    _assert_identifier_sequence_r48(data.get("open_blocker_ids"), source="p7_r48_handoff.open_blocker_ids", allowed_refs=P7_R48_READFEEL_BLOCKER_ID_REFS)
    _assert_identifier_sequence_r48(data.get("open_execution_blocker_ids"), source="p7_r48_handoff.open_execution_blocker_ids", allowed_refs=P7_R48_EXECUTION_BLOCKER_ID_REFS)
    _assert_identifier_sequence_r48(data.get("boundary_violation_blocker_ids"), source="p7_r48_handoff.boundary_violation_blocker_ids", allowed_refs=tuple(P7_R48_P5_BOUNDARY_VIOLATION_BLOCKER_ID_REFS))
    if data.get("disposal_status") not in P7_R47_DISPOSAL_STATUSES:
        raise ValueError("R48 handoff summary disposal status enum changed")
    for bool_key in ("family_coverage_satisfied", "axis_targets_satisfied", "body_removed", "reviewer_notes_removed", "local_packet_exported", "content_hash_of_body_stored", "disposal_verified_for_candidate", "p5_human_blind_qa_confirmed_candidate", "p6_limited_human_readfeel_start_allowed_candidate", "release_allowed", "p7_complete", "p8_start_allowed", "hold004_close_allowed", "body_free"):
        if not isinstance(data.get(bool_key), bool):
            raise ValueError(f"R48 handoff summary requires boolean {bool_key}")
    if data.get("local_packet_exported") is not False or data.get("content_hash_of_body_stored") is not False:
        raise ValueError("R48 handoff summary must not report exported local packet or body hash")
    for false_key in ("release_allowed", "p7_complete", "p8_start_allowed", "hold004_close_allowed"):
        if data.get(false_key) is not False:
            raise ValueError(f"R48 handoff summary must keep {false_key}=False")
    if data.get("p6_limited_human_readfeel_start_allowed_candidate") is True and data.get("p5_human_blind_qa_confirmed_candidate") is not True:
        raise ValueError("R48 R11 cannot allow P6 candidate without P5 confirmed candidate")
    if data.get("p5_human_blind_qa_confirmed_candidate") is True:
        required_true_keys = (
            "family_coverage_satisfied",
            "axis_targets_satisfied",
            "body_removed",
            "reviewer_notes_removed",
            "disposal_verified_for_candidate",
        )
        for key in required_true_keys:
            if data.get(key) is not True:
                raise ValueError(f"R48 P5 confirmed candidate requires {key}=True")
        if data.get("review_session_status") != "FINALIZED":
            raise ValueError("R48 P5 confirmed candidate requires finalized review session")
        if data.get("case_count") < 24 or data.get("reviewed_case_count") < data.get("case_count"):
            raise ValueError("R48 P5 confirmed candidate requires full case coverage")
        if data.get("red_case_count") != 0 or data.get("repair_required_case_count") != 0:
            raise ValueError("R48 P5 confirmed candidate cannot have RED or REPAIR_REQUIRED cases")
        if data.get("open_blocker_ids") or data.get("open_execution_blocker_ids") or data.get("boundary_violation_blocker_ids"):
            raise ValueError("R48 P5 confirmed candidate cannot have open blockers")
    _assert_r48_body_free(data, source="p7_r48_p5_review_handoff_summary_bodyfree")
    return True


def assert_p7_r48_disposal_receipt_builder_policy_contract(policy: Mapping[str, Any]) -> bool:
    data = safe_mapping(policy)
    _assert_common(data, schema_version=P7_R48_DISPOSAL_RECEIPT_BUILDER_SCHEMA_VERSION, source="p7_r48_r10_disposal_receipt_builder_policy")
    if data.get("policy_section") != "R10_disposal_receipt_builder":
        raise ValueError("R48 R10 policy section changed")
    if tuple(data.get("required_field_refs") or ()) != P7_R48_P5_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS:
        raise ValueError("R48 R10 disposal receipt required fields changed")
    if set(P7_R48_P5_DISPOSAL_RECEIPT_FORBIDDEN_FIELD_REFS) - set(dedupe_identifiers(data.get("forbidden_field_refs"), limit=260, max_length=160)):
        raise ValueError("R48 R10 forbidden field coverage changed")
    for true_key in ("disposal_receipt_builder_ready", "body_free_disposal_receipt_required_before_p5_confirmed", "body_removed_required_before_p5_confirmed", "reviewer_notes_removed_required_before_p5_confirmed", "local_packet_exported_required_false", "content_hash_of_body_required_false"):
        if data.get(true_key) is not True:
            raise ValueError(f"R48 R10 must keep {true_key}=True")
    for false_key in ("body_hash_allowed", "local_absolute_path_included", "deleted_body_preview_allowed", "reviewer_free_text_included", "actual_disposal_run_here", "actual_cleanup_run_here", "actual_disposal_receipt_materialized_here", "actual_human_review_run_here", "actual_body_full_packet_generated_here", "body_full_writer_created_here", "local_reviewer_payload_materialized_here"):
        if data.get(false_key) is not False:
            raise ValueError(f"R48 R10 must keep {false_key}=False")
    if tuple(data.get("implemented_steps") or ()) != (*P7_R48_R8_R9_IMPLEMENTED_STEPS, "R10_disposal_receipt_builder"):
        raise ValueError("R48 R10 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != ("R11_p5_review_handoff_summary_builder", *P7_R48_R10_R11_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("R48 R10 not-yet steps changed")
    if data.get("next_required_step") != P7_R48_R10_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R48 R10 must point to R11 next")
    _assert_r10_r11_not_ready(data, source="p7_r48_r10_disposal_receipt_builder_policy")
    return True


def assert_p7_r48_p5_review_handoff_summary_builder_policy_contract(policy: Mapping[str, Any]) -> bool:
    data = safe_mapping(policy)
    _assert_common(data, schema_version=P7_R48_P5_REVIEW_HANDOFF_SUMMARY_BUILDER_SCHEMA_VERSION, source="p7_r48_r11_p5_review_handoff_summary_builder_policy")
    if data.get("policy_section") != "R11_p5_review_handoff_summary_builder":
        raise ValueError("R48 R11 policy section changed")
    if tuple(data.get("required_field_refs") or ()) != P7_R48_P5_REVIEW_HANDOFF_SUMMARY_REQUIRED_FIELD_REFS:
        raise ValueError("R48 R11 handoff summary required fields changed")
    for true_key in ("case_coverage_aggregated", "axis_averages_aggregated", "open_blockers_aggregated", "open_execution_blockers_aggregated", "disposal_status_checked", "p5_human_blind_qa_confirmed_candidate_calculated", "p6_limited_human_readfeel_start_allowed_candidate_calculated"):
        if data.get(true_key) is not True:
            raise ValueError(f"R48 R11 must keep {true_key}=True")
    for false_key in ("rating_only_confirmation_allowed", "release_allowed_from_r11", "p7_complete_from_r11", "p8_start_allowed_from_r11", "actual_human_review_run_here", "actual_disposal_run_here", "actual_disposal_receipt_materialized_here", "actual_review_handoff_summary_materialized_here"):
        if data.get(false_key) is not False:
            raise ValueError(f"R48 R11 must keep {false_key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R48_R10_R11_IMPLEMENTED_STEPS:
        raise ValueError("R48 R11 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R48_R10_R11_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R48 R11 not-yet steps changed")
    if data.get("next_required_step") != P7_R48_R10_R11_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R48 R11 must point to R12 next")
    _assert_r10_r11_not_ready(data, source="p7_r48_r11_p5_review_handoff_summary_builder_policy")
    return True


def assert_p7_r48_r10_r11_disposal_handoff_summary_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_common(data, schema_version=P7_R48_R10_R11_DISPOSAL_HANDOFF_SUMMARY_FREEZE_SCHEMA_VERSION, source="p7_r48_r10_r11_disposal_handoff_summary_freeze")
    if data.get("freeze_kind") != "r10_r11_disposal_handoff_summary_freeze":
        raise ValueError("R48 R10/R11 freeze kind changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R48_R10_R11_IMPLEMENTED_STEPS:
        raise ValueError("R48 R10/R11 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R48_R10_R11_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R48 R10/R11 not-yet steps changed")
    assert_p7_r48_r8_r9_rating_blocker_rows_freeze_contract(safe_mapping(data.get("r8_r9_rating_blocker_rows_freeze")))
    assert_p7_r48_disposal_receipt_builder_policy_contract(safe_mapping(data.get("disposal_receipt_builder_policy")))
    assert_p7_r48_p5_review_handoff_summary_builder_policy_contract(safe_mapping(data.get("p5_review_handoff_summary_builder_policy")))
    for true_key in ("disposal_receipt_builder_ready", "p5_review_handoff_summary_builder_ready", "r10_disposal_receipt_schema_fixed", "r11_handoff_summary_schema_fixed"):
        if data.get(true_key) is not True:
            raise ValueError(f"R48 R10/R11 must keep {true_key}=True")
    if data.get("next_required_step") != P7_R48_R10_R11_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R48 R10/R11 must point to R12 next")
    _assert_r10_r11_not_ready(data, source="p7_r48_r10_r11_disposal_handoff_summary_freeze")
    return True


def _p5_confirmed_candidate_gate_missing_requirement_refs(summary: Mapping[str, Any]) -> list[str]:
    data = safe_mapping(summary)
    missing: list[str] = []
    case_count = _non_negative_int_r48(data.get("case_count"), source="R48 R12 gate case_count")
    reviewed_case_count = _non_negative_int_r48(data.get("reviewed_case_count"), source="R48 R12 gate reviewed_case_count")
    rating_row_count = _non_negative_int_r48(data.get("rating_row_count"), source="R48 R12 gate rating_row_count")
    if data.get("review_session_status") != "FINALIZED":
        missing.append("review_session_finalized")
    if case_count < 24:
        missing.append("minimum_total_cases_24")
    if reviewed_case_count < case_count or rating_row_count < case_count:
        missing.append("rating_rows_present_for_all_reviewable_cases")
    if data.get("family_coverage_satisfied") is not True:
        missing.append("family_coverage_satisfied")
    if data.get("axis_targets_satisfied") is not True:
        missing.append("axis_targets_satisfied")
    if data.get("red_case_count") != 0:
        missing.append("red_case_count_zero")
    if data.get("repair_required_case_count") != 0:
        missing.append("repair_required_case_count_zero")
    if data.get("open_blocker_ids"):
        missing.append("open_readfeel_blockers_zero")
    if data.get("open_execution_blocker_ids"):
        missing.append("open_execution_blockers_zero")
    if data.get("boundary_violation_blocker_ids"):
        missing.append("boundary_violation_blockers_zero")
    if data.get("body_removed") is not True:
        missing.append("body_removed")
    if data.get("reviewer_notes_removed") is not True:
        missing.append("reviewer_notes_removed")
    if data.get("disposal_verified_for_candidate") is not True:
        missing.append("disposal_verified_for_candidate")
    if data.get("local_packet_exported") is not False:
        missing.append("local_packet_not_exported")
    if data.get("content_hash_of_body_stored") is not False:
        missing.append("content_hash_of_body_not_stored")
    if data.get("p5_human_blind_qa_confirmed_candidate") is not True:
        missing.append("handoff_summary_candidate_claim_true")
    if data.get("p6_limited_human_readfeel_start_allowed_candidate") is not True:
        missing.append("handoff_summary_p6_candidate_consistent")
    return [ref for ref in P7_R48_P5_CONFIRMED_CANDIDATE_REQUIRED_CONDITION_REFS if ref in set(missing)]


def build_p7_r48_p5_confirmed_candidate_gate_policy(
    *,
    r10_r11_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r48_p5_confirmed_candidate_gate_policy",
) -> dict[str, Any]:
    """Build the R12 body-free policy material for the P5 confirmed-candidate gate."""

    r10_r11 = (
        safe_mapping(r10_r11_freeze)
        if r10_r11_freeze is not None
        else build_p7_r48_r10_r11_disposal_handoff_summary_freeze()
    )
    assert_p7_r48_r10_r11_disposal_handoff_summary_freeze_contract(r10_r11)
    policy = {
        "schema_version": P7_R48_P5_CONFIRMED_CANDIDATE_GATE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R48_STEP,
        "scope": P7_R48_SCOPE,
        "policy_kind": P7_R48_POLICY_KIND,
        "policy_section": "R12_p5_confirmed_candidate_gate",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r48_p5_confirmed_candidate_gate_policy", max_length=160),
        "r10_r11_freeze_ref": clean_identifier(r10_r11.get("material_id"), default="p7_r48_r10_r11_disposal_handoff_summary_freeze", max_length=160),
        "handoff_summary_schema_version": P7_R48_P5_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION,
        "required_summary_field_refs": list(P7_R48_P5_REVIEW_HANDOFF_SUMMARY_REQUIRED_FIELD_REFS),
        "required_condition_refs": list(P7_R48_P5_CONFIRMED_CANDIDATE_REQUIRED_CONDITION_REFS),
        "rating_only_confirmation_allowed": False,
        "body_removed_required": True,
        "reviewer_notes_removed_required": True,
        "disposal_verified_required": True,
        "red_or_repair_open_allowed": False,
        "policy_blocker_open_allowed": False,
        "boundary_violation_allowed": False,
        "open_execution_blocker_allowed": False,
        "local_packet_export_allowed": False,
        "body_hash_allowed": False,
        "machine_metric_confirmation_allowed": False,
        "reviewer_free_text_confirmation_allowed": False,
        "p5_confirmed_candidate_gate_ready": True,
        "actual_p5_confirmed_candidate_gate_materialized_here": False,
        "actual_human_review_run_here": False,
        "actual_disposal_run_here": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "local_reviewer_payload_materialized_here": False,
        "implemented_steps": list(P7_R48_R12_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R48_R12_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R48_R12_NEXT_REQUIRED_STEP_REF,
        "p5_human_blind_qa_start_allowed_after_r47_policy": True,
        "p5_human_blind_qa_actual_review_start_allowed_after_r12_r13": False,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
        **_r12_r13_false_flags(),
    }
    assert_p7_r48_p5_confirmed_candidate_gate_policy_contract(policy)
    return policy


def build_p7_r48_p5_confirmed_candidate_gate_bodyfree(
    *,
    handoff_summary: Mapping[str, Any] | None = None,
    review_session_id: Any = P7_R48_REVIEW_SESSION_DEFAULT_REF,
) -> dict[str, Any]:
    """Evaluate the R12 P5 confirmed-candidate gate from a body-free R11 summary."""

    summary = (
        build_p7_r48_p5_review_handoff_summary_bodyfree(review_session_id=review_session_id)
        if handoff_summary is None
        else safe_mapping(handoff_summary)
    )
    assert_p7_r48_p5_review_handoff_summary_bodyfree_contract(summary)
    missing = _p5_confirmed_candidate_gate_missing_requirement_refs(summary)
    gate_passed = not missing
    gate = {
        "schema_version": P7_R48_P5_CONFIRMED_CANDIDATE_GATE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R48_STEP,
        "scope": P7_R48_SCOPE,
        "policy_kind": P7_R48_POLICY_KIND,
        "policy_section": "R12_p5_confirmed_candidate_gate",
        "current_phase": "P7",
        "review_session_id": clean_identifier(summary.get("review_session_id"), default=P7_R48_REVIEW_SESSION_DEFAULT_REF, max_length=120),
        "review_kind": P7_R48_REVIEW_KIND,
        "packet_kind": P7_R48_PACKET_KIND,
        "handoff_summary_schema_version": P7_R48_P5_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION,
        "review_session_status": clean_identifier(summary.get("review_session_status"), default="NOT_STARTED", max_length=80),
        "required_total_cases": 24,
        "case_count": _non_negative_int_r48(summary.get("case_count"), source="R48 R12 gate case_count"),
        "reviewed_case_count": _non_negative_int_r48(summary.get("reviewed_case_count"), source="R48 R12 gate reviewed_case_count"),
        "rating_row_count": _non_negative_int_r48(summary.get("rating_row_count"), source="R48 R12 gate rating_row_count"),
        "family_coverage_satisfied": summary.get("family_coverage_satisfied") is True,
        "axis_targets_satisfied": summary.get("axis_targets_satisfied") is True,
        "red_case_count": _non_negative_int_r48(summary.get("red_case_count"), source="R48 R12 gate red_case_count"),
        "repair_required_case_count": _non_negative_int_r48(summary.get("repair_required_case_count"), source="R48 R12 gate repair_required_case_count"),
        "open_blocker_ids": _assert_identifier_sequence_r48(summary.get("open_blocker_ids"), source="p7_r48_gate.open_blocker_ids", allowed_refs=P7_R48_READFEEL_BLOCKER_ID_REFS),
        "open_execution_blocker_ids": _assert_identifier_sequence_r48(summary.get("open_execution_blocker_ids"), source="p7_r48_gate.open_execution_blocker_ids", allowed_refs=P7_R48_EXECUTION_BLOCKER_ID_REFS),
        "boundary_violation_blocker_ids": _assert_identifier_sequence_r48(summary.get("boundary_violation_blocker_ids"), source="p7_r48_gate.boundary_violation_blocker_ids", allowed_refs=tuple(P7_R48_P5_BOUNDARY_VIOLATION_BLOCKER_ID_REFS)),
        "disposal_status": clean_identifier(summary.get("disposal_status"), default="NOT_GENERATED", max_length=80),
        "body_removed": summary.get("body_removed") is True,
        "reviewer_notes_removed": summary.get("reviewer_notes_removed") is True,
        "local_packet_exported": summary.get("local_packet_exported") is True,
        "content_hash_of_body_stored": summary.get("content_hash_of_body_stored") is True,
        "disposal_verified_for_candidate": summary.get("disposal_verified_for_candidate") is True,
        "required_condition_refs": list(P7_R48_P5_CONFIRMED_CANDIDATE_REQUIRED_CONDITION_REFS),
        "missing_requirement_refs": missing,
        "failed_requirement_count": len(missing),
        "handoff_summary_candidate_claim": summary.get("p5_human_blind_qa_confirmed_candidate") is True,
        "p5_confirmed_candidate_gate_passed": gate_passed,
        "p5_human_blind_qa_confirmed_candidate": gate_passed,
        "p6_limited_human_readfeel_start_allowed_candidate": gate_passed,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "real_device_modal_review_start_allowed": False,
        "real_device_modal_review_confirmed": False,
        "actual_human_review_run_here": False,
        "actual_disposal_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "local_reviewer_payload_materialized_here": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
    }
    assert_p7_r48_p5_confirmed_candidate_gate_bodyfree_contract(gate)
    return gate


def assert_p7_r48_no_body_free_leak_guard_bodyfree_material(
    material: Mapping[str, Any], *, source: str = "p7_r48_body_free_material"
) -> bool:
    data = safe_mapping(material)
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must declare body_free=True before R13 leak guard validation")
    if _contains_forbidden_key_ref(data, set(P7_R48_BODY_FREE_LEAK_GUARD_FORBIDDEN_FIELD_REFS)):
        raise ValueError(f"{source} contains local-only reviewer packet, reviewer note, body hash, local path, or body payload fields")
    _assert_r48_body_free(data, source=source)
    return True


def build_p7_r48_r47_regression_no_body_free_leak_guard(
    *,
    r12_policy: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r48_r47_regression_no_body_free_leak_guard",
) -> dict[str, Any]:
    """Build the R13 body-free R47 regression/no body-free leak guard policy material."""

    r12 = safe_mapping(r12_policy) if r12_policy is not None else build_p7_r48_p5_confirmed_candidate_gate_policy()
    assert_p7_r48_p5_confirmed_candidate_gate_policy_contract(r12)
    r47_freeze = build_p7_r47_r14_r15_validation_touch_boundary_freeze()
    assert_p7_r47_r14_r15_validation_touch_boundary_freeze_contract(r47_freeze)
    policy = {
        "schema_version": P7_R48_R47_REGRESSION_NO_BODY_FREE_LEAK_GUARD_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R48_STEP,
        "scope": P7_R48_SCOPE,
        "policy_kind": P7_R48_POLICY_KIND,
        "policy_section": "R13_r47_regression_no_body_free_leak_guard",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r48_r47_regression_no_body_free_leak_guard", max_length=160),
        "r12_policy_ref": clean_identifier(r12.get("material_id"), default="p7_r48_p5_confirmed_candidate_gate_policy", max_length=160),
        "r47_handoff_schema_version": clean_identifier(r47_freeze.get("schema_version"), default=P7_R47_R14_R15_VALIDATION_TOUCH_BOUNDARY_SCHEMA_VERSION, max_length=180),
        "r47_policy_ready_required": True,
        "r47_target_regression_required": True,
        "r47_target_regression_test_refs": list(P7_R48_R47_TARGET_REGRESSION_TEST_REFS),
        "r47_target_regression_executed_here": False,
        "no_body_free_leak_guard_ready": True,
        "body_free_leak_guard_forbidden_field_refs": list(P7_R48_BODY_FREE_LEAK_GUARD_FORBIDDEN_FIELD_REFS),
        "body_free_material_guarded_refs": [
            "controller_manifest",
            "case_matrix",
            "rating_rows",
            "blocker_rows",
            "execution_blocker_rows",
            "disposal_receipt",
            "p5_review_handoff_summary",
            "p5_confirmed_candidate_gate",
        ],
        "reviewer_packet_payload_bodyfree_allowed": False,
        "reviewer_notes_bodyfree_allowed": False,
        "body_hash_bodyfree_allowed": False,
        "local_absolute_path_bodyfree_allowed": False,
        "local_only_body_payload_bodyfree_allowed": False,
        "actual_no_body_free_leak_scan_executed_here": False,
        "actual_human_review_run_here": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "local_reviewer_payload_materialized_here": False,
        "implemented_steps": list(P7_R48_R12_R13_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R48_R12_R13_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R48_R12_R13_NEXT_REQUIRED_STEP_REF,
        "p5_human_blind_qa_start_allowed_after_r47_policy": True,
        "p5_human_blind_qa_actual_review_start_allowed_after_r12_r13": False,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
        **_r12_r13_false_flags(),
    }
    assert_p7_r48_r47_regression_no_body_free_leak_guard_contract(policy)
    return policy


def build_p7_r48_r12_r13_confirmed_gate_leak_guard_freeze(
    *,
    r10_r11_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r48_r12_r13_confirmed_gate_leak_guard_freeze",
) -> dict[str, Any]:
    r10_r11 = (
        safe_mapping(r10_r11_freeze)
        if r10_r11_freeze is not None
        else build_p7_r48_r10_r11_disposal_handoff_summary_freeze()
    )
    assert_p7_r48_r10_r11_disposal_handoff_summary_freeze_contract(r10_r11)
    r12 = build_p7_r48_p5_confirmed_candidate_gate_policy(r10_r11_freeze=r10_r11)
    r13 = build_p7_r48_r47_regression_no_body_free_leak_guard(r12_policy=r12)
    freeze = {
        "schema_version": P7_R48_R12_R13_CONFIRMED_GATE_LEAK_GUARD_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R48_STEP,
        "scope": P7_R48_SCOPE,
        "policy_kind": P7_R48_POLICY_KIND,
        "freeze_kind": "r12_r13_confirmed_gate_leak_guard_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r48_r12_r13_confirmed_gate_leak_guard_freeze", max_length=160),
        "review_kind": P7_R48_REVIEW_KIND,
        "packet_kind": P7_R48_PACKET_KIND,
        "review_session_id": clean_identifier(r10_r11.get("review_session_id"), default=P7_R48_REVIEW_SESSION_DEFAULT_REF, max_length=120),
        "case_count": int(r10_r11.get("case_count") or 0),
        "r10_r11_disposal_handoff_summary_freeze": r10_r11,
        "p5_confirmed_candidate_gate_policy": r12,
        "r47_regression_no_body_free_leak_guard": r13,
        "p5_confirmed_candidate_gate_ready": True,
        "no_body_free_leak_guard_ready": True,
        "r47_target_regression_required": True,
        "r47_target_regression_executed_here": False,
        "actual_no_body_free_leak_scan_executed_here": False,
        "p5_human_blind_qa_confirmed_candidate": False,
        "p6_limited_human_readfeel_start_allowed_candidate": False,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "actual_human_review_run_here": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "local_reviewer_payload_materialized_here": False,
        "implemented_steps": list(P7_R48_R12_R13_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R48_R12_R13_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R48_R12_R13_NEXT_REQUIRED_STEP_REF,
        "p5_human_blind_qa_start_allowed_after_r47_policy": True,
        "p5_human_blind_qa_actual_review_start_allowed_after_r12_r13": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
        **_r12_r13_false_flags(),
    }
    assert_p7_r48_r12_r13_confirmed_gate_leak_guard_freeze_contract(freeze)
    return freeze



def _r46_handoff_regression_bodyfree_snapshot() -> dict[str, Any]:
    """Build and contract-check the R46 handoff materials without retaining bodies."""

    p5 = build_p5_human_blind_qa_handoff_material()
    assert_p5_human_blind_qa_handoff_material_contract(p5)
    p6 = build_p6_limited_human_readfeel_handoff_material()
    assert_p6_limited_human_readfeel_handoff_material_contract(p6)
    p5_p6 = build_p5_p6_human_readfeel_handoff_summary(p5_material=p5, p6_material=p6)
    assert_p5_p6_human_readfeel_handoff_summary_contract(p5_p6)

    real_device_checklist = build_real_device_submit_modal_readfeel_checklist()
    assert_real_device_submit_modal_readfeel_checklist_contract(real_device_checklist)
    closed_validation = build_p7_hold_release_p8_closed_validation(real_device_checklist=real_device_checklist)
    assert_p7_hold_release_p8_closed_validation_contract(closed_validation)
    real_device_summary = build_real_device_and_closed_validation_summary(
        checklist=real_device_checklist,
        closed_validation=closed_validation,
    )
    assert_real_device_and_closed_validation_summary_contract(real_device_summary)

    next_summary = build_p7_r46_next_decision_summary(closed_validation=closed_validation)
    assert_p7_r46_next_decision_summary_contract(next_summary)
    next_ledger = build_p7_r46_next_decision_handoff_ledger(closed_validation=closed_validation)
    assert_p7_r46_next_decision_handoff_ledger_contract(next_ledger)

    unresolved_hold_refs = dedupe_identifiers(
        [
            *dedupe_identifiers(p5_p6.get("unresolved_hold_refs"), limit=80, max_length=120),
            *dedupe_identifiers(real_device_summary.get("unresolved_hold_refs"), limit=80, max_length=120),
            *dedupe_identifiers(next_ledger.get("unresolved_hold_refs"), limit=120, max_length=120),
        ],
        limit=160,
        max_length=120,
    )
    snapshot = {
        "schema_version_refs": {
            "p5_human_blind_qa_handoff": P7_R46_P5_HUMAN_BLIND_QA_HANDOFF_SCHEMA_VERSION,
            "p6_limited_human_readfeel_handoff": P7_R46_P6_LIMITED_HUMAN_READFEEL_HANDOFF_SCHEMA_VERSION,
            "p5_p6_human_readfeel_handoff_summary": P7_R46_P5_P6_HUMAN_READFEEL_HANDOFF_SUMMARY_SCHEMA_VERSION,
            "real_device_modal_review_checklist": P7_R46_REAL_DEVICE_MODAL_REVIEW_CHECKLIST_SCHEMA_VERSION,
            "hold_release_p8_closed_validation": P7_R46_HOLD_RELEASE_P8_CLOSED_VALIDATION_SCHEMA_VERSION,
            "real_device_and_closed_validation_summary": P7_R46_REAL_DEVICE_AND_CLOSED_VALIDATION_SUMMARY_SCHEMA_VERSION,
            "next_decision_summary": P7_R46_NEXT_DECISION_SUMMARY_SCHEMA_VERSION,
            "next_decision_handoff_ledger": P7_R46_NEXT_DECISION_HANDOFF_LEDGER_SCHEMA_VERSION,
        },
        "material_refs": {
            "p5_material_ref": clean_identifier(p5.get("material_id"), default="p7_r46_p5_human_blind_qa_handoff_material", max_length=160),
            "p6_material_ref": clean_identifier(p6.get("material_id"), default="p7_r46_p6_limited_human_readfeel_handoff_material", max_length=160),
            "p5_p6_summary_ref": clean_identifier(p5_p6.get("material_id"), default="p7_r46_p5_p6_human_readfeel_handoff_summary", max_length=160),
            "real_device_summary_ref": clean_identifier(real_device_summary.get("material_id"), default="p7_r46_real_device_and_closed_validation_summary", max_length=160),
            "next_decision_summary_ref": clean_identifier(next_summary.get("material_id"), default="p7_r46_next_decision_summary", max_length=160),
            "next_decision_ledger_ref": clean_identifier(next_ledger.get("material_id"), default="p7_r46_next_decision_handoff_ledger", max_length=160),
        },
        "unresolved_hold_refs": unresolved_hold_refs,
        "required_unresolved_hold_refs": list(P7_R48_REQUIRED_UNRESOLVED_HOLD_REFS),
        "p5_human_blind_qa_start_allowed_after_r46_ledger": next_ledger.get("p5_human_blind_qa_start_allowed") is True,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed": next_ledger.get("p6_limited_human_readfeel_start_allowed") is True,
        "p6_limited_human_readfeel_confirmed": False,
        "real_device_modal_review_start_allowed": next_ledger.get("real_device_modal_review_start_allowed") is True,
        "real_device_modal_review_confirmed": False,
        "human_review_confirmed": False,
        "manual_real_device_review_confirmed": False,
        "release_allowed": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "hold004_close_allowed": False,
        "body_free": True,
    }
    _assert_r48_body_free(snapshot, source="p7_r48_r46_handoff_regression_snapshot")
    return snapshot


def build_p7_r48_r46_handoff_regression_policy(
    *,
    r12_r13_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r48_r46_handoff_regression_policy",
) -> dict[str, Any]:
    """Build the R14 body-free R46 handoff regression policy material."""

    r13 = (
        safe_mapping(r12_r13_freeze)
        if r12_r13_freeze is not None
        else build_p7_r48_r12_r13_confirmed_gate_leak_guard_freeze()
    )
    assert_p7_r48_r12_r13_confirmed_gate_leak_guard_freeze_contract(r13)
    snapshot = _r46_handoff_regression_bodyfree_snapshot()
    policy = {
        "schema_version": P7_R48_R46_HANDOFF_REGRESSION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R48_STEP,
        "scope": P7_R48_SCOPE,
        "policy_kind": P7_R48_POLICY_KIND,
        "policy_section": "R14_r46_handoff_regression",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r48_r46_handoff_regression_policy", max_length=160),
        "r12_r13_freeze_ref": clean_identifier(r13.get("material_id"), default="p7_r48_r12_r13_confirmed_gate_leak_guard_freeze", max_length=160),
        "r46_handoff_regression_required": True,
        "r46_p5_p6_handoff_regression_required": True,
        "r46_real_device_closed_validation_regression_required": True,
        "r46_next_decision_ledger_regression_required": True,
        "r46_handoff_regression_test_refs": list(P7_R48_R46_HANDOFF_REGRESSION_TEST_REFS),
        "r46_handoff_regression_executed_here": False,
        "actual_r46_handoff_regression_executed_here": False,
        "r46_contract_builders_checked_here": True,
        "r46_schema_version_refs": dict(snapshot["schema_version_refs"]),
        "r46_material_refs": dict(snapshot["material_refs"]),
        "unresolved_hold_refs": list(snapshot["unresolved_hold_refs"]),
        "required_unresolved_hold_refs": list(P7_R48_REQUIRED_UNRESOLVED_HOLD_REFS),
        "p5_human_blind_qa_start_allowed_after_r46_ledger": snapshot["p5_human_blind_qa_start_allowed_after_r46_ledger"],
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "real_device_modal_review_start_allowed": False,
        "real_device_modal_review_confirmed": False,
        "human_review_confirmed": False,
        "manual_real_device_review_confirmed": False,
        "body_full_packet_materialized_here": False,
        "local_reviewer_payload_materialized_here": False,
        "actual_human_review_run_here": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "implemented_steps": list(P7_R48_R14_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R48_R14_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R48_R14_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
        **_r14_r15_false_flags(),
    }
    policy["p5_human_blind_qa_start_allowed_after_r46_ledger"] = snapshot[
        "p5_human_blind_qa_start_allowed_after_r46_ledger"
    ]
    assert_p7_r48_r46_handoff_regression_policy_contract(policy)
    return policy


def build_p7_r48_p5_core_subset_regression_policy(
    *,
    r46_handoff_regression_policy: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r48_p5_core_subset_regression_policy",
) -> dict[str, Any]:
    """Build the R15 body-free P5 core subset regression policy material."""

    r14 = (
        safe_mapping(r46_handoff_regression_policy)
        if r46_handoff_regression_policy is not None
        else build_p7_r48_r46_handoff_regression_policy()
    )
    assert_p7_r48_r46_handoff_regression_policy_contract(r14)
    policy = {
        "schema_version": P7_R48_P5_CORE_SUBSET_REGRESSION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R48_STEP,
        "scope": P7_R48_SCOPE,
        "policy_kind": P7_R48_POLICY_KIND,
        "policy_section": "R15_p5_core_subset_regression",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r48_p5_core_subset_regression_policy", max_length=160),
        "r46_handoff_regression_policy_ref": clean_identifier(r14.get("material_id"), default="p7_r48_r46_handoff_regression_policy", max_length=160),
        "p5_core_subset_regression_required": True,
        "p5_core_subset_regression_test_refs": list(P7_R48_P5_CORE_SUBSET_REGRESSION_TEST_REFS),
        "p5_product_quality_qa_optional_regression_test_refs": list(P7_R48_P5_PRODUCT_QUALITY_QA_OPTIONAL_REGRESSION_TEST_REFS),
        "p5_product_quality_qa_required_here": False,
        "p5_core_subset_regression_executed_here": False,
        "actual_p5_core_subset_regression_executed_here": False,
        "p5_core_subset_green_confirmed_here": False,
        "p5_core_subset_green_claim_allowed": False,
        "p5_existing_boundary_preserved_required": True,
        "p5_runtime_changed_here": False,
        "p5_gate_relaxed_here": False,
        "api_response_shape_changed_here": False,
        "db_schema_changed_here": False,
        "emlis_reply_runtime_changed_here": False,
        "public_response_top_level_key_added_here": False,
        "rn_contract_changed_here": False,
        "actual_human_review_run_here": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "local_reviewer_payload_materialized_here": False,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "real_device_modal_review_start_allowed": False,
        "real_device_modal_review_confirmed": False,
        "implemented_steps": list(P7_R48_R14_R15_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R48_R14_R15_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R48_R14_R15_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
        **_r14_r15_false_flags(),
    }
    assert_p7_r48_p5_core_subset_regression_policy_contract(policy)
    return policy


def build_p7_r48_r14_r15_regression_freeze(
    *,
    r12_r13_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r48_r14_r15_regression_freeze",
) -> dict[str, Any]:
    """Build the R14/R15 combined body-free regression freeze."""

    r13 = (
        safe_mapping(r12_r13_freeze)
        if r12_r13_freeze is not None
        else build_p7_r48_r12_r13_confirmed_gate_leak_guard_freeze()
    )
    assert_p7_r48_r12_r13_confirmed_gate_leak_guard_freeze_contract(r13)
    r14 = build_p7_r48_r46_handoff_regression_policy(r12_r13_freeze=r13)
    r15 = build_p7_r48_p5_core_subset_regression_policy(r46_handoff_regression_policy=r14)
    freeze = {
        "schema_version": P7_R48_R14_R15_REGRESSION_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R48_STEP,
        "scope": P7_R48_SCOPE,
        "policy_kind": P7_R48_POLICY_KIND,
        "freeze_kind": "r14_r15_regression_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r48_r14_r15_regression_freeze", max_length=160),
        "r12_r13_confirmed_gate_leak_guard_freeze": r13,
        "r46_handoff_regression_policy": r14,
        "p5_core_subset_regression_policy": r15,
        "r46_handoff_regression_required": True,
        "p5_core_subset_regression_required": True,
        "r46_handoff_regression_executed_here": False,
        "p5_core_subset_regression_executed_here": False,
        "actual_r46_handoff_regression_executed_here": False,
        "actual_p5_core_subset_regression_executed_here": False,
        "p5_core_subset_green_confirmed_here": False,
        "p5_core_subset_green_claim_allowed": False,
        "p5_runtime_changed_here": False,
        "p5_gate_relaxed_here": False,
        "api_response_shape_changed_here": False,
        "db_schema_changed_here": False,
        "emlis_reply_runtime_changed_here": False,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "real_device_modal_review_start_allowed": False,
        "real_device_modal_review_confirmed": False,
        "actual_human_review_run_here": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "local_reviewer_payload_materialized_here": False,
        "implemented_steps": list(P7_R48_R14_R15_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R48_R14_R15_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R48_R14_R15_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
        **_r14_r15_false_flags(),
    }
    assert_p7_r48_r14_r15_regression_freeze_contract(freeze)
    return freeze

def assert_p7_r48_p5_confirmed_candidate_gate_bodyfree_contract(gate: Mapping[str, Any]) -> bool:
    data = safe_mapping(gate)
    if set(data) != set(P7_R48_P5_CONFIRMED_CANDIDATE_GATE_REQUIRED_FIELD_REFS):
        raise ValueError("R48 R12 confirmed candidate gate fields must exactly match the body-free schema")
    _assert_common(data, schema_version=P7_R48_P5_CONFIRMED_CANDIDATE_GATE_SCHEMA_VERSION, source="p7_r48_r12_p5_confirmed_candidate_gate")
    if data.get("policy_section") != "R12_p5_confirmed_candidate_gate":
        raise ValueError("R48 R12 gate section changed")
    if data.get("review_kind") != P7_R48_REVIEW_KIND or data.get("packet_kind") != P7_R48_PACKET_KIND:
        raise ValueError("R48 R12 gate review or packet kind changed")
    if data.get("handoff_summary_schema_version") != P7_R48_P5_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R48 R12 gate must consume the R11 body-free handoff summary")
    if data.get("review_session_status") not in P7_R48_REVIEW_SESSION_STATUS_REFS:
        raise ValueError("R48 R12 gate review session status changed")
    for int_key in ("required_total_cases", "case_count", "reviewed_case_count", "rating_row_count", "red_case_count", "repair_required_case_count", "failed_requirement_count"):
        _non_negative_int_r48(data.get(int_key), source=f"R48 R12 gate {int_key}")
    if data.get("required_total_cases") != 24:
        raise ValueError("R48 R12 confirmed candidate gate requires 24 cases")
    _assert_identifier_sequence_r48(data.get("open_blocker_ids"), source="p7_r48_gate.open_blocker_ids", allowed_refs=P7_R48_READFEEL_BLOCKER_ID_REFS)
    _assert_identifier_sequence_r48(data.get("open_execution_blocker_ids"), source="p7_r48_gate.open_execution_blocker_ids", allowed_refs=P7_R48_EXECUTION_BLOCKER_ID_REFS)
    _assert_identifier_sequence_r48(data.get("boundary_violation_blocker_ids"), source="p7_r48_gate.boundary_violation_blocker_ids", allowed_refs=tuple(P7_R48_P5_BOUNDARY_VIOLATION_BLOCKER_ID_REFS))
    required_refs = _assert_identifier_sequence_r48(data.get("required_condition_refs"), source="p7_r48_gate.required_condition_refs", allowed_refs=P7_R48_P5_CONFIRMED_CANDIDATE_REQUIRED_CONDITION_REFS)
    missing_refs = _assert_identifier_sequence_r48(data.get("missing_requirement_refs"), source="p7_r48_gate.missing_requirement_refs", allowed_refs=P7_R48_P5_CONFIRMED_CANDIDATE_REQUIRED_CONDITION_REFS)
    if tuple(required_refs) != P7_R48_P5_CONFIRMED_CANDIDATE_REQUIRED_CONDITION_REFS:
        raise ValueError("R48 R12 confirmed candidate required refs changed")
    if data.get("failed_requirement_count") != len(missing_refs):
        raise ValueError("R48 R12 failed requirement count must match missing requirement refs")
    if data.get("disposal_status") not in P7_R47_DISPOSAL_STATUSES:
        raise ValueError("R48 R12 gate disposal status enum changed")
    for bool_key in ("family_coverage_satisfied", "axis_targets_satisfied", "body_removed", "reviewer_notes_removed", "local_packet_exported", "content_hash_of_body_stored", "disposal_verified_for_candidate", "handoff_summary_candidate_claim", "p5_confirmed_candidate_gate_passed", "p5_human_blind_qa_confirmed_candidate", "p6_limited_human_readfeel_start_allowed_candidate", "p5_human_blind_qa_confirmed", "p6_limited_human_readfeel_start_allowed", "p6_limited_human_readfeel_confirmed", "real_device_modal_review_start_allowed", "real_device_modal_review_confirmed", "actual_human_review_run_here", "actual_disposal_run_here", "actual_disposal_receipt_materialized_here", "actual_body_full_packet_generated_here", "body_full_writer_created_here", "local_reviewer_payload_materialized_here", "body_free"):
        if not isinstance(data.get(bool_key), bool):
            raise ValueError(f"R48 R12 gate requires boolean {bool_key}")
    if data.get("local_packet_exported") is not False or data.get("content_hash_of_body_stored") is not False:
        raise ValueError("R48 R12 gate must keep local packet export and body hash false")
    for false_key in ("p5_human_blind_qa_confirmed", "p6_limited_human_readfeel_start_allowed", "p6_limited_human_readfeel_confirmed", "real_device_modal_review_start_allowed", "real_device_modal_review_confirmed", "actual_human_review_run_here", "actual_disposal_run_here", "actual_disposal_receipt_materialized_here", "actual_body_full_packet_generated_here", "body_full_writer_created_here", "local_reviewer_payload_materialized_here"):
        if data.get(false_key) is not False:
            raise ValueError(f"R48 R12 gate must keep actual flag {false_key}=False")
    gate_passed = data.get("p5_confirmed_candidate_gate_passed") is True
    if data.get("p5_human_blind_qa_confirmed_candidate") is not gate_passed:
        raise ValueError("R48 R12 P5 candidate must equal the gate result")
    if data.get("p6_limited_human_readfeel_start_allowed_candidate") is not gate_passed:
        raise ValueError("R48 R12 P6 candidate must equal the P5 candidate gate result")
    if gate_passed:
        if missing_refs:
            raise ValueError("R48 R12 gate cannot pass with missing requirements")
        for key in ("family_coverage_satisfied", "axis_targets_satisfied", "body_removed", "reviewer_notes_removed", "disposal_verified_for_candidate", "handoff_summary_candidate_claim"):
            if data.get(key) is not True:
                raise ValueError(f"R48 R12 gate pass requires {key}=True")
        if data.get("review_session_status") != "FINALIZED" or data.get("case_count") < 24 or data.get("reviewed_case_count") < data.get("case_count") or data.get("rating_row_count") < data.get("case_count"):
            raise ValueError("R48 R12 gate pass requires finalized full 24-case coverage")
        if data.get("red_case_count") != 0 or data.get("repair_required_case_count") != 0 or data.get("open_blocker_ids") or data.get("open_execution_blocker_ids") or data.get("boundary_violation_blocker_ids"):
            raise ValueError("R48 R12 gate pass cannot have RED, repair, open blockers, or boundary violations")
    assert_p7_r48_no_body_free_leak_guard_bodyfree_material(data, source="p7_r48_r12_p5_confirmed_candidate_gate")
    return True


def assert_p7_r48_p5_confirmed_candidate_gate_policy_contract(policy: Mapping[str, Any]) -> bool:
    data = safe_mapping(policy)
    _assert_common(data, schema_version=P7_R48_P5_CONFIRMED_CANDIDATE_GATE_SCHEMA_VERSION, source="p7_r48_r12_p5_confirmed_candidate_gate_policy")
    if data.get("policy_section") != "R12_p5_confirmed_candidate_gate":
        raise ValueError("R48 R12 policy section changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R48_R12_IMPLEMENTED_STEPS:
        raise ValueError("R48 R12 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R48_R12_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R48 R12 not-yet steps changed")
    if tuple(data.get("required_condition_refs") or ()) != P7_R48_P5_CONFIRMED_CANDIDATE_REQUIRED_CONDITION_REFS:
        raise ValueError("R48 R12 confirmed candidate requirements changed")
    if set(P7_R48_P5_REVIEW_HANDOFF_SUMMARY_REQUIRED_FIELD_REFS) - set(dedupe_identifiers(data.get("required_summary_field_refs"), limit=120, max_length=160)):
        raise ValueError("R48 R12 required summary field coverage changed")
    for true_key in ("body_removed_required", "reviewer_notes_removed_required", "disposal_verified_required", "p5_confirmed_candidate_gate_ready"):
        if data.get(true_key) is not True:
            raise ValueError(f"R48 R12 policy must keep {true_key}=True")
    for false_key in ("rating_only_confirmation_allowed", "red_or_repair_open_allowed", "policy_blocker_open_allowed", "boundary_violation_allowed", "open_execution_blocker_allowed", "local_packet_export_allowed", "body_hash_allowed", "machine_metric_confirmation_allowed", "reviewer_free_text_confirmation_allowed", "actual_p5_confirmed_candidate_gate_materialized_here", "actual_human_review_run_here", "actual_disposal_run_here", "actual_body_full_packet_generated_here", "body_full_writer_created_here", "local_reviewer_payload_materialized_here"):
        if data.get(false_key) is not False:
            raise ValueError(f"R48 R12 policy must keep {false_key}=False")
    if data.get("next_required_step") != P7_R48_R12_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R48 R12 policy must point to R13 next")
    _assert_r12_r13_not_actualized(data, source="p7_r48_r12_p5_confirmed_candidate_gate_policy")
    return True


def assert_p7_r48_r47_regression_no_body_free_leak_guard_contract(policy: Mapping[str, Any]) -> bool:
    data = safe_mapping(policy)
    _assert_common(data, schema_version=P7_R48_R47_REGRESSION_NO_BODY_FREE_LEAK_GUARD_SCHEMA_VERSION, source="p7_r48_r13_r47_regression_no_body_free_leak_guard")
    if data.get("policy_section") != "R13_r47_regression_no_body_free_leak_guard":
        raise ValueError("R48 R13 policy section changed")
    if data.get("r47_policy_ready_required") is not True or data.get("r47_target_regression_required") is not True:
        raise ValueError("R48 R13 must require R47 policy ready and target regression")
    if tuple(data.get("r47_target_regression_test_refs") or ()) != P7_R48_R47_TARGET_REGRESSION_TEST_REFS:
        raise ValueError("R48 R13 R47 regression test refs changed")
    if data.get("r47_target_regression_executed_here") is not False:
        raise ValueError("R48 R13 policy must not claim R47 regression was executed by the builder")
    if data.get("no_body_free_leak_guard_ready") is not True:
        raise ValueError("R48 R13 no body-free leak guard must be ready")
    if set(P7_R48_BODY_FREE_LEAK_GUARD_FORBIDDEN_FIELD_REFS) - set(dedupe_identifiers(data.get("body_free_leak_guard_forbidden_field_refs"), limit=260, max_length=160)):
        raise ValueError("R48 R13 body-free leak guard forbidden refs changed")
    for false_key in ("reviewer_packet_payload_bodyfree_allowed", "reviewer_notes_bodyfree_allowed", "body_hash_bodyfree_allowed", "local_absolute_path_bodyfree_allowed", "local_only_body_payload_bodyfree_allowed", "actual_no_body_free_leak_scan_executed_here", "actual_human_review_run_here", "actual_body_full_packet_generated_here", "body_full_writer_created_here", "local_reviewer_payload_materialized_here"):
        if data.get(false_key) is not False:
            raise ValueError(f"R48 R13 must keep {false_key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R48_R12_R13_IMPLEMENTED_STEPS:
        raise ValueError("R48 R13 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R48_R12_R13_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R48 R13 not-yet steps changed")
    if data.get("next_required_step") != P7_R48_R12_R13_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R48 R13 must point to R14 next")
    _assert_r12_r13_not_actualized(data, source="p7_r48_r13_r47_regression_no_body_free_leak_guard")
    return True


def assert_p7_r48_r12_r13_confirmed_gate_leak_guard_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_common(data, schema_version=P7_R48_R12_R13_CONFIRMED_GATE_LEAK_GUARD_FREEZE_SCHEMA_VERSION, source="p7_r48_r12_r13_confirmed_gate_leak_guard_freeze")
    if data.get("freeze_kind") != "r12_r13_confirmed_gate_leak_guard_freeze":
        raise ValueError("R48 R12/R13 freeze kind changed")
    assert_p7_r48_r10_r11_disposal_handoff_summary_freeze_contract(safe_mapping(data.get("r10_r11_disposal_handoff_summary_freeze")))
    assert_p7_r48_p5_confirmed_candidate_gate_policy_contract(safe_mapping(data.get("p5_confirmed_candidate_gate_policy")))
    assert_p7_r48_r47_regression_no_body_free_leak_guard_contract(safe_mapping(data.get("r47_regression_no_body_free_leak_guard")))
    for true_key in ("p5_confirmed_candidate_gate_ready", "no_body_free_leak_guard_ready", "r47_target_regression_required"):
        if data.get(true_key) is not True:
            raise ValueError(f"R48 R12/R13 freeze must keep {true_key}=True")
    for false_key in ("r47_target_regression_executed_here", "actual_no_body_free_leak_scan_executed_here", "p5_human_blind_qa_confirmed_candidate", "p6_limited_human_readfeel_start_allowed_candidate", "p5_human_blind_qa_confirmed", "p6_limited_human_readfeel_start_allowed", "p6_limited_human_readfeel_confirmed", "actual_human_review_run_here", "actual_body_full_packet_generated_here", "body_full_writer_created_here", "local_reviewer_payload_materialized_here"):
        if data.get(false_key) is not False:
            raise ValueError(f"R48 R12/R13 freeze must keep {false_key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R48_R12_R13_IMPLEMENTED_STEPS:
        raise ValueError("R48 R12/R13 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R48_R12_R13_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R48 R12/R13 not-yet steps changed")
    if data.get("next_required_step") != P7_R48_R12_R13_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R48 R12/R13 must point to R14 next")
    _assert_r12_r13_not_actualized(data, source="p7_r48_r12_r13_confirmed_gate_leak_guard_freeze")
    return True



def _assert_r14_r15_not_actualized(data: Mapping[str, Any], *, source: str) -> None:
    for key in _R48_R14_R15_FALSE_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=False during R48 R14/R15")


def assert_p7_r48_r46_handoff_regression_policy_contract(policy: Mapping[str, Any]) -> bool:
    data = safe_mapping(policy)
    _assert_common(data, schema_version=P7_R48_R46_HANDOFF_REGRESSION_SCHEMA_VERSION, source="p7_r48_r14_r46_handoff_regression_policy")
    if data.get("policy_section") != "R14_r46_handoff_regression":
        raise ValueError("R48 R14 policy section changed")
    for true_key in (
        "r46_handoff_regression_required",
        "r46_p5_p6_handoff_regression_required",
        "r46_real_device_closed_validation_regression_required",
        "r46_next_decision_ledger_regression_required",
        "r46_contract_builders_checked_here",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R48 R14 must keep {true_key}=True")
    if tuple(data.get("r46_handoff_regression_test_refs") or ()) != P7_R48_R46_HANDOFF_REGRESSION_TEST_REFS:
        raise ValueError("R48 R14 R46 regression test refs changed")
    schema_refs = safe_mapping(data.get("r46_schema_version_refs"))
    expected_schema_refs = {
        "p5_human_blind_qa_handoff": P7_R46_P5_HUMAN_BLIND_QA_HANDOFF_SCHEMA_VERSION,
        "p6_limited_human_readfeel_handoff": P7_R46_P6_LIMITED_HUMAN_READFEEL_HANDOFF_SCHEMA_VERSION,
        "p5_p6_human_readfeel_handoff_summary": P7_R46_P5_P6_HUMAN_READFEEL_HANDOFF_SUMMARY_SCHEMA_VERSION,
        "real_device_modal_review_checklist": P7_R46_REAL_DEVICE_MODAL_REVIEW_CHECKLIST_SCHEMA_VERSION,
        "hold_release_p8_closed_validation": P7_R46_HOLD_RELEASE_P8_CLOSED_VALIDATION_SCHEMA_VERSION,
        "real_device_and_closed_validation_summary": P7_R46_REAL_DEVICE_AND_CLOSED_VALIDATION_SUMMARY_SCHEMA_VERSION,
        "next_decision_summary": P7_R46_NEXT_DECISION_SUMMARY_SCHEMA_VERSION,
        "next_decision_handoff_ledger": P7_R46_NEXT_DECISION_HANDOFF_LEDGER_SCHEMA_VERSION,
    }
    if schema_refs != expected_schema_refs:
        raise ValueError("R48 R14 R46 schema refs changed")
    unresolved = set(dedupe_identifiers(data.get("unresolved_hold_refs"), limit=160, max_length=120))
    required = set(P7_R48_REQUIRED_UNRESOLVED_HOLD_REFS)
    if required - unresolved:
        raise ValueError("R48 R14 must preserve R46 P5/P6/real-device/full-backend HOLD refs")
    for false_key in (
        "r46_handoff_regression_executed_here",
        "actual_r46_handoff_regression_executed_here",
        "p5_human_blind_qa_confirmed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_limited_human_readfeel_confirmed",
        "real_device_modal_review_start_allowed",
        "real_device_modal_review_confirmed",
        "human_review_confirmed",
        "manual_real_device_review_confirmed",
        "actual_human_review_run_here",
        "actual_body_full_packet_generated_here",
        "body_full_writer_created_here",
        "local_reviewer_payload_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R48 R14 must keep {false_key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R48_R14_IMPLEMENTED_STEPS:
        raise ValueError("R48 R14 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R48_R14_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R48 R14 not-yet steps changed")
    if data.get("next_required_step") != P7_R48_R14_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R48 R14 must point to R15 next")
    _assert_r14_r15_not_actualized(data, source="p7_r48_r14_r46_handoff_regression_policy")
    return True


def assert_p7_r48_p5_core_subset_regression_policy_contract(policy: Mapping[str, Any]) -> bool:
    data = safe_mapping(policy)
    _assert_common(data, schema_version=P7_R48_P5_CORE_SUBSET_REGRESSION_SCHEMA_VERSION, source="p7_r48_r15_p5_core_subset_regression_policy")
    if data.get("policy_section") != "R15_p5_core_subset_regression":
        raise ValueError("R48 R15 policy section changed")
    if data.get("p5_core_subset_regression_required") is not True:
        raise ValueError("R48 R15 must require P5 core subset regression")
    if tuple(data.get("p5_core_subset_regression_test_refs") or ()) != P7_R48_P5_CORE_SUBSET_REGRESSION_TEST_REFS:
        raise ValueError("R48 R15 P5 core subset test refs changed")
    if tuple(data.get("p5_product_quality_qa_optional_regression_test_refs") or ()) != P7_R48_P5_PRODUCT_QUALITY_QA_OPTIONAL_REGRESSION_TEST_REFS:
        raise ValueError("R48 R15 optional P5 product-quality test refs changed")
    for true_key in ("p5_existing_boundary_preserved_required",):
        if data.get(true_key) is not True:
            raise ValueError(f"R48 R15 must keep {true_key}=True")
    for false_key in (
        "p5_product_quality_qa_required_here",
        "p5_core_subset_regression_executed_here",
        "actual_p5_core_subset_regression_executed_here",
        "p5_core_subset_green_confirmed_here",
        "p5_core_subset_green_claim_allowed",
        "p5_runtime_changed_here",
        "p5_gate_relaxed_here",
        "api_response_shape_changed_here",
        "db_schema_changed_here",
        "emlis_reply_runtime_changed_here",
        "public_response_top_level_key_added_here",
        "rn_contract_changed_here",
        "actual_human_review_run_here",
        "actual_body_full_packet_generated_here",
        "body_full_writer_created_here",
        "local_reviewer_payload_materialized_here",
        "p5_human_blind_qa_confirmed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_limited_human_readfeel_confirmed",
        "real_device_modal_review_start_allowed",
        "real_device_modal_review_confirmed",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R48 R15 must keep {false_key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R48_R14_R15_IMPLEMENTED_STEPS:
        raise ValueError("R48 R15 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R48_R14_R15_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R48 R15 not-yet steps changed")
    if data.get("next_required_step") != P7_R48_R14_R15_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R48 R15 must point to R16 next")
    _assert_r14_r15_not_actualized(data, source="p7_r48_r15_p5_core_subset_regression_policy")
    return True


def assert_p7_r48_r14_r15_regression_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_common(data, schema_version=P7_R48_R14_R15_REGRESSION_FREEZE_SCHEMA_VERSION, source="p7_r48_r14_r15_regression_freeze")
    if data.get("freeze_kind") != "r14_r15_regression_freeze":
        raise ValueError("R48 R14/R15 freeze kind changed")
    assert_p7_r48_r12_r13_confirmed_gate_leak_guard_freeze_contract(
        safe_mapping(data.get("r12_r13_confirmed_gate_leak_guard_freeze"))
    )
    assert_p7_r48_r46_handoff_regression_policy_contract(safe_mapping(data.get("r46_handoff_regression_policy")))
    assert_p7_r48_p5_core_subset_regression_policy_contract(safe_mapping(data.get("p5_core_subset_regression_policy")))
    for true_key in ("r46_handoff_regression_required", "p5_core_subset_regression_required"):
        if data.get(true_key) is not True:
            raise ValueError(f"R48 R14/R15 freeze must keep {true_key}=True")
    for false_key in (
        "r46_handoff_regression_executed_here",
        "p5_core_subset_regression_executed_here",
        "actual_r46_handoff_regression_executed_here",
        "actual_p5_core_subset_regression_executed_here",
        "p5_core_subset_green_confirmed_here",
        "p5_core_subset_green_claim_allowed",
        "p5_runtime_changed_here",
        "p5_gate_relaxed_here",
        "api_response_shape_changed_here",
        "db_schema_changed_here",
        "emlis_reply_runtime_changed_here",
        "p5_human_blind_qa_confirmed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_limited_human_readfeel_confirmed",
        "real_device_modal_review_start_allowed",
        "real_device_modal_review_confirmed",
        "actual_human_review_run_here",
        "actual_body_full_packet_generated_here",
        "body_full_writer_created_here",
        "local_reviewer_payload_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R48 R14/R15 freeze must keep {false_key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R48_R14_R15_IMPLEMENTED_STEPS:
        raise ValueError("R48 R14/R15 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R48_R14_R15_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R48 R14/R15 not-yet steps changed")
    if data.get("next_required_step") != P7_R48_R14_R15_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R48 R14/R15 must point to R16 next")
    _assert_r14_r15_not_actualized(data, source="p7_r48_r14_r15_regression_freeze")
    return True

def assert_p7_r48_p5_reviewer_packet_local_only_payload_contract(packet: Mapping[str, Any]) -> bool:
    """Validate a local-only reviewer packet payload without exporting it.

    This is intentionally not a builder: R5 fixes the schema/guard only and does
    not materialize any body-full packet here.
    """

    data = safe_mapping(packet)
    required = set(P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_REQUIRED_FIELD_REFS)
    forbidden = set(P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_FORBIDDEN_FIELD_REFS)
    if set(data) != required:
        raise ValueError("R48 local-only reviewer packet payload fields must exactly match the R5 schema")
    if set(data) & forbidden:
        raise ValueError("R48 local-only reviewer packet payload contains forbidden controller or raw fields")
    if data.get("schema_version") != P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION:
        raise ValueError("unexpected R48 local-only reviewer packet payload schema_version")
    for true_key in ("local_only", "must_not_export", "disposal_required"):
        if data.get(true_key) is not True:
            raise ValueError(f"R48 local-only reviewer packet payload must keep {true_key}=True")
    if data.get("packet_kind") != P7_R48_PACKET_KIND or data.get("review_kind") != P7_R48_REVIEW_KIND:
        raise ValueError("R48 local-only reviewer packet payload packet or review kind changed")
    if data.get("review_prompt_version") != P7_R48_REVIEW_PROMPT_VERSION:
        raise ValueError("R48 local-only reviewer packet payload prompt version changed")
    blind_id = clean_identifier(data.get("blind_case_id"), default="", max_length=160)
    if not blind_id:
        raise ValueError("R48 local-only reviewer packet payload requires blind_case_id")
    leak_probe = blind_id.lower()
    for hint in ("case-ref", "case_ref", "family", "tier", "free", "expected", "eligible", "gate", "history-line", "low-information"):
        if hint in leak_probe:
            raise ValueError("R48 local-only reviewer packet blind_case_id must not encode controller facts")
    for string_key in ("review_session_id", "packet_ref_id", "current_input_review_surface", "returned_emlis_surface"):
        value = data.get(string_key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"R48 local-only reviewer packet payload requires non-empty {string_key}")
    bounded_history = data.get("bounded_owned_history_review_surface")
    if bounded_history is not None and (not isinstance(bounded_history, str) or not bounded_history.strip()):
        raise ValueError("R48 local-only reviewer packet bounded history surface must be string or null")
    questions = data.get("review_questions")
    if not isinstance(questions, list) or len(questions) < 6 or not all(isinstance(item, str) and item.strip() for item in questions):
        raise ValueError("R48 local-only reviewer packet requires at least six review questions")
    axis_form = safe_mapping(data.get("axis_rating_form"))
    if axis_form.get("score_min") != 0.0 or axis_form.get("score_max") != 1.0:
        raise ValueError("R48 local-only reviewer packet axis form score range changed")
    if tuple(axis_form.get("required_axes") or ()) != P5_HUMAN_BLIND_QA_RATING_AXES:
        raise ValueError("R48 local-only reviewer packet axis form rating axes changed")
    if axis_form.get("free_text_allowed_local_only") is not True:
        raise ValueError("R48 local-only reviewer packet may allow free text only locally")
    return True


def assert_p7_r48_p5_body_full_packet_materialization_request_contract(
    packet: Mapping[str, Any],
    *,
    body_full_packet_materialization_guard: Mapping[str, Any],
) -> bool:
    """Validate a local-only packet materialization request against the R6 guard.

    The request may contain local-only body surfaces. This validator does not
    write, return, hash, or export the body-full packet.
    """

    guard = safe_mapping(body_full_packet_materialization_guard)
    assert_p7_r48_body_full_packet_materialization_guard_contract(guard)
    if guard.get("body_full_packet_materialization_allowed_by_guard") is not True:
        raise ValueError("R48 R6 guard must allow materialization before a local-only packet request is accepted")
    assert_p7_r48_p5_reviewer_packet_local_only_payload_contract(packet)
    data = safe_mapping(packet)
    for flag_ref in P7_R48_LOCAL_REVIEWER_PACKET_REQUIRED_FLAG_REFS:
        if data.get(flag_ref) is not True:
            raise ValueError(f"R48 R6 local-only packet request must set {flag_ref}=True")
    if set(data) & set(P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_FORBIDDEN_FIELD_REFS):
        raise ValueError("R48 R6 local-only packet request leaked forbidden controller/raw fields")
    return True



def _assert_common(data: Mapping[str, Any], *, schema_version: str, source: str) -> None:
    payload = safe_mapping(data)
    if payload.get("schema_version") != schema_version:
        raise ValueError(f"unexpected {source} schema_version")
    if payload.get("phase") != P7_PHASE or payload.get("step") != P7_R48_STEP:
        raise ValueError(f"unexpected {source} phase or step")
    if payload.get("scope") != P7_R48_SCOPE:
        raise ValueError(f"unexpected {source} scope")
    if payload.get("policy_kind") != P7_R48_POLICY_KIND:
        raise ValueError(f"unexpected {source} policy kind")
    if payload.get("current_phase") != "P7":
        raise ValueError(f"{source} must keep current phase as P7")
    if payload.get("body_free") is not True:
        raise ValueError(f"{source} must be body-free")
    for key in _R48_RELEASE_CLOSED_KEYS:
        if payload.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=False")
    assert_false_markers(safe_mapping(payload.get("public_contract")), source=f"{source}.public_contract")
    assert_false_markers(safe_mapping(payload.get("body_free_markers")), source=f"{source}.body_free_markers")
    _assert_r48_body_free(payload, source=source)


def _assert_r0_r1_not_ready(data: Mapping[str, Any], *, source: str) -> None:
    for key in _R48_R0_R1_FALSE_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=False during R48 R0/R1")


def _assert_r2_r3_not_ready(data: Mapping[str, Any], *, source: str) -> None:
    for key in _R48_R2_R3_FALSE_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=False during R48 R2/R3")


def _assert_r6_r7_not_ready(data: Mapping[str, Any], *, source: str) -> None:
    for key in _R48_R6_R7_FALSE_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=False during R48 R6/R7")


def assert_p7_r48_local_storage_root_policy_contract(policy: Mapping[str, Any]) -> bool:
    data = safe_mapping(policy)
    _assert_common(
        data,
        schema_version=P7_R48_LOCAL_STORAGE_ROOT_POLICY_SCHEMA_VERSION,
        source="p7_r48_r2_local_storage_root_policy",
    )
    if data.get("policy_section") != "R2_local_storage_root_policy":
        raise ValueError("R48 R2 policy section changed")
    if data.get("r0_current_source_r47_handoff_hold_refrozen") is not True:
        raise ValueError("R48 R2 must preserve R0 marker")
    if data.get("r1_scope_schema_packet_kind_fixed") is not True:
        raise ValueError("R48 R2 must preserve R1 marker")
    if data.get("local_storage_root_policy_connected") is not True:
        raise ValueError("R48 R2 must connect the local storage root policy")
    if data.get("storage_mode") != P7_R48_STORAGE_MODE_EXTERNAL_LOCAL_ONLY:
        raise ValueError("R48 R2 storage mode must remain external_local_only")
    if data.get("env_var") != P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR:
        raise ValueError("R48 R2 env var must inherit R47 COCOLON_EMLIS_LOCAL_REVIEW_ROOT")
    if data.get("r47_storage_root_policy_schema_version") != P7_R47_LOCAL_REVIEW_STORAGE_ROOT_POLICY_SCHEMA_VERSION:
        raise ValueError("R48 R2 must reference the R47 storage root policy schema")
    assert_p7_r47_local_review_storage_root_policy_contract(safe_mapping(data.get("r47_storage_root_policy")))
    if data.get("root_path_exposed") is not False or data.get("local_absolute_path_included") is not False:
        raise ValueError("R48 R2 must not expose local absolute paths")
    if "local_review_root_path" in data or "absolute_path" in data or "local_absolute_path" in data:
        raise ValueError("R48 R2 must not include actual local paths")
    for false_key in (
        "repo_local_storage_allowed",
        "artifact_export_path_allowed",
        "docs_tests_services_storage_allowed",
        "premise_storage_allowed",
        "implemented_docs_storage_allowed",
        "mnt_data_artifact_storage_allowed",
        "git_tracked_path_storage_allowed",
        "body_free_case_matrix_ready",
        "actual_case_matrix_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R48 R2 must keep {false_key}=False")
    for true_key in ("body_full_generation_requires_env_root", "body_full_generation_requires_explicit_allow"):
        if data.get(true_key) is not True:
            raise ValueError(f"R48 R2 must keep {true_key}=True")
    status = data.get("local_review_root_status")
    if status not in {"missing", "invalid", "valid"}:
        raise ValueError("R48 R2 local root status changed")
    root_valid = data.get("local_review_root_valid") is True
    explicit_allow = data.get("explicit_body_full_generation_allow") is True
    generation_allowed = data.get("local_body_packet_generation_allowed") is True
    if generation_allowed != (root_valid and explicit_allow):
        raise ValueError("R48 R2 generation allow must require both valid local root and explicit allow")
    reasons = dedupe_identifiers(data.get("generation_block_reason_ids"), limit=20, max_length=160)
    if generation_allowed and reasons:
        raise ValueError("R48 R2 generation-allowed policy must not carry block reasons")
    if not generation_allowed and not reasons:
        raise ValueError("R48 R2 generation-blocked policy must carry block reasons")
    if status == "missing" and "review_packet_generation_blocked_missing_local_root" not in reasons:
        raise ValueError("R48 R2 missing local root must expose a body-free missing-root reason")
    if status == "invalid" and "review_packet_generation_blocked_invalid_local_root" not in reasons:
        raise ValueError("R48 R2 invalid local root must expose a body-free invalid-root reason")
    if status == "valid" and not explicit_allow and P7_R48_EXPLICIT_ALLOW_BLOCK_REASON_REF not in reasons:
        raise ValueError("R48 R2 valid root without explicit allow must remain generation-blocked")
    if data.get("p5_human_blind_qa_start_allowed_after_r47_policy") is not True:
        raise ValueError("R48 R2 must preserve the R47 P5 start-allowed handoff")
    _assert_r2_r3_not_ready(data, source="p7_r48_r2_local_storage_root_policy")
    return True


def _assert_blind_case_id_does_not_leak(row: Mapping[str, Any]) -> None:
    item = safe_mapping(row)
    blind_case_id = clean_identifier(item.get("blind_case_id"), default="", max_length=160).lower()
    family = clean_identifier(item.get("family"), default="", max_length=160).lower()
    tier = clean_identifier(item.get("subscription_tier_ref"), default="", max_length=80).lower()
    leak_hints = [family, tier, "expected", "eligible", "gate", "history_line", "low_information", "free_tier"]
    if any(hint and hint.replace("_", "-") in blind_case_id for hint in leak_hints):
        raise ValueError("R48 R3 blind_case_id must not encode family, tier, expected result, or gate status")


def assert_p7_r48_p5_first_formal_review_case_matrix_contract(matrix: Mapping[str, Any]) -> bool:
    data = safe_mapping(matrix)
    _assert_common(
        data,
        schema_version=P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION,
        source="p7_r48_r3_p5_case_matrix",
    )
    if data.get("matrix_kind") != "p5_24_case_first_formal_review_matrix":
        raise ValueError("R48 R3 matrix kind changed")
    if data.get("packet_kind") != P7_R48_PACKET_KIND or data.get("review_kind") != P7_R48_REVIEW_KIND:
        raise ValueError("R48 R3 packet or review kind changed")
    if data.get("review_prompt_version") != P7_R48_REVIEW_PROMPT_VERSION:
        raise ValueError("R48 R3 review prompt version changed")
    if safe_mapping(data.get("r47_minimums_ref")) != dict(P7_R47_P5_FIRST_FORMAL_MINIMUMS):
        raise ValueError("R48 R3 must inherit R47 P5 first formal minimums")
    if safe_mapping(data.get("r47_history_surface_policy_ref")) != dict(P7_R47_P5_HISTORY_SURFACE_POLICY):
        raise ValueError("R48 R3 must inherit R47 P5 history surface policy")
    rows_raw = data.get("case_rows")
    if not isinstance(rows_raw, list):
        raise ValueError("R48 R3 case_rows must be a list")
    rows = [safe_mapping(row) for row in rows_raw]
    if data.get("case_count") != len(rows):
        raise ValueError("R48 R3 case_count must match case_rows length")
    if not _matrix_minimums_satisfied(rows) or data.get("minimums_satisfied") is not True:
        raise ValueError("R48 R3 case matrix must satisfy first formal review minimums")
    case_refs: set[str] = set()
    blind_refs: set[str] = set()
    packet_refs: set[str] = set()
    for row in rows:
        extra_keys = set(row) - set(P7_R48_P5_CASE_MATRIX_ROW_FIELD_REFS)
        missing_keys = set(P7_R48_P5_CASE_MATRIX_ROW_FIELD_REFS) - set(row)
        if extra_keys or missing_keys:
            raise ValueError("R48 R3 case row fields changed")
        if row.get("body_free") is not True:
            raise ValueError("R48 R3 case rows must be body-free")
        if row.get("controller_only") is not True:
            raise ValueError("R48 R3 case rows must stay controller-only")
        for false_key in (
            "reviewer_facing_family_exposed",
            "reviewer_facing_tier_exposed",
            "body_full_packet_materialized_here",
            "local_reviewer_payload_materialized_here",
        ):
            if row.get(false_key) is not False:
                raise ValueError(f"R48 R3 case row must keep {false_key}=False")
        family = clean_identifier(row.get("family"), default="", max_length=160)
        role = clean_identifier(row.get("case_role"), default="", max_length=80)
        tier = clean_identifier(row.get("subscription_tier_ref"), default="", max_length=80)
        if family not in P5_HUMAN_BLIND_QA_FAMILIES:
            raise ValueError("R48 R3 case row family changed")
        if role not in P7_R48_P5_CASE_ROLE_REFS:
            raise ValueError("R48 R3 case row role changed")
        if tier not in P7_R48_P5_TIER_REF_REFS:
            raise ValueError("R48 R3 tier ref changed")
        if family == "free_tier_history_present_not_allowed" and tier != "free":
            raise ValueError("R48 R3 free-tier boundary rows must keep free tier ref")
        if family != "free_tier_history_present_not_allowed" and tier == "free":
            raise ValueError("R48 R3 positive/low-info rows must not use free tier ref")
        if family in P7_R48_P5_BOUNDARY_FAMILY_REFS and role != "boundary_no_history_line":
            raise ValueError("R48 R3 boundary families must use boundary role")
        if family not in P7_R48_P5_BOUNDARY_FAMILY_REFS and role == "boundary_no_history_line":
            raise ValueError("R48 R3 positive families must not use boundary role")
        _assert_blind_case_id_does_not_leak(row)
        for ref_key, target_set in (
            ("case_ref_id", case_refs),
            ("blind_case_id", blind_refs),
            ("packet_ref_id", packet_refs),
        ):
            ref = clean_identifier(row.get(ref_key), default="", max_length=160)
            if not ref or ref in target_set:
                raise ValueError(f"R48 R3 {ref_key} must be unique and non-empty")
            target_set.add(ref)
    if data.get("owned_history_positive_case_count") < P7_R47_P5_FIRST_FORMAL_MINIMUMS["minimum_owned_history_positive_cases"]:
        raise ValueError("R48 R3 owned history positive count below minimum")
    policy = safe_mapping(data.get("blind_case_id_policy"))
    if policy.get("family_tier_expected_gate_not_encoded") is not True:
        raise ValueError("R48 R3 blind id policy must not encode family/tier/expected/gate")
    if policy.get("derived_from_record_or_body_hash") is not False:
        raise ValueError("R48 R3 blind ids must not derive from body or record hashes")
    if data.get("reviewer_facing_family_exposed") is not False or data.get("reviewer_facing_tier_exposed") is not False:
        raise ValueError("R48 R3 matrix must not expose family/tier to reviewer-facing packet")
    for false_key in (
        "body_full_packet_materialized_here",
        "local_reviewer_payload_materialized_here",
        "actual_body_full_packet_generated_here",
        "body_full_writer_created_here",
        "actual_human_review_run_here",
        "actual_rating_rows_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "p5_human_blind_qa_actual_review_start_allowed_after_r2_r3",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R48 R3 must keep {false_key}=False")
    if data.get("body_free_case_matrix_ready") is not True or data.get("actual_case_matrix_materialized_here") is not True:
        raise ValueError("R48 R3 must mark only the body-free case matrix as ready")
    if data.get("p5_human_blind_qa_start_allowed_after_r47_policy") is not True:
        raise ValueError("R48 R3 must preserve the R47 P5 start-allowed handoff")
    return True


def assert_p7_r48_r2_r3_local_storage_case_matrix_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_common(
        data,
        schema_version=P7_R48_R2_R3_LOCAL_STORAGE_CASE_MATRIX_FREEZE_SCHEMA_VERSION,
        source="p7_r48_r2_r3_local_storage_case_matrix_freeze",
    )
    if data.get("freeze_kind") != "r2_r3_local_storage_case_matrix_freeze":
        raise ValueError("R48 R2/R3 freeze kind changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R48_R2_R3_IMPLEMENTED_STEPS:
        raise ValueError("R48 R2/R3 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R48_R2_R3_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R48 R2/R3 not-yet-implemented steps changed")
    assert_p7_r48_r0_r1_scope_freeze_contract(safe_mapping(data.get("r0_r1_scope_freeze")))
    assert_p7_r48_local_storage_root_policy_contract(safe_mapping(data.get("local_storage_policy")))
    assert_p7_r48_p5_first_formal_review_case_matrix_contract(safe_mapping(data.get("p5_case_matrix")))
    if data.get("next_required_step") != P7_R48_R2_R3_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R48 R2/R3 must point to R4 next")
    if data.get("packet_kind") != P7_R48_PACKET_KIND or data.get("review_kind") != P7_R48_REVIEW_KIND:
        raise ValueError("R48 R2/R3 packet or review kind changed")
    for true_key in (
        "r0_current_source_r47_handoff_hold_refrozen",
        "r1_scope_schema_packet_kind_fixed",
        "local_storage_root_policy_connected",
        "p5_24_case_first_formal_review_matrix_built",
        "body_free_case_matrix_ready",
        "actual_case_matrix_materialized_here",
        "minimums_satisfied",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R48 R2/R3 must keep {true_key}=True")
    if data.get("case_count") != 24:
        raise ValueError("R48 R2/R3 first formal matrix must contain exactly 24 cases")
    if data.get("p5_human_blind_qa_start_allowed_after_r47_policy") is not True:
        raise ValueError("R48 R2/R3 must preserve the R47 P5 start-allowed handoff")
    _assert_r2_r3_not_ready(data, source="p7_r48_r2_r3_local_storage_case_matrix_freeze")
    return True



def _assert_r4_r5_not_ready(data: Mapping[str, Any], *, source: str) -> None:
    for key in _R48_R4_R5_FALSE_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=False during R48 R4/R5")


def assert_p7_r48_blind_case_id_case_ref_separation_contract(separation: Mapping[str, Any]) -> bool:
    data = safe_mapping(separation)
    _assert_common(
        data,
        schema_version=P7_R48_BLIND_CASE_ID_CASE_REF_SEPARATION_SCHEMA_VERSION,
        source="p7_r48_r4_blind_case_id_case_ref_separation",
    )
    if data.get("separation_kind") != "blind_case_id_case_ref_separation":
        raise ValueError("R48 R4 separation kind changed")
    if data.get("packet_kind") != P7_R48_PACKET_KIND or data.get("review_kind") != P7_R48_REVIEW_KIND:
        raise ValueError("R48 R4 packet or review kind changed")
    if data.get("case_ref_to_blind_case_ref_separated") is not True:
        raise ValueError("R48 R4 must separate case_ref_id from blind_case_id")
    for true_key in (
        "controller_manifest_keeps_case_ref_family_tier",
        "reviewer_facing_uses_blind_case_id_only",
        "blind_case_id_family_tier_expected_gate_not_encoded",
        "body_free_case_matrix_ready",
        "actual_case_matrix_materialized_here",
        "blind_case_id_case_ref_separated",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R48 R4 must keep {true_key}=True")
    for false_key in (
        "reviewer_facing_case_ref_id_allowed",
        "reviewer_facing_family_allowed",
        "reviewer_facing_subscription_tier_allowed",
        "reviewer_facing_expected_result_allowed",
        "reviewer_facing_gate_result_allowed",
        "blind_case_id_derived_from_body_or_record_hash",
        "blind_case_id_derived_from_record_id_hash",
        "body_full_packet_materialized_here",
        "local_reviewer_payload_materialized_here",
        "actual_body_full_packet_generated_here",
        "body_full_writer_created_here",
        "actual_human_review_run_here",
        "actual_rating_rows_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "reviewer_facing_local_packet_schema_fixed",
        "p5_human_blind_qa_actual_review_start_allowed_after_r4_r5",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R48 R4 must keep {false_key}=False")
    if data.get("reviewer_facing_identifier_policy") != "blind_case_id_only":
        raise ValueError("R48 R4 reviewer-facing identifier policy changed")
    controller_rows_raw = data.get("controller_manifest_rows")
    reviewer_rows_raw = data.get("reviewer_facing_case_index_rows")
    if not isinstance(controller_rows_raw, list) or not isinstance(reviewer_rows_raw, list):
        raise ValueError("R48 R4 rows must be lists")
    controller_rows = [safe_mapping(row) for row in controller_rows_raw]
    reviewer_rows = [safe_mapping(row) for row in reviewer_rows_raw]
    if data.get("case_count") != len(controller_rows) or len(controller_rows) != len(reviewer_rows):
        raise ValueError("R48 R4 row counts must match case_count")
    if data.get("case_ref_count") != len({row.get("case_ref_id") for row in controller_rows}):
        raise ValueError("R48 R4 case_ref count mismatch")
    if data.get("blind_case_id_count") != len({row.get("blind_case_id") for row in controller_rows}):
        raise ValueError("R48 R4 blind_case_id count mismatch")
    controller_blind_ids: set[str] = set()
    for row in controller_rows:
        if set(row) != set(P7_R48_CONTROLLER_MANIFEST_ROW_FIELD_REFS):
            raise ValueError("R48 R4 controller manifest row fields changed")
        if row.get("body_free") is not True or row.get("controller_only") is not True:
            raise ValueError("R48 R4 controller rows must be body-free controller-only")
        for true_key in ("reviewer_receives_blind_case_id",):
            if row.get(true_key) is not True:
                raise ValueError(f"R48 R4 controller row must keep {true_key}=True")
        for false_key in (
            "reviewer_receives_case_ref_id",
            "reviewer_receives_family",
            "reviewer_receives_subscription_tier",
            "reviewer_receives_expected_result",
            "reviewer_receives_gate_result",
            "blind_case_id_derived_from_body_or_record_hash",
        ):
            if row.get(false_key) is not False:
                raise ValueError(f"R48 R4 controller row must keep {false_key}=False")
        _assert_blind_case_id_does_not_leak(row)
        controller_blind_ids.add(clean_identifier(row.get("blind_case_id"), default="", max_length=160))
    reviewer_blind_ids: set[str] = set()
    for row in reviewer_rows:
        if set(row) != set(P7_R48_REVIEWER_FACING_CASE_INDEX_ROW_FIELD_REFS):
            raise ValueError("R48 R4 reviewer-facing case index row fields changed")
        if row.get("body_free") is not True:
            raise ValueError("R48 R4 reviewer-facing case index rows must be body-free")
        for key in ("case_ref_id", "family", "subscription_tier_ref", "expected_result", "gate_result"):
            if key in row:
                raise ValueError("R48 R4 reviewer-facing case index row leaked controller fields")
        for true_key in ("case_ref_hidden", "family_hidden", "tier_hidden", "expected_result_hidden", "gate_result_hidden"):
            if row.get(true_key) is not True:
                raise ValueError(f"R48 R4 reviewer row must keep {true_key}=True")
        if row.get("derived_from_body_or_record_hash") is not False:
            raise ValueError("R48 R4 reviewer row blind id must not derive from hashes")
        blind = clean_identifier(row.get("blind_case_id"), default="", max_length=160)
        if not blind:
            raise ValueError("R48 R4 reviewer row blind id missing")
        reviewer_blind_ids.add(blind)
    if reviewer_blind_ids != controller_blind_ids:
        raise ValueError("R48 R4 reviewer blind ids must exactly match controller blind ids")
    if data.get("next_required_step") != P7_R48_R4_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R48 R4 must point to R5 next")
    _assert_r4_r5_not_ready(data, source="p7_r48_r4_blind_case_id_case_ref_separation")
    return True


def assert_p7_r48_p5_reviewer_facing_local_packet_schema_freeze_contract(schema: Mapping[str, Any]) -> bool:
    data = safe_mapping(schema)
    _assert_common(
        data,
        schema_version=P7_R48_REVIEWER_FACING_LOCAL_PACKET_SCHEMA_FREEZE_SCHEMA_VERSION,
        source="p7_r48_r5_reviewer_facing_local_packet_schema_freeze",
    )
    if data.get("schema_freeze_kind") != "p5_reviewer_facing_local_packet_schema_freeze":
        raise ValueError("R48 R5 schema freeze kind changed")
    if data.get("packet_schema_version") != P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION:
        raise ValueError("R48 R5 local-only packet schema version changed")
    if data.get("packet_kind") != P7_R48_PACKET_KIND or data.get("review_kind") != P7_R48_REVIEW_KIND:
        raise ValueError("R48 R5 packet or review kind changed")
    if data.get("review_prompt_version") != P7_R48_REVIEW_PROMPT_VERSION:
        raise ValueError("R48 R5 review prompt version changed")
    if data.get("reviewer_facing_identifier_policy") != "blind_case_id_only":
        raise ValueError("R48 R5 reviewer identifier policy changed")
    if tuple(data.get("reviewer_visible_field_refs") or ()) != P7_R48_P5_REVIEWER_PACKET_REVIEWER_VISIBLE_FIELD_REFS:
        raise ValueError("R48 R5 reviewer visible fields changed")
    if tuple(data.get("local_only_control_field_refs") or ()) != P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_CONTROL_FIELD_REFS:
        raise ValueError("R48 R5 local-only control fields changed")
    if tuple(data.get("required_field_refs") or ()) != P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_REQUIRED_FIELD_REFS:
        raise ValueError("R48 R5 required fields changed")
    if tuple(data.get("allowed_payload_field_refs") or ()) != P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_REQUIRED_FIELD_REFS:
        raise ValueError("R48 R5 allowed payload fields changed")
    forbidden = set(dedupe_identifiers(data.get("forbidden_payload_field_refs"), limit=160, max_length=160))
    if set(P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_FORBIDDEN_FIELD_REFS) - forbidden:
        raise ValueError("R48 R5 forbidden payload field coverage changed")
    if set(data.get("allowed_payload_field_refs") or ()) & forbidden:
        raise ValueError("R48 R5 allowed and forbidden payload fields overlap")
    if tuple(data.get("local_only_body_field_refs") or ()) != P7_R48_P5_REVIEWER_PACKET_BODY_FIELD_REFS:
        raise ValueError("R48 R5 local-only body field refs changed")
    if tuple(data.get("review_question_refs") or ()) != P7_R48_P5_REVIEW_QUESTION_REFS:
        raise ValueError("R48 R5 review question refs changed")
    fields = [safe_mapping(item) for item in data.get("field_contracts") or []]
    if [item.get("field_ref") for item in fields] != list(P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_REQUIRED_FIELD_REFS):
        raise ValueError("R48 R5 field contract order changed")
    for item in fields:
        if item.get("required") is not True or item.get("local_only") is not True:
            raise ValueError("R48 R5 field contracts must be required local-only refs")
        if item.get("body_free_material_allowed") is not False or item.get("body_free") is not True:
            raise ValueError("R48 R5 field contracts must stay schema-only/body-free")
    axis_contract = safe_mapping(data.get("axis_rating_form_contract"))
    if axis_contract.get("score_min") != 0.0 or axis_contract.get("score_max") != 1.0:
        raise ValueError("R48 R5 axis rating score bounds changed")
    if tuple(axis_contract.get("required_axis_refs") or ()) != P5_HUMAN_BLIND_QA_RATING_AXES:
        raise ValueError("R48 R5 axis rating refs changed")
    if axis_contract.get("free_text_allowed_local_only") is not True:
        raise ValueError("R48 R5 free text must be local-only when allowed")
    if axis_contract.get("free_text_bodyfree_allowed") is not False:
        raise ValueError("R48 R5 free text must not be body-free")
    for true_key in (
        "local_only_required",
        "must_not_export_required",
        "disposal_required_required",
        "blind_case_id_case_ref_separated",
        "reviewer_facing_local_packet_schema_fixed",
        "body_free_case_matrix_ready",
        "actual_case_matrix_materialized_here",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R48 R5 must keep {true_key}=True")
    for false_key in (
        "additional_properties_allowed",
        "family_visible_to_reviewer_allowed",
        "subscription_tier_visible_to_reviewer_allowed",
        "expected_result_visible_to_reviewer_allowed",
        "gate_result_visible_to_reviewer_allowed",
        "case_ref_visible_to_reviewer_allowed",
        "public_meta_in_reviewer_payload_allowed",
        "raw_input_in_reviewer_payload_allowed",
        "comment_text_in_reviewer_payload_allowed",
        "candidate_body_in_reviewer_payload_allowed",
        "surface_body_in_reviewer_payload_allowed",
        "controller_expected_boundary_in_reviewer_payload_allowed",
        "reviewer_free_text_in_packet_payload_allowed",
        "body_free_material_can_include_local_packet_payload",
        "json_schema_file_created_here",
        "body_full_packet_materialized_here",
        "local_reviewer_payload_materialized_here",
        "actual_body_full_packet_generated_here",
        "body_full_writer_created_here",
        "actual_human_review_run_here",
        "actual_rating_rows_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "p5_human_blind_qa_actual_review_start_allowed_after_r4_r5",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R48 R5 must keep {false_key}=False")
    if data.get("next_required_step") != P7_R48_R4_R5_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R48 R5 must point to R6 next")
    _assert_r4_r5_not_ready(data, source="p7_r48_r5_reviewer_facing_local_packet_schema_freeze")
    return True


def assert_p7_r48_r4_r5_reviewer_packet_schema_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_common(
        data,
        schema_version=P7_R48_R4_R5_REVIEWER_PACKET_SCHEMA_FREEZE_SCHEMA_VERSION,
        source="p7_r48_r4_r5_reviewer_packet_schema_freeze",
    )
    if data.get("freeze_kind") != "r4_r5_reviewer_packet_schema_freeze":
        raise ValueError("R48 R4/R5 combined freeze kind changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R48_R4_R5_IMPLEMENTED_STEPS:
        raise ValueError("R48 R4/R5 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R48_R4_R5_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R48 R4/R5 not-yet-implemented steps changed")
    assert_p7_r48_r2_r3_local_storage_case_matrix_freeze_contract(safe_mapping(data.get("r2_r3_local_storage_case_matrix_freeze")))
    assert_p7_r48_blind_case_id_case_ref_separation_contract(safe_mapping(data.get("blind_case_id_case_ref_separation")))
    assert_p7_r48_p5_reviewer_facing_local_packet_schema_freeze_contract(
        safe_mapping(data.get("reviewer_facing_local_packet_schema_freeze"))
    )
    if data.get("next_required_step") != P7_R48_R4_R5_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R48 R4/R5 must point to R6 next")
    if data.get("packet_kind") != P7_R48_PACKET_KIND or data.get("review_kind") != P7_R48_REVIEW_KIND:
        raise ValueError("R48 R4/R5 packet or review kind changed")
    for true_key in (
        "r0_current_source_r47_handoff_hold_refrozen",
        "r1_scope_schema_packet_kind_fixed",
        "local_storage_root_policy_connected",
        "p5_24_case_first_formal_review_matrix_built",
        "blind_case_id_case_ref_separated",
        "reviewer_facing_local_packet_schema_fixed",
        "body_free_case_matrix_ready",
        "actual_case_matrix_materialized_here",
        "minimums_satisfied",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R48 R4/R5 must keep {true_key}=True")
    if data.get("case_count") != 24:
        raise ValueError("R48 R4/R5 first formal matrix must contain exactly 24 cases")
    for false_key in (
        "body_full_packet_materialized_here",
        "local_reviewer_payload_materialized_here",
        "actual_body_full_packet_generated_here",
        "body_full_writer_created_here",
        "actual_human_review_run_here",
        "actual_rating_rows_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "p5_human_blind_qa_actual_review_start_allowed_after_r4_r5",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R48 R4/R5 must keep {false_key}=False")
    if data.get("p5_human_blind_qa_start_allowed_after_r47_policy") is not True:
        raise ValueError("R48 R4/R5 must preserve the R47 P5 start-allowed handoff")
    _assert_r4_r5_not_ready(data, source="p7_r48_r4_r5_reviewer_packet_schema_freeze")
    return True


def assert_p7_r48_body_full_packet_materialization_guard_contract(guard: Mapping[str, Any]) -> bool:
    data = safe_mapping(guard)
    _assert_common(
        data,
        schema_version=P7_R48_BODY_FULL_PACKET_MATERIALIZATION_GUARD_SCHEMA_VERSION,
        source="p7_r48_r6_body_full_packet_materialization_guard",
    )
    if data.get("policy_section") != "R6_body_full_packet_materialization_guard":
        raise ValueError("R48 R6 materialization guard section changed")
    assert_p7_r48_r4_r5_reviewer_packet_schema_freeze_contract(
        safe_mapping(data.get("r4_r5_reviewer_packet_schema_freeze"))
    )
    storage = _local_storage_policy_from_r4_r5_freeze(safe_mapping(data.get("r4_r5_reviewer_packet_schema_freeze")))
    root_valid = data.get("local_review_root_valid") is True
    explicit_allow = data.get("explicit_body_full_generation_allow") is True
    allowed = data.get("body_full_packet_materialization_allowed_by_guard") is True
    if root_valid != (storage.get("local_review_root_valid") is True):
        raise ValueError("R48 R6 local root validity drifted from R2 policy")
    if explicit_allow != (storage.get("explicit_body_full_generation_allow") is True):
        raise ValueError("R48 R6 explicit allow drifted from R2 policy")
    if allowed != (root_valid and explicit_allow and storage.get("local_body_packet_generation_allowed") is True):
        raise ValueError("R48 R6 materialization permission must require valid root, R2 allow, and explicit allow")
    if data.get("body_full_packet_materialization_permission_allowed") is not allowed:
        raise ValueError("R48 R6 permission aliases must match")
    reasons = dedupe_identifiers(data.get("body_full_packet_materialization_block_reason_ids"), limit=20, max_length=160)
    if allowed and reasons:
        raise ValueError("R48 R6 allowed guard must not carry block reasons")
    if not allowed and not reasons:
        raise ValueError("R48 R6 blocked guard must carry body-free block reasons")
    if set(reasons) - set(P7_R48_BODY_FULL_PACKET_MATERIALIZATION_BLOCK_REASON_REFS):
        raise ValueError("R48 R6 materialization guard emitted unknown block reasons")
    if data.get("root_path_exposed") is not False or data.get("local_absolute_path_included") is not False:
        raise ValueError("R48 R6 must not expose local absolute paths")
    if data.get("local_packet_output_ref_is_abstract") is not True:
        raise ValueError("R48 R6 local packet output ref must remain abstract")
    for true_key in (
        "body_full_generation_requires_env_root",
        "body_full_generation_requires_explicit_allow",
        "body_full_packet_materialization_guard_ready",
        "generated_local_packet_must_set_local_only",
        "generated_local_packet_must_set_must_not_export",
        "generated_local_packet_must_set_disposal_required",
        "dry_run_body_free_default",
        "body_free_case_matrix_ready",
        "actual_case_matrix_materialized_here",
        "blind_case_id_case_ref_separated",
        "reviewer_facing_local_packet_schema_fixed",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R48 R6 must keep {true_key}=True")
    for false_key in (
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
        "p5_human_blind_qa_actual_review_start_allowed_after_r6_r7",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R48 R6 must keep {false_key}=False")
    if tuple(data.get("generated_local_packet_required_flag_refs") or ()) != P7_R48_LOCAL_REVIEWER_PACKET_REQUIRED_FLAG_REFS:
        raise ValueError("R48 R6 required local-only packet flags changed")
    if data.get("generated_local_packet_schema_version") != P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION:
        raise ValueError("R48 R6 local packet schema version changed")
    if tuple(data.get("generated_local_packet_allowed_field_refs") or ()) != P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_REQUIRED_FIELD_REFS:
        raise ValueError("R48 R6 allowed local packet field refs changed")
    forbidden = set(dedupe_identifiers(data.get("generated_local_packet_forbidden_field_refs"), limit=200, max_length=160))
    if set(P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_FORBIDDEN_FIELD_REFS) - forbidden:
        raise ValueError("R48 R6 local packet forbidden field coverage changed")
    if tuple(data.get("implemented_steps") or ()) != (*P7_R48_R4_R5_IMPLEMENTED_STEPS, "R6_body_full_packet_materialization_guard"):
        raise ValueError("R48 R6 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != ("R7_local_reviewer_notes_policy", *P7_R48_R6_R7_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("R48 R6 not-yet-implemented steps changed")
    if data.get("next_required_step") != P7_R48_R6_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R48 R6 must point to R7 next")
    if data.get("p5_human_blind_qa_start_allowed_after_r47_policy") is not True:
        raise ValueError("R48 R6 must preserve the R47 P5 start-allowed handoff")
    _assert_r6_r7_not_ready(data, source="p7_r48_r6_body_full_packet_materialization_guard")
    return True


def assert_p7_r48_local_reviewer_notes_policy_contract(policy: Mapping[str, Any]) -> bool:
    data = safe_mapping(policy)
    _assert_common(
        data,
        schema_version=P7_R48_LOCAL_REVIEWER_NOTES_POLICY_SCHEMA_VERSION,
        source="p7_r48_r7_local_reviewer_notes_policy",
    )
    if data.get("policy_section") != "R7_local_reviewer_notes_policy":
        raise ValueError("R48 R7 reviewer notes policy section changed")
    if data.get("r47_reviewer_notes_policy_schema_version_ref") != P7_R47_REVIEWER_NOTES_LOCAL_ONLY_POLICY_SCHEMA_VERSION:
        raise ValueError("R48 R7 must retain the R47 reviewer-notes policy schema reference")
    for true_key in (
        "local_only_notes_policy_fixed",
        "reviewer_free_text_policy_fixed",
        "body_free_rating_row_reviewer_free_text_included_required_false",
        "body_free_blocker_row_reviewer_free_text_included_required_false",
        "rating_rows_body_free_only",
        "blocker_rows_body_free_only",
        "sanitized_reason_id_required_for_p7_material",
        "sanitized_reason_ids_only",
        "reason_id_other_local_note_purged",
        "notes_purge_required_after_rating_finalized",
        "body_free_result_can_retain_sanitized_reason_ids",
        "body_free_result_can_retain_blocker_ids",
        "body_free_result_can_retain_numeric_ratings_later",
        "body_free_result_can_retain_disposal_receipt_ref_later",
        "body_full_packet_materialization_guard_ready",
        "local_reviewer_notes_policy_fixed",
        "reviewer_notes_local_only_policy_fixed",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R48 R7 notes policy must keep {true_key}=True")
    for false_key in (
        "local_notes_schema_file_created_here",
        "local_notes_standard_export_allowed",
        "local_notes_release_material_allowed",
        "local_notes_p7_scorecard_material_allowed",
        "local_notes_handoff_ledger_material_allowed",
        "local_notes_public_meta_material_allowed",
        "direct_note_copy_to_p7_allowed",
        "raw_quote_to_reason_id_allowed",
        "reviewer_free_text_included",
        "reviewer_free_text_material_allowed",
        "reviewer_free_text_bodyfree_allowed",
        "local_reviewer_payload_materialized_here",
        "actual_notes_materialized_here",
        "actual_reviewer_notes_materialized_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_body_full_packet_generated_here",
        "body_full_writer_created_here",
        "actual_human_review_run_here",
        "actual_disposal_run_here",
        "actual_disposal_receipt_materialized_here",
        "json_schema_file_created_here",
        "p5_human_blind_qa_actual_review_start_allowed_after_r6_r7",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R48 R7 notes policy must keep {false_key}=False")
    if data.get("local_notes_dir_ref") != "reviewer_notes.local_only":
        raise ValueError("R48 R7 local notes dir ref changed")
    if data.get("notes_retention_after_rating_finalized_max_hours") != P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS:
        raise ValueError("R48 R7 notes retention changed")
    if data.get("body_full_packet_retention_max_hours") != P7_R47_BODY_FULL_PACKET_RETENTION_HOURS:
        raise ValueError("R48 R7 body-full retention reference changed")
    if data.get("default_unmapped_reason_id") != "reason_id_other_local_note_purged":
        raise ValueError("R48 R7 default unmapped reason id changed")
    reason_ids = set(dedupe_identifiers(data.get("sanitized_reason_id_refs"), limit=240, max_length=160))
    if set(P7_R48_SANITIZED_REASON_ID_REFS) - reason_ids:
        raise ValueError("R48 R7 sanitized reason ids lost coverage")
    blocker_ids = set(dedupe_identifiers(data.get("execution_blocker_id_refs"), limit=160, max_length=160))
    if set(P7_R48_EXECUTION_BLOCKER_ID_REFS) - blocker_ids:
        raise ValueError("R48 R7 execution blocker ids lost coverage")
    if tuple(data.get("implemented_steps") or ()) != P7_R48_R6_R7_IMPLEMENTED_STEPS:
        raise ValueError("R48 R7 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R48_R6_R7_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R48 R7 not-yet-implemented steps changed")
    if data.get("next_required_step") != P7_R48_R6_R7_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R48 R7 must point to R8 next")
    if data.get("p5_human_blind_qa_start_allowed_after_r47_policy") is not True:
        raise ValueError("R48 R7 must preserve the R47 P5 start-allowed handoff")
    _assert_r6_r7_not_ready(data, source="p7_r48_r7_local_reviewer_notes_policy")
    return True


def assert_p7_r48_r6_r7_materialization_notes_policy_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_common(
        data,
        schema_version=P7_R48_R6_R7_MATERIALIZATION_NOTES_POLICY_FREEZE_SCHEMA_VERSION,
        source="p7_r48_r6_r7_materialization_notes_policy_freeze",
    )
    if data.get("freeze_kind") != "r6_r7_materialization_notes_policy_freeze":
        raise ValueError("R48 R6/R7 combined freeze kind changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R48_R6_R7_IMPLEMENTED_STEPS:
        raise ValueError("R48 R6/R7 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R48_R6_R7_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R48 R6/R7 not-yet-implemented steps changed")
    assert_p7_r48_r4_r5_reviewer_packet_schema_freeze_contract(
        safe_mapping(data.get("r4_r5_reviewer_packet_schema_freeze"))
    )
    assert_p7_r48_body_full_packet_materialization_guard_contract(
        safe_mapping(data.get("body_full_packet_materialization_guard"))
    )
    assert_p7_r48_local_reviewer_notes_policy_contract(safe_mapping(data.get("local_reviewer_notes_policy")))
    if data.get("next_required_step") != P7_R48_R6_R7_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R48 R6/R7 must point to R8 next")
    if data.get("packet_kind") != P7_R48_PACKET_KIND or data.get("review_kind") != P7_R48_REVIEW_KIND:
        raise ValueError("R48 R6/R7 packet or review kind changed")
    for true_key in (
        "r0_current_source_r47_handoff_hold_refrozen",
        "r1_scope_schema_packet_kind_fixed",
        "local_storage_root_policy_connected",
        "p5_24_case_first_formal_review_matrix_built",
        "blind_case_id_case_ref_separated",
        "reviewer_facing_local_packet_schema_fixed",
        "body_full_packet_materialization_guard_ready",
        "local_reviewer_notes_policy_fixed",
        "reviewer_notes_local_only_policy_fixed",
        "body_free_case_matrix_ready",
        "actual_case_matrix_materialized_here",
        "minimums_satisfied",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R48 R6/R7 must keep {true_key}=True")
    if data.get("case_count") != 24:
        raise ValueError("R48 R6/R7 first formal matrix must contain exactly 24 cases")
    for false_key in (
        "body_full_packet_materialized_here",
        "local_reviewer_payload_materialized_here",
        "actual_body_full_packet_generated_here",
        "body_full_writer_created_here",
        "actual_human_review_run_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_reviewer_notes_materialized_here",
        "actual_notes_materialized_here",
        "actual_disposal_run_here",
        "actual_disposal_receipt_materialized_here",
        "p5_human_blind_qa_actual_review_start_allowed_after_r6_r7",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R48 R6/R7 must keep {false_key}=False")
    if data.get("p5_human_blind_qa_start_allowed_after_r47_policy") is not True:
        raise ValueError("R48 R6/R7 must preserve the R47 P5 start-allowed handoff")
    _assert_r6_r7_not_ready(data, source="p7_r48_r6_r7_materialization_notes_policy_freeze")
    return True



def assert_p7_r48_current_source_r47_handoff_hold_refreeze_contract(refreeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(refreeze)
    _assert_common(
        data,
        schema_version=P7_R48_CURRENT_SOURCE_R47_HANDOFF_HOLD_REFREEZE_SCHEMA_VERSION,
        source="p7_r48_r0_refreeze",
    )
    if data.get("freeze_kind") != "current_source_r47_handoff_hold_refreeze":
        raise ValueError("R48 R0 freeze kind changed")
    if data.get("source_mode") != P7_SOURCE_MODE:
        raise ValueError("R48 R0 must remain local snapshot source mode")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError("R48 R0 must not require or claim Git checking")
    r47 = safe_mapping(data.get("r47_handoff"))
    for true_key in (
        "r47_policy_ready",
        "local_review_packet_policy_ready",
        "policy_ready",
        "p5_human_blind_qa_start_allowed_after_r47_policy",
    ):
        if r47.get(true_key) is not True:
            raise ValueError(f"R48 R0 must preserve R47 {true_key}=True")
    for false_key in (
        "p5_human_blind_qa_confirmed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_limited_human_readfeel_confirmed",
        "real_device_modal_review_start_allowed",
        "real_device_modal_review_confirmed",
        "release_allowed",
        "p7_complete",
        "p8_start_allowed",
        "hold004_close_allowed",
    ):
        if r47.get(false_key) is not False:
            raise ValueError(f"R48 R0 must keep R47 handoff {false_key}=False")
    hold = safe_mapping(data.get("hold_state"))
    unresolved = set(dedupe_identifiers(hold.get("unresolved_hold_refs"), limit=120, max_length=120))
    if set(P7_R48_REQUIRED_UNRESOLVED_HOLD_REFS) - unresolved:
        raise ValueError("R48 R0 must preserve unresolved P5/P6/real-device/full-backend HOLD refs")
    for key in (
        "p5_human_blind_qa_confirmed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_limited_human_readfeel_confirmed",
        "real_device_modal_review_start_allowed",
        "real_device_modal_review_confirmed",
        "full_backend_suite_green_confirmed",
        "body_full_review_packet_generated",
        "body_free_case_matrix_ready",
        "body_free_rating_rows_ready",
        "disposal_receipt_verified",
        "body_removed_verified",
    ):
        if hold.get(key) is not False:
            raise ValueError(f"R48 R0 hold state must keep {key}=False")
    if data.get("r0_current_source_r47_handoff_hold_refrozen") is not True:
        raise ValueError("R48 R0 marker must be true")
    if data.get("r1_scope_schema_packet_kind_fixed") is not False:
        raise ValueError("R48 R0 must not mark R1 fixed")
    if data.get("p5_human_blind_qa_start_allowed_after_r47_policy") is not True:
        raise ValueError("R48 R0 must carry the R47 P5 start-allowed handoff")
    _assert_r0_r1_not_ready(data, source="p7_r48_r0_refreeze")
    return True


def assert_p7_r48_scope_schema_packet_kind_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_common(
        data,
        schema_version=P7_R48_SCOPE_SCHEMA_PACKET_KIND_FREEZE_SCHEMA_VERSION,
        source="p7_r48_r1_scope_freeze",
    )
    if data.get("freeze_kind") != "scope_schema_version_packet_kind_freeze":
        raise ValueError("R48 R1 freeze kind changed")
    if data.get("r0_schema_version") != P7_R48_CURRENT_SOURCE_R47_HANDOFF_HOLD_REFREEZE_SCHEMA_VERSION:
        raise ValueError("R48 R1 must reference the R0 schema")
    if data.get("r48_policy_schema_version") != P7_R48_P5_REVIEW_POLICY_SCHEMA_VERSION:
        raise ValueError("R48 R1 policy schema version changed")
    expected_versions = {
        "case_matrix_schema_version": P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION,
        "reviewer_packet_local_only_schema_version": P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION,
        "rating_row_bodyfree_schema_version": P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION,
        "execution_blocker_row_bodyfree_schema_version": P7_R48_P5_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "disposal_receipt_bodyfree_schema_version": P7_R48_P5_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION,
        "review_handoff_summary_bodyfree_schema_version": P7_R48_P5_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION,
    }
    for key, expected in expected_versions.items():
        if data.get(key) != expected:
            raise ValueError(f"R48 R1 {key} changed")
    if data.get("r47_local_review_root_env_var") != P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR:
        raise ValueError("R48 R1 must inherit the R47 local review root env var")
    if data.get("packet_kind") != P7_R48_PACKET_KIND:
        raise ValueError("R48 R1 packet kind changed")
    if data.get("review_kind") != P7_R48_REVIEW_KIND:
        raise ValueError("R48 R1 review kind changed")
    if data.get("r48_scope_fixed") is not True or data.get("r48_schema_versions_fixed") is not True:
        raise ValueError("R48 R1 must fix scope and schema versions")
    if data.get("packet_kind_fixed") is not True or data.get("review_kind_fixed") is not True:
        raise ValueError("R48 R1 must fix packet_kind and review_kind")
    if list(data.get("p5_human_blind_qa_families") or []) != list(P5_HUMAN_BLIND_QA_FAMILIES):
        raise ValueError("R48 R1 P5 family refs changed")
    if list(data.get("p5_human_blind_qa_rating_axes") or []) != list(P5_HUMAN_BLIND_QA_RATING_AXES):
        raise ValueError("R48 R1 P5 rating axes changed")
    if safe_mapping(data.get("p5_human_blind_qa_target_thresholds")) != dict(P5_HUMAN_BLIND_QA_TARGETS):
        raise ValueError("R48 R1 P5 target thresholds changed")
    if safe_mapping(data.get("r47_p5_first_formal_minimums")) != dict(P7_R47_P5_FIRST_FORMAL_MINIMUMS):
        raise ValueError("R48 R1 must inherit R47 P5 first formal minimums")
    if list(data.get("r47_p5_reviewer_facing_allowed_field_refs") or []) != list(P7_R47_P5_REVIEWER_FACING_ALLOWED_FIELD_REFS):
        raise ValueError("R48 R1 reviewer-facing allowed refs changed")
    if list(data.get("r47_p5_reviewer_facing_forbidden_field_refs") or []) != list(P7_R47_P5_REVIEWER_FACING_FORBIDDEN_FIELD_REFS):
        raise ValueError("R48 R1 reviewer-facing forbidden refs changed")
    policy = safe_mapping(data.get("packet_policy"))
    if policy.get("packet_kind") != P7_R48_PACKET_KIND or policy.get("review_kind") != P7_R48_REVIEW_KIND:
        raise ValueError("R48 R1 packet policy kind changed")
    for true_key in (
        "p5_actual_review_packet_lane_only",
        "local_only_required_later",
        "body_full_payload_allowed_only_later_with_valid_local_root_and_explicit_allow",
        "body_free_result_required_later",
        "body_free",
    ):
        if policy.get(true_key) is not True:
            raise ValueError(f"R48 R1 packet policy must keep {true_key}=True")
    for false_key in (
        "p6_limited_human_readfeel_in_scope",
        "real_device_modal_review_in_scope",
        "release_decision_in_scope",
        "materialized_here",
        "writer_created_here",
        "standard_export_allowed",
        "public_meta_material_allowed",
        "p7_scorecard_body_full_material_allowed",
        "release_material_allowed",
    ):
        if policy.get(false_key) is not False:
            raise ValueError(f"R48 R1 packet policy must keep {false_key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R48_IMPLEMENTED_STEPS:
        raise ValueError("R48 R1 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R48_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R48 R1 not-yet-implemented steps changed")
    if data.get("next_required_step") != P7_R48_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R48 R1 must point to R2 next")
    if data.get("r0_current_source_r47_handoff_hold_refrozen") is not True:
        raise ValueError("R48 R1 must preserve R0 marker")
    if data.get("r1_scope_schema_packet_kind_fixed") is not True:
        raise ValueError("R48 R1 marker must be true")
    if data.get("p5_human_blind_qa_start_allowed_after_r47_policy") is not True:
        raise ValueError("R48 R1 must preserve the R47 P5 start-allowed handoff")
    _assert_r0_r1_not_ready(data, source="p7_r48_r1_scope_freeze")
    return True


def assert_p7_r48_r0_r1_scope_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_common(
        data,
        schema_version=P7_R48_R0_R1_SCOPE_FREEZE_SCHEMA_VERSION,
        source="p7_r48_r0_r1_scope_freeze",
    )
    if data.get("freeze_kind") != "r0_r1_scope_freeze":
        raise ValueError("R48 R0/R1 combined freeze kind changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R48_IMPLEMENTED_STEPS:
        raise ValueError("R48 R0/R1 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R48_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R48 R0/R1 not-yet-implemented steps changed")
    assert_p7_r48_current_source_r47_handoff_hold_refreeze_contract(safe_mapping(data.get("r0_current_source_refreeze")))
    assert_p7_r48_scope_schema_packet_kind_freeze_contract(safe_mapping(data.get("r1_scope_schema_packet_kind_freeze")))
    if data.get("first_next_work_ref") != P7_R48_FIRST_NEXT_WORK_REF:
        raise ValueError("R48 R0/R1 first next work changed")
    if data.get("next_required_step") != P7_R48_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R48 R0/R1 must point to R2 next")
    if data.get("packet_kind") != P7_R48_PACKET_KIND or data.get("review_kind") != P7_R48_REVIEW_KIND:
        raise ValueError("R48 R0/R1 packet or review kind changed")
    if data.get("r0_current_source_r47_handoff_hold_refrozen") is not True:
        raise ValueError("R48 R0/R1 must preserve R0 marker")
    if data.get("r1_scope_schema_packet_kind_fixed") is not True:
        raise ValueError("R48 R0/R1 must preserve R1 marker")
    if data.get("p5_human_blind_qa_start_allowed_after_r47_policy") is not True:
        raise ValueError("R48 R0/R1 must preserve the R47 P5 start-allowed handoff")
    _assert_r0_r1_not_ready(data, source="p7_r48_r0_r1_scope_freeze")
    return True



def build_p7_r48_display_contract_rn_no_touch_confirmation(
    *,
    r14_r15_regression_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r48_display_contract_rn_no_touch_confirmation",
) -> dict[str, Any]:
    """Build the R16 body-free display-contract/RN no-touch confirmation policy."""

    r15 = (
        safe_mapping(r14_r15_regression_freeze)
        if r14_r15_regression_freeze is not None
        else build_p7_r48_r14_r15_regression_freeze()
    )
    assert_p7_r48_r14_r15_regression_freeze_contract(r15)
    policy = {
        "schema_version": P7_R48_DISPLAY_CONTRACT_RN_NO_TOUCH_CONFIRMATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R48_STEP,
        "scope": P7_R48_SCOPE,
        "policy_kind": P7_R48_POLICY_KIND,
        "policy_section": "R16_display_contract_rn_no_touch_confirmation",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r48_display_contract_rn_no_touch_confirmation", max_length=160),
        "r14_r15_regression_freeze_ref": clean_identifier(r15.get("material_id"), default="p7_r48_r14_r15_regression_freeze", max_length=160),
        "display_contract_regression_required": True,
        "display_contract_regression_test_refs": list(P7_R48_DISPLAY_CONTRACT_REGRESSION_TEST_REFS),
        "display_contract_regression_executed_here": False,
        "actual_display_contract_regression_executed_here": False,
        "display_contract_green_confirmed_here": False,
        "display_contract_green_claim_allowed": False,
        "rn_no_touch_confirmation_required": True,
        "rn_contract_optional": True,
        "rn_contract_test_refs": list(P7_R48_RN_CONTRACT_OPTIONAL_TEST_REFS),
        "rn_contract_command_refs": list(P7_R48_RN_CONTRACT_COMMAND_REFS),
        "rn_contract_executed_here": False,
        "actual_rn_contract_executed_here": False,
        "rn_contract_green_confirmed_here": False,
        "rn_production_file_refs": list(P7_R48_RN_PRODUCTION_NO_TOUCH_FILE_REFS),
        "rn_contract_changed_here": False,
        "rn_production_files_touched_here": False,
        "rn_visible_contract_changed_here": False,
        "public_response_shape_changed_here": False,
        "api_response_shape_changed_here": False,
        "public_response_top_level_key_added_here": False,
        "db_schema_changed_here": False,
        "emlis_reply_runtime_changed_here": False,
        "p5_runtime_changed_here": False,
        "p5_gate_relaxed_here": False,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "real_device_modal_review_start_allowed": False,
        "real_device_modal_review_confirmed": False,
        "actual_human_review_run_here": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "local_reviewer_payload_materialized_here": False,
        "implemented_steps": list(P7_R48_R16_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R48_R16_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R48_R16_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
    }
    assert_p7_r48_display_contract_rn_no_touch_confirmation_contract(policy)
    return policy


def _build_p7_r48_validation_command_rows() -> list[dict[str, Any]]:
    def row(
        validation_ref: str,
        validation_group: str,
        command_ref: str,
        target_refs: Sequence[str] = (),
        *,
        required: bool = True,
        optional: bool = False,
        working_dir_ref: str = "mashos-api/ai",
    ) -> dict[str, Any]:
        return {
            "validation_ref": validation_ref,
            "validation_group": validation_group,
            "required": required,
            "optional": optional,
            "working_dir_ref": working_dir_ref,
            "command_ref": command_ref,
            "target_refs": list(target_refs),
            "executed_here": False,
            "green_confirmed_here": False,
            "green_claim_allowed_here": False,
            "full_backend_suite_green_confirmation": False,
            "body_free": True,
        }

    return [
        row(
            "py_compile",
            "syntax_import",
            "PYTHONPATH=services/ai_inference python -m py_compile services/ai_inference/emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet.py",
            (),
        ),
        row(
            "r48_target_tests",
            "r48_target",
            "PYTHONPATH=services/ai_inference pytest -q <P7_R48_R48_TARGET_TEST_REFS>",
            P7_R48_R48_TARGET_TEST_REFS,
        ),
        row(
            "r47_target_regression",
            "r47_regression",
            "PYTHONPATH=services/ai_inference pytest -q <P7_R48_R47_TARGET_REGRESSION_TEST_REFS>",
            P7_R48_R47_TARGET_REGRESSION_TEST_REFS,
        ),
        row(
            "r46_handoff_regression",
            "r46_regression",
            "PYTHONPATH=services/ai_inference pytest -q <P7_R48_R46_HANDOFF_REGRESSION_TEST_REFS>",
            P7_R48_R46_HANDOFF_REGRESSION_TEST_REFS,
        ),
        row(
            "display_contract_regression",
            "display_contract",
            "PYTHONPATH=services/ai_inference pytest -q tests/test_emlis_ai_display_contract.py",
            P7_R48_DISPLAY_CONTRACT_REGRESSION_TEST_REFS,
        ),
        row(
            "p5_core_subset_regression",
            "p5_core_subset",
            "PYTHONPATH=services/ai_inference pytest -q <P7_R48_P5_CORE_SUBSET_REGRESSION_TEST_REFS>",
            P7_R48_P5_CORE_SUBSET_REGRESSION_TEST_REFS,
        ),
        row(
            "backend_collect_only",
            "collect_only",
            "PYTHONPATH=services/ai_inference pytest --collect-only -q",
            (),
        ),
        row(
            "rn_contract_optional",
            "rn_contract_optional",
            P7_R48_RN_CONTRACT_COMMAND_REFS[0],
            P7_R48_RN_CONTRACT_OPTIONAL_TEST_REFS,
            required=False,
            optional=True,
            working_dir_ref="Cocolon",
        ),
    ]


def build_p7_r48_validation_command_matrix(
    *,
    display_contract_rn_no_touch_confirmation: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r48_validation_command_matrix",
) -> dict[str, Any]:
    """Build the R17 body-free validation command matrix without executing commands."""

    r16 = (
        safe_mapping(display_contract_rn_no_touch_confirmation)
        if display_contract_rn_no_touch_confirmation is not None
        else build_p7_r48_display_contract_rn_no_touch_confirmation()
    )
    assert_p7_r48_display_contract_rn_no_touch_confirmation_contract(r16)
    matrix = {
        "schema_version": P7_R48_VALIDATION_COMMAND_MATRIX_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R48_STEP,
        "scope": P7_R48_SCOPE,
        "policy_kind": P7_R48_POLICY_KIND,
        "policy_section": "R17_validation_command_matrix",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r48_validation_command_matrix", max_length=160),
        "r16_display_contract_rn_no_touch_ref": clean_identifier(r16.get("material_id"), default="p7_r48_display_contract_rn_no_touch_confirmation", max_length=160),
        "validation_command_matrix_required": True,
        "validation_command_refs": list(P7_R48_VALIDATION_COMMAND_REFS),
        "validation_command_rows": _build_p7_r48_validation_command_rows(),
        "validation_commands_executed_here": False,
        "actual_validation_commands_executed_here": False,
        "r48_target_tests_green_confirmed_here": False,
        "r47_target_regression_green_confirmed_here": False,
        "r46_handoff_regression_green_confirmed_here": False,
        "display_contract_green_confirmed_here": False,
        "p5_core_subset_green_confirmed_here": False,
        "backend_collect_only_executed_here": False,
        "backend_collect_only_green_confirmed_here": False,
        "backend_collect_only_claimed_as_full_suite_green": False,
        "full_backend_suite_executed_here": False,
        "full_backend_suite_green_confirmed_here": False,
        "rn_contract_optional": True,
        "rn_contract_executed_here": False,
        "rn_contract_green_confirmed_here": False,
        "collect_only_is_full_backend_suite_green": False,
        "green_unconfirmed_must_not_be_reported_as_green": True,
        "implemented_steps": list(P7_R48_R16_R17_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R48_R16_R17_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R48_R16_R17_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
    }
    matrix["green_unconfirmed_must_not_be_reported_as_green"] = True
    matrix["rn_contract_optional"] = True
    assert_p7_r48_validation_command_matrix_contract(matrix)
    return matrix


def build_p7_r48_r16_r17_validation_no_touch_freeze(
    *,
    r14_r15_regression_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r48_r16_r17_validation_no_touch_freeze",
) -> dict[str, Any]:
    """Build the R16/R17 combined no-touch validation freeze."""

    r15 = (
        safe_mapping(r14_r15_regression_freeze)
        if r14_r15_regression_freeze is not None
        else build_p7_r48_r14_r15_regression_freeze()
    )
    assert_p7_r48_r14_r15_regression_freeze_contract(r15)
    r16 = build_p7_r48_display_contract_rn_no_touch_confirmation(r14_r15_regression_freeze=r15)
    r17 = build_p7_r48_validation_command_matrix(display_contract_rn_no_touch_confirmation=r16)
    freeze = {
        "schema_version": P7_R48_R16_R17_VALIDATION_NO_TOUCH_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R48_STEP,
        "scope": P7_R48_SCOPE,
        "policy_kind": P7_R48_POLICY_KIND,
        "freeze_kind": "r16_r17_validation_no_touch_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r48_r16_r17_validation_no_touch_freeze", max_length=160),
        "r14_r15_regression_freeze": r15,
        "display_contract_rn_no_touch_confirmation": r16,
        "validation_command_matrix": r17,
        "display_contract_regression_required": True,
        "rn_no_touch_confirmation_required": True,
        "validation_command_matrix_required": True,
        "display_contract_regression_executed_here": False,
        "actual_display_contract_regression_executed_here": False,
        "validation_commands_executed_here": False,
        "actual_validation_commands_executed_here": False,
        "rn_contract_executed_here": False,
        "actual_rn_contract_executed_here": False,
        "rn_production_files_touched_here": False,
        "rn_contract_changed_here": False,
        "rn_visible_contract_changed_here": False,
        "p5_runtime_changed_here": False,
        "p5_gate_relaxed_here": False,
        "api_response_shape_changed_here": False,
        "db_schema_changed_here": False,
        "emlis_reply_runtime_changed_here": False,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "real_device_modal_review_start_allowed": False,
        "real_device_modal_review_confirmed": False,
        "actual_human_review_run_here": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "local_reviewer_payload_materialized_here": False,
        "full_backend_suite_executed_here": False,
        "backend_collect_only_claimed_as_full_suite_green": False,
        "implemented_steps": list(P7_R48_R16_R17_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R48_R16_R17_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R48_R16_R17_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
    }
    assert_p7_r48_r16_r17_validation_no_touch_freeze_contract(freeze)
    return freeze


def _assert_r16_r17_not_actualized(data: Mapping[str, Any], *, source: str) -> None:
    for key in _R48_R16_R17_FALSE_KEYS:
        if key in data and data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=False during R48 R16/R17")


def assert_p7_r48_display_contract_rn_no_touch_confirmation_contract(policy: Mapping[str, Any]) -> bool:
    data = safe_mapping(policy)
    if set(data) != set(P7_R48_DISPLAY_CONTRACT_RN_NO_TOUCH_REQUIRED_FIELD_REFS):
        raise ValueError("R48 R16 display/RN no-touch fields must exactly match the body-free schema")
    _assert_common(data, schema_version=P7_R48_DISPLAY_CONTRACT_RN_NO_TOUCH_CONFIRMATION_SCHEMA_VERSION, source="p7_r48_r16_display_contract_rn_no_touch_confirmation")
    if data.get("policy_section") != "R16_display_contract_rn_no_touch_confirmation":
        raise ValueError("R48 R16 policy section changed")
    if data.get("display_contract_regression_required") is not True:
        raise ValueError("R48 R16 must require display contract regression")
    if tuple(data.get("display_contract_regression_test_refs") or ()) != P7_R48_DISPLAY_CONTRACT_REGRESSION_TEST_REFS:
        raise ValueError("R48 R16 display contract regression test refs changed")
    if data.get("rn_no_touch_confirmation_required") is not True or data.get("rn_contract_optional") is not True:
        raise ValueError("R48 R16 must keep RN no-touch required and RN contract optional")
    if tuple(data.get("rn_contract_test_refs") or ()) != P7_R48_RN_CONTRACT_OPTIONAL_TEST_REFS:
        raise ValueError("R48 R16 RN optional contract test refs changed")
    if tuple(data.get("rn_contract_command_refs") or ()) != P7_R48_RN_CONTRACT_COMMAND_REFS:
        raise ValueError("R48 R16 RN optional command refs changed")
    if tuple(data.get("rn_production_file_refs") or ()) != P7_R48_RN_PRODUCTION_NO_TOUCH_FILE_REFS:
        raise ValueError("R48 R16 RN production no-touch refs changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R48_R16_IMPLEMENTED_STEPS:
        raise ValueError("R48 R16 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R48_R16_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R48 R16 not-yet steps changed")
    if data.get("next_required_step") != P7_R48_R16_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R48 R16 must point to R17 next")
    _assert_r16_r17_not_actualized(data, source="p7_r48_r16_display_contract_rn_no_touch_confirmation")
    return True


def assert_p7_r48_validation_command_matrix_contract(matrix: Mapping[str, Any]) -> bool:
    data = safe_mapping(matrix)
    if set(data) != set(P7_R48_VALIDATION_COMMAND_MATRIX_REQUIRED_FIELD_REFS):
        raise ValueError("R48 R17 validation command matrix fields must exactly match the body-free schema")
    _assert_common(data, schema_version=P7_R48_VALIDATION_COMMAND_MATRIX_SCHEMA_VERSION, source="p7_r48_r17_validation_command_matrix")
    if data.get("policy_section") != "R17_validation_command_matrix":
        raise ValueError("R48 R17 policy section changed")
    if data.get("validation_command_matrix_required") is not True:
        raise ValueError("R48 R17 must require a validation command matrix")
    if tuple(data.get("validation_command_refs") or ()) != P7_R48_VALIDATION_COMMAND_REFS:
        raise ValueError("R48 R17 validation command refs changed")
    rows = data.get("validation_command_rows")
    if not isinstance(rows, list) or len(rows) != len(P7_R48_VALIDATION_COMMAND_REFS):
        raise ValueError("R48 R17 validation command rows changed")
    seen: list[str] = []
    for row in rows:
        row_data = safe_mapping(row)
        if set(row_data) != set(P7_R48_VALIDATION_COMMAND_ROW_FIELD_REFS):
            raise ValueError("R48 R17 validation command row fields changed")
        if row_data.get("body_free") is not True:
            raise ValueError("R48 R17 validation command rows must be body-free")
        for false_key in ("executed_here", "green_confirmed_here", "green_claim_allowed_here", "full_backend_suite_green_confirmation"):
            if row_data.get(false_key) is not False:
                raise ValueError(f"R48 R17 validation command row must keep {false_key}=False")
        seen.append(clean_identifier(row_data.get("validation_ref"), default="", max_length=120))
    if tuple(seen) != P7_R48_VALIDATION_COMMAND_REFS:
        raise ValueError("R48 R17 validation command row order changed")
    rows_by_ref = {safe_mapping(row)["validation_ref"]: safe_mapping(row) for row in rows}
    expected_targets = {
        "r48_target_tests": P7_R48_R48_TARGET_TEST_REFS,
        "r47_target_regression": P7_R48_R47_TARGET_REGRESSION_TEST_REFS,
        "r46_handoff_regression": P7_R48_R46_HANDOFF_REGRESSION_TEST_REFS,
        "display_contract_regression": P7_R48_DISPLAY_CONTRACT_REGRESSION_TEST_REFS,
        "p5_core_subset_regression": P7_R48_P5_CORE_SUBSET_REGRESSION_TEST_REFS,
        "rn_contract_optional": P7_R48_RN_CONTRACT_OPTIONAL_TEST_REFS,
    }
    for ref, expected in expected_targets.items():
        if tuple(rows_by_ref[ref].get("target_refs") or ()) != expected:
            raise ValueError(f"R48 R17 {ref} targets changed")
    if rows_by_ref["rn_contract_optional"].get("required") is not False or rows_by_ref["rn_contract_optional"].get("optional") is not True:
        raise ValueError("R48 R17 RN contract must remain optional")
    if data.get("green_unconfirmed_must_not_be_reported_as_green") is not True:
        raise ValueError("R48 R17 must keep unconfirmed green claims blocked")
    if data.get("collect_only_is_full_backend_suite_green") is not False:
        raise ValueError("R48 R17 collect-only must not count as full backend suite green")
    if data.get("rn_contract_optional") is not True:
        raise ValueError("R48 R17 must keep RN contract optional")
    if tuple(data.get("implemented_steps") or ()) != P7_R48_R16_R17_IMPLEMENTED_STEPS:
        raise ValueError("R48 R17 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R48_R16_R17_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R48 R17 not-yet steps changed")
    if data.get("next_required_step") != P7_R48_R16_R17_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R48 R17 must point to R18 next")
    _assert_r16_r17_not_actualized(data, source="p7_r48_r17_validation_command_matrix")
    return True


def assert_p7_r48_r16_r17_validation_no_touch_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_common(data, schema_version=P7_R48_R16_R17_VALIDATION_NO_TOUCH_FREEZE_SCHEMA_VERSION, source="p7_r48_r16_r17_validation_no_touch_freeze")
    if data.get("freeze_kind") != "r16_r17_validation_no_touch_freeze":
        raise ValueError("R48 R16/R17 freeze kind changed")
    assert_p7_r48_r14_r15_regression_freeze_contract(safe_mapping(data.get("r14_r15_regression_freeze")))
    assert_p7_r48_display_contract_rn_no_touch_confirmation_contract(safe_mapping(data.get("display_contract_rn_no_touch_confirmation")))
    assert_p7_r48_validation_command_matrix_contract(safe_mapping(data.get("validation_command_matrix")))
    for true_key in ("display_contract_regression_required", "rn_no_touch_confirmation_required", "validation_command_matrix_required"):
        if data.get(true_key) is not True:
            raise ValueError(f"R48 R16/R17 freeze must keep {true_key}=True")
    if tuple(data.get("implemented_steps") or ()) != P7_R48_R16_R17_IMPLEMENTED_STEPS:
        raise ValueError("R48 R16/R17 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R48_R16_R17_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R48 R16/R17 not-yet steps changed")
    if data.get("next_required_step") != P7_R48_R16_R17_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R48 R16/R17 must point to R18 next")
    _assert_r16_r17_not_actualized(data, source="p7_r48_r16_r17_validation_no_touch_freeze")
    return True


def build_p7_r48_touch_candidate_no_touch_boundary_freeze(
    *,
    r16_r17_validation_no_touch_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r48_touch_candidate_no_touch_boundary_freeze",
) -> dict[str, Any]:
    """Build the R18 body-free touch-candidate/no-touch boundary freeze.

    This builder fixes the file refs that R48 may touch and the refs/areas that
    must remain no-touch. It does not scan the filesystem, execute validation,
    or claim that the current patch has been externally verified.
    """

    r17 = (
        safe_mapping(r16_r17_validation_no_touch_freeze)
        if r16_r17_validation_no_touch_freeze is not None
        else build_p7_r48_r16_r17_validation_no_touch_freeze()
    )
    assert_p7_r48_r16_r17_validation_no_touch_freeze_contract(r17)
    freeze = {
        "schema_version": P7_R48_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R48_STEP,
        "scope": P7_R48_SCOPE,
        "policy_kind": P7_R48_POLICY_KIND,
        "policy_section": "R18_touch_candidate_no_touch_boundary_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r48_touch_candidate_no_touch_boundary_freeze", max_length=160),
        "r16_r17_validation_no_touch_freeze_ref": clean_identifier(r17.get("material_id"), default="p7_r48_r16_r17_validation_no_touch_freeze", max_length=160),
        "touch_boundary_freeze_required": True,
        "production_touch_candidate_file_refs": list(P7_R48_PRODUCTION_TOUCH_CANDIDATE_FILE_REFS),
        "optional_touch_candidate_file_refs": list(P7_R48_OPTIONAL_TOUCH_CANDIDATE_FILE_REFS),
        "test_touch_candidate_file_refs": list(P7_R48_R48_TARGET_TEST_REFS),
        "allowed_production_file_refs": list(P7_R48_ALLOWED_PRODUCTION_TOUCH_FILE_REFS),
        "allowed_test_file_refs": list(P7_R48_ALLOWED_TEST_TOUCH_FILE_REFS),
        "allowed_actual_touched_file_refs": list(P7_R48_ALLOWED_ACTUAL_TOUCHED_FILE_REFS),
        "explicit_no_touch_file_refs": list(P7_R48_EXPLICIT_NO_TOUCH_FILE_REFS),
        "explicit_no_touch_area_refs": list(P7_R48_EXPLICIT_NO_TOUCH_AREA_REFS),
        "forbidden_actual_touched_file_refs": list(P7_R48_EXPLICIT_NO_TOUCH_FILE_REFS),
        "current_patch_expected_touched_file_refs": list(P7_R48_R18_CURRENT_PATCH_EXPECTED_TOUCHED_FILE_REFS),
        "actual_touched_file_refs_checked_here": False,
        "actual_touched_file_refs_verified_here": False,
        "actual_touched_file_refs_materialized_here": False,
        "forbidden_actual_touched_refs_detected_here": False,
        "touch_candidate_boundary_frozen": True,
        "no_touch_boundary_frozen": True,
        "forbidden_actual_touched_refs_rejected": True,
        "no_touch_refs_must_remain_untouched": True,
        "allowed_refs_do_not_include_no_touch_refs": True,
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
        "api_route_changed_here": False,
        "db_schema_changed_here": False,
        "db_migration_changed_here": False,
        "emlis_reply_runtime_changed_here": False,
        "p5_runtime_changed_here": False,
        "p5_gate_relaxed_here": False,
        "release_material_changed_here": False,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "real_device_modal_review_start_allowed": False,
        "real_device_modal_review_confirmed": False,
        "actual_human_review_run_here": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "local_reviewer_payload_materialized_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_disposal_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "implemented_steps": list(P7_R48_R18_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R48_R18_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R48_R18_NEXT_REQUIRED_STEP_REF,
        "post_r18_next_work_ref": P7_R48_R18_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
    }
    assert_p7_r48_touch_candidate_no_touch_boundary_freeze_contract(freeze)
    return freeze


def _assert_r18_not_actualized(data: Mapping[str, Any], *, source: str) -> None:
    for key in _R48_R18_FALSE_KEYS:
        if key in data and data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=False during R48 R18")


def assert_p7_r48_touch_candidate_no_touch_boundary_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    if set(data) != set(P7_R48_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS):
        raise ValueError("R48 R18 touch/no-touch boundary fields must exactly match the body-free schema")
    _assert_common(data, schema_version=P7_R48_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION, source="p7_r48_r18_touch_candidate_no_touch_boundary_freeze")
    if data.get("policy_section") != "R18_touch_candidate_no_touch_boundary_freeze":
        raise ValueError("R48 R18 policy section changed")
    if data.get("touch_boundary_freeze_required") is not True:
        raise ValueError("R48 R18 must require a touch/no-touch boundary freeze")
    if tuple(data.get("production_touch_candidate_file_refs") or ()) != P7_R48_PRODUCTION_TOUCH_CANDIDATE_FILE_REFS:
        raise ValueError("R48 R18 production touch candidate refs changed")
    if tuple(data.get("optional_touch_candidate_file_refs") or ()) != P7_R48_OPTIONAL_TOUCH_CANDIDATE_FILE_REFS:
        raise ValueError("R48 R18 optional touch candidate refs changed")
    if tuple(data.get("test_touch_candidate_file_refs") or ()) != P7_R48_R48_TARGET_TEST_REFS:
        raise ValueError("R48 R18 test touch candidate refs changed")
    if tuple(data.get("allowed_production_file_refs") or ()) != P7_R48_ALLOWED_PRODUCTION_TOUCH_FILE_REFS:
        raise ValueError("R48 R18 allowed production refs changed")
    if tuple(data.get("allowed_test_file_refs") or ()) != P7_R48_ALLOWED_TEST_TOUCH_FILE_REFS:
        raise ValueError("R48 R18 allowed test refs changed")
    if tuple(data.get("allowed_actual_touched_file_refs") or ()) != P7_R48_ALLOWED_ACTUAL_TOUCHED_FILE_REFS:
        raise ValueError("R48 R18 allowed actual touched refs changed")
    if tuple(data.get("explicit_no_touch_file_refs") or ()) != P7_R48_EXPLICIT_NO_TOUCH_FILE_REFS:
        raise ValueError("R48 R18 explicit no-touch file refs changed")
    if tuple(data.get("explicit_no_touch_area_refs") or ()) != P7_R48_EXPLICIT_NO_TOUCH_AREA_REFS:
        raise ValueError("R48 R18 explicit no-touch area refs changed")
    if tuple(data.get("forbidden_actual_touched_file_refs") or ()) != P7_R48_EXPLICIT_NO_TOUCH_FILE_REFS:
        raise ValueError("R48 R18 forbidden actual touched refs changed")
    if tuple(data.get("current_patch_expected_touched_file_refs") or ()) != P7_R48_R18_CURRENT_PATCH_EXPECTED_TOUCHED_FILE_REFS:
        raise ValueError("R48 R18 expected current patch touch refs changed")
    allowed = set(data.get("allowed_actual_touched_file_refs") or ())
    no_touch = set(data.get("explicit_no_touch_file_refs") or ())
    if allowed & no_touch:
        raise ValueError("R48 R18 allowed refs must not overlap no-touch refs")
    expected_current = set(data.get("current_patch_expected_touched_file_refs") or ())
    if not expected_current or not expected_current.issubset(allowed):
        raise ValueError("R48 R18 current patch expected touched refs must be allowed refs")
    if expected_current & no_touch:
        raise ValueError("R48 R18 current patch expected touched refs must not include no-touch refs")
    for true_key in (
        "touch_candidate_boundary_frozen",
        "no_touch_boundary_frozen",
        "forbidden_actual_touched_refs_rejected",
        "no_touch_refs_must_remain_untouched",
        "allowed_refs_do_not_include_no_touch_refs",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R48 R18 must keep {true_key}=True")
    if tuple(data.get("implemented_steps") or ()) != P7_R48_R18_IMPLEMENTED_STEPS:
        raise ValueError("R48 R18 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R48_R18_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R48 R18 not-yet steps changed")
    if data.get("next_required_step") != P7_R48_R18_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R48 R18 next step changed")
    if data.get("post_r18_next_work_ref") != P7_R48_R18_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R48 R18 post next work ref changed")
    _assert_r18_not_actualized(data, source="p7_r48_r18_touch_candidate_no_touch_boundary_freeze")
    return True


def assert_p7_r48_touch_candidate_no_touch_actual_touched_file_refs_contract(
    actual_touched_file_refs: Sequence[str] | Any,
    *,
    touch_boundary_freeze: Mapping[str, Any] | None = None,
) -> bool:
    """Validate actual touched file refs against the R18 boundary.

    This function validates caller-provided refs only. It does not inspect git,
    mutate files, or claim that a scan was executed inside the policy builder.
    """

    boundary = (
        safe_mapping(touch_boundary_freeze)
        if touch_boundary_freeze is not None
        else build_p7_r48_touch_candidate_no_touch_boundary_freeze()
    )
    assert_p7_r48_touch_candidate_no_touch_boundary_freeze_contract(boundary)
    touched_refs = tuple(dedupe_identifiers(actual_touched_file_refs, limit=200, max_length=220))
    if not touched_refs:
        raise ValueError("R48 R18 actual touched refs must be provided for boundary validation")
    allowed = set(boundary.get("allowed_actual_touched_file_refs") or ())
    no_touch = set(boundary.get("explicit_no_touch_file_refs") or ())
    forbidden = set(boundary.get("forbidden_actual_touched_file_refs") or ())
    touched_set = set(touched_refs)
    if touched_set & no_touch or touched_set & forbidden:
        raise ValueError("R48 R18 actual touched refs include explicit no-touch refs")
    not_allowed = sorted(touched_set - allowed)
    if not_allowed:
        raise ValueError(f"R48 R18 actual touched refs are outside allowed candidates: {not_allowed[:6]}")
    return True


__all__ = [
    "P7_R48_CURRENT_SOURCE_R47_HANDOFF_HOLD_REFREEZE_SCHEMA_VERSION",
    "P7_R48_SCOPE_SCHEMA_PACKET_KIND_FREEZE_SCHEMA_VERSION",
    "P7_R48_R0_R1_SCOPE_FREEZE_SCHEMA_VERSION",
    "P7_R48_LOCAL_STORAGE_ROOT_POLICY_SCHEMA_VERSION",
    "P7_R48_R2_R3_LOCAL_STORAGE_CASE_MATRIX_FREEZE_SCHEMA_VERSION",
    "P7_R48_BLIND_CASE_ID_CASE_REF_SEPARATION_SCHEMA_VERSION",
    "P7_R48_REVIEWER_FACING_LOCAL_PACKET_SCHEMA_FREEZE_SCHEMA_VERSION",
    "P7_R48_R4_R5_REVIEWER_PACKET_SCHEMA_FREEZE_SCHEMA_VERSION",
    "P7_R48_BODY_FULL_PACKET_MATERIALIZATION_GUARD_SCHEMA_VERSION",
    "P7_R48_LOCAL_REVIEWER_NOTES_POLICY_SCHEMA_VERSION",
    "P7_R48_R6_R7_MATERIALIZATION_NOTES_POLICY_FREEZE_SCHEMA_VERSION",
    "P7_R48_P5_REVIEW_POLICY_SCHEMA_VERSION",
    "P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION",
    "P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION",
    "P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION",
    "P7_R48_P5_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION",
    "P7_R48_P5_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION",
    "P7_R48_P5_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION",
    "P7_R48_STEP",
    "P7_R48_SCOPE",
    "P7_R48_POLICY_KIND",
    "P7_R48_PACKET_KIND",
    "P7_R48_REVIEW_KIND",
    "P7_R48_FIRST_NEXT_WORK_REF",
    "P7_R48_NEXT_REQUIRED_STEP_REF",
    "P7_R48_R2_R3_NEXT_REQUIRED_STEP_REF",
    "P7_R48_R4_NEXT_REQUIRED_STEP_REF",
    "P7_R48_R4_R5_NEXT_REQUIRED_STEP_REF",
    "P7_R48_R6_NEXT_REQUIRED_STEP_REF",
    "P7_R48_R6_R7_NEXT_REQUIRED_STEP_REF",
    "P7_R48_IMPLEMENTED_STEPS",
    "P7_R48_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R48_R2_R3_IMPLEMENTED_STEPS",
    "P7_R48_R2_R3_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R48_R4_R5_IMPLEMENTED_STEPS",
    "P7_R48_R4_R5_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R48_R6_R7_IMPLEMENTED_STEPS",
    "P7_R48_R6_R7_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R48_RECEIVED_LOCAL_SNAPSHOT_REFS",
    "P7_R48_REQUIRED_UNRESOLVED_HOLD_REFS",
    "P7_R48_REVIEW_PROMPT_VERSION",
    "P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION",
    "P7_R48_P5_CASE_MATRIX_ROW_FIELD_REFS",
    "P7_R48_CONTROLLER_MANIFEST_ROW_FIELD_REFS",
    "P7_R48_REVIEWER_FACING_CASE_INDEX_ROW_FIELD_REFS",
    "P7_R48_P5_REVIEWER_PACKET_REVIEWER_VISIBLE_FIELD_REFS",
    "P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_CONTROL_FIELD_REFS",
    "P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_REQUIRED_FIELD_REFS",
    "P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_FORBIDDEN_FIELD_REFS",
    "P7_R48_P5_REVIEWER_PACKET_BODY_FIELD_REFS",
    "P7_R48_LOCAL_REVIEWER_PACKET_REQUIRED_FLAG_REFS",
    "P7_R48_BODY_FULL_PACKET_MATERIALIZATION_BLOCK_REASON_REFS",
    "P7_R48_SANITIZED_REASON_ID_REFS",
    "P7_R48_EXECUTION_BLOCKER_ID_REFS",
    "P7_R48_P5_REVIEW_QUESTION_REFS",
    "assert_p7_r48_current_source_r47_handoff_hold_refreeze_contract",
    "assert_p7_r48_local_storage_root_policy_contract",
    "assert_p7_r48_p5_first_formal_review_case_matrix_contract",
    "assert_p7_r48_blind_case_id_case_ref_separation_contract",
    "assert_p7_r48_p5_reviewer_facing_local_packet_schema_freeze_contract",
    "assert_p7_r48_p5_reviewer_packet_local_only_payload_contract",
    "assert_p7_r48_body_full_packet_materialization_guard_contract",
    "assert_p7_r48_local_reviewer_notes_policy_contract",
    "assert_p7_r48_p5_body_full_packet_materialization_request_contract",
    "assert_p7_r48_r6_r7_materialization_notes_policy_freeze_contract",
    "assert_p7_r48_r2_r3_local_storage_case_matrix_freeze_contract",
    "assert_p7_r48_r4_r5_reviewer_packet_schema_freeze_contract",
    "assert_p7_r48_scope_schema_packet_kind_freeze_contract",
    "assert_p7_r48_r0_r1_scope_freeze_contract",
    "build_p7_r48_current_source_r47_handoff_hold_refreeze",
    "build_p7_r48_local_storage_root_policy",
    "build_p7_r48_p5_first_formal_review_case_matrix",
    "build_p7_r48_blind_case_id_case_ref_separation",
    "build_p7_r48_p5_reviewer_facing_local_packet_schema_freeze",
    "build_p7_r48_r2_r3_local_storage_case_matrix_freeze",
    "build_p7_r48_r4_r5_reviewer_packet_schema_freeze",
    "build_p7_r48_body_full_packet_materialization_guard",
    "build_p7_r48_local_reviewer_notes_policy",
    "build_p7_r48_r6_r7_materialization_notes_policy_freeze",
    "build_p7_r48_scope_schema_packet_kind_freeze",
    "build_p7_r48_r0_r1_scope_freeze",
    "P7_R48_RATING_ROW_NORMALIZER_SCHEMA_VERSION",
    "P7_R48_BLOCKER_EXECUTION_BLOCKER_ROW_BUILDER_SCHEMA_VERSION",
    "P7_R48_R8_R9_RATING_BLOCKER_ROWS_FREEZE_SCHEMA_VERSION",
    "P7_R48_P5_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION",
    "P7_R48_R8_NEXT_REQUIRED_STEP_REF",
    "P7_R48_R8_R9_NEXT_REQUIRED_STEP_REF",
    "P7_R48_R8_R9_IMPLEMENTED_STEPS",
    "P7_R48_R8_R9_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R48_P5_REVIEW_VERDICTS",
    "P7_R48_P5_REVIEWABLE_VERDICTS",
    "P7_R48_READFEEL_BLOCKER_ID_REFS",
    "P7_R48_P5_BLOCKER_KINDS",
    "P7_R48_P5_BLOCKER_STATUSES",
    "P7_R48_EXECUTION_BLOCKER_KIND_REFS",
    "P7_R48_EXECUTION_BLOCKER_STATUS_REFS",
    "P7_R48_P5_RATING_ROW_REQUIRED_FIELD_REFS",
    "P7_R48_P5_BLOCKER_ROW_REQUIRED_FIELD_REFS",
    "P7_R48_P5_EXECUTION_BLOCKER_ROW_REQUIRED_FIELD_REFS",
    "P7_R48_P5_RATING_BLOCKER_FORBIDDEN_FIELD_REFS",
    "normalize_p7_r48_p5_rating_row_bodyfree",
    "build_p7_r48_p5_blocker_row_bodyfree",
    "build_p7_r48_p5_execution_blocker_row_bodyfree",
    "build_p7_r48_rating_row_normalizer_policy",
    "build_p7_r48_blocker_execution_blocker_row_builder_policy",
    "build_p7_r48_r8_r9_rating_blocker_rows_freeze",
    "assert_p7_r48_p5_rating_row_bodyfree_contract",
    "assert_p7_r48_p5_blocker_row_bodyfree_contract",
    "assert_p7_r48_p5_execution_blocker_row_bodyfree_contract",
    "assert_p7_r48_rating_row_normalizer_policy_contract",
    "assert_p7_r48_blocker_execution_blocker_row_builder_policy_contract",
    "assert_p7_r48_r8_r9_rating_blocker_rows_freeze_contract",

    "P7_R48_DISPOSAL_RECEIPT_BUILDER_SCHEMA_VERSION",
    "P7_R48_P5_REVIEW_HANDOFF_SUMMARY_BUILDER_SCHEMA_VERSION",
    "P7_R48_R10_R11_DISPOSAL_HANDOFF_SUMMARY_FREEZE_SCHEMA_VERSION",
    "P7_R48_R10_NEXT_REQUIRED_STEP_REF",
    "P7_R48_R10_R11_NEXT_REQUIRED_STEP_REF",
    "P7_R48_R10_R11_IMPLEMENTED_STEPS",
    "P7_R48_R10_R11_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R48_P5_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS",
    "P7_R48_P5_DISPOSAL_RECEIPT_FORBIDDEN_FIELD_REFS",
    "P7_R48_P5_REVIEW_HANDOFF_SUMMARY_REQUIRED_FIELD_REFS",
    "P7_R48_REVIEW_SESSION_STATUS_REFS",
    "P7_R48_P5_CONFIRMED_ALLOWED_DISPOSAL_STATUS_REFS",
    "P7_R48_P5_BOUNDARY_VIOLATION_BLOCKER_ID_REFS",
    "build_p7_r48_p5_disposal_receipt_bodyfree",
    "build_p7_r48_p5_review_handoff_summary_bodyfree",
    "build_p7_r48_disposal_receipt_builder_policy",
    "build_p7_r48_p5_review_handoff_summary_builder_policy",
    "build_p7_r48_r10_r11_disposal_handoff_summary_freeze",
    "assert_p7_r48_p5_disposal_receipt_bodyfree_contract",
    "assert_p7_r48_p5_review_handoff_summary_bodyfree_contract",
    "assert_p7_r48_disposal_receipt_builder_policy_contract",
    "assert_p7_r48_p5_review_handoff_summary_builder_policy_contract",
    "assert_p7_r48_r10_r11_disposal_handoff_summary_freeze_contract",

    "P7_R48_P5_CONFIRMED_CANDIDATE_GATE_SCHEMA_VERSION",
    "P7_R48_R47_REGRESSION_NO_BODY_FREE_LEAK_GUARD_SCHEMA_VERSION",
    "P7_R48_R12_R13_CONFIRMED_GATE_LEAK_GUARD_FREEZE_SCHEMA_VERSION",
    "P7_R48_R12_NEXT_REQUIRED_STEP_REF",
    "P7_R48_R12_R13_NEXT_REQUIRED_STEP_REF",
    "P7_R48_R12_IMPLEMENTED_STEPS",
    "P7_R48_R12_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R48_R12_R13_IMPLEMENTED_STEPS",
    "P7_R48_R12_R13_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R48_P5_CONFIRMED_CANDIDATE_REQUIRED_CONDITION_REFS",
    "P7_R48_P5_CONFIRMED_CANDIDATE_GATE_REQUIRED_FIELD_REFS",
    "P7_R48_BODY_FREE_LEAK_GUARD_FORBIDDEN_FIELD_REFS",
    "P7_R48_R47_TARGET_REGRESSION_TEST_REFS",
    "build_p7_r48_p5_confirmed_candidate_gate_policy",
    "build_p7_r48_p5_confirmed_candidate_gate_bodyfree",
    "build_p7_r48_r47_regression_no_body_free_leak_guard",
    "build_p7_r48_r12_r13_confirmed_gate_leak_guard_freeze",
    "assert_p7_r48_no_body_free_leak_guard_bodyfree_material",
    "assert_p7_r48_p5_confirmed_candidate_gate_policy_contract",
    "assert_p7_r48_p5_confirmed_candidate_gate_bodyfree_contract",
    "assert_p7_r48_r47_regression_no_body_free_leak_guard_contract",
    "assert_p7_r48_r12_r13_confirmed_gate_leak_guard_freeze_contract",

    "P7_R48_R46_HANDOFF_REGRESSION_SCHEMA_VERSION",
    "P7_R48_P5_CORE_SUBSET_REGRESSION_SCHEMA_VERSION",
    "P7_R48_R14_R15_REGRESSION_FREEZE_SCHEMA_VERSION",
    "P7_R48_R14_NEXT_REQUIRED_STEP_REF",
    "P7_R48_R14_R15_NEXT_REQUIRED_STEP_REF",
    "P7_R48_R14_IMPLEMENTED_STEPS",
    "P7_R48_R14_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R48_R14_R15_IMPLEMENTED_STEPS",
    "P7_R48_R14_R15_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R48_R46_HANDOFF_REGRESSION_TEST_REFS",
    "P7_R48_P5_CORE_SUBSET_REGRESSION_TEST_REFS",
    "P7_R48_P5_PRODUCT_QUALITY_QA_OPTIONAL_REGRESSION_TEST_REFS",
    "build_p7_r48_r46_handoff_regression_policy",
    "build_p7_r48_p5_core_subset_regression_policy",
    "build_p7_r48_r14_r15_regression_freeze",
    "assert_p7_r48_r46_handoff_regression_policy_contract",
    "assert_p7_r48_p5_core_subset_regression_policy_contract",
    "assert_p7_r48_r14_r15_regression_freeze_contract",
    "P7_R48_DISPLAY_CONTRACT_RN_NO_TOUCH_CONFIRMATION_SCHEMA_VERSION",
    "P7_R48_VALIDATION_COMMAND_MATRIX_SCHEMA_VERSION",
    "P7_R48_R16_R17_VALIDATION_NO_TOUCH_FREEZE_SCHEMA_VERSION",
    "P7_R48_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION",
    "P7_R48_R16_NEXT_REQUIRED_STEP_REF",
    "P7_R48_R16_R17_NEXT_REQUIRED_STEP_REF",
    "P7_R48_R18_NEXT_REQUIRED_STEP_REF",
    "P7_R48_R16_IMPLEMENTED_STEPS",
    "P7_R48_R16_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R48_R16_R17_IMPLEMENTED_STEPS",
    "P7_R48_R16_R17_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R48_R18_IMPLEMENTED_STEPS",
    "P7_R48_R18_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R48_DISPLAY_CONTRACT_REGRESSION_TEST_REFS",
    "P7_R48_RN_CONTRACT_OPTIONAL_TEST_REFS",
    "P7_R48_RN_PRODUCTION_NO_TOUCH_FILE_REFS",
    "P7_R48_RN_CONTRACT_COMMAND_REFS",
    "P7_R48_R48_TARGET_TEST_REFS",
    "P7_R48_PRODUCTION_TOUCH_CANDIDATE_FILE_REFS",
    "P7_R48_OPTIONAL_TOUCH_CANDIDATE_FILE_REFS",
    "P7_R48_ALLOWED_PRODUCTION_TOUCH_FILE_REFS",
    "P7_R48_ALLOWED_TEST_TOUCH_FILE_REFS",
    "P7_R48_ALLOWED_ACTUAL_TOUCHED_FILE_REFS",
    "P7_R48_EXPLICIT_NO_TOUCH_FILE_REFS",
    "P7_R48_EXPLICIT_NO_TOUCH_AREA_REFS",
    "P7_R48_R18_CURRENT_PATCH_EXPECTED_TOUCHED_FILE_REFS",
    "P7_R48_VALIDATION_COMMAND_REFS",
    "P7_R48_VALIDATION_COMMAND_ROW_FIELD_REFS",
    "P7_R48_DISPLAY_CONTRACT_RN_NO_TOUCH_REQUIRED_FIELD_REFS",
    "P7_R48_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS",
    "P7_R48_VALIDATION_COMMAND_MATRIX_REQUIRED_FIELD_REFS",
    "build_p7_r48_display_contract_rn_no_touch_confirmation",
    "build_p7_r48_validation_command_matrix",
    "build_p7_r48_r16_r17_validation_no_touch_freeze",
    "build_p7_r48_touch_candidate_no_touch_boundary_freeze",
    "assert_p7_r48_display_contract_rn_no_touch_confirmation_contract",
    "assert_p7_r48_validation_command_matrix_contract",
    "assert_p7_r48_r16_r17_validation_no_touch_freeze_contract",
    "assert_p7_r48_touch_candidate_no_touch_boundary_freeze_contract",
    "assert_p7_r48_touch_candidate_no_touch_actual_touched_file_refs_contract",


]
