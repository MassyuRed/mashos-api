# -*- coding: utf-8 -*-
"""P7-R54 current snapshot local review run CLR20-CLR21 helpers.

CLR20 creates only a body-free P6 limited human readfeel candidate handoff when
CLR19 has separated a P5 confirmed candidate.  It never starts P6, finalizes P5,
marks actual review evidence complete, starts P8, or allows release.

CLR21 aggregates question-need observation counts as P8 material candidate-only
handoff.  It never creates question text, draft question text, question API/DB/RN
UI, trigger logic, response keys, persistence, P8 start, or release permission.
"""

from __future__ import annotations

from collections.abc import Mapping
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
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr14_clr15_20260627 as clr15
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr18_clr19_20260627 as clr19


P7_R54_CLR20_P6_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr20_p6_candidate_only_handoff.bodyfree.v1"
)
P7_R54_CLR21_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr21_p8_material_candidate_only_handoff.bodyfree.v1"
)
P7_R54_CLR20_SCHEMA_VERSION: Final = P7_R54_CLR20_P6_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION
P7_R54_CLR21_SCHEMA_VERSION: Final = P7_R54_CLR21_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION

P7_R54_CLR_STEP: Final = clr03.P7_R54_CLR_STEP
P7_R54_CLR_SCOPE: Final = clr03.P7_R54_CLR_SCOPE
P7_R54_CLR_POLICY_KIND: Final = clr03.P7_R54_CLR_POLICY_KIND
P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID: Final = clr03.P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID
P7_R54_CLR20_STEP_REF: Final = clr03.P7_R54_CLR20_STEP_REF
P7_R54_CLR21_STEP_REF: Final = clr03.P7_R54_CLR21_STEP_REF
P7_R54_CLR22_STEP_REF: Final = clr03.P7_R54_CLR22_STEP_REF

P7_R54_CLR20_P6_CANDIDATE_HANDOFF_READY_STATUS_REF: Final = "P6_CANDIDATE_ONLY_HANDOFF_READY_BODYFREE_20260627"
P7_R54_CLR20_P6_CANDIDATE_HANDOFF_BLOCKED_STATUS_REF: Final = "P6_CANDIDATE_ONLY_HANDOFF_BLOCKED_20260627"
P7_R54_CLR20_ALLOWED_P6_CANDIDATE_HANDOFF_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_CLR20_P6_CANDIDATE_HANDOFF_READY_STATUS_REF,
    P7_R54_CLR20_P6_CANDIDATE_HANDOFF_BLOCKED_STATUS_REF,
)
P7_R54_CLR20_P6_CANDIDATE_HANDOFF_REF: Final = "R54_CLR20_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_ONLY_HANDOFF_20260627"
P7_R54_CLR20_P6_CANDIDATE_REF: Final = "P6_LIMITED_HUMAN_READFEEL_CANDIDATE_FROM_CLR19_P5_CONFIRMED_CANDIDATE_BODYFREE"
P7_R54_CLR20_READY_REASON_REF: Final = "r54_clr20_p6_candidate_only_handoff_ready_from_p5_confirmed_candidate_bodyfree"
P7_R54_CLR20_BLOCKED_REASON_REF: Final = "r54_clr20_p6_candidate_only_handoff_blocked_until_clr19_p5_confirmed_candidate"
P7_R54_CLR20_CANDIDATE_ONLY_POLICY_REF: Final = "p6_candidate_only_handoff_start_allowed_false_20260627"
P7_R54_CLR20_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-CLR-20_blocked_until_p5_confirmed_candidate_and_bodyfree_validation_before_p6_candidate_handoff"
)
P7_R54_CLR20_NEXT_WORK_AFTER_CLR19_REF: Final = "r54_clr20_p6_candidate_only_handoff_after_p5_decision_candidate_separation"
P7_R54_CLR20_NEXT_WORK_AFTER_CLR20_REF: Final = "r54_clr21_p8_material_candidate_only_handoff_after_p6_candidate_handoff"

P7_R54_CLR21_P8_MATERIAL_HANDOFF_READY_STATUS_REF: Final = "P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_READY_BODYFREE_20260627"
P7_R54_CLR21_P8_MATERIAL_HANDOFF_BLOCKED_STATUS_REF: Final = "P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_BLOCKED_20260627"
P7_R54_CLR21_ALLOWED_P8_MATERIAL_HANDOFF_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_CLR21_P8_MATERIAL_HANDOFF_READY_STATUS_REF,
    P7_R54_CLR21_P8_MATERIAL_HANDOFF_BLOCKED_STATUS_REF,
)
P7_R54_CLR21_P8_MATERIAL_HANDOFF_REF: Final = "R54_CLR21_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_ONLY_HANDOFF_20260627"
P7_R54_CLR21_P8_MATERIAL_CANDIDATE_REF: Final = "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_FROM_R54_CLR_BODYFREE_OBSERVATION"
P7_R54_CLR21_READY_REASON_REF: Final = "r54_clr21_p8_material_candidate_only_handoff_ready_from_question_observation_rows_bodyfree"
P7_R54_CLR21_NO_MATERIAL_REASON_REF: Final = "r54_clr21_p8_material_candidate_only_handoff_ready_no_question_material_rows_bodyfree"
P7_R54_CLR21_BLOCKED_REASON_REF: Final = "r54_clr21_p8_material_candidate_only_handoff_blocked_until_clr20_p6_candidate_handoff_ready"
P7_R54_CLR21_CANDIDATE_ONLY_POLICY_REF: Final = "p8_material_candidate_only_start_allowed_false_question_implementation_false_20260627"
P7_R54_CLR21_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-CLR-21_blocked_until_p6_candidate_handoff_ready_before_p8_material_handoff"
)
P7_R54_CLR21_NEXT_WORK_AFTER_CLR20_REF: Final = "r54_clr21_p8_material_candidate_only_handoff_after_p6_candidate_handoff"
P7_R54_CLR21_NEXT_WORK_AFTER_CLR21_REF: Final = "r54_clr22_final_no_body_leak_no_question_text_no_touch_validation_after_candidate_handoffs"

P7_R54_CLR21_P8_MATERIAL_ALLOWED_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = (
    *clr15.P7_R54_CLR14_P8_MATERIAL_CANDIDATE_PRIMARY_CLASS_REFS,
)
P7_R54_CLR21_P8_MATERIAL_DISALLOWED_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = tuple(
    primary
    for primary in clr15.P7_R54_CLR14_QUESTION_NEED_PRIMARY_CLASS_REFS
    if primary not in set(P7_R54_CLR21_P8_MATERIAL_ALLOWED_PRIMARY_CLASS_REFS)
)

P7_R54_CLR20_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*clr19.P7_R54_CLR19_IMPLEMENTED_STEPS, P7_R54_CLR20_STEP_REF)
P7_R54_CLR20_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = clr03.P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR01[19:]
P7_R54_CLR21_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_CLR20_IMPLEMENTED_STEPS, P7_R54_CLR21_STEP_REF)
P7_R54_CLR21_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = clr03.P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR01[20:]

P7_R54_CLR20_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[frozenset[str]] = frozenset(
    {
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "disposal_verified",
        "p5_human_blind_qa_confirmed_candidate",
        "p6_limited_human_readfeel_candidate",
    }
)
P7_R54_CLR21_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[frozenset[str]] = frozenset(
    {
        *P7_R54_CLR20_ALLOWED_TRUE_FALSE_FLAG_REFS,
        "p8_question_design_material_candidate",
    }
)

P7_R54_CLR20_P6_CANDIDATE_ONLY_HANDOFF_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *clr03.P7_R54_CLR_COMMON_REQUIRED_FIELD_REFS,
    "clr19_schema_version",
    "clr19_material_ref",
    "clr19_next_required_step",
    "clr19_decision_candidate_separation_status",
    "clr19_p5_decision_candidate_ref",
    "clr19_p5_confirmed_candidate_conditions_met",
    "clr19_p5_human_blind_qa_confirmed_candidate",
    "existing_op20_helper_ref",
    "existing_op20_schema_version",
    "existing_op20_operation_current_refs",
    "existing_op20_current_refs_are_historical_here",
    "existing_op20_reused_as_actual_p6_candidate_basis",
    "existing_op20_reused_as_actual_p6_candidate_handoff_basis",
    "existing_op20_structural_contract_reused",
    "existing_ev18_schema_version",
    "existing_ev18_current_refs",
    "existing_ev18_current_refs_are_historical_here",
    "existing_ev18_reused_as_actual_p6_candidate_basis",
    "existing_ev18_reused_as_actual_p6_candidate_handoff_basis",
    "existing_ev18_structural_contract_reused",
    "required_case_count",
    "reviewed_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "p6_candidate_handoff_status",
    "p6_candidate_handoff_ref",
    "p6_candidate_handoff_policy_ref",
    "p6_candidate_handoff_reason_refs",
    "p6_limited_human_readfeel_candidate_ref",
    "p6_limited_human_readfeel_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "p6_candidate_basis_ref",
    "p6_candidate_only_policy_ref",
    "p6_candidate_only_not_start",
    "p6_start_blocked_here",
    "p6_candidate_handoff_materialized_here",
    "p8_material_candidate_handoff_allowed_next",
    "p8_material_candidate_allowed_primary_class_refs",
    "p8_material_candidate_disallowed_primary_class_refs",
    "p8_material_candidate_allowed_primary_class_counts",
    "p8_material_candidate_row_count",
    "primary_class_counts",
    "verdict_counts",
    "axis_score_averages",
    "rating_axis_target_thresholds",
    "below_target_axis_refs",
    "open_readfeel_blocker_count",
    "open_execution_blocker_count",
    "disposal_verified",
    "no_body_leak_validation_passed",
    "no_question_text_validation_passed",
    "no_touch_validation_passed",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_human_blind_qa_confirmed_final",
    "p8_question_design_material_candidate",
    "p8_start_allowed",
    "question_implementation_started_here",
    "p8_implementation_spec_finalized_here",
    "release_allowed",
    "actual_review_evidence_complete",
    "human_review_completion_claim_blocked_here",
    "actual_human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    *clr03.P7_R54_CLR_CURRENT_REF_REQUIRED_FIELD_REFS,
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    *clr03.P7_R54_CLR_NO_TOUCH_BODYFREE_REQUIRED_FIELD_REFS,
    "raw_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    *clr03.P7_R54_CLR_FALSE_FLAG_REFS,
)

P7_R54_CLR21_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *clr03.P7_R54_CLR_COMMON_REQUIRED_FIELD_REFS,
    "clr20_schema_version",
    "clr20_material_ref",
    "clr20_next_required_step",
    "clr20_p6_candidate_handoff_status",
    "clr20_p6_limited_human_readfeel_candidate",
    "clr20_p6_limited_human_readfeel_start_allowed",
    "existing_op21_helper_ref",
    "existing_op21_schema_version",
    "existing_op21_operation_current_refs",
    "existing_op21_current_refs_are_historical_here",
    "existing_op21_reused_as_actual_p8_material_basis",
    "existing_op21_reused_as_actual_p8_material_handoff_basis",
    "existing_op21_structural_contract_reused",
    "existing_ev19_schema_version",
    "existing_ev19_current_refs",
    "existing_ev19_current_refs_are_historical_here",
    "existing_ev19_reused_as_actual_p8_material_basis",
    "existing_ev19_reused_as_actual_p8_material_handoff_basis",
    "existing_ev19_structural_contract_reused",
    "required_case_count",
    "reviewed_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "p8_material_candidate_handoff_status",
    "p8_material_candidate_handoff_ref",
    "p8_material_candidate_handoff_policy_ref",
    "p8_material_candidate_handoff_reason_refs",
    "question_need_observation_rows_aggregated",
    "question_need_observation_rows_aggregated_count",
    "p8_material_candidate_allowed_primary_class_refs",
    "p8_material_candidate_disallowed_primary_class_refs",
    "p8_material_candidate_allowed_primary_class_counts",
    "p8_material_candidate_row_count",
    "p8_question_design_material_candidate",
    "p8_question_design_material_candidate_ref",
    "p8_design_material_candidate_only_not_start",
    "p8_candidate_only_policy_ref",
    "p8_start_allowed",
    "question_implementation_started_here",
    "p8_implementation_spec_finalized_here",
    "question_trigger_logic_implemented",
    "question_answer_persistence_implemented",
    "question_api_implemented",
    "question_db_schema_implemented",
    "question_rn_ui_implemented",
    "question_response_key_implemented",
    "question_plan_guard_implemented",
    "question_storage_schema_implemented",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "question_text_included",
    "draft_question_text_included",
    "api_db_rn_response_key_changed_here",
    "runtime_changed_here",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_human_blind_qa_confirmed_final",
    "p6_limited_human_readfeel_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "release_allowed",
    "actual_review_evidence_complete",
    "human_review_completion_claim_blocked_here",
    "actual_human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "no_body_leak_validation_passed",
    "no_question_text_validation_passed",
    "no_touch_validation_passed",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    *clr03.P7_R54_CLR_CURRENT_REF_REQUIRED_FIELD_REFS,
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    *clr03.P7_R54_CLR_NO_TOUCH_BODYFREE_REQUIRED_FIELD_REFS,
    "raw_body_included",
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
    clr19._assert_common_base(  # type: ignore[attr-defined]
        data,
        schema_version=schema_version,
        policy_section=policy_section,
        source=source,
        allowed_true_false_flags=allowed_true_false_flags,
    )
    for key in ("raw_body_included", "question_text_included", "draft_question_text_included", "local_path_included"):
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=False")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)


def _count_sum(mapping: Mapping[str, Any]) -> int:
    total = 0
    for value in safe_mapping(mapping).values():
        try:
            total += int(value or 0)
        except (TypeError, ValueError):
            total += 0
    return total


def _allowed_p8_counts(source: Mapping[str, Any]) -> dict[str, int]:
    counts = safe_mapping(source.get("p8_material_candidate_allowed_primary_class_counts"))
    out: dict[str, int] = {}
    for primary_class_ref in P7_R54_CLR21_P8_MATERIAL_ALLOWED_PRIMARY_CLASS_REFS:
        try:
            count = int(counts.get(primary_class_ref) or 0)
        except (TypeError, ValueError):
            count = 0
        if count > 0:
            out[primary_class_ref] = count
    return out


def _clr20_blocker_refs(clr19_material: Mapping[str, Any]) -> list[str]:
    data = safe_mapping(clr19_material)
    blockers: list[str] = []
    if data.get("decision_candidate_separation_status") != clr19.P7_R54_CLR19_DECISION_SEPARATION_READY_STATUS_REF:
        blockers.append("clr19_p5_decision_candidate_separation_not_ready_for_p6_candidate_handoff")
    if data.get("p5_decision_candidate_ref") != clr19.P7_R54_CLR19_P5_CONFIRMED_CANDIDATE_REF:
        blockers.append("p5_confirmed_candidate_not_available_for_clr20_p6_candidate_handoff")
    if data.get("p5_confirmed_candidate_conditions_met") is not True:
        blockers.append("p5_confirmed_candidate_conditions_not_met_for_clr20_p6_candidate_handoff")
    if data.get("p5_human_blind_qa_confirmed_candidate") is not True:
        blockers.append("p5_human_blind_qa_confirmed_candidate_flag_not_true_for_clr20_p6_handoff")
    if data.get("next_required_step") != P7_R54_CLR20_STEP_REF:
        blockers.append("clr19_next_required_step_not_clr20_p6_candidate_handoff")
    if int(data.get("rating_row_count") or 0) != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("rating_row_count_not_24_for_clr20_p6_candidate_handoff")
    if int(data.get("question_observation_row_count") or 0) != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("question_observation_row_count_not_24_for_clr20_p6_candidate_handoff")
    if int(data.get("open_readfeel_blocker_count") or 0) != 0 or int(data.get("open_execution_blocker_count") or 0) != 0:
        blockers.append("open_blocker_count_not_zero_for_clr20_p6_candidate_handoff")
    if data.get("disposal_verified") is not True:
        blockers.append("disposal_not_verified_for_clr20_p6_candidate_handoff")
    if data.get("no_body_leak_validation_passed") is not True or data.get("no_question_text_validation_passed") is not True or data.get("no_touch_validation_passed") is not True:
        blockers.append("bodyfree_no_touch_validation_not_ready_for_clr20_p6_candidate_handoff")
    if data.get("p5_human_blind_qa_confirmed_final") is not False:
        blockers.append("p5_final_confirmation_must_not_precede_clr20_p6_candidate_handoff")
    if data.get("p6_limited_human_readfeel_start_allowed") is not False or data.get("p8_start_allowed") is not False or data.get("release_allowed") is not False:
        blockers.append("clr19_must_not_allow_p6_p8_or_release_before_candidate_handoffs")
    return dedupe_identifiers(blockers, limit=100, max_length=180)


def build_p7_r54_clr20_p6_candidate_only_handoff(
    *,
    p5_decision_candidate_separation: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_clr20_p6_candidate_only_handoff",
) -> dict[str, Any]:
    """Build CLR20 body-free P6 candidate-only handoff, not P6 start."""
    prior = safe_mapping(p5_decision_candidate_separation) if p5_decision_candidate_separation is not None else clr19.build_p7_r54_clr19_p5_decision_candidate_separation()
    clr19.assert_p7_r54_clr19_p5_decision_candidate_separation_contract(prior)
    blockers = _clr20_blocker_refs(prior)
    ready = not blockers
    p8_counts = _allowed_p8_counts(prior) if ready else {}
    p8_candidate_row_count = _count_sum(p8_counts) if ready else 0
    material = {
        "schema_version": P7_R54_CLR20_P6_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_CLR_STEP,
        "scope": P7_R54_CLR_SCOPE,
        "policy_kind": P7_R54_CLR_POLICY_KIND,
        "policy_section": P7_R54_CLR20_STEP_REF,
        "operation_step_ref": P7_R54_CLR20_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_clr20_p6_candidate_only_handoff", max_length=220),
        "review_session_id": _safe_review_session_id(prior.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "clr19_schema_version": clr19.P7_R54_CLR19_SCHEMA_VERSION,
        "clr19_material_ref": clean_identifier(prior.get("material_id"), default="p7_r54_clr19_p5_decision_candidate_separation", max_length=220),
        "clr19_next_required_step": clean_identifier(prior.get("next_required_step"), default="", max_length=220),
        "clr19_decision_candidate_separation_status": clean_identifier(prior.get("decision_candidate_separation_status"), default=clr19.P7_R54_CLR19_DECISION_SEPARATION_BLOCKED_STATUS_REF, max_length=180),
        "clr19_p5_decision_candidate_ref": clean_identifier(prior.get("p5_decision_candidate_ref"), default=clr19.P7_R54_CLR19_INCONCLUSIVE_REF, max_length=180),
        "clr19_p5_confirmed_candidate_conditions_met": prior.get("p5_confirmed_candidate_conditions_met") is True,
        "clr19_p5_human_blind_qa_confirmed_candidate": prior.get("p5_human_blind_qa_confirmed_candidate") is True,
        "existing_op20_helper_ref": "build_p7_r54_op20_p6_candidate_handoff",
        "existing_op20_schema_version": r54op.P7_R54_OPERATION_P6_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        "existing_op20_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op20_current_refs_are_historical_here": True,
        "existing_op20_reused_as_actual_p6_candidate_basis": False,
        "existing_op20_reused_as_actual_p6_candidate_handoff_basis": False,
        "existing_op20_structural_contract_reused": True,
        "existing_ev18_schema_version": r54ev.P7_R54_EV_P6_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION,
        "existing_ev18_current_refs": dict(r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "existing_ev18_current_refs_are_historical_here": True,
        "existing_ev18_reused_as_actual_p6_candidate_basis": False,
        "existing_ev18_reused_as_actual_p6_candidate_handoff_basis": False,
        "existing_ev18_structural_contract_reused": True,
        "required_case_count": clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "reviewed_case_count": int(prior.get("reviewed_case_count") or 0) if ready else 0,
        "rating_row_count": int(prior.get("rating_row_count") or 0) if ready else 0,
        "question_observation_row_count": int(prior.get("question_observation_row_count") or 0) if ready else 0,
        "p6_candidate_handoff_status": P7_R54_CLR20_P6_CANDIDATE_HANDOFF_READY_STATUS_REF if ready else P7_R54_CLR20_P6_CANDIDATE_HANDOFF_BLOCKED_STATUS_REF,
        "p6_candidate_handoff_ref": P7_R54_CLR20_P6_CANDIDATE_HANDOFF_REF if ready else "p6_candidate_handoff_not_ready_bodyfree_20260627",
        "p6_candidate_handoff_policy_ref": P7_R54_CLR20_CANDIDATE_ONLY_POLICY_REF,
        "p6_candidate_handoff_reason_refs": [P7_R54_CLR20_READY_REASON_REF] if ready else dedupe_identifiers([P7_R54_CLR20_BLOCKED_REASON_REF, *blockers], limit=100, max_length=180),
        "p6_limited_human_readfeel_candidate_ref": P7_R54_CLR20_P6_CANDIDATE_REF if ready else "",
        "p6_limited_human_readfeel_candidate": ready,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_candidate_basis_ref": "clr19_p5_confirmed_candidate_conditions_bodyfree_review_summary" if ready else "p5_confirmed_candidate_required_before_p6_candidate_handoff",
        "p6_candidate_only_policy_ref": P7_R54_CLR20_CANDIDATE_ONLY_POLICY_REF,
        "p6_candidate_only_not_start": True,
        "p6_start_blocked_here": True,
        "p6_candidate_handoff_materialized_here": ready,
        "p8_material_candidate_handoff_allowed_next": ready,
        "p8_material_candidate_allowed_primary_class_refs": list(P7_R54_CLR21_P8_MATERIAL_ALLOWED_PRIMARY_CLASS_REFS),
        "p8_material_candidate_disallowed_primary_class_refs": list(P7_R54_CLR21_P8_MATERIAL_DISALLOWED_PRIMARY_CLASS_REFS),
        "p8_material_candidate_allowed_primary_class_counts": dict(p8_counts),
        "p8_material_candidate_row_count": p8_candidate_row_count,
        "primary_class_counts": dict(safe_mapping(prior.get("primary_class_counts"))) if ready else {},
        "verdict_counts": dict(safe_mapping(prior.get("verdict_counts"))) if ready else {},
        "axis_score_averages": dict(safe_mapping(prior.get("axis_score_averages"))) if ready else {},
        "rating_axis_target_thresholds": dict(safe_mapping(prior.get("rating_axis_target_thresholds"))) if ready else {},
        "below_target_axis_refs": list(prior.get("below_target_axis_refs") or []) if ready else [],
        "open_readfeel_blocker_count": int(prior.get("open_readfeel_blocker_count") or 0) if ready else 0,
        "open_execution_blocker_count": int(prior.get("open_execution_blocker_count") or 0) if ready else len(blockers),
        "disposal_verified": prior.get("disposal_verified") is True and ready,
        "no_body_leak_validation_passed": prior.get("no_body_leak_validation_passed") is True and ready,
        "no_question_text_validation_passed": prior.get("no_question_text_validation_passed") is True and ready,
        "no_touch_validation_passed": prior.get("no_touch_validation_passed") is True and ready,
        "p5_human_blind_qa_confirmed_candidate": prior.get("p5_human_blind_qa_confirmed_candidate") is True and ready,
        "p5_human_blind_qa_confirmed_final": False,
        "p8_question_design_material_candidate": False,
        "p8_start_allowed": False,
        "question_implementation_started_here": False,
        "p8_implementation_spec_finalized_here": False,
        "release_allowed": False,
        "actual_review_evidence_complete": False,
        "human_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "actual_rating_rows_materialized_here": bool(prior.get("actual_rating_rows_materialized_here") is True and ready),
        "actual_blocker_rows_materialized_here": bool(prior.get("actual_blocker_rows_materialized_here") is True and ready),
        "actual_question_need_observation_rows_materialized_here": bool(prior.get("actual_question_need_observation_rows_materialized_here") is True and ready),
        "actual_disposal_receipt_materialized_here": bool(prior.get("actual_disposal_receipt_materialized_here") is True and ready),
        "execution_blocker_ids": [] if ready else dedupe_identifiers(blockers, limit=100, max_length=180),
        "open_execution_blocker_ids": [] if ready else dedupe_identifiers(blockers, limit=100, max_length=180),
        **_current_ref_fields(),
        "implemented_steps": list(P7_R54_CLR20_IMPLEMENTED_STEPS if ready else tuple(prior.get("implemented_steps") or clr19.P7_R54_CLR19_IMPLEMENTED_STEPS)),
        "not_yet_implemented_steps": list(P7_R54_CLR20_NOT_YET_IMPLEMENTED_STEPS if ready else tuple(prior.get("not_yet_implemented_steps") or clr19.P7_R54_CLR19_NOT_YET_IMPLEMENTED_STEPS)),
        "first_next_work_ref": P7_R54_CLR20_NEXT_WORK_AFTER_CLR20_REF if ready else P7_R54_CLR20_NEXT_WORK_AFTER_CLR19_REF,
        "next_required_step": P7_R54_CLR21_STEP_REF if ready else P7_R54_CLR20_BLOCKED_NEXT_REQUIRED_STEP_REF,
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
            "p6_limited_human_readfeel_candidate",
        ),
    }
    material["actual_rating_rows_materialized_here"] = bool(prior.get("actual_rating_rows_materialized_here") is True and ready)
    material["actual_blocker_rows_materialized_here"] = bool(prior.get("actual_blocker_rows_materialized_here") is True and ready)
    material["actual_question_need_observation_rows_materialized_here"] = bool(prior.get("actual_question_need_observation_rows_materialized_here") is True and ready)
    material["actual_disposal_receipt_materialized_here"] = bool(prior.get("actual_disposal_receipt_materialized_here") is True and ready)
    material["disposal_verified"] = prior.get("disposal_verified") is True and ready
    material["p5_human_blind_qa_confirmed_candidate"] = prior.get("p5_human_blind_qa_confirmed_candidate") is True and ready
    material["p6_limited_human_readfeel_candidate"] = ready
    assert_p7_r54_clr20_p6_candidate_only_handoff_contract(material)
    return material


def assert_p7_r54_clr20_p6_candidate_only_handoff_contract(data: Mapping[str, Any]) -> bool:
    material = safe_mapping(data)
    _assert_required_fields(material, required=P7_R54_CLR20_P6_CANDIDATE_ONLY_HANDOFF_REQUIRED_FIELD_REFS, source="P7-R54-CLR20")
    _assert_common_base(
        material,
        schema_version=P7_R54_CLR20_P6_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION,
        policy_section=P7_R54_CLR20_STEP_REF,
        source="P7-R54-CLR20",
        allowed_true_false_flags=P7_R54_CLR20_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    if safe_mapping(material.get("existing_op20_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("P7-R54-CLR20 existing OP20 refs changed")
    if safe_mapping(material.get("existing_ev18_current_refs")) != r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("P7-R54-CLR20 existing EV18 refs changed")
    for key in (
        "existing_op20_current_refs_are_historical_here",
        "existing_op20_structural_contract_reused",
        "existing_ev18_current_refs_are_historical_here",
        "existing_ev18_structural_contract_reused",
        "p6_candidate_only_not_start",
        "p6_start_blocked_here",
        "human_review_completion_claim_blocked_here",
        "actual_human_review_completion_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if material.get(key) is not True:
            raise ValueError(f"P7-R54-CLR20 must keep {key}=True")
    for key in (
        "existing_op20_reused_as_actual_p6_candidate_basis",
        "existing_op20_reused_as_actual_p6_candidate_handoff_basis",
        "existing_ev18_reused_as_actual_p6_candidate_basis",
        "existing_ev18_reused_as_actual_p6_candidate_handoff_basis",
        "p6_limited_human_readfeel_start_allowed",
        "p5_human_blind_qa_confirmed_final",
        "p8_question_design_material_candidate",
        "p8_start_allowed",
        "question_implementation_started_here",
        "p8_implementation_spec_finalized_here",
        "release_allowed",
        "actual_review_evidence_complete",
    ):
        if material.get(key) is not False:
            raise ValueError(f"P7-R54-CLR20 must keep {key}=False")
    if material.get("p6_candidate_handoff_status") not in P7_R54_CLR20_ALLOWED_P6_CANDIDATE_HANDOFF_STATUS_REFS:
        raise ValueError("P7-R54-CLR20 P6 candidate status changed")
    ready = material.get("p6_candidate_handoff_status") == P7_R54_CLR20_P6_CANDIDATE_HANDOFF_READY_STATUS_REF
    if material.get("p6_limited_human_readfeel_candidate") is not ready:
        raise ValueError("P7-R54-CLR20 P6 candidate flag must match readiness")
    if material.get("p6_candidate_handoff_materialized_here") is not ready:
        raise ValueError("P7-R54-CLR20 materialized flag must match readiness")
    if material.get("p8_material_candidate_handoff_allowed_next") is not ready:
        raise ValueError("P7-R54-CLR20 P8 material next allowance must match readiness")
    p8_counts = safe_mapping(material.get("p8_material_candidate_allowed_primary_class_counts"))
    if material.get("p8_material_candidate_row_count") != _count_sum(p8_counts):
        raise ValueError("P7-R54-CLR20 P8 material count mismatch")
    if not set(p8_counts).issubset(set(P7_R54_CLR21_P8_MATERIAL_ALLOWED_PRIMARY_CLASS_REFS)):
        raise ValueError("P7-R54-CLR20 P8 material counts outside allowed refs")
    if tuple(material.get("p8_material_candidate_allowed_primary_class_refs") or ()) != P7_R54_CLR21_P8_MATERIAL_ALLOWED_PRIMARY_CLASS_REFS:
        raise ValueError("P7-R54-CLR20 allowed P8 primary class refs changed")
    if tuple(material.get("p8_material_candidate_disallowed_primary_class_refs") or ()) != P7_R54_CLR21_P8_MATERIAL_DISALLOWED_PRIMARY_CLASS_REFS:
        raise ValueError("P7-R54-CLR20 disallowed P8 primary class refs changed")
    if ready:
        if material.get("p6_candidate_handoff_ref") != P7_R54_CLR20_P6_CANDIDATE_HANDOFF_REF:
            raise ValueError("P7-R54-CLR20 ready handoff ref changed")
        if material.get("p6_limited_human_readfeel_candidate_ref") != P7_R54_CLR20_P6_CANDIDATE_REF:
            raise ValueError("P7-R54-CLR20 P6 candidate ref changed")
        if material.get("p6_candidate_handoff_reason_refs") != [P7_R54_CLR20_READY_REASON_REF]:
            raise ValueError("P7-R54-CLR20 ready reason refs changed")
        if material.get("clr19_p5_decision_candidate_ref") != clr19.P7_R54_CLR19_P5_CONFIRMED_CANDIDATE_REF:
            raise ValueError("P7-R54-CLR20 ready requires CLR19 P5 confirmed candidate")
        if material.get("clr19_p5_confirmed_candidate_conditions_met") is not True or material.get("clr19_p5_human_blind_qa_confirmed_candidate") is not True:
            raise ValueError("P7-R54-CLR20 ready requires CLR19 confirmed candidate conditions")
        if material.get("p5_human_blind_qa_confirmed_candidate") is not True:
            raise ValueError("P7-R54-CLR20 ready must retain P5 candidate basis")
        if material.get("rating_row_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-CLR20 ready rating count changed")
        if material.get("question_observation_row_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-CLR20 ready question count changed")
        if material.get("open_readfeel_blocker_count") != 0 or material.get("open_execution_blocker_count") != 0 or material.get("open_execution_blocker_ids"):
            raise ValueError("P7-R54-CLR20 ready must not carry open blockers")
        if material.get("disposal_verified") is not True:
            raise ValueError("P7-R54-CLR20 ready must preserve verified disposal")
        if material.get("no_body_leak_validation_passed") is not True or material.get("no_question_text_validation_passed") is not True or material.get("no_touch_validation_passed") is not True:
            raise ValueError("P7-R54-CLR20 ready must preserve body-free/no-touch validation")
        for true_key in (
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "p5_human_blind_qa_confirmed_candidate",
            "p6_limited_human_readfeel_candidate",
        ):
            if material.get(true_key) is not True:
                raise ValueError(f"P7-R54-CLR20 ready must keep {true_key}=True")
        if tuple(material.get("implemented_steps") or ()) != P7_R54_CLR20_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR20 implemented steps changed")
        if tuple(material.get("not_yet_implemented_steps") or ()) != P7_R54_CLR20_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR20 not-yet steps changed")
        if material.get("next_required_step") != P7_R54_CLR21_STEP_REF:
            raise ValueError("P7-R54-CLR20 ready must point to CLR21")
    else:
        if material.get("p6_candidate_handoff_status") != P7_R54_CLR20_P6_CANDIDATE_HANDOFF_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-CLR20 blocked status changed")
        if material.get("p6_candidate_handoff_ref") != "p6_candidate_handoff_not_ready_bodyfree_20260627":
            raise ValueError("P7-R54-CLR20 blocked handoff ref changed")
        if material.get("p6_limited_human_readfeel_candidate") is not False:
            raise ValueError("P7-R54-CLR20 blocked must not set P6 candidate")
        if not material.get("open_execution_blocker_ids"):
            raise ValueError("P7-R54-CLR20 blocked must carry execution blockers")
        if material.get("next_required_step") != P7_R54_CLR20_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-CLR20 blocked next step changed")
    return True


def build_p7_r54_clr21_p8_material_candidate_only_handoff(
    *,
    p6_candidate_only_handoff: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_clr21_p8_material_candidate_only_handoff",
) -> dict[str, Any]:
    """Build CLR21 body-free P8 material candidate-only handoff, not P8 start."""
    prior = safe_mapping(p6_candidate_only_handoff) if p6_candidate_only_handoff is not None else build_p7_r54_clr20_p6_candidate_only_handoff()
    assert_p7_r54_clr20_p6_candidate_only_handoff_contract(prior)
    ready = bool(
        prior.get("p6_candidate_handoff_status") == P7_R54_CLR20_P6_CANDIDATE_HANDOFF_READY_STATUS_REF
        and prior.get("p8_material_candidate_handoff_allowed_next") is True
        and prior.get("next_required_step") == P7_R54_CLR21_STEP_REF
        and prior.get("p6_limited_human_readfeel_candidate") is True
        and prior.get("p6_limited_human_readfeel_start_allowed") is False
        and prior.get("disposal_verified") is True
        and prior.get("no_body_leak_validation_passed") is True
        and prior.get("no_question_text_validation_passed") is True
        and prior.get("no_touch_validation_passed") is True
    )
    blockers = [] if ready else [P7_R54_CLR21_BLOCKED_REASON_REF, "clr20_p6_candidate_handoff_not_ready_for_p8_material_candidate_handoff"]
    p8_counts = dict(safe_mapping(prior.get("p8_material_candidate_allowed_primary_class_counts"))) if ready else {}
    p8_candidate_row_count = _count_sum(p8_counts) if ready else 0
    p8_candidate = bool(ready and p8_candidate_row_count > 0)
    material = {
        "schema_version": P7_R54_CLR21_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_CLR_STEP,
        "scope": P7_R54_CLR_SCOPE,
        "policy_kind": P7_R54_CLR_POLICY_KIND,
        "policy_section": P7_R54_CLR21_STEP_REF,
        "operation_step_ref": P7_R54_CLR21_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_clr21_p8_material_candidate_only_handoff", max_length=220),
        "review_session_id": _safe_review_session_id(prior.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "clr20_schema_version": P7_R54_CLR20_SCHEMA_VERSION,
        "clr20_material_ref": clean_identifier(prior.get("material_id"), default="p7_r54_clr20_p6_candidate_only_handoff", max_length=220),
        "clr20_next_required_step": clean_identifier(prior.get("next_required_step"), default="", max_length=220),
        "clr20_p6_candidate_handoff_status": clean_identifier(prior.get("p6_candidate_handoff_status"), default=P7_R54_CLR20_P6_CANDIDATE_HANDOFF_BLOCKED_STATUS_REF, max_length=180),
        "clr20_p6_limited_human_readfeel_candidate": prior.get("p6_limited_human_readfeel_candidate") is True,
        "clr20_p6_limited_human_readfeel_start_allowed": prior.get("p6_limited_human_readfeel_start_allowed") is True,
        "existing_op21_helper_ref": "build_p7_r54_op21_p8_material_candidate_handoff",
        "existing_op21_schema_version": r54op.P7_R54_OPERATION_P8_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        "existing_op21_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op21_current_refs_are_historical_here": True,
        "existing_op21_reused_as_actual_p8_material_basis": False,
        "existing_op21_reused_as_actual_p8_material_handoff_basis": False,
        "existing_op21_structural_contract_reused": True,
        "existing_ev19_schema_version": r54ev.P7_R54_EV_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION,
        "existing_ev19_current_refs": dict(r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "existing_ev19_current_refs_are_historical_here": True,
        "existing_ev19_reused_as_actual_p8_material_basis": False,
        "existing_ev19_reused_as_actual_p8_material_handoff_basis": False,
        "existing_ev19_structural_contract_reused": True,
        "required_case_count": clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "reviewed_case_count": int(prior.get("reviewed_case_count") or 0) if ready else 0,
        "rating_row_count": int(prior.get("rating_row_count") or 0) if ready else 0,
        "question_observation_row_count": int(prior.get("question_observation_row_count") or 0) if ready else 0,
        "p8_material_candidate_handoff_status": P7_R54_CLR21_P8_MATERIAL_HANDOFF_READY_STATUS_REF if ready else P7_R54_CLR21_P8_MATERIAL_HANDOFF_BLOCKED_STATUS_REF,
        "p8_material_candidate_handoff_ref": P7_R54_CLR21_P8_MATERIAL_HANDOFF_REF if ready else "p8_material_candidate_handoff_not_ready_bodyfree_20260627",
        "p8_material_candidate_handoff_policy_ref": P7_R54_CLR21_CANDIDATE_ONLY_POLICY_REF,
        "p8_material_candidate_handoff_reason_refs": (
            [P7_R54_CLR21_READY_REASON_REF] if p8_candidate else [P7_R54_CLR21_NO_MATERIAL_REASON_REF]
        ) if ready else dedupe_identifiers(blockers, limit=100, max_length=180),
        "question_need_observation_rows_aggregated": ready,
        "question_need_observation_rows_aggregated_count": int(prior.get("question_observation_row_count") or 0) if ready else 0,
        "p8_material_candidate_allowed_primary_class_refs": list(P7_R54_CLR21_P8_MATERIAL_ALLOWED_PRIMARY_CLASS_REFS),
        "p8_material_candidate_disallowed_primary_class_refs": list(P7_R54_CLR21_P8_MATERIAL_DISALLOWED_PRIMARY_CLASS_REFS),
        "p8_material_candidate_allowed_primary_class_counts": dict(p8_counts),
        "p8_material_candidate_row_count": p8_candidate_row_count,
        "p8_question_design_material_candidate": p8_candidate,
        "p8_question_design_material_candidate_ref": P7_R54_CLR21_P8_MATERIAL_CANDIDATE_REF if p8_candidate else "",
        "p8_design_material_candidate_only_not_start": True,
        "p8_candidate_only_policy_ref": P7_R54_CLR21_CANDIDATE_ONLY_POLICY_REF,
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
        "p5_human_blind_qa_confirmed_candidate": prior.get("p5_human_blind_qa_confirmed_candidate") is True and ready,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_candidate": prior.get("p6_limited_human_readfeel_candidate") is True and ready,
        "p6_limited_human_readfeel_start_allowed": False,
        "release_allowed": False,
        "actual_review_evidence_complete": False,
        "human_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "actual_rating_rows_materialized_here": bool(prior.get("actual_rating_rows_materialized_here") is True and ready),
        "actual_blocker_rows_materialized_here": bool(prior.get("actual_blocker_rows_materialized_here") is True and ready),
        "actual_question_need_observation_rows_materialized_here": bool(prior.get("actual_question_need_observation_rows_materialized_here") is True and ready),
        "actual_disposal_receipt_materialized_here": bool(prior.get("actual_disposal_receipt_materialized_here") is True and ready),
        "disposal_verified": prior.get("disposal_verified") is True and ready,
        "no_body_leak_validation_passed": prior.get("no_body_leak_validation_passed") is True and ready,
        "no_question_text_validation_passed": prior.get("no_question_text_validation_passed") is True and ready,
        "no_touch_validation_passed": prior.get("no_touch_validation_passed") is True and ready,
        "execution_blocker_ids": [] if ready else dedupe_identifiers(blockers, limit=100, max_length=180),
        "open_execution_blocker_ids": [] if ready else dedupe_identifiers(blockers, limit=100, max_length=180),
        **_current_ref_fields(),
        "implemented_steps": list(P7_R54_CLR21_IMPLEMENTED_STEPS if ready else tuple(prior.get("implemented_steps") or P7_R54_CLR20_IMPLEMENTED_STEPS)),
        "not_yet_implemented_steps": list(P7_R54_CLR21_NOT_YET_IMPLEMENTED_STEPS if ready else tuple(prior.get("not_yet_implemented_steps") or P7_R54_CLR20_NOT_YET_IMPLEMENTED_STEPS)),
        "first_next_work_ref": P7_R54_CLR21_NEXT_WORK_AFTER_CLR21_REF if ready else P7_R54_CLR21_NEXT_WORK_AFTER_CLR20_REF,
        "next_required_step": P7_R54_CLR22_STEP_REF if ready else P7_R54_CLR21_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_clr_no_touch_contract": clr15._no_touch_contract(),  # type: ignore[attr-defined]
        "body_free_markers": clr15._body_free_markers(),  # type: ignore[attr-defined]
        "body_free": True,
        "raw_body_included": False,
        "local_path_included": False,
        **_false_flags_except(
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "disposal_verified",
            "p5_human_blind_qa_confirmed_candidate",
            "p6_limited_human_readfeel_candidate",
            "p8_question_design_material_candidate",
        ),
    }
    material["actual_rating_rows_materialized_here"] = bool(prior.get("actual_rating_rows_materialized_here") is True and ready)
    material["actual_blocker_rows_materialized_here"] = bool(prior.get("actual_blocker_rows_materialized_here") is True and ready)
    material["actual_question_need_observation_rows_materialized_here"] = bool(prior.get("actual_question_need_observation_rows_materialized_here") is True and ready)
    material["actual_disposal_receipt_materialized_here"] = bool(prior.get("actual_disposal_receipt_materialized_here") is True and ready)
    material["disposal_verified"] = prior.get("disposal_verified") is True and ready
    material["p5_human_blind_qa_confirmed_candidate"] = prior.get("p5_human_blind_qa_confirmed_candidate") is True and ready
    material["p6_limited_human_readfeel_candidate"] = prior.get("p6_limited_human_readfeel_candidate") is True and ready
    material["p8_question_design_material_candidate"] = p8_candidate
    material["question_text_included"] = False
    material["draft_question_text_included"] = False
    assert_p7_r54_clr21_p8_material_candidate_only_handoff_contract(material)
    return material


def assert_p7_r54_clr21_p8_material_candidate_only_handoff_contract(data: Mapping[str, Any]) -> bool:
    material = safe_mapping(data)
    _assert_required_fields(material, required=P7_R54_CLR21_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_REQUIRED_FIELD_REFS, source="P7-R54-CLR21")
    _assert_common_base(
        material,
        schema_version=P7_R54_CLR21_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION,
        policy_section=P7_R54_CLR21_STEP_REF,
        source="P7-R54-CLR21",
        allowed_true_false_flags=P7_R54_CLR21_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    if safe_mapping(material.get("existing_op21_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("P7-R54-CLR21 existing OP21 refs changed")
    if safe_mapping(material.get("existing_ev19_current_refs")) != r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("P7-R54-CLR21 existing EV19 refs changed")
    for key in (
        "existing_op21_current_refs_are_historical_here",
        "existing_op21_structural_contract_reused",
        "existing_ev19_current_refs_are_historical_here",
        "existing_ev19_structural_contract_reused",
        "p8_design_material_candidate_only_not_start",
        "human_review_completion_claim_blocked_here",
        "actual_human_review_completion_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if material.get(key) is not True:
            raise ValueError(f"P7-R54-CLR21 must keep {key}=True")
    for key in (
        "existing_op21_reused_as_actual_p8_material_basis",
        "existing_op21_reused_as_actual_p8_material_handoff_basis",
        "existing_ev19_reused_as_actual_p8_material_basis",
        "existing_ev19_reused_as_actual_p8_material_handoff_basis",
        "p8_start_allowed",
        "question_implementation_started_here",
        "p8_implementation_spec_finalized_here",
        "question_trigger_logic_implemented",
        "question_answer_persistence_implemented",
        "question_api_implemented",
        "question_db_schema_implemented",
        "question_rn_ui_implemented",
        "question_response_key_implemented",
        "question_plan_guard_implemented",
        "question_storage_schema_implemented",
        "question_text_materialized_here",
        "draft_question_text_materialized_here",
        "question_text_included",
        "draft_question_text_included",
        "api_db_rn_response_key_changed_here",
        "runtime_changed_here",
        "p5_human_blind_qa_confirmed_final",
        "p6_limited_human_readfeel_start_allowed",
        "release_allowed",
        "actual_review_evidence_complete",
    ):
        if material.get(key) is not False:
            raise ValueError(f"P7-R54-CLR21 must keep {key}=False")
    if material.get("p8_material_candidate_handoff_status") not in P7_R54_CLR21_ALLOWED_P8_MATERIAL_HANDOFF_STATUS_REFS:
        raise ValueError("P7-R54-CLR21 P8 material status changed")
    ready = material.get("p8_material_candidate_handoff_status") == P7_R54_CLR21_P8_MATERIAL_HANDOFF_READY_STATUS_REF
    if material.get("question_need_observation_rows_aggregated") is not ready:
        raise ValueError("P7-R54-CLR21 aggregation flag must match readiness")
    p8_counts = safe_mapping(material.get("p8_material_candidate_allowed_primary_class_counts"))
    candidate_count = _count_sum(p8_counts)
    if material.get("p8_material_candidate_row_count") != candidate_count:
        raise ValueError("P7-R54-CLR21 P8 material candidate count mismatch")
    if not set(p8_counts).issubset(set(P7_R54_CLR21_P8_MATERIAL_ALLOWED_PRIMARY_CLASS_REFS)):
        raise ValueError("P7-R54-CLR21 P8 material counts outside allowed primary refs")
    if tuple(material.get("p8_material_candidate_allowed_primary_class_refs") or ()) != P7_R54_CLR21_P8_MATERIAL_ALLOWED_PRIMARY_CLASS_REFS:
        raise ValueError("P7-R54-CLR21 allowed P8 primary class refs changed")
    if tuple(material.get("p8_material_candidate_disallowed_primary_class_refs") or ()) != P7_R54_CLR21_P8_MATERIAL_DISALLOWED_PRIMARY_CLASS_REFS:
        raise ValueError("P7-R54-CLR21 disallowed P8 primary class refs changed")
    if material.get("p8_question_design_material_candidate") is not bool(ready and candidate_count > 0):
        raise ValueError("P7-R54-CLR21 P8 candidate flag must match material count")
    if ready:
        if material.get("p8_material_candidate_handoff_ref") != P7_R54_CLR21_P8_MATERIAL_HANDOFF_REF:
            raise ValueError("P7-R54-CLR21 ready handoff ref changed")
        expected_reason_refs = [P7_R54_CLR21_READY_REASON_REF] if candidate_count > 0 else [P7_R54_CLR21_NO_MATERIAL_REASON_REF]
        if material.get("p8_material_candidate_handoff_reason_refs") != expected_reason_refs:
            raise ValueError("P7-R54-CLR21 ready/no-material reason refs changed")
        if material.get("question_observation_row_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-CLR21 ready must aggregate 24 question rows")
        if material.get("question_need_observation_rows_aggregated_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-CLR21 ready aggregated count changed")
        if material.get("clr20_p6_limited_human_readfeel_candidate") is not True or material.get("p6_limited_human_readfeel_candidate") is not True:
            raise ValueError("P7-R54-CLR21 ready must retain P6 candidate basis")
        if material.get("clr20_p6_limited_human_readfeel_start_allowed") is not False or material.get("p6_limited_human_readfeel_start_allowed") is not False:
            raise ValueError("P7-R54-CLR21 must keep P6 start blocked")
        if material.get("disposal_verified") is not True:
            raise ValueError("P7-R54-CLR21 ready must preserve verified disposal")
        for true_key in (
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "p5_human_blind_qa_confirmed_candidate",
            "p6_limited_human_readfeel_candidate",
        ):
            if material.get(true_key) is not True:
                raise ValueError(f"P7-R54-CLR21 ready must keep {true_key}=True")
        if tuple(material.get("implemented_steps") or ()) != P7_R54_CLR21_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR21 implemented steps changed")
        if tuple(material.get("not_yet_implemented_steps") or ()) != P7_R54_CLR21_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR21 not-yet steps changed")
        if material.get("next_required_step") != P7_R54_CLR22_STEP_REF:
            raise ValueError("P7-R54-CLR21 ready must point to CLR22")
        if material.get("open_execution_blocker_ids"):
            raise ValueError("P7-R54-CLR21 ready must not carry open execution blockers")
    else:
        if material.get("p8_material_candidate_handoff_status") != P7_R54_CLR21_P8_MATERIAL_HANDOFF_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-CLR21 blocked status changed")
        if material.get("p8_material_candidate_handoff_ref") != "p8_material_candidate_handoff_not_ready_bodyfree_20260627":
            raise ValueError("P7-R54-CLR21 blocked handoff ref changed")
        if material.get("p8_question_design_material_candidate") is not False:
            raise ValueError("P7-R54-CLR21 blocked must not set P8 candidate")
        if not material.get("open_execution_blocker_ids"):
            raise ValueError("P7-R54-CLR21 blocked must carry execution blockers")
        if material.get("next_required_step") != P7_R54_CLR21_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-CLR21 blocked next step changed")
    return True


build_p7_r54_current_snapshot_local_run_clr20_p6_candidate_only_handoff = build_p7_r54_clr20_p6_candidate_only_handoff
assert_p7_r54_current_snapshot_local_run_clr20_p6_candidate_only_handoff_contract = assert_p7_r54_clr20_p6_candidate_only_handoff_contract
build_p7_r54_current_snapshot_p6_candidate_only_handoff_bodyfree = build_p7_r54_clr20_p6_candidate_only_handoff
assert_p7_r54_current_snapshot_p6_candidate_only_handoff_bodyfree_contract = assert_p7_r54_clr20_p6_candidate_only_handoff_contract
build_p7_r54_current_snapshot_local_run_clr21_p8_material_candidate_only_handoff = build_p7_r54_clr21_p8_material_candidate_only_handoff
assert_p7_r54_current_snapshot_local_run_clr21_p8_material_candidate_only_handoff_contract = assert_p7_r54_clr21_p8_material_candidate_only_handoff_contract
build_p7_r54_current_snapshot_p8_material_candidate_only_handoff_bodyfree = build_p7_r54_clr21_p8_material_candidate_only_handoff
assert_p7_r54_current_snapshot_p8_material_candidate_only_handoff_bodyfree_contract = assert_p7_r54_clr21_p8_material_candidate_only_handoff_contract

build_clr20_p6_candidate_only_handoff = build_p7_r54_clr20_p6_candidate_only_handoff
assert_clr20_p6_candidate_only_handoff_contract = assert_p7_r54_clr20_p6_candidate_only_handoff_contract
build_clr21_p8_material_candidate_only_handoff = build_p7_r54_clr21_p8_material_candidate_only_handoff
assert_clr21_p8_material_candidate_only_handoff_contract = assert_p7_r54_clr21_p8_material_candidate_only_handoff_contract

__all__ = (
    "P7_R54_CLR20_P6_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION",
    "P7_R54_CLR21_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION",
    "P7_R54_CLR20_SCHEMA_VERSION",
    "P7_R54_CLR21_SCHEMA_VERSION",
    "P7_R54_CLR20_STEP_REF",
    "P7_R54_CLR21_STEP_REF",
    "P7_R54_CLR22_STEP_REF",
    "P7_R54_CLR20_P6_CANDIDATE_HANDOFF_READY_STATUS_REF",
    "P7_R54_CLR20_P6_CANDIDATE_HANDOFF_BLOCKED_STATUS_REF",
    "P7_R54_CLR20_ALLOWED_P6_CANDIDATE_HANDOFF_STATUS_REFS",
    "P7_R54_CLR20_P6_CANDIDATE_HANDOFF_REF",
    "P7_R54_CLR20_P6_CANDIDATE_REF",
    "P7_R54_CLR20_CANDIDATE_ONLY_POLICY_REF",
    "P7_R54_CLR20_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_CLR21_P8_MATERIAL_HANDOFF_READY_STATUS_REF",
    "P7_R54_CLR21_P8_MATERIAL_HANDOFF_BLOCKED_STATUS_REF",
    "P7_R54_CLR21_ALLOWED_P8_MATERIAL_HANDOFF_STATUS_REFS",
    "P7_R54_CLR21_P8_MATERIAL_HANDOFF_REF",
    "P7_R54_CLR21_P8_MATERIAL_CANDIDATE_REF",
    "P7_R54_CLR21_CANDIDATE_ONLY_POLICY_REF",
    "P7_R54_CLR21_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_CLR21_P8_MATERIAL_ALLOWED_PRIMARY_CLASS_REFS",
    "P7_R54_CLR21_P8_MATERIAL_DISALLOWED_PRIMARY_CLASS_REFS",
    "P7_R54_CLR20_IMPLEMENTED_STEPS",
    "P7_R54_CLR20_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_CLR21_IMPLEMENTED_STEPS",
    "P7_R54_CLR21_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_CLR20_P6_CANDIDATE_ONLY_HANDOFF_REQUIRED_FIELD_REFS",
    "P7_R54_CLR21_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_REQUIRED_FIELD_REFS",
    "build_p7_r54_clr20_p6_candidate_only_handoff",
    "assert_p7_r54_clr20_p6_candidate_only_handoff_contract",
    "build_p7_r54_clr21_p8_material_candidate_only_handoff",
    "assert_p7_r54_clr21_p8_material_candidate_only_handoff_contract",
    "build_p7_r54_current_snapshot_local_run_clr20_p6_candidate_only_handoff",
    "assert_p7_r54_current_snapshot_local_run_clr20_p6_candidate_only_handoff_contract",
    "build_p7_r54_current_snapshot_p6_candidate_only_handoff_bodyfree",
    "assert_p7_r54_current_snapshot_p6_candidate_only_handoff_bodyfree_contract",
    "build_p7_r54_current_snapshot_local_run_clr21_p8_material_candidate_only_handoff",
    "assert_p7_r54_current_snapshot_local_run_clr21_p8_material_candidate_only_handoff_contract",
    "build_p7_r54_current_snapshot_p8_material_candidate_only_handoff_bodyfree",
    "assert_p7_r54_current_snapshot_p8_material_candidate_only_handoff_bodyfree_contract",
    "build_clr20_p6_candidate_only_handoff",
    "assert_clr20_p6_candidate_only_handoff_contract",
    "build_clr21_p8_material_candidate_only_handoff",
    "assert_clr21_p8_material_candidate_only_handoff_contract",
)
