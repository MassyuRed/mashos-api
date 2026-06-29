# -*- coding: utf-8 -*-
"""P7-R54 current snapshot local review run CLR16-CLR17 helpers.

CLR16 materializes only the body-free pause / abort / expiration protocol for
this 2026-06-27 current snapshot run.  It decides whether the local body-full
materials must be purged before any handoff can happen.  Paused local-only
review stays no-handoff.  Aborted, expired, incomplete, and consistency-guarded
runs require purge before any later summary or re-intake material.

CLR17 accepts only a body-free disposal receipt after an external local purge.
It never deletes files itself and never exports packet content, local paths,
hashes, reviewer notes, raw input, returned Emlis body, history surface, or
question text.  API, DB, RN, runtime, public response keys, P8 implementation,
P5 finalization, P6/P8 start, P7 completion, and release remain untouched.
"""

from __future__ import annotations

import re
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
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr10_clr11_20260627 as clr11
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr14_clr15_20260627 as clr15


P7_R54_CLR16_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr16_pause_abort_expiration_protocol.bodyfree.v1"
)
P7_R54_CLR17_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr17_purge_disposal_receipt.bodyfree.v1"
)
P7_R54_CLR16_SCHEMA_VERSION: Final = P7_R54_CLR16_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION
P7_R54_CLR17_SCHEMA_VERSION: Final = P7_R54_CLR17_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION

P7_R54_CLR_STEP: Final = clr03.P7_R54_CLR_STEP
P7_R54_CLR_SCOPE: Final = clr03.P7_R54_CLR_SCOPE
P7_R54_CLR_POLICY_KIND: Final = clr03.P7_R54_CLR_POLICY_KIND
P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID: Final = clr03.P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID
P7_R54_CLR16_STEP_REF: Final = clr03.P7_R54_CLR16_STEP_REF
P7_R54_CLR17_STEP_REF: Final = clr03.P7_R54_CLR17_STEP_REF
P7_R54_CLR18_STEP_REF: Final = clr03.P7_R54_CLR18_STEP_REF

P7_R54_CLR16_PROTOCOL_READY_STATUS_REF: Final = "READY_FOR_PURGE_DISPOSAL_RECEIPT"
P7_R54_CLR16_PROTOCOL_PAUSED_STATUS_REF: Final = "PAUSED_NO_HANDOFF_LOCAL_ONLY"
P7_R54_CLR16_PROTOCOL_ABORTED_STATUS_REF: Final = "ABORTED_PURGE_REQUIRED"
P7_R54_CLR16_PROTOCOL_EXPIRED_STATUS_REF: Final = "EXPIRED_PURGE_REQUIRED"
P7_R54_CLR16_PROTOCOL_RATING_INCOMPLETE_STATUS_REF: Final = "RATING_INCOMPLETE_PURGE_REQUIRED"
P7_R54_CLR16_PROTOCOL_BLOCKED_STATUS_REF: Final = "BLOCKED_BY_CONSISTENCY_GUARD"
P7_R54_CLR16_PROTOCOL_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_CLR16_PROTOCOL_READY_STATUS_REF,
    P7_R54_CLR16_PROTOCOL_PAUSED_STATUS_REF,
    P7_R54_CLR16_PROTOCOL_ABORTED_STATUS_REF,
    P7_R54_CLR16_PROTOCOL_EXPIRED_STATUS_REF,
    P7_R54_CLR16_PROTOCOL_RATING_INCOMPLETE_STATUS_REF,
    P7_R54_CLR16_PROTOCOL_BLOCKED_STATUS_REF,
)
P7_R54_CLR16_PROTOCOL_REF: Final = "r54_clr16_pause_abort_expiration_protocol_bodyfree_20260627"
P7_R54_CLR16_PROTOCOL_POLICY_REF: Final = "pause_abort_expiration_requires_purge_before_handoff_20260627"
P7_R54_CLR16_READY_REASON_REF: Final = "r54_clr16_ready_for_purge_disposal_receipt_bodyfree"
P7_R54_CLR16_PAUSED_REASON_REF: Final = "r54_clr16_paused_no_handoff_local_only_bodyfree"
P7_R54_CLR16_ABORTED_REASON_REF: Final = "r54_clr16_aborted_purge_required_bodyfree"
P7_R54_CLR16_EXPIRED_REASON_REF: Final = "r54_clr16_expired_purge_required_bodyfree"
P7_R54_CLR16_RATING_INCOMPLETE_REASON_REF: Final = "r54_clr16_rating_or_question_incomplete_purge_required_bodyfree"
P7_R54_CLR16_BLOCKED_REASON_REF: Final = "r54_clr16_blocked_by_rating_question_consistency_guard_bodyfree"
P7_R54_CLR16_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "R54-CLR-16_blocked_until_rating_question_consistency_guard_repair"
P7_R54_CLR16_PAUSED_NEXT_REQUIRED_STEP_REF: Final = "R54-CLR-16_paused_resume_or_abort_before_purge_disposal_receipt"

P7_R54_CLR16_REVIEW_OPERATION_STATUS_REFS: Final[tuple[str, ...]] = (
    clr11.P7_R54_CLR10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF,
    clr11.P7_R54_CLR10_REVIEW_PAUSED_STATUS_REF,
    clr11.P7_R54_CLR10_REVIEW_ABORTED_STATUS_REF,
    clr11.P7_R54_CLR10_REVIEW_EXPIRED_STATUS_REF,
    r54op.P7_R54_OP10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF,
    r54op.P7_R54_OP10_REVIEW_PAUSED_STATUS_REF,
    r54op.P7_R54_OP10_REVIEW_ABORTED_STATUS_REF,
    r54op.P7_R54_OP10_REVIEW_EXPIRED_STATUS_REF,
    "REVIEW_RATING_INCOMPLETE",
    "rating_incomplete_purge_required",
)
P7_R54_CLR16_REQUIRED_LOCAL_DELETE_TARGET_REFS: Final[tuple[str, ...]] = (
    "body_full_packet",
    "reviewer_notes",
    "temporary_form",
)
P7_R54_CLR16_PURGE_TRIGGER_REFS: Final[tuple[str, ...]] = (
    "rating_rows_finalized",
    "blocker_rows_finalized",
    "question_observation_rows_finalized",
    "review_session_cancelled",
    "review_session_aborted",
    "retention_deadline_reached",
)
P7_R54_CLR16_P5_DECISION_DIRECTION_REFS: Final[tuple[str, ...]] = (
    "continue_after_purge_disposal_receipt",
    "no_p5_decision_materialized_here",
    "pause_no_handoff_local_only",
    "r54_operation_inconclusive_required_later",
    "p5_or_emlis_repair_required_later_not_p8_material",
    "p5_inconclusive_due_to_consistency_guard_not_ready",
)

P7_R54_CLR17_DISPOSAL_VERIFIED_STATUS_REF: Final = "DISPOSAL_VERIFIED"
P7_R54_CLR17_DISPOSAL_BLOCKED_STATUS_REF: Final = "R54_OPERATION_BLOCKED_DISPOSAL"
P7_R54_CLR17_ALLOWED_DISPOSAL_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_CLR17_DISPOSAL_VERIFIED_STATUS_REF,
    P7_R54_CLR17_DISPOSAL_BLOCKED_STATUS_REF,
)
P7_R54_CLR17_DISPOSAL_RECEIPT_REF: Final = "r54_clr17_bodyfree_purge_disposal_receipt_verified_20260627"
P7_R54_CLR17_DISPOSAL_RECEIPT_POLICY_REF: Final = (
    "bodyfree_receipt_only_after_external_local_purge_no_body_hash_no_path_20260627"
)
P7_R54_CLR17_READY_REASON_REF: Final = "r54_clr17_purge_disposal_receipt_verified_bodyfree"
P7_R54_CLR17_BLOCKED_REASON_REF: Final = "r54_clr17_purge_disposal_receipt_blocked_bodyfree"
P7_R54_CLR17_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "R54-CLR-17_blocked_until_purge_disposal_receipt_repair_before_bodyfree_summary"
P7_R54_CLR17_REMOVAL_TARGET_REFS: Final[tuple[str, ...]] = P7_R54_CLR16_REQUIRED_LOCAL_DELETE_TARGET_REFS
P7_R54_CLR17_RECEIPT_ALLOWED_FIELD_REFS: Final[tuple[str, ...]] = (
    "review_session_id",
    "disposal_operation_ref",
    "body_full_packet_removed",
    "reviewer_notes_removed",
    "temporary_form_removed",
    "local_packet_exported",
    "content_hash_of_body_stored",
    "disposal_verified",
    "disposal_verified_at_ref",
    "execution_blocker_ids",
)

P7_R54_CLR16_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*clr15.P7_R54_CLR15_IMPLEMENTED_STEPS, P7_R54_CLR16_STEP_REF)
P7_R54_CLR16_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = clr03.P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR01[15:]
P7_R54_CLR17_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_CLR16_IMPLEMENTED_STEPS, P7_R54_CLR17_STEP_REF)
P7_R54_CLR17_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = clr03.P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR01[16:]

P7_R54_CLR16_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[frozenset[str]] = frozenset(
    {
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
    }
)
P7_R54_CLR17_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[frozenset[str]] = frozenset(
    {
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "disposal_verified",
    }
)

P7_R54_CLR_PROHIBITED_PAYLOAD_OR_QUESTION_FIELD_REFS: Final[frozenset[str]] = clr15.P7_R54_CLR_PROHIBITED_PAYLOAD_OR_QUESTION_FIELD_REFS

P7_R54_CLR16_PAUSE_ABORT_EXPIRATION_PROTOCOL_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *clr03.P7_R54_CLR_COMMON_REQUIRED_FIELD_REFS,
    "clr15_schema_version",
    "clr15_material_ref",
    "clr15_next_required_step",
    "clr15_rating_question_consistency_guard_status",
    "clr15_ready_for_pause_abort_expiration_protocol",
    "clr15_consistency_issue_count",
    "clr15_consistency_guard_passed",
    "clr15_p5_repair_required_not_reclassified_as_p8_material",
    "existing_op16_helper_ref",
    "existing_op16_schema_version",
    "existing_op16_operation_current_refs",
    "existing_op16_current_refs_are_historical_here",
    "existing_op16_reused_as_actual_pause_abort_basis",
    "existing_op16_reused_as_actual_protocol_basis",
    "existing_op16_structural_contract_reused",
    "existing_ev14_schema_version",
    "existing_ev14_current_refs",
    "existing_ev14_current_refs_are_historical_here",
    "existing_ev14_reused_as_actual_pause_abort_basis",
    "existing_ev14_reused_as_actual_protocol_basis",
    "existing_ev14_structural_contract_reused",
    *clr03.P7_R54_CLR_CURRENT_REF_REQUIRED_FIELD_REFS,
    "required_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "consistency_issue_count",
    "pause_abort_expiration_protocol_status",
    "pause_abort_expiration_protocol_ref",
    "pause_abort_expiration_protocol_policy_ref",
    "pause_abort_expiration_protocol_reason_refs",
    "review_operation_status_ref",
    "review_operation_status_refs",
    "review_operation_status_allowed",
    "purge_trigger_refs",
    "purge_trigger_ref_count",
    "review_session_cancelled_is_purge_trigger",
    "review_session_aborted_is_purge_trigger",
    "retention_deadline_reached_is_purge_trigger",
    "required_local_delete_target_refs",
    "required_local_delete_target_ref_count",
    "body_full_packet_retention_hours",
    "reviewer_notes_retention_after_rating_hours",
    "body_full_material_must_not_remain_after_cancel_or_deadline",
    "reviewer_notes_must_not_remain_after_cancel_or_deadline",
    "temporary_form_must_not_remain_after_cancel_or_deadline",
    "purge_before_handoff_required",
    "handoff_allowed_before_purge",
    "r52_reintake_handoff_allowed_before_purge",
    "review_paused_without_handoff",
    "review_aborted_or_expired",
    "review_rating_or_question_incomplete",
    "blocked_by_consistency_guard_requires_purge",
    "p5_decision_direction_ref",
    "p5_decision_direction_refs",
    "p5_decision_materialized_here",
    "p5_inconclusive_direction_only_not_decision_materialized",
    "ready_for_purge_disposal_receipt",
    "purge_disposal_receipt_allowed_next",
    "disposal_receipt_allowed_next",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_review_evidence_complete",
    "disposal_verified",
    "actual_disposal_receipt_materialized_here",
    "human_review_completion_claim_blocked_here",
    "actual_human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "upstream_consistency_issue_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *clr03.P7_R54_CLR_NO_TOUCH_BODYFREE_REQUIRED_FIELD_REFS,
    "raw_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    *clr03.P7_R54_CLR_FALSE_FLAG_REFS,
)

P7_R54_CLR17_PURGE_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *clr03.P7_R54_CLR_COMMON_REQUIRED_FIELD_REFS,
    "clr16_schema_version",
    "clr16_material_ref",
    "clr16_next_required_step",
    "clr16_pause_abort_expiration_protocol_status",
    "clr16_purge_disposal_receipt_allowed_next",
    "clr16_ready_for_purge_disposal_receipt",
    "clr16_open_execution_blocker_ids",
    "existing_op17_helper_ref",
    "existing_op17_schema_version",
    "existing_op17_operation_current_refs",
    "existing_op17_current_refs_are_historical_here",
    "existing_op17_reused_as_actual_disposal_basis",
    "existing_op17_reused_as_actual_disposal_receipt_basis",
    "existing_op17_structural_contract_reused",
    "existing_ev15_schema_version",
    "existing_ev15_current_refs",
    "existing_ev15_current_refs_are_historical_here",
    "existing_ev15_reused_as_actual_disposal_basis",
    "existing_ev15_reused_as_actual_disposal_receipt_basis",
    "existing_ev15_structural_contract_reused",
    *clr03.P7_R54_CLR_CURRENT_REF_REQUIRED_FIELD_REFS,
    "required_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "purge_disposal_receipt_status",
    "purge_disposal_receipt_ref",
    "purge_disposal_receipt_policy_ref",
    "purge_disposal_receipt_reason_refs",
    "received_receipt_allowed_field_refs",
    "received_receipt_field_refs",
    "received_receipt_has_only_allowed_fields",
    "disposal_operation_ref",
    "disposal_verified_at_ref",
    "removal_target_refs",
    "removal_target_ref_count",
    "body_full_packet_removed",
    "body_removed",
    "reviewer_notes_removed",
    "temporary_form_removed",
    "all_required_local_targets_removed",
    "local_packet_exported",
    "content_hash_of_body_stored",
    "body_full_packet_zip_inclusion_allowed",
    "reviewer_notes_export_allowed",
    "body_full_packet_export_allowed",
    "disposal_verified",
    "actual_disposal_receipt_materialized_here",
    "actual_disposal_run_here",
    "disposal_failure_decision_ref",
    "body_free_post_review_summary_allowed_next",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_review_evidence_complete",
    "human_review_completion_claim_blocked_here",
    "actual_human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "upstream_execution_blocker_ids",
    "disposal_execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *clr03.P7_R54_CLR_NO_TOUCH_BODYFREE_REQUIRED_FIELD_REFS,
    "raw_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    *clr03.P7_R54_CLR_FALSE_FLAG_REFS,
)

_SAFE_BODYFREE_REF_RE = re.compile(r"^[A-Za-z0-9_.:-]+$")
_HASH_LIKE_REF_RE = re.compile(r"^[0-9a-fA-F]{32,}$")


def _safe_receipt_ref(value: Any, *, default: str = "", max_length: int = 220) -> str:
    text = clean_identifier(value, default=default, max_length=max_length)
    if not text:
        return ""
    if not _SAFE_BODYFREE_REF_RE.fullmatch(text):
        return ""
    if _HASH_LIKE_REF_RE.fullmatch(text):
        return ""
    return text


def _false_flags_except(*allowed_true_refs: str) -> dict[str, bool]:
    allowed = set(allowed_true_refs)
    return {key: False for key in clr03.P7_R54_CLR_FALSE_FLAG_REFS if key not in allowed}


def _safe_review_session_id(value: Any) -> str:
    return clean_identifier(value, default=P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID, max_length=180)


def _assert_required_fields(data: Mapping[str, Any], *, required: tuple[str, ...], source: str) -> None:
    required_set = set(required)
    missing = [field for field in required if field not in data]
    extra = [field for field in data if field not in required_set]
    if missing or extra:
        raise ValueError(f"{source} field mismatch missing={missing[:8]} extra={extra[:8]}")


def _assert_common_base(
    data: Mapping[str, Any], *, schema_version: str, policy_section: str, source: str, allowed_true_false_flags: frozenset[str]
) -> None:
    clr15._assert_common_base(  # type: ignore[attr-defined]
        data,
        schema_version=schema_version,
        policy_section=policy_section,
        source=source,
        allowed_true_false_flags=allowed_true_false_flags,
    )
    clr15._assert_current_refs(data, source=source)  # type: ignore[attr-defined]
    if data.get("raw_body_included") is not False:
        raise ValueError(f"{source} must keep raw_body_included=False")
    if data.get("question_text_included") is not False:
        raise ValueError(f"{source} must keep question_text_included=False")
    if data.get("draft_question_text_included") is not False:
        raise ValueError(f"{source} must keep draft_question_text_included=False")
    if data.get("local_path_included") is not False:
        raise ValueError(f"{source} must keep local_path_included=False")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)


def _receipt_contains_forbidden_payload(value: Any) -> bool:
    return clr15._contains_forbidden_key(value)  # type: ignore[attr-defined]


def _status_decision(
    *,
    clr15_ready: bool,
    consistency_guard_blocked_with_rows: bool,
    review_status: str,
    rating_row_count: int,
    question_observation_row_count: int,
) -> tuple[str, str, str, bool, bool, bool, bool, str]:
    if consistency_guard_blocked_with_rows:
        return (
            P7_R54_CLR16_PROTOCOL_BLOCKED_STATUS_REF,
            P7_R54_CLR16_BLOCKED_REASON_REF,
            "rating_question_consistency_guard_blocked_purge_required",
            True,
            False,
            False,
            False,
            "p5_or_emlis_repair_required_later_not_p8_material",
        )
    if not clr15_ready:
        return (
            P7_R54_CLR16_PROTOCOL_BLOCKED_STATUS_REF,
            P7_R54_CLR16_BLOCKED_REASON_REF,
            "clr15_consistency_guard_not_ready_for_pause_abort_expiration_protocol",
            False,
            False,
            False,
            False,
            "p5_inconclusive_due_to_consistency_guard_not_ready",
        )
    if review_status in (
        clr11.P7_R54_CLR10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF,
        r54op.P7_R54_OP10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF,
    ):
        if rating_row_count != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT or question_observation_row_count != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            return (
                P7_R54_CLR16_PROTOCOL_RATING_INCOMPLETE_STATUS_REF,
                P7_R54_CLR16_RATING_INCOMPLETE_REASON_REF,
                "rating_or_question_row_count_incomplete_before_disposal",
                True,
                False,
                False,
                True,
                "r54_operation_inconclusive_required_later",
            )
        return (
            P7_R54_CLR16_PROTOCOL_READY_STATUS_REF,
            P7_R54_CLR16_READY_REASON_REF,
            "",
            True,
            False,
            False,
            False,
            "continue_after_purge_disposal_receipt",
        )
    if review_status in (
        clr11.P7_R54_CLR10_REVIEW_PAUSED_STATUS_REF,
        r54op.P7_R54_OP10_REVIEW_PAUSED_STATUS_REF,
    ):
        return (
            P7_R54_CLR16_PROTOCOL_PAUSED_STATUS_REF,
            P7_R54_CLR16_PAUSED_REASON_REF,
            "",
            False,
            True,
            False,
            False,
            "pause_no_handoff_local_only",
        )
    if review_status in (
        clr11.P7_R54_CLR10_REVIEW_ABORTED_STATUS_REF,
        r54op.P7_R54_OP10_REVIEW_ABORTED_STATUS_REF,
    ):
        return (
            P7_R54_CLR16_PROTOCOL_ABORTED_STATUS_REF,
            P7_R54_CLR16_ABORTED_REASON_REF,
            "",
            True,
            False,
            True,
            False,
            "r54_operation_inconclusive_required_later",
        )
    if review_status in (
        clr11.P7_R54_CLR10_REVIEW_EXPIRED_STATUS_REF,
        r54op.P7_R54_OP10_REVIEW_EXPIRED_STATUS_REF,
    ):
        return (
            P7_R54_CLR16_PROTOCOL_EXPIRED_STATUS_REF,
            P7_R54_CLR16_EXPIRED_REASON_REF,
            "",
            True,
            False,
            True,
            False,
            "r54_operation_inconclusive_required_later",
        )
    if review_status in ("REVIEW_RATING_INCOMPLETE", "rating_incomplete_purge_required"):
        return (
            P7_R54_CLR16_PROTOCOL_RATING_INCOMPLETE_STATUS_REF,
            P7_R54_CLR16_RATING_INCOMPLETE_REASON_REF,
            "rating_incomplete_purge_required",
            True,
            False,
            False,
            True,
            "r54_operation_inconclusive_required_later",
        )
    return (
        P7_R54_CLR16_PROTOCOL_BLOCKED_STATUS_REF,
        P7_R54_CLR16_BLOCKED_REASON_REF,
        "review_operation_status_not_allowed_for_pause_abort_expiration_protocol",
        False,
        False,
        False,
        False,
        "p5_inconclusive_due_to_consistency_guard_not_ready",
    )


def build_p7_r54_clr16_pause_abort_expiration_protocol(
    *,
    rating_question_consistency_guard: Mapping[str, Any] | None = None,
    review_operation_status_ref: Any = clr11.P7_R54_CLR10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF,
    material_id: Any = "p7_r54_clr16_pause_abort_expiration_protocol",
) -> dict[str, Any]:
    """Build the body-free CLR16 pause / abort / expiration protocol."""

    clr15_material = (
        safe_mapping(rating_question_consistency_guard)
        if rating_question_consistency_guard is not None
        else clr15.build_p7_r54_clr15_rating_question_consistency_guard()
    )
    clr15.assert_p7_r54_clr15_rating_question_consistency_guard_contract(clr15_material)
    review_status = clean_identifier(review_operation_status_ref, default="", max_length=180)
    review_status_allowed = review_status in P7_R54_CLR16_REVIEW_OPERATION_STATUS_REFS
    rating_count_from_clr15 = int(clr15_material.get("rating_row_count") or 0)
    question_count_from_clr15 = int(clr15_material.get("question_observation_row_count") or 0)
    consistency_issue_count = int(clr15_material.get("consistency_issue_count") or 0)
    clr15_ready = bool(
        clr15_material.get("rating_question_consistency_guard_status") == clr15.P7_R54_CLR15_CONSISTENCY_GUARD_READY_STATUS_REF
        and clr15_material.get("ready_for_pause_abort_expiration_protocol") is True
        and clr15_material.get("next_required_step") == P7_R54_CLR16_STEP_REF
        and not clr15_material.get("open_execution_blocker_ids")
    )
    consistency_guard_blocked_with_rows = bool(
        not clr15_ready
        and clr15_material.get("rating_question_consistency_guard_status") == clr15.P7_R54_CLR15_CONSISTENCY_GUARD_BLOCKED_STATUS_REF
        and rating_count_from_clr15 == clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and question_count_from_clr15 == clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and consistency_issue_count > 0
    )
    row_counts_available = bool(clr15_ready or consistency_guard_blocked_with_rows)
    rating_row_count = rating_count_from_clr15 if row_counts_available else 0
    question_observation_row_count = question_count_from_clr15 if row_counts_available else 0
    (
        status,
        reason_ref,
        blocker_ref,
        purge_allowed,
        paused,
        abort_or_expired,
        rating_or_question_incomplete,
        p5_decision_direction_ref,
    ) = _status_decision(
        clr15_ready=bool(clr15_ready and review_status_allowed),
        consistency_guard_blocked_with_rows=consistency_guard_blocked_with_rows,
        review_status=review_status,
        rating_row_count=rating_row_count,
        question_observation_row_count=question_observation_row_count,
    )
    upstream_issue_ids = dedupe_identifiers(
        [row.get("issue_id") for row in (clr15_material.get("rating_question_consistency_issue_rows") or [])],
        limit=100,
        max_length=180,
    )
    blockers = dedupe_identifiers(
        [blocker_ref, *(upstream_issue_ids if consistency_guard_blocked_with_rows else [])],
        limit=100,
        max_length=180,
    )
    ready_for_disposal = bool(purge_allowed)
    material: dict[str, Any] = {
        "schema_version": P7_R54_CLR16_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_CLR_STEP,
        "scope": P7_R54_CLR_SCOPE,
        "policy_kind": P7_R54_CLR_POLICY_KIND,
        "policy_section": P7_R54_CLR16_STEP_REF,
        "operation_step_ref": P7_R54_CLR16_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_clr16_pause_abort_expiration_protocol", max_length=220),
        "review_session_id": _safe_review_session_id(clr15_material.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "clr15_schema_version": clr15.P7_R54_CLR15_SCHEMA_VERSION,
        "clr15_material_ref": clean_identifier(clr15_material.get("material_id"), default="p7_r54_clr15_rating_question_consistency_guard", max_length=220),
        "clr15_next_required_step": clean_identifier(clr15_material.get("next_required_step"), default=clr15.P7_R54_CLR15_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220),
        "clr15_rating_question_consistency_guard_status": clean_identifier(clr15_material.get("rating_question_consistency_guard_status"), default=clr15.P7_R54_CLR15_CONSISTENCY_GUARD_BLOCKED_STATUS_REF, max_length=180),
        "clr15_ready_for_pause_abort_expiration_protocol": clr15_ready,
        "clr15_consistency_issue_count": consistency_issue_count,
        "clr15_consistency_guard_passed": bool(clr15_material.get("rating_question_consistency_guard_passed") is True),
        "clr15_p5_repair_required_not_reclassified_as_p8_material": bool(clr15_material.get("p5_repair_required_not_reclassified_as_p8_material") is True),
        "existing_op16_helper_ref": "build_p7_r54_op16_pause_abort_expiration_protocol",
        "existing_op16_schema_version": r54op.P7_R54_OPERATION_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION,
        "existing_op16_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op16_current_refs_are_historical_here": True,
        "existing_op16_reused_as_actual_pause_abort_basis": False,
        "existing_op16_reused_as_actual_protocol_basis": False,
        "existing_op16_structural_contract_reused": True,
        "existing_ev14_schema_version": r54ev.P7_R54_EV_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION,
        "existing_ev14_current_refs": dict(r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "existing_ev14_current_refs_are_historical_here": True,
        "existing_ev14_reused_as_actual_pause_abort_basis": False,
        "existing_ev14_reused_as_actual_protocol_basis": False,
        "existing_ev14_structural_contract_reused": True,
        **clr15._current_ref_fields(),  # type: ignore[attr-defined]
        "required_case_count": clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "rating_row_count": rating_row_count,
        "question_observation_row_count": question_observation_row_count,
        "consistency_issue_count": consistency_issue_count,
        "pause_abort_expiration_protocol_status": status,
        "pause_abort_expiration_protocol_ref": P7_R54_CLR16_PROTOCOL_REF if status != P7_R54_CLR16_PROTOCOL_BLOCKED_STATUS_REF or ready_for_disposal else "pause_abort_expiration_protocol_not_ready_bodyfree_20260627",
        "pause_abort_expiration_protocol_policy_ref": P7_R54_CLR16_PROTOCOL_POLICY_REF,
        "pause_abort_expiration_protocol_reason_refs": dedupe_identifiers([reason_ref, *blockers], limit=100, max_length=180),
        "review_operation_status_ref": review_status,
        "review_operation_status_refs": list(P7_R54_CLR16_REVIEW_OPERATION_STATUS_REFS),
        "review_operation_status_allowed": review_status_allowed,
        "purge_trigger_refs": list(P7_R54_CLR16_PURGE_TRIGGER_REFS),
        "purge_trigger_ref_count": len(P7_R54_CLR16_PURGE_TRIGGER_REFS),
        "review_session_cancelled_is_purge_trigger": "review_session_cancelled" in P7_R54_CLR16_PURGE_TRIGGER_REFS,
        "review_session_aborted_is_purge_trigger": "review_session_aborted" in P7_R54_CLR16_PURGE_TRIGGER_REFS,
        "retention_deadline_reached_is_purge_trigger": "retention_deadline_reached" in P7_R54_CLR16_PURGE_TRIGGER_REFS,
        "required_local_delete_target_refs": list(P7_R54_CLR16_REQUIRED_LOCAL_DELETE_TARGET_REFS),
        "required_local_delete_target_ref_count": len(P7_R54_CLR16_REQUIRED_LOCAL_DELETE_TARGET_REFS),
        "body_full_packet_retention_hours": r54op.P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
        "reviewer_notes_retention_after_rating_hours": r54op.P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
        "body_full_material_must_not_remain_after_cancel_or_deadline": True,
        "reviewer_notes_must_not_remain_after_cancel_or_deadline": True,
        "temporary_form_must_not_remain_after_cancel_or_deadline": True,
        "purge_before_handoff_required": True,
        "handoff_allowed_before_purge": False,
        "r52_reintake_handoff_allowed_before_purge": False,
        "review_paused_without_handoff": paused,
        "review_aborted_or_expired": abort_or_expired,
        "review_rating_or_question_incomplete": rating_or_question_incomplete,
        "blocked_by_consistency_guard_requires_purge": consistency_guard_blocked_with_rows,
        "p5_decision_direction_ref": p5_decision_direction_ref,
        "p5_decision_direction_refs": list(P7_R54_CLR16_P5_DECISION_DIRECTION_REFS),
        "p5_decision_materialized_here": False,
        "p5_inconclusive_direction_only_not_decision_materialized": p5_decision_direction_ref != "continue_after_purge_disposal_receipt",
        "ready_for_purge_disposal_receipt": ready_for_disposal,
        "purge_disposal_receipt_allowed_next": ready_for_disposal,
        "disposal_receipt_allowed_next": ready_for_disposal,
        "actual_rating_rows_materialized_here": bool(clr15_material.get("actual_rating_rows_materialized_here") is True) if row_counts_available else False,
        "actual_blocker_rows_materialized_here": bool(clr15_material.get("actual_blocker_rows_materialized_here") is True) if row_counts_available else False,
        "actual_question_need_observation_rows_materialized_here": bool(clr15_material.get("actual_question_need_observation_rows_materialized_here") is True) if row_counts_available else False,
        "actual_review_evidence_complete": False,
        "disposal_verified": False,
        "actual_disposal_receipt_materialized_here": False,
        "human_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "upstream_consistency_issue_ids": upstream_issue_ids,
        "implemented_steps": list(P7_R54_CLR16_IMPLEMENTED_STEPS if (ready_for_disposal or paused) else (clr15_material.get("implemented_steps") or [])),
        "not_yet_implemented_steps": list(P7_R54_CLR16_NOT_YET_IMPLEMENTED_STEPS if (ready_for_disposal or paused) else (clr15_material.get("not_yet_implemented_steps") or [])),
        "next_required_step": P7_R54_CLR17_STEP_REF if ready_for_disposal else (P7_R54_CLR16_PAUSED_NEXT_REQUIRED_STEP_REF if paused else P7_R54_CLR16_BLOCKED_NEXT_REQUIRED_STEP_REF),
        "public_contract": public_contract_flags(),
        "r54_clr_no_touch_contract": clr15._no_touch_contract(),  # type: ignore[attr-defined]
        "body_free_markers": clr15._body_free_markers(),  # type: ignore[attr-defined]
        "body_free": True,
        "raw_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags_except("actual_rating_rows_materialized_here", "actual_question_need_observation_rows_materialized_here"),
    }
    material["actual_rating_rows_materialized_here"] = bool(clr15_material.get("actual_rating_rows_materialized_here") is True) if row_counts_available else False
    material["actual_blocker_rows_materialized_here"] = bool(clr15_material.get("actual_blocker_rows_materialized_here") is True) if row_counts_available else False
    material["actual_question_need_observation_rows_materialized_here"] = bool(clr15_material.get("actual_question_need_observation_rows_materialized_here") is True) if row_counts_available else False
    assert_p7_r54_clr16_pause_abort_expiration_protocol_contract(material)
    return material


def assert_p7_r54_clr16_pause_abort_expiration_protocol_contract(data: Mapping[str, Any]) -> bool:
    material = safe_mapping(data)
    _assert_required_fields(material, required=P7_R54_CLR16_PAUSE_ABORT_EXPIRATION_PROTOCOL_REQUIRED_FIELD_REFS, source="P7-R54-CLR16")
    _assert_common_base(
        material,
        schema_version=P7_R54_CLR16_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION,
        policy_section=P7_R54_CLR16_STEP_REF,
        source="P7-R54-CLR16",
        allowed_true_false_flags=P7_R54_CLR16_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    if safe_mapping(material.get("existing_op16_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("P7-R54-CLR16 existing OP16 refs changed")
    if safe_mapping(material.get("existing_ev14_current_refs")) != r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("P7-R54-CLR16 existing EV14 refs changed")
    for key in (
        "existing_op16_current_refs_are_historical_here",
        "existing_op16_structural_contract_reused",
        "existing_ev14_current_refs_are_historical_here",
        "existing_ev14_structural_contract_reused",
        "body_full_material_must_not_remain_after_cancel_or_deadline",
        "reviewer_notes_must_not_remain_after_cancel_or_deadline",
        "temporary_form_must_not_remain_after_cancel_or_deadline",
        "purge_before_handoff_required",
        "human_review_completion_claim_blocked_here",
        "actual_human_review_completion_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if material.get(key) is not True:
            raise ValueError(f"P7-R54-CLR16 must keep {key}=True")
    for key in (
        "existing_op16_reused_as_actual_pause_abort_basis",
        "existing_op16_reused_as_actual_protocol_basis",
        "existing_ev14_reused_as_actual_pause_abort_basis",
        "existing_ev14_reused_as_actual_protocol_basis",
        "handoff_allowed_before_purge",
        "r52_reintake_handoff_allowed_before_purge",
        "p5_decision_materialized_here",
        "actual_review_evidence_complete",
        "disposal_verified",
        "actual_disposal_receipt_materialized_here",
    ):
        if material.get(key) is not False:
            raise ValueError(f"P7-R54-CLR16 must keep {key}=False")
    if material.get("required_case_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-CLR16 required case count changed")
    if material.get("pause_abort_expiration_protocol_status") not in P7_R54_CLR16_PROTOCOL_STATUS_REFS:
        raise ValueError("P7-R54-CLR16 protocol status changed")
    if tuple(material.get("review_operation_status_refs") or ()) != P7_R54_CLR16_REVIEW_OPERATION_STATUS_REFS:
        raise ValueError("P7-R54-CLR16 review operation status refs changed")
    if tuple(material.get("purge_trigger_refs") or ()) != P7_R54_CLR16_PURGE_TRIGGER_REFS:
        raise ValueError("P7-R54-CLR16 purge trigger refs changed")
    if tuple(material.get("required_local_delete_target_refs") or ()) != P7_R54_CLR16_REQUIRED_LOCAL_DELETE_TARGET_REFS:
        raise ValueError("P7-R54-CLR16 required local delete target refs changed")
    if tuple(material.get("p5_decision_direction_refs") or ()) != P7_R54_CLR16_P5_DECISION_DIRECTION_REFS:
        raise ValueError("P7-R54-CLR16 P5 direction refs changed")
    blockers = dedupe_identifiers(material.get("execution_blocker_ids") or [], limit=100, max_length=180)
    if material.get("open_execution_blocker_ids") != blockers:
        raise ValueError("P7-R54-CLR16 open blockers mismatch")
    status = material.get("pause_abort_expiration_protocol_status")
    if status == P7_R54_CLR16_PROTOCOL_READY_STATUS_REF:
        if material.get("clr15_ready_for_pause_abort_expiration_protocol") is not True:
            raise ValueError("P7-R54-CLR16 ready protocol requires ready CLR15")
        if material.get("rating_row_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT or material.get("question_observation_row_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-CLR16 ready protocol requires 24 rating/question rows")
        if blockers:
            raise ValueError("P7-R54-CLR16 ready protocol must not carry blockers")
        if material.get("ready_for_purge_disposal_receipt") is not True or material.get("next_required_step") != P7_R54_CLR17_STEP_REF:
            raise ValueError("P7-R54-CLR16 ready protocol must point to CLR17")
        if tuple(material.get("implemented_steps") or ()) != P7_R54_CLR16_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR16 ready implemented steps changed")
        if tuple(material.get("not_yet_implemented_steps") or ()) != P7_R54_CLR16_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR16 ready not-yet steps changed")
    elif status == P7_R54_CLR16_PROTOCOL_PAUSED_STATUS_REF:
        if material.get("review_paused_without_handoff") is not True:
            raise ValueError("P7-R54-CLR16 paused must stay no-handoff")
        if material.get("ready_for_purge_disposal_receipt") is not False or material.get("next_required_step") != P7_R54_CLR16_PAUSED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-CLR16 paused next step changed")
        if tuple(material.get("implemented_steps") or ()) != P7_R54_CLR16_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR16 paused implemented steps changed")
    elif status in (
        P7_R54_CLR16_PROTOCOL_ABORTED_STATUS_REF,
        P7_R54_CLR16_PROTOCOL_EXPIRED_STATUS_REF,
        P7_R54_CLR16_PROTOCOL_RATING_INCOMPLETE_STATUS_REF,
    ):
        if material.get("ready_for_purge_disposal_receipt") is not True or material.get("next_required_step") != P7_R54_CLR17_STEP_REF:
            raise ValueError("P7-R54-CLR16 abort/expire/incomplete must route to CLR17")
        if material.get("p5_inconclusive_direction_only_not_decision_materialized") is not True:
            raise ValueError("P7-R54-CLR16 abort/expire/incomplete must be inconclusive direction only")
    else:
        if status != P7_R54_CLR16_PROTOCOL_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-CLR16 unknown status")
        if material.get("blocked_by_consistency_guard_requires_purge") is True:
            if material.get("ready_for_purge_disposal_receipt") is not True or material.get("next_required_step") != P7_R54_CLR17_STEP_REF:
                raise ValueError("P7-R54-CLR16 consistency-guarded rows must route to CLR17 purge")
            if material.get("p5_decision_direction_ref") != "p5_or_emlis_repair_required_later_not_p8_material":
                raise ValueError("P7-R54-CLR16 consistency-guarded rows must not become P8 material")
        else:
            if material.get("ready_for_purge_disposal_receipt") is not False or material.get("next_required_step") != P7_R54_CLR16_BLOCKED_NEXT_REQUIRED_STEP_REF:
                raise ValueError("P7-R54-CLR16 blocked next step changed")
            if not blockers:
                raise ValueError("P7-R54-CLR16 blocked material must carry blockers")
    return True


def build_p7_r54_clr17_bodyfree_verified_disposal_receipt_from_protocol(
    pause_abort_expiration_protocol: Mapping[str, Any],
    *,
    disposal_verified_at_ref: Any = "r54_clr17_disposal_verified_at_bodyfree_ref_20260627",
) -> dict[str, Any]:
    """Create a body-free synthetic receipt shape for contract tests / intake.

    This does not perform disposal.  It only represents the allowed body-free
    receipt fields an external local purge operation may return.
    """

    protocol = safe_mapping(pause_abort_expiration_protocol)
    assert_p7_r54_clr16_pause_abort_expiration_protocol_contract(protocol)
    return {
        "review_session_id": _safe_review_session_id(protocol.get("review_session_id")),
        "disposal_operation_ref": P7_R54_CLR17_DISPOSAL_RECEIPT_REF,
        "body_full_packet_removed": True,
        "reviewer_notes_removed": True,
        "temporary_form_removed": True,
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "disposal_verified": True,
        "disposal_verified_at_ref": _safe_receipt_ref(disposal_verified_at_ref, default="r54_clr17_disposal_verified_at_bodyfree_ref_20260627", max_length=220),
        "execution_blocker_ids": [],
    }


def _receipt_value(receipt: Mapping[str, Any], key: str, fallback: Any) -> Any:
    return receipt[key] if key in receipt else fallback


def build_p7_r54_clr17_purge_disposal_receipt(
    *,
    pause_abort_expiration_protocol: Mapping[str, Any] | None = None,
    disposal_receipt: Mapping[str, Any] | None = None,
    body_full_packet_removed: bool = False,
    reviewer_notes_removed: bool = False,
    temporary_form_removed: bool = False,
    local_packet_exported: bool = False,
    content_hash_of_body_stored: bool = False,
    disposal_verified: bool = False,
    disposal_operation_ref: Any = "",
    disposal_verified_at_ref: Any = "",
    material_id: Any = "p7_r54_clr17_purge_disposal_receipt",
) -> dict[str, Any]:
    """Build the body-free CLR17 purge / disposal receipt intake."""

    protocol = (
        safe_mapping(pause_abort_expiration_protocol)
        if pause_abort_expiration_protocol is not None
        else build_p7_r54_clr16_pause_abort_expiration_protocol()
    )
    assert_p7_r54_clr16_pause_abort_expiration_protocol_contract(protocol)
    receipt = safe_mapping(disposal_receipt) if disposal_receipt is not None else {}
    if receipt and _receipt_contains_forbidden_payload(receipt):
        raise ValueError("P7-R54-CLR17 disposal receipt contains forbidden body/question/path/hash key")
    received_field_refs = sorted(receipt.keys()) if receipt else []
    received_has_only_allowed = bool(not receipt or set(received_field_refs).issubset(set(P7_R54_CLR17_RECEIPT_ALLOWED_FIELD_REFS)))
    if not received_has_only_allowed:
        raise ValueError("P7-R54-CLR17 disposal receipt includes fields outside the body-free allowlist")
    body_removed = bool(_receipt_value(receipt, "body_full_packet_removed", body_full_packet_removed))
    notes_removed = bool(_receipt_value(receipt, "reviewer_notes_removed", reviewer_notes_removed))
    form_removed = bool(_receipt_value(receipt, "temporary_form_removed", temporary_form_removed))
    packet_exported = bool(_receipt_value(receipt, "local_packet_exported", local_packet_exported))
    content_hash_stored = bool(_receipt_value(receipt, "content_hash_of_body_stored", content_hash_of_body_stored))
    verified = bool(_receipt_value(receipt, "disposal_verified", disposal_verified))
    operation_ref = _safe_receipt_ref(_receipt_value(receipt, "disposal_operation_ref", disposal_operation_ref), default="", max_length=220)
    verified_at_ref = _safe_receipt_ref(_receipt_value(receipt, "disposal_verified_at_ref", disposal_verified_at_ref), default="", max_length=220)
    receipt_blockers = dedupe_identifiers(_receipt_value(receipt, "execution_blocker_ids", []) or [], limit=100, max_length=180)
    protocol_allows_receipt = bool(
        protocol.get("purge_disposal_receipt_allowed_next") is True
        and protocol.get("ready_for_purge_disposal_receipt") is True
        and protocol.get("next_required_step") == P7_R54_CLR17_STEP_REF
    )
    disposal_blockers: list[str] = []
    if not protocol_allows_receipt:
        disposal_blockers.append("pause_abort_expiration_protocol_not_ready_for_disposal_receipt")
    if not body_removed:
        disposal_blockers.append("body_full_packet_not_removed")
    if not notes_removed:
        disposal_blockers.append("reviewer_notes_not_removed")
    if not form_removed:
        disposal_blockers.append("temporary_form_not_removed")
    if packet_exported:
        disposal_blockers.append("local_packet_exported_during_disposal")
    if content_hash_stored:
        disposal_blockers.append("content_hash_of_body_stored_during_disposal")
    if not verified:
        disposal_blockers.append("disposal_verified_flag_missing_or_false")
    if operation_ref != P7_R54_CLR17_DISPOSAL_RECEIPT_REF:
        disposal_blockers.append("bodyfree_disposal_operation_ref_missing_or_unexpected")
    if not verified_at_ref:
        disposal_blockers.append("disposal_verified_at_ref_missing")
    disposal_blockers = dedupe_identifiers([*disposal_blockers, *receipt_blockers], limit=100, max_length=180)
    ready = bool(protocol_allows_receipt and not disposal_blockers)
    upstream_blockers = dedupe_identifiers(protocol.get("open_execution_blocker_ids") or [], limit=100, max_length=180)
    open_blockers = dedupe_identifiers([*upstream_blockers, *([] if ready else disposal_blockers)], limit=120, max_length=180)
    material: dict[str, Any] = {
        "schema_version": P7_R54_CLR17_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_CLR_STEP,
        "scope": P7_R54_CLR_SCOPE,
        "policy_kind": P7_R54_CLR_POLICY_KIND,
        "policy_section": P7_R54_CLR17_STEP_REF,
        "operation_step_ref": P7_R54_CLR17_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_clr17_purge_disposal_receipt", max_length=220),
        "review_session_id": _safe_review_session_id(protocol.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "clr16_schema_version": P7_R54_CLR16_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION,
        "clr16_material_ref": clean_identifier(protocol.get("material_id"), default="p7_r54_clr16_pause_abort_expiration_protocol", max_length=220),
        "clr16_next_required_step": clean_identifier(protocol.get("next_required_step"), default=P7_R54_CLR16_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220),
        "clr16_pause_abort_expiration_protocol_status": clean_identifier(protocol.get("pause_abort_expiration_protocol_status"), default=P7_R54_CLR16_PROTOCOL_BLOCKED_STATUS_REF, max_length=180),
        "clr16_purge_disposal_receipt_allowed_next": protocol_allows_receipt,
        "clr16_ready_for_purge_disposal_receipt": protocol_allows_receipt,
        "clr16_open_execution_blocker_ids": upstream_blockers,
        "existing_op17_helper_ref": "build_p7_r54_op17_purge_disposal_receipt",
        "existing_op17_schema_version": r54op.P7_R54_OPERATION_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION,
        "existing_op17_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op17_current_refs_are_historical_here": True,
        "existing_op17_reused_as_actual_disposal_basis": False,
        "existing_op17_reused_as_actual_disposal_receipt_basis": False,
        "existing_op17_structural_contract_reused": True,
        "existing_ev15_schema_version": r54ev.P7_R54_EV_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION,
        "existing_ev15_current_refs": dict(r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "existing_ev15_current_refs_are_historical_here": True,
        "existing_ev15_reused_as_actual_disposal_basis": False,
        "existing_ev15_reused_as_actual_disposal_receipt_basis": False,
        "existing_ev15_structural_contract_reused": True,
        **clr15._current_ref_fields(),  # type: ignore[attr-defined]
        "required_case_count": clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "rating_row_count": int(protocol.get("rating_row_count") or 0) if protocol_allows_receipt else 0,
        "question_observation_row_count": int(protocol.get("question_observation_row_count") or 0) if protocol_allows_receipt else 0,
        "purge_disposal_receipt_status": P7_R54_CLR17_DISPOSAL_VERIFIED_STATUS_REF if ready else P7_R54_CLR17_DISPOSAL_BLOCKED_STATUS_REF,
        "purge_disposal_receipt_ref": operation_ref if ready else "purge_disposal_receipt_not_verified_bodyfree_20260627",
        "purge_disposal_receipt_policy_ref": P7_R54_CLR17_DISPOSAL_RECEIPT_POLICY_REF,
        "purge_disposal_receipt_reason_refs": [P7_R54_CLR17_READY_REASON_REF] if ready else dedupe_identifiers([P7_R54_CLR17_BLOCKED_REASON_REF, *disposal_blockers], limit=100, max_length=180),
        "received_receipt_allowed_field_refs": list(P7_R54_CLR17_RECEIPT_ALLOWED_FIELD_REFS),
        "received_receipt_field_refs": received_field_refs,
        "received_receipt_has_only_allowed_fields": received_has_only_allowed,
        "disposal_operation_ref": operation_ref,
        "disposal_verified_at_ref": verified_at_ref if ready else "",
        "removal_target_refs": list(P7_R54_CLR17_REMOVAL_TARGET_REFS),
        "removal_target_ref_count": len(P7_R54_CLR17_REMOVAL_TARGET_REFS),
        "body_full_packet_removed": body_removed,
        "body_removed": body_removed,
        "reviewer_notes_removed": notes_removed,
        "temporary_form_removed": form_removed,
        "all_required_local_targets_removed": bool(body_removed and notes_removed and form_removed),
        "local_packet_exported": packet_exported,
        "content_hash_of_body_stored": content_hash_stored,
        "body_full_packet_zip_inclusion_allowed": False,
        "reviewer_notes_export_allowed": False,
        "body_full_packet_export_allowed": False,
        "disposal_verified": ready,
        "actual_disposal_receipt_materialized_here": ready,
        "actual_disposal_run_here": False,
        "disposal_failure_decision_ref": "" if ready else P7_R54_CLR17_DISPOSAL_BLOCKED_STATUS_REF,
        "body_free_post_review_summary_allowed_next": ready,
        "actual_rating_rows_materialized_here": bool(protocol.get("actual_rating_rows_materialized_here") is True) if protocol_allows_receipt else False,
        "actual_blocker_rows_materialized_here": bool(protocol.get("actual_blocker_rows_materialized_here") is True) if protocol_allows_receipt else False,
        "actual_question_need_observation_rows_materialized_here": bool(protocol.get("actual_question_need_observation_rows_materialized_here") is True) if protocol_allows_receipt else False,
        "actual_review_evidence_complete": False,
        "human_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "execution_blocker_ids": open_blockers,
        "open_execution_blocker_ids": open_blockers,
        "upstream_execution_blocker_ids": upstream_blockers,
        "disposal_execution_blocker_ids": [] if ready else disposal_blockers,
        "implemented_steps": list(P7_R54_CLR17_IMPLEMENTED_STEPS if ready else (protocol.get("implemented_steps") or [])),
        "not_yet_implemented_steps": list(P7_R54_CLR17_NOT_YET_IMPLEMENTED_STEPS if ready else (protocol.get("not_yet_implemented_steps") or [])),
        "next_required_step": P7_R54_CLR18_STEP_REF if ready else P7_R54_CLR17_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_clr_no_touch_contract": clr15._no_touch_contract(),  # type: ignore[attr-defined]
        "body_free_markers": clr15._body_free_markers(),  # type: ignore[attr-defined]
        "body_free": True,
        "raw_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags_except(
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "disposal_verified",
        ),
    }
    material["actual_rating_rows_materialized_here"] = bool(protocol.get("actual_rating_rows_materialized_here") is True) if protocol_allows_receipt else False
    material["actual_blocker_rows_materialized_here"] = bool(protocol.get("actual_blocker_rows_materialized_here") is True) if protocol_allows_receipt else False
    material["actual_question_need_observation_rows_materialized_here"] = bool(protocol.get("actual_question_need_observation_rows_materialized_here") is True) if protocol_allows_receipt else False
    material["actual_disposal_receipt_materialized_here"] = ready
    material["disposal_verified"] = ready
    assert_p7_r54_clr17_purge_disposal_receipt_contract(material)
    return material


def assert_p7_r54_clr17_purge_disposal_receipt_contract(data: Mapping[str, Any]) -> bool:
    material = safe_mapping(data)
    _assert_required_fields(material, required=P7_R54_CLR17_PURGE_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS, source="P7-R54-CLR17")
    _assert_common_base(
        material,
        schema_version=P7_R54_CLR17_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION,
        policy_section=P7_R54_CLR17_STEP_REF,
        source="P7-R54-CLR17",
        allowed_true_false_flags=P7_R54_CLR17_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    if safe_mapping(material.get("existing_op17_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("P7-R54-CLR17 existing OP17 refs changed")
    if safe_mapping(material.get("existing_ev15_current_refs")) != r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("P7-R54-CLR17 existing EV15 refs changed")
    for key in (
        "existing_op17_current_refs_are_historical_here",
        "existing_op17_structural_contract_reused",
        "existing_ev15_current_refs_are_historical_here",
        "existing_ev15_structural_contract_reused",
        "human_review_completion_claim_blocked_here",
        "actual_human_review_completion_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
        "received_receipt_has_only_allowed_fields",
    ):
        if material.get(key) is not True:
            raise ValueError(f"P7-R54-CLR17 must keep {key}=True")
    for key in (
        "existing_op17_reused_as_actual_disposal_basis",
        "existing_op17_reused_as_actual_disposal_receipt_basis",
        "existing_ev15_reused_as_actual_disposal_basis",
        "existing_ev15_reused_as_actual_disposal_receipt_basis",
        "body_full_packet_zip_inclusion_allowed",
        "reviewer_notes_export_allowed",
        "body_full_packet_export_allowed",
        "actual_disposal_run_here",
        "actual_review_evidence_complete",
    ):
        if material.get(key) is not False:
            raise ValueError(f"P7-R54-CLR17 must keep {key}=False")
    if material.get("required_case_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-CLR17 required case count changed")
    if material.get("purge_disposal_receipt_status") not in P7_R54_CLR17_ALLOWED_DISPOSAL_STATUS_REFS:
        raise ValueError("P7-R54-CLR17 disposal status changed")
    if tuple(material.get("removal_target_refs") or ()) != P7_R54_CLR17_REMOVAL_TARGET_REFS:
        raise ValueError("P7-R54-CLR17 removal target refs changed")
    if tuple(material.get("received_receipt_allowed_field_refs") or ()) != P7_R54_CLR17_RECEIPT_ALLOWED_FIELD_REFS:
        raise ValueError("P7-R54-CLR17 receipt allowlist changed")
    blockers = dedupe_identifiers(material.get("execution_blocker_ids") or [], limit=120, max_length=180)
    if material.get("open_execution_blocker_ids") != blockers:
        raise ValueError("P7-R54-CLR17 open blockers mismatch")
    ready = material.get("purge_disposal_receipt_status") == P7_R54_CLR17_DISPOSAL_VERIFIED_STATUS_REF
    if ready and (material.get("local_packet_exported") is not False or material.get("content_hash_of_body_stored") is not False):
        raise ValueError("P7-R54-CLR17 ready must not export packet or store body hash")
    if not ready:
        blockers_for_export_guard = set(blockers)
        if material.get("local_packet_exported") is True and "local_packet_exported_during_disposal" not in blockers_for_export_guard:
            raise ValueError("P7-R54-CLR17 blocked local packet export must carry blocker")
        if material.get("content_hash_of_body_stored") is True and "content_hash_of_body_stored_during_disposal" not in blockers_for_export_guard:
            raise ValueError("P7-R54-CLR17 blocked content hash storage must carry blocker")
    if ready:
        for key in (
            "clr16_purge_disposal_receipt_allowed_next",
            "clr16_ready_for_purge_disposal_receipt",
            "body_full_packet_removed",
            "body_removed",
            "reviewer_notes_removed",
            "temporary_form_removed",
            "all_required_local_targets_removed",
            "disposal_verified",
            "actual_disposal_receipt_materialized_here",
            "body_free_post_review_summary_allowed_next",
        ):
            if material.get(key) is not True:
                raise ValueError(f"P7-R54-CLR17 ready must keep {key}=True")
        if material.get("purge_disposal_receipt_ref") != P7_R54_CLR17_DISPOSAL_RECEIPT_REF:
            raise ValueError("P7-R54-CLR17 ready receipt ref changed")
        if material.get("disposal_operation_ref") != P7_R54_CLR17_DISPOSAL_RECEIPT_REF:
            raise ValueError("P7-R54-CLR17 ready disposal operation ref changed")
        if material.get("disposal_execution_blocker_ids") != []:
            raise ValueError("P7-R54-CLR17 ready must not carry disposal blockers")
        if tuple(material.get("implemented_steps") or ()) != P7_R54_CLR17_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR17 ready implemented steps changed")
        if tuple(material.get("not_yet_implemented_steps") or ()) != P7_R54_CLR17_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR17 ready not-yet steps changed")
        if material.get("next_required_step") != P7_R54_CLR18_STEP_REF:
            raise ValueError("P7-R54-CLR17 ready must point to CLR18")
    else:
        if material.get("purge_disposal_receipt_status") != P7_R54_CLR17_DISPOSAL_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-CLR17 blocked status changed")
        if material.get("disposal_verified") is not False or material.get("actual_disposal_receipt_materialized_here") is not False:
            raise ValueError("P7-R54-CLR17 blocked must not verify disposal")
        if material.get("body_free_post_review_summary_allowed_next") is not False:
            raise ValueError("P7-R54-CLR17 blocked must not allow CLR18")
        if material.get("disposal_failure_decision_ref") != P7_R54_CLR17_DISPOSAL_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-CLR17 blocked decision ref changed")
        if not material.get("disposal_execution_blocker_ids") and not blockers:
            raise ValueError("P7-R54-CLR17 blocked must carry blockers")
        if material.get("next_required_step") != P7_R54_CLR17_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-CLR17 blocked next step changed")
    return True


build_p7_r54_current_snapshot_local_run_clr16_pause_abort_expiration_protocol = build_p7_r54_clr16_pause_abort_expiration_protocol
assert_p7_r54_current_snapshot_local_run_clr16_pause_abort_expiration_protocol_contract = assert_p7_r54_clr16_pause_abort_expiration_protocol_contract
build_p7_r54_current_snapshot_pause_abort_expiration_protocol_bodyfree = build_p7_r54_clr16_pause_abort_expiration_protocol
assert_p7_r54_current_snapshot_pause_abort_expiration_protocol_bodyfree_contract = assert_p7_r54_clr16_pause_abort_expiration_protocol_contract
build_p7_r54_current_snapshot_local_run_clr17_purge_disposal_receipt = build_p7_r54_clr17_purge_disposal_receipt
assert_p7_r54_current_snapshot_local_run_clr17_purge_disposal_receipt_contract = assert_p7_r54_clr17_purge_disposal_receipt_contract
build_p7_r54_current_snapshot_purge_disposal_receipt_bodyfree = build_p7_r54_clr17_purge_disposal_receipt
assert_p7_r54_current_snapshot_purge_disposal_receipt_bodyfree_contract = assert_p7_r54_clr17_purge_disposal_receipt_contract

build_clr16_pause_abort_expiration_protocol = build_p7_r54_clr16_pause_abort_expiration_protocol
assert_clr16_pause_abort_expiration_protocol_contract = assert_p7_r54_clr16_pause_abort_expiration_protocol_contract
build_clr17_bodyfree_verified_disposal_receipt_from_protocol = build_p7_r54_clr17_bodyfree_verified_disposal_receipt_from_protocol
build_clr17_purge_disposal_receipt = build_p7_r54_clr17_purge_disposal_receipt
assert_clr17_purge_disposal_receipt_contract = assert_p7_r54_clr17_purge_disposal_receipt_contract


# Compatibility aliases for current snapshot CLR16/CLR17 design wording.
P7_R54_CLR16_READY_STATUS_REF: Final = P7_R54_CLR16_PROTOCOL_READY_STATUS_REF
P7_R54_CLR16_PAUSED_STATUS_REF: Final = P7_R54_CLR16_PROTOCOL_PAUSED_STATUS_REF
P7_R54_CLR16_ABORTED_STATUS_REF: Final = P7_R54_CLR16_PROTOCOL_ABORTED_STATUS_REF
P7_R54_CLR16_EXPIRED_STATUS_REF: Final = P7_R54_CLR16_PROTOCOL_EXPIRED_STATUS_REF
P7_R54_CLR16_RATING_INCOMPLETE_STATUS_REF: Final = P7_R54_CLR16_PROTOCOL_RATING_INCOMPLETE_STATUS_REF
P7_R54_CLR16_BLOCKED_STATUS_REF: Final = P7_R54_CLR16_PROTOCOL_BLOCKED_STATUS_REF
build_p7_r54_clr17_verified_disposal_receipt_bodyfree = build_p7_r54_clr17_bodyfree_verified_disposal_receipt_from_protocol
build_p7_r54_clr17_bodyfree_verified_disposal_receipt_from_clr16 = build_p7_r54_clr17_bodyfree_verified_disposal_receipt_from_protocol
build_clr17_verified_disposal_receipt_bodyfree = build_p7_r54_clr17_verified_disposal_receipt_bodyfree

__all__ = (
    "P7_R54_CLR16_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION",
    "P7_R54_CLR17_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION",
    "P7_R54_CLR16_SCHEMA_VERSION",
    "P7_R54_CLR17_SCHEMA_VERSION",
    "P7_R54_CLR16_STEP_REF",
    "P7_R54_CLR17_STEP_REF",
    "P7_R54_CLR18_STEP_REF",
    "P7_R54_CLR16_PROTOCOL_READY_STATUS_REF",
    "P7_R54_CLR16_PROTOCOL_PAUSED_STATUS_REF",
    "P7_R54_CLR16_PROTOCOL_ABORTED_STATUS_REF",
    "P7_R54_CLR16_PROTOCOL_EXPIRED_STATUS_REF",
    "P7_R54_CLR16_PROTOCOL_RATING_INCOMPLETE_STATUS_REF",
    "P7_R54_CLR16_PROTOCOL_BLOCKED_STATUS_REF",
    "P7_R54_CLR16_PROTOCOL_STATUS_REFS",
    "P7_R54_CLR16_PROTOCOL_REF",
    "P7_R54_CLR16_PROTOCOL_POLICY_REF",
    "P7_R54_CLR16_READY_REASON_REF",
    "P7_R54_CLR16_PAUSED_REASON_REF",
    "P7_R54_CLR16_ABORTED_REASON_REF",
    "P7_R54_CLR16_EXPIRED_REASON_REF",
    "P7_R54_CLR16_RATING_INCOMPLETE_REASON_REF",
    "P7_R54_CLR16_BLOCKED_REASON_REF",
    "P7_R54_CLR16_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_CLR16_PAUSED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_CLR16_REVIEW_OPERATION_STATUS_REFS",
    "P7_R54_CLR16_REQUIRED_LOCAL_DELETE_TARGET_REFS",
    "P7_R54_CLR16_PURGE_TRIGGER_REFS",
    "P7_R54_CLR16_P5_DECISION_DIRECTION_REFS",
    "P7_R54_CLR17_DISPOSAL_VERIFIED_STATUS_REF",
    "P7_R54_CLR17_DISPOSAL_BLOCKED_STATUS_REF",
    "P7_R54_CLR17_ALLOWED_DISPOSAL_STATUS_REFS",
    "P7_R54_CLR17_DISPOSAL_RECEIPT_REF",
    "P7_R54_CLR17_DISPOSAL_RECEIPT_POLICY_REF",
    "P7_R54_CLR17_READY_REASON_REF",
    "P7_R54_CLR17_BLOCKED_REASON_REF",
    "P7_R54_CLR17_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_CLR17_REMOVAL_TARGET_REFS",
    "P7_R54_CLR17_RECEIPT_ALLOWED_FIELD_REFS",
    "P7_R54_CLR16_IMPLEMENTED_STEPS",
    "P7_R54_CLR16_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_CLR17_IMPLEMENTED_STEPS",
    "P7_R54_CLR17_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_CLR16_ALLOWED_TRUE_FALSE_FLAG_REFS",
    "P7_R54_CLR17_ALLOWED_TRUE_FALSE_FLAG_REFS",
    "P7_R54_CLR16_PAUSE_ABORT_EXPIRATION_PROTOCOL_REQUIRED_FIELD_REFS",
    "P7_R54_CLR17_PURGE_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS",
    "build_p7_r54_clr16_pause_abort_expiration_protocol",
    "assert_p7_r54_clr16_pause_abort_expiration_protocol_contract",
    "build_p7_r54_clr17_bodyfree_verified_disposal_receipt_from_protocol",
    "build_p7_r54_clr17_purge_disposal_receipt",
    "assert_p7_r54_clr17_purge_disposal_receipt_contract",
    "build_p7_r54_current_snapshot_local_run_clr16_pause_abort_expiration_protocol",
    "assert_p7_r54_current_snapshot_local_run_clr16_pause_abort_expiration_protocol_contract",
    "build_p7_r54_current_snapshot_pause_abort_expiration_protocol_bodyfree",
    "assert_p7_r54_current_snapshot_pause_abort_expiration_protocol_bodyfree_contract",
    "build_p7_r54_current_snapshot_local_run_clr17_purge_disposal_receipt",
    "assert_p7_r54_current_snapshot_local_run_clr17_purge_disposal_receipt_contract",
    "build_p7_r54_current_snapshot_purge_disposal_receipt_bodyfree",
    "assert_p7_r54_current_snapshot_purge_disposal_receipt_bodyfree_contract",
    "build_clr16_pause_abort_expiration_protocol",
    "assert_clr16_pause_abort_expiration_protocol_contract",
    "build_clr17_bodyfree_verified_disposal_receipt_from_protocol",
    "build_clr17_purge_disposal_receipt",
    "assert_clr17_purge_disposal_receipt_contract",
)
