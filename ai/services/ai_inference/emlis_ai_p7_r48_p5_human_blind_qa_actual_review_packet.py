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

This module intentionally does not create JSON schema files, body-full reviewer
packets, rating rows, blocker rows, disposal receipts, or handoff summaries. It
also does not start or confirm P5 human review, start P6 readfeel, run
real-device review, close HOLD-004, complete P7, open P8, or permit release.
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
    P5_HUMAN_BLIND_QA_HOLD_REF,
    P5_HUMAN_BLIND_QA_RATING_AXES,
    P5_HUMAN_BLIND_QA_RETURN_HOLD_REF,
    P5_HUMAN_BLIND_QA_TARGETS,
    P6_LIMITED_HUMAN_READFEEL_HOLD_REF,
    P6_LIMITED_HUMAN_READFEEL_RETURN_HOLD_REF,
)
from emlis_ai_p7_r46_real_device_modal_review_closed_validation import (
    HOLD_DC_FULL_BACKEND_SUITE_REF,
    P7_HOLD_FULL_BACKEND_SUITE_REF,
    P7_HOLD_REAL_DEVICE_MODAL_REF,
    P7_RETURN_REAL_DEVICE_HOLD_REF,
)
from emlis_ai_p7_r47_local_review_packet_policy import (
    P7_R47_BODY_FREE_DISPOSAL_RECEIPT_SCHEMA_VERSION,
    P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
    P7_R47_DISPOSAL_STATUSES,
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
    P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
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
P7_R48_P5_REVIEW_POLICY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.p5_human_blind_qa_actual_review_policy.v1"
)
P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION: Final = "cocolon.emlis.p7_r48.p5_case_matrix.bodyfree.v1"
P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r48.p5_reviewer_packet.local_only.v1"
)
P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION: Final = "cocolon.emlis.p7_r48.p5_rating_row.bodyfree.v1"
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


__all__ = [
    "P7_R48_CURRENT_SOURCE_R47_HANDOFF_HOLD_REFREEZE_SCHEMA_VERSION",
    "P7_R48_SCOPE_SCHEMA_PACKET_KIND_FREEZE_SCHEMA_VERSION",
    "P7_R48_R0_R1_SCOPE_FREEZE_SCHEMA_VERSION",
    "P7_R48_LOCAL_STORAGE_ROOT_POLICY_SCHEMA_VERSION",
    "P7_R48_R2_R3_LOCAL_STORAGE_CASE_MATRIX_FREEZE_SCHEMA_VERSION",
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
    "P7_R48_IMPLEMENTED_STEPS",
    "P7_R48_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R48_R2_R3_IMPLEMENTED_STEPS",
    "P7_R48_R2_R3_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R48_RECEIVED_LOCAL_SNAPSHOT_REFS",
    "P7_R48_REQUIRED_UNRESOLVED_HOLD_REFS",
    "P7_R48_REVIEW_PROMPT_VERSION",
    "P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION",
    "assert_p7_r48_current_source_r47_handoff_hold_refreeze_contract",
    "assert_p7_r48_local_storage_root_policy_contract",
    "assert_p7_r48_p5_first_formal_review_case_matrix_contract",
    "assert_p7_r48_r2_r3_local_storage_case_matrix_freeze_contract",
    "assert_p7_r48_scope_schema_packet_kind_freeze_contract",
    "assert_p7_r48_r0_r1_scope_freeze_contract",
    "build_p7_r48_current_source_r47_handoff_hold_refreeze",
    "build_p7_r48_local_storage_root_policy",
    "build_p7_r48_p5_first_formal_review_case_matrix",
    "build_p7_r48_r2_r3_local_storage_case_matrix_freeze",
    "build_p7_r48_scope_schema_packet_kind_freeze",
    "build_p7_r48_r0_r1_scope_freeze",
]
