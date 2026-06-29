# -*- coding: utf-8 -*-
"""R54-AHR-CR current received actual local-only review operation helper.

CR00-CR22 are intentionally thin, body-free, and no-touch:

* CR00 freezes the scope / no-touch boundary for the current received
  264/85/258/171 actual local-only human review operation.
* CR01 freezes the current received 264/85/258/171 basis envelope as the only
  allowed actual-review basis for later CR operation steps.
* CR02 separates the existing AHR / CS / related helpers as historical,
  structural, and regression refs only.
* CR03 records basis impact handling body-free; direct diff unavailable is not
  treated as no impact, and CR04 manifest refreeze remains required.
* CR04 refreezes the current 24-case manifest body-free on the current received
  basis; it does not materialize packet bodies or actual review rows.
* CR05 freezes local-only preflight / explicit allow / retention boundaries
  before any body-full packet generation request bridge can be considered.
* CR06 records only the body-free packet-generation request bridge; it never
  generates or exports packet bodies.
* CR07 records only body-free packet receipt / completeness / export-denylist
  refs when explicitly supplied; it never stores packet bodies, paths, or hashes.
* CR08 freezes the reviewer person boundary and selection-only form shape; it
  does not run or complete the actual human review.
* CR09 intakes only the body-free operation receipt for a person-executed
  local-only review; it still does not create rating rows, question rows,
  disposal receipts, P5 finalization, P6/P8 start, or release permission.
* CR10 intakes only sanitized selection-only result rows as body-free refs,
  counts, scores, and classifications; it does not create rating rows.
* CR11 normalizes rating rows from accepted sanitized rows; it still does not
  create question observation rows, disposal receipts, P5 finalization, P6/P8
  start, R52 execution, P7 completion, or release permission.
* CR12 normalizes readfeel / execution / repair / inconclusive blockers as
  body-free rows and explicitly prevents P5/P4/operation blockers from escaping
  into P8 material candidates.
* CR13 normalizes 24 body-free question need observation rows from CR10/CR11
  and CR12; it does not create question text, P8 implementation specs, P8 start,
  evidence completion, disposal receipts, or release permission.
* CR14 guards rating rows against question observation rows so repair, blocker,
  risk, or insufficient material cases cannot escape into P8 material candidates;
  it still does not complete evidence, create disposal receipts, start P8/P6, or
  execute R52.
* CR15 intakes only body-free pause / abort / expiration / disposal receipt refs
  and lifecycle flags; it may verify disposal but still leaves actual review
  evidence completion, P5 finalization, P6/P8 start, R52 execution, P7
  completion, and release permission to later gates.
* CR16 evaluates the post-review summary / evidence-complete predicate only
  when the person receipt, 24 sanitized rows, 24 rating rows, 24 question
  observation rows, consistency guard, disposal, no-leak, no-question, and
  no-touch predicates are all complete; it still does not finalize P5 or start
  P6/P8/R52/release.
* CR17 separates P5 confirmed candidate, P5 repair, P4 current-only repair,
  operation blocked, and inconclusive states body-free; P5 confirmed candidate
  remains candidate-only and is not P5 final.
* CR18 hands off P6 limited human readfeel as candidate-only material when
  CR17 has a clean P5 confirmed candidate; it still does not start P6.
* CR19 hands off P8 material candidates from actual-review-derived question
  observation rows as body-free rows only; it still does not create question
  text, P8 API/DB/RN/trigger/storage, P8 start, or release permission.
* CR20 creates an R52 handoff candidate envelope only when CR16-CR19 are
  ready; R52 re-intake execution remains blocked and unconfirmed here.
* CR21 validates CR00-CR20 body-free artifacts for no body leak,
  no-question-text, and no-touch boundaries without promoting P5/P6/P8/R52,
  P7 completion, or release.
* CR22 documents the validation command matrix, result memo ref, and claim
  boundary without claiming full backend suite green, RN real-device verification,
  P5 finalization, P6/P8 start, R52 execution, P7 completion, or release.

This helper does not rewrite the existing 2026-06-27 AHR helper
(260/83/256/169) or the 2026-06-28 CS re-entry helper (262/84/257/170).
Those remain historical / structural / regression references only.

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
import emlis_ai_p7_r54_ahr_current_snapshot_actual_review_reentry_20260628 as historical_cs


P7_R54_AHR_CR00_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_received_actual_local_review_operation."
    "cr00_scope_no_touch_boundary_freeze.bodyfree.v1"
)
P7_R54_AHR_CR01_CURRENT_RECEIVED_BASIS_ENVELOPE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_received_actual_local_review_operation."
    "cr01_current_received_basis_envelope.bodyfree.v1"
)
P7_R54_AHR_CR02_HISTORICAL_HELPER_REFS_SEPARATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_received_actual_local_review_operation."
    "cr02_historical_helper_refs_separation.bodyfree.v1"
)
P7_R54_AHR_CR03_BASIS_IMPACT_ASSESSMENT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_received_actual_local_review_operation."
    "cr03_basis_impact_assessment.bodyfree.v1"
)
P7_R54_AHR_CR04_CURRENT_24_CASE_MANIFEST_REFREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_received_actual_local_review_operation."
    "cr04_current_24_case_manifest_refreeze.bodyfree.v1"
)
P7_R54_AHR_CR05_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_received_actual_local_review_operation."
    "cr05_local_only_preflight_explicit_allow_retention.bodyfree.v1"
)
P7_R54_AHR_CR06_PACKET_GENERATION_REQUEST_BRIDGE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_received_actual_local_review_operation."
    "cr06_body_full_packet_generation_request_bridge.bodyfree.v1"
)
P7_R54_AHR_CR07_PACKET_GENERATION_RECEIPT_SCAN_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_received_actual_local_review_operation."
    "cr07_packet_generation_receipt_completeness_export_denylist_scan.bodyfree.v1"
)
P7_R54_AHR_CR08_REVIEWER_SELECTION_FORM_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_received_actual_local_review_operation."
    "cr08_reviewer_selection_form_person_boundary.bodyfree.v1"
)
P7_R54_AHR_CR09_ACTUAL_LOCAL_HUMAN_REVIEW_OPERATION_RECEIPT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_received_actual_local_review_operation."
    "cr09_actual_local_only_human_review_operation_receipt_intake.bodyfree.v1"
)
P7_R54_AHR_CR10_SANITIZED_SELECTION_ONLY_RESULT_ROWS_INTAKE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_received_actual_local_review_operation."
    "cr10_sanitized_selection_only_result_rows_intake.bodyfree.v1"
)
P7_R54_AHR_CR11_RATING_ROW_NORMALIZATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_received_actual_local_review_operation."
    "cr11_rating_row_normalization.bodyfree.v1"
)
P7_R54_AHR_CR10_SELECTION_RESULT_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_received_actual_local_review_operation."
    "cr10_sanitized_selection_only_result_row.bodyfree.v1"
)
P7_R54_AHR_CR11_RATING_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_received_actual_local_review_operation."
    "cr11_rating_row.bodyfree.v1"
)
P7_R54_AHR_CR_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CR00_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION
)
P7_R54_AHR_CR_CURRENT_RECEIVED_BASIS_ENVELOPE_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CR01_CURRENT_RECEIVED_BASIS_ENVELOPE_SCHEMA_VERSION
)
P7_R54_AHR_CR_HISTORICAL_HELPER_REFS_SEPARATION_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CR02_HISTORICAL_HELPER_REFS_SEPARATION_SCHEMA_VERSION
)
P7_R54_AHR_CR_BASIS_IMPACT_ASSESSMENT_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CR03_BASIS_IMPACT_ASSESSMENT_SCHEMA_VERSION
)
P7_R54_AHR_CR_CURRENT_24_CASE_MANIFEST_REFREEZE_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CR04_CURRENT_24_CASE_MANIFEST_REFREEZE_SCHEMA_VERSION
)
P7_R54_AHR_CR_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CR05_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION
)
P7_R54_AHR_CR_PACKET_GENERATION_REQUEST_BRIDGE_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CR06_PACKET_GENERATION_REQUEST_BRIDGE_SCHEMA_VERSION
)
P7_R54_AHR_CR_PACKET_GENERATION_RECEIPT_SCAN_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CR07_PACKET_GENERATION_RECEIPT_SCAN_SCHEMA_VERSION
)
P7_R54_AHR_CR_REVIEWER_SELECTION_FORM_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CR08_REVIEWER_SELECTION_FORM_SCHEMA_VERSION
)
P7_R54_AHR_CR_ACTUAL_LOCAL_HUMAN_REVIEW_OPERATION_RECEIPT_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CR09_ACTUAL_LOCAL_HUMAN_REVIEW_OPERATION_RECEIPT_SCHEMA_VERSION
)
P7_R54_AHR_CR_SANITIZED_SELECTION_ONLY_RESULT_ROWS_INTAKE_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CR10_SANITIZED_SELECTION_ONLY_RESULT_ROWS_INTAKE_SCHEMA_VERSION
)
P7_R54_AHR_CR_RATING_ROW_NORMALIZATION_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CR11_RATING_ROW_NORMALIZATION_SCHEMA_VERSION
)

P7_R54_AHR_CR_STEP: Final = "R54-AHR-CR_CurrentReceivedActualLocalReviewOperation_20260628"
P7_R54_AHR_CR_SCOPE: Final = "p5_user_label_connection_current_received_actual_local_only_human_review_operation"
P7_R54_AHR_CR_POLICY_KIND: Final = "r54_ahr_current_received_actual_local_review_operation_boundary"
P7_R54_AHR_CR_CURRENT_PHASE: Final = P7_PHASE
P7_R54_AHR_CR_DEFAULT_REVIEW_SESSION_ID: Final = (
    "p7_r54_ahr_current_received_actual_local_review_operation_20260628"
)

P7_R54_AHR_CR00_STEP_REF: Final = "R54-AHR-CR00_scope_no_touch_boundary_freeze"
P7_R54_AHR_CR01_STEP_REF: Final = "R54-AHR-CR01_current_received_264_85_258_171_basis_envelope"
P7_R54_AHR_CR02_STEP_REF: Final = "R54-AHR-CR02_historical_helper_refs_separation"
P7_R54_AHR_CR03_STEP_REF: Final = "R54-AHR-CR03_basis_impact_assessment"
P7_R54_AHR_CR04_STEP_REF: Final = "R54-AHR-CR04_current_24_case_manifest_refreeze"
P7_R54_AHR_CR05_STEP_REF: Final = "R54-AHR-CR05_local_only_preflight_explicit_allow_retention"
P7_R54_AHR_CR06_STEP_REF: Final = "R54-AHR-CR06_body_full_packet_generation_request_bridge"
P7_R54_AHR_CR07_STEP_REF: Final = "R54-AHR-CR07_packet_generation_receipt_completeness_export_scan"
P7_R54_AHR_CR08_STEP_REF: Final = "R54-AHR-CR08_reviewer_selection_form_person_boundary"
P7_R54_AHR_CR09_STEP_REF: Final = "R54-AHR-CR09_actual_local_human_review_operation_receipt_intake"
P7_R54_AHR_CR10_STEP_REF: Final = "R54-AHR-CR10_sanitized_selection_only_result_rows_intake"
P7_R54_AHR_CR11_STEP_REF: Final = "R54-AHR-CR11_rating_row_normalization"
P7_R54_AHR_CR12_STEP_REF: Final = "R54-AHR-CR12_readfeel_execution_blocker_normalization"
P7_R54_AHR_CR13_STEP_REF: Final = "R54-AHR-CR13_question_need_observation_normalization"
P7_R54_AHR_CR14_STEP_REF: Final = "R54-AHR-CR14_rating_question_consistency_guard"
P7_R54_AHR_CR15_STEP_REF: Final = "R54-AHR-CR15_pause_abort_expiration_disposal_receipt"
P7_R54_AHR_CR16_STEP_REF: Final = "R54-AHR-CR16_post_review_summary_evidence_complete_predicate"
P7_R54_AHR_CR17_STEP_REF: Final = "R54-AHR-CR17_p5_decision_candidate_repair_separation"
P7_R54_AHR_CR18_STEP_REF: Final = "R54-AHR-CR18_p6_candidate_only_handoff"
P7_R54_AHR_CR19_STEP_REF: Final = "R54-AHR-CR19_p8_material_candidate_only_handoff"
P7_R54_AHR_CR20_STEP_REF: Final = "R54-AHR-CR20_r52_handoff_candidate_envelope"
P7_R54_AHR_CR21_STEP_REF: Final = "R54-AHR-CR21_final_no_body_no_question_no_touch_validation"
P7_R54_AHR_CR22_STEP_REF: Final = "R54-AHR-CR22_validation_command_matrix_documentation_output"

P7_R54_AHR_CR_STEP_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR00_STEP_REF,
    P7_R54_AHR_CR01_STEP_REF,
    P7_R54_AHR_CR02_STEP_REF,
    P7_R54_AHR_CR03_STEP_REF,
    P7_R54_AHR_CR04_STEP_REF,
    P7_R54_AHR_CR05_STEP_REF,
    P7_R54_AHR_CR06_STEP_REF,
    P7_R54_AHR_CR07_STEP_REF,
    P7_R54_AHR_CR08_STEP_REF,
    P7_R54_AHR_CR09_STEP_REF,
    P7_R54_AHR_CR10_STEP_REF,
    P7_R54_AHR_CR11_STEP_REF,
    P7_R54_AHR_CR12_STEP_REF,
    P7_R54_AHR_CR13_STEP_REF,
    P7_R54_AHR_CR14_STEP_REF,
    P7_R54_AHR_CR15_STEP_REF,
    P7_R54_AHR_CR16_STEP_REF,
    P7_R54_AHR_CR17_STEP_REF,
    P7_R54_AHR_CR18_STEP_REF,
    P7_R54_AHR_CR19_STEP_REF,
    P7_R54_AHR_CR20_STEP_REF,
    P7_R54_AHR_CR21_STEP_REF,
    P7_R54_AHR_CR22_STEP_REF,
)
P7_R54_AHR_CR00_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_AHR_CR00_STEP_REF,)
P7_R54_AHR_CR00_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CR_STEP_REFS[1:]
P7_R54_AHR_CR01_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR00_STEP_REF,
    P7_R54_AHR_CR01_STEP_REF,
)
P7_R54_AHR_CR01_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CR_STEP_REFS[2:]
P7_R54_AHR_CR02_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR00_STEP_REF,
    P7_R54_AHR_CR01_STEP_REF,
    P7_R54_AHR_CR02_STEP_REF,
)
P7_R54_AHR_CR02_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CR_STEP_REFS[3:]
P7_R54_AHR_CR03_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR00_STEP_REF,
    P7_R54_AHR_CR01_STEP_REF,
    P7_R54_AHR_CR02_STEP_REF,
    P7_R54_AHR_CR03_STEP_REF,
)
P7_R54_AHR_CR03_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CR_STEP_REFS[4:]
P7_R54_AHR_CR04_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR00_STEP_REF,
    P7_R54_AHR_CR01_STEP_REF,
    P7_R54_AHR_CR02_STEP_REF,
    P7_R54_AHR_CR03_STEP_REF,
    P7_R54_AHR_CR04_STEP_REF,
)
P7_R54_AHR_CR04_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CR_STEP_REFS[5:]
P7_R54_AHR_CR05_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR00_STEP_REF,
    P7_R54_AHR_CR01_STEP_REF,
    P7_R54_AHR_CR02_STEP_REF,
    P7_R54_AHR_CR03_STEP_REF,
    P7_R54_AHR_CR04_STEP_REF,
    P7_R54_AHR_CR05_STEP_REF,
)
P7_R54_AHR_CR05_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CR_STEP_REFS[6:]
P7_R54_AHR_CR06_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR00_STEP_REF,
    P7_R54_AHR_CR01_STEP_REF,
    P7_R54_AHR_CR02_STEP_REF,
    P7_R54_AHR_CR03_STEP_REF,
    P7_R54_AHR_CR04_STEP_REF,
    P7_R54_AHR_CR05_STEP_REF,
    P7_R54_AHR_CR06_STEP_REF,
)
P7_R54_AHR_CR06_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CR_STEP_REFS[7:]
P7_R54_AHR_CR07_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR00_STEP_REF,
    P7_R54_AHR_CR01_STEP_REF,
    P7_R54_AHR_CR02_STEP_REF,
    P7_R54_AHR_CR03_STEP_REF,
    P7_R54_AHR_CR04_STEP_REF,
    P7_R54_AHR_CR05_STEP_REF,
    P7_R54_AHR_CR06_STEP_REF,
    P7_R54_AHR_CR07_STEP_REF,
)
P7_R54_AHR_CR07_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CR_STEP_REFS[8:]
P7_R54_AHR_CR08_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR00_STEP_REF,
    P7_R54_AHR_CR01_STEP_REF,
    P7_R54_AHR_CR02_STEP_REF,
    P7_R54_AHR_CR03_STEP_REF,
    P7_R54_AHR_CR04_STEP_REF,
    P7_R54_AHR_CR05_STEP_REF,
    P7_R54_AHR_CR06_STEP_REF,
    P7_R54_AHR_CR07_STEP_REF,
    P7_R54_AHR_CR08_STEP_REF,
)
P7_R54_AHR_CR08_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CR_STEP_REFS[9:]
P7_R54_AHR_CR09_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR00_STEP_REF,
    P7_R54_AHR_CR01_STEP_REF,
    P7_R54_AHR_CR02_STEP_REF,
    P7_R54_AHR_CR03_STEP_REF,
    P7_R54_AHR_CR04_STEP_REF,
    P7_R54_AHR_CR05_STEP_REF,
    P7_R54_AHR_CR06_STEP_REF,
    P7_R54_AHR_CR07_STEP_REF,
    P7_R54_AHR_CR08_STEP_REF,
    P7_R54_AHR_CR09_STEP_REF,
)
P7_R54_AHR_CR09_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CR_STEP_REFS[10:]
P7_R54_AHR_CR10_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR09_IMPLEMENTED_STEPS,
    P7_R54_AHR_CR10_STEP_REF,
)
P7_R54_AHR_CR10_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CR_STEP_REFS[11:]
P7_R54_AHR_CR11_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR10_IMPLEMENTED_STEPS,
    P7_R54_AHR_CR11_STEP_REF,
)
P7_R54_AHR_CR11_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CR_STEP_REFS[12:]

P7_R54_AHR_CR_ACTUAL_REVIEW_BASIS_REF: Final = "current_received_snapshot_264_85_258_171"
P7_R54_AHR_CR_ACTUAL_REVIEW_BASIS_ALLOWED_REF: Final = "current_received_snapshot_264_85_258_171_only"
P7_R54_AHR_CR_CURRENT_BASIS_STATUS_REF: Final = (
    "CURRENT_RECEIVED_264_85_258_171_BASIS_REFROZEN_FOR_R54_AHR_CR_ACTUAL_LOCAL_REVIEW_OPERATION"
)
P7_R54_AHR_CR_CURRENT_BASIS_REFREEZE_STATUS_REF: Final = P7_R54_AHR_CR_CURRENT_BASIS_STATUS_REF

P7_R54_AHR_CR_CURRENT_RECEIVED_SNAPSHOT_REFS: Final[dict[str, str]] = {
    "premise_zip_ref": "Cocolon_前提資料(264).zip",
    "implemented_materials_zip_ref": "EmlisAIの実装済み資料(85).zip",
    "roadmap_zip_ref": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619(4).zip",
    "rn_zip_ref": "Cocolon(258).zip",
    "backend_zip_ref": "mashos-api(171).zip",
    "pre_design_memo_ref": "Cocolon_EmlisAI_P7_R54AHR_CurrentReceivedSnapshotActualReview_PreDesignMemo_20260628.md",
    "detailed_design_ref": (
        "Cocolon_EmlisAI_P7_R54AHR_CurrentReceivedSnapshotActualLocalReviewOperation_"
        "DetailedDesign_ImplementationOrder_20260628.md"
    ),
}
P7_R54_AHR_CR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS: Final[tuple[str, ...]] = tuple(
    P7_R54_AHR_CR_CURRENT_RECEIVED_SNAPSHOT_REFS.keys()
)
P7_R54_AHR_CR_REQUIRED_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS: Final[tuple[str, ...]] = (
    "premise_zip_ref",
    "implemented_materials_zip_ref",
    "roadmap_zip_ref",
    "rn_zip_ref",
    "backend_zip_ref",
    "pre_design_memo_ref",
    "detailed_design_ref",
)
P7_R54_AHR_CR_OUTER_RECEIVED_ZIP_REF_KEYS: Final[tuple[str, ...]] = (
    "premise_zip_ref",
    "implemented_materials_zip_ref",
    "roadmap_zip_ref",
    "rn_zip_ref",
    "backend_zip_ref",
)
P7_R54_AHR_CR_INTERNAL_SOURCE_LINEAGE_REFS: Final[dict[str, str]] = {
    "premise_manifest_ref": "Cocolon_前提資料/manifest.json",
    "premise_read_first_ref": "Cocolon_前提資料/00_karen_read_first.md",
    "work_attitude_read_first_ref": "Cocolon_前提資料/work_attitude_rules_for_karen/00_read_first.txt",
    "work_attitude_integrated_ref": "Cocolon_前提資料/work_attitude_rules_for_karen/99_integrated_paste_each_time.txt",
    "correction_policy_ref": "Cocolon_前提資料/emlis_ai_correction_policy_withdrawal_retention_redesign_2026_05_31.md",
}

P7_R54_AHR_CR_HISTORICAL_AHR_BASIS_REF: Final = historical_ahr.P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF
P7_R54_AHR_CR_HISTORICAL_AHR_BASIS_ALLOWED_REF: Final = historical_ahr.P7_R54_AHR_ACTUAL_EXECUTION_BASIS_ALLOWED_REF
P7_R54_AHR_CR_HISTORICAL_AHR_BASIS_REFS: Final[dict[str, str]] = dict(
    historical_ahr.P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS
)
P7_R54_AHR_CR_HISTORICAL_CS_BASIS_REF: Final = historical_cs.P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF
P7_R54_AHR_CR_HISTORICAL_CS_BASIS_ALLOWED_REF: Final = historical_cs.P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_ALLOWED_REF
P7_R54_AHR_CR_HISTORICAL_CS_BASIS_REFS: Final[dict[str, str]] = dict(
    historical_cs.P7_R54_AHR_CS_CURRENT_RECEIVED_SNAPSHOT_REFS
)
P7_R54_AHR_CR_HISTORICAL_BASIS_REFS: Final[dict[str, dict[str, str]]] = {
    "r54_ahr_20260627_basis_260_83_256_169": dict(P7_R54_AHR_CR_HISTORICAL_AHR_BASIS_REFS),
    "r54_ahr_cs_20260628_basis_262_84_257_170": dict(P7_R54_AHR_CR_HISTORICAL_CS_BASIS_REFS),
}
P7_R54_AHR_CR_HISTORICAL_BASIS_CLASSIFICATION_REFS: Final[dict[str, str]] = {
    "r54_ahr_20260627_basis_260_83_256_169": "historical_structural_regression_ref_only",
    "r54_ahr_cs_20260628_basis_262_84_257_170": "historical_structural_regression_ref_only",
}
P7_R54_AHR_CR_CLAIM_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "helper_green_is_not_actual_human_review_complete",
    "existing_ahr_260_83_256_169_is_not_current_264_85_258_171_actual_review_evidence",
    "existing_cs_262_84_257_170_is_not_current_264_85_258_171_actual_review_evidence",
    "selected_regression_green_is_not_full_backend_suite_green",
    "p8_material_candidate_only_is_not_p8_start_allowed",
    "p5_confirmed_candidate_is_not_p5_final",
    "r52_handoff_ready_is_not_r52_reintake_executed",
)

P7_R54_AHR_CR_HISTORICAL_HELPER_SEPARATION_STATUS_REF: Final = (
    "HISTORICAL_HELPER_REFS_SEPARATED_FROM_CURRENT_264_85_258_171_ACTUAL_REVIEW_EVIDENCE"
)
P7_R54_AHR_CR_HISTORICAL_HELPER_REF_GROUP_REFS: Final[tuple[str, ...]] = (
    "r54_ahr_20260627_basis",
    "r54_ahr_cs_20260628_basis",
    "r54_clr_refs",
    "r54_op_refs",
    "r54_ev_refs",
    "r55_refs",
    "r52_refs",
)
P7_R54_AHR_CR_HISTORICAL_HELPER_REFS: Final[dict[str, dict[str, str]]] = {
    "r54_ahr_20260627_basis": dict(P7_R54_AHR_CR_HISTORICAL_AHR_BASIS_REFS),
    "r54_ahr_cs_20260628_basis": dict(P7_R54_AHR_CR_HISTORICAL_CS_BASIS_REFS),
    "r54_clr_refs": dict(historical_ahr.P7_R54_AHR_HISTORICAL_HELPER_REFS["r54_clr_20260627"]),
    "r54_op_refs": dict(historical_ahr.P7_R54_AHR_HISTORICAL_HELPER_REFS["r54_op_20260625"]),
    "r54_ev_refs": dict(historical_ahr.P7_R54_AHR_HISTORICAL_HELPER_REFS["r54_ev_20260626"]),
    "r55_refs": dict(historical_ahr.P7_R54_AHR_HISTORICAL_HELPER_REFS["r55_20260623"]),
    "r52_refs": dict(historical_ahr.P7_R54_AHR_HISTORICAL_HELPER_REFS["r52_20260621"]),
}
P7_R54_AHR_CR_HISTORICAL_HELPER_ROLE_REFS: Final[dict[str, str]] = {
    "r54_ahr_20260627_basis": "actual_human_review_bodyfree_intake_historical_contract",
    "r54_ahr_cs_20260628_basis": "current_snapshot_actual_review_reentry_historical_contract",
    "r54_clr_refs": "current_snapshot_local_run_structural_helper",
    "r54_op_refs": "actual_local_review_operation_structural_helper",
    "r54_ev_refs": "execution_evidence_materialization_structural_helper",
    "r55_refs": "evidence_reconcile_reintake_decision_structural_helper",
    "r52_refs": "handoff_p6_p8_start_decision_gate_structural_helper",
}
P7_R54_AHR_CR_HISTORICAL_HELPER_CLASSIFICATION_REFS: Final[dict[str, str]] = {
    group_ref: "historical_structural_regression_ref_only"
    for group_ref in P7_R54_AHR_CR_HISTORICAL_HELPER_REF_GROUP_REFS
}
P7_R54_AHR_CR_HISTORICAL_HELPER_ALLOWED_USAGE_REFS: Final[tuple[str, ...]] = (
    "historical_ref",
    "structural_ref",
    "regression_ref",
    "bodyfree_helper_design_reference",
    "no_leak_no_question_no_touch_test_design_reference",
)
P7_R54_AHR_CR_HISTORICAL_HELPER_PROHIBITED_USAGE_REFS: Final[tuple[str, ...]] = (
    "current_264_85_258_171_actual_review_basis",
    "current_264_85_258_171_actual_review_evidence",
    "current_264_85_258_171_actual_rating_rows",
    "current_264_85_258_171_question_need_observation_rows",
    "p5_final",
    "p6_start",
    "p8_start",
    "release_decision",
)
P7_R54_AHR_CR_BASIS_IMPACT_ASSESSMENT_STATUS_REF: Final = (
    "CURRENT_264_85_258_171_BASIS_IMPACT_ASSESSMENT_RECORDED_BODYFREE_REFREEZE_REQUIRED"
)
P7_R54_AHR_CR03_DIRECT_DIFF_UNAVAILABLE_REASON_REF_DEFAULT: Final = (
    "DIRECT_DIFF_UNAVAILABLE_HISTORICAL_262_84_257_170_ZIP_SET_NOT_RECEIVED_IN_CURRENT_LOCAL_PACKAGE"
)
P7_R54_AHR_CR03_DIRECT_DIFF_UNAVAILABLE_RESULT_REF: Final = (
    "DIRECT_DIFF_UNAVAILABLE_CURRENT_MANIFEST_REFREEZE_REQUIRED"
)
P7_R54_AHR_CR03_DIRECT_DIFF_EXECUTED_RESULT_REF: Final = (
    "DIRECT_DIFF_EXECUTED_BODYFREE_IMPACT_SUMMARY_RECORDED"
)
P7_R54_AHR_CR03_DEFAULT_IMPACT_SUMMARY_REF: Final = "CURRENT_BASIS_IMPACT_SUMMARY_BODYFREE_REF"
P7_R54_AHR_CR03_DIFF_IMPACT_STATUS_REFS: Final[tuple[str, ...]] = (
    "NO_REVIEW_MANIFEST_IMPACT",
    "REVIEW_MANIFEST_IMPACT_PRESENT",
    "DIFF_INCONCLUSIVE",
    P7_R54_AHR_CR03_DIRECT_DIFF_UNAVAILABLE_RESULT_REF,
    P7_R54_AHR_CR03_DIRECT_DIFF_EXECUTED_RESULT_REF,
)
P7_R54_AHR_CR03_IMPACT_TARGET_REFS: Final[tuple[str, ...]] = (
    "current_24_case_manifest",
    "local_only_packet_boundary",
    "bodyfree_evidence_rows",
    "actual_review_receipt_chain",
    "r52_reintake_handoff_candidate_envelope",
)

P7_R54_AHR_CR_REQUIRED_CASE_COUNT: Final = 24
P7_R54_AHR_CR04_MANIFEST_REFREEZE_STATUS_REF: Final = (
    "CR04_CURRENT_RECEIVED_264_85_258_171_24_CASE_MANIFEST_REFROZEN_BODYFREE"
)
P7_R54_AHR_CR04_MANIFEST_SOURCE_KIND_REF: Final = (
    "current_received_264_85_258_171_bodyfree_manifest_refreeze"
)
P7_R54_AHR_CR04_REVIEW_AXIS_PROFILE_REF: Final = (
    "r54_ahr_p5_history_line_existing_6_axis_profile_current_received_20260628"
)
P7_R54_AHR_CR04_CASE_DISTRIBUTION: Final[dict[str, int]] = dict(historical_ahr.P7_R54_AHR05_CASE_DISTRIBUTION)
P7_R54_AHR_CR04_CASE_ROLE_BY_FAMILY: Final[dict[str, str]] = dict(historical_ahr.P7_R54_AHR05_CASE_ROLE_BY_FAMILY)
P7_R54_AHR_CR04_RATING_AXIS_REFS: Final[tuple[str, ...]] = historical_ahr.P7_R54_AHR05_RATING_AXIS_REFS
P7_R54_AHR_CR04_RATING_AXIS_TARGET_THRESHOLDS: Final[dict[str, float]] = dict(
    historical_ahr.P7_R54_AHR05_RATING_AXIS_TARGET_THRESHOLDS
)
P7_R54_AHR_CR04_CASE_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "case_index",
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
    "family_ref",
    "case_role_ref",
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
P7_R54_AHR_CR05_PREFLIGHT_READY_STATUS_REF: Final = (
    "CR05_LOCAL_ONLY_PREFLIGHT_READY_BODYFULL_PACKET_REQUEST_MAY_BE_CONSIDERED"
)
P7_R54_AHR_CR05_PREFLIGHT_BLOCKED_STATUS_REF: Final = (
    "CR05_LOCAL_ONLY_PREFLIGHT_BLOCKED_EXPLICIT_ALLOW_OR_POLICY_MISSING"
)
P7_R54_AHR_CR05_ALLOWED_PREFLIGHT_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR05_PREFLIGHT_READY_STATUS_REF,
    P7_R54_AHR_CR05_PREFLIGHT_BLOCKED_STATUS_REF,
)
P7_R54_AHR_CR05_READY_REASON_REF: Final = (
    "CR05_LOCAL_ONLY_EXPLICIT_ALLOW_RETENTION_DISPOSAL_EXPORT_DENYLIST_READY"
)
P7_R54_AHR_CR05_EXPLICIT_ALLOW_MISSING_BLOCKER_REF: Final = "explicit_allow_ref_missing"
P7_R54_AHR_CR05_LOCAL_REVIEW_ROOT_MISSING_BLOCKER_REF: Final = "local_review_root_ref_missing"
P7_R54_AHR_CR05_RETENTION_POLICY_MISSING_BLOCKER_REF: Final = "retention_policy_ref_missing"
P7_R54_AHR_CR05_DISPOSAL_POLICY_MISSING_BLOCKER_REF: Final = "disposal_policy_ref_missing"
P7_R54_AHR_CR05_EXPORT_DENYLIST_POLICY_MISSING_BLOCKER_REF: Final = "export_denylist_policy_ref_missing"
P7_R54_AHR_CR05_BODYFULL_EXPORT_ALLOWED_BLOCKER_REF: Final = "body_full_packet_export_allowed"
P7_R54_AHR_CR05_LOCAL_ONLY_FALSE_BLOCKER_REF: Final = "local_only_not_confirmed"
P7_R54_AHR_CR05_MUST_NOT_EXPORT_FALSE_BLOCKER_REF: Final = "must_not_export_not_confirmed"
P7_R54_AHR_CR05_DEFAULT_EXPLICIT_ALLOW_REF: Final = (
    "R54_AHR_CURRENT_RECEIVED_264_85_258_171_LOCAL_ONLY_REVIEW_ALLOWED"
)
P7_R54_AHR_CR05_DEFAULT_LOCAL_REVIEW_ROOT_REF: Final = "LOCAL_ONLY_REVIEW_ROOT_SANITIZED_REF"
P7_R54_AHR_CR05_DEFAULT_RETENTION_POLICY_REF: Final = "local_body_full_packet_max_72h_or_shorter"
P7_R54_AHR_CR05_DEFAULT_DISPOSAL_POLICY_REF: Final = "body_full_packet_disposal_required_after_review_or_abort"
P7_R54_AHR_CR05_DEFAULT_EXPORT_DENYLIST_POLICY_REF: Final = (
    "body_full_packet_never_exported_to_repo_docs_release_public_meta"
)
P7_R54_AHR_CR05_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "explicit_allow_or_stop"

P7_R54_AHR_CR06_PACKET_REQUEST_READY_STATUS_REF: Final = (
    "CR06_PACKET_GENERATION_REQUEST_BRIDGE_READY_BODYFREE_REQUEST_REF_ONLY"
)
P7_R54_AHR_CR06_PACKET_REQUEST_BLOCKED_STATUS_REF: Final = (
    "CR06_PACKET_GENERATION_REQUEST_BRIDGE_BLOCKED_PREFLIGHT_NOT_READY"
)
P7_R54_AHR_CR06_ALLOWED_PACKET_REQUEST_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR06_PACKET_REQUEST_READY_STATUS_REF,
    P7_R54_AHR_CR06_PACKET_REQUEST_BLOCKED_STATUS_REF,
)
P7_R54_AHR_CR06_READY_REASON_REF: Final = (
    "CR06_CR05_READY_PREFLIGHT_ALLOWS_BODYFREE_PACKET_REQUEST_BRIDGE"
)
P7_R54_AHR_CR06_PREFLIGHT_NOT_READY_BLOCKER_REF: Final = "cr05_preflight_not_ready"
P7_R54_AHR_CR06_PACKET_NOT_ALLOWED_BY_PREFLIGHT_BLOCKER_REF: Final = (
    "cr05_packet_generation_not_allowed_by_preflight"
)
P7_R54_AHR_CR06_ACTUAL_OPERATION_NOT_ALLOWED_BY_PREFLIGHT_BLOCKER_REF: Final = (
    "cr05_actual_review_operation_not_allowed_by_preflight"
)
P7_R54_AHR_CR06_EXPLICIT_ALLOW_MISSING_BLOCKER_REF: Final = "cr05_explicit_allow_missing"
P7_R54_AHR_CR06_BODYFULL_EXPORT_ALLOWED_BLOCKER_REF: Final = "cr05_body_full_packet_export_allowed"
P7_R54_AHR_CR06_BODYFULL_CONTENT_INCLUDED_BLOCKER_REF: Final = "cr05_body_full_packet_content_included"
P7_R54_AHR_CR06_BODYFULL_ALREADY_GENERATED_BLOCKER_REF: Final = "cr05_body_full_packet_already_generated"
P7_R54_AHR_CR06_ACTUAL_REVIEW_ALREADY_RUN_BLOCKER_REF: Final = "cr05_actual_human_review_already_run"
P7_R54_AHR_CR06_DEFAULT_PACKET_GENERATION_REQUEST_REF: Final = (
    "R54_AHR_CR06_CURRENT_RECEIVED_264_85_258_171_BODYFULL_PACKET_GENERATION_REQUEST_BODYFREE_REF"
)
P7_R54_AHR_CR06_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "cr05_ready_preflight_or_stop"

P7_R54_AHR_CR07_PACKET_RECEIPT_ACCEPTED_STATUS_REF: Final = (
    "CR07_PACKET_GENERATION_RECEIPT_AND_SCAN_ACCEPTED_BODYFREE_REFS_ONLY"
)
P7_R54_AHR_CR07_PACKET_RECEIPT_BLOCKED_STATUS_REF: Final = (
    "CR07_PACKET_GENERATION_RECEIPT_AND_SCAN_BLOCKED_OR_MISSING"
)
P7_R54_AHR_CR07_ALLOWED_PACKET_RECEIPT_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR07_PACKET_RECEIPT_ACCEPTED_STATUS_REF,
    P7_R54_AHR_CR07_PACKET_RECEIPT_BLOCKED_STATUS_REF,
)
P7_R54_AHR_CR07_READY_REASON_REF: Final = (
    "CR07_BODYFREE_RECEIPT_COUNTS_COMPLETENESS_EXPORT_DENYLIST_REFS_ACCEPTED"
)
P7_R54_AHR_CR07_CR06_NOT_READY_BLOCKER_REF: Final = "cr06_packet_generation_request_bridge_not_ready"
P7_R54_AHR_CR07_CR06_REQUEST_REF_MISSING_BLOCKER_REF: Final = "cr06_packet_generation_request_ref_missing"
P7_R54_AHR_CR07_RECEIPT_INPUT_MISSING_BLOCKER_REF: Final = "packet_generation_receipt_input_missing"
P7_R54_AHR_CR07_RECEIPT_REF_MISSING_BLOCKER_REF: Final = "packet_generation_receipt_ref_missing"
P7_R54_AHR_CR07_PACKET_COUNT_NOT_24_BLOCKER_REF: Final = "packet_case_count_not_24"
P7_R54_AHR_CR07_COMPLETENESS_SCAN_REF_MISSING_BLOCKER_REF: Final = "packet_completeness_scan_ref_missing"
P7_R54_AHR_CR07_EXPORT_DENYLIST_SCAN_REF_MISSING_BLOCKER_REF: Final = "export_denylist_scan_ref_missing"
P7_R54_AHR_CR07_COMPLETENESS_SCAN_NOT_PASSED_BLOCKER_REF: Final = "packet_completeness_scan_not_passed"
P7_R54_AHR_CR07_EXPORT_DENYLIST_SCAN_NOT_PASSED_BLOCKER_REF: Final = "export_denylist_scan_not_passed"
P7_R54_AHR_CR07_FORBIDDEN_RECEIPT_KEY_BLOCKER_REF: Final = "receipt_input_forbidden_body_question_path_hash_key"
P7_R54_AHR_CR07_DEFAULT_PACKET_GENERATION_RECEIPT_REF: Final = (
    "R54_AHR_CR07_CURRENT_RECEIVED_264_85_258_171_LOCAL_ONLY_PACKET_GENERATION_RECEIPT_BODYFREE_REF"
)
P7_R54_AHR_CR07_DEFAULT_PACKET_COMPLETENESS_SCAN_REF: Final = (
    "R54_AHR_CR07_24_PACKET_COMPLETENESS_SCAN_BODYFREE_REF"
)
P7_R54_AHR_CR07_DEFAULT_EXPORT_DENYLIST_SCAN_REF: Final = (
    "R54_AHR_CR07_EXPORT_DENYLIST_SCAN_BODYFREE_REF"
)
P7_R54_AHR_CR07_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "packet_generation_receipt_or_stop"

P7_R54_AHR_CR08_REVIEWER_FORM_READY_STATUS_REF: Final = (
    "CR08_REVIEWER_SELECTION_FORM_READY_SELECTION_ONLY_PERSON_BOUNDARY_BODYFREE"
)
P7_R54_AHR_CR08_REVIEWER_FORM_BLOCKED_STATUS_REF: Final = (
    "CR08_REVIEWER_SELECTION_FORM_BLOCKED_PERSON_BOUNDARY_OR_PACKET_RECEIPT_MISSING"
)
P7_R54_AHR_CR08_ALLOWED_REVIEWER_FORM_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR08_REVIEWER_FORM_READY_STATUS_REF,
    P7_R54_AHR_CR08_REVIEWER_FORM_BLOCKED_STATUS_REF,
)
P7_R54_AHR_CR08_READY_REASON_REF: Final = (
    "CR08_CR07_ACCEPTED_PACKET_RECEIPT_AND_REVIEWER_PERSON_BOUNDARY_READY"
)
P7_R54_AHR_CR08_CR07_NOT_READY_BLOCKER_REF: Final = "cr07_packet_generation_receipt_not_ready"
P7_R54_AHR_CR08_CR07_RECEIPT_REF_MISSING_BLOCKER_REF: Final = "cr07_packet_generation_receipt_ref_missing"
P7_R54_AHR_CR08_CR07_PACKET_COUNT_NOT_24_BLOCKER_REF: Final = "cr07_packet_case_count_not_24"
P7_R54_AHR_CR08_CR07_PACKET_SCAN_NOT_PASSED_BLOCKER_REF: Final = "cr07_packet_completeness_or_export_scan_not_passed"
P7_R54_AHR_CR08_CR07_BODY_LEAK_BLOCKER_REF: Final = "cr07_packet_receipt_body_leak_detected"
P7_R54_AHR_CR08_CR07_PATH_HASH_LEAK_BLOCKER_REF: Final = "cr07_packet_receipt_path_or_hash_leak_detected"
P7_R54_AHR_CR08_REVIEWER_PERSON_REF_MISSING_BLOCKER_REF: Final = "reviewer_person_ref_missing"
P7_R54_AHR_CR08_REVIEWER_IS_PERSON_FALSE_BLOCKER_REF: Final = "reviewer_is_person_not_confirmed"
P7_R54_AHR_CR08_REVIEWER_PERSON_NOT_CONFIRMED_BLOCKER_REF: Final = "reviewer_person_confirmed_false"
P7_R54_AHR_CR08_DEFAULT_REVIEWER_PERSON_REF: Final = (
    "R54_AHR_CR08_CURRENT_RECEIVED_264_85_258_171_REVIEWER_PERSON_LOCAL_ONLY_REF"
)
P7_R54_AHR_CR08_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "reviewer_person_boundary_or_stop"
P7_R54_AHR_CR08_RATING_AXIS_REFS: Final[tuple[str, ...]] = P7_R54_AHR_CR04_RATING_AXIS_REFS
P7_R54_AHR_CR08_RATING_AXIS_TARGET_THRESHOLDS: Final[dict[str, float]] = dict(
    P7_R54_AHR_CR04_RATING_AXIS_TARGET_THRESHOLDS
)
P7_R54_AHR_CR08_QUESTION_NEED_PRIMARY_CLASS_OPTION_REFS: Final[tuple[str, ...]] = (
    historical_ahr.P7_R54_AHR09_QUESTION_NEED_PRIMARY_CLASS_REFS
)
P7_R54_AHR_CR08_ONE_QUESTION_FIT_OPTION_REFS: Final[tuple[str, ...]] = (
    historical_ahr.P7_R54_AHR09_ONE_QUESTION_FIT_OPTION_REFS
)

P7_R54_AHR_CR09_OPERATION_RECEIPT_ACCEPTED_STATUS_REF: Final = (
    "CR09_ACTUAL_LOCAL_ONLY_HUMAN_REVIEW_OPERATION_RECEIPT_ACCEPTED_BODYFREE"
)
P7_R54_AHR_CR09_OPERATION_RECEIPT_BLOCKED_STATUS_REF: Final = (
    "CR09_ACTUAL_LOCAL_ONLY_HUMAN_REVIEW_OPERATION_RECEIPT_BLOCKED_OR_MISSING"
)
P7_R54_AHR_CR09_ALLOWED_OPERATION_RECEIPT_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR09_OPERATION_RECEIPT_ACCEPTED_STATUS_REF,
    P7_R54_AHR_CR09_OPERATION_RECEIPT_BLOCKED_STATUS_REF,
)
P7_R54_AHR_CR09_READY_REASON_REF: Final = (
    "CR09_PERSON_EXECUTED_LOCAL_ONLY_REVIEW_RECEIPT_ACCEPTED_BODYFREE_COUNTS_ONLY"
)
P7_R54_AHR_CR09_CR08_NOT_READY_BLOCKER_REF: Final = "cr08_reviewer_selection_form_not_ready"
P7_R54_AHR_CR09_CR08_REVIEWER_PERSON_REF_MISSING_BLOCKER_REF: Final = "cr08_reviewer_person_ref_missing"
P7_R54_AHR_CR09_CR08_REVIEWER_PERSON_NOT_CONFIRMED_BLOCKER_REF: Final = "cr08_reviewer_person_not_confirmed"
P7_R54_AHR_CR09_OPERATION_RECEIPT_INPUT_MISSING_BLOCKER_REF: Final = "operation_receipt_input_missing"
P7_R54_AHR_CR09_FORBIDDEN_RECEIPT_KEY_BLOCKER_REF: Final = "operation_receipt_forbidden_body_question_path_hash_key"
P7_R54_AHR_CR09_OPERATION_RECEIPT_REF_MISSING_BLOCKER_REF: Final = "operation_receipt_ref_missing"
P7_R54_AHR_CR09_REVIEWER_LOCAL_ONLY_READ_RECEIPT_MISSING_BLOCKER_REF: Final = (
    "reviewer_local_only_read_receipt_missing"
)
P7_R54_AHR_CR09_REVIEW_STARTED_BUCKET_REF_MISSING_BLOCKER_REF: Final = "review_started_at_bucket_ref_missing"
P7_R54_AHR_CR09_REVIEW_COMPLETED_BUCKET_REF_MISSING_BLOCKER_REF: Final = "review_completed_at_bucket_ref_missing"
P7_R54_AHR_CR09_REVIEWED_CASE_COUNT_NOT_24_BLOCKER_REF: Final = "reviewed_case_count_not_24"
P7_R54_AHR_CR09_SELECTION_ROW_COUNT_NOT_24_BLOCKER_REF: Final = "selection_row_count_not_24"
P7_R54_AHR_CR09_LOCAL_ONLY_FALSE_BLOCKER_REF: Final = "operation_receipt_local_only_not_confirmed"
P7_R54_AHR_CR09_MUST_NOT_EXPORT_FALSE_BLOCKER_REF: Final = "operation_receipt_must_not_export_not_confirmed"
P7_R54_AHR_CR09_SELECTION_ONLY_FALSE_BLOCKER_REF: Final = "operation_receipt_selection_only_not_confirmed"
P7_R54_AHR_CR09_REVIEWER_PERSON_REF_MISMATCH_BLOCKER_REF: Final = "operation_receipt_reviewer_person_ref_mismatch"
P7_R54_AHR_CR09_DEFAULT_OPERATION_RECEIPT_REF: Final = (
    "R54_AHR_CR09_CURRENT_RECEIVED_264_85_258_171_ACTUAL_LOCAL_ONLY_HUMAN_REVIEW_OPERATION_RECEIPT_BODYFREE_REF"
)
P7_R54_AHR_CR09_DEFAULT_REVIEW_STARTED_AT_BUCKET_REF: Final = "review_started_bucket_20260628_local_only"
P7_R54_AHR_CR09_DEFAULT_REVIEW_COMPLETED_AT_BUCKET_REF: Final = "review_completed_bucket_20260628_local_only"
P7_R54_AHR_CR09_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "actual_local_review_operation_receipt_or_stop"
P7_R54_AHR_CR09_ALLOWED_TRUE_OPERATION_FLAG_REFS: Final[tuple[str, ...]] = (
    "actual_human_review_run_here",
    "actual_human_review_operation_run",
    "actual_human_review_executed_by_person",
)

P7_R54_AHR_CR10_SANITIZED_ROWS_ACCEPTED_STATUS_REF: Final = (
    "CR10_SANITIZED_SELECTION_ONLY_RESULT_ROWS_ACCEPTED_BODYFREE"
)
P7_R54_AHR_CR10_SANITIZED_ROWS_BLOCKED_STATUS_REF: Final = (
    "CR10_SANITIZED_SELECTION_ONLY_RESULT_ROWS_BLOCKED_OR_INVALID"
)
P7_R54_AHR_CR10_ALLOWED_SANITIZED_ROWS_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR10_SANITIZED_ROWS_ACCEPTED_STATUS_REF,
    P7_R54_AHR_CR10_SANITIZED_ROWS_BLOCKED_STATUS_REF,
)
P7_R54_AHR_CR10_READY_REASON_REF: Final = (
    "CR10_PERSON_EXECUTED_LOCAL_REVIEW_SELECTION_ONLY_ROWS_ACCEPTED_BODYFREE"
)
P7_R54_AHR_CR10_CR09_NOT_READY_BLOCKER_REF: Final = "cr09_operation_receipt_not_ready"
P7_R54_AHR_CR10_CR09_NEXT_STEP_NOT_CR10_BLOCKER_REF: Final = "cr09_next_step_not_cr10"
P7_R54_AHR_CR10_CR09_PERSON_EXECUTION_NOT_CONFIRMED_BLOCKER_REF: Final = (
    "cr09_actual_human_review_executed_by_person_not_confirmed"
)
P7_R54_AHR_CR10_CR09_REVIEWED_CASE_COUNT_NOT_24_BLOCKER_REF: Final = "cr09_reviewed_case_count_not_24"
P7_R54_AHR_CR10_CR09_SELECTION_ROW_COUNT_NOT_24_BLOCKER_REF: Final = "cr09_selection_row_count_not_24"
P7_R54_AHR_CR10_SELECTION_ROWS_INPUT_MISSING_BLOCKER_REF: Final = "selection_result_rows_input_missing"
P7_R54_AHR_CR10_SELECTION_ROW_COUNT_NOT_24_BLOCKER_REF: Final = "selection_result_row_count_not_24"
P7_R54_AHR_CR10_SELECTION_ROW_NOT_MAPPING_BLOCKER_REF: Final = "selection_result_row_not_mapping"
P7_R54_AHR_CR10_SELECTION_ROW_FORBIDDEN_KEY_BLOCKER_REF: Final = (
    "selection_result_row_forbidden_body_question_path_hash_key"
)
P7_R54_AHR_CR10_SELECTION_ROW_CASE_REF_NOT_IN_MANIFEST_BLOCKER_REF: Final = "selection_result_row_case_ref_not_in_manifest"
P7_R54_AHR_CR10_SELECTION_ROW_ID_MISMATCH_BLOCKER_REF: Final = "selection_result_row_blind_or_packet_id_mismatch"
P7_R54_AHR_CR10_SELECTION_ROW_OPERATION_RECEIPT_REF_MISMATCH_BLOCKER_REF: Final = (
    "selection_result_row_operation_receipt_ref_mismatch"
)
P7_R54_AHR_CR10_SELECTION_ROW_REVIEW_SESSION_ID_MISMATCH_BLOCKER_REF: Final = (
    "selection_result_row_review_session_id_mismatch"
)
P7_R54_AHR_CR10_SELECTION_ROW_REVIEWER_PERSON_REF_MISMATCH_BLOCKER_REF: Final = (
    "selection_result_row_reviewer_person_ref_mismatch"
)
P7_R54_AHR_CR10_SELECTION_ROW_REVIEWED_AT_REF_MISSING_BLOCKER_REF: Final = "selection_result_row_reviewed_at_ref_missing"
P7_R54_AHR_CR10_SELECTION_ROW_AXIS_REFS_MISMATCH_BLOCKER_REF: Final = "selection_result_row_axis_refs_mismatch"
P7_R54_AHR_CR10_SELECTION_ROW_AXIS_SCORE_INVALID_BLOCKER_REF: Final = "selection_result_row_axis_score_invalid"
P7_R54_AHR_CR10_SELECTION_ROW_VERDICT_NOT_ALLOWED_BLOCKER_REF: Final = "selection_result_row_verdict_not_allowed"
P7_R54_AHR_CR10_SELECTION_ROW_OPTION_NOT_ALLOWED_BLOCKER_REF: Final = "selection_result_row_option_ref_not_allowed"
P7_R54_AHR_CR10_SELECTION_ROW_SELECTION_ONLY_FALSE_BLOCKER_REF: Final = "selection_result_row_selection_only_false"
P7_R54_AHR_CR10_SELECTION_ROW_BODY_FREE_FALSE_BLOCKER_REF: Final = "selection_result_row_body_free_false"
P7_R54_AHR_CR10_SELECTION_ROW_UNIQUE_REFS_NOT_24_BLOCKER_REF: Final = "selection_result_row_unique_refs_not_24"
P7_R54_AHR_CR10_DEFAULT_REVIEWED_AT_BUCKET_REF: Final = "reviewed_bucket_20260628_local_only"
P7_R54_AHR_CR10_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "sanitized_selection_only_result_rows_or_stop"
P7_R54_AHR_CR10_VERDICT_OPTION_REFS: Final[tuple[str, ...]] = historical_ahr.P7_R54_AHR09_VERDICT_OPTION_REFS
P7_R54_AHR_CR10_SANITIZED_REASON_ID_OPTION_REFS: Final[tuple[str, ...]] = (
    historical_ahr.P7_R54_AHR09_SANITIZED_REASON_ID_OPTION_REFS
)
P7_R54_AHR_CR10_READFEEL_BLOCKER_ID_OPTION_REFS: Final[tuple[str, ...]] = (
    historical_ahr.P7_R54_AHR09_READFEEL_BLOCKER_ID_OPTION_REFS
)
P7_R54_AHR_CR10_EXECUTION_BLOCKER_ID_OPTION_REFS: Final[tuple[str, ...]] = (
    historical_ahr.P7_R54_AHR09_EXECUTION_BLOCKER_ID_OPTION_REFS
)
P7_R54_AHR_CR10_QUESTION_NEED_PRIMARY_CLASS_OPTION_REFS: Final[tuple[str, ...]] = (
    historical_ahr.P7_R54_AHR09_QUESTION_NEED_PRIMARY_CLASS_REFS
)
P7_R54_AHR_CR10_AMBIGUITY_KIND_OPTION_REFS: Final[tuple[str, ...]] = (
    historical_ahr.P7_R54_AHR09_AMBIGUITY_KIND_OPTION_REFS
)
P7_R54_AHR_CR10_ONE_QUESTION_FIT_OPTION_REFS: Final[tuple[str, ...]] = (
    historical_ahr.P7_R54_AHR09_ONE_QUESTION_FIT_OPTION_REFS
)
P7_R54_AHR_CR10_REPAIR_REQUIRED_OPTION_REFS: Final[tuple[str, ...]] = (
    historical_ahr.P7_R54_AHR09_REPAIR_REQUIRED_OPTION_REFS
)
P7_R54_AHR_CR10_PLAN_CANDIDATE_FLAG_REFS: Final[tuple[str, ...]] = (
    historical_ahr.P7_R54_AHR09_PLAN_CANDIDATE_FLAG_REFS
)
P7_R54_AHR_CR10_ROW_BODYFREE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
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
P7_R54_AHR_CR10_ALLOWED_TRUE_OPERATION_FLAG_REFS: Final[tuple[str, ...]] = (
    "actual_human_review_executed_by_person",
)

P7_R54_AHR_CR11_RATING_ROWS_NORMALIZED_STATUS_REF: Final = "CR11_RATING_ROWS_NORMALIZED_BODYFREE"
P7_R54_AHR_CR11_RATING_ROWS_BLOCKED_STATUS_REF: Final = "CR11_RATING_ROW_NORMALIZATION_BLOCKED"
P7_R54_AHR_CR11_ALLOWED_RATING_ROW_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR11_RATING_ROWS_NORMALIZED_STATUS_REF,
    P7_R54_AHR_CR11_RATING_ROWS_BLOCKED_STATUS_REF,
)
P7_R54_AHR_CR11_READY_REASON_REF: Final = "CR11_SANITIZED_SELECTION_ROWS_NORMALIZED_TO_RATING_ROWS_BODYFREE"
P7_R54_AHR_CR11_CR10_NOT_READY_BLOCKER_REF: Final = "cr10_sanitized_selection_result_rows_not_ready"
P7_R54_AHR_CR11_CR10_NEXT_STEP_NOT_CR11_BLOCKER_REF: Final = "cr10_next_step_not_cr11"
P7_R54_AHR_CR11_CR10_PERSON_EXECUTION_NOT_CONFIRMED_BLOCKER_REF: Final = (
    "cr10_actual_human_review_executed_by_person_not_confirmed"
)
P7_R54_AHR_CR11_CR10_SANITIZED_ROW_COUNT_NOT_24_BLOCKER_REF: Final = "cr10_sanitized_review_result_row_count_not_24"
P7_R54_AHR_CR11_SOURCE_ROW_INVALID_BLOCKER_REF: Final = "rating_source_sanitized_row_invalid"
P7_R54_AHR_CR11_SOURCE_ROW_FORBIDDEN_KEY_BLOCKER_REF: Final = "rating_source_row_forbidden_body_question_path_hash_key"
P7_R54_AHR_CR11_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "rating_row_normalization_or_stop"
P7_R54_AHR_CR11_RATING_ROW_BODYFREE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = P7_R54_AHR_CR10_ROW_BODYFREE_FALSE_FLAG_REFS
P7_R54_AHR_CR11_ALLOWED_TRUE_OPERATION_FLAG_REFS: Final[tuple[str, ...]] = (
    "actual_human_review_executed_by_person",
    "actual_rating_rows_materialized_here",
)

P7_R54_AHR_CR_OUT_OF_SCOPE_REFS: Final[tuple[str, ...]] = (
    "api_route_or_request_response_key_change",
    "db_schema_or_migration_change",
    "rn_production_ui_or_display_condition_change",
    "runtime_generation_or_gate_threshold_change",
    "public_response_key_change",
    "user_label_connection_runtime_change",
    "p8_question_api_db_rn_trigger_storage_or_text_generation",
    "question_answer_persistence",
    "body_full_packet_generation_or_export",
    "actual_human_review_execution",
    "actual_rating_or_question_rows_materialization",
    "disposal_or_purge_execution",
    "p6_limited_human_readfeel_start",
    "r52_reintake_actual_execution",
    "p5_finalization",
    "p7_completion",
    "release_decision",
)

P7_R54_AHR_CR_NO_TOUCH_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "api_changed",
    "db_changed",
    "rn_changed",
    "runtime_changed",
    "api_route_changed",
    "request_key_changed",
    "response_key_changed",
    "response_shape_changed",
    "request_response_key_changed",
    "db_schema_changed",
    "db_migration_added",
    "db_migration_created",
    "db_physical_schema_changed",
    "rn_ui_changed",
    "rn_production_ui_changed",
    "rn_visible_contract_changed",
    "rn_display_condition_changed",
    "public_response_key_changed",
    "public_response_top_level_key_added",
    "public_response_top_level_key_changed",
    "runtime_gate_threshold_changed",
    "gate_threshold_changed",
    "user_label_connection_runtime_changed",
    "emlis_visible_output_generation_changed",
    "subscription_or_plan_access_policy_changed",
    "question_implementation_started_here",
    "question_trigger_logic_implemented",
    "question_api_implemented",
    "question_db_schema_implemented",
    "question_rn_ui_implemented",
    "question_answer_persistence_implemented",
    "p8_question_implementation_started",
    "p8_question_api_created",
    "p8_question_db_schema_created",
    "p8_question_rn_ui_created",
    "p8_question_trigger_logic_created",
    "p8_question_implementation_spec_finalized_here",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "release_decision_layer_changed",
)
P7_R54_AHR_CR_BODY_FREE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
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
    "packet_content_included",
    "local_path_included",
    "local_absolute_path_included",
    "body_hash_included",
    "terminal_output_body_included",
    "stdout_body_included",
    "stderr_body_included",
    "traceback_body_included",
)
P7_R54_AHR_CR_OPERATION_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "body_full_generation_requested_here",
    "body_full_packet_generation_allowed_here",
    "body_full_packet_generated_here",
    "body_full_packet_exported_here",
    "actual_human_review_run_here",
    "actual_human_review_operation_run",
    "actual_human_review_executed_by_person",
    "actual_human_review_complete",
    "actual_review_evidence_complete",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "p5_human_blind_qa_confirmed_final",
    "p5_confirmed_final",
    "p5_final_allowed",
    "p6_limited_human_readfeel_start_allowed",
    "p6_start_allowed",
    "p8_start_allowed",
    "r52_reintake_execution_requested_here",
    "actual_r52_reintake_execution_confirmed",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_confirmed",
    "rn_contract_green_confirmed",
    "rn_real_device_modal_verified",
)
P7_R54_AHR_CR_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR_NO_TOUCH_FALSE_FLAG_REFS,
    *P7_R54_AHR_CR_BODY_FREE_FALSE_FLAG_REFS,
    *P7_R54_AHR_CR_OPERATION_FALSE_FLAG_REFS,
)

P7_R54_AHR_CR_FORBIDDEN_BODY_OR_QUESTION_KEYS: Final[frozenset[str]] = frozenset(
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

P7_R54_AHR_CR_BASE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
P7_R54_AHR_CR_CURRENT_RECEIVED_BASIS_FIELD_REFS: Final[tuple[str, ...]] = (
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "current_received_snapshot_ref_keys",
    "required_current_received_snapshot_ref_keys",
    "all_required_current_received_snapshot_refs_present",
    "outer_received_zip_refs",
    "outer_received_zip_ref_count",
    "outer_received_zip_ref_keys",
    "outer_received_zip_refs_present",
    "outer_received_zip_refs_are_actual_review_basis",
    "outer_received_zip_refs_used_as_actual_review_basis",
    "current_received_snapshot_refs_are_actual_review_basis",
    "current_received_snapshot_refs_used_as_actual_review_basis",
    "internal_source_lineage_refs",
    "internal_source_lineage_ref_count",
    "internal_source_lineage_refs_separated",
    "outer_received_zip_refs_internal_lineage_same_object",
)
P7_R54_AHR_CR_HISTORICAL_BASIS_FIELD_REFS: Final[tuple[str, ...]] = (
    "historical_ahr_basis_ref",
    "historical_ahr_basis_allowed_ref",
    "historical_ahr_basis_refs",
    "historical_cs_basis_ref",
    "historical_cs_basis_allowed_ref",
    "historical_cs_basis_refs",
    "historical_basis_refs",
    "historical_basis_ref_count",
    "historical_basis_classification_refs",
    "historical_basis_refs_are_structural_or_regression_refs_only",
    "historical_basis_refs_used_as_current_actual_review_basis",
    "historical_basis_refs_used_as_current_actual_review_evidence",
    "historical_helper_green_claimed_as_actual_review_complete",
    "synthetic_contract_rows_used_as_actual_review_rows",
    "existing_ahr_helper_rewritten",
    "existing_cs_helper_rewritten",
    "existing_ahr_cs_helpers_preserved_as_historical_structural_regression_refs",
    "current_basis_does_not_rewrite_existing_ahr_or_cs_helpers",
    "old_260_83_256_169_not_relabelled_as_current",
    "old_262_84_257_170_not_relabelled_as_current",
    "claim_boundary_refs",
)
P7_R54_AHR_CR_NO_TOUCH_MATERIAL_FIELD_REFS: Final[tuple[str, ...]] = (
    "public_contract",
    "r54_ahr_cr_no_touch_contract",
    "body_free_markers",
    "body_free",
)
P7_R54_AHR_CR00_SCOPE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR_BASE_REQUIRED_FIELD_REFS,
    "scope_boundary_confirmed",
    "no_touch_boundary_confirmed",
    "no_touch_boundary_frozen",
    "current_received_actual_local_review_operation_selected",
    "r54_ahr_cr_prefix_used",
    "p7_r54_ahr_line_preserved",
    "cr00_does_not_claim_current_basis_complete",
    "current_basis_refreeze_required_next",
    "current_basis_refrozen_here",
    "current_received_basis_refrozen_for_actual_review_operation",
    *P7_R54_AHR_CR_CURRENT_RECEIVED_BASIS_FIELD_REFS,
    *P7_R54_AHR_CR_HISTORICAL_BASIS_FIELD_REFS,
    "p8_question_design_out_of_scope",
    "p8_question_implementation_out_of_scope",
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
    *P7_R54_AHR_CR_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CR_FALSE_FLAG_REFS,
)
P7_R54_AHR_CR01_CURRENT_RECEIVED_BASIS_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR_BASE_REQUIRED_FIELD_REFS,
    "cr00_schema_version",
    "cr00_material_ref",
    "cr00_next_required_step",
    "cr00_scope_boundary_confirmed",
    "cr00_no_touch_boundary_confirmed",
    "current_basis_status_ref",
    "current_basis_refrozen_here",
    "current_received_basis_refrozen_for_actual_review_operation",
    "current_received_snapshot_refs_match_264_85_258_171",
    "current_264_85_258_171_does_not_claim_actual_review_complete",
    *P7_R54_AHR_CR_CURRENT_RECEIVED_BASIS_FIELD_REFS,
    *P7_R54_AHR_CR_HISTORICAL_BASIS_FIELD_REFS,
    "current_basis_envelope_only",
    "cr01_does_not_create_manifest_packet_review_rows_or_disposal",
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
    *P7_R54_AHR_CR_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CR_FALSE_FLAG_REFS,
)
P7_R54_AHR_CR_SCOPE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CR00_SCOPE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS
)
P7_R54_AHR_CR_CURRENT_RECEIVED_BASIS_ENVELOPE_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CR01_CURRENT_RECEIVED_BASIS_REQUIRED_FIELD_REFS
)

P7_R54_AHR_CR02_HISTORICAL_HELPER_REFS_SEPARATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR_BASE_REQUIRED_FIELD_REFS,
    "cr01_schema_version",
    "cr01_material_ref",
    "cr01_next_required_step",
    "cr01_current_basis_refrozen_here",
    "cr01_current_basis_status_ref",
    *P7_R54_AHR_CR_CURRENT_RECEIVED_BASIS_FIELD_REFS,
    *P7_R54_AHR_CR_HISTORICAL_BASIS_FIELD_REFS,
    "historical_helper_separation_status_ref",
    "historical_helper_refs_separated",
    "historical_helper_ref_groups",
    "historical_helper_ref_group_count",
    "historical_helper_refs",
    "historical_helper_ref_count",
    "historical_helper_role_refs",
    "historical_helper_classification_refs",
    "historical_helper_allowed_usage_refs",
    "historical_helper_prohibited_usage_refs",
    "historical_helper_refs_are_historical_here",
    "historical_helper_refs_are_structural_refs_only",
    "historical_helper_refs_are_regression_refs_only",
    "historical_helper_refs_can_be_used_for_helper_regression_only",
    "historical_helper_refs_can_be_used_for_current_actual_review_basis",
    "historical_helper_refs_used_as_current_actual_review_basis",
    "historical_helper_refs_can_be_used_for_current_actual_review_evidence",
    "historical_helper_refs_used_as_current_actual_review_evidence",
    "existing_ahr_used_as_current_actual_review_evidence",
    "existing_cs_used_as_current_actual_review_evidence",
    "helper_green_not_actual_human_review_complete",
    "synthetic_contract_rows_not_actual_review_rows",
    "separation_does_not_modify_helper_modules",
    "existing_helper_constants_rewritten",
    "existing_helper_refs_preserved_as_received",
    "current_264_85_258_171_remains_only_actual_review_basis",
    "cr02_does_not_execute_direct_diff",
    "cr02_does_not_assess_impact_as_no_impact",
    "cr02_does_not_create_manifest_packet_review_rows_or_disposal",
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
    *P7_R54_AHR_CR_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CR_FALSE_FLAG_REFS,
)
P7_R54_AHR_CR03_BASIS_IMPACT_ASSESSMENT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR_BASE_REQUIRED_FIELD_REFS,
    "cr02_schema_version",
    "cr02_material_ref",
    "cr02_next_required_step",
    "cr02_historical_helper_refs_separated",
    "cr02_historical_helper_refs_used_as_current_actual_review_evidence",
    *P7_R54_AHR_CR_CURRENT_RECEIVED_BASIS_FIELD_REFS,
    *P7_R54_AHR_CR_HISTORICAL_BASIS_FIELD_REFS,
    "basis_impact_assessment_status_ref",
    "basis_impact_assessment_from_ref",
    "basis_impact_assessment_to_ref",
    "historical_helper_refs_separated_before_impact_assessment",
    "basis_impact_assessed_here",
    "impact_target_refs",
    "impact_target_ref_count",
    "direct_file_diff_available",
    "direct_file_diff_executed",
    "direct_file_diff_not_available_reason_ref",
    "diff_impact_status_ref",
    "diff_impact_status_allowed_refs",
    "direct_diff_cannot_claim_no_impact",
    "diff_unavailable_does_not_equal_no_impact",
    "diff_unavailable_no_impact_claimed",
    "impact_summary_refs_bodyfree_only",
    "raw_diff_body_included",
    "body_full_diff_content_included",
    "local_file_path_included",
    "review_manifest_impact_unknown_until_current_manifest_refreeze",
    "current_manifest_refreeze_required",
    "current_manifest_refreeze_required_reason_ref",
    "old_manifest_allowed_as_current_manifest",
    "old_manifest_allowed_as_structural_ref",
    "old_manifest_unconditional_adoption_blocked",
    "old_packet_boundary_allowed_as_current_packet_boundary",
    "old_packet_boundary_unconditional_adoption_blocked",
    "old_evidence_rows_allowed_as_current_actual_review_rows",
    "old_evidence_rows_current_adoption_blocked",
    "current_24_case_manifest_must_be_refrozen_next",
    "current_manifest_refreeze_is_next_step",
    "cr03_does_not_create_manifest_packet_review_rows_or_disposal",
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
    *P7_R54_AHR_CR_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CR_FALSE_FLAG_REFS,
)
P7_R54_AHR_CR_HISTORICAL_HELPER_REFS_SEPARATION_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CR02_HISTORICAL_HELPER_REFS_SEPARATION_REQUIRED_FIELD_REFS
)
P7_R54_AHR_CR_BASIS_IMPACT_ASSESSMENT_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CR03_BASIS_IMPACT_ASSESSMENT_REQUIRED_FIELD_REFS
)
P7_R54_AHR_CR04_CURRENT_24_CASE_MANIFEST_REFREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR_BASE_REQUIRED_FIELD_REFS,
    "cr03_schema_version",
    "cr03_material_ref",
    "cr03_next_required_step",
    "cr03_current_manifest_refreeze_required",
    "cr03_current_24_case_manifest_must_be_refrozen_next",
    "cr03_old_manifest_allowed_as_current_manifest",
    "cr03_old_evidence_rows_allowed_as_current_actual_review_rows",
    *P7_R54_AHR_CR_CURRENT_RECEIVED_BASIS_FIELD_REFS,
    *P7_R54_AHR_CR_HISTORICAL_BASIS_FIELD_REFS,
    "manifest_refreeze_status_ref",
    "manifest_source_kind_ref",
    "manifest_source_basis_ref",
    "current_manifest_refrozen_here",
    "required_case_count",
    "case_distribution",
    "case_distribution_total_count",
    "case_distribution_matches_design",
    "case_role_counts",
    "family_ref_counts",
    "subscription_tier_ref_counts",
    "history_evidence_policy_ref_counts",
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
    "review_axis_profile_ref",
    "rating_axis_refs",
    "rating_axis_count",
    "rating_axis_target_thresholds",
    "reviewer_facing_family_exposed",
    "reviewer_facing_tier_exposed",
    "requires_history_line_review_count",
    "current_only_boundary_case_count",
    "body_full_packet_materialized_here",
    "local_reviewer_payload_materialized_here",
    "old_manifest_adopted_unconditionally",
    "old_packet_boundary_adopted_unconditionally",
    "old_evidence_rows_current_adopted",
    "cr04_does_not_generate_body_full_packet",
    "cr04_does_not_create_local_reviewer_payload",
    "cr04_does_not_execute_actual_human_review",
    "cr04_does_not_create_actual_rating_or_question_rows",
    "cr04_does_not_create_disposal_receipt",
    "body_full_generation_blocked_until_preflight",
    "actual_human_review_completion_claim_blocked_here",
    "actual_rating_or_question_rows_claim_blocked_here",
    "disposal_receipt_claim_blocked_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CR_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CR_FALSE_FLAG_REFS,
)
P7_R54_AHR_CR05_LOCAL_ONLY_PREFLIGHT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR_BASE_REQUIRED_FIELD_REFS,
    "cr04_schema_version",
    "cr04_material_ref",
    "cr04_next_required_step",
    "cr04_current_manifest_refrozen_here",
    "cr04_case_row_count",
    "cr04_case_rows_bodyfree_only",
    "cr04_body_full_packet_materialized_here",
    "cr04_actual_human_review_run_here",
    *P7_R54_AHR_CR_CURRENT_RECEIVED_BASIS_FIELD_REFS,
    *P7_R54_AHR_CR_HISTORICAL_BASIS_FIELD_REFS,
    "preflight_status_ref",
    "preflight_allowed_status_refs",
    "preflight_ready",
    "preflight_reason_refs",
    "preflight_blocker_refs",
    "preflight_blocker_ref_count",
    "local_only",
    "must_not_export",
    "local_review_root_ref",
    "local_review_root_ref_present",
    "explicit_allow_ref",
    "explicit_allow_ref_present",
    "explicit_allow_ref_expected",
    "retention_policy_ref",
    "retention_policy_ref_present",
    "disposal_policy_ref",
    "disposal_policy_ref_present",
    "export_denylist_policy_ref",
    "export_denylist_policy_ref_present",
    "body_full_packet_export_allowed",
    "body_free_summary_export_allowed",
    "body_full_packet_generation_allowed_by_preflight",
    "actual_review_operation_allowed_by_preflight",
    "body_full_packet_generation_started_here",
    "body_full_packet_generated_here",
    "body_full_packet_content_included",
    "body_full_packet_content_exported",
    "body_full_packet_never_export_to_repo_docs_release_public_meta",
    "local_absolute_path_included",
    "body_hash_included",
    "terminal_output_body_included",
    "preflight_ready_all_policy_refs_present",
    "preflight_blocks_without_explicit_allow",
    "preflight_blocks_body_full_export",
    "preflight_does_not_generate_packet_or_review_rows",
    "preflight_does_not_execute_actual_human_review",
    "actual_human_review_completion_claim_blocked_here",
    "actual_rating_or_question_rows_claim_blocked_here",
    "disposal_receipt_claim_blocked_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CR_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CR_FALSE_FLAG_REFS,
)
P7_R54_AHR_CR_CURRENT_24_CASE_MANIFEST_REFREEZE_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CR04_CURRENT_24_CASE_MANIFEST_REFREEZE_REQUIRED_FIELD_REFS
)
P7_R54_AHR_CR_LOCAL_ONLY_PREFLIGHT_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CR05_LOCAL_ONLY_PREFLIGHT_REQUIRED_FIELD_REFS
)
P7_R54_AHR_CR06_PACKET_GENERATION_REQUEST_BRIDGE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR_BASE_REQUIRED_FIELD_REFS,
    "cr05_schema_version",
    "cr05_material_ref",
    "cr05_next_required_step",
    "cr05_preflight_status_ref",
    "cr05_preflight_ready",
    "cr05_preflight_blocker_refs",
    "cr05_body_full_packet_generation_allowed_by_preflight",
    "cr05_actual_review_operation_allowed_by_preflight",
    "cr05_local_only",
    "cr05_must_not_export",
    "cr05_explicit_allow_ref_present",
    "cr05_body_full_packet_export_allowed",
    "cr05_body_full_packet_content_included",
    "cr05_body_full_packet_generated_here",
    "cr05_actual_human_review_run_here",
    *P7_R54_AHR_CR_CURRENT_RECEIVED_BASIS_FIELD_REFS,
    *P7_R54_AHR_CR_HISTORICAL_BASIS_FIELD_REFS,
    "packet_generation_request_bridge_status_ref",
    "packet_generation_request_bridge_allowed_status_refs",
    "packet_generation_request_bridge_ready",
    "packet_generation_request_bridge_reason_refs",
    "packet_generation_request_bridge_blocker_refs",
    "packet_generation_request_bridge_blocker_ref_count",
    "packet_generation_request_ref",
    "packet_generation_request_ref_present",
    "packet_generation_allowed_by_preflight",
    "packet_generation_started_here",
    "body_full_packet_generation_started_here",
    "body_full_packet_generated_here",
    "body_full_packet_content_included",
    "local_absolute_path_included",
    "body_hash_included",
    "terminal_output_body_included",
    "request_bridge_requires_cr05_ready_preflight",
    "request_bridge_does_not_generate_packet_body",
    "request_bridge_does_not_materialize_local_packet",
    "request_bridge_does_not_execute_actual_human_review",
    "request_bridge_does_not_create_review_rows",
    "request_bridge_does_not_create_disposal_receipt",
    "request_bridge_keeps_request_receipt_refs_bodyfree",
    "actual_human_review_completion_claim_blocked_here",
    "actual_rating_or_question_rows_claim_blocked_here",
    "disposal_receipt_claim_blocked_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CR_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CR_FALSE_FLAG_REFS,
)
P7_R54_AHR_CR07_PACKET_GENERATION_RECEIPT_SCAN_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR_BASE_REQUIRED_FIELD_REFS,
    "cr06_schema_version",
    "cr06_material_ref",
    "cr06_next_required_step",
    "cr06_packet_generation_request_bridge_status_ref",
    "cr06_packet_generation_request_bridge_ready",
    "cr06_packet_generation_request_ref",
    "cr06_packet_generation_request_ref_present",
    "cr06_packet_generation_allowed_by_preflight",
    "cr06_packet_generation_started_here",
    "cr06_body_full_packet_generation_started_here",
    "cr06_body_full_packet_generated_here",
    "cr06_body_full_packet_content_included",
    "cr06_local_absolute_path_included",
    "cr06_body_hash_included",
    "cr06_actual_human_review_run_here",
    *P7_R54_AHR_CR_CURRENT_RECEIVED_BASIS_FIELD_REFS,
    *P7_R54_AHR_CR_HISTORICAL_BASIS_FIELD_REFS,
    "packet_generation_receipt_status_ref",
    "packet_generation_receipt_allowed_status_refs",
    "packet_generation_receipt_ready",
    "packet_generation_receipt_reason_refs",
    "packet_generation_receipt_blocker_refs",
    "packet_generation_receipt_blocker_ref_count",
    "packet_generation_receipt_input_provided",
    "receipt_input_forbidden_key_detected",
    "packet_generation_receipt_ref",
    "packet_generation_receipt_ref_present",
    "packet_case_count",
    "packet_case_count_matches_manifest",
    "packet_completeness_scan_ref",
    "packet_completeness_scan_ref_present",
    "packet_completeness_passed",
    "export_denylist_scan_ref",
    "export_denylist_scan_ref_present",
    "export_denylist_scan_passed",
    "packet_completeness_scan_bodyfree_only",
    "export_denylist_scan_bodyfree_only",
    "receipt_does_not_include_packet_body",
    "receipt_does_not_include_local_absolute_path",
    "receipt_does_not_include_body_hash",
    "receipt_does_not_generate_packet_body_here",
    "receipt_does_not_execute_actual_human_review",
    "receipt_does_not_create_review_rows",
    "receipt_does_not_create_disposal_receipt",
    "receipt_is_bodyfree_counts_and_refs_only",
    "body_full_packet_content_included",
    "local_absolute_path_included",
    "body_hash_included",
    "terminal_output_body_included",
    "actual_human_review_completion_claim_blocked_here",
    "actual_rating_or_question_rows_claim_blocked_here",
    "disposal_receipt_claim_blocked_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CR_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CR_FALSE_FLAG_REFS,
)
P7_R54_AHR_CR_PACKET_GENERATION_REQUEST_BRIDGE_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CR06_PACKET_GENERATION_REQUEST_BRIDGE_REQUIRED_FIELD_REFS
)
P7_R54_AHR_CR_PACKET_GENERATION_RECEIPT_SCAN_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CR07_PACKET_GENERATION_RECEIPT_SCAN_REQUIRED_FIELD_REFS
)
P7_R54_AHR_CR08_REVIEWER_SELECTION_FORM_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR_BASE_REQUIRED_FIELD_REFS,
    "cr07_schema_version",
    "cr07_material_ref",
    "cr07_next_required_step",
    "cr07_packet_generation_receipt_status_ref",
    "cr07_packet_generation_receipt_ready",
    "cr07_packet_generation_receipt_ref",
    "cr07_packet_generation_receipt_ref_present",
    "cr07_packet_case_count",
    "cr07_packet_completeness_passed",
    "cr07_export_denylist_scan_passed",
    "cr07_body_full_packet_content_included",
    "cr07_local_absolute_path_included",
    "cr07_body_hash_included",
    "cr07_actual_human_review_run_here",
    *P7_R54_AHR_CR_CURRENT_RECEIVED_BASIS_FIELD_REFS,
    *P7_R54_AHR_CR_HISTORICAL_BASIS_FIELD_REFS,
    "reviewer_selection_form_status_ref",
    "reviewer_selection_form_allowed_status_refs",
    "reviewer_selection_form_ready",
    "reviewer_selection_form_reason_refs",
    "reviewer_selection_form_blocker_refs",
    "reviewer_selection_form_blocker_ref_count",
    "reviewer_person_ref",
    "reviewer_person_ref_present",
    "reviewer_is_person",
    "reviewer_person_confirmed",
    "reviewer_person_boundary_confirmed",
    "reviewer_identity_bodyfree_ref_only",
    "selection_form_status_ref",
    "rating_axis_refs",
    "rating_axis_count",
    "rating_axis_target_thresholds",
    "question_need_primary_class_options",
    "question_need_primary_class_option_count",
    "one_question_fit_option_refs",
    "one_question_fit_option_count",
    "selection_row_count_required",
    "allowed_selection_row_count",
    "selection_only",
    "selection_form_selection_only",
    "free_text_allowed",
    "reviewer_free_text_allowed",
    "reviewer_notes_export_allowed",
    "question_text_allowed",
    "draft_question_text_allowed",
    "selection_form_bodyfree_only",
    "selection_form_does_not_include_body",
    "selection_form_does_not_include_reviewer_free_text",
    "selection_form_does_not_include_question_text",
    "selection_form_does_not_execute_actual_human_review",
    "selection_form_does_not_create_review_rows",
    "selection_form_does_not_create_disposal_receipt",
    "actual_human_review_completion_claim_blocked_here",
    "actual_rating_or_question_rows_claim_blocked_here",
    "disposal_receipt_claim_blocked_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CR_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CR_FALSE_FLAG_REFS,
)
P7_R54_AHR_CR09_ACTUAL_LOCAL_HUMAN_REVIEW_OPERATION_RECEIPT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR_BASE_REQUIRED_FIELD_REFS,
    "cr08_schema_version",
    "cr08_material_ref",
    "cr08_next_required_step",
    "cr08_reviewer_selection_form_status_ref",
    "cr08_reviewer_selection_form_ready",
    "cr08_reviewer_person_ref",
    "cr08_reviewer_person_ref_present",
    "cr08_reviewer_is_person",
    "cr08_reviewer_person_confirmed",
    "cr08_selection_row_count_required",
    "cr08_selection_only",
    "cr08_free_text_allowed",
    "cr08_question_text_allowed",
    *P7_R54_AHR_CR_CURRENT_RECEIVED_BASIS_FIELD_REFS,
    *P7_R54_AHR_CR_HISTORICAL_BASIS_FIELD_REFS,
    "operation_receipt_status_ref",
    "operation_receipt_allowed_status_refs",
    "operation_receipt_ready",
    "operation_receipt_reason_refs",
    "operation_receipt_blocker_refs",
    "operation_receipt_blocker_ref_count",
    "operation_receipt_input_provided",
    "operation_receipt_input_forbidden_key_detected",
    "operation_receipt_ref",
    "operation_receipt_ref_present",
    "reviewer_person_ref",
    "reviewer_person_ref_matches_cr08",
    "reviewer_is_person",
    "reviewer_person_confirmed",
    "reviewer_local_only_read_receipt_present",
    "actual_human_review_executed_by_person",
    "review_started_at_bucket_ref",
    "review_started_at_bucket_ref_present",
    "review_completed_at_bucket_ref",
    "review_completed_at_bucket_ref_present",
    "reviewed_case_count",
    "reviewed_case_count_matches_manifest",
    "selection_row_count",
    "selection_row_count_matches_required",
    "local_only",
    "must_not_export",
    "selection_only",
    "operation_receipt_bodyfree_only",
    "operation_receipt_does_not_include_body",
    "operation_receipt_does_not_include_reviewer_free_text",
    "operation_receipt_does_not_include_question_text",
    "operation_receipt_does_not_include_local_absolute_path",
    "operation_receipt_does_not_include_body_hash",
    "operation_receipt_does_not_include_terminal_output",
    "operation_receipt_does_not_create_rating_rows",
    "operation_receipt_does_not_create_question_rows",
    "operation_receipt_does_not_create_disposal_receipt",
    "actual_human_review_operation_run",
    "actual_human_review_run_here",
    "actual_human_review_completion_claim_blocked_here",
    "actual_review_evidence_still_incomplete_until_rows_and_disposal",
    "actual_rating_or_question_rows_claim_blocked_here",
    "disposal_receipt_claim_blocked_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CR_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CR_FALSE_FLAG_REFS,
)
P7_R54_AHR_CR_REVIEWER_SELECTION_FORM_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CR08_REVIEWER_SELECTION_FORM_REQUIRED_FIELD_REFS
)
P7_R54_AHR_CR_ACTUAL_LOCAL_HUMAN_REVIEW_OPERATION_RECEIPT_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CR09_ACTUAL_LOCAL_HUMAN_REVIEW_OPERATION_RECEIPT_REQUIRED_FIELD_REFS
)
P7_R54_AHR_CR10_SELECTION_RESULT_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "operation_receipt_ref",
    "review_result_row_ref",
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
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
    "selection_only",
    "selection_only_row",
    "body_free",
    *P7_R54_AHR_CR10_ROW_BODYFREE_FALSE_FLAG_REFS,
)
P7_R54_AHR_CR11_RATING_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "rating_row_ref",
    "source_review_result_row_ref",
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
    "axis_scores",
    "axis_targets",
    "axis_score_count",
    "below_target_axis_refs",
    "below_target_axis_ref_count",
    "axis_pass_flags",
    "axis_pass_flag_count",
    "all_axis_scores_at_or_above_target",
    "verdict",
    "sanitized_reason_ids",
    "readfeel_blocker_ids",
    "execution_blocker_ids",
    "question_need_primary_class",
    "one_question_fit_ref",
    "repair_required_refs",
    "plan_candidate_flags",
    "body_free",
    *P7_R54_AHR_CR11_RATING_ROW_BODYFREE_FALSE_FLAG_REFS,
)
P7_R54_AHR_CR10_SANITIZED_SELECTION_ONLY_RESULT_ROWS_INTAKE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR_BASE_REQUIRED_FIELD_REFS,
    "cr09_schema_version",
    "cr09_material_ref",
    "cr09_next_required_step",
    "cr09_operation_receipt_status_ref",
    "cr09_operation_receipt_ready",
    "cr09_operation_receipt_ref",
    "cr09_operation_receipt_ref_present",
    "cr09_reviewer_person_ref",
    "cr09_actual_human_review_executed_by_person",
    "cr09_actual_human_review_run_here",
    "cr09_reviewed_case_count",
    "cr09_selection_row_count",
    "cr09_local_only",
    "cr09_must_not_export",
    "cr09_selection_only",
    *P7_R54_AHR_CR_CURRENT_RECEIVED_BASIS_FIELD_REFS,
    *P7_R54_AHR_CR_HISTORICAL_BASIS_FIELD_REFS,
    "sanitized_selection_only_result_rows_intake_status_ref",
    "sanitized_selection_only_result_rows_allowed_status_refs",
    "sanitized_selection_only_result_rows_ready",
    "sanitized_selection_only_result_rows_reason_refs",
    "sanitized_selection_only_result_rows_blocker_refs",
    "sanitized_selection_only_result_rows_blocker_ref_count",
    "selection_rows_input_provided",
    "selection_rows_input_forbidden_key_detected",
    "required_case_count",
    "received_selection_result_row_count",
    "selection_result_row_count",
    "sanitized_review_result_row_count",
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
    "verdict_counts",
    "question_need_primary_class_counts",
    "rows_match_24_case_manifest",
    "rows_bodyfree_only",
    "rows_selection_only",
    "rows_have_required_axis_scores",
    "rows_have_allowed_verdict_refs",
    "rows_have_allowed_question_observation_refs",
    "rows_have_no_body_or_question_or_path_or_hash",
    "sanitized_selection_only_result_rows_intaken_here",
    "actual_sanitized_review_result_rows_intaken_here",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_review_evidence_complete",
    "rating_row_normalization_allowed_next",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CR_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CR_FALSE_FLAG_REFS,
)
P7_R54_AHR_CR11_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR_BASE_REQUIRED_FIELD_REFS,
    "cr10_schema_version",
    "cr10_material_ref",
    "cr10_next_required_step",
    "cr10_sanitized_selection_only_result_rows_intake_status_ref",
    "cr10_rating_row_normalization_allowed_next",
    "cr10_sanitized_review_result_row_count",
    "cr10_selection_result_row_count",
    "cr10_case_ref_id_count",
    "cr10_actual_human_review_executed_by_person",
    *P7_R54_AHR_CR_CURRENT_RECEIVED_BASIS_FIELD_REFS,
    *P7_R54_AHR_CR_HISTORICAL_BASIS_FIELD_REFS,
    "rating_row_normalization_status_ref",
    "rating_row_normalization_allowed_status_refs",
    "rating_row_normalization_ready",
    "rating_row_normalization_reason_refs",
    "rating_row_normalization_blocker_refs",
    "rating_row_normalization_blocker_ref_count",
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
    "axis_score_count_per_row",
    "rating_axis_target_thresholds",
    "average_axis_scores",
    "average_axis_scores_present",
    "overall_average_axis_score",
    "rating_rows_bodyfree_only",
    "rating_rows_match_sanitized_review_result_case_refs",
    "rating_rows_have_required_axis_scores",
    "rating_scores_in_range",
    "rating_rows_have_allowed_verdict_refs",
    "axis_pass_flags_present_per_row",
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
    "readfeel_execution_blocker_normalization_allowed_next",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CR_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CR_FALSE_FLAG_REFS,
)
P7_R54_AHR_CR_SANITIZED_SELECTION_ONLY_RESULT_ROWS_INTAKE_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CR10_SANITIZED_SELECTION_ONLY_RESULT_ROWS_INTAKE_REQUIRED_FIELD_REFS
)
P7_R54_AHR_CR_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CR11_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS
)


def _safe_review_session_id(value: Any) -> str:
    return clean_identifier(value, default=P7_R54_AHR_CR_DEFAULT_REVIEW_SESSION_ID, max_length=120)


def _false_flags() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_CR_FALSE_FLAG_REFS}


def _no_touch_contract() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_CR_NO_TOUCH_FALSE_FLAG_REFS}


def _body_free_markers() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_CR_BODY_FREE_FALSE_FLAG_REFS}


def _contains_forbidden_body_or_question_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in P7_R54_AHR_CR_FORBIDDEN_BODY_OR_QUESTION_KEYS:
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
    data: Mapping[str, Any],
    *,
    schema_version: str,
    policy_section: str,
    operation_step_ref: str,
    source: str,
    allowed_true_false_flag_refs: tuple[str, ...] = (),
) -> None:
    expected_base = {
        "schema_version": schema_version,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CR_STEP,
        "scope": P7_R54_AHR_CR_SCOPE,
        "policy_kind": P7_R54_AHR_CR_POLICY_KIND,
        "policy_section": policy_section,
        "operation_step_ref": operation_step_ref,
        "current_phase": P7_R54_AHR_CR_CURRENT_PHASE,
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
    allowed_true_flags = set(allowed_true_false_flag_refs)
    for key in P7_R54_AHR_CR_FALSE_FLAG_REFS:
        if key in allowed_true_flags:
            if data.get(key) not in (False, True):
                raise ValueError(f"{source} {key} must be boolean")
            continue
        if data.get(key) is not False:
            raise ValueError(f"{source} {key} must remain false")
    for flag_map_key in ("public_contract", "r54_ahr_cr_no_touch_contract", "body_free_markers"):
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


def _outer_received_zip_refs() -> dict[str, str]:
    return {
        key: P7_R54_AHR_CR_CURRENT_RECEIVED_SNAPSHOT_REFS[key]
        for key in P7_R54_AHR_CR_OUTER_RECEIVED_ZIP_REF_KEYS
    }


def _current_received_basis_fields(*, actual_basis: bool) -> dict[str, Any]:
    return {
        "actual_review_basis_ref": P7_R54_AHR_CR_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_CR_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_received_snapshot_refs": dict(P7_R54_AHR_CR_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R54_AHR_CR_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_keys": list(P7_R54_AHR_CR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS),
        "required_current_received_snapshot_ref_keys": list(P7_R54_AHR_CR_REQUIRED_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS),
        "all_required_current_received_snapshot_refs_present": True,
        "outer_received_zip_refs": _outer_received_zip_refs(),
        "outer_received_zip_ref_count": len(P7_R54_AHR_CR_OUTER_RECEIVED_ZIP_REF_KEYS),
        "outer_received_zip_ref_keys": list(P7_R54_AHR_CR_OUTER_RECEIVED_ZIP_REF_KEYS),
        "outer_received_zip_refs_present": True,
        "outer_received_zip_refs_are_actual_review_basis": actual_basis,
        "outer_received_zip_refs_used_as_actual_review_basis": actual_basis,
        "current_received_snapshot_refs_are_actual_review_basis": actual_basis,
        "current_received_snapshot_refs_used_as_actual_review_basis": actual_basis,
        "internal_source_lineage_refs": dict(P7_R54_AHR_CR_INTERNAL_SOURCE_LINEAGE_REFS),
        "internal_source_lineage_ref_count": len(P7_R54_AHR_CR_INTERNAL_SOURCE_LINEAGE_REFS),
        "internal_source_lineage_refs_separated": True,
        "outer_received_zip_refs_internal_lineage_same_object": False,
    }


def _historical_basis_fields() -> dict[str, Any]:
    return {
        "historical_ahr_basis_ref": P7_R54_AHR_CR_HISTORICAL_AHR_BASIS_REF,
        "historical_ahr_basis_allowed_ref": P7_R54_AHR_CR_HISTORICAL_AHR_BASIS_ALLOWED_REF,
        "historical_ahr_basis_refs": dict(P7_R54_AHR_CR_HISTORICAL_AHR_BASIS_REFS),
        "historical_cs_basis_ref": P7_R54_AHR_CR_HISTORICAL_CS_BASIS_REF,
        "historical_cs_basis_allowed_ref": P7_R54_AHR_CR_HISTORICAL_CS_BASIS_ALLOWED_REF,
        "historical_cs_basis_refs": dict(P7_R54_AHR_CR_HISTORICAL_CS_BASIS_REFS),
        "historical_basis_refs": {key: dict(value) for key, value in P7_R54_AHR_CR_HISTORICAL_BASIS_REFS.items()},
        "historical_basis_ref_count": len(P7_R54_AHR_CR_HISTORICAL_BASIS_REFS),
        "historical_basis_classification_refs": dict(P7_R54_AHR_CR_HISTORICAL_BASIS_CLASSIFICATION_REFS),
        "historical_basis_refs_are_structural_or_regression_refs_only": True,
        "historical_basis_refs_used_as_current_actual_review_basis": False,
        "historical_basis_refs_used_as_current_actual_review_evidence": False,
        "historical_helper_green_claimed_as_actual_review_complete": False,
        "synthetic_contract_rows_used_as_actual_review_rows": False,
        "existing_ahr_helper_rewritten": False,
        "existing_cs_helper_rewritten": False,
        "existing_ahr_cs_helpers_preserved_as_historical_structural_regression_refs": True,
        "current_basis_does_not_rewrite_existing_ahr_or_cs_helpers": True,
        "old_260_83_256_169_not_relabelled_as_current": True,
        "old_262_84_257_170_not_relabelled_as_current": True,
        "claim_boundary_refs": list(P7_R54_AHR_CR_CLAIM_BOUNDARY_REFS),
    }


def _assert_current_received_basis_fields(data: Mapping[str, Any], *, actual_basis: bool, source: str) -> None:
    for key, expected in _current_received_basis_fields(actual_basis=actual_basis).items():
        if data.get(key) != expected:
            raise ValueError(f"{source} {key} changed")
    if tuple(data.get("current_received_snapshot_ref_keys") or ()) != P7_R54_AHR_CR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS:
        raise ValueError(f"{source} current received snapshot ref keys changed")
    if tuple(data.get("required_current_received_snapshot_ref_keys") or ()) != (
        P7_R54_AHR_CR_REQUIRED_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS
    ):
        raise ValueError(f"{source} required current received snapshot ref keys changed")
    if tuple(data.get("outer_received_zip_ref_keys") or ()) != P7_R54_AHR_CR_OUTER_RECEIVED_ZIP_REF_KEYS:
        raise ValueError(f"{source} outer received zip ref keys changed")


def _assert_historical_basis_fields(data: Mapping[str, Any], *, source: str) -> None:
    for key, expected in _historical_basis_fields().items():
        if data.get(key) != expected:
            raise ValueError(f"{source} {key} changed")


def build_p7_r54_ahr_cr00_scope_no_touch_boundary_freeze(*, review_session_id: Any = None) -> dict[str, Any]:
    """Build CR00 body-free scope / no-touch boundary material."""

    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CR00_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CR_STEP,
        "scope": P7_R54_AHR_CR_SCOPE,
        "policy_kind": P7_R54_AHR_CR_POLICY_KIND,
        "policy_section": P7_R54_AHR_CR00_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CR00_STEP_REF,
        "current_phase": P7_R54_AHR_CR_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cr00_scope_no_touch_boundary_freeze_20260628",
        "review_session_id": _safe_review_session_id(review_session_id),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "scope_boundary_confirmed": True,
        "no_touch_boundary_confirmed": True,
        "no_touch_boundary_frozen": True,
        "current_received_actual_local_review_operation_selected": True,
        "r54_ahr_cr_prefix_used": True,
        "p7_r54_ahr_line_preserved": True,
        "cr00_does_not_claim_current_basis_complete": True,
        "current_basis_refreeze_required_next": True,
        "current_basis_refrozen_here": False,
        "current_received_basis_refrozen_for_actual_review_operation": False,
        **_current_received_basis_fields(actual_basis=False),
        **_historical_basis_fields(),
        "p8_question_design_out_of_scope": True,
        "p8_question_implementation_out_of_scope": True,
        "p8_p6_r52_p5_release_out_of_scope": True,
        "api_db_rn_runtime_public_contract_no_touch_boundary_frozen": True,
        "body_full_generation_blocked_until_later_preflight": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_rating_or_question_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "out_of_scope_refs": list(P7_R54_AHR_CR_OUT_OF_SCOPE_REFS),
        "implemented_steps": list(P7_R54_AHR_CR00_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_CR00_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_CR01_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_ahr_cr00_scope_no_touch_boundary_freeze_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CR00_SCOPE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CR00 scope / no-touch boundary freeze",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CR00_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CR00_STEP_REF,
        operation_step_ref=P7_R54_AHR_CR00_STEP_REF,
        source="P7-R54-AHR-CR00 scope / no-touch boundary freeze",
    )
    _assert_current_received_basis_fields(
        data, actual_basis=False, source="P7-R54-AHR-CR00 scope / no-touch boundary freeze"
    )
    _assert_historical_basis_fields(data, source="P7-R54-AHR-CR00 scope / no-touch boundary freeze")
    _assert_true_fields(
        data,
        keys=(
            "scope_boundary_confirmed",
            "no_touch_boundary_confirmed",
            "no_touch_boundary_frozen",
            "current_received_actual_local_review_operation_selected",
            "r54_ahr_cr_prefix_used",
            "p7_r54_ahr_line_preserved",
            "cr00_does_not_claim_current_basis_complete",
            "current_basis_refreeze_required_next",
            "p8_question_design_out_of_scope",
            "p8_question_implementation_out_of_scope",
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
        source="P7-R54-AHR-CR00 scope / no-touch boundary freeze",
    )
    _assert_false_fields(
        data,
        keys=(
            "current_basis_refrozen_here",
            "current_received_basis_refrozen_for_actual_review_operation",
            "outer_received_zip_refs_are_actual_review_basis",
            "outer_received_zip_refs_used_as_actual_review_basis",
            "current_received_snapshot_refs_are_actual_review_basis",
            "current_received_snapshot_refs_used_as_actual_review_basis",
            "actual_human_review_complete",
            "actual_review_evidence_complete",
            "p5_confirmed_final",
            "p6_start_allowed",
            "p8_start_allowed",
            "p7_complete",
            "release_allowed",
        ),
        source="P7-R54-AHR-CR00 scope / no-touch boundary freeze",
    )
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CR00_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CR00 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CR00_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CR00 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R54_AHR_CR01_STEP_REF:
        raise ValueError("P7-R54-AHR-CR00 next required step changed")
    return True


def build_p7_r54_ahr_cr01_current_received_basis_envelope(
    *,
    scope_no_touch_boundary_freeze: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build CR01 body-free current received 264/85/258/171 basis envelope."""

    cr00 = dict(scope_no_touch_boundary_freeze or build_p7_r54_ahr_cr00_scope_no_touch_boundary_freeze())
    assert_p7_r54_ahr_cr00_scope_no_touch_boundary_freeze_contract(cr00)
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CR01_CURRENT_RECEIVED_BASIS_ENVELOPE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CR_STEP,
        "scope": P7_R54_AHR_CR_SCOPE,
        "policy_kind": P7_R54_AHR_CR_POLICY_KIND,
        "policy_section": P7_R54_AHR_CR01_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CR01_STEP_REF,
        "current_phase": P7_R54_AHR_CR_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cr01_current_received_264_85_258_171_basis_envelope_20260628",
        "review_session_id": _safe_review_session_id(review_session_id or cr00.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cr00_schema_version": cr00["schema_version"],
        "cr00_material_ref": cr00["material_id"],
        "cr00_next_required_step": cr00["next_required_step"],
        "cr00_scope_boundary_confirmed": cr00["scope_boundary_confirmed"],
        "cr00_no_touch_boundary_confirmed": cr00["no_touch_boundary_confirmed"],
        "current_basis_status_ref": P7_R54_AHR_CR_CURRENT_BASIS_STATUS_REF,
        "current_basis_refrozen_here": True,
        "current_received_basis_refrozen_for_actual_review_operation": True,
        "current_received_snapshot_refs_match_264_85_258_171": True,
        "current_264_85_258_171_does_not_claim_actual_review_complete": True,
        **_current_received_basis_fields(actual_basis=True),
        **_historical_basis_fields(),
        "current_basis_envelope_only": True,
        "cr01_does_not_create_manifest_packet_review_rows_or_disposal": True,
        "body_full_generation_blocked_until_later_preflight": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_rating_or_question_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR_CR01_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_CR01_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_CR02_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_ahr_cr01_current_received_basis_envelope_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CR01_CURRENT_RECEIVED_BASIS_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CR01 current received 264/85/258/171 basis envelope",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CR01_CURRENT_RECEIVED_BASIS_ENVELOPE_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CR01_STEP_REF,
        operation_step_ref=P7_R54_AHR_CR01_STEP_REF,
        source="P7-R54-AHR-CR01 current received 264/85/258/171 basis envelope",
    )
    if data.get("cr00_schema_version") != P7_R54_AHR_CR00_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CR01 CR00 schema version changed")
    if data.get("cr00_next_required_step") != P7_R54_AHR_CR01_STEP_REF:
        raise ValueError("P7-R54-AHR-CR01 CR00 next required step changed")
    if data.get("cr00_scope_boundary_confirmed") is not True or data.get("cr00_no_touch_boundary_confirmed") is not True:
        raise ValueError("P7-R54-AHR-CR01 CR00 boundary confirmation changed")
    if data.get("current_basis_status_ref") != P7_R54_AHR_CR_CURRENT_BASIS_STATUS_REF:
        raise ValueError("P7-R54-AHR-CR01 current basis status ref changed")
    _assert_current_received_basis_fields(
        data, actual_basis=True, source="P7-R54-AHR-CR01 current received basis envelope"
    )
    _assert_historical_basis_fields(data, source="P7-R54-AHR-CR01 current received basis envelope")
    _assert_true_fields(
        data,
        keys=(
            "current_basis_refrozen_here",
            "current_received_basis_refrozen_for_actual_review_operation",
            "current_received_snapshot_refs_match_264_85_258_171",
            "current_264_85_258_171_does_not_claim_actual_review_complete",
            "outer_received_zip_refs_are_actual_review_basis",
            "outer_received_zip_refs_used_as_actual_review_basis",
            "current_received_snapshot_refs_are_actual_review_basis",
            "current_received_snapshot_refs_used_as_actual_review_basis",
            "current_basis_envelope_only",
            "cr01_does_not_create_manifest_packet_review_rows_or_disposal",
            "body_full_generation_blocked_until_later_preflight",
            "actual_human_review_completion_claim_blocked_here",
            "actual_rating_or_question_rows_claim_blocked_here",
            "disposal_receipt_claim_blocked_here",
            "r52_reintake_claim_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "p5_finalization_blocked_here",
        ),
        source="P7-R54-AHR-CR01 current received basis envelope",
    )
    _assert_false_fields(
        data,
        keys=(
            "historical_basis_refs_used_as_current_actual_review_basis",
            "historical_basis_refs_used_as_current_actual_review_evidence",
            "historical_helper_green_claimed_as_actual_review_complete",
            "synthetic_contract_rows_used_as_actual_review_rows",
            "existing_ahr_helper_rewritten",
            "existing_cs_helper_rewritten",
            "actual_human_review_run_here",
            "actual_human_review_complete",
            "actual_review_evidence_complete",
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "actual_r52_reintake_execution_confirmed",
            "p5_confirmed_final",
            "p5_final_allowed",
            "p6_start_allowed",
            "p8_start_allowed",
            "p7_complete",
            "release_allowed",
        ),
        source="P7-R54-AHR-CR01 current received basis envelope",
    )
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CR01_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CR01 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CR01_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CR01 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R54_AHR_CR02_STEP_REF:
        raise ValueError("P7-R54-AHR-CR01 next required step changed")
    return True


def _assert_historical_helper_separation_fields(data: Mapping[str, Any], *, source: str) -> None:
    if data.get("historical_helper_separation_status_ref") != P7_R54_AHR_CR_HISTORICAL_HELPER_SEPARATION_STATUS_REF:
        raise ValueError(f"{source}: historical helper separation status changed")
    if tuple(data.get("historical_helper_ref_groups") or ()) != P7_R54_AHR_CR_HISTORICAL_HELPER_REF_GROUP_REFS:
        raise ValueError(f"{source}: historical helper groups changed")
    if data.get("historical_helper_ref_group_count") != len(P7_R54_AHR_CR_HISTORICAL_HELPER_REF_GROUP_REFS):
        raise ValueError(f"{source}: historical helper group count changed")
    if data.get("historical_helper_refs") != P7_R54_AHR_CR_HISTORICAL_HELPER_REFS:
        raise ValueError(f"{source}: historical helper refs changed")
    if data.get("historical_helper_ref_count") != len(P7_R54_AHR_CR_HISTORICAL_HELPER_REFS):
        raise ValueError(f"{source}: historical helper ref count changed")
    if data.get("historical_helper_role_refs") != P7_R54_AHR_CR_HISTORICAL_HELPER_ROLE_REFS:
        raise ValueError(f"{source}: historical helper role refs changed")
    if data.get("historical_helper_classification_refs") != P7_R54_AHR_CR_HISTORICAL_HELPER_CLASSIFICATION_REFS:
        raise ValueError(f"{source}: historical helper classification refs changed")
    if tuple(data.get("historical_helper_allowed_usage_refs") or ()) != P7_R54_AHR_CR_HISTORICAL_HELPER_ALLOWED_USAGE_REFS:
        raise ValueError(f"{source}: historical helper allowed usage refs changed")
    if tuple(data.get("historical_helper_prohibited_usage_refs") or ()) != P7_R54_AHR_CR_HISTORICAL_HELPER_PROHIBITED_USAGE_REFS:
        raise ValueError(f"{source}: historical helper prohibited usage refs changed")


def build_p7_r54_ahr_cr02_historical_helper_refs_separation(
    *,
    current_received_basis_envelope: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build CR02 body-free historical helper refs separation material."""

    cr01 = dict(current_received_basis_envelope or build_p7_r54_ahr_cr01_current_received_basis_envelope())
    assert_p7_r54_ahr_cr01_current_received_basis_envelope_contract(cr01)
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CR02_HISTORICAL_HELPER_REFS_SEPARATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CR_STEP,
        "scope": P7_R54_AHR_CR_SCOPE,
        "policy_kind": P7_R54_AHR_CR_POLICY_KIND,
        "policy_section": P7_R54_AHR_CR02_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CR02_STEP_REF,
        "current_phase": P7_R54_AHR_CR_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cr02_historical_helper_refs_separation_20260628",
        "review_session_id": _safe_review_session_id(review_session_id or cr01.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cr01_schema_version": cr01["schema_version"],
        "cr01_material_ref": cr01["material_id"],
        "cr01_next_required_step": cr01["next_required_step"],
        "cr01_current_basis_refrozen_here": cr01["current_basis_refrozen_here"],
        "cr01_current_basis_status_ref": cr01["current_basis_status_ref"],
        **_current_received_basis_fields(actual_basis=True),
        **_historical_basis_fields(),
        "historical_helper_separation_status_ref": P7_R54_AHR_CR_HISTORICAL_HELPER_SEPARATION_STATUS_REF,
        "historical_helper_refs_separated": True,
        "historical_helper_ref_groups": list(P7_R54_AHR_CR_HISTORICAL_HELPER_REF_GROUP_REFS),
        "historical_helper_ref_group_count": len(P7_R54_AHR_CR_HISTORICAL_HELPER_REF_GROUP_REFS),
        "historical_helper_refs": {key: dict(value) for key, value in P7_R54_AHR_CR_HISTORICAL_HELPER_REFS.items()},
        "historical_helper_ref_count": len(P7_R54_AHR_CR_HISTORICAL_HELPER_REFS),
        "historical_helper_role_refs": dict(P7_R54_AHR_CR_HISTORICAL_HELPER_ROLE_REFS),
        "historical_helper_classification_refs": dict(P7_R54_AHR_CR_HISTORICAL_HELPER_CLASSIFICATION_REFS),
        "historical_helper_allowed_usage_refs": list(P7_R54_AHR_CR_HISTORICAL_HELPER_ALLOWED_USAGE_REFS),
        "historical_helper_prohibited_usage_refs": list(P7_R54_AHR_CR_HISTORICAL_HELPER_PROHIBITED_USAGE_REFS),
        "historical_helper_refs_are_historical_here": True,
        "historical_helper_refs_are_structural_refs_only": True,
        "historical_helper_refs_are_regression_refs_only": True,
        "historical_helper_refs_can_be_used_for_helper_regression_only": True,
        "historical_helper_refs_can_be_used_for_current_actual_review_basis": False,
        "historical_helper_refs_used_as_current_actual_review_basis": False,
        "historical_helper_refs_can_be_used_for_current_actual_review_evidence": False,
        "historical_helper_refs_used_as_current_actual_review_evidence": False,
        "existing_ahr_used_as_current_actual_review_evidence": False,
        "existing_cs_used_as_current_actual_review_evidence": False,
        "helper_green_not_actual_human_review_complete": True,
        "synthetic_contract_rows_not_actual_review_rows": True,
        "separation_does_not_modify_helper_modules": True,
        "existing_helper_constants_rewritten": False,
        "existing_helper_refs_preserved_as_received": True,
        "current_264_85_258_171_remains_only_actual_review_basis": True,
        "cr02_does_not_execute_direct_diff": True,
        "cr02_does_not_assess_impact_as_no_impact": True,
        "cr02_does_not_create_manifest_packet_review_rows_or_disposal": True,
        "body_full_generation_blocked_until_later_preflight": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_rating_or_question_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR_CR02_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_CR02_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_CR03_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_ahr_cr02_historical_helper_refs_separation_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CR02_HISTORICAL_HELPER_REFS_SEPARATION_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CR02 historical helper refs separation",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CR02_HISTORICAL_HELPER_REFS_SEPARATION_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CR02_STEP_REF,
        operation_step_ref=P7_R54_AHR_CR02_STEP_REF,
        source="P7-R54-AHR-CR02 historical helper refs separation",
    )
    if data.get("cr01_schema_version") != P7_R54_AHR_CR01_CURRENT_RECEIVED_BASIS_ENVELOPE_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CR02 CR01 schema version changed")
    if data.get("cr01_next_required_step") != P7_R54_AHR_CR02_STEP_REF:
        raise ValueError("P7-R54-AHR-CR02 must follow CR01")
    if data.get("cr01_current_basis_refrozen_here") is not True:
        raise ValueError("P7-R54-AHR-CR02 requires CR01 current basis refreeze")
    if data.get("cr01_current_basis_status_ref") != P7_R54_AHR_CR_CURRENT_BASIS_STATUS_REF:
        raise ValueError("P7-R54-AHR-CR02 current basis status changed")
    _assert_current_received_basis_fields(data, actual_basis=True, source="P7-R54-AHR-CR02 historical helper refs separation")
    _assert_historical_basis_fields(data, source="P7-R54-AHR-CR02 historical helper refs separation")
    _assert_historical_helper_separation_fields(data, source="P7-R54-AHR-CR02 historical helper refs separation")
    _assert_true_fields(
        data,
        keys=(
            "historical_helper_refs_separated",
            "historical_helper_refs_are_historical_here",
            "historical_helper_refs_are_structural_refs_only",
            "historical_helper_refs_are_regression_refs_only",
            "historical_helper_refs_can_be_used_for_helper_regression_only",
            "helper_green_not_actual_human_review_complete",
            "synthetic_contract_rows_not_actual_review_rows",
            "separation_does_not_modify_helper_modules",
            "existing_helper_refs_preserved_as_received",
            "current_264_85_258_171_remains_only_actual_review_basis",
            "cr02_does_not_execute_direct_diff",
            "cr02_does_not_assess_impact_as_no_impact",
            "cr02_does_not_create_manifest_packet_review_rows_or_disposal",
            "body_full_generation_blocked_until_later_preflight",
            "actual_human_review_completion_claim_blocked_here",
            "actual_rating_or_question_rows_claim_blocked_here",
            "disposal_receipt_claim_blocked_here",
            "r52_reintake_claim_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "p5_finalization_blocked_here",
        ),
        source="P7-R54-AHR-CR02 historical helper refs separation",
    )
    _assert_false_fields(
        data,
        keys=(
            "historical_helper_refs_can_be_used_for_current_actual_review_basis",
            "historical_helper_refs_used_as_current_actual_review_basis",
            "historical_helper_refs_can_be_used_for_current_actual_review_evidence",
            "historical_helper_refs_used_as_current_actual_review_evidence",
            "existing_ahr_used_as_current_actual_review_evidence",
            "existing_cs_used_as_current_actual_review_evidence",
            "existing_helper_constants_rewritten",
            "historical_basis_refs_used_as_current_actual_review_basis",
            "historical_basis_refs_used_as_current_actual_review_evidence",
            "historical_helper_green_claimed_as_actual_review_complete",
            "synthetic_contract_rows_used_as_actual_review_rows",
            "existing_ahr_helper_rewritten",
            "existing_cs_helper_rewritten",
            "actual_human_review_run_here",
            "actual_human_review_complete",
            "actual_review_evidence_complete",
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "actual_r52_reintake_execution_confirmed",
            "p5_confirmed_final",
            "p5_final_allowed",
            "p6_start_allowed",
            "p8_start_allowed",
            "p7_complete",
            "release_allowed",
        ),
        source="P7-R54-AHR-CR02 historical helper refs separation",
    )
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CR02_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CR02 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CR02_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CR02 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R54_AHR_CR03_STEP_REF:
        raise ValueError("P7-R54-AHR-CR02 next required step changed")
    return True


def _basis_impact_status_fields(*, direct_diff_available: bool = False, direct_diff_executed: bool = False) -> dict[str, Any]:
    diff_available = bool(direct_diff_available)
    diff_executed = bool(direct_diff_executed and diff_available)
    diff_status_ref = (
        P7_R54_AHR_CR03_DIRECT_DIFF_EXECUTED_RESULT_REF
        if diff_executed
        else P7_R54_AHR_CR03_DIRECT_DIFF_UNAVAILABLE_RESULT_REF
    )
    return {
        "basis_impact_assessment_status_ref": P7_R54_AHR_CR_BASIS_IMPACT_ASSESSMENT_STATUS_REF,
        "basis_impact_assessment_from_ref": P7_R54_AHR_CR_HISTORICAL_CS_BASIS_REF,
        "basis_impact_assessment_to_ref": P7_R54_AHR_CR_ACTUAL_REVIEW_BASIS_REF,
        "historical_helper_refs_separated_before_impact_assessment": True,
        "basis_impact_assessed_here": True,
        "impact_target_refs": list(P7_R54_AHR_CR03_IMPACT_TARGET_REFS),
        "impact_target_ref_count": len(P7_R54_AHR_CR03_IMPACT_TARGET_REFS),
        "direct_file_diff_available": diff_available,
        "direct_file_diff_executed": diff_executed,
        "direct_file_diff_not_available_reason_ref": (
            "" if diff_executed else P7_R54_AHR_CR03_DIRECT_DIFF_UNAVAILABLE_REASON_REF_DEFAULT
        ),
        "diff_impact_status_ref": diff_status_ref,
        "diff_impact_status_allowed_refs": list(P7_R54_AHR_CR03_DIFF_IMPACT_STATUS_REFS),
        "direct_diff_cannot_claim_no_impact": not diff_executed,
        "diff_unavailable_does_not_equal_no_impact": not diff_executed,
        "diff_unavailable_no_impact_claimed": False,
        "impact_summary_refs_bodyfree_only": True,
        "raw_diff_body_included": False,
        "body_full_diff_content_included": False,
        "local_file_path_included": False,
        "review_manifest_impact_unknown_until_current_manifest_refreeze": True,
        "current_manifest_refreeze_required": True,
        "current_manifest_refreeze_required_reason_ref": diff_status_ref,
        "old_manifest_allowed_as_current_manifest": False,
        "old_manifest_allowed_as_structural_ref": True,
        "old_manifest_unconditional_adoption_blocked": True,
        "old_packet_boundary_allowed_as_current_packet_boundary": False,
        "old_packet_boundary_unconditional_adoption_blocked": True,
        "old_evidence_rows_allowed_as_current_actual_review_rows": False,
        "old_evidence_rows_current_adoption_blocked": True,
        "current_24_case_manifest_must_be_refrozen_next": True,
        "current_manifest_refreeze_is_next_step": True,
    }


def build_p7_r54_ahr_cr03_basis_impact_assessment(
    *,
    historical_helper_refs_separation: Mapping[str, Any] | None = None,
    direct_diff_available: bool = False,
    direct_diff_executed: bool = False,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build CR03 body-free basis impact assessment material."""

    cr02 = dict(historical_helper_refs_separation or build_p7_r54_ahr_cr02_historical_helper_refs_separation())
    assert_p7_r54_ahr_cr02_historical_helper_refs_separation_contract(cr02)
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CR03_BASIS_IMPACT_ASSESSMENT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CR_STEP,
        "scope": P7_R54_AHR_CR_SCOPE,
        "policy_kind": P7_R54_AHR_CR_POLICY_KIND,
        "policy_section": P7_R54_AHR_CR03_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CR03_STEP_REF,
        "current_phase": P7_R54_AHR_CR_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cr03_basis_impact_assessment_20260628",
        "review_session_id": _safe_review_session_id(review_session_id or cr02.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cr02_schema_version": cr02["schema_version"],
        "cr02_material_ref": cr02["material_id"],
        "cr02_next_required_step": cr02["next_required_step"],
        "cr02_historical_helper_refs_separated": cr02["historical_helper_refs_separated"],
        "cr02_historical_helper_refs_used_as_current_actual_review_evidence": cr02[
            "historical_helper_refs_used_as_current_actual_review_evidence"
        ],
        **_current_received_basis_fields(actual_basis=True),
        **_historical_basis_fields(),
        **_basis_impact_status_fields(
            direct_diff_available=direct_diff_available,
            direct_diff_executed=direct_diff_executed,
        ),
        "cr03_does_not_create_manifest_packet_review_rows_or_disposal": True,
        "body_full_generation_blocked_until_later_preflight": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_rating_or_question_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR_CR03_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_CR03_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_CR04_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_ahr_cr03_basis_impact_assessment_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CR03_BASIS_IMPACT_ASSESSMENT_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CR03 basis impact assessment",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CR03_BASIS_IMPACT_ASSESSMENT_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CR03_STEP_REF,
        operation_step_ref=P7_R54_AHR_CR03_STEP_REF,
        source="P7-R54-AHR-CR03 basis impact assessment",
    )
    if data.get("cr02_schema_version") != P7_R54_AHR_CR02_HISTORICAL_HELPER_REFS_SEPARATION_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CR03 CR02 schema version changed")
    if data.get("cr02_next_required_step") != P7_R54_AHR_CR03_STEP_REF:
        raise ValueError("P7-R54-AHR-CR03 must follow CR02")
    if data.get("cr02_historical_helper_refs_separated") is not True:
        raise ValueError("P7-R54-AHR-CR03 requires CR02 separation")
    if data.get("cr02_historical_helper_refs_used_as_current_actual_review_evidence") is not False:
        raise ValueError("P7-R54-AHR-CR03 cannot use historical refs as current actual evidence")
    _assert_current_received_basis_fields(data, actual_basis=True, source="P7-R54-AHR-CR03 basis impact assessment")
    _assert_historical_basis_fields(data, source="P7-R54-AHR-CR03 basis impact assessment")
    expected_status_fields = _basis_impact_status_fields(
        direct_diff_available=bool(data.get("direct_file_diff_available")),
        direct_diff_executed=bool(data.get("direct_file_diff_executed")),
    )
    for key, expected in expected_status_fields.items():
        if data.get(key) != expected:
            raise ValueError(f"P7-R54-AHR-CR03 basis impact assessment {key} changed")
    _assert_true_fields(
        data,
        keys=(
            "historical_helper_refs_separated_before_impact_assessment",
            "basis_impact_assessed_here",
            "impact_summary_refs_bodyfree_only",
            "review_manifest_impact_unknown_until_current_manifest_refreeze",
            "current_manifest_refreeze_required",
            "old_manifest_allowed_as_structural_ref",
            "old_manifest_unconditional_adoption_blocked",
            "old_packet_boundary_unconditional_adoption_blocked",
            "old_evidence_rows_current_adoption_blocked",
            "current_24_case_manifest_must_be_refrozen_next",
            "current_manifest_refreeze_is_next_step",
            "cr03_does_not_create_manifest_packet_review_rows_or_disposal",
            "body_full_generation_blocked_until_later_preflight",
            "actual_human_review_completion_claim_blocked_here",
            "actual_rating_or_question_rows_claim_blocked_here",
            "disposal_receipt_claim_blocked_here",
            "r52_reintake_claim_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "p5_finalization_blocked_here",
        ),
        source="P7-R54-AHR-CR03 basis impact assessment",
    )
    _assert_false_fields(
        data,
        keys=(
            "diff_unavailable_no_impact_claimed",
            "raw_diff_body_included",
            "body_full_diff_content_included",
            "local_file_path_included",
            "old_manifest_allowed_as_current_manifest",
            "old_packet_boundary_allowed_as_current_packet_boundary",
            "old_evidence_rows_allowed_as_current_actual_review_rows",
            "historical_basis_refs_used_as_current_actual_review_basis",
            "historical_basis_refs_used_as_current_actual_review_evidence",
            "historical_helper_green_claimed_as_actual_review_complete",
            "synthetic_contract_rows_used_as_actual_review_rows",
            "existing_ahr_helper_rewritten",
            "existing_cs_helper_rewritten",
            "actual_human_review_run_here",
            "actual_human_review_complete",
            "actual_review_evidence_complete",
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "actual_r52_reintake_execution_confirmed",
            "p5_confirmed_final",
            "p5_final_allowed",
            "p6_start_allowed",
            "p8_start_allowed",
            "p7_complete",
            "release_allowed",
        ),
        source="P7-R54-AHR-CR03 basis impact assessment",
    )
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CR03_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CR03 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CR03_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CR03 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R54_AHR_CR04_STEP_REF:
        raise ValueError("P7-R54-AHR-CR03 next required step changed")
    return True


def _cr04_subscription_tier_ref(family_ref: str) -> str:
    if family_ref == "free_tier_history_present_not_allowed":
        return "free_tier_history_present_not_allowed_boundary"
    if family_ref == "low_information_history_not_eligible":
        return "tier_hidden_current_only_boundary"
    return "paid_owned_history_context_ref"


def _cr04_history_evidence_policy_ref(family_ref: str) -> str:
    if family_ref == "free_tier_history_present_not_allowed":
        return "owned_history_present_but_not_allowed_by_tier_boundary"
    if family_ref == "low_information_history_not_eligible":
        return "history_not_eligible_current_only_boundary"
    return "bounded_owned_history_local_only"


def _cr04_default_case_manifest_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = 1
    for family_ref, count in P7_R54_AHR_CR04_CASE_DISTRIBUTION.items():
        case_role_ref = P7_R54_AHR_CR04_CASE_ROLE_BY_FAMILY[family_ref]
        for _ in range(count):
            rows.append(
                {
                    "case_index": index,
                    "case_ref_id": f"cral_case_ref_{index:03d}",
                    "blind_case_id": f"cral_blind_case_{index:03d}",
                    "packet_ref_id": f"cral_packet_ref_{index:03d}",
                    "family_ref": family_ref,
                    "case_role_ref": case_role_ref,
                    "subscription_tier_ref": _cr04_subscription_tier_ref(family_ref),
                    "history_evidence_policy_ref": _cr04_history_evidence_policy_ref(family_ref),
                    "review_axis_profile_ref": P7_R54_AHR_CR04_REVIEW_AXIS_PROFILE_REF,
                    "reviewer_facing_family_exposed": False,
                    "reviewer_facing_tier_exposed": False,
                    "requires_history_line_review": case_role_ref == "positive_history_line",
                    "current_only_boundary_case": case_role_ref == "boundary_no_history_line",
                    "body_full_packet_materialized_here": False,
                    "local_reviewer_payload_materialized_here": False,
                    "body_free": True,
                }
            )
            index += 1
    return rows


def _count_refs(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        ref = str(row.get(key) or "")
        counts[ref] = counts.get(ref, 0) + 1
    return counts


def _assert_cr04_case_manifest_row(row: Mapping[str, Any], *, index: int, source: str) -> None:
    _assert_required_fields(
        row,
        required=P7_R54_AHR_CR04_CASE_ROW_REQUIRED_FIELD_REFS,
        source=f"{source} row {index}",
    )
    if row.get("case_index") != index:
        raise ValueError(f"{source} case index changed at {index}")
    if row.get("case_ref_id") != f"cral_case_ref_{index:03d}":
        raise ValueError(f"{source} case ref changed at {index}")
    if row.get("blind_case_id") != f"cral_blind_case_{index:03d}":
        raise ValueError(f"{source} blind case ref changed at {index}")
    if row.get("packet_ref_id") != f"cral_packet_ref_{index:03d}":
        raise ValueError(f"{source} packet ref changed at {index}")
    family_ref = str(row.get("family_ref") or "")
    if family_ref not in P7_R54_AHR_CR04_CASE_DISTRIBUTION:
        raise ValueError(f"{source} unknown family ref at {index}")
    if row.get("case_role_ref") != P7_R54_AHR_CR04_CASE_ROLE_BY_FAMILY[family_ref]:
        raise ValueError(f"{source} case role changed at {index}")
    if row.get("subscription_tier_ref") != _cr04_subscription_tier_ref(family_ref):
        raise ValueError(f"{source} subscription tier ref changed at {index}")
    if row.get("history_evidence_policy_ref") != _cr04_history_evidence_policy_ref(family_ref):
        raise ValueError(f"{source} history evidence policy changed at {index}")
    if row.get("review_axis_profile_ref") != P7_R54_AHR_CR04_REVIEW_AXIS_PROFILE_REF:
        raise ValueError(f"{source} review axis profile changed at {index}")
    expected_positive = row.get("case_role_ref") == "positive_history_line"
    expected_boundary = row.get("case_role_ref") == "boundary_no_history_line"
    if row.get("requires_history_line_review") is not expected_positive:
        raise ValueError(f"{source} requires_history_line_review changed at {index}")
    if row.get("current_only_boundary_case") is not expected_boundary:
        raise ValueError(f"{source} current_only_boundary_case changed at {index}")
    for key in (
        "reviewer_facing_family_exposed",
        "reviewer_facing_tier_exposed",
        "body_full_packet_materialized_here",
        "local_reviewer_payload_materialized_here",
    ):
        if row.get(key) is not False:
            raise ValueError(f"{source} {key} must remain false at {index}")
    if row.get("body_free") is not True:
        raise ValueError(f"{source} row {index} must remain body-free")
    if _contains_forbidden_body_or_question_key(row):
        raise ValueError(f"{source} row {index} contains forbidden body/question/path/hash key")


def _cr05_preflight_fields(
    *,
    local_only: bool,
    must_not_export: bool,
    local_review_root_ref: Any,
    explicit_allow_ref: Any,
    retention_policy_ref: Any,
    disposal_policy_ref: Any,
    export_denylist_policy_ref: Any,
    body_full_packet_export_allowed: bool,
) -> dict[str, Any]:
    local_root = (
        P7_R54_AHR_CR05_DEFAULT_LOCAL_REVIEW_ROOT_REF
        if local_review_root_ref is None
        else clean_identifier(local_review_root_ref, default="", max_length=160)
    )
    explicit_allow = clean_identifier(explicit_allow_ref, default="", max_length=180)
    retention = (
        P7_R54_AHR_CR05_DEFAULT_RETENTION_POLICY_REF
        if retention_policy_ref is None
        else clean_identifier(retention_policy_ref, default="", max_length=180)
    )
    disposal = (
        P7_R54_AHR_CR05_DEFAULT_DISPOSAL_POLICY_REF
        if disposal_policy_ref is None
        else clean_identifier(disposal_policy_ref, default="", max_length=180)
    )
    export_denylist = (
        P7_R54_AHR_CR05_DEFAULT_EXPORT_DENYLIST_POLICY_REF
        if export_denylist_policy_ref is None
        else clean_identifier(export_denylist_policy_ref, default="", max_length=220)
    )
    blockers: list[str] = []
    if not local_only:
        blockers.append(P7_R54_AHR_CR05_LOCAL_ONLY_FALSE_BLOCKER_REF)
    if not must_not_export:
        blockers.append(P7_R54_AHR_CR05_MUST_NOT_EXPORT_FALSE_BLOCKER_REF)
    if not local_root:
        blockers.append(P7_R54_AHR_CR05_LOCAL_REVIEW_ROOT_MISSING_BLOCKER_REF)
    if not explicit_allow:
        blockers.append(P7_R54_AHR_CR05_EXPLICIT_ALLOW_MISSING_BLOCKER_REF)
    if not retention:
        blockers.append(P7_R54_AHR_CR05_RETENTION_POLICY_MISSING_BLOCKER_REF)
    if not disposal:
        blockers.append(P7_R54_AHR_CR05_DISPOSAL_POLICY_MISSING_BLOCKER_REF)
    if not export_denylist:
        blockers.append(P7_R54_AHR_CR05_EXPORT_DENYLIST_POLICY_MISSING_BLOCKER_REF)
    if body_full_packet_export_allowed:
        blockers.append(P7_R54_AHR_CR05_BODYFULL_EXPORT_ALLOWED_BLOCKER_REF)
    # Keep deterministic order while removing accidental duplicates.
    deduped_blockers: list[str] = []
    seen: set[str] = set()
    for blocker in blockers:
        if blocker not in seen:
            deduped_blockers.append(blocker)
            seen.add(blocker)
    ready = not deduped_blockers
    return {
        "preflight_status_ref": (
            P7_R54_AHR_CR05_PREFLIGHT_READY_STATUS_REF if ready else P7_R54_AHR_CR05_PREFLIGHT_BLOCKED_STATUS_REF
        ),
        "preflight_allowed_status_refs": list(P7_R54_AHR_CR05_ALLOWED_PREFLIGHT_STATUS_REFS),
        "preflight_ready": ready,
        "preflight_reason_refs": [P7_R54_AHR_CR05_READY_REASON_REF] if ready else [],
        "preflight_blocker_refs": deduped_blockers,
        "preflight_blocker_ref_count": len(deduped_blockers),
        "local_only": bool(local_only),
        "must_not_export": bool(must_not_export),
        "local_review_root_ref": local_root,
        "local_review_root_ref_present": bool(local_root),
        "explicit_allow_ref": explicit_allow,
        "explicit_allow_ref_present": bool(explicit_allow),
        "explicit_allow_ref_expected": P7_R54_AHR_CR05_DEFAULT_EXPLICIT_ALLOW_REF,
        "retention_policy_ref": retention,
        "retention_policy_ref_present": bool(retention),
        "disposal_policy_ref": disposal,
        "disposal_policy_ref_present": bool(disposal),
        "export_denylist_policy_ref": export_denylist,
        "export_denylist_policy_ref_present": bool(export_denylist),
        "body_full_packet_export_allowed": bool(body_full_packet_export_allowed),
        "body_free_summary_export_allowed": True,
        "body_full_packet_generation_allowed_by_preflight": ready,
        "actual_review_operation_allowed_by_preflight": ready,
        "body_full_packet_generation_started_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packet_content_included": False,
        "body_full_packet_content_exported": False,
        "body_full_packet_never_export_to_repo_docs_release_public_meta": True,
        "local_absolute_path_included": False,
        "body_hash_included": False,
        "terminal_output_body_included": False,
        "preflight_ready_all_policy_refs_present": ready,
        "preflight_blocks_without_explicit_allow": not bool(explicit_allow),
        "preflight_blocks_body_full_export": True,
    }


def build_p7_r54_ahr_cr04_current_24_case_manifest_refreeze(
    *,
    basis_impact_assessment: Mapping[str, Any] | None = None,
    case_rows: Sequence[Mapping[str, Any]] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build CR04 current received 24-case manifest refreeze material."""

    cr03 = dict(basis_impact_assessment or build_p7_r54_ahr_cr03_basis_impact_assessment())
    assert_p7_r54_ahr_cr03_basis_impact_assessment_contract(cr03)
    rows = [dict(row) for row in (case_rows if case_rows is not None else _cr04_default_case_manifest_rows())]
    case_refs = [str(row.get("case_ref_id") or "") for row in rows]
    blind_ids = [str(row.get("blind_case_id") or "") for row in rows]
    packet_refs = [str(row.get("packet_ref_id") or "") for row in rows]
    family_counts = _count_refs(rows, "family_ref")
    case_role_counts = _count_refs(rows, "case_role_ref")
    tier_counts = _count_refs(rows, "subscription_tier_ref")
    history_policy_counts = _count_refs(rows, "history_evidence_policy_ref")
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CR04_CURRENT_24_CASE_MANIFEST_REFREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CR_STEP,
        "scope": P7_R54_AHR_CR_SCOPE,
        "policy_kind": P7_R54_AHR_CR_POLICY_KIND,
        "policy_section": P7_R54_AHR_CR04_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CR04_STEP_REF,
        "current_phase": P7_R54_AHR_CR_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cr04_current_24_case_manifest_refreeze_20260628",
        "review_session_id": _safe_review_session_id(review_session_id or cr03.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cr03_schema_version": cr03["schema_version"],
        "cr03_material_ref": cr03["material_id"],
        "cr03_next_required_step": cr03["next_required_step"],
        "cr03_current_manifest_refreeze_required": cr03["current_manifest_refreeze_required"],
        "cr03_current_24_case_manifest_must_be_refrozen_next": cr03[
            "current_24_case_manifest_must_be_refrozen_next"
        ],
        "cr03_old_manifest_allowed_as_current_manifest": cr03["old_manifest_allowed_as_current_manifest"],
        "cr03_old_evidence_rows_allowed_as_current_actual_review_rows": cr03[
            "old_evidence_rows_allowed_as_current_actual_review_rows"
        ],
        **_current_received_basis_fields(actual_basis=True),
        **_historical_basis_fields(),
        "manifest_refreeze_status_ref": P7_R54_AHR_CR04_MANIFEST_REFREEZE_STATUS_REF,
        "manifest_source_kind_ref": P7_R54_AHR_CR04_MANIFEST_SOURCE_KIND_REF,
        "manifest_source_basis_ref": P7_R54_AHR_CR_ACTUAL_REVIEW_BASIS_REF,
        "current_manifest_refrozen_here": True,
        "required_case_count": P7_R54_AHR_CR_REQUIRED_CASE_COUNT,
        "case_distribution": dict(P7_R54_AHR_CR04_CASE_DISTRIBUTION),
        "case_distribution_total_count": sum(P7_R54_AHR_CR04_CASE_DISTRIBUTION.values()),
        "case_distribution_matches_design": family_counts == P7_R54_AHR_CR04_CASE_DISTRIBUTION,
        "case_role_counts": case_role_counts,
        "family_ref_counts": family_counts,
        "subscription_tier_ref_counts": tier_counts,
        "history_evidence_policy_ref_counts": history_policy_counts,
        "case_rows": rows,
        "case_row_count": len(rows),
        "case_rows_bodyfree_only": True,
        "case_ref_ids": case_refs,
        "case_ref_id_count": len(case_refs),
        "case_ref_ids_unique": len(set(case_refs)) == len(case_refs),
        "blind_case_ids": blind_ids,
        "blind_case_id_count": len(blind_ids),
        "blind_case_ids_unique": len(set(blind_ids)) == len(blind_ids),
        "packet_ref_ids": packet_refs,
        "packet_ref_id_count": len(packet_refs),
        "packet_ref_ids_unique": len(set(packet_refs)) == len(packet_refs),
        "blind_case_id_case_ref_separated": not set(blind_ids).intersection(case_refs),
        "blind_case_id_packet_ref_separated": not set(blind_ids).intersection(packet_refs),
        "case_ref_id_packet_ref_separated": not set(case_refs).intersection(packet_refs),
        "review_axis_profile_ref": P7_R54_AHR_CR04_REVIEW_AXIS_PROFILE_REF,
        "rating_axis_refs": list(P7_R54_AHR_CR04_RATING_AXIS_REFS),
        "rating_axis_count": len(P7_R54_AHR_CR04_RATING_AXIS_REFS),
        "rating_axis_target_thresholds": dict(P7_R54_AHR_CR04_RATING_AXIS_TARGET_THRESHOLDS),
        "reviewer_facing_family_exposed": False,
        "reviewer_facing_tier_exposed": False,
        "requires_history_line_review_count": sum(
            1 for row in rows if row.get("requires_history_line_review") is True
        ),
        "current_only_boundary_case_count": sum(1 for row in rows if row.get("current_only_boundary_case") is True),
        "body_full_packet_materialized_here": False,
        "local_reviewer_payload_materialized_here": False,
        "old_manifest_adopted_unconditionally": False,
        "old_packet_boundary_adopted_unconditionally": False,
        "old_evidence_rows_current_adopted": False,
        "cr04_does_not_generate_body_full_packet": True,
        "cr04_does_not_create_local_reviewer_payload": True,
        "cr04_does_not_execute_actual_human_review": True,
        "cr04_does_not_create_actual_rating_or_question_rows": True,
        "cr04_does_not_create_disposal_receipt": True,
        "body_full_generation_blocked_until_preflight": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_rating_or_question_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR_CR04_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_CR04_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_CR05_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_ahr_cr04_current_24_case_manifest_refreeze_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CR04_CURRENT_24_CASE_MANIFEST_REFREEZE_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CR04 current 24-case manifest refreeze",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CR04_CURRENT_24_CASE_MANIFEST_REFREEZE_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CR04_STEP_REF,
        operation_step_ref=P7_R54_AHR_CR04_STEP_REF,
        source="P7-R54-AHR-CR04 current 24-case manifest refreeze",
    )
    if data.get("cr03_schema_version") != P7_R54_AHR_CR03_BASIS_IMPACT_ASSESSMENT_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CR04 CR03 schema version changed")
    if data.get("cr03_next_required_step") != P7_R54_AHR_CR04_STEP_REF:
        raise ValueError("P7-R54-AHR-CR04 must follow CR03")
    if data.get("cr03_current_manifest_refreeze_required") is not True:
        raise ValueError("P7-R54-AHR-CR04 requires CR03 manifest refreeze flag")
    if data.get("cr03_current_24_case_manifest_must_be_refrozen_next") is not True:
        raise ValueError("P7-R54-AHR-CR04 requires CR03 current manifest next flag")
    if data.get("cr03_old_manifest_allowed_as_current_manifest") is not False:
        raise ValueError("P7-R54-AHR-CR04 cannot adopt old manifest as current")
    if data.get("cr03_old_evidence_rows_allowed_as_current_actual_review_rows") is not False:
        raise ValueError("P7-R54-AHR-CR04 cannot adopt old evidence rows as current actual rows")
    _assert_current_received_basis_fields(
        data, actual_basis=True, source="P7-R54-AHR-CR04 current 24-case manifest refreeze"
    )
    _assert_historical_basis_fields(data, source="P7-R54-AHR-CR04 current 24-case manifest refreeze")
    if data.get("manifest_refreeze_status_ref") != P7_R54_AHR_CR04_MANIFEST_REFREEZE_STATUS_REF:
        raise ValueError("P7-R54-AHR-CR04 manifest refreeze status changed")
    if data.get("manifest_source_kind_ref") != P7_R54_AHR_CR04_MANIFEST_SOURCE_KIND_REF:
        raise ValueError("P7-R54-AHR-CR04 manifest source kind changed")
    if data.get("manifest_source_basis_ref") != P7_R54_AHR_CR_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-CR04 source basis changed")
    if data.get("current_manifest_refrozen_here") is not True:
        raise ValueError("P7-R54-AHR-CR04 manifest must be refrozen here")
    if data.get("required_case_count") != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
        raise ValueError("P7-R54-AHR-CR04 required case count changed")
    if data.get("case_distribution") != P7_R54_AHR_CR04_CASE_DISTRIBUTION:
        raise ValueError("P7-R54-AHR-CR04 case distribution changed")
    if data.get("case_distribution_total_count") != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
        raise ValueError("P7-R54-AHR-CR04 case distribution total changed")
    rows = data.get("case_rows")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)):
        raise ValueError("P7-R54-AHR-CR04 rows must be a sequence")
    row_mappings = [dict(row) for row in rows if isinstance(row, Mapping)]
    if len(row_mappings) != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
        raise ValueError("P7-R54-AHR-CR04 requires 24 manifest rows")
    for index, row in enumerate(row_mappings, start=1):
        _assert_cr04_case_manifest_row(
            row, index=index, source="P7-R54-AHR-CR04 current 24-case manifest refreeze"
        )
    case_refs = [row["case_ref_id"] for row in row_mappings]
    blind_ids = [row["blind_case_id"] for row in row_mappings]
    packet_refs = [row["packet_ref_id"] for row in row_mappings]
    if data.get("case_row_count") != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
        raise ValueError("P7-R54-AHR-CR04 case row count changed")
    if data.get("case_rows_bodyfree_only") is not True:
        raise ValueError("P7-R54-AHR-CR04 rows must remain body-free only")
    expected_family_counts = _count_refs(row_mappings, "family_ref")
    if expected_family_counts != P7_R54_AHR_CR04_CASE_DISTRIBUTION:
        raise ValueError("P7-R54-AHR-CR04 family distribution changed")
    expected_fields = {
        "family_ref_counts": expected_family_counts,
        "case_role_counts": _count_refs(row_mappings, "case_role_ref"),
        "subscription_tier_ref_counts": _count_refs(row_mappings, "subscription_tier_ref"),
        "history_evidence_policy_ref_counts": _count_refs(row_mappings, "history_evidence_policy_ref"),
        "case_ref_ids": case_refs,
        "case_ref_id_count": len(case_refs),
        "case_ref_ids_unique": len(set(case_refs)) == len(case_refs),
        "blind_case_ids": blind_ids,
        "blind_case_id_count": len(blind_ids),
        "blind_case_ids_unique": len(set(blind_ids)) == len(blind_ids),
        "packet_ref_ids": packet_refs,
        "packet_ref_id_count": len(packet_refs),
        "packet_ref_ids_unique": len(set(packet_refs)) == len(packet_refs),
        "blind_case_id_case_ref_separated": not set(blind_ids).intersection(case_refs),
        "blind_case_id_packet_ref_separated": not set(blind_ids).intersection(packet_refs),
        "case_ref_id_packet_ref_separated": not set(case_refs).intersection(packet_refs),
        "requires_history_line_review_count": sum(
            1 for row in row_mappings if row.get("requires_history_line_review") is True
        ),
        "current_only_boundary_case_count": sum(
            1 for row in row_mappings if row.get("current_only_boundary_case") is True
        ),
    }
    for key, expected in expected_fields.items():
        if data.get(key) != expected:
            raise ValueError(f"P7-R54-AHR-CR04 {key} changed")
    if data.get("case_distribution_matches_design") is not True:
        raise ValueError("P7-R54-AHR-CR04 case distribution must match design")
    if data.get("review_axis_profile_ref") != P7_R54_AHR_CR04_REVIEW_AXIS_PROFILE_REF:
        raise ValueError("P7-R54-AHR-CR04 review axis profile changed")
    if tuple(data.get("rating_axis_refs") or ()) != P7_R54_AHR_CR04_RATING_AXIS_REFS:
        raise ValueError("P7-R54-AHR-CR04 rating axis refs changed")
    if data.get("rating_axis_count") != len(P7_R54_AHR_CR04_RATING_AXIS_REFS):
        raise ValueError("P7-R54-AHR-CR04 rating axis count changed")
    if data.get("rating_axis_target_thresholds") != P7_R54_AHR_CR04_RATING_AXIS_TARGET_THRESHOLDS:
        raise ValueError("P7-R54-AHR-CR04 rating axis thresholds changed")
    _assert_true_fields(
        data,
        keys=(
            "cr04_does_not_generate_body_full_packet",
            "cr04_does_not_create_local_reviewer_payload",
            "cr04_does_not_execute_actual_human_review",
            "cr04_does_not_create_actual_rating_or_question_rows",
            "cr04_does_not_create_disposal_receipt",
            "body_full_generation_blocked_until_preflight",
            "actual_human_review_completion_claim_blocked_here",
            "actual_rating_or_question_rows_claim_blocked_here",
            "disposal_receipt_claim_blocked_here",
            "r52_reintake_claim_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "p5_finalization_blocked_here",
        ),
        source="P7-R54-AHR-CR04 current 24-case manifest refreeze",
    )
    _assert_false_fields(
        data,
        keys=(
            "reviewer_facing_family_exposed",
            "reviewer_facing_tier_exposed",
            "body_full_packet_materialized_here",
            "local_reviewer_payload_materialized_here",
            "old_manifest_adopted_unconditionally",
            "old_packet_boundary_adopted_unconditionally",
            "old_evidence_rows_current_adopted",
            "actual_human_review_run_here",
            "actual_human_review_complete",
            "actual_review_evidence_complete",
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "p5_confirmed_final",
            "p6_start_allowed",
            "p8_start_allowed",
            "release_allowed",
        ),
        source="P7-R54-AHR-CR04 current 24-case manifest refreeze",
    )
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CR04_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CR04 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CR04_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CR04 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R54_AHR_CR05_STEP_REF:
        raise ValueError("P7-R54-AHR-CR04 next required step changed")
    return True


def build_p7_r54_ahr_cr05_local_only_preflight(
    *,
    current_24_case_manifest_refreeze: Mapping[str, Any] | None = None,
    local_only: bool = True,
    must_not_export: bool = True,
    local_review_root_ref: Any = P7_R54_AHR_CR05_DEFAULT_LOCAL_REVIEW_ROOT_REF,
    explicit_allow_ref: Any = "",
    retention_policy_ref: Any = P7_R54_AHR_CR05_DEFAULT_RETENTION_POLICY_REF,
    disposal_policy_ref: Any = P7_R54_AHR_CR05_DEFAULT_DISPOSAL_POLICY_REF,
    export_denylist_policy_ref: Any = P7_R54_AHR_CR05_DEFAULT_EXPORT_DENYLIST_POLICY_REF,
    body_full_packet_export_allowed: bool = False,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build CR05 local-only preflight / explicit allow / retention material."""

    cr04 = dict(current_24_case_manifest_refreeze or build_p7_r54_ahr_cr04_current_24_case_manifest_refreeze())
    assert_p7_r54_ahr_cr04_current_24_case_manifest_refreeze_contract(cr04)
    preflight_fields = _cr05_preflight_fields(
        local_only=local_only,
        must_not_export=must_not_export,
        local_review_root_ref=local_review_root_ref,
        explicit_allow_ref=explicit_allow_ref,
        retention_policy_ref=retention_policy_ref,
        disposal_policy_ref=disposal_policy_ref,
        export_denylist_policy_ref=export_denylist_policy_ref,
        body_full_packet_export_allowed=body_full_packet_export_allowed,
    )
    ready = preflight_fields["preflight_ready"] is True
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CR05_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CR_STEP,
        "scope": P7_R54_AHR_CR_SCOPE,
        "policy_kind": P7_R54_AHR_CR_POLICY_KIND,
        "policy_section": P7_R54_AHR_CR05_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CR05_STEP_REF,
        "current_phase": P7_R54_AHR_CR_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cr05_local_only_preflight_explicit_allow_retention_20260628",
        "review_session_id": _safe_review_session_id(review_session_id or cr04.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cr04_schema_version": cr04["schema_version"],
        "cr04_material_ref": cr04["material_id"],
        "cr04_next_required_step": cr04["next_required_step"],
        "cr04_current_manifest_refrozen_here": cr04["current_manifest_refrozen_here"],
        "cr04_case_row_count": cr04["case_row_count"],
        "cr04_case_rows_bodyfree_only": cr04["case_rows_bodyfree_only"],
        "cr04_body_full_packet_materialized_here": cr04["body_full_packet_materialized_here"],
        "cr04_actual_human_review_run_here": cr04["actual_human_review_run_here"],
        **_current_received_basis_fields(actual_basis=True),
        **_historical_basis_fields(),
        **preflight_fields,
        "preflight_does_not_generate_packet_or_review_rows": True,
        "preflight_does_not_execute_actual_human_review": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_rating_or_question_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR_CR05_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_CR05_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": (
            P7_R54_AHR_CR06_STEP_REF if ready else P7_R54_AHR_CR05_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
        ),
        "public_contract": public_contract_flags(),
        "r54_ahr_cr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    # Re-apply CR05-specific false indicators after the shared false flags, so
    # required fields stay explicit and body-free while operation flags remain false.
    material["body_full_packet_content_included"] = False
    material["local_absolute_path_included"] = False
    material["body_hash_included"] = False
    material["terminal_output_body_included"] = False
    return material


def assert_p7_r54_ahr_cr05_local_only_preflight_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CR05_LOCAL_ONLY_PREFLIGHT_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CR05 local-only preflight",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CR05_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CR05_STEP_REF,
        operation_step_ref=P7_R54_AHR_CR05_STEP_REF,
        source="P7-R54-AHR-CR05 local-only preflight",
    )
    if data.get("cr04_schema_version") != P7_R54_AHR_CR04_CURRENT_24_CASE_MANIFEST_REFREEZE_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CR05 CR04 schema version changed")
    if data.get("cr04_next_required_step") != P7_R54_AHR_CR05_STEP_REF:
        raise ValueError("P7-R54-AHR-CR05 must follow CR04")
    if data.get("cr04_current_manifest_refrozen_here") is not True:
        raise ValueError("P7-R54-AHR-CR05 requires CR04 manifest refreeze")
    if data.get("cr04_case_row_count") != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
        raise ValueError("P7-R54-AHR-CR05 requires CR04 24 cases")
    if data.get("cr04_case_rows_bodyfree_only") is not True:
        raise ValueError("P7-R54-AHR-CR05 requires body-free CR04 rows")
    if data.get("cr04_body_full_packet_materialized_here") is not False:
        raise ValueError("P7-R54-AHR-CR05 cannot follow materialized packet at CR04")
    if data.get("cr04_actual_human_review_run_here") is not False:
        raise ValueError("P7-R54-AHR-CR05 cannot follow actual review execution at CR04")
    _assert_current_received_basis_fields(data, actual_basis=True, source="P7-R54-AHR-CR05 local-only preflight")
    _assert_historical_basis_fields(data, source="P7-R54-AHR-CR05 local-only preflight")
    if tuple(data.get("preflight_allowed_status_refs") or ()) != P7_R54_AHR_CR05_ALLOWED_PREFLIGHT_STATUS_REFS:
        raise ValueError("P7-R54-AHR-CR05 allowed status refs changed")
    status = data.get("preflight_status_ref")
    if status not in P7_R54_AHR_CR05_ALLOWED_PREFLIGHT_STATUS_REFS:
        raise ValueError("P7-R54-AHR-CR05 status ref changed")
    blockers = list(data.get("preflight_blocker_refs") or [])
    if data.get("preflight_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-CR05 blocker count changed")
    ready = status == P7_R54_AHR_CR05_PREFLIGHT_READY_STATUS_REF
    if data.get("preflight_ready") is not ready:
        raise ValueError("P7-R54-AHR-CR05 preflight ready flag changed")
    if ready:
        if blockers:
            raise ValueError("P7-R54-AHR-CR05 ready preflight cannot have blockers")
        if data.get("preflight_reason_refs") != [P7_R54_AHR_CR05_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-CR05 ready reason changed")
        if data.get("body_full_packet_generation_allowed_by_preflight") is not True:
            raise ValueError("P7-R54-AHR-CR05 ready preflight must allow later packet request consideration")
        if data.get("actual_review_operation_allowed_by_preflight") is not True:
            raise ValueError("P7-R54-AHR-CR05 ready preflight must allow later operation consideration")
        if data.get("next_required_step") != P7_R54_AHR_CR06_STEP_REF:
            raise ValueError("P7-R54-AHR-CR05 ready next step changed")
    else:
        if not blockers:
            raise ValueError("P7-R54-AHR-CR05 blocked preflight must carry blockers")
        if data.get("preflight_reason_refs") != []:
            raise ValueError("P7-R54-AHR-CR05 blocked preflight cannot carry ready reasons")
        if data.get("body_full_packet_generation_allowed_by_preflight") is not False:
            raise ValueError("P7-R54-AHR-CR05 blocked preflight cannot allow packet generation")
        if data.get("actual_review_operation_allowed_by_preflight") is not False:
            raise ValueError("P7-R54-AHR-CR05 blocked preflight cannot allow actual review operation")
        if data.get("next_required_step") != P7_R54_AHR_CR05_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CR05 blocked next step changed")
    expected_preflight = _cr05_preflight_fields(
        local_only=bool(data.get("local_only")),
        must_not_export=bool(data.get("must_not_export")),
        local_review_root_ref=data.get("local_review_root_ref"),
        explicit_allow_ref=data.get("explicit_allow_ref"),
        retention_policy_ref=data.get("retention_policy_ref"),
        disposal_policy_ref=data.get("disposal_policy_ref"),
        export_denylist_policy_ref=data.get("export_denylist_policy_ref"),
        body_full_packet_export_allowed=bool(data.get("body_full_packet_export_allowed")),
    )
    for key, expected in expected_preflight.items():
        if data.get(key) != expected:
            raise ValueError(f"P7-R54-AHR-CR05 {key} changed")
    _assert_true_fields(
        data,
        keys=(
            "body_free_summary_export_allowed",
            "body_full_packet_never_export_to_repo_docs_release_public_meta",
            "preflight_blocks_body_full_export",
            "preflight_does_not_generate_packet_or_review_rows",
            "preflight_does_not_execute_actual_human_review",
            "actual_human_review_completion_claim_blocked_here",
            "actual_rating_or_question_rows_claim_blocked_here",
            "disposal_receipt_claim_blocked_here",
            "r52_reintake_claim_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "p5_finalization_blocked_here",
        ),
        source="P7-R54-AHR-CR05 local-only preflight",
    )
    _assert_false_fields(
        data,
        keys=(
            "body_full_packet_generation_started_here",
            "body_full_packet_generated_here",
            "body_full_packet_content_included",
            "body_full_packet_content_exported",
            "local_absolute_path_included",
            "body_hash_included",
            "terminal_output_body_included",
            "actual_human_review_run_here",
            "actual_human_review_complete",
            "actual_review_evidence_complete",
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "p5_confirmed_final",
            "p6_start_allowed",
            "p8_start_allowed",
            "release_allowed",
        ),
        source="P7-R54-AHR-CR05 local-only preflight",
    )
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CR05_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CR05 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CR05_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CR05 not-yet implemented steps changed")
    return True


def _cr06_packet_generation_request_bridge_fields(
    *,
    preflight_material: Mapping[str, Any],
    packet_generation_request_ref: Any = P7_R54_AHR_CR06_DEFAULT_PACKET_GENERATION_REQUEST_REF,
) -> dict[str, Any]:
    blockers: list[str] = []
    if preflight_material.get("preflight_ready") is not True:
        blockers.append(P7_R54_AHR_CR06_PREFLIGHT_NOT_READY_BLOCKER_REF)
    if preflight_material.get("body_full_packet_generation_allowed_by_preflight") is not True:
        blockers.append(P7_R54_AHR_CR06_PACKET_NOT_ALLOWED_BY_PREFLIGHT_BLOCKER_REF)
    if preflight_material.get("actual_review_operation_allowed_by_preflight") is not True:
        blockers.append(P7_R54_AHR_CR06_ACTUAL_OPERATION_NOT_ALLOWED_BY_PREFLIGHT_BLOCKER_REF)
    if preflight_material.get("explicit_allow_ref_present") is not True:
        blockers.append(P7_R54_AHR_CR06_EXPLICIT_ALLOW_MISSING_BLOCKER_REF)
    if preflight_material.get("body_full_packet_export_allowed") is not False:
        blockers.append(P7_R54_AHR_CR06_BODYFULL_EXPORT_ALLOWED_BLOCKER_REF)
    if preflight_material.get("body_full_packet_content_included") is not False:
        blockers.append(P7_R54_AHR_CR06_BODYFULL_CONTENT_INCLUDED_BLOCKER_REF)
    if preflight_material.get("body_full_packet_generated_here") is not False:
        blockers.append(P7_R54_AHR_CR06_BODYFULL_ALREADY_GENERATED_BLOCKER_REF)
    if preflight_material.get("actual_human_review_run_here") is not False:
        blockers.append(P7_R54_AHR_CR06_ACTUAL_REVIEW_ALREADY_RUN_BLOCKER_REF)
    deduped_blockers: list[str] = []
    seen: set[str] = set()
    for blocker in blockers:
        if blocker not in seen:
            deduped_blockers.append(blocker)
            seen.add(blocker)
    ready = not deduped_blockers
    request_ref = (
        clean_identifier(packet_generation_request_ref, default=P7_R54_AHR_CR06_DEFAULT_PACKET_GENERATION_REQUEST_REF, max_length=240)
        if ready
        else ""
    )
    return {
        "packet_generation_request_bridge_status_ref": (
            P7_R54_AHR_CR06_PACKET_REQUEST_READY_STATUS_REF
            if ready
            else P7_R54_AHR_CR06_PACKET_REQUEST_BLOCKED_STATUS_REF
        ),
        "packet_generation_request_bridge_allowed_status_refs": list(
            P7_R54_AHR_CR06_ALLOWED_PACKET_REQUEST_STATUS_REFS
        ),
        "packet_generation_request_bridge_ready": ready,
        "packet_generation_request_bridge_reason_refs": [P7_R54_AHR_CR06_READY_REASON_REF] if ready else [],
        "packet_generation_request_bridge_blocker_refs": deduped_blockers,
        "packet_generation_request_bridge_blocker_ref_count": len(deduped_blockers),
        "packet_generation_request_ref": request_ref,
        "packet_generation_request_ref_present": bool(request_ref),
        "packet_generation_allowed_by_preflight": ready,
        "packet_generation_started_here": False,
        "body_full_packet_generation_started_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packet_content_included": False,
        "local_absolute_path_included": False,
        "body_hash_included": False,
        "terminal_output_body_included": False,
        "request_bridge_requires_cr05_ready_preflight": True,
        "request_bridge_does_not_generate_packet_body": True,
        "request_bridge_does_not_materialize_local_packet": True,
        "request_bridge_does_not_execute_actual_human_review": True,
        "request_bridge_does_not_create_review_rows": True,
        "request_bridge_does_not_create_disposal_receipt": True,
        "request_bridge_keeps_request_receipt_refs_bodyfree": True,
    }


def build_p7_r54_ahr_cr06_packet_generation_request_bridge(
    *,
    local_only_preflight: Mapping[str, Any] | None = None,
    packet_generation_request_ref: Any = P7_R54_AHR_CR06_DEFAULT_PACKET_GENERATION_REQUEST_REF,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build CR06 body-free packet-generation request bridge material.

    CR06 never generates a body-full packet.  It only records whether CR05 is
    ready enough to consider a later local-only packet generation request, and
    it materializes at most a body-free request ref.
    """

    cr05 = dict(local_only_preflight or build_p7_r54_ahr_cr05_local_only_preflight())
    assert_p7_r54_ahr_cr05_local_only_preflight_contract(cr05)
    bridge_fields = _cr06_packet_generation_request_bridge_fields(
        preflight_material=cr05,
        packet_generation_request_ref=packet_generation_request_ref,
    )
    ready = bridge_fields["packet_generation_request_bridge_ready"] is True
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CR06_PACKET_GENERATION_REQUEST_BRIDGE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CR_STEP,
        "scope": P7_R54_AHR_CR_SCOPE,
        "policy_kind": P7_R54_AHR_CR_POLICY_KIND,
        "policy_section": P7_R54_AHR_CR06_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CR06_STEP_REF,
        "current_phase": P7_R54_AHR_CR_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cr06_packet_generation_request_bridge_20260628",
        "review_session_id": _safe_review_session_id(review_session_id or cr05.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cr05_schema_version": cr05["schema_version"],
        "cr05_material_ref": cr05["material_id"],
        "cr05_next_required_step": cr05["next_required_step"],
        "cr05_preflight_status_ref": cr05["preflight_status_ref"],
        "cr05_preflight_ready": cr05["preflight_ready"],
        "cr05_preflight_blocker_refs": list(cr05["preflight_blocker_refs"]),
        "cr05_body_full_packet_generation_allowed_by_preflight": cr05[
            "body_full_packet_generation_allowed_by_preflight"
        ],
        "cr05_actual_review_operation_allowed_by_preflight": cr05["actual_review_operation_allowed_by_preflight"],
        "cr05_local_only": cr05["local_only"],
        "cr05_must_not_export": cr05["must_not_export"],
        "cr05_explicit_allow_ref_present": cr05["explicit_allow_ref_present"],
        "cr05_body_full_packet_export_allowed": cr05["body_full_packet_export_allowed"],
        "cr05_body_full_packet_content_included": cr05["body_full_packet_content_included"],
        "cr05_body_full_packet_generated_here": cr05["body_full_packet_generated_here"],
        "cr05_actual_human_review_run_here": cr05["actual_human_review_run_here"],
        **_current_received_basis_fields(actual_basis=True),
        **_historical_basis_fields(),
        **bridge_fields,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_rating_or_question_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR_CR06_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_CR06_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_CR07_STEP_REF if ready else P7_R54_AHR_CR06_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    material["packet_generation_started_here"] = False
    material["body_full_packet_generation_started_here"] = False
    material["body_full_packet_generated_here"] = False
    material["body_full_packet_content_included"] = False
    material["local_absolute_path_included"] = False
    material["body_hash_included"] = False
    material["terminal_output_body_included"] = False
    return material


def assert_p7_r54_ahr_cr06_packet_generation_request_bridge_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CR06_PACKET_GENERATION_REQUEST_BRIDGE_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CR06 packet generation request bridge",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CR06_PACKET_GENERATION_REQUEST_BRIDGE_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CR06_STEP_REF,
        operation_step_ref=P7_R54_AHR_CR06_STEP_REF,
        source="P7-R54-AHR-CR06 packet generation request bridge",
    )
    if data.get("cr05_schema_version") != P7_R54_AHR_CR05_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CR06 CR05 schema version changed")
    if data.get("cr05_preflight_ready") is True:
        if data.get("cr05_next_required_step") != P7_R54_AHR_CR06_STEP_REF:
            raise ValueError("P7-R54-AHR-CR06 ready CR05 must point to CR06")
    elif data.get("cr05_next_required_step") != P7_R54_AHR_CR05_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
        raise ValueError("P7-R54-AHR-CR06 blocked CR05 next step changed")
    _assert_current_received_basis_fields(data, actual_basis=True, source="P7-R54-AHR-CR06 packet generation request bridge")
    _assert_historical_basis_fields(data, source="P7-R54-AHR-CR06 packet generation request bridge")
    synthetic_cr05 = {
        "preflight_ready": data.get("cr05_preflight_ready"),
        "body_full_packet_generation_allowed_by_preflight": data.get(
            "cr05_body_full_packet_generation_allowed_by_preflight"
        ),
        "actual_review_operation_allowed_by_preflight": data.get("cr05_actual_review_operation_allowed_by_preflight"),
        "explicit_allow_ref_present": data.get("cr05_explicit_allow_ref_present"),
        "body_full_packet_export_allowed": data.get("cr05_body_full_packet_export_allowed"),
        "body_full_packet_content_included": data.get("cr05_body_full_packet_content_included"),
        "body_full_packet_generated_here": data.get("cr05_body_full_packet_generated_here"),
        "actual_human_review_run_here": data.get("cr05_actual_human_review_run_here"),
    }
    expected_bridge = _cr06_packet_generation_request_bridge_fields(
        preflight_material=synthetic_cr05,
        packet_generation_request_ref=data.get("packet_generation_request_ref")
        or P7_R54_AHR_CR06_DEFAULT_PACKET_GENERATION_REQUEST_REF,
    )
    for key, expected in expected_bridge.items():
        if data.get(key) != expected:
            raise ValueError(f"P7-R54-AHR-CR06 packet generation request bridge {key} changed")
    ready = data.get("packet_generation_request_bridge_status_ref") == P7_R54_AHR_CR06_PACKET_REQUEST_READY_STATUS_REF
    if data.get("packet_generation_request_bridge_ready") is not ready:
        raise ValueError("P7-R54-AHR-CR06 ready flag changed")
    blockers = list(data.get("packet_generation_request_bridge_blocker_refs") or [])
    if data.get("packet_generation_request_bridge_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-CR06 blocker count changed")
    if ready:
        if blockers:
            raise ValueError("P7-R54-AHR-CR06 ready bridge cannot carry blockers")
        if data.get("packet_generation_request_bridge_reason_refs") != [P7_R54_AHR_CR06_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-CR06 ready reason changed")
        if data.get("packet_generation_request_ref_present") is not True:
            raise ValueError("P7-R54-AHR-CR06 ready bridge requires request ref")
        if data.get("packet_generation_allowed_by_preflight") is not True:
            raise ValueError("P7-R54-AHR-CR06 ready bridge must be allowed by preflight")
        if data.get("next_required_step") != P7_R54_AHR_CR07_STEP_REF:
            raise ValueError("P7-R54-AHR-CR06 ready next step changed")
    else:
        if not blockers:
            raise ValueError("P7-R54-AHR-CR06 blocked bridge must carry blockers")
        if data.get("packet_generation_request_bridge_reason_refs") != []:
            raise ValueError("P7-R54-AHR-CR06 blocked bridge cannot carry ready reasons")
        if data.get("packet_generation_request_ref_present") is not False:
            raise ValueError("P7-R54-AHR-CR06 blocked bridge cannot materialize request ref")
        if data.get("packet_generation_allowed_by_preflight") is not False:
            raise ValueError("P7-R54-AHR-CR06 blocked bridge cannot allow packet generation")
        if data.get("next_required_step") != P7_R54_AHR_CR06_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CR06 blocked next step changed")
    _assert_true_fields(
        data,
        keys=(
            "request_bridge_requires_cr05_ready_preflight",
            "request_bridge_does_not_generate_packet_body",
            "request_bridge_does_not_materialize_local_packet",
            "request_bridge_does_not_execute_actual_human_review",
            "request_bridge_does_not_create_review_rows",
            "request_bridge_does_not_create_disposal_receipt",
            "request_bridge_keeps_request_receipt_refs_bodyfree",
            "actual_human_review_completion_claim_blocked_here",
            "actual_rating_or_question_rows_claim_blocked_here",
            "disposal_receipt_claim_blocked_here",
            "r52_reintake_claim_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "p5_finalization_blocked_here",
        ),
        source="P7-R54-AHR-CR06 packet generation request bridge",
    )
    _assert_false_fields(
        data,
        keys=(
            "packet_generation_started_here",
            "body_full_packet_generation_started_here",
            "body_full_packet_generated_here",
            "body_full_packet_content_included",
            "local_absolute_path_included",
            "body_hash_included",
            "terminal_output_body_included",
            "actual_human_review_run_here",
            "actual_human_review_complete",
            "actual_review_evidence_complete",
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "p5_confirmed_final",
            "p6_start_allowed",
            "p8_start_allowed",
            "release_allowed",
        ),
        source="P7-R54-AHR-CR06 packet generation request bridge",
    )
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CR06_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CR06 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CR06_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CR06 not-yet implemented steps changed")
    return True


def build_p7_r54_ahr_cr07_bodyfree_receipt_input(
    *,
    packet_generation_receipt_ref: Any = P7_R54_AHR_CR07_DEFAULT_PACKET_GENERATION_RECEIPT_REF,
    packet_case_count: Any = P7_R54_AHR_CR_REQUIRED_CASE_COUNT,
    packet_completeness_scan_ref: Any = P7_R54_AHR_CR07_DEFAULT_PACKET_COMPLETENESS_SCAN_REF,
    export_denylist_scan_ref: Any = P7_R54_AHR_CR07_DEFAULT_EXPORT_DENYLIST_SCAN_REF,
    packet_completeness_passed: bool = True,
    export_denylist_scan_passed: bool = True,
) -> dict[str, Any]:
    """Build a minimal body-free CR07 receipt input.

    This is not a packet body.  It is only the metadata needed to exercise the
    CR07 receipt/scan contract.
    """

    return {
        "packet_generation_receipt_ref": clean_identifier(
            packet_generation_receipt_ref, default=P7_R54_AHR_CR07_DEFAULT_PACKET_GENERATION_RECEIPT_REF, max_length=240
        ),
        "packet_case_count": packet_case_count,
        "packet_completeness_scan_ref": clean_identifier(
            packet_completeness_scan_ref, default=P7_R54_AHR_CR07_DEFAULT_PACKET_COMPLETENESS_SCAN_REF, max_length=240
        ),
        "export_denylist_scan_ref": clean_identifier(
            export_denylist_scan_ref, default=P7_R54_AHR_CR07_DEFAULT_EXPORT_DENYLIST_SCAN_REF, max_length=240
        ),
        "packet_completeness_passed": bool(packet_completeness_passed),
        "export_denylist_scan_passed": bool(export_denylist_scan_passed),
    }


def _coerce_packet_case_count(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return -1


def _cr07_packet_generation_receipt_scan_fields(
    *,
    request_bridge: Mapping[str, Any],
    receipt_input: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    provided = receipt_input is not None
    receipt = dict(receipt_input or {})
    forbidden_detected = _contains_forbidden_body_or_question_key(receipt) if provided else False
    receipt_ref = clean_identifier(receipt.get("packet_generation_receipt_ref"), default="", max_length=240)
    packet_count = _coerce_packet_case_count(receipt.get("packet_case_count")) if provided else 0
    completeness_ref = clean_identifier(receipt.get("packet_completeness_scan_ref"), default="", max_length=240)
    export_scan_ref = clean_identifier(receipt.get("export_denylist_scan_ref"), default="", max_length=240)
    completeness_passed = bool(receipt.get("packet_completeness_passed")) if provided else False
    export_passed = bool(receipt.get("export_denylist_scan_passed")) if provided else False
    blockers: list[str] = []
    if request_bridge.get("packet_generation_request_bridge_ready") is not True:
        blockers.append(P7_R54_AHR_CR07_CR06_NOT_READY_BLOCKER_REF)
    if request_bridge.get("packet_generation_request_ref_present") is not True:
        blockers.append(P7_R54_AHR_CR07_CR06_REQUEST_REF_MISSING_BLOCKER_REF)
    if not provided:
        blockers.append(P7_R54_AHR_CR07_RECEIPT_INPUT_MISSING_BLOCKER_REF)
    if provided and forbidden_detected:
        blockers.append(P7_R54_AHR_CR07_FORBIDDEN_RECEIPT_KEY_BLOCKER_REF)
    if provided and not receipt_ref:
        blockers.append(P7_R54_AHR_CR07_RECEIPT_REF_MISSING_BLOCKER_REF)
    if provided and packet_count != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
        blockers.append(P7_R54_AHR_CR07_PACKET_COUNT_NOT_24_BLOCKER_REF)
    if provided and not completeness_ref:
        blockers.append(P7_R54_AHR_CR07_COMPLETENESS_SCAN_REF_MISSING_BLOCKER_REF)
    if provided and not export_scan_ref:
        blockers.append(P7_R54_AHR_CR07_EXPORT_DENYLIST_SCAN_REF_MISSING_BLOCKER_REF)
    if provided and not completeness_passed:
        blockers.append(P7_R54_AHR_CR07_COMPLETENESS_SCAN_NOT_PASSED_BLOCKER_REF)
    if provided and not export_passed:
        blockers.append(P7_R54_AHR_CR07_EXPORT_DENYLIST_SCAN_NOT_PASSED_BLOCKER_REF)
    deduped_blockers: list[str] = []
    seen: set[str] = set()
    for blocker in blockers:
        if blocker not in seen:
            deduped_blockers.append(blocker)
            seen.add(blocker)
    ready = not deduped_blockers
    return {
        "packet_generation_receipt_status_ref": (
            P7_R54_AHR_CR07_PACKET_RECEIPT_ACCEPTED_STATUS_REF
            if ready
            else P7_R54_AHR_CR07_PACKET_RECEIPT_BLOCKED_STATUS_REF
        ),
        "packet_generation_receipt_allowed_status_refs": list(
            P7_R54_AHR_CR07_ALLOWED_PACKET_RECEIPT_STATUS_REFS
        ),
        "packet_generation_receipt_ready": ready,
        "packet_generation_receipt_reason_refs": [P7_R54_AHR_CR07_READY_REASON_REF] if ready else [],
        "packet_generation_receipt_blocker_refs": deduped_blockers,
        "packet_generation_receipt_blocker_ref_count": len(deduped_blockers),
        "packet_generation_receipt_input_provided": provided,
        "receipt_input_forbidden_key_detected": forbidden_detected,
        "packet_generation_receipt_ref": receipt_ref if ready else "",
        "packet_generation_receipt_ref_present": bool(receipt_ref) if ready else False,
        "packet_case_count": packet_count if provided else 0,
        "packet_case_count_matches_manifest": packet_count == P7_R54_AHR_CR_REQUIRED_CASE_COUNT,
        "packet_completeness_scan_ref": completeness_ref if ready else "",
        "packet_completeness_scan_ref_present": bool(completeness_ref) if ready else False,
        "packet_completeness_passed": completeness_passed if ready else False,
        "export_denylist_scan_ref": export_scan_ref if ready else "",
        "export_denylist_scan_ref_present": bool(export_scan_ref) if ready else False,
        "export_denylist_scan_passed": export_passed if ready else False,
        "packet_completeness_scan_bodyfree_only": True,
        "export_denylist_scan_bodyfree_only": True,
        "receipt_does_not_include_packet_body": True,
        "receipt_does_not_include_local_absolute_path": True,
        "receipt_does_not_include_body_hash": True,
        "receipt_does_not_generate_packet_body_here": True,
        "receipt_does_not_execute_actual_human_review": True,
        "receipt_does_not_create_review_rows": True,
        "receipt_does_not_create_disposal_receipt": True,
        "receipt_is_bodyfree_counts_and_refs_only": True,
        "body_full_packet_content_included": False,
        "local_absolute_path_included": False,
        "body_hash_included": False,
        "terminal_output_body_included": False,
    }


def build_p7_r54_ahr_cr07_packet_generation_receipt_and_scan(
    *,
    packet_generation_request_bridge: Mapping[str, Any] | None = None,
    receipt_input: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build CR07 body-free packet generation receipt / scan material.

    CR07 never stores packet body, local path, or body hash.  Without a
    body-free receipt input, it remains blocked and does not claim packet
    completeness or export-denylist success.
    """

    cr06 = dict(packet_generation_request_bridge or build_p7_r54_ahr_cr06_packet_generation_request_bridge())
    assert_p7_r54_ahr_cr06_packet_generation_request_bridge_contract(cr06)
    receipt_fields = _cr07_packet_generation_receipt_scan_fields(
        request_bridge=cr06,
        receipt_input=receipt_input,
    )
    ready = receipt_fields["packet_generation_receipt_ready"] is True
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CR07_PACKET_GENERATION_RECEIPT_SCAN_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CR_STEP,
        "scope": P7_R54_AHR_CR_SCOPE,
        "policy_kind": P7_R54_AHR_CR_POLICY_KIND,
        "policy_section": P7_R54_AHR_CR07_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CR07_STEP_REF,
        "current_phase": P7_R54_AHR_CR_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cr07_packet_generation_receipt_completeness_export_scan_20260628",
        "review_session_id": _safe_review_session_id(review_session_id or cr06.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cr06_schema_version": cr06["schema_version"],
        "cr06_material_ref": cr06["material_id"],
        "cr06_next_required_step": cr06["next_required_step"],
        "cr06_packet_generation_request_bridge_status_ref": cr06["packet_generation_request_bridge_status_ref"],
        "cr06_packet_generation_request_bridge_ready": cr06["packet_generation_request_bridge_ready"],
        "cr06_packet_generation_request_ref": cr06["packet_generation_request_ref"],
        "cr06_packet_generation_request_ref_present": cr06["packet_generation_request_ref_present"],
        "cr06_packet_generation_allowed_by_preflight": cr06["packet_generation_allowed_by_preflight"],
        "cr06_packet_generation_started_here": cr06["packet_generation_started_here"],
        "cr06_body_full_packet_generation_started_here": cr06["body_full_packet_generation_started_here"],
        "cr06_body_full_packet_generated_here": cr06["body_full_packet_generated_here"],
        "cr06_body_full_packet_content_included": cr06["body_full_packet_content_included"],
        "cr06_local_absolute_path_included": cr06["local_absolute_path_included"],
        "cr06_body_hash_included": cr06["body_hash_included"],
        "cr06_actual_human_review_run_here": cr06["actual_human_review_run_here"],
        **_current_received_basis_fields(actual_basis=True),
        **_historical_basis_fields(),
        **receipt_fields,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_rating_or_question_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR_CR07_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_CR07_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_CR08_STEP_REF if ready else P7_R54_AHR_CR07_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    material["body_full_packet_content_included"] = False
    material["local_absolute_path_included"] = False
    material["body_hash_included"] = False
    material["terminal_output_body_included"] = False
    return material


def assert_p7_r54_ahr_cr07_packet_generation_receipt_and_scan_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CR07_PACKET_GENERATION_RECEIPT_SCAN_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CR07 packet generation receipt / scan",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CR07_PACKET_GENERATION_RECEIPT_SCAN_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CR07_STEP_REF,
        operation_step_ref=P7_R54_AHR_CR07_STEP_REF,
        source="P7-R54-AHR-CR07 packet generation receipt / scan",
    )
    if data.get("cr06_schema_version") != P7_R54_AHR_CR06_PACKET_GENERATION_REQUEST_BRIDGE_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CR07 CR06 schema version changed")
    if data.get("cr06_packet_generation_request_bridge_ready") is True:
        if data.get("cr06_next_required_step") != P7_R54_AHR_CR07_STEP_REF:
            raise ValueError("P7-R54-AHR-CR07 ready CR06 must point to CR07")
    elif data.get("cr06_next_required_step") != P7_R54_AHR_CR06_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
        raise ValueError("P7-R54-AHR-CR07 blocked CR06 next step changed")
    _assert_current_received_basis_fields(data, actual_basis=True, source="P7-R54-AHR-CR07 packet generation receipt / scan")
    _assert_historical_basis_fields(data, source="P7-R54-AHR-CR07 packet generation receipt / scan")
    if data.get("cr06_packet_generation_request_bridge_ready") is True:
        if data.get("cr06_packet_generation_allowed_by_preflight") is not True:
            raise ValueError("P7-R54-AHR-CR07 ready CR06 must remain allowed by preflight")
    ready = data.get("packet_generation_receipt_status_ref") == P7_R54_AHR_CR07_PACKET_RECEIPT_ACCEPTED_STATUS_REF
    if ready:
        synthetic_cr06 = {
            "packet_generation_request_bridge_ready": data.get("cr06_packet_generation_request_bridge_ready"),
            "packet_generation_request_ref_present": data.get("cr06_packet_generation_request_ref_present"),
        }
        synthetic_receipt = {
            "packet_generation_receipt_ref": data.get("packet_generation_receipt_ref"),
            "packet_case_count": data.get("packet_case_count"),
            "packet_completeness_scan_ref": data.get("packet_completeness_scan_ref"),
            "export_denylist_scan_ref": data.get("export_denylist_scan_ref"),
            "packet_completeness_passed": data.get("packet_completeness_passed"),
            "export_denylist_scan_passed": data.get("export_denylist_scan_passed"),
        }
        expected_receipt = _cr07_packet_generation_receipt_scan_fields(
            request_bridge=synthetic_cr06,
            receipt_input=synthetic_receipt,
        )
        for key, expected in expected_receipt.items():
            if data.get(key) != expected:
                raise ValueError(f"P7-R54-AHR-CR07 packet generation receipt / scan {key} changed")
    if data.get("packet_generation_receipt_ready") is not ready:
        raise ValueError("P7-R54-AHR-CR07 ready flag changed")
    blockers = list(data.get("packet_generation_receipt_blocker_refs") or [])
    if data.get("packet_generation_receipt_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-CR07 blocker count changed")
    if ready:
        if blockers:
            raise ValueError("P7-R54-AHR-CR07 accepted receipt cannot carry blockers")
        if data.get("packet_generation_receipt_reason_refs") != [P7_R54_AHR_CR07_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-CR07 ready reason changed")
        if data.get("packet_generation_receipt_ref_present") is not True:
            raise ValueError("P7-R54-AHR-CR07 accepted receipt requires receipt ref")
        if data.get("packet_case_count") != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-CR07 accepted receipt requires 24 packets")
        if data.get("packet_completeness_scan_ref_present") is not True:
            raise ValueError("P7-R54-AHR-CR07 accepted receipt requires completeness scan ref")
        if data.get("export_denylist_scan_ref_present") is not True:
            raise ValueError("P7-R54-AHR-CR07 accepted receipt requires export scan ref")
        if data.get("packet_completeness_passed") is not True:
            raise ValueError("P7-R54-AHR-CR07 completeness scan must pass")
        if data.get("export_denylist_scan_passed") is not True:
            raise ValueError("P7-R54-AHR-CR07 export denylist scan must pass")
        if data.get("next_required_step") != P7_R54_AHR_CR08_STEP_REF:
            raise ValueError("P7-R54-AHR-CR07 ready next step changed")
    else:
        if not blockers:
            raise ValueError("P7-R54-AHR-CR07 blocked receipt must carry blockers")
        if data.get("packet_generation_receipt_reason_refs") != []:
            raise ValueError("P7-R54-AHR-CR07 blocked receipt cannot carry ready reasons")
        if data.get("packet_generation_receipt_ref_present") is not False:
            raise ValueError("P7-R54-AHR-CR07 blocked receipt cannot materialize receipt ref")
        if data.get("next_required_step") != P7_R54_AHR_CR07_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CR07 blocked next step changed")
    _assert_true_fields(
        data,
        keys=(
            "packet_completeness_scan_bodyfree_only",
            "export_denylist_scan_bodyfree_only",
            "receipt_does_not_include_packet_body",
            "receipt_does_not_include_local_absolute_path",
            "receipt_does_not_include_body_hash",
            "receipt_does_not_generate_packet_body_here",
            "receipt_does_not_execute_actual_human_review",
            "receipt_does_not_create_review_rows",
            "receipt_does_not_create_disposal_receipt",
            "receipt_is_bodyfree_counts_and_refs_only",
            "actual_human_review_completion_claim_blocked_here",
            "actual_rating_or_question_rows_claim_blocked_here",
            "disposal_receipt_claim_blocked_here",
            "r52_reintake_claim_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "p5_finalization_blocked_here",
        ),
        source="P7-R54-AHR-CR07 packet generation receipt / scan",
    )
    _assert_false_fields(
        data,
        keys=(
            "cr06_packet_generation_started_here",
            "cr06_body_full_packet_generation_started_here",
            "cr06_body_full_packet_generated_here",
            "cr06_body_full_packet_content_included",
            "cr06_local_absolute_path_included",
            "cr06_body_hash_included",
            "cr06_actual_human_review_run_here",
            "body_full_packet_content_included",
            "local_absolute_path_included",
            "body_hash_included",
            "terminal_output_body_included",
            "actual_human_review_run_here",
            "actual_human_review_complete",
            "actual_review_evidence_complete",
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "p5_confirmed_final",
            "p6_start_allowed",
            "p8_start_allowed",
            "release_allowed",
        ),
        source="P7-R54-AHR-CR07 packet generation receipt / scan",
    )
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CR07_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CR07 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CR07_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CR07 not-yet implemented steps changed")
    return True


def _cr08_reviewer_selection_form_fields(
    *,
    packet_generation_receipt_scan: Mapping[str, Any],
    reviewer_person_ref: Any = "",
    reviewer_is_person: bool = False,
    reviewer_person_confirmed: bool = False,
) -> dict[str, Any]:
    reviewer_ref = clean_identifier(reviewer_person_ref, default="", max_length=200)
    blockers: list[str] = []
    if packet_generation_receipt_scan.get("packet_generation_receipt_ready") is not True:
        blockers.append(P7_R54_AHR_CR08_CR07_NOT_READY_BLOCKER_REF)
    if packet_generation_receipt_scan.get("packet_generation_receipt_ref_present") is not True:
        blockers.append(P7_R54_AHR_CR08_CR07_RECEIPT_REF_MISSING_BLOCKER_REF)
    if packet_generation_receipt_scan.get("packet_case_count") != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
        blockers.append(P7_R54_AHR_CR08_CR07_PACKET_COUNT_NOT_24_BLOCKER_REF)
    if (
        packet_generation_receipt_scan.get("packet_completeness_passed") is not True
        or packet_generation_receipt_scan.get("export_denylist_scan_passed") is not True
    ):
        blockers.append(P7_R54_AHR_CR08_CR07_PACKET_SCAN_NOT_PASSED_BLOCKER_REF)
    if packet_generation_receipt_scan.get("body_full_packet_content_included") is not False:
        blockers.append(P7_R54_AHR_CR08_CR07_BODY_LEAK_BLOCKER_REF)
    if (
        packet_generation_receipt_scan.get("local_absolute_path_included") is not False
        or packet_generation_receipt_scan.get("body_hash_included") is not False
    ):
        blockers.append(P7_R54_AHR_CR08_CR07_PATH_HASH_LEAK_BLOCKER_REF)
    if not reviewer_ref:
        blockers.append(P7_R54_AHR_CR08_REVIEWER_PERSON_REF_MISSING_BLOCKER_REF)
    if bool(reviewer_is_person) is not True:
        blockers.append(P7_R54_AHR_CR08_REVIEWER_IS_PERSON_FALSE_BLOCKER_REF)
    if bool(reviewer_person_confirmed) is not True:
        blockers.append(P7_R54_AHR_CR08_REVIEWER_PERSON_NOT_CONFIRMED_BLOCKER_REF)
    deduped_blockers: list[str] = []
    seen: set[str] = set()
    for blocker in blockers:
        if blocker not in seen:
            deduped_blockers.append(blocker)
            seen.add(blocker)
    ready = not deduped_blockers
    return {
        "reviewer_selection_form_status_ref": (
            P7_R54_AHR_CR08_REVIEWER_FORM_READY_STATUS_REF
            if ready
            else P7_R54_AHR_CR08_REVIEWER_FORM_BLOCKED_STATUS_REF
        ),
        "reviewer_selection_form_allowed_status_refs": list(P7_R54_AHR_CR08_ALLOWED_REVIEWER_FORM_STATUS_REFS),
        "reviewer_selection_form_ready": ready,
        "reviewer_selection_form_reason_refs": [P7_R54_AHR_CR08_READY_REASON_REF] if ready else [],
        "reviewer_selection_form_blocker_refs": deduped_blockers,
        "reviewer_selection_form_blocker_ref_count": len(deduped_blockers),
        "reviewer_person_ref": reviewer_ref if ready else "",
        "reviewer_person_ref_present": bool(reviewer_ref) if ready else False,
        "reviewer_is_person": bool(reviewer_is_person) if ready else False,
        "reviewer_person_confirmed": bool(reviewer_person_confirmed) if ready else False,
        "reviewer_person_boundary_confirmed": ready,
        "reviewer_identity_bodyfree_ref_only": True,
        "selection_form_status_ref": "CR08_SELECTION_ONLY_FORM_FROZEN_BODYFREE",
        "rating_axis_refs": list(P7_R54_AHR_CR08_RATING_AXIS_REFS),
        "rating_axis_count": len(P7_R54_AHR_CR08_RATING_AXIS_REFS),
        "rating_axis_target_thresholds": dict(P7_R54_AHR_CR08_RATING_AXIS_TARGET_THRESHOLDS),
        "question_need_primary_class_options": list(P7_R54_AHR_CR08_QUESTION_NEED_PRIMARY_CLASS_OPTION_REFS),
        "question_need_primary_class_option_count": len(P7_R54_AHR_CR08_QUESTION_NEED_PRIMARY_CLASS_OPTION_REFS),
        "one_question_fit_option_refs": list(P7_R54_AHR_CR08_ONE_QUESTION_FIT_OPTION_REFS),
        "one_question_fit_option_count": len(P7_R54_AHR_CR08_ONE_QUESTION_FIT_OPTION_REFS),
        "selection_row_count_required": P7_R54_AHR_CR_REQUIRED_CASE_COUNT,
        "allowed_selection_row_count": P7_R54_AHR_CR_REQUIRED_CASE_COUNT,
        "selection_only": True,
        "selection_form_selection_only": True,
        "free_text_allowed": False,
        "reviewer_free_text_allowed": False,
        "reviewer_notes_export_allowed": False,
        "question_text_allowed": False,
        "draft_question_text_allowed": False,
        "selection_form_bodyfree_only": True,
        "selection_form_does_not_include_body": True,
        "selection_form_does_not_include_reviewer_free_text": True,
        "selection_form_does_not_include_question_text": True,
        "selection_form_does_not_execute_actual_human_review": True,
        "selection_form_does_not_create_review_rows": True,
        "selection_form_does_not_create_disposal_receipt": True,
    }


def build_p7_r54_ahr_cr08_reviewer_selection_form(
    *,
    packet_generation_receipt_scan: Mapping[str, Any] | None = None,
    reviewer_person_ref: Any = "",
    reviewer_is_person: bool = False,
    reviewer_person_confirmed: bool = False,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build CR08 reviewer selection-only form / person boundary material.

    CR08 freezes the form and person boundary only. It does not execute the
    actual human review and does not materialize rating rows, question rows, or
    disposal receipts.
    """

    cr07 = dict(packet_generation_receipt_scan or build_p7_r54_ahr_cr07_packet_generation_receipt_and_scan())
    assert_p7_r54_ahr_cr07_packet_generation_receipt_and_scan_contract(cr07)
    form_fields = _cr08_reviewer_selection_form_fields(
        packet_generation_receipt_scan=cr07,
        reviewer_person_ref=reviewer_person_ref,
        reviewer_is_person=reviewer_is_person,
        reviewer_person_confirmed=reviewer_person_confirmed,
    )
    ready = form_fields["reviewer_selection_form_ready"] is True
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CR08_REVIEWER_SELECTION_FORM_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CR_STEP,
        "scope": P7_R54_AHR_CR_SCOPE,
        "policy_kind": P7_R54_AHR_CR_POLICY_KIND,
        "policy_section": P7_R54_AHR_CR08_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CR08_STEP_REF,
        "current_phase": P7_R54_AHR_CR_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cr08_reviewer_selection_form_person_boundary_20260628",
        "review_session_id": _safe_review_session_id(review_session_id or cr07.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cr07_schema_version": cr07["schema_version"],
        "cr07_material_ref": cr07["material_id"],
        "cr07_next_required_step": cr07["next_required_step"],
        "cr07_packet_generation_receipt_status_ref": cr07["packet_generation_receipt_status_ref"],
        "cr07_packet_generation_receipt_ready": cr07["packet_generation_receipt_ready"],
        "cr07_packet_generation_receipt_ref": cr07["packet_generation_receipt_ref"],
        "cr07_packet_generation_receipt_ref_present": cr07["packet_generation_receipt_ref_present"],
        "cr07_packet_case_count": cr07["packet_case_count"],
        "cr07_packet_completeness_passed": cr07["packet_completeness_passed"],
        "cr07_export_denylist_scan_passed": cr07["export_denylist_scan_passed"],
        "cr07_body_full_packet_content_included": cr07["body_full_packet_content_included"],
        "cr07_local_absolute_path_included": cr07["local_absolute_path_included"],
        "cr07_body_hash_included": cr07["body_hash_included"],
        "cr07_actual_human_review_run_here": cr07["actual_human_review_run_here"],
        **_current_received_basis_fields(actual_basis=True),
        **_historical_basis_fields(),
        **form_fields,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_rating_or_question_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR_CR08_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_CR08_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_CR09_STEP_REF if ready else P7_R54_AHR_CR08_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_ahr_cr08_reviewer_selection_form_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CR08_REVIEWER_SELECTION_FORM_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CR08 reviewer selection-only form / person boundary",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CR08_REVIEWER_SELECTION_FORM_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CR08_STEP_REF,
        operation_step_ref=P7_R54_AHR_CR08_STEP_REF,
        source="P7-R54-AHR-CR08 reviewer selection-only form / person boundary",
    )
    if data.get("cr07_schema_version") != P7_R54_AHR_CR07_PACKET_GENERATION_RECEIPT_SCAN_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CR08 CR07 schema version changed")
    if data.get("cr07_packet_generation_receipt_ready") is True:
        if data.get("cr07_next_required_step") != P7_R54_AHR_CR08_STEP_REF:
            raise ValueError("P7-R54-AHR-CR08 ready CR07 must point to CR08")
    elif data.get("cr07_next_required_step") != P7_R54_AHR_CR07_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
        raise ValueError("P7-R54-AHR-CR08 blocked CR07 next step changed")
    _assert_current_received_basis_fields(data, actual_basis=True, source="P7-R54-AHR-CR08 reviewer form")
    _assert_historical_basis_fields(data, source="P7-R54-AHR-CR08 reviewer form")
    ready = data.get("reviewer_selection_form_status_ref") == P7_R54_AHR_CR08_REVIEWER_FORM_READY_STATUS_REF
    if data.get("reviewer_selection_form_ready") is not ready:
        raise ValueError("P7-R54-AHR-CR08 ready flag changed")
    if tuple(data.get("reviewer_selection_form_allowed_status_refs") or ()) != P7_R54_AHR_CR08_ALLOWED_REVIEWER_FORM_STATUS_REFS:
        raise ValueError("P7-R54-AHR-CR08 allowed status refs changed")
    blockers = list(data.get("reviewer_selection_form_blocker_refs") or [])
    if data.get("reviewer_selection_form_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-CR08 blocker count changed")
    if tuple(data.get("rating_axis_refs") or ()) != P7_R54_AHR_CR08_RATING_AXIS_REFS:
        raise ValueError("P7-R54-AHR-CR08 rating axis refs changed")
    if data.get("rating_axis_count") != len(P7_R54_AHR_CR08_RATING_AXIS_REFS):
        raise ValueError("P7-R54-AHR-CR08 rating axis count changed")
    if data.get("rating_axis_target_thresholds") != P7_R54_AHR_CR08_RATING_AXIS_TARGET_THRESHOLDS:
        raise ValueError("P7-R54-AHR-CR08 rating thresholds changed")
    if tuple(data.get("question_need_primary_class_options") or ()) != P7_R54_AHR_CR08_QUESTION_NEED_PRIMARY_CLASS_OPTION_REFS:
        raise ValueError("P7-R54-AHR-CR08 question primary class options changed")
    if data.get("question_need_primary_class_option_count") != len(P7_R54_AHR_CR08_QUESTION_NEED_PRIMARY_CLASS_OPTION_REFS):
        raise ValueError("P7-R54-AHR-CR08 question primary class option count changed")
    if tuple(data.get("one_question_fit_option_refs") or ()) != P7_R54_AHR_CR08_ONE_QUESTION_FIT_OPTION_REFS:
        raise ValueError("P7-R54-AHR-CR08 one-question fit options changed")
    if data.get("one_question_fit_option_count") != len(P7_R54_AHR_CR08_ONE_QUESTION_FIT_OPTION_REFS):
        raise ValueError("P7-R54-AHR-CR08 one-question fit option count changed")
    _assert_true_fields(
        data,
        keys=(
            "reviewer_identity_bodyfree_ref_only",
            "selection_only",
            "selection_form_selection_only",
            "selection_form_bodyfree_only",
            "selection_form_does_not_include_body",
            "selection_form_does_not_include_reviewer_free_text",
            "selection_form_does_not_include_question_text",
            "selection_form_does_not_execute_actual_human_review",
            "selection_form_does_not_create_review_rows",
            "selection_form_does_not_create_disposal_receipt",
            "actual_human_review_completion_claim_blocked_here",
            "actual_rating_or_question_rows_claim_blocked_here",
            "disposal_receipt_claim_blocked_here",
            "r52_reintake_claim_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "p5_finalization_blocked_here",
        ),
        source="P7-R54-AHR-CR08 reviewer selection-only form / person boundary",
    )
    _assert_false_fields(
        data,
        keys=(
            "free_text_allowed",
            "reviewer_free_text_allowed",
            "reviewer_notes_export_allowed",
            "question_text_allowed",
            "draft_question_text_allowed",
            "cr07_body_full_packet_content_included",
            "cr07_local_absolute_path_included",
            "cr07_body_hash_included",
            "cr07_actual_human_review_run_here",
            "actual_human_review_run_here",
            "actual_human_review_complete",
            "actual_review_evidence_complete",
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "p5_confirmed_final",
            "p6_start_allowed",
            "p8_start_allowed",
            "release_allowed",
        ),
        source="P7-R54-AHR-CR08 reviewer selection-only form / person boundary",
    )
    if ready:
        if blockers:
            raise ValueError("P7-R54-AHR-CR08 ready form cannot carry blockers")
        if data.get("reviewer_selection_form_reason_refs") != [P7_R54_AHR_CR08_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-CR08 ready reason changed")
        if data.get("cr07_packet_generation_receipt_ready") is not True:
            raise ValueError("P7-R54-AHR-CR08 ready form requires CR07 accepted receipt")
        _assert_true_fields(
            data,
            keys=(
                "cr07_packet_generation_receipt_ref_present",
                "cr07_packet_completeness_passed",
                "cr07_export_denylist_scan_passed",
                "reviewer_person_ref_present",
                "reviewer_is_person",
                "reviewer_person_confirmed",
                "reviewer_person_boundary_confirmed",
            ),
            source="P7-R54-AHR-CR08 ready reviewer form",
        )
        if data.get("cr07_packet_case_count") != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-CR08 ready form requires 24 packet cases")
        if not data.get("reviewer_person_ref"):
            raise ValueError("P7-R54-AHR-CR08 ready form requires reviewer person ref")
        if data.get("selection_row_count_required") != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-CR08 ready form requires 24 selection rows")
        if data.get("allowed_selection_row_count") != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-CR08 ready form allowed selection count changed")
        if data.get("next_required_step") != P7_R54_AHR_CR09_STEP_REF:
            raise ValueError("P7-R54-AHR-CR08 ready next step changed")
    else:
        if not blockers:
            raise ValueError("P7-R54-AHR-CR08 blocked form must carry blockers")
        if data.get("reviewer_selection_form_reason_refs") != []:
            raise ValueError("P7-R54-AHR-CR08 blocked form cannot carry ready reasons")
        _assert_false_fields(
            data,
            keys=(
                "reviewer_person_ref_present",
                "reviewer_is_person",
                "reviewer_person_confirmed",
                "reviewer_person_boundary_confirmed",
            ),
            source="P7-R54-AHR-CR08 blocked reviewer form",
        )
        if data.get("reviewer_person_ref") != "":
            raise ValueError("P7-R54-AHR-CR08 blocked form cannot expose reviewer person ref")
        if data.get("next_required_step") != P7_R54_AHR_CR08_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CR08 blocked next step changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CR08_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CR08 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CR08_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CR08 not-yet implemented steps changed")
    return True


def build_p7_r54_ahr_cr09_bodyfree_operation_receipt_input(
    *,
    operation_receipt_ref: Any = P7_R54_AHR_CR09_DEFAULT_OPERATION_RECEIPT_REF,
    reviewer_person_ref: Any = P7_R54_AHR_CR08_DEFAULT_REVIEWER_PERSON_REF,
    reviewer_local_only_read_receipt_present: bool = True,
    review_started_at_bucket_ref: Any = P7_R54_AHR_CR09_DEFAULT_REVIEW_STARTED_AT_BUCKET_REF,
    review_completed_at_bucket_ref: Any = P7_R54_AHR_CR09_DEFAULT_REVIEW_COMPLETED_AT_BUCKET_REF,
    reviewed_case_count: Any = P7_R54_AHR_CR_REQUIRED_CASE_COUNT,
    selection_row_count: Any = P7_R54_AHR_CR_REQUIRED_CASE_COUNT,
    local_only: bool = True,
    must_not_export: bool = True,
    selection_only: bool = True,
) -> dict[str, Any]:
    """Build a minimal body-free CR09 operation receipt input.

    This helper returns refs and counts only. It is not a selection row set, not
    rating rows, and not question observation rows.
    """

    return {
        "operation_receipt_ref": clean_identifier(
            operation_receipt_ref, default=P7_R54_AHR_CR09_DEFAULT_OPERATION_RECEIPT_REF, max_length=240
        ),
        "reviewer_person_ref": clean_identifier(
            reviewer_person_ref, default=P7_R54_AHR_CR08_DEFAULT_REVIEWER_PERSON_REF, max_length=200
        ),
        "reviewer_local_only_read_receipt_present": bool(reviewer_local_only_read_receipt_present),
        "review_started_at_bucket_ref": clean_identifier(
            review_started_at_bucket_ref, default=P7_R54_AHR_CR09_DEFAULT_REVIEW_STARTED_AT_BUCKET_REF, max_length=160
        ),
        "review_completed_at_bucket_ref": clean_identifier(
            review_completed_at_bucket_ref, default=P7_R54_AHR_CR09_DEFAULT_REVIEW_COMPLETED_AT_BUCKET_REF, max_length=160
        ),
        "reviewed_case_count": reviewed_case_count,
        "selection_row_count": selection_row_count,
        "local_only": bool(local_only),
        "must_not_export": bool(must_not_export),
        "selection_only": bool(selection_only),
    }


def _cr09_actual_local_human_review_operation_receipt_fields(
    *,
    reviewer_selection_form: Mapping[str, Any],
    operation_receipt_input: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    provided = operation_receipt_input is not None
    receipt = dict(operation_receipt_input or {})
    forbidden_detected = _contains_forbidden_body_or_question_key(receipt) if provided else False
    operation_receipt_ref = clean_identifier(receipt.get("operation_receipt_ref"), default="", max_length=240)
    reviewer_person_ref = clean_identifier(receipt.get("reviewer_person_ref"), default="", max_length=200)
    review_started_ref = clean_identifier(receipt.get("review_started_at_bucket_ref"), default="", max_length=160)
    review_completed_ref = clean_identifier(receipt.get("review_completed_at_bucket_ref"), default="", max_length=160)
    reviewed_count = _coerce_packet_case_count(receipt.get("reviewed_case_count")) if provided else 0
    selection_count = _coerce_packet_case_count(receipt.get("selection_row_count")) if provided else 0
    local_only = bool(receipt.get("local_only")) if provided else False
    must_not_export = bool(receipt.get("must_not_export")) if provided else False
    selection_only = bool(receipt.get("selection_only")) if provided else False
    local_read_receipt = bool(receipt.get("reviewer_local_only_read_receipt_present")) if provided else False
    cr08_reviewer_ref = clean_identifier(reviewer_selection_form.get("reviewer_person_ref"), default="", max_length=200)
    blockers: list[str] = []
    if reviewer_selection_form.get("reviewer_selection_form_ready") is not True:
        blockers.append(P7_R54_AHR_CR09_CR08_NOT_READY_BLOCKER_REF)
    if reviewer_selection_form.get("reviewer_person_ref_present") is not True or not cr08_reviewer_ref:
        blockers.append(P7_R54_AHR_CR09_CR08_REVIEWER_PERSON_REF_MISSING_BLOCKER_REF)
    if (
        reviewer_selection_form.get("reviewer_is_person") is not True
        or reviewer_selection_form.get("reviewer_person_confirmed") is not True
    ):
        blockers.append(P7_R54_AHR_CR09_CR08_REVIEWER_PERSON_NOT_CONFIRMED_BLOCKER_REF)
    if not provided:
        blockers.append(P7_R54_AHR_CR09_OPERATION_RECEIPT_INPUT_MISSING_BLOCKER_REF)
    if provided and forbidden_detected:
        blockers.append(P7_R54_AHR_CR09_FORBIDDEN_RECEIPT_KEY_BLOCKER_REF)
    if provided and not operation_receipt_ref:
        blockers.append(P7_R54_AHR_CR09_OPERATION_RECEIPT_REF_MISSING_BLOCKER_REF)
    if provided and reviewer_person_ref != cr08_reviewer_ref:
        blockers.append(P7_R54_AHR_CR09_REVIEWER_PERSON_REF_MISMATCH_BLOCKER_REF)
    if provided and not local_read_receipt:
        blockers.append(P7_R54_AHR_CR09_REVIEWER_LOCAL_ONLY_READ_RECEIPT_MISSING_BLOCKER_REF)
    if provided and not review_started_ref:
        blockers.append(P7_R54_AHR_CR09_REVIEW_STARTED_BUCKET_REF_MISSING_BLOCKER_REF)
    if provided and not review_completed_ref:
        blockers.append(P7_R54_AHR_CR09_REVIEW_COMPLETED_BUCKET_REF_MISSING_BLOCKER_REF)
    if provided and reviewed_count != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
        blockers.append(P7_R54_AHR_CR09_REVIEWED_CASE_COUNT_NOT_24_BLOCKER_REF)
    if provided and selection_count != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
        blockers.append(P7_R54_AHR_CR09_SELECTION_ROW_COUNT_NOT_24_BLOCKER_REF)
    if provided and not local_only:
        blockers.append(P7_R54_AHR_CR09_LOCAL_ONLY_FALSE_BLOCKER_REF)
    if provided and not must_not_export:
        blockers.append(P7_R54_AHR_CR09_MUST_NOT_EXPORT_FALSE_BLOCKER_REF)
    if provided and not selection_only:
        blockers.append(P7_R54_AHR_CR09_SELECTION_ONLY_FALSE_BLOCKER_REF)
    deduped_blockers: list[str] = []
    seen: set[str] = set()
    for blocker in blockers:
        if blocker not in seen:
            deduped_blockers.append(blocker)
            seen.add(blocker)
    ready = not deduped_blockers
    return {
        "operation_receipt_status_ref": (
            P7_R54_AHR_CR09_OPERATION_RECEIPT_ACCEPTED_STATUS_REF
            if ready
            else P7_R54_AHR_CR09_OPERATION_RECEIPT_BLOCKED_STATUS_REF
        ),
        "operation_receipt_allowed_status_refs": list(P7_R54_AHR_CR09_ALLOWED_OPERATION_RECEIPT_STATUS_REFS),
        "operation_receipt_ready": ready,
        "operation_receipt_reason_refs": [P7_R54_AHR_CR09_READY_REASON_REF] if ready else [],
        "operation_receipt_blocker_refs": deduped_blockers,
        "operation_receipt_blocker_ref_count": len(deduped_blockers),
        "operation_receipt_input_provided": provided,
        "operation_receipt_input_forbidden_key_detected": forbidden_detected,
        "operation_receipt_ref": operation_receipt_ref if ready else "",
        "operation_receipt_ref_present": bool(operation_receipt_ref) if ready else False,
        "reviewer_person_ref": reviewer_person_ref if ready else "",
        "reviewer_person_ref_matches_cr08": reviewer_person_ref == cr08_reviewer_ref if ready else False,
        "reviewer_is_person": True if ready else False,
        "reviewer_person_confirmed": True if ready else False,
        "reviewer_local_only_read_receipt_present": local_read_receipt if ready else False,
        "actual_human_review_executed_by_person": True if ready else False,
        "review_started_at_bucket_ref": review_started_ref if ready else "",
        "review_started_at_bucket_ref_present": bool(review_started_ref) if ready else False,
        "review_completed_at_bucket_ref": review_completed_ref if ready else "",
        "review_completed_at_bucket_ref_present": bool(review_completed_ref) if ready else False,
        "reviewed_case_count": reviewed_count if provided else 0,
        "reviewed_case_count_matches_manifest": reviewed_count == P7_R54_AHR_CR_REQUIRED_CASE_COUNT,
        "selection_row_count": selection_count if provided else 0,
        "selection_row_count_matches_required": selection_count == P7_R54_AHR_CR_REQUIRED_CASE_COUNT,
        "local_only": local_only if ready else False,
        "must_not_export": must_not_export if ready else False,
        "selection_only": selection_only if ready else False,
        "operation_receipt_bodyfree_only": True,
        "operation_receipt_does_not_include_body": True,
        "operation_receipt_does_not_include_reviewer_free_text": True,
        "operation_receipt_does_not_include_question_text": True,
        "operation_receipt_does_not_include_local_absolute_path": True,
        "operation_receipt_does_not_include_body_hash": True,
        "operation_receipt_does_not_include_terminal_output": True,
        "operation_receipt_does_not_create_rating_rows": True,
        "operation_receipt_does_not_create_question_rows": True,
        "operation_receipt_does_not_create_disposal_receipt": True,
        "actual_human_review_operation_run": True if ready else False,
        "actual_human_review_run_here": True if ready else False,
    }


def build_p7_r54_ahr_cr09_actual_local_human_review_operation_receipt(
    *,
    reviewer_selection_form: Mapping[str, Any] | None = None,
    operation_receipt_input: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build CR09 actual local-only human review operation receipt intake.

    CR09 accepts only a body-free operation receipt.  Even when the receipt is
    accepted, actual evidence remains incomplete until sanitized rows, rating
    rows, question-observation rows, and disposal receipt are handled later.
    """

    cr08 = dict(reviewer_selection_form or build_p7_r54_ahr_cr08_reviewer_selection_form())
    assert_p7_r54_ahr_cr08_reviewer_selection_form_contract(cr08)
    receipt_fields = _cr09_actual_local_human_review_operation_receipt_fields(
        reviewer_selection_form=cr08,
        operation_receipt_input=operation_receipt_input,
    )
    ready = receipt_fields["operation_receipt_ready"] is True
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CR09_ACTUAL_LOCAL_HUMAN_REVIEW_OPERATION_RECEIPT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CR_STEP,
        "scope": P7_R54_AHR_CR_SCOPE,
        "policy_kind": P7_R54_AHR_CR_POLICY_KIND,
        "policy_section": P7_R54_AHR_CR09_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CR09_STEP_REF,
        "current_phase": P7_R54_AHR_CR_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cr09_actual_local_human_review_operation_receipt_intake_20260628",
        "review_session_id": _safe_review_session_id(review_session_id or cr08.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cr08_schema_version": cr08["schema_version"],
        "cr08_material_ref": cr08["material_id"],
        "cr08_next_required_step": cr08["next_required_step"],
        "cr08_reviewer_selection_form_status_ref": cr08["reviewer_selection_form_status_ref"],
        "cr08_reviewer_selection_form_ready": cr08["reviewer_selection_form_ready"],
        "cr08_reviewer_person_ref": cr08["reviewer_person_ref"],
        "cr08_reviewer_person_ref_present": cr08["reviewer_person_ref_present"],
        "cr08_reviewer_is_person": cr08["reviewer_is_person"],
        "cr08_reviewer_person_confirmed": cr08["reviewer_person_confirmed"],
        "cr08_selection_row_count_required": cr08["selection_row_count_required"],
        "cr08_selection_only": cr08["selection_only"],
        "cr08_free_text_allowed": cr08["free_text_allowed"],
        "cr08_question_text_allowed": cr08["question_text_allowed"],
        **_current_received_basis_fields(actual_basis=True),
        **_historical_basis_fields(),
        **receipt_fields,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_review_evidence_still_incomplete_until_rows_and_disposal": True,
        "actual_rating_or_question_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR_CR09_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_CR09_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_CR10_STEP_REF if ready else P7_R54_AHR_CR09_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    material.update(receipt_fields)
    material["actual_human_review_complete"] = False
    material["actual_review_evidence_complete"] = False
    material["actual_rating_rows_materialized_here"] = False
    material["actual_question_need_observation_rows_materialized_here"] = False
    material["actual_disposal_receipt_materialized_here"] = False
    material["disposal_verified"] = False
    material["p5_human_blind_qa_confirmed_final"] = False
    material["p5_confirmed_final"] = False
    material["p5_final_allowed"] = False
    material["p6_limited_human_readfeel_start_allowed"] = False
    material["p6_start_allowed"] = False
    material["p8_start_allowed"] = False
    material["r52_reintake_execution_requested_here"] = False
    material["actual_r52_reintake_execution_confirmed"] = False
    material["p7_complete"] = False
    material["release_allowed"] = False
    return material


def assert_p7_r54_ahr_cr09_actual_local_human_review_operation_receipt_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CR09_ACTUAL_LOCAL_HUMAN_REVIEW_OPERATION_RECEIPT_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CR09 actual local-only human review operation receipt",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CR09_ACTUAL_LOCAL_HUMAN_REVIEW_OPERATION_RECEIPT_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CR09_STEP_REF,
        operation_step_ref=P7_R54_AHR_CR09_STEP_REF,
        source="P7-R54-AHR-CR09 actual local-only human review operation receipt",
        allowed_true_false_flag_refs=P7_R54_AHR_CR09_ALLOWED_TRUE_OPERATION_FLAG_REFS,
    )
    if data.get("cr08_schema_version") != P7_R54_AHR_CR08_REVIEWER_SELECTION_FORM_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CR09 CR08 schema version changed")
    if data.get("cr08_reviewer_selection_form_ready") is True:
        if data.get("cr08_next_required_step") != P7_R54_AHR_CR09_STEP_REF:
            raise ValueError("P7-R54-AHR-CR09 ready CR08 must point to CR09")
    elif data.get("cr08_next_required_step") != P7_R54_AHR_CR08_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
        raise ValueError("P7-R54-AHR-CR09 blocked CR08 next step changed")
    _assert_current_received_basis_fields(data, actual_basis=True, source="P7-R54-AHR-CR09 operation receipt")
    _assert_historical_basis_fields(data, source="P7-R54-AHR-CR09 operation receipt")
    ready = data.get("operation_receipt_status_ref") == P7_R54_AHR_CR09_OPERATION_RECEIPT_ACCEPTED_STATUS_REF
    if data.get("operation_receipt_ready") is not ready:
        raise ValueError("P7-R54-AHR-CR09 ready flag changed")
    if tuple(data.get("operation_receipt_allowed_status_refs") or ()) != P7_R54_AHR_CR09_ALLOWED_OPERATION_RECEIPT_STATUS_REFS:
        raise ValueError("P7-R54-AHR-CR09 allowed status refs changed")
    blockers = list(data.get("operation_receipt_blocker_refs") or [])
    if data.get("operation_receipt_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-CR09 blocker count changed")
    _assert_true_fields(
        data,
        keys=(
            "operation_receipt_bodyfree_only",
            "operation_receipt_does_not_include_body",
            "operation_receipt_does_not_include_reviewer_free_text",
            "operation_receipt_does_not_include_question_text",
            "operation_receipt_does_not_include_local_absolute_path",
            "operation_receipt_does_not_include_body_hash",
            "operation_receipt_does_not_include_terminal_output",
            "operation_receipt_does_not_create_rating_rows",
            "operation_receipt_does_not_create_question_rows",
            "operation_receipt_does_not_create_disposal_receipt",
            "actual_human_review_completion_claim_blocked_here",
            "actual_review_evidence_still_incomplete_until_rows_and_disposal",
            "actual_rating_or_question_rows_claim_blocked_here",
            "disposal_receipt_claim_blocked_here",
            "r52_reintake_claim_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "p5_finalization_blocked_here",
        ),
        source="P7-R54-AHR-CR09 actual local-only human review operation receipt",
    )
    _assert_false_fields(
        data,
        keys=(
            "cr08_free_text_allowed",
            "cr08_question_text_allowed",
            "actual_human_review_complete",
            "actual_review_evidence_complete",
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "disposal_verified",
            "p5_human_blind_qa_confirmed_final",
            "p5_confirmed_final",
            "p5_final_allowed",
            "p6_limited_human_readfeel_start_allowed",
            "p6_start_allowed",
            "p8_start_allowed",
            "r52_reintake_execution_requested_here",
            "actual_r52_reintake_execution_confirmed",
            "p7_complete",
            "release_allowed",
        ),
        source="P7-R54-AHR-CR09 actual local-only human review operation receipt",
    )
    if ready:
        if blockers:
            raise ValueError("P7-R54-AHR-CR09 accepted receipt cannot carry blockers")
        if data.get("operation_receipt_reason_refs") != [P7_R54_AHR_CR09_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-CR09 ready reason changed")
        _assert_true_fields(
            data,
            keys=(
                "cr08_reviewer_selection_form_ready",
                "cr08_reviewer_person_ref_present",
                "cr08_reviewer_is_person",
                "cr08_reviewer_person_confirmed",
                "cr08_selection_only",
                "operation_receipt_input_provided",
                "operation_receipt_ref_present",
                "reviewer_person_ref_matches_cr08",
                "reviewer_is_person",
                "reviewer_person_confirmed",
                "reviewer_local_only_read_receipt_present",
                "actual_human_review_executed_by_person",
                "review_started_at_bucket_ref_present",
                "review_completed_at_bucket_ref_present",
                "reviewed_case_count_matches_manifest",
                "selection_row_count_matches_required",
                "local_only",
                "must_not_export",
                "selection_only",
                "actual_human_review_operation_run",
                "actual_human_review_run_here",
            ),
            source="P7-R54-AHR-CR09 accepted operation receipt",
        )
        if data.get("operation_receipt_input_forbidden_key_detected") is not False:
            raise ValueError("P7-R54-AHR-CR09 accepted receipt cannot have forbidden keys")
        if data.get("cr08_selection_row_count_required") != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-CR09 accepted receipt requires CR08 24-row form")
        if not data.get("operation_receipt_ref"):
            raise ValueError("P7-R54-AHR-CR09 accepted receipt requires operation receipt ref")
        if data.get("reviewer_person_ref") != data.get("cr08_reviewer_person_ref"):
            raise ValueError("P7-R54-AHR-CR09 reviewer ref must match CR08")
        if not data.get("review_started_at_bucket_ref"):
            raise ValueError("P7-R54-AHR-CR09 accepted receipt requires started bucket ref")
        if not data.get("review_completed_at_bucket_ref"):
            raise ValueError("P7-R54-AHR-CR09 accepted receipt requires completed bucket ref")
        if data.get("reviewed_case_count") != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-CR09 accepted receipt requires 24 reviewed cases")
        if data.get("selection_row_count") != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-CR09 accepted receipt requires 24 selection rows")
        if data.get("next_required_step") != P7_R54_AHR_CR10_STEP_REF:
            raise ValueError("P7-R54-AHR-CR09 ready next step changed")
    else:
        if not blockers:
            raise ValueError("P7-R54-AHR-CR09 blocked receipt must carry blockers")
        if data.get("operation_receipt_reason_refs") != []:
            raise ValueError("P7-R54-AHR-CR09 blocked receipt cannot carry ready reasons")
        _assert_false_fields(
            data,
            keys=(
                "operation_receipt_ref_present",
                "reviewer_person_ref_matches_cr08",
                "reviewer_is_person",
                "reviewer_person_confirmed",
                "reviewer_local_only_read_receipt_present",
                "actual_human_review_executed_by_person",
                "review_started_at_bucket_ref_present",
                "review_completed_at_bucket_ref_present",
                "local_only",
                "must_not_export",
                "selection_only",
                "actual_human_review_operation_run",
                "actual_human_review_run_here",
            ),
            source="P7-R54-AHR-CR09 blocked operation receipt",
        )
        if data.get("operation_receipt_ref") != "":
            raise ValueError("P7-R54-AHR-CR09 blocked receipt cannot expose operation receipt ref")
        if data.get("reviewer_person_ref") != "":
            raise ValueError("P7-R54-AHR-CR09 blocked receipt cannot expose reviewer person ref")
        if data.get("next_required_step") != P7_R54_AHR_CR09_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CR09 blocked next step changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CR09_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CR09 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CR09_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CR09 not-yet implemented steps changed")
    return True


def _dedupe_string_refs(values: Any, *, limit: int = 200, max_length: int = 240) -> list[str]:
    if isinstance(values, str):
        raw_values: Sequence[Any] = (values,)
    elif isinstance(values, Sequence) and not isinstance(values, (bytes, bytearray)):
        raw_values = values
    else:
        raw_values = ()
    result: list[str] = []
    seen: set[str] = set()
    for value in raw_values:
        ref = clean_identifier(value, default="", max_length=max_length)
        if not ref or ref in seen:
            continue
        result.append(ref)
        seen.add(ref)
        if len(result) >= limit:
            break
    return result


def _count_values(rows: Sequence[Mapping[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = str(row.get(field, ""))
        if not key:
            continue
        counts[key] = counts.get(key, 0) + 1
    return counts


def _expected_cr04_manifest_rows_by_case_ref() -> dict[str, dict[str, Any]]:
    manifest = build_p7_r54_ahr_cr04_current_24_case_manifest_refreeze()
    return {str(row.get("case_ref_id")): dict(row) for row in manifest.get("case_rows", [])}


def _clean_cr10_plan_candidate_flags(value: Any) -> dict[str, bool]:
    flags = {key: False for key in P7_R54_AHR_CR10_PLAN_CANDIDATE_FLAG_REFS}
    if isinstance(value, Mapping):
        for key in P7_R54_AHR_CR10_PLAN_CANDIDATE_FLAG_REFS:
            flags[key] = bool(value.get(key, False))
    flags["p8_implementation_spec_finalized_here"] = False
    return flags


def _coerce_axis_score(value: Any) -> tuple[float, bool]:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0, False
    if score < 0.0 or score > 1.0:
        return score, False
    return score, True


def _clean_axis_scores(raw_scores: Any) -> tuple[dict[str, float], bool]:
    if not isinstance(raw_scores, Mapping):
        return {axis_ref: 0.0 for axis_ref in P7_R54_AHR_CR08_RATING_AXIS_REFS}, False
    refs_match = set(str(key) for key in raw_scores.keys()) == set(P7_R54_AHR_CR08_RATING_AXIS_REFS)
    axis_scores: dict[str, float] = {}
    scores_valid = True
    for axis_ref in P7_R54_AHR_CR08_RATING_AXIS_REFS:
        score, valid = _coerce_axis_score(raw_scores.get(axis_ref))
        axis_scores[axis_ref] = score
        scores_valid = scores_valid and valid
    return axis_scores, bool(refs_match and scores_valid)


def build_p7_r54_ahr_cr10_bodyfree_selection_result_rows_input(
    *,
    operation_receipt_ref: Any = P7_R54_AHR_CR09_DEFAULT_OPERATION_RECEIPT_REF,
    reviewer_person_ref: Any = P7_R54_AHR_CR08_DEFAULT_REVIEWER_PERSON_REF,
    review_session_id: Any = P7_R54_AHR_CR_DEFAULT_REVIEW_SESSION_ID,
    verdict: Any = "PASS",
    question_need_primary_class: Any = "no_question_needed_emlis_can_observe",
    one_question_fit_ref: Any = "not_needed",
) -> list[dict[str, Any]]:
    """Build a default 24-row, body-free selection-only CR10 row input fixture.

    This helper creates selection rows only.  It does not create rating rows,
    question text, reviewer notes, disposal receipts, P5 finalization, P8 start,
    or release permission.
    """

    session_id = _safe_review_session_id(review_session_id)
    receipt_ref = clean_identifier(
        operation_receipt_ref, default=P7_R54_AHR_CR09_DEFAULT_OPERATION_RECEIPT_REF, max_length=240
    )
    reviewer_ref = clean_identifier(
        reviewer_person_ref, default=P7_R54_AHR_CR08_DEFAULT_REVIEWER_PERSON_REF, max_length=200
    )
    verdict_ref = clean_identifier(verdict, default="PASS", max_length=80)
    if verdict_ref not in P7_R54_AHR_CR10_VERDICT_OPTION_REFS:
        verdict_ref = "PASS"
    question_ref = clean_identifier(question_need_primary_class, default="no_question_needed_emlis_can_observe", max_length=160)
    if question_ref not in P7_R54_AHR_CR10_QUESTION_NEED_PRIMARY_CLASS_OPTION_REFS:
        question_ref = "no_question_needed_emlis_can_observe"
    one_question_ref = clean_identifier(one_question_fit_ref, default="not_needed", max_length=160)
    if one_question_ref not in P7_R54_AHR_CR10_ONE_QUESTION_FIT_OPTION_REFS:
        one_question_ref = "not_needed"
    manifest = build_p7_r54_ahr_cr04_current_24_case_manifest_refreeze()
    rows: list[dict[str, Any]] = []
    axis_scores = {axis_ref: 1.0 for axis_ref in P7_R54_AHR_CR08_RATING_AXIS_REFS}
    plan_flags = _clean_cr10_plan_candidate_flags({})
    for index, case_row in enumerate(manifest.get("case_rows", []), start=1):
        row = {
            "schema_version": P7_R54_AHR_CR10_SELECTION_RESULT_ROW_SCHEMA_VERSION,
            "review_session_id": session_id,
            "operation_receipt_ref": receipt_ref,
            "review_result_row_ref": f"cr10_review_result_row_{index:03d}",
            "case_ref_id": str(case_row.get("case_ref_id")),
            "blind_case_id": str(case_row.get("blind_case_id")),
            "packet_ref_id": str(case_row.get("packet_ref_id")),
            "reviewer_person_ref": reviewer_ref,
            "reviewed_at_bucket_ref": f"{P7_R54_AHR_CR10_DEFAULT_REVIEWED_AT_BUCKET_REF}_{index:03d}",
            "axis_scores": dict(axis_scores),
            "axis_score_count": len(P7_R54_AHR_CR08_RATING_AXIS_REFS),
            "verdict": verdict_ref,
            "sanitized_reason_ids": ["record_returned_as_natural_line"],
            "readfeel_blocker_ids": [],
            "execution_blocker_ids": [],
            "question_need_primary_class": question_ref,
            "ambiguity_kind_refs": ["no_material_ambiguity"],
            "one_question_fit_ref": one_question_ref,
            "repair_required_refs": ["no_repair_required"],
            "plan_candidate_flags": dict(plan_flags),
            "selection_only": True,
            "selection_only_row": True,
            "body_free": True,
        }
        row.update({key: False for key in P7_R54_AHR_CR10_ROW_BODYFREE_FALSE_FLAG_REFS})
        rows.append(row)
    return rows


def _validate_and_sanitize_cr10_selection_result_rows(
    rows: Sequence[Any],
    *,
    review_session_id: str,
    operation_receipt_ref: str,
    reviewer_person_ref: str,
) -> tuple[list[dict[str, Any]], list[str], bool]:
    blockers: list[str] = []
    sanitized_rows: list[dict[str, Any]] = []
    forbidden_detected_any = False
    expected_by_case_ref = _expected_cr04_manifest_rows_by_case_ref()
    if len(rows) != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
        blockers.append(P7_R54_AHR_CR10_SELECTION_ROW_COUNT_NOT_24_BLOCKER_REF)
    seen_case_refs: set[str] = set()
    seen_blind_ids: set[str] = set()
    seen_packet_ids: set[str] = set()
    for index, raw_row in enumerate(rows, start=1):
        if not isinstance(raw_row, Mapping):
            blockers.append(P7_R54_AHR_CR10_SELECTION_ROW_NOT_MAPPING_BLOCKER_REF)
            continue
        if _contains_forbidden_body_or_question_key(raw_row):
            forbidden_detected_any = True
            blockers.append(P7_R54_AHR_CR10_SELECTION_ROW_FORBIDDEN_KEY_BLOCKER_REF)
            continue
        case_ref_id = clean_identifier(raw_row.get("case_ref_id"), default="", max_length=120)
        blind_case_id = clean_identifier(raw_row.get("blind_case_id"), default="", max_length=120)
        packet_ref_id = clean_identifier(raw_row.get("packet_ref_id"), default="", max_length=120)
        expected = expected_by_case_ref.get(case_ref_id)
        if not expected:
            blockers.append(P7_R54_AHR_CR10_SELECTION_ROW_CASE_REF_NOT_IN_MANIFEST_BLOCKER_REF)
            continue
        if blind_case_id != expected.get("blind_case_id") or packet_ref_id != expected.get("packet_ref_id"):
            blockers.append(P7_R54_AHR_CR10_SELECTION_ROW_ID_MISMATCH_BLOCKER_REF)
        row_operation_receipt_ref = clean_identifier(raw_row.get("operation_receipt_ref"), default="", max_length=240)
        row_reviewer_person_ref = clean_identifier(raw_row.get("reviewer_person_ref"), default="", max_length=200)
        row_session_id = _safe_review_session_id(raw_row.get("review_session_id"))
        reviewed_at_bucket_ref = clean_identifier(raw_row.get("reviewed_at_bucket_ref"), default="", max_length=160)
        if row_operation_receipt_ref != operation_receipt_ref:
            blockers.append(P7_R54_AHR_CR10_SELECTION_ROW_OPERATION_RECEIPT_REF_MISMATCH_BLOCKER_REF)
        if row_reviewer_person_ref != reviewer_person_ref:
            blockers.append(P7_R54_AHR_CR10_SELECTION_ROW_REVIEWER_PERSON_REF_MISMATCH_BLOCKER_REF)
        if row_session_id != review_session_id:
            blockers.append(P7_R54_AHR_CR10_SELECTION_ROW_REVIEW_SESSION_ID_MISMATCH_BLOCKER_REF)
        if not reviewed_at_bucket_ref:
            blockers.append(P7_R54_AHR_CR10_SELECTION_ROW_REVIEWED_AT_REF_MISSING_BLOCKER_REF)
        axis_scores, axes_valid = _clean_axis_scores(raw_row.get("axis_scores"))
        if not axes_valid or raw_row.get("axis_score_count") != len(P7_R54_AHR_CR08_RATING_AXIS_REFS):
            blockers.append(P7_R54_AHR_CR10_SELECTION_ROW_AXIS_REFS_MISMATCH_BLOCKER_REF)
        if not all(0.0 <= score <= 1.0 for score in axis_scores.values()):
            blockers.append(P7_R54_AHR_CR10_SELECTION_ROW_AXIS_SCORE_INVALID_BLOCKER_REF)
        verdict = clean_identifier(raw_row.get("verdict"), default="", max_length=80)
        if verdict not in P7_R54_AHR_CR10_VERDICT_OPTION_REFS:
            blockers.append(P7_R54_AHR_CR10_SELECTION_ROW_VERDICT_NOT_ALLOWED_BLOCKER_REF)
        sanitized_reason_ids = _dedupe_string_refs(raw_row.get("sanitized_reason_ids") or (), limit=20, max_length=120)
        readfeel_blocker_ids = _dedupe_string_refs(raw_row.get("readfeel_blocker_ids") or (), limit=20, max_length=120)
        execution_blocker_ids = _dedupe_string_refs(raw_row.get("execution_blocker_ids") or (), limit=20, max_length=120)
        ambiguity_kind_refs = _dedupe_string_refs(raw_row.get("ambiguity_kind_refs") or (), limit=20, max_length=120)
        repair_required_refs = _dedupe_string_refs(raw_row.get("repair_required_refs") or (), limit=20, max_length=160)
        question_need_primary_class = clean_identifier(
            raw_row.get("question_need_primary_class"), default="", max_length=160
        )
        one_question_fit_ref = clean_identifier(raw_row.get("one_question_fit_ref"), default="", max_length=160)
        if any(item not in P7_R54_AHR_CR10_SANITIZED_REASON_ID_OPTION_REFS for item in sanitized_reason_ids):
            blockers.append(P7_R54_AHR_CR10_SELECTION_ROW_OPTION_NOT_ALLOWED_BLOCKER_REF)
        if any(item not in P7_R54_AHR_CR10_READFEEL_BLOCKER_ID_OPTION_REFS for item in readfeel_blocker_ids):
            blockers.append(P7_R54_AHR_CR10_SELECTION_ROW_OPTION_NOT_ALLOWED_BLOCKER_REF)
        if any(item not in P7_R54_AHR_CR10_EXECUTION_BLOCKER_ID_OPTION_REFS for item in execution_blocker_ids):
            blockers.append(P7_R54_AHR_CR10_SELECTION_ROW_OPTION_NOT_ALLOWED_BLOCKER_REF)
        if question_need_primary_class not in P7_R54_AHR_CR10_QUESTION_NEED_PRIMARY_CLASS_OPTION_REFS:
            blockers.append(P7_R54_AHR_CR10_SELECTION_ROW_OPTION_NOT_ALLOWED_BLOCKER_REF)
        if any(item not in P7_R54_AHR_CR10_AMBIGUITY_KIND_OPTION_REFS for item in ambiguity_kind_refs):
            blockers.append(P7_R54_AHR_CR10_SELECTION_ROW_OPTION_NOT_ALLOWED_BLOCKER_REF)
        if one_question_fit_ref not in P7_R54_AHR_CR10_ONE_QUESTION_FIT_OPTION_REFS:
            blockers.append(P7_R54_AHR_CR10_SELECTION_ROW_OPTION_NOT_ALLOWED_BLOCKER_REF)
        if any(item not in P7_R54_AHR_CR10_REPAIR_REQUIRED_OPTION_REFS for item in repair_required_refs):
            blockers.append(P7_R54_AHR_CR10_SELECTION_ROW_OPTION_NOT_ALLOWED_BLOCKER_REF)
        if raw_row.get("selection_only") is not True or raw_row.get("selection_only_row") is not True:
            blockers.append(P7_R54_AHR_CR10_SELECTION_ROW_SELECTION_ONLY_FALSE_BLOCKER_REF)
        if raw_row.get("body_free") is not True:
            blockers.append(P7_R54_AHR_CR10_SELECTION_ROW_BODY_FREE_FALSE_BLOCKER_REF)
        for flag_ref in P7_R54_AHR_CR10_ROW_BODYFREE_FALSE_FLAG_REFS:
            if raw_row.get(flag_ref) is not False:
                blockers.append(P7_R54_AHR_CR10_SELECTION_ROW_FORBIDDEN_KEY_BLOCKER_REF)
        seen_case_refs.add(case_ref_id)
        seen_blind_ids.add(blind_case_id)
        seen_packet_ids.add(packet_ref_id)
        sanitized_row: dict[str, Any] = {
            "schema_version": P7_R54_AHR_CR10_SELECTION_RESULT_ROW_SCHEMA_VERSION,
            "review_session_id": review_session_id,
            "operation_receipt_ref": operation_receipt_ref,
            "review_result_row_ref": clean_identifier(
                raw_row.get("review_result_row_ref"), default=f"cr10_review_result_row_{index:03d}", max_length=120
            ),
            "case_ref_id": case_ref_id,
            "blind_case_id": blind_case_id,
            "packet_ref_id": packet_ref_id,
            "reviewer_person_ref": reviewer_person_ref,
            "reviewed_at_bucket_ref": reviewed_at_bucket_ref,
            "axis_scores": axis_scores,
            "axis_score_count": len(P7_R54_AHR_CR08_RATING_AXIS_REFS),
            "verdict": verdict,
            "sanitized_reason_ids": sanitized_reason_ids,
            "readfeel_blocker_ids": readfeel_blocker_ids,
            "execution_blocker_ids": execution_blocker_ids,
            "question_need_primary_class": question_need_primary_class,
            "ambiguity_kind_refs": ambiguity_kind_refs,
            "one_question_fit_ref": one_question_fit_ref,
            "repair_required_refs": repair_required_refs,
            "plan_candidate_flags": _clean_cr10_plan_candidate_flags(raw_row.get("plan_candidate_flags")),
            "selection_only": True,
            "selection_only_row": True,
            "body_free": True,
        }
        sanitized_row.update({key: False for key in P7_R54_AHR_CR10_ROW_BODYFREE_FALSE_FLAG_REFS})
        sanitized_rows.append(sanitized_row)
    if len(seen_case_refs) != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
        blockers.append(P7_R54_AHR_CR10_SELECTION_ROW_UNIQUE_REFS_NOT_24_BLOCKER_REF)
    if len(seen_blind_ids) != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
        blockers.append(P7_R54_AHR_CR10_SELECTION_ROW_UNIQUE_REFS_NOT_24_BLOCKER_REF)
    if len(seen_packet_ids) != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
        blockers.append(P7_R54_AHR_CR10_SELECTION_ROW_UNIQUE_REFS_NOT_24_BLOCKER_REF)
    deduped_blockers = _dedupe_string_refs(blockers, limit=200, max_length=240)
    if deduped_blockers:
        return [], deduped_blockers, forbidden_detected_any
    return sanitized_rows, [], forbidden_detected_any


def build_p7_r54_ahr_cr10_sanitized_selection_only_result_rows_intake(
    *,
    actual_local_human_review_operation_receipt: Mapping[str, Any] | None = None,
    selection_result_rows: Sequence[Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build CR10 body-free sanitized selection-only result rows intake."""

    cr09 = dict(
        actual_local_human_review_operation_receipt
        or build_p7_r54_ahr_cr09_actual_local_human_review_operation_receipt()
    )
    assert_p7_r54_ahr_cr09_actual_local_human_review_operation_receipt_contract(cr09)
    session_id = _safe_review_session_id(review_session_id)
    rows_provided = selection_result_rows is not None
    rows_input = list(selection_result_rows or [])
    operation_receipt_ref = clean_identifier(cr09.get("operation_receipt_ref"), default="", max_length=240)
    reviewer_person_ref = clean_identifier(cr09.get("reviewer_person_ref"), default="", max_length=200)
    sanitized_rows, row_blockers, forbidden_detected = _validate_and_sanitize_cr10_selection_result_rows(
        rows_input,
        review_session_id=session_id,
        operation_receipt_ref=operation_receipt_ref,
        reviewer_person_ref=reviewer_person_ref,
    )
    blockers: list[str] = []
    if cr09.get("operation_receipt_ready") is not True:
        blockers.append(P7_R54_AHR_CR10_CR09_NOT_READY_BLOCKER_REF)
    if cr09.get("next_required_step") != P7_R54_AHR_CR10_STEP_REF:
        blockers.append(P7_R54_AHR_CR10_CR09_NEXT_STEP_NOT_CR10_BLOCKER_REF)
    if cr09.get("actual_human_review_executed_by_person") is not True:
        blockers.append(P7_R54_AHR_CR10_CR09_PERSON_EXECUTION_NOT_CONFIRMED_BLOCKER_REF)
    if cr09.get("reviewed_case_count") != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
        blockers.append(P7_R54_AHR_CR10_CR09_REVIEWED_CASE_COUNT_NOT_24_BLOCKER_REF)
    if cr09.get("selection_row_count") != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
        blockers.append(P7_R54_AHR_CR10_CR09_SELECTION_ROW_COUNT_NOT_24_BLOCKER_REF)
    if not rows_provided:
        blockers.append(P7_R54_AHR_CR10_SELECTION_ROWS_INPUT_MISSING_BLOCKER_REF)
    blockers.extend(row_blockers)
    blockers = _dedupe_string_refs(blockers, limit=200, max_length=240)
    ready = not blockers
    rows_for_output = sanitized_rows if ready else []
    row_refs = [str(row.get("review_result_row_ref")) for row in rows_for_output]
    case_refs = [str(row.get("case_ref_id")) for row in rows_for_output]
    blind_ids = [str(row.get("blind_case_id")) for row in rows_for_output]
    packet_refs = [str(row.get("packet_ref_id")) for row in rows_for_output]
    reviewer_refs = _dedupe_string_refs([row.get("reviewer_person_ref") for row in rows_for_output], limit=24, max_length=200)
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CR10_SANITIZED_SELECTION_ONLY_RESULT_ROWS_INTAKE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CR_STEP,
        "scope": P7_R54_AHR_CR_SCOPE,
        "policy_kind": P7_R54_AHR_CR_POLICY_KIND,
        "policy_section": P7_R54_AHR_CR10_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CR10_STEP_REF,
        "current_phase": P7_R54_AHR_CR_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cr10_sanitized_selection_only_result_rows_intake_20260628",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cr09_schema_version": cr09.get("schema_version"),
        "cr09_material_ref": cr09.get("material_id"),
        "cr09_next_required_step": cr09.get("next_required_step"),
        "cr09_operation_receipt_status_ref": cr09.get("operation_receipt_status_ref"),
        "cr09_operation_receipt_ready": cr09.get("operation_receipt_ready"),
        "cr09_operation_receipt_ref": cr09.get("operation_receipt_ref"),
        "cr09_operation_receipt_ref_present": cr09.get("operation_receipt_ref_present"),
        "cr09_reviewer_person_ref": cr09.get("reviewer_person_ref"),
        "cr09_actual_human_review_executed_by_person": cr09.get("actual_human_review_executed_by_person"),
        "cr09_actual_human_review_run_here": cr09.get("actual_human_review_run_here"),
        "cr09_reviewed_case_count": cr09.get("reviewed_case_count"),
        "cr09_selection_row_count": cr09.get("selection_row_count"),
        "cr09_local_only": cr09.get("local_only"),
        "cr09_must_not_export": cr09.get("must_not_export"),
        "cr09_selection_only": cr09.get("selection_only"),
        **_current_received_basis_fields(actual_basis=True),
        **_historical_basis_fields(),
        "sanitized_selection_only_result_rows_intake_status_ref": (
            P7_R54_AHR_CR10_SANITIZED_ROWS_ACCEPTED_STATUS_REF
            if ready
            else P7_R54_AHR_CR10_SANITIZED_ROWS_BLOCKED_STATUS_REF
        ),
        "sanitized_selection_only_result_rows_allowed_status_refs": list(
            P7_R54_AHR_CR10_ALLOWED_SANITIZED_ROWS_STATUS_REFS
        ),
        "sanitized_selection_only_result_rows_ready": ready,
        "sanitized_selection_only_result_rows_reason_refs": [P7_R54_AHR_CR10_READY_REASON_REF] if ready else [],
        "sanitized_selection_only_result_rows_blocker_refs": blockers,
        "sanitized_selection_only_result_rows_blocker_ref_count": len(blockers),
        "selection_rows_input_provided": rows_provided,
        "selection_rows_input_forbidden_key_detected": forbidden_detected,
        "required_case_count": P7_R54_AHR_CR_REQUIRED_CASE_COUNT,
        "received_selection_result_row_count": len(rows_input),
        "selection_result_row_count": len(rows_for_output),
        "sanitized_review_result_row_count": len(rows_for_output),
        "review_result_rows": rows_for_output,
        "review_result_row_refs": row_refs,
        "review_result_row_ref_count": len(row_refs),
        "case_ref_ids": case_refs,
        "case_ref_id_count": len(case_refs),
        "case_ref_ids_unique": len(set(case_refs)) == len(case_refs) == P7_R54_AHR_CR_REQUIRED_CASE_COUNT,
        "blind_case_ids": blind_ids,
        "blind_case_id_count": len(blind_ids),
        "blind_case_ids_unique": len(set(blind_ids)) == len(blind_ids) == P7_R54_AHR_CR_REQUIRED_CASE_COUNT,
        "packet_ref_ids": packet_refs,
        "packet_ref_id_count": len(packet_refs),
        "packet_ref_ids_unique": len(set(packet_refs)) == len(packet_refs) == P7_R54_AHR_CR_REQUIRED_CASE_COUNT,
        "reviewer_person_refs": reviewer_refs,
        "reviewer_person_ref_count": len(reviewer_refs),
        "reviewed_at_bucket_refs_present": ready,
        "axis_refs": list(P7_R54_AHR_CR08_RATING_AXIS_REFS),
        "axis_count": len(P7_R54_AHR_CR08_RATING_AXIS_REFS),
        "axis_score_count_per_row": len(P7_R54_AHR_CR08_RATING_AXIS_REFS) if ready else 0,
        "rating_axis_target_thresholds": dict(P7_R54_AHR_CR08_RATING_AXIS_TARGET_THRESHOLDS),
        "verdict_option_refs": list(P7_R54_AHR_CR10_VERDICT_OPTION_REFS),
        "verdict_option_count": len(P7_R54_AHR_CR10_VERDICT_OPTION_REFS),
        "sanitized_reason_id_option_refs": list(P7_R54_AHR_CR10_SANITIZED_REASON_ID_OPTION_REFS),
        "sanitized_reason_id_option_count": len(P7_R54_AHR_CR10_SANITIZED_REASON_ID_OPTION_REFS),
        "readfeel_blocker_id_option_refs": list(P7_R54_AHR_CR10_READFEEL_BLOCKER_ID_OPTION_REFS),
        "readfeel_blocker_id_option_count": len(P7_R54_AHR_CR10_READFEEL_BLOCKER_ID_OPTION_REFS),
        "execution_blocker_id_option_refs": list(P7_R54_AHR_CR10_EXECUTION_BLOCKER_ID_OPTION_REFS),
        "execution_blocker_id_option_count": len(P7_R54_AHR_CR10_EXECUTION_BLOCKER_ID_OPTION_REFS),
        "question_need_primary_class_options": list(P7_R54_AHR_CR10_QUESTION_NEED_PRIMARY_CLASS_OPTION_REFS),
        "question_need_primary_class_option_count": len(P7_R54_AHR_CR10_QUESTION_NEED_PRIMARY_CLASS_OPTION_REFS),
        "ambiguity_kind_option_refs": list(P7_R54_AHR_CR10_AMBIGUITY_KIND_OPTION_REFS),
        "ambiguity_kind_option_count": len(P7_R54_AHR_CR10_AMBIGUITY_KIND_OPTION_REFS),
        "one_question_fit_option_refs": list(P7_R54_AHR_CR10_ONE_QUESTION_FIT_OPTION_REFS),
        "one_question_fit_option_count": len(P7_R54_AHR_CR10_ONE_QUESTION_FIT_OPTION_REFS),
        "repair_required_option_refs": list(P7_R54_AHR_CR10_REPAIR_REQUIRED_OPTION_REFS),
        "repair_required_option_count": len(P7_R54_AHR_CR10_REPAIR_REQUIRED_OPTION_REFS),
        "plan_candidate_flag_refs": list(P7_R54_AHR_CR10_PLAN_CANDIDATE_FLAG_REFS),
        "plan_candidate_flag_count": len(P7_R54_AHR_CR10_PLAN_CANDIDATE_FLAG_REFS),
        "verdict_counts": _count_values(rows_for_output, "verdict") if ready else {},
        "question_need_primary_class_counts": _count_values(rows_for_output, "question_need_primary_class") if ready else {},
        "rows_match_24_case_manifest": ready,
        "rows_bodyfree_only": ready,
        "rows_selection_only": ready,
        "rows_have_required_axis_scores": ready,
        "rows_have_allowed_verdict_refs": ready,
        "rows_have_allowed_question_observation_refs": ready,
        "rows_have_no_body_or_question_or_path_or_hash": ready,
        "sanitized_selection_only_result_rows_intaken_here": ready,
        "actual_sanitized_review_result_rows_intaken_here": ready,
        "actual_human_review_executed_by_person": cr09.get("actual_human_review_executed_by_person") is True and ready,
        "actual_human_review_run_here": False,
        "actual_review_evidence_complete": False,
        "rating_row_normalization_allowed_next": ready,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "disposal_verified": False,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR_CR10_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CR09_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(
            P7_R54_AHR_CR10_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CR09_NOT_YET_IMPLEMENTED_STEPS
        ),
        "next_required_step": P7_R54_AHR_CR11_STEP_REF if ready else P7_R54_AHR_CR10_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    material["actual_human_review_executed_by_person"] = cr09.get("actual_human_review_executed_by_person") is True and ready
    material["actual_human_review_run_here"] = False
    material["actual_review_evidence_complete"] = False
    material["actual_rating_rows_materialized_here"] = False
    material["actual_question_need_observation_rows_materialized_here"] = False
    material["actual_disposal_receipt_materialized_here"] = False
    material["disposal_verified"] = False
    material["p5_human_blind_qa_confirmed_final"] = False
    material["p5_confirmed_final"] = False
    material["p5_final_allowed"] = False
    material["p6_limited_human_readfeel_start_allowed"] = False
    material["p6_start_allowed"] = False
    material["p8_start_allowed"] = False
    material["r52_reintake_execution_requested_here"] = False
    material["actual_r52_reintake_execution_confirmed"] = False
    material["p7_complete"] = False
    material["release_allowed"] = False
    return material


def assert_p7_r54_ahr_cr10_sanitized_selection_only_result_rows_intake_contract(
    data: Mapping[str, Any]
) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CR10_SANITIZED_SELECTION_ONLY_RESULT_ROWS_INTAKE_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CR10 sanitized selection-only result rows intake",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CR10_SANITIZED_SELECTION_ONLY_RESULT_ROWS_INTAKE_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CR10_STEP_REF,
        operation_step_ref=P7_R54_AHR_CR10_STEP_REF,
        source="P7-R54-AHR-CR10 sanitized selection-only result rows intake",
        allowed_true_false_flag_refs=P7_R54_AHR_CR10_ALLOWED_TRUE_OPERATION_FLAG_REFS,
    )
    if data.get("cr09_schema_version") != P7_R54_AHR_CR09_ACTUAL_LOCAL_HUMAN_REVIEW_OPERATION_RECEIPT_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CR10 CR09 schema version changed")
    if data.get("cr09_operation_receipt_ready") is True:
        if data.get("cr09_next_required_step") != P7_R54_AHR_CR10_STEP_REF:
            raise ValueError("P7-R54-AHR-CR10 ready CR09 must point to CR10")
    elif data.get("cr09_next_required_step") != P7_R54_AHR_CR09_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
        raise ValueError("P7-R54-AHR-CR10 blocked CR09 next step changed")
    _assert_current_received_basis_fields(data, actual_basis=True, source="P7-R54-AHR-CR10 sanitized rows")
    _assert_historical_basis_fields(data, source="P7-R54-AHR-CR10 sanitized rows")
    ready = data.get("sanitized_selection_only_result_rows_intake_status_ref") == P7_R54_AHR_CR10_SANITIZED_ROWS_ACCEPTED_STATUS_REF
    if data.get("sanitized_selection_only_result_rows_ready") is not ready:
        raise ValueError("P7-R54-AHR-CR10 ready flag changed")
    if tuple(data.get("sanitized_selection_only_result_rows_allowed_status_refs") or ()) != (
        P7_R54_AHR_CR10_ALLOWED_SANITIZED_ROWS_STATUS_REFS
    ):
        raise ValueError("P7-R54-AHR-CR10 allowed status refs changed")
    blockers = list(data.get("sanitized_selection_only_result_rows_blocker_refs") or [])
    if data.get("sanitized_selection_only_result_rows_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-CR10 blocker count changed")
    _assert_true_fields(
        data,
        keys=(
            "r52_reintake_claim_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "p5_finalization_blocked_here",
        ),
        source="P7-R54-AHR-CR10 sanitized selection-only result rows intake",
    )
    _assert_false_fields(
        data,
        keys=(
            "actual_human_review_run_here",
            "actual_review_evidence_complete",
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "disposal_verified",
            "p5_human_blind_qa_confirmed_final",
            "p5_confirmed_final",
            "p5_final_allowed",
            "p6_limited_human_readfeel_start_allowed",
            "p6_start_allowed",
            "p8_start_allowed",
            "r52_reintake_execution_requested_here",
            "actual_r52_reintake_execution_confirmed",
            "p7_complete",
            "release_allowed",
        ),
        source="P7-R54-AHR-CR10 sanitized selection-only result rows intake",
    )
    if ready:
        if blockers:
            raise ValueError("P7-R54-AHR-CR10 ready rows cannot carry blockers")
        if data.get("sanitized_selection_only_result_rows_reason_refs") != [P7_R54_AHR_CR10_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-CR10 ready reason changed")
        _assert_true_fields(
            data,
            keys=(
                "cr09_operation_receipt_ready",
                "cr09_operation_receipt_ref_present",
                "cr09_actual_human_review_executed_by_person",
                "cr09_actual_human_review_run_here",
                "cr09_local_only",
                "cr09_must_not_export",
                "cr09_selection_only",
                "selection_rows_input_provided",
                "case_ref_ids_unique",
                "blind_case_ids_unique",
                "packet_ref_ids_unique",
                "reviewed_at_bucket_refs_present",
                "rows_match_24_case_manifest",
                "rows_bodyfree_only",
                "rows_selection_only",
                "rows_have_required_axis_scores",
                "rows_have_allowed_verdict_refs",
                "rows_have_allowed_question_observation_refs",
                "rows_have_no_body_or_question_or_path_or_hash",
                "sanitized_selection_only_result_rows_intaken_here",
                "actual_sanitized_review_result_rows_intaken_here",
                "actual_human_review_executed_by_person",
                "rating_row_normalization_allowed_next",
            ),
            source="P7-R54-AHR-CR10 accepted sanitized rows",
        )
        if data.get("selection_rows_input_forbidden_key_detected") is not False:
            raise ValueError("P7-R54-AHR-CR10 ready rows cannot have forbidden input keys")
        for field in (
            "received_selection_result_row_count",
            "selection_result_row_count",
            "sanitized_review_result_row_count",
            "review_result_row_ref_count",
            "case_ref_id_count",
            "blind_case_id_count",
            "packet_ref_id_count",
        ):
            if data.get(field) != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
                raise ValueError(f"P7-R54-AHR-CR10 {field} changed")
        if tuple(data.get("axis_refs") or ()) != P7_R54_AHR_CR08_RATING_AXIS_REFS:
            raise ValueError("P7-R54-AHR-CR10 axis refs changed")
        if data.get("rating_axis_target_thresholds") != P7_R54_AHR_CR08_RATING_AXIS_TARGET_THRESHOLDS:
            raise ValueError("P7-R54-AHR-CR10 axis thresholds changed")
        for row in data.get("review_result_rows") or []:
            if not isinstance(row, Mapping):
                raise ValueError("P7-R54-AHR-CR10 row must be mapping")
            _assert_required_fields(
                row,
                required=P7_R54_AHR_CR10_SELECTION_RESULT_ROW_REQUIRED_FIELD_REFS,
                source="P7-R54-AHR-CR10 selection result row",
            )
            if row.get("schema_version") != P7_R54_AHR_CR10_SELECTION_RESULT_ROW_SCHEMA_VERSION:
                raise ValueError("P7-R54-AHR-CR10 row schema changed")
            if row.get("body_free") is not True or row.get("selection_only") is not True or row.get("selection_only_row") is not True:
                raise ValueError("P7-R54-AHR-CR10 row must remain body-free selection-only")
            for key in P7_R54_AHR_CR10_ROW_BODYFREE_FALSE_FLAG_REFS:
                if row.get(key) is not False:
                    raise ValueError(f"P7-R54-AHR-CR10 row must keep {key}=False")
            if set((row.get("axis_scores") or {}).keys()) != set(P7_R54_AHR_CR08_RATING_AXIS_REFS):
                raise ValueError("P7-R54-AHR-CR10 row axis refs changed")
            if row.get("axis_score_count") != len(P7_R54_AHR_CR08_RATING_AXIS_REFS):
                raise ValueError("P7-R54-AHR-CR10 row axis score count changed")
            if row.get("verdict") not in P7_R54_AHR_CR10_VERDICT_OPTION_REFS:
                raise ValueError("P7-R54-AHR-CR10 row verdict changed")
            if row.get("question_need_primary_class") not in P7_R54_AHR_CR10_QUESTION_NEED_PRIMARY_CLASS_OPTION_REFS:
                raise ValueError("P7-R54-AHR-CR10 row question class changed")
            if row.get("one_question_fit_ref") not in P7_R54_AHR_CR10_ONE_QUESTION_FIT_OPTION_REFS:
                raise ValueError("P7-R54-AHR-CR10 row one question fit changed")
            if set(row.get("plan_candidate_flags") or {}) != set(P7_R54_AHR_CR10_PLAN_CANDIDATE_FLAG_REFS):
                raise ValueError("P7-R54-AHR-CR10 row plan flag refs changed")
            if (row.get("plan_candidate_flags") or {}).get("p8_implementation_spec_finalized_here") is not False:
                raise ValueError("P7-R54-AHR-CR10 row must not finalize P8 implementation spec")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CR10_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CR10 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CR10_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CR10 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_CR11_STEP_REF:
            raise ValueError("P7-R54-AHR-CR10 ready next step changed")
    else:
        if data.get("sanitized_selection_only_result_rows_intake_status_ref") != P7_R54_AHR_CR10_SANITIZED_ROWS_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-CR10 blocked status changed")
        if not blockers:
            raise ValueError("P7-R54-AHR-CR10 blocked rows must carry blockers")
        if data.get("sanitized_selection_only_result_rows_reason_refs") != []:
            raise ValueError("P7-R54-AHR-CR10 blocked rows cannot carry ready reasons")
        if data.get("review_result_rows") != [] or data.get("sanitized_review_result_row_count") != 0:
            raise ValueError("P7-R54-AHR-CR10 blocked rows must not carry sanitized rows")
        if data.get("next_required_step") != P7_R54_AHR_CR10_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CR10 blocked next step changed")
    return True


def _rating_rows_from_cr10_sanitized_rows(
    rows: Sequence[Any], *, review_session_id: str
) -> tuple[list[dict[str, Any]], list[str]]:
    blockers: list[str] = []
    rating_rows: list[dict[str, Any]] = []
    for index, raw_row in enumerate(rows, start=1):
        if not isinstance(raw_row, Mapping):
            blockers.append(P7_R54_AHR_CR11_SOURCE_ROW_INVALID_BLOCKER_REF)
            continue
        if _contains_forbidden_body_or_question_key(raw_row):
            blockers.append(P7_R54_AHR_CR11_SOURCE_ROW_FORBIDDEN_KEY_BLOCKER_REF)
            continue
        if raw_row.get("schema_version") != P7_R54_AHR_CR10_SELECTION_RESULT_ROW_SCHEMA_VERSION:
            blockers.append(P7_R54_AHR_CR11_SOURCE_ROW_INVALID_BLOCKER_REF)
            continue
        axis_scores, axes_valid = _clean_axis_scores(raw_row.get("axis_scores"))
        if not axes_valid:
            blockers.append(P7_R54_AHR_CR11_SOURCE_ROW_INVALID_BLOCKER_REF)
        verdict = clean_identifier(raw_row.get("verdict"), default="", max_length=80)
        if verdict not in P7_R54_AHR_CR10_VERDICT_OPTION_REFS:
            blockers.append(P7_R54_AHR_CR11_SOURCE_ROW_INVALID_BLOCKER_REF)
        axis_targets = dict(P7_R54_AHR_CR08_RATING_AXIS_TARGET_THRESHOLDS)
        below_target_axis_refs = [
            axis_ref for axis_ref, target in axis_targets.items() if float(axis_scores.get(axis_ref, 0.0)) < float(target)
        ]
        axis_pass_flags = {axis_ref: axis_ref not in below_target_axis_refs for axis_ref in P7_R54_AHR_CR08_RATING_AXIS_REFS}
        rating_row: dict[str, Any] = {
            "schema_version": P7_R54_AHR_CR11_RATING_ROW_SCHEMA_VERSION,
            "review_session_id": review_session_id,
            "rating_row_ref": f"cr11_rating_row_{index:03d}",
            "source_review_result_row_ref": clean_identifier(
                raw_row.get("review_result_row_ref"), default=f"cr10_review_result_row_{index:03d}", max_length=120
            ),
            "case_ref_id": clean_identifier(raw_row.get("case_ref_id"), default="", max_length=120),
            "blind_case_id": clean_identifier(raw_row.get("blind_case_id"), default="", max_length=120),
            "packet_ref_id": clean_identifier(raw_row.get("packet_ref_id"), default="", max_length=120),
            "axis_scores": axis_scores,
            "axis_targets": axis_targets,
            "axis_score_count": len(P7_R54_AHR_CR08_RATING_AXIS_REFS),
            "below_target_axis_refs": below_target_axis_refs,
            "below_target_axis_ref_count": len(below_target_axis_refs),
            "axis_pass_flags": axis_pass_flags,
            "axis_pass_flag_count": len(axis_pass_flags),
            "all_axis_scores_at_or_above_target": not below_target_axis_refs,
            "verdict": verdict,
            "sanitized_reason_ids": _dedupe_string_refs(raw_row.get("sanitized_reason_ids") or (), limit=20, max_length=120),
            "readfeel_blocker_ids": _dedupe_string_refs(raw_row.get("readfeel_blocker_ids") or (), limit=20, max_length=120),
            "execution_blocker_ids": _dedupe_string_refs(raw_row.get("execution_blocker_ids") or (), limit=20, max_length=120),
            "question_need_primary_class": clean_identifier(
                raw_row.get("question_need_primary_class"), default="", max_length=160
            ),
            "one_question_fit_ref": clean_identifier(raw_row.get("one_question_fit_ref"), default="", max_length=160),
            "repair_required_refs": _dedupe_string_refs(raw_row.get("repair_required_refs") or (), limit=20, max_length=160),
            "plan_candidate_flags": _clean_cr10_plan_candidate_flags(raw_row.get("plan_candidate_flags")),
            "body_free": True,
        }
        rating_row.update({key: False for key in P7_R54_AHR_CR11_RATING_ROW_BODYFREE_FALSE_FLAG_REFS})
        rating_rows.append(rating_row)
    if len(rating_rows) != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
        blockers.append(P7_R54_AHR_CR11_CR10_SANITIZED_ROW_COUNT_NOT_24_BLOCKER_REF)
    return ([] if blockers else rating_rows), _dedupe_string_refs(blockers, limit=200, max_length=240)


def _average_axis_scores(rating_rows: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    if not rating_rows:
        return {axis_ref: 0.0 for axis_ref in P7_R54_AHR_CR08_RATING_AXIS_REFS}
    averages: dict[str, float] = {}
    for axis_ref in P7_R54_AHR_CR08_RATING_AXIS_REFS:
        total = sum(float((row.get("axis_scores") or {}).get(axis_ref, 0.0)) for row in rating_rows)
        averages[axis_ref] = round(total / len(rating_rows), 4)
    return averages


def _below_target_axis_counts(rating_rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = {axis_ref: 0 for axis_ref in P7_R54_AHR_CR08_RATING_AXIS_REFS}
    for row in rating_rows:
        for axis_ref in row.get("below_target_axis_refs") or []:
            if axis_ref in counts:
                counts[axis_ref] += 1
    return counts


def build_p7_r54_ahr_cr11_rating_row_normalization(
    *,
    sanitized_selection_only_result_rows_intake: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build CR11 body-free rating row normalization from CR10 sanitized rows."""

    cr10 = dict(sanitized_selection_only_result_rows_intake or build_p7_r54_ahr_cr10_sanitized_selection_only_result_rows_intake())
    assert_p7_r54_ahr_cr10_sanitized_selection_only_result_rows_intake_contract(cr10)
    session_id = _safe_review_session_id(review_session_id)
    cr10_ready = cr10.get("sanitized_selection_only_result_rows_ready") is True
    rating_rows, row_blockers = _rating_rows_from_cr10_sanitized_rows(
        cr10.get("review_result_rows") or (), review_session_id=session_id
    )
    blockers: list[str] = []
    if not cr10_ready:
        blockers.append(P7_R54_AHR_CR11_CR10_NOT_READY_BLOCKER_REF)
    if cr10.get("next_required_step") != P7_R54_AHR_CR11_STEP_REF:
        blockers.append(P7_R54_AHR_CR11_CR10_NEXT_STEP_NOT_CR11_BLOCKER_REF)
    if cr10.get("actual_human_review_executed_by_person") is not True:
        blockers.append(P7_R54_AHR_CR11_CR10_PERSON_EXECUTION_NOT_CONFIRMED_BLOCKER_REF)
    if cr10.get("sanitized_review_result_row_count") != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
        blockers.append(P7_R54_AHR_CR11_CR10_SANITIZED_ROW_COUNT_NOT_24_BLOCKER_REF)
    blockers.extend(row_blockers)
    blockers = _dedupe_string_refs(blockers, limit=200, max_length=240)
    ready = not blockers
    rows_for_output = rating_rows if ready else []
    rating_row_refs = [str(row.get("rating_row_ref")) for row in rows_for_output]
    source_refs = [str(row.get("source_review_result_row_ref")) for row in rows_for_output]
    case_refs = [str(row.get("case_ref_id")) for row in rows_for_output]
    blind_ids = [str(row.get("blind_case_id")) for row in rows_for_output]
    packet_refs = [str(row.get("packet_ref_id")) for row in rows_for_output]
    averages = _average_axis_scores(rows_for_output) if ready else _average_axis_scores(())
    overall_average = round(sum(averages.values()) / len(averages), 4) if averages else 0.0
    verdict_counts = _count_values(rows_for_output, "verdict") if ready else {}
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CR11_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CR_STEP,
        "scope": P7_R54_AHR_CR_SCOPE,
        "policy_kind": P7_R54_AHR_CR_POLICY_KIND,
        "policy_section": P7_R54_AHR_CR11_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CR11_STEP_REF,
        "current_phase": P7_R54_AHR_CR_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cr11_rating_row_normalization_20260628",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cr10_schema_version": cr10.get("schema_version"),
        "cr10_material_ref": cr10.get("material_id"),
        "cr10_next_required_step": cr10.get("next_required_step"),
        "cr10_sanitized_selection_only_result_rows_intake_status_ref": cr10.get(
            "sanitized_selection_only_result_rows_intake_status_ref"
        ),
        "cr10_rating_row_normalization_allowed_next": cr10.get("rating_row_normalization_allowed_next"),
        "cr10_sanitized_review_result_row_count": cr10.get("sanitized_review_result_row_count"),
        "cr10_selection_result_row_count": cr10.get("selection_result_row_count"),
        "cr10_case_ref_id_count": cr10.get("case_ref_id_count"),
        "cr10_actual_human_review_executed_by_person": cr10.get("actual_human_review_executed_by_person"),
        **_current_received_basis_fields(actual_basis=True),
        **_historical_basis_fields(),
        "rating_row_normalization_status_ref": (
            P7_R54_AHR_CR11_RATING_ROWS_NORMALIZED_STATUS_REF
            if ready
            else P7_R54_AHR_CR11_RATING_ROWS_BLOCKED_STATUS_REF
        ),
        "rating_row_normalization_allowed_status_refs": list(P7_R54_AHR_CR11_ALLOWED_RATING_ROW_STATUS_REFS),
        "rating_row_normalization_ready": ready,
        "rating_row_normalization_reason_refs": [P7_R54_AHR_CR11_READY_REASON_REF] if ready else [],
        "rating_row_normalization_blocker_refs": blockers,
        "rating_row_normalization_blocker_ref_count": len(blockers),
        "required_case_count": P7_R54_AHR_CR_REQUIRED_CASE_COUNT,
        "source_sanitized_review_result_row_count": cr10.get("sanitized_review_result_row_count") if cr10_ready else 0,
        "rating_row_count": len(rows_for_output),
        "rating_rows": rows_for_output,
        "rating_row_refs": rating_row_refs,
        "rating_row_ref_count": len(rating_row_refs),
        "source_review_result_row_refs": source_refs,
        "source_review_result_row_ref_count": len(source_refs),
        "case_ref_ids": case_refs,
        "case_ref_id_count": len(case_refs),
        "case_ref_ids_unique": len(set(case_refs)) == len(case_refs) == P7_R54_AHR_CR_REQUIRED_CASE_COUNT,
        "blind_case_ids": blind_ids,
        "blind_case_id_count": len(blind_ids),
        "blind_case_ids_unique": len(set(blind_ids)) == len(blind_ids) == P7_R54_AHR_CR_REQUIRED_CASE_COUNT,
        "packet_ref_ids": packet_refs,
        "packet_ref_id_count": len(packet_refs),
        "packet_ref_ids_unique": len(set(packet_refs)) == len(packet_refs) == P7_R54_AHR_CR_REQUIRED_CASE_COUNT,
        "axis_refs": list(P7_R54_AHR_CR08_RATING_AXIS_REFS),
        "axis_count": len(P7_R54_AHR_CR08_RATING_AXIS_REFS),
        "axis_score_count_per_row": len(P7_R54_AHR_CR08_RATING_AXIS_REFS) if ready else 0,
        "rating_axis_target_thresholds": dict(P7_R54_AHR_CR08_RATING_AXIS_TARGET_THRESHOLDS),
        "average_axis_scores": averages,
        "average_axis_scores_present": ready,
        "overall_average_axis_score": overall_average if ready else 0.0,
        "rating_rows_bodyfree_only": ready,
        "rating_rows_match_sanitized_review_result_case_refs": ready,
        "rating_rows_have_required_axis_scores": ready,
        "rating_scores_in_range": ready,
        "rating_rows_have_allowed_verdict_refs": ready,
        "axis_pass_flags_present_per_row": ready,
        "below_target_axis_refs_by_case": {
            str(row.get("case_ref_id")): list(row.get("below_target_axis_refs") or []) for row in rows_for_output
        },
        "below_target_axis_ref_counts": _below_target_axis_counts(rows_for_output) if ready else _below_target_axis_counts(()),
        "below_target_case_count": sum(1 for row in rows_for_output if row.get("below_target_axis_refs")),
        "verdict_counts": verdict_counts,
        "pass_case_count": verdict_counts.get("PASS", 0),
        "yellow_case_count": verdict_counts.get("YELLOW", 0),
        "repair_required_case_count": verdict_counts.get("REPAIR_REQUIRED", 0),
        "red_case_count": verdict_counts.get("RED", 0),
        "blocked_case_count": verdict_counts.get("BLOCKED", 0),
        "not_reviewable_case_count": verdict_counts.get("NOT_REVIEWABLE", 0),
        "readfeel_blocker_row_source_count": sum(len(row.get("readfeel_blocker_ids") or []) for row in rows_for_output),
        "execution_blocker_row_source_count": sum(len(row.get("execution_blocker_ids") or []) for row in rows_for_output),
        "rating_rows_normalized_here": ready,
        "actual_rating_rows_materialized_here": ready,
        "actual_human_review_executed_by_person": cr10.get("actual_human_review_executed_by_person") is True and ready,
        "actual_human_review_run_here": False,
        "actual_review_evidence_complete": False,
        "readfeel_execution_blocker_normalization_allowed_next": ready,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "disposal_verified": False,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR_CR11_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CR10_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(
            P7_R54_AHR_CR11_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CR10_NOT_YET_IMPLEMENTED_STEPS
        ),
        "next_required_step": P7_R54_AHR_CR12_STEP_REF if ready else P7_R54_AHR_CR11_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    material["actual_human_review_executed_by_person"] = cr10.get("actual_human_review_executed_by_person") is True and ready
    material["actual_rating_rows_materialized_here"] = ready
    material["actual_human_review_run_here"] = False
    material["actual_review_evidence_complete"] = False
    material["actual_question_need_observation_rows_materialized_here"] = False
    material["actual_disposal_receipt_materialized_here"] = False
    material["disposal_verified"] = False
    material["p5_human_blind_qa_confirmed_final"] = False
    material["p5_confirmed_final"] = False
    material["p5_final_allowed"] = False
    material["p6_limited_human_readfeel_start_allowed"] = False
    material["p6_start_allowed"] = False
    material["p8_start_allowed"] = False
    material["r52_reintake_execution_requested_here"] = False
    material["actual_r52_reintake_execution_confirmed"] = False
    material["p7_complete"] = False
    material["release_allowed"] = False
    return material


def assert_p7_r54_ahr_cr11_rating_row_normalization_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CR11_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CR11 rating row normalization",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CR11_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CR11_STEP_REF,
        operation_step_ref=P7_R54_AHR_CR11_STEP_REF,
        source="P7-R54-AHR-CR11 rating row normalization",
        allowed_true_false_flag_refs=P7_R54_AHR_CR11_ALLOWED_TRUE_OPERATION_FLAG_REFS,
    )
    if data.get("cr10_schema_version") != P7_R54_AHR_CR10_SANITIZED_SELECTION_ONLY_RESULT_ROWS_INTAKE_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CR11 CR10 schema version changed")
    if data.get("cr10_next_required_step") not in (
        P7_R54_AHR_CR11_STEP_REF,
        P7_R54_AHR_CR10_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF,
    ):
        raise ValueError("P7-R54-AHR-CR11 CR10 next step changed")
    _assert_current_received_basis_fields(data, actual_basis=True, source="P7-R54-AHR-CR11 rating rows")
    _assert_historical_basis_fields(data, source="P7-R54-AHR-CR11 rating rows")
    ready = data.get("rating_row_normalization_status_ref") == P7_R54_AHR_CR11_RATING_ROWS_NORMALIZED_STATUS_REF
    if data.get("rating_row_normalization_ready") is not ready:
        raise ValueError("P7-R54-AHR-CR11 ready flag changed")
    if tuple(data.get("rating_row_normalization_allowed_status_refs") or ()) != P7_R54_AHR_CR11_ALLOWED_RATING_ROW_STATUS_REFS:
        raise ValueError("P7-R54-AHR-CR11 allowed status refs changed")
    blockers = list(data.get("rating_row_normalization_blocker_refs") or [])
    if data.get("rating_row_normalization_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-CR11 blocker count changed")
    _assert_true_fields(
        data,
        keys=(
            "r52_reintake_claim_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "p5_finalization_blocked_here",
        ),
        source="P7-R54-AHR-CR11 rating row normalization",
    )
    _assert_false_fields(
        data,
        keys=(
            "actual_human_review_run_here",
            "actual_review_evidence_complete",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "disposal_verified",
            "p5_human_blind_qa_confirmed_final",
            "p5_confirmed_final",
            "p5_final_allowed",
            "p6_limited_human_readfeel_start_allowed",
            "p6_start_allowed",
            "p8_start_allowed",
            "r52_reintake_execution_requested_here",
            "actual_r52_reintake_execution_confirmed",
            "p7_complete",
            "release_allowed",
        ),
        source="P7-R54-AHR-CR11 rating row normalization",
    )
    if ready:
        if blockers:
            raise ValueError("P7-R54-AHR-CR11 ready material cannot carry blockers")
        if data.get("rating_row_normalization_reason_refs") != [P7_R54_AHR_CR11_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-CR11 ready reason changed")
        _assert_true_fields(
            data,
            keys=(
                "cr10_rating_row_normalization_allowed_next",
                "cr10_actual_human_review_executed_by_person",
                "case_ref_ids_unique",
                "blind_case_ids_unique",
                "packet_ref_ids_unique",
                "average_axis_scores_present",
                "rating_rows_bodyfree_only",
                "rating_rows_match_sanitized_review_result_case_refs",
                "rating_rows_have_required_axis_scores",
                "rating_scores_in_range",
                "rating_rows_have_allowed_verdict_refs",
                "axis_pass_flags_present_per_row",
                "rating_rows_normalized_here",
                "actual_rating_rows_materialized_here",
                "actual_human_review_executed_by_person",
                "readfeel_execution_blocker_normalization_allowed_next",
            ),
            source="P7-R54-AHR-CR11 normalized rating rows",
        )
        for field in (
            "source_sanitized_review_result_row_count",
            "rating_row_count",
            "rating_row_ref_count",
            "source_review_result_row_ref_count",
            "case_ref_id_count",
            "blind_case_id_count",
            "packet_ref_id_count",
        ):
            if data.get(field) != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
                raise ValueError(f"P7-R54-AHR-CR11 {field} changed")
        if tuple(data.get("axis_refs") or ()) != P7_R54_AHR_CR08_RATING_AXIS_REFS:
            raise ValueError("P7-R54-AHR-CR11 axis refs changed")
        if data.get("rating_axis_target_thresholds") != P7_R54_AHR_CR08_RATING_AXIS_TARGET_THRESHOLDS:
            raise ValueError("P7-R54-AHR-CR11 target thresholds changed")
        for row in data.get("rating_rows") or []:
            if not isinstance(row, Mapping):
                raise ValueError("P7-R54-AHR-CR11 rating row must be mapping")
            _assert_required_fields(
                row,
                required=P7_R54_AHR_CR11_RATING_ROW_REQUIRED_FIELD_REFS,
                source="P7-R54-AHR-CR11 rating row",
            )
            if row.get("schema_version") != P7_R54_AHR_CR11_RATING_ROW_SCHEMA_VERSION:
                raise ValueError("P7-R54-AHR-CR11 rating row schema changed")
            if row.get("body_free") is not True:
                raise ValueError("P7-R54-AHR-CR11 rating row must be body-free")
            for key in P7_R54_AHR_CR11_RATING_ROW_BODYFREE_FALSE_FLAG_REFS:
                if row.get(key) is not False:
                    raise ValueError(f"P7-R54-AHR-CR11 rating row must keep {key}=False")
            if set((row.get("axis_scores") or {}).keys()) != set(P7_R54_AHR_CR08_RATING_AXIS_REFS):
                raise ValueError("P7-R54-AHR-CR11 rating row axis refs changed")
            if row.get("axis_targets") != P7_R54_AHR_CR08_RATING_AXIS_TARGET_THRESHOLDS:
                raise ValueError("P7-R54-AHR-CR11 rating row axis targets changed")
            if row.get("axis_score_count") != len(P7_R54_AHR_CR08_RATING_AXIS_REFS):
                raise ValueError("P7-R54-AHR-CR11 rating row axis score count changed")
            if row.get("verdict") not in P7_R54_AHR_CR10_VERDICT_OPTION_REFS:
                raise ValueError("P7-R54-AHR-CR11 rating row verdict changed")
            if set(row.get("axis_pass_flags") or {}) != set(P7_R54_AHR_CR08_RATING_AXIS_REFS):
                raise ValueError("P7-R54-AHR-CR11 rating row pass flag refs changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CR11_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CR11 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CR11_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CR11 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_CR12_STEP_REF:
            raise ValueError("P7-R54-AHR-CR11 ready next step changed")
    else:
        if data.get("rating_row_normalization_status_ref") != P7_R54_AHR_CR11_RATING_ROWS_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-CR11 blocked status changed")
        if not blockers:
            raise ValueError("P7-R54-AHR-CR11 blocked material must carry blockers")
        if data.get("rating_row_normalization_reason_refs") != []:
            raise ValueError("P7-R54-AHR-CR11 blocked material cannot carry ready reasons")
        if data.get("rating_rows") != [] or data.get("rating_row_count") != 0:
            raise ValueError("P7-R54-AHR-CR11 blocked material must not carry rating rows")
        if data.get("next_required_step") != P7_R54_AHR_CR11_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CR11 blocked next step changed")
    return True


# Alias names for design/documentation wording.
def build_p7_r54_ahr_current_received_actual_local_review_operation_scope_no_touch_boundary_freeze_bodyfree(
    *, review_session_id: Any = None
) -> dict[str, Any]:
    return build_p7_r54_ahr_cr00_scope_no_touch_boundary_freeze(review_session_id=review_session_id)


def assert_p7_r54_ahr_current_received_actual_local_review_operation_scope_no_touch_boundary_freeze_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_cr00_scope_no_touch_boundary_freeze_contract(data)


def build_p7_r54_ahr_current_received_actual_local_review_operation_current_received_basis_envelope_bodyfree(
    *,
    scope_no_touch_boundary_freeze: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_cr01_current_received_basis_envelope(
        scope_no_touch_boundary_freeze=scope_no_touch_boundary_freeze,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_current_received_actual_local_review_operation_current_received_basis_envelope_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_cr01_current_received_basis_envelope_contract(data)


def build_p7_r54_ahr_current_received_actual_local_review_operation_historical_helper_refs_separation_bodyfree(
    *,
    current_received_basis_envelope: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_cr02_historical_helper_refs_separation(
        current_received_basis_envelope=current_received_basis_envelope,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_current_received_actual_local_review_operation_historical_helper_refs_separation_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_cr02_historical_helper_refs_separation_contract(data)


def build_p7_r54_ahr_current_received_actual_local_review_operation_basis_impact_assessment_bodyfree(
    *,
    historical_helper_refs_separation: Mapping[str, Any] | None = None,
    direct_diff_available: bool = False,
    direct_diff_executed: bool = False,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_cr03_basis_impact_assessment(
        historical_helper_refs_separation=historical_helper_refs_separation,
        direct_diff_available=direct_diff_available,
        direct_diff_executed=direct_diff_executed,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_current_received_actual_local_review_operation_basis_impact_assessment_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_cr03_basis_impact_assessment_contract(data)


def build_p7_r54_ahr_current_received_actual_local_review_operation_current_24_case_manifest_refreeze_bodyfree(
    *,
    basis_impact_assessment: Mapping[str, Any] | None = None,
    case_rows: Sequence[Mapping[str, Any]] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_cr04_current_24_case_manifest_refreeze(
        basis_impact_assessment=basis_impact_assessment,
        case_rows=case_rows,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_current_received_actual_local_review_operation_current_24_case_manifest_refreeze_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_cr04_current_24_case_manifest_refreeze_contract(data)


def build_p7_r54_ahr_current_received_actual_local_review_operation_local_only_preflight_bodyfree(
    *,
    current_24_case_manifest_refreeze: Mapping[str, Any] | None = None,
    local_only: bool = True,
    must_not_export: bool = True,
    local_review_root_ref: Any = P7_R54_AHR_CR05_DEFAULT_LOCAL_REVIEW_ROOT_REF,
    explicit_allow_ref: Any = "",
    retention_policy_ref: Any = P7_R54_AHR_CR05_DEFAULT_RETENTION_POLICY_REF,
    disposal_policy_ref: Any = P7_R54_AHR_CR05_DEFAULT_DISPOSAL_POLICY_REF,
    export_denylist_policy_ref: Any = P7_R54_AHR_CR05_DEFAULT_EXPORT_DENYLIST_POLICY_REF,
    body_full_packet_export_allowed: bool = False,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_cr05_local_only_preflight(
        current_24_case_manifest_refreeze=current_24_case_manifest_refreeze,
        local_only=local_only,
        must_not_export=must_not_export,
        local_review_root_ref=local_review_root_ref,
        explicit_allow_ref=explicit_allow_ref,
        retention_policy_ref=retention_policy_ref,
        disposal_policy_ref=disposal_policy_ref,
        export_denylist_policy_ref=export_denylist_policy_ref,
        body_full_packet_export_allowed=body_full_packet_export_allowed,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_current_received_actual_local_review_operation_local_only_preflight_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_cr05_local_only_preflight_contract(data)


def build_p7_r54_ahr_current_received_actual_local_review_operation_packet_generation_request_bridge_bodyfree(
    *,
    local_only_preflight: Mapping[str, Any] | None = None,
    packet_generation_request_ref: Any = P7_R54_AHR_CR06_DEFAULT_PACKET_GENERATION_REQUEST_REF,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_cr06_packet_generation_request_bridge(
        local_only_preflight=local_only_preflight,
        packet_generation_request_ref=packet_generation_request_ref,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_current_received_actual_local_review_operation_packet_generation_request_bridge_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_cr06_packet_generation_request_bridge_contract(data)


def build_p7_r54_ahr_current_received_actual_local_review_operation_packet_generation_receipt_and_scan_bodyfree(
    *,
    packet_generation_request_bridge: Mapping[str, Any] | None = None,
    receipt_input: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_cr07_packet_generation_receipt_and_scan(
        packet_generation_request_bridge=packet_generation_request_bridge,
        receipt_input=receipt_input,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_current_received_actual_local_review_operation_packet_generation_receipt_and_scan_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_cr07_packet_generation_receipt_and_scan_contract(data)


def build_p7_r54_ahr_current_received_actual_local_review_operation_reviewer_selection_form_bodyfree(
    *,
    packet_generation_receipt_scan: Mapping[str, Any] | None = None,
    reviewer_person_ref: Any = "",
    reviewer_is_person: bool = False,
    reviewer_person_confirmed: bool = False,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_cr08_reviewer_selection_form(
        packet_generation_receipt_scan=packet_generation_receipt_scan,
        reviewer_person_ref=reviewer_person_ref,
        reviewer_is_person=reviewer_is_person,
        reviewer_person_confirmed=reviewer_person_confirmed,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_current_received_actual_local_review_operation_reviewer_selection_form_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_cr08_reviewer_selection_form_contract(data)


def build_p7_r54_ahr_current_received_actual_local_review_operation_actual_local_human_review_operation_receipt_bodyfree(
    *,
    reviewer_selection_form: Mapping[str, Any] | None = None,
    operation_receipt_input: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_cr09_actual_local_human_review_operation_receipt(
        reviewer_selection_form=reviewer_selection_form,
        operation_receipt_input=operation_receipt_input,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_current_received_actual_local_review_operation_actual_local_human_review_operation_receipt_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_cr09_actual_local_human_review_operation_receipt_contract(data)

def build_p7_r54_ahr_current_received_actual_local_review_operation_sanitized_selection_only_result_rows_intake_bodyfree(
    *,
    actual_local_human_review_operation_receipt: Mapping[str, Any] | None = None,
    selection_result_rows: Sequence[Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_cr10_sanitized_selection_only_result_rows_intake(
        actual_local_human_review_operation_receipt=actual_local_human_review_operation_receipt,
        selection_result_rows=selection_result_rows,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_current_received_actual_local_review_operation_sanitized_selection_only_result_rows_intake_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_cr10_sanitized_selection_only_result_rows_intake_contract(data)


def build_p7_r54_ahr_current_received_actual_local_review_operation_rating_row_normalization_bodyfree(
    *,
    sanitized_selection_only_result_rows_intake: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_cr11_rating_row_normalization(
        sanitized_selection_only_result_rows_intake=sanitized_selection_only_result_rows_intake,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_current_received_actual_local_review_operation_rating_row_normalization_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_cr11_rating_row_normalization_contract(data)



# ---------------------------------------------------------------------------
# R54-AHR-CR12 / R54-AHR-CR13: blocker normalization and question observation
# normalization.  These helpers are appended after CR10/CR11 so earlier CR
# result memos and helper green meanings remain unchanged.  They keep P8 as
# material-candidate-only and do not create question text, P8 implementation,
# P5 finalization, P6/P8 start, R52 execution, P7 completion, or release.

P7_R54_AHR_CR12_READFEEL_EXECUTION_BLOCKER_NORMALIZATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_received_actual_local_review_operation."
    "cr12_readfeel_execution_blocker_normalization.bodyfree.v1"
)
P7_R54_AHR_CR13_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_received_actual_local_review_operation."
    "cr13_question_need_observation_normalization.bodyfree.v1"
)
P7_R54_AHR_CR12_BLOCKER_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_received_actual_local_review_operation."
    "cr12_blocker_row.bodyfree.v1"
)
P7_R54_AHR_CR13_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_received_actual_local_review_operation."
    "cr13_question_need_observation_row.bodyfree.v1"
)
P7_R54_AHR_CR_READFEEL_EXECUTION_BLOCKER_NORMALIZATION_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CR12_READFEEL_EXECUTION_BLOCKER_NORMALIZATION_SCHEMA_VERSION
)
P7_R54_AHR_CR_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CR13_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION
)

P7_R54_AHR_CR12_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR11_IMPLEMENTED_STEPS,
    P7_R54_AHR_CR12_STEP_REF,
)
P7_R54_AHR_CR12_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CR_STEP_REFS[13:]
P7_R54_AHR_CR13_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR12_IMPLEMENTED_STEPS,
    P7_R54_AHR_CR13_STEP_REF,
)
P7_R54_AHR_CR13_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CR_STEP_REFS[14:]

P7_R54_AHR_CR12_BLOCKERS_NORMALIZED_STATUS_REF: Final = (
    "CR12_READFEEL_EXECUTION_BLOCKERS_NORMALIZED_BODYFREE"
)
P7_R54_AHR_CR12_BLOCKERS_BLOCKED_STATUS_REF: Final = (
    "CR12_READFEEL_EXECUTION_BLOCKER_NORMALIZATION_BLOCKED"
)
P7_R54_AHR_CR12_ALLOWED_BLOCKER_NORMALIZATION_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR12_BLOCKERS_NORMALIZED_STATUS_REF,
    P7_R54_AHR_CR12_BLOCKERS_BLOCKED_STATUS_REF,
)
P7_R54_AHR_CR12_READY_REASON_REF: Final = (
    "CR12_RATING_ROWS_NORMALIZED_TO_BODYFREE_READFEEL_EXECUTION_BLOCKER_ROWS"
)
P7_R54_AHR_CR12_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "readfeel_execution_blocker_normalization_or_stop"
)
P7_R54_AHR_CR12_CR11_NOT_READY_BLOCKER_REF: Final = "cr11_rating_rows_not_ready"
P7_R54_AHR_CR12_CR11_NEXT_STEP_NOT_CR12_BLOCKER_REF: Final = "cr11_next_step_not_cr12"
P7_R54_AHR_CR12_CR11_RATING_ROWS_NOT_MATERIALIZED_BLOCKER_REF: Final = (
    "cr11_actual_rating_rows_not_materialized"
)
P7_R54_AHR_CR12_CR11_RATING_ROW_COUNT_NOT_24_BLOCKER_REF: Final = "cr11_rating_row_count_not_24"
P7_R54_AHR_CR12_RATING_ROW_INVALID_BLOCKER_REF: Final = "cr12_source_rating_row_invalid"
P7_R54_AHR_CR12_RATING_ROW_FORBIDDEN_KEY_BLOCKER_REF: Final = (
    "cr12_source_rating_row_forbidden_body_question_path_hash_key"
)
P7_R54_AHR_CR12_RATING_ROW_CASE_REF_NOT_IN_MANIFEST_BLOCKER_REF: Final = (
    "cr12_source_rating_row_case_ref_not_in_manifest"
)
P7_R54_AHR_CR12_RATING_ROW_UNIQUE_REFS_NOT_24_BLOCKER_REF: Final = (
    "cr12_source_rating_row_unique_refs_not_24"
)
P7_R54_AHR_CR12_READFEEL_BLOCKER_ID_NOT_ALLOWED_BLOCKER_REF: Final = (
    "cr12_readfeel_blocker_id_not_allowed"
)
P7_R54_AHR_CR12_EXECUTION_BLOCKER_ID_NOT_ALLOWED_BLOCKER_REF: Final = (
    "cr12_execution_blocker_id_not_allowed"
)
P7_R54_AHR_CR12_REPAIR_REQUIRED_REF_NOT_ALLOWED_BLOCKER_REF: Final = (
    "cr12_repair_required_ref_not_allowed"
)

P7_R54_AHR_CR12_BLOCKER_KIND_REFS: Final[tuple[str, ...]] = (
    "readfeel_blocker",
    "execution_blocker",
    "repair_required",
    "below_target_axis",
    "inconclusive_material",
)
P7_R54_AHR_CR12_BLOCKER_STATUS_OPEN_REF: Final = "open_bodyfree_product_or_operation_blocker"
P7_R54_AHR_CR12_BLOCKER_CATEGORY_REFS: Final[tuple[str, ...]] = (
    "p5_readfeel_repair_required",
    "p5_history_connection_weak",
    "p5_creepy_or_overclaim_risk",
    "p5_self_blame_amplification_risk",
    "p4_current_only_surface_repair_required",
    "operation_blocked_missing_receipt",
    "operation_blocked_body_leak",
    "operation_blocked_question_text",
    "operation_blocked_disposal_missing",
    "inconclusive_insufficient_material",
)
P7_R54_AHR_CR12_READFEEL_ROUTE_REF: Final = "P5_READFEEL_REPAIR_BEFORE_P8_OR_R52"
P7_R54_AHR_CR12_P4_ROUTE_REF: Final = "P4_CURRENT_ONLY_SURFACE_REPAIR_BEFORE_P8_OR_R52"
P7_R54_AHR_CR12_OPERATION_ROUTE_REF: Final = "R54_OPERATION_BLOCKER_REPAIR_BEFORE_EVIDENCE_COMPLETE"
P7_R54_AHR_CR12_INCONCLUSIVE_ROUTE_REF: Final = "R54_INCONCLUSIVE_MATERIAL_REVIEW_REQUIRED"
P7_R54_AHR_CR12_READFEEL_BLOCKER_CATEGORY_BY_ID: Final[dict[str, str]] = {
    "history_connection_weak": "p5_history_connection_weak",
    "history_line_creepy_or_overread": "p5_creepy_or_overclaim_risk",
    "current_input_overridden_by_history": "p5_creepy_or_overclaim_risk",
    "overclaim_or_unearned_certainty": "p5_creepy_or_overclaim_risk",
    "self_blame_amplified": "p5_self_blame_amplification_risk",
    "shallow_repeat_or_generic": "p5_readfeel_repair_required",
    "wants_less_input_or_no_accumulation": "p5_readfeel_repair_required",
    "boundary_history_line_leak": "p5_creepy_or_overclaim_risk",
}
P7_R54_AHR_CR12_EXECUTION_BLOCKER_CATEGORY_BY_ID: Final[dict[str, str]] = {
    "packet_missing": "operation_blocked_missing_receipt",
    "packet_not_local_only": "operation_blocked_missing_receipt",
    "case_manifest_incomplete": "operation_blocked_missing_receipt",
    "reviewer_selection_incomplete": "operation_blocked_missing_receipt",
    "forbidden_body_leak": "operation_blocked_body_leak",
    "question_text_leak": "operation_blocked_question_text",
    "disposal_missing": "operation_blocked_disposal_missing",
    "no_touch_violation": "operation_blocked_missing_receipt",
}
P7_R54_AHR_CR12_REPAIR_CATEGORY_BY_REF: Final[dict[str, str]] = {
    "emlis_readfeel_repair_required": "p5_readfeel_repair_required",
    "p5_surface_repair_required": "p5_readfeel_repair_required",
    "gate_boundary_repair_required": "p5_readfeel_repair_required",
    "p4_current_surface_repair_required": "p4_current_only_surface_repair_required",
}
P7_R54_AHR_CR12_BELOW_TARGET_AXIS_CATEGORY_BY_REF: Final[dict[str, str]] = {
    "history_connection_naturalness": "p5_history_connection_weak",
    "creepy_absence": "p5_creepy_or_overclaim_risk",
    "overclaim_absence": "p5_creepy_or_overclaim_risk",
    "self_blame_non_amplification": "p5_self_blame_amplification_risk",
    "wants_more_input_or_accumulation": "p5_readfeel_repair_required",
    "non_shallow_repeat": "p5_readfeel_repair_required",
}
P7_R54_AHR_CR12_ALLOWED_TRUE_OPERATION_FLAG_REFS: Final[tuple[str, ...]] = (
    "actual_human_review_executed_by_person",
    "actual_rating_rows_materialized_here",
)
P7_R54_AHR_CR12_BLOCKER_ROW_BODYFREE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR11_RATING_ROW_BODYFREE_FALSE_FLAG_REFS
)

P7_R54_AHR_CR13_QUESTION_OBSERVATIONS_NORMALIZED_STATUS_REF: Final = (
    "CR13_QUESTION_NEED_OBSERVATIONS_NORMALIZED_BODYFREE"
)
P7_R54_AHR_CR13_QUESTION_OBSERVATIONS_BLOCKED_STATUS_REF: Final = (
    "CR13_QUESTION_NEED_OBSERVATION_NORMALIZATION_BLOCKED"
)
P7_R54_AHR_CR13_ALLOWED_QUESTION_OBSERVATION_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR13_QUESTION_OBSERVATIONS_NORMALIZED_STATUS_REF,
    P7_R54_AHR_CR13_QUESTION_OBSERVATIONS_BLOCKED_STATUS_REF,
)
P7_R54_AHR_CR13_READY_REASON_REF: Final = (
    "CR13_24_BODYFREE_QUESTION_NEED_OBSERVATION_ROWS_NORMALIZED_WITHOUT_QUESTION_TEXT"
)
P7_R54_AHR_CR13_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "question_need_observation_normalization_or_stop"
)
P7_R54_AHR_CR13_CR10_NOT_READY_BLOCKER_REF: Final = "cr10_sanitized_rows_not_ready"
P7_R54_AHR_CR13_CR11_NOT_READY_BLOCKER_REF: Final = "cr11_rating_rows_not_ready"
P7_R54_AHR_CR13_CR12_NOT_READY_BLOCKER_REF: Final = "cr12_blocker_normalization_not_ready"
P7_R54_AHR_CR13_CR10_NEXT_STEP_NOT_CR11_BLOCKER_REF: Final = "cr10_next_step_not_cr11"
P7_R54_AHR_CR13_CR11_NEXT_STEP_NOT_CR12_BLOCKER_REF: Final = "cr11_next_step_not_cr12"
P7_R54_AHR_CR13_CR12_NEXT_STEP_NOT_CR13_BLOCKER_REF: Final = "cr12_next_step_not_cr13"
P7_R54_AHR_CR13_SOURCE_ROW_INVALID_BLOCKER_REF: Final = "cr13_source_row_invalid"
P7_R54_AHR_CR13_SOURCE_ROW_FORBIDDEN_KEY_BLOCKER_REF: Final = (
    "cr13_source_row_forbidden_body_question_path_hash_key"
)
P7_R54_AHR_CR13_SOURCE_ROW_COUNT_NOT_24_BLOCKER_REF: Final = "cr13_source_row_count_not_24"
P7_R54_AHR_CR13_CASE_REF_MISMATCH_BLOCKER_REF: Final = "cr13_case_ref_mismatch_between_cr10_cr11"
P7_R54_AHR_CR13_PRIMARY_CLASS_NOT_ALLOWED_BLOCKER_REF: Final = "cr13_primary_class_not_allowed"
P7_R54_AHR_CR13_ONE_QUESTION_FIT_NOT_ALLOWED_BLOCKER_REF: Final = "cr13_one_question_fit_not_allowed"
P7_R54_AHR_CR13_REPAIR_REQUIRED_REF_NOT_ALLOWED_BLOCKER_REF: Final = (
    "cr13_repair_required_ref_not_allowed"
)
P7_R54_AHR_CR13_AMBIGUITY_KIND_REF_NOT_ALLOWED_BLOCKER_REF: Final = (
    "cr13_ambiguity_kind_ref_not_allowed"
)
P7_R54_AHR_CR13_P8_MATERIAL_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = (
    "question_may_reduce_overread_risk",
    "plus_single_question_candidate_later",
    "premium_deep_dive_candidate_later",
)
P7_R54_AHR_CR13_P5_REPAIR_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = (
    "not_question_emlis_readfeel_repair_required",
    "not_question_p5_surface_repair_required",
    "not_question_gate_boundary_required",
)
P7_R54_AHR_CR13_P8_MATERIAL_ONE_QUESTION_FIT_REFS: Final[tuple[str, ...]] = (
    "fits_one_question",
)
P7_R54_AHR_CR13_ALLOWED_TRUE_OPERATION_FLAG_REFS: Final[tuple[str, ...]] = (
    "actual_human_review_executed_by_person",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
)
P7_R54_AHR_CR13_QUESTION_OBSERVATION_ROW_BODYFREE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR11_RATING_ROW_BODYFREE_FALSE_FLAG_REFS
)

P7_R54_AHR_CR12_BLOCKER_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "blocker_row_ref",
    "source_rating_row_ref",
    "source_review_result_row_ref",
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
    "blocker_kind",
    "blocker_category_ref",
    "blocker_id",
    "blocker_status_ref",
    "routes_to",
    "p8_material_candidate_blocked",
    "body_free",
    *P7_R54_AHR_CR12_BLOCKER_ROW_BODYFREE_FALSE_FLAG_REFS,
)
P7_R54_AHR_CR13_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "question_need_observation_row_ref",
    "source_rating_row_ref",
    "source_review_result_row_ref",
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
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
    "question_may_reduce_overread_risk",
    "p8_design_material_candidate",
    "p8_material_candidate_reason_ref",
    "p8_implementation_spec_finalized_here",
    "p5_repair_required",
    "p4_current_surface_repair_required",
    "operation_blocker_present",
    "readfeel_blocker_present",
    "question_would_make_immediate_observation_heavy",
    "p8_start_allowed",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "body_free",
    *P7_R54_AHR_CR13_QUESTION_OBSERVATION_ROW_BODYFREE_FALSE_FLAG_REFS,
)

P7_R54_AHR_CR12_READFEEL_EXECUTION_BLOCKER_NORMALIZATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR_BASE_REQUIRED_FIELD_REFS,
    "cr11_schema_version",
    "cr11_material_ref",
    "cr11_next_required_step",
    "cr11_rating_row_normalization_status_ref",
    "cr11_readfeel_execution_blocker_normalization_allowed_next",
    "cr11_rating_row_count",
    "cr11_actual_rating_rows_materialized_here",
    "cr11_actual_human_review_executed_by_person",
    *P7_R54_AHR_CR_CURRENT_RECEIVED_BASIS_FIELD_REFS,
    *P7_R54_AHR_CR_HISTORICAL_BASIS_FIELD_REFS,
    "readfeel_execution_blocker_normalization_status_ref",
    "readfeel_execution_blocker_normalization_allowed_status_refs",
    "readfeel_execution_blocker_normalization_ready",
    "readfeel_execution_blocker_normalization_reason_refs",
    "readfeel_execution_blocker_normalization_step_blocker_refs",
    "readfeel_execution_blocker_normalization_step_blocker_ref_count",
    "required_case_count",
    "source_rating_row_count",
    "source_rating_row_refs",
    "source_rating_row_ref_count",
    "case_ref_ids",
    "case_ref_id_count",
    "case_ref_ids_unique",
    "blocker_rows",
    "blocker_row_count",
    "blocker_row_refs",
    "blocker_row_ref_count",
    "blocker_kind_refs",
    "blocker_kind_counts",
    "blocker_category_refs",
    "blocker_category_counts",
    "readfeel_blocker_row_count",
    "execution_blocker_row_count",
    "repair_required_blocker_row_count",
    "below_target_axis_blocker_row_count",
    "inconclusive_blocker_row_count",
    "readfeel_blocker_id_counts",
    "execution_blocker_id_counts",
    "repair_required_ref_counts",
    "below_target_axis_ref_counts",
    "p5_repair_required_case_refs",
    "p5_repair_required_case_count",
    "p4_current_only_repair_required_case_refs",
    "p4_current_only_repair_required_case_count",
    "operation_blocked_case_refs",
    "operation_blocked_case_count",
    "inconclusive_insufficient_material_case_refs",
    "inconclusive_insufficient_material_case_count",
    "rows_bodyfree_only",
    "readfeel_execution_blockers_separated",
    "p5_repair_required_cases_not_promoted_to_p8_material_candidate",
    "p4_current_repair_cases_not_promoted_to_p8_material_candidate",
    "operation_blocker_cases_not_promoted_to_p8_material_candidate",
    "readfeel_blocker_cases_not_promoted_to_p8_material_candidate",
    "question_need_observation_normalization_allowed_next",
    "actual_rating_rows_materialized_here",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_review_evidence_complete",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CR_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CR_FALSE_FLAG_REFS,
)
P7_R54_AHR_CR13_QUESTION_NEED_OBSERVATION_NORMALIZATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR_BASE_REQUIRED_FIELD_REFS,
    "cr10_schema_version",
    "cr10_material_ref",
    "cr10_next_required_step",
    "cr10_sanitized_selection_only_result_rows_intake_status_ref",
    "cr10_sanitized_review_result_row_count",
    "cr11_schema_version",
    "cr11_material_ref",
    "cr11_next_required_step",
    "cr11_rating_row_normalization_status_ref",
    "cr11_rating_row_count",
    "cr11_actual_rating_rows_materialized_here",
    "cr12_schema_version",
    "cr12_material_ref",
    "cr12_next_required_step",
    "cr12_readfeel_execution_blocker_normalization_status_ref",
    "cr12_question_need_observation_normalization_allowed_next",
    "cr12_blocker_row_count",
    "cr12_p5_repair_required_case_count",
    "cr12_p4_current_only_repair_required_case_count",
    "cr12_operation_blocked_case_count",
    *P7_R54_AHR_CR_CURRENT_RECEIVED_BASIS_FIELD_REFS,
    *P7_R54_AHR_CR_HISTORICAL_BASIS_FIELD_REFS,
    "question_need_observation_normalization_status_ref",
    "question_need_observation_normalization_allowed_status_refs",
    "question_need_observation_normalization_ready",
    "question_need_observation_normalization_reason_refs",
    "question_need_observation_normalization_step_blocker_refs",
    "question_need_observation_normalization_step_blocker_ref_count",
    "required_case_count",
    "source_sanitized_review_result_row_count",
    "source_rating_row_count",
    "question_need_observation_row_count",
    "question_need_observation_rows",
    "question_need_observation_row_refs",
    "question_need_observation_row_ref_count",
    "case_ref_ids",
    "case_ref_id_count",
    "case_ref_ids_unique",
    "question_need_primary_class_options",
    "question_need_primary_class_option_count",
    "one_question_fit_option_refs",
    "one_question_fit_option_count",
    "repair_required_option_refs",
    "repair_required_option_count",
    "ambiguity_kind_option_refs",
    "ambiguity_kind_option_count",
    "plan_candidate_flag_refs",
    "plan_candidate_flag_count",
    "question_need_primary_class_counts",
    "one_question_fit_counts",
    "ambiguity_kind_counts",
    "p8_material_candidate_case_refs",
    "p8_material_candidate_case_count",
    "plus_single_question_candidate_case_refs",
    "plus_single_question_candidate_case_count",
    "premium_deep_dive_candidate_case_refs",
    "premium_deep_dive_candidate_case_count",
    "question_may_reduce_overread_risk_case_refs",
    "question_may_reduce_overread_risk_case_count",
    "question_would_make_immediate_observation_heavy_case_refs",
    "question_would_make_immediate_observation_heavy_case_count",
    "p5_repair_required_case_refs",
    "p5_repair_required_case_count",
    "p4_current_surface_repair_required_case_refs",
    "p4_current_surface_repair_required_case_count",
    "operation_blocker_case_refs",
    "operation_blocker_case_count",
    "readfeel_blocker_case_refs",
    "readfeel_blocker_case_count",
    "rows_bodyfree_only",
    "rows_have_no_question_text",
    "question_need_observation_rows_normalized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_rating_rows_materialized_here",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_review_evidence_complete",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "p8_question_implementation_spec_finalized_here",
    "p8_start_allowed",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CR_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CR_FALSE_FLAG_REFS,
)
P7_R54_AHR_CR_READFEEL_EXECUTION_BLOCKER_NORMALIZATION_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CR12_READFEEL_EXECUTION_BLOCKER_NORMALIZATION_REQUIRED_FIELD_REFS
)
P7_R54_AHR_CR_QUESTION_NEED_OBSERVATION_NORMALIZATION_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CR13_QUESTION_NEED_OBSERVATION_NORMALIZATION_REQUIRED_FIELD_REFS
)


def _cr12_blocker_category_routes_to(category_ref: str) -> str:
    if category_ref == "p4_current_only_surface_repair_required":
        return P7_R54_AHR_CR12_P4_ROUTE_REF
    if category_ref.startswith("operation_blocked_"):
        return P7_R54_AHR_CR12_OPERATION_ROUTE_REF
    if category_ref == "inconclusive_insufficient_material":
        return P7_R54_AHR_CR12_INCONCLUSIVE_ROUTE_REF
    return P7_R54_AHR_CR12_READFEEL_ROUTE_REF


def _cr12_make_blocker_row(
    *,
    seq: int,
    source_row: Mapping[str, Any],
    review_session_id: str,
    blocker_kind: str,
    blocker_category_ref: str,
    blocker_id: str,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CR12_BLOCKER_ROW_SCHEMA_VERSION,
        "review_session_id": review_session_id,
        "blocker_row_ref": f"cr12_blocker_row_{seq:03d}",
        "source_rating_row_ref": clean_identifier(
            source_row.get("rating_row_ref"), default=f"cr11_rating_row_{seq:03d}", max_length=120
        ),
        "source_review_result_row_ref": clean_identifier(
            source_row.get("source_review_result_row_ref"), default=f"cr10_review_result_row_{seq:03d}", max_length=120
        ),
        "case_ref_id": clean_identifier(source_row.get("case_ref_id"), default="", max_length=120),
        "blind_case_id": clean_identifier(source_row.get("blind_case_id"), default="", max_length=120),
        "packet_ref_id": clean_identifier(source_row.get("packet_ref_id"), default="", max_length=120),
        "blocker_kind": blocker_kind,
        "blocker_category_ref": blocker_category_ref,
        "blocker_id": clean_identifier(blocker_id, default="unknown_blocker", max_length=160),
        "blocker_status_ref": P7_R54_AHR_CR12_BLOCKER_STATUS_OPEN_REF,
        "routes_to": _cr12_blocker_category_routes_to(blocker_category_ref),
        "p8_material_candidate_blocked": True,
        "body_free": True,
    }
    row.update({key: False for key in P7_R54_AHR_CR12_BLOCKER_ROW_BODYFREE_FALSE_FLAG_REFS})
    return row


def _cr12_blocker_rows_from_rating_rows(
    rating_rows: Sequence[Any], *, review_session_id: str
) -> tuple[list[dict[str, Any]], list[str]]:
    step_blockers: list[str] = []
    blocker_rows: list[dict[str, Any]] = []
    expected_case_refs = set(_expected_cr04_manifest_rows_by_case_ref())
    seen_case_refs: set[str] = set()
    seq = 1
    if len(rating_rows) != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
        step_blockers.append(P7_R54_AHR_CR12_CR11_RATING_ROW_COUNT_NOT_24_BLOCKER_REF)
    for index, raw_row in enumerate(rating_rows, start=1):
        if not isinstance(raw_row, Mapping):
            step_blockers.append(P7_R54_AHR_CR12_RATING_ROW_INVALID_BLOCKER_REF)
            continue
        if _contains_forbidden_body_or_question_key(raw_row):
            step_blockers.append(P7_R54_AHR_CR12_RATING_ROW_FORBIDDEN_KEY_BLOCKER_REF)
            continue
        if raw_row.get("schema_version") != P7_R54_AHR_CR11_RATING_ROW_SCHEMA_VERSION:
            step_blockers.append(P7_R54_AHR_CR12_RATING_ROW_INVALID_BLOCKER_REF)
        if raw_row.get("body_free") is not True:
            step_blockers.append(P7_R54_AHR_CR12_RATING_ROW_INVALID_BLOCKER_REF)
        case_ref_id = clean_identifier(raw_row.get("case_ref_id"), default="", max_length=120)
        seen_case_refs.add(case_ref_id)
        if case_ref_id not in expected_case_refs:
            step_blockers.append(P7_R54_AHR_CR12_RATING_ROW_CASE_REF_NOT_IN_MANIFEST_BLOCKER_REF)
        for blocker_id in _dedupe_string_refs(raw_row.get("readfeel_blocker_ids") or (), limit=20, max_length=120):
            category = P7_R54_AHR_CR12_READFEEL_BLOCKER_CATEGORY_BY_ID.get(blocker_id)
            if not category:
                step_blockers.append(P7_R54_AHR_CR12_READFEEL_BLOCKER_ID_NOT_ALLOWED_BLOCKER_REF)
                continue
            blocker_rows.append(
                _cr12_make_blocker_row(
                    seq=seq,
                    source_row=raw_row,
                    review_session_id=review_session_id,
                    blocker_kind="readfeel_blocker",
                    blocker_category_ref=category,
                    blocker_id=blocker_id,
                )
            )
            seq += 1
        for blocker_id in _dedupe_string_refs(raw_row.get("execution_blocker_ids") or (), limit=20, max_length=120):
            category = P7_R54_AHR_CR12_EXECUTION_BLOCKER_CATEGORY_BY_ID.get(blocker_id)
            if not category:
                step_blockers.append(P7_R54_AHR_CR12_EXECUTION_BLOCKER_ID_NOT_ALLOWED_BLOCKER_REF)
                continue
            blocker_rows.append(
                _cr12_make_blocker_row(
                    seq=seq,
                    source_row=raw_row,
                    review_session_id=review_session_id,
                    blocker_kind="execution_blocker",
                    blocker_category_ref=category,
                    blocker_id=blocker_id,
                )
            )
            seq += 1
        for repair_ref in _dedupe_string_refs(raw_row.get("repair_required_refs") or (), limit=20, max_length=160):
            if repair_ref == "no_repair_required":
                continue
            category = P7_R54_AHR_CR12_REPAIR_CATEGORY_BY_REF.get(repair_ref)
            if not category:
                step_blockers.append(P7_R54_AHR_CR12_REPAIR_REQUIRED_REF_NOT_ALLOWED_BLOCKER_REF)
                continue
            blocker_rows.append(
                _cr12_make_blocker_row(
                    seq=seq,
                    source_row=raw_row,
                    review_session_id=review_session_id,
                    blocker_kind="repair_required",
                    blocker_category_ref=category,
                    blocker_id=repair_ref,
                )
            )
            seq += 1
        for axis_ref in _dedupe_string_refs(raw_row.get("below_target_axis_refs") or (), limit=20, max_length=120):
            category = P7_R54_AHR_CR12_BELOW_TARGET_AXIS_CATEGORY_BY_REF.get(axis_ref)
            if not category:
                continue
            blocker_rows.append(
                _cr12_make_blocker_row(
                    seq=seq,
                    source_row=raw_row,
                    review_session_id=review_session_id,
                    blocker_kind="below_target_axis",
                    blocker_category_ref=category,
                    blocker_id=f"below_target_axis_{axis_ref}",
                )
            )
            seq += 1
        primary_class = clean_identifier(raw_row.get("question_need_primary_class"), default="", max_length=160)
        if primary_class == "insufficient_material_execution_blocker" or raw_row.get("verdict") == "NOT_REVIEWABLE":
            blocker_rows.append(
                _cr12_make_blocker_row(
                    seq=seq,
                    source_row=raw_row,
                    review_session_id=review_session_id,
                    blocker_kind="inconclusive_material",
                    blocker_category_ref="inconclusive_insufficient_material",
                    blocker_id="insufficient_material_execution_blocker",
                )
            )
            seq += 1
    if len(seen_case_refs) != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
        step_blockers.append(P7_R54_AHR_CR12_RATING_ROW_UNIQUE_REFS_NOT_24_BLOCKER_REF)
    if seen_case_refs and seen_case_refs != expected_case_refs:
        step_blockers.append(P7_R54_AHR_CR12_RATING_ROW_CASE_REF_NOT_IN_MANIFEST_BLOCKER_REF)
    return blocker_rows if not step_blockers else [], _dedupe_string_refs(step_blockers, limit=200, max_length=240)


def _count_nested_string_values(rows: Sequence[Mapping[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        for value in row.get(field) or []:
            key = str(value)
            if not key:
                continue
            counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _case_refs_for_blocker_categories(rows: Sequence[Mapping[str, Any]], categories: set[str]) -> list[str]:
    refs = sorted({str(row.get("case_ref_id")) for row in rows if row.get("blocker_category_ref") in categories})
    return [ref for ref in refs if ref]


def build_p7_r54_ahr_cr12_readfeel_execution_blocker_normalization(
    *,
    rating_row_normalization: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build CR12 body-free readfeel / execution blocker normalization."""

    cr11 = dict(rating_row_normalization or build_p7_r54_ahr_cr11_rating_row_normalization())
    assert_p7_r54_ahr_cr11_rating_row_normalization_contract(cr11)
    session_id = _safe_review_session_id(review_session_id)
    cr11_ready = cr11.get("rating_row_normalization_ready") is True
    blocker_rows, row_blockers = _cr12_blocker_rows_from_rating_rows(
        cr11.get("rating_rows") or (), review_session_id=session_id
    )
    step_blockers: list[str] = []
    if not cr11_ready:
        step_blockers.append(P7_R54_AHR_CR12_CR11_NOT_READY_BLOCKER_REF)
    if cr11.get("next_required_step") != P7_R54_AHR_CR12_STEP_REF:
        step_blockers.append(P7_R54_AHR_CR12_CR11_NEXT_STEP_NOT_CR12_BLOCKER_REF)
    if cr11.get("actual_rating_rows_materialized_here") is not True:
        step_blockers.append(P7_R54_AHR_CR12_CR11_RATING_ROWS_NOT_MATERIALIZED_BLOCKER_REF)
    if cr11.get("rating_row_count") != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
        step_blockers.append(P7_R54_AHR_CR12_CR11_RATING_ROW_COUNT_NOT_24_BLOCKER_REF)
    step_blockers.extend(row_blockers)
    step_blockers = _dedupe_string_refs(step_blockers, limit=200, max_length=240)
    ready = not step_blockers
    rows_for_output = blocker_rows if ready else []
    source_refs = [str(row.get("rating_row_ref")) for row in cr11.get("rating_rows") or []] if ready else []
    case_refs = [str(row.get("case_ref_id")) for row in cr11.get("rating_rows") or []] if ready else []
    category_counts = _count_values(rows_for_output, "blocker_category_ref") if ready else {}
    kind_counts = _count_values(rows_for_output, "blocker_kind") if ready else {}
    p5_case_refs = _case_refs_for_blocker_categories(
        rows_for_output,
        {
            "p5_readfeel_repair_required",
            "p5_history_connection_weak",
            "p5_creepy_or_overclaim_risk",
            "p5_self_blame_amplification_risk",
        },
    )
    p4_case_refs = _case_refs_for_blocker_categories(rows_for_output, {"p4_current_only_surface_repair_required"})
    operation_case_refs = _case_refs_for_blocker_categories(
        rows_for_output,
        {
            "operation_blocked_missing_receipt",
            "operation_blocked_body_leak",
            "operation_blocked_question_text",
            "operation_blocked_disposal_missing",
        },
    )
    inconclusive_case_refs = _case_refs_for_blocker_categories(rows_for_output, {"inconclusive_insufficient_material"})
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CR12_READFEEL_EXECUTION_BLOCKER_NORMALIZATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CR_STEP,
        "scope": P7_R54_AHR_CR_SCOPE,
        "policy_kind": P7_R54_AHR_CR_POLICY_KIND,
        "policy_section": P7_R54_AHR_CR12_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CR12_STEP_REF,
        "current_phase": P7_R54_AHR_CR_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cr12_readfeel_execution_blocker_normalization_20260628",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cr11_schema_version": cr11.get("schema_version"),
        "cr11_material_ref": cr11.get("material_id"),
        "cr11_next_required_step": cr11.get("next_required_step"),
        "cr11_rating_row_normalization_status_ref": cr11.get("rating_row_normalization_status_ref"),
        "cr11_readfeel_execution_blocker_normalization_allowed_next": cr11.get(
            "readfeel_execution_blocker_normalization_allowed_next"
        ),
        "cr11_rating_row_count": cr11.get("rating_row_count"),
        "cr11_actual_rating_rows_materialized_here": cr11.get("actual_rating_rows_materialized_here"),
        "cr11_actual_human_review_executed_by_person": cr11.get("actual_human_review_executed_by_person"),
        **_current_received_basis_fields(actual_basis=True),
        **_historical_basis_fields(),
        "readfeel_execution_blocker_normalization_status_ref": (
            P7_R54_AHR_CR12_BLOCKERS_NORMALIZED_STATUS_REF if ready else P7_R54_AHR_CR12_BLOCKERS_BLOCKED_STATUS_REF
        ),
        "readfeel_execution_blocker_normalization_allowed_status_refs": list(
            P7_R54_AHR_CR12_ALLOWED_BLOCKER_NORMALIZATION_STATUS_REFS
        ),
        "readfeel_execution_blocker_normalization_ready": ready,
        "readfeel_execution_blocker_normalization_reason_refs": [P7_R54_AHR_CR12_READY_REASON_REF] if ready else [],
        "readfeel_execution_blocker_normalization_step_blocker_refs": step_blockers,
        "readfeel_execution_blocker_normalization_step_blocker_ref_count": len(step_blockers),
        "required_case_count": P7_R54_AHR_CR_REQUIRED_CASE_COUNT,
        "source_rating_row_count": cr11.get("rating_row_count") if cr11_ready else 0,
        "source_rating_row_refs": source_refs,
        "source_rating_row_ref_count": len(source_refs),
        "case_ref_ids": case_refs,
        "case_ref_id_count": len(case_refs),
        "case_ref_ids_unique": len(set(case_refs)) == len(case_refs) == P7_R54_AHR_CR_REQUIRED_CASE_COUNT,
        "blocker_rows": rows_for_output,
        "blocker_row_count": len(rows_for_output),
        "blocker_row_refs": [str(row.get("blocker_row_ref")) for row in rows_for_output],
        "blocker_row_ref_count": len(rows_for_output),
        "blocker_kind_refs": list(P7_R54_AHR_CR12_BLOCKER_KIND_REFS),
        "blocker_kind_counts": kind_counts,
        "blocker_category_refs": list(P7_R54_AHR_CR12_BLOCKER_CATEGORY_REFS),
        "blocker_category_counts": category_counts,
        "readfeel_blocker_row_count": kind_counts.get("readfeel_blocker", 0),
        "execution_blocker_row_count": kind_counts.get("execution_blocker", 0),
        "repair_required_blocker_row_count": kind_counts.get("repair_required", 0),
        "below_target_axis_blocker_row_count": kind_counts.get("below_target_axis", 0),
        "inconclusive_blocker_row_count": kind_counts.get("inconclusive_material", 0),
        "readfeel_blocker_id_counts": _count_nested_string_values(cr11.get("rating_rows") or [], "readfeel_blocker_ids") if ready else {},
        "execution_blocker_id_counts": _count_nested_string_values(cr11.get("rating_rows") or [], "execution_blocker_ids") if ready else {},
        "repair_required_ref_counts": _count_nested_string_values(cr11.get("rating_rows") or [], "repair_required_refs") if ready else {},
        "below_target_axis_ref_counts": _count_nested_string_values(cr11.get("rating_rows") or [], "below_target_axis_refs") if ready else {},
        "p5_repair_required_case_refs": p5_case_refs,
        "p5_repair_required_case_count": len(p5_case_refs),
        "p4_current_only_repair_required_case_refs": p4_case_refs,
        "p4_current_only_repair_required_case_count": len(p4_case_refs),
        "operation_blocked_case_refs": operation_case_refs,
        "operation_blocked_case_count": len(operation_case_refs),
        "inconclusive_insufficient_material_case_refs": inconclusive_case_refs,
        "inconclusive_insufficient_material_case_count": len(inconclusive_case_refs),
        "rows_bodyfree_only": ready and all(row.get("body_free") is True for row in rows_for_output),
        "readfeel_execution_blockers_separated": ready,
        "p5_repair_required_cases_not_promoted_to_p8_material_candidate": ready,
        "p4_current_repair_cases_not_promoted_to_p8_material_candidate": ready,
        "operation_blocker_cases_not_promoted_to_p8_material_candidate": ready,
        "readfeel_blocker_cases_not_promoted_to_p8_material_candidate": ready,
        "question_need_observation_normalization_allowed_next": ready,
        "actual_rating_rows_materialized_here": ready,
        "actual_human_review_executed_by_person": cr11.get("actual_human_review_executed_by_person") is True and ready,
        "actual_human_review_run_here": False,
        "actual_review_evidence_complete": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "disposal_verified": False,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR_CR12_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CR11_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(
            P7_R54_AHR_CR12_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CR11_NOT_YET_IMPLEMENTED_STEPS
        ),
        "next_required_step": P7_R54_AHR_CR13_STEP_REF if ready else P7_R54_AHR_CR12_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    material["actual_rating_rows_materialized_here"] = ready
    material["actual_human_review_executed_by_person"] = cr11.get("actual_human_review_executed_by_person") is True and ready
    material["actual_human_review_run_here"] = False
    material["actual_review_evidence_complete"] = False
    material["actual_question_need_observation_rows_materialized_here"] = False
    material["actual_disposal_receipt_materialized_here"] = False
    material["disposal_verified"] = False
    material["p5_human_blind_qa_confirmed_final"] = False
    material["p5_confirmed_final"] = False
    material["p5_final_allowed"] = False
    material["p6_limited_human_readfeel_start_allowed"] = False
    material["p6_start_allowed"] = False
    material["p8_start_allowed"] = False
    material["r52_reintake_execution_requested_here"] = False
    material["actual_r52_reintake_execution_confirmed"] = False
    material["p7_complete"] = False
    material["release_allowed"] = False
    return material


def assert_p7_r54_ahr_cr12_readfeel_execution_blocker_normalization_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CR12_READFEEL_EXECUTION_BLOCKER_NORMALIZATION_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CR12 readfeel / execution blocker normalization",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CR12_READFEEL_EXECUTION_BLOCKER_NORMALIZATION_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CR12_STEP_REF,
        operation_step_ref=P7_R54_AHR_CR12_STEP_REF,
        source="P7-R54-AHR-CR12 readfeel / execution blocker normalization",
        allowed_true_false_flag_refs=P7_R54_AHR_CR12_ALLOWED_TRUE_OPERATION_FLAG_REFS,
    )
    if data.get("cr11_schema_version") != P7_R54_AHR_CR11_RATING_ROW_NORMALIZATION_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CR12 CR11 schema changed")
    if tuple(data.get("readfeel_execution_blocker_normalization_allowed_status_refs") or ()) != P7_R54_AHR_CR12_ALLOWED_BLOCKER_NORMALIZATION_STATUS_REFS:
        raise ValueError("P7-R54-AHR-CR12 allowed status refs changed")
    _assert_current_received_basis_fields(data, actual_basis=True, source="P7-R54-AHR-CR12 blockers")
    _assert_historical_basis_fields(data, source="P7-R54-AHR-CR12 blockers")
    ready = data.get("readfeel_execution_blocker_normalization_status_ref") == P7_R54_AHR_CR12_BLOCKERS_NORMALIZED_STATUS_REF
    if ready and data.get("cr11_next_required_step") != P7_R54_AHR_CR12_STEP_REF:
        raise ValueError("P7-R54-AHR-CR12 must follow ready CR11 next step")
    if not ready and data.get("cr11_next_required_step") not in (
        P7_R54_AHR_CR12_STEP_REF,
        P7_R54_AHR_CR11_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF,
    ):
        raise ValueError("P7-R54-AHR-CR12 blocked material carries unexpected CR11 next step")
    if data.get("readfeel_execution_blocker_normalization_ready") is not ready:
        raise ValueError("P7-R54-AHR-CR12 ready flag changed")
    step_blockers = list(data.get("readfeel_execution_blocker_normalization_step_blocker_refs") or [])
    if data.get("readfeel_execution_blocker_normalization_step_blocker_ref_count") != len(step_blockers):
        raise ValueError("P7-R54-AHR-CR12 step blocker count changed")
    _assert_true_fields(
        data,
        keys=("r52_reintake_claim_blocked_here", "p6_p8_release_promotion_blocked_here", "p5_finalization_blocked_here"),
        source="P7-R54-AHR-CR12 blocker normalization",
    )
    _assert_false_fields(
        data,
        keys=(
            "actual_human_review_run_here",
            "actual_review_evidence_complete",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "disposal_verified",
            "p5_human_blind_qa_confirmed_final",
            "p5_confirmed_final",
            "p5_final_allowed",
            "p6_limited_human_readfeel_start_allowed",
            "p6_start_allowed",
            "p8_start_allowed",
            "r52_reintake_execution_requested_here",
            "actual_r52_reintake_execution_confirmed",
            "p7_complete",
            "release_allowed",
        ),
        source="P7-R54-AHR-CR12 blocker normalization",
    )
    if ready:
        if step_blockers:
            raise ValueError("P7-R54-AHR-CR12 ready material cannot carry step blockers")
        if data.get("readfeel_execution_blocker_normalization_reason_refs") != [P7_R54_AHR_CR12_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-CR12 ready reason changed")
        _assert_true_fields(
            data,
            keys=(
                "cr11_readfeel_execution_blocker_normalization_allowed_next",
                "cr11_actual_rating_rows_materialized_here",
                "cr11_actual_human_review_executed_by_person",
                "case_ref_ids_unique",
                "rows_bodyfree_only",
                "readfeel_execution_blockers_separated",
                "p5_repair_required_cases_not_promoted_to_p8_material_candidate",
                "p4_current_repair_cases_not_promoted_to_p8_material_candidate",
                "operation_blocker_cases_not_promoted_to_p8_material_candidate",
                "readfeel_blocker_cases_not_promoted_to_p8_material_candidate",
                "question_need_observation_normalization_allowed_next",
                "actual_rating_rows_materialized_here",
                "actual_human_review_executed_by_person",
            ),
            source="P7-R54-AHR-CR12 normalized blockers",
        )
        for field in ("source_rating_row_count", "source_rating_row_ref_count", "case_ref_id_count"):
            if data.get(field) != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
                raise ValueError(f"P7-R54-AHR-CR12 {field} changed")
        if tuple(data.get("blocker_kind_refs") or ()) != P7_R54_AHR_CR12_BLOCKER_KIND_REFS:
            raise ValueError("P7-R54-AHR-CR12 blocker kinds changed")
        if tuple(data.get("blocker_category_refs") or ()) != P7_R54_AHR_CR12_BLOCKER_CATEGORY_REFS:
            raise ValueError("P7-R54-AHR-CR12 blocker categories changed")
        if data.get("blocker_row_ref_count") != data.get("blocker_row_count"):
            raise ValueError("P7-R54-AHR-CR12 blocker row ref count changed")
        for row in data.get("blocker_rows") or []:
            if not isinstance(row, Mapping):
                raise ValueError("P7-R54-AHR-CR12 blocker row must be mapping")
            _assert_required_fields(
                row,
                required=P7_R54_AHR_CR12_BLOCKER_ROW_REQUIRED_FIELD_REFS,
                source="P7-R54-AHR-CR12 blocker row",
            )
            if row.get("schema_version") != P7_R54_AHR_CR12_BLOCKER_ROW_SCHEMA_VERSION:
                raise ValueError("P7-R54-AHR-CR12 blocker row schema changed")
            if row.get("blocker_kind") not in P7_R54_AHR_CR12_BLOCKER_KIND_REFS:
                raise ValueError("P7-R54-AHR-CR12 blocker kind changed")
            if row.get("blocker_category_ref") not in P7_R54_AHR_CR12_BLOCKER_CATEGORY_REFS:
                raise ValueError("P7-R54-AHR-CR12 blocker category changed")
            if row.get("p8_material_candidate_blocked") is not True:
                raise ValueError("P7-R54-AHR-CR12 blocker row must block P8 material candidate escape")
            if row.get("body_free") is not True:
                raise ValueError("P7-R54-AHR-CR12 blocker row must be body-free")
            for flag_ref in P7_R54_AHR_CR12_BLOCKER_ROW_BODYFREE_FALSE_FLAG_REFS:
                if row.get(flag_ref) is not False:
                    raise ValueError(f"P7-R54-AHR-CR12 blocker row must keep {flag_ref}=False")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CR12_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CR12 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CR12_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CR12 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_CR13_STEP_REF:
            raise ValueError("P7-R54-AHR-CR12 ready next step changed")
    else:
        if data.get("readfeel_execution_blocker_normalization_status_ref") != P7_R54_AHR_CR12_BLOCKERS_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-CR12 blocked status changed")
        if not step_blockers:
            raise ValueError("P7-R54-AHR-CR12 blocked material must carry step blockers")
        if data.get("readfeel_execution_blocker_normalization_reason_refs") != []:
            raise ValueError("P7-R54-AHR-CR12 blocked material cannot carry ready reasons")
        if data.get("blocker_rows") != [] or data.get("blocker_row_count") != 0:
            raise ValueError("P7-R54-AHR-CR12 blocked material must not carry blocker rows")
        if data.get("actual_rating_rows_materialized_here") is not False:
            raise ValueError("P7-R54-AHR-CR12 blocked material must not claim rating rows")
        if data.get("next_required_step") != P7_R54_AHR_CR12_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CR12 blocked next step changed")
    return True


def _cr13_rows_from_sources(
    *,
    cr10_rows: Sequence[Any],
    rating_rows: Sequence[Any],
    blocker_rows: Sequence[Any],
    review_session_id: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    step_blockers: list[str] = []
    if len(cr10_rows) != P7_R54_AHR_CR_REQUIRED_CASE_COUNT or len(rating_rows) != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
        step_blockers.append(P7_R54_AHR_CR13_SOURCE_ROW_COUNT_NOT_24_BLOCKER_REF)
    cr10_by_case: dict[str, Mapping[str, Any]] = {}
    for row in cr10_rows:
        if not isinstance(row, Mapping):
            step_blockers.append(P7_R54_AHR_CR13_SOURCE_ROW_INVALID_BLOCKER_REF)
            continue
        if _contains_forbidden_body_or_question_key(row):
            step_blockers.append(P7_R54_AHR_CR13_SOURCE_ROW_FORBIDDEN_KEY_BLOCKER_REF)
            continue
        cr10_by_case[clean_identifier(row.get("case_ref_id"), default="", max_length=120)] = row
    p5_blocker_cases = set(_case_refs_for_blocker_categories(
        blocker_rows,
        {
            "p5_readfeel_repair_required",
            "p5_history_connection_weak",
            "p5_creepy_or_overclaim_risk",
            "p5_self_blame_amplification_risk",
        },
    ))
    p4_blocker_cases = set(_case_refs_for_blocker_categories(blocker_rows, {"p4_current_only_surface_repair_required"}))
    operation_blocker_cases = set(_case_refs_for_blocker_categories(
        blocker_rows,
        {
            "operation_blocked_missing_receipt",
            "operation_blocked_body_leak",
            "operation_blocked_question_text",
            "operation_blocked_disposal_missing",
        },
    ))
    rows: list[dict[str, Any]] = []
    seen_case_refs: set[str] = set()
    for index, raw_row in enumerate(rating_rows, start=1):
        if not isinstance(raw_row, Mapping):
            step_blockers.append(P7_R54_AHR_CR13_SOURCE_ROW_INVALID_BLOCKER_REF)
            continue
        if _contains_forbidden_body_or_question_key(raw_row):
            step_blockers.append(P7_R54_AHR_CR13_SOURCE_ROW_FORBIDDEN_KEY_BLOCKER_REF)
            continue
        if raw_row.get("schema_version") != P7_R54_AHR_CR11_RATING_ROW_SCHEMA_VERSION:
            step_blockers.append(P7_R54_AHR_CR13_SOURCE_ROW_INVALID_BLOCKER_REF)
        case_ref_id = clean_identifier(raw_row.get("case_ref_id"), default="", max_length=120)
        seen_case_refs.add(case_ref_id)
        cr10_row = cr10_by_case.get(case_ref_id)
        if not cr10_row:
            step_blockers.append(P7_R54_AHR_CR13_CASE_REF_MISMATCH_BLOCKER_REF)
            continue
        primary_class = clean_identifier(raw_row.get("question_need_primary_class"), default="", max_length=160)
        if primary_class not in P7_R54_AHR_CR10_QUESTION_NEED_PRIMARY_CLASS_OPTION_REFS:
            step_blockers.append(P7_R54_AHR_CR13_PRIMARY_CLASS_NOT_ALLOWED_BLOCKER_REF)
        one_question_fit_ref = clean_identifier(raw_row.get("one_question_fit_ref"), default="", max_length=160)
        if one_question_fit_ref not in P7_R54_AHR_CR10_ONE_QUESTION_FIT_OPTION_REFS:
            step_blockers.append(P7_R54_AHR_CR13_ONE_QUESTION_FIT_NOT_ALLOWED_BLOCKER_REF)
        repair_required_refs = _dedupe_string_refs(raw_row.get("repair_required_refs") or (), limit=20, max_length=160)
        if any(ref not in P7_R54_AHR_CR10_REPAIR_REQUIRED_OPTION_REFS for ref in repair_required_refs):
            step_blockers.append(P7_R54_AHR_CR13_REPAIR_REQUIRED_REF_NOT_ALLOWED_BLOCKER_REF)
        ambiguity_kind_refs = _dedupe_string_refs(cr10_row.get("ambiguity_kind_refs") or (), limit=20, max_length=120)
        if not ambiguity_kind_refs:
            ambiguity_kind_refs = ["no_material_ambiguity"]
        if any(ref not in P7_R54_AHR_CR10_AMBIGUITY_KIND_OPTION_REFS for ref in ambiguity_kind_refs):
            step_blockers.append(P7_R54_AHR_CR13_AMBIGUITY_KIND_REF_NOT_ALLOWED_BLOCKER_REF)
        plan_flags = _clean_cr10_plan_candidate_flags(raw_row.get("plan_candidate_flags"))
        verdict = clean_identifier(raw_row.get("verdict"), default="", max_length=80)
        readfeel_blocker_present = case_ref_id in p5_blocker_cases or bool(raw_row.get("readfeel_blocker_ids"))
        operation_blocker_present = case_ref_id in operation_blocker_cases or bool(raw_row.get("execution_blocker_ids"))
        p4_current_surface_repair_required = case_ref_id in p4_blocker_cases or "p4_current_surface_repair_required" in repair_required_refs
        p5_repair_required = (
            case_ref_id in p5_blocker_cases
            or primary_class in P7_R54_AHR_CR13_P5_REPAIR_PRIMARY_CLASS_REFS
            or any(ref in repair_required_refs for ref in ("emlis_readfeel_repair_required", "p5_surface_repair_required", "gate_boundary_repair_required"))
        )
        heavy = primary_class == "question_would_make_immediate_observation_heavy" or one_question_fit_ref == "would_delay_immediate_observation"
        plus_candidate = primary_class == "plus_single_question_candidate_later" and plan_flags.get(
            "plus_single_question_candidate_later"
        ) is True
        premium_candidate = primary_class == "premium_deep_dive_candidate_later" and plan_flags.get(
            "premium_deep_dive_candidate_later"
        ) is True
        question_may_candidate = primary_class == "question_may_reduce_overread_risk"
        p8_signal = question_may_candidate or plus_candidate or premium_candidate or plan_flags.get("p8_design_material_candidate") is True
        p8_candidate = (
            p8_signal
            and primary_class in P7_R54_AHR_CR13_P8_MATERIAL_PRIMARY_CLASS_REFS
            and one_question_fit_ref in P7_R54_AHR_CR13_P8_MATERIAL_ONE_QUESTION_FIT_REFS
            and not p5_repair_required
            and not p4_current_surface_repair_required
            and not operation_blocker_present
            and not readfeel_blocker_present
            and not heavy
            and verdict not in {"RED", "REPAIR_REQUIRED", "BLOCKED", "NOT_REVIEWABLE"}
        )
        reason_ref = "p8_material_candidate_bodyfree_only" if p8_candidate else "not_p8_material_candidate"
        if p5_repair_required:
            reason_ref = "not_p8_material_p5_repair_required"
        elif p4_current_surface_repair_required:
            reason_ref = "not_p8_material_p4_current_only_repair_required"
        elif operation_blocker_present:
            reason_ref = "not_p8_material_operation_blocker_present"
        elif readfeel_blocker_present:
            reason_ref = "not_p8_material_readfeel_blocker_present"
        elif heavy:
            reason_ref = "not_p8_material_question_would_make_immediate_observation_heavy"
        row: dict[str, Any] = {
            "schema_version": P7_R54_AHR_CR13_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION,
            "review_session_id": review_session_id,
            "question_need_observation_row_ref": f"cr13_question_need_observation_row_{index:03d}",
            "source_rating_row_ref": clean_identifier(raw_row.get("rating_row_ref"), default=f"cr11_rating_row_{index:03d}", max_length=120),
            "source_review_result_row_ref": clean_identifier(
                raw_row.get("source_review_result_row_ref"), default=f"cr10_review_result_row_{index:03d}", max_length=120
            ),
            "case_ref_id": case_ref_id,
            "blind_case_id": clean_identifier(raw_row.get("blind_case_id"), default="", max_length=120),
            "packet_ref_id": clean_identifier(raw_row.get("packet_ref_id"), default="", max_length=120),
            "verdict": verdict,
            "question_need_primary_class": primary_class,
            "ambiguity_kind_refs": ambiguity_kind_refs,
            "ambiguity_kind_ref_count": len(ambiguity_kind_refs),
            "one_question_fit_ref": one_question_fit_ref,
            "repair_required_refs": repair_required_refs,
            "repair_required_ref_count": len(repair_required_refs),
            "plan_candidate_flags": plan_flags,
            "plus_single_question_candidate_later": plus_candidate,
            "premium_deep_dive_candidate_later": premium_candidate,
            "question_may_reduce_overread_risk": question_may_candidate,
            "p8_design_material_candidate": p8_candidate,
            "p8_material_candidate_reason_ref": reason_ref,
            "p8_implementation_spec_finalized_here": False,
            "p5_repair_required": p5_repair_required,
            "p4_current_surface_repair_required": p4_current_surface_repair_required,
            "operation_blocker_present": operation_blocker_present,
            "readfeel_blocker_present": readfeel_blocker_present,
            "question_would_make_immediate_observation_heavy": heavy,
            "p8_start_allowed": False,
            "question_text_materialized_here": False,
            "draft_question_text_materialized_here": False,
            "body_free": True,
        }
        row.update({key: False for key in P7_R54_AHR_CR13_QUESTION_OBSERVATION_ROW_BODYFREE_FALSE_FLAG_REFS})
        rows.append(row)
    expected_case_refs = set(_expected_cr04_manifest_rows_by_case_ref())
    if len(seen_case_refs) != P7_R54_AHR_CR_REQUIRED_CASE_COUNT or seen_case_refs != expected_case_refs:
        step_blockers.append(P7_R54_AHR_CR13_CASE_REF_MISMATCH_BLOCKER_REF)
    if step_blockers:
        return [], _dedupe_string_refs(step_blockers, limit=200, max_length=240)
    return rows, []


def build_p7_r54_ahr_cr13_question_need_observation_normalization(
    *,
    sanitized_selection_only_result_rows_intake: Mapping[str, Any] | None = None,
    rating_row_normalization: Mapping[str, Any] | None = None,
    readfeel_execution_blocker_normalization: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build CR13 body-free 24-row question need observation normalization."""

    cr10 = dict(sanitized_selection_only_result_rows_intake or build_p7_r54_ahr_cr10_sanitized_selection_only_result_rows_intake())
    cr11 = dict(rating_row_normalization or build_p7_r54_ahr_cr11_rating_row_normalization())
    cr12 = dict(readfeel_execution_blocker_normalization or build_p7_r54_ahr_cr12_readfeel_execution_blocker_normalization())
    assert_p7_r54_ahr_cr10_sanitized_selection_only_result_rows_intake_contract(cr10)
    assert_p7_r54_ahr_cr11_rating_row_normalization_contract(cr11)
    assert_p7_r54_ahr_cr12_readfeel_execution_blocker_normalization_contract(cr12)
    session_id = _safe_review_session_id(review_session_id)
    rows, row_blockers = _cr13_rows_from_sources(
        cr10_rows=cr10.get("review_result_rows") or (),
        rating_rows=cr11.get("rating_rows") or (),
        blocker_rows=cr12.get("blocker_rows") or (),
        review_session_id=session_id,
    )
    step_blockers: list[str] = []
    if cr10.get("sanitized_selection_only_result_rows_ready") is not True:
        step_blockers.append(P7_R54_AHR_CR13_CR10_NOT_READY_BLOCKER_REF)
    if cr11.get("rating_row_normalization_ready") is not True:
        step_blockers.append(P7_R54_AHR_CR13_CR11_NOT_READY_BLOCKER_REF)
    if cr12.get("readfeel_execution_blocker_normalization_ready") is not True:
        step_blockers.append(P7_R54_AHR_CR13_CR12_NOT_READY_BLOCKER_REF)
    if cr10.get("next_required_step") != P7_R54_AHR_CR11_STEP_REF:
        step_blockers.append(P7_R54_AHR_CR13_CR10_NEXT_STEP_NOT_CR11_BLOCKER_REF)
    if cr11.get("next_required_step") != P7_R54_AHR_CR12_STEP_REF:
        step_blockers.append(P7_R54_AHR_CR13_CR11_NEXT_STEP_NOT_CR12_BLOCKER_REF)
    if cr12.get("next_required_step") != P7_R54_AHR_CR13_STEP_REF:
        step_blockers.append(P7_R54_AHR_CR13_CR12_NEXT_STEP_NOT_CR13_BLOCKER_REF)
    if cr10.get("sanitized_review_result_row_count") != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
        step_blockers.append(P7_R54_AHR_CR13_SOURCE_ROW_COUNT_NOT_24_BLOCKER_REF)
    if cr11.get("rating_row_count") != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
        step_blockers.append(P7_R54_AHR_CR13_SOURCE_ROW_COUNT_NOT_24_BLOCKER_REF)
    step_blockers.extend(row_blockers)
    step_blockers = _dedupe_string_refs(step_blockers, limit=200, max_length=240)
    ready = not step_blockers
    rows_for_output = rows if ready else []
    case_refs = [str(row.get("case_ref_id")) for row in rows_for_output]
    p8_refs = [str(row.get("case_ref_id")) for row in rows_for_output if row.get("p8_design_material_candidate") is True]
    plus_refs = [str(row.get("case_ref_id")) for row in rows_for_output if row.get("plus_single_question_candidate_later") is True]
    premium_refs = [str(row.get("case_ref_id")) for row in rows_for_output if row.get("premium_deep_dive_candidate_later") is True]
    question_may_refs = [str(row.get("case_ref_id")) for row in rows_for_output if row.get("question_may_reduce_overread_risk") is True]
    heavy_refs = [str(row.get("case_ref_id")) for row in rows_for_output if row.get("question_would_make_immediate_observation_heavy") is True]
    p5_refs = [str(row.get("case_ref_id")) for row in rows_for_output if row.get("p5_repair_required") is True]
    p4_refs = [str(row.get("case_ref_id")) for row in rows_for_output if row.get("p4_current_surface_repair_required") is True]
    operation_refs = [str(row.get("case_ref_id")) for row in rows_for_output if row.get("operation_blocker_present") is True]
    readfeel_refs = [str(row.get("case_ref_id")) for row in rows_for_output if row.get("readfeel_blocker_present") is True]
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CR13_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CR_STEP,
        "scope": P7_R54_AHR_CR_SCOPE,
        "policy_kind": P7_R54_AHR_CR_POLICY_KIND,
        "policy_section": P7_R54_AHR_CR13_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CR13_STEP_REF,
        "current_phase": P7_R54_AHR_CR_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cr13_question_need_observation_normalization_20260628",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cr10_schema_version": cr10.get("schema_version"),
        "cr10_material_ref": cr10.get("material_id"),
        "cr10_next_required_step": cr10.get("next_required_step"),
        "cr10_sanitized_selection_only_result_rows_intake_status_ref": cr10.get(
            "sanitized_selection_only_result_rows_intake_status_ref"
        ),
        "cr10_sanitized_review_result_row_count": cr10.get("sanitized_review_result_row_count"),
        "cr11_schema_version": cr11.get("schema_version"),
        "cr11_material_ref": cr11.get("material_id"),
        "cr11_next_required_step": cr11.get("next_required_step"),
        "cr11_rating_row_normalization_status_ref": cr11.get("rating_row_normalization_status_ref"),
        "cr11_rating_row_count": cr11.get("rating_row_count"),
        "cr11_actual_rating_rows_materialized_here": cr11.get("actual_rating_rows_materialized_here"),
        "cr12_schema_version": cr12.get("schema_version"),
        "cr12_material_ref": cr12.get("material_id"),
        "cr12_next_required_step": cr12.get("next_required_step"),
        "cr12_readfeel_execution_blocker_normalization_status_ref": cr12.get(
            "readfeel_execution_blocker_normalization_status_ref"
        ),
        "cr12_question_need_observation_normalization_allowed_next": cr12.get(
            "question_need_observation_normalization_allowed_next"
        ),
        "cr12_blocker_row_count": cr12.get("blocker_row_count"),
        "cr12_p5_repair_required_case_count": cr12.get("p5_repair_required_case_count"),
        "cr12_p4_current_only_repair_required_case_count": cr12.get("p4_current_only_repair_required_case_count"),
        "cr12_operation_blocked_case_count": cr12.get("operation_blocked_case_count"),
        **_current_received_basis_fields(actual_basis=True),
        **_historical_basis_fields(),
        "question_need_observation_normalization_status_ref": (
            P7_R54_AHR_CR13_QUESTION_OBSERVATIONS_NORMALIZED_STATUS_REF
            if ready
            else P7_R54_AHR_CR13_QUESTION_OBSERVATIONS_BLOCKED_STATUS_REF
        ),
        "question_need_observation_normalization_allowed_status_refs": list(
            P7_R54_AHR_CR13_ALLOWED_QUESTION_OBSERVATION_STATUS_REFS
        ),
        "question_need_observation_normalization_ready": ready,
        "question_need_observation_normalization_reason_refs": [P7_R54_AHR_CR13_READY_REASON_REF] if ready else [],
        "question_need_observation_normalization_step_blocker_refs": step_blockers,
        "question_need_observation_normalization_step_blocker_ref_count": len(step_blockers),
        "required_case_count": P7_R54_AHR_CR_REQUIRED_CASE_COUNT,
        "source_sanitized_review_result_row_count": cr10.get("sanitized_review_result_row_count") if ready else 0,
        "source_rating_row_count": cr11.get("rating_row_count") if ready else 0,
        "question_need_observation_row_count": len(rows_for_output),
        "question_need_observation_rows": rows_for_output,
        "question_need_observation_row_refs": [str(row.get("question_need_observation_row_ref")) for row in rows_for_output],
        "question_need_observation_row_ref_count": len(rows_for_output),
        "case_ref_ids": case_refs,
        "case_ref_id_count": len(case_refs),
        "case_ref_ids_unique": len(set(case_refs)) == len(case_refs) == P7_R54_AHR_CR_REQUIRED_CASE_COUNT,
        "question_need_primary_class_options": list(P7_R54_AHR_CR10_QUESTION_NEED_PRIMARY_CLASS_OPTION_REFS),
        "question_need_primary_class_option_count": len(P7_R54_AHR_CR10_QUESTION_NEED_PRIMARY_CLASS_OPTION_REFS),
        "one_question_fit_option_refs": list(P7_R54_AHR_CR10_ONE_QUESTION_FIT_OPTION_REFS),
        "one_question_fit_option_count": len(P7_R54_AHR_CR10_ONE_QUESTION_FIT_OPTION_REFS),
        "repair_required_option_refs": list(P7_R54_AHR_CR10_REPAIR_REQUIRED_OPTION_REFS),
        "repair_required_option_count": len(P7_R54_AHR_CR10_REPAIR_REQUIRED_OPTION_REFS),
        "ambiguity_kind_option_refs": list(P7_R54_AHR_CR10_AMBIGUITY_KIND_OPTION_REFS),
        "ambiguity_kind_option_count": len(P7_R54_AHR_CR10_AMBIGUITY_KIND_OPTION_REFS),
        "plan_candidate_flag_refs": list(P7_R54_AHR_CR10_PLAN_CANDIDATE_FLAG_REFS),
        "plan_candidate_flag_count": len(P7_R54_AHR_CR10_PLAN_CANDIDATE_FLAG_REFS),
        "question_need_primary_class_counts": _count_values(rows_for_output, "question_need_primary_class") if ready else {},
        "one_question_fit_counts": _count_values(rows_for_output, "one_question_fit_ref") if ready else {},
        "ambiguity_kind_counts": _count_nested_string_values(rows_for_output, "ambiguity_kind_refs") if ready else {},
        "p8_material_candidate_case_refs": p8_refs,
        "p8_material_candidate_case_count": len(p8_refs),
        "plus_single_question_candidate_case_refs": plus_refs,
        "plus_single_question_candidate_case_count": len(plus_refs),
        "premium_deep_dive_candidate_case_refs": premium_refs,
        "premium_deep_dive_candidate_case_count": len(premium_refs),
        "question_may_reduce_overread_risk_case_refs": question_may_refs,
        "question_may_reduce_overread_risk_case_count": len(question_may_refs),
        "question_would_make_immediate_observation_heavy_case_refs": heavy_refs,
        "question_would_make_immediate_observation_heavy_case_count": len(heavy_refs),
        "p5_repair_required_case_refs": p5_refs,
        "p5_repair_required_case_count": len(p5_refs),
        "p4_current_surface_repair_required_case_refs": p4_refs,
        "p4_current_surface_repair_required_case_count": len(p4_refs),
        "operation_blocker_case_refs": operation_refs,
        "operation_blocker_case_count": len(operation_refs),
        "readfeel_blocker_case_refs": readfeel_refs,
        "readfeel_blocker_case_count": len(readfeel_refs),
        "rows_bodyfree_only": ready and all(row.get("body_free") is True for row in rows_for_output),
        "rows_have_no_question_text": ready,
        "question_need_observation_rows_normalized_here": ready,
        "actual_question_need_observation_rows_materialized_here": ready,
        "actual_rating_rows_materialized_here": ready,
        "actual_human_review_executed_by_person": cr11.get("actual_human_review_executed_by_person") is True and ready,
        "actual_human_review_run_here": False,
        "actual_review_evidence_complete": False,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "p8_question_implementation_spec_finalized_here": False,
        "p8_start_allowed": False,
        "actual_disposal_receipt_materialized_here": False,
        "disposal_verified": False,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR_CR13_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CR12_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(
            P7_R54_AHR_CR13_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CR12_NOT_YET_IMPLEMENTED_STEPS
        ),
        "next_required_step": P7_R54_AHR_CR14_STEP_REF if ready else P7_R54_AHR_CR13_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    material["actual_question_need_observation_rows_materialized_here"] = ready
    material["actual_rating_rows_materialized_here"] = ready
    material["actual_human_review_executed_by_person"] = cr11.get("actual_human_review_executed_by_person") is True and ready
    material["actual_human_review_run_here"] = False
    material["actual_review_evidence_complete"] = False
    material["question_text_materialized_here"] = False
    material["draft_question_text_materialized_here"] = False
    material["p8_question_implementation_spec_finalized_here"] = False
    material["p8_start_allowed"] = False
    material["actual_disposal_receipt_materialized_here"] = False
    material["disposal_verified"] = False
    material["p5_human_blind_qa_confirmed_final"] = False
    material["p5_confirmed_final"] = False
    material["p5_final_allowed"] = False
    material["p6_limited_human_readfeel_start_allowed"] = False
    material["p6_start_allowed"] = False
    material["r52_reintake_execution_requested_here"] = False
    material["actual_r52_reintake_execution_confirmed"] = False
    material["p7_complete"] = False
    material["release_allowed"] = False
    return material


def assert_p7_r54_ahr_cr13_question_need_observation_normalization_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CR13_QUESTION_NEED_OBSERVATION_NORMALIZATION_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CR13 question need observation normalization",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CR13_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CR13_STEP_REF,
        operation_step_ref=P7_R54_AHR_CR13_STEP_REF,
        source="P7-R54-AHR-CR13 question need observation normalization",
        allowed_true_false_flag_refs=P7_R54_AHR_CR13_ALLOWED_TRUE_OPERATION_FLAG_REFS,
    )
    if data.get("cr10_schema_version") != P7_R54_AHR_CR10_SANITIZED_SELECTION_ONLY_RESULT_ROWS_INTAKE_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CR13 CR10 schema changed")
    if data.get("cr11_schema_version") != P7_R54_AHR_CR11_RATING_ROW_NORMALIZATION_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CR13 CR11 schema changed")
    if data.get("cr12_schema_version") != P7_R54_AHR_CR12_READFEEL_EXECUTION_BLOCKER_NORMALIZATION_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CR13 CR12 schema changed")
    if tuple(data.get("question_need_observation_normalization_allowed_status_refs") or ()) != P7_R54_AHR_CR13_ALLOWED_QUESTION_OBSERVATION_STATUS_REFS:
        raise ValueError("P7-R54-AHR-CR13 allowed status refs changed")
    _assert_current_received_basis_fields(data, actual_basis=True, source="P7-R54-AHR-CR13 question observations")
    _assert_historical_basis_fields(data, source="P7-R54-AHR-CR13 question observations")
    ready = data.get("question_need_observation_normalization_status_ref") == P7_R54_AHR_CR13_QUESTION_OBSERVATIONS_NORMALIZED_STATUS_REF
    if ready:
        expected_next_steps = (
            ("cr10_next_required_step", P7_R54_AHR_CR11_STEP_REF),
            ("cr11_next_required_step", P7_R54_AHR_CR12_STEP_REF),
            ("cr12_next_required_step", P7_R54_AHR_CR13_STEP_REF),
        )
        for field_ref, expected_ref in expected_next_steps:
            if data.get(field_ref) != expected_ref:
                raise ValueError(f"P7-R54-AHR-CR13 ready material must preserve {field_ref}")
    else:
        blocked_allowed_next_steps = (
            ("cr10_next_required_step", (P7_R54_AHR_CR11_STEP_REF, P7_R54_AHR_CR10_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF)),
            ("cr11_next_required_step", (P7_R54_AHR_CR12_STEP_REF, P7_R54_AHR_CR11_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF)),
            ("cr12_next_required_step", (P7_R54_AHR_CR13_STEP_REF, P7_R54_AHR_CR12_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF)),
        )
        for field_ref, allowed_refs in blocked_allowed_next_steps:
            if data.get(field_ref) not in allowed_refs:
                raise ValueError(f"P7-R54-AHR-CR13 blocked material carries unexpected {field_ref}")
    if data.get("question_need_observation_normalization_ready") is not ready:
        raise ValueError("P7-R54-AHR-CR13 ready flag changed")
    step_blockers = list(data.get("question_need_observation_normalization_step_blocker_refs") or [])
    if data.get("question_need_observation_normalization_step_blocker_ref_count") != len(step_blockers):
        raise ValueError("P7-R54-AHR-CR13 step blocker count changed")
    _assert_true_fields(
        data,
        keys=("r52_reintake_claim_blocked_here", "p6_p8_release_promotion_blocked_here", "p5_finalization_blocked_here"),
        source="P7-R54-AHR-CR13 question observations",
    )
    _assert_false_fields(
        data,
        keys=(
            "actual_human_review_run_here",
            "actual_review_evidence_complete",
            "question_text_materialized_here",
            "draft_question_text_materialized_here",
            "p8_question_implementation_spec_finalized_here",
            "p8_start_allowed",
            "actual_disposal_receipt_materialized_here",
            "disposal_verified",
            "p5_human_blind_qa_confirmed_final",
            "p5_confirmed_final",
            "p5_final_allowed",
            "p6_limited_human_readfeel_start_allowed",
            "p6_start_allowed",
            "r52_reintake_execution_requested_here",
            "actual_r52_reintake_execution_confirmed",
            "p7_complete",
            "release_allowed",
        ),
        source="P7-R54-AHR-CR13 question observations",
    )
    if ready:
        if step_blockers:
            raise ValueError("P7-R54-AHR-CR13 ready material cannot carry step blockers")
        if data.get("question_need_observation_normalization_reason_refs") != [P7_R54_AHR_CR13_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-CR13 ready reason changed")
        _assert_true_fields(
            data,
            keys=(
                "cr12_question_need_observation_normalization_allowed_next",
                "case_ref_ids_unique",
                "rows_bodyfree_only",
                "rows_have_no_question_text",
                "question_need_observation_rows_normalized_here",
                "actual_question_need_observation_rows_materialized_here",
                "actual_rating_rows_materialized_here",
                "actual_human_review_executed_by_person",
            ),
            source="P7-R54-AHR-CR13 normalized question observations",
        )
        for field in (
            "source_sanitized_review_result_row_count",
            "source_rating_row_count",
            "question_need_observation_row_count",
            "question_need_observation_row_ref_count",
            "case_ref_id_count",
        ):
            if data.get(field) != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
                raise ValueError(f"P7-R54-AHR-CR13 {field} changed")
        if tuple(data.get("question_need_primary_class_options") or ()) != P7_R54_AHR_CR10_QUESTION_NEED_PRIMARY_CLASS_OPTION_REFS:
            raise ValueError("P7-R54-AHR-CR13 primary class options changed")
        if tuple(data.get("one_question_fit_option_refs") or ()) != P7_R54_AHR_CR10_ONE_QUESTION_FIT_OPTION_REFS:
            raise ValueError("P7-R54-AHR-CR13 one question options changed")
        for row in data.get("question_need_observation_rows") or []:
            if not isinstance(row, Mapping):
                raise ValueError("P7-R54-AHR-CR13 question observation row must be mapping")
            _assert_required_fields(
                row,
                required=P7_R54_AHR_CR13_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS,
                source="P7-R54-AHR-CR13 question observation row",
            )
            if row.get("schema_version") != P7_R54_AHR_CR13_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION:
                raise ValueError("P7-R54-AHR-CR13 row schema changed")
            if row.get("body_free") is not True:
                raise ValueError("P7-R54-AHR-CR13 row must be body-free")
            if row.get("question_text_materialized_here") is not False or row.get("draft_question_text_materialized_here") is not False:
                raise ValueError("P7-R54-AHR-CR13 row must not materialize question text")
            if row.get("p8_implementation_spec_finalized_here") is not False or row.get("p8_start_allowed") is not False:
                raise ValueError("P7-R54-AHR-CR13 row must not start/finalize P8")
            if row.get("question_need_primary_class") not in P7_R54_AHR_CR10_QUESTION_NEED_PRIMARY_CLASS_OPTION_REFS:
                raise ValueError("P7-R54-AHR-CR13 row primary class changed")
            if row.get("one_question_fit_ref") not in P7_R54_AHR_CR10_ONE_QUESTION_FIT_OPTION_REFS:
                raise ValueError("P7-R54-AHR-CR13 row one question fit changed")
            if any(ref not in P7_R54_AHR_CR10_REPAIR_REQUIRED_OPTION_REFS for ref in row.get("repair_required_refs") or []):
                raise ValueError("P7-R54-AHR-CR13 row repair refs changed")
            if any(ref not in P7_R54_AHR_CR10_AMBIGUITY_KIND_OPTION_REFS for ref in row.get("ambiguity_kind_refs") or []):
                raise ValueError("P7-R54-AHR-CR13 row ambiguity refs changed")
            if row.get("p8_design_material_candidate") is True:
                for blocker_flag in (
                    "p5_repair_required",
                    "p4_current_surface_repair_required",
                    "operation_blocker_present",
                    "readfeel_blocker_present",
                    "question_would_make_immediate_observation_heavy",
                ):
                    if row.get(blocker_flag) is True:
                        raise ValueError("P7-R54-AHR-CR13 cannot promote repair/blocker/heavy rows to P8 material")
            for flag_ref in P7_R54_AHR_CR13_QUESTION_OBSERVATION_ROW_BODYFREE_FALSE_FLAG_REFS:
                if row.get(flag_ref) is not False:
                    raise ValueError(f"P7-R54-AHR-CR13 row must keep {flag_ref}=False")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CR13_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CR13 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CR13_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CR13 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_CR14_STEP_REF:
            raise ValueError("P7-R54-AHR-CR13 ready next step changed")
    else:
        if data.get("question_need_observation_normalization_status_ref") != P7_R54_AHR_CR13_QUESTION_OBSERVATIONS_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-CR13 blocked status changed")
        if not step_blockers:
            raise ValueError("P7-R54-AHR-CR13 blocked material must carry step blockers")
        if data.get("question_need_observation_normalization_reason_refs") != []:
            raise ValueError("P7-R54-AHR-CR13 blocked material cannot carry ready reasons")
        if data.get("question_need_observation_rows") != [] or data.get("question_need_observation_row_count") != 0:
            raise ValueError("P7-R54-AHR-CR13 blocked material must not carry question observation rows")
        if data.get("actual_question_need_observation_rows_materialized_here") is not False:
            raise ValueError("P7-R54-AHR-CR13 blocked material must not claim question rows")
        if data.get("next_required_step") != P7_R54_AHR_CR13_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CR13 blocked next step changed")
    return True


# Alias names for CR12/CR13 design/documentation wording.
def build_p7_r54_ahr_current_received_actual_local_review_operation_readfeel_execution_blocker_normalization_bodyfree(
    *,
    rating_row_normalization: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_cr12_readfeel_execution_blocker_normalization(
        rating_row_normalization=rating_row_normalization,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_current_received_actual_local_review_operation_readfeel_execution_blocker_normalization_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_cr12_readfeel_execution_blocker_normalization_contract(data)


def build_p7_r54_ahr_current_received_actual_local_review_operation_question_need_observation_normalization_bodyfree(
    *,
    sanitized_selection_only_result_rows_intake: Mapping[str, Any] | None = None,
    rating_row_normalization: Mapping[str, Any] | None = None,
    readfeel_execution_blocker_normalization: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_cr13_question_need_observation_normalization(
        sanitized_selection_only_result_rows_intake=sanitized_selection_only_result_rows_intake,
        rating_row_normalization=rating_row_normalization,
        readfeel_execution_blocker_normalization=readfeel_execution_blocker_normalization,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_current_received_actual_local_review_operation_question_need_observation_normalization_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_cr13_question_need_observation_normalization_contract(data)


# ---------------------------------------------------------------------------
# R54-AHR-CR14 / R54-AHR-CR15: rating-question consistency guard and
# pause/abort/expiration/disposal receipt.  These helpers keep the review
# evidence chain body-free and no-touch.  CR14 prevents weak ratings, repair
# rows, operation blockers, heavy immediate-observation rows, and insufficient
# material rows from being promoted to P8 material.  CR15 records only a
# body-free lifecycle/disposal receipt and never stores packet content, local
# paths, body hashes, reviewer notes, question text, or public/runtime changes.

P7_R54_AHR_CR14_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_received_actual_local_review_operation."
    "cr14_rating_question_consistency_guard.bodyfree.v1"
)
P7_R54_AHR_CR15_DISPOSAL_RECEIPT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_received_actual_local_review_operation."
    "cr15_pause_abort_expiration_disposal_receipt.bodyfree.v1"
)
P7_R54_AHR_CR14_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_received_actual_local_review_operation."
    "cr14_rating_question_consistency_issue_row.bodyfree.v1"
)
P7_R54_AHR_CR_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CR14_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION
)
P7_R54_AHR_CR_DISPOSAL_RECEIPT_SCHEMA_VERSION: Final = P7_R54_AHR_CR15_DISPOSAL_RECEIPT_SCHEMA_VERSION

P7_R54_AHR_CR14_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR13_IMPLEMENTED_STEPS,
    P7_R54_AHR_CR14_STEP_REF,
)
P7_R54_AHR_CR14_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CR_STEP_REFS[15:]
P7_R54_AHR_CR15_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR14_IMPLEMENTED_STEPS,
    P7_R54_AHR_CR15_STEP_REF,
)
P7_R54_AHR_CR15_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CR_STEP_REFS[16:]

P7_R54_AHR_CR14_GUARD_PASSED_STATUS_REF: Final = "CR14_RATING_QUESTION_CONSISTENCY_GUARD_PASSED_BODYFREE"
P7_R54_AHR_CR14_GUARD_FAILED_STATUS_REF: Final = "CR14_RATING_QUESTION_CONSISTENCY_GUARD_FAILED_BODYFREE"
P7_R54_AHR_CR14_GUARD_BLOCKED_STATUS_REF: Final = "CR14_RATING_QUESTION_CONSISTENCY_GUARD_BLOCKED"
P7_R54_AHR_CR14_ALLOWED_GUARD_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR14_GUARD_PASSED_STATUS_REF,
    P7_R54_AHR_CR14_GUARD_FAILED_STATUS_REF,
    P7_R54_AHR_CR14_GUARD_BLOCKED_STATUS_REF,
)
P7_R54_AHR_CR14_READY_REASON_REF: Final = "CR14_RATING_QUESTION_CONSISTENCY_GUARD_PASSED_NO_ISSUES"
P7_R54_AHR_CR14_FAILED_REASON_REF: Final = "CR14_RATING_QUESTION_CONSISTENCY_ISSUES_BLOCK_EVIDENCE_COMPLETE"
P7_R54_AHR_CR14_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "rating_question_consistency_guard_or_stop"
P7_R54_AHR_CR14_ISSUE_REPAIR_OR_BLOCKER_P8_ESCAPE_REF: Final = "repair_or_blocker_p8_candidate_escape"
P7_R54_AHR_CR14_ISSUE_RATING_BELOW_TARGET_P8_ESCAPE_REF: Final = "rating_below_target_p8_candidate_escape"
P7_R54_AHR_CR14_ISSUE_CREEPY_OVERCLAIM_P8_ESCAPE_REF: Final = "creepy_or_overclaim_risk_question_escape"
P7_R54_AHR_CR14_ISSUE_SELF_BLAME_P8_ESCAPE_REF: Final = "self_blame_risk_question_escape"
P7_R54_AHR_CR14_ISSUE_HEAVY_OBSERVATION_P8_ESCAPE_REF: Final = "immediate_observation_heavy_p8_candidate_escape"
P7_R54_AHR_CR14_ISSUE_INSUFFICIENT_MATERIAL_P8_ESCAPE_REF: Final = "insufficient_material_p8_candidate_escape"
P7_R54_AHR_CR14_ISSUE_REASON_CHANGED_REF: Final = "p8_candidate_reason_inconsistent_with_question_observation"
P7_R54_AHR_CR14_CR11_NOT_READY_BLOCKER_REF: Final = "cr11_rating_rows_not_ready"
P7_R54_AHR_CR14_CR12_NOT_READY_BLOCKER_REF: Final = "cr12_blocker_normalization_not_ready"
P7_R54_AHR_CR14_CR13_NOT_READY_BLOCKER_REF: Final = "cr13_question_observation_not_ready"
P7_R54_AHR_CR14_CR11_NEXT_STEP_NOT_CR12_BLOCKER_REF: Final = "cr11_next_step_not_cr12"
P7_R54_AHR_CR14_CR12_NEXT_STEP_NOT_CR13_BLOCKER_REF: Final = "cr12_next_step_not_cr13"
P7_R54_AHR_CR14_CR13_NEXT_STEP_NOT_CR14_BLOCKER_REF: Final = "cr13_next_step_not_cr14"
P7_R54_AHR_CR14_SOURCE_ROW_INVALID_BLOCKER_REF: Final = "cr14_source_row_invalid"
P7_R54_AHR_CR14_SOURCE_ROW_COUNT_NOT_24_BLOCKER_REF: Final = "cr14_source_row_count_not_24"
P7_R54_AHR_CR14_SOURCE_ROW_FORBIDDEN_KEY_BLOCKER_REF: Final = "cr14_source_row_forbidden_body_question_path_hash_key"
P7_R54_AHR_CR14_CASE_REF_MISMATCH_BLOCKER_REF: Final = "cr14_case_ref_mismatch_between_rating_and_question_rows"
P7_R54_AHR_CR14_CONSISTENCY_ISSUE_TYPE_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR14_ISSUE_REPAIR_OR_BLOCKER_P8_ESCAPE_REF,
    P7_R54_AHR_CR14_ISSUE_RATING_BELOW_TARGET_P8_ESCAPE_REF,
    P7_R54_AHR_CR14_ISSUE_CREEPY_OVERCLAIM_P8_ESCAPE_REF,
    P7_R54_AHR_CR14_ISSUE_SELF_BLAME_P8_ESCAPE_REF,
    P7_R54_AHR_CR14_ISSUE_HEAVY_OBSERVATION_P8_ESCAPE_REF,
    P7_R54_AHR_CR14_ISSUE_INSUFFICIENT_MATERIAL_P8_ESCAPE_REF,
    P7_R54_AHR_CR14_ISSUE_REASON_CHANGED_REF,
)
P7_R54_AHR_CR14_RISK_AXIS_REFS: Final[tuple[str, ...]] = (
    "creepy_absence",
    "overclaim_absence",
    "self_blame_non_amplification",
)
P7_R54_AHR_CR14_ALLOWED_TRUE_OPERATION_FLAG_REFS: Final[tuple[str, ...]] = (
    "actual_human_review_executed_by_person",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
)
P7_R54_AHR_CR14_CONSISTENCY_ISSUE_ROW_BODYFREE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR11_RATING_ROW_BODYFREE_FALSE_FLAG_REFS
)
P7_R54_AHR_CR14_CONSISTENCY_ISSUE_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "consistency_issue_row_ref",
    "source_rating_row_ref",
    "source_question_need_observation_row_ref",
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
    "consistency_issue_type_ref",
    "consistency_issue_reason_ref",
    "rating_question_consistency_guard_blocks_evidence_complete",
    "p8_material_candidate_blocked",
    "body_free",
    *P7_R54_AHR_CR14_CONSISTENCY_ISSUE_ROW_BODYFREE_FALSE_FLAG_REFS,
)
P7_R54_AHR_CR14_RATING_QUESTION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR_BASE_REQUIRED_FIELD_REFS,
    "cr11_schema_version",
    "cr11_material_ref",
    "cr11_next_required_step",
    "cr11_rating_row_normalization_status_ref",
    "cr11_rating_row_count",
    "cr11_actual_rating_rows_materialized_here",
    "cr12_schema_version",
    "cr12_material_ref",
    "cr12_next_required_step",
    "cr12_readfeel_execution_blocker_normalization_status_ref",
    "cr12_blocker_row_count",
    "cr13_schema_version",
    "cr13_material_ref",
    "cr13_next_required_step",
    "cr13_question_need_observation_normalization_status_ref",
    "cr13_question_need_observation_row_count",
    "cr13_actual_question_need_observation_rows_materialized_here",
    *P7_R54_AHR_CR_CURRENT_RECEIVED_BASIS_FIELD_REFS,
    *P7_R54_AHR_CR_HISTORICAL_BASIS_FIELD_REFS,
    "rating_question_consistency_guard_status_ref",
    "rating_question_consistency_guard_allowed_status_refs",
    "rating_question_consistency_guard_evaluated",
    "rating_question_consistency_guard_passed",
    "rating_question_consistency_guard_reason_refs",
    "rating_question_consistency_guard_step_blocker_refs",
    "rating_question_consistency_guard_step_blocker_ref_count",
    "required_case_count",
    "source_rating_row_count",
    "source_question_need_observation_row_count",
    "source_blocker_row_count",
    "case_ref_ids",
    "case_ref_id_count",
    "case_ref_ids_unique",
    "consistency_issue_rows",
    "consistency_issue_row_count",
    "consistency_issue_row_refs",
    "consistency_issue_row_ref_count",
    "consistency_issue_type_refs",
    "consistency_issue_type_counts",
    "p8_material_candidate_case_refs",
    "p8_material_candidate_case_count",
    "rating_below_target_p8_escape_case_refs",
    "rating_below_target_p8_escape_case_count",
    "risk_axis_p8_escape_case_refs",
    "risk_axis_p8_escape_case_count",
    "repair_or_blocker_p8_escape_case_refs",
    "repair_or_blocker_p8_escape_case_count",
    "heavy_observation_p8_escape_case_refs",
    "heavy_observation_p8_escape_case_count",
    "insufficient_material_p8_escape_case_refs",
    "insufficient_material_p8_escape_case_count",
    "rows_bodyfree_only",
    "rows_have_no_question_text",
    "rating_question_consistency_guarded_here",
    "rating_below_target_cannot_escape_to_p8_material",
    "creepy_or_overclaim_risk_cannot_escape_to_question_candidate",
    "self_blame_risk_cannot_escape_to_question_candidate",
    "immediate_observation_heavy_cannot_escape_to_p8_material",
    "insufficient_material_cannot_escape_to_p8_material",
    "repair_or_blocker_rows_cannot_escape_to_p8_material",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_review_evidence_complete",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "p8_question_implementation_spec_finalized_here",
    "p8_start_allowed",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CR_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CR_FALSE_FLAG_REFS,
)
P7_R54_AHR_CR_RATING_QUESTION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CR14_RATING_QUESTION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS
)

P7_R54_AHR_CR15_DISPOSAL_VERIFIED_STATUS_REF: Final = "CR15_DISPOSAL_RECEIPT_VERIFIED_BODYFREE"
P7_R54_AHR_CR15_DISPOSAL_BLOCKED_STATUS_REF: Final = "CR15_DISPOSAL_RECEIPT_BLOCKED_OR_FAILED"
P7_R54_AHR_CR15_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR15_DISPOSAL_VERIFIED_STATUS_REF,
    P7_R54_AHR_CR15_DISPOSAL_BLOCKED_STATUS_REF,
)
P7_R54_AHR_CR15_READY_REASON_REF: Final = "CR15_BODYFREE_DISPOSAL_RECEIPT_VERIFIED_LIFECYCLE_CLOSED"
P7_R54_AHR_CR15_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "disposal_receipt_or_stop"
P7_R54_AHR_CR15_CR14_NOT_READY_BLOCKER_REF: Final = "cr14_consistency_guard_not_passed"
P7_R54_AHR_CR15_CR14_NEXT_STEP_NOT_CR15_BLOCKER_REF: Final = "cr14_next_step_not_cr15"
P7_R54_AHR_CR15_DISPOSAL_RECEIPT_MISSING_BLOCKER_REF: Final = "disposal_receipt_ref_missing"
P7_R54_AHR_CR15_DISPOSAL_STATUS_NOT_ALLOWED_BLOCKER_REF: Final = "disposal_status_ref_not_allowed"
P7_R54_AHR_CR15_BODY_REMOVED_REQUIRED_BLOCKER_REF: Final = "packet_materialized_body_removed_not_confirmed"
P7_R54_AHR_CR15_BODY_HASH_STORED_BLOCKER_REF: Final = "body_hash_or_content_hash_stored"
P7_R54_AHR_CR15_LOCAL_PATH_INCLUDED_BLOCKER_REF: Final = "local_absolute_path_included"
P7_R54_AHR_CR15_REVIEWER_NOTES_BODY_STORED_BLOCKER_REF: Final = "reviewer_notes_body_stored"
P7_R54_AHR_CR15_RECEIPT_FORBIDDEN_KEY_BLOCKER_REF: Final = "disposal_receipt_contains_forbidden_body_question_path_hash_key"
P7_R54_AHR_CR15_DISPOSAL_FAILED_BLOCKER_REF: Final = "disposal_failed"
P7_R54_AHR_CR15_DISPOSAL_STATUS_REFS: Final[tuple[str, ...]] = (
    "BODY_PURGED",
    "LOCAL_ONLY_PACKET_NOT_MATERIALIZED",
    "DISPOSAL_FAILED",
)
P7_R54_AHR_CR15_DEFAULT_DISPOSAL_RECEIPT_REF: Final = "R54_AHR_CR15_BODYFREE_DISPOSAL_RECEIPT_REF_20260628"
P7_R54_AHR_CR15_DEFAULT_RETENTION_POLICY_REF: Final = "local_body_full_packet_max_72h_or_shorter"
P7_R54_AHR_CR15_DEFAULT_EXPIRATION_POLICY_REF: Final = "local_body_full_packet_expired_or_disposed_before_export"
P7_R54_AHR_CR15_DEFAULT_PAUSE_ABORT_STATUS_REF: Final = "not_paused_not_aborted_lifecycle_closed_bodyfree"
P7_R54_AHR_CR15_ALLOWED_TRUE_OPERATION_FLAG_REFS: Final[tuple[str, ...]] = (
    "actual_human_review_executed_by_person",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
)
P7_R54_AHR_CR15_DISPOSAL_RECEIPT_REQUIRED_INPUT_FIELD_REFS: Final[tuple[str, ...]] = (
    "disposal_receipt_ref",
    "disposal_status_ref",
    "packet_materialized_for_review",
    "body_removed",
    "content_hash_of_body_stored",
    "body_hash_stored",
    "local_absolute_path_included",
    "reviewer_notes_body_stored",
    "pause_abort_status_ref",
    "retention_policy_ref",
    "expiration_policy_ref",
    "body_free",
)
P7_R54_AHR_CR15_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR_BASE_REQUIRED_FIELD_REFS,
    "cr14_schema_version",
    "cr14_material_ref",
    "cr14_next_required_step",
    "cr14_rating_question_consistency_guard_status_ref",
    "cr14_rating_question_consistency_guard_passed",
    "cr14_consistency_issue_row_count",
    "cr14_actual_rating_rows_materialized_here",
    "cr14_actual_question_need_observation_rows_materialized_here",
    *P7_R54_AHR_CR_CURRENT_RECEIVED_BASIS_FIELD_REFS,
    *P7_R54_AHR_CR_HISTORICAL_BASIS_FIELD_REFS,
    "pause_abort_expiration_disposal_receipt_status_ref",
    "pause_abort_expiration_disposal_receipt_allowed_status_refs",
    "pause_abort_expiration_disposal_receipt_ready",
    "pause_abort_expiration_disposal_receipt_reason_refs",
    "pause_abort_expiration_disposal_receipt_step_blocker_refs",
    "pause_abort_expiration_disposal_receipt_step_blocker_ref_count",
    "disposal_receipt_input_provided",
    "disposal_receipt_ref",
    "disposal_receipt_ref_present",
    "disposal_status_ref",
    "disposal_status_allowed_refs",
    "disposal_status_ref_allowed",
    "packet_materialized_for_review",
    "body_removed",
    "body_removed_required",
    "body_removed_requirement_satisfied",
    "content_hash_of_body_stored",
    "body_hash_stored",
    "local_absolute_path_included",
    "reviewer_notes_body_stored",
    "pause_abort_status_ref",
    "retention_policy_ref",
    "expiration_policy_ref",
    "receipt_bodyfree_only",
    "receipt_has_no_body_path_hash",
    "local_only_packet_lifecycle_closed_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_human_review_executed_by_person",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "actual_human_review_run_here",
    "actual_review_evidence_complete",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "p8_question_implementation_spec_finalized_here",
    "p8_start_allowed",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CR_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CR_FALSE_FLAG_REFS,
)
P7_R54_AHR_CR_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS: Final = P7_R54_AHR_CR15_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS


def _cr14_make_issue_row(
    *,
    index: int,
    review_session_id: str,
    issue_type_ref: str,
    reason_ref: str,
    rating_row: Mapping[str, Any],
    question_row: Mapping[str, Any],
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CR14_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION,
        "review_session_id": review_session_id,
        "consistency_issue_row_ref": f"cr14_consistency_issue_row_{index:03d}",
        "source_rating_row_ref": clean_identifier(rating_row.get("rating_row_ref"), default="", max_length=120),
        "source_question_need_observation_row_ref": clean_identifier(
            question_row.get("question_need_observation_row_ref"), default="", max_length=120
        ),
        "case_ref_id": clean_identifier(question_row.get("case_ref_id"), default="", max_length=120),
        "blind_case_id": clean_identifier(question_row.get("blind_case_id"), default="", max_length=120),
        "packet_ref_id": clean_identifier(question_row.get("packet_ref_id"), default="", max_length=120),
        "consistency_issue_type_ref": issue_type_ref,
        "consistency_issue_reason_ref": reason_ref,
        "rating_question_consistency_guard_blocks_evidence_complete": True,
        "p8_material_candidate_blocked": True,
        "body_free": True,
    }
    row.update({key: False for key in P7_R54_AHR_CR14_CONSISTENCY_ISSUE_ROW_BODYFREE_FALSE_FLAG_REFS})
    return row


def _cr14_consistency_issue_rows_from_sources(
    *,
    rating_rows: Sequence[Any],
    question_rows: Sequence[Any],
    review_session_id: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    step_blockers: list[str] = []
    if len(rating_rows) != P7_R54_AHR_CR_REQUIRED_CASE_COUNT or len(question_rows) != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
        step_blockers.append(P7_R54_AHR_CR14_SOURCE_ROW_COUNT_NOT_24_BLOCKER_REF)
    rating_by_case: dict[str, Mapping[str, Any]] = {}
    for row in rating_rows:
        if not isinstance(row, Mapping):
            step_blockers.append(P7_R54_AHR_CR14_SOURCE_ROW_INVALID_BLOCKER_REF)
            continue
        if _contains_forbidden_body_or_question_key(row):
            step_blockers.append(P7_R54_AHR_CR14_SOURCE_ROW_FORBIDDEN_KEY_BLOCKER_REF)
            continue
        if row.get("schema_version") != P7_R54_AHR_CR11_RATING_ROW_SCHEMA_VERSION:
            step_blockers.append(P7_R54_AHR_CR14_SOURCE_ROW_INVALID_BLOCKER_REF)
        rating_by_case[clean_identifier(row.get("case_ref_id"), default="", max_length=120)] = row
    issue_rows: list[dict[str, Any]] = []
    issue_index = 1
    seen_question_case_refs: set[str] = set()
    for qrow in question_rows:
        if not isinstance(qrow, Mapping):
            step_blockers.append(P7_R54_AHR_CR14_SOURCE_ROW_INVALID_BLOCKER_REF)
            continue
        if _contains_forbidden_body_or_question_key(qrow):
            step_blockers.append(P7_R54_AHR_CR14_SOURCE_ROW_FORBIDDEN_KEY_BLOCKER_REF)
            continue
        if qrow.get("schema_version") != P7_R54_AHR_CR13_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION:
            step_blockers.append(P7_R54_AHR_CR14_SOURCE_ROW_INVALID_BLOCKER_REF)
        case_ref_id = clean_identifier(qrow.get("case_ref_id"), default="", max_length=120)
        seen_question_case_refs.add(case_ref_id)
        rating_row = rating_by_case.get(case_ref_id)
        if not rating_row:
            step_blockers.append(P7_R54_AHR_CR14_CASE_REF_MISMATCH_BLOCKER_REF)
            continue
        p8_candidate = qrow.get("p8_design_material_candidate") is True
        below_axes = set(_dedupe_string_refs(rating_row.get("below_target_axis_refs") or (), limit=20, max_length=120))
        primary_class = clean_identifier(qrow.get("question_need_primary_class"), default="", max_length=160)
        one_question_fit_ref = clean_identifier(qrow.get("one_question_fit_ref"), default="", max_length=160)
        repair_or_blocker = any(
            qrow.get(flag_ref) is True
            for flag_ref in (
                "p5_repair_required",
                "p4_current_surface_repair_required",
                "operation_blocker_present",
                "readfeel_blocker_present",
            )
        )
        if p8_candidate and repair_or_blocker:
            issue_rows.append(
                _cr14_make_issue_row(
                    index=issue_index,
                    review_session_id=review_session_id,
                    issue_type_ref=P7_R54_AHR_CR14_ISSUE_REPAIR_OR_BLOCKER_P8_ESCAPE_REF,
                    reason_ref="p5_p4_operation_or_readfeel_blocker_cannot_be_p8_material",
                    rating_row=rating_row,
                    question_row=qrow,
                )
            )
            issue_index += 1
        if p8_candidate and below_axes:
            issue_rows.append(
                _cr14_make_issue_row(
                    index=issue_index,
                    review_session_id=review_session_id,
                    issue_type_ref=P7_R54_AHR_CR14_ISSUE_RATING_BELOW_TARGET_P8_ESCAPE_REF,
                    reason_ref="below_target_rating_cannot_be_p8_material_candidate",
                    rating_row=rating_row,
                    question_row=qrow,
                )
            )
            issue_index += 1
        if p8_candidate and (below_axes & {"creepy_absence", "overclaim_absence"}):
            issue_rows.append(
                _cr14_make_issue_row(
                    index=issue_index,
                    review_session_id=review_session_id,
                    issue_type_ref=P7_R54_AHR_CR14_ISSUE_CREEPY_OVERCLAIM_P8_ESCAPE_REF,
                    reason_ref="creepy_or_overclaim_risk_requires_repair_not_question_escape",
                    rating_row=rating_row,
                    question_row=qrow,
                )
            )
            issue_index += 1
        if p8_candidate and "self_blame_non_amplification" in below_axes:
            issue_rows.append(
                _cr14_make_issue_row(
                    index=issue_index,
                    review_session_id=review_session_id,
                    issue_type_ref=P7_R54_AHR_CR14_ISSUE_SELF_BLAME_P8_ESCAPE_REF,
                    reason_ref="self_blame_risk_requires_repair_not_question_escape",
                    rating_row=rating_row,
                    question_row=qrow,
                )
            )
            issue_index += 1
        if p8_candidate and qrow.get("question_would_make_immediate_observation_heavy") is True:
            issue_rows.append(
                _cr14_make_issue_row(
                    index=issue_index,
                    review_session_id=review_session_id,
                    issue_type_ref=P7_R54_AHR_CR14_ISSUE_HEAVY_OBSERVATION_P8_ESCAPE_REF,
                    reason_ref="immediate_observation_heavy_case_cannot_be_p8_material_candidate",
                    rating_row=rating_row,
                    question_row=qrow,
                )
            )
            issue_index += 1
        if p8_candidate and (
            primary_class == "insufficient_material_execution_blocker" or one_question_fit_ref == "insufficient_material"
        ):
            issue_rows.append(
                _cr14_make_issue_row(
                    index=issue_index,
                    review_session_id=review_session_id,
                    issue_type_ref=P7_R54_AHR_CR14_ISSUE_INSUFFICIENT_MATERIAL_P8_ESCAPE_REF,
                    reason_ref="insufficient_material_cannot_be_p8_material_candidate",
                    rating_row=rating_row,
                    question_row=qrow,
                )
            )
            issue_index += 1
        if p8_candidate and qrow.get("p8_material_candidate_reason_ref") != "p8_material_candidate_bodyfree_only":
            issue_rows.append(
                _cr14_make_issue_row(
                    index=issue_index,
                    review_session_id=review_session_id,
                    issue_type_ref=P7_R54_AHR_CR14_ISSUE_REASON_CHANGED_REF,
                    reason_ref="p8_candidate_reason_ref_must_remain_bodyfree_candidate_only",
                    rating_row=rating_row,
                    question_row=qrow,
                )
            )
            issue_index += 1
    expected_case_refs = set(_expected_cr04_manifest_rows_by_case_ref())
    if len(seen_question_case_refs) != P7_R54_AHR_CR_REQUIRED_CASE_COUNT or seen_question_case_refs != expected_case_refs:
        step_blockers.append(P7_R54_AHR_CR14_CASE_REF_MISMATCH_BLOCKER_REF)
    if step_blockers:
        return [], _dedupe_string_refs(step_blockers, limit=200, max_length=240)
    return issue_rows, []


def build_p7_r54_ahr_cr14_rating_question_consistency_guard(
    *,
    rating_row_normalization: Mapping[str, Any] | None = None,
    readfeel_execution_blocker_normalization: Mapping[str, Any] | None = None,
    question_need_observation_normalization: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build CR14 body-free rating-question consistency guard material."""

    cr11 = dict(rating_row_normalization or build_p7_r54_ahr_cr11_rating_row_normalization())
    cr12 = dict(
        readfeel_execution_blocker_normalization
        or build_p7_r54_ahr_cr12_readfeel_execution_blocker_normalization(rating_row_normalization=cr11)
    )
    cr13 = dict(
        question_need_observation_normalization
        or build_p7_r54_ahr_cr13_question_need_observation_normalization(
            rating_row_normalization=cr11,
            readfeel_execution_blocker_normalization=cr12,
        )
    )
    assert_p7_r54_ahr_cr11_rating_row_normalization_contract(cr11)
    assert_p7_r54_ahr_cr12_readfeel_execution_blocker_normalization_contract(cr12)
    assert_p7_r54_ahr_cr13_question_need_observation_normalization_contract(cr13)
    session_id = _safe_review_session_id(review_session_id)
    source_blockers: list[str] = []
    if cr11.get("rating_row_normalization_status_ref") != P7_R54_AHR_CR11_RATING_ROWS_NORMALIZED_STATUS_REF:
        source_blockers.append(P7_R54_AHR_CR14_CR11_NOT_READY_BLOCKER_REF)
    if cr12.get("readfeel_execution_blocker_normalization_status_ref") != P7_R54_AHR_CR12_BLOCKERS_NORMALIZED_STATUS_REF:
        source_blockers.append(P7_R54_AHR_CR14_CR12_NOT_READY_BLOCKER_REF)
    if cr13.get("question_need_observation_normalization_status_ref") != P7_R54_AHR_CR13_QUESTION_OBSERVATIONS_NORMALIZED_STATUS_REF:
        source_blockers.append(P7_R54_AHR_CR14_CR13_NOT_READY_BLOCKER_REF)
    if cr11.get("next_required_step") not in (P7_R54_AHR_CR12_STEP_REF, P7_R54_AHR_CR11_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF):
        source_blockers.append(P7_R54_AHR_CR14_CR11_NEXT_STEP_NOT_CR12_BLOCKER_REF)
    if cr12.get("next_required_step") not in (P7_R54_AHR_CR13_STEP_REF, P7_R54_AHR_CR12_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF):
        source_blockers.append(P7_R54_AHR_CR14_CR12_NEXT_STEP_NOT_CR13_BLOCKER_REF)
    if cr13.get("next_required_step") != P7_R54_AHR_CR14_STEP_REF:
        source_blockers.append(P7_R54_AHR_CR14_CR13_NEXT_STEP_NOT_CR14_BLOCKER_REF)
    issue_rows, row_blockers = _cr14_consistency_issue_rows_from_sources(
        rating_rows=cr11.get("rating_rows") or (),
        question_rows=cr13.get("question_need_observation_rows") or (),
        review_session_id=session_id,
    )
    source_blockers.extend(row_blockers)
    source_blockers = _dedupe_string_refs(source_blockers, limit=200, max_length=240)
    evaluated = not source_blockers
    guard_passed = evaluated and not issue_rows
    guard_failed = evaluated and bool(issue_rows)
    rows_for_output = issue_rows if guard_failed else []
    issue_type_counts = _count_values(rows_for_output, "consistency_issue_type_ref") if rows_for_output else {}
    p8_case_refs = sorted(
        {
            clean_identifier(row.get("case_ref_id"), default="", max_length=120)
            for row in (cr13.get("question_need_observation_rows") or [])
            if isinstance(row, Mapping) and row.get("p8_design_material_candidate") is True
        }
    )
    case_refs = sorted(
        {
            clean_identifier(row.get("case_ref_id"), default="", max_length=120)
            for row in (cr13.get("question_need_observation_rows") or [])
            if isinstance(row, Mapping)
        }
    ) if evaluated else []
    def _issue_case_refs(issue_type_ref: str) -> list[str]:
        return sorted({str(row.get("case_ref_id")) for row in rows_for_output if row.get("consistency_issue_type_ref") == issue_type_ref})
    below_refs = _issue_case_refs(P7_R54_AHR_CR14_ISSUE_RATING_BELOW_TARGET_P8_ESCAPE_REF)
    risk_refs = sorted(set(_issue_case_refs(P7_R54_AHR_CR14_ISSUE_CREEPY_OVERCLAIM_P8_ESCAPE_REF)) | set(_issue_case_refs(P7_R54_AHR_CR14_ISSUE_SELF_BLAME_P8_ESCAPE_REF)))
    repair_refs = _issue_case_refs(P7_R54_AHR_CR14_ISSUE_REPAIR_OR_BLOCKER_P8_ESCAPE_REF)
    heavy_refs = _issue_case_refs(P7_R54_AHR_CR14_ISSUE_HEAVY_OBSERVATION_P8_ESCAPE_REF)
    insufficient_refs = _issue_case_refs(P7_R54_AHR_CR14_ISSUE_INSUFFICIENT_MATERIAL_P8_ESCAPE_REF)
    status_ref = (
        P7_R54_AHR_CR14_GUARD_PASSED_STATUS_REF
        if guard_passed
        else P7_R54_AHR_CR14_GUARD_FAILED_STATUS_REF if guard_failed else P7_R54_AHR_CR14_GUARD_BLOCKED_STATUS_REF
    )
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CR14_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CR_STEP,
        "scope": P7_R54_AHR_CR_SCOPE,
        "policy_kind": P7_R54_AHR_CR_POLICY_KIND,
        "policy_section": P7_R54_AHR_CR14_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CR14_STEP_REF,
        "current_phase": P7_R54_AHR_CR_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cr14_rating_question_consistency_guard_20260628",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cr11_schema_version": cr11.get("schema_version"),
        "cr11_material_ref": cr11.get("material_id"),
        "cr11_next_required_step": cr11.get("next_required_step"),
        "cr11_rating_row_normalization_status_ref": cr11.get("rating_row_normalization_status_ref"),
        "cr11_rating_row_count": cr11.get("rating_row_count"),
        "cr11_actual_rating_rows_materialized_here": cr11.get("actual_rating_rows_materialized_here"),
        "cr12_schema_version": cr12.get("schema_version"),
        "cr12_material_ref": cr12.get("material_id"),
        "cr12_next_required_step": cr12.get("next_required_step"),
        "cr12_readfeel_execution_blocker_normalization_status_ref": cr12.get("readfeel_execution_blocker_normalization_status_ref"),
        "cr12_blocker_row_count": cr12.get("blocker_row_count"),
        "cr13_schema_version": cr13.get("schema_version"),
        "cr13_material_ref": cr13.get("material_id"),
        "cr13_next_required_step": cr13.get("next_required_step"),
        "cr13_question_need_observation_normalization_status_ref": cr13.get("question_need_observation_normalization_status_ref"),
        "cr13_question_need_observation_row_count": cr13.get("question_need_observation_row_count"),
        "cr13_actual_question_need_observation_rows_materialized_here": cr13.get(
            "actual_question_need_observation_rows_materialized_here"
        ),
        **_current_received_basis_fields(actual_basis=True),
        **_historical_basis_fields(),
        "rating_question_consistency_guard_status_ref": status_ref,
        "rating_question_consistency_guard_allowed_status_refs": list(P7_R54_AHR_CR14_ALLOWED_GUARD_STATUS_REFS),
        "rating_question_consistency_guard_evaluated": evaluated,
        "rating_question_consistency_guard_passed": guard_passed,
        "rating_question_consistency_guard_reason_refs": (
            [P7_R54_AHR_CR14_READY_REASON_REF]
            if guard_passed
            else [P7_R54_AHR_CR14_FAILED_REASON_REF] if guard_failed else []
        ),
        "rating_question_consistency_guard_step_blocker_refs": source_blockers,
        "rating_question_consistency_guard_step_blocker_ref_count": len(source_blockers),
        "required_case_count": P7_R54_AHR_CR_REQUIRED_CASE_COUNT,
        "source_rating_row_count": cr11.get("rating_row_count") if evaluated else 0,
        "source_question_need_observation_row_count": cr13.get("question_need_observation_row_count") if evaluated else 0,
        "source_blocker_row_count": cr12.get("blocker_row_count") if evaluated else 0,
        "case_ref_ids": case_refs,
        "case_ref_id_count": len(case_refs),
        "case_ref_ids_unique": len(case_refs) == len(set(case_refs)) == P7_R54_AHR_CR_REQUIRED_CASE_COUNT,
        "consistency_issue_rows": rows_for_output,
        "consistency_issue_row_count": len(rows_for_output),
        "consistency_issue_row_refs": [str(row.get("consistency_issue_row_ref")) for row in rows_for_output],
        "consistency_issue_row_ref_count": len(rows_for_output),
        "consistency_issue_type_refs": list(P7_R54_AHR_CR14_CONSISTENCY_ISSUE_TYPE_REFS),
        "consistency_issue_type_counts": issue_type_counts,
        "p8_material_candidate_case_refs": p8_case_refs if evaluated else [],
        "p8_material_candidate_case_count": len(p8_case_refs) if evaluated else 0,
        "rating_below_target_p8_escape_case_refs": below_refs,
        "rating_below_target_p8_escape_case_count": len(below_refs),
        "risk_axis_p8_escape_case_refs": risk_refs,
        "risk_axis_p8_escape_case_count": len(risk_refs),
        "repair_or_blocker_p8_escape_case_refs": repair_refs,
        "repair_or_blocker_p8_escape_case_count": len(repair_refs),
        "heavy_observation_p8_escape_case_refs": heavy_refs,
        "heavy_observation_p8_escape_case_count": len(heavy_refs),
        "insufficient_material_p8_escape_case_refs": insufficient_refs,
        "insufficient_material_p8_escape_case_count": len(insufficient_refs),
        "rows_bodyfree_only": evaluated and all(row.get("body_free") is True for row in rows_for_output),
        "rows_have_no_question_text": evaluated,
        "rating_question_consistency_guarded_here": evaluated,
        "rating_below_target_cannot_escape_to_p8_material": guard_passed,
        "creepy_or_overclaim_risk_cannot_escape_to_question_candidate": guard_passed,
        "self_blame_risk_cannot_escape_to_question_candidate": guard_passed,
        "immediate_observation_heavy_cannot_escape_to_p8_material": guard_passed,
        "insufficient_material_cannot_escape_to_p8_material": guard_passed,
        "repair_or_blocker_rows_cannot_escape_to_p8_material": guard_passed,
        "actual_rating_rows_materialized_here": evaluated,
        "actual_question_need_observation_rows_materialized_here": evaluated,
        "actual_human_review_executed_by_person": cr13.get("actual_human_review_executed_by_person") is True and evaluated,
        "actual_human_review_run_here": False,
        "actual_review_evidence_complete": False,
        "actual_disposal_receipt_materialized_here": False,
        "disposal_verified": False,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "p8_question_implementation_spec_finalized_here": False,
        "p8_start_allowed": False,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR_CR14_IMPLEMENTED_STEPS if evaluated else P7_R54_AHR_CR13_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(
            P7_R54_AHR_CR14_NOT_YET_IMPLEMENTED_STEPS if evaluated else P7_R54_AHR_CR13_NOT_YET_IMPLEMENTED_STEPS
        ),
        "next_required_step": P7_R54_AHR_CR15_STEP_REF if guard_passed else P7_R54_AHR_CR14_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    material["actual_rating_rows_materialized_here"] = evaluated
    material["actual_question_need_observation_rows_materialized_here"] = evaluated
    material["actual_human_review_executed_by_person"] = cr13.get("actual_human_review_executed_by_person") is True and evaluated
    material["actual_human_review_run_here"] = False
    material["actual_review_evidence_complete"] = False
    material["actual_disposal_receipt_materialized_here"] = False
    material["disposal_verified"] = False
    material["p5_human_blind_qa_confirmed_final"] = False
    material["p5_confirmed_final"] = False
    material["p5_final_allowed"] = False
    material["p6_limited_human_readfeel_start_allowed"] = False
    material["p6_start_allowed"] = False
    material["p8_start_allowed"] = False
    material["r52_reintake_execution_requested_here"] = False
    material["actual_r52_reintake_execution_confirmed"] = False
    material["p7_complete"] = False
    material["release_allowed"] = False
    return material


def assert_p7_r54_ahr_cr14_rating_question_consistency_guard_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CR14_RATING_QUESTION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CR14 rating-question consistency guard",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CR14_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CR14_STEP_REF,
        operation_step_ref=P7_R54_AHR_CR14_STEP_REF,
        source="P7-R54-AHR-CR14 rating-question consistency guard",
        allowed_true_false_flag_refs=P7_R54_AHR_CR14_ALLOWED_TRUE_OPERATION_FLAG_REFS,
    )
    _assert_current_received_basis_fields(data, actual_basis=True, source="P7-R54-AHR-CR14 guard")
    _assert_historical_basis_fields(data, source="P7-R54-AHR-CR14 guard")
    if data.get("cr11_schema_version") != P7_R54_AHR_CR11_RATING_ROW_NORMALIZATION_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CR14 CR11 schema version changed")
    if data.get("cr12_schema_version") != P7_R54_AHR_CR12_READFEEL_EXECUTION_BLOCKER_NORMALIZATION_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CR14 CR12 schema version changed")
    if data.get("cr13_schema_version") != P7_R54_AHR_CR13_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CR14 CR13 schema version changed")
    if tuple(data.get("rating_question_consistency_guard_allowed_status_refs") or ()) != P7_R54_AHR_CR14_ALLOWED_GUARD_STATUS_REFS:
        raise ValueError("P7-R54-AHR-CR14 allowed guard statuses changed")
    status_ref = data.get("rating_question_consistency_guard_status_ref")
    evaluated = status_ref in (P7_R54_AHR_CR14_GUARD_PASSED_STATUS_REF, P7_R54_AHR_CR14_GUARD_FAILED_STATUS_REF)
    guard_passed = status_ref == P7_R54_AHR_CR14_GUARD_PASSED_STATUS_REF
    guard_failed = status_ref == P7_R54_AHR_CR14_GUARD_FAILED_STATUS_REF
    if data.get("rating_question_consistency_guard_evaluated") is not evaluated:
        raise ValueError("P7-R54-AHR-CR14 evaluated flag changed")
    if data.get("rating_question_consistency_guard_passed") is not guard_passed:
        raise ValueError("P7-R54-AHR-CR14 passed flag changed")
    blockers = list(data.get("rating_question_consistency_guard_step_blocker_refs") or [])
    if data.get("rating_question_consistency_guard_step_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-CR14 blocker count changed")
    issue_rows = list(data.get("consistency_issue_rows") or [])
    if data.get("consistency_issue_row_count") != len(issue_rows):
        raise ValueError("P7-R54-AHR-CR14 issue row count changed")
    if data.get("consistency_issue_row_ref_count") != len(data.get("consistency_issue_row_refs") or []):
        raise ValueError("P7-R54-AHR-CR14 issue row ref count changed")
    if tuple(data.get("consistency_issue_type_refs") or ()) != P7_R54_AHR_CR14_CONSISTENCY_ISSUE_TYPE_REFS:
        raise ValueError("P7-R54-AHR-CR14 issue type refs changed")
    _assert_true_fields(
        data,
        keys=("r52_reintake_claim_blocked_here", "p6_p8_release_promotion_blocked_here", "p5_finalization_blocked_here"),
        source="P7-R54-AHR-CR14 guard",
    )
    _assert_false_fields(
        data,
        keys=(
            "actual_human_review_run_here",
            "actual_review_evidence_complete",
            "actual_disposal_receipt_materialized_here",
            "disposal_verified",
            "question_text_materialized_here",
            "draft_question_text_materialized_here",
            "p8_question_implementation_spec_finalized_here",
            "p8_start_allowed",
            "p5_human_blind_qa_confirmed_final",
            "p5_confirmed_final",
            "p5_final_allowed",
            "p6_limited_human_readfeel_start_allowed",
            "p6_start_allowed",
            "r52_reintake_execution_requested_here",
            "actual_r52_reintake_execution_confirmed",
            "p7_complete",
            "release_allowed",
        ),
        source="P7-R54-AHR-CR14 guard",
    )
    if evaluated:
        if blockers:
            raise ValueError("P7-R54-AHR-CR14 evaluated guard cannot carry source blockers")
        if data.get("source_rating_row_count") != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-CR14 source rating row count changed")
        if data.get("source_question_need_observation_row_count") != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-CR14 source question row count changed")
        if data.get("case_ref_id_count") != P7_R54_AHR_CR_REQUIRED_CASE_COUNT or data.get("case_ref_ids_unique") is not True:
            raise ValueError("P7-R54-AHR-CR14 case refs changed")
        if data.get("actual_rating_rows_materialized_here") is not True:
            raise ValueError("P7-R54-AHR-CR14 evaluated guard must carry rating rows materialized")
        if data.get("actual_question_need_observation_rows_materialized_here") is not True:
            raise ValueError("P7-R54-AHR-CR14 evaluated guard must carry question rows materialized")
        if data.get("actual_human_review_executed_by_person") is not True:
            raise ValueError("P7-R54-AHR-CR14 evaluated guard must carry person execution evidence")
        if data.get("rows_have_no_question_text") is not True or data.get("rating_question_consistency_guarded_here") is not True:
            raise ValueError("P7-R54-AHR-CR14 evaluated guard flags changed")
        for row in issue_rows:
            if not isinstance(row, Mapping):
                raise ValueError("P7-R54-AHR-CR14 issue row must be mapping")
            _assert_required_fields(
                row,
                required=P7_R54_AHR_CR14_CONSISTENCY_ISSUE_ROW_REQUIRED_FIELD_REFS,
                source="P7-R54-AHR-CR14 issue row",
            )
            if row.get("schema_version") != P7_R54_AHR_CR14_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION:
                raise ValueError("P7-R54-AHR-CR14 issue row schema changed")
            if row.get("consistency_issue_type_ref") not in P7_R54_AHR_CR14_CONSISTENCY_ISSUE_TYPE_REFS:
                raise ValueError("P7-R54-AHR-CR14 issue type changed")
            if row.get("rating_question_consistency_guard_blocks_evidence_complete") is not True:
                raise ValueError("P7-R54-AHR-CR14 issue must block evidence complete")
            if row.get("p8_material_candidate_blocked") is not True or row.get("body_free") is not True:
                raise ValueError("P7-R54-AHR-CR14 issue row must remain body-free and block P8 material")
            for flag_ref in P7_R54_AHR_CR14_CONSISTENCY_ISSUE_ROW_BODYFREE_FALSE_FLAG_REFS:
                if row.get(flag_ref) is not False:
                    raise ValueError(f"P7-R54-AHR-CR14 issue row must keep {flag_ref}=False")
        if guard_passed:
            if issue_rows:
                raise ValueError("P7-R54-AHR-CR14 passed guard cannot carry issue rows")
            if data.get("rating_question_consistency_guard_reason_refs") != [P7_R54_AHR_CR14_READY_REASON_REF]:
                raise ValueError("P7-R54-AHR-CR14 passed reason changed")
            _assert_true_fields(
                data,
                keys=(
                    "rating_below_target_cannot_escape_to_p8_material",
                    "creepy_or_overclaim_risk_cannot_escape_to_question_candidate",
                    "self_blame_risk_cannot_escape_to_question_candidate",
                    "immediate_observation_heavy_cannot_escape_to_p8_material",
                    "insufficient_material_cannot_escape_to_p8_material",
                    "repair_or_blocker_rows_cannot_escape_to_p8_material",
                ),
                source="P7-R54-AHR-CR14 passed guard",
            )
            if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CR14_IMPLEMENTED_STEPS:
                raise ValueError("P7-R54-AHR-CR14 implemented steps changed")
            if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CR14_NOT_YET_IMPLEMENTED_STEPS:
                raise ValueError("P7-R54-AHR-CR14 not-yet steps changed")
            if data.get("next_required_step") != P7_R54_AHR_CR15_STEP_REF:
                raise ValueError("P7-R54-AHR-CR14 passed next step changed")
        elif guard_failed:
            if not issue_rows:
                raise ValueError("P7-R54-AHR-CR14 failed guard must carry issue rows")
            if data.get("rating_question_consistency_guard_reason_refs") != [P7_R54_AHR_CR14_FAILED_REASON_REF]:
                raise ValueError("P7-R54-AHR-CR14 failed reason changed")
            if data.get("next_required_step") != P7_R54_AHR_CR14_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
                raise ValueError("P7-R54-AHR-CR14 failed next step changed")
    else:
        if status_ref != P7_R54_AHR_CR14_GUARD_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-CR14 blocked status changed")
        if not blockers:
            raise ValueError("P7-R54-AHR-CR14 blocked guard must carry source blockers")
        if issue_rows:
            raise ValueError("P7-R54-AHR-CR14 blocked guard must not carry issue rows")
        if data.get("rating_question_consistency_guard_reason_refs") != []:
            raise ValueError("P7-R54-AHR-CR14 blocked guard cannot carry ready/failed reasons")
        if data.get("next_required_step") != P7_R54_AHR_CR14_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CR14 blocked next step changed")
    return True


def build_p7_r54_ahr_cr15_bodyfree_disposal_receipt_input(
    *,
    disposal_receipt_ref: Any = None,
    disposal_status_ref: str = "BODY_PURGED",
    packet_materialized_for_review: bool = True,
    body_removed: bool = True,
    content_hash_of_body_stored: bool = False,
    body_hash_stored: bool = False,
    local_absolute_path_included: bool = False,
    reviewer_notes_body_stored: bool = False,
    pause_abort_status_ref: Any = None,
    retention_policy_ref: Any = None,
    expiration_policy_ref: Any = None,
) -> dict[str, Any]:
    """Build a body-free CR15 disposal receipt input fixture."""

    return {
        "disposal_receipt_ref": clean_identifier(
            disposal_receipt_ref, default=P7_R54_AHR_CR15_DEFAULT_DISPOSAL_RECEIPT_REF, max_length=160
        ),
        "disposal_status_ref": clean_identifier(disposal_status_ref, default="", max_length=160),
        "packet_materialized_for_review": bool(packet_materialized_for_review),
        "body_removed": bool(body_removed),
        "content_hash_of_body_stored": bool(content_hash_of_body_stored),
        "body_hash_stored": bool(body_hash_stored),
        "local_absolute_path_included": bool(local_absolute_path_included),
        "reviewer_notes_body_stored": bool(reviewer_notes_body_stored),
        "pause_abort_status_ref": clean_identifier(
            pause_abort_status_ref, default=P7_R54_AHR_CR15_DEFAULT_PAUSE_ABORT_STATUS_REF, max_length=160
        ),
        "retention_policy_ref": clean_identifier(
            retention_policy_ref, default=P7_R54_AHR_CR15_DEFAULT_RETENTION_POLICY_REF, max_length=160
        ),
        "expiration_policy_ref": clean_identifier(
            expiration_policy_ref, default=P7_R54_AHR_CR15_DEFAULT_EXPIRATION_POLICY_REF, max_length=160
        ),
        "body_free": True,
    }


def _cr15_receipt_input_fields(disposal_receipt_input: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(disposal_receipt_input, Mapping):
        return {
            "disposal_receipt_input_provided": False,
            "disposal_receipt_ref": "",
            "disposal_receipt_ref_present": False,
            "disposal_status_ref": "",
            "disposal_status_allowed_refs": list(P7_R54_AHR_CR15_DISPOSAL_STATUS_REFS),
            "disposal_status_ref_allowed": False,
            "packet_materialized_for_review": False,
            "body_removed": False,
            "body_removed_required": False,
            "body_removed_requirement_satisfied": False,
            "content_hash_of_body_stored": False,
            "body_hash_stored": False,
            "local_absolute_path_included": False,
            "reviewer_notes_body_stored": False,
            "pause_abort_status_ref": "",
            "retention_policy_ref": "",
            "expiration_policy_ref": "",
            "receipt_bodyfree_only": False,
            "receipt_has_no_body_path_hash": False,
        }
    receipt_ref = clean_identifier(disposal_receipt_input.get("disposal_receipt_ref"), default="", max_length=160)
    status_ref = clean_identifier(disposal_receipt_input.get("disposal_status_ref"), default="", max_length=160)
    packet_materialized = disposal_receipt_input.get("packet_materialized_for_review") is True
    body_removed = disposal_receipt_input.get("body_removed") is True
    body_removed_required = packet_materialized
    body_removed_ok = body_removed if body_removed_required else True
    content_hash_stored = disposal_receipt_input.get("content_hash_of_body_stored") is True
    body_hash_stored = disposal_receipt_input.get("body_hash_stored") is True
    local_path_included = disposal_receipt_input.get("local_absolute_path_included") is True
    reviewer_notes_body_stored = disposal_receipt_input.get("reviewer_notes_body_stored") is True
    bodyfree_only = disposal_receipt_input.get("body_free") is True and not _contains_forbidden_body_or_question_key(disposal_receipt_input)
    no_body_path_hash = not (content_hash_stored or body_hash_stored or local_path_included or reviewer_notes_body_stored)
    return {
        "disposal_receipt_input_provided": True,
        "disposal_receipt_ref": receipt_ref,
        "disposal_receipt_ref_present": bool(receipt_ref),
        "disposal_status_ref": status_ref,
        "disposal_status_allowed_refs": list(P7_R54_AHR_CR15_DISPOSAL_STATUS_REFS),
        "disposal_status_ref_allowed": status_ref in P7_R54_AHR_CR15_DISPOSAL_STATUS_REFS,
        "packet_materialized_for_review": packet_materialized,
        "body_removed": body_removed,
        "body_removed_required": body_removed_required,
        "body_removed_requirement_satisfied": body_removed_ok,
        "content_hash_of_body_stored": content_hash_stored,
        "body_hash_stored": body_hash_stored,
        "local_absolute_path_included": local_path_included,
        "reviewer_notes_body_stored": reviewer_notes_body_stored,
        "pause_abort_status_ref": clean_identifier(
            disposal_receipt_input.get("pause_abort_status_ref"), default="", max_length=160
        ),
        "retention_policy_ref": clean_identifier(disposal_receipt_input.get("retention_policy_ref"), default="", max_length=160),
        "expiration_policy_ref": clean_identifier(disposal_receipt_input.get("expiration_policy_ref"), default="", max_length=160),
        "receipt_bodyfree_only": bodyfree_only,
        "receipt_has_no_body_path_hash": no_body_path_hash,
    }


def build_p7_r54_ahr_cr15_pause_abort_expiration_disposal_receipt(
    *,
    rating_question_consistency_guard: Mapping[str, Any] | None = None,
    disposal_receipt_input: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build CR15 body-free pause/abort/expiration/disposal receipt material."""

    cr14 = dict(rating_question_consistency_guard or build_p7_r54_ahr_cr14_rating_question_consistency_guard())
    assert_p7_r54_ahr_cr14_rating_question_consistency_guard_contract(cr14)
    session_id = _safe_review_session_id(review_session_id)
    receipt_fields = _cr15_receipt_input_fields(disposal_receipt_input)
    blockers: list[str] = []
    cr14_passed = cr14.get("rating_question_consistency_guard_passed") is True
    if not cr14_passed:
        blockers.append(P7_R54_AHR_CR15_CR14_NOT_READY_BLOCKER_REF)
    if cr14.get("next_required_step") != P7_R54_AHR_CR15_STEP_REF:
        blockers.append(P7_R54_AHR_CR15_CR14_NEXT_STEP_NOT_CR15_BLOCKER_REF)
    if not receipt_fields["disposal_receipt_input_provided"] or not receipt_fields["disposal_receipt_ref_present"]:
        blockers.append(P7_R54_AHR_CR15_DISPOSAL_RECEIPT_MISSING_BLOCKER_REF)
    if not receipt_fields["disposal_status_ref_allowed"]:
        blockers.append(P7_R54_AHR_CR15_DISPOSAL_STATUS_NOT_ALLOWED_BLOCKER_REF)
    if receipt_fields["disposal_status_ref"] == "DISPOSAL_FAILED":
        blockers.append(P7_R54_AHR_CR15_DISPOSAL_FAILED_BLOCKER_REF)
    if not receipt_fields["body_removed_requirement_satisfied"]:
        blockers.append(P7_R54_AHR_CR15_BODY_REMOVED_REQUIRED_BLOCKER_REF)
    if receipt_fields["content_hash_of_body_stored"] or receipt_fields["body_hash_stored"]:
        blockers.append(P7_R54_AHR_CR15_BODY_HASH_STORED_BLOCKER_REF)
    if receipt_fields["local_absolute_path_included"]:
        blockers.append(P7_R54_AHR_CR15_LOCAL_PATH_INCLUDED_BLOCKER_REF)
    if receipt_fields["reviewer_notes_body_stored"]:
        blockers.append(P7_R54_AHR_CR15_REVIEWER_NOTES_BODY_STORED_BLOCKER_REF)
    if not receipt_fields["receipt_bodyfree_only"] or not receipt_fields["receipt_has_no_body_path_hash"]:
        blockers.append(P7_R54_AHR_CR15_RECEIPT_FORBIDDEN_KEY_BLOCKER_REF)
    blockers = _dedupe_string_refs(blockers, limit=200, max_length=240)
    ready = not blockers
    sanitized_receipt_fields = dict(receipt_fields)
    # Keep the exported CR15 material body-free even when the supplied receipt
    # is blocked for a local path/hash/reviewer-note violation. The blocker refs
    # preserve the reason; the artifact itself must not carry those true flags.
    sanitized_receipt_fields["content_hash_of_body_stored"] = False
    sanitized_receipt_fields["body_hash_stored"] = False
    sanitized_receipt_fields["local_absolute_path_included"] = False
    sanitized_receipt_fields["reviewer_notes_body_stored"] = False
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CR15_DISPOSAL_RECEIPT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CR_STEP,
        "scope": P7_R54_AHR_CR_SCOPE,
        "policy_kind": P7_R54_AHR_CR_POLICY_KIND,
        "policy_section": P7_R54_AHR_CR15_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CR15_STEP_REF,
        "current_phase": P7_R54_AHR_CR_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cr15_pause_abort_expiration_disposal_receipt_20260628",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cr14_schema_version": cr14.get("schema_version"),
        "cr14_material_ref": cr14.get("material_id"),
        "cr14_next_required_step": cr14.get("next_required_step"),
        "cr14_rating_question_consistency_guard_status_ref": cr14.get("rating_question_consistency_guard_status_ref"),
        "cr14_rating_question_consistency_guard_passed": cr14.get("rating_question_consistency_guard_passed"),
        "cr14_consistency_issue_row_count": cr14.get("consistency_issue_row_count"),
        "cr14_actual_rating_rows_materialized_here": cr14.get("actual_rating_rows_materialized_here"),
        "cr14_actual_question_need_observation_rows_materialized_here": cr14.get(
            "actual_question_need_observation_rows_materialized_here"
        ),
        **_current_received_basis_fields(actual_basis=True),
        **_historical_basis_fields(),
        "pause_abort_expiration_disposal_receipt_status_ref": (
            P7_R54_AHR_CR15_DISPOSAL_VERIFIED_STATUS_REF if ready else P7_R54_AHR_CR15_DISPOSAL_BLOCKED_STATUS_REF
        ),
        "pause_abort_expiration_disposal_receipt_allowed_status_refs": list(P7_R54_AHR_CR15_ALLOWED_STATUS_REFS),
        "pause_abort_expiration_disposal_receipt_ready": ready,
        "pause_abort_expiration_disposal_receipt_reason_refs": [P7_R54_AHR_CR15_READY_REASON_REF] if ready else [],
        "pause_abort_expiration_disposal_receipt_step_blocker_refs": blockers,
        "pause_abort_expiration_disposal_receipt_step_blocker_ref_count": len(blockers),
        **sanitized_receipt_fields,
        "local_only_packet_lifecycle_closed_here": ready,
        "actual_rating_rows_materialized_here": cr14.get("actual_rating_rows_materialized_here") is True and ready,
        "actual_question_need_observation_rows_materialized_here": cr14.get(
            "actual_question_need_observation_rows_materialized_here"
        ) is True and ready,
        "actual_human_review_executed_by_person": cr14.get("actual_human_review_executed_by_person") is True and ready,
        "actual_disposal_receipt_materialized_here": ready,
        "disposal_verified": ready,
        "actual_human_review_run_here": False,
        "actual_review_evidence_complete": False,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "p8_question_implementation_spec_finalized_here": False,
        "p8_start_allowed": False,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR_CR15_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CR14_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(
            P7_R54_AHR_CR15_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CR14_NOT_YET_IMPLEMENTED_STEPS
        ),
        "next_required_step": P7_R54_AHR_CR16_STEP_REF if ready else P7_R54_AHR_CR15_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    material["actual_rating_rows_materialized_here"] = cr14.get("actual_rating_rows_materialized_here") is True and ready
    material["actual_question_need_observation_rows_materialized_here"] = cr14.get(
        "actual_question_need_observation_rows_materialized_here"
    ) is True and ready
    material["actual_human_review_executed_by_person"] = cr14.get("actual_human_review_executed_by_person") is True and ready
    material["actual_disposal_receipt_materialized_here"] = ready
    material["disposal_verified"] = ready
    material["actual_human_review_run_here"] = False
    material["actual_review_evidence_complete"] = False
    material["p5_human_blind_qa_confirmed_final"] = False
    material["p5_confirmed_final"] = False
    material["p5_final_allowed"] = False
    material["p6_limited_human_readfeel_start_allowed"] = False
    material["p6_start_allowed"] = False
    material["p8_start_allowed"] = False
    material["r52_reintake_execution_requested_here"] = False
    material["actual_r52_reintake_execution_confirmed"] = False
    material["p7_complete"] = False
    material["release_allowed"] = False
    return material


def assert_p7_r54_ahr_cr15_pause_abort_expiration_disposal_receipt_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CR15_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CR15 disposal receipt",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CR15_DISPOSAL_RECEIPT_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CR15_STEP_REF,
        operation_step_ref=P7_R54_AHR_CR15_STEP_REF,
        source="P7-R54-AHR-CR15 disposal receipt",
        allowed_true_false_flag_refs=P7_R54_AHR_CR15_ALLOWED_TRUE_OPERATION_FLAG_REFS,
    )
    _assert_current_received_basis_fields(data, actual_basis=True, source="P7-R54-AHR-CR15 disposal receipt")
    _assert_historical_basis_fields(data, source="P7-R54-AHR-CR15 disposal receipt")
    if data.get("cr14_schema_version") != P7_R54_AHR_CR14_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CR15 CR14 schema changed")
    if tuple(data.get("pause_abort_expiration_disposal_receipt_allowed_status_refs") or ()) != P7_R54_AHR_CR15_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-CR15 allowed status refs changed")
    status_ref = data.get("pause_abort_expiration_disposal_receipt_status_ref")
    ready = status_ref == P7_R54_AHR_CR15_DISPOSAL_VERIFIED_STATUS_REF
    if data.get("pause_abort_expiration_disposal_receipt_ready") is not ready:
        raise ValueError("P7-R54-AHR-CR15 ready flag changed")
    blockers = list(data.get("pause_abort_expiration_disposal_receipt_step_blocker_refs") or [])
    if data.get("pause_abort_expiration_disposal_receipt_step_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-CR15 blocker count changed")
    if tuple(data.get("disposal_status_allowed_refs") or ()) != P7_R54_AHR_CR15_DISPOSAL_STATUS_REFS:
        raise ValueError("P7-R54-AHR-CR15 disposal status allowed refs changed")
    _assert_true_fields(
        data,
        keys=("r52_reintake_claim_blocked_here", "p6_p8_release_promotion_blocked_here", "p5_finalization_blocked_here"),
        source="P7-R54-AHR-CR15 disposal receipt",
    )
    _assert_false_fields(
        data,
        keys=(
            "actual_human_review_run_here",
            "actual_review_evidence_complete",
            "question_text_materialized_here",
            "draft_question_text_materialized_here",
            "p8_question_implementation_spec_finalized_here",
            "p8_start_allowed",
            "p5_human_blind_qa_confirmed_final",
            "p5_confirmed_final",
            "p5_final_allowed",
            "p6_limited_human_readfeel_start_allowed",
            "p6_start_allowed",
            "r52_reintake_execution_requested_here",
            "actual_r52_reintake_execution_confirmed",
            "p7_complete",
            "release_allowed",
        ),
        source="P7-R54-AHR-CR15 disposal receipt",
    )
    if ready:
        if data.get("content_hash_of_body_stored") is not False or data.get("body_hash_stored") is not False:
            raise ValueError("P7-R54-AHR-CR15 verified receipt must not store body hashes")
        if data.get("local_absolute_path_included") is not False or data.get("reviewer_notes_body_stored") is not False:
            raise ValueError("P7-R54-AHR-CR15 verified receipt must not store local paths or reviewer note bodies")
        if blockers:
            raise ValueError("P7-R54-AHR-CR15 verified receipt cannot carry blockers")
        if data.get("pause_abort_expiration_disposal_receipt_reason_refs") != [P7_R54_AHR_CR15_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-CR15 ready reason changed")
        _assert_true_fields(
            data,
            keys=(
                "cr14_rating_question_consistency_guard_passed",
                "disposal_receipt_input_provided",
                "disposal_receipt_ref_present",
                "disposal_status_ref_allowed",
                "body_removed_requirement_satisfied",
                "receipt_bodyfree_only",
                "receipt_has_no_body_path_hash",
                "local_only_packet_lifecycle_closed_here",
                "actual_rating_rows_materialized_here",
                "actual_question_need_observation_rows_materialized_here",
                "actual_human_review_executed_by_person",
                "actual_disposal_receipt_materialized_here",
                "disposal_verified",
            ),
            source="P7-R54-AHR-CR15 verified receipt",
        )
        if data.get("disposal_status_ref") not in ("BODY_PURGED", "LOCAL_ONLY_PACKET_NOT_MATERIALIZED"):
            raise ValueError("P7-R54-AHR-CR15 verified status changed")
        if data.get("packet_materialized_for_review") is True and data.get("body_removed") is not True:
            raise ValueError("P7-R54-AHR-CR15 materialized packet must have body_removed=True")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CR15_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CR15 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CR15_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CR15 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_CR16_STEP_REF:
            raise ValueError("P7-R54-AHR-CR15 ready next step changed")
    else:
        if status_ref != P7_R54_AHR_CR15_DISPOSAL_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-CR15 blocked status changed")
        if not blockers:
            raise ValueError("P7-R54-AHR-CR15 blocked receipt must carry blockers")
        if data.get("pause_abort_expiration_disposal_receipt_reason_refs") != []:
            raise ValueError("P7-R54-AHR-CR15 blocked receipt cannot carry ready reasons")
        if data.get("actual_disposal_receipt_materialized_here") is not False or data.get("disposal_verified") is not False:
            raise ValueError("P7-R54-AHR-CR15 blocked receipt must not verify disposal")
        if data.get("next_required_step") != P7_R54_AHR_CR15_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CR15 blocked next step changed")
    return True


# Alias names for CR14/CR15 design/documentation wording.
def build_p7_r54_ahr_current_received_actual_local_review_operation_rating_question_consistency_guard_bodyfree(
    *,
    rating_row_normalization: Mapping[str, Any] | None = None,
    readfeel_execution_blocker_normalization: Mapping[str, Any] | None = None,
    question_need_observation_normalization: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_cr14_rating_question_consistency_guard(
        rating_row_normalization=rating_row_normalization,
        readfeel_execution_blocker_normalization=readfeel_execution_blocker_normalization,
        question_need_observation_normalization=question_need_observation_normalization,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_current_received_actual_local_review_operation_rating_question_consistency_guard_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_cr14_rating_question_consistency_guard_contract(data)


def build_p7_r54_ahr_current_received_actual_local_review_operation_disposal_receipt_bodyfree(
    *,
    rating_question_consistency_guard: Mapping[str, Any] | None = None,
    disposal_receipt_input: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_cr15_pause_abort_expiration_disposal_receipt(
        rating_question_consistency_guard=rating_question_consistency_guard,
        disposal_receipt_input=disposal_receipt_input,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_current_received_actual_local_review_operation_disposal_receipt_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_cr15_pause_abort_expiration_disposal_receipt_contract(data)


# CR16/CR17 keep evidence completion and P5 decision separation body-free.
# They deliberately do not finalize P5, start P6/P8, execute R52, complete P7,
# or allow release.  A CR17 confirmed candidate is only a candidate for later
# handoff material, never the product final claim.
P7_R54_AHR_CR16_POST_REVIEW_SUMMARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_received_actual_local_review_operation."
    "cr16_post_review_summary_evidence_complete_predicate.bodyfree.v1"
)
P7_R54_AHR_CR17_P5_DECISION_CANDIDATE_REPAIR_SEPARATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_received_actual_local_review_operation."
    "cr17_p5_decision_candidate_repair_separation.bodyfree.v1"
)
P7_R54_AHR_CR_POST_REVIEW_SUMMARY_SCHEMA_VERSION: Final = P7_R54_AHR_CR16_POST_REVIEW_SUMMARY_SCHEMA_VERSION
P7_R54_AHR_CR_P5_DECISION_CANDIDATE_REPAIR_SEPARATION_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CR17_P5_DECISION_CANDIDATE_REPAIR_SEPARATION_SCHEMA_VERSION
)

P7_R54_AHR_CR16_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR15_IMPLEMENTED_STEPS,
    P7_R54_AHR_CR16_STEP_REF,
)
P7_R54_AHR_CR16_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CR_STEP_REFS[17:]
P7_R54_AHR_CR17_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR16_IMPLEMENTED_STEPS,
    P7_R54_AHR_CR17_STEP_REF,
)
P7_R54_AHR_CR17_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CR_STEP_REFS[18:]

P7_R54_AHR_CR16_EVIDENCE_COMPLETE_STATUS_REF: Final = (
    "CR16_ACTUAL_REVIEW_EVIDENCE_COMPLETE_BODYFREE_PREDICATE_PASSED"
)
P7_R54_AHR_CR16_EVIDENCE_INCOMPLETE_STATUS_REF: Final = (
    "CR16_ACTUAL_REVIEW_EVIDENCE_INCOMPLETE_BODYFREE_PREDICATE_BLOCKED"
)
P7_R54_AHR_CR16_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR16_EVIDENCE_COMPLETE_STATUS_REF,
    P7_R54_AHR_CR16_EVIDENCE_INCOMPLETE_STATUS_REF,
)
P7_R54_AHR_CR16_READY_REASON_REF: Final = (
    "CR16_CR09_TO_CR15_ALL_BODYFREE_EVIDENCE_PREDICATES_PASSED"
)
P7_R54_AHR_CR16_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "actual_review_evidence_completion_requirements_or_stop"
)
P7_R54_AHR_CR16_CR09_NOT_READY_BLOCKER_REF: Final = "cr09_actual_operation_receipt_not_ready"
P7_R54_AHR_CR16_CR10_NOT_READY_BLOCKER_REF: Final = "cr10_sanitized_selection_rows_not_ready"
P7_R54_AHR_CR16_CR11_NOT_READY_BLOCKER_REF: Final = "cr11_rating_rows_not_ready"
P7_R54_AHR_CR16_CR12_NOT_READY_BLOCKER_REF: Final = "cr12_blocker_normalization_not_ready"
P7_R54_AHR_CR16_CR13_NOT_READY_BLOCKER_REF: Final = "cr13_question_observation_rows_not_ready"
P7_R54_AHR_CR16_CR14_NOT_PASSED_BLOCKER_REF: Final = "cr14_rating_question_consistency_guard_not_passed"
P7_R54_AHR_CR16_CR15_NOT_READY_BLOCKER_REF: Final = "cr15_disposal_receipt_not_ready"
P7_R54_AHR_CR16_PERSON_EXECUTION_NOT_CONFIRMED_BLOCKER_REF: Final = "actual_human_review_person_execution_not_confirmed"
P7_R54_AHR_CR16_REVIEWED_CASE_COUNT_NOT_24_BLOCKER_REF: Final = "reviewed_case_count_not_24"
P7_R54_AHR_CR16_SANITIZED_ROW_COUNT_NOT_24_BLOCKER_REF: Final = "sanitized_review_result_row_count_not_24"
P7_R54_AHR_CR16_RATING_ROW_COUNT_NOT_24_BLOCKER_REF: Final = "rating_row_count_not_24"
P7_R54_AHR_CR16_QUESTION_ROW_COUNT_NOT_24_BLOCKER_REF: Final = "question_need_observation_row_count_not_24"
P7_R54_AHR_CR16_DISPOSAL_NOT_VERIFIED_BLOCKER_REF: Final = "disposal_verified_false"
P7_R54_AHR_CR16_CONSISTENCY_NOT_PASSED_BLOCKER_REF: Final = "consistency_guard_passed_false"
P7_R54_AHR_CR16_BODY_LEAK_VALIDATION_BLOCKER_REF: Final = "no_body_leak_validation_failed"
P7_R54_AHR_CR16_QUESTION_TEXT_VALIDATION_BLOCKER_REF: Final = "no_question_text_validation_failed"
P7_R54_AHR_CR16_NO_TOUCH_VALIDATION_BLOCKER_REF: Final = "no_touch_validation_failed"
P7_R54_AHR_CR16_SOURCE_FORBIDDEN_KEY_BLOCKER_REF: Final = "source_material_forbidden_body_question_path_hash_key"
P7_R54_AHR_CR16_ALLOWED_TRUE_OPERATION_FLAG_REFS: Final[tuple[str, ...]] = (
    "actual_human_review_executed_by_person",
    "actual_human_review_complete",
    "actual_review_evidence_complete",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
)

P7_R54_AHR_CR17_CONFIRMED_CANDIDATE_STATUS_REF: Final = (
    "CR17_P5_CONFIRMED_CANDIDATE_SEPARATED_BODYFREE_ONLY"
)
P7_R54_AHR_CR17_REPAIR_OR_BLOCKED_STATUS_REF: Final = (
    "CR17_P5_DECISION_REPAIR_OR_BLOCKER_SEPARATED_BODYFREE"
)
P7_R54_AHR_CR17_BLOCKED_STATUS_REF: Final = (
    "CR17_P5_DECISION_SEPARATION_BLOCKED_EVIDENCE_INCOMPLETE"
)
P7_R54_AHR_CR17_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR17_CONFIRMED_CANDIDATE_STATUS_REF,
    P7_R54_AHR_CR17_REPAIR_OR_BLOCKED_STATUS_REF,
    P7_R54_AHR_CR17_BLOCKED_STATUS_REF,
)
P7_R54_AHR_CR17_READY_REASON_REF: Final = (
    "CR17_EVIDENCE_COMPLETE_AND_NO_P5_P4_OPERATION_INCONCLUSIVE_REPAIR_REQUIRED"
)
P7_R54_AHR_CR17_REPAIR_REASON_REF: Final = (
    "CR17_EVIDENCE_COMPLETE_BUT_REPAIR_OR_BLOCKER_SEPARATED_BEFORE_R52"
)
P7_R54_AHR_CR17_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "cr16_evidence_complete_or_stop"
P7_R54_AHR_CR17_REPAIR_NEXT_REQUIRED_STEP_REF: Final = "p5_p4_operation_repair_or_stop_before_r52"
P7_R54_AHR_CR17_CR16_NOT_COMPLETE_BLOCKER_REF: Final = "cr16_actual_review_evidence_not_complete"
P7_R54_AHR_CR17_P5_CONFIRMED_CANDIDATE_REF: Final = "P5_CONFIRMED_CANDIDATE_BODYFREE_ONLY"
P7_R54_AHR_CR17_P5_REPAIR_REQUIRED_REF: Final = "P5_REPAIR_REQUIRED_BEFORE_R52_REINTAKE"
P7_R54_AHR_CR17_P4_CURRENT_ONLY_REPAIR_REQUIRED_REF: Final = (
    "P4_CURRENT_ONLY_REPAIR_REQUIRED_BEFORE_R52_REINTAKE"
)
P7_R54_AHR_CR17_OPERATION_BLOCKED_BODY_OR_QUESTION_REF: Final = (
    "R54_OPERATION_BLOCKED_BODY_LEAK_OR_QUESTION_TEXT"
)
P7_R54_AHR_CR17_OPERATION_BLOCKED_DISPOSAL_REF: Final = "R54_OPERATION_BLOCKED_DISPOSAL_NOT_VERIFIED"
P7_R54_AHR_CR17_OPERATION_INCONCLUSIVE_REF: Final = "R54_OPERATION_INCONCLUSIVE_INSUFFICIENT_MATERIAL"
P7_R54_AHR_CR17_DECISION_REF_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR17_P5_CONFIRMED_CANDIDATE_REF,
    P7_R54_AHR_CR17_P5_REPAIR_REQUIRED_REF,
    P7_R54_AHR_CR17_P4_CURRENT_ONLY_REPAIR_REQUIRED_REF,
    P7_R54_AHR_CR17_OPERATION_BLOCKED_BODY_OR_QUESTION_REF,
    P7_R54_AHR_CR17_OPERATION_BLOCKED_DISPOSAL_REF,
    P7_R54_AHR_CR17_OPERATION_INCONCLUSIVE_REF,
)
P7_R54_AHR_CR17_ALLOWED_TRUE_OPERATION_FLAG_REFS: Final[tuple[str, ...]] = P7_R54_AHR_CR16_ALLOWED_TRUE_OPERATION_FLAG_REFS

P7_R54_AHR_CR16_POST_REVIEW_SUMMARY_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR_BASE_REQUIRED_FIELD_REFS,
    "cr09_schema_version",
    "cr09_material_ref",
    "cr09_next_required_step",
    "cr09_operation_receipt_ready",
    "cr09_operation_receipt_status_ref",
    "cr09_actual_human_review_executed_by_person",
    "cr09_reviewed_case_count",
    "cr09_selection_row_count",
    "cr10_schema_version",
    "cr10_material_ref",
    "cr10_next_required_step",
    "cr10_sanitized_selection_only_result_rows_ready",
    "cr10_sanitized_review_result_row_count",
    "cr11_schema_version",
    "cr11_material_ref",
    "cr11_next_required_step",
    "cr11_rating_row_normalization_ready",
    "cr11_rating_row_count",
    "cr12_schema_version",
    "cr12_material_ref",
    "cr12_next_required_step",
    "cr12_readfeel_execution_blocker_normalization_ready",
    "cr12_p5_repair_required_case_count",
    "cr12_p4_current_only_repair_required_case_count",
    "cr12_operation_blocked_case_count",
    "cr12_inconclusive_insufficient_material_case_count",
    "cr13_schema_version",
    "cr13_material_ref",
    "cr13_next_required_step",
    "cr13_question_need_observation_normalization_ready",
    "cr13_question_need_observation_row_count",
    "cr13_p8_material_candidate_case_count",
    "cr14_schema_version",
    "cr14_material_ref",
    "cr14_next_required_step",
    "cr14_rating_question_consistency_guard_status_ref",
    "cr14_rating_question_consistency_guard_passed",
    "cr14_consistency_issue_row_count",
    "cr15_schema_version",
    "cr15_material_ref",
    "cr15_next_required_step",
    "cr15_pause_abort_expiration_disposal_receipt_ready",
    "cr15_disposal_verified",
    "cr15_actual_disposal_receipt_materialized_here",
    *P7_R54_AHR_CR_CURRENT_RECEIVED_BASIS_FIELD_REFS,
    *P7_R54_AHR_CR_HISTORICAL_BASIS_FIELD_REFS,
    "post_review_summary_status_ref",
    "post_review_summary_allowed_status_refs",
    "post_review_summary_ready",
    "post_review_summary_reason_refs",
    "post_review_summary_step_blocker_refs",
    "post_review_summary_step_blocker_ref_count",
    "actual_review_evidence_complete_predicate_evaluated",
    "actual_review_evidence_complete_requirements",
    "actual_review_evidence_complete_requirement_count",
    "actual_review_evidence_complete_passed_requirement_refs",
    "actual_review_evidence_complete_passed_requirement_count",
    "actual_review_evidence_complete_failed_requirement_refs",
    "actual_review_evidence_complete_failed_requirement_count",
    "reviewed_case_count",
    "sanitized_review_result_row_count",
    "rating_row_count",
    "question_need_observation_row_count",
    "disposal_receipt_verified_here",
    "consistency_guard_passed",
    "no_body_leak_validation_passed",
    "no_question_text_validation_passed",
    "no_touch_validation_passed",
    "source_materials_bodyfree_only",
    "source_materials_have_no_forbidden_keys",
    "post_review_summary_bodyfree_only",
    "post_review_summary_does_not_create_question_text",
    "post_review_summary_does_not_change_api_db_rn_runtime",
    "p5_decision_separation_allowed_next",
    "p5_confirmed_candidate",
    "p5_confirmed_candidate_only",
    "p5_confirmed_candidate_is_not_p5_final",
    "p5_repair_required_case_count",
    "p4_current_only_repair_required_case_count",
    "operation_blocked_case_count",
    "inconclusive_insufficient_material_case_count",
    "p8_material_candidate_case_count",
    "actual_human_review_complete",
    "actual_review_evidence_complete",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_human_review_operation_run",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "p8_question_implementation_spec_finalized_here",
    "p5_human_blind_qa_confirmed_final",
    "p5_confirmed_final",
    "p5_final_allowed",
    "p6_limited_human_readfeel_start_allowed",
    "p6_start_allowed",
    "p8_start_allowed",
    "r52_reintake_execution_requested_here",
    "actual_r52_reintake_execution_confirmed",
    "p7_complete",
    "release_allowed",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CR_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CR_FALSE_FLAG_REFS,
)
P7_R54_AHR_CR_POST_REVIEW_SUMMARY_REQUIRED_FIELD_REFS: Final = P7_R54_AHR_CR16_POST_REVIEW_SUMMARY_REQUIRED_FIELD_REFS

P7_R54_AHR_CR17_P5_DECISION_CANDIDATE_REPAIR_SEPARATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR_BASE_REQUIRED_FIELD_REFS,
    "cr16_schema_version",
    "cr16_material_ref",
    "cr16_next_required_step",
    "cr16_post_review_summary_ready",
    "cr16_actual_review_evidence_complete",
    "cr16_actual_human_review_complete",
    "cr16_p5_confirmed_candidate",
    "cr16_p5_repair_required_case_count",
    "cr16_p4_current_only_repair_required_case_count",
    "cr16_operation_blocked_case_count",
    "cr16_inconclusive_insufficient_material_case_count",
    "cr16_p8_material_candidate_case_count",
    *P7_R54_AHR_CR_CURRENT_RECEIVED_BASIS_FIELD_REFS,
    *P7_R54_AHR_CR_HISTORICAL_BASIS_FIELD_REFS,
    "p5_decision_candidate_separation_status_ref",
    "p5_decision_candidate_separation_allowed_status_refs",
    "p5_decision_candidate_separation_ready",
    "p5_decision_candidate_separation_reason_refs",
    "p5_decision_candidate_separation_step_blocker_refs",
    "p5_decision_candidate_separation_step_blocker_ref_count",
    "p5_decision_ref",
    "p5_decision_allowed_refs",
    "p5_confirmed_candidate",
    "p5_confirmed_candidate_only",
    "p5_confirmed_candidate_is_not_p5_final",
    "p5_decision_candidate_ready_for_r52_handoff",
    "p5_repair_required_before_r52",
    "p4_current_only_repair_required_before_r52",
    "operation_blocked_before_r52",
    "inconclusive_before_r52",
    "p5_repair_required_case_count",
    "p4_current_only_repair_required_case_count",
    "operation_blocked_case_count",
    "inconclusive_insufficient_material_case_count",
    "p8_material_candidate_case_count",
    "repair_or_blocker_case_count",
    "p5_repair_required_case_refs",
    "p4_current_only_repair_required_case_refs",
    "operation_blocked_case_refs",
    "inconclusive_insufficient_material_case_refs",
    "decision_boundary_refs",
    "decision_boundary_ref_count",
    "p5_finalization_remains_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "r52_actual_execution_blocked_here",
    "p8_material_candidate_only_is_not_p8_start_allowed",
    "p5_confirmed_candidate_not_promoted_to_final",
    "p5_repair_required_not_promoted_to_p8_material_candidate",
    "actual_human_review_complete",
    "actual_review_evidence_complete",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_human_review_operation_run",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "p8_question_implementation_spec_finalized_here",
    "p5_human_blind_qa_confirmed_final",
    "p5_confirmed_final",
    "p5_final_allowed",
    "p6_limited_human_readfeel_start_allowed",
    "p6_start_allowed",
    "p8_start_allowed",
    "r52_reintake_execution_requested_here",
    "actual_r52_reintake_execution_confirmed",
    "p7_complete",
    "release_allowed",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CR_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CR_FALSE_FLAG_REFS,
)
P7_R54_AHR_CR_P5_DECISION_CANDIDATE_REPAIR_SEPARATION_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CR17_P5_DECISION_CANDIDATE_REPAIR_SEPARATION_REQUIRED_FIELD_REFS
)


def _cr16_all_source_materials(
    *materials: Mapping[str, Any] | None,
) -> tuple[Mapping[str, Any], ...]:
    return tuple(material for material in materials if isinstance(material, Mapping))


def _cr16_all_false_for_refs(materials: Sequence[Mapping[str, Any]], refs: tuple[str, ...]) -> bool:
    return all(material.get(ref) is False for material in materials for ref in refs)


def _cr16_no_touch_passed(materials: Sequence[Mapping[str, Any]]) -> bool:
    return _cr16_all_false_for_refs(materials, P7_R54_AHR_CR_NO_TOUCH_FALSE_FLAG_REFS)


def _cr16_no_body_leak_passed(materials: Sequence[Mapping[str, Any]]) -> bool:
    return _cr16_all_false_for_refs(materials, P7_R54_AHR_CR_BODY_FREE_FALSE_FLAG_REFS)


def _cr16_no_question_text_passed(materials: Sequence[Mapping[str, Any]]) -> bool:
    question_false_refs = (
        "question_text_materialized_here",
        "draft_question_text_materialized_here",
        "question_text_included",
        "draft_question_text_included",
        "raw_question_answer_included",
    )
    return _cr16_all_false_for_refs(materials, question_false_refs)


def _cr16_sources_have_no_forbidden_keys(materials: Sequence[Mapping[str, Any]]) -> bool:
    return not any(_contains_forbidden_body_or_question_key(material) for material in materials)


def _cr16_requirement_map(
    *,
    cr09: Mapping[str, Any],
    cr10: Mapping[str, Any],
    cr11: Mapping[str, Any],
    cr12: Mapping[str, Any],
    cr13: Mapping[str, Any],
    cr14: Mapping[str, Any],
    cr15: Mapping[str, Any],
    source_materials: Sequence[Mapping[str, Any]],
) -> dict[str, bool]:
    reviewed_count = int(cr09.get("reviewed_case_count") or 0)
    sanitized_count = int(cr10.get("sanitized_review_result_row_count") or 0)
    rating_count = int(cr11.get("rating_row_count") or 0)
    question_count = int(cr13.get("question_need_observation_row_count") or 0)
    return {
        "cr09_actual_operation_receipt_ready": cr09.get("operation_receipt_ready") is True,
        "cr09_person_execution_confirmed": cr09.get("actual_human_review_executed_by_person") is True,
        "reviewed_case_count_is_24": reviewed_count == P7_R54_AHR_CR_REQUIRED_CASE_COUNT,
        "cr10_sanitized_selection_rows_ready": cr10.get("sanitized_selection_only_result_rows_ready") is True,
        "sanitized_review_result_row_count_is_24": sanitized_count == P7_R54_AHR_CR_REQUIRED_CASE_COUNT,
        "cr11_rating_rows_ready": cr11.get("rating_row_normalization_ready") is True,
        "rating_row_count_is_24": rating_count == P7_R54_AHR_CR_REQUIRED_CASE_COUNT,
        "cr12_blocker_normalization_ready": cr12.get("readfeel_execution_blocker_normalization_ready") is True,
        "cr13_question_observation_rows_ready": cr13.get("question_need_observation_normalization_ready") is True,
        "question_need_observation_row_count_is_24": question_count == P7_R54_AHR_CR_REQUIRED_CASE_COUNT,
        "cr14_rating_question_consistency_guard_passed": cr14.get("rating_question_consistency_guard_passed") is True,
        "cr15_disposal_receipt_ready": cr15.get("pause_abort_expiration_disposal_receipt_ready") is True,
        "disposal_verified": cr15.get("disposal_verified") is True,
        "no_body_leak_validation_passed": _cr16_no_body_leak_passed(source_materials),
        "no_question_text_validation_passed": _cr16_no_question_text_passed(source_materials),
        "no_touch_validation_passed": _cr16_no_touch_passed(source_materials),
        "source_materials_have_no_forbidden_keys": _cr16_sources_have_no_forbidden_keys(source_materials),
    }


def _cr16_blockers_from_requirements(requirements: Mapping[str, bool]) -> list[str]:
    blocker_by_requirement = {
        "cr09_actual_operation_receipt_ready": P7_R54_AHR_CR16_CR09_NOT_READY_BLOCKER_REF,
        "cr09_person_execution_confirmed": P7_R54_AHR_CR16_PERSON_EXECUTION_NOT_CONFIRMED_BLOCKER_REF,
        "reviewed_case_count_is_24": P7_R54_AHR_CR16_REVIEWED_CASE_COUNT_NOT_24_BLOCKER_REF,
        "cr10_sanitized_selection_rows_ready": P7_R54_AHR_CR16_CR10_NOT_READY_BLOCKER_REF,
        "sanitized_review_result_row_count_is_24": P7_R54_AHR_CR16_SANITIZED_ROW_COUNT_NOT_24_BLOCKER_REF,
        "cr11_rating_rows_ready": P7_R54_AHR_CR16_CR11_NOT_READY_BLOCKER_REF,
        "rating_row_count_is_24": P7_R54_AHR_CR16_RATING_ROW_COUNT_NOT_24_BLOCKER_REF,
        "cr12_blocker_normalization_ready": P7_R54_AHR_CR16_CR12_NOT_READY_BLOCKER_REF,
        "cr13_question_observation_rows_ready": P7_R54_AHR_CR16_CR13_NOT_READY_BLOCKER_REF,
        "question_need_observation_row_count_is_24": P7_R54_AHR_CR16_QUESTION_ROW_COUNT_NOT_24_BLOCKER_REF,
        "cr14_rating_question_consistency_guard_passed": P7_R54_AHR_CR16_CR14_NOT_PASSED_BLOCKER_REF,
        "cr15_disposal_receipt_ready": P7_R54_AHR_CR16_CR15_NOT_READY_BLOCKER_REF,
        "disposal_verified": P7_R54_AHR_CR16_DISPOSAL_NOT_VERIFIED_BLOCKER_REF,
        "no_body_leak_validation_passed": P7_R54_AHR_CR16_BODY_LEAK_VALIDATION_BLOCKER_REF,
        "no_question_text_validation_passed": P7_R54_AHR_CR16_QUESTION_TEXT_VALIDATION_BLOCKER_REF,
        "no_touch_validation_passed": P7_R54_AHR_CR16_NO_TOUCH_VALIDATION_BLOCKER_REF,
        "source_materials_have_no_forbidden_keys": P7_R54_AHR_CR16_SOURCE_FORBIDDEN_KEY_BLOCKER_REF,
    }
    return _dedupe_string_refs(
        [blocker for requirement, blocker in blocker_by_requirement.items() if requirements.get(requirement) is not True],
        limit=200,
        max_length=240,
    )


def build_p7_r54_ahr_cr16_post_review_summary_evidence_complete_predicate(
    *,
    actual_local_human_review_operation_receipt: Mapping[str, Any] | None = None,
    sanitized_selection_only_result_rows_intake: Mapping[str, Any] | None = None,
    rating_row_normalization: Mapping[str, Any] | None = None,
    readfeel_execution_blocker_normalization: Mapping[str, Any] | None = None,
    question_need_observation_normalization: Mapping[str, Any] | None = None,
    rating_question_consistency_guard: Mapping[str, Any] | None = None,
    disposal_receipt: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build CR16 body-free post-review summary / evidence complete predicate."""

    cr09 = dict(actual_local_human_review_operation_receipt or build_p7_r54_ahr_cr09_actual_local_human_review_operation_receipt())
    cr10 = dict(sanitized_selection_only_result_rows_intake or build_p7_r54_ahr_cr10_sanitized_selection_only_result_rows_intake())
    cr11 = dict(rating_row_normalization or build_p7_r54_ahr_cr11_rating_row_normalization())
    cr12 = dict(readfeel_execution_blocker_normalization or build_p7_r54_ahr_cr12_readfeel_execution_blocker_normalization())
    cr13 = dict(question_need_observation_normalization or build_p7_r54_ahr_cr13_question_need_observation_normalization())
    cr14 = dict(rating_question_consistency_guard or build_p7_r54_ahr_cr14_rating_question_consistency_guard())
    cr15 = dict(disposal_receipt or build_p7_r54_ahr_cr15_pause_abort_expiration_disposal_receipt())
    assert_p7_r54_ahr_cr09_actual_local_human_review_operation_receipt_contract(cr09)
    assert_p7_r54_ahr_cr10_sanitized_selection_only_result_rows_intake_contract(cr10)
    assert_p7_r54_ahr_cr11_rating_row_normalization_contract(cr11)
    assert_p7_r54_ahr_cr12_readfeel_execution_blocker_normalization_contract(cr12)
    assert_p7_r54_ahr_cr13_question_need_observation_normalization_contract(cr13)
    assert_p7_r54_ahr_cr14_rating_question_consistency_guard_contract(cr14)
    assert_p7_r54_ahr_cr15_pause_abort_expiration_disposal_receipt_contract(cr15)
    session_id = _safe_review_session_id(review_session_id)
    source_materials = _cr16_all_source_materials(cr09, cr10, cr11, cr12, cr13, cr14, cr15)
    requirements = _cr16_requirement_map(
        cr09=cr09,
        cr10=cr10,
        cr11=cr11,
        cr12=cr12,
        cr13=cr13,
        cr14=cr14,
        cr15=cr15,
        source_materials=source_materials,
    )
    blockers = _cr16_blockers_from_requirements(requirements)
    ready = not blockers
    passed_requirement_refs = [ref for ref, passed in requirements.items() if passed is True]
    failed_requirement_refs = [ref for ref, passed in requirements.items() if passed is not True]
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CR16_POST_REVIEW_SUMMARY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CR_STEP,
        "scope": P7_R54_AHR_CR_SCOPE,
        "policy_kind": P7_R54_AHR_CR_POLICY_KIND,
        "policy_section": P7_R54_AHR_CR16_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CR16_STEP_REF,
        "current_phase": P7_R54_AHR_CR_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cr16_post_review_summary_evidence_complete_predicate_20260628",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cr09_schema_version": cr09.get("schema_version"),
        "cr09_material_ref": cr09.get("material_id"),
        "cr09_next_required_step": cr09.get("next_required_step"),
        "cr09_operation_receipt_ready": cr09.get("operation_receipt_ready"),
        "cr09_operation_receipt_status_ref": cr09.get("operation_receipt_status_ref"),
        "cr09_actual_human_review_executed_by_person": cr09.get("actual_human_review_executed_by_person"),
        "cr09_reviewed_case_count": cr09.get("reviewed_case_count"),
        "cr09_selection_row_count": cr09.get("selection_row_count"),
        "cr10_schema_version": cr10.get("schema_version"),
        "cr10_material_ref": cr10.get("material_id"),
        "cr10_next_required_step": cr10.get("next_required_step"),
        "cr10_sanitized_selection_only_result_rows_ready": cr10.get("sanitized_selection_only_result_rows_ready"),
        "cr10_sanitized_review_result_row_count": cr10.get("sanitized_review_result_row_count"),
        "cr11_schema_version": cr11.get("schema_version"),
        "cr11_material_ref": cr11.get("material_id"),
        "cr11_next_required_step": cr11.get("next_required_step"),
        "cr11_rating_row_normalization_ready": cr11.get("rating_row_normalization_ready"),
        "cr11_rating_row_count": cr11.get("rating_row_count"),
        "cr12_schema_version": cr12.get("schema_version"),
        "cr12_material_ref": cr12.get("material_id"),
        "cr12_next_required_step": cr12.get("next_required_step"),
        "cr12_readfeel_execution_blocker_normalization_ready": cr12.get(
            "readfeel_execution_blocker_normalization_ready"
        ),
        "cr12_p5_repair_required_case_count": cr12.get("p5_repair_required_case_count"),
        "cr12_p4_current_only_repair_required_case_count": cr12.get("p4_current_only_repair_required_case_count"),
        "cr12_operation_blocked_case_count": cr12.get("operation_blocked_case_count"),
        "cr12_inconclusive_insufficient_material_case_count": cr12.get("inconclusive_insufficient_material_case_count"),
        "cr13_schema_version": cr13.get("schema_version"),
        "cr13_material_ref": cr13.get("material_id"),
        "cr13_next_required_step": cr13.get("next_required_step"),
        "cr13_question_need_observation_normalization_ready": cr13.get("question_need_observation_normalization_ready"),
        "cr13_question_need_observation_row_count": cr13.get("question_need_observation_row_count"),
        "cr13_p8_material_candidate_case_count": cr13.get("p8_material_candidate_case_count"),
        "cr14_schema_version": cr14.get("schema_version"),
        "cr14_material_ref": cr14.get("material_id"),
        "cr14_next_required_step": cr14.get("next_required_step"),
        "cr14_rating_question_consistency_guard_status_ref": cr14.get("rating_question_consistency_guard_status_ref"),
        "cr14_rating_question_consistency_guard_passed": cr14.get("rating_question_consistency_guard_passed"),
        "cr14_consistency_issue_row_count": cr14.get("consistency_issue_row_count"),
        "cr15_schema_version": cr15.get("schema_version"),
        "cr15_material_ref": cr15.get("material_id"),
        "cr15_next_required_step": cr15.get("next_required_step"),
        "cr15_pause_abort_expiration_disposal_receipt_ready": cr15.get("pause_abort_expiration_disposal_receipt_ready"),
        "cr15_disposal_verified": cr15.get("disposal_verified"),
        "cr15_actual_disposal_receipt_materialized_here": cr15.get("actual_disposal_receipt_materialized_here"),
        **_current_received_basis_fields(actual_basis=True),
        **_historical_basis_fields(),
        "post_review_summary_status_ref": (
            P7_R54_AHR_CR16_EVIDENCE_COMPLETE_STATUS_REF if ready else P7_R54_AHR_CR16_EVIDENCE_INCOMPLETE_STATUS_REF
        ),
        "post_review_summary_allowed_status_refs": list(P7_R54_AHR_CR16_ALLOWED_STATUS_REFS),
        "post_review_summary_ready": ready,
        "post_review_summary_reason_refs": [P7_R54_AHR_CR16_READY_REASON_REF] if ready else [],
        "post_review_summary_step_blocker_refs": blockers,
        "post_review_summary_step_blocker_ref_count": len(blockers),
        "actual_review_evidence_complete_predicate_evaluated": True,
        "actual_review_evidence_complete_requirements": dict(requirements),
        "actual_review_evidence_complete_requirement_count": len(requirements),
        "actual_review_evidence_complete_passed_requirement_refs": passed_requirement_refs,
        "actual_review_evidence_complete_passed_requirement_count": len(passed_requirement_refs),
        "actual_review_evidence_complete_failed_requirement_refs": failed_requirement_refs,
        "actual_review_evidence_complete_failed_requirement_count": len(failed_requirement_refs),
        "reviewed_case_count": int(cr09.get("reviewed_case_count") or 0) if ready else 0,
        "sanitized_review_result_row_count": int(cr10.get("sanitized_review_result_row_count") or 0) if ready else 0,
        "rating_row_count": int(cr11.get("rating_row_count") or 0) if ready else 0,
        "question_need_observation_row_count": int(cr13.get("question_need_observation_row_count") or 0) if ready else 0,
        "disposal_receipt_verified_here": cr15.get("disposal_verified") is True and ready,
        "consistency_guard_passed": cr14.get("rating_question_consistency_guard_passed") is True and ready,
        "no_body_leak_validation_passed": requirements["no_body_leak_validation_passed"] is True,
        "no_question_text_validation_passed": requirements["no_question_text_validation_passed"] is True,
        "no_touch_validation_passed": requirements["no_touch_validation_passed"] is True,
        "source_materials_bodyfree_only": all(material.get("body_free") is True for material in source_materials),
        "source_materials_have_no_forbidden_keys": requirements["source_materials_have_no_forbidden_keys"] is True,
        "post_review_summary_bodyfree_only": True,
        "post_review_summary_does_not_create_question_text": True,
        "post_review_summary_does_not_change_api_db_rn_runtime": True,
        "p5_decision_separation_allowed_next": ready,
        "p5_confirmed_candidate": ready
        and int(cr12.get("p5_repair_required_case_count") or 0) == 0
        and int(cr12.get("p4_current_only_repair_required_case_count") or 0) == 0
        and int(cr12.get("operation_blocked_case_count") or 0) == 0
        and int(cr12.get("inconclusive_insufficient_material_case_count") or 0) == 0
        and int(cr14.get("consistency_issue_row_count") or 0) == 0,
        "p5_confirmed_candidate_only": ready,
        "p5_confirmed_candidate_is_not_p5_final": True,
        "p5_repair_required_case_count": int(cr12.get("p5_repair_required_case_count") or 0) if ready else 0,
        "p4_current_only_repair_required_case_count": int(cr12.get("p4_current_only_repair_required_case_count") or 0) if ready else 0,
        "operation_blocked_case_count": int(cr12.get("operation_blocked_case_count") or 0) if ready else 0,
        "inconclusive_insufficient_material_case_count": int(cr12.get("inconclusive_insufficient_material_case_count") or 0) if ready else 0,
        "p8_material_candidate_case_count": int(cr13.get("p8_material_candidate_case_count") or 0) if ready else 0,
        "actual_human_review_complete": ready,
        "actual_review_evidence_complete": ready,
        "actual_rating_rows_materialized_here": ready,
        "actual_question_need_observation_rows_materialized_here": ready,
        "actual_disposal_receipt_materialized_here": ready,
        "disposal_verified": ready,
        "actual_human_review_executed_by_person": ready,
        "actual_human_review_run_here": False,
        "actual_human_review_operation_run": False,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "p8_question_implementation_spec_finalized_here": False,
        "p5_human_blind_qa_confirmed_final": False,
        "p5_confirmed_final": False,
        "p5_final_allowed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_start_allowed": False,
        "p8_start_allowed": False,
        "r52_reintake_execution_requested_here": False,
        "actual_r52_reintake_execution_confirmed": False,
        "p7_complete": False,
        "release_allowed": False,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR_CR16_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CR15_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_CR16_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CR15_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_CR17_STEP_REF if ready else P7_R54_AHR_CR16_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    material["actual_human_review_complete"] = ready
    material["actual_review_evidence_complete"] = ready
    material["actual_rating_rows_materialized_here"] = ready
    material["actual_question_need_observation_rows_materialized_here"] = ready
    material["actual_disposal_receipt_materialized_here"] = ready
    material["disposal_verified"] = ready
    material["actual_human_review_executed_by_person"] = ready
    return material


def assert_p7_r54_ahr_cr16_post_review_summary_evidence_complete_predicate_contract(
    data: Mapping[str, Any]
) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CR16_POST_REVIEW_SUMMARY_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CR16 post-review summary",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CR16_POST_REVIEW_SUMMARY_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CR16_STEP_REF,
        operation_step_ref=P7_R54_AHR_CR16_STEP_REF,
        source="P7-R54-AHR-CR16 post-review summary",
        allowed_true_false_flag_refs=P7_R54_AHR_CR16_ALLOWED_TRUE_OPERATION_FLAG_REFS,
    )
    _assert_current_received_basis_fields(data, actual_basis=True, source="P7-R54-AHR-CR16 post-review summary")
    _assert_historical_basis_fields(data, source="P7-R54-AHR-CR16 post-review summary")
    if tuple(data.get("post_review_summary_allowed_status_refs") or ()) != P7_R54_AHR_CR16_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-CR16 allowed status refs changed")
    ready = data.get("post_review_summary_status_ref") == P7_R54_AHR_CR16_EVIDENCE_COMPLETE_STATUS_REF
    if data.get("post_review_summary_ready") is not ready:
        raise ValueError("P7-R54-AHR-CR16 ready flag changed")
    blockers = list(data.get("post_review_summary_step_blocker_refs") or [])
    if data.get("post_review_summary_step_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-CR16 blocker count changed")
    requirements = data.get("actual_review_evidence_complete_requirements")
    if not isinstance(requirements, Mapping):
        raise ValueError("P7-R54-AHR-CR16 requirements must be a mapping")
    passed_refs = list(data.get("actual_review_evidence_complete_passed_requirement_refs") or [])
    failed_refs = list(data.get("actual_review_evidence_complete_failed_requirement_refs") or [])
    if data.get("actual_review_evidence_complete_requirement_count") != len(requirements):
        raise ValueError("P7-R54-AHR-CR16 requirement count changed")
    if data.get("actual_review_evidence_complete_passed_requirement_count") != len(passed_refs):
        raise ValueError("P7-R54-AHR-CR16 passed requirement count changed")
    if data.get("actual_review_evidence_complete_failed_requirement_count") != len(failed_refs):
        raise ValueError("P7-R54-AHR-CR16 failed requirement count changed")
    if set(passed_refs) | set(failed_refs) != set(requirements):
        raise ValueError("P7-R54-AHR-CR16 requirement refs changed")
    _assert_true_fields(
        data,
        keys=(
            "actual_review_evidence_complete_predicate_evaluated",
            "post_review_summary_bodyfree_only",
            "post_review_summary_does_not_create_question_text",
            "post_review_summary_does_not_change_api_db_rn_runtime",
            "p5_confirmed_candidate_is_not_p5_final",
            "r52_reintake_claim_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "p5_finalization_blocked_here",
        ),
        source="P7-R54-AHR-CR16 post-review summary",
    )
    _assert_false_fields(
        data,
        keys=(
            "actual_human_review_run_here",
            "actual_human_review_operation_run",
            "question_text_materialized_here",
            "draft_question_text_materialized_here",
            "p8_question_implementation_spec_finalized_here",
            "p5_human_blind_qa_confirmed_final",
            "p5_confirmed_final",
            "p5_final_allowed",
            "p6_limited_human_readfeel_start_allowed",
            "p6_start_allowed",
            "p8_start_allowed",
            "r52_reintake_execution_requested_here",
            "actual_r52_reintake_execution_confirmed",
            "p7_complete",
            "release_allowed",
        ),
        source="P7-R54-AHR-CR16 post-review summary",
    )
    if ready:
        if blockers or failed_refs:
            raise ValueError("P7-R54-AHR-CR16 complete summary cannot carry blockers or failed requirements")
        if data.get("post_review_summary_reason_refs") != [P7_R54_AHR_CR16_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-CR16 ready reason changed")
        _assert_true_fields(
            data,
            keys=(
                "actual_human_review_complete",
                "actual_review_evidence_complete",
                "actual_rating_rows_materialized_here",
                "actual_question_need_observation_rows_materialized_here",
                "actual_disposal_receipt_materialized_here",
                "disposal_verified",
                "actual_human_review_executed_by_person",
                "disposal_receipt_verified_here",
                "consistency_guard_passed",
                "no_body_leak_validation_passed",
                "no_question_text_validation_passed",
                "no_touch_validation_passed",
                "source_materials_bodyfree_only",
                "source_materials_have_no_forbidden_keys",
                "p5_decision_separation_allowed_next",
            ),
            source="P7-R54-AHR-CR16 complete summary",
        )
        for field in (
            "reviewed_case_count",
            "sanitized_review_result_row_count",
            "rating_row_count",
            "question_need_observation_row_count",
        ):
            if data.get(field) != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
                raise ValueError(f"P7-R54-AHR-CR16 {field} changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CR16_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CR16 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CR16_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CR16 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_CR17_STEP_REF:
            raise ValueError("P7-R54-AHR-CR16 ready next step changed")
    else:
        if data.get("post_review_summary_status_ref") != P7_R54_AHR_CR16_EVIDENCE_INCOMPLETE_STATUS_REF:
            raise ValueError("P7-R54-AHR-CR16 blocked status changed")
        if not blockers or not failed_refs:
            raise ValueError("P7-R54-AHR-CR16 incomplete summary must carry blockers and failed requirements")
        _assert_false_fields(
            data,
            keys=(
                "actual_human_review_complete",
                "actual_review_evidence_complete",
                "actual_rating_rows_materialized_here",
                "actual_question_need_observation_rows_materialized_here",
                "actual_disposal_receipt_materialized_here",
                "disposal_verified",
                "actual_human_review_executed_by_person",
                "p5_decision_separation_allowed_next",
            ),
            source="P7-R54-AHR-CR16 incomplete summary",
        )
        if data.get("post_review_summary_reason_refs") != []:
            raise ValueError("P7-R54-AHR-CR16 blocked material cannot carry ready reasons")
        if data.get("next_required_step") != P7_R54_AHR_CR16_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CR16 blocked next step changed")
    return True


def _cr17_decision_ref_from_summary(summary: Mapping[str, Any]) -> str:
    if summary.get("actual_review_evidence_complete") is not True or summary.get("post_review_summary_ready") is not True:
        return P7_R54_AHR_CR17_OPERATION_INCONCLUSIVE_REF
    if summary.get("disposal_verified") is not True:
        return P7_R54_AHR_CR17_OPERATION_BLOCKED_DISPOSAL_REF
    if summary.get("no_body_leak_validation_passed") is not True or summary.get("no_question_text_validation_passed") is not True:
        return P7_R54_AHR_CR17_OPERATION_BLOCKED_BODY_OR_QUESTION_REF
    if int(summary.get("operation_blocked_case_count") or 0) > 0:
        return P7_R54_AHR_CR17_OPERATION_BLOCKED_BODY_OR_QUESTION_REF
    if int(summary.get("inconclusive_insufficient_material_case_count") or 0) > 0:
        return P7_R54_AHR_CR17_OPERATION_INCONCLUSIVE_REF
    if int(summary.get("p4_current_only_repair_required_case_count") or 0) > 0:
        return P7_R54_AHR_CR17_P4_CURRENT_ONLY_REPAIR_REQUIRED_REF
    if int(summary.get("p5_repair_required_case_count") or 0) > 0:
        return P7_R54_AHR_CR17_P5_REPAIR_REQUIRED_REF
    return P7_R54_AHR_CR17_P5_CONFIRMED_CANDIDATE_REF


def build_p7_r54_ahr_cr17_p5_decision_candidate_repair_separation(
    *,
    post_review_summary: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build CR17 body-free P5 decision candidate / repair separation."""

    cr16 = dict(post_review_summary or build_p7_r54_ahr_cr16_post_review_summary_evidence_complete_predicate())
    assert_p7_r54_ahr_cr16_post_review_summary_evidence_complete_predicate_contract(cr16)
    session_id = _safe_review_session_id(review_session_id or cr16.get("review_session_id"))
    cr16_ready = cr16.get("post_review_summary_ready") is True and cr16.get("actual_review_evidence_complete") is True
    blockers = [] if cr16_ready else [P7_R54_AHR_CR17_CR16_NOT_COMPLETE_BLOCKER_REF]
    decision_ref = _cr17_decision_ref_from_summary(cr16)
    confirmed_candidate = cr16_ready and decision_ref == P7_R54_AHR_CR17_P5_CONFIRMED_CANDIDATE_REF
    repair_or_blocked = cr16_ready and not confirmed_candidate
    p5_repair_count = int(cr16.get("p5_repair_required_case_count") or 0) if cr16_ready else 0
    p4_repair_count = int(cr16.get("p4_current_only_repair_required_case_count") or 0) if cr16_ready else 0
    operation_blocked_count = int(cr16.get("operation_blocked_case_count") or 0) if cr16_ready else 0
    inconclusive_count = int(cr16.get("inconclusive_insufficient_material_case_count") or 0) if cr16_ready else 0
    p8_material_count = int(cr16.get("p8_material_candidate_case_count") or 0) if cr16_ready else 0
    repair_or_blocker_case_count = p5_repair_count + p4_repair_count + operation_blocked_count + inconclusive_count
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CR17_P5_DECISION_CANDIDATE_REPAIR_SEPARATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CR_STEP,
        "scope": P7_R54_AHR_CR_SCOPE,
        "policy_kind": P7_R54_AHR_CR_POLICY_KIND,
        "policy_section": P7_R54_AHR_CR17_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CR17_STEP_REF,
        "current_phase": P7_R54_AHR_CR_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cr17_p5_decision_candidate_repair_separation_20260628",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cr16_schema_version": cr16.get("schema_version"),
        "cr16_material_ref": cr16.get("material_id"),
        "cr16_next_required_step": cr16.get("next_required_step"),
        "cr16_post_review_summary_ready": cr16.get("post_review_summary_ready"),
        "cr16_actual_review_evidence_complete": cr16.get("actual_review_evidence_complete"),
        "cr16_actual_human_review_complete": cr16.get("actual_human_review_complete"),
        "cr16_p5_confirmed_candidate": cr16.get("p5_confirmed_candidate"),
        "cr16_p5_repair_required_case_count": cr16.get("p5_repair_required_case_count"),
        "cr16_p4_current_only_repair_required_case_count": cr16.get("p4_current_only_repair_required_case_count"),
        "cr16_operation_blocked_case_count": cr16.get("operation_blocked_case_count"),
        "cr16_inconclusive_insufficient_material_case_count": cr16.get("inconclusive_insufficient_material_case_count"),
        "cr16_p8_material_candidate_case_count": cr16.get("p8_material_candidate_case_count"),
        **_current_received_basis_fields(actual_basis=True),
        **_historical_basis_fields(),
        "p5_decision_candidate_separation_status_ref": (
            P7_R54_AHR_CR17_CONFIRMED_CANDIDATE_STATUS_REF
            if confirmed_candidate
            else P7_R54_AHR_CR17_REPAIR_OR_BLOCKED_STATUS_REF if repair_or_blocked else P7_R54_AHR_CR17_BLOCKED_STATUS_REF
        ),
        "p5_decision_candidate_separation_allowed_status_refs": list(P7_R54_AHR_CR17_ALLOWED_STATUS_REFS),
        "p5_decision_candidate_separation_ready": cr16_ready,
        "p5_decision_candidate_separation_reason_refs": (
            [P7_R54_AHR_CR17_READY_REASON_REF]
            if confirmed_candidate
            else [P7_R54_AHR_CR17_REPAIR_REASON_REF] if repair_or_blocked else []
        ),
        "p5_decision_candidate_separation_step_blocker_refs": blockers,
        "p5_decision_candidate_separation_step_blocker_ref_count": len(blockers),
        "p5_decision_ref": decision_ref,
        "p5_decision_allowed_refs": list(P7_R54_AHR_CR17_DECISION_REF_REFS),
        "p5_confirmed_candidate": confirmed_candidate,
        "p5_confirmed_candidate_only": confirmed_candidate,
        "p5_confirmed_candidate_is_not_p5_final": True,
        "p5_decision_candidate_ready_for_r52_handoff": confirmed_candidate,
        "p5_repair_required_before_r52": decision_ref == P7_R54_AHR_CR17_P5_REPAIR_REQUIRED_REF,
        "p4_current_only_repair_required_before_r52": decision_ref == P7_R54_AHR_CR17_P4_CURRENT_ONLY_REPAIR_REQUIRED_REF,
        "operation_blocked_before_r52": decision_ref in (
            P7_R54_AHR_CR17_OPERATION_BLOCKED_BODY_OR_QUESTION_REF,
            P7_R54_AHR_CR17_OPERATION_BLOCKED_DISPOSAL_REF,
        ),
        "inconclusive_before_r52": decision_ref == P7_R54_AHR_CR17_OPERATION_INCONCLUSIVE_REF,
        "p5_repair_required_case_count": p5_repair_count,
        "p4_current_only_repair_required_case_count": p4_repair_count,
        "operation_blocked_case_count": operation_blocked_count,
        "inconclusive_insufficient_material_case_count": inconclusive_count,
        "p8_material_candidate_case_count": p8_material_count,
        "repair_or_blocker_case_count": repair_or_blocker_case_count,
        "p5_repair_required_case_refs": [],
        "p4_current_only_repair_required_case_refs": [],
        "operation_blocked_case_refs": [],
        "inconclusive_insufficient_material_case_refs": [],
        "decision_boundary_refs": [
            "P5_CONFIRMED_CANDIDATE_IS_NOT_P5_FINAL",
            "P5_REPAIR_REQUIRED_IS_NOT_P8_MATERIAL_CANDIDATE",
            "P4_CURRENT_ONLY_REPAIR_REQUIRED_IS_NOT_P8_MATERIAL_CANDIDATE",
            "OPERATION_BLOCKER_IS_NOT_R52_EXECUTION",
            "P8_MATERIAL_CANDIDATE_ONLY_IS_NOT_P8_START_ALLOWED",
        ],
        "decision_boundary_ref_count": 5,
        "p5_finalization_remains_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "r52_actual_execution_blocked_here": True,
        "p8_material_candidate_only_is_not_p8_start_allowed": True,
        "p5_confirmed_candidate_not_promoted_to_final": True,
        "p5_repair_required_not_promoted_to_p8_material_candidate": True,
        "actual_human_review_complete": cr16_ready,
        "actual_review_evidence_complete": cr16_ready,
        "actual_rating_rows_materialized_here": cr16_ready,
        "actual_question_need_observation_rows_materialized_here": cr16_ready,
        "actual_disposal_receipt_materialized_here": cr16_ready,
        "disposal_verified": cr16_ready,
        "actual_human_review_executed_by_person": cr16_ready,
        "actual_human_review_run_here": False,
        "actual_human_review_operation_run": False,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "p8_question_implementation_spec_finalized_here": False,
        "p5_human_blind_qa_confirmed_final": False,
        "p5_confirmed_final": False,
        "p5_final_allowed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_start_allowed": False,
        "p8_start_allowed": False,
        "r52_reintake_execution_requested_here": False,
        "actual_r52_reintake_execution_confirmed": False,
        "p7_complete": False,
        "release_allowed": False,
        "implemented_steps": list(P7_R54_AHR_CR17_IMPLEMENTED_STEPS if cr16_ready else P7_R54_AHR_CR16_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(
            P7_R54_AHR_CR17_NOT_YET_IMPLEMENTED_STEPS if cr16_ready else P7_R54_AHR_CR16_NOT_YET_IMPLEMENTED_STEPS
        ),
        "next_required_step": (
            P7_R54_AHR_CR18_STEP_REF
            if confirmed_candidate
            else P7_R54_AHR_CR17_REPAIR_NEXT_REQUIRED_STEP_REF if repair_or_blocked else P7_R54_AHR_CR17_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
        ),
        "public_contract": public_contract_flags(),
        "r54_ahr_cr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    material["actual_human_review_complete"] = cr16_ready
    material["actual_review_evidence_complete"] = cr16_ready
    material["actual_rating_rows_materialized_here"] = cr16_ready
    material["actual_question_need_observation_rows_materialized_here"] = cr16_ready
    material["actual_disposal_receipt_materialized_here"] = cr16_ready
    material["disposal_verified"] = cr16_ready
    material["actual_human_review_executed_by_person"] = cr16_ready
    return material


def assert_p7_r54_ahr_cr17_p5_decision_candidate_repair_separation_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CR17_P5_DECISION_CANDIDATE_REPAIR_SEPARATION_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CR17 P5 decision separation",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CR17_P5_DECISION_CANDIDATE_REPAIR_SEPARATION_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CR17_STEP_REF,
        operation_step_ref=P7_R54_AHR_CR17_STEP_REF,
        source="P7-R54-AHR-CR17 P5 decision separation",
        allowed_true_false_flag_refs=P7_R54_AHR_CR17_ALLOWED_TRUE_OPERATION_FLAG_REFS,
    )
    _assert_current_received_basis_fields(data, actual_basis=True, source="P7-R54-AHR-CR17 P5 decision separation")
    _assert_historical_basis_fields(data, source="P7-R54-AHR-CR17 P5 decision separation")
    if tuple(data.get("p5_decision_candidate_separation_allowed_status_refs") or ()) != P7_R54_AHR_CR17_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-CR17 allowed status refs changed")
    if tuple(data.get("p5_decision_allowed_refs") or ()) != P7_R54_AHR_CR17_DECISION_REF_REFS:
        raise ValueError("P7-R54-AHR-CR17 decision refs changed")
    blockers = list(data.get("p5_decision_candidate_separation_step_blocker_refs") or [])
    if data.get("p5_decision_candidate_separation_step_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-CR17 blocker count changed")
    cr16_ready = data.get("cr16_post_review_summary_ready") is True and data.get("cr16_actual_review_evidence_complete") is True
    if data.get("p5_decision_candidate_separation_ready") is not cr16_ready:
        raise ValueError("P7-R54-AHR-CR17 ready flag changed")
    _assert_true_fields(
        data,
        keys=(
            "p5_confirmed_candidate_is_not_p5_final",
            "p5_finalization_remains_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "r52_actual_execution_blocked_here",
            "p8_material_candidate_only_is_not_p8_start_allowed",
            "p5_confirmed_candidate_not_promoted_to_final",
            "p5_repair_required_not_promoted_to_p8_material_candidate",
        ),
        source="P7-R54-AHR-CR17 P5 decision separation",
    )
    _assert_false_fields(
        data,
        keys=(
            "actual_human_review_run_here",
            "actual_human_review_operation_run",
            "question_text_materialized_here",
            "draft_question_text_materialized_here",
            "p8_question_implementation_spec_finalized_here",
            "p5_human_blind_qa_confirmed_final",
            "p5_confirmed_final",
            "p5_final_allowed",
            "p6_limited_human_readfeel_start_allowed",
            "p6_start_allowed",
            "p8_start_allowed",
            "r52_reintake_execution_requested_here",
            "actual_r52_reintake_execution_confirmed",
            "p7_complete",
            "release_allowed",
        ),
        source="P7-R54-AHR-CR17 P5 decision separation",
    )
    confirmed = data.get("p5_decision_ref") == P7_R54_AHR_CR17_P5_CONFIRMED_CANDIDATE_REF
    if cr16_ready:
        _assert_true_fields(
            data,
            keys=(
                "actual_human_review_complete",
                "actual_review_evidence_complete",
                "actual_rating_rows_materialized_here",
                "actual_question_need_observation_rows_materialized_here",
                "actual_disposal_receipt_materialized_here",
                "disposal_verified",
                "actual_human_review_executed_by_person",
            ),
            source="P7-R54-AHR-CR17 evidence flags",
        )
        if blockers:
            raise ValueError("P7-R54-AHR-CR17 ready separation cannot carry step blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CR17_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CR17 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CR17_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CR17 not-yet steps changed")
        if confirmed:
            if data.get("p5_decision_candidate_separation_status_ref") != P7_R54_AHR_CR17_CONFIRMED_CANDIDATE_STATUS_REF:
                raise ValueError("P7-R54-AHR-CR17 confirmed status changed")
            if data.get("p5_decision_candidate_separation_reason_refs") != [P7_R54_AHR_CR17_READY_REASON_REF]:
                raise ValueError("P7-R54-AHR-CR17 confirmed reason changed")
            _assert_true_fields(
                data,
                keys=("p5_confirmed_candidate", "p5_confirmed_candidate_only", "p5_decision_candidate_ready_for_r52_handoff"),
                source="P7-R54-AHR-CR17 confirmed candidate",
            )
            if data.get("repair_or_blocker_case_count") != 0:
                raise ValueError("P7-R54-AHR-CR17 confirmed candidate cannot carry repair/blocker cases")
            if data.get("next_required_step") != P7_R54_AHR_CR18_STEP_REF:
                raise ValueError("P7-R54-AHR-CR17 confirmed next step changed")
        else:
            if data.get("p5_decision_candidate_separation_status_ref") != P7_R54_AHR_CR17_REPAIR_OR_BLOCKED_STATUS_REF:
                raise ValueError("P7-R54-AHR-CR17 repair/blocker status changed")
            if data.get("p5_decision_candidate_separation_reason_refs") != [P7_R54_AHR_CR17_REPAIR_REASON_REF]:
                raise ValueError("P7-R54-AHR-CR17 repair/blocker reason changed")
            _assert_false_fields(
                data,
                keys=("p5_confirmed_candidate", "p5_confirmed_candidate_only", "p5_decision_candidate_ready_for_r52_handoff"),
                source="P7-R54-AHR-CR17 repair/blocker separation",
            )
            if data.get("next_required_step") != P7_R54_AHR_CR17_REPAIR_NEXT_REQUIRED_STEP_REF:
                raise ValueError("P7-R54-AHR-CR17 repair/blocker next step changed")
    else:
        if data.get("p5_decision_candidate_separation_status_ref") != P7_R54_AHR_CR17_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-CR17 blocked status changed")
        if P7_R54_AHR_CR17_CR16_NOT_COMPLETE_BLOCKER_REF not in blockers:
            raise ValueError("P7-R54-AHR-CR17 blocked material must carry CR16 blocker")
        _assert_false_fields(
            data,
            keys=(
                "actual_human_review_complete",
                "actual_review_evidence_complete",
                "actual_rating_rows_materialized_here",
                "actual_question_need_observation_rows_materialized_here",
                "actual_disposal_receipt_materialized_here",
                "disposal_verified",
                "actual_human_review_executed_by_person",
                "p5_confirmed_candidate",
                "p5_confirmed_candidate_only",
                "p5_decision_candidate_ready_for_r52_handoff",
            ),
            source="P7-R54-AHR-CR17 blocked separation",
        )
        if data.get("next_required_step") != P7_R54_AHR_CR17_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CR17 blocked next step changed")
    return True



# R54-AHR-CR18 / R54-AHR-CR19: P6 / P8 candidate-only handoff.
P7_R54_AHR_CR18_P6_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_received_actual_local_review_operation."
    "cr18_p6_candidate_only_handoff.bodyfree.v1"
)
P7_R54_AHR_CR19_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_received_actual_local_review_operation."
    "cr19_p8_material_candidate_only_handoff.bodyfree.v1"
)
P7_R54_AHR_CR_P6_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CR18_P6_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION
)
P7_R54_AHR_CR_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CR19_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION
)

P7_R54_AHR_CR18_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR17_IMPLEMENTED_STEPS,
    P7_R54_AHR_CR18_STEP_REF,
)
P7_R54_AHR_CR18_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CR_STEP_REFS[19:]
P7_R54_AHR_CR19_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR18_IMPLEMENTED_STEPS,
    P7_R54_AHR_CR19_STEP_REF,
)
P7_R54_AHR_CR19_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CR_STEP_REFS[20:]

P7_R54_AHR_CR18_READY_STATUS_REF: Final = "CR18_P6_CANDIDATE_ONLY_HANDOFF_MATERIALIZED_BODYFREE"
P7_R54_AHR_CR18_BLOCKED_STATUS_REF: Final = "CR18_P6_CANDIDATE_ONLY_HANDOFF_BLOCKED"
P7_R54_AHR_CR18_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR18_READY_STATUS_REF,
    P7_R54_AHR_CR18_BLOCKED_STATUS_REF,
)
P7_R54_AHR_CR18_READY_REASON_REF: Final = (
    "CR18_CR17_P5_CONFIRMED_CANDIDATE_CAN_HANDOFF_TO_P6_CANDIDATE_ONLY"
)
P7_R54_AHR_CR18_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "cr17_p5_confirmed_candidate_or_stop"
P7_R54_AHR_CR18_CR17_NOT_READY_BLOCKER_REF: Final = "cr17_p5_decision_candidate_separation_not_ready"
P7_R54_AHR_CR18_CR17_NEXT_STEP_NOT_CR18_BLOCKER_REF: Final = "cr17_next_step_not_cr18"
P7_R54_AHR_CR18_P5_CONFIRMED_CANDIDATE_NOT_PRESENT_BLOCKER_REF: Final = (
    "cr17_p5_confirmed_candidate_not_present"
)
P7_R54_AHR_CR18_REPAIR_OR_BLOCKER_PRESENT_BLOCKER_REF: Final = "cr17_repair_or_blocker_present"
P7_R54_AHR_CR18_P6_CANDIDATE_REF: Final = "P6_LIMITED_HUMAN_READFEEL_CANDIDATE_BODYFREE_ONLY"
P7_R54_AHR_CR18_P6_CANDIDATE_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "P6_CANDIDATE_ONLY_IS_NOT_P6_START_ALLOWED",
    "P6_LIMITED_HUMAN_READFEEL_START_REMAINS_BLOCKED_HERE",
    "P5_CONFIRMED_CANDIDATE_IS_NOT_P5_FINAL",
    "P8_MATERIAL_CANDIDATE_ONLY_IS_NOT_P8_START_ALLOWED",
    "R52_HANDOFF_READY_IS_NOT_R52_REINTAKE_EXECUTED",
)
P7_R54_AHR_CR18_ALLOWED_TRUE_OPERATION_FLAG_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR17_ALLOWED_TRUE_OPERATION_FLAG_REFS
)

P7_R54_AHR_CR19_READY_STATUS_REF: Final = "CR19_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_MATERIALIZED_BODYFREE"
P7_R54_AHR_CR19_BLOCKED_STATUS_REF: Final = "CR19_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_BLOCKED"
P7_R54_AHR_CR19_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR19_READY_STATUS_REF,
    P7_R54_AHR_CR19_BLOCKED_STATUS_REF,
)
P7_R54_AHR_CR19_READY_REASON_REF: Final = (
    "CR19_CR13_CR14_CR17_P8_MATERIAL_CANDIDATE_ROWS_EXTRACTED_BODYFREE_WITHOUT_QUESTION_TEXT"
)
P7_R54_AHR_CR19_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "cr13_cr14_cr17_candidate_material_or_stop"
P7_R54_AHR_CR19_CR13_NOT_READY_BLOCKER_REF: Final = "cr13_question_need_observation_not_ready"
P7_R54_AHR_CR19_CR14_NOT_PASSED_BLOCKER_REF: Final = "cr14_rating_question_consistency_guard_not_passed"
P7_R54_AHR_CR19_CR17_P5_CANDIDATE_NOT_CONFIRMED_BLOCKER_REF: Final = (
    "cr17_p5_confirmed_candidate_not_present"
)
P7_R54_AHR_CR19_CR13_NEXT_STEP_NOT_CR14_BLOCKER_REF: Final = "cr13_next_step_not_cr14"
P7_R54_AHR_CR19_CR14_NEXT_STEP_NOT_CR15_BLOCKER_REF: Final = "cr14_next_step_not_cr15"
P7_R54_AHR_CR19_CR17_NEXT_STEP_NOT_CR18_BLOCKER_REF: Final = "cr17_next_step_not_cr18"
P7_R54_AHR_CR19_SOURCE_ROW_COUNT_NOT_24_BLOCKER_REF: Final = "cr13_question_observation_row_count_not_24"
P7_R54_AHR_CR19_SOURCE_ROW_FORBIDDEN_KEY_BLOCKER_REF: Final = (
    "cr13_question_observation_row_forbidden_body_question_path_hash_key"
)
P7_R54_AHR_CR19_CANDIDATE_ROW_INVALID_BLOCKER_REF: Final = "cr19_candidate_row_invalid"
P7_R54_AHR_CR19_PLUS_CANDIDATE_REF: Final = "plus_single_question_candidate_later"
P7_R54_AHR_CR19_PREMIUM_CANDIDATE_REF: Final = "premium_deep_dive_candidate_later"
P7_R54_AHR_CR19_OVERREAD_RISK_ONLY_CANDIDATE_REF: Final = "question_may_reduce_overread_risk_candidate_only"
P7_R54_AHR_CR19_NO_P8_MATERIAL_CANDIDATE_REF: Final = "no_p8_material_candidate_rows_from_current_actual_review"
P7_R54_AHR_CR19_ALLOWED_TRUE_OPERATION_FLAG_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR17_ALLOWED_TRUE_OPERATION_FLAG_REFS
)
P7_R54_AHR_CR19_P8_CANDIDATE_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "case_ref_id",
    "blind_case_id",
    "question_need_primary_class",
    "one_question_fit_ref",
    "p8_candidate_reason_ref",
    "plus_or_premium_candidate_ref",
    "body_free",
)
P7_R54_AHR_CR19_ALLOWED_CANDIDATE_ROW_KEY_REFS: Final[frozenset[str]] = frozenset(
    P7_R54_AHR_CR19_P8_CANDIDATE_ROW_REQUIRED_FIELD_REFS
)

P7_R54_AHR_CR18_P6_CANDIDATE_ONLY_HANDOFF_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR_BASE_REQUIRED_FIELD_REFS,
    "cr17_schema_version",
    "cr17_material_ref",
    "cr17_next_required_step",
    "cr17_p5_decision_candidate_separation_status_ref",
    "cr17_p5_decision_candidate_separation_ready",
    "cr17_p5_decision_ref",
    "cr17_p5_confirmed_candidate",
    "cr17_p5_confirmed_candidate_only",
    "cr17_p5_decision_candidate_ready_for_r52_handoff",
    "cr17_repair_or_blocker_case_count",
    "cr17_p5_repair_required_case_count",
    "cr17_p4_current_only_repair_required_case_count",
    "cr17_operation_blocked_case_count",
    "cr17_inconclusive_insufficient_material_case_count",
    "cr17_p8_material_candidate_case_count",
    *P7_R54_AHR_CR_CURRENT_RECEIVED_BASIS_FIELD_REFS,
    *P7_R54_AHR_CR_HISTORICAL_BASIS_FIELD_REFS,
    "p6_candidate_only_handoff_status_ref",
    "p6_candidate_only_handoff_allowed_status_refs",
    "p6_candidate_only_handoff_ready",
    "p6_candidate_only_handoff_materialized",
    "p6_candidate_only_handoff_reason_refs",
    "p6_candidate_only_handoff_step_blocker_refs",
    "p6_candidate_only_handoff_step_blocker_ref_count",
    "p6_candidate_ref",
    "p6_candidate_boundary_refs",
    "p6_candidate_boundary_ref_count",
    "p6_limited_human_readfeel_candidate_only",
    "p6_limited_human_readfeel_candidate_materialized",
    "p6_candidate_only_is_not_p6_start_allowed",
    "p6_start_remains_blocked_here",
    "p5_confirmed_candidate",
    "p5_confirmed_candidate_only",
    "p5_confirmed_candidate_is_not_p5_final",
    "p5_finalization_remains_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "r52_actual_execution_blocked_here",
    "p8_material_candidate_only_is_not_p8_start_allowed",
    "p5_confirmed_candidate_not_promoted_to_final",
    "actual_human_review_complete",
    "actual_review_evidence_complete",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_human_review_operation_run",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "p8_question_implementation_spec_finalized_here",
    "p5_human_blind_qa_confirmed_final",
    "p5_confirmed_final",
    "p5_final_allowed",
    "p6_limited_human_readfeel_start_allowed",
    "p6_start_allowed",
    "p8_start_allowed",
    "r52_reintake_execution_requested_here",
    "actual_r52_reintake_execution_confirmed",
    "p7_complete",
    "release_allowed",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CR_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CR_FALSE_FLAG_REFS,
)
P7_R54_AHR_CR_P6_CANDIDATE_ONLY_HANDOFF_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CR18_P6_CANDIDATE_ONLY_HANDOFF_REQUIRED_FIELD_REFS
)

P7_R54_AHR_CR19_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR_BASE_REQUIRED_FIELD_REFS,
    "cr13_schema_version",
    "cr13_material_ref",
    "cr13_next_required_step",
    "cr13_question_need_observation_normalization_status_ref",
    "cr13_question_need_observation_normalization_ready",
    "cr13_question_need_observation_row_count",
    "cr13_p8_material_candidate_case_count",
    "cr14_schema_version",
    "cr14_material_ref",
    "cr14_next_required_step",
    "cr14_rating_question_consistency_guard_status_ref",
    "cr14_rating_question_consistency_guard_evaluated",
    "cr14_rating_question_consistency_guard_passed",
    "cr14_consistency_issue_row_count",
    "cr17_schema_version",
    "cr17_material_ref",
    "cr17_next_required_step",
    "cr17_p5_decision_ref",
    "cr17_p5_confirmed_candidate",
    "cr17_p5_confirmed_candidate_only",
    "cr17_p5_decision_candidate_separation_ready",
    *P7_R54_AHR_CR_CURRENT_RECEIVED_BASIS_FIELD_REFS,
    *P7_R54_AHR_CR_HISTORICAL_BASIS_FIELD_REFS,
    "p8_material_candidate_only_handoff_status_ref",
    "p8_material_candidate_only_handoff_allowed_status_refs",
    "p8_material_candidate_only_handoff_ready",
    "p8_material_candidate_only_handoff_materialized",
    "p8_material_candidate_only_handoff_reason_refs",
    "p8_material_candidate_only_handoff_step_blocker_refs",
    "p8_material_candidate_only_handoff_step_blocker_ref_count",
    "p8_material_candidate_only",
    "p8_material_candidate_rows",
    "p8_material_candidate_row_count",
    "p8_material_candidate_case_refs",
    "p8_material_candidate_case_ref_count",
    "p8_material_candidate_case_refs_unique",
    "p8_material_candidate_row_allowed_key_refs",
    "p8_material_candidate_row_required_field_refs",
    "p8_candidate_rows_bodyfree_only",
    "p8_candidate_rows_have_no_question_text",
    "p8_candidate_rows_have_only_allowed_keys",
    "p8_candidate_rows_from_actual_review_question_observations",
    "plus_single_question_candidate_case_refs",
    "plus_single_question_candidate_case_count",
    "premium_deep_dive_candidate_case_refs",
    "premium_deep_dive_candidate_case_count",
    "question_may_reduce_overread_risk_case_refs",
    "question_may_reduce_overread_risk_case_count",
    "no_p8_material_candidate_reason_ref",
    "p8_question_text_generation",
    "p8_question_api_implemented",
    "p8_question_db_schema_implemented",
    "p8_question_rn_ui_implemented",
    "p8_question_trigger_logic_implemented",
    "p8_question_answer_persistence_implemented",
    "p8_implementation_storage_created_here",
    "p8_question_implementation_spec_finalized_here",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "p8_material_candidate_only_is_not_p8_start_allowed",
    "p5_repair_required_not_promoted_to_p8_material_candidate",
    "p5_confirmed_candidate_not_promoted_to_final",
    "p5_finalization_remains_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "r52_actual_execution_blocked_here",
    "actual_human_review_complete",
    "actual_review_evidence_complete",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_human_review_operation_run",
    "p5_human_blind_qa_confirmed_final",
    "p5_confirmed_final",
    "p5_final_allowed",
    "p6_limited_human_readfeel_start_allowed",
    "p6_start_allowed",
    "p8_start_allowed",
    "r52_reintake_execution_requested_here",
    "actual_r52_reintake_execution_confirmed",
    "p7_complete",
    "release_allowed",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CR_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CR_FALSE_FLAG_REFS,
)
P7_R54_AHR_CR_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CR19_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_REQUIRED_FIELD_REFS
)


def build_p7_r54_ahr_cr18_p6_candidate_only_handoff(
    *,
    p5_decision_candidate_repair_separation: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build CR18 body-free P6 candidate-only handoff material."""

    cr17 = dict(
        p5_decision_candidate_repair_separation
        or build_p7_r54_ahr_cr17_p5_decision_candidate_repair_separation()
    )
    assert_p7_r54_ahr_cr17_p5_decision_candidate_repair_separation_contract(cr17)
    session_id = _safe_review_session_id(review_session_id or cr17.get("review_session_id"))
    cr17_ready = cr17.get("p5_decision_candidate_separation_ready") is True
    p5_confirmed_candidate = (
        cr17.get("p5_decision_ref") == P7_R54_AHR_CR17_P5_CONFIRMED_CANDIDATE_REF
        and cr17.get("p5_confirmed_candidate") is True
        and cr17.get("p5_confirmed_candidate_only") is True
        and cr17.get("p5_decision_candidate_ready_for_r52_handoff") is True
    )
    repair_or_blocker_case_count = int(cr17.get("repair_or_blocker_case_count") or 0)
    blockers: list[str] = []
    if not cr17_ready:
        blockers.append(P7_R54_AHR_CR18_CR17_NOT_READY_BLOCKER_REF)
    if cr17.get("next_required_step") != P7_R54_AHR_CR18_STEP_REF:
        blockers.append(P7_R54_AHR_CR18_CR17_NEXT_STEP_NOT_CR18_BLOCKER_REF)
    if not p5_confirmed_candidate:
        blockers.append(P7_R54_AHR_CR18_P5_CONFIRMED_CANDIDATE_NOT_PRESENT_BLOCKER_REF)
    if repair_or_blocker_case_count:
        blockers.append(P7_R54_AHR_CR18_REPAIR_OR_BLOCKER_PRESENT_BLOCKER_REF)
    blockers = _dedupe_string_refs(blockers, limit=20, max_length=180)
    ready = not blockers
    evidence_ready = bool(cr17.get("actual_review_evidence_complete") is True and cr17.get("actual_human_review_complete") is True)
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CR18_P6_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CR_STEP,
        "scope": P7_R54_AHR_CR_SCOPE,
        "policy_kind": P7_R54_AHR_CR_POLICY_KIND,
        "policy_section": P7_R54_AHR_CR18_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CR18_STEP_REF,
        "current_phase": P7_R54_AHR_CR_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cr18_p6_candidate_only_handoff_20260628",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cr17_schema_version": cr17.get("schema_version"),
        "cr17_material_ref": cr17.get("material_id"),
        "cr17_next_required_step": cr17.get("next_required_step"),
        "cr17_p5_decision_candidate_separation_status_ref": cr17.get("p5_decision_candidate_separation_status_ref"),
        "cr17_p5_decision_candidate_separation_ready": cr17.get("p5_decision_candidate_separation_ready"),
        "cr17_p5_decision_ref": cr17.get("p5_decision_ref"),
        "cr17_p5_confirmed_candidate": cr17.get("p5_confirmed_candidate"),
        "cr17_p5_confirmed_candidate_only": cr17.get("p5_confirmed_candidate_only"),
        "cr17_p5_decision_candidate_ready_for_r52_handoff": cr17.get("p5_decision_candidate_ready_for_r52_handoff"),
        "cr17_repair_or_blocker_case_count": repair_or_blocker_case_count,
        "cr17_p5_repair_required_case_count": cr17.get("p5_repair_required_case_count"),
        "cr17_p4_current_only_repair_required_case_count": cr17.get("p4_current_only_repair_required_case_count"),
        "cr17_operation_blocked_case_count": cr17.get("operation_blocked_case_count"),
        "cr17_inconclusive_insufficient_material_case_count": cr17.get("inconclusive_insufficient_material_case_count"),
        "cr17_p8_material_candidate_case_count": cr17.get("p8_material_candidate_case_count"),
        **_current_received_basis_fields(actual_basis=True),
        **_historical_basis_fields(),
        "p6_candidate_only_handoff_status_ref": P7_R54_AHR_CR18_READY_STATUS_REF if ready else P7_R54_AHR_CR18_BLOCKED_STATUS_REF,
        "p6_candidate_only_handoff_allowed_status_refs": list(P7_R54_AHR_CR18_ALLOWED_STATUS_REFS),
        "p6_candidate_only_handoff_ready": ready,
        "p6_candidate_only_handoff_materialized": ready,
        "p6_candidate_only_handoff_reason_refs": [P7_R54_AHR_CR18_READY_REASON_REF] if ready else [],
        "p6_candidate_only_handoff_step_blocker_refs": blockers,
        "p6_candidate_only_handoff_step_blocker_ref_count": len(blockers),
        "p6_candidate_ref": P7_R54_AHR_CR18_P6_CANDIDATE_REF if ready else "",
        "p6_candidate_boundary_refs": list(P7_R54_AHR_CR18_P6_CANDIDATE_BOUNDARY_REFS),
        "p6_candidate_boundary_ref_count": len(P7_R54_AHR_CR18_P6_CANDIDATE_BOUNDARY_REFS),
        "p6_limited_human_readfeel_candidate_only": ready,
        "p6_limited_human_readfeel_candidate_materialized": ready,
        "p6_candidate_only_is_not_p6_start_allowed": True,
        "p6_start_remains_blocked_here": True,
        "p5_confirmed_candidate": ready,
        "p5_confirmed_candidate_only": ready,
        "p5_confirmed_candidate_is_not_p5_final": True,
        "p5_finalization_remains_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "r52_actual_execution_blocked_here": True,
        "p8_material_candidate_only_is_not_p8_start_allowed": True,
        "p5_confirmed_candidate_not_promoted_to_final": True,
        "actual_human_review_complete": evidence_ready,
        "actual_review_evidence_complete": evidence_ready,
        "actual_rating_rows_materialized_here": evidence_ready,
        "actual_question_need_observation_rows_materialized_here": evidence_ready,
        "actual_disposal_receipt_materialized_here": evidence_ready,
        "disposal_verified": evidence_ready,
        "actual_human_review_executed_by_person": evidence_ready,
        "actual_human_review_run_here": False,
        "actual_human_review_operation_run": False,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "p8_question_implementation_spec_finalized_here": False,
        "p5_human_blind_qa_confirmed_final": False,
        "p5_confirmed_final": False,
        "p5_final_allowed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_start_allowed": False,
        "p8_start_allowed": False,
        "r52_reintake_execution_requested_here": False,
        "actual_r52_reintake_execution_confirmed": False,
        "p7_complete": False,
        "release_allowed": False,
        "implemented_steps": list(P7_R54_AHR_CR18_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CR17_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_CR18_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CR17_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_CR19_STEP_REF if ready else P7_R54_AHR_CR18_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    for flag_ref in P7_R54_AHR_CR18_ALLOWED_TRUE_OPERATION_FLAG_REFS:
        material[flag_ref] = evidence_ready
    return material


def _cr19_plus_or_premium_candidate_ref(row: Mapping[str, Any]) -> str:
    primary_class = clean_identifier(row.get("question_need_primary_class"), default="", max_length=160)
    if primary_class == "plus_single_question_candidate_later" or row.get("plus_single_question_candidate_later") is True:
        return P7_R54_AHR_CR19_PLUS_CANDIDATE_REF
    if primary_class == "premium_deep_dive_candidate_later" or row.get("premium_deep_dive_candidate_later") is True:
        return P7_R54_AHR_CR19_PREMIUM_CANDIDATE_REF
    return P7_R54_AHR_CR19_OVERREAD_RISK_ONLY_CANDIDATE_REF


def _cr19_candidate_row_from_question_observation(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "case_ref_id": clean_identifier(row.get("case_ref_id"), default="", max_length=120),
        "blind_case_id": clean_identifier(row.get("blind_case_id"), default="", max_length=120),
        "question_need_primary_class": clean_identifier(row.get("question_need_primary_class"), default="", max_length=160),
        "one_question_fit_ref": clean_identifier(row.get("one_question_fit_ref"), default="", max_length=160),
        "p8_candidate_reason_ref": clean_identifier(
            row.get("p8_material_candidate_reason_ref"), default="p8_material_candidate_bodyfree_only", max_length=180
        ),
        "plus_or_premium_candidate_ref": _cr19_plus_or_premium_candidate_ref(row),
        "body_free": True,
    }


def _cr19_candidate_row_is_valid(row: Mapping[str, Any]) -> bool:
    if set(row) != set(P7_R54_AHR_CR19_ALLOWED_CANDIDATE_ROW_KEY_REFS):
        return False
    if row.get("body_free") is not True:
        return False
    for key in ("case_ref_id", "blind_case_id", "question_need_primary_class", "one_question_fit_ref", "p8_candidate_reason_ref", "plus_or_premium_candidate_ref"):
        if not isinstance(row.get(key), str) or not row.get(key):
            return False
    return not _contains_forbidden_body_or_question_key(row)


def build_p7_r54_ahr_cr19_p8_material_candidate_only_handoff(
    *,
    question_need_observation_normalization: Mapping[str, Any] | None = None,
    rating_question_consistency_guard: Mapping[str, Any] | None = None,
    p5_decision_candidate_repair_separation: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build CR19 body-free P8 material candidate-only handoff material."""

    cr13 = dict(question_need_observation_normalization or build_p7_r54_ahr_cr13_question_need_observation_normalization())
    cr14 = dict(rating_question_consistency_guard or build_p7_r54_ahr_cr14_rating_question_consistency_guard())
    cr17 = dict(
        p5_decision_candidate_repair_separation
        or build_p7_r54_ahr_cr17_p5_decision_candidate_repair_separation()
    )
    assert_p7_r54_ahr_cr13_question_need_observation_normalization_contract(cr13)
    assert_p7_r54_ahr_cr14_rating_question_consistency_guard_contract(cr14)
    assert_p7_r54_ahr_cr17_p5_decision_candidate_repair_separation_contract(cr17)
    session_id = _safe_review_session_id(
        review_session_id or cr17.get("review_session_id") or cr13.get("review_session_id") or cr14.get("review_session_id")
    )
    source_rows_raw = cr13.get("question_need_observation_rows") or []
    source_rows = [dict(row) for row in source_rows_raw if isinstance(row, Mapping)]
    step_blockers: list[str] = []
    if cr13.get("question_need_observation_normalization_ready") is not True:
        step_blockers.append(P7_R54_AHR_CR19_CR13_NOT_READY_BLOCKER_REF)
    if cr14.get("rating_question_consistency_guard_passed") is not True:
        step_blockers.append(P7_R54_AHR_CR19_CR14_NOT_PASSED_BLOCKER_REF)
    if not (
        cr17.get("p5_decision_ref") == P7_R54_AHR_CR17_P5_CONFIRMED_CANDIDATE_REF
        and cr17.get("p5_confirmed_candidate") is True
        and cr17.get("p5_confirmed_candidate_only") is True
    ):
        step_blockers.append(P7_R54_AHR_CR19_CR17_P5_CANDIDATE_NOT_CONFIRMED_BLOCKER_REF)
    if cr13.get("next_required_step") != P7_R54_AHR_CR14_STEP_REF:
        step_blockers.append(P7_R54_AHR_CR19_CR13_NEXT_STEP_NOT_CR14_BLOCKER_REF)
    if cr14.get("next_required_step") != P7_R54_AHR_CR15_STEP_REF:
        step_blockers.append(P7_R54_AHR_CR19_CR14_NEXT_STEP_NOT_CR15_BLOCKER_REF)
    if cr17.get("next_required_step") != P7_R54_AHR_CR18_STEP_REF:
        step_blockers.append(P7_R54_AHR_CR19_CR17_NEXT_STEP_NOT_CR18_BLOCKER_REF)
    if cr13.get("question_need_observation_row_count") != P7_R54_AHR_CR_REQUIRED_CASE_COUNT or len(source_rows) != P7_R54_AHR_CR_REQUIRED_CASE_COUNT:
        step_blockers.append(P7_R54_AHR_CR19_SOURCE_ROW_COUNT_NOT_24_BLOCKER_REF)
    if _contains_forbidden_body_or_question_key(source_rows):
        step_blockers.append(P7_R54_AHR_CR19_SOURCE_ROW_FORBIDDEN_KEY_BLOCKER_REF)
    candidate_rows = [
        _cr19_candidate_row_from_question_observation(row)
        for row in source_rows
        if row.get("p8_design_material_candidate") is True
    ]
    if any(not _cr19_candidate_row_is_valid(row) for row in candidate_rows):
        step_blockers.append(P7_R54_AHR_CR19_CANDIDATE_ROW_INVALID_BLOCKER_REF)
    step_blockers = _dedupe_string_refs(step_blockers, limit=50, max_length=200)
    ready = not step_blockers
    rows_for_output = candidate_rows if ready else []
    case_refs = [str(row.get("case_ref_id")) for row in rows_for_output]
    plus_refs = [str(row.get("case_ref_id")) for row in rows_for_output if row.get("plus_or_premium_candidate_ref") == P7_R54_AHR_CR19_PLUS_CANDIDATE_REF]
    premium_refs = [str(row.get("case_ref_id")) for row in rows_for_output if row.get("plus_or_premium_candidate_ref") == P7_R54_AHR_CR19_PREMIUM_CANDIDATE_REF]
    overread_refs = [str(row.get("case_ref_id")) for row in rows_for_output if row.get("plus_or_premium_candidate_ref") == P7_R54_AHR_CR19_OVERREAD_RISK_ONLY_CANDIDATE_REF]
    evidence_ready = bool(cr17.get("actual_review_evidence_complete") is True and cr17.get("actual_human_review_complete") is True)
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CR19_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CR_STEP,
        "scope": P7_R54_AHR_CR_SCOPE,
        "policy_kind": P7_R54_AHR_CR_POLICY_KIND,
        "policy_section": P7_R54_AHR_CR19_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CR19_STEP_REF,
        "current_phase": P7_R54_AHR_CR_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cr19_p8_material_candidate_only_handoff_20260628",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cr13_schema_version": cr13.get("schema_version"),
        "cr13_material_ref": cr13.get("material_id"),
        "cr13_next_required_step": cr13.get("next_required_step"),
        "cr13_question_need_observation_normalization_status_ref": cr13.get("question_need_observation_normalization_status_ref"),
        "cr13_question_need_observation_normalization_ready": cr13.get("question_need_observation_normalization_ready"),
        "cr13_question_need_observation_row_count": cr13.get("question_need_observation_row_count"),
        "cr13_p8_material_candidate_case_count": cr13.get("p8_material_candidate_case_count"),
        "cr14_schema_version": cr14.get("schema_version"),
        "cr14_material_ref": cr14.get("material_id"),
        "cr14_next_required_step": cr14.get("next_required_step"),
        "cr14_rating_question_consistency_guard_status_ref": cr14.get("rating_question_consistency_guard_status_ref"),
        "cr14_rating_question_consistency_guard_evaluated": cr14.get("rating_question_consistency_guard_evaluated"),
        "cr14_rating_question_consistency_guard_passed": cr14.get("rating_question_consistency_guard_passed"),
        "cr14_consistency_issue_row_count": cr14.get("consistency_issue_row_count"),
        "cr17_schema_version": cr17.get("schema_version"),
        "cr17_material_ref": cr17.get("material_id"),
        "cr17_next_required_step": cr17.get("next_required_step"),
        "cr17_p5_decision_ref": cr17.get("p5_decision_ref"),
        "cr17_p5_confirmed_candidate": cr17.get("p5_confirmed_candidate"),
        "cr17_p5_confirmed_candidate_only": cr17.get("p5_confirmed_candidate_only"),
        "cr17_p5_decision_candidate_separation_ready": cr17.get("p5_decision_candidate_separation_ready"),
        **_current_received_basis_fields(actual_basis=True),
        **_historical_basis_fields(),
        "p8_material_candidate_only_handoff_status_ref": P7_R54_AHR_CR19_READY_STATUS_REF if ready else P7_R54_AHR_CR19_BLOCKED_STATUS_REF,
        "p8_material_candidate_only_handoff_allowed_status_refs": list(P7_R54_AHR_CR19_ALLOWED_STATUS_REFS),
        "p8_material_candidate_only_handoff_ready": ready,
        "p8_material_candidate_only_handoff_materialized": ready,
        "p8_material_candidate_only_handoff_reason_refs": [P7_R54_AHR_CR19_READY_REASON_REF] if ready else [],
        "p8_material_candidate_only_handoff_step_blocker_refs": step_blockers,
        "p8_material_candidate_only_handoff_step_blocker_ref_count": len(step_blockers),
        "p8_material_candidate_only": bool(rows_for_output),
        "p8_material_candidate_rows": rows_for_output,
        "p8_material_candidate_row_count": len(rows_for_output),
        "p8_material_candidate_case_refs": case_refs,
        "p8_material_candidate_case_ref_count": len(case_refs),
        "p8_material_candidate_case_refs_unique": len(case_refs) == len(set(case_refs)),
        "p8_material_candidate_row_allowed_key_refs": sorted(P7_R54_AHR_CR19_ALLOWED_CANDIDATE_ROW_KEY_REFS),
        "p8_material_candidate_row_required_field_refs": list(P7_R54_AHR_CR19_P8_CANDIDATE_ROW_REQUIRED_FIELD_REFS),
        "p8_candidate_rows_bodyfree_only": bool(ready),
        "p8_candidate_rows_have_no_question_text": bool(ready),
        "p8_candidate_rows_have_only_allowed_keys": all(set(row) == set(P7_R54_AHR_CR19_ALLOWED_CANDIDATE_ROW_KEY_REFS) for row in rows_for_output) if ready else False,
        "p8_candidate_rows_from_actual_review_question_observations": bool(ready),
        "plus_single_question_candidate_case_refs": plus_refs,
        "plus_single_question_candidate_case_count": len(plus_refs),
        "premium_deep_dive_candidate_case_refs": premium_refs,
        "premium_deep_dive_candidate_case_count": len(premium_refs),
        "question_may_reduce_overread_risk_case_refs": overread_refs,
        "question_may_reduce_overread_risk_case_count": len(overread_refs),
        "no_p8_material_candidate_reason_ref": "" if rows_for_output else P7_R54_AHR_CR19_NO_P8_MATERIAL_CANDIDATE_REF,
        "p8_question_text_generation": False,
        "p8_question_api_implemented": False,
        "p8_question_db_schema_implemented": False,
        "p8_question_rn_ui_implemented": False,
        "p8_question_trigger_logic_implemented": False,
        "p8_question_answer_persistence_implemented": False,
        "p8_implementation_storage_created_here": False,
        "p8_question_implementation_spec_finalized_here": False,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "p8_material_candidate_only_is_not_p8_start_allowed": True,
        "p5_repair_required_not_promoted_to_p8_material_candidate": True,
        "p5_confirmed_candidate_not_promoted_to_final": True,
        "p5_finalization_remains_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "r52_actual_execution_blocked_here": True,
        "actual_human_review_complete": evidence_ready,
        "actual_review_evidence_complete": evidence_ready,
        "actual_rating_rows_materialized_here": evidence_ready,
        "actual_question_need_observation_rows_materialized_here": evidence_ready,
        "actual_disposal_receipt_materialized_here": evidence_ready,
        "disposal_verified": evidence_ready,
        "actual_human_review_executed_by_person": evidence_ready,
        "actual_human_review_run_here": False,
        "actual_human_review_operation_run": False,
        "p5_human_blind_qa_confirmed_final": False,
        "p5_confirmed_final": False,
        "p5_final_allowed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_start_allowed": False,
        "p8_start_allowed": False,
        "r52_reintake_execution_requested_here": False,
        "actual_r52_reintake_execution_confirmed": False,
        "p7_complete": False,
        "release_allowed": False,
        "implemented_steps": list(P7_R54_AHR_CR19_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CR18_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_CR19_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CR18_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_CR20_STEP_REF if ready else P7_R54_AHR_CR19_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    for flag_ref in P7_R54_AHR_CR19_ALLOWED_TRUE_OPERATION_FLAG_REFS:
        material[flag_ref] = evidence_ready
    material["p8_question_implementation_spec_finalized_here"] = False
    material["question_text_materialized_here"] = False
    material["draft_question_text_materialized_here"] = False
    return material


def assert_p7_r54_ahr_cr18_p6_candidate_only_handoff_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CR18_P6_CANDIDATE_ONLY_HANDOFF_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CR18 P6 candidate handoff",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CR18_P6_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CR18_STEP_REF,
        operation_step_ref=P7_R54_AHR_CR18_STEP_REF,
        source="P7-R54-AHR-CR18 P6 candidate handoff",
        allowed_true_false_flag_refs=P7_R54_AHR_CR18_ALLOWED_TRUE_OPERATION_FLAG_REFS,
    )
    _assert_current_received_basis_fields(data, actual_basis=True, source="P7-R54-AHR-CR18 P6 candidate handoff")
    _assert_historical_basis_fields(data, source="P7-R54-AHR-CR18 P6 candidate handoff")
    if data.get("cr17_schema_version") != P7_R54_AHR_CR17_P5_DECISION_CANDIDATE_REPAIR_SEPARATION_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CR18 CR17 schema changed")
    if tuple(data.get("p6_candidate_only_handoff_allowed_status_refs") or ()) != P7_R54_AHR_CR18_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-CR18 allowed status refs changed")
    blockers = list(data.get("p6_candidate_only_handoff_step_blocker_refs") or [])
    if data.get("p6_candidate_only_handoff_step_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-CR18 blocker count changed")
    ready = (
        data.get("cr17_p5_decision_candidate_separation_ready") is True
        and data.get("cr17_p5_decision_ref") == P7_R54_AHR_CR17_P5_CONFIRMED_CANDIDATE_REF
        and data.get("cr17_p5_confirmed_candidate") is True
        and data.get("cr17_p5_confirmed_candidate_only") is True
        and data.get("cr17_p5_decision_candidate_ready_for_r52_handoff") is True
        and int(data.get("cr17_repair_or_blocker_case_count") or 0) == 0
        and data.get("cr17_next_required_step") == P7_R54_AHR_CR18_STEP_REF
    )
    if data.get("p6_candidate_only_handoff_ready") is not ready:
        raise ValueError("P7-R54-AHR-CR18 ready flag changed")
    if data.get("p6_candidate_only_is_not_p6_start_allowed") is not True or data.get("p6_start_remains_blocked_here") is not True:
        raise ValueError("P7-R54-AHR-CR18 P6 candidate boundary changed")
    _assert_false_fields(
        data,
        keys=(
            "actual_human_review_run_here",
            "actual_human_review_operation_run",
            "question_text_materialized_here",
            "draft_question_text_materialized_here",
            "p8_question_implementation_spec_finalized_here",
            "p5_human_blind_qa_confirmed_final",
            "p5_confirmed_final",
            "p5_final_allowed",
            "p6_limited_human_readfeel_start_allowed",
            "p6_start_allowed",
            "p8_start_allowed",
            "r52_reintake_execution_requested_here",
            "actual_r52_reintake_execution_confirmed",
            "p7_complete",
            "release_allowed",
        ),
        source="P7-R54-AHR-CR18 false promotions",
    )
    if ready:
        if data.get("p6_candidate_only_handoff_status_ref") != P7_R54_AHR_CR18_READY_STATUS_REF:
            raise ValueError("P7-R54-AHR-CR18 ready status changed")
        if data.get("p6_candidate_only_handoff_reason_refs") != [P7_R54_AHR_CR18_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-CR18 ready reason changed")
        if blockers:
            raise ValueError("P7-R54-AHR-CR18 ready material cannot carry blockers")
        _assert_true_fields(
            data,
            keys=(
                "p6_candidate_only_handoff_materialized",
                "p6_limited_human_readfeel_candidate_only",
                "p6_limited_human_readfeel_candidate_materialized",
                "p5_confirmed_candidate",
                "p5_confirmed_candidate_only",
                "p5_confirmed_candidate_is_not_p5_final",
            ),
            source="P7-R54-AHR-CR18 ready candidate",
        )
        if data.get("p6_candidate_ref") != P7_R54_AHR_CR18_P6_CANDIDATE_REF:
            raise ValueError("P7-R54-AHR-CR18 candidate ref changed")
        if tuple(data.get("p6_candidate_boundary_refs") or ()) != P7_R54_AHR_CR18_P6_CANDIDATE_BOUNDARY_REFS:
            raise ValueError("P7-R54-AHR-CR18 boundary refs changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CR18_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CR18 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CR18_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CR18 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_CR19_STEP_REF:
            raise ValueError("P7-R54-AHR-CR18 ready next step changed")
    else:
        if data.get("p6_candidate_only_handoff_status_ref") != P7_R54_AHR_CR18_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-CR18 blocked status changed")
        if not blockers:
            raise ValueError("P7-R54-AHR-CR18 blocked material must carry blockers")
        _assert_false_fields(
            data,
            keys=(
                "p6_candidate_only_handoff_materialized",
                "p6_limited_human_readfeel_candidate_only",
                "p6_limited_human_readfeel_candidate_materialized",
                "p5_confirmed_candidate",
                "p5_confirmed_candidate_only",
            ),
            source="P7-R54-AHR-CR18 blocked candidate",
        )
        if data.get("p6_candidate_ref") != "":
            raise ValueError("P7-R54-AHR-CR18 blocked material cannot carry candidate ref")
        if data.get("next_required_step") != P7_R54_AHR_CR18_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CR18 blocked next step changed")
    return True


def assert_p7_r54_ahr_cr19_p8_material_candidate_only_handoff_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CR19_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CR19 P8 material handoff",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CR19_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CR19_STEP_REF,
        operation_step_ref=P7_R54_AHR_CR19_STEP_REF,
        source="P7-R54-AHR-CR19 P8 material handoff",
        allowed_true_false_flag_refs=P7_R54_AHR_CR19_ALLOWED_TRUE_OPERATION_FLAG_REFS,
    )
    _assert_current_received_basis_fields(data, actual_basis=True, source="P7-R54-AHR-CR19 P8 material handoff")
    _assert_historical_basis_fields(data, source="P7-R54-AHR-CR19 P8 material handoff")
    if data.get("cr13_schema_version") != P7_R54_AHR_CR13_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CR19 CR13 schema changed")
    if data.get("cr14_schema_version") != P7_R54_AHR_CR14_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CR19 CR14 schema changed")
    if data.get("cr17_schema_version") != P7_R54_AHR_CR17_P5_DECISION_CANDIDATE_REPAIR_SEPARATION_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CR19 CR17 schema changed")
    if tuple(data.get("p8_material_candidate_only_handoff_allowed_status_refs") or ()) != P7_R54_AHR_CR19_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-CR19 allowed status refs changed")
    blockers = list(data.get("p8_material_candidate_only_handoff_step_blocker_refs") or [])
    if data.get("p8_material_candidate_only_handoff_step_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-CR19 blocker count changed")
    ready = (
        data.get("cr13_question_need_observation_normalization_ready") is True
        and data.get("cr13_question_need_observation_row_count") == P7_R54_AHR_CR_REQUIRED_CASE_COUNT
        and data.get("cr13_next_required_step") == P7_R54_AHR_CR14_STEP_REF
        and data.get("cr14_rating_question_consistency_guard_evaluated") is True
        and data.get("cr14_rating_question_consistency_guard_passed") is True
        and data.get("cr14_consistency_issue_row_count") == 0
        and data.get("cr14_next_required_step") == P7_R54_AHR_CR15_STEP_REF
        and data.get("cr17_p5_decision_ref") == P7_R54_AHR_CR17_P5_CONFIRMED_CANDIDATE_REF
        and data.get("cr17_p5_confirmed_candidate") is True
        and data.get("cr17_p5_confirmed_candidate_only") is True
        and data.get("cr17_next_required_step") == P7_R54_AHR_CR18_STEP_REF
    )
    if data.get("p8_material_candidate_only_handoff_ready") is not ready:
        raise ValueError("P7-R54-AHR-CR19 ready flag changed")
    _assert_false_fields(
        data,
        keys=(
            "p8_question_text_generation",
            "p8_question_api_implemented",
            "p8_question_db_schema_implemented",
            "p8_question_rn_ui_implemented",
            "p8_question_trigger_logic_implemented",
            "p8_question_answer_persistence_implemented",
            "p8_implementation_storage_created_here",
            "p8_question_implementation_spec_finalized_here",
            "question_text_materialized_here",
            "draft_question_text_materialized_here",
            "actual_human_review_run_here",
            "actual_human_review_operation_run",
            "p5_human_blind_qa_confirmed_final",
            "p5_confirmed_final",
            "p5_final_allowed",
            "p6_limited_human_readfeel_start_allowed",
            "p6_start_allowed",
            "p8_start_allowed",
            "r52_reintake_execution_requested_here",
            "actual_r52_reintake_execution_confirmed",
            "p7_complete",
            "release_allowed",
        ),
        source="P7-R54-AHR-CR19 false promotions",
    )
    if data.get("p8_material_candidate_only_is_not_p8_start_allowed") is not True:
        raise ValueError("P7-R54-AHR-CR19 P8 boundary changed")
    rows = data.get("p8_material_candidate_rows") or []
    if ready:
        if data.get("p8_material_candidate_only_handoff_status_ref") != P7_R54_AHR_CR19_READY_STATUS_REF:
            raise ValueError("P7-R54-AHR-CR19 ready status changed")
        if data.get("p8_material_candidate_only_handoff_reason_refs") != [P7_R54_AHR_CR19_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-CR19 ready reason changed")
        if blockers:
            raise ValueError("P7-R54-AHR-CR19 ready material cannot carry blockers")
        _assert_true_fields(
            data,
            keys=(
                "p8_material_candidate_only_handoff_materialized",
                "p8_candidate_rows_bodyfree_only",
                "p8_candidate_rows_have_no_question_text",
                "p8_candidate_rows_have_only_allowed_keys",
                "p8_candidate_rows_from_actual_review_question_observations",
            ),
            source="P7-R54-AHR-CR19 ready candidate rows",
        )
        if data.get("p8_material_candidate_only") is not bool(rows):
            raise ValueError("P7-R54-AHR-CR19 candidate-only flag changed")
        if data.get("p8_material_candidate_row_count") != len(rows):
            raise ValueError("P7-R54-AHR-CR19 candidate row count changed")
        if data.get("p8_material_candidate_case_ref_count") != len(data.get("p8_material_candidate_case_refs") or []):
            raise ValueError("P7-R54-AHR-CR19 candidate case count changed")
        if set(data.get("p8_material_candidate_row_allowed_key_refs") or []) != set(P7_R54_AHR_CR19_ALLOWED_CANDIDATE_ROW_KEY_REFS):
            raise ValueError("P7-R54-AHR-CR19 allowed row keys changed")
        if tuple(data.get("p8_material_candidate_row_required_field_refs") or ()) != P7_R54_AHR_CR19_P8_CANDIDATE_ROW_REQUIRED_FIELD_REFS:
            raise ValueError("P7-R54-AHR-CR19 row required fields changed")
        for row in rows:
            if not isinstance(row, Mapping):
                raise ValueError("P7-R54-AHR-CR19 candidate row must be mapping")
            if set(row) != set(P7_R54_AHR_CR19_ALLOWED_CANDIDATE_ROW_KEY_REFS):
                raise ValueError("P7-R54-AHR-CR19 candidate row must use only allowed keys")
            if not _cr19_candidate_row_is_valid(row):
                raise ValueError("P7-R54-AHR-CR19 candidate row changed")
        if rows and data.get("no_p8_material_candidate_reason_ref"):
            raise ValueError("P7-R54-AHR-CR19 non-empty candidate rows cannot carry no-candidate reason")
        if not rows and data.get("no_p8_material_candidate_reason_ref") != P7_R54_AHR_CR19_NO_P8_MATERIAL_CANDIDATE_REF:
            raise ValueError("P7-R54-AHR-CR19 empty handoff must carry no-candidate reason")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CR19_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CR19 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CR19_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CR19 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_CR20_STEP_REF:
            raise ValueError("P7-R54-AHR-CR19 ready next step changed")
    else:
        if data.get("p8_material_candidate_only_handoff_status_ref") != P7_R54_AHR_CR19_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-CR19 blocked status changed")
        if not blockers:
            raise ValueError("P7-R54-AHR-CR19 blocked material must carry blockers")
        _assert_false_fields(
            data,
            keys=(
                "p8_material_candidate_only_handoff_materialized",
                "p8_material_candidate_only",
                "p8_candidate_rows_bodyfree_only",
                "p8_candidate_rows_have_no_question_text",
                "p8_candidate_rows_have_only_allowed_keys",
                "p8_candidate_rows_from_actual_review_question_observations",
            ),
            source="P7-R54-AHR-CR19 blocked candidate rows",
        )
        if data.get("p8_material_candidate_rows") != [] or data.get("p8_material_candidate_row_count") != 0:
            raise ValueError("P7-R54-AHR-CR19 blocked material must not carry candidate rows")
        if data.get("next_required_step") != P7_R54_AHR_CR19_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CR19 blocked next step changed")
    return True

# Alias names for CR16-CR19 design/documentation wording.
def build_p7_r54_ahr_current_received_actual_local_review_operation_post_review_summary_bodyfree(
    *,
    actual_local_human_review_operation_receipt: Mapping[str, Any] | None = None,
    sanitized_selection_only_result_rows_intake: Mapping[str, Any] | None = None,
    rating_row_normalization: Mapping[str, Any] | None = None,
    readfeel_execution_blocker_normalization: Mapping[str, Any] | None = None,
    question_need_observation_normalization: Mapping[str, Any] | None = None,
    rating_question_consistency_guard: Mapping[str, Any] | None = None,
    disposal_receipt: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_cr16_post_review_summary_evidence_complete_predicate(
        actual_local_human_review_operation_receipt=actual_local_human_review_operation_receipt,
        sanitized_selection_only_result_rows_intake=sanitized_selection_only_result_rows_intake,
        rating_row_normalization=rating_row_normalization,
        readfeel_execution_blocker_normalization=readfeel_execution_blocker_normalization,
        question_need_observation_normalization=question_need_observation_normalization,
        rating_question_consistency_guard=rating_question_consistency_guard,
        disposal_receipt=disposal_receipt,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_current_received_actual_local_review_operation_post_review_summary_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_cr16_post_review_summary_evidence_complete_predicate_contract(data)


def build_p7_r54_ahr_current_received_actual_local_review_operation_p5_decision_candidate_repair_separation_bodyfree(
    *,
    post_review_summary: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_cr17_p5_decision_candidate_repair_separation(
        post_review_summary=post_review_summary,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_current_received_actual_local_review_operation_p5_decision_candidate_repair_separation_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_cr17_p5_decision_candidate_repair_separation_contract(data)


def build_p7_r54_ahr_current_received_actual_local_review_operation_p6_candidate_only_handoff_bodyfree(
    *,
    p5_decision_candidate_repair_separation: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_cr18_p6_candidate_only_handoff(
        p5_decision_candidate_repair_separation=p5_decision_candidate_repair_separation,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_current_received_actual_local_review_operation_p6_candidate_only_handoff_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_cr18_p6_candidate_only_handoff_contract(data)


def build_p7_r54_ahr_current_received_actual_local_review_operation_p8_material_candidate_only_handoff_bodyfree(
    *,
    question_need_observation_normalization: Mapping[str, Any] | None = None,
    rating_question_consistency_guard: Mapping[str, Any] | None = None,
    p5_decision_candidate_repair_separation: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_cr19_p8_material_candidate_only_handoff(
        question_need_observation_normalization=question_need_observation_normalization,
        rating_question_consistency_guard=rating_question_consistency_guard,
        p5_decision_candidate_repair_separation=p5_decision_candidate_repair_separation,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_current_received_actual_local_review_operation_p8_material_candidate_only_handoff_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_cr19_p8_material_candidate_only_handoff_contract(data)



# R54-AHR-CR20 / R54-AHR-CR21: R52 handoff candidate envelope and final validation.
P7_R54_AHR_CR20_R52_HANDOFF_CANDIDATE_ENVELOPE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_received_actual_local_review_operation."
    "cr20_r52_handoff_candidate_envelope.bodyfree.v1"
)
P7_R54_AHR_CR21_FINAL_NO_BODY_NO_QUESTION_NO_TOUCH_VALIDATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_received_actual_local_review_operation."
    "cr21_final_no_body_leak_no_question_text_no_touch_validation.bodyfree.v1"
)
P7_R54_AHR_CR_R52_HANDOFF_CANDIDATE_ENVELOPE_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CR20_R52_HANDOFF_CANDIDATE_ENVELOPE_SCHEMA_VERSION
)
P7_R54_AHR_CR_FINAL_NO_BODY_NO_QUESTION_NO_TOUCH_VALIDATION_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CR21_FINAL_NO_BODY_NO_QUESTION_NO_TOUCH_VALIDATION_SCHEMA_VERSION
)

P7_R54_AHR_CR20_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR19_IMPLEMENTED_STEPS,
    P7_R54_AHR_CR20_STEP_REF,
)
P7_R54_AHR_CR20_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CR_STEP_REFS[21:]
P7_R54_AHR_CR21_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR20_IMPLEMENTED_STEPS,
    P7_R54_AHR_CR21_STEP_REF,
)
P7_R54_AHR_CR21_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CR_STEP_REFS[22:]

P7_R54_AHR_CR20_READY_STATUS_REF: Final = "CR20_R52_HANDOFF_CANDIDATE_ENVELOPE_MATERIALIZED_BODYFREE"
P7_R54_AHR_CR20_BLOCKED_STATUS_REF: Final = "CR20_R52_HANDOFF_CANDIDATE_ENVELOPE_BLOCKED"
P7_R54_AHR_CR20_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR20_READY_STATUS_REF,
    P7_R54_AHR_CR20_BLOCKED_STATUS_REF,
)
P7_R54_AHR_CR20_READY_REASON_REF: Final = (
    "CR20_CR16_CR17_CR18_CR19_READY_R52_HANDOFF_CANDIDATE_ENVELOPE_BODYFREE_ONLY"
)
P7_R54_AHR_CR20_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "cr16_cr17_cr18_cr19_ready_or_stop"
P7_R54_AHR_CR20_CR16_NOT_READY_BLOCKER_REF: Final = "cr16_actual_review_evidence_complete_not_ready"
P7_R54_AHR_CR20_CR17_NOT_READY_BLOCKER_REF: Final = "cr17_p5_confirmed_candidate_not_ready"
P7_R54_AHR_CR20_CR18_NOT_READY_BLOCKER_REF: Final = "cr18_p6_candidate_only_handoff_not_ready"
P7_R54_AHR_CR20_CR19_NOT_READY_BLOCKER_REF: Final = "cr19_p8_material_candidate_only_handoff_not_ready"
P7_R54_AHR_CR20_CR16_NEXT_STEP_NOT_CR17_BLOCKER_REF: Final = "cr16_next_step_not_cr17"
P7_R54_AHR_CR20_CR17_NEXT_STEP_NOT_CR18_BLOCKER_REF: Final = "cr17_next_step_not_cr18"
P7_R54_AHR_CR20_CR18_NEXT_STEP_NOT_CR19_BLOCKER_REF: Final = "cr18_next_step_not_cr19"
P7_R54_AHR_CR20_CR19_NEXT_STEP_NOT_CR20_BLOCKER_REF: Final = "cr19_next_step_not_cr20"
P7_R54_AHR_CR20_SOURCE_FORBIDDEN_KEY_BLOCKER_REF: Final = (
    "cr20_source_material_forbidden_body_question_path_hash_key"
)
P7_R54_AHR_CR20_R52_HANDOFF_CANDIDATE_REF: Final = "R52_REINTAKE_HANDOFF_CANDIDATE_ENVELOPE_BODYFREE_ONLY"
P7_R54_AHR_CR20_R52_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "R52_HANDOFF_CANDIDATE_ENVELOPE_IS_NOT_R52_REINTAKE_EXECUTED",
    "R52_REINTAKE_EXECUTION_ALLOWED_HERE_FALSE",
    "ACTUAL_R52_REINTAKE_EXECUTION_CONFIRMED_FALSE",
    "P5_CONFIRMED_CANDIDATE_IS_NOT_P5_FINAL",
    "P6_CANDIDATE_ONLY_IS_NOT_P6_START_ALLOWED",
    "P8_MATERIAL_CANDIDATE_ONLY_IS_NOT_P8_START_ALLOWED",
    "P7_COMPLETE_FALSE",
    "RELEASE_ALLOWED_FALSE",
)
P7_R54_AHR_CR20_ALLOWED_TRUE_OPERATION_FLAG_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR17_ALLOWED_TRUE_OPERATION_FLAG_REFS
)

P7_R54_AHR_CR21_PASSED_STATUS_REF: Final = "CR21_FINAL_NO_BODY_NO_QUESTION_NO_TOUCH_VALIDATION_PASSED_BODYFREE"
P7_R54_AHR_CR21_BLOCKED_STATUS_REF: Final = "CR21_FINAL_NO_BODY_NO_QUESTION_NO_TOUCH_VALIDATION_BLOCKED"
P7_R54_AHR_CR21_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR21_PASSED_STATUS_REF,
    P7_R54_AHR_CR21_BLOCKED_STATUS_REF,
)
P7_R54_AHR_CR21_READY_REASON_REF: Final = (
    "CR21_CR00_TO_CR20_BODYFREE_ARTIFACTS_NO_BODY_NO_QUESTION_NO_TOUCH_VALIDATED"
)
P7_R54_AHR_CR21_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "fix_no_body_no_question_no_touch_validation_or_stop"
P7_R54_AHR_CR21_CR20_NOT_READY_BLOCKER_REF: Final = "cr20_r52_handoff_candidate_envelope_not_ready"
P7_R54_AHR_CR21_MISSING_TARGET_BLOCKER_REF: Final = "cr21_validation_target_missing"
P7_R54_AHR_CR21_DUPLICATE_TARGET_BLOCKER_REF: Final = "cr21_validation_target_duplicate"
P7_R54_AHR_CR21_FORBIDDEN_KEY_BLOCKER_REF: Final = "cr21_forbidden_body_question_path_hash_key_detected"
P7_R54_AHR_CR21_BODY_OR_QUESTION_LEAK_BLOCKER_REF: Final = "cr21_body_or_question_leak_detected"
P7_R54_AHR_CR21_PATH_OR_HASH_LEAK_BLOCKER_REF: Final = "cr21_path_or_hash_leak_detected"
P7_R54_AHR_CR21_CONTRACT_MUTATION_BLOCKER_REF: Final = "cr21_no_touch_contract_mutation_detected"
P7_R54_AHR_CR21_ALLOWED_TRUE_OPERATION_FLAG_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR17_ALLOWED_TRUE_OPERATION_FLAG_REFS
)
P7_R54_AHR_CR21_VALIDATION_TARGET_STEP_REFS: Final[tuple[str, ...]] = P7_R54_AHR_CR_STEP_REFS[:21]
P7_R54_AHR_CR21_VALIDATION_TARGET_LABEL_REFS: Final[tuple[str, ...]] = (
    "CR00 scope",
    "CR01 basis",
    "CR02 historical separation",
    "CR03 impact",
    "CR04 manifest",
    "CR05 preflight",
    "CR06 request",
    "CR07 packet receipt scan",
    "CR08 reviewer form",
    "CR09 operation receipt",
    "CR10 sanitized rows",
    "CR11 rating rows",
    "CR12 blocker rows",
    "CR13 question observation rows",
    "CR14 consistency guard",
    "CR15 disposal receipt",
    "CR16 summary",
    "CR17 P5 decision",
    "CR18 P6 candidate",
    "CR19 P8 candidate",
    "CR20 R52 handoff envelope",
)
P7_R54_AHR_CR21_FORBIDDEN_BODY_OR_QUESTION_KEY_REFS: Final[frozenset[str]] = frozenset(
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
        "terminal_output_body",
        "stdout_body",
        "stderr_body",
        "traceback_body",
    }
)
P7_R54_AHR_CR21_FORBIDDEN_PATH_OR_HASH_KEY_REFS: Final[frozenset[str]] = frozenset(
    {
        "local_path",
        "local_absolute_path",
        "body_hash",
    }
)

P7_R54_AHR_CR20_R52_HANDOFF_CANDIDATE_ENVELOPE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR_BASE_REQUIRED_FIELD_REFS,
    "cr16_schema_version",
    "cr16_material_ref",
    "cr16_next_required_step",
    "cr16_post_review_summary_ready",
    "cr16_actual_review_evidence_complete",
    "cr16_actual_human_review_complete",
    "cr16_actual_human_review_executed_by_person",
    "cr16_rating_row_count",
    "cr16_question_need_observation_row_count",
    "cr16_disposal_verified",
    "cr16_no_body_leak_validation_passed",
    "cr16_no_question_text_validation_passed",
    "cr16_no_touch_validation_passed",
    "cr17_schema_version",
    "cr17_material_ref",
    "cr17_next_required_step",
    "cr17_p5_decision_candidate_separation_ready",
    "cr17_p5_decision_ref",
    "cr17_p5_confirmed_candidate",
    "cr17_p5_confirmed_candidate_only",
    "cr17_p5_decision_candidate_ready_for_r52_handoff",
    "cr17_repair_or_blocker_case_count",
    "cr18_schema_version",
    "cr18_material_ref",
    "cr18_next_required_step",
    "cr18_p6_candidate_only_handoff_ready",
    "cr18_p6_candidate_ref",
    "cr19_schema_version",
    "cr19_material_ref",
    "cr19_next_required_step",
    "cr19_p8_material_candidate_only_handoff_ready",
    "cr19_p8_material_candidate_row_count",
    "cr19_p8_material_candidate_case_refs",
    "cr19_p8_material_candidate_case_ref_count",
    *P7_R54_AHR_CR_CURRENT_RECEIVED_BASIS_FIELD_REFS,
    *P7_R54_AHR_CR_HISTORICAL_BASIS_FIELD_REFS,
    "r52_reintake_handoff_status_ref",
    "r52_reintake_handoff_allowed_status_refs",
    "r52_reintake_handoff_ready",
    "r52_reintake_handoff_envelope_materialized_here",
    "r52_reintake_handoff_reason_refs",
    "r52_reintake_handoff_step_blocker_refs",
    "r52_reintake_handoff_step_blocker_ref_count",
    "r52_handoff_candidate_ref",
    "r52_handoff_candidate_envelope_refs",
    "r52_handoff_candidate_envelope_ref_count",
    "r52_handoff_candidate_source_material_refs",
    "r52_handoff_candidate_source_material_ref_count",
    "r52_handoff_candidate_boundary_refs",
    "r52_handoff_candidate_boundary_ref_count",
    "r52_handoff_candidate_bodyfree_only",
    "r52_handoff_candidate_contains_no_question_text",
    "r52_handoff_candidate_contains_no_body_payload",
    "p5_confirmed_candidate",
    "p5_confirmed_candidate_only",
    "p5_confirmed_candidate_is_not_p5_final",
    "p6_candidate_only_handoff_ready",
    "p6_candidate_ref",
    "p6_candidate_only_is_not_p6_start_allowed",
    "p8_material_candidate_only_handoff_ready",
    "p8_material_candidate_case_refs",
    "p8_material_candidate_case_ref_count",
    "p8_material_candidate_only_is_not_p8_start_allowed",
    "actual_human_review_complete",
    "actual_review_evidence_complete",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_human_review_operation_run",
    "r52_reintake_execution_allowed_here",
    "r52_reintake_execution_started_here",
    "r52_reintake_execution_completed_here",
    "r52_reintake_execution_requested_here",
    "actual_r52_reintake_execution_confirmed",
    "p5_human_blind_qa_confirmed_final",
    "p5_confirmed_final",
    "p5_final_allowed",
    "p6_limited_human_readfeel_start_allowed",
    "p6_start_allowed",
    "p8_start_allowed",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "p8_question_implementation_spec_finalized_here",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_confirmed",
    "rn_contract_green_confirmed",
    "rn_real_device_modal_verified",
    "r52_handoff_ready_is_not_r52_reintake_executed",
    "p5_confirmed_candidate_not_promoted_to_final",
    "p6_p8_release_promotion_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CR_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CR_FALSE_FLAG_REFS,
)
P7_R54_AHR_CR_R52_HANDOFF_CANDIDATE_ENVELOPE_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CR20_R52_HANDOFF_CANDIDATE_ENVELOPE_REQUIRED_FIELD_REFS
)

P7_R54_AHR_CR21_FINAL_VALIDATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR_BASE_REQUIRED_FIELD_REFS,
    "cr20_schema_version",
    "cr20_material_ref",
    "cr20_next_required_step",
    "cr20_r52_reintake_handoff_ready",
    "cr20_r52_reintake_handoff_envelope_materialized_here",
    "cr20_actual_review_evidence_complete",
    *P7_R54_AHR_CR_CURRENT_RECEIVED_BASIS_FIELD_REFS,
    *P7_R54_AHR_CR_HISTORICAL_BASIS_FIELD_REFS,
    "final_validation_status_ref",
    "final_validation_allowed_status_refs",
    "final_validation_passed",
    "final_validation_reason_refs",
    "final_validation_step_blocker_refs",
    "final_validation_step_blocker_ref_count",
    "validation_target_step_refs",
    "validation_target_step_ref_count",
    "validation_target_label_refs",
    "validation_target_label_ref_count",
    "provided_material_step_refs",
    "provided_material_step_ref_count",
    "missing_validation_target_step_refs",
    "missing_validation_target_step_ref_count",
    "duplicate_validation_target_step_refs",
    "duplicate_validation_target_step_ref_count",
    "no_body_leak_validation_passed",
    "no_question_text_validation_passed",
    "no_touch_validation_passed",
    "forbidden_key_refs_detected",
    "forbidden_key_ref_count",
    "body_or_question_leak_refs",
    "body_or_question_leak_ref_count",
    "path_or_hash_leak_refs",
    "path_or_hash_leak_ref_count",
    "contract_mutation_refs",
    "contract_mutation_ref_count",
    "validated_material_refs",
    "validated_material_ref_count",
    "validated_materials_bodyfree_only",
    "validated_materials_have_no_forbidden_keys",
    "validated_materials_public_contract_unchanged",
    "validated_materials_no_touch_contract_unchanged",
    "validated_materials_body_free_markers_unchanged",
    "actual_human_review_complete",
    "actual_review_evidence_complete",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_human_review_operation_run",
    "r52_reintake_execution_allowed_here",
    "r52_reintake_execution_started_here",
    "r52_reintake_execution_completed_here",
    "r52_reintake_execution_requested_here",
    "actual_r52_reintake_execution_confirmed",
    "p5_human_blind_qa_confirmed_final",
    "p5_confirmed_final",
    "p5_final_allowed",
    "p6_limited_human_readfeel_start_allowed",
    "p6_start_allowed",
    "p8_start_allowed",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "p8_question_implementation_spec_finalized_here",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_confirmed",
    "rn_contract_green_confirmed",
    "rn_real_device_modal_verified",
    "r52_handoff_ready_is_not_r52_reintake_executed",
    "p5_confirmed_candidate_not_promoted_to_final",
    "p6_p8_release_promotion_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CR_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CR_FALSE_FLAG_REFS,
)
P7_R54_AHR_CR_FINAL_NO_BODY_NO_QUESTION_NO_TOUCH_VALIDATION_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CR21_FINAL_VALIDATION_REQUIRED_FIELD_REFS
)


def _cr20_ready_from_sources(
    cr16: Mapping[str, Any],
    cr17: Mapping[str, Any],
    cr18: Mapping[str, Any],
    cr19: Mapping[str, Any],
) -> tuple[bool, list[str]]:
    blockers: list[str] = []
    cr16_ready = (
        cr16.get("schema_version") == P7_R54_AHR_CR16_POST_REVIEW_SUMMARY_SCHEMA_VERSION
        and cr16.get("post_review_summary_ready") is True
        and cr16.get("actual_review_evidence_complete") is True
        and cr16.get("actual_human_review_complete") is True
        and cr16.get("actual_human_review_executed_by_person") is True
        and cr16.get("rating_row_count") == P7_R54_AHR_CR_REQUIRED_CASE_COUNT
        and cr16.get("question_need_observation_row_count") == P7_R54_AHR_CR_REQUIRED_CASE_COUNT
        and cr16.get("disposal_verified") is True
        and cr16.get("no_body_leak_validation_passed") is True
        and cr16.get("no_question_text_validation_passed") is True
        and cr16.get("no_touch_validation_passed") is True
    )
    if not cr16_ready:
        blockers.append(P7_R54_AHR_CR20_CR16_NOT_READY_BLOCKER_REF)
    if cr16.get("next_required_step") != P7_R54_AHR_CR17_STEP_REF:
        blockers.append(P7_R54_AHR_CR20_CR16_NEXT_STEP_NOT_CR17_BLOCKER_REF)
    cr17_ready = (
        cr17.get("schema_version") == P7_R54_AHR_CR17_P5_DECISION_CANDIDATE_REPAIR_SEPARATION_SCHEMA_VERSION
        and cr17.get("p5_decision_candidate_separation_ready") is True
        and cr17.get("p5_decision_ref") == P7_R54_AHR_CR17_P5_CONFIRMED_CANDIDATE_REF
        and cr17.get("p5_confirmed_candidate") is True
        and cr17.get("p5_confirmed_candidate_only") is True
        and cr17.get("p5_decision_candidate_ready_for_r52_handoff") is True
        and int(cr17.get("repair_or_blocker_case_count") or 0) == 0
    )
    if not cr17_ready:
        blockers.append(P7_R54_AHR_CR20_CR17_NOT_READY_BLOCKER_REF)
    if cr17.get("next_required_step") != P7_R54_AHR_CR18_STEP_REF:
        blockers.append(P7_R54_AHR_CR20_CR17_NEXT_STEP_NOT_CR18_BLOCKER_REF)
    cr18_ready = (
        cr18.get("schema_version") == P7_R54_AHR_CR18_P6_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION
        and cr18.get("p6_candidate_only_handoff_ready") is True
        and cr18.get("p6_candidate_only_handoff_materialized") is True
        and cr18.get("p6_limited_human_readfeel_candidate_only") is True
        and cr18.get("p6_start_allowed") is False
    )
    if not cr18_ready:
        blockers.append(P7_R54_AHR_CR20_CR18_NOT_READY_BLOCKER_REF)
    if cr18.get("next_required_step") != P7_R54_AHR_CR19_STEP_REF:
        blockers.append(P7_R54_AHR_CR20_CR18_NEXT_STEP_NOT_CR19_BLOCKER_REF)
    cr19_ready = (
        cr19.get("schema_version") == P7_R54_AHR_CR19_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION
        and cr19.get("p8_material_candidate_only_handoff_ready") is True
        and cr19.get("p8_material_candidate_only_handoff_materialized") is True
        and cr19.get("p8_start_allowed") is False
        and cr19.get("p8_question_text_generation") is False
        and cr19.get("question_text_materialized_here") is False
        and cr19.get("draft_question_text_materialized_here") is False
    )
    if not cr19_ready:
        blockers.append(P7_R54_AHR_CR20_CR19_NOT_READY_BLOCKER_REF)
    if cr19.get("next_required_step") != P7_R54_AHR_CR20_STEP_REF:
        blockers.append(P7_R54_AHR_CR20_CR19_NEXT_STEP_NOT_CR20_BLOCKER_REF)
    if _contains_forbidden_body_or_question_key((cr16, cr17, cr18, cr19)):
        blockers.append(P7_R54_AHR_CR20_SOURCE_FORBIDDEN_KEY_BLOCKER_REF)
    blockers = _dedupe_string_refs(blockers, limit=50, max_length=200)
    return not blockers, blockers


def build_p7_r54_ahr_cr20_r52_handoff_candidate_envelope(
    *,
    cr16_summary: Mapping[str, Any] | None = None,
    cr17_p5_decision: Mapping[str, Any] | None = None,
    cr18_p6_candidate: Mapping[str, Any] | None = None,
    cr19_p8_candidate: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build CR20 body-free R52 handoff candidate envelope without executing R52."""

    session_id = _safe_review_session_id(review_session_id)
    cr16 = cr16_summary if isinstance(cr16_summary, Mapping) else {}
    cr17 = cr17_p5_decision if isinstance(cr17_p5_decision, Mapping) else {}
    cr18 = cr18_p6_candidate if isinstance(cr18_p6_candidate, Mapping) else {}
    cr19 = cr19_p8_candidate if isinstance(cr19_p8_candidate, Mapping) else {}
    ready, blockers = _cr20_ready_from_sources(cr16, cr17, cr18, cr19)
    evidence_ready = bool(ready and cr16.get("actual_review_evidence_complete") is True)
    p8_case_refs = _dedupe_string_refs(cr19.get("p8_material_candidate_case_refs") or (), limit=24, max_length=120)
    source_material_refs = _dedupe_string_refs(
        [
            cr16.get("material_id"),
            cr17.get("material_id"),
            cr18.get("material_id"),
            cr19.get("material_id"),
        ],
        limit=10,
        max_length=180,
    )
    envelope_refs = _dedupe_string_refs(
        [
            cr16.get("material_id"),
            cr17.get("p5_decision_ref"),
            cr18.get("p6_candidate_ref"),
            P7_R54_AHR_CR19_NO_P8_MATERIAL_CANDIDATE_REF if not p8_case_refs else "p8_material_candidate_rows_bodyfree_only",
            P7_R54_AHR_CR20_R52_HANDOFF_CANDIDATE_REF,
        ],
        limit=20,
        max_length=180,
    )
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CR20_R52_HANDOFF_CANDIDATE_ENVELOPE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CR_STEP,
        "scope": P7_R54_AHR_CR_SCOPE,
        "policy_kind": P7_R54_AHR_CR_POLICY_KIND,
        "policy_section": P7_R54_AHR_CR20_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CR20_STEP_REF,
        "current_phase": P7_R54_AHR_CR_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cr20_r52_handoff_candidate_envelope_20260628",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cr16_schema_version": cr16.get("schema_version"),
        "cr16_material_ref": cr16.get("material_id"),
        "cr16_next_required_step": cr16.get("next_required_step"),
        "cr16_post_review_summary_ready": cr16.get("post_review_summary_ready") is True,
        "cr16_actual_review_evidence_complete": cr16.get("actual_review_evidence_complete") is True,
        "cr16_actual_human_review_complete": cr16.get("actual_human_review_complete") is True,
        "cr16_actual_human_review_executed_by_person": cr16.get("actual_human_review_executed_by_person") is True,
        "cr16_rating_row_count": int(cr16.get("rating_row_count") or 0) if cr16 else 0,
        "cr16_question_need_observation_row_count": int(cr16.get("question_need_observation_row_count") or 0) if cr16 else 0,
        "cr16_disposal_verified": cr16.get("disposal_verified") is True,
        "cr16_no_body_leak_validation_passed": cr16.get("no_body_leak_validation_passed") is True,
        "cr16_no_question_text_validation_passed": cr16.get("no_question_text_validation_passed") is True,
        "cr16_no_touch_validation_passed": cr16.get("no_touch_validation_passed") is True,
        "cr17_schema_version": cr17.get("schema_version"),
        "cr17_material_ref": cr17.get("material_id"),
        "cr17_next_required_step": cr17.get("next_required_step"),
        "cr17_p5_decision_candidate_separation_ready": cr17.get("p5_decision_candidate_separation_ready") is True,
        "cr17_p5_decision_ref": cr17.get("p5_decision_ref"),
        "cr17_p5_confirmed_candidate": cr17.get("p5_confirmed_candidate") is True,
        "cr17_p5_confirmed_candidate_only": cr17.get("p5_confirmed_candidate_only") is True,
        "cr17_p5_decision_candidate_ready_for_r52_handoff": cr17.get("p5_decision_candidate_ready_for_r52_handoff") is True,
        "cr17_repair_or_blocker_case_count": int(cr17.get("repair_or_blocker_case_count") or 0) if cr17 else 0,
        "cr18_schema_version": cr18.get("schema_version"),
        "cr18_material_ref": cr18.get("material_id"),
        "cr18_next_required_step": cr18.get("next_required_step"),
        "cr18_p6_candidate_only_handoff_ready": cr18.get("p6_candidate_only_handoff_ready") is True,
        "cr18_p6_candidate_ref": cr18.get("p6_candidate_ref") or "",
        "cr19_schema_version": cr19.get("schema_version"),
        "cr19_material_ref": cr19.get("material_id"),
        "cr19_next_required_step": cr19.get("next_required_step"),
        "cr19_p8_material_candidate_only_handoff_ready": cr19.get("p8_material_candidate_only_handoff_ready") is True,
        "cr19_p8_material_candidate_row_count": int(cr19.get("p8_material_candidate_row_count") or 0) if cr19 else 0,
        "cr19_p8_material_candidate_case_refs": p8_case_refs if ready else [],
        "cr19_p8_material_candidate_case_ref_count": len(p8_case_refs) if ready else 0,
        **_current_received_basis_fields(actual_basis=True),
        **_historical_basis_fields(),
        "r52_reintake_handoff_status_ref": P7_R54_AHR_CR20_READY_STATUS_REF if ready else P7_R54_AHR_CR20_BLOCKED_STATUS_REF,
        "r52_reintake_handoff_allowed_status_refs": list(P7_R54_AHR_CR20_ALLOWED_STATUS_REFS),
        "r52_reintake_handoff_ready": ready,
        "r52_reintake_handoff_envelope_materialized_here": ready,
        "r52_reintake_handoff_reason_refs": [P7_R54_AHR_CR20_READY_REASON_REF] if ready else [],
        "r52_reintake_handoff_step_blocker_refs": blockers,
        "r52_reintake_handoff_step_blocker_ref_count": len(blockers),
        "r52_handoff_candidate_ref": P7_R54_AHR_CR20_R52_HANDOFF_CANDIDATE_REF if ready else "",
        "r52_handoff_candidate_envelope_refs": envelope_refs if ready else [],
        "r52_handoff_candidate_envelope_ref_count": len(envelope_refs) if ready else 0,
        "r52_handoff_candidate_source_material_refs": source_material_refs if ready else [],
        "r52_handoff_candidate_source_material_ref_count": len(source_material_refs) if ready else 0,
        "r52_handoff_candidate_boundary_refs": list(P7_R54_AHR_CR20_R52_BOUNDARY_REFS),
        "r52_handoff_candidate_boundary_ref_count": len(P7_R54_AHR_CR20_R52_BOUNDARY_REFS),
        "r52_handoff_candidate_bodyfree_only": ready,
        "r52_handoff_candidate_contains_no_question_text": ready,
        "r52_handoff_candidate_contains_no_body_payload": ready,
        "p5_confirmed_candidate": ready,
        "p5_confirmed_candidate_only": ready,
        "p5_confirmed_candidate_is_not_p5_final": True,
        "p6_candidate_only_handoff_ready": ready,
        "p6_candidate_ref": cr18.get("p6_candidate_ref") if ready else "",
        "p6_candidate_only_is_not_p6_start_allowed": True,
        "p8_material_candidate_only_handoff_ready": ready,
        "p8_material_candidate_case_refs": p8_case_refs if ready else [],
        "p8_material_candidate_case_ref_count": len(p8_case_refs) if ready else 0,
        "p8_material_candidate_only_is_not_p8_start_allowed": True,
        "actual_human_review_complete": evidence_ready,
        "actual_review_evidence_complete": evidence_ready,
        "actual_rating_rows_materialized_here": evidence_ready,
        "actual_question_need_observation_rows_materialized_here": evidence_ready,
        "actual_disposal_receipt_materialized_here": evidence_ready,
        "disposal_verified": evidence_ready,
        "actual_human_review_executed_by_person": evidence_ready,
        "actual_human_review_run_here": False,
        "actual_human_review_operation_run": False,
        "r52_reintake_execution_allowed_here": False,
        "r52_reintake_execution_started_here": False,
        "r52_reintake_execution_completed_here": False,
        "r52_reintake_execution_requested_here": False,
        "actual_r52_reintake_execution_confirmed": False,
        "p5_human_blind_qa_confirmed_final": False,
        "p5_confirmed_final": False,
        "p5_final_allowed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_start_allowed": False,
        "p8_start_allowed": False,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "p8_question_implementation_spec_finalized_here": False,
        "p7_complete": False,
        "release_allowed": False,
        "full_backend_suite_green_confirmed": False,
        "rn_contract_green_confirmed": False,
        "rn_real_device_modal_verified": False,
        "r52_handoff_ready_is_not_r52_reintake_executed": True,
        "p5_confirmed_candidate_not_promoted_to_final": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR_CR20_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CR19_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_CR20_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CR19_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_CR21_STEP_REF if ready else P7_R54_AHR_CR20_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    for flag_ref in P7_R54_AHR_CR20_ALLOWED_TRUE_OPERATION_FLAG_REFS:
        material[flag_ref] = evidence_ready
    material["r52_reintake_execution_requested_here"] = False
    material["actual_r52_reintake_execution_confirmed"] = False
    material["p5_human_blind_qa_confirmed_final"] = False
    material["p5_confirmed_final"] = False
    material["p5_final_allowed"] = False
    material["p6_limited_human_readfeel_start_allowed"] = False
    material["p6_start_allowed"] = False
    material["p8_start_allowed"] = False
    material["p7_complete"] = False
    material["release_allowed"] = False
    material["question_text_materialized_here"] = False
    material["draft_question_text_materialized_here"] = False
    material["p8_question_implementation_spec_finalized_here"] = False
    return material


def _cr21_materials_tuple(materials: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None) -> tuple[Mapping[str, Any], ...]:
    if isinstance(materials, Mapping):
        return (materials,)
    if isinstance(materials, Sequence) and not isinstance(materials, (str, bytes, bytearray)):
        return tuple(material for material in materials if isinstance(material, Mapping))
    return ()


def _cr21_material_step_refs(materials: Sequence[Mapping[str, Any]]) -> list[str]:
    return _dedupe_string_refs(
        [material.get("operation_step_ref") for material in materials],
        limit=40,
        max_length=160,
    )


def _cr21_duplicate_step_refs(materials: Sequence[Mapping[str, Any]]) -> list[str]:
    seen: set[str] = set()
    dupes: list[str] = []
    for material in materials:
        ref = clean_identifier(material.get("operation_step_ref"), default="", max_length=160)
        if not ref:
            continue
        if ref in seen and ref not in dupes:
            dupes.append(ref)
        seen.add(ref)
    return dupes


def _cr21_collect_forbidden_refs(value: Any, *, prefix: str = "material") -> tuple[list[str], list[str], list[str]]:
    forbidden: list[str] = []
    body_or_question: list[str] = []
    path_or_hash: list[str] = []

    def visit(node: Any, path_ref: str) -> None:
        if isinstance(node, Mapping):
            for key, child in node.items():
                key_ref = str(key)
                child_path = f"{path_ref}.{key_ref}"
                if key_ref in P7_R54_AHR_CR21_FORBIDDEN_BODY_OR_QUESTION_KEY_REFS:
                    forbidden.append(child_path)
                    body_or_question.append(child_path)
                if key_ref in P7_R54_AHR_CR21_FORBIDDEN_PATH_OR_HASH_KEY_REFS:
                    forbidden.append(child_path)
                    path_or_hash.append(child_path)
                visit(child, child_path)
        elif isinstance(node, Sequence) and not isinstance(node, (str, bytes, bytearray)):
            for index, child in enumerate(node):
                visit(child, f"{path_ref}[{index}]")

    visit(value, prefix)
    return (
        _dedupe_string_refs(forbidden, limit=100, max_length=220),
        _dedupe_string_refs(body_or_question, limit=100, max_length=220),
        _dedupe_string_refs(path_or_hash, limit=100, max_length=220),
    )


def _cr21_contract_mutation_refs(materials: Sequence[Mapping[str, Any]]) -> list[str]:
    refs: list[str] = []
    for material in materials:
        op_ref = clean_identifier(material.get("operation_step_ref"), default="unknown_step", max_length=160)
        if material.get("body_free") is not True:
            refs.append(f"{op_ref}.body_free_not_true")
        for flag_ref in P7_R54_AHR_CR_NO_TOUCH_FALSE_FLAG_REFS:
            if material.get(flag_ref) is not False:
                refs.append(f"{op_ref}.{flag_ref}")
        public_contract = material.get("public_contract")
        no_touch_contract = material.get("r54_ahr_cr_no_touch_contract")
        body_markers = material.get("body_free_markers")
        for map_name, flag_map in (
            ("public_contract", public_contract),
            ("r54_ahr_cr_no_touch_contract", no_touch_contract),
            ("body_free_markers", body_markers),
        ):
            if not isinstance(flag_map, Mapping):
                refs.append(f"{op_ref}.{map_name}_not_mapping")
                continue
            if any(value is not False for value in flag_map.values()):
                refs.append(f"{op_ref}.{map_name}_mutated")
    return _dedupe_string_refs(refs, limit=100, max_length=220)


def build_p7_r54_ahr_cr21_final_no_body_leak_no_question_text_no_touch_validation(
    materials: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None = None,
    *,
    cr20_handoff_candidate_envelope: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build CR21 final cross-material no-body/no-question/no-touch validation."""

    session_id = _safe_review_session_id(review_session_id)
    provided = list(_cr21_materials_tuple(materials))
    if isinstance(cr20_handoff_candidate_envelope, Mapping) and cr20_handoff_candidate_envelope not in provided:
        provided.append(cr20_handoff_candidate_envelope)
    provided_tuple = tuple(provided)
    material_step_refs = _cr21_material_step_refs(provided_tuple)
    duplicate_step_refs = _cr21_duplicate_step_refs(provided_tuple)
    missing_step_refs = [ref for ref in P7_R54_AHR_CR21_VALIDATION_TARGET_STEP_REFS if ref not in material_step_refs]
    forbidden_refs, body_or_question_refs, path_or_hash_refs = _cr21_collect_forbidden_refs(provided_tuple, prefix="cr21_sources")
    contract_mutation_refs = _cr21_contract_mutation_refs(provided_tuple)
    no_body_passed = not forbidden_refs and not body_or_question_refs and not path_or_hash_refs and not contract_mutation_refs
    no_question_passed = not body_or_question_refs and all(
        material.get("question_text_materialized_here") is not True
        and material.get("draft_question_text_materialized_here") is not True
        and material.get("p8_question_implementation_spec_finalized_here") is not True
        for material in provided_tuple
    )
    no_touch_passed = not contract_mutation_refs
    cr20 = cr20_handoff_candidate_envelope if isinstance(cr20_handoff_candidate_envelope, Mapping) else {}
    if not cr20:
        for material in provided_tuple:
            if material.get("operation_step_ref") == P7_R54_AHR_CR20_STEP_REF:
                cr20 = material
                break
    blockers: list[str] = []
    if cr20.get("schema_version") != P7_R54_AHR_CR20_R52_HANDOFF_CANDIDATE_ENVELOPE_SCHEMA_VERSION or cr20.get("r52_reintake_handoff_ready") is not True:
        blockers.append(P7_R54_AHR_CR21_CR20_NOT_READY_BLOCKER_REF)
    if missing_step_refs:
        blockers.append(P7_R54_AHR_CR21_MISSING_TARGET_BLOCKER_REF)
    if duplicate_step_refs:
        blockers.append(P7_R54_AHR_CR21_DUPLICATE_TARGET_BLOCKER_REF)
    if forbidden_refs:
        blockers.append(P7_R54_AHR_CR21_FORBIDDEN_KEY_BLOCKER_REF)
    if body_or_question_refs or not no_question_passed:
        blockers.append(P7_R54_AHR_CR21_BODY_OR_QUESTION_LEAK_BLOCKER_REF)
    if path_or_hash_refs:
        blockers.append(P7_R54_AHR_CR21_PATH_OR_HASH_LEAK_BLOCKER_REF)
    if contract_mutation_refs:
        blockers.append(P7_R54_AHR_CR21_CONTRACT_MUTATION_BLOCKER_REF)
    blockers = _dedupe_string_refs(blockers, limit=50, max_length=200)
    ready = not blockers and no_body_passed and no_question_passed and no_touch_passed
    evidence_ready = bool(ready and cr20.get("actual_review_evidence_complete") is True)
    validated_material_refs = _dedupe_string_refs(
        [material.get("material_id") for material in provided_tuple],
        limit=40,
        max_length=180,
    )
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CR21_FINAL_NO_BODY_NO_QUESTION_NO_TOUCH_VALIDATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CR_STEP,
        "scope": P7_R54_AHR_CR_SCOPE,
        "policy_kind": P7_R54_AHR_CR_POLICY_KIND,
        "policy_section": P7_R54_AHR_CR21_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CR21_STEP_REF,
        "current_phase": P7_R54_AHR_CR_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cr21_final_no_body_no_question_no_touch_validation_20260628",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cr20_schema_version": cr20.get("schema_version"),
        "cr20_material_ref": cr20.get("material_id"),
        "cr20_next_required_step": cr20.get("next_required_step"),
        "cr20_r52_reintake_handoff_ready": cr20.get("r52_reintake_handoff_ready") is True,
        "cr20_r52_reintake_handoff_envelope_materialized_here": cr20.get("r52_reintake_handoff_envelope_materialized_here") is True,
        "cr20_actual_review_evidence_complete": cr20.get("actual_review_evidence_complete") is True,
        **_current_received_basis_fields(actual_basis=True),
        **_historical_basis_fields(),
        "final_validation_status_ref": P7_R54_AHR_CR21_PASSED_STATUS_REF if ready else P7_R54_AHR_CR21_BLOCKED_STATUS_REF,
        "final_validation_allowed_status_refs": list(P7_R54_AHR_CR21_ALLOWED_STATUS_REFS),
        "final_validation_passed": ready,
        "final_validation_reason_refs": [P7_R54_AHR_CR21_READY_REASON_REF] if ready else [],
        "final_validation_step_blocker_refs": blockers,
        "final_validation_step_blocker_ref_count": len(blockers),
        "validation_target_step_refs": list(P7_R54_AHR_CR21_VALIDATION_TARGET_STEP_REFS),
        "validation_target_step_ref_count": len(P7_R54_AHR_CR21_VALIDATION_TARGET_STEP_REFS),
        "validation_target_label_refs": list(P7_R54_AHR_CR21_VALIDATION_TARGET_LABEL_REFS),
        "validation_target_label_ref_count": len(P7_R54_AHR_CR21_VALIDATION_TARGET_LABEL_REFS),
        "provided_material_step_refs": material_step_refs,
        "provided_material_step_ref_count": len(material_step_refs),
        "missing_validation_target_step_refs": missing_step_refs,
        "missing_validation_target_step_ref_count": len(missing_step_refs),
        "duplicate_validation_target_step_refs": duplicate_step_refs,
        "duplicate_validation_target_step_ref_count": len(duplicate_step_refs),
        "no_body_leak_validation_passed": no_body_passed,
        "no_question_text_validation_passed": no_question_passed,
        "no_touch_validation_passed": no_touch_passed,
        "forbidden_key_refs_detected": forbidden_refs,
        "forbidden_key_ref_count": len(forbidden_refs),
        "body_or_question_leak_refs": body_or_question_refs,
        "body_or_question_leak_ref_count": len(body_or_question_refs),
        "path_or_hash_leak_refs": path_or_hash_refs,
        "path_or_hash_leak_ref_count": len(path_or_hash_refs),
        "contract_mutation_refs": contract_mutation_refs,
        "contract_mutation_ref_count": len(contract_mutation_refs),
        "validated_material_refs": validated_material_refs,
        "validated_material_ref_count": len(validated_material_refs),
        "validated_materials_bodyfree_only": all(material.get("body_free") is True for material in provided_tuple) and bool(provided_tuple),
        "validated_materials_have_no_forbidden_keys": not forbidden_refs,
        "validated_materials_public_contract_unchanged": not any(ref.endswith("public_contract_mutated") or ref.endswith("public_contract_not_mapping") for ref in contract_mutation_refs),
        "validated_materials_no_touch_contract_unchanged": not any(ref.endswith("r54_ahr_cr_no_touch_contract_mutated") or ref.endswith("r54_ahr_cr_no_touch_contract_not_mapping") for ref in contract_mutation_refs),
        "validated_materials_body_free_markers_unchanged": not any(ref.endswith("body_free_markers_mutated") or ref.endswith("body_free_markers_not_mapping") for ref in contract_mutation_refs),
        "actual_human_review_complete": evidence_ready,
        "actual_review_evidence_complete": evidence_ready,
        "actual_rating_rows_materialized_here": evidence_ready,
        "actual_question_need_observation_rows_materialized_here": evidence_ready,
        "actual_disposal_receipt_materialized_here": evidence_ready,
        "disposal_verified": evidence_ready,
        "actual_human_review_executed_by_person": evidence_ready,
        "actual_human_review_run_here": False,
        "actual_human_review_operation_run": False,
        "r52_reintake_execution_allowed_here": False,
        "r52_reintake_execution_started_here": False,
        "r52_reintake_execution_completed_here": False,
        "r52_reintake_execution_requested_here": False,
        "actual_r52_reintake_execution_confirmed": False,
        "p5_human_blind_qa_confirmed_final": False,
        "p5_confirmed_final": False,
        "p5_final_allowed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_start_allowed": False,
        "p8_start_allowed": False,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "p8_question_implementation_spec_finalized_here": False,
        "p7_complete": False,
        "release_allowed": False,
        "full_backend_suite_green_confirmed": False,
        "rn_contract_green_confirmed": False,
        "rn_real_device_modal_verified": False,
        "r52_handoff_ready_is_not_r52_reintake_executed": True,
        "p5_confirmed_candidate_not_promoted_to_final": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR_CR21_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CR20_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_CR21_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CR20_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_CR22_STEP_REF if ready else P7_R54_AHR_CR21_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    for flag_ref in P7_R54_AHR_CR21_ALLOWED_TRUE_OPERATION_FLAG_REFS:
        material[flag_ref] = evidence_ready
    material["r52_reintake_execution_requested_here"] = False
    material["actual_r52_reintake_execution_confirmed"] = False
    material["p5_human_blind_qa_confirmed_final"] = False
    material["p5_confirmed_final"] = False
    material["p5_final_allowed"] = False
    material["p6_limited_human_readfeel_start_allowed"] = False
    material["p6_start_allowed"] = False
    material["p8_start_allowed"] = False
    material["p7_complete"] = False
    material["release_allowed"] = False
    material["question_text_materialized_here"] = False
    material["draft_question_text_materialized_here"] = False
    material["p8_question_implementation_spec_finalized_here"] = False
    return material


def assert_p7_r54_ahr_cr20_r52_handoff_candidate_envelope_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CR20_R52_HANDOFF_CANDIDATE_ENVELOPE_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CR20 R52 handoff candidate envelope",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CR20_R52_HANDOFF_CANDIDATE_ENVELOPE_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CR20_STEP_REF,
        operation_step_ref=P7_R54_AHR_CR20_STEP_REF,
        source="P7-R54-AHR-CR20 R52 handoff candidate envelope",
        allowed_true_false_flag_refs=P7_R54_AHR_CR20_ALLOWED_TRUE_OPERATION_FLAG_REFS,
    )
    _assert_current_received_basis_fields(data, actual_basis=True, source="P7-R54-AHR-CR20 R52 handoff")
    _assert_historical_basis_fields(data, source="P7-R54-AHR-CR20 R52 handoff")
    if tuple(data.get("r52_reintake_handoff_allowed_status_refs") or ()) != P7_R54_AHR_CR20_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-CR20 allowed status refs changed")
    blockers = list(data.get("r52_reintake_handoff_step_blocker_refs") or [])
    if data.get("r52_reintake_handoff_step_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-CR20 blocker count changed")
    ready = (
        data.get("cr16_actual_review_evidence_complete") is True
        and data.get("cr16_actual_human_review_complete") is True
        and data.get("cr16_actual_human_review_executed_by_person") is True
        and data.get("cr16_rating_row_count") == P7_R54_AHR_CR_REQUIRED_CASE_COUNT
        and data.get("cr16_question_need_observation_row_count") == P7_R54_AHR_CR_REQUIRED_CASE_COUNT
        and data.get("cr16_disposal_verified") is True
        and data.get("cr17_p5_decision_ref") == P7_R54_AHR_CR17_P5_CONFIRMED_CANDIDATE_REF
        and data.get("cr17_p5_confirmed_candidate") is True
        and data.get("cr17_p5_confirmed_candidate_only") is True
        and data.get("cr17_p5_decision_candidate_ready_for_r52_handoff") is True
        and data.get("cr17_repair_or_blocker_case_count") == 0
        and data.get("cr18_p6_candidate_only_handoff_ready") is True
        and data.get("cr19_p8_material_candidate_only_handoff_ready") is True
        and data.get("cr16_next_required_step") == P7_R54_AHR_CR17_STEP_REF
        and data.get("cr17_next_required_step") == P7_R54_AHR_CR18_STEP_REF
        and data.get("cr18_next_required_step") == P7_R54_AHR_CR19_STEP_REF
        and data.get("cr19_next_required_step") == P7_R54_AHR_CR20_STEP_REF
    )
    if data.get("r52_reintake_handoff_ready") is not ready:
        raise ValueError("P7-R54-AHR-CR20 ready flag changed")
    _assert_false_fields(
        data,
        keys=(
            "actual_human_review_run_here",
            "actual_human_review_operation_run",
            "r52_reintake_execution_allowed_here",
            "r52_reintake_execution_started_here",
            "r52_reintake_execution_completed_here",
            "r52_reintake_execution_requested_here",
            "actual_r52_reintake_execution_confirmed",
            "p5_human_blind_qa_confirmed_final",
            "p5_confirmed_final",
            "p5_final_allowed",
            "p6_limited_human_readfeel_start_allowed",
            "p6_start_allowed",
            "p8_start_allowed",
            "question_text_materialized_here",
            "draft_question_text_materialized_here",
            "p8_question_implementation_spec_finalized_here",
            "p7_complete",
            "release_allowed",
            "full_backend_suite_green_confirmed",
            "rn_contract_green_confirmed",
            "rn_real_device_modal_verified",
        ),
        source="P7-R54-AHR-CR20 false promotions",
    )
    if data.get("r52_handoff_ready_is_not_r52_reintake_executed") is not True:
        raise ValueError("P7-R54-AHR-CR20 R52 claim boundary changed")
    if ready:
        if data.get("r52_reintake_handoff_status_ref") != P7_R54_AHR_CR20_READY_STATUS_REF:
            raise ValueError("P7-R54-AHR-CR20 ready status changed")
        if blockers:
            raise ValueError("P7-R54-AHR-CR20 ready material cannot carry blockers")
        _assert_true_fields(
            data,
            keys=(
                "r52_reintake_handoff_envelope_materialized_here",
                "r52_handoff_candidate_bodyfree_only",
                "r52_handoff_candidate_contains_no_question_text",
                "r52_handoff_candidate_contains_no_body_payload",
                "p5_confirmed_candidate",
                "p5_confirmed_candidate_only",
                "p5_confirmed_candidate_is_not_p5_final",
                "p6_candidate_only_handoff_ready",
                "p6_candidate_only_is_not_p6_start_allowed",
                "p8_material_candidate_only_handoff_ready",
                "p8_material_candidate_only_is_not_p8_start_allowed",
            ),
            source="P7-R54-AHR-CR20 ready envelope",
        )
        if data.get("r52_handoff_candidate_ref") != P7_R54_AHR_CR20_R52_HANDOFF_CANDIDATE_REF:
            raise ValueError("P7-R54-AHR-CR20 candidate ref changed")
        if tuple(data.get("r52_handoff_candidate_boundary_refs") or ()) != P7_R54_AHR_CR20_R52_BOUNDARY_REFS:
            raise ValueError("P7-R54-AHR-CR20 boundary refs changed")
        if data.get("r52_handoff_candidate_boundary_ref_count") != len(P7_R54_AHR_CR20_R52_BOUNDARY_REFS):
            raise ValueError("P7-R54-AHR-CR20 boundary ref count changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CR20_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CR20 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CR20_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CR20 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_CR21_STEP_REF:
            raise ValueError("P7-R54-AHR-CR20 ready next step changed")
    else:
        if data.get("r52_reintake_handoff_status_ref") != P7_R54_AHR_CR20_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-CR20 blocked status changed")
        if not blockers:
            raise ValueError("P7-R54-AHR-CR20 blocked material must carry blockers")
        _assert_false_fields(
            data,
            keys=(
                "r52_reintake_handoff_envelope_materialized_here",
                "r52_handoff_candidate_bodyfree_only",
                "r52_handoff_candidate_contains_no_question_text",
                "r52_handoff_candidate_contains_no_body_payload",
                "p5_confirmed_candidate",
                "p5_confirmed_candidate_only",
                "p6_candidate_only_handoff_ready",
                "p8_material_candidate_only_handoff_ready",
            ),
            source="P7-R54-AHR-CR20 blocked envelope",
        )
        if data.get("r52_handoff_candidate_ref") != "":
            raise ValueError("P7-R54-AHR-CR20 blocked material cannot carry candidate ref")
        if data.get("next_required_step") != P7_R54_AHR_CR20_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CR20 blocked next step changed")
    return True


def assert_p7_r54_ahr_cr21_final_no_body_leak_no_question_text_no_touch_validation_contract(
    data: Mapping[str, Any]
) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CR21_FINAL_VALIDATION_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CR21 final no-body/no-question/no-touch validation",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CR21_FINAL_NO_BODY_NO_QUESTION_NO_TOUCH_VALIDATION_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CR21_STEP_REF,
        operation_step_ref=P7_R54_AHR_CR21_STEP_REF,
        source="P7-R54-AHR-CR21 final no-body/no-question/no-touch validation",
        allowed_true_false_flag_refs=P7_R54_AHR_CR21_ALLOWED_TRUE_OPERATION_FLAG_REFS,
    )
    _assert_current_received_basis_fields(data, actual_basis=True, source="P7-R54-AHR-CR21 final validation")
    _assert_historical_basis_fields(data, source="P7-R54-AHR-CR21 final validation")
    if tuple(data.get("final_validation_allowed_status_refs") or ()) != P7_R54_AHR_CR21_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-CR21 allowed status refs changed")
    if tuple(data.get("validation_target_step_refs") or ()) != P7_R54_AHR_CR21_VALIDATION_TARGET_STEP_REFS:
        raise ValueError("P7-R54-AHR-CR21 validation target refs changed")
    if tuple(data.get("validation_target_label_refs") or ()) != P7_R54_AHR_CR21_VALIDATION_TARGET_LABEL_REFS:
        raise ValueError("P7-R54-AHR-CR21 validation target labels changed")
    for field, count_field in (
        ("validation_target_step_refs", "validation_target_step_ref_count"),
        ("validation_target_label_refs", "validation_target_label_ref_count"),
        ("provided_material_step_refs", "provided_material_step_ref_count"),
        ("missing_validation_target_step_refs", "missing_validation_target_step_ref_count"),
        ("duplicate_validation_target_step_refs", "duplicate_validation_target_step_ref_count"),
        ("forbidden_key_refs_detected", "forbidden_key_ref_count"),
        ("body_or_question_leak_refs", "body_or_question_leak_ref_count"),
        ("path_or_hash_leak_refs", "path_or_hash_leak_ref_count"),
        ("contract_mutation_refs", "contract_mutation_ref_count"),
        ("validated_material_refs", "validated_material_ref_count"),
        ("final_validation_step_blocker_refs", "final_validation_step_blocker_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-CR21 {count_field} changed")
    ready = (
        data.get("cr20_schema_version") == P7_R54_AHR_CR20_R52_HANDOFF_CANDIDATE_ENVELOPE_SCHEMA_VERSION
        and data.get("cr20_r52_reintake_handoff_ready") is True
        and data.get("cr20_r52_reintake_handoff_envelope_materialized_here") is True
        and data.get("cr20_actual_review_evidence_complete") is True
        and data.get("missing_validation_target_step_refs") == []
        and data.get("duplicate_validation_target_step_refs") == []
        and data.get("no_body_leak_validation_passed") is True
        and data.get("no_question_text_validation_passed") is True
        and data.get("no_touch_validation_passed") is True
        and data.get("forbidden_key_refs_detected") == []
        and data.get("body_or_question_leak_refs") == []
        and data.get("path_or_hash_leak_refs") == []
        and data.get("contract_mutation_refs") == []
    )
    if data.get("final_validation_passed") is not ready:
        raise ValueError("P7-R54-AHR-CR21 final validation flag changed")
    _assert_false_fields(
        data,
        keys=(
            "actual_human_review_run_here",
            "actual_human_review_operation_run",
            "r52_reintake_execution_allowed_here",
            "r52_reintake_execution_started_here",
            "r52_reintake_execution_completed_here",
            "r52_reintake_execution_requested_here",
            "actual_r52_reintake_execution_confirmed",
            "p5_human_blind_qa_confirmed_final",
            "p5_confirmed_final",
            "p5_final_allowed",
            "p6_limited_human_readfeel_start_allowed",
            "p6_start_allowed",
            "p8_start_allowed",
            "question_text_materialized_here",
            "draft_question_text_materialized_here",
            "p8_question_implementation_spec_finalized_here",
            "p7_complete",
            "release_allowed",
            "full_backend_suite_green_confirmed",
            "rn_contract_green_confirmed",
            "rn_real_device_modal_verified",
        ),
        source="P7-R54-AHR-CR21 false promotions",
    )
    if ready:
        if data.get("final_validation_status_ref") != P7_R54_AHR_CR21_PASSED_STATUS_REF:
            raise ValueError("P7-R54-AHR-CR21 passed status changed")
        if data.get("final_validation_step_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-CR21 passed validation cannot carry blockers")
        _assert_true_fields(
            data,
            keys=(
                "validated_materials_bodyfree_only",
                "validated_materials_have_no_forbidden_keys",
                "validated_materials_public_contract_unchanged",
                "validated_materials_no_touch_contract_unchanged",
                "validated_materials_body_free_markers_unchanged",
                "r52_handoff_ready_is_not_r52_reintake_executed",
            ),
            source="P7-R54-AHR-CR21 passed validation",
        )
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CR21_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CR21 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CR21_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CR21 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_CR22_STEP_REF:
            raise ValueError("P7-R54-AHR-CR21 ready next step changed")
    else:
        if data.get("final_validation_status_ref") != P7_R54_AHR_CR21_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-CR21 blocked status changed")
        if not data.get("final_validation_step_blocker_refs"):
            raise ValueError("P7-R54-AHR-CR21 blocked validation must carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_CR21_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CR21 blocked next step changed")
    return True



# R54-AHR-CR22: validation command matrix and documentation output.
P7_R54_AHR_CR22_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_received_actual_local_review_operation."
    "cr22_validation_command_matrix_documentation_output.bodyfree.v1"
)
P7_R54_AHR_CR_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CR22_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION
)

P7_R54_AHR_CR22_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR21_IMPLEMENTED_STEPS,
    P7_R54_AHR_CR22_STEP_REF,
)
P7_R54_AHR_CR22_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = ()

P7_R54_AHR_CR22_READY_STATUS_REF: Final = "CR22_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_READY_BODYFREE"
P7_R54_AHR_CR22_BLOCKED_STATUS_REF: Final = "CR22_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_BLOCKED"
P7_R54_AHR_CR22_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR22_READY_STATUS_REF,
    P7_R54_AHR_CR22_BLOCKED_STATUS_REF,
)
P7_R54_AHR_CR22_READY_REASON_REF: Final = (
    "CR22_TARGET_SELECTED_REGRESSION_COMPILEALL_AND_CLAIM_BOUNDARY_DOCUMENTED_BODYFREE"
)
P7_R54_AHR_CR22_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "fix_cr22_validation_command_matrix_documentation_or_stop"
P7_R54_AHR_CR22_COMPLETE_NEXT_REQUIRED_STEP_REF: Final = "cr22_documentation_output_complete_no_p7_release_promotion"
P7_R54_AHR_CR22_CR21_NOT_READY_BLOCKER_REF: Final = "cr21_final_validation_not_ready"
P7_R54_AHR_CR22_MISSING_COMMAND_BLOCKER_REF: Final = "cr22_required_validation_command_row_missing"
P7_R54_AHR_CR22_DUPLICATE_COMMAND_BLOCKER_REF: Final = "cr22_validation_command_row_duplicate"
P7_R54_AHR_CR22_REQUIRED_PASS_COMMAND_NOT_PASSED_BLOCKER_REF: Final = "cr22_required_pass_command_not_passed"
P7_R54_AHR_CR22_REQUIRED_NOT_CLAIMED_COMMAND_CLAIMED_BLOCKER_REF: Final = (
    "cr22_required_not_claimed_command_claimed"
)
P7_R54_AHR_CR22_FORBIDDEN_KEY_BLOCKER_REF: Final = "cr22_command_matrix_forbidden_body_question_path_hash_key"
P7_R54_AHR_CR22_RESULT_MEMO_REF_MISSING_BLOCKER_REF: Final = "cr22_result_memo_ref_missing"
P7_R54_AHR_CR22_UNALLOWED_GREEN_CLAIM_BLOCKER_REF: Final = "cr22_unallowed_green_claim_detected"

P7_R54_AHR_CR22_COMMAND_STATUS_PASSED_REF: Final = "PASSED_BODYFREE_RECORDED"
P7_R54_AHR_CR22_COMMAND_STATUS_NOT_RUN_NOT_CLAIMED_REF: Final = "NOT_RUN_NOT_CLAIMED"
P7_R54_AHR_CR22_COMMAND_STATUS_TIMEOUT_NOT_CLAIMED_REF: Final = "TIMEOUT_NOT_CLAIMED"
P7_R54_AHR_CR22_COMMAND_STATUS_SKIPPED_NOT_CLAIMED_REF: Final = "SKIPPED_NOT_CLAIMED"
P7_R54_AHR_CR22_COMMAND_STATUS_FAILED_RECORDED_REF: Final = "FAILED_BODYFREE_RECORDED"
P7_R54_AHR_CR22_ALLOWED_COMMAND_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR22_COMMAND_STATUS_PASSED_REF,
    P7_R54_AHR_CR22_COMMAND_STATUS_NOT_RUN_NOT_CLAIMED_REF,
    P7_R54_AHR_CR22_COMMAND_STATUS_TIMEOUT_NOT_CLAIMED_REF,
    P7_R54_AHR_CR22_COMMAND_STATUS_SKIPPED_NOT_CLAIMED_REF,
    P7_R54_AHR_CR22_COMMAND_STATUS_FAILED_RECORDED_REF,
)

P7_R54_AHR_CR22_TARGET_CR00_TO_CR22_COMMAND_REF: Final = "CR22_TARGET_PYTEST_CR00_TO_CR22"
P7_R54_AHR_CR22_SELECTED_CS_COMMAND_REF: Final = "CR22_SELECTED_REGRESSION_CS00_TO_CS18"
P7_R54_AHR_CR22_SELECTED_SMOKE_COMMAND_REF: Final = "CR22_SELECTED_REGRESSION_CS00_CS01_AHR00_AHR01"
P7_R54_AHR_CR22_COMPILEALL_COMMAND_REF: Final = "CR22_COMPILEALL_AI_SERVICES_AI_TESTS"
P7_R54_AHR_CR22_FULL_BACKEND_NOT_CLAIMED_COMMAND_REF: Final = "CR22_FULL_BACKEND_SUITE_GREEN_NOT_CLAIMED"
P7_R54_AHR_CR22_RN_CONTRACT_NOT_CLAIMED_COMMAND_REF: Final = "CR22_RN_CONTRACT_GREEN_NOT_CLAIMED_UNLESS_ACTUALLY_RUN"
P7_R54_AHR_CR22_RN_REAL_DEVICE_NOT_CLAIMED_COMMAND_REF: Final = "CR22_RN_REAL_DEVICE_MODAL_NOT_CLAIMED"
P7_R54_AHR_CR22_EXISTING_AHR_FULL_SPLIT_NOT_CLAIMED_COMMAND_REF: Final = (
    "CR22_EXISTING_AHR_FULL_SPLIT_GREEN_NOT_CLAIMED_HERE"
)
P7_R54_AHR_CR22_REQUIRED_COMMAND_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR22_TARGET_CR00_TO_CR22_COMMAND_REF,
    P7_R54_AHR_CR22_SELECTED_CS_COMMAND_REF,
    P7_R54_AHR_CR22_SELECTED_SMOKE_COMMAND_REF,
    P7_R54_AHR_CR22_COMPILEALL_COMMAND_REF,
    P7_R54_AHR_CR22_FULL_BACKEND_NOT_CLAIMED_COMMAND_REF,
    P7_R54_AHR_CR22_RN_CONTRACT_NOT_CLAIMED_COMMAND_REF,
    P7_R54_AHR_CR22_RN_REAL_DEVICE_NOT_CLAIMED_COMMAND_REF,
    P7_R54_AHR_CR22_EXISTING_AHR_FULL_SPLIT_NOT_CLAIMED_COMMAND_REF,
)
P7_R54_AHR_CR22_REQUIRED_PASS_COMMAND_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR22_TARGET_CR00_TO_CR22_COMMAND_REF,
    P7_R54_AHR_CR22_SELECTED_CS_COMMAND_REF,
    P7_R54_AHR_CR22_SELECTED_SMOKE_COMMAND_REF,
    P7_R54_AHR_CR22_COMPILEALL_COMMAND_REF,
)
P7_R54_AHR_CR22_REQUIRED_NOT_CLAIMED_COMMAND_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR22_FULL_BACKEND_NOT_CLAIMED_COMMAND_REF,
    P7_R54_AHR_CR22_RN_CONTRACT_NOT_CLAIMED_COMMAND_REF,
    P7_R54_AHR_CR22_RN_REAL_DEVICE_NOT_CLAIMED_COMMAND_REF,
    P7_R54_AHR_CR22_EXISTING_AHR_FULL_SPLIT_NOT_CLAIMED_COMMAND_REF,
)
P7_R54_AHR_CR22_COMMAND_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "command_ref",
    "command_kind_ref",
    "command_scope_ref",
    "command_display_ref",
    "command_status_ref",
    "command_status_allowed_refs",
    "passed",
    "ran_here",
    "green_claimed",
    "full_backend_suite_green_claimed",
    "rn_contract_green_claimed",
    "rn_real_device_modal_claimed",
    "actual_human_review_complete_claimed_by_command",
    "p5_final_claimed",
    "p6_start_claimed",
    "p8_start_claimed",
    "r52_actual_execution_claimed",
    "p7_complete_claimed",
    "release_allowed_claimed",
    "raw_terminal_output_included",
    "terminal_output_body_included",
    "stdout_body_included",
    "stderr_body_included",
    "traceback_body_included",
    "local_absolute_path_included",
    "body_hash_included",
    "body_free",
)
P7_R54_AHR_CR22_COMMAND_ROW_ALLOWED_KEY_REFS: Final[frozenset[str]] = frozenset(
    P7_R54_AHR_CR22_COMMAND_ROW_REQUIRED_FIELD_REFS
)
P7_R54_AHR_CR22_DEFAULT_RESULT_MEMO_REF: Final = (
    "R54_AHR_CR22_CurrentReceivedActualLocalReviewOperation_Result_20260628.md"
)
P7_R54_AHR_CR22_VALIDATION_MATRIX_REF: Final = "R54_AHR_CR22_VALIDATION_COMMAND_MATRIX_BODYFREE"
P7_R54_AHR_CR22_RESULT_MEMO_KIND_REF: Final = "bodyfree_result_memo_documentation_output"
P7_R54_AHR_CR22_CLAIM_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "CR22_TARGET_AND_SELECTED_REGRESSION_DOCUMENTED_IS_NOT_FULL_BACKEND_SUITE_GREEN",
    "CR22_RN_CONTRACT_GREEN_NOT_CLAIMED_UNLESS_ACTUALLY_RUN",
    "CR22_RN_REAL_DEVICE_MODAL_VERIFIED_FALSE",
    "CR22_ACTUAL_HUMAN_REVIEW_NEWLY_RUN_HERE_FALSE",
    "CR22_P5_CONFIRMED_CANDIDATE_IS_NOT_P5_FINAL",
    "CR22_P6_CANDIDATE_ONLY_IS_NOT_P6_START_ALLOWED",
    "CR22_P8_MATERIAL_CANDIDATE_ONLY_IS_NOT_P8_START_ALLOWED",
    "CR22_R52_HANDOFF_CANDIDATE_IS_NOT_R52_ACTUAL_EXECUTION",
    "CR22_P7_COMPLETE_FALSE",
    "CR22_RELEASE_ALLOWED_FALSE",
)
P7_R54_AHR_CR22_ALLOWED_TRUE_OPERATION_FLAG_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CR21_ALLOWED_TRUE_OPERATION_FLAG_REFS
)

P7_R54_AHR_CR22_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CR_BASE_REQUIRED_FIELD_REFS,
    "cr21_schema_version",
    "cr21_material_ref",
    "cr21_next_required_step",
    "cr21_final_validation_passed",
    "cr21_no_body_leak_validation_passed",
    "cr21_no_question_text_validation_passed",
    "cr21_no_touch_validation_passed",
    "cr21_actual_review_evidence_complete",
    *P7_R54_AHR_CR_CURRENT_RECEIVED_BASIS_FIELD_REFS,
    *P7_R54_AHR_CR_HISTORICAL_BASIS_FIELD_REFS,
    "documentation_output_status_ref",
    "documentation_output_allowed_status_refs",
    "documentation_output_ready",
    "documentation_output_reason_refs",
    "documentation_output_step_blocker_refs",
    "documentation_output_step_blocker_ref_count",
    "validation_matrix_ref",
    "validation_command_rows",
    "validation_command_row_count",
    "validation_command_refs",
    "validation_command_ref_count",
    "required_validation_command_refs",
    "required_validation_command_ref_count",
    "required_pass_validation_command_refs",
    "required_pass_validation_command_ref_count",
    "required_not_claimed_validation_command_refs",
    "required_not_claimed_validation_command_ref_count",
    "missing_validation_command_refs",
    "missing_validation_command_ref_count",
    "duplicate_validation_command_refs",
    "duplicate_validation_command_ref_count",
    "nonpassed_required_validation_command_refs",
    "nonpassed_required_validation_command_ref_count",
    "claimed_required_not_claimed_command_refs",
    "claimed_required_not_claimed_command_ref_count",
    "unallowed_green_claim_refs",
    "unallowed_green_claim_ref_count",
    "forbidden_command_row_key_refs",
    "forbidden_command_row_key_ref_count",
    "target_tests_documented",
    "selected_regression_documented",
    "compileall_documented",
    "claim_boundary_documented",
    "result_memo_ref",
    "result_memo_ref_present",
    "result_memo_kind_ref",
    "result_memo_bodyfree_only",
    "result_memo_raw_output_included",
    "result_memo_question_text_included",
    "result_memo_local_path_included",
    "result_memo_materialized_here",
    "validation_matrix_materialized_here",
    "documentation_claim_boundary_refs",
    "documentation_claim_boundary_ref_count",
    "actual_human_review_complete_documented_from_cr21_predicate_only",
    "actual_human_review_newly_run_here",
    "full_backend_suite_green_unclaimed",
    "rn_contract_green_unclaimed_unless_actually_run",
    "rn_real_device_modal_verified_unclaimed",
    "selected_regression_green_is_not_full_backend_suite_green",
    "rn_contract_green_is_not_rn_real_device_modal_verified",
    "r52_handoff_ready_is_not_r52_reintake_executed",
    "p5_confirmed_candidate_is_not_p5_final",
    "p6_candidate_only_is_not_p6_start_allowed",
    "p8_material_candidate_only_is_not_p8_start_allowed",
    "actual_human_review_complete",
    "actual_review_evidence_complete",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_human_review_operation_run",
    "r52_reintake_execution_allowed_here",
    "r52_reintake_execution_started_here",
    "r52_reintake_execution_completed_here",
    "r52_reintake_execution_requested_here",
    "actual_r52_reintake_execution_confirmed",
    "p5_human_blind_qa_confirmed_final",
    "p5_confirmed_final",
    "p5_final_allowed",
    "p6_limited_human_readfeel_start_allowed",
    "p6_start_allowed",
    "p8_start_allowed",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "p8_question_implementation_spec_finalized_here",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_confirmed",
    "rn_contract_green_confirmed",
    "rn_real_device_modal_verified",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CR_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CR_FALSE_FLAG_REFS,
)
P7_R54_AHR_CR_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CR22_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_REQUIRED_FIELD_REFS
)


def _cr22_command_row(
    *,
    command_ref: str,
    command_kind_ref: str,
    command_scope_ref: str,
    command_display_ref: str,
    command_status_ref: str,
    ran_here: bool,
    green_claimed: bool = False,
    full_backend_suite_green_claimed: bool = False,
    rn_contract_green_claimed: bool = False,
    rn_real_device_modal_claimed: bool = False,
) -> dict[str, Any]:
    passed = command_status_ref == P7_R54_AHR_CR22_COMMAND_STATUS_PASSED_REF
    return {
        "command_ref": command_ref,
        "command_kind_ref": command_kind_ref,
        "command_scope_ref": command_scope_ref,
        "command_display_ref": command_display_ref,
        "command_status_ref": command_status_ref,
        "command_status_allowed_refs": list(P7_R54_AHR_CR22_ALLOWED_COMMAND_STATUS_REFS),
        "passed": passed,
        "ran_here": bool(ran_here),
        "green_claimed": bool(green_claimed),
        "full_backend_suite_green_claimed": bool(full_backend_suite_green_claimed),
        "rn_contract_green_claimed": bool(rn_contract_green_claimed),
        "rn_real_device_modal_claimed": bool(rn_real_device_modal_claimed),
        "actual_human_review_complete_claimed_by_command": False,
        "p5_final_claimed": False,
        "p6_start_claimed": False,
        "p8_start_claimed": False,
        "r52_actual_execution_claimed": False,
        "p7_complete_claimed": False,
        "release_allowed_claimed": False,
        "raw_terminal_output_included": False,
        "terminal_output_body_included": False,
        "stdout_body_included": False,
        "stderr_body_included": False,
        "traceback_body_included": False,
        "local_absolute_path_included": False,
        "body_hash_included": False,
        "body_free": True,
    }


def build_p7_r54_ahr_cr22_bodyfree_validation_command_rows_input() -> list[dict[str, Any]]:
    """Return a body-free CR22 command matrix input for the intended local validation pass."""
    return [
        _cr22_command_row(
            command_ref=P7_R54_AHR_CR22_TARGET_CR00_TO_CR22_COMMAND_REF,
            command_kind_ref="target_pytest",
            command_scope_ref="cr00_to_cr22_current_received_actual_local_review_operation",
            command_display_ref=(
                "PYTHONPATH=ai/services/ai_inference python -m pytest "
                "ai/tests/test_r54_ahr_current_received_actual_local_review_operation_cr00_cr01_20260628.py "
                "ai/tests/test_r54_ahr_current_received_actual_local_review_operation_cr02_cr03_20260628.py "
                "ai/tests/test_r54_ahr_current_received_actual_local_review_operation_cr04_cr05_20260628.py "
                "ai/tests/test_r54_ahr_current_received_actual_local_review_operation_cr06_cr07_20260628.py "
                "ai/tests/test_r54_ahr_current_received_actual_local_review_operation_cr08_cr09_20260628.py "
                "ai/tests/test_r54_ahr_current_received_actual_local_review_operation_cr10_cr11_20260628.py "
                "ai/tests/test_r54_ahr_current_received_actual_local_review_operation_cr12_cr13_20260628.py "
                "ai/tests/test_r54_ahr_current_received_actual_local_review_operation_cr14_cr15_20260628.py "
                "ai/tests/test_r54_ahr_current_received_actual_local_review_operation_cr16_cr17_20260628.py "
                "ai/tests/test_r54_ahr_current_received_actual_local_review_operation_cr18_cr19_20260628.py "
                "ai/tests/test_r54_ahr_current_received_actual_local_review_operation_cr20_cr21_20260628.py "
                "ai/tests/test_r54_ahr_current_received_actual_local_review_operation_cr22_20260628.py -q"
            ),
            command_status_ref=P7_R54_AHR_CR22_COMMAND_STATUS_PASSED_REF,
            ran_here=True,
            green_claimed=True,
        ),
        _cr22_command_row(
            command_ref=P7_R54_AHR_CR22_SELECTED_CS_COMMAND_REF,
            command_kind_ref="selected_regression_pytest",
            command_scope_ref="cs00_to_cs18_selected_regression",
            command_display_ref=(
                "PYTHONPATH=ai/services/ai_inference python -m pytest "
                "ai/tests/test_r54_ahr_current_snapshot_actual_review_reentry_cs00_cs01_20260628.py "
                "ai/tests/test_r54_ahr_current_snapshot_actual_review_reentry_cs02_cs03_20260628.py "
                "ai/tests/test_r54_ahr_current_snapshot_actual_review_reentry_cs04_cs05_20260628.py "
                "ai/tests/test_r54_ahr_current_snapshot_actual_review_reentry_cs06_cs07_20260628.py "
                "ai/tests/test_r54_ahr_current_snapshot_actual_review_reentry_cs08_cs09_20260628.py "
                "ai/tests/test_r54_ahr_current_snapshot_actual_review_reentry_cs10_cs11_20260628.py "
                "ai/tests/test_r54_ahr_current_snapshot_actual_review_reentry_cs12_cs13_20260628.py "
                "ai/tests/test_r54_ahr_current_snapshot_actual_review_reentry_cs14_cs15_20260628.py "
                "ai/tests/test_r54_ahr_current_snapshot_actual_review_reentry_cs16_cs17_20260628.py "
                "ai/tests/test_r54_ahr_current_snapshot_actual_review_reentry_cs18_20260628.py -q"
            ),
            command_status_ref=P7_R54_AHR_CR22_COMMAND_STATUS_PASSED_REF,
            ran_here=True,
            green_claimed=True,
        ),
        _cr22_command_row(
            command_ref=P7_R54_AHR_CR22_SELECTED_SMOKE_COMMAND_REF,
            command_kind_ref="selected_smoke_regression_pytest",
            command_scope_ref="cs00_cs01_plus_ahr00_ahr01_smoke",
            command_display_ref=(
                "PYTHONPATH=ai/services/ai_inference python -m pytest "
                "ai/tests/test_r54_ahr_current_snapshot_actual_review_reentry_cs00_cs01_20260628.py "
                "ai/tests/test_r54_actual_human_review_execution_bodyfree_intake_ahr00_ahr01_20260627.py -q"
            ),
            command_status_ref=P7_R54_AHR_CR22_COMMAND_STATUS_PASSED_REF,
            ran_here=True,
            green_claimed=True,
        ),
        _cr22_command_row(
            command_ref=P7_R54_AHR_CR22_COMPILEALL_COMMAND_REF,
            command_kind_ref="compileall",
            command_scope_ref="ai_services_ai_inference_and_tests",
            command_display_ref="python -m compileall ai/services/ai_inference ai/tests",
            command_status_ref=P7_R54_AHR_CR22_COMMAND_STATUS_PASSED_REF,
            ran_here=True,
            green_claimed=True,
        ),
        _cr22_command_row(
            command_ref=P7_R54_AHR_CR22_FULL_BACKEND_NOT_CLAIMED_COMMAND_REF,
            command_kind_ref="claim_boundary",
            command_scope_ref="full_backend_suite_green",
            command_display_ref="full backend suite green not claimed by CR22 selected validation",
            command_status_ref=P7_R54_AHR_CR22_COMMAND_STATUS_NOT_RUN_NOT_CLAIMED_REF,
            ran_here=False,
        ),
        _cr22_command_row(
            command_ref=P7_R54_AHR_CR22_RN_CONTRACT_NOT_CLAIMED_COMMAND_REF,
            command_kind_ref="claim_boundary",
            command_scope_ref="rn_contract_green",
            command_display_ref="RN contract green not claimed unless actually run",
            command_status_ref=P7_R54_AHR_CR22_COMMAND_STATUS_NOT_RUN_NOT_CLAIMED_REF,
            ran_here=False,
        ),
        _cr22_command_row(
            command_ref=P7_R54_AHR_CR22_RN_REAL_DEVICE_NOT_CLAIMED_COMMAND_REF,
            command_kind_ref="claim_boundary",
            command_scope_ref="rn_real_device_modal_verified",
            command_display_ref="RN real-device modal verified not claimed",
            command_status_ref=P7_R54_AHR_CR22_COMMAND_STATUS_NOT_RUN_NOT_CLAIMED_REF,
            ran_here=False,
        ),
        _cr22_command_row(
            command_ref=P7_R54_AHR_CR22_EXISTING_AHR_FULL_SPLIT_NOT_CLAIMED_COMMAND_REF,
            command_kind_ref="claim_boundary",
            command_scope_ref="existing_ahr_full_split_green",
            command_display_ref="existing AHR full split green not claimed by CR22 when not rerun here",
            command_status_ref=P7_R54_AHR_CR22_COMMAND_STATUS_NOT_RUN_NOT_CLAIMED_REF,
            ran_here=False,
        ),
    ]


def _cr22_clean_command_row(row: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    forbidden_refs: list[str] = []
    if not isinstance(row, Mapping):
        row = {}
    for key_ref in row.keys():
        key = str(key_ref)
        if key not in P7_R54_AHR_CR22_COMMAND_ROW_ALLOWED_KEY_REFS:
            forbidden_refs.append(key)
        if key in P7_R54_AHR_CR21_FORBIDDEN_BODY_OR_QUESTION_KEY_REFS or key in P7_R54_AHR_CR21_FORBIDDEN_PATH_OR_HASH_KEY_REFS:
            forbidden_refs.append(key)
    command_ref = clean_identifier(row.get("command_ref"), default="", max_length=160)
    command_kind_ref = clean_identifier(row.get("command_kind_ref"), default="unknown_command_kind", max_length=160)
    command_scope_ref = clean_identifier(row.get("command_scope_ref"), default="unknown_command_scope", max_length=180)
    command_display_ref = clean_identifier(row.get("command_display_ref"), default="command_ref_only", max_length=720)
    status_ref = clean_identifier(row.get("command_status_ref"), default="", max_length=160)
    if status_ref not in P7_R54_AHR_CR22_ALLOWED_COMMAND_STATUS_REFS:
        status_ref = P7_R54_AHR_CR22_COMMAND_STATUS_FAILED_RECORDED_REF
    cleaned = _cr22_command_row(
        command_ref=command_ref,
        command_kind_ref=command_kind_ref,
        command_scope_ref=command_scope_ref,
        command_display_ref=command_display_ref,
        command_status_ref=status_ref,
        ran_here=row.get("ran_here") is True,
        green_claimed=row.get("green_claimed") is True,
        full_backend_suite_green_claimed=row.get("full_backend_suite_green_claimed") is True,
        rn_contract_green_claimed=row.get("rn_contract_green_claimed") is True,
        rn_real_device_modal_claimed=row.get("rn_real_device_modal_claimed") is True,
    )
    for claim_key in (
        "actual_human_review_complete_claimed_by_command",
        "p5_final_claimed",
        "p6_start_claimed",
        "p8_start_claimed",
        "r52_actual_execution_claimed",
        "p7_complete_claimed",
        "release_allowed_claimed",
    ):
        cleaned[claim_key] = row.get(claim_key) is True
    for leak_key in (
        "raw_terminal_output_included",
        "terminal_output_body_included",
        "stdout_body_included",
        "stderr_body_included",
        "traceback_body_included",
        "local_absolute_path_included",
        "body_hash_included",
    ):
        if row.get(leak_key) is True:
            forbidden_refs.append(leak_key)
        cleaned[leak_key] = False
    cleaned["body_free"] = True
    cleaned["command_status_allowed_refs"] = list(P7_R54_AHR_CR22_ALLOWED_COMMAND_STATUS_REFS)
    cleaned["passed"] = cleaned["command_status_ref"] == P7_R54_AHR_CR22_COMMAND_STATUS_PASSED_REF
    return cleaned, _dedupe_string_refs(forbidden_refs, limit=60, max_length=180)


def _cr22_command_rows(command_rows: Sequence[Mapping[str, Any]] | None) -> tuple[list[dict[str, Any]], list[str]]:
    if command_rows is None:
        return [], []
    rows: list[dict[str, Any]] = []
    forbidden: list[str] = []
    for row in command_rows:
        cleaned, row_forbidden = _cr22_clean_command_row(row)
        rows.append(cleaned)
        forbidden.extend(row_forbidden)
    return rows, _dedupe_string_refs(forbidden, limit=120, max_length=180)


def _cr22_duplicate_command_refs(command_refs: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for ref in command_refs:
        if ref in seen and ref not in duplicates:
            duplicates.append(ref)
        seen.add(ref)
    return duplicates


def _cr22_unallowed_green_claim_refs(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    refs: list[str] = []
    for row in rows:
        command_ref = clean_identifier(row.get("command_ref"), default="unknown_command", max_length=160)
        if row.get("full_backend_suite_green_claimed") is True:
            refs.append(f"{command_ref}:full_backend_suite_green_claimed")
        if row.get("rn_contract_green_claimed") is True:
            refs.append(f"{command_ref}:rn_contract_green_claimed")
        if row.get("rn_real_device_modal_claimed") is True:
            refs.append(f"{command_ref}:rn_real_device_modal_claimed")
        for claim_key in (
            "actual_human_review_complete_claimed_by_command",
            "p5_final_claimed",
            "p6_start_claimed",
            "p8_start_claimed",
            "r52_actual_execution_claimed",
            "p7_complete_claimed",
            "release_allowed_claimed",
        ):
            if row.get(claim_key) is True:
                refs.append(f"{command_ref}:{claim_key}")
    return _dedupe_string_refs(refs, limit=80, max_length=220)


def build_p7_r54_ahr_cr22_validation_command_matrix_documentation_output(
    cr21_validation: Mapping[str, Any] | None = None,
    command_rows: Sequence[Mapping[str, Any]] | None = None,
    *,
    result_memo_ref: Any = P7_R54_AHR_CR22_DEFAULT_RESULT_MEMO_REF,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build CR22 validation command matrix / documentation output body-free."""
    session_id = clean_identifier(
        review_session_id,
        default=P7_R54_AHR_CR_DEFAULT_REVIEW_SESSION_ID,
        max_length=160,
    )
    cr21 = cr21_validation if isinstance(cr21_validation, Mapping) else {}
    rows, forbidden_row_key_refs = _cr22_command_rows(command_rows)
    command_refs = [str(row.get("command_ref")) for row in rows if row.get("command_ref")]
    duplicate_command_refs = _cr22_duplicate_command_refs(command_refs)
    missing_command_refs = [ref for ref in P7_R54_AHR_CR22_REQUIRED_COMMAND_REFS if ref not in command_refs]
    by_ref = {str(row.get("command_ref")): row for row in rows}
    nonpassed_required_refs = [
        ref
        for ref in P7_R54_AHR_CR22_REQUIRED_PASS_COMMAND_REFS
        if by_ref.get(ref, {}).get("command_status_ref") != P7_R54_AHR_CR22_COMMAND_STATUS_PASSED_REF
    ]
    claimed_required_not_claimed_refs = [
        ref
        for ref in P7_R54_AHR_CR22_REQUIRED_NOT_CLAIMED_COMMAND_REFS
        if by_ref.get(ref, {}).get("command_status_ref") == P7_R54_AHR_CR22_COMMAND_STATUS_PASSED_REF
        or by_ref.get(ref, {}).get("green_claimed") is True
    ]
    unallowed_green_claim_refs = _cr22_unallowed_green_claim_refs(rows)
    result_memo = clean_identifier(
        result_memo_ref,
        default="",
        max_length=220,
    )
    cr21_ready = (
        cr21.get("schema_version") == P7_R54_AHR_CR21_FINAL_NO_BODY_NO_QUESTION_NO_TOUCH_VALIDATION_SCHEMA_VERSION
        and cr21.get("final_validation_passed") is True
        and cr21.get("no_body_leak_validation_passed") is True
        and cr21.get("no_question_text_validation_passed") is True
        and cr21.get("no_touch_validation_passed") is True
        and cr21.get("next_required_step") == P7_R54_AHR_CR22_STEP_REF
    )
    blockers: list[str] = []
    if not cr21_ready:
        blockers.append(P7_R54_AHR_CR22_CR21_NOT_READY_BLOCKER_REF)
    if missing_command_refs:
        blockers.append(P7_R54_AHR_CR22_MISSING_COMMAND_BLOCKER_REF)
    if duplicate_command_refs:
        blockers.append(P7_R54_AHR_CR22_DUPLICATE_COMMAND_BLOCKER_REF)
    if nonpassed_required_refs:
        blockers.append(P7_R54_AHR_CR22_REQUIRED_PASS_COMMAND_NOT_PASSED_BLOCKER_REF)
    if claimed_required_not_claimed_refs:
        blockers.append(P7_R54_AHR_CR22_REQUIRED_NOT_CLAIMED_COMMAND_CLAIMED_BLOCKER_REF)
    if forbidden_row_key_refs:
        blockers.append(P7_R54_AHR_CR22_FORBIDDEN_KEY_BLOCKER_REF)
    if not result_memo:
        blockers.append(P7_R54_AHR_CR22_RESULT_MEMO_REF_MISSING_BLOCKER_REF)
    if unallowed_green_claim_refs:
        blockers.append(P7_R54_AHR_CR22_UNALLOWED_GREEN_CLAIM_BLOCKER_REF)
    blockers = _dedupe_string_refs(blockers, limit=50, max_length=220)
    ready = not blockers
    evidence_ready = bool(ready and cr21.get("actual_review_evidence_complete") is True)
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CR22_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CR_STEP,
        "scope": P7_R54_AHR_CR_SCOPE,
        "policy_kind": P7_R54_AHR_CR_POLICY_KIND,
        "policy_section": P7_R54_AHR_CR22_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CR22_STEP_REF,
        "current_phase": P7_R54_AHR_CR_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cr22_validation_command_matrix_documentation_output_20260628",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cr21_schema_version": cr21.get("schema_version"),
        "cr21_material_ref": cr21.get("material_id"),
        "cr21_next_required_step": cr21.get("next_required_step"),
        "cr21_final_validation_passed": cr21.get("final_validation_passed") is True,
        "cr21_no_body_leak_validation_passed": cr21.get("no_body_leak_validation_passed") is True,
        "cr21_no_question_text_validation_passed": cr21.get("no_question_text_validation_passed") is True,
        "cr21_no_touch_validation_passed": cr21.get("no_touch_validation_passed") is True,
        "cr21_actual_review_evidence_complete": cr21.get("actual_review_evidence_complete") is True,
        **_current_received_basis_fields(actual_basis=True),
        **_historical_basis_fields(),
        "documentation_output_status_ref": P7_R54_AHR_CR22_READY_STATUS_REF if ready else P7_R54_AHR_CR22_BLOCKED_STATUS_REF,
        "documentation_output_allowed_status_refs": list(P7_R54_AHR_CR22_ALLOWED_STATUS_REFS),
        "documentation_output_ready": ready,
        "documentation_output_reason_refs": [P7_R54_AHR_CR22_READY_REASON_REF] if ready else [],
        "documentation_output_step_blocker_refs": blockers,
        "documentation_output_step_blocker_ref_count": len(blockers),
        "validation_matrix_ref": P7_R54_AHR_CR22_VALIDATION_MATRIX_REF,
        "validation_command_rows": rows,
        "validation_command_row_count": len(rows),
        "validation_command_refs": command_refs,
        "validation_command_ref_count": len(command_refs),
        "required_validation_command_refs": list(P7_R54_AHR_CR22_REQUIRED_COMMAND_REFS),
        "required_validation_command_ref_count": len(P7_R54_AHR_CR22_REQUIRED_COMMAND_REFS),
        "required_pass_validation_command_refs": list(P7_R54_AHR_CR22_REQUIRED_PASS_COMMAND_REFS),
        "required_pass_validation_command_ref_count": len(P7_R54_AHR_CR22_REQUIRED_PASS_COMMAND_REFS),
        "required_not_claimed_validation_command_refs": list(P7_R54_AHR_CR22_REQUIRED_NOT_CLAIMED_COMMAND_REFS),
        "required_not_claimed_validation_command_ref_count": len(P7_R54_AHR_CR22_REQUIRED_NOT_CLAIMED_COMMAND_REFS),
        "missing_validation_command_refs": missing_command_refs,
        "missing_validation_command_ref_count": len(missing_command_refs),
        "duplicate_validation_command_refs": duplicate_command_refs,
        "duplicate_validation_command_ref_count": len(duplicate_command_refs),
        "nonpassed_required_validation_command_refs": nonpassed_required_refs,
        "nonpassed_required_validation_command_ref_count": len(nonpassed_required_refs),
        "claimed_required_not_claimed_command_refs": claimed_required_not_claimed_refs,
        "claimed_required_not_claimed_command_ref_count": len(claimed_required_not_claimed_refs),
        "unallowed_green_claim_refs": unallowed_green_claim_refs,
        "unallowed_green_claim_ref_count": len(unallowed_green_claim_refs),
        "forbidden_command_row_key_refs": forbidden_row_key_refs,
        "forbidden_command_row_key_ref_count": len(forbidden_row_key_refs),
        "target_tests_documented": all(ref in command_refs for ref in (
            P7_R54_AHR_CR22_TARGET_CR00_TO_CR22_COMMAND_REF,
        )),
        "selected_regression_documented": all(ref in command_refs for ref in (
            P7_R54_AHR_CR22_SELECTED_CS_COMMAND_REF,
            P7_R54_AHR_CR22_SELECTED_SMOKE_COMMAND_REF,
        )),
        "compileall_documented": P7_R54_AHR_CR22_COMPILEALL_COMMAND_REF in command_refs,
        "claim_boundary_documented": all(ref in command_refs for ref in P7_R54_AHR_CR22_REQUIRED_NOT_CLAIMED_COMMAND_REFS),
        "result_memo_ref": result_memo,
        "result_memo_ref_present": bool(result_memo),
        "result_memo_kind_ref": P7_R54_AHR_CR22_RESULT_MEMO_KIND_REF,
        "result_memo_bodyfree_only": True,
        "result_memo_raw_output_included": False,
        "result_memo_question_text_included": False,
        "result_memo_local_path_included": False,
        "result_memo_materialized_here": ready,
        "validation_matrix_materialized_here": ready,
        "documentation_claim_boundary_refs": list(P7_R54_AHR_CR22_CLAIM_BOUNDARY_REFS),
        "documentation_claim_boundary_ref_count": len(P7_R54_AHR_CR22_CLAIM_BOUNDARY_REFS),
        "actual_human_review_complete_documented_from_cr21_predicate_only": evidence_ready,
        "actual_human_review_newly_run_here": False,
        "full_backend_suite_green_unclaimed": True,
        "rn_contract_green_unclaimed_unless_actually_run": True,
        "rn_real_device_modal_verified_unclaimed": True,
        "selected_regression_green_is_not_full_backend_suite_green": True,
        "rn_contract_green_is_not_rn_real_device_modal_verified": True,
        "r52_handoff_ready_is_not_r52_reintake_executed": True,
        "p5_confirmed_candidate_is_not_p5_final": True,
        "p6_candidate_only_is_not_p6_start_allowed": True,
        "p8_material_candidate_only_is_not_p8_start_allowed": True,
        "actual_human_review_complete": evidence_ready,
        "actual_review_evidence_complete": evidence_ready,
        "actual_rating_rows_materialized_here": evidence_ready,
        "actual_question_need_observation_rows_materialized_here": evidence_ready,
        "actual_disposal_receipt_materialized_here": evidence_ready,
        "disposal_verified": evidence_ready,
        "actual_human_review_executed_by_person": evidence_ready,
        "actual_human_review_run_here": False,
        "actual_human_review_operation_run": False,
        "r52_reintake_execution_allowed_here": False,
        "r52_reintake_execution_started_here": False,
        "r52_reintake_execution_completed_here": False,
        "r52_reintake_execution_requested_here": False,
        "actual_r52_reintake_execution_confirmed": False,
        "p5_human_blind_qa_confirmed_final": False,
        "p5_confirmed_final": False,
        "p5_final_allowed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_start_allowed": False,
        "p8_start_allowed": False,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "p8_question_implementation_spec_finalized_here": False,
        "p7_complete": False,
        "release_allowed": False,
        "full_backend_suite_green_confirmed": False,
        "rn_contract_green_confirmed": False,
        "rn_real_device_modal_verified": False,
        "implemented_steps": list(P7_R54_AHR_CR22_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CR21_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_CR22_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CR21_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_CR22_COMPLETE_NEXT_REQUIRED_STEP_REF if ready else P7_R54_AHR_CR22_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    for flag_ref in P7_R54_AHR_CR22_ALLOWED_TRUE_OPERATION_FLAG_REFS:
        material[flag_ref] = evidence_ready
    for flag_ref in (
        "actual_human_review_run_here",
        "actual_human_review_operation_run",
        "r52_reintake_execution_allowed_here",
        "r52_reintake_execution_started_here",
        "r52_reintake_execution_completed_here",
        "r52_reintake_execution_requested_here",
        "actual_r52_reintake_execution_confirmed",
        "p5_human_blind_qa_confirmed_final",
        "p5_confirmed_final",
        "p5_final_allowed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "question_text_materialized_here",
        "draft_question_text_materialized_here",
        "p8_question_implementation_spec_finalized_here",
        "p7_complete",
        "release_allowed",
        "full_backend_suite_green_confirmed",
        "rn_contract_green_confirmed",
        "rn_real_device_modal_verified",
    ):
        material[flag_ref] = False
    return material


def assert_p7_r54_ahr_cr22_validation_command_matrix_documentation_output_contract(
    data: Mapping[str, Any]
) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CR22_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CR22 validation command matrix documentation",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CR22_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CR22_STEP_REF,
        operation_step_ref=P7_R54_AHR_CR22_STEP_REF,
        source="P7-R54-AHR-CR22 validation command matrix documentation",
        allowed_true_false_flag_refs=P7_R54_AHR_CR22_ALLOWED_TRUE_OPERATION_FLAG_REFS,
    )
    _assert_current_received_basis_fields(data, actual_basis=True, source="P7-R54-AHR-CR22 documentation")
    _assert_historical_basis_fields(data, source="P7-R54-AHR-CR22 documentation")
    if tuple(data.get("documentation_output_allowed_status_refs") or ()) != P7_R54_AHR_CR22_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-CR22 allowed status refs changed")
    rows = data.get("validation_command_rows")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)):
        raise ValueError("P7-R54-AHR-CR22 command rows must be a sequence")
    command_refs = list(data.get("validation_command_refs") or [])
    count_pairs = (
        ("validation_command_rows", "validation_command_row_count"),
        ("validation_command_refs", "validation_command_ref_count"),
        ("required_validation_command_refs", "required_validation_command_ref_count"),
        ("required_pass_validation_command_refs", "required_pass_validation_command_ref_count"),
        ("required_not_claimed_validation_command_refs", "required_not_claimed_validation_command_ref_count"),
        ("missing_validation_command_refs", "missing_validation_command_ref_count"),
        ("duplicate_validation_command_refs", "duplicate_validation_command_ref_count"),
        ("nonpassed_required_validation_command_refs", "nonpassed_required_validation_command_ref_count"),
        ("claimed_required_not_claimed_command_refs", "claimed_required_not_claimed_command_ref_count"),
        ("unallowed_green_claim_refs", "unallowed_green_claim_ref_count"),
        ("forbidden_command_row_key_refs", "forbidden_command_row_key_ref_count"),
        ("documentation_claim_boundary_refs", "documentation_claim_boundary_ref_count"),
        ("documentation_output_step_blocker_refs", "documentation_output_step_blocker_ref_count"),
    )
    for field, count_field in count_pairs:
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-CR22 {count_field} changed")
    if tuple(data.get("required_validation_command_refs") or ()) != P7_R54_AHR_CR22_REQUIRED_COMMAND_REFS:
        raise ValueError("P7-R54-AHR-CR22 required command refs changed")
    if tuple(data.get("required_pass_validation_command_refs") or ()) != P7_R54_AHR_CR22_REQUIRED_PASS_COMMAND_REFS:
        raise ValueError("P7-R54-AHR-CR22 required pass command refs changed")
    if tuple(data.get("required_not_claimed_validation_command_refs") or ()) != P7_R54_AHR_CR22_REQUIRED_NOT_CLAIMED_COMMAND_REFS:
        raise ValueError("P7-R54-AHR-CR22 required not-claimed command refs changed")
    if tuple(data.get("documentation_claim_boundary_refs") or ()) != P7_R54_AHR_CR22_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-CR22 claim boundary refs changed")
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("P7-R54-AHR-CR22 command row must be a mapping")
        if set(row.keys()) != set(P7_R54_AHR_CR22_COMMAND_ROW_REQUIRED_FIELD_REFS):
            raise ValueError("P7-R54-AHR-CR22 command row fields changed")
        if tuple(row.get("command_status_allowed_refs") or ()) != P7_R54_AHR_CR22_ALLOWED_COMMAND_STATUS_REFS:
            raise ValueError("P7-R54-AHR-CR22 command row status refs changed")
        if row.get("body_free") is not True:
            raise ValueError("P7-R54-AHR-CR22 command row must remain body-free")
        for leak_flag in (
            "raw_terminal_output_included",
            "terminal_output_body_included",
            "stdout_body_included",
            "stderr_body_included",
            "traceback_body_included",
            "local_absolute_path_included",
            "body_hash_included",
        ):
            if row.get(leak_flag) is not False:
                raise ValueError("P7-R54-AHR-CR22 command row leak flag changed")
        if row.get("passed") is not (row.get("command_status_ref") == P7_R54_AHR_CR22_COMMAND_STATUS_PASSED_REF):
            raise ValueError("P7-R54-AHR-CR22 command row passed flag changed")
    ready = (
        data.get("cr21_schema_version") == P7_R54_AHR_CR21_FINAL_NO_BODY_NO_QUESTION_NO_TOUCH_VALIDATION_SCHEMA_VERSION
        and data.get("cr21_final_validation_passed") is True
        and data.get("cr21_no_body_leak_validation_passed") is True
        and data.get("cr21_no_question_text_validation_passed") is True
        and data.get("cr21_no_touch_validation_passed") is True
        and data.get("cr21_next_required_step") == P7_R54_AHR_CR22_STEP_REF
        and data.get("missing_validation_command_refs") == []
        and data.get("duplicate_validation_command_refs") == []
        and data.get("nonpassed_required_validation_command_refs") == []
        and data.get("claimed_required_not_claimed_command_refs") == []
        and data.get("forbidden_command_row_key_refs") == []
        and data.get("unallowed_green_claim_refs") == []
        and data.get("result_memo_ref_present") is True
        and data.get("target_tests_documented") is True
        and data.get("selected_regression_documented") is True
        and data.get("compileall_documented") is True
        and data.get("claim_boundary_documented") is True
    )
    if data.get("documentation_output_ready") is not ready:
        raise ValueError("P7-R54-AHR-CR22 ready flag changed")
    if data.get("documentation_output_status_ref") != (P7_R54_AHR_CR22_READY_STATUS_REF if ready else P7_R54_AHR_CR22_BLOCKED_STATUS_REF):
        raise ValueError("P7-R54-AHR-CR22 status changed")
    evidence_ready = bool(ready and data.get("cr21_actual_review_evidence_complete") is True)
    for flag_ref in P7_R54_AHR_CR22_ALLOWED_TRUE_OPERATION_FLAG_REFS:
        if data.get(flag_ref) is not evidence_ready:
            raise ValueError(f"P7-R54-AHR-CR22 {flag_ref} predicate changed")
    _assert_false_fields(
        data,
        keys=(
            "actual_human_review_run_here",
            "actual_human_review_operation_run",
            "r52_reintake_execution_allowed_here",
            "r52_reintake_execution_started_here",
            "r52_reintake_execution_completed_here",
            "r52_reintake_execution_requested_here",
            "actual_r52_reintake_execution_confirmed",
            "p5_human_blind_qa_confirmed_final",
            "p5_confirmed_final",
            "p5_final_allowed",
            "p6_limited_human_readfeel_start_allowed",
            "p6_start_allowed",
            "p8_start_allowed",
            "question_text_materialized_here",
            "draft_question_text_materialized_here",
            "p8_question_implementation_spec_finalized_here",
            "p7_complete",
            "release_allowed",
            "full_backend_suite_green_confirmed",
            "rn_contract_green_confirmed",
            "rn_real_device_modal_verified",
            "result_memo_raw_output_included",
            "result_memo_question_text_included",
            "result_memo_local_path_included",
        ),
        source="P7-R54-AHR-CR22 false promotions",
    )
    _assert_true_fields(
        data,
        keys=(
            "full_backend_suite_green_unclaimed",
            "rn_contract_green_unclaimed_unless_actually_run",
            "rn_real_device_modal_verified_unclaimed",
            "selected_regression_green_is_not_full_backend_suite_green",
            "rn_contract_green_is_not_rn_real_device_modal_verified",
            "r52_handoff_ready_is_not_r52_reintake_executed",
            "p5_confirmed_candidate_is_not_p5_final",
            "p6_candidate_only_is_not_p6_start_allowed",
            "p8_material_candidate_only_is_not_p8_start_allowed",
            "result_memo_bodyfree_only",
        ),
        source="P7-R54-AHR-CR22 claim boundary",
    )
    if ready:
        if data.get("documentation_output_step_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-CR22 ready documentation cannot carry blockers")
        if data.get("documentation_output_reason_refs") != [P7_R54_AHR_CR22_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-CR22 ready reason changed")
        if data.get("result_memo_materialized_here") is not True or data.get("validation_matrix_materialized_here") is not True:
            raise ValueError("P7-R54-AHR-CR22 ready documentation materialization changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CR22_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CR22 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CR22_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CR22 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_CR22_COMPLETE_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CR22 complete next step changed")
    else:
        if not data.get("documentation_output_step_blocker_refs"):
            raise ValueError("P7-R54-AHR-CR22 blocked documentation must carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_CR22_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CR22 blocked next step changed")
    return True


# Alias names for CR20-CR22 design/documentation wording.
def build_p7_r54_ahr_current_received_actual_local_review_operation_r52_handoff_candidate_envelope_bodyfree(
    *,
    cr16_summary: Mapping[str, Any] | None = None,
    cr17_p5_decision: Mapping[str, Any] | None = None,
    cr18_p6_candidate: Mapping[str, Any] | None = None,
    cr19_p8_candidate: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_cr20_r52_handoff_candidate_envelope(
        cr16_summary=cr16_summary,
        cr17_p5_decision=cr17_p5_decision,
        cr18_p6_candidate=cr18_p6_candidate,
        cr19_p8_candidate=cr19_p8_candidate,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_current_received_actual_local_review_operation_r52_handoff_candidate_envelope_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_cr20_r52_handoff_candidate_envelope_contract(data)


def build_p7_r54_ahr_current_received_actual_local_review_operation_final_no_body_leak_no_question_text_no_touch_validation_bodyfree(
    materials: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None = None,
    *,
    cr20_handoff_candidate_envelope: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_cr21_final_no_body_leak_no_question_text_no_touch_validation(
        materials=materials,
        cr20_handoff_candidate_envelope=cr20_handoff_candidate_envelope,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_current_received_actual_local_review_operation_final_no_body_leak_no_question_text_no_touch_validation_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_cr21_final_no_body_leak_no_question_text_no_touch_validation_contract(data)


def build_p7_r54_ahr_current_received_actual_local_review_operation_validation_command_matrix_documentation_output_bodyfree(
    cr21_validation: Mapping[str, Any] | None = None,
    command_rows: Sequence[Mapping[str, Any]] | None = None,
    *,
    result_memo_ref: Any = P7_R54_AHR_CR22_DEFAULT_RESULT_MEMO_REF,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_cr22_validation_command_matrix_documentation_output(
        cr21_validation=cr21_validation,
        command_rows=command_rows,
        result_memo_ref=result_memo_ref,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_current_received_actual_local_review_operation_validation_command_matrix_documentation_output_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_cr22_validation_command_matrix_documentation_output_contract(data)
