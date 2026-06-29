# -*- coding: utf-8 -*-
"""P7-R54 current snapshot local review run CLR12-CLR13 helpers.

CLR12 normalizes sanitized selection-only reviewer rows into body-free rating
rows. It does not run human review, generate body-full packets, create question
observation rows, verify disposal, or promote P5/P6/P8/release state.

CLR13 separates P5 history-line readfeel blockers from review-execution blockers
as body-free rows. Execution blockers never assign readfeel verdicts, and these
helpers do not create question text or touch API/DB/RN/runtime surfaces.
"""

from __future__ import annotations

from collections import Counter
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


P7_R54_CLR12_RATING_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr12_rating_row.bodyfree.v1"
)
P7_R54_CLR12_RATING_ROW_NORMALIZATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr12_rating_row_normalization.bodyfree.v1"
)
P7_R54_CLR13_READFEEL_BLOCKER_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr13_readfeel_blocker_row.bodyfree.v1"
)
P7_R54_CLR13_EXECUTION_BLOCKER_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr13_execution_blocker_row.bodyfree.v1"
)
P7_R54_CLR13_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr13_readfeel_blocker_execution_blocker_ingestion.bodyfree.v1"
)
P7_R54_CLR12_SCHEMA_VERSION: Final = P7_R54_CLR12_RATING_ROW_NORMALIZATION_SCHEMA_VERSION
P7_R54_CLR12_ROW_SCHEMA_VERSION: Final = P7_R54_CLR12_RATING_ROW_SCHEMA_VERSION
P7_R54_CLR13_SCHEMA_VERSION: Final = P7_R54_CLR13_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION

P7_R54_CLR_STEP: Final = clr03.P7_R54_CLR_STEP
P7_R54_CLR_SCOPE: Final = clr03.P7_R54_CLR_SCOPE
P7_R54_CLR_POLICY_KIND: Final = clr03.P7_R54_CLR_POLICY_KIND
P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID: Final = clr03.P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID
P7_R54_CLR12_STEP_REF: Final = clr03.P7_R54_CLR12_STEP_REF
P7_R54_CLR13_STEP_REF: Final = clr03.P7_R54_CLR13_STEP_REF
P7_R54_CLR14_STEP_REF: Final = clr03.P7_R54_CLR14_STEP_REF

P7_R54_CLR12_RATING_NORMALIZATION_READY_STATUS_REF: Final = "RATING_ROWS_NORMALIZED_BODYFREE"
P7_R54_CLR12_RATING_NORMALIZATION_BLOCKED_STATUS_REF: Final = "RATING_ROW_NORMALIZATION_BLOCKED"
P7_R54_CLR12_ALLOWED_NORMALIZATION_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_CLR12_RATING_NORMALIZATION_READY_STATUS_REF,
    P7_R54_CLR12_RATING_NORMALIZATION_BLOCKED_STATUS_REF,
)
P7_R54_CLR12_RATING_ROW_NORMALIZATION_REF: Final = "r54_clr12_rating_row_normalization_bodyfree_20260627"
P7_R54_CLR12_RATING_ROW_SOURCE_REF: Final = "clr11_sanitized_external_local_reviewer_selection_only"
P7_R54_CLR12_READY_REASON_REF: Final = "r54_clr12_24_rating_rows_normalized_bodyfree"
P7_R54_CLR12_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "R54-CLR-12_blocked_until_24_sanitized_selection_rows_are_rating_normalizable"
P7_R54_CLR12_RATING_SCORE_MIN: Final = 0.0
P7_R54_CLR12_RATING_SCORE_MAX: Final = 1.0
P7_R54_CLR12_VERDICT_BLOCKER_CONSISTENT_REF: Final = "clr12_verdict_blocker_consistency_passed"

P7_R54_CLR13_BLOCKER_INGESTION_READY_STATUS_REF: Final = "READFEEL_EXECUTION_BLOCKERS_INGESTED_BODYFREE"
P7_R54_CLR13_BLOCKER_INGESTION_BLOCKED_STATUS_REF: Final = "READFEEL_EXECUTION_BLOCKER_INGESTION_BLOCKED"
P7_R54_CLR13_ALLOWED_BLOCKER_INGESTION_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_CLR13_BLOCKER_INGESTION_READY_STATUS_REF,
    P7_R54_CLR13_BLOCKER_INGESTION_BLOCKED_STATUS_REF,
)
P7_R54_CLR13_BLOCKER_INGESTION_REF: Final = "r54_clr13_readfeel_execution_blocker_ingestion_bodyfree_20260627"
P7_R54_CLR13_READY_REASON_REF: Final = "r54_clr13_readfeel_and_execution_blockers_separated_bodyfree"
P7_R54_CLR13_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "R54-CLR-13_blocked_until_rating_rows_are_available"
P7_R54_CLR13_READFEEL_BLOCKER_KIND_REF: Final = "p5_history_line_readfeel_blocker"
P7_R54_CLR13_EXECUTION_BLOCKER_KIND_REF: Final = "review_execution_boundary_blocker"
P7_R54_CLR13_BLOCKER_STATUS_REFS: Final[tuple[str, ...]] = ("open", "closed")

P7_R54_CLR12_RATING_AXIS_REFS: Final[tuple[str, ...]] = clr11.P7_R54_CLR11_RATING_AXIS_REFS
P7_R54_CLR12_RATING_AXIS_TARGET_THRESHOLDS: Final[dict[str, float]] = dict(clr11.P7_R54_CLR11_RATING_AXIS_TARGET_THRESHOLDS)
P7_R54_CLR12_SCORE_OPTION_REFS: Final[tuple[float, ...]] = clr11.P7_R54_CLR11_SCORE_OPTION_REFS
P7_R54_CLR12_VERDICT_OPTION_REFS: Final[tuple[str, ...]] = ("PASS", "YELLOW", "REPAIR_REQUIRED", "RED", "NOT_REVIEWABLE")
P7_R54_CLR12_READFEEL_BLOCKER_ID_REFS: Final[tuple[str, ...]] = clr11.P7_R54_CLR11_READFEEL_BLOCKER_OPTION_REFS
P7_R54_CLR12_EXECUTION_BLOCKER_ID_REFS: Final[tuple[str, ...]] = clr11.P7_R54_CLR11_EXECUTION_BLOCKER_OPTION_REFS
P7_R54_CLR13_READFEEL_BLOCKER_ID_REFS: Final[tuple[str, ...]] = P7_R54_CLR12_READFEEL_BLOCKER_ID_REFS
P7_R54_CLR13_EXECUTION_BLOCKER_ID_REFS: Final[tuple[str, ...]] = P7_R54_CLR12_EXECUTION_BLOCKER_ID_REFS

P7_R54_CLR12_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*clr11.P7_R54_CLR11_IMPLEMENTED_STEPS, P7_R54_CLR12_STEP_REF)
P7_R54_CLR12_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = clr03.P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR01[11:]
P7_R54_CLR13_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_CLR12_IMPLEMENTED_STEPS, P7_R54_CLR13_STEP_REF)
P7_R54_CLR13_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = clr03.P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR01[12:]

P7_R54_CLR12_RATING_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "rating_row_ref",
    "review_result_row_ref",
    "selection_row_ref",
    "review_session_id",
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
    "case_index",
    "case_role_family_ref",
    "plan_tier_context_ref",
    "reviewer_ref",
    "reviewed_at_ref",
    "axis_scores",
    "axis_score_count",
    "axis_score_average",
    "average_score",
    "axis_score_min",
    "axis_score_max",
    "target_thresholds",
    "below_target_axis_refs",
    "below_target_axis_count",
    "overall_read_feeling_ref",
    "verdict",
    "sanitized_reason_ids",
    "readfeel_blocker_ids",
    "readfeel_blocker_count",
    "execution_blocker_ids",
    "execution_blocker_count",
    "question_need_primary_class",
    "ambiguity_kind_refs",
    "one_question_fit_ref",
    "repair_required_refs",
    "plan_candidate_flags",
    "rating_source_ref",
    "verdict_blocker_consistency_ref",
    "pass_requires_no_blocker",
    "red_or_repair_requires_blocker_or_reason",
    "rating_row_is_bodyfree",
    "selection_only_source_row",
    "reviewer_free_text_included",
    "reviewer_note_included",
    "reviewer_notes_included",
    "raw_body_included",
    "returned_emlis_body_included",
    "history_surface_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    "local_absolute_path_included",
    "body_hash_included",
    "packet_content_included",
    "terminal_output_body_included",
    "machine_auto_score_used",
    "machine_metrics_used_for_readfeel",
    "body_free",
)

P7_R54_CLR12_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *clr03.P7_R54_CLR_COMMON_REQUIRED_FIELD_REFS,
    "clr11_schema_version",
    "clr11_material_ref",
    "clr11_next_required_step",
    "clr11_sanitized_review_result_intake_status",
    "clr11_rating_row_normalization_allowed_next",
    "existing_op12_helper_ref",
    "existing_op12_schema_version",
    "existing_ev10_schema_version",
    "existing_op12_operation_current_refs",
    "existing_ev10_current_refs",
    "existing_op12_current_refs_are_historical_here",
    "existing_ev10_current_refs_are_historical_here",
    "existing_op12_reused_as_actual_rating_basis",
    "existing_ev10_reused_as_actual_rating_basis",
    "existing_op12_structural_contract_reused",
    "existing_ev10_structural_contract_reused",
    "required_case_count",
    "sanitized_review_result_row_count",
    "rating_row_normalization_status",
    "rating_row_normalization_ref",
    "rating_row_normalization_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "rating_rows",
    "rating_row_count",
    "reviewed_case_count",
    "rating_row_refs",
    "rating_row_ref_count",
    "rating_row_refs_unique",
    "packet_ref_ids",
    "packet_ref_count",
    "packet_ref_ids_unique",
    "case_ref_ids",
    "case_ref_count",
    "case_ref_ids_unique",
    "blind_case_ids",
    "blind_case_id_count",
    "blind_case_ids_unique",
    "selection_row_refs",
    "selection_row_ref_count",
    "selection_row_refs_unique",
    "reviewer_ref_ids",
    "reviewer_ref_count",
    "rating_row_schema_version",
    "rating_row_required_field_refs",
    "rating_axis_refs",
    "rating_axis_target_thresholds",
    "rating_score_min",
    "rating_score_max",
    "allowed_score_option_refs",
    "allowed_verdict_refs",
    "readfeel_blocker_id_refs",
    "execution_blocker_id_refs",
    "all_axes_present",
    "axis_score_range_valid",
    "verdict_allowed",
    "below_target_axis_refs_calculated",
    "missing_axis_scores_pass_allowed",
    "extra_rating_axis_allowed",
    "machine_auto_score_allowed",
    "machine_metrics_used_for_readfeel_allowed",
    "reviewer_free_text_bodyfree_allowed",
    "blocked_or_not_reviewable_must_use_execution_blocker_row",
    "red_or_repair_requires_blocker_or_reason",
    "pass_requires_targets_and_no_blockers",
    "rating_rows_are_bodyfree",
    "all_required_rating_rows_present",
    "rating_case_ref_sets_match_sanitized_intake",
    "verdict_counts",
    "overall_read_feeling_counts",
    "axis_score_averages",
    "below_target_axis_refs",
    "below_target_axis_count",
    "below_target_rating_row_count",
    "rating_consistency_issue_rows",
    "rating_consistency_issue_count",
    "pass_with_any_blocker_detected",
    "pass_below_axis_target_detected",
    "red_or_repair_without_blocker_or_reason_detected",
    "readfeel_blocker_row_candidate_count",
    "execution_blocker_row_candidate_count",
    "readfeel_blocker_execution_blocker_ingestion_allowed_next",
    "rating_rows_normalized_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_review_evidence_complete",
    "question_observation_row_count",
    "disposal_verified",
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

P7_R54_CLR13_READFEEL_BLOCKER_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "blocker_row_ref",
    "review_session_id",
    "rating_row_ref",
    "packet_ref_id",
    "blind_case_id",
    "case_ref_id",
    "case_index",
    "case_role_family_ref",
    "reviewer_ref",
    "readfeel_blocker_id",
    "blocker_kind_ref",
    "blocker_status_ref",
    "source_verdict",
    "raw_body_included",
    "returned_emlis_body_included",
    "history_surface_included",
    "reviewer_free_text_included",
    "reviewer_note_included",
    "reviewer_notes_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    "local_absolute_path_included",
    "body_hash_included",
    "packet_content_included",
    "terminal_output_body_included",
    "machine_auto_score_used",
    "machine_metrics_used_for_readfeel",
    "body_free",
)

P7_R54_CLR13_EXECUTION_BLOCKER_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "execution_blocker_row_ref",
    "review_session_id",
    "source_ref",
    "packet_ref_id",
    "blind_case_id",
    "case_ref_id",
    "case_index",
    "case_role_family_ref",
    "execution_blocker_id",
    "execution_blocker_kind_ref",
    "execution_blocker_status_ref",
    "execution_blocker_does_not_assign_readfeel_verdict",
    "raw_body_included",
    "returned_emlis_body_included",
    "history_surface_included",
    "reviewer_free_text_included",
    "reviewer_note_included",
    "reviewer_notes_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    "local_absolute_path_included",
    "body_hash_included",
    "packet_content_included",
    "terminal_output_body_included",
    "machine_auto_score_used",
    "machine_metrics_used_for_readfeel",
    "body_free",
)

P7_R54_CLR13_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *clr03.P7_R54_CLR_COMMON_REQUIRED_FIELD_REFS,
    "clr12_schema_version",
    "clr12_material_ref",
    "clr12_next_required_step",
    "clr12_rating_row_normalization_status",
    "clr12_blocker_ingestion_allowed_next",
    "existing_op13_helper_ref",
    "existing_op13_schema_version",
    "existing_ev11_schema_version",
    "existing_op13_operation_current_refs",
    "existing_ev11_current_refs",
    "existing_op13_current_refs_are_historical_here",
    "existing_ev11_current_refs_are_historical_here",
    "existing_op13_reused_as_actual_blocker_basis",
    "existing_ev11_reused_as_actual_blocker_basis",
    "existing_op13_structural_contract_reused",
    "existing_ev11_structural_contract_reused",
    "required_case_count",
    "rating_row_count",
    "blocker_ingestion_status",
    "blocker_ingestion_ref",
    "blocker_ingestion_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "readfeel_blocker_row_schema_version",
    "execution_blocker_row_schema_version",
    "readfeel_blocker_row_required_field_refs",
    "execution_blocker_row_required_field_refs",
    "readfeel_blocker_id_refs",
    "execution_blocker_id_refs",
    "blocker_status_refs",
    "rating_rows",
    "readfeel_blocker_rows",
    "execution_blocker_rows",
    "readfeel_blocker_row_count",
    "execution_blocker_row_count",
    "open_readfeel_blocker_count",
    "open_execution_blocker_count",
    "readfeel_blocker_counts",
    "execution_blocker_counts",
    "rating_packet_ref_ids",
    "rating_case_ref_ids",
    "rating_blind_case_ids",
    "readfeel_blocker_rows_normalized",
    "execution_blocker_rows_normalized",
    "readfeel_and_execution_blockers_separated",
    "execution_blocker_not_mixed_into_readfeel_verdict",
    "execution_blockers_do_not_assign_readfeel_verdict",
    "execution_blocker_cases_do_not_create_rating_rows",
    "execution_blocker_open_blocks_p5_confirmed_candidate",
    "p5_confirmed_candidate_blocked_by_open_execution_blockers",
    "rating_missing_maps_to_execution_blocker_not_red",
    "local_root_missing_maps_to_execution_blocker_not_red",
    "disposal_failed_maps_to_execution_blocker_not_red",
    "body_free_leak_maps_to_execution_blocker_not_red",
    "rating_rows_preserved_from_clr12",
    "question_need_observation_normalization_allowed_next",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_review_evidence_complete",
    "question_observation_row_count",
    "disposal_verified",
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

P7_R54_CLR13_BLOCKER_INGESTION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = P7_R54_CLR13_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION_REQUIRED_FIELD_REFS

P7_R54_CLR12_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[frozenset[str]] = frozenset({"actual_rating_rows_materialized_here"})
P7_R54_CLR13_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[frozenset[str]] = frozenset({"actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here"})
P7_R54_CLR_PROHIBITED_PAYLOAD_OR_QUESTION_FIELD_REFS: Final[frozenset[str]] = frozenset(
    {
        "reviewer_free_text",
        "reviewer_note",
        "reviewer_notes",
        "raw_input",
        "returned_emlis_body",
        "history_surface",
        "question_text",
        "draft_question_text",
        "local_absolute_path",
        "local_path",
        "body_hash",
        "packet_content",
        "terminal_output_body",
    }
)


def _false_flags_except(*allowed_true_refs: str) -> dict[str, bool]:
    allowed = set(allowed_true_refs)
    return {key: False for key in clr03.P7_R54_CLR_FALSE_FLAG_REFS if key not in allowed}


def _body_free_markers() -> dict[str, bool]:
    return {
        "raw_input_included": False,
        "history_raw_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "reviewer_free_text_included": False,
        "reviewer_note_included": False,
        "reviewer_notes_included": False,
        "terminal_output_included": False,
    }


def _no_touch_contract() -> dict[str, bool]:
    return {
        "api_changed": False,
        "db_changed": False,
        "rn_changed": False,
        "runtime_changed": False,
        "api_route_changed": False,
        "request_key_changed": False,
        "response_key_changed": False,
        "db_migration_changed": False,
        "rn_visible_contract_changed": False,
        "public_response_key_changed": False,
        "runtime_gate_threshold_changed": False,
        "user_label_connection_runtime_changed": False,
        "p8_question_trigger_logic_changed": False,
        "p8_question_text_materialized": False,
        "p8_question_api_changed": False,
        "p8_question_db_changed": False,
        "p8_question_rn_changed": False,
        "release_decision_changed": False,
    }


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


def _safe_review_session_id(value: Any) -> str:
    return clean_identifier(value, default=P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID, max_length=180)


def _assert_required_fields(data: Mapping[str, Any], *, required: tuple[str, ...], source: str) -> None:
    required_set = set(required)
    missing = [field for field in required if field not in data]
    extra = [field for field in data if field not in required_set]
    if missing or extra:
        raise ValueError(f"{source} field mismatch missing={missing[:8]} extra={extra[:8]}")


def _contains_forbidden_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in P7_R54_CLR_PROHIBITED_PAYLOAD_OR_QUESTION_FIELD_REFS:
                return True
            if _contains_forbidden_key(child):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_key(child) for child in value)
    return False


def _assert_common_base(
    data: Mapping[str, Any], *, schema_version: str, policy_section: str, source: str, allowed_true_false_flags: frozenset[str] | None = None
) -> None:
    allowed = allowed_true_false_flags or frozenset()
    if data.get("schema_version") != schema_version:
        raise ValueError(f"{source} schema version changed")
    if data.get("phase") != P7_PHASE or data.get("current_phase") != "P7":
        raise ValueError(f"{source} phase changed")
    if data.get("step") != P7_R54_CLR_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R54_CLR_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("policy_kind") != P7_R54_CLR_POLICY_KIND:
        raise ValueError(f"{source} policy kind changed")
    if data.get("policy_section") != policy_section or data.get("operation_step_ref") != policy_section:
        raise ValueError(f"{source} policy section changed")
    if data.get("source_mode") != P7_SOURCE_MODE:
        raise ValueError(f"{source} source mode changed")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} git flags must stay false")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must remain body-free")
    for nested_key in ("public_contract", "r54_clr_no_touch_contract", "body_free_markers"):
        nested = safe_mapping(data.get(nested_key))
        if not nested or any(value is True for value in nested.values()):
            raise ValueError(f"{source} {nested_key} must contain only false markers")
    for false_key in clr03.P7_R54_CLR_FALSE_FLAG_REFS:
        if false_key in allowed:
            continue
        if data.get(false_key) is not False:
            raise ValueError(f"{source} must keep {false_key}=False")
    if _contains_forbidden_key(data):
        raise ValueError(f"{source} contains forbidden body/question/path/hash key")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)


def _assert_current_refs(data: Mapping[str, Any], *, source: str) -> None:
    if safe_mapping(data.get("operation_current_refs")) != clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError(f"{source} current refs changed")
    if data.get("operation_current_refs_are_actual_review_basis") is not True:
        raise ValueError(f"{source} must use current refs as actual review basis")
    if data.get("operation_current_refs_used_as_actual_review_basis") is not True:
        raise ValueError(f"{source} must mark current refs used as basis")
    if data.get("actual_review_basis_ref") != clr03.P7_R54_CLR_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError(f"{source} actual review basis changed")
    if data.get("all_required_current_refs_present") is not True:
        raise ValueError(f"{source} must keep all current refs present")


def _float_score(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _case_refs(rows: Sequence[Mapping[str, Any]], field: str) -> list[str]:
    return [clean_identifier(row.get(field), max_length=180) for row in rows]


def _unique_non_empty(values: Sequence[str], *, required_count: int) -> bool:
    return len(values) == required_count and len(set(values)) == required_count and all(bool(item) for item in values)


def _count_by(rows: Sequence[Mapping[str, Any]], field: str) -> dict[str, int]:
    return dict(Counter(clean_identifier(row.get(field), default="unknown", max_length=180) for row in rows))


def _counter_from_ids(rows: Sequence[Mapping[str, Any]], field: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        for item in row.get(field) or []:
            ident = clean_identifier(item, max_length=180)
            if ident:
                counter[ident] += 1
    return dict(counter)


def _axis_averages(rows: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    if not rows:
        return {axis: 0.0 for axis in P7_R54_CLR12_RATING_AXIS_REFS}
    out: dict[str, float] = {}
    for axis in P7_R54_CLR12_RATING_AXIS_REFS:
        values = [float(safe_mapping(row.get("axis_scores")).get(axis) or 0.0) for row in rows]
        out[axis] = round(sum(values) / len(values), 4)
    return out


def _below_target_axis_refs(scores: Mapping[str, Any]) -> list[str]:
    out: list[str] = []
    for axis in P7_R54_CLR12_RATING_AXIS_REFS:
        score = _float_score(scores.get(axis))
        if score is None or score < float(P7_R54_CLR12_RATING_AXIS_TARGET_THRESHOLDS[axis]):
            out.append(axis)
    return out


def _axis_average(scores: Mapping[str, Any]) -> float:
    values = [float(scores.get(axis) or 0.0) for axis in P7_R54_CLR12_RATING_AXIS_REFS]
    return round(sum(values) / len(values), 4)


def _axis_min(scores: Mapping[str, Any]) -> float:
    return min(float(scores.get(axis) or 0.0) for axis in P7_R54_CLR12_RATING_AXIS_REFS)


def _axis_max(scores: Mapping[str, Any]) -> float:
    return max(float(scores.get(axis) or 0.0) for axis in P7_R54_CLR12_RATING_AXIS_REFS)


def _bodyfree_false_row_markers() -> dict[str, bool]:
    return {
        "reviewer_free_text_included": False,
        "reviewer_note_included": False,
        "reviewer_notes_included": False,
        "raw_body_included": False,
        "returned_emlis_body_included": False,
        "history_surface_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        "local_absolute_path_included": False,
        "body_hash_included": False,
        "packet_content_included": False,
        "terminal_output_body_included": False,
        "machine_auto_score_used": False,
        "machine_metrics_used_for_readfeel": False,
    }


def _assert_rating_row(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R54_CLR12_RATING_ROW_REQUIRED_FIELD_REFS, source="P7-R54-CLR12 rating row")
    if data.get("schema_version") != P7_R54_CLR12_RATING_ROW_SCHEMA_VERSION:
        raise ValueError("P7-R54-CLR12 rating row schema version changed")
    if data.get("rating_row_is_bodyfree") is not True or data.get("selection_only_source_row") is not True or data.get("body_free") is not True:
        raise ValueError("P7-R54-CLR12 rating row must remain body-free selection-source row")
    scores = safe_mapping(data.get("axis_scores"))
    if tuple(scores.keys()) != P7_R54_CLR12_RATING_AXIS_REFS:
        raise ValueError("P7-R54-CLR12 rating axis refs changed")
    if data.get("axis_score_count") != len(P7_R54_CLR12_RATING_AXIS_REFS):
        raise ValueError("P7-R54-CLR12 rating axis count changed")
    for axis in P7_R54_CLR12_RATING_AXIS_REFS:
        score = _float_score(scores.get(axis))
        if score is None or not P7_R54_CLR12_RATING_SCORE_MIN <= score <= P7_R54_CLR12_RATING_SCORE_MAX:
            raise ValueError("P7-R54-CLR12 rating score out of range")
        if score not in P7_R54_CLR12_SCORE_OPTION_REFS:
            raise ValueError("P7-R54-CLR12 rating score outside frozen option refs")
    if safe_mapping(data.get("target_thresholds")) != P7_R54_CLR12_RATING_AXIS_TARGET_THRESHOLDS:
        raise ValueError("P7-R54-CLR12 target thresholds changed")
    below = _below_target_axis_refs(scores)
    if data.get("below_target_axis_refs") != below or data.get("below_target_axis_count") != len(below):
        raise ValueError("P7-R54-CLR12 below-target refs changed")
    if data.get("verdict") not in P7_R54_CLR12_VERDICT_OPTION_REFS:
        raise ValueError("P7-R54-CLR12 verdict option changed")
    if not set(data.get("readfeel_blocker_ids") or []).issubset(set(P7_R54_CLR12_READFEEL_BLOCKER_ID_REFS)):
        raise ValueError("P7-R54-CLR12 readfeel blocker id outside frozen options")
    if not set(data.get("execution_blocker_ids") or []).issubset(set(P7_R54_CLR12_EXECUTION_BLOCKER_ID_REFS)):
        raise ValueError("P7-R54-CLR12 execution blocker id outside frozen options")
    if data.get("readfeel_blocker_count") != len(data.get("readfeel_blocker_ids") or []):
        raise ValueError("P7-R54-CLR12 readfeel blocker count changed")
    if data.get("execution_blocker_count") != len(data.get("execution_blocker_ids") or []):
        raise ValueError("P7-R54-CLR12 execution blocker count changed")
    if data.get("rating_source_ref") != P7_R54_CLR12_RATING_ROW_SOURCE_REF:
        raise ValueError("P7-R54-CLR12 rating source ref changed")
    if data.get("verdict_blocker_consistency_ref") != P7_R54_CLR12_VERDICT_BLOCKER_CONSISTENT_REF:
        raise ValueError("P7-R54-CLR12 verdict/blocker consistency ref changed")
    for false_key, expected in _bodyfree_false_row_markers().items():
        if data.get(false_key) is not expected:
            raise ValueError(f"P7-R54-CLR12 rating row must keep {false_key}=False")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_clr12_rating_row")
    return True


def _build_rating_row_from_sanitized_row(source: Mapping[str, Any], *, review_session_id: str) -> dict[str, Any]:
    src = safe_mapping(source)
    scores = safe_mapping(src.get("axis_scores"))
    axis_scores = {axis: float(scores.get(axis)) for axis in P7_R54_CLR12_RATING_AXIS_REFS}
    below = _below_target_axis_refs(axis_scores)
    readfeel_blockers = dedupe_identifiers(src.get("readfeel_blocker_ids") or [], limit=20, max_length=180)
    execution_blockers = dedupe_identifiers(src.get("execution_blocker_ids") or [], limit=20, max_length=180)
    row = {
        "schema_version": P7_R54_CLR12_RATING_ROW_SCHEMA_VERSION,
        "rating_row_ref": f"r54clr12-rating-row-{int(src.get('case_index') or 0):03d}",
        "review_result_row_ref": clean_identifier(src.get("review_result_row_ref"), default="review_result_row_ref_missing", max_length=180),
        "selection_row_ref": clean_identifier(src.get("selection_row_ref"), default="selection_row_ref_missing", max_length=180),
        "review_session_id": review_session_id,
        "case_ref_id": clean_identifier(src.get("case_ref_id"), default="case_ref_missing", max_length=180),
        "blind_case_id": clean_identifier(src.get("blind_case_id"), default="blind_case_missing", max_length=180),
        "packet_ref_id": clean_identifier(src.get("packet_ref_id"), default="packet_ref_missing", max_length=180),
        "case_index": int(src.get("case_index") or 0),
        "case_role_family_ref": clean_identifier(src.get("case_role_family_ref"), default="case_role_family_ref_missing", max_length=180),
        "plan_tier_context_ref": clean_identifier(src.get("plan_tier_context_ref"), default="plan_tier_context_ref_missing", max_length=180),
        "reviewer_ref": clean_identifier(src.get("reviewer_ref"), default="reviewer_ref_missing", max_length=120),
        "reviewed_at_ref": clean_identifier(src.get("reviewed_at_ref"), default="coarse_reviewed_at_ref_20260627", max_length=180),
        "axis_scores": axis_scores,
        "axis_score_count": len(P7_R54_CLR12_RATING_AXIS_REFS),
        "axis_score_average": _axis_average(axis_scores),
        "average_score": _axis_average(axis_scores),
        "axis_score_min": _axis_min(axis_scores),
        "axis_score_max": _axis_max(axis_scores),
        "target_thresholds": dict(P7_R54_CLR12_RATING_AXIS_TARGET_THRESHOLDS),
        "below_target_axis_refs": below,
        "below_target_axis_count": len(below),
        "overall_read_feeling_ref": clean_identifier(src.get("overall_read_feeling_ref"), default="felt_not_reviewable", max_length=160),
        "verdict": clean_identifier(src.get("verdict"), default="NOT_REVIEWABLE", max_length=80),
        "sanitized_reason_ids": dedupe_identifiers(src.get("sanitized_reason_ids") or [], limit=20, max_length=180),
        "readfeel_blocker_ids": readfeel_blockers,
        "readfeel_blocker_count": len(readfeel_blockers),
        "execution_blocker_ids": execution_blockers,
        "execution_blocker_count": len(execution_blockers),
        "question_need_primary_class": clean_identifier(src.get("question_need_primary_class"), default="insufficient_material_execution_blocker", max_length=180),
        "ambiguity_kind_refs": dedupe_identifiers(src.get("ambiguity_kind_refs") or [], limit=20, max_length=180),
        "one_question_fit_ref": clean_identifier(src.get("one_question_fit_ref"), default="insufficient_material", max_length=180),
        "repair_required_refs": dedupe_identifiers(src.get("repair_required_refs") or [], limit=20, max_length=180),
        "plan_candidate_flags": {key: bool(safe_mapping(src.get("plan_candidate_flags")).get(key) is True) for key in clr11.P7_R54_CLR11_PLAN_CANDIDATE_FLAG_REFS},
        "rating_source_ref": P7_R54_CLR12_RATING_ROW_SOURCE_REF,
        "verdict_blocker_consistency_ref": P7_R54_CLR12_VERDICT_BLOCKER_CONSISTENT_REF,
        "pass_requires_no_blocker": True,
        "red_or_repair_requires_blocker_or_reason": True,
        "rating_row_is_bodyfree": True,
        "selection_only_source_row": True,
        **_bodyfree_false_row_markers(),
        "body_free": True,
    }
    _assert_rating_row(row)
    return row


def _rating_consistency_issue_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
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
            issues.append({"issue_id": "r54_clr12_pass_with_any_blocker_detected", "rating_row_ref": rating_row_ref})
        if verdict == "PASS" and below_target_axis_refs:
            issues.append({"issue_id": "r54_clr12_pass_below_axis_target_detected", "rating_row_ref": rating_row_ref})
        if verdict in {"REPAIR_REQUIRED", "RED"} and not readfeel_blockers and not reason_ids:
            issues.append({"issue_id": "r54_clr12_red_or_repair_without_blocker_or_reason_detected", "rating_row_ref": rating_row_ref})
    return issues


def build_p7_r54_clr12_rating_row_normalization(
    *,
    sanitized_review_result_row_intake: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_clr12_rating_row_normalization",
) -> dict[str, Any]:
    """Normalize CLR11 sanitized selection rows into body-free CLR12 rating rows."""
    clr11_material = safe_mapping(sanitized_review_result_row_intake) if sanitized_review_result_row_intake is not None else clr11.build_p7_r54_clr11_sanitized_review_result_row_intake()
    clr11.assert_p7_r54_clr11_sanitized_review_result_row_intake_contract(clr11_material)
    allows_next = bool(
        clr11_material.get("sanitized_review_result_intake_status") == clr11.P7_R54_CLR11_INTAKE_READY_STATUS_REF
        and clr11_material.get("rating_row_normalization_allowed_next") is True
        and clr11_material.get("next_required_step") == P7_R54_CLR12_STEP_REF
    )
    review_session_id = _safe_review_session_id(clr11_material.get("review_session_id"))
    blockers: list[str] = []
    rows_source = [safe_mapping(row) for row in (clr11_material.get("sanitized_review_result_rows") or [])] if allows_next else []
    normalized_rows: list[dict[str, Any]] = []
    if not allows_next:
        blockers.append("clr11_sanitized_review_result_row_intake_not_ready_for_rating_normalization")
    else:
        try:
            normalized_rows = [_build_rating_row_from_sanitized_row(row, review_session_id=review_session_id) for row in rows_source]
        except (TypeError, ValueError) as exc:
            blockers.append(clean_identifier(str(exc), default="rating_row_normalization_failed", max_length=180))
            normalized_rows = []
    if allows_next and len(normalized_rows) != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("rating_row_count_must_be_24")
    if allows_next and _case_refs(normalized_rows, "case_ref_id") != list(clr11_material.get("case_ref_ids") or []):
        blockers.append("rating_row_case_refs_must_match_sanitized_intake")
    if allows_next and _case_refs(normalized_rows, "packet_ref_id") != list(clr11_material.get("packet_ref_ids") or []):
        blockers.append("rating_row_packet_refs_must_match_sanitized_intake")
    if allows_next and _case_refs(normalized_rows, "selection_row_ref") != list(clr11_material.get("selection_row_refs") or []):
        blockers.append("rating_row_selection_refs_must_match_sanitized_intake")
    consistency_issues = _rating_consistency_issue_rows(normalized_rows) if allows_next else []
    if consistency_issues:
        blockers.append("rating_row_verdict_blocker_consistency_failed")
    execution_blockers = dedupe_identifiers([*blockers, *(clr11_material.get("open_execution_blocker_ids") or [])], limit=100, max_length=180)
    ready = bool(allows_next and len(normalized_rows) == clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT and not execution_blockers)
    rows = normalized_rows if ready else []
    rating_refs = _case_refs(rows, "rating_row_ref")
    packet_refs = _case_refs(rows, "packet_ref_id")
    case_refs = _case_refs(rows, "case_ref_id")
    blind_ids = _case_refs(rows, "blind_case_id")
    selection_refs = _case_refs(rows, "selection_row_ref")
    reviewer_refs = dedupe_identifiers(_case_refs(rows, "reviewer_ref"), limit=8, max_length=120)
    below_unique = dedupe_identifiers([axis for row in rows for axis in (row.get("below_target_axis_refs") or [])], limit=20, max_length=180)
    reason_refs = [P7_R54_CLR12_READY_REASON_REF] if ready else dedupe_identifiers([P7_R54_CLR12_RATING_NORMALIZATION_BLOCKED_STATUS_REF, *execution_blockers], limit=100, max_length=180)
    material = {
        "schema_version": P7_R54_CLR12_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_CLR_STEP,
        "scope": P7_R54_CLR_SCOPE,
        "policy_kind": P7_R54_CLR_POLICY_KIND,
        "policy_section": P7_R54_CLR12_STEP_REF,
        "operation_step_ref": P7_R54_CLR12_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_clr12_rating_row_normalization", max_length=220),
        "review_session_id": review_session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "clr11_schema_version": clr11.P7_R54_CLR11_SANITIZED_REVIEW_RESULT_ROW_INTAKE_SCHEMA_VERSION,
        "clr11_material_ref": clean_identifier(clr11_material.get("material_id"), default="p7_r54_clr11_sanitized_review_result_row_intake", max_length=220),
        "clr11_next_required_step": clean_identifier(clr11_material.get("next_required_step"), default=clr11.P7_R54_CLR11_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220),
        "clr11_sanitized_review_result_intake_status": clean_identifier(clr11_material.get("sanitized_review_result_intake_status"), default=clr11.P7_R54_CLR11_INTAKE_BLOCKED_STATUS_REF, max_length=180),
        "clr11_rating_row_normalization_allowed_next": bool(clr11_material.get("rating_row_normalization_allowed_next") is True),
        "existing_op12_helper_ref": "build_p7_r54_op12_rating_row_normalization",
        "existing_op12_schema_version": r54op.P7_R54_OPERATION_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        "existing_ev10_schema_version": r54ev.P7_R54_EV10_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        "existing_op12_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_ev10_current_refs": dict(r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "existing_op12_current_refs_are_historical_here": True,
        "existing_ev10_current_refs_are_historical_here": True,
        "existing_op12_reused_as_actual_rating_basis": False,
        "existing_ev10_reused_as_actual_rating_basis": False,
        "existing_op12_structural_contract_reused": True,
        "existing_ev10_structural_contract_reused": True,
        "required_case_count": clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "sanitized_review_result_row_count": int(clr11_material.get("sanitized_review_result_row_count") or 0) if allows_next else 0,
        "rating_row_normalization_status": P7_R54_CLR12_RATING_NORMALIZATION_READY_STATUS_REF if ready else P7_R54_CLR12_RATING_NORMALIZATION_BLOCKED_STATUS_REF,
        "rating_row_normalization_ref": P7_R54_CLR12_RATING_ROW_NORMALIZATION_REF if ready else "rating_row_normalization_not_ready_bodyfree",
        "rating_row_normalization_reason_refs": reason_refs,
        "execution_blocker_ids": execution_blockers,
        "open_execution_blocker_ids": execution_blockers,
        "rating_rows": rows,
        "rating_row_count": len(rows),
        "reviewed_case_count": len(rows),
        "rating_row_refs": rating_refs,
        "rating_row_ref_count": len(rating_refs),
        "rating_row_refs_unique": _unique_non_empty(rating_refs, required_count=clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT) if ready else False,
        "packet_ref_ids": packet_refs,
        "packet_ref_count": len(packet_refs),
        "packet_ref_ids_unique": _unique_non_empty(packet_refs, required_count=clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT) if ready else False,
        "case_ref_ids": case_refs,
        "case_ref_count": len(case_refs),
        "case_ref_ids_unique": _unique_non_empty(case_refs, required_count=clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT) if ready else False,
        "blind_case_ids": blind_ids,
        "blind_case_id_count": len(blind_ids),
        "blind_case_ids_unique": _unique_non_empty(blind_ids, required_count=clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT) if ready else False,
        "selection_row_refs": selection_refs,
        "selection_row_ref_count": len(selection_refs),
        "selection_row_refs_unique": _unique_non_empty(selection_refs, required_count=clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT) if ready else False,
        "reviewer_ref_ids": reviewer_refs,
        "reviewer_ref_count": len(reviewer_refs),
        "rating_row_schema_version": P7_R54_CLR12_RATING_ROW_SCHEMA_VERSION,
        "rating_row_required_field_refs": list(P7_R54_CLR12_RATING_ROW_REQUIRED_FIELD_REFS),
        "rating_axis_refs": list(P7_R54_CLR12_RATING_AXIS_REFS),
        "rating_axis_target_thresholds": dict(P7_R54_CLR12_RATING_AXIS_TARGET_THRESHOLDS),
        "rating_score_min": P7_R54_CLR12_RATING_SCORE_MIN,
        "rating_score_max": P7_R54_CLR12_RATING_SCORE_MAX,
        "allowed_score_option_refs": list(P7_R54_CLR12_SCORE_OPTION_REFS),
        "allowed_verdict_refs": list(P7_R54_CLR12_VERDICT_OPTION_REFS),
        "readfeel_blocker_id_refs": list(P7_R54_CLR12_READFEEL_BLOCKER_ID_REFS),
        "execution_blocker_id_refs": list(P7_R54_CLR12_EXECUTION_BLOCKER_ID_REFS),
        "all_axes_present": ready,
        "axis_score_range_valid": ready,
        "verdict_allowed": ready,
        "below_target_axis_refs_calculated": ready,
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
        "rating_case_ref_sets_match_sanitized_intake": ready,
        "verdict_counts": _count_by(rows, "verdict") if ready else {},
        "overall_read_feeling_counts": _count_by(rows, "overall_read_feeling_ref") if ready else {},
        "axis_score_averages": _axis_averages(rows) if ready else {},
        "below_target_axis_refs": below_unique,
        "below_target_axis_count": len(below_unique),
        "below_target_rating_row_count": sum(1 for row in rows if row.get("below_target_axis_refs")) if ready else 0,
        "rating_consistency_issue_rows": consistency_issues if ready is False and consistency_issues else [],
        "rating_consistency_issue_count": 0 if ready else len(consistency_issues),
        "pass_with_any_blocker_detected": any(item.get("issue_id") == "r54_clr12_pass_with_any_blocker_detected" for item in consistency_issues),
        "pass_below_axis_target_detected": any(item.get("issue_id") == "r54_clr12_pass_below_axis_target_detected" for item in consistency_issues),
        "red_or_repair_without_blocker_or_reason_detected": any(item.get("issue_id") == "r54_clr12_red_or_repair_without_blocker_or_reason_detected" for item in consistency_issues),
        "readfeel_blocker_row_candidate_count": sum(len(row.get("readfeel_blocker_ids") or []) for row in rows) if ready else 0,
        "execution_blocker_row_candidate_count": sum(len(row.get("execution_blocker_ids") or []) for row in rows) if ready else 0,
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
        "p5_finalization_blocked_here": True,
        **_current_ref_fields(),
        "implemented_steps": list(P7_R54_CLR12_IMPLEMENTED_STEPS if ready else (clr11_material.get("implemented_steps") or [])),
        "not_yet_implemented_steps": list(P7_R54_CLR12_NOT_YET_IMPLEMENTED_STEPS if ready else (clr11_material.get("not_yet_implemented_steps") or [])),
        "next_required_step": P7_R54_CLR13_STEP_REF if ready else P7_R54_CLR12_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_clr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_except("actual_rating_rows_materialized_here"),
    }
    material["actual_rating_rows_materialized_here"] = ready
    return material


def assert_p7_r54_clr12_rating_row_normalization_contract(data: Mapping[str, Any]) -> bool:
    material = safe_mapping(data)
    _assert_required_fields(material, required=P7_R54_CLR12_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS, source="P7-R54-CLR12")
    _assert_common_base(
        material,
        schema_version=P7_R54_CLR12_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        policy_section=P7_R54_CLR12_STEP_REF,
        source="P7-R54-CLR12",
        allowed_true_false_flags=P7_R54_CLR12_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    _assert_current_refs(material, source="P7-R54-CLR12")
    if safe_mapping(material.get("existing_op12_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("P7-R54-CLR12 OP12 refs changed")
    if safe_mapping(material.get("existing_ev10_current_refs")) != r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("P7-R54-CLR12 EV10 refs changed")
    for key in (
        "existing_op12_current_refs_are_historical_here",
        "existing_ev10_current_refs_are_historical_here",
        "existing_op12_structural_contract_reused",
        "existing_ev10_structural_contract_reused",
    ):
        if material.get(key) is not True:
            raise ValueError(f"P7-R54-CLR12 must keep {key}=True")
    for key in ("existing_op12_reused_as_actual_rating_basis", "existing_ev10_reused_as_actual_rating_basis"):
        if material.get(key) is not False:
            raise ValueError(f"P7-R54-CLR12 must keep {key}=False")
    if material.get("required_case_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-CLR12 required case count changed")
    status = material.get("rating_row_normalization_status")
    if status not in P7_R54_CLR12_ALLOWED_NORMALIZATION_STATUS_REFS:
        raise ValueError("P7-R54-CLR12 rating normalization status changed")
    blockers = dedupe_identifiers(material.get("execution_blocker_ids") or [], limit=100, max_length=180)
    if material.get("open_execution_blocker_ids") != blockers:
        raise ValueError("P7-R54-CLR12 blockers mismatch")
    ready = status == P7_R54_CLR12_RATING_NORMALIZATION_READY_STATUS_REF
    if ready:
        if material.get("clr11_rating_row_normalization_allowed_next") is not True or material.get("clr11_next_required_step") != P7_R54_CLR12_STEP_REF:
            raise ValueError("P7-R54-CLR12 ready normalization requires ready CLR11")
        if blockers:
            raise ValueError("P7-R54-CLR12 ready normalization must not carry blockers")
        rows = [safe_mapping(row) for row in (material.get("rating_rows") or [])]
        if len(rows) != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-CLR12 ready normalization must contain 24 rating rows")
        for row in rows:
            _assert_rating_row(row)
        if material.get("rating_row_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-CLR12 rating row count changed")
        for key in (
            "rating_row_refs_unique",
            "packet_ref_ids_unique",
            "case_ref_ids_unique",
            "blind_case_ids_unique",
            "selection_row_refs_unique",
            "all_axes_present",
            "axis_score_range_valid",
            "verdict_allowed",
            "below_target_axis_refs_calculated",
            "rating_rows_are_bodyfree",
            "all_required_rating_rows_present",
            "rating_case_ref_sets_match_sanitized_intake",
            "readfeel_blocker_execution_blocker_ingestion_allowed_next",
            "rating_rows_normalized_here",
            "actual_rating_rows_materialized_here",
        ):
            if material.get(key) is not True:
                raise ValueError(f"P7-R54-CLR12 ready normalization must keep {key}=True")
        if material.get("actual_review_evidence_complete") is not False or material.get("actual_question_need_observation_rows_materialized_here") is not False:
            raise ValueError("P7-R54-CLR12 must not complete review evidence or question rows")
        if material.get("question_observation_row_count") != 0 or material.get("disposal_verified") is not False:
            raise ValueError("P7-R54-CLR12 must not materialize question/disposal evidence")
        if tuple(material.get("implemented_steps") or ()) != P7_R54_CLR12_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR12 implemented steps changed")
        if tuple(material.get("not_yet_implemented_steps") or ()) != P7_R54_CLR12_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR12 not-yet steps changed")
        if material.get("next_required_step") != P7_R54_CLR13_STEP_REF:
            raise ValueError("P7-R54-CLR12 ready normalization must point to CLR13")
    else:
        if material.get("rating_rows") != [] or material.get("rating_row_count") != 0:
            raise ValueError("P7-R54-CLR12 blocked normalization must not expose rating rows")
        if material.get("actual_rating_rows_materialized_here") is not False or material.get("rating_rows_normalized_here") is not False:
            raise ValueError("P7-R54-CLR12 blocked normalization must not materialize rows")
        if not blockers or material.get("next_required_step") != P7_R54_CLR12_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-CLR12 blocked normalization must carry blockers and repair next step")
    return True


def build_p7_r54_clr13_readfeel_blocker_row_bodyfree(*, rating_row: Mapping[str, Any], blocker_id: Any, blocker_status_ref: Any = "open") -> dict[str, Any]:
    row = safe_mapping(rating_row)
    _assert_rating_row(row)
    blocker_ref = clean_identifier(blocker_id, default="", max_length=180)
    if blocker_ref not in P7_R54_CLR13_READFEEL_BLOCKER_ID_REFS:
        raise ValueError("P7-R54-CLR13 readfeel blocker row must use frozen readfeel blocker id")
    status_ref = clean_identifier(blocker_status_ref, default="open", max_length=40)
    if status_ref not in P7_R54_CLR13_BLOCKER_STATUS_REFS:
        raise ValueError("P7-R54-CLR13 blocker status changed")
    out = {
        "schema_version": P7_R54_CLR13_READFEEL_BLOCKER_ROW_SCHEMA_VERSION,
        "blocker_row_ref": f"r54clr13-readfeel-blocker-{clean_identifier(row.get('rating_row_ref'), default='rating-row', max_length=120)}-{blocker_ref}",
        "review_session_id": _safe_review_session_id(row.get("review_session_id")),
        "rating_row_ref": clean_identifier(row.get("rating_row_ref"), default="rating_row_missing", max_length=180),
        "packet_ref_id": clean_identifier(row.get("packet_ref_id"), default="packet_ref_missing", max_length=180),
        "blind_case_id": clean_identifier(row.get("blind_case_id"), default="blind_case_missing", max_length=180),
        "case_ref_id": clean_identifier(row.get("case_ref_id"), default="case_ref_missing", max_length=180),
        "case_index": int(row.get("case_index") or 0),
        "case_role_family_ref": clean_identifier(row.get("case_role_family_ref"), default="case_role_family_missing", max_length=180),
        "reviewer_ref": clean_identifier(row.get("reviewer_ref"), default="reviewer_ref_missing", max_length=120),
        "readfeel_blocker_id": blocker_ref,
        "blocker_kind_ref": P7_R54_CLR13_READFEEL_BLOCKER_KIND_REF,
        "blocker_status_ref": status_ref,
        "source_verdict": clean_identifier(row.get("verdict"), default="NOT_REVIEWABLE", max_length=80),
        **_bodyfree_false_row_markers(),
        "body_free": True,
    }
    assert_p7_r54_clr13_readfeel_blocker_row_bodyfree_contract(out)
    return out


def assert_p7_r54_clr13_readfeel_blocker_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R54_CLR13_READFEEL_BLOCKER_ROW_REQUIRED_FIELD_REFS, source="P7-R54-CLR13 readfeel blocker row")
    if data.get("schema_version") != P7_R54_CLR13_READFEEL_BLOCKER_ROW_SCHEMA_VERSION:
        raise ValueError("P7-R54-CLR13 readfeel blocker row schema changed")
    if data.get("readfeel_blocker_id") not in P7_R54_CLR13_READFEEL_BLOCKER_ID_REFS:
        raise ValueError("P7-R54-CLR13 readfeel blocker id outside frozen options")
    if data.get("blocker_kind_ref") != P7_R54_CLR13_READFEEL_BLOCKER_KIND_REF:
        raise ValueError("P7-R54-CLR13 readfeel blocker kind changed")
    if data.get("blocker_status_ref") not in P7_R54_CLR13_BLOCKER_STATUS_REFS:
        raise ValueError("P7-R54-CLR13 readfeel blocker status changed")
    for false_key, expected in _bodyfree_false_row_markers().items():
        if data.get(false_key) is not expected:
            raise ValueError(f"P7-R54-CLR13 readfeel row must keep {false_key}=False")
    if data.get("body_free") is not True:
        raise ValueError("P7-R54-CLR13 readfeel blocker row must be body-free")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_clr13_readfeel_blocker_row")
    return True


def build_p7_r54_clr13_execution_blocker_row_bodyfree(
    *,
    source_ref: Any,
    execution_blocker_id: Any,
    review_session_id: Any = P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID,
    packet_ref_id: Any = "execution_blocker_no_packet_ref",
    blind_case_id: Any = "execution_blocker_no_blind_case_id",
    case_ref_id: Any = "execution_blocker_no_case_ref_id",
    case_index: Any = 0,
    case_role_family_ref: Any = "operation_execution_boundary",
    execution_blocker_status_ref: Any = "open",
) -> dict[str, Any]:
    blocker_ref = clean_identifier(execution_blocker_id, default="", max_length=180)
    if blocker_ref not in P7_R54_CLR13_EXECUTION_BLOCKER_ID_REFS:
        raise ValueError("P7-R54-CLR13 execution blocker row must use canonical execution blocker id")
    status_ref = clean_identifier(execution_blocker_status_ref, default="open", max_length=40)
    if status_ref not in P7_R54_CLR13_BLOCKER_STATUS_REFS:
        raise ValueError("P7-R54-CLR13 execution blocker row status changed")
    out = {
        "schema_version": P7_R54_CLR13_EXECUTION_BLOCKER_ROW_SCHEMA_VERSION,
        "execution_blocker_row_ref": f"r54clr13-execution-blocker-{clean_identifier(source_ref, default='source-ref', max_length=120)}-{blocker_ref}",
        "review_session_id": _safe_review_session_id(review_session_id),
        "source_ref": clean_identifier(source_ref, default="execution_blocker_source_ref", max_length=180),
        "packet_ref_id": clean_identifier(packet_ref_id, default="execution_blocker_no_packet_ref", max_length=180),
        "blind_case_id": clean_identifier(blind_case_id, default="execution_blocker_no_blind_case_id", max_length=180),
        "case_ref_id": clean_identifier(case_ref_id, default="execution_blocker_no_case_ref_id", max_length=180),
        "case_index": int(case_index or 0),
        "case_role_family_ref": clean_identifier(case_role_family_ref, default="operation_execution_boundary", max_length=180),
        "execution_blocker_id": blocker_ref,
        "execution_blocker_kind_ref": P7_R54_CLR13_EXECUTION_BLOCKER_KIND_REF,
        "execution_blocker_status_ref": status_ref,
        "execution_blocker_does_not_assign_readfeel_verdict": True,
        **_bodyfree_false_row_markers(),
        "body_free": True,
    }
    assert_p7_r54_clr13_execution_blocker_row_bodyfree_contract(out)
    return out


def assert_p7_r54_clr13_execution_blocker_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R54_CLR13_EXECUTION_BLOCKER_ROW_REQUIRED_FIELD_REFS, source="P7-R54-CLR13 execution blocker row")
    if data.get("schema_version") != P7_R54_CLR13_EXECUTION_BLOCKER_ROW_SCHEMA_VERSION:
        raise ValueError("P7-R54-CLR13 execution blocker row schema changed")
    if data.get("execution_blocker_id") not in P7_R54_CLR13_EXECUTION_BLOCKER_ID_REFS:
        raise ValueError("P7-R54-CLR13 execution blocker id outside frozen options")
    if data.get("execution_blocker_kind_ref") != P7_R54_CLR13_EXECUTION_BLOCKER_KIND_REF:
        raise ValueError("P7-R54-CLR13 execution blocker kind changed")
    if data.get("execution_blocker_status_ref") not in P7_R54_CLR13_BLOCKER_STATUS_REFS:
        raise ValueError("P7-R54-CLR13 execution blocker status changed")
    if data.get("execution_blocker_does_not_assign_readfeel_verdict") is not True:
        raise ValueError("P7-R54-CLR13 execution blocker must not assign readfeel verdict")
    for false_key, expected in _bodyfree_false_row_markers().items():
        if data.get(false_key) is not expected:
            raise ValueError(f"P7-R54-CLR13 execution row must keep {false_key}=False")
    if data.get("body_free") is not True:
        raise ValueError("P7-R54-CLR13 execution blocker row must be body-free")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_clr13_execution_blocker_row")
    return True


def _blocker_rows_from_rating_rows(rating_rows: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    readfeel_rows: list[dict[str, Any]] = []
    execution_rows: list[dict[str, Any]] = []
    for rating_row in rating_rows:
        row = safe_mapping(rating_row)
        _assert_rating_row(row)
        for blocker_id in row.get("readfeel_blocker_ids") or []:
            readfeel_rows.append(build_p7_r54_clr13_readfeel_blocker_row_bodyfree(rating_row=row, blocker_id=blocker_id))
        for blocker_id in row.get("execution_blocker_ids") or []:
            execution_rows.append(
                build_p7_r54_clr13_execution_blocker_row_bodyfree(
                    source_ref=clean_identifier(row.get("rating_row_ref"), default="rating_row", max_length=180),
                    execution_blocker_id=blocker_id,
                    review_session_id=row.get("review_session_id"),
                    packet_ref_id=row.get("packet_ref_id"),
                    blind_case_id=row.get("blind_case_id"),
                    case_ref_id=row.get("case_ref_id"),
                    case_index=row.get("case_index"),
                    case_role_family_ref=row.get("case_role_family_ref"),
                )
            )
    return readfeel_rows, execution_rows


def _single_id_counts(rows: Sequence[Mapping[str, Any]], field: str) -> dict[str, int]:
    return dict(Counter(clean_identifier(row.get(field), max_length=180) for row in rows if clean_identifier(row.get(field), max_length=180)))


def build_p7_r54_clr13_readfeel_blocker_execution_blocker_ingestion(
    *,
    rating_row_normalization: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_clr13_readfeel_blocker_execution_blocker_ingestion",
) -> dict[str, Any]:
    """Ingest body-free readfeel/execution blockers from normalized rating rows."""
    clr12 = safe_mapping(rating_row_normalization) if rating_row_normalization is not None else build_p7_r54_clr12_rating_row_normalization()
    assert_p7_r54_clr12_rating_row_normalization_contract(clr12)
    allows_next = bool(
        clr12.get("rating_row_normalization_status") == P7_R54_CLR12_RATING_NORMALIZATION_READY_STATUS_REF
        and clr12.get("readfeel_blocker_execution_blocker_ingestion_allowed_next") is True
        and clr12.get("next_required_step") == P7_R54_CLR13_STEP_REF
    )
    rating_rows = [safe_mapping(row) for row in (clr12.get("rating_rows") or [])] if allows_next else []
    readfeel_rows, row_execution_rows = _blocker_rows_from_rating_rows(rating_rows) if allows_next else ([], [])
    blockers = [] if allows_next else dedupe_identifiers(["rating_row_normalization_not_ready_for_blocker_ingestion", *(clr12.get("open_execution_blocker_ids") or [])], limit=100, max_length=180)
    operation_execution_rows = [
        build_p7_r54_clr13_execution_blocker_row_bodyfree(
            source_ref=clean_identifier(clr12.get("material_id"), default="p7_r54_clr12_rating_row_normalization", max_length=180),
            execution_blocker_id=blocker,
            review_session_id=clr12.get("review_session_id"),
        )
        for blocker in blockers
        if blocker in P7_R54_CLR13_EXECUTION_BLOCKER_ID_REFS
    ]
    execution_rows = row_execution_rows if allows_next else operation_execution_rows
    open_readfeel_count = sum(1 for row in readfeel_rows if row.get("blocker_status_ref") == "open")
    open_execution_count = sum(1 for row in execution_rows if row.get("execution_blocker_status_ref") == "open")
    ready = bool(allows_next)
    reason_refs = [P7_R54_CLR13_READY_REASON_REF] if ready else dedupe_identifiers([P7_R54_CLR13_BLOCKER_INGESTION_BLOCKED_STATUS_REF, *blockers], limit=100, max_length=180)
    material = {
        "schema_version": P7_R54_CLR13_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_CLR_STEP,
        "scope": P7_R54_CLR_SCOPE,
        "policy_kind": P7_R54_CLR_POLICY_KIND,
        "policy_section": P7_R54_CLR13_STEP_REF,
        "operation_step_ref": P7_R54_CLR13_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_clr13_readfeel_blocker_execution_blocker_ingestion", max_length=220),
        "review_session_id": _safe_review_session_id(clr12.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "clr12_schema_version": P7_R54_CLR12_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        "clr12_material_ref": clean_identifier(clr12.get("material_id"), default="p7_r54_clr12_rating_row_normalization", max_length=220),
        "clr12_next_required_step": clean_identifier(clr12.get("next_required_step"), default=P7_R54_CLR12_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220),
        "clr12_rating_row_normalization_status": clean_identifier(clr12.get("rating_row_normalization_status"), default=P7_R54_CLR12_RATING_NORMALIZATION_BLOCKED_STATUS_REF, max_length=180),
        "clr12_blocker_ingestion_allowed_next": bool(clr12.get("readfeel_blocker_execution_blocker_ingestion_allowed_next") is True),
        "existing_op13_helper_ref": "build_p7_r54_op13_readfeel_blocker_execution_blocker_ingestion",
        "existing_op13_schema_version": r54op.P7_R54_OPERATION_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION,
        "existing_ev11_schema_version": r54ev.P7_R54_EV11_BLOCKER_INGESTION_SCHEMA_VERSION,
        "existing_op13_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_ev11_current_refs": dict(r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "existing_op13_current_refs_are_historical_here": True,
        "existing_ev11_current_refs_are_historical_here": True,
        "existing_op13_reused_as_actual_blocker_basis": False,
        "existing_ev11_reused_as_actual_blocker_basis": False,
        "existing_op13_structural_contract_reused": True,
        "existing_ev11_structural_contract_reused": True,
        "required_case_count": clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "rating_row_count": len(rating_rows),
        "blocker_ingestion_status": P7_R54_CLR13_BLOCKER_INGESTION_READY_STATUS_REF if ready else P7_R54_CLR13_BLOCKER_INGESTION_BLOCKED_STATUS_REF,
        "blocker_ingestion_ref": P7_R54_CLR13_BLOCKER_INGESTION_REF if ready else "readfeel_execution_blocker_ingestion_not_ready_bodyfree",
        "blocker_ingestion_reason_refs": reason_refs,
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        "readfeel_blocker_row_schema_version": P7_R54_CLR13_READFEEL_BLOCKER_ROW_SCHEMA_VERSION,
        "execution_blocker_row_schema_version": P7_R54_CLR13_EXECUTION_BLOCKER_ROW_SCHEMA_VERSION,
        "readfeel_blocker_row_required_field_refs": list(P7_R54_CLR13_READFEEL_BLOCKER_ROW_REQUIRED_FIELD_REFS),
        "execution_blocker_row_required_field_refs": list(P7_R54_CLR13_EXECUTION_BLOCKER_ROW_REQUIRED_FIELD_REFS),
        "readfeel_blocker_id_refs": list(P7_R54_CLR13_READFEEL_BLOCKER_ID_REFS),
        "execution_blocker_id_refs": list(P7_R54_CLR13_EXECUTION_BLOCKER_ID_REFS),
        "blocker_status_refs": list(P7_R54_CLR13_BLOCKER_STATUS_REFS),
        "rating_rows": rating_rows,
        "readfeel_blocker_rows": readfeel_rows,
        "execution_blocker_rows": execution_rows,
        "readfeel_blocker_row_count": len(readfeel_rows),
        "execution_blocker_row_count": len(execution_rows),
        "open_readfeel_blocker_count": open_readfeel_count,
        "open_execution_blocker_count": open_execution_count,
        "readfeel_blocker_counts": _single_id_counts(readfeel_rows, "readfeel_blocker_id"),
        "execution_blocker_counts": _single_id_counts(execution_rows, "execution_blocker_id"),
        "rating_packet_ref_ids": _case_refs(rating_rows, "packet_ref_id"),
        "rating_case_ref_ids": _case_refs(rating_rows, "case_ref_id"),
        "rating_blind_case_ids": _case_refs(rating_rows, "blind_case_id"),
        "readfeel_blocker_rows_normalized": ready,
        "execution_blocker_rows_normalized": ready,
        "readfeel_and_execution_blockers_separated": True,
        "execution_blocker_not_mixed_into_readfeel_verdict": True,
        "execution_blockers_do_not_assign_readfeel_verdict": True,
        "execution_blocker_cases_do_not_create_rating_rows": True,
        "execution_blocker_open_blocks_p5_confirmed_candidate": True,
        "p5_confirmed_candidate_blocked_by_open_execution_blockers": open_execution_count > 0,
        "rating_missing_maps_to_execution_blocker_not_red": True,
        "local_root_missing_maps_to_execution_blocker_not_red": True,
        "disposal_failed_maps_to_execution_blocker_not_red": True,
        "body_free_leak_maps_to_execution_blocker_not_red": True,
        "rating_rows_preserved_from_clr12": ready,
        "question_need_observation_normalization_allowed_next": ready,
        "actual_rating_rows_materialized_here": bool(ready and clr12.get("actual_rating_rows_materialized_here") is True),
        "actual_blocker_rows_materialized_here": ready,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_review_evidence_complete": False,
        "question_observation_row_count": 0,
        "disposal_verified": False,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        **_current_ref_fields(),
        "implemented_steps": list(P7_R54_CLR13_IMPLEMENTED_STEPS if ready else (clr12.get("implemented_steps") or [])),
        "not_yet_implemented_steps": list(P7_R54_CLR13_NOT_YET_IMPLEMENTED_STEPS if ready else (clr12.get("not_yet_implemented_steps") or [])),
        "next_required_step": P7_R54_CLR14_STEP_REF if ready else P7_R54_CLR13_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_clr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_except("actual_rating_rows_materialized_here"),
    }
    material["actual_rating_rows_materialized_here"] = bool(ready and clr12.get("actual_rating_rows_materialized_here") is True)
    assert_p7_r54_clr13_readfeel_blocker_execution_blocker_ingestion_contract(material)
    return material


def assert_p7_r54_clr13_readfeel_blocker_execution_blocker_ingestion_contract(data: Mapping[str, Any]) -> bool:
    material = safe_mapping(data)
    _assert_required_fields(material, required=P7_R54_CLR13_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION_REQUIRED_FIELD_REFS, source="P7-R54-CLR13")
    _assert_common_base(
        material,
        schema_version=P7_R54_CLR13_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION,
        policy_section=P7_R54_CLR13_STEP_REF,
        source="P7-R54-CLR13",
        allowed_true_false_flags=P7_R54_CLR13_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    _assert_current_refs(material, source="P7-R54-CLR13")
    if safe_mapping(material.get("existing_op13_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("P7-R54-CLR13 OP13 refs changed")
    if safe_mapping(material.get("existing_ev11_current_refs")) != r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("P7-R54-CLR13 EV11 refs changed")
    for key in (
        "existing_op13_current_refs_are_historical_here",
        "existing_ev11_current_refs_are_historical_here",
        "existing_op13_structural_contract_reused",
        "existing_ev11_structural_contract_reused",
        "readfeel_and_execution_blockers_separated",
        "execution_blocker_not_mixed_into_readfeel_verdict",
        "execution_blockers_do_not_assign_readfeel_verdict",
        "execution_blocker_cases_do_not_create_rating_rows",
        "execution_blocker_open_blocks_p5_confirmed_candidate",
        "rating_missing_maps_to_execution_blocker_not_red",
        "local_root_missing_maps_to_execution_blocker_not_red",
        "disposal_failed_maps_to_execution_blocker_not_red",
        "body_free_leak_maps_to_execution_blocker_not_red",
    ):
        if material.get(key) is not True:
            raise ValueError(f"P7-R54-CLR13 must keep {key}=True")
    for key in ("existing_op13_reused_as_actual_blocker_basis", "existing_ev11_reused_as_actual_blocker_basis"):
        if material.get(key) is not False:
            raise ValueError(f"P7-R54-CLR13 must keep {key}=False")
    if material.get("required_case_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-CLR13 required case count changed")
    status = material.get("blocker_ingestion_status")
    if status not in P7_R54_CLR13_ALLOWED_BLOCKER_INGESTION_STATUS_REFS:
        raise ValueError("P7-R54-CLR13 blocker ingestion status changed")
    blockers = dedupe_identifiers(material.get("execution_blocker_ids") or [], limit=100, max_length=180)
    if material.get("open_execution_blocker_ids") != blockers:
        raise ValueError("P7-R54-CLR13 materialization blockers mismatch")
    for row in material.get("readfeel_blocker_rows") or []:
        assert_p7_r54_clr13_readfeel_blocker_row_bodyfree_contract(safe_mapping(row))
    for row in material.get("execution_blocker_rows") or []:
        assert_p7_r54_clr13_execution_blocker_row_bodyfree_contract(safe_mapping(row))
    if material.get("readfeel_blocker_row_count") != len(material.get("readfeel_blocker_rows") or []):
        raise ValueError("P7-R54-CLR13 readfeel row count mismatch")
    if material.get("execution_blocker_row_count") != len(material.get("execution_blocker_rows") or []):
        raise ValueError("P7-R54-CLR13 execution row count mismatch")
    if material.get("open_readfeel_blocker_count") != sum(1 for row in material.get("readfeel_blocker_rows") or [] if safe_mapping(row).get("blocker_status_ref") == "open"):
        raise ValueError("P7-R54-CLR13 open readfeel count mismatch")
    if material.get("open_execution_blocker_count") != sum(1 for row in material.get("execution_blocker_rows") or [] if safe_mapping(row).get("execution_blocker_status_ref") == "open"):
        raise ValueError("P7-R54-CLR13 open execution count mismatch")
    if material.get("p5_confirmed_candidate_blocked_by_open_execution_blockers") is not (material.get("open_execution_blocker_count") > 0):
        raise ValueError("P7-R54-CLR13 P5 confirmed blocker flag must reflect open execution blockers")
    if material.get("actual_question_need_observation_rows_materialized_here") is not False or material.get("actual_review_evidence_complete") is not False:
        raise ValueError("P7-R54-CLR13 must not complete question/review evidence")
    if material.get("question_observation_row_count") != 0 or material.get("disposal_verified") is not False:
        raise ValueError("P7-R54-CLR13 must not materialize question/disposal evidence")
    ready = status == P7_R54_CLR13_BLOCKER_INGESTION_READY_STATUS_REF
    if ready:
        if material.get("clr12_blocker_ingestion_allowed_next") is not True or material.get("clr12_next_required_step") != P7_R54_CLR13_STEP_REF:
            raise ValueError("P7-R54-CLR13 ready ingestion requires ready CLR12")
        if blockers:
            raise ValueError("P7-R54-CLR13 ready ingestion must not carry materialization blockers")
        if material.get("rating_row_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-CLR13 ready ingestion requires 24 rating rows")
        if material.get("readfeel_blocker_rows_normalized") is not True or material.get("execution_blocker_rows_normalized") is not True:
            raise ValueError("P7-R54-CLR13 ready ingestion must normalize blocker rows")
        if material.get("actual_rating_rows_materialized_here") is not True or material.get("actual_blocker_rows_materialized_here") is not True:
            raise ValueError("P7-R54-CLR13 ready ingestion must preserve rating rows and materialize blocker rows")
        if material.get("question_need_observation_normalization_allowed_next") is not True:
            raise ValueError("P7-R54-CLR13 ready ingestion must allow CLR14 next")
        if tuple(material.get("implemented_steps") or ()) != P7_R54_CLR13_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR13 implemented steps changed")
        if tuple(material.get("not_yet_implemented_steps") or ()) != P7_R54_CLR13_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR13 not-yet steps changed")
        if material.get("next_required_step") != P7_R54_CLR14_STEP_REF:
            raise ValueError("P7-R54-CLR13 ready ingestion must point to CLR14")
    else:
        if material.get("actual_blocker_rows_materialized_here") is not False:
            raise ValueError("P7-R54-CLR13 blocked ingestion must not materialize blocker rows")
        if material.get("readfeel_blocker_rows_normalized") is not False or material.get("execution_blocker_rows_normalized") is not False:
            raise ValueError("P7-R54-CLR13 blocked ingestion must not normalize blocker rows")
        if not blockers or material.get("next_required_step") != P7_R54_CLR13_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-CLR13 blocked ingestion must carry blockers and repair next step")
    return True


build_p7_r54_current_snapshot_local_run_clr12_rating_row_normalization = build_p7_r54_clr12_rating_row_normalization
assert_p7_r54_current_snapshot_local_run_clr12_rating_row_normalization_contract = assert_p7_r54_clr12_rating_row_normalization_contract
build_p7_r54_current_snapshot_rating_row_normalization_bodyfree = build_p7_r54_clr12_rating_row_normalization
assert_p7_r54_current_snapshot_rating_row_normalization_bodyfree_contract = assert_p7_r54_clr12_rating_row_normalization_contract

build_p7_r54_current_snapshot_local_run_clr13_readfeel_blocker_execution_blocker_ingestion = build_p7_r54_clr13_readfeel_blocker_execution_blocker_ingestion
assert_p7_r54_current_snapshot_local_run_clr13_readfeel_blocker_execution_blocker_ingestion_contract = assert_p7_r54_clr13_readfeel_blocker_execution_blocker_ingestion_contract
build_p7_r54_current_snapshot_readfeel_blocker_execution_blocker_ingestion_bodyfree = build_p7_r54_clr13_readfeel_blocker_execution_blocker_ingestion
assert_p7_r54_current_snapshot_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract = assert_p7_r54_clr13_readfeel_blocker_execution_blocker_ingestion_contract

build_clr12_rating_row_normalization = build_p7_r54_clr12_rating_row_normalization
assert_clr12_rating_row_normalization_contract = assert_p7_r54_clr12_rating_row_normalization_contract
build_clr13_readfeel_blocker_row_bodyfree = build_p7_r54_clr13_readfeel_blocker_row_bodyfree
assert_clr13_readfeel_blocker_row_bodyfree_contract = assert_p7_r54_clr13_readfeel_blocker_row_bodyfree_contract
build_clr13_execution_blocker_row_bodyfree = build_p7_r54_clr13_execution_blocker_row_bodyfree
assert_clr13_execution_blocker_row_bodyfree_contract = assert_p7_r54_clr13_execution_blocker_row_bodyfree_contract
build_clr13_readfeel_blocker_execution_blocker_ingestion = build_p7_r54_clr13_readfeel_blocker_execution_blocker_ingestion
assert_clr13_readfeel_blocker_execution_blocker_ingestion_contract = assert_p7_r54_clr13_readfeel_blocker_execution_blocker_ingestion_contract

__all__ = (
    "P7_R54_CLR12_RATING_ROW_SCHEMA_VERSION",
    "P7_R54_CLR12_RATING_ROW_NORMALIZATION_SCHEMA_VERSION",
    "P7_R54_CLR13_READFEEL_BLOCKER_ROW_SCHEMA_VERSION",
    "P7_R54_CLR13_EXECUTION_BLOCKER_ROW_SCHEMA_VERSION",
    "P7_R54_CLR13_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION",
    "P7_R54_CLR12_STEP_REF",
    "P7_R54_CLR13_STEP_REF",
    "P7_R54_CLR14_STEP_REF",
    "P7_R54_CLR12_IMPLEMENTED_STEPS",
    "P7_R54_CLR12_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_CLR13_IMPLEMENTED_STEPS",
    "P7_R54_CLR13_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_CLR12_RATING_ROW_REQUIRED_FIELD_REFS",
    "P7_R54_CLR12_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS",
    "P7_R54_CLR13_READFEEL_BLOCKER_ROW_REQUIRED_FIELD_REFS",
    "P7_R54_CLR13_EXECUTION_BLOCKER_ROW_REQUIRED_FIELD_REFS",
    "P7_R54_CLR13_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION_REQUIRED_FIELD_REFS",
    "P7_R54_CLR13_BLOCKER_INGESTION_REQUIRED_FIELD_REFS",
    "build_p7_r54_clr12_rating_row_normalization",
    "assert_p7_r54_clr12_rating_row_normalization_contract",
    "build_p7_r54_clr13_readfeel_blocker_row_bodyfree",
    "assert_p7_r54_clr13_readfeel_blocker_row_bodyfree_contract",
    "build_p7_r54_clr13_execution_blocker_row_bodyfree",
    "assert_p7_r54_clr13_execution_blocker_row_bodyfree_contract",
    "build_p7_r54_clr13_readfeel_blocker_execution_blocker_ingestion",
    "assert_p7_r54_clr13_readfeel_blocker_execution_blocker_ingestion_contract",
)
