# -*- coding: utf-8 -*-
"""P7-R54 AHR00-AHR24 actual human review body-free intake helpers.

This module starts the R54-AHR line described in the 2026-06-27 detailed
implementation design.  It materializes the first twenty-five body-free boundary
steps:

R54-AHR-00 freezes the scope and no-touch boundary for actual human review
execution / body-free evidence intake.

R54-AHR-01 refreezes the 2026-06-27 received local snapshot
(260 / 83 / 256 / 169) as the current execution basis for the later actual
review operation, without rewriting any historical R54-OP / R54-EV / R54-CLR /
R55 / R52 helper refs.

R54-AHR-02 reconciles those older helper refs as historical / structural /
contract refs only, so helper green cannot become actual human review evidence.

R54-AHR-03 re-intakes the existing R55 hold line as actual review evidence
missing before any new local-only preflight or actual review operation.

R54-AHR-04 freezes the local-only preflight conditions required before any
body-full packet generation request can be considered.

R54-AHR-05 freezes the 24-case manifest as body-free refs only.

R54-AHR-06 records the body-free request evidence for later local-only
body-full packet generation, without carrying packet content, path, or hash.

R54-AHR-07 intakes the local packet generation operation receipt as body-free
counts and safety flags only.

R54-AHR-08 scans packet completeness and export denylist status before any
reviewer-facing selection form can be frozen.

R54-AHR-09 freezes the reviewer selection-only form structure without adding
question text, free-text export, raw body copy, or local path/hash fields.

R54-AHR-10 intakes a body-free receipt for a person-run, local-only actual
human review operation.  The helper does not run that review by itself; it
validates the receipt boundary and keeps review completion separate from P5
finalization / P6 / P8 / release decisions.

R54-AHR-11 intakes selection-only sanitized review result rows as body-free
rows.

R54-AHR-12 normalizes those sanitized rows into P5 rating rows without
question text, body payloads, paths, or hashes.

R54-AHR-13 ingests readfeel blockers and execution blockers as separated
body-free rows, keeping P5 repair, operation repair, and later P8 material
boundaries distinct.

R54-AHR-14 normalizes actual review-derived question need observations as
body-free rows without question text or draft text.

R54-AHR-15 guards consistency between rating rows and question observation
rows, keeping P5 repair, execution blockers, and P8 material candidates
separated.

R54-AHR-16 freezes the pause / abort / expiration protocol so any body-full
local-only packet lifecycle fails closed instead of being left ambiguous.

R54-AHR-17 intakes the purge / disposal receipt as body-free evidence, without
body content, reviewer notes, paths, or hashes.

R54-AHR-18 materializes the body-free post-review summary from complete review
counts, rating statistics, blocker counts, question observation counts, and
disposal receipt evidence.

R54-AHR-19 separates P5 confirmed candidate / P5 repair / P4 current-only repair
/ operation blocked decision candidates without promoting P5 finalization.

R54-AHR-20 materializes the P6 limited human readfeel candidate-only
handoff from P5_CONFIRMED_CANDIDATE without allowing P6 start.

R54-AHR-21 materializes the P8 material candidate-only handoff from actual
review-derived question need observation rows without creating question text,
trigger logic, storage, UI, or P8 start permission.

R54-AHR-22 performs the final no-body-leak / no-question-text / no-touch
validation over the body-free post-review artifacts.

R54-AHR-23 materializes the body-free R52 re-intake handoff envelope without
executing R52 or finalizing P5 / P6 / P8 / release.

R54-AHR-24 records the validation command matrix and documentation output
claim boundary as body-free evidence.

It does not execute R52 re-intake, P5 finalization, P6/P8 start, P7
completion, or release permission.

No body-full packet content is generated or exported here.  No API, DB, RN,
runtime, public response contract, P8 question implementation, P5 finalization,
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
    dedupe_identifiers,
    public_contract_flags,
    safe_mapping,
)
import emlis_ai_p7_r52_r51_handoff_p6_p8_start_decision_gate as r52
import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as r54op
import emlis_ai_p7_r54_actual_review_execution_evidence_materialization_20260626 as r54ev
import emlis_ai_p7_r54_current_snapshot_local_review_run_20260627 as r54clr
import emlis_ai_p7_r54_p5_human_blind_qa_actual_local_review_result_handoff as r54handoff
import emlis_ai_p7_r55_r54_evidence_reconcile_r52_reintake_decision_materialization as r55


P7_R54_AHR_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.ahr00_scope_no_touch_boundary_freeze.bodyfree.v1"
)
P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.ahr01_current_execution_basis_refreeze.bodyfree.v1"
)
P7_R54_AHR_HISTORICAL_HELPER_REFS_RECONCILE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.ahr02_historical_helper_refs_reconcile.bodyfree.v1"
)
P7_R54_AHR_R55_HOLD_EVIDENCE_MISSING_INTAKE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.ahr03_r55_hold_evidence_missing_intake.bodyfree.v1"
)
P7_R54_AHR_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.ahr04_local_only_preflight.bodyfree.v1"
)
P7_R54_AHR_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.ahr05_24_case_manifest_freeze.bodyfree.v1"
)
P7_R54_AHR_EXECUTION_BASIS_ENVELOPE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.execution_basis_envelope.bodyfree.v1"
)
P7_R54_AHR00_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION: Final = (
    P7_R54_AHR_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION
)
P7_R54_AHR01_CURRENT_EXECUTION_BASIS_REFREEZE_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFREEZE_SCHEMA_VERSION
)
P7_R54_AHR02_HISTORICAL_HELPER_REFS_RECONCILE_SCHEMA_VERSION: Final = (
    P7_R54_AHR_HISTORICAL_HELPER_REFS_RECONCILE_SCHEMA_VERSION
)
P7_R54_AHR03_R55_HOLD_EVIDENCE_MISSING_INTAKE_SCHEMA_VERSION: Final = (
    P7_R54_AHR_R55_HOLD_EVIDENCE_MISSING_INTAKE_SCHEMA_VERSION
)
P7_R54_AHR04_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION: Final = (
    P7_R54_AHR_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION
)
P7_R54_AHR05_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION: Final = (
    P7_R54_AHR_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION
)

P7_R54_AHR_STEP: Final = "R54_actual_human_review_execution_bodyfree_intake_20260627"
P7_R54_AHR_SCOPE: Final = "p5_user_label_connection_actual_human_review_execution_bodyfree_intake"
P7_R54_AHR_POLICY_KIND: Final = "r54_actual_human_review_execution_bodyfree_intake_boundary"
P7_R54_AHR_DEFAULT_REVIEW_SESSION_ID: Final = "p7_r54_actual_human_review_execution_20260627"

P7_R54_AHR00_STEP_REF: Final = "R54-AHR-00_scope_no_touch_boundary_freeze"
P7_R54_AHR01_STEP_REF: Final = "R54-AHR-01_current_execution_basis_refreeze"
P7_R54_AHR02_STEP_REF: Final = "R54-AHR-02_historical_helper_refs_reconcile"
P7_R54_AHR03_STEP_REF: Final = "R54-AHR-03_r55_hold_evidence_missing_intake"
P7_R54_AHR04_STEP_REF: Final = "R54-AHR-04_local_only_preflight"
P7_R54_AHR05_STEP_REF: Final = "R54-AHR-05_24_case_manifest_freeze"
P7_R54_AHR06_STEP_REF: Final = "R54-AHR-06_body_full_packet_generation_request_bodyfree_evidence"
P7_R54_AHR07_STEP_REF: Final = "R54-AHR-07_local_packet_generation_operation_receipt_intake"
P7_R54_AHR08_STEP_REF: Final = "R54-AHR-08_packet_completeness_export_denylist_scan"
P7_R54_AHR09_STEP_REF: Final = "R54-AHR-09_reviewer_selection_form_freeze"
P7_R54_AHR10_STEP_REF: Final = "R54-AHR-10_actual_human_review_local_only_operation"
P7_R54_AHR11_STEP_REF: Final = "R54-AHR-11_sanitized_review_result_row_intake"
P7_R54_AHR12_STEP_REF: Final = "R54-AHR-12_rating_row_normalization"
P7_R54_AHR13_STEP_REF: Final = "R54-AHR-13_readfeel_blocker_execution_blocker_ingestion"
P7_R54_AHR14_STEP_REF: Final = "R54-AHR-14_question_need_observation_normalization"
P7_R54_AHR15_STEP_REF: Final = "R54-AHR-15_rating_question_consistency_guard"
P7_R54_AHR16_STEP_REF: Final = "R54-AHR-16_pause_abort_expiration_protocol"
P7_R54_AHR17_STEP_REF: Final = "R54-AHR-17_purge_disposal_receipt"
P7_R54_AHR18_STEP_REF: Final = "R54-AHR-18_bodyfree_post_review_summary"
P7_R54_AHR19_STEP_REF: Final = "R54-AHR-19_p5_decision_candidate_separation"
P7_R54_AHR20_STEP_REF: Final = "R54-AHR-20_p6_candidate_only_handoff"
P7_R54_AHR21_STEP_REF: Final = "R54-AHR-21_p8_material_candidate_only_handoff"
P7_R54_AHR22_STEP_REF: Final = "R54-AHR-22_final_no_body_leak_no_question_text_no_touch_validation"
P7_R54_AHR23_STEP_REF: Final = "R54-AHR-23_r52_reintake_handoff"
P7_R54_AHR24_STEP_REF: Final = "R54-AHR-24_validation_command_matrix_documentation_output"

P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR01: Final[tuple[str, ...]] = (
    P7_R54_AHR02_STEP_REF,
    P7_R54_AHR03_STEP_REF,
    P7_R54_AHR04_STEP_REF,
    P7_R54_AHR05_STEP_REF,
    P7_R54_AHR06_STEP_REF,
    P7_R54_AHR07_STEP_REF,
    P7_R54_AHR08_STEP_REF,
    P7_R54_AHR09_STEP_REF,
    P7_R54_AHR10_STEP_REF,
    P7_R54_AHR11_STEP_REF,
    P7_R54_AHR12_STEP_REF,
    P7_R54_AHR13_STEP_REF,
    P7_R54_AHR14_STEP_REF,
    P7_R54_AHR15_STEP_REF,
    P7_R54_AHR16_STEP_REF,
    P7_R54_AHR17_STEP_REF,
    P7_R54_AHR18_STEP_REF,
    P7_R54_AHR19_STEP_REF,
    P7_R54_AHR20_STEP_REF,
    P7_R54_AHR21_STEP_REF,
    P7_R54_AHR22_STEP_REF,
    P7_R54_AHR23_STEP_REF,
    P7_R54_AHR24_STEP_REF,
)
P7_R54_AHR00_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_AHR00_STEP_REF,)
P7_R54_AHR00_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR01_STEP_REF,
    *P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR01,
)
P7_R54_AHR01_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR00_STEP_REF,
    P7_R54_AHR01_STEP_REF,
)
P7_R54_AHR01_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR01
P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR02: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR01[1:]
P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR03: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR02[1:]
P7_R54_AHR02_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR00_STEP_REF,
    P7_R54_AHR01_STEP_REF,
    P7_R54_AHR02_STEP_REF,
)
P7_R54_AHR02_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR02
P7_R54_AHR03_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR00_STEP_REF,
    P7_R54_AHR01_STEP_REF,
    P7_R54_AHR02_STEP_REF,
    P7_R54_AHR03_STEP_REF,
)
P7_R54_AHR03_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR03
P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR04: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR03[1:]
P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR05: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR04[1:]
P7_R54_AHR04_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR00_STEP_REF,
    P7_R54_AHR01_STEP_REF,
    P7_R54_AHR02_STEP_REF,
    P7_R54_AHR03_STEP_REF,
    P7_R54_AHR04_STEP_REF,
)
P7_R54_AHR04_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR04
P7_R54_AHR05_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR04_IMPLEMENTED_STEPS,
    P7_R54_AHR05_STEP_REF,
)
P7_R54_AHR05_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR05
P7_R54_AHR02_NEXT_REQUIRED_STEP_REF: Final = P7_R54_AHR02_STEP_REF
P7_R54_AHR03_NEXT_REQUIRED_STEP_REF: Final = P7_R54_AHR03_STEP_REF
P7_R54_AHR04_NEXT_REQUIRED_STEP_REF: Final = P7_R54_AHR04_STEP_REF
P7_R54_AHR05_NEXT_REQUIRED_STEP_REF: Final = P7_R54_AHR05_STEP_REF
P7_R54_AHR06_NEXT_REQUIRED_STEP_REF: Final = P7_R54_AHR06_STEP_REF
P7_R54_AHR07_NEXT_REQUIRED_STEP_REF: Final = P7_R54_AHR07_STEP_REF
P7_R54_AHR08_NEXT_REQUIRED_STEP_REF: Final = P7_R54_AHR08_STEP_REF

P7_R54_AHR_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_EVIDENCE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.ahr06_body_full_packet_generation_request.bodyfree.v1"
)
P7_R54_AHR_LOCAL_PACKET_GENERATION_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.ahr07_local_packet_generation_receipt_intake.bodyfree.v1"
)
P7_R54_AHR06_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_EVIDENCE_SCHEMA_VERSION: Final = (
    P7_R54_AHR_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_EVIDENCE_SCHEMA_VERSION
)
P7_R54_AHR07_LOCAL_PACKET_GENERATION_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION: Final = (
    P7_R54_AHR_LOCAL_PACKET_GENERATION_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION
)

P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR06: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR05[1:]
P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR07: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR06[1:]
P7_R54_AHR06_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_AHR05_IMPLEMENTED_STEPS, P7_R54_AHR06_STEP_REF)
P7_R54_AHR06_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR06
P7_R54_AHR07_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_AHR06_IMPLEMENTED_STEPS, P7_R54_AHR07_STEP_REF)
P7_R54_AHR07_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR07


P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF: Final = "current_received_snapshot_260_83_256_169"
P7_R54_AHR_ACTUAL_EXECUTION_BASIS_ALLOWED_REF: Final = "current_received_snapshot_260_83_256_169_only"
P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFREEZE_STATUS_REF: Final = (
    "CURRENT_EXECUTION_BASIS_260_83_256_169_REFROZEN_FOR_R54_AHR"
)
P7_R54_AHR_HISTORICAL_HELPER_REF_COMPARISON_STATUS_REF: Final = (
    "HISTORICAL_HELPER_REFS_DIFFER_FROM_CURRENT_EXECUTION_BASIS_260_83_256_169"
)
P7_R54_AHR_HISTORICAL_HELPER_REFS_RECONCILE_STATUS_REF: Final = (
    "HISTORICAL_HELPER_REFS_RECONCILED_AS_STRUCTURAL_REGRESSION_ONLY"
)
P7_R54_AHR_R55_HOLD_EVIDENCE_MISSING_STATUS_REF: Final = "R55_HOLD_ACTUAL_REVIEW_EVIDENCE_MISSING"
P7_R54_AHR_R55_GAP_STATUS_REF: Final = r55.P7_R55_ACTUAL_REVIEW_EVIDENCE_MISSING_GAP_STATUS_REF
P7_R54_AHR_P5_DECISION_BEFORE_RUN_REF: Final = "P5_NOT_REVIEWED"
P7_R54_AHR_R52_REINTAKE_STATUS_BEFORE_RUN_REF: Final = "BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING"
P7_R54_AHR_R54_R52_REINTAKE_HANDOFF_STATUS_BEFORE_RUN_REF: Final = (
    r55.P7_R55_R54_DEFAULT_HANDOFF_EXPECTED_STATUS_REF
)
P7_R54_AHR_R55_MISSING_EVIDENCE_REFS: Final[tuple[str, ...]] = r55.P7_R55_DEFAULT_MISSING_EVIDENCE_REFS
P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT: Final = r55.P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT

P7_R54_AHR04_PREFLIGHT_READY_STATUS_REF: Final = "PREFLIGHT_READY"
P7_R54_AHR04_PREFLIGHT_BLOCKED_STATUS_REF: Final = "PREFLIGHT_BLOCKED"
P7_R54_AHR04_ALLOWED_PREFLIGHT_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR04_PREFLIGHT_READY_STATUS_REF,
    P7_R54_AHR04_PREFLIGHT_BLOCKED_STATUS_REF,
)
P7_R54_AHR04_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "R54-AHR-04_repair_local_only_preflight_before_24_case_manifest_freeze"
P7_R54_AHR04_READY_REASON_REF: Final = "r54_ahr_local_only_preflight_ready_for_24_case_manifest_freeze"
P7_R54_AHR04_EXPLICIT_LOCAL_ONLY_ALLOW_REF: Final = "R54_AHR_LOCAL_ONLY_EXPLICIT_ALLOW_PRESENT"
P7_R54_AHR04_LOCAL_ONLY_ROOT_AVAILABLE_REF: Final = "R54_AHR_LOCAL_ONLY_REVIEW_ROOT_AVAILABLE_REF"
P7_R54_AHR04_MANIFEST_SOURCE_AVAILABLE_REF: Final = "R54_AHR_24_CASE_MANIFEST_SOURCE_AVAILABLE"
P7_R54_AHR04_EXPORT_DENYLIST_READY_REF: Final = "R54_AHR_EXPORT_DENYLIST_READY"
P7_R54_AHR04_PURGE_PLAN_READY_REF: Final = "R54_AHR_BODY_FULL_PURGE_PLAN_READY"
P7_R54_AHR04_REVIEW_SESSION_PRESENT_REF: Final = "R54_AHR_REVIEW_SESSION_ID_PRESENT"
P7_R54_AHR04_EXPORT_DENYLIST_REFS: Final[tuple[str, ...]] = (
    "raw_input",
    "current_input_body",
    "returned_emlis_body",
    "history_surface",
    "comment_text_body",
    "reviewer_free_text",
    "reviewer_notes_body",
    "question_text",
    "draft_question_text",
    "body_full_packet_content",
    "body_hash",
    "local_absolute_path",
    "terminal_output_body",
    "stdout_body",
    "stderr_body",
    "traceback_body",
)
P7_R54_AHR04_FORBIDDEN_OUTPUT_REFS: Final[tuple[str, ...]] = (
    "body_full_artifact_public_export",
    "raw_input_export",
    "returned_emlis_body_export",
    "history_surface_export",
    "reviewer_free_text_export",
    "reviewer_notes_export",
    "question_text_export",
    "draft_question_text_export",
    "local_path_or_hash_export",
    "terminal_output_body_export",
    "api_db_rn_runtime_touch",
)

P7_R54_AHR05_MANIFEST_READY_STATUS_REF: Final = "AHR_24_CASE_MANIFEST_FROZEN_BODYFREE_READY_FOR_PACKET_REQUEST"
P7_R54_AHR05_MANIFEST_BLOCKED_STATUS_REF: Final = "AHR_24_CASE_MANIFEST_BLOCKED_BY_LOCAL_ONLY_PREFLIGHT"
P7_R54_AHR05_ALLOWED_MANIFEST_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR05_MANIFEST_READY_STATUS_REF,
    P7_R54_AHR05_MANIFEST_BLOCKED_STATUS_REF,
)
P7_R54_AHR05_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "R54-AHR-05_repair_24_case_manifest_before_packet_generation_request"
P7_R54_AHR05_READY_REASON_REF: Final = "r54_ahr_24_case_manifest_frozen_bodyfree"
P7_R54_AHR05_MANIFEST_SOURCE_KIND_REF: Final = "r48_p5_first_formal_24_case_matrix_bodyfree_source"
P7_R54_AHR05_REVIEW_AXIS_PROFILE_REF: Final = "r54_ahr_p5_history_line_existing_6_axis_profile_20260627"
P7_R54_AHR05_CASE_DISTRIBUTION: Final[dict[str, int]] = dict(r54op.P7_R54_OP05_CASE_DISTRIBUTION)
P7_R54_AHR05_CASE_ROLE_BY_FAMILY: Final[dict[str, str]] = {
    family: case_role for family, _count, case_role in r54op.P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION
}
P7_R54_AHR05_CURRENT_ONLY_BOUNDARY_FAMILY_REFS: Final[tuple[str, ...]] = (
    "low_information_history_not_eligible",
    "free_tier_history_present_not_allowed",
)
P7_R54_AHR05_RATING_AXIS_REFS: Final[tuple[str, ...]] = tuple(r54op.P7_R54_OP09_RATING_AXIS_REFS)
P7_R54_AHR05_RATING_AXIS_TARGET_THRESHOLDS: Final[dict[str, float]] = dict(
    r54op.P7_R54_OP09_RATING_AXIS_TARGET_THRESHOLDS
)
P7_R54_AHR05_CASE_MANIFEST_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "case_index",
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
    "family",
    "case_role",
    "subscription_tier_ref",
    "history_evidence_policy_ref",
    "review_axis_profile_ref",
    "reviewer_facing_family_exposed",
    "reviewer_facing_tier_exposed",
    "requires_history_line_review",
    "current_only_boundary_case",
    "body_full_packet_materialized_here",
    "local_reviewer_payload_materialized_here",
    "body_free",
)

P7_R54_AHR06_REQUEST_READY_STATUS_REF: Final = "AHR_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_READY"
P7_R54_AHR06_REQUEST_BLOCKED_STATUS_REF: Final = "AHR_BODY_FULL_PACKET_GENERATION_REQUEST_BLOCKED"
P7_R54_AHR06_ALLOWED_REQUEST_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR06_REQUEST_READY_STATUS_REF,
    P7_R54_AHR06_REQUEST_BLOCKED_STATUS_REF,
)
P7_R54_AHR06_READY_REASON_REF: Final = "r54_ahr_body_full_packet_generation_request_bodyfree_ready"
P7_R54_AHR06_EXPLICIT_REQUEST_REF: Final = "R54_AHR_BODY_FULL_PACKET_GENERATION_REQUEST_EXPLICIT_BODYFREE_ONLY"
P7_R54_AHR06_LOCAL_PACKET_GENERATION_OPERATION_REF: Final = "R54_AHR_LOCAL_ONLY_PACKET_GENERATION_OPERATION_REF"
P7_R54_AHR06_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-06_repair_body_full_packet_generation_request_bodyfree_evidence_before_local_receipt"
)
P7_R54_AHR06_FORBIDDEN_EVIDENCE_FLAG_REFS: Final[tuple[str, ...]] = (
    "body_full_packet_content_included",
    "raw_input_included",
    "returned_emlis_body_included",
    "history_surface_included",
    "question_text_included",
    "draft_question_text_included",
    "local_absolute_path_included",
    "body_hash_included",
    "terminal_output_body_included",
    "packet_content_included",
)

P7_R54_AHR07_RECEIPT_READY_STATUS_REF: Final = "LOCAL_ONLY_PACKET_GENERATED_BODYFULL_NOT_EXPORTED"
P7_R54_AHR07_RECEIPT_BLOCKED_STATUS_REF: Final = "LOCAL_PACKET_GENERATION_RECEIPT_BLOCKED"
P7_R54_AHR07_ALLOWED_RECEIPT_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR07_RECEIPT_READY_STATUS_REF,
    P7_R54_AHR07_RECEIPT_BLOCKED_STATUS_REF,
)
P7_R54_AHR07_READY_REASON_REF: Final = "r54_ahr_local_packet_generation_receipt_bodyfree_intaken"
P7_R54_AHR07_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-07_repair_local_packet_generation_operation_receipt_before_packet_scan"
)

P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS: Final[dict[str, str]] = {
    "premise_zip_ref": "Cocolon_前提資料(260).zip",
    "implemented_materials_zip_ref": "EmlisAIの実装済み資料(83).zip",
    "rn_zip_ref": "Cocolon(256).zip",
    "backend_zip_ref": "mashos-api(169).zip",
    "roadmap_ref": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619.md",
    "pre_design_memo_ref": "Cocolon_EmlisAI_RoadmapStageDecision_R54ActualHumanReviewExecution_PreDesignMemo_20260627.md",
    "detailed_design_ref": "Cocolon_EmlisAI_P7_R54ActualHumanReviewExecution_BodyFreeEvidenceIntake_DetailedDesign_ImplementationOrder_20260627.md",
}
P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS: Final[tuple[str, ...]] = tuple(
    P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS.keys()
)

P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS: Final[tuple[str, ...]] = (
    "r52_20260621",
    "r54_bodyfree_handoff_20260622",
    "r55_20260623",
    "r54_op_20260625",
    "r54_ev_20260626",
    "r54_clr_20260627",
)
P7_R54_AHR_HISTORICAL_HELPER_REF_GROUPS: Final[tuple[str, ...]] = P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS
P7_R54_AHR_HISTORICAL_HELPER_REFS: Final[dict[str, dict[str, str]]] = {
    "r52_20260621": dict(r52.P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFS),
    "r54_bodyfree_handoff_20260622": dict(r54handoff.P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS),
    "r55_20260623": dict(r55.P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS),
    "r54_op_20260625": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
    "r54_ev_20260626": dict(r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
    "r54_clr_20260627": dict(r54clr.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS),
}
P7_R54_AHR_HISTORICAL_HELPER_ROLE_REFS: Final[dict[str, str]] = {
    "r52_20260621": "actual_evidence_decision_gate_contract",
    "r54_bodyfree_handoff_20260622": "bodyfree_result_handoff_contract",
    "r55_20260623": "evidence_missing_hold_and_reintake_decision_contract",
    "r54_op_20260625": "actual_local_review_operation_structural_helper",
    "r54_ev_20260626": "execution_evidence_materialization_structural_helper",
    "r54_clr_20260627": "current_snapshot_local_run_structural_helper",
}
P7_R54_AHR_HISTORICAL_HELPER_CLASSIFICATION_REFS: Final[dict[str, str]] = {
    group_ref: "historical_structural_contract_ref_only"
    for group_ref in P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS
}
P7_R54_AHR_PRIOR_HELPER_GREEN_CLAIM_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "helper_green_is_contract_boundary_only",
    "helper_green_is_not_actual_human_review_complete",
    "historical_helper_refs_are_not_current_execution_basis",
    "synthetic_contract_rows_are_not_actual_review_rows",
    "r52_handoff_ready_contract_is_not_actual_r52_reintake_execution",
)

P7_R54_AHR_OUT_OF_SCOPE_REFS: Final[tuple[str, ...]] = (
    "api_route_or_response_key_change",
    "api_route_or_request_response_key_change",
    "db_schema_or_migration_change",
    "rn_production_ui_or_visible_title_change",
    "runtime_generation_or_gate_threshold_change",
    "public_response_contract_change",
    "p8_question_design_or_implementation",
    "p8_question_text_or_draft_text_creation",
    "p8_question_trigger_storage_or_ui",
    "p6_limited_human_readfeel_start",
    "p5_confirmed_final_promotion",
    "p7_complete_or_release_decision",
    "body_full_packet_generation",
    "actual_human_review_execution",
    "actual_human_review_execution_or_completion_claim",
    "actual_rating_rows_from_real_review",
    "actual_question_need_observation_rows_from_real_review",
    "actual_disposal_or_purge_receipt",
    "actual_r52_reintake_execution",
)

P7_R54_AHR_NO_TOUCH_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "api_changed",
    "db_changed",
    "rn_changed",
    "runtime_changed",
    "api_route_changed",
    "request_key_changed",
    "response_key_changed",
    "response_shape_changed",
    "db_schema_changed",
    "db_migration_added",
    "db_physical_schema_changed",
    "rn_ui_changed",
    "rn_visible_contract_changed",
    "public_response_key_changed",
    "public_response_top_level_key_added",
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
    "body_full_packet_generation_requested_here",
    "body_full_generation_requested_here",
    "body_full_packet_generated_here",
    "actual_human_review_run_here",
    "actual_human_review_executed_by_person",
    "actual_manual_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "actual_r52_reintake_execution_confirmed",
    "r54_clr_historical_refs_used_as_actual_execution_basis",
    "actual_review_evidence_complete",
    "disposal_verified",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_human_blind_qa_confirmed_final",
    "p5_final_allowed",
    "p6_limited_human_readfeel_start_allowed",
    "p6_start_allowed",
    "p8_start_allowed",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_confirmed",
    "real_device_modal_verified",
    "rn_real_device_modal_verified",
)
P7_R54_AHR_BODY_FREE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "raw_input_included",
    "raw_body_included",
    "returned_emlis_body_included",
    "history_surface_included",
    "comment_text_included",
    "reviewer_free_text_included",
    "reviewer_notes_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    "local_absolute_path_included",
    "body_hash_included",
    "packet_content_included",
    "terminal_output_body_included",
    "stdout_body_included",
    "stderr_body_included",
    "traceback_body_included",
)
P7_R54_AHR_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_NO_TOUCH_FALSE_FLAG_REFS,
    *P7_R54_AHR_BODY_FREE_FALSE_FLAG_REFS,
)
P7_R54_AHR_FORBIDDEN_BODY_OR_QUESTION_KEYS: Final[frozenset[str]] = frozenset(
    {
        "raw_input",
        "raw_body",
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
        "stdout_body",
        "stderr_body",
        "traceback_body",
    }
)

P7_R54_AHR_BASE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
P7_R54_AHR_CURRENT_EXECUTION_BASIS_FIELD_REFS: Final[tuple[str, ...]] = (
    "current_execution_basis_refs",
    "current_execution_basis_ref_count",
    "current_execution_basis_ref_keys",
    "current_execution_basis_ref_key_count",
    "operation_current_refs",
    "operation_current_ref_count",
    "operation_current_ref_keys",
    "operation_current_ref_key_count",
    "required_current_execution_basis_ref_keys",
    "required_current_execution_basis_ref_key_count",
    "all_required_current_execution_basis_refs_present",
    "actual_execution_basis_ref",
    "actual_execution_basis_allowed",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "current_execution_basis_refs_are_actual_execution_basis",
    "current_execution_basis_refs_used_as_actual_execution_basis",
    "operation_current_refs_are_actual_execution_basis",
    "operation_current_refs_used_as_actual_execution_basis",
)
P7_R54_AHR_SCOPE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_BASE_REQUIRED_FIELD_REFS,
    "scope_boundary_confirmed",
    "no_touch_boundary_confirmed",
    "no_touch_boundary_frozen",
    "ahr_line_selected",
    "r54_ahr_prefix_used",
    *P7_R54_AHR_CURRENT_EXECUTION_BASIS_FIELD_REFS,
    "current_execution_basis_refs_are_current_snapshot_candidate",
    "current_execution_basis_refs_are_current_received_snapshot_candidate",
    "current_execution_basis_refreeze_required_next",
    "allowed_operation_step_refs",
    "out_of_scope_refs",
    "existing_r54_op00_contract_available",
    "existing_r54_ev00_contract_available",
    "existing_r54_clr00_contract_available",
    "existing_helper_refs_can_be_used_for_helper_regression_only",
    "existing_helper_refs_can_be_used_for_actual_execution_basis",
    "historical_helper_ref_groups",
    "historical_helper_refs_must_be_separated",
    "historical_helper_refs_used_as_actual_execution_basis",
    "r54_clr_historical_refs_used_as_actual_execution_basis",
    "old_helper_refs_allowed_as_actual_execution_basis",
    "current_execution_basis_required_before_actual_review",
    "p8_p6_release_api_db_rn_runtime_out_of_scope",
    "p8_question_design_not_started_here",
    "api_db_rn_runtime_no_touch_boundary_frozen",
    "body_full_generation_blocked_until_later_preflight",
    "body_full_generation_blocked_until_preflight",
    "human_review_completion_claim_blocked_here",
    "actual_review_completion_claim_blocked_here",
    "actual_human_review_completion_claim_blocked_here",
    "actual_rating_or_question_rows_claim_blocked_here",
    "disposal_receipt_claim_blocked_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "r54_ahr_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R54_AHR_FALSE_FLAG_REFS,
)
P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_BASE_REQUIRED_FIELD_REFS,
    "ahr00_schema_version",
    "ahr00_material_ref",
    "ahr00_next_required_step",
    "ahr00_scope_boundary_confirmed",
    "ahr00_no_touch_boundary_confirmed",
    "execution_basis_envelope_schema_version",
    "current_execution_basis_refreeze_status_ref",
    "current_execution_basis_refrozen",
    "current_execution_basis_source_mode",
    *P7_R54_AHR_CURRENT_EXECUTION_BASIS_FIELD_REFS,
    "operation_current_refs_match_current_execution_basis_260_83_256_169",
    "current_execution_basis_refs_match_received_snapshot_260_83_256_169",
    "current_execution_basis_refs_match_260_83_256_169_snapshot",
    "historical_helper_ref_groups",
    "historical_helper_ref_group_count",
    "historical_helper_refs",
    "historical_helper_refs_separated",
    "historical_helper_refs_are_historical_here",
    "historical_helper_refs_are_structural_refs_only",
    "historical_helper_refs_can_be_used_for_helper_regression_only",
    "existing_helper_refs_can_be_used_for_helper_regression_only",
    "historical_helper_refs_can_be_used_for_actual_execution_basis",
    "historical_helper_refs_used_as_actual_execution_basis",
    "r54_clr_historical_refs_used_as_actual_execution_basis",
    "old_helper_refs_allowed_as_actual_execution_basis",
    "old_helper_refs_match_current_execution_basis_260_83_256_169",
    "r52_refs_are_historical_here",
    "r54_bodyfree_handoff_refs_are_historical_here",
    "r55_refs_are_historical_here",
    "r54_op_refs_are_historical_here",
    "r54_ev_refs_are_historical_here",
    "r54_clr_refs_are_historical_here",
    "r54_clr_current_refs_are_historical_here",
    "r54_clr_current_refs_match_current_execution_basis_260_83_256_169",
    "r52_refs_used_as_actual_execution_basis",
    "r54_bodyfree_handoff_refs_used_as_actual_execution_basis",
    "r55_refs_used_as_actual_execution_basis",
    "r54_op_refs_used_as_actual_execution_basis",
    "r54_ev_refs_used_as_actual_execution_basis",
    "r54_clr_refs_used_as_actual_execution_basis",
    "historical_helper_refs_match_current_execution_basis_260_83_256_169",
    "historical_helper_differing_current_execution_basis_ref_keys",
    "historical_helper_differing_execution_basis_ref_keys",
    "historical_helper_differing_current_execution_basis_ref_key_counts",
    "differing_current_execution_basis_ref_group_count",
    "differing_execution_basis_ref_group_count",
    "historical_helper_ref_comparison_status_ref",
    "current_execution_basis_refreeze_completed_here",
    "current_refs_refreeze_does_not_rewrite_historical_helpers",
    "current_execution_basis_refreeze_does_not_rewrite_historical_helpers",
    "historical_helper_refs_reconcile_required_next",
    "current_refs_override_uses_thin_ahr_boundary_layer",
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
    "actual_rating_or_question_rows_claim_blocked_here",
    "disposal_receipt_claim_blocked_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "r54_ahr_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R54_AHR_FALSE_FLAG_REFS,
)



P7_R54_AHR_HISTORICAL_HELPER_REFS_RECONCILE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_BASE_REQUIRED_FIELD_REFS,
    "ahr01_schema_version",
    "ahr01_material_ref",
    "ahr01_next_required_step",
    "ahr01_current_execution_basis_refrozen",
    "ahr01_current_execution_basis_refreeze_status_ref",
    *P7_R54_AHR_CURRENT_EXECUTION_BASIS_FIELD_REFS,
    "operation_current_refs_match_current_execution_basis_260_83_256_169",
    "current_execution_basis_refs_match_received_snapshot_260_83_256_169",
    "current_execution_basis_refs_match_260_83_256_169_snapshot",
    "historical_helper_refs_reconcile_status_ref",
    "historical_helper_refs_reconciled",
    "historical_helper_ref_groups",
    "historical_helper_ref_group_count",
    "historical_helper_refs",
    "historical_helper_ref_rows",
    "historical_helper_role_refs",
    "historical_helper_classification_refs",
    "historical_helper_refs_match_current_execution_basis_260_83_256_169",
    "historical_helper_differing_current_execution_basis_ref_keys",
    "historical_helper_differing_current_execution_basis_ref_key_counts",
    "differing_current_execution_basis_ref_group_count",
    "r52_refs_reconciled_as_actual_evidence_decision_gate",
    "r54_bodyfree_handoff_refs_reconciled_as_bodyfree_handoff_contract",
    "r55_refs_reconciled_as_evidence_missing_hold_contract",
    "r54_op_refs_reconciled_as_operation_structural_helper",
    "r54_ev_refs_reconciled_as_evidence_materialization_structural_helper",
    "r54_clr_refs_reconciled_as_current_snapshot_local_run_structural_helper",
    "historical_helper_refs_are_historical_here",
    "historical_helper_refs_are_structural_refs_only",
    "historical_helper_refs_are_contract_refs_only",
    "historical_helper_refs_can_be_used_for_helper_regression_only",
    "existing_helper_refs_can_be_used_for_helper_regression_only",
    "historical_helper_refs_can_be_used_for_actual_execution_basis",
    "historical_helper_refs_used_as_actual_execution_basis",
    "r54_clr_historical_refs_used_as_actual_execution_basis",
    "old_helper_refs_allowed_as_actual_execution_basis",
    "r54_clr_current_refs_are_historical_here",
    "r54_clr_current_refs_preserved_as_historical",
    "r54_clr_current_refs_not_rewritten",
    "r54_clr_current_refs_match_current_execution_basis_260_83_256_169",
    "historical_helper_green_claim_boundary_refs",
    "helper_green_not_actual_human_review_complete",
    "synthetic_contract_rows_not_actual_review_rows",
    "r52_handoff_ready_contract_not_actual_r52_reintake_execution",
    "reconcile_does_not_modify_helper_modules",
    "existing_helper_constants_not_rewritten",
    "existing_helper_constants_rewritten",
    "existing_helper_refs_preserved_as_received",
    "current_refs_override_uses_thin_ahr_boundary_layer",
    "new_thin_boundary_helper_only",
    "new_full_operation_helper_required_here",
    "body_full_generation_blocked_until_later_preflight",
    "body_full_generation_blocked_until_preflight",
    "human_review_completion_claim_blocked_here",
    "actual_review_completion_claim_blocked_here",
    "actual_human_review_completion_claim_blocked_here",
    "actual_rating_or_question_rows_claim_blocked_here",
    "disposal_receipt_claim_blocked_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "r54_ahr_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R54_AHR_FALSE_FLAG_REFS,
)

P7_R54_AHR_R55_HOLD_EVIDENCE_MISSING_INTAKE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_BASE_REQUIRED_FIELD_REFS,
    "ahr02_schema_version",
    "ahr02_material_ref",
    "ahr02_next_required_step",
    "ahr02_historical_helper_refs_reconciled",
    *P7_R54_AHR_CURRENT_EXECUTION_BASIS_FIELD_REFS,
    "operation_current_refs_match_current_execution_basis_260_83_256_169",
    "current_execution_basis_refs_match_received_snapshot_260_83_256_169",
    "current_execution_basis_refs_match_260_83_256_169_snapshot",
    "r55_hold_intake_status_ref",
    "r55_hold_intaken",
    "r55_actual_review_evidence_gap_assessment_schema_version",
    "r55_actual_review_evidence_gap_assessment_material_ref",
    "r55_r52_reintake_decision_materialization_schema_version",
    "r55_r52_reintake_decision_materialization_material_ref",
    "r55_gap_assessment_intaken",
    "r55_decision_materialization_intaken",
    "r55_gap_status_ref",
    "actual_review_evidence_gap_status_ref",
    "actual_review_evidence_missing_confirmed",
    "r54_handoff_status_ref",
    "r54_review_operation_state_ref",
    "p5_decision_before_run",
    "p5_decision_status_ref",
    "r52_reintake_status_before_run",
    "r55_decision_ref",
    "r52_existing_decision_equivalent",
    "decision_status",
    "decision_reason_refs",
    "decision_reason_ref_count",
    "r55_next_required_step",
    "required_case_count",
    "reviewed_case_count",
    "sanitized_review_result_row_count",
    "rating_row_count",
    "question_observation_row_count",
    "missing_evidence_refs",
    "missing_evidence_ref_count",
    "r55_missing_evidence_refs_match_default",
    "actual_rating_rows_missing",
    "actual_question_observation_rows_missing",
    "actual_disposal_receipt_missing",
    "actual_r52_reintake_blocked_before_run",
    "r52_handoff_ready_before_actual_review",
    "r52_reintake_ready_before_actual_review",
    "p5_confirmed_candidate_before_actual_review",
    "p8_material_candidate_before_actual_review",
    "next_required_step_is_local_only_preflight",
    "body_full_generation_blocked_until_later_preflight",
    "body_full_generation_blocked_until_preflight",
    "human_review_completion_claim_blocked_here",
    "actual_review_completion_claim_blocked_here",
    "actual_human_review_completion_claim_blocked_here",
    "actual_rating_or_question_rows_claim_blocked_here",
    "disposal_receipt_claim_blocked_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "r54_ahr_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R54_AHR_FALSE_FLAG_REFS,
)
P7_R54_AHR_LOCAL_ONLY_PREFLIGHT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_BASE_REQUIRED_FIELD_REFS,
    "ahr03_schema_version",
    "ahr03_material_ref",
    "ahr03_next_required_step",
    "ahr03_r55_gap_status_ref",
    "ahr03_actual_review_evidence_missing_confirmed",
    "ahr03_r52_reintake_status_before_run",
    *P7_R54_AHR_CURRENT_EXECUTION_BASIS_FIELD_REFS,
    "operation_current_refs_match_current_execution_basis_260_83_256_169",
    "current_execution_basis_refs_match_received_snapshot_260_83_256_169",
    "current_execution_basis_refs_match_260_83_256_169_snapshot",
    "local_only",
    "must_not_export",
    "disposal_required",
    "local_only_root_ref",
    "local_only_root_available",
    "local_only_root_is_ref_only",
    "explicit_allow_token_ref",
    "explicit_allow_token_present",
    "review_session_present",
    "review_session_present_ref",
    "current_execution_basis_refreeze_ready",
    "historical_helper_refs_reconciled_before_preflight",
    "r55_hold_intaken_before_preflight",
    "manifest_source_ref",
    "manifest_source_available",
    "export_denylist_ref",
    "export_denylist_ready",
    "export_denylist_refs",
    "export_denylist_ref_count",
    "forbidden_output_refs",
    "forbidden_output_ref_count",
    "purge_plan_ref",
    "purge_plan_ready",
    "body_full_artifact_public_export_allowed",
    "terminal_output_body_allowed",
    "api_db_rn_runtime_touch_allowed",
    "api_db_rn_runtime_no_touch",
    "preflight_status",
    "preflight_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "body_full_packet_generation_allowed_before_preflight",
    "body_full_packet_generation_allowed_by_preflight",
    "body_full_packet_generation_request_allowed_next",
    "body_full_generation_blocked_until_manifest_freeze",
    "actual_review_execution_blocked_until_packet_and_manifest_ready",
    "human_review_completion_claim_blocked_here",
    "actual_review_completion_claim_blocked_here",
    "actual_human_review_completion_claim_blocked_here",
    "actual_rating_or_question_rows_claim_blocked_here",
    "disposal_receipt_claim_blocked_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "r54_ahr_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R54_AHR_FALSE_FLAG_REFS,
)

P7_R54_AHR_24_CASE_MANIFEST_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_BASE_REQUIRED_FIELD_REFS,
    "ahr04_schema_version",
    "ahr04_material_ref",
    "ahr04_next_required_step",
    "ahr04_preflight_status",
    "ahr04_body_full_packet_generation_allowed_by_preflight",
    "local_only_preflight_ready",
    *P7_R54_AHR_CURRENT_EXECUTION_BASIS_FIELD_REFS,
    "operation_current_refs_match_current_execution_basis_260_83_256_169",
    "current_execution_basis_refs_match_received_snapshot_260_83_256_169",
    "current_execution_basis_refs_match_260_83_256_169_snapshot",
    "manifest_source_kind_ref",
    "r48_case_matrix_schema_version",
    "r48_case_matrix_material_ref",
    "r48_case_matrix_case_count",
    "required_case_count",
    "case_distribution",
    "case_distribution_total_count",
    "case_distribution_matches_design",
    "manifest_status",
    "manifest_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "case_rows",
    "case_row_count",
    "case_rows_bodyfree_only",
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
    "family_case_counts",
    "case_role_counts",
    "subscription_tier_ref_counts",
    "history_evidence_policy_ref_counts",
    "review_axis_profile_ref",
    "rating_axis_refs",
    "rating_axis_count",
    "rating_axis_target_thresholds",
    "requires_history_line_review_count",
    "current_only_boundary_case_count",
    "reviewer_facing_family_exposed",
    "reviewer_facing_tier_exposed",
    "body_full_packet_materialized_here",
    "local_reviewer_payload_materialized_here",
    "body_full_packet_generation_requested_here",
    "body_full_packet_generated_here",
    "actual_human_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "body_full_packet_generation_request_allowed_next",
    "body_full_generation_blocked_until_packet_generation_request",
    "human_review_completion_claim_blocked_here",
    "actual_review_completion_claim_blocked_here",
    "actual_human_review_completion_claim_blocked_here",
    "actual_rating_or_question_rows_claim_blocked_here",
    "disposal_receipt_claim_blocked_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "r54_ahr_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R54_AHR_FALSE_FLAG_REFS,
)

P7_R54_AHR06_BODY_FULL_PACKET_GENERATION_REQUEST_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_BASE_REQUIRED_FIELD_REFS,
    "ahr05_schema_version",
    "ahr05_material_ref",
    "ahr05_next_required_step",
    "ahr05_manifest_status",
    "ahr05_required_case_count",
    "ahr05_case_row_count",
    "ahr05_case_ref_id_count",
    "ahr05_blind_case_id_count",
    "ahr05_packet_ref_id_count",
    "ahr05_body_full_packet_generation_request_allowed_next",
    "ahr05_case_rows_bodyfree_only",
    *P7_R54_AHR_CURRENT_EXECUTION_BASIS_FIELD_REFS,
    "operation_current_refs_match_current_execution_basis_260_83_256_169",
    "current_execution_basis_refs_match_received_snapshot_260_83_256_169",
    "current_execution_basis_refs_match_260_83_256_169_snapshot",
    "packet_generation_request_status",
    "packet_generation_request_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "manifest_ready_for_packet_generation_request",
    "body_full_packet_generation_request_allowed_from_manifest",
    "local_only",
    "must_not_export",
    "disposal_required",
    "explicit_allow_token_ref",
    "explicit_allow_token_present",
    "packet_generation_request_ref",
    "packet_generation_request_ref_present",
    "packet_generation_request_is_ref_only",
    "local_packet_generation_operation_ref",
    "local_packet_generation_operation_ref_only",
    "required_case_count",
    "case_row_count",
    "case_ref_ids",
    "case_ref_id_count",
    "blind_case_ids",
    "blind_case_id_count",
    "packet_ref_ids",
    "packet_ref_id_count",
    "packet_ref_ids_unique",
    "packet_generation_requested",
    "packet_generation_requested_as_bodyfree_evidence_only",
    "body_full_packet_generation_request_evidence_only",
    "body_full_packet_generation_requested_here",
    "body_full_generation_requested_here",
    "body_full_packet_generated_here",
    "body_full_packet_materialized_here",
    "local_reviewer_payload_materialized_here",
    "local_packet_generation_operation_allowed_next",
    "local_packet_generation_receipt_required_next",
    "actual_review_execution_blocked_until_local_packet_receipt",
    "human_review_completion_claim_blocked_here",
    "actual_review_completion_claim_blocked_here",
    "actual_human_review_completion_claim_blocked_here",
    "actual_rating_or_question_rows_claim_blocked_here",
    "disposal_receipt_claim_blocked_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    *P7_R54_AHR06_FORBIDDEN_EVIDENCE_FLAG_REFS,
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "r54_ahr_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R54_AHR_FALSE_FLAG_REFS,
)

P7_R54_AHR07_LOCAL_PACKET_GENERATION_RECEIPT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_BASE_REQUIRED_FIELD_REFS,
    "ahr06_schema_version",
    "ahr06_material_ref",
    "ahr06_next_required_step",
    "ahr06_packet_generation_request_status",
    "ahr06_packet_generation_requested",
    "ahr06_local_packet_generation_operation_allowed_next",
    "ahr06_required_case_count",
    "ahr06_packet_ref_id_count",
    "ahr06_packet_ref_ids",
    *P7_R54_AHR_CURRENT_EXECUTION_BASIS_FIELD_REFS,
    "operation_current_refs_match_current_execution_basis_260_83_256_169",
    "current_execution_basis_refs_match_received_snapshot_260_83_256_169",
    "current_execution_basis_refs_match_260_83_256_169_snapshot",
    "receipt_status",
    "generation_status_ref",
    "receipt_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "request_ready_for_receipt_intake",
    "required_case_count",
    "expected_generated_case_count",
    "expected_generated_packet_count",
    "generated_case_count",
    "generated_packet_count",
    "generated_packet_refs_match_expected_count",
    "local_only",
    "must_not_export",
    "exported",
    "local_packet_exported",
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
    "body_full_packet_generated_here",
    "actual_human_review_run_here",
    "actual_review_execution_allowed_next",
    "packet_generation_operation_receipt_only",
    "local_packet_generation_operation_receipt_intaken",
    "packet_generation_receipt_intaken",
    "packet_completeness_export_denylist_scan_allowed_next",
    "actual_review_execution_blocked_until_packet_completeness_scan",
    "human_review_completion_claim_blocked_here",
    "actual_review_completion_claim_blocked_here",
    "actual_human_review_completion_claim_blocked_here",
    "actual_rating_or_question_rows_claim_blocked_here",
    "disposal_receipt_claim_blocked_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "r54_ahr_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R54_AHR_FALSE_FLAG_REFS,
)


def _safe_review_session_id(value: Any) -> str:
    return clean_identifier(value, default=P7_R54_AHR_DEFAULT_REVIEW_SESSION_ID, max_length=120)


def _false_flags() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_FALSE_FLAG_REFS}


def _no_touch_contract() -> dict[str, bool]:
    return {
        "api_route_changed": False,
        "request_key_changed": False,
        "response_key_changed": False,
        "db_schema_changed": False,
        "db_migration_added": False,
        "rn_ui_changed": False,
        "rn_visible_contract_changed": False,
        "runtime_changed": False,
        "public_response_top_level_key_added": False,
        "p8_question_implementation_spec_finalized_here": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
    }


def _body_free_markers() -> dict[str, bool]:
    markers = body_free_flags(include_history=True, include_reviewer=True, include_terminal=True)
    markers.update(
        {
            "raw_body_included": False,
            "returned_emlis_body_included": False,
            "history_surface_included": False,
            "reviewer_notes_body_included": False,
            "question_text_included": False,
            "draft_question_text_included": False,
            "local_absolute_path_included": False,
            "body_hash_included": False,
            "packet_content_included": False,
            "terminal_output_body_included": False,
        }
    )
    return markers


def _contains_forbidden_ahr_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in P7_R54_AHR_FORBIDDEN_BODY_OR_QUESTION_KEYS:
                return True
            if _contains_forbidden_ahr_key(child):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_ahr_key(child) for child in value)
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
    if data.get("step") != P7_R54_AHR_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R54_AHR_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("policy_kind") != P7_R54_AHR_POLICY_KIND:
        raise ValueError(f"{source} policy kind changed")
    if data.get("policy_section") != policy_section or data.get("operation_step_ref") != operation_step_ref:
        raise ValueError(f"{source} operation step changed")
    if data.get("source_mode") != P7_SOURCE_MODE:
        raise ValueError(f"{source} source mode changed")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} must keep Git connection unchecked / not required")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must remain body-free")
    if _contains_forbidden_ahr_key(data):
        raise ValueError(f"{source} contains forbidden body-full/question/path/hash key")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)
    assert_false_markers({key: data.get(key) for key in P7_R54_AHR_FALSE_FLAG_REFS}, source=source)
    public_contract = safe_mapping(data.get("public_contract"))
    if public_contract != public_contract_flags():
        raise ValueError(f"{source} public contract flags changed")
    assert_false_markers(public_contract, source=f"{source} public contract")
    no_touch_contract = safe_mapping(data.get("r54_ahr_no_touch_contract"))
    if no_touch_contract != _no_touch_contract():
        raise ValueError(f"{source} no-touch contract changed")
    assert_false_markers(no_touch_contract, source=f"{source} no-touch contract")
    body_markers = safe_mapping(data.get("body_free_markers"))
    if body_markers != _body_free_markers():
        raise ValueError(f"{source} body-free markers changed")
    assert_false_markers(body_markers, source=f"{source} body-free markers")


def _assert_current_execution_basis_refs(data: Mapping[str, Any], *, source: str, actual_basis: bool) -> None:
    refs = safe_mapping(data.get("current_execution_basis_refs"))
    if refs != P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS:
        raise ValueError(f"{source} current execution basis refs changed")
    if safe_mapping(data.get("operation_current_refs")) != P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS:
        raise ValueError(f"{source} operation current refs changed")
    expected_keys = P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS
    for field in ("current_execution_basis_ref_keys", "operation_current_ref_keys", "required_current_execution_basis_ref_keys"):
        if tuple(data.get(field) or ()) != expected_keys:
            raise ValueError(f"{source} {field} changed")
    expected_count = len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS)
    for field in (
        "current_execution_basis_ref_count",
        "current_execution_basis_ref_key_count",
        "operation_current_ref_count",
        "operation_current_ref_key_count",
        "required_current_execution_basis_ref_key_count",
    ):
        if data.get(field) != expected_count:
            raise ValueError(f"{source} {field} changed")
    if data.get("all_required_current_execution_basis_refs_present") is not True:
        raise ValueError(f"{source} must carry all required current execution basis refs")
    if data.get("actual_execution_basis_ref") != P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF:
        raise ValueError(f"{source} actual execution basis ref changed")
    if data.get("actual_execution_basis_allowed") != P7_R54_AHR_ACTUAL_EXECUTION_BASIS_ALLOWED_REF:
        raise ValueError(f"{source} actual execution basis allowed ref changed")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF:
        raise ValueError(f"{source} actual review basis ref alias changed")
    if data.get("actual_review_basis_allowed") != P7_R54_AHR_ACTUAL_EXECUTION_BASIS_ALLOWED_REF:
        raise ValueError(f"{source} actual review basis allowed alias changed")
    for field in (
        "current_execution_basis_refs_are_actual_execution_basis",
        "current_execution_basis_refs_used_as_actual_execution_basis",
        "operation_current_refs_are_actual_execution_basis",
        "operation_current_refs_used_as_actual_execution_basis",
    ):
        if data.get(field) is not actual_basis:
            raise ValueError(f"{source} {field} changed")


def _historical_diff_keys_by_group() -> dict[str, list[str]]:
    return {
        group_ref: [
            key
            for key, current_value in P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS.items()
            if refs.get(key) != current_value
        ]
        for group_ref, refs in P7_R54_AHR_HISTORICAL_HELPER_REFS.items()
    }


def build_p7_r54_ahr00_scope_no_touch_boundary_freeze(
    *, review_session_id: Any = P7_R54_AHR_DEFAULT_REVIEW_SESSION_ID
) -> dict[str, Any]:
    """Build R54-AHR-00 body-free scope / no-touch boundary material."""

    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_STEP,
        "scope": P7_R54_AHR_SCOPE,
        "policy_kind": P7_R54_AHR_POLICY_KIND,
        "policy_section": P7_R54_AHR00_STEP_REF,
        "operation_step_ref": P7_R54_AHR00_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr00_scope_no_touch_boundary_20260627",
        "review_session_id": _safe_review_session_id(review_session_id),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "scope_boundary_confirmed": True,
        "no_touch_boundary_confirmed": True,
        "no_touch_boundary_frozen": True,
        "ahr_line_selected": True,
        "r54_ahr_prefix_used": True,
        "current_execution_basis_refs": dict(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "current_execution_basis_ref_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "current_execution_basis_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "current_execution_basis_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_refs": dict(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_ref_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "operation_current_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "required_current_execution_basis_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "required_current_execution_basis_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "all_required_current_execution_basis_refs_present": True,
        "actual_execution_basis_ref": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF,
        "actual_execution_basis_allowed": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_ALLOWED_REF,
        "actual_review_basis_ref": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_ALLOWED_REF,
        "current_execution_basis_refs_are_actual_execution_basis": False,
        "current_execution_basis_refs_used_as_actual_execution_basis": False,
        "operation_current_refs_are_actual_execution_basis": False,
        "operation_current_refs_used_as_actual_execution_basis": False,
        "current_execution_basis_refs_are_current_snapshot_candidate": True,
        "current_execution_basis_refs_are_current_received_snapshot_candidate": True,
        "current_execution_basis_refreeze_required_next": True,
        "allowed_operation_step_refs": [P7_R54_AHR00_STEP_REF, P7_R54_AHR01_STEP_REF],
        "out_of_scope_refs": list(P7_R54_AHR_OUT_OF_SCOPE_REFS),
        "existing_r54_op00_contract_available": hasattr(
            r54op, "assert_p7_r54_op00_scope_no_touch_boundary_freeze_contract"
        ),
        "existing_r54_ev00_contract_available": hasattr(
            r54ev, "assert_p7_r54_ev00_scope_no_touch_boundary_confirmation_contract"
        ),
        "existing_r54_clr00_contract_available": hasattr(
            r54clr, "assert_p7_r54_clr00_scope_no_touch_boundary_freeze_contract"
        ),
        "existing_helper_refs_can_be_used_for_helper_regression_only": True,
        "existing_helper_refs_can_be_used_for_actual_execution_basis": False,
        "historical_helper_ref_groups": list(P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS),
        "historical_helper_refs_must_be_separated": True,
        "historical_helper_refs_used_as_actual_execution_basis": False,
        "r54_clr_historical_refs_used_as_actual_execution_basis": False,
        "old_helper_refs_allowed_as_actual_execution_basis": False,
        "current_execution_basis_required_before_actual_review": True,
        "p8_p6_release_api_db_rn_runtime_out_of_scope": True,
        "p8_question_design_not_started_here": True,
        "api_db_rn_runtime_no_touch_boundary_frozen": True,
        "body_full_generation_blocked_until_later_preflight": True,
        "body_full_generation_blocked_until_preflight": True,
        "human_review_completion_claim_blocked_here": True,
        "actual_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_rating_or_question_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR00_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR00_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR01_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_ahr00_scope_no_touch_boundary_freeze_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_SCOPE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR00 scope/no-touch boundary",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION,
        policy_section=P7_R54_AHR00_STEP_REF,
        operation_step_ref=P7_R54_AHR00_STEP_REF,
        source="P7-R54-AHR00 scope/no-touch boundary",
    )
    _assert_current_execution_basis_refs(data, source="P7-R54-AHR00 scope/no-touch boundary", actual_basis=False)
    for key in (
        "scope_boundary_confirmed",
        "no_touch_boundary_confirmed",
        "no_touch_boundary_frozen",
        "ahr_line_selected",
        "r54_ahr_prefix_used",
        "current_execution_basis_refs_are_current_snapshot_candidate",
        "current_execution_basis_refs_are_current_received_snapshot_candidate",
        "current_execution_basis_refreeze_required_next",
        "existing_helper_refs_can_be_used_for_helper_regression_only",
        "historical_helper_refs_must_be_separated",
        "current_execution_basis_required_before_actual_review",
        "p8_p6_release_api_db_rn_runtime_out_of_scope",
        "p8_question_design_not_started_here",
        "api_db_rn_runtime_no_touch_boundary_frozen",
        "body_full_generation_blocked_until_later_preflight",
        "body_full_generation_blocked_until_preflight",
        "human_review_completion_claim_blocked_here",
        "actual_review_completion_claim_blocked_here",
        "actual_human_review_completion_claim_blocked_here",
        "actual_rating_or_question_rows_claim_blocked_here",
        "disposal_receipt_claim_blocked_here",
        "r52_reintake_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR00 must keep {key}=True")
    for key in (
        "existing_helper_refs_can_be_used_for_actual_execution_basis",
        "historical_helper_refs_used_as_actual_execution_basis",
        "r54_clr_historical_refs_used_as_actual_execution_basis",
        "old_helper_refs_allowed_as_actual_execution_basis",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR00 must keep {key}=False")
    if tuple(data.get("historical_helper_ref_groups") or ()) != P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS:
        raise ValueError("P7-R54-AHR00 historical helper ref groups changed")
    if tuple(data.get("allowed_operation_step_refs") or ()) != (P7_R54_AHR00_STEP_REF, P7_R54_AHR01_STEP_REF):
        raise ValueError("P7-R54-AHR00 allowed operation steps changed")
    if tuple(data.get("out_of_scope_refs") or ()) != P7_R54_AHR_OUT_OF_SCOPE_REFS:
        raise ValueError("P7-R54-AHR00 out-of-scope refs changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR00_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR00 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR00_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR00 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R54_AHR01_STEP_REF:
        raise ValueError("P7-R54-AHR00 next required step changed")
    return True


def build_p7_r54_ahr01_current_execution_basis_refreeze(
    *,
    scope_no_touch_boundary_freeze: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build R54-AHR-01 body-free current execution basis refreeze material."""

    ahr00 = dict(scope_no_touch_boundary_freeze or build_p7_r54_ahr00_scope_no_touch_boundary_freeze())
    assert_p7_r54_ahr00_scope_no_touch_boundary_freeze_contract(ahr00)
    differing = _historical_diff_keys_by_group()
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_STEP,
        "scope": P7_R54_AHR_SCOPE,
        "policy_kind": P7_R54_AHR_POLICY_KIND,
        "policy_section": P7_R54_AHR01_STEP_REF,
        "operation_step_ref": P7_R54_AHR01_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr01_current_execution_basis_refreeze_20260627",
        "review_session_id": _safe_review_session_id(review_session_id or ahr00.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ahr00_schema_version": ahr00["schema_version"],
        "ahr00_material_ref": ahr00["material_id"],
        "ahr00_next_required_step": ahr00["next_required_step"],
        "ahr00_scope_boundary_confirmed": ahr00["scope_boundary_confirmed"],
        "ahr00_no_touch_boundary_confirmed": ahr00["no_touch_boundary_confirmed"],
        "execution_basis_envelope_schema_version": P7_R54_AHR_EXECUTION_BASIS_ENVELOPE_SCHEMA_VERSION,
        "current_execution_basis_refreeze_status_ref": P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFREEZE_STATUS_REF,
        "current_execution_basis_refrozen": True,
        "current_execution_basis_source_mode": P7_SOURCE_MODE,
        "current_execution_basis_refs": dict(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "current_execution_basis_ref_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "current_execution_basis_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "current_execution_basis_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_refs": dict(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_ref_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "operation_current_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "required_current_execution_basis_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "required_current_execution_basis_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "all_required_current_execution_basis_refs_present": True,
        "actual_execution_basis_ref": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF,
        "actual_execution_basis_allowed": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_ALLOWED_REF,
        "actual_review_basis_ref": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_ALLOWED_REF,
        "current_execution_basis_refs_are_actual_execution_basis": True,
        "current_execution_basis_refs_used_as_actual_execution_basis": True,
        "operation_current_refs_are_actual_execution_basis": True,
        "operation_current_refs_used_as_actual_execution_basis": True,
        "operation_current_refs_match_current_execution_basis_260_83_256_169": True,
        "current_execution_basis_refs_match_received_snapshot_260_83_256_169": True,
        "current_execution_basis_refs_match_260_83_256_169_snapshot": True,
        "historical_helper_ref_groups": list(P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS),
        "historical_helper_ref_group_count": len(P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS),
        "historical_helper_refs": {key: dict(value) for key, value in P7_R54_AHR_HISTORICAL_HELPER_REFS.items()},
        "historical_helper_refs_separated": True,
        "historical_helper_refs_are_historical_here": True,
        "historical_helper_refs_are_structural_refs_only": True,
        "historical_helper_refs_can_be_used_for_helper_regression_only": True,
        "existing_helper_refs_can_be_used_for_helper_regression_only": True,
        "historical_helper_refs_can_be_used_for_actual_execution_basis": False,
        "historical_helper_refs_used_as_actual_execution_basis": False,
        "r54_clr_historical_refs_used_as_actual_execution_basis": False,
        "old_helper_refs_allowed_as_actual_execution_basis": False,
        "old_helper_refs_match_current_execution_basis_260_83_256_169": False,
        "r52_refs_are_historical_here": True,
        "r54_bodyfree_handoff_refs_are_historical_here": True,
        "r55_refs_are_historical_here": True,
        "r54_op_refs_are_historical_here": True,
        "r54_ev_refs_are_historical_here": True,
        "r54_clr_refs_are_historical_here": True,
        "r54_clr_current_refs_are_historical_here": True,
        "r54_clr_current_refs_match_current_execution_basis_260_83_256_169": False,
        "r52_refs_used_as_actual_execution_basis": False,
        "r54_bodyfree_handoff_refs_used_as_actual_execution_basis": False,
        "r55_refs_used_as_actual_execution_basis": False,
        "r54_op_refs_used_as_actual_execution_basis": False,
        "r54_ev_refs_used_as_actual_execution_basis": False,
        "r54_clr_refs_used_as_actual_execution_basis": False,
        "historical_helper_refs_match_current_execution_basis_260_83_256_169": {
            group_ref: False for group_ref in P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS
        },
        "historical_helper_differing_current_execution_basis_ref_keys": differing,
        "historical_helper_differing_execution_basis_ref_keys": differing,
        "historical_helper_differing_current_execution_basis_ref_key_counts": {
            group_ref: len(keys) for group_ref, keys in differing.items()
        },
        "differing_current_execution_basis_ref_group_count": len(differing),
        "differing_execution_basis_ref_group_count": len(differing),
        "historical_helper_ref_comparison_status_ref": P7_R54_AHR_HISTORICAL_HELPER_REF_COMPARISON_STATUS_REF,
        "current_execution_basis_refreeze_completed_here": True,
        "current_refs_refreeze_does_not_rewrite_historical_helpers": True,
        "current_execution_basis_refreeze_does_not_rewrite_historical_helpers": True,
        "historical_helper_refs_reconcile_required_next": True,
        "current_refs_override_uses_thin_ahr_boundary_layer": True,
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
        "actual_rating_or_question_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR01_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR01_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR02_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_ahr01_current_execution_basis_refreeze_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFREEZE_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR01 current execution basis refreeze",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFREEZE_SCHEMA_VERSION,
        policy_section=P7_R54_AHR01_STEP_REF,
        operation_step_ref=P7_R54_AHR01_STEP_REF,
        source="P7-R54-AHR01 current execution basis refreeze",
    )
    _assert_current_execution_basis_refs(
        data, source="P7-R54-AHR01 current execution basis refreeze", actual_basis=True
    )
    if data.get("ahr00_schema_version") != P7_R54_AHR_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR01 AHR00 schema version changed")
    if data.get("ahr00_next_required_step") != P7_R54_AHR01_STEP_REF:
        raise ValueError("P7-R54-AHR01 must follow AHR00")
    if data.get("execution_basis_envelope_schema_version") != P7_R54_AHR_EXECUTION_BASIS_ENVELOPE_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR01 execution basis envelope schema changed")
    for key in (
        "ahr00_scope_boundary_confirmed",
        "ahr00_no_touch_boundary_confirmed",
        "current_execution_basis_refrozen",
        "operation_current_refs_match_current_execution_basis_260_83_256_169",
        "current_execution_basis_refs_match_received_snapshot_260_83_256_169",
        "current_execution_basis_refs_match_260_83_256_169_snapshot",
        "historical_helper_refs_separated",
        "historical_helper_refs_are_historical_here",
        "historical_helper_refs_are_structural_refs_only",
        "historical_helper_refs_can_be_used_for_helper_regression_only",
        "existing_helper_refs_can_be_used_for_helper_regression_only",
        "r52_refs_are_historical_here",
        "r54_bodyfree_handoff_refs_are_historical_here",
        "r55_refs_are_historical_here",
        "r54_op_refs_are_historical_here",
        "r54_ev_refs_are_historical_here",
        "r54_clr_refs_are_historical_here",
        "r54_clr_current_refs_are_historical_here",
        "current_execution_basis_refreeze_completed_here",
        "current_refs_refreeze_does_not_rewrite_historical_helpers",
        "current_execution_basis_refreeze_does_not_rewrite_historical_helpers",
        "historical_helper_refs_reconcile_required_next",
        "current_refs_override_uses_thin_ahr_boundary_layer",
        "existing_helper_constants_not_rewritten",
        "existing_helper_refs_preserved_as_received",
        "new_thin_boundary_helper_only",
        "body_full_generation_blocked_until_later_preflight",
        "body_full_generation_blocked_until_preflight",
        "human_review_completion_claim_blocked_here",
        "actual_review_completion_claim_blocked_here",
        "actual_human_review_completion_claim_blocked_here",
        "actual_rating_or_question_rows_claim_blocked_here",
        "disposal_receipt_claim_blocked_here",
        "r52_reintake_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR01 must keep {key}=True")
    for key in (
        "historical_helper_refs_can_be_used_for_actual_execution_basis",
        "historical_helper_refs_used_as_actual_execution_basis",
        "r54_clr_historical_refs_used_as_actual_execution_basis",
        "old_helper_refs_allowed_as_actual_execution_basis",
        "old_helper_refs_match_current_execution_basis_260_83_256_169",
        "r52_refs_used_as_actual_execution_basis",
        "r54_bodyfree_handoff_refs_used_as_actual_execution_basis",
        "r55_refs_used_as_actual_execution_basis",
        "r54_op_refs_used_as_actual_execution_basis",
        "r54_ev_refs_used_as_actual_execution_basis",
        "r54_clr_refs_used_as_actual_execution_basis",
        "r54_clr_current_refs_match_current_execution_basis_260_83_256_169",
        "existing_helper_constants_rewritten",
        "new_full_operation_helper_required",
        "new_full_operation_helper_required_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR01 must keep {key}=False")
    if data.get("current_execution_basis_source_mode") != P7_SOURCE_MODE:
        raise ValueError("P7-R54-AHR01 current execution basis source mode changed")
    if data.get("current_execution_basis_refreeze_status_ref") != P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFREEZE_STATUS_REF:
        raise ValueError("P7-R54-AHR01 refreeze status changed")
    if tuple(data.get("historical_helper_ref_groups") or ()) != P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS:
        raise ValueError("P7-R54-AHR01 historical helper groups changed")
    if data.get("historical_helper_ref_group_count") != len(P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS):
        raise ValueError("P7-R54-AHR01 historical helper group count changed")
    if safe_mapping(data.get("historical_helper_refs")) != P7_R54_AHR_HISTORICAL_HELPER_REFS:
        raise ValueError("P7-R54-AHR01 historical helper refs changed")
    match_map = safe_mapping(data.get("historical_helper_refs_match_current_execution_basis_260_83_256_169"))
    if set(match_map) != set(P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS) or any(match_map.values()):
        raise ValueError("P7-R54-AHR01 historical helper match map changed")
    differing = safe_mapping(data.get("historical_helper_differing_current_execution_basis_ref_keys"))
    differing_alias = safe_mapping(data.get("historical_helper_differing_execution_basis_ref_keys"))
    if differing_alias != differing:
        raise ValueError("P7-R54-AHR01 differing historical ref alias changed")
    if set(differing) != set(P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS):
        raise ValueError("P7-R54-AHR01 differing historical ref groups changed")
    for group_ref in P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS:
        if not differing.get(group_ref):
            raise ValueError(f"P7-R54-AHR01 must show historical refs differ for {group_ref}")
    if data.get("differing_current_execution_basis_ref_group_count") != len(P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS):
        raise ValueError("P7-R54-AHR01 differing historical ref group count changed")
    if data.get("differing_execution_basis_ref_group_count") != len(P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS):
        raise ValueError("P7-R54-AHR01 differing historical ref group alias count changed")
    if data.get("historical_helper_ref_comparison_status_ref") != P7_R54_AHR_HISTORICAL_HELPER_REF_COMPARISON_STATUS_REF:
        raise ValueError("P7-R54-AHR01 historical helper comparison status changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR01_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR01 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR01_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR01 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R54_AHR02_STEP_REF:
        raise ValueError("P7-R54-AHR01 next required step changed")
    return True

def _historical_helper_ref_rows() -> list[dict[str, Any]]:
    differing = _historical_diff_keys_by_group()
    return [
        {
            "group_ref": group_ref,
            "helper_role_ref": P7_R54_AHR_HISTORICAL_HELPER_ROLE_REFS[group_ref],
            "classification_ref": P7_R54_AHR_HISTORICAL_HELPER_CLASSIFICATION_REFS[group_ref],
            "ref_count": len(P7_R54_AHR_HISTORICAL_HELPER_REFS[group_ref]),
            "differing_current_execution_basis_ref_keys": list(differing[group_ref]),
            "matches_current_execution_basis_260_83_256_169": False,
            "used_as_actual_execution_basis": False,
            "helper_green_can_complete_actual_review": False,
            "rewritten_here": False,
            "body_free": True,
        }
        for group_ref in P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS
    ]


def build_p7_r54_ahr02_historical_helper_refs_reconcile(
    *,
    current_execution_basis_refreeze: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build R54-AHR-02 body-free historical helper refs reconcile material."""

    ahr01 = dict(current_execution_basis_refreeze or build_p7_r54_ahr01_current_execution_basis_refreeze())
    assert_p7_r54_ahr01_current_execution_basis_refreeze_contract(ahr01)
    differing = _historical_diff_keys_by_group()
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_HISTORICAL_HELPER_REFS_RECONCILE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_STEP,
        "scope": P7_R54_AHR_SCOPE,
        "policy_kind": P7_R54_AHR_POLICY_KIND,
        "policy_section": P7_R54_AHR02_STEP_REF,
        "operation_step_ref": P7_R54_AHR02_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr02_historical_helper_refs_reconcile_20260627",
        "review_session_id": _safe_review_session_id(review_session_id or ahr01.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ahr01_schema_version": ahr01["schema_version"],
        "ahr01_material_ref": ahr01["material_id"],
        "ahr01_next_required_step": ahr01["next_required_step"],
        "ahr01_current_execution_basis_refrozen": ahr01["current_execution_basis_refrozen"],
        "ahr01_current_execution_basis_refreeze_status_ref": ahr01["current_execution_basis_refreeze_status_ref"],
        "current_execution_basis_refs": dict(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "current_execution_basis_ref_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "current_execution_basis_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "current_execution_basis_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_refs": dict(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_ref_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "operation_current_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "required_current_execution_basis_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "required_current_execution_basis_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "all_required_current_execution_basis_refs_present": True,
        "actual_execution_basis_ref": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF,
        "actual_execution_basis_allowed": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_ALLOWED_REF,
        "actual_review_basis_ref": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_ALLOWED_REF,
        "current_execution_basis_refs_are_actual_execution_basis": True,
        "current_execution_basis_refs_used_as_actual_execution_basis": True,
        "operation_current_refs_are_actual_execution_basis": True,
        "operation_current_refs_used_as_actual_execution_basis": True,
        "operation_current_refs_match_current_execution_basis_260_83_256_169": True,
        "current_execution_basis_refs_match_received_snapshot_260_83_256_169": True,
        "current_execution_basis_refs_match_260_83_256_169_snapshot": True,
        "historical_helper_refs_reconcile_status_ref": P7_R54_AHR_HISTORICAL_HELPER_REFS_RECONCILE_STATUS_REF,
        "historical_helper_refs_reconciled": True,
        "historical_helper_ref_groups": list(P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS),
        "historical_helper_ref_group_count": len(P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS),
        "historical_helper_refs": {key: dict(value) for key, value in P7_R54_AHR_HISTORICAL_HELPER_REFS.items()},
        "historical_helper_ref_rows": _historical_helper_ref_rows(),
        "historical_helper_role_refs": dict(P7_R54_AHR_HISTORICAL_HELPER_ROLE_REFS),
        "historical_helper_classification_refs": dict(P7_R54_AHR_HISTORICAL_HELPER_CLASSIFICATION_REFS),
        "historical_helper_refs_match_current_execution_basis_260_83_256_169": {
            group_ref: False for group_ref in P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS
        },
        "historical_helper_differing_current_execution_basis_ref_keys": differing,
        "historical_helper_differing_current_execution_basis_ref_key_counts": {
            group_ref: len(keys) for group_ref, keys in differing.items()
        },
        "differing_current_execution_basis_ref_group_count": len(differing),
        "r52_refs_reconciled_as_actual_evidence_decision_gate": True,
        "r54_bodyfree_handoff_refs_reconciled_as_bodyfree_handoff_contract": True,
        "r55_refs_reconciled_as_evidence_missing_hold_contract": True,
        "r54_op_refs_reconciled_as_operation_structural_helper": True,
        "r54_ev_refs_reconciled_as_evidence_materialization_structural_helper": True,
        "r54_clr_refs_reconciled_as_current_snapshot_local_run_structural_helper": True,
        "historical_helper_refs_are_historical_here": True,
        "historical_helper_refs_are_structural_refs_only": True,
        "historical_helper_refs_are_contract_refs_only": True,
        "historical_helper_refs_can_be_used_for_helper_regression_only": True,
        "existing_helper_refs_can_be_used_for_helper_regression_only": True,
        "historical_helper_refs_can_be_used_for_actual_execution_basis": False,
        "historical_helper_refs_used_as_actual_execution_basis": False,
        "r54_clr_historical_refs_used_as_actual_execution_basis": False,
        "old_helper_refs_allowed_as_actual_execution_basis": False,
        "r54_clr_current_refs_are_historical_here": True,
        "r54_clr_current_refs_preserved_as_historical": True,
        "r54_clr_current_refs_not_rewritten": True,
        "r54_clr_current_refs_match_current_execution_basis_260_83_256_169": False,
        "historical_helper_green_claim_boundary_refs": list(P7_R54_AHR_PRIOR_HELPER_GREEN_CLAIM_BOUNDARY_REFS),
        "helper_green_not_actual_human_review_complete": True,
        "synthetic_contract_rows_not_actual_review_rows": True,
        "r52_handoff_ready_contract_not_actual_r52_reintake_execution": True,
        "reconcile_does_not_modify_helper_modules": True,
        "existing_helper_constants_not_rewritten": True,
        "existing_helper_constants_rewritten": False,
        "existing_helper_refs_preserved_as_received": True,
        "current_refs_override_uses_thin_ahr_boundary_layer": True,
        "new_thin_boundary_helper_only": True,
        "new_full_operation_helper_required_here": False,
        "body_full_generation_blocked_until_later_preflight": True,
        "body_full_generation_blocked_until_preflight": True,
        "human_review_completion_claim_blocked_here": True,
        "actual_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_rating_or_question_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR02_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR02_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR03_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_ahr02_historical_helper_refs_reconcile_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_HISTORICAL_HELPER_REFS_RECONCILE_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR02 historical helper refs reconcile",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_HISTORICAL_HELPER_REFS_RECONCILE_SCHEMA_VERSION,
        policy_section=P7_R54_AHR02_STEP_REF,
        operation_step_ref=P7_R54_AHR02_STEP_REF,
        source="P7-R54-AHR02 historical helper refs reconcile",
    )
    _assert_current_execution_basis_refs(data, source="P7-R54-AHR02 historical helper refs reconcile", actual_basis=True)
    if data.get("ahr01_schema_version") != P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFREEZE_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR02 AHR01 schema reference changed")
    if data.get("ahr01_next_required_step") != P7_R54_AHR02_STEP_REF:
        raise ValueError("P7-R54-AHR02 must follow AHR01")
    for key in (
        "ahr01_current_execution_basis_refrozen",
        "operation_current_refs_match_current_execution_basis_260_83_256_169",
        "current_execution_basis_refs_match_received_snapshot_260_83_256_169",
        "current_execution_basis_refs_match_260_83_256_169_snapshot",
        "historical_helper_refs_reconciled",
        "r52_refs_reconciled_as_actual_evidence_decision_gate",
        "r54_bodyfree_handoff_refs_reconciled_as_bodyfree_handoff_contract",
        "r55_refs_reconciled_as_evidence_missing_hold_contract",
        "r54_op_refs_reconciled_as_operation_structural_helper",
        "r54_ev_refs_reconciled_as_evidence_materialization_structural_helper",
        "r54_clr_refs_reconciled_as_current_snapshot_local_run_structural_helper",
        "historical_helper_refs_are_historical_here",
        "historical_helper_refs_are_structural_refs_only",
        "historical_helper_refs_are_contract_refs_only",
        "historical_helper_refs_can_be_used_for_helper_regression_only",
        "existing_helper_refs_can_be_used_for_helper_regression_only",
        "r54_clr_current_refs_are_historical_here",
        "r54_clr_current_refs_preserved_as_historical",
        "r54_clr_current_refs_not_rewritten",
        "helper_green_not_actual_human_review_complete",
        "synthetic_contract_rows_not_actual_review_rows",
        "r52_handoff_ready_contract_not_actual_r52_reintake_execution",
        "reconcile_does_not_modify_helper_modules",
        "existing_helper_constants_not_rewritten",
        "existing_helper_refs_preserved_as_received",
        "current_refs_override_uses_thin_ahr_boundary_layer",
        "new_thin_boundary_helper_only",
        "body_full_generation_blocked_until_later_preflight",
        "body_full_generation_blocked_until_preflight",
        "human_review_completion_claim_blocked_here",
        "actual_review_completion_claim_blocked_here",
        "actual_human_review_completion_claim_blocked_here",
        "actual_rating_or_question_rows_claim_blocked_here",
        "disposal_receipt_claim_blocked_here",
        "r52_reintake_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR02 must keep {key}=True")
    for key in (
        "historical_helper_refs_can_be_used_for_actual_execution_basis",
        "historical_helper_refs_used_as_actual_execution_basis",
        "r54_clr_historical_refs_used_as_actual_execution_basis",
        "old_helper_refs_allowed_as_actual_execution_basis",
        "r54_clr_current_refs_match_current_execution_basis_260_83_256_169",
        "existing_helper_constants_rewritten",
        "new_full_operation_helper_required_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR02 must keep {key}=False")
    if data.get("historical_helper_refs_reconcile_status_ref") != P7_R54_AHR_HISTORICAL_HELPER_REFS_RECONCILE_STATUS_REF:
        raise ValueError("P7-R54-AHR02 reconcile status changed")
    if tuple(data.get("historical_helper_ref_groups") or ()) != P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS:
        raise ValueError("P7-R54-AHR02 historical helper groups changed")
    if data.get("historical_helper_ref_group_count") != len(P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS):
        raise ValueError("P7-R54-AHR02 historical helper group count changed")
    if safe_mapping(data.get("historical_helper_refs")) != P7_R54_AHR_HISTORICAL_HELPER_REFS:
        raise ValueError("P7-R54-AHR02 historical helper refs changed")
    if safe_mapping(data.get("historical_helper_role_refs")) != P7_R54_AHR_HISTORICAL_HELPER_ROLE_REFS:
        raise ValueError("P7-R54-AHR02 historical helper role refs changed")
    if safe_mapping(data.get("historical_helper_classification_refs")) != P7_R54_AHR_HISTORICAL_HELPER_CLASSIFICATION_REFS:
        raise ValueError("P7-R54-AHR02 historical helper classification refs changed")
    if tuple(data.get("historical_helper_green_claim_boundary_refs") or ()) != P7_R54_AHR_PRIOR_HELPER_GREEN_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR02 helper green claim boundary changed")
    rows = data.get("historical_helper_ref_rows") or []
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)):
        raise ValueError("P7-R54-AHR02 historical helper rows must be a sequence")
    if len(rows) != len(P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS):
        raise ValueError("P7-R54-AHR02 historical helper row count changed")
    for row in rows:
        row_map = safe_mapping(row)
        group_ref = row_map.get("group_ref")
        if group_ref not in P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS:
            raise ValueError("P7-R54-AHR02 historical helper row group changed")
        if row_map.get("used_as_actual_execution_basis") is not False:
            raise ValueError("P7-R54-AHR02 helper row cannot be actual execution basis")
        if row_map.get("helper_green_can_complete_actual_review") is not False:
            raise ValueError("P7-R54-AHR02 helper row cannot complete actual review")
        if row_map.get("rewritten_here") is not False:
            raise ValueError("P7-R54-AHR02 helper row cannot rewrite historical refs")
    match_map = safe_mapping(data.get("historical_helper_refs_match_current_execution_basis_260_83_256_169"))
    if set(match_map) != set(P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS) or any(match_map.values()):
        raise ValueError("P7-R54-AHR02 historical helper match map changed")
    differing = safe_mapping(data.get("historical_helper_differing_current_execution_basis_ref_keys"))
    if set(differing) != set(P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS):
        raise ValueError("P7-R54-AHR02 differing groups changed")
    for group_ref in P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS:
        if not differing.get(group_ref):
            raise ValueError(f"P7-R54-AHR02 missing differing refs for {group_ref}")
    if data.get("differing_current_execution_basis_ref_group_count") != len(P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS):
        raise ValueError("P7-R54-AHR02 differing group count changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR02_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR02 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR02_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR02 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R54_AHR03_STEP_REF:
        raise ValueError("P7-R54-AHR02 next required step changed")
    return True


def build_p7_r54_ahr03_r55_hold_evidence_missing_intake(
    *,
    historical_helper_refs_reconcile: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build R54-AHR-03 body-free R55 hold / evidence missing intake material."""

    ahr02 = dict(historical_helper_refs_reconcile or build_p7_r54_ahr02_historical_helper_refs_reconcile())
    assert_p7_r54_ahr02_historical_helper_refs_reconcile_contract(ahr02)
    r55_gap = r55.build_p7_r55_actual_review_evidence_gap_assessment_bodyfree()
    r55.assert_p7_r55_actual_review_evidence_gap_assessment_bodyfree_contract(r55_gap)
    r55_decision = r55.build_p7_r55_r52_reintake_decision_materialization_bodyfree(
        actual_review_evidence_gap_assessment=r55_gap
    )
    r55.assert_p7_r55_r52_reintake_decision_materialization_bodyfree_contract(r55_decision)
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_R55_HOLD_EVIDENCE_MISSING_INTAKE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_STEP,
        "scope": P7_R54_AHR_SCOPE,
        "policy_kind": P7_R54_AHR_POLICY_KIND,
        "policy_section": P7_R54_AHR03_STEP_REF,
        "operation_step_ref": P7_R54_AHR03_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr03_r55_hold_evidence_missing_intake_20260627",
        "review_session_id": _safe_review_session_id(review_session_id or ahr02.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ahr02_schema_version": ahr02["schema_version"],
        "ahr02_material_ref": ahr02["material_id"],
        "ahr02_next_required_step": ahr02["next_required_step"],
        "ahr02_historical_helper_refs_reconciled": ahr02["historical_helper_refs_reconciled"],
        "current_execution_basis_refs": dict(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "current_execution_basis_ref_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "current_execution_basis_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "current_execution_basis_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_refs": dict(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_ref_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "operation_current_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "required_current_execution_basis_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "required_current_execution_basis_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "all_required_current_execution_basis_refs_present": True,
        "actual_execution_basis_ref": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF,
        "actual_execution_basis_allowed": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_ALLOWED_REF,
        "actual_review_basis_ref": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_ALLOWED_REF,
        "current_execution_basis_refs_are_actual_execution_basis": True,
        "current_execution_basis_refs_used_as_actual_execution_basis": True,
        "operation_current_refs_are_actual_execution_basis": True,
        "operation_current_refs_used_as_actual_execution_basis": True,
        "operation_current_refs_match_current_execution_basis_260_83_256_169": True,
        "current_execution_basis_refs_match_received_snapshot_260_83_256_169": True,
        "current_execution_basis_refs_match_260_83_256_169_snapshot": True,
        "r55_hold_intake_status_ref": P7_R54_AHR_R55_HOLD_EVIDENCE_MISSING_STATUS_REF,
        "r55_hold_intaken": True,
        "r55_actual_review_evidence_gap_assessment_schema_version": r55.P7_R55_ACTUAL_REVIEW_EVIDENCE_GAP_ASSESSMENT_SCHEMA_VERSION,
        "r55_actual_review_evidence_gap_assessment_material_ref": clean_identifier(
            r55_gap.get("material_id"), default="p7_r55_actual_review_evidence_gap_assessment", max_length=220
        ),
        "r55_r52_reintake_decision_materialization_schema_version": r55.P7_R55_R52_REINTAKE_DECISION_MATERIALIZATION_SCHEMA_VERSION,
        "r55_r52_reintake_decision_materialization_material_ref": clean_identifier(
            r55_decision.get("material_id"), default="p7_r55_r52_reintake_decision_materialization_current_default", max_length=220
        ),
        "r55_gap_assessment_intaken": True,
        "r55_decision_materialization_intaken": True,
        "r55_gap_status_ref": clean_identifier(r55_gap.get("gap_status_ref"), default=P7_R54_AHR_R55_GAP_STATUS_REF, max_length=180),
        "actual_review_evidence_gap_status_ref": clean_identifier(
            r55_decision.get("actual_review_evidence_gap_status_ref"), default=P7_R54_AHR_R55_GAP_STATUS_REF, max_length=180
        ),
        "actual_review_evidence_missing_confirmed": True,
        "r54_handoff_status_ref": clean_identifier(
            r55_decision.get("r54_handoff_status"), default=P7_R54_AHR_R54_R52_REINTAKE_HANDOFF_STATUS_BEFORE_RUN_REF, max_length=180
        ),
        "r54_review_operation_state_ref": clean_identifier(
            r55_decision.get("r54_review_operation_state_ref"), default=r55.P7_R55_R54_DEFAULT_REVIEW_OPERATION_STATE_REF, max_length=180
        ),
        "p5_decision_before_run": P7_R54_AHR_P5_DECISION_BEFORE_RUN_REF,
        "p5_decision_status_ref": clean_identifier(
            r55_decision.get("p5_decision_status_ref"), default=r55.P7_R55_P5_DECISION_STATUS_NOT_REVIEWED_REF, max_length=180
        ),
        "r52_reintake_status_before_run": P7_R54_AHR_R52_REINTAKE_STATUS_BEFORE_RUN_REF,
        "r55_decision_ref": clean_identifier(
            r55_decision.get("r55_decision_ref"), default=r55.P7_R55_DEFAULT_R52_REINTAKE_DECISION_REF, max_length=180
        ),
        "r52_existing_decision_equivalent": clean_identifier(
            r55_decision.get("r52_existing_decision_equivalent"), default=r55.P7_R55_DEFAULT_R52_EXISTING_DECISION_EQUIVALENT_REF, max_length=180
        ),
        "decision_status": clean_identifier(r55_decision.get("decision_status"), default=r55.P7_R55_DEFAULT_DECISION_STATUS_REF, max_length=60),
        "decision_reason_refs": list(r55.P7_R55_DEFAULT_DECISION_REASON_REFS),
        "decision_reason_ref_count": len(r55.P7_R55_DEFAULT_DECISION_REASON_REFS),
        "r55_next_required_step": r55.P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF,
        "required_case_count": P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "reviewed_case_count": 0,
        "sanitized_review_result_row_count": 0,
        "rating_row_count": 0,
        "question_observation_row_count": 0,
        "missing_evidence_refs": list(P7_R54_AHR_R55_MISSING_EVIDENCE_REFS),
        "missing_evidence_ref_count": len(P7_R54_AHR_R55_MISSING_EVIDENCE_REFS),
        "r55_missing_evidence_refs_match_default": True,
        "actual_rating_rows_missing": True,
        "actual_question_observation_rows_missing": True,
        "actual_disposal_receipt_missing": True,
        "actual_r52_reintake_blocked_before_run": True,
        "r52_handoff_ready_before_actual_review": False,
        "r52_reintake_ready_before_actual_review": False,
        "p5_confirmed_candidate_before_actual_review": False,
        "p8_material_candidate_before_actual_review": False,
        "next_required_step_is_local_only_preflight": True,
        "body_full_generation_blocked_until_later_preflight": True,
        "body_full_generation_blocked_until_preflight": True,
        "human_review_completion_claim_blocked_here": True,
        "actual_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_rating_or_question_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR03_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR03_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR04_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_ahr03_r55_hold_evidence_missing_intake_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_R55_HOLD_EVIDENCE_MISSING_INTAKE_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR03 R55 hold evidence missing intake",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_R55_HOLD_EVIDENCE_MISSING_INTAKE_SCHEMA_VERSION,
        policy_section=P7_R54_AHR03_STEP_REF,
        operation_step_ref=P7_R54_AHR03_STEP_REF,
        source="P7-R54-AHR03 R55 hold evidence missing intake",
    )
    _assert_current_execution_basis_refs(data, source="P7-R54-AHR03 R55 hold evidence missing intake", actual_basis=True)
    if data.get("ahr02_schema_version") != P7_R54_AHR_HISTORICAL_HELPER_REFS_RECONCILE_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR03 AHR02 schema reference changed")
    if data.get("ahr02_next_required_step") != P7_R54_AHR03_STEP_REF:
        raise ValueError("P7-R54-AHR03 must follow AHR02")
    for key in (
        "ahr02_historical_helper_refs_reconciled",
        "operation_current_refs_match_current_execution_basis_260_83_256_169",
        "current_execution_basis_refs_match_received_snapshot_260_83_256_169",
        "current_execution_basis_refs_match_260_83_256_169_snapshot",
        "r55_hold_intaken",
        "r55_gap_assessment_intaken",
        "r55_decision_materialization_intaken",
        "actual_review_evidence_missing_confirmed",
        "r55_missing_evidence_refs_match_default",
        "actual_rating_rows_missing",
        "actual_question_observation_rows_missing",
        "actual_disposal_receipt_missing",
        "actual_r52_reintake_blocked_before_run",
        "next_required_step_is_local_only_preflight",
        "body_full_generation_blocked_until_later_preflight",
        "body_full_generation_blocked_until_preflight",
        "human_review_completion_claim_blocked_here",
        "actual_review_completion_claim_blocked_here",
        "actual_human_review_completion_claim_blocked_here",
        "actual_rating_or_question_rows_claim_blocked_here",
        "disposal_receipt_claim_blocked_here",
        "r52_reintake_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR03 must keep {key}=True")
    for key in (
        "r52_handoff_ready_before_actual_review",
        "r52_reintake_ready_before_actual_review",
        "p5_confirmed_candidate_before_actual_review",
        "p8_material_candidate_before_actual_review",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR03 must keep {key}=False")
    if data.get("r55_hold_intake_status_ref") != P7_R54_AHR_R55_HOLD_EVIDENCE_MISSING_STATUS_REF:
        raise ValueError("P7-R54-AHR03 R55 hold status changed")
    if data.get("r55_gap_status_ref") != P7_R54_AHR_R55_GAP_STATUS_REF:
        raise ValueError("P7-R54-AHR03 R55 gap status changed")
    if data.get("actual_review_evidence_gap_status_ref") != P7_R54_AHR_R55_GAP_STATUS_REF:
        raise ValueError("P7-R54-AHR03 evidence gap status changed")
    if data.get("r54_handoff_status_ref") != P7_R54_AHR_R54_R52_REINTAKE_HANDOFF_STATUS_BEFORE_RUN_REF:
        raise ValueError("P7-R54-AHR03 R54 handoff status changed")
    if data.get("r54_review_operation_state_ref") != r55.P7_R55_R54_DEFAULT_REVIEW_OPERATION_STATE_REF:
        raise ValueError("P7-R54-AHR03 review operation state changed")
    if data.get("p5_decision_before_run") != P7_R54_AHR_P5_DECISION_BEFORE_RUN_REF:
        raise ValueError("P7-R54-AHR03 P5 decision before run changed")
    if data.get("p5_decision_status_ref") != r55.P7_R55_P5_DECISION_STATUS_NOT_REVIEWED_REF:
        raise ValueError("P7-R54-AHR03 P5 decision status changed")
    if data.get("r52_reintake_status_before_run") != P7_R54_AHR_R52_REINTAKE_STATUS_BEFORE_RUN_REF:
        raise ValueError("P7-R54-AHR03 R52 status before run changed")
    if data.get("r55_decision_ref") != r55.P7_R55_DEFAULT_R52_REINTAKE_DECISION_REF:
        raise ValueError("P7-R54-AHR03 R55 decision ref changed")
    if data.get("r52_existing_decision_equivalent") != r55.P7_R55_DEFAULT_R52_EXISTING_DECISION_EQUIVALENT_REF:
        raise ValueError("P7-R54-AHR03 R52 equivalent decision changed")
    if data.get("decision_status") != r55.P7_R55_DEFAULT_DECISION_STATUS_REF:
        raise ValueError("P7-R54-AHR03 decision status changed")
    if tuple(data.get("decision_reason_refs") or ()) != r55.P7_R55_DEFAULT_DECISION_REASON_REFS:
        raise ValueError("P7-R54-AHR03 decision reason refs changed")
    if data.get("decision_reason_ref_count") != len(r55.P7_R55_DEFAULT_DECISION_REASON_REFS):
        raise ValueError("P7-R54-AHR03 decision reason count changed")
    if data.get("r55_next_required_step") != r55.P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF:
        raise ValueError("P7-R54-AHR03 R55 next required step changed")
    if data.get("required_case_count") != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-AHR03 required case count changed")
    for count_key in (
        "reviewed_case_count",
        "sanitized_review_result_row_count",
        "rating_row_count",
        "question_observation_row_count",
    ):
        if data.get(count_key) != 0:
            raise ValueError(f"P7-R54-AHR03 must keep {count_key}=0 before actual review")
    if tuple(data.get("missing_evidence_refs") or ()) != P7_R54_AHR_R55_MISSING_EVIDENCE_REFS:
        raise ValueError("P7-R54-AHR03 missing evidence refs changed")
    if data.get("missing_evidence_ref_count") != len(P7_R54_AHR_R55_MISSING_EVIDENCE_REFS):
        raise ValueError("P7-R54-AHR03 missing evidence count changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR03_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR03 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR03_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR03 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R54_AHR04_STEP_REF:
        raise ValueError("P7-R54-AHR03 next required step changed")
    return True

def _current_execution_basis_material_fields(*, actual_basis: bool = True) -> dict[str, Any]:
    expected_count = len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS)
    return {
        "current_execution_basis_refs": dict(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "current_execution_basis_ref_count": expected_count,
        "current_execution_basis_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "current_execution_basis_ref_key_count": expected_count,
        "operation_current_refs": dict(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_ref_count": expected_count,
        "operation_current_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "operation_current_ref_key_count": expected_count,
        "required_current_execution_basis_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "required_current_execution_basis_ref_key_count": expected_count,
        "all_required_current_execution_basis_refs_present": True,
        "actual_execution_basis_ref": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF,
        "actual_execution_basis_allowed": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_ALLOWED_REF,
        "actual_review_basis_ref": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_ALLOWED_REF,
        "current_execution_basis_refs_are_actual_execution_basis": actual_basis,
        "current_execution_basis_refs_used_as_actual_execution_basis": actual_basis,
        "operation_current_refs_are_actual_execution_basis": actual_basis,
        "operation_current_refs_used_as_actual_execution_basis": actual_basis,
        "operation_current_refs_match_current_execution_basis_260_83_256_169": True,
        "current_execution_basis_refs_match_received_snapshot_260_83_256_169": True,
        "current_execution_basis_refs_match_260_83_256_169_snapshot": True,
    }


def _ahr04_preflight_status_and_blockers(
    *,
    local_only: bool,
    must_not_export: bool,
    disposal_required: bool,
    local_only_root_available: bool,
    explicit_allow_token_present: bool,
    review_session_present: bool,
    current_execution_basis_refreeze_ready: bool,
    historical_helper_refs_reconciled_before_preflight: bool,
    r55_hold_intaken_before_preflight: bool,
    manifest_source_available: bool,
    export_denylist_ready: bool,
    purge_plan_ready: bool,
    body_full_artifact_public_export_allowed: bool,
    terminal_output_body_allowed: bool,
    api_db_rn_runtime_touch_allowed: bool,
) -> tuple[str, list[str], list[str]]:
    blockers: list[str] = []
    if not local_only:
        blockers.append("local_only_not_confirmed")
    if not must_not_export:
        blockers.append("must_not_export_not_confirmed")
    if not disposal_required:
        blockers.append("disposal_required_not_confirmed")
    if not local_only_root_available:
        blockers.append("local_only_root_missing")
    if not explicit_allow_token_present:
        blockers.append("explicit_local_only_allow_missing")
    if not review_session_present:
        blockers.append("review_session_missing")
    if not current_execution_basis_refreeze_ready:
        blockers.append("current_execution_basis_refreeze_missing")
    if not historical_helper_refs_reconciled_before_preflight:
        blockers.append("historical_helper_refs_not_reconciled")
    if not r55_hold_intaken_before_preflight:
        blockers.append("r55_hold_not_intaken")
    if not manifest_source_available:
        blockers.append("manifest_source_missing")
    if not export_denylist_ready:
        blockers.append("export_denylist_missing")
    if not purge_plan_ready:
        blockers.append("purge_plan_missing")
    if body_full_artifact_public_export_allowed:
        blockers.append("body_full_artifact_public_export_allowed")
    if terminal_output_body_allowed:
        blockers.append("terminal_output_body_allowed")
    if api_db_rn_runtime_touch_allowed:
        blockers.append("api_db_rn_runtime_touch_allowed")
    blockers = dedupe_identifiers(blockers, limit=40, max_length=180)
    if blockers:
        return P7_R54_AHR04_PREFLIGHT_BLOCKED_STATUS_REF, blockers, blockers
    return P7_R54_AHR04_PREFLIGHT_READY_STATUS_REF, [P7_R54_AHR04_READY_REASON_REF], []


def _ahr05_subscription_tier_ref(family: str) -> str:
    if family == "free_tier_history_present_not_allowed":
        return "free_tier_history_present_not_allowed_boundary"
    if family == "low_information_history_not_eligible":
        return "tier_hidden_current_only_boundary"
    return "paid_owned_history_context_ref"


def _ahr05_history_evidence_policy_ref(family: str) -> str:
    if family == "free_tier_history_present_not_allowed":
        return "owned_history_present_but_not_allowed_by_tier_boundary"
    if family == "low_information_history_not_eligible":
        return "history_not_eligible_current_only_boundary"
    return "bounded_owned_history_local_only"


def _ahr05_default_case_manifest_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = 1
    for family, count, case_role in r54op.P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION:
        for _ in range(count):
            row = {
                "case_index": index,
                "case_ref_id": f"ahr_case_ref_{index:03d}",
                "blind_case_id": f"ahr_blind_case_{index:03d}",
                "packet_ref_id": f"ahr_packet_ref_{index:03d}",
                "family": family,
                "case_role": case_role,
                "subscription_tier_ref": _ahr05_subscription_tier_ref(family),
                "history_evidence_policy_ref": _ahr05_history_evidence_policy_ref(family),
                "review_axis_profile_ref": P7_R54_AHR05_REVIEW_AXIS_PROFILE_REF,
                "reviewer_facing_family_exposed": False,
                "reviewer_facing_tier_exposed": False,
                "requires_history_line_review": family not in P7_R54_AHR05_CURRENT_ONLY_BOUNDARY_FAMILY_REFS,
                "current_only_boundary_case": family in P7_R54_AHR05_CURRENT_ONLY_BOUNDARY_FAMILY_REFS,
                "body_full_packet_materialized_here": False,
                "local_reviewer_payload_materialized_here": False,
                "body_free": True,
            }
            rows.append(row)
            index += 1
    return rows


def _count_by(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = clean_identifier(row.get(key), max_length=180)
        counts[value] = counts.get(value, 0) + 1
    return counts


def _unique_non_empty(values: Sequence[str], *, required_count: int) -> bool:
    return len(values) == required_count and all(values) and len(set(values)) == required_count


def _assert_ahr05_case_manifest_row(row: Mapping[str, Any], *, expected_index: int) -> None:
    _assert_required_fields(
        row,
        required=P7_R54_AHR05_CASE_MANIFEST_ROW_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR05 case manifest row",
    )
    if row.get("case_index") != expected_index:
        raise ValueError("P7-R54-AHR05 case manifest row index changed")
    family = clean_identifier(row.get("family"), max_length=180)
    if family not in P7_R54_AHR05_CASE_DISTRIBUTION:
        raise ValueError("P7-R54-AHR05 case manifest row family changed")
    if row.get("case_role") != P7_R54_AHR05_CASE_ROLE_BY_FAMILY[family]:
        raise ValueError("P7-R54-AHR05 case manifest row role changed")
    if clean_identifier(row.get("case_ref_id"), max_length=180) == clean_identifier(row.get("blind_case_id"), max_length=180):
        raise ValueError("P7-R54-AHR05 case_ref_id and blind_case_id must be separated")
    if clean_identifier(row.get("packet_ref_id"), max_length=180) in {
        clean_identifier(row.get("case_ref_id"), max_length=180),
        clean_identifier(row.get("blind_case_id"), max_length=180),
    }:
        raise ValueError("P7-R54-AHR05 packet_ref_id must be separated")
    expected_boundary = family in P7_R54_AHR05_CURRENT_ONLY_BOUNDARY_FAMILY_REFS
    if row.get("current_only_boundary_case") is not expected_boundary:
        raise ValueError("P7-R54-AHR05 current-only boundary flag changed")
    if row.get("requires_history_line_review") is not (not expected_boundary):
        raise ValueError("P7-R54-AHR05 history-line review flag changed")
    for key in (
        "reviewer_facing_family_exposed",
        "reviewer_facing_tier_exposed",
        "body_full_packet_materialized_here",
        "local_reviewer_payload_materialized_here",
    ):
        if row.get(key) is not False:
            raise ValueError(f"P7-R54-AHR05 case manifest row must keep {key}=False")
    if row.get("body_free") is not True:
        raise ValueError("P7-R54-AHR05 case manifest row must remain body-free")
    if _contains_forbidden_ahr_key(row):
        raise ValueError("P7-R54-AHR05 case manifest row contains forbidden key")
    assert_p7_no_body_payload_or_contract_mutation(row, source="P7-R54-AHR05 case manifest row")


def build_p7_r54_ahr04_local_only_preflight(
    *,
    r55_hold_evidence_missing_intake: Mapping[str, Any] | None = None,
    review_session_id: Any | None = None,
    explicit_allow_token_ref: Any = P7_R54_AHR04_EXPLICIT_LOCAL_ONLY_ALLOW_REF,
    local_only_root_ref: Any = P7_R54_AHR04_LOCAL_ONLY_ROOT_AVAILABLE_REF,
    manifest_source_ref: Any = P7_R54_AHR04_MANIFEST_SOURCE_AVAILABLE_REF,
    export_denylist_ref: Any = P7_R54_AHR04_EXPORT_DENYLIST_READY_REF,
    purge_plan_ref: Any = P7_R54_AHR04_PURGE_PLAN_READY_REF,
    local_only: bool = True,
    must_not_export: bool = True,
    disposal_required: bool = True,
    body_full_artifact_public_export_allowed: bool = False,
    terminal_output_body_allowed: bool = False,
    api_db_rn_runtime_touch_allowed: bool = False,
) -> dict[str, Any]:
    """Build R54-AHR-04 body-free local-only preflight material."""

    prior = dict(r55_hold_evidence_missing_intake or build_p7_r54_ahr03_r55_hold_evidence_missing_intake())
    assert_p7_r54_ahr03_r55_hold_evidence_missing_intake_contract(prior)
    session_id = _safe_review_session_id(review_session_id or prior.get("review_session_id"))
    explicit_ref = clean_identifier(explicit_allow_token_ref, default="missing_explicit_allow_token_ref", max_length=220)
    root_ref = clean_identifier(local_only_root_ref, default="missing_local_only_root_ref", max_length=220)
    manifest_ref = clean_identifier(manifest_source_ref, default="missing_manifest_source_ref", max_length=220)
    export_ref = clean_identifier(export_denylist_ref, default="missing_export_denylist_ref", max_length=220)
    purge_ref = clean_identifier(purge_plan_ref, default="missing_purge_plan_ref", max_length=220)
    explicit_present = explicit_ref == P7_R54_AHR04_EXPLICIT_LOCAL_ONLY_ALLOW_REF
    local_root_available = root_ref == P7_R54_AHR04_LOCAL_ONLY_ROOT_AVAILABLE_REF
    review_session_present = bool(session_id)
    current_refreeze_ready = prior.get("current_execution_basis_refs_are_actual_execution_basis") is True
    historical_reconciled = prior.get("ahr02_historical_helper_refs_reconciled") is True
    r55_intaken = prior.get("r55_hold_intaken") is True
    manifest_available = manifest_ref == P7_R54_AHR04_MANIFEST_SOURCE_AVAILABLE_REF
    export_ready = export_ref == P7_R54_AHR04_EXPORT_DENYLIST_READY_REF
    purge_ready = purge_ref == P7_R54_AHR04_PURGE_PLAN_READY_REF
    status, reasons, blockers = _ahr04_preflight_status_and_blockers(
        local_only=local_only is True,
        must_not_export=must_not_export is True,
        disposal_required=disposal_required is True,
        local_only_root_available=local_root_available,
        explicit_allow_token_present=explicit_present,
        review_session_present=review_session_present,
        current_execution_basis_refreeze_ready=current_refreeze_ready,
        historical_helper_refs_reconciled_before_preflight=historical_reconciled,
        r55_hold_intaken_before_preflight=r55_intaken,
        manifest_source_available=manifest_available,
        export_denylist_ready=export_ready,
        purge_plan_ready=purge_ready,
        body_full_artifact_public_export_allowed=body_full_artifact_public_export_allowed is True,
        terminal_output_body_allowed=terminal_output_body_allowed is True,
        api_db_rn_runtime_touch_allowed=api_db_rn_runtime_touch_allowed is True,
    )
    ready = status == P7_R54_AHR04_PREFLIGHT_READY_STATUS_REF
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_STEP,
        "scope": P7_R54_AHR_SCOPE,
        "policy_kind": P7_R54_AHR_POLICY_KIND,
        "policy_section": P7_R54_AHR04_STEP_REF,
        "operation_step_ref": P7_R54_AHR04_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr04_local_only_preflight_20260627",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ahr03_schema_version": prior["schema_version"],
        "ahr03_material_ref": prior["material_id"],
        "ahr03_next_required_step": prior["next_required_step"],
        "ahr03_r55_gap_status_ref": prior["r55_gap_status_ref"],
        "ahr03_actual_review_evidence_missing_confirmed": prior["actual_review_evidence_missing_confirmed"],
        "ahr03_r52_reintake_status_before_run": prior["r52_reintake_status_before_run"],
        **_current_execution_basis_material_fields(actual_basis=True),
        "local_only": local_only is True,
        "must_not_export": must_not_export is True,
        "disposal_required": disposal_required is True,
        "local_only_root_ref": root_ref,
        "local_only_root_available": local_root_available,
        "local_only_root_is_ref_only": True,
        "explicit_allow_token_ref": explicit_ref,
        "explicit_allow_token_present": explicit_present,
        "review_session_present": review_session_present,
        "review_session_present_ref": P7_R54_AHR04_REVIEW_SESSION_PRESENT_REF,
        "current_execution_basis_refreeze_ready": current_refreeze_ready,
        "historical_helper_refs_reconciled_before_preflight": historical_reconciled,
        "r55_hold_intaken_before_preflight": r55_intaken,
        "manifest_source_ref": manifest_ref,
        "manifest_source_available": manifest_available,
        "export_denylist_ref": export_ref,
        "export_denylist_ready": export_ready,
        "export_denylist_refs": list(P7_R54_AHR04_EXPORT_DENYLIST_REFS),
        "export_denylist_ref_count": len(P7_R54_AHR04_EXPORT_DENYLIST_REFS),
        "forbidden_output_refs": list(P7_R54_AHR04_FORBIDDEN_OUTPUT_REFS),
        "forbidden_output_ref_count": len(P7_R54_AHR04_FORBIDDEN_OUTPUT_REFS),
        "purge_plan_ref": purge_ref,
        "purge_plan_ready": purge_ready,
        "body_full_artifact_public_export_allowed": body_full_artifact_public_export_allowed is True,
        "terminal_output_body_allowed": terminal_output_body_allowed is True,
        "api_db_rn_runtime_touch_allowed": api_db_rn_runtime_touch_allowed is True,
        "api_db_rn_runtime_no_touch": api_db_rn_runtime_touch_allowed is False,
        "preflight_status": status,
        "preflight_reason_refs": reasons,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "body_full_packet_generation_allowed_before_preflight": False,
        "body_full_packet_generation_allowed_by_preflight": ready,
        "body_full_packet_generation_request_allowed_next": False,
        "body_full_generation_blocked_until_manifest_freeze": True,
        "actual_review_execution_blocked_until_packet_and_manifest_ready": True,
        "human_review_completion_claim_blocked_here": True,
        "actual_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_rating_or_question_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR04_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR04_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR05_STEP_REF if ready else P7_R54_AHR04_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_ahr04_local_only_preflight_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_LOCAL_ONLY_PREFLIGHT_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR04 local-only preflight",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION,
        policy_section=P7_R54_AHR04_STEP_REF,
        operation_step_ref=P7_R54_AHR04_STEP_REF,
        source="P7-R54-AHR04 local-only preflight",
    )
    _assert_current_execution_basis_refs(data, source="P7-R54-AHR04 local-only preflight", actual_basis=True)
    if data.get("ahr03_schema_version") != P7_R54_AHR_R55_HOLD_EVIDENCE_MISSING_INTAKE_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR04 must follow AHR03")
    if data.get("ahr03_next_required_step") != P7_R54_AHR04_STEP_REF:
        raise ValueError("P7-R54-AHR04 AHR03 next step changed")
    if data.get("ahr03_r55_gap_status_ref") != P7_R54_AHR_R55_GAP_STATUS_REF:
        raise ValueError("P7-R54-AHR04 must preserve R55 evidence-missing gap")
    if data.get("ahr03_actual_review_evidence_missing_confirmed") is not True:
        raise ValueError("P7-R54-AHR04 must preserve actual review evidence missing")
    if data.get("ahr03_r52_reintake_status_before_run") != P7_R54_AHR_R52_REINTAKE_STATUS_BEFORE_RUN_REF:
        raise ValueError("P7-R54-AHR04 must preserve R52 pre-run block")
    if data.get("preflight_status") not in P7_R54_AHR04_ALLOWED_PREFLIGHT_STATUS_REFS:
        raise ValueError("P7-R54-AHR04 preflight status changed")
    if tuple(data.get("export_denylist_refs") or ()) != P7_R54_AHR04_EXPORT_DENYLIST_REFS:
        raise ValueError("P7-R54-AHR04 export denylist refs changed")
    if data.get("export_denylist_ref_count") != len(P7_R54_AHR04_EXPORT_DENYLIST_REFS):
        raise ValueError("P7-R54-AHR04 export denylist count changed")
    if tuple(data.get("forbidden_output_refs") or ()) != P7_R54_AHR04_FORBIDDEN_OUTPUT_REFS:
        raise ValueError("P7-R54-AHR04 forbidden output refs changed")
    if data.get("forbidden_output_ref_count") != len(P7_R54_AHR04_FORBIDDEN_OUTPUT_REFS):
        raise ValueError("P7-R54-AHR04 forbidden output count changed")
    for key in (
        "local_only",
        "must_not_export",
        "disposal_required",
        "local_only_root_is_ref_only",
        "review_session_present",
        "current_execution_basis_refreeze_ready",
        "historical_helper_refs_reconciled_before_preflight",
        "r55_hold_intaken_before_preflight",
        "body_full_generation_blocked_until_manifest_freeze",
        "actual_review_execution_blocked_until_packet_and_manifest_ready",
        "human_review_completion_claim_blocked_here",
        "actual_review_completion_claim_blocked_here",
        "actual_human_review_completion_claim_blocked_here",
        "actual_rating_or_question_rows_claim_blocked_here",
        "disposal_receipt_claim_blocked_here",
        "r52_reintake_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR04 must keep {key}=True")
    for key in (
        "body_full_artifact_public_export_allowed",
        "terminal_output_body_allowed",
        "api_db_rn_runtime_touch_allowed",
        "body_full_packet_generation_allowed_before_preflight",
        "body_full_packet_generation_request_allowed_next",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR04 must keep {key}=False")
    if data.get("api_db_rn_runtime_no_touch") is not True:
        raise ValueError("P7-R54-AHR04 must keep API/DB/RN/runtime no-touch")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("P7-R54-AHR04 open blockers must match blockers")
    ready = data.get("preflight_status") == P7_R54_AHR04_PREFLIGHT_READY_STATUS_REF
    if ready:
        for key in (
            "local_only_root_available",
            "explicit_allow_token_present",
            "manifest_source_available",
            "export_denylist_ready",
            "purge_plan_ready",
            "body_full_packet_generation_allowed_by_preflight",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR04 ready preflight must keep {key}=True")
        if blockers:
            raise ValueError("P7-R54-AHR04 ready preflight must not carry blockers")
        if data.get("preflight_reason_refs") != [P7_R54_AHR04_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR04 ready reason changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR04_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR04 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR04_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR04 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR05_STEP_REF:
            raise ValueError("P7-R54-AHR04 ready next step changed")
    else:
        if data.get("body_full_packet_generation_allowed_by_preflight") is not False:
            raise ValueError("P7-R54-AHR04 blocked preflight must not allow body-full generation")
        if not blockers:
            raise ValueError("P7-R54-AHR04 blocked preflight must carry blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR04_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR04 blocked implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR04_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR04 blocked not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR04_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR04 blocked next step changed")
    return True


def build_p7_r54_ahr05_24_case_manifest_freeze(
    *,
    local_only_preflight: Mapping[str, Any] | None = None,
    case_rows: Sequence[Mapping[str, Any]] | None = None,
    review_session_id: Any | None = None,
) -> dict[str, Any]:
    """Build R54-AHR-05 body-free 24-case manifest freeze material."""

    preflight = dict(local_only_preflight or build_p7_r54_ahr04_local_only_preflight())
    assert_p7_r54_ahr04_local_only_preflight_contract(preflight)
    preflight_ready = preflight.get("preflight_status") == P7_R54_AHR04_PREFLIGHT_READY_STATUS_REF
    required_count = P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
    source_rows = [dict(row) for row in (case_rows if case_rows is not None else _ahr05_default_case_manifest_rows())]
    case_refs = [clean_identifier(row.get("case_ref_id"), max_length=180) for row in source_rows]
    blind_ids = [clean_identifier(row.get("blind_case_id"), max_length=180) for row in source_rows]
    packet_refs = [clean_identifier(row.get("packet_ref_id"), max_length=180) for row in source_rows]
    family_counts = _count_by(source_rows, "family")
    case_role_counts = _count_by(source_rows, "case_role")
    tier_counts = _count_by(source_rows, "subscription_tier_ref")
    history_policy_counts = _count_by(source_rows, "history_evidence_policy_ref")
    distribution_matches = family_counts == P7_R54_AHR05_CASE_DISTRIBUTION
    separated_case_blind = set(case_refs).isdisjoint(set(blind_ids))
    separated_blind_packet = set(blind_ids).isdisjoint(set(packet_refs))
    separated_case_packet = set(case_refs).isdisjoint(set(packet_refs))
    case_refs_unique = _unique_non_empty(case_refs, required_count=required_count)
    blind_ids_unique = _unique_non_empty(blind_ids, required_count=required_count)
    packet_refs_unique = _unique_non_empty(packet_refs, required_count=required_count)
    manifest_ready = bool(
        preflight_ready
        and len(source_rows) == required_count
        and distribution_matches
        and case_refs_unique
        and blind_ids_unique
        and packet_refs_unique
        and separated_case_blind
        and separated_blind_packet
        and separated_case_packet
    )
    blockers = [] if manifest_ready else dedupe_identifiers(
        [
            *(preflight.get("execution_blocker_ids") or []),
            *([] if preflight_ready else ["local_only_preflight_not_ready_for_24_case_manifest_freeze"]),
            *([] if len(source_rows) == required_count else ["case_count_not_24"]),
            *([] if distribution_matches else ["case_distribution_mismatch"]),
            *([] if case_refs_unique else ["case_ref_ids_not_unique_or_missing"]),
            *([] if blind_ids_unique else ["blind_case_ids_not_unique_or_missing"]),
            *([] if packet_refs_unique else ["packet_ref_ids_not_unique_or_missing"]),
            *([] if separated_case_blind else ["blind_case_id_case_ref_not_separated"]),
            *([] if separated_blind_packet else ["blind_case_id_packet_ref_not_separated"]),
            *([] if separated_case_packet else ["case_ref_id_packet_ref_not_separated"]),
        ],
        limit=40,
        max_length=180,
    )
    reasons = [P7_R54_AHR05_READY_REASON_REF] if manifest_ready else blockers
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_STEP,
        "scope": P7_R54_AHR_SCOPE,
        "policy_kind": P7_R54_AHR_POLICY_KIND,
        "policy_section": P7_R54_AHR05_STEP_REF,
        "operation_step_ref": P7_R54_AHR05_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr05_24_case_manifest_freeze_20260627",
        "review_session_id": _safe_review_session_id(review_session_id or preflight.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ahr04_schema_version": preflight["schema_version"],
        "ahr04_material_ref": preflight["material_id"],
        "ahr04_next_required_step": preflight["next_required_step"],
        "ahr04_preflight_status": preflight["preflight_status"],
        "ahr04_body_full_packet_generation_allowed_by_preflight": preflight[
            "body_full_packet_generation_allowed_by_preflight"
        ],
        "local_only_preflight_ready": preflight_ready,
        **_current_execution_basis_material_fields(actual_basis=True),
        "manifest_source_kind_ref": P7_R54_AHR05_MANIFEST_SOURCE_KIND_REF,
        "r48_case_matrix_schema_version": r54op.P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION,
        "r48_case_matrix_material_ref": "p7_r48_p5_first_formal_review_case_matrix_bodyfree_source",
        "r48_case_matrix_case_count": len(source_rows),
        "required_case_count": required_count,
        "case_distribution": dict(P7_R54_AHR05_CASE_DISTRIBUTION),
        "case_distribution_total_count": sum(P7_R54_AHR05_CASE_DISTRIBUTION.values()),
        "case_distribution_matches_design": distribution_matches if manifest_ready else False,
        "manifest_status": P7_R54_AHR05_MANIFEST_READY_STATUS_REF if manifest_ready else P7_R54_AHR05_MANIFEST_BLOCKED_STATUS_REF,
        "manifest_reason_refs": reasons,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "case_rows": source_rows if manifest_ready else [],
        "case_row_count": len(source_rows) if manifest_ready else 0,
        "case_rows_bodyfree_only": manifest_ready,
        "case_ref_ids": case_refs if manifest_ready else [],
        "case_ref_id_count": len(case_refs) if manifest_ready else 0,
        "case_ref_ids_unique": case_refs_unique if manifest_ready else False,
        "blind_case_ids": blind_ids if manifest_ready else [],
        "blind_case_id_count": len(blind_ids) if manifest_ready else 0,
        "blind_case_ids_unique": blind_ids_unique if manifest_ready else False,
        "packet_ref_ids": packet_refs if manifest_ready else [],
        "packet_ref_id_count": len(packet_refs) if manifest_ready else 0,
        "packet_ref_ids_unique": packet_refs_unique if manifest_ready else False,
        "blind_case_id_case_ref_separated": separated_case_blind if manifest_ready else False,
        "blind_case_id_packet_ref_separated": separated_blind_packet if manifest_ready else False,
        "case_ref_id_packet_ref_separated": separated_case_packet if manifest_ready else False,
        "family_case_counts": family_counts if manifest_ready else {},
        "case_role_counts": case_role_counts if manifest_ready else {},
        "subscription_tier_ref_counts": tier_counts if manifest_ready else {},
        "history_evidence_policy_ref_counts": history_policy_counts if manifest_ready else {},
        "review_axis_profile_ref": P7_R54_AHR05_REVIEW_AXIS_PROFILE_REF,
        "rating_axis_refs": list(P7_R54_AHR05_RATING_AXIS_REFS),
        "rating_axis_count": len(P7_R54_AHR05_RATING_AXIS_REFS),
        "rating_axis_target_thresholds": dict(P7_R54_AHR05_RATING_AXIS_TARGET_THRESHOLDS),
        "requires_history_line_review_count": sum(
            1 for row in source_rows if row.get("requires_history_line_review") is True
        ) if manifest_ready else 0,
        "current_only_boundary_case_count": sum(
            1 for row in source_rows if row.get("current_only_boundary_case") is True
        ) if manifest_ready else 0,
        "reviewer_facing_family_exposed": False,
        "reviewer_facing_tier_exposed": False,
        "body_full_packet_materialized_here": False,
        "local_reviewer_payload_materialized_here": False,
        "body_full_packet_generation_requested_here": False,
        "body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "body_full_packet_generation_request_allowed_next": manifest_ready,
        "body_full_generation_blocked_until_packet_generation_request": True,
        "human_review_completion_claim_blocked_here": True,
        "actual_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_rating_or_question_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR05_IMPLEMENTED_STEPS if manifest_ready else P7_R54_AHR04_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR05_NOT_YET_IMPLEMENTED_STEPS if manifest_ready else P7_R54_AHR04_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR06_STEP_REF if manifest_ready else P7_R54_AHR05_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_ahr05_24_case_manifest_freeze_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_24_CASE_MANIFEST_FREEZE_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR05 24-case manifest freeze",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION,
        policy_section=P7_R54_AHR05_STEP_REF,
        operation_step_ref=P7_R54_AHR05_STEP_REF,
        source="P7-R54-AHR05 24-case manifest freeze",
    )
    _assert_current_execution_basis_refs(data, source="P7-R54-AHR05 24-case manifest freeze", actual_basis=True)
    if data.get("ahr04_schema_version") != P7_R54_AHR_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR05 must follow AHR04")
    if data.get("ahr04_preflight_status") not in P7_R54_AHR04_ALLOWED_PREFLIGHT_STATUS_REFS:
        raise ValueError("P7-R54-AHR05 AHR04 status changed")
    if data.get("required_case_count") != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-AHR05 required case count changed")
    if data.get("r48_case_matrix_schema_version") != r54op.P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR05 R48 case matrix schema changed")
    if safe_mapping(data.get("case_distribution")) != P7_R54_AHR05_CASE_DISTRIBUTION:
        raise ValueError("P7-R54-AHR05 case distribution changed")
    if data.get("case_distribution_total_count") != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-AHR05 case distribution total changed")
    if tuple(data.get("rating_axis_refs") or ()) != P7_R54_AHR05_RATING_AXIS_REFS:
        raise ValueError("P7-R54-AHR05 rating axis refs changed")
    if data.get("rating_axis_count") != len(P7_R54_AHR05_RATING_AXIS_REFS):
        raise ValueError("P7-R54-AHR05 rating axis count changed")
    if safe_mapping(data.get("rating_axis_target_thresholds")) != P7_R54_AHR05_RATING_AXIS_TARGET_THRESHOLDS:
        raise ValueError("P7-R54-AHR05 rating axis thresholds changed")
    for key in (
        "reviewer_facing_family_exposed",
        "reviewer_facing_tier_exposed",
        "body_full_packet_materialized_here",
        "local_reviewer_payload_materialized_here",
        "body_full_packet_generation_requested_here",
        "body_full_packet_generated_here",
        "actual_human_review_run_here",
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_disposal_receipt_materialized_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR05 must keep {key}=False")
    for key in (
        "body_full_generation_blocked_until_packet_generation_request",
        "human_review_completion_claim_blocked_here",
        "actual_review_completion_claim_blocked_here",
        "actual_human_review_completion_claim_blocked_here",
        "actual_rating_or_question_rows_claim_blocked_here",
        "disposal_receipt_claim_blocked_here",
        "r52_reintake_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR05 must keep {key}=True")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("P7-R54-AHR05 open blockers must match blockers")
    ready = data.get("manifest_status") == P7_R54_AHR05_MANIFEST_READY_STATUS_REF
    rows = [safe_mapping(row) for row in (data.get("case_rows") or [])]
    if ready:
        if data.get("ahr04_preflight_status") != P7_R54_AHR04_PREFLIGHT_READY_STATUS_REF:
            raise ValueError("P7-R54-AHR05 ready manifest requires ready AHR04")
        if data.get("ahr04_body_full_packet_generation_allowed_by_preflight") is not True:
            raise ValueError("P7-R54-AHR05 ready manifest requires AHR04 preflight allowance")
        if data.get("local_only_preflight_ready") is not True:
            raise ValueError("P7-R54-AHR05 ready manifest requires local-only preflight ready")
        if data.get("manifest_reason_refs") != [P7_R54_AHR05_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR05 ready reason changed")
        if blockers:
            raise ValueError("P7-R54-AHR05 ready manifest must not carry blockers")
        required_count = P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        if len(rows) != required_count or data.get("case_row_count") != required_count:
            raise ValueError("P7-R54-AHR05 must freeze 24 body-free rows")
        for index, row in enumerate(rows, start=1):
            _assert_ahr05_case_manifest_row(row, expected_index=index)
        case_refs = [clean_identifier(row.get("case_ref_id"), max_length=180) for row in rows]
        blind_ids = [clean_identifier(row.get("blind_case_id"), max_length=180) for row in rows]
        packet_refs = [clean_identifier(row.get("packet_ref_id"), max_length=180) for row in rows]
        family_counts = _count_by(rows, "family")
        case_role_counts = _count_by(rows, "case_role")
        tier_counts = _count_by(rows, "subscription_tier_ref")
        history_policy_counts = _count_by(rows, "history_evidence_policy_ref")
        if data.get("case_ref_ids") != case_refs or data.get("case_ref_id_count") != required_count:
            raise ValueError("P7-R54-AHR05 case ref list changed")
        if data.get("blind_case_ids") != blind_ids or data.get("blind_case_id_count") != required_count:
            raise ValueError("P7-R54-AHR05 blind case id list changed")
        if data.get("packet_ref_ids") != packet_refs or data.get("packet_ref_id_count") != required_count:
            raise ValueError("P7-R54-AHR05 packet ref list changed")
        for key, values in (
            ("case_ref_ids_unique", case_refs),
            ("blind_case_ids_unique", blind_ids),
            ("packet_ref_ids_unique", packet_refs),
        ):
            if data.get(key) is not True or not _unique_non_empty(values, required_count=required_count):
                raise ValueError(f"P7-R54-AHR05 {key} failed")
        if not set(case_refs).isdisjoint(set(blind_ids)) or data.get("blind_case_id_case_ref_separated") is not True:
            raise ValueError("P7-R54-AHR05 blind_case_id/case_ref_id separation failed")
        if not set(blind_ids).isdisjoint(set(packet_refs)) or data.get("blind_case_id_packet_ref_separated") is not True:
            raise ValueError("P7-R54-AHR05 blind_case_id/packet_ref_id separation failed")
        if not set(case_refs).isdisjoint(set(packet_refs)) or data.get("case_ref_id_packet_ref_separated") is not True:
            raise ValueError("P7-R54-AHR05 case_ref_id/packet_ref_id separation failed")
        if family_counts != P7_R54_AHR05_CASE_DISTRIBUTION or data.get("family_case_counts") != family_counts:
            raise ValueError("P7-R54-AHR05 family distribution changed")
        if data.get("case_role_counts") != case_role_counts:
            raise ValueError("P7-R54-AHR05 case role counts changed")
        if data.get("subscription_tier_ref_counts") != tier_counts:
            raise ValueError("P7-R54-AHR05 tier counts changed")
        if data.get("history_evidence_policy_ref_counts") != history_policy_counts:
            raise ValueError("P7-R54-AHR05 history policy counts changed")
        if data.get("case_distribution_matches_design") is not True:
            raise ValueError("P7-R54-AHR05 distribution must match design")
        if data.get("case_rows_bodyfree_only") is not True:
            raise ValueError("P7-R54-AHR05 case rows must be body-free")
        if data.get("requires_history_line_review_count") != 20:
            raise ValueError("P7-R54-AHR05 history-line review count changed")
        if data.get("current_only_boundary_case_count") != 4:
            raise ValueError("P7-R54-AHR05 current-only boundary case count changed")
        if data.get("body_full_packet_generation_request_allowed_next") is not True:
            raise ValueError("P7-R54-AHR05 ready manifest must allow next packet request step")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR05_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR05 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR05_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR05 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR06_STEP_REF:
            raise ValueError("P7-R54-AHR05 next step changed")
    else:
        if data.get("manifest_status") != P7_R54_AHR05_MANIFEST_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR05 blocked status changed")
        if data.get("body_full_packet_generation_request_allowed_next") is not False:
            raise ValueError("P7-R54-AHR05 blocked manifest must not allow packet request")
        if data.get("case_rows") != [] or data.get("case_row_count") != 0:
            raise ValueError("P7-R54-AHR05 blocked manifest must not carry rows")
        if not blockers:
            raise ValueError("P7-R54-AHR05 blocked manifest must carry blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR04_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR05 blocked implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR04_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR05 blocked not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR05_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR05 blocked next step changed")
    return True



def _ahr06_request_status_and_blockers(
    *,
    prior_manifest_ready: bool,
    manifest_request_allowed: bool,
    case_row_count: int,
    case_ref_id_count: int,
    blind_case_id_count: int,
    packet_ref_id_count: int,
    packet_ref_ids_unique: bool,
    local_only: bool,
    must_not_export: bool,
    disposal_required: bool,
    explicit_allow_token_present: bool,
    packet_generation_request_ref: str,
    local_packet_generation_operation_ref: str,
) -> tuple[str, list[str], list[str]]:
    blockers: list[str] = []
    if not prior_manifest_ready:
        blockers.append("ahr05_manifest_not_ready")
    if not manifest_request_allowed:
        blockers.append("ahr05_packet_generation_request_not_allowed")
    if case_row_count != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("case_row_count_not_24")
    if case_ref_id_count != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("case_ref_id_count_not_24")
    if blind_case_id_count != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("blind_case_id_count_not_24")
    if packet_ref_id_count != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("packet_ref_id_count_not_24")
    if not packet_ref_ids_unique:
        blockers.append("packet_ref_ids_not_unique")
    if not local_only:
        blockers.append("local_only_not_confirmed")
    if not must_not_export:
        blockers.append("must_not_export_not_confirmed")
    if not disposal_required:
        blockers.append("disposal_required_not_confirmed")
    if not explicit_allow_token_present:
        blockers.append("explicit_allow_token_missing")
    if packet_generation_request_ref != P7_R54_AHR06_EXPLICIT_REQUEST_REF:
        blockers.append("packet_generation_request_ref_missing_or_unexpected")
    if local_packet_generation_operation_ref != P7_R54_AHR06_LOCAL_PACKET_GENERATION_OPERATION_REF:
        blockers.append("local_packet_generation_operation_ref_missing_or_unexpected")
    blockers = dedupe_identifiers(blockers, limit=40, max_length=180)
    if blockers:
        return P7_R54_AHR06_REQUEST_BLOCKED_STATUS_REF, blockers, blockers
    return P7_R54_AHR06_REQUEST_READY_STATUS_REF, [P7_R54_AHR06_READY_REASON_REF], []


def build_p7_r54_ahr06_body_full_packet_generation_request_bodyfree_evidence(
    *,
    review_session_id: Any = P7_R54_AHR_DEFAULT_REVIEW_SESSION_ID,
    manifest_freeze: Mapping[str, Any] | None = None,
    local_only: bool = True,
    must_not_export: bool = True,
    disposal_required: bool = True,
    explicit_allow_token_ref: Any = P7_R54_AHR04_EXPLICIT_LOCAL_ONLY_ALLOW_REF,
    packet_generation_request_ref: Any = P7_R54_AHR06_EXPLICIT_REQUEST_REF,
    local_packet_generation_operation_ref: Any = P7_R54_AHR06_LOCAL_PACKET_GENERATION_OPERATION_REF,
) -> dict[str, Any]:
    session_id = _safe_review_session_id(review_session_id)
    prior = dict(manifest_freeze or build_p7_r54_ahr05_24_case_manifest_freeze(review_session_id=session_id))
    assert_p7_r54_ahr05_24_case_manifest_freeze_contract(prior)
    case_rows = [safe_mapping(row) for row in (prior.get("case_rows") or [])]
    case_ref_ids = [clean_identifier(row.get("case_ref_id"), max_length=180) for row in case_rows]
    blind_case_ids = [clean_identifier(row.get("blind_case_id"), max_length=180) for row in case_rows]
    packet_ref_ids = [clean_identifier(row.get("packet_ref_id"), max_length=180) for row in case_rows]
    prior_manifest_ready = prior.get("manifest_status") == P7_R54_AHR05_MANIFEST_READY_STATUS_REF
    manifest_request_allowed = prior.get("body_full_packet_generation_request_allowed_next") is True
    request_ref = clean_identifier(packet_generation_request_ref, max_length=180)
    operation_ref = clean_identifier(local_packet_generation_operation_ref, max_length=180)
    explicit_allow_ref = clean_identifier(explicit_allow_token_ref, max_length=180)
    status, reasons, blockers = _ahr06_request_status_and_blockers(
        prior_manifest_ready=prior_manifest_ready,
        manifest_request_allowed=manifest_request_allowed,
        case_row_count=len(case_rows),
        case_ref_id_count=len(case_ref_ids),
        blind_case_id_count=len(blind_case_ids),
        packet_ref_id_count=len(packet_ref_ids),
        packet_ref_ids_unique=_unique_non_empty(packet_ref_ids, required_count=P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT),
        local_only=local_only,
        must_not_export=must_not_export,
        disposal_required=disposal_required,
        explicit_allow_token_present=explicit_allow_ref == P7_R54_AHR04_EXPLICIT_LOCAL_ONLY_ALLOW_REF,
        packet_generation_request_ref=request_ref,
        local_packet_generation_operation_ref=operation_ref,
    )
    ready = status == P7_R54_AHR06_REQUEST_READY_STATUS_REF
    if not ready:
        case_ref_ids = []
        blind_case_ids = []
        packet_ref_ids = []
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_EVIDENCE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_STEP,
        "scope": P7_R54_AHR_SCOPE,
        "policy_kind": P7_R54_AHR_POLICY_KIND,
        "policy_section": P7_R54_AHR06_STEP_REF,
        "operation_step_ref": P7_R54_AHR06_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": f"p7_r54_ahr06_body_full_packet_generation_request_bodyfree_evidence_{session_id}",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ahr05_schema_version": prior.get("schema_version"),
        "ahr05_material_ref": clean_identifier(prior.get("material_id"), max_length=180),
        "ahr05_next_required_step": clean_identifier(prior.get("next_required_step"), max_length=180),
        "ahr05_manifest_status": clean_identifier(prior.get("manifest_status"), max_length=180),
        "ahr05_required_case_count": int(prior.get("required_case_count") or 0),
        "ahr05_case_row_count": int(prior.get("case_row_count") or 0),
        "ahr05_case_ref_id_count": int(prior.get("case_ref_id_count") or 0),
        "ahr05_blind_case_id_count": int(prior.get("blind_case_id_count") or 0),
        "ahr05_packet_ref_id_count": int(prior.get("packet_ref_id_count") or 0),
        "ahr05_body_full_packet_generation_request_allowed_next": prior.get("body_full_packet_generation_request_allowed_next") is True,
        "ahr05_case_rows_bodyfree_only": prior.get("case_rows_bodyfree_only") is True,
        **_current_execution_basis_material_fields(actual_basis=True),
        "packet_generation_request_status": status,
        "packet_generation_request_reason_refs": reasons,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "manifest_ready_for_packet_generation_request": ready,
        "body_full_packet_generation_request_allowed_from_manifest": manifest_request_allowed and prior_manifest_ready,
        "local_only": local_only,
        "must_not_export": must_not_export,
        "disposal_required": disposal_required,
        "explicit_allow_token_ref": explicit_allow_ref,
        "explicit_allow_token_present": explicit_allow_ref == P7_R54_AHR04_EXPLICIT_LOCAL_ONLY_ALLOW_REF,
        "packet_generation_request_ref": request_ref,
        "packet_generation_request_ref_present": request_ref == P7_R54_AHR06_EXPLICIT_REQUEST_REF,
        "packet_generation_request_is_ref_only": request_ref == P7_R54_AHR06_EXPLICIT_REQUEST_REF,
        "local_packet_generation_operation_ref": operation_ref,
        "local_packet_generation_operation_ref_only": operation_ref == P7_R54_AHR06_LOCAL_PACKET_GENERATION_OPERATION_REF,
        "required_case_count": P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "case_row_count": len(case_ref_ids),
        "case_ref_ids": case_ref_ids,
        "case_ref_id_count": len(case_ref_ids),
        "blind_case_ids": blind_case_ids,
        "blind_case_id_count": len(blind_case_ids),
        "packet_ref_ids": packet_ref_ids,
        "packet_ref_id_count": len(packet_ref_ids),
        "packet_ref_ids_unique": _unique_non_empty(packet_ref_ids, required_count=P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT),
        "packet_generation_requested": ready,
        "packet_generation_requested_as_bodyfree_evidence_only": ready,
        "body_full_packet_generation_request_evidence_only": True,
        "body_full_packet_generation_requested_here": False,
        "body_full_generation_requested_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packet_materialized_here": False,
        "local_reviewer_payload_materialized_here": False,
        "local_packet_generation_operation_allowed_next": ready,
        "local_packet_generation_receipt_required_next": ready,
        "actual_review_execution_blocked_until_local_packet_receipt": True,
        "human_review_completion_claim_blocked_here": True,
        "actual_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_rating_or_question_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "body_full_packet_content_included": False,
        "raw_input_included": False,
        "returned_emlis_body_included": False,
        "history_surface_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_absolute_path_included": False,
        "body_hash_included": False,
        "terminal_output_body_included": False,
        "packet_content_included": False,
        "implemented_steps": list(P7_R54_AHR06_IMPLEMENTED_STEPS if ready else P7_R54_AHR05_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR06_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR05_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR07_STEP_REF if ready else P7_R54_AHR06_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_ahr06_body_full_packet_generation_request_bodyfree_evidence_contract(
    data: Mapping[str, Any]
) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR06_BODY_FULL_PACKET_GENERATION_REQUEST_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR06 body-full packet generation request body-free evidence",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_EVIDENCE_SCHEMA_VERSION,
        policy_section=P7_R54_AHR06_STEP_REF,
        operation_step_ref=P7_R54_AHR06_STEP_REF,
        source="P7-R54-AHR06 body-full packet generation request body-free evidence",
    )
    _assert_current_execution_basis_refs(data, source="P7-R54-AHR06 body-full packet generation request body-free evidence", actual_basis=True)
    if data.get("ahr05_schema_version") != P7_R54_AHR_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR06 must follow AHR05")
    if data.get("packet_generation_request_status") not in P7_R54_AHR06_ALLOWED_REQUEST_STATUS_REFS:
        raise ValueError("P7-R54-AHR06 request status changed")
    if data.get("required_case_count") != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-AHR06 required case count changed")
    for key in (
        "body_full_packet_generation_request_evidence_only",
        "actual_review_execution_blocked_until_local_packet_receipt",
        "human_review_completion_claim_blocked_here",
        "actual_review_completion_claim_blocked_here",
        "actual_human_review_completion_claim_blocked_here",
        "actual_rating_or_question_rows_claim_blocked_here",
        "disposal_receipt_claim_blocked_here",
        "r52_reintake_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR06 must keep {key}=True")
    for key in (
        "body_full_packet_generation_requested_here",
        "body_full_generation_requested_here",
        "body_full_packet_generated_here",
        "body_full_packet_materialized_here",
        "local_reviewer_payload_materialized_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR06 must keep {key}=False")
    for key in P7_R54_AHR06_FORBIDDEN_EVIDENCE_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR06 must keep forbidden evidence flag {key}=False")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("P7-R54-AHR06 open blockers must match blockers")
    ready = data.get("packet_generation_request_status") == P7_R54_AHR06_REQUEST_READY_STATUS_REF
    if ready:
        if data.get("ahr05_manifest_status") != P7_R54_AHR05_MANIFEST_READY_STATUS_REF:
            raise ValueError("P7-R54-AHR06 ready request requires ready AHR05 manifest")
        if data.get("ahr05_body_full_packet_generation_request_allowed_next") is not True:
            raise ValueError("P7-R54-AHR06 ready request requires AHR05 request allowance")
        if data.get("ahr05_case_rows_bodyfree_only") is not True:
            raise ValueError("P7-R54-AHR06 ready request requires body-free AHR05 rows")
        if data.get("case_row_count") != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR06 ready request must carry 24 case refs")
        if data.get("case_ref_id_count") != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR06 case ref count changed")
        if data.get("blind_case_id_count") != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR06 blind case count changed")
        packet_refs = [clean_identifier(value, max_length=180) for value in (data.get("packet_ref_ids") or [])]
        if data.get("packet_ref_id_count") != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR06 packet ref count changed")
        if data.get("packet_ref_ids_unique") is not True or not _unique_non_empty(packet_refs, required_count=P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT):
            raise ValueError("P7-R54-AHR06 packet refs must remain unique body-free refs")
        for key in (
            "manifest_ready_for_packet_generation_request",
            "body_full_packet_generation_request_allowed_from_manifest",
            "local_only",
            "must_not_export",
            "disposal_required",
            "explicit_allow_token_present",
            "packet_generation_request_ref_present",
            "packet_generation_request_is_ref_only",
            "local_packet_generation_operation_ref_only",
            "packet_generation_requested",
            "packet_generation_requested_as_bodyfree_evidence_only",
            "local_packet_generation_operation_allowed_next",
            "local_packet_generation_receipt_required_next",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR06 ready request must keep {key}=True")
        if data.get("packet_generation_request_ref") != P7_R54_AHR06_EXPLICIT_REQUEST_REF:
            raise ValueError("P7-R54-AHR06 request ref changed")
        if data.get("local_packet_generation_operation_ref") != P7_R54_AHR06_LOCAL_PACKET_GENERATION_OPERATION_REF:
            raise ValueError("P7-R54-AHR06 local operation ref changed")
        if data.get("packet_generation_request_reason_refs") != [P7_R54_AHR06_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR06 ready reason changed")
        if blockers:
            raise ValueError("P7-R54-AHR06 ready request must not carry blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR06_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR06 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR06_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR06 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR07_STEP_REF:
            raise ValueError("P7-R54-AHR06 next step changed")
    else:
        if data.get("packet_generation_request_status") != P7_R54_AHR06_REQUEST_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR06 blocked status changed")
        if not blockers:
            raise ValueError("P7-R54-AHR06 blocked request must carry blockers")
        for key in (
            "packet_generation_requested",
            "packet_generation_requested_as_bodyfree_evidence_only",
            "local_packet_generation_operation_allowed_next",
            "local_packet_generation_receipt_required_next",
        ):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR06 blocked request must keep {key}=False")
        if data.get("case_row_count") != 0 or data.get("packet_ref_ids") != []:
            raise ValueError("P7-R54-AHR06 blocked request must not carry packet refs")
        if data.get("next_required_step") != P7_R54_AHR06_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR06 blocked next step changed")
    return True


def _ahr07_receipt_status_and_blockers(
    *,
    ahr06_ready: bool,
    required_case_count: int,
    expected_packet_ref_id_count: int,
    generated_case_count: int,
    generated_packet_count: int,
    local_only: bool,
    must_not_export: bool,
    local_packet_exported: bool,
    exported: bool,
    content_included: bool,
    absolute_path_included: bool,
    hash_included: bool,
) -> tuple[str, list[str], list[str]]:
    blockers: list[str] = []
    if not ahr06_ready:
        blockers.append("ahr06_packet_generation_request_not_ready")
    if required_case_count != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("required_case_count_not_24")
    if expected_packet_ref_id_count != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("expected_packet_ref_id_count_not_24")
    if generated_case_count != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("generated_case_count_not_24")
    if generated_packet_count != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("generated_packet_count_not_24")
    if not local_only:
        blockers.append("local_only_not_confirmed")
    if not must_not_export:
        blockers.append("must_not_export_not_confirmed")
    if local_packet_exported:
        blockers.append("local_packet_exported")
    if exported:
        blockers.append("receipt_marked_exported")
    if content_included:
        blockers.append("packet_content_included")
    if absolute_path_included:
        blockers.append("absolute_path_included")
    if hash_included:
        blockers.append("hash_included")
    blockers = dedupe_identifiers(blockers, limit=40, max_length=180)
    if blockers:
        return P7_R54_AHR07_RECEIPT_BLOCKED_STATUS_REF, blockers, blockers
    return P7_R54_AHR07_RECEIPT_READY_STATUS_REF, [P7_R54_AHR07_READY_REASON_REF], []


def build_p7_r54_ahr07_local_packet_generation_operation_receipt_intake(
    *,
    review_session_id: Any = P7_R54_AHR_DEFAULT_REVIEW_SESSION_ID,
    packet_generation_request: Mapping[str, Any] | None = None,
    generated_case_count: int = P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
    generated_packet_count: int = P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
    local_only: bool = True,
    must_not_export: bool = True,
    local_packet_exported: bool = False,
    exported: bool = False,
    content_included: bool = False,
    absolute_path_included: bool = False,
    hash_included: bool = False,
) -> dict[str, Any]:
    session_id = _safe_review_session_id(review_session_id)
    prior = dict(packet_generation_request or build_p7_r54_ahr06_body_full_packet_generation_request_bodyfree_evidence(review_session_id=session_id))
    assert_p7_r54_ahr06_body_full_packet_generation_request_bodyfree_evidence_contract(prior)
    ahr06_ready = prior.get("packet_generation_request_status") == P7_R54_AHR06_REQUEST_READY_STATUS_REF
    expected_packet_refs = [clean_identifier(value, max_length=180) for value in (prior.get("packet_ref_ids") or [])]
    status, reasons, blockers = _ahr07_receipt_status_and_blockers(
        ahr06_ready=ahr06_ready,
        required_case_count=int(prior.get("required_case_count") or 0),
        expected_packet_ref_id_count=len(expected_packet_refs),
        generated_case_count=generated_case_count,
        generated_packet_count=generated_packet_count,
        local_only=local_only,
        must_not_export=must_not_export,
        local_packet_exported=local_packet_exported,
        exported=exported,
        content_included=content_included,
        absolute_path_included=absolute_path_included,
        hash_included=hash_included,
    )
    ready = status == P7_R54_AHR07_RECEIPT_READY_STATUS_REF
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_LOCAL_PACKET_GENERATION_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_STEP,
        "scope": P7_R54_AHR_SCOPE,
        "policy_kind": P7_R54_AHR_POLICY_KIND,
        "policy_section": P7_R54_AHR07_STEP_REF,
        "operation_step_ref": P7_R54_AHR07_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": f"p7_r54_ahr07_local_packet_generation_operation_receipt_intake_{session_id}",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ahr06_schema_version": prior.get("schema_version"),
        "ahr06_material_ref": clean_identifier(prior.get("material_id"), max_length=180),
        "ahr06_next_required_step": clean_identifier(prior.get("next_required_step"), max_length=180),
        "ahr06_packet_generation_request_status": clean_identifier(prior.get("packet_generation_request_status"), max_length=180),
        "ahr06_packet_generation_requested": prior.get("packet_generation_requested") is True,
        "ahr06_local_packet_generation_operation_allowed_next": prior.get("local_packet_generation_operation_allowed_next") is True,
        "ahr06_required_case_count": int(prior.get("required_case_count") or 0),
        "ahr06_packet_ref_id_count": int(prior.get("packet_ref_id_count") or 0),
        "ahr06_packet_ref_ids": expected_packet_refs,
        **_current_execution_basis_material_fields(actual_basis=True),
        "receipt_status": status,
        "generation_status_ref": P7_R54_AHR07_RECEIPT_READY_STATUS_REF if ready else P7_R54_AHR07_RECEIPT_BLOCKED_STATUS_REF,
        "receipt_reason_refs": reasons,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "request_ready_for_receipt_intake": ahr06_ready,
        "required_case_count": P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "expected_generated_case_count": P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "expected_generated_packet_count": P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "generated_case_count": int(generated_case_count),
        "generated_packet_count": int(generated_packet_count),
        "generated_packet_refs_match_expected_count": ready,
        "local_only": local_only,
        "must_not_export": must_not_export,
        "exported": False,
        "local_packet_exported": False,
        "content_included": False,
        "absolute_path_included": False,
        "hash_included": False,
        "packet_content_included": False,
        "body_full_packet_content_included": False,
        "raw_input_included": False,
        "returned_emlis_body_included": False,
        "history_surface_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_absolute_path_included": False,
        "body_hash_included": False,
        "terminal_output_body_included": False,
        "body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "actual_review_execution_allowed_next": False,
        "packet_generation_operation_receipt_only": True,
        "local_packet_generation_operation_receipt_intaken": ready,
        "packet_generation_receipt_intaken": ready,
        "packet_completeness_export_denylist_scan_allowed_next": ready,
        "actual_review_execution_blocked_until_packet_completeness_scan": True,
        "human_review_completion_claim_blocked_here": True,
        "actual_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_rating_or_question_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR07_IMPLEMENTED_STEPS if ready else P7_R54_AHR06_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR07_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR06_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR08_STEP_REF if ready else P7_R54_AHR07_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_ahr07_local_packet_generation_operation_receipt_intake_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR07_LOCAL_PACKET_GENERATION_RECEIPT_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR07 local packet generation operation receipt intake",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_LOCAL_PACKET_GENERATION_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION,
        policy_section=P7_R54_AHR07_STEP_REF,
        operation_step_ref=P7_R54_AHR07_STEP_REF,
        source="P7-R54-AHR07 local packet generation operation receipt intake",
    )
    _assert_current_execution_basis_refs(data, source="P7-R54-AHR07 local packet generation operation receipt intake", actual_basis=True)
    if data.get("ahr06_schema_version") != P7_R54_AHR_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR07 must follow AHR06")
    if data.get("receipt_status") not in P7_R54_AHR07_ALLOWED_RECEIPT_STATUS_REFS:
        raise ValueError("P7-R54-AHR07 receipt status changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("P7-R54-AHR07 open blockers must match blockers")
    for key in (
        "packet_generation_operation_receipt_only",
        "actual_review_execution_blocked_until_packet_completeness_scan",
        "human_review_completion_claim_blocked_here",
        "actual_review_completion_claim_blocked_here",
        "actual_human_review_completion_claim_blocked_here",
        "actual_rating_or_question_rows_claim_blocked_here",
        "disposal_receipt_claim_blocked_here",
        "r52_reintake_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR07 must keep {key}=True")
    for key in (
        "local_packet_exported",
        "exported",
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
        "body_full_packet_generated_here",
        "actual_human_review_run_here",
        "actual_review_execution_allowed_next",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR07 must keep {key}=False")
    ready = data.get("receipt_status") == P7_R54_AHR07_RECEIPT_READY_STATUS_REF
    if ready:
        if data.get("ahr06_packet_generation_request_status") != P7_R54_AHR06_REQUEST_READY_STATUS_REF:
            raise ValueError("P7-R54-AHR07 ready receipt requires ready AHR06 request")
        if data.get("ahr06_packet_generation_requested") is not True:
            raise ValueError("P7-R54-AHR07 ready receipt requires AHR06 packet request")
        if data.get("ahr06_local_packet_generation_operation_allowed_next") is not True:
            raise ValueError("P7-R54-AHR07 ready receipt requires allowed local operation")
        for key in (
            "request_ready_for_receipt_intake",
            "generated_packet_refs_match_expected_count",
            "local_only",
            "must_not_export",
            "local_packet_generation_operation_receipt_intaken",
            "packet_generation_receipt_intaken",
            "packet_completeness_export_denylist_scan_allowed_next",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR07 ready receipt must keep {key}=True")
        if data.get("generated_case_count") != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR07 generated case count changed")
        if data.get("generated_packet_count") != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR07 generated packet count changed")
        if data.get("generation_status_ref") != P7_R54_AHR07_RECEIPT_READY_STATUS_REF:
            raise ValueError("P7-R54-AHR07 generation status changed")
        if data.get("receipt_reason_refs") != [P7_R54_AHR07_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR07 ready reason changed")
        if blockers:
            raise ValueError("P7-R54-AHR07 ready receipt must not carry blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR07_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR07 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR07_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR07 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR08_STEP_REF:
            raise ValueError("P7-R54-AHR07 next step changed")
    else:
        if data.get("receipt_status") != P7_R54_AHR07_RECEIPT_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR07 blocked status changed")
        if not blockers:
            raise ValueError("P7-R54-AHR07 blocked receipt must carry blockers")
        for key in (
            "local_packet_generation_operation_receipt_intaken",
            "packet_generation_receipt_intaken",
            "packet_completeness_export_denylist_scan_allowed_next",
        ):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR07 blocked receipt must keep {key}=False")
        if data.get("next_required_step") != P7_R54_AHR07_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR07 blocked next step changed")
    return True


build_p7_r54_ahr06_body_full_packet_generation_request_bodyfree = (
    build_p7_r54_ahr06_body_full_packet_generation_request_bodyfree_evidence
)
assert_p7_r54_ahr06_body_full_packet_generation_request_bodyfree_contract = (
    assert_p7_r54_ahr06_body_full_packet_generation_request_bodyfree_evidence_contract
)
build_p7_r54_ahr07_local_packet_generation_operation_receipt_intake_bodyfree = (
    build_p7_r54_ahr07_local_packet_generation_operation_receipt_intake
)
assert_p7_r54_ahr07_local_packet_generation_operation_receipt_intake_bodyfree_contract = (
    assert_p7_r54_ahr07_local_packet_generation_operation_receipt_intake_contract
)
build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr06_body_full_packet_generation_request_bodyfree_evidence = (
    build_p7_r54_ahr06_body_full_packet_generation_request_bodyfree_evidence
)
assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr06_body_full_packet_generation_request_bodyfree_evidence_contract = (
    assert_p7_r54_ahr06_body_full_packet_generation_request_bodyfree_evidence_contract
)
build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr07_local_packet_generation_operation_receipt_intake = (
    build_p7_r54_ahr07_local_packet_generation_operation_receipt_intake
)
assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr07_local_packet_generation_operation_receipt_intake_contract = (
    assert_p7_r54_ahr07_local_packet_generation_operation_receipt_intake_contract
)
build_p7_r54_actual_human_review_execution_body_full_packet_generation_request_bodyfree_evidence = (
    build_p7_r54_ahr06_body_full_packet_generation_request_bodyfree_evidence
)
assert_p7_r54_actual_human_review_execution_body_full_packet_generation_request_bodyfree_evidence_contract = (
    assert_p7_r54_ahr06_body_full_packet_generation_request_bodyfree_evidence_contract
)
build_p7_r54_actual_human_review_execution_local_packet_generation_operation_receipt_intake_bodyfree = (
    build_p7_r54_ahr07_local_packet_generation_operation_receipt_intake
)
assert_p7_r54_actual_human_review_execution_local_packet_generation_operation_receipt_intake_bodyfree_contract = (
    assert_p7_r54_ahr07_local_packet_generation_operation_receipt_intake_contract
)




# Compatibility aliases for future split files / documentation wording.
build_p7_r54_ahr00_scope_no_touch_boundary_freeze_bodyfree = build_p7_r54_ahr00_scope_no_touch_boundary_freeze
assert_p7_r54_ahr00_scope_no_touch_boundary_freeze_bodyfree_contract = (
    assert_p7_r54_ahr00_scope_no_touch_boundary_freeze_contract
)
build_p7_r54_ahr01_current_execution_basis_refreeze_bodyfree = build_p7_r54_ahr01_current_execution_basis_refreeze
assert_p7_r54_ahr01_current_execution_basis_refreeze_bodyfree_contract = (
    assert_p7_r54_ahr01_current_execution_basis_refreeze_contract
)
build_p7_r54_ahr02_historical_helper_refs_reconcile_bodyfree = build_p7_r54_ahr02_historical_helper_refs_reconcile
assert_p7_r54_ahr02_historical_helper_refs_reconcile_bodyfree_contract = (
    assert_p7_r54_ahr02_historical_helper_refs_reconcile_contract
)
build_p7_r54_ahr03_r55_hold_evidence_missing_intake_bodyfree = build_p7_r54_ahr03_r55_hold_evidence_missing_intake
assert_p7_r54_ahr03_r55_hold_evidence_missing_intake_bodyfree_contract = (
    assert_p7_r54_ahr03_r55_hold_evidence_missing_intake_contract
)
build_p7_r54_ahr04_local_only_preflight_bodyfree = build_p7_r54_ahr04_local_only_preflight
assert_p7_r54_ahr04_local_only_preflight_bodyfree_contract = (
    assert_p7_r54_ahr04_local_only_preflight_contract
)
build_p7_r54_ahr05_24_case_manifest_freeze_bodyfree = build_p7_r54_ahr05_24_case_manifest_freeze
assert_p7_r54_ahr05_24_case_manifest_freeze_bodyfree_contract = (
    assert_p7_r54_ahr05_24_case_manifest_freeze_contract
)
build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr00_scope_no_touch_boundary_freeze = (
    build_p7_r54_ahr00_scope_no_touch_boundary_freeze
)
assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr00_scope_no_touch_boundary_freeze_contract = (
    assert_p7_r54_ahr00_scope_no_touch_boundary_freeze_contract
)
build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr01_current_execution_basis_refreeze = (
    build_p7_r54_ahr01_current_execution_basis_refreeze
)
assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr01_current_execution_basis_refreeze_contract = (
    assert_p7_r54_ahr01_current_execution_basis_refreeze_contract
)
build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr02_historical_helper_refs_reconcile = (
    build_p7_r54_ahr02_historical_helper_refs_reconcile
)
assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr02_historical_helper_refs_reconcile_contract = (
    assert_p7_r54_ahr02_historical_helper_refs_reconcile_contract
)
build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr03_r55_hold_evidence_missing_intake = (
    build_p7_r54_ahr03_r55_hold_evidence_missing_intake
)
assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr03_r55_hold_evidence_missing_intake_contract = (
    assert_p7_r54_ahr03_r55_hold_evidence_missing_intake_contract
)
build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr04_local_only_preflight = (
    build_p7_r54_ahr04_local_only_preflight
)
assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr04_local_only_preflight_contract = (
    assert_p7_r54_ahr04_local_only_preflight_contract
)
build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr05_24_case_manifest_freeze = (
    build_p7_r54_ahr05_24_case_manifest_freeze
)
assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr05_24_case_manifest_freeze_contract = (
    assert_p7_r54_ahr05_24_case_manifest_freeze_contract
)

# Additional compatibility aliases used by the AHR design wording.
build_p7_r54_actual_human_review_execution_scope_no_touch_boundary_freeze_bodyfree = (
    build_p7_r54_ahr00_scope_no_touch_boundary_freeze
)
assert_p7_r54_actual_human_review_execution_scope_no_touch_boundary_freeze_bodyfree_contract = (
    assert_p7_r54_ahr00_scope_no_touch_boundary_freeze_contract
)
build_p7_r54_actual_human_review_execution_current_execution_basis_refreeze_bodyfree = (
    build_p7_r54_ahr01_current_execution_basis_refreeze
)
assert_p7_r54_actual_human_review_execution_current_execution_basis_refreeze_bodyfree_contract = (
    assert_p7_r54_ahr01_current_execution_basis_refreeze_contract
)
build_p7_r54_actual_human_review_execution_historical_helper_refs_reconcile_bodyfree = (
    build_p7_r54_ahr02_historical_helper_refs_reconcile
)
assert_p7_r54_actual_human_review_execution_historical_helper_refs_reconcile_bodyfree_contract = (
    assert_p7_r54_ahr02_historical_helper_refs_reconcile_contract
)
build_p7_r54_actual_human_review_execution_r55_hold_evidence_missing_intake_bodyfree = (
    build_p7_r54_ahr03_r55_hold_evidence_missing_intake
)
assert_p7_r54_actual_human_review_execution_r55_hold_evidence_missing_intake_bodyfree_contract = (
    assert_p7_r54_ahr03_r55_hold_evidence_missing_intake_contract
)
build_p7_r54_actual_human_review_execution_local_only_preflight_bodyfree = (
    build_p7_r54_ahr04_local_only_preflight
)
assert_p7_r54_actual_human_review_execution_local_only_preflight_bodyfree_contract = (
    assert_p7_r54_ahr04_local_only_preflight_contract
)
build_p7_r54_actual_human_review_execution_24_case_manifest_freeze_bodyfree = (
    build_p7_r54_ahr05_24_case_manifest_freeze
)
assert_p7_r54_actual_human_review_execution_24_case_manifest_freeze_bodyfree_contract = (
    assert_p7_r54_ahr05_24_case_manifest_freeze_contract
)

# ---------------------------------------------------------------------------
# R54-AHR-08 / R54-AHR-09: packet scan and reviewer selection-form freeze.
# ---------------------------------------------------------------------------

P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR08: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR07[1:]
P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR09: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR08[1:]
P7_R54_AHR08_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_AHR07_IMPLEMENTED_STEPS, P7_R54_AHR08_STEP_REF)
P7_R54_AHR08_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR08
P7_R54_AHR09_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_AHR08_IMPLEMENTED_STEPS, P7_R54_AHR09_STEP_REF)
P7_R54_AHR09_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR09

P7_R54_AHR_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.ahr08_packet_completeness_export_denylist_scan.bodyfree.v1"
)
P7_R54_AHR_REVIEWER_SELECTION_FORM_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.ahr09_reviewer_selection_form_freeze.bodyfree.v1"
)
P7_R54_AHR08_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION: Final = (
    P7_R54_AHR_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION
)
P7_R54_AHR09_REVIEWER_SELECTION_FORM_FREEZE_SCHEMA_VERSION: Final = (
    P7_R54_AHR_REVIEWER_SELECTION_FORM_FREEZE_SCHEMA_VERSION
)

P7_R54_AHR08_SCAN_PASSED_STATUS_REF: Final = "AHR_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_PASSED"
P7_R54_AHR08_SCAN_BLOCKED_STATUS_REF: Final = "AHR_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_BLOCKED"
P7_R54_AHR08_ALLOWED_SCAN_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR08_SCAN_PASSED_STATUS_REF,
    P7_R54_AHR08_SCAN_BLOCKED_STATUS_REF,
)
P7_R54_AHR08_READY_REASON_REF: Final = "r54_ahr_packet_completeness_export_denylist_scan_passed"
P7_R54_AHR08_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-08_repair_packet_completeness_export_denylist_scan_before_reviewer_form"
)
P7_R54_AHR08_SCAN_TARGET_REFS: Final[tuple[str, ...]] = (
    "raw_input",
    "returned_emlis_body",
    "history_surface",
    "comment_text_body",
    "reviewer_free_text",
    "reviewer_notes",
    "question_text",
    "draft_question_text",
    "packet_content",
    "body_hash",
    "local_absolute_path",
    "terminal_output_body",
    "stdout",
    "stderr",
    "traceback",
)
P7_R54_AHR08_FORBIDDEN_SCAN_FLAG_REFS: Final[tuple[str, ...]] = (
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

P7_R54_AHR09_FORM_FROZEN_STATUS_REF: Final = "AHR_REVIEWER_SELECTION_FORM_FROZEN_BODYFREE_READY"
P7_R54_AHR09_FORM_BLOCKED_STATUS_REF: Final = "AHR_REVIEWER_SELECTION_FORM_BLOCKED_BY_PACKET_SCAN"
P7_R54_AHR09_ALLOWED_FORM_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR09_FORM_FROZEN_STATUS_REF,
    P7_R54_AHR09_FORM_BLOCKED_STATUS_REF,
)
P7_R54_AHR09_READY_REASON_REF: Final = "r54_ahr_reviewer_selection_form_frozen_bodyfree"
P7_R54_AHR09_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-09_repair_reviewer_selection_form_before_actual_human_review_operation"
)
P7_R54_AHR09_SCORE_OPTION_REFS: Final[tuple[float, ...]] = (0.0, 0.25, 0.5, 0.75, 1.0)
P7_R54_AHR09_VERDICT_OPTION_REFS: Final[tuple[str, ...]] = (
    "PASS",
    "YELLOW",
    "REPAIR_REQUIRED",
    "RED",
    "BLOCKED",
    "NOT_REVIEWABLE",
)
P7_R54_AHR09_SANITIZED_REASON_ID_OPTION_REFS: Final[tuple[str, ...]] = (
    "record_returned_as_natural_line",
    "history_line_weak_or_generic",
    "history_line_overread_or_creepy",
    "current_input_overridden_by_history",
    "boundary_history_correctly_not_used",
    "low_information_correctly_not_deep_read",
    "free_tier_history_correctly_not_used",
    "question_may_reduce_overread_risk_later",
    "p5_surface_repair_required",
    "p4_current_surface_repair_required",
    "execution_blocker_present",
)
P7_R54_AHR09_READFEEL_BLOCKER_ID_OPTION_REFS: Final[tuple[str, ...]] = (
    "history_connection_weak",
    "history_line_creepy_or_overread",
    "current_input_overridden_by_history",
    "overclaim_or_unearned_certainty",
    "self_blame_amplified",
    "shallow_repeat_or_generic",
    "wants_less_input_or_no_accumulation",
    "boundary_history_line_leak",
)
P7_R54_AHR09_EXECUTION_BLOCKER_ID_OPTION_REFS: Final[tuple[str, ...]] = (
    "packet_missing",
    "packet_not_local_only",
    "case_manifest_incomplete",
    "reviewer_selection_incomplete",
    "forbidden_body_leak",
    "question_text_leak",
    "disposal_missing",
    "no_touch_violation",
)
P7_R54_AHR09_QUESTION_NEED_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = (
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
P7_R54_AHR09_AMBIGUITY_KIND_OPTION_REFS: Final[tuple[str, ...]] = (
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
P7_R54_AHR09_ONE_QUESTION_FIT_OPTION_REFS: Final[tuple[str, ...]] = (
    "not_needed",
    "fits_one_question",
    "needs_more_than_one_question_not_p7",
    "would_delay_immediate_observation",
    "unsafe_or_boundary_not_question",
    "repair_required_not_question",
    "insufficient_material",
)
P7_R54_AHR09_REPAIR_REQUIRED_OPTION_REFS: Final[tuple[str, ...]] = (
    "no_repair_required",
    "emlis_readfeel_repair_required",
    "p5_surface_repair_required",
    "gate_boundary_repair_required",
    "p4_current_surface_repair_required",
)
P7_R54_AHR09_PLAN_CANDIDATE_FLAG_REFS: Final[tuple[str, ...]] = (
    "plus_single_question_candidate_later",
    "premium_deep_dive_candidate_later",
    "p8_design_material_candidate",
    "p8_implementation_spec_finalized_here",
)

P7_R54_AHR08_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_BASE_REQUIRED_FIELD_REFS,
    "ahr07_schema_version",
    "ahr07_material_ref",
    "ahr07_next_required_step",
    "ahr07_receipt_status",
    "ahr07_generation_status_ref",
    "ahr07_packet_completeness_export_denylist_scan_allowed_next",
    "ahr07_required_case_count",
    "ahr07_generated_case_count",
    "ahr07_generated_packet_count",
    "ahr07_local_packet_exported",
    "ahr07_exported",
    "ahr07_packet_ref_ids",
    "ahr07_packet_ref_id_count",
    *P7_R54_AHR_CURRENT_EXECUTION_BASIS_FIELD_REFS,
    "operation_current_refs_match_current_execution_basis_260_83_256_169",
    "current_execution_basis_refs_match_received_snapshot_260_83_256_169",
    "current_execution_basis_refs_match_260_83_256_169_snapshot",
    "scan_status",
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
    "forbidden_key_scan_passed",
    "packet_completeness_export_denylist_scan_completed",
    "packet_completeness_export_denylist_scan_bodyfree_evidence_only",
    "packet_content_not_included_in_scan_evidence",
    "local_absolute_path_not_included_in_scan_evidence",
    "body_hash_not_included_in_scan_evidence",
    "terminal_output_not_included_in_scan_evidence",
    "reviewer_selection_form_freeze_allowed_next",
    "actual_review_execution_blocked_until_selection_form_freeze",
    "actual_human_review_run_here",
    "actual_review_execution_allowed_next",
    "human_review_completion_claim_blocked_here",
    "actual_review_completion_claim_blocked_here",
    "actual_human_review_completion_claim_blocked_here",
    "actual_rating_or_question_rows_claim_blocked_here",
    "disposal_receipt_claim_blocked_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    *P7_R54_AHR08_FORBIDDEN_SCAN_FLAG_REFS,
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "r54_ahr_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R54_AHR_FALSE_FLAG_REFS,
)

P7_R54_AHR09_REVIEWER_SELECTION_FORM_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_BASE_REQUIRED_FIELD_REFS,
    "ahr08_schema_version",
    "ahr08_material_ref",
    "ahr08_next_required_step",
    "ahr08_scan_status",
    "ahr08_packet_completeness_passed",
    "ahr08_export_denylist_scan_passed",
    "ahr08_forbidden_key_scan_passed",
    "ahr08_reviewer_selection_form_freeze_allowed_next",
    *P7_R54_AHR_CURRENT_EXECUTION_BASIS_FIELD_REFS,
    "operation_current_refs_match_current_execution_basis_260_83_256_169",
    "current_execution_basis_refs_match_received_snapshot_260_83_256_169",
    "current_execution_basis_refs_match_260_83_256_169_snapshot",
    "selection_form_status",
    "selection_form_status_ref",
    "selection_form_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "packet_scan_ready_for_form_freeze",
    "selection_only",
    "selection_only_form",
    "selection_form_structure_frozen",
    "selection_form_bodyfree_only",
    "free_text_export_allowed",
    "reviewer_free_text_field_present",
    "reviewer_free_text_export_allowed",
    "reviewer_free_text_field_exported_to_bodyfree_evidence",
    "free_text_note_field_exported_to_bodyfree_evidence",
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
    "reviewer_facing_family_exposed",
    "reviewer_facing_tier_exposed",
    "local_only",
    "must_not_export",
    "body_full_packet_content_available_to_local_reviewer_only",
    "body_full_packet_content_included",
    "packet_content_included",
    "local_absolute_path_included",
    "body_hash_included",
    "question_text_included",
    "draft_question_text_included",
    "reviewer_selection_form_file_materialized_here",
    "local_reviewer_payload_materialized_here",
    "actual_human_review_local_only_operation_allowed_next",
    "actual_review_execution_allowed_here",
    "actual_review_execution_allowed_next",
    "actual_human_review_run_here",
    "sanitized_review_result_rows_materialized_here",
    "rating_rows_materialized_here",
    "question_need_observation_rows_materialized_here",
    "disposal_receipt_materialized_here",
    "p8_implementation_spec_finalized_here",
    "human_review_completion_claim_blocked_here",
    "actual_review_completion_claim_blocked_here",
    "actual_human_review_completion_claim_blocked_here",
    "actual_rating_or_question_rows_claim_blocked_here",
    "disposal_receipt_claim_blocked_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "r54_ahr_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R54_AHR_FALSE_FLAG_REFS,
)


def _evaluate_ahr08_packet_completeness_scan(
    *,
    receipt: Mapping[str, Any],
    scanned_case_count: int,
    scanned_packet_count: int,
    local_only: bool,
    must_not_export: bool,
    exported: bool,
    local_packet_exported: bool,
    forbidden_key_findings: Sequence[Any] | None,
) -> tuple[str, list[str], list[str]]:
    blockers: list[str] = []
    if receipt.get("receipt_status") != P7_R54_AHR07_RECEIPT_READY_STATUS_REF:
        blockers.append("ahr07_packet_generation_receipt_not_ready")
    if receipt.get("packet_completeness_export_denylist_scan_allowed_next") is not True:
        blockers.append("ahr07_packet_scan_not_allowed_next")
    if scanned_case_count != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("scanned_case_count_not_24")
    if scanned_packet_count != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("scanned_packet_count_not_24")
    if local_only is not True:
        blockers.append("local_only_not_confirmed")
    if must_not_export is not True:
        blockers.append("must_not_export_not_confirmed")
    if exported is True:
        blockers.append("scan_marked_exported")
    if local_packet_exported is True:
        blockers.append("local_packet_exported")
    finding_refs = dedupe_identifiers(forbidden_key_findings or (), limit=40, max_length=180)
    if finding_refs:
        blockers.extend(f"forbidden_key_found:{ref}" for ref in finding_refs)
    blockers = dedupe_identifiers(blockers, limit=80, max_length=220)
    if blockers:
        return P7_R54_AHR08_SCAN_BLOCKED_STATUS_REF, blockers, blockers
    return P7_R54_AHR08_SCAN_PASSED_STATUS_REF, [P7_R54_AHR08_READY_REASON_REF], []


def build_p7_r54_ahr08_packet_completeness_export_denylist_scan(
    *,
    local_packet_generation_receipt: Mapping[str, Any] | None = None,
    scanned_case_count: int | None = None,
    scanned_packet_count: int | None = None,
    local_only: bool = True,
    must_not_export: bool = True,
    exported: bool = False,
    local_packet_exported: bool = False,
    forbidden_key_findings: Sequence[Any] | None = None,
    review_session_id: Any = P7_R54_AHR_DEFAULT_REVIEW_SESSION_ID,
) -> dict[str, Any]:
    """Build R54-AHR-08 packet completeness / export denylist scan evidence."""

    receipt = dict(local_packet_generation_receipt or build_p7_r54_ahr07_local_packet_generation_operation_receipt_intake())
    packet_refs = dedupe_identifiers(receipt.get("ahr06_packet_ref_ids") or (), limit=80, max_length=160)
    expected_count = P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
    case_count = int(scanned_case_count if scanned_case_count is not None else receipt.get("generated_case_count") or 0)
    packet_count = int(scanned_packet_count if scanned_packet_count is not None else receipt.get("generated_packet_count") or 0)
    finding_refs = dedupe_identifiers(forbidden_key_findings or (), limit=40, max_length=180)
    status, reason_refs, blockers = _evaluate_ahr08_packet_completeness_scan(
        receipt=receipt,
        scanned_case_count=case_count,
        scanned_packet_count=packet_count,
        local_only=local_only,
        must_not_export=must_not_export,
        exported=exported,
        local_packet_exported=local_packet_exported,
        forbidden_key_findings=finding_refs,
    )
    ready = status == P7_R54_AHR08_SCAN_PASSED_STATUS_REF
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR08_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_STEP,
        "scope": P7_R54_AHR_SCOPE,
        "policy_kind": P7_R54_AHR_POLICY_KIND,
        "policy_section": P7_R54_AHR08_STEP_REF,
        "operation_step_ref": P7_R54_AHR08_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr08_packet_completeness_export_denylist_scan_20260627",
        "review_session_id": _safe_review_session_id(review_session_id),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ahr07_schema_version": receipt.get("schema_version"),
        "ahr07_material_ref": receipt.get("material_id", "p7_r54_ahr07_local_packet_generation_operation_receipt_intake_20260627"),
        "ahr07_next_required_step": receipt.get("next_required_step"),
        "ahr07_receipt_status": receipt.get("receipt_status"),
        "ahr07_generation_status_ref": receipt.get("generation_status_ref"),
        "ahr07_packet_completeness_export_denylist_scan_allowed_next": receipt.get(
            "packet_completeness_export_denylist_scan_allowed_next"
        ),
        "ahr07_required_case_count": receipt.get("required_case_count"),
        "ahr07_generated_case_count": receipt.get("generated_case_count"),
        "ahr07_generated_packet_count": receipt.get("generated_packet_count"),
        "ahr07_local_packet_exported": receipt.get("local_packet_exported"),
        "ahr07_exported": receipt.get("exported"),
        "ahr07_packet_ref_ids": list(packet_refs),
        "ahr07_packet_ref_id_count": len(packet_refs),
        **_current_execution_basis_material_fields(actual_basis=True),
        "operation_current_refs_match_current_execution_basis_260_83_256_169": True,
        "current_execution_basis_refs_match_received_snapshot_260_83_256_169": True,
        "current_execution_basis_refs_match_260_83_256_169_snapshot": True,
        "scan_status": status,
        "scan_status_ref": status,
        "scan_reason_refs": list(reason_refs),
        "execution_blocker_ids": list(blockers),
        "open_execution_blocker_ids": list(blockers),
        "receipt_ready_for_packet_scan": receipt.get("receipt_status") == P7_R54_AHR07_RECEIPT_READY_STATUS_REF,
        "local_only": local_only,
        "must_not_export": must_not_export,
        "exported": exported,
        "local_packet_exported": local_packet_exported,
        "required_case_count": expected_count,
        "expected_packet_count": expected_count,
        "scanned_case_count": case_count,
        "scanned_packet_count": packet_count,
        "scanned_packet_ref_ids": list(packet_refs) if ready else [],
        "scanned_packet_ref_id_count": len(packet_refs) if ready else 0,
        "scanned_packet_refs_unique": len(packet_refs) == len(set(packet_refs)) if ready else False,
        "packet_count_complete": ready,
        "packet_completeness_passed": ready,
        "packet_completeness_bodyfree_only": ready,
        "export_denylist_scan_target_refs": list(P7_R54_AHR08_SCAN_TARGET_REFS),
        "export_denylist_scan_target_count": len(P7_R54_AHR08_SCAN_TARGET_REFS),
        "export_denylist_refs": list(P7_R54_AHR04_EXPORT_DENYLIST_REFS),
        "export_denylist_ref_count": len(P7_R54_AHR04_EXPORT_DENYLIST_REFS),
        "export_denylist_scan_passed": ready,
        "forbidden_output_refs": list(P7_R54_AHR04_FORBIDDEN_OUTPUT_REFS),
        "forbidden_output_ref_count": len(P7_R54_AHR04_FORBIDDEN_OUTPUT_REFS),
        "forbidden_key_findings": list(finding_refs),
        "forbidden_key_findings_count": len(finding_refs),
        "forbidden_key_scan_passed": ready,
        "packet_completeness_export_denylist_scan_completed": ready,
        "packet_completeness_export_denylist_scan_bodyfree_evidence_only": ready,
        "packet_content_not_included_in_scan_evidence": True,
        "local_absolute_path_not_included_in_scan_evidence": True,
        "body_hash_not_included_in_scan_evidence": True,
        "terminal_output_not_included_in_scan_evidence": True,
        "reviewer_selection_form_freeze_allowed_next": ready,
        "actual_review_execution_blocked_until_selection_form_freeze": True,
        "actual_human_review_run_here": False,
        "actual_review_execution_allowed_next": False,
        "human_review_completion_claim_blocked_here": True,
        "actual_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_rating_or_question_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        **{key: False for key in P7_R54_AHR08_FORBIDDEN_SCAN_FLAG_REFS},
        "implemented_steps": list(P7_R54_AHR08_IMPLEMENTED_STEPS if ready else P7_R54_AHR07_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR08_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR07_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR09_STEP_REF if ready else P7_R54_AHR08_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_ahr08_packet_completeness_export_denylist_scan_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR08_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR08 packet completeness / export denylist scan",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR08_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION,
        policy_section=P7_R54_AHR08_STEP_REF,
        operation_step_ref=P7_R54_AHR08_STEP_REF,
        source="P7-R54-AHR08 packet completeness / export denylist scan",
    )
    _assert_current_execution_basis_refs(data, source="P7-R54-AHR08 packet completeness / export denylist scan", actual_basis=True)
    if data.get("ahr07_schema_version") != P7_R54_AHR07_LOCAL_PACKET_GENERATION_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR08 must follow AHR07 receipt intake")
    if data.get("ahr07_receipt_status") == P7_R54_AHR07_RECEIPT_READY_STATUS_REF:
        if data.get("ahr07_next_required_step") != P7_R54_AHR08_STEP_REF:
            raise ValueError("P7-R54-AHR08 must follow AHR07 next step")
    elif data.get("ahr07_next_required_step") != P7_R54_AHR07_BLOCKED_NEXT_REQUIRED_STEP_REF:
        raise ValueError("P7-R54-AHR08 blocked predecessor must preserve AHR07 repair next step")
    if data.get("scan_status") not in P7_R54_AHR08_ALLOWED_SCAN_STATUS_REFS:
        raise ValueError("P7-R54-AHR08 scan status changed")
    if data.get("scan_status_ref") != data.get("scan_status"):
        raise ValueError("P7-R54-AHR08 scan status alias changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or (), limit=80, max_length=220)
    if blockers != dedupe_identifiers(data.get("open_execution_blocker_ids") or (), limit=80, max_length=220):
        raise ValueError("P7-R54-AHR08 open blockers must match blockers")
    if data.get("required_case_count") != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-AHR08 required case count changed")
    if data.get("expected_packet_count") != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-AHR08 expected packet count changed")
    if tuple(data.get("export_denylist_scan_target_refs") or ()) != P7_R54_AHR08_SCAN_TARGET_REFS:
        raise ValueError("P7-R54-AHR08 scan targets changed")
    if data.get("export_denylist_scan_target_count") != len(P7_R54_AHR08_SCAN_TARGET_REFS):
        raise ValueError("P7-R54-AHR08 scan target count changed")
    if tuple(data.get("export_denylist_refs") or ()) != P7_R54_AHR04_EXPORT_DENYLIST_REFS:
        raise ValueError("P7-R54-AHR08 export denylist refs changed")
    if data.get("export_denylist_ref_count") != len(P7_R54_AHR04_EXPORT_DENYLIST_REFS):
        raise ValueError("P7-R54-AHR08 export denylist count changed")
    if tuple(data.get("forbidden_output_refs") or ()) != P7_R54_AHR04_FORBIDDEN_OUTPUT_REFS:
        raise ValueError("P7-R54-AHR08 forbidden output refs changed")
    if data.get("forbidden_output_ref_count") != len(P7_R54_AHR04_FORBIDDEN_OUTPUT_REFS):
        raise ValueError("P7-R54-AHR08 forbidden output count changed")
    if data.get("forbidden_key_findings_count") != len(data.get("forbidden_key_findings") or []):
        raise ValueError("P7-R54-AHR08 finding count changed")
    for key in P7_R54_AHR08_FORBIDDEN_SCAN_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR08 must keep forbidden scan flag {key}=False")
    for key in (
        "packet_content_not_included_in_scan_evidence",
        "local_absolute_path_not_included_in_scan_evidence",
        "body_hash_not_included_in_scan_evidence",
        "terminal_output_not_included_in_scan_evidence",
        "actual_review_execution_blocked_until_selection_form_freeze",
        "human_review_completion_claim_blocked_here",
        "actual_review_completion_claim_blocked_here",
        "actual_human_review_completion_claim_blocked_here",
        "actual_rating_or_question_rows_claim_blocked_here",
        "disposal_receipt_claim_blocked_here",
        "r52_reintake_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR08 must keep {key}=True")
    ready = data.get("scan_status") == P7_R54_AHR08_SCAN_PASSED_STATUS_REF
    if ready:
        if blockers:
            raise ValueError("P7-R54-AHR08 passed scan must not carry blockers")
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
            "reviewer_selection_form_freeze_allowed_next",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR08 passed scan must keep {key}=True")
        for key in ("exported", "local_packet_exported", "actual_human_review_run_here", "actual_review_execution_allowed_next"):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR08 passed scan must keep {key}=False")
        if data.get("scanned_case_count") != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR08 scanned case count changed")
        if data.get("scanned_packet_count") != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR08 scanned packet count changed")
        if data.get("scanned_packet_ref_id_count") != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR08 packet ref count changed")
        if len(set(data.get("scanned_packet_ref_ids") or [])) != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR08 packet refs must remain unique")
        if data.get("scan_reason_refs") != [P7_R54_AHR08_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR08 ready reason changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR08_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR08 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR08_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR08 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR09_STEP_REF:
            raise ValueError("P7-R54-AHR08 next step changed")
    else:
        if data.get("scan_status") != P7_R54_AHR08_SCAN_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR08 blocked scan status changed")
        if not blockers:
            raise ValueError("P7-R54-AHR08 blocked scan must carry blockers")
        for key in (
            "packet_count_complete",
            "packet_completeness_passed",
            "packet_completeness_bodyfree_only",
            "export_denylist_scan_passed",
            "forbidden_key_scan_passed",
            "packet_completeness_export_denylist_scan_completed",
            "packet_completeness_export_denylist_scan_bodyfree_evidence_only",
            "reviewer_selection_form_freeze_allowed_next",
        ):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR08 blocked scan must keep {key}=False")
        if data.get("next_required_step") != P7_R54_AHR08_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR08 blocked next step changed")
    return True


def _evaluate_ahr09_reviewer_selection_form(
    *,
    packet_scan: Mapping[str, Any],
    selection_only: bool,
    free_text_export_allowed: bool,
    reviewer_free_text_field_present: bool,
    question_text_input_allowed: bool,
    draft_question_text_input_allowed: bool,
    raw_body_copy_field_present: bool,
    history_surface_copy_field_present: bool,
    local_path_field_present: bool,
    body_hash_field_present: bool,
    packet_content_copy_field_present: bool,
) -> tuple[str, list[str], list[str]]:
    blockers: list[str] = []
    if packet_scan.get("scan_status") != P7_R54_AHR08_SCAN_PASSED_STATUS_REF:
        blockers.append("ahr08_packet_completeness_scan_not_passed")
    if packet_scan.get("reviewer_selection_form_freeze_allowed_next") is not True:
        blockers.append("ahr08_reviewer_selection_form_freeze_not_allowed")
    if selection_only is not True:
        blockers.append("selection_only_not_confirmed")
    if free_text_export_allowed is True:
        blockers.append("free_text_export_allowed")
    if reviewer_free_text_field_present is True:
        blockers.append("reviewer_free_text_field_present")
    if question_text_input_allowed is True:
        blockers.append("question_text_input_allowed")
    if draft_question_text_input_allowed is True:
        blockers.append("draft_question_text_input_allowed")
    if raw_body_copy_field_present is True:
        blockers.append("raw_body_copy_field_present")
    if history_surface_copy_field_present is True:
        blockers.append("history_surface_copy_field_present")
    if local_path_field_present is True:
        blockers.append("local_path_field_present")
    if body_hash_field_present is True:
        blockers.append("body_hash_field_present")
    if packet_content_copy_field_present is True:
        blockers.append("packet_content_copy_field_present")
    blockers = dedupe_identifiers(blockers, limit=80, max_length=220)
    if blockers:
        return P7_R54_AHR09_FORM_BLOCKED_STATUS_REF, blockers, blockers
    return P7_R54_AHR09_FORM_FROZEN_STATUS_REF, [P7_R54_AHR09_READY_REASON_REF], []


def build_p7_r54_ahr09_reviewer_selection_form_freeze(
    *,
    packet_completeness_scan: Mapping[str, Any] | None = None,
    selection_only: bool = True,
    free_text_export_allowed: bool = False,
    reviewer_free_text_field_present: bool = False,
    question_text_input_allowed: bool = False,
    draft_question_text_input_allowed: bool = False,
    raw_body_copy_field_present: bool = False,
    history_surface_copy_field_present: bool = False,
    local_path_field_present: bool = False,
    body_hash_field_present: bool = False,
    packet_content_copy_field_present: bool = False,
    review_session_id: Any = P7_R54_AHR_DEFAULT_REVIEW_SESSION_ID,
) -> dict[str, Any]:
    """Build R54-AHR-09 reviewer selection-only form freeze evidence."""

    scan = dict(packet_completeness_scan or build_p7_r54_ahr08_packet_completeness_export_denylist_scan())
    status, reason_refs, blockers = _evaluate_ahr09_reviewer_selection_form(
        packet_scan=scan,
        selection_only=selection_only,
        free_text_export_allowed=free_text_export_allowed,
        reviewer_free_text_field_present=reviewer_free_text_field_present,
        question_text_input_allowed=question_text_input_allowed,
        draft_question_text_input_allowed=draft_question_text_input_allowed,
        raw_body_copy_field_present=raw_body_copy_field_present,
        history_surface_copy_field_present=history_surface_copy_field_present,
        local_path_field_present=local_path_field_present,
        body_hash_field_present=body_hash_field_present,
        packet_content_copy_field_present=packet_content_copy_field_present,
    )
    ready = status == P7_R54_AHR09_FORM_FROZEN_STATUS_REF
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR09_REVIEWER_SELECTION_FORM_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_STEP,
        "scope": P7_R54_AHR_SCOPE,
        "policy_kind": P7_R54_AHR_POLICY_KIND,
        "policy_section": P7_R54_AHR09_STEP_REF,
        "operation_step_ref": P7_R54_AHR09_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr09_reviewer_selection_form_freeze_20260627",
        "review_session_id": _safe_review_session_id(review_session_id),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ahr08_schema_version": scan.get("schema_version"),
        "ahr08_material_ref": scan.get("material_id", "p7_r54_ahr08_packet_completeness_export_denylist_scan_20260627"),
        "ahr08_next_required_step": scan.get("next_required_step"),
        "ahr08_scan_status": scan.get("scan_status"),
        "ahr08_packet_completeness_passed": scan.get("packet_completeness_passed"),
        "ahr08_export_denylist_scan_passed": scan.get("export_denylist_scan_passed"),
        "ahr08_forbidden_key_scan_passed": scan.get("forbidden_key_scan_passed"),
        "ahr08_reviewer_selection_form_freeze_allowed_next": scan.get("reviewer_selection_form_freeze_allowed_next"),
        **_current_execution_basis_material_fields(actual_basis=True),
        "operation_current_refs_match_current_execution_basis_260_83_256_169": True,
        "current_execution_basis_refs_match_received_snapshot_260_83_256_169": True,
        "current_execution_basis_refs_match_260_83_256_169_snapshot": True,
        "selection_form_status": status,
        "selection_form_status_ref": status,
        "selection_form_reason_refs": list(reason_refs),
        "execution_blocker_ids": list(blockers),
        "open_execution_blocker_ids": list(blockers),
        "packet_scan_ready_for_form_freeze": scan.get("scan_status") == P7_R54_AHR08_SCAN_PASSED_STATUS_REF,
        "selection_only": selection_only,
        "selection_only_form": ready,
        "selection_form_structure_frozen": ready,
        "selection_form_bodyfree_only": ready,
        "free_text_export_allowed": False,
        "reviewer_free_text_field_present": False,
        "reviewer_free_text_export_allowed": False,
        "reviewer_free_text_field_exported_to_bodyfree_evidence": False,
        "free_text_note_field_exported_to_bodyfree_evidence": False,
        "question_text_input_allowed": False,
        "draft_question_text_input_allowed": False,
        "question_text_or_draft_text_field_present": False,
        "raw_body_copy_field_present": False,
        "history_surface_copy_field_present": False,
        "raw_body_copy_field_allowed": False,
        "history_surface_copy_field_allowed": False,
        "local_path_field_present": False,
        "body_hash_field_present": False,
        "packet_content_copy_field_present": False,
        "rating_axis_refs": list(P7_R54_AHR05_RATING_AXIS_REFS) if ready else [],
        "rating_axis_count": len(P7_R54_AHR05_RATING_AXIS_REFS) if ready else 0,
        "rating_axis_target_thresholds": dict(P7_R54_AHR05_RATING_AXIS_TARGET_THRESHOLDS) if ready else {},
        "score_option_refs": list(P7_R54_AHR09_SCORE_OPTION_REFS) if ready else [],
        "score_option_count": len(P7_R54_AHR09_SCORE_OPTION_REFS) if ready else 0,
        "verdict_option_refs": list(P7_R54_AHR09_VERDICT_OPTION_REFS) if ready else [],
        "verdict_option_count": len(P7_R54_AHR09_VERDICT_OPTION_REFS) if ready else 0,
        "sanitized_reason_id_option_refs": list(P7_R54_AHR09_SANITIZED_REASON_ID_OPTION_REFS) if ready else [],
        "sanitized_reason_id_option_count": len(P7_R54_AHR09_SANITIZED_REASON_ID_OPTION_REFS) if ready else 0,
        "readfeel_blocker_id_option_refs": list(P7_R54_AHR09_READFEEL_BLOCKER_ID_OPTION_REFS) if ready else [],
        "readfeel_blocker_id_option_count": len(P7_R54_AHR09_READFEEL_BLOCKER_ID_OPTION_REFS) if ready else 0,
        "execution_blocker_id_option_refs": list(P7_R54_AHR09_EXECUTION_BLOCKER_ID_OPTION_REFS) if ready else [],
        "execution_blocker_id_option_count": len(P7_R54_AHR09_EXECUTION_BLOCKER_ID_OPTION_REFS) if ready else 0,
        "question_need_primary_class_options": list(P7_R54_AHR09_QUESTION_NEED_PRIMARY_CLASS_REFS) if ready else [],
        "question_need_primary_class_option_count": len(P7_R54_AHR09_QUESTION_NEED_PRIMARY_CLASS_REFS) if ready else 0,
        "ambiguity_kind_option_refs": list(P7_R54_AHR09_AMBIGUITY_KIND_OPTION_REFS) if ready else [],
        "ambiguity_kind_option_count": len(P7_R54_AHR09_AMBIGUITY_KIND_OPTION_REFS) if ready else 0,
        "one_question_fit_option_refs": list(P7_R54_AHR09_ONE_QUESTION_FIT_OPTION_REFS) if ready else [],
        "one_question_fit_option_count": len(P7_R54_AHR09_ONE_QUESTION_FIT_OPTION_REFS) if ready else 0,
        "repair_required_option_refs": list(P7_R54_AHR09_REPAIR_REQUIRED_OPTION_REFS) if ready else [],
        "repair_required_option_count": len(P7_R54_AHR09_REPAIR_REQUIRED_OPTION_REFS) if ready else 0,
        "plan_candidate_flag_refs": list(P7_R54_AHR09_PLAN_CANDIDATE_FLAG_REFS) if ready else [],
        "plan_candidate_flag_count": len(P7_R54_AHR09_PLAN_CANDIDATE_FLAG_REFS) if ready else 0,
        "reviewer_facing_family_exposed": False,
        "reviewer_facing_tier_exposed": False,
        "local_only": True,
        "must_not_export": True,
        "body_full_packet_content_available_to_local_reviewer_only": True,
        "body_full_packet_content_included": False,
        "packet_content_included": False,
        "local_absolute_path_included": False,
        "body_hash_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "reviewer_selection_form_file_materialized_here": False,
        "local_reviewer_payload_materialized_here": False,
        "actual_human_review_local_only_operation_allowed_next": ready,
        "actual_review_execution_allowed_here": False,
        "actual_review_execution_allowed_next": False,
        "actual_human_review_run_here": False,
        "sanitized_review_result_rows_materialized_here": False,
        "rating_rows_materialized_here": False,
        "question_need_observation_rows_materialized_here": False,
        "disposal_receipt_materialized_here": False,
        "p8_implementation_spec_finalized_here": False,
        "human_review_completion_claim_blocked_here": True,
        "actual_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_rating_or_question_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR09_IMPLEMENTED_STEPS if ready else P7_R54_AHR08_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR09_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR08_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR10_STEP_REF if ready else P7_R54_AHR09_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_ahr09_reviewer_selection_form_freeze_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR09_REVIEWER_SELECTION_FORM_FREEZE_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR09 reviewer selection form freeze",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR09_REVIEWER_SELECTION_FORM_FREEZE_SCHEMA_VERSION,
        policy_section=P7_R54_AHR09_STEP_REF,
        operation_step_ref=P7_R54_AHR09_STEP_REF,
        source="P7-R54-AHR09 reviewer selection form freeze",
    )
    _assert_current_execution_basis_refs(data, source="P7-R54-AHR09 reviewer selection form freeze", actual_basis=True)
    if data.get("ahr08_schema_version") != P7_R54_AHR08_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR09 must follow AHR08 packet scan")
    if data.get("ahr08_scan_status") == P7_R54_AHR08_SCAN_PASSED_STATUS_REF:
        if data.get("ahr08_next_required_step") != P7_R54_AHR09_STEP_REF:
            raise ValueError("P7-R54-AHR09 must follow AHR08 next step")
    elif data.get("ahr08_next_required_step") != P7_R54_AHR08_BLOCKED_NEXT_REQUIRED_STEP_REF:
        raise ValueError("P7-R54-AHR09 blocked predecessor must preserve AHR08 repair next step")
    if data.get("selection_form_status") not in P7_R54_AHR09_ALLOWED_FORM_STATUS_REFS:
        raise ValueError("P7-R54-AHR09 form status changed")
    if data.get("selection_form_status_ref") != data.get("selection_form_status"):
        raise ValueError("P7-R54-AHR09 form status alias changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or (), limit=80, max_length=220)
    if blockers != dedupe_identifiers(data.get("open_execution_blocker_ids") or (), limit=80, max_length=220):
        raise ValueError("P7-R54-AHR09 open blockers must match blockers")
    for key in (
        "free_text_export_allowed",
        "reviewer_free_text_field_present",
        "reviewer_free_text_export_allowed",
        "reviewer_free_text_field_exported_to_bodyfree_evidence",
        "free_text_note_field_exported_to_bodyfree_evidence",
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
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR09 must keep {key}=False")
    for key in (
        "local_only",
        "must_not_export",
        "body_full_packet_content_available_to_local_reviewer_only",
        "human_review_completion_claim_blocked_here",
        "actual_review_completion_claim_blocked_here",
        "actual_human_review_completion_claim_blocked_here",
        "actual_rating_or_question_rows_claim_blocked_here",
        "disposal_receipt_claim_blocked_here",
        "r52_reintake_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR09 must keep {key}=True")
    ready = data.get("selection_form_status") == P7_R54_AHR09_FORM_FROZEN_STATUS_REF
    if ready:
        if blockers:
            raise ValueError("P7-R54-AHR09 frozen form must not carry blockers")
        for key in (
            "packet_scan_ready_for_form_freeze",
            "selection_only",
            "selection_only_form",
            "selection_form_structure_frozen",
            "selection_form_bodyfree_only",
            "actual_human_review_local_only_operation_allowed_next",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR09 frozen form must keep {key}=True")
        expected_options: tuple[tuple[str, Sequence[Any] | Mapping[str, Any], str], ...] = (
            ("rating_axis_refs", P7_R54_AHR05_RATING_AXIS_REFS, "rating axes"),
            ("score_option_refs", P7_R54_AHR09_SCORE_OPTION_REFS, "score options"),
            ("verdict_option_refs", P7_R54_AHR09_VERDICT_OPTION_REFS, "verdict options"),
            ("sanitized_reason_id_option_refs", P7_R54_AHR09_SANITIZED_REASON_ID_OPTION_REFS, "reason options"),
            ("readfeel_blocker_id_option_refs", P7_R54_AHR09_READFEEL_BLOCKER_ID_OPTION_REFS, "readfeel blocker options"),
            ("execution_blocker_id_option_refs", P7_R54_AHR09_EXECUTION_BLOCKER_ID_OPTION_REFS, "execution blocker options"),
            ("question_need_primary_class_options", P7_R54_AHR09_QUESTION_NEED_PRIMARY_CLASS_REFS, "question class options"),
            ("ambiguity_kind_option_refs", P7_R54_AHR09_AMBIGUITY_KIND_OPTION_REFS, "ambiguity options"),
            ("one_question_fit_option_refs", P7_R54_AHR09_ONE_QUESTION_FIT_OPTION_REFS, "one question fit options"),
            ("repair_required_option_refs", P7_R54_AHR09_REPAIR_REQUIRED_OPTION_REFS, "repair options"),
            ("plan_candidate_flag_refs", P7_R54_AHR09_PLAN_CANDIDATE_FLAG_REFS, "plan flags"),
        )
        for field, expected, label in expected_options:
            if list(data.get(field) or []) != list(expected):
                raise ValueError(f"P7-R54-AHR09 {label} changed")
        if safe_mapping(data.get("rating_axis_target_thresholds")) != P7_R54_AHR05_RATING_AXIS_TARGET_THRESHOLDS:
            raise ValueError("P7-R54-AHR09 rating axis thresholds changed")
        expected_counts = (
            ("rating_axis_count", len(P7_R54_AHR05_RATING_AXIS_REFS)),
            ("score_option_count", len(P7_R54_AHR09_SCORE_OPTION_REFS)),
            ("verdict_option_count", len(P7_R54_AHR09_VERDICT_OPTION_REFS)),
            ("sanitized_reason_id_option_count", len(P7_R54_AHR09_SANITIZED_REASON_ID_OPTION_REFS)),
            ("readfeel_blocker_id_option_count", len(P7_R54_AHR09_READFEEL_BLOCKER_ID_OPTION_REFS)),
            ("execution_blocker_id_option_count", len(P7_R54_AHR09_EXECUTION_BLOCKER_ID_OPTION_REFS)),
            ("question_need_primary_class_option_count", len(P7_R54_AHR09_QUESTION_NEED_PRIMARY_CLASS_REFS)),
            ("ambiguity_kind_option_count", len(P7_R54_AHR09_AMBIGUITY_KIND_OPTION_REFS)),
            ("one_question_fit_option_count", len(P7_R54_AHR09_ONE_QUESTION_FIT_OPTION_REFS)),
            ("repair_required_option_count", len(P7_R54_AHR09_REPAIR_REQUIRED_OPTION_REFS)),
            ("plan_candidate_flag_count", len(P7_R54_AHR09_PLAN_CANDIDATE_FLAG_REFS)),
        )
        for field, expected in expected_counts:
            if data.get(field) != expected:
                raise ValueError(f"P7-R54-AHR09 {field} changed")
        if data.get("selection_form_reason_refs") != [P7_R54_AHR09_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR09 ready reason changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR09_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR09 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR09_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR09 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR10_STEP_REF:
            raise ValueError("P7-R54-AHR09 next step changed")
    else:
        if data.get("selection_form_status") != P7_R54_AHR09_FORM_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR09 blocked form status changed")
        if not blockers:
            raise ValueError("P7-R54-AHR09 blocked form must carry blockers")
        for key in (
            "selection_only_form",
            "selection_form_structure_frozen",
            "selection_form_bodyfree_only",
            "actual_human_review_local_only_operation_allowed_next",
        ):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR09 blocked form must keep {key}=False")
        if data.get("next_required_step") != P7_R54_AHR09_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR09 blocked next step changed")
    return True


build_p7_r54_ahr08_packet_completeness_export_denylist_scan_bodyfree = (
    build_p7_r54_ahr08_packet_completeness_export_denylist_scan
)
assert_p7_r54_ahr08_packet_completeness_export_denylist_scan_bodyfree_contract = (
    assert_p7_r54_ahr08_packet_completeness_export_denylist_scan_contract
)
build_p7_r54_ahr09_reviewer_selection_form_freeze_bodyfree = build_p7_r54_ahr09_reviewer_selection_form_freeze
assert_p7_r54_ahr09_reviewer_selection_form_freeze_bodyfree_contract = (
    assert_p7_r54_ahr09_reviewer_selection_form_freeze_contract
)
build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr08_packet_completeness_export_denylist_scan = (
    build_p7_r54_ahr08_packet_completeness_export_denylist_scan
)
assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr08_packet_completeness_export_denylist_scan_contract = (
    assert_p7_r54_ahr08_packet_completeness_export_denylist_scan_contract
)
build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr09_reviewer_selection_form_freeze = (
    build_p7_r54_ahr09_reviewer_selection_form_freeze
)
assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr09_reviewer_selection_form_freeze_contract = (
    assert_p7_r54_ahr09_reviewer_selection_form_freeze_contract
)
build_p7_r54_actual_human_review_execution_packet_completeness_export_denylist_scan_bodyfree = (
    build_p7_r54_ahr08_packet_completeness_export_denylist_scan
)
assert_p7_r54_actual_human_review_execution_packet_completeness_export_denylist_scan_bodyfree_contract = (
    assert_p7_r54_ahr08_packet_completeness_export_denylist_scan_contract
)
build_p7_r54_actual_human_review_execution_reviewer_selection_form_freeze_bodyfree = (
    build_p7_r54_ahr09_reviewer_selection_form_freeze
)
assert_p7_r54_actual_human_review_execution_reviewer_selection_form_freeze_bodyfree_contract = (
    assert_p7_r54_ahr09_reviewer_selection_form_freeze_contract
)


# ---------------------------------------------------------------------------
# R54-AHR-10 / R54-AHR-11: actual human review receipt and sanitized rows.
# ---------------------------------------------------------------------------

P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR10: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR09[1:]
P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR11: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR10[1:]
P7_R54_AHR10_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_AHR09_IMPLEMENTED_STEPS, P7_R54_AHR10_STEP_REF)
P7_R54_AHR10_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR10
P7_R54_AHR11_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_AHR10_IMPLEMENTED_STEPS, P7_R54_AHR11_STEP_REF)
P7_R54_AHR11_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR11

P7_R54_AHR_ACTUAL_HUMAN_REVIEW_LOCAL_ONLY_OPERATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.ahr10_actual_human_review_local_only_operation.bodyfree.v1"
)
P7_R54_AHR_SANITIZED_REVIEW_RESULT_ROW_INTAKE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.ahr11_sanitized_review_result_row_intake.bodyfree.v1"
)
P7_R54_AHR10_ACTUAL_HUMAN_REVIEW_LOCAL_ONLY_OPERATION_SCHEMA_VERSION: Final = (
    P7_R54_AHR_ACTUAL_HUMAN_REVIEW_LOCAL_ONLY_OPERATION_SCHEMA_VERSION
)
P7_R54_AHR11_SANITIZED_REVIEW_RESULT_ROW_INTAKE_SCHEMA_VERSION: Final = (
    P7_R54_AHR_SANITIZED_REVIEW_RESULT_ROW_INTAKE_SCHEMA_VERSION
)

P7_R54_AHR10_OPERATION_RECEIPT_INTAKEN_STATUS_REF: Final = (
    "AHR_ACTUAL_HUMAN_REVIEW_LOCAL_ONLY_OPERATION_RECEIPT_INTAKEN"
)
P7_R54_AHR10_OPERATION_BLOCKED_STATUS_REF: Final = "AHR_ACTUAL_HUMAN_REVIEW_LOCAL_ONLY_OPERATION_BLOCKED"
P7_R54_AHR10_ALLOWED_OPERATION_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR10_OPERATION_RECEIPT_INTAKEN_STATUS_REF,
    P7_R54_AHR10_OPERATION_BLOCKED_STATUS_REF,
)
P7_R54_AHR10_READY_REASON_REF: Final = "r54_ahr_actual_human_review_local_only_operation_receipt_intaken"
P7_R54_AHR10_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-10_repair_actual_human_review_operation_before_sanitized_result_intake"
)
P7_R54_AHR10_OPERATION_RECEIPT_REF: Final = "R54_AHR_ACTUAL_HUMAN_REVIEW_LOCAL_ONLY_OPERATION_RECEIPT_REF"
P7_R54_AHR10_REVIEWER_PERSON_REF_DEFAULT: Final = "reviewer_person_ref_001"
P7_R54_AHR10_REVIEW_STARTED_AT_REF_DEFAULT: Final = "review_started_at_bucket_ref"
P7_R54_AHR10_REVIEW_COMPLETED_AT_REF_DEFAULT: Final = "review_completed_at_bucket_ref"

P7_R54_AHR11_INTAKE_READY_STATUS_REF: Final = "AHR_SANITIZED_REVIEW_RESULT_ROW_INTAKE_READY"
P7_R54_AHR11_INTAKE_BLOCKED_STATUS_REF: Final = "AHR_SANITIZED_REVIEW_RESULT_ROW_INTAKE_BLOCKED"
P7_R54_AHR11_ALLOWED_INTAKE_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR11_INTAKE_READY_STATUS_REF,
    P7_R54_AHR11_INTAKE_BLOCKED_STATUS_REF,
)
P7_R54_AHR11_READY_REASON_REF: Final = "r54_ahr_sanitized_review_result_rows_intaken_bodyfree"
P7_R54_AHR11_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-11_repair_sanitized_review_result_rows_before_rating_row_normalization"
)
P7_R54_AHR11_REVIEW_RESULT_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.sanitized_review_result_row.bodyfree.v1"
)
P7_R54_AHR11_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "actual_human_review_executed_by_person",
)
P7_R54_AHR11_ROW_BODYFREE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "reviewer_free_text_included",
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

P7_R54_AHR10_ACTUAL_HUMAN_REVIEW_LOCAL_ONLY_OPERATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_BASE_REQUIRED_FIELD_REFS,
    "ahr09_schema_version",
    "ahr09_material_ref",
    "ahr09_next_required_step",
    "ahr09_selection_form_status",
    "ahr09_actual_human_review_local_only_operation_allowed_next",
    *P7_R54_AHR_CURRENT_EXECUTION_BASIS_FIELD_REFS,
    "operation_current_refs_match_current_execution_basis_260_83_256_169",
    "current_execution_basis_refs_match_received_snapshot_260_83_256_169",
    "current_execution_basis_refs_match_260_83_256_169_snapshot",
    "operation_status_ref",
    "operation_receipt_status_ref",
    "operation_receipt_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "reviewer_selection_form_ready_for_actual_review_operation",
    "operation_receipt_ref",
    "operation_receipt_ref_present",
    "operation_receipt_bodyfree_only",
    "reviewer_ref",
    "reviewer_ref_present",
    "reviewer_is_person",
    "reviewer_person_confirmed",
    "reviewer_local_only_read_receipt_present",
    "review_started_at_ref",
    "review_completed_at_ref",
    "review_time_refs_present",
    "required_case_count",
    "reviewed_case_count",
    "selection_row_count",
    "reviewed_case_count_complete",
    "selection_row_count_complete",
    "local_only",
    "must_not_export",
    "selection_only",
    "body_full_packet_read_local_only",
    "body_full_packet_content_available_to_local_reviewer_only",
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
    "packet_content_included",
    "terminal_output_body_included",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_human_review_operation_receipt_intaken_here",
    "actual_human_review_operation_complete",
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
    "public_contract",
    "r54_ahr_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R54_AHR_FALSE_FLAG_REFS,
)

P7_R54_AHR11_SANITIZED_REVIEW_RESULT_ROW_INTAKE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_BASE_REQUIRED_FIELD_REFS,
    "ahr10_schema_version",
    "ahr10_material_ref",
    "ahr10_next_required_step",
    "ahr10_operation_status_ref",
    "ahr10_actual_human_review_executed_by_person",
    "ahr10_reviewed_case_count",
    "ahr10_selection_row_count",
    *P7_R54_AHR_CURRENT_EXECUTION_BASIS_FIELD_REFS,
    "operation_current_refs_match_current_execution_basis_260_83_256_169",
    "current_execution_basis_refs_match_received_snapshot_260_83_256_169",
    "current_execution_basis_refs_match_260_83_256_169_snapshot",
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
    "reviewer_refs",
    "reviewer_ref_count",
    "reviewed_at_refs_present",
    "axis_refs",
    "axis_count",
    "axis_score_count_per_row",
    "rating_axis_target_thresholds",
    "verdict_counts",
    "readfeel_blocker_row_count",
    "execution_blocker_row_count",
    "question_need_primary_class_counts",
    "rows_match_24_case_manifest",
    "rows_bodyfree_only",
    "rows_selection_only",
    "rows_have_required_axis_scores",
    "rows_have_allowed_verdict_refs",
    "rows_have_allowed_question_observation_refs",
    "rows_have_no_body_or_question_or_path_or_hash",
    "sanitized_review_result_rows_intaken_here",
    "actual_sanitized_review_result_rows_intaken_here",
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
    "public_contract",
    "r54_ahr_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R54_AHR_FALSE_FLAG_REFS,
)


def _false_flags_with_allowed_true(*, allowed_true_refs: tuple[str, ...] = ()) -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_FALSE_FLAG_REFS if key not in set(allowed_true_refs)}


def _add_false_flags_preserving_allowed(material: dict[str, Any], *, allowed_true_refs: tuple[str, ...] = ()) -> None:
    for key in P7_R54_AHR_FALSE_FLAG_REFS:
        if key not in allowed_true_refs:
            material.setdefault(key, False)


def _assert_bodyfree_no_touch_base_allowing_actual_review_receipt(
    data: Mapping[str, Any], *, schema_version: str, policy_section: str, operation_step_ref: str, source: str
) -> None:
    if data.get("schema_version") != schema_version:
        raise ValueError(f"{source} schema version changed")
    if data.get("phase") != P7_PHASE or data.get("current_phase") != P7_PHASE:
        raise ValueError(f"{source} phase changed")
    if data.get("step") != P7_R54_AHR_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R54_AHR_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("policy_kind") != P7_R54_AHR_POLICY_KIND:
        raise ValueError(f"{source} policy kind changed")
    if data.get("policy_section") != policy_section or data.get("operation_step_ref") != operation_step_ref:
        raise ValueError(f"{source} operation step changed")
    if data.get("source_mode") != P7_SOURCE_MODE:
        raise ValueError(f"{source} source mode changed")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} must keep Git connection unchecked / not required")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must remain body-free")
    if _contains_forbidden_ahr_key(data):
        raise ValueError(f"{source} contains forbidden body-full/question/path/hash key")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)
    assert_false_markers(
        {key: data.get(key) for key in P7_R54_AHR_FALSE_FLAG_REFS if key not in P7_R54_AHR11_ALLOWED_TRUE_FALSE_FLAG_REFS},
        source=source,
    )
    public_contract = safe_mapping(data.get("public_contract"))
    if public_contract != public_contract_flags():
        raise ValueError(f"{source} public contract flags changed")
    assert_false_markers(public_contract, source=f"{source} public contract")
    no_touch_contract = safe_mapping(data.get("r54_ahr_no_touch_contract"))
    if no_touch_contract != _no_touch_contract():
        raise ValueError(f"{source} no-touch contract changed")
    assert_false_markers(no_touch_contract, source=f"{source} no-touch contract")
    body_markers = safe_mapping(data.get("body_free_markers"))
    if body_markers != _body_free_markers():
        raise ValueError(f"{source} body-free markers changed")
    assert_false_markers(body_markers, source=f"{source} body-free markers")


def _operation_form_blockers(reviewer_selection_form: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    if reviewer_selection_form.get("selection_form_status") != P7_R54_AHR09_FORM_FROZEN_STATUS_REF:
        blockers.append("ahr09_reviewer_selection_form_not_frozen")
    if reviewer_selection_form.get("next_required_step") != P7_R54_AHR10_STEP_REF:
        blockers.append("ahr09_next_step_not_actual_review_operation")
    if reviewer_selection_form.get("actual_human_review_local_only_operation_allowed_next") is not True:
        blockers.append("ahr09_actual_human_review_operation_not_allowed_next")
    return blockers


def _bodyfree_receipt_blockers(
    *,
    actual_human_review_executed_by_person: bool,
    reviewer_is_person: bool,
    reviewer_person_confirmed: bool,
    reviewer_local_only_read_receipt_present: bool,
    operation_receipt_ref: str,
    reviewer_ref: str,
    review_started_at_ref: str,
    review_completed_at_ref: str,
    reviewed_case_count: int,
    selection_row_count: int,
    local_only: bool,
    must_not_export: bool,
    selection_only: bool,
    body_full_packet_content_included: bool,
    raw_input_included: bool,
    returned_emlis_body_included: bool,
    history_surface_included: bool,
    reviewer_free_text_included: bool,
    reviewer_notes_body_included: bool,
    question_text_included: bool,
    draft_question_text_included: bool,
    local_absolute_path_included: bool,
    body_hash_included: bool,
    packet_content_included: bool,
    terminal_output_body_included: bool,
) -> list[str]:
    blockers: list[str] = []
    if not operation_receipt_ref:
        blockers.append("operation_receipt_ref_missing")
    if not reviewer_ref:
        blockers.append("reviewer_ref_missing")
    if not reviewer_is_person:
        blockers.append("reviewer_is_not_person")
    if not reviewer_person_confirmed:
        blockers.append("reviewer_person_not_confirmed")
    if not reviewer_local_only_read_receipt_present:
        blockers.append("reviewer_local_only_read_receipt_missing")
    if not actual_human_review_executed_by_person:
        blockers.append("actual_human_review_executed_by_person_not_confirmed")
    if not review_started_at_ref or not review_completed_at_ref:
        blockers.append("review_time_refs_missing")
    if reviewed_case_count != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("reviewed_case_count_not_24")
    if selection_row_count != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("selection_row_count_not_24")
    if not local_only:
        blockers.append("local_only_not_confirmed")
    if not must_not_export:
        blockers.append("must_not_export_not_confirmed")
    if not selection_only:
        blockers.append("selection_only_not_confirmed")
    forbidden_flags = {
        "body_full_packet_content_included": body_full_packet_content_included,
        "raw_input_included": raw_input_included,
        "returned_emlis_body_included": returned_emlis_body_included,
        "history_surface_included": history_surface_included,
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
    return blockers


def build_p7_r54_ahr10_actual_human_review_local_only_operation(
    *,
    reviewer_selection_form: Mapping[str, Any] | None = None,
    review_session_id: Any = P7_R54_AHR_DEFAULT_REVIEW_SESSION_ID,
    operation_receipt_ref: Any = "",
    reviewer_ref: Any = "",
    reviewer_is_person: bool = False,
    reviewer_person_confirmed: bool = False,
    reviewer_local_only_read_receipt_present: bool = False,
    actual_human_review_executed_by_person: bool = False,
    review_started_at_ref: Any = "",
    review_completed_at_ref: Any = "",
    reviewed_case_count: int = 0,
    selection_row_count: int = 0,
    local_only: bool = True,
    must_not_export: bool = True,
    selection_only: bool = True,
    body_full_packet_content_included: bool = False,
    raw_input_included: bool = False,
    returned_emlis_body_included: bool = False,
    history_surface_included: bool = False,
    reviewer_free_text_included: bool = False,
    reviewer_notes_body_included: bool = False,
    question_text_included: bool = False,
    draft_question_text_included: bool = False,
    local_absolute_path_included: bool = False,
    body_hash_included: bool = False,
    packet_content_included: bool = False,
    terminal_output_body_included: bool = False,
) -> dict[str, Any]:
    """Intake body-free receipt of a person-run local-only actual review.

    The default is fail-closed.  Passing tests can exercise a body-free receipt,
    but pytest alone must not be read as the real review having happened.
    """

    form = dict(reviewer_selection_form or build_p7_r54_ahr09_reviewer_selection_form_freeze())
    session_id = _safe_review_session_id(review_session_id)
    receipt_ref = clean_identifier(operation_receipt_ref, default="", max_length=180)
    safe_reviewer_ref = clean_identifier(reviewer_ref, default="", max_length=160)
    started_ref = clean_identifier(review_started_at_ref, default="", max_length=160)
    completed_ref = clean_identifier(review_completed_at_ref, default="", max_length=160)
    form_blockers = _operation_form_blockers(form)
    receipt_blockers = _bodyfree_receipt_blockers(
        actual_human_review_executed_by_person=bool(actual_human_review_executed_by_person),
        reviewer_is_person=bool(reviewer_is_person),
        reviewer_person_confirmed=bool(reviewer_person_confirmed),
        reviewer_local_only_read_receipt_present=bool(reviewer_local_only_read_receipt_present),
        operation_receipt_ref=receipt_ref,
        reviewer_ref=safe_reviewer_ref,
        review_started_at_ref=started_ref,
        review_completed_at_ref=completed_ref,
        reviewed_case_count=int(reviewed_case_count),
        selection_row_count=int(selection_row_count),
        local_only=bool(local_only),
        must_not_export=bool(must_not_export),
        selection_only=bool(selection_only),
        body_full_packet_content_included=bool(body_full_packet_content_included),
        raw_input_included=bool(raw_input_included),
        returned_emlis_body_included=bool(returned_emlis_body_included),
        history_surface_included=bool(history_surface_included),
        reviewer_free_text_included=bool(reviewer_free_text_included),
        reviewer_notes_body_included=bool(reviewer_notes_body_included),
        question_text_included=bool(question_text_included),
        draft_question_text_included=bool(draft_question_text_included),
        local_absolute_path_included=bool(local_absolute_path_included),
        body_hash_included=bool(body_hash_included),
        packet_content_included=bool(packet_content_included),
        terminal_output_body_included=bool(terminal_output_body_included),
    )
    blockers = dedupe_identifiers((*form_blockers, *receipt_blockers), limit=80, max_length=220)
    ready = not blockers
    status = P7_R54_AHR10_OPERATION_RECEIPT_INTAKEN_STATUS_REF if ready else P7_R54_AHR10_OPERATION_BLOCKED_STATUS_REF
    reason_refs = [P7_R54_AHR10_READY_REASON_REF] if ready else blockers

    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR10_ACTUAL_HUMAN_REVIEW_LOCAL_ONLY_OPERATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_STEP,
        "scope": P7_R54_AHR_SCOPE,
        "policy_kind": P7_R54_AHR_POLICY_KIND,
        "policy_section": P7_R54_AHR10_STEP_REF,
        "operation_step_ref": P7_R54_AHR10_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr10_actual_human_review_local_only_operation_20260627",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ahr09_schema_version": form.get("schema_version"),
        "ahr09_material_ref": form.get("material_id"),
        "ahr09_next_required_step": form.get("next_required_step"),
        "ahr09_selection_form_status": form.get("selection_form_status"),
        "ahr09_actual_human_review_local_only_operation_allowed_next": form.get(
            "actual_human_review_local_only_operation_allowed_next"
        ),
        "current_execution_basis_refs": dict(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "current_execution_basis_ref_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "current_execution_basis_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "current_execution_basis_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_refs": dict(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_ref_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "operation_current_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "required_current_execution_basis_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "required_current_execution_basis_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "all_required_current_execution_basis_refs_present": True,
        "actual_execution_basis_ref": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF,
        "actual_execution_basis_allowed": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_ALLOWED_REF,
        "actual_review_basis_ref": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_ALLOWED_REF,
        "current_execution_basis_refs_are_actual_execution_basis": True,
        "current_execution_basis_refs_used_as_actual_execution_basis": True,
        "operation_current_refs_are_actual_execution_basis": True,
        "operation_current_refs_used_as_actual_execution_basis": True,
        "operation_current_refs_match_current_execution_basis_260_83_256_169": True,
        "current_execution_basis_refs_match_received_snapshot_260_83_256_169": True,
        "current_execution_basis_refs_match_260_83_256_169_snapshot": True,
        "operation_status_ref": status,
        "operation_receipt_status_ref": status,
        "operation_receipt_reason_refs": reason_refs,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "reviewer_selection_form_ready_for_actual_review_operation": not form_blockers,
        "operation_receipt_ref": receipt_ref if ready else "",
        "operation_receipt_ref_present": bool(receipt_ref),
        "operation_receipt_bodyfree_only": True,
        "reviewer_ref": safe_reviewer_ref if safe_reviewer_ref else "",
        "reviewer_ref_present": bool(safe_reviewer_ref),
        "reviewer_is_person": bool(reviewer_is_person),
        "reviewer_person_confirmed": bool(reviewer_person_confirmed),
        "reviewer_local_only_read_receipt_present": bool(reviewer_local_only_read_receipt_present),
        "review_started_at_ref": started_ref if started_ref else "",
        "review_completed_at_ref": completed_ref if completed_ref else "",
        "review_time_refs_present": bool(started_ref and completed_ref),
        "required_case_count": P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "reviewed_case_count": int(reviewed_case_count),
        "selection_row_count": int(selection_row_count),
        "reviewed_case_count_complete": int(reviewed_case_count) == P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "selection_row_count_complete": int(selection_row_count) == P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "local_only": bool(local_only),
        "must_not_export": bool(must_not_export),
        "selection_only": bool(selection_only),
        "body_full_packet_read_local_only": ready,
        "body_full_packet_content_available_to_local_reviewer_only": ready,
        "body_full_packet_content_included": False,
        "raw_input_included": False,
        "returned_emlis_body_included": False,
        "history_surface_included": False,
        "comment_text_included": False,
        "reviewer_free_text_included": False,
        "reviewer_notes_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_absolute_path_included": False,
        "body_hash_included": False,
        "packet_content_included": False,
        "terminal_output_body_included": False,
        "actual_human_review_executed_by_person": bool(actual_human_review_executed_by_person and reviewer_is_person),
        "actual_human_review_run_here": False,
        "actual_human_review_operation_receipt_intaken_here": ready,
        "actual_human_review_operation_complete": ready,
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
        "implemented_steps": list(P7_R54_AHR10_IMPLEMENTED_STEPS if ready else P7_R54_AHR09_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR10_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR09_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR11_STEP_REF if ready else P7_R54_AHR10_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    _add_false_flags_preserving_allowed(material, allowed_true_refs=P7_R54_AHR11_ALLOWED_TRUE_FALSE_FLAG_REFS)
    return material


def assert_p7_r54_ahr10_actual_human_review_local_only_operation_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR10_ACTUAL_HUMAN_REVIEW_LOCAL_ONLY_OPERATION_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR10 actual human review local-only operation",
    )
    _assert_bodyfree_no_touch_base_allowing_actual_review_receipt(
        data,
        schema_version=P7_R54_AHR10_ACTUAL_HUMAN_REVIEW_LOCAL_ONLY_OPERATION_SCHEMA_VERSION,
        policy_section=P7_R54_AHR10_STEP_REF,
        operation_step_ref=P7_R54_AHR10_STEP_REF,
        source="P7-R54-AHR10 actual human review local-only operation",
    )
    _assert_current_execution_basis_refs(data, source="P7-R54-AHR10 actual human review local-only operation", actual_basis=True)
    if data.get("ahr09_schema_version") != P7_R54_AHR09_REVIEWER_SELECTION_FORM_FREEZE_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR10 must follow AHR09 reviewer selection form")
    if data.get("ahr09_next_required_step") == P7_R54_AHR10_STEP_REF:
        if data.get("ahr09_selection_form_status") != P7_R54_AHR09_FORM_FROZEN_STATUS_REF:
            raise ValueError("P7-R54-AHR10 ready predecessor must be frozen")
    if data.get("operation_status_ref") not in P7_R54_AHR10_ALLOWED_OPERATION_STATUS_REFS:
        raise ValueError("P7-R54-AHR10 status changed")
    if data.get("operation_receipt_status_ref") != data.get("operation_status_ref"):
        raise ValueError("P7-R54-AHR10 status alias changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or (), limit=80, max_length=220)
    if blockers != dedupe_identifiers(data.get("open_execution_blocker_ids") or (), limit=80, max_length=220):
        raise ValueError("P7-R54-AHR10 open blockers must match blockers")
    for key in P7_R54_AHR11_ROW_BODYFREE_FALSE_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR10 must keep {key}=False")
    for key in (
        "actual_human_review_run_here",
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
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR10 must keep {key}=False")
    ready = data.get("operation_status_ref") == P7_R54_AHR10_OPERATION_RECEIPT_INTAKEN_STATUS_REF
    if ready:
        if blockers:
            raise ValueError("P7-R54-AHR10 ready operation must not carry blockers")
        for key in (
            "reviewer_selection_form_ready_for_actual_review_operation",
            "operation_receipt_ref_present",
            "operation_receipt_bodyfree_only",
            "reviewer_ref_present",
            "reviewer_is_person",
            "reviewer_person_confirmed",
            "reviewer_local_only_read_receipt_present",
            "review_time_refs_present",
            "reviewed_case_count_complete",
            "selection_row_count_complete",
            "local_only",
            "must_not_export",
            "selection_only",
            "body_full_packet_read_local_only",
            "body_full_packet_content_available_to_local_reviewer_only",
            "actual_human_review_executed_by_person",
            "actual_human_review_operation_receipt_intaken_here",
            "actual_human_review_operation_complete",
            "sanitized_review_result_row_intake_allowed_next",
            "r52_reintake_claim_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "p5_finalization_blocked_here",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR10 ready operation must keep {key}=True")
        if data.get("reviewed_case_count") != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR10 reviewed case count changed")
        if data.get("selection_row_count") != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR10 selection row count changed")
        if data.get("operation_receipt_reason_refs") != [P7_R54_AHR10_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR10 ready reason changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR10_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR10 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR10_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR10 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR11_STEP_REF:
            raise ValueError("P7-R54-AHR10 next step changed")
    else:
        if data.get("operation_status_ref") != P7_R54_AHR10_OPERATION_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR10 blocked status changed")
        if not blockers:
            raise ValueError("P7-R54-AHR10 blocked operation must carry blockers")
        for key in (
            "actual_human_review_operation_receipt_intaken_here",
            "actual_human_review_operation_complete",
            "sanitized_review_result_row_intake_allowed_next",
        ):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR10 blocked operation must keep {key}=False")
        if data.get("next_required_step") != P7_R54_AHR10_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR10 blocked next step changed")
    return True


def _expected_manifest_rows_by_case_ref() -> dict[str, dict[str, Any]]:
    manifest = build_p7_r54_ahr05_24_case_manifest_freeze()
    return {str(row.get("case_ref_id")): dict(row) for row in manifest.get("case_rows", [])}


def _clean_plan_candidate_flags(value: Any) -> dict[str, bool]:
    flags = {key: False for key in P7_R54_AHR09_PLAN_CANDIDATE_FLAG_REFS}
    if isinstance(value, Mapping):
        for key in P7_R54_AHR09_PLAN_CANDIDATE_FLAG_REFS:
            flags[key] = bool(value.get(key, False))
    flags["p8_implementation_spec_finalized_here"] = False
    return flags


def _validate_and_sanitize_review_result_rows(
    rows: Sequence[Any], *, review_session_id: str, reviewer_ref: str
) -> tuple[list[dict[str, Any]], list[str]]:
    blockers: list[str] = []
    sanitized_rows: list[dict[str, Any]] = []
    expected_by_case_ref = _expected_manifest_rows_by_case_ref()
    if len(rows) != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("review_result_row_count_not_24")
    seen_case_refs: set[str] = set()
    seen_blind_ids: set[str] = set()
    seen_packet_ids: set[str] = set()
    for index, raw_row in enumerate(rows, start=1):
        if not isinstance(raw_row, Mapping):
            blockers.append(f"review_result_row_{index:02d}_not_mapping")
            continue
        if _contains_forbidden_ahr_key(raw_row):
            blockers.append(f"review_result_row_{index:02d}_contains_forbidden_body_question_path_hash_key")
            continue
        row = safe_mapping(raw_row)
        case_ref_id = clean_identifier(row.get("case_ref_id"), default="", max_length=120)
        blind_case_id = clean_identifier(row.get("blind_case_id"), default="", max_length=120)
        packet_ref_id = clean_identifier(row.get("packet_ref_id"), default="", max_length=120)
        expected = expected_by_case_ref.get(case_ref_id)
        if not expected:
            blockers.append(f"review_result_row_{index:02d}_case_ref_not_in_manifest")
            continue
        if blind_case_id != expected.get("blind_case_id"):
            blockers.append(f"review_result_row_{index:02d}_blind_case_id_mismatch")
        if packet_ref_id != expected.get("packet_ref_id"):
            blockers.append(f"review_result_row_{index:02d}_packet_ref_id_mismatch")
        if row.get("family") != expected.get("family"):
            blockers.append(f"review_result_row_{index:02d}_family_mismatch")
        if row.get("case_role") != expected.get("case_role"):
            blockers.append(f"review_result_row_{index:02d}_case_role_mismatch")
        seen_case_refs.add(case_ref_id)
        seen_blind_ids.add(blind_case_id)
        seen_packet_ids.add(packet_ref_id)
        axis_scores_raw = safe_mapping(row.get("axis_scores"))
        axis_scores: dict[str, float] = {}
        if set(axis_scores_raw) != set(P7_R54_AHR05_RATING_AXIS_REFS):
            blockers.append(f"review_result_row_{index:02d}_axis_refs_mismatch")
        for axis_ref in P7_R54_AHR05_RATING_AXIS_REFS:
            try:
                score = float(axis_scores_raw.get(axis_ref))
            except (TypeError, ValueError):
                blockers.append(f"review_result_row_{index:02d}_{axis_ref}_score_not_number")
                score = -1.0
            if score < 0.0 or score > 1.0:
                blockers.append(f"review_result_row_{index:02d}_{axis_ref}_score_out_of_range")
            axis_scores[axis_ref] = score
        if row.get("axis_score_count") != len(P7_R54_AHR05_RATING_AXIS_REFS):
            blockers.append(f"review_result_row_{index:02d}_axis_score_count_not_6")
        verdict = clean_identifier(row.get("verdict"), default="", max_length=80)
        if verdict not in P7_R54_AHR09_VERDICT_OPTION_REFS:
            blockers.append(f"review_result_row_{index:02d}_verdict_not_allowed")
        sanitized_reason_ids = dedupe_identifiers(row.get("sanitized_reason_ids") or (), limit=20, max_length=120)
        unknown_reason_ids = [item for item in sanitized_reason_ids if item not in P7_R54_AHR09_SANITIZED_REASON_ID_OPTION_REFS]
        if unknown_reason_ids:
            blockers.append(f"review_result_row_{index:02d}_sanitized_reason_id_not_allowed")
        readfeel_blocker_ids = dedupe_identifiers(row.get("readfeel_blocker_ids") or (), limit=20, max_length=120)
        if any(item not in P7_R54_AHR09_READFEEL_BLOCKER_ID_OPTION_REFS for item in readfeel_blocker_ids):
            blockers.append(f"review_result_row_{index:02d}_readfeel_blocker_id_not_allowed")
        execution_blocker_ids = dedupe_identifiers(row.get("execution_blocker_ids") or (), limit=20, max_length=120)
        if any(item not in P7_R54_AHR09_EXECUTION_BLOCKER_ID_OPTION_REFS for item in execution_blocker_ids):
            blockers.append(f"review_result_row_{index:02d}_execution_blocker_id_not_allowed")
        question_need_primary_class = clean_identifier(row.get("question_need_primary_class"), default="", max_length=160)
        if question_need_primary_class not in P7_R54_AHR09_QUESTION_NEED_PRIMARY_CLASS_REFS:
            blockers.append(f"review_result_row_{index:02d}_question_need_primary_class_not_allowed")
        ambiguity_kind_refs = dedupe_identifiers(row.get("ambiguity_kind_refs") or (), limit=20, max_length=120)
        if any(item not in P7_R54_AHR09_AMBIGUITY_KIND_OPTION_REFS for item in ambiguity_kind_refs):
            blockers.append(f"review_result_row_{index:02d}_ambiguity_kind_ref_not_allowed")
        one_question_fit_ref = clean_identifier(row.get("one_question_fit_ref"), default="", max_length=160)
        if one_question_fit_ref not in P7_R54_AHR09_ONE_QUESTION_FIT_OPTION_REFS:
            blockers.append(f"review_result_row_{index:02d}_one_question_fit_ref_not_allowed")
        repair_required_refs = dedupe_identifiers(row.get("repair_required_refs") or (), limit=20, max_length=160)
        if any(item not in P7_R54_AHR09_REPAIR_REQUIRED_OPTION_REFS for item in repair_required_refs):
            blockers.append(f"review_result_row_{index:02d}_repair_required_ref_not_allowed")
        plan_candidate_flags = _clean_plan_candidate_flags(row.get("plan_candidate_flags"))
        for flag_ref in P7_R54_AHR11_ROW_BODYFREE_FALSE_FLAG_REFS:
            if row.get(flag_ref) is not False:
                blockers.append(f"review_result_row_{index:02d}_{flag_ref}_not_false")
        if row.get("selection_only_row") is not True:
            blockers.append(f"review_result_row_{index:02d}_selection_only_row_not_true")
        if row.get("body_free") is not True:
            blockers.append(f"review_result_row_{index:02d}_body_free_not_true")
        if row.get("review_session_id") != review_session_id:
            blockers.append(f"review_result_row_{index:02d}_review_session_id_mismatch")
        if row.get("reviewer_ref") != reviewer_ref:
            blockers.append(f"review_result_row_{index:02d}_reviewer_ref_mismatch")
        if not clean_identifier(row.get("reviewed_at_ref"), default="", max_length=160):
            blockers.append(f"review_result_row_{index:02d}_reviewed_at_ref_missing")
        sanitized_rows.append(
            {
                "schema_version": P7_R54_AHR11_REVIEW_RESULT_ROW_SCHEMA_VERSION,
                "review_result_row_ref": clean_identifier(
                    row.get("review_result_row_ref"), default=f"review_result_row_{index:03d}", max_length=120
                ),
                "review_session_id": review_session_id,
                "case_ref_id": case_ref_id,
                "blind_case_id": blind_case_id,
                "packet_ref_id": packet_ref_id,
                "family": expected.get("family"),
                "case_role": expected.get("case_role"),
                "reviewer_ref": reviewer_ref,
                "reviewed_at_ref": clean_identifier(row.get("reviewed_at_ref"), default="reviewed_at_bucket_ref", max_length=160),
                "axis_scores": axis_scores,
                "axis_score_count": len(P7_R54_AHR05_RATING_AXIS_REFS),
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
                "reviewer_free_text_included": False,
                "raw_body_included": False,
                "returned_emlis_body_included": False,
                "history_surface_included": False,
                "comment_text_included": False,
                "question_text_included": False,
                "draft_question_text_included": False,
                "local_absolute_path_included": False,
                "body_hash_included": False,
                "packet_content_included": False,
                "body_free": True,
            }
        )
    if len(seen_case_refs) != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("case_ref_ids_not_unique_or_not_24")
    if len(seen_blind_ids) != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("blind_case_ids_not_unique_or_not_24")
    if len(seen_packet_ids) != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("packet_ref_ids_not_unique_or_not_24")
    if blockers:
        return [], dedupe_identifiers(blockers, limit=120, max_length=240)
    return sanitized_rows, []


def _count_values(rows: Sequence[Mapping[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = str(row.get(field, ""))
        counts[key] = counts.get(key, 0) + 1
    return counts


def build_p7_r54_ahr11_sanitized_review_result_row_intake(
    *,
    actual_human_review_operation: Mapping[str, Any] | None = None,
    review_result_rows: Sequence[Any] | None = None,
    review_session_id: Any = P7_R54_AHR_DEFAULT_REVIEW_SESSION_ID,
) -> dict[str, Any]:
    """Intake 24 selection-only sanitized review result rows as body-free rows."""

    operation = dict(actual_human_review_operation or build_p7_r54_ahr10_actual_human_review_local_only_operation())
    session_id = _safe_review_session_id(review_session_id)
    rows_input = list(review_result_rows or [])
    operation_ready = operation.get("operation_status_ref") == P7_R54_AHR10_OPERATION_RECEIPT_INTAKEN_STATUS_REF
    reviewer_ref = clean_identifier(operation.get("reviewer_ref"), default=P7_R54_AHR10_REVIEWER_PERSON_REF_DEFAULT, max_length=160)
    sanitized_rows, row_blockers = _validate_and_sanitize_review_result_rows(
        rows_input, review_session_id=session_id, reviewer_ref=reviewer_ref
    )
    blockers: list[str] = []
    if not operation_ready:
        blockers.append("ahr10_actual_human_review_operation_not_ready")
    if operation.get("next_required_step") != P7_R54_AHR11_STEP_REF:
        blockers.append("ahr10_next_step_not_sanitized_result_row_intake")
    if operation.get("actual_human_review_executed_by_person") is not True:
        blockers.append("ahr10_actual_human_review_executed_by_person_not_confirmed")
    if operation.get("reviewed_case_count") != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("ahr10_reviewed_case_count_not_24")
    if operation.get("selection_row_count") != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("ahr10_selection_row_count_not_24")
    blockers.extend(row_blockers)
    blockers = dedupe_identifiers(blockers, limit=160, max_length=240)
    ready = not blockers
    status = P7_R54_AHR11_INTAKE_READY_STATUS_REF if ready else P7_R54_AHR11_INTAKE_BLOCKED_STATUS_REF
    reason_refs = [P7_R54_AHR11_READY_REASON_REF] if ready else blockers
    rows_for_output = sanitized_rows if ready else []
    row_refs = [str(row.get("review_result_row_ref")) for row in rows_for_output]
    case_refs = [str(row.get("case_ref_id")) for row in rows_for_output]
    blind_ids = [str(row.get("blind_case_id")) for row in rows_for_output]
    packet_refs = [str(row.get("packet_ref_id")) for row in rows_for_output]
    reviewer_refs = dedupe_identifiers([row.get("reviewer_ref") for row in rows_for_output], limit=24, max_length=160)
    verdict_counts = _count_values(rows_for_output, "verdict") if ready else {}
    question_counts = _count_values(rows_for_output, "question_need_primary_class") if ready else {}
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR11_SANITIZED_REVIEW_RESULT_ROW_INTAKE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_STEP,
        "scope": P7_R54_AHR_SCOPE,
        "policy_kind": P7_R54_AHR_POLICY_KIND,
        "policy_section": P7_R54_AHR11_STEP_REF,
        "operation_step_ref": P7_R54_AHR11_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr11_sanitized_review_result_row_intake_20260627",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ahr10_schema_version": operation.get("schema_version"),
        "ahr10_material_ref": operation.get("material_id"),
        "ahr10_next_required_step": operation.get("next_required_step"),
        "ahr10_operation_status_ref": operation.get("operation_status_ref"),
        "ahr10_actual_human_review_executed_by_person": operation.get("actual_human_review_executed_by_person"),
        "ahr10_reviewed_case_count": operation.get("reviewed_case_count"),
        "ahr10_selection_row_count": operation.get("selection_row_count"),
        "current_execution_basis_refs": dict(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "current_execution_basis_ref_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "current_execution_basis_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "current_execution_basis_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_refs": dict(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_ref_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "operation_current_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "required_current_execution_basis_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "required_current_execution_basis_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "all_required_current_execution_basis_refs_present": True,
        "actual_execution_basis_ref": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF,
        "actual_execution_basis_allowed": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_ALLOWED_REF,
        "actual_review_basis_ref": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_ALLOWED_REF,
        "current_execution_basis_refs_are_actual_execution_basis": True,
        "current_execution_basis_refs_used_as_actual_execution_basis": True,
        "operation_current_refs_are_actual_execution_basis": True,
        "operation_current_refs_used_as_actual_execution_basis": True,
        "operation_current_refs_match_current_execution_basis_260_83_256_169": True,
        "current_execution_basis_refs_match_received_snapshot_260_83_256_169": True,
        "current_execution_basis_refs_match_260_83_256_169_snapshot": True,
        "sanitized_review_result_row_intake_status_ref": status,
        "sanitized_review_result_row_intake_reason_refs": reason_refs,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "operation_ready_for_sanitized_result_intake": operation_ready,
        "required_case_count": P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "received_review_result_row_count": len(rows_input),
        "review_result_row_count": len(rows_for_output),
        "sanitized_review_result_row_count": len(rows_for_output),
        "reviewed_case_count": operation.get("reviewed_case_count") if operation_ready else 0,
        "selection_row_count": operation.get("selection_row_count") if operation_ready else 0,
        "review_result_rows": rows_for_output,
        "review_result_row_refs": row_refs,
        "review_result_row_ref_count": len(row_refs),
        "case_ref_ids": case_refs,
        "case_ref_id_count": len(case_refs),
        "case_ref_ids_unique": len(set(case_refs)) == len(case_refs) == P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "blind_case_ids": blind_ids,
        "blind_case_id_count": len(blind_ids),
        "blind_case_ids_unique": len(set(blind_ids)) == len(blind_ids) == P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "packet_ref_ids": packet_refs,
        "packet_ref_id_count": len(packet_refs),
        "packet_ref_ids_unique": len(set(packet_refs)) == len(packet_refs) == P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "reviewer_refs": reviewer_refs,
        "reviewer_ref_count": len(reviewer_refs),
        "reviewed_at_refs_present": ready,
        "axis_refs": list(P7_R54_AHR05_RATING_AXIS_REFS),
        "axis_count": len(P7_R54_AHR05_RATING_AXIS_REFS),
        "axis_score_count_per_row": len(P7_R54_AHR05_RATING_AXIS_REFS) if ready else 0,
        "rating_axis_target_thresholds": dict(P7_R54_AHR05_RATING_AXIS_TARGET_THRESHOLDS),
        "verdict_counts": verdict_counts,
        "readfeel_blocker_row_count": sum(1 for row in rows_for_output if row.get("readfeel_blocker_ids")),
        "execution_blocker_row_count": sum(1 for row in rows_for_output if row.get("execution_blocker_ids")),
        "question_need_primary_class_counts": question_counts,
        "rows_match_24_case_manifest": ready,
        "rows_bodyfree_only": ready,
        "rows_selection_only": ready,
        "rows_have_required_axis_scores": ready,
        "rows_have_allowed_verdict_refs": ready,
        "rows_have_allowed_question_observation_refs": ready,
        "rows_have_no_body_or_question_or_path_or_hash": ready,
        "sanitized_review_result_rows_intaken_here": ready,
        "actual_sanitized_review_result_rows_intaken_here": ready,
        "actual_human_review_executed_by_person": operation.get("actual_human_review_executed_by_person") is True,
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
        "implemented_steps": list(P7_R54_AHR11_IMPLEMENTED_STEPS if ready else (P7_R54_AHR10_IMPLEMENTED_STEPS if operation_ready else P7_R54_AHR09_IMPLEMENTED_STEPS)),
        "not_yet_implemented_steps": list(P7_R54_AHR11_NOT_YET_IMPLEMENTED_STEPS if ready else (P7_R54_AHR10_NOT_YET_IMPLEMENTED_STEPS if operation_ready else P7_R54_AHR09_NOT_YET_IMPLEMENTED_STEPS)),
        "next_required_step": P7_R54_AHR12_STEP_REF if ready else P7_R54_AHR11_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    _add_false_flags_preserving_allowed(material, allowed_true_refs=P7_R54_AHR11_ALLOWED_TRUE_FALSE_FLAG_REFS)
    return material


def assert_p7_r54_ahr11_sanitized_review_result_row_intake_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR11_SANITIZED_REVIEW_RESULT_ROW_INTAKE_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR11 sanitized review result row intake",
    )
    _assert_bodyfree_no_touch_base_allowing_actual_review_receipt(
        data,
        schema_version=P7_R54_AHR11_SANITIZED_REVIEW_RESULT_ROW_INTAKE_SCHEMA_VERSION,
        policy_section=P7_R54_AHR11_STEP_REF,
        operation_step_ref=P7_R54_AHR11_STEP_REF,
        source="P7-R54-AHR11 sanitized review result row intake",
    )
    _assert_current_execution_basis_refs(data, source="P7-R54-AHR11 sanitized review result row intake", actual_basis=True)
    if data.get("ahr10_schema_version") != P7_R54_AHR10_ACTUAL_HUMAN_REVIEW_LOCAL_ONLY_OPERATION_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR11 must follow AHR10 actual review operation")
    if data.get("sanitized_review_result_row_intake_status_ref") not in P7_R54_AHR11_ALLOWED_INTAKE_STATUS_REFS:
        raise ValueError("P7-R54-AHR11 intake status changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or (), limit=160, max_length=240)
    if blockers != dedupe_identifiers(data.get("open_execution_blocker_ids") or (), limit=160, max_length=240):
        raise ValueError("P7-R54-AHR11 open blockers must match blockers")
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
            raise ValueError(f"P7-R54-AHR11 must keep {key}=False")
    ready = data.get("sanitized_review_result_row_intake_status_ref") == P7_R54_AHR11_INTAKE_READY_STATUS_REF
    if ready:
        if blockers:
            raise ValueError("P7-R54-AHR11 ready intake must not carry blockers")
        for key in (
            "operation_ready_for_sanitized_result_intake",
            "rows_match_24_case_manifest",
            "rows_bodyfree_only",
            "rows_selection_only",
            "rows_have_required_axis_scores",
            "rows_have_allowed_verdict_refs",
            "rows_have_allowed_question_observation_refs",
            "rows_have_no_body_or_question_or_path_or_hash",
            "sanitized_review_result_rows_intaken_here",
            "actual_sanitized_review_result_rows_intaken_here",
            "actual_human_review_executed_by_person",
            "rating_row_normalization_allowed_next",
            "r52_reintake_claim_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "p5_finalization_blocked_here",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR11 ready intake must keep {key}=True")
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
            if data.get(field) != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
                raise ValueError(f"P7-R54-AHR11 {field} changed")
        if data.get("axis_score_count_per_row") != len(P7_R54_AHR05_RATING_AXIS_REFS):
            raise ValueError("P7-R54-AHR11 axis score count changed")
        if tuple(data.get("axis_refs") or ()) != P7_R54_AHR05_RATING_AXIS_REFS:
            raise ValueError("P7-R54-AHR11 axis refs changed")
        if safe_mapping(data.get("rating_axis_target_thresholds")) != P7_R54_AHR05_RATING_AXIS_TARGET_THRESHOLDS:
            raise ValueError("P7-R54-AHR11 axis thresholds changed")
        for row in data.get("review_result_rows") or []:
            if not isinstance(row, Mapping):
                raise ValueError("P7-R54-AHR11 review row must be mapping")
            if row.get("schema_version") != P7_R54_AHR11_REVIEW_RESULT_ROW_SCHEMA_VERSION:
                raise ValueError("P7-R54-AHR11 review row schema changed")
            for key in P7_R54_AHR11_ROW_BODYFREE_FALSE_FLAG_REFS:
                if row.get(key) is not False:
                    raise ValueError(f"P7-R54-AHR11 row must keep {key}=False")
            if row.get("selection_only_row") is not True or row.get("body_free") is not True:
                raise ValueError("P7-R54-AHR11 row must remain selection-only body-free")
            plan_flags = safe_mapping(row.get("plan_candidate_flags"))
            if set(plan_flags) != set(P7_R54_AHR09_PLAN_CANDIDATE_FLAG_REFS):
                raise ValueError("P7-R54-AHR11 row plan flag refs changed")
            if plan_flags.get("p8_implementation_spec_finalized_here") is not False:
                raise ValueError("P7-R54-AHR11 must not finalize P8 implementation")
        if data.get("sanitized_review_result_row_intake_reason_refs") != [P7_R54_AHR11_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR11 ready reason changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR11_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR11 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR11_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR11 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR12_STEP_REF:
            raise ValueError("P7-R54-AHR11 next step changed")
    else:
        if data.get("sanitized_review_result_row_intake_status_ref") != P7_R54_AHR11_INTAKE_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR11 blocked status changed")
        if not blockers:
            raise ValueError("P7-R54-AHR11 blocked intake must carry blockers")
        for key in (
            "rows_match_24_case_manifest",
            "rows_bodyfree_only",
            "rows_selection_only",
            "rows_have_required_axis_scores",
            "rows_have_allowed_verdict_refs",
            "rows_have_allowed_question_observation_refs",
            "rows_have_no_body_or_question_or_path_or_hash",
            "sanitized_review_result_rows_intaken_here",
            "actual_sanitized_review_result_rows_intaken_here",
            "rating_row_normalization_allowed_next",
        ):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR11 blocked intake must keep {key}=False")
        if data.get("next_required_step") != P7_R54_AHR11_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR11 blocked next step changed")
    return True


build_p7_r54_ahr10_actual_human_review_local_only_operation_bodyfree = (
    build_p7_r54_ahr10_actual_human_review_local_only_operation
)
assert_p7_r54_ahr10_actual_human_review_local_only_operation_bodyfree_contract = (
    assert_p7_r54_ahr10_actual_human_review_local_only_operation_contract
)
build_p7_r54_ahr11_sanitized_review_result_row_intake_bodyfree = (
    build_p7_r54_ahr11_sanitized_review_result_row_intake
)
assert_p7_r54_ahr11_sanitized_review_result_row_intake_bodyfree_contract = (
    assert_p7_r54_ahr11_sanitized_review_result_row_intake_contract
)
build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr10_actual_human_review_local_only_operation = (
    build_p7_r54_ahr10_actual_human_review_local_only_operation
)
assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr10_actual_human_review_local_only_operation_contract = (
    assert_p7_r54_ahr10_actual_human_review_local_only_operation_contract
)
build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr11_sanitized_review_result_row_intake = (
    build_p7_r54_ahr11_sanitized_review_result_row_intake
)
assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr11_sanitized_review_result_row_intake_contract = (
    assert_p7_r54_ahr11_sanitized_review_result_row_intake_contract
)
build_p7_r54_actual_human_review_execution_local_only_operation_bodyfree_receipt = (
    build_p7_r54_ahr10_actual_human_review_local_only_operation
)
assert_p7_r54_actual_human_review_execution_local_only_operation_bodyfree_receipt_contract = (
    assert_p7_r54_ahr10_actual_human_review_local_only_operation_contract
)
build_p7_r54_actual_human_review_execution_sanitized_review_result_row_intake_bodyfree = (
    build_p7_r54_ahr11_sanitized_review_result_row_intake
)
assert_p7_r54_actual_human_review_execution_sanitized_review_result_row_intake_bodyfree_contract = (
    assert_p7_r54_ahr11_sanitized_review_result_row_intake_contract
)

# ---------------------------------------------------------------------------
# R54-AHR-12 / R54-AHR-13: rating normalization and blocker ingestion.
# ---------------------------------------------------------------------------

P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR12: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR11[1:]
P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR13: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR12[1:]
P7_R54_AHR12_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_AHR11_IMPLEMENTED_STEPS, P7_R54_AHR12_STEP_REF)
P7_R54_AHR12_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR12
P7_R54_AHR13_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_AHR12_IMPLEMENTED_STEPS, P7_R54_AHR13_STEP_REF)
P7_R54_AHR13_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR13

P7_R54_AHR_RATING_ROW_NORMALIZATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.ahr12_rating_row_normalization.bodyfree.v1"
)
P7_R54_AHR_READFEEL_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.ahr13_readfeel_execution_blocker_ingestion.bodyfree.v1"
)
P7_R54_AHR12_RATING_ROW_NORMALIZATION_SCHEMA_VERSION: Final = P7_R54_AHR_RATING_ROW_NORMALIZATION_SCHEMA_VERSION
P7_R54_AHR13_READFEEL_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION: Final = (
    P7_R54_AHR_READFEEL_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION
)
P7_R54_AHR12_RATING_ROW_SCHEMA_VERSION: Final = "cocolon.emlis.p7_r54.ahr.rating_row.bodyfree.v1"
P7_R54_AHR13_BLOCKER_ROW_SCHEMA_VERSION: Final = "cocolon.emlis.p7_r54.ahr.blocker_row.bodyfree.v1"

P7_R54_AHR12_NORMALIZED_STATUS_REF: Final = "AHR_RATING_ROW_NORMALIZATION_READY"
P7_R54_AHR12_BLOCKED_STATUS_REF: Final = "AHR_RATING_ROW_NORMALIZATION_BLOCKED"
P7_R54_AHR12_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR12_NORMALIZED_STATUS_REF,
    P7_R54_AHR12_BLOCKED_STATUS_REF,
)
P7_R54_AHR12_READY_REASON_REF: Final = "r54_ahr_rating_rows_normalized_bodyfree_from_sanitized_review_results"
P7_R54_AHR12_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-12_repair_rating_row_normalization_before_blocker_ingestion"
)

P7_R54_AHR13_INGESTED_STATUS_REF: Final = "AHR_READFEEL_EXECUTION_BLOCKERS_INGESTED_BODYFREE"
P7_R54_AHR13_BLOCKED_STATUS_REF: Final = "AHR_READFEEL_EXECUTION_BLOCKER_INGESTION_BLOCKED"
P7_R54_AHR13_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR13_INGESTED_STATUS_REF,
    P7_R54_AHR13_BLOCKED_STATUS_REF,
)
P7_R54_AHR13_READY_REASON_REF: Final = "r54_ahr_readfeel_and_execution_blockers_ingested_separately_bodyfree"
P7_R54_AHR13_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-13_repair_blocker_ingestion_before_question_need_observation_normalization"
)
P7_R54_AHR13_READFEEL_BLOCKER_KIND_REF: Final = "READFEEL_BLOCKER"
P7_R54_AHR13_EXECUTION_BLOCKER_KIND_REF: Final = "EXECUTION_BLOCKER"
P7_R54_AHR13_BLOCKER_STATUS_OPEN_REF: Final = "OPEN"
P7_R54_AHR13_READFEEL_ROUTE_REF: Final = "P5_REPAIR_RETURN"
P7_R54_AHR13_EXECUTION_ROUTE_REF: Final = "R54_OPERATION_BLOCKED_EVIDENCE_REPAIR"
P7_R54_AHR13_FORBIDDEN_FREE_TEXT_KEY_REFS: Final[frozenset[str]] = frozenset(
    {
        "blocker_free_text",
        "readfeel_blocker_free_text",
        "execution_blocker_free_text",
        "blocker_note",
        "blocker_notes",
        "reviewer_blocker_note",
    }
)

P7_R54_AHR12_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "actual_human_review_executed_by_person",
    "actual_rating_rows_materialized_here",
)
P7_R54_AHR13_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = P7_R54_AHR12_ALLOWED_TRUE_FALSE_FLAG_REFS
P7_R54_AHR12_RATING_ROW_BODYFREE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "reviewer_free_text_included",
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
P7_R54_AHR13_BLOCKER_ROW_BODYFREE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = P7_R54_AHR12_RATING_ROW_BODYFREE_FALSE_FLAG_REFS

P7_R54_AHR12_RATING_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "rating_row_ref",
    "source_review_result_row_ref",
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
    "family",
    "case_role",
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
    "body_free",
    *P7_R54_AHR12_RATING_ROW_BODYFREE_FALSE_FLAG_REFS,
)
P7_R54_AHR13_BLOCKER_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "blocker_row_ref",
    "source_rating_row_ref",
    "source_review_result_row_ref",
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
    "blocker_kind",
    "blocker_id",
    "blocker_status",
    "sanitized_reason_ids",
    "routes_to",
    "body_free",
    *P7_R54_AHR13_BLOCKER_ROW_BODYFREE_FALSE_FLAG_REFS,
)

P7_R54_AHR12_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_BASE_REQUIRED_FIELD_REFS,
    "ahr11_schema_version",
    "ahr11_material_ref",
    "ahr11_next_required_step",
    "ahr11_sanitized_review_result_row_intake_status_ref",
    "ahr11_rating_row_normalization_allowed_next",
    "ahr11_sanitized_review_result_row_count",
    "ahr11_review_result_row_count",
    "ahr11_case_ref_id_count",
    "ahr11_actual_human_review_executed_by_person",
    *P7_R54_AHR_CURRENT_EXECUTION_BASIS_FIELD_REFS,
    "operation_current_refs_match_current_execution_basis_260_83_256_169",
    "current_execution_basis_refs_match_received_snapshot_260_83_256_169",
    "current_execution_basis_refs_match_260_83_256_169_snapshot",
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
    "rating_rows_bodyfree_only",
    "rating_rows_match_sanitized_review_result_case_refs",
    "rating_rows_have_required_axis_scores",
    "rating_scores_in_range",
    "rating_rows_have_allowed_verdict_refs",
    "below_target_axis_refs_by_case",
    "below_target_axis_ref_counts",
    "below_target_case_count",
    "verdict_counts",
    "pass_case_count",
    "yellow_case_count",
    "repair_required_case_count",
    "red_case_count",
    "blocked_case_count",
    "not_reviewable_case_count",
    "readfeel_blocker_row_source_count",
    "execution_blocker_row_source_count",
    "rating_rows_normalized_here",
    "actual_rating_rows_materialized_here",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_review_evidence_complete",
    "readfeel_blocker_ingestion_allowed_next",
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
    "public_contract",
    "r54_ahr_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R54_AHR_FALSE_FLAG_REFS,
)

P7_R54_AHR13_READFEEL_EXECUTION_BLOCKER_INGESTION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_BASE_REQUIRED_FIELD_REFS,
    "ahr12_schema_version",
    "ahr12_material_ref",
    "ahr12_next_required_step",
    "ahr12_rating_row_normalization_status_ref",
    "ahr12_rating_row_count",
    "ahr12_readfeel_blocker_ingestion_allowed_next",
    "ahr12_actual_rating_rows_materialized_here",
    *P7_R54_AHR_CURRENT_EXECUTION_BASIS_FIELD_REFS,
    "operation_current_refs_match_current_execution_basis_260_83_256_169",
    "current_execution_basis_refs_match_received_snapshot_260_83_256_169",
    "current_execution_basis_refs_match_260_83_256_169_snapshot",
    "blocker_ingestion_status_ref",
    "blocker_ingestion_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "rating_rows_ready_for_blocker_ingestion",
    "required_case_count",
    "rating_row_count",
    "source_rating_row_refs",
    "source_rating_row_ref_count",
    "blocker_rows",
    "blocker_row_count",
    "readfeel_blocker_rows",
    "readfeel_blocker_row_count",
    "execution_blocker_rows",
    "execution_blocker_row_count",
    "open_readfeel_blocker_count",
    "open_execution_blocker_count",
    "observed_readfeel_blocker_ids",
    "observed_readfeel_blocker_id_count",
    "observed_execution_blocker_ids",
    "observed_execution_blocker_id_count",
    "readfeel_blocker_ids_are_allowed",
    "execution_blocker_ids_are_allowed",
    "blocker_rows_bodyfree_only",
    "blocker_free_text_included",
    "readfeel_execution_blockers_separated",
    "readfeel_blockers_routed_to_p5_repair",
    "readfeel_blockers_routed_to_p8_material",
    "readfeel_blockers_not_routed_to_p8_material",
    "execution_blockers_routed_to_operation_blocked",
    "execution_blockers_mixed_into_p5_quality",
    "execution_blockers_not_mixed_into_p5_quality",
    "readfeel_blocker_ingestion_completed",
    "execution_blocker_ingestion_completed",
    "question_need_observation_normalization_allowed_next",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_review_evidence_complete",
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
    "public_contract",
    "r54_ahr_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R54_AHR_FALSE_FLAG_REFS,
)


def _assert_bodyfree_no_touch_base_allowing_true_flags(
    data: Mapping[str, Any],
    *,
    schema_version: str,
    policy_section: str,
    operation_step_ref: str,
    source: str,
    allowed_true_refs: tuple[str, ...],
) -> None:
    if data.get("schema_version") != schema_version:
        raise ValueError(f"{source} schema version changed")
    if data.get("phase") != P7_PHASE or data.get("current_phase") != P7_PHASE:
        raise ValueError(f"{source} phase changed")
    if data.get("step") != P7_R54_AHR_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R54_AHR_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("policy_kind") != P7_R54_AHR_POLICY_KIND:
        raise ValueError(f"{source} policy kind changed")
    if data.get("policy_section") != policy_section or data.get("operation_step_ref") != operation_step_ref:
        raise ValueError(f"{source} operation step changed")
    if data.get("source_mode") != P7_SOURCE_MODE:
        raise ValueError(f"{source} source mode changed")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} must keep Git connection unchecked / not required")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must remain body-free")
    if _contains_forbidden_ahr_key(data):
        raise ValueError(f"{source} contains forbidden body-full/question/path/hash key")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)
    allowed = set(allowed_true_refs)
    assert_false_markers(
        {key: data.get(key) for key in P7_R54_AHR_FALSE_FLAG_REFS if key not in allowed},
        source=source,
    )
    public_contract = safe_mapping(data.get("public_contract"))
    if public_contract != public_contract_flags():
        raise ValueError(f"{source} public contract flags changed")
    assert_false_markers(public_contract, source=f"{source} public contract")
    no_touch_contract = safe_mapping(data.get("r54_ahr_no_touch_contract"))
    if no_touch_contract != _no_touch_contract():
        raise ValueError(f"{source} no-touch contract changed")
    assert_false_markers(no_touch_contract, source=f"{source} no-touch contract")
    body_markers = safe_mapping(data.get("body_free_markers"))
    if body_markers != _body_free_markers():
        raise ValueError(f"{source} body-free markers changed")
    assert_false_markers(body_markers, source=f"{source} body-free markers")


def _has_forbidden_free_text_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in P7_R54_AHR13_FORBIDDEN_FREE_TEXT_KEY_REFS:
                return True
            if _has_forbidden_free_text_key(child):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_has_forbidden_free_text_key(child) for child in value)
    return False


def _normalize_rating_rows_from_sanitized_results(rows: Sequence[Any], *, review_session_id: str) -> tuple[list[dict[str, Any]], list[str]]:
    blockers: list[str] = []
    rating_rows: list[dict[str, Any]] = []
    expected_case_refs: set[str] = set(_expected_manifest_rows_by_case_ref())
    seen_case_refs: set[str] = set()
    for index, raw_row in enumerate(rows, start=1):
        if not isinstance(raw_row, Mapping):
            blockers.append(f"rating_source_row_{index:02d}_not_mapping")
            continue
        if _contains_forbidden_ahr_key(raw_row):
            blockers.append(f"rating_source_row_{index:02d}_contains_forbidden_body_question_path_hash_key")
            continue
        row = safe_mapping(raw_row)
        if row.get("schema_version") != P7_R54_AHR11_REVIEW_RESULT_ROW_SCHEMA_VERSION:
            blockers.append(f"rating_source_row_{index:02d}_schema_version_changed")
        case_ref_id = clean_identifier(row.get("case_ref_id"), default="", max_length=120)
        if case_ref_id not in expected_case_refs:
            blockers.append(f"rating_source_row_{index:02d}_case_ref_not_in_manifest")
        seen_case_refs.add(case_ref_id)
        axis_scores_raw = safe_mapping(row.get("axis_scores"))
        axis_scores: dict[str, float] = {}
        if set(axis_scores_raw) != set(P7_R54_AHR05_RATING_AXIS_REFS):
            blockers.append(f"rating_source_row_{index:02d}_axis_refs_mismatch")
        for axis_ref in P7_R54_AHR05_RATING_AXIS_REFS:
            try:
                score = float(axis_scores_raw.get(axis_ref))
            except (TypeError, ValueError):
                blockers.append(f"rating_source_row_{index:02d}_{axis_ref}_score_not_number")
                score = -1.0
            if score < 0.0 or score > 1.0:
                blockers.append(f"rating_source_row_{index:02d}_{axis_ref}_score_out_of_range")
            axis_scores[axis_ref] = score
        if row.get("axis_score_count") != len(P7_R54_AHR05_RATING_AXIS_REFS):
            blockers.append(f"rating_source_row_{index:02d}_axis_score_count_not_6")
        verdict = clean_identifier(row.get("verdict"), default="", max_length=80)
        if verdict not in P7_R54_AHR09_VERDICT_OPTION_REFS:
            blockers.append(f"rating_source_row_{index:02d}_verdict_not_allowed")
        sanitized_reason_ids = dedupe_identifiers(row.get("sanitized_reason_ids") or (), limit=20, max_length=120)
        if any(item not in P7_R54_AHR09_SANITIZED_REASON_ID_OPTION_REFS for item in sanitized_reason_ids):
            blockers.append(f"rating_source_row_{index:02d}_sanitized_reason_id_not_allowed")
        readfeel_blocker_ids = dedupe_identifiers(row.get("readfeel_blocker_ids") or (), limit=20, max_length=120)
        if any(item not in P7_R54_AHR09_READFEEL_BLOCKER_ID_OPTION_REFS for item in readfeel_blocker_ids):
            blockers.append(f"rating_source_row_{index:02d}_readfeel_blocker_id_not_allowed")
        execution_blocker_ids = dedupe_identifiers(row.get("execution_blocker_ids") or (), limit=20, max_length=120)
        if any(item not in P7_R54_AHR09_EXECUTION_BLOCKER_ID_OPTION_REFS for item in execution_blocker_ids):
            blockers.append(f"rating_source_row_{index:02d}_execution_blocker_id_not_allowed")
        plan_candidate_flags = _clean_plan_candidate_flags(row.get("plan_candidate_flags"))
        below_target_axis_refs = [
            axis_ref
            for axis_ref in P7_R54_AHR05_RATING_AXIS_REFS
            if axis_scores.get(axis_ref, -1.0) < P7_R54_AHR05_RATING_AXIS_TARGET_THRESHOLDS[axis_ref]
        ]
        rating_row = {
            "schema_version": P7_R54_AHR12_RATING_ROW_SCHEMA_VERSION,
            "review_session_id": review_session_id,
            "rating_row_ref": f"rating_row_{index:03d}",
            "source_review_result_row_ref": clean_identifier(
                row.get("review_result_row_ref"), default=f"review_result_row_{index:03d}", max_length=120
            ),
            "case_ref_id": case_ref_id,
            "blind_case_id": clean_identifier(row.get("blind_case_id"), default="", max_length=120),
            "packet_ref_id": clean_identifier(row.get("packet_ref_id"), default="", max_length=120),
            "family": clean_identifier(row.get("family"), default="", max_length=160),
            "case_role": clean_identifier(row.get("case_role"), default="", max_length=160),
            "axis_scores": axis_scores,
            "axis_score_count": len(P7_R54_AHR05_RATING_AXIS_REFS),
            "axis_targets": dict(P7_R54_AHR05_RATING_AXIS_TARGET_THRESHOLDS),
            "below_target_axis_refs": below_target_axis_refs,
            "below_target_axis_count": len(below_target_axis_refs),
            "verdict": verdict,
            "sanitized_reason_ids": sanitized_reason_ids,
            "readfeel_blocker_ids": readfeel_blocker_ids,
            "execution_blocker_ids": execution_blocker_ids,
            "question_need_primary_class": clean_identifier(row.get("question_need_primary_class"), default="", max_length=160),
            "ambiguity_kind_refs": dedupe_identifiers(row.get("ambiguity_kind_refs") or (), limit=20, max_length=160),
            "one_question_fit_ref": clean_identifier(row.get("one_question_fit_ref"), default="", max_length=160),
            "repair_required_refs": dedupe_identifiers(row.get("repair_required_refs") or (), limit=20, max_length=160),
            "plan_candidate_flags": plan_candidate_flags,
            "body_free": True,
            "reviewer_free_text_included": False,
            "raw_body_included": False,
            "returned_emlis_body_included": False,
            "history_surface_included": False,
            "comment_text_included": False,
            "question_text_included": False,
            "draft_question_text_included": False,
            "local_absolute_path_included": False,
            "body_hash_included": False,
            "packet_content_included": False,
        }
        rating_rows.append(rating_row)
    if len(rows) != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("source_sanitized_review_result_row_count_not_24")
    if len(seen_case_refs) != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("rating_row_case_ref_ids_not_unique_or_not_24")
    if seen_case_refs != expected_case_refs:
        blockers.append("rating_rows_do_not_match_24_case_manifest")
    if blockers:
        return [], dedupe_identifiers(blockers, limit=160, max_length=240)
    return rating_rows, []


def _count_below_target_axes(rating_rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {axis_ref: 0 for axis_ref in P7_R54_AHR05_RATING_AXIS_REFS}
    for row in rating_rows:
        for axis_ref in row.get("below_target_axis_refs") or []:
            axis_key = str(axis_ref)
            if axis_key in counts:
                counts[axis_key] += 1
    return counts


def build_p7_r54_ahr12_rating_row_normalization(
    *,
    sanitized_review_result_intake: Mapping[str, Any] | None = None,
    review_session_id: Any = P7_R54_AHR_DEFAULT_REVIEW_SESSION_ID,
) -> dict[str, Any]:
    """Normalize AHR11 sanitized result rows into body-free P5 rating rows."""

    intake = dict(sanitized_review_result_intake or build_p7_r54_ahr11_sanitized_review_result_row_intake())
    session_id = _safe_review_session_id(review_session_id)
    intake_ready = (
        intake.get("sanitized_review_result_row_intake_status_ref") == P7_R54_AHR11_INTAKE_READY_STATUS_REF
        and intake.get("rating_row_normalization_allowed_next") is True
        and intake.get("sanitized_review_result_row_count") == P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
    )
    rating_rows, row_blockers = _normalize_rating_rows_from_sanitized_results(
        intake.get("review_result_rows") or [], review_session_id=session_id
    ) if intake_ready else ([], ["ahr11_sanitized_review_result_row_intake_not_ready"])
    ready = intake_ready and not row_blockers and len(rating_rows) == P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
    blockers = [] if ready else dedupe_identifiers(row_blockers or ["rating_row_normalization_not_ready"], limit=160, max_length=240)
    status = P7_R54_AHR12_NORMALIZED_STATUS_REF if ready else P7_R54_AHR12_BLOCKED_STATUS_REF
    reason_refs = [P7_R54_AHR12_READY_REASON_REF] if ready else blockers
    rating_row_refs = [str(row.get("rating_row_ref")) for row in rating_rows]
    source_refs = [str(row.get("source_review_result_row_ref")) for row in rating_rows]
    case_refs = [str(row.get("case_ref_id")) for row in rating_rows]
    blind_ids = [str(row.get("blind_case_id")) for row in rating_rows]
    packet_refs = [str(row.get("packet_ref_id")) for row in rating_rows]
    verdict_counts = _count_values(rating_rows, "verdict")
    below_by_case = {str(row.get("case_ref_id")): list(row.get("below_target_axis_refs") or []) for row in rating_rows}
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR12_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_STEP,
        "scope": P7_R54_AHR_SCOPE,
        "policy_kind": P7_R54_AHR_POLICY_KIND,
        "policy_section": P7_R54_AHR12_STEP_REF,
        "operation_step_ref": P7_R54_AHR12_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr12_rating_row_normalization_20260627",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ahr11_schema_version": intake.get("schema_version"),
        "ahr11_material_ref": intake.get("material_id", ""),
        "ahr11_next_required_step": intake.get("next_required_step", ""),
        "ahr11_sanitized_review_result_row_intake_status_ref": intake.get("sanitized_review_result_row_intake_status_ref", ""),
        "ahr11_rating_row_normalization_allowed_next": intake.get("rating_row_normalization_allowed_next") is True,
        "ahr11_sanitized_review_result_row_count": int(intake.get("sanitized_review_result_row_count") or 0),
        "ahr11_review_result_row_count": int(intake.get("review_result_row_count") or 0),
        "ahr11_case_ref_id_count": int(intake.get("case_ref_id_count") or 0),
        "ahr11_actual_human_review_executed_by_person": intake.get("actual_human_review_executed_by_person") is True,
        "current_execution_basis_refs": dict(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "current_execution_basis_ref_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "current_execution_basis_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "current_execution_basis_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_refs": dict(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_ref_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "operation_current_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "required_current_execution_basis_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "required_current_execution_basis_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "all_required_current_execution_basis_refs_present": True,
        "actual_execution_basis_ref": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF,
        "actual_execution_basis_allowed": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_ALLOWED_REF,
        "actual_review_basis_ref": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_ALLOWED_REF,
        "current_execution_basis_refs_are_actual_execution_basis": True,
        "current_execution_basis_refs_used_as_actual_execution_basis": True,
        "operation_current_refs_are_actual_execution_basis": True,
        "operation_current_refs_used_as_actual_execution_basis": True,
        "operation_current_refs_match_current_execution_basis_260_83_256_169": True,
        "current_execution_basis_refs_match_received_snapshot_260_83_256_169": True,
        "current_execution_basis_refs_match_260_83_256_169_snapshot": True,
        "rating_row_normalization_status_ref": status,
        "rating_row_normalization_reason_refs": reason_refs,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "sanitized_review_result_rows_ready_for_rating_normalization": ready,
        "required_case_count": P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "source_sanitized_review_result_row_count": int(intake.get("sanitized_review_result_row_count") or 0) if intake_ready else 0,
        "rating_row_count": len(rating_rows),
        "rating_rows": rating_rows,
        "rating_row_refs": rating_row_refs,
        "rating_row_ref_count": len(rating_row_refs),
        "source_review_result_row_refs": source_refs,
        "source_review_result_row_ref_count": len(source_refs),
        "case_ref_ids": case_refs,
        "case_ref_id_count": len(case_refs),
        "case_ref_ids_unique": len(set(case_refs)) == len(case_refs) == P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "blind_case_ids": blind_ids,
        "blind_case_id_count": len(blind_ids),
        "blind_case_ids_unique": len(set(blind_ids)) == len(blind_ids) == P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "packet_ref_ids": packet_refs,
        "packet_ref_id_count": len(packet_refs),
        "packet_ref_ids_unique": len(set(packet_refs)) == len(packet_refs) == P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "axis_refs": list(P7_R54_AHR05_RATING_AXIS_REFS),
        "axis_count": len(P7_R54_AHR05_RATING_AXIS_REFS),
        "rating_axis_target_thresholds": dict(P7_R54_AHR05_RATING_AXIS_TARGET_THRESHOLDS),
        "rating_rows_bodyfree_only": ready,
        "rating_rows_match_sanitized_review_result_case_refs": ready,
        "rating_rows_have_required_axis_scores": ready,
        "rating_scores_in_range": ready,
        "rating_rows_have_allowed_verdict_refs": ready,
        "below_target_axis_refs_by_case": below_by_case,
        "below_target_axis_ref_counts": _count_below_target_axes(rating_rows),
        "below_target_case_count": sum(1 for row in rating_rows if row.get("below_target_axis_refs")),
        "verdict_counts": verdict_counts,
        "pass_case_count": verdict_counts.get("PASS", 0),
        "yellow_case_count": verdict_counts.get("YELLOW", 0),
        "repair_required_case_count": verdict_counts.get("REPAIR_REQUIRED", 0),
        "red_case_count": verdict_counts.get("RED", 0),
        "blocked_case_count": verdict_counts.get("BLOCKED", 0),
        "not_reviewable_case_count": verdict_counts.get("NOT_REVIEWABLE", 0),
        "readfeel_blocker_row_source_count": sum(len(row.get("readfeel_blocker_ids") or []) for row in rating_rows),
        "execution_blocker_row_source_count": sum(len(row.get("execution_blocker_ids") or []) for row in rating_rows),
        "rating_rows_normalized_here": ready,
        "actual_rating_rows_materialized_here": ready,
        "actual_human_review_executed_by_person": intake.get("actual_human_review_executed_by_person") is True and ready,
        "actual_human_review_run_here": False,
        "actual_review_evidence_complete": False,
        "readfeel_blocker_ingestion_allowed_next": ready,
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
        "implemented_steps": list(P7_R54_AHR12_IMPLEMENTED_STEPS if ready else P7_R54_AHR11_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR12_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR11_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR13_STEP_REF if ready else P7_R54_AHR12_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    _add_false_flags_preserving_allowed(material, allowed_true_refs=P7_R54_AHR12_ALLOWED_TRUE_FALSE_FLAG_REFS)
    return material


def assert_p7_r54_ahr12_rating_row_normalization_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR12_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR12 rating row normalization",
    )
    _assert_bodyfree_no_touch_base_allowing_true_flags(
        data,
        schema_version=P7_R54_AHR12_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        policy_section=P7_R54_AHR12_STEP_REF,
        operation_step_ref=P7_R54_AHR12_STEP_REF,
        source="P7-R54-AHR12 rating row normalization",
        allowed_true_refs=P7_R54_AHR12_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    _assert_current_execution_basis_refs(data, source="P7-R54-AHR12 rating row normalization", actual_basis=True)
    if data.get("ahr11_schema_version") != P7_R54_AHR11_SANITIZED_REVIEW_RESULT_ROW_INTAKE_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR12 must follow AHR11 sanitized review result intake")
    if data.get("rating_row_normalization_status_ref") not in P7_R54_AHR12_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR12 status changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or (), limit=160, max_length=240)
    if blockers != dedupe_identifiers(data.get("open_execution_blocker_ids") or (), limit=160, max_length=240):
        raise ValueError("P7-R54-AHR12 open blockers must match step blockers")
    for key in (
        "actual_human_review_run_here",
        "actual_review_evidence_complete",
        "question_need_observation_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "disposal_receipt_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "p5_human_blind_qa_confirmed_final",
        "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR12 must keep {key}=False")
    ready = data.get("rating_row_normalization_status_ref") == P7_R54_AHR12_NORMALIZED_STATUS_REF
    if ready:
        if blockers:
            raise ValueError("P7-R54-AHR12 ready material must not carry execution blockers")
        for key in (
            "sanitized_review_result_rows_ready_for_rating_normalization",
            "rating_rows_bodyfree_only",
            "rating_rows_match_sanitized_review_result_case_refs",
            "rating_rows_have_required_axis_scores",
            "rating_scores_in_range",
            "rating_rows_have_allowed_verdict_refs",
            "rating_rows_normalized_here",
            "actual_rating_rows_materialized_here",
            "actual_human_review_executed_by_person",
            "readfeel_blocker_ingestion_allowed_next",
            "r52_reintake_claim_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "p5_finalization_blocked_here",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR12 ready material must keep {key}=True")
        for field in (
            "rating_row_count",
            "rating_row_ref_count",
            "source_review_result_row_ref_count",
            "case_ref_id_count",
            "blind_case_id_count",
            "packet_ref_id_count",
        ):
            if data.get(field) != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
                raise ValueError(f"P7-R54-AHR12 {field} changed")
        if tuple(data.get("axis_refs") or ()) != P7_R54_AHR05_RATING_AXIS_REFS:
            raise ValueError("P7-R54-AHR12 axis refs changed")
        if safe_mapping(data.get("rating_axis_target_thresholds")) != P7_R54_AHR05_RATING_AXIS_TARGET_THRESHOLDS:
            raise ValueError("P7-R54-AHR12 target thresholds changed")
        for row in data.get("rating_rows") or []:
            if not isinstance(row, Mapping):
                raise ValueError("P7-R54-AHR12 rating row must be mapping")
            _assert_required_fields(row, required=P7_R54_AHR12_RATING_ROW_REQUIRED_FIELD_REFS, source="P7-R54-AHR12 rating row")
            if row.get("schema_version") != P7_R54_AHR12_RATING_ROW_SCHEMA_VERSION:
                raise ValueError("P7-R54-AHR12 rating row schema changed")
            if row.get("body_free") is not True:
                raise ValueError("P7-R54-AHR12 rating row must be body-free")
            for key in P7_R54_AHR12_RATING_ROW_BODYFREE_FALSE_FLAG_REFS:
                if row.get(key) is not False:
                    raise ValueError(f"P7-R54-AHR12 rating row must keep {key}=False")
            if set(safe_mapping(row.get("axis_scores"))) != set(P7_R54_AHR05_RATING_AXIS_REFS):
                raise ValueError("P7-R54-AHR12 rating row axis refs changed")
            if safe_mapping(row.get("axis_targets")) != P7_R54_AHR05_RATING_AXIS_TARGET_THRESHOLDS:
                raise ValueError("P7-R54-AHR12 rating row axis targets changed")
            if row.get("verdict") not in P7_R54_AHR09_VERDICT_OPTION_REFS:
                raise ValueError("P7-R54-AHR12 rating row verdict changed")
            if any(item not in P7_R54_AHR09_READFEEL_BLOCKER_ID_OPTION_REFS for item in row.get("readfeel_blocker_ids") or []):
                raise ValueError("P7-R54-AHR12 rating row readfeel blocker ref changed")
            if any(item not in P7_R54_AHR09_EXECUTION_BLOCKER_ID_OPTION_REFS for item in row.get("execution_blocker_ids") or []):
                raise ValueError("P7-R54-AHR12 rating row execution blocker ref changed")
        if data.get("rating_row_normalization_reason_refs") != [P7_R54_AHR12_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR12 ready reason changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR12_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR12 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR12_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR12 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR13_STEP_REF:
            raise ValueError("P7-R54-AHR12 next step changed")
    else:
        if data.get("rating_row_normalization_status_ref") != P7_R54_AHR12_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR12 blocked status changed")
        if not blockers:
            raise ValueError("P7-R54-AHR12 blocked material must carry blockers")
        for key in (
            "sanitized_review_result_rows_ready_for_rating_normalization",
            "rating_rows_bodyfree_only",
            "rating_rows_normalized_here",
            "actual_rating_rows_materialized_here",
            "readfeel_blocker_ingestion_allowed_next",
        ):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR12 blocked material must keep {key}=False")
        if data.get("rating_row_count") != 0 or data.get("rating_rows") != []:
            raise ValueError("P7-R54-AHR12 blocked material must not carry rating rows")
        if data.get("next_required_step") != P7_R54_AHR12_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR12 blocked next step changed")
    return True


def _blocker_rows_from_rating_rows(rating_rows: Sequence[Any], *, review_session_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    blockers: list[str] = []
    readfeel_rows: list[dict[str, Any]] = []
    execution_rows: list[dict[str, Any]] = []
    seq = 1
    for index, raw_row in enumerate(rating_rows, start=1):
        if not isinstance(raw_row, Mapping):
            blockers.append(f"rating_row_{index:02d}_not_mapping")
            continue
        if _contains_forbidden_ahr_key(raw_row):
            blockers.append(f"rating_row_{index:02d}_contains_forbidden_body_question_path_hash_key")
            continue
        if _has_forbidden_free_text_key(raw_row):
            blockers.append(f"rating_row_{index:02d}_contains_free_text_blocker_key")
            continue
        row = safe_mapping(raw_row)
        if row.get("schema_version") != P7_R54_AHR12_RATING_ROW_SCHEMA_VERSION:
            blockers.append(f"rating_row_{index:02d}_schema_version_changed")
        readfeel_ids = dedupe_identifiers(row.get("readfeel_blocker_ids") or (), limit=20, max_length=120)
        execution_ids = dedupe_identifiers(row.get("execution_blocker_ids") or (), limit=20, max_length=120)
        for blocker_id in readfeel_ids:
            if blocker_id not in P7_R54_AHR09_READFEEL_BLOCKER_ID_OPTION_REFS:
                blockers.append(f"rating_row_{index:02d}_readfeel_blocker_id_not_allowed")
                continue
            if blocker_id in P7_R54_AHR09_EXECUTION_BLOCKER_ID_OPTION_REFS:
                blockers.append(f"rating_row_{index:02d}_readfeel_blocker_id_crosses_execution_boundary")
                continue
            readfeel_rows.append(
                {
                    "schema_version": P7_R54_AHR13_BLOCKER_ROW_SCHEMA_VERSION,
                    "review_session_id": review_session_id,
                    "blocker_row_ref": f"blocker_row_{seq:03d}",
                    "source_rating_row_ref": clean_identifier(row.get("rating_row_ref"), default=f"rating_row_{index:03d}", max_length=120),
                    "source_review_result_row_ref": clean_identifier(
                        row.get("source_review_result_row_ref"), default=f"review_result_row_{index:03d}", max_length=120
                    ),
                    "case_ref_id": clean_identifier(row.get("case_ref_id"), default="", max_length=120),
                    "blind_case_id": clean_identifier(row.get("blind_case_id"), default="", max_length=120),
                    "packet_ref_id": clean_identifier(row.get("packet_ref_id"), default="", max_length=120),
                    "blocker_kind": P7_R54_AHR13_READFEEL_BLOCKER_KIND_REF,
                    "blocker_id": blocker_id,
                    "blocker_status": P7_R54_AHR13_BLOCKER_STATUS_OPEN_REF,
                    "sanitized_reason_ids": dedupe_identifiers(row.get("sanitized_reason_ids") or (), limit=20, max_length=120),
                    "routes_to": P7_R54_AHR13_READFEEL_ROUTE_REF,
                    "body_free": True,
                    "reviewer_free_text_included": False,
                    "raw_body_included": False,
                    "returned_emlis_body_included": False,
                    "history_surface_included": False,
                    "comment_text_included": False,
                    "question_text_included": False,
                    "draft_question_text_included": False,
                    "local_absolute_path_included": False,
                    "body_hash_included": False,
                    "packet_content_included": False,
                }
            )
            seq += 1
        for blocker_id in execution_ids:
            if blocker_id not in P7_R54_AHR09_EXECUTION_BLOCKER_ID_OPTION_REFS:
                blockers.append(f"rating_row_{index:02d}_execution_blocker_id_not_allowed")
                continue
            if blocker_id in P7_R54_AHR09_READFEEL_BLOCKER_ID_OPTION_REFS:
                blockers.append(f"rating_row_{index:02d}_execution_blocker_id_crosses_readfeel_boundary")
                continue
            execution_rows.append(
                {
                    "schema_version": P7_R54_AHR13_BLOCKER_ROW_SCHEMA_VERSION,
                    "review_session_id": review_session_id,
                    "blocker_row_ref": f"blocker_row_{seq:03d}",
                    "source_rating_row_ref": clean_identifier(row.get("rating_row_ref"), default=f"rating_row_{index:03d}", max_length=120),
                    "source_review_result_row_ref": clean_identifier(
                        row.get("source_review_result_row_ref"), default=f"review_result_row_{index:03d}", max_length=120
                    ),
                    "case_ref_id": clean_identifier(row.get("case_ref_id"), default="", max_length=120),
                    "blind_case_id": clean_identifier(row.get("blind_case_id"), default="", max_length=120),
                    "packet_ref_id": clean_identifier(row.get("packet_ref_id"), default="", max_length=120),
                    "blocker_kind": P7_R54_AHR13_EXECUTION_BLOCKER_KIND_REF,
                    "blocker_id": blocker_id,
                    "blocker_status": P7_R54_AHR13_BLOCKER_STATUS_OPEN_REF,
                    "sanitized_reason_ids": dedupe_identifiers(row.get("sanitized_reason_ids") or (), limit=20, max_length=120),
                    "routes_to": P7_R54_AHR13_EXECUTION_ROUTE_REF,
                    "body_free": True,
                    "reviewer_free_text_included": False,
                    "raw_body_included": False,
                    "returned_emlis_body_included": False,
                    "history_surface_included": False,
                    "comment_text_included": False,
                    "question_text_included": False,
                    "draft_question_text_included": False,
                    "local_absolute_path_included": False,
                    "body_hash_included": False,
                    "packet_content_included": False,
                }
            )
            seq += 1
    return readfeel_rows, execution_rows, dedupe_identifiers(blockers, limit=160, max_length=240)


def build_p7_r54_ahr13_readfeel_blocker_execution_blocker_ingestion(
    *,
    rating_row_normalization: Mapping[str, Any] | None = None,
    review_session_id: Any = P7_R54_AHR_DEFAULT_REVIEW_SESSION_ID,
) -> dict[str, Any]:
    """Ingest readfeel and execution blockers from normalized rating rows separately."""

    rating_material = dict(rating_row_normalization or build_p7_r54_ahr12_rating_row_normalization())
    session_id = _safe_review_session_id(review_session_id)
    rating_ready = (
        rating_material.get("rating_row_normalization_status_ref") == P7_R54_AHR12_NORMALIZED_STATUS_REF
        and rating_material.get("readfeel_blocker_ingestion_allowed_next") is True
        and rating_material.get("rating_row_count") == P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
    )
    readfeel_rows, execution_rows, row_blockers = _blocker_rows_from_rating_rows(
        rating_material.get("rating_rows") or [], review_session_id=session_id
    ) if rating_ready else ([], [], ["ahr12_rating_row_normalization_not_ready"])
    ready = rating_ready and not row_blockers
    step_blockers = [] if ready else dedupe_identifiers(row_blockers or ["blocker_ingestion_not_ready"], limit=160, max_length=240)
    status = P7_R54_AHR13_INGESTED_STATUS_REF if ready else P7_R54_AHR13_BLOCKED_STATUS_REF
    reason_refs = [P7_R54_AHR13_READY_REASON_REF] if ready else step_blockers
    blocker_rows = [*readfeel_rows, *execution_rows]
    readfeel_ids = dedupe_identifiers([row.get("blocker_id") for row in readfeel_rows], limit=80, max_length=120)
    observed_execution_ids = dedupe_identifiers([row.get("blocker_id") for row in execution_rows], limit=80, max_length=120)
    source_rating_refs = [str(row.get("rating_row_ref")) for row in rating_material.get("rating_rows") or []] if ready else []
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR13_READFEEL_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_STEP,
        "scope": P7_R54_AHR_SCOPE,
        "policy_kind": P7_R54_AHR_POLICY_KIND,
        "policy_section": P7_R54_AHR13_STEP_REF,
        "operation_step_ref": P7_R54_AHR13_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr13_readfeel_execution_blocker_ingestion_20260627",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ahr12_schema_version": rating_material.get("schema_version"),
        "ahr12_material_ref": rating_material.get("material_id", ""),
        "ahr12_next_required_step": rating_material.get("next_required_step", ""),
        "ahr12_rating_row_normalization_status_ref": rating_material.get("rating_row_normalization_status_ref", ""),
        "ahr12_rating_row_count": int(rating_material.get("rating_row_count") or 0),
        "ahr12_readfeel_blocker_ingestion_allowed_next": rating_material.get("readfeel_blocker_ingestion_allowed_next") is True,
        "ahr12_actual_rating_rows_materialized_here": rating_material.get("actual_rating_rows_materialized_here") is True,
        "current_execution_basis_refs": dict(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "current_execution_basis_ref_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "current_execution_basis_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "current_execution_basis_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_refs": dict(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_ref_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "operation_current_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "required_current_execution_basis_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "required_current_execution_basis_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "all_required_current_execution_basis_refs_present": True,
        "actual_execution_basis_ref": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF,
        "actual_execution_basis_allowed": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_ALLOWED_REF,
        "actual_review_basis_ref": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_ALLOWED_REF,
        "current_execution_basis_refs_are_actual_execution_basis": True,
        "current_execution_basis_refs_used_as_actual_execution_basis": True,
        "operation_current_refs_are_actual_execution_basis": True,
        "operation_current_refs_used_as_actual_execution_basis": True,
        "operation_current_refs_match_current_execution_basis_260_83_256_169": True,
        "current_execution_basis_refs_match_received_snapshot_260_83_256_169": True,
        "current_execution_basis_refs_match_260_83_256_169_snapshot": True,
        "blocker_ingestion_status_ref": status,
        "blocker_ingestion_reason_refs": reason_refs,
        "execution_blocker_ids": step_blockers,
        "open_execution_blocker_ids": step_blockers,
        "rating_rows_ready_for_blocker_ingestion": ready,
        "required_case_count": P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "rating_row_count": int(rating_material.get("rating_row_count") or 0) if rating_ready else 0,
        "source_rating_row_refs": source_rating_refs,
        "source_rating_row_ref_count": len(source_rating_refs),
        "blocker_rows": blocker_rows,
        "blocker_row_count": len(blocker_rows),
        "readfeel_blocker_rows": readfeel_rows,
        "readfeel_blocker_row_count": len(readfeel_rows),
        "execution_blocker_rows": execution_rows,
        "execution_blocker_row_count": len(execution_rows),
        "open_readfeel_blocker_count": len(readfeel_rows),
        "open_execution_blocker_count": len(execution_rows),
        "observed_readfeel_blocker_ids": readfeel_ids,
        "observed_readfeel_blocker_id_count": len(readfeel_ids),
        "observed_execution_blocker_ids": observed_execution_ids,
        "observed_execution_blocker_id_count": len(observed_execution_ids),
        "readfeel_blocker_ids_are_allowed": ready,
        "execution_blocker_ids_are_allowed": ready,
        "blocker_rows_bodyfree_only": ready,
        "blocker_free_text_included": False,
        "readfeel_execution_blockers_separated": ready,
        "readfeel_blockers_routed_to_p5_repair": ready,
        "readfeel_blockers_routed_to_p8_material": False,
        "readfeel_blockers_not_routed_to_p8_material": ready,
        "execution_blockers_routed_to_operation_blocked": ready,
        "execution_blockers_mixed_into_p5_quality": False,
        "execution_blockers_not_mixed_into_p5_quality": ready,
        "readfeel_blocker_ingestion_completed": ready,
        "execution_blocker_ingestion_completed": ready,
        "question_need_observation_normalization_allowed_next": ready,
        "actual_human_review_executed_by_person": rating_material.get("actual_human_review_executed_by_person") is True and ready,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": rating_material.get("actual_rating_rows_materialized_here") is True and ready,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_review_evidence_complete": False,
        "disposal_receipt_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "implemented_steps": list(P7_R54_AHR13_IMPLEMENTED_STEPS if ready else P7_R54_AHR12_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR13_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR12_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR14_STEP_REF if ready else P7_R54_AHR13_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    _add_false_flags_preserving_allowed(material, allowed_true_refs=P7_R54_AHR13_ALLOWED_TRUE_FALSE_FLAG_REFS)
    return material


def assert_p7_r54_ahr13_readfeel_blocker_execution_blocker_ingestion_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR13_READFEEL_EXECUTION_BLOCKER_INGESTION_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR13 readfeel / execution blocker ingestion",
    )
    _assert_bodyfree_no_touch_base_allowing_true_flags(
        data,
        schema_version=P7_R54_AHR13_READFEEL_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION,
        policy_section=P7_R54_AHR13_STEP_REF,
        operation_step_ref=P7_R54_AHR13_STEP_REF,
        source="P7-R54-AHR13 readfeel / execution blocker ingestion",
        allowed_true_refs=P7_R54_AHR13_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    _assert_current_execution_basis_refs(data, source="P7-R54-AHR13 readfeel / execution blocker ingestion", actual_basis=True)
    if data.get("ahr12_schema_version") != P7_R54_AHR12_RATING_ROW_NORMALIZATION_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR13 must follow AHR12 rating normalization")
    if data.get("blocker_ingestion_status_ref") not in P7_R54_AHR13_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR13 status changed")
    step_blockers = dedupe_identifiers(data.get("execution_blocker_ids") or (), limit=160, max_length=240)
    if step_blockers != dedupe_identifiers(data.get("open_execution_blocker_ids") or (), limit=160, max_length=240):
        raise ValueError("P7-R54-AHR13 open step blockers must match step blockers")
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
        "readfeel_blockers_routed_to_p8_material",
        "execution_blockers_mixed_into_p5_quality",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR13 must keep {key}=False")
    ready = data.get("blocker_ingestion_status_ref") == P7_R54_AHR13_INGESTED_STATUS_REF
    if ready:
        if step_blockers:
            raise ValueError("P7-R54-AHR13 ready material must not carry step blockers")
        for key in (
            "rating_rows_ready_for_blocker_ingestion",
            "readfeel_blocker_ids_are_allowed",
            "execution_blocker_ids_are_allowed",
            "blocker_rows_bodyfree_only",
            "readfeel_execution_blockers_separated",
            "readfeel_blockers_routed_to_p5_repair",
            "readfeel_blockers_not_routed_to_p8_material",
            "execution_blockers_routed_to_operation_blocked",
            "execution_blockers_not_mixed_into_p5_quality",
            "readfeel_blocker_ingestion_completed",
            "execution_blocker_ingestion_completed",
            "question_need_observation_normalization_allowed_next",
            "actual_human_review_executed_by_person",
            "actual_rating_rows_materialized_here",
            "r52_reintake_claim_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "p5_finalization_blocked_here",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR13 ready material must keep {key}=True")
        if data.get("rating_row_count") != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR13 rating row count changed")
        if data.get("source_rating_row_ref_count") != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR13 source rating refs changed")
        if data.get("blocker_row_count") != data.get("readfeel_blocker_row_count") + data.get("execution_blocker_row_count"):
            raise ValueError("P7-R54-AHR13 blocker counts do not add up")
        for row in data.get("blocker_rows") or []:
            if not isinstance(row, Mapping):
                raise ValueError("P7-R54-AHR13 blocker row must be mapping")
            _assert_required_fields(row, required=P7_R54_AHR13_BLOCKER_ROW_REQUIRED_FIELD_REFS, source="P7-R54-AHR13 blocker row")
            if row.get("schema_version") != P7_R54_AHR13_BLOCKER_ROW_SCHEMA_VERSION:
                raise ValueError("P7-R54-AHR13 blocker row schema changed")
            if row.get("body_free") is not True:
                raise ValueError("P7-R54-AHR13 blocker row must be body-free")
            for key in P7_R54_AHR13_BLOCKER_ROW_BODYFREE_FALSE_FLAG_REFS:
                if row.get(key) is not False:
                    raise ValueError(f"P7-R54-AHR13 blocker row must keep {key}=False")
            kind = row.get("blocker_kind")
            blocker_id = row.get("blocker_id")
            if kind == P7_R54_AHR13_READFEEL_BLOCKER_KIND_REF:
                if blocker_id not in P7_R54_AHR09_READFEEL_BLOCKER_ID_OPTION_REFS:
                    raise ValueError("P7-R54-AHR13 readfeel blocker id changed")
                if row.get("routes_to") != P7_R54_AHR13_READFEEL_ROUTE_REF:
                    raise ValueError("P7-R54-AHR13 readfeel blocker route changed")
            elif kind == P7_R54_AHR13_EXECUTION_BLOCKER_KIND_REF:
                if blocker_id not in P7_R54_AHR09_EXECUTION_BLOCKER_ID_OPTION_REFS:
                    raise ValueError("P7-R54-AHR13 execution blocker id changed")
                if row.get("routes_to") != P7_R54_AHR13_EXECUTION_ROUTE_REF:
                    raise ValueError("P7-R54-AHR13 execution blocker route changed")
            else:
                raise ValueError("P7-R54-AHR13 blocker kind changed")
        if data.get("blocker_ingestion_reason_refs") != [P7_R54_AHR13_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR13 ready reason changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR13_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR13 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR13_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR13 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR14_STEP_REF:
            raise ValueError("P7-R54-AHR13 next step changed")
    else:
        if data.get("blocker_ingestion_status_ref") != P7_R54_AHR13_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR13 blocked status changed")
        if not step_blockers:
            raise ValueError("P7-R54-AHR13 blocked material must carry step blockers")
        for key in (
            "rating_rows_ready_for_blocker_ingestion",
            "readfeel_blocker_ids_are_allowed",
            "execution_blocker_ids_are_allowed",
            "blocker_rows_bodyfree_only",
            "readfeel_execution_blockers_separated",
            "readfeel_blocker_ingestion_completed",
            "execution_blocker_ingestion_completed",
            "question_need_observation_normalization_allowed_next",
            "actual_rating_rows_materialized_here",
        ):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR13 blocked material must keep {key}=False")
        if data.get("blocker_rows") != [] or data.get("blocker_row_count") != 0:
            raise ValueError("P7-R54-AHR13 blocked material must not carry blocker rows")
        if data.get("next_required_step") != P7_R54_AHR13_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR13 blocked next step changed")
    return True


build_p7_r54_ahr12_rating_row_normalization_bodyfree = build_p7_r54_ahr12_rating_row_normalization
assert_p7_r54_ahr12_rating_row_normalization_bodyfree_contract = assert_p7_r54_ahr12_rating_row_normalization_contract
build_p7_r54_ahr13_readfeel_blocker_execution_blocker_ingestion_bodyfree = (
    build_p7_r54_ahr13_readfeel_blocker_execution_blocker_ingestion
)
assert_p7_r54_ahr13_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract = (
    assert_p7_r54_ahr13_readfeel_blocker_execution_blocker_ingestion_contract
)
build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr12_rating_row_normalization = (
    build_p7_r54_ahr12_rating_row_normalization
)
assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr12_rating_row_normalization_contract = (
    assert_p7_r54_ahr12_rating_row_normalization_contract
)
build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr13_readfeel_blocker_execution_blocker_ingestion = (
    build_p7_r54_ahr13_readfeel_blocker_execution_blocker_ingestion
)
assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr13_readfeel_blocker_execution_blocker_ingestion_contract = (
    assert_p7_r54_ahr13_readfeel_blocker_execution_blocker_ingestion_contract
)
build_p7_r54_actual_human_review_execution_rating_row_normalization_bodyfree = (
    build_p7_r54_ahr12_rating_row_normalization
)
assert_p7_r54_actual_human_review_execution_rating_row_normalization_bodyfree_contract = (
    assert_p7_r54_ahr12_rating_row_normalization_contract
)
build_p7_r54_actual_human_review_execution_readfeel_execution_blocker_ingestion_bodyfree = (
    build_p7_r54_ahr13_readfeel_blocker_execution_blocker_ingestion
)
assert_p7_r54_actual_human_review_execution_readfeel_execution_blocker_ingestion_bodyfree_contract = (
    assert_p7_r54_ahr13_readfeel_blocker_execution_blocker_ingestion_contract
)


# ---------------------------------------------------------------------------
# R54-AHR14 / R54-AHR15: question observation normalization and consistency
# guard.  These helpers are intentionally appended after AHR12/AHR13 so the
# older aliases and result memos remain historical; no prior helper refs are
# rewritten.

P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR14: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR13[1:]
P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR15: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR14[1:]
P7_R54_AHR14_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_AHR13_IMPLEMENTED_STEPS, P7_R54_AHR14_STEP_REF)
P7_R54_AHR14_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR14
P7_R54_AHR15_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_AHR14_IMPLEMENTED_STEPS, P7_R54_AHR15_STEP_REF)
P7_R54_AHR15_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR15

P7_R54_AHR_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.ahr14_question_need_observation_normalization.bodyfree.v1"
)
P7_R54_AHR_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.ahr15_rating_question_consistency_guard.bodyfree.v1"
)
P7_R54_AHR14_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION: Final = (
    P7_R54_AHR_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION
)
P7_R54_AHR15_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION: Final = (
    P7_R54_AHR_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION
)
P7_R54_AHR14_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.question_need_observation_row.bodyfree.v1"
)
P7_R54_AHR15_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.rating_question_consistency_issue_row.bodyfree.v1"
)

P7_R54_AHR14_NORMALIZED_STATUS_REF: Final = "AHR_QUESTION_NEED_OBSERVATION_NORMALIZED_BODYFREE"
P7_R54_AHR14_BLOCKED_STATUS_REF: Final = "AHR_QUESTION_NEED_OBSERVATION_NORMALIZATION_BLOCKED"
P7_R54_AHR14_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR14_NORMALIZED_STATUS_REF,
    P7_R54_AHR14_BLOCKED_STATUS_REF,
)
P7_R54_AHR14_READY_REASON_REF: Final = "r54_ahr_question_need_observation_rows_normalized_bodyfree"
P7_R54_AHR14_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-14_repair_question_need_observation_normalization_before_consistency_guard"
)

P7_R54_AHR15_PASSED_STATUS_REF: Final = "AHR_RATING_QUESTION_CONSISTENCY_GUARD_PASSED"
P7_R54_AHR15_BLOCKED_STATUS_REF: Final = "AHR_RATING_QUESTION_CONSISTENCY_GUARD_BLOCKED"
P7_R54_AHR15_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR15_PASSED_STATUS_REF,
    P7_R54_AHR15_BLOCKED_STATUS_REF,
)
P7_R54_AHR15_READY_REASON_REF: Final = "r54_ahr_rating_question_consistency_guard_passed_bodyfree"
P7_R54_AHR15_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-15_repair_rating_question_consistency_before_pause_abort_expiration_protocol"
)
P7_R54_AHR15_CONSISTENCY_ROUTE_REF: Final = "R54_AHR_QUESTION_OBSERVATION_CONSISTENCY_REPAIR"

P7_R54_AHR14_P8_MATERIAL_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = (
    "plus_single_question_candidate_later",
    "premium_deep_dive_candidate_later",
)
P7_R54_AHR14_P5_REPAIR_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = (
    "not_question_emlis_readfeel_repair_required",
    "not_question_p5_surface_repair_required",
    "not_question_gate_boundary_required",
)
P7_R54_AHR14_P8_MATERIAL_ONE_QUESTION_FIT_REFS: Final[tuple[str, ...]] = (
    "fits_one_question",
    "needs_more_than_one_question_not_p7",
)
P7_R54_AHR14_NO_REPAIR_REF: Final = "no_repair_required"
P7_R54_AHR14_EXECUTION_BLOCKER_PRIMARY_CLASS_REF: Final = "insufficient_material_execution_blocker"
P7_R54_AHR14_NOT_QUESTION_REPAIR_FIT_REFS: Final[tuple[str, ...]] = (
    "repair_required_not_question",
    "unsafe_or_boundary_not_question",
    "insufficient_material",
)

P7_R54_AHR14_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "actual_human_review_executed_by_person",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
)
P7_R54_AHR15_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = P7_R54_AHR14_ALLOWED_TRUE_FALSE_FLAG_REFS
P7_R54_AHR14_ROW_BODYFREE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = P7_R54_AHR12_RATING_ROW_BODYFREE_FALSE_FLAG_REFS
P7_R54_AHR15_ISSUE_ROW_BODYFREE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = P7_R54_AHR12_RATING_ROW_BODYFREE_FALSE_FLAG_REFS

P7_R54_AHR14_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "question_observation_row_ref",
    "source_rating_row_ref",
    "source_review_result_row_ref",
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
    "family",
    "case_role",
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
    "body_free",
    *P7_R54_AHR14_ROW_BODYFREE_FALSE_FLAG_REFS,
)
P7_R54_AHR15_CONSISTENCY_ISSUE_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "consistency_issue_row_ref",
    "source_question_observation_row_ref",
    "source_rating_row_ref",
    "case_ref_id",
    "issue_id",
    "issue_kind",
    "routes_to",
    "body_free",
    *P7_R54_AHR15_ISSUE_ROW_BODYFREE_FALSE_FLAG_REFS,
)

P7_R54_AHR14_QUESTION_NEED_OBSERVATION_NORMALIZATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_BASE_REQUIRED_FIELD_REFS,
    "ahr13_schema_version",
    "ahr13_material_ref",
    "ahr13_next_required_step",
    "ahr13_blocker_ingestion_status_ref",
    "ahr13_question_need_observation_normalization_allowed_next",
    "ahr13_rating_row_count",
    "ahr13_open_readfeel_blocker_count",
    "ahr13_open_execution_blocker_count",
    "ahr12_schema_version",
    "ahr12_material_ref",
    "ahr12_rating_row_normalization_status_ref",
    "ahr12_rating_row_count",
    "ahr12_actual_rating_rows_materialized_here",
    *P7_R54_AHR_CURRENT_EXECUTION_BASIS_FIELD_REFS,
    "operation_current_refs_match_current_execution_basis_260_83_256_169",
    "current_execution_basis_refs_match_received_snapshot_260_83_256_169",
    "current_execution_basis_refs_match_260_83_256_169_snapshot",
    "question_need_observation_normalization_status_ref",
    "question_need_observation_normalization_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "rating_rows_ready_for_question_observation_normalization",
    "blocker_ingestion_ready_for_question_observation_normalization",
    "required_case_count",
    "source_rating_row_count",
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
    "p8_material_candidate_row_count",
    "plus_single_question_candidate_row_count",
    "premium_deep_dive_candidate_row_count",
    "p5_repair_required_observation_row_count",
    "p4_current_surface_repair_required_row_count",
    "execution_blocker_observation_row_count",
    "readfeel_blocker_observation_row_count",
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
    "question_need_observation_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
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
    "public_contract",
    "r54_ahr_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R54_AHR_FALSE_FLAG_REFS,
)

P7_R54_AHR15_RATING_QUESTION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_BASE_REQUIRED_FIELD_REFS,
    "ahr14_schema_version",
    "ahr14_material_ref",
    "ahr14_next_required_step",
    "ahr14_question_need_observation_normalization_status_ref",
    "ahr14_rating_question_consistency_guard_allowed_next",
    "ahr14_question_need_observation_row_count",
    "ahr14_actual_question_need_observation_rows_materialized_here",
    *P7_R54_AHR_CURRENT_EXECUTION_BASIS_FIELD_REFS,
    "operation_current_refs_match_current_execution_basis_260_83_256_169",
    "current_execution_basis_refs_match_received_snapshot_260_83_256_169",
    "current_execution_basis_refs_match_260_83_256_169_snapshot",
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
    "execution_blocker_observation_row_count",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_review_evidence_complete",
    "disposal_receipt_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "pause_abort_expiration_protocol_allowed_next",
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
    "public_contract",
    "r54_ahr_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R54_AHR_FALSE_FLAG_REFS,
)


def _question_need_observation_rows_from_rating_rows(
    rating_rows: Sequence[Mapping[str, Any]], *, review_session_id: str
) -> tuple[list[dict[str, Any]], list[str]]:
    blockers: list[str] = []
    rows_for_output: list[dict[str, Any]] = []
    expected_case_refs = set(_expected_manifest_rows_by_case_ref())
    seen_case_refs: set[str] = set()
    if len(rating_rows) != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("source_rating_row_count_not_24")
    for index, raw_row in enumerate(rating_rows, start=1):
        if not isinstance(raw_row, Mapping):
            blockers.append(f"question_observation_source_rating_row_{index:02d}_not_mapping")
            continue
        row = safe_mapping(raw_row)
        if _contains_forbidden_ahr_key(row):
            blockers.append(f"question_observation_source_rating_row_{index:02d}_contains_forbidden_body_question_path_hash_key")
        if row.get("schema_version") != P7_R54_AHR12_RATING_ROW_SCHEMA_VERSION:
            blockers.append(f"question_observation_source_rating_row_{index:02d}_schema_version_changed")
        case_ref_id = clean_identifier(row.get("case_ref_id"), default="", max_length=120)
        if case_ref_id not in expected_case_refs:
            blockers.append(f"question_observation_source_rating_row_{index:02d}_case_ref_not_in_manifest")
        seen_case_refs.add(case_ref_id)
        primary_class = clean_identifier(row.get("question_need_primary_class"), default="", max_length=160)
        if primary_class not in P7_R54_AHR09_QUESTION_NEED_PRIMARY_CLASS_REFS:
            blockers.append(f"question_observation_source_rating_row_{index:02d}_primary_class_not_allowed")
        ambiguity_kind_refs = dedupe_identifiers(row.get("ambiguity_kind_refs") or (), limit=20, max_length=120)
        if not ambiguity_kind_refs:
            blockers.append(f"question_observation_source_rating_row_{index:02d}_ambiguity_kind_refs_missing")
        if any(item not in P7_R54_AHR09_AMBIGUITY_KIND_OPTION_REFS for item in ambiguity_kind_refs):
            blockers.append(f"question_observation_source_rating_row_{index:02d}_ambiguity_kind_ref_not_allowed")
        one_question_fit_ref = clean_identifier(row.get("one_question_fit_ref"), default="", max_length=160)
        if one_question_fit_ref not in P7_R54_AHR09_ONE_QUESTION_FIT_OPTION_REFS:
            blockers.append(f"question_observation_source_rating_row_{index:02d}_one_question_fit_ref_not_allowed")
        repair_required_refs = dedupe_identifiers(row.get("repair_required_refs") or (), limit=20, max_length=160)
        if not repair_required_refs:
            blockers.append(f"question_observation_source_rating_row_{index:02d}_repair_required_refs_missing")
        if any(item not in P7_R54_AHR09_REPAIR_REQUIRED_OPTION_REFS for item in repair_required_refs):
            blockers.append(f"question_observation_source_rating_row_{index:02d}_repair_required_ref_not_allowed")
        raw_plan_flags = safe_mapping(row.get("plan_candidate_flags"))
        if raw_plan_flags.get("p8_implementation_spec_finalized_here") is True:
            blockers.append(f"question_observation_source_rating_row_{index:02d}_p8_implementation_spec_finalized_here")
        plan_candidate_flags = _clean_plan_candidate_flags(raw_plan_flags)
        verdict = clean_identifier(row.get("verdict"), default="", max_length=80)
        if verdict not in P7_R54_AHR09_VERDICT_OPTION_REFS:
            blockers.append(f"question_observation_source_rating_row_{index:02d}_verdict_not_allowed")
        readfeel_blocker_ids = dedupe_identifiers(row.get("readfeel_blocker_ids") or (), limit=20, max_length=120)
        if any(item not in P7_R54_AHR09_READFEEL_BLOCKER_ID_OPTION_REFS for item in readfeel_blocker_ids):
            blockers.append(f"question_observation_source_rating_row_{index:02d}_readfeel_blocker_id_not_allowed")
        execution_blocker_ids = dedupe_identifiers(row.get("execution_blocker_ids") or (), limit=20, max_length=120)
        if any(item not in P7_R54_AHR09_EXECUTION_BLOCKER_ID_OPTION_REFS for item in execution_blocker_ids):
            blockers.append(f"question_observation_source_rating_row_{index:02d}_execution_blocker_id_not_allowed")
        p5_repair_required = any(
            ref in repair_required_refs
            for ref in ("emlis_readfeel_repair_required", "p5_surface_repair_required")
        ) or primary_class in (
            "not_question_emlis_readfeel_repair_required",
            "not_question_p5_surface_repair_required",
        )
        p4_current_repair_required = "p4_current_surface_repair_required" in repair_required_refs
        gate_boundary_repair_required = "gate_boundary_repair_required" in repair_required_refs
        emlis_readfeel_repair_required = "emlis_readfeel_repair_required" in repair_required_refs
        execution_blocker_present = bool(execution_blocker_ids) or primary_class == P7_R54_AHR14_EXECUTION_BLOCKER_PRIMARY_CLASS_REF
        readfeel_blocker_present = bool(readfeel_blocker_ids)
        plus_candidate = (
            primary_class == "plus_single_question_candidate_later"
            and plan_candidate_flags.get("plus_single_question_candidate_later") is True
            and one_question_fit_ref == "fits_one_question"
        )
        premium_candidate = (
            primary_class == "premium_deep_dive_candidate_later"
            and plan_candidate_flags.get("premium_deep_dive_candidate_later") is True
            and one_question_fit_ref in P7_R54_AHR14_P8_MATERIAL_ONE_QUESTION_FIT_REFS
        )
        p8_material_candidate = (
            plan_candidate_flags.get("p8_design_material_candidate") is True
            and primary_class in P7_R54_AHR14_P8_MATERIAL_PRIMARY_CLASS_REFS
            and one_question_fit_ref in P7_R54_AHR14_P8_MATERIAL_ONE_QUESTION_FIT_REFS
            and not p5_repair_required
            and not p4_current_repair_required
            and not execution_blocker_present
            and not readfeel_blocker_present
            and verdict not in {"RED", "REPAIR_REQUIRED", "BLOCKED", "NOT_REVIEWABLE"}
        )
        rows_for_output.append(
            {
                "schema_version": P7_R54_AHR14_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION,
                "review_session_id": review_session_id,
                "question_observation_row_ref": f"question_observation_row_{index:03d}",
                "source_rating_row_ref": clean_identifier(row.get("rating_row_ref"), default=f"rating_row_{index:03d}", max_length=120),
                "source_review_result_row_ref": clean_identifier(
                    row.get("source_review_result_row_ref"), default=f"review_result_row_{index:03d}", max_length=120
                ),
                "case_ref_id": case_ref_id,
                "blind_case_id": clean_identifier(row.get("blind_case_id"), default="", max_length=120),
                "packet_ref_id": clean_identifier(row.get("packet_ref_id"), default="", max_length=120),
                "family": clean_identifier(row.get("family"), default="", max_length=160),
                "case_role": clean_identifier(row.get("case_role"), default="", max_length=160),
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
                "body_free": True,
                "reviewer_free_text_included": False,
                "raw_body_included": False,
                "returned_emlis_body_included": False,
                "history_surface_included": False,
                "comment_text_included": False,
                "question_text_included": False,
                "draft_question_text_included": False,
                "local_absolute_path_included": False,
                "body_hash_included": False,
                "packet_content_included": False,
            }
        )
    if len(seen_case_refs) != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("question_observation_case_ref_ids_not_unique_or_not_24")
    if seen_case_refs != expected_case_refs:
        blockers.append("question_observation_rows_do_not_match_24_case_manifest")
    if blockers:
        return [], dedupe_identifiers(blockers, limit=200, max_length=260)
    return rows_for_output, []


def _count_nested_refs(rows: Sequence[Mapping[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        for value in row.get(field) or []:
            key = str(value)
            counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def build_p7_r54_ahr14_question_need_observation_normalization(
    *,
    blocker_ingestion: Mapping[str, Any] | None = None,
    rating_row_normalization: Mapping[str, Any] | None = None,
    review_session_id: Any = P7_R54_AHR_DEFAULT_REVIEW_SESSION_ID,
) -> dict[str, Any]:
    """Normalize review-derived question need observations as body-free rows."""

    blocker_material = dict(blocker_ingestion or build_p7_r54_ahr13_readfeel_blocker_execution_blocker_ingestion())
    rating_material = dict(rating_row_normalization or {})
    session_id = _safe_review_session_id(review_session_id)
    blocker_ready = (
        blocker_material.get("blocker_ingestion_status_ref") == P7_R54_AHR13_INGESTED_STATUS_REF
        and blocker_material.get("question_need_observation_normalization_allowed_next") is True
        and blocker_material.get("next_required_step") == P7_R54_AHR14_STEP_REF
    )
    rating_ready = (
        rating_material.get("rating_row_normalization_status_ref") == P7_R54_AHR12_NORMALIZED_STATUS_REF
        and rating_material.get("rating_row_count") == P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and rating_material.get("actual_rating_rows_materialized_here") is True
    )
    rows, row_blockers = _question_need_observation_rows_from_rating_rows(
        rating_material.get("rating_rows") or [], review_session_id=session_id
    ) if blocker_ready and rating_ready else ([], [])
    blockers: list[str] = []
    if not blocker_ready:
        blockers.append("ahr13_blocker_ingestion_not_ready")
    if not rating_ready:
        blockers.append("ahr12_rating_row_normalization_not_ready_for_question_observation")
    blockers.extend(row_blockers)
    ready = blocker_ready and rating_ready and not blockers
    step_blockers = [] if ready else dedupe_identifiers(blockers or ["question_need_observation_normalization_not_ready"], limit=200, max_length=260)
    status = P7_R54_AHR14_NORMALIZED_STATUS_REF if ready else P7_R54_AHR14_BLOCKED_STATUS_REF
    reason_refs = [P7_R54_AHR14_READY_REASON_REF] if ready else step_blockers
    rows_for_counts = rows if ready else []
    row_refs = [str(row.get("question_observation_row_ref")) for row in rows_for_counts]
    rating_refs = [str(row.get("source_rating_row_ref")) for row in rows_for_counts]
    case_refs = [str(row.get("case_ref_id")) for row in rows_for_counts]
    p8_material_count = sum(1 for row in rows_for_counts if row.get("p8_design_material_candidate") is True)
    plus_count = sum(1 for row in rows_for_counts if row.get("plus_single_question_candidate_later") is True)
    premium_count = sum(1 for row in rows_for_counts if row.get("premium_deep_dive_candidate_later") is True)
    p5_repair_count = sum(1 for row in rows_for_counts if row.get("p5_repair_required") is True)
    p4_repair_count = sum(1 for row in rows_for_counts if row.get("p4_current_surface_repair_required") is True)
    execution_count = sum(1 for row in rows_for_counts if row.get("execution_blocker_present") is True)
    readfeel_count = sum(1 for row in rows_for_counts if row.get("readfeel_blocker_present") is True)
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR14_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_STEP,
        "scope": P7_R54_AHR_SCOPE,
        "policy_kind": P7_R54_AHR_POLICY_KIND,
        "policy_section": P7_R54_AHR14_STEP_REF,
        "operation_step_ref": P7_R54_AHR14_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr14_question_need_observation_normalization_20260627",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ahr13_schema_version": blocker_material.get("schema_version"),
        "ahr13_material_ref": blocker_material.get("material_id", ""),
        "ahr13_next_required_step": blocker_material.get("next_required_step", ""),
        "ahr13_blocker_ingestion_status_ref": blocker_material.get("blocker_ingestion_status_ref", ""),
        "ahr13_question_need_observation_normalization_allowed_next": blocker_material.get("question_need_observation_normalization_allowed_next") is True,
        "ahr13_rating_row_count": int(blocker_material.get("rating_row_count") or 0),
        "ahr13_open_readfeel_blocker_count": int(blocker_material.get("open_readfeel_blocker_count") or 0),
        "ahr13_open_execution_blocker_count": int(blocker_material.get("open_execution_blocker_count") or 0),
        "ahr12_schema_version": rating_material.get("schema_version", ""),
        "ahr12_material_ref": rating_material.get("material_id", ""),
        "ahr12_rating_row_normalization_status_ref": rating_material.get("rating_row_normalization_status_ref", ""),
        "ahr12_rating_row_count": int(rating_material.get("rating_row_count") or 0),
        "ahr12_actual_rating_rows_materialized_here": rating_material.get("actual_rating_rows_materialized_here") is True,
        "current_execution_basis_refs": dict(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "current_execution_basis_ref_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "current_execution_basis_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "current_execution_basis_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_refs": dict(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_ref_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "operation_current_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "required_current_execution_basis_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "required_current_execution_basis_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "all_required_current_execution_basis_refs_present": True,
        "actual_execution_basis_ref": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF,
        "actual_execution_basis_allowed": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_ALLOWED_REF,
        "actual_review_basis_ref": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_ALLOWED_REF,
        "current_execution_basis_refs_are_actual_execution_basis": True,
        "current_execution_basis_refs_used_as_actual_execution_basis": True,
        "operation_current_refs_are_actual_execution_basis": True,
        "operation_current_refs_used_as_actual_execution_basis": True,
        "operation_current_refs_match_current_execution_basis_260_83_256_169": True,
        "current_execution_basis_refs_match_received_snapshot_260_83_256_169": True,
        "current_execution_basis_refs_match_260_83_256_169_snapshot": True,
        "question_need_observation_normalization_status_ref": status,
        "question_need_observation_normalization_reason_refs": reason_refs,
        "execution_blocker_ids": step_blockers,
        "open_execution_blocker_ids": step_blockers,
        "rating_rows_ready_for_question_observation_normalization": ready,
        "blocker_ingestion_ready_for_question_observation_normalization": blocker_ready and not step_blockers,
        "required_case_count": P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "source_rating_row_count": int(rating_material.get("rating_row_count") or 0) if rating_ready else 0,
        "question_need_observation_row_count": len(rows_for_counts),
        "actual_question_need_observation_row_count": len(rows_for_counts),
        "question_need_observation_rows": rows_for_counts,
        "question_need_observation_row_refs": row_refs,
        "question_need_observation_row_ref_count": len(row_refs),
        "source_rating_row_refs": rating_refs,
        "source_rating_row_ref_count": len(rating_refs),
        "case_ref_ids": case_refs,
        "case_ref_id_count": len(case_refs),
        "case_ref_ids_unique": len(case_refs) == len(set(case_refs)) == P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT if ready else False,
        "question_need_primary_class_counts": _count_values(rows_for_counts, "question_need_primary_class"),
        "ambiguity_kind_ref_counts": _count_nested_refs(rows_for_counts, "ambiguity_kind_refs"),
        "one_question_fit_ref_counts": _count_values(rows_for_counts, "one_question_fit_ref"),
        "repair_required_ref_counts": _count_nested_refs(rows_for_counts, "repair_required_refs"),
        "p8_material_candidate_row_count": p8_material_count,
        "plus_single_question_candidate_row_count": plus_count,
        "premium_deep_dive_candidate_row_count": premium_count,
        "p5_repair_required_observation_row_count": p5_repair_count,
        "p4_current_surface_repair_required_row_count": p4_repair_count,
        "execution_blocker_observation_row_count": execution_count,
        "readfeel_blocker_observation_row_count": readfeel_count,
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
        "question_need_observation_rows_materialized_here": ready,
        "actual_question_need_observation_rows_materialized_here": ready,
        "actual_human_review_executed_by_person": blocker_material.get("actual_human_review_executed_by_person") is True and ready,
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
        "implemented_steps": list(P7_R54_AHR14_IMPLEMENTED_STEPS if ready else P7_R54_AHR13_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR14_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR13_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR15_STEP_REF if ready else P7_R54_AHR14_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    _add_false_flags_preserving_allowed(material, allowed_true_refs=P7_R54_AHR14_ALLOWED_TRUE_FALSE_FLAG_REFS)
    return material


def assert_p7_r54_ahr14_question_need_observation_normalization_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR14_QUESTION_NEED_OBSERVATION_NORMALIZATION_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR14 question need observation normalization",
    )
    _assert_bodyfree_no_touch_base_allowing_true_flags(
        data,
        schema_version=P7_R54_AHR14_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION,
        policy_section=P7_R54_AHR14_STEP_REF,
        operation_step_ref=P7_R54_AHR14_STEP_REF,
        source="P7-R54-AHR14 question need observation normalization",
        allowed_true_refs=P7_R54_AHR14_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    _assert_current_execution_basis_refs(data, source="P7-R54-AHR14 question need observation normalization", actual_basis=True)
    if data.get("ahr13_schema_version") != P7_R54_AHR13_READFEEL_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR14 must follow AHR13 blocker ingestion")
    if data.get("question_need_observation_normalization_status_ref") not in P7_R54_AHR14_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR14 status changed")
    step_blockers = dedupe_identifiers(data.get("execution_blocker_ids") or (), limit=200, max_length=260)
    if step_blockers != dedupe_identifiers(data.get("open_execution_blocker_ids") or (), limit=200, max_length=260):
        raise ValueError("P7-R54-AHR14 open step blockers must match step blockers")
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
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR14 must keep {key}=False")
    ready = data.get("question_need_observation_normalization_status_ref") == P7_R54_AHR14_NORMALIZED_STATUS_REF
    if ready:
        if step_blockers:
            raise ValueError("P7-R54-AHR14 ready material must not carry step blockers")
        for key in (
            "rating_rows_ready_for_question_observation_normalization",
            "blocker_ingestion_ready_for_question_observation_normalization",
            "question_observation_rows_bodyfree_only",
            "question_observation_rows_from_actual_review_only",
            "question_observation_rows_have_allowed_primary_class_refs",
            "question_observation_rows_have_allowed_ambiguity_kind_refs",
            "question_observation_rows_have_allowed_one_question_fit_refs",
            "question_observation_rows_have_allowed_repair_required_refs",
            "p5_repair_required_rows_excluded_from_p8_material",
            "p4_current_surface_repair_rows_excluded_from_p8_material",
            "execution_blocker_rows_excluded_from_p8_material",
            "question_need_observation_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_human_review_executed_by_person",
            "actual_rating_rows_materialized_here",
            "rating_question_consistency_guard_allowed_next",
            "r52_reintake_claim_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "p5_finalization_blocked_here",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR14 ready material must keep {key}=True")
        if data.get("question_need_observation_row_count") != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR14 row count changed")
        if data.get("actual_question_need_observation_row_count") != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR14 actual row count changed")
        if data.get("source_rating_row_ref_count") != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR14 source rating row refs changed")
        if data.get("case_ref_ids_unique") is not True:
            raise ValueError("P7-R54-AHR14 case refs must be unique")
        for row in data.get("question_need_observation_rows") or []:
            if not isinstance(row, Mapping):
                raise ValueError("P7-R54-AHR14 question observation row must be mapping")
            _assert_required_fields(
                row,
                required=P7_R54_AHR14_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS,
                source="P7-R54-AHR14 question observation row",
            )
            if row.get("schema_version") != P7_R54_AHR14_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION:
                raise ValueError("P7-R54-AHR14 question observation row schema changed")
            if row.get("body_free") is not True:
                raise ValueError("P7-R54-AHR14 question observation row must be body-free")
            for key in P7_R54_AHR14_ROW_BODYFREE_FALSE_FLAG_REFS:
                if row.get(key) is not False:
                    raise ValueError(f"P7-R54-AHR14 question observation row must keep {key}=False")
            if row.get("question_need_primary_class") not in P7_R54_AHR09_QUESTION_NEED_PRIMARY_CLASS_REFS:
                raise ValueError("P7-R54-AHR14 primary class changed")
            if any(item not in P7_R54_AHR09_AMBIGUITY_KIND_OPTION_REFS for item in row.get("ambiguity_kind_refs") or []):
                raise ValueError("P7-R54-AHR14 ambiguity kind refs changed")
            if row.get("one_question_fit_ref") not in P7_R54_AHR09_ONE_QUESTION_FIT_OPTION_REFS:
                raise ValueError("P7-R54-AHR14 one question fit ref changed")
            if any(item not in P7_R54_AHR09_REPAIR_REQUIRED_OPTION_REFS for item in row.get("repair_required_refs") or []):
                raise ValueError("P7-R54-AHR14 repair refs changed")
            if row.get("p8_implementation_spec_finalized_here") is not False:
                raise ValueError("P7-R54-AHR14 must not finalize P8 spec")
            if row.get("p8_design_material_candidate") is True and (
                row.get("p5_repair_required") is True
                or row.get("p4_current_surface_repair_required") is True
                or row.get("execution_blocker_present") is True
                or row.get("readfeel_blocker_present") is True
            ):
                raise ValueError("P7-R54-AHR14 repair/blocker row cannot be P8 material")
        if data.get("question_need_observation_normalization_reason_refs") != [P7_R54_AHR14_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR14 ready reason changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR14_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR14 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR14_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR14 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR15_STEP_REF:
            raise ValueError("P7-R54-AHR14 next step changed")
    else:
        if data.get("question_need_observation_normalization_status_ref") != P7_R54_AHR14_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR14 blocked status changed")
        if not step_blockers:
            raise ValueError("P7-R54-AHR14 blocked material must carry blockers")
        for key in (
            "rating_rows_ready_for_question_observation_normalization",
            "question_need_observation_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_rating_rows_materialized_here",
            "rating_question_consistency_guard_allowed_next",
        ):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR14 blocked material must keep {key}=False")
        if data.get("question_need_observation_rows") != [] or data.get("question_need_observation_row_count") != 0:
            raise ValueError("P7-R54-AHR14 blocked material must not carry observation rows")
        if data.get("next_required_step") != P7_R54_AHR14_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR14 blocked next step changed")
    return True


def _rating_question_consistency_issue_rows(
    question_rows: Sequence[Mapping[str, Any]], *, review_session_id: str
) -> list[dict[str, Any]]:
    issue_rows: list[dict[str, Any]] = []

    def add_issue(source_row: Mapping[str, Any], issue_id: str, issue_kind: str) -> None:
        issue_index = len(issue_rows) + 1
        issue_rows.append(
            {
                "schema_version": P7_R54_AHR15_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION,
                "review_session_id": review_session_id,
                "consistency_issue_row_ref": f"consistency_issue_row_{issue_index:03d}",
                "source_question_observation_row_ref": clean_identifier(
                    source_row.get("question_observation_row_ref"), default=f"question_observation_row_{issue_index:03d}", max_length=120
                ),
                "source_rating_row_ref": clean_identifier(source_row.get("source_rating_row_ref"), default="", max_length=120),
                "case_ref_id": clean_identifier(source_row.get("case_ref_id"), default="", max_length=120),
                "issue_id": issue_id,
                "issue_kind": issue_kind,
                "routes_to": P7_R54_AHR15_CONSISTENCY_ROUTE_REF,
                "body_free": True,
                "reviewer_free_text_included": False,
                "raw_body_included": False,
                "returned_emlis_body_included": False,
                "history_surface_included": False,
                "comment_text_included": False,
                "question_text_included": False,
                "draft_question_text_included": False,
                "local_absolute_path_included": False,
                "body_hash_included": False,
                "packet_content_included": False,
            }
        )

    for index, raw_row in enumerate(question_rows, start=1):
        if not isinstance(raw_row, Mapping):
            add_issue({"question_observation_row_ref": f"question_observation_row_{index:03d}"}, "question_observation_row_not_mapping", "shape_violation")
            continue
        row = safe_mapping(raw_row)
        if _contains_forbidden_ahr_key(row):
            add_issue(row, "forbidden_body_question_path_hash_key_present", "bodyfree_boundary_violation")
        if row.get("schema_version") != P7_R54_AHR14_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION:
            add_issue(row, "question_observation_row_schema_changed", "shape_violation")
        if row.get("question_text_included") is not False or row.get("draft_question_text_included") is not False:
            add_issue(row, "question_or_draft_text_included", "question_text_leak")
        if row.get("p8_implementation_spec_finalized_here") is not False:
            add_issue(row, "p8_implementation_spec_finalized_here", "p8_boundary_violation")
        primary_class = clean_identifier(row.get("question_need_primary_class"), default="", max_length=160)
        one_question_fit_ref = clean_identifier(row.get("one_question_fit_ref"), default="", max_length=160)
        repair_refs = set(dedupe_identifiers(row.get("repair_required_refs") or (), limit=20, max_length=160))
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
        if "p5_surface_repair_required" in repair_refs and primary_class == "no_question_needed_emlis_can_observe":
            add_issue(row, "p5_surface_repair_required_misclassified_as_no_question_needed", "rating_question_contradiction")
        if repair_refs - {P7_R54_AHR14_NO_REPAIR_REF} and p8_candidate:
            add_issue(row, "repair_required_row_routed_to_p8_material", "rating_question_contradiction")
        if primary_class in P7_R54_AHR14_P5_REPAIR_PRIMARY_CLASS_REFS and p8_candidate:
            add_issue(row, "p5_repair_primary_class_routed_to_p8_material", "rating_question_contradiction")
        if primary_class in P7_R54_AHR14_P8_MATERIAL_PRIMARY_CLASS_REFS and one_question_fit_ref not in P7_R54_AHR14_P8_MATERIAL_ONE_QUESTION_FIT_REFS:
            add_issue(row, "p8_material_primary_class_without_allowed_question_fit", "rating_question_contradiction")
    return issue_rows


def build_p7_r54_ahr15_rating_question_consistency_guard(
    *,
    question_need_observation_normalization: Mapping[str, Any] | None = None,
    review_session_id: Any = P7_R54_AHR_DEFAULT_REVIEW_SESSION_ID,
) -> dict[str, Any]:
    """Guard consistency between rating rows and normalized question observations."""

    question_material = dict(question_need_observation_normalization or build_p7_r54_ahr14_question_need_observation_normalization())
    session_id = _safe_review_session_id(review_session_id)
    question_ready = (
        question_material.get("question_need_observation_normalization_status_ref") == P7_R54_AHR14_NORMALIZED_STATUS_REF
        and question_material.get("rating_question_consistency_guard_allowed_next") is True
        and question_material.get("question_need_observation_row_count") == P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
    )
    issue_rows = _rating_question_consistency_issue_rows(
        question_material.get("question_need_observation_rows") or [], review_session_id=session_id
    ) if question_ready else []
    blockers: list[str] = []
    if not question_ready:
        blockers.append("ahr14_question_need_observation_normalization_not_ready")
    blockers.extend(str(row.get("issue_id")) for row in issue_rows)
    ready = question_ready and not issue_rows and not blockers
    step_blockers = [] if ready else dedupe_identifiers(blockers or ["rating_question_consistency_guard_not_ready"], limit=200, max_length=260)
    status = P7_R54_AHR15_PASSED_STATUS_REF if ready else P7_R54_AHR15_BLOCKED_STATUS_REF
    reason_refs = [P7_R54_AHR15_READY_REASON_REF] if ready else step_blockers
    question_rows = list(question_material.get("question_need_observation_rows") or []) if question_ready else []
    question_row_refs = [str(row.get("question_observation_row_ref")) for row in question_rows]
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR15_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_STEP,
        "scope": P7_R54_AHR_SCOPE,
        "policy_kind": P7_R54_AHR_POLICY_KIND,
        "policy_section": P7_R54_AHR15_STEP_REF,
        "operation_step_ref": P7_R54_AHR15_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr15_rating_question_consistency_guard_20260627",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ahr14_schema_version": question_material.get("schema_version"),
        "ahr14_material_ref": question_material.get("material_id", ""),
        "ahr14_next_required_step": question_material.get("next_required_step", ""),
        "ahr14_question_need_observation_normalization_status_ref": question_material.get(
            "question_need_observation_normalization_status_ref", ""
        ),
        "ahr14_rating_question_consistency_guard_allowed_next": question_material.get("rating_question_consistency_guard_allowed_next") is True,
        "ahr14_question_need_observation_row_count": int(question_material.get("question_need_observation_row_count") or 0),
        "ahr14_actual_question_need_observation_rows_materialized_here": question_material.get(
            "actual_question_need_observation_rows_materialized_here"
        ) is True,
        "current_execution_basis_refs": dict(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "current_execution_basis_ref_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "current_execution_basis_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "current_execution_basis_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_refs": dict(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_ref_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "operation_current_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "required_current_execution_basis_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "required_current_execution_basis_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "all_required_current_execution_basis_refs_present": True,
        "actual_execution_basis_ref": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF,
        "actual_execution_basis_allowed": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_ALLOWED_REF,
        "actual_review_basis_ref": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_ALLOWED_REF,
        "current_execution_basis_refs_are_actual_execution_basis": True,
        "current_execution_basis_refs_used_as_actual_execution_basis": True,
        "operation_current_refs_are_actual_execution_basis": True,
        "operation_current_refs_used_as_actual_execution_basis": True,
        "operation_current_refs_match_current_execution_basis_260_83_256_169": True,
        "current_execution_basis_refs_match_received_snapshot_260_83_256_169": True,
        "current_execution_basis_refs_match_260_83_256_169_snapshot": True,
        "consistency_guard_status_ref": status,
        "consistency_guard_reason_refs": reason_refs,
        "execution_blocker_ids": step_blockers,
        "open_execution_blocker_ids": step_blockers,
        "question_rows_ready_for_consistency_guard": question_ready,
        "required_case_count": P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "question_need_observation_row_count": len(question_rows),
        "question_need_observation_row_refs": question_row_refs,
        "question_need_observation_row_ref_count": len(question_row_refs),
        "consistency_issue_rows": issue_rows,
        "consistency_issue_row_count": len(issue_rows),
        "consistency_issue_ids": dedupe_identifiers([row.get("issue_id") for row in issue_rows], limit=200, max_length=160),
        "consistency_issue_id_count": len(dedupe_identifiers([row.get("issue_id") for row in issue_rows], limit=200, max_length=160)),
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
        "execution_blocker_observation_row_count": int(question_material.get("execution_blocker_observation_row_count") or 0) if question_ready else 0,
        "actual_human_review_executed_by_person": question_material.get("actual_human_review_executed_by_person") is True and question_ready,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": question_material.get("actual_rating_rows_materialized_here") is True and question_ready,
        "actual_question_need_observation_rows_materialized_here": question_material.get(
            "actual_question_need_observation_rows_materialized_here"
        ) is True and question_ready,
        "actual_review_evidence_complete": False,
        "disposal_receipt_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "pause_abort_expiration_protocol_allowed_next": ready,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "implemented_steps": list(P7_R54_AHR15_IMPLEMENTED_STEPS if ready else P7_R54_AHR14_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR15_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR14_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR16_STEP_REF if ready else P7_R54_AHR15_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    _add_false_flags_preserving_allowed(material, allowed_true_refs=P7_R54_AHR15_ALLOWED_TRUE_FALSE_FLAG_REFS)
    return material


def assert_p7_r54_ahr15_rating_question_consistency_guard_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR15_RATING_QUESTION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR15 rating / question consistency guard",
    )
    _assert_bodyfree_no_touch_base_allowing_true_flags(
        data,
        schema_version=P7_R54_AHR15_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        policy_section=P7_R54_AHR15_STEP_REF,
        operation_step_ref=P7_R54_AHR15_STEP_REF,
        source="P7-R54-AHR15 rating / question consistency guard",
        allowed_true_refs=P7_R54_AHR15_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    _assert_current_execution_basis_refs(data, source="P7-R54-AHR15 rating / question consistency guard", actual_basis=True)
    if data.get("ahr14_schema_version") != P7_R54_AHR14_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR15 must follow AHR14 question observation normalization")
    if data.get("consistency_guard_status_ref") not in P7_R54_AHR15_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR15 status changed")
    step_blockers = dedupe_identifiers(data.get("execution_blocker_ids") or (), limit=200, max_length=260)
    if step_blockers != dedupe_identifiers(data.get("open_execution_blocker_ids") or (), limit=200, max_length=260):
        raise ValueError("P7-R54-AHR15 open step blockers must match step blockers")
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
            raise ValueError(f"P7-R54-AHR15 must keep {key}=False")
    ready = data.get("consistency_guard_status_ref") == P7_R54_AHR15_PASSED_STATUS_REF
    if ready:
        if step_blockers:
            raise ValueError("P7-R54-AHR15 ready material must not carry blockers")
        if data.get("consistency_issue_rows") != [] or data.get("consistency_issue_row_count") != 0:
            raise ValueError("P7-R54-AHR15 passed material must not carry consistency issues")
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
            "actual_human_review_executed_by_person",
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "pause_abort_expiration_protocol_allowed_next",
            "r52_reintake_claim_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "p5_finalization_blocked_here",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR15 ready material must keep {key}=True")
        if data.get("question_need_observation_row_count") != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR15 question observation row count changed")
        if data.get("question_need_observation_row_ref_count") != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR15 question observation row ref count changed")
        if data.get("consistency_guard_reason_refs") != [P7_R54_AHR15_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR15 ready reason changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR15_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR15 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR15_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR15 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR16_STEP_REF:
            raise ValueError("P7-R54-AHR15 next step changed")
    else:
        if data.get("consistency_guard_status_ref") != P7_R54_AHR15_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR15 blocked status changed")
        if not step_blockers:
            raise ValueError("P7-R54-AHR15 blocked material must carry blockers")
        if data.get("rating_question_consistency_guard_passed") is not False:
            raise ValueError("P7-R54-AHR15 blocked material must not pass guard")
        if data.get("pause_abort_expiration_protocol_allowed_next") is not False:
            raise ValueError("P7-R54-AHR15 blocked material must not allow AHR16")
        for row in data.get("consistency_issue_rows") or []:
            if not isinstance(row, Mapping):
                raise ValueError("P7-R54-AHR15 issue row must be mapping")
            _assert_required_fields(
                row,
                required=P7_R54_AHR15_CONSISTENCY_ISSUE_ROW_REQUIRED_FIELD_REFS,
                source="P7-R54-AHR15 consistency issue row",
            )
            if row.get("schema_version") != P7_R54_AHR15_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION:
                raise ValueError("P7-R54-AHR15 issue row schema changed")
            if row.get("body_free") is not True:
                raise ValueError("P7-R54-AHR15 issue row must be body-free")
            for key in P7_R54_AHR15_ISSUE_ROW_BODYFREE_FALSE_FLAG_REFS:
                if row.get(key) is not False:
                    raise ValueError(f"P7-R54-AHR15 issue row must keep {key}=False")
        if data.get("next_required_step") != P7_R54_AHR15_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR15 blocked next step changed")
    return True


build_p7_r54_ahr14_question_need_observation_normalization_bodyfree = build_p7_r54_ahr14_question_need_observation_normalization
assert_p7_r54_ahr14_question_need_observation_normalization_bodyfree_contract = (
    assert_p7_r54_ahr14_question_need_observation_normalization_contract
)
build_p7_r54_ahr15_rating_question_consistency_guard_bodyfree = build_p7_r54_ahr15_rating_question_consistency_guard
assert_p7_r54_ahr15_rating_question_consistency_guard_bodyfree_contract = (
    assert_p7_r54_ahr15_rating_question_consistency_guard_contract
)
build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr14_question_need_observation_normalization = (
    build_p7_r54_ahr14_question_need_observation_normalization
)
assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr14_question_need_observation_normalization_contract = (
    assert_p7_r54_ahr14_question_need_observation_normalization_contract
)
build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr15_rating_question_consistency_guard = (
    build_p7_r54_ahr15_rating_question_consistency_guard
)
assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr15_rating_question_consistency_guard_contract = (
    assert_p7_r54_ahr15_rating_question_consistency_guard_contract
)
build_p7_r54_actual_human_review_execution_question_need_observation_normalization_bodyfree = (
    build_p7_r54_ahr14_question_need_observation_normalization
)
assert_p7_r54_actual_human_review_execution_question_need_observation_normalization_bodyfree_contract = (
    assert_p7_r54_ahr14_question_need_observation_normalization_contract
)
build_p7_r54_actual_human_review_execution_rating_question_consistency_guard_bodyfree = (
    build_p7_r54_ahr15_rating_question_consistency_guard
)
assert_p7_r54_actual_human_review_execution_rating_question_consistency_guard_bodyfree_contract = (
    assert_p7_r54_ahr15_rating_question_consistency_guard_contract
)
# R54-AHR16 / R54-AHR17: pause / abort / expiration protocol and disposal
# receipt.  These helpers close the local-only body-full handling boundary
# without turning helper green into P5 final / P6 / P8 / release permission.

P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR16: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR15[1:]
P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR17: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR16[1:]
P7_R54_AHR16_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_AHR15_IMPLEMENTED_STEPS, P7_R54_AHR16_STEP_REF)
P7_R54_AHR16_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR16
P7_R54_AHR17_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_AHR16_IMPLEMENTED_STEPS, P7_R54_AHR17_STEP_REF)
P7_R54_AHR17_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR17

P7_R54_AHR_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.ahr16_pause_abort_expiration_protocol.bodyfree.v1"
)
P7_R54_AHR_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.ahr17_purge_disposal_receipt.bodyfree.v1"
)
P7_R54_AHR16_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION: Final = (
    P7_R54_AHR_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION
)
P7_R54_AHR17_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION: Final = P7_R54_AHR_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION

P7_R54_AHR16_PROTOCOL_READY_STATUS_REF: Final = "AHR_PAUSE_ABORT_EXPIRATION_PROTOCOL_BODYFREE_READY"
P7_R54_AHR16_PROTOCOL_BLOCKED_STATUS_REF: Final = "AHR_PAUSE_ABORT_EXPIRATION_PROTOCOL_BLOCKED"
P7_R54_AHR16_ALLOWED_PROTOCOL_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR16_PROTOCOL_READY_STATUS_REF,
    P7_R54_AHR16_PROTOCOL_BLOCKED_STATUS_REF,
)
P7_R54_AHR16_READY_REASON_REF: Final = "r54_ahr_pause_abort_expiration_protocol_bodyfree_ready"
P7_R54_AHR16_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-16_repair_pause_abort_expiration_protocol_before_disposal_receipt"
)
P7_R54_AHR16_WAITING_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-16_wait_for_local_operation_to_complete_abort_pause_or_expire_before_disposal"
)
P7_R54_AHR16_ALLOWED_REVIEW_LIFECYCLE_STATUS_REFS: Final[tuple[str, ...]] = (
    "RUNNING",
    "PAUSED_LOCAL_ONLY",
    "ABORTED_PURGE_REQUIRED",
    "EXPIRED_PURGE_REQUIRED",
    "COMPLETED_PURGE_REQUIRED",
)
P7_R54_AHR16_PURGE_PLAN_REQUIRED_STATUS_REFS: Final[tuple[str, ...]] = (
    "PAUSED_LOCAL_ONLY",
    "ABORTED_PURGE_REQUIRED",
    "EXPIRED_PURGE_REQUIRED",
    "COMPLETED_PURGE_REQUIRED",
)
P7_R54_AHR16_DISPOSAL_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = P7_R54_AHR16_PURGE_PLAN_REQUIRED_STATUS_REFS
P7_R54_AHR16_DEFAULT_REVIEW_LIFECYCLE_STATUS_REF: Final = "COMPLETED_PURGE_REQUIRED"
P7_R54_AHR16_FAIL_CLOSED_ROUTE_REF: Final = "R54_AHR_FAIL_CLOSED_LOCAL_ONLY_PURGE_REQUIRED_ROUTE"

P7_R54_AHR17_DISPOSAL_READY_STATUS_REF: Final = "AHR_PURGE_DISPOSAL_RECEIPT_VERIFIED_BODYFREE"
P7_R54_AHR17_DISPOSAL_BLOCKED_STATUS_REF: Final = "AHR_PURGE_DISPOSAL_RECEIPT_BLOCKED"
P7_R54_AHR17_ALLOWED_RECEIPT_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR17_DISPOSAL_READY_STATUS_REF,
    P7_R54_AHR17_DISPOSAL_BLOCKED_STATUS_REF,
)
P7_R54_AHR17_ALLOWED_DISPOSAL_STATUS_REFS: Final[tuple[str, ...]] = (
    "DISPOSAL_VERIFIED",
    "EXPIRED_PURGED",
)
P7_R54_AHR17_DEFAULT_DISPOSAL_STATUS_REF: Final = "DISPOSAL_VERIFIED"
P7_R54_AHR17_READY_REASON_REF: Final = "r54_ahr_purge_disposal_receipt_verified_bodyfree"
P7_R54_AHR17_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-17_repair_purge_disposal_receipt_before_post_review_summary"
)
P7_R54_AHR17_LOCAL_PURGE_RECEIPT_REF: Final = "R54_AHR_LOCAL_ONLY_PURGE_DISPOSAL_RECEIPT_BODYFREE_REF"

P7_R54_AHR16_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "actual_human_review_executed_by_person",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
)
P7_R54_AHR17_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR16_ALLOWED_TRUE_FALSE_FLAG_REFS,
    "disposal_verified",
    "actual_disposal_receipt_materialized_here",
)

P7_R54_AHR16_PROTOCOL_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_BASE_REQUIRED_FIELD_REFS,
    "ahr15_schema_version",
    "ahr15_material_ref",
    "ahr15_next_required_step",
    "ahr15_consistency_guard_status_ref",
    "ahr15_pause_abort_expiration_protocol_allowed_next",
    "ahr15_open_consistency_issue_count",
    "ahr15_open_execution_blocker_count",
    *P7_R54_AHR_CURRENT_EXECUTION_BASIS_FIELD_REFS,
    "operation_current_refs_match_current_execution_basis_260_83_256_169",
    "current_execution_basis_refs_match_received_snapshot_260_83_256_169",
    "current_execution_basis_refs_match_260_83_256_169_snapshot",
    "pause_abort_expiration_protocol_status_ref",
    "review_lifecycle_status_ref",
    "review_lifecycle_status_allowed",
    "protocol_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "required_case_count",
    "reviewed_case_count",
    "sanitized_review_result_row_count",
    "rating_row_count",
    "question_observation_row_count",
    "pause_abort_expiration_status_refs",
    "pause_abort_expiration_status_ref_count",
    "purge_plan_required_status_refs",
    "purge_plan_required_status_ref_count",
    "purge_plan_required_for_current_status",
    "purge_plan_present",
    "purge_plan_bodyfree_only",
    "purge_plan_local_only",
    "fail_closed_on_pause_abort_expiration",
    "fail_closed_route_ref",
    "body_full_packet_must_not_remain_unhandled",
    "body_full_packet_disposal_required_next",
    "reviewer_local_notes_disposal_required_next",
    "temporary_form_disposal_required_next",
    "local_packet_exported",
    "local_packet_export_blocked",
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
    "stdout_body_included",
    "stderr_body_included",
    "traceback_body_included",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_review_evidence_complete",
    "disposal_receipt_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "purge_disposal_receipt_allowed_next",
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
    "public_contract",
    "r54_ahr_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R54_AHR_FALSE_FLAG_REFS,
)

P7_R54_AHR17_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_BASE_REQUIRED_FIELD_REFS,
    "ahr16_schema_version",
    "ahr16_material_ref",
    "ahr16_next_required_step",
    "ahr16_pause_abort_expiration_protocol_status_ref",
    "ahr16_review_lifecycle_status_ref",
    "ahr16_purge_disposal_receipt_allowed_next",
    "ahr16_purge_plan_present",
    *P7_R54_AHR_CURRENT_EXECUTION_BASIS_FIELD_REFS,
    "operation_current_refs_match_current_execution_basis_260_83_256_169",
    "current_execution_basis_refs_match_received_snapshot_260_83_256_169",
    "current_execution_basis_refs_match_260_83_256_169_snapshot",
    "purge_disposal_receipt_status_ref",
    "disposal_status_ref",
    "disposal_status_allowed",
    "disposal_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "local_purge_receipt_ref",
    "required_case_count",
    "reviewed_case_count",
    "sanitized_review_result_row_count",
    "rating_row_count",
    "question_observation_row_count",
    "disposal_verified",
    "disposal_receipt_intaken_here",
    "disposal_receipt_bodyfree_only",
    "body_removed",
    "body_full_packet_removed",
    "body_full_packet_deleted",
    "reviewer_notes_removed",
    "reviewer_local_notes_removed",
    "temporary_form_removed",
    "temporary_selection_form_removed",
    "local_packet_exported",
    "content_hash_of_body_stored",
    "raw_body_included",
    "raw_input_included",
    "returned_emlis_body_included",
    "history_surface_included",
    "comment_text_included",
    "reviewer_free_text_included",
    "reviewer_notes_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_absolute_path_included",
    "local_path_included",
    "body_hash_included",
    "packet_content_included",
    "body_full_packet_content_included",
    "terminal_output_body_included",
    "stdout_body_included",
    "stderr_body_included",
    "traceback_body_included",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "disposal_receipt_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "actual_review_evidence_complete",
    "body_free_post_review_summary_allowed_next",
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
    "public_contract",
    "r54_ahr_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R54_AHR_FALSE_FLAG_REFS,
)


def _ahr16_ahr17_current_execution_basis_fields(*, actual_basis: bool = True) -> dict[str, Any]:
    return {
        "current_execution_basis_refs": dict(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "current_execution_basis_ref_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "current_execution_basis_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "current_execution_basis_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_refs": dict(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_ref_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "operation_current_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "required_current_execution_basis_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "required_current_execution_basis_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "all_required_current_execution_basis_refs_present": True,
        "actual_execution_basis_ref": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF,
        "actual_execution_basis_allowed": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_ALLOWED_REF,
        "actual_review_basis_ref": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_ALLOWED_REF,
        "current_execution_basis_refs_are_actual_execution_basis": actual_basis,
        "current_execution_basis_refs_used_as_actual_execution_basis": actual_basis,
        "operation_current_refs_are_actual_execution_basis": actual_basis,
        "operation_current_refs_used_as_actual_execution_basis": actual_basis,
    }


def _ahr16_bodyfree_false_flags() -> dict[str, bool]:
    return {
        "body_full_packet_content_included": False,
        "raw_input_included": False,
        "raw_body_included": False,
        "returned_emlis_body_included": False,
        "history_surface_included": False,
        "comment_text_included": False,
        "reviewer_free_text_included": False,
        "reviewer_notes_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_absolute_path_included": False,
        "body_hash_included": False,
        "packet_content_included": False,
        "terminal_output_body_included": False,
        "stdout_body_included": False,
        "stderr_body_included": False,
        "traceback_body_included": False,
    }


def build_p7_r54_ahr16_pause_abort_expiration_protocol(
    *,
    rating_question_consistency_guard: Mapping[str, Any] | None = None,
    review_lifecycle_status_ref: Any = P7_R54_AHR16_DEFAULT_REVIEW_LIFECYCLE_STATUS_REF,
    purge_plan_present: bool = True,
    review_session_id: Any = P7_R54_AHR_DEFAULT_REVIEW_SESSION_ID,
) -> dict[str, Any]:
    """Build R54-AHR-16 pause / abort / expiration protocol material."""

    guard = dict(rating_question_consistency_guard or build_p7_r54_ahr15_rating_question_consistency_guard())
    try:
        assert_p7_r54_ahr15_rating_question_consistency_guard_contract(guard)
        guard_contract_ok = True
    except ValueError:
        guard_contract_ok = False
    lifecycle_status = clean_identifier(
        review_lifecycle_status_ref,
        default="",
        max_length=120,
    )
    status_allowed = lifecycle_status in P7_R54_AHR16_ALLOWED_REVIEW_LIFECYCLE_STATUS_REFS
    purge_required = lifecycle_status in P7_R54_AHR16_PURGE_PLAN_REQUIRED_STATUS_REFS
    blockers: list[str] = []
    if not guard_contract_ok:
        blockers.append("ahr15_rating_question_consistency_guard_contract_invalid")
    if guard.get("schema_version") != P7_R54_AHR15_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION:
        blockers.append("ahr15_rating_question_consistency_guard_schema_missing")
    if guard.get("pause_abort_expiration_protocol_allowed_next") is not True:
        blockers.append("ahr15_pause_abort_expiration_protocol_not_allowed")
    if guard.get("consistency_guard_status_ref") != P7_R54_AHR15_PASSED_STATUS_REF:
        blockers.append("ahr15_rating_question_consistency_guard_not_passed")
    if guard.get("next_required_step") != P7_R54_AHR16_STEP_REF:
        blockers.append("ahr15_next_step_not_ahr16")
    if int(guard.get("open_consistency_issue_count") or 0) != 0:
        blockers.append("ahr15_open_consistency_issues_remaining")
    if int(guard.get("open_execution_blocker_count") or 0) != 0:
        blockers.append("ahr15_open_execution_blockers_remaining")
    if not status_allowed:
        blockers.append("review_lifecycle_status_not_allowed")
    if purge_required and not purge_plan_present:
        blockers.append("purge_plan_missing_for_pause_abort_expiration_status")
    ready = not blockers
    disposal_allowed = ready and lifecycle_status in P7_R54_AHR16_DISPOSAL_ALLOWED_STATUS_REFS and purge_plan_present
    reason_refs = [P7_R54_AHR16_READY_REASON_REF] if ready else blockers
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR16_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_STEP,
        "scope": P7_R54_AHR_SCOPE,
        "policy_kind": P7_R54_AHR_POLICY_KIND,
        "policy_section": P7_R54_AHR16_STEP_REF,
        "operation_step_ref": P7_R54_AHR16_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr16_pause_abort_expiration_protocol_20260627",
        "review_session_id": _safe_review_session_id(review_session_id or guard.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ahr15_schema_version": guard.get("schema_version", ""),
        "ahr15_material_ref": guard.get("material_id", ""),
        "ahr15_next_required_step": guard.get("next_required_step", ""),
        "ahr15_consistency_guard_status_ref": guard.get("consistency_guard_status_ref", ""),
        "ahr15_pause_abort_expiration_protocol_allowed_next": guard.get(
            "pause_abort_expiration_protocol_allowed_next"
        ) is True,
        "ahr15_open_consistency_issue_count": int(guard.get("open_consistency_issue_count") or 0),
        "ahr15_open_execution_blocker_count": int(guard.get("open_execution_blocker_count") or 0),
        **_ahr16_ahr17_current_execution_basis_fields(actual_basis=True),
        "operation_current_refs_match_current_execution_basis_260_83_256_169": True,
        "current_execution_basis_refs_match_received_snapshot_260_83_256_169": True,
        "current_execution_basis_refs_match_260_83_256_169_snapshot": True,
        "pause_abort_expiration_protocol_status_ref": (
            P7_R54_AHR16_PROTOCOL_READY_STATUS_REF if ready else P7_R54_AHR16_PROTOCOL_BLOCKED_STATUS_REF
        ),
        "review_lifecycle_status_ref": lifecycle_status,
        "review_lifecycle_status_allowed": status_allowed,
        "protocol_reason_refs": reason_refs,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "required_case_count": P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "reviewed_case_count": (
            int(guard.get("reviewed_case_count") or guard.get("question_need_observation_row_count") or 0) if ready else 0
        ),
        "sanitized_review_result_row_count": (
            int(guard.get("sanitized_review_result_row_count") or guard.get("question_need_observation_row_count") or 0)
            if ready
            else 0
        ),
        "rating_row_count": int(guard.get("rating_row_count") or guard.get("question_need_observation_row_count") or 0) if ready else 0,
        "question_observation_row_count": int(guard.get("question_need_observation_row_count") or 0) if ready else 0,
        "pause_abort_expiration_status_refs": list(P7_R54_AHR16_ALLOWED_REVIEW_LIFECYCLE_STATUS_REFS),
        "pause_abort_expiration_status_ref_count": len(P7_R54_AHR16_ALLOWED_REVIEW_LIFECYCLE_STATUS_REFS),
        "purge_plan_required_status_refs": list(P7_R54_AHR16_PURGE_PLAN_REQUIRED_STATUS_REFS),
        "purge_plan_required_status_ref_count": len(P7_R54_AHR16_PURGE_PLAN_REQUIRED_STATUS_REFS),
        "purge_plan_required_for_current_status": purge_required,
        "purge_plan_present": bool(purge_plan_present) if ready or purge_required else bool(purge_plan_present),
        "purge_plan_bodyfree_only": bool(purge_plan_present),
        "purge_plan_local_only": bool(purge_plan_present),
        "fail_closed_on_pause_abort_expiration": ready,
        "fail_closed_route_ref": P7_R54_AHR16_FAIL_CLOSED_ROUTE_REF,
        "body_full_packet_must_not_remain_unhandled": ready,
        "body_full_packet_disposal_required_next": disposal_allowed,
        "reviewer_local_notes_disposal_required_next": disposal_allowed,
        "temporary_form_disposal_required_next": disposal_allowed,
        "local_packet_exported": False,
        "local_packet_export_blocked": True,
        **_ahr16_bodyfree_false_flags(),
        "actual_human_review_executed_by_person": guard.get("actual_human_review_executed_by_person") is True and ready,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": guard.get("actual_rating_rows_materialized_here") is True and ready,
        "actual_question_need_observation_rows_materialized_here": guard.get(
            "actual_question_need_observation_rows_materialized_here"
        ) is True and ready,
        "actual_review_evidence_complete": False,
        "disposal_receipt_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "purge_disposal_receipt_allowed_next": disposal_allowed,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "implemented_steps": list(P7_R54_AHR16_IMPLEMENTED_STEPS if ready else P7_R54_AHR15_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR16_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR15_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": (
            P7_R54_AHR17_STEP_REF
            if disposal_allowed
            else P7_R54_AHR16_WAITING_NEXT_REQUIRED_STEP_REF
            if ready
            else P7_R54_AHR16_BLOCKED_NEXT_REQUIRED_STEP_REF
        ),
        "public_contract": public_contract_flags(),
        "r54_ahr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    _add_false_flags_preserving_allowed(material, allowed_true_refs=P7_R54_AHR16_ALLOWED_TRUE_FALSE_FLAG_REFS)
    return material


def assert_p7_r54_ahr16_pause_abort_expiration_protocol_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR16_PROTOCOL_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR16 pause / abort / expiration protocol",
    )
    _assert_bodyfree_no_touch_base_allowing_true_flags(
        data,
        schema_version=P7_R54_AHR16_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION,
        policy_section=P7_R54_AHR16_STEP_REF,
        operation_step_ref=P7_R54_AHR16_STEP_REF,
        source="P7-R54-AHR16 pause / abort / expiration protocol",
        allowed_true_refs=P7_R54_AHR16_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    _assert_current_execution_basis_refs(data, source="P7-R54-AHR16 pause / abort / expiration protocol", actual_basis=True)
    if data.get("ahr15_schema_version") != P7_R54_AHR15_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR16 must reference AHR15 consistency guard")
    if data.get("pause_abort_expiration_protocol_status_ref") not in P7_R54_AHR16_ALLOWED_PROTOCOL_STATUS_REFS:
        raise ValueError("P7-R54-AHR16 protocol status changed")
    if data.get("review_lifecycle_status_ref") not in P7_R54_AHR16_ALLOWED_REVIEW_LIFECYCLE_STATUS_REFS:
        if data.get("pause_abort_expiration_protocol_status_ref") != P7_R54_AHR16_PROTOCOL_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR16 invalid lifecycle status must block")
    if tuple(data.get("pause_abort_expiration_status_refs") or ()) != P7_R54_AHR16_ALLOWED_REVIEW_LIFECYCLE_STATUS_REFS:
        raise ValueError("P7-R54-AHR16 lifecycle status refs changed")
    if tuple(data.get("purge_plan_required_status_refs") or ()) != P7_R54_AHR16_PURGE_PLAN_REQUIRED_STATUS_REFS:
        raise ValueError("P7-R54-AHR16 purge-required status refs changed")
    for key in (
        "local_packet_exported",
        "body_full_packet_content_included",
        "actual_human_review_run_here",
        "actual_review_evidence_complete",
        "disposal_receipt_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "p5_human_blind_qa_confirmed_final",
        "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR16 must keep {key}=False")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or (), limit=200, max_length=260)
    if blockers != dedupe_identifiers(data.get("open_execution_blocker_ids") or (), limit=200, max_length=260):
        raise ValueError("P7-R54-AHR16 open blockers must match blockers")
    ready = data.get("pause_abort_expiration_protocol_status_ref") == P7_R54_AHR16_PROTOCOL_READY_STATUS_REF
    if ready:
        if blockers:
            raise ValueError("P7-R54-AHR16 ready protocol must not carry blockers")
        if data.get("protocol_reason_refs") != [P7_R54_AHR16_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR16 ready reason changed")
        for key in (
            "ahr15_pause_abort_expiration_protocol_allowed_next",
            "review_lifecycle_status_allowed",
            "fail_closed_on_pause_abort_expiration",
            "body_full_packet_must_not_remain_unhandled",
            "local_packet_export_blocked",
            "actual_human_review_executed_by_person",
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "r52_reintake_claim_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "p5_finalization_blocked_here",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR16 ready material must keep {key}=True")
        if data.get("review_lifecycle_status_ref") in P7_R54_AHR16_PURGE_PLAN_REQUIRED_STATUS_REFS:
            if data.get("purge_plan_required_for_current_status") is not True or data.get("purge_plan_present") is not True:
                raise ValueError("P7-R54-AHR16 purge-required status needs purge plan")
            if data.get("purge_disposal_receipt_allowed_next") is not True:
                raise ValueError("P7-R54-AHR16 purge-required status must allow AHR17")
            if data.get("next_required_step") != P7_R54_AHR17_STEP_REF:
                raise ValueError("P7-R54-AHR16 purge-required status next step changed")
        else:
            if data.get("purge_disposal_receipt_allowed_next") is not False:
                raise ValueError("P7-R54-AHR16 running state cannot allow AHR17")
            if data.get("next_required_step") != P7_R54_AHR16_WAITING_NEXT_REQUIRED_STEP_REF:
                raise ValueError("P7-R54-AHR16 running next step changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR16_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR16 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR16_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR16 not-yet steps changed")
    else:
        if not blockers:
            raise ValueError("P7-R54-AHR16 blocked material must carry blockers")
        if data.get("purge_disposal_receipt_allowed_next") is not False:
            raise ValueError("P7-R54-AHR16 blocked material must not allow AHR17")
        if data.get("next_required_step") != P7_R54_AHR16_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR16 blocked next step changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR15_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR16 blocked implemented steps changed")
    return True


def build_p7_r54_ahr17_purge_disposal_receipt(
    *,
    pause_abort_expiration_protocol: Mapping[str, Any] | None = None,
    disposal_status_ref: Any = P7_R54_AHR17_DEFAULT_DISPOSAL_STATUS_REF,
    body_removed: bool = True,
    reviewer_notes_removed: bool = True,
    temporary_form_removed: bool = True,
    local_packet_exported: bool = False,
    content_hash_of_body_stored: bool = False,
    review_session_id: Any = P7_R54_AHR_DEFAULT_REVIEW_SESSION_ID,
) -> dict[str, Any]:
    """Build R54-AHR-17 body-free purge / disposal receipt material."""

    protocol = dict(pause_abort_expiration_protocol or build_p7_r54_ahr16_pause_abort_expiration_protocol())
    try:
        assert_p7_r54_ahr16_pause_abort_expiration_protocol_contract(protocol)
        protocol_contract_ok = True
    except ValueError:
        protocol_contract_ok = False
    disposal_status = clean_identifier(disposal_status_ref, default="", max_length=120)
    disposal_status_allowed = disposal_status in P7_R54_AHR17_ALLOWED_DISPOSAL_STATUS_REFS
    blockers: list[str] = []
    if not protocol_contract_ok:
        blockers.append("ahr16_pause_abort_expiration_protocol_contract_invalid")
    if protocol.get("schema_version") != P7_R54_AHR16_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION:
        blockers.append("ahr16_pause_abort_expiration_protocol_schema_missing")
    if protocol.get("purge_disposal_receipt_allowed_next") is not True:
        blockers.append("ahr16_purge_disposal_receipt_not_allowed")
    if protocol.get("next_required_step") != P7_R54_AHR17_STEP_REF:
        blockers.append("ahr16_next_step_not_ahr17")
    if protocol.get("purge_plan_present") is not True:
        blockers.append("ahr16_purge_plan_missing")
    if not disposal_status_allowed:
        blockers.append("disposal_status_not_allowed")
    if not body_removed:
        blockers.append("body_removed_false")
    if not reviewer_notes_removed:
        blockers.append("reviewer_notes_removed_false")
    if not temporary_form_removed:
        blockers.append("temporary_form_removed_false")
    if local_packet_exported:
        blockers.append("local_packet_exported_true")
    if content_hash_of_body_stored:
        blockers.append("content_hash_of_body_stored_true")
    ready = not blockers
    reason_refs = [P7_R54_AHR17_READY_REASON_REF] if ready else blockers
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR17_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_STEP,
        "scope": P7_R54_AHR_SCOPE,
        "policy_kind": P7_R54_AHR_POLICY_KIND,
        "policy_section": P7_R54_AHR17_STEP_REF,
        "operation_step_ref": P7_R54_AHR17_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr17_purge_disposal_receipt_20260627",
        "review_session_id": _safe_review_session_id(review_session_id or protocol.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ahr16_schema_version": protocol.get("schema_version", ""),
        "ahr16_material_ref": protocol.get("material_id", ""),
        "ahr16_next_required_step": protocol.get("next_required_step", ""),
        "ahr16_pause_abort_expiration_protocol_status_ref": protocol.get("pause_abort_expiration_protocol_status_ref", ""),
        "ahr16_review_lifecycle_status_ref": protocol.get("review_lifecycle_status_ref", ""),
        "ahr16_purge_disposal_receipt_allowed_next": protocol.get("purge_disposal_receipt_allowed_next") is True,
        "ahr16_purge_plan_present": protocol.get("purge_plan_present") is True,
        **_ahr16_ahr17_current_execution_basis_fields(actual_basis=True),
        "operation_current_refs_match_current_execution_basis_260_83_256_169": True,
        "current_execution_basis_refs_match_received_snapshot_260_83_256_169": True,
        "current_execution_basis_refs_match_260_83_256_169_snapshot": True,
        "purge_disposal_receipt_status_ref": (
            P7_R54_AHR17_DISPOSAL_READY_STATUS_REF if ready else P7_R54_AHR17_DISPOSAL_BLOCKED_STATUS_REF
        ),
        "disposal_status_ref": disposal_status,
        "disposal_status_allowed": disposal_status_allowed,
        "disposal_reason_refs": reason_refs,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "local_purge_receipt_ref": P7_R54_AHR17_LOCAL_PURGE_RECEIPT_REF,
        "required_case_count": P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "reviewed_case_count": int(protocol.get("reviewed_case_count") or 0) if ready else 0,
        "sanitized_review_result_row_count": int(protocol.get("sanitized_review_result_row_count") or 0) if ready else 0,
        "rating_row_count": int(protocol.get("rating_row_count") or 0) if ready else 0,
        "question_observation_row_count": int(protocol.get("question_observation_row_count") or 0) if ready else 0,
        "disposal_verified": ready,
        "disposal_receipt_intaken_here": ready,
        "disposal_receipt_bodyfree_only": ready,
        "body_removed": bool(body_removed) and ready,
        "body_full_packet_removed": bool(body_removed) and ready,
        "body_full_packet_deleted": bool(body_removed) and ready,
        "reviewer_notes_removed": bool(reviewer_notes_removed) and ready,
        "reviewer_local_notes_removed": bool(reviewer_notes_removed) and ready,
        "temporary_form_removed": bool(temporary_form_removed) and ready,
        "temporary_selection_form_removed": bool(temporary_form_removed) and ready,
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "raw_body_included": False,
        "raw_input_included": False,
        "returned_emlis_body_included": False,
        "history_surface_included": False,
        "comment_text_included": False,
        "reviewer_free_text_included": False,
        "reviewer_notes_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_absolute_path_included": False,
        "local_path_included": False,
        "body_hash_included": False,
        "packet_content_included": False,
        "body_full_packet_content_included": False,
        "terminal_output_body_included": False,
        "stdout_body_included": False,
        "stderr_body_included": False,
        "traceback_body_included": False,
        "actual_human_review_executed_by_person": protocol.get("actual_human_review_executed_by_person") is True and ready,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": protocol.get("actual_rating_rows_materialized_here") is True and ready,
        "actual_question_need_observation_rows_materialized_here": protocol.get(
            "actual_question_need_observation_rows_materialized_here"
        ) is True and ready,
        "disposal_receipt_materialized_here": ready,
        "actual_disposal_receipt_materialized_here": ready,
        "actual_review_evidence_complete": False,
        "body_free_post_review_summary_allowed_next": ready,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "implemented_steps": list(P7_R54_AHR17_IMPLEMENTED_STEPS if ready else P7_R54_AHR16_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR17_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR16_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR18_STEP_REF if ready else P7_R54_AHR17_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    _add_false_flags_preserving_allowed(material, allowed_true_refs=P7_R54_AHR17_ALLOWED_TRUE_FALSE_FLAG_REFS)
    return material


def assert_p7_r54_ahr17_purge_disposal_receipt_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR17_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR17 purge / disposal receipt",
    )
    _assert_bodyfree_no_touch_base_allowing_true_flags(
        data,
        schema_version=P7_R54_AHR17_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION,
        policy_section=P7_R54_AHR17_STEP_REF,
        operation_step_ref=P7_R54_AHR17_STEP_REF,
        source="P7-R54-AHR17 purge / disposal receipt",
        allowed_true_refs=P7_R54_AHR17_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    _assert_current_execution_basis_refs(data, source="P7-R54-AHR17 purge / disposal receipt", actual_basis=True)
    if data.get("ahr16_schema_version") != P7_R54_AHR16_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR17 must reference AHR16 pause / abort / expiration protocol")
    if data.get("purge_disposal_receipt_status_ref") not in P7_R54_AHR17_ALLOWED_RECEIPT_STATUS_REFS:
        raise ValueError("P7-R54-AHR17 receipt status changed")
    if data.get("disposal_status_ref") not in P7_R54_AHR17_ALLOWED_DISPOSAL_STATUS_REFS:
        if data.get("purge_disposal_receipt_status_ref") != P7_R54_AHR17_DISPOSAL_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR17 invalid disposal status must block")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or (), limit=200, max_length=260)
    if blockers != dedupe_identifiers(data.get("open_execution_blocker_ids") or (), limit=200, max_length=260):
        raise ValueError("P7-R54-AHR17 open blockers must match blockers")
    for key in (
        "local_packet_exported",
        "content_hash_of_body_stored",
        "raw_body_included",
        "raw_input_included",
        "returned_emlis_body_included",
        "history_surface_included",
        "reviewer_free_text_included",
        "reviewer_notes_body_included",
        "question_text_included",
        "draft_question_text_included",
        "local_absolute_path_included",
        "body_hash_included",
        "packet_content_included",
        "body_full_packet_content_included",
        "terminal_output_body_included",
        "actual_human_review_run_here",
        "actual_review_evidence_complete",
        "p5_human_blind_qa_confirmed_final",
        "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR17 must keep {key}=False")
    ready = data.get("purge_disposal_receipt_status_ref") == P7_R54_AHR17_DISPOSAL_READY_STATUS_REF
    if ready:
        if blockers:
            raise ValueError("P7-R54-AHR17 ready receipt must not carry blockers")
        if data.get("disposal_reason_refs") != [P7_R54_AHR17_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR17 ready reason changed")
        for key in (
            "ahr16_purge_disposal_receipt_allowed_next",
            "ahr16_purge_plan_present",
            "disposal_status_allowed",
            "disposal_verified",
            "disposal_receipt_intaken_here",
            "disposal_receipt_bodyfree_only",
            "body_removed",
            "body_full_packet_removed",
            "body_full_packet_deleted",
            "reviewer_notes_removed",
            "reviewer_local_notes_removed",
            "temporary_form_removed",
            "temporary_selection_form_removed",
            "actual_human_review_executed_by_person",
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "disposal_receipt_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "body_free_post_review_summary_allowed_next",
            "r52_reintake_claim_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "p5_finalization_blocked_here",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR17 ready material must keep {key}=True")
        if data.get("reviewed_case_count") != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR17 reviewed case count changed")
        if data.get("rating_row_count") != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR17 rating row count changed")
        if data.get("question_observation_row_count") != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR17 question observation row count changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR17_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR17 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR17_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR17 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR18_STEP_REF:
            raise ValueError("P7-R54-AHR17 next step changed")
    else:
        if not blockers:
            raise ValueError("P7-R54-AHR17 blocked material must carry blockers")
        for key in (
            "disposal_verified",
            "disposal_receipt_intaken_here",
            "disposal_receipt_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "body_free_post_review_summary_allowed_next",
        ):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR17 blocked material must keep {key}=False")
        if data.get("next_required_step") != P7_R54_AHR17_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR17 blocked next step changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR16_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR17 blocked implemented steps changed")
    return True


build_p7_r54_ahr16_pause_abort_expiration_protocol_bodyfree = build_p7_r54_ahr16_pause_abort_expiration_protocol
assert_p7_r54_ahr16_pause_abort_expiration_protocol_bodyfree_contract = (
    assert_p7_r54_ahr16_pause_abort_expiration_protocol_contract
)
build_p7_r54_ahr17_purge_disposal_receipt_bodyfree = build_p7_r54_ahr17_purge_disposal_receipt
assert_p7_r54_ahr17_purge_disposal_receipt_bodyfree_contract = assert_p7_r54_ahr17_purge_disposal_receipt_contract
build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr16_pause_abort_expiration_protocol = (
    build_p7_r54_ahr16_pause_abort_expiration_protocol
)
assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr16_pause_abort_expiration_protocol_contract = (
    assert_p7_r54_ahr16_pause_abort_expiration_protocol_contract
)
build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr17_purge_disposal_receipt = (
    build_p7_r54_ahr17_purge_disposal_receipt
)
assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr17_purge_disposal_receipt_contract = (
    assert_p7_r54_ahr17_purge_disposal_receipt_contract
)
build_p7_r54_actual_human_review_execution_pause_abort_expiration_protocol_bodyfree = (
    build_p7_r54_ahr16_pause_abort_expiration_protocol
)
assert_p7_r54_actual_human_review_execution_pause_abort_expiration_protocol_bodyfree_contract = (
    assert_p7_r54_ahr16_pause_abort_expiration_protocol_contract
)
build_p7_r54_actual_human_review_execution_purge_disposal_receipt_bodyfree = (
    build_p7_r54_ahr17_purge_disposal_receipt
)
assert_p7_r54_actual_human_review_execution_purge_disposal_receipt_bodyfree_contract = (
    assert_p7_r54_ahr17_purge_disposal_receipt_contract
)

# ---------------------------------------------------------------------------
# R54-AHR18 / R54-AHR19: body-free post-review summary and P5 decision
# candidate separation.

P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR18: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR17[1:]
P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR19: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR18[1:]
P7_R54_AHR18_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_AHR17_IMPLEMENTED_STEPS, P7_R54_AHR18_STEP_REF)
P7_R54_AHR18_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR18
P7_R54_AHR19_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_AHR18_IMPLEMENTED_STEPS, P7_R54_AHR19_STEP_REF)
P7_R54_AHR19_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR19

P7_R54_AHR18_BODYFREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.ahr18_bodyfree_post_review_summary.bodyfree.v1"
)
P7_R54_AHR19_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.ahr19_p5_decision_candidate_separation.bodyfree.v1"
)
P7_R54_AHR18_READY_STATUS_REF: Final = "AHR_BODYFREE_POST_REVIEW_SUMMARY_READY"
P7_R54_AHR18_BLOCKED_STATUS_REF: Final = "AHR_BODYFREE_POST_REVIEW_SUMMARY_BLOCKED"
P7_R54_AHR18_READY_REASON_REF: Final = "r54_ahr_bodyfree_post_review_summary_ready"
P7_R54_AHR18_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-18_repair_post_review_summary_inputs_before_p5_decision_candidate_separation"
)
P7_R54_AHR19_READY_STATUS_REF: Final = "AHR_P5_DECISION_CANDIDATE_SEPARATED_BODYFREE"
P7_R54_AHR19_BLOCKED_STATUS_REF: Final = "AHR_P5_DECISION_CANDIDATE_SEPARATION_BLOCKED"
P7_R54_AHR19_READY_REASON_REF: Final = "r54_ahr_p5_decision_candidate_separated_bodyfree"
P7_R54_AHR19_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-19_repair_post_review_summary_before_decision_candidate_separation"
)
P7_R54_AHR19_P5_REPAIR_NEXT_REQUIRED_STEP_REF: Final = "P5_REPAIR_RETURN_BEFORE_R52_REINTAKE_HANDOFF"
P7_R54_AHR19_P4_REPAIR_NEXT_REQUIRED_STEP_REF: Final = "P4_R12_TARGETED_CURRENT_ONLY_SURFACE_REPAIR_BEFORE_R52_REINTAKE_HANDOFF"
P7_R54_AHR19_OPERATION_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "R54_OPERATION_BLOCKED_REPAIR_BEFORE_R52_REINTAKE_HANDOFF"

P7_R54_AHR19_P5_CONFIRMED_CANDIDATE_REF: Final = "P5_CONFIRMED_CANDIDATE"
P7_R54_AHR19_P5_REPAIR_RETURN_REF: Final = "P5_REPAIR_RETURN"
P7_R54_AHR19_P4_CURRENT_ONLY_REPAIR_REF: Final = "P4_R12_TARGETED_CURRENT_ONLY_SURFACE_REPAIR"
P7_R54_AHR19_OPERATION_INCONCLUSIVE_REF: Final = "R54_OPERATION_INCONCLUSIVE"
P7_R54_AHR19_OPERATION_BLOCKED_PREFLIGHT_REF: Final = "R54_OPERATION_BLOCKED_PREFLIGHT"
P7_R54_AHR19_OPERATION_BLOCKED_DISPOSAL_REF: Final = "R54_OPERATION_BLOCKED_DISPOSAL"
P7_R54_AHR19_OPERATION_BLOCKED_BODY_LEAK_OR_QUESTION_TEXT_REF: Final = "R54_OPERATION_BLOCKED_BODY_LEAK_OR_QUESTION_TEXT"
P7_R54_AHR19_OPERATION_BLOCKED_NO_TOUCH_REF: Final = "R54_OPERATION_BLOCKED_NO_TOUCH_VIOLATION"
P7_R54_AHR19_ALLOWED_DECISION_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR19_P5_CONFIRMED_CANDIDATE_REF,
    P7_R54_AHR19_P5_REPAIR_RETURN_REF,
    P7_R54_AHR19_P4_CURRENT_ONLY_REPAIR_REF,
    P7_R54_AHR19_OPERATION_INCONCLUSIVE_REF,
    P7_R54_AHR19_OPERATION_BLOCKED_PREFLIGHT_REF,
    P7_R54_AHR19_OPERATION_BLOCKED_DISPOSAL_REF,
    P7_R54_AHR19_OPERATION_BLOCKED_BODY_LEAK_OR_QUESTION_TEXT_REF,
    P7_R54_AHR19_OPERATION_BLOCKED_NO_TOUCH_REF,
)

P7_R54_AHR18_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "actual_human_review_executed_by_person",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "disposal_verified",
    "actual_disposal_receipt_materialized_here",
    "actual_review_evidence_complete",
)
P7_R54_AHR19_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR18_ALLOWED_TRUE_FALSE_FLAG_REFS,
    "p5_human_blind_qa_confirmed_candidate",
)


def _ahr18_current_basis_fields() -> dict[str, Any]:
    return {
        "current_execution_basis_refs": dict(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "current_execution_basis_ref_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "current_execution_basis_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "current_execution_basis_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_refs": dict(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_ref_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "operation_current_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "operation_current_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "required_current_execution_basis_ref_keys": list(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS),
        "required_current_execution_basis_ref_key_count": len(P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS),
        "all_required_current_execution_basis_refs_present": True,
        "actual_execution_basis_ref": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF,
        "actual_execution_basis_allowed": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_ALLOWED_REF,
        "actual_review_basis_ref": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_ALLOWED_REF,
        "current_execution_basis_refs_are_actual_execution_basis": True,
        "current_execution_basis_refs_used_as_actual_execution_basis": True,
        "operation_current_refs_are_actual_execution_basis": True,
        "operation_current_refs_used_as_actual_execution_basis": True,
    }


def _ahr_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _ahr_axis_averages(rating_rows: Sequence[Any]) -> dict[str, float]:
    averages: dict[str, float] = {}
    for axis_ref in P7_R54_AHR05_RATING_AXIS_REFS:
        values: list[float] = []
        for raw_row in rating_rows:
            axis_scores = safe_mapping(safe_mapping(raw_row).get("axis_scores"))
            try:
                values.append(float(axis_scores.get(axis_ref)))
            except (TypeError, ValueError):
                pass
        averages[axis_ref] = round(sum(values) / len(values), 4) if values else 0.0
    return averages


def _ahr_verdict_counts(raw_counts: Mapping[str, Any]) -> dict[str, int]:
    return {verdict_ref: _ahr_int(raw_counts.get(verdict_ref)) for verdict_ref in P7_R54_AHR09_VERDICT_OPTION_REFS}


def build_p7_r54_ahr18_bodyfree_post_review_summary(
    *,
    purge_disposal_receipt: Mapping[str, Any] | None = None,
    rating_row_normalization: Mapping[str, Any] | None = None,
    readfeel_execution_blocker_ingestion: Mapping[str, Any] | None = None,
    question_need_observation_normalization: Mapping[str, Any] | None = None,
    rating_question_consistency_guard: Mapping[str, Any] | None = None,
    review_session_id: Any = P7_R54_AHR_DEFAULT_REVIEW_SESSION_ID,
) -> dict[str, Any]:
    disposal = dict(purge_disposal_receipt or build_p7_r54_ahr17_purge_disposal_receipt())
    rating = dict(rating_row_normalization or {})
    blocker_material = dict(readfeel_execution_blocker_ingestion or {})
    question = dict(question_need_observation_normalization or {})
    consistency = dict(rating_question_consistency_guard or {})
    session_id = _safe_review_session_id(review_session_id or disposal.get("review_session_id"))
    blockers: list[str] = []
    checks = (
        (assert_p7_r54_ahr17_purge_disposal_receipt_contract, disposal, "ahr17_purge_disposal_receipt_contract_invalid"),
        (assert_p7_r54_ahr12_rating_row_normalization_contract, rating, "ahr12_rating_row_normalization_contract_invalid_or_missing"),
        (assert_p7_r54_ahr13_readfeel_blocker_execution_blocker_ingestion_contract, blocker_material, "ahr13_blocker_ingestion_contract_invalid_or_missing"),
        (assert_p7_r54_ahr14_question_need_observation_normalization_contract, question, "ahr14_question_need_observation_contract_invalid_or_missing"),
        (assert_p7_r54_ahr15_rating_question_consistency_guard_contract, consistency, "ahr15_consistency_guard_contract_invalid_or_missing"),
    )
    for check, material, blocker_id in checks:
        try:
            check(material)
        except ValueError:
            blockers.append(blocker_id)
    if disposal.get("purge_disposal_receipt_status_ref") != P7_R54_AHR17_DISPOSAL_READY_STATUS_REF:
        blockers.append("ahr17_purge_disposal_receipt_not_ready")
    if disposal.get("body_free_post_review_summary_allowed_next") is not True:
        blockers.append("ahr17_body_free_post_review_summary_not_allowed")
    if disposal.get("disposal_verified") is not True:
        blockers.append("ahr17_disposal_not_verified")
    if rating.get("rating_row_normalization_status_ref") != P7_R54_AHR12_NORMALIZED_STATUS_REF:
        blockers.append("ahr12_rating_row_normalization_not_ready")
    if _ahr_int(rating.get("rating_row_count")) != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("ahr12_rating_row_count_not_24")
    if blocker_material.get("blocker_ingestion_status_ref") != P7_R54_AHR13_INGESTED_STATUS_REF:
        blockers.append("ahr13_blocker_ingestion_not_ready")
    if question.get("question_need_observation_normalization_status_ref") != P7_R54_AHR14_NORMALIZED_STATUS_REF:
        blockers.append("ahr14_question_need_observation_not_ready")
    if _ahr_int(question.get("question_need_observation_row_count")) != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("ahr14_question_observation_row_count_not_24")
    if consistency.get("consistency_guard_status_ref") != P7_R54_AHR15_PASSED_STATUS_REF:
        blockers.append("ahr15_consistency_guard_not_passed")
    if _ahr_int(consistency.get("open_consistency_issue_count")) != 0:
        blockers.append("ahr15_open_consistency_issues_present")
    ready = not blockers
    rating_rows = list(rating.get("rating_rows") or []) if ready else []
    verdict_counts = _ahr_verdict_counts(safe_mapping(rating.get("verdict_counts"))) if ready else {}
    axis_averages = _ahr_axis_averages(rating_rows) if ready else {}
    axis_passed = {
        axis_ref: axis_averages.get(axis_ref, 0.0) >= P7_R54_AHR05_RATING_AXIS_TARGET_THRESHOLDS[axis_ref]
        for axis_ref in P7_R54_AHR05_RATING_AXIS_REFS
    } if ready else {}
    below_counts = {
        axis_ref: _ahr_int(safe_mapping(rating.get("below_target_axis_ref_counts")).get(axis_ref))
        for axis_ref in P7_R54_AHR05_RATING_AXIS_REFS
    } if ready else {}
    below_refs = [axis_ref for axis_ref, count in below_counts.items() if count > 0]
    blockers = dedupe_identifiers(blockers, limit=200, max_length=260)
    status = P7_R54_AHR18_READY_STATUS_REF if ready else P7_R54_AHR18_BLOCKED_STATUS_REF
    reason_refs = [P7_R54_AHR18_READY_REASON_REF] if ready else blockers
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR18_BODYFREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION,
        "phase": P7_PHASE, "step": P7_R54_AHR_STEP, "scope": P7_R54_AHR_SCOPE,
        "policy_kind": P7_R54_AHR_POLICY_KIND, "policy_section": P7_R54_AHR18_STEP_REF,
        "operation_step_ref": P7_R54_AHR18_STEP_REF, "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr18_bodyfree_post_review_summary_20260627",
        "review_session_id": session_id, "source_mode": P7_SOURCE_MODE, "git_connection_required": False, "git_checked": False,
        "ahr17_schema_version": disposal.get("schema_version", ""), "ahr17_material_ref": disposal.get("material_id", ""),
        "ahr17_next_required_step": disposal.get("next_required_step", ""),
        "ahr17_purge_disposal_receipt_status_ref": disposal.get("purge_disposal_receipt_status_ref", ""),
        "ahr17_body_free_post_review_summary_allowed_next": disposal.get("body_free_post_review_summary_allowed_next") is True,
        "ahr17_disposal_verified": disposal.get("disposal_verified") is True,
        "ahr17_actual_disposal_receipt_materialized_here": disposal.get("actual_disposal_receipt_materialized_here") is True,
        "ahr12_schema_version": rating.get("schema_version", ""), "ahr12_material_ref": rating.get("material_id", ""),
        "ahr12_rating_row_normalization_status_ref": rating.get("rating_row_normalization_status_ref", ""),
        "ahr12_rating_row_count": _ahr_int(rating.get("rating_row_count")),
        "ahr13_schema_version": blocker_material.get("schema_version", ""), "ahr13_material_ref": blocker_material.get("material_id", ""),
        "ahr13_blocker_ingestion_status_ref": blocker_material.get("blocker_ingestion_status_ref", ""),
        "ahr14_schema_version": question.get("schema_version", ""), "ahr14_material_ref": question.get("material_id", ""),
        "ahr14_question_need_observation_normalization_status_ref": question.get("question_need_observation_normalization_status_ref", ""),
        "ahr15_schema_version": consistency.get("schema_version", ""), "ahr15_material_ref": consistency.get("material_id", ""),
        "ahr15_consistency_guard_status_ref": consistency.get("consistency_guard_status_ref", ""),
        **_ahr18_current_basis_fields(),
        "operation_current_refs_match_current_execution_basis_260_83_256_169": True,
        "current_execution_basis_refs_match_received_snapshot_260_83_256_169": True,
        "current_execution_basis_refs_match_260_83_256_169_snapshot": True,
        "post_review_summary_status_ref": status, "post_review_summary_reason_refs": reason_refs,
        "execution_blocker_ids": blockers, "open_execution_blocker_ids": blockers,
        "required_case_count": P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "reviewed_case_count": _ahr_int(disposal.get("reviewed_case_count")) if ready else 0,
        "sanitized_review_result_row_count": _ahr_int(disposal.get("sanitized_review_result_row_count")) if ready else 0,
        "rating_row_count": _ahr_int(rating.get("rating_row_count")) if ready else 0,
        "question_observation_row_count": _ahr_int(question.get("question_need_observation_row_count")) if ready else 0,
        "verdict_counts": verdict_counts, "pass_case_count": verdict_counts.get("PASS", 0) if ready else 0,
        "yellow_case_count": verdict_counts.get("YELLOW", 0) if ready else 0,
        "repair_required_case_count": verdict_counts.get("REPAIR_REQUIRED", 0) if ready else 0,
        "red_case_count": verdict_counts.get("RED", 0) if ready else 0,
        "blocked_case_count": verdict_counts.get("BLOCKED", 0) if ready else 0,
        "not_reviewable_case_count": verdict_counts.get("NOT_REVIEWABLE", 0) if ready else 0,
        "rating_axis_refs": list(P7_R54_AHR05_RATING_AXIS_REFS) if ready else [],
        "rating_axis_count": len(P7_R54_AHR05_RATING_AXIS_REFS) if ready else 0,
        "rating_axis_target_thresholds": dict(P7_R54_AHR05_RATING_AXIS_TARGET_THRESHOLDS) if ready else {},
        "axis_score_averages": axis_averages,
        "axis_score_average_target_passed_by_axis": axis_passed,
        "all_axis_score_averages_meet_targets": all(axis_passed.values()) if ready else False,
        "below_target_axis_refs": below_refs,
        "below_target_axis_ref_counts": below_counts,
        "below_target_axis_ref_count": len(below_refs) if ready else 0,
        "below_target_case_count": _ahr_int(rating.get("below_target_case_count")) if ready else 0,
        "open_readfeel_blocker_count": _ahr_int(blocker_material.get("open_readfeel_blocker_count")) if ready else 0,
        "open_execution_blocker_count": _ahr_int(blocker_material.get("open_execution_blocker_count")) if ready else 0,
        "p5_repair_required_observation_row_count": _ahr_int(question.get("p5_repair_required_observation_row_count")) if ready else 0,
        "p4_current_surface_repair_required_row_count": _ahr_int(question.get("p4_current_surface_repair_required_row_count")) if ready else 0,
        "p8_material_candidate_row_count": _ahr_int(consistency.get("p8_material_candidate_row_count")) if ready else 0,
        "plus_single_question_candidate_row_count": _ahr_int(question.get("plus_single_question_candidate_row_count")) if ready else 0,
        "premium_deep_dive_candidate_row_count": _ahr_int(question.get("premium_deep_dive_candidate_row_count")) if ready else 0,
        "disposal_verified": ready and disposal.get("disposal_verified") is True,
        "body_removed": ready and disposal.get("body_removed") is True,
        "reviewer_notes_removed": ready and disposal.get("reviewer_notes_removed") is True,
        "temporary_form_removed": ready and disposal.get("temporary_form_removed") is True,
        "local_packet_exported": False, "content_hash_of_body_stored": False,
        "no_body_leak_validation_passed": ready, "no_question_text_validation_passed": ready, "no_touch_validation_passed": ready,
        "body_free_post_review_summary_materialized_here": ready,
        "actual_human_review_executed_by_person": ready and disposal.get("actual_human_review_executed_by_person") is True,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": ready and rating.get("actual_rating_rows_materialized_here") is True,
        "actual_question_need_observation_rows_materialized_here": ready and question.get("actual_question_need_observation_rows_materialized_here") is True,
        "disposal_receipt_materialized_here": ready and disposal.get("disposal_receipt_materialized_here") is True,
        "actual_disposal_receipt_materialized_here": ready and disposal.get("actual_disposal_receipt_materialized_here") is True,
        "actual_review_evidence_complete": ready,
        "p5_decision_candidate_separation_allowed_next": ready,
        "r52_reintake_claim_blocked_here": True, "p6_p8_release_promotion_blocked_here": True, "p5_finalization_blocked_here": True,
        "p5_human_blind_qa_confirmed_candidate": False, "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_start_allowed": False, "p8_start_allowed": False, "p7_complete": False, "release_allowed": False,
        "implemented_steps": list(P7_R54_AHR18_IMPLEMENTED_STEPS if ready else P7_R54_AHR17_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR18_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR17_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR19_STEP_REF if ready else P7_R54_AHR18_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(), "r54_ahr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(), "body_free": True,
    }
    _add_false_flags_preserving_allowed(material, allowed_true_refs=P7_R54_AHR18_ALLOWED_TRUE_FALSE_FLAG_REFS)
    return material

def assert_p7_r54_ahr18_bodyfree_post_review_summary_contract(data: Mapping[str, Any]) -> bool:
    _assert_bodyfree_no_touch_base_allowing_true_flags(
        data,
        schema_version=P7_R54_AHR18_BODYFREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION,
        policy_section=P7_R54_AHR18_STEP_REF,
        operation_step_ref=P7_R54_AHR18_STEP_REF,
        source="P7-R54-AHR18 body-free post-review summary",
        allowed_true_refs=P7_R54_AHR18_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    _assert_current_execution_basis_refs(data, source="P7-R54-AHR18 body-free post-review summary", actual_basis=True)
    if data.get("ahr17_schema_version") != P7_R54_AHR17_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR18 must follow AHR17")
    ready = data.get("post_review_summary_status_ref") == P7_R54_AHR18_READY_STATUS_REF
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or (), limit=200, max_length=260)
    if blockers != dedupe_identifiers(data.get("open_execution_blocker_ids") or (), limit=200, max_length=260):
        raise ValueError("P7-R54-AHR18 blockers mismatch")
    for key in ("actual_human_review_run_here", "p5_human_blind_qa_confirmed_candidate", "p5_human_blind_qa_confirmed_final", "p6_limited_human_readfeel_start_allowed", "p8_start_allowed", "p7_complete", "release_allowed", "local_packet_exported", "content_hash_of_body_stored"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR18 must keep {key}=False")
    if ready:
        if blockers:
            raise ValueError("P7-R54-AHR18 ready summary must not carry blockers")
        if data.get("post_review_summary_reason_refs") != [P7_R54_AHR18_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR18 ready reason changed")
        for key in ("disposal_verified", "body_removed", "reviewer_notes_removed", "temporary_form_removed", "no_body_leak_validation_passed", "no_question_text_validation_passed", "no_touch_validation_passed", "body_free_post_review_summary_materialized_here", "actual_human_review_executed_by_person", "actual_rating_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "disposal_receipt_materialized_here", "actual_disposal_receipt_materialized_here", "actual_review_evidence_complete", "p5_decision_candidate_separation_allowed_next"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR18 ready summary must keep {key}=True")
        for count_field in ("reviewed_case_count", "sanitized_review_result_row_count", "rating_row_count", "question_observation_row_count"):
            if data.get(count_field) != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
                raise ValueError(f"P7-R54-AHR18 {count_field} changed")
        if tuple(data.get("rating_axis_refs") or ()) != P7_R54_AHR05_RATING_AXIS_REFS:
            raise ValueError("P7-R54-AHR18 rating axes changed")
        if safe_mapping(data.get("rating_axis_target_thresholds")) != P7_R54_AHR05_RATING_AXIS_TARGET_THRESHOLDS:
            raise ValueError("P7-R54-AHR18 thresholds changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR18_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR18 implemented steps changed")
        if data.get("next_required_step") != P7_R54_AHR19_STEP_REF:
            raise ValueError("P7-R54-AHR18 next step changed")
    else:
        if not blockers:
            raise ValueError("P7-R54-AHR18 blocked summary must carry blockers")
        if data.get("actual_review_evidence_complete") is not False or data.get("p5_decision_candidate_separation_allowed_next") is not False:
            raise ValueError("P7-R54-AHR18 blocked summary must not complete evidence")
        if data.get("next_required_step") != P7_R54_AHR18_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR18 blocked next step changed")
    return True


def _ahr19_decision(summary: Mapping[str, Any]) -> str:
    if summary.get("post_review_summary_status_ref") != P7_R54_AHR18_READY_STATUS_REF:
        return P7_R54_AHR19_OPERATION_INCONCLUSIVE_REF
    if summary.get("no_touch_validation_passed") is not True:
        return P7_R54_AHR19_OPERATION_BLOCKED_NO_TOUCH_REF
    if summary.get("no_body_leak_validation_passed") is not True or summary.get("no_question_text_validation_passed") is not True:
        return P7_R54_AHR19_OPERATION_BLOCKED_BODY_LEAK_OR_QUESTION_TEXT_REF
    if summary.get("disposal_verified") is not True or summary.get("body_removed") is not True:
        return P7_R54_AHR19_OPERATION_BLOCKED_DISPOSAL_REF
    if _ahr_int(summary.get("open_execution_blocker_count")) > 0:
        return P7_R54_AHR19_OPERATION_BLOCKED_PREFLIGHT_REF
    if _ahr_int(summary.get("p4_current_surface_repair_required_row_count")) > 0:
        return P7_R54_AHR19_P4_CURRENT_ONLY_REPAIR_REF
    if (
        _ahr_int(summary.get("red_case_count")) > 0 or _ahr_int(summary.get("repair_required_case_count")) > 0
        or _ahr_int(summary.get("open_readfeel_blocker_count")) > 0 or _ahr_int(summary.get("below_target_axis_ref_count")) > 0
        or _ahr_int(summary.get("below_target_case_count")) > 0 or _ahr_int(summary.get("p5_repair_required_observation_row_count")) > 0
        or summary.get("all_axis_score_averages_meet_targets") is not True
    ):
        return P7_R54_AHR19_P5_REPAIR_RETURN_REF
    return P7_R54_AHR19_P5_CONFIRMED_CANDIDATE_REF


def _ahr19_next(decision_ref: str, *, separated: bool) -> str:
    if not separated:
        return P7_R54_AHR19_BLOCKED_NEXT_REQUIRED_STEP_REF
    if decision_ref == P7_R54_AHR19_P5_CONFIRMED_CANDIDATE_REF:
        return P7_R54_AHR20_STEP_REF
    if decision_ref == P7_R54_AHR19_P5_REPAIR_RETURN_REF:
        return P7_R54_AHR19_P5_REPAIR_NEXT_REQUIRED_STEP_REF
    if decision_ref == P7_R54_AHR19_P4_CURRENT_ONLY_REPAIR_REF:
        return P7_R54_AHR19_P4_REPAIR_NEXT_REQUIRED_STEP_REF
    return P7_R54_AHR19_OPERATION_BLOCKED_NEXT_REQUIRED_STEP_REF


def build_p7_r54_ahr19_p5_decision_candidate_separation(
    *,
    bodyfree_post_review_summary: Mapping[str, Any] | None = None,
    review_session_id: Any = P7_R54_AHR_DEFAULT_REVIEW_SESSION_ID,
) -> dict[str, Any]:
    summary = dict(bodyfree_post_review_summary or build_p7_r54_ahr18_bodyfree_post_review_summary())
    session_id = _safe_review_session_id(review_session_id or summary.get("review_session_id"))
    blockers: list[str] = []
    try:
        assert_p7_r54_ahr18_bodyfree_post_review_summary_contract(summary)
    except ValueError:
        blockers.append("ahr18_bodyfree_post_review_summary_contract_invalid")
    if summary.get("post_review_summary_status_ref") != P7_R54_AHR18_READY_STATUS_REF:
        blockers.append("ahr18_bodyfree_post_review_summary_not_ready")
    if summary.get("actual_review_evidence_complete") is not True:
        blockers.append("ahr18_actual_review_evidence_not_complete")
    if summary.get("p5_decision_candidate_separation_allowed_next") is not True:
        blockers.append("ahr18_p5_decision_candidate_separation_not_allowed")
    blockers = dedupe_identifiers(blockers, limit=120, max_length=240)
    separated = not blockers
    decision_ref = _ahr19_decision(summary) if separated else P7_R54_AHR19_OPERATION_INCONCLUSIVE_REF
    p5_candidate = separated and decision_ref == P7_R54_AHR19_P5_CONFIRMED_CANDIDATE_REF
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR19_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION,
        "phase": P7_PHASE, "step": P7_R54_AHR_STEP, "scope": P7_R54_AHR_SCOPE,
        "policy_kind": P7_R54_AHR_POLICY_KIND, "policy_section": P7_R54_AHR19_STEP_REF,
        "operation_step_ref": P7_R54_AHR19_STEP_REF, "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr19_p5_decision_candidate_separation_20260627",
        "review_session_id": session_id, "source_mode": P7_SOURCE_MODE, "git_connection_required": False, "git_checked": False,
        "ahr18_schema_version": summary.get("schema_version", ""), "ahr18_material_ref": summary.get("material_id", ""),
        "ahr18_next_required_step": summary.get("next_required_step", ""),
        "ahr18_post_review_summary_status_ref": summary.get("post_review_summary_status_ref", ""),
        "ahr18_actual_review_evidence_complete": summary.get("actual_review_evidence_complete") is True,
        "ahr18_p5_decision_candidate_separation_allowed_next": summary.get("p5_decision_candidate_separation_allowed_next") is True,
        **_ahr18_current_basis_fields(),
        "operation_current_refs_match_current_execution_basis_260_83_256_169": True,
        "current_execution_basis_refs_match_received_snapshot_260_83_256_169": True,
        "current_execution_basis_refs_match_260_83_256_169_snapshot": True,
        "p5_decision_candidate_separation_status_ref": P7_R54_AHR19_READY_STATUS_REF if separated else P7_R54_AHR19_BLOCKED_STATUS_REF,
        "p5_decision_candidate_separation_reason_refs": [P7_R54_AHR19_READY_REASON_REF] if separated else blockers,
        "execution_blocker_ids": [] if separated else blockers, "open_execution_blocker_ids": [] if separated else blockers,
        "required_case_count": P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "reviewed_case_count": _ahr_int(summary.get("reviewed_case_count")) if separated else 0,
        "rating_row_count": _ahr_int(summary.get("rating_row_count")) if separated else 0,
        "question_observation_row_count": _ahr_int(summary.get("question_observation_row_count")) if separated else 0,
        "decision_candidate_ref": decision_ref, "decision_candidate_ref_allowed": decision_ref in P7_R54_AHR19_ALLOWED_DECISION_REFS,
        "decision_candidate_separated_here": separated, "decision_candidate_bodyfree_only": separated,
        "p5_confirmed_candidate_conditions_satisfied": p5_candidate,
        "p5_repair_return_required": separated and decision_ref == P7_R54_AHR19_P5_REPAIR_RETURN_REF,
        "p4_current_only_repair_required": separated and decision_ref == P7_R54_AHR19_P4_CURRENT_ONLY_REPAIR_REF,
        "r54_operation_inconclusive": decision_ref == P7_R54_AHR19_OPERATION_INCONCLUSIVE_REF,
        "r54_operation_blocked_preflight_or_execution": separated and decision_ref == P7_R54_AHR19_OPERATION_BLOCKED_PREFLIGHT_REF,
        "r54_operation_blocked_disposal": separated and decision_ref == P7_R54_AHR19_OPERATION_BLOCKED_DISPOSAL_REF,
        "r54_operation_blocked_body_leak_or_question_text": separated and decision_ref == P7_R54_AHR19_OPERATION_BLOCKED_BODY_LEAK_OR_QUESTION_TEXT_REF,
        "r54_operation_blocked_no_touch_violation": separated and decision_ref == P7_R54_AHR19_OPERATION_BLOCKED_NO_TOUCH_REF,
        "all_axis_targets_satisfied": separated and summary.get("all_axis_score_averages_meet_targets") is True,
        "red_case_count": _ahr_int(summary.get("red_case_count")) if separated else 0,
        "repair_required_case_count": _ahr_int(summary.get("repair_required_case_count")) if separated else 0,
        "open_readfeel_blocker_count": _ahr_int(summary.get("open_readfeel_blocker_count")) if separated else 0,
        "open_execution_blocker_count": _ahr_int(summary.get("open_execution_blocker_count")) if separated else 0,
        "boundary_violation_blocker_count": 0 if separated else len(blockers),
        "p5_repair_required_observation_row_count": _ahr_int(summary.get("p5_repair_required_observation_row_count")) if separated else 0,
        "p4_current_surface_repair_required_row_count": _ahr_int(summary.get("p4_current_surface_repair_required_row_count")) if separated else 0,
        "below_target_axis_ref_count": _ahr_int(summary.get("below_target_axis_ref_count")) if separated else 0,
        "p8_material_candidate_row_count": _ahr_int(summary.get("p8_material_candidate_row_count")) if separated else 0,
        "p8_material_candidate_count_preserved_for_later": separated and _ahr_int(summary.get("p8_material_candidate_row_count")) > 0,
        "disposal_verified": separated and summary.get("disposal_verified") is True,
        "body_removed": separated and summary.get("body_removed") is True,
        "reviewer_notes_removed": separated and summary.get("reviewer_notes_removed") is True,
        "local_packet_exported": False, "content_hash_of_body_stored": False,
        "no_body_leak_validation_passed": separated and summary.get("no_body_leak_validation_passed") is True,
        "no_question_text_validation_passed": separated and summary.get("no_question_text_validation_passed") is True,
        "no_touch_validation_passed": separated and summary.get("no_touch_validation_passed") is True,
        "actual_human_review_executed_by_person": separated and summary.get("actual_human_review_executed_by_person") is True,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": separated and summary.get("actual_rating_rows_materialized_here") is True,
        "actual_question_need_observation_rows_materialized_here": separated and summary.get("actual_question_need_observation_rows_materialized_here") is True,
        "actual_disposal_receipt_materialized_here": separated and summary.get("actual_disposal_receipt_materialized_here") is True,
        "actual_review_evidence_complete": separated and summary.get("actual_review_evidence_complete") is True,
        "p5_human_blind_qa_confirmed_candidate": p5_candidate, "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_candidate_only_allowed_later": p5_candidate,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_question_design_material_candidate_only_preserved": separated and _ahr_int(summary.get("p8_material_candidate_row_count")) > 0,
        "p8_start_allowed": False, "p7_complete": False, "release_allowed": False,
        "next_decision_route_ref": decision_ref,
        "implemented_steps": list(P7_R54_AHR19_IMPLEMENTED_STEPS if separated else P7_R54_AHR18_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR19_NOT_YET_IMPLEMENTED_STEPS if separated else P7_R54_AHR18_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": _ahr19_next(decision_ref, separated=separated),
        "public_contract": public_contract_flags(), "r54_ahr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(), "body_free": True,
    }
    _add_false_flags_preserving_allowed(material, allowed_true_refs=P7_R54_AHR19_ALLOWED_TRUE_FALSE_FLAG_REFS)
    return material


def assert_p7_r54_ahr19_p5_decision_candidate_separation_contract(data: Mapping[str, Any]) -> bool:
    _assert_bodyfree_no_touch_base_allowing_true_flags(
        data,
        schema_version=P7_R54_AHR19_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION,
        policy_section=P7_R54_AHR19_STEP_REF,
        operation_step_ref=P7_R54_AHR19_STEP_REF,
        source="P7-R54-AHR19 P5 decision candidate separation",
        allowed_true_refs=P7_R54_AHR19_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    _assert_current_execution_basis_refs(data, source="P7-R54-AHR19 P5 decision candidate separation", actual_basis=True)
    if data.get("ahr18_schema_version") != P7_R54_AHR18_BODYFREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR19 must follow AHR18")
    if data.get("decision_candidate_ref") not in P7_R54_AHR19_ALLOWED_DECISION_REFS or data.get("decision_candidate_ref_allowed") is not True:
        raise ValueError("P7-R54-AHR19 decision ref changed")
    for key in ("actual_human_review_run_here", "p5_human_blind_qa_confirmed_final", "p6_limited_human_readfeel_start_allowed", "p8_start_allowed", "p7_complete", "release_allowed", "local_packet_exported", "content_hash_of_body_stored"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR19 must keep {key}=False")
    separated = data.get("p5_decision_candidate_separation_status_ref") == P7_R54_AHR19_READY_STATUS_REF
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or (), limit=120, max_length=240)
    if separated:
        if blockers:
            raise ValueError("P7-R54-AHR19 separated decision must not carry step blockers")
        for count_field in ("reviewed_case_count", "rating_row_count", "question_observation_row_count"):
            if data.get(count_field) != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
                raise ValueError(f"P7-R54-AHR19 {count_field} changed")
        if data.get("decision_candidate_ref") == P7_R54_AHR19_P5_CONFIRMED_CANDIDATE_REF:
            if data.get("p5_human_blind_qa_confirmed_candidate") is not True or data.get("p5_confirmed_candidate_conditions_satisfied") is not True:
                raise ValueError("P7-R54-AHR19 P5 candidate flags missing")
            if data.get("next_required_step") != P7_R54_AHR20_STEP_REF:
                raise ValueError("P7-R54-AHR19 P5 candidate next step changed")
        elif data.get("p5_human_blind_qa_confirmed_candidate") is not False:
            raise ValueError("P7-R54-AHR19 non-candidate must not set P5 candidate")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR19_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR19 implemented steps changed")
    else:
        if not blockers:
            raise ValueError("P7-R54-AHR19 blocked separation must carry blockers")
        if data.get("actual_review_evidence_complete") is not False or data.get("p5_human_blind_qa_confirmed_candidate") is not False:
            raise ValueError("P7-R54-AHR19 blocked separation must not complete or candidate")
        if data.get("next_required_step") != P7_R54_AHR19_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR19 blocked next step changed")
    return True


build_p7_r54_ahr18_bodyfree_post_review_summary_bodyfree = build_p7_r54_ahr18_bodyfree_post_review_summary
assert_p7_r54_ahr18_bodyfree_post_review_summary_bodyfree_contract = assert_p7_r54_ahr18_bodyfree_post_review_summary_contract
build_p7_r54_ahr19_p5_decision_candidate_separation_bodyfree = build_p7_r54_ahr19_p5_decision_candidate_separation
assert_p7_r54_ahr19_p5_decision_candidate_separation_bodyfree_contract = assert_p7_r54_ahr19_p5_decision_candidate_separation_contract
build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr18_bodyfree_post_review_summary = build_p7_r54_ahr18_bodyfree_post_review_summary
assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr18_bodyfree_post_review_summary_contract = assert_p7_r54_ahr18_bodyfree_post_review_summary_contract
build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr19_p5_decision_candidate_separation = build_p7_r54_ahr19_p5_decision_candidate_separation
assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr19_p5_decision_candidate_separation_contract = assert_p7_r54_ahr19_p5_decision_candidate_separation_contract

# ---------------------------------------------------------------------------
# R54-AHR20 / R54-AHR21: P6 candidate-only and P8 material candidate-only
# handoff boundaries.

P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR20: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR19[1:]
P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR21: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR20[1:]
P7_R54_AHR20_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_AHR19_IMPLEMENTED_STEPS, P7_R54_AHR20_STEP_REF)
P7_R54_AHR20_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR20
P7_R54_AHR21_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_AHR20_IMPLEMENTED_STEPS, P7_R54_AHR21_STEP_REF)
P7_R54_AHR21_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR21

P7_R54_AHR20_P6_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.ahr20_p6_candidate_only_handoff.bodyfree.v1"
)
P7_R54_AHR21_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.ahr21_p8_material_candidate_only_handoff.bodyfree.v1"
)
P7_R54_AHR21_P8_MATERIAL_CANDIDATE_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.p8_material_candidate_row.bodyfree.v1"
)

P7_R54_AHR20_READY_STATUS_REF: Final = "AHR_P6_CANDIDATE_ONLY_HANDOFF_READY"
P7_R54_AHR20_BLOCKED_STATUS_REF: Final = "AHR_P6_CANDIDATE_ONLY_HANDOFF_BLOCKED"
P7_R54_AHR20_READY_REASON_REF: Final = "r54_ahr_p6_candidate_only_handoff_ready_bodyfree"
P7_R54_AHR20_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-20_repair_p5_decision_candidate_before_p6_candidate_only_handoff"
)
P7_R54_AHR20_P6_CANDIDATE_SOURCE_REF: Final = "P5_CONFIRMED_CANDIDATE_BODYFREE_ONLY"

P7_R54_AHR21_READY_STATUS_REF: Final = "AHR_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_READY"
P7_R54_AHR21_BLOCKED_STATUS_REF: Final = "AHR_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_BLOCKED"
P7_R54_AHR21_READY_REASON_REF: Final = "r54_ahr_p8_material_candidate_only_handoff_ready_bodyfree"
P7_R54_AHR21_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-21_repair_question_observation_material_candidates_before_final_validation"
)
P7_R54_AHR21_ALLOWED_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = P7_R54_AHR14_P8_MATERIAL_PRIMARY_CLASS_REFS
P7_R54_AHR21_ALLOWED_ONE_QUESTION_FIT_REFS: Final[tuple[str, ...]] = P7_R54_AHR14_P8_MATERIAL_ONE_QUESTION_FIT_REFS

P7_R54_AHR20_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = P7_R54_AHR19_ALLOWED_TRUE_FALSE_FLAG_REFS
P7_R54_AHR21_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = P7_R54_AHR20_ALLOWED_TRUE_FALSE_FLAG_REFS

P7_R54_AHR21_CANDIDATE_ROW_BODYFREE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "reviewer_free_text_included",
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


def build_p7_r54_ahr20_p6_candidate_only_handoff(
    *,
    p5_decision_candidate_separation: Mapping[str, Any] | None = None,
    review_session_id: Any = P7_R54_AHR_DEFAULT_REVIEW_SESSION_ID,
) -> dict[str, Any]:
    """Create a body-free P6 candidate-only handoff without allowing P6 start."""

    decision = dict(p5_decision_candidate_separation or build_p7_r54_ahr19_p5_decision_candidate_separation())
    session_id = _safe_review_session_id(review_session_id or decision.get("review_session_id"))
    blockers: list[str] = []
    try:
        assert_p7_r54_ahr19_p5_decision_candidate_separation_contract(decision)
    except ValueError:
        blockers.append("ahr19_p5_decision_candidate_separation_contract_invalid")
    if decision.get("p5_decision_candidate_separation_status_ref") != P7_R54_AHR19_READY_STATUS_REF:
        blockers.append("ahr19_p5_decision_candidate_separation_not_ready")
    if decision.get("decision_candidate_ref") != P7_R54_AHR19_P5_CONFIRMED_CANDIDATE_REF:
        blockers.append("ahr19_decision_not_p5_confirmed_candidate")
    if decision.get("p5_human_blind_qa_confirmed_candidate") is not True:
        blockers.append("ahr19_p5_confirmed_candidate_flag_missing")
    if decision.get("p5_human_blind_qa_confirmed_final") is not False:
        blockers.append("ahr19_p5_final_promoted_before_p6_candidate_handoff")
    if decision.get("p6_limited_human_readfeel_start_allowed") is not False:
        blockers.append("ahr19_p6_start_allowed_before_candidate_only_handoff")
    if decision.get("p8_start_allowed") is not False or decision.get("release_allowed") is not False:
        blockers.append("ahr19_p8_or_release_promoted_before_candidate_only_handoff")
    blockers = dedupe_identifiers(blockers, limit=120, max_length=240)
    ready = not blockers
    p8_candidate_count = _ahr_int(decision.get("p8_material_candidate_row_count")) if ready else 0
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR20_P6_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION,
        "phase": P7_PHASE, "step": P7_R54_AHR_STEP, "scope": P7_R54_AHR_SCOPE,
        "policy_kind": P7_R54_AHR_POLICY_KIND, "policy_section": P7_R54_AHR20_STEP_REF,
        "operation_step_ref": P7_R54_AHR20_STEP_REF, "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr20_p6_candidate_only_handoff_20260627",
        "review_session_id": session_id, "source_mode": P7_SOURCE_MODE, "git_connection_required": False, "git_checked": False,
        "ahr19_schema_version": decision.get("schema_version", ""), "ahr19_material_ref": decision.get("material_id", ""),
        "ahr19_next_required_step": decision.get("next_required_step", ""),
        "ahr19_p5_decision_candidate_separation_status_ref": decision.get("p5_decision_candidate_separation_status_ref", ""),
        "ahr19_decision_candidate_ref": decision.get("decision_candidate_ref", ""),
        "ahr19_p5_human_blind_qa_confirmed_candidate": decision.get("p5_human_blind_qa_confirmed_candidate") is True,
        "ahr19_actual_review_evidence_complete": decision.get("actual_review_evidence_complete") is True,
        **_ahr18_current_basis_fields(),
        "operation_current_refs_match_current_execution_basis_260_83_256_169": True,
        "current_execution_basis_refs_match_received_snapshot_260_83_256_169": True,
        "current_execution_basis_refs_match_260_83_256_169_snapshot": True,
        "p6_candidate_only_handoff_status_ref": P7_R54_AHR20_READY_STATUS_REF if ready else P7_R54_AHR20_BLOCKED_STATUS_REF,
        "p6_candidate_only_handoff_reason_refs": [P7_R54_AHR20_READY_REASON_REF] if ready else blockers,
        "execution_blocker_ids": [] if ready else blockers, "open_execution_blocker_ids": [] if ready else blockers,
        "required_case_count": P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "reviewed_case_count": _ahr_int(decision.get("reviewed_case_count")) if ready else 0,
        "rating_row_count": _ahr_int(decision.get("rating_row_count")) if ready else 0,
        "question_observation_row_count": _ahr_int(decision.get("question_observation_row_count")) if ready else 0,
        "decision_candidate_ref": decision.get("decision_candidate_ref", "") if ready else P7_R54_AHR19_OPERATION_INCONCLUSIVE_REF,
        "p5_confirmed_candidate_conditions_satisfied": ready and decision.get("p5_confirmed_candidate_conditions_satisfied") is True,
        "p5_human_blind_qa_confirmed_candidate": ready,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_candidate": ready,
        "p6_limited_human_readfeel_candidate_only": ready,
        "p6_limited_human_readfeel_candidate_source_ref": P7_R54_AHR20_P6_CANDIDATE_SOURCE_REF if ready else "",
        "p6_candidate_only_handoff_bodyfree_only": ready,
        "p6_candidate_only_handoff_materialized_here": ready,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_start_allowed": False,
        "p6_start_claim_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p8_material_candidate_row_count": p8_candidate_count,
        "p8_material_candidate_count_preserved_for_later": ready and p8_candidate_count > 0,
        "p8_material_candidate_only_handoff_allowed_next": ready,
        "p8_question_design_material_candidate_only_preserved": ready and p8_candidate_count > 0,
        "p8_question_design_material_candidate": False,
        "p8_start_allowed": False, "p7_complete": False, "release_allowed": False,
        "actual_human_review_executed_by_person": ready and decision.get("actual_human_review_executed_by_person") is True,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": ready and decision.get("actual_rating_rows_materialized_here") is True,
        "actual_question_need_observation_rows_materialized_here": ready and decision.get("actual_question_need_observation_rows_materialized_here") is True,
        "actual_disposal_receipt_materialized_here": ready and decision.get("actual_disposal_receipt_materialized_here") is True,
        "disposal_verified": ready and decision.get("disposal_verified") is True,
        "actual_review_evidence_complete": ready and decision.get("actual_review_evidence_complete") is True,
        "implemented_steps": list(P7_R54_AHR20_IMPLEMENTED_STEPS if ready else P7_R54_AHR19_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR20_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR19_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR21_STEP_REF if ready else P7_R54_AHR20_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(), "r54_ahr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(), "body_free": True,
    }
    _add_false_flags_preserving_allowed(material, allowed_true_refs=P7_R54_AHR20_ALLOWED_TRUE_FALSE_FLAG_REFS)
    return material


def assert_p7_r54_ahr20_p6_candidate_only_handoff_contract(data: Mapping[str, Any]) -> bool:
    _assert_bodyfree_no_touch_base_allowing_true_flags(
        data,
        schema_version=P7_R54_AHR20_P6_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION,
        policy_section=P7_R54_AHR20_STEP_REF,
        operation_step_ref=P7_R54_AHR20_STEP_REF,
        source="P7-R54-AHR20 P6 candidate-only handoff",
        allowed_true_refs=P7_R54_AHR20_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    _assert_current_execution_basis_refs(data, source="P7-R54-AHR20 P6 candidate-only handoff", actual_basis=True)
    if data.get("ahr19_schema_version") != P7_R54_AHR19_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR20 must follow AHR19")
    for key in ("p5_human_blind_qa_confirmed_final", "p6_limited_human_readfeel_start_allowed", "p6_start_allowed", "p8_start_allowed", "p7_complete", "release_allowed", "actual_human_review_run_here"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR20 must keep {key}=False")
    ready = data.get("p6_candidate_only_handoff_status_ref") == P7_R54_AHR20_READY_STATUS_REF
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or (), limit=120, max_length=240)
    if ready:
        if blockers:
            raise ValueError("P7-R54-AHR20 ready handoff must not carry blockers")
        if data.get("p6_candidate_only_handoff_reason_refs") != [P7_R54_AHR20_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR20 ready reason changed")
        for key in (
            "p5_human_blind_qa_confirmed_candidate",
            "p5_confirmed_candidate_conditions_satisfied",
            "p6_limited_human_readfeel_candidate",
            "p6_limited_human_readfeel_candidate_only",
            "p6_candidate_only_handoff_bodyfree_only",
            "p6_candidate_only_handoff_materialized_here",
            "p8_material_candidate_only_handoff_allowed_next",
            "actual_human_review_executed_by_person",
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "disposal_verified",
            "actual_review_evidence_complete",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR20 ready handoff must keep {key}=True")
        if data.get("decision_candidate_ref") != P7_R54_AHR19_P5_CONFIRMED_CANDIDATE_REF:
            raise ValueError("P7-R54-AHR20 decision source changed")
        for count_field in ("reviewed_case_count", "rating_row_count", "question_observation_row_count"):
            if data.get(count_field) != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
                raise ValueError(f"P7-R54-AHR20 {count_field} changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR20_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR20 implemented steps changed")
        if data.get("next_required_step") != P7_R54_AHR21_STEP_REF:
            raise ValueError("P7-R54-AHR20 next step changed")
    else:
        if not blockers:
            raise ValueError("P7-R54-AHR20 blocked handoff must carry blockers")
        if data.get("p6_limited_human_readfeel_candidate") is not False:
            raise ValueError("P7-R54-AHR20 blocked handoff must not set P6 candidate")
        if data.get("p8_material_candidate_only_handoff_allowed_next") is not False:
            raise ValueError("P7-R54-AHR20 blocked handoff must not allow P8 material handoff next")
        if data.get("next_required_step") != P7_R54_AHR20_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR20 blocked next step changed")
    return True


def _ahr21_candidate_rows_from_question_observations(
    rows: Sequence[Any], *, review_session_id: str
) -> tuple[list[dict[str, Any]], list[str]]:
    candidate_rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    for index, raw_row in enumerate(rows, start=1):
        if not isinstance(raw_row, Mapping):
            blockers.append(f"p8_candidate_source_row_{index:03d}_not_mapping")
            continue
        row = safe_mapping(raw_row)
        if row.get("p8_design_material_candidate") is not True:
            continue
        row_ref = clean_identifier(row.get("question_observation_row_ref"), default=f"question_observation_row_{index:03d}", max_length=160)
        primary_class = clean_identifier(row.get("question_need_primary_class"), default="", max_length=160)
        one_question_fit_ref = clean_identifier(row.get("one_question_fit_ref"), default="", max_length=160)
        repair_refs = set(dedupe_identifiers(row.get("repair_required_refs") or (), limit=20, max_length=160))
        row_blockers: list[str] = []
        if _contains_forbidden_ahr_key(row):
            row_blockers.append("forbidden_body_question_path_hash_key_present")
        if row.get("schema_version") != P7_R54_AHR14_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION:
            row_blockers.append("source_question_observation_row_schema_changed")
        if row.get("body_free") is not True:
            row_blockers.append("source_question_observation_row_not_bodyfree")
        for key in P7_R54_AHR21_CANDIDATE_ROW_BODYFREE_FALSE_FLAG_REFS:
            if row.get(key) is not False:
                row_blockers.append(f"{key}_not_false")
        if primary_class not in P7_R54_AHR21_ALLOWED_PRIMARY_CLASS_REFS:
            row_blockers.append("primary_class_not_allowed_for_p8_material")
        if one_question_fit_ref not in P7_R54_AHR21_ALLOWED_ONE_QUESTION_FIT_REFS:
            row_blockers.append("one_question_fit_ref_not_allowed_for_p8_material")
        if row.get("p8_implementation_spec_finalized_here") is not False:
            row_blockers.append("p8_implementation_spec_finalized_here")
        if row.get("p5_repair_required") is True:
            row_blockers.append("p5_repair_required_row_routed_to_p8_material")
        if row.get("p4_current_surface_repair_required") is True:
            row_blockers.append("p4_current_surface_repair_required_row_routed_to_p8_material")
        if row.get("execution_blocker_present") is True:
            row_blockers.append("execution_blocker_row_routed_to_p8_material")
        if row.get("readfeel_blocker_present") is True:
            row_blockers.append("readfeel_blocker_row_routed_to_p8_material")
        if repair_refs - {P7_R54_AHR14_NO_REPAIR_REF}:
            row_blockers.append("repair_required_refs_routed_to_p8_material")
        plan_flags = safe_mapping(row.get("plan_candidate_flags"))
        if plan_flags.get("p8_design_material_candidate") is not True:
            row_blockers.append("plan_candidate_flag_missing_p8_design_material_candidate")
        if plan_flags.get("p8_implementation_spec_finalized_here") is True:
            row_blockers.append("plan_candidate_flag_finalized_p8_spec")
        if row_blockers:
            blockers.extend(f"{row_ref}:{blocker}" for blocker in row_blockers)
            continue
        candidate_rows.append(
            {
                "schema_version": P7_R54_AHR21_P8_MATERIAL_CANDIDATE_ROW_SCHEMA_VERSION,
                "review_session_id": review_session_id,
                "p8_material_candidate_row_ref": f"p8_material_candidate_row_{len(candidate_rows) + 1:03d}",
                "source_question_observation_row_ref": row_ref,
                "source_rating_row_ref": clean_identifier(row.get("source_rating_row_ref"), default="", max_length=120),
                "source_review_result_row_ref": clean_identifier(row.get("source_review_result_row_ref"), default="", max_length=120),
                "case_ref_id": clean_identifier(row.get("case_ref_id"), default="", max_length=120),
                "blind_case_id": clean_identifier(row.get("blind_case_id"), default="", max_length=120),
                "packet_ref_id": clean_identifier(row.get("packet_ref_id"), default="", max_length=120),
                "family": clean_identifier(row.get("family"), default="", max_length=160),
                "case_role": clean_identifier(row.get("case_role"), default="", max_length=160),
                "question_need_primary_class_ref": primary_class,
                "one_question_fit_ref": one_question_fit_ref,
                "ambiguity_kind_refs": dedupe_identifiers(row.get("ambiguity_kind_refs") or (), limit=20, max_length=160),
                "plan_candidate_flag_refs": [
                    ref for ref in ("plus_single_question_candidate_later", "premium_deep_dive_candidate_later", "p8_design_material_candidate")
                    if plan_flags.get(ref) is True
                ],
                "p8_design_material_candidate": True,
                "p8_implementation_spec_finalized_here": False,
                "plus_single_question_candidate_later": primary_class == "plus_single_question_candidate_later",
                "premium_deep_dive_candidate_later": primary_class == "premium_deep_dive_candidate_later",
                "p5_repair_required": False,
                "p4_current_surface_repair_required": False,
                "execution_blocker_present": False,
                "readfeel_blocker_present": False,
                "body_free": True,
                "reviewer_free_text_included": False,
                "raw_body_included": False,
                "returned_emlis_body_included": False,
                "history_surface_included": False,
                "comment_text_included": False,
                "question_text_included": False,
                "draft_question_text_included": False,
                "local_absolute_path_included": False,
                "body_hash_included": False,
                "packet_content_included": False,
            }
        )
    return candidate_rows, dedupe_identifiers(blockers, limit=200, max_length=260)


def build_p7_r54_ahr21_p8_material_candidate_only_handoff(
    *,
    p6_candidate_only_handoff: Mapping[str, Any] | None = None,
    question_need_observation_normalization: Mapping[str, Any] | None = None,
    rating_question_consistency_guard: Mapping[str, Any] | None = None,
    review_session_id: Any = P7_R54_AHR_DEFAULT_REVIEW_SESSION_ID,
) -> dict[str, Any]:
    """Create a body-free P8 material candidate-only handoff without starting P8."""

    p6_handoff = dict(p6_candidate_only_handoff or build_p7_r54_ahr20_p6_candidate_only_handoff())
    question = dict(question_need_observation_normalization or build_p7_r54_ahr14_question_need_observation_normalization())
    consistency = dict(rating_question_consistency_guard or build_p7_r54_ahr15_rating_question_consistency_guard())
    session_id = _safe_review_session_id(review_session_id or p6_handoff.get("review_session_id") or question.get("review_session_id"))
    blockers: list[str] = []
    checks = (
        (assert_p7_r54_ahr20_p6_candidate_only_handoff_contract, p6_handoff, "ahr20_p6_candidate_only_handoff_contract_invalid"),
        (assert_p7_r54_ahr14_question_need_observation_normalization_contract, question, "ahr14_question_need_observation_contract_invalid"),
        (assert_p7_r54_ahr15_rating_question_consistency_guard_contract, consistency, "ahr15_consistency_guard_contract_invalid"),
    )
    for check, material, blocker_id in checks:
        try:
            check(material)
        except ValueError:
            blockers.append(blocker_id)
    if p6_handoff.get("p6_candidate_only_handoff_status_ref") != P7_R54_AHR20_READY_STATUS_REF:
        blockers.append("ahr20_p6_candidate_only_handoff_not_ready")
    if p6_handoff.get("p8_material_candidate_only_handoff_allowed_next") is not True:
        blockers.append("ahr20_p8_material_candidate_only_handoff_not_allowed")
    if question.get("question_need_observation_normalization_status_ref") != P7_R54_AHR14_NORMALIZED_STATUS_REF:
        blockers.append("ahr14_question_need_observation_not_ready")
    if _ahr_int(question.get("question_need_observation_row_count")) != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("ahr14_question_need_observation_row_count_not_24")
    if question.get("actual_question_need_observation_rows_materialized_here") is not True:
        blockers.append("ahr14_actual_question_need_observation_rows_missing")
    if consistency.get("consistency_guard_status_ref") != P7_R54_AHR15_PASSED_STATUS_REF:
        blockers.append("ahr15_consistency_guard_not_passed")
    if _ahr_int(consistency.get("open_consistency_issue_count")) != 0:
        blockers.append("ahr15_open_consistency_issues_present")
    candidate_rows, candidate_blockers = _ahr21_candidate_rows_from_question_observations(
        question.get("question_need_observation_rows") or [], review_session_id=session_id
    ) if not blockers else ([], [])
    blockers.extend(candidate_blockers)
    blockers = dedupe_identifiers(blockers, limit=240, max_length=260)
    ready = not blockers
    rows = candidate_rows if ready else []
    row_refs = [str(row.get("p8_material_candidate_row_ref")) for row in rows]
    source_refs = [str(row.get("source_question_observation_row_ref")) for row in rows]
    plus_count = sum(1 for row in rows if row.get("plus_single_question_candidate_later") is True)
    premium_count = sum(1 for row in rows if row.get("premium_deep_dive_candidate_later") is True)
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR21_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION,
        "phase": P7_PHASE, "step": P7_R54_AHR_STEP, "scope": P7_R54_AHR_SCOPE,
        "policy_kind": P7_R54_AHR_POLICY_KIND, "policy_section": P7_R54_AHR21_STEP_REF,
        "operation_step_ref": P7_R54_AHR21_STEP_REF, "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr21_p8_material_candidate_only_handoff_20260627",
        "review_session_id": session_id, "source_mode": P7_SOURCE_MODE, "git_connection_required": False, "git_checked": False,
        "ahr20_schema_version": p6_handoff.get("schema_version", ""), "ahr20_material_ref": p6_handoff.get("material_id", ""),
        "ahr20_next_required_step": p6_handoff.get("next_required_step", ""),
        "ahr20_p6_candidate_only_handoff_status_ref": p6_handoff.get("p6_candidate_only_handoff_status_ref", ""),
        "ahr20_p8_material_candidate_only_handoff_allowed_next": p6_handoff.get("p8_material_candidate_only_handoff_allowed_next") is True,
        "ahr14_schema_version": question.get("schema_version", ""), "ahr14_material_ref": question.get("material_id", ""),
        "ahr14_question_need_observation_normalization_status_ref": question.get("question_need_observation_normalization_status_ref", ""),
        "ahr15_schema_version": consistency.get("schema_version", ""), "ahr15_material_ref": consistency.get("material_id", ""),
        "ahr15_consistency_guard_status_ref": consistency.get("consistency_guard_status_ref", ""),
        **_ahr18_current_basis_fields(),
        "operation_current_refs_match_current_execution_basis_260_83_256_169": True,
        "current_execution_basis_refs_match_received_snapshot_260_83_256_169": True,
        "current_execution_basis_refs_match_260_83_256_169_snapshot": True,
        "p8_material_candidate_only_handoff_status_ref": P7_R54_AHR21_READY_STATUS_REF if ready else P7_R54_AHR21_BLOCKED_STATUS_REF,
        "p8_material_candidate_only_handoff_reason_refs": [P7_R54_AHR21_READY_REASON_REF] if ready else blockers,
        "execution_blocker_ids": [] if ready else blockers, "open_execution_blocker_ids": [] if ready else blockers,
        "required_case_count": P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "source_question_observation_row_count": _ahr_int(question.get("question_need_observation_row_count")) if ready else 0,
        "p8_material_candidate_rows": rows,
        "p8_material_candidate_row_refs": row_refs,
        "p8_material_candidate_row_ref_count": len(row_refs),
        "source_question_observation_row_refs": source_refs,
        "source_question_observation_row_ref_count": len(source_refs),
        "p8_material_candidate_row_count": len(rows),
        "plus_single_question_candidate_row_count": plus_count,
        "premium_deep_dive_candidate_row_count": premium_count,
        "allowed_primary_class_refs": list(P7_R54_AHR21_ALLOWED_PRIMARY_CLASS_REFS),
        "allowed_one_question_fit_refs": list(P7_R54_AHR21_ALLOWED_ONE_QUESTION_FIT_REFS),
        "p8_question_design_material_candidate": ready and bool(rows),
        "p8_question_design_material_candidate_only": ready and bool(rows),
        "p8_material_candidate_only_handoff_bodyfree_only": ready,
        "p8_material_candidate_rows_bodyfree_only": ready,
        "p8_material_candidate_rows_from_actual_review_only": ready,
        "p8_material_candidates_from_actual_review_only": ready,
        "p8_material_candidates_exclude_question_text": ready,
        "p8_material_candidates_exclude_draft_question_text": ready,
        "p5_repair_targets_excluded_from_p8_material": ready,
        "p4_current_surface_repair_targets_excluded_from_p8_material": ready,
        "execution_blocker_targets_excluded_from_p8_material": ready,
        "readfeel_blocker_targets_excluded_from_p8_material": ready,
        "p8_implementation_spec_finalized_here": False,
        "p8_question_text_created_here": False,
        "p8_trigger_logic_created_here": False,
        "p8_storage_or_ui_created_here": False,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "question_implementation_started_here": False,
        "question_trigger_logic_implemented": False,
        "question_api_implemented": False,
        "question_db_schema_implemented": False,
        "question_rn_ui_implemented": False,
        "question_answer_persistence_implemented": False,
        "p5_human_blind_qa_confirmed_candidate": ready and p6_handoff.get("p5_human_blind_qa_confirmed_candidate") is True,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_candidate": ready and p6_handoff.get("p6_limited_human_readfeel_candidate") is True,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_start_allowed": False,
        "p8_start_allowed": False, "p7_complete": False, "release_allowed": False,
        "actual_human_review_executed_by_person": ready and p6_handoff.get("actual_human_review_executed_by_person") is True,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": ready and p6_handoff.get("actual_rating_rows_materialized_here") is True,
        "actual_question_need_observation_rows_materialized_here": ready and p6_handoff.get("actual_question_need_observation_rows_materialized_here") is True,
        "actual_disposal_receipt_materialized_here": ready and p6_handoff.get("actual_disposal_receipt_materialized_here") is True,
        "disposal_verified": ready and p6_handoff.get("disposal_verified") is True,
        "actual_review_evidence_complete": ready and p6_handoff.get("actual_review_evidence_complete") is True,
        "final_no_body_leak_no_question_text_no_touch_validation_allowed_next": ready,
        "p5_finalization_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR21_IMPLEMENTED_STEPS if ready else P7_R54_AHR20_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR21_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR20_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR22_STEP_REF if ready else P7_R54_AHR21_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(), "r54_ahr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(), "body_free": True,
    }
    _add_false_flags_preserving_allowed(material, allowed_true_refs=P7_R54_AHR21_ALLOWED_TRUE_FALSE_FLAG_REFS)
    return material


def assert_p7_r54_ahr21_p8_material_candidate_only_handoff_contract(data: Mapping[str, Any]) -> bool:
    _assert_bodyfree_no_touch_base_allowing_true_flags(
        data,
        schema_version=P7_R54_AHR21_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION,
        policy_section=P7_R54_AHR21_STEP_REF,
        operation_step_ref=P7_R54_AHR21_STEP_REF,
        source="P7-R54-AHR21 P8 material candidate-only handoff",
        allowed_true_refs=P7_R54_AHR21_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    _assert_current_execution_basis_refs(data, source="P7-R54-AHR21 P8 material candidate-only handoff", actual_basis=True)
    if data.get("ahr20_schema_version") != P7_R54_AHR20_P6_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR21 must follow AHR20")
    if data.get("ahr14_schema_version") != P7_R54_AHR14_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR21 must reference AHR14 question observations")
    if data.get("ahr15_schema_version") != P7_R54_AHR15_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR21 must reference AHR15 consistency guard")
    for key in (
        "p5_human_blind_qa_confirmed_final",
        "p6_limited_human_readfeel_start_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
        "actual_human_review_run_here",
        "question_implementation_started_here",
        "question_trigger_logic_implemented",
        "question_api_implemented",
        "question_db_schema_implemented",
        "question_rn_ui_implemented",
        "question_answer_persistence_implemented",
        "question_text_materialized_here",
        "draft_question_text_materialized_here",
        "p8_implementation_spec_finalized_here",
        "p8_question_text_created_here",
        "p8_trigger_logic_created_here",
        "p8_storage_or_ui_created_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR21 must keep {key}=False")
    ready = data.get("p8_material_candidate_only_handoff_status_ref") == P7_R54_AHR21_READY_STATUS_REF
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or (), limit=240, max_length=260)
    rows = list(data.get("p8_material_candidate_rows") or [])
    if ready:
        if blockers:
            raise ValueError("P7-R54-AHR21 ready handoff must not carry blockers")
        if data.get("p8_material_candidate_only_handoff_reason_refs") != [P7_R54_AHR21_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR21 ready reason changed")
        for key in (
            "p8_material_candidate_only_handoff_bodyfree_only",
            "p8_material_candidate_rows_bodyfree_only",
            "p8_material_candidate_rows_from_actual_review_only",
            "p8_material_candidates_from_actual_review_only",
            "p8_material_candidates_exclude_question_text",
            "p8_material_candidates_exclude_draft_question_text",
            "p5_repair_targets_excluded_from_p8_material",
            "p4_current_surface_repair_targets_excluded_from_p8_material",
            "execution_blocker_targets_excluded_from_p8_material",
            "readfeel_blocker_targets_excluded_from_p8_material",
            "p5_human_blind_qa_confirmed_candidate",
            "p6_limited_human_readfeel_candidate",
            "actual_human_review_executed_by_person",
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "disposal_verified",
            "actual_review_evidence_complete",
            "final_no_body_leak_no_question_text_no_touch_validation_allowed_next",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR21 ready handoff must keep {key}=True")
        if data.get("source_question_observation_row_count") != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR21 source question row count changed")
        if data.get("p8_material_candidate_row_count") != len(rows):
            raise ValueError("P7-R54-AHR21 candidate row count mismatch")
        if tuple(data.get("allowed_primary_class_refs") or ()) != P7_R54_AHR21_ALLOWED_PRIMARY_CLASS_REFS:
            raise ValueError("P7-R54-AHR21 allowed primary class refs changed")
        if tuple(data.get("allowed_one_question_fit_refs") or ()) != P7_R54_AHR21_ALLOWED_ONE_QUESTION_FIT_REFS:
            raise ValueError("P7-R54-AHR21 allowed one-question fit refs changed")
        for row in rows:
            if not isinstance(row, Mapping):
                raise ValueError("P7-R54-AHR21 candidate row must be mapping")
            if _contains_forbidden_ahr_key(row):
                raise ValueError("P7-R54-AHR21 candidate row contains forbidden key")
            if row.get("schema_version") != P7_R54_AHR21_P8_MATERIAL_CANDIDATE_ROW_SCHEMA_VERSION:
                raise ValueError("P7-R54-AHR21 candidate row schema changed")
            if row.get("body_free") is not True or row.get("p8_design_material_candidate") is not True:
                raise ValueError("P7-R54-AHR21 candidate row body-free/material flags changed")
            if row.get("question_need_primary_class_ref") not in P7_R54_AHR21_ALLOWED_PRIMARY_CLASS_REFS:
                raise ValueError("P7-R54-AHR21 candidate primary class changed")
            if row.get("one_question_fit_ref") not in P7_R54_AHR21_ALLOWED_ONE_QUESTION_FIT_REFS:
                raise ValueError("P7-R54-AHR21 candidate one-question fit changed")
            for key in P7_R54_AHR21_CANDIDATE_ROW_BODYFREE_FALSE_FLAG_REFS:
                if row.get(key) is not False:
                    raise ValueError(f"P7-R54-AHR21 candidate row must keep {key}=False")
            for key in (
                "p8_implementation_spec_finalized_here",
                "p5_repair_required",
                "p4_current_surface_repair_required",
                "execution_blocker_present",
                "readfeel_blocker_present",
            ):
                if row.get(key) is not False:
                    raise ValueError(f"P7-R54-AHR21 candidate row must keep {key}=False")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR21_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR21 implemented steps changed")
        if data.get("next_required_step") != P7_R54_AHR22_STEP_REF:
            raise ValueError("P7-R54-AHR21 next step changed")
    else:
        if not blockers:
            raise ValueError("P7-R54-AHR21 blocked handoff must carry blockers")
        if data.get("p8_question_design_material_candidate") is not False:
            raise ValueError("P7-R54-AHR21 blocked handoff must not set P8 material candidate")
        if data.get("final_no_body_leak_no_question_text_no_touch_validation_allowed_next") is not False:
            raise ValueError("P7-R54-AHR21 blocked handoff must not allow final validation")
        if data.get("next_required_step") != P7_R54_AHR21_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR21 blocked next step changed")
    return True


build_p7_r54_ahr20_p6_candidate_only_handoff_bodyfree = build_p7_r54_ahr20_p6_candidate_only_handoff
assert_p7_r54_ahr20_p6_candidate_only_handoff_bodyfree_contract = assert_p7_r54_ahr20_p6_candidate_only_handoff_contract
build_p7_r54_ahr21_p8_material_candidate_only_handoff_bodyfree = build_p7_r54_ahr21_p8_material_candidate_only_handoff
assert_p7_r54_ahr21_p8_material_candidate_only_handoff_bodyfree_contract = assert_p7_r54_ahr21_p8_material_candidate_only_handoff_contract
build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr20_p6_candidate_only_handoff = build_p7_r54_ahr20_p6_candidate_only_handoff
assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr20_p6_candidate_only_handoff_contract = assert_p7_r54_ahr20_p6_candidate_only_handoff_contract
build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr21_p8_material_candidate_only_handoff = build_p7_r54_ahr21_p8_material_candidate_only_handoff
assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr21_p8_material_candidate_only_handoff_contract = assert_p7_r54_ahr21_p8_material_candidate_only_handoff_contract


# R54-AHR22 / R54-AHR23: final body-free validation and R52 handoff envelope.
# These helpers intentionally stop before actual R52 re-intake execution,
# P5 finalization, P6/P8 start, P7 completion, or release.

P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR22: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR21[1:]
P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR23: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR22[1:]
P7_R54_AHR22_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_AHR21_IMPLEMENTED_STEPS, P7_R54_AHR22_STEP_REF)
P7_R54_AHR22_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR22
P7_R54_AHR23_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_AHR22_IMPLEMENTED_STEPS, P7_R54_AHR23_STEP_REF)
P7_R54_AHR23_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR23

P7_R54_AHR22_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.ahr22_final_no_body_leak_no_question_text_no_touch_validation.bodyfree.v1"
)
P7_R54_AHR23_R52_REINTAKE_HANDOFF_ENVELOPE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.ahr23_r52_reintake_handoff_envelope.bodyfree.v1"
)

P7_R54_AHR22_READY_STATUS_REF: Final = "AHR_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_PASSED"
P7_R54_AHR22_PASSED_STATUS_REF: Final = P7_R54_AHR22_READY_STATUS_REF
P7_R54_AHR22_BLOCKED_STATUS_REF: Final = "AHR_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_BLOCKED"
P7_R54_AHR22_READY_REASON_REF: Final = "r54_ahr_final_bodyfree_validation_passed_for_r52_handoff"
P7_R54_AHR22_PASSED_REASON_REF: Final = P7_R54_AHR22_READY_REASON_REF
P7_R54_AHR22_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-22_repair_bodyfree_validation_before_r52_reintake_handoff"
)

P7_R54_AHR23_READY_STATUS_REF: Final = "AHR_R52_REINTAKE_HANDOFF_ENVELOPE_READY"
P7_R54_AHR23_BLOCKED_STATUS_REF: Final = "AHR_R52_REINTAKE_HANDOFF_ENVELOPE_BLOCKED"
P7_R54_AHR23_READY_REASON_REF: Final = "r54_ahr_r52_reintake_handoff_envelope_ready_bodyfree"
P7_R54_AHR23_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-23_repair_final_validation_before_r52_reintake_handoff_envelope"
)
P7_R54_AHR23_R52_CONSUMER_REF: Final = "R52_R51_HANDOFF_P6_P8_START_DECISION_GATE"
P7_R54_AHR23_HANDOFF_ENVELOPE_REF: Final = "R54_AHR23_BODYFREE_R52_REINTAKE_HANDOFF_ENVELOPE"
P7_R54_AHR23_R52_HANDOFF_ENVELOPE_REF: Final = P7_R54_AHR23_HANDOFF_ENVELOPE_REF

P7_R54_AHR22_FORBIDDEN_EXACT_KEY_SCAN_REFS: Final[tuple[str, ...]] = tuple(sorted(P7_R54_AHR_FORBIDDEN_BODY_OR_QUESTION_KEYS))
P7_R54_AHR22_BODYFREE_TRUE_FLAG_FORBIDDEN_REFS: Final[tuple[str, ...]] = P7_R54_AHR_BODY_FREE_FALSE_FLAG_REFS
P7_R54_AHR22_NO_TOUCH_TRUE_FLAG_FORBIDDEN_REFS: Final[tuple[str, ...]] = P7_R54_AHR_NO_TOUCH_FALSE_FLAG_REFS
P7_R54_AHR22_VALIDATION_TARGET_REFS: Final[tuple[str, ...]] = (
    "raw_input_absent",
    "returned_emlis_body_absent",
    "history_surface_absent",
    "comment_text_body_absent",
    "reviewer_free_text_absent",
    "reviewer_notes_body_absent",
    "question_text_absent",
    "draft_question_text_absent",
    "body_hash_absent",
    "packet_content_absent",
    "local_absolute_path_absent",
    "terminal_output_body_absent",
    "api_db_rn_runtime_touch_absent",
)
P7_R54_AHR23_HANDOFF_READY_CONDITION_REFS: Final[tuple[str, ...]] = (
    "actual_human_review_executed_by_person_true",
    "reviewed_case_count_24",
    "sanitized_review_result_row_count_24",
    "rating_row_count_24",
    "question_observation_row_count_24",
    "disposal_verified_true",
    "no_body_leak_validation_passed_true",
    "no_question_text_validation_passed_true",
    "no_touch_validation_passed_true",
    "p5_final_false",
    "p6_start_allowed_false",
    "p8_start_allowed_false",
    "release_allowed_false",
)
P7_R54_AHR23_CLAIM_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "r52_handoff_ready_is_not_actual_r52_reintake_execution",
    "r52_handoff_ready_is_not_p5_final",
    "r52_handoff_ready_is_not_p6_start",
    "r52_handoff_ready_is_not_p8_start",
    "r52_handoff_ready_is_not_release",
)

P7_R54_AHR22_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = P7_R54_AHR21_ALLOWED_TRUE_FALSE_FLAG_REFS
P7_R54_AHR23_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = P7_R54_AHR22_ALLOWED_TRUE_FALSE_FLAG_REFS


def _ahr22_collect_forbidden_exact_key_refs(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_ref = str(key)
            if key_ref in P7_R54_AHR_FORBIDDEN_BODY_OR_QUESTION_KEYS:
                found.append(key_ref)
            found.extend(_ahr22_collect_forbidden_exact_key_refs(child))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child in value:
            found.extend(_ahr22_collect_forbidden_exact_key_refs(child))
    return dedupe_identifiers(found, limit=240, max_length=160)


def _ahr22_collect_true_flag_refs(value: Any, forbidden_refs: tuple[str, ...]) -> list[str]:
    forbidden = set(forbidden_refs)
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_ref = str(key)
            if key_ref in forbidden and child is True:
                found.append(key_ref)
            found.extend(_ahr22_collect_true_flag_refs(child, forbidden_refs))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child in value:
            found.extend(_ahr22_collect_true_flag_refs(child, forbidden_refs))
    return dedupe_identifiers(found, limit=240, max_length=160)


def _ahr22_question_leak_refs(forbidden_key_refs: Sequence[Any], true_flag_refs: Sequence[Any]) -> list[str]:
    combined = [*forbidden_key_refs, *true_flag_refs]
    return dedupe_identifiers(
        [ref for ref in combined if "question" in str(ref) or "draft_question" in str(ref)],
        limit=120,
        max_length=160,
    )


def _ahr22_body_path_hash_leak_refs(forbidden_key_refs: Sequence[Any], true_flag_refs: Sequence[Any]) -> list[str]:
    combined = [*forbidden_key_refs, *true_flag_refs]
    markers = (
        "raw",
        "body",
        "history",
        "comment",
        "reviewer",
        "packet",
        "path",
        "hash",
        "terminal",
        "stdout",
        "stderr",
        "traceback",
    )
    return dedupe_identifiers(
        [ref for ref in combined if any(marker in str(ref) for marker in markers)],
        limit=160,
        max_length=160,
    )


def _ahr22_source_validation_findings(*sources: Mapping[str, Any]) -> dict[str, list[str]]:
    forbidden_key_refs: list[str] = []
    bodyfree_true_refs: list[str] = []
    no_touch_true_refs: list[str] = []
    for source in sources:
        forbidden_key_refs.extend(_ahr22_collect_forbidden_exact_key_refs(source))
        bodyfree_true_refs.extend(_ahr22_collect_true_flag_refs(source, P7_R54_AHR22_BODYFREE_TRUE_FLAG_FORBIDDEN_REFS))
        no_touch_true_refs.extend(_ahr22_collect_true_flag_refs(source, P7_R54_AHR22_NO_TOUCH_TRUE_FLAG_FORBIDDEN_REFS))
    allowed_true_refs = set(P7_R54_AHR22_ALLOWED_TRUE_FALSE_FLAG_REFS)
    forbidden_key_refs = dedupe_identifiers(forbidden_key_refs, limit=240, max_length=160)
    bodyfree_true_refs = dedupe_identifiers(
        [ref for ref in bodyfree_true_refs if ref not in allowed_true_refs],
        limit=240,
        max_length=160,
    )
    no_touch_true_refs = dedupe_identifiers(
        [ref for ref in no_touch_true_refs if ref not in allowed_true_refs],
        limit=240,
        max_length=160,
    )
    return {
        "forbidden_exact_key_refs": forbidden_key_refs,
        "bodyfree_true_flag_refs": bodyfree_true_refs,
        "no_touch_true_flag_refs": no_touch_true_refs,
        "question_leak_refs": _ahr22_question_leak_refs(forbidden_key_refs, bodyfree_true_refs),
        "body_path_hash_leak_refs": _ahr22_body_path_hash_leak_refs(forbidden_key_refs, bodyfree_true_refs),
    }


def _ahr22_contract_invalid_marker(label: str, validator: Any, material: Mapping[str, Any]) -> list[str]:
    if not material:
        return [f"{label}_missing"]
    try:
        validator(material)
    except ValueError:
        return [f"{label}_contract_invalid"]
    return []


def build_p7_r54_ahr22_final_no_body_leak_no_question_text_no_touch_validation(
    *,
    bodyfree_post_review_summary: Mapping[str, Any] | None = None,
    p5_decision_candidate_separation: Mapping[str, Any] | None = None,
    p6_candidate_only_handoff: Mapping[str, Any] | None = None,
    p8_material_candidate_only_handoff: Mapping[str, Any] | None = None,
    review_session_id: Any = P7_R54_AHR_DEFAULT_REVIEW_SESSION_ID,
) -> dict[str, Any]:
    """Build R54-AHR-22 final body-free validation for the complete upstream chain."""

    summary = safe_mapping(bodyfree_post_review_summary)
    decision = safe_mapping(p5_decision_candidate_separation)
    p6_handoff = safe_mapping(p6_candidate_only_handoff)
    p8_handoff = safe_mapping(p8_material_candidate_only_handoff)
    blockers: list[str] = []
    blockers.extend(_ahr22_contract_invalid_marker("ahr18_bodyfree_post_review_summary", assert_p7_r54_ahr18_bodyfree_post_review_summary_contract, summary))
    blockers.extend(_ahr22_contract_invalid_marker("ahr19_p5_decision_candidate_separation", assert_p7_r54_ahr19_p5_decision_candidate_separation_contract, decision))
    blockers.extend(_ahr22_contract_invalid_marker("ahr20_p6_candidate_only_handoff", assert_p7_r54_ahr20_p6_candidate_only_handoff_contract, p6_handoff))
    blockers.extend(_ahr22_contract_invalid_marker("ahr21_p8_material_candidate_only_handoff", assert_p7_r54_ahr21_p8_material_candidate_only_handoff_contract, p8_handoff))
    if summary.get("post_review_summary_status_ref") != P7_R54_AHR18_READY_STATUS_REF:
        blockers.append("ahr18_bodyfree_post_review_summary_not_ready")
    if decision.get("p5_decision_candidate_separation_status_ref") != P7_R54_AHR19_READY_STATUS_REF:
        blockers.append("ahr19_p5_decision_candidate_separation_not_ready")
    if p6_handoff.get("p6_candidate_only_handoff_status_ref") != P7_R54_AHR20_READY_STATUS_REF:
        blockers.append("ahr20_p6_candidate_only_handoff_not_ready")
    if p8_handoff.get("p8_material_candidate_only_handoff_status_ref") != P7_R54_AHR21_READY_STATUS_REF:
        blockers.append("ahr21_p8_material_candidate_only_handoff_not_ready")
    if p8_handoff.get("final_no_body_leak_no_question_text_no_touch_validation_allowed_next") is not True:
        blockers.append("ahr21_final_validation_not_allowed_next")
    for count_field in (
        "reviewed_case_count",
        "sanitized_review_result_row_count",
        "rating_row_count",
        "question_observation_row_count",
    ):
        if _ahr_int(summary.get(count_field)) != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            blockers.append(f"ahr18_{count_field}_not_24")
    for flag_ref in (
        "actual_human_review_executed_by_person",
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "disposal_verified",
        "actual_review_evidence_complete",
        "no_body_leak_validation_passed",
        "no_question_text_validation_passed",
        "no_touch_validation_passed",
    ):
        if summary.get(flag_ref) is not True:
            blockers.append(f"ahr18_{flag_ref}_not_true")
        if flag_ref in p8_handoff and p8_handoff.get(flag_ref) is not True:
            blockers.append(f"ahr21_{flag_ref}_not_true")
    for flag_ref in (
        "p5_human_blind_qa_confirmed_final",
        "p6_limited_human_readfeel_start_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
        "actual_r52_reintake_execution_confirmed",
    ):
        if summary.get(flag_ref) is True or decision.get(flag_ref) is True or p6_handoff.get(flag_ref) is True or p8_handoff.get(flag_ref) is True:
            blockers.append(f"{flag_ref}_promoted_before_ahr22")
    findings = _ahr22_source_validation_findings(summary, decision, p6_handoff, p8_handoff)
    if findings["forbidden_exact_key_refs"]:
        blockers.append("forbidden_exact_key_found_in_bodyfree_sources")
    if findings["bodyfree_true_flag_refs"]:
        blockers.append("bodyfree_false_flag_true_in_bodyfree_sources")
    if findings["question_leak_refs"]:
        blockers.append("question_text_or_draft_question_text_leak_detected")
    if findings["body_path_hash_leak_refs"]:
        blockers.append("body_path_hash_or_terminal_leak_detected")
    if findings["no_touch_true_flag_refs"]:
        blockers.append("no_touch_violation_detected")
    blockers = dedupe_identifiers(blockers, limit=260, max_length=260)
    ready = not blockers
    session_id = _safe_review_session_id(
        review_session_id
        or summary.get("review_session_id")
        or decision.get("review_session_id")
        or p6_handoff.get("review_session_id")
        or p8_handoff.get("review_session_id")
    )
    p8_candidate_row_refs = list(p8_handoff.get("p8_material_candidate_row_refs") or []) if ready else []
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR22_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_STEP,
        "scope": P7_R54_AHR_SCOPE,
        "policy_kind": P7_R54_AHR_POLICY_KIND,
        "policy_section": P7_R54_AHR22_STEP_REF,
        "operation_step_ref": P7_R54_AHR22_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr22_final_no_body_leak_no_question_text_no_touch_validation_20260627",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ahr18_schema_version": summary.get("schema_version", ""),
        "ahr18_material_ref": summary.get("material_id", ""),
        "ahr18_post_review_summary_status_ref": summary.get("post_review_summary_status_ref", ""),
        "ahr19_schema_version": decision.get("schema_version", ""),
        "ahr19_material_ref": decision.get("material_id", ""),
        "ahr19_p5_decision_candidate_separation_status_ref": decision.get("p5_decision_candidate_separation_status_ref", ""),
        "ahr20_schema_version": p6_handoff.get("schema_version", ""),
        "ahr20_material_ref": p6_handoff.get("material_id", ""),
        "ahr20_p6_candidate_only_handoff_status_ref": p6_handoff.get("p6_candidate_only_handoff_status_ref", ""),
        "ahr21_schema_version": p8_handoff.get("schema_version", ""),
        "ahr21_material_ref": p8_handoff.get("material_id", ""),
        "ahr21_p8_material_candidate_only_handoff_status_ref": p8_handoff.get("p8_material_candidate_only_handoff_status_ref", ""),
        **_ahr18_current_basis_fields(),
        "operation_current_refs_match_current_execution_basis_260_83_256_169": True,
        "current_execution_basis_refs_match_received_snapshot_260_83_256_169": True,
        "current_execution_basis_refs_match_260_83_256_169_snapshot": True,
        "validation_target_refs": list(P7_R54_AHR22_VALIDATION_TARGET_REFS),
        "validation_target_ref_count": len(P7_R54_AHR22_VALIDATION_TARGET_REFS),
        "forbidden_exact_key_scan_refs": list(P7_R54_AHR22_FORBIDDEN_EXACT_KEY_SCAN_REFS),
        "bodyfree_true_flag_scan_refs": list(P7_R54_AHR22_BODYFREE_TRUE_FLAG_FORBIDDEN_REFS),
        "no_touch_true_flag_scan_refs": list(P7_R54_AHR22_NO_TOUCH_TRUE_FLAG_FORBIDDEN_REFS),
        "forbidden_exact_key_finding_refs": findings["forbidden_exact_key_refs"],
        "forbidden_exact_key_finding_count": len(findings["forbidden_exact_key_refs"]),
        "bodyfree_true_flag_finding_refs": findings["bodyfree_true_flag_refs"],
        "bodyfree_true_flag_finding_count": len(findings["bodyfree_true_flag_refs"]),
        "body_path_hash_leak_finding_refs": findings["body_path_hash_leak_refs"],
        "body_path_hash_leak_finding_count": len(findings["body_path_hash_leak_refs"]),
        "question_text_leak_finding_refs": findings["question_leak_refs"],
        "question_text_leak_finding_count": len(findings["question_leak_refs"]),
        "no_touch_violation_finding_refs": findings["no_touch_true_flag_refs"],
        "no_touch_violation_finding_count": len(findings["no_touch_true_flag_refs"]),
        "final_validation_status_ref": P7_R54_AHR22_READY_STATUS_REF if ready else P7_R54_AHR22_BLOCKED_STATUS_REF,
        "final_no_body_leak_no_question_text_no_touch_validation_status_ref": P7_R54_AHR22_READY_STATUS_REF if ready else P7_R54_AHR22_BLOCKED_STATUS_REF,
        "final_validation_reason_refs": [P7_R54_AHR22_READY_REASON_REF] if ready else blockers,
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        "required_case_count": P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "reviewed_case_count": _ahr_int(summary.get("reviewed_case_count")) if ready else 0,
        "sanitized_review_result_row_count": _ahr_int(summary.get("sanitized_review_result_row_count")) if ready else 0,
        "rating_row_count": _ahr_int(summary.get("rating_row_count")) if ready else 0,
        "question_observation_row_count": _ahr_int(summary.get("question_observation_row_count")) if ready else 0,
        "p8_material_candidate_row_count": _ahr_int(p8_handoff.get("p8_material_candidate_row_count")) if ready else 0,
        "p8_material_candidate_row_refs": p8_candidate_row_refs,
        "p8_material_candidate_row_ref_count": len(p8_candidate_row_refs),
        "raw_input_absent": ready,
        "returned_emlis_body_absent": ready,
        "history_surface_absent": ready,
        "comment_text_body_absent": ready,
        "reviewer_free_text_absent": ready,
        "reviewer_notes_body_absent": ready,
        "question_text_absent": ready,
        "draft_question_text_absent": ready,
        "body_hash_absent": ready,
        "packet_content_absent": ready,
        "local_absolute_path_absent": ready,
        "terminal_output_body_absent": ready,
        "api_db_rn_runtime_touch_absent": ready,
        "final_no_body_leak_no_question_text_no_touch_validation_passed": ready,
        "no_body_leak_validation_passed": ready,
        "no_question_text_validation_passed": ready,
        "no_touch_validation_passed": ready,
        "final_bodyfree_validation_materialized_here": ready,
        "r52_reintake_handoff_allowed_next": ready,
        "r52_reintake_handoff_envelope_allowed_next": ready,
        "actual_human_review_executed_by_person": ready and summary.get("actual_human_review_executed_by_person") is True,
        "actual_rating_rows_materialized_here": ready and summary.get("actual_rating_rows_materialized_here") is True,
        "actual_question_need_observation_rows_materialized_here": ready and summary.get("actual_question_need_observation_rows_materialized_here") is True,
        "actual_disposal_receipt_materialized_here": ready and summary.get("actual_disposal_receipt_materialized_here") is True,
        "disposal_verified": ready and summary.get("disposal_verified") is True,
        "actual_review_evidence_complete": ready and summary.get("actual_review_evidence_complete") is True,
        "p5_decision_candidate_ref": decision.get("p5_decision_candidate_ref", "") if ready else P7_R54_AHR19_OPERATION_INCONCLUSIVE_REF,
        "p5_human_blind_qa_confirmed_candidate": ready and decision.get("p5_human_blind_qa_confirmed_candidate") is True,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_candidate": ready and p6_handoff.get("p6_limited_human_readfeel_candidate") is True,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_start_allowed": False,
        "p8_question_design_material_candidate": ready and p8_handoff.get("p8_question_design_material_candidate") is True,
        "p8_question_design_material_candidate_only": ready and p8_handoff.get("p8_question_design_material_candidate_only") is True,
        "p8_start_allowed": False,
        "p8_implementation_spec_finalized_here": False,
        "p8_question_text_created_here": False,
        "p8_trigger_logic_created_here": False,
        "p8_storage_or_ui_created_here": False,
        "question_implementation_started_here": False,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "actual_human_review_run_here": False,
        "actual_r52_reintake_execution_confirmed": False,
        "r52_reintake_execution_allowed_here": False,
        "p7_complete": False,
        "release_allowed": False,
        "helper_green_is_not_actual_human_review_complete": True,
        "helper_green_is_not_actual_r52_reintake_execution": True,
        "r52_handoff_ready_is_not_p5_final_or_p6_p8_release": True,
        "p5_finalization_blocked_here": True,
        "r52_reintake_execution_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR22_IMPLEMENTED_STEPS if ready else P7_R54_AHR21_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR22_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR21_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR23_STEP_REF if ready else P7_R54_AHR22_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    _add_false_flags_preserving_allowed(material, allowed_true_refs=P7_R54_AHR22_ALLOWED_TRUE_FALSE_FLAG_REFS)
    return material


def assert_p7_r54_ahr22_final_no_body_leak_no_question_text_no_touch_validation_contract(data: Mapping[str, Any]) -> bool:
    _assert_bodyfree_no_touch_base_allowing_true_flags(
        data,
        schema_version=P7_R54_AHR22_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION,
        policy_section=P7_R54_AHR22_STEP_REF,
        operation_step_ref=P7_R54_AHR22_STEP_REF,
        source="P7-R54-AHR22 final no-body-leak/no-question-text/no-touch validation",
        allowed_true_refs=P7_R54_AHR22_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    _assert_current_execution_basis_refs(data, source="P7-R54-AHR22 final validation", actual_basis=True)
    if tuple(data.get("validation_target_refs") or ()) != P7_R54_AHR22_VALIDATION_TARGET_REFS:
        raise ValueError("P7-R54-AHR22 validation targets changed")
    if data.get("validation_target_ref_count") != len(P7_R54_AHR22_VALIDATION_TARGET_REFS):
        raise ValueError("P7-R54-AHR22 validation target count changed")
    for key in (
        "p5_human_blind_qa_confirmed_final",
        "p6_limited_human_readfeel_start_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
        "actual_human_review_run_here",
        "actual_r52_reintake_execution_confirmed",
        "r52_reintake_execution_allowed_here",
        "question_implementation_started_here",
        "question_text_materialized_here",
        "draft_question_text_materialized_here",
        "p8_implementation_spec_finalized_here",
        "p8_question_text_created_here",
        "p8_trigger_logic_created_here",
        "p8_storage_or_ui_created_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR22 must keep {key}=False")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or (), limit=260, max_length=260)
    if blockers != dedupe_identifiers(data.get("open_execution_blocker_ids") or (), limit=260, max_length=260):
        raise ValueError("P7-R54-AHR22 blocker lists differ")
    for count_field in (
        "forbidden_exact_key_finding_count",
        "bodyfree_true_flag_finding_count",
        "body_path_hash_leak_finding_count",
        "question_text_leak_finding_count",
        "no_touch_violation_finding_count",
    ):
        if data.get(count_field) != len(data.get(count_field.replace("_count", "_refs")) or []):
            raise ValueError(f"P7-R54-AHR22 {count_field} mismatch")
    if tuple(data.get("forbidden_exact_key_scan_refs") or ()) != P7_R54_AHR22_FORBIDDEN_EXACT_KEY_SCAN_REFS:
        raise ValueError("P7-R54-AHR22 forbidden exact key scan refs changed")
    ready = data.get("final_validation_status_ref") == P7_R54_AHR22_READY_STATUS_REF
    if data.get("final_no_body_leak_no_question_text_no_touch_validation_status_ref") != data.get("final_validation_status_ref"):
        raise ValueError("P7-R54-AHR22 status alias changed")
    if ready:
        if blockers:
            raise ValueError("P7-R54-AHR22 ready validation must not carry blockers")
        if data.get("final_validation_reason_refs") != [P7_R54_AHR22_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR22 ready reason changed")
        for count_field in ("reviewed_case_count", "sanitized_review_result_row_count", "rating_row_count", "question_observation_row_count"):
            if data.get(count_field) != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
                raise ValueError(f"P7-R54-AHR22 {count_field} changed")
        for key in P7_R54_AHR22_VALIDATION_TARGET_REFS:
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR22 ready validation must keep {key}=True")
        for key in (
            "final_no_body_leak_no_question_text_no_touch_validation_passed",
            "no_body_leak_validation_passed",
            "no_question_text_validation_passed",
            "no_touch_validation_passed",
            "r52_reintake_handoff_envelope_allowed_next",
            "actual_human_review_executed_by_person",
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "disposal_verified",
            "actual_review_evidence_complete",
            "p5_human_blind_qa_confirmed_candidate",
            "p6_limited_human_readfeel_candidate",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR22 ready validation must keep {key}=True")
        if data.get("forbidden_exact_key_finding_count") != 0:
            raise ValueError("P7-R54-AHR22 ready validation must not carry forbidden key findings")
        if data.get("bodyfree_true_flag_finding_count") != 0 or data.get("no_touch_violation_finding_count") != 0:
            raise ValueError("P7-R54-AHR22 ready validation must not carry flag findings")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR22_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR22 implemented steps changed")
        if data.get("next_required_step") != P7_R54_AHR23_STEP_REF:
            raise ValueError("P7-R54-AHR22 next step changed")
    else:
        if not blockers:
            raise ValueError("P7-R54-AHR22 blocked validation must carry blockers")
        if data.get("r52_reintake_handoff_envelope_allowed_next") is not False:
            raise ValueError("P7-R54-AHR22 blocked validation must not allow R52 envelope")
        if data.get("actual_review_evidence_complete") is not False:
            raise ValueError("P7-R54-AHR22 blocked validation must not complete evidence")
        if data.get("next_required_step") != P7_R54_AHR22_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR22 blocked next step changed")
    return True


def _ahr23_handoff_blockers(final_validation: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not final_validation:
        return ["ahr22_final_validation_missing"]
    if final_validation.get("final_validation_status_ref") != P7_R54_AHR22_READY_STATUS_REF:
        blockers.append("ahr22_final_validation_not_passed")
    if final_validation.get("r52_reintake_handoff_envelope_allowed_next") is not True:
        blockers.append("ahr22_r52_reintake_handoff_envelope_not_allowed")
    for count_field in (
        "reviewed_case_count",
        "sanitized_review_result_row_count",
        "rating_row_count",
        "question_observation_row_count",
    ):
        if _ahr_int(final_validation.get(count_field)) != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            blockers.append(f"ahr22_{count_field}_not_24")
    for flag_ref in (
        "actual_human_review_executed_by_person",
        "disposal_verified",
        "no_body_leak_validation_passed",
        "no_question_text_validation_passed",
        "no_touch_validation_passed",
        "actual_review_evidence_complete",
    ):
        if final_validation.get(flag_ref) is not True:
            blockers.append(f"ahr22_{flag_ref}_not_true")
    for flag_ref in (
        "p5_human_blind_qa_confirmed_final",
        "p6_limited_human_readfeel_start_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "release_allowed",
        "actual_r52_reintake_execution_confirmed",
    ):
        if final_validation.get(flag_ref) is True:
            blockers.append(f"{flag_ref}_promoted_before_ahr23")
    return dedupe_identifiers(blockers, limit=160, max_length=260)


def _ahr23_condition_rows(*, ready: bool) -> list[dict[str, Any]]:
    return [
        {"condition_ref": ref, "satisfied": bool(ready), "body_free": True}
        for ref in P7_R54_AHR23_HANDOFF_READY_CONDITION_REFS
    ]


def build_p7_r54_ahr23_r52_reintake_handoff_envelope(
    *,
    final_validation: Mapping[str, Any] | None = None,
    final_no_body_leak_no_question_text_no_touch_validation: Mapping[str, Any] | None = None,
    review_session_id: Any = P7_R54_AHR_DEFAULT_REVIEW_SESSION_ID,
) -> dict[str, Any]:
    """Build R54-AHR-23 body-free R52 handoff envelope without executing R52."""

    validation = safe_mapping(final_validation or final_no_body_leak_no_question_text_no_touch_validation)
    blockers = _ahr23_handoff_blockers(validation)
    blockers.extend(_ahr22_contract_invalid_marker(
        "ahr22_final_validation",
        assert_p7_r54_ahr22_final_no_body_leak_no_question_text_no_touch_validation_contract,
        validation,
    ))
    blockers = dedupe_identifiers(blockers, limit=160, max_length=260)
    ready = not blockers
    session_id = _safe_review_session_id(review_session_id or validation.get("review_session_id"))
    p8_candidate_row_refs = list(validation.get("p8_material_candidate_row_refs") or []) if ready else []
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR23_R52_REINTAKE_HANDOFF_ENVELOPE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_STEP,
        "scope": P7_R54_AHR_SCOPE,
        "policy_kind": P7_R54_AHR_POLICY_KIND,
        "policy_section": P7_R54_AHR23_STEP_REF,
        "operation_step_ref": P7_R54_AHR23_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr23_r52_reintake_handoff_envelope_20260627",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ahr22_schema_version": validation.get("schema_version", ""),
        "ahr22_material_ref": validation.get("material_id", ""),
        "ahr22_final_validation_status_ref": validation.get("final_validation_status_ref", ""),
        **_ahr18_current_basis_fields(),
        "r52_reintake_handoff_status_ref": P7_R54_AHR23_READY_STATUS_REF if ready else P7_R54_AHR23_BLOCKED_STATUS_REF,
        "r52_reintake_handoff_envelope_status_ref": P7_R54_AHR23_READY_STATUS_REF if ready else P7_R54_AHR23_BLOCKED_STATUS_REF,
        "handoff_status": P7_R54_AHR23_READY_STATUS_REF if ready else P7_R54_AHR23_BLOCKED_STATUS_REF,
        "r52_reintake_handoff_reason_refs": [P7_R54_AHR23_READY_REASON_REF] if ready else blockers,
        "r52_reintake_handoff_envelope_reason_refs": [P7_R54_AHR23_READY_REASON_REF] if ready else blockers,
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        "r52_reintake_consumer_ref": P7_R54_AHR23_R52_CONSUMER_REF,
        "handoff_envelope_ref": P7_R54_AHR23_HANDOFF_ENVELOPE_REF,
        "r52_reintake_handoff_envelope_ref": P7_R54_AHR23_R52_HANDOFF_ENVELOPE_REF if ready else "",
        "handoff_ready_condition_refs": list(P7_R54_AHR23_HANDOFF_READY_CONDITION_REFS),
        "handoff_ready_condition_ref_count": len(P7_R54_AHR23_HANDOFF_READY_CONDITION_REFS),
        "r52_reintake_handoff_ready_conditions": _ahr23_condition_rows(ready=ready),
        "claim_boundary_refs": list(P7_R54_AHR23_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR23_CLAIM_BOUNDARY_REFS),
        "r52_reintake_handoff_envelope_bodyfree_only": ready,
        "r52_reintake_handoff_envelope_materialized_here": ready,
        "handoff_envelope_bodyfree_only": ready,
        "handoff_ready_for_r52_reintake_decision": ready,
        "r52_reintake_handoff_ready": ready,
        "r52_reintake_execution_allowed_here": False,
        "r52_reintake_execution_started_here": False,
        "r52_reintake_execution_completed_here": False,
        "r52_reintake_execution_not_run_here": True,
        "actual_r52_reintake_execution_confirmed": False,
        "actual_execution_basis_ref": P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF,
        "actual_human_review_executed_by_person": ready,
        "reviewed_case_count": _ahr_int(validation.get("reviewed_case_count")) if ready else 0,
        "sanitized_review_result_row_count": _ahr_int(validation.get("sanitized_review_result_row_count")) if ready else 0,
        "rating_row_count": _ahr_int(validation.get("rating_row_count")) if ready else 0,
        "question_observation_row_count": _ahr_int(validation.get("question_observation_row_count")) if ready else 0,
        "disposal_verified": ready,
        "no_body_leak_validation_passed": ready,
        "no_question_text_validation_passed": ready,
        "no_touch_validation_passed": ready,
        "actual_review_evidence_complete": ready,
        "p5_decision_candidate_ref": validation.get("p5_decision_candidate_ref", "") if ready else P7_R54_AHR19_OPERATION_INCONCLUSIVE_REF,
        "p5_human_blind_qa_confirmed_candidate": bool(validation.get("p5_human_blind_qa_confirmed_candidate")) if ready else False,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_candidate": bool(validation.get("p6_limited_human_readfeel_candidate")) if ready else False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_start_allowed": False,
        "p8_question_design_material_candidate": bool(validation.get("p8_question_design_material_candidate")) if ready else False,
        "p8_material_candidate_row_count": _ahr_int(validation.get("p8_material_candidate_row_count")) if ready else 0,
        "p8_material_candidate_row_refs": p8_candidate_row_refs,
        "p8_material_candidate_row_ref_count": len(p8_candidate_row_refs),
        "p8_start_allowed": False,
        "p8_implementation_spec_finalized_here": False,
        "p8_question_text_created_here": False,
        "p8_trigger_logic_created_here": False,
        "p8_storage_or_ui_created_here": False,
        "question_implementation_started_here": False,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "p7_complete": False,
        "release_allowed": False,
        "helper_green_is_not_actual_r52_reintake_execution": True,
        "r52_handoff_ready_is_not_p5_final_or_p6_p8_release": True,
        "p5_finalization_blocked_here": True,
        "r52_reintake_execution_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR23_IMPLEMENTED_STEPS if ready else P7_R54_AHR22_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR23_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR22_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR24_STEP_REF if ready else P7_R54_AHR23_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    _add_false_flags_preserving_allowed(material, allowed_true_refs=P7_R54_AHR23_ALLOWED_TRUE_FALSE_FLAG_REFS)
    return material


def assert_p7_r54_ahr23_r52_reintake_handoff_envelope_contract(data: Mapping[str, Any]) -> bool:
    _assert_bodyfree_no_touch_base_allowing_true_flags(
        data,
        schema_version=P7_R54_AHR23_R52_REINTAKE_HANDOFF_ENVELOPE_SCHEMA_VERSION,
        policy_section=P7_R54_AHR23_STEP_REF,
        operation_step_ref=P7_R54_AHR23_STEP_REF,
        source="P7-R54-AHR23 R52 re-intake handoff envelope",
        allowed_true_refs=P7_R54_AHR23_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    _assert_current_execution_basis_refs(data, source="P7-R54-AHR23 R52 re-intake handoff", actual_basis=True)
    if data.get("r52_reintake_consumer_ref") != P7_R54_AHR23_R52_CONSUMER_REF:
        raise ValueError("P7-R54-AHR23 R52 consumer ref changed")
    if data.get("handoff_envelope_ref") != P7_R54_AHR23_HANDOFF_ENVELOPE_REF:
        raise ValueError("P7-R54-AHR23 handoff envelope ref changed")
    if tuple(data.get("handoff_ready_condition_refs") or ()) != P7_R54_AHR23_HANDOFF_READY_CONDITION_REFS:
        raise ValueError("P7-R54-AHR23 ready condition refs changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR23_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR23 claim boundary refs changed")
    for key in (
        "p5_human_blind_qa_confirmed_final",
        "p6_limited_human_readfeel_start_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
        "actual_r52_reintake_execution_confirmed",
        "r52_reintake_execution_allowed_here",
        "r52_reintake_execution_started_here",
        "r52_reintake_execution_completed_here",
        "question_implementation_started_here",
        "question_text_materialized_here",
        "draft_question_text_materialized_here",
        "p8_implementation_spec_finalized_here",
        "p8_question_text_created_here",
        "p8_trigger_logic_created_here",
        "p8_storage_or_ui_created_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR23 must keep {key}=False")
    ready = data.get("r52_reintake_handoff_status_ref") == P7_R54_AHR23_READY_STATUS_REF
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or (), limit=160, max_length=260)
    if blockers != dedupe_identifiers(data.get("open_execution_blocker_ids") or (), limit=160, max_length=260):
        raise ValueError("P7-R54-AHR23 blockers mismatch")
    if data.get("handoff_status") != data.get("r52_reintake_handoff_status_ref"):
        raise ValueError("P7-R54-AHR23 handoff status alias changed")
    if data.get("r52_reintake_handoff_envelope_status_ref") != data.get("r52_reintake_handoff_status_ref"):
        raise ValueError("P7-R54-AHR23 envelope status alias changed")
    if ready:
        if blockers:
            raise ValueError("P7-R54-AHR23 ready handoff must not carry blockers")
        if data.get("r52_reintake_handoff_reason_refs") != [P7_R54_AHR23_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR23 ready reason changed")
        for key in (
            "r52_reintake_handoff_envelope_bodyfree_only",
            "r52_reintake_handoff_envelope_materialized_here",
            "handoff_envelope_bodyfree_only",
            "handoff_ready_for_r52_reintake_decision",
            "r52_reintake_handoff_ready",
            "r52_reintake_execution_not_run_here",
            "actual_human_review_executed_by_person",
            "disposal_verified",
            "no_body_leak_validation_passed",
            "no_question_text_validation_passed",
            "no_touch_validation_passed",
            "actual_review_evidence_complete",
            "p5_human_blind_qa_confirmed_candidate",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR23 ready handoff must keep {key}=True")
        for count_field in ("reviewed_case_count", "sanitized_review_result_row_count", "rating_row_count", "question_observation_row_count"):
            if data.get(count_field) != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
                raise ValueError(f"P7-R54-AHR23 {count_field} changed")
        if data.get("next_required_step") != P7_R54_AHR24_STEP_REF:
            raise ValueError("P7-R54-AHR23 next step changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR23_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR23 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR23_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR23 not-yet steps changed")
    else:
        if not blockers:
            raise ValueError("P7-R54-AHR23 blocked handoff must carry blockers")
        if data.get("r52_reintake_handoff_ready") is not False or data.get("r52_reintake_handoff_envelope_materialized_here") is not False:
            raise ValueError("P7-R54-AHR23 blocked handoff must not be ready")
        if data.get("actual_review_evidence_complete") is not False:
            raise ValueError("P7-R54-AHR23 blocked handoff must not complete evidence")
        if data.get("next_required_step") != P7_R54_AHR23_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR23 blocked next step changed")
    return True



# R54-AHR24: validation command matrix / documentation output.
# This helper records validation command status and claim boundaries only.  It is
# not a full-suite execution wrapper, not an RN real-device verifier, and not an
# R52 / P5 / P6 / P8 / release decision layer.

P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR24: Final[tuple[str, ...]] = ()
P7_R54_AHR24_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_AHR23_IMPLEMENTED_STEPS, P7_R54_AHR24_STEP_REF)
P7_R54_AHR24_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_FUTURE_STEP_REFS_AFTER_AHR24

P7_R54_AHR24_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.ahr24_validation_command_matrix_documentation_output.bodyfree.v1"
)
P7_R54_AHR24_READY_STATUS_REF: Final = "AHR_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_READY"
P7_R54_AHR24_BLOCKED_STATUS_REF: Final = "AHR_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_BLOCKED"
P7_R54_AHR24_READY_REASON_REF: Final = "r54_ahr_validation_command_matrix_documentation_output_bodyfree_ready"
P7_R54_AHR24_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-24_repair_validation_command_matrix_documentation_output_before_r52_reintake_decision"
)
P7_R54_AHR24_NEXT_REQUIRED_STEP_REF: Final = "R52_reintake_execution_decision_after_AHR24_bodyfree_handoff_documentation"

P7_R54_AHR24_RESULT_STATUS_PASSED_REF: Final = "PASSED"
P7_R54_AHR24_RESULT_STATUS_FAILED_REF: Final = "FAILED"
P7_R54_AHR24_RESULT_STATUS_NOT_EXECUTED_REF: Final = "NOT_EXECUTED"
P7_R54_AHR24_ALLOWED_RESULT_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR24_RESULT_STATUS_PASSED_REF,
    P7_R54_AHR24_RESULT_STATUS_FAILED_REF,
    P7_R54_AHR24_RESULT_STATUS_NOT_EXECUTED_REF,
)
P7_R54_AHR24_COMMAND_REF_REFS: Final[tuple[str, ...]] = (
    "compileall_services_ai_inference_tests",
    "r54_ahr24_target",
    "r54_ahr00_ahr23_chain_split",
    "selected_clr18_clr24_regression",
    "selected_r55_regression",
    "selected_r52_regression",
    "full_backend_suite",
    "rn_contract",
    "rn_real_device_modal",
)
P7_R54_AHR24_REQUIRED_EXECUTED_PASSED_COMMAND_REFS: Final[tuple[str, ...]] = (
    "compileall_services_ai_inference_tests",
    "r54_ahr24_target",
    "r54_ahr00_ahr23_chain_split",
    "selected_clr18_clr24_regression",
    "selected_r55_regression",
    "selected_r52_regression",
)
P7_R54_AHR24_MUST_REMAIN_UNCLAIMED_COMMAND_REFS: Final[tuple[str, ...]] = (
    "full_backend_suite",
    "rn_real_device_modal",
)
P7_R54_AHR24_CLAIM_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "helper_green_is_not_actual_human_review_complete",
    "selected_regression_green_is_not_full_backend_suite_green",
    "rn_contract_green_is_not_rn_real_device_modal_verified",
    "r52_handoff_ready_is_not_p5_final_p6_start_p8_start_release",
)
P7_R54_AHR24_DOCUMENTATION_OMITTED_BODY_REFS: Final[tuple[str, ...]] = (
    "terminal_output_body",
    "stdout_body",
    "stderr_body",
    "traceback_body",
    "raw_body",
    "question_text",
    "local_absolute_path",
)
P7_R54_AHR24_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = P7_R54_AHR23_ALLOWED_TRUE_FALSE_FLAG_REFS

P7_R54_AHR24_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_BASE_REQUIRED_FIELD_REFS,
    "ahr23_schema_version",
    "ahr23_material_ref",
    "ahr23_r52_reintake_handoff_status_ref",
    *P7_R54_AHR_CURRENT_EXECUTION_BASIS_FIELD_REFS,
    "validation_command_matrix_status_ref",
    "documentation_output_status_ref",
    "validation_command_matrix_documentation_output_status_ref",
    "validation_command_matrix_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "command_ref_refs",
    "command_ref_count",
    "required_executed_passed_command_refs",
    "required_executed_passed_command_ref_count",
    "required_executed_passed_command_refs_passed",
    "must_remain_unclaimed_command_refs",
    "must_remain_unclaimed_command_ref_count",
    "command_rows",
    "command_row_count",
    "executed_command_count",
    "not_executed_command_count",
    "passed_command_count",
    "failed_command_count",
    "failed_command_refs",
    "failed_command_ref_count",
    "not_executed_command_refs",
    "not_executed_command_ref_count",
    "passed_command_refs",
    "passed_command_ref_count",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "claim_boundaries_preserved",
    "helper_green_is_not_actual_human_review_complete",
    "selected_regression_green_is_not_full_backend_suite_green",
    "rn_contract_green_is_not_rn_real_device_modal_verified",
    "r52_handoff_ready_is_not_p5_final_p6_start_p8_start_release",
    "documentation_omitted_body_refs",
    "documentation_omitted_body_ref_count",
    "result_memo_bodyfree_only",
    "result_memo_materialized_here",
    "terminal_output_body_recorded",
    "stdout_body_recorded",
    "stderr_body_recorded",
    "traceback_body_recorded",
    "raw_body_recorded",
    "question_text_recorded",
    "local_absolute_path_recorded",
    "full_backend_suite_green_confirmed",
    "rn_contract_green_confirmed",
    "rn_real_device_modal_verified",
    "real_device_modal_verified",
    "actual_r52_reintake_execution_confirmed",
    "r52_reintake_execution_not_run_here",
    "r52_reintake_handoff_ready",
    "actual_human_review_executed_by_person",
    "reviewed_case_count",
    "sanitized_review_result_row_count",
    "rating_row_count",
    "question_observation_row_count",
    "disposal_verified",
    "no_body_leak_validation_passed",
    "no_question_text_validation_passed",
    "no_touch_validation_passed",
    "actual_review_evidence_complete",
    "p5_decision_candidate_ref",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_human_blind_qa_confirmed_final",
    "p6_limited_human_readfeel_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "p6_start_allowed",
    "p8_question_design_material_candidate",
    "p8_material_candidate_row_count",
    "p8_material_candidate_row_refs",
    "p8_material_candidate_row_ref_count",
    "p8_start_allowed",
    "p8_implementation_spec_finalized_here",
    "p8_question_text_created_here",
    "p8_trigger_logic_created_here",
    "p8_storage_or_ui_created_here",
    "question_implementation_started_here",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "p7_complete",
    "release_allowed",
    "p5_finalization_blocked_here",
    "r52_reintake_execution_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "r54_ahr_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R54_AHR_FALSE_FLAG_REFS,
)


def _ahr24_default_claims_for_command(command_ref: str) -> tuple[list[str], list[str]]:
    common_forbidden = [
        "helper_green_is_actual_human_review_complete",
        "p5_human_blind_qa_confirmed_final",
        "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed",
        "release_allowed",
    ]
    if command_ref == "compileall_services_ai_inference_tests":
        return ["compileall_passed_for_modified_ai_helpers"], ["full_backend_suite_green_confirmed", *common_forbidden]
    if command_ref == "r54_ahr24_target":
        return ["r54_ahr24_target_green"], ["actual_r52_reintake_execution_confirmed", *common_forbidden]
    if command_ref == "r54_ahr00_ahr23_chain_split":
        return ["r54_ahr00_ahr23_split_chain_green"], ["full_backend_suite_green_confirmed", *common_forbidden]
    if command_ref.startswith("selected_"):
        return [f"{command_ref}_green"], ["full_backend_suite_green_confirmed", *common_forbidden]
    if command_ref == "rn_contract":
        return ["rn_contract_status_recorded"], ["rn_real_device_modal_verified", "real_device_modal_verified", *common_forbidden]
    if command_ref == "rn_real_device_modal":
        return ["rn_real_device_modal_status_recorded"], ["rn_real_device_modal_verified", "real_device_modal_verified", *common_forbidden]
    if command_ref == "full_backend_suite":
        return ["full_backend_suite_status_recorded"], ["full_backend_suite_green_confirmed", *common_forbidden]
    return ["validation_command_status_recorded"], common_forbidden


def _ahr24_default_command_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for command_ref in P7_R54_AHR24_COMMAND_REF_REFS:
        allowed, forbidden = _ahr24_default_claims_for_command(command_ref)
        rows.append(
            {
                "command_ref": command_ref,
                "executed": False,
                "not_executed": True,
                "result_status_ref": P7_R54_AHR24_RESULT_STATUS_NOT_EXECUTED_REF,
                "result_status": P7_R54_AHR24_RESULT_STATUS_NOT_EXECUTED_REF,
                "pass_count": 0,
                "failure_summary_ref": "",
                "claim_allowed_refs": allowed,
                "claim_forbidden_refs": forbidden,
                "bodyfree_row_only": True,
                "terminal_output_body_recorded": False,
                "stdout_body_recorded": False,
                "stderr_body_recorded": False,
                "traceback_body_recorded": False,
                "raw_body_recorded": False,
                "question_text_recorded": False,
                "local_absolute_path_recorded": False,
            }
        )
    return rows


def _ahr24_normalize_command_rows(raw_rows: Sequence[Any] | None) -> tuple[list[dict[str, Any]], list[str]]:
    defaults = {row["command_ref"]: dict(row) for row in _ahr24_default_command_rows()}
    blockers: list[str] = []
    for index, raw_row in enumerate(raw_rows or (), start=1):
        row = safe_mapping(raw_row)
        if not row:
            blockers.append(f"command_row_{index:02d}_not_mapping")
            continue
        if _contains_forbidden_ahr_key(row):
            blockers.append(f"command_row_{index:02d}_contains_forbidden_body_question_path_hash_key")
            continue
        command_ref = clean_identifier(row.get("command_ref"), default=f"unknown_command_{index:02d}", max_length=160)
        if command_ref not in defaults:
            blockers.append(f"unexpected_command_ref_{command_ref}")
            continue
        allowed, forbidden = _ahr24_default_claims_for_command(command_ref)
        executed = bool(row.get("executed"))
        requested_status = clean_identifier(
            row.get("result_status_ref") or row.get("result_status"),
            default="",
            max_length=80,
        )
        if not requested_status:
            requested_status = P7_R54_AHR24_RESULT_STATUS_PASSED_REF if executed else P7_R54_AHR24_RESULT_STATUS_NOT_EXECUTED_REF
        if requested_status not in P7_R54_AHR24_ALLOWED_RESULT_STATUS_REFS:
            blockers.append(f"command_row_{command_ref}_result_status_not_allowed")
            requested_status = P7_R54_AHR24_RESULT_STATUS_FAILED_REF
        pass_count = _ahr_int(row.get("pass_count"))
        if requested_status == P7_R54_AHR24_RESULT_STATUS_PASSED_REF:
            executed = True
        if requested_status == P7_R54_AHR24_RESULT_STATUS_NOT_EXECUTED_REF:
            executed = False
            pass_count = 0
        failure_summary_ref = clean_identifier(row.get("failure_summary_ref"), default="", max_length=200)
        if requested_status == P7_R54_AHR24_RESULT_STATUS_FAILED_REF and not failure_summary_ref:
            blockers.append(f"command_row_{command_ref}_failed_without_failure_summary_ref")
            failure_summary_ref = f"{command_ref}_failure_summary_ref_required"
        normalized_allowed = dedupe_identifiers([*allowed, *(row.get("claim_allowed_refs") or ())], limit=80, max_length=160)
        normalized_forbidden = dedupe_identifiers([*forbidden, *(row.get("claim_forbidden_refs") or ())], limit=120, max_length=180)
        defaults[command_ref] = {
            "command_ref": command_ref,
            "executed": executed,
            "not_executed": not executed,
            "result_status_ref": requested_status,
            "result_status": requested_status,
            "pass_count": pass_count,
            "failure_summary_ref": failure_summary_ref,
            "claim_allowed_refs": normalized_allowed,
            "claim_forbidden_refs": normalized_forbidden,
            "bodyfree_row_only": True,
            "terminal_output_body_recorded": False,
            "stdout_body_recorded": False,
            "stderr_body_recorded": False,
            "traceback_body_recorded": False,
            "raw_body_recorded": False,
            "question_text_recorded": False,
            "local_absolute_path_recorded": False,
        }
    return [defaults[ref] for ref in P7_R54_AHR24_COMMAND_REF_REFS], dedupe_identifiers(blockers, limit=120, max_length=260)


def _ahr24_command_matrix_blockers(command_rows: Sequence[Mapping[str, Any]]) -> list[str]:
    blockers: list[str] = []
    rows_by_ref = {str(row.get("command_ref")): row for row in command_rows}
    for command_ref in P7_R54_AHR24_REQUIRED_EXECUTED_PASSED_COMMAND_REFS:
        row = rows_by_ref.get(command_ref)
        if not row:
            blockers.append(f"required_command_{command_ref}_missing")
            continue
        if row.get("executed") is not True:
            blockers.append(f"required_command_{command_ref}_not_executed")
        if row.get("result_status_ref") != P7_R54_AHR24_RESULT_STATUS_PASSED_REF:
            blockers.append(f"required_command_{command_ref}_not_passed")
    for command_ref in P7_R54_AHR24_MUST_REMAIN_UNCLAIMED_COMMAND_REFS:
        row = rows_by_ref.get(command_ref)
        if row and row.get("result_status_ref") == P7_R54_AHR24_RESULT_STATUS_PASSED_REF:
            blockers.append(f"{command_ref}_passed_but_must_not_be_claimed_here")
    return dedupe_identifiers(blockers, limit=120, max_length=260)


def _ahr24_boundary_blockers(handoff: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not handoff:
        return ["ahr23_r52_reintake_handoff_envelope_missing"]
    if handoff.get("r52_reintake_handoff_status_ref") != P7_R54_AHR23_READY_STATUS_REF:
        blockers.append("ahr23_r52_reintake_handoff_not_ready")
    if handoff.get("r52_reintake_handoff_ready") is not True:
        blockers.append("ahr23_r52_reintake_handoff_ready_not_true")
    if handoff.get("actual_review_evidence_complete") is not True:
        blockers.append("ahr23_actual_review_evidence_complete_not_true")
    if handoff.get("actual_r52_reintake_execution_confirmed") is True:
        blockers.append("actual_r52_reintake_execution_claimed_before_ahr24")
    for flag_ref in (
        "p5_human_blind_qa_confirmed_final",
        "p6_limited_human_readfeel_start_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
    ):
        if handoff.get(flag_ref) is True:
            blockers.append(f"{flag_ref}_promoted_before_ahr24")
    return dedupe_identifiers(blockers, limit=120, max_length=260)


def build_p7_r54_ahr24_validation_command_matrix_documentation_output(
    *,
    r52_reintake_handoff_envelope: Mapping[str, Any] | None = None,
    command_rows: Sequence[Any] | None = None,
    review_session_id: Any = P7_R54_AHR_DEFAULT_REVIEW_SESSION_ID,
) -> dict[str, Any]:
    """Build R54-AHR-24 body-free validation command matrix / result memo boundary."""

    handoff = safe_mapping(r52_reintake_handoff_envelope)
    normalized_command_rows, command_row_blockers = _ahr24_normalize_command_rows(command_rows)
    blockers: list[str] = []
    blockers.extend(_ahr24_boundary_blockers(handoff))
    blockers.extend(_ahr22_contract_invalid_marker(
        "ahr23_r52_reintake_handoff_envelope",
        assert_p7_r54_ahr23_r52_reintake_handoff_envelope_contract,
        handoff,
    ))
    blockers.extend(command_row_blockers)
    blockers.extend(_ahr24_command_matrix_blockers(normalized_command_rows))
    blockers = dedupe_identifiers(blockers, limit=260, max_length=260)
    ready = not blockers
    rows_by_status = {
        status: [row for row in normalized_command_rows if row.get("result_status_ref") == status]
        for status in P7_R54_AHR24_ALLOWED_RESULT_STATUS_REFS
    }
    passed_command_refs = [str(row["command_ref"]) for row in rows_by_status[P7_R54_AHR24_RESULT_STATUS_PASSED_REF]]
    failed_command_refs = [str(row["command_ref"]) for row in rows_by_status[P7_R54_AHR24_RESULT_STATUS_FAILED_REF]]
    not_executed_command_refs = [str(row["command_ref"]) for row in rows_by_status[P7_R54_AHR24_RESULT_STATUS_NOT_EXECUTED_REF]]
    session_id = _safe_review_session_id(review_session_id or handoff.get("review_session_id"))
    p8_candidate_row_refs = list(handoff.get("p8_material_candidate_row_refs") or []) if ready else []
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR24_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_STEP,
        "scope": P7_R54_AHR_SCOPE,
        "policy_kind": P7_R54_AHR_POLICY_KIND,
        "policy_section": P7_R54_AHR24_STEP_REF,
        "operation_step_ref": P7_R54_AHR24_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr24_validation_command_matrix_documentation_output_20260627",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ahr23_schema_version": handoff.get("schema_version", ""),
        "ahr23_material_ref": handoff.get("material_id", ""),
        "ahr23_r52_reintake_handoff_status_ref": handoff.get("r52_reintake_handoff_status_ref", ""),
        **_ahr18_current_basis_fields(),
        "validation_command_matrix_status_ref": P7_R54_AHR24_READY_STATUS_REF if ready else P7_R54_AHR24_BLOCKED_STATUS_REF,
        "documentation_output_status_ref": P7_R54_AHR24_READY_STATUS_REF if ready else P7_R54_AHR24_BLOCKED_STATUS_REF,
        "validation_command_matrix_documentation_output_status_ref": P7_R54_AHR24_READY_STATUS_REF if ready else P7_R54_AHR24_BLOCKED_STATUS_REF,
        "validation_command_matrix_reason_refs": [P7_R54_AHR24_READY_REASON_REF] if ready else blockers,
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        "command_ref_refs": list(P7_R54_AHR24_COMMAND_REF_REFS),
        "command_ref_count": len(P7_R54_AHR24_COMMAND_REF_REFS),
        "required_executed_passed_command_refs": list(P7_R54_AHR24_REQUIRED_EXECUTED_PASSED_COMMAND_REFS),
        "required_executed_passed_command_ref_count": len(P7_R54_AHR24_REQUIRED_EXECUTED_PASSED_COMMAND_REFS),
        "required_executed_passed_command_refs_passed": all(ref in passed_command_refs for ref in P7_R54_AHR24_REQUIRED_EXECUTED_PASSED_COMMAND_REFS),
        "must_remain_unclaimed_command_refs": list(P7_R54_AHR24_MUST_REMAIN_UNCLAIMED_COMMAND_REFS),
        "must_remain_unclaimed_command_ref_count": len(P7_R54_AHR24_MUST_REMAIN_UNCLAIMED_COMMAND_REFS),
        "command_rows": normalized_command_rows,
        "command_row_count": len(normalized_command_rows),
        "executed_command_count": sum(1 for row in normalized_command_rows if row.get("executed") is True),
        "not_executed_command_count": len(not_executed_command_refs),
        "passed_command_count": len(passed_command_refs),
        "failed_command_count": len(failed_command_refs),
        "failed_command_refs": failed_command_refs,
        "failed_command_ref_count": len(failed_command_refs),
        "not_executed_command_refs": not_executed_command_refs,
        "not_executed_command_ref_count": len(not_executed_command_refs),
        "passed_command_refs": passed_command_refs,
        "passed_command_ref_count": len(passed_command_refs),
        "claim_boundary_refs": list(P7_R54_AHR24_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR24_CLAIM_BOUNDARY_REFS),
        "claim_boundaries_preserved": ready,
        "helper_green_is_not_actual_human_review_complete": True,
        "selected_regression_green_is_not_full_backend_suite_green": True,
        "rn_contract_green_is_not_rn_real_device_modal_verified": True,
        "r52_handoff_ready_is_not_p5_final_p6_start_p8_start_release": True,
        "documentation_omitted_body_refs": list(P7_R54_AHR24_DOCUMENTATION_OMITTED_BODY_REFS),
        "documentation_omitted_body_ref_count": len(P7_R54_AHR24_DOCUMENTATION_OMITTED_BODY_REFS),
        "result_memo_bodyfree_only": ready,
        "result_memo_materialized_here": ready,
        "terminal_output_body_recorded": False,
        "stdout_body_recorded": False,
        "stderr_body_recorded": False,
        "traceback_body_recorded": False,
        "raw_body_recorded": False,
        "question_text_recorded": False,
        "local_absolute_path_recorded": False,
        "full_backend_suite_green_confirmed": False,
        "rn_contract_green_confirmed": "rn_contract" in passed_command_refs,
        "rn_real_device_modal_verified": False,
        "real_device_modal_verified": False,
        "actual_r52_reintake_execution_confirmed": False,
        "r52_reintake_execution_not_run_here": True,
        "r52_reintake_handoff_ready": ready,
        "actual_human_review_executed_by_person": ready,
        "actual_rating_rows_materialized_here": ready,
        "actual_question_need_observation_rows_materialized_here": ready,
        "actual_disposal_receipt_materialized_here": ready,
        "reviewed_case_count": _ahr_int(handoff.get("reviewed_case_count")) if ready else 0,
        "sanitized_review_result_row_count": _ahr_int(handoff.get("sanitized_review_result_row_count")) if ready else 0,
        "rating_row_count": _ahr_int(handoff.get("rating_row_count")) if ready else 0,
        "question_observation_row_count": _ahr_int(handoff.get("question_observation_row_count")) if ready else 0,
        "disposal_verified": ready,
        "no_body_leak_validation_passed": ready,
        "no_question_text_validation_passed": ready,
        "no_touch_validation_passed": ready,
        "actual_review_evidence_complete": ready,
        "p5_decision_candidate_ref": handoff.get("p5_decision_candidate_ref", "") if ready else P7_R54_AHR19_OPERATION_INCONCLUSIVE_REF,
        "p5_human_blind_qa_confirmed_candidate": bool(handoff.get("p5_human_blind_qa_confirmed_candidate")) if ready else False,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_candidate": bool(handoff.get("p6_limited_human_readfeel_candidate")) if ready else False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_start_allowed": False,
        "p8_question_design_material_candidate": bool(handoff.get("p8_question_design_material_candidate")) if ready else False,
        "p8_material_candidate_row_count": _ahr_int(handoff.get("p8_material_candidate_row_count")) if ready else 0,
        "p8_material_candidate_row_refs": p8_candidate_row_refs,
        "p8_material_candidate_row_ref_count": len(p8_candidate_row_refs),
        "p8_start_allowed": False,
        "p8_implementation_spec_finalized_here": False,
        "p8_question_text_created_here": False,
        "p8_trigger_logic_created_here": False,
        "p8_storage_or_ui_created_here": False,
        "question_implementation_started_here": False,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "p7_complete": False,
        "release_allowed": False,
        "p5_finalization_blocked_here": True,
        "r52_reintake_execution_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR24_IMPLEMENTED_STEPS if ready else P7_R54_AHR23_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR24_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR23_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR24_NEXT_REQUIRED_STEP_REF if ready else P7_R54_AHR24_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    _add_false_flags_preserving_allowed(material, allowed_true_refs=P7_R54_AHR24_ALLOWED_TRUE_FALSE_FLAG_REFS)
    return material


def assert_p7_r54_ahr24_validation_command_matrix_documentation_output_contract(data: Mapping[str, Any]) -> bool:
    _assert_bodyfree_no_touch_base_allowing_true_flags(
        data,
        schema_version=P7_R54_AHR24_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION,
        policy_section=P7_R54_AHR24_STEP_REF,
        operation_step_ref=P7_R54_AHR24_STEP_REF,
        source="P7-R54-AHR24 validation command matrix documentation output",
        allowed_true_refs=P7_R54_AHR24_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    _assert_current_execution_basis_refs(data, source="P7-R54-AHR24 validation command matrix documentation output", actual_basis=True)
    _assert_required_fields(
        data,
        required=P7_R54_AHR24_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR24 validation command matrix documentation output",
    )
    if tuple(data.get("command_ref_refs") or ()) != P7_R54_AHR24_COMMAND_REF_REFS:
        raise ValueError("P7-R54-AHR24 command refs changed")
    if tuple(data.get("required_executed_passed_command_refs") or ()) != P7_R54_AHR24_REQUIRED_EXECUTED_PASSED_COMMAND_REFS:
        raise ValueError("P7-R54-AHR24 required command refs changed")
    if tuple(data.get("must_remain_unclaimed_command_refs") or ()) != P7_R54_AHR24_MUST_REMAIN_UNCLAIMED_COMMAND_REFS:
        raise ValueError("P7-R54-AHR24 unclaimed command refs changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR24_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR24 claim boundary refs changed")
    if tuple(data.get("documentation_omitted_body_refs") or ()) != P7_R54_AHR24_DOCUMENTATION_OMITTED_BODY_REFS:
        raise ValueError("P7-R54-AHR24 omitted body refs changed")
    command_rows = [safe_mapping(row) for row in (data.get("command_rows") or ())]
    if [row.get("command_ref") for row in command_rows] != list(P7_R54_AHR24_COMMAND_REF_REFS):
        raise ValueError("P7-R54-AHR24 command row refs changed")
    for row in command_rows:
        if row.get("result_status_ref") not in P7_R54_AHR24_ALLOWED_RESULT_STATUS_REFS:
            raise ValueError("P7-R54-AHR24 command row status changed")
        if row.get("result_status") != row.get("result_status_ref"):
            raise ValueError("P7-R54-AHR24 command row status alias changed")
        if row.get("executed") is row.get("not_executed"):
            raise ValueError("P7-R54-AHR24 command row executed/not_executed flags changed")
        for key in (
            "bodyfree_row_only",
        ):
            if row.get(key) is not True:
                raise ValueError(f"P7-R54-AHR24 command row must keep {key}=True")
        for key in (
            "terminal_output_body_recorded",
            "stdout_body_recorded",
            "stderr_body_recorded",
            "traceback_body_recorded",
            "raw_body_recorded",
            "question_text_recorded",
            "local_absolute_path_recorded",
        ):
            if row.get(key) is not False:
                raise ValueError(f"P7-R54-AHR24 command row must keep {key}=False")
    passed_command_refs = tuple(data.get("passed_command_refs") or ())
    failed_command_refs = tuple(data.get("failed_command_refs") or ())
    not_executed_command_refs = tuple(data.get("not_executed_command_refs") or ())
    if data.get("command_row_count") != len(P7_R54_AHR24_COMMAND_REF_REFS):
        raise ValueError("P7-R54-AHR24 command row count changed")
    if data.get("passed_command_count") != len(passed_command_refs):
        raise ValueError("P7-R54-AHR24 passed command count changed")
    if data.get("failed_command_count") != len(failed_command_refs):
        raise ValueError("P7-R54-AHR24 failed command count changed")
    if data.get("not_executed_command_count") != len(not_executed_command_refs):
        raise ValueError("P7-R54-AHR24 not-executed command count changed")
    if data.get("failed_command_ref_count") != len(failed_command_refs):
        raise ValueError("P7-R54-AHR24 failed command ref count changed")
    if data.get("not_executed_command_ref_count") != len(not_executed_command_refs):
        raise ValueError("P7-R54-AHR24 not-executed command ref count changed")
    if data.get("passed_command_ref_count") != len(passed_command_refs):
        raise ValueError("P7-R54-AHR24 passed command ref count changed")
    for key in (
        "terminal_output_body_recorded",
        "stdout_body_recorded",
        "stderr_body_recorded",
        "traceback_body_recorded",
        "raw_body_recorded",
        "question_text_recorded",
        "local_absolute_path_recorded",
        "full_backend_suite_green_confirmed",
        "rn_real_device_modal_verified",
        "real_device_modal_verified",
        "actual_r52_reintake_execution_confirmed",
        "p5_human_blind_qa_confirmed_final",
        "p6_limited_human_readfeel_start_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
        "question_implementation_started_here",
        "question_text_materialized_here",
        "draft_question_text_materialized_here",
        "p8_implementation_spec_finalized_here",
        "p8_question_text_created_here",
        "p8_trigger_logic_created_here",
        "p8_storage_or_ui_created_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR24 must keep {key}=False")
    for key in (
        "helper_green_is_not_actual_human_review_complete",
        "selected_regression_green_is_not_full_backend_suite_green",
        "rn_contract_green_is_not_rn_real_device_modal_verified",
        "r52_handoff_ready_is_not_p5_final_p6_start_p8_start_release",
        "r52_reintake_execution_not_run_here",
        "p5_finalization_blocked_here",
        "r52_reintake_execution_blocked_here",
        "p6_p8_release_promotion_blocked_here",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR24 must keep {key}=True")
    ready = data.get("validation_command_matrix_status_ref") == P7_R54_AHR24_READY_STATUS_REF
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or (), limit=260, max_length=260)
    if blockers != dedupe_identifiers(data.get("open_execution_blocker_ids") or (), limit=260, max_length=260):
        raise ValueError("P7-R54-AHR24 blockers mismatch")
    if data.get("documentation_output_status_ref") != data.get("validation_command_matrix_status_ref"):
        raise ValueError("P7-R54-AHR24 documentation status alias changed")
    if data.get("validation_command_matrix_documentation_output_status_ref") != data.get("validation_command_matrix_status_ref"):
        raise ValueError("P7-R54-AHR24 combined status alias changed")
    if ready:
        if blockers:
            raise ValueError("P7-R54-AHR24 ready output must not carry blockers")
        if data.get("validation_command_matrix_reason_refs") != [P7_R54_AHR24_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR24 ready reason changed")
        if data.get("required_executed_passed_command_refs_passed") is not True:
            raise ValueError("P7-R54-AHR24 ready output must have required commands passed")
        for command_ref in P7_R54_AHR24_REQUIRED_EXECUTED_PASSED_COMMAND_REFS:
            if command_ref not in passed_command_refs:
                raise ValueError("P7-R54-AHR24 ready output missing passed required command")
        if "full_backend_suite" in passed_command_refs or "rn_real_device_modal" in passed_command_refs:
            raise ValueError("P7-R54-AHR24 must not claim full backend suite or RN real device green")
        for key in (
            "result_memo_bodyfree_only",
            "result_memo_materialized_here",
            "claim_boundaries_preserved",
            "r52_reintake_handoff_ready",
            "actual_human_review_executed_by_person",
            "disposal_verified",
            "no_body_leak_validation_passed",
            "no_question_text_validation_passed",
            "no_touch_validation_passed",
            "actual_review_evidence_complete",
            "p5_human_blind_qa_confirmed_candidate",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR24 ready output must keep {key}=True")
        for count_field in ("reviewed_case_count", "sanitized_review_result_row_count", "rating_row_count", "question_observation_row_count"):
            if data.get(count_field) != P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
                raise ValueError(f"P7-R54-AHR24 {count_field} changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR24_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR24 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR24_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR24 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR24_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR24 next step changed")
    else:
        if not blockers:
            raise ValueError("P7-R54-AHR24 blocked output must carry blockers")
        if data.get("result_memo_bodyfree_only") is not False or data.get("result_memo_materialized_here") is not False:
            raise ValueError("P7-R54-AHR24 blocked output must not materialize result memo")
        if data.get("next_required_step") != P7_R54_AHR24_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR24 blocked next step changed")
    return True


build_p7_r54_ahr24_validation_command_matrix_documentation_output_bodyfree = build_p7_r54_ahr24_validation_command_matrix_documentation_output
assert_p7_r54_ahr24_validation_command_matrix_documentation_output_bodyfree_contract = assert_p7_r54_ahr24_validation_command_matrix_documentation_output_contract
build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr24_validation_command_matrix_documentation_output = build_p7_r54_ahr24_validation_command_matrix_documentation_output
assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr24_validation_command_matrix_documentation_output_contract = assert_p7_r54_ahr24_validation_command_matrix_documentation_output_contract

build_p7_r54_ahr22_final_no_body_leak_no_question_text_no_touch_validation_bodyfree = build_p7_r54_ahr22_final_no_body_leak_no_question_text_no_touch_validation
assert_p7_r54_ahr22_final_no_body_leak_no_question_text_no_touch_validation_bodyfree_contract = assert_p7_r54_ahr22_final_no_body_leak_no_question_text_no_touch_validation_contract
build_p7_r54_ahr23_r52_reintake_handoff_envelope_bodyfree = build_p7_r54_ahr23_r52_reintake_handoff_envelope
assert_p7_r54_ahr23_r52_reintake_handoff_envelope_bodyfree_contract = assert_p7_r54_ahr23_r52_reintake_handoff_envelope_contract
build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr22_final_no_body_leak_no_question_text_no_touch_validation = build_p7_r54_ahr22_final_no_body_leak_no_question_text_no_touch_validation
assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr22_final_no_body_leak_no_question_text_no_touch_validation_contract = assert_p7_r54_ahr22_final_no_body_leak_no_question_text_no_touch_validation_contract
build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr23_r52_reintake_handoff_envelope = build_p7_r54_ahr23_r52_reintake_handoff_envelope
assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr23_r52_reintake_handoff_envelope_contract = assert_p7_r54_ahr23_r52_reintake_handoff_envelope_contract
