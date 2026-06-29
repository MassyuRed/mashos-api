# -*- coding: utf-8 -*-
"""P7-R54 current snapshot local review run CLR06-CLR07 helpers.

This module continues the 2026-06-27 R54 current snapshot local run without
rewriting the already frozen CLR00-CLR05 helper modules.

R54-CLR-06 records only body-free evidence that body-full packet generation may
be requested for the already frozen 24-case manifest.  It does not include,
export, hash, persist, or generate packet content.

R54-CLR-07 intakes a body-free local packet generation operation receipt.  The
helper does not generate local packets.  It accepts a receipt with safe refs,
counts, status, and blocker ids only; local paths, hashes, packet content, raw
input, terminal output body, and question text are rejected.

No API, DB, RN, runtime, public response contract, P8 question implementation,
actual human review, rating/question rows, disposal verification, P5 finalization,
P6/P8 start, P7 completion, or release permission is performed here.
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
import emlis_ai_p7_r54_current_snapshot_local_review_run_20260627 as clr03
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr04_clr05_20260627 as clr05


P7_R54_CLR06_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_EVIDENCE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr06_body_full_packet_generation_request_bodyfree_evidence.bodyfree.v1"
)
P7_R54_CLR07_LOCAL_PACKET_GENERATION_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr07_local_packet_generation_operation_receipt_intake.bodyfree.v1"
)

P7_R54_CLR_STEP: Final = clr03.P7_R54_CLR_STEP
P7_R54_CLR_SCOPE: Final = clr03.P7_R54_CLR_SCOPE
P7_R54_CLR_POLICY_KIND: Final = clr03.P7_R54_CLR_POLICY_KIND
P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID: Final = clr03.P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID
P7_R54_CLR06_STEP_REF: Final = clr03.P7_R54_CLR06_STEP_REF
P7_R54_CLR07_STEP_REF: Final = clr03.P7_R54_CLR07_STEP_REF
P7_R54_CLR08_STEP_REF: Final = clr03.P7_R54_CLR08_STEP_REF

P7_R54_CLR06_REQUEST_READY_STATUS_REF: Final = "PACKET_GENERATION_REQUEST_BODYFREE_EVIDENCE_READY"
P7_R54_CLR06_REQUEST_BLOCKED_STATUS_REF: Final = "PACKET_GENERATION_REQUEST_BLOCKED_BY_CLR05_MANIFEST"
P7_R54_CLR06_ALLOWED_REQUEST_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_CLR06_REQUEST_READY_STATUS_REF,
    P7_R54_CLR06_REQUEST_BLOCKED_STATUS_REF,
)
P7_R54_CLR06_PACKET_GENERATION_REQUEST_STATUS_REF: Final = "R54_CLR06_BODYFREE_PACKET_GENERATION_REQUEST_REFROZEN"
P7_R54_CLR06_PACKET_GENERATION_REQUEST_REF: Final = (
    "r54_clr06_local_only_body_full_packet_generation_request_bodyfree_20260627"
)
P7_R54_CLR06_PACKET_GENERATION_REQUEST_POLICY_REF: Final = (
    "packet_generation_request_is_bodyfree_refs_only_no_packet_content_no_path_no_hash_20260627"
)
P7_R54_CLR06_ALLOWED_OUTPUT_REF: Final = "local_only_body_full_packet"
P7_R54_CLR06_READY_REASON_REF: Final = "r54_clr06_bodyfree_packet_generation_request_ready_after_20260627_manifest"
P7_R54_CLR06_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "R54-CLR-06_repair_24_case_manifest_before_packet_generation_request"
P7_R54_CLR06_FORBIDDEN_OUTPUT_REFS: Final[tuple[str, ...]] = (
    "packet_content_export",
    "local_absolute_path_export",
    "body_hash_export",
    "raw_input_export",
    "returned_emlis_body_export",
    "history_surface_export",
    "reviewer_free_text_export",
    "question_text_export",
    "terminal_output_body_export",
    "artifact_zip_export",
    "release_material_export",
    "repo_docs_export",
    "premise_materials_export",
    "implemented_materials_export",
)
P7_R54_CLR06_PACKET_REQUEST_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "packet_request_row_ref",
    "case_index",
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
    "case_role_family_ref",
    "plan_tier_context_ref",
    "packet_generation_requested",
    "request_is_bodyfree_only",
    "allowed_output_ref",
    "forbidden_output_refs",
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

P7_R54_CLR07_LOCAL_ONLY_PACKET_GENERATED_STATUS_REF: Final = "LOCAL_ONLY_PACKET_GENERATED"
P7_R54_CLR07_PACKET_GENERATION_BLOCKED_STATUS_REF: Final = "BLOCKED"
P7_R54_CLR07_PACKET_GENERATION_PARTIAL_STATUS_REF: Final = "PARTIAL"
P7_R54_CLR07_ALLOWED_PACKET_GENERATION_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_CLR07_LOCAL_ONLY_PACKET_GENERATED_STATUS_REF,
    P7_R54_CLR07_PACKET_GENERATION_BLOCKED_STATUS_REF,
    P7_R54_CLR07_PACKET_GENERATION_PARTIAL_STATUS_REF,
)
P7_R54_CLR07_RECEIPT_READY_STATUS_REF: Final = "LOCAL_PACKET_GENERATION_RECEIPT_READY_BODYFREE"
P7_R54_CLR07_RECEIPT_BLOCKED_STATUS_REF: Final = "LOCAL_PACKET_GENERATION_RECEIPT_BLOCKED"
P7_R54_CLR07_RECEIPT_PARTIAL_STATUS_REF: Final = "LOCAL_PACKET_GENERATION_RECEIPT_PARTIAL"
P7_R54_CLR07_ALLOWED_RECEIPT_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_CLR07_RECEIPT_READY_STATUS_REF,
    P7_R54_CLR07_RECEIPT_BLOCKED_STATUS_REF,
    P7_R54_CLR07_RECEIPT_PARTIAL_STATUS_REF,
)
P7_R54_CLR07_PACKET_GENERATION_OPERATION_REF: Final = (
    "r54_clr07_local_packet_generation_operation_receipt_bodyfree_20260627"
)
P7_R54_CLR07_PACKET_GENERATION_RECEIPT_POLICY_REF: Final = (
    "local_packet_generation_receipt_is_bodyfree_refs_counts_status_only_no_paths_no_hash_no_packet_content"
)
P7_R54_CLR07_READY_REASON_REF: Final = "r54_clr07_local_packet_generation_receipt_ready_bodyfree"
P7_R54_CLR07_RECEIPT_MISSING_REASON_REF: Final = "local_packet_generation_operation_receipt_missing"
P7_R54_CLR07_PARTIAL_REASON_REF: Final = "local_packet_generation_operation_receipt_partial_or_mismatched"
P7_R54_CLR07_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "R54-CLR-07_local_packet_generation_operation_receipt_required"
P7_R54_CLR07_RECEIPT_ALLOWED_FIELD_REFS: Final[tuple[str, ...]] = (
    "packet_generation_operation_ref",
    "packet_generation_status",
    "actual_packet_count",
    "packet_ref_ids",
    "export_candidate_count",
    "execution_blocker_ids",
)

P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR06: Final[tuple[str, ...]] = clr03.P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR01[5:]
P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR07: Final[tuple[str, ...]] = clr03.P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR01[6:]
P7_R54_CLR06_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *clr05.P7_R54_CLR05_IMPLEMENTED_STEPS,
    P7_R54_CLR06_STEP_REF,
)
P7_R54_CLR06_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR06
P7_R54_CLR07_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_CLR06_IMPLEMENTED_STEPS,
    P7_R54_CLR07_STEP_REF,
)
P7_R54_CLR07_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR07

P7_R54_CLR06_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_EVIDENCE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *clr03.P7_R54_CLR_COMMON_REQUIRED_FIELD_REFS,
    "clr05_schema_version",
    "clr05_material_ref",
    "clr05_next_required_step",
    "clr05_manifest_status",
    "clr05_manifest_ready",
    "clr05_manifest_row_count",
    "clr05_manifest_rows_bodyfree_only",
    "existing_op06_helper_ref",
    "existing_op06_schema_version",
    "existing_op06_operation_current_refs",
    "existing_op06_current_refs_are_historical_here",
    "existing_op06_reused_as_actual_request_basis",
    "existing_op06_structural_contract_reused",
    "required_case_count",
    "packet_generation_request_status",
    "packet_generation_request_status_ref",
    "packet_generation_request_ref",
    "packet_generation_request_policy_ref",
    "packet_generation_request_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "packet_request_count",
    "packet_ref_ids",
    "packet_ref_count",
    "expected_packet_ref_count",
    "packet_ref_ids_unique",
    "packet_generation_request_rows",
    "packet_generation_request_row_count",
    "allowed_output_ref",
    "forbidden_output_refs",
    "forbidden_output_ref_count",
    "export_denylist_refs",
    "export_denylist_ref_count",
    "request_is_bodyfree_only",
    "request_contains_packet_content",
    "request_contains_local_path",
    "request_contains_local_absolute_path",
    "request_contains_body_hash",
    "request_contains_raw_body",
    "request_contains_returned_body",
    "request_contains_history_surface",
    "request_contains_reviewer_free_text",
    "request_contains_question_text",
    "request_contains_draft_question_text",
    "request_contains_terminal_output_body",
    "body_full_packet_generation_request_evidence_materialized_here",
    "body_full_packet_generation_local_operation_started_here",
    "body_full_packet_generated_here",
    "body_full_packet_export_allowed",
    "body_full_packet_zip_inclusion_allowed",
    "reviewer_notes_export_allowed",
    "local_review_root_path_included",
    "local_packet_directory_path_included",
    "body_full_packet_content_included",
    "local_packet_generation_operation_receipt_intake_allowed_next",
    "p5_actual_review_still_not_run",
    "actual_review_evidence_complete",
    "rating_row_count",
    "question_observation_row_count",
    "disposal_verified_before_receipt",
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
P7_R54_CLR07_LOCAL_PACKET_GENERATION_OPERATION_RECEIPT_INTAKE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *clr03.P7_R54_CLR_COMMON_REQUIRED_FIELD_REFS,
    "clr06_schema_version",
    "clr06_material_ref",
    "clr06_next_required_step",
    "clr06_packet_generation_request_status",
    "clr06_request_ready",
    "existing_op07_helper_ref",
    "existing_op07_schema_version",
    "existing_op07_operation_current_refs",
    "existing_op07_current_refs_are_historical_here",
    "existing_op07_reused_as_actual_local_operation_basis",
    "existing_op07_structural_contract_reused",
    "required_case_count",
    "expected_packet_count",
    "expected_packet_ref_ids",
    "expected_packet_ref_count",
    "packet_generation_operation_ref",
    "packet_generation_status",
    "packet_generation_receipt_status_ref",
    "packet_generation_receipt_policy_ref",
    "packet_generation_receipt_reason_refs",
    "receipt_allowed_field_refs",
    "receipt_allowed_field_ref_count",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "actual_packet_count",
    "packet_ref_ids",
    "packet_ref_count",
    "packet_ref_ids_unique",
    "packet_ref_ids_match_request",
    "export_candidate_count",
    "receipt_is_bodyfree_only",
    "receipt_contains_packet_content",
    "receipt_contains_local_path",
    "receipt_contains_local_absolute_path",
    "receipt_contains_body_hash",
    "receipt_contains_raw_body",
    "receipt_contains_returned_body",
    "receipt_contains_history_surface",
    "receipt_contains_reviewer_free_text",
    "receipt_contains_question_text",
    "receipt_contains_draft_question_text",
    "receipt_contains_terminal_output_body",
    "packet_generation_local_operation_declared_complete",
    "packet_generation_local_operation_unverified_by_artifact",
    "local_operation_executed_outside_artifact_boundary",
    "local_operation_receipt_materialized_here",
    "local_operation_receipt_body_stored_here",
    "body_full_packet_content_included",
    "body_full_packet_generated_here",
    "actual_body_full_packet_generated_here",
    "local_reviewer_payload_materialized_here",
    "local_review_root_path_included",
    "local_packet_directory_path_included",
    "local_packet_exported",
    "local_packet_export_candidate_count",
    "body_full_packet_export_allowed",
    "body_full_packet_zip_inclusion_allowed",
    "reviewer_notes_export_allowed",
    "packet_completeness_export_denylist_scan_allowed_next",
    "actual_review_execution_blocked_until_packet_scan",
    "p5_actual_review_still_not_run",
    "actual_review_evidence_complete",
    "rating_row_count",
    "question_observation_row_count",
    "disposal_verified_before_receipt",
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
    return clr05._false_flags()


def _body_free_markers() -> dict[str, bool]:
    return clr05._body_free_markers()


def _no_touch_contract() -> dict[str, bool]:
    return clr05._no_touch_contract()


def _current_ref_fields() -> dict[str, Any]:
    return clr05._current_ref_fields()


def _safe_review_session_id(value: Any) -> str:
    return clean_identifier(value, default=P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID, max_length=220)


def _assert_required_fields(data: Mapping[str, Any], *, required: tuple[str, ...], source: str) -> None:
    clr05._assert_required_fields(data, required=required, source=source)


def _assert_bodyfree_no_touch_base(
    data: Mapping[str, Any], *, schema_version: str, policy_section: str, operation_step_ref: str, source: str
) -> None:
    clr05._assert_bodyfree_no_touch_base(
        data,
        schema_version=schema_version,
        policy_section=policy_section,
        operation_step_ref=operation_step_ref,
        source=source,
    )


def _assert_current_refs(data: Mapping[str, Any], *, source: str) -> None:
    clr05._assert_current_refs(data, source=source)


def _unique_non_empty(values: Sequence[str], *, required_count: int) -> bool:
    return len(values) == required_count and all(values) and len(set(values)) == len(values)


def _int_non_negative(value: Any, *, default: int = 0) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return number if number >= 0 else default


def _packet_ref_ids_from_manifest(manifest: Mapping[str, Any]) -> list[str]:
    return [clean_identifier(item, max_length=180) for item in (manifest.get("packet_ref_ids") or [])]


def _packet_generation_request_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    request_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        data = safe_mapping(row)
        request_rows.append(
            {
                "packet_request_row_ref": f"r54clr06-packet-request-row-{index:03d}",
                "case_index": _int_non_negative(data.get("case_index"), default=index),
                "case_ref_id": clean_identifier(data.get("case_ref_id"), max_length=180),
                "blind_case_id": clean_identifier(data.get("blind_case_id"), max_length=180),
                "packet_ref_id": clean_identifier(data.get("packet_ref_id"), max_length=180),
                "case_role_family_ref": clean_identifier(data.get("case_role_family_ref"), max_length=180),
                "plan_tier_context_ref": clean_identifier(data.get("plan_tier_context_ref"), max_length=120),
                "packet_generation_requested": True,
                "request_is_bodyfree_only": True,
                "allowed_output_ref": P7_R54_CLR06_ALLOWED_OUTPUT_REF,
                "forbidden_output_refs": list(P7_R54_CLR06_FORBIDDEN_OUTPUT_REFS),
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
        )
    return request_rows


def _assert_packet_generation_request_row(row: Mapping[str, Any]) -> None:
    data = safe_mapping(row)
    _assert_required_fields(
        data,
        required=P7_R54_CLR06_PACKET_REQUEST_ROW_REQUIRED_FIELD_REFS,
        source="P7-R54-CLR06 packet request row",
    )
    if data.get("packet_generation_requested") is not True or data.get("request_is_bodyfree_only") is not True:
        raise ValueError("P7-R54-CLR06 packet request row must be body-free request evidence")
    if data.get("allowed_output_ref") != P7_R54_CLR06_ALLOWED_OUTPUT_REF:
        raise ValueError("P7-R54-CLR06 packet request row allowed output changed")
    if tuple(data.get("forbidden_output_refs") or ()) != P7_R54_CLR06_FORBIDDEN_OUTPUT_REFS:
        raise ValueError("P7-R54-CLR06 packet request row forbidden outputs changed")
    for false_key in (
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
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"P7-R54-CLR06 packet request row must keep {false_key}=False")
    if data.get("body_free") is not True:
        raise ValueError("P7-R54-CLR06 packet request row must remain body-free")
    assert_p7_no_body_payload_or_contract_mutation(data, source="P7-R54-CLR06 packet request row")


def build_p7_r54_clr06_body_full_packet_generation_request_bodyfree_evidence(
    *,
    case_manifest_freeze: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build R54-CLR-06 body-free packet generation request evidence."""

    manifest = dict(case_manifest_freeze or clr05.build_p7_r54_clr05_24_case_manifest_freeze())
    clr05.assert_p7_r54_clr05_24_case_manifest_freeze_contract(manifest)
    manifest_ready = manifest.get("manifest_status") == clr05.P7_R54_CLR05_MANIFEST_READY_STATUS_REF
    manifest_rows = [safe_mapping(row) for row in (manifest.get("manifest_rows") or [])] if manifest_ready else []
    packet_ref_ids = _packet_ref_ids_from_manifest(manifest) if manifest_ready else []
    request_rows = _packet_generation_request_rows(manifest_rows) if manifest_ready else []
    required_count = clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
    request_ready = bool(
        manifest_ready
        and manifest.get("body_full_packet_generation_request_allowed_next") is True
        and manifest.get("manifest_row_count") == required_count
        and len(packet_ref_ids) == required_count
        and _unique_non_empty(packet_ref_ids, required_count=required_count)
        and len(request_rows) == required_count
    )
    blockers = [] if request_ready else dedupe_identifiers(
        ["r54_clr06_blocked_until_24_case_manifest_ready", *(manifest.get("open_execution_blocker_ids") or [])],
        limit=40,
        max_length=180,
    )
    reasons = (
        [P7_R54_CLR06_READY_REASON_REF]
        if request_ready
        else dedupe_identifiers(
            ["clr05_manifest_not_ready_for_bodyfree_packet_generation_request", *(manifest.get("manifest_reason_refs") or [])],
            limit=40,
            max_length=180,
        )
    )
    material: dict[str, Any] = {
        "schema_version": P7_R54_CLR06_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_EVIDENCE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_CLR_STEP,
        "scope": P7_R54_CLR_SCOPE,
        "policy_kind": P7_R54_CLR_POLICY_KIND,
        "policy_section": P7_R54_CLR06_STEP_REF,
        "operation_step_ref": P7_R54_CLR06_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_clr06_body_full_packet_generation_request_bodyfree_evidence_20260627",
        "review_session_id": _safe_review_session_id(review_session_id or manifest.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "clr05_schema_version": manifest["schema_version"],
        "clr05_material_ref": manifest["material_id"],
        "clr05_next_required_step": manifest["next_required_step"],
        "clr05_manifest_status": manifest["manifest_status"],
        "clr05_manifest_ready": manifest_ready,
        "clr05_manifest_row_count": manifest.get("manifest_row_count"),
        "clr05_manifest_rows_bodyfree_only": manifest.get("manifest_rows_bodyfree_only"),
        "existing_op06_helper_ref": "emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625.build_p7_r54_op06_local_only_body_full_packet_generation_request",
        "existing_op06_schema_version": r54op.P7_R54_OPERATION_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION,
        "existing_op06_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op06_current_refs_are_historical_here": True,
        "existing_op06_reused_as_actual_request_basis": False,
        "existing_op06_structural_contract_reused": True,
        "required_case_count": required_count,
        "packet_generation_request_status": P7_R54_CLR06_REQUEST_READY_STATUS_REF if request_ready else P7_R54_CLR06_REQUEST_BLOCKED_STATUS_REF,
        "packet_generation_request_status_ref": P7_R54_CLR06_PACKET_GENERATION_REQUEST_STATUS_REF,
        "packet_generation_request_ref": P7_R54_CLR06_PACKET_GENERATION_REQUEST_REF if request_ready else "not_requested_until_clr05_manifest_ready",
        "packet_generation_request_policy_ref": P7_R54_CLR06_PACKET_GENERATION_REQUEST_POLICY_REF,
        "packet_generation_request_reason_refs": reasons,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "packet_request_count": len(packet_ref_ids) if request_ready else 0,
        "packet_ref_ids": packet_ref_ids if request_ready else [],
        "packet_ref_count": len(packet_ref_ids) if request_ready else 0,
        "expected_packet_ref_count": required_count,
        "packet_ref_ids_unique": _unique_non_empty(packet_ref_ids, required_count=required_count) if request_ready else False,
        "packet_generation_request_rows": request_rows if request_ready else [],
        "packet_generation_request_row_count": len(request_rows) if request_ready else 0,
        "allowed_output_ref": P7_R54_CLR06_ALLOWED_OUTPUT_REF,
        "forbidden_output_refs": list(P7_R54_CLR06_FORBIDDEN_OUTPUT_REFS),
        "forbidden_output_ref_count": len(P7_R54_CLR06_FORBIDDEN_OUTPUT_REFS),
        "export_denylist_refs": list(clr05.P7_R54_CLR04_EXPORT_DENYLIST_REFS),
        "export_denylist_ref_count": len(clr05.P7_R54_CLR04_EXPORT_DENYLIST_REFS),
        "request_is_bodyfree_only": True,
        "request_contains_packet_content": False,
        "request_contains_local_path": False,
        "request_contains_local_absolute_path": False,
        "request_contains_body_hash": False,
        "request_contains_raw_body": False,
        "request_contains_returned_body": False,
        "request_contains_history_surface": False,
        "request_contains_reviewer_free_text": False,
        "request_contains_question_text": False,
        "request_contains_draft_question_text": False,
        "request_contains_terminal_output_body": False,
        "body_full_packet_generation_request_evidence_materialized_here": request_ready,
        "body_full_packet_generation_local_operation_started_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packet_export_allowed": False,
        "body_full_packet_zip_inclusion_allowed": False,
        "reviewer_notes_export_allowed": False,
        "local_review_root_path_included": False,
        "local_packet_directory_path_included": False,
        "body_full_packet_content_included": False,
        "local_packet_generation_operation_receipt_intake_allowed_next": request_ready,
        "p5_actual_review_still_not_run": True,
        "actual_review_evidence_complete": False,
        "rating_row_count": 0,
        "question_observation_row_count": 0,
        "disposal_verified_before_receipt": False,
        "actual_human_review_completion_claim_blocked_here": True,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        **_current_ref_fields(),
        "implemented_steps": list(P7_R54_CLR06_IMPLEMENTED_STEPS if request_ready else (manifest.get("implemented_steps") or [])),
        "not_yet_implemented_steps": list(
            P7_R54_CLR06_NOT_YET_IMPLEMENTED_STEPS if request_ready else (manifest.get("not_yet_implemented_steps") or [])
        ),
        "next_required_step": P7_R54_CLR07_STEP_REF if request_ready else P7_R54_CLR06_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_clr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_clr06_body_full_packet_generation_request_bodyfree_evidence_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_CLR06_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_EVIDENCE_REQUIRED_FIELD_REFS,
        source="P7-R54-CLR06",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_CLR06_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_EVIDENCE_SCHEMA_VERSION,
        policy_section=P7_R54_CLR06_STEP_REF,
        operation_step_ref=P7_R54_CLR06_STEP_REF,
        source="P7-R54-CLR06",
    )
    _assert_current_refs(data, source="P7-R54-CLR06")
    if data.get("clr05_schema_version") != clr05.P7_R54_CLR05_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION:
        raise ValueError("P7-R54-CLR06 must follow CLR05")
    if data.get("existing_op06_schema_version") != r54op.P7_R54_OPERATION_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION:
        raise ValueError("P7-R54-CLR06 existing OP06 schema changed")
    if safe_mapping(data.get("existing_op06_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("P7-R54-CLR06 existing OP06 refs changed")
    if data.get("existing_op06_current_refs_are_historical_here") is not True:
        raise ValueError("P7-R54-CLR06 must classify OP06 refs as historical")
    if data.get("existing_op06_reused_as_actual_request_basis") is not False:
        raise ValueError("P7-R54-CLR06 must not reuse historical OP06 as actual request basis")
    if data.get("existing_op06_structural_contract_reused") is not True:
        raise ValueError("P7-R54-CLR06 must reuse only OP06 structural contract")
    if data.get("required_case_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-CLR06 required case count changed")
    if data.get("packet_generation_request_status") not in P7_R54_CLR06_ALLOWED_REQUEST_STATUS_REFS:
        raise ValueError("P7-R54-CLR06 request status changed")
    if data.get("packet_generation_request_status_ref") != P7_R54_CLR06_PACKET_GENERATION_REQUEST_STATUS_REF:
        raise ValueError("P7-R54-CLR06 request status ref changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("P7-R54-CLR06 open blockers must match blockers")
    if data.get("allowed_output_ref") != P7_R54_CLR06_ALLOWED_OUTPUT_REF:
        raise ValueError("P7-R54-CLR06 allowed output changed")
    if tuple(data.get("forbidden_output_refs") or ()) != P7_R54_CLR06_FORBIDDEN_OUTPUT_REFS:
        raise ValueError("P7-R54-CLR06 forbidden outputs changed")
    if data.get("forbidden_output_ref_count") != len(P7_R54_CLR06_FORBIDDEN_OUTPUT_REFS):
        raise ValueError("P7-R54-CLR06 forbidden output count changed")
    if tuple(data.get("export_denylist_refs") or ()) != clr05.P7_R54_CLR04_EXPORT_DENYLIST_REFS:
        raise ValueError("P7-R54-CLR06 export denylist changed")
    if data.get("export_denylist_ref_count") != len(clr05.P7_R54_CLR04_EXPORT_DENYLIST_REFS):
        raise ValueError("P7-R54-CLR06 export denylist count changed")
    for false_key in (
        "request_contains_packet_content",
        "request_contains_local_path",
        "request_contains_local_absolute_path",
        "request_contains_body_hash",
        "request_contains_raw_body",
        "request_contains_returned_body",
        "request_contains_history_surface",
        "request_contains_reviewer_free_text",
        "request_contains_question_text",
        "request_contains_draft_question_text",
        "request_contains_terminal_output_body",
        "body_full_packet_generation_local_operation_started_here",
        "body_full_packet_generated_here",
        "body_full_packet_export_allowed",
        "body_full_packet_zip_inclusion_allowed",
        "reviewer_notes_export_allowed",
        "local_review_root_path_included",
        "local_packet_directory_path_included",
        "body_full_packet_content_included",
        "actual_review_evidence_complete",
        "disposal_verified_before_receipt",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"P7-R54-CLR06 must keep {false_key}=False")
    if data.get("request_is_bodyfree_only") is not True:
        raise ValueError("P7-R54-CLR06 request must be body-free only")
    if data.get("p5_actual_review_still_not_run") is not True:
        raise ValueError("P7-R54-CLR06 must keep P5 actual review not run")
    if data.get("rating_row_count") != 0 or data.get("question_observation_row_count") != 0:
        raise ValueError("P7-R54-CLR06 must not materialize rating/question rows")
    for true_key in (
        "human_review_completion_claim_blocked_here",
        "actual_human_review_completion_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"P7-R54-CLR06 must keep {true_key}=True")
    request_ready = data.get("packet_generation_request_status") == P7_R54_CLR06_REQUEST_READY_STATUS_REF
    if request_ready:
        if data.get("clr05_manifest_ready") is not True or data.get("clr05_next_required_step") != P7_R54_CLR06_STEP_REF:
            raise ValueError("P7-R54-CLR06 ready request requires ready CLR05 manifest")
        if data.get("clr05_manifest_row_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-CLR06 ready request requires 24 CLR05 rows")
        packet_refs = [clean_identifier(item, max_length=180) for item in (data.get("packet_ref_ids") or [])]
        request_rows = [safe_mapping(row) for row in (data.get("packet_generation_request_rows") or [])]
        if data.get("packet_generation_request_ref") != P7_R54_CLR06_PACKET_GENERATION_REQUEST_REF:
            raise ValueError("P7-R54-CLR06 request ref changed")
        if data.get("packet_generation_request_policy_ref") != P7_R54_CLR06_PACKET_GENERATION_REQUEST_POLICY_REF:
            raise ValueError("P7-R54-CLR06 request policy changed")
        if data.get("packet_generation_request_reason_refs") != [P7_R54_CLR06_READY_REASON_REF]:
            raise ValueError("P7-R54-CLR06 ready reason changed")
        if blockers:
            raise ValueError("P7-R54-CLR06 ready request must not carry blockers")
        required_count = clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        if data.get("packet_request_count") != required_count:
            raise ValueError("P7-R54-CLR06 packet request count changed")
        if data.get("packet_ref_count") != required_count or data.get("expected_packet_ref_count") != required_count:
            raise ValueError("P7-R54-CLR06 packet ref count changed")
        if data.get("packet_ref_ids_unique") is not True or not _unique_non_empty(packet_refs, required_count=required_count):
            raise ValueError("P7-R54-CLR06 packet refs must be unique")
        if len(request_rows) != required_count or data.get("packet_generation_request_row_count") != required_count:
            raise ValueError("P7-R54-CLR06 request row count changed")
        for row in request_rows:
            _assert_packet_generation_request_row(row)
        if [row.get("packet_ref_id") for row in request_rows] != packet_refs:
            raise ValueError("P7-R54-CLR06 request rows must match packet refs")
        if data.get("body_full_packet_generation_request_evidence_materialized_here") is not True:
            raise ValueError("P7-R54-CLR06 ready request must materialize body-free request evidence")
        if data.get("local_packet_generation_operation_receipt_intake_allowed_next") is not True:
            raise ValueError("P7-R54-CLR06 ready request must allow CLR07 receipt intake next")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_CLR06_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR06 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_CLR06_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR06 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_CLR07_STEP_REF:
            raise ValueError("P7-R54-CLR06 ready request must point to CLR07")
    else:
        if data.get("packet_ref_ids") != [] or data.get("packet_generation_request_rows") != []:
            raise ValueError("P7-R54-CLR06 blocked request must not expose packet refs")
        if data.get("body_full_packet_generation_request_evidence_materialized_here") is not False:
            raise ValueError("P7-R54-CLR06 blocked request must not materialize request evidence")
        if data.get("local_packet_generation_operation_receipt_intake_allowed_next") is not False:
            raise ValueError("P7-R54-CLR06 blocked request must not allow CLR07")
        if not blockers:
            raise ValueError("P7-R54-CLR06 blocked request must carry blockers")
        implemented_steps = tuple(data.get("implemented_steps") or ())
        not_yet_steps = tuple(data.get("not_yet_implemented_steps") or ())
        if P7_R54_CLR06_STEP_REF in implemented_steps:
            raise ValueError("P7-R54-CLR06 blocked request must not mark CLR06 implemented")
        if P7_R54_CLR06_STEP_REF not in not_yet_steps:
            raise ValueError("P7-R54-CLR06 blocked request must keep CLR06 not-yet")
        if data.get("next_required_step") != P7_R54_CLR06_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-CLR06 blocked next step changed")
    return True


def _receipt_fields(receipt: Mapping[str, Any] | None) -> dict[str, Any]:
    if receipt is None:
        return {
            "packet_generation_operation_ref": "not_supplied_until_external_local_packet_generation",
            "packet_generation_status": P7_R54_CLR07_PACKET_GENERATION_BLOCKED_STATUS_REF,
            "actual_packet_count": 0,
            "packet_ref_ids": [],
            "export_candidate_count": 0,
            "execution_blocker_ids": ["local_packet_generation_operation_receipt_missing"],
        }
    data = safe_mapping(receipt)
    if clr05._contains_forbidden_key(data):
        raise ValueError("P7-R54-CLR07 receipt contains forbidden body or question payload key")
    assert_p7_no_body_payload_or_contract_mutation(data, source="P7-R54-CLR07 receipt")
    allowed = set(P7_R54_CLR07_RECEIPT_ALLOWED_FIELD_REFS)
    extra = [key for key in data if key not in allowed]
    if extra:
        raise ValueError(f"P7-R54-CLR07 receipt contains unsupported fields: {', '.join(extra[:8])}")
    status = clean_identifier(
        data.get("packet_generation_status"),
        default=P7_R54_CLR07_PACKET_GENERATION_BLOCKED_STATUS_REF,
        max_length=120,
    )
    if status not in P7_R54_CLR07_ALLOWED_PACKET_GENERATION_STATUS_REFS:
        status = P7_R54_CLR07_PACKET_GENERATION_BLOCKED_STATUS_REF
    return {
        "packet_generation_operation_ref": clean_identifier(
            data.get("packet_generation_operation_ref"),
            default="missing_packet_generation_operation_ref",
            max_length=220,
        ),
        "packet_generation_status": status,
        "actual_packet_count": _int_non_negative(data.get("actual_packet_count"), default=0),
        "packet_ref_ids": [clean_identifier(item, max_length=180) for item in (data.get("packet_ref_ids") or [])],
        "export_candidate_count": _int_non_negative(data.get("export_candidate_count"), default=0),
        "execution_blocker_ids": dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=180),
    }


def build_p7_r54_clr07_bodyfree_generated_receipt_from_request(
    packet_generation_request: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a body-free receipt-shaped object from a ready CLR06 request.

    This helper does not generate packets. It only creates the safe receipt shape
    expected from an external local-only operation, for tests or manual intake.
    """

    request = dict(packet_generation_request or build_p7_r54_clr06_body_full_packet_generation_request_bodyfree_evidence())
    assert_p7_r54_clr06_body_full_packet_generation_request_bodyfree_evidence_contract(request)
    return {
        "packet_generation_operation_ref": P7_R54_CLR07_PACKET_GENERATION_OPERATION_REF,
        "packet_generation_status": P7_R54_CLR07_LOCAL_ONLY_PACKET_GENERATED_STATUS_REF,
        "actual_packet_count": int(request.get("packet_ref_count") or 0),
        "packet_ref_ids": list(request.get("packet_ref_ids") or []),
        "export_candidate_count": 0,
        "execution_blocker_ids": [],
    }


def build_p7_r54_clr07_local_packet_generation_operation_receipt_intake(
    *,
    body_full_packet_generation_request_bodyfree_evidence: Mapping[str, Any] | None = None,
    packet_generation_operation_receipt: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build R54-CLR-07 body-free local packet generation operation receipt intake."""

    request = dict(
        body_full_packet_generation_request_bodyfree_evidence
        or build_p7_r54_clr06_body_full_packet_generation_request_bodyfree_evidence()
    )
    assert_p7_r54_clr06_body_full_packet_generation_request_bodyfree_evidence_contract(request)
    request_ready = request.get("packet_generation_request_status") == P7_R54_CLR06_REQUEST_READY_STATUS_REF
    expected_refs = [clean_identifier(item, max_length=180) for item in (request.get("packet_ref_ids") or [])] if request_ready else []
    expected_count = clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
    receipt = _receipt_fields(packet_generation_operation_receipt)
    received_refs = receipt["packet_ref_ids"]
    receipt_blockers = dedupe_identifiers(receipt.get("execution_blocker_ids") or [], limit=40, max_length=180)
    refs_match = bool(
        request_ready
        and receipt["packet_generation_status"] == P7_R54_CLR07_LOCAL_ONLY_PACKET_GENERATED_STATUS_REF
        and receipt["packet_generation_operation_ref"] == P7_R54_CLR07_PACKET_GENERATION_OPERATION_REF
        and receipt["actual_packet_count"] == expected_count
        and len(received_refs) == expected_count
        and received_refs == expected_refs
        and _unique_non_empty(received_refs, required_count=expected_count)
        and receipt["export_candidate_count"] == 0
        and not receipt_blockers
    )
    if refs_match:
        normalized_status = P7_R54_CLR07_LOCAL_ONLY_PACKET_GENERATED_STATUS_REF
        receipt_status_ref = P7_R54_CLR07_RECEIPT_READY_STATUS_REF
        blockers: list[str] = []
        reasons = [P7_R54_CLR07_READY_REASON_REF]
    else:
        if not request_ready:
            normalized_status = P7_R54_CLR07_PACKET_GENERATION_BLOCKED_STATUS_REF
            receipt_status_ref = P7_R54_CLR07_RECEIPT_BLOCKED_STATUS_REF
            blockers = dedupe_identifiers(
                ["r54_clr07_blocked_until_clr06_bodyfree_packet_generation_request_ready", *receipt_blockers],
                limit=40,
                max_length=180,
            )
            reasons = dedupe_identifiers(
                ["clr06_bodyfree_packet_generation_request_not_ready_for_receipt_intake", *(request.get("packet_generation_request_reason_refs") or [])],
                limit=40,
                max_length=180,
            )
        elif receipt["packet_generation_status"] == P7_R54_CLR07_PACKET_GENERATION_PARTIAL_STATUS_REF:
            normalized_status = P7_R54_CLR07_PACKET_GENERATION_PARTIAL_STATUS_REF
            receipt_status_ref = P7_R54_CLR07_RECEIPT_PARTIAL_STATUS_REF
            blockers = dedupe_identifiers(
                ["local_packet_generation_operation_receipt_partial", *receipt_blockers],
                limit=40,
                max_length=180,
            )
            reasons = [P7_R54_CLR07_PARTIAL_REASON_REF]
        else:
            normalized_status = P7_R54_CLR07_PACKET_GENERATION_BLOCKED_STATUS_REF
            receipt_status_ref = P7_R54_CLR07_RECEIPT_BLOCKED_STATUS_REF
            blockers = dedupe_identifiers(
                [
                    *receipt_blockers,
                    *([] if packet_generation_operation_receipt is not None else ["local_packet_generation_operation_receipt_missing"]),
                    *(
                        []
                        if receipt["packet_generation_status"] != P7_R54_CLR07_PACKET_GENERATION_BLOCKED_STATUS_REF
                        else ["local_packet_generation_operation_receipt_blocked"]
                    ),
                    *([] if receipt["packet_generation_operation_ref"] == P7_R54_CLR07_PACKET_GENERATION_OPERATION_REF else ["local_packet_generation_operation_ref_missing_or_mismatched"]),
                    *([] if received_refs == expected_refs and len(received_refs) == expected_count else ["local_packet_generation_packet_refs_missing_or_mismatched"]),
                    *([] if receipt["actual_packet_count"] == expected_count else ["local_packet_generation_actual_packet_count_mismatched"]),
                    *([] if receipt["export_candidate_count"] == 0 else ["body_payload_leak_detected"]),
                ],
                limit=40,
                max_length=180,
            )
            reasons = [P7_R54_CLR07_RECEIPT_MISSING_REASON_REF if packet_generation_operation_receipt is None else P7_R54_CLR07_PARTIAL_REASON_REF]
    material: dict[str, Any] = {
        "schema_version": P7_R54_CLR07_LOCAL_PACKET_GENERATION_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_CLR_STEP,
        "scope": P7_R54_CLR_SCOPE,
        "policy_kind": P7_R54_CLR_POLICY_KIND,
        "policy_section": P7_R54_CLR07_STEP_REF,
        "operation_step_ref": P7_R54_CLR07_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_clr07_local_packet_generation_operation_receipt_intake_20260627",
        "review_session_id": _safe_review_session_id(review_session_id or request.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "clr06_schema_version": request["schema_version"],
        "clr06_material_ref": request["material_id"],
        "clr06_next_required_step": request["next_required_step"],
        "clr06_packet_generation_request_status": request["packet_generation_request_status"],
        "clr06_request_ready": request_ready,
        "existing_op07_helper_ref": "emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625.build_p7_r54_op07_packet_generation_local_operation",
        "existing_op07_schema_version": r54op.P7_R54_OPERATION_PACKET_GENERATION_LOCAL_OPERATION_SCHEMA_VERSION,
        "existing_op07_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op07_current_refs_are_historical_here": True,
        "existing_op07_reused_as_actual_local_operation_basis": False,
        "existing_op07_structural_contract_reused": True,
        "required_case_count": expected_count,
        "expected_packet_count": expected_count,
        "expected_packet_ref_ids": expected_refs,
        "expected_packet_ref_count": len(expected_refs) if request_ready else 0,
        "packet_generation_operation_ref": receipt["packet_generation_operation_ref"],
        "packet_generation_status": normalized_status,
        "packet_generation_receipt_status_ref": receipt_status_ref,
        "packet_generation_receipt_policy_ref": P7_R54_CLR07_PACKET_GENERATION_RECEIPT_POLICY_REF,
        "packet_generation_receipt_reason_refs": reasons,
        "receipt_allowed_field_refs": list(P7_R54_CLR07_RECEIPT_ALLOWED_FIELD_REFS),
        "receipt_allowed_field_ref_count": len(P7_R54_CLR07_RECEIPT_ALLOWED_FIELD_REFS),
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "actual_packet_count": receipt["actual_packet_count"] if request_ready else 0,
        "packet_ref_ids": received_refs if request_ready else [],
        "packet_ref_count": len(received_refs) if request_ready else 0,
        "packet_ref_ids_unique": _unique_non_empty(received_refs, required_count=expected_count) if request_ready and received_refs else False,
        "packet_ref_ids_match_request": received_refs == expected_refs and len(received_refs) == expected_count if request_ready else False,
        "export_candidate_count": receipt["export_candidate_count"] if request_ready else 0,
        "receipt_is_bodyfree_only": True,
        "receipt_contains_packet_content": False,
        "receipt_contains_local_path": False,
        "receipt_contains_local_absolute_path": False,
        "receipt_contains_body_hash": False,
        "receipt_contains_raw_body": False,
        "receipt_contains_returned_body": False,
        "receipt_contains_history_surface": False,
        "receipt_contains_reviewer_free_text": False,
        "receipt_contains_question_text": False,
        "receipt_contains_draft_question_text": False,
        "receipt_contains_terminal_output_body": False,
        "packet_generation_local_operation_declared_complete": refs_match,
        "packet_generation_local_operation_unverified_by_artifact": refs_match,
        "local_operation_executed_outside_artifact_boundary": refs_match,
        "local_operation_receipt_materialized_here": packet_generation_operation_receipt is not None,
        "local_operation_receipt_body_stored_here": False,
        "body_full_packet_content_included": False,
        "body_full_packet_generated_here": False,
        "actual_body_full_packet_generated_here": False,
        "local_reviewer_payload_materialized_here": False,
        "local_review_root_path_included": False,
        "local_packet_directory_path_included": False,
        "local_packet_exported": False,
        "local_packet_export_candidate_count": receipt["export_candidate_count"] if request_ready else 0,
        "body_full_packet_export_allowed": False,
        "body_full_packet_zip_inclusion_allowed": False,
        "reviewer_notes_export_allowed": False,
        "packet_completeness_export_denylist_scan_allowed_next": refs_match,
        "actual_review_execution_blocked_until_packet_scan": True,
        "p5_actual_review_still_not_run": True,
        "actual_review_evidence_complete": False,
        "rating_row_count": 0,
        "question_observation_row_count": 0,
        "disposal_verified_before_receipt": False,
        "actual_human_review_completion_claim_blocked_here": True,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        **_current_ref_fields(),
        "implemented_steps": list(P7_R54_CLR07_IMPLEMENTED_STEPS if refs_match else (request.get("implemented_steps") or [])),
        "not_yet_implemented_steps": list(
            P7_R54_CLR07_NOT_YET_IMPLEMENTED_STEPS if refs_match else (request.get("not_yet_implemented_steps") or [])
        ),
        "next_required_step": P7_R54_CLR08_STEP_REF if refs_match else P7_R54_CLR07_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_clr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_clr07_local_packet_generation_operation_receipt_intake_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_CLR07_LOCAL_PACKET_GENERATION_OPERATION_RECEIPT_INTAKE_REQUIRED_FIELD_REFS,
        source="P7-R54-CLR07",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_CLR07_LOCAL_PACKET_GENERATION_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION,
        policy_section=P7_R54_CLR07_STEP_REF,
        operation_step_ref=P7_R54_CLR07_STEP_REF,
        source="P7-R54-CLR07",
    )
    _assert_current_refs(data, source="P7-R54-CLR07")
    if data.get("clr06_schema_version") != P7_R54_CLR06_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("P7-R54-CLR07 must follow CLR06")
    if data.get("existing_op07_schema_version") != r54op.P7_R54_OPERATION_PACKET_GENERATION_LOCAL_OPERATION_SCHEMA_VERSION:
        raise ValueError("P7-R54-CLR07 existing OP07 schema changed")
    if safe_mapping(data.get("existing_op07_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("P7-R54-CLR07 existing OP07 refs changed")
    if data.get("existing_op07_current_refs_are_historical_here") is not True:
        raise ValueError("P7-R54-CLR07 must classify OP07 refs as historical")
    if data.get("existing_op07_reused_as_actual_local_operation_basis") is not False:
        raise ValueError("P7-R54-CLR07 must not reuse historical OP07 as actual operation basis")
    if data.get("existing_op07_structural_contract_reused") is not True:
        raise ValueError("P7-R54-CLR07 must reuse only OP07 structural contract")
    if data.get("required_case_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-CLR07 required case count changed")
    if data.get("packet_generation_status") not in P7_R54_CLR07_ALLOWED_PACKET_GENERATION_STATUS_REFS:
        raise ValueError("P7-R54-CLR07 packet generation status changed")
    if data.get("packet_generation_receipt_status_ref") not in P7_R54_CLR07_ALLOWED_RECEIPT_STATUS_REFS:
        raise ValueError("P7-R54-CLR07 receipt status changed")
    if data.get("packet_generation_receipt_policy_ref") != P7_R54_CLR07_PACKET_GENERATION_RECEIPT_POLICY_REF:
        raise ValueError("P7-R54-CLR07 receipt policy changed")
    if tuple(data.get("receipt_allowed_field_refs") or ()) != P7_R54_CLR07_RECEIPT_ALLOWED_FIELD_REFS:
        raise ValueError("P7-R54-CLR07 receipt allowed fields changed")
    if data.get("receipt_allowed_field_ref_count") != len(P7_R54_CLR07_RECEIPT_ALLOWED_FIELD_REFS):
        raise ValueError("P7-R54-CLR07 receipt allowed field count changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("P7-R54-CLR07 open blockers must match blockers")
    for false_key in (
        "receipt_contains_packet_content",
        "receipt_contains_local_path",
        "receipt_contains_local_absolute_path",
        "receipt_contains_body_hash",
        "receipt_contains_raw_body",
        "receipt_contains_returned_body",
        "receipt_contains_history_surface",
        "receipt_contains_reviewer_free_text",
        "receipt_contains_question_text",
        "receipt_contains_draft_question_text",
        "receipt_contains_terminal_output_body",
        "local_operation_receipt_body_stored_here",
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
        "actual_review_evidence_complete",
        "disposal_verified_before_receipt",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"P7-R54-CLR07 must keep {false_key}=False")
    if data.get("receipt_is_bodyfree_only") is not True:
        raise ValueError("P7-R54-CLR07 receipt must be body-free only")
    if data.get("actual_review_execution_blocked_until_packet_scan") is not True:
        raise ValueError("P7-R54-CLR07 must block actual review until CLR08 scan")
    if data.get("p5_actual_review_still_not_run") is not True:
        raise ValueError("P7-R54-CLR07 must keep P5 actual review not run")
    if data.get("rating_row_count") != 0 or data.get("question_observation_row_count") != 0:
        raise ValueError("P7-R54-CLR07 must not materialize rating/question rows")
    for true_key in (
        "human_review_completion_claim_blocked_here",
        "actual_human_review_completion_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"P7-R54-CLR07 must keep {true_key}=True")
    receipt_ready = (
        data.get("packet_generation_status") == P7_R54_CLR07_LOCAL_ONLY_PACKET_GENERATED_STATUS_REF
        and not blockers
        and data.get("local_operation_receipt_materialized_here") is True
    )
    expected_refs = [clean_identifier(item, max_length=180) for item in (data.get("expected_packet_ref_ids") or [])]
    packet_refs = [clean_identifier(item, max_length=180) for item in (data.get("packet_ref_ids") or [])]
    expected_count = clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
    if receipt_ready:
        if data.get("clr06_request_ready") is not True or data.get("clr06_next_required_step") != P7_R54_CLR07_STEP_REF:
            raise ValueError("P7-R54-CLR07 ready receipt requires ready CLR06 request")
        if data.get("clr06_packet_generation_request_status") != P7_R54_CLR06_REQUEST_READY_STATUS_REF:
            raise ValueError("P7-R54-CLR07 ready receipt requires CLR06 request ready")
        if data.get("expected_packet_count") != expected_count or data.get("expected_packet_ref_count") != expected_count:
            raise ValueError("P7-R54-CLR07 expected packet count changed")
        if data.get("actual_packet_count") != expected_count:
            raise ValueError("P7-R54-CLR07 actual packet count changed")
        if data.get("packet_ref_count") != expected_count or len(packet_refs) != expected_count:
            raise ValueError("P7-R54-CLR07 packet ref count changed")
        if data.get("packet_ref_ids_unique") is not True or not _unique_non_empty(packet_refs, required_count=expected_count):
            raise ValueError("P7-R54-CLR07 packet refs must be unique")
        if data.get("packet_ref_ids_match_request") is not True or packet_refs != expected_refs:
            raise ValueError("P7-R54-CLR07 packet refs must match CLR06 request")
        if data.get("packet_generation_operation_ref") != P7_R54_CLR07_PACKET_GENERATION_OPERATION_REF:
            raise ValueError("P7-R54-CLR07 operation ref changed")
        if data.get("packet_generation_receipt_status_ref") != P7_R54_CLR07_RECEIPT_READY_STATUS_REF:
            raise ValueError("P7-R54-CLR07 ready receipt status changed")
        if data.get("packet_generation_receipt_reason_refs") != [P7_R54_CLR07_READY_REASON_REF]:
            raise ValueError("P7-R54-CLR07 ready reason changed")
        if blockers:
            raise ValueError("P7-R54-CLR07 ready receipt must not carry blockers")
        if data.get("export_candidate_count") != 0 or data.get("local_packet_export_candidate_count") != 0:
            raise ValueError("P7-R54-CLR07 ready receipt must have no export candidates")
        for true_key in (
            "packet_generation_local_operation_declared_complete",
            "packet_generation_local_operation_unverified_by_artifact",
            "local_operation_executed_outside_artifact_boundary",
            "local_operation_receipt_materialized_here",
            "packet_completeness_export_denylist_scan_allowed_next",
        ):
            if data.get(true_key) is not True:
                raise ValueError(f"P7-R54-CLR07 ready receipt must keep {true_key}=True")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_CLR07_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR07 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_CLR07_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR07 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_CLR08_STEP_REF:
            raise ValueError("P7-R54-CLR07 ready receipt must point to CLR08")
    else:
        for false_key in (
            "packet_generation_local_operation_declared_complete",
            "packet_generation_local_operation_unverified_by_artifact",
            "local_operation_executed_outside_artifact_boundary",
            "packet_completeness_export_denylist_scan_allowed_next",
        ):
            if data.get(false_key) is not False:
                raise ValueError(f"P7-R54-CLR07 blocked/partial receipt must keep {false_key}=False")
        if not blockers:
            raise ValueError("P7-R54-CLR07 blocked/partial receipt must carry blockers")
        implemented_steps = tuple(data.get("implemented_steps") or ())
        not_yet_steps = tuple(data.get("not_yet_implemented_steps") or ())
        if P7_R54_CLR07_STEP_REF in implemented_steps:
            raise ValueError("P7-R54-CLR07 blocked/partial receipt must not mark CLR07 implemented")
        if P7_R54_CLR07_STEP_REF not in not_yet_steps:
            raise ValueError("P7-R54-CLR07 blocked/partial receipt must keep CLR07 not-yet")
        if data.get("next_required_step") != P7_R54_CLR07_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-CLR07 blocked/partial next step changed")
    return True


build_p7_r54_current_snapshot_local_run_clr06_body_full_packet_generation_request_bodyfree_evidence = (
    build_p7_r54_clr06_body_full_packet_generation_request_bodyfree_evidence
)
assert_p7_r54_current_snapshot_local_run_clr06_body_full_packet_generation_request_bodyfree_evidence_contract = (
    assert_p7_r54_clr06_body_full_packet_generation_request_bodyfree_evidence_contract
)
build_p7_r54_current_snapshot_body_full_packet_generation_request_bodyfree_evidence = (
    build_p7_r54_clr06_body_full_packet_generation_request_bodyfree_evidence
)
assert_p7_r54_current_snapshot_body_full_packet_generation_request_bodyfree_evidence_contract = (
    assert_p7_r54_clr06_body_full_packet_generation_request_bodyfree_evidence_contract
)
build_p7_r54_current_snapshot_local_run_clr07_local_packet_generation_operation_receipt_intake = (
    build_p7_r54_clr07_local_packet_generation_operation_receipt_intake
)
assert_p7_r54_current_snapshot_local_run_clr07_local_packet_generation_operation_receipt_intake_contract = (
    assert_p7_r54_clr07_local_packet_generation_operation_receipt_intake_contract
)
build_p7_r54_current_snapshot_local_packet_generation_operation_receipt_intake_bodyfree = (
    build_p7_r54_clr07_local_packet_generation_operation_receipt_intake
)
assert_p7_r54_current_snapshot_local_packet_generation_operation_receipt_intake_bodyfree_contract = (
    assert_p7_r54_clr07_local_packet_generation_operation_receipt_intake_contract
)
build_p7_r54_current_snapshot_local_packet_generation_operation_receipt_bodyfree = (
    build_p7_r54_clr07_local_packet_generation_operation_receipt_intake
)
assert_p7_r54_current_snapshot_local_packet_generation_operation_receipt_bodyfree_contract = (
    assert_p7_r54_clr07_local_packet_generation_operation_receipt_intake_contract
)
