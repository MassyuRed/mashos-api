# -*- coding: utf-8 -*-
"""P7-R54 current snapshot local review run CLR04-CLR05 helpers.

This module continues the 2026-06-27 R54 current snapshot local run without
rewriting the already frozen CLR00-CLR03 helper module.

R54-CLR-04 records a body-free local-only preflight decision.  It may allow the
next manifest-freeze step, but it does not request, generate, export, hash,
retain, or review body-full packets.

R54-CLR-05 freezes the 24-case manifest from the existing R48 P5 Human Blind QA
body-free case matrix.  It does not mix P4-R11 audit rows, materialize body-full
packets, run human review, create rating/question rows, verify disposal, start
P6/P8, finalize P5, or allow release.
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
import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as r54op
import emlis_ai_p7_r54_current_snapshot_local_review_run_20260627 as clr03


P7_R54_CLR04_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr04_local_only_preflight.bodyfree.v1"
)
P7_R54_CLR05_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr05_24_case_manifest_freeze.bodyfree.v1"
)

P7_R54_CLR_STEP: Final = clr03.P7_R54_CLR_STEP
P7_R54_CLR_SCOPE: Final = clr03.P7_R54_CLR_SCOPE
P7_R54_CLR_POLICY_KIND: Final = clr03.P7_R54_CLR_POLICY_KIND
P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID: Final = clr03.P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID
P7_R54_CLR04_STEP_REF: Final = clr03.P7_R54_CLR04_STEP_REF
P7_R54_CLR05_STEP_REF: Final = clr03.P7_R54_CLR05_STEP_REF
P7_R54_CLR06_STEP_REF: Final = clr03.P7_R54_CLR06_STEP_REF

P7_R54_CLR04_PREFLIGHT_READY_STATUS_REF: Final = "PREFLIGHT_READY"
P7_R54_CLR04_PREFLIGHT_BLOCKED_STATUS_REF: Final = "PREFLIGHT_BLOCKED"
P7_R54_CLR04_ALLOWED_PREFLIGHT_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_CLR04_PREFLIGHT_READY_STATUS_REF,
    P7_R54_CLR04_PREFLIGHT_BLOCKED_STATUS_REF,
)
P7_R54_CLR04_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "R54-CLR-04_repair_local_only_preflight_before_manifest_freeze"
P7_R54_CLR04_READY_REASON_REF: Final = "local_only_preflight_ready_for_24_case_manifest_freeze"
P7_R54_CLR04_EXPLICIT_LOCAL_ONLY_ALLOW_REF: Final = "explicit_local_only_allow_r54_current_snapshot_20260627"
P7_R54_CLR04_REVIEW_SESSION_PRESENT_REF: Final = "r54_current_snapshot_review_session_id_present"
P7_R54_CLR04_MANIFEST_SOURCE_AVAILABLE_REF: Final = "r54_p5_human_blind_qa_24_case_manifest_source_available"
P7_R54_CLR04_EXPORT_DENYLIST_READY_REF: Final = "r54_current_snapshot_export_denylist_ready"
P7_R54_CLR04_PURGE_PLAN_READY_REF: Final = "r54_current_snapshot_body_full_packet_purge_plan_ready"
P7_R54_CLR04_EXPORT_DENYLIST_REFS: Final[tuple[str, ...]] = (
    "raw_input",
    "returned_emlis_body",
    "history_surface",
    "reviewer_free_text",
    "reviewer_notes_body",
    "question_text",
    "draft_question_text",
    "local_absolute_path",
    "body_hash",
    "packet_content",
    "terminal_output_body",
)
P7_R54_CLR04_FORBIDDEN_OUTPUT_REFS: Final[tuple[str, ...]] = (
    "body_full_packet_artifact_export",
    "raw_input_export",
    "returned_emlis_body_export",
    "history_surface_export",
    "reviewer_free_text_export",
    "question_text_export",
    "local_path_or_hash_export",
    "terminal_output_body_export",
)

P7_R54_CLR05_MANIFEST_READY_STATUS_REF: Final = "MANIFEST_FROZEN_READY_FOR_BODYFREE_PACKET_GENERATION_REQUEST"
P7_R54_CLR05_MANIFEST_BLOCKED_STATUS_REF: Final = "MANIFEST_BLOCKED_BY_LOCAL_ONLY_PREFLIGHT"
P7_R54_CLR05_ALLOWED_MANIFEST_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_CLR05_MANIFEST_READY_STATUS_REF,
    P7_R54_CLR05_MANIFEST_BLOCKED_STATUS_REF,
)
P7_R54_CLR05_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "R54-CLR-05_repair_24_case_manifest_before_packet_generation_request"
P7_R54_CLR05_READY_REASON_REF: Final = "r54_current_snapshot_24_case_manifest_frozen_bodyfree"
P7_R54_CLR05_MANIFEST_SOURCE_KIND_REF: Final = "r48_p5_first_formal_24_case_matrix_bodyfree_source"
P7_R54_CLR05_REVIEW_AXIS_PROFILE_REF: Final = "r54_p5_history_line_existing_6_axis_profile_20260627"
P7_R54_CLR05_CURRENT_ONLY_BOUNDARY_FAMILY_REFS: Final[tuple[str, ...]] = (
    "low_information_history_not_eligible",
    "free_tier_history_present_not_allowed",
)
P7_R54_CLR05_CASE_DISTRIBUTION: Final[dict[str, int]] = dict(r54op.P7_R54_OP05_CASE_DISTRIBUTION)
P7_R54_CLR05_RATING_AXIS_REFS: Final[tuple[str, ...]] = tuple(r54op.P7_R54_OP09_RATING_AXIS_REFS)
P7_R54_CLR05_RATING_AXIS_TARGET_THRESHOLDS: Final[dict[str, float]] = dict(
    r54op.P7_R54_OP09_RATING_AXIS_TARGET_THRESHOLDS
)
P7_R54_CLR05_CASE_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "case_index",
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
    "case_role_family_ref",
    "plan_tier_context_ref",
    "review_axis_profile_ref",
    "requires_history_line_review",
    "current_only_boundary_case",
    "body_free",
)

P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR04: Final[tuple[str, ...]] = clr03.P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR01[3:]
P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR05: Final[tuple[str, ...]] = clr03.P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR01[4:]
P7_R54_CLR04_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *clr03.P7_R54_CLR03_IMPLEMENTED_STEPS,
    P7_R54_CLR04_STEP_REF,
)
P7_R54_CLR04_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR04
P7_R54_CLR05_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_CLR04_IMPLEMENTED_STEPS,
    P7_R54_CLR05_STEP_REF,
)
P7_R54_CLR05_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR05

P7_R54_CLR04_LOCAL_ONLY_PREFLIGHT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *clr03.P7_R54_CLR_COMMON_REQUIRED_FIELD_REFS,
    "clr03_schema_version",
    "clr03_material_ref",
    "clr03_next_required_step",
    "clr03_r55_hold_state_preserved",
    "clr03_actual_review_evidence_missing_before_run",
    "clr03_r52_reintake_handoff_status_ref",
    "explicit_local_only_allow_ref",
    "explicit_local_only_allow_present",
    "review_session_present",
    "review_session_present_ref",
    "current_snapshot_basis_refreeze_ready",
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
    "no_api_db_rn_runtime_touch",
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
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    *clr03.P7_R54_CLR_CURRENT_REF_REQUIRED_FIELD_REFS,
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *clr03.P7_R54_CLR_NO_TOUCH_BODYFREE_REQUIRED_FIELD_REFS,
    *clr03.P7_R54_CLR_FALSE_FLAG_REFS,
)
P7_R54_CLR05_24_CASE_MANIFEST_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *clr03.P7_R54_CLR_COMMON_REQUIRED_FIELD_REFS,
    "clr04_schema_version",
    "clr04_material_ref",
    "clr04_next_required_step",
    "clr04_preflight_status",
    "clr04_body_full_packet_generation_allowed_by_preflight",
    "local_only_preflight_ready",
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
    "manifest_rows",
    "manifest_row_count",
    "manifest_rows_bodyfree_only",
    "case_ref_ids",
    "case_ref_id_count",
    "case_ref_id_unique",
    "blind_case_ids",
    "blind_case_id_count",
    "blind_case_id_unique",
    "packet_ref_ids",
    "packet_ref_id_count",
    "packet_ref_id_unique",
    "case_role_family_counts",
    "plan_tier_context_counts",
    "review_axis_profile_ref",
    "rating_axis_refs",
    "rating_axis_count",
    "rating_axis_target_thresholds",
    "requires_history_line_review_count",
    "current_only_boundary_case_count",
    "p4_r11_rows_mixed_in",
    "p4_r11_audit_rows_converted_to_r54_actual_review_cases",
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
    markers = body_free_flags(include_history=True, include_reviewer=True, include_terminal=True)
    markers.update(
        {
            "raw_body_included": False,
            "returned_emlis_body_included": False,
            "history_surface_included": False,
            "reviewer_note_included": False,
            "reviewer_notes_included": False,
            "reviewer_notes_body_included": False,
            "packet_content_included": False,
            "question_text_included": False,
            "draft_question_text_included": False,
            "local_path_included": False,
            "local_absolute_path_included": False,
            "body_hash_included": False,
            "terminal_output_body_included": False,
        }
    )
    return markers


def _no_touch_contract() -> dict[str, bool]:
    return {
        "api_changed": False,
        "db_changed": False,
        "rn_changed": False,
        "runtime_changed": False,
        "public_response_key_changed": False,
        "question_implementation_started_here": False,
        "body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "actual_review_evidence_complete": False,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "full_backend_suite_green_confirmed": False,
        "real_device_modal_verified": False,
    }


def _contains_forbidden_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in clr03.P7_R54_CLR_FORBIDDEN_BODY_OR_QUESTION_KEYS:
                return True
            if _contains_forbidden_key(child):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_key(child) for child in value)
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
    if data.get("step") != P7_R54_CLR_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R54_CLR_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("policy_kind") != P7_R54_CLR_POLICY_KIND:
        raise ValueError(f"{source} policy kind changed")
    if data.get("policy_section") != policy_section or data.get("operation_step_ref") != operation_step_ref:
        raise ValueError(f"{source} operation step changed")
    if data.get("source_mode") != P7_SOURCE_MODE:
        raise ValueError(f"{source} must remain local snapshot")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} must not require or perform Git checks")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must remain body-free")
    assert_false_markers(data.get("public_contract") or {}, source=f"{source}.public_contract")
    assert_false_markers(data.get("r54_clr_no_touch_contract") or {}, source=f"{source}.r54_clr_no_touch_contract")
    assert_false_markers(data.get("body_free_markers") or {}, source=f"{source}.body_free_markers")
    for key in clr03.P7_R54_CLR_FALSE_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=False")
    if _contains_forbidden_key(data):
        raise ValueError(f"{source} contains a forbidden body or question payload key")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)


def _assert_current_refs(data: Mapping[str, Any], *, source: str) -> None:
    refs = safe_mapping(data.get("operation_current_refs"))
    if refs != clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError(f"{source} operation current refs changed")
    if data.get("operation_current_ref_count") != len(clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS):
        raise ValueError(f"{source} operation current ref count changed")
    if tuple(data.get("operation_current_ref_keys") or ()) != clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS:
        raise ValueError(f"{source} operation current ref keys changed")
    if data.get("operation_current_ref_key_count") != len(clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS):
        raise ValueError(f"{source} operation current ref key count changed")
    if tuple(data.get("required_current_snapshot_ref_keys") or ()) != clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS:
        raise ValueError(f"{source} required current snapshot ref keys changed")
    if data.get("required_current_snapshot_ref_key_count") != len(clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS):
        raise ValueError(f"{source} required current snapshot ref key count changed")
    if data.get("all_required_current_refs_present") is not True:
        raise ValueError(f"{source} must carry all required current refs")
    if data.get("actual_review_basis_ref") != clr03.P7_R54_CLR_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError(f"{source} actual review basis ref changed")
    if data.get("actual_review_basis_allowed") != clr03.P7_R54_CLR_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError(f"{source} actual review basis allowed ref changed")
    if data.get("operation_current_refs_are_actual_review_basis") is not True:
        raise ValueError(f"{source} current refs actual review basis flag changed")
    if data.get("operation_current_refs_used_as_actual_review_basis") is not True:
        raise ValueError(f"{source} current refs used-as-actual-review-basis flag changed")


def _current_ref_fields() -> dict[str, Any]:
    return {
        "operation_current_refs": dict(clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_count": len(clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_keys": list(clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS),
        "operation_current_ref_key_count": len(clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "required_current_snapshot_ref_keys": list(clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS),
        "required_current_snapshot_ref_key_count": len(clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "all_required_current_refs_present": True,
        "actual_review_basis_ref": clr03.P7_R54_CLR_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": clr03.P7_R54_CLR_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "operation_current_refs_used_as_actual_review_basis": True,
    }


def _safe_review_session_id(value: Any) -> str:
    return clean_identifier(value, default=P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID, max_length=220)


def _preflight_status_and_blockers(
    *,
    explicit_local_only_allow_present: bool,
    review_session_present: bool,
    current_snapshot_basis_refreeze_ready: bool,
    historical_helper_refs_reconciled_before_preflight: bool,
    r55_hold_intaken_before_preflight: bool,
    manifest_source_available: bool,
    export_denylist_ready: bool,
    purge_plan_ready: bool,
    no_api_db_rn_runtime_touch: bool,
) -> tuple[str, list[str], list[str]]:
    blockers: list[str] = []
    reasons: list[str] = []
    if not explicit_local_only_allow_present:
        blockers.append("review_packet_generation_blocked_missing_explicit_allow")
        reasons.append("explicit_local_only_allow_missing")
    if not review_session_present:
        blockers.append("reviewer_not_assigned")
        reasons.append("review_session_id_missing")
    if not current_snapshot_basis_refreeze_ready:
        blockers.append("body_free_validation_failed")
        reasons.append("current_snapshot_basis_refreeze_not_ready")
    if not historical_helper_refs_reconciled_before_preflight:
        blockers.append("body_free_validation_failed")
        reasons.append("historical_helper_refs_reconcile_not_ready")
    if not r55_hold_intaken_before_preflight:
        blockers.append("body_free_validation_failed")
        reasons.append("r55_hold_intake_not_ready")
    if not manifest_source_available:
        blockers.append("review_case_material_missing")
        reasons.append("manifest_source_missing")
    if not export_denylist_ready:
        blockers.append("body_free_validation_failed")
        reasons.append("export_denylist_not_ready")
    if not purge_plan_ready:
        blockers.append("body_purge_not_verified")
        reasons.append("purge_plan_not_ready")
    if not no_api_db_rn_runtime_touch:
        blockers.append("no_touch_violation_detected")
        reasons.append("api_db_rn_runtime_touch_detected")
    blockers = dedupe_identifiers(blockers, limit=40, max_length=180)
    reasons = dedupe_identifiers(reasons, limit=40, max_length=180)
    if blockers:
        return P7_R54_CLR04_PREFLIGHT_BLOCKED_STATUS_REF, reasons, blockers
    return P7_R54_CLR04_PREFLIGHT_READY_STATUS_REF, [P7_R54_CLR04_READY_REASON_REF], []


def build_p7_r54_clr04_local_only_preflight(
    *,
    r55_hold_evidence_missing_intake: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
    explicit_local_only_allow_ref: Any = P7_R54_CLR04_EXPLICIT_LOCAL_ONLY_ALLOW_REF,
    manifest_source_ref: Any = P7_R54_CLR04_MANIFEST_SOURCE_AVAILABLE_REF,
    export_denylist_ref: Any = P7_R54_CLR04_EXPORT_DENYLIST_READY_REF,
    purge_plan_ref: Any = P7_R54_CLR04_PURGE_PLAN_READY_REF,
    no_api_db_rn_runtime_touch: bool = True,
) -> dict[str, Any]:
    """Build R54-CLR-04 body-free local-only preflight material."""

    prior = dict(r55_hold_evidence_missing_intake or clr03.build_p7_r54_clr03_r55_hold_evidence_missing_intake())
    clr03.assert_p7_r54_clr03_r55_hold_evidence_missing_intake_contract(prior)
    session_id = _safe_review_session_id(review_session_id or prior.get("review_session_id"))
    explicit_ref = clean_identifier(explicit_local_only_allow_ref, default="missing_explicit_local_only_allow_ref", max_length=220)
    manifest_ref = clean_identifier(manifest_source_ref, default="missing_manifest_source_ref", max_length=220)
    export_ref = clean_identifier(export_denylist_ref, default="missing_export_denylist_ref", max_length=220)
    purge_ref = clean_identifier(purge_plan_ref, default="missing_purge_plan_ref", max_length=220)
    explicit_present = explicit_ref == P7_R54_CLR04_EXPLICIT_LOCAL_ONLY_ALLOW_REF
    review_session_present = bool(session_id)
    current_refreeze_ready = prior.get("current_snapshot_basis_preserved") is True
    historical_reconciled = prior.get("historical_helper_refs_reconciled_before_hold_intake") is True
    r55_intaken = prior.get("r55_hold_state_preserved") is True
    manifest_available = manifest_ref == P7_R54_CLR04_MANIFEST_SOURCE_AVAILABLE_REF
    export_ready = export_ref == P7_R54_CLR04_EXPORT_DENYLIST_READY_REF
    purge_ready = purge_ref == P7_R54_CLR04_PURGE_PLAN_READY_REF
    status, reasons, blockers = _preflight_status_and_blockers(
        explicit_local_only_allow_present=explicit_present,
        review_session_present=review_session_present,
        current_snapshot_basis_refreeze_ready=current_refreeze_ready,
        historical_helper_refs_reconciled_before_preflight=historical_reconciled,
        r55_hold_intaken_before_preflight=r55_intaken,
        manifest_source_available=manifest_available,
        export_denylist_ready=export_ready,
        purge_plan_ready=purge_ready,
        no_api_db_rn_runtime_touch=no_api_db_rn_runtime_touch is True,
    )
    ready = status == P7_R54_CLR04_PREFLIGHT_READY_STATUS_REF
    material: dict[str, Any] = {
        "schema_version": P7_R54_CLR04_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_CLR_STEP,
        "scope": P7_R54_CLR_SCOPE,
        "policy_kind": P7_R54_CLR_POLICY_KIND,
        "policy_section": P7_R54_CLR04_STEP_REF,
        "operation_step_ref": P7_R54_CLR04_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_clr04_local_only_preflight_20260627",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "clr03_schema_version": prior["schema_version"],
        "clr03_material_ref": prior["material_id"],
        "clr03_next_required_step": prior["next_required_step"],
        "clr03_r55_hold_state_preserved": prior["r55_hold_state_preserved"],
        "clr03_actual_review_evidence_missing_before_run": prior["actual_review_evidence_missing_before_run"],
        "clr03_r52_reintake_handoff_status_ref": prior["r52_reintake_handoff_status_ref"],
        "explicit_local_only_allow_ref": explicit_ref,
        "explicit_local_only_allow_present": explicit_present,
        "review_session_present": review_session_present,
        "review_session_present_ref": P7_R54_CLR04_REVIEW_SESSION_PRESENT_REF,
        "current_snapshot_basis_refreeze_ready": current_refreeze_ready,
        "historical_helper_refs_reconciled_before_preflight": historical_reconciled,
        "r55_hold_intaken_before_preflight": r55_intaken,
        "manifest_source_ref": manifest_ref,
        "manifest_source_available": manifest_available,
        "export_denylist_ref": export_ref,
        "export_denylist_ready": export_ready,
        "export_denylist_refs": list(P7_R54_CLR04_EXPORT_DENYLIST_REFS),
        "export_denylist_ref_count": len(P7_R54_CLR04_EXPORT_DENYLIST_REFS),
        "forbidden_output_refs": list(P7_R54_CLR04_FORBIDDEN_OUTPUT_REFS),
        "forbidden_output_ref_count": len(P7_R54_CLR04_FORBIDDEN_OUTPUT_REFS),
        "purge_plan_ref": purge_ref,
        "purge_plan_ready": purge_ready,
        "no_api_db_rn_runtime_touch": no_api_db_rn_runtime_touch is True,
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
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        **_current_ref_fields(),
        "implemented_steps": list(P7_R54_CLR04_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_CLR04_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_CLR05_STEP_REF if ready else P7_R54_CLR04_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_clr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_clr04_local_only_preflight_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(data, required=P7_R54_CLR04_LOCAL_ONLY_PREFLIGHT_REQUIRED_FIELD_REFS, source="P7-R54-CLR04")
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_CLR04_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION,
        policy_section=P7_R54_CLR04_STEP_REF,
        operation_step_ref=P7_R54_CLR04_STEP_REF,
        source="P7-R54-CLR04",
    )
    _assert_current_refs(data, source="P7-R54-CLR04")
    if data.get("clr03_schema_version") != clr03.P7_R54_CLR_R55_HOLD_EVIDENCE_MISSING_INTAKE_SCHEMA_VERSION:
        raise ValueError("P7-R54-CLR04 must follow CLR03")
    if data.get("clr03_next_required_step") != P7_R54_CLR04_STEP_REF:
        raise ValueError("P7-R54-CLR04 CLR03 next step changed")
    if data.get("clr03_actual_review_evidence_missing_before_run") is not True:
        raise ValueError("P7-R54-CLR04 must preserve evidence missing")
    if data.get("clr03_r52_reintake_handoff_status_ref") != clr03.P7_R54_CLR03_R52_REINTAKE_BLOCKED_STATUS_REF:
        raise ValueError("P7-R54-CLR04 must preserve R52 evidence-missing hold")
    if data.get("preflight_status") not in P7_R54_CLR04_ALLOWED_PREFLIGHT_STATUS_REFS:
        raise ValueError("P7-R54-CLR04 preflight status changed")
    if tuple(data.get("export_denylist_refs") or ()) != P7_R54_CLR04_EXPORT_DENYLIST_REFS:
        raise ValueError("P7-R54-CLR04 export denylist refs changed")
    if data.get("export_denylist_ref_count") != len(P7_R54_CLR04_EXPORT_DENYLIST_REFS):
        raise ValueError("P7-R54-CLR04 export denylist count changed")
    if tuple(data.get("forbidden_output_refs") or ()) != P7_R54_CLR04_FORBIDDEN_OUTPUT_REFS:
        raise ValueError("P7-R54-CLR04 forbidden output refs changed")
    for key in (
        "review_session_present",
        "current_snapshot_basis_refreeze_ready",
        "historical_helper_refs_reconciled_before_preflight",
        "r55_hold_intaken_before_preflight",
        "body_full_generation_blocked_until_manifest_freeze",
        "actual_review_execution_blocked_until_packet_and_manifest_ready",
        "human_review_completion_claim_blocked_here",
        "actual_review_completion_claim_blocked_here",
        "actual_human_review_completion_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-CLR04 must keep {key}=True")
    if data.get("body_full_packet_generation_allowed_before_preflight") is not False:
        raise ValueError("P7-R54-CLR04 must not allow body-full generation before preflight")
    if data.get("body_full_packet_generation_request_allowed_next") is not False:
        raise ValueError("P7-R54-CLR04 must wait for CLR05 before request")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("P7-R54-CLR04 open blockers must match blockers")
    ready = data.get("preflight_status") == P7_R54_CLR04_PREFLIGHT_READY_STATUS_REF
    if ready:
        for key in (
            "explicit_local_only_allow_present",
            "manifest_source_available",
            "export_denylist_ready",
            "purge_plan_ready",
            "no_api_db_rn_runtime_touch",
            "body_full_packet_generation_allowed_by_preflight",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-CLR04 ready preflight must keep {key}=True")
        if blockers:
            raise ValueError("P7-R54-CLR04 ready preflight must not carry blockers")
        if data.get("preflight_reason_refs") != [P7_R54_CLR04_READY_REASON_REF]:
            raise ValueError("P7-R54-CLR04 ready reason changed")
        if data.get("next_required_step") != P7_R54_CLR05_STEP_REF:
            raise ValueError("P7-R54-CLR04 ready next step changed")
    else:
        if data.get("body_full_packet_generation_allowed_by_preflight") is not False:
            raise ValueError("P7-R54-CLR04 blocked preflight must not allow generation")
        if not blockers:
            raise ValueError("P7-R54-CLR04 blocked preflight must carry blockers")
        if data.get("next_required_step") != P7_R54_CLR04_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-CLR04 blocked next step changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_CLR04_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-CLR04 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_CLR04_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-CLR04 not-yet steps changed")
    return True


def _unique_non_empty(values: Sequence[str], *, required_count: int) -> bool:
    return len(values) == required_count and all(values) and len(set(values)) == len(values)


def _count_by(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = clean_identifier(safe_mapping(row).get(key), default="unknown", max_length=180)
        counts[value] = counts.get(value, 0) + 1
    return counts


def _manifest_row(source: Mapping[str, Any], *, index: int) -> dict[str, Any]:
    row = safe_mapping(source)
    family_ref = clean_identifier(row.get("family"), default="unknown_family", max_length=180)
    tier_ref = clean_identifier(row.get("subscription_tier_ref"), default="unknown", max_length=80)
    current_only_boundary = family_ref in P7_R54_CLR05_CURRENT_ONLY_BOUNDARY_FAMILY_REFS
    return {
        "case_index": index,
        "case_ref_id": clean_identifier(row.get("case_ref_id"), max_length=180),
        "blind_case_id": clean_identifier(row.get("blind_case_id"), max_length=180),
        "packet_ref_id": clean_identifier(row.get("packet_ref_id"), max_length=180),
        "case_role_family_ref": family_ref,
        "plan_tier_context_ref": tier_ref,
        "review_axis_profile_ref": P7_R54_CLR05_REVIEW_AXIS_PROFILE_REF,
        "requires_history_line_review": not current_only_boundary,
        "current_only_boundary_case": current_only_boundary,
        "body_free": True,
    }


def _assert_manifest_row(row: Mapping[str, Any], *, expected_index: int) -> None:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R54_CLR05_CASE_ROW_REQUIRED_FIELD_REFS, source="P7-R54-CLR05 row")
    if data.get("case_index") != expected_index:
        raise ValueError("P7-R54-CLR05 row case index changed")
    if data.get("body_free") is not True:
        raise ValueError("P7-R54-CLR05 row must be body-free")
    if not data.get("case_ref_id") or not data.get("blind_case_id") or not data.get("packet_ref_id"):
        raise ValueError("P7-R54-CLR05 row safe refs must be present")
    if data.get("review_axis_profile_ref") != P7_R54_CLR05_REVIEW_AXIS_PROFILE_REF:
        raise ValueError("P7-R54-CLR05 row review axis profile changed")
    boundary = data.get("case_role_family_ref") in P7_R54_CLR05_CURRENT_ONLY_BOUNDARY_FAMILY_REFS
    if data.get("current_only_boundary_case") is not boundary:
        raise ValueError("P7-R54-CLR05 row boundary flag changed")
    if data.get("requires_history_line_review") is not (not boundary):
        raise ValueError("P7-R54-CLR05 row history-line flag changed")
    assert_p7_no_body_payload_or_contract_mutation(data, source="P7-R54-CLR05 row")


def build_p7_r54_clr05_24_case_manifest_freeze(
    *,
    local_only_preflight: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build R54-CLR-05 body-free 24-case manifest freeze material."""

    preflight = dict(local_only_preflight or build_p7_r54_clr04_local_only_preflight())
    assert_p7_r54_clr04_local_only_preflight_contract(preflight)
    preflight_ready = preflight.get("preflight_status") == P7_R54_CLR04_PREFLIGHT_READY_STATUS_REF
    source_rows: list[dict[str, Any]] = []
    r48_material_ref = "not_materialized_until_preflight_ready"
    if preflight_ready:
        matrix = r54op.build_p7_r48_p5_first_formal_review_case_matrix(
            review_session_id=preflight.get("review_session_id"),
            session_short_ref="r54clr",
            material_id="p7_r54_clr05_r48_first_formal_case_matrix_basis_20260627",
        )
        r54op.assert_p7_r48_p5_first_formal_review_case_matrix_contract(matrix)
        r48_material_ref = clean_identifier(matrix.get("material_id"), max_length=220)
        source_rows = [dict(safe_mapping(row)) for row in matrix.get("case_rows") or []]
    manifest_rows = [_manifest_row(row, index=index) for index, row in enumerate(source_rows, start=1)]
    case_refs = [clean_identifier(row.get("case_ref_id"), max_length=180) for row in manifest_rows]
    blind_ids = [clean_identifier(row.get("blind_case_id"), max_length=180) for row in manifest_rows]
    packet_refs = [clean_identifier(row.get("packet_ref_id"), max_length=180) for row in manifest_rows]
    family_counts = _count_by(manifest_rows, "case_role_family_ref")
    tier_counts = _count_by(manifest_rows, "plan_tier_context_ref")
    required_count = clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
    manifest_ready = bool(
        preflight_ready
        and len(manifest_rows) == required_count
        and family_counts == P7_R54_CLR05_CASE_DISTRIBUTION
        and _unique_non_empty(case_refs, required_count=required_count)
        and _unique_non_empty(blind_ids, required_count=required_count)
        and _unique_non_empty(packet_refs, required_count=required_count)
    )
    blockers = [] if manifest_ready else dedupe_identifiers(
        ["review_case_matrix_minimum_not_met", *(preflight.get("open_execution_blocker_ids") or [])],
        limit=40,
        max_length=180,
    )
    reasons = (
        [P7_R54_CLR05_READY_REASON_REF]
        if manifest_ready
        else dedupe_identifiers(
            ["local_only_preflight_not_ready_for_24_case_manifest_freeze", *(preflight.get("preflight_reason_refs") or [])],
            limit=40,
            max_length=180,
        )
    )
    material: dict[str, Any] = {
        "schema_version": P7_R54_CLR05_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_CLR_STEP,
        "scope": P7_R54_CLR_SCOPE,
        "policy_kind": P7_R54_CLR_POLICY_KIND,
        "policy_section": P7_R54_CLR05_STEP_REF,
        "operation_step_ref": P7_R54_CLR05_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_clr05_24_case_manifest_freeze_20260627",
        "review_session_id": _safe_review_session_id(review_session_id or preflight.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "clr04_schema_version": preflight["schema_version"],
        "clr04_material_ref": preflight["material_id"],
        "clr04_next_required_step": preflight["next_required_step"],
        "clr04_preflight_status": preflight["preflight_status"],
        "clr04_body_full_packet_generation_allowed_by_preflight": preflight[
            "body_full_packet_generation_allowed_by_preflight"
        ],
        "local_only_preflight_ready": preflight_ready,
        "manifest_source_kind_ref": P7_R54_CLR05_MANIFEST_SOURCE_KIND_REF,
        "r48_case_matrix_schema_version": r54op.P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION,
        "r48_case_matrix_material_ref": r48_material_ref,
        "r48_case_matrix_case_count": len(source_rows),
        "required_case_count": required_count,
        "case_distribution": dict(P7_R54_CLR05_CASE_DISTRIBUTION),
        "case_distribution_total_count": sum(P7_R54_CLR05_CASE_DISTRIBUTION.values()),
        "case_distribution_matches_design": family_counts == P7_R54_CLR05_CASE_DISTRIBUTION if manifest_ready else False,
        "manifest_status": P7_R54_CLR05_MANIFEST_READY_STATUS_REF if manifest_ready else P7_R54_CLR05_MANIFEST_BLOCKED_STATUS_REF,
        "manifest_reason_refs": reasons,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "manifest_rows": manifest_rows if manifest_ready else [],
        "manifest_row_count": len(manifest_rows) if manifest_ready else 0,
        "manifest_rows_bodyfree_only": manifest_ready,
        "case_ref_ids": case_refs if manifest_ready else [],
        "case_ref_id_count": len(case_refs) if manifest_ready else 0,
        "case_ref_id_unique": _unique_non_empty(case_refs, required_count=required_count) if manifest_ready else False,
        "blind_case_ids": blind_ids if manifest_ready else [],
        "blind_case_id_count": len(blind_ids) if manifest_ready else 0,
        "blind_case_id_unique": _unique_non_empty(blind_ids, required_count=required_count) if manifest_ready else False,
        "packet_ref_ids": packet_refs if manifest_ready else [],
        "packet_ref_id_count": len(packet_refs) if manifest_ready else 0,
        "packet_ref_id_unique": _unique_non_empty(packet_refs, required_count=required_count) if manifest_ready else False,
        "case_role_family_counts": family_counts if manifest_ready else {},
        "plan_tier_context_counts": tier_counts if manifest_ready else {},
        "review_axis_profile_ref": P7_R54_CLR05_REVIEW_AXIS_PROFILE_REF,
        "rating_axis_refs": list(P7_R54_CLR05_RATING_AXIS_REFS),
        "rating_axis_count": len(P7_R54_CLR05_RATING_AXIS_REFS),
        "rating_axis_target_thresholds": dict(P7_R54_CLR05_RATING_AXIS_TARGET_THRESHOLDS),
        "requires_history_line_review_count": sum(1 for row in manifest_rows if row["requires_history_line_review"]) if manifest_ready else 0,
        "current_only_boundary_case_count": sum(1 for row in manifest_rows if row["current_only_boundary_case"]) if manifest_ready else 0,
        "p4_r11_rows_mixed_in": False,
        "p4_r11_audit_rows_converted_to_r54_actual_review_cases": False,
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
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        **_current_ref_fields(),
        "implemented_steps": list(P7_R54_CLR05_IMPLEMENTED_STEPS if manifest_ready else P7_R54_CLR04_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_CLR05_NOT_YET_IMPLEMENTED_STEPS if manifest_ready else P7_R54_CLR04_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_CLR06_STEP_REF if manifest_ready else P7_R54_CLR05_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_clr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_clr05_24_case_manifest_freeze_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(data, required=P7_R54_CLR05_24_CASE_MANIFEST_FREEZE_REQUIRED_FIELD_REFS, source="P7-R54-CLR05")
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_CLR05_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION,
        policy_section=P7_R54_CLR05_STEP_REF,
        operation_step_ref=P7_R54_CLR05_STEP_REF,
        source="P7-R54-CLR05",
    )
    _assert_current_refs(data, source="P7-R54-CLR05")
    if data.get("clr04_schema_version") != P7_R54_CLR04_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION:
        raise ValueError("P7-R54-CLR05 must follow CLR04")
    if data.get("clr04_preflight_status") not in P7_R54_CLR04_ALLOWED_PREFLIGHT_STATUS_REFS:
        raise ValueError("P7-R54-CLR05 CLR04 status changed")
    if data.get("required_case_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-CLR05 required case count changed")
    if data.get("r48_case_matrix_schema_version") != r54op.P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION:
        raise ValueError("P7-R54-CLR05 R48 case matrix schema changed")
    if data.get("case_distribution") != P7_R54_CLR05_CASE_DISTRIBUTION:
        raise ValueError("P7-R54-CLR05 case distribution changed")
    if data.get("case_distribution_total_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-CLR05 case distribution total changed")
    if tuple(data.get("rating_axis_refs") or ()) != P7_R54_CLR05_RATING_AXIS_REFS:
        raise ValueError("P7-R54-CLR05 rating axis refs changed")
    if data.get("rating_axis_count") != len(P7_R54_CLR05_RATING_AXIS_REFS):
        raise ValueError("P7-R54-CLR05 rating axis count changed")
    if safe_mapping(data.get("rating_axis_target_thresholds")) != P7_R54_CLR05_RATING_AXIS_TARGET_THRESHOLDS:
        raise ValueError("P7-R54-CLR05 thresholds changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("P7-R54-CLR05 open blockers must match blockers")
    for key in (
        "p4_r11_rows_mixed_in",
        "p4_r11_audit_rows_converted_to_r54_actual_review_cases",
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
            raise ValueError(f"P7-R54-CLR05 must keep {key}=False")
    for key in (
        "body_full_generation_blocked_until_packet_generation_request",
        "human_review_completion_claim_blocked_here",
        "actual_review_completion_claim_blocked_here",
        "actual_human_review_completion_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-CLR05 must keep {key}=True")
    ready = data.get("manifest_status") == P7_R54_CLR05_MANIFEST_READY_STATUS_REF
    rows = [safe_mapping(row) for row in (data.get("manifest_rows") or [])]
    if ready:
        if data.get("clr04_preflight_status") != P7_R54_CLR04_PREFLIGHT_READY_STATUS_REF:
            raise ValueError("P7-R54-CLR05 ready manifest requires ready CLR04")
        if data.get("clr04_body_full_packet_generation_allowed_by_preflight") is not True:
            raise ValueError("P7-R54-CLR05 ready manifest requires preflight allowance")
        if data.get("local_only_preflight_ready") is not True:
            raise ValueError("P7-R54-CLR05 ready manifest requires preflight ready")
        if data.get("manifest_reason_refs") != [P7_R54_CLR05_READY_REASON_REF]:
            raise ValueError("P7-R54-CLR05 ready reason changed")
        if blockers:
            raise ValueError("P7-R54-CLR05 ready manifest must not carry blockers")
        required_count = clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        if len(rows) != required_count or data.get("manifest_row_count") != required_count:
            raise ValueError("P7-R54-CLR05 must freeze 24 rows")
        for index, row in enumerate(rows, start=1):
            _assert_manifest_row(row, expected_index=index)
        case_refs = [clean_identifier(row.get("case_ref_id"), max_length=180) for row in rows]
        blind_ids = [clean_identifier(row.get("blind_case_id"), max_length=180) for row in rows]
        packet_refs = [clean_identifier(row.get("packet_ref_id"), max_length=180) for row in rows]
        family_counts = _count_by(rows, "case_role_family_ref")
        tier_counts = _count_by(rows, "plan_tier_context_ref")
        if data.get("case_ref_ids") != case_refs or data.get("case_ref_id_count") != required_count:
            raise ValueError("P7-R54-CLR05 case ref list changed")
        if data.get("blind_case_ids") != blind_ids or data.get("blind_case_id_count") != required_count:
            raise ValueError("P7-R54-CLR05 blind case id list changed")
        if data.get("packet_ref_ids") != packet_refs or data.get("packet_ref_id_count") != required_count:
            raise ValueError("P7-R54-CLR05 packet ref list changed")
        if family_counts != P7_R54_CLR05_CASE_DISTRIBUTION or data.get("case_role_family_counts") != family_counts:
            raise ValueError("P7-R54-CLR05 family counts changed")
        if data.get("plan_tier_context_counts") != tier_counts:
            raise ValueError("P7-R54-CLR05 tier counts changed")
        for key, values in (
            ("case_ref_id_unique", case_refs),
            ("blind_case_id_unique", blind_ids),
            ("packet_ref_id_unique", packet_refs),
        ):
            if data.get(key) is not True or not _unique_non_empty(values, required_count=required_count):
                raise ValueError(f"P7-R54-CLR05 {key} failed")
        if data.get("manifest_rows_bodyfree_only") is not True:
            raise ValueError("P7-R54-CLR05 manifest rows must be body-free")
        if data.get("case_distribution_matches_design") is not True:
            raise ValueError("P7-R54-CLR05 distribution must match design")
        if data.get("requires_history_line_review_count") != 20:
            raise ValueError("P7-R54-CLR05 history-line count changed")
        if data.get("current_only_boundary_case_count") != 4:
            raise ValueError("P7-R54-CLR05 current-only boundary count changed")
        if data.get("body_full_packet_generation_request_allowed_next") is not True:
            raise ValueError("P7-R54-CLR05 ready manifest must allow next request step")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_CLR05_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR05 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_CLR05_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR05 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_CLR06_STEP_REF:
            raise ValueError("P7-R54-CLR05 next step changed")
    else:
        if data.get("manifest_status") != P7_R54_CLR05_MANIFEST_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-CLR05 blocked status changed")
        if data.get("body_full_packet_generation_request_allowed_next") is not False:
            raise ValueError("P7-R54-CLR05 blocked manifest must not allow packet request")
        if data.get("manifest_rows") != [] or data.get("manifest_row_count") != 0:
            raise ValueError("P7-R54-CLR05 blocked manifest must not carry rows")
        if not blockers:
            raise ValueError("P7-R54-CLR05 blocked manifest must carry blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_CLR04_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR05 blocked implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_CLR04_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR05 blocked not-yet steps changed")
        if data.get("next_required_step") != P7_R54_CLR05_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-CLR05 blocked next step changed")
    return True


build_p7_r54_current_snapshot_local_run_clr04_local_only_preflight = build_p7_r54_clr04_local_only_preflight
assert_p7_r54_current_snapshot_local_run_clr04_local_only_preflight_contract = (
    assert_p7_r54_clr04_local_only_preflight_contract
)
build_p7_r54_current_snapshot_local_only_preflight_bodyfree = build_p7_r54_clr04_local_only_preflight
assert_p7_r54_current_snapshot_local_only_preflight_bodyfree_contract = (
    assert_p7_r54_clr04_local_only_preflight_contract
)
build_p7_r54_current_snapshot_local_run_clr05_24_case_manifest_freeze = build_p7_r54_clr05_24_case_manifest_freeze
assert_p7_r54_current_snapshot_local_run_clr05_24_case_manifest_freeze_contract = (
    assert_p7_r54_clr05_24_case_manifest_freeze_contract
)
build_p7_r54_current_snapshot_24_case_manifest_freeze_bodyfree = build_p7_r54_clr05_24_case_manifest_freeze
assert_p7_r54_current_snapshot_24_case_manifest_freeze_bodyfree_contract = (
    assert_p7_r54_clr05_24_case_manifest_freeze_contract
)
