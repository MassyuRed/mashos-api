# -*- coding: utf-8 -*-
"""P7-R54 actual local-only human review operation re-entry helpers.

This module implements the initial operation-layer steps from the
2026-06-25 R54 re-entry design:

R54-OP-00 freezes the scope / no-touch boundary for the operation layer.
R54-OP-01 refreezes the operation-current snapshot refs received for this work
session, while keeping the existing R54/R55 helper refs as historical regression
context only.
R54-OP-02 records the historical helper source delta without mixing it into the
actual review basis.
R54-OP-03 intakes the R55 hold decision that requires R54 actual review.
R54-OP-04 checks the local-only preflight boundary before body-full packet
generation can be requested.
R54-OP-05 freezes the 24-case body-free manifest separately from P4-R11 audit
rows.
R54-OP-06 materializes only the body-free packet generation request.
R54-OP-07 records the local-only packet generation operation as a body-free
receipt boundary, without putting packet content or local paths in artifacts.
R54-OP-08 scans packet completeness and export-denylist status as body-free
counts / refs only.
R54-OP-09 freezes reviewer instructions and the rating form as selection-only
body-free material, without question text or reviewer free-text export fields.
R54-OP-10 captures the local-only human review operation state as body-free
refs/counts only.
R54-OP-11 captures supplied reviewer selections as sanitized body-free rows
without raw body, reviewer free text, question text, local paths, or body hashes.
R54-OP-12 normalizes those sanitized selections into body-free rating rows.
R54-OP-13 ingests readfeel blockers separately from execution blockers.
R54-OP-14 normalizes question-need observation selections into body-free enum rows,
without creating question text or P8 implementation specs.
R54-OP-15 checks rating rows against question-observation rows so P5 repair needs
are not hidden as P8 material candidates.
R54-OP-16 captures pause / abort / expiration policy without keeping body-full
material in artifacts.
R54-OP-17 accepts only a body-free purge / disposal receipt boundary.
R54-OP-18 summarizes rating / blocker / question / disposal evidence as
body-free counts.
R54-OP-19 separates P5 decision candidates without finalizing P5.
R54-OP-20 creates a P6 limited human readfeel candidate handoff only.
R54-OP-21 aggregates P8 question-design material candidates only, without
starting or implementing P8.
R54-OP-22 performs final no-body-leak / no-question-text / no-touch validation.
R54-OP-23 materializes the R52 re-intake handoff as body-free evidence.
R54-OP-24 records the validation command matrix, unexecuted scopes, and green
claim boundaries as documentation output without storing terminal output.

It intentionally does not put body-full packets in artifacts, run an actual
human review itself, perform local deletion itself, implement P8 questions,
store terminal output, modify API/DB/RN/runtime contracts, start P6/P8, complete
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
from emlis_ai_p7_r47_local_review_packet_policy import (
    P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS,
    P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
    P7_R47_EXPORT_DENYLIST_PATTERNS,
    P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR,
    P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
)
from emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet import (
    P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION,
    P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION,
    assert_p7_r48_p5_first_formal_review_case_matrix_contract,
    build_p7_r48_p5_first_formal_review_case_matrix,
)
from emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run import (
    P7_R51_REQUIRED_CASE_COUNT,
)
from emlis_ai_p7_r54_p5_human_blind_qa_actual_local_review_result_handoff import (
    P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS,
    P7_R54_POLICY_KIND,
    P7_R54_SCOPE,
    P7_R54_STEP,
)
from emlis_ai_p7_r55_r54_evidence_reconcile_r52_reintake_decision_materialization import (
    P7_R55_ACTUAL_REVIEW_EVIDENCE_MISSING_GAP_STATUS_REF,
    P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS,
    P7_R55_DEFAULT_DECISION_STATUS_REF,
    P7_R55_DEFAULT_MISSING_EVIDENCE_REFS,
    P7_R55_DEFAULT_R52_EXISTING_DECISION_EQUIVALENT_REF,
    P7_R55_DEFAULT_R52_REINTAKE_DECISION_REF,
    P7_R55_P5_DECISION_STATUS_NOT_REVIEWED_REF,
    P7_R55_POLICY_KIND,
    P7_R55_R52_REINTAKE_DECISION_MATERIALIZATION_SCHEMA_VERSION,
    P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF,
    P7_R55_R54_DEFAULT_P5_DECISION_CANDIDATE_REF,
    P7_R55_R54_DEFAULT_REVIEW_OPERATION_STATE_REF,
    P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
    P7_R55_SCOPE,
    P7_R55_STEP,
    assert_p7_r55_r52_reintake_decision_materialization_bodyfree_contract,
    build_p7_r55_r52_reintake_decision_materialization_bodyfree,
)


P7_R54_OPERATION_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_scope_no_touch_boundary_freeze.bodyfree.v1"
)
P7_R54_OPERATION_CURRENT_SNAPSHOT_REFREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_current_snapshot_refreeze.bodyfree.v1"
)
P7_R54_OPERATION_SOURCE_DELTA_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_source_delta_row.bodyfree.v1"
)
P7_R54_OPERATION_HISTORICAL_HELPER_SOURCE_DELTA_RECONCILE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_historical_helper_source_delta_reconcile.bodyfree.v1"
)
P7_R54_OPERATION_R55_HOLD_INTAKE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_r55_hold_intake.bodyfree.v1"
)
P7_R54_OPERATION_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_local_only_preflight.bodyfree.v1"
)
P7_R54_OPERATION_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_24_case_manifest_freeze.bodyfree.v1"
)
P7_R54_OPERATION_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_body_full_packet_generation_request.bodyfree.v1"
)
P7_R54_OPERATION_PACKET_GENERATION_LOCAL_OPERATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_packet_generation_local_operation.bodyfree.v1"
)
P7_R54_OPERATION_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_packet_completeness_export_denylist_scan.bodyfree.v1"
)
P7_R54_OPERATION_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_reviewer_instruction_rating_form_freeze.bodyfree.v1"
)
P7_R54_OPERATION_ACTUAL_HUMAN_REVIEW_OPERATION_STATE_CAPTURE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_actual_human_review_operation_state_capture.bodyfree.v1"
)
P7_R54_OPERATION_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_sanitized_review_result_row.bodyfree.v1"
)
P7_R54_OPERATION_SANITIZED_REVIEW_RESULT_CAPTURE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_sanitized_review_result_capture.bodyfree.v1"
)
P7_R54_OPERATION_RATING_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_rating_row.bodyfree.v1"
)
P7_R54_OPERATION_RATING_ROW_NORMALIZATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_rating_row_normalization.bodyfree.v1"
)
P7_R54_OPERATION_READFEEL_BLOCKER_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_readfeel_blocker_row.bodyfree.v1"
)
P7_R54_OPERATION_EXECUTION_BLOCKER_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_execution_blocker_row.bodyfree.v1"
)
P7_R54_OPERATION_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_readfeel_blocker_execution_blocker_ingestion.bodyfree.v1"
)
P7_R54_OPERATION_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_question_need_observation_row.bodyfree.v1"
)
P7_R54_OPERATION_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_question_need_observation_normalization.bodyfree.v1"
)
P7_R54_OPERATION_RATING_QUESTION_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_rating_question_consistency_issue_row.bodyfree.v1"
)
P7_R54_OPERATION_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_rating_question_consistency_guard.bodyfree.v1"
)

P7_R54_OPERATION_REENTRY_STEP: Final = "R54_actual_local_only_human_review_operation_reentry_20260625"
P7_R54_OPERATION_REENTRY_SCOPE: Final = "p5_human_blind_qa_actual_local_review_operation_reentry"
P7_R54_OPERATION_REENTRY_POLICY_KIND: Final = "r54_actual_local_only_human_review_operation_reentry_bodyfree_boundary"
P7_R54_OPERATION_DEFAULT_REVIEW_SESSION_ID: Final = "p7_r54_actual_local_review_operation_reentry_20260625"
P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_REF: Final = "operation_current_refs_only"
P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_ALLOWED_REF: Final = "current_ref_only"

P7_R54_OP00_STEP_REF: Final = "R54-OP-00_scope_no_touch_boundary_freeze"
P7_R54_OP01_STEP_REF: Final = "R54-OP-01_operation_current_snapshot_refs_refreeze"
P7_R54_OP02_STEP_REF: Final = "R54-OP-02_historical_helper_source_delta_reconcile"
P7_R54_OP02_NEXT_REQUIRED_STEP_REF: Final = P7_R54_OP02_STEP_REF
P7_R54_OP03_STEP_REF: Final = "R54-OP-03_r55_hold_intake"
P7_R54_OP04_NEXT_REQUIRED_STEP_REF: Final = "R54-OP-04_local_only_preflight"
P7_R54_OP04_STEP_REF: Final = P7_R54_OP04_NEXT_REQUIRED_STEP_REF
P7_R54_OP05_STEP_REF: Final = "R54-OP-05_24_case_manifest_freeze"
P7_R54_OP06_STEP_REF: Final = "R54-OP-06_local_only_body_full_packet_generation_request"
P7_R54_OP07_STEP_REF: Final = "R54-OP-07_packet_generation_local_operation"
P7_R54_OP08_STEP_REF: Final = "R54-OP-08_packet_completeness_export_denylist_scan"
P7_R54_OP09_STEP_REF: Final = "R54-OP-09_reviewer_instruction_rating_form_freeze"
P7_R54_OP10_STEP_REF: Final = "R54-OP-10_actual_human_review_operation_state_capture"
P7_R54_OP11_STEP_REF: Final = "R54-OP-11_sanitized_review_result_capture"
P7_R54_OP12_STEP_REF: Final = "R54-OP-12_rating_row_normalization"
P7_R54_OP13_STEP_REF: Final = "R54-OP-13_readfeel_blocker_execution_blocker_ingestion"
P7_R54_OP14_STEP_REF: Final = "R54-OP-14_question_need_observation_normalization"
P7_R54_OP15_STEP_REF: Final = "R54-OP-15_rating_question_consistency_guard"
P7_R54_OP04_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "local_only_preflight_repair"
P7_R54_OP05_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "local_only_preflight_repair_before_24_case_manifest_freeze"
P7_R54_OP06_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "24_case_manifest_repair_before_packet_generation_request"
P7_R54_OP07_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "local_only_packet_generation_operation_receipt_required"
P7_R54_OP08_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "packet_completeness_scan_repair_before_reviewer_instruction_rating_form_freeze"
P7_R54_OP09_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "packet_scan_repair_before_reviewer_instruction_rating_form_freeze"
P7_R54_OP10_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "reviewer_instruction_rating_form_repair_before_actual_review_state_capture"
P7_R54_OP10_NOT_COMPLETED_NEXT_REQUIRED_STEP_REF: Final = "actual_human_review_operation_continue_or_retry_before_sanitized_result_capture"
P7_R54_OP11_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "sanitized_review_result_capture_repair_before_rating_row_normalization"
P7_R54_OP12_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "rating_row_normalization_repair_before_readfeel_blocker_execution_blocker_ingestion"
P7_R54_OP13_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "readfeel_blocker_execution_blocker_ingestion_repair_before_question_observation_normalization"
P7_R54_OP14_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "question_need_observation_normalization_repair_before_rating_question_consistency_guard"
P7_R54_OP15_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "rating_question_consistency_guard_repair_before_pause_abort_expiration_protocol"
P7_R54_OP_FIRST_NEXT_WORK_REF: Final = "r54_op02_historical_helper_source_delta_reconcile_before_preflight"
P7_R54_OP_NEXT_WORK_AFTER_OP03_REF: Final = "r54_op04_local_only_preflight_after_r55_hold_intake"
P7_R54_OP_NEXT_WORK_AFTER_OP04_REF: Final = "r54_op05_24_case_manifest_freeze_after_local_only_preflight"
P7_R54_OP_NEXT_WORK_AFTER_OP05_REF: Final = "r54_op06_bodyfree_packet_generation_request_after_manifest_freeze"
P7_R54_OP_NEXT_WORK_AFTER_OP06_REF: Final = "r54_op07_packet_generation_local_operation_after_bodyfree_request"
P7_R54_OP_NEXT_WORK_AFTER_OP07_REF: Final = "r54_op08_packet_completeness_export_denylist_scan_after_local_operation_receipt"
P7_R54_OP_NEXT_WORK_AFTER_OP08_REF: Final = "r54_op09_reviewer_instruction_rating_form_freeze_after_packet_scan"
P7_R54_OP_NEXT_WORK_AFTER_OP09_REF: Final = "r54_op10_actual_human_review_operation_state_capture_after_form_freeze"
P7_R54_OP_NEXT_WORK_AFTER_OP10_REF: Final = "r54_op11_sanitized_review_result_capture_after_state_capture"
P7_R54_OP_NEXT_WORK_AFTER_OP11_REF: Final = "r54_op12_rating_row_normalization_after_sanitized_result_capture"
P7_R54_OP_NEXT_WORK_AFTER_OP12_REF: Final = "r54_op13_readfeel_blocker_execution_blocker_ingestion_after_rating_row_normalization"
P7_R54_OP_NEXT_WORK_AFTER_OP13_REF: Final = "r54_op14_question_need_observation_normalization_after_blocker_ingestion"
P7_R54_OP_NEXT_WORK_AFTER_OP14_REF: Final = "r54_op15_rating_question_consistency_guard_after_question_observation_normalization"
P7_R54_OP_NEXT_WORK_AFTER_OP15_REF: Final = "r54_op16_pause_abort_expiration_protocol_after_rating_question_consistency_guard"

P7_R54_OPERATION_CURRENT_REFS: Final[dict[str, str]] = {
    "premise_zip_ref": "Cocolon_前提資料(254).zip",
    "implemented_materials_zip_ref": "EmlisAIの実装済み資料(80).zip",
    "rn_zip_ref": "Cocolon(253).zip",
    "backend_zip_ref": "mashos-api(166).zip",
    "roadmap_ref": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619(13).md",
    "pre_design_memo_ref": "Cocolon_EmlisAI_P7_R54ActualReviewOperation_Reentry_PreDesignMemo_20260625.md",
    "detailed_design_ref": "Cocolon_EmlisAI_P7_R54ActualLocalOnlyHumanReviewOperation_Reentry_DetailedDesign_ImplementationOrder_20260625.md",
}

P7_R54_OPERATION_HISTORICAL_HELPER_REFS: Final[dict[str, dict[str, str]]] = {
    "r54_helper_current_received_snapshot_refs": dict(P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS),
    "r55_helper_current_received_snapshot_refs": dict(P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS),
}
P7_R54_OPERATION_HISTORICAL_HELPER_REF_GROUP_REFS: Final[tuple[str, ...]] = tuple(
    P7_R54_OPERATION_HISTORICAL_HELPER_REFS.keys()
)

P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP01: Final[tuple[str, ...]] = (
    P7_R54_OP02_NEXT_REQUIRED_STEP_REF,
    "R54-OP-03_r55_hold_intake",
    "R54-OP-04_local_only_preflight",
    "R54-OP-05_24_case_manifest_freeze",
    P7_R54_OP06_STEP_REF,
    P7_R54_OP07_STEP_REF,
    P7_R54_OP08_STEP_REF,
    P7_R54_OP09_STEP_REF,
    P7_R54_OP10_STEP_REF,
    P7_R54_OP11_STEP_REF,
    P7_R54_OP12_STEP_REF,
    P7_R54_OP13_STEP_REF,
    P7_R54_OP14_STEP_REF,
    P7_R54_OP15_STEP_REF,
    "R54-OP-16_pause_abort_expiration_protocol",
    "R54-OP-17_purge_disposal_receipt",
    "R54-OP-18_bodyfree_post_review_summary",
    "R54-OP-19_p5_decision_candidate_separation",
    "R54-OP-20_p6_candidate_handoff",
    "R54-OP-21_p8_material_candidate_handoff",
    "R54-OP-22_final_no_body_leak_no_question_text_no_touch_validation",
    "R54-OP-23_r52_reintake_handoff",
    "R54-OP-24_validation_command_matrix_documentation_output",
)
P7_R54_OP00_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_OP00_STEP_REF,)
P7_R54_OP00_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_OP01_STEP_REF,
    *P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP01,
)
P7_R54_OP01_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_OP00_STEP_REF,
    P7_R54_OP01_STEP_REF,
)
P7_R54_OP01_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP01
P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP02: Final[tuple[str, ...]] = P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP01[1:]
P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP03: Final[tuple[str, ...]] = P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP01[2:]
P7_R54_OP02_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_OP00_STEP_REF,
    P7_R54_OP01_STEP_REF,
    P7_R54_OP02_STEP_REF,
)
P7_R54_OP02_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP02
P7_R54_OP03_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_OP00_STEP_REF,
    P7_R54_OP01_STEP_REF,
    P7_R54_OP02_STEP_REF,
    P7_R54_OP03_STEP_REF,
)
P7_R54_OP03_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP03
P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP04: Final[tuple[str, ...]] = P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP01[3:]
P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP05: Final[tuple[str, ...]] = P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP01[4:]
P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP06: Final[tuple[str, ...]] = P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP01[5:]
P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP07: Final[tuple[str, ...]] = P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP01[6:]
P7_R54_OP04_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_OP00_STEP_REF,
    P7_R54_OP01_STEP_REF,
    P7_R54_OP02_STEP_REF,
    P7_R54_OP03_STEP_REF,
    P7_R54_OP04_STEP_REF,
)
P7_R54_OP04_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP04
P7_R54_OP05_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_OP00_STEP_REF,
    P7_R54_OP01_STEP_REF,
    P7_R54_OP02_STEP_REF,
    P7_R54_OP03_STEP_REF,
    P7_R54_OP04_STEP_REF,
    P7_R54_OP05_STEP_REF,
)
P7_R54_OP05_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP05
P7_R54_OP06_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_OP00_STEP_REF,
    P7_R54_OP01_STEP_REF,
    P7_R54_OP02_STEP_REF,
    P7_R54_OP03_STEP_REF,
    P7_R54_OP04_STEP_REF,
    P7_R54_OP05_STEP_REF,
    P7_R54_OP06_STEP_REF,
)
P7_R54_OP06_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP06
P7_R54_OP07_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_OP00_STEP_REF,
    P7_R54_OP01_STEP_REF,
    P7_R54_OP02_STEP_REF,
    P7_R54_OP03_STEP_REF,
    P7_R54_OP04_STEP_REF,
    P7_R54_OP05_STEP_REF,
    P7_R54_OP06_STEP_REF,
    P7_R54_OP07_STEP_REF,
)
P7_R54_OP07_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP07
P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP08: Final[tuple[str, ...]] = P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP01[7:]
P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP09: Final[tuple[str, ...]] = P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP01[8:]
P7_R54_OP08_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_OP00_STEP_REF,
    P7_R54_OP01_STEP_REF,
    P7_R54_OP02_STEP_REF,
    P7_R54_OP03_STEP_REF,
    P7_R54_OP04_STEP_REF,
    P7_R54_OP05_STEP_REF,
    P7_R54_OP06_STEP_REF,
    P7_R54_OP07_STEP_REF,
    P7_R54_OP08_STEP_REF,
)
P7_R54_OP08_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP08
P7_R54_OP09_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_OP00_STEP_REF,
    P7_R54_OP01_STEP_REF,
    P7_R54_OP02_STEP_REF,
    P7_R54_OP03_STEP_REF,
    P7_R54_OP04_STEP_REF,
    P7_R54_OP05_STEP_REF,
    P7_R54_OP06_STEP_REF,
    P7_R54_OP07_STEP_REF,
    P7_R54_OP08_STEP_REF,
    P7_R54_OP09_STEP_REF,
)
P7_R54_OP09_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP09
P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP10: Final[tuple[str, ...]] = P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP01[9:]
P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP11: Final[tuple[str, ...]] = P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP01[10:]
P7_R54_OP10_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_OP09_IMPLEMENTED_STEPS,
    P7_R54_OP10_STEP_REF,
)
P7_R54_OP10_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP10
P7_R54_OP11_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_OP10_IMPLEMENTED_STEPS,
    P7_R54_OP11_STEP_REF,
)
P7_R54_OP11_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP11
P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP12: Final[tuple[str, ...]] = P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP01[11:]
P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP13: Final[tuple[str, ...]] = P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP01[12:]
P7_R54_OP12_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_OP11_IMPLEMENTED_STEPS,
    P7_R54_OP12_STEP_REF,
)
P7_R54_OP12_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP12
P7_R54_OP13_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_OP12_IMPLEMENTED_STEPS,
    P7_R54_OP13_STEP_REF,
)
P7_R54_OP13_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP13
P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP14: Final[tuple[str, ...]] = P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP01[13:]
P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP15: Final[tuple[str, ...]] = P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP01[14:]
P7_R54_OP14_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_OP13_IMPLEMENTED_STEPS,
    P7_R54_OP14_STEP_REF,
)
P7_R54_OP14_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP14
P7_R54_OP15_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_OP14_IMPLEMENTED_STEPS,
    P7_R54_OP15_STEP_REF,
)
P7_R54_OP15_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_OP_FUTURE_STEP_REFS_AFTER_OP15

P7_R54_SOURCE_DELTA_ROW_REFS: Final[tuple[str, ...]] = (
    "r54_helper_refs_vs_operation_current_refs",
    "r55_helper_refs_vs_operation_current_refs",
)
P7_R54_SOURCE_DELTA_COMPARISON_STATUS_REF: Final = "HISTORICAL_HELPER_REFS_DIFFER_FROM_OPERATION_CURRENT_REFS"
P7_R54_SOURCE_DELTA_CLASSIFICATION_REF: Final = "historical_regression_context_not_actual_review_basis"
P7_R54_R55_HOLD_INTAKE_STATUS_REF: Final = "R55_HOLD_INTAKE_REQUIRES_R54_ACTUAL_LOCAL_REVIEW"

P7_R54_OP04_PREFLIGHT_READY_STATUS_REF: Final = "PREFLIGHT_READY"
P7_R54_OP04_PREFLIGHT_BLOCKED_STATUS_REF: Final = "PREFLIGHT_BLOCKED"
P7_R54_OP04_LOCAL_REVIEW_ROOT_READY_REF: Final = "local_review_root_declared_outside_repo_export_scope"
P7_R54_OP04_LOCAL_REVIEW_ROOT_MISSING_REF: Final = "missing_local_review_root_presence_ref"
P7_R54_OP04_EXPLICIT_ALLOW_TOKEN_REF: Final = "R54_ACTUAL_LOCAL_REVIEW_BODY_FULL_PACKET_GENERATION_ALLOWED_20260625"
P7_R54_OP04_PURGE_PLAN_READY_REF: Final = "r54_actual_local_review_purge_plan_ready_bodyfree"
P7_R54_OP04_RETENTION_POLICY_READY_REF: Final = "r54_actual_local_review_retention_policy_ready_bodyfree"
P7_R54_OP04_EXPORT_DENYLIST_POLICY_READY_REF: Final = "r54_actual_local_review_export_denylist_policy_ready_bodyfree"
P7_R54_OP04_PREFLIGHT_READY_REASON_REF: Final = "local_only_preflight_ready_for_24_case_manifest_freeze"
P7_R54_OP04_ALLOWED_PREFLIGHT_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_OP04_PREFLIGHT_READY_STATUS_REF,
    P7_R54_OP04_PREFLIGHT_BLOCKED_STATUS_REF,
)
P7_R54_OP04_REQUIRED_DELETE_TARGET_REFS: Final[tuple[str, ...]] = (
    "body_full_packet",
    "reviewer_notes",
    "temporary_form",
)
P7_R54_OP05_MANIFEST_READY_STATUS_REF: Final = "MANIFEST_FROZEN_READY_FOR_BODYFREE_PACKET_GENERATION_REQUEST"
P7_R54_OP05_MANIFEST_BLOCKED_STATUS_REF: Final = "MANIFEST_BLOCKED_BY_LOCAL_ONLY_PREFLIGHT"
P7_R54_OP05_ALLOWED_MANIFEST_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_OP05_MANIFEST_READY_STATUS_REF,
    P7_R54_OP05_MANIFEST_BLOCKED_STATUS_REF,
)
P7_R54_OP05_REVIEWER_IDENTIFIER_POLICY_REF: Final = "reviewer_receives_blind_case_id_only_controller_keeps_case_refs"
P7_R54_OP05_CASE_DISTRIBUTION: Final[dict[str, int]] = {
    family: count for family, count, _case_role in P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION
}

P7_R54_OP06_REQUEST_READY_STATUS_REF: Final = "PACKET_GENERATION_REQUESTED_BODYFREE"
P7_R54_OP06_REQUEST_BLOCKED_STATUS_REF: Final = "PACKET_GENERATION_REQUEST_BLOCKED_BY_24_CASE_MANIFEST"
P7_R54_OP06_ALLOWED_REQUEST_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_OP06_REQUEST_READY_STATUS_REF,
    P7_R54_OP06_REQUEST_BLOCKED_STATUS_REF,
)
P7_R54_OP06_PACKET_GENERATION_REQUEST_REF: Final = "r54_local_only_body_full_packet_generation_request_bodyfree_20260625"
P7_R54_OP06_PACKET_GENERATION_REQUEST_POLICY_REF: Final = "packet_generation_request_is_bodyfree_refs_only"
P7_R54_OP06_LOCAL_ONLY_OUTPUT_SCOPE_REF: Final = "local_only_body_full_packets_do_not_export"
P7_R54_OP06_READY_REASON_REF: Final = "r54_bodyfree_packet_generation_request_ready_after_manifest_freeze"

P7_R54_OP07_LOCAL_OPERATION_READY_STATUS_REF: Final = "PACKET_GENERATED_LOCAL_ONLY_UNVERIFIED"
P7_R54_OP07_LOCAL_OPERATION_BLOCKED_STATUS_REF: Final = "PACKET_GENERATION_LOCAL_OPERATION_BLOCKED"
P7_R54_OP07_ALLOWED_LOCAL_OPERATION_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_OP07_LOCAL_OPERATION_READY_STATUS_REF,
    P7_R54_OP07_LOCAL_OPERATION_BLOCKED_STATUS_REF,
)
P7_R54_OP07_LOCAL_OPERATION_RECEIPT_REF: Final = "r54_local_only_packet_generation_receipt_bodyfree_20260625"
P7_R54_OP07_LOCAL_OPERATION_RECEIPT_POLICY_REF: Final = "local_packet_generation_receipt_is_bodyfree_refs_only"
P7_R54_OP07_READY_REASON_REF: Final = "r54_local_packet_generation_receipt_recorded_bodyfree"

P7_R54_OP08_PACKET_SCAN_READY_STATUS_REF: Final = "PACKET_SCAN_READY"
P7_R54_OP08_PACKET_SCAN_BLOCKED_STATUS_REF: Final = "PACKET_SCAN_BLOCKED_BY_PACKET_GENERATION_LOCAL_OPERATION"
P7_R54_OP08_PACKET_SCAN_BLOCKED_BY_LEAK_STATUS_REF: Final = "BLOCKED_BY_BODY_LEAK_OR_QUESTION_TEXT"
P7_R54_OP08_ALLOWED_PACKET_SCAN_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_OP08_PACKET_SCAN_READY_STATUS_REF,
    P7_R54_OP08_PACKET_SCAN_BLOCKED_STATUS_REF,
    P7_R54_OP08_PACKET_SCAN_BLOCKED_BY_LEAK_STATUS_REF,
)
P7_R54_OP08_PACKET_SCAN_REF: Final = "r54_packet_completeness_export_denylist_scan_bodyfree_20260625"
P7_R54_OP08_READY_REASON_REF: Final = "r54_packet_completeness_and_export_denylist_scan_ready_bodyfree"
P7_R54_OP08_REQUIRED_PACKET_FIELD_REFS: Final[tuple[str, ...]] = (
    "current_input_review_surface_local_only",
    "returned_emlis_surface_local_only",
    "p5_history_line_or_boundary_surface_local_only",
    "plan_tier_context_local_only",
    "case_role_family_ref",
    "rating_axis_instruction_ref",
    "selection_form_ref",
)

P7_R54_OP09_FORM_READY_STATUS_REF: Final = "REVIEWER_INSTRUCTION_RATING_FORM_FROZEN_BODYFREE"
P7_R54_OP09_FORM_BLOCKED_STATUS_REF: Final = "REVIEWER_INSTRUCTION_RATING_FORM_BLOCKED_BY_PACKET_SCAN"
P7_R54_OP09_ALLOWED_FORM_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_OP09_FORM_READY_STATUS_REF,
    P7_R54_OP09_FORM_BLOCKED_STATUS_REF,
)
P7_R54_OP09_REVIEWER_INSTRUCTION_REF: Final = "r54_reviewer_instruction_selection_only_no_free_text_20260625"
P7_R54_OP09_RATING_FORM_REF: Final = "r54_p5_human_blind_qa_rating_form_bodyfree_20260625"
P7_R54_OP09_READY_REASON_REF: Final = "r54_reviewer_instruction_and_rating_form_frozen_bodyfree"
P7_R54_OP09_RATING_AXIS_REFS: Final[tuple[str, ...]] = (
    "history_connection_naturalness",
    "creepy_absence",
    "overclaim_absence",
    "self_blame_non_amplification",
    "wants_more_input_or_accumulation",
    "non_shallow_repeat",
)
P7_R54_OP09_RATING_AXIS_TARGET_THRESHOLDS: Final[dict[str, float]] = {
    "history_connection_naturalness": 0.90,
    "creepy_absence": 0.95,
    "overclaim_absence": 0.95,
    "self_blame_non_amplification": 0.95,
    "wants_more_input_or_accumulation": 0.85,
    "non_shallow_repeat": 0.90,
}
P7_R54_OP09_SCORE_OPTION_REFS: Final[tuple[float, ...]] = (0.0, 0.25, 0.5, 0.75, 1.0)
P7_R54_OP09_VERDICT_OPTION_REFS: Final[tuple[str, ...]] = ("PASS", "YELLOW", "REPAIR_REQUIRED", "RED")
P7_R54_OP09_BLOCKER_ID_OPTION_REFS: Final[tuple[str, ...]] = (
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
P7_R54_OP09_QUESTION_NEED_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = (
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
P7_R54_OP09_AMBIGUITY_KIND_OPTION_REFS: Final[tuple[str, ...]] = (
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
P7_R54_OP09_ONE_QUESTION_FIT_OPTION_REFS: Final[tuple[str, ...]] = (
    "not_needed",
    "fits_one_question",
    "needs_more_than_one_question_not_p7",
    "would_delay_immediate_observation",
    "unsafe_or_boundary_not_question",
    "repair_required_not_question",
    "insufficient_material",
)
P7_R54_OP09_REPAIR_REQUIRED_OPTION_REFS: Final[tuple[str, ...]] = (
    "emlis_readfeel_repair_required",
    "p5_surface_repair_required",
    "gate_boundary_repair_required",
    "no_repair_required",
)
P7_R54_OP09_PLAN_CANDIDATE_FLAG_REFS: Final[tuple[str, ...]] = (
    "plus_single_question_candidate_later",
    "premium_deep_dive_candidate_later",
    "p8_design_material_candidate",
    "p8_implementation_spec_finalized_here",
)

P7_R54_OP10_REVIEW_STATE_CAPTURE_READY_STATUS_REF: Final = "REVIEW_OPERATION_STATE_CAPTURED_BODYFREE"
P7_R54_OP10_REVIEW_STATE_CAPTURE_BLOCKED_STATUS_REF: Final = "REVIEW_OPERATION_STATE_CAPTURE_BLOCKED_BY_REVIEWER_FORM"
P7_R54_OP10_REVIEW_NOT_STARTED_STATUS_REF: Final = "NOT_STARTED"
P7_R54_OP10_REVIEW_IN_PROGRESS_STATUS_REF: Final = "REVIEW_IN_PROGRESS_LOCAL_ONLY"
P7_R54_OP10_REVIEW_PAUSED_STATUS_REF: Final = "REVIEW_PAUSED"
P7_R54_OP10_REVIEW_ABORTED_STATUS_REF: Final = "REVIEW_ABORTED"
P7_R54_OP10_REVIEW_EXPIRED_STATUS_REF: Final = "REVIEW_EXPIRED"
P7_R54_OP10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF: Final = "REVIEW_COMPLETED_SELECTIONS_CAPTURED"
P7_R54_OP10_ALLOWED_REVIEW_OPERATION_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_OP10_REVIEW_NOT_STARTED_STATUS_REF,
    P7_R54_OP10_REVIEW_IN_PROGRESS_STATUS_REF,
    P7_R54_OP10_REVIEW_PAUSED_STATUS_REF,
    P7_R54_OP10_REVIEW_ABORTED_STATUS_REF,
    P7_R54_OP10_REVIEW_EXPIRED_STATUS_REF,
    P7_R54_OP10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF,
)
P7_R54_OP10_REVIEWER_IDENTITY_POLICY_REF: Final = "reviewer_ref_is_pseudonymous_no_name_email_account"
P7_R54_OP10_COMPLETION_READY_REASON_REF: Final = "r54_actual_human_review_completion_state_captured_bodyfree"
P7_R54_OP10_STATE_CAPTURE_READY_REASON_REF: Final = "r54_actual_human_review_operation_state_captured_bodyfree"

P7_R54_OP11_SANITIZED_CAPTURE_READY_STATUS_REF: Final = "REVIEW_COMPLETED_SELECTIONS_CAPTURED_BODYFREE_ROWS_READY"
P7_R54_OP11_SANITIZED_CAPTURE_BLOCKED_STATUS_REF: Final = "SANITIZED_REVIEW_RESULT_CAPTURE_BLOCKED"
P7_R54_OP11_SANITIZED_REVIEW_RESULT_CAPTURE_REF: Final = "r54_sanitized_review_result_capture_bodyfree_20260625"
P7_R54_OP11_READY_REASON_REF: Final = "r54_sanitized_review_result_rows_captured_bodyfree"

P7_R54_OP12_RATING_NORMALIZATION_READY_STATUS_REF: Final = "RATING_ROWS_NORMALIZED"
P7_R54_OP12_RATING_NORMALIZATION_BLOCKED_STATUS_REF: Final = "RATING_ROW_NORMALIZATION_BLOCKED"
P7_R54_OP12_RATING_ROW_NORMALIZATION_REF: Final = "r54_rating_row_normalization_bodyfree_20260625"
P7_R54_OP12_RATING_ROW_SOURCE_REF: Final = "sanitized_external_local_reviewer_selection_only"
P7_R54_OP12_READY_REASON_REF: Final = "r54_rating_rows_normalized_bodyfree"
P7_R54_OP12_ALLOWED_RATING_NORMALIZATION_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_OP12_RATING_NORMALIZATION_READY_STATUS_REF,
    P7_R54_OP12_RATING_NORMALIZATION_BLOCKED_STATUS_REF,
)
P7_R54_OP12_RATING_SCORE_MIN: Final = 0.0
P7_R54_OP12_RATING_SCORE_MAX: Final = 1.0
P7_R54_OP12_VERDICT_BLOCKER_CONSISTENT_REF: Final = "verdict_blocker_consistency_passed"

P7_R54_OP13_BLOCKER_INGESTION_READY_STATUS_REF: Final = "READFEEL_EXECUTION_BLOCKERS_INGESTED_BODYFREE"
P7_R54_OP13_BLOCKER_INGESTION_BLOCKED_STATUS_REF: Final = "READFEEL_EXECUTION_BLOCKER_INGESTION_BLOCKED"
P7_R54_OP13_READY_REASON_REF: Final = "r54_readfeel_and_execution_blockers_separated_bodyfree"
P7_R54_OP13_ALLOWED_BLOCKER_INGESTION_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_OP13_BLOCKER_INGESTION_READY_STATUS_REF,
    P7_R54_OP13_BLOCKER_INGESTION_BLOCKED_STATUS_REF,
)
P7_R54_OP13_BLOCKER_STATUS_REFS: Final[tuple[str, ...]] = ("open", "closed")
P7_R54_OP13_READFEEL_BLOCKER_KIND_REF: Final = "p5_history_line_readfeel_blocker"
P7_R54_OP13_EXECUTION_BLOCKER_KIND_REF: Final = "review_execution_boundary_blocker"
P7_R54_OP13_EXECUTION_BLOCKER_ID_REFS: Final[tuple[str, ...]] = (
    "review_packet_generation_blocked_missing_local_root",
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
    "no_touch_violation_detected",
    "rating_row_normalization_not_ready_for_blocker_ingestion",
    "blocker_ingestion_not_ready_for_question_observation_normalization",
    "sanitized_review_capture_not_ready_for_question_observation_normalization",
    "rating_row_normalization_not_ready_for_question_observation_normalization",
    "question_observation_normalization_not_ready_for_consistency_guard",
    "rating_row_normalization_not_ready_for_consistency_guard",
    "rating_question_case_ref_set_mismatch",
)

P7_R54_OP14_QUESTION_OBSERVATION_NORMALIZATION_READY_STATUS_REF: Final = "QUESTION_OBSERVATION_ROWS_NORMALIZED"
P7_R54_OP14_QUESTION_OBSERVATION_NORMALIZATION_BLOCKED_STATUS_REF: Final = "QUESTION_OBSERVATION_NORMALIZATION_BLOCKED"
P7_R54_OP14_QUESTION_OBSERVATION_NORMALIZATION_REF: Final = "r54_question_need_observation_normalization_bodyfree_20260625"
P7_R54_OP14_READY_REASON_REF: Final = "r54_question_need_observation_rows_normalized_bodyfree"
P7_R54_OP14_ALLOWED_NORMALIZATION_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_OP14_QUESTION_OBSERVATION_NORMALIZATION_READY_STATUS_REF,
    P7_R54_OP14_QUESTION_OBSERVATION_NORMALIZATION_BLOCKED_STATUS_REF,
)
P7_R54_OP14_P8_MATERIAL_CANDIDATE_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = (
    "question_may_reduce_overread_risk",
    "plus_single_question_candidate_later",
    "premium_deep_dive_candidate_later",
)
P7_R54_OP14_NOT_QUESTION_REPAIR_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = (
    "not_question_emlis_readfeel_repair_required",
    "not_question_p5_surface_repair_required",
    "not_question_gate_boundary_required",
)

P7_R54_OP15_CONSISTENCY_GUARD_READY_STATUS_REF: Final = "RATING_QUESTION_CONSISTENCY_GUARD_READY"
P7_R54_OP15_CONSISTENCY_GUARD_BLOCKED_STATUS_REF: Final = "RATING_QUESTION_CONSISTENCY_GUARD_BLOCKED"
P7_R54_OP15_CONSISTENCY_GUARD_REF: Final = "r54_rating_question_consistency_guard_bodyfree_20260625"
P7_R54_OP15_READY_REASON_REF: Final = "r54_rating_question_consistency_guard_passed_bodyfree"
P7_R54_OP15_CONSISTENCY_ISSUE_ID_REFS: Final[tuple[str, ...]] = (
    "r54_op15_red_or_repair_with_no_question_needed_observation",
    "r54_op15_repair_required_with_p8_material_candidate",
    "r54_op15_pass_with_not_question_repair_required",
    "r54_op15_insufficient_material_with_pass_or_no_execution_blocker",
    "r54_op15_rating_question_case_ref_set_mismatch",
)
P7_R54_OP15_CONSISTENCY_ISSUE_KIND_REFS: Final[tuple[str, ...]] = (
    "rating_question_observation_semantic_mismatch",
    "p5_repair_hidden_by_question_candidate",
    "p5_inconclusive_or_execution_boundary_mismatch",
    "rating_question_case_integrity_issue",
)
P7_R54_OP15_DECISION_DIRECTION_REFS: Final[tuple[str, ...]] = (
    "continue_after_consistency_guard",
    "p5_repair_return_required_later",
    "r54_operation_inconclusive_required_later",
    "rating_question_row_repair_required",
)

P7_R54_OPERATION_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
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
    "api_db_rn_response_key_changed_here",
    "runtime_changed_here",
    "question_api_implemented",
    "question_db_schema_implemented",
    "question_rn_ui_implemented",
    "question_response_key_implemented",
    "question_trigger_logic_implemented",
    "question_storage_schema_implemented",
    "question_answer_persistence_implemented",
    "question_plan_guard_implemented",
    "question_implementation_started_here",
    "p8_question_implementation_spec_finalized_here",
    "body_full_packet_generated_here",
    "actual_body_full_packet_generated_here",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_run_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "p5_human_blind_qa_confirmed",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_human_blind_qa_confirmed_final",
    "p6_limited_human_readfeel_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "p8_question_design_material_candidate",
    "p8_start_allowed",
    "p7_complete",
    "release_allowed",
    "json_schema_file_created_here",
    "schema_files_materialized_here",
    "body_full_packet_export_allowed",
    "reviewer_notes_export_allowed",
    "body_full_packet_zip_inclusion_allowed",
    "local_absolute_path_materialized_here",
    "body_content_hash_materialized_here",
    "packet_content_hash_materialized_here",
    "command_result_body_stored_here",
    "terminal_output_stored_here",
    "source_delta_rows_materialized_here",
)

P7_R54_OPERATION_SCOPE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "allowed_operation_step_refs",
    "out_of_scope_refs",
    "no_touch_boundary_frozen",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "operation_current_refs_required_before_actual_review",
    "historical_helper_refs_must_be_separated",
    "body_full_generation_blocked_until_preflight",
    "human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r54_operation_no_touch_contract",
    "body_free_markers",
    "body_free",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    *P7_R54_OPERATION_FALSE_FLAG_REFS,
)
P7_R54_OPERATION_CURRENT_SNAPSHOT_REFREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "op00_schema_version",
    "op00_material_ref",
    "op00_next_required_step",
    "operation_current_refs",
    "operation_current_ref_count",
    "historical_helper_ref_groups",
    "historical_helper_refs",
    "historical_helper_ref_group_count",
    "historical_helper_refs_separated",
    "historical_helper_refs_can_be_used_for_helper_regression_only",
    "historical_helper_refs_can_be_used_for_actual_review_basis",
    "old_helper_refs_allowed_as_actual_review_basis",
    "historical_helper_refs_used_as_actual_review_basis",
    "operation_current_refs_used_as_actual_review_basis",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis",
    "source_delta_rows_required_next",
    "body_full_generation_blocked_until_preflight",
    "human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r54_operation_no_touch_contract",
    "body_free_markers",
    "body_free",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    *P7_R54_OPERATION_FALSE_FLAG_REFS,
)

P7_R54_SOURCE_DELTA_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "source_delta_row_ref",
    "helper_ref_group",
    "comparison_status_ref",
    "classification_ref",
    "helper_snapshot_refs",
    "operation_current_refs",
    "helper_ref_count",
    "operation_current_ref_count",
    "compared_ref_count",
    "same_ref_keys",
    "changed_ref_keys",
    "missing_in_helper_ref_keys",
    "missing_in_operation_ref_keys",
    "mismatched_ref_count",
    "historical_helper_refs_used_as_actual_review_basis",
    "operation_current_refs_used_as_actual_review_basis",
    "old_helper_refs_allowed_as_actual_review_basis",
    "body_free",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
)

P7_R54_OPERATION_HISTORICAL_HELPER_SOURCE_DELTA_RECONCILE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "op01_schema_version",
    "op01_material_ref",
    "op01_next_required_step",
    "operation_current_refs",
    "operation_current_ref_count",
    "historical_helper_ref_groups",
    "historical_helper_refs",
    "historical_helper_ref_group_count",
    "source_delta_row_refs",
    "source_delta_rows",
    "source_delta_row_count",
    "source_delta_rows_required_next",
    "source_delta_rows_materialized_here",
    "all_historical_helper_refs_reconciled",
    "historical_helper_refs_separated",
    "historical_helper_refs_can_be_used_for_helper_regression_only",
    "historical_helper_refs_can_be_used_for_actual_review_basis",
    "old_helper_refs_allowed_as_actual_review_basis",
    "historical_helper_refs_used_as_actual_review_basis",
    "operation_current_refs_used_as_actual_review_basis",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis",
    "body_full_generation_blocked_until_preflight",
    "human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r54_operation_no_touch_contract",
    "body_free_markers",
    "body_free",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    *tuple(key for key in P7_R54_OPERATION_FALSE_FLAG_REFS if key != "source_delta_rows_materialized_here"),
)

P7_R54_OPERATION_R55_HOLD_INTAKE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "op02_schema_version",
    "op02_material_ref",
    "op02_next_required_step",
    "operation_current_refs",
    "operation_current_ref_count",
    "source_delta_row_refs",
    "source_delta_row_count",
    "op02_source_delta_rows_materialized",
    "r55_decision_material_schema_version",
    "r55_decision_material_ref",
    "r55_decision_ref",
    "r55_decision_status",
    "r55_next_required_step",
    "r55_existing_r52_decision_equivalent",
    "r55_hold_intake_status_ref",
    "r55_actual_review_evidence_gap_status_ref",
    "r55_actual_review_evidence_complete",
    "required_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "disposal_verified",
    "missing_evidence_refs",
    "missing_evidence_ref_count",
    "r54_review_operation_state_ref",
    "p5_decision_status_ref",
    "p5_decision_candidate_ref",
    "p6_hold",
    "p8_hold",
    "release_hold",
    "r54_actual_local_only_human_review_operation_required_before_r52_reintake",
    "actual_review_evidence_complete",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis",
    "source_delta_rows_materialized_here",
    "body_full_generation_blocked_until_preflight",
    "human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r54_operation_no_touch_contract",
    "body_free_markers",
    "body_free",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    *P7_R54_OPERATION_FALSE_FLAG_REFS,
)

P7_R54_OPERATION_LOCAL_ONLY_PREFLIGHT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "op03_schema_version",
    "op03_material_ref",
    "op03_next_required_step",
    "operation_current_refs",
    "operation_current_ref_count",
    "r55_hold_intake_status_ref",
    "r55_actual_review_evidence_complete",
    "required_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "disposal_verified",
    "p6_hold",
    "p8_hold",
    "release_hold",
    "actual_review_evidence_complete",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis",
    "local_review_root_env_var",
    "local_review_root_presence_ref",
    "local_review_root_declared",
    "local_review_root_outside_repo_export_scope",
    "local_review_root_path_included",
    "explicit_allow_token_ref",
    "explicit_allow_present",
    "explicit_allow_token_body_stored_here",
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
    "human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r54_operation_no_touch_contract",
    "body_free_markers",
    "body_free",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    *P7_R54_OPERATION_FALSE_FLAG_REFS,
)

P7_R54_OPERATION_24_CASE_MANIFEST_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "op04_schema_version",
    "op04_material_ref",
    "op04_next_required_step",
    "op04_preflight_status",
    "op04_preflight_ready",
    "operation_current_refs",
    "operation_current_ref_count",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis",
    "required_case_count",
    "r48_case_matrix_schema_version",
    "r48_case_matrix_material_ref",
    "case_distribution",
    "case_distribution_total_count",
    "case_distribution_matches_design",
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
    "body_full_packet_generated_here",
    "body_full_generation_blocked_until_request_step",
    "p5_actual_review_still_not_run",
    "actual_review_evidence_complete",
    "rating_row_count",
    "question_observation_row_count",
    "disposal_verified",
    "human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r54_operation_no_touch_contract",
    "body_free_markers",
    "body_free",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    *P7_R54_OPERATION_FALSE_FLAG_REFS,
)


P7_R54_OPERATION_BODY_FULL_PACKET_GENERATION_REQUEST_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op05_schema_version", "op05_material_ref", "op05_next_required_step", "op05_manifest_status", "op05_manifest_ready",
    "operation_current_refs", "operation_current_ref_count", "actual_review_basis_ref", "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis", "required_case_count", "op05_case_count",
    "op05_controller_manifest_row_count", "op05_reviewer_facing_row_count", "packet_generation_request_status",
    "packet_generation_request_ref", "packet_generation_request_policy_ref", "packet_generation_request_reason_refs",
    "execution_blocker_ids", "open_execution_blocker_ids", "requested_case_count", "requested_packet_count",
    "requested_packet_ref_ids", "requested_packet_ref_count", "requested_packet_ref_ids_unique",
    "packet_generation_request_rows", "packet_generation_request_row_count", "request_is_bodyfree_only",
    "request_contains_packet_content", "request_contains_local_path", "request_contains_question_text",
    "local_only_output_scope_ref", "local_review_root_path_included", "local_packet_directory_path_included",
    "body_full_packet_content_included", "body_full_packet_generation_local_operation_started_here",
    "body_full_packet_generated_here", "body_full_packet_export_allowed", "body_full_packet_zip_inclusion_allowed",
    "reviewer_notes_export_allowed", "packet_generation_request_materialized_here", "p5_actual_review_still_not_run",
    "actual_review_evidence_complete", "rating_row_count", "question_observation_row_count", "disposal_verified",
    "human_review_completion_claim_blocked_here", "p6_p8_release_promotion_blocked_here", "implemented_steps",
    "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract",
    "r54_operation_no_touch_contract", "body_free_markers", "body_free", "question_text_included",
    "draft_question_text_included", "local_path_included", *P7_R54_OPERATION_FALSE_FLAG_REFS,
)

P7_R54_OPERATION_PACKET_GENERATION_LOCAL_OPERATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op06_schema_version", "op06_material_ref", "op06_next_required_step", "op06_packet_generation_request_status",
    "op06_packet_generation_request_ref", "op06_request_ready", "operation_current_refs", "operation_current_ref_count",
    "actual_review_basis_ref", "actual_review_basis_allowed", "operation_current_refs_are_actual_review_basis",
    "required_case_count", "expected_packet_ref_ids", "expected_packet_ref_count", "local_operation_status",
    "local_operation_receipt_ref", "local_operation_receipt_policy_ref", "local_operation_reason_refs",
    "execution_blocker_ids", "open_execution_blocker_ids", "declared_generated_packet_ref_ids",
    "declared_generated_packet_ref_count", "declared_generated_packet_ref_ids_unique", "packet_ref_ids_match_request",
    "packet_generation_local_operation_declared_complete", "packet_generation_local_operation_unverified_by_artifact",
    "local_operation_executed_outside_artifact_boundary", "local_operation_receipt_materialized_here",
    "local_operation_receipt_body_stored_here", "body_full_packet_content_included", "body_full_packet_generated_here",
    "actual_body_full_packet_generated_here", "local_reviewer_payload_materialized_here", "local_review_root_path_included",
    "local_packet_directory_path_included", "local_packet_exported", "local_packet_export_candidate_count",
    "body_full_packet_export_allowed", "body_full_packet_zip_inclusion_allowed", "reviewer_notes_export_allowed",
    "export_denylist_violation_refs", "export_denylist_violation_count", "packet_completeness_scan_required_next",
    "p5_actual_review_still_not_run", "actual_review_evidence_complete", "rating_row_count", "question_observation_row_count",
    "disposal_verified", "human_review_completion_claim_blocked_here", "p6_p8_release_promotion_blocked_here",
    "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract",
    "r54_operation_no_touch_contract", "body_free_markers", "body_free", "question_text_included", "draft_question_text_included",
    "local_path_included", *P7_R54_OPERATION_FALSE_FLAG_REFS,
)


P7_R54_OPERATION_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op07_schema_version", "op07_material_ref", "op07_next_required_step", "op07_local_operation_status",
    "op07_local_operation_ready", "operation_current_refs", "operation_current_ref_count", "actual_review_basis_ref",
    "actual_review_basis_allowed", "operation_current_refs_are_actual_review_basis", "required_case_count",
    "packet_scan_status", "packet_scan_ref", "packet_scan_reason_refs", "execution_blocker_ids", "open_execution_blocker_ids",
    "expected_packet_ref_ids", "expected_packet_ref_count", "declared_packet_ref_ids", "declared_packet_ref_count",
    "declared_packet_ref_ids_unique", "packet_ref_ids_match_local_operation", "packet_scan_rows", "packet_scan_row_count",
    "total_case_count", "packet_present_count", "required_fields_present_count", "required_packet_field_refs",
    "required_packet_field_ref_count", "packet_completeness_ready", "export_denylist_policy_ref", "export_denylist_patterns",
    "export_denylist_violation_refs", "export_denylist_violation_count", "body_full_packet_export_candidate_refs",
    "body_full_packet_export_candidate_count", "body_full_packet_content_detected_in_export", "question_text_detected_in_export",
    "local_path_detected_in_export", "packet_scan_is_bodyfree_only", "packet_scan_contains_packet_content",
    "packet_scan_contains_local_path", "packet_scan_contains_question_text", "reviewer_instruction_rating_form_freeze_allowed_next",
    "body_full_packet_content_included", "body_full_packet_generated_here", "actual_body_full_packet_generated_here",
    "local_review_root_path_included", "local_packet_directory_path_included", "local_packet_exported",
    "body_full_packet_export_allowed", "body_full_packet_zip_inclusion_allowed", "reviewer_notes_export_allowed",
    "p5_actual_review_still_not_run", "actual_review_evidence_complete", "rating_row_count", "question_observation_row_count",
    "disposal_verified", "human_review_completion_claim_blocked_here", "p6_p8_release_promotion_blocked_here",
    "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract",
    "r54_operation_no_touch_contract", "body_free_markers", "body_free", "question_text_included", "draft_question_text_included",
    "local_path_included", *P7_R54_OPERATION_FALSE_FLAG_REFS,
)

P7_R54_OPERATION_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op08_schema_version", "op08_material_ref", "op08_next_required_step", "op08_packet_scan_status",
    "op08_packet_scan_ready", "operation_current_refs", "operation_current_ref_count", "actual_review_basis_ref",
    "actual_review_basis_allowed", "operation_current_refs_are_actual_review_basis", "required_case_count",
    "packet_scan_row_count", "packet_present_count", "required_fields_present_count", "reviewer_instruction_status",
    "reviewer_instruction_ref", "reviewer_instruction_policy_ref", "rating_form_ref", "rating_form_reason_refs",
    "execution_blocker_ids", "open_execution_blocker_ids", "rating_axis_refs", "rating_axis_count",
    "rating_axis_target_thresholds", "score_option_refs", "verdict_option_refs", "blocker_id_option_refs",
    "question_need_primary_class_options", "ambiguity_kind_option_refs", "one_question_fit_option_refs",
    "repair_required_option_refs", "plan_candidate_flag_refs", "selection_only_form", "reviewer_free_text_field_present",
    "reviewer_free_text_export_allowed", "raw_body_copy_field_present", "question_text_field_present", "draft_question_text_field_present",
    "local_path_field_present", "body_hash_field_present", "packet_content_field_present", "rating_form_contains_question_text",
    "rating_form_contains_raw_body_copy", "rating_form_contains_local_path", "rating_form_contains_body_hash",
    "rating_form_contains_reviewer_free_text_export", "actual_human_review_operation_state_capture_allowed_next",
    "reviewer_instruction_materialized_here", "rating_form_materialized_here", "actual_human_review_started_here",
    "actual_human_review_run_here", "p5_actual_review_still_not_run", "actual_review_evidence_complete",
    "rating_row_count", "question_observation_row_count", "disposal_verified", "human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here", "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref",
    "next_required_step", "public_contract", "r54_operation_no_touch_contract", "body_free_markers", "body_free",
    "question_text_included", "draft_question_text_included", "local_path_included", *P7_R54_OPERATION_FALSE_FLAG_REFS,
)


P7_R54_OPERATION_ACTUAL_HUMAN_REVIEW_OPERATION_STATE_CAPTURE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op09_schema_version", "op09_material_ref", "op09_next_required_step", "op09_reviewer_instruction_status",
    "op09_form_ready", "operation_current_refs", "operation_current_ref_count", "actual_review_basis_ref",
    "actual_review_basis_allowed", "operation_current_refs_are_actual_review_basis", "required_case_count",
    "state_capture_status", "review_operation_status", "review_operation_state_reason_refs", "execution_blocker_ids",
    "open_execution_blocker_ids", "reviewer_assignment_ref", "reviewer_ref_ids", "reviewer_ref_count",
    "reviewer_identity_policy_ref", "reviewer_identity_personal_info_included", "reviewer_name_included",
    "reviewer_email_included", "reviewer_account_included", "review_started_state_declared", "review_paused_state_declared",
    "review_aborted_state_declared", "review_expired_state_declared", "review_completed_state_declared",
    "review_completion_receipt_ref", "review_completed_packet_ref_ids", "review_completed_packet_ref_count",
    "review_completed_packet_ref_ids_unique", "review_completed_selection_row_refs", "review_completed_selection_row_count",
    "review_completed_selection_row_refs_unique", "review_completed_selection_rows_expected_count",
    "review_completed_selections_captured_by_external_human_ref", "sanitized_review_result_capture_allowed_next",
    "state_capture_is_bodyfree_only", "state_capture_contains_reviewer_free_text", "state_capture_contains_packet_content",
    "state_capture_contains_local_path", "state_capture_contains_question_text", "state_capture_contains_body_hash",
    "actual_human_review_started_here", "actual_human_review_run_here", "actual_manual_review_run_here",
    "actual_review_evidence_complete", "rating_row_count", "question_observation_row_count", "disposal_verified",
    "human_review_completion_claim_blocked_here", "p6_p8_release_promotion_blocked_here", "implemented_steps",
    "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract",
    "r54_operation_no_touch_contract", "body_free_markers", "body_free", "question_text_included",
    "draft_question_text_included", "local_path_included", *P7_R54_OPERATION_FALSE_FLAG_REFS,
)

P7_R54_OPERATION_SANITIZED_REVIEW_RESULT_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "review_result_row_ref", "review_session_id", "packet_ref_id", "blind_case_id", "case_ref_id",
    "family", "case_role", "reviewer_ref", "reviewed_at_ref", "axis_scores", "axis_score_count",
    "verdict", "sanitized_reason_ids", "blocker_ids", "question_need_primary_class", "ambiguity_kind_refs",
    "one_question_fit_ref", "repair_required_refs", "plan_candidate_flags", "selection_only_row",
    "reviewer_free_text_included", "raw_body_included", "comment_text_included", "question_text_included",
    "draft_question_text_included", "local_path_included", "body_hash_included", "packet_content_included",
    "body_removed", "body_free",
)

P7_R54_OPERATION_SANITIZED_REVIEW_RESULT_CAPTURE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op10_schema_version", "op10_material_ref", "op10_next_required_step", "op10_review_operation_status",
    "op10_sanitized_capture_allowed_next", "op10_completed_packet_ref_count", "op10_completed_selection_row_count",
    "operation_current_refs", "operation_current_ref_count", "actual_review_basis_ref", "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis", "required_case_count", "sanitized_review_result_capture_status",
    "sanitized_review_result_capture_ref", "sanitized_review_result_reason_refs", "execution_blocker_ids",
    "open_execution_blocker_ids", "expected_packet_ref_ids", "expected_packet_ref_count", "expected_selection_row_refs",
    "expected_selection_row_ref_count", "sanitized_review_result_rows", "sanitized_review_result_row_count",
    "reviewed_case_count", "packet_ref_ids", "packet_ref_count", "packet_ref_ids_unique", "case_ref_ids",
    "case_ref_count", "case_ref_ids_unique", "blind_case_ids", "blind_case_id_count", "blind_case_ids_unique",
    "reviewer_ref_ids", "reviewer_ref_count", "family_case_counts", "case_role_counts", "selection_rows_are_bodyfree_only",
    "sanitized_rows_contain_reviewer_free_text", "sanitized_rows_contain_raw_body", "sanitized_rows_contain_comment_text",
    "sanitized_rows_contain_question_text", "sanitized_rows_contain_local_path", "sanitized_rows_contain_body_hash",
    "sanitized_rows_contain_packet_content", "rating_row_normalization_allowed_next", "sanitized_review_result_rows_materialized_here",
    "actual_rating_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_review_evidence_complete",
    "rating_row_count", "question_observation_row_count", "disposal_verified", "human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here", "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref",
    "next_required_step", "public_contract", "r54_operation_no_touch_contract", "body_free_markers", "body_free",
    "question_text_included", "draft_question_text_included", "local_path_included", *P7_R54_OPERATION_FALSE_FLAG_REFS,
)



P7_R54_OPERATION_RATING_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "rating_row_ref", "review_result_row_ref", "review_session_id", "packet_ref_id",
    "blind_case_id", "case_ref_id", "family", "case_role", "reviewer_ref", "reviewed_at_ref",
    "axis_scores", "axis_score_count", "axis_score_average", "axis_score_min", "axis_score_max",
    "target_thresholds", "below_target_axis_refs", "below_target_axis_count", "verdict",
    "sanitized_reason_ids", "readfeel_blocker_ids", "readfeel_blocker_count", "execution_blocker_ids",
    "execution_blocker_count", "question_need_primary_class", "repair_required_refs", "rating_source_ref",
    "verdict_blocker_consistency_ref", "pass_requires_no_blocker", "red_or_repair_requires_blocker_or_reason",
    "body_removed", "rating_row_is_bodyfree", "reviewer_free_text_included", "raw_body_included",
    "comment_text_included", "question_text_included", "draft_question_text_included", "local_path_included",
    "body_hash_included", "packet_content_included", "machine_auto_score_used",
    "machine_metrics_used_for_readfeel", "body_free",
)

P7_R54_OPERATION_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op11_schema_version", "op11_material_ref", "op11_next_required_step", "op11_sanitized_review_result_capture_status",
    "op11_rating_row_normalization_allowed_next", "operation_current_refs", "operation_current_ref_count",
    "actual_review_basis_ref", "actual_review_basis_allowed", "operation_current_refs_are_actual_review_basis",
    "required_case_count", "sanitized_review_result_row_count", "rating_row_normalization_status",
    "rating_row_normalization_ref", "rating_row_normalization_reason_refs", "execution_blocker_ids",
    "open_execution_blocker_ids", "rating_rows", "rating_row_count", "reviewed_case_count", "rating_row_refs",
    "rating_row_ref_count", "rating_row_refs_unique", "packet_ref_ids", "packet_ref_count", "packet_ref_ids_unique",
    "case_ref_ids", "case_ref_count", "case_ref_ids_unique", "blind_case_ids", "blind_case_id_count",
    "blind_case_ids_unique", "rating_row_schema_version", "rating_row_required_field_refs", "rating_axis_refs",
    "rating_axis_target_thresholds", "rating_score_min", "rating_score_max", "allowed_verdict_refs",
    "readfeel_blocker_id_refs", "execution_blocker_id_refs", "sanitized_reason_ids_only", "blocker_ids_only",
    "missing_axis_scores_pass_allowed", "extra_rating_axis_allowed", "machine_auto_score_allowed",
    "machine_metrics_used_for_readfeel_allowed", "reviewer_free_text_bodyfree_allowed",
    "blocked_or_not_reviewable_must_use_execution_blocker_row", "red_or_repair_requires_blocker_or_reason",
    "pass_requires_targets_and_no_blockers", "rating_rows_are_bodyfree", "all_required_rating_rows_present",
    "rating_case_ref_sets_match_review_capture", "verdict_counts", "axis_score_averages",
    "rating_consistency_issue_rows", "rating_consistency_issue_count", "pass_with_any_blocker_detected",
    "pass_below_axis_target_detected", "red_or_repair_without_blocker_or_reason_detected",
    "readfeel_blocker_row_candidate_count", "execution_blocker_row_candidate_count",
    "readfeel_blocker_execution_blocker_ingestion_allowed_next", "rating_rows_normalized_here",
    "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here", "actual_review_evidence_complete", "question_observation_row_count",
    "disposal_verified", "human_review_completion_claim_blocked_here", "p6_p8_release_promotion_blocked_here",
    "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract",
    "r54_operation_no_touch_contract", "body_free_markers", "body_free", "question_text_included",
    "draft_question_text_included", "local_path_included", *P7_R54_OPERATION_FALSE_FLAG_REFS,
)

P7_R54_OPERATION_READFEEL_BLOCKER_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "blocker_row_ref", "review_session_id", "rating_row_ref", "packet_ref_id",
    "blind_case_id", "case_ref_id", "family", "case_role", "reviewer_ref", "readfeel_blocker_id",
    "blocker_kind_ref", "blocker_status_ref", "source_verdict", "raw_body_included", "comment_text_included",
    "reviewer_free_text_included", "question_text_included", "draft_question_text_included", "local_path_included",
    "body_hash_included", "packet_content_included", "machine_auto_score_used", "machine_metrics_used_for_readfeel",
    "body_free",
)

P7_R54_OPERATION_EXECUTION_BLOCKER_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "execution_blocker_row_ref", "review_session_id", "source_ref", "packet_ref_id",
    "blind_case_id", "case_ref_id", "family", "case_role", "execution_blocker_id", "execution_blocker_kind_ref",
    "execution_blocker_status_ref", "execution_blocker_does_not_assign_readfeel_verdict", "raw_body_included",
    "comment_text_included", "reviewer_free_text_included", "question_text_included", "draft_question_text_included",
    "local_path_included", "body_hash_included", "packet_content_included", "machine_auto_score_used",
    "machine_metrics_used_for_readfeel", "body_free",
)

P7_R54_OPERATION_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op12_schema_version", "op12_material_ref", "op12_next_required_step", "op12_rating_row_normalization_status",
    "op12_blocker_ingestion_allowed_next", "operation_current_refs", "operation_current_ref_count",
    "actual_review_basis_ref", "actual_review_basis_allowed", "operation_current_refs_are_actual_review_basis",
    "required_case_count", "rating_row_count", "blocker_ingestion_status", "blocker_ingestion_reason_refs",
    "execution_blocker_ids", "open_execution_blocker_ids", "readfeel_blocker_row_schema_version",
    "execution_blocker_row_schema_version", "readfeel_blocker_row_required_field_refs", "execution_blocker_row_required_field_refs",
    "readfeel_blocker_id_refs", "execution_blocker_id_refs", "blocker_status_refs", "readfeel_blocker_rows",
    "execution_blocker_rows", "readfeel_blocker_row_count", "execution_blocker_row_count", "open_readfeel_blocker_count",
    "open_execution_blocker_count", "readfeel_blocker_counts", "execution_blocker_counts", "rating_packet_ref_ids",
    "rating_case_ref_ids", "rating_blind_case_ids", "readfeel_and_execution_blockers_separated",
    "execution_blockers_do_not_assign_readfeel_verdict", "execution_blocker_cases_do_not_create_rating_rows",
    "execution_blocker_open_blocks_p5_confirmed_candidate", "p5_confirmed_candidate_blocked_by_open_execution_blockers",
    "rating_missing_maps_to_execution_blocker_not_red", "local_root_missing_maps_to_execution_blocker_not_red",
    "disposal_failed_maps_to_execution_blocker_not_red", "body_free_leak_maps_to_execution_blocker_not_red",
    "readfeel_blocker_row_builder_ready", "execution_blocker_row_builder_ready", "rating_rows_preserved_from_op12",
    "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here", "actual_review_evidence_complete", "question_observation_row_count",
    "disposal_verified", "human_review_completion_claim_blocked_here", "p6_p8_release_promotion_blocked_here",
    "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract",
    "r54_operation_no_touch_contract", "body_free_markers", "body_free", "question_text_included",
    "draft_question_text_included", "local_path_included", *P7_R54_OPERATION_FALSE_FLAG_REFS,
)

P7_R54_OPERATION_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "question_observation_row_ref", "review_session_id", "review_result_row_ref",
    "rating_row_ref", "packet_ref_id", "blind_case_id", "case_ref_id", "family", "case_role",
    "reviewer_ref", "question_need_primary_class", "ambiguity_kind_refs", "one_question_fit_ref",
    "repair_required_refs", "plan_candidate_flags", "p8_material_candidate_allowed",
    "not_question_repair_required", "insufficient_material_execution_blocker", "question_observation_row_is_bodyfree",
    "question_text_included", "draft_question_text_included", "reviewer_free_text_included", "raw_body_included",
    "comment_text_included", "local_path_included", "body_hash_included", "packet_content_included",
    "machine_auto_score_used", "machine_metrics_used_for_readfeel", "body_free",
)

P7_R54_OPERATION_QUESTION_NEED_OBSERVATION_NORMALIZATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op13_schema_version", "op13_material_ref", "op13_next_required_step", "op13_blocker_ingestion_status",
    "op13_question_observation_normalization_allowed_next", "op12_schema_version", "op12_material_ref",
    "op12_rating_row_normalization_status", "op11_schema_version", "op11_material_ref",
    "op11_sanitized_review_result_capture_status", "operation_current_refs", "operation_current_ref_count",
    "actual_review_basis_ref", "actual_review_basis_allowed", "operation_current_refs_are_actual_review_basis",
    "required_case_count", "question_observation_normalization_status", "question_observation_normalization_ref",
    "question_observation_normalization_reason_refs", "execution_blocker_ids", "open_execution_blocker_ids",
    "sanitized_review_result_row_count", "rating_row_count", "question_observation_rows",
    "question_observation_row_count", "question_observation_row_refs", "question_observation_row_ref_count",
    "question_observation_row_refs_unique", "case_ref_ids", "case_ref_count", "case_ref_ids_unique",
    "packet_ref_ids", "packet_ref_count", "packet_ref_ids_unique", "blind_case_ids", "blind_case_id_count",
    "blind_case_ids_unique", "question_observation_row_schema_version", "question_observation_row_required_field_refs",
    "question_need_primary_class_refs", "ambiguity_kind_refs", "one_question_fit_refs", "repair_required_ref_refs",
    "plan_candidate_flag_refs", "question_need_observation_rows_are_bodyfree", "question_text_absent_for_all_rows",
    "draft_question_text_absent_for_all_rows", "reviewer_free_text_absent_for_all_rows", "raw_body_absent_for_all_rows",
    "comment_text_absent_for_all_rows", "local_path_absent_for_all_rows", "body_hash_absent_for_all_rows",
    "question_text_included_allowed", "draft_question_text_included_allowed", "reviewer_free_text_included_allowed",
    "raw_body_allowed", "comment_text_allowed", "local_path_allowed", "body_hash_allowed",
    "p8_question_implementation_spec_finalized_here", "question_trigger_logic_implemented",
    "question_trigger_logic_implemented_here", "api_db_rn_response_key_changed_here", "question_api_implemented",
    "question_db_schema_implemented", "question_rn_ui_implemented", "question_response_key_implemented",
    "question_storage_schema_implemented", "question_answer_persistence_implemented", "question_plan_guard_implemented",
    "row_case_ref_sets_match_review_capture", "row_case_ref_sets_match_rating_rows",
    "all_required_question_need_observation_rows_present", "primary_class_ambiguity_one_question_fit_are_canonical_refs",
    "not_question_repair_rows_misclassified_as_p8_material", "p5_weakness_not_hidden_by_question_candidates_here",
    "question_text_or_draft_text_saved_here", "question_need_primary_class_counts", "ambiguity_kind_counts",
    "one_question_fit_counts", "repair_required_counts", "plan_candidate_flag_counts",
    "p8_material_candidate_row_count", "not_question_repair_required_count", "insufficient_material_execution_blocker_count",
    "rating_rows_preserved_from_op12", "blocker_rows_preserved_from_op13", "rating_question_consistency_guard_allowed_next",
    "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here", "actual_review_evidence_complete",
    "disposal_verified", "human_review_completion_claim_blocked_here", "p6_p8_release_promotion_blocked_here",
    "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract",
    "r54_operation_no_touch_contract", "body_free_markers", "body_free", "question_text_included",
    "draft_question_text_included", "local_path_included", *P7_R54_OPERATION_FALSE_FLAG_REFS,
)

P7_R54_OPERATION_RATING_QUESTION_CONSISTENCY_ISSUE_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "consistency_issue_row_ref", "review_session_id", "rating_row_ref",
    "question_observation_row_ref", "packet_ref_id", "blind_case_id", "case_ref_id", "family", "case_role",
    "issue_id", "issue_kind_ref", "decision_direction_ref", "issue_status_ref", "source_verdict",
    "question_need_primary_class", "repair_required_refs", "p8_material_candidate_allowed",
    "not_question_repair_required", "insufficient_material_execution_blocker", "body_free",
    "question_text_included", "draft_question_text_included", "reviewer_free_text_included", "raw_body_included",
    "comment_text_included", "local_path_included", "body_hash_included", "packet_content_included",
)

P7_R54_OPERATION_RATING_QUESTION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op14_schema_version", "op14_material_ref", "op14_next_required_step", "op14_question_observation_normalization_status",
    "op14_consistency_guard_allowed_next", "op12_schema_version", "op12_material_ref", "op12_rating_row_normalization_status",
    "operation_current_refs", "operation_current_ref_count", "actual_review_basis_ref", "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis", "required_case_count", "rating_question_consistency_guard_status",
    "rating_question_consistency_guard_ref", "rating_question_consistency_guard_reason_refs", "execution_blocker_ids",
    "open_execution_blocker_ids", "rating_row_count", "question_observation_row_count",
    "rating_question_case_ref_sets_match", "all_required_rating_and_question_rows_present",
    "rating_question_consistency_issue_row_schema_version", "rating_question_consistency_issue_row_required_field_refs",
    "rating_question_consistency_issue_rows", "consistency_issue_count", "consistency_issue_id_refs",
    "consistency_issue_kind_refs", "decision_direction_refs", "red_or_repair_with_no_question_needed_count",
    "repair_required_with_p8_material_candidate_count", "pass_with_not_question_repair_required_count",
    "insufficient_material_with_pass_or_no_execution_blocker_count", "case_ref_set_mismatch_count",
    "consistency_issue_direction_counts", "p5_confirmed_candidate_blocked_by_consistency_issues",
    "p5_decision_candidate_not_materialized_here", "issues_route_to_p5_repair_return_or_inconclusive_later",
    "p8_material_candidates_do_not_hide_p5_repair_here", "ready_for_pause_abort_expiration_protocol",
    "rating_rows_preserved_from_op12", "question_observation_rows_preserved_from_op14",
    "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here", "actual_review_evidence_complete",
    "disposal_verified", "human_review_completion_claim_blocked_here", "p6_p8_release_promotion_blocked_here",
    "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract",
    "r54_operation_no_touch_contract", "body_free_markers", "body_free", "question_text_included",
    "draft_question_text_included", "local_path_included", *P7_R54_OPERATION_FALSE_FLAG_REFS,
)


def _false_flags() -> dict[str, bool]:
    return {key: False for key in P7_R54_OPERATION_FALSE_FLAG_REFS}


def _safe_review_session_id(value: Any) -> str:
    return clean_identifier(value, default=P7_R54_OPERATION_DEFAULT_REVIEW_SESSION_ID, max_length=160)


def _operation_current_refs(overrides: Mapping[str, Any] | None = None) -> dict[str, str]:
    refs = dict(P7_R54_OPERATION_CURRENT_REFS)
    for key, value in safe_mapping(overrides).items():
        if key in refs:
            refs[key] = clean_identifier(value, default=refs[key], max_length=320)
    return refs


def _historical_helper_refs() -> dict[str, dict[str, str]]:
    return {key: dict(value) for key, value in P7_R54_OPERATION_HISTORICAL_HELPER_REFS.items()}


def _operation_no_touch_contract() -> dict[str, bool]:
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


def _assert_common_operation_contract(
    data: Mapping[str, Any],
    *,
    schema_version: str,
    policy_section: str,
    operation_step_ref: str,
    source: str,
    false_flag_refs: Sequence[str] = P7_R54_OPERATION_FALSE_FLAG_REFS,
) -> None:
    if data.get("schema_version") != schema_version:
        raise ValueError(f"{source} schema version changed")
    if data.get("phase") != P7_PHASE:
        raise ValueError(f"{source} phase changed")
    if data.get("step") != P7_R54_OPERATION_REENTRY_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R54_OPERATION_REENTRY_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("policy_kind") != P7_R54_OPERATION_REENTRY_POLICY_KIND:
        raise ValueError(f"{source} policy kind changed")
    if data.get("policy_section") != policy_section:
        raise ValueError(f"{source} policy section changed")
    if data.get("operation_step_ref") != operation_step_ref:
        raise ValueError(f"{source} operation step ref changed")
    if data.get("source_mode") != P7_SOURCE_MODE:
        raise ValueError(f"{source} must remain local snapshot")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} must not require or perform Git checks")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must be body-free")
    if data.get("actual_review_basis_ref") != P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError(f"{source} actual review basis ref changed")
    if data.get("actual_review_basis_allowed") != P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError(f"{source} must allow only operation-current refs as actual review basis")
    if data.get("question_text_included") is not False or data.get("draft_question_text_included") is not False:
        raise ValueError(f"{source} must not include question text")
    if data.get("local_path_included") is not False:
        raise ValueError(f"{source} must not include local paths")
    assert_false_markers(data.get("public_contract") or {}, source=f"{source}.public_contract")
    assert_false_markers(data.get("r54_operation_no_touch_contract") or {}, source=f"{source}.r54_operation_no_touch_contract")
    assert_false_markers(data.get("body_free_markers") or {}, source=f"{source}.body_free_markers")
    for false_key in false_flag_refs:
        if data.get(false_key) is not False:
            raise ValueError(f"{source} must keep {false_key}=False")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)


def _assert_operation_current_refs(data: Mapping[str, Any], *, source: str) -> None:
    refs = safe_mapping(data.get("operation_current_refs"))
    if refs != P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError(f"{source} operation current refs changed")
    if data.get("operation_current_ref_count") != len(P7_R54_OPERATION_CURRENT_REFS):
        raise ValueError(f"{source} operation current ref count changed")


def _assert_historical_helper_refs(data: Mapping[str, Any], *, source: str) -> None:
    groups = tuple(data.get("historical_helper_ref_groups") or ())
    refs = safe_mapping(data.get("historical_helper_refs"))
    if groups != P7_R54_OPERATION_HISTORICAL_HELPER_REF_GROUP_REFS:
        raise ValueError(f"{source} historical helper ref groups changed")
    if refs != P7_R54_OPERATION_HISTORICAL_HELPER_REFS:
        raise ValueError(f"{source} historical helper refs changed")
    if data.get("historical_helper_ref_group_count") != len(P7_R54_OPERATION_HISTORICAL_HELPER_REF_GROUP_REFS):
        raise ValueError(f"{source} historical helper ref group count changed")
    if data.get("historical_helper_refs_separated") is not True:
        raise ValueError(f"{source} must separate historical helper refs")
    if data.get("historical_helper_refs_can_be_used_for_helper_regression_only") is not True:
        raise ValueError(f"{source} must preserve helper refs only for regression context")
    if data.get("historical_helper_refs_can_be_used_for_actual_review_basis") is not False:
        raise ValueError(f"{source} must not allow helper refs as actual review basis")
    if data.get("old_helper_refs_allowed_as_actual_review_basis") is not False:
        raise ValueError(f"{source} must not allow old helper refs as actual review basis")
    if data.get("historical_helper_refs_used_as_actual_review_basis") is not False:
        raise ValueError(f"{source} must not use historical helper refs as actual review basis")
    if data.get("operation_current_refs_used_as_actual_review_basis") is not True:
        raise ValueError(f"{source} must use operation current refs as actual review basis")


def build_p7_r54_op00_scope_no_touch_boundary_freeze(
    *,
    review_session_id: Any = P7_R54_OPERATION_DEFAULT_REVIEW_SESSION_ID,
    material_id: Any = "p7_r54_operation_scope_no_touch_boundary_freeze",
) -> dict[str, Any]:
    """Build R54-OP-00 body-free scope / no-touch boundary freeze."""

    material = {
        "schema_version": P7_R54_OPERATION_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_OPERATION_REENTRY_STEP,
        "scope": P7_R54_OPERATION_REENTRY_SCOPE,
        "policy_kind": P7_R54_OPERATION_REENTRY_POLICY_KIND,
        "policy_section": P7_R54_OP00_STEP_REF,
        "operation_step_ref": P7_R54_OP00_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_operation_scope_no_touch_boundary_freeze", max_length=220),
        "review_session_id": _safe_review_session_id(review_session_id),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "allowed_operation_step_refs": [P7_R54_OP00_STEP_REF, P7_R54_OP01_STEP_REF],
        "out_of_scope_refs": [
            "p8_question_design",
            "api_route_change",
            "db_schema_or_migration_change",
            "rn_ui_or_visible_contract_change",
            "emlis_runtime_surface_change",
            "user_label_connection_runtime_change",
            "body_full_packet_generation",
            "actual_human_review_completion_claim",
            "p6_p8_or_release_promotion",
        ],
        "no_touch_boundary_frozen": True,
        "actual_review_basis_ref": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_required_before_actual_review": True,
        "historical_helper_refs_must_be_separated": True,
        "body_full_generation_blocked_until_preflight": True,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_OP00_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_OP00_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R54_OP_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R54_OP01_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_operation_no_touch_contract": _operation_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
    }
    assert_p7_r54_op00_scope_no_touch_boundary_freeze_contract(material)
    return material


def assert_p7_r54_op00_scope_no_touch_boundary_freeze_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(
        data,
        required=P7_R54_OPERATION_SCOPE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS,
        source="p7_r54_op00_scope_no_touch_boundary_freeze",
    )
    _assert_common_operation_contract(
        data,
        schema_version=P7_R54_OPERATION_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION,
        policy_section=P7_R54_OP00_STEP_REF,
        operation_step_ref=P7_R54_OP00_STEP_REF,
        source="p7_r54_op00_scope_no_touch_boundary_freeze",
    )
    if data.get("allowed_operation_step_refs") != [P7_R54_OP00_STEP_REF, P7_R54_OP01_STEP_REF]:
        raise ValueError("R54 OP00 allowed operation steps changed")
    if data.get("no_touch_boundary_frozen") is not True:
        raise ValueError("R54 OP00 must freeze the no-touch boundary")
    if data.get("operation_current_refs_required_before_actual_review") is not True:
        raise ValueError("R54 OP00 must require operation-current refs before actual review")
    if data.get("historical_helper_refs_must_be_separated") is not True:
        raise ValueError("R54 OP00 must require historical helper refs separation")
    if data.get("body_full_generation_blocked_until_preflight") is not True:
        raise ValueError("R54 OP00 must block body-full generation until preflight")
    if data.get("human_review_completion_claim_blocked_here") is not True:
        raise ValueError("R54 OP00 must block human-review completion claims")
    if data.get("p6_p8_release_promotion_blocked_here") is not True:
        raise ValueError("R54 OP00 must block P6/P8/release promotion")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_OP00_IMPLEMENTED_STEPS:
        raise ValueError("R54 OP00 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_OP00_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R54 OP00 not-yet steps changed")
    if data.get("next_required_step") != P7_R54_OP01_STEP_REF:
        raise ValueError("R54 OP00 must point to R54-OP-01")
    return True


def build_p7_r54_op01_operation_current_snapshot_refs_refreeze(
    *,
    scope_no_touch_boundary_freeze: Mapping[str, Any] | None = None,
    operation_current_refs: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_operation_current_snapshot_refreeze",
) -> dict[str, Any]:
    """Build R54-OP-01 body-free operation-current snapshot refs refreeze."""

    op00 = (
        safe_mapping(scope_no_touch_boundary_freeze)
        if scope_no_touch_boundary_freeze is not None
        else build_p7_r54_op00_scope_no_touch_boundary_freeze()
    )
    assert_p7_r54_op00_scope_no_touch_boundary_freeze_contract(op00)
    current_refs = _operation_current_refs(operation_current_refs)
    historical_refs = _historical_helper_refs()
    material = {
        "schema_version": P7_R54_OPERATION_CURRENT_SNAPSHOT_REFREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_OPERATION_REENTRY_STEP,
        "scope": P7_R54_OPERATION_REENTRY_SCOPE,
        "policy_kind": P7_R54_OPERATION_REENTRY_POLICY_KIND,
        "policy_section": P7_R54_OP01_STEP_REF,
        "operation_step_ref": P7_R54_OP01_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_operation_current_snapshot_refreeze", max_length=220),
        "review_session_id": _safe_review_session_id(op00.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op00_schema_version": P7_R54_OPERATION_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION,
        "op00_material_ref": clean_identifier(op00.get("material_id"), default="p7_r54_operation_scope_no_touch_boundary_freeze", max_length=220),
        "op00_next_required_step": clean_identifier(op00.get("next_required_step"), default=P7_R54_OP01_STEP_REF, max_length=180),
        "operation_current_refs": current_refs,
        "operation_current_ref_count": len(current_refs),
        "historical_helper_ref_groups": list(P7_R54_OPERATION_HISTORICAL_HELPER_REF_GROUP_REFS),
        "historical_helper_refs": historical_refs,
        "historical_helper_ref_group_count": len(P7_R54_OPERATION_HISTORICAL_HELPER_REF_GROUP_REFS),
        "historical_helper_refs_separated": True,
        "historical_helper_refs_can_be_used_for_helper_regression_only": True,
        "historical_helper_refs_can_be_used_for_actual_review_basis": False,
        "old_helper_refs_allowed_as_actual_review_basis": False,
        "historical_helper_refs_used_as_actual_review_basis": False,
        "operation_current_refs_used_as_actual_review_basis": True,
        "actual_review_basis_ref": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "source_delta_rows_required_next": True,
        "body_full_generation_blocked_until_preflight": True,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_OP01_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_OP01_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R54_OP_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R54_OP02_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_operation_no_touch_contract": _operation_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
    }
    assert_p7_r54_op01_operation_current_snapshot_refs_refreeze_contract(material)
    return material


def assert_p7_r54_op01_operation_current_snapshot_refs_refreeze_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(
        data,
        required=P7_R54_OPERATION_CURRENT_SNAPSHOT_REFREEZE_REQUIRED_FIELD_REFS,
        source="p7_r54_op01_operation_current_snapshot_refs_refreeze",
    )
    _assert_common_operation_contract(
        data,
        schema_version=P7_R54_OPERATION_CURRENT_SNAPSHOT_REFREEZE_SCHEMA_VERSION,
        policy_section=P7_R54_OP01_STEP_REF,
        operation_step_ref=P7_R54_OP01_STEP_REF,
        source="p7_r54_op01_operation_current_snapshot_refs_refreeze",
    )
    if data.get("op00_schema_version") != P7_R54_OPERATION_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION:
        raise ValueError("R54 OP01 OP00 schema reference changed")
    if data.get("op00_next_required_step") != P7_R54_OP01_STEP_REF:
        raise ValueError("R54 OP01 must be built after OP00")
    _assert_operation_current_refs(data, source="p7_r54_op01_operation_current_snapshot_refs_refreeze")
    _assert_historical_helper_refs(data, source="p7_r54_op01_operation_current_snapshot_refs_refreeze")
    if data.get("operation_current_refs_are_actual_review_basis") is not True:
        raise ValueError("R54 OP01 must mark operation-current refs as actual review basis")
    if data.get("source_delta_rows_required_next") is not True:
        raise ValueError("R54 OP01 must require OP02 source delta rows next")
    if data.get("body_full_generation_blocked_until_preflight") is not True:
        raise ValueError("R54 OP01 must block body-full generation until preflight")
    if data.get("human_review_completion_claim_blocked_here") is not True:
        raise ValueError("R54 OP01 must block human-review completion claims")
    if data.get("p6_p8_release_promotion_blocked_here") is not True:
        raise ValueError("R54 OP01 must block P6/P8/release promotion")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_OP01_IMPLEMENTED_STEPS:
        raise ValueError("R54 OP01 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_OP01_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R54 OP01 not-yet steps changed")
    if data.get("next_required_step") != P7_R54_OP02_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R54 OP01 must point to R54-OP-02")
    return True


def _source_delta_allowed_true_false_flag_refs() -> tuple[str, ...]:
    return tuple(
        key for key in P7_R54_OPERATION_FALSE_FLAG_REFS if key != "source_delta_rows_materialized_here"
    )


def _operation_ref_key_order() -> tuple[str, ...]:
    return tuple(P7_R54_OPERATION_CURRENT_REFS.keys())


def _build_source_delta_row(
    *,
    source_delta_row_ref: str,
    helper_ref_group: str,
    helper_snapshot_refs: Mapping[str, Any],
    operation_current_refs: Mapping[str, Any],
) -> dict[str, Any]:
    helper_refs = {key: clean_identifier(value, default="", max_length=320) for key, value in safe_mapping(helper_snapshot_refs).items()}
    current_refs = {key: clean_identifier(value, default="", max_length=320) for key, value in safe_mapping(operation_current_refs).items()}
    ordered_keys = _operation_ref_key_order()
    same_keys = [key for key in ordered_keys if helper_refs.get(key) == current_refs.get(key)]
    changed_keys = [key for key in ordered_keys if helper_refs.get(key) != current_refs.get(key)]
    missing_in_helper = [key for key in ordered_keys if key not in helper_refs]
    missing_in_operation = [key for key in helper_refs if key not in current_refs]
    row = {
        "schema_version": P7_R54_OPERATION_SOURCE_DELTA_ROW_SCHEMA_VERSION,
        "source_delta_row_ref": source_delta_row_ref,
        "helper_ref_group": helper_ref_group,
        "comparison_status_ref": P7_R54_SOURCE_DELTA_COMPARISON_STATUS_REF,
        "classification_ref": P7_R54_SOURCE_DELTA_CLASSIFICATION_REF,
        "helper_snapshot_refs": helper_refs,
        "operation_current_refs": current_refs,
        "helper_ref_count": len(helper_refs),
        "operation_current_ref_count": len(current_refs),
        "compared_ref_count": len(ordered_keys),
        "same_ref_keys": same_keys,
        "changed_ref_keys": changed_keys,
        "missing_in_helper_ref_keys": missing_in_helper,
        "missing_in_operation_ref_keys": missing_in_operation,
        "mismatched_ref_count": len(changed_keys) + len(missing_in_helper) + len(missing_in_operation),
        "historical_helper_refs_used_as_actual_review_basis": False,
        "operation_current_refs_used_as_actual_review_basis": True,
        "old_helper_refs_allowed_as_actual_review_basis": False,
        "body_free": True,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
    }
    assert_p7_r54_source_delta_row_bodyfree_contract(row)
    return row


def assert_p7_r54_source_delta_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(
        data,
        required=P7_R54_SOURCE_DELTA_ROW_REQUIRED_FIELD_REFS,
        source="p7_r54_source_delta_row",
    )
    row_ref = clean_identifier(data.get("source_delta_row_ref"), max_length=180)
    group = clean_identifier(data.get("helper_ref_group"), max_length=180)
    if data.get("schema_version") != P7_R54_OPERATION_SOURCE_DELTA_ROW_SCHEMA_VERSION:
        raise ValueError("R54 OP02 source delta row schema version changed")
    if row_ref not in P7_R54_SOURCE_DELTA_ROW_REFS:
        raise ValueError("R54 OP02 source delta row ref is not registered")
    if group not in P7_R54_OPERATION_HISTORICAL_HELPER_REF_GROUP_REFS:
        raise ValueError("R54 OP02 source delta helper group is not registered")
    if data.get("comparison_status_ref") != P7_R54_SOURCE_DELTA_COMPARISON_STATUS_REF:
        raise ValueError("R54 OP02 source delta comparison status changed")
    if data.get("classification_ref") != P7_R54_SOURCE_DELTA_CLASSIFICATION_REF:
        raise ValueError("R54 OP02 source delta classification changed")
    helper_refs = safe_mapping(data.get("helper_snapshot_refs"))
    operation_refs = safe_mapping(data.get("operation_current_refs"))
    if helper_refs != P7_R54_OPERATION_HISTORICAL_HELPER_REFS.get(group):
        raise ValueError("R54 OP02 source delta helper refs changed")
    if operation_refs != P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("R54 OP02 source delta operation refs changed")
    if data.get("helper_ref_count") != len(helper_refs):
        raise ValueError("R54 OP02 source delta helper ref count changed")
    if data.get("operation_current_ref_count") != len(P7_R54_OPERATION_CURRENT_REFS):
        raise ValueError("R54 OP02 source delta operation ref count changed")
    if data.get("compared_ref_count") != len(_operation_ref_key_order()):
        raise ValueError("R54 OP02 source delta compared ref count changed")
    changed = tuple(data.get("changed_ref_keys") or ())
    same = tuple(data.get("same_ref_keys") or ())
    missing_helper = tuple(data.get("missing_in_helper_ref_keys") or ())
    missing_operation = tuple(data.get("missing_in_operation_ref_keys") or ())
    if set(changed).intersection(same):
        raise ValueError("R54 OP02 source delta cannot mark a ref as both same and changed")
    if "backend_zip_ref" not in changed:
        raise ValueError("R54 OP02 source delta must make backend snapshot delta visible")
    if data.get("mismatched_ref_count") != len(changed) + len(missing_helper) + len(missing_operation):
        raise ValueError("R54 OP02 source delta mismatch count changed")
    if data.get("historical_helper_refs_used_as_actual_review_basis") is not False:
        raise ValueError("R54 OP02 source delta must not use historical helper refs as actual review basis")
    if data.get("operation_current_refs_used_as_actual_review_basis") is not True:
        raise ValueError("R54 OP02 source delta must use operation current refs as actual review basis")
    if data.get("old_helper_refs_allowed_as_actual_review_basis") is not False:
        raise ValueError("R54 OP02 source delta must not allow old helper refs as actual review basis")
    if data.get("body_free") is not True:
        raise ValueError("R54 OP02 source delta row must be body-free")
    if data.get("question_text_included") is not False or data.get("draft_question_text_included") is not False:
        raise ValueError("R54 OP02 source delta row must not include question text")
    if data.get("local_path_included") is not False:
        raise ValueError("R54 OP02 source delta row must not include local path")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_source_delta_row")
    return True


def _assert_source_delta_rows(rows: Any, *, source: str) -> None:
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)):
        raise ValueError(f"{source} source delta rows must be a sequence")
    if len(rows) != len(P7_R54_SOURCE_DELTA_ROW_REFS):
        raise ValueError(f"{source} source delta row count changed")
    seen: set[str] = set()
    for row in rows:
        assert_p7_r54_source_delta_row_bodyfree_contract(safe_mapping(row))
        row_ref = clean_identifier(safe_mapping(row).get("source_delta_row_ref"), max_length=180)
        if row_ref in seen:
            raise ValueError(f"{source} duplicate source delta row ref")
        seen.add(row_ref)
    if tuple(row_ref for row_ref in P7_R54_SOURCE_DELTA_ROW_REFS if row_ref in seen) != P7_R54_SOURCE_DELTA_ROW_REFS:
        raise ValueError(f"{source} source delta row refs changed")


def build_p7_r54_op02_historical_helper_source_delta_reconcile(
    *,
    operation_current_snapshot_refreeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_operation_historical_helper_source_delta_reconcile",
) -> dict[str, Any]:
    """Build R54-OP-02 body-free source-delta rows for R54/R55 helper refs."""

    op01 = (
        safe_mapping(operation_current_snapshot_refreeze)
        if operation_current_snapshot_refreeze is not None
        else build_p7_r54_op01_operation_current_snapshot_refs_refreeze()
    )
    assert_p7_r54_op01_operation_current_snapshot_refs_refreeze_contract(op01)
    current_refs = safe_mapping(op01.get("operation_current_refs"))
    historical_refs = safe_mapping(op01.get("historical_helper_refs"))
    source_delta_rows = [
        _build_source_delta_row(
            source_delta_row_ref="r54_helper_refs_vs_operation_current_refs",
            helper_ref_group="r54_helper_current_received_snapshot_refs",
            helper_snapshot_refs=safe_mapping(historical_refs.get("r54_helper_current_received_snapshot_refs")),
            operation_current_refs=current_refs,
        ),
        _build_source_delta_row(
            source_delta_row_ref="r55_helper_refs_vs_operation_current_refs",
            helper_ref_group="r55_helper_current_received_snapshot_refs",
            helper_snapshot_refs=safe_mapping(historical_refs.get("r55_helper_current_received_snapshot_refs")),
            operation_current_refs=current_refs,
        ),
    ]
    material = {
        "schema_version": P7_R54_OPERATION_HISTORICAL_HELPER_SOURCE_DELTA_RECONCILE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_OPERATION_REENTRY_STEP,
        "scope": P7_R54_OPERATION_REENTRY_SCOPE,
        "policy_kind": P7_R54_OPERATION_REENTRY_POLICY_KIND,
        "policy_section": P7_R54_OP02_STEP_REF,
        "operation_step_ref": P7_R54_OP02_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_operation_historical_helper_source_delta_reconcile", max_length=220),
        "review_session_id": _safe_review_session_id(op01.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op01_schema_version": P7_R54_OPERATION_CURRENT_SNAPSHOT_REFREEZE_SCHEMA_VERSION,
        "op01_material_ref": clean_identifier(op01.get("material_id"), default="p7_r54_operation_current_snapshot_refreeze", max_length=220),
        "op01_next_required_step": clean_identifier(op01.get("next_required_step"), default=P7_R54_OP02_STEP_REF, max_length=180),
        "operation_current_refs": dict(P7_R54_OPERATION_CURRENT_REFS),
        "operation_current_ref_count": len(P7_R54_OPERATION_CURRENT_REFS),
        "historical_helper_ref_groups": list(P7_R54_OPERATION_HISTORICAL_HELPER_REF_GROUP_REFS),
        "historical_helper_refs": _historical_helper_refs(),
        "historical_helper_ref_group_count": len(P7_R54_OPERATION_HISTORICAL_HELPER_REF_GROUP_REFS),
        "source_delta_row_refs": list(P7_R54_SOURCE_DELTA_ROW_REFS),
        "source_delta_rows": source_delta_rows,
        "source_delta_row_count": len(source_delta_rows),
        "source_delta_rows_required_next": False,
        "source_delta_rows_materialized_here": True,
        "all_historical_helper_refs_reconciled": True,
        "historical_helper_refs_separated": True,
        "historical_helper_refs_can_be_used_for_helper_regression_only": True,
        "historical_helper_refs_can_be_used_for_actual_review_basis": False,
        "old_helper_refs_allowed_as_actual_review_basis": False,
        "historical_helper_refs_used_as_actual_review_basis": False,
        "operation_current_refs_used_as_actual_review_basis": True,
        "actual_review_basis_ref": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "body_full_generation_blocked_until_preflight": True,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_OP02_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_OP02_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": "r54_op03_r55_hold_intake_before_preflight",
        "next_required_step": P7_R54_OP03_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_operation_no_touch_contract": _operation_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **{key: False for key in _source_delta_allowed_true_false_flag_refs()},
    }
    assert_p7_r54_op02_historical_helper_source_delta_reconcile_contract(material)
    return material


def assert_p7_r54_op02_historical_helper_source_delta_reconcile_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(
        data,
        required=P7_R54_OPERATION_HISTORICAL_HELPER_SOURCE_DELTA_RECONCILE_REQUIRED_FIELD_REFS,
        source="p7_r54_op02_historical_helper_source_delta_reconcile",
    )
    _assert_common_operation_contract(
        data,
        schema_version=P7_R54_OPERATION_HISTORICAL_HELPER_SOURCE_DELTA_RECONCILE_SCHEMA_VERSION,
        policy_section=P7_R54_OP02_STEP_REF,
        operation_step_ref=P7_R54_OP02_STEP_REF,
        source="p7_r54_op02_historical_helper_source_delta_reconcile",
        false_flag_refs=_source_delta_allowed_true_false_flag_refs(),
    )
    if data.get("op01_schema_version") != P7_R54_OPERATION_CURRENT_SNAPSHOT_REFREEZE_SCHEMA_VERSION:
        raise ValueError("R54 OP02 OP01 schema reference changed")
    if data.get("op01_next_required_step") != P7_R54_OP02_STEP_REF:
        raise ValueError("R54 OP02 must be built after OP01")
    _assert_operation_current_refs(data, source="p7_r54_op02_historical_helper_source_delta_reconcile")
    _assert_historical_helper_refs(data, source="p7_r54_op02_historical_helper_source_delta_reconcile")
    _assert_source_delta_rows(data.get("source_delta_rows"), source="p7_r54_op02_historical_helper_source_delta_reconcile")
    if tuple(data.get("source_delta_row_refs") or ()) != P7_R54_SOURCE_DELTA_ROW_REFS:
        raise ValueError("R54 OP02 source delta row refs changed")
    if data.get("source_delta_row_count") != len(P7_R54_SOURCE_DELTA_ROW_REFS):
        raise ValueError("R54 OP02 source delta row count changed")
    if data.get("source_delta_rows_required_next") is not False:
        raise ValueError("R54 OP02 must clear source-delta-required-next after materializing rows")
    if data.get("source_delta_rows_materialized_here") is not True:
        raise ValueError("R54 OP02 must materialize source delta rows here")
    if data.get("all_historical_helper_refs_reconciled") is not True:
        raise ValueError("R54 OP02 must reconcile all historical helper refs")
    if data.get("operation_current_refs_are_actual_review_basis") is not True:
        raise ValueError("R54 OP02 must keep operation-current refs as actual review basis")
    if data.get("body_full_generation_blocked_until_preflight") is not True:
        raise ValueError("R54 OP02 must keep body-full generation blocked until preflight")
    if data.get("human_review_completion_claim_blocked_here") is not True:
        raise ValueError("R54 OP02 must block human-review completion claims")
    if data.get("p6_p8_release_promotion_blocked_here") is not True:
        raise ValueError("R54 OP02 must block P6/P8/release promotion")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_OP02_IMPLEMENTED_STEPS:
        raise ValueError("R54 OP02 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_OP02_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R54 OP02 not-yet steps changed")
    if data.get("next_required_step") != P7_R54_OP03_STEP_REF:
        raise ValueError("R54 OP02 must point to R54-OP-03")
    return True


def build_p7_r54_op03_r55_hold_intake(
    *,
    historical_helper_source_delta_reconcile: Mapping[str, Any] | None = None,
    r55_r52_reintake_decision_material: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_operation_r55_hold_intake",
) -> dict[str, Any]:
    """Build R54-OP-03 body-free intake of the R55 hold decision."""

    op02 = (
        safe_mapping(historical_helper_source_delta_reconcile)
        if historical_helper_source_delta_reconcile is not None
        else build_p7_r54_op02_historical_helper_source_delta_reconcile()
    )
    assert_p7_r54_op02_historical_helper_source_delta_reconcile_contract(op02)
    r55_decision = (
        safe_mapping(r55_r52_reintake_decision_material)
        if r55_r52_reintake_decision_material is not None
        else build_p7_r55_r52_reintake_decision_materialization_bodyfree()
    )
    assert_p7_r55_r52_reintake_decision_materialization_bodyfree_contract(r55_decision)
    material = {
        "schema_version": P7_R54_OPERATION_R55_HOLD_INTAKE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_OPERATION_REENTRY_STEP,
        "scope": P7_R54_OPERATION_REENTRY_SCOPE,
        "policy_kind": P7_R54_OPERATION_REENTRY_POLICY_KIND,
        "policy_section": P7_R54_OP03_STEP_REF,
        "operation_step_ref": P7_R54_OP03_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_operation_r55_hold_intake", max_length=220),
        "review_session_id": _safe_review_session_id(op02.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op02_schema_version": P7_R54_OPERATION_HISTORICAL_HELPER_SOURCE_DELTA_RECONCILE_SCHEMA_VERSION,
        "op02_material_ref": clean_identifier(op02.get("material_id"), default="p7_r54_operation_historical_helper_source_delta_reconcile", max_length=220),
        "op02_next_required_step": clean_identifier(op02.get("next_required_step"), default=P7_R54_OP03_STEP_REF, max_length=180),
        "operation_current_refs": dict(P7_R54_OPERATION_CURRENT_REFS),
        "operation_current_ref_count": len(P7_R54_OPERATION_CURRENT_REFS),
        "source_delta_row_refs": list(P7_R54_SOURCE_DELTA_ROW_REFS),
        "source_delta_row_count": len(P7_R54_SOURCE_DELTA_ROW_REFS),
        "op02_source_delta_rows_materialized": True,
        "r55_decision_material_schema_version": P7_R55_R52_REINTAKE_DECISION_MATERIALIZATION_SCHEMA_VERSION,
        "r55_decision_material_ref": clean_identifier(r55_decision.get("material_id"), default="p7_r55_r52_reintake_decision_materialization_current_default", max_length=220),
        "r55_decision_ref": clean_identifier(r55_decision.get("r55_decision_ref"), default=P7_R55_DEFAULT_R52_REINTAKE_DECISION_REF, max_length=180),
        "r55_decision_status": clean_identifier(r55_decision.get("decision_status"), default=P7_R55_DEFAULT_DECISION_STATUS_REF, max_length=80),
        "r55_next_required_step": clean_identifier(r55_decision.get("next_required_step"), default=P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF, max_length=220),
        "r55_existing_r52_decision_equivalent": clean_identifier(r55_decision.get("r52_existing_decision_equivalent"), default=P7_R55_DEFAULT_R52_EXISTING_DECISION_EQUIVALENT_REF, max_length=180),
        "r55_hold_intake_status_ref": P7_R54_R55_HOLD_INTAKE_STATUS_REF,
        "r55_actual_review_evidence_gap_status_ref": clean_identifier(r55_decision.get("actual_review_evidence_gap_status_ref"), default=P7_R55_ACTUAL_REVIEW_EVIDENCE_MISSING_GAP_STATUS_REF, max_length=180),
        "r55_actual_review_evidence_complete": False,
        "required_case_count": P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "rating_row_count": 0,
        "question_observation_row_count": 0,
        "disposal_verified": False,
        "missing_evidence_refs": list(P7_R55_DEFAULT_MISSING_EVIDENCE_REFS),
        "missing_evidence_ref_count": len(P7_R55_DEFAULT_MISSING_EVIDENCE_REFS),
        "r54_review_operation_state_ref": P7_R55_R54_DEFAULT_REVIEW_OPERATION_STATE_REF,
        "p5_decision_status_ref": P7_R55_P5_DECISION_STATUS_NOT_REVIEWED_REF,
        "p5_decision_candidate_ref": P7_R55_R54_DEFAULT_P5_DECISION_CANDIDATE_REF,
        "p6_hold": True,
        "p8_hold": True,
        "release_hold": True,
        "r54_actual_local_only_human_review_operation_required_before_r52_reintake": True,
        "actual_review_evidence_complete": False,
        "actual_review_basis_ref": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "source_delta_rows_materialized_here": False,
        "body_full_generation_blocked_until_preflight": True,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_OP03_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_OP03_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R54_OP_NEXT_WORK_AFTER_OP03_REF,
        "next_required_step": P7_R54_OP04_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_operation_no_touch_contract": _operation_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
    }
    assert_p7_r54_op03_r55_hold_intake_contract(material)
    return material


def assert_p7_r54_op03_r55_hold_intake_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(
        data,
        required=P7_R54_OPERATION_R55_HOLD_INTAKE_REQUIRED_FIELD_REFS,
        source="p7_r54_op03_r55_hold_intake",
    )
    _assert_common_operation_contract(
        data,
        schema_version=P7_R54_OPERATION_R55_HOLD_INTAKE_SCHEMA_VERSION,
        policy_section=P7_R54_OP03_STEP_REF,
        operation_step_ref=P7_R54_OP03_STEP_REF,
        source="p7_r54_op03_r55_hold_intake",
    )
    if data.get("op02_schema_version") != P7_R54_OPERATION_HISTORICAL_HELPER_SOURCE_DELTA_RECONCILE_SCHEMA_VERSION:
        raise ValueError("R54 OP03 OP02 schema reference changed")
    if data.get("op02_next_required_step") != P7_R54_OP03_STEP_REF:
        raise ValueError("R54 OP03 must be built after OP02")
    _assert_operation_current_refs(data, source="p7_r54_op03_r55_hold_intake")
    if tuple(data.get("source_delta_row_refs") or ()) != P7_R54_SOURCE_DELTA_ROW_REFS:
        raise ValueError("R54 OP03 source delta row refs changed")
    if data.get("source_delta_row_count") != len(P7_R54_SOURCE_DELTA_ROW_REFS):
        raise ValueError("R54 OP03 source delta row count changed")
    if data.get("op02_source_delta_rows_materialized") is not True:
        raise ValueError("R54 OP03 requires OP02 source-delta rows before R55 hold intake")
    if data.get("r55_decision_material_schema_version") != P7_R55_R52_REINTAKE_DECISION_MATERIALIZATION_SCHEMA_VERSION:
        raise ValueError("R54 OP03 R55 decision material schema version changed")
    if data.get("r55_decision_ref") != P7_R55_DEFAULT_R52_REINTAKE_DECISION_REF:
        raise ValueError("R54 OP03 must intake the R55 return-to-R54-actual-review decision")
    if data.get("r55_decision_status") != P7_R55_DEFAULT_DECISION_STATUS_REF:
        raise ValueError("R54 OP03 R55 decision status changed")
    if data.get("r55_next_required_step") != P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R54 OP03 R55 next required step changed")
    if data.get("r55_existing_r52_decision_equivalent") != P7_R55_DEFAULT_R52_EXISTING_DECISION_EQUIVALENT_REF:
        raise ValueError("R54 OP03 R55 existing R52 equivalent changed")
    if data.get("r55_hold_intake_status_ref") != P7_R54_R55_HOLD_INTAKE_STATUS_REF:
        raise ValueError("R54 OP03 hold intake status changed")
    if data.get("r55_actual_review_evidence_gap_status_ref") != P7_R55_ACTUAL_REVIEW_EVIDENCE_MISSING_GAP_STATUS_REF:
        raise ValueError("R54 OP03 must keep the R55 actual-review-evidence-missing gap")
    if data.get("r55_actual_review_evidence_complete") is not False:
        raise ValueError("R54 OP03 must not mark R55 actual review evidence complete")
    if data.get("required_case_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("R54 OP03 required case count changed")
    if data.get("rating_row_count") != 0 or data.get("question_observation_row_count") != 0:
        raise ValueError("R54 OP03 must keep R55 rating/question rows at zero")
    if data.get("disposal_verified") is not False:
        raise ValueError("R54 OP03 must keep disposal unverified")
    if tuple(data.get("missing_evidence_refs") or ()) != P7_R55_DEFAULT_MISSING_EVIDENCE_REFS:
        raise ValueError("R54 OP03 missing evidence refs changed")
    if data.get("missing_evidence_ref_count") != len(P7_R55_DEFAULT_MISSING_EVIDENCE_REFS):
        raise ValueError("R54 OP03 missing evidence ref count changed")
    if data.get("r54_review_operation_state_ref") != P7_R55_R54_DEFAULT_REVIEW_OPERATION_STATE_REF:
        raise ValueError("R54 OP03 R54 review operation state changed")
    if data.get("p5_decision_status_ref") != P7_R55_P5_DECISION_STATUS_NOT_REVIEWED_REF:
        raise ValueError("R54 OP03 P5 decision status changed")
    if data.get("p5_decision_candidate_ref") != P7_R55_R54_DEFAULT_P5_DECISION_CANDIDATE_REF:
        raise ValueError("R54 OP03 P5 decision candidate changed")
    if data.get("p6_hold") is not True or data.get("p8_hold") is not True or data.get("release_hold") is not True:
        raise ValueError("R54 OP03 must keep P6/P8/release holds true")
    if data.get("r54_actual_local_only_human_review_operation_required_before_r52_reintake") is not True:
        raise ValueError("R54 OP03 must require R54 actual local-only review before R52 re-intake")
    if data.get("actual_review_evidence_complete") is not False:
        raise ValueError("R54 OP03 must not mark actual review evidence complete")
    if data.get("operation_current_refs_are_actual_review_basis") is not True:
        raise ValueError("R54 OP03 must keep operation-current refs as actual review basis")
    if data.get("source_delta_rows_materialized_here") is not False:
        raise ValueError("R54 OP03 must not rematerialize source delta rows")
    if data.get("body_full_generation_blocked_until_preflight") is not True:
        raise ValueError("R54 OP03 must keep body-full generation blocked until preflight")
    if data.get("human_review_completion_claim_blocked_here") is not True:
        raise ValueError("R54 OP03 must block human-review completion claims")
    if data.get("p6_p8_release_promotion_blocked_here") is not True:
        raise ValueError("R54 OP03 must block P6/P8/release promotion")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_OP03_IMPLEMENTED_STEPS:
        raise ValueError("R54 OP03 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_OP03_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R54 OP03 not-yet steps changed")
    if data.get("next_required_step") != P7_R54_OP04_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R54 OP03 must point to R54-OP-04")
    return True



def _matches_ref(value: Any, expected: str, *, missing_default: str) -> bool:
    return clean_identifier(value, default=missing_default, max_length=220) == expected


def _op04_preflight_status_and_reasons(
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
        reason_refs.append("explicit_allow_token_ref_missing_or_mismatched")
        blocker_ids.append("review_packet_generation_blocked_missing_explicit_allow")
    if not purge_plan_ready:
        reason_refs.append("purge_plan_not_ready")
        blocker_ids.append("review_packet_generation_blocked_missing_purge_plan")
    if not retention_policy_present:
        reason_refs.append("retention_policy_missing")
        blocker_ids.append("review_packet_generation_blocked_missing_retention_policy")
    if not export_denylist_present:
        reason_refs.append("export_denylist_policy_missing")
        blocker_ids.append("review_packet_generation_blocked_missing_export_denylist")
    if export_denylist_violation_refs:
        reason_refs.append("export_denylist_violation_detected")
        blocker_ids.append("review_packet_generation_blocked_export_denylist_violation")
    if blocker_ids:
        return (
            P7_R54_OP04_PREFLIGHT_BLOCKED_STATUS_REF,
            dedupe_identifiers(reason_refs, limit=40, max_length=160),
            dedupe_identifiers(blocker_ids, limit=40, max_length=160),
        )
    return P7_R54_OP04_PREFLIGHT_READY_STATUS_REF, [P7_R54_OP04_PREFLIGHT_READY_REASON_REF], []


def _op05_count_by(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = clean_identifier(row.get(key), max_length=180)
        if value:
            counts[value] = counts.get(value, 0) + 1
    return counts


def _op05_unique_non_empty(values: Sequence[str]) -> bool:
    return bool(values) and all(values) and len(set(values)) == len(values)


def _op05_case_refs(rows: Sequence[Mapping[str, Any]], key: str) -> list[str]:
    return [clean_identifier(row.get(key), max_length=180) for row in rows]


def _op05_controller_manifest_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    controller_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        source = safe_mapping(row)
        controller_rows.append(
            {
                "controller_row_ref": f"r54op05-controller-row-{index:03d}",
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


def _op05_reviewer_facing_case_index_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
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


def _assert_op05_case_row(row: Mapping[str, Any]) -> None:
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
    _assert_required_fields(data, required=required, source="p7_r54_op05_case_row")
    if data.get("controller_only") is not True:
        raise ValueError("R54 OP05 case row must remain controller-only")
    for false_key in (
        "reviewer_facing_family_exposed",
        "reviewer_facing_tier_exposed",
        "body_full_packet_materialized_here",
        "local_reviewer_payload_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 OP05 case row must keep {false_key}=False")
    if data.get("body_free") is not True:
        raise ValueError("R54 OP05 case row must be body-free")
    if clean_identifier(data.get("family"), max_length=180) not in P7_R54_OP05_CASE_DISTRIBUTION:
        raise ValueError("R54 OP05 case row family changed")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_op05_case_row")


def _assert_op05_controller_manifest_row(row: Mapping[str, Any]) -> None:
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
    _assert_required_fields(data, required=required, source="p7_r54_op05_controller_manifest_row")
    if data.get("controller_only") is not True:
        raise ValueError("R54 OP05 controller row must remain controller-only")
    for false_key in (
        "reviewer_facing_family_exposed",
        "reviewer_facing_tier_exposed",
        "reviewer_facing_case_ref_exposed",
        "reviewer_facing_packet_ref_exposed",
        "reviewer_facing_expected_result_exposed",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 OP05 controller row must keep {false_key}=False")
    if data.get("body_free") is not True:
        raise ValueError("R54 OP05 controller row must be body-free")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_op05_controller_manifest_row")


def _assert_op05_reviewer_facing_case_index_row(row: Mapping[str, Any]) -> None:
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
    _assert_required_fields(data, required=required, source="p7_r54_op05_reviewer_facing_case_index_row")
    if data.get("reviewer_receives_blind_case_id_only") is not True:
        raise ValueError("R54 OP05 reviewer row must expose only blind_case_id")
    for false_key in (
        "family_exposed",
        "tier_exposed",
        "case_ref_exposed",
        "packet_ref_exposed",
        "expected_result_exposed",
        "hidden_metadata_exposed",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 OP05 reviewer row must keep {false_key}=False")
    if data.get("body_free") is not True:
        raise ValueError("R54 OP05 reviewer row must be body-free")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_op05_reviewer_facing_case_index_row")


def build_p7_r54_op04_local_only_preflight(
    *,
    r55_hold_intake: Mapping[str, Any] | None = None,
    local_review_root_presence_ref: Any = None,
    explicit_allow_token_ref: Any = None,
    purge_plan_ref: Any = None,
    retention_policy_ref: Any = None,
    export_denylist_policy_ref: Any = None,
    export_denylist_violation_refs: Sequence[Any] | Any | None = None,
    material_id: Any = "p7_r54_operation_local_only_preflight",
) -> dict[str, Any]:
    """Build R54-OP-04 body-free local-only preflight without generating packets."""

    op03 = safe_mapping(r55_hold_intake) if r55_hold_intake is not None else build_p7_r54_op03_r55_hold_intake()
    assert_p7_r54_op03_r55_hold_intake_contract(op03)
    root_presence_ref = clean_identifier(
        local_review_root_presence_ref,
        default=P7_R54_OP04_LOCAL_REVIEW_ROOT_MISSING_REF,
        max_length=220,
    )
    explicit_ref = clean_identifier(
        explicit_allow_token_ref,
        default="missing_explicit_allow_token_ref",
        max_length=220,
    )
    purge_ref = clean_identifier(purge_plan_ref, default="missing_purge_plan_ref", max_length=220)
    retention_ref = clean_identifier(retention_policy_ref, default="missing_retention_policy_ref", max_length=220)
    export_policy_ref = clean_identifier(export_denylist_policy_ref, default="missing_export_denylist_policy_ref", max_length=220)
    deny_refs = dedupe_identifiers(export_denylist_violation_refs, limit=40, max_length=180)

    local_root_declared = root_presence_ref == P7_R54_OP04_LOCAL_REVIEW_ROOT_READY_REF
    explicit_allow_present = explicit_ref == P7_R54_OP04_EXPLICIT_ALLOW_TOKEN_REF
    purge_ready = purge_ref == P7_R54_OP04_PURGE_PLAN_READY_REF
    retention_present = retention_ref == P7_R54_OP04_RETENTION_POLICY_READY_REF
    export_denylist_present = export_policy_ref == P7_R54_OP04_EXPORT_DENYLIST_POLICY_READY_REF
    preflight_status, reason_refs, blocker_ids = _op04_preflight_status_and_reasons(
        local_review_root_declared=local_root_declared,
        explicit_allow_present=explicit_allow_present,
        purge_plan_ready=purge_ready,
        retention_policy_present=retention_present,
        export_denylist_present=export_denylist_present,
        export_denylist_violation_refs=deny_refs,
    )
    ready = preflight_status == P7_R54_OP04_PREFLIGHT_READY_STATUS_REF
    material = {
        "schema_version": P7_R54_OPERATION_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_OPERATION_REENTRY_STEP,
        "scope": P7_R54_OPERATION_REENTRY_SCOPE,
        "policy_kind": P7_R54_OPERATION_REENTRY_POLICY_KIND,
        "policy_section": P7_R54_OP04_STEP_REF,
        "operation_step_ref": P7_R54_OP04_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_operation_local_only_preflight", max_length=220),
        "review_session_id": _safe_review_session_id(op03.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op03_schema_version": P7_R54_OPERATION_R55_HOLD_INTAKE_SCHEMA_VERSION,
        "op03_material_ref": clean_identifier(op03.get("material_id"), default="p7_r54_operation_r55_hold_intake", max_length=220),
        "op03_next_required_step": clean_identifier(op03.get("next_required_step"), default=P7_R54_OP04_STEP_REF, max_length=180),
        "operation_current_refs": dict(P7_R54_OPERATION_CURRENT_REFS),
        "operation_current_ref_count": len(P7_R54_OPERATION_CURRENT_REFS),
        "r55_hold_intake_status_ref": clean_identifier(op03.get("r55_hold_intake_status_ref"), default=P7_R54_R55_HOLD_INTAKE_STATUS_REF, max_length=180),
        "r55_actual_review_evidence_complete": False,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "rating_row_count": 0,
        "question_observation_row_count": 0,
        "disposal_verified": False,
        "p6_hold": True,
        "p8_hold": True,
        "release_hold": True,
        "actual_review_evidence_complete": False,
        "actual_review_basis_ref": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "local_review_root_env_var": P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR,
        "local_review_root_presence_ref": root_presence_ref,
        "local_review_root_declared": local_root_declared,
        "local_review_root_outside_repo_export_scope": local_root_declared,
        "local_review_root_path_included": False,
        "explicit_allow_token_ref": explicit_ref,
        "explicit_allow_present": explicit_allow_present,
        "explicit_allow_token_body_stored_here": False,
        "purge_plan_ref": purge_ref,
        "purge_plan_present": purge_ref != "missing_purge_plan_ref",
        "purge_plan_ready": purge_ready,
        "purge_plan_required_before_body_full_generation": True,
        "purge_plan_required_delete_target_refs": list(P7_R54_OP04_REQUIRED_DELETE_TARGET_REFS),
        "retention_policy_ref": retention_ref,
        "retention_policy_present": retention_present,
        "body_full_packet_retention_max_hours": P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
        "reviewer_notes_retention_after_rating_finalized_max_hours": P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
        "delete_trigger_refs": list(P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS),
        "export_denylist_policy_ref": export_policy_ref,
        "export_denylist_present": export_denylist_present,
        "export_denylist_patterns": list(P7_R47_EXPORT_DENYLIST_PATTERNS),
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
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_OP04_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_OP04_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R54_OP_NEXT_WORK_AFTER_OP04_REF,
        "next_required_step": P7_R54_OP05_STEP_REF if ready else P7_R54_OP04_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_operation_no_touch_contract": _operation_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
    }
    assert_p7_r54_op04_local_only_preflight_contract(material)
    return material


def assert_p7_r54_op04_local_only_preflight_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(
        data,
        required=P7_R54_OPERATION_LOCAL_ONLY_PREFLIGHT_REQUIRED_FIELD_REFS,
        source="p7_r54_op04_local_only_preflight",
    )
    _assert_common_operation_contract(
        data,
        schema_version=P7_R54_OPERATION_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION,
        policy_section=P7_R54_OP04_STEP_REF,
        operation_step_ref=P7_R54_OP04_STEP_REF,
        source="p7_r54_op04_local_only_preflight",
    )
    if data.get("op03_schema_version") != P7_R54_OPERATION_R55_HOLD_INTAKE_SCHEMA_VERSION:
        raise ValueError("R54 OP04 OP03 schema reference changed")
    if data.get("op03_next_required_step") != P7_R54_OP04_STEP_REF:
        raise ValueError("R54 OP04 must be built after OP03")
    _assert_operation_current_refs(data, source="p7_r54_op04_local_only_preflight")
    if data.get("r55_hold_intake_status_ref") != P7_R54_R55_HOLD_INTAKE_STATUS_REF:
        raise ValueError("R54 OP04 must preserve the R55 hold intake status")
    if data.get("r55_actual_review_evidence_complete") is not False:
        raise ValueError("R54 OP04 must not mark R55 actual review evidence complete")
    if data.get("required_case_count") != P7_R51_REQUIRED_CASE_COUNT:
        raise ValueError("R54 OP04 required case count changed")
    if data.get("rating_row_count") != 0 or data.get("question_observation_row_count") != 0:
        raise ValueError("R54 OP04 must not materialize rating/question rows")
    if data.get("disposal_verified") is not False:
        raise ValueError("R54 OP04 must not verify disposal")
    if data.get("p6_hold") is not True or data.get("p8_hold") is not True or data.get("release_hold") is not True:
        raise ValueError("R54 OP04 must keep P6/P8/release holds true")
    if data.get("actual_review_evidence_complete") is not False:
        raise ValueError("R54 OP04 must not mark actual review evidence complete")
    if data.get("operation_current_refs_are_actual_review_basis") is not True:
        raise ValueError("R54 OP04 must keep operation-current refs as actual review basis")
    if data.get("local_review_root_env_var") != P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR:
        raise ValueError("R54 OP04 local review root env var changed")
    if data.get("local_review_root_path_included") is not False:
        raise ValueError("R54 OP04 must not include a local review root path")
    if data.get("explicit_allow_token_body_stored_here") is not False:
        raise ValueError("R54 OP04 must not store explicit allow token body")
    if data.get("purge_plan_required_before_body_full_generation") is not True:
        raise ValueError("R54 OP04 must require a purge plan before body-full generation")
    if tuple(data.get("purge_plan_required_delete_target_refs") or ()) != P7_R54_OP04_REQUIRED_DELETE_TARGET_REFS:
        raise ValueError("R54 OP04 purge target refs changed")
    if data.get("body_full_packet_retention_max_hours") != P7_R47_BODY_FULL_PACKET_RETENTION_HOURS:
        raise ValueError("R54 OP04 body-full retention changed")
    if data.get("reviewer_notes_retention_after_rating_finalized_max_hours") != P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS:
        raise ValueError("R54 OP04 reviewer-notes retention changed")
    if tuple(data.get("delete_trigger_refs") or ()) != P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS:
        raise ValueError("R54 OP04 delete triggers changed")
    if tuple(data.get("export_denylist_patterns") or ()) != P7_R47_EXPORT_DENYLIST_PATTERNS:
        raise ValueError("R54 OP04 export denylist patterns changed")
    if data.get("preflight_status") not in P7_R54_OP04_ALLOWED_PREFLIGHT_STATUS_REFS:
        raise ValueError("R54 OP04 preflight status changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=160)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 OP04 open blockers must match execution blockers")
    ready = data.get("preflight_status") == P7_R54_OP04_PREFLIGHT_READY_STATUS_REF
    if data.get("body_full_packet_generation_allowed_before_preflight") is not False:
        raise ValueError("R54 OP04 must never allow body-full generation before preflight")
    if data.get("body_full_generation_blocked_until_manifest_freeze") is not True:
        raise ValueError("R54 OP04 must keep body-full generation blocked until manifest freeze")
    if data.get("human_review_completion_claim_blocked_here") is not True:
        raise ValueError("R54 OP04 must block human-review completion claims")
    if data.get("p6_p8_release_promotion_blocked_here") is not True:
        raise ValueError("R54 OP04 must block P6/P8/release promotion")
    if ready:
        for key in (
            "local_review_root_declared",
            "local_review_root_outside_repo_export_scope",
            "explicit_allow_present",
            "purge_plan_present",
            "purge_plan_ready",
            "retention_policy_present",
            "export_denylist_present",
            "body_full_packet_generation_allowed_by_preflight",
            "body_full_packet_generation_request_allowed_next",
        ):
            if data.get(key) is not True:
                raise ValueError(f"R54 OP04 ready preflight must keep {key}=True")
        if data.get("local_review_root_presence_ref") != P7_R54_OP04_LOCAL_REVIEW_ROOT_READY_REF:
            raise ValueError("R54 OP04 ready preflight root ref changed")
        if data.get("explicit_allow_token_ref") != P7_R54_OP04_EXPLICIT_ALLOW_TOKEN_REF:
            raise ValueError("R54 OP04 ready preflight explicit allow token ref changed")
        if data.get("purge_plan_ref") != P7_R54_OP04_PURGE_PLAN_READY_REF:
            raise ValueError("R54 OP04 ready preflight purge plan ref changed")
        if data.get("retention_policy_ref") != P7_R54_OP04_RETENTION_POLICY_READY_REF:
            raise ValueError("R54 OP04 ready preflight retention policy ref changed")
        if data.get("export_denylist_policy_ref") != P7_R54_OP04_EXPORT_DENYLIST_POLICY_READY_REF:
            raise ValueError("R54 OP04 ready preflight export denylist policy ref changed")
        if data.get("export_denylist_violation_refs") != [] or data.get("export_denylist_violation_count") != 0:
            raise ValueError("R54 OP04 ready preflight must have no export denylist violations")
        if blockers:
            raise ValueError("R54 OP04 ready preflight must not carry execution blockers")
        if data.get("preflight_reason_refs") != [P7_R54_OP04_PREFLIGHT_READY_REASON_REF]:
            raise ValueError("R54 OP04 ready preflight reason refs changed")
        if data.get("next_required_step") != P7_R54_OP05_STEP_REF:
            raise ValueError("R54 OP04 ready preflight must point to R54-OP-05")
    else:
        if data.get("body_full_packet_generation_allowed_by_preflight") is not False:
            raise ValueError("R54 OP04 blocked preflight must not allow body-full generation")
        if data.get("body_full_packet_generation_request_allowed_next") is not False:
            raise ValueError("R54 OP04 blocked preflight must not allow packet generation request next")
        if not blockers:
            raise ValueError("R54 OP04 blocked preflight must carry execution blockers")
        if not data.get("preflight_reason_refs"):
            raise ValueError("R54 OP04 blocked preflight must carry reason refs")
        if data.get("next_required_step") != P7_R54_OP04_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 OP04 blocked preflight must point to local-only preflight repair")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_OP04_IMPLEMENTED_STEPS:
        raise ValueError("R54 OP04 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_OP04_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R54 OP04 not-yet steps changed")
    return True


def build_p7_r54_op05_24_case_manifest_freeze(
    *,
    local_only_preflight: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_operation_24_case_manifest_freeze",
) -> dict[str, Any]:
    """Build R54-OP-05 body-free 24-case manifest freeze without packet generation."""

    op04 = safe_mapping(local_only_preflight) if local_only_preflight is not None else build_p7_r54_op04_local_only_preflight()
    assert_p7_r54_op04_local_only_preflight_contract(op04)
    preflight_ready = op04.get("preflight_status") == P7_R54_OP04_PREFLIGHT_READY_STATUS_REF
    rows: list[dict[str, Any]] = []
    r48_material_ref = "not_materialized_until_preflight_ready"
    if preflight_ready:
        case_matrix = build_p7_r48_p5_first_formal_review_case_matrix(
            material_id="p7_r54_op05_r48_first_formal_case_matrix_basis"
        )
        assert_p7_r48_p5_first_formal_review_case_matrix_contract(case_matrix)
        r48_material_ref = clean_identifier(case_matrix.get("material_id"), default="p7_r54_op05_r48_first_formal_case_matrix_basis", max_length=220)
        rows = [dict(safe_mapping(row)) for row in (case_matrix.get("case_rows") or [])]
    family_counts = _op05_count_by(rows, "family")
    role_counts = _op05_count_by(rows, "case_role")
    tier_counts = _op05_count_by(rows, "subscription_tier_ref")
    blind_ids = _op05_case_refs(rows, "blind_case_id")
    case_refs = _op05_case_refs(rows, "case_ref_id")
    packet_refs = _op05_case_refs(rows, "packet_ref_id")
    distribution_matches = bool(preflight_ready and family_counts == P7_R54_OP05_CASE_DISTRIBUTION)
    manifest_ready = bool(
        preflight_ready
        and len(rows) == P7_R51_REQUIRED_CASE_COUNT
        and distribution_matches
        and _op05_unique_non_empty(blind_ids)
        and _op05_unique_non_empty(case_refs)
        and _op05_unique_non_empty(packet_refs)
    )
    controller_rows = _op05_controller_manifest_rows(rows) if manifest_ready else []
    reviewer_rows = _op05_reviewer_facing_case_index_rows(rows) if manifest_ready else []
    execution_blockers = [] if manifest_ready else dedupe_identifiers(
        ["r54_op05_blocked_until_local_only_preflight_ready", *(op04.get("open_execution_blocker_ids") or [])],
        limit=40,
        max_length=180,
    )
    manifest_reason_refs = (
        ["r54_24_case_manifest_frozen_bodyfree"]
        if manifest_ready
        else dedupe_identifiers(
            ["local_only_preflight_not_ready_for_24_case_manifest_freeze", *(op04.get("preflight_reason_refs") or [])],
            limit=40,
            max_length=180,
        )
    )
    material = {
        "schema_version": P7_R54_OPERATION_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_OPERATION_REENTRY_STEP,
        "scope": P7_R54_OPERATION_REENTRY_SCOPE,
        "policy_kind": P7_R54_OPERATION_REENTRY_POLICY_KIND,
        "policy_section": P7_R54_OP05_STEP_REF,
        "operation_step_ref": P7_R54_OP05_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_operation_24_case_manifest_freeze", max_length=220),
        "review_session_id": _safe_review_session_id(op04.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op04_schema_version": P7_R54_OPERATION_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION,
        "op04_material_ref": clean_identifier(op04.get("material_id"), default="p7_r54_operation_local_only_preflight", max_length=220),
        "op04_next_required_step": clean_identifier(op04.get("next_required_step"), default=P7_R54_OP04_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=180),
        "op04_preflight_status": clean_identifier(op04.get("preflight_status"), default=P7_R54_OP04_PREFLIGHT_BLOCKED_STATUS_REF, max_length=80),
        "op04_preflight_ready": preflight_ready,
        "operation_current_refs": dict(P7_R54_OPERATION_CURRENT_REFS),
        "operation_current_ref_count": len(P7_R54_OPERATION_CURRENT_REFS),
        "actual_review_basis_ref": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "r48_case_matrix_schema_version": P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION,
        "r48_case_matrix_material_ref": r48_material_ref,
        "case_distribution": dict(P7_R54_OP05_CASE_DISTRIBUTION),
        "case_distribution_total_count": sum(P7_R54_OP05_CASE_DISTRIBUTION.values()),
        "case_distribution_matches_design": distribution_matches,
        "manifest_status": P7_R54_OP05_MANIFEST_READY_STATUS_REF if manifest_ready else P7_R54_OP05_MANIFEST_BLOCKED_STATUS_REF,
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
        "case_ref_ids_unique": _op05_unique_non_empty(case_refs) if manifest_ready else False,
        "blind_case_ids_unique": _op05_unique_non_empty(blind_ids) if manifest_ready else False,
        "packet_ref_ids_unique": _op05_unique_non_empty(packet_refs) if manifest_ready else False,
        "blind_case_id_case_ref_separated": set(blind_ids).isdisjoint(set(case_refs)) if manifest_ready else False,
        "blind_case_id_packet_ref_separated": set(blind_ids).isdisjoint(set(packet_refs)) if manifest_ready else False,
        "case_ref_id_packet_ref_separated": set(case_refs).isdisjoint(set(packet_refs)) if manifest_ready else False,
        "controller_manifest_rows": controller_rows,
        "reviewer_facing_case_index_rows": reviewer_rows,
        "controller_manifest_row_count": len(controller_rows),
        "reviewer_facing_row_count": len(reviewer_rows),
        "reviewer_identifier_policy_ref": P7_R54_OP05_REVIEWER_IDENTIFIER_POLICY_REF,
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
        "body_full_packet_generated_here": False,
        "body_full_generation_blocked_until_request_step": True,
        "p5_actual_review_still_not_run": True,
        "actual_review_evidence_complete": False,
        "rating_row_count": 0,
        "question_observation_row_count": 0,
        "disposal_verified": False,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_OP05_IMPLEMENTED_STEPS if manifest_ready else P7_R54_OP04_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_OP05_NOT_YET_IMPLEMENTED_STEPS if manifest_ready else P7_R54_OP04_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R54_OP_NEXT_WORK_AFTER_OP05_REF if manifest_ready else P7_R54_OP_NEXT_WORK_AFTER_OP04_REF,
        "next_required_step": P7_R54_OP06_STEP_REF if manifest_ready else P7_R54_OP05_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_operation_no_touch_contract": _operation_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
    }
    assert_p7_r54_op05_24_case_manifest_freeze_contract(material)
    return material


def assert_p7_r54_op05_24_case_manifest_freeze_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(
        data,
        required=P7_R54_OPERATION_24_CASE_MANIFEST_FREEZE_REQUIRED_FIELD_REFS,
        source="p7_r54_op05_24_case_manifest_freeze",
    )
    _assert_common_operation_contract(
        data,
        schema_version=P7_R54_OPERATION_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION,
        policy_section=P7_R54_OP05_STEP_REF,
        operation_step_ref=P7_R54_OP05_STEP_REF,
        source="p7_r54_op05_24_case_manifest_freeze",
    )
    if data.get("op04_schema_version") != P7_R54_OPERATION_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION:
        raise ValueError("R54 OP05 OP04 schema reference changed")
    _assert_operation_current_refs(data, source="p7_r54_op05_24_case_manifest_freeze")
    if data.get("operation_current_refs_are_actual_review_basis") is not True:
        raise ValueError("R54 OP05 must keep operation-current refs as actual review basis")
    if data.get("required_case_count") != P7_R51_REQUIRED_CASE_COUNT:
        raise ValueError("R54 OP05 required case count changed")
    if data.get("r48_case_matrix_schema_version") != P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION:
        raise ValueError("R54 OP05 R48 case matrix schema reference changed")
    if data.get("case_distribution") != P7_R54_OP05_CASE_DISTRIBUTION:
        raise ValueError("R54 OP05 case distribution changed")
    if data.get("case_distribution_total_count") != P7_R51_REQUIRED_CASE_COUNT:
        raise ValueError("R54 OP05 distribution must total 24 cases")
    if data.get("manifest_status") not in P7_R54_OP05_ALLOWED_MANIFEST_STATUS_REFS:
        raise ValueError("R54 OP05 manifest status changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 OP05 open blockers must match execution blockers")
    if data.get("p4_r11_rows_mixed_in") is not False or data.get("p4_r11_rows_mixed_in_count") != 0:
        raise ValueError("R54 OP05 must not mix P4-R11 rows into the R54 manifest")
    for false_key in (
        "reviewer_facing_family_exposed",
        "reviewer_facing_tier_exposed",
        "reviewer_facing_case_ref_exposed",
        "reviewer_facing_packet_ref_exposed",
        "reviewer_facing_expected_result_exposed",
        "reviewer_facing_hidden_metadata_exposed",
        "body_full_packet_generated_here",
        "disposal_verified",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 OP05 must keep {false_key}=False")
    if data.get("body_full_generation_blocked_until_request_step") is not True:
        raise ValueError("R54 OP05 must keep body-full generation blocked until the request step")
    if data.get("p5_actual_review_still_not_run") is not True:
        raise ValueError("R54 OP05 must not claim actual P5 review ran")
    if data.get("actual_review_evidence_complete") is not False:
        raise ValueError("R54 OP05 must not mark actual review evidence complete")
    if data.get("rating_row_count") != 0 or data.get("question_observation_row_count") != 0:
        raise ValueError("R54 OP05 must not materialize rating/question rows")
    if data.get("human_review_completion_claim_blocked_here") is not True:
        raise ValueError("R54 OP05 must block human-review completion claims")
    if data.get("p6_p8_release_promotion_blocked_here") is not True:
        raise ValueError("R54 OP05 must block P6/P8/release promotion")
    rows = [safe_mapping(row) for row in (data.get("case_rows") or [])]
    controller_rows = [safe_mapping(row) for row in (data.get("controller_manifest_rows") or [])]
    reviewer_rows = [safe_mapping(row) for row in (data.get("reviewer_facing_case_index_rows") or [])]
    manifest_ready = data.get("manifest_status") == P7_R54_OP05_MANIFEST_READY_STATUS_REF
    if manifest_ready:
        if data.get("op04_preflight_status") != P7_R54_OP04_PREFLIGHT_READY_STATUS_REF or data.get("op04_preflight_ready") is not True:
            raise ValueError("R54 OP05 ready manifest requires OP04 ready preflight")
        if data.get("op04_next_required_step") != P7_R54_OP05_STEP_REF:
            raise ValueError("R54 OP05 ready manifest must be built after OP04 ready next step")
        if data.get("case_distribution_matches_design") is not True:
            raise ValueError("R54 OP05 ready manifest must match design distribution")
        if len(rows) != P7_R51_REQUIRED_CASE_COUNT or data.get("case_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 OP05 ready manifest must freeze exactly 24 cases")
        for row in rows:
            _assert_op05_case_row(row)
        if data.get("family_case_counts") != _op05_count_by(rows, "family"):
            raise ValueError("R54 OP05 family counts changed")
        if data.get("case_role_counts") != _op05_count_by(rows, "case_role"):
            raise ValueError("R54 OP05 role counts changed")
        if data.get("subscription_tier_ref_counts") != _op05_count_by(rows, "subscription_tier_ref"):
            raise ValueError("R54 OP05 tier counts changed")
        if data.get("family_case_counts") != P7_R54_OP05_CASE_DISTRIBUTION:
            raise ValueError("R54 OP05 family distribution changed")
        if data.get("boundary_case_count") != 4 or data.get("low_information_boundary_case_count") != 2 or data.get("free_tier_boundary_case_count") != 2:
            raise ValueError("R54 OP05 boundary counts changed")
        blind_ids = _op05_case_refs(rows, "blind_case_id")
        case_refs = _op05_case_refs(rows, "case_ref_id")
        packet_refs = _op05_case_refs(rows, "packet_ref_id")
        for key, values in (
            ("blind_case_ids_unique", blind_ids),
            ("case_ref_ids_unique", case_refs),
            ("packet_ref_ids_unique", packet_refs),
        ):
            if data.get(key) is not True or not _op05_unique_non_empty(values):
                raise ValueError(f"R54 OP05 {key} failed")
        if data.get("blind_case_id_case_ref_separated") is not True or not set(blind_ids).isdisjoint(set(case_refs)):
            raise ValueError("R54 OP05 blind case ids and case refs must be separated")
        if data.get("blind_case_id_packet_ref_separated") is not True or not set(blind_ids).isdisjoint(set(packet_refs)):
            raise ValueError("R54 OP05 blind case ids and packet refs must be separated")
        if data.get("case_ref_id_packet_ref_separated") is not True or not set(case_refs).isdisjoint(set(packet_refs)):
            raise ValueError("R54 OP05 case refs and packet refs must be separated")
        if len(controller_rows) != P7_R51_REQUIRED_CASE_COUNT or data.get("controller_manifest_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 OP05 controller manifest row count changed")
        if len(reviewer_rows) != P7_R51_REQUIRED_CASE_COUNT or data.get("reviewer_facing_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 OP05 reviewer-facing row count changed")
        for row in controller_rows:
            _assert_op05_controller_manifest_row(row)
        for row in reviewer_rows:
            _assert_op05_reviewer_facing_case_index_row(row)
        if data.get("reviewer_identifier_policy_ref") != P7_R54_OP05_REVIEWER_IDENTIFIER_POLICY_REF:
            raise ValueError("R54 OP05 reviewer identifier policy changed")
        if data.get("controller_keeps_family_tier_expected_refs") is not True:
            raise ValueError("R54 OP05 controller must keep family/tier/expected refs")
        if data.get("reviewer_receives_blind_case_id_only") is not True:
            raise ValueError("R54 OP05 reviewer must receive blind case id only")
        if blockers:
            raise ValueError("R54 OP05 ready manifest must not carry blockers")
        if data.get("body_full_packet_generation_request_allowed_next") is not True:
            raise ValueError("R54 OP05 ready manifest must allow the next body-free packet request step")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_OP05_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP05 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_OP05_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP05 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_OP06_STEP_REF:
            raise ValueError("R54 OP05 ready manifest must point to R54-OP-06")
    else:
        if data.get("op04_preflight_ready") is not False:
            raise ValueError("R54 OP05 blocked manifest must not mark OP04 preflight ready")
        if rows or controller_rows or reviewer_rows:
            raise ValueError("R54 OP05 blocked manifest must not freeze rows")
        if data.get("case_count") != 0 or data.get("controller_manifest_row_count") != 0 or data.get("reviewer_facing_row_count") != 0:
            raise ValueError("R54 OP05 blocked manifest row counts must be zero")
        if data.get("case_distribution_matches_design") is not False:
            raise ValueError("R54 OP05 blocked manifest must not claim distribution was frozen")
        if data.get("body_full_packet_generation_request_allowed_next") is not False:
            raise ValueError("R54 OP05 blocked manifest must not allow packet request next")
        if not blockers:
            raise ValueError("R54 OP05 blocked manifest must carry blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_OP04_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP05 blocked manifest must not advance implemented steps past OP04")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_OP04_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP05 blocked manifest not-yet steps changed")
        if data.get("next_required_step") != P7_R54_OP05_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 OP05 blocked manifest must point to preflight repair before manifest freeze")
    return True


def _op06_packet_request_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    request_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        source = safe_mapping(row)
        request_rows.append({
            "packet_request_row_ref": f"r54op06-packet-request-row-{index:03d}",
            "case_ref_id": clean_identifier(source.get("case_ref_id"), max_length=180),
            "blind_case_id": clean_identifier(source.get("blind_case_id"), max_length=180),
            "packet_ref_id": clean_identifier(source.get("packet_ref_id"), max_length=180),
            "family": clean_identifier(source.get("family"), max_length=180),
            "case_role": clean_identifier(source.get("case_role"), max_length=180),
            "subscription_tier_ref": clean_identifier(source.get("subscription_tier_ref"), max_length=80),
            "case_material_status_ref": clean_identifier(source.get("case_material_status_ref"), max_length=180),
            "packet_generation_requested": True,
            "request_is_bodyfree_only": True,
            "packet_content_included": False,
            "local_path_included": False,
            "question_text_included": False,
            "body_free": True,
        })
    return request_rows


def _assert_op06_packet_request_row(row: Mapping[str, Any]) -> None:
    data = safe_mapping(row)
    required = (
        "packet_request_row_ref", "case_ref_id", "blind_case_id", "packet_ref_id", "family", "case_role",
        "subscription_tier_ref", "case_material_status_ref", "packet_generation_requested", "request_is_bodyfree_only",
        "packet_content_included", "local_path_included", "question_text_included", "body_free",
    )
    _assert_required_fields(data, required=required, source="p7_r54_op06_packet_request_row")
    if data.get("packet_generation_requested") is not True or data.get("request_is_bodyfree_only") is not True:
        raise ValueError("R54 OP06 packet request row must be a body-free request")
    for false_key in ("packet_content_included", "local_path_included", "question_text_included"):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 OP06 packet request row must keep {false_key}=False")
    if data.get("body_free") is not True:
        raise ValueError("R54 OP06 packet request row must be body-free")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_op06_packet_request_row")


def build_p7_r54_op06_local_only_body_full_packet_generation_request(
    *,
    case_manifest_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_operation_body_full_packet_generation_request",
) -> dict[str, Any]:
    """Build R54-OP-06 body-free packet generation request without packet content."""
    op05 = safe_mapping(case_manifest_freeze) if case_manifest_freeze is not None else build_p7_r54_op05_24_case_manifest_freeze()
    assert_p7_r54_op05_24_case_manifest_freeze_contract(op05)
    manifest_ready = op05.get("manifest_status") == P7_R54_OP05_MANIFEST_READY_STATUS_REF
    case_rows = [safe_mapping(row) for row in (op05.get("case_rows") or [])] if manifest_ready else []
    packet_ref_ids = _op05_case_refs(case_rows, "packet_ref_id") if manifest_ready else []
    request_rows = _op06_packet_request_rows(case_rows) if manifest_ready else []
    request_ready = bool(
        manifest_ready
        and op05.get("body_full_packet_generation_request_allowed_next") is True
        and len(packet_ref_ids) == P7_R51_REQUIRED_CASE_COUNT
        and _op05_unique_non_empty(packet_ref_ids)
        and len(request_rows) == P7_R51_REQUIRED_CASE_COUNT
    )
    execution_blockers = [] if request_ready else dedupe_identifiers(
        ["r54_op06_blocked_until_24_case_manifest_ready", *(op05.get("open_execution_blocker_ids") or [])],
        limit=40,
        max_length=180,
    )
    reason_refs = [P7_R54_OP06_READY_REASON_REF] if request_ready else dedupe_identifiers(
        ["24_case_manifest_not_ready_for_bodyfree_packet_generation_request", *(op05.get("manifest_reason_refs") or [])],
        limit=40,
        max_length=180,
    )
    material = {
        "schema_version": P7_R54_OPERATION_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_OPERATION_REENTRY_STEP,
        "scope": P7_R54_OPERATION_REENTRY_SCOPE,
        "policy_kind": P7_R54_OPERATION_REENTRY_POLICY_KIND,
        "policy_section": P7_R54_OP06_STEP_REF,
        "operation_step_ref": P7_R54_OP06_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_operation_body_full_packet_generation_request", max_length=220),
        "review_session_id": _safe_review_session_id(op05.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op05_schema_version": P7_R54_OPERATION_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION,
        "op05_material_ref": clean_identifier(op05.get("material_id"), default="p7_r54_operation_24_case_manifest_freeze", max_length=220),
        "op05_next_required_step": clean_identifier(op05.get("next_required_step"), default=P7_R54_OP05_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=180),
        "op05_manifest_status": clean_identifier(op05.get("manifest_status"), default=P7_R54_OP05_MANIFEST_BLOCKED_STATUS_REF, max_length=120),
        "op05_manifest_ready": manifest_ready,
        "operation_current_refs": dict(P7_R54_OPERATION_CURRENT_REFS),
        "operation_current_ref_count": len(P7_R54_OPERATION_CURRENT_REFS),
        "actual_review_basis_ref": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "op05_case_count": int(op05.get("case_count") or 0),
        "op05_controller_manifest_row_count": int(op05.get("controller_manifest_row_count") or 0),
        "op05_reviewer_facing_row_count": int(op05.get("reviewer_facing_row_count") or 0),
        "packet_generation_request_status": P7_R54_OP06_REQUEST_READY_STATUS_REF if request_ready else P7_R54_OP06_REQUEST_BLOCKED_STATUS_REF,
        "packet_generation_request_ref": P7_R54_OP06_PACKET_GENERATION_REQUEST_REF if request_ready else "not_requested_until_manifest_ready",
        "packet_generation_request_policy_ref": P7_R54_OP06_PACKET_GENERATION_REQUEST_POLICY_REF,
        "packet_generation_request_reason_refs": reason_refs,
        "execution_blocker_ids": execution_blockers,
        "open_execution_blocker_ids": execution_blockers,
        "requested_case_count": len(case_rows) if request_ready else 0,
        "requested_packet_count": len(packet_ref_ids) if request_ready else 0,
        "requested_packet_ref_ids": packet_ref_ids if request_ready else [],
        "requested_packet_ref_count": len(packet_ref_ids) if request_ready else 0,
        "requested_packet_ref_ids_unique": _op05_unique_non_empty(packet_ref_ids) if request_ready else False,
        "packet_generation_request_rows": request_rows if request_ready else [],
        "packet_generation_request_row_count": len(request_rows) if request_ready else 0,
        "request_is_bodyfree_only": True,
        "request_contains_packet_content": False,
        "request_contains_local_path": False,
        "request_contains_question_text": False,
        "local_only_output_scope_ref": P7_R54_OP06_LOCAL_ONLY_OUTPUT_SCOPE_REF,
        "local_review_root_path_included": False,
        "local_packet_directory_path_included": False,
        "body_full_packet_content_included": False,
        "body_full_packet_generation_local_operation_started_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packet_export_allowed": False,
        "body_full_packet_zip_inclusion_allowed": False,
        "reviewer_notes_export_allowed": False,
        "packet_generation_request_materialized_here": request_ready,
        "p5_actual_review_still_not_run": True,
        "actual_review_evidence_complete": False,
        "rating_row_count": 0,
        "question_observation_row_count": 0,
        "disposal_verified": False,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_OP06_IMPLEMENTED_STEPS if request_ready else P7_R54_OP05_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_OP06_NOT_YET_IMPLEMENTED_STEPS if request_ready else P7_R54_OP05_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R54_OP_NEXT_WORK_AFTER_OP06_REF if request_ready else P7_R54_OP_NEXT_WORK_AFTER_OP05_REF,
        "next_required_step": P7_R54_OP07_STEP_REF if request_ready else P7_R54_OP06_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_operation_no_touch_contract": _operation_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
    }
    assert_p7_r54_op06_local_only_body_full_packet_generation_request_contract(material)
    return material


def assert_p7_r54_op06_local_only_body_full_packet_generation_request_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_OPERATION_BODY_FULL_PACKET_GENERATION_REQUEST_REQUIRED_FIELD_REFS, source="p7_r54_op06_body_full_packet_generation_request")
    _assert_common_operation_contract(
        data,
        schema_version=P7_R54_OPERATION_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION,
        policy_section=P7_R54_OP06_STEP_REF,
        operation_step_ref=P7_R54_OP06_STEP_REF,
        source="p7_r54_op06_body_full_packet_generation_request",
    )
    if data.get("op05_schema_version") != P7_R54_OPERATION_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION:
        raise ValueError("R54 OP06 OP05 schema reference changed")
    _assert_operation_current_refs(data, source="p7_r54_op06_body_full_packet_generation_request")
    if data.get("operation_current_refs_are_actual_review_basis") is not True:
        raise ValueError("R54 OP06 must keep operation-current refs as actual review basis")
    if data.get("required_case_count") != P7_R51_REQUIRED_CASE_COUNT:
        raise ValueError("R54 OP06 required case count changed")
    if data.get("packet_generation_request_status") not in P7_R54_OP06_ALLOWED_REQUEST_STATUS_REFS:
        raise ValueError("R54 OP06 request status changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 OP06 open blockers must match execution blockers")
    for false_key in (
        "request_contains_packet_content", "request_contains_local_path", "request_contains_question_text",
        "local_review_root_path_included", "local_packet_directory_path_included", "body_full_packet_content_included",
        "body_full_packet_generation_local_operation_started_here", "body_full_packet_generated_here", "body_full_packet_export_allowed",
        "body_full_packet_zip_inclusion_allowed", "reviewer_notes_export_allowed", "actual_review_evidence_complete", "disposal_verified",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 OP06 must keep {false_key}=False")
    if data.get("request_is_bodyfree_only") is not True:
        raise ValueError("R54 OP06 request must be body-free only")
    if data.get("p5_actual_review_still_not_run") is not True:
        raise ValueError("R54 OP06 must keep P5 actual review not run")
    if data.get("rating_row_count") != 0 or data.get("question_observation_row_count") != 0:
        raise ValueError("R54 OP06 must not materialize rating/question rows")
    if data.get("human_review_completion_claim_blocked_here") is not True or data.get("p6_p8_release_promotion_blocked_here") is not True:
        raise ValueError("R54 OP06 must block human-review and promotion claims")
    request_ready = data.get("packet_generation_request_status") == P7_R54_OP06_REQUEST_READY_STATUS_REF
    request_rows = [safe_mapping(row) for row in (data.get("packet_generation_request_rows") or [])]
    packet_ref_ids = [clean_identifier(item, max_length=180) for item in (data.get("requested_packet_ref_ids") or [])]
    if request_ready:
        if data.get("op05_manifest_status") != P7_R54_OP05_MANIFEST_READY_STATUS_REF or data.get("op05_manifest_ready") is not True:
            raise ValueError("R54 OP06 ready request requires OP05 ready manifest")
        if data.get("op05_next_required_step") != P7_R54_OP06_STEP_REF:
            raise ValueError("R54 OP06 ready request must be built after OP05 ready next step")
        for count_key in ("op05_case_count", "op05_controller_manifest_row_count", "op05_reviewer_facing_row_count"):
            if data.get(count_key) != P7_R51_REQUIRED_CASE_COUNT:
                raise ValueError(f"R54 OP06 ready request requires {count_key}=24")
        if data.get("packet_generation_request_ref") != P7_R54_OP06_PACKET_GENERATION_REQUEST_REF:
            raise ValueError("R54 OP06 packet generation request ref changed")
        if data.get("packet_generation_request_policy_ref") != P7_R54_OP06_PACKET_GENERATION_REQUEST_POLICY_REF:
            raise ValueError("R54 OP06 request policy ref changed")
        if data.get("packet_generation_request_reason_refs") != [P7_R54_OP06_READY_REASON_REF]:
            raise ValueError("R54 OP06 ready reason refs changed")
        if blockers:
            raise ValueError("R54 OP06 ready request must not carry execution blockers")
        if data.get("requested_case_count") != P7_R51_REQUIRED_CASE_COUNT or data.get("requested_packet_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 OP06 ready request must request 24 cases and packets")
        if data.get("requested_packet_ref_count") != P7_R51_REQUIRED_CASE_COUNT or len(packet_ref_ids) != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 OP06 ready request packet ref count changed")
        if data.get("requested_packet_ref_ids_unique") is not True or not _op05_unique_non_empty(packet_ref_ids):
            raise ValueError("R54 OP06 packet refs must be unique")
        if data.get("packet_generation_request_row_count") != P7_R51_REQUIRED_CASE_COUNT or len(request_rows) != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 OP06 request row count changed")
        for row in request_rows:
            _assert_op06_packet_request_row(row)
        if _op05_case_refs(request_rows, "packet_ref_id") != packet_ref_ids:
            raise ValueError("R54 OP06 request rows must match requested packet refs")
        if data.get("packet_generation_request_materialized_here") is not True:
            raise ValueError("R54 OP06 ready request must materialize body-free request refs")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_OP06_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP06 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_OP06_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP06 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_OP07_STEP_REF:
            raise ValueError("R54 OP06 ready request must point to R54-OP-07")
    else:
        if request_rows or packet_ref_ids:
            raise ValueError("R54 OP06 blocked request must not carry request rows or packet refs")
        for count_key in ("requested_case_count", "requested_packet_count", "requested_packet_ref_count", "packet_generation_request_row_count"):
            if data.get(count_key) != 0:
                raise ValueError(f"R54 OP06 blocked request must keep {count_key}=0")
        if data.get("requested_packet_ref_ids_unique") is not False or data.get("packet_generation_request_materialized_here") is not False:
            raise ValueError("R54 OP06 blocked request must not claim request materialization")
        if not blockers:
            raise ValueError("R54 OP06 blocked request must carry execution blockers")
        if data.get("next_required_step") != P7_R54_OP06_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 OP06 blocked request must point to manifest repair before request")
    return True


def build_p7_r54_op07_packet_generation_local_operation(
    *,
    body_full_packet_generation_request: Mapping[str, Any] | None = None,
    local_operation_receipt_ref: Any = None,
    declared_generated_packet_ref_ids: Sequence[Any] | Any | None = None,
    export_denylist_violation_refs: Sequence[Any] | Any | None = None,
    material_id: Any = "p7_r54_operation_packet_generation_local_operation",
) -> dict[str, Any]:
    """Build R54-OP-07 body-free local packet-generation operation receipt boundary."""
    op06 = safe_mapping(body_full_packet_generation_request) if body_full_packet_generation_request is not None else build_p7_r54_op06_local_only_body_full_packet_generation_request()
    assert_p7_r54_op06_local_only_body_full_packet_generation_request_contract(op06)
    request_ready = op06.get("packet_generation_request_status") == P7_R54_OP06_REQUEST_READY_STATUS_REF
    expected_packet_refs = [clean_identifier(item, max_length=180) for item in (op06.get("requested_packet_ref_ids") or [])]
    receipt_ref = clean_identifier(local_operation_receipt_ref, default="missing_local_operation_receipt_ref", max_length=220)
    generated_refs = dedupe_identifiers(declared_generated_packet_ref_ids, limit=P7_R51_REQUIRED_CASE_COUNT + 1, max_length=180)
    deny_refs = dedupe_identifiers(export_denylist_violation_refs, limit=40, max_length=180)
    refs_match = bool(request_ready and receipt_ref == P7_R54_OP07_LOCAL_OPERATION_RECEIPT_REF and generated_refs == expected_packet_refs and len(generated_refs) == P7_R51_REQUIRED_CASE_COUNT and _op05_unique_non_empty(generated_refs) and not deny_refs)
    local_ready = refs_match
    execution_blockers = [] if local_ready else dedupe_identifiers([
        "r54_op07_blocked_until_bodyfree_local_generation_receipt_ready",
        *(op06.get("open_execution_blocker_ids") or []),
        *([] if request_ready else ["packet_generation_request_not_ready"]),
        *([] if receipt_ref == P7_R54_OP07_LOCAL_OPERATION_RECEIPT_REF else ["local_operation_receipt_ref_missing_or_mismatched"]),
        *([] if generated_refs == expected_packet_refs and len(generated_refs) == P7_R51_REQUIRED_CASE_COUNT else ["declared_generated_packet_refs_missing_or_mismatched"]),
        *([] if not deny_refs else ["export_denylist_violation_detected"]),
    ], limit=40, max_length=180)
    reason_refs = [P7_R54_OP07_READY_REASON_REF] if local_ready else dedupe_identifiers(
        ["local_packet_generation_operation_not_ready", *(op06.get("packet_generation_request_reason_refs") or []), *execution_blockers],
        limit=60,
        max_length=180,
    )
    material = {
        "schema_version": P7_R54_OPERATION_PACKET_GENERATION_LOCAL_OPERATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_OPERATION_REENTRY_STEP,
        "scope": P7_R54_OPERATION_REENTRY_SCOPE,
        "policy_kind": P7_R54_OPERATION_REENTRY_POLICY_KIND,
        "policy_section": P7_R54_OP07_STEP_REF,
        "operation_step_ref": P7_R54_OP07_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_operation_packet_generation_local_operation", max_length=220),
        "review_session_id": _safe_review_session_id(op06.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op06_schema_version": P7_R54_OPERATION_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION,
        "op06_material_ref": clean_identifier(op06.get("material_id"), default="p7_r54_operation_body_full_packet_generation_request", max_length=220),
        "op06_next_required_step": clean_identifier(op06.get("next_required_step"), default=P7_R54_OP06_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=180),
        "op06_packet_generation_request_status": clean_identifier(op06.get("packet_generation_request_status"), default=P7_R54_OP06_REQUEST_BLOCKED_STATUS_REF, max_length=120),
        "op06_packet_generation_request_ref": clean_identifier(op06.get("packet_generation_request_ref"), default="not_requested_until_manifest_ready", max_length=220),
        "op06_request_ready": request_ready,
        "operation_current_refs": dict(P7_R54_OPERATION_CURRENT_REFS),
        "operation_current_ref_count": len(P7_R54_OPERATION_CURRENT_REFS),
        "actual_review_basis_ref": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "expected_packet_ref_ids": expected_packet_refs if request_ready else [],
        "expected_packet_ref_count": len(expected_packet_refs) if request_ready else 0,
        "local_operation_status": P7_R54_OP07_LOCAL_OPERATION_READY_STATUS_REF if local_ready else P7_R54_OP07_LOCAL_OPERATION_BLOCKED_STATUS_REF,
        "local_operation_receipt_ref": receipt_ref,
        "local_operation_receipt_policy_ref": P7_R54_OP07_LOCAL_OPERATION_RECEIPT_POLICY_REF,
        "local_operation_reason_refs": reason_refs,
        "execution_blocker_ids": execution_blockers,
        "open_execution_blocker_ids": execution_blockers,
        "declared_generated_packet_ref_ids": generated_refs if request_ready else [],
        "declared_generated_packet_ref_count": len(generated_refs) if request_ready else 0,
        "declared_generated_packet_ref_ids_unique": _op05_unique_non_empty(generated_refs) if request_ready else False,
        "packet_ref_ids_match_request": refs_match,
        "packet_generation_local_operation_declared_complete": local_ready,
        "packet_generation_local_operation_unverified_by_artifact": local_ready,
        "local_operation_executed_outside_artifact_boundary": local_ready,
        "local_operation_receipt_materialized_here": local_ready,
        "local_operation_receipt_body_stored_here": False,
        "body_full_packet_content_included": False,
        "body_full_packet_generated_here": False,
        "actual_body_full_packet_generated_here": False,
        "local_reviewer_payload_materialized_here": False,
        "local_review_root_path_included": False,
        "local_packet_directory_path_included": False,
        "local_packet_exported": False,
        "local_packet_export_candidate_count": 0,
        "body_full_packet_export_allowed": False,
        "body_full_packet_zip_inclusion_allowed": False,
        "reviewer_notes_export_allowed": False,
        "export_denylist_violation_refs": deny_refs,
        "export_denylist_violation_count": len(deny_refs),
        "packet_completeness_scan_required_next": local_ready,
        "p5_actual_review_still_not_run": True,
        "actual_review_evidence_complete": False,
        "rating_row_count": 0,
        "question_observation_row_count": 0,
        "disposal_verified": False,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_OP07_IMPLEMENTED_STEPS if local_ready else P7_R54_OP06_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_OP07_NOT_YET_IMPLEMENTED_STEPS if local_ready else P7_R54_OP06_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R54_OP_NEXT_WORK_AFTER_OP07_REF if local_ready else P7_R54_OP_NEXT_WORK_AFTER_OP06_REF,
        "next_required_step": P7_R54_OP08_STEP_REF if local_ready else P7_R54_OP07_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_operation_no_touch_contract": _operation_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
    }
    assert_p7_r54_op07_packet_generation_local_operation_contract(material)
    return material


def assert_p7_r54_op07_packet_generation_local_operation_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_OPERATION_PACKET_GENERATION_LOCAL_OPERATION_REQUIRED_FIELD_REFS, source="p7_r54_op07_packet_generation_local_operation")
    _assert_common_operation_contract(
        data,
        schema_version=P7_R54_OPERATION_PACKET_GENERATION_LOCAL_OPERATION_SCHEMA_VERSION,
        policy_section=P7_R54_OP07_STEP_REF,
        operation_step_ref=P7_R54_OP07_STEP_REF,
        source="p7_r54_op07_packet_generation_local_operation",
    )
    if data.get("op06_schema_version") != P7_R54_OPERATION_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION:
        raise ValueError("R54 OP07 OP06 schema reference changed")
    _assert_operation_current_refs(data, source="p7_r54_op07_packet_generation_local_operation")
    if data.get("operation_current_refs_are_actual_review_basis") is not True or data.get("required_case_count") != P7_R51_REQUIRED_CASE_COUNT:
        raise ValueError("R54 OP07 basis or required case count changed")
    if data.get("local_operation_status") not in P7_R54_OP07_ALLOWED_LOCAL_OPERATION_STATUS_REFS:
        raise ValueError("R54 OP07 local operation status changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 OP07 open blockers must match execution blockers")
    for false_key in (
        "local_operation_receipt_body_stored_here", "body_full_packet_content_included", "body_full_packet_generated_here",
        "actual_body_full_packet_generated_here", "local_reviewer_payload_materialized_here", "local_review_root_path_included",
        "local_packet_directory_path_included", "local_packet_exported", "body_full_packet_export_allowed",
        "body_full_packet_zip_inclusion_allowed", "reviewer_notes_export_allowed", "actual_review_evidence_complete", "disposal_verified",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 OP07 must keep {false_key}=False")
    if data.get("local_packet_export_candidate_count") != 0:
        raise ValueError("R54 OP07 must not expose packet export candidates")
    if data.get("p5_actual_review_still_not_run") is not True:
        raise ValueError("R54 OP07 must keep P5 actual review not run")
    if data.get("rating_row_count") != 0 or data.get("question_observation_row_count") != 0:
        raise ValueError("R54 OP07 must not materialize rating/question rows")
    if data.get("human_review_completion_claim_blocked_here") is not True or data.get("p6_p8_release_promotion_blocked_here") is not True:
        raise ValueError("R54 OP07 must block human-review and promotion claims")
    expected_packet_refs = [clean_identifier(item, max_length=180) for item in (data.get("expected_packet_ref_ids") or [])]
    generated_refs = [clean_identifier(item, max_length=180) for item in (data.get("declared_generated_packet_ref_ids") or [])]
    local_ready = data.get("local_operation_status") == P7_R54_OP07_LOCAL_OPERATION_READY_STATUS_REF
    if local_ready:
        if data.get("op06_request_ready") is not True or data.get("op06_next_required_step") != P7_R54_OP07_STEP_REF:
            raise ValueError("R54 OP07 ready local operation requires OP06 ready next step")
        if data.get("op06_packet_generation_request_status") != P7_R54_OP06_REQUEST_READY_STATUS_REF:
            raise ValueError("R54 OP07 ready local operation requires OP06 request status ready")
        if data.get("op06_packet_generation_request_ref") != P7_R54_OP06_PACKET_GENERATION_REQUEST_REF:
            raise ValueError("R54 OP07 OP06 request ref changed")
        if data.get("expected_packet_ref_count") != P7_R51_REQUIRED_CASE_COUNT or len(expected_packet_refs) != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 OP07 expected packet refs changed")
        if data.get("local_operation_receipt_ref") != P7_R54_OP07_LOCAL_OPERATION_RECEIPT_REF:
            raise ValueError("R54 OP07 local receipt ref changed")
        if data.get("local_operation_receipt_policy_ref") != P7_R54_OP07_LOCAL_OPERATION_RECEIPT_POLICY_REF:
            raise ValueError("R54 OP07 receipt policy ref changed")
        if data.get("local_operation_reason_refs") != [P7_R54_OP07_READY_REASON_REF]:
            raise ValueError("R54 OP07 ready reason refs changed")
        if blockers:
            raise ValueError("R54 OP07 ready local operation must not carry blockers")
        if data.get("declared_generated_packet_ref_count") != P7_R51_REQUIRED_CASE_COUNT or len(generated_refs) != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 OP07 generated packet ref count changed")
        if data.get("declared_generated_packet_ref_ids_unique") is not True or not _op05_unique_non_empty(generated_refs):
            raise ValueError("R54 OP07 generated packet refs must be unique")
        if data.get("packet_ref_ids_match_request") is not True or generated_refs != expected_packet_refs:
            raise ValueError("R54 OP07 generated packet refs must match OP06 request refs")
        for key in (
            "packet_generation_local_operation_declared_complete", "packet_generation_local_operation_unverified_by_artifact",
            "local_operation_executed_outside_artifact_boundary", "local_operation_receipt_materialized_here", "packet_completeness_scan_required_next",
        ):
            if data.get(key) is not True:
                raise ValueError(f"R54 OP07 ready local operation must keep {key}=True")
        if data.get("export_denylist_violation_refs") != [] or data.get("export_denylist_violation_count") != 0:
            raise ValueError("R54 OP07 ready local operation must have no export denylist violations")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_OP07_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP07 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_OP07_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP07 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_OP08_STEP_REF:
            raise ValueError("R54 OP07 ready local operation must point to R54-OP-08")
    else:
        if data.get("packet_generation_local_operation_declared_complete") is not False:
            raise ValueError("R54 OP07 blocked local operation must not declare completion")
        if data.get("packet_generation_local_operation_unverified_by_artifact") is not False:
            raise ValueError("R54 OP07 blocked local operation must not claim local packets exist")
        if data.get("local_operation_executed_outside_artifact_boundary") is not False:
            raise ValueError("R54 OP07 blocked local operation must not claim external local operation execution")
        if data.get("local_operation_receipt_materialized_here") is not False or data.get("packet_completeness_scan_required_next") is not False:
            raise ValueError("R54 OP07 blocked local operation must not materialize receipt or require scan")
        if not blockers:
            raise ValueError("R54 OP07 blocked local operation must carry execution blockers")
        if data.get("next_required_step") != P7_R54_OP07_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 OP07 blocked local operation must point to local operation receipt requirement")
    return True


def _op08_packet_scan_rows(
    *,
    packet_ref_ids: Sequence[Any],
    required_fields_present_ref_ids: Sequence[Any],
    export_denylist_violation_refs: Sequence[Any],
    body_full_packet_export_candidate_refs: Sequence[Any],
    body_full_packet_content_detected_in_export: bool,
    question_text_detected_in_export: bool,
    local_path_detected_in_export: bool,
) -> list[dict[str, Any]]:
    required_present = set(dedupe_identifiers(required_fields_present_ref_ids, limit=200, max_length=180))
    violation_refs = set(dedupe_identifiers(export_denylist_violation_refs, limit=80, max_length=220))
    export_candidate_refs = set(dedupe_identifiers(body_full_packet_export_candidate_refs, limit=80, max_length=220))
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(packet_ref_ids, start=1):
        packet_ref = clean_identifier(item, max_length=180)
        rows.append({
            "packet_scan_row_ref": f"r54op08-packet-scan-row-{index:03d}",
            "packet_ref_id": packet_ref,
            "packet_present_ref": packet_ref,
            "required_fields_present_ref": packet_ref if packet_ref in required_present else "missing_required_packet_fields_bodyfree_ref",
            "required_packet_field_refs": list(P7_R54_OP08_REQUIRED_PACKET_FIELD_REFS),
            "required_packet_field_ref_count": len(P7_R54_OP08_REQUIRED_PACKET_FIELD_REFS),
            "packet_present": True,
            "required_fields_present": packet_ref in required_present,
            "export_denylist_violation_detected": bool(packet_ref in violation_refs or violation_refs),
            "body_full_packet_export_candidate_detected": bool(packet_ref in export_candidate_refs or export_candidate_refs),
            "body_full_packet_content_detected_in_export": bool(body_full_packet_content_detected_in_export),
            "question_text_detected_in_export": bool(question_text_detected_in_export),
            "local_path_detected_in_export": bool(local_path_detected_in_export),
            "packet_scan_is_bodyfree_only": True,
            "packet_content_included": False,
            "local_path_included": False,
            "question_text_included": False,
            "body_free": True,
        })
    return rows


def _assert_op08_packet_scan_row(row: Mapping[str, Any]) -> None:
    data = safe_mapping(row)
    required = (
        "packet_scan_row_ref", "packet_ref_id", "packet_present_ref", "required_fields_present_ref",
        "required_packet_field_refs", "required_packet_field_ref_count", "packet_present", "required_fields_present",
        "export_denylist_violation_detected", "body_full_packet_export_candidate_detected",
        "body_full_packet_content_detected_in_export", "question_text_detected_in_export", "local_path_detected_in_export",
        "packet_scan_is_bodyfree_only", "packet_content_included", "local_path_included", "question_text_included", "body_free",
    )
    _assert_required_fields(data, required=required, source="p7_r54_op08_packet_scan_row")
    if data.get("packet_scan_is_bodyfree_only") is not True or data.get("body_free") is not True:
        raise ValueError("R54 OP08 packet scan row must remain body-free")
    if data.get("packet_present") is not True:
        raise ValueError("R54 OP08 packet scan row must mark packet present only through body-free refs")
    if tuple(data.get("required_packet_field_refs") or ()) != P7_R54_OP08_REQUIRED_PACKET_FIELD_REFS:
        raise ValueError("R54 OP08 packet scan row required field refs changed")
    if data.get("required_packet_field_ref_count") != len(P7_R54_OP08_REQUIRED_PACKET_FIELD_REFS):
        raise ValueError("R54 OP08 packet scan row required field count changed")
    for false_key in ("packet_content_included", "local_path_included", "question_text_included"):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 OP08 packet scan row must keep {false_key}=False")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_op08_packet_scan_row")


def build_p7_r54_op08_packet_completeness_export_denylist_scan(
    *,
    packet_generation_local_operation: Mapping[str, Any] | None = None,
    declared_packet_ref_ids: Sequence[Any] | None = None,
    required_fields_present_ref_ids: Sequence[Any] | None = None,
    export_denylist_violation_refs: Sequence[Any] | None = None,
    body_full_packet_export_candidate_refs: Sequence[Any] | None = None,
    body_full_packet_content_detected_in_export: bool = False,
    question_text_detected_in_export: bool = False,
    local_path_detected_in_export: bool = False,
    material_id: Any = "p7_r54_operation_packet_completeness_export_denylist_scan",
) -> dict[str, Any]:
    """Build R54-OP-08 body-free packet completeness / export denylist scan."""
    op07 = safe_mapping(packet_generation_local_operation) if packet_generation_local_operation is not None else build_p7_r54_op07_packet_generation_local_operation()
    assert_p7_r54_op07_packet_generation_local_operation_contract(op07)
    op07_ready = op07.get("local_operation_status") == P7_R54_OP07_LOCAL_OPERATION_READY_STATUS_REF
    expected_refs = [clean_identifier(item, max_length=180) for item in (op07.get("expected_packet_ref_ids") or [])]
    default_declared_refs = [clean_identifier(item, max_length=180) for item in (op07.get("declared_generated_packet_ref_ids") or [])]
    declared_refs = dedupe_identifiers(
        declared_packet_ref_ids if declared_packet_ref_ids is not None else default_declared_refs,
        limit=200,
        max_length=180,
    ) if op07_ready else []
    required_refs = dedupe_identifiers(
        required_fields_present_ref_ids if required_fields_present_ref_ids is not None else declared_refs,
        limit=200,
        max_length=180,
    ) if op07_ready else []
    deny_refs = dedupe_identifiers(export_denylist_violation_refs or [], limit=80, max_length=220)
    export_candidate_refs = dedupe_identifiers(body_full_packet_export_candidate_refs or [], limit=80, max_length=220)
    scan_rows = _op08_packet_scan_rows(
        packet_ref_ids=declared_refs,
        required_fields_present_ref_ids=required_refs,
        export_denylist_violation_refs=deny_refs,
        body_full_packet_export_candidate_refs=export_candidate_refs,
        body_full_packet_content_detected_in_export=body_full_packet_content_detected_in_export,
        question_text_detected_in_export=question_text_detected_in_export,
        local_path_detected_in_export=local_path_detected_in_export,
    ) if op07_ready else []
    packet_refs_match = bool(op07_ready and declared_refs == expected_refs and len(declared_refs) == P7_R51_REQUIRED_CASE_COUNT)
    packet_count_ready = bool(packet_refs_match and _op05_unique_non_empty(declared_refs))
    required_count = sum(1 for row in scan_rows if row.get("required_fields_present") is True)
    completeness_ready = bool(packet_count_ready and required_count == P7_R51_REQUIRED_CASE_COUNT)
    leak_detected = bool(deny_refs or export_candidate_refs or body_full_packet_content_detected_in_export or question_text_detected_in_export or local_path_detected_in_export)
    scan_ready = bool(op07_ready and completeness_ready and not leak_detected)
    if scan_ready:
        scan_status = P7_R54_OP08_PACKET_SCAN_READY_STATUS_REF
    elif leak_detected:
        scan_status = P7_R54_OP08_PACKET_SCAN_BLOCKED_BY_LEAK_STATUS_REF
    else:
        scan_status = P7_R54_OP08_PACKET_SCAN_BLOCKED_STATUS_REF
    blocker_seed: list[str] = []
    if not op07_ready:
        blocker_seed.append("r54_op08_blocked_until_op07_local_operation_ready")
    if op07_ready and not packet_count_ready:
        blocker_seed.append("packet_ref_count_or_identity_mismatch")
    if op07_ready and not completeness_ready:
        blocker_seed.append("packet_required_fields_missing")
    if deny_refs:
        blocker_seed.append("export_denylist_violation_detected")
    if export_candidate_refs:
        blocker_seed.append("body_full_packet_export_candidate_detected")
    if body_full_packet_content_detected_in_export:
        blocker_seed.append("body_full_packet_content_detected_in_export")
    if question_text_detected_in_export:
        blocker_seed.append("question_text_detected_in_export")
    if local_path_detected_in_export:
        blocker_seed.append("local_path_detected_in_export")
    execution_blockers = [] if scan_ready else dedupe_identifiers([*blocker_seed, *(op07.get("open_execution_blocker_ids") or [])], limit=60, max_length=180)
    reason_refs = [P7_R54_OP08_READY_REASON_REF] if scan_ready else dedupe_identifiers([scan_status, *execution_blockers], limit=60, max_length=180)
    material = {
        "schema_version": P7_R54_OPERATION_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_OPERATION_REENTRY_STEP,
        "scope": P7_R54_OPERATION_REENTRY_SCOPE,
        "policy_kind": P7_R54_OPERATION_REENTRY_POLICY_KIND,
        "policy_section": P7_R54_OP08_STEP_REF,
        "operation_step_ref": P7_R54_OP08_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_operation_packet_completeness_export_denylist_scan", max_length=220),
        "review_session_id": _safe_review_session_id(op07.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op07_schema_version": P7_R54_OPERATION_PACKET_GENERATION_LOCAL_OPERATION_SCHEMA_VERSION,
        "op07_material_ref": clean_identifier(op07.get("material_id"), default="p7_r54_operation_packet_generation_local_operation", max_length=220),
        "op07_next_required_step": clean_identifier(op07.get("next_required_step"), default="", max_length=180),
        "op07_local_operation_status": clean_identifier(op07.get("local_operation_status"), default=P7_R54_OP07_LOCAL_OPERATION_BLOCKED_STATUS_REF, max_length=180),
        "op07_local_operation_ready": op07_ready,
        "operation_current_refs": dict(P7_R54_OPERATION_CURRENT_REFS),
        "operation_current_ref_count": len(P7_R54_OPERATION_CURRENT_REFS),
        "actual_review_basis_ref": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "packet_scan_status": scan_status,
        "packet_scan_ref": P7_R54_OP08_PACKET_SCAN_REF if scan_ready else "packet_scan_not_ready_bodyfree",
        "packet_scan_reason_refs": reason_refs,
        "execution_blocker_ids": execution_blockers,
        "open_execution_blocker_ids": execution_blockers,
        "expected_packet_ref_ids": expected_refs if op07_ready else [],
        "expected_packet_ref_count": len(expected_refs) if op07_ready else 0,
        "declared_packet_ref_ids": declared_refs,
        "declared_packet_ref_count": len(declared_refs),
        "declared_packet_ref_ids_unique": _op05_unique_non_empty(declared_refs),
        "packet_ref_ids_match_local_operation": packet_refs_match,
        "packet_scan_rows": scan_rows,
        "packet_scan_row_count": len(scan_rows),
        "total_case_count": P7_R51_REQUIRED_CASE_COUNT if op07_ready else 0,
        "packet_present_count": len(declared_refs),
        "required_fields_present_count": required_count,
        "required_packet_field_refs": list(P7_R54_OP08_REQUIRED_PACKET_FIELD_REFS),
        "required_packet_field_ref_count": len(P7_R54_OP08_REQUIRED_PACKET_FIELD_REFS),
        "packet_completeness_ready": completeness_ready,
        "export_denylist_policy_ref": P7_R54_OP04_EXPORT_DENYLIST_POLICY_READY_REF,
        "export_denylist_patterns": list(P7_R47_EXPORT_DENYLIST_PATTERNS),
        "export_denylist_violation_refs": deny_refs,
        "export_denylist_violation_count": len(deny_refs),
        "body_full_packet_export_candidate_refs": export_candidate_refs,
        "body_full_packet_export_candidate_count": len(export_candidate_refs),
        "body_full_packet_content_detected_in_export": bool(body_full_packet_content_detected_in_export),
        "question_text_detected_in_export": bool(question_text_detected_in_export),
        "local_path_detected_in_export": bool(local_path_detected_in_export),
        "packet_scan_is_bodyfree_only": True,
        "packet_scan_contains_packet_content": False,
        "packet_scan_contains_local_path": False,
        "packet_scan_contains_question_text": False,
        "reviewer_instruction_rating_form_freeze_allowed_next": scan_ready,
        "body_full_packet_content_included": False,
        "body_full_packet_generated_here": False,
        "actual_body_full_packet_generated_here": False,
        "local_review_root_path_included": False,
        "local_packet_directory_path_included": False,
        "local_packet_exported": False,
        "body_full_packet_export_allowed": False,
        "body_full_packet_zip_inclusion_allowed": False,
        "reviewer_notes_export_allowed": False,
        "p5_actual_review_still_not_run": True,
        "actual_review_evidence_complete": False,
        "rating_row_count": 0,
        "question_observation_row_count": 0,
        "disposal_verified": False,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(
            P7_R54_OP08_IMPLEMENTED_STEPS
            if scan_ready
            else (P7_R54_OP07_IMPLEMENTED_STEPS if op07_ready else P7_R54_OP06_IMPLEMENTED_STEPS)
        ),
        "not_yet_implemented_steps": list(
            P7_R54_OP08_NOT_YET_IMPLEMENTED_STEPS
            if scan_ready
            else (P7_R54_OP07_NOT_YET_IMPLEMENTED_STEPS if op07_ready else P7_R54_OP06_NOT_YET_IMPLEMENTED_STEPS)
        ),
        "first_next_work_ref": (
            P7_R54_OP_NEXT_WORK_AFTER_OP08_REF
            if scan_ready
            else (P7_R54_OP_NEXT_WORK_AFTER_OP07_REF if op07_ready else P7_R54_OP_NEXT_WORK_AFTER_OP06_REF)
        ),
        "next_required_step": P7_R54_OP09_STEP_REF if scan_ready else P7_R54_OP08_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_operation_no_touch_contract": _operation_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
    }
    assert_p7_r54_op08_packet_completeness_export_denylist_scan_contract(material)
    return material


def assert_p7_r54_op08_packet_completeness_export_denylist_scan_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_OPERATION_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_REQUIRED_FIELD_REFS, source="p7_r54_op08_packet_completeness_export_denylist_scan")
    _assert_common_operation_contract(
        data,
        schema_version=P7_R54_OPERATION_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION,
        policy_section=P7_R54_OP08_STEP_REF,
        operation_step_ref=P7_R54_OP08_STEP_REF,
        source="p7_r54_op08_packet_completeness_export_denylist_scan",
    )
    if data.get("op07_schema_version") != P7_R54_OPERATION_PACKET_GENERATION_LOCAL_OPERATION_SCHEMA_VERSION:
        raise ValueError("R54 OP08 OP07 schema reference changed")
    _assert_operation_current_refs(data, source="p7_r54_op08_packet_completeness_export_denylist_scan")
    if data.get("required_case_count") != P7_R51_REQUIRED_CASE_COUNT or data.get("operation_current_refs_are_actual_review_basis") is not True:
        raise ValueError("R54 OP08 basis or required case count changed")
    if data.get("packet_scan_status") not in P7_R54_OP08_ALLOWED_PACKET_SCAN_STATUS_REFS:
        raise ValueError("R54 OP08 packet scan status changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=60, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 OP08 open blockers must match execution blockers")
    for false_key in (
        "packet_scan_contains_packet_content", "packet_scan_contains_local_path", "packet_scan_contains_question_text",
        "body_full_packet_content_included", "body_full_packet_generated_here", "actual_body_full_packet_generated_here",
        "local_review_root_path_included", "local_packet_directory_path_included", "local_packet_exported",
        "body_full_packet_export_allowed", "body_full_packet_zip_inclusion_allowed", "reviewer_notes_export_allowed",
        "actual_review_evidence_complete", "disposal_verified",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 OP08 must keep {false_key}=False")
    if data.get("packet_scan_is_bodyfree_only") is not True:
        raise ValueError("R54 OP08 packet scan must be body-free only")
    if data.get("p5_actual_review_still_not_run") is not True:
        raise ValueError("R54 OP08 must keep P5 actual review not run")
    if data.get("rating_row_count") != 0 or data.get("question_observation_row_count") != 0:
        raise ValueError("R54 OP08 must not materialize rating/question rows")
    if data.get("human_review_completion_claim_blocked_here") is not True or data.get("p6_p8_release_promotion_blocked_here") is not True:
        raise ValueError("R54 OP08 must block human-review and promotion claims")
    if tuple(data.get("required_packet_field_refs") or ()) != P7_R54_OP08_REQUIRED_PACKET_FIELD_REFS:
        raise ValueError("R54 OP08 required packet field refs changed")
    if data.get("required_packet_field_ref_count") != len(P7_R54_OP08_REQUIRED_PACKET_FIELD_REFS):
        raise ValueError("R54 OP08 required packet field count changed")
    rows = [safe_mapping(row) for row in (data.get("packet_scan_rows") or [])]
    for row in rows:
        _assert_op08_packet_scan_row(row)
    expected_refs = [clean_identifier(item, max_length=180) for item in (data.get("expected_packet_ref_ids") or [])]
    declared_refs = [clean_identifier(item, max_length=180) for item in (data.get("declared_packet_ref_ids") or [])]
    scan_ready = data.get("packet_scan_status") == P7_R54_OP08_PACKET_SCAN_READY_STATUS_REF
    if scan_ready:
        if data.get("op07_local_operation_ready") is not True or data.get("op07_next_required_step") != P7_R54_OP08_STEP_REF:
            raise ValueError("R54 OP08 ready scan requires OP07 ready next step")
        if data.get("op07_local_operation_status") != P7_R54_OP07_LOCAL_OPERATION_READY_STATUS_REF:
            raise ValueError("R54 OP08 ready scan requires OP07 ready status")
        if data.get("expected_packet_ref_count") != P7_R51_REQUIRED_CASE_COUNT or len(expected_refs) != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 OP08 expected packet refs changed")
        if data.get("declared_packet_ref_count") != P7_R51_REQUIRED_CASE_COUNT or len(declared_refs) != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 OP08 declared packet refs changed")
        if data.get("declared_packet_ref_ids_unique") is not True or not _op05_unique_non_empty(declared_refs):
            raise ValueError("R54 OP08 declared packet refs must be unique")
        if data.get("packet_ref_ids_match_local_operation") is not True or declared_refs != expected_refs:
            raise ValueError("R54 OP08 packet refs must match OP07 local operation")
        if data.get("packet_scan_row_count") != P7_R51_REQUIRED_CASE_COUNT or len(rows) != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 OP08 scan row count changed")
        if data.get("total_case_count") != P7_R51_REQUIRED_CASE_COUNT or data.get("packet_present_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 OP08 packet presence counts changed")
        if data.get("required_fields_present_count") != P7_R51_REQUIRED_CASE_COUNT or data.get("packet_completeness_ready") is not True:
            raise ValueError("R54 OP08 completeness counts changed")
        if data.get("export_denylist_violation_refs") != [] or data.get("export_denylist_violation_count") != 0:
            raise ValueError("R54 OP08 ready scan must have no export-denylist violations")
        if data.get("body_full_packet_export_candidate_refs") != [] or data.get("body_full_packet_export_candidate_count") != 0:
            raise ValueError("R54 OP08 ready scan must have no body-full packet export candidates")
        for leak_key in ("body_full_packet_content_detected_in_export", "question_text_detected_in_export", "local_path_detected_in_export"):
            if data.get(leak_key) is not False:
                raise ValueError(f"R54 OP08 ready scan must keep {leak_key}=False")
        if data.get("packet_scan_ref") != P7_R54_OP08_PACKET_SCAN_REF or data.get("packet_scan_reason_refs") != [P7_R54_OP08_READY_REASON_REF]:
            raise ValueError("R54 OP08 ready scan ref/reason changed")
        if data.get("reviewer_instruction_rating_form_freeze_allowed_next") is not True:
            raise ValueError("R54 OP08 ready scan must allow OP09 next")
        if blockers:
            raise ValueError("R54 OP08 ready scan must not carry blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_OP08_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP08 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_OP08_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP08 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_OP09_STEP_REF:
            raise ValueError("R54 OP08 ready scan must point to R54-OP-09")
    else:
        if data.get("reviewer_instruction_rating_form_freeze_allowed_next") is not False:
            raise ValueError("R54 OP08 blocked scan must not allow OP09")
        if not blockers:
            raise ValueError("R54 OP08 blocked scan must carry execution blockers")
        expected_implemented = P7_R54_OP07_IMPLEMENTED_STEPS if data.get("op07_local_operation_ready") is True else P7_R54_OP06_IMPLEMENTED_STEPS
        expected_not_yet = P7_R54_OP07_NOT_YET_IMPLEMENTED_STEPS if data.get("op07_local_operation_ready") is True else P7_R54_OP06_NOT_YET_IMPLEMENTED_STEPS
        if tuple(data.get("implemented_steps") or ()) != expected_implemented:
            raise ValueError("R54 OP08 blocked scan must not advance implemented steps past the available OP07 boundary")
        if tuple(data.get("not_yet_implemented_steps") or ()) != expected_not_yet:
            raise ValueError("R54 OP08 blocked scan not-yet steps changed")
        if data.get("next_required_step") != P7_R54_OP08_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 OP08 blocked scan must point to packet scan repair")
    return True


def build_p7_r54_op09_reviewer_instruction_rating_form_freeze(
    *,
    packet_completeness_export_denylist_scan: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_operation_reviewer_instruction_rating_form_freeze",
) -> dict[str, Any]:
    """Build R54-OP-09 body-free reviewer instruction / rating form freeze."""
    op08 = safe_mapping(packet_completeness_export_denylist_scan) if packet_completeness_export_denylist_scan is not None else build_p7_r54_op08_packet_completeness_export_denylist_scan()
    assert_p7_r54_op08_packet_completeness_export_denylist_scan_contract(op08)
    scan_ready = op08.get("packet_scan_status") == P7_R54_OP08_PACKET_SCAN_READY_STATUS_REF
    form_ready = bool(scan_ready and op08.get("reviewer_instruction_rating_form_freeze_allowed_next") is True)
    execution_blockers = [] if form_ready else dedupe_identifiers(
        ["r54_op09_blocked_until_packet_scan_ready", *(op08.get("open_execution_blocker_ids") or [])],
        limit=60,
        max_length=180,
    )
    reason_refs = [P7_R54_OP09_READY_REASON_REF] if form_ready else dedupe_identifiers(
        [P7_R54_OP09_FORM_BLOCKED_STATUS_REF, *execution_blockers],
        limit=60,
        max_length=180,
    )
    material = {
        "schema_version": P7_R54_OPERATION_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_OPERATION_REENTRY_STEP,
        "scope": P7_R54_OPERATION_REENTRY_SCOPE,
        "policy_kind": P7_R54_OPERATION_REENTRY_POLICY_KIND,
        "policy_section": P7_R54_OP09_STEP_REF,
        "operation_step_ref": P7_R54_OP09_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_operation_reviewer_instruction_rating_form_freeze", max_length=220),
        "review_session_id": _safe_review_session_id(op08.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op08_schema_version": P7_R54_OPERATION_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION,
        "op08_material_ref": clean_identifier(op08.get("material_id"), default="p7_r54_operation_packet_completeness_export_denylist_scan", max_length=220),
        "op08_next_required_step": clean_identifier(op08.get("next_required_step"), default="", max_length=180),
        "op08_packet_scan_status": clean_identifier(op08.get("packet_scan_status"), default=P7_R54_OP08_PACKET_SCAN_BLOCKED_STATUS_REF, max_length=180),
        "op08_packet_scan_ready": scan_ready,
        "operation_current_refs": dict(P7_R54_OPERATION_CURRENT_REFS),
        "operation_current_ref_count": len(P7_R54_OPERATION_CURRENT_REFS),
        "actual_review_basis_ref": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "packet_scan_row_count": int(op08.get("packet_scan_row_count") or 0),
        "packet_present_count": int(op08.get("packet_present_count") or 0),
        "required_fields_present_count": int(op08.get("required_fields_present_count") or 0),
        "reviewer_instruction_status": P7_R54_OP09_FORM_READY_STATUS_REF if form_ready else P7_R54_OP09_FORM_BLOCKED_STATUS_REF,
        "reviewer_instruction_ref": P7_R54_OP09_REVIEWER_INSTRUCTION_REF if form_ready else "reviewer_instruction_not_frozen_until_packet_scan_ready",
        "reviewer_instruction_policy_ref": "selection_only_no_free_text_no_question_text_no_raw_body_copy",
        "rating_form_ref": P7_R54_OP09_RATING_FORM_REF if form_ready else "rating_form_not_frozen_until_packet_scan_ready",
        "rating_form_reason_refs": reason_refs,
        "execution_blocker_ids": execution_blockers,
        "open_execution_blocker_ids": execution_blockers,
        "rating_axis_refs": list(P7_R54_OP09_RATING_AXIS_REFS) if form_ready else [],
        "rating_axis_count": len(P7_R54_OP09_RATING_AXIS_REFS) if form_ready else 0,
        "rating_axis_target_thresholds": dict(P7_R54_OP09_RATING_AXIS_TARGET_THRESHOLDS) if form_ready else {},
        "score_option_refs": list(P7_R54_OP09_SCORE_OPTION_REFS) if form_ready else [],
        "verdict_option_refs": list(P7_R54_OP09_VERDICT_OPTION_REFS) if form_ready else [],
        "blocker_id_option_refs": list(P7_R54_OP09_BLOCKER_ID_OPTION_REFS) if form_ready else [],
        "question_need_primary_class_options": list(P7_R54_OP09_QUESTION_NEED_PRIMARY_CLASS_REFS) if form_ready else [],
        "ambiguity_kind_option_refs": list(P7_R54_OP09_AMBIGUITY_KIND_OPTION_REFS) if form_ready else [],
        "one_question_fit_option_refs": list(P7_R54_OP09_ONE_QUESTION_FIT_OPTION_REFS) if form_ready else [],
        "repair_required_option_refs": list(P7_R54_OP09_REPAIR_REQUIRED_OPTION_REFS) if form_ready else [],
        "plan_candidate_flag_refs": list(P7_R54_OP09_PLAN_CANDIDATE_FLAG_REFS) if form_ready else [],
        "selection_only_form": form_ready,
        "reviewer_free_text_field_present": False,
        "reviewer_free_text_export_allowed": False,
        "raw_body_copy_field_present": False,
        "question_text_field_present": False,
        "draft_question_text_field_present": False,
        "local_path_field_present": False,
        "body_hash_field_present": False,
        "packet_content_field_present": False,
        "rating_form_contains_question_text": False,
        "rating_form_contains_raw_body_copy": False,
        "rating_form_contains_local_path": False,
        "rating_form_contains_body_hash": False,
        "rating_form_contains_reviewer_free_text_export": False,
        "actual_human_review_operation_state_capture_allowed_next": form_ready,
        "reviewer_instruction_materialized_here": form_ready,
        "rating_form_materialized_here": form_ready,
        "actual_human_review_started_here": False,
        "actual_human_review_run_here": False,
        "p5_actual_review_still_not_run": True,
        "actual_review_evidence_complete": False,
        "rating_row_count": 0,
        "question_observation_row_count": 0,
        "disposal_verified": False,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_OP09_IMPLEMENTED_STEPS if form_ready else tuple(op08.get("implemented_steps") or ())),
        "not_yet_implemented_steps": list(P7_R54_OP09_NOT_YET_IMPLEMENTED_STEPS if form_ready else tuple(op08.get("not_yet_implemented_steps") or ())),
        "first_next_work_ref": P7_R54_OP_NEXT_WORK_AFTER_OP09_REF if form_ready else (P7_R54_OP_NEXT_WORK_AFTER_OP08_REF if scan_ready else P7_R54_OP_NEXT_WORK_AFTER_OP07_REF),
        "next_required_step": P7_R54_OP10_STEP_REF if form_ready else P7_R54_OP09_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_operation_no_touch_contract": _operation_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
    }
    assert_p7_r54_op09_reviewer_instruction_rating_form_freeze_contract(material)
    return material


def assert_p7_r54_op09_reviewer_instruction_rating_form_freeze_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_OPERATION_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_REQUIRED_FIELD_REFS, source="p7_r54_op09_reviewer_instruction_rating_form_freeze")
    _assert_common_operation_contract(
        data,
        schema_version=P7_R54_OPERATION_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION,
        policy_section=P7_R54_OP09_STEP_REF,
        operation_step_ref=P7_R54_OP09_STEP_REF,
        source="p7_r54_op09_reviewer_instruction_rating_form_freeze",
    )
    if data.get("op08_schema_version") != P7_R54_OPERATION_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION:
        raise ValueError("R54 OP09 OP08 schema reference changed")
    _assert_operation_current_refs(data, source="p7_r54_op09_reviewer_instruction_rating_form_freeze")
    if data.get("required_case_count") != P7_R51_REQUIRED_CASE_COUNT or data.get("operation_current_refs_are_actual_review_basis") is not True:
        raise ValueError("R54 OP09 basis or required case count changed")
    if data.get("reviewer_instruction_status") not in P7_R54_OP09_ALLOWED_FORM_STATUS_REFS:
        raise ValueError("R54 OP09 reviewer instruction status changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=60, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 OP09 open blockers must match execution blockers")
    for false_key in (
        "reviewer_free_text_field_present", "reviewer_free_text_export_allowed", "raw_body_copy_field_present",
        "question_text_field_present", "draft_question_text_field_present", "local_path_field_present",
        "body_hash_field_present", "packet_content_field_present", "rating_form_contains_question_text",
        "rating_form_contains_raw_body_copy", "rating_form_contains_local_path", "rating_form_contains_body_hash",
        "rating_form_contains_reviewer_free_text_export", "actual_human_review_started_here", "actual_human_review_run_here",
        "actual_review_evidence_complete", "disposal_verified",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 OP09 must keep {false_key}=False")
    if data.get("p5_actual_review_still_not_run") is not True:
        raise ValueError("R54 OP09 must keep P5 actual review not run")
    if data.get("rating_row_count") != 0 or data.get("question_observation_row_count") != 0:
        raise ValueError("R54 OP09 must not materialize rating/question rows")
    if data.get("human_review_completion_claim_blocked_here") is not True or data.get("p6_p8_release_promotion_blocked_here") is not True:
        raise ValueError("R54 OP09 must block human-review and promotion claims")
    form_ready = data.get("reviewer_instruction_status") == P7_R54_OP09_FORM_READY_STATUS_REF
    if form_ready:
        if data.get("op08_packet_scan_ready") is not True or data.get("op08_next_required_step") != P7_R54_OP09_STEP_REF:
            raise ValueError("R54 OP09 ready form requires OP08 ready next step")
        if data.get("op08_packet_scan_status") != P7_R54_OP08_PACKET_SCAN_READY_STATUS_REF:
            raise ValueError("R54 OP09 ready form requires OP08 ready status")
        if data.get("packet_scan_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 OP09 ready form requires 24 scan rows")
        if data.get("packet_present_count") != P7_R51_REQUIRED_CASE_COUNT or data.get("required_fields_present_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 OP09 ready form requires complete packet scan counts")
        if data.get("reviewer_instruction_ref") != P7_R54_OP09_REVIEWER_INSTRUCTION_REF:
            raise ValueError("R54 OP09 reviewer instruction ref changed")
        if data.get("rating_form_ref") != P7_R54_OP09_RATING_FORM_REF:
            raise ValueError("R54 OP09 rating form ref changed")
        if data.get("rating_form_reason_refs") != [P7_R54_OP09_READY_REASON_REF]:
            raise ValueError("R54 OP09 ready reason refs changed")
        if data.get("reviewer_instruction_policy_ref") != "selection_only_no_free_text_no_question_text_no_raw_body_copy":
            raise ValueError("R54 OP09 reviewer instruction policy changed")
        if data.get("rating_axis_refs") != list(P7_R54_OP09_RATING_AXIS_REFS):
            raise ValueError("R54 OP09 rating axis refs changed")
        if data.get("rating_axis_count") != len(P7_R54_OP09_RATING_AXIS_REFS):
            raise ValueError("R54 OP09 rating axis count changed")
        if data.get("rating_axis_target_thresholds") != P7_R54_OP09_RATING_AXIS_TARGET_THRESHOLDS:
            raise ValueError("R54 OP09 axis thresholds changed")
        if data.get("score_option_refs") != list(P7_R54_OP09_SCORE_OPTION_REFS):
            raise ValueError("R54 OP09 score options changed")
        if data.get("verdict_option_refs") != list(P7_R54_OP09_VERDICT_OPTION_REFS):
            raise ValueError("R54 OP09 verdict options changed")
        if data.get("blocker_id_option_refs") != list(P7_R54_OP09_BLOCKER_ID_OPTION_REFS):
            raise ValueError("R54 OP09 blocker options changed")
        if data.get("question_need_primary_class_options") != list(P7_R54_OP09_QUESTION_NEED_PRIMARY_CLASS_REFS):
            raise ValueError("R54 OP09 question observation class options changed")
        if data.get("ambiguity_kind_option_refs") != list(P7_R54_OP09_AMBIGUITY_KIND_OPTION_REFS):
            raise ValueError("R54 OP09 ambiguity options changed")
        if data.get("one_question_fit_option_refs") != list(P7_R54_OP09_ONE_QUESTION_FIT_OPTION_REFS):
            raise ValueError("R54 OP09 one-question-fit options changed")
        if data.get("repair_required_option_refs") != list(P7_R54_OP09_REPAIR_REQUIRED_OPTION_REFS):
            raise ValueError("R54 OP09 repair-required options changed")
        if data.get("plan_candidate_flag_refs") != list(P7_R54_OP09_PLAN_CANDIDATE_FLAG_REFS):
            raise ValueError("R54 OP09 plan candidate flag refs changed")
        for true_key in (
            "selection_only_form", "actual_human_review_operation_state_capture_allowed_next",
            "reviewer_instruction_materialized_here", "rating_form_materialized_here",
        ):
            if data.get(true_key) is not True:
                raise ValueError(f"R54 OP09 ready form must keep {true_key}=True")
        if blockers:
            raise ValueError("R54 OP09 ready form must not carry blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_OP09_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP09 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_OP09_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP09 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_OP10_STEP_REF:
            raise ValueError("R54 OP09 ready form must point to R54-OP-10")
    else:
        for key in (
            "selection_only_form", "actual_human_review_operation_state_capture_allowed_next",
            "reviewer_instruction_materialized_here", "rating_form_materialized_here",
        ):
            if data.get(key) is not False:
                raise ValueError("R54 OP09 blocked form must not materialize reviewer form")
        if data.get("rating_axis_refs") != [] or data.get("rating_axis_count") != 0:
            raise ValueError("R54 OP09 blocked form must not expose axes")
        if data.get("rating_axis_target_thresholds") != {} or data.get("score_option_refs") != [] or data.get("verdict_option_refs") != []:
            raise ValueError("R54 OP09 blocked form must not expose score/verdict options")
        if data.get("blocker_id_option_refs") != [] or data.get("question_need_primary_class_options") != []:
            raise ValueError("R54 OP09 blocked form must not expose reviewer selections")
        if not blockers:
            raise ValueError("R54 OP09 blocked form must carry execution blockers")
        expected_implemented = P7_R54_OP07_IMPLEMENTED_STEPS if int(data.get("packet_scan_row_count") or 0) else P7_R54_OP06_IMPLEMENTED_STEPS
        expected_not_yet = P7_R54_OP07_NOT_YET_IMPLEMENTED_STEPS if int(data.get("packet_scan_row_count") or 0) else P7_R54_OP06_NOT_YET_IMPLEMENTED_STEPS
        if tuple(data.get("implemented_steps") or ()) != expected_implemented:
            raise ValueError("R54 OP09 blocked form must not advance implemented steps past the available packet-scan boundary")
        if tuple(data.get("not_yet_implemented_steps") or ()) != expected_not_yet:
            raise ValueError("R54 OP09 blocked form not-yet steps changed")
        if data.get("next_required_step") != P7_R54_OP09_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 OP09 blocked form must point to packet scan repair")
    return True


def _op10_review_status(value: Any) -> str:
    status = clean_identifier(value, default=P7_R54_OP10_REVIEW_NOT_STARTED_STATUS_REF, max_length=120)
    return status if status in P7_R54_OP10_ALLOWED_REVIEW_OPERATION_STATUS_REFS else "invalid_review_operation_status_ref"


def build_p7_r54_op10_actual_human_review_operation_state_capture(
    *,
    reviewer_instruction_rating_form_freeze: Mapping[str, Any] | None = None,
    review_operation_status_ref: Any = P7_R54_OP10_REVIEW_NOT_STARTED_STATUS_REF,
    reviewer_assignment_ref: Any = "reviewer_assignment_not_started_bodyfree",
    reviewer_ref_ids: Sequence[Any] | None = None,
    review_completion_receipt_ref: Any = "review_completion_receipt_not_available_bodyfree",
    completed_packet_ref_ids: Sequence[Any] | None = None,
    completed_selection_row_refs: Sequence[Any] | None = None,
    material_id: Any = "p7_r54_operation_actual_human_review_operation_state_capture",
) -> dict[str, Any]:
    """Build R54-OP-10 body-free actual human review operation state capture.

    The helper captures a state supplied from a local-only human review operation;
    it does not run the review and it does not promote review evidence to complete.
    """
    op09 = safe_mapping(reviewer_instruction_rating_form_freeze) if reviewer_instruction_rating_form_freeze is not None else build_p7_r54_op09_reviewer_instruction_rating_form_freeze()
    assert_p7_r54_op09_reviewer_instruction_rating_form_freeze_contract(op09)
    form_ready = bool(
        op09.get("reviewer_instruction_status") == P7_R54_OP09_FORM_READY_STATUS_REF
        and op09.get("actual_human_review_operation_state_capture_allowed_next") is True
    )
    requested_status = _op10_review_status(review_operation_status_ref)
    reviewer_refs = dedupe_identifiers(reviewer_ref_ids or [], limit=8, max_length=120)
    packet_refs = dedupe_identifiers(completed_packet_ref_ids or [], limit=P7_R51_REQUIRED_CASE_COUNT + 1, max_length=180)
    selection_row_refs = dedupe_identifiers(completed_selection_row_refs or [], limit=P7_R51_REQUIRED_CASE_COUNT + 1, max_length=180)
    completion_receipt = clean_identifier(
        review_completion_receipt_ref,
        default="review_completion_receipt_not_available_bodyfree",
        max_length=220,
    )
    assignment_ref = clean_identifier(
        reviewer_assignment_ref,
        default="reviewer_assignment_not_started_bodyfree",
        max_length=220,
    )
    status_valid = requested_status in P7_R54_OP10_ALLOWED_REVIEW_OPERATION_STATUS_REFS
    completed_requested = requested_status == P7_R54_OP10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF
    active_state_requested = requested_status in (
        P7_R54_OP10_REVIEW_IN_PROGRESS_STATUS_REF,
        P7_R54_OP10_REVIEW_PAUSED_STATUS_REF,
        P7_R54_OP10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF,
    )
    completion_payload_ready = bool(
        completed_requested
        and completion_receipt != "review_completion_receipt_not_available_bodyfree"
        and reviewer_refs
        and len(packet_refs) == P7_R51_REQUIRED_CASE_COUNT
        and _op05_unique_non_empty(packet_refs)
        and len(selection_row_refs) == P7_R51_REQUIRED_CASE_COUNT
        and _op05_unique_non_empty(selection_row_refs)
    )
    blocker_seed: list[str] = []
    if not form_ready:
        blocker_seed.append("r54_op10_blocked_until_op09_selection_only_form_ready")
    if not status_valid:
        blocker_seed.append("invalid_review_operation_status_ref")
    if active_state_requested and not reviewer_refs:
        blocker_seed.append("reviewer_ref_required_for_active_or_completed_review_state")
    if completed_requested and completion_receipt == "review_completion_receipt_not_available_bodyfree":
        blocker_seed.append("review_completion_receipt_ref_required")
    if completed_requested and len(packet_refs) != P7_R51_REQUIRED_CASE_COUNT:
        blocker_seed.append("review_completed_packet_ref_count_must_be_24")
    if completed_requested and not _op05_unique_non_empty(packet_refs):
        blocker_seed.append("review_completed_packet_refs_must_be_unique")
    if completed_requested and len(selection_row_refs) != P7_R51_REQUIRED_CASE_COUNT:
        blocker_seed.append("review_completed_selection_row_ref_count_must_be_24")
    if completed_requested and not _op05_unique_non_empty(selection_row_refs):
        blocker_seed.append("review_completed_selection_row_refs_must_be_unique")
    execution_blockers = [] if form_ready and status_valid and (not completed_requested or completion_payload_ready) and (not active_state_requested or reviewer_refs) else dedupe_identifiers(
        [*blocker_seed, *(op09.get("open_execution_blocker_ids") or [])],
        limit=80,
        max_length=180,
    )
    state_capture_status = (
        P7_R54_OP10_REVIEW_STATE_CAPTURE_READY_STATUS_REF
        if form_ready and status_valid and not execution_blockers
        else P7_R54_OP10_REVIEW_STATE_CAPTURE_BLOCKED_STATUS_REF
    )
    reason_refs = [
        P7_R54_OP10_COMPLETION_READY_REASON_REF if completion_payload_ready else P7_R54_OP10_STATE_CAPTURE_READY_REASON_REF
    ] if state_capture_status == P7_R54_OP10_REVIEW_STATE_CAPTURE_READY_STATUS_REF else dedupe_identifiers(
        [state_capture_status, *execution_blockers],
        limit=80,
        max_length=180,
    )
    sanitized_allowed_next = bool(form_ready and status_valid and completion_payload_ready and not execution_blockers)
    material = {
        "schema_version": P7_R54_OPERATION_ACTUAL_HUMAN_REVIEW_OPERATION_STATE_CAPTURE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_OPERATION_REENTRY_STEP,
        "scope": P7_R54_OPERATION_REENTRY_SCOPE,
        "policy_kind": P7_R54_OPERATION_REENTRY_POLICY_KIND,
        "policy_section": P7_R54_OP10_STEP_REF,
        "operation_step_ref": P7_R54_OP10_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_operation_actual_human_review_operation_state_capture", max_length=220),
        "review_session_id": _safe_review_session_id(op09.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op09_schema_version": P7_R54_OPERATION_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION,
        "op09_material_ref": clean_identifier(op09.get("material_id"), default="p7_r54_operation_reviewer_instruction_rating_form_freeze", max_length=220),
        "op09_next_required_step": clean_identifier(op09.get("next_required_step"), default="", max_length=180),
        "op09_reviewer_instruction_status": clean_identifier(op09.get("reviewer_instruction_status"), default=P7_R54_OP09_FORM_BLOCKED_STATUS_REF, max_length=180),
        "op09_form_ready": form_ready,
        "operation_current_refs": dict(P7_R54_OPERATION_CURRENT_REFS),
        "operation_current_ref_count": len(P7_R54_OPERATION_CURRENT_REFS),
        "actual_review_basis_ref": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "state_capture_status": state_capture_status,
        "review_operation_status": requested_status if status_valid else P7_R54_OP10_REVIEW_NOT_STARTED_STATUS_REF,
        "review_operation_state_reason_refs": reason_refs,
        "execution_blocker_ids": execution_blockers,
        "open_execution_blocker_ids": execution_blockers,
        "reviewer_assignment_ref": assignment_ref if form_ready else "reviewer_assignment_blocked_until_form_ready_bodyfree",
        "reviewer_ref_ids": reviewer_refs if form_ready else [],
        "reviewer_ref_count": len(reviewer_refs) if form_ready else 0,
        "reviewer_identity_policy_ref": P7_R54_OP10_REVIEWER_IDENTITY_POLICY_REF,
        "reviewer_identity_personal_info_included": False,
        "reviewer_name_included": False,
        "reviewer_email_included": False,
        "reviewer_account_included": False,
        "review_started_state_declared": requested_status == P7_R54_OP10_REVIEW_IN_PROGRESS_STATUS_REF and form_ready,
        "review_paused_state_declared": requested_status == P7_R54_OP10_REVIEW_PAUSED_STATUS_REF and form_ready,
        "review_aborted_state_declared": requested_status == P7_R54_OP10_REVIEW_ABORTED_STATUS_REF and form_ready,
        "review_expired_state_declared": requested_status == P7_R54_OP10_REVIEW_EXPIRED_STATUS_REF and form_ready,
        "review_completed_state_declared": completed_requested and form_ready,
        "review_completion_receipt_ref": completion_receipt if completed_requested and form_ready else "review_completion_receipt_not_available_bodyfree",
        "review_completed_packet_ref_ids": packet_refs if completed_requested and form_ready else [],
        "review_completed_packet_ref_count": len(packet_refs) if completed_requested and form_ready else 0,
        "review_completed_packet_ref_ids_unique": _op05_unique_non_empty(packet_refs) if completed_requested and form_ready else False,
        "review_completed_selection_row_refs": selection_row_refs if completed_requested and form_ready else [],
        "review_completed_selection_row_count": len(selection_row_refs) if completed_requested and form_ready else 0,
        "review_completed_selection_row_refs_unique": _op05_unique_non_empty(selection_row_refs) if completed_requested and form_ready else False,
        "review_completed_selection_rows_expected_count": P7_R51_REQUIRED_CASE_COUNT if completed_requested and form_ready else 0,
        "review_completed_selections_captured_by_external_human_ref": (
            "external_human_review_selection_receipt_bodyfree"
            if completion_payload_ready
            else "external_human_review_selection_receipt_not_ready_bodyfree"
        ),
        "sanitized_review_result_capture_allowed_next": sanitized_allowed_next,
        "state_capture_is_bodyfree_only": True,
        "state_capture_contains_reviewer_free_text": False,
        "state_capture_contains_packet_content": False,
        "state_capture_contains_local_path": False,
        "state_capture_contains_question_text": False,
        "state_capture_contains_body_hash": False,
        "actual_human_review_started_here": False,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "actual_review_evidence_complete": False,
        "rating_row_count": 0,
        "question_observation_row_count": 0,
        "disposal_verified": False,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_OP10_IMPLEMENTED_STEPS if form_ready else tuple(op09.get("implemented_steps") or ())),
        "not_yet_implemented_steps": list(P7_R54_OP10_NOT_YET_IMPLEMENTED_STEPS if form_ready else tuple(op09.get("not_yet_implemented_steps") or ())),
        "first_next_work_ref": P7_R54_OP_NEXT_WORK_AFTER_OP10_REF if sanitized_allowed_next else (P7_R54_OP_NEXT_WORK_AFTER_OP09_REF if form_ready else P7_R54_OP_NEXT_WORK_AFTER_OP08_REF),
        "next_required_step": (
            P7_R54_OP11_STEP_REF
            if sanitized_allowed_next
            else (P7_R54_OP10_NOT_COMPLETED_NEXT_REQUIRED_STEP_REF if form_ready else P7_R54_OP10_BLOCKED_NEXT_REQUIRED_STEP_REF)
        ),
        "public_contract": public_contract_flags(),
        "r54_operation_no_touch_contract": _operation_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
    }
    assert_p7_r54_op10_actual_human_review_operation_state_capture_contract(material)
    return material


def assert_p7_r54_op10_actual_human_review_operation_state_capture_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(
        data,
        required=P7_R54_OPERATION_ACTUAL_HUMAN_REVIEW_OPERATION_STATE_CAPTURE_REQUIRED_FIELD_REFS,
        source="p7_r54_op10_actual_human_review_operation_state_capture",
    )
    _assert_common_operation_contract(
        data,
        schema_version=P7_R54_OPERATION_ACTUAL_HUMAN_REVIEW_OPERATION_STATE_CAPTURE_SCHEMA_VERSION,
        policy_section=P7_R54_OP10_STEP_REF,
        operation_step_ref=P7_R54_OP10_STEP_REF,
        source="p7_r54_op10_actual_human_review_operation_state_capture",
    )
    if data.get("op09_schema_version") != P7_R54_OPERATION_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION:
        raise ValueError("R54 OP10 OP09 schema reference changed")
    _assert_operation_current_refs(data, source="p7_r54_op10_actual_human_review_operation_state_capture")
    if data.get("required_case_count") != P7_R51_REQUIRED_CASE_COUNT:
        raise ValueError("R54 OP10 required case count changed")
    if data.get("review_operation_status") not in P7_R54_OP10_ALLOWED_REVIEW_OPERATION_STATUS_REFS:
        raise ValueError("R54 OP10 review operation status changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=80, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 OP10 open blockers must match execution blockers")
    for false_key in (
        "reviewer_identity_personal_info_included", "reviewer_name_included", "reviewer_email_included",
        "reviewer_account_included", "state_capture_contains_reviewer_free_text", "state_capture_contains_packet_content",
        "state_capture_contains_local_path", "state_capture_contains_question_text", "state_capture_contains_body_hash",
        "actual_human_review_started_here", "actual_human_review_run_here", "actual_manual_review_run_here",
        "actual_review_evidence_complete", "disposal_verified",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 OP10 must keep {false_key}=False")
    if data.get("state_capture_is_bodyfree_only") is not True:
        raise ValueError("R54 OP10 state capture must remain body-free only")
    if data.get("rating_row_count") != 0 or data.get("question_observation_row_count") != 0:
        raise ValueError("R54 OP10 must not materialize rating/question rows")
    if data.get("human_review_completion_claim_blocked_here") is not True or data.get("p6_p8_release_promotion_blocked_here") is not True:
        raise ValueError("R54 OP10 must block completion and promotion claims")
    form_ready = data.get("op09_form_ready") is True and data.get("op09_reviewer_instruction_status") == P7_R54_OP09_FORM_READY_STATUS_REF
    if form_ready:
        if data.get("op09_next_required_step") != P7_R54_OP10_STEP_REF:
            raise ValueError("R54 OP10 ready state capture requires OP09 next step")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_OP10_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP10 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_OP10_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP10 not-yet steps changed")
        if data.get("state_capture_status") == P7_R54_OP10_REVIEW_STATE_CAPTURE_READY_STATUS_REF:
            if blockers:
                raise ValueError("R54 OP10 ready state capture must not carry blockers")
            status = data.get("review_operation_status")
            if status == P7_R54_OP10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF:
                if data.get("sanitized_review_result_capture_allowed_next") is not True:
                    raise ValueError("R54 OP10 completed state must allow sanitized capture next")
                if data.get("review_completed_packet_ref_count") != P7_R51_REQUIRED_CASE_COUNT:
                    raise ValueError("R54 OP10 completed packet count must be 24")
                if data.get("review_completed_selection_row_count") != P7_R51_REQUIRED_CASE_COUNT:
                    raise ValueError("R54 OP10 completed selection row count must be 24")
                if data.get("review_completed_packet_ref_ids_unique") is not True or data.get("review_completed_selection_row_refs_unique") is not True:
                    raise ValueError("R54 OP10 completed refs must be unique")
                if data.get("reviewer_ref_count", 0) < 1:
                    raise ValueError("R54 OP10 completed state requires reviewer refs")
                if data.get("next_required_step") != P7_R54_OP11_STEP_REF:
                    raise ValueError("R54 OP10 completed state must point to OP11")
            else:
                if data.get("sanitized_review_result_capture_allowed_next") is not False:
                    raise ValueError("R54 OP10 non-completed state must not allow sanitized capture")
                if data.get("next_required_step") != P7_R54_OP10_NOT_COMPLETED_NEXT_REQUIRED_STEP_REF:
                    raise ValueError("R54 OP10 non-completed state must point to continue/retry")
        else:
            if not blockers:
                raise ValueError("R54 OP10 blocked state capture must carry blockers")
            if data.get("sanitized_review_result_capture_allowed_next") is not False:
                raise ValueError("R54 OP10 blocked state must not allow sanitized capture")
    else:
        if data.get("state_capture_status") != P7_R54_OP10_REVIEW_STATE_CAPTURE_BLOCKED_STATUS_REF:
            raise ValueError("R54 OP10 blocked by form must use blocked state")
        if data.get("sanitized_review_result_capture_allowed_next") is not False:
            raise ValueError("R54 OP10 blocked by form must not allow sanitized capture")
        if data.get("reviewer_ref_ids") != [] or data.get("reviewer_ref_count") != 0:
            raise ValueError("R54 OP10 blocked by form must not expose reviewer refs")
        if tuple(data.get("implemented_steps") or ()) != tuple(data.get("implemented_steps") or ()):  # structural no-op for clarity
            raise ValueError("R54 OP10 unreachable implemented-step guard")
        if data.get("next_required_step") != P7_R54_OP10_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 OP10 blocked by form must point to OP09 repair")
        if not blockers:
            raise ValueError("R54 OP10 blocked by form must carry blockers")
    return True


def _op11_plan_candidate_flags(value: Any) -> dict[str, bool]:
    mapping = safe_mapping(value)
    return {key: bool(mapping.get(key, False)) for key in P7_R54_OP09_PLAN_CANDIDATE_FLAG_REFS}


def _op11_axis_scores(value: Any) -> dict[str, float]:
    mapping = safe_mapping(value)
    scores: dict[str, float] = {}
    for axis in P7_R54_OP09_RATING_AXIS_REFS:
        raw = mapping.get(axis)
        if isinstance(raw, bool):
            continue
        try:
            score = float(raw)
        except (TypeError, ValueError):
            continue
        scores[axis] = score
    return scores


def _op11_normalized_sanitized_review_rows(rows: Sequence[Any], *, review_session_id: str) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        source = safe_mapping(row)
        assert_p7_no_body_payload_or_contract_mutation(source, source="p7_r54_op11_input_selection_row")
        normalized.append({
            "schema_version": P7_R54_OPERATION_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION,
            "review_result_row_ref": clean_identifier(source.get("review_result_row_ref"), default=f"r54op11-sanitized-review-row-{index:03d}", max_length=180),
            "review_session_id": review_session_id,
            "packet_ref_id": clean_identifier(source.get("packet_ref_id"), max_length=180),
            "blind_case_id": clean_identifier(source.get("blind_case_id"), max_length=180),
            "case_ref_id": clean_identifier(source.get("case_ref_id"), max_length=180),
            "family": clean_identifier(source.get("family"), max_length=180),
            "case_role": clean_identifier(source.get("case_role"), max_length=180),
            "reviewer_ref": clean_identifier(source.get("reviewer_ref"), max_length=120),
            "reviewed_at_ref": clean_identifier(source.get("reviewed_at_ref"), default="coarse_reviewed_at_ref_20260625", max_length=160),
            "axis_scores": _op11_axis_scores(source.get("axis_scores")),
            "axis_score_count": len(_op11_axis_scores(source.get("axis_scores"))),
            "verdict": clean_identifier(source.get("verdict"), max_length=80),
            "sanitized_reason_ids": dedupe_identifiers(source.get("sanitized_reason_ids") or [], limit=20, max_length=160),
            "blocker_ids": dedupe_identifiers(source.get("blocker_ids") or [], limit=20, max_length=160),
            "question_need_primary_class": clean_identifier(source.get("question_need_primary_class"), max_length=160),
            "ambiguity_kind_refs": dedupe_identifiers(source.get("ambiguity_kind_refs") or [], limit=20, max_length=160),
            "one_question_fit_ref": clean_identifier(source.get("one_question_fit_ref"), max_length=160),
            "repair_required_refs": dedupe_identifiers(source.get("repair_required_refs") or [], limit=20, max_length=160),
            "plan_candidate_flags": _op11_plan_candidate_flags(source.get("plan_candidate_flags")),
            "selection_only_row": True,
            "reviewer_free_text_included": False,
            "raw_body_included": False,
            "comment_text_included": False,
            "question_text_included": False,
            "draft_question_text_included": False,
            "local_path_included": False,
            "body_hash_included": False,
            "packet_content_included": False,
            "body_removed": True,
            "body_free": True,
        })
    return normalized


def _assert_p7_r54_op11_sanitized_review_result_row(row: Mapping[str, Any], *, reviewer_refs: Sequence[str]) -> None:
    data = safe_mapping(row)
    _assert_required_fields(
        data,
        required=P7_R54_OPERATION_SANITIZED_REVIEW_RESULT_ROW_REQUIRED_FIELD_REFS,
        source="p7_r54_op11_sanitized_review_result_row",
    )
    if data.get("schema_version") != P7_R54_OPERATION_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION:
        raise ValueError("R54 OP11 row schema version changed")
    if data.get("selection_only_row") is not True or data.get("body_free") is not True:
        raise ValueError("R54 OP11 row must remain a body-free selection row")
    for field in ("packet_ref_id", "blind_case_id", "case_ref_id", "family", "case_role", "reviewer_ref", "reviewed_at_ref"):
        if not clean_identifier(data.get(field), max_length=180):
            raise ValueError(f"R54 OP11 row missing {field}")
    scores = safe_mapping(data.get("axis_scores"))
    if tuple(scores.keys()) != P7_R54_OP09_RATING_AXIS_REFS:
        raise ValueError("R54 OP11 row axis score keys changed")
    if data.get("axis_score_count") != len(P7_R54_OP09_RATING_AXIS_REFS):
        raise ValueError("R54 OP11 row axis score count changed")
    for axis in P7_R54_OP09_RATING_AXIS_REFS:
        score = scores.get(axis)
        if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0.0 <= float(score) <= 1.0:
            raise ValueError("R54 OP11 row axis score out of range")
    if data.get("verdict") not in P7_R54_OP09_VERDICT_OPTION_REFS:
        raise ValueError("R54 OP11 row verdict option changed")
    if data.get("reviewer_ref") not in reviewer_refs:
        raise ValueError("R54 OP11 row reviewer ref must be one of OP10 reviewer refs")
    if not set(data.get("blocker_ids") or []).issubset(set(P7_R54_OP09_BLOCKER_ID_OPTION_REFS)):
        raise ValueError("R54 OP11 row blocker id outside frozen form options")
    if data.get("question_need_primary_class") not in P7_R54_OP09_QUESTION_NEED_PRIMARY_CLASS_REFS:
        raise ValueError("R54 OP11 row question need class outside frozen options")
    if not set(data.get("ambiguity_kind_refs") or []).issubset(set(P7_R54_OP09_AMBIGUITY_KIND_OPTION_REFS)):
        raise ValueError("R54 OP11 row ambiguity refs outside frozen options")
    if data.get("one_question_fit_ref") not in P7_R54_OP09_ONE_QUESTION_FIT_OPTION_REFS:
        raise ValueError("R54 OP11 row one-question-fit option changed")
    repair_refs = data.get("repair_required_refs") or []
    if not repair_refs or not set(repair_refs).issubset(set(P7_R54_OP09_REPAIR_REQUIRED_OPTION_REFS)):
        raise ValueError("R54 OP11 row repair refs outside frozen options")
    flags = safe_mapping(data.get("plan_candidate_flags"))
    if tuple(flags.keys()) != P7_R54_OP09_PLAN_CANDIDATE_FLAG_REFS:
        raise ValueError("R54 OP11 row plan candidate flag keys changed")
    if flags.get("p8_implementation_spec_finalized_here") is not False:
        raise ValueError("R54 OP11 row must not finalize P8 implementation spec")
    for false_key in (
        "reviewer_free_text_included", "raw_body_included", "comment_text_included", "question_text_included",
        "draft_question_text_included", "local_path_included", "body_hash_included", "packet_content_included",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 OP11 row must keep {false_key}=False")
    if data.get("body_removed") is not True:
        raise ValueError("R54 OP11 row must mark body removed from sanitized result row")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_op11_sanitized_review_result_row")


def _op11_sanitized_rows_ready(rows: Sequence[Mapping[str, Any]], *, op10: Mapping[str, Any]) -> tuple[bool, list[str]]:
    blockers: list[str] = []
    expected_packets = [clean_identifier(item, max_length=180) for item in (op10.get("review_completed_packet_ref_ids") or [])]
    expected_row_refs = [clean_identifier(item, max_length=180) for item in (op10.get("review_completed_selection_row_refs") or [])]
    reviewer_refs = [clean_identifier(item, max_length=120) for item in (op10.get("reviewer_ref_ids") or [])]
    if len(rows) != P7_R51_REQUIRED_CASE_COUNT:
        blockers.append("sanitized_review_result_row_count_must_be_24")
    packet_refs = _op05_case_refs(rows, "packet_ref_id")
    row_refs = _op05_case_refs(rows, "review_result_row_ref")
    case_refs = _op05_case_refs(rows, "case_ref_id")
    blind_ids = _op05_case_refs(rows, "blind_case_id")
    if packet_refs != expected_packets:
        blockers.append("sanitized_review_packet_refs_must_match_op10_completion_refs")
    if row_refs != expected_row_refs:
        blockers.append("sanitized_review_row_refs_must_match_op10_completion_refs")
    if not _op05_unique_non_empty(packet_refs):
        blockers.append("sanitized_review_packet_refs_must_be_unique")
    if not _op05_unique_non_empty(row_refs):
        blockers.append("sanitized_review_row_refs_must_be_unique")
    if not _op05_unique_non_empty(case_refs):
        blockers.append("sanitized_review_case_refs_must_be_unique")
    if not _op05_unique_non_empty(blind_ids):
        blockers.append("sanitized_review_blind_case_ids_must_be_unique")
    try:
        for row in rows:
            _assert_p7_r54_op11_sanitized_review_result_row(row, reviewer_refs=reviewer_refs)
    except ValueError as exc:
        blockers.append(clean_identifier(str(exc), default="sanitized_review_result_row_contract_failed", max_length=180))
    return not blockers, dedupe_identifiers(blockers, limit=80, max_length=180)


def build_p7_r54_op11_sanitized_review_result_capture(
    *,
    actual_human_review_operation_state_capture: Mapping[str, Any] | None = None,
    reviewer_selection_rows: Sequence[Any] | None = None,
    material_id: Any = "p7_r54_operation_sanitized_review_result_capture",
) -> dict[str, Any]:
    """Build R54-OP-11 body-free sanitized review result capture."""
    op10 = safe_mapping(actual_human_review_operation_state_capture) if actual_human_review_operation_state_capture is not None else build_p7_r54_op10_actual_human_review_operation_state_capture()
    assert_p7_r54_op10_actual_human_review_operation_state_capture_contract(op10)
    op10_allows_next = bool(
        op10.get("review_operation_status") == P7_R54_OP10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF
        and op10.get("sanitized_review_result_capture_allowed_next") is True
        and op10.get("next_required_step") == P7_R54_OP11_STEP_REF
    )
    review_session_id = _safe_review_session_id(op10.get("review_session_id"))
    normalized_input_rows = _op11_normalized_sanitized_review_rows(reviewer_selection_rows or [], review_session_id=review_session_id) if op10_allows_next else []
    rows_ready, row_blockers = _op11_sanitized_rows_ready(normalized_input_rows, op10=op10) if op10_allows_next else (False, ["r54_op11_blocked_until_op10_completed_state_ready"])
    capture_ready = bool(op10_allows_next and rows_ready)
    rows = normalized_input_rows if capture_ready else []
    packet_refs = _op05_case_refs(rows, "packet_ref_id")
    case_refs = _op05_case_refs(rows, "case_ref_id")
    blind_ids = _op05_case_refs(rows, "blind_case_id")
    reviewer_refs = _op05_case_refs(rows, "reviewer_ref")
    family_counts = _op05_count_by(rows, "family") if capture_ready else {}
    role_counts = _op05_count_by(rows, "case_role") if capture_ready else {}
    execution_blockers = [] if capture_ready else dedupe_identifiers([*row_blockers, *(op10.get("open_execution_blocker_ids") or [])], limit=100, max_length=180)
    reason_refs = [P7_R54_OP11_READY_REASON_REF] if capture_ready else dedupe_identifiers([P7_R54_OP11_SANITIZED_CAPTURE_BLOCKED_STATUS_REF, *execution_blockers], limit=100, max_length=180)
    material = {
        "schema_version": P7_R54_OPERATION_SANITIZED_REVIEW_RESULT_CAPTURE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_OPERATION_REENTRY_STEP,
        "scope": P7_R54_OPERATION_REENTRY_SCOPE,
        "policy_kind": P7_R54_OPERATION_REENTRY_POLICY_KIND,
        "policy_section": P7_R54_OP11_STEP_REF,
        "operation_step_ref": P7_R54_OP11_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_operation_sanitized_review_result_capture", max_length=220),
        "review_session_id": review_session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op10_schema_version": P7_R54_OPERATION_ACTUAL_HUMAN_REVIEW_OPERATION_STATE_CAPTURE_SCHEMA_VERSION,
        "op10_material_ref": clean_identifier(op10.get("material_id"), default="p7_r54_operation_actual_human_review_operation_state_capture", max_length=220),
        "op10_next_required_step": clean_identifier(op10.get("next_required_step"), default="", max_length=180),
        "op10_review_operation_status": clean_identifier(op10.get("review_operation_status"), default=P7_R54_OP10_REVIEW_NOT_STARTED_STATUS_REF, max_length=180),
        "op10_sanitized_capture_allowed_next": op10_allows_next,
        "op10_completed_packet_ref_count": int(op10.get("review_completed_packet_ref_count") or 0),
        "op10_completed_selection_row_count": int(op10.get("review_completed_selection_row_count") or 0),
        "operation_current_refs": dict(P7_R54_OPERATION_CURRENT_REFS),
        "operation_current_ref_count": len(P7_R54_OPERATION_CURRENT_REFS),
        "actual_review_basis_ref": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "sanitized_review_result_capture_status": P7_R54_OP11_SANITIZED_CAPTURE_READY_STATUS_REF if capture_ready else P7_R54_OP11_SANITIZED_CAPTURE_BLOCKED_STATUS_REF,
        "sanitized_review_result_capture_ref": P7_R54_OP11_SANITIZED_REVIEW_RESULT_CAPTURE_REF if capture_ready else "sanitized_review_result_capture_not_ready_bodyfree",
        "sanitized_review_result_reason_refs": reason_refs,
        "execution_blocker_ids": execution_blockers,
        "open_execution_blocker_ids": execution_blockers,
        "expected_packet_ref_ids": list(op10.get("review_completed_packet_ref_ids") or []) if op10_allows_next else [],
        "expected_packet_ref_count": int(op10.get("review_completed_packet_ref_count") or 0) if op10_allows_next else 0,
        "expected_selection_row_refs": list(op10.get("review_completed_selection_row_refs") or []) if op10_allows_next else [],
        "expected_selection_row_ref_count": int(op10.get("review_completed_selection_row_count") or 0) if op10_allows_next else 0,
        "sanitized_review_result_rows": rows,
        "sanitized_review_result_row_count": len(rows),
        "reviewed_case_count": len(rows),
        "packet_ref_ids": packet_refs,
        "packet_ref_count": len(packet_refs),
        "packet_ref_ids_unique": _op05_unique_non_empty(packet_refs) if capture_ready else False,
        "case_ref_ids": case_refs,
        "case_ref_count": len(case_refs),
        "case_ref_ids_unique": _op05_unique_non_empty(case_refs) if capture_ready else False,
        "blind_case_ids": blind_ids,
        "blind_case_id_count": len(blind_ids),
        "blind_case_ids_unique": _op05_unique_non_empty(blind_ids) if capture_ready else False,
        "reviewer_ref_ids": dedupe_identifiers(reviewer_refs, limit=8, max_length=120),
        "reviewer_ref_count": len(dedupe_identifiers(reviewer_refs, limit=8, max_length=120)),
        "family_case_counts": family_counts,
        "case_role_counts": role_counts,
        "selection_rows_are_bodyfree_only": capture_ready,
        "sanitized_rows_contain_reviewer_free_text": False,
        "sanitized_rows_contain_raw_body": False,
        "sanitized_rows_contain_comment_text": False,
        "sanitized_rows_contain_question_text": False,
        "sanitized_rows_contain_local_path": False,
        "sanitized_rows_contain_body_hash": False,
        "sanitized_rows_contain_packet_content": False,
        "rating_row_normalization_allowed_next": capture_ready,
        "sanitized_review_result_rows_materialized_here": capture_ready,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_review_evidence_complete": False,
        "rating_row_count": 0,
        "question_observation_row_count": 0,
        "disposal_verified": False,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_OP11_IMPLEMENTED_STEPS if capture_ready else tuple(op10.get("implemented_steps") or ())),
        "not_yet_implemented_steps": list(P7_R54_OP11_NOT_YET_IMPLEMENTED_STEPS if capture_ready else tuple(op10.get("not_yet_implemented_steps") or ())),
        "first_next_work_ref": P7_R54_OP_NEXT_WORK_AFTER_OP11_REF if capture_ready else P7_R54_OP_NEXT_WORK_AFTER_OP10_REF,
        "next_required_step": P7_R54_OP12_STEP_REF if capture_ready else P7_R54_OP11_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_operation_no_touch_contract": _operation_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
    }
    assert_p7_r54_op11_sanitized_review_result_capture_contract(material)
    return material


def assert_p7_r54_op11_sanitized_review_result_capture_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(
        data,
        required=P7_R54_OPERATION_SANITIZED_REVIEW_RESULT_CAPTURE_REQUIRED_FIELD_REFS,
        source="p7_r54_op11_sanitized_review_result_capture",
    )
    _assert_common_operation_contract(
        data,
        schema_version=P7_R54_OPERATION_SANITIZED_REVIEW_RESULT_CAPTURE_SCHEMA_VERSION,
        policy_section=P7_R54_OP11_STEP_REF,
        operation_step_ref=P7_R54_OP11_STEP_REF,
        source="p7_r54_op11_sanitized_review_result_capture",
    )
    if data.get("op10_schema_version") != P7_R54_OPERATION_ACTUAL_HUMAN_REVIEW_OPERATION_STATE_CAPTURE_SCHEMA_VERSION:
        raise ValueError("R54 OP11 OP10 schema reference changed")
    _assert_operation_current_refs(data, source="p7_r54_op11_sanitized_review_result_capture")
    if data.get("required_case_count") != P7_R51_REQUIRED_CASE_COUNT:
        raise ValueError("R54 OP11 required case count changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=100, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 OP11 open blockers must match execution blockers")
    for false_key in (
        "sanitized_rows_contain_reviewer_free_text", "sanitized_rows_contain_raw_body", "sanitized_rows_contain_comment_text",
        "sanitized_rows_contain_question_text", "sanitized_rows_contain_local_path", "sanitized_rows_contain_body_hash",
        "sanitized_rows_contain_packet_content", "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here", "actual_review_evidence_complete", "disposal_verified",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 OP11 must keep {false_key}=False")
    if data.get("rating_row_count") != 0 or data.get("question_observation_row_count") != 0:
        raise ValueError("R54 OP11 must not materialize normalized rating/question rows")
    if data.get("human_review_completion_claim_blocked_here") is not True or data.get("p6_p8_release_promotion_blocked_here") is not True:
        raise ValueError("R54 OP11 must block completion and promotion claims")
    capture_ready = data.get("sanitized_review_result_capture_status") == P7_R54_OP11_SANITIZED_CAPTURE_READY_STATUS_REF
    if capture_ready:
        if data.get("op10_review_operation_status") != P7_R54_OP10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF:
            raise ValueError("R54 OP11 ready capture requires OP10 completed status")
        if data.get("op10_sanitized_capture_allowed_next") is not True or data.get("op10_next_required_step") != P7_R54_OP11_STEP_REF:
            raise ValueError("R54 OP11 ready capture requires OP10 next allowance")
        if blockers:
            raise ValueError("R54 OP11 ready capture must not carry blockers")
        if data.get("sanitized_review_result_capture_ref") != P7_R54_OP11_SANITIZED_REVIEW_RESULT_CAPTURE_REF:
            raise ValueError("R54 OP11 capture ref changed")
        if data.get("sanitized_review_result_reason_refs") != [P7_R54_OP11_READY_REASON_REF]:
            raise ValueError("R54 OP11 ready reason refs changed")
        if data.get("sanitized_review_result_row_count") != P7_R51_REQUIRED_CASE_COUNT or data.get("reviewed_case_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 OP11 ready capture must contain 24 sanitized rows")
        if data.get("packet_ref_count") != P7_R51_REQUIRED_CASE_COUNT or data.get("case_ref_count") != P7_R51_REQUIRED_CASE_COUNT or data.get("blind_case_id_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 OP11 ready capture counts changed")
        if data.get("packet_ref_ids") != data.get("expected_packet_ref_ids"):
            raise ValueError("R54 OP11 packet refs must match OP10 completion refs")
        row_refs = _op05_case_refs([safe_mapping(row) for row in (data.get("sanitized_review_result_rows") or [])], "review_result_row_ref")
        if row_refs != list(data.get("expected_selection_row_refs") or []):
            raise ValueError("R54 OP11 row refs must match OP10 completion refs")
        if data.get("packet_ref_ids_unique") is not True or data.get("case_ref_ids_unique") is not True or data.get("blind_case_ids_unique") is not True:
            raise ValueError("R54 OP11 ready capture must keep unique refs")
        if data.get("selection_rows_are_bodyfree_only") is not True or data.get("rating_row_normalization_allowed_next") is not True:
            raise ValueError("R54 OP11 ready capture must allow rating normalization next")
        if data.get("sanitized_review_result_rows_materialized_here") is not True:
            raise ValueError("R54 OP11 ready capture must materialize sanitized rows")
        reviewer_refs = [clean_identifier(item, max_length=120) for item in (data.get("reviewer_ref_ids") or [])]
        for row in data.get("sanitized_review_result_rows") or []:
            _assert_p7_r54_op11_sanitized_review_result_row(safe_mapping(row), reviewer_refs=reviewer_refs)
        if tuple(data.get("implemented_steps") or ()) != P7_R54_OP11_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP11 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_OP11_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP11 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_OP12_STEP_REF:
            raise ValueError("R54 OP11 ready capture must point to OP12")
    else:
        if data.get("sanitized_review_result_capture_status") != P7_R54_OP11_SANITIZED_CAPTURE_BLOCKED_STATUS_REF:
            raise ValueError("R54 OP11 blocked capture status changed")
        if data.get("sanitized_review_result_rows") != [] or data.get("sanitized_review_result_row_count") != 0:
            raise ValueError("R54 OP11 blocked capture must not materialize sanitized rows")
        if data.get("selection_rows_are_bodyfree_only") is not False or data.get("rating_row_normalization_allowed_next") is not False:
            raise ValueError("R54 OP11 blocked capture must not allow rating normalization")
        if data.get("sanitized_review_result_rows_materialized_here") is not False:
            raise ValueError("R54 OP11 blocked capture must not materialize sanitized rows")
        if not blockers:
            raise ValueError("R54 OP11 blocked capture must carry blockers")
        if data.get("next_required_step") != P7_R54_OP11_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 OP11 blocked capture must point to repair")
    return True


def _op12_false_flag_refs() -> tuple[str, ...]:
    return tuple(key for key in P7_R54_OPERATION_FALSE_FLAG_REFS if key != "actual_rating_rows_materialized_here")


def _op13_false_flag_refs() -> tuple[str, ...]:
    return tuple(
        key
        for key in P7_R54_OPERATION_FALSE_FLAG_REFS
        if key not in {"actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here"}
    )


def _op12_axis_average(scores: Mapping[str, Any]) -> float:
    numeric_scores = [float(safe_mapping(scores).get(axis, 0.0)) for axis in P7_R54_OP09_RATING_AXIS_REFS]
    return round(sum(numeric_scores) / len(P7_R54_OP09_RATING_AXIS_REFS), 4)


def _op12_axis_score_extreme(scores: Mapping[str, Any], *, kind: str) -> float:
    numeric_scores = [float(safe_mapping(scores).get(axis, 0.0)) for axis in P7_R54_OP09_RATING_AXIS_REFS]
    return min(numeric_scores) if kind == "min" else max(numeric_scores)


def _op12_below_target_axis_refs(scores: Mapping[str, Any]) -> list[str]:
    safe_scores = safe_mapping(scores)
    return [
        axis
        for axis in P7_R54_OP09_RATING_AXIS_REFS
        if float(safe_scores.get(axis, 0.0)) < float(P7_R54_OP09_RATING_AXIS_TARGET_THRESHOLDS[axis])
    ]


def _op12_verdict_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = {verdict: 0 for verdict in P7_R54_OP09_VERDICT_OPTION_REFS}
    for row in rows:
        verdict = clean_identifier(safe_mapping(row).get("verdict"), max_length=80)
        if verdict in counts:
            counts[verdict] += 1
    return counts


def _op12_axis_score_averages(rows: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    if not rows:
        return {axis: 0.0 for axis in P7_R54_OP09_RATING_AXIS_REFS}
    averages: dict[str, float] = {}
    for axis in P7_R54_OP09_RATING_AXIS_REFS:
        total = sum(float(safe_mapping(safe_mapping(row).get("axis_scores")).get(axis, 0.0)) for row in rows)
        averages[axis] = round(total / len(rows), 4)
    return averages


def _build_p7_r54_op12_rating_row_from_sanitized_row(row: Mapping[str, Any]) -> dict[str, Any]:
    source = safe_mapping(row)
    _assert_p7_r54_op11_sanitized_review_result_row(source, reviewer_refs=[clean_identifier(source.get("reviewer_ref"), max_length=120)])
    scores = safe_mapping(source.get("axis_scores"))
    below_target_axis_refs = _op12_below_target_axis_refs(scores)
    readfeel_blocker_ids = dedupe_identifiers(source.get("blocker_ids") or [], limit=20, max_length=160)
    execution_blocker_ids: list[str] = []
    verdict = clean_identifier(source.get("verdict"), max_length=80)
    sanitized_reason_ids = dedupe_identifiers(source.get("sanitized_reason_ids") or [], limit=20, max_length=160)
    rating_row = {
        "schema_version": P7_R54_OPERATION_RATING_ROW_SCHEMA_VERSION,
        "rating_row_ref": f"r54op12-rating-row-{clean_identifier(source.get('review_result_row_ref'), default='review-row', max_length=140)}",
        "review_result_row_ref": clean_identifier(source.get("review_result_row_ref"), max_length=180),
        "review_session_id": _safe_review_session_id(source.get("review_session_id")),
        "packet_ref_id": clean_identifier(source.get("packet_ref_id"), max_length=180),
        "blind_case_id": clean_identifier(source.get("blind_case_id"), max_length=180),
        "case_ref_id": clean_identifier(source.get("case_ref_id"), max_length=180),
        "family": clean_identifier(source.get("family"), max_length=180),
        "case_role": clean_identifier(source.get("case_role"), max_length=180),
        "reviewer_ref": clean_identifier(source.get("reviewer_ref"), max_length=120),
        "reviewed_at_ref": clean_identifier(source.get("reviewed_at_ref"), default="coarse_reviewed_at_ref_20260625", max_length=160),
        "axis_scores": {axis: float(scores.get(axis)) for axis in P7_R54_OP09_RATING_AXIS_REFS},
        "axis_score_count": len(P7_R54_OP09_RATING_AXIS_REFS),
        "axis_score_average": _op12_axis_average(scores),
        "axis_score_min": _op12_axis_score_extreme(scores, kind="min"),
        "axis_score_max": _op12_axis_score_extreme(scores, kind="max"),
        "target_thresholds": dict(P7_R54_OP09_RATING_AXIS_TARGET_THRESHOLDS),
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
        "rating_source_ref": P7_R54_OP12_RATING_ROW_SOURCE_REF,
        "verdict_blocker_consistency_ref": P7_R54_OP12_VERDICT_BLOCKER_CONSISTENT_REF,
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
    assert_p7_r54_op12_rating_row_bodyfree_contract(rating_row)
    return rating_row


def assert_p7_r54_op12_rating_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(
        data,
        required=P7_R54_OPERATION_RATING_ROW_REQUIRED_FIELD_REFS,
        source="p7_r54_op12_rating_row",
    )
    if data.get("schema_version") != P7_R54_OPERATION_RATING_ROW_SCHEMA_VERSION:
        raise ValueError("R54 OP12 rating row schema version changed")
    if data.get("rating_row_is_bodyfree") is not True or data.get("body_free") is not True:
        raise ValueError("R54 OP12 rating row must be body-free")
    scores = safe_mapping(data.get("axis_scores"))
    if tuple(scores.keys()) != P7_R54_OP09_RATING_AXIS_REFS:
        raise ValueError("R54 OP12 rating row axis keys changed")
    if data.get("axis_score_count") != len(P7_R54_OP09_RATING_AXIS_REFS):
        raise ValueError("R54 OP12 rating row axis count changed")
    for axis in P7_R54_OP09_RATING_AXIS_REFS:
        score = scores.get(axis)
        if not isinstance(score, (int, float)) or isinstance(score, bool) or not P7_R54_OP12_RATING_SCORE_MIN <= float(score) <= P7_R54_OP12_RATING_SCORE_MAX:
            raise ValueError("R54 OP12 rating score out of range")
    if safe_mapping(data.get("target_thresholds")) != P7_R54_OP09_RATING_AXIS_TARGET_THRESHOLDS:
        raise ValueError("R54 OP12 target thresholds changed")
    below_target = _op12_below_target_axis_refs(scores)
    if data.get("below_target_axis_refs") != below_target or data.get("below_target_axis_count") != len(below_target):
        raise ValueError("R54 OP12 below-target axis refs changed")
    if data.get("verdict") not in P7_R54_OP09_VERDICT_OPTION_REFS:
        raise ValueError("R54 OP12 rating row verdict option changed")
    readfeel_blockers = dedupe_identifiers(data.get("readfeel_blocker_ids") or [], limit=20, max_length=160)
    execution_blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=20, max_length=160)
    if not set(readfeel_blockers).issubset(set(P7_R54_OP09_BLOCKER_ID_OPTION_REFS)):
        raise ValueError("R54 OP12 readfeel blocker id outside frozen form options")
    if not set(execution_blockers).issubset(set(P7_R54_OP13_EXECUTION_BLOCKER_ID_REFS)):
        raise ValueError("R54 OP12 execution blocker id outside canonical options")
    if data.get("readfeel_blocker_count") != len(readfeel_blockers) or data.get("execution_blocker_count") != len(execution_blockers):
        raise ValueError("R54 OP12 blocker counts changed")
    if data.get("rating_source_ref") != P7_R54_OP12_RATING_ROW_SOURCE_REF:
        raise ValueError("R54 OP12 rating source ref changed")
    if data.get("pass_requires_no_blocker") is not True or data.get("red_or_repair_requires_blocker_or_reason") is not True:
        raise ValueError("R54 OP12 verdict/blocker guard refs changed")
    for false_key in (
        "reviewer_free_text_included", "raw_body_included", "comment_text_included", "question_text_included",
        "draft_question_text_included", "local_path_included", "body_hash_included", "packet_content_included",
        "machine_auto_score_used", "machine_metrics_used_for_readfeel",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 OP12 rating row must keep {false_key}=False")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_op12_rating_row")
    return True


def _op12_rating_consistency_issue_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
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
            issues.append({"issue_id": "r54_op12_pass_with_any_blocker_detected", "rating_row_ref": rating_row_ref})
        if verdict == "PASS" and below_target_axis_refs:
            issues.append({"issue_id": "r54_op12_pass_below_axis_target_detected", "rating_row_ref": rating_row_ref})
        if verdict in {"REPAIR_REQUIRED", "RED"} and not readfeel_blockers and not reason_ids:
            issues.append({"issue_id": "r54_op12_red_or_repair_without_blocker_or_reason_detected", "rating_row_ref": rating_row_ref})
    return issues


def build_p7_r54_op12_rating_row_normalization(
    *,
    sanitized_review_result_capture: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_operation_rating_row_normalization",
) -> dict[str, Any]:
    """Build R54-OP-12 body-free rating row normalization."""
    op11 = safe_mapping(sanitized_review_result_capture) if sanitized_review_result_capture is not None else build_p7_r54_op11_sanitized_review_result_capture()
    assert_p7_r54_op11_sanitized_review_result_capture_contract(op11)
    op11_allows_next = bool(
        op11.get("sanitized_review_result_capture_status") == P7_R54_OP11_SANITIZED_CAPTURE_READY_STATUS_REF
        and op11.get("rating_row_normalization_allowed_next") is True
        and op11.get("next_required_step") == P7_R54_OP12_STEP_REF
    )
    review_session_id = _safe_review_session_id(op11.get("review_session_id"))
    normalized_rows = [
        _build_p7_r54_op12_rating_row_from_sanitized_row(safe_mapping(row))
        for row in (op11.get("sanitized_review_result_rows") or [])
    ] if op11_allows_next else []
    blockers: list[str] = []
    if not op11_allows_next:
        blockers.append("op11_sanitized_review_result_capture_not_ready_for_rating_normalization")
    if op11_allows_next and len(normalized_rows) != P7_R51_REQUIRED_CASE_COUNT:
        blockers.append("rating_row_count_must_be_24")
    if op11_allows_next and _op05_case_refs(normalized_rows, "case_ref_id") != list(op11.get("case_ref_ids") or []):
        blockers.append("rating_row_case_refs_must_match_sanitized_capture")
    if op11_allows_next and _op05_case_refs(normalized_rows, "packet_ref_id") != list(op11.get("packet_ref_ids") or []):
        blockers.append("rating_row_packet_refs_must_match_sanitized_capture")
    consistency_issues = _op12_rating_consistency_issue_rows(normalized_rows) if op11_allows_next else []
    if consistency_issues:
        blockers.append("rating_row_verdict_blocker_consistency_failed")
    execution_blockers = dedupe_identifiers([*blockers, *(op11.get("open_execution_blocker_ids") or [])], limit=100, max_length=180)
    ready = bool(op11_allows_next and len(normalized_rows) == P7_R51_REQUIRED_CASE_COUNT and not execution_blockers)
    rows = normalized_rows if ready else []
    rating_row_refs = _op05_case_refs(rows, "rating_row_ref")
    packet_refs = _op05_case_refs(rows, "packet_ref_id")
    case_refs = _op05_case_refs(rows, "case_ref_id")
    blind_ids = _op05_case_refs(rows, "blind_case_id")
    reason_refs = [P7_R54_OP12_READY_REASON_REF] if ready else dedupe_identifiers([P7_R54_OP12_RATING_NORMALIZATION_BLOCKED_STATUS_REF, *execution_blockers], limit=100, max_length=180)
    material = {
        "schema_version": P7_R54_OPERATION_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_OPERATION_REENTRY_STEP,
        "scope": P7_R54_OPERATION_REENTRY_SCOPE,
        "policy_kind": P7_R54_OPERATION_REENTRY_POLICY_KIND,
        "policy_section": P7_R54_OP12_STEP_REF,
        "operation_step_ref": P7_R54_OP12_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_operation_rating_row_normalization", max_length=220),
        "review_session_id": review_session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op11_schema_version": P7_R54_OPERATION_SANITIZED_REVIEW_RESULT_CAPTURE_SCHEMA_VERSION,
        "op11_material_ref": clean_identifier(op11.get("material_id"), default="p7_r54_operation_sanitized_review_result_capture", max_length=220),
        "op11_next_required_step": clean_identifier(op11.get("next_required_step"), default="", max_length=180),
        "op11_sanitized_review_result_capture_status": clean_identifier(op11.get("sanitized_review_result_capture_status"), default=P7_R54_OP11_SANITIZED_CAPTURE_BLOCKED_STATUS_REF, max_length=180),
        "op11_rating_row_normalization_allowed_next": op11_allows_next,
        "operation_current_refs": dict(P7_R54_OPERATION_CURRENT_REFS),
        "operation_current_ref_count": len(P7_R54_OPERATION_CURRENT_REFS),
        "actual_review_basis_ref": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "sanitized_review_result_row_count": int(op11.get("sanitized_review_result_row_count") or 0) if op11_allows_next else 0,
        "rating_row_normalization_status": P7_R54_OP12_RATING_NORMALIZATION_READY_STATUS_REF if ready else P7_R54_OP12_RATING_NORMALIZATION_BLOCKED_STATUS_REF,
        "rating_row_normalization_ref": P7_R54_OP12_RATING_ROW_NORMALIZATION_REF if ready else "rating_row_normalization_not_ready_bodyfree",
        "rating_row_normalization_reason_refs": reason_refs,
        "execution_blocker_ids": [] if ready else execution_blockers,
        "open_execution_blocker_ids": [] if ready else execution_blockers,
        "rating_rows": rows,
        "rating_row_count": len(rows),
        "reviewed_case_count": len(rows),
        "rating_row_refs": rating_row_refs,
        "rating_row_ref_count": len(rating_row_refs),
        "rating_row_refs_unique": _op05_unique_non_empty(rating_row_refs) if ready else False,
        "packet_ref_ids": packet_refs,
        "packet_ref_count": len(packet_refs),
        "packet_ref_ids_unique": _op05_unique_non_empty(packet_refs) if ready else False,
        "case_ref_ids": case_refs,
        "case_ref_count": len(case_refs),
        "case_ref_ids_unique": _op05_unique_non_empty(case_refs) if ready else False,
        "blind_case_ids": blind_ids,
        "blind_case_id_count": len(blind_ids),
        "blind_case_ids_unique": _op05_unique_non_empty(blind_ids) if ready else False,
        "rating_row_schema_version": P7_R54_OPERATION_RATING_ROW_SCHEMA_VERSION,
        "rating_row_required_field_refs": list(P7_R54_OPERATION_RATING_ROW_REQUIRED_FIELD_REFS),
        "rating_axis_refs": list(P7_R54_OP09_RATING_AXIS_REFS),
        "rating_axis_target_thresholds": dict(P7_R54_OP09_RATING_AXIS_TARGET_THRESHOLDS),
        "rating_score_min": P7_R54_OP12_RATING_SCORE_MIN,
        "rating_score_max": P7_R54_OP12_RATING_SCORE_MAX,
        "allowed_verdict_refs": list(P7_R54_OP09_VERDICT_OPTION_REFS),
        "readfeel_blocker_id_refs": list(P7_R54_OP09_BLOCKER_ID_OPTION_REFS),
        "execution_blocker_id_refs": list(P7_R54_OP13_EXECUTION_BLOCKER_ID_REFS),
        "sanitized_reason_ids_only": True,
        "blocker_ids_only": True,
        "missing_axis_scores_pass_allowed": False,
        "extra_rating_axis_allowed": False,
        "machine_auto_score_allowed": False,
        "machine_metrics_used_for_readfeel_allowed": False,
        "reviewer_free_text_bodyfree_allowed": False,
        "blocked_or_not_reviewable_must_use_execution_blocker_row": True,
        "red_or_repair_requires_blocker_or_reason": True,
        "pass_requires_targets_and_no_blockers": True,
        "rating_rows_are_bodyfree": ready,
        "all_required_rating_rows_present": ready,
        "rating_case_ref_sets_match_review_capture": ready,
        "verdict_counts": _op12_verdict_counts(rows),
        "axis_score_averages": _op12_axis_score_averages(rows),
        "rating_consistency_issue_rows": consistency_issues if op11_allows_next else [],
        "rating_consistency_issue_count": len(consistency_issues) if op11_allows_next else 0,
        "pass_with_any_blocker_detected": any(safe_mapping(row).get("issue_id") == "r54_op12_pass_with_any_blocker_detected" for row in consistency_issues) if op11_allows_next else False,
        "pass_below_axis_target_detected": any(safe_mapping(row).get("issue_id") == "r54_op12_pass_below_axis_target_detected" for row in consistency_issues) if op11_allows_next else False,
        "red_or_repair_without_blocker_or_reason_detected": any(safe_mapping(row).get("issue_id") == "r54_op12_red_or_repair_without_blocker_or_reason_detected" for row in consistency_issues) if op11_allows_next else False,
        "readfeel_blocker_row_candidate_count": sum(1 for row in rows if safe_mapping(row).get("readfeel_blocker_ids")),
        "execution_blocker_row_candidate_count": sum(1 for row in rows if safe_mapping(row).get("execution_blocker_ids")),
        "readfeel_blocker_execution_blocker_ingestion_allowed_next": ready,
        "rating_rows_normalized_here": ready,
        "actual_rating_rows_materialized_here": ready,
        "actual_blocker_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_review_evidence_complete": False,
        "question_observation_row_count": 0,
        "disposal_verified": False,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_OP12_IMPLEMENTED_STEPS if ready else tuple(op11.get("implemented_steps") or ())),
        "not_yet_implemented_steps": list(P7_R54_OP12_NOT_YET_IMPLEMENTED_STEPS if ready else tuple(op11.get("not_yet_implemented_steps") or ())),
        "first_next_work_ref": P7_R54_OP_NEXT_WORK_AFTER_OP12_REF if ready else P7_R54_OP_NEXT_WORK_AFTER_OP11_REF,
        "next_required_step": P7_R54_OP13_STEP_REF if ready else P7_R54_OP12_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_operation_no_touch_contract": _operation_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
        "actual_rating_rows_materialized_here": ready,
    }
    assert_p7_r54_op12_rating_row_normalization_contract(material)
    return material


def assert_p7_r54_op12_rating_row_normalization_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(
        data,
        required=P7_R54_OPERATION_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS,
        source="p7_r54_op12_rating_row_normalization",
    )
    _assert_common_operation_contract(
        data,
        schema_version=P7_R54_OPERATION_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        policy_section=P7_R54_OP12_STEP_REF,
        operation_step_ref=P7_R54_OP12_STEP_REF,
        source="p7_r54_op12_rating_row_normalization",
        false_flag_refs=_op12_false_flag_refs(),
    )
    _assert_operation_current_refs(data, source="p7_r54_op12_rating_row_normalization")
    if data.get("op11_schema_version") != P7_R54_OPERATION_SANITIZED_REVIEW_RESULT_CAPTURE_SCHEMA_VERSION:
        raise ValueError("R54 OP12 OP11 schema reference changed")
    if data.get("required_case_count") != P7_R51_REQUIRED_CASE_COUNT:
        raise ValueError("R54 OP12 required case count changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=100, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 OP12 open blockers must match execution blockers")
    for row in data.get("rating_rows") or []:
        assert_p7_r54_op12_rating_row_bodyfree_contract(safe_mapping(row))
    for true_key in (
        "sanitized_reason_ids_only", "blocker_ids_only", "blocked_or_not_reviewable_must_use_execution_blocker_row",
        "red_or_repair_requires_blocker_or_reason", "pass_requires_targets_and_no_blockers",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R54 OP12 must keep {true_key}=True")
    for false_key in (
        "missing_axis_scores_pass_allowed", "extra_rating_axis_allowed", "machine_auto_score_allowed",
        "machine_metrics_used_for_readfeel_allowed", "reviewer_free_text_bodyfree_allowed",
        "actual_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here",
        "actual_review_evidence_complete", "disposal_verified",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 OP12 must keep {false_key}=False")
    if data.get("question_observation_row_count") != 0:
        raise ValueError("R54 OP12 must not normalize question observation rows")
    if data.get("human_review_completion_claim_blocked_here") is not True or data.get("p6_p8_release_promotion_blocked_here") is not True:
        raise ValueError("R54 OP12 must block completion and promotion claims")
    if data.get("rating_row_schema_version") != P7_R54_OPERATION_RATING_ROW_SCHEMA_VERSION:
        raise ValueError("R54 OP12 rating row schema reference changed")
    if tuple(data.get("rating_row_required_field_refs") or ()) != P7_R54_OPERATION_RATING_ROW_REQUIRED_FIELD_REFS:
        raise ValueError("R54 OP12 rating row required fields changed")
    if tuple(data.get("rating_axis_refs") or ()) != P7_R54_OP09_RATING_AXIS_REFS:
        raise ValueError("R54 OP12 rating axes changed")
    if safe_mapping(data.get("rating_axis_target_thresholds")) != P7_R54_OP09_RATING_AXIS_TARGET_THRESHOLDS:
        raise ValueError("R54 OP12 rating thresholds changed")
    if data.get("rating_score_min") != P7_R54_OP12_RATING_SCORE_MIN or data.get("rating_score_max") != P7_R54_OP12_RATING_SCORE_MAX:
        raise ValueError("R54 OP12 score bounds changed")
    ready = data.get("rating_row_normalization_status") == P7_R54_OP12_RATING_NORMALIZATION_READY_STATUS_REF
    if data.get("actual_rating_rows_materialized_here") is not ready:
        raise ValueError("R54 OP12 rating row materialized flag must match readiness")
    if data.get("rating_consistency_issue_count") != len(data.get("rating_consistency_issue_rows") or []):
        raise ValueError("R54 OP12 consistency issue count mismatch")
    if ready:
        if data.get("op11_rating_row_normalization_allowed_next") is not True or data.get("op11_next_required_step") != P7_R54_OP12_STEP_REF:
            raise ValueError("R54 OP12 ready normalization requires OP11 allowance")
        if blockers:
            raise ValueError("R54 OP12 ready normalization must not carry blockers")
        if data.get("rating_row_normalization_ref") != P7_R54_OP12_RATING_ROW_NORMALIZATION_REF:
            raise ValueError("R54 OP12 normalization ref changed")
        if data.get("rating_row_normalization_reason_refs") != [P7_R54_OP12_READY_REASON_REF]:
            raise ValueError("R54 OP12 ready reason refs changed")
        if data.get("rating_row_count") != P7_R51_REQUIRED_CASE_COUNT or data.get("reviewed_case_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 OP12 ready normalization must contain 24 rating rows")
        if data.get("rating_row_refs_unique") is not True or data.get("packet_ref_ids_unique") is not True or data.get("case_ref_ids_unique") is not True or data.get("blind_case_ids_unique") is not True:
            raise ValueError("R54 OP12 ready normalization must preserve unique refs")
        if data.get("rating_rows_are_bodyfree") is not True or data.get("all_required_rating_rows_present") is not True or data.get("rating_case_ref_sets_match_review_capture") is not True:
            raise ValueError("R54 OP12 ready normalization must keep body-free complete rating rows")
        if data.get("rating_consistency_issue_rows") != []:
            raise ValueError("R54 OP12 ready normalization must not carry rating consistency issues")
        if data.get("readfeel_blocker_execution_blocker_ingestion_allowed_next") is not True:
            raise ValueError("R54 OP12 ready normalization must allow OP13 next")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_OP12_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP12 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_OP12_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP12 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_OP13_STEP_REF:
            raise ValueError("R54 OP12 ready normalization must point to OP13")
    else:
        if data.get("rating_row_normalization_status") != P7_R54_OP12_RATING_NORMALIZATION_BLOCKED_STATUS_REF:
            raise ValueError("R54 OP12 blocked status changed")
        if data.get("rating_rows") != [] or data.get("rating_row_count") != 0:
            raise ValueError("R54 OP12 blocked normalization must not materialize rating rows")
        if data.get("actual_rating_rows_materialized_here") is not False:
            raise ValueError("R54 OP12 blocked normalization must not materialize rating rows")
        if data.get("readfeel_blocker_execution_blocker_ingestion_allowed_next") is not False:
            raise ValueError("R54 OP12 blocked normalization must not allow OP13")
        if not blockers:
            raise ValueError("R54 OP12 blocked normalization must carry blockers")
        if data.get("next_required_step") != P7_R54_OP12_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 OP12 blocked normalization must point to repair")
    return True


def _op13_single_id_counts(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        item = clean_identifier(safe_mapping(row).get(key), max_length=180)
        if item:
            counts[item] = counts.get(item, 0) + 1
    return counts


def build_p7_r54_op13_readfeel_blocker_row_bodyfree(*, rating_row: Mapping[str, Any], blocker_id: Any, blocker_status_ref: Any = "open") -> dict[str, Any]:
    row = safe_mapping(rating_row)
    assert_p7_r54_op12_rating_row_bodyfree_contract(row)
    blocker_ref = clean_identifier(blocker_id, default="", max_length=160)
    if blocker_ref not in P7_R54_OP09_BLOCKER_ID_OPTION_REFS:
        raise ValueError("R54 OP13 readfeel blocker row must use frozen blocker id")
    status_ref = clean_identifier(blocker_status_ref, default="open", max_length=40)
    if status_ref not in P7_R54_OP13_BLOCKER_STATUS_REFS:
        raise ValueError("R54 OP13 readfeel blocker row status changed")
    out = {
        "schema_version": P7_R54_OPERATION_READFEEL_BLOCKER_ROW_SCHEMA_VERSION,
        "blocker_row_ref": f"r54op13-readfeel-blocker-{clean_identifier(row.get('rating_row_ref'), default='rating-row', max_length=120)}-{blocker_ref}",
        "review_session_id": _safe_review_session_id(row.get("review_session_id")),
        "rating_row_ref": clean_identifier(row.get("rating_row_ref"), max_length=180),
        "packet_ref_id": clean_identifier(row.get("packet_ref_id"), max_length=180),
        "blind_case_id": clean_identifier(row.get("blind_case_id"), max_length=180),
        "case_ref_id": clean_identifier(row.get("case_ref_id"), max_length=180),
        "family": clean_identifier(row.get("family"), max_length=180),
        "case_role": clean_identifier(row.get("case_role"), max_length=180),
        "reviewer_ref": clean_identifier(row.get("reviewer_ref"), max_length=120),
        "readfeel_blocker_id": blocker_ref,
        "blocker_kind_ref": P7_R54_OP13_READFEEL_BLOCKER_KIND_REF,
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
    assert_p7_r54_op13_readfeel_blocker_row_bodyfree_contract(out)
    return out


def assert_p7_r54_op13_readfeel_blocker_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R54_OPERATION_READFEEL_BLOCKER_ROW_REQUIRED_FIELD_REFS, source="p7_r54_op13_readfeel_blocker_row")
    if data.get("schema_version") != P7_R54_OPERATION_READFEEL_BLOCKER_ROW_SCHEMA_VERSION:
        raise ValueError("R54 OP13 readfeel blocker row schema version changed")
    if data.get("readfeel_blocker_id") not in P7_R54_OP09_BLOCKER_ID_OPTION_REFS:
        raise ValueError("R54 OP13 readfeel blocker id outside frozen form options")
    if data.get("blocker_kind_ref") != P7_R54_OP13_READFEEL_BLOCKER_KIND_REF:
        raise ValueError("R54 OP13 readfeel blocker kind changed")
    if data.get("blocker_status_ref") not in P7_R54_OP13_BLOCKER_STATUS_REFS:
        raise ValueError("R54 OP13 readfeel blocker status changed")
    for false_key in (
        "raw_body_included", "comment_text_included", "reviewer_free_text_included", "question_text_included",
        "draft_question_text_included", "local_path_included", "body_hash_included", "packet_content_included",
        "machine_auto_score_used", "machine_metrics_used_for_readfeel",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 OP13 readfeel blocker row must keep {false_key}=False")
    if data.get("body_free") is not True:
        raise ValueError("R54 OP13 readfeel blocker row must be body-free")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_op13_readfeel_blocker_row")
    return True


def build_p7_r54_op13_execution_blocker_row_bodyfree(
    *,
    source_ref: Any,
    execution_blocker_id: Any,
    review_session_id: Any = P7_R54_OPERATION_DEFAULT_REVIEW_SESSION_ID,
    packet_ref_id: Any = "execution_blocker_no_packet_ref",
    blind_case_id: Any = "execution_blocker_no_blind_case_id",
    case_ref_id: Any = "execution_blocker_no_case_ref_id",
    family: Any = "operation_execution_boundary",
    case_role: Any = "operation_execution_boundary",
    execution_blocker_status_ref: Any = "open",
) -> dict[str, Any]:
    blocker_ref = clean_identifier(execution_blocker_id, default="", max_length=180)
    if blocker_ref not in P7_R54_OP13_EXECUTION_BLOCKER_ID_REFS:
        raise ValueError("R54 OP13 execution blocker row must use canonical execution blocker id")
    status_ref = clean_identifier(execution_blocker_status_ref, default="open", max_length=40)
    if status_ref not in P7_R54_OP13_BLOCKER_STATUS_REFS:
        raise ValueError("R54 OP13 execution blocker row status changed")
    src = clean_identifier(source_ref, default="operation_execution_blocker", max_length=180)
    out = {
        "schema_version": P7_R54_OPERATION_EXECUTION_BLOCKER_ROW_SCHEMA_VERSION,
        "execution_blocker_row_ref": f"r54op13-execution-blocker-{src}-{blocker_ref}",
        "review_session_id": _safe_review_session_id(review_session_id),
        "source_ref": src,
        "packet_ref_id": clean_identifier(packet_ref_id, default="execution_blocker_no_packet_ref", max_length=180),
        "blind_case_id": clean_identifier(blind_case_id, default="execution_blocker_no_blind_case_id", max_length=180),
        "case_ref_id": clean_identifier(case_ref_id, default="execution_blocker_no_case_ref_id", max_length=180),
        "family": clean_identifier(family, default="operation_execution_boundary", max_length=180),
        "case_role": clean_identifier(case_role, default="operation_execution_boundary", max_length=180),
        "execution_blocker_id": blocker_ref,
        "execution_blocker_kind_ref": P7_R54_OP13_EXECUTION_BLOCKER_KIND_REF,
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
    assert_p7_r54_op13_execution_blocker_row_bodyfree_contract(out)
    return out


def assert_p7_r54_op13_execution_blocker_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R54_OPERATION_EXECUTION_BLOCKER_ROW_REQUIRED_FIELD_REFS, source="p7_r54_op13_execution_blocker_row")
    if data.get("schema_version") != P7_R54_OPERATION_EXECUTION_BLOCKER_ROW_SCHEMA_VERSION:
        raise ValueError("R54 OP13 execution blocker row schema version changed")
    if data.get("execution_blocker_id") not in P7_R54_OP13_EXECUTION_BLOCKER_ID_REFS:
        raise ValueError("R54 OP13 execution blocker id outside canonical options")
    if data.get("execution_blocker_kind_ref") != P7_R54_OP13_EXECUTION_BLOCKER_KIND_REF:
        raise ValueError("R54 OP13 execution blocker kind changed")
    if data.get("execution_blocker_status_ref") not in P7_R54_OP13_BLOCKER_STATUS_REFS:
        raise ValueError("R54 OP13 execution blocker status changed")
    if data.get("execution_blocker_does_not_assign_readfeel_verdict") is not True:
        raise ValueError("R54 OP13 execution blocker must not assign readfeel verdict")
    for false_key in (
        "raw_body_included", "comment_text_included", "reviewer_free_text_included", "question_text_included",
        "draft_question_text_included", "local_path_included", "body_hash_included", "packet_content_included",
        "machine_auto_score_used", "machine_metrics_used_for_readfeel",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 OP13 execution blocker row must keep {false_key}=False")
    if data.get("body_free") is not True:
        raise ValueError("R54 OP13 execution blocker row must be body-free")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_op13_execution_blocker_row")
    return True


def _op13_blocker_rows_from_rating_rows(rating_rows: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    readfeel_rows: list[dict[str, Any]] = []
    execution_rows: list[dict[str, Any]] = []
    for rating_row in rating_rows:
        row = safe_mapping(rating_row)
        assert_p7_r54_op12_rating_row_bodyfree_contract(row)
        for blocker_id in row.get("readfeel_blocker_ids") or []:
            readfeel_rows.append(build_p7_r54_op13_readfeel_blocker_row_bodyfree(rating_row=row, blocker_id=blocker_id))
        for blocker_id in row.get("execution_blocker_ids") or []:
            execution_rows.append(
                build_p7_r54_op13_execution_blocker_row_bodyfree(
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


def build_p7_r54_op13_readfeel_blocker_execution_blocker_ingestion(
    *,
    rating_row_normalization: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_operation_readfeel_blocker_execution_blocker_ingestion",
) -> dict[str, Any]:
    """Build R54-OP-13 body-free readfeel/execution blocker ingestion."""
    op12 = safe_mapping(rating_row_normalization) if rating_row_normalization is not None else build_p7_r54_op12_rating_row_normalization()
    assert_p7_r54_op12_rating_row_normalization_contract(op12)
    op12_ready = bool(
        op12.get("rating_row_normalization_status") == P7_R54_OP12_RATING_NORMALIZATION_READY_STATUS_REF
        and op12.get("readfeel_blocker_execution_blocker_ingestion_allowed_next") is True
        and op12.get("next_required_step") == P7_R54_OP13_STEP_REF
    )
    rating_rows = [safe_mapping(row) for row in (op12.get("rating_rows") or [])] if op12_ready else []
    readfeel_rows, row_execution_rows = _op13_blocker_rows_from_rating_rows(rating_rows) if op12_ready else ([], [])
    blockers = [] if op12_ready else dedupe_identifiers(["rating_row_normalization_not_ready_for_blocker_ingestion", *(op12.get("open_execution_blocker_ids") or [])], limit=100, max_length=180)
    operation_execution_rows = [
        build_p7_r54_op13_execution_blocker_row_bodyfree(
            source_ref=clean_identifier(op12.get("material_id"), default="p7_r54_op12_rating_row_normalization", max_length=180),
            execution_blocker_id=blocker,
            review_session_id=op12.get("review_session_id"),
        )
        for blocker in blockers
        if blocker in P7_R54_OP13_EXECUTION_BLOCKER_ID_REFS
    ]
    execution_rows = row_execution_rows if op12_ready else operation_execution_rows
    open_readfeel_count = sum(1 for row in readfeel_rows if row.get("blocker_status_ref") == "open")
    open_execution_count = sum(1 for row in execution_rows if row.get("execution_blocker_status_ref") == "open")
    ready = bool(op12_ready)
    reason_refs = [P7_R54_OP13_READY_REASON_REF] if ready else dedupe_identifiers([P7_R54_OP13_BLOCKER_INGESTION_BLOCKED_STATUS_REF, *blockers], limit=100, max_length=180)
    material = {
        "schema_version": P7_R54_OPERATION_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_OPERATION_REENTRY_STEP,
        "scope": P7_R54_OPERATION_REENTRY_SCOPE,
        "policy_kind": P7_R54_OPERATION_REENTRY_POLICY_KIND,
        "policy_section": P7_R54_OP13_STEP_REF,
        "operation_step_ref": P7_R54_OP13_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_operation_readfeel_blocker_execution_blocker_ingestion", max_length=220),
        "review_session_id": _safe_review_session_id(op12.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op12_schema_version": P7_R54_OPERATION_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        "op12_material_ref": clean_identifier(op12.get("material_id"), default="p7_r54_operation_rating_row_normalization", max_length=220),
        "op12_next_required_step": clean_identifier(op12.get("next_required_step"), default="", max_length=180),
        "op12_rating_row_normalization_status": clean_identifier(op12.get("rating_row_normalization_status"), default=P7_R54_OP12_RATING_NORMALIZATION_BLOCKED_STATUS_REF, max_length=180),
        "op12_blocker_ingestion_allowed_next": op12_ready,
        "operation_current_refs": dict(P7_R54_OPERATION_CURRENT_REFS),
        "operation_current_ref_count": len(P7_R54_OPERATION_CURRENT_REFS),
        "actual_review_basis_ref": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "rating_row_count": len(rating_rows),
        "blocker_ingestion_status": P7_R54_OP13_BLOCKER_INGESTION_READY_STATUS_REF if ready else P7_R54_OP13_BLOCKER_INGESTION_BLOCKED_STATUS_REF,
        "blocker_ingestion_reason_refs": reason_refs,
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        "readfeel_blocker_row_schema_version": P7_R54_OPERATION_READFEEL_BLOCKER_ROW_SCHEMA_VERSION,
        "execution_blocker_row_schema_version": P7_R54_OPERATION_EXECUTION_BLOCKER_ROW_SCHEMA_VERSION,
        "readfeel_blocker_row_required_field_refs": list(P7_R54_OPERATION_READFEEL_BLOCKER_ROW_REQUIRED_FIELD_REFS),
        "execution_blocker_row_required_field_refs": list(P7_R54_OPERATION_EXECUTION_BLOCKER_ROW_REQUIRED_FIELD_REFS),
        "readfeel_blocker_id_refs": list(P7_R54_OP09_BLOCKER_ID_OPTION_REFS),
        "execution_blocker_id_refs": list(P7_R54_OP13_EXECUTION_BLOCKER_ID_REFS),
        "blocker_status_refs": list(P7_R54_OP13_BLOCKER_STATUS_REFS),
        "readfeel_blocker_rows": readfeel_rows,
        "execution_blocker_rows": execution_rows,
        "readfeel_blocker_row_count": len(readfeel_rows),
        "execution_blocker_row_count": len(execution_rows),
        "open_readfeel_blocker_count": open_readfeel_count,
        "open_execution_blocker_count": open_execution_count,
        "readfeel_blocker_counts": _op13_single_id_counts(readfeel_rows, "readfeel_blocker_id"),
        "execution_blocker_counts": _op13_single_id_counts(execution_rows, "execution_blocker_id"),
        "rating_packet_ref_ids": _op05_case_refs(rating_rows, "packet_ref_id"),
        "rating_case_ref_ids": _op05_case_refs(rating_rows, "case_ref_id"),
        "rating_blind_case_ids": _op05_case_refs(rating_rows, "blind_case_id"),
        "readfeel_and_execution_blockers_separated": True,
        "execution_blockers_do_not_assign_readfeel_verdict": True,
        "execution_blocker_cases_do_not_create_rating_rows": True,
        "execution_blocker_open_blocks_p5_confirmed_candidate": True,
        "p5_confirmed_candidate_blocked_by_open_execution_blockers": open_execution_count > 0,
        "rating_missing_maps_to_execution_blocker_not_red": True,
        "local_root_missing_maps_to_execution_blocker_not_red": True,
        "disposal_failed_maps_to_execution_blocker_not_red": True,
        "body_free_leak_maps_to_execution_blocker_not_red": True,
        "readfeel_blocker_row_builder_ready": ready,
        "execution_blocker_row_builder_ready": ready,
        "rating_rows_preserved_from_op12": ready,
        "actual_rating_rows_materialized_here": bool(ready and op12.get("actual_rating_rows_materialized_here") is True),
        "actual_blocker_rows_materialized_here": ready,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_review_evidence_complete": False,
        "question_observation_row_count": 0,
        "disposal_verified": False,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_OP13_IMPLEMENTED_STEPS if ready else tuple(op12.get("implemented_steps") or ())),
        "not_yet_implemented_steps": list(P7_R54_OP13_NOT_YET_IMPLEMENTED_STEPS if ready else tuple(op12.get("not_yet_implemented_steps") or ())),
        "first_next_work_ref": P7_R54_OP_NEXT_WORK_AFTER_OP13_REF if ready else P7_R54_OP_NEXT_WORK_AFTER_OP12_REF,
        "next_required_step": P7_R54_OP14_STEP_REF if ready else P7_R54_OP13_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_operation_no_touch_contract": _operation_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
        "actual_rating_rows_materialized_here": bool(ready and op12.get("actual_rating_rows_materialized_here") is True),
        "actual_blocker_rows_materialized_here": ready,
    }
    assert_p7_r54_op13_readfeel_blocker_execution_blocker_ingestion_contract(material)
    return material


def assert_p7_r54_op13_readfeel_blocker_execution_blocker_ingestion_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(
        data,
        required=P7_R54_OPERATION_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION_REQUIRED_FIELD_REFS,
        source="p7_r54_op13_readfeel_blocker_execution_blocker_ingestion",
    )
    _assert_common_operation_contract(
        data,
        schema_version=P7_R54_OPERATION_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION,
        policy_section=P7_R54_OP13_STEP_REF,
        operation_step_ref=P7_R54_OP13_STEP_REF,
        source="p7_r54_op13_readfeel_blocker_execution_blocker_ingestion",
        false_flag_refs=_op13_false_flag_refs(),
    )
    _assert_operation_current_refs(data, source="p7_r54_op13_readfeel_blocker_execution_blocker_ingestion")
    if data.get("op12_schema_version") != P7_R54_OPERATION_RATING_ROW_NORMALIZATION_SCHEMA_VERSION:
        raise ValueError("R54 OP13 OP12 schema reference changed")
    if data.get("required_case_count") != P7_R51_REQUIRED_CASE_COUNT:
        raise ValueError("R54 OP13 required case count changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=100, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 OP13 open execution blockers must match materialization blockers")
    for row in data.get("readfeel_blocker_rows") or []:
        assert_p7_r54_op13_readfeel_blocker_row_bodyfree_contract(safe_mapping(row))
    for row in data.get("execution_blocker_rows") or []:
        assert_p7_r54_op13_execution_blocker_row_bodyfree_contract(safe_mapping(row))
    if data.get("readfeel_blocker_row_count") != len(data.get("readfeel_blocker_rows") or []):
        raise ValueError("R54 OP13 readfeel blocker row count mismatch")
    if data.get("execution_blocker_row_count") != len(data.get("execution_blocker_rows") or []):
        raise ValueError("R54 OP13 execution blocker row count mismatch")
    if data.get("open_readfeel_blocker_count") != sum(1 for row in data.get("readfeel_blocker_rows") or [] if safe_mapping(row).get("blocker_status_ref") == "open"):
        raise ValueError("R54 OP13 open readfeel blocker count mismatch")
    if data.get("open_execution_blocker_count") != sum(1 for row in data.get("execution_blocker_rows") or [] if safe_mapping(row).get("execution_blocker_status_ref") == "open"):
        raise ValueError("R54 OP13 open execution blocker count mismatch")
    for true_key in (
        "readfeel_and_execution_blockers_separated", "execution_blockers_do_not_assign_readfeel_verdict",
        "execution_blocker_cases_do_not_create_rating_rows", "execution_blocker_open_blocks_p5_confirmed_candidate",
        "rating_missing_maps_to_execution_blocker_not_red", "local_root_missing_maps_to_execution_blocker_not_red",
        "disposal_failed_maps_to_execution_blocker_not_red", "body_free_leak_maps_to_execution_blocker_not_red",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R54 OP13 must keep {true_key}=True")
    if data.get("p5_confirmed_candidate_blocked_by_open_execution_blockers") is not (data.get("open_execution_blocker_count") > 0):
        raise ValueError("R54 OP13 P5-confirmed blocker flag must reflect open execution blockers")
    for false_key in (
        "actual_question_need_observation_rows_materialized_here", "actual_review_evidence_complete", "disposal_verified",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 OP13 must keep {false_key}=False")
    if data.get("question_observation_row_count") != 0:
        raise ValueError("R54 OP13 must not normalize question observation rows")
    if data.get("human_review_completion_claim_blocked_here") is not True or data.get("p6_p8_release_promotion_blocked_here") is not True:
        raise ValueError("R54 OP13 must block completion and promotion claims")
    ready = data.get("blocker_ingestion_status") == P7_R54_OP13_BLOCKER_INGESTION_READY_STATUS_REF
    if ready:
        if data.get("op12_blocker_ingestion_allowed_next") is not True or data.get("op12_next_required_step") != P7_R54_OP13_STEP_REF:
            raise ValueError("R54 OP13 ready ingestion requires OP12 allowance")
        if blockers:
            raise ValueError("R54 OP13 ready ingestion must not carry materialization blockers")
        if data.get("rating_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 OP13 ready ingestion requires 24 rating rows")
        if len(data.get("rating_packet_ref_ids") or []) != P7_R51_REQUIRED_CASE_COUNT or len(data.get("rating_case_ref_ids") or []) != P7_R51_REQUIRED_CASE_COUNT or len(data.get("rating_blind_case_ids") or []) != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 OP13 ready ingestion must preserve 24 rating case refs")
        if data.get("actual_rating_rows_materialized_here") is not True or data.get("actual_blocker_rows_materialized_here") is not True:
            raise ValueError("R54 OP13 ready ingestion must preserve rating rows and materialize blocker rows")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_OP13_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP13 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_OP13_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP13 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_OP14_STEP_REF:
            raise ValueError("R54 OP13 ready ingestion must point to OP14")
    else:
        if data.get("blocker_ingestion_status") != P7_R54_OP13_BLOCKER_INGESTION_BLOCKED_STATUS_REF:
            raise ValueError("R54 OP13 blocked ingestion status changed")
        if data.get("actual_blocker_rows_materialized_here") is not False:
            raise ValueError("R54 OP13 blocked ingestion must not materialize blocker rows")
        if data.get("readfeel_blocker_row_builder_ready") is not False or data.get("execution_blocker_row_builder_ready") is not False:
            raise ValueError("R54 OP13 blocked ingestion must not claim row builders ready")
        if not blockers or data.get("next_required_step") != P7_R54_OP13_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 OP13 blocked ingestion must point to repair")
    return True



def _op14_false_flag_refs() -> tuple[str, ...]:
    return tuple(
        key
        for key in P7_R54_OPERATION_FALSE_FLAG_REFS
        if key not in {"actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here"}
    )


def _op15_false_flag_refs() -> tuple[str, ...]:
    return _op14_false_flag_refs()


def _op14_question_plan_candidate_flags(primary_class: str, repair_required_refs: Sequence[str]) -> tuple[dict[str, bool], bool, bool, bool]:
    repair_refs = set(dedupe_identifiers(repair_required_refs, limit=20, max_length=160))
    repair_without_no_repair = repair_refs - {"no_repair_required"}
    not_question_repair = bool(primary_class in P7_R54_OP14_NOT_QUESTION_REPAIR_PRIMARY_CLASS_REFS or repair_without_no_repair)
    insufficient = primary_class == "insufficient_material_execution_blocker"
    p8_allowed = bool(
        primary_class in P7_R54_OP14_P8_MATERIAL_CANDIDATE_PRIMARY_CLASS_REFS
        and not not_question_repair
        and not insufficient
    )
    flags = {flag: False for flag in P7_R54_OP09_PLAN_CANDIDATE_FLAG_REFS}
    if p8_allowed:
        flags["p8_design_material_candidate"] = True
        if primary_class in flags:
            flags[primary_class] = True
    flags["p8_implementation_spec_finalized_here"] = False
    return flags, p8_allowed, not_question_repair, insufficient


def _op14_question_observation_row_from_sanitized_row(
    row: Mapping[str, Any],
    *,
    rating_row_ref: Any,
) -> dict[str, Any]:
    source = safe_mapping(row)
    _assert_p7_r54_op11_sanitized_review_result_row(source, reviewer_refs=[clean_identifier(source.get("reviewer_ref"), max_length=120)])
    primary_class = clean_identifier(source.get("question_need_primary_class"), max_length=160)
    if primary_class not in P7_R54_OP09_QUESTION_NEED_PRIMARY_CLASS_REFS:
        raise ValueError("R54 OP14 question observation primary class outside frozen options")
    ambiguity_refs = dedupe_identifiers(source.get("ambiguity_kind_refs") or [], limit=20, max_length=160)
    if not ambiguity_refs or not set(ambiguity_refs).issubset(set(P7_R54_OP09_AMBIGUITY_KIND_OPTION_REFS)):
        raise ValueError("R54 OP14 ambiguity refs outside frozen options")
    one_question_fit = clean_identifier(source.get("one_question_fit_ref"), max_length=160)
    if one_question_fit not in P7_R54_OP09_ONE_QUESTION_FIT_OPTION_REFS:
        raise ValueError("R54 OP14 one-question fit ref outside frozen options")
    repair_refs = dedupe_identifiers(source.get("repair_required_refs") or [], limit=20, max_length=160)
    if not repair_refs or not set(repair_refs).issubset(set(P7_R54_OP09_REPAIR_REQUIRED_OPTION_REFS)):
        raise ValueError("R54 OP14 repair refs outside frozen options")
    plan_flags, p8_allowed, not_question_repair, insufficient = _op14_question_plan_candidate_flags(primary_class, repair_refs)
    out = {
        "schema_version": P7_R54_OPERATION_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION,
        "question_observation_row_ref": f"r54op14-question-row-{clean_identifier(source.get('review_result_row_ref'), default='review-row', max_length=140)}",
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
        "p8_material_candidate_allowed": p8_allowed,
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
    assert_p7_r54_op14_question_need_observation_row_bodyfree_contract(out)
    return out


def assert_p7_r54_op14_question_need_observation_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R54_OPERATION_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS, source="p7_r54_op14_question_observation_row")
    if data.get("schema_version") != P7_R54_OPERATION_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION:
        raise ValueError("R54 OP14 question observation row schema version changed")
    if data.get("question_observation_row_is_bodyfree") is not True or data.get("body_free") is not True:
        raise ValueError("R54 OP14 question observation row must be body-free")
    if data.get("question_need_primary_class") not in P7_R54_OP09_QUESTION_NEED_PRIMARY_CLASS_REFS:
        raise ValueError("R54 OP14 primary class outside frozen refs")
    if not set(data.get("ambiguity_kind_refs") or []).issubset(set(P7_R54_OP09_AMBIGUITY_KIND_OPTION_REFS)):
        raise ValueError("R54 OP14 ambiguity refs outside frozen refs")
    if data.get("one_question_fit_ref") not in P7_R54_OP09_ONE_QUESTION_FIT_OPTION_REFS:
        raise ValueError("R54 OP14 one-question fit outside frozen refs")
    if not set(data.get("repair_required_refs") or []).issubset(set(P7_R54_OP09_REPAIR_REQUIRED_OPTION_REFS)):
        raise ValueError("R54 OP14 repair refs outside frozen refs")
    flags = safe_mapping(data.get("plan_candidate_flags"))
    if tuple(flags.keys()) != P7_R54_OP09_PLAN_CANDIDATE_FLAG_REFS:
        raise ValueError("R54 OP14 plan candidate flag keys changed")
    if flags.get("p8_implementation_spec_finalized_here") is not False:
        raise ValueError("R54 OP14 must not finalize P8 implementation spec")
    expected_flags, expected_p8, expected_not_question, expected_insufficient = _op14_question_plan_candidate_flags(
        clean_identifier(data.get("question_need_primary_class"), max_length=160),
        data.get("repair_required_refs") or [],
    )
    if flags != expected_flags:
        raise ValueError("R54 OP14 plan candidate flags must be derived from canonical refs")
    if data.get("p8_material_candidate_allowed") is not expected_p8:
        raise ValueError("R54 OP14 p8 material candidate flag mismatch")
    if data.get("not_question_repair_required") is not expected_not_question:
        raise ValueError("R54 OP14 not-question repair flag mismatch")
    if data.get("insufficient_material_execution_blocker") is not expected_insufficient:
        raise ValueError("R54 OP14 insufficient material flag mismatch")
    for false_key in (
        "question_text_included", "draft_question_text_included", "reviewer_free_text_included", "raw_body_included",
        "comment_text_included", "local_path_included", "body_hash_included", "packet_content_included",
        "machine_auto_score_used", "machine_metrics_used_for_readfeel",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 OP14 question row must keep {false_key}=False")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_op14_question_observation_row")
    return True


def _op14_single_id_counts(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = safe_mapping(row).get(key)
        values = value if isinstance(value, list) else [value]
        for item in values:
            ref = clean_identifier(item, default="", max_length=180)
            if ref:
                counts[ref] = counts.get(ref, 0) + 1
    return counts


def build_p7_r54_op14_question_need_observation_normalization(
    *,
    blocker_ingestion: Mapping[str, Any] | None = None,
    rating_row_normalization: Mapping[str, Any] | None = None,
    sanitized_review_result_capture: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_operation_question_need_observation_normalization",
) -> dict[str, Any]:
    """Build R54-OP-14 body-free question-need observation row normalization."""
    op13 = safe_mapping(blocker_ingestion) if blocker_ingestion is not None else build_p7_r54_op13_readfeel_blocker_execution_blocker_ingestion()
    assert_p7_r54_op13_readfeel_blocker_execution_blocker_ingestion_contract(op13)
    op12 = safe_mapping(rating_row_normalization) if rating_row_normalization is not None else build_p7_r54_op12_rating_row_normalization()
    assert_p7_r54_op12_rating_row_normalization_contract(op12)
    op11 = safe_mapping(sanitized_review_result_capture) if sanitized_review_result_capture is not None else build_p7_r54_op11_sanitized_review_result_capture()
    assert_p7_r54_op11_sanitized_review_result_capture_contract(op11)

    op13_ready = bool(
        op13.get("blocker_ingestion_status") == P7_R54_OP13_BLOCKER_INGESTION_READY_STATUS_REF
        and op13.get("next_required_step") == P7_R54_OP14_STEP_REF
        and not op13.get("open_execution_blocker_ids")
    )
    op12_ready = bool(
        op12.get("rating_row_normalization_status") == P7_R54_OP12_RATING_NORMALIZATION_READY_STATUS_REF
        and op12.get("rating_row_count") == P7_R51_REQUIRED_CASE_COUNT
        and not op12.get("open_execution_blocker_ids")
    )
    op11_ready = bool(
        op11.get("sanitized_review_result_capture_status") == P7_R54_OP11_SANITIZED_CAPTURE_READY_STATUS_REF
        and op11.get("sanitized_review_result_row_count") == P7_R51_REQUIRED_CASE_COUNT
        and not op11.get("open_execution_blocker_ids")
    )
    blockers: list[str] = []
    if not op13_ready:
        blockers.append("blocker_ingestion_not_ready_for_question_observation_normalization")
    if not op12_ready:
        blockers.append("rating_row_normalization_not_ready_for_question_observation_normalization")
    if not op11_ready:
        blockers.append("sanitized_review_capture_not_ready_for_question_observation_normalization")
    rating_rows = [safe_mapping(row) for row in (op12.get("rating_rows") or [])] if op12_ready else []
    sanitized_rows = [safe_mapping(row) for row in (op11.get("sanitized_review_result_rows") or [])] if op11_ready else []
    rating_by_review_result_ref = {
        clean_identifier(row.get("review_result_row_ref"), default="", max_length=180): clean_identifier(row.get("rating_row_ref"), default="", max_length=180)
        for row in rating_rows
    }
    question_rows = []
    if op13_ready and op12_ready and op11_ready:
        for row in sanitized_rows:
            review_result_ref = clean_identifier(row.get("review_result_row_ref"), default="", max_length=180)
            question_rows.append(_op14_question_observation_row_from_sanitized_row(row, rating_row_ref=rating_by_review_result_ref.get(review_result_ref, "")))
    row_case_ref_sets_match_review_capture = bool(_op05_case_refs(question_rows, "case_ref_id") == list(op11.get("case_ref_ids") or [])) if question_rows else False
    row_case_ref_sets_match_rating_rows = bool(_op05_case_refs(question_rows, "case_ref_id") == list(op12.get("case_ref_ids") or [])) if question_rows else False
    all_required = bool(len(question_rows) == P7_R51_REQUIRED_CASE_COUNT and row_case_ref_sets_match_review_capture and row_case_ref_sets_match_rating_rows)
    canonical = all(
        row.get("question_need_primary_class") in P7_R54_OP09_QUESTION_NEED_PRIMARY_CLASS_REFS
        and set(row.get("ambiguity_kind_refs") or []).issubset(set(P7_R54_OP09_AMBIGUITY_KIND_OPTION_REFS))
        and row.get("one_question_fit_ref") in P7_R54_OP09_ONE_QUESTION_FIT_OPTION_REFS
        for row in question_rows
    ) if question_rows else False
    not_question_misclassified = any(
        row.get("not_question_repair_required") is True and row.get("p8_material_candidate_allowed") is True
        for row in question_rows
    )
    if question_rows and not all_required:
        blockers.append("question_observation_row_count_or_case_ref_set_mismatch")
    if question_rows and not canonical:
        blockers.append("question_observation_canonical_refs_failed")
    if not_question_misclassified:
        blockers.append("not_question_repair_rows_misclassified_as_p8_material")
    blockers = dedupe_identifiers([*blockers, *(op13.get("open_execution_blocker_ids") or [])], limit=100, max_length=180)
    ready = bool(op13_ready and op12_ready and op11_ready and all_required and canonical and not blockers)
    rows = question_rows if ready else []
    reason_refs = [P7_R54_OP14_READY_REASON_REF] if ready else dedupe_identifiers([P7_R54_OP14_QUESTION_OBSERVATION_NORMALIZATION_BLOCKED_STATUS_REF, *blockers], limit=100, max_length=180)
    material = {
        "schema_version": P7_R54_OPERATION_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_OPERATION_REENTRY_STEP,
        "scope": P7_R54_OPERATION_REENTRY_SCOPE,
        "policy_kind": P7_R54_OPERATION_REENTRY_POLICY_KIND,
        "policy_section": P7_R54_OP14_STEP_REF,
        "operation_step_ref": P7_R54_OP14_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_operation_question_need_observation_normalization", max_length=220),
        "review_session_id": _safe_review_session_id(op13.get("review_session_id") or op12.get("review_session_id") or op11.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op13_schema_version": P7_R54_OPERATION_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION,
        "op13_material_ref": clean_identifier(op13.get("material_id"), default="p7_r54_operation_readfeel_blocker_execution_blocker_ingestion", max_length=220),
        "op13_next_required_step": clean_identifier(op13.get("next_required_step"), default="", max_length=180),
        "op13_blocker_ingestion_status": clean_identifier(op13.get("blocker_ingestion_status"), default=P7_R54_OP13_BLOCKER_INGESTION_BLOCKED_STATUS_REF, max_length=180),
        "op13_question_observation_normalization_allowed_next": op13_ready,
        "op12_schema_version": P7_R54_OPERATION_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        "op12_material_ref": clean_identifier(op12.get("material_id"), default="p7_r54_operation_rating_row_normalization", max_length=220),
        "op12_rating_row_normalization_status": clean_identifier(op12.get("rating_row_normalization_status"), default=P7_R54_OP12_RATING_NORMALIZATION_BLOCKED_STATUS_REF, max_length=180),
        "op11_schema_version": P7_R54_OPERATION_SANITIZED_REVIEW_RESULT_CAPTURE_SCHEMA_VERSION,
        "op11_material_ref": clean_identifier(op11.get("material_id"), default="p7_r54_operation_sanitized_review_result_capture", max_length=220),
        "op11_sanitized_review_result_capture_status": clean_identifier(op11.get("sanitized_review_result_capture_status"), default=P7_R54_OP11_SANITIZED_CAPTURE_BLOCKED_STATUS_REF, max_length=180),
        "operation_current_refs": dict(P7_R54_OPERATION_CURRENT_REFS),
        "operation_current_ref_count": len(P7_R54_OPERATION_CURRENT_REFS),
        "actual_review_basis_ref": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "question_observation_normalization_status": P7_R54_OP14_QUESTION_OBSERVATION_NORMALIZATION_READY_STATUS_REF if ready else P7_R54_OP14_QUESTION_OBSERVATION_NORMALIZATION_BLOCKED_STATUS_REF,
        "question_observation_normalization_ref": P7_R54_OP14_QUESTION_OBSERVATION_NORMALIZATION_REF if ready else "question_observation_normalization_not_ready_bodyfree",
        "question_observation_normalization_reason_refs": reason_refs,
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        "sanitized_review_result_row_count": len(sanitized_rows) if op11_ready else 0,
        "rating_row_count": len(rating_rows) if op12_ready else 0,
        "question_observation_rows": rows,
        "question_observation_row_count": len(rows),
        "question_observation_row_refs": _op05_case_refs(rows, "question_observation_row_ref"),
        "question_observation_row_ref_count": len(rows),
        "question_observation_row_refs_unique": (_op05_unique_non_empty(_op05_case_refs(rows, "question_observation_row_ref")) and len(_op05_case_refs(rows, "question_observation_row_ref")) == len(rows)) if rows else False,
        "case_ref_ids": _op05_case_refs(rows, "case_ref_id"),
        "case_ref_count": len(rows),
        "case_ref_ids_unique": (_op05_unique_non_empty(_op05_case_refs(rows, "case_ref_id")) and len(_op05_case_refs(rows, "case_ref_id")) == len(rows)) if rows else False,
        "packet_ref_ids": _op05_case_refs(rows, "packet_ref_id"),
        "packet_ref_count": len(rows),
        "packet_ref_ids_unique": (_op05_unique_non_empty(_op05_case_refs(rows, "packet_ref_id")) and len(_op05_case_refs(rows, "packet_ref_id")) == len(rows)) if rows else False,
        "blind_case_ids": _op05_case_refs(rows, "blind_case_id"),
        "blind_case_id_count": len(rows),
        "blind_case_ids_unique": (_op05_unique_non_empty(_op05_case_refs(rows, "blind_case_id")) and len(_op05_case_refs(rows, "blind_case_id")) == len(rows)) if rows else False,
        "question_observation_row_schema_version": P7_R54_OPERATION_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION,
        "question_observation_row_required_field_refs": list(P7_R54_OPERATION_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS),
        "question_need_primary_class_refs": list(P7_R54_OP09_QUESTION_NEED_PRIMARY_CLASS_REFS),
        "ambiguity_kind_refs": list(P7_R54_OP09_AMBIGUITY_KIND_OPTION_REFS),
        "one_question_fit_refs": list(P7_R54_OP09_ONE_QUESTION_FIT_OPTION_REFS),
        "repair_required_ref_refs": list(P7_R54_OP09_REPAIR_REQUIRED_OPTION_REFS),
        "plan_candidate_flag_refs": list(P7_R54_OP09_PLAN_CANDIDATE_FLAG_REFS),
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
        "row_case_ref_sets_match_review_capture": bool(ready and row_case_ref_sets_match_review_capture),
        "row_case_ref_sets_match_rating_rows": bool(ready and row_case_ref_sets_match_rating_rows),
        "all_required_question_need_observation_rows_present": bool(ready and all_required),
        "primary_class_ambiguity_one_question_fit_are_canonical_refs": bool(ready and canonical),
        "not_question_repair_rows_misclassified_as_p8_material": bool(not_question_misclassified),
        "p5_weakness_not_hidden_by_question_candidates_here": not bool(not_question_misclassified),
        "question_text_or_draft_text_saved_here": False,
        "question_need_primary_class_counts": _op14_single_id_counts(rows, "question_need_primary_class"),
        "ambiguity_kind_counts": _op14_single_id_counts(rows, "ambiguity_kind_refs"),
        "one_question_fit_counts": _op14_single_id_counts(rows, "one_question_fit_ref"),
        "repair_required_counts": _op14_single_id_counts(rows, "repair_required_refs"),
        "plan_candidate_flag_counts": {flag: sum(1 for row in rows if safe_mapping(row.get("plan_candidate_flags")).get(flag) is True) for flag in P7_R54_OP09_PLAN_CANDIDATE_FLAG_REFS},
        "p8_material_candidate_row_count": sum(1 for row in rows if row.get("p8_material_candidate_allowed") is True),
        "not_question_repair_required_count": sum(1 for row in rows if row.get("not_question_repair_required") is True),
        "insufficient_material_execution_blocker_count": sum(1 for row in rows if row.get("insufficient_material_execution_blocker") is True),
        "rating_rows_preserved_from_op12": bool(ready and op12.get("actual_rating_rows_materialized_here") is True),
        "blocker_rows_preserved_from_op13": bool(ready and op13.get("actual_blocker_rows_materialized_here") is True),
        "rating_question_consistency_guard_allowed_next": ready,
        "actual_rating_rows_materialized_here": bool(ready and op12.get("actual_rating_rows_materialized_here") is True),
        "actual_blocker_rows_materialized_here": bool(ready and op13.get("actual_blocker_rows_materialized_here") is True),
        "actual_question_need_observation_rows_materialized_here": ready,
        "actual_review_evidence_complete": False,
        "disposal_verified": False,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_OP14_IMPLEMENTED_STEPS if ready else tuple(op13.get("implemented_steps") or ())),
        "not_yet_implemented_steps": list(P7_R54_OP14_NOT_YET_IMPLEMENTED_STEPS if ready else tuple(op13.get("not_yet_implemented_steps") or ())),
        "first_next_work_ref": P7_R54_OP_NEXT_WORK_AFTER_OP14_REF if ready else P7_R54_OP_NEXT_WORK_AFTER_OP13_REF,
        "next_required_step": P7_R54_OP15_STEP_REF if ready else P7_R54_OP14_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_operation_no_touch_contract": _operation_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
        "actual_rating_rows_materialized_here": bool(ready and op12.get("actual_rating_rows_materialized_here") is True),
        "actual_blocker_rows_materialized_here": bool(ready and op13.get("actual_blocker_rows_materialized_here") is True),
        "actual_question_need_observation_rows_materialized_here": ready,
    }
    assert_p7_r54_op14_question_need_observation_normalization_contract(material)
    return material


def assert_p7_r54_op14_question_need_observation_normalization_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_OPERATION_QUESTION_NEED_OBSERVATION_NORMALIZATION_REQUIRED_FIELD_REFS, source="p7_r54_op14_question_need_observation_normalization")
    _assert_common_operation_contract(
        data,
        schema_version=P7_R54_OPERATION_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION,
        policy_section=P7_R54_OP14_STEP_REF,
        operation_step_ref=P7_R54_OP14_STEP_REF,
        source="p7_r54_op14_question_need_observation_normalization",
        false_flag_refs=_op14_false_flag_refs(),
    )
    _assert_operation_current_refs(data, source="p7_r54_op14_question_need_observation_normalization")
    if data.get("op13_schema_version") != P7_R54_OPERATION_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION:
        raise ValueError("R54 OP14 OP13 schema reference changed")
    if data.get("op12_schema_version") != P7_R54_OPERATION_RATING_ROW_NORMALIZATION_SCHEMA_VERSION:
        raise ValueError("R54 OP14 OP12 schema reference changed")
    if data.get("op11_schema_version") != P7_R54_OPERATION_SANITIZED_REVIEW_RESULT_CAPTURE_SCHEMA_VERSION:
        raise ValueError("R54 OP14 OP11 schema reference changed")
    if data.get("required_case_count") != P7_R51_REQUIRED_CASE_COUNT:
        raise ValueError("R54 OP14 required case count changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=100, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 OP14 open blockers must match blockers")
    rows = [safe_mapping(row) for row in (data.get("question_observation_rows") or [])]
    for row in rows:
        assert_p7_r54_op14_question_need_observation_row_bodyfree_contract(row)
    if data.get("question_observation_row_count") != len(rows):
        raise ValueError("R54 OP14 question row count mismatch")
    if data.get("question_observation_row_ref_count") != len(data.get("question_observation_row_refs") or []):
        raise ValueError("R54 OP14 question row ref count mismatch")
    for true_key in (
        "question_need_observation_rows_are_bodyfree", "question_text_absent_for_all_rows", "draft_question_text_absent_for_all_rows",
        "reviewer_free_text_absent_for_all_rows", "raw_body_absent_for_all_rows", "comment_text_absent_for_all_rows",
        "local_path_absent_for_all_rows", "body_hash_absent_for_all_rows", "p5_weakness_not_hidden_by_question_candidates_here",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R54 OP14 must keep {true_key}=True")
    for false_key in (
        "question_text_included_allowed", "draft_question_text_included_allowed", "reviewer_free_text_included_allowed",
        "raw_body_allowed", "comment_text_allowed", "local_path_allowed", "body_hash_allowed",
        "p8_question_implementation_spec_finalized_here", "question_trigger_logic_implemented",
        "question_trigger_logic_implemented_here", "api_db_rn_response_key_changed_here", "question_api_implemented",
        "question_db_schema_implemented", "question_rn_ui_implemented", "question_response_key_implemented",
        "question_storage_schema_implemented", "question_answer_persistence_implemented", "question_plan_guard_implemented",
        "question_text_or_draft_text_saved_here", "actual_review_evidence_complete", "disposal_verified",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 OP14 must keep {false_key}=False")
    if tuple(data.get("question_need_primary_class_refs") or ()) != P7_R54_OP09_QUESTION_NEED_PRIMARY_CLASS_REFS:
        raise ValueError("R54 OP14 primary class refs changed")
    if tuple(data.get("ambiguity_kind_refs") or ()) != P7_R54_OP09_AMBIGUITY_KIND_OPTION_REFS:
        raise ValueError("R54 OP14 ambiguity refs changed")
    if tuple(data.get("one_question_fit_refs") or ()) != P7_R54_OP09_ONE_QUESTION_FIT_OPTION_REFS:
        raise ValueError("R54 OP14 one-question refs changed")
    if tuple(data.get("repair_required_ref_refs") or ()) != P7_R54_OP09_REPAIR_REQUIRED_OPTION_REFS:
        raise ValueError("R54 OP14 repair refs changed")
    if tuple(data.get("plan_candidate_flag_refs") or ()) != P7_R54_OP09_PLAN_CANDIDATE_FLAG_REFS:
        raise ValueError("R54 OP14 plan candidate flag refs changed")
    ready = data.get("question_observation_normalization_status") == P7_R54_OP14_QUESTION_OBSERVATION_NORMALIZATION_READY_STATUS_REF
    if ready:
        if data.get("op13_question_observation_normalization_allowed_next") is not True or data.get("op13_next_required_step") != P7_R54_OP14_STEP_REF:
            raise ValueError("R54 OP14 ready normalization requires OP13 allowance")
        if data.get("question_observation_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 OP14 ready normalization requires 24 question rows")
        if data.get("actual_question_need_observation_rows_materialized_here") is not True:
            raise ValueError("R54 OP14 ready normalization must materialize question rows")
        if data.get("rating_question_consistency_guard_allowed_next") is not True or data.get("next_required_step") != P7_R54_OP15_STEP_REF:
            raise ValueError("R54 OP14 ready normalization must point to OP15")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_OP14_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP14 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_OP14_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP14 not-yet steps changed")
    else:
        if data.get("question_observation_normalization_status") != P7_R54_OP14_QUESTION_OBSERVATION_NORMALIZATION_BLOCKED_STATUS_REF:
            raise ValueError("R54 OP14 blocked status changed")
        if rows or data.get("question_observation_row_count") != 0:
            raise ValueError("R54 OP14 blocked normalization must not materialize rows")
        if data.get("actual_question_need_observation_rows_materialized_here") is not False:
            raise ValueError("R54 OP14 blocked normalization must not materialize question rows")
        if not blockers or data.get("next_required_step") != P7_R54_OP14_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 OP14 blocked normalization must point to repair")
    return True


def build_p7_r54_op15_rating_question_consistency_issue_row_bodyfree(
    *,
    rating_row: Mapping[str, Any],
    question_observation_row: Mapping[str, Any],
    issue_id: Any,
    issue_kind_ref: Any,
    decision_direction_ref: Any,
) -> dict[str, Any]:
    rating = safe_mapping(rating_row)
    question = safe_mapping(question_observation_row)
    assert_p7_r54_op12_rating_row_bodyfree_contract(rating)
    assert_p7_r54_op14_question_need_observation_row_bodyfree_contract(question)
    issue_id_ref = clean_identifier(issue_id, max_length=180)
    if issue_id_ref not in P7_R54_OP15_CONSISTENCY_ISSUE_ID_REFS:
        raise ValueError("R54 OP15 issue id must be canonical")
    issue_kind = clean_identifier(issue_kind_ref, max_length=180)
    if issue_kind not in P7_R54_OP15_CONSISTENCY_ISSUE_KIND_REFS:
        raise ValueError("R54 OP15 issue kind must be canonical")
    direction = clean_identifier(decision_direction_ref, max_length=180)
    if direction not in P7_R54_OP15_DECISION_DIRECTION_REFS:
        raise ValueError("R54 OP15 decision direction must be canonical")
    out = {
        "schema_version": P7_R54_OPERATION_RATING_QUESTION_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION,
        "consistency_issue_row_ref": f"r54op15-issue-{issue_id_ref}-{clean_identifier(rating.get('case_ref_id'), default='case', max_length=100)}",
        "review_session_id": _safe_review_session_id(rating.get("review_session_id") or question.get("review_session_id")),
        "rating_row_ref": clean_identifier(rating.get("rating_row_ref"), max_length=180),
        "question_observation_row_ref": clean_identifier(question.get("question_observation_row_ref"), max_length=180),
        "packet_ref_id": clean_identifier(rating.get("packet_ref_id") or question.get("packet_ref_id"), max_length=180),
        "blind_case_id": clean_identifier(rating.get("blind_case_id") or question.get("blind_case_id"), max_length=180),
        "case_ref_id": clean_identifier(rating.get("case_ref_id") or question.get("case_ref_id"), max_length=180),
        "family": clean_identifier(rating.get("family") or question.get("family"), max_length=180),
        "case_role": clean_identifier(rating.get("case_role") or question.get("case_role"), max_length=180),
        "issue_id": issue_id_ref,
        "issue_kind_ref": issue_kind,
        "decision_direction_ref": direction,
        "issue_status_ref": "open",
        "source_verdict": clean_identifier(rating.get("verdict"), max_length=80),
        "question_need_primary_class": clean_identifier(question.get("question_need_primary_class"), max_length=160),
        "repair_required_refs": dedupe_identifiers(question.get("repair_required_refs") or [], limit=20, max_length=160),
        "p8_material_candidate_allowed": question.get("p8_material_candidate_allowed") is True,
        "not_question_repair_required": question.get("not_question_repair_required") is True,
        "insufficient_material_execution_blocker": question.get("insufficient_material_execution_blocker") is True,
        "body_free": True,
        "question_text_included": False,
        "draft_question_text_included": False,
        "reviewer_free_text_included": False,
        "raw_body_included": False,
        "comment_text_included": False,
        "local_path_included": False,
        "body_hash_included": False,
        "packet_content_included": False,
    }
    assert_p7_r54_op15_rating_question_consistency_issue_row_bodyfree_contract(out)
    return out


def assert_p7_r54_op15_rating_question_consistency_issue_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R54_OPERATION_RATING_QUESTION_CONSISTENCY_ISSUE_ROW_REQUIRED_FIELD_REFS, source="p7_r54_op15_consistency_issue_row")
    if data.get("schema_version") != P7_R54_OPERATION_RATING_QUESTION_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION:
        raise ValueError("R54 OP15 issue row schema version changed")
    if data.get("issue_id") not in P7_R54_OP15_CONSISTENCY_ISSUE_ID_REFS:
        raise ValueError("R54 OP15 issue id outside canonical refs")
    if data.get("issue_kind_ref") not in P7_R54_OP15_CONSISTENCY_ISSUE_KIND_REFS:
        raise ValueError("R54 OP15 issue kind outside canonical refs")
    if data.get("decision_direction_ref") not in P7_R54_OP15_DECISION_DIRECTION_REFS:
        raise ValueError("R54 OP15 direction outside canonical refs")
    if data.get("issue_status_ref") != "open":
        raise ValueError("R54 OP15 issue row status must remain open")
    for false_key in (
        "question_text_included", "draft_question_text_included", "reviewer_free_text_included", "raw_body_included",
        "comment_text_included", "local_path_included", "body_hash_included", "packet_content_included",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 OP15 issue row must keep {false_key}=False")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_op15_consistency_issue_row")
    return True


def _op15_question_by_case_ref(rows: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {clean_identifier(row.get("case_ref_id"), default="", max_length=180): row for row in rows}


def _op15_rating_question_consistency_issue_rows(
    *,
    rating_rows: Sequence[Mapping[str, Any]],
    question_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    question_by_case_ref = _op15_question_by_case_ref(question_rows)
    rating_case_refs = {clean_identifier(row.get("case_ref_id"), default="", max_length=180) for row in rating_rows}
    question_case_refs = {clean_identifier(row.get("case_ref_id"), default="", max_length=180) for row in question_rows}
    if rating_case_refs != question_case_refs:
        sample_rating = safe_mapping(rating_rows[0]) if rating_rows else {}
        sample_question = safe_mapping(question_rows[0]) if question_rows else {}
        if sample_rating and sample_question:
            issues.append(build_p7_r54_op15_rating_question_consistency_issue_row_bodyfree(
                rating_row=sample_rating,
                question_observation_row=sample_question,
                issue_id="r54_op15_rating_question_case_ref_set_mismatch",
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
        p8_allowed = question.get("p8_material_candidate_allowed") is True
        not_question_repair = question.get("not_question_repair_required") is True
        insufficient = question.get("insufficient_material_execution_blocker") is True
        if verdict in {"REPAIR_REQUIRED", "RED"} and primary_class == "no_question_needed_emlis_can_observe":
            issues.append(build_p7_r54_op15_rating_question_consistency_issue_row_bodyfree(
                rating_row=rating_row,
                question_observation_row=question,
                issue_id="r54_op15_red_or_repair_with_no_question_needed_observation",
                issue_kind_ref="rating_question_observation_semantic_mismatch",
                decision_direction_ref="p5_repair_return_required_later",
            ))
        if verdict in {"REPAIR_REQUIRED", "RED"} and p8_allowed:
            issues.append(build_p7_r54_op15_rating_question_consistency_issue_row_bodyfree(
                rating_row=rating_row,
                question_observation_row=question,
                issue_id="r54_op15_repair_required_with_p8_material_candidate",
                issue_kind_ref="p5_repair_hidden_by_question_candidate",
                decision_direction_ref="p5_repair_return_required_later",
            ))
        if verdict == "PASS" and not_question_repair:
            issues.append(build_p7_r54_op15_rating_question_consistency_issue_row_bodyfree(
                rating_row=rating_row,
                question_observation_row=question,
                issue_id="r54_op15_pass_with_not_question_repair_required",
                issue_kind_ref="rating_question_observation_semantic_mismatch",
                decision_direction_ref="p5_repair_return_required_later",
            ))
        if insufficient and verdict == "PASS":
            issues.append(build_p7_r54_op15_rating_question_consistency_issue_row_bodyfree(
                rating_row=rating_row,
                question_observation_row=question,
                issue_id="r54_op15_insufficient_material_with_pass_or_no_execution_blocker",
                issue_kind_ref="p5_inconclusive_or_execution_boundary_mismatch",
                decision_direction_ref="r54_operation_inconclusive_required_later",
            ))
    return issues


def build_p7_r54_op15_rating_question_consistency_guard(
    *,
    question_need_observation_normalization: Mapping[str, Any] | None = None,
    rating_row_normalization: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_operation_rating_question_consistency_guard",
) -> dict[str, Any]:
    """Build R54-OP-15 body-free rating/question consistency guard."""
    op14 = safe_mapping(question_need_observation_normalization) if question_need_observation_normalization is not None else build_p7_r54_op14_question_need_observation_normalization()
    assert_p7_r54_op14_question_need_observation_normalization_contract(op14)
    op12 = safe_mapping(rating_row_normalization) if rating_row_normalization is not None else build_p7_r54_op12_rating_row_normalization()
    assert_p7_r54_op12_rating_row_normalization_contract(op12)
    op14_ready = bool(
        op14.get("question_observation_normalization_status") == P7_R54_OP14_QUESTION_OBSERVATION_NORMALIZATION_READY_STATUS_REF
        and op14.get("rating_question_consistency_guard_allowed_next") is True
        and op14.get("next_required_step") == P7_R54_OP15_STEP_REF
        and not op14.get("open_execution_blocker_ids")
    )
    op12_ready = bool(
        op12.get("rating_row_normalization_status") == P7_R54_OP12_RATING_NORMALIZATION_READY_STATUS_REF
        and op12.get("rating_row_count") == P7_R51_REQUIRED_CASE_COUNT
        and not op12.get("open_execution_blocker_ids")
    )
    blockers: list[str] = []
    if not op14_ready:
        blockers.append("question_observation_normalization_not_ready_for_consistency_guard")
    if not op12_ready:
        blockers.append("rating_row_normalization_not_ready_for_consistency_guard")
    rating_rows = [safe_mapping(row) for row in (op12.get("rating_rows") or [])] if op12_ready else []
    question_rows = [safe_mapping(row) for row in (op14.get("question_observation_rows") or [])] if op14_ready else []
    rating_case_refs = {clean_identifier(row.get("case_ref_id"), default="", max_length=180) for row in rating_rows}
    question_case_refs = {clean_identifier(row.get("case_ref_id"), default="", max_length=180) for row in question_rows}
    case_sets_match = bool(rating_rows and question_rows and rating_case_refs == question_case_refs)
    all_required = bool(len(rating_rows) == P7_R51_REQUIRED_CASE_COUNT and len(question_rows) == P7_R51_REQUIRED_CASE_COUNT and case_sets_match)
    issue_rows = _op15_rating_question_consistency_issue_rows(rating_rows=rating_rows, question_rows=question_rows) if op14_ready and op12_ready else []
    issue_count = len(issue_rows)
    if op14_ready and op12_ready and not all_required:
        blockers.append("rating_question_case_ref_set_mismatch")
    blockers = dedupe_identifiers([*blockers, *(op14.get("open_execution_blocker_ids") or [])], limit=100, max_length=180)
    ready = bool(op14_ready and op12_ready and all_required and issue_count == 0 and not blockers)
    direction_counts = _op14_single_id_counts(issue_rows, "decision_direction_ref")
    reason_refs = [P7_R54_OP15_READY_REASON_REF] if ready else dedupe_identifiers([P7_R54_OP15_CONSISTENCY_GUARD_BLOCKED_STATUS_REF, *blockers, *(row.get("issue_id") for row in issue_rows)], limit=100, max_length=180)
    material = {
        "schema_version": P7_R54_OPERATION_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_OPERATION_REENTRY_STEP,
        "scope": P7_R54_OPERATION_REENTRY_SCOPE,
        "policy_kind": P7_R54_OPERATION_REENTRY_POLICY_KIND,
        "policy_section": P7_R54_OP15_STEP_REF,
        "operation_step_ref": P7_R54_OP15_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_operation_rating_question_consistency_guard", max_length=220),
        "review_session_id": _safe_review_session_id(op14.get("review_session_id") or op12.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op14_schema_version": P7_R54_OPERATION_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION,
        "op14_material_ref": clean_identifier(op14.get("material_id"), default="p7_r54_operation_question_need_observation_normalization", max_length=220),
        "op14_next_required_step": clean_identifier(op14.get("next_required_step"), default="", max_length=180),
        "op14_question_observation_normalization_status": clean_identifier(op14.get("question_observation_normalization_status"), default=P7_R54_OP14_QUESTION_OBSERVATION_NORMALIZATION_BLOCKED_STATUS_REF, max_length=180),
        "op14_consistency_guard_allowed_next": op14_ready,
        "op12_schema_version": P7_R54_OPERATION_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        "op12_material_ref": clean_identifier(op12.get("material_id"), default="p7_r54_operation_rating_row_normalization", max_length=220),
        "op12_rating_row_normalization_status": clean_identifier(op12.get("rating_row_normalization_status"), default=P7_R54_OP12_RATING_NORMALIZATION_BLOCKED_STATUS_REF, max_length=180),
        "operation_current_refs": dict(P7_R54_OPERATION_CURRENT_REFS),
        "operation_current_ref_count": len(P7_R54_OPERATION_CURRENT_REFS),
        "actual_review_basis_ref": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "rating_question_consistency_guard_status": P7_R54_OP15_CONSISTENCY_GUARD_READY_STATUS_REF if ready else P7_R54_OP15_CONSISTENCY_GUARD_BLOCKED_STATUS_REF,
        "rating_question_consistency_guard_ref": P7_R54_OP15_CONSISTENCY_GUARD_REF if ready else "rating_question_consistency_guard_not_ready_bodyfree",
        "rating_question_consistency_guard_reason_refs": reason_refs,
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        "rating_row_count": len(rating_rows) if op12_ready else 0,
        "question_observation_row_count": len(question_rows) if op14_ready else 0,
        "rating_question_case_ref_sets_match": bool(case_sets_match),
        "all_required_rating_and_question_rows_present": bool(all_required),
        "rating_question_consistency_issue_row_schema_version": P7_R54_OPERATION_RATING_QUESTION_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION,
        "rating_question_consistency_issue_row_required_field_refs": list(P7_R54_OPERATION_RATING_QUESTION_CONSISTENCY_ISSUE_ROW_REQUIRED_FIELD_REFS),
        "rating_question_consistency_issue_rows": issue_rows,
        "consistency_issue_count": issue_count,
        "consistency_issue_id_refs": list(P7_R54_OP15_CONSISTENCY_ISSUE_ID_REFS),
        "consistency_issue_kind_refs": list(P7_R54_OP15_CONSISTENCY_ISSUE_KIND_REFS),
        "decision_direction_refs": list(P7_R54_OP15_DECISION_DIRECTION_REFS),
        "red_or_repair_with_no_question_needed_count": sum(1 for row in issue_rows if row.get("issue_id") == "r54_op15_red_or_repair_with_no_question_needed_observation"),
        "repair_required_with_p8_material_candidate_count": sum(1 for row in issue_rows if row.get("issue_id") == "r54_op15_repair_required_with_p8_material_candidate"),
        "pass_with_not_question_repair_required_count": sum(1 for row in issue_rows if row.get("issue_id") == "r54_op15_pass_with_not_question_repair_required"),
        "insufficient_material_with_pass_or_no_execution_blocker_count": sum(1 for row in issue_rows if row.get("issue_id") == "r54_op15_insufficient_material_with_pass_or_no_execution_blocker"),
        "case_ref_set_mismatch_count": sum(1 for row in issue_rows if row.get("issue_id") == "r54_op15_rating_question_case_ref_set_mismatch"),
        "consistency_issue_direction_counts": direction_counts,
        "p5_confirmed_candidate_blocked_by_consistency_issues": issue_count > 0,
        "p5_decision_candidate_not_materialized_here": True,
        "issues_route_to_p5_repair_return_or_inconclusive_later": issue_count > 0,
        "p8_material_candidates_do_not_hide_p5_repair_here": True,
        "ready_for_pause_abort_expiration_protocol": ready,
        "rating_rows_preserved_from_op12": bool(op12_ready and op12.get("actual_rating_rows_materialized_here") is True),
        "question_observation_rows_preserved_from_op14": bool(op14_ready and op14.get("actual_question_need_observation_rows_materialized_here") is True),
        "actual_rating_rows_materialized_here": bool(op12_ready and op12.get("actual_rating_rows_materialized_here") is True),
        "actual_blocker_rows_materialized_here": bool(op14_ready and op14.get("actual_blocker_rows_materialized_here") is True),
        "actual_question_need_observation_rows_materialized_here": bool(op14_ready and op14.get("actual_question_need_observation_rows_materialized_here") is True),
        "actual_review_evidence_complete": False,
        "disposal_verified": False,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_OP15_IMPLEMENTED_STEPS if op14_ready and op12_ready else tuple(op14.get("implemented_steps") or ())),
        "not_yet_implemented_steps": list(P7_R54_OP15_NOT_YET_IMPLEMENTED_STEPS if op14_ready and op12_ready else tuple(op14.get("not_yet_implemented_steps") or ())),
        "first_next_work_ref": P7_R54_OP_NEXT_WORK_AFTER_OP15_REF if ready else P7_R54_OP_NEXT_WORK_AFTER_OP14_REF,
        "next_required_step": "R54-OP-16_pause_abort_expiration_protocol" if ready else P7_R54_OP15_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_operation_no_touch_contract": _operation_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
        "actual_rating_rows_materialized_here": bool(op12_ready and op12.get("actual_rating_rows_materialized_here") is True),
        "actual_blocker_rows_materialized_here": bool(op14_ready and op14.get("actual_blocker_rows_materialized_here") is True),
        "actual_question_need_observation_rows_materialized_here": bool(op14_ready and op14.get("actual_question_need_observation_rows_materialized_here") is True),
    }
    assert_p7_r54_op15_rating_question_consistency_guard_contract(material)
    return material


def assert_p7_r54_op15_rating_question_consistency_guard_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_OPERATION_RATING_QUESTION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS, source="p7_r54_op15_rating_question_consistency_guard")
    _assert_common_operation_contract(
        data,
        schema_version=P7_R54_OPERATION_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        policy_section=P7_R54_OP15_STEP_REF,
        operation_step_ref=P7_R54_OP15_STEP_REF,
        source="p7_r54_op15_rating_question_consistency_guard",
        false_flag_refs=_op15_false_flag_refs(),
    )
    _assert_operation_current_refs(data, source="p7_r54_op15_rating_question_consistency_guard")
    if data.get("op14_schema_version") != P7_R54_OPERATION_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION:
        raise ValueError("R54 OP15 OP14 schema reference changed")
    if data.get("op12_schema_version") != P7_R54_OPERATION_RATING_ROW_NORMALIZATION_SCHEMA_VERSION:
        raise ValueError("R54 OP15 OP12 schema reference changed")
    if data.get("required_case_count") != P7_R51_REQUIRED_CASE_COUNT:
        raise ValueError("R54 OP15 required case count changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=100, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 OP15 open blockers must match blockers")
    rows = [safe_mapping(row) for row in (data.get("rating_question_consistency_issue_rows") or [])]
    for row in rows:
        assert_p7_r54_op15_rating_question_consistency_issue_row_bodyfree_contract(row)
    if data.get("consistency_issue_count") != len(rows):
        raise ValueError("R54 OP15 issue count mismatch")
    if tuple(data.get("consistency_issue_id_refs") or ()) != P7_R54_OP15_CONSISTENCY_ISSUE_ID_REFS:
        raise ValueError("R54 OP15 issue id refs changed")
    if tuple(data.get("consistency_issue_kind_refs") or ()) != P7_R54_OP15_CONSISTENCY_ISSUE_KIND_REFS:
        raise ValueError("R54 OP15 issue kind refs changed")
    if tuple(data.get("decision_direction_refs") or ()) != P7_R54_OP15_DECISION_DIRECTION_REFS:
        raise ValueError("R54 OP15 decision direction refs changed")
    for true_key in (
        "p5_decision_candidate_not_materialized_here", "p8_material_candidates_do_not_hide_p5_repair_here",
        "human_review_completion_claim_blocked_here", "p6_p8_release_promotion_blocked_here",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R54 OP15 must keep {true_key}=True")
    for false_key in ("actual_review_evidence_complete", "disposal_verified"):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 OP15 must keep {false_key}=False")
    ready = data.get("rating_question_consistency_guard_status") == P7_R54_OP15_CONSISTENCY_GUARD_READY_STATUS_REF
    if ready:
        if data.get("op14_consistency_guard_allowed_next") is not True or data.get("op14_next_required_step") != P7_R54_OP15_STEP_REF:
            raise ValueError("R54 OP15 ready guard requires OP14 allowance")
        if data.get("rating_row_count") != P7_R51_REQUIRED_CASE_COUNT or data.get("question_observation_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 OP15 ready guard requires 24 rating and question rows")
        if data.get("consistency_issue_count") != 0 or rows:
            raise ValueError("R54 OP15 ready guard must have zero issues")
        if data.get("ready_for_pause_abort_expiration_protocol") is not True:
            raise ValueError("R54 OP15 ready guard must allow OP16 protocol next")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_OP15_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP15 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_OP15_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP15 not-yet steps changed")
        if data.get("next_required_step") != "R54-OP-16_pause_abort_expiration_protocol":
            raise ValueError("R54 OP15 ready guard must point to OP16")
    else:
        if data.get("rating_question_consistency_guard_status") != P7_R54_OP15_CONSISTENCY_GUARD_BLOCKED_STATUS_REF:
            raise ValueError("R54 OP15 blocked guard status changed")
        if data.get("ready_for_pause_abort_expiration_protocol") is not False:
            raise ValueError("R54 OP15 blocked guard must not allow OP16")
        if not blockers and not rows:
            raise ValueError("R54 OP15 blocked guard must carry blockers or issue rows")
        if data.get("next_required_step") != P7_R54_OP15_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 OP15 blocked guard must point to repair")
    return True


# Compatibility aliases using the detailed-design wording.
build_p7_r54_operation_scope_no_touch_boundary_freeze = build_p7_r54_op00_scope_no_touch_boundary_freeze
assert_p7_r54_operation_scope_no_touch_boundary_freeze_contract = assert_p7_r54_op00_scope_no_touch_boundary_freeze_contract
build_p7_r54_operation_current_snapshot_refreeze = build_p7_r54_op01_operation_current_snapshot_refs_refreeze
assert_p7_r54_operation_current_snapshot_refreeze_contract = assert_p7_r54_op01_operation_current_snapshot_refs_refreeze_contract
build_p7_r54_operation_historical_helper_source_delta_reconcile = build_p7_r54_op02_historical_helper_source_delta_reconcile
assert_p7_r54_operation_historical_helper_source_delta_reconcile_contract = assert_p7_r54_op02_historical_helper_source_delta_reconcile_contract
build_p7_r54_operation_r55_hold_intake = build_p7_r54_op03_r55_hold_intake
assert_p7_r54_operation_r55_hold_intake_contract = assert_p7_r54_op03_r55_hold_intake_contract
build_p7_r54_operation_local_only_preflight = build_p7_r54_op04_local_only_preflight
assert_p7_r54_operation_local_only_preflight_contract = assert_p7_r54_op04_local_only_preflight_contract
build_p7_r54_operation_24_case_manifest_freeze = build_p7_r54_op05_24_case_manifest_freeze
assert_p7_r54_operation_24_case_manifest_freeze_contract = assert_p7_r54_op05_24_case_manifest_freeze_contract
build_p7_r54_operation_body_full_packet_generation_request = build_p7_r54_op06_local_only_body_full_packet_generation_request
assert_p7_r54_operation_body_full_packet_generation_request_contract = assert_p7_r54_op06_local_only_body_full_packet_generation_request_contract
build_p7_r54_operation_packet_generation_local_operation = build_p7_r54_op07_packet_generation_local_operation
assert_p7_r54_operation_packet_generation_local_operation_contract = assert_p7_r54_op07_packet_generation_local_operation_contract
build_p7_r54_operation_packet_completeness_export_denylist_scan = build_p7_r54_op08_packet_completeness_export_denylist_scan
assert_p7_r54_operation_packet_completeness_export_denylist_scan_contract = assert_p7_r54_op08_packet_completeness_export_denylist_scan_contract
build_p7_r54_operation_reviewer_instruction_rating_form_freeze = build_p7_r54_op09_reviewer_instruction_rating_form_freeze
assert_p7_r54_operation_reviewer_instruction_rating_form_freeze_contract = assert_p7_r54_op09_reviewer_instruction_rating_form_freeze_contract
build_p7_r54_operation_actual_human_review_operation_state_capture = build_p7_r54_op10_actual_human_review_operation_state_capture
assert_p7_r54_operation_actual_human_review_operation_state_capture_contract = assert_p7_r54_op10_actual_human_review_operation_state_capture_contract
build_p7_r54_operation_sanitized_review_result_capture = build_p7_r54_op11_sanitized_review_result_capture
assert_p7_r54_operation_sanitized_review_result_capture_contract = assert_p7_r54_op11_sanitized_review_result_capture_contract
build_p7_r54_operation_rating_row_normalization = build_p7_r54_op12_rating_row_normalization
assert_p7_r54_operation_rating_row_normalization_contract = assert_p7_r54_op12_rating_row_normalization_contract
build_p7_r54_operation_readfeel_blocker_execution_blocker_ingestion = build_p7_r54_op13_readfeel_blocker_execution_blocker_ingestion
assert_p7_r54_operation_readfeel_blocker_execution_blocker_ingestion_contract = assert_p7_r54_op13_readfeel_blocker_execution_blocker_ingestion_contract

# Body-free explicit aliases used by operation-step tests and handoff code.
build_p7_r54_operation_scope_no_touch_boundary_freeze_bodyfree = build_p7_r54_operation_scope_no_touch_boundary_freeze
assert_p7_r54_operation_scope_no_touch_boundary_freeze_bodyfree_contract = assert_p7_r54_operation_scope_no_touch_boundary_freeze_contract
build_p7_r54_operation_current_snapshot_refreeze_bodyfree = build_p7_r54_operation_current_snapshot_refreeze
assert_p7_r54_operation_current_snapshot_refreeze_bodyfree_contract = assert_p7_r54_operation_current_snapshot_refreeze_contract
build_p7_r54_operation_historical_helper_source_delta_reconcile_bodyfree = build_p7_r54_operation_historical_helper_source_delta_reconcile
assert_p7_r54_operation_historical_helper_source_delta_reconcile_bodyfree_contract = assert_p7_r54_operation_historical_helper_source_delta_reconcile_contract
build_p7_r54_operation_r55_hold_intake_bodyfree = build_p7_r54_operation_r55_hold_intake
assert_p7_r54_operation_r55_hold_intake_bodyfree_contract = assert_p7_r54_operation_r55_hold_intake_contract
build_p7_r54_operation_local_only_preflight_bodyfree = build_p7_r54_operation_local_only_preflight
assert_p7_r54_operation_local_only_preflight_bodyfree_contract = assert_p7_r54_operation_local_only_preflight_contract
build_p7_r54_operation_24_case_manifest_freeze_bodyfree = build_p7_r54_operation_24_case_manifest_freeze
assert_p7_r54_operation_24_case_manifest_freeze_bodyfree_contract = assert_p7_r54_operation_24_case_manifest_freeze_contract
build_p7_r54_operation_body_full_packet_generation_request_bodyfree = build_p7_r54_operation_body_full_packet_generation_request
assert_p7_r54_operation_body_full_packet_generation_request_bodyfree_contract = assert_p7_r54_operation_body_full_packet_generation_request_contract
build_p7_r54_operation_packet_generation_local_operation_bodyfree = build_p7_r54_operation_packet_generation_local_operation
assert_p7_r54_operation_packet_generation_local_operation_bodyfree_contract = assert_p7_r54_operation_packet_generation_local_operation_contract
build_p7_r54_operation_packet_completeness_export_denylist_scan_bodyfree = build_p7_r54_operation_packet_completeness_export_denylist_scan
assert_p7_r54_operation_packet_completeness_export_denylist_scan_bodyfree_contract = assert_p7_r54_operation_packet_completeness_export_denylist_scan_contract
build_p7_r54_operation_reviewer_instruction_rating_form_freeze_bodyfree = build_p7_r54_operation_reviewer_instruction_rating_form_freeze
assert_p7_r54_operation_reviewer_instruction_rating_form_freeze_bodyfree_contract = assert_p7_r54_operation_reviewer_instruction_rating_form_freeze_contract
build_p7_r54_operation_actual_human_review_operation_state_capture_bodyfree = build_p7_r54_operation_actual_human_review_operation_state_capture
assert_p7_r54_operation_actual_human_review_operation_state_capture_bodyfree_contract = assert_p7_r54_operation_actual_human_review_operation_state_capture_contract
build_p7_r54_operation_sanitized_review_result_capture_bodyfree = build_p7_r54_operation_sanitized_review_result_capture
assert_p7_r54_operation_sanitized_review_result_capture_bodyfree_contract = assert_p7_r54_operation_sanitized_review_result_capture_contract
build_p7_r54_operation_rating_row_normalization_bodyfree = build_p7_r54_operation_rating_row_normalization
assert_p7_r54_operation_rating_row_normalization_bodyfree_contract = assert_p7_r54_operation_rating_row_normalization_contract
build_p7_r54_operation_readfeel_blocker_execution_blocker_ingestion_bodyfree = build_p7_r54_operation_readfeel_blocker_execution_blocker_ingestion
assert_p7_r54_operation_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract = assert_p7_r54_operation_readfeel_blocker_execution_blocker_ingestion_contract
build_p7_r54_operation_question_need_observation_normalization = build_p7_r54_op14_question_need_observation_normalization
assert_p7_r54_operation_question_need_observation_normalization_contract = assert_p7_r54_op14_question_need_observation_normalization_contract
build_p7_r54_operation_question_need_observation_row_bodyfree = _op14_question_observation_row_from_sanitized_row
assert_p7_r54_operation_question_need_observation_row_bodyfree_contract = assert_p7_r54_op14_question_need_observation_row_bodyfree_contract
build_p7_r54_operation_rating_question_consistency_guard = build_p7_r54_op15_rating_question_consistency_guard
assert_p7_r54_operation_rating_question_consistency_guard_contract = assert_p7_r54_op15_rating_question_consistency_guard_contract
build_p7_r54_operation_rating_question_consistency_issue_row_bodyfree = build_p7_r54_op15_rating_question_consistency_issue_row_bodyfree
assert_p7_r54_operation_rating_question_consistency_issue_row_bodyfree_contract = assert_p7_r54_op15_rating_question_consistency_issue_row_bodyfree_contract
build_p7_r54_operation_question_need_observation_normalization_bodyfree = build_p7_r54_operation_question_need_observation_normalization
assert_p7_r54_operation_question_need_observation_normalization_bodyfree_contract = assert_p7_r54_operation_question_need_observation_normalization_contract
build_p7_r54_operation_rating_question_consistency_guard_bodyfree = build_p7_r54_operation_rating_question_consistency_guard
assert_p7_r54_operation_rating_question_consistency_guard_bodyfree_contract = assert_p7_r54_operation_rating_question_consistency_guard_contract


# R54-OP-16 / R54-OP-17 operation-layer additions.
# These helpers preserve the local-only/body-free boundary: they do not run a
# human review, do not delete local files by themselves, and never export packet
# contents, local paths, body hashes, reviewer notes, or question text.
P7_R54_OPERATION_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_pause_abort_expiration_protocol.bodyfree.v1"
)
P7_R54_OPERATION_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_purge_disposal_receipt.bodyfree.v1"
)

P7_R54_OP16_STEP_REF: Final = "R54-OP-16_pause_abort_expiration_protocol"
P7_R54_OP17_STEP_REF: Final = "R54-OP-17_purge_disposal_receipt"
P7_R54_OP18_STEP_REF: Final = "R54-OP-18_bodyfree_post_review_summary"
P7_R54_OP16_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "pause_abort_expiration_protocol_repair_before_purge_disposal_receipt"
P7_R54_OP16_PAUSED_NEXT_REQUIRED_STEP_REF: Final = "resume_or_abort_r54_op16_paused_local_only_review_before_purge_disposal_receipt"
P7_R54_OP17_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "purge_disposal_receipt_repair_before_bodyfree_post_review_summary"
P7_R54_OP_NEXT_WORK_AFTER_OP16_REF: Final = "r54_op17_purge_disposal_receipt_after_pause_abort_expiration_protocol"
P7_R54_OP_NEXT_WORK_AFTER_OP17_REF: Final = "r54_op18_bodyfree_post_review_summary_after_purge_disposal_receipt"

P7_R54_OP16_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_OP15_IMPLEMENTED_STEPS,
    P7_R54_OP16_STEP_REF,
)
P7_R54_OP16_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = tuple(
    step for step in P7_R54_OP15_NOT_YET_IMPLEMENTED_STEPS if step != P7_R54_OP16_STEP_REF
)
P7_R54_OP17_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_OP16_IMPLEMENTED_STEPS,
    P7_R54_OP17_STEP_REF,
)
P7_R54_OP17_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = tuple(
    step for step in P7_R54_OP16_NOT_YET_IMPLEMENTED_STEPS if step != P7_R54_OP17_STEP_REF
)

P7_R54_OP16_PROTOCOL_READY_STATUS_REF: Final = "READY_FOR_PURGE_DISPOSAL_RECEIPT"
P7_R54_OP16_PROTOCOL_PAUSED_STATUS_REF: Final = "PAUSED_NO_HANDOFF_LOCAL_ONLY"
P7_R54_OP16_PROTOCOL_ABORTED_STATUS_REF: Final = "ABORTED_PURGE_REQUIRED"
P7_R54_OP16_PROTOCOL_EXPIRED_STATUS_REF: Final = "EXPIRED_PURGE_REQUIRED"
P7_R54_OP16_PROTOCOL_RATING_INCOMPLETE_STATUS_REF: Final = "RATING_INCOMPLETE_PURGE_REQUIRED"
P7_R54_OP16_PROTOCOL_BLOCKED_STATUS_REF: Final = "BLOCKED_BY_OP15_CONSISTENCY_GUARD"
P7_R54_OP16_PROTOCOL_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_OP16_PROTOCOL_READY_STATUS_REF,
    P7_R54_OP16_PROTOCOL_PAUSED_STATUS_REF,
    P7_R54_OP16_PROTOCOL_ABORTED_STATUS_REF,
    P7_R54_OP16_PROTOCOL_EXPIRED_STATUS_REF,
    P7_R54_OP16_PROTOCOL_RATING_INCOMPLETE_STATUS_REF,
    P7_R54_OP16_PROTOCOL_BLOCKED_STATUS_REF,
)
P7_R54_OP16_PROTOCOL_REF: Final = "r54_pause_abort_expiration_protocol_bodyfree_20260625"
P7_R54_OP16_READY_REASON_REF: Final = "r54_pause_abort_expiration_protocol_ready_bodyfree"
P7_R54_OP16_PAUSED_REASON_REF: Final = "r54_review_paused_without_handoff_bodyfree"
P7_R54_OP16_ABORTED_REASON_REF: Final = "r54_review_aborted_p5_inconclusive_purge_required_bodyfree"
P7_R54_OP16_EXPIRED_REASON_REF: Final = "r54_review_expired_p5_inconclusive_purge_required_bodyfree"
P7_R54_OP16_RATING_INCOMPLETE_REASON_REF: Final = "r54_review_rating_incomplete_p5_inconclusive_purge_required_bodyfree"
P7_R54_OP16_BLOCKED_REASON_REF: Final = "r54_pause_abort_expiration_protocol_blocked_by_op15_bodyfree"
P7_R54_OP16_SESSION_EVENT_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_OP10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF,
    P7_R54_OP10_REVIEW_PAUSED_STATUS_REF,
    P7_R54_OP10_REVIEW_ABORTED_STATUS_REF,
    P7_R54_OP10_REVIEW_EXPIRED_STATUS_REF,
    "rating_incomplete_purge_required",
)
P7_R54_OP16_REQUIRED_LOCAL_DELETE_TARGET_REFS: Final[tuple[str, ...]] = (
    "body_full_packet",
    "reviewer_notes",
    "temporary_form",
)
P7_R54_OP16_P5_DECISION_DIRECTION_REFS: Final[tuple[str, ...]] = (
    "no_p5_decision_materialized_here",
    "p5_inconclusive_due_to_pause_without_handoff",
    "p5_inconclusive_due_to_abort_or_expiration",
    "p5_inconclusive_due_to_rating_incomplete",
    "p5_inconclusive_due_to_op15_not_ready",
)

P7_R54_OP17_DISPOSAL_VERIFIED_STATUS_REF: Final = "DISPOSAL_VERIFIED"
P7_R54_OP17_DISPOSAL_BLOCKED_STATUS_REF: Final = "R54_OPERATION_BLOCKED_DISPOSAL"
P7_R54_OP17_DISPOSAL_RECEIPT_REF: Final = "r54_bodyfree_purge_disposal_receipt_verified_20260625"
P7_R54_OP17_READY_REASON_REF: Final = "r54_purge_disposal_receipt_verified_bodyfree"
P7_R54_OP17_BLOCKED_REASON_REF: Final = "r54_purge_disposal_receipt_blocked_bodyfree"
P7_R54_OP17_REMOVAL_TARGET_REFS: Final[tuple[str, ...]] = P7_R54_OP16_REQUIRED_LOCAL_DELETE_TARGET_REFS

P7_R54_OPERATION_PAUSE_ABORT_EXPIRATION_PROTOCOL_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op15_schema_version", "op15_material_ref", "op15_next_required_step", "op15_consistency_guard_status",
    "op15_ready_for_pause_abort_expiration_protocol", "op15_consistency_issue_count", "operation_current_refs",
    "operation_current_ref_count", "actual_review_basis_ref", "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis", "required_case_count", "rating_row_count",
    "question_observation_row_count", "consistency_issue_count", "pause_abort_expiration_protocol_status",
    "pause_abort_expiration_protocol_ref", "pause_abort_expiration_protocol_reason_refs", "review_operation_status_ref",
    "review_operation_status_refs", "review_operation_status_allowed", "purge_trigger_refs", "purge_trigger_ref_count",
    "review_session_cancelled_is_purge_trigger", "retention_deadline_reached_is_purge_trigger",
    "required_local_delete_target_refs", "required_local_delete_target_ref_count", "body_full_packet_retention_hours",
    "reviewer_notes_retention_after_rating_hours", "body_full_material_must_not_remain_after_cancel_or_deadline",
    "reviewer_notes_must_not_remain_after_cancel_or_deadline", "temporary_form_must_not_remain_after_cancel_or_deadline",
    "purge_before_handoff_required", "handoff_allowed_before_purge", "r52_reintake_handoff_allowed_before_purge",
    "review_paused_without_handoff", "review_aborted_or_expired", "p5_decision_direction_ref",
    "p5_decision_materialized_here", "p5_inconclusive_direction_only_not_decision_materialized",
    "ready_for_purge_disposal_receipt", "purge_disposal_receipt_allowed_next", "disposal_receipt_allowed_next",
    "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here", "actual_review_evidence_complete", "disposal_verified",
    "actual_disposal_receipt_materialized_here", "human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here", "execution_blocker_ids", "open_execution_blocker_ids", "implemented_steps",
    "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract",
    "r54_operation_no_touch_contract", "body_free_markers", "body_free", "question_text_included", "draft_question_text_included",
    "local_path_included", *P7_R54_OPERATION_FALSE_FLAG_REFS,
)

P7_R54_OPERATION_PURGE_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op16_schema_version", "op16_material_ref", "op16_next_required_step", "op16_pause_abort_expiration_protocol_status",
    "op16_purge_disposal_receipt_allowed_next", "op16_ready_for_purge_disposal_receipt", "operation_current_refs",
    "operation_current_ref_count", "actual_review_basis_ref", "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis", "required_case_count", "rating_row_count",
    "question_observation_row_count", "purge_disposal_receipt_status", "purge_disposal_receipt_ref",
    "purge_disposal_receipt_reason_refs", "removal_target_refs", "removal_target_ref_count", "body_removed",
    "reviewer_notes_removed", "temporary_form_removed", "all_required_local_targets_removed", "local_packet_exported",
    "content_hash_of_body_stored", "body_full_packet_zip_inclusion_allowed", "reviewer_notes_export_allowed",
    "body_full_packet_export_allowed", "disposal_verified", "actual_disposal_receipt_materialized_here",
    "actual_disposal_run_here", "disposal_failure_decision_ref", "body_free_post_review_summary_allowed_next",
    "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here", "actual_review_evidence_complete",
    "human_review_completion_claim_blocked_here", "p6_p8_release_promotion_blocked_here", "execution_blocker_ids",
    "open_execution_blocker_ids", "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step",
    "public_contract", "r54_operation_no_touch_contract", "body_free_markers", "body_free", "question_text_included",
    "draft_question_text_included", "local_path_included", *P7_R54_OPERATION_FALSE_FLAG_REFS,
)


def _op16_false_flag_refs() -> tuple[str, ...]:
    return tuple(
        key for key in P7_R54_OPERATION_FALSE_FLAG_REFS
        if key not in {
            "actual_rating_rows_materialized_here",
            "actual_blocker_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
        }
    )


def _op17_false_flag_refs() -> tuple[str, ...]:
    return tuple(
        key for key in P7_R54_OPERATION_FALSE_FLAG_REFS
        if key not in {
            "actual_rating_rows_materialized_here",
            "actual_blocker_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "disposal_verified",
        }
    )


def _op16_protocol_decision(review_status: str, *, op15_ready: bool, rating_row_count: int) -> tuple[str, str, str, bool, bool, bool]:
    if not op15_ready:
        return (
            P7_R54_OP16_PROTOCOL_BLOCKED_STATUS_REF,
            P7_R54_OP16_BLOCKED_REASON_REF,
            "op15_consistency_guard_not_ready_for_pause_abort_expiration_protocol",
            False,
            False,
            False,
        )
    if review_status == P7_R54_OP10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF:
        if rating_row_count != P7_R51_REQUIRED_CASE_COUNT:
            return (
                P7_R54_OP16_PROTOCOL_RATING_INCOMPLETE_STATUS_REF,
                P7_R54_OP16_RATING_INCOMPLETE_REASON_REF,
                "rating_row_count_incomplete_before_disposal",
                True,
                False,
                True,
            )
        return (P7_R54_OP16_PROTOCOL_READY_STATUS_REF, P7_R54_OP16_READY_REASON_REF, "", True, False, False)
    if review_status == P7_R54_OP10_REVIEW_PAUSED_STATUS_REF:
        return (P7_R54_OP16_PROTOCOL_PAUSED_STATUS_REF, P7_R54_OP16_PAUSED_REASON_REF, "", False, True, False)
    if review_status == P7_R54_OP10_REVIEW_ABORTED_STATUS_REF:
        return (P7_R54_OP16_PROTOCOL_ABORTED_STATUS_REF, P7_R54_OP16_ABORTED_REASON_REF, "", True, False, True)
    if review_status == P7_R54_OP10_REVIEW_EXPIRED_STATUS_REF:
        return (P7_R54_OP16_PROTOCOL_EXPIRED_STATUS_REF, P7_R54_OP16_EXPIRED_REASON_REF, "", True, False, True)
    if review_status == "rating_incomplete_purge_required":
        return (
            P7_R54_OP16_PROTOCOL_RATING_INCOMPLETE_STATUS_REF,
            P7_R54_OP16_RATING_INCOMPLETE_REASON_REF,
            "rating_incomplete_purge_required",
            True,
            False,
            True,
        )
    return (
        P7_R54_OP16_PROTOCOL_BLOCKED_STATUS_REF,
        P7_R54_OP16_BLOCKED_REASON_REF,
        "review_operation_status_not_allowed_for_pause_abort_expiration_protocol",
        False,
        False,
        False,
    )


def build_p7_r54_op16_pause_abort_expiration_protocol(
    *,
    rating_question_consistency_guard: Mapping[str, Any] | None = None,
    review_operation_status_ref: Any = P7_R54_OP10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF,
    session_event_status_ref: Any | None = None,
    material_id: Any = "p7_r54_operation_pause_abort_expiration_protocol",
) -> dict[str, Any]:
    """Build R54-OP-16 body-free pause / abort / expiration protocol."""
    op15 = safe_mapping(rating_question_consistency_guard) if rating_question_consistency_guard is not None else build_p7_r54_op15_rating_question_consistency_guard()
    assert_p7_r54_op15_rating_question_consistency_guard_contract(op15)
    if session_event_status_ref is not None:
        review_operation_status_ref = session_event_status_ref
    review_status = clean_identifier(review_operation_status_ref, default="", max_length=180)
    review_status_allowed = review_status in P7_R54_OP16_SESSION_EVENT_STATUS_REFS
    op15_ready = bool(
        op15.get("rating_question_consistency_guard_status") == P7_R54_OP15_CONSISTENCY_GUARD_READY_STATUS_REF
        and op15.get("ready_for_pause_abort_expiration_protocol") is True
        and op15.get("next_required_step") == P7_R54_OP16_STEP_REF
        and not op15.get("open_execution_blocker_ids")
    )
    rating_row_count = int(op15.get("rating_row_count") or 0) if op15_ready else 0
    question_row_count = int(op15.get("question_observation_row_count") or 0) if op15_ready else 0
    status, reason_ref, blocker_ref, purge_allowed, paused, abort_or_expired = _op16_protocol_decision(
        review_status,
        op15_ready=op15_ready and review_status_allowed,
        rating_row_count=rating_row_count,
    )
    blockers = dedupe_identifiers([blocker_ref] if blocker_ref else [], limit=100, max_length=180)
    p5_decision_direction_ref = "no_p5_decision_materialized_here"
    if status == P7_R54_OP16_PROTOCOL_PAUSED_STATUS_REF:
        p5_decision_direction_ref = "p5_inconclusive_due_to_pause_without_handoff"
    elif status in (P7_R54_OP16_PROTOCOL_ABORTED_STATUS_REF, P7_R54_OP16_PROTOCOL_EXPIRED_STATUS_REF):
        p5_decision_direction_ref = "p5_inconclusive_due_to_abort_or_expiration"
    elif status == P7_R54_OP16_PROTOCOL_RATING_INCOMPLETE_STATUS_REF:
        p5_decision_direction_ref = "p5_inconclusive_due_to_rating_incomplete"
    elif status == P7_R54_OP16_PROTOCOL_BLOCKED_STATUS_REF:
        p5_decision_direction_ref = "p5_inconclusive_due_to_op15_not_ready"
    ready_for_disposal = purge_allowed and not blockers
    material = {
        "schema_version": P7_R54_OPERATION_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_OPERATION_REENTRY_STEP,
        "scope": P7_R54_OPERATION_REENTRY_SCOPE,
        "policy_kind": P7_R54_OPERATION_REENTRY_POLICY_KIND,
        "policy_section": P7_R54_OP16_STEP_REF,
        "operation_step_ref": P7_R54_OP16_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_operation_pause_abort_expiration_protocol", max_length=220),
        "review_session_id": _safe_review_session_id(op15.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op15_schema_version": P7_R54_OPERATION_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        "op15_material_ref": clean_identifier(op15.get("material_id"), default="p7_r54_operation_rating_question_consistency_guard", max_length=220),
        "op15_next_required_step": clean_identifier(op15.get("next_required_step"), default="", max_length=180),
        "op15_consistency_guard_status": clean_identifier(op15.get("rating_question_consistency_guard_status"), default=P7_R54_OP15_CONSISTENCY_GUARD_BLOCKED_STATUS_REF, max_length=180),
        "op15_ready_for_pause_abort_expiration_protocol": op15_ready,
        "op15_consistency_issue_count": int(op15.get("consistency_issue_count") or 0),
        "operation_current_refs": dict(P7_R54_OPERATION_CURRENT_REFS),
        "operation_current_ref_count": len(P7_R54_OPERATION_CURRENT_REFS),
        "actual_review_basis_ref": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "rating_row_count": rating_row_count,
        "question_observation_row_count": question_row_count,
        "consistency_issue_count": int(op15.get("consistency_issue_count") or 0),
        "pause_abort_expiration_protocol_status": status,
        "pause_abort_expiration_protocol_ref": P7_R54_OP16_PROTOCOL_REF if status != P7_R54_OP16_PROTOCOL_BLOCKED_STATUS_REF else "pause_abort_expiration_protocol_not_ready_bodyfree",
        "pause_abort_expiration_protocol_reason_refs": dedupe_identifiers([reason_ref, *blockers], limit=100, max_length=180),
        "review_operation_status_ref": review_status,
        "review_operation_status_refs": list(P7_R54_OP16_SESSION_EVENT_STATUS_REFS),
        "review_operation_status_allowed": review_status_allowed,
        "purge_trigger_refs": list(P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS),
        "purge_trigger_ref_count": len(P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS),
        "review_session_cancelled_is_purge_trigger": "review_session_cancelled" in P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS,
        "retention_deadline_reached_is_purge_trigger": "retention_deadline_reached" in P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS,
        "required_local_delete_target_refs": list(P7_R54_OP16_REQUIRED_LOCAL_DELETE_TARGET_REFS),
        "required_local_delete_target_ref_count": len(P7_R54_OP16_REQUIRED_LOCAL_DELETE_TARGET_REFS),
        "body_full_packet_retention_hours": P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
        "reviewer_notes_retention_after_rating_hours": P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
        "body_full_material_must_not_remain_after_cancel_or_deadline": True,
        "reviewer_notes_must_not_remain_after_cancel_or_deadline": True,
        "temporary_form_must_not_remain_after_cancel_or_deadline": True,
        "purge_before_handoff_required": True,
        "handoff_allowed_before_purge": False,
        "r52_reintake_handoff_allowed_before_purge": False,
        "review_paused_without_handoff": paused,
        "review_aborted_or_expired": abort_or_expired,
        "p5_decision_direction_ref": p5_decision_direction_ref,
        "p5_decision_materialized_here": False,
        "p5_inconclusive_direction_only_not_decision_materialized": p5_decision_direction_ref != "no_p5_decision_materialized_here",
        "ready_for_purge_disposal_receipt": ready_for_disposal,
        "purge_disposal_receipt_allowed_next": ready_for_disposal,
        "disposal_receipt_allowed_next": ready_for_disposal,
        "actual_rating_rows_materialized_here": op15_ready and rating_row_count == P7_R51_REQUIRED_CASE_COUNT,
        "actual_blocker_rows_materialized_here": bool(op15.get("actual_blocker_rows_materialized_here") is True) if op15_ready else False,
        "actual_question_need_observation_rows_materialized_here": bool(op15.get("actual_question_need_observation_rows_materialized_here") is True) if op15_ready else False,
        "actual_review_evidence_complete": False,
        "disposal_verified": False,
        "actual_disposal_receipt_materialized_here": False,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "implemented_steps": list(P7_R54_OP16_IMPLEMENTED_STEPS if status != P7_R54_OP16_PROTOCOL_BLOCKED_STATUS_REF else tuple(op15.get("implemented_steps") or ())),
        "not_yet_implemented_steps": list(P7_R54_OP16_NOT_YET_IMPLEMENTED_STEPS if status != P7_R54_OP16_PROTOCOL_BLOCKED_STATUS_REF else tuple(op15.get("not_yet_implemented_steps") or ())),
        "first_next_work_ref": P7_R54_OP_NEXT_WORK_AFTER_OP16_REF if ready_for_disposal else P7_R54_OP_NEXT_WORK_AFTER_OP15_REF,
        "next_required_step": P7_R54_OP17_STEP_REF if ready_for_disposal else (P7_R54_OP16_PAUSED_NEXT_REQUIRED_STEP_REF if paused else P7_R54_OP16_BLOCKED_NEXT_REQUIRED_STEP_REF),
        "public_contract": public_contract_flags(),
        "r54_operation_no_touch_contract": _operation_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
        "actual_rating_rows_materialized_here": op15_ready and rating_row_count == P7_R51_REQUIRED_CASE_COUNT,
        "actual_blocker_rows_materialized_here": bool(op15.get("actual_blocker_rows_materialized_here") is True) if op15_ready else False,
        "actual_question_need_observation_rows_materialized_here": bool(op15.get("actual_question_need_observation_rows_materialized_here") is True) if op15_ready else False,
    }
    assert_p7_r54_op16_pause_abort_expiration_protocol_contract(material)
    return material


def assert_p7_r54_op16_pause_abort_expiration_protocol_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_OPERATION_PAUSE_ABORT_EXPIRATION_PROTOCOL_REQUIRED_FIELD_REFS, source="p7_r54_op16_pause_abort_expiration_protocol")
    _assert_common_operation_contract(
        data,
        schema_version=P7_R54_OPERATION_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION,
        policy_section=P7_R54_OP16_STEP_REF,
        operation_step_ref=P7_R54_OP16_STEP_REF,
        source="p7_r54_op16_pause_abort_expiration_protocol",
        false_flag_refs=_op16_false_flag_refs(),
    )
    _assert_operation_current_refs(data, source="p7_r54_op16_pause_abort_expiration_protocol")
    if data.get("op15_schema_version") != P7_R54_OPERATION_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION:
        raise ValueError("R54 OP16 OP15 schema reference changed")
    if tuple(data.get("review_operation_status_refs") or ()) != P7_R54_OP16_SESSION_EVENT_STATUS_REFS:
        raise ValueError("R54 OP16 review operation status refs changed")
    if tuple(data.get("purge_trigger_refs") or ()) != P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS:
        raise ValueError("R54 OP16 purge trigger refs changed")
    if data.get("review_session_cancelled_is_purge_trigger") is not True or data.get("retention_deadline_reached_is_purge_trigger") is not True:
        raise ValueError("R54 OP16 must keep cancel/deadline as purge triggers")
    if tuple(data.get("required_local_delete_target_refs") or ()) != P7_R54_OP16_REQUIRED_LOCAL_DELETE_TARGET_REFS:
        raise ValueError("R54 OP16 delete target refs changed")
    for true_key in (
        "body_full_material_must_not_remain_after_cancel_or_deadline",
        "reviewer_notes_must_not_remain_after_cancel_or_deadline",
        "temporary_form_must_not_remain_after_cancel_or_deadline",
        "purge_before_handoff_required",
        "human_review_completion_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R54 OP16 must keep {true_key}=True")
    for false_key in (
        "handoff_allowed_before_purge",
        "r52_reintake_handoff_allowed_before_purge",
        "p5_decision_materialized_here",
        "actual_review_evidence_complete",
        "disposal_verified",
        "actual_disposal_receipt_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 OP16 must keep {false_key}=False")
    status = data.get("pause_abort_expiration_protocol_status")
    if status == P7_R54_OP16_PROTOCOL_READY_STATUS_REF:
        if data.get("ready_for_purge_disposal_receipt") is not True or data.get("purge_disposal_receipt_allowed_next") is not True:
            raise ValueError("R54 OP16 ready must allow OP17 only")
        if data.get("next_required_step") != P7_R54_OP17_STEP_REF:
            raise ValueError("R54 OP16 ready must point to OP17")
        if data.get("open_execution_blocker_ids"):
            raise ValueError("R54 OP16 ready must not carry blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_OP16_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP16 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_OP16_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP16 not-yet steps changed")
    elif status in (P7_R54_OP16_PROTOCOL_ABORTED_STATUS_REF, P7_R54_OP16_PROTOCOL_EXPIRED_STATUS_REF, P7_R54_OP16_PROTOCOL_RATING_INCOMPLETE_STATUS_REF):
        if data.get("ready_for_purge_disposal_receipt") is not True or data.get("next_required_step") != P7_R54_OP17_STEP_REF:
            raise ValueError("R54 OP16 abort/expire/incomplete must route to purge")
        if data.get("p5_inconclusive_direction_only_not_decision_materialized") is not True:
            raise ValueError("R54 OP16 abort/expire/incomplete must mark inconclusive direction only")
    elif status == P7_R54_OP16_PROTOCOL_PAUSED_STATUS_REF:
        if data.get("review_paused_without_handoff") is not True:
            raise ValueError("R54 OP16 paused must remain without handoff")
        if data.get("ready_for_purge_disposal_receipt") is not False or data.get("next_required_step") != P7_R54_OP16_PAUSED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 OP16 paused next step changed")
    else:
        if status != P7_R54_OP16_PROTOCOL_BLOCKED_STATUS_REF:
            raise ValueError("R54 OP16 unknown protocol status")
        if data.get("ready_for_purge_disposal_receipt") is not False or data.get("next_required_step") != P7_R54_OP16_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 OP16 blocked next step changed")
        if not data.get("open_execution_blocker_ids"):
            raise ValueError("R54 OP16 blocked must carry blockers")
    return True


def build_p7_r54_op17_purge_disposal_receipt(
    *,
    pause_abort_expiration_protocol: Mapping[str, Any] | None = None,
    body_removed: bool = False,
    reviewer_notes_removed: bool = False,
    temporary_form_removed: bool = False,
    local_packet_exported: bool = False,
    content_hash_of_body_stored: bool = False,
    disposal_receipt_ref: Any = "",
    material_id: Any = "p7_r54_operation_purge_disposal_receipt",
) -> dict[str, Any]:
    """Build R54-OP-17 body-free purge / disposal receipt."""
    op16 = safe_mapping(pause_abort_expiration_protocol) if pause_abort_expiration_protocol is not None else build_p7_r54_op16_pause_abort_expiration_protocol()
    assert_p7_r54_op16_pause_abort_expiration_protocol_contract(op16)
    op16_ready = bool(
        op16.get("ready_for_purge_disposal_receipt") is True
        and op16.get("purge_disposal_receipt_allowed_next") is True
        and op16.get("next_required_step") == P7_R54_OP17_STEP_REF
        and not op16.get("open_execution_blocker_ids")
    )
    receipt_ref = clean_identifier(disposal_receipt_ref, default="", max_length=220)
    blockers: list[str] = []
    if not op16_ready:
        blockers.append("pause_abort_expiration_protocol_not_ready_for_disposal_receipt")
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
    if receipt_ref != P7_R54_OP17_DISPOSAL_RECEIPT_REF:
        blockers.append("disposal_receipt_ref_not_verified")
    blockers = dedupe_identifiers(blockers, limit=100, max_length=180)
    ready = op16_ready and not blockers
    material = {
        "schema_version": P7_R54_OPERATION_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_OPERATION_REENTRY_STEP,
        "scope": P7_R54_OPERATION_REENTRY_SCOPE,
        "policy_kind": P7_R54_OPERATION_REENTRY_POLICY_KIND,
        "policy_section": P7_R54_OP17_STEP_REF,
        "operation_step_ref": P7_R54_OP17_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_operation_purge_disposal_receipt", max_length=220),
        "review_session_id": _safe_review_session_id(op16.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op16_schema_version": P7_R54_OPERATION_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION,
        "op16_material_ref": clean_identifier(op16.get("material_id"), default="p7_r54_operation_pause_abort_expiration_protocol", max_length=220),
        "op16_next_required_step": clean_identifier(op16.get("next_required_step"), default="", max_length=180),
        "op16_pause_abort_expiration_protocol_status": clean_identifier(op16.get("pause_abort_expiration_protocol_status"), default=P7_R54_OP16_PROTOCOL_BLOCKED_STATUS_REF, max_length=180),
        "op16_purge_disposal_receipt_allowed_next": op16_ready,
        "op16_ready_for_purge_disposal_receipt": op16_ready,
        "operation_current_refs": dict(P7_R54_OPERATION_CURRENT_REFS),
        "operation_current_ref_count": len(P7_R54_OPERATION_CURRENT_REFS),
        "actual_review_basis_ref": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "rating_row_count": int(op16.get("rating_row_count") or 0) if op16_ready else 0,
        "question_observation_row_count": int(op16.get("question_observation_row_count") or 0) if op16_ready else 0,
        "purge_disposal_receipt_status": P7_R54_OP17_DISPOSAL_VERIFIED_STATUS_REF if ready else P7_R54_OP17_DISPOSAL_BLOCKED_STATUS_REF,
        "purge_disposal_receipt_ref": receipt_ref if ready else "purge_disposal_receipt_not_verified_bodyfree",
        "purge_disposal_receipt_reason_refs": [P7_R54_OP17_READY_REASON_REF] if ready else dedupe_identifiers([P7_R54_OP17_BLOCKED_REASON_REF, *blockers], limit=100, max_length=180),
        "removal_target_refs": list(P7_R54_OP17_REMOVAL_TARGET_REFS),
        "removal_target_ref_count": len(P7_R54_OP17_REMOVAL_TARGET_REFS),
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
        "disposal_failure_decision_ref": "" if ready else P7_R54_OP17_DISPOSAL_BLOCKED_STATUS_REF,
        "body_free_post_review_summary_allowed_next": ready,
        "actual_rating_rows_materialized_here": bool(op16.get("actual_rating_rows_materialized_here") is True) if op16_ready else False,
        "actual_blocker_rows_materialized_here": bool(op16.get("actual_blocker_rows_materialized_here") is True) if op16_ready else False,
        "actual_question_need_observation_rows_materialized_here": bool(op16.get("actual_question_need_observation_rows_materialized_here") is True) if op16_ready else False,
        "actual_review_evidence_complete": False,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        "implemented_steps": list(P7_R54_OP17_IMPLEMENTED_STEPS if ready else tuple(op16.get("implemented_steps") or ())),
        "not_yet_implemented_steps": list(P7_R54_OP17_NOT_YET_IMPLEMENTED_STEPS if ready else tuple(op16.get("not_yet_implemented_steps") or ())),
        "first_next_work_ref": P7_R54_OP_NEXT_WORK_AFTER_OP17_REF if ready else P7_R54_OP_NEXT_WORK_AFTER_OP16_REF,
        "next_required_step": P7_R54_OP18_STEP_REF if ready else P7_R54_OP17_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_operation_no_touch_contract": _operation_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
        "actual_rating_rows_materialized_here": bool(op16.get("actual_rating_rows_materialized_here") is True) if op16_ready else False,
        "actual_blocker_rows_materialized_here": bool(op16.get("actual_blocker_rows_materialized_here") is True) if op16_ready else False,
        "actual_question_need_observation_rows_materialized_here": bool(op16.get("actual_question_need_observation_rows_materialized_here") is True) if op16_ready else False,
        "actual_disposal_receipt_materialized_here": ready,
        "disposal_verified": ready,
    }
    assert_p7_r54_op17_purge_disposal_receipt_contract(material)
    return material


def assert_p7_r54_op17_purge_disposal_receipt_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_OPERATION_PURGE_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS, source="p7_r54_op17_purge_disposal_receipt")
    _assert_common_operation_contract(
        data,
        schema_version=P7_R54_OPERATION_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION,
        policy_section=P7_R54_OP17_STEP_REF,
        operation_step_ref=P7_R54_OP17_STEP_REF,
        source="p7_r54_op17_purge_disposal_receipt",
        false_flag_refs=_op17_false_flag_refs(),
    )
    _assert_operation_current_refs(data, source="p7_r54_op17_purge_disposal_receipt")
    if data.get("op16_schema_version") != P7_R54_OPERATION_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION:
        raise ValueError("R54 OP17 OP16 schema reference changed")
    if tuple(data.get("removal_target_refs") or ()) != P7_R54_OP17_REMOVAL_TARGET_REFS:
        raise ValueError("R54 OP17 removal target refs changed")
    for false_key in (
        "local_packet_exported", "content_hash_of_body_stored", "body_full_packet_zip_inclusion_allowed",
        "reviewer_notes_export_allowed", "body_full_packet_export_allowed", "actual_disposal_run_here",
        "actual_review_evidence_complete",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 OP17 must keep {false_key}=False")
    for true_key in ("human_review_completion_claim_blocked_here", "p6_p8_release_promotion_blocked_here"):
        if data.get(true_key) is not True:
            raise ValueError(f"R54 OP17 must keep {true_key}=True")
    ready = data.get("purge_disposal_receipt_status") == P7_R54_OP17_DISPOSAL_VERIFIED_STATUS_REF
    if ready:
        for true_key in (
            "op16_purge_disposal_receipt_allowed_next", "op16_ready_for_purge_disposal_receipt", "body_removed",
            "reviewer_notes_removed", "temporary_form_removed", "all_required_local_targets_removed", "disposal_verified",
            "actual_disposal_receipt_materialized_here", "body_free_post_review_summary_allowed_next",
        ):
            if data.get(true_key) is not True:
                raise ValueError(f"R54 OP17 ready must keep {true_key}=True")
        if data.get("purge_disposal_receipt_ref") != P7_R54_OP17_DISPOSAL_RECEIPT_REF:
            raise ValueError("R54 OP17 ready receipt ref changed")
        if data.get("open_execution_blocker_ids"):
            raise ValueError("R54 OP17 ready must not carry open execution blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_OP17_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP17 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_OP17_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP17 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_OP18_STEP_REF:
            raise ValueError("R54 OP17 ready must point to OP18")
    else:
        if data.get("purge_disposal_receipt_status") != P7_R54_OP17_DISPOSAL_BLOCKED_STATUS_REF:
            raise ValueError("R54 OP17 blocked status changed")
        if data.get("disposal_verified") is not False or data.get("actual_disposal_receipt_materialized_here") is not False:
            raise ValueError("R54 OP17 blocked must not verify disposal")
        if data.get("body_free_post_review_summary_allowed_next") is not False:
            raise ValueError("R54 OP17 blocked must not allow OP18")
        if data.get("disposal_failure_decision_ref") != P7_R54_OP17_DISPOSAL_BLOCKED_STATUS_REF:
            raise ValueError("R54 OP17 blocked decision ref changed")
        if not data.get("open_execution_blocker_ids"):
            raise ValueError("R54 OP17 blocked must carry execution blockers")
        if data.get("local_packet_exported") is True and "local_packet_exported_during_disposal" not in data.get("open_execution_blocker_ids", []):
            raise ValueError("R54 OP17 packet export violation must be visible as a blocker")
        if data.get("content_hash_of_body_stored") is True and "content_hash_of_body_stored_during_disposal" not in data.get("open_execution_blocker_ids", []):
            raise ValueError("R54 OP17 body hash violation must be visible as a blocker")
        if data.get("next_required_step") != P7_R54_OP17_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 OP17 blocked must point to repair")
    return True


# OP16/OP17 detailed-design wording aliases.
build_p7_r54_operation_pause_abort_expiration_protocol = build_p7_r54_op16_pause_abort_expiration_protocol
assert_p7_r54_operation_pause_abort_expiration_protocol_contract = assert_p7_r54_op16_pause_abort_expiration_protocol_contract
build_p7_r54_operation_purge_disposal_receipt = build_p7_r54_op17_purge_disposal_receipt
assert_p7_r54_operation_purge_disposal_receipt_contract = assert_p7_r54_op17_purge_disposal_receipt_contract
build_p7_r54_operation_pause_abort_expiration_protocol_bodyfree = build_p7_r54_operation_pause_abort_expiration_protocol
assert_p7_r54_operation_pause_abort_expiration_protocol_bodyfree_contract = assert_p7_r54_operation_pause_abort_expiration_protocol_contract
build_p7_r54_operation_purge_disposal_receipt_bodyfree = build_p7_r54_operation_purge_disposal_receipt
assert_p7_r54_operation_purge_disposal_receipt_bodyfree_contract = assert_p7_r54_operation_purge_disposal_receipt_contract


# R54-OP-18 / R54-OP-19 operation-layer additions.
# These helpers summarize the completed local-only review evidence as body-free
# counts and separate the P5 decision candidate. They do not create packet
# contents, do not store body hashes or local paths, and do not start P6/P8 or
# release readiness.
P7_R54_OPERATION_BODYFREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_bodyfree_post_review_summary.bodyfree.v1"
)
P7_R54_OPERATION_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_p5_decision_candidate_separation.bodyfree.v1"
)

P7_R54_OP19_STEP_REF: Final = "R54-OP-19_p5_decision_candidate_separation"
P7_R54_OP20_STEP_REF: Final = "R54-OP-20_p6_candidate_handoff"
P7_R54_OP18_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "bodyfree_post_review_summary_repair_before_p5_decision_candidate_separation"
P7_R54_OP19_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "p5_decision_candidate_separation_repair_before_p6_candidate_handoff"
P7_R54_OP19_P5_REPAIR_NEXT_REQUIRED_STEP_REF: Final = "p5_repair_return_required_before_p6_candidate_handoff"
P7_R54_OP19_P4_R12_REPAIR_NEXT_REQUIRED_STEP_REF: Final = "p4_r12_targeted_current_only_surface_repair_required_before_p6_candidate_handoff"
P7_R54_OP19_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF: Final = "r54_operation_inconclusive_retry_or_r52_reintake_before_p6_candidate_handoff"
P7_R54_OP_NEXT_WORK_AFTER_OP18_REF: Final = "r54_op19_p5_decision_candidate_separation_after_bodyfree_post_review_summary"
P7_R54_OP_NEXT_WORK_AFTER_OP19_REF: Final = "r54_op20_p6_candidate_handoff_after_p5_decision_candidate_separation"

P7_R54_OP18_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_OP17_IMPLEMENTED_STEPS,
    P7_R54_OP18_STEP_REF,
)
P7_R54_OP18_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = tuple(
    step for step in P7_R54_OP17_NOT_YET_IMPLEMENTED_STEPS if step != P7_R54_OP18_STEP_REF
)
P7_R54_OP19_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_OP18_IMPLEMENTED_STEPS,
    P7_R54_OP19_STEP_REF,
)
P7_R54_OP19_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = tuple(
    step for step in P7_R54_OP18_NOT_YET_IMPLEMENTED_STEPS if step != P7_R54_OP19_STEP_REF
)

P7_R54_OP18_SUMMARY_READY_STATUS_REF: Final = "BODYFREE_SUMMARY_READY"
P7_R54_OP18_SUMMARY_BLOCKED_STATUS_REF: Final = "BODYFREE_SUMMARY_BLOCKED"
P7_R54_OP18_SUMMARY_REF: Final = "R54_OP18_BODYFREE_POST_REVIEW_SUMMARY_20260625"
P7_R54_OP18_READY_REASON_REF: Final = "r54_op18_rating_blocker_question_disposal_summary_ready_bodyfree"

P7_R54_OP19_DECISION_SEPARATION_READY_STATUS_REF: Final = "P5_DECISION_CANDIDATE_SEPARATED"
P7_R54_OP19_DECISION_SEPARATION_BLOCKED_STATUS_REF: Final = "P5_DECISION_CANDIDATE_SEPARATION_BLOCKED"
P7_R54_OP19_DECISION_SEPARATION_REF: Final = "R54_OP19_P5_DECISION_CANDIDATE_SEPARATION_20260625"
P7_R54_OP19_P5_CONFIRMED_CANDIDATE_REF: Final = "P5_CONFIRMED_CANDIDATE"
P7_R54_OP19_P5_REPAIR_RETURN_REF: Final = "P5_REPAIR_RETURN"
P7_R54_OP19_P4_R12_TARGETED_REPAIR_REF: Final = "P4_R12_TARGETED_CURRENT_ONLY_SURFACE_REPAIR"
P7_R54_OP19_INCONCLUSIVE_REF: Final = "R54_OPERATION_INCONCLUSIVE"
P7_R54_OP19_DECISION_CANDIDATE_REFS: Final[tuple[str, ...]] = (
    P7_R54_OP19_P5_CONFIRMED_CANDIDATE_REF,
    P7_R54_OP19_P5_REPAIR_RETURN_REF,
    P7_R54_OP19_P4_R12_TARGETED_REPAIR_REF,
    P7_R54_OP19_INCONCLUSIVE_REF,
)

P7_R54_OP19_REPAIR_RETURN_BLOCKER_REFS: Final[tuple[str, ...]] = (
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
)
P7_R54_OP19_NOT_QUESTION_REPAIR_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = (
    "not_question_emlis_readfeel_repair_required",
    "not_question_p5_surface_repair_required",
    "not_question_gate_boundary_required",
)

P7_R54_OPERATION_BODYFREE_POST_REVIEW_SUMMARY_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op17_schema_version", "op17_material_ref", "op17_next_required_step", "op17_purge_disposal_receipt_status", "op17_bodyfree_summary_allowed_next",
    "op15_schema_version", "op15_material_ref", "op15_next_required_step", "op15_consistency_guard_status",
    "op14_schema_version", "op14_material_ref", "op14_question_observation_normalization_status",
    "op13_schema_version", "op13_material_ref", "op13_blocker_ingestion_status",
    "op12_schema_version", "op12_material_ref", "op12_rating_row_normalization_status",
    "operation_current_refs", "operation_current_ref_count", "actual_review_basis_ref", "actual_review_basis_allowed", "operation_current_refs_are_actual_review_basis",
    "required_case_count", "reviewed_case_count", "rating_row_count", "question_observation_row_count",
    "bodyfree_post_review_summary_status", "bodyfree_post_review_summary_ref", "bodyfree_post_review_summary_reason_refs",
    "execution_blocker_ids", "open_execution_blocker_ids", "summary_blocker_ids", "summary_blocker_count",
    "verdict_counts", "axis_score_averages", "rating_axis_target_thresholds", "below_target_axis_refs", "below_target_axis_count",
    "open_readfeel_blocker_count", "open_execution_blocker_count", "readfeel_blocker_counts", "execution_blocker_counts",
    "primary_class_counts", "ambiguity_kind_counts", "one_question_fit_counts", "repair_required_counts", "plan_candidate_flag_counts",
    "p8_material_candidate_row_count", "not_question_repair_required_count", "insufficient_material_execution_blocker_count",
    "consistency_issue_count", "consistency_issue_direction_counts",
    "disposal_verified", "body_removed", "reviewer_notes_removed", "temporary_form_removed", "local_packet_exported", "content_hash_of_body_stored",
    "all_required_review_counts_present", "all_required_summary_inputs_ready", "no_body_leak_validation_passed", "no_question_text_validation_passed", "no_touch_validation_passed",
    "p5_decision_candidate_separation_allowed_next", "actual_review_evidence_complete", "human_review_completion_claim_blocked_here", "p6_p8_release_promotion_blocked_here",
    "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract", "r54_operation_no_touch_contract", "body_free_markers",
    "body_free", "question_text_included", "draft_question_text_included", "local_path_included",
    *P7_R54_OPERATION_FALSE_FLAG_REFS,
)

P7_R54_OPERATION_P5_DECISION_CANDIDATE_SEPARATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op18_schema_version", "op18_material_ref", "op18_next_required_step", "op18_bodyfree_post_review_summary_status", "op18_decision_separation_allowed_next",
    "operation_current_refs", "operation_current_ref_count", "actual_review_basis_ref", "actual_review_basis_allowed", "operation_current_refs_are_actual_review_basis",
    "required_case_count", "reviewed_case_count", "rating_row_count", "question_observation_row_count",
    "decision_candidate_separation_status", "decision_candidate_separation_ref", "decision_candidate_separation_reason_refs",
    "p5_decision_candidate_ref", "p5_decision_candidate_materialized_here", "p5_decision_candidate_reason_refs", "p5_decision_repair_reason_refs", "p5_decision_inconclusive_reason_refs", "p4_current_only_surface_issue_refs",
    "p5_confirmed_candidate_conditions_met", "p5_repair_return_required", "p4_r12_targeted_current_only_surface_repair_required", "r54_operation_inconclusive_required",
    "verdict_counts", "axis_score_averages", "rating_axis_target_thresholds", "below_target_axis_refs", "open_readfeel_blocker_count", "open_execution_blocker_count",
    "primary_class_counts", "repair_required_counts", "not_question_repair_required_count", "insufficient_material_execution_blocker_count", "disposal_verified",
    "p5_human_blind_qa_confirmed_candidate", "p5_human_blind_qa_confirmed_final", "p6_limited_human_readfeel_start_allowed", "p8_start_allowed", "release_allowed",
    "p5_final_confirmation_blocked_here", "p6_start_blocked_here", "p8_start_blocked_here", "release_blocked_here", "actual_review_evidence_complete",
    "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract", "r54_operation_no_touch_contract", "body_free_markers",
    "body_free", "question_text_included", "draft_question_text_included", "local_path_included",
    *P7_R54_OPERATION_FALSE_FLAG_REFS,
)


def _op18_false_flag_refs() -> tuple[str, ...]:
    return tuple(key for key in P7_R54_OPERATION_FALSE_FLAG_REFS if key != "disposal_verified")


def _op19_false_flag_refs() -> tuple[str, ...]:
    return tuple(
        key for key in P7_R54_OPERATION_FALSE_FLAG_REFS
        if key not in {"disposal_verified", "p5_human_blind_qa_confirmed_candidate"}
    )


def _op18_below_target_axis_refs(axis_averages: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    averages = safe_mapping(axis_averages)
    for axis, target in P7_R54_OP09_RATING_AXIS_TARGET_THRESHOLDS.items():
        score = averages.get(axis)
        if not isinstance(score, (int, float)) or isinstance(score, bool) or float(score) < float(target):
            refs.append(axis)
    return refs


def _op18_summary_inputs_ready(
    *,
    op17: Mapping[str, Any],
    op15: Mapping[str, Any],
    op14: Mapping[str, Any],
    op13: Mapping[str, Any],
    op12: Mapping[str, Any],
) -> tuple[bool, list[str]]:
    blockers: list[str] = []
    if not (
        op17.get("purge_disposal_receipt_status") == P7_R54_OP17_DISPOSAL_VERIFIED_STATUS_REF
        and op17.get("body_free_post_review_summary_allowed_next") is True
        and op17.get("disposal_verified") is True
    ):
        blockers.append("op17_disposal_receipt_not_verified_for_bodyfree_summary")
    if not (
        op15.get("rating_question_consistency_guard_status") == P7_R54_OP15_CONSISTENCY_GUARD_READY_STATUS_REF
        and op15.get("next_required_step") == P7_R54_OP16_STEP_REF
        and int(op15.get("consistency_issue_count") or 0) == 0
        and not op15.get("open_execution_blocker_ids")
    ):
        blockers.append("op15_consistency_guard_not_ready_for_bodyfree_summary")
    if not (
        op14.get("question_observation_normalization_status") == P7_R54_OP14_QUESTION_OBSERVATION_NORMALIZATION_READY_STATUS_REF
        and int(op14.get("question_observation_row_count") or 0) == P7_R51_REQUIRED_CASE_COUNT
        and op14.get("actual_question_need_observation_rows_materialized_here") is True
        and not op14.get("open_execution_blocker_ids")
    ):
        blockers.append("op14_question_observation_rows_not_ready_for_bodyfree_summary")
    if not (
        op13.get("blocker_ingestion_status") == P7_R54_OP13_BLOCKER_INGESTION_READY_STATUS_REF
        and not op13.get("open_execution_blocker_ids")
    ):
        blockers.append("op13_blocker_ingestion_not_ready_for_bodyfree_summary")
    if not (
        op12.get("rating_row_normalization_status") == P7_R54_OP12_RATING_NORMALIZATION_READY_STATUS_REF
        and int(op12.get("rating_row_count") or 0) == P7_R51_REQUIRED_CASE_COUNT
        and op12.get("actual_rating_rows_materialized_here") is True
        and not op12.get("open_execution_blocker_ids")
    ):
        blockers.append("op12_rating_rows_not_ready_for_bodyfree_summary")
    return (not blockers, blockers)


def build_p7_r54_op18_bodyfree_post_review_summary(
    *,
    purge_disposal_receipt: Mapping[str, Any] | None = None,
    rating_question_consistency_guard: Mapping[str, Any] | None = None,
    question_need_observation_normalization: Mapping[str, Any] | None = None,
    blocker_ingestion: Mapping[str, Any] | None = None,
    rating_row_normalization: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_operation_bodyfree_post_review_summary",
) -> dict[str, Any]:
    """Build R54-OP-18 body-free post-review count summary."""
    op17 = safe_mapping(purge_disposal_receipt) if purge_disposal_receipt is not None else build_p7_r54_op17_purge_disposal_receipt()
    assert_p7_r54_op17_purge_disposal_receipt_contract(op17)
    op15 = safe_mapping(rating_question_consistency_guard) if rating_question_consistency_guard is not None else build_p7_r54_op15_rating_question_consistency_guard()
    assert_p7_r54_op15_rating_question_consistency_guard_contract(op15)
    op14 = safe_mapping(question_need_observation_normalization) if question_need_observation_normalization is not None else build_p7_r54_op14_question_need_observation_normalization()
    assert_p7_r54_op14_question_need_observation_normalization_contract(op14)
    op13 = safe_mapping(blocker_ingestion) if blocker_ingestion is not None else build_p7_r54_op13_readfeel_blocker_execution_blocker_ingestion()
    assert_p7_r54_op13_readfeel_blocker_execution_blocker_ingestion_contract(op13)
    op12 = safe_mapping(rating_row_normalization) if rating_row_normalization is not None else build_p7_r54_op12_rating_row_normalization()
    assert_p7_r54_op12_rating_row_normalization_contract(op12)

    inputs_ready, input_blockers = _op18_summary_inputs_ready(op17=op17, op15=op15, op14=op14, op13=op13, op12=op12)
    verdict_counts = safe_mapping(op12.get("verdict_counts")) if inputs_ready else {}
    axis_score_averages = safe_mapping(op12.get("axis_score_averages")) if inputs_ready else {}
    below_target_axis_refs = _op18_below_target_axis_refs(axis_score_averages) if inputs_ready else []
    open_execution_blockers = dedupe_identifiers(
        [
            *input_blockers,
            *(op17.get("open_execution_blocker_ids") or []),
            *(op15.get("open_execution_blocker_ids") or []),
            *(op14.get("open_execution_blocker_ids") or []),
            *(op13.get("open_execution_blocker_ids") or []),
            *(op12.get("open_execution_blocker_ids") or []),
        ],
        limit=120,
        max_length=180,
    )
    counts_ready = bool(
        int(op12.get("reviewed_case_count") or 0) == P7_R51_REQUIRED_CASE_COUNT
        and int(op12.get("rating_row_count") or 0) == P7_R51_REQUIRED_CASE_COUNT
        and int(op14.get("question_observation_row_count") or 0) == P7_R51_REQUIRED_CASE_COUNT
    )
    no_body_leak_validation_passed = bool(
        inputs_ready
        and op17.get("local_packet_exported") is False
        and op17.get("content_hash_of_body_stored") is False
        and op14.get("raw_body_absent_for_all_rows") is True
        and op14.get("comment_text_absent_for_all_rows") is True
        and op14.get("local_path_absent_for_all_rows") is True
        and op14.get("body_hash_absent_for_all_rows") is True
    )
    no_question_text_validation_passed = bool(
        inputs_ready
        and op14.get("question_text_absent_for_all_rows") is True
        and op14.get("draft_question_text_absent_for_all_rows") is True
        and op14.get("question_text_or_draft_text_saved_here") is False
    )
    no_touch_validation_passed = bool(inputs_ready and _operation_no_touch_contract().get("release_allowed") is False)
    summary_ready = bool(
        inputs_ready
        and counts_ready
        and not open_execution_blockers
        and no_body_leak_validation_passed
        and no_question_text_validation_passed
        and no_touch_validation_passed
        and int(op15.get("consistency_issue_count") or 0) == 0
        and op17.get("disposal_verified") is True
    )
    reason_refs = [P7_R54_OP18_READY_REASON_REF] if summary_ready else dedupe_identifiers(
        [P7_R54_OP18_SUMMARY_BLOCKED_STATUS_REF, *open_execution_blockers],
        limit=120,
        max_length=180,
    )
    material = {
        "schema_version": P7_R54_OPERATION_BODYFREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_OPERATION_REENTRY_STEP,
        "scope": P7_R54_OPERATION_REENTRY_SCOPE,
        "policy_kind": P7_R54_OPERATION_REENTRY_POLICY_KIND,
        "policy_section": P7_R54_OP18_STEP_REF,
        "operation_step_ref": P7_R54_OP18_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_operation_bodyfree_post_review_summary", max_length=220),
        "review_session_id": _safe_review_session_id(op17.get("review_session_id") or op15.get("review_session_id") or op12.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op17_schema_version": P7_R54_OPERATION_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION,
        "op17_material_ref": clean_identifier(op17.get("material_id"), default="p7_r54_operation_purge_disposal_receipt", max_length=220),
        "op17_next_required_step": clean_identifier(op17.get("next_required_step"), default="", max_length=180),
        "op17_purge_disposal_receipt_status": clean_identifier(op17.get("purge_disposal_receipt_status"), default=P7_R54_OP17_DISPOSAL_BLOCKED_STATUS_REF, max_length=180),
        "op17_bodyfree_summary_allowed_next": op17.get("body_free_post_review_summary_allowed_next") is True,
        "op15_schema_version": P7_R54_OPERATION_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        "op15_material_ref": clean_identifier(op15.get("material_id"), default="p7_r54_operation_rating_question_consistency_guard", max_length=220),
        "op15_next_required_step": clean_identifier(op15.get("next_required_step"), default="", max_length=180),
        "op15_consistency_guard_status": clean_identifier(op15.get("rating_question_consistency_guard_status"), default=P7_R54_OP15_CONSISTENCY_GUARD_BLOCKED_STATUS_REF, max_length=180),
        "op14_schema_version": P7_R54_OPERATION_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION,
        "op14_material_ref": clean_identifier(op14.get("material_id"), default="p7_r54_operation_question_need_observation_normalization", max_length=220),
        "op14_question_observation_normalization_status": clean_identifier(op14.get("question_observation_normalization_status"), default=P7_R54_OP14_QUESTION_OBSERVATION_NORMALIZATION_BLOCKED_STATUS_REF, max_length=180),
        "op13_schema_version": P7_R54_OPERATION_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION,
        "op13_material_ref": clean_identifier(op13.get("material_id"), default="p7_r54_operation_readfeel_blocker_execution_blocker_ingestion", max_length=220),
        "op13_blocker_ingestion_status": clean_identifier(op13.get("blocker_ingestion_status"), default=P7_R54_OP13_BLOCKER_INGESTION_BLOCKED_STATUS_REF, max_length=180),
        "op12_schema_version": P7_R54_OPERATION_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        "op12_material_ref": clean_identifier(op12.get("material_id"), default="p7_r54_operation_rating_row_normalization", max_length=220),
        "op12_rating_row_normalization_status": clean_identifier(op12.get("rating_row_normalization_status"), default=P7_R54_OP12_RATING_NORMALIZATION_BLOCKED_STATUS_REF, max_length=180),
        "operation_current_refs": dict(P7_R54_OPERATION_CURRENT_REFS),
        "operation_current_ref_count": len(P7_R54_OPERATION_CURRENT_REFS),
        "actual_review_basis_ref": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "reviewed_case_count": int(op12.get("reviewed_case_count") or 0) if inputs_ready else 0,
        "rating_row_count": int(op12.get("rating_row_count") or 0) if inputs_ready else 0,
        "question_observation_row_count": int(op14.get("question_observation_row_count") or 0) if inputs_ready else 0,
        "bodyfree_post_review_summary_status": P7_R54_OP18_SUMMARY_READY_STATUS_REF if summary_ready else P7_R54_OP18_SUMMARY_BLOCKED_STATUS_REF,
        "bodyfree_post_review_summary_ref": P7_R54_OP18_SUMMARY_REF if summary_ready else "bodyfree_post_review_summary_not_ready",
        "bodyfree_post_review_summary_reason_refs": reason_refs,
        "execution_blocker_ids": [] if summary_ready else open_execution_blockers,
        "open_execution_blocker_ids": [] if summary_ready else open_execution_blockers,
        "summary_blocker_ids": [] if summary_ready else open_execution_blockers,
        "summary_blocker_count": 0 if summary_ready else len(open_execution_blockers),
        "verdict_counts": dict(verdict_counts),
        "axis_score_averages": dict(axis_score_averages),
        "rating_axis_target_thresholds": dict(P7_R54_OP09_RATING_AXIS_TARGET_THRESHOLDS),
        "below_target_axis_refs": below_target_axis_refs,
        "below_target_axis_count": len(below_target_axis_refs),
        "open_readfeel_blocker_count": int(op13.get("open_readfeel_blocker_count") or 0) if inputs_ready else 0,
        "open_execution_blocker_count": int(op13.get("open_execution_blocker_count") or 0) if inputs_ready else len(open_execution_blockers),
        "readfeel_blocker_counts": dict(safe_mapping(op13.get("readfeel_blocker_counts"))) if inputs_ready else {},
        "execution_blocker_counts": dict(safe_mapping(op13.get("execution_blocker_counts"))) if inputs_ready else {},
        "primary_class_counts": dict(safe_mapping(op14.get("question_need_primary_class_counts"))) if inputs_ready else {},
        "ambiguity_kind_counts": dict(safe_mapping(op14.get("ambiguity_kind_counts"))) if inputs_ready else {},
        "one_question_fit_counts": dict(safe_mapping(op14.get("one_question_fit_counts"))) if inputs_ready else {},
        "repair_required_counts": dict(safe_mapping(op14.get("repair_required_counts"))) if inputs_ready else {},
        "plan_candidate_flag_counts": dict(safe_mapping(op14.get("plan_candidate_flag_counts"))) if inputs_ready else {},
        "p8_material_candidate_row_count": int(op14.get("p8_material_candidate_row_count") or 0) if inputs_ready else 0,
        "not_question_repair_required_count": int(op14.get("not_question_repair_required_count") or 0) if inputs_ready else 0,
        "insufficient_material_execution_blocker_count": int(op14.get("insufficient_material_execution_blocker_count") or 0) if inputs_ready else 0,
        "consistency_issue_count": int(op15.get("consistency_issue_count") or 0) if inputs_ready else 0,
        "consistency_issue_direction_counts": dict(safe_mapping(op15.get("issue_direction_counts"))) if inputs_ready else {},
        "disposal_verified": op17.get("disposal_verified") is True if inputs_ready else False,
        "body_removed": op17.get("body_removed") is True if inputs_ready else False,
        "reviewer_notes_removed": op17.get("reviewer_notes_removed") is True if inputs_ready else False,
        "temporary_form_removed": op17.get("temporary_form_removed") is True if inputs_ready else False,
        "local_packet_exported": op17.get("local_packet_exported") is True,
        "content_hash_of_body_stored": op17.get("content_hash_of_body_stored") is True,
        "all_required_review_counts_present": counts_ready,
        "all_required_summary_inputs_ready": inputs_ready,
        "no_body_leak_validation_passed": no_body_leak_validation_passed,
        "no_question_text_validation_passed": no_question_text_validation_passed,
        "no_touch_validation_passed": no_touch_validation_passed,
        "p5_decision_candidate_separation_allowed_next": summary_ready,
        "actual_review_evidence_complete": False,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_OP18_IMPLEMENTED_STEPS if summary_ready else tuple(op17.get("implemented_steps") or ())),
        "not_yet_implemented_steps": list(P7_R54_OP18_NOT_YET_IMPLEMENTED_STEPS if summary_ready else tuple(op17.get("not_yet_implemented_steps") or ())),
        "first_next_work_ref": P7_R54_OP_NEXT_WORK_AFTER_OP18_REF if summary_ready else P7_R54_OP_NEXT_WORK_AFTER_OP17_REF,
        "next_required_step": P7_R54_OP19_STEP_REF if summary_ready else P7_R54_OP18_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_operation_no_touch_contract": _operation_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
        "disposal_verified": op17.get("disposal_verified") is True if inputs_ready else False,
    }
    assert_p7_r54_op18_bodyfree_post_review_summary_contract(material)
    return material


def assert_p7_r54_op18_bodyfree_post_review_summary_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_OPERATION_BODYFREE_POST_REVIEW_SUMMARY_REQUIRED_FIELD_REFS, source="p7_r54_op18_bodyfree_post_review_summary")
    _assert_common_operation_contract(
        data,
        schema_version=P7_R54_OPERATION_BODYFREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION,
        policy_section=P7_R54_OP18_STEP_REF,
        operation_step_ref=P7_R54_OP18_STEP_REF,
        source="p7_r54_op18_bodyfree_post_review_summary",
        false_flag_refs=_op18_false_flag_refs(),
    )
    _assert_operation_current_refs(data, source="p7_r54_op18_bodyfree_post_review_summary")
    if data.get("actual_review_evidence_complete") is not False:
        raise ValueError("R54 OP18 must not finalize actual review evidence")
    for false_key in ("local_packet_exported", "content_hash_of_body_stored"):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 OP18 must keep {false_key}=False")
    if data.get("op17_schema_version") != P7_R54_OPERATION_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION:
        raise ValueError("R54 OP18 OP17 schema reference changed")
    if data.get("op15_schema_version") != P7_R54_OPERATION_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION:
        raise ValueError("R54 OP18 OP15 schema reference changed")
    ready = data.get("bodyfree_post_review_summary_status") == P7_R54_OP18_SUMMARY_READY_STATUS_REF
    if data.get("p5_decision_candidate_separation_allowed_next") is not ready:
        raise ValueError("R54 OP18 decision separation allowance must match readiness")
    if ready:
        if data.get("bodyfree_post_review_summary_ref") != P7_R54_OP18_SUMMARY_REF:
            raise ValueError("R54 OP18 summary ref changed")
        if data.get("bodyfree_post_review_summary_reason_refs") != [P7_R54_OP18_READY_REASON_REF]:
            raise ValueError("R54 OP18 ready reason refs changed")
        if data.get("required_case_count") != P7_R51_REQUIRED_CASE_COUNT or data.get("reviewed_case_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 OP18 ready summary must preserve 24 reviewed cases")
        if data.get("rating_row_count") != P7_R51_REQUIRED_CASE_COUNT or data.get("question_observation_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 OP18 ready summary must preserve 24 rating/question rows")
        for true_key in (
            "all_required_review_counts_present", "all_required_summary_inputs_ready", "disposal_verified", "body_removed",
            "reviewer_notes_removed", "temporary_form_removed", "no_body_leak_validation_passed", "no_question_text_validation_passed", "no_touch_validation_passed",
        ):
            if data.get(true_key) is not True:
                raise ValueError(f"R54 OP18 ready summary must keep {true_key}=True")
        if data.get("open_execution_blocker_ids") != [] or data.get("summary_blocker_count") != 0 or data.get("consistency_issue_count") != 0:
            raise ValueError("R54 OP18 ready summary must not carry open execution blockers or consistency issues")
        if data.get("next_required_step") != P7_R54_OP19_STEP_REF:
            raise ValueError("R54 OP18 ready summary must point to OP19")
    else:
        if data.get("bodyfree_post_review_summary_status") != P7_R54_OP18_SUMMARY_BLOCKED_STATUS_REF:
            raise ValueError("R54 OP18 blocked status changed")
        if data.get("disposal_verified") is not False:
            raise ValueError("R54 OP18 blocked summary must not verify disposal")
        if data.get("next_required_step") != P7_R54_OP18_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 OP18 blocked summary must point to repair")
    return True


def _op19_p5_repair_reason_refs(summary: Mapping[str, Any]) -> list[str]:
    data = safe_mapping(summary)
    reasons: list[str] = []
    verdict_counts = safe_mapping(data.get("verdict_counts"))
    if int(verdict_counts.get("RED") or 0) > 0:
        reasons.append("red_verdict_present")
    if int(verdict_counts.get("REPAIR_REQUIRED") or 0) > 0:
        reasons.append("repair_required_verdict_present")
    readfeel_counts = safe_mapping(data.get("readfeel_blocker_counts"))
    for blocker_id in P7_R54_OP19_REPAIR_RETURN_BLOCKER_REFS:
        if int(readfeel_counts.get(blocker_id) or 0) > 0:
            reasons.append(f"readfeel_blocker:{blocker_id}")
    for axis in data.get("below_target_axis_refs") or []:
        reasons.append(f"axis_below_target:{clean_identifier(axis, max_length=120)}")
    primary_counts = safe_mapping(data.get("primary_class_counts"))
    for primary_class_ref in P7_R54_OP19_NOT_QUESTION_REPAIR_PRIMARY_CLASS_REFS:
        if int(primary_counts.get(primary_class_ref) or 0) > 0:
            reasons.append(f"not_question_repair_primary_class:{primary_class_ref}")
    if int(data.get("not_question_repair_required_count") or 0) > 0:
        reasons.append("not_question_repair_required_row_present")
    return dedupe_identifiers(reasons, limit=80, max_length=180)


def _op19_p5_inconclusive_reason_refs(summary: Mapping[str, Any]) -> list[str]:
    data = safe_mapping(summary)
    reasons: list[str] = []
    verdict_counts = safe_mapping(data.get("verdict_counts"))
    if int(verdict_counts.get("YELLOW") or 0) > 0:
        reasons.append("yellow_verdict_present")
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
    if int(data.get("reviewed_case_count") or 0) != P7_R51_REQUIRED_CASE_COUNT:
        reasons.append("reviewed_case_count_not_24")
    if int(data.get("rating_row_count") or 0) != P7_R51_REQUIRED_CASE_COUNT:
        reasons.append("rating_row_count_not_24")
    if int(data.get("question_observation_row_count") or 0) != P7_R51_REQUIRED_CASE_COUNT:
        reasons.append("question_observation_row_count_not_24")
    return dedupe_identifiers(reasons, limit=80, max_length=180)


def _op19_confirmed_candidate_conditions_met(summary: Mapping[str, Any]) -> bool:
    data = safe_mapping(summary)
    verdict_counts = safe_mapping(data.get("verdict_counts"))
    return bool(
        data.get("bodyfree_post_review_summary_status") == P7_R54_OP18_SUMMARY_READY_STATUS_REF
        and int(data.get("reviewed_case_count") or 0) == P7_R51_REQUIRED_CASE_COUNT
        and int(data.get("rating_row_count") or 0) == P7_R51_REQUIRED_CASE_COUNT
        and int(data.get("question_observation_row_count") or 0) == P7_R51_REQUIRED_CASE_COUNT
        and int(verdict_counts.get("PASS") or 0) == P7_R51_REQUIRED_CASE_COUNT
        and int(verdict_counts.get("YELLOW") or 0) == 0
        and int(verdict_counts.get("REPAIR_REQUIRED") or 0) == 0
        and int(verdict_counts.get("RED") or 0) == 0
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
        and not _op19_p5_repair_reason_refs(data)
        and not _op19_p5_inconclusive_reason_refs(data)
    )


def build_p7_r54_op19_p5_decision_candidate_separation(
    *,
    bodyfree_post_review_summary: Mapping[str, Any] | None = None,
    p4_current_only_surface_issue_refs: Sequence[Any] | None = None,
    material_id: Any = "p7_r54_operation_p5_decision_candidate_separation",
) -> dict[str, Any]:
    """Build R54-OP-19 body-free P5 decision candidate separation."""
    op18 = safe_mapping(bodyfree_post_review_summary) if bodyfree_post_review_summary is not None else build_p7_r54_op18_bodyfree_post_review_summary()
    assert_p7_r54_op18_bodyfree_post_review_summary_contract(op18)
    op18_ready = bool(
        op18.get("bodyfree_post_review_summary_status") == P7_R54_OP18_SUMMARY_READY_STATUS_REF
        and op18.get("p5_decision_candidate_separation_allowed_next") is True
        and op18.get("next_required_step") == P7_R54_OP19_STEP_REF
    )
    p4_issue_refs = dedupe_identifiers(p4_current_only_surface_issue_refs or [], limit=24, max_length=180)
    repair_reasons = _op19_p5_repair_reason_refs(op18) if op18_ready else []
    inconclusive_reasons = _op19_p5_inconclusive_reason_refs(op18) if op18_ready else ["op18_bodyfree_post_review_summary_not_ready"]
    confirmed_conditions_met = bool(op18_ready and not p4_issue_refs and _op19_confirmed_candidate_conditions_met(op18))
    if not op18_ready:
        decision = P7_R54_OP19_INCONCLUSIVE_REF
    elif p4_issue_refs:
        decision = P7_R54_OP19_P4_R12_TARGETED_REPAIR_REF
    elif repair_reasons:
        decision = P7_R54_OP19_P5_REPAIR_RETURN_REF
    elif confirmed_conditions_met:
        decision = P7_R54_OP19_P5_CONFIRMED_CANDIDATE_REF
    else:
        decision = P7_R54_OP19_INCONCLUSIVE_REF
        if not inconclusive_reasons:
            inconclusive_reasons = ["p5_confirmed_candidate_conditions_not_all_met"]
    separation_ready = bool(op18_ready)
    p5_candidate_reason_refs = ["p5_confirmed_candidate_conditions_met_bodyfree"] if decision == P7_R54_OP19_P5_CONFIRMED_CANDIDATE_REF else []
    if decision == P7_R54_OP19_P4_R12_TARGETED_REPAIR_REF:
        p5_candidate_reason_refs = ["current_only_surface_issue_requires_p4_r12_targeted_repair"]
    elif decision == P7_R54_OP19_P5_REPAIR_RETURN_REF:
        p5_candidate_reason_refs = ["p5_repair_return_required_by_bodyfree_review_summary"]
    elif decision == P7_R54_OP19_INCONCLUSIVE_REF:
        p5_candidate_reason_refs = ["r54_operation_inconclusive_by_bodyfree_review_summary"]
    if decision == P7_R54_OP19_P5_CONFIRMED_CANDIDATE_REF:
        next_step = P7_R54_OP20_STEP_REF
    elif decision == P7_R54_OP19_P5_REPAIR_RETURN_REF:
        next_step = P7_R54_OP19_P5_REPAIR_NEXT_REQUIRED_STEP_REF
    elif decision == P7_R54_OP19_P4_R12_TARGETED_REPAIR_REF:
        next_step = P7_R54_OP19_P4_R12_REPAIR_NEXT_REQUIRED_STEP_REF
    elif separation_ready:
        next_step = P7_R54_OP19_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF
    else:
        next_step = P7_R54_OP19_BLOCKED_NEXT_REQUIRED_STEP_REF
    material = {
        "schema_version": P7_R54_OPERATION_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_OPERATION_REENTRY_STEP,
        "scope": P7_R54_OPERATION_REENTRY_SCOPE,
        "policy_kind": P7_R54_OPERATION_REENTRY_POLICY_KIND,
        "policy_section": P7_R54_OP19_STEP_REF,
        "operation_step_ref": P7_R54_OP19_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_operation_p5_decision_candidate_separation", max_length=220),
        "review_session_id": _safe_review_session_id(op18.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op18_schema_version": P7_R54_OPERATION_BODYFREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION,
        "op18_material_ref": clean_identifier(op18.get("material_id"), default="p7_r54_operation_bodyfree_post_review_summary", max_length=220),
        "op18_next_required_step": clean_identifier(op18.get("next_required_step"), default="", max_length=180),
        "op18_bodyfree_post_review_summary_status": clean_identifier(op18.get("bodyfree_post_review_summary_status"), default=P7_R54_OP18_SUMMARY_BLOCKED_STATUS_REF, max_length=180),
        "op18_decision_separation_allowed_next": op18_ready,
        "operation_current_refs": dict(P7_R54_OPERATION_CURRENT_REFS),
        "operation_current_ref_count": len(P7_R54_OPERATION_CURRENT_REFS),
        "actual_review_basis_ref": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "reviewed_case_count": int(op18.get("reviewed_case_count") or 0),
        "rating_row_count": int(op18.get("rating_row_count") or 0),
        "question_observation_row_count": int(op18.get("question_observation_row_count") or 0),
        "decision_candidate_separation_status": P7_R54_OP19_DECISION_SEPARATION_READY_STATUS_REF if separation_ready else P7_R54_OP19_DECISION_SEPARATION_BLOCKED_STATUS_REF,
        "decision_candidate_separation_ref": P7_R54_OP19_DECISION_SEPARATION_REF if separation_ready else "p5_decision_candidate_separation_not_ready",
        "decision_candidate_separation_reason_refs": ["p5_decision_candidate_separation_ready_bodyfree"] if separation_ready else ["op18_summary_not_ready_for_decision_candidate_separation"],
        "p5_decision_candidate_ref": decision,
        "p5_decision_candidate_materialized_here": separation_ready,
        "p5_decision_candidate_reason_refs": p5_candidate_reason_refs,
        "p5_decision_repair_reason_refs": repair_reasons,
        "p5_decision_inconclusive_reason_refs": inconclusive_reasons if decision == P7_R54_OP19_INCONCLUSIVE_REF else [],
        "p4_current_only_surface_issue_refs": p4_issue_refs,
        "p5_confirmed_candidate_conditions_met": confirmed_conditions_met,
        "p5_repair_return_required": decision == P7_R54_OP19_P5_REPAIR_RETURN_REF,
        "p4_r12_targeted_current_only_surface_repair_required": decision == P7_R54_OP19_P4_R12_TARGETED_REPAIR_REF,
        "r54_operation_inconclusive_required": decision == P7_R54_OP19_INCONCLUSIVE_REF,
        "verdict_counts": dict(safe_mapping(op18.get("verdict_counts"))),
        "axis_score_averages": dict(safe_mapping(op18.get("axis_score_averages"))),
        "rating_axis_target_thresholds": dict(P7_R54_OP09_RATING_AXIS_TARGET_THRESHOLDS),
        "below_target_axis_refs": list(op18.get("below_target_axis_refs") or []),
        "open_readfeel_blocker_count": int(op18.get("open_readfeel_blocker_count") or 0),
        "open_execution_blocker_count": int(op18.get("open_execution_blocker_count") or 0),
        "primary_class_counts": dict(safe_mapping(op18.get("primary_class_counts"))),
        "repair_required_counts": dict(safe_mapping(op18.get("repair_required_counts"))),
        "not_question_repair_required_count": int(op18.get("not_question_repair_required_count") or 0),
        "insufficient_material_execution_blocker_count": int(op18.get("insufficient_material_execution_blocker_count") or 0),
        "disposal_verified": op18.get("disposal_verified") is True,
        "p5_human_blind_qa_confirmed_candidate": decision == P7_R54_OP19_P5_CONFIRMED_CANDIDATE_REF,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "p5_final_confirmation_blocked_here": True,
        "p6_start_blocked_here": True,
        "p8_start_blocked_here": True,
        "release_blocked_here": True,
        "actual_review_evidence_complete": False,
        "implemented_steps": list(P7_R54_OP19_IMPLEMENTED_STEPS if separation_ready else tuple(op18.get("implemented_steps") or ())),
        "not_yet_implemented_steps": list(P7_R54_OP19_NOT_YET_IMPLEMENTED_STEPS if separation_ready else tuple(op18.get("not_yet_implemented_steps") or ())),
        "first_next_work_ref": P7_R54_OP_NEXT_WORK_AFTER_OP19_REF if separation_ready else P7_R54_OP_NEXT_WORK_AFTER_OP18_REF,
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "r54_operation_no_touch_contract": _operation_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
        "disposal_verified": op18.get("disposal_verified") is True,
        "p5_human_blind_qa_confirmed_candidate": decision == P7_R54_OP19_P5_CONFIRMED_CANDIDATE_REF,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
    }
    assert_p7_r54_op19_p5_decision_candidate_separation_contract(material)
    return material


def assert_p7_r54_op19_p5_decision_candidate_separation_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_OPERATION_P5_DECISION_CANDIDATE_SEPARATION_REQUIRED_FIELD_REFS, source="p7_r54_op19_p5_decision_candidate_separation")
    _assert_common_operation_contract(
        data,
        schema_version=P7_R54_OPERATION_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION,
        policy_section=P7_R54_OP19_STEP_REF,
        operation_step_ref=P7_R54_OP19_STEP_REF,
        source="p7_r54_op19_p5_decision_candidate_separation",
        false_flag_refs=_op19_false_flag_refs(),
    )
    _assert_operation_current_refs(data, source="p7_r54_op19_p5_decision_candidate_separation")
    if data.get("actual_review_evidence_complete") is not False:
        raise ValueError("R54 OP19 must not finalize actual review evidence")
    if data.get("p5_decision_candidate_ref") not in P7_R54_OP19_DECISION_CANDIDATE_REFS:
        raise ValueError("R54 OP19 decision candidate ref outside allowed refs")
    separation_ready = data.get("decision_candidate_separation_status") == P7_R54_OP19_DECISION_SEPARATION_READY_STATUS_REF
    if data.get("p5_decision_candidate_materialized_here") is not separation_ready:
        raise ValueError("R54 OP19 materialized flag must match separation readiness")
    if data.get("p5_human_blind_qa_confirmed_final") is not False or data.get("p6_limited_human_readfeel_start_allowed") is not False or data.get("p8_start_allowed") is not False or data.get("release_allowed") is not False:
        raise ValueError("R54 OP19 must not finalize P5 or start P6/P8/release")
    if data.get("p5_final_confirmation_blocked_here") is not True or data.get("p6_start_blocked_here") is not True or data.get("p8_start_blocked_here") is not True or data.get("release_blocked_here") is not True:
        raise ValueError("R54 OP19 must explicitly block final/start/release promotion")
    if separation_ready:
        if data.get("decision_candidate_separation_ref") != P7_R54_OP19_DECISION_SEPARATION_REF:
            raise ValueError("R54 OP19 separation ref changed")
        if data.get("decision_candidate_separation_reason_refs") != ["p5_decision_candidate_separation_ready_bodyfree"]:
            raise ValueError("R54 OP19 ready reason refs changed")
        if data.get("required_case_count") != P7_R51_REQUIRED_CASE_COUNT or data.get("rating_row_count") != P7_R51_REQUIRED_CASE_COUNT or data.get("question_observation_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 OP19 ready separation must carry 24-case evidence counts")
        if data.get("p5_decision_candidate_ref") == P7_R54_OP19_P5_CONFIRMED_CANDIDATE_REF:
            if data.get("p5_human_blind_qa_confirmed_candidate") is not True or data.get("p5_confirmed_candidate_conditions_met") is not True:
                raise ValueError("R54 OP19 P5 confirmed candidate must be candidate-only and condition-backed")
            if data.get("next_required_step") != P7_R54_OP20_STEP_REF:
                raise ValueError("R54 OP19 P5 confirmed candidate must point to OP20 candidate handoff")
        else:
            if data.get("p5_human_blind_qa_confirmed_candidate") is not False:
                raise ValueError("R54 OP19 non-confirmed decision must not set P5 candidate flag")
    else:
        if data.get("decision_candidate_separation_status") != P7_R54_OP19_DECISION_SEPARATION_BLOCKED_STATUS_REF:
            raise ValueError("R54 OP19 blocked status changed")
        if data.get("p5_decision_candidate_ref") != P7_R54_OP19_INCONCLUSIVE_REF:
            raise ValueError("R54 OP19 blocked decision must be inconclusive")
        if data.get("next_required_step") != P7_R54_OP19_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 OP19 blocked separation must point to repair")
    return True


build_p7_r54_operation_bodyfree_post_review_summary = build_p7_r54_op18_bodyfree_post_review_summary
assert_p7_r54_operation_bodyfree_post_review_summary_contract = assert_p7_r54_op18_bodyfree_post_review_summary_contract
build_p7_r54_operation_p5_decision_candidate_separation = build_p7_r54_op19_p5_decision_candidate_separation
assert_p7_r54_operation_p5_decision_candidate_separation_contract = assert_p7_r54_op19_p5_decision_candidate_separation_contract
build_p7_r54_operation_bodyfree_post_review_summary_bodyfree = build_p7_r54_operation_bodyfree_post_review_summary
assert_p7_r54_operation_bodyfree_post_review_summary_bodyfree_contract = assert_p7_r54_operation_bodyfree_post_review_summary_contract
build_p7_r54_operation_p5_decision_candidate_separation_bodyfree = build_p7_r54_operation_p5_decision_candidate_separation
assert_p7_r54_operation_p5_decision_candidate_separation_bodyfree_contract = assert_p7_r54_operation_p5_decision_candidate_separation_contract


__all__ = (
    "P7_R54_OPERATION_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION",
    "P7_R54_OPERATION_CURRENT_SNAPSHOT_REFREEZE_SCHEMA_VERSION",
    "P7_R54_OPERATION_SOURCE_DELTA_ROW_SCHEMA_VERSION",
    "P7_R54_OPERATION_HISTORICAL_HELPER_SOURCE_DELTA_RECONCILE_SCHEMA_VERSION",
    "P7_R54_OPERATION_R55_HOLD_INTAKE_SCHEMA_VERSION",
    "P7_R54_OPERATION_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION",
    "P7_R54_OPERATION_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION",
    "P7_R54_OPERATION_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION",
    "P7_R54_OPERATION_PACKET_GENERATION_LOCAL_OPERATION_SCHEMA_VERSION",
    "P7_R54_OPERATION_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION",
    "P7_R54_OPERATION_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION",
    "P7_R54_OPERATION_ACTUAL_HUMAN_REVIEW_OPERATION_STATE_CAPTURE_SCHEMA_VERSION",
    "P7_R54_OPERATION_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION",
    "P7_R54_OPERATION_SANITIZED_REVIEW_RESULT_CAPTURE_SCHEMA_VERSION",
    "P7_R54_OPERATION_RATING_ROW_SCHEMA_VERSION",
    "P7_R54_OPERATION_RATING_ROW_NORMALIZATION_SCHEMA_VERSION",
    "P7_R54_OPERATION_READFEEL_BLOCKER_ROW_SCHEMA_VERSION",
    "P7_R54_OPERATION_EXECUTION_BLOCKER_ROW_SCHEMA_VERSION",
    "P7_R54_OPERATION_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION",
    "P7_R54_OPERATION_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION",
    "P7_R54_OPERATION_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION",
    "P7_R54_OPERATION_RATING_QUESTION_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION",
    "P7_R54_OPERATION_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION",
    "P7_R54_OPERATION_REENTRY_STEP",
    "P7_R54_OPERATION_REENTRY_SCOPE",
    "P7_R54_OPERATION_CURRENT_REFS",
    "P7_R54_OPERATION_HISTORICAL_HELPER_REFS",
    "P7_R54_OP00_STEP_REF",
    "P7_R54_OP01_STEP_REF",
    "P7_R54_OP02_STEP_REF",
    "P7_R54_OP02_NEXT_REQUIRED_STEP_REF",
    "P7_R54_OP03_STEP_REF",
    "P7_R54_OP04_NEXT_REQUIRED_STEP_REF",
    "P7_R54_OP04_STEP_REF",
    "P7_R54_OP05_STEP_REF",
    "P7_R54_OP06_STEP_REF",
    "P7_R54_OP07_STEP_REF",
    "P7_R54_OP08_STEP_REF",
    "P7_R54_OP09_STEP_REF",
    "P7_R54_OP10_STEP_REF",
    "P7_R54_OP11_STEP_REF",
    "P7_R54_OP12_STEP_REF",
    "P7_R54_OP13_STEP_REF",
    "P7_R54_OP14_STEP_REF",
    "P7_R54_OP15_STEP_REF",
    "P7_R54_OP04_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_OP05_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_OP06_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_OP07_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_OP08_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_OP09_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_OP10_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_OP10_NOT_COMPLETED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_OP11_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_OP12_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_OP13_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_OP14_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_OP15_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_OP04_PREFLIGHT_READY_STATUS_REF",
    "P7_R54_OP04_PREFLIGHT_BLOCKED_STATUS_REF",
    "P7_R54_OP04_LOCAL_REVIEW_ROOT_READY_REF",
    "P7_R54_OP04_EXPLICIT_ALLOW_TOKEN_REF",
    "P7_R54_OP04_PURGE_PLAN_READY_REF",
    "P7_R54_OP04_RETENTION_POLICY_READY_REF",
    "P7_R54_OP04_EXPORT_DENYLIST_POLICY_READY_REF",
    "P7_R54_OP05_MANIFEST_READY_STATUS_REF",
    "P7_R54_OP05_MANIFEST_BLOCKED_STATUS_REF",
    "P7_R54_OP05_CASE_DISTRIBUTION",
    "P7_R54_OP06_REQUEST_READY_STATUS_REF",
    "P7_R54_OP06_REQUEST_BLOCKED_STATUS_REF",
    "P7_R54_OP06_PACKET_GENERATION_REQUEST_REF",
    "P7_R54_OP07_LOCAL_OPERATION_READY_STATUS_REF",
    "P7_R54_OP07_LOCAL_OPERATION_BLOCKED_STATUS_REF",
    "P7_R54_OP07_LOCAL_OPERATION_RECEIPT_REF",
    "P7_R54_OP08_PACKET_SCAN_READY_STATUS_REF",
    "P7_R54_OP08_PACKET_SCAN_BLOCKED_STATUS_REF",
    "P7_R54_OP08_PACKET_SCAN_BLOCKED_BY_LEAK_STATUS_REF",
    "P7_R54_OP08_PACKET_SCAN_REF",
    "P7_R54_OP09_FORM_READY_STATUS_REF",
    "P7_R54_OP09_FORM_BLOCKED_STATUS_REF",
    "P7_R54_OP09_REVIEWER_INSTRUCTION_REF",
    "P7_R54_OP09_RATING_FORM_REF",
    "P7_R54_OP10_REVIEW_STATE_CAPTURE_READY_STATUS_REF",
    "P7_R54_OP10_REVIEW_STATE_CAPTURE_BLOCKED_STATUS_REF",
    "P7_R54_OP10_REVIEW_NOT_STARTED_STATUS_REF",
    "P7_R54_OP10_REVIEW_IN_PROGRESS_STATUS_REF",
    "P7_R54_OP10_REVIEW_PAUSED_STATUS_REF",
    "P7_R54_OP10_REVIEW_ABORTED_STATUS_REF",
    "P7_R54_OP10_REVIEW_EXPIRED_STATUS_REF",
    "P7_R54_OP10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF",
    "P7_R54_OP10_ALLOWED_REVIEW_OPERATION_STATUS_REFS",
    "P7_R54_OP11_SANITIZED_CAPTURE_READY_STATUS_REF",
    "P7_R54_OP11_SANITIZED_CAPTURE_BLOCKED_STATUS_REF",
    "P7_R54_OP11_SANITIZED_REVIEW_RESULT_CAPTURE_REF",
    "P7_R54_OP12_RATING_NORMALIZATION_READY_STATUS_REF",
    "P7_R54_OP12_RATING_NORMALIZATION_BLOCKED_STATUS_REF",
    "P7_R54_OP12_RATING_ROW_NORMALIZATION_REF",
    "P7_R54_OP13_BLOCKER_INGESTION_READY_STATUS_REF",
    "P7_R54_OP13_BLOCKER_INGESTION_BLOCKED_STATUS_REF",
    "P7_R54_OP13_EXECUTION_BLOCKER_ID_REFS",
    "P7_R54_OP14_QUESTION_OBSERVATION_NORMALIZATION_READY_STATUS_REF",
    "P7_R54_OP14_QUESTION_OBSERVATION_NORMALIZATION_BLOCKED_STATUS_REF",
    "P7_R54_OP14_QUESTION_OBSERVATION_NORMALIZATION_REF",
    "P7_R54_OP15_CONSISTENCY_GUARD_READY_STATUS_REF",
    "P7_R54_OP15_CONSISTENCY_GUARD_BLOCKED_STATUS_REF",
    "P7_R54_OP15_CONSISTENCY_GUARD_REF",
    "P7_R54_OP15_CONSISTENCY_ISSUE_ID_REFS",
    "P7_R54_OP09_RATING_AXIS_REFS",
    "P7_R54_OP09_RATING_AXIS_TARGET_THRESHOLDS",
    "P7_R54_OP09_SCORE_OPTION_REFS",
    "P7_R54_OP09_VERDICT_OPTION_REFS",
    "P7_R54_SOURCE_DELTA_ROW_REFS",
    "P7_R54_R55_HOLD_INTAKE_STATUS_REF",
    "P7_R54_OPERATION_SCOPE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS",
    "P7_R54_OPERATION_CURRENT_SNAPSHOT_REFREEZE_REQUIRED_FIELD_REFS",
    "P7_R54_SOURCE_DELTA_ROW_REQUIRED_FIELD_REFS",
    "P7_R54_OPERATION_HISTORICAL_HELPER_SOURCE_DELTA_RECONCILE_REQUIRED_FIELD_REFS",
    "P7_R54_OPERATION_R55_HOLD_INTAKE_REQUIRED_FIELD_REFS",
    "P7_R54_OPERATION_LOCAL_ONLY_PREFLIGHT_REQUIRED_FIELD_REFS",
    "P7_R54_OPERATION_24_CASE_MANIFEST_FREEZE_REQUIRED_FIELD_REFS",
    "P7_R54_OPERATION_BODY_FULL_PACKET_GENERATION_REQUEST_REQUIRED_FIELD_REFS",
    "P7_R54_OPERATION_PACKET_GENERATION_LOCAL_OPERATION_REQUIRED_FIELD_REFS",
    "P7_R54_OPERATION_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_REQUIRED_FIELD_REFS",
    "P7_R54_OPERATION_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_REQUIRED_FIELD_REFS",
    "P7_R54_OPERATION_ACTUAL_HUMAN_REVIEW_OPERATION_STATE_CAPTURE_REQUIRED_FIELD_REFS",
    "P7_R54_OPERATION_SANITIZED_REVIEW_RESULT_ROW_REQUIRED_FIELD_REFS",
    "P7_R54_OPERATION_SANITIZED_REVIEW_RESULT_CAPTURE_REQUIRED_FIELD_REFS",
    "P7_R54_OPERATION_RATING_ROW_REQUIRED_FIELD_REFS",
    "P7_R54_OPERATION_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS",
    "P7_R54_OPERATION_READFEEL_BLOCKER_ROW_REQUIRED_FIELD_REFS",
    "P7_R54_OPERATION_EXECUTION_BLOCKER_ROW_REQUIRED_FIELD_REFS",
    "P7_R54_OPERATION_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION_REQUIRED_FIELD_REFS",
    "P7_R54_OPERATION_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS",
    "P7_R54_OPERATION_QUESTION_NEED_OBSERVATION_NORMALIZATION_REQUIRED_FIELD_REFS",
    "P7_R54_OPERATION_RATING_QUESTION_CONSISTENCY_ISSUE_ROW_REQUIRED_FIELD_REFS",
    "P7_R54_OPERATION_RATING_QUESTION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS",
    "build_p7_r54_op00_scope_no_touch_boundary_freeze",
    "assert_p7_r54_op00_scope_no_touch_boundary_freeze_contract",
    "build_p7_r54_op01_operation_current_snapshot_refs_refreeze",
    "assert_p7_r54_op01_operation_current_snapshot_refs_refreeze_contract",
    "assert_p7_r54_source_delta_row_bodyfree_contract",
    "build_p7_r54_op02_historical_helper_source_delta_reconcile",
    "assert_p7_r54_op02_historical_helper_source_delta_reconcile_contract",
    "build_p7_r54_op03_r55_hold_intake",
    "assert_p7_r54_op03_r55_hold_intake_contract",
    "build_p7_r54_op04_local_only_preflight",
    "assert_p7_r54_op04_local_only_preflight_contract",
    "build_p7_r54_op05_24_case_manifest_freeze",
    "assert_p7_r54_op05_24_case_manifest_freeze_contract",
    "build_p7_r54_op06_local_only_body_full_packet_generation_request",
    "assert_p7_r54_op06_local_only_body_full_packet_generation_request_contract",
    "build_p7_r54_op07_packet_generation_local_operation",
    "assert_p7_r54_op07_packet_generation_local_operation_contract",
    "build_p7_r54_op08_packet_completeness_export_denylist_scan",
    "assert_p7_r54_op08_packet_completeness_export_denylist_scan_contract",
    "build_p7_r54_op09_reviewer_instruction_rating_form_freeze",
    "assert_p7_r54_op09_reviewer_instruction_rating_form_freeze_contract",
    "build_p7_r54_op10_actual_human_review_operation_state_capture",
    "assert_p7_r54_op10_actual_human_review_operation_state_capture_contract",
    "build_p7_r54_op11_sanitized_review_result_capture",
    "assert_p7_r54_op11_sanitized_review_result_capture_contract",
    "build_p7_r54_op12_rating_row_normalization",
    "assert_p7_r54_op12_rating_row_normalization_contract",
    "assert_p7_r54_op12_rating_row_bodyfree_contract",
    "build_p7_r54_op13_readfeel_blocker_execution_blocker_ingestion",
    "assert_p7_r54_op13_readfeel_blocker_execution_blocker_ingestion_contract",
    "build_p7_r54_op13_readfeel_blocker_row_bodyfree",
    "assert_p7_r54_op13_readfeel_blocker_row_bodyfree_contract",
    "build_p7_r54_op13_execution_blocker_row_bodyfree",
    "assert_p7_r54_op13_execution_blocker_row_bodyfree_contract",
    "build_p7_r54_op14_question_need_observation_normalization",
    "assert_p7_r54_op14_question_need_observation_normalization_contract",
    "assert_p7_r54_op14_question_need_observation_row_bodyfree_contract",
    "build_p7_r54_op15_rating_question_consistency_guard",
    "assert_p7_r54_op15_rating_question_consistency_guard_contract",
    "build_p7_r54_op15_rating_question_consistency_issue_row_bodyfree",
    "assert_p7_r54_op15_rating_question_consistency_issue_row_bodyfree_contract",
    "build_p7_r54_operation_scope_no_touch_boundary_freeze",
    "assert_p7_r54_operation_scope_no_touch_boundary_freeze_contract",
    "build_p7_r54_operation_current_snapshot_refreeze",
    "assert_p7_r54_operation_current_snapshot_refreeze_contract",
    "build_p7_r54_operation_historical_helper_source_delta_reconcile",
    "assert_p7_r54_operation_historical_helper_source_delta_reconcile_contract",
    "build_p7_r54_operation_r55_hold_intake",
    "assert_p7_r54_operation_r55_hold_intake_contract",
    "build_p7_r54_operation_local_only_preflight",
    "assert_p7_r54_operation_local_only_preflight_contract",
    "build_p7_r54_operation_24_case_manifest_freeze",
    "assert_p7_r54_operation_24_case_manifest_freeze_contract",
    "build_p7_r54_operation_body_full_packet_generation_request",
    "assert_p7_r54_operation_body_full_packet_generation_request_contract",
    "build_p7_r54_operation_packet_generation_local_operation",
    "assert_p7_r54_operation_packet_generation_local_operation_contract",
    "build_p7_r54_operation_packet_completeness_export_denylist_scan",
    "assert_p7_r54_operation_packet_completeness_export_denylist_scan_contract",
    "build_p7_r54_operation_reviewer_instruction_rating_form_freeze",
    "assert_p7_r54_operation_reviewer_instruction_rating_form_freeze_contract",
    "build_p7_r54_operation_actual_human_review_operation_state_capture",
    "assert_p7_r54_operation_actual_human_review_operation_state_capture_contract",
    "build_p7_r54_operation_sanitized_review_result_capture",
    "assert_p7_r54_operation_sanitized_review_result_capture_contract",
    "build_p7_r54_operation_rating_row_normalization",
    "assert_p7_r54_operation_rating_row_normalization_contract",
    "build_p7_r54_operation_readfeel_blocker_execution_blocker_ingestion",
    "assert_p7_r54_operation_readfeel_blocker_execution_blocker_ingestion_contract",
    "build_p7_r54_operation_question_need_observation_normalization",
    "assert_p7_r54_operation_question_need_observation_normalization_contract",
    "build_p7_r54_operation_rating_question_consistency_guard",
    "assert_p7_r54_operation_rating_question_consistency_guard_contract",
    "build_p7_r54_operation_scope_no_touch_boundary_freeze_bodyfree",
    "assert_p7_r54_operation_scope_no_touch_boundary_freeze_bodyfree_contract",
    "build_p7_r54_operation_current_snapshot_refreeze_bodyfree",
    "assert_p7_r54_operation_current_snapshot_refreeze_bodyfree_contract",
    "build_p7_r54_operation_historical_helper_source_delta_reconcile_bodyfree",
    "assert_p7_r54_operation_historical_helper_source_delta_reconcile_bodyfree_contract",
    "build_p7_r54_operation_r55_hold_intake_bodyfree",
    "assert_p7_r54_operation_r55_hold_intake_bodyfree_contract",
    "build_p7_r54_operation_local_only_preflight_bodyfree",
    "assert_p7_r54_operation_local_only_preflight_bodyfree_contract",
    "build_p7_r54_operation_24_case_manifest_freeze_bodyfree",
    "assert_p7_r54_operation_24_case_manifest_freeze_bodyfree_contract",
    "build_p7_r54_operation_body_full_packet_generation_request_bodyfree",
    "assert_p7_r54_operation_body_full_packet_generation_request_bodyfree_contract",
    "build_p7_r54_operation_packet_generation_local_operation_bodyfree",
    "assert_p7_r54_operation_packet_generation_local_operation_bodyfree_contract",
    "build_p7_r54_operation_packet_completeness_export_denylist_scan_bodyfree",
    "assert_p7_r54_operation_packet_completeness_export_denylist_scan_bodyfree_contract",
    "build_p7_r54_operation_reviewer_instruction_rating_form_freeze_bodyfree",
    "assert_p7_r54_operation_reviewer_instruction_rating_form_freeze_bodyfree_contract",
    "build_p7_r54_operation_actual_human_review_operation_state_capture_bodyfree",
    "assert_p7_r54_operation_actual_human_review_operation_state_capture_bodyfree_contract",
    "build_p7_r54_operation_sanitized_review_result_capture_bodyfree",
    "assert_p7_r54_operation_sanitized_review_result_capture_bodyfree_contract",
    "build_p7_r54_operation_rating_row_normalization_bodyfree",
    "assert_p7_r54_operation_rating_row_normalization_bodyfree_contract",
    "build_p7_r54_operation_readfeel_blocker_execution_blocker_ingestion_bodyfree",
    "assert_p7_r54_operation_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract",
    "build_p7_r54_operation_question_need_observation_normalization_bodyfree",
    "assert_p7_r54_operation_question_need_observation_normalization_bodyfree_contract",
    "build_p7_r54_operation_rating_question_consistency_guard_bodyfree",
    "assert_p7_r54_operation_rating_question_consistency_guard_bodyfree_contract",
)


__all__ = tuple(__all__) + (
    "P7_R54_OPERATION_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION",
    "P7_R54_OPERATION_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION",
    "P7_R54_OP16_STEP_REF",
    "P7_R54_OP17_STEP_REF",
    "P7_R54_OP18_STEP_REF",
    "P7_R54_OP16_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_OP16_PAUSED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_OP17_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_OP16_PROTOCOL_READY_STATUS_REF",
    "P7_R54_OP16_PROTOCOL_PAUSED_STATUS_REF",
    "P7_R54_OP16_PROTOCOL_ABORTED_STATUS_REF",
    "P7_R54_OP16_PROTOCOL_EXPIRED_STATUS_REF",
    "P7_R54_OP16_PROTOCOL_RATING_INCOMPLETE_STATUS_REF",
    "P7_R54_OP16_PROTOCOL_BLOCKED_STATUS_REF",
    "P7_R54_OP17_DISPOSAL_VERIFIED_STATUS_REF",
    "P7_R54_OP17_DISPOSAL_BLOCKED_STATUS_REF",
    "P7_R54_OP17_DISPOSAL_RECEIPT_REF",
    "P7_R54_OPERATION_PAUSE_ABORT_EXPIRATION_PROTOCOL_REQUIRED_FIELD_REFS",
    "P7_R54_OPERATION_PURGE_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS",
    "build_p7_r54_op16_pause_abort_expiration_protocol",
    "assert_p7_r54_op16_pause_abort_expiration_protocol_contract",
    "build_p7_r54_op17_purge_disposal_receipt",
    "assert_p7_r54_op17_purge_disposal_receipt_contract",
    "build_p7_r54_operation_pause_abort_expiration_protocol",
    "assert_p7_r54_operation_pause_abort_expiration_protocol_contract",
    "build_p7_r54_operation_purge_disposal_receipt",
    "assert_p7_r54_operation_purge_disposal_receipt_contract",
    "build_p7_r54_operation_pause_abort_expiration_protocol_bodyfree",
    "assert_p7_r54_operation_pause_abort_expiration_protocol_bodyfree_contract",
    "build_p7_r54_operation_purge_disposal_receipt_bodyfree",
    "assert_p7_r54_operation_purge_disposal_receipt_bodyfree_contract",
)


__all__ = tuple(__all__) + (
    "P7_R54_OPERATION_BODYFREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION",
    "P7_R54_OPERATION_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION",
    "P7_R54_OP19_STEP_REF",
    "P7_R54_OP20_STEP_REF",
    "P7_R54_OP18_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_OP19_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_OP19_P5_REPAIR_NEXT_REQUIRED_STEP_REF",
    "P7_R54_OP19_P4_R12_REPAIR_NEXT_REQUIRED_STEP_REF",
    "P7_R54_OP19_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF",
    "P7_R54_OP_NEXT_WORK_AFTER_OP18_REF",
    "P7_R54_OP_NEXT_WORK_AFTER_OP19_REF",
    "P7_R54_OP18_IMPLEMENTED_STEPS",
    "P7_R54_OP18_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_OP19_IMPLEMENTED_STEPS",
    "P7_R54_OP19_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_OP18_SUMMARY_READY_STATUS_REF",
    "P7_R54_OP18_SUMMARY_BLOCKED_STATUS_REF",
    "P7_R54_OP18_SUMMARY_REF",
    "P7_R54_OP19_DECISION_SEPARATION_READY_STATUS_REF",
    "P7_R54_OP19_DECISION_SEPARATION_BLOCKED_STATUS_REF",
    "P7_R54_OP19_DECISION_SEPARATION_REF",
    "P7_R54_OP19_P5_CONFIRMED_CANDIDATE_REF",
    "P7_R54_OP19_P5_REPAIR_RETURN_REF",
    "P7_R54_OP19_P4_R12_TARGETED_REPAIR_REF",
    "P7_R54_OP19_INCONCLUSIVE_REF",
    "P7_R54_OP19_DECISION_CANDIDATE_REFS",
    "P7_R54_OPERATION_BODYFREE_POST_REVIEW_SUMMARY_REQUIRED_FIELD_REFS",
    "P7_R54_OPERATION_P5_DECISION_CANDIDATE_SEPARATION_REQUIRED_FIELD_REFS",
    "build_p7_r54_op18_bodyfree_post_review_summary",
    "assert_p7_r54_op18_bodyfree_post_review_summary_contract",
    "build_p7_r54_op19_p5_decision_candidate_separation",
    "assert_p7_r54_op19_p5_decision_candidate_separation_contract",
    "build_p7_r54_operation_bodyfree_post_review_summary",
    "assert_p7_r54_operation_bodyfree_post_review_summary_contract",
    "build_p7_r54_operation_p5_decision_candidate_separation",
    "assert_p7_r54_operation_p5_decision_candidate_separation_contract",
    "build_p7_r54_operation_bodyfree_post_review_summary_bodyfree",
    "assert_p7_r54_operation_bodyfree_post_review_summary_bodyfree_contract",
    "build_p7_r54_operation_p5_decision_candidate_separation_bodyfree",
    "assert_p7_r54_operation_p5_decision_candidate_separation_bodyfree_contract",
)

# ---------------------------------------------------------------------------
# R54-OP-20 / R54-OP-21 operation-layer additions.
#
# These steps intentionally create candidate handoffs only.  They do not start
# P6/P8, do not finalize P5, and do not create question text or runtime/API/DB/RN
# mutations.
# ---------------------------------------------------------------------------

P7_R54_OPERATION_P6_CANDIDATE_HANDOFF_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_p6_candidate_handoff.bodyfree.v1"
)
P7_R54_OPERATION_P8_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_p8_material_candidate_handoff.bodyfree.v1"
)

# OP20 is already declared by OP18/OP19 as the next step. Keep that ref as-is.
P7_R54_OP21_STEP_REF: Final = "R54-OP-21_p8_material_candidate_handoff"
P7_R54_OP22_STEP_REF: Final = "R54-OP-22_final_no_body_leak_no_question_text_no_touch_validation"

P7_R54_OP20_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "p6_candidate_handoff_blocked_until_p5_confirmed_candidate_bodyfree"
)
P7_R54_OP21_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "p8_material_candidate_handoff_blocked_until_p6_candidate_handoff_ready"
)
P7_R54_OP_NEXT_WORK_AFTER_OP20_REF: Final = "r54_op21_p8_material_candidate_handoff_after_p6_candidate_handoff"
P7_R54_OP_NEXT_WORK_AFTER_OP21_REF: Final = "r54_op22_final_no_body_leak_no_question_text_no_touch_validation_after_p8_material_candidate_handoff"

P7_R54_OP20_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_OP19_IMPLEMENTED_STEPS,
    P7_R54_OP20_STEP_REF,
)
P7_R54_OP20_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = tuple(
    step for step in P7_R54_OP19_NOT_YET_IMPLEMENTED_STEPS if step != P7_R54_OP20_STEP_REF
)
P7_R54_OP21_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_OP20_IMPLEMENTED_STEPS,
    P7_R54_OP21_STEP_REF,
)
P7_R54_OP21_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = tuple(
    step for step in P7_R54_OP20_NOT_YET_IMPLEMENTED_STEPS if step != P7_R54_OP21_STEP_REF
)

P7_R54_OP20_P6_CANDIDATE_HANDOFF_READY_STATUS_REF: Final = "P6_CANDIDATE_HANDOFF_READY_BODYFREE"
P7_R54_OP20_P6_CANDIDATE_HANDOFF_BLOCKED_STATUS_REF: Final = "P6_CANDIDATE_HANDOFF_BLOCKED"
P7_R54_OP20_P6_CANDIDATE_HANDOFF_REF: Final = "R54_OP20_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_20260625"
P7_R54_OP20_P6_CANDIDATE_REF: Final = "P6_LIMITED_HUMAN_READFEEL_CANDIDATE_FROM_P5_CONFIRMED_CANDIDATE_BODYFREE"
P7_R54_OP20_READY_REASON_REF: Final = "p6_candidate_handoff_ready_from_p5_confirmed_candidate_bodyfree"
P7_R54_OP20_BLOCKED_REASON_REF: Final = "p6_candidate_handoff_blocked_until_p5_confirmed_candidate"
P7_R54_OP20_CANDIDATE_ONLY_POLICY_REF: Final = "p6_candidate_only_start_allowed_false"

P7_R54_OP21_P8_MATERIAL_HANDOFF_READY_STATUS_REF: Final = "P8_MATERIAL_CANDIDATE_HANDOFF_READY_BODYFREE"
P7_R54_OP21_P8_MATERIAL_HANDOFF_BLOCKED_STATUS_REF: Final = "P8_MATERIAL_CANDIDATE_HANDOFF_BLOCKED"
P7_R54_OP21_P8_MATERIAL_HANDOFF_REF: Final = "R54_OP21_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_20260625"
P7_R54_OP21_P8_MATERIAL_CANDIDATE_REF: Final = "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_FROM_R54_BODYFREE_OBSERVATION"
P7_R54_OP21_READY_REASON_REF: Final = "p8_material_candidate_handoff_ready_from_question_need_observation_rows_bodyfree"
P7_R54_OP21_NO_MATERIAL_REASON_REF: Final = "p8_material_candidate_handoff_ready_no_question_material_rows_bodyfree"
P7_R54_OP21_BLOCKED_REASON_REF: Final = "p8_material_candidate_handoff_blocked_until_p6_candidate_handoff_ready"
P7_R54_OP21_CANDIDATE_ONLY_POLICY_REF: Final = "p8_material_candidate_only_start_allowed_false_question_implementation_false"

P7_R54_OP21_P8_MATERIAL_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = (
    *P7_R54_OP14_P8_MATERIAL_CANDIDATE_PRIMARY_CLASS_REFS,
)

P7_R54_OPERATION_P6_CANDIDATE_HANDOFF_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op19_schema_version", "op19_material_ref", "op19_next_required_step", "op19_decision_candidate_separation_status",
    "op19_p5_decision_candidate_ref", "op19_p5_confirmed_candidate_conditions_met", "op19_p5_human_blind_qa_confirmed_candidate",
    "operation_current_refs", "operation_current_ref_count", "actual_review_basis_ref", "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis", "required_case_count", "reviewed_case_count", "rating_row_count",
    "question_observation_row_count", "p6_candidate_handoff_status", "p6_candidate_handoff_ref", "p6_candidate_handoff_reason_refs",
    "p6_limited_human_readfeel_candidate_ref", "p6_limited_human_readfeel_candidate", "p6_limited_human_readfeel_start_allowed",
    "p6_candidate_basis_ref", "p6_candidate_only_policy_ref", "p6_candidate_only_not_start", "p6_start_blocked_here",
    "p6_candidate_handoff_materialized_here", "p8_material_candidate_handoff_allowed_next", "p8_material_candidate_row_count",
    "p8_material_candidate_primary_class_counts", "p8_material_candidate_primary_class_refs", "primary_class_counts",
    "verdict_counts", "axis_score_averages", "rating_axis_target_thresholds", "below_target_axis_refs",
    "open_readfeel_blocker_count", "open_execution_blocker_count", "disposal_verified", "no_body_leak_validation_passed",
    "no_question_text_validation_passed", "no_touch_validation_passed", "p5_human_blind_qa_confirmed_candidate",
    "p5_human_blind_qa_confirmed_final", "p8_question_design_material_candidate", "p8_start_allowed",
    "question_implementation_started_here", "p8_implementation_spec_finalized_here", "release_allowed",
    "actual_review_evidence_complete", "human_review_completion_claim_blocked_here", "p6_p8_release_promotion_blocked_here",
    "execution_blocker_ids", "open_execution_blocker_ids", "implemented_steps", "not_yet_implemented_steps",
    "first_next_work_ref", "next_required_step", "public_contract", "r54_operation_no_touch_contract",
    "body_free_markers", "body_free", "question_text_included", "draft_question_text_included", "local_path_included",
    *P7_R54_OPERATION_FALSE_FLAG_REFS,
)

P7_R54_OPERATION_P8_MATERIAL_CANDIDATE_HANDOFF_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op20_schema_version", "op20_material_ref", "op20_next_required_step", "op20_p6_candidate_handoff_status",
    "op20_p6_limited_human_readfeel_candidate", "op20_p6_limited_human_readfeel_start_allowed", "operation_current_refs",
    "operation_current_ref_count", "actual_review_basis_ref", "actual_review_basis_allowed", "operation_current_refs_are_actual_review_basis",
    "required_case_count", "reviewed_case_count", "rating_row_count", "question_observation_row_count",
    "p8_material_candidate_handoff_status", "p8_material_candidate_handoff_ref", "p8_material_candidate_handoff_reason_refs",
    "question_need_observation_rows_aggregated", "question_need_observation_rows_aggregated_count", "p8_material_candidate_primary_class_refs",
    "p8_material_candidate_primary_class_counts", "p8_material_candidate_row_count", "p8_question_design_material_candidate",
    "p8_question_design_material_candidate_ref", "p8_design_material_candidate_only_not_start", "p8_candidate_only_policy_ref", "p8_start_allowed",
    "question_implementation_started_here", "p8_implementation_spec_finalized_here", "question_trigger_logic_implemented",
    "question_answer_persistence_implemented", "question_api_implemented", "question_db_schema_implemented", "question_rn_ui_implemented",
    "question_response_key_implemented", "question_plan_guard_implemented", "question_storage_schema_implemented",
    "question_text_materialized_here", "draft_question_text_materialized_here", "question_text_included", "draft_question_text_included",
    "api_db_rn_response_key_changed_here", "runtime_changed_here", "p5_human_blind_qa_confirmed_candidate",
    "p5_human_blind_qa_confirmed_final", "p6_limited_human_readfeel_candidate",
    "p6_limited_human_readfeel_start_allowed", "release_allowed", "actual_review_evidence_complete",
    "human_review_completion_claim_blocked_here", "p6_p8_release_promotion_blocked_here", "execution_blocker_ids",
    "open_execution_blocker_ids", "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step",
    "public_contract", "r54_operation_no_touch_contract", "body_free_markers", "body_free", "local_path_included",
    "disposal_verified", *P7_R54_OPERATION_FALSE_FLAG_REFS,
)


def _op20_false_flag_refs() -> tuple[str, ...]:
    return tuple(
        key for key in P7_R54_OPERATION_FALSE_FLAG_REFS
        if key not in {"disposal_verified", "p5_human_blind_qa_confirmed_candidate", "p6_limited_human_readfeel_candidate"}
    )


def _op21_false_flag_refs() -> tuple[str, ...]:
    return tuple(
        key for key in P7_R54_OPERATION_FALSE_FLAG_REFS
        if key not in {"disposal_verified", "p5_human_blind_qa_confirmed_candidate", "p6_limited_human_readfeel_candidate", "p8_question_design_material_candidate"}
    )


def _op20_p8_material_candidate_primary_class_counts(primary_class_counts: Mapping[str, Any]) -> dict[str, int]:
    counts = safe_mapping(primary_class_counts)
    out: dict[str, int] = {}
    for primary_class_ref in P7_R54_OP21_P8_MATERIAL_PRIMARY_CLASS_REFS:
        try:
            count = int(counts.get(primary_class_ref) or 0)
        except (TypeError, ValueError):
            count = 0
        if count > 0:
            out[primary_class_ref] = count
    return out


def _op20_blocker_refs(op19: Mapping[str, Any]) -> list[str]:
    data = safe_mapping(op19)
    blockers: list[str] = []
    if data.get("decision_candidate_separation_status") != P7_R54_OP19_DECISION_SEPARATION_READY_STATUS_REF:
        blockers.append("op19_p5_decision_candidate_separation_not_ready_for_p6_handoff")
    if data.get("p5_decision_candidate_ref") != P7_R54_OP19_P5_CONFIRMED_CANDIDATE_REF:
        blockers.append("p5_confirmed_candidate_not_available_for_p6_handoff")
    if data.get("p5_confirmed_candidate_conditions_met") is not True:
        blockers.append("p5_confirmed_candidate_conditions_not_met_for_p6_handoff")
    if data.get("p5_human_blind_qa_confirmed_candidate") is not True:
        blockers.append("p5_human_blind_qa_confirmed_candidate_flag_not_true_for_p6_handoff")
    if data.get("next_required_step") != P7_R54_OP20_STEP_REF:
        blockers.append("op19_next_required_step_not_op20_p6_candidate_handoff")
    if data.get("p5_human_blind_qa_confirmed_final") is not False:
        blockers.append("p5_final_confirmation_must_not_precede_p6_candidate_handoff")
    if data.get("p6_limited_human_readfeel_start_allowed") is not False or data.get("p8_start_allowed") is not False or data.get("release_allowed") is not False:
        blockers.append("op19_must_not_allow_p6_p8_or_release_before_handoff")
    return dedupe_identifiers(blockers, limit=60, max_length=180)


def build_p7_r54_op20_p6_candidate_handoff(
    *,
    p5_decision_candidate_separation: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_operation_p6_candidate_handoff",
) -> dict[str, Any]:
    """Build R54-OP-20 body-free P6 candidate handoff, not P6 start."""
    op19 = safe_mapping(p5_decision_candidate_separation) if p5_decision_candidate_separation is not None else build_p7_r54_op19_p5_decision_candidate_separation()
    assert_p7_r54_op19_p5_decision_candidate_separation_contract(op19)
    blockers = _op20_blocker_refs(op19)
    ready = not blockers
    p8_primary_counts = _op20_p8_material_candidate_primary_class_counts(op19.get("primary_class_counts") or {}) if ready else {}
    p8_candidate_row_count = sum(p8_primary_counts.values())
    material = {
        "schema_version": P7_R54_OPERATION_P6_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_OPERATION_REENTRY_STEP,
        "scope": P7_R54_OPERATION_REENTRY_SCOPE,
        "policy_kind": P7_R54_OPERATION_REENTRY_POLICY_KIND,
        "policy_section": P7_R54_OP20_STEP_REF,
        "operation_step_ref": P7_R54_OP20_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_operation_p6_candidate_handoff", max_length=220),
        "review_session_id": _safe_review_session_id(op19.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op19_schema_version": P7_R54_OPERATION_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION,
        "op19_material_ref": clean_identifier(op19.get("material_id"), default="p7_r54_operation_p5_decision_candidate_separation", max_length=220),
        "op19_next_required_step": clean_identifier(op19.get("next_required_step"), default="", max_length=180),
        "op19_decision_candidate_separation_status": clean_identifier(op19.get("decision_candidate_separation_status"), default=P7_R54_OP19_DECISION_SEPARATION_BLOCKED_STATUS_REF, max_length=180),
        "op19_p5_decision_candidate_ref": clean_identifier(op19.get("p5_decision_candidate_ref"), default=P7_R54_OP19_INCONCLUSIVE_REF, max_length=180),
        "op19_p5_confirmed_candidate_conditions_met": op19.get("p5_confirmed_candidate_conditions_met") is True,
        "op19_p5_human_blind_qa_confirmed_candidate": op19.get("p5_human_blind_qa_confirmed_candidate") is True,
        "operation_current_refs": dict(P7_R54_OPERATION_CURRENT_REFS),
        "operation_current_ref_count": len(P7_R54_OPERATION_CURRENT_REFS),
        "actual_review_basis_ref": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "reviewed_case_count": int(op19.get("reviewed_case_count") or 0) if ready else 0,
        "rating_row_count": int(op19.get("rating_row_count") or 0) if ready else 0,
        "question_observation_row_count": int(op19.get("question_observation_row_count") or 0) if ready else 0,
        "p6_candidate_handoff_status": P7_R54_OP20_P6_CANDIDATE_HANDOFF_READY_STATUS_REF if ready else P7_R54_OP20_P6_CANDIDATE_HANDOFF_BLOCKED_STATUS_REF,
        "p6_candidate_handoff_ref": P7_R54_OP20_P6_CANDIDATE_HANDOFF_REF if ready else "p6_candidate_handoff_not_ready",
        "p6_candidate_handoff_reason_refs": [P7_R54_OP20_READY_REASON_REF] if ready else dedupe_identifiers([P7_R54_OP20_BLOCKED_REASON_REF, *blockers], limit=80, max_length=180),
        "p6_limited_human_readfeel_candidate_ref": P7_R54_OP20_P6_CANDIDATE_REF if ready else "",
        **_false_flags(),
        "p5_human_blind_qa_confirmed_candidate": op19.get("p5_human_blind_qa_confirmed_candidate") is True and ready,
        "p6_limited_human_readfeel_candidate": ready,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_candidate_basis_ref": "p5_confirmed_candidate_conditions_bodyfree_review_summary" if ready else "p5_confirmed_candidate_required_before_p6_candidate",
        "p6_candidate_only_policy_ref": P7_R54_OP20_CANDIDATE_ONLY_POLICY_REF,
        "p6_candidate_only_not_start": True,
        "p6_start_blocked_here": True,
        "p6_candidate_handoff_materialized_here": ready,
        "p8_material_candidate_handoff_allowed_next": ready,
        "p8_material_candidate_row_count": p8_candidate_row_count,
        "p8_material_candidate_primary_class_counts": dict(p8_primary_counts),
        "p8_material_candidate_primary_class_refs": list(p8_primary_counts.keys()),
        "primary_class_counts": dict(safe_mapping(op19.get("primary_class_counts"))) if ready else {},
        "verdict_counts": dict(safe_mapping(op19.get("verdict_counts"))) if ready else {},
        "axis_score_averages": dict(safe_mapping(op19.get("axis_score_averages"))) if ready else {},
        "rating_axis_target_thresholds": dict(P7_R54_OP09_RATING_AXIS_TARGET_THRESHOLDS),
        "below_target_axis_refs": list(op19.get("below_target_axis_refs") or []) if ready else [],
        "open_readfeel_blocker_count": int(op19.get("open_readfeel_blocker_count") or 0) if ready else 0,
        "open_execution_blocker_count": int(op19.get("open_execution_blocker_count") or 0) if ready else len(blockers),
        "disposal_verified": op19.get("disposal_verified") is True and ready,
        "no_body_leak_validation_passed": ready,
        "no_question_text_validation_passed": ready,
        "no_touch_validation_passed": ready,
        "p5_human_blind_qa_confirmed_final": False,
        "p8_question_design_material_candidate": False,
        "p8_start_allowed": False,
        "question_implementation_started_here": False,
        "p8_implementation_spec_finalized_here": False,
        "release_allowed": False,
        "actual_review_evidence_complete": False,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "execution_blocker_ids": [] if ready else dedupe_identifiers(blockers, limit=80, max_length=180),
        "open_execution_blocker_ids": [] if ready else dedupe_identifiers(blockers, limit=80, max_length=180),
        "implemented_steps": list(P7_R54_OP20_IMPLEMENTED_STEPS if ready else tuple(op19.get("implemented_steps") or ())),
        "not_yet_implemented_steps": list(P7_R54_OP20_NOT_YET_IMPLEMENTED_STEPS if ready else tuple(op19.get("not_yet_implemented_steps") or ())),
        "first_next_work_ref": P7_R54_OP_NEXT_WORK_AFTER_OP20_REF if ready else P7_R54_OP_NEXT_WORK_AFTER_OP19_REF,
        "next_required_step": P7_R54_OP21_STEP_REF if ready else P7_R54_OP20_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_operation_no_touch_contract": _operation_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
    }
    assert_p7_r54_op20_p6_candidate_handoff_contract(material)
    return material


def assert_p7_r54_op20_p6_candidate_handoff_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_OPERATION_P6_CANDIDATE_HANDOFF_REQUIRED_FIELD_REFS, source="p7_r54_op20_p6_candidate_handoff")
    _assert_common_operation_contract(
        data,
        schema_version=P7_R54_OPERATION_P6_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        policy_section=P7_R54_OP20_STEP_REF,
        operation_step_ref=P7_R54_OP20_STEP_REF,
        source="p7_r54_op20_p6_candidate_handoff",
        false_flag_refs=_op20_false_flag_refs(),
    )
    _assert_operation_current_refs(data, source="p7_r54_op20_p6_candidate_handoff")
    if data.get("p6_limited_human_readfeel_start_allowed") is not False or data.get("p8_start_allowed") is not False or data.get("release_allowed") is not False:
        raise ValueError("R54 OP20 must not start P6/P8 or release")
    if data.get("p5_human_blind_qa_confirmed_final") is not False or data.get("actual_review_evidence_complete") is not False:
        raise ValueError("R54 OP20 must not finalize P5 or actual review evidence")
    if data.get("p8_question_design_material_candidate") is not False or data.get("question_implementation_started_here") is not False or data.get("p8_implementation_spec_finalized_here") is not False:
        raise ValueError("R54 OP20 must not create P8 material candidate or implementation")
    if data.get("p6_candidate_only_not_start") is not True or data.get("p6_start_blocked_here") is not True:
        raise ValueError("R54 OP20 must explicitly block P6 start")
    ready = data.get("p6_candidate_handoff_status") == P7_R54_OP20_P6_CANDIDATE_HANDOFF_READY_STATUS_REF
    if data.get("p6_limited_human_readfeel_candidate") is not ready:
        raise ValueError("R54 OP20 P6 candidate flag must match handoff readiness")
    if data.get("p6_candidate_handoff_materialized_here") is not ready:
        raise ValueError("R54 OP20 materialization flag must match readiness")
    if data.get("p8_material_candidate_handoff_allowed_next") is not ready:
        raise ValueError("R54 OP20 P8 material handoff allowance must match readiness")
    if ready:
        if data.get("p6_candidate_handoff_ref") != P7_R54_OP20_P6_CANDIDATE_HANDOFF_REF:
            raise ValueError("R54 OP20 ready handoff ref changed")
        if data.get("p6_limited_human_readfeel_candidate_ref") != P7_R54_OP20_P6_CANDIDATE_REF:
            raise ValueError("R54 OP20 P6 candidate ref changed")
        if data.get("p6_candidate_handoff_reason_refs") != [P7_R54_OP20_READY_REASON_REF]:
            raise ValueError("R54 OP20 ready reason refs changed")
        if data.get("op19_p5_decision_candidate_ref") != P7_R54_OP19_P5_CONFIRMED_CANDIDATE_REF or data.get("op19_p5_confirmed_candidate_conditions_met") is not True:
            raise ValueError("R54 OP20 ready requires OP19 P5 confirmed candidate")
        if data.get("op19_p5_human_blind_qa_confirmed_candidate") is not True or data.get("p5_human_blind_qa_confirmed_candidate") is not True:
            raise ValueError("R54 OP20 ready must retain P5 candidate basis as body-free")
        if data.get("rating_row_count") != P7_R51_REQUIRED_CASE_COUNT or data.get("question_observation_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 OP20 ready must preserve 24 rating/question rows")
        if data.get("open_readfeel_blocker_count") != 0 or data.get("open_execution_blocker_count") != 0 or data.get("open_execution_blocker_ids"):
            raise ValueError("R54 OP20 ready must not carry open blockers")
        if data.get("disposal_verified") is not True:
            raise ValueError("R54 OP20 ready must preserve verified disposal receipt")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_OP20_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP20 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_OP20_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP20 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_OP21_STEP_REF:
            raise ValueError("R54 OP20 ready must point to OP21")
    else:
        if data.get("p6_candidate_handoff_status") != P7_R54_OP20_P6_CANDIDATE_HANDOFF_BLOCKED_STATUS_REF:
            raise ValueError("R54 OP20 blocked status changed")
        if data.get("p6_candidate_handoff_ref") != "p6_candidate_handoff_not_ready":
            raise ValueError("R54 OP20 blocked handoff ref changed")
        if not data.get("open_execution_blocker_ids"):
            raise ValueError("R54 OP20 blocked must carry execution blockers")
        if data.get("next_required_step") != P7_R54_OP20_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 OP20 blocked must point to repair")
    return True


def build_p7_r54_op21_p8_material_candidate_handoff(
    *,
    p6_candidate_handoff: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_operation_p8_material_candidate_handoff",
) -> dict[str, Any]:
    """Build R54-OP-21 body-free P8 material candidate handoff, not P8 start."""
    op20 = safe_mapping(p6_candidate_handoff) if p6_candidate_handoff is not None else build_p7_r54_op20_p6_candidate_handoff()
    assert_p7_r54_op20_p6_candidate_handoff_contract(op20)
    ready = bool(
        op20.get("p6_candidate_handoff_status") == P7_R54_OP20_P6_CANDIDATE_HANDOFF_READY_STATUS_REF
        and op20.get("p8_material_candidate_handoff_allowed_next") is True
        and op20.get("next_required_step") == P7_R54_OP21_STEP_REF
    )
    blockers = [] if ready else [P7_R54_OP21_BLOCKED_REASON_REF, "op20_p6_candidate_handoff_not_ready_for_p8_material_candidate_handoff"]
    p8_primary_counts = dict(safe_mapping(op20.get("p8_material_candidate_primary_class_counts"))) if ready else {}
    p8_candidate_row_count = sum(int(value or 0) for value in p8_primary_counts.values()) if ready else 0
    p8_candidate = bool(ready and p8_candidate_row_count > 0)
    material = {
        "schema_version": P7_R54_OPERATION_P8_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_OPERATION_REENTRY_STEP,
        "scope": P7_R54_OPERATION_REENTRY_SCOPE,
        "policy_kind": P7_R54_OPERATION_REENTRY_POLICY_KIND,
        "policy_section": P7_R54_OP21_STEP_REF,
        "operation_step_ref": P7_R54_OP21_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_operation_p8_material_candidate_handoff", max_length=220),
        "review_session_id": _safe_review_session_id(op20.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op20_schema_version": P7_R54_OPERATION_P6_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        "op20_material_ref": clean_identifier(op20.get("material_id"), default="p7_r54_operation_p6_candidate_handoff", max_length=220),
        "op20_next_required_step": clean_identifier(op20.get("next_required_step"), default="", max_length=180),
        "op20_p6_candidate_handoff_status": clean_identifier(op20.get("p6_candidate_handoff_status"), default=P7_R54_OP20_P6_CANDIDATE_HANDOFF_BLOCKED_STATUS_REF, max_length=180),
        "op20_p6_limited_human_readfeel_candidate": op20.get("p6_limited_human_readfeel_candidate") is True,
        "op20_p6_limited_human_readfeel_start_allowed": False,
        "operation_current_refs": dict(P7_R54_OPERATION_CURRENT_REFS),
        "operation_current_ref_count": len(P7_R54_OPERATION_CURRENT_REFS),
        "actual_review_basis_ref": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "reviewed_case_count": int(op20.get("reviewed_case_count") or 0) if ready else 0,
        "rating_row_count": int(op20.get("rating_row_count") or 0) if ready else 0,
        "question_observation_row_count": int(op20.get("question_observation_row_count") or 0) if ready else 0,
        "p8_material_candidate_handoff_status": P7_R54_OP21_P8_MATERIAL_HANDOFF_READY_STATUS_REF if ready else P7_R54_OP21_P8_MATERIAL_HANDOFF_BLOCKED_STATUS_REF,
        "p8_material_candidate_handoff_ref": P7_R54_OP21_P8_MATERIAL_HANDOFF_REF if ready else "p8_material_candidate_handoff_not_ready",
        "p8_material_candidate_handoff_reason_refs": (
            [P7_R54_OP21_READY_REASON_REF] if p8_candidate else [P7_R54_OP21_NO_MATERIAL_REASON_REF]
        ) if ready else dedupe_identifiers(blockers, limit=80, max_length=180),
        "question_need_observation_rows_aggregated": ready,
        "question_need_observation_rows_aggregated_count": int(op20.get("question_observation_row_count") or 0) if ready else 0,
        "p8_material_candidate_primary_class_refs": list(p8_primary_counts.keys()),
        "p8_material_candidate_primary_class_counts": p8_primary_counts,
        "p8_material_candidate_row_count": p8_candidate_row_count,
        **_false_flags(),
        "disposal_verified": op20.get("disposal_verified") is True and ready,
        "p5_human_blind_qa_confirmed_candidate": op20.get("p5_human_blind_qa_confirmed_candidate") is True and ready,
        "p6_limited_human_readfeel_candidate": op20.get("p6_limited_human_readfeel_candidate") is True if ready else False,
        "p8_question_design_material_candidate": p8_candidate,
        "p8_question_design_material_candidate_ref": P7_R54_OP21_P8_MATERIAL_CANDIDATE_REF if p8_candidate else "",
        "p8_design_material_candidate_only_not_start": True,
        "p8_candidate_only_policy_ref": P7_R54_OP21_CANDIDATE_ONLY_POLICY_REF,
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
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "release_allowed": False,
        "actual_review_evidence_complete": False,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "execution_blocker_ids": [] if ready else dedupe_identifiers(blockers, limit=80, max_length=180),
        "open_execution_blocker_ids": [] if ready else dedupe_identifiers(blockers, limit=80, max_length=180),
        "implemented_steps": list(P7_R54_OP21_IMPLEMENTED_STEPS if ready else tuple(op20.get("implemented_steps") or ())),
        "not_yet_implemented_steps": list(P7_R54_OP21_NOT_YET_IMPLEMENTED_STEPS if ready else tuple(op20.get("not_yet_implemented_steps") or ())),
        "first_next_work_ref": P7_R54_OP_NEXT_WORK_AFTER_OP21_REF if ready else P7_R54_OP_NEXT_WORK_AFTER_OP20_REF,
        "next_required_step": P7_R54_OP22_STEP_REF if ready else P7_R54_OP21_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_operation_no_touch_contract": _operation_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "local_path_included": False,
    }
    assert_p7_r54_op21_p8_material_candidate_handoff_contract(material)
    return material


def assert_p7_r54_op21_p8_material_candidate_handoff_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_OPERATION_P8_MATERIAL_CANDIDATE_HANDOFF_REQUIRED_FIELD_REFS, source="p7_r54_op21_p8_material_candidate_handoff")
    _assert_common_operation_contract(
        data,
        schema_version=P7_R54_OPERATION_P8_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        policy_section=P7_R54_OP21_STEP_REF,
        operation_step_ref=P7_R54_OP21_STEP_REF,
        source="p7_r54_op21_p8_material_candidate_handoff",
        false_flag_refs=_op21_false_flag_refs(),
    )
    _assert_operation_current_refs(data, source="p7_r54_op21_p8_material_candidate_handoff")
    if data.get("p8_start_allowed") is not False or data.get("release_allowed") is not False:
        raise ValueError("R54 OP21 must not start P8 or release")
    for false_key in (
        "question_implementation_started_here", "p8_implementation_spec_finalized_here", "question_trigger_logic_implemented",
        "question_answer_persistence_implemented", "question_api_implemented", "question_db_schema_implemented", "question_rn_ui_implemented",
        "question_response_key_implemented", "question_plan_guard_implemented", "question_storage_schema_implemented",
        "question_text_materialized_here", "draft_question_text_materialized_here", "api_db_rn_response_key_changed_here", "runtime_changed_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 OP21 must keep {false_key}=False")
    if data.get("p8_design_material_candidate_only_not_start") is not True:
        raise ValueError("R54 OP21 must be candidate-only, not P8 start")
    if data.get("actual_review_evidence_complete") is not False or data.get("p5_human_blind_qa_confirmed_final") is not False:
        raise ValueError("R54 OP21 must not finalize P5 or actual review evidence")
    ready = data.get("p8_material_candidate_handoff_status") == P7_R54_OP21_P8_MATERIAL_HANDOFF_READY_STATUS_REF
    if data.get("question_need_observation_rows_aggregated") is not ready:
        raise ValueError("R54 OP21 aggregation flag must match readiness")
    candidate_count = int(data.get("p8_material_candidate_row_count") or 0)
    if data.get("p8_question_design_material_candidate") is not bool(ready and candidate_count > 0):
        raise ValueError("R54 OP21 P8 candidate flag must match material row count")
    if ready:
        if data.get("p8_material_candidate_handoff_ref") != P7_R54_OP21_P8_MATERIAL_HANDOFF_REF:
            raise ValueError("R54 OP21 ready handoff ref changed")
        expected_reason_refs = [P7_R54_OP21_READY_REASON_REF] if candidate_count > 0 else [P7_R54_OP21_NO_MATERIAL_REASON_REF]
        if data.get("p8_material_candidate_handoff_reason_refs") != expected_reason_refs:
            raise ValueError("R54 OP21 ready/no-material reason refs changed")
        if data.get("question_observation_row_count") != P7_R51_REQUIRED_CASE_COUNT or data.get("question_need_observation_rows_aggregated_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 OP21 ready must aggregate 24 question observation rows")
        if data.get("op20_p6_limited_human_readfeel_candidate") is not True or data.get("p6_limited_human_readfeel_candidate") is not True:
            raise ValueError("R54 OP21 ready must retain P6 candidate basis")
        if data.get("p6_limited_human_readfeel_start_allowed") is not False:
            raise ValueError("R54 OP21 must keep P6 start blocked")
        if data.get("disposal_verified") is not True:
            raise ValueError("R54 OP21 ready must preserve verified disposal receipt")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_OP21_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP21 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_OP21_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP21 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_OP22_STEP_REF:
            raise ValueError("R54 OP21 ready must point to OP22")
        if data.get("open_execution_blocker_ids"):
            raise ValueError("R54 OP21 ready must not carry open execution blockers")
    else:
        if data.get("p8_material_candidate_handoff_status") != P7_R54_OP21_P8_MATERIAL_HANDOFF_BLOCKED_STATUS_REF:
            raise ValueError("R54 OP21 blocked status changed")
        if data.get("p8_material_candidate_handoff_ref") != "p8_material_candidate_handoff_not_ready":
            raise ValueError("R54 OP21 blocked handoff ref changed")
        if data.get("p8_question_design_material_candidate") is not False:
            raise ValueError("R54 OP21 blocked must not set P8 material candidate")
        if not data.get("open_execution_blocker_ids"):
            raise ValueError("R54 OP21 blocked must carry execution blockers")
        if data.get("next_required_step") != P7_R54_OP21_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 OP21 blocked must point to repair")
    return True


# OP20/OP21 detailed-design wording aliases.
build_p7_r54_operation_p6_candidate_handoff = build_p7_r54_op20_p6_candidate_handoff
assert_p7_r54_operation_p6_candidate_handoff_contract = assert_p7_r54_op20_p6_candidate_handoff_contract
build_p7_r54_operation_p8_material_candidate_handoff = build_p7_r54_op21_p8_material_candidate_handoff
assert_p7_r54_operation_p8_material_candidate_handoff_contract = assert_p7_r54_op21_p8_material_candidate_handoff_contract
build_p7_r54_operation_p6_candidate_handoff_bodyfree = build_p7_r54_operation_p6_candidate_handoff
assert_p7_r54_operation_p6_candidate_handoff_bodyfree_contract = assert_p7_r54_operation_p6_candidate_handoff_contract
build_p7_r54_operation_p8_material_candidate_handoff_bodyfree = build_p7_r54_operation_p8_material_candidate_handoff
assert_p7_r54_operation_p8_material_candidate_handoff_bodyfree_contract = assert_p7_r54_operation_p8_material_candidate_handoff_contract

__all__ = tuple(__all__) + (
    "P7_R54_OPERATION_P6_CANDIDATE_HANDOFF_SCHEMA_VERSION",
    "P7_R54_OPERATION_P8_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION",
    "P7_R54_OP21_STEP_REF",
    "P7_R54_OP22_STEP_REF",
    "P7_R54_OP20_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_OP21_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_OP_NEXT_WORK_AFTER_OP20_REF",
    "P7_R54_OP_NEXT_WORK_AFTER_OP21_REF",
    "P7_R54_OP20_IMPLEMENTED_STEPS",
    "P7_R54_OP20_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_OP21_IMPLEMENTED_STEPS",
    "P7_R54_OP21_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_OP20_P6_CANDIDATE_HANDOFF_READY_STATUS_REF",
    "P7_R54_OP20_P6_CANDIDATE_HANDOFF_BLOCKED_STATUS_REF",
    "P7_R54_OP20_P6_CANDIDATE_HANDOFF_REF",
    "P7_R54_OP20_P6_CANDIDATE_REF",
    "P7_R54_OP20_CANDIDATE_ONLY_POLICY_REF",
    "P7_R54_OP21_P8_MATERIAL_HANDOFF_READY_STATUS_REF",
    "P7_R54_OP21_P8_MATERIAL_HANDOFF_BLOCKED_STATUS_REF",
    "P7_R54_OP21_P8_MATERIAL_HANDOFF_REF",
    "P7_R54_OP21_P8_MATERIAL_CANDIDATE_REF",
    "P7_R54_OP21_CANDIDATE_ONLY_POLICY_REF",
    "P7_R54_OP21_P8_MATERIAL_PRIMARY_CLASS_REFS",
    "P7_R54_OPERATION_P6_CANDIDATE_HANDOFF_REQUIRED_FIELD_REFS",
    "P7_R54_OPERATION_P8_MATERIAL_CANDIDATE_HANDOFF_REQUIRED_FIELD_REFS",
    "build_p7_r54_op20_p6_candidate_handoff",
    "assert_p7_r54_op20_p6_candidate_handoff_contract",
    "build_p7_r54_op21_p8_material_candidate_handoff",
    "assert_p7_r54_op21_p8_material_candidate_handoff_contract",
    "build_p7_r54_operation_p6_candidate_handoff",
    "assert_p7_r54_operation_p6_candidate_handoff_contract",
    "build_p7_r54_operation_p8_material_candidate_handoff",
    "assert_p7_r54_operation_p8_material_candidate_handoff_contract",
    "build_p7_r54_operation_p6_candidate_handoff_bodyfree",
    "assert_p7_r54_operation_p6_candidate_handoff_bodyfree_contract",
    "build_p7_r54_operation_p8_material_candidate_handoff_bodyfree",
    "assert_p7_r54_operation_p8_material_candidate_handoff_bodyfree_contract",
)



# ---------------------------------------------------------------------------
# R54-OP-22 / R54-OP-23: final validation and R52 re-intake handoff.
# ---------------------------------------------------------------------------

P7_R54_OPERATION_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_final_no_body_leak_no_question_text_no_touch_validation.bodyfree.v1"
)
P7_R54_OPERATION_R52_REINTAKE_HANDOFF_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_r52_reintake_handoff.bodyfree.v1"
)

P7_R54_OP23_STEP_REF: Final = "R54-OP-23_r52_reintake_handoff"
P7_R54_OP24_STEP_REF: Final = "R54-OP-24_validation_command_matrix_documentation_output"

P7_R54_OP22_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "r54_op22_final_validation_repair_before_r52_reintake_handoff"
P7_R54_OP22_BODY_LEAK_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "body_leak_or_question_text_repair_before_r52_reintake_handoff"
P7_R54_OP22_NO_TOUCH_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "no_touch_boundary_repair_before_r52_reintake_handoff"
P7_R54_OP23_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "r52_reintake_handoff_blocked_until_bodyfree_actual_review_evidence_ready"
P7_R54_OP23_DISPOSAL_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "disposal_receipt_repair_before_r52_reintake_handoff"
P7_R54_OP23_BODY_LEAK_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "body_leak_or_question_text_repair_before_r52_reintake_handoff"
P7_R54_OP23_NO_TOUCH_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "no_touch_boundary_repair_before_r52_reintake_handoff"
P7_R54_OP23_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF: Final = "r54_operation_inconclusive_retry_or_r52_reintake_repair"
P7_R54_OP_NEXT_WORK_AFTER_OP22_REF: Final = "r54_op23_r52_reintake_handoff_after_final_validation"
P7_R54_OP_NEXT_WORK_AFTER_OP23_REF: Final = "r54_op24_validation_command_matrix_documentation_output_after_r52_handoff"

P7_R54_OP22_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_OP21_IMPLEMENTED_STEPS, P7_R54_OP22_STEP_REF)
P7_R54_OP22_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = tuple(
    step for step in P7_R54_OP21_NOT_YET_IMPLEMENTED_STEPS if step != P7_R54_OP22_STEP_REF
)
P7_R54_OP23_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_OP22_IMPLEMENTED_STEPS, P7_R54_OP23_STEP_REF)
P7_R54_OP23_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = tuple(
    step for step in P7_R54_OP22_NOT_YET_IMPLEMENTED_STEPS if step != P7_R54_OP23_STEP_REF
)

P7_R54_OP22_FINAL_VALIDATION_READY_STATUS_REF: Final = "FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_READY_BODYFREE"
P7_R54_OP22_FINAL_VALIDATION_BLOCKED_STATUS_REF: Final = "FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_BLOCKED"
P7_R54_OP22_FINAL_VALIDATION_BLOCKED_BY_OP21_STATUS_REF: Final = P7_R54_OP22_FINAL_VALIDATION_BLOCKED_STATUS_REF
P7_R54_OP22_BODY_LEAK_BLOCKED_STATUS_REF: Final = "R54_OPERATION_BLOCKED_BODY_LEAK_OR_QUESTION_TEXT"
P7_R54_OP22_FINAL_VALIDATION_BLOCKED_BY_BODY_OR_QUESTION_STATUS_REF: Final = P7_R54_OP22_BODY_LEAK_BLOCKED_STATUS_REF
P7_R54_OP22_NO_TOUCH_BLOCKED_STATUS_REF: Final = "BLOCKED_BY_NO_TOUCH_VIOLATION"
P7_R54_OP22_FINAL_VALIDATION_BLOCKED_BY_NO_TOUCH_STATUS_REF: Final = P7_R54_OP22_NO_TOUCH_BLOCKED_STATUS_REF
P7_R54_OP22_ALLOWED_FINAL_VALIDATION_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_OP22_FINAL_VALIDATION_READY_STATUS_REF,
    P7_R54_OP22_FINAL_VALIDATION_BLOCKED_STATUS_REF,
    P7_R54_OP22_BODY_LEAK_BLOCKED_STATUS_REF,
    P7_R54_OP22_NO_TOUCH_BLOCKED_STATUS_REF,
)
P7_R54_OP22_FINAL_VALIDATION_REF: Final = "R54_OP22_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_20260625"
P7_R54_OP22_READY_DECISION_REF: Final = "R54_OPERATION_FINAL_BODYFREE_VALIDATION_READY"
P7_R54_OP22_BLOCKED_DECISION_REF: Final = "R54_OPERATION_FINAL_BODYFREE_VALIDATION_BLOCKED"
P7_R54_OP22_READY_REASON_REF: Final = "r54_op22_final_validation_ready_bodyfree"
P7_R54_OP22_INPUT_BLOCKED_REASON_REF: Final = "r54_op22_blocked_until_op21_p8_material_candidate_handoff_ready"
P7_R54_OP22_BODY_LEAK_BLOCKED_REASON_REF: Final = "r54_op22_body_leak_or_question_text_detected_bodyfree"
P7_R54_OP22_BODY_OR_QUESTION_BLOCKED_REASON_REF: Final = P7_R54_OP22_BODY_LEAK_BLOCKED_REASON_REF
P7_R54_OP22_NO_TOUCH_BLOCKED_REASON_REF: Final = "r54_op22_no_touch_contract_mutation_detected_bodyfree"

P7_R54_OP23_R52_REINTAKE_HANDOFF_READY_STATUS_REF: Final = "R54_R52_REINTAKE_HANDOFF_READY"
P7_R54_OP23_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING_STATUS_REF: Final = "R54_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING"
P7_R54_OP23_R52_REINTAKE_BLOCKED_BY_DISPOSAL_STATUS_REF: Final = "R54_R52_REINTAKE_BLOCKED_BY_DISPOSAL"
P7_R54_OP23_R52_REINTAKE_BLOCKED_BY_BODY_LEAK_OR_QUESTION_TEXT_STATUS_REF: Final = "R54_R52_REINTAKE_BLOCKED_BY_BODY_LEAK_OR_QUESTION_TEXT"
P7_R54_OP23_R52_REINTAKE_BLOCKED_BY_NO_TOUCH_VIOLATION_STATUS_REF: Final = "R54_R52_REINTAKE_BLOCKED_BY_NO_TOUCH_VIOLATION"
P7_R54_OP23_R52_REINTAKE_BLOCKED_BY_INCONCLUSIVE_STATUS_REF: Final = "R54_R52_REINTAKE_BLOCKED_BY_INCONCLUSIVE"
P7_R54_OP23_ALLOWED_R52_REINTAKE_HANDOFF_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_OP23_R52_REINTAKE_HANDOFF_READY_STATUS_REF,
    P7_R54_OP23_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING_STATUS_REF,
    P7_R54_OP23_R52_REINTAKE_BLOCKED_BY_DISPOSAL_STATUS_REF,
    P7_R54_OP23_R52_REINTAKE_BLOCKED_BY_BODY_LEAK_OR_QUESTION_TEXT_STATUS_REF,
    P7_R54_OP23_R52_REINTAKE_BLOCKED_BY_NO_TOUCH_VIOLATION_STATUS_REF,
    P7_R54_OP23_R52_REINTAKE_BLOCKED_BY_INCONCLUSIVE_STATUS_REF,
)
P7_R54_OP23_R52_REINTAKE_HANDOFF_STATUS_REFS: Final[tuple[str, ...]] = P7_R54_OP23_ALLOWED_R52_REINTAKE_HANDOFF_STATUS_REFS
P7_R54_OP23_R52_REINTAKE_HANDOFF_REF: Final = "R54_OP23_R52_REINTAKE_HANDOFF_BODYFREE_20260625"
P7_R54_OP23_BODY_FREE_ACTUAL_REVIEW_EVIDENCE_REF: Final = "R54_OP23_BODYFREE_ACTUAL_REVIEW_EVIDENCE_READY_FOR_R52_REINTAKE_20260625"
P7_R54_OP23_R52_REINTAKE_DECISION_REF: Final = "R52_REINTAKE_REQUIRED"
P7_R54_OP23_R52_REINTAKE_REQUIRED_REF: Final = "R52_REINTAKE_REQUIRED_AFTER_R54_ACTUAL_LOCAL_REVIEW_BODYFREE"
P7_R54_OP23_READY_REASON_REF: Final = "r54_op23_r52_reintake_handoff_ready_bodyfree_actual_review_evidence"
P7_R54_OP23_EVIDENCE_MISSING_REASON_REF: Final = "r54_op23_actual_review_evidence_missing_or_incomplete"
P7_R54_OP23_MISSING_REASON_REF: Final = P7_R54_OP23_EVIDENCE_MISSING_REASON_REF
P7_R54_OP23_DISPOSAL_BLOCKED_REASON_REF: Final = "r54_op23_disposal_not_verified"
P7_R54_OP23_BODY_LEAK_BLOCKED_REASON_REF: Final = "r54_op23_blocked_by_body_leak_or_question_text_validation"
P7_R54_OP23_BODY_OR_QUESTION_REASON_REF: Final = P7_R54_OP23_BODY_LEAK_BLOCKED_REASON_REF
P7_R54_OP23_NO_TOUCH_BLOCKED_REASON_REF: Final = "r54_op23_blocked_by_no_touch_validation"
P7_R54_OP23_NO_TOUCH_REASON_REF: Final = P7_R54_OP23_NO_TOUCH_BLOCKED_REASON_REF
P7_R54_OP23_INCONCLUSIVE_REASON_REF: Final = "r54_op23_operation_inconclusive_before_r52_reintake"

P7_R54_OPERATION_FINAL_VALIDATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked", "op21_schema_version",
    "op21_material_ref", "op21_next_required_step", "op21_p8_material_candidate_handoff_status", "op21_p8_start_allowed",
    "op21_question_implementation_started_here", "op21_p8_implementation_spec_finalized_here", "operation_current_refs",
    "operation_current_ref_count", "actual_review_basis_ref", "actual_review_basis_allowed", "operation_current_refs_are_actual_review_basis",
    "required_case_count", "reviewed_case_count", "rating_row_count", "question_observation_row_count", "question_need_observation_rows_aggregated_count", "disposal_verified",
    "p5_decision_candidate_ref", "p5_human_blind_qa_confirmed_candidate", "p5_human_blind_qa_confirmed_final",
    "p6_limited_human_readfeel_candidate", "p6_limited_human_readfeel_start_allowed", "p8_question_design_material_candidate", "p8_material_candidate_row_count",
    "p8_start_allowed", "question_implementation_started_here", "p8_implementation_spec_finalized_here", "release_allowed",
    "validation_evidence_ref", "final_validation_status", "final_validation_ref", "final_validation_decision_ref", "final_validation_reason_refs", "final_validation_issue_refs", "final_validation_issue_count", "final_validation_failure_class_ref",
    "body_leak_violation_refs", "body_leak_violation_count", "question_text_violation_refs", "question_text_violation_count", "no_touch_violation_refs", "no_touch_violation_count",
    "body_leak_or_question_text_violation_detected", "no_touch_violation_detected", "body_full_artifact_export_candidate_detected", "body_full_packet_content_boundary_detected",
    "question_text_boundary_detected", "draft_question_text_boundary_detected", "local_path_boundary_detected", "body_hash_boundary_detected", "contract_mutation_boundary_detected", "api_db_rn_runtime_mutation_detected",
    "no_body_leak_validation_passed", "no_question_text_validation_passed", "no_touch_validation_passed", "final_validation_passed", "r52_reintake_handoff_allowed_next",
    "actual_review_evidence_complete", "human_review_completion_claim_blocked_here", "p6_p8_release_promotion_blocked_here", "execution_blocker_ids", "open_execution_blocker_ids",
    "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract", "r54_operation_no_touch_contract", "body_free_markers", "body_free",
    "raw_body_included", "question_text_included", "draft_question_text_included", "local_path_included", *P7_R54_OPERATION_FALSE_FLAG_REFS,
)

P7_R54_OPERATION_R52_REINTAKE_HANDOFF_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked", "op22_schema_version", "op22_material_ref", "op22_next_required_step", "op22_final_validation_status", "op22_r52_reintake_handoff_allowed_next",
    "operation_current_refs", "operation_current_ref_count", "actual_review_basis_ref", "actual_review_basis_allowed", "operation_current_refs_are_actual_review_basis",
    "required_case_count", "reviewed_case_count", "rating_row_count", "question_observation_row_count", "handoff_status", "handoff_ref", "handoff_reason_refs", "r52_reintake_decision_ref", "r52_reintake_handoff_ready",
    "r52_reintake_handoff_status", "r52_reintake_handoff_ref", "r52_reintake_handoff_reason_refs", "r52_reintake_required_ref",
    "actual_review_evidence_complete", "actual_review_evidence_complete_from_bodyfree_receipts", "r52_bodyfree_actual_review_evidence_complete", "r52_bodyfree_evidence_handoff_ready", "actual_human_review_run_here", "actual_manual_review_run_here",
    "rating_rows_bodyfree_handoff_count", "question_observation_rows_bodyfree_handoff_count", "disposal_verified", "no_body_leak_validation_passed", "no_question_text_validation_passed", "no_touch_validation_passed",
    "p5_decision_candidate", "p5_decision_candidate_ref", "p5_human_blind_qa_confirmed_candidate", "p5_human_blind_qa_confirmed_final", "p6_candidate_only", "p6_limited_human_readfeel_candidate", "p6_limited_human_readfeel_start_allowed",
    "p8_material_candidate_only", "p8_question_design_material_candidate", "p8_material_candidate_row_count", "p8_design_material_candidate_only_not_start", "p8_start_allowed", "question_implementation_started_here", "p8_implementation_spec_finalized_here",
    "question_text_materialized_here", "draft_question_text_materialized_here", "question_trigger_logic_implemented", "question_answer_persistence_implemented", "question_api_implemented", "question_db_schema_implemented", "question_rn_ui_implemented", "question_response_key_implemented", "question_plan_guard_implemented", "question_storage_schema_implemented",
    "question_text_included", "draft_question_text_included", "api_db_rn_response_key_changed_here", "runtime_changed_here", "release_allowed", "p7_complete",
    "body_free_evidence_handoff_materialized_here", "r52_reintake_required", "body_free_actual_review_evidence_ref", "body_free_result_handoff_ref", "handoff_evidence_refs", "handoff_evidence_ref_count", "r52_handoff_preserves_candidate_only_boundaries",
    "r52_handoff_contains_body_full_packet", "r52_handoff_contains_question_text", "r52_handoff_contains_local_path", "r52_handoff_contains_payload_hash", "r52_handoff_contains_reviewer_free_text", "r52_handoff_contains_raw_payload",
    "human_review_completion_claim_blocked_here", "p6_p8_release_promotion_blocked_here", "execution_blocker_ids", "open_execution_blocker_ids", "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract", "r54_operation_no_touch_contract", "body_free_markers", "body_free", "raw_body_included", "local_path_included", *P7_R54_OPERATION_FALSE_FLAG_REFS,
)


def _op22_false_flag_refs() -> tuple[str, ...]:
    return tuple(key for key in P7_R54_OPERATION_FALSE_FLAG_REFS if key not in {"disposal_verified", "p5_human_blind_qa_confirmed_candidate", "p6_limited_human_readfeel_candidate", "p8_question_design_material_candidate"})


def _op23_false_flag_refs() -> tuple[str, ...]:
    return tuple(key for key in P7_R54_OPERATION_FALSE_FLAG_REFS if key not in {"actual_review_evidence_complete", "disposal_verified", "p5_human_blind_qa_confirmed_candidate", "p6_limited_human_readfeel_candidate", "p8_question_design_material_candidate"})


def _clean_op22_refs(values: Sequence[Any] | None) -> list[str]:
    return dedupe_identifiers(values or [], limit=80, max_length=180)


def _mapping_all_false(value: Mapping[str, Any] | None) -> bool:
    return all(child is False for child in safe_mapping(value).values())


def _op22_refs_from_evidence(validation_evidence: Mapping[str, Any] | None, keys: Sequence[str]) -> list[str]:
    data = safe_mapping(validation_evidence)
    return [key for key in keys if data.get(key) is True]


def _op22_prior_refs(op21: Mapping[str, Any]) -> tuple[list[str], list[str], list[str]]:
    prior: list[str] = []
    leak: list[str] = []
    no_touch: list[str] = []
    if op21.get("p8_material_candidate_handoff_status") != P7_R54_OP21_P8_MATERIAL_HANDOFF_READY_STATUS_REF:
        prior.append(P7_R54_OP22_INPUT_BLOCKED_REASON_REF)
    if op21.get("next_required_step") != P7_R54_OP22_STEP_REF:
        prior.append("op21_next_required_step_not_op22")
    if op21.get("open_execution_blocker_ids"):
        prior.append("op21_open_execution_blockers_present")
    if op21.get("body_free") is not True:
        leak.append("op21_material_not_bodyfree")
    if op21.get("question_text_included") is not False or op21.get("draft_question_text_included") is not False:
        leak.append("op21_question_text_or_draft_question_text_included")
    if op21.get("local_path_included") is not False:
        leak.append("op21_local_path_included")
    for key in ("body_full_packet_zip_inclusion_allowed", "reviewer_notes_export_allowed", "body_content_hash_materialized_here", "packet_content_hash_materialized_here"):
        if op21.get(key) is True:
            leak.append(f"{key}_must_remain_false")
    if not _mapping_all_false(op21.get("public_contract")) or not _mapping_all_false(op21.get("r54_operation_no_touch_contract")):
        no_touch.append("no_touch_contract_marker_true")
    for key in ("api_changed", "db_changed", "rn_changed", "runtime_changed", "api_db_rn_response_key_changed_here", "runtime_changed_here", "question_api_implemented", "question_db_schema_implemented", "question_rn_ui_implemented", "question_response_key_implemented", "question_trigger_logic_implemented", "question_answer_persistence_implemented", "question_implementation_started_here", "p8_implementation_spec_finalized_here", "p8_start_allowed", "p6_limited_human_readfeel_start_allowed", "release_allowed", "p7_complete"):
        if op21.get(key) is True:
            no_touch.append(f"{key}_must_remain_false")
    return (dedupe_identifiers(prior, limit=50, max_length=180), dedupe_identifiers(leak, limit=50, max_length=180), dedupe_identifiers(no_touch, limit=50, max_length=180))


def _op22_status_next_reason(prior: Sequence[str], body_refs: Sequence[str], question_refs: Sequence[str], no_touch_refs: Sequence[str]) -> tuple[str, str, str, list[str]]:
    if body_refs or question_refs:
        reasons = dedupe_identifiers([P7_R54_OP22_BODY_LEAK_BLOCKED_REASON_REF, *body_refs, *question_refs], limit=100, max_length=180)
        return (P7_R54_OP22_BODY_LEAK_BLOCKED_STATUS_REF, P7_R54_OP22_BODY_LEAK_BLOCKED_NEXT_REQUIRED_STEP_REF, "body_or_question_text", reasons)
    if no_touch_refs:
        reasons = dedupe_identifiers([P7_R54_OP22_NO_TOUCH_BLOCKED_REASON_REF, *no_touch_refs], limit=100, max_length=180)
        return (P7_R54_OP22_NO_TOUCH_BLOCKED_STATUS_REF, P7_R54_OP22_NO_TOUCH_BLOCKED_NEXT_REQUIRED_STEP_REF, "no_touch", reasons)
    if prior:
        reasons = dedupe_identifiers([P7_R54_OP22_INPUT_BLOCKED_REASON_REF, *prior], limit=100, max_length=180)
        return (P7_R54_OP22_FINAL_VALIDATION_BLOCKED_STATUS_REF, P7_R54_OP22_BLOCKED_NEXT_REQUIRED_STEP_REF, "op21_not_ready", reasons)
    return (P7_R54_OP22_FINAL_VALIDATION_READY_STATUS_REF, P7_R54_OP23_STEP_REF, "none", [P7_R54_OP22_READY_REASON_REF])


def build_p7_r54_op22_final_no_body_leak_no_question_text_no_touch_validation(
    *,
    p8_material_candidate_handoff: Mapping[str, Any] | None = None,
    validation_evidence: Mapping[str, Any] | None = None,
    validation_evidence_ref: Any = "r54_op22_final_validation_bodyfree_evidence_ref",
    body_leak_violation_refs: Sequence[Any] | None = None,
    question_text_violation_refs: Sequence[Any] | None = None,
    no_touch_violation_refs: Sequence[Any] | None = None,
    material_id: Any = "p7_r54_operation_final_no_body_leak_no_question_text_no_touch_validation",
) -> dict[str, Any]:
    op21 = safe_mapping(p8_material_candidate_handoff) if p8_material_candidate_handoff is not None else build_p7_r54_op21_p8_material_candidate_handoff()
    assert_p7_r54_op21_p8_material_candidate_handoff_contract(op21)
    prior_refs, prior_leak_refs, prior_no_touch_refs = _op22_prior_refs(op21)
    body_refs = _clean_op22_refs([*prior_leak_refs, *_op22_refs_from_evidence(validation_evidence, ("body_full_packet_artifact_detected", "body_full_packet_content_detected", "reviewer_notes_artifact_detected", "raw_payload_artifact_detected")), *list(body_leak_violation_refs or [])])
    question_refs = _clean_op22_refs([*_op22_refs_from_evidence(validation_evidence, ("question_text_artifact_detected", "draft_question_text_artifact_detected", "p8_question_text_artifact_detected")), *list(question_text_violation_refs or [])])
    no_touch_refs = _clean_op22_refs([*prior_no_touch_refs, *_op22_refs_from_evidence(validation_evidence, ("api_changed_detected", "db_changed_detected", "rn_changed_detected", "runtime_changed_detected", "public_response_key_changed_detected")), *list(no_touch_violation_refs or [])])
    status, next_step, failure_class, reason_refs = _op22_status_next_reason(prior_refs, body_refs, question_refs, no_touch_refs)
    ready = status == P7_R54_OP22_FINAL_VALIDATION_READY_STATUS_REF
    blockers = [] if ready else dedupe_identifiers(reason_refs, limit=120, max_length=180)
    material = {
        "schema_version": P7_R54_OPERATION_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION,
        "phase": P7_PHASE, "step": P7_R54_OPERATION_REENTRY_STEP, "scope": P7_R54_OPERATION_REENTRY_SCOPE,
        "policy_kind": P7_R54_OPERATION_REENTRY_POLICY_KIND, "policy_section": P7_R54_OP22_STEP_REF, "operation_step_ref": P7_R54_OP22_STEP_REF,
        "current_phase": "P7", "material_id": clean_identifier(material_id, default="p7_r54_operation_final_no_body_leak_no_question_text_no_touch_validation", max_length=220),
        "review_session_id": _safe_review_session_id(op21.get("review_session_id")), "source_mode": P7_SOURCE_MODE, "git_connection_required": False, "git_checked": False,
        "op21_schema_version": P7_R54_OPERATION_P8_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        "op21_material_ref": clean_identifier(op21.get("material_id"), default="p7_r54_operation_p8_material_candidate_handoff", max_length=220),
        "op21_next_required_step": clean_identifier(op21.get("next_required_step"), default="", max_length=180),
        "op21_p8_material_candidate_handoff_status": clean_identifier(op21.get("p8_material_candidate_handoff_status"), default=P7_R54_OP21_P8_MATERIAL_HANDOFF_BLOCKED_STATUS_REF, max_length=180),
        "op21_p8_start_allowed": op21.get("p8_start_allowed") is True,
        "op21_question_implementation_started_here": op21.get("question_implementation_started_here") is True,
        "op21_p8_implementation_spec_finalized_here": op21.get("p8_implementation_spec_finalized_here") is True,
        "operation_current_refs": dict(P7_R54_OPERATION_CURRENT_REFS), "operation_current_ref_count": len(P7_R54_OPERATION_CURRENT_REFS),
        "actual_review_basis_ref": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_REF, "actual_review_basis_allowed": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_ALLOWED_REF, "operation_current_refs_are_actual_review_basis": True,
        **_false_flags(),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "reviewed_case_count": int(op21.get("reviewed_case_count") or 0) if ready else 0,
        "rating_row_count": int(op21.get("rating_row_count") or 0) if ready else 0,
        "question_observation_row_count": int(op21.get("question_observation_row_count") or 0) if ready else 0,
        "question_need_observation_rows_aggregated_count": int(op21.get("question_need_observation_rows_aggregated_count") or 0) if ready else 0,
        "disposal_verified": op21.get("disposal_verified") is True and ready,
        "p5_decision_candidate_ref": clean_identifier(op21.get("p5_decision_candidate_ref"), default=P7_R54_OP19_P5_CONFIRMED_CANDIDATE_REF if ready else P7_R54_OP19_INCONCLUSIVE_REF, max_length=180),
        "p5_human_blind_qa_confirmed_candidate": op21.get("p5_human_blind_qa_confirmed_candidate") is True and ready,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_candidate": op21.get("p6_limited_human_readfeel_candidate") is True and ready,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_question_design_material_candidate": op21.get("p8_question_design_material_candidate") is True and ready,
        "p8_material_candidate_row_count": int(op21.get("p8_material_candidate_row_count") or 0) if ready else 0,
        "p8_start_allowed": False, "question_implementation_started_here": False, "p8_implementation_spec_finalized_here": False, "release_allowed": False,
        "validation_evidence_ref": clean_identifier(validation_evidence_ref, default="r54_op22_final_validation_bodyfree_evidence_ref", max_length=220),
        "final_validation_status": status, "final_validation_ref": P7_R54_OP22_FINAL_VALIDATION_REF if ready else "final_validation_not_ready_bodyfree",
        "final_validation_decision_ref": P7_R54_OP22_READY_DECISION_REF if ready else P7_R54_OP22_BLOCKED_DECISION_REF,
        "final_validation_reason_refs": reason_refs, "final_validation_issue_refs": blockers, "final_validation_issue_count": len(blockers), "final_validation_failure_class_ref": failure_class,
        "body_leak_violation_refs": body_refs, "body_leak_violation_count": len(body_refs),
        "question_text_violation_refs": question_refs, "question_text_violation_count": len(question_refs),
        "no_touch_violation_refs": no_touch_refs, "no_touch_violation_count": len(no_touch_refs),
        "body_leak_or_question_text_violation_detected": bool(body_refs or question_refs), "no_touch_violation_detected": bool(no_touch_refs),
        "body_full_artifact_export_candidate_detected": bool(body_refs), "body_full_packet_content_boundary_detected": bool(body_refs),
        "question_text_boundary_detected": bool(question_refs), "draft_question_text_boundary_detected": bool(question_refs),
        "local_path_boundary_detected": any("local_path" in ref for ref in body_refs), "body_hash_boundary_detected": any("hash" in ref for ref in body_refs),
        "contract_mutation_boundary_detected": bool(no_touch_refs), "api_db_rn_runtime_mutation_detected": any(any(token in ref for token in ("api", "db", "rn", "runtime")) for ref in no_touch_refs),
        "no_body_leak_validation_passed": (not prior_refs and not body_refs and not question_refs), "no_question_text_validation_passed": (not prior_refs and not body_refs and not question_refs), "no_touch_validation_passed": (not prior_refs and not no_touch_refs), "final_validation_passed": ready, "r52_reintake_handoff_allowed_next": ready,
        "actual_review_evidence_complete": False, "human_review_completion_claim_blocked_here": True, "p6_p8_release_promotion_blocked_here": True,
        "execution_blocker_ids": blockers, "open_execution_blocker_ids": blockers,
        "implemented_steps": list(P7_R54_OP22_IMPLEMENTED_STEPS if ready else tuple(op21.get("implemented_steps") or ())),
        "not_yet_implemented_steps": list(P7_R54_OP22_NOT_YET_IMPLEMENTED_STEPS if ready else tuple(op21.get("not_yet_implemented_steps") or ())),
        "first_next_work_ref": P7_R54_OP_NEXT_WORK_AFTER_OP22_REF if ready else P7_R54_OP_NEXT_WORK_AFTER_OP21_REF,
        "next_required_step": next_step,
        "public_contract": public_contract_flags(), "r54_operation_no_touch_contract": _operation_no_touch_contract(), "body_free_markers": _body_free_markers(),
        "body_free": True, "raw_body_included": False, "question_text_included": False, "draft_question_text_included": False, "local_path_included": False,
    }
    assert_p7_r54_op22_final_no_body_leak_no_question_text_no_touch_validation_contract(material)
    return material


def assert_p7_r54_op22_final_no_body_leak_no_question_text_no_touch_validation_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_OPERATION_FINAL_VALIDATION_REQUIRED_FIELD_REFS, source="p7_r54_op22_final_validation")
    _assert_common_operation_contract(data, schema_version=P7_R54_OPERATION_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION, policy_section=P7_R54_OP22_STEP_REF, operation_step_ref=P7_R54_OP22_STEP_REF, source="p7_r54_op22_final_validation", false_flag_refs=_op22_false_flag_refs())
    _assert_operation_current_refs(data, source="p7_r54_op22_final_validation")
    if data.get("final_validation_status") not in P7_R54_OP22_ALLOWED_FINAL_VALIDATION_STATUS_REFS:
        raise ValueError("R54 OP22 status outside allowed refs")
    ready = data.get("final_validation_status") == P7_R54_OP22_FINAL_VALIDATION_READY_STATUS_REF
    if data.get("final_validation_passed") is not ready or data.get("r52_reintake_handoff_allowed_next") is not ready:
        raise ValueError("R54 OP22 ready flags must match status")
    if data.get("actual_review_evidence_complete") is not False or data.get("p5_human_blind_qa_confirmed_final") is not False:
        raise ValueError("R54 OP22 must not complete evidence or finalize P5")
    for false_key in ("p6_limited_human_readfeel_start_allowed", "p8_start_allowed", "release_allowed", "question_implementation_started_here", "p8_implementation_spec_finalized_here", "raw_body_included", "question_text_included", "draft_question_text_included", "local_path_included"):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 OP22 must keep {false_key}=False")
    if ready:
        if data.get("final_validation_ref") != P7_R54_OP22_FINAL_VALIDATION_REF or data.get("final_validation_reason_refs") != [P7_R54_OP22_READY_REASON_REF]:
            raise ValueError("R54 OP22 ready validation refs changed")
        for count_key in ("reviewed_case_count", "rating_row_count", "question_observation_row_count"):
            if data.get(count_key) != P7_R51_REQUIRED_CASE_COUNT:
                raise ValueError(f"R54 OP22 ready must preserve 24 {count_key}")
        if data.get("disposal_verified") is not True or data.get("p5_human_blind_qa_confirmed_candidate") is not True or data.get("p6_limited_human_readfeel_candidate") is not True:
            raise ValueError("R54 OP22 ready must preserve actual review candidate evidence")
        if data.get("open_execution_blocker_ids"):
            raise ValueError("R54 OP22 ready must not carry blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_OP22_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_OP22_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP22 step lists changed")
        if data.get("next_required_step") != P7_R54_OP23_STEP_REF:
            raise ValueError("R54 OP22 ready must point to OP23")
    else:
        if not data.get("open_execution_blocker_ids"):
            raise ValueError("R54 OP22 blocked must carry blockers")
        if data.get("next_required_step") not in {P7_R54_OP22_BLOCKED_NEXT_REQUIRED_STEP_REF, P7_R54_OP22_BODY_LEAK_BLOCKED_NEXT_REQUIRED_STEP_REF, P7_R54_OP22_NO_TOUCH_BLOCKED_NEXT_REQUIRED_STEP_REF}:
            raise ValueError("R54 OP22 blocked next step changed")
    return True


def _op23_status_next_reason(op22: Mapping[str, Any]) -> tuple[str, str, list[str]]:
    if op22.get("final_validation_status") == P7_R54_OP22_BODY_LEAK_BLOCKED_STATUS_REF or op22.get("body_leak_or_question_text_violation_detected") is True:
        return (P7_R54_OP23_R52_REINTAKE_BLOCKED_BY_BODY_LEAK_OR_QUESTION_TEXT_STATUS_REF, P7_R54_OP23_BODY_LEAK_BLOCKED_NEXT_REQUIRED_STEP_REF, [P7_R54_OP23_BODY_LEAK_BLOCKED_REASON_REF])
    if op22.get("final_validation_status") == P7_R54_OP22_NO_TOUCH_BLOCKED_STATUS_REF or op22.get("no_touch_violation_detected") is True:
        return (P7_R54_OP23_R52_REINTAKE_BLOCKED_BY_NO_TOUCH_VIOLATION_STATUS_REF, P7_R54_OP23_NO_TOUCH_BLOCKED_NEXT_REQUIRED_STEP_REF, [P7_R54_OP23_NO_TOUCH_BLOCKED_REASON_REF])
    if op22.get("final_validation_status") != P7_R54_OP22_FINAL_VALIDATION_READY_STATUS_REF or op22.get("r52_reintake_handoff_allowed_next") is not True:
        return (P7_R54_OP23_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING_STATUS_REF, P7_R54_OP23_BLOCKED_NEXT_REQUIRED_STEP_REF, [P7_R54_OP23_EVIDENCE_MISSING_REASON_REF])
    if op22.get("disposal_verified") is not True:
        return (P7_R54_OP23_R52_REINTAKE_BLOCKED_BY_DISPOSAL_STATUS_REF, P7_R54_OP23_DISPOSAL_BLOCKED_NEXT_REQUIRED_STEP_REF, [P7_R54_OP23_DISPOSAL_BLOCKED_REASON_REF])
    if op22.get("reviewed_case_count") != P7_R51_REQUIRED_CASE_COUNT or op22.get("rating_row_count") != P7_R51_REQUIRED_CASE_COUNT or op22.get("question_observation_row_count") != P7_R51_REQUIRED_CASE_COUNT:
        return (P7_R54_OP23_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING_STATUS_REF, P7_R54_OP23_BLOCKED_NEXT_REQUIRED_STEP_REF, [P7_R54_OP23_EVIDENCE_MISSING_REASON_REF])
    if op22.get("p5_human_blind_qa_confirmed_candidate") is not True:
        return (P7_R54_OP23_R52_REINTAKE_BLOCKED_BY_INCONCLUSIVE_STATUS_REF, P7_R54_OP23_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF, [P7_R54_OP23_INCONCLUSIVE_REASON_REF])
    return (P7_R54_OP23_R52_REINTAKE_HANDOFF_READY_STATUS_REF, P7_R54_OP24_STEP_REF, [P7_R54_OP23_READY_REASON_REF])


def build_p7_r54_op23_r52_reintake_handoff(*, final_validation: Mapping[str, Any] | None = None, material_id: Any = "p7_r54_operation_r52_reintake_handoff") -> dict[str, Any]:
    op22 = safe_mapping(final_validation) if final_validation is not None else build_p7_r54_op22_final_no_body_leak_no_question_text_no_touch_validation()
    assert_p7_r54_op22_final_no_body_leak_no_question_text_no_touch_validation_contract(op22)
    status, next_step, reason_refs = _op23_status_next_reason(op22)
    ready = status == P7_R54_OP23_R52_REINTAKE_HANDOFF_READY_STATUS_REF
    blockers = [] if ready else dedupe_identifiers([*reason_refs, *(op22.get("open_execution_blocker_ids") or [])], limit=120, max_length=180)
    p5_candidate_ref = clean_identifier(op22.get("p5_decision_candidate_ref"), default=P7_R54_OP19_INCONCLUSIVE_REF, max_length=180)
    handoff_evidence_refs = (
        "op12_rating_rows_normalized_bodyfree", "op14_question_need_observation_rows_normalized_bodyfree", "op17_disposal_receipt_verified_bodyfree", "op18_post_review_summary_ready_bodyfree", "op19_p5_decision_candidate_separated_bodyfree", "op20_p6_candidate_handoff_candidate_only_bodyfree", "op21_p8_material_candidate_handoff_candidate_only_bodyfree", "op22_final_validation_bodyfree",
    )
    material = {
        "schema_version": P7_R54_OPERATION_R52_REINTAKE_HANDOFF_SCHEMA_VERSION,
        "phase": P7_PHASE, "step": P7_R54_OPERATION_REENTRY_STEP, "scope": P7_R54_OPERATION_REENTRY_SCOPE,
        "policy_kind": P7_R54_OPERATION_REENTRY_POLICY_KIND, "policy_section": P7_R54_OP23_STEP_REF, "operation_step_ref": P7_R54_OP23_STEP_REF,
        "current_phase": "P7", "material_id": clean_identifier(material_id, default="p7_r54_operation_r52_reintake_handoff", max_length=220),
        "review_session_id": _safe_review_session_id(op22.get("review_session_id")), "source_mode": P7_SOURCE_MODE, "git_connection_required": False, "git_checked": False,
        "op22_schema_version": P7_R54_OPERATION_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION,
        "op22_material_ref": clean_identifier(op22.get("material_id"), default="p7_r54_operation_final_validation", max_length=220),
        "op22_next_required_step": clean_identifier(op22.get("next_required_step"), default="", max_length=180),
        "op22_final_validation_status": clean_identifier(op22.get("final_validation_status"), default=P7_R54_OP22_FINAL_VALIDATION_BLOCKED_STATUS_REF, max_length=180),
        "op22_r52_reintake_handoff_allowed_next": op22.get("r52_reintake_handoff_allowed_next") is True,
        "operation_current_refs": dict(P7_R54_OPERATION_CURRENT_REFS), "operation_current_ref_count": len(P7_R54_OPERATION_CURRENT_REFS),
        "actual_review_basis_ref": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_REF, "actual_review_basis_allowed": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_ALLOWED_REF, "operation_current_refs_are_actual_review_basis": True,
        **_false_flags(),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "reviewed_case_count": int(op22.get("reviewed_case_count") or 0) if ready else 0,
        "rating_row_count": int(op22.get("rating_row_count") or 0) if ready else 0,
        "question_observation_row_count": int(op22.get("question_observation_row_count") or 0) if ready else 0,
        "handoff_status": status, "handoff_ref": P7_R54_OP23_R52_REINTAKE_HANDOFF_REF if ready else "r52_reintake_handoff_not_ready_bodyfree", "handoff_reason_refs": reason_refs if ready else blockers,
        "r52_reintake_decision_ref": P7_R54_OP23_R52_REINTAKE_DECISION_REF if ready else "R52_REINTAKE_HELD", "r52_reintake_handoff_ready": ready,
        "r52_reintake_handoff_status": status, "r52_reintake_handoff_ref": P7_R54_OP23_R52_REINTAKE_HANDOFF_REF if ready else "r52_reintake_handoff_not_ready_bodyfree", "r52_reintake_handoff_reason_refs": reason_refs if ready else blockers,
        "r52_reintake_required_ref": P7_R54_OP23_R52_REINTAKE_REQUIRED_REF if ready else "R52_REINTAKE_HELD",
        "actual_review_evidence_complete": ready, "actual_review_evidence_complete_from_bodyfree_receipts": ready, "r52_bodyfree_actual_review_evidence_complete": ready, "r52_bodyfree_evidence_handoff_ready": ready,
        "actual_human_review_run_here": False, "actual_manual_review_run_here": False,
        "rating_rows_bodyfree_handoff_count": P7_R51_REQUIRED_CASE_COUNT if ready else 0,
        "question_observation_rows_bodyfree_handoff_count": P7_R51_REQUIRED_CASE_COUNT if ready else 0,
        "disposal_verified": op22.get("disposal_verified") is True and ready,
        "no_body_leak_validation_passed": op22.get("no_body_leak_validation_passed") is True and ready,
        "no_question_text_validation_passed": op22.get("no_question_text_validation_passed") is True and ready,
        "no_touch_validation_passed": op22.get("no_touch_validation_passed") is True and ready,
        "p5_decision_candidate": p5_candidate_ref if ready else P7_R54_OP19_INCONCLUSIVE_REF, "p5_decision_candidate_ref": p5_candidate_ref if ready else P7_R54_OP19_INCONCLUSIVE_REF,
        "p5_human_blind_qa_confirmed_candidate": op22.get("p5_human_blind_qa_confirmed_candidate") is True and ready,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_candidate_only": op22.get("p6_limited_human_readfeel_candidate") is True and ready,
        "p6_limited_human_readfeel_candidate": op22.get("p6_limited_human_readfeel_candidate") is True and ready,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_material_candidate_only": op22.get("p8_question_design_material_candidate") is True and ready,
        "p8_question_design_material_candidate": op22.get("p8_question_design_material_candidate") is True and ready,
        "p8_material_candidate_row_count": int(op22.get("p8_material_candidate_row_count") or 0) if ready else 0,
        "p8_design_material_candidate_only_not_start": True,
        "p8_start_allowed": False, "question_implementation_started_here": False, "p8_implementation_spec_finalized_here": False,
        "question_text_materialized_here": False, "draft_question_text_materialized_here": False, "question_trigger_logic_implemented": False, "question_answer_persistence_implemented": False,
        "question_api_implemented": False, "question_db_schema_implemented": False, "question_rn_ui_implemented": False, "question_response_key_implemented": False, "question_plan_guard_implemented": False, "question_storage_schema_implemented": False,
        "question_text_included": False, "draft_question_text_included": False, "api_db_rn_response_key_changed_here": False, "runtime_changed_here": False, "release_allowed": False, "p7_complete": False,
        "body_free_evidence_handoff_materialized_here": ready, "r52_reintake_required": ready,
        "body_free_actual_review_evidence_ref": P7_R54_OP23_BODY_FREE_ACTUAL_REVIEW_EVIDENCE_REF if ready else "bodyfree_actual_review_evidence_not_ready",
        "body_free_result_handoff_ref": P7_R54_OP23_R52_REINTAKE_HANDOFF_REF if ready else "bodyfree_result_handoff_not_ready",
        "handoff_evidence_refs": list(handoff_evidence_refs) if ready else [],
        "handoff_evidence_ref_count": len(handoff_evidence_refs) if ready else 0,
        "r52_handoff_preserves_candidate_only_boundaries": True,
        "r52_handoff_contains_body_full_packet": False, "r52_handoff_contains_question_text": False, "r52_handoff_contains_local_path": False, "r52_handoff_contains_payload_hash": False, "r52_handoff_contains_reviewer_free_text": False, "r52_handoff_contains_raw_payload": False,
        "human_review_completion_claim_blocked_here": True, "p6_p8_release_promotion_blocked_here": True,
        "execution_blocker_ids": blockers, "open_execution_blocker_ids": blockers,
        "implemented_steps": list(P7_R54_OP23_IMPLEMENTED_STEPS if ready else tuple(op22.get("implemented_steps") or ())),
        "not_yet_implemented_steps": list(P7_R54_OP23_NOT_YET_IMPLEMENTED_STEPS if ready else tuple(op22.get("not_yet_implemented_steps") or ())),
        "first_next_work_ref": P7_R54_OP_NEXT_WORK_AFTER_OP23_REF if ready else P7_R54_OP_NEXT_WORK_AFTER_OP22_REF,
        "next_required_step": next_step,
        "public_contract": public_contract_flags(), "r54_operation_no_touch_contract": _operation_no_touch_contract(), "body_free_markers": _body_free_markers(),
        "body_free": True, "raw_body_included": False, "local_path_included": False,
    }
    assert_p7_r54_op23_r52_reintake_handoff_contract(material)
    return material


def assert_p7_r54_op23_r52_reintake_handoff_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_OPERATION_R52_REINTAKE_HANDOFF_REQUIRED_FIELD_REFS, source="p7_r54_op23_r52_reintake_handoff")
    _assert_common_operation_contract(data, schema_version=P7_R54_OPERATION_R52_REINTAKE_HANDOFF_SCHEMA_VERSION, policy_section=P7_R54_OP23_STEP_REF, operation_step_ref=P7_R54_OP23_STEP_REF, source="p7_r54_op23_r52_reintake_handoff", false_flag_refs=_op23_false_flag_refs())
    _assert_operation_current_refs(data, source="p7_r54_op23_r52_reintake_handoff")
    if data.get("handoff_status") != data.get("r52_reintake_handoff_status"):
        raise ValueError("R54 OP23 handoff status aliases must match")
    ready = data.get("handoff_status") == P7_R54_OP23_R52_REINTAKE_HANDOFF_READY_STATUS_REF
    if data.get("handoff_status") not in P7_R54_OP23_ALLOWED_R52_REINTAKE_HANDOFF_STATUS_REFS:
        raise ValueError("R54 OP23 status outside allowed refs")
    if data.get("actual_review_evidence_complete") is not ready or data.get("r52_reintake_handoff_ready") is not ready:
        raise ValueError("R54 OP23 readiness flags must match status")
    for false_key in ("actual_human_review_run_here", "actual_manual_review_run_here", "p5_human_blind_qa_confirmed_final", "p6_limited_human_readfeel_start_allowed", "p8_start_allowed", "release_allowed", "p7_complete", "question_implementation_started_here", "p8_implementation_spec_finalized_here", "question_text_materialized_here", "draft_question_text_materialized_here", "question_text_included", "draft_question_text_included", "raw_body_included", "local_path_included"):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 OP23 must keep {false_key}=False")
    for false_key in ("r52_handoff_contains_body_full_packet", "r52_handoff_contains_question_text", "r52_handoff_contains_local_path", "r52_handoff_contains_payload_hash", "r52_handoff_contains_reviewer_free_text", "r52_handoff_contains_raw_payload"):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 OP23 must keep {false_key}=False")
    if ready:
        if data.get("handoff_ref") != P7_R54_OP23_R52_REINTAKE_HANDOFF_REF or data.get("r52_reintake_handoff_ref") != P7_R54_OP23_R52_REINTAKE_HANDOFF_REF:
            raise ValueError("R54 OP23 ready handoff ref changed")
        if data.get("handoff_reason_refs") != [P7_R54_OP23_READY_REASON_REF]:
            raise ValueError("R54 OP23 ready reason refs changed")
        for count_key in ("reviewed_case_count", "rating_row_count", "question_observation_row_count", "rating_rows_bodyfree_handoff_count", "question_observation_rows_bodyfree_handoff_count"):
            if data.get(count_key) != P7_R51_REQUIRED_CASE_COUNT:
                raise ValueError(f"R54 OP23 ready must preserve 24 {count_key}")
        if data.get("p5_decision_candidate") != P7_R54_OP19_P5_CONFIRMED_CANDIDATE_REF or data.get("p5_human_blind_qa_confirmed_candidate") is not True:
            raise ValueError("R54 OP23 ready must carry P5 confirmed candidate")
        if data.get("body_free_evidence_handoff_materialized_here") is not True or data.get("r52_reintake_required") is not True:
            raise ValueError("R54 OP23 ready must materialize body-free R52 evidence")
        if data.get("open_execution_blocker_ids"):
            raise ValueError("R54 OP23 ready must not carry blockers")
        if data.get("next_required_step") != P7_R54_OP24_STEP_REF:
            raise ValueError("R54 OP23 ready must point to OP24")
    else:
        if data.get("body_free_evidence_handoff_materialized_here") is not False or data.get("r52_reintake_required") is not False:
            raise ValueError("R54 OP23 blocked must not materialize evidence")
        if not data.get("open_execution_blocker_ids"):
            raise ValueError("R54 OP23 blocked must carry blockers")
        if data.get("next_required_step") not in {P7_R54_OP23_BLOCKED_NEXT_REQUIRED_STEP_REF, P7_R54_OP23_DISPOSAL_BLOCKED_NEXT_REQUIRED_STEP_REF, P7_R54_OP23_BODY_LEAK_BLOCKED_NEXT_REQUIRED_STEP_REF, P7_R54_OP23_NO_TOUCH_BLOCKED_NEXT_REQUIRED_STEP_REF, P7_R54_OP23_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF}:
            raise ValueError("R54 OP23 blocked next step changed")
    return True


# OP22/OP23 detailed-design wording aliases.
build_p7_r54_operation_final_no_body_leak_no_question_text_no_touch_validation = build_p7_r54_op22_final_no_body_leak_no_question_text_no_touch_validation
assert_p7_r54_operation_final_no_body_leak_no_question_text_no_touch_validation_contract = assert_p7_r54_op22_final_no_body_leak_no_question_text_no_touch_validation_contract
build_p7_r54_operation_r52_reintake_handoff = build_p7_r54_op23_r52_reintake_handoff
assert_p7_r54_operation_r52_reintake_handoff_contract = assert_p7_r54_op23_r52_reintake_handoff_contract
build_p7_r54_operation_final_no_body_leak_no_question_text_no_touch_validation_bodyfree = build_p7_r54_operation_final_no_body_leak_no_question_text_no_touch_validation
assert_p7_r54_operation_final_no_body_leak_no_question_text_no_touch_validation_bodyfree_contract = assert_p7_r54_operation_final_no_body_leak_no_question_text_no_touch_validation_contract
build_p7_r54_operation_r52_reintake_handoff_bodyfree = build_p7_r54_operation_r52_reintake_handoff
assert_p7_r54_operation_r52_reintake_handoff_bodyfree_contract = assert_p7_r54_operation_r52_reintake_handoff_contract

__all__ = tuple(__all__) + (
    "P7_R54_OPERATION_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION", "P7_R54_OPERATION_R52_REINTAKE_HANDOFF_SCHEMA_VERSION",
    "P7_R54_OP23_STEP_REF", "P7_R54_OP24_STEP_REF", "P7_R54_OP22_BLOCKED_NEXT_REQUIRED_STEP_REF", "P7_R54_OP22_BODY_LEAK_BLOCKED_NEXT_REQUIRED_STEP_REF", "P7_R54_OP22_NO_TOUCH_BLOCKED_NEXT_REQUIRED_STEP_REF", "P7_R54_OP23_BLOCKED_NEXT_REQUIRED_STEP_REF", "P7_R54_OP23_DISPOSAL_BLOCKED_NEXT_REQUIRED_STEP_REF", "P7_R54_OP23_BODY_LEAK_BLOCKED_NEXT_REQUIRED_STEP_REF", "P7_R54_OP23_NO_TOUCH_BLOCKED_NEXT_REQUIRED_STEP_REF", "P7_R54_OP23_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF",
    "P7_R54_OP_NEXT_WORK_AFTER_OP22_REF", "P7_R54_OP_NEXT_WORK_AFTER_OP23_REF", "P7_R54_OP22_IMPLEMENTED_STEPS", "P7_R54_OP22_NOT_YET_IMPLEMENTED_STEPS", "P7_R54_OP23_IMPLEMENTED_STEPS", "P7_R54_OP23_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_OP22_FINAL_VALIDATION_READY_STATUS_REF", "P7_R54_OP22_FINAL_VALIDATION_BLOCKED_STATUS_REF", "P7_R54_OP22_FINAL_VALIDATION_BLOCKED_BY_OP21_STATUS_REF", "P7_R54_OP22_BODY_LEAK_BLOCKED_STATUS_REF", "P7_R54_OP22_FINAL_VALIDATION_BLOCKED_BY_BODY_OR_QUESTION_STATUS_REF", "P7_R54_OP22_NO_TOUCH_BLOCKED_STATUS_REF", "P7_R54_OP22_FINAL_VALIDATION_BLOCKED_BY_NO_TOUCH_STATUS_REF", "P7_R54_OP22_ALLOWED_FINAL_VALIDATION_STATUS_REFS", "P7_R54_OP22_FINAL_VALIDATION_REF", "P7_R54_OP22_READY_DECISION_REF", "P7_R54_OP22_BLOCKED_DECISION_REF",
    "P7_R54_OP23_R52_REINTAKE_HANDOFF_READY_STATUS_REF", "P7_R54_OP23_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING_STATUS_REF", "P7_R54_OP23_R52_REINTAKE_BLOCKED_BY_DISPOSAL_STATUS_REF", "P7_R54_OP23_R52_REINTAKE_BLOCKED_BY_BODY_LEAK_OR_QUESTION_TEXT_STATUS_REF", "P7_R54_OP23_R52_REINTAKE_BLOCKED_BY_NO_TOUCH_VIOLATION_STATUS_REF", "P7_R54_OP23_R52_REINTAKE_BLOCKED_BY_INCONCLUSIVE_STATUS_REF", "P7_R54_OP23_ALLOWED_R52_REINTAKE_HANDOFF_STATUS_REFS", "P7_R54_OP23_R52_REINTAKE_HANDOFF_STATUS_REFS", "P7_R54_OP23_R52_REINTAKE_HANDOFF_REF", "P7_R54_OP23_BODY_FREE_ACTUAL_REVIEW_EVIDENCE_REF", "P7_R54_OP22_READY_DECISION_REF", "P7_R54_OP22_BLOCKED_DECISION_REF", "P7_R54_OP23_R52_REINTAKE_DECISION_REF", "P7_R54_OP23_R52_REINTAKE_REQUIRED_REF",
    "P7_R54_OPERATION_FINAL_VALIDATION_REQUIRED_FIELD_REFS", "P7_R54_OPERATION_R52_REINTAKE_HANDOFF_REQUIRED_FIELD_REFS",
    "build_p7_r54_op22_final_no_body_leak_no_question_text_no_touch_validation", "assert_p7_r54_op22_final_no_body_leak_no_question_text_no_touch_validation_contract", "build_p7_r54_op23_r52_reintake_handoff", "assert_p7_r54_op23_r52_reintake_handoff_contract",
    "build_p7_r54_operation_final_no_body_leak_no_question_text_no_touch_validation", "assert_p7_r54_operation_final_no_body_leak_no_question_text_no_touch_validation_contract", "build_p7_r54_operation_r52_reintake_handoff", "assert_p7_r54_operation_r52_reintake_handoff_contract", "build_p7_r54_operation_final_no_body_leak_no_question_text_no_touch_validation_bodyfree", "assert_p7_r54_operation_final_no_body_leak_no_question_text_no_touch_validation_bodyfree_contract", "build_p7_r54_operation_r52_reintake_handoff_bodyfree", "assert_p7_r54_operation_r52_reintake_handoff_bodyfree_contract",
)


# ---------------------------------------------------------------------------
# R54-OP-24: validation command matrix / documentation output.
# ---------------------------------------------------------------------------

P7_R54_OPERATION_VALIDATION_COMMAND_MATRIX_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_validation_command_matrix_row.bodyfree.v1"
)
P7_R54_OPERATION_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.operation_validation_command_matrix_documentation_output.bodyfree.v1"
)

P7_R54_OP24_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "validation_command_matrix_documentation_output_repair_before_r52_reintake_consumption"
)
P7_R54_OP_NEXT_WORK_AFTER_OP24_REF: Final = (
    "r52_reintake_consumes_r54_bodyfree_evidence_after_validation_documentation_output"
)

P7_R54_OP24_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_OP23_IMPLEMENTED_STEPS, P7_R54_OP24_STEP_REF)
P7_R54_OP24_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = tuple(
    step for step in P7_R54_OP23_NOT_YET_IMPLEMENTED_STEPS if step != P7_R54_OP24_STEP_REF
)

P7_R54_OP24_DOCUMENTATION_OUTPUT_READY_STATUS_REF: Final = "VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_READY_BODYFREE"
P7_R54_OP24_DOCUMENTATION_OUTPUT_BLOCKED_STATUS_REF: Final = "VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_BLOCKED"
P7_R54_OP24_DOCUMENTATION_OUTPUT_BLOCKED_BY_OP23_STATUS_REF: Final = "VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_BLOCKED_BY_R52_REINTAKE_HANDOFF"
P7_R54_OP24_DOCUMENTATION_OUTPUT_BLOCKED_BY_COMMAND_MATRIX_STATUS_REF: Final = "VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_BLOCKED_BY_COMMAND_MATRIX"
P7_R54_OP24_DOCUMENTATION_OUTPUT_BLOCKED_BY_CLAIM_OVERREACH_STATUS_REF: Final = "VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_BLOCKED_BY_GREEN_CLAIM_OVERREACH"
P7_R54_OP24_ALLOWED_DOCUMENTATION_OUTPUT_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_OP24_DOCUMENTATION_OUTPUT_READY_STATUS_REF,
    P7_R54_OP24_DOCUMENTATION_OUTPUT_BLOCKED_STATUS_REF,
    P7_R54_OP24_DOCUMENTATION_OUTPUT_BLOCKED_BY_OP23_STATUS_REF,
    P7_R54_OP24_DOCUMENTATION_OUTPUT_BLOCKED_BY_COMMAND_MATRIX_STATUS_REF,
    P7_R54_OP24_DOCUMENTATION_OUTPUT_BLOCKED_BY_CLAIM_OVERREACH_STATUS_REF,
)
P7_R54_OP24_DOCUMENTATION_OUTPUT_REF: Final = "R54_OP24_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_BODYFREE_20260625"
P7_R54_OP24_READY_REASON_REF: Final = "r54_op24_validation_command_matrix_documentation_output_ready_bodyfree"
P7_R54_OP24_BLOCKED_BY_OP23_REASON_REF: Final = "r54_op24_blocked_until_r52_reintake_handoff_ready"
P7_R54_OP24_COMMAND_MATRIX_MISSING_REASON_REF: Final = "r54_op24_validation_command_matrix_rows_missing"
P7_R54_OP24_COMMAND_MATRIX_FAILED_REASON_REF: Final = "r54_op24_validation_command_matrix_has_failed_result_refs"
P7_R54_OP24_GREEN_CLAIM_OVERREACH_REASON_REF: Final = "r54_op24_green_claim_scope_overreach_detected_bodyfree"

P7_R54_OP24_COMMAND_RESULT_PASSED_REF: Final = "PASSED"
P7_R54_OP24_COMMAND_RESULT_COLLECTED_ONLY_REF: Final = "COLLECTED_ONLY_NOT_FULL_SUITE_GREEN"
P7_R54_OP24_COMMAND_RESULT_NOT_EXECUTED_REF: Final = "NOT_EXECUTED"
P7_R54_OP24_COMMAND_RESULT_FAILED_REF: Final = "FAILED"
P7_R54_OP24_ALLOWED_COMMAND_RESULT_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_OP24_COMMAND_RESULT_PASSED_REF,
    P7_R54_OP24_COMMAND_RESULT_COLLECTED_ONLY_REF,
    P7_R54_OP24_COMMAND_RESULT_NOT_EXECUTED_REF,
    P7_R54_OP24_COMMAND_RESULT_FAILED_REF,
)
P7_R54_OP24_CLAIM_BOUNDARY_GUARD_REFS: Final[tuple[str, ...]] = (
    "collect_only_not_full_suite_green",
    "rn_contract_not_real_device_modal_verification",
    "r54_helper_green_not_actual_human_review_complete",
    "selected_regression_not_full_backend_suite_green",
    "compileall_not_runtime_product_readfeel",
)
P7_R54_OP24_DEFAULT_NOT_EXECUTED_VALIDATION_REFS: Final[tuple[str, ...]] = (
    "full_backend_suite_not_executed_in_op24",
    "rn_contract_not_executed_in_op24",
    "real_device_modal_not_executed_in_op24",
    "actual_human_review_operation_not_executed_in_op24",
    "local_file_deletion_not_executed_by_helper",
)
P7_R54_OP24_BLOCKED_GREEN_CLAIM_TOKEN_REFS: Final[tuple[str, ...]] = (
    "full_backend_suite_green",
    "real_device_modal_verified",
    "actual_human_review_complete",
    "release_allowed",
    "p8_start_allowed",
    "p6_start_allowed",
)

P7_R54_OPERATION_VALIDATION_COMMAND_MATRIX_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "validation_command_row_ref", "review_session_id", "command_ref", "command_group_ref",
    "command_kind_ref", "result_status_ref", "result_scope_ref", "passed_count", "collected_count",
    "warning_count", "failure_count", "green_claim_allowed", "collection_only_claim_allowed",
    "full_suite_claim_allowed", "real_device_claim_allowed", "actual_human_review_claim_allowed",
    "result_summary_ref", "command_result_body_stored_here", "terminal_output_stored_here",
    "command_string_included", "body_free", "raw_body_included", "question_text_included",
    "draft_question_text_included", "local_path_included",
)
P7_R54_OPERATION_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op23_schema_version", "op23_material_ref", "op23_next_required_step", "op23_handoff_status",
    "op23_r52_reintake_handoff_ready", "op23_actual_review_evidence_complete", "operation_current_refs",
    "operation_current_ref_count", "actual_review_basis_ref", "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis", "required_case_count", "reviewed_case_count",
    "rating_row_count", "question_observation_row_count", "disposal_verified", "actual_review_evidence_complete",
    "body_free_evidence_handoff_materialized_here", "r52_reintake_handoff_ready", "r52_reintake_required",
    "p5_decision_candidate", "p5_human_blind_qa_confirmed_candidate", "p5_human_blind_qa_confirmed_final",
    "p6_limited_human_readfeel_candidate", "p6_limited_human_readfeel_start_allowed",
    "p8_question_design_material_candidate", "p8_start_allowed", "question_implementation_started_here",
    "p8_implementation_spec_finalized_here", "release_allowed", "documentation_output_status",
    "documentation_output_ref", "documentation_output_reason_refs", "documentation_output_issue_refs",
    "documentation_output_issue_count", "documentation_output_materialized_here",
    "validation_command_row_schema_version", "validation_command_row_required_field_refs", "validation_command_rows",
    "validation_command_row_count", "executed_validation_command_refs", "executed_validation_command_count",
    "passed_validation_command_count", "collected_only_validation_command_count", "failed_validation_command_count",
    "not_executed_validation_command_count", "not_executed_validation_refs", "not_executed_validation_ref_count",
    "green_claim_scope_refs", "green_claim_scope_count", "collection_only_scope_refs", "collection_only_scope_count",
    "blocked_green_claim_refs", "blocked_green_claim_count", "claim_boundary_guard_refs", "claim_boundary_guard_count",
    "collect_only_claimed_as_full_suite_green", "rn_contract_claimed_as_real_device_modal_verified",
    "r54_helper_green_claimed_as_actual_human_review_complete", "full_backend_suite_green_claimed",
    "real_device_modal_verified_claimed", "actual_human_review_complete_claimed_by_helper",
    "release_claimed_from_validation_matrix", "command_result_body_stored_here", "terminal_output_stored_here",
    "command_string_included", "human_review_completion_claim_blocked_here", "p6_p8_release_promotion_blocked_here",
    "execution_blocker_ids", "open_execution_blocker_ids", "implemented_steps", "not_yet_implemented_steps",
    "first_next_work_ref", "next_required_step", "public_contract", "r54_operation_no_touch_contract",
    "body_free_markers", "body_free", "raw_body_included", "question_text_included", "draft_question_text_included",
    "local_path_included", *P7_R54_OPERATION_FALSE_FLAG_REFS,
)


def _op24_false_flag_refs() -> tuple[str, ...]:
    return tuple(
        key for key in P7_R54_OPERATION_FALSE_FLAG_REFS
        if key not in {
            "actual_review_evidence_complete",
            "disposal_verified",
            "p5_human_blind_qa_confirmed_candidate",
            "p6_limited_human_readfeel_candidate",
            "p8_question_design_material_candidate",
        }
    )


def _op24_contains_blocked_claim_ref(value: str) -> bool:
    lowered = value.lower()
    return any(token in lowered for token in P7_R54_OP24_BLOCKED_GREEN_CLAIM_TOKEN_REFS)


def build_p7_r54_op24_validation_command_matrix_row(
    *,
    command_ref: Any,
    command_group_ref: Any = "r54_op24_validation",
    command_kind_ref: Any = "pytest_target",
    result_status_ref: Any = P7_R54_OP24_COMMAND_RESULT_PASSED_REF,
    result_scope_ref: Any = "selected_target_only",
    passed_count: Any = 0,
    collected_count: Any = 0,
    warning_count: Any = 0,
    failure_count: Any = 0,
    result_summary_ref: Any = "bodyfree_result_summary_ref",
    review_session_id: Any = None,
) -> dict[str, Any]:
    status = clean_identifier(result_status_ref, default=P7_R54_OP24_COMMAND_RESULT_NOT_EXECUTED_REF, max_length=120)
    if status not in P7_R54_OP24_ALLOWED_COMMAND_RESULT_STATUS_REFS:
        status = P7_R54_OP24_COMMAND_RESULT_FAILED_REF
    scope_ref = clean_identifier(result_scope_ref, default="selected_target_only", max_length=180)
    command_id = clean_identifier(command_ref, default="validation_command_ref_missing", max_length=220)
    row_ref = f"r54_op24_validation_command_row__{command_id}"[:260]
    passed = max(0, int(passed_count or 0))
    collected = max(0, int(collected_count or 0))
    warnings = max(0, int(warning_count or 0))
    failures = max(0, int(failure_count or 0))
    green_claim_allowed = status == P7_R54_OP24_COMMAND_RESULT_PASSED_REF and not _op24_contains_blocked_claim_ref(scope_ref)
    row = {
        "schema_version": P7_R54_OPERATION_VALIDATION_COMMAND_MATRIX_ROW_SCHEMA_VERSION,
        "validation_command_row_ref": row_ref,
        "review_session_id": _safe_review_session_id(review_session_id),
        "command_ref": command_id,
        "command_group_ref": clean_identifier(command_group_ref, default="r54_op24_validation", max_length=180),
        "command_kind_ref": clean_identifier(command_kind_ref, default="pytest_target", max_length=160),
        "result_status_ref": status,
        "result_scope_ref": scope_ref,
        "passed_count": passed,
        "collected_count": collected,
        "warning_count": warnings,
        "failure_count": failures if status == P7_R54_OP24_COMMAND_RESULT_FAILED_REF else 0,
        "green_claim_allowed": green_claim_allowed,
        "collection_only_claim_allowed": status == P7_R54_OP24_COMMAND_RESULT_COLLECTED_ONLY_REF,
        "full_suite_claim_allowed": False,
        "real_device_claim_allowed": False,
        "actual_human_review_claim_allowed": False,
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
    assert_p7_r54_op24_validation_command_matrix_row_contract(row)
    return row


def assert_p7_r54_op24_validation_command_matrix_row_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R54_OPERATION_VALIDATION_COMMAND_MATRIX_ROW_REQUIRED_FIELD_REFS, source="p7_r54_op24_validation_command_matrix_row")
    if data.get("schema_version") != P7_R54_OPERATION_VALIDATION_COMMAND_MATRIX_ROW_SCHEMA_VERSION:
        raise ValueError("R54 OP24 command row schema version changed")
    if data.get("result_status_ref") not in P7_R54_OP24_ALLOWED_COMMAND_RESULT_STATUS_REFS:
        raise ValueError("R54 OP24 command row result status outside allowed refs")
    if data.get("body_free") is not True:
        raise ValueError("R54 OP24 command row must be body-free")
    for false_key in (
        "full_suite_claim_allowed", "real_device_claim_allowed", "actual_human_review_claim_allowed",
        "command_result_body_stored_here", "terminal_output_stored_here", "command_string_included",
        "raw_body_included", "question_text_included", "draft_question_text_included", "local_path_included",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 OP24 command row must keep {false_key}=False")
    if data.get("result_status_ref") == P7_R54_OP24_COMMAND_RESULT_COLLECTED_ONLY_REF:
        if data.get("collection_only_claim_allowed") is not True:
            raise ValueError("R54 OP24 collect-only row must keep collection-only claim explicit")
        if data.get("green_claim_allowed") is not False:
            raise ValueError("R54 OP24 collect-only row must not be claimed as green")
    if data.get("result_status_ref") == P7_R54_OP24_COMMAND_RESULT_FAILED_REF and int(data.get("failure_count") or 0) <= 0:
        raise ValueError("R54 OP24 failed row must carry failure_count")
    if data.get("result_status_ref") == P7_R54_OP24_COMMAND_RESULT_PASSED_REF and int(data.get("failure_count") or 0) != 0:
        raise ValueError("R54 OP24 passed row must not carry failures")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_op24_validation_command_matrix_row")
    return True


def _op24_command_rows_from_input(rows: Sequence[Mapping[str, Any]] | None, *, review_session_id: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for index, raw_row in enumerate(rows or ()):  # type: ignore[arg-type]
        row_data = safe_mapping(raw_row)
        if not row_data:
            continue
        out.append(
            build_p7_r54_op24_validation_command_matrix_row(
                command_ref=row_data.get("command_ref") or row_data.get("validation_command_row_ref") or f"validation_command_{index}",
                command_group_ref=row_data.get("command_group_ref", "r54_op24_validation"),
                command_kind_ref=row_data.get("command_kind_ref", "pytest_target"),
                result_status_ref=row_data.get("result_status_ref", P7_R54_OP24_COMMAND_RESULT_PASSED_REF),
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


def _op24_claim_scope_refs(rows: Sequence[Mapping[str, Any]], supplied: Sequence[Any] | None) -> tuple[list[str], list[str], list[str]]:
    safe_claims: list[str] = []
    collection_claims: list[str] = []
    blocked_claims: list[str] = []
    for row in rows:
        command_ref = clean_identifier(row.get("command_ref"), default="validation_command_ref", max_length=220)
        scope_ref = clean_identifier(row.get("result_scope_ref"), default="selected_target_only", max_length=180)
        if row.get("green_claim_allowed") is True:
            safe_claims.append(f"{command_ref}__{scope_ref}__green_claim_scope")
        if row.get("collection_only_claim_allowed") is True:
            collection_claims.append(f"{command_ref}__{scope_ref}__collection_only_not_full_suite")
    for claim in supplied or ():
        clean = clean_identifier(claim, max_length=220)
        if not clean:
            continue
        if _op24_contains_blocked_claim_ref(clean):
            blocked_claims.append(clean)
        else:
            safe_claims.append(clean)
    return (
        dedupe_identifiers(safe_claims, limit=120, max_length=240),
        dedupe_identifiers(collection_claims, limit=120, max_length=240),
        dedupe_identifiers(blocked_claims, limit=120, max_length=240),
    )


def _op24_status_next_reason(
    op23: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    blocked_claim_refs: Sequence[str],
) -> tuple[str, str, list[str]]:
    if op23.get("handoff_status") != P7_R54_OP23_R52_REINTAKE_HANDOFF_READY_STATUS_REF or op23.get("next_required_step") != P7_R54_OP24_STEP_REF:
        reasons = dedupe_identifiers([P7_R54_OP24_BLOCKED_BY_OP23_REASON_REF, *(op23.get("open_execution_blocker_ids") or [])], limit=120, max_length=220)
        return (P7_R54_OP24_DOCUMENTATION_OUTPUT_BLOCKED_BY_OP23_STATUS_REF, P7_R54_OP24_BLOCKED_NEXT_REQUIRED_STEP_REF, reasons)
    if not rows:
        return (P7_R54_OP24_DOCUMENTATION_OUTPUT_BLOCKED_BY_COMMAND_MATRIX_STATUS_REF, P7_R54_OP24_BLOCKED_NEXT_REQUIRED_STEP_REF, [P7_R54_OP24_COMMAND_MATRIX_MISSING_REASON_REF])
    failed_rows = [clean_identifier(row.get("command_ref"), default="validation_command_failed", max_length=220) for row in rows if row.get("result_status_ref") == P7_R54_OP24_COMMAND_RESULT_FAILED_REF]
    if failed_rows:
        return (
            P7_R54_OP24_DOCUMENTATION_OUTPUT_BLOCKED_BY_COMMAND_MATRIX_STATUS_REF,
            P7_R54_OP24_BLOCKED_NEXT_REQUIRED_STEP_REF,
            dedupe_identifiers([P7_R54_OP24_COMMAND_MATRIX_FAILED_REASON_REF, *failed_rows], limit=120, max_length=220),
        )
    if blocked_claim_refs:
        return (
            P7_R54_OP24_DOCUMENTATION_OUTPUT_BLOCKED_BY_CLAIM_OVERREACH_STATUS_REF,
            P7_R54_OP24_BLOCKED_NEXT_REQUIRED_STEP_REF,
            dedupe_identifiers([P7_R54_OP24_GREEN_CLAIM_OVERREACH_REASON_REF, *blocked_claim_refs], limit=120, max_length=220),
        )
    return (P7_R54_OP24_DOCUMENTATION_OUTPUT_READY_STATUS_REF, P7_R54_OP_NEXT_WORK_AFTER_OP24_REF, [P7_R54_OP24_READY_REASON_REF])


def build_p7_r54_op24_validation_command_matrix_documentation_output(
    *,
    r52_reintake_handoff: Mapping[str, Any] | None = None,
    validation_command_rows: Sequence[Mapping[str, Any]] | None = None,
    not_executed_validation_refs: Sequence[Any] | None = None,
    green_claim_scope_refs: Sequence[Any] | None = None,
    material_id: Any = "p7_r54_operation_validation_command_matrix_documentation_output",
) -> dict[str, Any]:
    op23 = safe_mapping(r52_reintake_handoff) if r52_reintake_handoff is not None else build_p7_r54_op23_r52_reintake_handoff()
    assert_p7_r54_op23_r52_reintake_handoff_contract(op23)
    review_session_id = _safe_review_session_id(op23.get("review_session_id"))
    rows = _op24_command_rows_from_input(validation_command_rows, review_session_id=review_session_id)
    safe_claim_refs, collection_claim_refs, blocked_claim_refs = _op24_claim_scope_refs(rows, green_claim_scope_refs)
    status, next_step, reason_refs = _op24_status_next_reason(op23, rows, blocked_claim_refs)
    ready = status == P7_R54_OP24_DOCUMENTATION_OUTPUT_READY_STATUS_REF
    not_executed_refs = dedupe_identifiers(
        not_executed_validation_refs or P7_R54_OP24_DEFAULT_NOT_EXECUTED_VALIDATION_REFS,
        limit=80,
        max_length=220,
    )
    failed_count = sum(1 for row in rows if row.get("result_status_ref") == P7_R54_OP24_COMMAND_RESULT_FAILED_REF)
    collected_count = sum(1 for row in rows if row.get("result_status_ref") == P7_R54_OP24_COMMAND_RESULT_COLLECTED_ONLY_REF)
    passed_count = sum(1 for row in rows if row.get("result_status_ref") == P7_R54_OP24_COMMAND_RESULT_PASSED_REF)
    executed_rows = [row for row in rows if row.get("result_status_ref") != P7_R54_OP24_COMMAND_RESULT_NOT_EXECUTED_REF]
    issue_refs = [] if ready else dedupe_identifiers([*reason_refs, *blocked_claim_refs], limit=160, max_length=240)
    material = {
        "schema_version": P7_R54_OPERATION_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_OPERATION_REENTRY_STEP,
        "scope": P7_R54_OPERATION_REENTRY_SCOPE,
        "policy_kind": P7_R54_OPERATION_REENTRY_POLICY_KIND,
        "policy_section": P7_R54_OP24_STEP_REF,
        "operation_step_ref": P7_R54_OP24_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_operation_validation_command_matrix_documentation_output", max_length=220),
        "review_session_id": review_session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op23_schema_version": P7_R54_OPERATION_R52_REINTAKE_HANDOFF_SCHEMA_VERSION,
        "op23_material_ref": clean_identifier(op23.get("material_id"), default="p7_r54_operation_r52_reintake_handoff", max_length=220),
        "op23_next_required_step": clean_identifier(op23.get("next_required_step"), default="", max_length=180),
        "op23_handoff_status": clean_identifier(op23.get("handoff_status"), default=P7_R54_OP23_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING_STATUS_REF, max_length=180),
        "op23_r52_reintake_handoff_ready": op23.get("r52_reintake_handoff_ready") is True,
        "op23_actual_review_evidence_complete": op23.get("actual_review_evidence_complete") is True,
        "operation_current_refs": dict(P7_R54_OPERATION_CURRENT_REFS),
        "operation_current_ref_count": len(P7_R54_OPERATION_CURRENT_REFS),
        "actual_review_basis_ref": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_OPERATION_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        **_false_flags(),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "reviewed_case_count": int(op23.get("reviewed_case_count") or 0) if op23.get("r52_reintake_handoff_ready") is True else 0,
        "rating_row_count": int(op23.get("rating_row_count") or 0) if op23.get("r52_reintake_handoff_ready") is True else 0,
        "question_observation_row_count": int(op23.get("question_observation_row_count") or 0) if op23.get("r52_reintake_handoff_ready") is True else 0,
        "disposal_verified": op23.get("disposal_verified") is True and op23.get("r52_reintake_handoff_ready") is True,
        "actual_review_evidence_complete": op23.get("actual_review_evidence_complete") is True and ready,
        "body_free_evidence_handoff_materialized_here": op23.get("body_free_evidence_handoff_materialized_here") is True and ready,
        "r52_reintake_handoff_ready": op23.get("r52_reintake_handoff_ready") is True and ready,
        "r52_reintake_required": op23.get("r52_reintake_required") is True and ready,
        "p5_decision_candidate": clean_identifier(op23.get("p5_decision_candidate"), default=P7_R54_OP19_INCONCLUSIVE_REF, max_length=180),
        "p5_human_blind_qa_confirmed_candidate": op23.get("p5_human_blind_qa_confirmed_candidate") is True and ready,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_candidate": op23.get("p6_limited_human_readfeel_candidate") is True and ready,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_question_design_material_candidate": op23.get("p8_question_design_material_candidate") is True and ready,
        "p8_start_allowed": False,
        "question_implementation_started_here": False,
        "p8_implementation_spec_finalized_here": False,
        "p8_question_implementation_spec_finalized_here": False,
        "release_allowed": False,
        "documentation_output_status": status,
        "documentation_output_ref": P7_R54_OP24_DOCUMENTATION_OUTPUT_REF if ready else "validation_command_matrix_documentation_output_not_ready_bodyfree",
        "documentation_output_reason_refs": reason_refs,
        "documentation_output_issue_refs": issue_refs,
        "documentation_output_issue_count": len(issue_refs),
        "documentation_output_materialized_here": ready,
        "validation_command_row_schema_version": P7_R54_OPERATION_VALIDATION_COMMAND_MATRIX_ROW_SCHEMA_VERSION,
        "validation_command_row_required_field_refs": list(P7_R54_OPERATION_VALIDATION_COMMAND_MATRIX_ROW_REQUIRED_FIELD_REFS),
        "validation_command_rows": rows,
        "validation_command_row_count": len(rows),
        "executed_validation_command_refs": [clean_identifier(row.get("command_ref"), default="validation_command", max_length=220) for row in executed_rows] if ready else [],
        "executed_validation_command_count": len(executed_rows) if ready else 0,
        "passed_validation_command_count": passed_count if ready else 0,
        "collected_only_validation_command_count": collected_count if ready else 0,
        "failed_validation_command_count": failed_count,
        "not_executed_validation_command_count": sum(1 for row in rows if row.get("result_status_ref") == P7_R54_OP24_COMMAND_RESULT_NOT_EXECUTED_REF),
        "not_executed_validation_refs": not_executed_refs,
        "not_executed_validation_ref_count": len(not_executed_refs),
        "green_claim_scope_refs": safe_claim_refs if ready else [],
        "green_claim_scope_count": len(safe_claim_refs) if ready else 0,
        "collection_only_scope_refs": collection_claim_refs if ready else [],
        "collection_only_scope_count": len(collection_claim_refs) if ready else 0,
        "blocked_green_claim_refs": blocked_claim_refs,
        "blocked_green_claim_count": len(blocked_claim_refs),
        "claim_boundary_guard_refs": list(P7_R54_OP24_CLAIM_BOUNDARY_GUARD_REFS),
        "claim_boundary_guard_count": len(P7_R54_OP24_CLAIM_BOUNDARY_GUARD_REFS),
        "collect_only_claimed_as_full_suite_green": False,
        "rn_contract_claimed_as_real_device_modal_verified": False,
        "r54_helper_green_claimed_as_actual_human_review_complete": False,
        "full_backend_suite_green_claimed": False,
        "real_device_modal_verified_claimed": False,
        "actual_human_review_complete_claimed_by_helper": False,
        "release_claimed_from_validation_matrix": False,
        "command_result_body_stored_here": False,
        "terminal_output_stored_here": False,
        "command_string_included": False,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "execution_blocker_ids": issue_refs,
        "open_execution_blocker_ids": issue_refs,
        "implemented_steps": list(P7_R54_OP24_IMPLEMENTED_STEPS if ready else tuple(op23.get("implemented_steps") or ())),
        "not_yet_implemented_steps": list(P7_R54_OP24_NOT_YET_IMPLEMENTED_STEPS if ready else tuple(op23.get("not_yet_implemented_steps") or ())),
        "first_next_work_ref": P7_R54_OP_NEXT_WORK_AFTER_OP24_REF if ready else P7_R54_OP_NEXT_WORK_AFTER_OP23_REF,
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "r54_operation_no_touch_contract": _operation_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "raw_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
    }
    assert_p7_r54_op24_validation_command_matrix_documentation_output_contract(material)
    return material


def assert_p7_r54_op24_validation_command_matrix_documentation_output_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_OPERATION_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS, source="p7_r54_op24_validation_command_matrix_documentation_output")
    _assert_common_operation_contract(
        data,
        schema_version=P7_R54_OPERATION_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION,
        policy_section=P7_R54_OP24_STEP_REF,
        operation_step_ref=P7_R54_OP24_STEP_REF,
        source="p7_r54_op24_validation_command_matrix_documentation_output",
        false_flag_refs=_op24_false_flag_refs(),
    )
    _assert_operation_current_refs(data, source="p7_r54_op24_validation_command_matrix_documentation_output")
    if data.get("documentation_output_status") not in P7_R54_OP24_ALLOWED_DOCUMENTATION_OUTPUT_STATUS_REFS:
        raise ValueError("R54 OP24 documentation output status outside allowed refs")
    ready = data.get("documentation_output_status") == P7_R54_OP24_DOCUMENTATION_OUTPUT_READY_STATUS_REF
    if data.get("documentation_output_materialized_here") is not ready:
        raise ValueError("R54 OP24 documentation materialization flag must match status")
    for row in data.get("validation_command_rows") or ():
        assert_p7_r54_op24_validation_command_matrix_row_contract(row)
    for false_key in (
        "collect_only_claimed_as_full_suite_green", "rn_contract_claimed_as_real_device_modal_verified",
        "r54_helper_green_claimed_as_actual_human_review_complete", "full_backend_suite_green_claimed",
        "real_device_modal_verified_claimed", "actual_human_review_complete_claimed_by_helper",
        "release_claimed_from_validation_matrix", "command_result_body_stored_here", "terminal_output_stored_here",
        "command_string_included", "p5_human_blind_qa_confirmed_final", "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed", "question_implementation_started_here", "p8_implementation_spec_finalized_here",
        "p8_question_implementation_spec_finalized_here", "release_allowed", "raw_body_included",
        "question_text_included", "draft_question_text_included", "local_path_included",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 OP24 must keep {false_key}=False")
    if data.get("blocked_green_claim_count") != len(data.get("blocked_green_claim_refs") or ()): 
        raise ValueError("R54 OP24 blocked green claim count changed")
    if data.get("collection_only_scope_count") != len(data.get("collection_only_scope_refs") or ()): 
        raise ValueError("R54 OP24 collection-only scope count changed")
    if data.get("green_claim_scope_count") != len(data.get("green_claim_scope_refs") or ()): 
        raise ValueError("R54 OP24 green claim scope count changed")
    if data.get("not_executed_validation_ref_count") != len(data.get("not_executed_validation_refs") or ()): 
        raise ValueError("R54 OP24 not-executed validation count changed")
    if ready:
        if data.get("op23_handoff_status") != P7_R54_OP23_R52_REINTAKE_HANDOFF_READY_STATUS_REF or data.get("op23_r52_reintake_handoff_ready") is not True:
            raise ValueError("R54 OP24 ready must be based on OP23 R52 handoff ready")
        if data.get("actual_review_evidence_complete") is not True or data.get("r52_reintake_handoff_ready") is not True:
            raise ValueError("R54 OP24 ready must preserve OP23 body-free evidence completion")
        for count_key in ("reviewed_case_count", "rating_row_count", "question_observation_row_count"):
            if data.get(count_key) != P7_R51_REQUIRED_CASE_COUNT:
                raise ValueError(f"R54 OP24 ready must preserve 24 {count_key}")
        if data.get("validation_command_row_count") <= 0 or data.get("executed_validation_command_count") <= 0:
            raise ValueError("R54 OP24 ready requires executed validation command refs")
        if data.get("failed_validation_command_count") != 0 or data.get("open_execution_blocker_ids"):
            raise ValueError("R54 OP24 ready must not carry failed validation rows or blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_OP24_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP24 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_OP24_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 OP24 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_OP_NEXT_WORK_AFTER_OP24_REF:
            raise ValueError("R54 OP24 ready next required step changed")
    else:
        if data.get("actual_review_evidence_complete") is not False or data.get("r52_reintake_handoff_ready") is not False:
            raise ValueError("R54 OP24 blocked must not expose evidence completion")
        if not data.get("open_execution_blocker_ids"):
            raise ValueError("R54 OP24 blocked must carry blocker refs")
        if data.get("next_required_step") != P7_R54_OP24_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 OP24 blocked next step changed")
    return True


# OP24 detailed-design wording aliases.
build_p7_r54_operation_validation_command_matrix_documentation_output = build_p7_r54_op24_validation_command_matrix_documentation_output
assert_p7_r54_operation_validation_command_matrix_documentation_output_contract = assert_p7_r54_op24_validation_command_matrix_documentation_output_contract
build_p7_r54_operation_validation_command_matrix_documentation_output_bodyfree = build_p7_r54_operation_validation_command_matrix_documentation_output
assert_p7_r54_operation_validation_command_matrix_documentation_output_bodyfree_contract = assert_p7_r54_operation_validation_command_matrix_documentation_output_contract

__all__ = tuple(__all__) + (
    "P7_R54_OPERATION_VALIDATION_COMMAND_MATRIX_ROW_SCHEMA_VERSION",
    "P7_R54_OPERATION_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION",
    "P7_R54_OP24_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_OP_NEXT_WORK_AFTER_OP24_REF",
    "P7_R54_OP24_IMPLEMENTED_STEPS",
    "P7_R54_OP24_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_OP24_DOCUMENTATION_OUTPUT_READY_STATUS_REF",
    "P7_R54_OP24_DOCUMENTATION_OUTPUT_BLOCKED_STATUS_REF",
    "P7_R54_OP24_DOCUMENTATION_OUTPUT_BLOCKED_BY_OP23_STATUS_REF",
    "P7_R54_OP24_DOCUMENTATION_OUTPUT_BLOCKED_BY_COMMAND_MATRIX_STATUS_REF",
    "P7_R54_OP24_DOCUMENTATION_OUTPUT_BLOCKED_BY_CLAIM_OVERREACH_STATUS_REF",
    "P7_R54_OP24_ALLOWED_DOCUMENTATION_OUTPUT_STATUS_REFS",
    "P7_R54_OP24_DOCUMENTATION_OUTPUT_REF",
    "P7_R54_OP24_READY_REASON_REF",
    "P7_R54_OP24_BLOCKED_BY_OP23_REASON_REF",
    "P7_R54_OP24_COMMAND_MATRIX_MISSING_REASON_REF",
    "P7_R54_OP24_COMMAND_MATRIX_FAILED_REASON_REF",
    "P7_R54_OP24_GREEN_CLAIM_OVERREACH_REASON_REF",
    "P7_R54_OP24_COMMAND_RESULT_PASSED_REF",
    "P7_R54_OP24_COMMAND_RESULT_COLLECTED_ONLY_REF",
    "P7_R54_OP24_COMMAND_RESULT_NOT_EXECUTED_REF",
    "P7_R54_OP24_COMMAND_RESULT_FAILED_REF",
    "P7_R54_OP24_ALLOWED_COMMAND_RESULT_STATUS_REFS",
    "P7_R54_OP24_CLAIM_BOUNDARY_GUARD_REFS",
    "P7_R54_OP24_DEFAULT_NOT_EXECUTED_VALIDATION_REFS",
    "P7_R54_OPERATION_VALIDATION_COMMAND_MATRIX_ROW_REQUIRED_FIELD_REFS",
    "P7_R54_OPERATION_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS",
    "build_p7_r54_op24_validation_command_matrix_row",
    "assert_p7_r54_op24_validation_command_matrix_row_contract",
    "build_p7_r54_op24_validation_command_matrix_documentation_output",
    "assert_p7_r54_op24_validation_command_matrix_documentation_output_contract",
    "build_p7_r54_operation_validation_command_matrix_documentation_output",
    "assert_p7_r54_operation_validation_command_matrix_documentation_output_contract",
    "build_p7_r54_operation_validation_command_matrix_documentation_output_bodyfree",
    "assert_p7_r54_operation_validation_command_matrix_documentation_output_bodyfree_contract",
)
