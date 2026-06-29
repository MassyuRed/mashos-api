# -*- coding: utf-8 -*-
"""P7-R54 current snapshot local review run CLR14-CLR15 helpers.

CLR14 normalizes question-need observations from body-free rating rows. It keeps
question need as enum/count/class only: no question text, no draft question text,
no raw input, no returned body, no history surface, no local path, and no hash.

CLR15 guards rating rows and question-need observation rows against the main
escape route this run is meant to prevent: P5 readfeel/repair problems being
reclassified as P8 question material. These helpers do not touch API/DB/RN,
runtime, public response keys, P8 implementation, disposal, or release state.
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
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr12_clr13_20260627 as clr13


P7_R54_CLR14_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr14_question_need_observation_row.bodyfree.v1"
)
P7_R54_CLR14_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr14_question_need_observation_normalization.bodyfree.v1"
)
P7_R54_CLR15_RATING_QUESTION_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr15_rating_question_consistency_issue_row.bodyfree.v1"
)
P7_R54_CLR15_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr15_rating_question_consistency_guard.bodyfree.v1"
)
P7_R54_CLR14_SCHEMA_VERSION: Final = P7_R54_CLR14_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION
P7_R54_CLR14_ROW_SCHEMA_VERSION: Final = P7_R54_CLR14_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION
P7_R54_CLR15_SCHEMA_VERSION: Final = P7_R54_CLR15_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION
P7_R54_CLR15_ROW_SCHEMA_VERSION: Final = P7_R54_CLR15_RATING_QUESTION_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION

P7_R54_CLR_STEP: Final = clr03.P7_R54_CLR_STEP
P7_R54_CLR_SCOPE: Final = clr03.P7_R54_CLR_SCOPE
P7_R54_CLR_POLICY_KIND: Final = clr03.P7_R54_CLR_POLICY_KIND
P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID: Final = clr03.P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID
P7_R54_CLR14_STEP_REF: Final = clr03.P7_R54_CLR14_STEP_REF
P7_R54_CLR15_STEP_REF: Final = clr03.P7_R54_CLR15_STEP_REF
P7_R54_CLR16_STEP_REF: Final = clr03.P7_R54_CLR16_STEP_REF

P7_R54_CLR14_QUESTION_OBSERVATION_NORMALIZATION_READY_STATUS_REF: Final = "QUESTION_NEED_OBSERVATION_ROWS_NORMALIZED_BODYFREE"
P7_R54_CLR14_QUESTION_OBSERVATION_NORMALIZATION_BLOCKED_STATUS_REF: Final = "QUESTION_NEED_OBSERVATION_NORMALIZATION_BLOCKED"
P7_R54_CLR14_ALLOWED_NORMALIZATION_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_CLR14_QUESTION_OBSERVATION_NORMALIZATION_READY_STATUS_REF,
    P7_R54_CLR14_QUESTION_OBSERVATION_NORMALIZATION_BLOCKED_STATUS_REF,
)
P7_R54_CLR14_QUESTION_OBSERVATION_NORMALIZATION_REF: Final = "r54_clr14_question_need_observation_normalization_bodyfree_20260627"
P7_R54_CLR14_READY_REASON_REF: Final = "r54_clr14_24_question_need_observation_rows_normalized_bodyfree"
P7_R54_CLR14_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "R54-CLR-14_blocked_until_question_need_observation_rows_are_normalizable"

P7_R54_CLR15_CONSISTENCY_GUARD_READY_STATUS_REF: Final = "RATING_QUESTION_CONSISTENCY_GUARD_READY_BODYFREE"
P7_R54_CLR15_CONSISTENCY_GUARD_BLOCKED_STATUS_REF: Final = "RATING_QUESTION_CONSISTENCY_GUARD_BLOCKED"
P7_R54_CLR15_ALLOWED_CONSISTENCY_GUARD_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_CLR15_CONSISTENCY_GUARD_READY_STATUS_REF,
    P7_R54_CLR15_CONSISTENCY_GUARD_BLOCKED_STATUS_REF,
)
P7_R54_CLR15_CONSISTENCY_GUARD_REF: Final = "r54_clr15_rating_question_consistency_guard_bodyfree_20260627"
P7_R54_CLR15_READY_REASON_REF: Final = "r54_clr15_rating_question_consistency_guard_passed_bodyfree"
P7_R54_CLR15_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "R54-CLR-15_blocked_until_rating_question_consistency_issues_are_repaired"

P7_R54_CLR14_QUESTION_NEED_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = clr11.P7_R54_CLR11_QUESTION_NEED_PRIMARY_CLASS_REFS
P7_R54_CLR14_AMBIGUITY_KIND_OPTION_REFS: Final[tuple[str, ...]] = clr11.P7_R54_CLR11_AMBIGUITY_KIND_OPTION_REFS
P7_R54_CLR14_ONE_QUESTION_FIT_OPTION_REFS: Final[tuple[str, ...]] = clr11.P7_R54_CLR11_ONE_QUESTION_FIT_OPTION_REFS
P7_R54_CLR14_REPAIR_REQUIRED_OPTION_REFS: Final[tuple[str, ...]] = clr11.P7_R54_CLR11_REPAIR_REQUIRED_OPTION_REFS
P7_R54_CLR14_PLAN_CANDIDATE_FLAG_REFS: Final[tuple[str, ...]] = clr11.P7_R54_CLR11_PLAN_CANDIDATE_FLAG_REFS
P7_R54_CLR14_P8_MATERIAL_CANDIDATE_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = (
    "question_may_reduce_overread_risk",
    "plus_single_question_candidate_later",
    "premium_deep_dive_candidate_later",
)
P7_R54_CLR14_NOT_QUESTION_REPAIR_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = (
    "not_question_emlis_readfeel_repair_required",
    "not_question_p5_surface_repair_required",
    "not_question_gate_boundary_required",
)

P7_R54_CLR15_CONSISTENCY_ISSUE_ID_REFS: Final[tuple[str, ...]] = (
    "r54_clr15_yellow_red_repair_or_below_target_blocks_p5_confirmed_candidate",
    "r54_clr15_repair_required_with_p8_material_candidate",
    "r54_clr15_pass_with_not_question_repair_required",
    "r54_clr15_readfeel_blocker_blocks_p5_confirmed_candidate",
    "r54_clr15_not_question_repair_not_p8_material",
    "r54_clr15_insufficient_material_with_pass_or_no_execution_blocker",
    "r54_clr15_rating_question_case_ref_set_mismatch",
    "r54_clr15_p8_material_candidate_question_text_violation",
)
P7_R54_CLR15_CONSISTENCY_ISSUE_KIND_REFS: Final[tuple[str, ...]] = (
    "rating_question_observation_semantic_mismatch",
    "p5_repair_hidden_by_question_candidate",
    "p5_inconclusive_or_execution_boundary_mismatch",
    "rating_question_case_integrity_issue",
    "bodyfree_question_text_boundary_violation",
)
P7_R54_CLR15_DECISION_DIRECTION_REFS: Final[tuple[str, ...]] = (
    "continue_after_consistency_guard",
    "p5_repair_return_required_later",
    "keep_as_p5_or_emlis_or_gate_repair_not_p8_material",
    "r54_operation_inconclusive_required_later",
    "mark_inconclusive_until_execution_material_is_repaired",
    "rating_question_row_repair_required",
    "bodyfree_boundary_repair_required",
)

P7_R54_CLR14_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*clr13.P7_R54_CLR13_IMPLEMENTED_STEPS, P7_R54_CLR14_STEP_REF)
P7_R54_CLR14_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = clr03.P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR01[13:]
P7_R54_CLR15_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_CLR14_IMPLEMENTED_STEPS, P7_R54_CLR15_STEP_REF)
P7_R54_CLR15_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = clr03.P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR01[14:]

P7_R54_CLR14_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[frozenset[str]] = frozenset(
    {"actual_rating_rows_materialized_here", "actual_question_need_observation_rows_materialized_here"}
)
P7_R54_CLR15_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[frozenset[str]] = P7_R54_CLR14_ALLOWED_TRUE_FALSE_FLAG_REFS

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

P7_R54_CLR14_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "question_observation_row_ref",
    "review_session_id",
    "review_result_row_ref",
    "selection_row_ref",
    "rating_row_ref",
    "packet_ref_id",
    "blind_case_id",
    "case_ref_id",
    "case_index",
    "case_role_family_ref",
    "plan_tier_context_ref",
    "reviewer_ref",
    "reviewed_at_ref",
    "question_need_primary_class",
    "ambiguity_kind_refs",
    "ambiguity_kind_count",
    "one_question_fit_ref",
    "repair_required_refs",
    "repair_required_ref_count",
    "plan_candidate_flags",
    "p8_material_candidate_requested",
    "p8_material_candidate_allowed",
    "p8_material_candidate_safe_for_handoff",
    "p8_design_material_candidate_requested",
    "p8_design_material_candidate_allowed",
    "p8_material_candidate_safe_for_later_design",
    "p8_implementation_spec_finalized_here",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "not_question_repair_required",
    "insufficient_material_execution_blocker",
    "question_observation_row_is_bodyfree",
    "question_text_included",
    "draft_question_text_included",
    "reviewer_free_text_included",
    "reviewer_note_included",
    "reviewer_notes_included",
    "raw_body_included",
    "returned_emlis_body_included",
    "history_surface_included",
    "comment_text_included",
    "local_path_included",
    "local_absolute_path_included",
    "body_hash_included",
    "packet_content_included",
    "terminal_output_body_included",
    "machine_auto_score_used",
    "machine_metrics_used_for_readfeel",
    "body_free",
)

P7_R54_CLR14_QUESTION_NEED_OBSERVATION_NORMALIZATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *clr03.P7_R54_CLR_COMMON_REQUIRED_FIELD_REFS,
    "clr13_schema_version",
    "clr13_material_ref",
    "clr13_next_required_step",
    "clr13_blocker_ingestion_status",
    "clr13_question_observation_normalization_allowed_next",
    "clr12_schema_version",
    "clr12_material_ref",
    "clr12_rating_row_normalization_status",
    "existing_op14_helper_ref",
    "existing_op14_schema_version",
    "existing_ev12_schema_version",
    "existing_op14_operation_current_refs",
    "existing_ev12_current_refs",
    "existing_op14_current_refs_are_historical_here",
    "existing_ev12_current_refs_are_historical_here",
    "existing_op14_reused_as_actual_question_observation_basis",
    "existing_ev12_reused_as_actual_question_observation_basis",
    "existing_op14_reused_as_actual_normalization_basis",
    "existing_ev12_reused_as_actual_normalization_basis",
    "existing_op14_structural_contract_reused",
    "existing_ev12_structural_contract_reused",
    "required_case_count",
    "rating_row_count",
    "question_observation_normalization_status",
    "question_observation_normalization_ref",
    "question_observation_normalization_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "rating_rows",
    "question_observation_rows",
    "question_observation_row_count",
    "question_observation_row_refs",
    "question_observation_row_ref_count",
    "question_observation_row_refs_unique",
    "case_ref_ids",
    "case_ref_count",
    "case_ref_ids_unique",
    "packet_ref_ids",
    "packet_ref_count",
    "packet_ref_ids_unique",
    "blind_case_ids",
    "blind_case_id_count",
    "blind_case_ids_unique",
    "question_observation_row_schema_version",
    "question_observation_row_required_field_refs",
    "question_need_primary_class_refs",
    "ambiguity_kind_refs",
    "one_question_fit_refs",
    "repair_required_ref_refs",
    "plan_candidate_flag_refs",
    "p8_material_candidate_primary_class_refs",
    "not_question_repair_primary_class_refs",
    "question_need_observation_rows_are_bodyfree",
    "question_text_absent_for_all_rows",
    "draft_question_text_absent_for_all_rows",
    "reviewer_free_text_absent_for_all_rows",
    "raw_body_absent_for_all_rows",
    "returned_emlis_body_absent_for_all_rows",
    "history_surface_absent_for_all_rows",
    "comment_text_absent_for_all_rows",
    "local_path_absent_for_all_rows",
    "body_hash_absent_for_all_rows",
    "question_text_included_allowed",
    "draft_question_text_included_allowed",
    "reviewer_free_text_included_allowed",
    "raw_body_allowed",
    "returned_emlis_body_allowed",
    "history_surface_allowed",
    "local_path_allowed",
    "body_hash_allowed",
    "question_text_or_draft_text_saved_here",
    "p8_question_implementation_spec_finalized_here",
    "question_trigger_logic_implemented",
    "question_trigger_logic_implemented_here",
    "question_api_implemented",
    "question_db_schema_implemented",
    "question_rn_ui_implemented",
    "question_response_key_implemented",
    "question_storage_schema_implemented",
    "question_answer_persistence_implemented",
    "question_plan_guard_implemented",
    "row_case_ref_sets_match_rating_rows",
    "all_required_question_need_observation_rows_present",
    "question_observation_rows_normalized_here",
    "primary_class_ambiguity_one_question_fit_are_canonical_refs",
    "not_question_repair_rows_misclassified_as_p8_material",
    "p5_weakness_not_hidden_by_question_candidates_here",
    "question_need_primary_class_counts",
    "ambiguity_kind_counts",
    "one_question_fit_counts",
    "repair_required_counts",
    "plan_candidate_flag_counts",
    "p8_material_candidate_requested_row_count",
    "p8_material_candidate_allowed_row_count",
    "p8_material_candidate_row_count",
    "p8_material_candidate_allowed_primary_class_counts",
    "not_question_repair_required_count",
    "insufficient_material_execution_blocker_count",
    "rating_rows_preserved_from_clr13",
    "blocker_rows_preserved_from_clr13",
    "rating_question_consistency_guard_allowed_next",
    "p8_implementation_spec_finalized_here",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_review_evidence_complete",
    "disposal_verified",
    "human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    *clr03.P7_R54_CLR_CURRENT_REF_REQUIRED_FIELD_REFS,
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *clr03.P7_R54_CLR_NO_TOUCH_BODYFREE_REQUIRED_FIELD_REFS,
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    *clr03.P7_R54_CLR_FALSE_FLAG_REFS,
)

P7_R54_CLR15_RATING_QUESTION_CONSISTENCY_ISSUE_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "consistency_issue_row_ref",
    "review_session_id",
    "rating_row_ref",
    "question_observation_row_ref",
    "packet_ref_id",
    "blind_case_id",
    "case_ref_id",
    "case_index",
    "case_role_family_ref",
    "issue_id",
    "issue_kind_ref",
    "decision_direction_ref",
    "issue_status_ref",
    "source_verdict",
    "question_need_primary_class",
    "below_target_axis_refs",
    "readfeel_blocker_ids",
    "repair_required_refs",
    "p8_material_candidate_requested",
    "p8_material_candidate_allowed",
    "not_question_repair_required",
    "insufficient_material_execution_blocker",
    "question_text_included",
    "draft_question_text_included",
    "reviewer_free_text_included",
    "reviewer_note_included",
    "reviewer_notes_included",
    "raw_body_included",
    "returned_emlis_body_included",
    "history_surface_included",
    "local_path_included",
    "local_absolute_path_included",
    "body_hash_included",
    "packet_content_included",
    "terminal_output_body_included",
    "body_free",
)

P7_R54_CLR15_RATING_QUESTION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *clr03.P7_R54_CLR_COMMON_REQUIRED_FIELD_REFS,
    "clr14_schema_version",
    "clr14_material_ref",
    "clr14_next_required_step",
    "clr14_question_observation_normalization_status",
    "clr14_consistency_guard_allowed_next",
    "clr12_schema_version",
    "clr12_material_ref",
    "clr12_rating_row_normalization_status",
    "existing_op15_helper_ref",
    "existing_op15_schema_version",
    "existing_ev13_schema_version",
    "existing_op15_operation_current_refs",
    "existing_ev13_current_refs",
    "existing_op15_current_refs_are_historical_here",
    "existing_ev13_current_refs_are_historical_here",
    "existing_op15_reused_as_actual_consistency_basis",
    "existing_ev13_reused_as_actual_consistency_basis",
    "existing_op15_structural_contract_reused",
    "existing_ev13_structural_contract_reused",
    "required_case_count",
    "rating_question_consistency_guard_status",
    "rating_question_consistency_guard_ref",
    "rating_question_consistency_guard_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "rating_rows",
    "question_observation_rows",
    "rating_row_count",
    "question_observation_row_count",
    "rating_question_case_ref_sets_match",
    "all_required_rating_and_question_rows_present",
    "rating_question_consistency_issue_row_schema_version",
    "rating_question_consistency_issue_row_required_field_refs",
    "rating_question_consistency_issue_rows",
    "consistency_issue_rows",
    "consistency_issue_count",
    "consistency_issue_id_refs",
    "consistency_issue_kind_refs",
    "decision_direction_refs",
    "yellow_red_repair_or_below_target_block_count",
    "repair_required_with_p8_material_candidate_count",
    "pass_with_not_question_repair_required_count",
    "readfeel_blocker_block_count",
    "not_question_repair_not_p8_material_count",
    "insufficient_material_with_pass_or_no_execution_blocker_count",
    "case_ref_set_mismatch_count",
    "p8_material_candidate_question_text_violation_count",
    "open_readfeel_blocker_count",
    "below_target_axis_count",
    "insufficient_material_execution_blocker_count",
    "consistency_issue_direction_counts",
    "p5_confirmed_candidate_blocked_by_consistency_issues",
    "p5_decision_candidate_not_materialized_here",
    "rating_question_consistency_guard_passed",
    "issues_route_to_p5_repair_return_or_inconclusive_later",
    "p8_material_candidates_do_not_hide_p5_repair_here",
    "p5_repair_required_not_reclassified_as_p8_material",
    "not_question_repair_not_promoted_to_p8_material",
    "question_text_absent",
    "draft_question_text_absent",
    "ready_for_pause_abort_expiration_protocol",
    "rating_rows_preserved_from_clr12",
    "question_observation_rows_preserved_from_clr14",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_review_evidence_complete",
    "disposal_verified",
    "human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    *clr03.P7_R54_CLR_CURRENT_REF_REQUIRED_FIELD_REFS,
    "implemented_steps",
    "not_yet_implemented_steps",
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


def _single_id_counts(rows: Sequence[Mapping[str, Any]], field: str) -> dict[str, int]:
    return dict(Counter(clean_identifier(row.get(field), max_length=180) for row in rows if clean_identifier(row.get(field), max_length=180)))


def _plan_candidate_flag_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = {flag: 0 for flag in P7_R54_CLR14_PLAN_CANDIDATE_FLAG_REFS}
    for row in rows:
        flags = safe_mapping(row.get("plan_candidate_flags"))
        for flag in P7_R54_CLR14_PLAN_CANDIDATE_FLAG_REFS:
            if flags.get(flag) is True:
                counts[flag] += 1
    return counts


def _p8_allowed_primary_class_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        if row.get("p8_material_candidate_allowed") is not True:
            continue
        primary = clean_identifier(row.get("question_need_primary_class"), max_length=180)
        if primary in P7_R54_CLR14_P8_MATERIAL_CANDIDATE_PRIMARY_CLASS_REFS:
            counts[primary] = counts.get(primary, 0) + 1
    return counts


def _bodyfree_false_row_markers() -> dict[str, bool]:
    return {
        "reviewer_free_text_included": False,
        "reviewer_note_included": False,
        "reviewer_notes_included": False,
        "raw_body_included": False,
        "returned_emlis_body_included": False,
        "history_surface_included": False,
        "comment_text_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "local_path_included": False,
        "local_absolute_path_included": False,
        "body_hash_included": False,
        "packet_content_included": False,
        "terminal_output_body_included": False,
        "machine_auto_score_used": False,
        "machine_metrics_used_for_readfeel": False,
    }


def _question_plan_flags(
    *, primary_class: str, repair_required_refs: Sequence[str], source_flags: Mapping[str, Any]
) -> tuple[dict[str, bool], bool, bool, bool, bool]:
    if safe_mapping(source_flags).get("p8_implementation_spec_finalized_here") is True:
        raise ValueError("P8 implementation spec must not be finalized in P7-R54-CLR14")
    repair_refs = set(dedupe_identifiers(repair_required_refs, limit=20, max_length=160))
    repair_without_no_repair = repair_refs - {"no_repair_required"}
    not_question_repair = bool(primary_class in P7_R54_CLR14_NOT_QUESTION_REPAIR_PRIMARY_CLASS_REFS or repair_without_no_repair)
    insufficient = primary_class == "insufficient_material_execution_blocker"
    source = safe_mapping(source_flags)
    p8_requested = bool(source.get("p8_design_material_candidate") is True or primary_class in P7_R54_CLR14_P8_MATERIAL_CANDIDATE_PRIMARY_CLASS_REFS)
    p8_allowed = bool(primary_class in P7_R54_CLR14_P8_MATERIAL_CANDIDATE_PRIMARY_CLASS_REFS and not not_question_repair and not insufficient)
    flags = {flag: False for flag in P7_R54_CLR14_PLAN_CANDIDATE_FLAG_REFS}
    flags["plus_single_question_candidate_later"] = bool(source.get("plus_single_question_candidate_later") is True or primary_class == "plus_single_question_candidate_later")
    flags["premium_deep_dive_candidate_later"] = bool(source.get("premium_deep_dive_candidate_later") is True or primary_class == "premium_deep_dive_candidate_later")
    flags["p8_design_material_candidate"] = p8_allowed
    flags["p8_implementation_spec_finalized_here"] = False
    return flags, p8_requested, p8_allowed, not_question_repair, insufficient


def build_p7_r54_clr14_question_need_observation_row_bodyfree(*, rating_row: Mapping[str, Any]) -> dict[str, Any]:
    row = safe_mapping(rating_row)
    clr13._assert_rating_row(row)  # structural CLR12 row contract; keeps this wrapper thin and aligned.
    primary_class = clean_identifier(row.get("question_need_primary_class"), max_length=160)
    if primary_class not in P7_R54_CLR14_QUESTION_NEED_PRIMARY_CLASS_REFS:
        raise ValueError("P7-R54-CLR14 question observation primary class outside frozen options")
    ambiguity_refs = dedupe_identifiers(row.get("ambiguity_kind_refs") or [], limit=20, max_length=160)
    if not ambiguity_refs or not set(ambiguity_refs).issubset(set(P7_R54_CLR14_AMBIGUITY_KIND_OPTION_REFS)):
        raise ValueError("P7-R54-CLR14 ambiguity refs outside frozen options")
    one_question_fit = clean_identifier(row.get("one_question_fit_ref"), max_length=160)
    if one_question_fit not in P7_R54_CLR14_ONE_QUESTION_FIT_OPTION_REFS:
        raise ValueError("P7-R54-CLR14 one-question fit ref outside frozen options")
    repair_refs = dedupe_identifiers(row.get("repair_required_refs") or [], limit=20, max_length=160)
    if not repair_refs or not set(repair_refs).issubset(set(P7_R54_CLR14_REPAIR_REQUIRED_OPTION_REFS)):
        raise ValueError("P7-R54-CLR14 repair refs outside frozen options")
    plan_flags, p8_requested, p8_allowed, not_question_repair, insufficient = _question_plan_flags(
        primary_class=primary_class,
        repair_required_refs=repair_refs,
        source_flags=safe_mapping(row.get("plan_candidate_flags")),
    )
    out = {
        "schema_version": P7_R54_CLR14_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION,
        "question_observation_row_ref": f"r54clr14-question-row-{clean_identifier(row.get('rating_row_ref'), default='rating-row', max_length=140)}",
        "review_session_id": _safe_review_session_id(row.get("review_session_id")),
        "review_result_row_ref": clean_identifier(row.get("review_result_row_ref"), default="review_result_row_missing", max_length=180),
        "selection_row_ref": clean_identifier(row.get("selection_row_ref"), default="selection_row_missing", max_length=180),
        "rating_row_ref": clean_identifier(row.get("rating_row_ref"), default="rating_row_missing", max_length=180),
        "packet_ref_id": clean_identifier(row.get("packet_ref_id"), default="packet_ref_missing", max_length=180),
        "blind_case_id": clean_identifier(row.get("blind_case_id"), default="blind_case_missing", max_length=180),
        "case_ref_id": clean_identifier(row.get("case_ref_id"), default="case_ref_missing", max_length=180),
        "case_index": int(row.get("case_index") or 0),
        "case_role_family_ref": clean_identifier(row.get("case_role_family_ref"), default="case_role_family_missing", max_length=180),
        "plan_tier_context_ref": clean_identifier(row.get("plan_tier_context_ref"), default="plan_tier_context_missing", max_length=180),
        "reviewer_ref": clean_identifier(row.get("reviewer_ref"), default="reviewer_ref_missing", max_length=120),
        "reviewed_at_ref": clean_identifier(row.get("reviewed_at_ref"), default="reviewed_at_ref_missing", max_length=120),
        "question_need_primary_class": primary_class,
        "ambiguity_kind_refs": ambiguity_refs,
        "ambiguity_kind_count": len(ambiguity_refs),
        "one_question_fit_ref": one_question_fit,
        "repair_required_refs": repair_refs,
        "repair_required_ref_count": len(repair_refs),
        "plan_candidate_flags": plan_flags,
        "p8_material_candidate_requested": p8_requested,
        "p8_material_candidate_allowed": p8_allowed,
        "p8_material_candidate_safe_for_handoff": p8_allowed,
        "p8_design_material_candidate_requested": p8_requested,
        "p8_design_material_candidate_allowed": p8_allowed,
        "p8_material_candidate_safe_for_later_design": p8_allowed,
        "p8_implementation_spec_finalized_here": False,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "not_question_repair_required": not_question_repair,
        "insufficient_material_execution_blocker": insufficient,
        "question_observation_row_is_bodyfree": True,
        **_bodyfree_false_row_markers(),
        "body_free": True,
    }
    assert_p7_r54_clr14_question_need_observation_row_bodyfree_contract(out)
    return out


def assert_p7_r54_clr14_question_need_observation_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R54_CLR14_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS, source="P7-R54-CLR14 question row")
    if data.get("schema_version") != P7_R54_CLR14_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION:
        raise ValueError("P7-R54-CLR14 question row schema changed")
    if data.get("question_observation_row_is_bodyfree") is not True or data.get("body_free") is not True:
        raise ValueError("P7-R54-CLR14 question row must be body-free")
    primary_class = clean_identifier(data.get("question_need_primary_class"), max_length=160)
    if primary_class not in P7_R54_CLR14_QUESTION_NEED_PRIMARY_CLASS_REFS:
        raise ValueError("P7-R54-CLR14 question row primary class changed")
    ambiguity_refs = data.get("ambiguity_kind_refs") or []
    if not ambiguity_refs or not set(ambiguity_refs).issubset(set(P7_R54_CLR14_AMBIGUITY_KIND_OPTION_REFS)):
        raise ValueError("P7-R54-CLR14 question row ambiguity refs changed")
    if data.get("ambiguity_kind_count") != len(ambiguity_refs):
        raise ValueError("P7-R54-CLR14 question row ambiguity count mismatch")
    if data.get("one_question_fit_ref") not in P7_R54_CLR14_ONE_QUESTION_FIT_OPTION_REFS:
        raise ValueError("P7-R54-CLR14 question row one-question fit changed")
    repair_refs = data.get("repair_required_refs") or []
    if not repair_refs or not set(repair_refs).issubset(set(P7_R54_CLR14_REPAIR_REQUIRED_OPTION_REFS)):
        raise ValueError("P7-R54-CLR14 question row repair refs changed")
    if data.get("repair_required_ref_count") != len(repair_refs):
        raise ValueError("P7-R54-CLR14 question row repair count mismatch")
    flags = safe_mapping(data.get("plan_candidate_flags"))
    if tuple(flags.keys()) != P7_R54_CLR14_PLAN_CANDIDATE_FLAG_REFS:
        raise ValueError("P7-R54-CLR14 plan candidate flag keys changed")
    if flags.get("p8_implementation_spec_finalized_here") is not False or data.get("p8_implementation_spec_finalized_here") is not False:
        raise ValueError("P7-R54-CLR14 must not finalize P8 implementation spec")
    expected_flags, p8_requested, p8_allowed, not_question_repair, insufficient = _question_plan_flags(
        primary_class=primary_class,
        repair_required_refs=repair_refs,
        source_flags={
            **flags,
            # The normalized flag is allowed-only.  The row keeps a separate
            # requested flag so CLR15 can detect attempts to route P5/Emlis/Gate
            # repair classes into later P8 material without creating question text.
            "p8_design_material_candidate": data.get("p8_material_candidate_requested") is True,
        },
    )
    if flags != expected_flags:
        raise ValueError("P7-R54-CLR14 plan candidate flags changed")
    requested_flag = data.get("p8_material_candidate_requested")
    if requested_flag not in (True, False):
        raise ValueError("P7-R54-CLR14 P8 material requested flag must be boolean")
    if requested_flag is not p8_requested and not (requested_flag is True and not_question_repair):
        raise ValueError("P7-R54-CLR14 P8 material requested flag mismatch")
    if data.get("p8_material_candidate_allowed") is not p8_allowed or data.get("p8_material_candidate_safe_for_handoff") is not p8_allowed:
        raise ValueError("P7-R54-CLR14 P8 material allowed flag mismatch")
    if data.get("p8_design_material_candidate_requested") is not p8_requested:
        raise ValueError("P7-R54-CLR14 P8 material requested alias mismatch")
    if data.get("p8_design_material_candidate_allowed") is not p8_allowed or data.get("p8_material_candidate_safe_for_later_design") is not p8_allowed:
        raise ValueError("P7-R54-CLR14 P8 material allowed alias mismatch")
    if data.get("not_question_repair_required") is not not_question_repair:
        raise ValueError("P7-R54-CLR14 not-question repair flag mismatch")
    if data.get("insufficient_material_execution_blocker") is not insufficient:
        raise ValueError("P7-R54-CLR14 insufficient material flag mismatch")
    for false_key, expected in _bodyfree_false_row_markers().items():
        if data.get(false_key) is not expected:
            raise ValueError(f"P7-R54-CLR14 question row must keep {false_key}=False")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_clr14_question_need_observation_row")
    return True


def _question_rows_from_rating_rows(rating_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [build_p7_r54_clr14_question_need_observation_row_bodyfree(rating_row=row) for row in rating_rows]


def build_p7_r54_clr14_question_need_observation_normalization(
    *,
    readfeel_blocker_execution_blocker_ingestion: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_clr14_question_need_observation_normalization",
) -> dict[str, Any]:
    """Normalize body-free question need observation rows without question text."""
    clr13_material = (
        safe_mapping(readfeel_blocker_execution_blocker_ingestion)
        if readfeel_blocker_execution_blocker_ingestion is not None
        else clr13.build_p7_r54_clr13_readfeel_blocker_execution_blocker_ingestion()
    )
    clr13.assert_p7_r54_clr13_readfeel_blocker_execution_blocker_ingestion_contract(clr13_material)
    allows_next = bool(
        clr13_material.get("blocker_ingestion_status") == clr13.P7_R54_CLR13_BLOCKER_INGESTION_READY_STATUS_REF
        and clr13_material.get("question_need_observation_normalization_allowed_next") is True
        and clr13_material.get("next_required_step") == P7_R54_CLR14_STEP_REF
    )
    rating_rows = [safe_mapping(row) for row in (clr13_material.get("rating_rows") or [])] if allows_next else []
    blockers = [] if allows_next else dedupe_identifiers(
        [
            "blocker_ingestion_not_ready_for_question_need_observation_normalization",
            "clr13_readfeel_blocker_execution_blocker_ingestion_not_ready_for_question_observation_normalization",
            *(clr13_material.get("open_execution_blocker_ids") or []),
        ],
        limit=100,
        max_length=180,
    )
    question_rows = _question_rows_from_rating_rows(rating_rows) if allows_next else []
    rating_case_refs = _case_refs(rating_rows, "case_ref_id")
    question_case_refs = _case_refs(question_rows, "case_ref_id")
    rating_packet_refs = _case_refs(rating_rows, "packet_ref_id")
    question_packet_refs = _case_refs(question_rows, "packet_ref_id")
    row_case_refs_match = bool(question_rows) and set(question_case_refs) == set(rating_case_refs)
    row_packet_refs_match = bool(question_rows) and set(question_packet_refs) == set(rating_packet_refs)
    all_required = bool(
        len(question_rows) == clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and len(rating_rows) == clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and row_case_refs_match
        and row_packet_refs_match
    )
    if allows_next and not all_required:
        blockers = dedupe_identifiers([*blockers, "question_observation_row_set_mismatch_or_count_mismatch"], limit=100, max_length=180)
    ready = bool(allows_next and all_required and not blockers)
    reason_refs = [P7_R54_CLR14_READY_REASON_REF] if ready else dedupe_identifiers(
        [P7_R54_CLR14_QUESTION_OBSERVATION_NORMALIZATION_BLOCKED_STATUS_REF, *blockers], limit=100, max_length=180
    )
    material = {
        "schema_version": P7_R54_CLR14_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_CLR_STEP,
        "scope": P7_R54_CLR_SCOPE,
        "policy_kind": P7_R54_CLR_POLICY_KIND,
        "policy_section": P7_R54_CLR14_STEP_REF,
        "operation_step_ref": P7_R54_CLR14_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_clr14_question_need_observation_normalization", max_length=220),
        "review_session_id": _safe_review_session_id(clr13_material.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "clr13_schema_version": clr13.P7_R54_CLR13_SCHEMA_VERSION,
        "clr13_material_ref": clean_identifier(clr13_material.get("material_id"), default="p7_r54_clr13_readfeel_blocker_execution_blocker_ingestion", max_length=220),
        "clr13_next_required_step": clean_identifier(clr13_material.get("next_required_step"), default=clr13.P7_R54_CLR13_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220),
        "clr13_blocker_ingestion_status": clean_identifier(clr13_material.get("blocker_ingestion_status"), default=clr13.P7_R54_CLR13_BLOCKER_INGESTION_BLOCKED_STATUS_REF, max_length=180),
        "clr13_question_observation_normalization_allowed_next": bool(clr13_material.get("question_need_observation_normalization_allowed_next") is True),
        "clr12_schema_version": clr13.P7_R54_CLR12_SCHEMA_VERSION,
        "clr12_material_ref": clean_identifier(clr13_material.get("clr12_material_ref"), default="p7_r54_clr12_rating_row_normalization", max_length=220),
        "clr12_rating_row_normalization_status": clean_identifier(clr13_material.get("clr12_rating_row_normalization_status"), default=clr13.P7_R54_CLR12_RATING_NORMALIZATION_BLOCKED_STATUS_REF, max_length=180),
        "existing_op14_helper_ref": "build_p7_r54_op14_question_need_observation_normalization",
        "existing_op14_schema_version": r54op.P7_R54_OPERATION_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION,
        "existing_ev12_schema_version": r54ev.P7_R54_EV12_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION_SCHEMA_VERSION,
        "existing_op14_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_ev12_current_refs": dict(r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "existing_op14_current_refs_are_historical_here": True,
        "existing_ev12_current_refs_are_historical_here": True,
        "existing_op14_reused_as_actual_question_observation_basis": False,
        "existing_ev12_reused_as_actual_question_observation_basis": False,
        "existing_op14_reused_as_actual_normalization_basis": False,
        "existing_ev12_reused_as_actual_normalization_basis": False,
        "existing_op14_structural_contract_reused": True,
        "existing_ev12_structural_contract_reused": True,
        "required_case_count": clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "rating_row_count": len(rating_rows),
        "question_observation_normalization_status": P7_R54_CLR14_QUESTION_OBSERVATION_NORMALIZATION_READY_STATUS_REF if ready else P7_R54_CLR14_QUESTION_OBSERVATION_NORMALIZATION_BLOCKED_STATUS_REF,
        "question_observation_normalization_ref": P7_R54_CLR14_QUESTION_OBSERVATION_NORMALIZATION_REF if ready else "question_need_observation_normalization_not_ready_bodyfree",
        "question_observation_normalization_reason_refs": reason_refs,
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        "rating_rows": rating_rows,
        "question_observation_rows": question_rows,
        "question_observation_row_count": len(question_rows),
        "question_observation_row_refs": _case_refs(question_rows, "question_observation_row_ref"),
        "question_observation_row_ref_count": len(question_rows),
        "question_observation_row_refs_unique": _unique_non_empty(_case_refs(question_rows, "question_observation_row_ref"), required_count=len(question_rows)) if question_rows else False,
        "case_ref_ids": question_case_refs,
        "case_ref_count": len(question_case_refs),
        "case_ref_ids_unique": _unique_non_empty(question_case_refs, required_count=len(question_rows)) if question_rows else False,
        "packet_ref_ids": question_packet_refs,
        "packet_ref_count": len(question_packet_refs),
        "packet_ref_ids_unique": _unique_non_empty(question_packet_refs, required_count=len(question_rows)) if question_rows else False,
        "blind_case_ids": _case_refs(question_rows, "blind_case_id"),
        "blind_case_id_count": len(question_rows),
        "blind_case_ids_unique": _unique_non_empty(_case_refs(question_rows, "blind_case_id"), required_count=len(question_rows)) if question_rows else False,
        "question_observation_row_schema_version": P7_R54_CLR14_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION,
        "question_observation_row_required_field_refs": list(P7_R54_CLR14_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS),
        "question_need_primary_class_refs": list(P7_R54_CLR14_QUESTION_NEED_PRIMARY_CLASS_REFS),
        "ambiguity_kind_refs": list(P7_R54_CLR14_AMBIGUITY_KIND_OPTION_REFS),
        "one_question_fit_refs": list(P7_R54_CLR14_ONE_QUESTION_FIT_OPTION_REFS),
        "repair_required_ref_refs": list(P7_R54_CLR14_REPAIR_REQUIRED_OPTION_REFS),
        "plan_candidate_flag_refs": list(P7_R54_CLR14_PLAN_CANDIDATE_FLAG_REFS),
        "p8_material_candidate_primary_class_refs": list(P7_R54_CLR14_P8_MATERIAL_CANDIDATE_PRIMARY_CLASS_REFS),
        "not_question_repair_primary_class_refs": list(P7_R54_CLR14_NOT_QUESTION_REPAIR_PRIMARY_CLASS_REFS),
        "question_need_observation_rows_are_bodyfree": True,
        "question_text_absent_for_all_rows": True,
        "draft_question_text_absent_for_all_rows": True,
        "reviewer_free_text_absent_for_all_rows": True,
        "raw_body_absent_for_all_rows": True,
        "returned_emlis_body_absent_for_all_rows": True,
        "history_surface_absent_for_all_rows": True,
        "comment_text_absent_for_all_rows": True,
        "local_path_absent_for_all_rows": True,
        "body_hash_absent_for_all_rows": True,
        "question_text_included_allowed": False,
        "draft_question_text_included_allowed": False,
        "reviewer_free_text_included_allowed": False,
        "raw_body_allowed": False,
        "returned_emlis_body_allowed": False,
        "history_surface_allowed": False,
        "local_path_allowed": False,
        "body_hash_allowed": False,
        "question_text_or_draft_text_saved_here": False,
        "p8_question_implementation_spec_finalized_here": False,
        "question_trigger_logic_implemented": False,
        "question_trigger_logic_implemented_here": False,
        "question_api_implemented": False,
        "question_db_schema_implemented": False,
        "question_rn_ui_implemented": False,
        "question_response_key_implemented": False,
        "question_storage_schema_implemented": False,
        "question_answer_persistence_implemented": False,
        "question_plan_guard_implemented": False,
        "row_case_ref_sets_match_rating_rows": bool(row_case_refs_match and row_packet_refs_match),
        "all_required_question_need_observation_rows_present": ready,
        "question_observation_rows_normalized_here": ready,
        "primary_class_ambiguity_one_question_fit_are_canonical_refs": ready,
        "not_question_repair_rows_misclassified_as_p8_material": False,
        "p5_weakness_not_hidden_by_question_candidates_here": True,
        "question_need_primary_class_counts": _count_by(question_rows, "question_need_primary_class"),
        "ambiguity_kind_counts": _counter_from_ids(question_rows, "ambiguity_kind_refs"),
        "one_question_fit_counts": _count_by(question_rows, "one_question_fit_ref"),
        "repair_required_counts": _counter_from_ids(question_rows, "repair_required_refs"),
        "plan_candidate_flag_counts": _plan_candidate_flag_counts(question_rows),
        "p8_material_candidate_requested_row_count": sum(1 for row in question_rows if row.get("p8_material_candidate_requested") is True),
        "p8_material_candidate_allowed_row_count": sum(1 for row in question_rows if row.get("p8_material_candidate_allowed") is True),
        "p8_material_candidate_row_count": sum(1 for row in question_rows if row.get("p8_material_candidate_allowed") is True),
        "p8_material_candidate_allowed_primary_class_counts": _p8_allowed_primary_class_counts(question_rows),
        "not_question_repair_required_count": sum(1 for row in question_rows if row.get("not_question_repair_required") is True),
        "insufficient_material_execution_blocker_count": sum(1 for row in question_rows if row.get("insufficient_material_execution_blocker") is True),
        "rating_rows_preserved_from_clr13": ready,
        "blocker_rows_preserved_from_clr13": bool(ready and clr13_material.get("actual_blocker_rows_materialized_here") is True),
        "rating_question_consistency_guard_allowed_next": ready,
        "p8_implementation_spec_finalized_here": False,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "actual_rating_rows_materialized_here": bool(ready and clr13_material.get("actual_rating_rows_materialized_here") is True),
        "actual_blocker_rows_materialized_here": bool(ready and clr13_material.get("actual_blocker_rows_materialized_here") is True),
        "actual_question_need_observation_rows_materialized_here": ready,
        "actual_review_evidence_complete": False,
        "disposal_verified": False,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        **_current_ref_fields(),
        "implemented_steps": list(P7_R54_CLR14_IMPLEMENTED_STEPS if ready else (clr13_material.get("implemented_steps") or [])),
        "not_yet_implemented_steps": list(P7_R54_CLR14_NOT_YET_IMPLEMENTED_STEPS if ready else (clr13_material.get("not_yet_implemented_steps") or [])),
        "next_required_step": P7_R54_CLR15_STEP_REF if ready else P7_R54_CLR14_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_clr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "question_text_included": False,
        "draft_question_text_included": False,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "local_path_included": False,
        **_false_flags_except("actual_rating_rows_materialized_here", "actual_question_need_observation_rows_materialized_here"),
    }
    material["actual_rating_rows_materialized_here"] = bool(ready and clr13_material.get("actual_rating_rows_materialized_here") is True)
    material["actual_question_need_observation_rows_materialized_here"] = ready
    assert_p7_r54_clr14_question_need_observation_normalization_contract(material)
    return material


def assert_p7_r54_clr14_question_need_observation_normalization_contract(data: Mapping[str, Any]) -> bool:
    material = safe_mapping(data)
    _assert_required_fields(material, required=P7_R54_CLR14_QUESTION_NEED_OBSERVATION_NORMALIZATION_REQUIRED_FIELD_REFS, source="P7-R54-CLR14")
    _assert_common_base(
        material,
        schema_version=P7_R54_CLR14_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION,
        policy_section=P7_R54_CLR14_STEP_REF,
        source="P7-R54-CLR14",
        allowed_true_false_flags=P7_R54_CLR14_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    _assert_current_refs(material, source="P7-R54-CLR14")
    if safe_mapping(material.get("existing_op14_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("P7-R54-CLR14 OP14 refs changed")
    if safe_mapping(material.get("existing_ev12_current_refs")) != r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("P7-R54-CLR14 EV12 refs changed")
    for key in (
        "existing_op14_current_refs_are_historical_here",
        "existing_ev12_current_refs_are_historical_here",
        "existing_op14_structural_contract_reused",
        "existing_ev12_structural_contract_reused",
        "question_need_observation_rows_are_bodyfree",
        "question_text_absent_for_all_rows",
        "draft_question_text_absent_for_all_rows",
        "reviewer_free_text_absent_for_all_rows",
        "raw_body_absent_for_all_rows",
        "returned_emlis_body_absent_for_all_rows",
        "history_surface_absent_for_all_rows",
        "comment_text_absent_for_all_rows",
        "local_path_absent_for_all_rows",
        "body_hash_absent_for_all_rows",
        "p5_weakness_not_hidden_by_question_candidates_here",
        "human_review_completion_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if material.get(key) is not True:
            raise ValueError(f"P7-R54-CLR14 must keep {key}=True")
    for key in (
        "existing_op14_reused_as_actual_question_observation_basis",
        "existing_ev12_reused_as_actual_question_observation_basis",
        "existing_op14_reused_as_actual_normalization_basis",
        "existing_ev12_reused_as_actual_normalization_basis",
        "question_text_included_allowed",
        "draft_question_text_included_allowed",
        "reviewer_free_text_included_allowed",
        "raw_body_allowed",
        "returned_emlis_body_allowed",
        "history_surface_allowed",
        "local_path_allowed",
        "body_hash_allowed",
        "question_text_or_draft_text_saved_here",
        "p8_question_implementation_spec_finalized_here",
        "p8_implementation_spec_finalized_here",
        "question_text_materialized_here",
        "draft_question_text_materialized_here",
        "question_trigger_logic_implemented",
        "question_trigger_logic_implemented_here",
        "question_api_implemented",
        "question_db_schema_implemented",
        "question_rn_ui_implemented",
        "question_response_key_implemented",
        "question_storage_schema_implemented",
        "question_answer_persistence_implemented",
        "question_plan_guard_implemented",
        "not_question_repair_rows_misclassified_as_p8_material",
        "actual_review_evidence_complete",
        "disposal_verified",
    ):
        if material.get(key) is not False:
            raise ValueError(f"P7-R54-CLR14 must keep {key}=False")
    if material.get("required_case_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-CLR14 required case count changed")
    status = material.get("question_observation_normalization_status")
    if status not in P7_R54_CLR14_ALLOWED_NORMALIZATION_STATUS_REFS:
        raise ValueError("P7-R54-CLR14 status changed")
    blockers = dedupe_identifiers(material.get("execution_blocker_ids") or [], limit=100, max_length=180)
    if material.get("open_execution_blocker_ids") != blockers:
        raise ValueError("P7-R54-CLR14 open blockers mismatch")
    rows = [safe_mapping(row) for row in (material.get("question_observation_rows") or [])]
    for row in rows:
        assert_p7_r54_clr14_question_need_observation_row_bodyfree_contract(row)
    if material.get("question_observation_row_count") != len(rows):
        raise ValueError("P7-R54-CLR14 row count mismatch")
    if material.get("question_observation_row_ref_count") != len(material.get("question_observation_row_refs") or []):
        raise ValueError("P7-R54-CLR14 row ref count mismatch")
    if tuple(material.get("question_need_primary_class_refs") or ()) != P7_R54_CLR14_QUESTION_NEED_PRIMARY_CLASS_REFS:
        raise ValueError("P7-R54-CLR14 primary class refs changed")
    if tuple(material.get("ambiguity_kind_refs") or ()) != P7_R54_CLR14_AMBIGUITY_KIND_OPTION_REFS:
        raise ValueError("P7-R54-CLR14 ambiguity refs changed")
    if tuple(material.get("one_question_fit_refs") or ()) != P7_R54_CLR14_ONE_QUESTION_FIT_OPTION_REFS:
        raise ValueError("P7-R54-CLR14 one-question refs changed")
    if tuple(material.get("repair_required_ref_refs") or ()) != P7_R54_CLR14_REPAIR_REQUIRED_OPTION_REFS:
        raise ValueError("P7-R54-CLR14 repair refs changed")
    if tuple(material.get("plan_candidate_flag_refs") or ()) != P7_R54_CLR14_PLAN_CANDIDATE_FLAG_REFS:
        raise ValueError("P7-R54-CLR14 plan candidate refs changed")
    if tuple(material.get("p8_material_candidate_primary_class_refs") or ()) != P7_R54_CLR14_P8_MATERIAL_CANDIDATE_PRIMARY_CLASS_REFS:
        raise ValueError("P7-R54-CLR14 P8 primary refs changed")
    if tuple(material.get("not_question_repair_primary_class_refs") or ()) != P7_R54_CLR14_NOT_QUESTION_REPAIR_PRIMARY_CLASS_REFS:
        raise ValueError("P7-R54-CLR14 not-question repair refs changed")
    if material.get("p8_material_candidate_requested_row_count") != sum(1 for row in rows if row.get("p8_material_candidate_requested") is True):
        raise ValueError("P7-R54-CLR14 P8 requested count mismatch")
    if material.get("p8_material_candidate_allowed_row_count") != sum(1 for row in rows if row.get("p8_material_candidate_allowed") is True):
        raise ValueError("P7-R54-CLR14 P8 allowed count mismatch")
    if material.get("p8_material_candidate_row_count") != sum(1 for row in rows if row.get("p8_material_candidate_allowed") is True):
        raise ValueError("P7-R54-CLR14 P8 material row count mismatch")
    if safe_mapping(material.get("p8_material_candidate_allowed_primary_class_counts")) != _p8_allowed_primary_class_counts(rows):
        raise ValueError("P7-R54-CLR14 P8 allowed primary class counts mismatch")
    if material.get("not_question_repair_required_count") != sum(1 for row in rows if row.get("not_question_repair_required") is True):
        raise ValueError("P7-R54-CLR14 not-question repair count mismatch")
    if material.get("insufficient_material_execution_blocker_count") != sum(1 for row in rows if row.get("insufficient_material_execution_blocker") is True):
        raise ValueError("P7-R54-CLR14 insufficient material count mismatch")
    ready = status == P7_R54_CLR14_QUESTION_OBSERVATION_NORMALIZATION_READY_STATUS_REF
    if material.get("actual_question_need_observation_rows_materialized_here") is not ready:
        raise ValueError("P7-R54-CLR14 question materialization flag must match readiness")
    if ready:
        if material.get("clr13_question_observation_normalization_allowed_next") is not True or material.get("clr13_next_required_step") != P7_R54_CLR14_STEP_REF:
            raise ValueError("P7-R54-CLR14 ready normalization requires ready CLR13")
        if blockers:
            raise ValueError("P7-R54-CLR14 ready normalization must not carry materialization blockers")
        if material.get("rating_row_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-CLR14 ready normalization requires 24 rating rows")
        if material.get("question_observation_row_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-CLR14 ready normalization requires 24 question rows")
        if material.get("question_observation_row_refs_unique") is not True or material.get("case_ref_ids_unique") is not True:
            raise ValueError("P7-R54-CLR14 ready normalization requires unique rows/cases")
        if material.get("question_observation_rows_normalized_here") is not True:
            raise ValueError("P7-R54-CLR14 ready normalization must mark rows normalized here")
        if material.get("all_required_question_need_observation_rows_present") is not True or material.get("primary_class_ambiguity_one_question_fit_are_canonical_refs") is not True:
            raise ValueError("P7-R54-CLR14 ready normalization requires canonical rows")
        if material.get("row_case_ref_sets_match_rating_rows") is not True:
            raise ValueError("P7-R54-CLR14 ready rows must match rating rows")
        if material.get("rating_rows_preserved_from_clr13") is not True or material.get("blocker_rows_preserved_from_clr13") is not True:
            raise ValueError("P7-R54-CLR14 ready must preserve rating/blocker material")
        if material.get("rating_question_consistency_guard_allowed_next") is not True:
            raise ValueError("P7-R54-CLR14 ready must allow CLR15 next")
        if tuple(material.get("implemented_steps") or ()) != P7_R54_CLR14_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR14 implemented steps changed")
        if tuple(material.get("not_yet_implemented_steps") or ()) != P7_R54_CLR14_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR14 not-yet steps changed")
        if material.get("next_required_step") != P7_R54_CLR15_STEP_REF:
            raise ValueError("P7-R54-CLR14 ready must point to CLR15")
    else:
        if material.get("question_observation_rows") != [] or material.get("question_observation_row_count") != 0:
            raise ValueError("P7-R54-CLR14 blocked normalization must not materialize rows")
        if material.get("rating_question_consistency_guard_allowed_next") is not False:
            raise ValueError("P7-R54-CLR14 blocked normalization must not allow CLR15")
        if not blockers or material.get("next_required_step") != P7_R54_CLR14_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-CLR14 blocked normalization must carry blockers and repair next step")
    return True


def _question_by_case_ref(rows: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {clean_identifier(row.get("case_ref_id"), default="", max_length=180): row for row in rows}


def build_p7_r54_clr15_rating_question_consistency_issue_row_bodyfree(
    *,
    rating_row: Mapping[str, Any],
    question_observation_row: Mapping[str, Any],
    issue_id: Any,
    issue_kind_ref: Any,
    decision_direction_ref: Any,
) -> dict[str, Any]:
    rating = safe_mapping(rating_row)
    question = safe_mapping(question_observation_row)
    clr13._assert_rating_row(rating)
    assert_p7_r54_clr14_question_need_observation_row_bodyfree_contract(question)
    issue = clean_identifier(issue_id, max_length=180)
    kind = clean_identifier(issue_kind_ref, max_length=180)
    direction = clean_identifier(decision_direction_ref, max_length=180)
    if issue not in P7_R54_CLR15_CONSISTENCY_ISSUE_ID_REFS:
        raise ValueError("P7-R54-CLR15 issue id outside frozen refs")
    if kind not in P7_R54_CLR15_CONSISTENCY_ISSUE_KIND_REFS:
        raise ValueError("P7-R54-CLR15 issue kind outside frozen refs")
    if direction not in P7_R54_CLR15_DECISION_DIRECTION_REFS:
        raise ValueError("P7-R54-CLR15 decision direction outside frozen refs")
    out = {
        "schema_version": P7_R54_CLR15_RATING_QUESTION_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION,
        "consistency_issue_row_ref": f"r54clr15-issue-{clean_identifier(rating.get('rating_row_ref'), default='rating-row', max_length=120)}-{issue}",
        "review_session_id": _safe_review_session_id(rating.get("review_session_id") or question.get("review_session_id")),
        "rating_row_ref": clean_identifier(rating.get("rating_row_ref"), default="rating_row_missing", max_length=180),
        "question_observation_row_ref": clean_identifier(question.get("question_observation_row_ref"), default="question_row_missing", max_length=180),
        "packet_ref_id": clean_identifier(rating.get("packet_ref_id") or question.get("packet_ref_id"), default="packet_ref_missing", max_length=180),
        "blind_case_id": clean_identifier(rating.get("blind_case_id") or question.get("blind_case_id"), default="blind_case_missing", max_length=180),
        "case_ref_id": clean_identifier(rating.get("case_ref_id") or question.get("case_ref_id"), default="case_ref_missing", max_length=180),
        "case_index": int(rating.get("case_index") or question.get("case_index") or 0),
        "case_role_family_ref": clean_identifier(rating.get("case_role_family_ref") or question.get("case_role_family_ref"), default="case_role_family_missing", max_length=180),
        "issue_id": issue,
        "issue_kind_ref": kind,
        "decision_direction_ref": direction,
        "issue_status_ref": "open",
        "source_verdict": clean_identifier(rating.get("verdict"), default="NOT_REVIEWABLE", max_length=80),
        "question_need_primary_class": clean_identifier(question.get("question_need_primary_class"), default="unknown", max_length=180),
        "below_target_axis_refs": list(rating.get("below_target_axis_refs") or []),
        "readfeel_blocker_ids": list(rating.get("readfeel_blocker_ids") or []),
        "repair_required_refs": list(question.get("repair_required_refs") or []),
        "p8_material_candidate_requested": question.get("p8_material_candidate_requested") is True,
        "p8_material_candidate_allowed": question.get("p8_material_candidate_allowed") is True,
        "not_question_repair_required": question.get("not_question_repair_required") is True,
        "insufficient_material_execution_blocker": question.get("insufficient_material_execution_blocker") is True,
        "question_text_included": False,
        "draft_question_text_included": False,
        "reviewer_free_text_included": False,
        "reviewer_note_included": False,
        "reviewer_notes_included": False,
        "raw_body_included": False,
        "returned_emlis_body_included": False,
        "history_surface_included": False,
        "local_path_included": False,
        "local_absolute_path_included": False,
        "body_hash_included": False,
        "packet_content_included": False,
        "terminal_output_body_included": False,
        "body_free": True,
    }
    assert_p7_r54_clr15_rating_question_consistency_issue_row_bodyfree_contract(out)
    return out


def assert_p7_r54_clr15_rating_question_consistency_issue_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R54_CLR15_RATING_QUESTION_CONSISTENCY_ISSUE_ROW_REQUIRED_FIELD_REFS, source="P7-R54-CLR15 issue row")
    if data.get("schema_version") != P7_R54_CLR15_RATING_QUESTION_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION:
        raise ValueError("P7-R54-CLR15 issue row schema changed")
    if data.get("issue_id") not in P7_R54_CLR15_CONSISTENCY_ISSUE_ID_REFS:
        raise ValueError("P7-R54-CLR15 issue id changed")
    if data.get("issue_kind_ref") not in P7_R54_CLR15_CONSISTENCY_ISSUE_KIND_REFS:
        raise ValueError("P7-R54-CLR15 issue kind changed")
    if data.get("decision_direction_ref") not in P7_R54_CLR15_DECISION_DIRECTION_REFS:
        raise ValueError("P7-R54-CLR15 decision direction changed")
    if data.get("issue_status_ref") != "open":
        raise ValueError("P7-R54-CLR15 issue status must remain open")
    if data.get("body_free") is not True:
        raise ValueError("P7-R54-CLR15 issue row must be body-free")
    for false_key in (
        "question_text_included",
        "draft_question_text_included",
        "reviewer_free_text_included",
        "reviewer_note_included",
        "reviewer_notes_included",
        "raw_body_included",
        "returned_emlis_body_included",
        "history_surface_included",
        "local_path_included",
        "local_absolute_path_included",
        "body_hash_included",
        "packet_content_included",
        "terminal_output_body_included",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"P7-R54-CLR15 issue row must keep {false_key}=False")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_clr15_consistency_issue_row")
    return True


def _rating_question_consistency_issue_rows(
    *, rating_rows: Sequence[Mapping[str, Any]], question_rows: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    question_by_case_ref = _question_by_case_ref(question_rows)
    rating_case_refs = {clean_identifier(row.get("case_ref_id"), default="", max_length=180) for row in rating_rows}
    question_case_refs = {clean_identifier(row.get("case_ref_id"), default="", max_length=180) for row in question_rows}
    if rating_case_refs != question_case_refs:
        if rating_rows and question_rows:
            issues.append(
                build_p7_r54_clr15_rating_question_consistency_issue_row_bodyfree(
                    rating_row=safe_mapping(rating_rows[0]),
                    question_observation_row=safe_mapping(question_rows[0]),
                    issue_id="r54_clr15_rating_question_case_ref_set_mismatch",
                    issue_kind_ref="rating_question_case_integrity_issue",
                    decision_direction_ref="rating_question_row_repair_required",
                )
            )
        return issues
    for rating in rating_rows:
        rating_row = safe_mapping(rating)
        question = safe_mapping(question_by_case_ref.get(clean_identifier(rating_row.get("case_ref_id"), default="", max_length=180)))
        if not question:
            continue
        verdict = clean_identifier(rating_row.get("verdict"), max_length=80)
        below_target = list(rating_row.get("below_target_axis_refs") or [])
        readfeel_blockers = list(rating_row.get("readfeel_blocker_ids") or [])
        execution_blockers = list(rating_row.get("execution_blocker_ids") or [])
        p8_requested = question.get("p8_material_candidate_requested") is True
        p8_allowed = question.get("p8_material_candidate_allowed") is True
        not_question_repair = question.get("not_question_repair_required") is True
        insufficient = question.get("insufficient_material_execution_blocker") is True
        repair_or_below_target = bool(verdict in {"YELLOW", "REPAIR_REQUIRED", "RED"} or below_target)
        if repair_or_below_target and (p8_allowed or p8_requested):
            issues.append(
                build_p7_r54_clr15_rating_question_consistency_issue_row_bodyfree(
                    rating_row=rating_row,
                    question_observation_row=question,
                    issue_id="r54_clr15_repair_required_with_p8_material_candidate",
                    issue_kind_ref="p5_repair_hidden_by_question_candidate",
                    decision_direction_ref="p5_repair_return_required_later",
                )
            )
        elif repair_or_below_target:
            issues.append(
                build_p7_r54_clr15_rating_question_consistency_issue_row_bodyfree(
                    rating_row=rating_row,
                    question_observation_row=question,
                    issue_id="r54_clr15_yellow_red_repair_or_below_target_blocks_p5_confirmed_candidate",
                    issue_kind_ref="rating_question_observation_semantic_mismatch",
                    decision_direction_ref="p5_repair_return_required_later",
                )
            )
        if readfeel_blockers:
            issues.append(
                build_p7_r54_clr15_rating_question_consistency_issue_row_bodyfree(
                    rating_row=rating_row,
                    question_observation_row=question,
                    issue_id="r54_clr15_readfeel_blocker_blocks_p5_confirmed_candidate",
                    issue_kind_ref="rating_question_observation_semantic_mismatch",
                    decision_direction_ref="p5_repair_return_required_later",
                )
            )
        if not_question_repair and (p8_allowed or p8_requested):
            issues.append(
                build_p7_r54_clr15_rating_question_consistency_issue_row_bodyfree(
                    rating_row=rating_row,
                    question_observation_row=question,
                    issue_id="r54_clr15_not_question_repair_not_p8_material",
                    issue_kind_ref="p5_repair_hidden_by_question_candidate",
                    decision_direction_ref="keep_as_p5_or_emlis_or_gate_repair_not_p8_material",
                )
            )
        if not_question_repair and verdict == "PASS":
            issues.append(
                build_p7_r54_clr15_rating_question_consistency_issue_row_bodyfree(
                    rating_row=rating_row,
                    question_observation_row=question,
                    issue_id="r54_clr15_pass_with_not_question_repair_required",
                    issue_kind_ref="rating_question_observation_semantic_mismatch",
                    decision_direction_ref="p5_repair_return_required_later",
                )
            )
        if insufficient and (verdict == "PASS" or not execution_blockers):
            issues.append(
                build_p7_r54_clr15_rating_question_consistency_issue_row_bodyfree(
                    rating_row=rating_row,
                    question_observation_row=question,
                    issue_id="r54_clr15_insufficient_material_with_pass_or_no_execution_blocker",
                    issue_kind_ref="p5_inconclusive_or_execution_boundary_mismatch",
                    decision_direction_ref="mark_inconclusive_until_execution_material_is_repaired",
                )
            )
        if question.get("question_text_included") is True or question.get("draft_question_text_included") is True:
            issues.append(
                build_p7_r54_clr15_rating_question_consistency_issue_row_bodyfree(
                    rating_row=rating_row,
                    question_observation_row=question,
                    issue_id="r54_clr15_p8_material_candidate_question_text_violation",
                    issue_kind_ref="bodyfree_question_text_boundary_violation",
                    decision_direction_ref="bodyfree_boundary_repair_required",
                )
            )
    return issues


def build_p7_r54_clr15_rating_question_consistency_guard(
    *,
    question_need_observation_normalization: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_clr15_rating_question_consistency_guard",
) -> dict[str, Any]:
    """Guard that P5 repair/readfeel issues are not escaped into P8 material."""
    clr14_material = (
        safe_mapping(question_need_observation_normalization)
        if question_need_observation_normalization is not None
        else build_p7_r54_clr14_question_need_observation_normalization()
    )
    assert_p7_r54_clr14_question_need_observation_normalization_contract(clr14_material)
    clr14_ready = bool(
        clr14_material.get("question_observation_normalization_status") == P7_R54_CLR14_QUESTION_OBSERVATION_NORMALIZATION_READY_STATUS_REF
        and clr14_material.get("rating_question_consistency_guard_allowed_next") is True
        and clr14_material.get("next_required_step") == P7_R54_CLR15_STEP_REF
    )
    rating_rows = [safe_mapping(row) for row in (clr14_material.get("rating_rows") or [])] if clr14_ready else []
    question_rows = [safe_mapping(row) for row in (clr14_material.get("question_observation_rows") or [])] if clr14_ready else []
    blockers = [] if clr14_ready else dedupe_identifiers(
        [
            "question_observation_normalization_not_ready_for_consistency_guard",
            "clr14_question_need_observation_normalization_not_ready_for_consistency_guard",
            *(clr14_material.get("open_execution_blocker_ids") or []),
        ],
        limit=100,
        max_length=180,
    )
    rating_case_refs = {clean_identifier(row.get("case_ref_id"), default="", max_length=180) for row in rating_rows}
    question_case_refs = {clean_identifier(row.get("case_ref_id"), default="", max_length=180) for row in question_rows}
    case_sets_match = bool(rating_rows and question_rows and rating_case_refs == question_case_refs)
    all_required = bool(
        len(rating_rows) == clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and len(question_rows) == clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and case_sets_match
    )
    if clr14_ready and not all_required:
        blockers = dedupe_identifiers([*blockers, "rating_question_case_ref_set_mismatch"], limit=100, max_length=180)
    issue_rows = _rating_question_consistency_issue_rows(rating_rows=rating_rows, question_rows=question_rows) if clr14_ready else []
    issue_count = len(issue_rows)
    ready = bool(clr14_ready and all_required and issue_count == 0 and not blockers)
    reason_refs = [P7_R54_CLR15_READY_REASON_REF] if ready else dedupe_identifiers(
        [P7_R54_CLR15_CONSISTENCY_GUARD_BLOCKED_STATUS_REF, *blockers, *(row.get("issue_id") for row in issue_rows)],
        limit=120,
        max_length=180,
    )
    direction_counts = _single_id_counts(issue_rows, "decision_direction_ref")
    material = {
        "schema_version": P7_R54_CLR15_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_CLR_STEP,
        "scope": P7_R54_CLR_SCOPE,
        "policy_kind": P7_R54_CLR_POLICY_KIND,
        "policy_section": P7_R54_CLR15_STEP_REF,
        "operation_step_ref": P7_R54_CLR15_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_clr15_rating_question_consistency_guard", max_length=220),
        "review_session_id": _safe_review_session_id(clr14_material.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "clr14_schema_version": P7_R54_CLR14_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION,
        "clr14_material_ref": clean_identifier(clr14_material.get("material_id"), default="p7_r54_clr14_question_need_observation_normalization", max_length=220),
        "clr14_next_required_step": clean_identifier(clr14_material.get("next_required_step"), default=P7_R54_CLR14_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220),
        "clr14_question_observation_normalization_status": clean_identifier(clr14_material.get("question_observation_normalization_status"), default=P7_R54_CLR14_QUESTION_OBSERVATION_NORMALIZATION_BLOCKED_STATUS_REF, max_length=180),
        "clr14_consistency_guard_allowed_next": clr14_ready,
        "clr12_schema_version": clr13.P7_R54_CLR12_SCHEMA_VERSION,
        "clr12_material_ref": clean_identifier(clr14_material.get("clr12_material_ref"), default="p7_r54_clr12_rating_row_normalization", max_length=220),
        "clr12_rating_row_normalization_status": clean_identifier(clr14_material.get("clr12_rating_row_normalization_status"), default=clr13.P7_R54_CLR12_RATING_NORMALIZATION_BLOCKED_STATUS_REF, max_length=180),
        "existing_op15_helper_ref": "build_p7_r54_op15_rating_question_consistency_guard",
        "existing_op15_schema_version": r54op.P7_R54_OPERATION_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        "existing_ev13_schema_version": r54ev.P7_R54_EV13_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        "existing_op15_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_ev13_current_refs": dict(r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "existing_op15_current_refs_are_historical_here": True,
        "existing_ev13_current_refs_are_historical_here": True,
        "existing_op15_reused_as_actual_consistency_basis": False,
        "existing_ev13_reused_as_actual_consistency_basis": False,
        "existing_op15_structural_contract_reused": True,
        "existing_ev13_structural_contract_reused": True,
        "required_case_count": clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "rating_question_consistency_guard_status": P7_R54_CLR15_CONSISTENCY_GUARD_READY_STATUS_REF if ready else P7_R54_CLR15_CONSISTENCY_GUARD_BLOCKED_STATUS_REF,
        "rating_question_consistency_guard_ref": P7_R54_CLR15_CONSISTENCY_GUARD_REF if ready else "rating_question_consistency_guard_not_ready_bodyfree",
        "rating_question_consistency_guard_reason_refs": reason_refs,
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        "rating_rows": rating_rows,
        "question_observation_rows": question_rows,
        "rating_row_count": len(rating_rows),
        "question_observation_row_count": len(question_rows),
        "rating_question_case_ref_sets_match": case_sets_match,
        "all_required_rating_and_question_rows_present": bool(all_required),
        "rating_question_consistency_issue_row_schema_version": P7_R54_CLR15_RATING_QUESTION_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION,
        "rating_question_consistency_issue_row_required_field_refs": list(P7_R54_CLR15_RATING_QUESTION_CONSISTENCY_ISSUE_ROW_REQUIRED_FIELD_REFS),
        "rating_question_consistency_issue_rows": issue_rows,
        "consistency_issue_rows": issue_rows,
        "consistency_issue_count": issue_count,
        "consistency_issue_id_refs": list(P7_R54_CLR15_CONSISTENCY_ISSUE_ID_REFS),
        "consistency_issue_kind_refs": list(P7_R54_CLR15_CONSISTENCY_ISSUE_KIND_REFS),
        "decision_direction_refs": list(P7_R54_CLR15_DECISION_DIRECTION_REFS),
        "yellow_red_repair_or_below_target_block_count": sum(1 for row in issue_rows if row.get("issue_id") == "r54_clr15_yellow_red_repair_or_below_target_blocks_p5_confirmed_candidate"),
        "repair_required_with_p8_material_candidate_count": sum(1 for row in issue_rows if row.get("issue_id") == "r54_clr15_repair_required_with_p8_material_candidate"),
        "pass_with_not_question_repair_required_count": sum(1 for row in issue_rows if row.get("issue_id") == "r54_clr15_pass_with_not_question_repair_required"),
        "readfeel_blocker_block_count": sum(1 for row in issue_rows if row.get("issue_id") == "r54_clr15_readfeel_blocker_blocks_p5_confirmed_candidate"),
        "not_question_repair_not_p8_material_count": sum(1 for row in issue_rows if row.get("issue_id") == "r54_clr15_not_question_repair_not_p8_material"),
        "insufficient_material_with_pass_or_no_execution_blocker_count": sum(1 for row in issue_rows if row.get("issue_id") == "r54_clr15_insufficient_material_with_pass_or_no_execution_blocker"),
        "case_ref_set_mismatch_count": sum(1 for row in issue_rows if row.get("issue_id") == "r54_clr15_rating_question_case_ref_set_mismatch"),
        "p8_material_candidate_question_text_violation_count": sum(1 for row in issue_rows if row.get("issue_id") == "r54_clr15_p8_material_candidate_question_text_violation"),
        "open_readfeel_blocker_count": sum(1 for row in rating_rows if row.get("readfeel_blocker_ids")),
        "below_target_axis_count": sum(len(row.get("below_target_axis_refs") or []) for row in rating_rows),
        "insufficient_material_execution_blocker_count": sum(1 for row in question_rows if row.get("insufficient_material_execution_blocker") is True),
        "consistency_issue_direction_counts": direction_counts,
        "p5_confirmed_candidate_blocked_by_consistency_issues": issue_count > 0,
        "p5_decision_candidate_not_materialized_here": True,
        "rating_question_consistency_guard_passed": ready,
        "issues_route_to_p5_repair_return_or_inconclusive_later": issue_count > 0,
        "p8_material_candidates_do_not_hide_p5_repair_here": True,
        "p5_repair_required_not_reclassified_as_p8_material": not any(row.get("issue_id") in {"r54_clr15_not_question_repair_not_p8_material", "r54_clr15_repair_required_with_p8_material_candidate"} for row in issue_rows),
        "not_question_repair_not_promoted_to_p8_material": not any(row.get("issue_id") == "r54_clr15_not_question_repair_not_p8_material" for row in issue_rows),
        "question_text_absent": not any((row.get("question_text_included") is True or row.get("draft_question_text_included") is True) for row in question_rows),
        "draft_question_text_absent": not any(row.get("draft_question_text_included") is True for row in question_rows),
        "ready_for_pause_abort_expiration_protocol": ready,
        "rating_rows_preserved_from_clr12": bool(clr14_ready and clr14_material.get("actual_rating_rows_materialized_here") is True),
        "question_observation_rows_preserved_from_clr14": bool(clr14_ready and clr14_material.get("actual_question_need_observation_rows_materialized_here") is True),
        "actual_rating_rows_materialized_here": bool(clr14_ready and clr14_material.get("actual_rating_rows_materialized_here") is True),
        "actual_blocker_rows_materialized_here": bool(clr14_ready and clr14_material.get("actual_blocker_rows_materialized_here") is True),
        "actual_question_need_observation_rows_materialized_here": bool(clr14_ready and clr14_material.get("actual_question_need_observation_rows_materialized_here") is True),
        "actual_review_evidence_complete": False,
        "disposal_verified": False,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        **_current_ref_fields(),
        "implemented_steps": list(P7_R54_CLR15_IMPLEMENTED_STEPS if clr14_ready else (clr14_material.get("implemented_steps") or [])),
        "not_yet_implemented_steps": list(P7_R54_CLR15_NOT_YET_IMPLEMENTED_STEPS if clr14_ready else (clr14_material.get("not_yet_implemented_steps") or [])),
        "next_required_step": P7_R54_CLR16_STEP_REF if ready else P7_R54_CLR15_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_clr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "question_text_included": False,
        "draft_question_text_included": False,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "local_path_included": False,
        **_false_flags_except("actual_rating_rows_materialized_here", "actual_question_need_observation_rows_materialized_here"),
    }
    material["actual_rating_rows_materialized_here"] = bool(clr14_ready and clr14_material.get("actual_rating_rows_materialized_here") is True)
    material["actual_question_need_observation_rows_materialized_here"] = bool(clr14_ready and clr14_material.get("actual_question_need_observation_rows_materialized_here") is True)
    assert_p7_r54_clr15_rating_question_consistency_guard_contract(material)
    return material


def assert_p7_r54_clr15_rating_question_consistency_guard_contract(data: Mapping[str, Any]) -> bool:
    material = safe_mapping(data)
    _assert_required_fields(material, required=P7_R54_CLR15_RATING_QUESTION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS, source="P7-R54-CLR15")
    _assert_common_base(
        material,
        schema_version=P7_R54_CLR15_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        policy_section=P7_R54_CLR15_STEP_REF,
        source="P7-R54-CLR15",
        allowed_true_false_flags=P7_R54_CLR15_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    _assert_current_refs(material, source="P7-R54-CLR15")
    if safe_mapping(material.get("existing_op15_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("P7-R54-CLR15 OP15 refs changed")
    if safe_mapping(material.get("existing_ev13_current_refs")) != r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("P7-R54-CLR15 EV13 refs changed")
    for key in (
        "existing_op15_current_refs_are_historical_here",
        "existing_ev13_current_refs_are_historical_here",
        "existing_op15_structural_contract_reused",
        "existing_ev13_structural_contract_reused",
        "p5_decision_candidate_not_materialized_here",
        "p8_material_candidates_do_not_hide_p5_repair_here",
        "human_review_completion_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if material.get(key) is not True:
            raise ValueError(f"P7-R54-CLR15 must keep {key}=True")
    for key in (
        "existing_op15_reused_as_actual_consistency_basis",
        "existing_ev13_reused_as_actual_consistency_basis",
        "actual_review_evidence_complete",
        "disposal_verified",
    ):
        if material.get(key) is not False:
            raise ValueError(f"P7-R54-CLR15 must keep {key}=False")
    if material.get("required_case_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-CLR15 required case count changed")
    status = material.get("rating_question_consistency_guard_status")
    if status not in P7_R54_CLR15_ALLOWED_CONSISTENCY_GUARD_STATUS_REFS:
        raise ValueError("P7-R54-CLR15 guard status changed")
    blockers = dedupe_identifiers(material.get("execution_blocker_ids") or [], limit=100, max_length=180)
    if material.get("open_execution_blocker_ids") != blockers:
        raise ValueError("P7-R54-CLR15 blockers mismatch")
    rows = [safe_mapping(row) for row in (material.get("rating_question_consistency_issue_rows") or [])]
    if material.get("consistency_issue_rows") != material.get("rating_question_consistency_issue_rows"):
        raise ValueError("P7-R54-CLR15 issue row alias mismatch")
    for row in rows:
        assert_p7_r54_clr15_rating_question_consistency_issue_row_bodyfree_contract(row)
    if material.get("consistency_issue_count") != len(rows):
        raise ValueError("P7-R54-CLR15 issue count mismatch")
    if tuple(material.get("consistency_issue_id_refs") or ()) != P7_R54_CLR15_CONSISTENCY_ISSUE_ID_REFS:
        raise ValueError("P7-R54-CLR15 issue refs changed")
    if tuple(material.get("consistency_issue_kind_refs") or ()) != P7_R54_CLR15_CONSISTENCY_ISSUE_KIND_REFS:
        raise ValueError("P7-R54-CLR15 issue kinds changed")
    if tuple(material.get("decision_direction_refs") or ()) != P7_R54_CLR15_DECISION_DIRECTION_REFS:
        raise ValueError("P7-R54-CLR15 direction refs changed")
    if material.get("question_text_absent") is not True:
        raise ValueError("P7-R54-CLR15 must keep question text absent")
    if material.get("draft_question_text_absent") is not True:
        raise ValueError("P7-R54-CLR15 must keep draft question text absent")
    if material.get("actual_question_need_observation_rows_materialized_here") is not (material.get("question_observation_rows_preserved_from_clr14") is True):
        raise ValueError("P7-R54-CLR15 question row preservation flag mismatch")
    ready = status == P7_R54_CLR15_CONSISTENCY_GUARD_READY_STATUS_REF
    if material.get("rating_question_consistency_guard_passed") is not ready:
        raise ValueError("P7-R54-CLR15 guard passed flag must match readiness")
    if ready:
        if material.get("clr14_consistency_guard_allowed_next") is not True or material.get("clr14_next_required_step") != P7_R54_CLR15_STEP_REF:
            raise ValueError("P7-R54-CLR15 ready guard requires ready CLR14")
        if blockers:
            raise ValueError("P7-R54-CLR15 ready guard must not carry blockers")
        if material.get("rating_row_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT or material.get("question_observation_row_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-CLR15 ready guard requires 24 rating/question rows")
        if material.get("rating_question_case_ref_sets_match") is not True or material.get("all_required_rating_and_question_rows_present") is not True:
            raise ValueError("P7-R54-CLR15 ready guard requires matching row sets")
        if material.get("consistency_issue_count") != 0 or rows:
            raise ValueError("P7-R54-CLR15 ready guard must have zero issues")
        if material.get("ready_for_pause_abort_expiration_protocol") is not True:
            raise ValueError("P7-R54-CLR15 ready guard must allow CLR16 next")
        if tuple(material.get("implemented_steps") or ()) != P7_R54_CLR15_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR15 implemented steps changed")
        if tuple(material.get("not_yet_implemented_steps") or ()) != P7_R54_CLR15_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR15 not-yet steps changed")
        if material.get("next_required_step") != P7_R54_CLR16_STEP_REF:
            raise ValueError("P7-R54-CLR15 ready guard must point to CLR16")
    else:
        if material.get("ready_for_pause_abort_expiration_protocol") is not False:
            raise ValueError("P7-R54-CLR15 blocked guard must not allow CLR16")
        if not blockers and not rows:
            raise ValueError("P7-R54-CLR15 blocked guard must carry blockers or issue rows")
        if material.get("next_required_step") != P7_R54_CLR15_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-CLR15 blocked guard must point to repair")
    return True


build_p7_r54_current_snapshot_local_run_clr14_question_need_observation_normalization = build_p7_r54_clr14_question_need_observation_normalization
assert_p7_r54_current_snapshot_local_run_clr14_question_need_observation_normalization_contract = assert_p7_r54_clr14_question_need_observation_normalization_contract
build_p7_r54_current_snapshot_question_need_observation_normalization_bodyfree = build_p7_r54_clr14_question_need_observation_normalization
assert_p7_r54_current_snapshot_question_need_observation_normalization_bodyfree_contract = assert_p7_r54_clr14_question_need_observation_normalization_contract
build_p7_r54_current_snapshot_local_run_clr15_rating_question_consistency_guard = build_p7_r54_clr15_rating_question_consistency_guard
assert_p7_r54_current_snapshot_local_run_clr15_rating_question_consistency_guard_contract = assert_p7_r54_clr15_rating_question_consistency_guard_contract
build_p7_r54_current_snapshot_rating_question_consistency_guard_bodyfree = build_p7_r54_clr15_rating_question_consistency_guard
assert_p7_r54_current_snapshot_rating_question_consistency_guard_bodyfree_contract = assert_p7_r54_clr15_rating_question_consistency_guard_contract

build_clr14_question_need_observation_row_bodyfree = build_p7_r54_clr14_question_need_observation_row_bodyfree
assert_clr14_question_need_observation_row_bodyfree_contract = assert_p7_r54_clr14_question_need_observation_row_bodyfree_contract
build_clr14_question_need_observation_normalization = build_p7_r54_clr14_question_need_observation_normalization
assert_clr14_question_need_observation_normalization_contract = assert_p7_r54_clr14_question_need_observation_normalization_contract
build_clr15_rating_question_consistency_issue_row_bodyfree = build_p7_r54_clr15_rating_question_consistency_issue_row_bodyfree
assert_clr15_rating_question_consistency_issue_row_bodyfree_contract = assert_p7_r54_clr15_rating_question_consistency_issue_row_bodyfree_contract
build_clr15_rating_question_consistency_guard = build_p7_r54_clr15_rating_question_consistency_guard
assert_clr15_rating_question_consistency_guard_contract = assert_p7_r54_clr15_rating_question_consistency_guard_contract

__all__ = (
    "P7_R54_CLR14_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION",
    "P7_R54_CLR14_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION",
    "P7_R54_CLR15_RATING_QUESTION_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION",
    "P7_R54_CLR15_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION",
    "P7_R54_CLR14_STEP_REF",
    "P7_R54_CLR15_STEP_REF",
    "P7_R54_CLR16_STEP_REF",
    "P7_R54_CLR14_IMPLEMENTED_STEPS",
    "P7_R54_CLR14_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_CLR15_IMPLEMENTED_STEPS",
    "P7_R54_CLR15_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_CLR14_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS",
    "P7_R54_CLR14_QUESTION_NEED_OBSERVATION_NORMALIZATION_REQUIRED_FIELD_REFS",
    "P7_R54_CLR15_RATING_QUESTION_CONSISTENCY_ISSUE_ROW_REQUIRED_FIELD_REFS",
    "P7_R54_CLR15_RATING_QUESTION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS",
    "build_p7_r54_clr14_question_need_observation_row_bodyfree",
    "assert_p7_r54_clr14_question_need_observation_row_bodyfree_contract",
    "build_p7_r54_clr14_question_need_observation_normalization",
    "assert_p7_r54_clr14_question_need_observation_normalization_contract",
    "build_p7_r54_clr15_rating_question_consistency_issue_row_bodyfree",
    "assert_p7_r54_clr15_rating_question_consistency_issue_row_bodyfree_contract",
    "build_p7_r54_clr15_rating_question_consistency_guard",
    "assert_p7_r54_clr15_rating_question_consistency_guard_contract",
)
