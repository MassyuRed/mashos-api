# -*- coding: utf-8 -*-
"""P7-R54 current snapshot local review run CLR18-CLR19 helpers.

CLR18 creates only a body-free post-review summary from already-normalized
rating/question rows and an already-verified body-free disposal receipt.  It
keeps the packet body, returned Emlis body, history surface, reviewer notes,
local paths, hashes, terminal output, and question text out of the material.

CLR19 separates P5 decision candidates from the body-free summary.  It can mark
only a candidate ref, not P5 final, P6 start, P8 start, release, API, DB, RN,
runtime, or public contract changes.  P8 material remains later candidate-only
material; question text and P8 implementation are still prohibited.
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
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr12_clr13_20260627 as clr13
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr14_clr15_20260627 as clr15
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr16_clr17_20260627 as clr17


P7_R54_CLR18_BODYFREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr18_bodyfree_post_review_summary.bodyfree.v1"
)
P7_R54_CLR19_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr19_p5_decision_candidate_separation.bodyfree.v1"
)
P7_R54_CLR18_SCHEMA_VERSION: Final = P7_R54_CLR18_BODYFREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION
P7_R54_CLR19_SCHEMA_VERSION: Final = P7_R54_CLR19_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION

P7_R54_CLR_STEP: Final = clr03.P7_R54_CLR_STEP
P7_R54_CLR_SCOPE: Final = clr03.P7_R54_CLR_SCOPE
P7_R54_CLR_POLICY_KIND: Final = clr03.P7_R54_CLR_POLICY_KIND
P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID: Final = clr03.P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID
P7_R54_CLR18_STEP_REF: Final = clr03.P7_R54_CLR18_STEP_REF
P7_R54_CLR19_STEP_REF: Final = clr03.P7_R54_CLR19_STEP_REF
P7_R54_CLR20_STEP_REF: Final = clr03.P7_R54_CLR20_STEP_REF

P7_R54_CLR18_SUMMARY_READY_STATUS_REF: Final = "BODYFREE_POST_REVIEW_SUMMARY_READY_20260627"
P7_R54_CLR18_SUMMARY_BLOCKED_STATUS_REF: Final = "BODYFREE_POST_REVIEW_SUMMARY_BLOCKED_20260627"
P7_R54_CLR18_ALLOWED_SUMMARY_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_CLR18_SUMMARY_READY_STATUS_REF,
    P7_R54_CLR18_SUMMARY_BLOCKED_STATUS_REF,
)
P7_R54_CLR18_SUMMARY_REF: Final = "r54_clr18_bodyfree_post_review_summary_20260627"
P7_R54_CLR18_SUMMARY_POLICY_REF: Final = "rating_blocker_question_disposal_counts_only_no_body_no_question_text_20260627"
P7_R54_CLR18_READY_REASON_REF: Final = "r54_clr18_rating_blocker_question_disposal_summary_ready_bodyfree"
P7_R54_CLR18_BLOCKED_REASON_REF: Final = "r54_clr18_bodyfree_post_review_summary_blocked"
P7_R54_CLR18_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-CLR-18_blocked_until_bodyfree_summary_inputs_repaired_before_p5_decision_candidate_separation"
)

P7_R54_CLR19_DECISION_SEPARATION_READY_STATUS_REF: Final = "P5_DECISION_CANDIDATE_SEPARATED_BODYFREE_20260627"
P7_R54_CLR19_DECISION_SEPARATION_BLOCKED_STATUS_REF: Final = "P5_DECISION_CANDIDATE_SEPARATION_BLOCKED_20260627"
P7_R54_CLR19_ALLOWED_DECISION_SEPARATION_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_CLR19_DECISION_SEPARATION_READY_STATUS_REF,
    P7_R54_CLR19_DECISION_SEPARATION_BLOCKED_STATUS_REF,
)
P7_R54_CLR19_DECISION_SEPARATION_REF: Final = "r54_clr19_p5_decision_candidate_separation_bodyfree_20260627"
P7_R54_CLR19_DECISION_SEPARATION_POLICY_REF: Final = (
    "p5_candidate_p5_repair_p4_r12_inconclusive_separated_no_p6_p8_release_start_20260627"
)
P7_R54_CLR19_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-CLR-19_blocked_until_p5_decision_candidate_separation_repaired_before_candidate_handoffs"
)
P7_R54_CLR19_P5_REPAIR_NEXT_REQUIRED_STEP_REF: Final = "p5_repair_return_required_before_p6_candidate_handoff"
P7_R54_CLR19_P4_R12_REPAIR_NEXT_REQUIRED_STEP_REF: Final = (
    "p4_r12_targeted_current_only_surface_repair_required_before_p6_candidate_handoff"
)
P7_R54_CLR19_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF: Final = (
    "r54_operation_inconclusive_retry_or_r52_reintake_before_p6_candidate_handoff"
)
P7_R54_CLR19_NEXT_WORK_AFTER_CLR18_REF: Final = "r54_clr19_p5_decision_candidate_separation_after_bodyfree_post_review_summary"
P7_R54_CLR19_NEXT_WORK_AFTER_CLR19_REF: Final = "r54_clr20_p6_candidate_only_handoff_after_p5_decision_candidate_separation"

P7_R54_CLR19_P5_CONFIRMED_CANDIDATE_REF: Final = "P5_CONFIRMED_CANDIDATE"
P7_R54_CLR19_P5_REPAIR_RETURN_REF: Final = "P5_REPAIR_RETURN"
P7_R54_CLR19_P4_R12_TARGETED_REPAIR_REF: Final = "P4_R12_TARGETED_CURRENT_ONLY_SURFACE_REPAIR"
P7_R54_CLR19_INCONCLUSIVE_REF: Final = "R54_OPERATION_INCONCLUSIVE"
P7_R54_CLR19_BLOCKED_PREFLIGHT_REF: Final = "R54_OPERATION_BLOCKED_PREFLIGHT"
P7_R54_CLR19_BLOCKED_DISPOSAL_REF: Final = "R54_OPERATION_BLOCKED_DISPOSAL"
P7_R54_CLR19_BLOCKED_BODY_LEAK_OR_QUESTION_TEXT_REF: Final = "R54_OPERATION_BLOCKED_BODY_LEAK_OR_QUESTION_TEXT"
P7_R54_CLR19_BLOCKED_NO_TOUCH_VIOLATION_REF: Final = "R54_OPERATION_BLOCKED_NO_TOUCH_VIOLATION"
P7_R54_CLR19_DECISION_CANDIDATE_REFS: Final[tuple[str, ...]] = (
    P7_R54_CLR19_P5_CONFIRMED_CANDIDATE_REF,
    P7_R54_CLR19_P5_REPAIR_RETURN_REF,
    P7_R54_CLR19_P4_R12_TARGETED_REPAIR_REF,
    P7_R54_CLR19_INCONCLUSIVE_REF,
    P7_R54_CLR19_BLOCKED_PREFLIGHT_REF,
    P7_R54_CLR19_BLOCKED_DISPOSAL_REF,
    P7_R54_CLR19_BLOCKED_BODY_LEAK_OR_QUESTION_TEXT_REF,
    P7_R54_CLR19_BLOCKED_NO_TOUCH_VIOLATION_REF,
)
P7_R54_CLR19_NOT_QUESTION_REPAIR_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = (
    "not_question_emlis_readfeel_repair_required",
    "not_question_p5_surface_repair_required",
    "not_question_gate_boundary_required",
)
P7_R54_CLR19_REPAIR_REQUIRED_REFS: Final[tuple[str, ...]] = (
    "emlis_readfeel_repair_required",
    "p5_surface_repair_required",
    "gate_boundary_repair_required",
    "p4_current_surface_repair_required",
)
P7_R54_CLR19_P4_CURRENT_ONLY_REPAIR_REFS: Final[tuple[str, ...]] = (
    "p4_current_surface_repair_required",
)

P7_R54_CLR18_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*clr17.P7_R54_CLR17_IMPLEMENTED_STEPS, P7_R54_CLR18_STEP_REF)
P7_R54_CLR18_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = clr03.P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR01[17:]
P7_R54_CLR19_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_CLR18_IMPLEMENTED_STEPS, P7_R54_CLR19_STEP_REF)
P7_R54_CLR19_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = clr03.P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR01[18:]

P7_R54_CLR18_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[frozenset[str]] = frozenset(
    {
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "disposal_verified",
    }
)
P7_R54_CLR19_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[frozenset[str]] = frozenset(
    {
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "disposal_verified",
        "p5_human_blind_qa_confirmed_candidate",
    }
)

P7_R54_CLR_PROHIBITED_PAYLOAD_OR_QUESTION_FIELD_REFS: Final[frozenset[str]] = clr17.P7_R54_CLR_PROHIBITED_PAYLOAD_OR_QUESTION_FIELD_REFS

P7_R54_CLR18_BODYFREE_POST_REVIEW_SUMMARY_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *clr03.P7_R54_CLR_COMMON_REQUIRED_FIELD_REFS,
    "clr17_schema_version",
    "clr17_material_ref",
    "clr17_next_required_step",
    "clr17_purge_disposal_receipt_status",
    "clr17_bodyfree_summary_allowed_next",
    "clr15_schema_version",
    "clr15_material_ref",
    "clr15_next_required_step",
    "clr15_rating_question_consistency_guard_status",
    "clr15_consistency_guard_passed",
    "existing_op18_helper_ref",
    "existing_op18_schema_version",
    "existing_op18_operation_current_refs",
    "existing_op18_current_refs_are_historical_here",
    "existing_op18_reused_as_actual_summary_basis",
    "existing_op18_reused_as_actual_post_review_summary_basis",
    "existing_op18_structural_contract_reused",
    "existing_ev16_schema_version",
    "existing_ev16_current_refs",
    "existing_ev16_current_refs_are_historical_here",
    "existing_ev16_reused_as_actual_summary_basis",
    "existing_ev16_reused_as_actual_post_review_summary_basis",
    "existing_ev16_structural_contract_reused",
    "required_case_count",
    "reviewed_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "bodyfree_post_review_summary_status",
    "bodyfree_post_review_summary_ref",
    "bodyfree_post_review_summary_policy_ref",
    "bodyfree_post_review_summary_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "summary_blocker_ids",
    "summary_blocker_count",
    "verdict_counts",
    "overall_read_feeling_counts",
    "axis_score_averages",
    "rating_axis_target_thresholds",
    "below_target_axis_refs",
    "below_target_axis_count",
    "readfeel_blocker_counts",
    "open_readfeel_blocker_count",
    "execution_blocker_counts",
    "open_execution_blocker_count",
    "primary_class_counts",
    "ambiguity_kind_counts",
    "one_question_fit_counts",
    "repair_required_counts",
    "plan_candidate_flag_counts",
    "p8_material_candidate_row_count",
    "p8_material_candidate_allowed_primary_class_counts",
    "not_question_repair_required_count",
    "insufficient_material_execution_blocker_count",
    "consistency_issue_count",
    "consistency_issue_direction_counts",
    "disposal_verified",
    "body_removed",
    "reviewer_notes_removed",
    "temporary_form_removed",
    "local_packet_exported",
    "content_hash_of_body_stored",
    "all_required_review_counts_present",
    "all_required_summary_inputs_ready",
    "no_body_leak_validation_passed",
    "no_question_text_validation_passed",
    "no_touch_validation_passed",
    "p5_decision_candidate_separation_allowed_next",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "actual_review_evidence_complete",
    "human_review_completion_claim_blocked_here",
    "actual_human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    *clr03.P7_R54_CLR_CURRENT_REF_REQUIRED_FIELD_REFS,
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    *clr03.P7_R54_CLR_NO_TOUCH_BODYFREE_REQUIRED_FIELD_REFS,
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    *clr03.P7_R54_CLR_FALSE_FLAG_REFS,
)

P7_R54_CLR19_P5_DECISION_CANDIDATE_SEPARATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *clr03.P7_R54_CLR_COMMON_REQUIRED_FIELD_REFS,
    "clr18_schema_version",
    "clr18_material_ref",
    "clr18_next_required_step",
    "clr18_bodyfree_post_review_summary_status",
    "clr18_decision_separation_allowed_next",
    "existing_op19_helper_ref",
    "existing_op19_schema_version",
    "existing_op19_operation_current_refs",
    "existing_op19_current_refs_are_historical_here",
    "existing_op19_reused_as_actual_decision_basis",
    "existing_op19_reused_as_actual_decision_candidate_basis",
    "existing_op19_structural_contract_reused",
    "existing_ev17_schema_version",
    "existing_ev17_current_refs",
    "existing_ev17_current_refs_are_historical_here",
    "existing_ev17_reused_as_actual_decision_basis",
    "existing_ev17_reused_as_actual_decision_candidate_basis",
    "existing_ev17_structural_contract_reused",
    "required_case_count",
    "reviewed_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "decision_candidate_separation_status",
    "decision_candidate_separation_ref",
    "decision_candidate_separation_policy_ref",
    "decision_candidate_separation_reason_refs",
    "decision_candidate_allowed_refs",
    "p5_decision_candidate_ref",
    "p5_decision_candidate_materialized_here",
    "p5_decision_candidate_reason_refs",
    "p5_decision_repair_reason_refs",
    "p5_decision_inconclusive_reason_refs",
    "p4_current_only_surface_issue_refs",
    "p5_confirmed_candidate_conditions_met",
    "p5_repair_return_required",
    "p4_r12_targeted_current_only_surface_repair_required",
    "r54_operation_inconclusive_required",
    "r54_operation_blocked_preflight_required",
    "r54_operation_blocked_disposal_required",
    "r54_operation_blocked_body_leak_or_question_text_required",
    "r54_operation_blocked_no_touch_violation_required",
    "verdict_counts",
    "overall_read_feeling_counts",
    "axis_score_averages",
    "rating_axis_target_thresholds",
    "below_target_axis_refs",
    "open_readfeel_blocker_count",
    "open_execution_blocker_count",
    "primary_class_counts",
    "repair_required_counts",
    "p8_material_candidate_row_count",
    "p8_material_candidate_allowed_primary_class_counts",
    "not_question_repair_required_count",
    "insufficient_material_execution_blocker_count",
    "disposal_verified",
    "body_removed",
    "reviewer_notes_removed",
    "temporary_form_removed",
    "local_packet_exported",
    "content_hash_of_body_stored",
    "no_body_leak_validation_passed",
    "no_question_text_validation_passed",
    "no_touch_validation_passed",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_human_blind_qa_confirmed_final",
    "p6_limited_human_readfeel_start_allowed",
    "p8_start_allowed",
    "release_allowed",
    "p5_final_confirmation_blocked_here",
    "p6_start_blocked_here",
    "p8_start_blocked_here",
    "release_blocked_here",
    "actual_review_evidence_complete",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    *clr03.P7_R54_CLR_CURRENT_REF_REQUIRED_FIELD_REFS,
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    *clr03.P7_R54_CLR_NO_TOUCH_BODYFREE_REQUIRED_FIELD_REFS,
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    *clr03.P7_R54_CLR_FALSE_FLAG_REFS,
)


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


def _current_ref_fields() -> dict[str, Any]:
    refs = dict(clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS)
    return {
        "operation_current_refs": refs,
        "operation_current_ref_count": len(refs),
        "operation_current_ref_keys": list(refs.keys()),
        "operation_current_ref_key_count": len(refs),
        "required_current_snapshot_ref_keys": list(clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS),
        "required_current_snapshot_ref_key_count": len(clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS),
        "all_required_current_refs_present": True,
        "actual_review_basis_ref": clr03.P7_R54_CLR_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": clr03.P7_R54_CLR_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "operation_current_refs_used_as_actual_review_basis": True,
    }


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


def _contains_forbidden_key(value: Any) -> bool:
    return clr15._contains_forbidden_key(value)  # type: ignore[attr-defined]


def _count_refs(rows: Sequence[Mapping[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = row.get(field)
        if isinstance(value, Mapping):
            for key, enabled in value.items():
                if enabled is True:
                    ref = clean_identifier(key, max_length=180)
                    counts[ref] = counts.get(ref, 0) + 1
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for item in value:
                ref = clean_identifier(item, max_length=180)
                if ref:
                    counts[ref] = counts.get(ref, 0) + 1
        else:
            ref = clean_identifier(value, max_length=180)
            if ref:
                counts[ref] = counts.get(ref, 0) + 1
    return counts


def _count_plan_flags(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        flags = safe_mapping(row.get("plan_candidate_flags"))
        for key, enabled in flags.items():
            if enabled is True:
                ref = clean_identifier(key, max_length=180)
                counts[ref] = counts.get(ref, 0) + 1
    return counts


def _axis_score_averages(rating_rows: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    if not rating_rows:
        return {}
    out: dict[str, float] = {}
    for axis in clr13.P7_R54_CLR12_RATING_AXIS_REFS:
        values: list[float] = []
        for row in rating_rows:
            scores = safe_mapping(row.get("axis_scores"))
            score = scores.get(axis)
            if isinstance(score, (int, float)) and not isinstance(score, bool):
                values.append(float(score))
        if values:
            out[axis] = round(sum(values) / len(values), 4)
    return out


def _below_target_axis_refs(rating_rows: Sequence[Mapping[str, Any]], axis_averages: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for row in rating_rows:
        refs.extend(row.get("below_target_axis_refs") or [])
    averages = safe_mapping(axis_averages)
    for axis, target in clr13.P7_R54_CLR12_RATING_AXIS_TARGET_THRESHOLDS.items():
        score = averages.get(axis)
        if not isinstance(score, (int, float)) or isinstance(score, bool) or float(score) < float(target):
            refs.append(axis)
    return dedupe_identifiers(refs, limit=24, max_length=180)


def _p8_material_candidate_counts(question_rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in question_rows:
        if row.get("p8_material_candidate_allowed") is True or row.get("p8_design_material_candidate_allowed") is True:
            primary = clean_identifier(row.get("question_need_primary_class"), max_length=180)
            if primary:
                counts[primary] = counts.get(primary, 0) + 1
    return counts


def _not_question_repair_count(question_rows: Sequence[Mapping[str, Any]]) -> int:
    count = 0
    for row in question_rows:
        primary = clean_identifier(row.get("question_need_primary_class"), max_length=180)
        if row.get("not_question_repair_required") is True or primary in P7_R54_CLR19_NOT_QUESTION_REPAIR_PRIMARY_CLASS_REFS:
            count += 1
    return count


def _insufficient_material_execution_blocker_count(question_rows: Sequence[Mapping[str, Any]]) -> int:
    count = 0
    for row in question_rows:
        primary = clean_identifier(row.get("question_need_primary_class"), max_length=180)
        if row.get("insufficient_material_execution_blocker") is True or primary == "insufficient_material_execution_blocker":
            count += 1
    return count


def _decision_issue_ids_for_summary_filter() -> set[str]:
    """Return CLR15/CLR16 issue ids that are decision material, not CLR18 summary blockers.

    CLR18 is a body-free count summary. It blocks on disposal, body leak,
    question text leak, no-touch violations, missing rows, and true execution
    blockers. P5 readfeel / consistency issues stay visible as counts so CLR19
    can separate P5 repair vs confirmed candidate instead of hiding them as
    disposal failures.
    """

    return {
        "rating_question_consistency_guard_blocked_purge_required",
        *clr15.P7_R54_CLR15_CONSISTENCY_ISSUE_ID_REFS,
    }


def _execution_blockers_for_summary(values: Sequence[Any]) -> list[str]:
    decision_issue_ids = _decision_issue_ids_for_summary_filter()
    return [
        blocker_id
        for blocker_id in dedupe_identifiers(values, limit=120, max_length=180)
        if blocker_id not in decision_issue_ids
    ]


def _summary_inputs_ready(*, clr17_receipt: Mapping[str, Any], clr15_guard: Mapping[str, Any]) -> tuple[bool, list[str]]:
    blockers: list[str] = []
    hard_blockers: list[str] = []
    if not clr17_receipt:
        hard_blockers.append("clr17_disposal_receipt_missing_for_bodyfree_summary")
    if not clr15_guard:
        hard_blockers.append("clr15_rating_question_consistency_guard_missing_for_bodyfree_summary")
    if clr17_receipt and not (
        clr17_receipt.get("purge_disposal_receipt_status") == clr17.P7_R54_CLR17_DISPOSAL_VERIFIED_STATUS_REF
        and clr17_receipt.get("body_free_post_review_summary_allowed_next") is True
        and clr17_receipt.get("disposal_verified") is True
        and clr17_receipt.get("actual_disposal_receipt_materialized_here") is True
    ):
        blockers.append("clr17_disposal_receipt_not_verified_for_bodyfree_summary")
    if clr15_guard:
        guard_status = clr15_guard.get("rating_question_consistency_guard_status")
        guard_has_24_rows = bool(
            int(clr15_guard.get("rating_row_count") or 0) == clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
            and int(clr15_guard.get("question_observation_row_count") or 0) == clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
            and len(clr15_guard.get("rating_rows") or []) == clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
            and len(clr15_guard.get("question_observation_rows") or []) == clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        )
        if guard_status not in {
            clr15.P7_R54_CLR15_CONSISTENCY_GUARD_READY_STATUS_REF,
            clr15.P7_R54_CLR15_CONSISTENCY_GUARD_BLOCKED_STATUS_REF,
        } or not guard_has_24_rows:
            hard_blockers.append("clr15_rating_question_rows_not_ready_for_bodyfree_summary")
        if _execution_blockers_for_summary(clr15_guard.get("open_execution_blocker_ids") or []):
            hard_blockers.append("clr15_execution_blocker_not_decision_issue_for_bodyfree_summary")
    if clr17_receipt and _execution_blockers_for_summary(clr17_receipt.get("open_execution_blocker_ids") or []):
        # Disposal/purge failures are still useful as body-free decision material for CLR19.
        # Missing rows, leaks, and session mismatches remain hard blockers.
        blockers.append("clr17_execution_blocker_not_decision_issue_for_bodyfree_summary")
    if _contains_forbidden_key(clr17_receipt) or _contains_forbidden_key(clr15_guard):
        hard_blockers.append("body_or_question_payload_key_detected_in_summary_inputs")
    if clr17_receipt and clr15_guard:
        session_17 = _safe_review_session_id(clr17_receipt.get("review_session_id"))
        session_15 = _safe_review_session_id(clr15_guard.get("review_session_id"))
        if session_17 != session_15:
            hard_blockers.append("review_session_mismatch_between_clr17_and_clr15")
    return not hard_blockers, dedupe_identifiers([*hard_blockers, *blockers], limit=120, max_length=180)


def build_p7_r54_clr18_bodyfree_post_review_summary(
    *,
    purge_disposal_receipt: Mapping[str, Any] | None = None,
    rating_question_consistency_guard: Mapping[str, Any] | None = None,
    question_need_observation_normalization: Mapping[str, Any] | None = None,
    readfeel_blocker_execution_blocker_ingestion: Mapping[str, Any] | None = None,
    rating_row_normalization: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_clr18_bodyfree_post_review_summary",
) -> dict[str, Any]:
    """Build a body-free count summary from CLR15 rows and CLR17 disposal receipt."""
    clr17_receipt = safe_mapping(purge_disposal_receipt)
    if clr17_receipt:
        clr17.assert_p7_r54_clr17_purge_disposal_receipt_contract(clr17_receipt)
    clr15_guard = safe_mapping(rating_question_consistency_guard)
    if clr15_guard:
        clr15.assert_p7_r54_clr15_rating_question_consistency_guard_contract(clr15_guard)

    inputs_ready, input_blockers = _summary_inputs_ready(clr17_receipt=clr17_receipt, clr15_guard=clr15_guard)
    rating_rows = [safe_mapping(row) for row in (clr15_guard.get("rating_rows") or [])] if inputs_ready else []
    question_rows = [safe_mapping(row) for row in (clr15_guard.get("question_observation_rows") or [])] if inputs_ready else []
    verdict_counts = _count_refs(rating_rows, "verdict") if inputs_ready else {}
    overall_read_feeling_counts = _count_refs(rating_rows, "overall_read_feeling_ref") if inputs_ready else {}
    axis_score_averages = _axis_score_averages(rating_rows) if inputs_ready else {}
    below_target_axis_refs = _below_target_axis_refs(rating_rows, axis_score_averages) if inputs_ready else []
    readfeel_blocker_counts = _count_refs(rating_rows, "readfeel_blocker_ids") if inputs_ready else {}
    execution_blocker_counts = _count_refs(rating_rows, "execution_blocker_ids") if inputs_ready else {}
    primary_class_counts = _count_refs(question_rows, "question_need_primary_class") if inputs_ready else {}
    ambiguity_kind_counts = _count_refs(question_rows, "ambiguity_kind_refs") if inputs_ready else {}
    one_question_fit_counts = _count_refs(question_rows, "one_question_fit_ref") if inputs_ready else {}
    repair_required_counts = _count_refs(question_rows, "repair_required_refs") if inputs_ready else {}
    plan_candidate_flag_counts = _count_plan_flags(question_rows) if inputs_ready else {}
    p8_counts = _p8_material_candidate_counts(question_rows) if inputs_ready else {}
    not_question_repair_count = _not_question_repair_count(question_rows) if inputs_ready else 0
    insufficient_material_count = _insufficient_material_execution_blocker_count(question_rows) if inputs_ready else 0
    open_execution_blockers = dedupe_identifiers(
        [
            *input_blockers,
            *_execution_blockers_for_summary(clr17_receipt.get("open_execution_blocker_ids") or []),
            *_execution_blockers_for_summary(clr15_guard.get("open_execution_blocker_ids") or []),
        ],
        limit=120,
        max_length=180,
    )
    counts_ready = bool(
        inputs_ready
        and len(rating_rows) == clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and len(question_rows) == clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and int(clr15_guard.get("rating_row_count") or 0) == clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and int(clr15_guard.get("question_observation_row_count") or 0) == clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and int(clr17_receipt.get("rating_row_count") or 0) == clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and int(clr17_receipt.get("question_observation_row_count") or 0) == clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
    )
    no_body_leak_validation_passed = bool(
        inputs_ready
        and clr17_receipt.get("local_packet_exported") is False
        and clr17_receipt.get("content_hash_of_body_stored") is False
        and all(row.get("raw_body_included") is False for row in rating_rows)
        and all(row.get("returned_emlis_body_included") is False for row in rating_rows)
        and all(row.get("history_surface_included") is False for row in rating_rows)
        and all(row.get("local_path_included") is False for row in rating_rows)
        and all(row.get("body_hash_included") is False for row in rating_rows)
        and all(row.get("packet_content_included") is False for row in rating_rows)
        and all(row.get("raw_body_included") is False for row in question_rows)
        and all(row.get("history_surface_included") is False for row in question_rows)
        and all(row.get("local_path_included") is False for row in question_rows)
        and all(row.get("body_hash_included") is False for row in question_rows)
        and all(row.get("packet_content_included") is False for row in question_rows)
    )
    no_question_text_validation_passed = bool(
        inputs_ready
        and all(row.get("question_text_included") is False for row in rating_rows)
        and all(row.get("draft_question_text_included") is False for row in rating_rows)
        and all(row.get("question_text_included") is False for row in question_rows)
        and all(row.get("draft_question_text_included") is False for row in question_rows)
        and clr15_guard.get("question_text_absent") is True
        and clr15_guard.get("draft_question_text_absent") is True
    )
    no_touch_contract = clr15._no_touch_contract()  # type: ignore[attr-defined]
    no_touch_validation_passed = bool(
        inputs_ready
        and all(value is False for value in no_touch_contract.values())
        and all(value is False for value in public_contract_flags().values())
        and clr17_receipt.get("p6_limited_human_readfeel_start_allowed") is False
        and clr17_receipt.get("p8_start_allowed") is False
        and clr17_receipt.get("release_allowed") is False
        and clr15_guard.get("p6_limited_human_readfeel_start_allowed") is False
        and clr15_guard.get("p8_start_allowed") is False
        and clr15_guard.get("release_allowed") is False
    )
    summary_ready = bool(
        inputs_ready
        and counts_ready
        and not open_execution_blockers
        and no_body_leak_validation_passed
        and no_question_text_validation_passed
        and no_touch_validation_passed
        and clr17_receipt.get("disposal_verified") is True
    )
    decision_separation_allowed = bool(summary_ready or (inputs_ready and counts_ready))
    reason_refs = [P7_R54_CLR18_READY_REASON_REF] if summary_ready else dedupe_identifiers(
        [P7_R54_CLR18_BLOCKED_REASON_REF, *open_execution_blockers],
        limit=120,
        max_length=180,
    )
    material = {
        "schema_version": P7_R54_CLR18_BODYFREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_CLR_STEP,
        "scope": P7_R54_CLR_SCOPE,
        "policy_kind": P7_R54_CLR_POLICY_KIND,
        "policy_section": P7_R54_CLR18_STEP_REF,
        "operation_step_ref": P7_R54_CLR18_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_clr18_bodyfree_post_review_summary", max_length=220),
        "review_session_id": _safe_review_session_id(clr17_receipt.get("review_session_id") or clr15_guard.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "clr17_schema_version": clr17.P7_R54_CLR17_SCHEMA_VERSION,
        "clr17_material_ref": clean_identifier(clr17_receipt.get("material_id"), default="p7_r54_clr17_purge_disposal_receipt", max_length=220),
        "clr17_next_required_step": clean_identifier(clr17_receipt.get("next_required_step"), default="", max_length=180),
        "clr17_purge_disposal_receipt_status": clean_identifier(clr17_receipt.get("purge_disposal_receipt_status"), default=clr17.P7_R54_CLR17_DISPOSAL_BLOCKED_STATUS_REF, max_length=180),
        "clr17_bodyfree_summary_allowed_next": clr17_receipt.get("body_free_post_review_summary_allowed_next") is True,
        "clr15_schema_version": clr15.P7_R54_CLR15_SCHEMA_VERSION,
        "clr15_material_ref": clean_identifier(clr15_guard.get("material_id"), default="p7_r54_clr15_rating_question_consistency_guard", max_length=220),
        "clr15_next_required_step": clean_identifier(clr15_guard.get("next_required_step"), default="", max_length=180),
        "clr15_rating_question_consistency_guard_status": clean_identifier(clr15_guard.get("rating_question_consistency_guard_status"), default=clr15.P7_R54_CLR15_CONSISTENCY_GUARD_BLOCKED_STATUS_REF, max_length=180),
        "clr15_consistency_guard_passed": clr15_guard.get("rating_question_consistency_guard_passed") is True,
        "existing_op18_helper_ref": "build_p7_r54_op18_bodyfree_post_review_summary",
        "existing_op18_schema_version": r54op.P7_R54_OPERATION_BODYFREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION,
        "existing_op18_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op18_current_refs_are_historical_here": True,
        "existing_op18_reused_as_actual_summary_basis": False,
        "existing_op18_reused_as_actual_post_review_summary_basis": False,
        "existing_op18_structural_contract_reused": True,
        "existing_ev16_schema_version": r54ev.P7_R54_EV_BODYFREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION,
        "existing_ev16_current_refs": dict(r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "existing_ev16_current_refs_are_historical_here": True,
        "existing_ev16_reused_as_actual_summary_basis": False,
        "existing_ev16_reused_as_actual_post_review_summary_basis": False,
        "existing_ev16_structural_contract_reused": True,
        "required_case_count": clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "reviewed_case_count": len(rating_rows) if inputs_ready else 0,
        "rating_row_count": len(rating_rows) if inputs_ready else 0,
        "question_observation_row_count": len(question_rows) if inputs_ready else 0,
        "bodyfree_post_review_summary_status": P7_R54_CLR18_SUMMARY_READY_STATUS_REF if summary_ready else P7_R54_CLR18_SUMMARY_BLOCKED_STATUS_REF,
        "bodyfree_post_review_summary_ref": P7_R54_CLR18_SUMMARY_REF if summary_ready else "r54_clr18_bodyfree_post_review_summary_not_ready",
        "bodyfree_post_review_summary_policy_ref": P7_R54_CLR18_SUMMARY_POLICY_REF,
        "bodyfree_post_review_summary_reason_refs": reason_refs,
        "execution_blocker_ids": [] if summary_ready else open_execution_blockers,
        "open_execution_blocker_ids": [] if summary_ready else open_execution_blockers,
        "summary_blocker_ids": [] if summary_ready else open_execution_blockers,
        "summary_blocker_count": 0 if summary_ready else len(open_execution_blockers),
        "verdict_counts": dict(verdict_counts),
        "overall_read_feeling_counts": dict(overall_read_feeling_counts),
        "axis_score_averages": dict(axis_score_averages),
        "rating_axis_target_thresholds": dict(clr13.P7_R54_CLR12_RATING_AXIS_TARGET_THRESHOLDS),
        "below_target_axis_refs": below_target_axis_refs,
        "below_target_axis_count": len(below_target_axis_refs),
        "readfeel_blocker_counts": dict(readfeel_blocker_counts),
        "open_readfeel_blocker_count": sum(int(value or 0) for value in readfeel_blocker_counts.values()),
        "execution_blocker_counts": dict(execution_blocker_counts),
        "open_execution_blocker_count": sum(int(value or 0) for value in execution_blocker_counts.values()) if inputs_ready else len(open_execution_blockers),
        "primary_class_counts": dict(primary_class_counts),
        "ambiguity_kind_counts": dict(ambiguity_kind_counts),
        "one_question_fit_counts": dict(one_question_fit_counts),
        "repair_required_counts": dict(repair_required_counts),
        "plan_candidate_flag_counts": dict(plan_candidate_flag_counts),
        "p8_material_candidate_row_count": sum(int(value or 0) for value in p8_counts.values()),
        "p8_material_candidate_allowed_primary_class_counts": dict(p8_counts),
        "not_question_repair_required_count": not_question_repair_count,
        "insufficient_material_execution_blocker_count": insufficient_material_count,
        "consistency_issue_count": int(clr15_guard.get("consistency_issue_count") or 0) if inputs_ready else 0,
        "consistency_issue_direction_counts": dict(safe_mapping(clr15_guard.get("consistency_issue_direction_counts"))) if inputs_ready else {},
        "disposal_verified": clr17_receipt.get("disposal_verified") is True if inputs_ready else False,
        "body_removed": clr17_receipt.get("body_removed") is True if inputs_ready else False,
        "reviewer_notes_removed": clr17_receipt.get("reviewer_notes_removed") is True if inputs_ready else False,
        "temporary_form_removed": clr17_receipt.get("temporary_form_removed") is True if inputs_ready else False,
        "local_packet_exported": clr17_receipt.get("local_packet_exported") is True,
        "content_hash_of_body_stored": clr17_receipt.get("content_hash_of_body_stored") is True,
        "all_required_review_counts_present": counts_ready,
        "all_required_summary_inputs_ready": inputs_ready,
        "no_body_leak_validation_passed": no_body_leak_validation_passed,
        "no_question_text_validation_passed": no_question_text_validation_passed,
        "no_touch_validation_passed": no_touch_validation_passed,
        "p5_decision_candidate_separation_allowed_next": decision_separation_allowed,
        "actual_rating_rows_materialized_here": bool(clr15_guard.get("actual_rating_rows_materialized_here") is True) if inputs_ready else False,
        "actual_blocker_rows_materialized_here": bool(clr15_guard.get("actual_blocker_rows_materialized_here") is True) if inputs_ready else False,
        "actual_question_need_observation_rows_materialized_here": bool(clr15_guard.get("actual_question_need_observation_rows_materialized_here") is True) if inputs_ready else False,
        "actual_disposal_receipt_materialized_here": bool(clr17_receipt.get("actual_disposal_receipt_materialized_here") is True) if inputs_ready else False,
        "actual_review_evidence_complete": False,
        "human_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        **_current_ref_fields(),
        "implemented_steps": list(P7_R54_CLR18_IMPLEMENTED_STEPS if decision_separation_allowed else tuple(clr17_receipt.get("implemented_steps") or clr17.P7_R54_CLR17_IMPLEMENTED_STEPS)),
        "not_yet_implemented_steps": list(P7_R54_CLR18_NOT_YET_IMPLEMENTED_STEPS if decision_separation_allowed else tuple(clr17_receipt.get("not_yet_implemented_steps") or clr17.P7_R54_CLR17_NOT_YET_IMPLEMENTED_STEPS)),
        "first_next_work_ref": P7_R54_CLR19_NEXT_WORK_AFTER_CLR18_REF if decision_separation_allowed else P7_R54_CLR18_STEP_REF,
        "next_required_step": P7_R54_CLR19_STEP_REF if decision_separation_allowed else P7_R54_CLR18_BLOCKED_NEXT_REQUIRED_STEP_REF,
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
    material["actual_rating_rows_materialized_here"] = bool(clr15_guard.get("actual_rating_rows_materialized_here") is True) if inputs_ready else False
    material["actual_blocker_rows_materialized_here"] = bool(clr15_guard.get("actual_blocker_rows_materialized_here") is True) if inputs_ready else False
    material["actual_question_need_observation_rows_materialized_here"] = bool(clr15_guard.get("actual_question_need_observation_rows_materialized_here") is True) if inputs_ready else False
    material["actual_disposal_receipt_materialized_here"] = bool(clr17_receipt.get("actual_disposal_receipt_materialized_here") is True) if inputs_ready else False
    material["disposal_verified"] = clr17_receipt.get("disposal_verified") is True if inputs_ready else False
    assert_p7_r54_clr18_bodyfree_post_review_summary_contract(material)
    return material


def assert_p7_r54_clr18_bodyfree_post_review_summary_contract(data: Mapping[str, Any]) -> bool:
    material = safe_mapping(data)
    _assert_required_fields(material, required=P7_R54_CLR18_BODYFREE_POST_REVIEW_SUMMARY_REQUIRED_FIELD_REFS, source="P7-R54-CLR18")
    _assert_common_base(
        material,
        schema_version=P7_R54_CLR18_BODYFREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION,
        policy_section=P7_R54_CLR18_STEP_REF,
        source="P7-R54-CLR18",
        allowed_true_false_flags=P7_R54_CLR18_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    if safe_mapping(material.get("existing_op18_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("P7-R54-CLR18 existing OP18 refs changed")
    if safe_mapping(material.get("existing_ev16_current_refs")) != r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("P7-R54-CLR18 existing EV16 refs changed")
    for key in (
        "existing_op18_current_refs_are_historical_here",
        "existing_op18_structural_contract_reused",
        "existing_ev16_current_refs_are_historical_here",
        "existing_ev16_structural_contract_reused",
        "human_review_completion_claim_blocked_here",
        "actual_human_review_completion_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if material.get(key) is not True:
            raise ValueError(f"P7-R54-CLR18 must keep {key}=True")
    for key in (
        "existing_op18_reused_as_actual_summary_basis",
        "existing_op18_reused_as_actual_post_review_summary_basis",
        "existing_ev16_reused_as_actual_summary_basis",
        "existing_ev16_reused_as_actual_post_review_summary_basis",
        "local_packet_exported",
        "content_hash_of_body_stored",
        "actual_review_evidence_complete",
    ):
        if material.get(key) is not False:
            raise ValueError(f"P7-R54-CLR18 must keep {key}=False")
    if material.get("bodyfree_post_review_summary_status") not in P7_R54_CLR18_ALLOWED_SUMMARY_STATUS_REFS:
        raise ValueError("P7-R54-CLR18 summary status changed")
    p8_counts = safe_mapping(material.get("p8_material_candidate_allowed_primary_class_counts"))
    if material.get("p8_material_candidate_row_count") != sum(int(value or 0) for value in p8_counts.values()):
        raise ValueError("P7-R54-CLR18 P8 material candidate row count mismatch")
    ready = material.get("bodyfree_post_review_summary_status") == P7_R54_CLR18_SUMMARY_READY_STATUS_REF
    decision_allowed = material.get("p5_decision_candidate_separation_allowed_next") is True
    if ready and not decision_allowed:
        raise ValueError("P7-R54-CLR18 ready summary must allow decision separation")
    if ready:
        if material.get("bodyfree_post_review_summary_ref") != P7_R54_CLR18_SUMMARY_REF:
            raise ValueError("P7-R54-CLR18 summary ref changed")
        if material.get("bodyfree_post_review_summary_reason_refs") != [P7_R54_CLR18_READY_REASON_REF]:
            raise ValueError("P7-R54-CLR18 ready reason refs changed")
        if material.get("required_case_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-CLR18 required case count changed")
        if material.get("reviewed_case_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-CLR18 ready reviewed count changed")
        if material.get("rating_row_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-CLR18 ready rating count changed")
        if material.get("question_observation_row_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-CLR18 ready question count changed")
        for true_key in (
            "all_required_review_counts_present",
            "all_required_summary_inputs_ready",
            "disposal_verified",
            "body_removed",
            "reviewer_notes_removed",
            "temporary_form_removed",
            "no_body_leak_validation_passed",
            "no_question_text_validation_passed",
            "no_touch_validation_passed",
            "actual_rating_rows_materialized_here",
            "actual_blocker_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
        ):
            if material.get(true_key) is not True:
                raise ValueError(f"P7-R54-CLR18 ready summary must keep {true_key}=True")
        if material.get("summary_blocker_count") != 0 or material.get("open_execution_blocker_ids") != []:
            raise ValueError("P7-R54-CLR18 ready summary must not carry blockers")
        if tuple(material.get("implemented_steps") or ()) != P7_R54_CLR18_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR18 implemented steps changed")
        if tuple(material.get("not_yet_implemented_steps") or ()) != P7_R54_CLR18_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR18 not-yet steps changed")
        if material.get("next_required_step") != P7_R54_CLR19_STEP_REF:
            raise ValueError("P7-R54-CLR18 ready summary must point to CLR19")
    else:
        if material.get("bodyfree_post_review_summary_status") != P7_R54_CLR18_SUMMARY_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-CLR18 blocked status changed")
        if not material.get("summary_blocker_ids"):
            raise ValueError("P7-R54-CLR18 blocked summary must carry blockers")
        if decision_allowed:
            if material.get("next_required_step") != P7_R54_CLR19_STEP_REF:
                raise ValueError("P7-R54-CLR18 classified blocked summary must point to CLR19")
            if tuple(material.get("implemented_steps") or ()) != P7_R54_CLR18_IMPLEMENTED_STEPS:
                raise ValueError("P7-R54-CLR18 classified blocked summary implemented steps changed")
        elif material.get("next_required_step") != P7_R54_CLR18_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-CLR18 unclassified blocked summary must point to repair")
    return True


def _p5_repair_reason_refs(summary: Mapping[str, Any]) -> list[str]:
    data = safe_mapping(summary)
    reasons: list[str] = []
    verdict_counts = safe_mapping(data.get("verdict_counts"))
    for verdict_ref in ("RED", "REPAIR_REQUIRED", "YELLOW"):
        if int(verdict_counts.get(verdict_ref) or 0) > 0:
            reasons.append(f"{verdict_ref.lower()}_verdict_present")
    readfeel_counts = safe_mapping(data.get("readfeel_blocker_counts"))
    for blocker_id in clr13.P7_R54_CLR13_READFEEL_BLOCKER_ID_REFS:
        if int(readfeel_counts.get(blocker_id) or 0) > 0:
            reasons.append(f"readfeel_blocker:{blocker_id}")
    for axis in data.get("below_target_axis_refs") or []:
        reasons.append(f"axis_below_target:{clean_identifier(axis, max_length=120)}")
    primary_counts = safe_mapping(data.get("primary_class_counts"))
    for primary_class_ref in P7_R54_CLR19_NOT_QUESTION_REPAIR_PRIMARY_CLASS_REFS:
        if int(primary_counts.get(primary_class_ref) or 0) > 0:
            reasons.append(f"not_question_repair_primary_class:{primary_class_ref}")
    repair_counts = safe_mapping(data.get("repair_required_counts"))
    for repair_ref in P7_R54_CLR19_REPAIR_REQUIRED_REFS:
        if int(repair_counts.get(repair_ref) or 0) > 0:
            reasons.append(f"repair_required_ref:{repair_ref}")
    if int(data.get("not_question_repair_required_count") or 0) > 0:
        reasons.append("not_question_repair_required_row_present")
    return dedupe_identifiers(reasons, limit=120, max_length=180)


def _p5_inconclusive_reason_refs(summary: Mapping[str, Any]) -> list[str]:
    data = safe_mapping(summary)
    reasons: list[str] = []
    if data.get("bodyfree_post_review_summary_status") != P7_R54_CLR18_SUMMARY_READY_STATUS_REF:
        reasons.append("clr18_bodyfree_post_review_summary_not_ready")
    if int(data.get("open_execution_blocker_count") or 0) > 0:
        reasons.append("open_execution_blocker_present")
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
    if int(data.get("reviewed_case_count") or 0) != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        reasons.append("reviewed_case_count_not_24")
    if int(data.get("rating_row_count") or 0) != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        reasons.append("rating_row_count_not_24")
    if int(data.get("question_observation_row_count") or 0) != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        reasons.append("question_observation_row_count_not_24")
    return dedupe_identifiers(reasons, limit=120, max_length=180)


def _confirmed_candidate_conditions_met(summary: Mapping[str, Any]) -> bool:
    data = safe_mapping(summary)
    verdict_counts = safe_mapping(data.get("verdict_counts"))
    return bool(
        data.get("bodyfree_post_review_summary_status") == P7_R54_CLR18_SUMMARY_READY_STATUS_REF
        and int(data.get("reviewed_case_count") or 0) == clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and int(data.get("rating_row_count") or 0) == clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and int(data.get("question_observation_row_count") or 0) == clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and int(verdict_counts.get("PASS") or 0) == clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and int(verdict_counts.get("YELLOW") or 0) == 0
        and int(verdict_counts.get("REPAIR_REQUIRED") or 0) == 0
        and int(verdict_counts.get("RED") or 0) == 0
        and int(verdict_counts.get("NOT_REVIEWABLE") or 0) == 0
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
        and not _p5_repair_reason_refs(data)
        and not _p5_inconclusive_reason_refs(data)
    )


def _p4_current_only_issue_refs(summary: Mapping[str, Any]) -> list[str]:
    repair_counts = safe_mapping(summary.get("repair_required_counts"))
    refs: list[str] = []
    for repair_ref in P7_R54_CLR19_P4_CURRENT_ONLY_REPAIR_REFS:
        if int(repair_counts.get(repair_ref) or 0) > 0:
            refs.append(repair_ref)
    return dedupe_identifiers(refs, limit=24, max_length=180)


def build_p7_r54_clr19_p5_decision_candidate_separation(
    *,
    bodyfree_post_review_summary: Mapping[str, Any] | None = None,
    p4_current_only_surface_issue_refs: Sequence[Any] | None = None,
    material_id: Any = "p7_r54_clr19_p5_decision_candidate_separation",
) -> dict[str, Any]:
    """Separate P5 decision candidates without final/start/release promotion."""
    summary = safe_mapping(bodyfree_post_review_summary)
    if summary:
        assert_p7_r54_clr18_bodyfree_post_review_summary_contract(summary)
    summary_ready = bool(
        summary.get("p5_decision_candidate_separation_allowed_next") is True
        and summary.get("next_required_step") == P7_R54_CLR19_STEP_REF
    )
    p4_issue_refs = dedupe_identifiers([*(p4_current_only_surface_issue_refs or []), *_p4_current_only_issue_refs(summary)], limit=24, max_length=180)
    repair_reasons = _p5_repair_reason_refs(summary) if summary_ready else []
    inconclusive_reasons = _p5_inconclusive_reason_refs(summary) if summary_ready else ["clr18_bodyfree_post_review_summary_not_ready"]
    confirmed_conditions_met = bool(summary_ready and not p4_issue_refs and _confirmed_candidate_conditions_met(summary))
    if not summary_ready:
        decision = P7_R54_CLR19_INCONCLUSIVE_REF
    elif summary.get("no_body_leak_validation_passed") is not True or summary.get("no_question_text_validation_passed") is not True:
        decision = P7_R54_CLR19_BLOCKED_BODY_LEAK_OR_QUESTION_TEXT_REF
    elif summary.get("no_touch_validation_passed") is not True:
        decision = P7_R54_CLR19_BLOCKED_NO_TOUCH_VIOLATION_REF
    elif summary.get("disposal_verified") is not True:
        decision = P7_R54_CLR19_BLOCKED_DISPOSAL_REF
    elif p4_issue_refs:
        decision = P7_R54_CLR19_P4_R12_TARGETED_REPAIR_REF
    elif repair_reasons:
        decision = P7_R54_CLR19_P5_REPAIR_RETURN_REF
    elif confirmed_conditions_met:
        decision = P7_R54_CLR19_P5_CONFIRMED_CANDIDATE_REF
    else:
        decision = P7_R54_CLR19_INCONCLUSIVE_REF
        if not inconclusive_reasons:
            inconclusive_reasons = ["p5_confirmed_candidate_conditions_not_all_met"]
    separation_ready = bool(summary_ready)
    if decision == P7_R54_CLR19_P5_CONFIRMED_CANDIDATE_REF:
        decision_reason_refs = ["p5_confirmed_candidate_conditions_met_bodyfree"]
        next_step = P7_R54_CLR20_STEP_REF
    elif decision == P7_R54_CLR19_P4_R12_TARGETED_REPAIR_REF:
        decision_reason_refs = ["current_only_surface_issue_requires_p4_r12_targeted_repair"]
        next_step = P7_R54_CLR19_P4_R12_REPAIR_NEXT_REQUIRED_STEP_REF
    elif decision == P7_R54_CLR19_P5_REPAIR_RETURN_REF:
        decision_reason_refs = ["p5_repair_return_required_by_bodyfree_review_summary"]
        next_step = P7_R54_CLR19_P5_REPAIR_NEXT_REQUIRED_STEP_REF
    elif decision == P7_R54_CLR19_BLOCKED_BODY_LEAK_OR_QUESTION_TEXT_REF:
        decision_reason_refs = ["body_leak_or_question_text_validation_failed"]
        next_step = P7_R54_CLR19_BLOCKED_NEXT_REQUIRED_STEP_REF
    elif decision == P7_R54_CLR19_BLOCKED_NO_TOUCH_VIOLATION_REF:
        decision_reason_refs = ["no_touch_validation_failed"]
        next_step = P7_R54_CLR19_BLOCKED_NEXT_REQUIRED_STEP_REF
    elif decision == P7_R54_CLR19_BLOCKED_DISPOSAL_REF:
        decision_reason_refs = ["disposal_receipt_not_verified"]
        next_step = P7_R54_CLR19_BLOCKED_NEXT_REQUIRED_STEP_REF
    elif separation_ready:
        decision_reason_refs = ["r54_operation_inconclusive_by_bodyfree_review_summary"]
        next_step = P7_R54_CLR19_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF
    else:
        decision_reason_refs = ["p5_decision_candidate_separation_blocked_by_clr18_summary"]
        next_step = P7_R54_CLR19_BLOCKED_NEXT_REQUIRED_STEP_REF
    material = {
        "schema_version": P7_R54_CLR19_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_CLR_STEP,
        "scope": P7_R54_CLR_SCOPE,
        "policy_kind": P7_R54_CLR_POLICY_KIND,
        "policy_section": P7_R54_CLR19_STEP_REF,
        "operation_step_ref": P7_R54_CLR19_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_clr19_p5_decision_candidate_separation", max_length=220),
        "review_session_id": _safe_review_session_id(summary.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "clr18_schema_version": P7_R54_CLR18_BODYFREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION,
        "clr18_material_ref": clean_identifier(summary.get("material_id"), default="p7_r54_clr18_bodyfree_post_review_summary", max_length=220),
        "clr18_next_required_step": clean_identifier(summary.get("next_required_step"), default="", max_length=180),
        "clr18_bodyfree_post_review_summary_status": clean_identifier(summary.get("bodyfree_post_review_summary_status"), default=P7_R54_CLR18_SUMMARY_BLOCKED_STATUS_REF, max_length=180),
        "clr18_decision_separation_allowed_next": summary_ready,
        "existing_op19_helper_ref": "build_p7_r54_op19_p5_decision_candidate_separation",
        "existing_op19_schema_version": r54op.P7_R54_OPERATION_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION,
        "existing_op19_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op19_current_refs_are_historical_here": True,
        "existing_op19_reused_as_actual_decision_basis": False,
        "existing_op19_reused_as_actual_decision_candidate_basis": False,
        "existing_op19_structural_contract_reused": True,
        "existing_ev17_schema_version": r54ev.P7_R54_EV_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION,
        "existing_ev17_current_refs": dict(r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "existing_ev17_current_refs_are_historical_here": True,
        "existing_ev17_reused_as_actual_decision_basis": False,
        "existing_ev17_reused_as_actual_decision_candidate_basis": False,
        "existing_ev17_structural_contract_reused": True,
        "required_case_count": clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "reviewed_case_count": int(summary.get("reviewed_case_count") or 0),
        "rating_row_count": int(summary.get("rating_row_count") or 0),
        "question_observation_row_count": int(summary.get("question_observation_row_count") or 0),
        "decision_candidate_separation_status": P7_R54_CLR19_DECISION_SEPARATION_READY_STATUS_REF if separation_ready else P7_R54_CLR19_DECISION_SEPARATION_BLOCKED_STATUS_REF,
        "decision_candidate_separation_ref": P7_R54_CLR19_DECISION_SEPARATION_REF if separation_ready else "r54_clr19_p5_decision_candidate_separation_not_ready",
        "decision_candidate_separation_policy_ref": P7_R54_CLR19_DECISION_SEPARATION_POLICY_REF,
        "decision_candidate_separation_reason_refs": ["p5_decision_candidate_separation_ready_bodyfree"] if separation_ready else ["clr18_summary_not_ready_for_p5_decision_candidate_separation"],
        "decision_candidate_allowed_refs": list(P7_R54_CLR19_DECISION_CANDIDATE_REFS),
        "p5_decision_candidate_ref": decision,
        "p5_decision_candidate_materialized_here": separation_ready,
        "p5_decision_candidate_reason_refs": decision_reason_refs,
        "p5_decision_repair_reason_refs": repair_reasons,
        "p5_decision_inconclusive_reason_refs": inconclusive_reasons if decision == P7_R54_CLR19_INCONCLUSIVE_REF else [],
        "p4_current_only_surface_issue_refs": p4_issue_refs,
        "p5_confirmed_candidate_conditions_met": confirmed_conditions_met,
        "p5_repair_return_required": decision == P7_R54_CLR19_P5_REPAIR_RETURN_REF,
        "p4_r12_targeted_current_only_surface_repair_required": decision == P7_R54_CLR19_P4_R12_TARGETED_REPAIR_REF,
        "r54_operation_inconclusive_required": decision == P7_R54_CLR19_INCONCLUSIVE_REF,
        "r54_operation_blocked_preflight_required": decision == P7_R54_CLR19_BLOCKED_PREFLIGHT_REF,
        "r54_operation_blocked_disposal_required": decision == P7_R54_CLR19_BLOCKED_DISPOSAL_REF,
        "r54_operation_blocked_body_leak_or_question_text_required": decision == P7_R54_CLR19_BLOCKED_BODY_LEAK_OR_QUESTION_TEXT_REF,
        "r54_operation_blocked_no_touch_violation_required": decision == P7_R54_CLR19_BLOCKED_NO_TOUCH_VIOLATION_REF,
        "verdict_counts": dict(safe_mapping(summary.get("verdict_counts"))),
        "overall_read_feeling_counts": dict(safe_mapping(summary.get("overall_read_feeling_counts"))),
        "axis_score_averages": dict(safe_mapping(summary.get("axis_score_averages"))),
        "rating_axis_target_thresholds": dict(clr13.P7_R54_CLR12_RATING_AXIS_TARGET_THRESHOLDS),
        "below_target_axis_refs": list(summary.get("below_target_axis_refs") or []),
        "open_readfeel_blocker_count": int(summary.get("open_readfeel_blocker_count") or 0),
        "open_execution_blocker_count": int(summary.get("open_execution_blocker_count") or 0),
        "primary_class_counts": dict(safe_mapping(summary.get("primary_class_counts"))),
        "repair_required_counts": dict(safe_mapping(summary.get("repair_required_counts"))),
        "p8_material_candidate_row_count": int(summary.get("p8_material_candidate_row_count") or 0),
        "p8_material_candidate_allowed_primary_class_counts": dict(safe_mapping(summary.get("p8_material_candidate_allowed_primary_class_counts"))),
        "not_question_repair_required_count": int(summary.get("not_question_repair_required_count") or 0),
        "insufficient_material_execution_blocker_count": int(summary.get("insufficient_material_execution_blocker_count") or 0),
        "disposal_verified": summary.get("disposal_verified") is True,
        "body_removed": summary.get("body_removed") is True,
        "reviewer_notes_removed": summary.get("reviewer_notes_removed") is True,
        "temporary_form_removed": summary.get("temporary_form_removed") is True,
        "local_packet_exported": summary.get("local_packet_exported") is True,
        "content_hash_of_body_stored": summary.get("content_hash_of_body_stored") is True,
        "no_body_leak_validation_passed": summary.get("no_body_leak_validation_passed") is True,
        "no_question_text_validation_passed": summary.get("no_question_text_validation_passed") is True,
        "no_touch_validation_passed": summary.get("no_touch_validation_passed") is True,
        "p5_human_blind_qa_confirmed_candidate": decision == P7_R54_CLR19_P5_CONFIRMED_CANDIDATE_REF,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "p5_final_confirmation_blocked_here": True,
        "p6_start_blocked_here": True,
        "p8_start_blocked_here": True,
        "release_blocked_here": True,
        "actual_review_evidence_complete": False,
        "actual_rating_rows_materialized_here": bool(summary.get("actual_rating_rows_materialized_here") is True),
        "actual_blocker_rows_materialized_here": bool(summary.get("actual_blocker_rows_materialized_here") is True),
        "actual_question_need_observation_rows_materialized_here": bool(summary.get("actual_question_need_observation_rows_materialized_here") is True),
        "actual_disposal_receipt_materialized_here": bool(summary.get("actual_disposal_receipt_materialized_here") is True),
        **_current_ref_fields(),
        "implemented_steps": list(P7_R54_CLR19_IMPLEMENTED_STEPS if separation_ready else tuple(summary.get("implemented_steps") or P7_R54_CLR18_IMPLEMENTED_STEPS)),
        "not_yet_implemented_steps": list(P7_R54_CLR19_NOT_YET_IMPLEMENTED_STEPS if separation_ready else tuple(summary.get("not_yet_implemented_steps") or P7_R54_CLR18_NOT_YET_IMPLEMENTED_STEPS)),
        "first_next_work_ref": P7_R54_CLR19_NEXT_WORK_AFTER_CLR19_REF if separation_ready else P7_R54_CLR19_NEXT_WORK_AFTER_CLR18_REF,
        "next_required_step": next_step,
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
            "p5_human_blind_qa_confirmed_candidate",
        ),
    }
    material["actual_rating_rows_materialized_here"] = bool(summary.get("actual_rating_rows_materialized_here") is True)
    material["actual_blocker_rows_materialized_here"] = bool(summary.get("actual_blocker_rows_materialized_here") is True)
    material["actual_question_need_observation_rows_materialized_here"] = bool(summary.get("actual_question_need_observation_rows_materialized_here") is True)
    material["actual_disposal_receipt_materialized_here"] = bool(summary.get("actual_disposal_receipt_materialized_here") is True)
    material["disposal_verified"] = summary.get("disposal_verified") is True
    material["p5_human_blind_qa_confirmed_candidate"] = decision == P7_R54_CLR19_P5_CONFIRMED_CANDIDATE_REF
    assert_p7_r54_clr19_p5_decision_candidate_separation_contract(material)
    return material


def assert_p7_r54_clr19_p5_decision_candidate_separation_contract(data: Mapping[str, Any]) -> bool:
    material = safe_mapping(data)
    _assert_required_fields(material, required=P7_R54_CLR19_P5_DECISION_CANDIDATE_SEPARATION_REQUIRED_FIELD_REFS, source="P7-R54-CLR19")
    _assert_common_base(
        material,
        schema_version=P7_R54_CLR19_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION,
        policy_section=P7_R54_CLR19_STEP_REF,
        source="P7-R54-CLR19",
        allowed_true_false_flags=P7_R54_CLR19_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    if safe_mapping(material.get("existing_op19_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("P7-R54-CLR19 existing OP19 refs changed")
    if safe_mapping(material.get("existing_ev17_current_refs")) != r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("P7-R54-CLR19 existing EV17 refs changed")
    for key in (
        "existing_op19_current_refs_are_historical_here",
        "existing_op19_structural_contract_reused",
        "existing_ev17_current_refs_are_historical_here",
        "existing_ev17_structural_contract_reused",
        "p5_final_confirmation_blocked_here",
        "p6_start_blocked_here",
        "p8_start_blocked_here",
        "release_blocked_here",
    ):
        if material.get(key) is not True:
            raise ValueError(f"P7-R54-CLR19 must keep {key}=True")
    for key in (
        "existing_op19_reused_as_actual_decision_basis",
        "existing_op19_reused_as_actual_decision_candidate_basis",
        "existing_ev17_reused_as_actual_decision_basis",
        "existing_ev17_reused_as_actual_decision_candidate_basis",
        "local_packet_exported",
        "content_hash_of_body_stored",
        "actual_review_evidence_complete",
        "p5_human_blind_qa_confirmed_final",
        "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed",
        "release_allowed",
    ):
        if material.get(key) is not False:
            raise ValueError(f"P7-R54-CLR19 must keep {key}=False")
    if material.get("p5_decision_candidate_ref") not in P7_R54_CLR19_DECISION_CANDIDATE_REFS:
        raise ValueError("P7-R54-CLR19 decision candidate outside allowed refs")
    if material.get("decision_candidate_separation_status") not in P7_R54_CLR19_ALLOWED_DECISION_SEPARATION_STATUS_REFS:
        raise ValueError("P7-R54-CLR19 separation status changed")
    p8_counts = safe_mapping(material.get("p8_material_candidate_allowed_primary_class_counts"))
    if material.get("p8_material_candidate_row_count") != sum(int(value or 0) for value in p8_counts.values()):
        raise ValueError("P7-R54-CLR19 P8 material candidate row count mismatch")
    separation_ready = material.get("decision_candidate_separation_status") == P7_R54_CLR19_DECISION_SEPARATION_READY_STATUS_REF
    if material.get("p5_decision_candidate_materialized_here") is not separation_ready:
        raise ValueError("P7-R54-CLR19 materialized flag must match readiness")
    if separation_ready:
        if material.get("decision_candidate_separation_ref") != P7_R54_CLR19_DECISION_SEPARATION_REF:
            raise ValueError("P7-R54-CLR19 separation ref changed")
        if material.get("decision_candidate_separation_reason_refs") != ["p5_decision_candidate_separation_ready_bodyfree"]:
            raise ValueError("P7-R54-CLR19 ready reason refs changed")
        if material.get("required_case_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-CLR19 required case count changed")
        if material.get("rating_row_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-CLR19 ready rating count changed")
        if material.get("question_observation_row_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-CLR19 ready question count changed")
        if tuple(material.get("implemented_steps") or ()) != P7_R54_CLR19_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR19 implemented steps changed")
        if tuple(material.get("not_yet_implemented_steps") or ()) != P7_R54_CLR19_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR19 not-yet steps changed")
        if material.get("p5_decision_candidate_ref") == P7_R54_CLR19_P5_CONFIRMED_CANDIDATE_REF:
            if material.get("p5_human_blind_qa_confirmed_candidate") is not True or material.get("p5_confirmed_candidate_conditions_met") is not True:
                raise ValueError("P7-R54-CLR19 P5 confirmed candidate must be condition-backed")
            if material.get("next_required_step") != P7_R54_CLR20_STEP_REF:
                raise ValueError("P7-R54-CLR19 P5 confirmed candidate must point to CLR20")
        else:
            if material.get("p5_human_blind_qa_confirmed_candidate") is not False:
                raise ValueError("P7-R54-CLR19 non-confirmed decision must not set P5 candidate flag")
            if material.get("p5_decision_candidate_ref") == P7_R54_CLR19_P5_REPAIR_RETURN_REF and material.get("next_required_step") != P7_R54_CLR19_P5_REPAIR_NEXT_REQUIRED_STEP_REF:
                raise ValueError("P7-R54-CLR19 P5 repair next step changed")
            if material.get("p5_decision_candidate_ref") == P7_R54_CLR19_P4_R12_TARGETED_REPAIR_REF and material.get("next_required_step") != P7_R54_CLR19_P4_R12_REPAIR_NEXT_REQUIRED_STEP_REF:
                raise ValueError("P7-R54-CLR19 P4-R12 next step changed")
            if material.get("p5_decision_candidate_ref") == P7_R54_CLR19_INCONCLUSIVE_REF and material.get("next_required_step") != P7_R54_CLR19_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF:
                raise ValueError("P7-R54-CLR19 inconclusive next step changed")
    else:
        if material.get("decision_candidate_separation_status") != P7_R54_CLR19_DECISION_SEPARATION_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-CLR19 blocked status changed")
        if material.get("p5_decision_candidate_ref") != P7_R54_CLR19_INCONCLUSIVE_REF:
            raise ValueError("P7-R54-CLR19 blocked decision must be inconclusive")
        if material.get("next_required_step") != P7_R54_CLR19_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-CLR19 blocked separation must point to repair")
    return True


build_p7_r54_current_snapshot_local_run_clr18_bodyfree_post_review_summary = build_p7_r54_clr18_bodyfree_post_review_summary
assert_p7_r54_current_snapshot_local_run_clr18_bodyfree_post_review_summary_contract = assert_p7_r54_clr18_bodyfree_post_review_summary_contract
build_p7_r54_current_snapshot_bodyfree_post_review_summary = build_p7_r54_clr18_bodyfree_post_review_summary
assert_p7_r54_current_snapshot_bodyfree_post_review_summary_contract = assert_p7_r54_clr18_bodyfree_post_review_summary_contract
build_p7_r54_current_snapshot_local_run_clr19_p5_decision_candidate_separation = build_p7_r54_clr19_p5_decision_candidate_separation
assert_p7_r54_current_snapshot_local_run_clr19_p5_decision_candidate_separation_contract = assert_p7_r54_clr19_p5_decision_candidate_separation_contract
build_p7_r54_current_snapshot_p5_decision_candidate_separation_bodyfree = build_p7_r54_clr19_p5_decision_candidate_separation
assert_p7_r54_current_snapshot_p5_decision_candidate_separation_bodyfree_contract = assert_p7_r54_clr19_p5_decision_candidate_separation_contract

build_clr18_bodyfree_post_review_summary = build_p7_r54_clr18_bodyfree_post_review_summary
assert_clr18_bodyfree_post_review_summary_contract = assert_p7_r54_clr18_bodyfree_post_review_summary_contract
build_clr19_p5_decision_candidate_separation = build_p7_r54_clr19_p5_decision_candidate_separation
assert_clr19_p5_decision_candidate_separation_contract = assert_p7_r54_clr19_p5_decision_candidate_separation_contract

__all__ = (
    "P7_R54_CLR18_BODYFREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION",
    "P7_R54_CLR19_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION",
    "P7_R54_CLR18_SCHEMA_VERSION",
    "P7_R54_CLR19_SCHEMA_VERSION",
    "P7_R54_CLR18_STEP_REF",
    "P7_R54_CLR19_STEP_REF",
    "P7_R54_CLR20_STEP_REF",
    "P7_R54_CLR18_SUMMARY_READY_STATUS_REF",
    "P7_R54_CLR18_SUMMARY_BLOCKED_STATUS_REF",
    "P7_R54_CLR18_ALLOWED_SUMMARY_STATUS_REFS",
    "P7_R54_CLR18_SUMMARY_REF",
    "P7_R54_CLR18_SUMMARY_POLICY_REF",
    "P7_R54_CLR18_READY_REASON_REF",
    "P7_R54_CLR18_BLOCKED_REASON_REF",
    "P7_R54_CLR18_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_CLR19_DECISION_SEPARATION_READY_STATUS_REF",
    "P7_R54_CLR19_DECISION_SEPARATION_BLOCKED_STATUS_REF",
    "P7_R54_CLR19_DECISION_SEPARATION_REF",
    "P7_R54_CLR19_P5_CONFIRMED_CANDIDATE_REF",
    "P7_R54_CLR19_P5_REPAIR_RETURN_REF",
    "P7_R54_CLR19_P4_R12_TARGETED_REPAIR_REF",
    "P7_R54_CLR19_INCONCLUSIVE_REF",
    "P7_R54_CLR19_DECISION_CANDIDATE_REFS",
    "P7_R54_CLR18_IMPLEMENTED_STEPS",
    "P7_R54_CLR18_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_CLR19_IMPLEMENTED_STEPS",
    "P7_R54_CLR19_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_CLR18_BODYFREE_POST_REVIEW_SUMMARY_REQUIRED_FIELD_REFS",
    "P7_R54_CLR19_P5_DECISION_CANDIDATE_SEPARATION_REQUIRED_FIELD_REFS",
    "build_p7_r54_clr18_bodyfree_post_review_summary",
    "assert_p7_r54_clr18_bodyfree_post_review_summary_contract",
    "build_p7_r54_clr19_p5_decision_candidate_separation",
    "assert_p7_r54_clr19_p5_decision_candidate_separation_contract",
    "build_clr18_bodyfree_post_review_summary",
    "assert_clr18_bodyfree_post_review_summary_contract",
    "build_clr19_p5_decision_candidate_separation",
    "assert_clr19_p5_decision_candidate_separation_contract",
)
