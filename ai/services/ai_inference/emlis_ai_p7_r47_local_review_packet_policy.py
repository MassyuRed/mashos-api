# -*- coding: utf-8 -*-
"""P7-R47 local review packet policy freeze helpers.

R0 refreezes the current local source/R46 branch-A handoff/HOLD state.
R1 fixes only the R47 scope, schema version, and packet-kind enum.
R2 fixes the local-only storage-root policy without writing body-full packets.
R3 fixes the export denylist/Git-zip mixing prevention policy.
R4 fixes the body-full local packet schema proposal as local-only/non-exportable
metadata without creating a writer or any body-full packet.
R5 fixes the body-free manifest schema proposal and a payload contract for future
manifest rows without materializing local reviewer payloads.
R6 fixes body-free rating-row and blocker-row schema proposals without writing
actual review result rows.
R7 fixes reviewer free-text/notes as local-only material that may only be reduced
to sanitized reason/blocker identifiers for P7 material.
R8 fixes disposal/cleanup/retention and the body-free disposal receipt policy.
R9 fixes the P5 human Blind QA packet policy.
R10 fixes the P6 limited human readfeel packet policy.
R11 fixes the real-device modal review packet policy.
R12 fixes how R47 connects back to the R46 next-decision ledger as body-free
policy-ready handoff material.
R13 fixes the R47 contract-test policy required to prevent body-full/body-free
mixing regressions.
R14 fixes the target validation command matrix without claiming unexecuted
commands as green.
R15 fixes implementation touch candidates and no-touch boundaries so R47 policy
work cannot drift into runtime, RN, API, DB, release, or Gate threshold changes.

This module intentionally does not generate body-full reviewer packets, create
actual review manifests, write rating rows, write reviewer notes, run disposal,
start P5/P6 human review, run real-device review, close HOLD-004, complete P7,
open P8, or permit release.
"""

from __future__ import annotations

import fnmatch
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
from emlis_ai_p7_r46_next_decision_handoff_ledger import (
    BRANCH_A_DISPLAY_GREEN_LINEAGE_CONSISTENT,
    P7_R46_NEXT_DECISION_HANDOFF_LEDGER_SCHEMA_VERSION,
    P7_R46_NEXT_DECISION_HANDOFF_LEDGER_STEP,
    assert_p7_r46_next_decision_handoff_ledger_contract,
    build_p7_r46_next_decision_handoff_ledger,
)
from emlis_ai_p7_r46_p5_p6_human_readfeel_handoff_material import (
    P5_HUMAN_BLIND_QA_FAMILIES,
    P5_HUMAN_BLIND_QA_HOLD_REF,
    P5_HUMAN_BLIND_QA_RATING_AXES,
    P5_HUMAN_BLIND_QA_RETURN_HOLD_REF,
    P5_HUMAN_BLIND_QA_TARGETS,
    P6_LIMITED_HUMAN_READFEEL_HOLD_REF,
    P6_LIMITED_HUMAN_READFEEL_RETURN_HOLD_REF,
    P6_LIMITED_READFEEL_RATING_AXES,
    P6_LIMITED_READFEEL_REVIEW_FAMILIES,
    P6_LIMITED_READFEEL_TARGETS,
    P6_NO_CONNECT_FAMILIES,
)
from emlis_ai_p7_r46_real_device_modal_review_closed_validation import (
    HOLD_DC_FULL_BACKEND_SUITE_REF,
    P7_HOLD_FULL_BACKEND_SUITE_REF,
    P7_HOLD_REAL_DEVICE_MODAL_REF,
    P7_RETURN_REAL_DEVICE_HOLD_REF,
    assert_real_device_submit_modal_readfeel_checklist_contract,
    build_real_device_submit_modal_readfeel_checklist,
)

P7_R47_CURRENT_SOURCE_REFREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r47.current_source_r46_handoff_hold_refreeze.v1"
)
P7_R47_SCOPE_SCHEMA_PACKET_KIND_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r47.scope_schema_packet_kind_freeze.v1"
)
P7_R47_R0_R1_SCOPE_FREEZE_SCHEMA_VERSION: Final = "cocolon.emlis.p7_r47.r0_r1_scope_freeze.v1"
P7_R47_LOCAL_REVIEW_PACKET_POLICY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r47.local_review_packet_policy.v1"
)
P7_R47_LOCAL_REVIEW_PACKET_STEP: Final = "R47_LocalReviewPacketPolicy_20260618"
P7_R47_LOCAL_REVIEW_PACKET_SCOPE: Final = "p7_r47_local_review_packet_storage_generation_disposal_policy"
P7_R47_POLICY_KIND: Final = "local_review_packet_policy"
P7_R47_FIRST_NEXT_WORK_REF: Final = "local_review_packet_storage_generation_disposal_policy"
P7_R47_NEXT_REQUIRED_STEP_REF: Final = "R2_local_only_storage_root_policy"
P7_R47_R2_R3_STORAGE_EXPORT_POLICY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r47.r2_r3_storage_export_policy.v1"
)
P7_R47_LOCAL_REVIEW_STORAGE_ROOT_POLICY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r47.local_review_storage_root_policy.v1"
)
P7_R47_EXPORT_DENYLIST_POLICY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r47.export_denylist_git_zip_policy.v1"
)
P7_R47_R2_R3_NEXT_REQUIRED_STEP_REF: Final = "R4_body_full_local_packet_schema"
P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR: Final = "COCOLON_EMLIS_LOCAL_REVIEW_ROOT"
P7_R47_STORAGE_MODE_EXTERNAL_LOCAL_ONLY: Final = "external_local_only"
P7_R47_STORAGE_ROOT_REF: Final = "external_local_review_root"
P7_R47_BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "p5_human_blind_qa_confirmed",
    "p6_limited_human_readfeel_confirmed",
    "real_device_modal_review_confirmed",
    "full_backend_suite_green_claim_without_execution",
    "p7_completion",
    "release_readiness",
    "p8_start",
    "p7_hold004_closure",
)

P7_R47_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R0_current_source_r46_handoff_hold_refreeze",
    "R1_scope_schema_version_packet_kind_enum_freeze",
)
P7_R47_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R2_local_only_storage_root_policy",
    "R3_export_denylist_git_zip_mixing_prevention",
    "R4_body_full_local_packet_schema",
    "R5_body_free_manifest_schema",
    "R6_body_free_rating_blocker_rows",
    "R7_reviewer_free_text_notes_local_only_policy",
    "R8_disposal_cleanup_retention_policy",
    "R9_p5_human_blind_qa_packet_policy",
    "R10_p6_limited_human_readfeel_packet_policy",
    "R11_real_device_modal_review_packet_policy",
    "R12_r46_next_decision_ledger_connection",
    "R13_r47_contract_test_policy",
    "R14_target_validation_command_matrix",
    "R15_touch_candidate_and_no_touch_boundary",
)
P7_R47_R2_R3_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R47_IMPLEMENTED_STEPS,
    "R2_local_only_storage_root_policy",
    "R3_export_denylist_git_zip_mixing_prevention",
)
P7_R47_R2_R3_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R4_body_full_local_packet_schema",
    "R5_body_free_manifest_schema",
    "R6_body_free_rating_blocker_rows",
    "R7_reviewer_free_text_notes_local_only_policy",
    "R8_disposal_cleanup_retention_policy",
    "R9_p5_human_blind_qa_packet_policy",
    "R10_p6_limited_human_readfeel_packet_policy",
    "R11_real_device_modal_review_packet_policy",
    "R12_r46_next_decision_ledger_connection",
    "R13_r47_contract_test_policy",
    "R14_target_validation_command_matrix",
    "R15_touch_candidate_and_no_touch_boundary",
)
P7_R47_BODY_FULL_LOCAL_REVIEW_PACKET_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r47.body_full_local_review_packet.local_only.v1"
)
P7_R47_BODY_FREE_LOCAL_REVIEW_MANIFEST_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r47.body_free_local_review_manifest.v1"
)
P7_R47_R4_R5_SCHEMA_FREEZE_SCHEMA_VERSION: Final = "cocolon.emlis.p7_r47.r4_r5_schema_freeze.v1"
P7_R47_R4_R5_NEXT_REQUIRED_STEP_REF: Final = "R6_body_free_rating_blocker_rows"
P7_R47_R4_R5_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R47_R2_R3_IMPLEMENTED_STEPS,
    "R4_body_full_local_packet_schema",
    "R5_body_free_manifest_schema",
)
P7_R47_R4_R5_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R6_body_free_rating_blocker_rows",
    "R7_reviewer_free_text_notes_local_only_policy",
    "R8_disposal_cleanup_retention_policy",
    "R9_p5_human_blind_qa_packet_policy",
    "R10_p6_limited_human_readfeel_packet_policy",
    "R11_real_device_modal_review_packet_policy",
    "R12_r46_next_decision_ledger_connection",
    "R13_r47_contract_test_policy",
    "R14_target_validation_command_matrix",
    "R15_touch_candidate_and_no_touch_boundary",
)
P7_R47_BODY_FREE_RATING_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r47.body_free_rating_row.v1"
)
P7_R47_BODY_FREE_BLOCKER_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r47.body_free_blocker_row.v1"
)
P7_R47_REVIEWER_NOTES_LOCAL_ONLY_POLICY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r47.reviewer_notes_local_only_policy.v1"
)
P7_R47_R6_R7_RATING_BLOCKER_NOTES_POLICY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r47.r6_r7_rating_blocker_notes_policy.v1"
)
P7_R47_R6_R7_NEXT_REQUIRED_STEP_REF: Final = "R8_disposal_cleanup_retention_policy"
P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS: Final = 24
P7_R47_R6_R7_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R47_R4_R5_IMPLEMENTED_STEPS,
    "R6_body_free_rating_blocker_rows",
    "R7_reviewer_free_text_notes_local_only_policy",
)
P7_R47_R6_R7_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R8_disposal_cleanup_retention_policy",
    "R9_p5_human_blind_qa_packet_policy",
    "R10_p6_limited_human_readfeel_packet_policy",
    "R11_real_device_modal_review_packet_policy",
    "R12_r46_next_decision_ledger_connection",
    "R13_r47_contract_test_policy",
    "R14_target_validation_command_matrix",
    "R15_touch_candidate_and_no_touch_boundary",
)
P7_R47_BODY_FULL_PACKET_RETENTION_HOURS: Final = 72
P7_R47_BODY_FREE_DISPOSAL_RECEIPT_SCHEMA_VERSION: Final = "cocolon.emlis.p7_r47.body_free_disposal_receipt.v1"
P7_R47_DISPOSAL_CLEANUP_RETENTION_POLICY_SCHEMA_VERSION: Final = "cocolon.emlis.p7_r47.disposal_cleanup_retention_policy.v1"
P7_R47_P5_HUMAN_BLIND_QA_PACKET_POLICY_SCHEMA_VERSION: Final = "cocolon.emlis.p7_r47.p5_human_blind_qa_packet_policy.v1"
P7_R47_R8_R9_DISPOSAL_P5_PACKET_POLICY_SCHEMA_VERSION: Final = "cocolon.emlis.p7_r47.r8_r9_disposal_p5_packet_policy.v1"
P7_R47_R8_R9_NEXT_REQUIRED_STEP_REF: Final = "R10_p6_limited_human_readfeel_packet_policy"
P7_R47_R8_R9_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R47_R6_R7_IMPLEMENTED_STEPS, "R8_disposal_cleanup_retention_policy", "R9_p5_human_blind_qa_packet_policy")
P7_R47_R8_R9_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = ("R10_p6_limited_human_readfeel_packet_policy", "R11_real_device_modal_review_packet_policy", "R12_r46_next_decision_ledger_connection", "R13_r47_contract_test_policy", "R14_target_validation_command_matrix", "R15_touch_candidate_and_no_touch_boundary")
P7_R47_DISPOSAL_STATUS_REFS: Final[tuple[str, ...]] = ("NOT_GENERATED", "GENERATION_BLOCKED", "GENERATED_LOCAL_ONLY", "REVIEW_IN_PROGRESS", "RATINGS_EXTRACTED", "PURGE_REQUIRED", "BODY_PURGED", "DISPOSAL_VERIFIED", "DISPOSAL_FAILED", "EXPIRED_PURGED")
P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS: Final[tuple[str, ...]] = ("rating_rows_finalized", "blocker_rows_finalized", "review_session_cancelled", "retention_deadline_reached")
P7_R47_BODY_FREE_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = ("schema_version", "review_session_id", "packet_kind", "case_count", "deleted_file_count", "disposal_status", "body_removed", "reviewer_notes_removed", "local_packet_exported", "content_hash_of_body_stored", "body_free", "release_allowed", "p7_complete", "p8_start_allowed", "hold004_close_allowed")
P7_R47_BODY_FREE_DISPOSAL_RECEIPT_OPTIONAL_FIELD_REFS: Final[tuple[str, ...]] = ("purge_started_at", "purge_completed_at", "p7_material_body_free")
P7_R47_DISPOSAL_RECEIPT_FORBIDDEN_FIELD_REFS: Final[tuple[str, ...]] = ("raw_input", "current_input", "memo", "memo_action", "history_raw_text", "comment_text", "comment_text_body", "candidate_body", "surface_body", "insight_text", "review_surface", "visible_surface", "surface_for_reviewer", "current_input_for_reviewer", "history_summary_for_reviewer", "reviewer_free_text", "reviewer_note", "reviewer_notes", "terminal_output", "stdout", "stderr", "traceback", "comment_body", "reply_text", "visible_text", "display_text", "observation_text", "reception_text", "deleted_body_preview", "body_content_hash", "body_full_file_content_hash", "raw_text_hash", "comment_text_hash", "local_absolute_path", "terminal_full_output", "traceback_full_output")
P7_R47_DISPOSAL_STATUSES: Final[tuple[str, ...]] = P7_R47_DISPOSAL_STATUS_REFS
P7_R47_BODY_FREE_DISPOSAL_RECEIPT_FORBIDDEN_FIELD_REFS: Final[tuple[str, ...]] = P7_R47_DISPOSAL_RECEIPT_FORBIDDEN_FIELD_REFS
P7_R47_R8_R9_DISPOSAL_P5_POLICY_SCHEMA_VERSION: Final = P7_R47_R8_R9_DISPOSAL_P5_PACKET_POLICY_SCHEMA_VERSION
P7_R47_P5_REVIEW_KIND: Final = "p5_history_line_readfeel"
P7_R47_P5_FIRST_FORMAL_REVIEW_MINIMUM_TOTAL_CASES: Final = 24
P7_R47_P5_FIRST_FORMAL_REVIEW_MINIMUM_PER_FAMILY: Final = 2
P7_R47_P5_MINIMUM_HISTORY_LINE_ELIGIBLE_INPUT_CASES: Final = 4
P7_R47_P5_MINIMUM_OWNED_HISTORY_POSITIVE_CASES: Final = 12
P7_R47_P5_MAX_HISTORY_RECORD_SURFACES: Final = 3
P7_R47_P5_MIN_EVIDENCE_RECORD_COUNT_WHEN_HISTORY_LINE_EXPECTED: Final = 2
P7_R47_P5_MINIMUM_BLOCK_BOUNDARY_CASE_COUNTS: Final[dict[str, int]] = {"low_information_history_not_eligible": 2, "free_tier_history_present_not_allowed": 2}
P7_R47_P5_FIRST_FORMAL_MINIMUMS: Final[dict[str, Any]] = {
    "minimum_total_cases": P7_R47_P5_FIRST_FORMAL_REVIEW_MINIMUM_TOTAL_CASES,
    "minimum_per_family": P7_R47_P5_FIRST_FORMAL_REVIEW_MINIMUM_PER_FAMILY,
    "minimum_history_line_eligible_input": P7_R47_P5_MINIMUM_HISTORY_LINE_ELIGIBLE_INPUT_CASES,
    "minimum_owned_history_positive_cases": P7_R47_P5_MINIMUM_OWNED_HISTORY_POSITIVE_CASES,
    "minimum_block_boundary_cases": dict(P7_R47_P5_MINIMUM_BLOCK_BOUNDARY_CASE_COUNTS),
}
P7_R47_P5_HISTORY_SURFACE_MAX_RECORDS: Final = P7_R47_P5_MAX_HISTORY_RECORD_SURFACES
P7_R47_P5_HISTORY_SURFACE_MIN_EVIDENCE_RECORDS: Final = P7_R47_P5_MIN_EVIDENCE_RECORD_COUNT_WHEN_HISTORY_LINE_EXPECTED
P7_R47_P5_HISTORY_SURFACE_POLICY: Final[dict[str, Any]] = {
    "max_history_record_surfaces": P7_R47_P5_MAX_HISTORY_RECORD_SURFACES,
    "min_evidence_record_count_when_history_line_expected": P7_R47_P5_MIN_EVIDENCE_RECORD_COUNT_WHEN_HISTORY_LINE_EXPECTED,
    "history_record_identifier_policy": "no_db_id_no_user_id",
    "created_at_policy": "bucketed_or_relative_only",
    "raw_memo_full_dump_allowed": False,
    "history_summary_style": "bounded_review_surface_local_only",
}
P7_R47_P5_REVIEWER_FACING_ALLOWED_FIELD_REFS: Final[tuple[str, ...]] = ("blind_case_id", "review_kind", "review_prompt_version", "current_input_review_surface", "returned_emlis_surface", "bounded_owned_history_review_surface", "review_questions", "axis_rating_form")
P7_R47_P5_REVIEWER_FACING_FORBIDDEN_FIELD_REFS: Final[tuple[str, ...]] = ("family", "subscription_tier", "expected_result", "eligible", "visible_applied", "gate_result", "case_ref_id", "user_id", "record_id", "db_id", "raw_history_dump", "public_meta", "raw_input", "comment_text", "candidate_body", "surface_body")

# R8/R9 public constant aliases used by the contract tests.
P7_R47_BODY_FREE_DISPOSAL_RECEIPT_FORBIDDEN_FIELD_REFS: Final = P7_R47_DISPOSAL_RECEIPT_FORBIDDEN_FIELD_REFS
P7_R47_DISPOSAL_STATUSES: Final = P7_R47_DISPOSAL_STATUS_REFS
P7_R47_P5_FIRST_FORMAL_MINIMUMS: Final[dict[str, Any]] = {
    "minimum_total_cases": P7_R47_P5_FIRST_FORMAL_REVIEW_MINIMUM_TOTAL_CASES,
    "minimum_per_family": P7_R47_P5_FIRST_FORMAL_REVIEW_MINIMUM_PER_FAMILY,
    "minimum_history_line_eligible_input": P7_R47_P5_MINIMUM_HISTORY_LINE_ELIGIBLE_INPUT_CASES,
    "minimum_owned_history_positive_cases": P7_R47_P5_MINIMUM_OWNED_HISTORY_POSITIVE_CASES,
    "minimum_block_boundary_cases": dict(P7_R47_P5_MINIMUM_BLOCK_BOUNDARY_CASE_COUNTS),
}
P7_R47_P5_HISTORY_SURFACE_MAX_RECORDS: Final = P7_R47_P5_MAX_HISTORY_RECORD_SURFACES
P7_R47_P5_HISTORY_SURFACE_MIN_EVIDENCE_RECORDS: Final = P7_R47_P5_MIN_EVIDENCE_RECORD_COUNT_WHEN_HISTORY_LINE_EXPECTED
P7_R47_R8_R9_DISPOSAL_P5_POLICY_SCHEMA_VERSION: Final = P7_R47_R8_R9_DISPOSAL_P5_PACKET_POLICY_SCHEMA_VERSION
P7_R47_P6_LIMITED_HUMAN_READFEEL_PACKET_POLICY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r47.p6_limited_human_readfeel_packet_policy.v1"
)
P7_R47_REAL_DEVICE_MODAL_REVIEW_PACKET_POLICY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r47.real_device_modal_review_packet_policy.v1"
)
P7_R47_R10_R11_P6_REAL_DEVICE_PACKET_POLICY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r47.r10_r11_p6_real_device_packet_policy.v1"
)
P7_R47_R10_R11_NEXT_REQUIRED_STEP_REF: Final = "R12_r46_next_decision_ledger_connection"
P7_R47_R10_R11_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R47_R8_R9_IMPLEMENTED_STEPS,
    "R10_p6_limited_human_readfeel_packet_policy",
    "R11_real_device_modal_review_packet_policy",
)
P7_R47_R10_R11_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R12_r46_next_decision_ledger_connection",
    "R13_r47_contract_test_policy",
    "R14_target_validation_command_matrix",
    "R15_touch_candidate_and_no_touch_boundary",
)
P7_R47_R46_NEXT_DECISION_LEDGER_CONNECTION_POLICY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r47.r46_next_decision_ledger_connection_policy.v1"
)
P7_R47_CONTRACT_TEST_POLICY_SCHEMA_VERSION: Final = "cocolon.emlis.p7_r47.contract_test_policy.v1"
P7_R47_R12_R13_LEDGER_CONTRACT_TEST_POLICY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r47.r12_r13_ledger_connection_contract_test_policy.v1"
)
P7_R47_R12_R13_NEXT_REQUIRED_STEP_REF: Final = "R14_target_validation_command_matrix"
P7_R47_R12_R13_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R47_R10_R11_IMPLEMENTED_STEPS,
    "R12_r46_next_decision_ledger_connection",
    "R13_r47_contract_test_policy",
)
P7_R47_R12_R13_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R14_target_validation_command_matrix",
    "R15_touch_candidate_and_no_touch_boundary",
)
P7_R47_R12_LEDGER_CONNECTION_KIND: Final = "r47_body_free_policy_summary_for_r46_branch_a"
P7_R47_R12_NEXT_RECOMMENDED_WORK_AFTER_POLICY_REFS: Final[tuple[str, ...]] = (
    "p5_human_blind_qa_material_generation_and_review",
    "p6_limited_human_readfeel_review_after_p5",
    "real_device_submit_modal_readfeel_review",
)
P7_R47_R12_POLICY_READY_SUMMARY_FIELD_REFS: Final[tuple[str, ...]] = (
    "r47_policy_ready",
    "local_review_packet_policy_ready",
    "policy_ready",
    "p5_human_blind_qa_start_allowed_after_policy",
    "p5_human_blind_qa_confirmed",
    "p6_limited_human_readfeel_start_allowed",
    "real_device_modal_review_start_allowed",
    "release_allowed",
    "p7_complete",
    "p8_start_allowed",
    "hold004_close_allowed",
)
P7_R47_R13_REQUIRED_CONTRACT_TEST_REFS: Final[tuple[str, ...]] = (
    "policy_builder_body_free_release_closed",
    "missing_storage_root_denies_body_full_generation",
    "repo_docs_tests_services_mnt_data_roots_rejected",
    "body_free_manifest_rejects_body_and_reviewer_payload_keys",
    "body_free_rating_row_rejects_reviewer_text_comment_text_terminal_output",
    "disposal_receipt_rejects_body_content_hash",
    "p5_policy_matches_r46_families_axes_thresholds",
    "p6_policy_matches_r46_families_no_connect_axes_thresholds",
    "p6_start_blocked_before_p5_human_review_confirmed",
    "real_device_policy_preserves_rn_api_db_public_shape",
    "release_p7_p8_hold004_remain_closed",
    "body_full_local_packet_schema_marked_local_only_and_rejected_as_body_free_p7_material",
)
P7_R47_R13_TARGET_TEST_MODULE_REFS: Final[tuple[str, ...]] = (
    "tests/test_emlis_ai_p7_r47_local_review_packet_policy_r0_r1_20260618.py",
    "tests/test_emlis_ai_p7_r47_local_review_packet_policy_r2_r3_20260618.py",
    "tests/test_emlis_ai_p7_r47_local_review_packet_policy_r4_r5_20260618.py",
    "tests/test_emlis_ai_p7_r47_local_review_packet_policy_r6_r7_20260618.py",
    "tests/test_emlis_ai_p7_r47_local_review_packet_policy_r8_r9_20260618.py",
    "tests/test_emlis_ai_p7_r47_local_review_packet_policy_r10_r11_20260618.py",
    "tests/test_emlis_ai_p7_r47_local_review_packet_policy_r12_r13_20260618.py",
)

P7_R47_TARGET_VALIDATION_COMMAND_MATRIX_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r47.target_validation_command_matrix.v1"
)
P7_R47_TOUCH_NO_TOUCH_BOUNDARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r47.touch_candidate_no_touch_boundary.v1"
)
P7_R47_R14_R15_VALIDATION_TOUCH_BOUNDARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r47.r14_r15_validation_touch_boundary_freeze.v1"
)
P7_R47_R14_R15_NEXT_REQUIRED_STEP_REF: Final = "p5_human_blind_qa_material_generation_and_review"
P7_R47_R14_R15_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R47_R12_R13_IMPLEMENTED_STEPS,
    "R14_target_validation_command_matrix",
    "R15_touch_candidate_and_no_touch_boundary",
)
P7_R47_R14_R15_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = ()
P7_R47_R14_R15_TARGET_TEST_MODULE_REFS: Final[tuple[str, ...]] = (
    *P7_R47_R13_TARGET_TEST_MODULE_REFS,
    "tests/test_emlis_ai_p7_r47_local_review_packet_policy_r14_r15_20260618.py",
)
P7_R47_R14_VALIDATION_COMMAND_IDS: Final[tuple[str, ...]] = (
    "py_compile_r47_policy_module",
    "r47_split_policy_contract_target",
    "r46_handoff_regression_target",
    "display_contract_regression_target",
    "backend_collect_only_hold_visibility_target",
    "rn_contract_optional_no_touch_confirmation",
)
P7_R47_R14_REQUIRED_VALIDATION_COMMAND_IDS: Final[tuple[str, ...]] = (
    "py_compile_r47_policy_module",
    "r47_split_policy_contract_target",
    "r46_handoff_regression_target",
    "display_contract_regression_target",
)
P7_R47_R14_OPTIONAL_VALIDATION_COMMAND_IDS: Final[tuple[str, ...]] = (
    "backend_collect_only_hold_visibility_target",
    "rn_contract_optional_no_touch_confirmation",
)
P7_R47_R14_DESIGN_SINGLE_FILE_TARGET_REF: Final = (
    "tests/test_emlis_ai_p7_r47_local_review_packet_policy_20260618.py"
)
P7_R47_R46_REGRESSION_TEST_MODULE_REFS: Final[tuple[str, ...]] = (
    "tests/test_emlis_ai_p7_r46_p5_p6_human_readfeel_handoff_material_r10_r11_20260617.py",
    "tests/test_emlis_ai_p7_r46_real_device_modal_review_closed_validation_r12_r13_20260617.py",
    "tests/test_emlis_ai_p7_r46_next_decision_handoff_ledger_r14_20260617.py",
)
P7_R47_DISPLAY_CONTRACT_REGRESSION_TEST_MODULE_REFS: Final[tuple[str, ...]] = (
    "tests/test_emlis_ai_display_contract.py",
)
P7_R47_R15_DESIGN_TOUCH_CANDIDATE_FILE_REFS: Final[tuple[str, ...]] = (
    "mashos-api/ai/services/ai_inference/emlis_ai_p7_r47_local_review_packet_policy.py",
    "mashos-api/ai/services/ai_inference/emlis_ai_p7_r47_local_review_packet_manifest.py",
    "mashos-api/ai/tests/test_emlis_ai_p7_r47_local_review_packet_policy_20260618.py",
)
P7_R47_R15_ACTUAL_TOUCH_CANDIDATE_FILE_REFS: Final[tuple[str, ...]] = (
    "mashos-api/ai/services/ai_inference/emlis_ai_p7_r47_local_review_packet_policy.py",
    "mashos-api/ai/tests/test_emlis_ai_p7_r47_local_review_packet_policy_r14_r15_20260618.py",
)
P7_R47_R15_OPTIONAL_TOUCH_CANDIDATE_FILE_REFS: Final[tuple[str, ...]] = (
    "mashos-api/ai/docs/Cocolon_EmlisAI_P7_R47_LocalReviewPacketPolicy_20260618.md",
)
P7_R47_R15_NO_TOUCH_FILE_REFS: Final[tuple[str, ...]] = (
    "Cocolon/screens/InputScreen.js",
    "Cocolon/screens/input/useInputFeedbackModal.js",
    "Cocolon/screens/input/inputFeedbackModel.js",
    "Cocolon/screens/input/InputFeedbackReplyModal.js",
    "Cocolon/tests/rn-screen-contracts.test.js",
    "mashos-api/ai/services/ai_inference/emlis_ai_reply_service.py",
    "mashos-api/ai/services/ai_inference/emlis_ai_public_feedback_meta.py",
    "mashos-api/ai/services/ai_inference/emlis_ai_body_free_public_source_lineage.py",
    "DB schema / migration files",
    "API route files",
    "runtime Gate threshold files",
)
P7_R47_R15_NO_TOUCH_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "rn_production_screens_and_modal_contracts",
    "rn_screen_contract_tests",
    "emlis_reply_runtime",
    "public_feedback_meta_runtime",
    "public_source_lineage_runtime",
    "db_schema_and_migrations",
    "api_routes_request_keys_response_shape",
    "runtime_gate_threshold_files",
    "release_material_and_public_contracts",
)
P7_R47_R15_ALLOWED_TEST_PATH_PATTERNS: Final[tuple[str, ...]] = (
    "mashos-api/ai/tests/test_emlis_ai_p7_r47_local_review_packet_policy*.py",
)
P7_R47_P6_REVIEW_KIND: Final = "p6_structure_insight_limited_readfeel"
P7_R47_P6_FIRST_FORMAL_REVIEW_MINIMUM_TOTAL_CASES: Final = 18
P7_R47_P6_MINIMUM_REVIEW_FAMILY_CASE_COUNTS: Final[dict[str, int]] = {
    "structure_question": 4,
    "long_meaning_arc": 4,
    "self_understanding_follow": 4,
}
P7_R47_P6_MINIMUM_NO_CONNECT_AUDIT_CASE_COUNTS: Final[dict[str, int]] = {
    "daily_unpleasant": 1,
    "daily_positive": 1,
    "positive_only": 1,
    "low_information": 1,
    "limited_grounding_insufficient": 1,
    "safety_triage_required": 1,
}
P7_R47_P6_FIRST_FORMAL_MINIMUMS: Final[dict[str, Any]] = {
    "minimum_total_cases": P7_R47_P6_FIRST_FORMAL_REVIEW_MINIMUM_TOTAL_CASES,
    "minimum_review_family_cases": dict(P7_R47_P6_MINIMUM_REVIEW_FAMILY_CASE_COUNTS),
    "minimum_no_connect_audit_cases": dict(P7_R47_P6_MINIMUM_NO_CONNECT_AUDIT_CASE_COUNTS),
}
P7_R47_P6_REVIEWER_FACING_ALLOWED_FIELD_REFS: Final[tuple[str, ...]] = (
    "blind_case_id",
    "review_kind",
    "review_prompt_version",
    "current_input_review_surface",
    "returned_emlis_surface",
    "structure_insight_review_surface_or_position",
    "review_questions",
    "axis_rating_form",
)
P7_R47_P6_REVIEWER_FACING_FORBIDDEN_FIELD_REFS: Final[tuple[str, ...]] = (
    "family",
    "subscription_tier",
    "expected_result",
    "eligible",
    "visible_applied",
    "gate_result",
    "case_ref_id",
    "relation_pattern_internal_id",
    "diagnostic_label",
    "candidate_internal_body",
    "public_meta",
    "raw_input",
    "comment_text",
    "candidate_body",
    "surface_body",
    "history_used_as_fact",
)
P7_R47_REAL_DEVICE_REVIEW_KIND: Final = "real_device_submit_modal_readfeel"
P7_R47_REAL_DEVICE_REQUIRED_MANUAL_REVIEW_FAMILY_REFS: Final[tuple[str, ...]] = (
    "free_standard_state_answer_no_history_line",
    "plus_history_line_eligible",
    "plus_history_line_blocked_low_information",
    "p6_structure_question_visible",
    "p6_daily_positive_no_connect",
)
P7_R47_REAL_DEVICE_REQUIRED_MANUAL_REVIEW_FAMILIES: Final = P7_R47_REAL_DEVICE_REQUIRED_MANUAL_REVIEW_FAMILY_REFS
P7_R47_REAL_DEVICE_READFEEL_AXIS_REFS: Final[tuple[str, ...]] = (
    "readable_on_phone",
    "length_pressure_absence",
    "weight_absence",
    "shallow_absence",
    "p5_history_line_creepy_absence",
    "p6_overread_absence",
    "wants_more_input",
)
P7_R47_REAL_DEVICE_RECOMMENDED_DEVICE_CONTEXT_REFS: Final[tuple[str, ...]] = (
    "small_phone",
    "medium_phone",
)
P7_R47_REAL_DEVICE_FIRST_REVIEW_MINIMUMS: Final[dict[str, Any]] = {
    "minimum_device_contexts": 1,
    "recommended_device_contexts": list(P7_R47_REAL_DEVICE_RECOMMENDED_DEVICE_CONTEXT_REFS),
    "minimum_case_per_required_family_per_device": 1,
    "minimum_total_cases_first_review": 5,
}
P7_R47_REAL_DEVICE_REVIEWER_FACING_ALLOWED_FIELD_REFS: Final[tuple[str, ...]] = (
    "blind_case_id",
    "review_kind",
    "review_prompt_version",
    "device_ref",
    "os_ref",
    "app_build_ref",
    "visible_modal_review_surface",
    "modal_layout_review_note",
    "readfeel_questions",
    "axis_rating_form",
)
P7_R47_REAL_DEVICE_REVIEWER_FACING_FORBIDDEN_FIELD_REFS: Final[tuple[str, ...]] = (
    "family",
    "expected_result",
    "eligible",
    "visible_applied",
    "gate_result",
    "case_ref_id",
    "user_id",
    "record_id",
    "db_id",
    "public_meta",
    "raw_input",
    "comment_text",
    "candidate_body",
    "surface_body",
    "screenshot_body",
    "visible_text_body",
    "reviewer_free_text",
    "terminal_output",
)
P7_R47_REVIEW_VERDICTS: Final[tuple[str, ...]] = (
    "PASS",
    "YELLOW",
    "REPAIR_REQUIRED",
    "RED",
    "BLOCKED",
    "NOT_REVIEWABLE",
)
P7_R47_BLOCKER_KINDS: Final[tuple[str, ...]] = (
    "READFEEL_RED",
    "REPAIR_REQUIRED",
    "EXECUTION_BLOCKER",
    "NOT_REVIEWABLE",
    "POLICY_BLOCKER",
)
P7_R47_BLOCKER_STATUSES: Final[tuple[str, ...]] = (
    "OPEN",
    "TRIAGED",
    "REPAIRED",
    "WAIVED_WITH_REASON",
    "CLOSED",
)
P7_R47_BODY_FREE_RATING_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "packet_ref_id",
    "blind_case_id",
    "case_ref_id",
    "packet_kind",
    "family",
    "subscription_tier",
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
P7_R47_BODY_FREE_BLOCKER_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "packet_ref_id",
    "blind_case_id",
    "case_ref_id",
    "packet_kind",
    "family",
    "subscription_tier",
    "blocker_id",
    "blocker_kind",
    "blocker_status",
    "sanitized_reason_ids",
    "reviewer_free_text_included",
    "body_removed",
    "body_free",
)
P7_R47_BODY_FREE_RATING_BLOCKER_FORBIDDEN_FIELD_REFS: Final[tuple[str, ...]] = (
    "raw_input",
    "current_input",
    "memo",
    "memo_action",
    "history_raw_text",
    "comment_text",
    "comment_text_body",
    "candidate_body",
    "surface_body",
    "insight_text",
    "review_surface",
    "visible_surface",
    "surface_for_reviewer",
    "current_input_for_reviewer",
    "history_summary_for_reviewer",
    "reviewer_free_text",
    "reviewer_note",
    "reviewer_notes",
    "terminal_output",
    "stdout",
    "stderr",
    "traceback",
    "comment_body",
    "reply_text",
    "visible_text",
    "display_text",
    "observation_text",
    "reception_text",
    "deleted_body_preview",
    "body_content_hash",
    "raw_text_hash",
    "comment_text_hash",
)
P7_R47_SANITIZED_REASON_ID_REFS: Final[tuple[str, ...]] = (
    "p5_history_connection_too_generic",
    "p5_history_scope_overclaim",
    "p5_history_creepy_or_surveillance_feeling",
    "p5_history_line_self_blame_amplification",
    "p5_history_line_shallow_repeat",
    "p5_history_line_wants_more_input_low",
    "p5_free_tier_history_boundary_violation",
    "p5_low_information_history_overread",
    "p5_review_not_enough_context",
    "p5_review_execution_blocked",
    "p6_structure_insight_mirror_only",
    "p6_relation_seen_feeling_low",
    "p6_structure_overclaim",
    "p6_diagnostic_or_personality_claim",
    "p6_advice_pressure",
    "p6_creepy_overread",
    "p6_no_connect_family_insight_leak",
    "p6_history_used_as_fact",
    "p6_wants_more_input_low",
    "p6_review_execution_blocked",
    "modal_length_pressure_small_phone",
    "modal_line_break_readability_low",
    "modal_weight_too_heavy",
    "modal_title_or_source_contract_mismatch",
    "modal_non_passed_visible_violation",
    "modal_p5_history_line_creepy_on_phone",
    "modal_p6_overread_on_phone",
    "modal_wants_more_input_low",
    "modal_review_execution_blocked",
    "reason_id_other_local_note_purged",
)
P7_R47_EXECUTION_BLOCKER_ID_REFS: Final[tuple[str, ...]] = (
    "review_packet_generation_blocked_missing_local_root",
    "review_packet_generation_blocked_invalid_local_root",
    "review_case_material_missing",
    "review_timeout_unclassified",
    "reviewer_not_assigned",
    "rating_row_incomplete",
    "body_purge_failed",
    "body_purge_not_verified",
    "full_backend_suite_not_run",
    "real_device_context_not_set",
)

P7_R47_BODY_FULL_PACKET_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "local_only",
    "must_not_export",
    "packet_kind",
    "review_session_id",
    "packet_ref_id",
    "blind_case_id",
    "reviewer_payload",
    "review_form",
    "disposal_required",
)
P7_R47_BODY_FULL_REVIEWER_PAYLOAD_FIELD_REFS: Final[tuple[str, ...]] = (
    "current_input_review_surface",
    "returned_emlis_review_surface",
    "bounded_history_review_surface",
    "structure_insight_review_surface",
    "modal_layout_review_note",
)
P7_R47_BODY_FULL_REVIEW_FORM_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "rating_axes",
    "free_text_allowed_local_only",
)
P7_R47_REVIEWER_FACING_FORBIDDEN_FIELD_REFS: Final[tuple[str, ...]] = (
    "family",
    "subscription_tier",
    "expected_result",
    "eligible",
    "visible_applied",
    "gate_result",
    "case_ref_id",
    "user_id",
    "record_id",
    "db_id",
    "raw_history_dump",
    "public_meta",
    "raw_input",
    "comment_text",
    "candidate_body",
    "surface_body",
)
P7_R47_BODY_FREE_MANIFEST_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "manifest_kind",
    "review_session_id",
    "packet_kind",
    "case_refs",
    "local_body_packet_materialized_here",
    "body_full_packet_export_allowed",
    "body_free",
    "release_allowed",
    "p7_complete",
    "p8_start_allowed",
)
P7_R47_BODY_FREE_MANIFEST_CASE_REF_FIELD_REFS: Final[tuple[str, ...]] = (
    "blind_case_id",
    "case_ref_id",
    "family",
    "subscription_tier",
    "packet_ref_id",
    "body_free",
)
P7_R47_BODY_FREE_MANIFEST_FORBIDDEN_FIELD_REFS: Final[tuple[str, ...]] = (
    "raw_input",
    "current_input",
    "memo",
    "memo_action",
    "history_raw_text",
    "comment_text",
    "comment_text_body",
    "candidate_body",
    "surface_body",
    "insight_text",
    "review_surface",
    "visible_surface",
    "surface_for_reviewer",
    "current_input_for_reviewer",
    "history_summary_for_reviewer",
    "reviewer_free_text",
    "reviewer_note",
    "reviewer_notes",
    "terminal_output",
    "stdout",
    "stderr",
    "traceback",
)
P7_R47_EXPORT_DENYLIST_PATTERNS: Final[tuple[str, ...]] = (
    ".local_review_packets/",
    "body_full_packets.local_only/",
    "reviewer_notes.local_only/",
    "*.local_review_packet.json",
    "*.reviewer_notes.json",
    "*.local_only.json",
    "Cocolon_EmlisAI_*_LocalReviewPacket_*_body_full*",
)
P7_R47_STORAGE_ROOT_FORBIDDEN_NAME_FRAGMENTS: Final[tuple[str, ...]] = (
    "Cocolon_前提資料",
    "Cocolon_#U524d#U63d0#U8cc7#U6599",
    "EmlisAIの実装済み資料",
    "release",
    "public_meta",
)
P7_R47_STORAGE_ROOT_FORBIDDEN_COMPONENTS: Final[tuple[str, ...]] = (
    ".git",
    "docs",
    "tests",
    "services",
)
P7_R47_PACKET_KINDS: Final[tuple[str, ...]] = (
    "p5_human_blind_qa_local_review_packet",
    "p6_limited_human_readfeel_local_review_packet",
    "real_device_modal_review_local_packet",
)
P7_R47_PACKET_KIND_SET: Final[frozenset[str]] = frozenset(P7_R47_PACKET_KINDS)
P7_R47_REQUIRED_UNRESOLVED_HOLD_REFS: Final[tuple[str, ...]] = (
    P5_HUMAN_BLIND_QA_HOLD_REF,
    P5_HUMAN_BLIND_QA_RETURN_HOLD_REF,
    P6_LIMITED_HUMAN_READFEEL_HOLD_REF,
    P6_LIMITED_HUMAN_READFEEL_RETURN_HOLD_REF,
    P7_HOLD_REAL_DEVICE_MODAL_REF,
    P7_RETURN_REAL_DEVICE_HOLD_REF,
    P7_HOLD_FULL_BACKEND_SUITE_REF,
    HOLD_DC_FULL_BACKEND_SUITE_REF,
)
P7_R47_RECEIVED_LOCAL_SNAPSHOT_REFS: Final[dict[str, str]] = {
    "premise_zip_ref": "Cocolon_前提資料(232).zip",
    "implemented_materials_zip_ref": "EmlisAIの実装済み資料(68).zip",
    "rn_zip_ref": "Cocolon(241).zip",
    "backend_zip_ref": "mashos-api(154).zip",
    "roadmap_ref": "Cocolon_EmlisAI_longterm_roadmap_20260608(20).md",
    "detailed_design_ref": "Cocolon_EmlisAI_P7_R47_LocalReviewPacketPolicy_DetailedDesign_ImplementationOrder_20260618.md",
}

_LOCAL_REVIEW_BODY_KEYS: Final[frozenset[str]] = frozenset(
    {
        "review_surface",
        "returned_surface",
        "visible_surface",
        "surface_for_reviewer",
        "comment_text_for_reviewer",
        "current_input_for_reviewer",
        "history_summary_for_reviewer",
        "bounded_history_review_surface",
        "structure_insight_review_surface",
        "modal_layout_review_note",
        "visible_modal_review_surface",
        "visible_modal_text",
        "modal_visible_text",
        "screenshot",
        "screenshot_body",
        "screenshot_image_body",
        "visible_text_body",
        "visible_modal_text_body",
        "screen_capture_body",
        "image_body",
        "reviewer_free_text",
        "reviewer_note",
        "reviewer_notes",
        "manual_note",
        "manual_notes",
        "terminal_output",
        "stdout",
        "stderr",
        "traceback",
        "body_content_hash",
        "body_full_file_content_hash",
        "raw_text_hash",
        "comment_text_hash",
        "local_absolute_path",
    }
)
_RELEASE_CLOSED_KEYS: Final[tuple[str, ...]] = (
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
_R0_R1_FALSE_KEYS: Final[tuple[str, ...]] = (
    "local_review_packet_policy_ready",
    "policy_ready",
    "r47_policy_ready",
    "local_review_packet_storage_policy_fixed",
    "local_body_packet_generation_allowed",
    "actual_body_full_packet_generated_here",
    "body_full_writer_created_here",
    "body_full_packet_schema_created_here",
    "body_free_manifest_schema_created_here",
    "rating_row_schema_created_here",
    "disposal_policy_created_here",
    "p5_human_blind_qa_start_allowed_after_r0_r1",
    "p5_human_blind_qa_confirmed",
    "p6_limited_human_readfeel_start_allowed",
    "p6_limited_human_readfeel_confirmed",
    "real_device_modal_review_start_allowed",
    "real_device_modal_review_confirmed",
    "actual_human_review_run_here",
    "actual_real_device_review_run_here",
    "local_reviewer_payload_materialized_here",
)


def _contains_local_review_body_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(
            str(key) in _LOCAL_REVIEW_BODY_KEYS or _contains_local_review_body_key(child)
            for key, child in value.items()
        )
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_local_review_body_key(child) for child in value)
    return False


def _assert_r47_body_free(value: Any, *, source: str) -> None:
    if _contains_local_review_body_key(value):
        raise ValueError(f"{source} contains local-only review body payload keys")
    assert_p7_no_body_payload_or_contract_mutation(value, source=source)


def _body_free_markers() -> dict[str, bool]:
    return body_free_flags(include_history=True, include_reviewer=True, include_terminal=True)


def _release_closed_flags() -> dict[str, bool]:
    return {key: False for key in _RELEASE_CLOSED_KEYS}


def _r0_r1_false_flags() -> dict[str, bool]:
    return {key: False for key in _R0_R1_FALSE_KEYS}


def _safe_snapshot_refs(snapshot_refs: Mapping[str, Any] | None) -> dict[str, str]:
    merged: dict[str, str] = dict(P7_R47_RECEIVED_LOCAL_SNAPSHOT_REFS)
    if snapshot_refs is None:
        return merged
    _assert_r47_body_free(snapshot_refs, source="p7_r47.snapshot_refs")
    for key, value in safe_mapping(snapshot_refs).items():
        clean_key = clean_identifier(key, default="snapshot_ref", max_length=120)
        if clean_key:
            merged[clean_key] = clean_identifier(value, default="unknown", max_length=180)
    return merged


def _module_repo_root() -> str:
    # services/ai_inference/<this file> -> services -> ai -> mashos-api
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def _normalize_local_path(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    text = str(value).strip()
    if not text:
        return ""
    return os.path.normpath(os.path.expanduser(text))


def _safe_root_source(local_review_root: Any) -> tuple[str, str]:
    explicit_root = _normalize_local_path(local_review_root)
    if explicit_root:
        return explicit_root, "provided_argument"
    env_root = _normalize_local_path(os.environ.get(P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR))
    if env_root:
        return env_root, "environment"
    return "", "missing"


def _is_equal_or_under(path: str, parent: str) -> bool:
    if not path or not parent:
        return False
    try:
        path_abs = os.path.abspath(path)
        parent_abs = os.path.abspath(parent)
        return os.path.commonpath([path_abs, parent_abs]) == parent_abs
    except ValueError:
        return False


def _path_components(path: str) -> tuple[str, ...]:
    return tuple(part for part in os.path.normpath(path).replace("\\", "/").split("/") if part)


def _local_root_rejection_reasons(
    root_path: str,
    *,
    repo_roots: Sequence[Any] | None,
    export_roots: Sequence[Any] | None,
) -> list[str]:
    if not root_path:
        return ["local_review_root_not_configured"]
    reasons: list[str] = []
    if not os.path.isabs(root_path):
        reasons.append("local_review_root_not_absolute")

    normalized = os.path.abspath(root_path) if os.path.isabs(root_path) else root_path
    lower_normalized = normalized.lower()
    repo_root_values = [_module_repo_root(), *dedupe_identifiers(repo_roots, limit=20, max_length=260)]
    export_root_values = dedupe_identifiers(export_roots, limit=20, max_length=260)

    if any(_is_equal_or_under(normalized, repo_root) for repo_root in repo_root_values):
        reasons.append("local_review_root_under_repo_root")
    if any(_is_equal_or_under(normalized, export_root) for export_root in export_root_values):
        reasons.append("local_review_root_under_export_root")
    if _is_equal_or_under(normalized, "/mnt/data"):
        reasons.append("local_review_root_under_mnt_data_artifact_root")

    components = {part.lower() for part in _path_components(normalized)}
    forbidden_components = {part.lower() for part in P7_R47_STORAGE_ROOT_FORBIDDEN_COMPONENTS}
    if components & forbidden_components:
        reasons.append("local_review_root_contains_repo_or_git_component")
    if any(fragment.lower() in lower_normalized for fragment in P7_R47_STORAGE_ROOT_FORBIDDEN_NAME_FRAGMENTS):
        reasons.append("local_review_root_contains_forbidden_name_fragment")

    return dedupe_identifiers(reasons, limit=20, max_length=120)


def p7_r47_export_candidate_deny_reasons(candidate_ref: Any) -> tuple[str, ...]:
    """Return deny reasons for a candidate export ref without exposing local paths."""

    text = clean_identifier(candidate_ref, default="", max_length=260).replace("\\", "/")
    lower = text.lower()
    reasons: list[str] = []
    for pattern in P7_R47_EXPORT_DENYLIST_PATTERNS:
        normalized_pattern = pattern.replace("\\", "/")
        if fnmatch.fnmatch(lower, normalized_pattern.lower()) or normalized_pattern.rstrip("/").lower() in lower:
            reasons.append("r47_export_denylist_pattern_match")
            break
    if ".git" in lower:
        reasons.append("r47_git_tracked_or_git_metadata_path")
    if lower.endswith(".zip") and ("localreviewpacket" in lower or "local_review_packet" in lower or "body_full" in lower):
        reasons.append("r47_body_full_packet_zip_inclusion_blocked")
    if "cocolon_前提資料" in lower or "emlisaiの実装済み資料" in lower:
        reasons.append("r47_premise_or_implemented_docs_zip_inclusion_blocked")
    return tuple(dedupe_identifiers(reasons, limit=10, max_length=120))


def _r46_ledger(r46_next_decision_ledger: Mapping[str, Any] | None) -> dict[str, Any]:
    ledger = (
        safe_mapping(r46_next_decision_ledger)
        if r46_next_decision_ledger is not None
        else build_p7_r46_next_decision_handoff_ledger()
    )
    assert_p7_r46_next_decision_handoff_ledger_contract(ledger)
    if r46_next_decision_ledger is not None:
        _assert_r47_body_free(ledger, source="p7_r47.r46_next_decision_ledger")
    return ledger


def _r46_handoff_freeze(ledger: Mapping[str, Any]) -> dict[str, Any]:
    summary = safe_mapping(ledger.get("next_decision_summary"))
    display = safe_mapping(summary.get("display_decision_status"))
    p5 = safe_mapping(summary.get("p5_return_status"))
    p6 = safe_mapping(summary.get("p6_return_status"))
    real_device = safe_mapping(summary.get("real_device_modal_status"))
    next_refs = dedupe_identifiers(summary.get("next_recommended_work_refs"), limit=20, max_length=160)
    if not next_refs:
        raise ValueError("R47 R0 requires R46 summary next_recommended_work_refs")
    active_branch = clean_identifier(summary.get("active_decision_branch"), default="unknown", max_length=140)
    if active_branch != BRANCH_A_DISPLAY_GREEN_LINEAGE_CONSISTENT:
        raise ValueError("R47 R0 requires R46 branch A before local review packet policy work")
    if next_refs[0] != P7_R47_FIRST_NEXT_WORK_REF:
        raise ValueError("R47 R0 requires local review packet policy to be first in the R46 next order")
    return {
        "r46_ledger_schema_version": clean_identifier(
            ledger.get("schema_version"), default=P7_R46_NEXT_DECISION_HANDOFF_LEDGER_SCHEMA_VERSION, max_length=160
        ),
        "r46_ledger_step": P7_R46_NEXT_DECISION_HANDOFF_LEDGER_STEP,
        "active_decision_branch": active_branch,
        "branch_code": active_branch,
        "next_order_first": next_refs[0],
        "next_recommended_work_refs": next_refs,
        "display_contract_green_confirmed": display.get("display_contract_green") is True,
        "public_lineage_consistency_confirmed": display.get("public_lineage_consistency_passed") is True,
        "public_meta_body_free_confirmed": display.get("public_meta_body_free_confirmed") is True,
        "p5_human_blind_qa_path_open_from_r46": ledger.get("p5_human_blind_qa_start_allowed") is True,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_path_open_from_r46": ledger.get("p6_limited_human_readfeel_start_allowed") is True,
        "p6_waits_for_p5_confirmation": p6.get("ready_after_p5_human_blind_qa") is True,
        "p6_limited_human_readfeel_confirmed": False,
        "real_device_modal_review_path_open_from_r46": ledger.get("real_device_modal_review_start_allowed") is True,
        "real_device_modal_review_confirmed": real_device.get("modal_review_confirmed") is True,
        "human_review_confirmed": False,
        "manual_real_device_review_confirmed": False,
        "release_allowed": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "hold004_close_allowed": False,
        "body_free": True,
    }


def _hold_state(ledger: Mapping[str, Any]) -> dict[str, Any]:
    unresolved = dedupe_identifiers(
        [
            *dedupe_identifiers(ledger.get("unresolved_hold_refs"), limit=100, max_length=120),
            *P7_R47_REQUIRED_UNRESOLVED_HOLD_REFS,
        ],
        limit=120,
        max_length=120,
    )
    return {
        "unresolved_hold_refs": unresolved,
        "required_unresolved_hold_refs": list(P7_R47_REQUIRED_UNRESOLVED_HOLD_REFS),
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "real_device_modal_review_confirmed": False,
        "full_backend_suite_green_confirmed": False,
        "local_review_packet_policy_ready": False,
        "body_full_review_packet_generated": False,
        "body_free_rating_rows_ready": False,
        "body_removed_verified": False,
        "release_allowed": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "hold004_close_allowed": False,
        "body_free": True,
    }


def build_p7_r47_current_source_r46_handoff_hold_refreeze(
    *,
    snapshot_refs: Mapping[str, Any] | None = None,
    r46_next_decision_ledger: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r47_current_source_r46_handoff_hold_refreeze",
) -> dict[str, Any]:
    """Build the R0 body-free current-source/R46-handoff/HOLD refreeze."""

    ledger = _r46_ledger(r46_next_decision_ledger)
    refreeze = {
        "schema_version": P7_R47_CURRENT_SOURCE_REFREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R47_LOCAL_REVIEW_PACKET_STEP,
        "scope": P7_R47_LOCAL_REVIEW_PACKET_SCOPE,
        "policy_kind": P7_R47_POLICY_KIND,
        "material_id": clean_identifier(material_id, default="p7_r47_current_source_r46_handoff_hold_refreeze", max_length=160),
        "freeze_kind": "current_source_r46_handoff_hold_refreeze",
        "current_phase": "P7",
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": P7_GIT_CHECKED,
        "source_snapshot_refs": _safe_snapshot_refs(snapshot_refs),
        "r46_handoff": _r46_handoff_freeze(ledger),
        "hold_state": _hold_state(ledger),
        "blocked_actions": list(P7_R47_BLOCKED_ACTIONS),
        "next_required_step": "R1_scope_schema_version_packet_kind_enum_freeze",
        "r0_current_source_handoff_hold_refrozen": True,
        "r1_scope_packet_kind_enum_fixed": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
        **_r0_r1_false_flags(),
    }
    assert_p7_r47_current_source_r46_handoff_hold_refreeze_contract(refreeze)
    return refreeze


def _safe_packet_kinds(packet_kinds: Sequence[Any] | None) -> list[str]:
    values = dedupe_identifiers(packet_kinds if packet_kinds is not None else P7_R47_PACKET_KINDS, limit=10, max_length=120)
    if tuple(values) != P7_R47_PACKET_KINDS or frozenset(values) != P7_R47_PACKET_KIND_SET:
        raise ValueError("R47 R1 packet kind enum must remain exactly fixed")
    return values


def _packet_kind_policies(packet_kinds: Sequence[str]) -> list[dict[str, Any]]:
    review_kinds = {
        "p5_human_blind_qa_local_review_packet": "p5_history_line_readfeel",
        "p6_limited_human_readfeel_local_review_packet": "p6_structure_insight_limited_readfeel",
        "real_device_modal_review_local_packet": "real_device_submit_modal_readfeel",
    }
    return [
        {
            "packet_kind": packet_kind,
            "review_kind": review_kinds[packet_kind],
            "local_only_required_later": True,
            "body_full_payload_required_later": True,
            "materialized_here": False,
            "writer_created_here": False,
            "standard_export_allowed": False,
            "public_meta_material_allowed": False,
            "p7_scorecard_material_allowed": False,
            "release_material_allowed": False,
            "body_free_result_required_later": True,
            "body_free": True,
        }
        for packet_kind in packet_kinds
    ]


def build_p7_r47_scope_schema_packet_kind_freeze(
    *,
    packet_kinds: Sequence[Any] | None = None,
    current_source_refreeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r47_scope_schema_packet_kind_freeze",
) -> dict[str, Any]:
    """Build the R1 body-free R47 scope/schema-version/packet-kind freeze."""

    r0 = (
        safe_mapping(current_source_refreeze)
        if current_source_refreeze is not None
        else build_p7_r47_current_source_r46_handoff_hold_refreeze()
    )
    assert_p7_r47_current_source_r46_handoff_hold_refreeze_contract(r0)
    if current_source_refreeze is not None:
        _assert_r47_body_free(r0, source="p7_r47.current_source_refreeze")

    kinds = _safe_packet_kinds(packet_kinds)
    freeze = {
        "schema_version": P7_R47_SCOPE_SCHEMA_PACKET_KIND_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R47_LOCAL_REVIEW_PACKET_STEP,
        "scope": P7_R47_LOCAL_REVIEW_PACKET_SCOPE,
        "policy_kind": P7_R47_POLICY_KIND,
        "material_id": clean_identifier(material_id, default="p7_r47_scope_schema_packet_kind_freeze", max_length=160),
        "freeze_kind": "scope_schema_version_packet_kind_enum_freeze",
        "current_phase": "P7",
        "source_mode": clean_identifier(r0.get("source_mode"), default=P7_SOURCE_MODE, max_length=80),
        "git_connection_required": False,
        "git_checked": False,
        "policy_schema_version": P7_R47_LOCAL_REVIEW_PACKET_POLICY_SCHEMA_VERSION,
        "r0_schema_version": P7_R47_CURRENT_SOURCE_REFREEZE_SCHEMA_VERSION,
        "r0_material_ref": clean_identifier(r0.get("material_id"), default="p7_r47_current_source_r46_handoff_hold_refreeze", max_length=160),
        "r46_branch_code": safe_mapping(r0.get("r46_handoff")).get("active_decision_branch"),
        "r47_scope_fixed": True,
        "r47_schema_version_fixed": True,
        "packet_kind_enum_fixed": True,
        "packet_kind_enum": kinds,
        "packet_kind_count": len(kinds),
        "packet_kind_policies": _packet_kind_policies(kinds),
        "first_next_work_ref": P7_R47_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R47_NEXT_REQUIRED_STEP_REF,
        "r0_current_source_handoff_hold_refrozen": True,
        "r1_scope_packet_kind_enum_fixed": True,
        "implemented_steps": list(P7_R47_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R47_NOT_YET_IMPLEMENTED_STEPS),
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
        **_r0_r1_false_flags(),
    }
    assert_p7_r47_scope_schema_packet_kind_freeze_contract(freeze)
    return freeze


def build_p7_r47_r0_r1_scope_freeze(
    *,
    snapshot_refs: Mapping[str, Any] | None = None,
    r46_next_decision_ledger: Mapping[str, Any] | None = None,
    packet_kinds: Sequence[Any] | None = None,
    material_id: Any = "p7_r47_r0_r1_scope_freeze",
) -> dict[str, Any]:
    """Build a compact body-free combined R0/R1 summary."""

    r0 = build_p7_r47_current_source_r46_handoff_hold_refreeze(
        snapshot_refs=snapshot_refs,
        r46_next_decision_ledger=r46_next_decision_ledger,
    )
    r1 = build_p7_r47_scope_schema_packet_kind_freeze(packet_kinds=packet_kinds, current_source_refreeze=r0)
    combined = {
        "schema_version": P7_R47_R0_R1_SCOPE_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R47_LOCAL_REVIEW_PACKET_STEP,
        "scope": P7_R47_LOCAL_REVIEW_PACKET_SCOPE,
        "policy_kind": P7_R47_POLICY_KIND,
        "material_id": clean_identifier(material_id, default="p7_r47_r0_r1_scope_freeze", max_length=160),
        "freeze_kind": "r0_r1_scope_freeze",
        "current_phase": "P7",
        "implemented_steps": list(P7_R47_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R47_NOT_YET_IMPLEMENTED_STEPS),
        "r0_current_source_refreeze": r0,
        "r1_scope_schema_packet_kind_freeze": r1,
        "first_next_work_ref": P7_R47_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R47_NEXT_REQUIRED_STEP_REF,
        "packet_kind_enum": list(P7_R47_PACKET_KINDS),
        "r0_current_source_handoff_hold_refrozen": True,
        "r1_scope_packet_kind_enum_fixed": True,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
        **_r0_r1_false_flags(),
    }
    assert_p7_r47_r0_r1_scope_freeze_contract(combined)
    return combined



def build_p7_r47_local_review_storage_root_policy(
    *,
    local_review_root: Any = None,
    repo_roots: Sequence[Any] | None = None,
    export_roots: Sequence[Any] | None = None,
    material_id: Any = "p7_r47_local_review_storage_root_policy",
) -> dict[str, Any]:
    """Build the R2 body-free local-only storage root policy."""

    root_path, root_source = _safe_root_source(local_review_root)
    reasons = _local_root_rejection_reasons(root_path, repo_roots=repo_roots, export_roots=export_roots)
    root_configured = bool(root_path)
    root_valid = root_configured and not reasons
    policy = {
        "schema_version": P7_R47_LOCAL_REVIEW_STORAGE_ROOT_POLICY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R47_LOCAL_REVIEW_PACKET_STEP,
        "scope": P7_R47_LOCAL_REVIEW_PACKET_SCOPE,
        "policy_kind": P7_R47_POLICY_KIND,
        "policy_section": "R2_local_only_storage_root_policy",
        "material_id": clean_identifier(material_id, default="p7_r47_local_review_storage_root_policy", max_length=160),
        "current_phase": "P7",
        "storage_mode": P7_R47_STORAGE_MODE_EXTERNAL_LOCAL_ONLY,
        "env_var": P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR,
        "local_review_root_source": root_source,
        "local_review_root_configured": root_configured,
        "local_review_root_status": "valid" if root_valid else ("missing" if not root_configured else "invalid"),
        "storage_root_ref": P7_R47_STORAGE_ROOT_REF if root_valid else "not_configured_or_invalid",
        "root_path_exposed": False,
        "local_absolute_path_included": False,
        "root_is_absolute": bool(root_path and os.path.isabs(root_path)),
        "repo_local_storage_allowed": False,
        "artifact_export_path_allowed": False,
        "docs_tests_services_storage_allowed": False,
        "premise_storage_allowed": False,
        "implemented_docs_storage_allowed": False,
        "mnt_data_artifact_storage_allowed": False,
        "git_tracked_path_storage_allowed": False,
        "body_full_generation_requires_env_root": True,
        "local_body_packet_generation_allowed": root_valid,
        "generation_block_reason_ids": [] if root_valid else reasons,
        "recommended_layout_refs": [
            "p7_r47/{review_session_id}/controller_manifest.bodyfree.json",
            "p7_r47/{review_session_id}/body_full_packets.local_only/{blind_case_id}.local_review_packet.json",
            "p7_r47/{review_session_id}/reviewer_notes.local_only/{blind_case_id}.reviewer_notes.json",
            "p7_r47/{review_session_id}/body_free_results/rating_rows.bodyfree.jsonl",
            "p7_r47/{review_session_id}/body_free_results/blocker_rows.bodyfree.jsonl",
            "p7_r47/{review_session_id}/body_free_results/disposal_receipt.bodyfree.json",
            "p7_r47/{review_session_id}/audit.bodyfree/export_denylist_check.bodyfree.json",
        ],
        "body_full_packets_local_only_dir_ref": "body_full_packets.local_only",
        "reviewer_notes_local_only_dir_ref": "reviewer_notes.local_only",
        "body_free_results_dir_ref": "body_free_results",
        "audit_bodyfree_dir_ref": "audit.bodyfree",
        "p5_human_blind_qa_start_allowed_after_r2": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "real_device_modal_review_start_allowed": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
    }
    assert_p7_r47_local_review_storage_root_policy_contract(policy)
    return policy


def build_p7_r47_export_denylist_policy(
    *,
    material_id: Any = "p7_r47_export_denylist_git_zip_policy",
) -> dict[str, Any]:
    """Build the R3 body-free export denylist/Git-zip mixing prevention policy."""

    policy = {
        "schema_version": P7_R47_EXPORT_DENYLIST_POLICY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R47_LOCAL_REVIEW_PACKET_STEP,
        "scope": P7_R47_LOCAL_REVIEW_PACKET_SCOPE,
        "policy_kind": P7_R47_POLICY_KIND,
        "policy_section": "R3_export_denylist_git_zip_mixing_prevention",
        "material_id": clean_identifier(material_id, default="p7_r47_export_denylist_git_zip_policy", max_length=160),
        "current_phase": "P7",
        "git_zip_mixing_prevention_policy_fixed": True,
        "export_denylist_patterns": list(P7_R47_EXPORT_DENYLIST_PATTERNS),
        "body_full_packet_export_allowed": False,
        "body_full_packet_git_tracking_allowed": False,
        "body_full_packet_zip_inclusion_allowed": False,
        "reviewer_notes_export_allowed": False,
        "release_material_body_full_allowed": False,
        "premise_zip_inclusion_allowed": False,
        "implemented_docs_zip_inclusion_allowed": False,
        "standard_patch_zip_body_full_inclusion_allowed": False,
        "public_meta_body_full_material_allowed": False,
        "p7_scorecard_body_full_material_allowed": False,
        "handoff_ledger_body_full_material_allowed": False,
        "body_free_summary_export_allowed": True,
        "body_free_rating_rows_export_allowed_later": True,
        "body_free_disposal_receipt_export_allowed_later": True,
        "allowed_export_material_refs": [
            "body_free_summary",
            "body_free_rating_rows_later",
            "body_free_blocker_rows_later",
            "body_free_disposal_receipt_later",
        ],
        "denied_export_material_refs": [
            "body_full_local_review_packet",
            "reviewer_notes_local_only",
            "local_only_json",
            "local_review_packet_zip",
            "git_tracked_local_review_packet",
        ],
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
    }
    assert_p7_r47_export_denylist_policy_contract(policy)
    return policy


def build_p7_r47_r2_r3_storage_export_policy(
    *,
    local_review_root: Any = None,
    repo_roots: Sequence[Any] | None = None,
    export_roots: Sequence[Any] | None = None,
    r0_r1_scope_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r47_r2_r3_storage_export_policy",
) -> dict[str, Any]:
    """Build a compact body-free combined R2/R3 policy summary."""

    r0_r1 = (
        safe_mapping(r0_r1_scope_freeze)
        if r0_r1_scope_freeze is not None
        else build_p7_r47_r0_r1_scope_freeze()
    )
    assert_p7_r47_r0_r1_scope_freeze_contract(r0_r1)
    if r0_r1_scope_freeze is not None:
        _assert_r47_body_free(r0_r1, source="p7_r47.r0_r1_scope_freeze")

    storage = build_p7_r47_local_review_storage_root_policy(
        local_review_root=local_review_root,
        repo_roots=repo_roots,
        export_roots=export_roots,
    )
    export = build_p7_r47_export_denylist_policy()
    combined = {
        "schema_version": P7_R47_R2_R3_STORAGE_EXPORT_POLICY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R47_LOCAL_REVIEW_PACKET_STEP,
        "scope": P7_R47_LOCAL_REVIEW_PACKET_SCOPE,
        "policy_kind": P7_R47_POLICY_KIND,
        "material_id": clean_identifier(material_id, default="p7_r47_r2_r3_storage_export_policy", max_length=160),
        "policy_section": "R2_R3_storage_export_policy",
        "current_phase": "P7",
        "implemented_steps": list(P7_R47_R2_R3_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R47_R2_R3_NOT_YET_IMPLEMENTED_STEPS),
        "r0_r1_scope_freeze": r0_r1,
        "storage_policy": storage,
        "export_policy": export,
        "first_next_work_ref": P7_R47_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R47_R2_R3_NEXT_REQUIRED_STEP_REF,
        "packet_kind_enum": list(P7_R47_PACKET_KINDS),
        "r0_current_source_handoff_hold_refrozen": True,
        "r1_scope_packet_kind_enum_fixed": True,
        "local_review_packet_storage_policy_fixed": True,
        "export_denylist_policy_fixed": True,
        "git_zip_mixing_prevention_policy_fixed": True,
        "local_body_packet_generation_allowed": storage["local_body_packet_generation_allowed"],
        "local_review_packet_policy_ready": False,
        "policy_ready": False,
        "r47_policy_ready": False,
        "p5_human_blind_qa_start_allowed_after_r2_r3": False,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "real_device_modal_review_start_allowed": False,
        "real_device_modal_review_confirmed": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "body_full_packet_schema_created_here": False,
        "body_free_manifest_schema_created_here": False,
        "rating_row_schema_created_here": False,
        "disposal_policy_created_here": False,
        "actual_human_review_run_here": False,
        "actual_real_device_review_run_here": False,
        "local_reviewer_payload_materialized_here": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
    }
    assert_p7_r47_r2_r3_storage_export_policy_contract(combined)
    return combined



def _json_schema_property_names(value: Any) -> tuple[str, ...]:
    names: list[str] = []
    if isinstance(value, Mapping):
        properties = value.get("properties")
        if isinstance(properties, Mapping):
            names.extend(str(key) for key in properties.keys())
        for child in value.values():
            names.extend(_json_schema_property_names(child))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child in value:
            names.extend(_json_schema_property_names(child))
    return tuple(names)


def _forbidden_schema_property_names(value: Any, forbidden: Sequence[str]) -> tuple[str, ...]:
    forbidden_set = {str(item) for item in forbidden}
    return tuple(dedupe_identifiers(name for name in _json_schema_property_names(value) if name in forbidden_set))


def _body_full_local_packet_json_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": P7_R47_BODY_FULL_LOCAL_REVIEW_PACKET_SCHEMA_VERSION,
        "title": "Cocolon EmlisAI P7-R47 Body-full Local Review Packet - Local Only",
        "type": "object",
        "additionalProperties": False,
        "required": list(P7_R47_BODY_FULL_PACKET_REQUIRED_FIELD_REFS),
        "properties": {
            "schema_version": {"const": P7_R47_BODY_FULL_LOCAL_REVIEW_PACKET_SCHEMA_VERSION},
            "local_only": {"const": True},
            "must_not_export": {"const": True},
            "packet_kind": {"enum": list(P7_R47_PACKET_KINDS)},
            "review_session_id": {"type": "string", "pattern": "^[a-zA-Z0-9_.:-]{1,120}$"},
            "packet_ref_id": {"type": "string", "pattern": "^[a-zA-Z0-9_.:-]{1,120}$"},
            "blind_case_id": {"type": "string", "pattern": "^[a-zA-Z0-9_.:-]{1,120}$"},
            "reviewer_payload": {
                "type": "object",
                "additionalProperties": False,
                "required": ["current_input_review_surface", "returned_emlis_review_surface"],
                "properties": {
                    "current_input_review_surface": {"type": "string"},
                    "returned_emlis_review_surface": {"type": "string"},
                    "bounded_history_review_surface": {"type": ["string", "null"]},
                    "structure_insight_review_surface": {"type": ["string", "null"]},
                    "modal_layout_review_note": {"type": ["string", "null"]},
                },
            },
            "review_form": {
                "type": "object",
                "additionalProperties": False,
                "required": list(P7_R47_BODY_FULL_REVIEW_FORM_REQUIRED_FIELD_REFS),
                "properties": {
                    "rating_axes": {"type": "array", "items": {"type": "string"}},
                    "free_text_allowed_local_only": {"const": True},
                },
            },
            "disposal_required": {"const": True},
        },
    }


def _body_free_local_review_manifest_json_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": P7_R47_BODY_FREE_LOCAL_REVIEW_MANIFEST_SCHEMA_VERSION,
        "title": "Cocolon EmlisAI P7-R47 Body-free Local Review Manifest",
        "type": "object",
        "additionalProperties": False,
        "required": list(P7_R47_BODY_FREE_MANIFEST_REQUIRED_FIELD_REFS),
        "properties": {
            "schema_version": {"const": P7_R47_BODY_FREE_LOCAL_REVIEW_MANIFEST_SCHEMA_VERSION},
            "phase": {"const": P7_PHASE},
            "step": {"const": P7_R47_LOCAL_REVIEW_PACKET_STEP},
            "manifest_kind": {"const": "body_free_local_review_manifest"},
            "review_session_id": {"type": "string"},
            "packet_kind": {"enum": list(P7_R47_PACKET_KINDS)},
            "case_refs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": list(P7_R47_BODY_FREE_MANIFEST_CASE_REF_FIELD_REFS),
                    "properties": {
                        "blind_case_id": {"type": "string"},
                        "case_ref_id": {"type": "string"},
                        "family": {"type": "string"},
                        "subscription_tier": {"enum": ["free", "plus", "premium", "unknown"]},
                        "packet_ref_id": {"type": "string"},
                        "body_free": {"const": True},
                    },
                },
            },
            "local_body_packet_materialized_here": {"const": False},
            "body_full_packet_export_allowed": {"const": False},
            "body_free": {"const": True},
            "release_allowed": {"const": False},
            "p7_complete": {"const": False},
            "p8_start_allowed": {"const": False},
        },
    }


def build_p7_r47_body_full_local_review_packet_schema(
    *,
    material_id: Any = "p7_r47_body_full_local_review_packet_schema",
) -> dict[str, Any]:
    """Build the R4 local-only body-full packet schema proposal.

    This fixes the packet shape only. It does not create a writer, materialize
    reviewer text, or make body-full material eligible for export.
    """

    schema = {
        "schema_version": P7_R47_BODY_FULL_LOCAL_REVIEW_PACKET_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R47_LOCAL_REVIEW_PACKET_STEP,
        "scope": P7_R47_LOCAL_REVIEW_PACKET_SCOPE,
        "policy_kind": P7_R47_POLICY_KIND,
        "policy_section": "R4_body_full_local_packet_schema",
        "material_id": clean_identifier(material_id, default="p7_r47_body_full_local_review_packet_schema", max_length=160),
        "current_phase": "P7",
        "schema_kind": "body_full_local_review_packet_schema",
        "schema_definition_only": True,
        "json_schema_file_created_here": False,
        "local_only": True,
        "must_not_export": True,
        "must_not_enter_p7_material": True,
        "disposal_required": True,
        "packet_kind_enum": list(P7_R47_PACKET_KINDS),
        "required_field_refs": list(P7_R47_BODY_FULL_PACKET_REQUIRED_FIELD_REFS),
        "reviewer_facing_identifier_policy": "blind_case_id_only",
        "reviewer_payload_additional_properties_allowed": False,
        "reviewer_payload_allowed_field_refs": list(P7_R47_BODY_FULL_REVIEWER_PAYLOAD_FIELD_REFS),
        "reviewer_payload_nullable_field_refs": [
            "bounded_history_review_surface",
            "structure_insight_review_surface",
            "modal_layout_review_note",
        ],
        "review_form_required_field_refs": list(P7_R47_BODY_FULL_REVIEW_FORM_REQUIRED_FIELD_REFS),
        "free_text_allowed_local_only": True,
        "reviewer_facing_forbidden_field_refs": list(P7_R47_REVIEWER_FACING_FORBIDDEN_FIELD_REFS),
        "family_visible_to_reviewer_allowed": False,
        "reviewer_facing_family_visible_allowed": False,
        "subscription_tier_visible_to_reviewer_allowed": False,
        "expected_result_visible_to_reviewer_allowed": False,
        "gate_result_visible_to_reviewer_allowed": False,
        "case_ref_visible_to_reviewer_allowed": False,
        "user_or_db_identifier_visible_to_reviewer_allowed": False,
        "raw_history_dump_allowed": False,
        "public_meta_in_reviewer_payload_allowed": False,
        "standard_export_allowed": False,
        "public_meta_material_allowed": False,
        "p7_scorecard_material_allowed": False,
        "release_material_allowed": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "local_reviewer_payload_materialized_here": False,
        "body_free_manifest_schema_created_here": False,
        "body_full_packet_schema_created_here": True,
        "json_schema": _body_full_local_packet_json_schema(),
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        **_release_closed_flags(),
    }
    assert_p7_r47_body_full_local_review_packet_schema_contract(schema)
    return schema


def build_p7_r47_body_free_local_review_manifest_schema(
    *,
    material_id: Any = "p7_r47_body_free_local_review_manifest_schema",
) -> dict[str, Any]:
    """Build the R5 body-free manifest schema proposal."""

    schema = {
        "schema_version": P7_R47_BODY_FREE_LOCAL_REVIEW_MANIFEST_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R47_LOCAL_REVIEW_PACKET_STEP,
        "scope": P7_R47_LOCAL_REVIEW_PACKET_SCOPE,
        "policy_kind": P7_R47_POLICY_KIND,
        "policy_section": "R5_body_free_manifest_schema",
        "material_id": clean_identifier(material_id, default="p7_r47_body_free_local_review_manifest_schema", max_length=160),
        "current_phase": "P7",
        "schema_kind": "body_free_local_review_manifest_schema",
        "manifest_kind": "body_free_local_review_manifest",
        "schema_definition_only": True,
        "json_schema_file_created_here": False,
        "packet_kind_enum": list(P7_R47_PACKET_KINDS),
        "required_field_refs": list(P7_R47_BODY_FREE_MANIFEST_REQUIRED_FIELD_REFS),
        "case_ref_required_field_refs": list(P7_R47_BODY_FREE_MANIFEST_CASE_REF_FIELD_REFS),
        "case_ref_allowed_field_refs": list(P7_R47_BODY_FREE_MANIFEST_CASE_REF_FIELD_REFS),
        "case_ref_additional_properties_allowed": False,
        "subscription_tier_enum": ["free", "plus", "premium", "unknown"],
        "forbidden_field_refs": list(P7_R47_BODY_FREE_MANIFEST_FORBIDDEN_FIELD_REFS),
        "forbidden_field_rejection_policy_fixed": True,
        "local_body_packet_materialized_here": False,
        "body_full_packet_export_allowed": False,
        "local_absolute_path_included": False,
        "root_path_exposed": False,
        "actual_body_free_manifest_materialized_here": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "local_reviewer_payload_materialized_here": False,
        "body_full_packet_schema_created_here": False,
        "body_free_manifest_schema_created_here": True,
        "json_schema": _body_free_local_review_manifest_json_schema(),
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
    }
    assert_p7_r47_body_free_local_review_manifest_schema_contract(schema)
    return schema


def build_p7_r47_r4_r5_schema_freeze(
    *,
    r2_r3_storage_export_policy: Mapping[str, Any] | None = None,
    local_review_root: Any = None,
    repo_roots: Sequence[Any] | None = None,
    export_roots: Sequence[Any] | None = None,
    material_id: Any = "p7_r47_r4_r5_schema_freeze",
) -> dict[str, Any]:
    """Build a body-free combined R4/R5 schema freeze summary."""

    r2_r3 = (
        safe_mapping(r2_r3_storage_export_policy)
        if r2_r3_storage_export_policy is not None
        else build_p7_r47_r2_r3_storage_export_policy(
            local_review_root=local_review_root,
            repo_roots=repo_roots,
            export_roots=export_roots,
        )
    )
    assert_p7_r47_r2_r3_storage_export_policy_contract(r2_r3)
    if r2_r3_storage_export_policy is not None:
        _assert_r47_body_free(r2_r3, source="p7_r47.r2_r3_storage_export_policy")

    body_full_schema = build_p7_r47_body_full_local_review_packet_schema()
    manifest_schema = build_p7_r47_body_free_local_review_manifest_schema()
    freeze = {
        "schema_version": P7_R47_R4_R5_SCHEMA_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R47_LOCAL_REVIEW_PACKET_STEP,
        "scope": P7_R47_LOCAL_REVIEW_PACKET_SCOPE,
        "policy_kind": P7_R47_POLICY_KIND,
        "material_id": clean_identifier(material_id, default="p7_r47_r4_r5_schema_freeze", max_length=160),
        "policy_section": "R4_R5_schema_freeze",
        "current_phase": "P7",
        "implemented_steps": list(P7_R47_R4_R5_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R47_R4_R5_NOT_YET_IMPLEMENTED_STEPS),
        "r2_r3_storage_export_policy": r2_r3,
        "body_full_local_packet_schema_version": body_full_schema["schema_version"],
        "body_full_local_packet_schema_fixed": True,
        "body_full_local_packet_schema_local_only": True,
        "body_full_local_packet_schema_must_not_export": True,
        "body_full_local_packet_schema_required_field_refs": list(P7_R47_BODY_FULL_PACKET_REQUIRED_FIELD_REFS),
        "body_free_manifest_schema_version": manifest_schema["schema_version"],
        "body_free_manifest_schema_fixed": True,
        "body_free_manifest_allowed_case_ref_fields": list(P7_R47_BODY_FREE_MANIFEST_CASE_REF_FIELD_REFS),
        "body_free_manifest_forbidden_field_policy_fixed": True,
        "first_next_work_ref": P7_R47_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R47_R4_R5_NEXT_REQUIRED_STEP_REF,
        "packet_kind_enum": list(P7_R47_PACKET_KINDS),
        "r0_current_source_handoff_hold_refrozen": True,
        "r1_scope_packet_kind_enum_fixed": True,
        "local_review_packet_storage_policy_fixed": True,
        "export_denylist_policy_fixed": True,
        "git_zip_mixing_prevention_policy_fixed": True,
        "body_full_packet_schema_created_here": True,
        "body_free_manifest_schema_created_here": True,
        "json_schema_file_created_here": False,
        "local_review_packet_policy_ready": False,
        "policy_ready": False,
        "r47_policy_ready": False,
        "p5_human_blind_qa_start_allowed_after_r4_r5": False,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "real_device_modal_review_start_allowed": False,
        "real_device_modal_review_confirmed": False,
        "actual_body_full_packet_generated_here": False,
        "actual_body_free_manifest_materialized_here": False,
        "body_full_writer_created_here": False,
        "rating_row_schema_created_here": False,
        "disposal_policy_created_here": False,
        "actual_human_review_run_here": False,
        "actual_real_device_review_run_here": False,
        "local_reviewer_payload_materialized_here": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
    }
    assert_p7_r47_r4_r5_schema_freeze_contract(freeze)
    return freeze


def assert_p7_r47_body_full_local_review_packet_schema_contract(schema: Mapping[str, Any]) -> bool:
    data = safe_mapping(schema)
    if data.get("schema_version") != P7_R47_BODY_FULL_LOCAL_REVIEW_PACKET_SCHEMA_VERSION:
        raise ValueError("unexpected R47 R4 body-full local packet schema_version")
    if data.get("phase") != P7_PHASE or data.get("step") != P7_R47_LOCAL_REVIEW_PACKET_STEP:
        raise ValueError("unexpected R47 R4 body-full schema phase or step")
    if data.get("scope") != P7_R47_LOCAL_REVIEW_PACKET_SCOPE or data.get("policy_kind") != P7_R47_POLICY_KIND:
        raise ValueError("unexpected R47 R4 body-full schema scope or policy kind")
    if data.get("policy_section") != "R4_body_full_local_packet_schema":
        raise ValueError("R47 R4 body-full schema policy section changed")
    for true_key in (
        "schema_definition_only",
        "local_only",
        "must_not_export",
        "must_not_enter_p7_material",
        "disposal_required",
        "free_text_allowed_local_only",
        "body_full_packet_schema_created_here",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R47 R4 body-full schema must keep {true_key}=True")
    for false_key in (
        "json_schema_file_created_here",
        "reviewer_payload_additional_properties_allowed",
        "family_visible_to_reviewer_allowed",
        "subscription_tier_visible_to_reviewer_allowed",
        "expected_result_visible_to_reviewer_allowed",
        "gate_result_visible_to_reviewer_allowed",
        "case_ref_visible_to_reviewer_allowed",
        "user_or_db_identifier_visible_to_reviewer_allowed",
        "raw_history_dump_allowed",
        "public_meta_in_reviewer_payload_allowed",
        "standard_export_allowed",
        "public_meta_material_allowed",
        "p7_scorecard_material_allowed",
        "release_material_allowed",
        "actual_body_full_packet_generated_here",
        "body_full_writer_created_here",
        "local_reviewer_payload_materialized_here",
        "body_free_manifest_schema_created_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R47 R4 body-full schema must keep {false_key}=False")
    if tuple(data.get("packet_kind_enum") or ()) != P7_R47_PACKET_KINDS:
        raise ValueError("R47 R4 packet kind enum changed")
    if tuple(data.get("required_field_refs") or ()) != P7_R47_BODY_FULL_PACKET_REQUIRED_FIELD_REFS:
        raise ValueError("R47 R4 required fields changed")
    if tuple(data.get("reviewer_payload_allowed_field_refs") or ()) != P7_R47_BODY_FULL_REVIEWER_PAYLOAD_FIELD_REFS:
        raise ValueError("R47 R4 reviewer payload field refs changed")
    if tuple(data.get("review_form_required_field_refs") or ()) != P7_R47_BODY_FULL_REVIEW_FORM_REQUIRED_FIELD_REFS:
        raise ValueError("R47 R4 review form required fields changed")
    if data.get("reviewer_facing_identifier_policy") != "blind_case_id_only":
        raise ValueError("R47 R4 reviewer-facing identifier policy changed")
    forbidden = set(dedupe_identifiers(data.get("reviewer_facing_forbidden_field_refs"), limit=80, max_length=160))
    if set(P7_R47_REVIEWER_FACING_FORBIDDEN_FIELD_REFS) - forbidden:
        raise ValueError("R47 R4 reviewer-facing forbidden fields lost coverage")
    if forbidden & set(dedupe_identifiers(data.get("reviewer_payload_allowed_field_refs"), limit=80, max_length=160)):
        raise ValueError("R47 R4 reviewer payload allowed refs must not include controller-only fields")
    json_schema = safe_mapping(data.get("json_schema"))
    if json_schema.get("$id") != P7_R47_BODY_FULL_LOCAL_REVIEW_PACKET_SCHEMA_VERSION:
        raise ValueError("R47 R4 body-full JSON schema id changed")
    properties = safe_mapping(json_schema.get("properties"))
    if set(P7_R47_BODY_FULL_PACKET_REQUIRED_FIELD_REFS) - set(properties.keys()):
        raise ValueError("R47 R4 body-full JSON schema missing required properties")
    reviewer_payload_properties = safe_mapping(safe_mapping(properties.get("reviewer_payload")).get("properties"))
    if tuple(reviewer_payload_properties.keys()) != P7_R47_BODY_FULL_REVIEWER_PAYLOAD_FIELD_REFS:
        raise ValueError("R47 R4 body-full reviewer payload schema fields changed")
    bad_property_names = _forbidden_schema_property_names(json_schema, P7_R47_REVIEWER_FACING_FORBIDDEN_FIELD_REFS)
    if bad_property_names:
        raise ValueError(f"R47 R4 body-full schema exposes controller-only reviewer fields: {bad_property_names}")
    for key in _RELEASE_CLOSED_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"R47 R4 body-full schema must keep {key}=False")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_r47_r4_body_full_schema.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_r47_r4_body_full_schema.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r47_r4_body_full_schema")
    return True


def assert_p7_r47_body_free_local_review_manifest_schema_contract(schema: Mapping[str, Any]) -> bool:
    data = safe_mapping(schema)
    _assert_common(
        data,
        schema_version=P7_R47_BODY_FREE_LOCAL_REVIEW_MANIFEST_SCHEMA_VERSION,
        source="p7_r47_r5_body_free_manifest_schema",
    )
    if data.get("policy_section") != "R5_body_free_manifest_schema":
        raise ValueError("R47 R5 manifest schema policy section changed")
    if data.get("schema_kind") != "body_free_local_review_manifest_schema":
        raise ValueError("R47 R5 manifest schema kind changed")
    if data.get("manifest_kind") != "body_free_local_review_manifest":
        raise ValueError("R47 R5 manifest kind changed")
    for true_key in (
        "schema_definition_only",
        "forbidden_field_rejection_policy_fixed",
        "body_free_manifest_schema_created_here",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R47 R5 manifest schema must keep {true_key}=True")
    for false_key in (
        "json_schema_file_created_here",
        "local_body_packet_materialized_here",
        "body_full_packet_export_allowed",
        "local_absolute_path_included",
        "root_path_exposed",
        "actual_body_free_manifest_materialized_here",
        "actual_body_full_packet_generated_here",
        "body_full_writer_created_here",
        "local_reviewer_payload_materialized_here",
        "body_full_packet_schema_created_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R47 R5 manifest schema must keep {false_key}=False")
    if tuple(data.get("packet_kind_enum") or ()) != P7_R47_PACKET_KINDS:
        raise ValueError("R47 R5 manifest schema packet kind enum changed")
    if tuple(data.get("required_field_refs") or ()) != P7_R47_BODY_FREE_MANIFEST_REQUIRED_FIELD_REFS:
        raise ValueError("R47 R5 manifest required fields changed")
    if tuple(data.get("case_ref_required_field_refs") or ()) != P7_R47_BODY_FREE_MANIFEST_CASE_REF_FIELD_REFS:
        raise ValueError("R47 R5 manifest case required fields changed")
    if tuple(data.get("case_ref_allowed_field_refs") or ()) != P7_R47_BODY_FREE_MANIFEST_CASE_REF_FIELD_REFS:
        raise ValueError("R47 R5 manifest case allowed fields changed")
    if data.get("case_ref_additional_properties_allowed") is not False:
        raise ValueError("R47 R5 case refs must reject additional properties")
    forbidden = set(dedupe_identifiers(data.get("forbidden_field_refs"), limit=120, max_length=160))
    if set(P7_R47_BODY_FREE_MANIFEST_FORBIDDEN_FIELD_REFS) - forbidden:
        raise ValueError("R47 R5 forbidden field refs lost coverage")
    if set(data.get("subscription_tier_enum") or ()) != {"free", "plus", "premium", "unknown"}:
        raise ValueError("R47 R5 subscription tier enum changed")
    bad_property_names = _forbidden_schema_property_names(safe_mapping(data.get("json_schema")), P7_R47_BODY_FREE_MANIFEST_FORBIDDEN_FIELD_REFS)
    if bad_property_names:
        raise ValueError(f"R47 R5 manifest schema allows body payload fields: {bad_property_names}")
    return True


def assert_p7_r47_body_free_local_review_manifest_payload_contract(manifest: Mapping[str, Any]) -> bool:
    """Validate a future body-free manifest payload without materializing one here."""

    data = safe_mapping(manifest)
    if data.get("schema_version") != P7_R47_BODY_FREE_LOCAL_REVIEW_MANIFEST_SCHEMA_VERSION:
        raise ValueError("unexpected R47 body-free manifest payload schema_version")
    if data.get("phase") != P7_PHASE or data.get("step") != P7_R47_LOCAL_REVIEW_PACKET_STEP:
        raise ValueError("unexpected R47 body-free manifest payload phase or step")
    if data.get("scope") not in {None, P7_R47_LOCAL_REVIEW_PACKET_SCOPE}:
        raise ValueError("unexpected R47 body-free manifest payload scope")
    if data.get("manifest_kind") != "body_free_local_review_manifest":
        raise ValueError("R47 body-free manifest payload kind changed")
    if data.get("packet_kind") not in P7_R47_PACKET_KIND_SET:
        raise ValueError("R47 body-free manifest packet kind is not fixed enum")
    if data.get("body_free") is not True:
        raise ValueError("R47 body-free manifest payload must set body_free=True")
    for false_key in (
        "local_body_packet_materialized_here",
        "body_full_packet_export_allowed",
        "release_allowed",
        "p7_complete",
        "p8_start_allowed",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R47 body-free manifest payload must keep {false_key}=False")
    for required in P7_R47_BODY_FREE_MANIFEST_REQUIRED_FIELD_REFS:
        if required not in data:
            raise ValueError(f"R47 body-free manifest payload missing required field {required}")
    case_refs = data.get("case_refs")
    if not isinstance(case_refs, list):
        raise ValueError("R47 body-free manifest case_refs must be a list")
    expected_case_keys = set(P7_R47_BODY_FREE_MANIFEST_CASE_REF_FIELD_REFS)
    for item in case_refs:
        case_ref = safe_mapping(item)
        if set(case_ref) != expected_case_keys:
            raise ValueError("R47 body-free manifest case_ref contains non-body-free or missing fields")
        if case_ref.get("body_free") is not True:
            raise ValueError("R47 body-free manifest case_ref must be body_free")
        if case_ref.get("subscription_tier") not in {"free", "plus", "premium", "unknown"}:
            raise ValueError("R47 body-free manifest case_ref subscription tier changed")
    _assert_r47_body_free(data, source="p7_r47_body_free_manifest_payload")
    return True


def assert_p7_r47_r4_r5_schema_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_common(data, schema_version=P7_R47_R4_R5_SCHEMA_FREEZE_SCHEMA_VERSION, source="p7_r47_r4_r5_schema_freeze")
    if data.get("policy_section") != "R4_R5_schema_freeze":
        raise ValueError("R47 R4/R5 schema freeze policy section changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R47_R4_R5_IMPLEMENTED_STEPS:
        raise ValueError("R47 R4/R5 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R47_R4_R5_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R47 R4/R5 not-yet-implemented steps changed")
    assert_p7_r47_r2_r3_storage_export_policy_contract(safe_mapping(data.get("r2_r3_storage_export_policy")))
    if data.get("next_required_step") != P7_R47_R4_R5_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R47 R4/R5 must point to R6 as next required step")
    if tuple(data.get("packet_kind_enum") or ()) != P7_R47_PACKET_KINDS:
        raise ValueError("R47 R4/R5 packet enum changed")
    if data.get("body_full_local_packet_schema_version") != P7_R47_BODY_FULL_LOCAL_REVIEW_PACKET_SCHEMA_VERSION:
        raise ValueError("R47 R4/R5 body-full schema version changed")
    if data.get("body_free_manifest_schema_version") != P7_R47_BODY_FREE_LOCAL_REVIEW_MANIFEST_SCHEMA_VERSION:
        raise ValueError("R47 R4/R5 manifest schema version changed")
    for true_key in (
        "r0_current_source_handoff_hold_refrozen",
        "r1_scope_packet_kind_enum_fixed",
        "local_review_packet_storage_policy_fixed",
        "export_denylist_policy_fixed",
        "git_zip_mixing_prevention_policy_fixed",
        "body_full_local_packet_schema_fixed",
        "body_full_local_packet_schema_local_only",
        "body_full_local_packet_schema_must_not_export",
        "body_free_manifest_schema_fixed",
        "body_free_manifest_forbidden_field_policy_fixed",
        "body_full_packet_schema_created_here",
        "body_free_manifest_schema_created_here",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R47 R4/R5 must keep {true_key}=True")
    for false_key in (
        "json_schema_file_created_here",
        "local_review_packet_policy_ready",
        "policy_ready",
        "r47_policy_ready",
        "p5_human_blind_qa_start_allowed_after_r4_r5",
        "p5_human_blind_qa_confirmed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_limited_human_readfeel_confirmed",
        "real_device_modal_review_start_allowed",
        "real_device_modal_review_confirmed",
        "actual_body_full_packet_generated_here",
        "actual_body_free_manifest_materialized_here",
        "body_full_writer_created_here",
        "rating_row_schema_created_here",
        "disposal_policy_created_here",
        "actual_human_review_run_here",
        "actual_real_device_review_run_here",
        "local_reviewer_payload_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R47 R4/R5 must keep {false_key}=False")
    if tuple(data.get("body_full_local_packet_schema_required_field_refs") or ()) != P7_R47_BODY_FULL_PACKET_REQUIRED_FIELD_REFS:
        raise ValueError("R47 R4/R5 body-full schema required field summary changed")
    if tuple(data.get("body_free_manifest_allowed_case_ref_fields") or ()) != P7_R47_BODY_FREE_MANIFEST_CASE_REF_FIELD_REFS:
        raise ValueError("R47 R4/R5 manifest case ref field summary changed")
    return True


def _body_free_rating_row_json_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": P7_R47_BODY_FREE_RATING_ROW_SCHEMA_VERSION,
        "title": "Cocolon EmlisAI P7-R47 Body-free Rating Row",
        "type": "object",
        "additionalProperties": False,
        "required": list(P7_R47_BODY_FREE_RATING_ROW_REQUIRED_FIELD_REFS),
        "properties": {
            "schema_version": {"const": P7_R47_BODY_FREE_RATING_ROW_SCHEMA_VERSION},
            "review_session_id": {"type": "string"},
            "packet_ref_id": {"type": "string"},
            "blind_case_id": {"type": "string"},
            "case_ref_id": {"type": "string"},
            "packet_kind": {"enum": list(P7_R47_PACKET_KINDS)},
            "family": {"type": "string"},
            "subscription_tier": {"enum": ["free", "plus", "premium", "unknown"]},
            "reviewer_ref": {"type": "string"},
            "reviewed_at": {"type": "string"},
            "axis_scores": {
                "type": "object",
                "additionalProperties": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            },
            "verdict": {"enum": list(P7_R47_REVIEW_VERDICTS)},
            "sanitized_reason_ids": {"type": "array", "items": {"type": "string"}},
            "blocker_ids": {"type": "array", "items": {"type": "string"}},
            "reviewer_free_text_included": {"const": False},
            "body_removed": {"type": "boolean"},
            "body_free": {"const": True},
        },
    }


def _body_free_blocker_row_json_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": P7_R47_BODY_FREE_BLOCKER_ROW_SCHEMA_VERSION,
        "title": "Cocolon EmlisAI P7-R47 Body-free Blocker Row",
        "type": "object",
        "additionalProperties": False,
        "required": list(P7_R47_BODY_FREE_BLOCKER_ROW_REQUIRED_FIELD_REFS),
        "properties": {
            "schema_version": {"const": P7_R47_BODY_FREE_BLOCKER_ROW_SCHEMA_VERSION},
            "review_session_id": {"type": "string"},
            "packet_ref_id": {"type": "string"},
            "blind_case_id": {"type": "string"},
            "case_ref_id": {"type": "string"},
            "packet_kind": {"enum": list(P7_R47_PACKET_KINDS)},
            "family": {"type": "string"},
            "subscription_tier": {"enum": ["free", "plus", "premium", "unknown"]},
            "blocker_id": {"type": "string"},
            "blocker_kind": {"enum": list(P7_R47_BLOCKER_KINDS)},
            "blocker_status": {"enum": list(P7_R47_BLOCKER_STATUSES)},
            "sanitized_reason_ids": {"type": "array", "items": {"type": "string"}},
            "reviewer_free_text_included": {"const": False},
            "body_removed": {"type": "boolean"},
            "body_free": {"const": True},
        },
    }


def build_p7_r47_body_free_rating_row_schema(
    *,
    material_id: Any = "p7_r47_body_free_rating_row_schema",
) -> dict[str, Any]:
    """Build the R6 body-free rating-row schema proposal without writing rows."""

    schema = {
        "schema_version": P7_R47_BODY_FREE_RATING_ROW_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R47_LOCAL_REVIEW_PACKET_STEP,
        "scope": P7_R47_LOCAL_REVIEW_PACKET_SCOPE,
        "policy_kind": P7_R47_POLICY_KIND,
        "policy_section": "R6_body_free_rating_row_schema",
        "material_id": clean_identifier(material_id, default="p7_r47_body_free_rating_row_schema", max_length=160),
        "current_phase": "P7",
        "schema_kind": "body_free_rating_row_schema",
        "schema_definition_only": True,
        "json_schema_file_created_here": False,
        "required_field_refs": list(P7_R47_BODY_FREE_RATING_ROW_REQUIRED_FIELD_REFS),
        "packet_kind_enum": list(P7_R47_PACKET_KINDS),
        "subscription_tier_enum": ["free", "plus", "premium", "unknown"],
        "verdict_enum": list(P7_R47_REVIEW_VERDICTS),
        "axis_scores_range": {"minimum": 0.0, "maximum": 1.0},
        "axis_scores_machine_auto_fill_allowed": False,
        "read_feeling_auto_estimation_allowed": False,
        "sanitized_reason_ids_only": True,
        "blocker_ids_only": True,
        "reviewer_free_text_included": False,
        "reviewer_free_text_material_allowed": False,
        "body_removed_status_required": True,
        "body_removed_may_be_false_until_r8_disposal": True,
        "forbidden_field_refs": list(P7_R47_BODY_FREE_RATING_BLOCKER_FORBIDDEN_FIELD_REFS),
        "actual_rating_rows_materialized_here": False,
        "actual_human_review_run_here": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "local_reviewer_payload_materialized_here": False,
        "rating_row_schema_created_here": True,
        "blocker_row_schema_created_here": False,
        "disposal_policy_created_here": False,
        "json_schema": _body_free_rating_row_json_schema(),
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
    }
    assert_p7_r47_body_free_rating_row_schema_contract(schema)
    return schema


def build_p7_r47_body_free_blocker_row_schema(
    *,
    material_id: Any = "p7_r47_body_free_blocker_row_schema",
) -> dict[str, Any]:
    """Build the R6 body-free blocker-row schema proposal without writing rows."""

    schema = {
        "schema_version": P7_R47_BODY_FREE_BLOCKER_ROW_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R47_LOCAL_REVIEW_PACKET_STEP,
        "scope": P7_R47_LOCAL_REVIEW_PACKET_SCOPE,
        "policy_kind": P7_R47_POLICY_KIND,
        "policy_section": "R6_body_free_blocker_row_schema",
        "material_id": clean_identifier(material_id, default="p7_r47_body_free_blocker_row_schema", max_length=160),
        "current_phase": "P7",
        "schema_kind": "body_free_blocker_row_schema",
        "schema_definition_only": True,
        "json_schema_file_created_here": False,
        "required_field_refs": list(P7_R47_BODY_FREE_BLOCKER_ROW_REQUIRED_FIELD_REFS),
        "packet_kind_enum": list(P7_R47_PACKET_KINDS),
        "subscription_tier_enum": ["free", "plus", "premium", "unknown"],
        "blocker_kind_enum": list(P7_R47_BLOCKER_KINDS),
        "blocker_status_enum": list(P7_R47_BLOCKER_STATUSES),
        "execution_blocker_id_refs": list(P7_R47_EXECUTION_BLOCKER_ID_REFS),
        "sanitized_reason_ids_only": True,
        "reviewer_free_text_included": False,
        "reviewer_free_text_material_allowed": False,
        "body_removed_status_required": True,
        "body_removed_may_be_false_until_r8_disposal": True,
        "forbidden_field_refs": list(P7_R47_BODY_FREE_RATING_BLOCKER_FORBIDDEN_FIELD_REFS),
        "actual_blocker_rows_materialized_here": False,
        "actual_human_review_run_here": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "local_reviewer_payload_materialized_here": False,
        "rating_row_schema_created_here": False,
        "blocker_row_schema_created_here": True,
        "disposal_policy_created_here": False,
        "json_schema": _body_free_blocker_row_json_schema(),
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
    }
    assert_p7_r47_body_free_blocker_row_schema_contract(schema)
    return schema


def build_p7_r47_reviewer_notes_local_only_policy(
    *,
    material_id: Any = "p7_r47_reviewer_notes_local_only_policy",
) -> dict[str, Any]:
    """Build the R7 reviewer free-text/notes local-only policy."""

    policy = {
        "schema_version": P7_R47_REVIEWER_NOTES_LOCAL_ONLY_POLICY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R47_LOCAL_REVIEW_PACKET_STEP,
        "scope": P7_R47_LOCAL_REVIEW_PACKET_SCOPE,
        "policy_kind": P7_R47_POLICY_KIND,
        "policy_section": "R7_reviewer_free_text_notes_local_only_policy",
        "material_id": clean_identifier(material_id, default="p7_r47_reviewer_notes_local_only_policy", max_length=160),
        "current_phase": "P7",
        "local_only_notes_policy_fixed": True,
        "reviewer_free_text_policy_fixed": True,
        "local_notes_dir_ref": "reviewer_notes.local_only",
        "local_notes_standard_export_allowed": False,
        "local_notes_release_material_allowed": False,
        "local_notes_p7_scorecard_material_allowed": False,
        "local_notes_handoff_ledger_material_allowed": False,
        "direct_note_copy_to_p7_allowed": False,
        "raw_quote_to_reason_id_allowed": False,
        "sanitized_reason_id_required_for_p7_material": True,
        "sanitized_reason_id_refs": list(P7_R47_SANITIZED_REASON_ID_REFS),
        "execution_blocker_id_refs": list(P7_R47_EXECUTION_BLOCKER_ID_REFS),
        "default_unmapped_reason_id": "reason_id_other_local_note_purged",
        "reason_id_other_local_note_purged": True,
        "notes_retention_after_rating_finalized_max_hours": P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
        "notes_purge_required_after_rating_finalized": True,
        "rating_rows_body_free_only": True,
        "blocker_rows_body_free_only": True,
        "reviewer_free_text_included": False,
        "reviewer_free_text_material_allowed": False,
        "actual_notes_materialized_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "local_reviewer_payload_materialized_here": False,
        "actual_human_review_run_here": False,
        "disposal_policy_created_here": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
    }
    assert_p7_r47_reviewer_notes_local_only_policy_contract(policy)
    return policy


def build_p7_r47_r6_r7_rating_blocker_notes_policy_freeze(
    *,
    r4_r5_schema_freeze: Mapping[str, Any] | None = None,
    local_review_root: Any = None,
    repo_roots: Sequence[Any] | None = None,
    export_roots: Sequence[Any] | None = None,
    material_id: Any = "p7_r47_r6_r7_rating_blocker_notes_policy_freeze",
) -> dict[str, Any]:
    """Build a body-free combined R6/R7 schema and notes-policy freeze."""

    r4_r5 = (
        safe_mapping(r4_r5_schema_freeze)
        if r4_r5_schema_freeze is not None
        else build_p7_r47_r4_r5_schema_freeze(
            local_review_root=local_review_root,
            repo_roots=repo_roots,
            export_roots=export_roots,
        )
    )
    assert_p7_r47_r4_r5_schema_freeze_contract(r4_r5)
    if r4_r5_schema_freeze is not None:
        _assert_r47_body_free(r4_r5, source="p7_r47.r4_r5_schema_freeze")

    rating_schema = build_p7_r47_body_free_rating_row_schema()
    blocker_schema = build_p7_r47_body_free_blocker_row_schema()
    notes_policy = build_p7_r47_reviewer_notes_local_only_policy()
    freeze = {
        "schema_version": P7_R47_R6_R7_RATING_BLOCKER_NOTES_POLICY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R47_LOCAL_REVIEW_PACKET_STEP,
        "scope": P7_R47_LOCAL_REVIEW_PACKET_SCOPE,
        "policy_kind": P7_R47_POLICY_KIND,
        "material_id": clean_identifier(
            material_id,
            default="p7_r47_r6_r7_rating_blocker_notes_policy_freeze",
            max_length=160,
        ),
        "policy_section": "R6_R7_rating_blocker_notes_policy_freeze",
        "current_phase": "P7",
        "implemented_steps": list(P7_R47_R6_R7_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R47_R6_R7_NOT_YET_IMPLEMENTED_STEPS),
        "r4_r5_schema_freeze": r4_r5,
        "rating_row_schema_version": rating_schema["schema_version"],
        "rating_row_schema_fixed": True,
        "rating_row_required_field_refs": list(P7_R47_BODY_FREE_RATING_ROW_REQUIRED_FIELD_REFS),
        "blocker_row_schema_version": blocker_schema["schema_version"],
        "blocker_row_schema_fixed": True,
        "blocker_row_required_field_refs": list(P7_R47_BODY_FREE_BLOCKER_ROW_REQUIRED_FIELD_REFS),
        "reviewer_notes_policy_schema_version": notes_policy["schema_version"],
        "reviewer_notes_local_only_policy_fixed": True,
        "reviewer_free_text_policy_fixed": True,
        "sanitized_reason_id_required_for_p7_material": True,
        "notes_retention_after_rating_finalized_max_hours": P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
        "first_next_work_ref": P7_R47_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R47_R6_R7_NEXT_REQUIRED_STEP_REF,
        "packet_kind_enum": list(P7_R47_PACKET_KINDS),
        "r0_current_source_handoff_hold_refrozen": True,
        "r1_scope_packet_kind_enum_fixed": True,
        "local_review_packet_storage_policy_fixed": True,
        "export_denylist_policy_fixed": True,
        "git_zip_mixing_prevention_policy_fixed": True,
        "body_full_packet_schema_created_here": True,
        "body_free_manifest_schema_created_here": True,
        "rating_row_schema_created_here": True,
        "blocker_row_schema_created_here": True,
        "reviewer_notes_policy_created_here": True,
        "json_schema_file_created_here": False,
        "local_review_packet_policy_ready": False,
        "policy_ready": False,
        "r47_policy_ready": False,
        "p5_human_blind_qa_start_allowed_after_r6_r7": False,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "real_device_modal_review_start_allowed": False,
        "real_device_modal_review_confirmed": False,
        "actual_body_full_packet_generated_here": False,
        "actual_body_free_manifest_materialized_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_notes_materialized_here": False,
        "body_full_writer_created_here": False,
        "disposal_policy_created_here": False,
        "actual_human_review_run_here": False,
        "actual_real_device_review_run_here": False,
        "local_reviewer_payload_materialized_here": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
    }
    assert_p7_r47_r6_r7_rating_blocker_notes_policy_freeze_contract(freeze)
    return freeze


def _assert_schema_common_for_r6(data: Mapping[str, Any], *, schema_version: str, policy_section: str, source: str) -> None:
    _assert_common(data, schema_version=schema_version, source=source)
    if data.get("policy_section") != policy_section:
        raise ValueError(f"{source} policy section changed")
    if data.get("schema_definition_only") is not True:
        raise ValueError(f"{source} must remain schema-definition only")
    if data.get("json_schema_file_created_here") is not False:
        raise ValueError(f"{source} must not create a JSON schema file here")
    if tuple(data.get("packet_kind_enum") or ()) != P7_R47_PACKET_KINDS:
        raise ValueError(f"{source} packet kind enum changed")
    if set(data.get("subscription_tier_enum") or ()) != {"free", "plus", "premium", "unknown"}:
        raise ValueError(f"{source} subscription tier enum changed")
    for false_key in (
        "reviewer_free_text_included",
        "reviewer_free_text_material_allowed",
        "actual_human_review_run_here",
        "actual_body_full_packet_generated_here",
        "body_full_writer_created_here",
        "local_reviewer_payload_materialized_here",
        "disposal_policy_created_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"{source} must keep {false_key}=False")
    if data.get("body_removed_status_required") is not True:
        raise ValueError(f"{source} must require body_removed status")
    bad_property_names = _forbidden_schema_property_names(
        safe_mapping(data.get("json_schema")),
        P7_R47_BODY_FREE_RATING_BLOCKER_FORBIDDEN_FIELD_REFS,
    )
    if bad_property_names:
        raise ValueError(f"{source} schema allows body or reviewer-note fields: {bad_property_names}")


def assert_p7_r47_body_free_rating_row_schema_contract(schema: Mapping[str, Any]) -> bool:
    data = safe_mapping(schema)
    _assert_schema_common_for_r6(
        data,
        schema_version=P7_R47_BODY_FREE_RATING_ROW_SCHEMA_VERSION,
        policy_section="R6_body_free_rating_row_schema",
        source="p7_r47_r6_rating_row_schema",
    )
    if data.get("schema_kind") != "body_free_rating_row_schema":
        raise ValueError("R47 R6 rating row schema kind changed")
    if tuple(data.get("required_field_refs") or ()) != P7_R47_BODY_FREE_RATING_ROW_REQUIRED_FIELD_REFS:
        raise ValueError("R47 R6 rating row required fields changed")
    if tuple(data.get("verdict_enum") or ()) != P7_R47_REVIEW_VERDICTS:
        raise ValueError("R47 R6 rating row verdict enum changed")
    if data.get("axis_scores_machine_auto_fill_allowed") is not False:
        raise ValueError("R47 R6 rating row must not auto-fill readfeel axes from machine metrics")
    if data.get("read_feeling_auto_estimation_allowed") is not False:
        raise ValueError("R47 R6 rating row must not estimate read feeling automatically")
    for true_key in ("sanitized_reason_ids_only", "blocker_ids_only", "rating_row_schema_created_here"):
        if data.get(true_key) is not True:
            raise ValueError(f"R47 R6 rating row schema must keep {true_key}=True")
    if data.get("blocker_row_schema_created_here") is not False:
        raise ValueError("R47 R6 rating row schema must not mark blocker schema created")
    json_schema = safe_mapping(data.get("json_schema"))
    if json_schema.get("$id") != P7_R47_BODY_FREE_RATING_ROW_SCHEMA_VERSION:
        raise ValueError("R47 R6 rating row JSON schema id changed")
    if tuple(json_schema.get("required") or ()) != P7_R47_BODY_FREE_RATING_ROW_REQUIRED_FIELD_REFS:
        raise ValueError("R47 R6 rating row JSON schema required fields changed")
    properties = safe_mapping(json_schema.get("properties"))
    if tuple(properties.keys()) != P7_R47_BODY_FREE_RATING_ROW_REQUIRED_FIELD_REFS:
        raise ValueError("R47 R6 rating row JSON schema properties changed")
    return True


def assert_p7_r47_body_free_blocker_row_schema_contract(schema: Mapping[str, Any]) -> bool:
    data = safe_mapping(schema)
    _assert_schema_common_for_r6(
        data,
        schema_version=P7_R47_BODY_FREE_BLOCKER_ROW_SCHEMA_VERSION,
        policy_section="R6_body_free_blocker_row_schema",
        source="p7_r47_r6_blocker_row_schema",
    )
    if data.get("schema_kind") != "body_free_blocker_row_schema":
        raise ValueError("R47 R6 blocker row schema kind changed")
    if tuple(data.get("required_field_refs") or ()) != P7_R47_BODY_FREE_BLOCKER_ROW_REQUIRED_FIELD_REFS:
        raise ValueError("R47 R6 blocker row required fields changed")
    if tuple(data.get("blocker_kind_enum") or ()) != P7_R47_BLOCKER_KINDS:
        raise ValueError("R47 R6 blocker kind enum changed")
    if tuple(data.get("blocker_status_enum") or ()) != P7_R47_BLOCKER_STATUSES:
        raise ValueError("R47 R6 blocker status enum changed")
    for true_key in ("sanitized_reason_ids_only", "blocker_row_schema_created_here"):
        if data.get(true_key) is not True:
            raise ValueError(f"R47 R6 blocker row schema must keep {true_key}=True")
    if data.get("rating_row_schema_created_here") is not False:
        raise ValueError("R47 R6 blocker row schema must not mark rating schema created")
    json_schema = safe_mapping(data.get("json_schema"))
    if json_schema.get("$id") != P7_R47_BODY_FREE_BLOCKER_ROW_SCHEMA_VERSION:
        raise ValueError("R47 R6 blocker row JSON schema id changed")
    if tuple(json_schema.get("required") or ()) != P7_R47_BODY_FREE_BLOCKER_ROW_REQUIRED_FIELD_REFS:
        raise ValueError("R47 R6 blocker row JSON schema required fields changed")
    properties = safe_mapping(json_schema.get("properties"))
    if tuple(properties.keys()) != P7_R47_BODY_FREE_BLOCKER_ROW_REQUIRED_FIELD_REFS:
        raise ValueError("R47 R6 blocker row JSON schema properties changed")
    return True


def _assert_identifier_sequence(value: Any, *, source: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{source} must be a list")
    cleaned = tuple(dedupe_identifiers(value, limit=200, max_length=160))
    if len(cleaned) != len(value):
        raise ValueError(f"{source} must contain only non-empty identifier strings")
    return cleaned


def assert_p7_r47_body_free_rating_row_payload_contract(row: Mapping[str, Any]) -> bool:
    """Validate a future body-free rating row without writing one here."""

    data = safe_mapping(row)
    if data.get("schema_version") != P7_R47_BODY_FREE_RATING_ROW_SCHEMA_VERSION:
        raise ValueError("unexpected R47 body-free rating row schema_version")
    if set(data) != set(P7_R47_BODY_FREE_RATING_ROW_REQUIRED_FIELD_REFS):
        raise ValueError("R47 body-free rating row contains non-body-free or missing fields")
    if data.get("packet_kind") not in P7_R47_PACKET_KIND_SET:
        raise ValueError("R47 body-free rating row packet kind is not fixed enum")
    if data.get("subscription_tier") not in {"free", "plus", "premium", "unknown"}:
        raise ValueError("R47 body-free rating row subscription tier changed")
    axis_scores = safe_mapping(data.get("axis_scores"))
    if not axis_scores:
        raise ValueError("R47 body-free rating row requires axis_scores")
    for axis, score in axis_scores.items():
        if not clean_identifier(axis, default="", max_length=120):
            raise ValueError("R47 body-free rating row axis id must be an identifier")
        if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0.0 <= float(score) <= 1.0:
            raise ValueError("R47 body-free rating row axis scores must be numbers from 0.0 to 1.0")
    if data.get("verdict") not in P7_R47_REVIEW_VERDICTS:
        raise ValueError("R47 body-free rating row verdict enum changed")
    _assert_identifier_sequence(data.get("sanitized_reason_ids"), source="p7_r47_rating_row.sanitized_reason_ids")
    _assert_identifier_sequence(data.get("blocker_ids"), source="p7_r47_rating_row.blocker_ids")
    if data.get("reviewer_free_text_included") is not False:
        raise ValueError("R47 body-free rating row must not include reviewer free text")
    if not isinstance(data.get("body_removed"), bool):
        raise ValueError("R47 body-free rating row must carry a boolean body_removed status")
    if data.get("body_free") is not True:
        raise ValueError("R47 body-free rating row must set body_free=True")
    _assert_r47_body_free(data, source="p7_r47_body_free_rating_row_payload")
    return True


def assert_p7_r47_body_free_blocker_row_payload_contract(row: Mapping[str, Any]) -> bool:
    """Validate a future body-free blocker row without writing one here."""

    data = safe_mapping(row)
    if data.get("schema_version") != P7_R47_BODY_FREE_BLOCKER_ROW_SCHEMA_VERSION:
        raise ValueError("unexpected R47 body-free blocker row schema_version")
    if set(data) != set(P7_R47_BODY_FREE_BLOCKER_ROW_REQUIRED_FIELD_REFS):
        raise ValueError("R47 body-free blocker row contains non-body-free or missing fields")
    if data.get("packet_kind") not in P7_R47_PACKET_KIND_SET:
        raise ValueError("R47 body-free blocker row packet kind is not fixed enum")
    if data.get("subscription_tier") not in {"free", "plus", "premium", "unknown"}:
        raise ValueError("R47 body-free blocker row subscription tier changed")
    if not clean_identifier(data.get("blocker_id"), default="", max_length=160):
        raise ValueError("R47 body-free blocker row requires a blocker_id identifier")
    if data.get("blocker_kind") not in P7_R47_BLOCKER_KINDS:
        raise ValueError("R47 body-free blocker row blocker kind enum changed")
    if data.get("blocker_status") not in P7_R47_BLOCKER_STATUSES:
        raise ValueError("R47 body-free blocker row blocker status enum changed")
    _assert_identifier_sequence(data.get("sanitized_reason_ids"), source="p7_r47_blocker_row.sanitized_reason_ids")
    if data.get("reviewer_free_text_included") is not False:
        raise ValueError("R47 body-free blocker row must not include reviewer free text")
    if not isinstance(data.get("body_removed"), bool):
        raise ValueError("R47 body-free blocker row must carry a boolean body_removed status")
    if data.get("body_free") is not True:
        raise ValueError("R47 body-free blocker row must set body_free=True")
    _assert_r47_body_free(data, source="p7_r47_body_free_blocker_row_payload")
    return True


def assert_p7_r47_reviewer_notes_local_only_policy_contract(policy: Mapping[str, Any]) -> bool:
    data = safe_mapping(policy)
    _assert_common(
        data,
        schema_version=P7_R47_REVIEWER_NOTES_LOCAL_ONLY_POLICY_SCHEMA_VERSION,
        source="p7_r47_r7_reviewer_notes_policy",
    )
    if data.get("policy_section") != "R7_reviewer_free_text_notes_local_only_policy":
        raise ValueError("R47 R7 notes policy section changed")
    for true_key in (
        "local_only_notes_policy_fixed",
        "reviewer_free_text_policy_fixed",
        "sanitized_reason_id_required_for_p7_material",
        "reason_id_other_local_note_purged",
        "notes_purge_required_after_rating_finalized",
        "rating_rows_body_free_only",
        "blocker_rows_body_free_only",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R47 R7 notes policy must keep {true_key}=True")
    for false_key in (
        "local_notes_standard_export_allowed",
        "local_notes_release_material_allowed",
        "local_notes_p7_scorecard_material_allowed",
        "local_notes_handoff_ledger_material_allowed",
        "direct_note_copy_to_p7_allowed",
        "raw_quote_to_reason_id_allowed",
        "reviewer_free_text_included",
        "reviewer_free_text_material_allowed",
        "actual_notes_materialized_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_body_full_packet_generated_here",
        "body_full_writer_created_here",
        "local_reviewer_payload_materialized_here",
        "actual_human_review_run_here",
        "disposal_policy_created_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R47 R7 notes policy must keep {false_key}=False")
    if data.get("local_notes_dir_ref") != "reviewer_notes.local_only":
        raise ValueError("R47 R7 local notes dir ref changed")
    if data.get("notes_retention_after_rating_finalized_max_hours") != P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS:
        raise ValueError("R47 R7 notes retention changed")
    if data.get("default_unmapped_reason_id") != "reason_id_other_local_note_purged":
        raise ValueError("R47 R7 default unmapped reason id changed")
    reason_ids = set(dedupe_identifiers(data.get("sanitized_reason_id_refs"), limit=200, max_length=160))
    if set(P7_R47_SANITIZED_REASON_ID_REFS) - reason_ids:
        raise ValueError("R47 R7 sanitized reason ids lost coverage")
    blocker_ids = set(dedupe_identifiers(data.get("execution_blocker_id_refs"), limit=120, max_length=160))
    if set(P7_R47_EXECUTION_BLOCKER_ID_REFS) - blocker_ids:
        raise ValueError("R47 R7 execution blocker ids lost coverage")
    return True


def assert_p7_r47_r6_r7_rating_blocker_notes_policy_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_common(
        data,
        schema_version=P7_R47_R6_R7_RATING_BLOCKER_NOTES_POLICY_SCHEMA_VERSION,
        source="p7_r47_r6_r7_rating_blocker_notes_policy_freeze",
    )
    if data.get("policy_section") != "R6_R7_rating_blocker_notes_policy_freeze":
        raise ValueError("R47 R6/R7 policy section changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R47_R6_R7_IMPLEMENTED_STEPS:
        raise ValueError("R47 R6/R7 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R47_R6_R7_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R47 R6/R7 not-yet-implemented steps changed")
    assert_p7_r47_r4_r5_schema_freeze_contract(safe_mapping(data.get("r4_r5_schema_freeze")))
    if data.get("next_required_step") != P7_R47_R6_R7_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R47 R6/R7 must point to R8 as next required step")
    if data.get("rating_row_schema_version") != P7_R47_BODY_FREE_RATING_ROW_SCHEMA_VERSION:
        raise ValueError("R47 R6/R7 rating row schema version changed")
    if data.get("blocker_row_schema_version") != P7_R47_BODY_FREE_BLOCKER_ROW_SCHEMA_VERSION:
        raise ValueError("R47 R6/R7 blocker row schema version changed")
    if data.get("reviewer_notes_policy_schema_version") != P7_R47_REVIEWER_NOTES_LOCAL_ONLY_POLICY_SCHEMA_VERSION:
        raise ValueError("R47 R6/R7 reviewer notes policy version changed")
    if tuple(data.get("rating_row_required_field_refs") or ()) != P7_R47_BODY_FREE_RATING_ROW_REQUIRED_FIELD_REFS:
        raise ValueError("R47 R6/R7 rating row required field summary changed")
    if tuple(data.get("blocker_row_required_field_refs") or ()) != P7_R47_BODY_FREE_BLOCKER_ROW_REQUIRED_FIELD_REFS:
        raise ValueError("R47 R6/R7 blocker row required field summary changed")
    for true_key in (
        "r0_current_source_handoff_hold_refrozen",
        "r1_scope_packet_kind_enum_fixed",
        "local_review_packet_storage_policy_fixed",
        "export_denylist_policy_fixed",
        "git_zip_mixing_prevention_policy_fixed",
        "body_full_packet_schema_created_here",
        "body_free_manifest_schema_created_here",
        "rating_row_schema_created_here",
        "blocker_row_schema_created_here",
        "reviewer_notes_policy_created_here",
        "rating_row_schema_fixed",
        "blocker_row_schema_fixed",
        "reviewer_notes_local_only_policy_fixed",
        "reviewer_free_text_policy_fixed",
        "sanitized_reason_id_required_for_p7_material",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R47 R6/R7 must keep {true_key}=True")
    for false_key in (
        "json_schema_file_created_here",
        "local_review_packet_policy_ready",
        "policy_ready",
        "r47_policy_ready",
        "p5_human_blind_qa_start_allowed_after_r6_r7",
        "p5_human_blind_qa_confirmed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_limited_human_readfeel_confirmed",
        "real_device_modal_review_start_allowed",
        "real_device_modal_review_confirmed",
        "actual_body_full_packet_generated_here",
        "actual_body_free_manifest_materialized_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_notes_materialized_here",
        "body_full_writer_created_here",
        "disposal_policy_created_here",
        "actual_human_review_run_here",
        "actual_real_device_review_run_here",
        "local_reviewer_payload_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R47 R6/R7 must keep {false_key}=False")
    if data.get("notes_retention_after_rating_finalized_max_hours") != P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS:
        raise ValueError("R47 R6/R7 notes retention changed")
    return True


def _body_free_disposal_receipt_json_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": P7_R47_BODY_FREE_DISPOSAL_RECEIPT_SCHEMA_VERSION,
        "title": "Cocolon EmlisAI P7-R47 Body-free Disposal Receipt",
        "type": "object",
        "additionalProperties": False,
        "required": list(P7_R47_BODY_FREE_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS),
        "properties": {
            "schema_version": {"const": P7_R47_BODY_FREE_DISPOSAL_RECEIPT_SCHEMA_VERSION},
            "review_session_id": {"type": "string"},
            "packet_kind": {"enum": list(P7_R47_PACKET_KINDS)},
            "case_count": {"type": "integer", "minimum": 0},
            "deleted_file_count": {"type": "integer", "minimum": 0},
            "disposal_status": {"enum": list(P7_R47_DISPOSAL_STATUS_REFS)},
            "body_removed": {"type": "boolean"},
            "reviewer_notes_removed": {"type": "boolean"},
            "local_packet_exported": {"const": False},
            "content_hash_of_body_stored": {"const": False},
            "body_free": {"const": True},
            "release_allowed": {"const": False},
            "p7_complete": {"const": False},
            "p8_start_allowed": {"const": False},
            "hold004_close_allowed": {"const": False},
        },
    }


def build_p7_r47_body_free_disposal_receipt_schema(*, material_id: Any = "p7_r47_body_free_disposal_receipt_schema") -> dict[str, Any]:
    schema = {
        "schema_version": P7_R47_BODY_FREE_DISPOSAL_RECEIPT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R47_LOCAL_REVIEW_PACKET_STEP,
        "scope": P7_R47_LOCAL_REVIEW_PACKET_SCOPE,
        "policy_kind": P7_R47_POLICY_KIND,
        "policy_section": "R8_body_free_disposal_receipt_schema",
        "material_id": clean_identifier(material_id, default="p7_r47_body_free_disposal_receipt_schema", max_length=160),
        "current_phase": "P7",
        "schema_kind": "body_free_disposal_receipt_schema",
        "schema_definition_only": True,
        "json_schema_file_created_here": False,
        "disposal_receipt_required": True,
        "required_field_refs": list(P7_R47_BODY_FREE_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS),
        "receipt_required_field_refs": list(P7_R47_BODY_FREE_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS),
        "optional_field_refs": list(P7_R47_BODY_FREE_DISPOSAL_RECEIPT_OPTIONAL_FIELD_REFS),
        "packet_kind_enum": list(P7_R47_PACKET_KINDS),
        "disposal_status_enum": list(P7_R47_DISPOSAL_STATUS_REFS),
        "forbidden_field_refs": list(P7_R47_DISPOSAL_RECEIPT_FORBIDDEN_FIELD_REFS),
        "receipt_forbidden_field_refs": list(P7_R47_DISPOSAL_RECEIPT_FORBIDDEN_FIELD_REFS),
        "content_hash_of_body_allowed": False,
        "content_hash_of_body_stored": False,
        "body_full_file_content_hash_allowed": False,
        "raw_text_hash_allowed": False,
        "comment_text_hash_allowed": False,
        "local_absolute_path_included": False,
        "reviewer_free_text_included": False,
        "local_packet_exported": False,
        "body_full_packet_export_allowed": False,
        "body_free_disposal_receipt_schema_created_here": True,
        "actual_disposal_run_here": False,
        "actual_cleanup_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "body_full_writer_created_here": False,
        "json_schema": _body_free_disposal_receipt_json_schema(),
        "receipt_json_schema": _body_free_disposal_receipt_json_schema(),
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
    }
    assert_p7_r47_body_free_disposal_receipt_schema_contract(schema)
    return schema


def build_p7_r47_disposal_cleanup_retention_policy(*, material_id: Any = "p7_r47_disposal_cleanup_retention_policy") -> dict[str, Any]:
    policy = {
        "schema_version": P7_R47_DISPOSAL_CLEANUP_RETENTION_POLICY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R47_LOCAL_REVIEW_PACKET_STEP,
        "scope": P7_R47_LOCAL_REVIEW_PACKET_SCOPE,
        "policy_kind": P7_R47_POLICY_KIND,
        "policy_section": "R8_disposal_cleanup_retention_policy",
        "material_id": clean_identifier(material_id, default="p7_r47_disposal_cleanup_retention_policy", max_length=160),
        "current_phase": "P7",
        "disposal_cleanup_retention_policy_fixed": True,
        "disposal_policy_fixed": True,
        "body_full_packet_retention_max_hours": P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
        "reviewer_notes_retention_after_rating_finalized_max_hours": P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
        "shorter_retention_trigger_wins": True,
        "rating_finalized_requires_immediate_purge": True,
        "rating_finalized_requires_purge_required": True,
        "body_full_packet_delete_trigger_refs": list(P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS),
        "disposal_status_enum": list(P7_R47_DISPOSAL_STATUS_REFS),
        "body_free_disposal_receipt_schema_version": P7_R47_BODY_FREE_DISPOSAL_RECEIPT_SCHEMA_VERSION,
        "disposal_receipt_required": True,
        "disposal_receipt_body_free": True,
        "body_removed_required_before_handoff_close": True,
        "body_removed_required_before_p5_human_blind_qa_confirmed": True,
        "body_removed_required_before_p6_limited_human_readfeel_confirmed": True,
        "body_removed_required_before_p5_p6_review_confirmed": True,
        "body_removed_required_before_hold_close": True,
        "content_hash_of_body_allowed": False,
        "content_hash_of_body_stored": False,
        "body_full_file_content_hash_allowed": False,
        "raw_text_hash_allowed": False,
        "comment_text_hash_allowed": False,
        "deleted_body_preview_allowed": False,
        "terminal_full_output_allowed": False,
        "traceback_full_output_allowed": False,
        "local_absolute_path_included": False,
        "reviewer_free_text_included": False,
        "local_packet_exported": False,
        "p7_material_body_free_required": True,
        "p5_human_blind_qa_confirmed_without_body_removed_allowed": False,
        "p6_limited_human_readfeel_confirmed_without_body_removed_allowed": False,
        "hold004_close_without_disposal_verified_allowed": False,
        "body_free_disposal_receipt_export_allowed_later": True,
        "actual_disposal_run_here": False,
        "actual_cleanup_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_notes_materialized_here": False,
        "body_full_writer_created_here": False,
        "disposal_policy_created_here": True,
        "body_free_disposal_receipt_schema_created_here": True,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "real_device_modal_review_confirmed": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
    }
    assert_p7_r47_disposal_cleanup_retention_policy_contract(policy)
    return policy


def build_p7_r47_p5_human_blind_qa_packet_policy(*, material_id: Any = "p7_r47_p5_human_blind_qa_packet_policy") -> dict[str, Any]:
    policy = {
        "schema_version": P7_R47_P5_HUMAN_BLIND_QA_PACKET_POLICY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R47_LOCAL_REVIEW_PACKET_STEP,
        "scope": P7_R47_LOCAL_REVIEW_PACKET_SCOPE,
        "policy_kind": P7_R47_POLICY_KIND,
        "policy_section": "R9_p5_human_blind_qa_packet_policy",
        "material_id": clean_identifier(material_id, default="p7_r47_p5_human_blind_qa_packet_policy", max_length=160),
        "current_phase": "P7",
        "p5_human_blind_qa_packet_policy_fixed": True,
        "packet_kind": "p5_human_blind_qa_local_review_packet",
        "packet_kind_enum": list(P7_R47_PACKET_KINDS),
        "review_kind": P7_R47_P5_REVIEW_KIND,
        "p5_family_refs": list(P5_HUMAN_BLIND_QA_FAMILIES),
        "review_family_refs": list(P5_HUMAN_BLIND_QA_FAMILIES),
        "p5_rating_axis_refs": list(P5_HUMAN_BLIND_QA_RATING_AXES),
        "rating_axis_refs": list(P5_HUMAN_BLIND_QA_RATING_AXES),
        "p5_target_thresholds": dict(P5_HUMAN_BLIND_QA_TARGETS),
        "rating_axis_target_thresholds": dict(P5_HUMAN_BLIND_QA_TARGETS),
        "first_formal_review_minimum_total_cases": P7_R47_P5_FIRST_FORMAL_REVIEW_MINIMUM_TOTAL_CASES,
        "first_formal_review_minimum_per_family": P7_R47_P5_FIRST_FORMAL_REVIEW_MINIMUM_PER_FAMILY,
        "minimum_history_line_eligible_input_cases": P7_R47_P5_MINIMUM_HISTORY_LINE_ELIGIBLE_INPUT_CASES,
        "minimum_owned_history_positive_cases": P7_R47_P5_MINIMUM_OWNED_HISTORY_POSITIVE_CASES,
        "minimum_block_boundary_case_counts": dict(P7_R47_P5_MINIMUM_BLOCK_BOUNDARY_CASE_COUNTS),
        "first_formal_review_minimums": {
            "minimum_total_cases": P7_R47_P5_FIRST_FORMAL_REVIEW_MINIMUM_TOTAL_CASES,
            "minimum_per_family": P7_R47_P5_FIRST_FORMAL_REVIEW_MINIMUM_PER_FAMILY,
            "minimum_history_line_eligible_input": P7_R47_P5_MINIMUM_HISTORY_LINE_ELIGIBLE_INPUT_CASES,
            "minimum_owned_history_positive_cases": P7_R47_P5_MINIMUM_OWNED_HISTORY_POSITIVE_CASES,
            "minimum_block_boundary_cases": dict(P7_R47_P5_MINIMUM_BLOCK_BOUNDARY_CASE_COUNTS),
        },
        "max_history_record_surfaces": P7_R47_P5_MAX_HISTORY_RECORD_SURFACES,
        "min_evidence_record_count_when_history_line_expected": P7_R47_P5_MIN_EVIDENCE_RECORD_COUNT_WHEN_HISTORY_LINE_EXPECTED,
        "history_record_identifier_policy": "no_db_id_no_user_id",
        "created_at_policy": "bucketed_or_relative_only",
        "raw_memo_full_dump_allowed": False,
        "history_summary_style": "bounded_review_surface_local_only",
        "bounded_owned_history_review_surface_policy": {
            "max_history_record_surfaces": P7_R47_P5_MAX_HISTORY_RECORD_SURFACES,
            "min_evidence_record_count_when_history_line_expected": P7_R47_P5_MIN_EVIDENCE_RECORD_COUNT_WHEN_HISTORY_LINE_EXPECTED,
            "history_record_identifier_policy": "no_db_id_no_user_id",
            "created_at_policy": "bucketed_or_relative_only",
            "raw_memo_full_dump_allowed": False,
            "history_summary_style": "bounded_review_surface_local_only",
        },
        "free_tier_boundary_family_ref": "free_tier_history_present_not_allowed",
        "low_information_boundary_family_ref": "low_information_history_not_eligible",
        "reviewer_facing_identifier_policy": "blind_case_id_only",
        "reviewer_facing_allowed_field_refs": list(P7_R47_P5_REVIEWER_FACING_ALLOWED_FIELD_REFS),
        "reviewer_facing_forbidden_field_refs": list(P7_R47_P5_REVIEWER_FACING_FORBIDDEN_FIELD_REFS),
        "family_visible_to_reviewer_allowed": False,
        "reviewer_facing_family_visible_allowed": False,
        "subscription_tier_visible_to_reviewer_allowed": False,
        "expected_result_visible_to_reviewer_allowed": False,
        "eligible_flag_visible_to_reviewer_allowed": False,
        "visible_applied_visible_to_reviewer_allowed": False,
        "gate_result_visible_to_reviewer_allowed": False,
        "case_ref_visible_to_reviewer_allowed": False,
        "user_or_db_identifier_visible_to_reviewer_allowed": False,
        "public_meta_in_reviewer_payload_allowed": False,
        "free_tier_history_boundary_required": True,
        "low_information_history_boundary_required": True,
        "bounded_history_surface_local_only": True,
        "body_full_packet_export_allowed": False,
        "body_free_rating_rows_required_later": True,
        "disposal_receipt_required_before_p5_confirmed": True,
        "body_removed_required_before_p5_confirmed": True,
        "p5_human_blind_qa_packet_generation_allowed_here": False,
        "p5_human_blind_qa_start_allowed_after_r9": False,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "real_device_modal_review_start_allowed": False,
        "real_device_modal_review_confirmed": False,
        "actual_body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "body_full_writer_created_here": False,
        "local_reviewer_payload_materialized_here": False,
        "p5_human_blind_qa_packet_policy_created_here": True,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
    }
    assert_p7_r47_p5_human_blind_qa_packet_policy_contract(policy)
    return policy


def build_p7_r47_r8_r9_disposal_p5_packet_policy_freeze(
    *,
    r6_r7_rating_blocker_notes_policy_freeze: Mapping[str, Any] | None = None,
    local_review_root: Any = None,
    repo_roots: Sequence[Any] | None = None,
    export_roots: Sequence[Any] | None = None,
    material_id: Any = "p7_r47_r8_r9_disposal_p5_packet_policy_freeze",
) -> dict[str, Any]:
    r6_r7 = (
        safe_mapping(r6_r7_rating_blocker_notes_policy_freeze)
        if r6_r7_rating_blocker_notes_policy_freeze is not None
        else build_p7_r47_r6_r7_rating_blocker_notes_policy_freeze(
            local_review_root=local_review_root,
            repo_roots=repo_roots,
            export_roots=export_roots,
        )
    )
    assert_p7_r47_r6_r7_rating_blocker_notes_policy_freeze_contract(r6_r7)
    if r6_r7_rating_blocker_notes_policy_freeze is not None:
        _assert_r47_body_free(r6_r7, source="p7_r47.r6_r7_rating_blocker_notes_policy_freeze")
    disposal_policy = build_p7_r47_disposal_cleanup_retention_policy()
    disposal_receipt_schema = build_p7_r47_body_free_disposal_receipt_schema()
    p5_policy = build_p7_r47_p5_human_blind_qa_packet_policy()
    freeze = {
        "schema_version": P7_R47_R8_R9_DISPOSAL_P5_PACKET_POLICY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R47_LOCAL_REVIEW_PACKET_STEP,
        "scope": P7_R47_LOCAL_REVIEW_PACKET_SCOPE,
        "policy_kind": P7_R47_POLICY_KIND,
        "material_id": clean_identifier(material_id, default="p7_r47_r8_r9_disposal_p5_packet_policy_freeze", max_length=160),
        "policy_section": "R8_R9_disposal_p5_packet_policy_freeze",
        "current_phase": "P7",
        "implemented_steps": list(P7_R47_R8_R9_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R47_R8_R9_NOT_YET_IMPLEMENTED_STEPS),
        "r6_r7_rating_blocker_notes_policy_freeze": r6_r7,
        "disposal_cleanup_retention_policy_schema_version": disposal_policy["schema_version"],
        "disposal_cleanup_retention_policy_fixed": True,
        "disposal_policy_fixed": True,
        "disposal_policy_fixed": True,
        "body_full_packet_retention_max_hours": P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
        "reviewer_notes_retention_after_rating_finalized_max_hours": P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
        "body_free_disposal_receipt_schema_version": disposal_receipt_schema["schema_version"],
        "body_free_disposal_receipt_schema_fixed": True,
        "p5_human_blind_qa_packet_policy_schema_version": p5_policy["schema_version"],
        "p5_human_blind_qa_packet_policy_fixed": True,
        "p5_first_formal_review_minimum_total_cases": P7_R47_P5_FIRST_FORMAL_REVIEW_MINIMUM_TOTAL_CASES,
        "p5_first_formal_minimum_total_cases": P7_R47_P5_FIRST_FORMAL_REVIEW_MINIMUM_TOTAL_CASES,
        "p5_bounded_history_max_record_surfaces": P7_R47_P5_MAX_HISTORY_RECORD_SURFACES,
        "p5_family_refs": list(P5_HUMAN_BLIND_QA_FAMILIES),
        "p5_rating_axis_refs": list(P5_HUMAN_BLIND_QA_RATING_AXES),
        "first_next_work_ref": P7_R47_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R47_R8_R9_NEXT_REQUIRED_STEP_REF,
        "packet_kind_enum": list(P7_R47_PACKET_KINDS),
        "r0_current_source_handoff_hold_refrozen": True,
        "r1_scope_packet_kind_enum_fixed": True,
        "local_review_packet_storage_policy_fixed": True,
        "export_denylist_policy_fixed": True,
        "git_zip_mixing_prevention_policy_fixed": True,
        "body_full_packet_schema_created_here": True,
        "body_free_manifest_schema_created_here": True,
        "rating_row_schema_created_here": True,
        "blocker_row_schema_created_here": True,
        "reviewer_notes_policy_created_here": True,
        "disposal_policy_created_here": True,
        "body_free_disposal_receipt_schema_created_here": True,
        "p5_human_blind_qa_packet_policy_created_here": True,
        "json_schema_file_created_here": False,
        "local_review_packet_policy_ready": False,
        "policy_ready": False,
        "r47_policy_ready": False,
        "p5_human_blind_qa_start_allowed_after_r8_r9": False,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "real_device_modal_review_start_allowed": False,
        "real_device_modal_review_confirmed": False,
        "actual_body_full_packet_generated_here": False,
        "actual_body_free_manifest_materialized_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_notes_materialized_here": False,
        "actual_disposal_run_here": False,
        "actual_cleanup_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "body_full_writer_created_here": False,
        "actual_human_review_run_here": False,
        "actual_real_device_review_run_here": False,
        "local_reviewer_payload_materialized_here": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
    }
    assert_p7_r47_r8_r9_disposal_p5_packet_policy_freeze_contract(freeze)
    return freeze


def assert_p7_r47_body_free_disposal_receipt_schema_contract(schema: Mapping[str, Any]) -> bool:
    data = safe_mapping(schema)
    _assert_common(data, schema_version=P7_R47_BODY_FREE_DISPOSAL_RECEIPT_SCHEMA_VERSION, source="p7_r47_r8_body_free_disposal_receipt_schema")
    if data.get("policy_section") != "R8_body_free_disposal_receipt_schema":
        raise ValueError("R47 R8 disposal receipt schema policy section changed")
    for true_key in ("schema_definition_only", "disposal_receipt_required", "body_free_disposal_receipt_schema_created_here"):
        if data.get(true_key) is not True:
            raise ValueError(f"R47 R8 disposal receipt schema must keep {true_key}=True")
    for false_key in (
        "json_schema_file_created_here", "content_hash_of_body_stored", "body_full_file_content_hash_allowed", "raw_text_hash_allowed", "comment_text_hash_allowed", "local_absolute_path_included", "reviewer_free_text_included", "local_packet_exported", "actual_disposal_run_here", "actual_body_full_packet_generated_here", "actual_human_review_run_here", "body_full_writer_created_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R47 R8 disposal receipt schema must keep {false_key}=False")
    if tuple(data.get("required_field_refs") or ()) != P7_R47_BODY_FREE_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS:
        raise ValueError("R47 R8 disposal receipt required fields changed")
    if tuple(data.get("optional_field_refs") or ()) != P7_R47_BODY_FREE_DISPOSAL_RECEIPT_OPTIONAL_FIELD_REFS:
        raise ValueError("R47 R8 disposal receipt optional fields changed")
    if tuple(data.get("packet_kind_enum") or ()) != P7_R47_PACKET_KINDS:
        raise ValueError("R47 R8 disposal receipt packet kind enum changed")
    if tuple(data.get("disposal_status_enum") or ()) != P7_R47_DISPOSAL_STATUS_REFS:
        raise ValueError("R47 R8 disposal status enum changed")
    bad_property_names = _forbidden_schema_property_names(safe_mapping(data.get("json_schema")), P7_R47_DISPOSAL_RECEIPT_FORBIDDEN_FIELD_REFS)
    if bad_property_names:
        raise ValueError(f"R47 R8 disposal receipt schema allows body fields: {bad_property_names}")
    return True


def assert_p7_r47_disposal_cleanup_retention_policy_contract(policy: Mapping[str, Any]) -> bool:
    data = safe_mapping(policy)
    _assert_common(data, schema_version=P7_R47_DISPOSAL_CLEANUP_RETENTION_POLICY_SCHEMA_VERSION, source="p7_r47_r8_disposal_cleanup_retention_policy")
    if data.get("policy_section") != "R8_disposal_cleanup_retention_policy":
        raise ValueError("R47 R8 disposal policy section changed")
    for true_key in (
        "disposal_cleanup_retention_policy_fixed", "shorter_retention_trigger_wins", "rating_finalized_requires_immediate_purge", "disposal_receipt_required", "body_removed_required_before_handoff_close", "body_removed_required_before_p5_human_blind_qa_confirmed", "body_removed_required_before_p6_limited_human_readfeel_confirmed", "body_removed_required_before_hold_close", "p7_material_body_free_required", "body_free_disposal_receipt_export_allowed_later", "disposal_policy_created_here", "body_free_disposal_receipt_schema_created_here",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R47 R8 disposal policy must keep {true_key}=True")
    for false_key in (
        "content_hash_of_body_allowed", "content_hash_of_body_stored", "body_full_file_content_hash_allowed", "raw_text_hash_allowed", "comment_text_hash_allowed", "deleted_body_preview_allowed", "terminal_full_output_allowed", "traceback_full_output_allowed", "local_absolute_path_included", "reviewer_free_text_included", "local_packet_exported", "p5_human_blind_qa_confirmed_without_body_removed_allowed", "p6_limited_human_readfeel_confirmed_without_body_removed_allowed", "hold004_close_without_disposal_verified_allowed", "actual_disposal_run_here", "actual_body_full_packet_generated_here", "actual_human_review_run_here", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_notes_materialized_here", "body_full_writer_created_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R47 R8 disposal policy must keep {false_key}=False")
    if data.get("body_full_packet_retention_max_hours") != P7_R47_BODY_FULL_PACKET_RETENTION_HOURS:
        raise ValueError("R47 R8 body-full retention changed")
    if data.get("reviewer_notes_retention_after_rating_finalized_max_hours") != P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS:
        raise ValueError("R47 R8 reviewer notes retention changed")
    if tuple(data.get("body_full_packet_delete_trigger_refs") or ()) != P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS:
        raise ValueError("R47 R8 delete triggers changed")
    if tuple(data.get("disposal_status_enum") or ()) != P7_R47_DISPOSAL_STATUS_REFS:
        raise ValueError("R47 R8 disposal status enum changed")
    return True


def assert_p7_r47_body_free_disposal_receipt_payload_contract(receipt: Mapping[str, Any]) -> bool:
    data = safe_mapping(receipt)
    allowed_keys = set(P7_R47_BODY_FREE_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS) | set(P7_R47_BODY_FREE_DISPOSAL_RECEIPT_OPTIONAL_FIELD_REFS)
    if not set(P7_R47_BODY_FREE_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS).issubset(data):
        raise ValueError("R47 disposal receipt payload missing required fields")
    if set(data) - allowed_keys:
        raise ValueError("R47 disposal receipt payload contains non-body-free or unsupported fields")
    if data.get("schema_version") != P7_R47_BODY_FREE_DISPOSAL_RECEIPT_SCHEMA_VERSION:
        raise ValueError("unexpected R47 disposal receipt schema_version")
    if data.get("packet_kind") not in P7_R47_PACKET_KIND_SET:
        raise ValueError("R47 disposal receipt packet kind is not fixed enum")
    for integer_key in ("case_count", "deleted_file_count"):
        value = data.get(integer_key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"R47 disposal receipt {integer_key} must be a non-negative integer")
    status = data.get("disposal_status")
    if status not in P7_R47_DISPOSAL_STATUS_REFS:
        raise ValueError("R47 disposal receipt status enum changed")
    for boolean_key in ("body_removed", "reviewer_notes_removed"):
        if not isinstance(data.get(boolean_key), bool):
            raise ValueError(f"R47 disposal receipt {boolean_key} must be boolean")
    for false_key in ("local_packet_exported", "content_hash_of_body_stored", "release_allowed", "p7_complete", "p8_start_allowed", "hold004_close_allowed"):
        if data.get(false_key) is not False:
            raise ValueError(f"R47 disposal receipt must keep {false_key}=False")
    if data.get("body_free") is not True:
        raise ValueError("R47 disposal receipt must be body-free")
    if "p7_material_body_free" in data and data.get("p7_material_body_free") is not True:
        raise ValueError("R47 disposal receipt optional P7 material marker must be body-free")
    if status in {"BODY_PURGED", "DISPOSAL_VERIFIED", "EXPIRED_PURGED"} and data.get("body_removed") is not True:
        raise ValueError("R47 purged/verified disposal receipt must set body_removed=True")
    if status == "DISPOSAL_VERIFIED" and data.get("reviewer_notes_removed") is not True:
        raise ValueError("R47 verified disposal receipt must remove reviewer notes")
    _assert_r47_body_free(data, source="p7_r47_body_free_disposal_receipt_payload")
    return True


def assert_p7_r47_p5_human_blind_qa_packet_policy_contract(policy: Mapping[str, Any]) -> bool:
    data = safe_mapping(policy)
    _assert_common(data, schema_version=P7_R47_P5_HUMAN_BLIND_QA_PACKET_POLICY_SCHEMA_VERSION, source="p7_r47_r9_p5_human_blind_qa_packet_policy")
    if data.get("policy_section") != "R9_p5_human_blind_qa_packet_policy":
        raise ValueError("R47 R9 P5 policy section changed")
    for true_key in ("p5_human_blind_qa_packet_policy_fixed", "free_tier_history_boundary_required", "low_information_history_boundary_required", "bounded_history_surface_local_only", "body_free_rating_rows_required_later", "disposal_receipt_required_before_p5_confirmed", "body_removed_required_before_p5_confirmed", "p5_human_blind_qa_packet_policy_created_here"):
        if data.get(true_key) is not True:
            raise ValueError(f"R47 R9 P5 policy must keep {true_key}=True")
    for false_key in ("raw_memo_full_dump_allowed", "family_visible_to_reviewer_allowed", "reviewer_facing_family_visible_allowed", "subscription_tier_visible_to_reviewer_allowed", "expected_result_visible_to_reviewer_allowed", "eligible_flag_visible_to_reviewer_allowed", "visible_applied_visible_to_reviewer_allowed", "gate_result_visible_to_reviewer_allowed", "case_ref_visible_to_reviewer_allowed", "user_or_db_identifier_visible_to_reviewer_allowed", "public_meta_in_reviewer_payload_allowed", "body_full_packet_export_allowed", "p5_human_blind_qa_packet_generation_allowed_here", "p5_human_blind_qa_start_allowed_after_r9", "p5_human_blind_qa_confirmed", "p6_limited_human_readfeel_start_allowed", "p6_limited_human_readfeel_confirmed", "real_device_modal_review_start_allowed", "real_device_modal_review_confirmed", "actual_body_full_packet_generated_here", "actual_human_review_run_here", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "body_full_writer_created_here", "local_reviewer_payload_materialized_here"):
        if data.get(false_key) is not False:
            raise ValueError(f"R47 R9 P5 policy must keep {false_key}=False")
    if data.get("packet_kind") != "p5_human_blind_qa_local_review_packet":
        raise ValueError("R47 R9 P5 packet kind changed")
    if tuple(data.get("p5_family_refs") or ()) != P5_HUMAN_BLIND_QA_FAMILIES:
        raise ValueError("R47 R9 P5 family refs must match R46 handoff")
    if tuple(data.get("p5_rating_axis_refs") or ()) != P5_HUMAN_BLIND_QA_RATING_AXES:
        raise ValueError("R47 R9 P5 rating axes must match R46 handoff")
    if safe_mapping(data.get("p5_target_thresholds")) != P5_HUMAN_BLIND_QA_TARGETS:
        raise ValueError("R47 R9 P5 targets must match R46 handoff")
    if tuple(data.get("review_family_refs") or ()) != P5_HUMAN_BLIND_QA_FAMILIES:
        raise ValueError("R47 R9 P5 review family refs must match R46 handoff")
    if tuple(data.get("rating_axis_refs") or ()) != P5_HUMAN_BLIND_QA_RATING_AXES:
        raise ValueError("R47 R9 P5 rating axis refs must match R46 handoff")
    if safe_mapping(data.get("rating_axis_target_thresholds")) != P5_HUMAN_BLIND_QA_TARGETS:
        raise ValueError("R47 R9 P5 rating axis thresholds must match R46 handoff")
    if safe_mapping(data.get("first_formal_review_minimums")) != P7_R47_P5_FIRST_FORMAL_MINIMUMS:
        raise ValueError("R47 R9 P5 first formal review minimums changed")
    history_policy = safe_mapping(data.get("bounded_owned_history_review_surface_policy"))
    if history_policy != P7_R47_P5_HISTORY_SURFACE_POLICY:
        raise ValueError("R47 R9 P5 bounded history review surface policy changed")
    if data.get("first_formal_review_minimum_total_cases") != P7_R47_P5_FIRST_FORMAL_REVIEW_MINIMUM_TOTAL_CASES:
        raise ValueError("R47 R9 P5 first formal review total changed")
    if data.get("first_formal_review_minimum_per_family") != P7_R47_P5_FIRST_FORMAL_REVIEW_MINIMUM_PER_FAMILY:
        raise ValueError("R47 R9 P5 per-family minimum changed")
    if data.get("max_history_record_surfaces") != P7_R47_P5_MAX_HISTORY_RECORD_SURFACES:
        raise ValueError("R47 R9 P5 history surface max changed")
    if data.get("reviewer_facing_identifier_policy") != "blind_case_id_only":
        raise ValueError("R47 R9 P5 blind identifier policy changed")
    if tuple(data.get("reviewer_facing_allowed_field_refs") or ()) != P7_R47_P5_REVIEWER_FACING_ALLOWED_FIELD_REFS:
        raise ValueError("R47 R9 P5 reviewer allowed field refs changed")
    forbidden = set(dedupe_identifiers(data.get("reviewer_facing_forbidden_field_refs"), limit=120, max_length=160))
    if set(P7_R47_P5_REVIEWER_FACING_FORBIDDEN_FIELD_REFS) - forbidden:
        raise ValueError("R47 R9 P5 reviewer forbidden refs lost coverage")
    if set(data.get("reviewer_facing_allowed_field_refs") or ()) & forbidden:
        raise ValueError("R47 R9 P5 reviewer allowed refs must not overlap forbidden refs")
    return True


def assert_p7_r47_r8_r9_disposal_p5_packet_policy_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_common(data, schema_version=P7_R47_R8_R9_DISPOSAL_P5_PACKET_POLICY_SCHEMA_VERSION, source="p7_r47_r8_r9_disposal_p5_packet_policy_freeze")
    if data.get("policy_section") != "R8_R9_disposal_p5_packet_policy_freeze":
        raise ValueError("R47 R8/R9 policy section changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R47_R8_R9_IMPLEMENTED_STEPS:
        raise ValueError("R47 R8/R9 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R47_R8_R9_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R47 R8/R9 not-yet-implemented steps changed")
    assert_p7_r47_r6_r7_rating_blocker_notes_policy_freeze_contract(safe_mapping(data.get("r6_r7_rating_blocker_notes_policy_freeze")))
    if data.get("next_required_step") != P7_R47_R8_R9_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R47 R8/R9 must point to R10 as next required step")
    for true_key in ("disposal_cleanup_retention_policy_fixed", "disposal_policy_fixed", "body_free_disposal_receipt_schema_fixed", "p5_human_blind_qa_packet_policy_fixed", "disposal_policy_created_here", "body_free_disposal_receipt_schema_created_here", "p5_human_blind_qa_packet_policy_created_here"):
        if data.get(true_key) is not True:
            raise ValueError(f"R47 R8/R9 must keep {true_key}=True")
    for false_key in ("json_schema_file_created_here", "local_review_packet_policy_ready", "policy_ready", "r47_policy_ready", "p5_human_blind_qa_start_allowed_after_r8_r9", "p5_human_blind_qa_confirmed", "p6_limited_human_readfeel_start_allowed", "p6_limited_human_readfeel_confirmed", "real_device_modal_review_start_allowed", "real_device_modal_review_confirmed", "actual_body_full_packet_generated_here", "actual_body_free_manifest_materialized_here", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_notes_materialized_here", "actual_disposal_run_here", "actual_cleanup_run_here", "actual_disposal_receipt_materialized_here", "body_full_writer_created_here", "actual_human_review_run_here", "actual_real_device_review_run_here", "local_reviewer_payload_materialized_here"):
        if data.get(false_key) is not False:
            raise ValueError(f"R47 R8/R9 must keep {false_key}=False")
    if data.get("p5_first_formal_review_minimum_total_cases") != P7_R47_P5_FIRST_FORMAL_REVIEW_MINIMUM_TOTAL_CASES:
        raise ValueError("R47 R8/R9 P5 minimum total changed")
    if data.get("p5_first_formal_minimum_total_cases") != P7_R47_P5_FIRST_FORMAL_REVIEW_MINIMUM_TOTAL_CASES:
        raise ValueError("R47 R8/R9 P5 minimum total alias changed")
    if data.get("p5_bounded_history_max_record_surfaces") != P7_R47_P5_MAX_HISTORY_RECORD_SURFACES:
        raise ValueError("R47 R8/R9 P5 bounded history max changed")
    return True


def build_p7_r47_p6_limited_human_readfeel_packet_policy(
    *,
    material_id: Any = "p7_r47_p6_limited_human_readfeel_packet_policy",
) -> dict[str, Any]:
    policy = {
        "schema_version": P7_R47_P6_LIMITED_HUMAN_READFEEL_PACKET_POLICY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R47_LOCAL_REVIEW_PACKET_STEP,
        "scope": P7_R47_LOCAL_REVIEW_PACKET_SCOPE,
        "policy_kind": P7_R47_POLICY_KIND,
        "policy_section": "R10_p6_limited_human_readfeel_packet_policy",
        "material_id": clean_identifier(material_id, default="p7_r47_p6_limited_human_readfeel_packet_policy", max_length=160),
        "current_phase": "P7",
        "p6_limited_human_readfeel_packet_policy_fixed": True,
        "packet_kind": "p6_limited_human_readfeel_local_review_packet",
        "packet_kind_enum": list(P7_R47_PACKET_KINDS),
        "review_kind": P7_R47_P6_REVIEW_KIND,
        "p6_review_family_refs": list(P6_LIMITED_READFEEL_REVIEW_FAMILIES),
        "review_family_refs": list(P6_LIMITED_READFEEL_REVIEW_FAMILIES),
        "p6_no_connect_family_refs": list(P6_NO_CONNECT_FAMILIES),
        "no_connect_family_refs": list(P6_NO_CONNECT_FAMILIES),
        "p6_rating_axis_refs": list(P6_LIMITED_READFEEL_RATING_AXES),
        "rating_axis_refs": list(P6_LIMITED_READFEEL_RATING_AXES),
        "p6_target_thresholds": dict(P6_LIMITED_READFEEL_TARGETS),
        "rating_axis_target_thresholds": dict(P6_LIMITED_READFEEL_TARGETS),
        "first_formal_review_minimum_total_cases": P7_R47_P6_FIRST_FORMAL_REVIEW_MINIMUM_TOTAL_CASES,
        "minimum_review_family_case_counts": dict(P7_R47_P6_MINIMUM_REVIEW_FAMILY_CASE_COUNTS),
        "minimum_no_connect_audit_case_counts": dict(P7_R47_P6_MINIMUM_NO_CONNECT_AUDIT_CASE_COUNTS),
        "first_formal_review_minimums": {
            "minimum_total_cases": P7_R47_P6_FIRST_FORMAL_REVIEW_MINIMUM_TOTAL_CASES,
            "minimum_review_family_cases": dict(P7_R47_P6_MINIMUM_REVIEW_FAMILY_CASE_COUNTS),
            "minimum_no_connect_audit_cases": dict(P7_R47_P6_MINIMUM_NO_CONNECT_AUDIT_CASE_COUNTS),
        },
        "p5_human_blind_qa_confirmed_required_before_p6_start": True,
        "p5_body_full_packets_removed_required_before_p6_start": True,
        "p5_body_free_rating_rows_ready_required_before_p6_start": True,
        "p5_red_or_repair_blockers_triaged_required_before_p6_start": True,
        "p6_waits_for_p5_confirmation": True,
        "p6_is_not_p5_history_line_substitute": True,
        "no_connect_family_audit_required": True,
        "no_connect_family_insight_leak_allowed": False,
        "visible_expansion_allowed": False,
        "visible_expansion_requires_future_design": True,
        "history_used_as_fact_allowed": False,
        "p5_history_line_substitution_allowed": False,
        "diagnostic_label_allowed": False,
        "advice_pressure_allowed": False,
        "reviewer_facing_identifier_policy": "blind_case_id_only",
        "reviewer_facing_allowed_field_refs": list(P7_R47_P6_REVIEWER_FACING_ALLOWED_FIELD_REFS),
        "reviewer_facing_forbidden_field_refs": list(P7_R47_P6_REVIEWER_FACING_FORBIDDEN_FIELD_REFS),
        "family_visible_to_reviewer_allowed": False,
        "subscription_tier_visible_to_reviewer_allowed": False,
        "expected_result_visible_to_reviewer_allowed": False,
        "eligible_flag_visible_to_reviewer_allowed": False,
        "visible_applied_visible_to_reviewer_allowed": False,
        "gate_result_visible_to_reviewer_allowed": False,
        "case_ref_visible_to_reviewer_allowed": False,
        "relation_pattern_internal_id_visible_to_reviewer_allowed": False,
        "diagnostic_label_visible_to_reviewer_allowed": False,
        "candidate_internal_body_visible_to_reviewer_allowed": False,
        "public_meta_in_reviewer_payload_allowed": False,
        "body_full_packet_export_allowed": False,
        "body_free_rating_rows_required_later": True,
        "disposal_receipt_required_before_p6_confirmed": True,
        "body_removed_required_before_p6_confirmed": True,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_packet_generation_allowed_here": False,
        "p6_limited_human_readfeel_start_allowed_after_r10": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "real_device_modal_review_start_allowed": False,
        "real_device_modal_review_confirmed": False,
        "actual_body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "body_full_writer_created_here": False,
        "local_reviewer_payload_materialized_here": False,
        "p6_limited_human_readfeel_packet_policy_created_here": True,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
    }
    assert_p7_r47_p6_limited_human_readfeel_packet_policy_contract(policy)
    return policy


def build_p7_r47_real_device_modal_review_packet_policy(
    *,
    material_id: Any = "p7_r47_real_device_modal_review_packet_policy",
) -> dict[str, Any]:
    r46_checklist = build_real_device_submit_modal_readfeel_checklist()
    assert_real_device_submit_modal_readfeel_checklist_contract(r46_checklist)
    r46_readfeel_axes = tuple(safe_mapping(r46_checklist.get("readfeel_axes")).keys())
    policy = {
        "schema_version": P7_R47_REAL_DEVICE_MODAL_REVIEW_PACKET_POLICY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R47_LOCAL_REVIEW_PACKET_STEP,
        "scope": P7_R47_LOCAL_REVIEW_PACKET_SCOPE,
        "policy_kind": P7_R47_POLICY_KIND,
        "policy_section": "R11_real_device_modal_review_packet_policy",
        "material_id": clean_identifier(material_id, default="p7_r47_real_device_modal_review_packet_policy", max_length=160),
        "current_phase": "P7",
        "real_device_modal_review_packet_policy_fixed": True,
        "packet_kind": "real_device_modal_review_local_packet",
        "packet_kind_enum": list(P7_R47_PACKET_KINDS),
        "review_kind": P7_R47_REAL_DEVICE_REVIEW_KIND,
        "required_manual_review_family_refs": list(P7_R47_REAL_DEVICE_REQUIRED_MANUAL_REVIEW_FAMILY_REFS),
        "r46_required_manual_review_family_refs": list(r46_checklist.get("required_manual_review_families") or []),
        "readfeel_axis_refs": list(P7_R47_REAL_DEVICE_READFEEL_AXIS_REFS),
        "r46_readfeel_axis_refs": list(r46_readfeel_axes),
        "minimum_device_contexts": P7_R47_REAL_DEVICE_FIRST_REVIEW_MINIMUMS["minimum_device_contexts"],
        "recommended_device_context_refs": list(P7_R47_REAL_DEVICE_RECOMMENDED_DEVICE_CONTEXT_REFS),
        "minimum_case_per_required_family_per_device": P7_R47_REAL_DEVICE_FIRST_REVIEW_MINIMUMS["minimum_case_per_required_family_per_device"],
        "minimum_total_cases_first_review": P7_R47_REAL_DEVICE_FIRST_REVIEW_MINIMUMS["minimum_total_cases_first_review"],
        "first_review_minimums": dict(P7_R47_REAL_DEVICE_FIRST_REVIEW_MINIMUMS),
        "reviewer_facing_identifier_policy": "blind_case_id_only",
        "reviewer_facing_allowed_field_refs": list(P7_R47_REAL_DEVICE_REVIEWER_FACING_ALLOWED_FIELD_REFS),
        "reviewer_facing_forbidden_field_refs": list(P7_R47_REAL_DEVICE_REVIEWER_FACING_FORBIDDEN_FIELD_REFS),
        "visible_payload_source_required": r46_checklist.get("visible_payload_source_required"),
        "visible_payload_source_public_ref": "input_feedback.comment_text",
        "input_feedback_comment_text_source_required": True,
        "rn_title_preserved_required": True,
        "rn_display_condition_preserved_required": True,
        "public_top_level_shape_preserved_required": True,
        "passed_non_empty_comment_text_only_required": True,
        "non_passed_hidden_required": True,
        "device_ref_body_free_only": True,
        "os_ref_body_free_only": True,
        "app_build_ref_body_free_only": True,
        "screenshot_local_only": True,
        "visible_modal_text_local_only": True,
        "modal_layout_note_local_only": True,
        "body_free_readfeel_axes_only": True,
        "screenshot_or_visible_body_export_allowed": False,
        "screenshot_body_p7_material_allowed": False,
        "visible_modal_text_body_p7_material_allowed": False,
        "body_full_packet_export_allowed": False,
        "body_free_checklist_results_required_later": True,
        "disposal_receipt_required_before_real_device_confirmed": True,
        "body_removed_required_before_real_device_confirmed": True,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "rn_display_condition_changed": False,
        "api_route_changed": False,
        "request_key_changed": False,
        "response_shape_changed": False,
        "public_response_key_added": False,
        "api_response_key_added": False,
        "db_schema_changed": False,
        "visible_payload_source_changed": False,
        "gate_relaxed": False,
        "real_device_modal_review_packet_generation_allowed_here": False,
        "real_device_modal_review_start_allowed_after_r11": False,
        "real_device_modal_review_start_allowed": False,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "real_device_modal_review_confirmed": False,
        "manual_real_device_review_confirmed": False,
        "actual_body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "actual_real_device_review_run_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "body_full_writer_created_here": False,
        "local_reviewer_payload_materialized_here": False,
        "real_device_modal_review_packet_policy_created_here": True,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
    }
    assert_p7_r47_real_device_modal_review_packet_policy_contract(policy)
    return policy


def build_p7_r47_r10_r11_p6_real_device_packet_policy_freeze(
    *,
    r8_r9_disposal_p5_packet_policy_freeze: Mapping[str, Any] | None = None,
    local_review_root: Any = None,
    repo_roots: Sequence[Any] | None = None,
    export_roots: Sequence[Any] | None = None,
    material_id: Any = "p7_r47_r10_r11_p6_real_device_packet_policy_freeze",
) -> dict[str, Any]:
    r8_r9 = (
        safe_mapping(r8_r9_disposal_p5_packet_policy_freeze)
        if r8_r9_disposal_p5_packet_policy_freeze is not None
        else build_p7_r47_r8_r9_disposal_p5_packet_policy_freeze(
            local_review_root=local_review_root,
            repo_roots=repo_roots,
            export_roots=export_roots,
        )
    )
    assert_p7_r47_r8_r9_disposal_p5_packet_policy_freeze_contract(r8_r9)
    if r8_r9_disposal_p5_packet_policy_freeze is not None:
        _assert_r47_body_free(r8_r9, source="p7_r47.r8_r9_disposal_p5_packet_policy_freeze")
    p6_policy = build_p7_r47_p6_limited_human_readfeel_packet_policy()
    real_device_policy = build_p7_r47_real_device_modal_review_packet_policy()
    freeze = {
        "schema_version": P7_R47_R10_R11_P6_REAL_DEVICE_PACKET_POLICY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R47_LOCAL_REVIEW_PACKET_STEP,
        "scope": P7_R47_LOCAL_REVIEW_PACKET_SCOPE,
        "policy_kind": P7_R47_POLICY_KIND,
        "material_id": clean_identifier(material_id, default="p7_r47_r10_r11_p6_real_device_packet_policy_freeze", max_length=160),
        "policy_section": "R10_R11_p6_real_device_packet_policy_freeze",
        "current_phase": "P7",
        "implemented_steps": list(P7_R47_R10_R11_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R47_R10_R11_NOT_YET_IMPLEMENTED_STEPS),
        "r8_r9_disposal_p5_packet_policy_freeze": r8_r9,
        "p6_limited_human_readfeel_packet_policy_schema_version": p6_policy["schema_version"],
        "p6_limited_human_readfeel_packet_policy_fixed": True,
        "real_device_modal_review_packet_policy_schema_version": real_device_policy["schema_version"],
        "real_device_modal_review_packet_policy_fixed": True,
        "p6_first_formal_review_minimum_total_cases": P7_R47_P6_FIRST_FORMAL_REVIEW_MINIMUM_TOTAL_CASES,
        "p6_review_family_refs": list(P6_LIMITED_READFEEL_REVIEW_FAMILIES),
        "p6_no_connect_family_refs": list(P6_NO_CONNECT_FAMILIES),
        "p6_rating_axis_refs": list(P6_LIMITED_READFEEL_RATING_AXES),
        "real_device_required_manual_review_family_refs": list(P7_R47_REAL_DEVICE_REQUIRED_MANUAL_REVIEW_FAMILY_REFS),
        "real_device_readfeel_axis_refs": list(P7_R47_REAL_DEVICE_READFEEL_AXIS_REFS),
        "real_device_minimum_total_cases_first_review": P7_R47_REAL_DEVICE_FIRST_REVIEW_MINIMUMS["minimum_total_cases_first_review"],
        "first_next_work_ref": P7_R47_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R47_R10_R11_NEXT_REQUIRED_STEP_REF,
        "packet_kind_enum": list(P7_R47_PACKET_KINDS),
        "r0_current_source_handoff_hold_refrozen": True,
        "r1_scope_packet_kind_enum_fixed": True,
        "local_review_packet_storage_policy_fixed": True,
        "export_denylist_policy_fixed": True,
        "git_zip_mixing_prevention_policy_fixed": True,
        "body_full_packet_schema_created_here": True,
        "body_free_manifest_schema_created_here": True,
        "rating_row_schema_created_here": True,
        "blocker_row_schema_created_here": True,
        "reviewer_notes_policy_created_here": True,
        "disposal_policy_created_here": True,
        "body_free_disposal_receipt_schema_created_here": True,
        "p5_human_blind_qa_packet_policy_created_here": True,
        "p6_limited_human_readfeel_packet_policy_created_here": True,
        "real_device_modal_review_packet_policy_created_here": True,
        "p6_start_gated_by_p5_confirmation": True,
        "real_device_review_queued_after_p5_p6_review": True,
        "json_schema_file_created_here": False,
        "local_review_packet_policy_ready": False,
        "policy_ready": False,
        "r47_policy_ready": False,
        "p5_human_blind_qa_start_allowed_after_r10_r11": False,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed_after_r10_r11": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "real_device_modal_review_start_allowed_after_r10_r11": False,
        "real_device_modal_review_start_allowed": False,
        "real_device_modal_review_confirmed": False,
        "actual_body_full_packet_generated_here": False,
        "actual_body_free_manifest_materialized_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_notes_materialized_here": False,
        "actual_disposal_run_here": False,
        "actual_cleanup_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "body_full_writer_created_here": False,
        "actual_human_review_run_here": False,
        "actual_real_device_review_run_here": False,
        "local_reviewer_payload_materialized_here": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
    }
    assert_p7_r47_r10_r11_p6_real_device_packet_policy_freeze_contract(freeze)
    return freeze


def assert_p7_r47_p6_limited_human_readfeel_packet_policy_contract(policy: Mapping[str, Any]) -> bool:
    data = safe_mapping(policy)
    _assert_common(
        data,
        schema_version=P7_R47_P6_LIMITED_HUMAN_READFEEL_PACKET_POLICY_SCHEMA_VERSION,
        source="p7_r47_r10_p6_limited_human_readfeel_packet_policy",
    )
    if data.get("policy_section") != "R10_p6_limited_human_readfeel_packet_policy":
        raise ValueError("R47 R10 P6 policy section changed")
    for true_key in (
        "p6_limited_human_readfeel_packet_policy_fixed",
        "p5_human_blind_qa_confirmed_required_before_p6_start",
        "p5_body_full_packets_removed_required_before_p6_start",
        "p5_body_free_rating_rows_ready_required_before_p6_start",
        "p5_red_or_repair_blockers_triaged_required_before_p6_start",
        "p6_waits_for_p5_confirmation",
        "p6_is_not_p5_history_line_substitute",
        "no_connect_family_audit_required",
        "visible_expansion_requires_future_design",
        "body_free_rating_rows_required_later",
        "disposal_receipt_required_before_p6_confirmed",
        "body_removed_required_before_p6_confirmed",
        "p6_limited_human_readfeel_packet_policy_created_here",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R47 R10 P6 policy must keep {true_key}=True")
    for false_key in (
        "no_connect_family_insight_leak_allowed",
        "visible_expansion_allowed",
        "history_used_as_fact_allowed",
        "p5_history_line_substitution_allowed",
        "diagnostic_label_allowed",
        "advice_pressure_allowed",
        "family_visible_to_reviewer_allowed",
        "subscription_tier_visible_to_reviewer_allowed",
        "expected_result_visible_to_reviewer_allowed",
        "eligible_flag_visible_to_reviewer_allowed",
        "visible_applied_visible_to_reviewer_allowed",
        "gate_result_visible_to_reviewer_allowed",
        "case_ref_visible_to_reviewer_allowed",
        "relation_pattern_internal_id_visible_to_reviewer_allowed",
        "diagnostic_label_visible_to_reviewer_allowed",
        "candidate_internal_body_visible_to_reviewer_allowed",
        "public_meta_in_reviewer_payload_allowed",
        "body_full_packet_export_allowed",
        "p5_human_blind_qa_confirmed",
        "p6_limited_human_readfeel_packet_generation_allowed_here",
        "p6_limited_human_readfeel_start_allowed_after_r10",
        "p6_limited_human_readfeel_start_allowed",
        "p6_limited_human_readfeel_confirmed",
        "real_device_modal_review_start_allowed",
        "real_device_modal_review_confirmed",
        "actual_body_full_packet_generated_here",
        "actual_human_review_run_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "body_full_writer_created_here",
        "local_reviewer_payload_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R47 R10 P6 policy must keep {false_key}=False")
    for forbidden_key in P7_R47_P6_REVIEWER_FACING_FORBIDDEN_FIELD_REFS:
        if forbidden_key in data:
            raise ValueError(f"R47 R10 P6 policy contains forbidden reviewer/body key: {forbidden_key}")
    if data.get("packet_kind") != "p6_limited_human_readfeel_local_review_packet":
        raise ValueError("R47 R10 P6 packet kind changed")
    if tuple(data.get("review_family_refs") or ()) != P6_LIMITED_READFEEL_REVIEW_FAMILIES:
        raise ValueError("R47 R10 P6 review family refs must match R46 handoff")
    if tuple(data.get("no_connect_family_refs") or ()) != P6_NO_CONNECT_FAMILIES:
        raise ValueError("R47 R10 P6 no-connect family refs must match R46 handoff")
    if tuple(data.get("rating_axis_refs") or ()) != P6_LIMITED_READFEEL_RATING_AXES:
        raise ValueError("R47 R10 P6 rating axes must match R46 handoff")
    if safe_mapping(data.get("rating_axis_target_thresholds")) != P6_LIMITED_READFEEL_TARGETS:
        raise ValueError("R47 R10 P6 rating thresholds must match R46 handoff")
    if safe_mapping(data.get("first_formal_review_minimums")) != P7_R47_P6_FIRST_FORMAL_MINIMUMS:
        raise ValueError("R47 R10 P6 first formal review minimums changed")
    if data.get("first_formal_review_minimum_total_cases") != P7_R47_P6_FIRST_FORMAL_REVIEW_MINIMUM_TOTAL_CASES:
        raise ValueError("R47 R10 P6 first formal total changed")
    if safe_mapping(data.get("minimum_review_family_case_counts")) != P7_R47_P6_MINIMUM_REVIEW_FAMILY_CASE_COUNTS:
        raise ValueError("R47 R10 P6 review family minimums changed")
    if safe_mapping(data.get("minimum_no_connect_audit_case_counts")) != P7_R47_P6_MINIMUM_NO_CONNECT_AUDIT_CASE_COUNTS:
        raise ValueError("R47 R10 P6 no-connect audit minimums changed")
    if data.get("reviewer_facing_identifier_policy") != "blind_case_id_only":
        raise ValueError("R47 R10 P6 blind identifier policy changed")
    if tuple(data.get("reviewer_facing_allowed_field_refs") or ()) != P7_R47_P6_REVIEWER_FACING_ALLOWED_FIELD_REFS:
        raise ValueError("R47 R10 P6 reviewer allowed field refs changed")
    forbidden = set(dedupe_identifiers(data.get("reviewer_facing_forbidden_field_refs"), limit=120, max_length=160))
    if set(P7_R47_P6_REVIEWER_FACING_FORBIDDEN_FIELD_REFS) - forbidden:
        raise ValueError("R47 R10 P6 reviewer forbidden refs lost coverage")
    if set(data.get("reviewer_facing_allowed_field_refs") or ()) & forbidden:
        raise ValueError("R47 R10 P6 reviewer allowed refs must not overlap forbidden refs")
    return True


def assert_p7_r47_real_device_modal_review_packet_policy_contract(policy: Mapping[str, Any]) -> bool:
    data = safe_mapping(policy)
    _assert_common(
        data,
        schema_version=P7_R47_REAL_DEVICE_MODAL_REVIEW_PACKET_POLICY_SCHEMA_VERSION,
        source="p7_r47_r11_real_device_modal_review_packet_policy",
    )
    if data.get("policy_section") != "R11_real_device_modal_review_packet_policy":
        raise ValueError("R47 R11 real-device policy section changed")
    r46_checklist = build_real_device_submit_modal_readfeel_checklist()
    assert_real_device_submit_modal_readfeel_checklist_contract(r46_checklist)
    r46_readfeel_axes = tuple(safe_mapping(r46_checklist.get("readfeel_axes")).keys())
    for true_key in (
        "real_device_modal_review_packet_policy_fixed",
        "input_feedback_comment_text_source_required",
        "rn_title_preserved_required",
        "rn_display_condition_preserved_required",
        "public_top_level_shape_preserved_required",
        "passed_non_empty_comment_text_only_required",
        "non_passed_hidden_required",
        "device_ref_body_free_only",
        "os_ref_body_free_only",
        "app_build_ref_body_free_only",
        "screenshot_local_only",
        "visible_modal_text_local_only",
        "modal_layout_note_local_only",
        "body_free_readfeel_axes_only",
        "body_free_checklist_results_required_later",
        "disposal_receipt_required_before_real_device_confirmed",
        "body_removed_required_before_real_device_confirmed",
        "real_device_modal_review_packet_policy_created_here",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R47 R11 real-device policy must keep {true_key}=True")
    for false_key in (
        "screenshot_or_visible_body_export_allowed",
        "screenshot_body_p7_material_allowed",
        "visible_modal_text_body_p7_material_allowed",
        "body_full_packet_export_allowed",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "rn_display_condition_changed",
        "api_route_changed",
        "request_key_changed",
        "response_shape_changed",
        "public_response_key_added",
        "api_response_key_added",
        "db_schema_changed",
        "visible_payload_source_changed",
        "gate_relaxed",
        "real_device_modal_review_packet_generation_allowed_here",
        "real_device_modal_review_start_allowed_after_r11",
        "real_device_modal_review_start_allowed",
        "p5_human_blind_qa_confirmed",
        "p6_limited_human_readfeel_confirmed",
        "real_device_modal_review_confirmed",
        "manual_real_device_review_confirmed",
        "actual_body_full_packet_generated_here",
        "actual_human_review_run_here",
        "actual_real_device_review_run_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "body_full_writer_created_here",
        "local_reviewer_payload_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R47 R11 real-device policy must keep {false_key}=False")
    for forbidden_key in P7_R47_REAL_DEVICE_REVIEWER_FACING_FORBIDDEN_FIELD_REFS:
        if forbidden_key in data:
            raise ValueError(f"R47 R11 real-device policy contains forbidden reviewer/body key: {forbidden_key}")
    if data.get("packet_kind") != "real_device_modal_review_local_packet":
        raise ValueError("R47 R11 real-device packet kind changed")
    if tuple(data.get("required_manual_review_family_refs") or ()) != P7_R47_REAL_DEVICE_REQUIRED_MANUAL_REVIEW_FAMILY_REFS:
        raise ValueError("R47 R11 required manual review family refs changed")
    if tuple(data.get("r46_required_manual_review_family_refs") or ()) != tuple(r46_checklist.get("required_manual_review_families") or ()):
        raise ValueError("R47 R11 required manual families must match R46 checklist")
    if tuple(data.get("readfeel_axis_refs") or ()) != P7_R47_REAL_DEVICE_READFEEL_AXIS_REFS:
        raise ValueError("R47 R11 readfeel axes changed")
    if tuple(data.get("r46_readfeel_axis_refs") or ()) != r46_readfeel_axes:
        raise ValueError("R47 R11 readfeel axes must match R46 checklist")
    if data.get("visible_payload_source_required") != r46_checklist.get("visible_payload_source_required"):
        raise ValueError("R47 R11 visible payload source must match R46 checklist")
    if data.get("visible_payload_source_public_ref") != "input_feedback.comment_text":
        raise ValueError("R47 R11 visible payload public ref changed")
    if safe_mapping(data.get("first_review_minimums")) != P7_R47_REAL_DEVICE_FIRST_REVIEW_MINIMUMS:
        raise ValueError("R47 R11 first review minimums changed")
    if data.get("minimum_total_cases_first_review") != 5:
        raise ValueError("R47 R11 first real-device review total changed")
    if data.get("reviewer_facing_identifier_policy") != "blind_case_id_only":
        raise ValueError("R47 R11 blind identifier policy changed")
    if tuple(data.get("reviewer_facing_allowed_field_refs") or ()) != P7_R47_REAL_DEVICE_REVIEWER_FACING_ALLOWED_FIELD_REFS:
        raise ValueError("R47 R11 reviewer allowed field refs changed")
    forbidden = set(dedupe_identifiers(data.get("reviewer_facing_forbidden_field_refs"), limit=120, max_length=160))
    if set(P7_R47_REAL_DEVICE_REVIEWER_FACING_FORBIDDEN_FIELD_REFS) - forbidden:
        raise ValueError("R47 R11 reviewer forbidden refs lost coverage")
    if set(data.get("reviewer_facing_allowed_field_refs") or ()) & forbidden:
        raise ValueError("R47 R11 reviewer allowed refs must not overlap forbidden refs")
    return True


def assert_p7_r47_r10_r11_p6_real_device_packet_policy_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_common(
        data,
        schema_version=P7_R47_R10_R11_P6_REAL_DEVICE_PACKET_POLICY_SCHEMA_VERSION,
        source="p7_r47_r10_r11_p6_real_device_packet_policy_freeze",
    )
    if data.get("policy_section") != "R10_R11_p6_real_device_packet_policy_freeze":
        raise ValueError("R47 R10/R11 policy section changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R47_R10_R11_IMPLEMENTED_STEPS:
        raise ValueError("R47 R10/R11 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R47_R10_R11_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R47 R10/R11 not-yet-implemented steps changed")
    assert_p7_r47_r8_r9_disposal_p5_packet_policy_freeze_contract(safe_mapping(data.get("r8_r9_disposal_p5_packet_policy_freeze")))
    if data.get("next_required_step") != P7_R47_R10_R11_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R47 R10/R11 must point to R12 as next required step")
    for true_key in (
        "p6_limited_human_readfeel_packet_policy_fixed",
        "real_device_modal_review_packet_policy_fixed",
        "p6_limited_human_readfeel_packet_policy_created_here",
        "real_device_modal_review_packet_policy_created_here",
        "p6_start_gated_by_p5_confirmation",
        "real_device_review_queued_after_p5_p6_review",
        "body_full_packet_schema_created_here",
        "body_free_manifest_schema_created_here",
        "rating_row_schema_created_here",
        "blocker_row_schema_created_here",
        "reviewer_notes_policy_created_here",
        "disposal_policy_created_here",
        "body_free_disposal_receipt_schema_created_here",
        "p5_human_blind_qa_packet_policy_created_here",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R47 R10/R11 must keep {true_key}=True")
    for false_key in (
        "json_schema_file_created_here",
        "local_review_packet_policy_ready",
        "policy_ready",
        "r47_policy_ready",
        "p5_human_blind_qa_start_allowed_after_r10_r11",
        "p5_human_blind_qa_confirmed",
        "p6_limited_human_readfeel_start_allowed_after_r10_r11",
        "p6_limited_human_readfeel_start_allowed",
        "p6_limited_human_readfeel_confirmed",
        "real_device_modal_review_start_allowed_after_r10_r11",
        "real_device_modal_review_start_allowed",
        "real_device_modal_review_confirmed",
        "actual_body_full_packet_generated_here",
        "actual_body_free_manifest_materialized_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_notes_materialized_here",
        "actual_disposal_run_here",
        "actual_cleanup_run_here",
        "actual_disposal_receipt_materialized_here",
        "body_full_writer_created_here",
        "actual_human_review_run_here",
        "actual_real_device_review_run_here",
        "local_reviewer_payload_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R47 R10/R11 must keep {false_key}=False")
    if data.get("p6_first_formal_review_minimum_total_cases") != P7_R47_P6_FIRST_FORMAL_REVIEW_MINIMUM_TOTAL_CASES:
        raise ValueError("R47 R10/R11 P6 minimum total changed")
    if tuple(data.get("p6_review_family_refs") or ()) != P6_LIMITED_READFEEL_REVIEW_FAMILIES:
        raise ValueError("R47 R10/R11 P6 review families changed")
    if tuple(data.get("p6_no_connect_family_refs") or ()) != P6_NO_CONNECT_FAMILIES:
        raise ValueError("R47 R10/R11 P6 no-connect families changed")
    if tuple(data.get("p6_rating_axis_refs") or ()) != P6_LIMITED_READFEEL_RATING_AXES:
        raise ValueError("R47 R10/R11 P6 axes changed")
    if tuple(data.get("real_device_required_manual_review_family_refs") or ()) != P7_R47_REAL_DEVICE_REQUIRED_MANUAL_REVIEW_FAMILY_REFS:
        raise ValueError("R47 R10/R11 real-device families changed")
    if tuple(data.get("real_device_readfeel_axis_refs") or ()) != P7_R47_REAL_DEVICE_READFEEL_AXIS_REFS:
        raise ValueError("R47 R10/R11 real-device axes changed")
    return True



def _next_work_after_r47_policy_from_ledger(ledger: Mapping[str, Any]) -> list[str]:
    summary = safe_mapping(ledger.get("next_decision_summary"))
    refs = dedupe_identifiers(summary.get("next_recommended_work_refs"), limit=20, max_length=160)
    if not refs:
        raise ValueError("R47 R12 requires R46 next decision work refs")
    if refs[0] != P7_R47_FIRST_NEXT_WORK_REF:
        raise ValueError("R47 R12 requires R46 first next work to remain local review packet policy")
    after_policy = [ref for ref in refs if ref != P7_R47_FIRST_NEXT_WORK_REF]
    if tuple(after_policy) != P7_R47_R12_NEXT_RECOMMENDED_WORK_AFTER_POLICY_REFS:
        raise ValueError("R47 R12 next work after policy must remain P5 -> P6 -> real-device")
    return after_policy


def build_p7_r47_r46_next_decision_ledger_connection_policy(
    *,
    r10_r11_policy_freeze: Mapping[str, Any] | None = None,
    r46_next_decision_ledger: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r47_r46_next_decision_ledger_connection_policy",
) -> dict[str, Any]:
    """Build the R12 body-free connection policy to the R46 next-decision ledger.

    R12 does not mutate the R46 ledger. It emits a body-free R47 policy-ready
    handoff summary saying that the next allowed action is preparing P5 human
    Blind QA packets, while keeping all actual review, P7 completion, P8, HOLD,
    and release markers closed.
    """

    r10_r11 = (
        safe_mapping(r10_r11_policy_freeze)
        if r10_r11_policy_freeze is not None
        else build_p7_r47_r10_r11_p6_real_device_packet_policy_freeze()
    )
    assert_p7_r47_r10_r11_p6_real_device_packet_policy_freeze_contract(r10_r11)
    if r10_r11_policy_freeze is not None:
        _assert_r47_body_free(r10_r11, source="p7_r47.r10_r11_policy_freeze")

    ledger = _r46_ledger(r46_next_decision_ledger)
    r46_summary = safe_mapping(ledger.get("next_decision_summary"))
    branch = clean_identifier(r46_summary.get("active_decision_branch"), default="unknown", max_length=160)
    if branch != BRANCH_A_DISPLAY_GREEN_LINEAGE_CONSISTENT:
        raise ValueError("R47 R12 requires R46 branch A")
    after_policy_refs = _next_work_after_r47_policy_from_ledger(ledger)

    policy_summary = {
        "r47_policy_ready": True,
        "local_review_packet_policy_ready": True,
        "policy_ready": True,
        "p5_human_blind_qa_start_allowed_after_policy": True,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "real_device_modal_review_start_allowed": False,
        "real_device_modal_review_queued_after_p5_p6": True,
        "real_device_modal_review_confirmed": False,
        "release_allowed": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "hold004_close_allowed": False,
        "body_free": True,
    }
    policy = {
        "schema_version": P7_R47_R46_NEXT_DECISION_LEDGER_CONNECTION_POLICY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R47_LOCAL_REVIEW_PACKET_STEP,
        "scope": P7_R47_LOCAL_REVIEW_PACKET_SCOPE,
        "policy_kind": P7_R47_POLICY_KIND,
        "policy_section": "R12_r46_next_decision_ledger_connection_policy",
        "material_id": clean_identifier(material_id, default="p7_r47_r46_next_decision_ledger_connection_policy", max_length=160),
        "current_phase": "P7",
        "connection_kind": P7_R47_R12_LEDGER_CONNECTION_KIND,
        "r46_ledger_connection_policy_fixed": True,
        "r46_ledger_schema_version_ref": clean_identifier(ledger.get("schema_version"), default=P7_R46_NEXT_DECISION_HANDOFF_LEDGER_SCHEMA_VERSION, max_length=160),
        "r46_ledger_step_ref": P7_R46_NEXT_DECISION_HANDOFF_LEDGER_STEP,
        "r46_next_decision_branch_ref": branch,
        "r46_next_order_from_ledger": dedupe_identifiers(r46_summary.get("next_recommended_work_refs"), limit=20, max_length=160),
        "r47_completed_policy_step_ref": P7_R47_FIRST_NEXT_WORK_REF,
        "r47_policy_summary_field_refs": list(P7_R47_R12_POLICY_READY_SUMMARY_FIELD_REFS),
        "r47_policy_summary": policy_summary,
        "next_recommended_work_after_r47_policy_refs": after_policy_refs,
        "next_recommended_work_ref": after_policy_refs[0],
        "p5_human_blind_qa_next_work_ref": after_policy_refs[0],
        "p6_limited_human_readfeel_queued_after_p5_ref": after_policy_refs[1],
        "real_device_modal_review_queued_after_p5_p6_ref": after_policy_refs[2],
        "r46_ledger_mutation_required": False,
        "r46_ledger_mutated_here": False,
        "r46_ledger_write_required": False,
        "r46_ledger_body_free_reference_only": True,
        "r47_summary_is_new_body_free_material": True,
        "r47_policy_ready": True,
        "local_review_packet_policy_ready": True,
        "policy_ready": True,
        "p5_human_blind_qa_start_allowed_after_policy": True,
        "p5_human_blind_qa_start_allowed_after_r12": True,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "real_device_modal_review_start_allowed": False,
        "real_device_modal_review_queued_after_p5_p6": True,
        "real_device_modal_review_confirmed": False,
        "actual_body_full_packet_generated_here": False,
        "actual_body_free_manifest_materialized_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_notes_materialized_here": False,
        "actual_disposal_run_here": False,
        "actual_cleanup_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "body_full_writer_created_here": False,
        "actual_human_review_run_here": False,
        "actual_real_device_review_run_here": False,
        "local_reviewer_payload_materialized_here": False,
        "next_required_step": "R13_r47_contract_test_policy",
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
    }
    assert_p7_r47_r46_next_decision_ledger_connection_policy_contract(policy)
    return policy


def build_p7_r47_contract_test_policy(
    *,
    material_id: Any = "p7_r47_contract_test_policy",
) -> dict[str, Any]:
    """Build the R13 body-free contract-test policy freeze."""

    policy = {
        "schema_version": P7_R47_CONTRACT_TEST_POLICY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R47_LOCAL_REVIEW_PACKET_STEP,
        "scope": P7_R47_LOCAL_REVIEW_PACKET_SCOPE,
        "policy_kind": P7_R47_POLICY_KIND,
        "policy_section": "R13_r47_contract_test_policy",
        "material_id": clean_identifier(material_id, default="p7_r47_contract_test_policy", max_length=160),
        "current_phase": "P7",
        "contract_test_policy_fixed": True,
        "contract_test_scope_ref": "local_review_packet_body_full_body_free_boundary",
        "required_contract_test_refs": list(P7_R47_R13_REQUIRED_CONTRACT_TEST_REFS),
        "required_contract_test_count": len(P7_R47_R13_REQUIRED_CONTRACT_TEST_REFS),
        "target_test_module_refs": list(P7_R47_R13_TARGET_TEST_MODULE_REFS),
        "body_free_contract_tests_required": True,
        "release_closed_contract_tests_required": True,
        "storage_root_contract_tests_required": True,
        "export_denylist_contract_tests_required": True,
        "body_full_schema_local_only_contract_test_required": True,
        "body_free_manifest_contract_test_required": True,
        "body_free_rating_blocker_contract_test_required": True,
        "reviewer_notes_local_only_contract_test_required": True,
        "disposal_receipt_body_free_contract_test_required": True,
        "p5_r46_alignment_contract_test_required": True,
        "p6_r46_alignment_contract_test_required": True,
        "real_device_rn_api_db_boundary_contract_test_required": True,
        "release_p7_p8_hold004_closed_contract_test_required": True,
        "contract_test_file_materialized_here": True,
        "actual_contract_test_execution_claimed_here": False,
        "full_backend_suite_green_claimed_here": False,
        "full_backend_suite_execution_green_confirmed": False,
        "rn_contract_execution_claimed_here": False,
        "real_device_execution_claimed_here": False,
        "body_full_packet_generation_claimed_here": False,
        "human_review_execution_claimed_here": False,
        "local_review_packet_policy_ready": True,
        "policy_ready": True,
        "r47_policy_ready": True,
        "p5_human_blind_qa_start_allowed_after_policy": True,
        "p5_human_blind_qa_start_allowed_after_r13": True,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "real_device_modal_review_start_allowed": False,
        "real_device_modal_review_confirmed": False,
        "actual_body_full_packet_generated_here": False,
        "actual_body_free_manifest_materialized_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_notes_materialized_here": False,
        "actual_disposal_run_here": False,
        "actual_cleanup_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "body_full_writer_created_here": False,
        "actual_human_review_run_here": False,
        "actual_real_device_review_run_here": False,
        "local_reviewer_payload_materialized_here": False,
        "next_required_step": P7_R47_R12_R13_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
    }
    assert_p7_r47_contract_test_policy_contract(policy)
    return policy


def build_p7_r47_r12_r13_ledger_contract_test_policy_freeze(
    *,
    r10_r11_policy_freeze: Mapping[str, Any] | None = None,
    r46_next_decision_ledger: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r47_r12_r13_ledger_contract_test_policy_freeze",
) -> dict[str, Any]:
    """Build a compact R12/R13 body-free policy-ready freeze."""

    r10_r11 = (
        safe_mapping(r10_r11_policy_freeze)
        if r10_r11_policy_freeze is not None
        else build_p7_r47_r10_r11_p6_real_device_packet_policy_freeze()
    )
    assert_p7_r47_r10_r11_p6_real_device_packet_policy_freeze_contract(r10_r11)
    r12 = build_p7_r47_r46_next_decision_ledger_connection_policy(
        r10_r11_policy_freeze=r10_r11,
        r46_next_decision_ledger=r46_next_decision_ledger,
    )
    r13 = build_p7_r47_contract_test_policy()
    freeze = {
        "schema_version": P7_R47_R12_R13_LEDGER_CONTRACT_TEST_POLICY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R47_LOCAL_REVIEW_PACKET_STEP,
        "scope": P7_R47_LOCAL_REVIEW_PACKET_SCOPE,
        "policy_kind": P7_R47_POLICY_KIND,
        "policy_section": "R12_R13_ledger_connection_contract_test_policy_freeze",
        "material_id": clean_identifier(material_id, default="p7_r47_r12_r13_ledger_contract_test_policy_freeze", max_length=160),
        "current_phase": "P7",
        "implemented_steps": list(P7_R47_R12_R13_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R47_R12_R13_NOT_YET_IMPLEMENTED_STEPS),
        "r10_r11_p6_real_device_packet_policy_freeze": r10_r11,
        "r12_r46_next_decision_ledger_connection_policy": r12,
        "r13_contract_test_policy": r13,
        "r46_ledger_connection_policy_fixed": True,
        "contract_test_policy_fixed": True,
        "r47_policy_ready": True,
        "local_review_packet_policy_ready": True,
        "policy_ready": True,
        "p5_human_blind_qa_start_allowed_after_policy": True,
        "p5_human_blind_qa_start_allowed_after_r12_r13": True,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "real_device_modal_review_start_allowed": False,
        "real_device_modal_review_queued_after_p5_p6": True,
        "real_device_modal_review_confirmed": False,
        "next_recommended_work_after_r47_policy_refs": list(P7_R47_R12_NEXT_RECOMMENDED_WORK_AFTER_POLICY_REFS),
        "next_recommended_work_ref": P7_R47_R12_NEXT_RECOMMENDED_WORK_AFTER_POLICY_REFS[0],
        "required_contract_test_refs": list(P7_R47_R13_REQUIRED_CONTRACT_TEST_REFS),
        "required_contract_test_count": len(P7_R47_R13_REQUIRED_CONTRACT_TEST_REFS),
        "next_required_step": P7_R47_R12_R13_NEXT_REQUIRED_STEP_REF,
        "json_schema_file_created_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_body_free_manifest_materialized_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_notes_materialized_here": False,
        "actual_disposal_run_here": False,
        "actual_cleanup_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "body_full_writer_created_here": False,
        "actual_human_review_run_here": False,
        "actual_real_device_review_run_here": False,
        "actual_contract_test_execution_claimed_here": False,
        "full_backend_suite_green_claimed_here": False,
        "full_backend_suite_execution_green_confirmed": False,
        "local_reviewer_payload_materialized_here": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
    }
    assert_p7_r47_r12_r13_ledger_contract_test_policy_freeze_contract(freeze)
    return freeze


def assert_p7_r47_r46_next_decision_ledger_connection_policy_contract(policy: Mapping[str, Any]) -> bool:
    data = safe_mapping(policy)
    _assert_common(
        data,
        schema_version=P7_R47_R46_NEXT_DECISION_LEDGER_CONNECTION_POLICY_SCHEMA_VERSION,
        source="p7_r47_r12_r46_next_decision_ledger_connection_policy",
    )
    if data.get("policy_section") != "R12_r46_next_decision_ledger_connection_policy":
        raise ValueError("R47 R12 policy section changed")
    if data.get("connection_kind") != P7_R47_R12_LEDGER_CONNECTION_KIND:
        raise ValueError("R47 R12 connection kind changed")
    if data.get("r46_next_decision_branch_ref") != BRANCH_A_DISPLAY_GREEN_LINEAGE_CONSISTENT:
        raise ValueError("R47 R12 must connect only to R46 branch A")
    if tuple(data.get("r46_next_order_from_ledger") or ()) != (
        P7_R47_FIRST_NEXT_WORK_REF,
        *P7_R47_R12_NEXT_RECOMMENDED_WORK_AFTER_POLICY_REFS,
    ):
        raise ValueError("R47 R12 R46 next order changed")
    if tuple(data.get("next_recommended_work_after_r47_policy_refs") or ()) != P7_R47_R12_NEXT_RECOMMENDED_WORK_AFTER_POLICY_REFS:
        raise ValueError("R47 R12 next work after policy changed")
    if data.get("next_recommended_work_ref") != P7_R47_R12_NEXT_RECOMMENDED_WORK_AFTER_POLICY_REFS[0]:
        raise ValueError("R47 R12 must point next work to P5 human Blind QA")
    if tuple(data.get("r47_policy_summary_field_refs") or ()) != P7_R47_R12_POLICY_READY_SUMMARY_FIELD_REFS:
        raise ValueError("R47 R12 policy summary field refs changed")
    summary = safe_mapping(data.get("r47_policy_summary"))
    for true_key in (
        "r47_policy_ready",
        "local_review_packet_policy_ready",
        "policy_ready",
        "p5_human_blind_qa_start_allowed_after_policy",
        "real_device_modal_review_queued_after_p5_p6",
        "body_free",
    ):
        if summary.get(true_key) is not True:
            raise ValueError(f"R47 R12 summary must keep {true_key}=True")
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
        if summary.get(false_key) is not False:
            raise ValueError(f"R47 R12 summary must keep {false_key}=False")
    for true_key in (
        "r46_ledger_connection_policy_fixed",
        "r46_ledger_body_free_reference_only",
        "r47_summary_is_new_body_free_material",
        "r47_policy_ready",
        "local_review_packet_policy_ready",
        "policy_ready",
        "p5_human_blind_qa_start_allowed_after_policy",
        "p5_human_blind_qa_start_allowed_after_r12",
        "real_device_modal_review_queued_after_p5_p6",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R47 R12 policy must keep {true_key}=True")
    for false_key in (
        "r46_ledger_mutation_required",
        "r46_ledger_mutated_here",
        "r46_ledger_write_required",
        "p5_human_blind_qa_confirmed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_limited_human_readfeel_confirmed",
        "real_device_modal_review_start_allowed",
        "real_device_modal_review_confirmed",
        "actual_body_full_packet_generated_here",
        "actual_body_free_manifest_materialized_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_notes_materialized_here",
        "actual_disposal_run_here",
        "actual_cleanup_run_here",
        "actual_disposal_receipt_materialized_here",
        "body_full_writer_created_here",
        "actual_human_review_run_here",
        "actual_real_device_review_run_here",
        "local_reviewer_payload_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R47 R12 policy must keep {false_key}=False")
    if data.get("next_required_step") != "R13_r47_contract_test_policy":
        raise ValueError("R47 R12 must point to R13 next")
    return True


def assert_p7_r47_contract_test_policy_contract(policy: Mapping[str, Any]) -> bool:
    data = safe_mapping(policy)
    _assert_common(
        data,
        schema_version=P7_R47_CONTRACT_TEST_POLICY_SCHEMA_VERSION,
        source="p7_r47_r13_contract_test_policy",
    )
    if data.get("policy_section") != "R13_r47_contract_test_policy":
        raise ValueError("R47 R13 policy section changed")
    if data.get("contract_test_policy_fixed") is not True:
        raise ValueError("R47 R13 contract test policy must be fixed")
    if tuple(data.get("required_contract_test_refs") or ()) != P7_R47_R13_REQUIRED_CONTRACT_TEST_REFS:
        raise ValueError("R47 R13 required contract test refs changed")
    if data.get("required_contract_test_count") != len(P7_R47_R13_REQUIRED_CONTRACT_TEST_REFS):
        raise ValueError("R47 R13 required contract test count changed")
    if tuple(data.get("target_test_module_refs") or ()) != P7_R47_R13_TARGET_TEST_MODULE_REFS:
        raise ValueError("R47 R13 target test module refs changed")
    for true_key in (
        "body_free_contract_tests_required",
        "release_closed_contract_tests_required",
        "storage_root_contract_tests_required",
        "export_denylist_contract_tests_required",
        "body_full_schema_local_only_contract_test_required",
        "body_free_manifest_contract_test_required",
        "body_free_rating_blocker_contract_test_required",
        "reviewer_notes_local_only_contract_test_required",
        "disposal_receipt_body_free_contract_test_required",
        "p5_r46_alignment_contract_test_required",
        "p6_r46_alignment_contract_test_required",
        "real_device_rn_api_db_boundary_contract_test_required",
        "release_p7_p8_hold004_closed_contract_test_required",
        "contract_test_file_materialized_here",
        "local_review_packet_policy_ready",
        "policy_ready",
        "r47_policy_ready",
        "p5_human_blind_qa_start_allowed_after_policy",
        "p5_human_blind_qa_start_allowed_after_r13",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R47 R13 policy must keep {true_key}=True")
    for false_key in (
        "actual_contract_test_execution_claimed_here",
        "full_backend_suite_green_claimed_here",
        "full_backend_suite_execution_green_confirmed",
        "rn_contract_execution_claimed_here",
        "real_device_execution_claimed_here",
        "body_full_packet_generation_claimed_here",
        "human_review_execution_claimed_here",
        "p5_human_blind_qa_confirmed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_limited_human_readfeel_confirmed",
        "real_device_modal_review_start_allowed",
        "real_device_modal_review_confirmed",
        "actual_body_full_packet_generated_here",
        "actual_body_free_manifest_materialized_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_notes_materialized_here",
        "actual_disposal_run_here",
        "actual_cleanup_run_here",
        "actual_disposal_receipt_materialized_here",
        "body_full_writer_created_here",
        "actual_human_review_run_here",
        "actual_real_device_review_run_here",
        "local_reviewer_payload_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R47 R13 policy must keep {false_key}=False")
    if data.get("next_required_step") != P7_R47_R12_R13_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R47 R13 must point to R14 next")
    return True


def assert_p7_r47_r12_r13_ledger_contract_test_policy_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_common(
        data,
        schema_version=P7_R47_R12_R13_LEDGER_CONTRACT_TEST_POLICY_SCHEMA_VERSION,
        source="p7_r47_r12_r13_ledger_contract_test_policy_freeze",
    )
    if data.get("policy_section") != "R12_R13_ledger_connection_contract_test_policy_freeze":
        raise ValueError("R47 R12/R13 policy section changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R47_R12_R13_IMPLEMENTED_STEPS:
        raise ValueError("R47 R12/R13 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R47_R12_R13_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R47 R12/R13 not-yet-implemented steps changed")
    assert_p7_r47_r10_r11_p6_real_device_packet_policy_freeze_contract(safe_mapping(data.get("r10_r11_p6_real_device_packet_policy_freeze")))
    assert_p7_r47_r46_next_decision_ledger_connection_policy_contract(safe_mapping(data.get("r12_r46_next_decision_ledger_connection_policy")))
    assert_p7_r47_contract_test_policy_contract(safe_mapping(data.get("r13_contract_test_policy")))
    if tuple(data.get("next_recommended_work_after_r47_policy_refs") or ()) != P7_R47_R12_NEXT_RECOMMENDED_WORK_AFTER_POLICY_REFS:
        raise ValueError("R47 R12/R13 next work after policy changed")
    if tuple(data.get("required_contract_test_refs") or ()) != P7_R47_R13_REQUIRED_CONTRACT_TEST_REFS:
        raise ValueError("R47 R12/R13 required contract tests changed")
    if data.get("required_contract_test_count") != len(P7_R47_R13_REQUIRED_CONTRACT_TEST_REFS):
        raise ValueError("R47 R12/R13 required contract test count changed")
    for true_key in (
        "r46_ledger_connection_policy_fixed",
        "contract_test_policy_fixed",
        "r47_policy_ready",
        "local_review_packet_policy_ready",
        "policy_ready",
        "p5_human_blind_qa_start_allowed_after_policy",
        "p5_human_blind_qa_start_allowed_after_r12_r13",
        "real_device_modal_review_queued_after_p5_p6",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R47 R12/R13 must keep {true_key}=True")
    for false_key in (
        "json_schema_file_created_here",
        "p5_human_blind_qa_confirmed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_limited_human_readfeel_confirmed",
        "real_device_modal_review_start_allowed",
        "real_device_modal_review_confirmed",
        "actual_body_full_packet_generated_here",
        "actual_body_free_manifest_materialized_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_notes_materialized_here",
        "actual_disposal_run_here",
        "actual_cleanup_run_here",
        "actual_disposal_receipt_materialized_here",
        "body_full_writer_created_here",
        "actual_human_review_run_here",
        "actual_real_device_review_run_here",
        "actual_contract_test_execution_claimed_here",
        "full_backend_suite_green_claimed_here",
        "full_backend_suite_execution_green_confirmed",
        "local_reviewer_payload_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R47 R12/R13 must keep {false_key}=False")
    if data.get("next_required_step") != P7_R47_R12_R13_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R47 R12/R13 must point to R14 next")
    return True




def _command_string(*parts: str) -> str:
    return " ".join(part for part in parts if part)


def _validation_command_rows() -> list[dict[str, Any]]:
    r47_modules = " ".join(P7_R47_R14_R15_TARGET_TEST_MODULE_REFS)
    r46_modules = " ".join(P7_R47_R46_REGRESSION_TEST_MODULE_REFS)
    display_modules = " ".join(P7_R47_DISPLAY_CONTRACT_REGRESSION_TEST_MODULE_REFS)
    return [
        {
            "command_id": "py_compile_r47_policy_module",
            "command_kind": "python_compile",
            "workspace_ref": "mashos-api/ai",
            "required_for_patch_zip": True,
            "optional": False,
            "timeout_seconds": 60,
            "command": _command_string(
                "PYTHONPATH=services/ai_inference",
                "python -m py_compile",
                "services/ai_inference/emlis_ai_p7_r47_local_review_packet_policy.py",
            ),
            "target_refs": ["services/ai_inference/emlis_ai_p7_r47_local_review_packet_policy.py"],
            "claims_execution_green_here": False,
            "body_free": True,
        },
        {
            "command_id": "r47_split_policy_contract_target",
            "command_kind": "pytest",
            "workspace_ref": "mashos-api/ai",
            "required_for_patch_zip": True,
            "optional": False,
            "timeout_seconds": 240,
            "command": _command_string(
                "PYTHONPATH=services/ai_inference timeout 240s pytest -q",
                r47_modules,
            ),
            "target_refs": list(P7_R47_R14_R15_TARGET_TEST_MODULE_REFS),
            "design_single_file_target_ref": P7_R47_R14_DESIGN_SINGLE_FILE_TARGET_REF,
            "design_single_file_materialized_in_this_snapshot": False,
            "claims_execution_green_here": False,
            "body_free": True,
        },
        {
            "command_id": "r46_handoff_regression_target",
            "command_kind": "pytest",
            "workspace_ref": "mashos-api/ai",
            "required_for_patch_zip": True,
            "optional": False,
            "timeout_seconds": 240,
            "command": _command_string(
                "PYTHONPATH=services/ai_inference timeout 240s pytest -q",
                r46_modules,
            ),
            "target_refs": list(P7_R47_R46_REGRESSION_TEST_MODULE_REFS),
            "claims_execution_green_here": False,
            "body_free": True,
        },
        {
            "command_id": "display_contract_regression_target",
            "command_kind": "pytest",
            "workspace_ref": "mashos-api/ai",
            "required_for_patch_zip": True,
            "optional": False,
            "timeout_seconds": 180,
            "command": _command_string(
                "PYTHONPATH=services/ai_inference timeout 180s pytest -q",
                display_modules,
            ),
            "target_refs": list(P7_R47_DISPLAY_CONTRACT_REGRESSION_TEST_MODULE_REFS),
            "claims_execution_green_here": False,
            "body_free": True,
        },
        {
            "command_id": "backend_collect_only_hold_visibility_target",
            "command_kind": "pytest_collect_only",
            "workspace_ref": "mashos-api/ai",
            "required_for_patch_zip": False,
            "optional": True,
            "timeout_seconds": 180,
            "command": "PYTHONPATH=services/ai_inference timeout 180s pytest --collect-only -q",
            "target_refs": ["backend_collect_only"],
            "claims_execution_green_here": False,
            "body_free": True,
        },
        {
            "command_id": "rn_contract_optional_no_touch_confirmation",
            "command_kind": "npm_test",
            "workspace_ref": "Cocolon",
            "required_for_patch_zip": False,
            "optional": True,
            "timeout_seconds": 120,
            "command": "npm run test:rn-screens --silent",
            "target_refs": ["Cocolon/tests/rn-screen-contracts.test.js"],
            "r47_backend_policy_touch_required": False,
            "claims_execution_green_here": False,
            "body_free": True,
        },
    ]


def _normalize_repo_ref(value: Any) -> str:
    return clean_identifier(value, default="", max_length=260).replace("\\", "/").lstrip("./")


def p7_r47_touch_candidate_deny_reasons(candidate_ref: Any) -> tuple[str, ...]:
    """Return R15 no-touch deny reasons for a candidate path reference."""

    ref = _normalize_repo_ref(candidate_ref)
    lower = ref.lower()
    reasons: list[str] = []
    if not ref:
        return ("r47_touch_candidate_ref_missing",)

    allowed_exact = {
        _normalize_repo_ref(item) for item in (
            *P7_R47_R15_DESIGN_TOUCH_CANDIDATE_FILE_REFS,
            *P7_R47_R15_ACTUAL_TOUCH_CANDIDATE_FILE_REFS,
            *P7_R47_R15_OPTIONAL_TOUCH_CANDIDATE_FILE_REFS,
        )
    }
    allowed_by_pattern = any(fnmatch.fnmatch(ref, pattern) for pattern in P7_R47_R15_ALLOWED_TEST_PATH_PATTERNS)
    if ref in allowed_exact or allowed_by_pattern:
        return ()

    no_touch_exact = {_normalize_repo_ref(item) for item in P7_R47_R15_NO_TOUCH_FILE_REFS}
    if ref in no_touch_exact:
        reasons.append("r47_explicit_no_touch_file_ref")
    if lower.startswith("cocolon/screens/") or lower.startswith("cocolon/tests/rn-screen-contracts"):
        reasons.append("r47_rn_contract_or_screen_no_touch_boundary")
    if lower.endswith("emlis_ai_reply_service.py"):
        reasons.append("r47_emlis_reply_runtime_no_touch_boundary")
    if lower.endswith("emlis_ai_public_feedback_meta.py"):
        reasons.append("r47_public_feedback_meta_no_touch_boundary")
    if lower.endswith("emlis_ai_body_free_public_source_lineage.py"):
        reasons.append("r47_public_lineage_runtime_no_touch_boundary")
    if "/api_" in lower or lower.endswith("api_emotion_submit.py") or "route" in lower:
        reasons.append("r47_api_route_request_response_no_touch_boundary")
    if "migration" in lower or lower.endswith(".sql") or "/db" in lower:
        reasons.append("r47_db_schema_migration_no_touch_boundary")
    if "gate" in lower and ("threshold" in lower or "runtime" in lower):
        reasons.append("r47_runtime_gate_threshold_no_touch_boundary")
    if not reasons:
        reasons.append("r47_not_listed_as_touch_candidate")
    return tuple(dedupe_identifiers(reasons, limit=10, max_length=120))


def build_p7_r47_target_validation_command_matrix(
    *,
    material_id: Any = "p7_r47_target_validation_command_matrix",
) -> dict[str, Any]:
    """Build the R14 body-free target validation command matrix."""

    command_rows = _validation_command_rows()
    command_ids = tuple(clean_identifier(row.get("command_id"), default="unknown", max_length=120) for row in command_rows)
    matrix = {
        "schema_version": P7_R47_TARGET_VALIDATION_COMMAND_MATRIX_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R47_LOCAL_REVIEW_PACKET_STEP,
        "scope": P7_R47_LOCAL_REVIEW_PACKET_SCOPE,
        "policy_kind": P7_R47_POLICY_KIND,
        "policy_section": "R14_target_validation_command_matrix",
        "material_id": clean_identifier(material_id, default="p7_r47_target_validation_command_matrix", max_length=160),
        "current_phase": "P7",
        "target_validation_command_matrix_fixed": True,
        "validation_command_ids": list(P7_R47_R14_VALIDATION_COMMAND_IDS),
        "required_validation_command_ids": list(P7_R47_R14_REQUIRED_VALIDATION_COMMAND_IDS),
        "optional_validation_command_ids": list(P7_R47_R14_OPTIONAL_VALIDATION_COMMAND_IDS),
        "command_rows": command_rows,
        "r47_target_test_module_refs": list(P7_R47_R14_R15_TARGET_TEST_MODULE_REFS),
        "r46_regression_test_module_refs": list(P7_R47_R46_REGRESSION_TEST_MODULE_REFS),
        "display_contract_regression_test_module_refs": list(P7_R47_DISPLAY_CONTRACT_REGRESSION_TEST_MODULE_REFS),
        "design_single_file_target_ref": P7_R47_R14_DESIGN_SINGLE_FILE_TARGET_REF,
        "design_single_file_materialized_in_this_snapshot": False,
        "rn_contract_required_for_r47_backend_policy_patch": False,
        "rn_contract_optional_confirmation_before_zip": True,
        "actual_validation_execution_claimed_here": False,
        "actual_contract_test_execution_claimed_here": False,
        "full_backend_suite_green_claimed_here": False,
        "full_backend_suite_execution_green_confirmed": False,
        "rn_contract_execution_claimed_here": False,
        "real_device_execution_claimed_here": False,
        "actual_human_review_run_here": False,
        "actual_real_device_review_run_here": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "local_reviewer_payload_materialized_here": False,
        "local_review_packet_policy_ready": True,
        "policy_ready": True,
        "r47_policy_ready": True,
        "p5_human_blind_qa_start_allowed_after_policy": True,
        "p5_human_blind_qa_start_allowed_after_r14": True,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "real_device_modal_review_start_allowed": False,
        "real_device_modal_review_confirmed": False,
        "next_required_step": "R15_touch_candidate_and_no_touch_boundary",
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
    }
    if command_ids != P7_R47_R14_VALIDATION_COMMAND_IDS:
        raise ValueError("R47 R14 validation command ids changed")
    assert_p7_r47_target_validation_command_matrix_contract(matrix)
    return matrix


def build_p7_r47_touch_candidate_no_touch_boundary(
    *,
    actual_touched_file_refs: Sequence[Any] | None = None,
    material_id: Any = "p7_r47_touch_candidate_no_touch_boundary",
) -> dict[str, Any]:
    """Build the R15 body-free implementation touch/no-touch boundary."""

    touched_refs = dedupe_identifiers(
        actual_touched_file_refs if actual_touched_file_refs is not None else P7_R47_R15_ACTUAL_TOUCH_CANDIDATE_FILE_REFS,
        limit=20,
        max_length=260,
    )
    denied = {ref: p7_r47_touch_candidate_deny_reasons(ref) for ref in touched_refs}
    denied = {ref: reasons for ref, reasons in denied.items() if reasons}
    boundary = {
        "schema_version": P7_R47_TOUCH_NO_TOUCH_BOUNDARY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R47_LOCAL_REVIEW_PACKET_STEP,
        "scope": P7_R47_LOCAL_REVIEW_PACKET_SCOPE,
        "policy_kind": P7_R47_POLICY_KIND,
        "policy_section": "R15_touch_candidate_and_no_touch_boundary",
        "material_id": clean_identifier(material_id, default="p7_r47_touch_candidate_no_touch_boundary", max_length=160),
        "current_phase": "P7",
        "touch_candidate_no_touch_boundary_fixed": True,
        "design_touch_candidate_file_refs": list(P7_R47_R15_DESIGN_TOUCH_CANDIDATE_FILE_REFS),
        "actual_touch_candidate_file_refs": list(P7_R47_R15_ACTUAL_TOUCH_CANDIDATE_FILE_REFS),
        "actual_touched_file_refs": touched_refs,
        "optional_touch_candidate_file_refs": list(P7_R47_R15_OPTIONAL_TOUCH_CANDIDATE_FILE_REFS),
        "no_touch_file_refs": list(P7_R47_R15_NO_TOUCH_FILE_REFS),
        "no_touch_boundary_refs": list(P7_R47_R15_NO_TOUCH_BOUNDARY_REFS),
        "allowed_test_path_patterns": list(P7_R47_R15_ALLOWED_TEST_PATH_PATTERNS),
        "denied_actual_touched_file_refs": denied,
        "r47_policy_module_touch_allowed_here": True,
        "r47_split_contract_test_touch_allowed_here": True,
        "r47_manifest_module_touch_candidate_fixed_but_not_created_here": True,
        "r47_docs_touch_candidate_optional_but_not_created_here": True,
        "rn_production_files_touched_here": False,
        "rn_contract_test_touched_here": False,
        "emlis_reply_runtime_touched_here": False,
        "public_feedback_meta_runtime_touched_here": False,
        "public_source_lineage_runtime_touched_here": False,
        "db_schema_or_migration_touched_here": False,
        "api_route_or_public_response_shape_touched_here": False,
        "runtime_gate_threshold_touched_here": False,
        "release_material_touched_here": False,
        "rn_visible_contract_changed": False,
        "api_response_key_added": False,
        "db_schema_changed": False,
        "request_key_changed": False,
        "response_shape_changed": False,
        "runtime_surface_gate_relaxed": False,
        "visible_surface_gate_relaxed": False,
        "gate_relaxed": False,
        "actual_body_full_packet_generated_here": False,
        "body_full_writer_created_here": False,
        "local_reviewer_payload_materialized_here": False,
        "actual_human_review_run_here": False,
        "actual_real_device_review_run_here": False,
        "local_review_packet_policy_ready": True,
        "policy_ready": True,
        "r47_policy_ready": True,
        "p5_human_blind_qa_start_allowed_after_policy": True,
        "p5_human_blind_qa_start_allowed_after_r15": True,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "real_device_modal_review_start_allowed": False,
        "real_device_modal_review_confirmed": False,
        "next_required_step": P7_R47_R14_R15_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
    }
    assert_p7_r47_touch_candidate_no_touch_boundary_contract(boundary)
    return boundary


def build_p7_r47_r14_r15_validation_touch_boundary_freeze(
    *,
    r12_r13_policy_freeze: Mapping[str, Any] | None = None,
    actual_touched_file_refs: Sequence[Any] | None = None,
    material_id: Any = "p7_r47_r14_r15_validation_touch_boundary_freeze",
) -> dict[str, Any]:
    """Build a compact final R14/R15 body-free policy freeze."""

    r12_r13 = (
        safe_mapping(r12_r13_policy_freeze)
        if r12_r13_policy_freeze is not None
        else build_p7_r47_r12_r13_ledger_contract_test_policy_freeze()
    )
    assert_p7_r47_r12_r13_ledger_contract_test_policy_freeze_contract(r12_r13)
    if r12_r13_policy_freeze is not None:
        _assert_r47_body_free(r12_r13, source="p7_r47.r12_r13_policy_freeze")

    r14 = build_p7_r47_target_validation_command_matrix()
    r15 = build_p7_r47_touch_candidate_no_touch_boundary(actual_touched_file_refs=actual_touched_file_refs)
    freeze = {
        "schema_version": P7_R47_R14_R15_VALIDATION_TOUCH_BOUNDARY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R47_LOCAL_REVIEW_PACKET_STEP,
        "scope": P7_R47_LOCAL_REVIEW_PACKET_SCOPE,
        "policy_kind": P7_R47_POLICY_KIND,
        "policy_section": "R14_R15_validation_touch_boundary_freeze",
        "material_id": clean_identifier(material_id, default="p7_r47_r14_r15_validation_touch_boundary_freeze", max_length=160),
        "current_phase": "P7",
        "implemented_steps": list(P7_R47_R14_R15_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R47_R14_R15_NOT_YET_IMPLEMENTED_STEPS),
        "r12_r13_ledger_contract_test_policy_freeze": r12_r13,
        "r14_target_validation_command_matrix": r14,
        "r15_touch_candidate_no_touch_boundary": r15,
        "r46_ledger_connection_policy_fixed": True,
        "contract_test_policy_fixed": True,
        "target_validation_command_matrix_fixed": True,
        "touch_candidate_no_touch_boundary_fixed": True,
        "r47_policy_ready": True,
        "local_review_packet_policy_ready": True,
        "policy_ready": True,
        "p5_human_blind_qa_start_allowed_after_policy": True,
        "p5_human_blind_qa_start_allowed_after_r14_r15": True,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_confirmed": False,
        "real_device_modal_review_start_allowed": False,
        "real_device_modal_review_queued_after_p5_p6": True,
        "real_device_modal_review_confirmed": False,
        "r47_target_test_module_refs": list(P7_R47_R14_R15_TARGET_TEST_MODULE_REFS),
        "r46_regression_test_module_refs": list(P7_R47_R46_REGRESSION_TEST_MODULE_REFS),
        "display_contract_regression_test_module_refs": list(P7_R47_DISPLAY_CONTRACT_REGRESSION_TEST_MODULE_REFS),
        "actual_touched_file_refs": list(r15["actual_touched_file_refs"]),
        "no_touch_file_refs": list(P7_R47_R15_NO_TOUCH_FILE_REFS),
        "next_recommended_work_ref": P7_R47_R14_R15_NEXT_REQUIRED_STEP_REF,
        "next_required_step": P7_R47_R14_R15_NEXT_REQUIRED_STEP_REF,
        "json_schema_file_created_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_body_free_manifest_materialized_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_notes_materialized_here": False,
        "actual_disposal_run_here": False,
        "actual_cleanup_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "body_full_writer_created_here": False,
        "actual_human_review_run_here": False,
        "actual_real_device_review_run_here": False,
        "actual_contract_test_execution_claimed_here": False,
        "actual_validation_execution_claimed_here": False,
        "full_backend_suite_green_claimed_here": False,
        "full_backend_suite_execution_green_confirmed": False,
        "rn_contract_execution_claimed_here": False,
        "local_reviewer_payload_materialized_here": False,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_release_closed_flags(),
    }
    assert_p7_r47_r14_r15_validation_touch_boundary_freeze_contract(freeze)
    return freeze


def assert_p7_r47_target_validation_command_matrix_contract(matrix: Mapping[str, Any]) -> bool:
    data = safe_mapping(matrix)
    _assert_common(
        data,
        schema_version=P7_R47_TARGET_VALIDATION_COMMAND_MATRIX_SCHEMA_VERSION,
        source="p7_r47_r14_target_validation_command_matrix",
    )
    if data.get("policy_section") != "R14_target_validation_command_matrix":
        raise ValueError("R47 R14 policy section changed")
    if data.get("target_validation_command_matrix_fixed") is not True:
        raise ValueError("R47 R14 validation command matrix must be fixed")
    if tuple(data.get("validation_command_ids") or ()) != P7_R47_R14_VALIDATION_COMMAND_IDS:
        raise ValueError("R47 R14 validation command ids changed")
    if tuple(data.get("required_validation_command_ids") or ()) != P7_R47_R14_REQUIRED_VALIDATION_COMMAND_IDS:
        raise ValueError("R47 R14 required command ids changed")
    if tuple(data.get("optional_validation_command_ids") or ()) != P7_R47_R14_OPTIONAL_VALIDATION_COMMAND_IDS:
        raise ValueError("R47 R14 optional command ids changed")
    rows = data.get("command_rows")
    if not isinstance(rows, list) or len(rows) != len(P7_R47_R14_VALIDATION_COMMAND_IDS):
        raise ValueError("R47 R14 command rows changed")
    row_ids = tuple(clean_identifier(safe_mapping(row).get("command_id"), default="unknown", max_length=120) for row in rows)
    if row_ids != P7_R47_R14_VALIDATION_COMMAND_IDS:
        raise ValueError("R47 R14 command row ids changed")
    for row in rows:
        item = safe_mapping(row)
        if item.get("body_free") is not True:
            raise ValueError("R47 R14 command row must be body-free")
        if item.get("claims_execution_green_here") is not False:
            raise ValueError("R47 R14 command rows must not claim execution green")
        if clean_identifier(item.get("command"), default="", max_length=2000) == "":
            raise ValueError("R47 R14 command row command missing")
    if tuple(data.get("r47_target_test_module_refs") or ()) != P7_R47_R14_R15_TARGET_TEST_MODULE_REFS:
        raise ValueError("R47 R14 target test modules changed")
    if tuple(data.get("r46_regression_test_module_refs") or ()) != P7_R47_R46_REGRESSION_TEST_MODULE_REFS:
        raise ValueError("R47 R14 R46 regression modules changed")
    if tuple(data.get("display_contract_regression_test_module_refs") or ()) != P7_R47_DISPLAY_CONTRACT_REGRESSION_TEST_MODULE_REFS:
        raise ValueError("R47 R14 display regression modules changed")
    if data.get("design_single_file_target_ref") != P7_R47_R14_DESIGN_SINGLE_FILE_TARGET_REF:
        raise ValueError("R47 R14 design target ref changed")
    for true_key in (
        "target_validation_command_matrix_fixed",
        "local_review_packet_policy_ready",
        "policy_ready",
        "r47_policy_ready",
        "p5_human_blind_qa_start_allowed_after_policy",
        "p5_human_blind_qa_start_allowed_after_r14",
        "rn_contract_optional_confirmation_before_zip",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R47 R14 must keep {true_key}=True")
    for false_key in (
        "design_single_file_materialized_in_this_snapshot",
        "rn_contract_required_for_r47_backend_policy_patch",
        "actual_validation_execution_claimed_here",
        "actual_contract_test_execution_claimed_here",
        "full_backend_suite_green_claimed_here",
        "full_backend_suite_execution_green_confirmed",
        "rn_contract_execution_claimed_here",
        "real_device_execution_claimed_here",
        "actual_human_review_run_here",
        "actual_real_device_review_run_here",
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
            raise ValueError(f"R47 R14 must keep {false_key}=False")
    if data.get("next_required_step") != "R15_touch_candidate_and_no_touch_boundary":
        raise ValueError("R47 R14 must point to R15 next")
    return True


def assert_p7_r47_touch_candidate_no_touch_boundary_contract(boundary: Mapping[str, Any]) -> bool:
    data = safe_mapping(boundary)
    _assert_common(
        data,
        schema_version=P7_R47_TOUCH_NO_TOUCH_BOUNDARY_SCHEMA_VERSION,
        source="p7_r47_r15_touch_candidate_no_touch_boundary",
    )
    if data.get("policy_section") != "R15_touch_candidate_and_no_touch_boundary":
        raise ValueError("R47 R15 policy section changed")
    if data.get("touch_candidate_no_touch_boundary_fixed") is not True:
        raise ValueError("R47 R15 boundary must be fixed")
    if tuple(data.get("design_touch_candidate_file_refs") or ()) != P7_R47_R15_DESIGN_TOUCH_CANDIDATE_FILE_REFS:
        raise ValueError("R47 R15 design touch candidate refs changed")
    if tuple(data.get("actual_touch_candidate_file_refs") or ()) != P7_R47_R15_ACTUAL_TOUCH_CANDIDATE_FILE_REFS:
        raise ValueError("R47 R15 actual touch candidate refs changed")
    if tuple(data.get("optional_touch_candidate_file_refs") or ()) != P7_R47_R15_OPTIONAL_TOUCH_CANDIDATE_FILE_REFS:
        raise ValueError("R47 R15 optional touch candidate refs changed")
    if tuple(data.get("no_touch_file_refs") or ()) != P7_R47_R15_NO_TOUCH_FILE_REFS:
        raise ValueError("R47 R15 no-touch file refs changed")
    if tuple(data.get("no_touch_boundary_refs") or ()) != P7_R47_R15_NO_TOUCH_BOUNDARY_REFS:
        raise ValueError("R47 R15 no-touch boundary refs changed")
    touched_refs = dedupe_identifiers(data.get("actual_touched_file_refs"), limit=20, max_length=260)
    if not touched_refs:
        raise ValueError("R47 R15 actual touched file refs must be explicit")
    denied = safe_mapping(data.get("denied_actual_touched_file_refs"))
    if denied:
        raise ValueError("R47 R15 actual touched files include no-touch or unknown refs")
    for ref in touched_refs:
        if p7_r47_touch_candidate_deny_reasons(ref):
            raise ValueError(f"R47 R15 touched ref is outside touch candidates: {ref}")
    for no_touch_ref in P7_R47_R15_NO_TOUCH_FILE_REFS:
        if not p7_r47_touch_candidate_deny_reasons(no_touch_ref):
            raise ValueError("R47 R15 no-touch ref was accidentally allowed")
    for true_key in (
        "touch_candidate_no_touch_boundary_fixed",
        "r47_policy_module_touch_allowed_here",
        "r47_split_contract_test_touch_allowed_here",
        "r47_manifest_module_touch_candidate_fixed_but_not_created_here",
        "r47_docs_touch_candidate_optional_but_not_created_here",
        "local_review_packet_policy_ready",
        "policy_ready",
        "r47_policy_ready",
        "p5_human_blind_qa_start_allowed_after_policy",
        "p5_human_blind_qa_start_allowed_after_r15",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R47 R15 must keep {true_key}=True")
    for false_key in (
        "rn_production_files_touched_here",
        "rn_contract_test_touched_here",
        "emlis_reply_runtime_touched_here",
        "public_feedback_meta_runtime_touched_here",
        "public_source_lineage_runtime_touched_here",
        "db_schema_or_migration_touched_here",
        "api_route_or_public_response_shape_touched_here",
        "runtime_gate_threshold_touched_here",
        "release_material_touched_here",
        "rn_visible_contract_changed",
        "api_response_key_added",
        "db_schema_changed",
        "request_key_changed",
        "response_shape_changed",
        "runtime_surface_gate_relaxed",
        "visible_surface_gate_relaxed",
        "gate_relaxed",
        "actual_body_full_packet_generated_here",
        "body_full_writer_created_here",
        "local_reviewer_payload_materialized_here",
        "actual_human_review_run_here",
        "actual_real_device_review_run_here",
        "p5_human_blind_qa_confirmed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_limited_human_readfeel_confirmed",
        "real_device_modal_review_start_allowed",
        "real_device_modal_review_confirmed",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R47 R15 must keep {false_key}=False")
    if data.get("next_required_step") != P7_R47_R14_R15_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R47 R15 must point to P5 human Blind QA next")
    return True


def assert_p7_r47_r14_r15_validation_touch_boundary_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_common(
        data,
        schema_version=P7_R47_R14_R15_VALIDATION_TOUCH_BOUNDARY_SCHEMA_VERSION,
        source="p7_r47_r14_r15_validation_touch_boundary_freeze",
    )
    if data.get("policy_section") != "R14_R15_validation_touch_boundary_freeze":
        raise ValueError("R47 R14/R15 policy section changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R47_R14_R15_IMPLEMENTED_STEPS:
        raise ValueError("R47 R14/R15 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R47_R14_R15_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R47 R14/R15 not-yet-implemented steps must be empty")
    assert_p7_r47_r12_r13_ledger_contract_test_policy_freeze_contract(safe_mapping(data.get("r12_r13_ledger_contract_test_policy_freeze")))
    assert_p7_r47_target_validation_command_matrix_contract(safe_mapping(data.get("r14_target_validation_command_matrix")))
    assert_p7_r47_touch_candidate_no_touch_boundary_contract(safe_mapping(data.get("r15_touch_candidate_no_touch_boundary")))
    if tuple(data.get("r47_target_test_module_refs") or ()) != P7_R47_R14_R15_TARGET_TEST_MODULE_REFS:
        raise ValueError("R47 R14/R15 target test modules changed")
    if tuple(data.get("actual_touched_file_refs") or ()) != P7_R47_R15_ACTUAL_TOUCH_CANDIDATE_FILE_REFS:
        raise ValueError("R47 R14/R15 actual touched refs changed")
    for true_key in (
        "r46_ledger_connection_policy_fixed",
        "contract_test_policy_fixed",
        "target_validation_command_matrix_fixed",
        "touch_candidate_no_touch_boundary_fixed",
        "r47_policy_ready",
        "local_review_packet_policy_ready",
        "policy_ready",
        "p5_human_blind_qa_start_allowed_after_policy",
        "p5_human_blind_qa_start_allowed_after_r14_r15",
        "real_device_modal_review_queued_after_p5_p6",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R47 R14/R15 must keep {true_key}=True")
    for false_key in (
        "json_schema_file_created_here",
        "p5_human_blind_qa_confirmed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_limited_human_readfeel_confirmed",
        "real_device_modal_review_start_allowed",
        "real_device_modal_review_confirmed",
        "actual_body_full_packet_generated_here",
        "actual_body_free_manifest_materialized_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_notes_materialized_here",
        "actual_disposal_run_here",
        "actual_cleanup_run_here",
        "actual_disposal_receipt_materialized_here",
        "body_full_writer_created_here",
        "actual_human_review_run_here",
        "actual_real_device_review_run_here",
        "actual_contract_test_execution_claimed_here",
        "actual_validation_execution_claimed_here",
        "full_backend_suite_green_claimed_here",
        "full_backend_suite_execution_green_confirmed",
        "rn_contract_execution_claimed_here",
        "local_reviewer_payload_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R47 R14/R15 must keep {false_key}=False")
    if data.get("next_required_step") != P7_R47_R14_R15_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R47 R14/R15 must point to P5 human Blind QA next")
    if data.get("next_recommended_work_ref") != P7_R47_R14_R15_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R47 R14/R15 next recommended work changed")
    return True

def build_p7_r47_r8_r9_disposal_p5_policy_freeze(**kwargs: Any) -> dict[str, Any]:
    return build_p7_r47_r8_r9_disposal_p5_packet_policy_freeze(**kwargs)


def assert_p7_r47_r8_r9_disposal_p5_policy_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    return assert_p7_r47_r8_r9_disposal_p5_packet_policy_freeze_contract(freeze)


def _assert_common(data: Mapping[str, Any], *, schema_version: str, source: str) -> None:
    payload = safe_mapping(data)
    if payload.get("schema_version") != schema_version:
        raise ValueError(f"unexpected {source} schema_version")
    if payload.get("phase") != P7_PHASE or payload.get("step") != P7_R47_LOCAL_REVIEW_PACKET_STEP:
        raise ValueError(f"unexpected {source} phase or step")
    if payload.get("scope") != P7_R47_LOCAL_REVIEW_PACKET_SCOPE:
        raise ValueError(f"unexpected {source} scope")
    if payload.get("policy_kind") != P7_R47_POLICY_KIND:
        raise ValueError(f"unexpected {source} policy kind")
    if payload.get("current_phase") != "P7":
        raise ValueError(f"{source} must keep current phase as P7")
    if payload.get("body_free") is not True:
        raise ValueError(f"{source} must be body-free")
    for key in _RELEASE_CLOSED_KEYS:
        if payload.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=False")
    assert_false_markers(safe_mapping(payload.get("public_contract")), source=f"{source}.public_contract")
    assert_false_markers(safe_mapping(payload.get("body_free_markers")), source=f"{source}.body_free_markers")
    _assert_r47_body_free(payload, source=source)


def _assert_r0_r1_not_ready(data: Mapping[str, Any], *, source: str) -> None:
    for key in _R0_R1_FALSE_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=False during R0/R1")


def assert_p7_r47_current_source_r46_handoff_hold_refreeze_contract(refreeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(refreeze)
    _assert_common(data, schema_version=P7_R47_CURRENT_SOURCE_REFREEZE_SCHEMA_VERSION, source="p7_r47_r0_refreeze")
    if data.get("freeze_kind") != "current_source_r46_handoff_hold_refreeze":
        raise ValueError("R47 R0 freeze kind changed")
    if data.get("source_mode") != P7_SOURCE_MODE:
        raise ValueError("R47 R0 must remain local snapshot source mode")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError("R47 R0 must not require or claim Git checking")
    r46 = safe_mapping(data.get("r46_handoff"))
    if r46.get("active_decision_branch") != BRANCH_A_DISPLAY_GREEN_LINEAGE_CONSISTENT:
        raise ValueError("R47 R0 must refreeze R46 branch A")
    if r46.get("next_order_first") != P7_R47_FIRST_NEXT_WORK_REF:
        raise ValueError("R47 R0 must refreeze local review packet policy as first next work")
    if r46.get("p5_human_blind_qa_path_open_from_r46") is not True:
        raise ValueError("R47 R0 must preserve that R46 opened only the P5 path")
    if r46.get("p6_limited_human_readfeel_path_open_from_r46") is not False:
        raise ValueError("R47 R0 must keep P6 blocked before P5 confirmation")
    hold = safe_mapping(data.get("hold_state"))
    unresolved = set(dedupe_identifiers(hold.get("unresolved_hold_refs"), limit=120, max_length=120))
    if set(P7_R47_REQUIRED_UNRESOLVED_HOLD_REFS) - unresolved:
        raise ValueError("R47 R0 must preserve unresolved P5/P6/real-device/full-backend HOLD refs")
    for key in (
        "p5_human_blind_qa_confirmed",
        "p6_limited_human_readfeel_confirmed",
        "real_device_modal_review_confirmed",
        "full_backend_suite_green_confirmed",
        "local_review_packet_policy_ready",
        "body_full_review_packet_generated",
        "body_free_rating_rows_ready",
        "body_removed_verified",
    ):
        if hold.get(key) is not False:
            raise ValueError(f"R47 R0 hold state must keep {key}=False")
    if data.get("r0_current_source_handoff_hold_refrozen") is not True:
        raise ValueError("R47 R0 marker must be true")
    if data.get("r1_scope_packet_kind_enum_fixed") is not False:
        raise ValueError("R47 R0 must not mark R1 fixed")
    _assert_r0_r1_not_ready(data, source="p7_r47_r0_refreeze")
    return True


def assert_p7_r47_scope_schema_packet_kind_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_common(data, schema_version=P7_R47_SCOPE_SCHEMA_PACKET_KIND_FREEZE_SCHEMA_VERSION, source="p7_r47_r1_scope_freeze")
    if data.get("freeze_kind") != "scope_schema_version_packet_kind_enum_freeze":
        raise ValueError("R47 R1 freeze kind changed")
    if data.get("policy_schema_version") != P7_R47_LOCAL_REVIEW_PACKET_POLICY_SCHEMA_VERSION:
        raise ValueError("R47 R1 policy schema version changed")
    if data.get("r0_schema_version") != P7_R47_CURRENT_SOURCE_REFREEZE_SCHEMA_VERSION:
        raise ValueError("R47 R1 must reference the R0 schema")
    if data.get("r46_branch_code") != BRANCH_A_DISPLAY_GREEN_LINEAGE_CONSISTENT:
        raise ValueError("R47 R1 must remain attached to R46 branch A")
    if data.get("r47_scope_fixed") is not True or data.get("r47_schema_version_fixed") is not True:
        raise ValueError("R47 R1 must fix scope and schema version")
    if tuple(data.get("packet_kind_enum") or ()) != P7_R47_PACKET_KINDS:
        raise ValueError("R47 R1 packet kind enum changed")
    if data.get("packet_kind_count") != len(P7_R47_PACKET_KINDS) or data.get("packet_kind_enum_fixed") is not True:
        raise ValueError("R47 R1 packet kind count/fixed marker changed")
    if data.get("first_next_work_ref") != P7_R47_FIRST_NEXT_WORK_REF:
        raise ValueError("R47 R1 first next work changed")
    if data.get("next_required_step") != P7_R47_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R47 R1 must point to R2 as next required step")
    policies = data.get("packet_kind_policies")
    if not isinstance(policies, list) or len(policies) != len(P7_R47_PACKET_KINDS):
        raise ValueError("R47 R1 packet kind policies changed")
    for index, policy in enumerate(policies):
        item = safe_mapping(policy)
        if item.get("packet_kind") != P7_R47_PACKET_KINDS[index]:
            raise ValueError("R47 R1 packet kind policy order changed")
        for true_key in ("local_only_required_later", "body_full_payload_required_later", "body_free_result_required_later"):
            if item.get(true_key) is not True:
                raise ValueError(f"R47 R1 packet policy must keep {true_key}=True")
        for false_key in (
            "materialized_here",
            "writer_created_here",
            "standard_export_allowed",
            "public_meta_material_allowed",
            "p7_scorecard_material_allowed",
            "release_material_allowed",
        ):
            if item.get(false_key) is not False:
                raise ValueError(f"R47 R1 packet policy must keep {false_key}=False")
    if data.get("r0_current_source_handoff_hold_refrozen") is not True:
        raise ValueError("R47 R1 must preserve R0 marker")
    if data.get("r1_scope_packet_kind_enum_fixed") is not True:
        raise ValueError("R47 R1 marker must be true")
    _assert_r0_r1_not_ready(data, source="p7_r47_r1_scope_freeze")
    return True


def assert_p7_r47_r0_r1_scope_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_common(data, schema_version=P7_R47_R0_R1_SCOPE_FREEZE_SCHEMA_VERSION, source="p7_r47_r0_r1_scope_freeze")
    if data.get("freeze_kind") != "r0_r1_scope_freeze":
        raise ValueError("R47 R0/R1 combined freeze kind changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R47_IMPLEMENTED_STEPS:
        raise ValueError("R47 R0/R1 implemented steps changed")
    assert_p7_r47_current_source_r46_handoff_hold_refreeze_contract(safe_mapping(data.get("r0_current_source_refreeze")))
    assert_p7_r47_scope_schema_packet_kind_freeze_contract(safe_mapping(data.get("r1_scope_schema_packet_kind_freeze")))
    if data.get("first_next_work_ref") != P7_R47_FIRST_NEXT_WORK_REF:
        raise ValueError("R47 R0/R1 first next work changed")
    if data.get("next_required_step") != P7_R47_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R47 R0/R1 must point to R2 as next required step")
    if tuple(data.get("packet_kind_enum") or ()) != P7_R47_PACKET_KINDS:
        raise ValueError("R47 R0/R1 packet enum changed")
    if data.get("r0_current_source_handoff_hold_refrozen") is not True or data.get("r1_scope_packet_kind_enum_fixed") is not True:
        raise ValueError("R47 R0/R1 markers must be true")
    _assert_r0_r1_not_ready(data, source="p7_r47_r0_r1_scope_freeze")
    return True


def assert_p7_r47_local_review_storage_root_policy_contract(policy: Mapping[str, Any]) -> bool:
    data = safe_mapping(policy)
    if data.get("schema_version") != P7_R47_LOCAL_REVIEW_STORAGE_ROOT_POLICY_SCHEMA_VERSION:
        raise ValueError("unexpected R47 R2 storage root policy schema_version")
    if data.get("phase") != P7_PHASE or data.get("step") != P7_R47_LOCAL_REVIEW_PACKET_STEP:
        raise ValueError("unexpected R47 R2 storage root policy phase or step")
    if data.get("scope") != P7_R47_LOCAL_REVIEW_PACKET_SCOPE or data.get("policy_kind") != P7_R47_POLICY_KIND:
        raise ValueError("unexpected R47 R2 storage root policy scope or policy kind")
    if data.get("policy_section") != "R2_local_only_storage_root_policy":
        raise ValueError("R47 R2 policy section changed")
    if data.get("current_phase") != "P7" or data.get("body_free") is not True:
        raise ValueError("R47 R2 storage policy must remain P7 body-free")
    if data.get("storage_mode") != P7_R47_STORAGE_MODE_EXTERNAL_LOCAL_ONLY:
        raise ValueError("R47 R2 storage mode must be external_local_only")
    if data.get("env_var") != P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR:
        raise ValueError("R47 R2 local review root env var changed")
    for false_key in (
        "root_path_exposed",
        "local_absolute_path_included",
        "repo_local_storage_allowed",
        "artifact_export_path_allowed",
        "docs_tests_services_storage_allowed",
        "premise_storage_allowed",
        "implemented_docs_storage_allowed",
        "mnt_data_artifact_storage_allowed",
        "git_tracked_path_storage_allowed",
        "p5_human_blind_qa_start_allowed_after_r2",
        "p6_limited_human_readfeel_start_allowed",
        "real_device_modal_review_start_allowed",
        "actual_body_full_packet_generated_here",
        "body_full_writer_created_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R47 R2 storage policy must keep {false_key}=False")
    if data.get("body_full_generation_requires_env_root") is not True:
        raise ValueError("R47 R2 storage policy must require local review env root")
    status = data.get("local_review_root_status")
    if status not in {"missing", "invalid", "valid"}:
        raise ValueError("R47 R2 storage root status changed")
    if status == "valid":
        if data.get("local_review_root_configured") is not True or data.get("local_body_packet_generation_allowed") is not True:
            raise ValueError("R47 R2 valid root must allow generation by storage policy")
        if data.get("storage_root_ref") != P7_R47_STORAGE_ROOT_REF:
            raise ValueError("R47 R2 valid root must expose only the abstract root ref")
        if data.get("generation_block_reason_ids"):
            raise ValueError("R47 R2 valid root must not carry block reasons")
    else:
        if data.get("local_body_packet_generation_allowed") is not False:
            raise ValueError("R47 R2 missing/invalid root must block body-full generation")
        if not data.get("generation_block_reason_ids"):
            raise ValueError("R47 R2 missing/invalid root must carry a block reason")
    if "local_review_root_path" in data or "absolute_path" in data:
        raise ValueError("R47 R2 storage policy must not expose local absolute paths")
    for key in _RELEASE_CLOSED_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"R47 R2 storage policy must keep {key}=False")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_r47_r2_storage.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_r47_r2_storage.body_free_markers")
    _assert_r47_body_free(data, source="p7_r47_r2_storage")
    return True


def assert_p7_r47_export_denylist_policy_contract(policy: Mapping[str, Any]) -> bool:
    data = safe_mapping(policy)
    if data.get("schema_version") != P7_R47_EXPORT_DENYLIST_POLICY_SCHEMA_VERSION:
        raise ValueError("unexpected R47 R3 export denylist policy schema_version")
    if data.get("phase") != P7_PHASE or data.get("step") != P7_R47_LOCAL_REVIEW_PACKET_STEP:
        raise ValueError("unexpected R47 R3 export policy phase or step")
    if data.get("scope") != P7_R47_LOCAL_REVIEW_PACKET_SCOPE or data.get("policy_kind") != P7_R47_POLICY_KIND:
        raise ValueError("unexpected R47 R3 export policy scope or policy kind")
    if data.get("policy_section") != "R3_export_denylist_git_zip_mixing_prevention":
        raise ValueError("R47 R3 policy section changed")
    if data.get("current_phase") != "P7" or data.get("body_free") is not True:
        raise ValueError("R47 R3 export policy must remain P7 body-free")
    if data.get("git_zip_mixing_prevention_policy_fixed") is not True:
        raise ValueError("R47 R3 export policy must fix git/zip mixing prevention")
    patterns = tuple(data.get("export_denylist_patterns") or ())
    if patterns != P7_R47_EXPORT_DENYLIST_PATTERNS:
        raise ValueError("R47 R3 export denylist patterns changed")
    for false_key in (
        "body_full_packet_export_allowed",
        "body_full_packet_git_tracking_allowed",
        "body_full_packet_zip_inclusion_allowed",
        "reviewer_notes_export_allowed",
        "release_material_body_full_allowed",
        "premise_zip_inclusion_allowed",
        "implemented_docs_zip_inclusion_allowed",
        "standard_patch_zip_body_full_inclusion_allowed",
        "public_meta_body_full_material_allowed",
        "p7_scorecard_body_full_material_allowed",
        "handoff_ledger_body_full_material_allowed",
        "actual_body_full_packet_generated_here",
        "body_full_writer_created_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R47 R3 export policy must keep {false_key}=False")
    for true_key in (
        "body_free_summary_export_allowed",
        "body_free_rating_rows_export_allowed_later",
        "body_free_disposal_receipt_export_allowed_later",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R47 R3 export policy must keep {true_key}=True")
    for key in _RELEASE_CLOSED_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"R47 R3 export policy must keep {key}=False")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_r47_r3_export.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_r47_r3_export.body_free_markers")
    _assert_r47_body_free(data, source="p7_r47_r3_export")
    return True


def assert_p7_r47_r2_r3_storage_export_policy_contract(policy: Mapping[str, Any]) -> bool:
    data = safe_mapping(policy)
    _assert_common(data, schema_version=P7_R47_R2_R3_STORAGE_EXPORT_POLICY_SCHEMA_VERSION, source="p7_r47_r2_r3_storage_export")
    if data.get("policy_section") != "R2_R3_storage_export_policy":
        raise ValueError("R47 R2/R3 policy section changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R47_R2_R3_IMPLEMENTED_STEPS:
        raise ValueError("R47 R2/R3 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R47_R2_R3_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R47 R2/R3 not-yet-implemented steps changed")
    assert_p7_r47_r0_r1_scope_freeze_contract(safe_mapping(data.get("r0_r1_scope_freeze")))
    assert_p7_r47_local_review_storage_root_policy_contract(safe_mapping(data.get("storage_policy")))
    assert_p7_r47_export_denylist_policy_contract(safe_mapping(data.get("export_policy")))
    if data.get("next_required_step") != P7_R47_R2_R3_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R47 R2/R3 must point to R4 as next required step")
    if tuple(data.get("packet_kind_enum") or ()) != P7_R47_PACKET_KINDS:
        raise ValueError("R47 R2/R3 packet enum changed")
    for true_key in (
        "r0_current_source_handoff_hold_refrozen",
        "r1_scope_packet_kind_enum_fixed",
        "local_review_packet_storage_policy_fixed",
        "export_denylist_policy_fixed",
        "git_zip_mixing_prevention_policy_fixed",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R47 R2/R3 must keep {true_key}=True")
    for false_key in (
        "local_review_packet_policy_ready",
        "policy_ready",
        "r47_policy_ready",
        "p5_human_blind_qa_start_allowed_after_r2_r3",
        "p5_human_blind_qa_confirmed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_limited_human_readfeel_confirmed",
        "real_device_modal_review_start_allowed",
        "real_device_modal_review_confirmed",
        "actual_body_full_packet_generated_here",
        "body_full_writer_created_here",
        "body_full_packet_schema_created_here",
        "body_free_manifest_schema_created_here",
        "rating_row_schema_created_here",
        "disposal_policy_created_here",
        "actual_human_review_run_here",
        "actual_real_device_review_run_here",
        "local_reviewer_payload_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R47 R2/R3 must keep {false_key}=False")
    return True



# R8/R9 public function aliases used by the contract tests.
build_p7_r47_r8_r9_disposal_p5_policy_freeze = build_p7_r47_r8_r9_disposal_p5_packet_policy_freeze
assert_p7_r47_r8_r9_disposal_p5_policy_freeze_contract = assert_p7_r47_r8_r9_disposal_p5_packet_policy_freeze_contract

__all__ = [
    "P7_R47_BLOCKER_KINDS",
    "P7_R47_BLOCKER_STATUSES",
    "P7_R47_BODY_FREE_BLOCKER_ROW_REQUIRED_FIELD_REFS",
    "P7_R47_BODY_FREE_BLOCKER_ROW_SCHEMA_VERSION",
    "P7_R47_BODY_FREE_RATING_BLOCKER_FORBIDDEN_FIELD_REFS",
    "P7_R47_BODY_FREE_RATING_ROW_REQUIRED_FIELD_REFS",
    "P7_R47_BODY_FREE_RATING_ROW_SCHEMA_VERSION",
    "P7_R47_BODY_FREE_LOCAL_REVIEW_MANIFEST_SCHEMA_VERSION",
    "P7_R47_BODY_FREE_MANIFEST_CASE_REF_FIELD_REFS",
    "P7_R47_BODY_FREE_MANIFEST_FORBIDDEN_FIELD_REFS",
    "P7_R47_BODY_FREE_MANIFEST_REQUIRED_FIELD_REFS",
    "P7_R47_BODY_FULL_LOCAL_REVIEW_PACKET_SCHEMA_VERSION",
    "P7_R47_BODY_FULL_PACKET_REQUIRED_FIELD_REFS",
    "P7_R47_BODY_FULL_REVIEWER_PAYLOAD_FIELD_REFS",
    "P7_R47_BODY_FULL_REVIEW_FORM_REQUIRED_FIELD_REFS",
    "P7_R47_REVIEWER_FACING_FORBIDDEN_FIELD_REFS",
    "P7_R47_CURRENT_SOURCE_REFREEZE_SCHEMA_VERSION",
    "P7_R47_FIRST_NEXT_WORK_REF",
    "P7_R47_IMPLEMENTED_STEPS",
    "P7_R47_LOCAL_REVIEW_PACKET_POLICY_SCHEMA_VERSION",
    "P7_R47_LOCAL_REVIEW_PACKET_SCOPE",
    "P7_R47_LOCAL_REVIEW_PACKET_STEP",
    "P7_R47_NEXT_REQUIRED_STEP_REF",
    "P7_R47_R2_R3_NEXT_REQUIRED_STEP_REF",
    "P7_R47_R4_R5_NEXT_REQUIRED_STEP_REF",
    "P7_R47_BLOCKED_ACTIONS",
    "P7_R47_EXPORT_DENYLIST_PATTERNS",
    "P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR",
    "P7_R47_LOCAL_REVIEW_STORAGE_ROOT_POLICY_SCHEMA_VERSION",
    "P7_R47_EXPORT_DENYLIST_POLICY_SCHEMA_VERSION",
    "P7_R47_R2_R3_STORAGE_EXPORT_POLICY_SCHEMA_VERSION",
    "P7_R47_R4_R5_SCHEMA_FREEZE_SCHEMA_VERSION",
    "P7_R47_R6_R7_IMPLEMENTED_STEPS",
    "P7_R47_R6_R7_NEXT_REQUIRED_STEP_REF",
    "P7_R47_R6_R7_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R47_R6_R7_RATING_BLOCKER_NOTES_POLICY_SCHEMA_VERSION",
    "P7_R47_REVIEW_VERDICTS",
    "P7_R47_REVIEWER_NOTES_LOCAL_ONLY_POLICY_SCHEMA_VERSION",
    "P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS",
    "P7_R47_SANITIZED_REASON_ID_REFS",
    "P7_R47_EXECUTION_BLOCKER_ID_REFS",
    "P7_R47_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R47_R2_R3_IMPLEMENTED_STEPS",
    "P7_R47_R2_R3_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R47_R4_R5_IMPLEMENTED_STEPS",
    "P7_R47_R4_R5_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R47_PACKET_KINDS",
    "P7_R47_PACKET_KIND_SET",
    "P7_R47_POLICY_KIND",
    "P7_R47_R0_R1_SCOPE_FREEZE_SCHEMA_VERSION",
    "P7_R47_RECEIVED_LOCAL_SNAPSHOT_REFS",
    "P7_R47_REQUIRED_UNRESOLVED_HOLD_REFS",
    "P7_R47_SCOPE_SCHEMA_PACKET_KIND_FREEZE_SCHEMA_VERSION",
    "assert_p7_r47_body_free_blocker_row_payload_contract",
    "assert_p7_r47_body_free_blocker_row_schema_contract",
    "assert_p7_r47_body_free_rating_row_payload_contract",
    "assert_p7_r47_body_free_rating_row_schema_contract",
    "assert_p7_r47_body_free_local_review_manifest_payload_contract",
    "assert_p7_r47_body_free_local_review_manifest_schema_contract",
    "assert_p7_r47_body_full_local_review_packet_schema_contract",
    "assert_p7_r47_current_source_r46_handoff_hold_refreeze_contract",
    "assert_p7_r47_export_denylist_policy_contract",
    "assert_p7_r47_local_review_storage_root_policy_contract",
    "assert_p7_r47_r0_r1_scope_freeze_contract",
    "assert_p7_r47_r2_r3_storage_export_policy_contract",
    "assert_p7_r47_r4_r5_schema_freeze_contract",
    "assert_p7_r47_r6_r7_rating_blocker_notes_policy_freeze_contract",
    "assert_p7_r47_reviewer_notes_local_only_policy_contract",
    "assert_p7_r47_scope_schema_packet_kind_freeze_contract",
    "build_p7_r47_body_free_blocker_row_schema",
    "build_p7_r47_body_free_rating_row_schema",
    "build_p7_r47_body_free_local_review_manifest_schema",
    "build_p7_r47_body_full_local_review_packet_schema",
    "build_p7_r47_current_source_r46_handoff_hold_refreeze",
    "build_p7_r47_export_denylist_policy",
    "build_p7_r47_local_review_storage_root_policy",
    "build_p7_r47_r0_r1_scope_freeze",
    "build_p7_r47_r2_r3_storage_export_policy",
    "build_p7_r47_r4_r5_schema_freeze",
    "build_p7_r47_r6_r7_rating_blocker_notes_policy_freeze",
    "build_p7_r47_reviewer_notes_local_only_policy",
    "build_p7_r47_scope_schema_packet_kind_freeze",
    "P7_R47_P6_FIRST_FORMAL_MINIMUMS",
    "P7_R47_P6_LIMITED_HUMAN_READFEEL_PACKET_POLICY_SCHEMA_VERSION",
    "P7_R47_P6_MINIMUM_NO_CONNECT_AUDIT_CASE_COUNTS",
    "P7_R47_P6_MINIMUM_REVIEW_FAMILY_CASE_COUNTS",
    "P7_R47_P6_REVIEWER_FACING_ALLOWED_FIELD_REFS",
    "P7_R47_P6_REVIEWER_FACING_FORBIDDEN_FIELD_REFS",
    "P7_R47_REAL_DEVICE_FIRST_REVIEW_MINIMUMS",
    "P7_R47_REAL_DEVICE_MODAL_REVIEW_PACKET_POLICY_SCHEMA_VERSION",
    "P7_R47_REAL_DEVICE_READFEEL_AXIS_REFS",
    "P7_R47_REAL_DEVICE_REQUIRED_MANUAL_REVIEW_FAMILY_REFS",
    "P7_R47_REAL_DEVICE_REQUIRED_MANUAL_REVIEW_FAMILIES",
    "P7_R47_REAL_DEVICE_REVIEWER_FACING_ALLOWED_FIELD_REFS",
    "P7_R47_REAL_DEVICE_REVIEWER_FACING_FORBIDDEN_FIELD_REFS",
    "P7_R47_R10_R11_IMPLEMENTED_STEPS",
    "P7_R47_R10_R11_NEXT_REQUIRED_STEP_REF",
    "P7_R47_R10_R11_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R47_R10_R11_P6_REAL_DEVICE_PACKET_POLICY_SCHEMA_VERSION",
    "P7_R47_CONTRACT_TEST_POLICY_SCHEMA_VERSION",
    "P7_R47_R12_LEDGER_CONNECTION_KIND",
    "P7_R47_R12_NEXT_RECOMMENDED_WORK_AFTER_POLICY_REFS",
    "P7_R47_R12_POLICY_READY_SUMMARY_FIELD_REFS",
    "P7_R47_R12_R13_IMPLEMENTED_STEPS",
    "P7_R47_R12_R13_LEDGER_CONTRACT_TEST_POLICY_SCHEMA_VERSION",
    "P7_R47_R12_R13_NEXT_REQUIRED_STEP_REF",
    "P7_R47_R12_R13_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R47_R13_REQUIRED_CONTRACT_TEST_REFS",
    "P7_R47_R13_TARGET_TEST_MODULE_REFS",
    "P7_R47_DISPLAY_CONTRACT_REGRESSION_TEST_MODULE_REFS",
    "P7_R47_R14_DESIGN_SINGLE_FILE_TARGET_REF",
    "P7_R47_R14_OPTIONAL_VALIDATION_COMMAND_IDS",
    "P7_R47_R14_R15_IMPLEMENTED_STEPS",
    "P7_R47_R14_R15_NEXT_REQUIRED_STEP_REF",
    "P7_R47_R14_R15_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R47_R14_R15_TARGET_TEST_MODULE_REFS",
    "P7_R47_R14_R15_VALIDATION_TOUCH_BOUNDARY_SCHEMA_VERSION",
    "P7_R47_R14_REQUIRED_VALIDATION_COMMAND_IDS",
    "P7_R47_R14_VALIDATION_COMMAND_IDS",
    "P7_R47_R15_ACTUAL_TOUCH_CANDIDATE_FILE_REFS",
    "P7_R47_R15_ALLOWED_TEST_PATH_PATTERNS",
    "P7_R47_R15_DESIGN_TOUCH_CANDIDATE_FILE_REFS",
    "P7_R47_R15_NO_TOUCH_BOUNDARY_REFS",
    "P7_R47_R15_NO_TOUCH_FILE_REFS",
    "P7_R47_R15_OPTIONAL_TOUCH_CANDIDATE_FILE_REFS",
    "P7_R47_R46_REGRESSION_TEST_MODULE_REFS",
    "P7_R47_TARGET_VALIDATION_COMMAND_MATRIX_SCHEMA_VERSION",
    "P7_R47_TOUCH_NO_TOUCH_BOUNDARY_SCHEMA_VERSION",
    "P7_R47_R46_NEXT_DECISION_LEDGER_CONNECTION_POLICY_SCHEMA_VERSION",
    "assert_p7_r47_contract_test_policy_contract",
    "assert_p7_r47_r12_r13_ledger_contract_test_policy_freeze_contract",
    "assert_p7_r47_r46_next_decision_ledger_connection_policy_contract",
    "assert_p7_r47_r14_r15_validation_touch_boundary_freeze_contract",
    "assert_p7_r47_target_validation_command_matrix_contract",
    "assert_p7_r47_touch_candidate_no_touch_boundary_contract",
    "build_p7_r47_contract_test_policy",
    "build_p7_r47_r12_r13_ledger_contract_test_policy_freeze",
    "build_p7_r47_r46_next_decision_ledger_connection_policy",
    "build_p7_r47_r14_r15_validation_touch_boundary_freeze",
    "build_p7_r47_target_validation_command_matrix",
    "build_p7_r47_touch_candidate_no_touch_boundary",
    "assert_p7_r47_p6_limited_human_readfeel_packet_policy_contract",
    "assert_p7_r47_real_device_modal_review_packet_policy_contract",
    "assert_p7_r47_r10_r11_p6_real_device_packet_policy_freeze_contract",
    "build_p7_r47_p6_limited_human_readfeel_packet_policy",
    "build_p7_r47_real_device_modal_review_packet_policy",
    "build_p7_r47_r10_r11_p6_real_device_packet_policy_freeze",
    "p7_r47_export_candidate_deny_reasons",
    "p7_r47_touch_candidate_deny_reasons",
]
