# -*- coding: utf-8 -*-
"""P7-R54 current snapshot local review run CLR08-CLR09 helpers.

CLR08 performs only a body-free packet completeness / export-denylist scan.
CLR09 freezes only a body-free selection-only reviewer form.  This helper does
not generate packet bodies, run human review, materialize rating/question rows,
verify disposal, or touch API/DB/RN/runtime/P8/release surfaces.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import (
    P7_PHASE,
    P7_SOURCE_MODE,
    assert_p7_no_body_payload_or_contract_mutation,
    clean_identifier,
    dedupe_identifiers,
    public_contract_flags,
    safe_mapping,
)
import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as r54op
import emlis_ai_p7_r54_actual_review_execution_evidence_materialization_20260626 as r54ev
import emlis_ai_p7_r54_current_snapshot_local_review_run_20260627 as clr03
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr04_clr05_20260627 as clr05
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr06_clr07_20260627 as clr07


P7_R54_CLR08_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr08_packet_completeness_export_denylist_scan.bodyfree.v1"
)
P7_R54_CLR09_REVIEWER_SELECTION_FORM_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr09_reviewer_selection_form_freeze.bodyfree.v1"
)

P7_R54_CLR08_SCHEMA_VERSION: Final = P7_R54_CLR08_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION
P7_R54_CLR09_SCHEMA_VERSION: Final = P7_R54_CLR09_REVIEWER_SELECTION_FORM_FREEZE_SCHEMA_VERSION

P7_R54_CLR_STEP: Final = clr03.P7_R54_CLR_STEP
P7_R54_CLR_SCOPE: Final = clr03.P7_R54_CLR_SCOPE
P7_R54_CLR_POLICY_KIND: Final = clr03.P7_R54_CLR_POLICY_KIND
P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID: Final = clr03.P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID
P7_R54_CLR08_STEP_REF: Final = clr03.P7_R54_CLR08_STEP_REF
P7_R54_CLR09_STEP_REF: Final = clr03.P7_R54_CLR09_STEP_REF
P7_R54_CLR10_STEP_REF: Final = clr03.P7_R54_CLR10_STEP_REF

P7_R54_CLR08_PACKET_SCAN_READY_STATUS_REF: Final = "PACKET_SCAN_READY"
P7_R54_CLR08_PACKET_SCAN_BLOCKED_STATUS_REF: Final = "PACKET_SCAN_BLOCKED_BY_PACKET_GENERATION_RECEIPT"
P7_R54_CLR08_PACKET_SCAN_BLOCKED_INCOMPLETE_STATUS_REF: Final = "PACKET_SCAN_BLOCKED_INCOMPLETE"
P7_R54_CLR08_PACKET_SCAN_BLOCKED_BY_EXPORT_DENYLIST_STATUS_REF: Final = "PACKET_SCAN_BLOCKED_BY_EXPORT_DENYLIST"
P7_R54_CLR08_PACKET_SCAN_BLOCKED_BY_LEAK_STATUS_REF: Final = P7_R54_CLR08_PACKET_SCAN_BLOCKED_BY_EXPORT_DENYLIST_STATUS_REF
P7_R54_CLR08_ALLOWED_PACKET_SCAN_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_CLR08_PACKET_SCAN_READY_STATUS_REF,
    P7_R54_CLR08_PACKET_SCAN_BLOCKED_STATUS_REF,
    P7_R54_CLR08_PACKET_SCAN_BLOCKED_INCOMPLETE_STATUS_REF,
    P7_R54_CLR08_PACKET_SCAN_BLOCKED_BY_EXPORT_DENYLIST_STATUS_REF,
)
P7_R54_CLR08_PACKET_SCAN_REF: Final = "r54_clr08_packet_completeness_export_denylist_scan_bodyfree_20260627"
P7_R54_CLR08_PACKET_SCAN_POLICY_REF: Final = "packet_scan_bodyfree_refs_counts_booleans_only_no_content_no_path_no_hash"
P7_R54_CLR08_READY_REASON_REF: Final = "r54_clr08_packet_completeness_and_export_denylist_scan_ready_bodyfree"
P7_R54_CLR08_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "R54-CLR-08_packet_scan_repair_required_before_reviewer_form"
P7_R54_CLR08_REQUIRED_PACKET_FIELD_REFS: Final[tuple[str, ...]] = r54op.P7_R54_OP08_REQUIRED_PACKET_FIELD_REFS
P7_R54_CLR08_PACKET_SCAN_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "case_index",
    "packet_ref_id",
    "blind_case_id",
    "required_fields_present",
    "packet_present_local_only",
    "packet_present_local_only_by_receipt_ref_only",
    "export_denylist_violation",
    "body_full_packet_export_candidate",
    "required_packet_field_refs",
    "required_packet_field_ref_count",
    "packet_content_included",
    "raw_body_included",
    "returned_emlis_body_included",
    "history_surface_included",
    "reviewer_free_text_included",
    "local_path_included",
    "local_absolute_path_included",
    "body_hash_included",
    "question_text_included",
    "draft_question_text_included",
    "terminal_output_body_included",
    "body_free",
)
P7_R54_CLR08_SCAN_ROW_REQUIRED_FIELD_REFS: Final = P7_R54_CLR08_PACKET_SCAN_ROW_REQUIRED_FIELD_REFS
P7_R54_CLR08_PACKET_SCAN_ROW_FIELD_REFS: Final = P7_R54_CLR08_PACKET_SCAN_ROW_REQUIRED_FIELD_REFS

P7_R54_CLR09_REVIEWER_SELECTION_FORM_READY_STATUS_REF: Final = "REVIEWER_SELECTION_FORM_FROZEN_BODYFREE"
P7_R54_CLR09_REVIEWER_SELECTION_FORM_BLOCKED_STATUS_REF: Final = "REVIEWER_SELECTION_FORM_BLOCKED_BY_PACKET_SCAN"
P7_R54_CLR09_FORM_READY_STATUS_REF: Final = P7_R54_CLR09_REVIEWER_SELECTION_FORM_READY_STATUS_REF
P7_R54_CLR09_FORM_BLOCKED_STATUS_REF: Final = P7_R54_CLR09_REVIEWER_SELECTION_FORM_BLOCKED_STATUS_REF
P7_R54_CLR09_ALLOWED_FORM_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_CLR09_REVIEWER_SELECTION_FORM_READY_STATUS_REF,
    P7_R54_CLR09_REVIEWER_SELECTION_FORM_BLOCKED_STATUS_REF,
)
P7_R54_CLR09_REVIEWER_SELECTION_FORM_REF: Final = "r54_clr09_reviewer_selection_form_bodyfree_20260627"
P7_R54_CLR09_REVIEWER_SELECTION_FORM_POLICY_REF: Final = "selection_only_bodyfree_no_free_text_no_question_text_no_paths_no_hashes_20260627"
P7_R54_CLR09_REVIEWER_FORM_POLICY_REF: Final = P7_R54_CLR09_REVIEWER_SELECTION_FORM_POLICY_REF
P7_R54_CLR09_REVIEWER_INSTRUCTION_REF: Final = "r54_clr09_reviewer_instruction_selection_only_no_free_text_20260627"
P7_R54_CLR09_RATING_FORM_REF: Final = "r54_clr09_p5_human_blind_qa_rating_form_bodyfree_20260627"
P7_R54_CLR09_READY_REASON_REF: Final = "r54_clr09_reviewer_selection_form_frozen_bodyfree"
P7_R54_CLR09_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "R54-CLR-09_blocked_until_clr08_packet_scan_ready"
P7_R54_CLR09_SELECTION_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *r54ev.P7_R54_EV08_REQUIRED_SELECTION_FIELD_REFS[:5],
    "axis_scores",
    "overall_read_feeling_ref",
    *r54ev.P7_R54_EV08_REQUIRED_SELECTION_FIELD_REFS[6:],
)
P7_R54_CLR09_RATING_AXIS_REFS: Final[tuple[str, ...]] = r54ev.P7_R54_EV08_RATING_AXIS_REFS
P7_R54_CLR09_RATING_AXIS_TARGET_THRESHOLDS: Final[dict[str, float]] = dict(r54ev.P7_R54_EV08_RATING_AXIS_TARGET_THRESHOLDS)
P7_R54_CLR09_SCORE_OPTION_REFS: Final[tuple[float, ...]] = r54ev.P7_R54_EV08_SCORE_OPTION_REFS
P7_R54_CLR09_VERDICT_OPTION_REFS: Final[tuple[str, ...]] = r54ev.P7_R54_EV08_VERDICT_OPTION_REFS
P7_R54_CLR09_OVERALL_READ_FEELING_OPTION_REFS: Final[tuple[str, ...]] = (
    "felt_record_returned_as_line",
    "felt_generic_or_shallow",
    "felt_creepy_or_overread",
    "felt_current_input_overridden_by_history",
    "felt_not_reviewable",
)
P7_R54_CLR09_READFEEL_BLOCKER_OPTION_REFS: Final[tuple[str, ...]] = r54ev.P7_R54_EV08_READFEEL_BLOCKER_ID_OPTION_REFS
P7_R54_CLR09_EXECUTION_BLOCKER_OPTION_REFS: Final[tuple[str, ...]] = r54ev.P7_R54_EV08_EXECUTION_BLOCKER_ID_OPTION_REFS
P7_R54_CLR09_QUESTION_NEED_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = r54ev.P7_R54_EV08_QUESTION_NEED_PRIMARY_CLASS_REFS
P7_R54_CLR09_AMBIGUITY_KIND_OPTION_REFS: Final[tuple[str, ...]] = r54ev.P7_R54_EV08_AMBIGUITY_KIND_OPTION_REFS
P7_R54_CLR09_ONE_QUESTION_FIT_OPTION_REFS: Final[tuple[str, ...]] = r54ev.P7_R54_EV08_ONE_QUESTION_FIT_OPTION_REFS
P7_R54_CLR09_REPAIR_REQUIRED_OPTION_REFS: Final[tuple[str, ...]] = r54ev.P7_R54_EV08_REPAIR_REQUIRED_OPTION_REFS
P7_R54_CLR09_PLAN_CANDIDATE_FLAG_REFS: Final[tuple[str, ...]] = r54ev.P7_R54_EV08_PLAN_CANDIDATE_FLAG_REFS

P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR08: Final[tuple[str, ...]] = clr03.P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR01[7:]
P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR09: Final[tuple[str, ...]] = clr03.P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR01[8:]
P7_R54_CLR08_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*clr07.P7_R54_CLR07_IMPLEMENTED_STEPS, P7_R54_CLR08_STEP_REF)
P7_R54_CLR08_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR08
P7_R54_CLR09_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_CLR08_IMPLEMENTED_STEPS, P7_R54_CLR09_STEP_REF)
P7_R54_CLR09_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR09

P7_R54_CLR08_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *clr03.P7_R54_CLR_COMMON_REQUIRED_FIELD_REFS,
    "clr06_request_ready",
    "clr07_schema_version",
    "clr07_material_ref",
    "clr07_next_required_step",
    "clr07_packet_generation_status",
    "clr07_receipt_ready",
    "clr07_packet_completeness_export_denylist_scan_allowed_next",
    "existing_op08_helper_ref",
    "existing_op08_schema_version",
    "existing_op08_operation_current_refs",
    "existing_op08_current_refs_are_historical_here",
    "existing_op08_reused_as_actual_packet_scan_basis",
    "existing_op08_structural_contract_reused",
    "required_case_count",
    "packet_scan_status",
    "packet_scan_ref",
    "packet_scan_policy_ref",
    "packet_scan_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "expected_packet_ref_ids",
    "expected_packet_ref_count",
    "declared_packet_ref_ids",
    "declared_packet_ref_count",
    "declared_packet_ref_ids_unique",
    "packet_ref_ids_match_receipt_and_request",
    "packet_scan_rows",
    "packet_scan_row_count",
    "total_case_count",
    "packet_present_count",
    "required_fields_present_count",
    "required_packet_field_refs",
    "required_packet_field_ref_count",
    "packet_completeness_ready",
    "packet_completeness_verified_by_bodyfree_receipt_only",
    "export_denylist_policy_ref",
    "export_denylist_refs",
    "export_denylist_ref_count",
    "export_denylist_violation_refs",
    "export_denylist_violation_count",
    "body_full_packet_export_candidate_refs",
    "body_full_packet_export_candidate_count",
    "body_full_packet_content_detected_in_export",
    "question_text_detected_in_export",
    "local_path_detected_in_export",
    "body_hash_detected_in_export",
    "packet_scan_is_bodyfree_only",
    "packet_scan_contains_packet_content",
    "packet_scan_contains_local_path",
    "packet_scan_contains_local_absolute_path",
    "packet_scan_contains_body_hash",
    "packet_scan_contains_raw_body",
    "packet_scan_contains_returned_body",
    "packet_scan_contains_history_surface",
    "packet_scan_contains_reviewer_free_text",
    "packet_scan_contains_question_text",
    "packet_scan_contains_draft_question_text",
    "packet_scan_contains_terminal_output_body",
    "body_full_packet_content_inspected_here",
    "reviewer_selection_form_freeze_allowed_next",
    "actual_review_execution_blocked_until_reviewer_selection_form",
    "body_full_packet_content_included",
    "body_full_packet_generated_here",
    "actual_body_full_packet_generated_here",
    "local_reviewer_payload_materialized_here",
    "local_review_root_path_included",
    "local_packet_directory_path_included",
    "local_packet_exported",
    "body_full_packet_export_allowed",
    "body_full_packet_zip_inclusion_allowed",
    "reviewer_notes_export_allowed",
    "p5_actual_review_still_not_run",
    "actual_review_evidence_complete",
    "rating_row_count",
    "question_observation_row_count",
    "disposal_verified_before_scan",
    "disposal_verified",
    "actual_human_review_completion_claim_blocked_here",
    "human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    *clr03.P7_R54_CLR_CURRENT_REF_REQUIRED_FIELD_REFS,
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *clr03.P7_R54_CLR_NO_TOUCH_BODYFREE_REQUIRED_FIELD_REFS,
    *clr03.P7_R54_CLR_FALSE_FLAG_REFS,
)

P7_R54_CLR09_REVIEWER_SELECTION_FORM_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *clr03.P7_R54_CLR_COMMON_REQUIRED_FIELD_REFS,
    "clr08_schema_version",
    "clr08_material_ref",
    "clr08_next_required_step",
    "clr08_packet_scan_status",
    "clr08_packet_scan_ready",
    "existing_op09_helper_ref",
    "existing_op09_schema_version",
    "existing_op09_operation_current_refs",
    "existing_op09_current_refs_are_historical_here",
    "existing_op09_reused_as_actual_form_basis",
    "existing_op09_structural_contract_reused",
    "existing_ev08_selection_options_reused",
    "required_case_count",
    "reviewer_selection_form_status",
    "reviewer_selection_form_ref",
    "reviewer_selection_form_policy_ref",
    "reviewer_instruction_ref",
    "rating_form_ref",
    "reviewer_selection_form_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "packet_scan_row_count",
    "packet_present_count",
    "required_fields_present_count",
    "selection_row_required_field_refs",
    "selection_row_required_field_ref_count",
    "rating_axis_refs",
    "rating_axis_count",
    "rating_axis_target_thresholds",
    "score_option_refs",
    "verdict_option_refs",
    "overall_read_feeling_option_refs",
    "readfeel_blocker_id_option_refs",
    "execution_blocker_id_option_refs",
    "question_need_primary_class_options",
    "ambiguity_kind_option_refs",
    "one_question_fit_option_refs",
    "repair_required_option_refs",
    "plan_candidate_flag_refs",
    "selection_only_form",
    "actual_human_review_operation_allowed_next",
    "actual_human_review_operation_state_capture_allowed_next",
    "reviewer_selection_form_materialized_here",
    "rating_form_materialized_here",
    "reviewer_free_text_field_present",
    "reviewer_free_text_export_allowed",
    "raw_body_copy_field_present",
    "question_text_field_present",
    "draft_question_text_field_present",
    "local_path_field_present",
    "local_absolute_path_field_present",
    "body_hash_field_present",
    "packet_content_field_present",
    "terminal_output_body_field_present",
    "rating_form_contains_question_text",
    "rating_form_contains_raw_body_copy",
    "rating_form_contains_local_path",
    "rating_form_contains_local_absolute_path",
    "rating_form_contains_body_hash",
    "rating_form_contains_packet_content",
    "rating_form_contains_terminal_output_body",
    "rating_form_contains_reviewer_free_text_export",
    "actual_human_review_started_here",
    "actual_human_review_run_here",
    "p5_actual_review_still_not_run",
    "actual_review_evidence_complete",
    "rating_row_count",
    "question_observation_row_count",
    "disposal_verified_before_form",
    "disposal_verified_before_review",
    "disposal_verified",
    "actual_human_review_completion_claim_blocked_here",
    "human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    *clr03.P7_R54_CLR_CURRENT_REF_REQUIRED_FIELD_REFS,
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *clr03.P7_R54_CLR_NO_TOUCH_BODYFREE_REQUIRED_FIELD_REFS,
    *clr03.P7_R54_CLR_FALSE_FLAG_REFS,
)


def _false_flags() -> dict[str, bool]:
    return {key: False for key in clr03.P7_R54_CLR_FALSE_FLAG_REFS}


def _body_free_markers() -> dict[str, bool]:
    return dict(clr03._body_free_markers())


def _no_touch_contract() -> dict[str, bool]:
    return dict(clr03._no_touch_contract())


def _current_ref_fields() -> dict[str, Any]:
    refs = dict(clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS)
    keys = list(clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS)
    return {
        "operation_current_refs": refs,
        "operation_current_ref_count": len(refs),
        "operation_current_ref_keys": keys,
        "operation_current_ref_key_count": len(keys),
        "required_current_snapshot_ref_keys": keys,
        "required_current_snapshot_ref_key_count": len(keys),
        "all_required_current_refs_present": True,
        "actual_review_basis_ref": clr03.P7_R54_CLR_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": clr03.P7_R54_CLR_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "operation_current_refs_used_as_actual_review_basis": True,
    }


def _safe_review_session_id(value: Any) -> str:
    return clr03._safe_review_session_id(value)


def _contains_forbidden_key(value: Any) -> bool:
    forbidden = {
        "raw_input", "returned_emlis_body", "history_surface", "reviewer_free_text",
        "reviewer_note", "reviewer_notes", "reviewer_notes_body", "question_text",
        "draft_question_text", "local_path", "local_absolute_path", "body_hash",
        "packet_content", "terminal_output_body", "stdout_body", "stderr_body",
    }
    if isinstance(value, Mapping):
        return any(str(k) in forbidden or _contains_forbidden_key(v) for k, v in value.items())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_key(v) for v in value)
    return False


def _assert_required_fields(data: Mapping[str, Any], *, required: tuple[str, ...], source: str) -> None:
    missing = [key for key in required if key not in data]
    extra = [key for key in data if key not in required]
    if missing:
        raise ValueError(f"{source} missing required fields: {', '.join(missing[:12])}")
    if extra:
        raise ValueError(f"{source} has unexpected fields: {', '.join(extra[:12])}")


def _assert_base(data: Mapping[str, Any], *, schema_version: str, policy_section: str, source: str) -> None:
    if _contains_forbidden_key(data):
        raise ValueError(f"{source} contains forbidden body/question/path/hash key")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)
    if data.get("schema_version") != schema_version:
        raise ValueError(f"{source} schema version changed")
    if data.get("phase") != P7_PHASE or data.get("current_phase") != P7_PHASE:
        raise ValueError(f"{source} phase changed")
    if data.get("step") != P7_R54_CLR_STEP or data.get("scope") != P7_R54_CLR_SCOPE:
        raise ValueError(f"{source} step/scope changed")
    if data.get("policy_kind") != P7_R54_CLR_POLICY_KIND:
        raise ValueError(f"{source} policy kind changed")
    if data.get("policy_section") != policy_section or data.get("operation_step_ref") != policy_section:
        raise ValueError(f"{source} policy section changed")
    if data.get("source_mode") != P7_SOURCE_MODE:
        raise ValueError(f"{source} source mode changed")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} must remain local-only without git")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must remain body-free")
    if any(v is not False for v in safe_mapping(data.get("public_contract")).values()):
        raise ValueError(f"{source} public contract changed")
    if any(v is not False for v in safe_mapping(data.get("r54_clr_no_touch_contract")).values()):
        raise ValueError(f"{source} no-touch contract changed")
    if any(v is not False for v in safe_mapping(data.get("body_free_markers")).values()):
        raise ValueError(f"{source} body-free markers changed")
    for key in clr03.P7_R54_CLR_FALSE_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=False")


def _assert_current_refs(data: Mapping[str, Any], *, source: str) -> None:
    if safe_mapping(data.get("operation_current_refs")) != clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError(f"{source} current refs changed")
    for key in ("all_required_current_refs_present", "operation_current_refs_are_actual_review_basis", "operation_current_refs_used_as_actual_review_basis"):
        if data.get(key) is not True:
            raise ValueError(f"{source} must keep {key}=True")


def _default_request() -> dict[str, Any]:
    req = clr07.build_p7_r54_clr06_body_full_packet_generation_request_bodyfree_evidence()
    clr07.assert_p7_r54_clr06_body_full_packet_generation_request_bodyfree_evidence_contract(req)
    return req


def _default_receipt(request: Mapping[str, Any]) -> dict[str, Any]:
    receipt = clr07.build_p7_r54_clr07_bodyfree_generated_receipt_from_request(request)
    material = clr07.build_p7_r54_clr07_local_packet_generation_operation_receipt_intake(
        body_full_packet_generation_request_bodyfree_evidence=request,
        packet_generation_operation_receipt=receipt,
    )
    clr07.assert_p7_r54_clr07_local_packet_generation_operation_receipt_intake_contract(material)
    return material


def _clean_refs(values: Sequence[Any] | None) -> list[str]:
    return [clean_identifier(v, max_length=180) for v in (values or [])]


def _unique_non_empty(values: Sequence[str], *, required_count: int) -> bool:
    return len(values) == required_count and len(set(values)) == required_count and all(values)


def _blind_case_id_for_packet(packet_ref_id: str, *, index: int) -> str:
    if packet_ref_id.startswith("p7r48-p5-packet-r54clr-"):
        return packet_ref_id.replace("p7r48-p5-packet-r54clr-", "p7r48-p5-bqa-r54clr-")
    return f"p7r54-clr08-blind-case-{index:03d}"


def _scan_row(packet_ref: str, *, index: int, present: bool = True, fields_present: bool = True,
              deny: bool = False, export: bool = False) -> dict[str, Any]:
    return {
        "case_index": index,
        "packet_ref_id": packet_ref,
        "blind_case_id": _blind_case_id_for_packet(packet_ref, index=index),
        "required_fields_present": fields_present,
        "packet_present_local_only": present,
        "packet_present_local_only_by_receipt_ref_only": present,
        "export_denylist_violation": deny,
        "body_full_packet_export_candidate": export,
        "required_packet_field_refs": list(P7_R54_CLR08_REQUIRED_PACKET_FIELD_REFS),
        "required_packet_field_ref_count": len(P7_R54_CLR08_REQUIRED_PACKET_FIELD_REFS),
        "packet_content_included": False,
        "raw_body_included": False,
        "returned_emlis_body_included": False,
        "history_surface_included": False,
        "reviewer_free_text_included": False,
        "local_path_included": False,
        "local_absolute_path_included": False,
        "body_hash_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "terminal_output_body_included": False,
        "body_free": True,
    }


def _assert_scan_row(row: Mapping[str, Any]) -> None:
    _assert_required_fields(row, required=P7_R54_CLR08_PACKET_SCAN_ROW_REQUIRED_FIELD_REFS, source="P7-R54-CLR08 scan row")
    if _contains_forbidden_key(row):
        raise ValueError("P7-R54-CLR08 scan row contains forbidden key")
    assert_p7_no_body_payload_or_contract_mutation(row, source="P7-R54-CLR08 scan row")
    if row.get("body_free") is not True:
        raise ValueError("P7-R54-CLR08 scan row must remain body-free")
    for key in (
        "packet_content_included", "raw_body_included", "returned_emlis_body_included",
        "history_surface_included", "reviewer_free_text_included", "local_path_included",
        "local_absolute_path_included", "body_hash_included", "question_text_included",
        "draft_question_text_included", "terminal_output_body_included",
    ):
        if row.get(key) is not False:
            raise ValueError(f"P7-R54-CLR08 scan row must keep {key}=False")


def build_p7_r54_clr08_packet_completeness_export_denylist_scan(
    *,
    body_full_packet_generation_request_bodyfree_evidence: Mapping[str, Any] | None = None,
    local_packet_generation_operation_receipt_intake: Mapping[str, Any] | None = None,
    declared_packet_ref_ids: Sequence[Any] | None = None,
    required_fields_present_ref_ids: Sequence[Any] | None = None,
    packet_scan_rows: Sequence[Mapping[str, Any]] | None = None,
    export_denylist_violation_refs: Sequence[Any] | None = None,
    body_full_packet_export_candidate_refs: Sequence[Any] | None = None,
    body_full_packet_content_detected_in_export: bool = False,
    question_text_detected_in_export: bool = False,
    local_path_detected_in_export: bool = False,
    body_hash_detected_in_export: bool = False,
    review_session_id: Any = None,
) -> dict[str, Any]:
    request = dict(body_full_packet_generation_request_bodyfree_evidence or _default_request())
    clr07.assert_p7_r54_clr06_body_full_packet_generation_request_bodyfree_evidence_contract(request)
    receipt = dict(local_packet_generation_operation_receipt_intake or _default_receipt(request))
    clr07.assert_p7_r54_clr07_local_packet_generation_operation_receipt_intake_contract(receipt)
    receipt_ready = bool(
        receipt.get("packet_completeness_export_denylist_scan_allowed_next") is True
        and receipt.get("packet_generation_status") == clr07.P7_R54_CLR07_LOCAL_ONLY_PACKET_GENERATED_STATUS_REF
        and not (receipt.get("open_execution_blocker_ids") or [])
    )
    required_count = clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
    expected_refs = _clean_refs(request.get("packet_ref_ids") or receipt.get("expected_packet_ref_ids")) if receipt_ready else []
    declared_refs = _clean_refs(declared_packet_ref_ids if declared_packet_ref_ids is not None else receipt.get("packet_ref_ids")) if receipt_ready else []
    fields_ok_refs = set(_clean_refs(required_fields_present_ref_ids)) if required_fields_present_ref_ids is not None else set(declared_refs)
    deny_refs = set(_clean_refs(export_denylist_violation_refs))
    export_refs = set(_clean_refs(body_full_packet_export_candidate_refs))

    if receipt_ready:
        if packet_scan_rows is None:
            rows = [
                _scan_row(ref, index=i, fields_present=ref in fields_ok_refs, deny=ref in deny_refs, export=ref in export_refs)
                for i, ref in enumerate(declared_refs, start=1)
            ]
        else:
            rows = [dict(r) for r in packet_scan_rows]
    else:
        rows = []
    for row in rows:
        _assert_scan_row(row)

    row_refs = [clean_identifier(r.get("packet_ref_id"), max_length=180) for r in rows]
    present_count = sum(1 for r in rows if r.get("packet_present_local_only") is True)
    fields_present_count = sum(1 for r in rows if r.get("required_fields_present") is True)
    row_deny_refs = _clean_refs([r["packet_ref_id"] for r in rows if r.get("export_denylist_violation") is True])
    row_export_refs = _clean_refs([r["packet_ref_id"] for r in rows if r.get("body_full_packet_export_candidate") is True])
    deny_list = dedupe_identifiers([*deny_refs, *row_deny_refs], limit=80, max_length=180)
    export_list = dedupe_identifiers([*export_refs, *row_export_refs], limit=80, max_length=180)
    refs_match = bool(receipt_ready and row_refs == expected_refs and declared_refs == expected_refs and len(row_refs) == required_count)
    completeness_ready = bool(refs_match and _unique_non_empty(row_refs, required_count=required_count) and present_count == required_count and fields_present_count == required_count)
    export_leak = bool(deny_list or export_list or body_full_packet_content_detected_in_export or question_text_detected_in_export or local_path_detected_in_export or body_hash_detected_in_export)
    scan_ready = bool(receipt_ready and completeness_ready and not export_leak)

    blockers_seed: list[str] = []
    if not receipt_ready:
        blockers_seed.append("r54_clr08_blocked_until_clr07_bodyfree_packet_generation_receipt_ready")
    if receipt_ready and not refs_match:
        blockers_seed.append("packet_ref_count_or_identity_mismatch")
    if receipt_ready and refs_match and not completeness_ready:
        blockers_seed.append("packet_required_fields_missing")
    if deny_list:
        blockers_seed.append("export_denylist_violation_detected")
    if export_list:
        blockers_seed.append("body_full_packet_export_candidate_detected")
    if body_full_packet_content_detected_in_export:
        blockers_seed.append("body_full_packet_content_detected_in_export")
    if question_text_detected_in_export:
        blockers_seed.append("question_text_detected_in_export")
    if local_path_detected_in_export:
        blockers_seed.append("local_path_detected_in_export")
    if body_hash_detected_in_export:
        blockers_seed.append("body_hash_detected_in_export")
    blockers = dedupe_identifiers([*blockers_seed, *(receipt.get("open_execution_blocker_ids") or [])], limit=80, max_length=180)
    if scan_ready:
        status = P7_R54_CLR08_PACKET_SCAN_READY_STATUS_REF
        reasons = [P7_R54_CLR08_READY_REASON_REF]
    elif not receipt_ready:
        status = P7_R54_CLR08_PACKET_SCAN_BLOCKED_STATUS_REF
        reasons = dedupe_identifiers([status, *blockers], limit=80, max_length=180)
    elif export_leak:
        status = P7_R54_CLR08_PACKET_SCAN_BLOCKED_BY_EXPORT_DENYLIST_STATUS_REF
        reasons = dedupe_identifiers([status, *blockers], limit=80, max_length=180)
    else:
        status = P7_R54_CLR08_PACKET_SCAN_BLOCKED_INCOMPLETE_STATUS_REF
        reasons = dedupe_identifiers([status, *blockers], limit=80, max_length=180)

    material: dict[str, Any] = {
        "schema_version": P7_R54_CLR08_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_CLR_STEP,
        "scope": P7_R54_CLR_SCOPE,
        "policy_kind": P7_R54_CLR_POLICY_KIND,
        "policy_section": P7_R54_CLR08_STEP_REF,
        "operation_step_ref": P7_R54_CLR08_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_clr08_packet_completeness_export_denylist_scan_20260627",
        "review_session_id": _safe_review_session_id(review_session_id or receipt.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "clr06_request_ready": request.get("packet_generation_request_status") == clr07.P7_R54_CLR06_REQUEST_READY_STATUS_REF,
        "clr07_schema_version": receipt.get("schema_version"),
        "clr07_material_ref": receipt.get("material_id"),
        "clr07_next_required_step": receipt.get("next_required_step"),
        "clr07_packet_generation_status": receipt.get("packet_generation_status"),
        "clr07_receipt_ready": receipt_ready,
        "clr07_packet_completeness_export_denylist_scan_allowed_next": receipt.get("packet_completeness_export_denylist_scan_allowed_next") is True,
        "existing_op08_helper_ref": "emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625.build_p7_r54_op08_packet_completeness_export_denylist_scan",
        "existing_op08_schema_version": r54op.P7_R54_OPERATION_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION,
        "existing_op08_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op08_current_refs_are_historical_here": True,
        "existing_op08_reused_as_actual_packet_scan_basis": False,
        "existing_op08_structural_contract_reused": True,
        "required_case_count": required_count,
        "packet_scan_status": status,
        "packet_scan_ref": P7_R54_CLR08_PACKET_SCAN_REF if scan_ready else "packet_scan_not_ready_bodyfree",
        "packet_scan_policy_ref": P7_R54_CLR08_PACKET_SCAN_POLICY_REF,
        "packet_scan_reason_refs": reasons,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "expected_packet_ref_ids": expected_refs,
        "expected_packet_ref_count": len(expected_refs),
        "declared_packet_ref_ids": row_refs,
        "declared_packet_ref_count": len(row_refs),
        "declared_packet_ref_ids_unique": _unique_non_empty(row_refs, required_count=required_count) if row_refs else False,
        "packet_ref_ids_match_receipt_and_request": refs_match,
        "packet_scan_rows": rows,
        "packet_scan_row_count": len(rows),
        "total_case_count": required_count if receipt_ready else 0,
        "packet_present_count": present_count,
        "required_fields_present_count": fields_present_count,
        "required_packet_field_refs": list(P7_R54_CLR08_REQUIRED_PACKET_FIELD_REFS),
        "required_packet_field_ref_count": len(P7_R54_CLR08_REQUIRED_PACKET_FIELD_REFS),
        "packet_completeness_ready": completeness_ready,
        "packet_completeness_verified_by_bodyfree_receipt_only": completeness_ready,
        "export_denylist_policy_ref": clr05.P7_R54_CLR04_EXPORT_DENYLIST_READY_REF,
        "export_denylist_refs": list(clr05.P7_R54_CLR04_EXPORT_DENYLIST_REFS),
        "export_denylist_ref_count": len(clr05.P7_R54_CLR04_EXPORT_DENYLIST_REFS),
        "export_denylist_violation_refs": deny_list,
        "export_denylist_violation_count": len(deny_list),
        "body_full_packet_export_candidate_refs": export_list,
        "body_full_packet_export_candidate_count": len(export_list),
        "body_full_packet_content_detected_in_export": bool(body_full_packet_content_detected_in_export),
        "question_text_detected_in_export": bool(question_text_detected_in_export),
        "local_path_detected_in_export": bool(local_path_detected_in_export),
        "body_hash_detected_in_export": bool(body_hash_detected_in_export),
        "packet_scan_is_bodyfree_only": True,
        "packet_scan_contains_packet_content": False,
        "packet_scan_contains_local_path": False,
        "packet_scan_contains_local_absolute_path": False,
        "packet_scan_contains_body_hash": False,
        "packet_scan_contains_raw_body": False,
        "packet_scan_contains_returned_body": False,
        "packet_scan_contains_history_surface": False,
        "packet_scan_contains_reviewer_free_text": False,
        "packet_scan_contains_question_text": False,
        "packet_scan_contains_draft_question_text": False,
        "packet_scan_contains_terminal_output_body": False,
        "body_full_packet_content_inspected_here": False,
        "reviewer_selection_form_freeze_allowed_next": scan_ready,
        "actual_review_execution_blocked_until_reviewer_selection_form": True,
        "body_full_packet_content_included": False,
        "body_full_packet_generated_here": False,
        "actual_body_full_packet_generated_here": False,
        "local_reviewer_payload_materialized_here": False,
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
        "disposal_verified_before_scan": False,
        "disposal_verified": False,
        "actual_human_review_completion_claim_blocked_here": True,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        **_current_ref_fields(),
        "implemented_steps": list(P7_R54_CLR08_IMPLEMENTED_STEPS if scan_ready else (receipt.get("implemented_steps") or [])),
        "not_yet_implemented_steps": list(P7_R54_CLR08_NOT_YET_IMPLEMENTED_STEPS if scan_ready else (receipt.get("not_yet_implemented_steps") or [])),
        "next_required_step": P7_R54_CLR09_STEP_REF if scan_ready else P7_R54_CLR08_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_clr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_clr08_packet_completeness_export_denylist_scan_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(data, required=P7_R54_CLR08_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_REQUIRED_FIELD_REFS, source="P7-R54-CLR08")
    _assert_base(data, schema_version=P7_R54_CLR08_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION, policy_section=P7_R54_CLR08_STEP_REF, source="P7-R54-CLR08")
    _assert_current_refs(data, source="P7-R54-CLR08")
    if data.get("packet_scan_status") not in P7_R54_CLR08_ALLOWED_PACKET_SCAN_STATUS_REFS:
        raise ValueError("P7-R54-CLR08 packet scan status changed")
    if safe_mapping(data.get("existing_op08_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("P7-R54-CLR08 OP08 refs changed")
    if data.get("existing_op08_current_refs_are_historical_here") is not True or data.get("existing_op08_reused_as_actual_packet_scan_basis") is not False:
        raise ValueError("P7-R54-CLR08 historical OP08 boundary changed")
    if tuple(data.get("required_packet_field_refs") or ()) != P7_R54_CLR08_REQUIRED_PACKET_FIELD_REFS:
        raise ValueError("P7-R54-CLR08 required packet fields changed")
    if tuple(data.get("export_denylist_refs") or ()) != clr05.P7_R54_CLR04_EXPORT_DENYLIST_REFS:
        raise ValueError("P7-R54-CLR08 export denylist changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=80, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("P7-R54-CLR08 blockers mismatch")
    for row in data.get("packet_scan_rows") or []:
        _assert_scan_row(row)
    false_keys = (
        "packet_scan_contains_packet_content", "packet_scan_contains_local_path", "packet_scan_contains_local_absolute_path",
        "packet_scan_contains_body_hash", "packet_scan_contains_raw_body", "packet_scan_contains_returned_body",
        "packet_scan_contains_history_surface", "packet_scan_contains_reviewer_free_text", "packet_scan_contains_question_text",
        "packet_scan_contains_draft_question_text", "packet_scan_contains_terminal_output_body", "body_full_packet_content_inspected_here",
        "body_full_packet_content_included", "body_full_packet_generated_here", "actual_body_full_packet_generated_here",
        "local_reviewer_payload_materialized_here", "local_review_root_path_included", "local_packet_directory_path_included",
        "local_packet_exported", "body_full_packet_export_allowed", "body_full_packet_zip_inclusion_allowed",
        "reviewer_notes_export_allowed", "actual_review_evidence_complete", "actual_human_review_run_here",
        "disposal_verified_before_scan", "disposal_verified",
    )
    for key in false_keys:
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-CLR08 must keep {key}=False")
    if data.get("p5_actual_review_still_not_run") is not True or data.get("actual_review_execution_blocked_until_reviewer_selection_form") is not True:
        raise ValueError("P7-R54-CLR08 review boundary changed")
    if data.get("rating_row_count") != 0 or data.get("question_observation_row_count") != 0:
        raise ValueError("P7-R54-CLR08 must not materialize review rows")
    ready = data.get("packet_scan_status") == P7_R54_CLR08_PACKET_SCAN_READY_STATUS_REF
    if ready:
        if data.get("reviewer_selection_form_freeze_allowed_next") is not True or blockers:
            raise ValueError("P7-R54-CLR08 ready scan must allow CLR09 with no blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_CLR08_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR08 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_CLR08_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR08 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_CLR09_STEP_REF:
            raise ValueError("P7-R54-CLR08 ready next step changed")
        if data.get("packet_scan_row_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-CLR08 ready scan must have 24 rows")
    else:
        if data.get("reviewer_selection_form_freeze_allowed_next") is not False or not blockers:
            raise ValueError("P7-R54-CLR08 blocked scan must carry blockers")
        if P7_R54_CLR08_STEP_REF in tuple(data.get("implemented_steps") or ()): 
            raise ValueError("P7-R54-CLR08 blocked scan must not mark CLR08 implemented")
        if data.get("next_required_step") != P7_R54_CLR08_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-CLR08 blocked next step changed")
    return True


def build_p7_r54_clr09_reviewer_selection_form_freeze(
    *, packet_completeness_export_denylist_scan: Mapping[str, Any] | None = None, review_session_id: Any = None
) -> dict[str, Any]:
    scan = dict(packet_completeness_export_denylist_scan or build_p7_r54_clr08_packet_completeness_export_denylist_scan())
    assert_p7_r54_clr08_packet_completeness_export_denylist_scan_contract(scan)
    scan_ready = bool(
        scan.get("packet_scan_status") == P7_R54_CLR08_PACKET_SCAN_READY_STATUS_REF
        and scan.get("reviewer_selection_form_freeze_allowed_next") is True
        and not (scan.get("open_execution_blocker_ids") or [])
    )
    blockers = [] if scan_ready else dedupe_identifiers(["r54_clr09_blocked_until_clr08_packet_scan_ready", *(scan.get("open_execution_blocker_ids") or [])], limit=100, max_length=180)
    reasons = [P7_R54_CLR09_READY_REASON_REF] if scan_ready else blockers
    material: dict[str, Any] = {
        "schema_version": P7_R54_CLR09_REVIEWER_SELECTION_FORM_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_CLR_STEP,
        "scope": P7_R54_CLR_SCOPE,
        "policy_kind": P7_R54_CLR_POLICY_KIND,
        "policy_section": P7_R54_CLR09_STEP_REF,
        "operation_step_ref": P7_R54_CLR09_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_clr09_reviewer_selection_form_freeze_20260627",
        "review_session_id": _safe_review_session_id(review_session_id or scan.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "clr08_schema_version": scan.get("schema_version"),
        "clr08_material_ref": scan.get("material_id"),
        "clr08_next_required_step": scan.get("next_required_step"),
        "clr08_packet_scan_status": scan.get("packet_scan_status"),
        "clr08_packet_scan_ready": scan_ready,
        "existing_op09_helper_ref": "emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625.build_p7_r54_op09_reviewer_instruction_rating_form_freeze",
        "existing_op09_schema_version": r54op.P7_R54_OPERATION_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION,
        "existing_op09_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op09_current_refs_are_historical_here": True,
        "existing_op09_reused_as_actual_form_basis": False,
        "existing_op09_structural_contract_reused": True,
        "existing_ev08_selection_options_reused": True,
        "required_case_count": clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "reviewer_selection_form_status": P7_R54_CLR09_REVIEWER_SELECTION_FORM_READY_STATUS_REF if scan_ready else P7_R54_CLR09_REVIEWER_SELECTION_FORM_BLOCKED_STATUS_REF,
        "reviewer_selection_form_ref": P7_R54_CLR09_REVIEWER_SELECTION_FORM_REF if scan_ready else "reviewer_selection_form_not_ready_bodyfree",
        "reviewer_selection_form_policy_ref": P7_R54_CLR09_REVIEWER_SELECTION_FORM_POLICY_REF,
        "reviewer_instruction_ref": P7_R54_CLR09_REVIEWER_INSTRUCTION_REF if scan_ready else "reviewer_instruction_blocked_until_packet_scan",
        "rating_form_ref": P7_R54_CLR09_RATING_FORM_REF if scan_ready else "rating_form_blocked_until_packet_scan",
        "reviewer_selection_form_reason_refs": reasons,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "packet_scan_row_count": scan.get("packet_scan_row_count", 0),
        "packet_present_count": scan.get("packet_present_count", 0),
        "required_fields_present_count": scan.get("required_fields_present_count", 0),
        "selection_row_required_field_refs": list(P7_R54_CLR09_SELECTION_ROW_REQUIRED_FIELD_REFS) if scan_ready else [],
        "selection_row_required_field_ref_count": len(P7_R54_CLR09_SELECTION_ROW_REQUIRED_FIELD_REFS) if scan_ready else 0,
        "rating_axis_refs": list(P7_R54_CLR09_RATING_AXIS_REFS) if scan_ready else [],
        "rating_axis_count": len(P7_R54_CLR09_RATING_AXIS_REFS) if scan_ready else 0,
        "rating_axis_target_thresholds": dict(P7_R54_CLR09_RATING_AXIS_TARGET_THRESHOLDS) if scan_ready else {},
        "score_option_refs": list(P7_R54_CLR09_SCORE_OPTION_REFS) if scan_ready else [],
        "verdict_option_refs": list(P7_R54_CLR09_VERDICT_OPTION_REFS) if scan_ready else [],
        "overall_read_feeling_option_refs": list(P7_R54_CLR09_OVERALL_READ_FEELING_OPTION_REFS) if scan_ready else [],
        "readfeel_blocker_id_option_refs": list(P7_R54_CLR09_READFEEL_BLOCKER_OPTION_REFS) if scan_ready else [],
        "execution_blocker_id_option_refs": list(P7_R54_CLR09_EXECUTION_BLOCKER_OPTION_REFS) if scan_ready else [],
        "question_need_primary_class_options": list(P7_R54_CLR09_QUESTION_NEED_PRIMARY_CLASS_REFS) if scan_ready else [],
        "ambiguity_kind_option_refs": list(P7_R54_CLR09_AMBIGUITY_KIND_OPTION_REFS) if scan_ready else [],
        "one_question_fit_option_refs": list(P7_R54_CLR09_ONE_QUESTION_FIT_OPTION_REFS) if scan_ready else [],
        "repair_required_option_refs": list(P7_R54_CLR09_REPAIR_REQUIRED_OPTION_REFS) if scan_ready else [],
        "plan_candidate_flag_refs": list(P7_R54_CLR09_PLAN_CANDIDATE_FLAG_REFS) if scan_ready else [],
        "selection_only_form": scan_ready,
        "actual_human_review_operation_allowed_next": scan_ready,
        "actual_human_review_operation_state_capture_allowed_next": scan_ready,
        "reviewer_selection_form_materialized_here": scan_ready,
        "rating_form_materialized_here": scan_ready,
        "reviewer_free_text_field_present": False,
        "reviewer_free_text_export_allowed": False,
        "raw_body_copy_field_present": False,
        "question_text_field_present": False,
        "draft_question_text_field_present": False,
        "local_path_field_present": False,
        "local_absolute_path_field_present": False,
        "body_hash_field_present": False,
        "packet_content_field_present": False,
        "terminal_output_body_field_present": False,
        "rating_form_contains_question_text": False,
        "rating_form_contains_raw_body_copy": False,
        "rating_form_contains_local_path": False,
        "rating_form_contains_local_absolute_path": False,
        "rating_form_contains_body_hash": False,
        "rating_form_contains_packet_content": False,
        "rating_form_contains_terminal_output_body": False,
        "rating_form_contains_reviewer_free_text_export": False,
        "actual_human_review_started_here": False,
        "actual_human_review_run_here": False,
        "p5_actual_review_still_not_run": True,
        "actual_review_evidence_complete": False,
        "rating_row_count": 0,
        "question_observation_row_count": 0,
        "disposal_verified_before_form": False,
        "disposal_verified_before_review": False,
        "disposal_verified": False,
        "actual_human_review_completion_claim_blocked_here": True,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        **_current_ref_fields(),
        "implemented_steps": list(P7_R54_CLR09_IMPLEMENTED_STEPS if scan_ready else (scan.get("implemented_steps") or [])),
        "not_yet_implemented_steps": list(P7_R54_CLR09_NOT_YET_IMPLEMENTED_STEPS if scan_ready else (scan.get("not_yet_implemented_steps") or [])),
        "next_required_step": P7_R54_CLR10_STEP_REF if scan_ready else P7_R54_CLR09_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_clr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_clr09_reviewer_selection_form_freeze_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(data, required=P7_R54_CLR09_REVIEWER_SELECTION_FORM_FREEZE_REQUIRED_FIELD_REFS, source="P7-R54-CLR09")
    _assert_base(data, schema_version=P7_R54_CLR09_REVIEWER_SELECTION_FORM_FREEZE_SCHEMA_VERSION, policy_section=P7_R54_CLR09_STEP_REF, source="P7-R54-CLR09")
    _assert_current_refs(data, source="P7-R54-CLR09")
    if safe_mapping(data.get("existing_op09_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("P7-R54-CLR09 OP09 refs changed")
    if data.get("existing_op09_current_refs_are_historical_here") is not True or data.get("existing_op09_reused_as_actual_form_basis") is not False:
        raise ValueError("P7-R54-CLR09 historical OP09 boundary changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=100, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("P7-R54-CLR09 blockers mismatch")
    for key in (
        "reviewer_free_text_field_present", "reviewer_free_text_export_allowed", "raw_body_copy_field_present",
        "question_text_field_present", "draft_question_text_field_present", "local_path_field_present",
        "local_absolute_path_field_present", "body_hash_field_present", "packet_content_field_present",
        "terminal_output_body_field_present", "rating_form_contains_question_text", "rating_form_contains_raw_body_copy",
        "rating_form_contains_local_path", "rating_form_contains_local_absolute_path", "rating_form_contains_body_hash",
        "rating_form_contains_packet_content", "rating_form_contains_terminal_output_body",
        "rating_form_contains_reviewer_free_text_export", "actual_human_review_started_here",
        "actual_human_review_run_here", "actual_review_evidence_complete", "disposal_verified_before_form", "disposal_verified_before_review", "disposal_verified",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-CLR09 must keep {key}=False")
    if data.get("p5_actual_review_still_not_run") is not True:
        raise ValueError("P7-R54-CLR09 must not run actual human review")
    if data.get("rating_row_count") != 0 or data.get("question_observation_row_count") != 0:
        raise ValueError("P7-R54-CLR09 must not materialize review rows")
    ready = data.get("reviewer_selection_form_status") == P7_R54_CLR09_REVIEWER_SELECTION_FORM_READY_STATUS_REF
    if ready:
        if data.get("clr08_packet_scan_ready") is not True or data.get("clr08_packet_scan_status") != P7_R54_CLR08_PACKET_SCAN_READY_STATUS_REF:
            raise ValueError("P7-R54-CLR09 ready form requires ready CLR08 scan")
        if blockers:
            raise ValueError("P7-R54-CLR09 ready form must have no blockers")
        if tuple(data.get("selection_row_required_field_refs") or ()) != P7_R54_CLR09_SELECTION_ROW_REQUIRED_FIELD_REFS:
            raise ValueError("P7-R54-CLR09 selection fields changed")
        if tuple(data.get("rating_axis_refs") or ()) != P7_R54_CLR09_RATING_AXIS_REFS:
            raise ValueError("P7-R54-CLR09 axes changed")
        if safe_mapping(data.get("rating_axis_target_thresholds")) != P7_R54_CLR09_RATING_AXIS_TARGET_THRESHOLDS:
            raise ValueError("P7-R54-CLR09 thresholds changed")
        if tuple(data.get("score_option_refs") or ()) != P7_R54_CLR09_SCORE_OPTION_REFS:
            raise ValueError("P7-R54-CLR09 score options changed")
        if tuple(data.get("verdict_option_refs") or ()) != P7_R54_CLR09_VERDICT_OPTION_REFS:
            raise ValueError("P7-R54-CLR09 verdict options changed")
        if tuple(data.get("overall_read_feeling_option_refs") or ()) != P7_R54_CLR09_OVERALL_READ_FEELING_OPTION_REFS:
            raise ValueError("P7-R54-CLR09 overall read feeling options changed")
        if tuple(data.get("readfeel_blocker_id_option_refs") or ()) != P7_R54_CLR09_READFEEL_BLOCKER_OPTION_REFS:
            raise ValueError("P7-R54-CLR09 readfeel blockers changed")
        if tuple(data.get("execution_blocker_id_option_refs") or ()) != P7_R54_CLR09_EXECUTION_BLOCKER_OPTION_REFS:
            raise ValueError("P7-R54-CLR09 execution blockers changed")
        if tuple(data.get("question_need_primary_class_options") or ()) != P7_R54_CLR09_QUESTION_NEED_PRIMARY_CLASS_REFS:
            raise ValueError("P7-R54-CLR09 question options changed")
        if data.get("selection_only_form") is not True or data.get("actual_human_review_operation_allowed_next") is not True:
            raise ValueError("P7-R54-CLR09 ready form must be selection-only and allow CLR10")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_CLR09_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR09 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_CLR09_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR09 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_CLR10_STEP_REF:
            raise ValueError("P7-R54-CLR09 ready next step changed")
    else:
        if data.get("selection_only_form") is not False or data.get("actual_human_review_operation_allowed_next") is not False:
            raise ValueError("P7-R54-CLR09 blocked form must not allow review")
        if not blockers:
            raise ValueError("P7-R54-CLR09 blocked form must carry blockers")
        if P7_R54_CLR09_STEP_REF in tuple(data.get("implemented_steps") or ()): 
            raise ValueError("P7-R54-CLR09 blocked form must not mark CLR09 implemented")
        if data.get("next_required_step") != P7_R54_CLR09_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-CLR09 blocked next step changed")
    return True


build_p7_r54_current_snapshot_local_run_clr08_packet_completeness_export_denylist_scan = build_p7_r54_clr08_packet_completeness_export_denylist_scan
assert_p7_r54_current_snapshot_local_run_clr08_packet_completeness_export_denylist_scan_contract = assert_p7_r54_clr08_packet_completeness_export_denylist_scan_contract
build_p7_r54_current_snapshot_packet_completeness_export_denylist_scan_bodyfree = build_p7_r54_clr08_packet_completeness_export_denylist_scan
assert_p7_r54_current_snapshot_packet_completeness_export_denylist_scan_bodyfree_contract = assert_p7_r54_clr08_packet_completeness_export_denylist_scan_contract
build_p7_r54_current_snapshot_local_run_clr09_reviewer_selection_form_freeze = build_p7_r54_clr09_reviewer_selection_form_freeze
assert_p7_r54_current_snapshot_local_run_clr09_reviewer_selection_form_freeze_contract = assert_p7_r54_clr09_reviewer_selection_form_freeze_contract
build_p7_r54_current_snapshot_reviewer_selection_form_freeze_bodyfree = build_p7_r54_clr09_reviewer_selection_form_freeze
assert_p7_r54_current_snapshot_reviewer_selection_form_freeze_bodyfree_contract = assert_p7_r54_clr09_reviewer_selection_form_freeze_contract
# Short aliases kept for local validation and result memo compatibility.
build_clr08_packet_completeness_export_denylist_scan = build_p7_r54_clr08_packet_completeness_export_denylist_scan
assert_clr08_packet_completeness_export_denylist_scan_contract = assert_p7_r54_clr08_packet_completeness_export_denylist_scan_contract
build_clr09_reviewer_selection_form_freeze = build_p7_r54_clr09_reviewer_selection_form_freeze
assert_clr09_reviewer_selection_form_freeze_contract = assert_p7_r54_clr09_reviewer_selection_form_freeze_contract
