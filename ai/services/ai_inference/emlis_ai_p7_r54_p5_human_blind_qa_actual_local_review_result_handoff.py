# -*- coding: utf-8 -*-
"""P7-R54 P5 actual local review result handoff helpers.

R54-0 refreezes the current received local snapshot for the R54 work session.
R54-1 records the source delta between the R53 materialization snapshot and the
R54 current received snapshot, then adopts the R54 current snapshot as the only
allowed actual-review basis.
R54-2 intakes R49-R53 validation evidence without inflating timeout or
collect-only results into broader green claims.
R54-3 checks the local-only root, explicit allow token, purge plan, retention,
and export denylist before any body-full packet generation can be requested.
R54-4 freezes the body-free actual-review session envelope.
R54-5 freezes the 24-case manifest while keeping controller-only metadata
separate from reviewer-facing blind case identifiers.
R54-6 creates a body-free request for local-only body-full packet generation.
R54-7 verifies body-free packet-completeness/export-denylist scan evidence before review.
R54-8 freezes the reviewer instruction and rating/question observation form schema.
R54-9 captures the local-only actual human review operation state without
materializing rating rows.
R54-10 captures sanitized external-local actual review result selections.
R54-11 normalizes those sanitized selections into body-free rating rows.
R54-12 separates readfeel blockers from execution blockers.
R54-13 normalizes body-free question-need observation rows without question text.
R54-14 guards consistency between rating rows and question observation rows.
R54-15 captures pause/abort/expiration protocol states before purge/disposal.
R54-16 materializes a body-free purge/disposal receipt from local-only purge evidence.
R54-17 summarizes rating/blocker/question/disposal evidence using only counts and refs.
R54-18 separates P5 confirmed-candidate / repair-return / inconclusive decision candidates without finalizing P5.
R54-19 hands off only the P6 limited human readfeel candidate while keeping start_allowed false.
R54-20 hands off only P8 question-design material candidates without starting P8.
R54-21 performs final no-body-leak / no-question-text / no-touch validation.
R54-22 builds a body-free R52 re-intake handoff.
R54-23 builds a body-free validation command matrix / documentation output.

This module intentionally implements only R54-0 through R54-23.  It does not run
an actual human review itself, generate body-full local review packets,
perform local file deletion, modify API/DB/RN/runtime contracts, start P6/P8,
complete P7, or claim release readiness.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping, Sequence
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
from emlis_ai_p7_r47_local_review_packet_policy import (
    P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
    P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS,
    P7_R47_EXPORT_DENYLIST_PATTERNS,
    P7_R47_EXPORT_DENYLIST_POLICY_SCHEMA_VERSION,
    P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR,
    P7_R47_LOCAL_REVIEW_STORAGE_ROOT_POLICY_SCHEMA_VERSION,
    P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
    P7_R47_STORAGE_ROOT_REF,
    assert_p7_r47_export_denylist_policy_contract,
    assert_p7_r47_local_review_storage_root_policy_contract,
    build_p7_r47_export_denylist_policy,
    build_p7_r47_local_review_storage_root_policy,
    p7_r47_export_candidate_deny_reasons,
)
from emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet import (
    P5_HUMAN_BLIND_QA_TARGETS,
    P7_R48_P5_BOUNDARY_FAMILY_REFS,
    P7_R48_P5_CASE_MATRIX_ROW_FIELD_REFS,
    P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION,
    P7_R48_P5_CASE_ROLE_REFS,
    P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION,
    P7_R48_P5_POSITIVE_CASE_ROLE_REFS,
    P7_R48_READFEEL_BLOCKER_ID_REFS,
    P7_R48_SANITIZED_REASON_ID_REFS,
    assert_p7_r48_p5_first_formal_review_case_matrix_contract,
    build_p7_r48_p5_first_formal_review_case_matrix,
)
from emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution import (
    P7_R49_AMBIGUITY_KIND_REFS,
    P7_R49_ONE_QUESTION_FIT_REFS,
    P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS,
    P7_R49_REPAIR_REQUIRED_REF_REFS,
)
from emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision import (
    P5_HUMAN_BLIND_QA_RATING_AXES,
    P7_R50_QUESTION_NEED_OBSERVATION_STAGE_REF,
    P7_R50_RATING_FORM_VERSION,
    P7_R50_REVIEWER_HIDDEN_FIELD_REFS,
    P7_R50_REVIEWER_VISIBLE_FIELD_REFS,
)
from emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run import (
    P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS,
    P7_R51_REQUIRED_CASE_COUNT,
)
from emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization import (
    P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION,
    P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS,
    P7_R53_POLICY_KIND,
    P7_R53_R51_R52_SOURCE_DELTA_FREEZE_SCHEMA_VERSION,
    P7_R53_SCOPE,
    P7_R53_STEP,
)


P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_received_snapshot_refreeze.bodyfree.v1"
)
P7_R54_SOURCE_DELTA_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.source_delta_row.bodyfree.v1"
)
P7_R54_R53_SOURCE_DELTA_CURRENT_SNAPSHOT_OVERRIDE_ADOPTION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.r53_source_delta_current_snapshot_override_adoption.bodyfree.v1"
)

P7_R54_STEP: Final = "R54_P5HumanBlindQAActualLocalReviewExecution_BodyFreeResultHandoff_20260622"
P7_R54_SCOPE: Final = "p5_human_blind_qa_actual_local_review_execution_body_free_result_handoff"
P7_R54_POLICY_KIND: Final = "p5_human_blind_qa_actual_local_review_result_handoff_policy"
P7_R54_DEFAULT_REVIEW_SESSION_ID: Final = "p7_r54_p5_actual_local_review_session"

P7_R54_R0_NEXT_REQUIRED_STEP_REF: Final = "R54-1_r53_source_delta_current_snapshot_override_adoption"
P7_R54_R1_NEXT_REQUIRED_STEP_REF: Final = "R54-2_r49_to_r53_validation_evidence_intake"
P7_R54_FIRST_NEXT_WORK_REF: Final = "p5_actual_local_review_without_p6_p8_or_release_promotion"
P7_R54_ACTUAL_REVIEW_BASIS_REF: Final = "r54_current_received_snapshot_refs"
P7_R54_ACTUAL_REVIEW_BASIS_ALLOWED_REF: Final = "current_ref_only"

P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS: Final[dict[str, str]] = {
    "premise_zip_ref": "Cocolon_前提資料(246).zip",
    "implemented_materials_zip_ref": "EmlisAIの実装済み資料(76).zip",
    "rn_zip_ref": "Cocolon(249).zip",
    "backend_zip_ref": "mashos-api(162).zip",
    "roadmap_ref": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619(8).md",
    "pre_design_memo_ref": "Cocolon_EmlisAI_P7_R54Candidate_P5HumanBlindQAActualLocalReview_PreDesignMemo_20260622.md",
    "detailed_design_ref": "Cocolon_EmlisAI_P7_R54_P5HumanBlindQAActualLocalReviewExecution_BodyFreeResultHandoff_DetailedDesign_ImplementationOrder_20260622.md",
}

P7_R54_R0_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R54-0_scope_current_received_snapshot_refreeze",
)
P7_R54_FUTURE_STEPS_AFTER_R1: Final[tuple[str, ...]] = (
    "R54-2_r49_to_r53_validation_evidence_intake",
    "R54-3_local_only_root_explicit_allow_purge_plan_preflight",
    "R54-4_actual_review_session_envelope",
    "R54-5_24_case_manifest_freeze",
    "R54-6_local_only_body_full_packet_generation_request",
    "R54-7_packet_completeness_export_denylist_scan",
    "R54-8_reviewer_instruction_rating_form_freeze",
    "R54-9_actual_human_review_operation_state_capture",
    "R54-10_sanitized_actual_review_result_capture",
    "R54-11_rating_row_normalization",
    "R54-12_readfeel_blocker_execution_blocker_ingestion",
    "R54-13_question_need_observation_row_normalization",
    "R54-14_rating_question_observation_consistency_guard",
    "R54-15_pause_abort_expiration_protocol",
    "R54-16_purge_disposal_receipt",
    "R54-17_body_free_post_review_summary",
    "R54-18_p5_decision_candidate_separation",
    "R54-19_p6_limited_human_readfeel_candidate_handoff",
    "R54-20_p8_question_design_material_candidate_handoff",
    "R54-21_final_no_body_leak_no_question_text_no_touch_validation",
    "R54-22_r52_reintake_handoff",
    "R54-23_validation_command_matrix_documentation_output",
)
P7_R54_R0_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R54-1_r53_source_delta_current_snapshot_override_adoption",
    *P7_R54_FUTURE_STEPS_AFTER_R1,
)
P7_R54_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_R0_IMPLEMENTED_STEPS,
    "R54-1_r53_source_delta_current_snapshot_override_adoption",
)
P7_R54_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_FUTURE_STEPS_AFTER_R1

P7_R54_QUESTION_IMPLEMENTATION_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    "question_api_implemented",
    "question_db_schema_implemented",
    "question_rn_ui_implemented",
    "question_response_key_implemented",
    "question_trigger_logic_implemented",
    "question_storage_schema_implemented",
    "question_answer_persistence_implemented",
    "question_plan_guard_implemented",
    "p8_question_implementation_spec_finalized_here",
    "question_implementation_started_here",
)
P7_R54_REVIEW_RELEASE_CLOSED_KEY_REFS: Final[tuple[str, ...]] = (
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "actual_body_full_packet_generated_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_question_need_observation_summary_materialized_here",
    "actual_reviewer_notes_materialized_here",
    "actual_disposal_run_here",
    "disposal_receipt_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "post_review_summary_materialized_here",
    "local_root_preflight_passed_here",
    "explicit_allow_present_here",
    "purge_plan_verified_here",
    "validation_evidence_intake_done_here",
    "p5_human_blind_qa_confirmed",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_human_blind_qa_confirmed_final",
    "p5_repair_return_candidate",
    "p5_review_inconclusive",
    "p6_limited_human_readfeel_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "p8_question_design_material_candidate",
    "p8_start_allowed",
    "p7_complete",
    "release_allowed",
    "hold004_close_allowed",
)
P7_R54_SCHEMA_MUTATION_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    "json_schema_file_created_here",
    "schema_files_materialized_here",
    "api_db_rn_response_key_changed_here",
    "runtime_changed_here",
    "api_route_changed_here",
    "db_schema_changed_here",
    "db_migration_changed_here",
    "rn_visible_contract_changed_here",
    "public_response_top_level_key_added_here",
    "public_response_key_changed_here",
)
P7_R54_EXPORT_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    "body_full_packet_export_allowed",
    "reviewer_notes_export_allowed",
    "body_full_packet_zip_inclusion_allowed",
    "local_absolute_path_materialized_here",
    "body_content_hash_materialized_here",
    "packet_content_hash_materialized_here",
    "command_result_body_stored_here",
    "terminal_output_stored_here",
    "full_backend_suite_green_confirmed",
    "backend_collect_only_claimed_as_full_backend_green",
    "rn_contract_claimed_as_real_device_modal_readfeel",
)
P7_R54_R0_R1_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    *P7_R54_QUESTION_IMPLEMENTATION_FALSE_KEY_REFS,
    *P7_R54_REVIEW_RELEASE_CLOSED_KEY_REFS,
    *P7_R54_SCHEMA_MUTATION_FALSE_KEY_REFS,
    *P7_R54_EXPORT_FALSE_KEY_REFS,
)

P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "r53_source_snapshot_refs",
    "r53_source_snapshot_ref_count",
    "r53_refs_are_current_received_refs",
    "old_refs_allowed_as_actual_review_basis",
    "r53_source_refs_can_be_used_for_helper_regression_only",
    "r53_source_refs_can_be_used_for_actual_review_basis",
    "r54_current_snapshot_override_required",
    "current_snapshot_can_override_r53_source_refs",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "r54_0_scope_current_received_snapshot_refrozen",
    "r54_1_r53_source_delta_current_snapshot_override_adopted",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r54_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R54_R0_R1_FALSE_KEY_REFS,
)

P7_R54_SOURCE_DELTA_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "source_ref_key",
    "prior_snapshot_ref_group",
    "current_snapshot_ref_group",
    "prior_ref",
    "current_ref",
    "refs_match",
    "override_required",
    "override_applied_in_r54",
    "actual_review_basis_allowed",
    "prior_ref_allowed_as_actual_review_basis",
    "prior_ref_regression_context_allowed",
    "source_delta_reason_refs",
    "body_free",
)

P7_R54_R53_SOURCE_DELTA_CURRENT_SNAPSHOT_OVERRIDE_ADOPTION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r0_refreeze_schema_version",
    "r0_refreeze_material_ref",
    "r53_step",
    "r53_scope",
    "r53_policy_kind",
    "r53_refreeze_schema_version",
    "r53_source_delta_schema_version",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "r53_source_snapshot_refs",
    "r53_source_snapshot_ref_count",
    "source_delta_ref_keys",
    "source_delta_rows",
    "source_delta_row_count",
    "r53_refs_are_current_received_refs",
    "r54_current_received_refs_frozen",
    "old_refs_allowed_as_actual_review_basis",
    "r53_old_refs_allowed_as_actual_review_basis",
    "r53_source_refs_can_be_used_for_helper_regression_only",
    "r53_source_refs_can_be_used_for_actual_review_basis",
    "r54_current_snapshot_override_required",
    "r54_current_snapshot_override_applied",
    "current_snapshot_can_override_r53_source_refs",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "r54_0_scope_current_received_snapshot_refrozen",
    "r54_1_r53_source_delta_current_snapshot_override_adopted",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r54_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R54_R0_R1_FALSE_KEY_REFS,
)


def _false_flags() -> dict[str, bool]:
    return {key: False for key in P7_R54_R0_R1_FALSE_KEY_REFS}


def _safe_review_session_id(value: Any) -> str:
    return clean_identifier(value, default=P7_R54_DEFAULT_REVIEW_SESSION_ID, max_length=140)


def _snapshot_refs(base: Mapping[str, str], overrides: Mapping[str, Any] | None = None) -> dict[str, str]:
    refs = dict(base)
    for key, value in safe_mapping(overrides).items():
        if key in refs:
            refs[key] = clean_identifier(value, default=refs[key], max_length=300)
    return refs


def _current_received_snapshot_refs(overrides: Mapping[str, Any] | None = None) -> dict[str, str]:
    return _snapshot_refs(P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS, overrides)


def _r53_source_snapshot_refs(overrides: Mapping[str, Any] | None = None) -> dict[str, str]:
    return _snapshot_refs(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS, overrides)


def _refs_match(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return bool(left) and bool(right) and {str(k): str(v) for k, v in left.items()} == {str(k): str(v) for k, v in right.items()}


def _body_free_markers() -> dict[str, bool]:
    return body_free_flags(include_history=True, include_reviewer=True, include_terminal=True)


def _public_no_touch_contract() -> dict[str, bool]:
    return {
        "api_route_changed_here": False,
        "db_schema_changed_here": False,
        "db_migration_changed_here": False,
        "rn_visible_contract_changed_here": False,
        "public_response_top_level_key_added_here": False,
        "runtime_changed_here": False,
        "p8_question_implementation_changed_here": False,
        "release_material_changed_here": False,
    }


def _assert_required_fields(data: Mapping[str, Any], *, required: Sequence[str], source: str) -> None:
    missing = [field for field in required if field not in data]
    if missing:
        raise ValueError(f"{source} missing required fields: {missing[:6]}")
    extra = sorted(set(data) - set(required))
    if extra:
        raise ValueError(f"{source} has unexpected fields: {extra[:6]}")


def _assert_body_free_common(data: Mapping[str, Any], *, schema_version: str, source: str) -> None:
    if data.get("schema_version") != schema_version:
        raise ValueError(f"{source} schema version changed")
    if data.get("phase") != P7_PHASE:
        raise ValueError(f"{source} phase changed")
    if data.get("step") != P7_R54_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R54_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("source_mode") != P7_SOURCE_MODE:
        raise ValueError(f"{source} must remain local snapshot")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} must not require or perform Git checks")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must be body-free")
    assert_false_markers(data.get("public_contract") or {}, source=f"{source}.public_contract")
    assert_false_markers(data.get("r54_public_no_touch_contract") or {}, source=f"{source}.r54_public_no_touch_contract")
    assert_false_markers(data.get("body_free_markers") or {}, source=f"{source}.body_free_markers")
    for false_key in P7_R54_R0_R1_FALSE_KEY_REFS:
        if data.get(false_key) is not False:
            raise ValueError(f"{source} must keep {false_key}=False")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)


def _assert_current_refs(data: Mapping[str, Any], *, source: str) -> None:
    current_refs = safe_mapping(data.get("current_received_snapshot_refs"))
    r53_refs = safe_mapping(data.get("r53_source_snapshot_refs"))
    if current_refs != P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError(f"{source} current received snapshot refs changed")
    if r53_refs != P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError(f"{source} R53 source refs changed")
    if data.get("current_received_snapshot_ref_count") != len(P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS):
        raise ValueError(f"{source} current received snapshot ref count changed")
    if data.get("r53_source_snapshot_ref_count") != len(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS):
        raise ValueError(f"{source} R53 source ref count changed")
    if _refs_match(r53_refs, current_refs) or data.get("r53_refs_are_current_received_refs") is not False:
        raise ValueError(f"{source} must not treat R53 refs as R54 current received refs")


def _source_delta_row(*, source_ref_key: str, prior_ref: Any, current_ref: Any) -> dict[str, Any]:
    key = clean_identifier(source_ref_key, default="source_ref", max_length=120)
    prior = clean_identifier(prior_ref, default="prior_ref", max_length=300)
    current = clean_identifier(current_ref, default="current_ref", max_length=300)
    refs_match = prior == current
    row = {
        "schema_version": P7_R54_SOURCE_DELTA_ROW_SCHEMA_VERSION,
        "source_ref_key": key,
        "prior_snapshot_ref_group": "p7_r53_current_received_snapshot_refs",
        "current_snapshot_ref_group": "p7_r54_current_received_snapshot_refs",
        "prior_ref": prior,
        "current_ref": current,
        "refs_match": refs_match,
        "override_required": True,
        "override_applied_in_r54": True,
        "actual_review_basis_allowed": P7_R54_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "prior_ref_allowed_as_actual_review_basis": False,
        "prior_ref_regression_context_allowed": True,
        "source_delta_reason_refs": [
            "r53_refs_are_historical_materialization_refs_only",
            "r54_actual_review_basis_requires_current_received_snapshot_refreeze",
        ],
        "body_free": True,
    }
    assert_p7_r54_source_delta_row_contract(row)
    return row


def assert_p7_r54_source_delta_row_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(
        data,
        required=P7_R54_SOURCE_DELTA_ROW_REQUIRED_FIELD_REFS,
        source="p7_r54_source_delta_row",
    )
    if data.get("schema_version") != P7_R54_SOURCE_DELTA_ROW_SCHEMA_VERSION:
        raise ValueError("R54 source delta row schema version changed")
    key = data.get("source_ref_key")
    if key not in P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("R54 source delta row key is not canonical")
    expected_prior = P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS.get(str(key))
    expected_current = P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS.get(str(key))
    if data.get("prior_snapshot_ref_group") != "p7_r53_current_received_snapshot_refs":
        raise ValueError("R54 source delta row prior group changed")
    if data.get("current_snapshot_ref_group") != "p7_r54_current_received_snapshot_refs":
        raise ValueError("R54 source delta row current group changed")
    if data.get("prior_ref") != expected_prior:
        raise ValueError("R54 source delta row prior ref changed")
    if data.get("current_ref") != expected_current:
        raise ValueError("R54 source delta row current ref changed")
    if data.get("refs_match") is not False:
        raise ValueError("R54 source delta row must show R53 and R54 refs differ")
    if data.get("override_required") is not True:
        raise ValueError("R54 source delta row must require current snapshot override")
    if data.get("override_applied_in_r54") is not True:
        raise ValueError("R54 source delta row must mark override applied in R54")
    if data.get("actual_review_basis_allowed") != P7_R54_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("R54 source delta row must allow only current ref as actual review basis")
    if data.get("prior_ref_allowed_as_actual_review_basis") is not False:
        raise ValueError("R54 source delta row must not allow R53 prior ref as actual review basis")
    if data.get("prior_ref_regression_context_allowed") is not True:
        raise ValueError("R54 source delta row should preserve R53 prior ref only for regression context")
    if data.get("body_free") is not True:
        raise ValueError("R54 source delta row must be body-free")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_source_delta_row")
    return True


def build_p7_r54_current_received_snapshot_refreeze(
    *,
    current_received_snapshot_refs: Mapping[str, Any] | None = None,
    r53_source_snapshot_refs: Mapping[str, Any] | None = None,
    review_session_id: Any = P7_R54_DEFAULT_REVIEW_SESSION_ID,
    material_id: Any = "p7_r54_current_received_snapshot_refreeze",
) -> dict[str, Any]:
    """Build R54-0 body-free scope/current received snapshot refreeze."""

    current_refs = _current_received_snapshot_refs(current_received_snapshot_refs)
    r53_refs = _r53_source_snapshot_refs(r53_source_snapshot_refs)
    r53_is_current = _refs_match(r53_refs, current_refs)
    refreeze = {
        "schema_version": P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_STEP,
        "scope": P7_R54_SCOPE,
        "policy_kind": P7_R54_POLICY_KIND,
        "policy_section": "R54-0_scope_current_received_snapshot_refreeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_current_received_snapshot_refreeze", max_length=200),
        "review_session_id": _safe_review_session_id(review_session_id),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "current_received_snapshot_refs": current_refs,
        "current_received_snapshot_ref_count": len(current_refs),
        "r53_source_snapshot_refs": r53_refs,
        "r53_source_snapshot_ref_count": len(r53_refs),
        "r53_refs_are_current_received_refs": r53_is_current,
        "old_refs_allowed_as_actual_review_basis": False,
        "r53_source_refs_can_be_used_for_helper_regression_only": True,
        "r53_source_refs_can_be_used_for_actual_review_basis": False,
        "r54_current_snapshot_override_required": True,
        "current_snapshot_can_override_r53_source_refs": True,
        "actual_review_basis_ref": P7_R54_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "r54_0_scope_current_received_snapshot_refrozen": True,
        "r54_1_r53_source_delta_current_snapshot_override_adopted": False,
        "implemented_steps": list(P7_R54_R0_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_R0_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R54_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R54_R0_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r54_current_received_snapshot_refreeze_contract(refreeze)
    return refreeze


def assert_p7_r54_current_received_snapshot_refreeze_contract(refreeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(refreeze)
    _assert_required_fields(
        data,
        required=P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_REQUIRED_FIELD_REFS,
        source="p7_r54_r0_current_received_snapshot_refreeze",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION,
        source="p7_r54_r0_current_received_snapshot_refreeze",
    )
    if data.get("policy_section") != "R54-0_scope_current_received_snapshot_refreeze":
        raise ValueError("R54 R0 policy section changed")
    _assert_current_refs(data, source="p7_r54_r0_current_received_snapshot_refreeze")
    if data.get("old_refs_allowed_as_actual_review_basis") is not False:
        raise ValueError("R54 R0 must not allow old refs as actual review basis")
    if data.get("r53_source_refs_can_be_used_for_helper_regression_only") is not True:
        raise ValueError("R54 R0 must keep R53 refs available only as helper regression context")
    if data.get("r53_source_refs_can_be_used_for_actual_review_basis") is not False:
        raise ValueError("R54 R0 must not allow R53 refs for actual review basis")
    if data.get("r54_current_snapshot_override_required") is not True:
        raise ValueError("R54 R0 must require current snapshot override")
    if data.get("current_snapshot_can_override_r53_source_refs") is not True:
        raise ValueError("R54 R0 must allow current snapshot to override R53 source refs")
    if data.get("actual_review_basis_ref") != P7_R54_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("R54 R0 actual review basis ref changed")
    if data.get("actual_review_basis_allowed") != P7_R54_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("R54 R0 must allow only current refs as actual review basis")
    if data.get("r54_0_scope_current_received_snapshot_refrozen") is not True:
        raise ValueError("R54 R0 must mark current received snapshot refrozen")
    if data.get("r54_1_r53_source_delta_current_snapshot_override_adopted") is not False:
        raise ValueError("R54 R0 must not claim R54-1")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_R0_IMPLEMENTED_STEPS:
        raise ValueError("R54 R0 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_R0_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R54 R0 not-yet steps changed")
    if data.get("next_required_step") != P7_R54_R0_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R54 R0 must point to R54-1")
    return True


def build_p7_r54_r53_source_delta_current_snapshot_override_adoption(
    *,
    current_received_snapshot_refreeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_r53_source_delta_current_snapshot_override_adoption",
) -> dict[str, Any]:
    """Build R54-1 body-free R53 source delta/current snapshot override adoption."""

    r0 = (
        safe_mapping(current_received_snapshot_refreeze)
        if current_received_snapshot_refreeze is not None
        else build_p7_r54_current_received_snapshot_refreeze()
    )
    assert_p7_r54_current_received_snapshot_refreeze_contract(r0)
    current_refs = safe_mapping(r0.get("current_received_snapshot_refs"))
    r53_refs = safe_mapping(r0.get("r53_source_snapshot_refs"))
    rows = [
        _source_delta_row(
            source_ref_key=key,
            prior_ref=r53_refs.get(key),
            current_ref=current_refs.get(key),
        )
        for key in P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS
    ]
    adoption = {
        "schema_version": P7_R54_R53_SOURCE_DELTA_CURRENT_SNAPSHOT_OVERRIDE_ADOPTION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_STEP,
        "scope": P7_R54_SCOPE,
        "policy_kind": P7_R54_POLICY_KIND,
        "policy_section": "R54-1_r53_source_delta_current_snapshot_override_adoption",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_r53_source_delta_current_snapshot_override_adoption", max_length=220),
        "review_session_id": _safe_review_session_id(r0.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r0_refreeze_schema_version": P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION,
        "r0_refreeze_material_ref": clean_identifier(r0.get("material_id"), default="p7_r54_current_received_snapshot_refreeze", max_length=220),
        "r53_step": P7_R53_STEP,
        "r53_scope": P7_R53_SCOPE,
        "r53_policy_kind": P7_R53_POLICY_KIND,
        "r53_refreeze_schema_version": P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION,
        "r53_source_delta_schema_version": P7_R53_R51_R52_SOURCE_DELTA_FREEZE_SCHEMA_VERSION,
        "current_received_snapshot_refs": current_refs,
        "current_received_snapshot_ref_count": len(current_refs),
        "r53_source_snapshot_refs": r53_refs,
        "r53_source_snapshot_ref_count": len(r53_refs),
        "source_delta_ref_keys": list(P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS.keys()),
        "source_delta_rows": rows,
        "source_delta_row_count": len(rows),
        "r53_refs_are_current_received_refs": False,
        "r54_current_received_refs_frozen": True,
        "old_refs_allowed_as_actual_review_basis": False,
        "r53_old_refs_allowed_as_actual_review_basis": False,
        "r53_source_refs_can_be_used_for_helper_regression_only": True,
        "r53_source_refs_can_be_used_for_actual_review_basis": False,
        "r54_current_snapshot_override_required": True,
        "r54_current_snapshot_override_applied": True,
        "current_snapshot_can_override_r53_source_refs": True,
        "actual_review_basis_ref": P7_R54_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "r54_0_scope_current_received_snapshot_refrozen": True,
        "r54_1_r53_source_delta_current_snapshot_override_adopted": True,
        "implemented_steps": list(P7_R54_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R54_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R54_R1_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r54_r53_source_delta_current_snapshot_override_adoption_contract(adoption)
    return adoption


def assert_p7_r54_r53_source_delta_current_snapshot_override_adoption_contract(adoption: Mapping[str, Any]) -> bool:
    data = safe_mapping(adoption)
    _assert_required_fields(
        data,
        required=P7_R54_R53_SOURCE_DELTA_CURRENT_SNAPSHOT_OVERRIDE_ADOPTION_REQUIRED_FIELD_REFS,
        source="p7_r54_r1_r53_source_delta_current_snapshot_override_adoption",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R54_R53_SOURCE_DELTA_CURRENT_SNAPSHOT_OVERRIDE_ADOPTION_SCHEMA_VERSION,
        source="p7_r54_r1_r53_source_delta_current_snapshot_override_adoption",
    )
    if data.get("policy_section") != "R54-1_r53_source_delta_current_snapshot_override_adoption":
        raise ValueError("R54 R1 policy section changed")
    if data.get("r0_refreeze_schema_version") != P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION:
        raise ValueError("R54 R1 R0 schema reference changed")
    if data.get("r53_step") != P7_R53_STEP or data.get("r53_scope") != P7_R53_SCOPE:
        raise ValueError("R54 R1 R53 context changed")
    if data.get("r53_refreeze_schema_version") != P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION:
        raise ValueError("R54 R1 R53 refreeze schema reference changed")
    if data.get("r53_source_delta_schema_version") != P7_R53_R51_R52_SOURCE_DELTA_FREEZE_SCHEMA_VERSION:
        raise ValueError("R54 R1 R53 source delta schema reference changed")
    _assert_current_refs(data, source="p7_r54_r1_r53_source_delta_current_snapshot_override_adoption")
    rows = data.get("source_delta_rows")
    expected_keys = list(P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS.keys())
    if not isinstance(rows, list) or len(rows) != len(expected_keys):
        raise ValueError("R54 R1 source delta rows changed")
    if data.get("source_delta_ref_keys") != expected_keys:
        raise ValueError("R54 R1 source delta ref keys changed")
    if data.get("source_delta_row_count") != len(expected_keys):
        raise ValueError("R54 R1 source delta row count changed")
    row_keys = [safe_mapping(row).get("source_ref_key") for row in rows]
    if row_keys != expected_keys:
        raise ValueError("R54 R1 source delta row order changed")
    for row in rows:
        assert_p7_r54_source_delta_row_contract(safe_mapping(row))
    for false_key in (
        "old_refs_allowed_as_actual_review_basis",
        "r53_old_refs_allowed_as_actual_review_basis",
        "r53_source_refs_can_be_used_for_actual_review_basis",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 R1 must keep {false_key}=False")
    for true_key in (
        "r54_current_received_refs_frozen",
        "r53_source_refs_can_be_used_for_helper_regression_only",
        "r54_current_snapshot_override_required",
        "r54_current_snapshot_override_applied",
        "current_snapshot_can_override_r53_source_refs",
        "r54_0_scope_current_received_snapshot_refrozen",
        "r54_1_r53_source_delta_current_snapshot_override_adopted",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R54 R1 must keep {true_key}=True")
    if data.get("actual_review_basis_ref") != P7_R54_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("R54 R1 actual review basis ref changed")
    if data.get("actual_review_basis_allowed") != P7_R54_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("R54 R1 must allow only current refs as actual review basis")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_IMPLEMENTED_STEPS:
        raise ValueError("R54 R1 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R54 R1 not-yet steps changed")
    if data.get("next_required_step") != P7_R54_R1_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R54 R1 must point to R54-2")
    return True


# Compatibility aliases matching the shorter R54-1 design wording.
build_p7_r54_r53_source_delta_and_override_adoption = build_p7_r54_r53_source_delta_current_snapshot_override_adoption
assert_p7_r54_r53_source_delta_and_override_adoption_contract = assert_p7_r54_r53_source_delta_current_snapshot_override_adoption_contract


P7_R54_VALIDATION_EVIDENCE_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.validation_evidence_row.bodyfree.v1"
)
P7_R54_VALIDATION_EVIDENCE_INTAKE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.validation_evidence_intake.bodyfree.v1"
)
P7_R54_LOCAL_ONLY_ACTUAL_REVIEW_PREFLIGHT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.local_only_review_preflight.bodyfree.v1"
)

P7_R54_R2_NEXT_REQUIRED_STEP_REF: Final = "R54-3_local_only_root_explicit_allow_purge_plan_preflight"
P7_R54_R2_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R54-2_validation_evidence_intake_before_R54-3_preflight"
P7_R54_R3_NEXT_REQUIRED_STEP_REF: Final = "R54-4_actual_review_session_envelope"
P7_R54_R3_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R54-3_local_only_root_explicit_allow_purge_plan_preflight"

P7_R54_R2_STEP_REF: Final = "R54-2_r49_to_r53_validation_evidence_intake"
P7_R54_R3_STEP_REF: Final = "R54-3_local_only_root_explicit_allow_purge_plan_preflight"
P7_R54_FUTURE_STEPS_AFTER_R3: Final[tuple[str, ...]] = tuple(
    step for step in P7_R54_FUTURE_STEPS_AFTER_R1 if step not in {P7_R54_R2_STEP_REF, P7_R54_R3_STEP_REF}
)
P7_R54_R2_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_IMPLEMENTED_STEPS, P7_R54_R2_STEP_REF)
P7_R54_R2_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_R3_STEP_REF, *P7_R54_FUTURE_STEPS_AFTER_R3)
P7_R54_R3_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_R2_IMPLEMENTED_STEPS, P7_R54_R3_STEP_REF)
P7_R54_R3_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_FUTURE_STEPS_AFTER_R3

P7_R54_EXPLICIT_LOCAL_REVIEW_ALLOW_ENV_VAR: Final = "COCOLON_EMLIS_P7_R54_LOCAL_REVIEW_EXPLICIT_ALLOW"
P7_R54_EXPLICIT_LOCAL_REVIEW_ALLOW_TOKEN_REF: Final = "R54_LOCAL_ONLY_ACTUAL_REVIEW_CONFIRMED"

P7_R54_VALIDATION_EVIDENCE_GROUP_REFS: Final[tuple[str, ...]] = (
    "rn_contract_36_passed",
    "r49_individual_split_76_passed",
    "r50_target_99_passed",
    "r51_target_125_passed",
    "r52_target_219_passed",
    "r53_py_compile_passed",
    "r53_target_split_291_passed",
    "backend_collect_only_4101_collected_1_warning",
    "r49_all_in_one_timeout_unclaimed",
    "r53_all_in_one_timeout_unclaimed",
)
P7_R54_VALIDATION_EVIDENCE_REQUIRED_GROUP_REFS: Final[tuple[str, ...]] = (
    "rn_contract_36_passed",
    "r49_individual_split_76_passed",
    "r50_target_99_passed",
    "r51_target_125_passed",
    "r52_target_219_passed",
    "r53_py_compile_passed",
    "r53_target_split_291_passed",
)
P7_R54_VALIDATION_EVIDENCE_OPTIONAL_GROUP_REFS: Final[tuple[str, ...]] = (
    "backend_collect_only_4101_collected_1_warning",
    "r49_all_in_one_timeout_unclaimed",
    "r53_all_in_one_timeout_unclaimed",
)
P7_R54_VALIDATION_EVIDENCE_INTAKE_STATUS_REFS: Final[tuple[str, ...]] = (
    "VALIDATION_INTAKE_READY",
    "VALIDATION_INTAKE_BLOCKED",
)
P7_R54_LOCAL_REVIEW_PREFLIGHT_STATUS_REFS: Final[tuple[str, ...]] = (
    "R54_LOCAL_REVIEW_PREFLIGHT_READY",
    "R54_LOCAL_REVIEW_PREFLIGHT_BLOCKED",
)
P7_R54_VALIDATION_EXECUTION_BLOCKER_ID_REFS: Final[tuple[str, ...]] = (
    "r54_validation_evidence_required_groups_missing",
    "r54_rn_contract_36_passed_missing",
    "r54_r49_individual_split_76_passed_missing",
    "r54_r50_target_99_passed_missing",
    "r54_r51_target_125_passed_missing",
    "r54_r52_target_219_passed_missing",
    "r54_r53_py_compile_passed_missing",
    "r54_r53_target_split_291_passed_missing",
    "r54_collect_only_claimed_as_full_backend_green",
    "r54_timeout_claimed_as_green",
    "r54_actual_review_evidence_claimed_during_validation_intake",
    "r54_product_or_release_claimed_during_validation_intake",
)
P7_R54_LOCAL_REVIEW_PREFLIGHT_BLOCKER_ID_REFS: Final[tuple[str, ...]] = (
    "r54_validation_evidence_not_ready",
    "r54_local_review_root_missing",
    "r54_local_review_root_invalid",
    "r54_explicit_allow_missing",
    "r54_purge_plan_missing",
    "r54_export_denylist_missing",
    "r54_retention_policy_missing",
    "r54_packet_export_denylist_violation",
)

P7_R54_VALIDATION_EVIDENCE_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "evidence_group_ref",
    "command_ref",
    "execution_mode",
    "claim_level",
    "evidence_present",
    "passed_count",
    "failed_count",
    "collected_count",
    "warning_count",
    "timeout_observed",
    "full_suite_green_claimed",
    "collect_only",
    "product_value_claimed",
    "release_readiness_claimed",
    "actual_review_evidence_claimed",
    "required_for_r54_3_preflight",
    "optional",
    "limitation_refs",
    "body_free",
)
P7_R54_R2_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    key for key in P7_R54_R0_R1_FALSE_KEY_REFS if key != "validation_evidence_intake_done_here"
)
P7_R54_R3_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_R0_R1_FALSE_KEY_REFS
    if key
    not in {
        "validation_evidence_intake_done_here",
        "local_root_preflight_passed_here",
        "explicit_allow_present_here",
        "purge_plan_verified_here",
    }
)

P7_R54_VALIDATION_EVIDENCE_INTAKE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r1_source_delta_schema_version",
    "r1_source_delta_material_ref",
    "r1_source_delta_next_required_step",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "r53_source_snapshot_refs",
    "r53_source_snapshot_ref_count",
    "r53_refs_are_current_received_refs",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "validation_evidence_group_refs",
    "validation_evidence_required_group_refs",
    "validation_evidence_optional_group_refs",
    "validation_evidence_rows",
    "validation_evidence_row_count",
    "validation_evidence_required_groups_present",
    "validation_evidence_intake_status",
    "validation_evidence_ready_for_r54_3_preflight",
    "rn_contract_36_passed_evidence_present",
    "r49_individual_split_76_passed_evidence_present",
    "r50_target_99_passed_evidence_present",
    "r51_target_125_passed_evidence_present",
    "r52_target_219_passed_evidence_present",
    "r53_py_compile_passed_evidence_present",
    "r53_target_split_291_passed_evidence_present",
    "backend_collect_only_4101_collected_1_warning_evidence_present",
    "backend_collect_only_claimed_as_full_backend_green",
    "full_backend_suite_green_confirmed",
    "r49_all_in_one_timeout_observed",
    "r49_all_in_one_green_claimed",
    "r53_all_in_one_timeout_observed",
    "r53_all_in_one_green_claimed",
    "actual_review_evidence_claimed",
    "product_value_claimed",
    "release_readiness_claimed",
    "validation_commands_executed_here",
    "command_result_body_stored_here",
    "terminal_output_stored_here",
    "body_full_packet_generation_allowed_after_r54_2",
    "actual_review_generation_allowed_after_r54_2",
    "local_only_actual_review_preflight_allowed_after_r54_2",
    "r54_0_scope_current_received_snapshot_refrozen",
    "r54_1_r53_source_delta_current_snapshot_override_adopted",
    "r54_2_validation_evidence_intake_done",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "public_contract",
    "r54_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R54_R2_FALSE_KEY_REFS,
    "validation_evidence_intake_done_here",
)
P7_R54_LOCAL_ONLY_ACTUAL_REVIEW_PREFLIGHT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r2_validation_evidence_schema_version",
    "r2_validation_evidence_material_ref",
    "r2_validation_evidence_status",
    "r2_validation_evidence_ready_for_r54_3_preflight",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "r53_source_snapshot_refs",
    "r53_source_snapshot_ref_count",
    "r53_refs_are_current_received_refs",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "required_case_count",
    "local_review_root_env_var",
    "local_review_root_source",
    "local_review_root_configured",
    "local_review_root_valid",
    "storage_root_ref",
    "root_path_exposed",
    "local_absolute_path_included",
    "explicit_allow_env_var",
    "explicit_allow_token_ref",
    "explicit_allow_present",
    "explicit_allow_token_body_stored_here",
    "purge_plan_ref",
    "purge_plan_present",
    "purge_plan_status",
    "purge_plan_ready",
    "purge_plan_reason_refs",
    "purge_plan_required_before_body_full_generation",
    "purge_plan_delete_target_refs",
    "purge_plan_required_delete_target_refs",
    "retention_policy_present",
    "body_full_packet_retention_max_hours",
    "reviewer_notes_retention_after_rating_finalized_max_hours",
    "delete_trigger_refs",
    "export_denylist_policy_schema_version",
    "export_denylist_present",
    "export_denylist_patterns",
    "export_candidate_refs_checked_count",
    "export_denylist_violation_refs",
    "denied_export_candidate_count",
    "export_candidate_refs_stored_here",
    "export_candidate_body_stored_here",
    "body_full_packet_export_allowed",
    "reviewer_notes_export_allowed",
    "body_full_packet_zip_inclusion_allowed",
    "local_only_body_full_generation_allowed_before_preflight",
    "local_only_body_full_generation_allowed_after_preflight",
    "body_full_generation_allowed",
    "actual_review_session_envelope_allowed_after_r54_3",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "preflight_status",
    "preflight_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "r54_0_scope_current_received_snapshot_refrozen",
    "r54_1_r53_source_delta_current_snapshot_override_adopted",
    "r54_2_validation_evidence_intake_done",
    "r54_3_local_only_actual_review_preflight_built",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r54_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R54_R3_FALSE_KEY_REFS,
    "validation_evidence_intake_done_here",
    "local_root_preflight_passed_here",
    "explicit_allow_present_here",
    "purge_plan_verified_here",
)


def _safe_non_negative_int_r54(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 0
    return parsed if parsed >= 0 else 0


def _safe_bool_r54(value: Any, *, default: bool = False) -> bool:
    return value if isinstance(value, bool) else default


def _safe_sequence_r54(value: Any, *, default: Sequence[Any] = ()) -> Sequence[Any]:
    if value is None:
        return default
    if isinstance(value, (str, bytes, bytearray)):
        return (value,)
    if isinstance(value, Sequence):
        return value
    return default


def _false_flags_except(excluded: set[str] | frozenset[str]) -> dict[str, bool]:
    return {key: False for key in P7_R54_R0_R1_FALSE_KEY_REFS if key not in excluded}


def _assert_body_free_common_with_false_keys(
    data: Mapping[str, Any],
    *,
    schema_version: str,
    source: str,
    false_key_refs: Sequence[str],
) -> None:
    if data.get("schema_version") != schema_version:
        raise ValueError(f"{source} schema version changed")
    if data.get("phase") != P7_PHASE:
        raise ValueError(f"{source} phase changed")
    if data.get("step") != P7_R54_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R54_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("source_mode") != P7_SOURCE_MODE:
        raise ValueError(f"{source} must remain local snapshot")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} must not require or perform Git checks")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must be body-free")
    assert_false_markers(data.get("public_contract") or {}, source=f"{source}.public_contract")
    assert_false_markers(data.get("r54_public_no_touch_contract") or {}, source=f"{source}.r54_public_no_touch_contract")
    assert_false_markers(data.get("body_free_markers") or {}, source=f"{source}.body_free_markers")
    for false_key in false_key_refs:
        if data.get(false_key) is not False:
            raise ValueError(f"{source} must keep {false_key}=False")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)


def _r54_validation_evidence_row(
    *,
    evidence_group_ref: str,
    command_ref: str,
    execution_mode: str,
    claim_level: str,
    evidence_present: bool,
    passed_count: int = 0,
    failed_count: int = 0,
    collected_count: int = 0,
    warning_count: int = 0,
    timeout_observed: bool = False,
    full_suite_green_claimed: bool = False,
    collect_only: bool = False,
    product_value_claimed: bool = False,
    release_readiness_claimed: bool = False,
    actual_review_evidence_claimed: bool = False,
    required_for_r54_3_preflight: bool = True,
    optional: bool = False,
    limitation_refs: Sequence[Any] = (),
) -> dict[str, Any]:
    row = {
        "schema_version": P7_R54_VALIDATION_EVIDENCE_ROW_SCHEMA_VERSION,
        "evidence_group_ref": clean_identifier(evidence_group_ref, default="unknown_evidence_group", max_length=140),
        "command_ref": clean_identifier(command_ref, default="unknown_command", max_length=220),
        "execution_mode": clean_identifier(execution_mode, default="not_executed", max_length=60),
        "claim_level": clean_identifier(claim_level, default="claim_boundary_unspecified", max_length=160),
        "evidence_present": bool(evidence_present),
        "passed_count": _safe_non_negative_int_r54(passed_count),
        "failed_count": _safe_non_negative_int_r54(failed_count),
        "collected_count": _safe_non_negative_int_r54(collected_count),
        "warning_count": _safe_non_negative_int_r54(warning_count),
        "timeout_observed": bool(timeout_observed),
        "full_suite_green_claimed": bool(full_suite_green_claimed),
        "collect_only": bool(collect_only),
        "product_value_claimed": bool(product_value_claimed),
        "release_readiness_claimed": bool(release_readiness_claimed),
        "actual_review_evidence_claimed": bool(actual_review_evidence_claimed),
        "required_for_r54_3_preflight": bool(required_for_r54_3_preflight),
        "optional": bool(optional),
        "limitation_refs": dedupe_identifiers(limitation_refs, limit=30, max_length=180),
        "body_free": True,
    }
    assert_p7_r54_validation_evidence_row_contract(row)
    return row


def _default_r54_validation_evidence_rows() -> list[dict[str, Any]]:
    return [
        _r54_validation_evidence_row(
            evidence_group_ref="rn_contract_36_passed",
            command_ref="npm_run_test_rn_screens_silent",
            execution_mode="individual",
            claim_level="rn_contract_green",
            evidence_present=True,
            passed_count=36,
            limitation_refs=("rn_contract_only_not_real_device_modal_readfeel", "not_product_value_claim"),
        ),
        _r54_validation_evidence_row(
            evidence_group_ref="r49_individual_split_76_passed",
            command_ref="pytest_r49_target_files_individual",
            execution_mode="individual",
            claim_level="target_individual_green",
            evidence_present=True,
            passed_count=76,
            limitation_refs=("r49_all_in_one_timeout_not_green_claim", "actual_review_not_run"),
        ),
        _r54_validation_evidence_row(
            evidence_group_ref="r50_target_99_passed",
            command_ref="pytest_r50_target",
            execution_mode="split",
            claim_level="target_green",
            evidence_present=True,
            passed_count=99,
            limitation_refs=("helper_target_only", "not_actual_review_completion"),
        ),
        _r54_validation_evidence_row(
            evidence_group_ref="r51_target_125_passed",
            command_ref="pytest_r51_target",
            execution_mode="split",
            claim_level="target_green",
            evidence_present=True,
            passed_count=125,
            limitation_refs=("helper_target_only", "body_full_packet_not_generated", "actual_review_not_run"),
        ),
        _r54_validation_evidence_row(
            evidence_group_ref="r52_target_219_passed",
            command_ref="pytest_r52_target",
            execution_mode="split",
            claim_level="target_green",
            evidence_present=True,
            passed_count=219,
            limitation_refs=("decision_gate_helper_only", "not_p6_p8_or_release_start"),
        ),
        _r54_validation_evidence_row(
            evidence_group_ref="r53_py_compile_passed",
            command_ref="python_m_py_compile_r53_helper",
            execution_mode="individual",
            claim_level="py_compile_green",
            evidence_present=True,
            limitation_refs=("syntax_import_only", "not_actual_review_completion"),
        ),
        _r54_validation_evidence_row(
            evidence_group_ref="r53_target_split_291_passed",
            command_ref="pytest_r53_target_split_r0_r21",
            execution_mode="split",
            claim_level="target_split_green",
            evidence_present=True,
            passed_count=291,
            limitation_refs=("not_all_in_one_target_green", "body_free_materialization_only"),
        ),
        _r54_validation_evidence_row(
            evidence_group_ref="backend_collect_only_4101_collected_1_warning",
            command_ref="pytest_collect_only_q",
            execution_mode="collect_only",
            claim_level="collect_only_with_warning",
            evidence_present=True,
            collected_count=4101,
            warning_count=1,
            collect_only=True,
            required_for_r54_3_preflight=False,
            optional=True,
            limitation_refs=("collect_only_not_full_backend_suite_green",),
        ),
        _r54_validation_evidence_row(
            evidence_group_ref="r49_all_in_one_timeout_unclaimed",
            command_ref="pytest_r49_all_in_one_or_bulk",
            execution_mode="all_in_one",
            claim_level="timeout_unclaimed_not_green",
            evidence_present=True,
            timeout_observed=True,
            required_for_r54_3_preflight=False,
            optional=True,
            limitation_refs=("timeout_observed", "never_claimed_as_green"),
        ),
        _r54_validation_evidence_row(
            evidence_group_ref="r53_all_in_one_timeout_unclaimed",
            command_ref="pytest_r53_all_in_one_target",
            execution_mode="all_in_one",
            claim_level="timeout_unclaimed_not_green",
            evidence_present=True,
            timeout_observed=True,
            required_for_r54_3_preflight=False,
            optional=True,
            limitation_refs=("timeout_observed", "split_green_only_not_all_in_one_green"),
        ),
    ]


def _r54_validation_evidence_rows_with_overrides(overrides: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    rows = _default_r54_validation_evidence_rows()
    override_map = safe_mapping(overrides)
    if not override_map:
        return rows
    out: list[dict[str, Any]] = []
    for row in rows:
        group_ref = str(row["evidence_group_ref"])
        patch = safe_mapping(override_map.get(group_ref))
        if not patch:
            out.append(row)
            continue
        merged = dict(row)
        for key in (
            "command_ref",
            "execution_mode",
            "claim_level",
            "evidence_present",
            "passed_count",
            "failed_count",
            "collected_count",
            "warning_count",
            "timeout_observed",
            "full_suite_green_claimed",
            "collect_only",
            "product_value_claimed",
            "release_readiness_claimed",
            "actual_review_evidence_claimed",
            "required_for_r54_3_preflight",
            "optional",
            "limitation_refs",
        ):
            if key in patch:
                merged[key] = patch[key]
        out.append(
            _r54_validation_evidence_row(
                evidence_group_ref=group_ref,
                command_ref=clean_identifier(merged.get("command_ref"), default="unknown_command", max_length=220),
                execution_mode=clean_identifier(merged.get("execution_mode"), default="not_executed", max_length=60),
                claim_level=clean_identifier(merged.get("claim_level"), default="claim_boundary_unspecified", max_length=160),
                evidence_present=_safe_bool_r54(merged.get("evidence_present")),
                passed_count=_safe_non_negative_int_r54(merged.get("passed_count")),
                failed_count=_safe_non_negative_int_r54(merged.get("failed_count")),
                collected_count=_safe_non_negative_int_r54(merged.get("collected_count")),
                warning_count=_safe_non_negative_int_r54(merged.get("warning_count")),
                timeout_observed=_safe_bool_r54(merged.get("timeout_observed")),
                full_suite_green_claimed=_safe_bool_r54(merged.get("full_suite_green_claimed")),
                collect_only=_safe_bool_r54(merged.get("collect_only")),
                product_value_claimed=_safe_bool_r54(merged.get("product_value_claimed")),
                release_readiness_claimed=_safe_bool_r54(merged.get("release_readiness_claimed")),
                actual_review_evidence_claimed=_safe_bool_r54(merged.get("actual_review_evidence_claimed")),
                required_for_r54_3_preflight=_safe_bool_r54(merged.get("required_for_r54_3_preflight"), default=True),
                optional=_safe_bool_r54(merged.get("optional")),
                limitation_refs=_safe_sequence_r54(merged.get("limitation_refs"), default=row["limitation_refs"]),
            )
        )
    return out


def _r54_evidence_row_by_group(rows: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {str(safe_mapping(row).get("evidence_group_ref")): safe_mapping(row) for row in rows}


def _r54_validation_flags(rows: Sequence[Mapping[str, Any]]) -> dict[str, bool]:
    by_group = _r54_evidence_row_by_group(rows)
    required_present = all(by_group.get(group, {}).get("evidence_present") is True for group in P7_R54_VALIDATION_EVIDENCE_REQUIRED_GROUP_REFS)
    backend_collect = by_group.get("backend_collect_only_4101_collected_1_warning", {})
    r49_timeout = by_group.get("r49_all_in_one_timeout_unclaimed", {})
    r53_timeout = by_group.get("r53_all_in_one_timeout_unclaimed", {})
    return {
        "validation_evidence_required_groups_present": required_present,
        "rn_contract_36_passed_evidence_present": by_group.get("rn_contract_36_passed", {}).get("evidence_present") is True,
        "r49_individual_split_76_passed_evidence_present": by_group.get("r49_individual_split_76_passed", {}).get("evidence_present") is True,
        "r50_target_99_passed_evidence_present": by_group.get("r50_target_99_passed", {}).get("evidence_present") is True,
        "r51_target_125_passed_evidence_present": by_group.get("r51_target_125_passed", {}).get("evidence_present") is True,
        "r52_target_219_passed_evidence_present": by_group.get("r52_target_219_passed", {}).get("evidence_present") is True,
        "r53_py_compile_passed_evidence_present": by_group.get("r53_py_compile_passed", {}).get("evidence_present") is True,
        "r53_target_split_291_passed_evidence_present": by_group.get("r53_target_split_291_passed", {}).get("evidence_present") is True,
        "backend_collect_only_4101_collected_1_warning_evidence_present": backend_collect.get("evidence_present") is True and backend_collect.get("collect_only") is True,
        "backend_collect_only_claimed_as_full_backend_green": backend_collect.get("full_suite_green_claimed") is True,
        "full_backend_suite_green_confirmed": False,
        "r49_all_in_one_timeout_observed": r49_timeout.get("timeout_observed") is True,
        "r49_all_in_one_green_claimed": r49_timeout.get("full_suite_green_claimed") is True or r49_timeout.get("claim_level") in {"green", "all_in_one_green"},
        "r53_all_in_one_timeout_observed": r53_timeout.get("timeout_observed") is True,
        "r53_all_in_one_green_claimed": r53_timeout.get("full_suite_green_claimed") is True or r53_timeout.get("claim_level") in {"green", "all_in_one_green"},
        "actual_review_evidence_claimed": any(safe_mapping(row).get("actual_review_evidence_claimed") is True for row in rows),
        "product_value_claimed": any(safe_mapping(row).get("product_value_claimed") is True for row in rows),
        "release_readiness_claimed": any(safe_mapping(row).get("release_readiness_claimed") is True for row in rows),
    }


def _r54_validation_execution_blockers(flags: Mapping[str, bool]) -> list[str]:
    blockers: list[str] = []
    if flags.get("validation_evidence_required_groups_present") is not True:
        blockers.append("r54_validation_evidence_required_groups_missing")
    missing_map = {
        "rn_contract_36_passed_evidence_present": "r54_rn_contract_36_passed_missing",
        "r49_individual_split_76_passed_evidence_present": "r54_r49_individual_split_76_passed_missing",
        "r50_target_99_passed_evidence_present": "r54_r50_target_99_passed_missing",
        "r51_target_125_passed_evidence_present": "r54_r51_target_125_passed_missing",
        "r52_target_219_passed_evidence_present": "r54_r52_target_219_passed_missing",
        "r53_py_compile_passed_evidence_present": "r54_r53_py_compile_passed_missing",
        "r53_target_split_291_passed_evidence_present": "r54_r53_target_split_291_passed_missing",
    }
    for flag_key, blocker_id in missing_map.items():
        if flags.get(flag_key) is not True:
            blockers.append(blocker_id)
    if flags.get("backend_collect_only_claimed_as_full_backend_green") is True:
        blockers.append("r54_collect_only_claimed_as_full_backend_green")
    if flags.get("r49_all_in_one_green_claimed") is True or flags.get("r53_all_in_one_green_claimed") is True:
        blockers.append("r54_timeout_claimed_as_green")
    if flags.get("actual_review_evidence_claimed") is True:
        blockers.append("r54_actual_review_evidence_claimed_during_validation_intake")
    if flags.get("product_value_claimed") is True or flags.get("release_readiness_claimed") is True:
        blockers.append("r54_product_or_release_claimed_during_validation_intake")
    return dedupe_identifiers(blockers, limit=40, max_length=140)


def assert_p7_r54_validation_evidence_row_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(
        data,
        required=P7_R54_VALIDATION_EVIDENCE_ROW_REQUIRED_FIELD_REFS,
        source="p7_r54_validation_evidence_row",
    )
    if data.get("schema_version") != P7_R54_VALIDATION_EVIDENCE_ROW_SCHEMA_VERSION:
        raise ValueError("R54 validation evidence row schema version changed")
    if data.get("evidence_group_ref") not in P7_R54_VALIDATION_EVIDENCE_GROUP_REFS:
        raise ValueError("R54 validation evidence group is not canonical")
    if data.get("execution_mode") not in {"individual", "split", "all_in_one", "collect_only", "not_executed"}:
        raise ValueError("R54 validation evidence execution mode is not canonical")
    if data.get("full_suite_green_claimed") is not False:
        raise ValueError("R54 validation evidence row must not claim full suite green")
    if data.get("product_value_claimed") is not False:
        raise ValueError("R54 validation evidence row must not claim product value")
    if data.get("release_readiness_claimed") is not False:
        raise ValueError("R54 validation evidence row must not claim release readiness")
    if data.get("actual_review_evidence_claimed") is not False:
        raise ValueError("R54 validation evidence row must not claim actual review evidence")
    if data.get("body_free") is not True:
        raise ValueError("R54 validation evidence row must be body-free")
    group = data.get("evidence_group_ref")
    if group == "backend_collect_only_4101_collected_1_warning":
        if data.get("execution_mode") != "collect_only" or data.get("collect_only") is not True:
            raise ValueError("R54 backend evidence must remain collect-only")
        if data.get("collected_count") != 4101 or data.get("warning_count") != 1:
            raise ValueError("R54 backend collect-only count/warning changed")
        if data.get("required_for_r54_3_preflight") is not False:
            raise ValueError("R54 backend collect-only is optional context, not R54-3 blocker")
    if group in {"r49_all_in_one_timeout_unclaimed", "r53_all_in_one_timeout_unclaimed"}:
        if data.get("execution_mode") != "all_in_one" or data.get("timeout_observed") is not True:
            raise ValueError("R54 timeout rows must remain all-in-one timeout observations")
        if "green" in str(data.get("claim_level") or "").lower() and "not_green" not in str(data.get("claim_level") or "").lower():
            raise ValueError("R54 timeout rows must not become green claims")
        if data.get("required_for_r54_3_preflight") is not False:
            raise ValueError("R54 timeout rows are visible limitations, not R54-3 required green")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_validation_evidence_row")
    return True


def build_p7_r54_validation_evidence_intake_bodyfree(
    *,
    source_delta_current_snapshot_override_adoption: Mapping[str, Any] | None = None,
    r1_source_delta_current_snapshot_override_adoption: Mapping[str, Any] | None = None,
    validation_evidence_overrides: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_validation_evidence_intake",
) -> dict[str, Any]:
    """Build R54-2 body-free validation-evidence intake.

    This freezes prior local validation evidence with claim boundaries. It does
    not run validation commands, does not store terminal output, and does not
    convert timeout/collect-only evidence into full-suite or product-value green.
    """

    if source_delta_current_snapshot_override_adoption is not None and r1_source_delta_current_snapshot_override_adoption is not None:
        raise ValueError("provide only one R54-1 source-delta adoption value")
    r1 = (
        safe_mapping(source_delta_current_snapshot_override_adoption)
        if source_delta_current_snapshot_override_adoption is not None
        else safe_mapping(r1_source_delta_current_snapshot_override_adoption)
        if r1_source_delta_current_snapshot_override_adoption is not None
        else build_p7_r54_r53_source_delta_current_snapshot_override_adoption()
    )
    assert_p7_r54_r53_source_delta_current_snapshot_override_adoption_contract(r1)
    rows = _r54_validation_evidence_rows_with_overrides(validation_evidence_overrides)
    flags = _r54_validation_flags(rows)
    blockers = _r54_validation_execution_blockers(flags)
    ready = flags["validation_evidence_required_groups_present"] and not blockers
    intake = {
        "schema_version": P7_R54_VALIDATION_EVIDENCE_INTAKE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_STEP,
        "scope": P7_R54_SCOPE,
        "policy_kind": P7_R54_POLICY_KIND,
        "policy_section": "R54-2_r49_to_r53_validation_evidence_intake",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_validation_evidence_intake", max_length=200),
        "review_session_id": _safe_review_session_id(r1.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r1_source_delta_schema_version": P7_R54_R53_SOURCE_DELTA_CURRENT_SNAPSHOT_OVERRIDE_ADOPTION_SCHEMA_VERSION,
        "r1_source_delta_material_ref": clean_identifier(r1.get("material_id"), default="p7_r54_r53_source_delta_current_snapshot_override_adoption", max_length=220),
        "r1_source_delta_next_required_step": clean_identifier(r1.get("next_required_step"), default=P7_R54_R1_NEXT_REQUIRED_STEP_REF, max_length=180),
        "current_received_snapshot_refs": safe_mapping(r1.get("current_received_snapshot_refs")),
        "current_received_snapshot_ref_count": len(safe_mapping(r1.get("current_received_snapshot_refs"))),
        "r53_source_snapshot_refs": safe_mapping(r1.get("r53_source_snapshot_refs")),
        "r53_source_snapshot_ref_count": len(safe_mapping(r1.get("r53_source_snapshot_refs"))),
        "r53_refs_are_current_received_refs": False,
        "actual_review_basis_ref": P7_R54_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "validation_evidence_group_refs": list(P7_R54_VALIDATION_EVIDENCE_GROUP_REFS),
        "validation_evidence_required_group_refs": list(P7_R54_VALIDATION_EVIDENCE_REQUIRED_GROUP_REFS),
        "validation_evidence_optional_group_refs": list(P7_R54_VALIDATION_EVIDENCE_OPTIONAL_GROUP_REFS),
        "validation_evidence_rows": rows,
        "validation_evidence_row_count": len(rows),
        "validation_evidence_required_groups_present": flags["validation_evidence_required_groups_present"],
        "validation_evidence_intake_status": "VALIDATION_INTAKE_READY" if ready else "VALIDATION_INTAKE_BLOCKED",
        "validation_evidence_ready_for_r54_3_preflight": ready,
        "rn_contract_36_passed_evidence_present": flags["rn_contract_36_passed_evidence_present"],
        "r49_individual_split_76_passed_evidence_present": flags["r49_individual_split_76_passed_evidence_present"],
        "r50_target_99_passed_evidence_present": flags["r50_target_99_passed_evidence_present"],
        "r51_target_125_passed_evidence_present": flags["r51_target_125_passed_evidence_present"],
        "r52_target_219_passed_evidence_present": flags["r52_target_219_passed_evidence_present"],
        "r53_py_compile_passed_evidence_present": flags["r53_py_compile_passed_evidence_present"],
        "r53_target_split_291_passed_evidence_present": flags["r53_target_split_291_passed_evidence_present"],
        "backend_collect_only_4101_collected_1_warning_evidence_present": flags["backend_collect_only_4101_collected_1_warning_evidence_present"],
        "backend_collect_only_claimed_as_full_backend_green": flags["backend_collect_only_claimed_as_full_backend_green"],
        "full_backend_suite_green_confirmed": False,
        "r49_all_in_one_timeout_observed": flags["r49_all_in_one_timeout_observed"],
        "r49_all_in_one_green_claimed": flags["r49_all_in_one_green_claimed"],
        "r53_all_in_one_timeout_observed": flags["r53_all_in_one_timeout_observed"],
        "r53_all_in_one_green_claimed": flags["r53_all_in_one_green_claimed"],
        "actual_review_evidence_claimed": flags["actual_review_evidence_claimed"],
        "product_value_claimed": flags["product_value_claimed"],
        "release_readiness_claimed": flags["release_readiness_claimed"],
        "validation_commands_executed_here": False,
        "command_result_body_stored_here": False,
        "terminal_output_stored_here": False,
        "body_full_packet_generation_allowed_after_r54_2": False,
        "actual_review_generation_allowed_after_r54_2": False,
        "local_only_actual_review_preflight_allowed_after_r54_2": ready,
        "r54_0_scope_current_received_snapshot_refrozen": True,
        "r54_1_r53_source_delta_current_snapshot_override_adopted": True,
        "r54_2_validation_evidence_intake_done": True,
        "implemented_steps": list(P7_R54_R2_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_R2_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R54_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R54_R2_NEXT_REQUIRED_STEP_REF if ready else P7_R54_R2_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "public_contract": public_contract_flags(),
        "r54_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_except({"validation_evidence_intake_done_here"}),
        "validation_evidence_intake_done_here": True,
    }
    assert_p7_r54_validation_evidence_intake_bodyfree_contract(intake)
    return intake


def assert_p7_r54_validation_evidence_intake_bodyfree_contract(intake: Mapping[str, Any]) -> bool:
    data = safe_mapping(intake)
    _assert_required_fields(
        data,
        required=P7_R54_VALIDATION_EVIDENCE_INTAKE_REQUIRED_FIELD_REFS,
        source="p7_r54_r2_validation_evidence_intake",
    )
    _assert_body_free_common_with_false_keys(
        data,
        schema_version=P7_R54_VALIDATION_EVIDENCE_INTAKE_SCHEMA_VERSION,
        source="p7_r54_r2_validation_evidence_intake",
        false_key_refs=P7_R54_R2_FALSE_KEY_REFS,
    )
    if data.get("policy_section") != "R54-2_r49_to_r53_validation_evidence_intake":
        raise ValueError("R54 R2 policy section changed")
    if data.get("r1_source_delta_schema_version") != P7_R54_R53_SOURCE_DELTA_CURRENT_SNAPSHOT_OVERRIDE_ADOPTION_SCHEMA_VERSION:
        raise ValueError("R54 R2 R1 schema reference changed")
    if data.get("r1_source_delta_next_required_step") != P7_R54_R1_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R54 R2 must intake after R54-1")
    _assert_current_refs(data, source="p7_r54_r2_validation_evidence_intake")
    if data.get("actual_review_basis_ref") != P7_R54_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("R54 R2 actual review basis ref changed")
    if data.get("actual_review_basis_allowed") != P7_R54_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("R54 R2 must allow only current refs as actual review basis")
    rows = data.get("validation_evidence_rows")
    if not isinstance(rows, list) or len(rows) != len(P7_R54_VALIDATION_EVIDENCE_GROUP_REFS):
        raise ValueError("R54 R2 validation evidence rows changed")
    if [safe_mapping(row).get("evidence_group_ref") for row in rows] != list(P7_R54_VALIDATION_EVIDENCE_GROUP_REFS):
        raise ValueError("R54 R2 validation evidence row order changed")
    for row in rows:
        assert_p7_r54_validation_evidence_row_contract(safe_mapping(row))
    if tuple(data.get("validation_evidence_group_refs") or ()) != P7_R54_VALIDATION_EVIDENCE_GROUP_REFS:
        raise ValueError("R54 R2 validation evidence group refs changed")
    if tuple(data.get("validation_evidence_required_group_refs") or ()) != P7_R54_VALIDATION_EVIDENCE_REQUIRED_GROUP_REFS:
        raise ValueError("R54 R2 validation evidence required groups changed")
    if tuple(data.get("validation_evidence_optional_group_refs") or ()) != P7_R54_VALIDATION_EVIDENCE_OPTIONAL_GROUP_REFS:
        raise ValueError("R54 R2 validation evidence optional groups changed")
    flags = _r54_validation_flags([safe_mapping(row) for row in rows])
    for key, value in flags.items():
        if key in data and data.get(key) is not value:
            raise ValueError(f"R54 R2 top-level flag mismatch for {key}")
    blockers = _r54_validation_execution_blockers(flags)
    if tuple(data.get("execution_blocker_ids") or ()) != tuple(blockers):
        raise ValueError("R54 R2 execution blockers do not match validation flags")
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 R2 open blockers must match execution blockers")
    unknown_blockers = sorted(set(blockers) - set(P7_R54_VALIDATION_EXECUTION_BLOCKER_ID_REFS))
    if unknown_blockers:
        raise ValueError(f"R54 R2 execution blocker ids are not canonical: {unknown_blockers[:4]}")
    ready = flags["validation_evidence_required_groups_present"] and not blockers
    if data.get("validation_evidence_ready_for_r54_3_preflight") is not ready:
        raise ValueError("R54 R2 readiness does not match validation evidence")
    if data.get("validation_evidence_intake_status") != ("VALIDATION_INTAKE_READY" if ready else "VALIDATION_INTAKE_BLOCKED"):
        raise ValueError("R54 R2 intake status does not match readiness")
    for false_key in (
        "backend_collect_only_claimed_as_full_backend_green",
        "full_backend_suite_green_confirmed",
        "r49_all_in_one_green_claimed",
        "r53_all_in_one_green_claimed",
        "actual_review_evidence_claimed",
        "product_value_claimed",
        "release_readiness_claimed",
        "validation_commands_executed_here",
        "command_result_body_stored_here",
        "terminal_output_stored_here",
        "body_full_packet_generation_allowed_after_r54_2",
        "actual_review_generation_allowed_after_r54_2",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 R2 must keep {false_key}=False")
    for true_key in (
        "r49_all_in_one_timeout_observed",
        "r53_all_in_one_timeout_observed",
        "r54_0_scope_current_received_snapshot_refrozen",
        "r54_1_r53_source_delta_current_snapshot_override_adopted",
        "r54_2_validation_evidence_intake_done",
        "validation_evidence_intake_done_here",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R54 R2 must keep {true_key}=True")
    if data.get("local_only_actual_review_preflight_allowed_after_r54_2") is not ready:
        raise ValueError("R54 R2 must allow R54-3 preflight only when validation intake is ready")
    if ready:
        if data.get("next_required_step") != P7_R54_R2_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R2 ready intake must point to R54-3")
    else:
        if data.get("next_required_step") != P7_R54_R2_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R2 blocked intake must point to evidence resolution")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_R2_IMPLEMENTED_STEPS:
        raise ValueError("R54 R2 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_R2_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R54 R2 not-yet steps changed")
    return True


def _explicit_allow_present_r54(explicit_allow_token: Any) -> bool:
    token = clean_identifier(
        explicit_allow_token if explicit_allow_token is not None else os.environ.get(P7_R54_EXPLICIT_LOCAL_REVIEW_ALLOW_ENV_VAR),
        default="",
        max_length=180,
    )
    return token == P7_R54_EXPLICIT_LOCAL_REVIEW_ALLOW_TOKEN_REF


def _export_candidate_sequence_r54(value: Sequence[Any] | Any | None) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (str, bytes, bytearray)):
        return [value]
    if isinstance(value, Mapping):
        return list(value.values())
    if isinstance(value, Sequence):
        return list(value)
    return [value]


def _export_denylist_summary_r54(export_candidate_refs: Sequence[Any] | Any | None) -> tuple[int, int, list[str]]:
    candidates = _export_candidate_sequence_r54(export_candidate_refs)
    violation_refs: list[str] = []
    denied_count = 0
    for candidate_ref in candidates:
        reasons = p7_r47_export_candidate_deny_reasons(candidate_ref)
        if reasons:
            denied_count += 1
            violation_refs.extend(reasons)
    return len(candidates), denied_count, dedupe_identifiers(violation_refs, limit=30, max_length=140)


def build_p7_r54_default_local_only_purge_plan_bodyfree(
    *,
    purge_plan_ref: Any = "p7_r54_local_only_actual_review_purge_plan",
) -> dict[str, Any]:
    """Return a body-free R54 purge plan descriptor; this does not create files."""

    plan = {
        "purge_plan_ref": clean_identifier(purge_plan_ref, default="p7_r54_local_only_actual_review_purge_plan", max_length=180),
        "body_full_packet_purge_required": True,
        "reviewer_forms_purge_required": True,
        "reviewer_notes_purge_required": True,
        "disposal_receipt_required": True,
        "retention_deadline_defined": True,
        "review_abort_purge_required": True,
        "expiration_purge_required": True,
        "delete_target_refs": list(P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS),
        "body_full_packet_retention_max_hours": P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
        "reviewer_notes_retention_after_rating_finalized_max_hours": P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "body_free": True,
    }
    assert_p7_no_body_payload_or_contract_mutation(plan, source="p7_r54_default_local_only_purge_plan_bodyfree")
    return plan


def _purge_plan_summary_r54(purge_plan: Mapping[str, Any] | None) -> dict[str, Any]:
    if purge_plan is None:
        return {
            "purge_plan_ref": "missing_purge_plan",
            "purge_plan_present": False,
            "purge_plan_status": "MISSING",
            "purge_plan_ready": False,
            "purge_plan_reason_refs": ["purge_plan_missing"],
            "purge_plan_delete_target_refs": [],
            "purge_plan_required_delete_target_refs": list(P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS),
            "retention_policy_present": False,
            "body_full_packet_retention_max_hours": P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
            "reviewer_notes_retention_after_rating_finalized_max_hours": P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
            "delete_trigger_refs": list(P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS),
            "local_packet_exported_allowed": False,
            "content_hash_of_body_stored_allowed": False,
        }

    data = safe_mapping(purge_plan)
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_purge_plan_input")
    reasons: list[str] = []
    if data.get("body_free") is not True:
        reasons.append("purge_plan_not_body_free")
    for key in (
        "body_full_packet_purge_required",
        "reviewer_forms_purge_required",
        "reviewer_notes_purge_required",
        "disposal_receipt_required",
        "retention_deadline_defined",
        "review_abort_purge_required",
        "expiration_purge_required",
    ):
        if data.get(key) is not True:
            reasons.append(f"{key}_missing_or_false")
    delete_targets = dedupe_identifiers(data.get("delete_target_refs") or [], limit=20, max_length=160)
    missing_targets = [target for target in P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS if target not in delete_targets]
    if missing_targets:
        reasons.append("purge_plan_delete_targets_incomplete")
    retention_policy_present = True
    if _safe_non_negative_int_r54(data.get("body_full_packet_retention_max_hours")) != P7_R47_BODY_FULL_PACKET_RETENTION_HOURS:
        reasons.append("body_full_packet_retention_window_changed")
        retention_policy_present = False
    if (
        _safe_non_negative_int_r54(data.get("reviewer_notes_retention_after_rating_finalized_max_hours"))
        != P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS
    ):
        reasons.append("reviewer_notes_retention_window_changed")
        retention_policy_present = False
    if data.get("local_packet_exported") is not False:
        reasons.append("purge_plan_allows_local_packet_export")
    if data.get("content_hash_of_body_stored") is not False:
        reasons.append("purge_plan_allows_body_content_hash_storage")

    ready = not reasons
    return {
        "purge_plan_ref": clean_identifier(data.get("purge_plan_ref"), default="p7_r54_local_only_actual_review_purge_plan", max_length=180),
        "purge_plan_present": True,
        "purge_plan_status": "READY" if ready else "INCOMPLETE",
        "purge_plan_ready": ready,
        "purge_plan_reason_refs": [] if ready else dedupe_identifiers(reasons, limit=20, max_length=140),
        "purge_plan_delete_target_refs": delete_targets,
        "purge_plan_required_delete_target_refs": list(P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS),
        "retention_policy_present": retention_policy_present,
        "body_full_packet_retention_max_hours": P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
        "reviewer_notes_retention_after_rating_finalized_max_hours": P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
        "delete_trigger_refs": list(P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS),
        "local_packet_exported_allowed": False,
        "content_hash_of_body_stored_allowed": False,
    }


def _r54_preflight_status_and_reasons(
    *,
    validation_ready: bool,
    validation_blockers: Sequence[Any],
    local_root_valid: bool,
    local_root_configured: bool,
    explicit_allow_present: bool,
    purge_plan_ready: bool,
    retention_policy_present: bool,
    export_denylist_present: bool,
    export_denylist_violation_refs: Sequence[Any],
) -> tuple[str, list[str], list[str]]:
    reason_refs: list[str] = []
    blocker_ids: list[str] = []
    if validation_ready is not True:
        reason_refs.append("validation_evidence_not_ready_for_r54_3_preflight")
        blocker_ids.append("r54_validation_evidence_not_ready")
        blocker_ids.extend(dedupe_identifiers(validation_blockers, limit=20, max_length=140))
    if not local_root_configured:
        reason_refs.append("local_review_root_missing")
        blocker_ids.append("r54_local_review_root_missing")
    elif not local_root_valid:
        reason_refs.append("local_review_root_invalid")
        blocker_ids.append("r54_local_review_root_invalid")
    if explicit_allow_present is not True:
        reason_refs.append("explicit_allow_token_missing_or_invalid")
        blocker_ids.append("r54_explicit_allow_missing")
    if purge_plan_ready is not True:
        reason_refs.append("purge_plan_missing_or_incomplete")
        blocker_ids.append("r54_purge_plan_missing")
    if retention_policy_present is not True:
        reason_refs.append("retention_policy_missing_or_changed")
        blocker_ids.append("r54_retention_policy_missing")
    if export_denylist_present is not True:
        reason_refs.append("export_denylist_missing")
        blocker_ids.append("r54_export_denylist_missing")
    if export_denylist_violation_refs:
        reason_refs.append("export_denylist_violation_detected")
        blocker_ids.append("r54_packet_export_denylist_violation")
    if reason_refs:
        return "R54_LOCAL_REVIEW_PREFLIGHT_BLOCKED", dedupe_identifiers(reason_refs, limit=40, max_length=140), dedupe_identifiers(blocker_ids, limit=40, max_length=140)
    return "R54_LOCAL_REVIEW_PREFLIGHT_READY", ["r54_local_only_root_explicit_allow_purge_plan_preflight_ready"], []


def build_p7_r54_local_only_actual_review_preflight_bodyfree(
    *,
    validation_evidence_intake: Mapping[str, Any] | None = None,
    r2_validation_evidence_intake: Mapping[str, Any] | None = None,
    local_review_root: Any = None,
    repo_roots: Sequence[Any] | None = None,
    export_roots: Sequence[Any] | None = None,
    explicit_allow_token: Any = None,
    purge_plan: Mapping[str, Any] | None = None,
    export_candidate_refs: Sequence[Any] | Any | None = None,
    material_id: Any = "p7_r54_local_only_actual_review_preflight",
) -> dict[str, Any]:
    """Build R54-3 body-free local-only preflight without generating packets."""

    if validation_evidence_intake is not None and r2_validation_evidence_intake is not None:
        raise ValueError("provide only one R54-2 validation evidence intake value")
    r2 = (
        safe_mapping(validation_evidence_intake)
        if validation_evidence_intake is not None
        else safe_mapping(r2_validation_evidence_intake)
        if r2_validation_evidence_intake is not None
        else build_p7_r54_validation_evidence_intake_bodyfree()
    )
    assert_p7_r54_validation_evidence_intake_bodyfree_contract(r2)

    storage_policy = build_p7_r47_local_review_storage_root_policy(
        local_review_root=local_review_root,
        repo_roots=repo_roots,
        export_roots=export_roots,
        material_id="p7_r54_r3_r47_storage_root_preflight",
    )
    assert_p7_r47_local_review_storage_root_policy_contract(storage_policy)
    export_policy = build_p7_r47_export_denylist_policy(material_id="p7_r54_r3_r47_export_denylist_preflight")
    assert_p7_r47_export_denylist_policy_contract(export_policy)
    root_configured = storage_policy.get("local_review_root_configured") is True
    root_valid = storage_policy.get("local_review_root_status") == "valid" and storage_policy.get("local_body_packet_generation_allowed") is True
    allow_present = _explicit_allow_present_r54(explicit_allow_token)
    purge_summary = _purge_plan_summary_r54(purge_plan)
    checked_count, denied_count, deny_refs = _export_denylist_summary_r54(export_candidate_refs)
    export_denylist_present = bool(export_policy.get("export_denylist_patterns"))
    preflight_status, reason_refs, blockers = _r54_preflight_status_and_reasons(
        validation_ready=r2.get("validation_evidence_ready_for_r54_3_preflight") is True,
        validation_blockers=r2.get("execution_blocker_ids") or [],
        local_root_valid=root_valid,
        local_root_configured=root_configured,
        explicit_allow_present=allow_present,
        purge_plan_ready=purge_summary["purge_plan_ready"],
        retention_policy_present=purge_summary["retention_policy_present"],
        export_denylist_present=export_denylist_present,
        export_denylist_violation_refs=deny_refs,
    )
    ready = preflight_status == "R54_LOCAL_REVIEW_PREFLIGHT_READY"
    preflight = {
        "schema_version": P7_R54_LOCAL_ONLY_ACTUAL_REVIEW_PREFLIGHT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_STEP,
        "scope": P7_R54_SCOPE,
        "policy_kind": P7_R54_POLICY_KIND,
        "policy_section": "R54-3_local_only_root_explicit_allow_purge_plan_preflight",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_local_only_actual_review_preflight", max_length=200),
        "review_session_id": _safe_review_session_id(r2.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r2_validation_evidence_schema_version": P7_R54_VALIDATION_EVIDENCE_INTAKE_SCHEMA_VERSION,
        "r2_validation_evidence_material_ref": clean_identifier(r2.get("material_id"), default="p7_r54_validation_evidence_intake", max_length=200),
        "r2_validation_evidence_status": clean_identifier(r2.get("validation_evidence_intake_status"), default="VALIDATION_INTAKE_BLOCKED", max_length=80),
        "r2_validation_evidence_ready_for_r54_3_preflight": r2.get("validation_evidence_ready_for_r54_3_preflight") is True,
        "current_received_snapshot_refs": safe_mapping(r2.get("current_received_snapshot_refs")),
        "current_received_snapshot_ref_count": len(safe_mapping(r2.get("current_received_snapshot_refs"))),
        "r53_source_snapshot_refs": safe_mapping(r2.get("r53_source_snapshot_refs")),
        "r53_source_snapshot_ref_count": len(safe_mapping(r2.get("r53_source_snapshot_refs"))),
        "r53_refs_are_current_received_refs": False,
        "actual_review_basis_ref": P7_R54_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "local_review_root_env_var": P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR,
        "local_review_root_source": clean_identifier(storage_policy.get("local_review_root_source"), default="missing", max_length=80),
        "local_review_root_configured": root_configured,
        "local_review_root_valid": root_valid,
        "storage_root_ref": P7_R47_STORAGE_ROOT_REF if root_valid else "not_configured_or_invalid",
        "root_path_exposed": False,
        "local_absolute_path_included": False,
        "explicit_allow_env_var": P7_R54_EXPLICIT_LOCAL_REVIEW_ALLOW_ENV_VAR,
        "explicit_allow_token_ref": P7_R54_EXPLICIT_LOCAL_REVIEW_ALLOW_TOKEN_REF,
        "explicit_allow_present": allow_present,
        "explicit_allow_token_body_stored_here": False,
        "purge_plan_ref": clean_identifier(purge_summary.get("purge_plan_ref"), default="missing_purge_plan", max_length=180),
        "purge_plan_present": purge_summary["purge_plan_present"],
        "purge_plan_status": purge_summary["purge_plan_status"],
        "purge_plan_ready": purge_summary["purge_plan_ready"],
        "purge_plan_reason_refs": purge_summary["purge_plan_reason_refs"],
        "purge_plan_required_before_body_full_generation": True,
        "purge_plan_delete_target_refs": purge_summary["purge_plan_delete_target_refs"],
        "purge_plan_required_delete_target_refs": purge_summary["purge_plan_required_delete_target_refs"],
        "retention_policy_present": purge_summary["retention_policy_present"],
        "body_full_packet_retention_max_hours": P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
        "reviewer_notes_retention_after_rating_finalized_max_hours": P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
        "delete_trigger_refs": purge_summary["delete_trigger_refs"],
        "export_denylist_policy_schema_version": P7_R47_EXPORT_DENYLIST_POLICY_SCHEMA_VERSION,
        "export_denylist_present": export_denylist_present,
        "export_denylist_patterns": list(P7_R47_EXPORT_DENYLIST_PATTERNS),
        "export_candidate_refs_checked_count": checked_count,
        "export_denylist_violation_refs": deny_refs,
        "denied_export_candidate_count": denied_count,
        "export_candidate_refs_stored_here": False,
        "export_candidate_body_stored_here": False,
        "body_full_packet_export_allowed": False,
        "reviewer_notes_export_allowed": False,
        "body_full_packet_zip_inclusion_allowed": False,
        "local_only_body_full_generation_allowed_before_preflight": False,
        "local_only_body_full_generation_allowed_after_preflight": ready,
        "body_full_generation_allowed": ready,
        "actual_review_session_envelope_allowed_after_r54_3": ready,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "preflight_status": preflight_status,
        "preflight_reason_refs": reason_refs,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "r54_0_scope_current_received_snapshot_refrozen": True,
        "r54_1_r53_source_delta_current_snapshot_override_adopted": True,
        "r54_2_validation_evidence_intake_done": True,
        "r54_3_local_only_actual_review_preflight_built": True,
        "implemented_steps": list(P7_R54_R3_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_R3_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R54_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R54_R3_NEXT_REQUIRED_STEP_REF if ready else P7_R54_R3_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_except({
            "validation_evidence_intake_done_here",
            "local_root_preflight_passed_here",
            "explicit_allow_present_here",
            "purge_plan_verified_here",
        }),
        "validation_evidence_intake_done_here": True,
        "local_root_preflight_passed_here": ready,
        "explicit_allow_present_here": allow_present,
        "purge_plan_verified_here": purge_summary["purge_plan_ready"],
    }
    assert_p7_r54_local_only_actual_review_preflight_bodyfree_contract(preflight)
    return preflight


def assert_p7_r54_local_only_actual_review_preflight_bodyfree_contract(preflight: Mapping[str, Any]) -> bool:
    data = safe_mapping(preflight)
    _assert_required_fields(
        data,
        required=P7_R54_LOCAL_ONLY_ACTUAL_REVIEW_PREFLIGHT_REQUIRED_FIELD_REFS,
        source="p7_r54_r3_local_only_actual_review_preflight",
    )
    _assert_body_free_common_with_false_keys(
        data,
        schema_version=P7_R54_LOCAL_ONLY_ACTUAL_REVIEW_PREFLIGHT_SCHEMA_VERSION,
        source="p7_r54_r3_local_only_actual_review_preflight",
        false_key_refs=P7_R54_R3_FALSE_KEY_REFS,
    )
    if data.get("policy_section") != "R54-3_local_only_root_explicit_allow_purge_plan_preflight":
        raise ValueError("R54 R3 policy section changed")
    if data.get("r2_validation_evidence_schema_version") != P7_R54_VALIDATION_EVIDENCE_INTAKE_SCHEMA_VERSION:
        raise ValueError("R54 R3 R2 schema reference changed")
    _assert_current_refs(data, source="p7_r54_r3_local_only_actual_review_preflight")
    if data.get("actual_review_basis_ref") != P7_R54_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("R54 R3 actual review basis ref changed")
    if data.get("actual_review_basis_allowed") != P7_R54_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("R54 R3 must allow only current refs as actual review basis")
    if data.get("required_case_count") != P7_R51_REQUIRED_CASE_COUNT:
        raise ValueError("R54 R3 must keep required_case_count=24")
    if data.get("local_review_root_env_var") != P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR:
        raise ValueError("R54 R3 local review root env var changed")
    for false_key in (
        "root_path_exposed",
        "local_absolute_path_included",
        "explicit_allow_token_body_stored_here",
        "export_candidate_refs_stored_here",
        "export_candidate_body_stored_here",
        "body_full_packet_export_allowed",
        "reviewer_notes_export_allowed",
        "body_full_packet_zip_inclusion_allowed",
        "local_only_body_full_generation_allowed_before_preflight",
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 R3 must keep {false_key}=False")
    if data.get("explicit_allow_env_var") != P7_R54_EXPLICIT_LOCAL_REVIEW_ALLOW_ENV_VAR:
        raise ValueError("R54 R3 explicit allow env var changed")
    if data.get("explicit_allow_token_ref") != P7_R54_EXPLICIT_LOCAL_REVIEW_ALLOW_TOKEN_REF:
        raise ValueError("R54 R3 explicit allow token ref changed")
    if data.get("purge_plan_required_before_body_full_generation") is not True:
        raise ValueError("R54 R3 must require purge plan before body-full generation")
    if tuple(data.get("purge_plan_required_delete_target_refs") or ()) != P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS:
        raise ValueError("R54 R3 purge target refs changed")
    if data.get("body_full_packet_retention_max_hours") != P7_R47_BODY_FULL_PACKET_RETENTION_HOURS:
        raise ValueError("R54 R3 body-full packet retention changed")
    if data.get("reviewer_notes_retention_after_rating_finalized_max_hours") != P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS:
        raise ValueError("R54 R3 reviewer notes retention changed")
    if tuple(data.get("delete_trigger_refs") or ()) != P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS:
        raise ValueError("R54 R3 delete trigger refs changed")
    if data.get("export_denylist_policy_schema_version") != P7_R47_EXPORT_DENYLIST_POLICY_SCHEMA_VERSION:
        raise ValueError("R54 R3 export denylist schema ref changed")
    if tuple(data.get("export_denylist_patterns") or ()) != P7_R47_EXPORT_DENYLIST_PATTERNS:
        raise ValueError("R54 R3 export denylist patterns changed")
    if data.get("export_denylist_present") is not True:
        raise ValueError("R54 R3 export denylist must be present")
    status = data.get("preflight_status")
    if status not in P7_R54_LOCAL_REVIEW_PREFLIGHT_STATUS_REFS:
        raise ValueError("R54 R3 preflight status changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 R3 open blockers must match execution blockers")
    unknown_blockers = sorted(set(blockers) - set(P7_R54_LOCAL_REVIEW_PREFLIGHT_BLOCKER_ID_REFS) - set(P7_R54_VALIDATION_EXECUTION_BLOCKER_ID_REFS))
    if unknown_blockers:
        raise ValueError(f"R54 R3 execution blocker ids are not canonical: {unknown_blockers[:4]}")
    ready = status == "R54_LOCAL_REVIEW_PREFLIGHT_READY"
    if data.get("local_only_body_full_generation_allowed_after_preflight") is not ready:
        raise ValueError("R54 R3 after-preflight authorization must match status")
    if data.get("body_full_generation_allowed") is not ready:
        raise ValueError("R54 R3 body-full generation authorization must match status")
    if data.get("actual_review_session_envelope_allowed_after_r54_3") is not ready:
        raise ValueError("R54 R3 envelope allowance must match status")
    if data.get("local_root_preflight_passed_here") is not ready:
        raise ValueError("R54 R3 local root preflight marker must match readiness")
    for true_key in (
        "validation_evidence_intake_done_here",
        "r54_0_scope_current_received_snapshot_refrozen",
        "r54_1_r53_source_delta_current_snapshot_override_adopted",
        "r54_2_validation_evidence_intake_done",
        "r54_3_local_only_actual_review_preflight_built",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R54 R3 must keep {true_key}=True")
    if ready:
        for true_key in (
            "r2_validation_evidence_ready_for_r54_3_preflight",
            "local_review_root_configured",
            "local_review_root_valid",
            "explicit_allow_present",
            "explicit_allow_present_here",
            "purge_plan_present",
            "purge_plan_ready",
            "purge_plan_verified_here",
            "retention_policy_present",
            "export_denylist_present",
        ):
            if data.get(true_key) is not True:
                raise ValueError(f"R54 R3 READY requires {true_key}=True")
        if blockers:
            raise ValueError("R54 R3 READY must not carry blockers")
        if data.get("denied_export_candidate_count") != 0 or data.get("export_denylist_violation_refs"):
            raise ValueError("R54 R3 READY must have no export denylist violations")
        if data.get("next_required_step") != P7_R54_R3_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R3 READY must point to R54-4")
    else:
        if not data.get("preflight_reason_refs") or not blockers:
            raise ValueError("R54 R3 BLOCKED must carry reasons and blockers")
        if data.get("next_required_step") != P7_R54_R3_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R3 BLOCKED must point to preflight resolution")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_R3_IMPLEMENTED_STEPS:
        raise ValueError("R54 R3 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_R3_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R54 R3 not-yet steps changed")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_r3_local_only_actual_review_preflight")
    return True


P7_R54_ACTUAL_REVIEW_SESSION_ENVELOPE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_review_session_envelope.bodyfree.v1"
)
P7_R54_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.24_case_manifest_freeze.bodyfree.v1"
)

P7_R54_R4_STEP_REF: Final = "R54-4_actual_review_session_envelope"
P7_R54_R5_STEP_REF: Final = "R54-5_24_case_manifest_freeze"
P7_R54_R4_NEXT_REQUIRED_STEP_REF: Final = "R54-5_24_case_manifest_freeze"
P7_R54_R4_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R54-4_actual_review_session_envelope_after_R54-3_preflight"
P7_R54_R5_NEXT_REQUIRED_STEP_REF: Final = "R54-6_local_only_body_full_packet_generation_request"
P7_R54_R5_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R54-5_24_case_manifest_freeze_before_R54-6_packet_request"

P7_R54_FUTURE_STEPS_AFTER_R5: Final[tuple[str, ...]] = tuple(
    step for step in P7_R54_FUTURE_STEPS_AFTER_R3 if step not in {P7_R54_R4_STEP_REF, P7_R54_R5_STEP_REF}
)
P7_R54_R4_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_R3_IMPLEMENTED_STEPS, P7_R54_R4_STEP_REF)
P7_R54_R4_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_R5_STEP_REF, *P7_R54_FUTURE_STEPS_AFTER_R5)
P7_R54_R5_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_R4_IMPLEMENTED_STEPS, P7_R54_R5_STEP_REF)
P7_R54_R5_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_FUTURE_STEPS_AFTER_R5

P7_R54_DEFAULT_REVIEWER_REF: Final = "reviewer_ref_pseudonymous_r54_primary"
P7_R54_REVIEW_PROMPT_VERSION: Final = "p7_r54_p5_actual_local_review_prompt.v1"
P7_R54_MANIFEST_MATRIX_KIND_REF: Final = "p5_24_case_first_formal_review_matrix"
P7_R54_REVIEWER_IDENTIFIER_POLICY_REF: Final = "blind_case_id_only"
P7_R54_R4_REVIEW_SESSION_STATUS_REFS: Final[tuple[str, ...]] = (
    "R54_ACTUAL_REVIEW_SESSION_ENVELOPE_READY",
    "R54_PRECHECK_BLOCKED",
)
P7_R54_R4_ENVELOPE_STATUS_REFS: Final[tuple[str, ...]] = (
    "READY_FOR_24_CASE_MANIFEST_FREEZE",
    "BLOCKED_BY_R54_3_PREFLIGHT",
)
P7_R54_R5_REVIEW_SESSION_STATUS_REFS: Final[tuple[str, ...]] = (
    "R54_24_CASE_MANIFEST_READY",
    "R54_PRECHECK_BLOCKED",
)
P7_R54_R5_MANIFEST_STATUS_REFS: Final[tuple[str, ...]] = (
    "READY_FOR_LOCAL_ONLY_PACKET_GENERATION_REQUEST",
    "BLOCKED_BY_R54_4_ENVELOPE",
    "BLOCKED_BY_CASE_MATRIX_CONTRACT",
)
P7_R54_R4_R5_EXECUTION_BLOCKER_ID_REFS: Final[tuple[str, ...]] = (
    "r54_actual_review_session_preflight_not_ready",
    "r54_case_manifest_incomplete",
    "r54_case_manifest_id_boundary_violation",
    "r54_case_manifest_distribution_changed",
    "r54_case_manifest_reviewer_hidden_metadata_violation",
)
P7_R54_R4_R5_ALLOWED_EXECUTION_BLOCKER_ID_REFS: Final[frozenset[str]] = frozenset(
    (*P7_R54_VALIDATION_EXECUTION_BLOCKER_ID_REFS, *P7_R54_LOCAL_REVIEW_PREFLIGHT_BLOCKER_ID_REFS, *P7_R54_R4_R5_EXECUTION_BLOCKER_ID_REFS)
)

P7_R54_R4_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_R0_R1_FALSE_KEY_REFS
    if key
    not in {
        "validation_evidence_intake_done_here",
        "local_root_preflight_passed_here",
        "explicit_allow_present_here",
        "purge_plan_verified_here",
    }
)
P7_R54_R5_FALSE_KEY_REFS: Final[tuple[str, ...]] = P7_R54_R4_FALSE_KEY_REFS

P7_R54_ACTUAL_REVIEW_SESSION_ENVELOPE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r3_preflight_schema_version",
    "r3_preflight_material_ref",
    "r3_preflight_status",
    "r3_preflight_ready_for_envelope",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "r53_source_snapshot_refs",
    "r53_source_snapshot_ref_count",
    "r53_refs_are_current_received_refs",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "required_case_count",
    "review_session_status",
    "envelope_status",
    "envelope_reason_refs",
    "review_prompt_version",
    "reviewer_ref",
    "reviewer_ref_pseudonymous",
    "reviewer_ref_policy_ref",
    "actual_reviewer_name_included",
    "reviewer_notes_included",
    "reviewer_notes_materialized_here",
    "reviewer_free_text_materialized_here",
    "reviewer_blind_policy",
    "reviewer_visible_field_refs",
    "reviewer_hidden_field_refs",
    "rating_form_version",
    "rating_axis_refs",
    "question_need_observation_stage_ref",
    "local_root_ref",
    "root_path_exposed",
    "local_absolute_path_included",
    "body_full_generation_allowed",
    "local_only_body_full_generation_allowed",
    "disposal_plan_ref",
    "disposal_plan_ready",
    "actual_review_session_envelope_created_here",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "p5_actual_review_still_not_run",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "r54_0_scope_current_received_snapshot_refrozen",
    "r54_1_r53_source_delta_current_snapshot_override_adopted",
    "r54_2_validation_evidence_intake_done",
    "r54_3_local_only_actual_review_preflight_built",
    "r54_4_actual_review_session_envelope_built",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r54_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R54_R4_FALSE_KEY_REFS,
    "validation_evidence_intake_done_here",
    "local_root_preflight_passed_here",
    "explicit_allow_present_here",
    "purge_plan_verified_here",
)

P7_R54_24_CASE_MANIFEST_CONTROLLER_ROW_FIELD_REFS: Final[tuple[str, ...]] = (
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
    "family",
    "case_role",
    "subscription_tier_ref",
    "controller_only",
    "reviewer_facing_identifier_policy",
    "reviewer_receives_blind_case_id",
    "reviewer_receives_case_ref_id",
    "reviewer_receives_family",
    "reviewer_receives_subscription_tier",
    "reviewer_receives_expected_result",
    "reviewer_receives_gate_result",
    "blind_case_id_derived_from_body_or_record_hash",
    "body_full_packet_materialized_here",
    "local_reviewer_payload_materialized_here",
    "body_free",
)
P7_R54_REVIEWER_FACING_CASE_INDEX_ROW_FIELD_REFS: Final[tuple[str, ...]] = (
    "blind_case_id",
    "reviewer_identifier_kind",
    "case_ref_hidden",
    "packet_ref_hidden",
    "family_hidden",
    "tier_hidden",
    "expected_result_hidden",
    "gate_result_hidden",
    "derived_from_body_or_record_hash",
    "body_free",
)
P7_R54_24_CASE_MANIFEST_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r4_envelope_schema_version",
    "r4_envelope_material_ref",
    "r4_envelope_status",
    "r4_envelope_ready_for_manifest_freeze",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "r53_source_snapshot_refs",
    "r53_source_snapshot_ref_count",
    "r53_refs_are_current_received_refs",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "review_session_status",
    "manifest_status",
    "manifest_reason_refs",
    "r48_case_matrix_schema_version",
    "r48_case_matrix_ref",
    "matrix_kind",
    "required_case_count",
    "case_count",
    "case_rows",
    "controller_manifest_rows",
    "reviewer_facing_case_index_rows",
    "family_case_counts",
    "case_role_counts",
    "subscription_tier_ref_counts",
    "owned_history_positive_case_count",
    "boundary_case_count",
    "low_information_boundary_case_count",
    "free_tier_boundary_case_count",
    "minimums_satisfied",
    "blind_case_ids_unique",
    "case_ref_ids_unique",
    "packet_ref_ids_unique",
    "blind_case_id_case_ref_separated",
    "blind_case_id_packet_ref_separated",
    "case_ref_id_packet_ref_separated",
    "reviewer_facing_identifier_policy",
    "reviewer_facing_family_exposed",
    "reviewer_facing_tier_exposed",
    "reviewer_facing_case_ref_exposed",
    "reviewer_facing_packet_ref_exposed",
    "reviewer_facing_expected_result_exposed",
    "reviewer_facing_hidden_metadata_exposed",
    "controller_keeps_family_tier_expected_refs",
    "reviewer_receives_blind_case_id_only",
    "reviewer_facing_row_count",
    "controller_manifest_row_count",
    "body_full_packet_materialized_here",
    "local_reviewer_payload_materialized_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "p5_actual_review_still_not_run",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "r54_0_scope_current_received_snapshot_refrozen",
    "r54_1_r53_source_delta_current_snapshot_override_adopted",
    "r54_2_validation_evidence_intake_done",
    "r54_3_local_only_actual_review_preflight_built",
    "r54_4_actual_review_session_envelope_built",
    "r54_5_24_case_manifest_freeze_built",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r54_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R54_R5_FALSE_KEY_REFS,
    "validation_evidence_intake_done_here",
    "local_root_preflight_passed_here",
    "explicit_allow_present_here",
    "purge_plan_verified_here",
)


def _safe_pseudonymous_reviewer_ref_r54(value: Any) -> str:
    text = clean_identifier(value, default=P7_R54_DEFAULT_REVIEWER_REF, max_length=120)
    lowered = text.lower()
    allowed = lowered.startswith(("reviewer_ref_", "pseudonymous_", "r54_reviewer_"))
    if not allowed or any(token in text for token in (" ", "@", "/", "\\")):
        return P7_R54_DEFAULT_REVIEWER_REF
    return text


def _reviewer_blind_policy_r54() -> dict[str, bool]:
    return {
        "reviewer_receives_blind_case_id": True,
        "reviewer_receives_case_ref_id": False,
        "reviewer_receives_packet_ref_id": False,
        "reviewer_receives_exact_family_label": False,
        "reviewer_receives_subscription_tier_label": False,
        "reviewer_receives_controller_expected_result": False,
        "reviewer_receives_gate_expected_result": False,
        "reviewer_receives_p5_confirmed_candidate_conditions": False,
        "reviewer_receives_p8_material_candidate_conditions": False,
        "reviewer_notes_body_stored_here": False,
        "reviewer_free_text_body_stored_here": False,
        "body_free": True,
    }


def _assert_reviewer_blind_policy_r54(policy: Mapping[str, Any]) -> None:
    data = safe_mapping(policy)
    expected_keys = {
        "reviewer_receives_blind_case_id",
        "reviewer_receives_case_ref_id",
        "reviewer_receives_packet_ref_id",
        "reviewer_receives_exact_family_label",
        "reviewer_receives_subscription_tier_label",
        "reviewer_receives_controller_expected_result",
        "reviewer_receives_gate_expected_result",
        "reviewer_receives_p5_confirmed_candidate_conditions",
        "reviewer_receives_p8_material_candidate_conditions",
        "reviewer_notes_body_stored_here",
        "reviewer_free_text_body_stored_here",
        "body_free",
    }
    if set(data) != expected_keys:
        raise ValueError("R54 reviewer blind policy fields changed")
    if data.get("reviewer_receives_blind_case_id") is not True or data.get("body_free") is not True:
        raise ValueError("R54 reviewer blind policy must expose only blind case id")
    for false_key in expected_keys - {"reviewer_receives_blind_case_id", "body_free"}:
        if data.get(false_key) is not False:
            raise ValueError(f"R54 reviewer blind policy must keep {false_key}=False")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_reviewer_blind_policy")


def _r54_count_by(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = clean_identifier(safe_mapping(row).get(key), default="unknown", max_length=160)
        counts[value] = counts.get(value, 0) + 1
    return counts


def _r54_case_refs(rows: Sequence[Mapping[str, Any]], key: str) -> list[str]:
    return [clean_identifier(safe_mapping(row).get(key), default="", max_length=180) for row in rows]


def _r54_unique_non_empty(values: Sequence[Any]) -> bool:
    refs = [clean_identifier(value, default="", max_length=180) for value in values]
    return bool(refs) and all(refs) and len(set(refs)) == len(refs)


def _r54_manifest_minimums_satisfied(rows: Sequence[Mapping[str, Any]]) -> bool:
    if len(rows) != P7_R51_REQUIRED_CASE_COUNT:
        return False
    family_counts = _r54_count_by(rows, "family")
    role_counts = _r54_count_by(rows, "case_role")
    for family, expected_count, _case_role in P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION:
        if family_counts.get(family, 0) != expected_count:
            return False
    owned_positive = sum(role_counts.get(role, 0) for role in P7_R48_P5_POSITIVE_CASE_ROLE_REFS)
    if owned_positive < 20:
        return False
    if family_counts.get("low_information_history_not_eligible", 0) < 2:
        return False
    if family_counts.get("free_tier_history_present_not_allowed", 0) < 2:
        return False
    return True


def _assert_r54_case_row(row: Mapping[str, Any]) -> None:
    data = safe_mapping(row)
    _assert_required_fields(data, required=tuple(P7_R48_P5_CASE_MATRIX_ROW_FIELD_REFS), source="p7_r54_r5_case_row")
    if data.get("body_free") is not True:
        raise ValueError("R54 case row must be body-free")
    if data.get("controller_only") is not True:
        raise ValueError("R54 case row must remain controller-only")
    for false_key in (
        "reviewer_facing_family_exposed",
        "reviewer_facing_tier_exposed",
        "body_full_packet_materialized_here",
        "local_reviewer_payload_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 case row must keep {false_key}=False")
    for required_key in ("case_ref_id", "blind_case_id", "packet_ref_id", "family", "case_role", "subscription_tier_ref"):
        if not clean_identifier(data.get(required_key), default="", max_length=180):
            raise ValueError(f"R54 case row missing {required_key}")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_r5_case_row")


def _controller_manifest_rows_from_r54_case_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row_raw in rows:
        row = safe_mapping(row_raw)
        out.append(
            {
                "case_ref_id": clean_identifier(row.get("case_ref_id"), default="case_ref", max_length=160),
                "blind_case_id": clean_identifier(row.get("blind_case_id"), default="blind_case", max_length=160),
                "packet_ref_id": clean_identifier(row.get("packet_ref_id"), default="packet_ref", max_length=160),
                "family": clean_identifier(row.get("family"), default="unknown", max_length=160),
                "case_role": clean_identifier(row.get("case_role"), default="unknown", max_length=120),
                "subscription_tier_ref": clean_identifier(row.get("subscription_tier_ref"), default="unknown", max_length=80),
                "controller_only": True,
                "reviewer_facing_identifier_policy": P7_R54_REVIEWER_IDENTIFIER_POLICY_REF,
                "reviewer_receives_blind_case_id": True,
                "reviewer_receives_case_ref_id": False,
                "reviewer_receives_family": False,
                "reviewer_receives_subscription_tier": False,
                "reviewer_receives_expected_result": False,
                "reviewer_receives_gate_result": False,
                "blind_case_id_derived_from_body_or_record_hash": False,
                "body_full_packet_materialized_here": False,
                "local_reviewer_payload_materialized_here": False,
                "body_free": True,
            }
        )
    return out


def _reviewer_facing_case_index_rows_from_r54_case_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row_raw in rows:
        row = safe_mapping(row_raw)
        out.append(
            {
                "blind_case_id": clean_identifier(row.get("blind_case_id"), default="blind_case", max_length=160),
                "reviewer_identifier_kind": P7_R54_REVIEWER_IDENTIFIER_POLICY_REF,
                "case_ref_hidden": True,
                "packet_ref_hidden": True,
                "family_hidden": True,
                "tier_hidden": True,
                "expected_result_hidden": True,
                "gate_result_hidden": True,
                "derived_from_body_or_record_hash": False,
                "body_free": True,
            }
        )
    return out


def _assert_r54_controller_manifest_row(row: Mapping[str, Any]) -> None:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R54_24_CASE_MANIFEST_CONTROLLER_ROW_FIELD_REFS, source="p7_r54_r5_controller_manifest_row")
    for true_key in ("controller_only", "reviewer_receives_blind_case_id", "body_free"):
        if data.get(true_key) is not True:
            raise ValueError(f"R54 controller row must keep {true_key}=True")
    for false_key in (
        "reviewer_receives_case_ref_id",
        "reviewer_receives_family",
        "reviewer_receives_subscription_tier",
        "reviewer_receives_expected_result",
        "reviewer_receives_gate_result",
        "blind_case_id_derived_from_body_or_record_hash",
        "body_full_packet_materialized_here",
        "local_reviewer_payload_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 controller row must keep {false_key}=False")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_r5_controller_manifest_row")


def _assert_r54_reviewer_facing_case_index_row(row: Mapping[str, Any]) -> None:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R54_REVIEWER_FACING_CASE_INDEX_ROW_FIELD_REFS, source="p7_r54_r5_reviewer_case_index_row")
    for true_key in ("case_ref_hidden", "packet_ref_hidden", "family_hidden", "tier_hidden", "expected_result_hidden", "gate_result_hidden", "body_free"):
        if data.get(true_key) is not True:
            raise ValueError(f"R54 reviewer index row must keep {true_key}=True")
    if data.get("reviewer_identifier_kind") != P7_R54_REVIEWER_IDENTIFIER_POLICY_REF:
        raise ValueError("R54 reviewer index must use blind case id only")
    if data.get("derived_from_body_or_record_hash") is not False:
        raise ValueError("R54 reviewer index row must not derive ids from body or record hash")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_r5_reviewer_case_index_row")


def _r54_r5_matrix_from_input(
    *,
    envelope: Mapping[str, Any],
    case_matrix: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if case_matrix is not None:
        matrix = safe_mapping(case_matrix)
        assert_p7_r48_p5_first_formal_review_case_matrix_contract(matrix)
        return matrix
    if envelope.get("envelope_status") != "READY_FOR_24_CASE_MANIFEST_FREEZE":
        return None
    matrix = build_p7_r48_p5_first_formal_review_case_matrix(
        review_session_id=envelope.get("review_session_id"),
        session_short_ref="r54s000",
        material_id="p7_r54_r5_inherited_r48_24_case_matrix_source",
    )
    assert_p7_r48_p5_first_formal_review_case_matrix_contract(matrix)
    return matrix


def build_p7_r54_actual_review_session_envelope_bodyfree(
    *,
    local_only_actual_review_preflight: Mapping[str, Any] | None = None,
    r3_local_only_actual_review_preflight: Mapping[str, Any] | None = None,
    reviewer_ref: Any = P7_R54_DEFAULT_REVIEWER_REF,
    material_id: Any = "p7_r54_actual_review_session_envelope_bodyfree",
) -> dict[str, Any]:
    """Build R54-4 body-free actual-review session envelope without running review."""

    if local_only_actual_review_preflight is not None and r3_local_only_actual_review_preflight is not None:
        raise ValueError("provide only one R54-3 preflight value")
    r3 = (
        safe_mapping(local_only_actual_review_preflight)
        if local_only_actual_review_preflight is not None
        else safe_mapping(r3_local_only_actual_review_preflight)
        if r3_local_only_actual_review_preflight is not None
        else build_p7_r54_local_only_actual_review_preflight_bodyfree()
    )
    assert_p7_r54_local_only_actual_review_preflight_bodyfree_contract(r3)
    ready = r3.get("preflight_status") == "R54_LOCAL_REVIEW_PREFLIGHT_READY"
    blockers = dedupe_identifiers(r3.get("execution_blocker_ids") or [], limit=40, max_length=140)
    reason_refs = ["r54_actual_review_session_envelope_ready"] if ready else ["r54_3_preflight_not_ready"]
    if not ready:
        blockers = dedupe_identifiers((*blockers, "r54_actual_review_session_preflight_not_ready"), limit=40, max_length=140)
    envelope = {
        "schema_version": P7_R54_ACTUAL_REVIEW_SESSION_ENVELOPE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_STEP,
        "scope": P7_R54_SCOPE,
        "policy_kind": P7_R54_POLICY_KIND,
        "policy_section": "R54-4_actual_review_session_envelope",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_actual_review_session_envelope_bodyfree", max_length=200),
        "review_session_id": _safe_review_session_id(r3.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r3_preflight_schema_version": P7_R54_LOCAL_ONLY_ACTUAL_REVIEW_PREFLIGHT_SCHEMA_VERSION,
        "r3_preflight_material_ref": clean_identifier(r3.get("material_id"), default="p7_r54_local_only_actual_review_preflight", max_length=200),
        "r3_preflight_status": clean_identifier(r3.get("preflight_status"), default="R54_LOCAL_REVIEW_PREFLIGHT_BLOCKED", max_length=80),
        "r3_preflight_ready_for_envelope": ready,
        "current_received_snapshot_refs": safe_mapping(r3.get("current_received_snapshot_refs")),
        "current_received_snapshot_ref_count": len(safe_mapping(r3.get("current_received_snapshot_refs"))),
        "r53_source_snapshot_refs": safe_mapping(r3.get("r53_source_snapshot_refs")),
        "r53_source_snapshot_ref_count": len(safe_mapping(r3.get("r53_source_snapshot_refs"))),
        "r53_refs_are_current_received_refs": False,
        "actual_review_basis_ref": P7_R54_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "review_session_status": "R54_ACTUAL_REVIEW_SESSION_ENVELOPE_READY" if ready else "R54_PRECHECK_BLOCKED",
        "envelope_status": "READY_FOR_24_CASE_MANIFEST_FREEZE" if ready else "BLOCKED_BY_R54_3_PREFLIGHT",
        "envelope_reason_refs": reason_refs,
        "review_prompt_version": P7_R54_REVIEW_PROMPT_VERSION,
        "reviewer_ref": _safe_pseudonymous_reviewer_ref_r54(reviewer_ref),
        "reviewer_ref_pseudonymous": True,
        "reviewer_ref_policy_ref": "pseudonymous_ref_only_no_actual_name_or_notes",
        "actual_reviewer_name_included": False,
        "reviewer_notes_included": False,
        "reviewer_notes_materialized_here": False,
        "reviewer_free_text_materialized_here": False,
        "reviewer_blind_policy": _reviewer_blind_policy_r54(),
        "reviewer_visible_field_refs": list(P7_R50_REVIEWER_VISIBLE_FIELD_REFS),
        "reviewer_hidden_field_refs": list(P7_R50_REVIEWER_HIDDEN_FIELD_REFS),
        "rating_form_version": P7_R50_RATING_FORM_VERSION,
        "rating_axis_refs": list(P5_HUMAN_BLIND_QA_RATING_AXES),
        "question_need_observation_stage_ref": P7_R50_QUESTION_NEED_OBSERVATION_STAGE_REF,
        "local_root_ref": P7_R47_STORAGE_ROOT_REF if r3.get("local_review_root_valid") is True else "not_configured_or_invalid",
        "root_path_exposed": False,
        "local_absolute_path_included": False,
        "body_full_generation_allowed": ready,
        "local_only_body_full_generation_allowed": ready,
        "disposal_plan_ref": clean_identifier(r3.get("purge_plan_ref"), default="missing_purge_plan", max_length=180),
        "disposal_plan_ready": r3.get("purge_plan_ready") is True,
        "actual_review_session_envelope_created_here": True,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "p5_actual_review_still_not_run": True,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "r54_0_scope_current_received_snapshot_refrozen": True,
        "r54_1_r53_source_delta_current_snapshot_override_adopted": True,
        "r54_2_validation_evidence_intake_done": True,
        "r54_3_local_only_actual_review_preflight_built": True,
        "r54_4_actual_review_session_envelope_built": ready,
        "implemented_steps": list(P7_R54_R4_IMPLEMENTED_STEPS) if ready else list(P7_R54_R3_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_R4_NOT_YET_IMPLEMENTED_STEPS) if ready else list(P7_R54_R3_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R54_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R54_R4_NEXT_REQUIRED_STEP_REF if ready else P7_R54_R4_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_except({
            "validation_evidence_intake_done_here",
            "local_root_preflight_passed_here",
            "explicit_allow_present_here",
            "purge_plan_verified_here",
        }),
        "validation_evidence_intake_done_here": True,
        "local_root_preflight_passed_here": r3.get("local_root_preflight_passed_here") is True,
        "explicit_allow_present_here": r3.get("explicit_allow_present_here") is True,
        "purge_plan_verified_here": r3.get("purge_plan_verified_here") is True,
    }
    assert_p7_r54_actual_review_session_envelope_bodyfree_contract(envelope)
    return envelope


def assert_p7_r54_actual_review_session_envelope_bodyfree_contract(envelope: Mapping[str, Any]) -> bool:
    data = safe_mapping(envelope)
    _assert_required_fields(
        data,
        required=P7_R54_ACTUAL_REVIEW_SESSION_ENVELOPE_REQUIRED_FIELD_REFS,
        source="p7_r54_r4_actual_review_session_envelope",
    )
    _assert_body_free_common_with_false_keys(
        data,
        schema_version=P7_R54_ACTUAL_REVIEW_SESSION_ENVELOPE_SCHEMA_VERSION,
        source="p7_r54_r4_actual_review_session_envelope",
        false_key_refs=P7_R54_R4_FALSE_KEY_REFS,
    )
    if data.get("policy_section") != "R54-4_actual_review_session_envelope":
        raise ValueError("R54 R4 policy section changed")
    if data.get("r3_preflight_schema_version") != P7_R54_LOCAL_ONLY_ACTUAL_REVIEW_PREFLIGHT_SCHEMA_VERSION:
        raise ValueError("R54 R4 R3 preflight schema reference changed")
    _assert_current_refs(data, source="p7_r54_r4_actual_review_session_envelope")
    if data.get("actual_review_basis_ref") != P7_R54_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("R54 R4 actual review basis ref changed")
    if data.get("actual_review_basis_allowed") != P7_R54_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("R54 R4 must allow only current refs as actual review basis")
    if data.get("required_case_count") != P7_R51_REQUIRED_CASE_COUNT:
        raise ValueError("R54 R4 must keep required_case_count=24")
    if data.get("review_session_status") not in P7_R54_R4_REVIEW_SESSION_STATUS_REFS:
        raise ValueError("R54 R4 review session status changed")
    if data.get("envelope_status") not in P7_R54_R4_ENVELOPE_STATUS_REFS:
        raise ValueError("R54 R4 envelope status changed")
    reviewer_ref = clean_identifier(data.get("reviewer_ref"), default="", max_length=120)
    if reviewer_ref != _safe_pseudonymous_reviewer_ref_r54(reviewer_ref) or data.get("reviewer_ref_pseudonymous") is not True:
        raise ValueError("R54 R4 reviewer_ref must be pseudonymous")
    _assert_reviewer_blind_policy_r54(safe_mapping(data.get("reviewer_blind_policy")))
    if tuple(data.get("reviewer_visible_field_refs") or ()) != P7_R50_REVIEWER_VISIBLE_FIELD_REFS:
        raise ValueError("R54 R4 reviewer visible field refs changed")
    if tuple(data.get("reviewer_hidden_field_refs") or ()) != P7_R50_REVIEWER_HIDDEN_FIELD_REFS:
        raise ValueError("R54 R4 reviewer hidden field refs changed")
    if data.get("rating_form_version") != P7_R50_RATING_FORM_VERSION:
        raise ValueError("R54 R4 rating form version changed")
    if tuple(data.get("rating_axis_refs") or ()) != P5_HUMAN_BLIND_QA_RATING_AXES:
        raise ValueError("R54 R4 rating axis refs changed")
    if data.get("question_need_observation_stage_ref") != P7_R50_QUESTION_NEED_OBSERVATION_STAGE_REF:
        raise ValueError("R54 R4 question observation stage ref changed")
    for false_key in (
        "actual_reviewer_name_included",
        "reviewer_notes_included",
        "reviewer_notes_materialized_here",
        "reviewer_free_text_materialized_here",
        "root_path_exposed",
        "local_absolute_path_included",
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_disposal_receipt_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 R4 must keep {false_key}=False")
    if data.get("actual_review_session_envelope_created_here") is not True:
        raise ValueError("R54 R4 must materialize only the body-free envelope")
    if data.get("p5_actual_review_still_not_run") is not True:
        raise ValueError("R54 R4 must not claim P5 actual review ran")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 R4 open blockers must match execution blockers")
    unknown_blockers = sorted(set(blockers) - set(P7_R54_R4_R5_ALLOWED_EXECUTION_BLOCKER_ID_REFS))
    if unknown_blockers:
        raise ValueError(f"R54 R4 execution blocker ids are not canonical: {unknown_blockers[:4]}")
    ready = data.get("r3_preflight_ready_for_envelope") is True
    if data.get("body_full_generation_allowed") is not ready:
        raise ValueError("R54 R4 body-full generation authorization must match R3 preflight readiness")
    if data.get("local_only_body_full_generation_allowed") is not ready:
        raise ValueError("R54 R4 local-only generation authorization must match R3 preflight readiness")
    for true_key in (
        "validation_evidence_intake_done_here",
        "r54_0_scope_current_received_snapshot_refrozen",
        "r54_1_r53_source_delta_current_snapshot_override_adopted",
        "r54_2_validation_evidence_intake_done",
        "r54_3_local_only_actual_review_preflight_built",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R54 R4 must keep {true_key}=True")
    if ready:
        if data.get("review_session_status") != "R54_ACTUAL_REVIEW_SESSION_ENVELOPE_READY":
            raise ValueError("R54 R4 ready review session status changed")
        if data.get("envelope_status") != "READY_FOR_24_CASE_MANIFEST_FREEZE":
            raise ValueError("R54 R4 ready envelope must point to manifest freeze")
        for true_key in (
            "local_root_preflight_passed_here",
            "explicit_allow_present_here",
            "purge_plan_verified_here",
            "disposal_plan_ready",
            "r54_4_actual_review_session_envelope_built",
        ):
            if data.get(true_key) is not True:
                raise ValueError(f"R54 R4 READY requires {true_key}=True")
        if data.get("local_root_ref") != P7_R47_STORAGE_ROOT_REF:
            raise ValueError("R54 R4 ready envelope must expose only abstract local root ref")
        if blockers:
            raise ValueError("R54 R4 ready envelope must not carry blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_R4_IMPLEMENTED_STEPS:
            raise ValueError("R54 R4 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_R4_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 R4 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_R4_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R4 ready envelope must point to R54-5")
    else:
        if data.get("review_session_status") != "R54_PRECHECK_BLOCKED":
            raise ValueError("R54 R4 blocked review session status changed")
        if data.get("envelope_status") != "BLOCKED_BY_R54_3_PREFLIGHT":
            raise ValueError("R54 R4 blocked envelope status changed")
        if data.get("r54_4_actual_review_session_envelope_built") is not False:
            raise ValueError("R54 R4 blocked envelope must not claim R54-4 built")
        if not data.get("envelope_reason_refs") or "r54_actual_review_session_preflight_not_ready" not in blockers:
            raise ValueError("R54 R4 blocked envelope must carry preflight blocker")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_R3_IMPLEMENTED_STEPS:
            raise ValueError("R54 R4 blocked implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_R3_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 R4 blocked not-yet steps changed")
        if data.get("next_required_step") != P7_R54_R4_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R4 blocked envelope must point to preflight resolution")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_r4_actual_review_session_envelope")
    return True


def build_p7_r54_24_case_manifest_freeze_bodyfree(
    *,
    actual_review_session_envelope: Mapping[str, Any] | None = None,
    r4_actual_review_session_envelope: Mapping[str, Any] | None = None,
    case_matrix: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_24_case_manifest_freeze_bodyfree",
) -> dict[str, Any]:
    """Build R54-5 body-free 24-case manifest freeze without packet generation."""

    if actual_review_session_envelope is not None and r4_actual_review_session_envelope is not None:
        raise ValueError("provide only one R54-4 envelope value")
    r4 = (
        safe_mapping(actual_review_session_envelope)
        if actual_review_session_envelope is not None
        else safe_mapping(r4_actual_review_session_envelope)
        if r4_actual_review_session_envelope is not None
        else build_p7_r54_actual_review_session_envelope_bodyfree()
    )
    assert_p7_r54_actual_review_session_envelope_bodyfree_contract(r4)
    envelope_ready = r4.get("envelope_status") == "READY_FOR_24_CASE_MANIFEST_FREEZE"
    matrix = _r54_r5_matrix_from_input(envelope=r4, case_matrix=case_matrix)
    raw_rows = [safe_mapping(row) for row in (safe_mapping(matrix).get("case_rows") if matrix else [])]
    matrix_ready = bool(matrix) and _r54_manifest_minimums_satisfied(raw_rows)
    blind_ids = _r54_case_refs(raw_rows, "blind_case_id")
    case_refs = _r54_case_refs(raw_rows, "case_ref_id")
    packet_refs = _r54_case_refs(raw_rows, "packet_ref_id")
    ids_ready = matrix_ready and _r54_unique_non_empty(blind_ids) and _r54_unique_non_empty(case_refs) and _r54_unique_non_empty(packet_refs)
    ids_separated = ids_ready and set(blind_ids).isdisjoint(set(case_refs)) and set(blind_ids).isdisjoint(set(packet_refs)) and set(case_refs).isdisjoint(set(packet_refs))
    ready = envelope_ready and matrix_ready and ids_ready and ids_separated

    blockers = dedupe_identifiers(r4.get("execution_blocker_ids") or [], limit=40, max_length=140)
    reason_refs: list[str] = []
    if not envelope_ready:
        reason_refs.append("r54_4_session_envelope_not_ready")
    if envelope_ready and not matrix_ready:
        reason_refs.append("r54_24_case_manifest_incomplete_or_distribution_changed")
        blockers.append("r54_case_manifest_incomplete")
    if envelope_ready and matrix_ready and not ids_ready:
        reason_refs.append("r54_24_case_ids_not_unique")
        blockers.append("r54_case_manifest_incomplete")
    if envelope_ready and matrix_ready and ids_ready and not ids_separated:
        reason_refs.append("r54_blind_case_case_ref_packet_ref_not_separated")
        blockers.append("r54_case_manifest_id_boundary_violation")
    blockers = dedupe_identifiers(blockers, limit=40, max_length=140)
    rows = raw_rows if ready else []
    family_counts = _r54_count_by(rows, "family")
    role_counts = _r54_count_by(rows, "case_role")
    tier_counts = _r54_count_by(rows, "subscription_tier_ref")
    manifest = {
        "schema_version": P7_R54_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_STEP,
        "scope": P7_R54_SCOPE,
        "policy_kind": P7_R54_POLICY_KIND,
        "policy_section": "R54-5_24_case_manifest_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_24_case_manifest_freeze_bodyfree", max_length=200),
        "review_session_id": _safe_review_session_id(r4.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r4_envelope_schema_version": P7_R54_ACTUAL_REVIEW_SESSION_ENVELOPE_SCHEMA_VERSION,
        "r4_envelope_material_ref": clean_identifier(r4.get("material_id"), default="p7_r54_actual_review_session_envelope_bodyfree", max_length=200),
        "r4_envelope_status": clean_identifier(r4.get("envelope_status"), default="BLOCKED_BY_R54_3_PREFLIGHT", max_length=80),
        "r4_envelope_ready_for_manifest_freeze": envelope_ready,
        "current_received_snapshot_refs": safe_mapping(r4.get("current_received_snapshot_refs")),
        "current_received_snapshot_ref_count": len(safe_mapping(r4.get("current_received_snapshot_refs"))),
        "r53_source_snapshot_refs": safe_mapping(r4.get("r53_source_snapshot_refs")),
        "r53_source_snapshot_ref_count": len(safe_mapping(r4.get("r53_source_snapshot_refs"))),
        "r53_refs_are_current_received_refs": False,
        "actual_review_basis_ref": P7_R54_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "review_session_status": "R54_24_CASE_MANIFEST_READY" if ready else "R54_PRECHECK_BLOCKED",
        "manifest_status": "READY_FOR_LOCAL_ONLY_PACKET_GENERATION_REQUEST" if ready else ("BLOCKED_BY_CASE_MATRIX_CONTRACT" if envelope_ready else "BLOCKED_BY_R54_4_ENVELOPE"),
        "manifest_reason_refs": ["r54_24_case_manifest_frozen"] if ready else dedupe_identifiers(reason_refs, limit=20, max_length=140),
        "r48_case_matrix_schema_version": P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION,
        "r48_case_matrix_ref": clean_identifier(safe_mapping(matrix).get("material_id"), default="not_frozen", max_length=180),
        "matrix_kind": P7_R54_MANIFEST_MATRIX_KIND_REF if ready else "not_frozen",
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "case_count": len(rows),
        "case_rows": rows,
        "controller_manifest_rows": _controller_manifest_rows_from_r54_case_rows(rows),
        "reviewer_facing_case_index_rows": _reviewer_facing_case_index_rows_from_r54_case_rows(rows),
        "family_case_counts": family_counts,
        "case_role_counts": role_counts,
        "subscription_tier_ref_counts": tier_counts,
        "owned_history_positive_case_count": sum(role_counts.get(role, 0) for role in P7_R48_P5_POSITIVE_CASE_ROLE_REFS),
        "boundary_case_count": sum(family_counts.get(family, 0) for family in P7_R48_P5_BOUNDARY_FAMILY_REFS),
        "low_information_boundary_case_count": family_counts.get("low_information_history_not_eligible", 0),
        "free_tier_boundary_case_count": family_counts.get("free_tier_history_present_not_allowed", 0),
        "minimums_satisfied": ready and _r54_manifest_minimums_satisfied(rows),
        "blind_case_ids_unique": ready and _r54_unique_non_empty(_r54_case_refs(rows, "blind_case_id")),
        "case_ref_ids_unique": ready and _r54_unique_non_empty(_r54_case_refs(rows, "case_ref_id")),
        "packet_ref_ids_unique": ready and _r54_unique_non_empty(_r54_case_refs(rows, "packet_ref_id")),
        "blind_case_id_case_ref_separated": ready and set(_r54_case_refs(rows, "blind_case_id")).isdisjoint(set(_r54_case_refs(rows, "case_ref_id"))),
        "blind_case_id_packet_ref_separated": ready and set(_r54_case_refs(rows, "blind_case_id")).isdisjoint(set(_r54_case_refs(rows, "packet_ref_id"))),
        "case_ref_id_packet_ref_separated": ready and set(_r54_case_refs(rows, "case_ref_id")).isdisjoint(set(_r54_case_refs(rows, "packet_ref_id"))),
        "reviewer_facing_identifier_policy": P7_R54_REVIEWER_IDENTIFIER_POLICY_REF,
        "reviewer_facing_family_exposed": False,
        "reviewer_facing_tier_exposed": False,
        "reviewer_facing_case_ref_exposed": False,
        "reviewer_facing_packet_ref_exposed": False,
        "reviewer_facing_expected_result_exposed": False,
        "reviewer_facing_hidden_metadata_exposed": False,
        "controller_keeps_family_tier_expected_refs": ready,
        "reviewer_receives_blind_case_id_only": ready,
        "reviewer_facing_row_count": len(rows),
        "controller_manifest_row_count": len(rows),
        "body_full_packet_materialized_here": False,
        "local_reviewer_payload_materialized_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "p5_actual_review_still_not_run": True,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "r54_0_scope_current_received_snapshot_refrozen": True,
        "r54_1_r53_source_delta_current_snapshot_override_adopted": True,
        "r54_2_validation_evidence_intake_done": True,
        "r54_3_local_only_actual_review_preflight_built": True,
        "r54_4_actual_review_session_envelope_built": envelope_ready,
        "r54_5_24_case_manifest_freeze_built": ready,
        "implemented_steps": list(P7_R54_R5_IMPLEMENTED_STEPS) if ready else (list(P7_R54_R4_IMPLEMENTED_STEPS) if envelope_ready else list(P7_R54_R3_IMPLEMENTED_STEPS)),
        "not_yet_implemented_steps": list(P7_R54_R5_NOT_YET_IMPLEMENTED_STEPS) if ready else (list(P7_R54_R4_NOT_YET_IMPLEMENTED_STEPS) if envelope_ready else list(P7_R54_R3_NOT_YET_IMPLEMENTED_STEPS)),
        "first_next_work_ref": P7_R54_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R54_R5_NEXT_REQUIRED_STEP_REF if ready else P7_R54_R5_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_except({
            "validation_evidence_intake_done_here",
            "local_root_preflight_passed_here",
            "explicit_allow_present_here",
            "purge_plan_verified_here",
        }),
        "validation_evidence_intake_done_here": True,
        "local_root_preflight_passed_here": r4.get("local_root_preflight_passed_here") is True,
        "explicit_allow_present_here": r4.get("explicit_allow_present_here") is True,
        "purge_plan_verified_here": r4.get("purge_plan_verified_here") is True,
    }
    assert_p7_r54_24_case_manifest_freeze_bodyfree_contract(manifest)
    return manifest


def assert_p7_r54_24_case_manifest_freeze_bodyfree_contract(manifest: Mapping[str, Any]) -> bool:
    data = safe_mapping(manifest)
    _assert_required_fields(
        data,
        required=P7_R54_24_CASE_MANIFEST_FREEZE_REQUIRED_FIELD_REFS,
        source="p7_r54_r5_24_case_manifest_freeze",
    )
    _assert_body_free_common_with_false_keys(
        data,
        schema_version=P7_R54_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION,
        source="p7_r54_r5_24_case_manifest_freeze",
        false_key_refs=P7_R54_R5_FALSE_KEY_REFS,
    )
    if data.get("policy_section") != "R54-5_24_case_manifest_freeze":
        raise ValueError("R54 R5 policy section changed")
    if data.get("r4_envelope_schema_version") != P7_R54_ACTUAL_REVIEW_SESSION_ENVELOPE_SCHEMA_VERSION:
        raise ValueError("R54 R5 R4 envelope schema reference changed")
    _assert_current_refs(data, source="p7_r54_r5_24_case_manifest_freeze")
    if data.get("actual_review_basis_ref") != P7_R54_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("R54 R5 actual review basis ref changed")
    if data.get("actual_review_basis_allowed") != P7_R54_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("R54 R5 must allow only current refs as actual review basis")
    if data.get("review_session_status") not in P7_R54_R5_REVIEW_SESSION_STATUS_REFS:
        raise ValueError("R54 R5 review session status changed")
    if data.get("manifest_status") not in P7_R54_R5_MANIFEST_STATUS_REFS:
        raise ValueError("R54 R5 manifest status changed")
    if data.get("required_case_count") != P7_R51_REQUIRED_CASE_COUNT:
        raise ValueError("R54 R5 must keep required_case_count=24")
    if data.get("r48_case_matrix_schema_version") != P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION:
        raise ValueError("R54 R5 R48 case matrix schema reference changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 R5 open blockers must match execution blockers")
    unknown_blockers = sorted(set(blockers) - set(P7_R54_R4_R5_ALLOWED_EXECUTION_BLOCKER_ID_REFS))
    if unknown_blockers:
        raise ValueError(f"R54 R5 execution blocker ids are not canonical: {unknown_blockers[:4]}")
    for false_key in (
        "reviewer_facing_family_exposed",
        "reviewer_facing_tier_exposed",
        "reviewer_facing_case_ref_exposed",
        "reviewer_facing_packet_ref_exposed",
        "reviewer_facing_expected_result_exposed",
        "reviewer_facing_hidden_metadata_exposed",
        "body_full_packet_materialized_here",
        "local_reviewer_payload_materialized_here",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_disposal_receipt_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 R5 must keep {false_key}=False")
    if data.get("p5_actual_review_still_not_run") is not True:
        raise ValueError("R54 R5 must not claim actual P5 review ran")
    for true_key in (
        "validation_evidence_intake_done_here",
        "r54_0_scope_current_received_snapshot_refrozen",
        "r54_1_r53_source_delta_current_snapshot_override_adopted",
        "r54_2_validation_evidence_intake_done",
        "r54_3_local_only_actual_review_preflight_built",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R54 R5 must keep {true_key}=True")
    rows = [safe_mapping(row) for row in (data.get("case_rows") or [])]
    ready = data.get("manifest_status") == "READY_FOR_LOCAL_ONLY_PACKET_GENERATION_REQUEST"
    if ready:
        if data.get("review_session_status") != "R54_24_CASE_MANIFEST_READY":
            raise ValueError("R54 R5 ready review session status changed")
        if data.get("r4_envelope_ready_for_manifest_freeze") is not True or data.get("r54_4_actual_review_session_envelope_built") is not True:
            raise ValueError("R54 R5 ready manifest requires R54-4 ready envelope")
        if len(rows) != P7_R51_REQUIRED_CASE_COUNT or data.get("case_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 R5 ready manifest must freeze exactly 24 cases")
        for row in rows:
            _assert_r54_case_row(row)
        controller_rows = [safe_mapping(row) for row in (data.get("controller_manifest_rows") or [])]
        reviewer_rows = [safe_mapping(row) for row in (data.get("reviewer_facing_case_index_rows") or [])]
        if len(controller_rows) != P7_R51_REQUIRED_CASE_COUNT or len(reviewer_rows) != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 R5 manifest rows must match 24 cases")
        for row in controller_rows:
            _assert_r54_controller_manifest_row(row)
        for row in reviewer_rows:
            _assert_r54_reviewer_facing_case_index_row(row)
        blind_ids = _r54_case_refs(rows, "blind_case_id")
        case_refs = _r54_case_refs(rows, "case_ref_id")
        packet_refs = _r54_case_refs(rows, "packet_ref_id")
        for key, values in (("blind_case_ids_unique", blind_ids), ("case_ref_ids_unique", case_refs), ("packet_ref_ids_unique", packet_refs)):
            if data.get(key) is not True or not _r54_unique_non_empty(values):
                raise ValueError(f"R54 R5 {key} failed")
        if data.get("blind_case_id_case_ref_separated") is not True or not set(blind_ids).isdisjoint(set(case_refs)):
            raise ValueError("R54 R5 blind ids and case refs must be separated")
        if data.get("blind_case_id_packet_ref_separated") is not True or not set(blind_ids).isdisjoint(set(packet_refs)):
            raise ValueError("R54 R5 blind ids and packet refs must be separated")
        if data.get("case_ref_id_packet_ref_separated") is not True or not set(case_refs).isdisjoint(set(packet_refs)):
            raise ValueError("R54 R5 case refs and packet refs must be separated")
        if data.get("family_case_counts") != _r54_count_by(rows, "family"):
            raise ValueError("R54 R5 family counts changed")
        if data.get("case_role_counts") != _r54_count_by(rows, "case_role"):
            raise ValueError("R54 R5 role counts changed")
        if data.get("subscription_tier_ref_counts") != _r54_count_by(rows, "subscription_tier_ref"):
            raise ValueError("R54 R5 tier counts changed")
        for family, expected_count, _case_role in P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION:
            if data["family_case_counts"].get(family, 0) != expected_count:
                raise ValueError("R54 R5 family distribution changed")
        if data.get("boundary_case_count") != 4 or data.get("low_information_boundary_case_count") != 2 or data.get("free_tier_boundary_case_count") != 2:
            raise ValueError("R54 R5 boundary cases changed")
        if data.get("minimums_satisfied") is not True or not _r54_manifest_minimums_satisfied(rows):
            raise ValueError("R54 R5 ready manifest minimums not satisfied")
        if data.get("reviewer_facing_identifier_policy") != P7_R54_REVIEWER_IDENTIFIER_POLICY_REF:
            raise ValueError("R54 R5 reviewer identifier policy changed")
        if data.get("controller_keeps_family_tier_expected_refs") is not True:
            raise ValueError("R54 R5 controller must keep family/tier/expected refs")
        if data.get("reviewer_receives_blind_case_id_only") is not True:
            raise ValueError("R54 R5 reviewer must receive blind_case_id only")
        if data.get("reviewer_facing_row_count") != P7_R51_REQUIRED_CASE_COUNT or data.get("controller_manifest_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 R5 row counts changed")
        if blockers:
            raise ValueError("R54 R5 ready manifest must not carry blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_R5_IMPLEMENTED_STEPS:
            raise ValueError("R54 R5 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_R5_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 R5 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_R5_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R5 ready manifest must point to R54-6")
    else:
        if rows or data.get("case_count") != 0:
            raise ValueError("R54 R5 blocked manifest must not freeze case rows")
        if data.get("r54_5_24_case_manifest_freeze_built") is not False:
            raise ValueError("R54 R5 blocked manifest must not claim R54-5 built")
        if not data.get("manifest_reason_refs"):
            raise ValueError("R54 R5 blocked manifest must carry reasons")
        if data.get("next_required_step") != P7_R54_R5_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R5 blocked manifest must point to manifest resolution")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_r5_24_case_manifest_freeze")
    return True



# Compatibility aliases matching the shorter R54-2/R54-3 design wording.
build_p7_r54_validation_evidence_intake = build_p7_r54_validation_evidence_intake_bodyfree
assert_p7_r54_validation_evidence_intake_contract = assert_p7_r54_validation_evidence_intake_bodyfree_contract
build_p7_r54_local_only_actual_review_preflight = build_p7_r54_local_only_actual_review_preflight_bodyfree
assert_p7_r54_local_only_actual_review_preflight_contract = assert_p7_r54_local_only_actual_review_preflight_bodyfree_contract

# ---------------------------------------------------------------------------
# R54-6 / R54-7 packet request and packet scan body-free contracts
# ---------------------------------------------------------------------------

P7_R54_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.local_only_body_full_packet_generation_request.bodyfree.v1"
)
P7_R54_PACKET_GENERATION_REQUEST_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.packet_generation_request_row.bodyfree.v1"
)
P7_R54_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.packet_completeness_export_denylist_scan.bodyfree.v1"
)
P7_R54_PACKET_COMPLETION_SCAN_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.packet_completion_scan_row.bodyfree.v1"
)

P7_R54_R6_STEP_REF: Final = "R54-6_local_only_body_full_packet_generation_request"
P7_R54_R7_STEP_REF: Final = "R54-7_packet_completeness_export_denylist_scan"
P7_R54_R6_NEXT_REQUIRED_STEP_REF: Final = "R54-7_packet_completeness_export_denylist_scan"
P7_R54_R6_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R54-6_packet_generation_request_before_R54-7_scan"
P7_R54_R7_NEXT_REQUIRED_STEP_REF: Final = "R54-8_reviewer_instruction_rating_form_freeze"
P7_R54_R7_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R54-7_packet_scan_before_R54-8_review_form"
P7_R54_R7_PURGE_REQUIRED_NEXT_STEP_REF: Final = "R54-16_purge_disposal_receipt_required_before_review"

P7_R54_FUTURE_STEPS_AFTER_R7: Final[tuple[str, ...]] = tuple(
    step for step in P7_R54_R5_NOT_YET_IMPLEMENTED_STEPS if step not in {P7_R54_R6_STEP_REF, P7_R54_R7_STEP_REF}
)
P7_R54_R6_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_R5_IMPLEMENTED_STEPS, P7_R54_R6_STEP_REF)
P7_R54_R6_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_R7_STEP_REF, *P7_R54_FUTURE_STEPS_AFTER_R7)
P7_R54_R7_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_R6_IMPLEMENTED_STEPS, P7_R54_R7_STEP_REF)
P7_R54_R7_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_FUTURE_STEPS_AFTER_R7

P7_R54_R6_R7_ALLOWED_EXECUTION_BLOCKER_ID_REFS: Final[frozenset[str]] = frozenset(
    (
        *P7_R54_R4_R5_ALLOWED_EXECUTION_BLOCKER_ID_REFS,
        "r54_packet_generation_request_manifest_not_ready",
        "r54_body_full_packet_generation_request_blocked",
        "r54_packet_generation_request_not_ready",
        "r54_packet_generation_request_row_count_mismatch",
        "r54_packet_completeness_rows_missing",
        "r54_packet_completion_rows_missing_or_incomplete",
        "r54_packet_completeness_row_count_mismatch",
        "r54_packet_completeness_required_fields_missing",
        "r54_packet_export_denylist_violation",
        "r54_packet_export_candidate_body_full_ref_detected",
    )
)
P7_R54_R6_FALSE_KEY_REFS: Final[tuple[str, ...]] = P7_R54_R5_FALSE_KEY_REFS
P7_R54_R7_FALSE_KEY_REFS: Final[tuple[str, ...]] = P7_R54_R5_FALSE_KEY_REFS

P7_R54_PACKET_GENERATION_REQUEST_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "request_row_ref",
    "blind_case_id",
    "case_ref_id",
    "packet_ref_id",
    "request_status_ref",
    "local_only_required",
    "explicit_allow_required",
    "purge_plan_required",
    "export_denylist_required",
    "disposal_required",
    "disposal_receipt_required",
    "must_not_export",
    "request_created_here",
    "body_full_writer_invoked_here",
    "body_full_packet_materialized_here",
    "local_file_written_here",
    "raw_input_included",
    "returned_surface_included",
    "history_body_included",
    "comment_text_included",
    "reviewer_free_text_included",
    "question_text_included",
    "draft_question_text_included",
    "local_absolute_path_included",
    "body_content_hash_included",
    "packet_content_hash_included",
    "body_free",
)

P7_R54_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "r5_manifest_schema_version", "r5_manifest_material_ref", "r5_manifest_status", "r5_manifest_ready_for_packet_request",
    "current_received_snapshot_refs", "current_received_snapshot_ref_count", "r53_source_snapshot_refs", "r53_source_snapshot_ref_count", "r53_refs_are_current_received_refs",
    "required_case_count", "manifest_case_count", "packet_generation_request_row_count", "packet_generation_request_rows",
    "packet_request_blind_case_ids", "packet_request_case_ref_ids", "packet_request_packet_ref_ids",
    "packet_request_blind_case_ids_unique", "packet_request_case_ref_ids_unique", "packet_request_packet_ref_ids_unique",
    "blind_case_id_case_ref_separated", "blind_case_id_packet_ref_separated", "case_ref_id_packet_ref_separated",
    "generation_request_status", "review_session_status", "local_only_body_full_generation_allowed",
    "request_is_body_free", "body_full_writer_invocation_allowed_only_with_explicit_allow",
    "explicit_allow_verified_by_r54_3", "purge_plan_verified_by_r54_3", "export_denylist_present_by_r54_3", "retention_policy_present_by_r54_3",
    "body_full_packet_generation_request_created_here", "body_full_writer_invoked_here", "body_full_packet_generated_here", "actual_body_full_packet_generated_here",
    "actual_human_review_run_here", "actual_manual_review_run_here", "actual_rating_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_disposal_receipt_materialized_here",
    "raw_input_included", "returned_surface_included", "history_body_included", "comment_text_included", "reviewer_free_text_included", "question_text_included", "draft_question_text_included",
    "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included", "body_full_packet_export_allowed", "local_packet_exported", "body_full_packet_zip_included",
    "execution_blocker_ids", "open_execution_blocker_ids", "request_reason_refs",
    "r54_0_scope_current_received_snapshot_refrozen", "r54_1_r53_source_delta_current_snapshot_override_adopted", "r54_2_validation_evidence_intake_done", "r54_3_local_only_actual_review_preflight_built", "r54_4_actual_review_session_envelope_built", "r54_5_24_case_manifest_freeze_built", "r54_6_local_only_body_full_packet_generation_request_built",
    "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract", "r54_public_no_touch_contract", "body_free_markers", "body_free",
    *P7_R54_R6_FALSE_KEY_REFS,
    "validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here",
)

P7_R54_PACKET_COMPLETION_SCAN_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "blind_case_id", "packet_ref_id", "packet_completion_row_ref", "completion_status_ref", "packet_present_local_only", "required_body_full_review_packet_fields_present", "completion_scan_body_free",
    "body_full_packet_materialized_here", "local_packet_exported", "body_full_packet_export_candidate", "export_denylist_violation",
    "raw_input_included", "returned_surface_included", "history_body_included", "comment_text_included", "reviewer_free_text_included", "question_text_included", "draft_question_text_included",
    "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included", "body_free",
)

P7_R54_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "r6_packet_generation_request_schema_version", "r6_packet_generation_request_material_ref", "r6_generation_request_status", "r6_ready_for_packet_scan",
    "current_received_snapshot_refs", "current_received_snapshot_ref_count", "r53_source_snapshot_refs", "r53_source_snapshot_ref_count", "r53_refs_are_current_received_refs",
    "required_case_count", "packet_request_row_count", "packet_completion_row_count", "packet_completion_rows", "packet_completion_blind_case_ids", "packet_completion_packet_ref_ids",
    "packet_completion_blind_case_ids_unique", "packet_completion_packet_ref_ids_unique", "packet_completion_row_count_matches_request", "all_required_packet_fields_present",
    "packet_completeness_scan_status", "review_session_status", "ready_for_actual_human_review", "review_must_not_start_before_scan_ready", "violation_routes_to_purge_before_review",
    "export_candidate_count", "export_denied_candidate_count", "export_denylist_violation_refs", "body_full_export_candidate_ref_count", "export_candidate_refs_body_free_only",
    "local_packet_exported", "body_full_packet_export_allowed", "body_full_packet_zip_included", "body_full_packet_generated_here", "actual_body_full_packet_generated_here", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_rating_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_disposal_receipt_materialized_here",
    "raw_input_included", "returned_surface_included", "history_body_included", "comment_text_included", "reviewer_free_text_included", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included",
    "execution_blocker_ids", "open_execution_blocker_ids", "scan_reason_refs",
    "r54_0_scope_current_received_snapshot_refrozen", "r54_1_r53_source_delta_current_snapshot_override_adopted", "r54_2_validation_evidence_intake_done", "r54_3_local_only_actual_review_preflight_built", "r54_4_actual_review_session_envelope_built", "r54_5_24_case_manifest_freeze_built", "r54_6_local_only_body_full_packet_generation_request_built", "r54_7_packet_completeness_export_denylist_scan_built",
    "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract", "r54_public_no_touch_contract", "body_free_markers", "body_free",
    *P7_R54_R7_FALSE_KEY_REFS,
    "validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here",
)


def _r54_parent_current_refs(parent: Mapping[str, Any]) -> dict[str, Any]:
    refs = safe_mapping(parent.get("current_received_snapshot_refs"))
    return dict(refs) if refs else dict(P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS)


def _r54_parent_r53_refs(parent: Mapping[str, Any]) -> dict[str, Any]:
    refs = safe_mapping(parent.get("r53_source_snapshot_refs"))
    return dict(refs) if refs else dict(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS)


def _r54_generation_request_row(case_row: Mapping[str, Any], index: int) -> dict[str, Any]:
    row = safe_mapping(case_row)
    request_row = {
        "schema_version": P7_R54_PACKET_GENERATION_REQUEST_ROW_SCHEMA_VERSION,
        "request_row_ref": f"p7_r54_packet_generation_request_row_{index:03d}",
        "blind_case_id": clean_identifier(row.get("blind_case_id"), default=f"blind_case_{index:03d}", max_length=180),
        "case_ref_id": clean_identifier(row.get("case_ref_id"), default=f"case_ref_{index:03d}", max_length=180),
        "packet_ref_id": clean_identifier(row.get("packet_ref_id"), default=f"packet_ref_{index:03d}", max_length=180),
        "request_status_ref": "REQUEST_READY_NOT_GENERATED",
        "local_only_required": True,
        "explicit_allow_required": True,
        "purge_plan_required": True,
        "export_denylist_required": True,
        "disposal_required": True,
        "disposal_receipt_required": True,
        "must_not_export": True,
        "request_created_here": True,
        "body_full_writer_invoked_here": False,
        "body_full_packet_materialized_here": False,
        "local_file_written_here": False,
        "raw_input_included": False,
        "returned_surface_included": False,
        "history_body_included": False,
        "comment_text_included": False,
        "reviewer_free_text_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_absolute_path_included": False,
        "body_content_hash_included": False,
        "packet_content_hash_included": False,
        "body_free": True,
    }
    assert_p7_r54_packet_generation_request_row_bodyfree_contract(request_row)
    return request_row


def assert_p7_r54_packet_generation_request_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R54_PACKET_GENERATION_REQUEST_ROW_REQUIRED_FIELD_REFS, source="p7_r54_packet_generation_request_row")
    if data.get("schema_version") != P7_R54_PACKET_GENERATION_REQUEST_ROW_SCHEMA_VERSION:
        raise ValueError("R54 R6 packet generation request row schema changed")
    for key in ("local_only_required", "explicit_allow_required", "purge_plan_required", "export_denylist_required", "disposal_required", "disposal_receipt_required", "must_not_export", "request_created_here", "body_free"):
        if data.get(key) is not True:
            raise ValueError(f"R54 R6 request row must keep {key}=True")
    for key in ("body_full_writer_invoked_here", "body_full_packet_materialized_here", "local_file_written_here", "raw_input_included", "returned_surface_included", "history_body_included", "comment_text_included", "reviewer_free_text_included", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included"):
        if data.get(key) is not False:
            raise ValueError(f"R54 R6 request row must keep {key}=False")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_packet_generation_request_row")
    return True


def build_p7_r54_local_only_body_full_packet_generation_request_bodyfree(
    *,
    case_manifest_freeze: Mapping[str, Any] | None = None,
    r5_case_manifest_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_local_only_body_full_packet_generation_request",
) -> dict[str, Any]:
    """Create a body-free R54-6 request; no body-full writer is run here."""

    if case_manifest_freeze is not None and r5_case_manifest_freeze is not None:
        raise ValueError("provide only one R54-5 manifest value")
    r5 = safe_mapping(case_manifest_freeze if case_manifest_freeze is not None else r5_case_manifest_freeze)
    if r5:
        assert_p7_r54_24_case_manifest_freeze_bodyfree_contract(r5)
    manifest_ready = r5.get("manifest_status") == "READY_FOR_LOCAL_ONLY_PACKET_GENERATION_REQUEST"
    case_rows = [safe_mapping(row) for row in (r5.get("case_rows") or [])] if manifest_ready else []
    blockers = dedupe_identifiers(r5.get("open_execution_blocker_ids") or [], limit=60, max_length=140)
    if not manifest_ready:
        blockers = dedupe_identifiers((*blockers, "r54_packet_generation_request_manifest_not_ready", "r54_body_full_packet_generation_request_blocked"), limit=60, max_length=140)
    if manifest_ready and len(case_rows) != P7_R51_REQUIRED_CASE_COUNT:
        blockers = dedupe_identifiers((*blockers, "r54_packet_generation_request_row_count_mismatch"), limit=60, max_length=140)
    ready = manifest_ready and len(case_rows) == P7_R51_REQUIRED_CASE_COUNT and not blockers
    rows = [_r54_generation_request_row(row, i) for i, row in enumerate(case_rows, start=1)] if ready else []
    blind_ids = _r54_case_refs(rows, "blind_case_id")
    case_refs = _r54_case_refs(rows, "case_ref_id")
    packet_refs = _r54_case_refs(rows, "packet_ref_id")
    current_refs = _r54_parent_current_refs(r5)
    r53_refs = _r54_parent_r53_refs(r5)
    material = {
        "schema_version": P7_R54_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_STEP,
        "scope": P7_R54_SCOPE,
        "policy_kind": P7_R54_POLICY_KIND,
        "policy_section": "R54-6_local_only_body_full_packet_generation_request",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_local_only_body_full_packet_generation_request", max_length=200),
        "review_session_id": _safe_review_session_id(r5.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r5_manifest_schema_version": P7_R54_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION,
        "r5_manifest_material_ref": clean_identifier(r5.get("material_id"), default="missing_r54_5_manifest", max_length=200),
        "r5_manifest_status": clean_identifier(r5.get("manifest_status"), default="MISSING_R54_5_MANIFEST", max_length=120),
        "r5_manifest_ready_for_packet_request": manifest_ready,
        "current_received_snapshot_refs": current_refs,
        "current_received_snapshot_ref_count": len(current_refs),
        "r53_source_snapshot_refs": r53_refs,
        "r53_source_snapshot_ref_count": len(r53_refs),
        "r53_refs_are_current_received_refs": False,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "manifest_case_count": len(case_rows) if manifest_ready else 0,
        "packet_generation_request_row_count": len(rows),
        "packet_generation_request_rows": rows,
        "packet_request_blind_case_ids": blind_ids,
        "packet_request_case_ref_ids": case_refs,
        "packet_request_packet_ref_ids": packet_refs,
        "packet_request_blind_case_ids_unique": _r54_unique_non_empty(blind_ids) if ready else False,
        "packet_request_case_ref_ids_unique": _r54_unique_non_empty(case_refs) if ready else False,
        "packet_request_packet_ref_ids_unique": _r54_unique_non_empty(packet_refs) if ready else False,
        "blind_case_id_case_ref_separated": bool(ready and set(blind_ids).isdisjoint(set(case_refs))),
        "blind_case_id_packet_ref_separated": bool(ready and set(blind_ids).isdisjoint(set(packet_refs))),
        "case_ref_id_packet_ref_separated": bool(ready and set(case_refs).isdisjoint(set(packet_refs))),
        "generation_request_status": "READY_FOR_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN" if ready else "BLOCKED_BY_R54_5_MANIFEST",
        "review_session_status": "R54_READY_FOR_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN" if ready else "R54_PACKET_GENERATION_REQUEST_BLOCKED",
        "local_only_body_full_generation_allowed": ready,
        "request_is_body_free": True,
        "body_full_writer_invocation_allowed_only_with_explicit_allow": ready,
        "explicit_allow_verified_by_r54_3": r5.get("explicit_allow_present_here") is True,
        "purge_plan_verified_by_r54_3": r5.get("purge_plan_verified_here") is True,
        "export_denylist_present_by_r54_3": bool(manifest_ready),
        "retention_policy_present_by_r54_3": bool(manifest_ready),
        "body_full_packet_generation_request_created_here": ready,
        "body_full_writer_invoked_here": False,
        "body_full_packet_generated_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "raw_input_included": False,
        "returned_surface_included": False,
        "history_body_included": False,
        "comment_text_included": False,
        "reviewer_free_text_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_absolute_path_included": False,
        "body_content_hash_included": False,
        "packet_content_hash_included": False,
        "body_full_packet_export_allowed": False,
        "local_packet_exported": False,
        "body_full_packet_zip_included": False,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "request_reason_refs": ["r54_6_body_free_request_ready_no_writer_run"] if ready else ["r54_6_manifest_not_ready"],
        **_false_flags_except({"validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here"}),
        "r54_0_scope_current_received_snapshot_refrozen": r5.get("r54_0_scope_current_received_snapshot_refrozen") is True,
        "r54_1_r53_source_delta_current_snapshot_override_adopted": r5.get("r54_1_r53_source_delta_current_snapshot_override_adopted") is True,
        "r54_2_validation_evidence_intake_done": r5.get("r54_2_validation_evidence_intake_done") is True,
        "r54_3_local_only_actual_review_preflight_built": r5.get("r54_3_local_only_actual_review_preflight_built") is True,
        "r54_4_actual_review_session_envelope_built": r5.get("r54_4_actual_review_session_envelope_built") is True,
        "r54_5_24_case_manifest_freeze_built": r5.get("r54_5_24_case_manifest_freeze_built") is True,
        "r54_6_local_only_body_full_packet_generation_request_built": ready,
        "implemented_steps": list(P7_R54_R6_IMPLEMENTED_STEPS) if ready else list(P7_R54_R5_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_R6_NOT_YET_IMPLEMENTED_STEPS) if ready else list(P7_R54_R5_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R54_R6_NEXT_REQUIRED_STEP_REF if ready else P7_R54_R6_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "next_required_step": P7_R54_R6_NEXT_REQUIRED_STEP_REF if ready else P7_R54_R6_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "validation_evidence_intake_done_here": r5.get("validation_evidence_intake_done_here") is True,
        "local_root_preflight_passed_here": r5.get("local_root_preflight_passed_here") is True,
        "explicit_allow_present_here": r5.get("explicit_allow_present_here") is True,
        "purge_plan_verified_here": r5.get("purge_plan_verified_here") is True,
    }
    assert_p7_r54_local_only_body_full_packet_generation_request_bodyfree_contract(material)
    return material


def assert_p7_r54_local_only_body_full_packet_generation_request_bodyfree_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_REQUIRED_FIELD_REFS, source="p7_r54_local_only_body_full_packet_generation_request")
    _assert_body_free_common_with_false_keys(data, schema_version=P7_R54_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION, source="p7_r54_local_only_body_full_packet_generation_request", false_key_refs=P7_R54_R6_FALSE_KEY_REFS)
    _assert_current_refs(data, source="p7_r54_local_only_body_full_packet_generation_request")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=60, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 R6 open blockers must match execution blockers")
    if set(blockers) - set(P7_R54_R6_R7_ALLOWED_EXECUTION_BLOCKER_ID_REFS):
        raise ValueError("R54 R6 has non-canonical blocker ids")
    for key in ("body_full_writer_invoked_here", "body_full_packet_generated_here", "actual_body_full_packet_generated_here", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_rating_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_disposal_receipt_materialized_here", "raw_input_included", "returned_surface_included", "history_body_included", "comment_text_included", "reviewer_free_text_included", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included", "body_full_packet_export_allowed", "local_packet_exported", "body_full_packet_zip_included"):
        if data.get(key) is not False:
            raise ValueError(f"R54 R6 must keep {key}=False")
    ready = data.get("generation_request_status") == "READY_FOR_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN"
    rows = [safe_mapping(row) for row in (data.get("packet_generation_request_rows") or [])]
    if ready:
        if len(rows) != P7_R51_REQUIRED_CASE_COUNT or data.get("packet_generation_request_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 R6 ready request must contain exactly 24 request rows")
        for row in rows:
            assert_p7_r54_packet_generation_request_row_bodyfree_contract(row)
        blind_ids = _r54_case_refs(rows, "blind_case_id")
        case_refs = _r54_case_refs(rows, "case_ref_id")
        packet_refs = _r54_case_refs(rows, "packet_ref_id")
        if data.get("packet_request_blind_case_ids") != blind_ids or data.get("packet_request_case_ref_ids") != case_refs or data.get("packet_request_packet_ref_ids") != packet_refs:
            raise ValueError("R54 R6 request ids changed")
        for key in ("packet_request_blind_case_ids_unique", "packet_request_case_ref_ids_unique", "packet_request_packet_ref_ids_unique", "blind_case_id_case_ref_separated", "blind_case_id_packet_ref_separated", "case_ref_id_packet_ref_separated", "local_only_body_full_generation_allowed", "request_is_body_free", "body_full_writer_invocation_allowed_only_with_explicit_allow", "r54_6_local_only_body_full_packet_generation_request_built"):
            if data.get(key) is not True:
                raise ValueError(f"R54 R6 ready request must keep {key}=True")
        if blockers:
            raise ValueError("R54 R6 ready request must not carry blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_R6_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_R6_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 R6 step lists changed")
        if data.get("next_required_step") != P7_R54_R6_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R6 ready request next step changed")
    else:
        if rows or data.get("packet_generation_request_row_count") != 0:
            raise ValueError("R54 R6 blocked request must not create rows")
        if data.get("r54_6_local_only_body_full_packet_generation_request_built") is not False:
            raise ValueError("R54 R6 blocked request must not claim built")
        if data.get("next_required_step") != P7_R54_R6_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R6 blocked request next step changed")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_local_only_body_full_packet_generation_request")
    return True


def build_p7_r54_packet_completion_scan_row_bodyfree(*, blind_case_id: Any, packet_ref_id: Any, index: int = 1, packet_present_local_only: bool = True, required_body_full_review_packet_fields_present: bool = True, export_denylist_violation: bool = False, body_full_packet_export_candidate: bool = False) -> dict[str, Any]:
    row = {
        "schema_version": P7_R54_PACKET_COMPLETION_SCAN_ROW_SCHEMA_VERSION,
        "blind_case_id": clean_identifier(blind_case_id, default=f"blind_case_{index:03d}", max_length=180),
        "packet_ref_id": clean_identifier(packet_ref_id, default=f"packet_ref_{index:03d}", max_length=180),
        "packet_completion_row_ref": f"p7_r54_packet_completion_scan_row_{index:03d}",
        "completion_status_ref": "LOCAL_ONLY_PACKET_PRESENT_BODY_FREE_SCAN" if packet_present_local_only else "LOCAL_ONLY_PACKET_MISSING_BODY_FREE_SCAN",
        "packet_present_local_only": bool(packet_present_local_only),
        "required_body_full_review_packet_fields_present": bool(required_body_full_review_packet_fields_present),
        "completion_scan_body_free": True,
        "body_full_packet_materialized_here": False,
        "local_packet_exported": False,
        "body_full_packet_export_candidate": bool(body_full_packet_export_candidate),
        "export_denylist_violation": bool(export_denylist_violation),
        "raw_input_included": False,
        "returned_surface_included": False,
        "history_body_included": False,
        "comment_text_included": False,
        "reviewer_free_text_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_absolute_path_included": False,
        "body_content_hash_included": False,
        "packet_content_hash_included": False,
        "body_free": True,
    }
    assert_p7_r54_packet_completion_scan_row_bodyfree_contract(row)
    return row


def assert_p7_r54_packet_completion_scan_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R54_PACKET_COMPLETION_SCAN_ROW_REQUIRED_FIELD_REFS, source="p7_r54_packet_completion_scan_row")
    if data.get("schema_version") != P7_R54_PACKET_COMPLETION_SCAN_ROW_SCHEMA_VERSION:
        raise ValueError("R54 R7 scan row schema changed")
    for key in ("completion_scan_body_free", "body_free"):
        if data.get(key) is not True:
            raise ValueError(f"R54 R7 scan row must keep {key}=True")
    for key in ("body_full_packet_materialized_here", "local_packet_exported", "raw_input_included", "returned_surface_included", "history_body_included", "comment_text_included", "reviewer_free_text_included", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included"):
        if data.get(key) is not False:
            raise ValueError(f"R54 R7 scan row must keep {key}=False")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_packet_completion_scan_row")
    return True


def _r54_export_candidate_ref_is_body_full(candidate_ref: Any) -> bool:
    ref = str(candidate_ref or "").lower()
    return any(token in ref for token in ("body_full", "body-full", "packet_body", "reviewer_notes", "raw_input", "returned_surface", "history_body"))


def build_p7_r54_packet_completeness_export_denylist_scan_bodyfree(*, packet_generation_request: Mapping[str, Any] | None = None, r6_packet_generation_request: Mapping[str, Any] | None = None, packet_completion_rows: Sequence[Mapping[str, Any]] | None = None, export_candidate_refs: Sequence[Any] | Any | None = None, material_id: Any = "p7_r54_packet_completeness_export_denylist_scan") -> dict[str, Any]:
    if packet_generation_request is not None and r6_packet_generation_request is not None:
        raise ValueError("provide only one R54-6 request value")
    r6 = safe_mapping(packet_generation_request if packet_generation_request is not None else r6_packet_generation_request)
    if r6:
        assert_p7_r54_local_only_body_full_packet_generation_request_bodyfree_contract(r6)
    ready_request = r6.get("generation_request_status") == "READY_FOR_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN"
    request_rows = [safe_mapping(row) for row in (r6.get("packet_generation_request_rows") or [])]
    rows = [safe_mapping(row) for row in (packet_completion_rows or [])]
    for row in rows:
        assert_p7_r54_packet_completion_scan_row_bodyfree_contract(row)
    candidate_count, denied_count, denied_refs = _export_denylist_summary_r54(export_candidate_refs)
    export_candidates = _export_candidate_sequence_r54(export_candidate_refs)
    body_full_candidate_count = sum(1 for ref in export_candidates if _r54_export_candidate_ref_is_body_full(ref))
    blockers: list[str] = []
    if not ready_request:
        blockers.append("r54_packet_generation_request_manifest_not_ready")
    if not rows:
        blockers.append("r54_packet_completeness_rows_missing")
        blockers.append("r54_packet_completion_rows_missing_or_incomplete")
    if rows and len(rows) != P7_R51_REQUIRED_CASE_COUNT:
        blockers.append("r54_packet_completeness_row_count_mismatch")
        blockers.append("r54_packet_completion_rows_missing_or_incomplete")
    if any(row.get("packet_present_local_only") is not True or row.get("required_body_full_review_packet_fields_present") is not True for row in rows):
        blockers.append("r54_packet_completeness_required_fields_missing")
    if any(row.get("export_denylist_violation") is True for row in rows) or denied_count > 0:
        blockers.append("r54_packet_export_denylist_violation")
    if any(row.get("body_full_packet_export_candidate") is True for row in rows) or body_full_candidate_count > 0:
        blockers.append("r54_packet_export_candidate_body_full_ref_detected")
    completion_blind_ids = _r54_case_refs(rows, "blind_case_id")
    completion_packet_refs = _r54_case_refs(rows, "packet_ref_id")
    request_blind_ids = _r54_case_refs(request_rows, "blind_case_id")
    request_packet_refs = _r54_case_refs(request_rows, "packet_ref_id")
    if rows and (completion_blind_ids != request_blind_ids or completion_packet_refs != request_packet_refs):
        blockers.append("r54_packet_completeness_row_count_mismatch")
        blockers.append("r54_packet_completion_rows_missing_or_incomplete")
    open_blockers = dedupe_identifiers(blockers, limit=60, max_length=140)
    ready = ready_request and len(rows) == P7_R51_REQUIRED_CASE_COUNT and not open_blockers
    routes_to_purge = "r54_packet_export_denylist_violation" in open_blockers or "r54_packet_export_candidate_body_full_ref_detected" in open_blockers
    current_refs = _r54_parent_current_refs(r6)
    r53_refs = _r54_parent_r53_refs(r6)
    material = {
        "schema_version": P7_R54_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_STEP,
        "scope": P7_R54_SCOPE,
        "policy_kind": P7_R54_POLICY_KIND,
        "policy_section": "R54-7_packet_completeness_export_denylist_scan",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_packet_completeness_export_denylist_scan", max_length=200),
        "review_session_id": _safe_review_session_id(r6.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r6_packet_generation_request_schema_version": P7_R54_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION,
        "r6_packet_generation_request_material_ref": clean_identifier(r6.get("material_id"), default="missing_r54_6_request", max_length=200),
        "r6_generation_request_status": clean_identifier(r6.get("generation_request_status"), default="MISSING_R54_6_REQUEST", max_length=140),
        "r6_ready_for_packet_scan": ready_request,
        "current_received_snapshot_refs": current_refs,
        "current_received_snapshot_ref_count": len(current_refs),
        "r53_source_snapshot_refs": r53_refs,
        "r53_source_snapshot_ref_count": len(r53_refs),
        "r53_refs_are_current_received_refs": False,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "packet_request_row_count": len(request_rows),
        "packet_completion_row_count": len(rows),
        "packet_completion_rows": rows,
        "packet_completion_blind_case_ids": completion_blind_ids,
        "packet_completion_packet_ref_ids": completion_packet_refs,
        "packet_completion_blind_case_ids_unique": _r54_unique_non_empty(completion_blind_ids) if rows else False,
        "packet_completion_packet_ref_ids_unique": _r54_unique_non_empty(completion_packet_refs) if rows else False,
        "packet_completion_row_count_matches_request": bool(len(rows) == len(request_rows) == P7_R51_REQUIRED_CASE_COUNT),
        "all_required_packet_fields_present": bool(rows and all(row.get("packet_present_local_only") is True and row.get("required_body_full_review_packet_fields_present") is True for row in rows)),
        "packet_completeness_scan_status": "R54_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_READY" if ready else ("BLOCKED_BY_PACKET_COMPLETENESS_OR_EXPORT_DENYLIST" if ready_request else "R54_PACKET_SCAN_BLOCKED"),
        "review_session_status": "R54_READY_FOR_ACTUAL_HUMAN_REVIEW" if ready else "R54_PACKET_SCAN_BLOCKED",
        "ready_for_actual_human_review": ready,
        "review_must_not_start_before_scan_ready": True,
        "violation_routes_to_purge_before_review": routes_to_purge,
        "export_candidate_count": candidate_count,
        "export_denied_candidate_count": denied_count,
        "export_denylist_violation_refs": denied_refs,
        "body_full_export_candidate_ref_count": body_full_candidate_count,
        "export_candidate_refs_body_free_only": body_full_candidate_count == 0 and denied_count == 0,
        "local_packet_exported": False,
        "body_full_packet_export_allowed": False,
        "body_full_packet_zip_included": False,
        "body_full_packet_generated_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "raw_input_included": False,
        "returned_surface_included": False,
        "history_body_included": False,
        "comment_text_included": False,
        "reviewer_free_text_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_absolute_path_included": False,
        "body_content_hash_included": False,
        "packet_content_hash_included": False,
        "execution_blocker_ids": open_blockers,
        "open_execution_blocker_ids": open_blockers,
        "scan_reason_refs": ["r54_7_packet_scan_ready_body_free_no_export_violation"] if ready else ["r54_7_packet_scan_blocked_fail_closed"],
        **_false_flags_except({"validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here"}),
        "r54_0_scope_current_received_snapshot_refrozen": r6.get("r54_0_scope_current_received_snapshot_refrozen") is True,
        "r54_1_r53_source_delta_current_snapshot_override_adopted": r6.get("r54_1_r53_source_delta_current_snapshot_override_adopted") is True,
        "r54_2_validation_evidence_intake_done": r6.get("r54_2_validation_evidence_intake_done") is True,
        "r54_3_local_only_actual_review_preflight_built": r6.get("r54_3_local_only_actual_review_preflight_built") is True,
        "r54_4_actual_review_session_envelope_built": r6.get("r54_4_actual_review_session_envelope_built") is True,
        "r54_5_24_case_manifest_freeze_built": r6.get("r54_5_24_case_manifest_freeze_built") is True,
        "r54_6_local_only_body_full_packet_generation_request_built": r6.get("r54_6_local_only_body_full_packet_generation_request_built") is True,
        "r54_7_packet_completeness_export_denylist_scan_built": ready,
        "implemented_steps": list(P7_R54_R7_IMPLEMENTED_STEPS) if ready else list(P7_R54_R6_IMPLEMENTED_STEPS if ready_request else P7_R54_R5_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_R7_NOT_YET_IMPLEMENTED_STEPS) if ready else list(P7_R54_R6_NOT_YET_IMPLEMENTED_STEPS if ready_request else P7_R54_R5_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R54_R7_NEXT_REQUIRED_STEP_REF if ready else (P7_R54_R7_PURGE_REQUIRED_NEXT_STEP_REF if routes_to_purge else P7_R54_R7_BLOCKED_NEXT_REQUIRED_STEP_REF),
        "next_required_step": P7_R54_R7_NEXT_REQUIRED_STEP_REF if ready else (P7_R54_R7_PURGE_REQUIRED_NEXT_STEP_REF if routes_to_purge else P7_R54_R7_BLOCKED_NEXT_REQUIRED_STEP_REF),
        "public_contract": public_contract_flags(),
        "r54_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "validation_evidence_intake_done_here": r6.get("validation_evidence_intake_done_here") is True,
        "local_root_preflight_passed_here": r6.get("local_root_preflight_passed_here") is True,
        "explicit_allow_present_here": r6.get("explicit_allow_present_here") is True,
        "purge_plan_verified_here": r6.get("purge_plan_verified_here") is True,
    }
    assert_p7_r54_packet_completeness_export_denylist_scan_bodyfree_contract(material)
    return material


def assert_p7_r54_packet_completeness_export_denylist_scan_bodyfree_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_REQUIRED_FIELD_REFS, source="p7_r54_packet_completeness_export_denylist_scan")
    _assert_body_free_common_with_false_keys(data, schema_version=P7_R54_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION, source="p7_r54_packet_completeness_export_denylist_scan", false_key_refs=P7_R54_R7_FALSE_KEY_REFS)
    _assert_current_refs(data, source="p7_r54_packet_completeness_export_denylist_scan")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=60, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 R7 open blockers must match execution blockers")
    if set(blockers) - set(P7_R54_R6_R7_ALLOWED_EXECUTION_BLOCKER_ID_REFS):
        raise ValueError("R54 R7 has non-canonical blocker ids")
    for key in ("local_packet_exported", "body_full_packet_export_allowed", "body_full_packet_zip_included", "body_full_packet_generated_here", "actual_body_full_packet_generated_here", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_rating_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_disposal_receipt_materialized_here", "raw_input_included", "returned_surface_included", "history_body_included", "comment_text_included", "reviewer_free_text_included", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included"):
        if data.get(key) is not False:
            raise ValueError(f"R54 R7 must keep {key}=False")
    rows = [safe_mapping(row) for row in (data.get("packet_completion_rows") or [])]
    for row in rows:
        assert_p7_r54_packet_completion_scan_row_bodyfree_contract(row)
    ready = data.get("packet_completeness_scan_status") == "R54_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_READY"
    if ready:
        if data.get("ready_for_actual_human_review") is not True or data.get("r54_7_packet_completeness_export_denylist_scan_built") is not True:
            raise ValueError("R54 R7 ready scan boundary failed")
        if len(rows) != P7_R51_REQUIRED_CASE_COUNT or data.get("packet_completion_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 R7 ready scan must contain exactly 24 rows")
        if data.get("packet_completion_row_count_matches_request") is not True or data.get("all_required_packet_fields_present") is not True:
            raise ValueError("R54 R7 completeness failed")
        if data.get("export_denied_candidate_count") != 0 or data.get("body_full_export_candidate_ref_count") != 0 or data.get("export_candidate_refs_body_free_only") is not True:
            raise ValueError("R54 R7 ready scan export boundary failed")
        if blockers:
            raise ValueError("R54 R7 ready scan must not carry blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_R7_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_R7_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 R7 step lists changed")
        if data.get("next_required_step") != P7_R54_R7_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R7 ready scan next step changed")
    else:
        if data.get("ready_for_actual_human_review") is not False or data.get("r54_7_packet_completeness_export_denylist_scan_built") is not False:
            raise ValueError("R54 R7 blocked scan must not allow review")
        expected_next = P7_R54_R7_PURGE_REQUIRED_NEXT_STEP_REF if data.get("violation_routes_to_purge_before_review") is True else P7_R54_R7_BLOCKED_NEXT_REQUIRED_STEP_REF
        if data.get("next_required_step") != expected_next:
            raise ValueError("R54 R7 blocked scan next step changed")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_packet_completeness_export_denylist_scan")
    return True


# Compatibility aliases matching the shorter R54-6/R54-7 design wording.
build_p7_r54_local_only_body_full_packet_generation_request = build_p7_r54_local_only_body_full_packet_generation_request_bodyfree
assert_p7_r54_local_only_body_full_packet_generation_request_contract = assert_p7_r54_local_only_body_full_packet_generation_request_bodyfree_contract
build_p7_r54_packet_completion_scan_row = build_p7_r54_packet_completion_scan_row_bodyfree
assert_p7_r54_packet_completion_scan_row_contract = assert_p7_r54_packet_completion_scan_row_bodyfree_contract
build_p7_r54_packet_completeness_export_denylist_scan = build_p7_r54_packet_completeness_export_denylist_scan_bodyfree
assert_p7_r54_packet_completeness_export_denylist_scan_contract = assert_p7_r54_packet_completeness_export_denylist_scan_bodyfree_contract



# ---------------------------------------------------------------------------
# R54-8 / R54-9 reviewer instruction form and operation state body-free contracts
# ---------------------------------------------------------------------------

P7_R54_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.reviewer_instruction_rating_form_freeze.bodyfree.v1"
)
P7_R54_REVIEWER_RATING_AXIS_INSTRUCTION_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.reviewer_rating_axis_instruction_row.bodyfree.v1"
)
P7_R54_ACTUAL_HUMAN_REVIEW_OPERATION_STATE_CAPTURE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_human_review_operation_state_capture.bodyfree.v1"
)

P7_R54_R8_STEP_REF: Final = "R54-8_reviewer_instruction_rating_form_freeze"
P7_R54_R9_STEP_REF: Final = "R54-9_actual_human_review_operation_state_capture"
P7_R54_R8_NEXT_REQUIRED_STEP_REF: Final = "R54-9_actual_human_review_operation_state_capture"
P7_R54_R8_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R54-8_reviewer_instruction_rating_form_after_R54-7_scan"
P7_R54_R9_NEXT_REQUIRED_STEP_REF: Final = "R54-10_sanitized_actual_review_result_capture"
P7_R54_R9_OPERATION_PENDING_NEXT_STEP_REF: Final = "continue_R54-9_actual_human_review_operation_until_capture_ready"
P7_R54_R9_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R54-9_actual_human_review_operation_state_after_R54-8_form"
P7_R54_R9_BLOCKED_NEXT_STEP_REF: Final = P7_R54_R9_BLOCKED_NEXT_REQUIRED_STEP_REF
P7_R54_R9_PURGE_REQUIRED_NEXT_STEP_REF: Final = "R54-16_purge_disposal_receipt_required_after_review_abort_or_expiration"

P7_R54_FUTURE_STEPS_AFTER_R9: Final[tuple[str, ...]] = tuple(
    step for step in P7_R54_R7_NOT_YET_IMPLEMENTED_STEPS if step not in {P7_R54_R8_STEP_REF, P7_R54_R9_STEP_REF}
)
P7_R54_R8_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_R7_IMPLEMENTED_STEPS, P7_R54_R8_STEP_REF)
P7_R54_R8_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_R9_STEP_REF, *P7_R54_FUTURE_STEPS_AFTER_R9)
P7_R54_R9_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_R8_IMPLEMENTED_STEPS, P7_R54_R9_STEP_REF)
P7_R54_R9_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_FUTURE_STEPS_AFTER_R9

P7_R54_REVIEW_VERDICT_REFS: Final[tuple[str, ...]] = ("PASS", "YELLOW", "REPAIR_REQUIRED", "RED")
P7_R54_RATING_SCORE_MIN: Final[float] = 0.0
P7_R54_RATING_SCORE_MAX: Final[float] = 1.0
P7_R54_REVIEWER_INSTRUCTION_REF: Final = "p7_r54_body_free_reviewer_instruction_rating_form_freeze"
P7_R54_REVIEWER_INSTRUCTION_VERSION: Final = "p7_r54_reviewer_instruction_rating_form_bodyfree.v1"
P7_R54_QUESTION_NEED_SELECTION_MODE_REF: Final = "enum_only_no_question_text"
P7_R54_REVIEWER_FREE_TEXT_POLICY_REF: Final = "free_text_disallowed_or_local_notes_only_purge_required"
P7_R54_RATING_SOURCE_POLICY_REF: Final = "reviewer_selection_only_no_machine_score"
P7_R54_NOT_REVIEWED_RATING_POLICY_REF: Final = "not_reviewed_must_not_create_rating_rows"
P7_R54_REVIEW_OPERATION_STATE_REFS: Final[tuple[str, ...]] = (
    "not_started",
    "in_progress",
    "review_completed_pending_sanitized_capture",
    "sanitized_capture_ready",
    "aborted_purge_required",
    "expired_purge_required",
)
P7_R54_R9_OPERATION_REVIEW_SESSION_STATUS_BY_STATE: Final[dict[str, str]] = {
    "not_started": "R54_READY_FOR_ACTUAL_HUMAN_REVIEW_NOT_STARTED",
    "in_progress": "R54_REVIEW_IN_PROGRESS_LOCAL_ONLY",
    "review_completed_pending_sanitized_capture": "R54_REVIEW_COMPLETED_PENDING_SANITIZED_CAPTURE",
    "sanitized_capture_ready": "R54_REVIEW_CAPTURE_READY_FOR_NORMALIZATION",
    "aborted_purge_required": "R54_ABORTED_PURGE_REQUIRED",
    "expired_purge_required": "R54_EXPIRED_PURGE_REQUIRED",
}
P7_R54_R9_CAPTURE_READY_STATE_REFS: Final[tuple[str, ...]] = (
    "review_completed_pending_sanitized_capture",
    "sanitized_capture_ready",
)
P7_R54_R9_PURGE_REQUIRED_STATE_REFS: Final[tuple[str, ...]] = (
    "aborted_purge_required",
    "expired_purge_required",
)

P7_R54_R8_R9_EXECUTION_BLOCKER_ID_REFS: Final[tuple[str, ...]] = (
    "r54_reviewer_instruction_packet_scan_not_ready",
    "r54_reviewer_instruction_rating_form_axis_contract_changed",
    "r54_reviewer_instruction_question_text_field_detected",
    "r54_reviewer_instruction_free_text_field_detected",
    "r54_actual_review_operation_form_not_ready",
    "r54_actual_review_operation_state_invalid",
    "r54_actual_review_operation_not_reviewed_has_selection_count",
    "r54_actual_review_operation_capture_ready_selection_count_missing",
    "r54_actual_review_operation_machine_score_attempted",
    "r54_actual_review_operation_rating_rows_created_without_review",
)
P7_R54_R8_R9_ALLOWED_EXECUTION_BLOCKER_ID_REFS: Final[frozenset[str]] = frozenset(
    (*P7_R54_R6_R7_ALLOWED_EXECUTION_BLOCKER_ID_REFS, *P7_R54_R8_R9_EXECUTION_BLOCKER_ID_REFS)
)
P7_R54_R8_FALSE_KEY_REFS: Final[tuple[str, ...]] = P7_R54_R7_FALSE_KEY_REFS
P7_R54_R9_FALSE_KEY_REFS: Final[tuple[str, ...]] = P7_R54_R7_FALSE_KEY_REFS

P7_R54_REVIEWER_RATING_AXIS_INSTRUCTION_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "axis_ref",
    "score_min",
    "score_max",
    "score_range_ref",
    "score_value_source_ref",
    "machine_auto_score_allowed",
    "machine_metrics_used_for_readfeel",
    "reviewer_selection_required",
    "body_free",
)

P7_R54_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "r7_packet_scan_schema_version", "r7_packet_scan_material_ref", "r7_packet_scan_status", "r7_ready_for_actual_human_review",
    "current_received_snapshot_refs", "current_received_snapshot_ref_count", "r53_source_snapshot_refs", "r53_source_snapshot_ref_count", "r53_refs_are_current_received_refs",
    "required_case_count", "packet_completion_row_count", "review_session_status", "instruction_form_status", "instruction_form_reason_refs",
    "reviewer_instruction_ref", "reviewer_instruction_version", "review_prompt_version", "rating_form_version",
    "rating_axis_refs", "rating_axis_count", "rating_axis_instruction_rows", "axis_score_min", "axis_score_max", "axis_score_range_ref", "axis_score_bounds_enforced",
    "verdict_enum_refs", "question_need_observation_stage_ref", "question_need_primary_class_refs", "ambiguity_kind_refs", "one_question_fit_refs", "repair_required_ref_refs",
    "question_need_observation_selection_mode", "question_need_observation_enum_only", "question_text_field_present", "draft_question_text_field_present", "question_text_entry_allowed", "draft_question_text_entry_allowed",
    "reviewer_free_text_policy_ref", "reviewer_free_text_allowed", "reviewer_notes_local_only_if_any", "reviewer_notes_purge_required", "reviewer_notes_body_stored_here", "reviewer_free_text_body_stored_here",
    "reviewer_visible_field_refs", "reviewer_hidden_field_refs", "reviewer_hidden_metadata_exposed", "reviewer_receives_blind_case_id_only",
    "rating_source_policy_ref", "machine_auto_score_used", "machine_metrics_used_for_readfeel", "reviewer_selections_required_for_rating", "not_reviewed_rating_rows_allowed",
    "reviewer_instruction_body_materialized_here", "reviewer_instruction_body_stored_here", "rating_form_freeze_body_free", "rating_rows_materialized_here", "question_need_observation_rows_materialized_here",
    "body_full_packet_generated_here", "actual_body_full_packet_generated_here", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_rating_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_disposal_receipt_materialized_here",
    "raw_input_included", "returned_surface_included", "history_body_included", "comment_text_included", "reviewer_free_text_included", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included",
    "execution_blocker_ids", "open_execution_blocker_ids",
    "r54_0_scope_current_received_snapshot_refrozen", "r54_1_r53_source_delta_current_snapshot_override_adopted", "r54_2_validation_evidence_intake_done", "r54_3_local_only_actual_review_preflight_built", "r54_4_actual_review_session_envelope_built", "r54_5_24_case_manifest_freeze_built", "r54_6_local_only_body_full_packet_generation_request_built", "r54_7_packet_completeness_export_denylist_scan_built", "r54_8_reviewer_instruction_rating_form_freeze_built",
    "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract", "r54_public_no_touch_contract", "body_free_markers", "body_free",
    *P7_R54_R8_FALSE_KEY_REFS,
    "validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here",
)

P7_R54_ACTUAL_HUMAN_REVIEW_OPERATION_STATE_CAPTURE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "r8_reviewer_instruction_schema_version", "r8_reviewer_instruction_material_ref", "r8_instruction_form_status", "r8_instruction_form_ready_for_operation_state_capture",
    "current_received_snapshot_refs", "current_received_snapshot_ref_count", "r53_source_snapshot_refs", "r53_source_snapshot_ref_count", "r53_refs_are_current_received_refs",
    "required_case_count", "review_operation_state_ref", "review_session_status", "operation_state_capture_status", "operation_state_reason_refs",
    "reviewer_selection_count", "reviewer_selection_required_count", "reviewer_selection_count_matches_required_case_count", "reviewer_selection_source_ref", "reviewer_selection_rows_materialized_here",
    "reviewer_selection_body_stored_here", "reviewer_free_text_body_stored_here", "reviewer_notes_body_stored_here", "reviewer_notes_local_only_if_any", "reviewer_notes_purge_required",
    "machine_auto_score_used", "machine_metrics_used_for_readfeel", "machine_generated_rating_rows_allowed", "reviewer_selections_only_rating_source", "rating_source_policy_ref", "not_reviewed_rating_policy_ref", "not_reviewed_rating_rows_allowed", "rating_rows_created_for_not_reviewed",
    "ready_for_sanitized_actual_review_result_capture", "capture_ready_requires_reviewer_selections", "operation_pending_without_rating_rows", "purge_required_before_handoff", "handoff_to_r54_10_allowed",
    "actual_review_operation_state_captured_here", "actual_review_completed_claimed_here", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_rating_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_disposal_receipt_materialized_here", "p5_actual_review_still_not_run_by_helper",
    "body_full_packet_generated_here", "actual_body_full_packet_generated_here", "raw_input_included", "returned_surface_included", "history_body_included", "comment_text_included", "reviewer_free_text_included", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included",
    "execution_blocker_ids", "open_execution_blocker_ids",
    "r54_0_scope_current_received_snapshot_refrozen", "r54_1_r53_source_delta_current_snapshot_override_adopted", "r54_2_validation_evidence_intake_done", "r54_3_local_only_actual_review_preflight_built", "r54_4_actual_review_session_envelope_built", "r54_5_24_case_manifest_freeze_built", "r54_6_local_only_body_full_packet_generation_request_built", "r54_7_packet_completeness_export_denylist_scan_built", "r54_8_reviewer_instruction_rating_form_freeze_built", "r54_9_actual_human_review_operation_state_capture_built",
    "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract", "r54_public_no_touch_contract", "body_free_markers", "body_free",
    *P7_R54_R9_FALSE_KEY_REFS,
    "validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here",
)


def build_p7_r54_reviewer_rating_axis_instruction_row_bodyfree(*, axis_ref: Any) -> dict[str, Any]:
    axis = clean_identifier(axis_ref, default="unknown_axis", max_length=120)
    row = {
        "schema_version": P7_R54_REVIEWER_RATING_AXIS_INSTRUCTION_ROW_SCHEMA_VERSION,
        "axis_ref": axis,
        "score_min": P7_R54_RATING_SCORE_MIN,
        "score_max": P7_R54_RATING_SCORE_MAX,
        "score_range_ref": "0.00_to_1.00_inclusive",
        "score_value_source_ref": "reviewer_selection_only",
        "machine_auto_score_allowed": False,
        "machine_metrics_used_for_readfeel": False,
        "reviewer_selection_required": True,
        "body_free": True,
    }
    assert_p7_r54_reviewer_rating_axis_instruction_row_bodyfree_contract(row)
    return row


def assert_p7_r54_reviewer_rating_axis_instruction_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R54_REVIEWER_RATING_AXIS_INSTRUCTION_ROW_REQUIRED_FIELD_REFS, source="p7_r54_reviewer_rating_axis_instruction_row")
    if data.get("schema_version") != P7_R54_REVIEWER_RATING_AXIS_INSTRUCTION_ROW_SCHEMA_VERSION:
        raise ValueError("R54 R8 axis row schema changed")
    if data.get("axis_ref") not in P5_HUMAN_BLIND_QA_RATING_AXES:
        raise ValueError("R54 R8 axis row has non-canonical axis")
    if data.get("score_min") != P7_R54_RATING_SCORE_MIN or data.get("score_max") != P7_R54_RATING_SCORE_MAX:
        raise ValueError("R54 R8 axis score bounds changed")
    if data.get("score_range_ref") != "0.00_to_1.00_inclusive":
        raise ValueError("R54 R8 axis score range ref changed")
    for false_key in ("machine_auto_score_allowed", "machine_metrics_used_for_readfeel"):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 R8 axis row must keep {false_key}=False")
    if data.get("score_value_source_ref") != "reviewer_selection_only" or data.get("reviewer_selection_required") is not True or data.get("body_free") is not True:
        raise ValueError("R54 R8 axis row must be reviewer-selection body-free")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_reviewer_rating_axis_instruction_row")
    return True


def build_p7_r54_reviewer_instruction_rating_form_freeze_bodyfree(
    *,
    packet_completeness_export_denylist_scan: Mapping[str, Any] | None = None,
    r7_packet_completeness_export_denylist_scan: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_reviewer_instruction_rating_form_freeze",
) -> dict[str, Any]:
    """Build R54-8 body-free reviewer instruction/rating form freeze."""

    if packet_completeness_export_denylist_scan is not None and r7_packet_completeness_export_denylist_scan is not None:
        raise ValueError("provide only one R54-7 packet scan value")
    r7 = safe_mapping(
        packet_completeness_export_denylist_scan
        if packet_completeness_export_denylist_scan is not None
        else r7_packet_completeness_export_denylist_scan
    )
    if not r7:
        r7 = build_p7_r54_packet_completeness_export_denylist_scan_bodyfree()
    assert_p7_r54_packet_completeness_export_denylist_scan_bodyfree_contract(r7)
    ready = r7.get("packet_completeness_scan_status") == "R54_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_READY" and r7.get("ready_for_actual_human_review") is True
    blockers = dedupe_identifiers(r7.get("execution_blocker_ids") or [], limit=60, max_length=140)
    reason_refs = ["r54_8_reviewer_instruction_rating_form_frozen_body_free"] if ready else ["r54_7_packet_scan_not_ready_for_review_form"]
    if not ready:
        blockers = dedupe_identifiers((*blockers, "r54_reviewer_instruction_packet_scan_not_ready"), limit=60, max_length=140)
    axis_rows = [build_p7_r54_reviewer_rating_axis_instruction_row_bodyfree(axis_ref=axis) for axis in P5_HUMAN_BLIND_QA_RATING_AXES] if ready else []
    material = {
        "schema_version": P7_R54_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_STEP,
        "scope": P7_R54_SCOPE,
        "policy_kind": P7_R54_POLICY_KIND,
        "policy_section": "R54-8_reviewer_instruction_rating_form_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_reviewer_instruction_rating_form_freeze", max_length=200),
        "review_session_id": _safe_review_session_id(r7.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r7_packet_scan_schema_version": P7_R54_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION,
        "r7_packet_scan_material_ref": clean_identifier(r7.get("material_id"), default="p7_r54_packet_completeness_export_denylist_scan", max_length=200),
        "r7_packet_scan_status": clean_identifier(r7.get("packet_completeness_scan_status"), default="R54_PACKET_SCAN_BLOCKED", max_length=120),
        "r7_ready_for_actual_human_review": ready,
        "current_received_snapshot_refs": safe_mapping(r7.get("current_received_snapshot_refs")),
        "current_received_snapshot_ref_count": len(safe_mapping(r7.get("current_received_snapshot_refs"))),
        "r53_source_snapshot_refs": safe_mapping(r7.get("r53_source_snapshot_refs")),
        "r53_source_snapshot_ref_count": len(safe_mapping(r7.get("r53_source_snapshot_refs"))),
        "r53_refs_are_current_received_refs": False,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "packet_completion_row_count": _safe_non_negative_int_r54(r7.get("packet_completion_row_count")),
        "review_session_status": "R54_REVIEWER_INSTRUCTION_RATING_FORM_READY" if ready else "R54_PRECHECK_BLOCKED",
        "instruction_form_status": "READY_FOR_ACTUAL_HUMAN_REVIEW_OPERATION_STATE_CAPTURE" if ready else "BLOCKED_BY_R54_7_PACKET_SCAN",
        "instruction_form_reason_refs": reason_refs,
        "reviewer_instruction_ref": P7_R54_REVIEWER_INSTRUCTION_REF if ready else "not_frozen",
        "reviewer_instruction_version": P7_R54_REVIEWER_INSTRUCTION_VERSION if ready else "not_frozen",
        "review_prompt_version": P7_R54_REVIEW_PROMPT_VERSION if ready else "not_frozen",
        "rating_form_version": P7_R50_RATING_FORM_VERSION,
        "rating_axis_refs": list(P5_HUMAN_BLIND_QA_RATING_AXES) if ready else [],
        "rating_axis_count": len(P5_HUMAN_BLIND_QA_RATING_AXES) if ready else 0,
        "rating_axis_instruction_rows": axis_rows,
        "axis_score_min": P7_R54_RATING_SCORE_MIN,
        "axis_score_max": P7_R54_RATING_SCORE_MAX,
        "axis_score_range_ref": "0.00_to_1.00_inclusive",
        "axis_score_bounds_enforced": ready,
        "verdict_enum_refs": list(P7_R54_REVIEW_VERDICT_REFS),
        "question_need_observation_stage_ref": P7_R50_QUESTION_NEED_OBSERVATION_STAGE_REF,
        "question_need_primary_class_refs": list(P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS),
        "ambiguity_kind_refs": list(P7_R49_AMBIGUITY_KIND_REFS),
        "one_question_fit_refs": list(P7_R49_ONE_QUESTION_FIT_REFS),
        "repair_required_ref_refs": list(P7_R49_REPAIR_REQUIRED_REF_REFS),
        "question_need_observation_selection_mode": P7_R54_QUESTION_NEED_SELECTION_MODE_REF,
        "question_need_observation_enum_only": True,
        "question_text_field_present": False,
        "draft_question_text_field_present": False,
        "question_text_entry_allowed": False,
        "draft_question_text_entry_allowed": False,
        "reviewer_free_text_policy_ref": P7_R54_REVIEWER_FREE_TEXT_POLICY_REF,
        "reviewer_free_text_allowed": False,
        "reviewer_notes_local_only_if_any": True,
        "reviewer_notes_purge_required": True,
        "reviewer_notes_body_stored_here": False,
        "reviewer_free_text_body_stored_here": False,
        "reviewer_visible_field_refs": list(P7_R50_REVIEWER_VISIBLE_FIELD_REFS),
        "reviewer_hidden_field_refs": list(P7_R50_REVIEWER_HIDDEN_FIELD_REFS),
        "reviewer_hidden_metadata_exposed": False,
        "reviewer_receives_blind_case_id_only": ready,
        "rating_source_policy_ref": P7_R54_RATING_SOURCE_POLICY_REF,
        "machine_auto_score_used": False,
        "machine_metrics_used_for_readfeel": False,
        "reviewer_selections_required_for_rating": True,
        "not_reviewed_rating_rows_allowed": False,
        "reviewer_instruction_body_materialized_here": False,
        "reviewer_instruction_body_stored_here": False,
        "rating_form_freeze_body_free": True,
        "rating_rows_materialized_here": False,
        "question_need_observation_rows_materialized_here": False,
        "body_full_packet_generated_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "raw_input_included": False,
        "returned_surface_included": False,
        "history_body_included": False,
        "comment_text_included": False,
        "reviewer_free_text_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_absolute_path_included": False,
        "body_content_hash_included": False,
        "packet_content_hash_included": False,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        **_false_flags_except({"validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here"}),
        "r54_0_scope_current_received_snapshot_refrozen": r7.get("r54_0_scope_current_received_snapshot_refrozen") is True,
        "r54_1_r53_source_delta_current_snapshot_override_adopted": r7.get("r54_1_r53_source_delta_current_snapshot_override_adopted") is True,
        "r54_2_validation_evidence_intake_done": r7.get("r54_2_validation_evidence_intake_done") is True,
        "r54_3_local_only_actual_review_preflight_built": r7.get("r54_3_local_only_actual_review_preflight_built") is True,
        "r54_4_actual_review_session_envelope_built": r7.get("r54_4_actual_review_session_envelope_built") is True,
        "r54_5_24_case_manifest_freeze_built": r7.get("r54_5_24_case_manifest_freeze_built") is True,
        "r54_6_local_only_body_full_packet_generation_request_built": r7.get("r54_6_local_only_body_full_packet_generation_request_built") is True,
        "r54_7_packet_completeness_export_denylist_scan_built": r7.get("r54_7_packet_completeness_export_denylist_scan_built") is True,
        "r54_8_reviewer_instruction_rating_form_freeze_built": ready,
        "implemented_steps": list(P7_R54_R8_IMPLEMENTED_STEPS) if ready else list(P7_R54_R7_IMPLEMENTED_STEPS if r7.get("r54_7_packet_completeness_export_denylist_scan_built") is True else P7_R54_R6_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_R8_NOT_YET_IMPLEMENTED_STEPS) if ready else list(P7_R54_R7_NOT_YET_IMPLEMENTED_STEPS if r7.get("r54_7_packet_completeness_export_denylist_scan_built") is True else P7_R54_R6_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R54_R8_NEXT_REQUIRED_STEP_REF if ready else P7_R54_R8_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "next_required_step": P7_R54_R8_NEXT_REQUIRED_STEP_REF if ready else P7_R54_R8_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "validation_evidence_intake_done_here": r7.get("validation_evidence_intake_done_here") is True,
        "local_root_preflight_passed_here": r7.get("local_root_preflight_passed_here") is True,
        "explicit_allow_present_here": r7.get("explicit_allow_present_here") is True,
        "purge_plan_verified_here": r7.get("purge_plan_verified_here") is True,
    }
    assert_p7_r54_reviewer_instruction_rating_form_freeze_bodyfree_contract(material)
    return material


def assert_p7_r54_reviewer_instruction_rating_form_freeze_bodyfree_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_REQUIRED_FIELD_REFS, source="p7_r54_reviewer_instruction_rating_form_freeze")
    _assert_body_free_common_with_false_keys(data, schema_version=P7_R54_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION, source="p7_r54_reviewer_instruction_rating_form_freeze", false_key_refs=P7_R54_R8_FALSE_KEY_REFS)
    _assert_current_refs(data, source="p7_r54_reviewer_instruction_rating_form_freeze")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=80, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 R8 open blockers must match execution blockers")
    if set(blockers) - set(P7_R54_R8_R9_ALLOWED_EXECUTION_BLOCKER_ID_REFS):
        raise ValueError("R54 R8 has non-canonical blocker ids")
    for false_key in (
        "question_text_field_present", "draft_question_text_field_present", "question_text_entry_allowed", "draft_question_text_entry_allowed",
        "reviewer_free_text_allowed", "reviewer_notes_body_stored_here", "reviewer_free_text_body_stored_here", "reviewer_hidden_metadata_exposed",
        "machine_auto_score_used", "machine_metrics_used_for_readfeel", "not_reviewed_rating_rows_allowed", "reviewer_instruction_body_materialized_here", "reviewer_instruction_body_stored_here", "rating_rows_materialized_here", "question_need_observation_rows_materialized_here",
        "body_full_packet_generated_here", "actual_body_full_packet_generated_here", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_rating_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_disposal_receipt_materialized_here",
        "raw_input_included", "returned_surface_included", "history_body_included", "comment_text_included", "reviewer_free_text_included", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 R8 must keep {false_key}=False")
    if data.get("rating_form_version") != P7_R50_RATING_FORM_VERSION:
        raise ValueError("R54 R8 rating form version changed")
    if tuple(data.get("verdict_enum_refs") or ()) != P7_R54_REVIEW_VERDICT_REFS:
        raise ValueError("R54 R8 verdict enum changed")
    if data.get("axis_score_min") != P7_R54_RATING_SCORE_MIN or data.get("axis_score_max") != P7_R54_RATING_SCORE_MAX or data.get("axis_score_range_ref") != "0.00_to_1.00_inclusive":
        raise ValueError("R54 R8 axis score range changed")
    if data.get("question_need_observation_stage_ref") != P7_R50_QUESTION_NEED_OBSERVATION_STAGE_REF:
        raise ValueError("R54 R8 question observation stage changed")
    if tuple(data.get("question_need_primary_class_refs") or ()) != P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS:
        raise ValueError("R54 R8 primary class refs changed")
    if tuple(data.get("ambiguity_kind_refs") or ()) != P7_R49_AMBIGUITY_KIND_REFS:
        raise ValueError("R54 R8 ambiguity refs changed")
    if tuple(data.get("one_question_fit_refs") or ()) != P7_R49_ONE_QUESTION_FIT_REFS:
        raise ValueError("R54 R8 one-question fit refs changed")
    if tuple(data.get("repair_required_ref_refs") or ()) != P7_R49_REPAIR_REQUIRED_REF_REFS:
        raise ValueError("R54 R8 repair refs changed")
    if data.get("question_need_observation_selection_mode") != P7_R54_QUESTION_NEED_SELECTION_MODE_REF or data.get("question_need_observation_enum_only") is not True:
        raise ValueError("R54 R8 question observation must remain enum-only")
    if tuple(data.get("reviewer_visible_field_refs") or ()) != P7_R50_REVIEWER_VISIBLE_FIELD_REFS:
        raise ValueError("R54 R8 reviewer visible refs changed")
    if tuple(data.get("reviewer_hidden_field_refs") or ()) != P7_R50_REVIEWER_HIDDEN_FIELD_REFS:
        raise ValueError("R54 R8 reviewer hidden refs changed")
    if data.get("rating_source_policy_ref") != P7_R54_RATING_SOURCE_POLICY_REF or data.get("reviewer_selections_required_for_rating") is not True:
        raise ValueError("R54 R8 rating source policy changed")
    ready = data.get("instruction_form_status") == "READY_FOR_ACTUAL_HUMAN_REVIEW_OPERATION_STATE_CAPTURE"
    rows = [safe_mapping(row) for row in (data.get("rating_axis_instruction_rows") or [])]
    for row in rows:
        assert_p7_r54_reviewer_rating_axis_instruction_row_bodyfree_contract(row)
    if ready:
        if data.get("r7_ready_for_actual_human_review") is not True or data.get("r54_8_reviewer_instruction_rating_form_freeze_built") is not True:
            raise ValueError("R54 R8 ready requires R54-7 ready scan")
        if tuple(data.get("rating_axis_refs") or ()) != P5_HUMAN_BLIND_QA_RATING_AXES or data.get("rating_axis_count") != len(P5_HUMAN_BLIND_QA_RATING_AXES):
            raise ValueError("R54 R8 rating axes changed")
        if len(rows) != len(P5_HUMAN_BLIND_QA_RATING_AXES):
            raise ValueError("R54 R8 must freeze one axis row per P5 axis")
        if data.get("axis_score_bounds_enforced") is not True or data.get("reviewer_receives_blind_case_id_only") is not True or data.get("rating_form_freeze_body_free") is not True:
            raise ValueError("R54 R8 ready form boundary failed")
        if blockers:
            raise ValueError("R54 R8 ready form must not carry blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_R8_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_R8_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 R8 step lists changed")
        if data.get("next_required_step") != P7_R54_R8_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R8 ready form next step changed")
    else:
        if data.get("r54_8_reviewer_instruction_rating_form_freeze_built") is not False:
            raise ValueError("R54 R8 blocked form must not claim built")
        if rows or data.get("rating_axis_count") != 0 or data.get("rating_axis_refs"):
            raise ValueError("R54 R8 blocked form must not freeze rating axis rows")
        if not blockers or data.get("next_required_step") != P7_R54_R8_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R8 blocked form next step changed")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_reviewer_instruction_rating_form_freeze")
    return True


def _safe_r54_review_operation_state_ref(value: Any) -> str:
    state = clean_identifier(value, default="not_started", max_length=80)
    return state if state in P7_R54_REVIEW_OPERATION_STATE_REFS else "invalid"


def build_p7_r54_actual_human_review_operation_state_capture_bodyfree(
    *,
    reviewer_instruction_rating_form_freeze: Mapping[str, Any] | None = None,
    r8_reviewer_instruction_rating_form_freeze: Mapping[str, Any] | None = None,
    review_operation_state_ref: Any = "not_started",
    reviewer_selection_count: Any = 0,
    reviewer_selection_source_ref: Any = "none",
    material_id: Any = "p7_r54_actual_human_review_operation_state_capture",
) -> dict[str, Any]:
    """Build R54-9 body-free actual human review operation state capture."""

    if reviewer_instruction_rating_form_freeze is not None and r8_reviewer_instruction_rating_form_freeze is not None:
        raise ValueError("provide only one R54-8 form value")
    r8 = safe_mapping(
        reviewer_instruction_rating_form_freeze
        if reviewer_instruction_rating_form_freeze is not None
        else r8_reviewer_instruction_rating_form_freeze
    )
    if not r8:
        r8 = build_p7_r54_reviewer_instruction_rating_form_freeze_bodyfree()
    assert_p7_r54_reviewer_instruction_rating_form_freeze_bodyfree_contract(r8)
    form_ready = r8.get("instruction_form_status") == "READY_FOR_ACTUAL_HUMAN_REVIEW_OPERATION_STATE_CAPTURE"
    state = _safe_r54_review_operation_state_ref(review_operation_state_ref)
    selection_count = _safe_non_negative_int_r54(reviewer_selection_count)
    capture_ready_state = state in P7_R54_R9_CAPTURE_READY_STATE_REFS
    purge_required_state = state in P7_R54_R9_PURGE_REQUIRED_STATE_REFS
    pending_state = state in {"not_started", "in_progress"}
    valid_state = state in P7_R54_REVIEW_OPERATION_STATE_REFS
    selection_count_ok_for_state = (selection_count == P7_R51_REQUIRED_CASE_COUNT) if capture_ready_state else (selection_count == 0 if pending_state else True)
    ready_for_capture = form_ready and capture_ready_state and selection_count == P7_R51_REQUIRED_CASE_COUNT
    blockers = dedupe_identifiers(r8.get("execution_blocker_ids") or [], limit=80, max_length=140)
    reason_refs: list[str] = []
    if not form_ready:
        reason_refs.append("r54_8_instruction_form_not_ready")
        blockers.append("r54_actual_review_operation_form_not_ready")
    if not valid_state:
        reason_refs.append("r54_review_operation_state_invalid")
        blockers.append("r54_actual_review_operation_state_invalid")
    if form_ready and pending_state and selection_count != 0:
        reason_refs.append("r54_not_reviewed_or_in_progress_must_not_have_selection_count")
        blockers.append("r54_actual_review_operation_not_reviewed_has_selection_count")
    if form_ready and capture_ready_state and selection_count != P7_R51_REQUIRED_CASE_COUNT:
        reason_refs.append("r54_capture_ready_state_requires_24_reviewer_selections")
        blockers.append("r54_actual_review_operation_capture_ready_selection_count_missing")
    if form_ready and valid_state and not reason_refs:
        if ready_for_capture:
            reason_refs.append("r54_review_operation_capture_ready_body_free_count_only")
        elif purge_required_state:
            reason_refs.append("r54_review_operation_abort_or_expired_purge_required")
        else:
            reason_refs.append("r54_review_operation_state_captured_pending_no_rating_rows")
    blockers = dedupe_identifiers(blockers, limit=80, max_length=140)
    if not form_ready:
        status = "BLOCKED_BY_R54_8_FORM"
        review_session_status = "R54_PRECHECK_BLOCKED"
        next_step = P7_R54_R9_BLOCKED_NEXT_STEP_REF
        implemented_steps = list(P7_R54_R8_IMPLEMENTED_STEPS if r8.get("r54_8_reviewer_instruction_rating_form_freeze_built") is True else P7_R54_R7_IMPLEMENTED_STEPS)
        not_yet_steps = list(P7_R54_R8_NOT_YET_IMPLEMENTED_STEPS if r8.get("r54_8_reviewer_instruction_rating_form_freeze_built") is True else P7_R54_R7_NOT_YET_IMPLEMENTED_STEPS)
        r9_built = False
    elif purge_required_state:
        status = "PURGE_REQUIRED_BEFORE_HANDOFF"
        review_session_status = P7_R54_R9_OPERATION_REVIEW_SESSION_STATUS_BY_STATE.get(state, "R54_PRECHECK_BLOCKED")
        next_step = P7_R54_R9_PURGE_REQUIRED_NEXT_STEP_REF
        implemented_steps = list(P7_R54_R9_IMPLEMENTED_STEPS)
        not_yet_steps = list(P7_R54_R9_NOT_YET_IMPLEMENTED_STEPS)
        r9_built = True
    elif ready_for_capture:
        status = "READY_FOR_SANITIZED_ACTUAL_REVIEW_RESULT_CAPTURE"
        review_session_status = P7_R54_R9_OPERATION_REVIEW_SESSION_STATUS_BY_STATE[state]
        next_step = P7_R54_R9_NEXT_REQUIRED_STEP_REF
        implemented_steps = list(P7_R54_R9_IMPLEMENTED_STEPS)
        not_yet_steps = list(P7_R54_R9_NOT_YET_IMPLEMENTED_STEPS)
        r9_built = True
    else:
        status = "R54_REVIEW_OPERATION_STATE_CAPTURED_PENDING"
        review_session_status = P7_R54_R9_OPERATION_REVIEW_SESSION_STATUS_BY_STATE.get(state, "R54_PRECHECK_BLOCKED")
        next_step = P7_R54_R9_OPERATION_PENDING_NEXT_STEP_REF if valid_state and not blockers else P7_R54_R9_BLOCKED_NEXT_STEP_REF
        implemented_steps = list(P7_R54_R9_IMPLEMENTED_STEPS) if valid_state and not blockers else list(P7_R54_R8_IMPLEMENTED_STEPS)
        not_yet_steps = list(P7_R54_R9_NOT_YET_IMPLEMENTED_STEPS) if valid_state and not blockers else list(P7_R54_R8_NOT_YET_IMPLEMENTED_STEPS)
        r9_built = bool(valid_state and not blockers)
    material = {
        "schema_version": P7_R54_ACTUAL_HUMAN_REVIEW_OPERATION_STATE_CAPTURE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_STEP,
        "scope": P7_R54_SCOPE,
        "policy_kind": P7_R54_POLICY_KIND,
        "policy_section": "R54-9_actual_human_review_operation_state_capture",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_actual_human_review_operation_state_capture", max_length=200),
        "review_session_id": _safe_review_session_id(r8.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r8_reviewer_instruction_schema_version": P7_R54_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION,
        "r8_reviewer_instruction_material_ref": clean_identifier(r8.get("material_id"), default="p7_r54_reviewer_instruction_rating_form_freeze", max_length=200),
        "r8_instruction_form_status": clean_identifier(r8.get("instruction_form_status"), default="BLOCKED_BY_R54_7_PACKET_SCAN", max_length=120),
        "r8_instruction_form_ready_for_operation_state_capture": form_ready,
        "current_received_snapshot_refs": safe_mapping(r8.get("current_received_snapshot_refs")),
        "current_received_snapshot_ref_count": len(safe_mapping(r8.get("current_received_snapshot_refs"))),
        "r53_source_snapshot_refs": safe_mapping(r8.get("r53_source_snapshot_refs")),
        "r53_source_snapshot_ref_count": len(safe_mapping(r8.get("r53_source_snapshot_refs"))),
        "r53_refs_are_current_received_refs": False,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "review_operation_state_ref": state,
        "review_session_status": review_session_status,
        "operation_state_capture_status": status,
        "operation_state_reason_refs": dedupe_identifiers(reason_refs, limit=20, max_length=140),
        "reviewer_selection_count": selection_count,
        "reviewer_selection_required_count": P7_R51_REQUIRED_CASE_COUNT,
        "reviewer_selection_count_matches_required_case_count": selection_count == P7_R51_REQUIRED_CASE_COUNT,
        "reviewer_selection_source_ref": clean_identifier(reviewer_selection_source_ref, default="none", max_length=160),
        "reviewer_selection_rows_materialized_here": False,
        "reviewer_selection_body_stored_here": False,
        "reviewer_free_text_body_stored_here": False,
        "reviewer_notes_body_stored_here": False,
        "reviewer_notes_local_only_if_any": True,
        "reviewer_notes_purge_required": True,
        "machine_auto_score_used": False,
        "machine_metrics_used_for_readfeel": False,
        "machine_generated_rating_rows_allowed": False,
        "reviewer_selections_only_rating_source": True,
        "rating_source_policy_ref": P7_R54_RATING_SOURCE_POLICY_REF,
        "not_reviewed_rating_policy_ref": P7_R54_NOT_REVIEWED_RATING_POLICY_REF,
        "not_reviewed_rating_rows_allowed": False,
        "rating_rows_created_for_not_reviewed": False,
        "ready_for_sanitized_actual_review_result_capture": ready_for_capture,
        "capture_ready_requires_reviewer_selections": True,
        "operation_pending_without_rating_rows": bool(form_ready and pending_state and not blockers),
        "purge_required_before_handoff": bool(form_ready and purge_required_state),
        "handoff_to_r54_10_allowed": ready_for_capture,
        "actual_review_operation_state_captured_here": r9_built,
        "actual_review_completed_claimed_here": False,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "p5_actual_review_still_not_run_by_helper": True,
        "body_full_packet_generated_here": False,
        "actual_body_full_packet_generated_here": False,
        "raw_input_included": False,
        "returned_surface_included": False,
        "history_body_included": False,
        "comment_text_included": False,
        "reviewer_free_text_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_absolute_path_included": False,
        "body_content_hash_included": False,
        "packet_content_hash_included": False,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        **_false_flags_except({"validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here"}),
        "r54_0_scope_current_received_snapshot_refrozen": r8.get("r54_0_scope_current_received_snapshot_refrozen") is True,
        "r54_1_r53_source_delta_current_snapshot_override_adopted": r8.get("r54_1_r53_source_delta_current_snapshot_override_adopted") is True,
        "r54_2_validation_evidence_intake_done": r8.get("r54_2_validation_evidence_intake_done") is True,
        "r54_3_local_only_actual_review_preflight_built": r8.get("r54_3_local_only_actual_review_preflight_built") is True,
        "r54_4_actual_review_session_envelope_built": r8.get("r54_4_actual_review_session_envelope_built") is True,
        "r54_5_24_case_manifest_freeze_built": r8.get("r54_5_24_case_manifest_freeze_built") is True,
        "r54_6_local_only_body_full_packet_generation_request_built": r8.get("r54_6_local_only_body_full_packet_generation_request_built") is True,
        "r54_7_packet_completeness_export_denylist_scan_built": r8.get("r54_7_packet_completeness_export_denylist_scan_built") is True,
        "r54_8_reviewer_instruction_rating_form_freeze_built": r8.get("r54_8_reviewer_instruction_rating_form_freeze_built") is True,
        "r54_9_actual_human_review_operation_state_capture_built": r9_built,
        "implemented_steps": implemented_steps,
        "not_yet_implemented_steps": not_yet_steps,
        "first_next_work_ref": next_step,
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "r54_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "validation_evidence_intake_done_here": r8.get("validation_evidence_intake_done_here") is True,
        "local_root_preflight_passed_here": r8.get("local_root_preflight_passed_here") is True,
        "explicit_allow_present_here": r8.get("explicit_allow_present_here") is True,
        "purge_plan_verified_here": r8.get("purge_plan_verified_here") is True,
    }
    assert_p7_r54_actual_human_review_operation_state_capture_bodyfree_contract(material)
    return material


def assert_p7_r54_actual_human_review_operation_state_capture_bodyfree_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_ACTUAL_HUMAN_REVIEW_OPERATION_STATE_CAPTURE_REQUIRED_FIELD_REFS, source="p7_r54_actual_human_review_operation_state_capture")
    _assert_body_free_common_with_false_keys(data, schema_version=P7_R54_ACTUAL_HUMAN_REVIEW_OPERATION_STATE_CAPTURE_SCHEMA_VERSION, source="p7_r54_actual_human_review_operation_state_capture", false_key_refs=P7_R54_R9_FALSE_KEY_REFS)
    _assert_current_refs(data, source="p7_r54_actual_human_review_operation_state_capture")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=80, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 R9 open blockers must match execution blockers")
    if set(blockers) - set(P7_R54_R8_R9_ALLOWED_EXECUTION_BLOCKER_ID_REFS):
        raise ValueError("R54 R9 has non-canonical blocker ids")
    for false_key in (
        "reviewer_selection_rows_materialized_here", "reviewer_selection_body_stored_here", "reviewer_free_text_body_stored_here", "reviewer_notes_body_stored_here", "machine_auto_score_used", "machine_metrics_used_for_readfeel", "machine_generated_rating_rows_allowed", "not_reviewed_rating_rows_allowed", "rating_rows_created_for_not_reviewed", "actual_review_completed_claimed_here",
        "actual_human_review_run_here", "actual_manual_review_run_here", "actual_rating_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_disposal_receipt_materialized_here", "body_full_packet_generated_here", "actual_body_full_packet_generated_here",
        "raw_input_included", "returned_surface_included", "history_body_included", "comment_text_included", "reviewer_free_text_included", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 R9 must keep {false_key}=False")
    if data.get("rating_source_policy_ref") != P7_R54_RATING_SOURCE_POLICY_REF or data.get("reviewer_selections_only_rating_source") is not True:
        raise ValueError("R54 R9 rating source policy changed")
    if data.get("not_reviewed_rating_policy_ref") != P7_R54_NOT_REVIEWED_RATING_POLICY_REF:
        raise ValueError("R54 R9 not-reviewed rating policy changed")
    if data.get("review_operation_state_ref") not in P7_R54_REVIEW_OPERATION_STATE_REFS:
        raise ValueError("R54 R9 operation state must be canonical")
    if data.get("review_session_status") != P7_R54_R9_OPERATION_REVIEW_SESSION_STATUS_BY_STATE.get(str(data.get("review_operation_state_ref")), "R54_PRECHECK_BLOCKED") and data.get("operation_state_capture_status") != "BLOCKED_BY_R54_8_FORM":
        raise ValueError("R54 R9 review session status changed")
    selection_count = _safe_non_negative_int_r54(data.get("reviewer_selection_count"))
    state = str(data.get("review_operation_state_ref"))
    form_ready = data.get("r8_instruction_form_ready_for_operation_state_capture") is True
    ready_for_capture = data.get("ready_for_sanitized_actual_review_result_capture") is True
    if state in {"not_started", "in_progress"} and selection_count != 0:
        if "r54_actual_review_operation_not_reviewed_has_selection_count" not in blockers:
            raise ValueError("R54 R9 not-started/in-progress selection count must be blocked")
        if data.get("ready_for_sanitized_actual_review_result_capture") is not False or data.get("rating_rows_created_for_not_reviewed") is not False:
            raise ValueError("R54 R9 not-reviewed selection count must not create rating rows")
    if state in P7_R54_R9_CAPTURE_READY_STATE_REFS:
        if ready_for_capture:
            if selection_count != P7_R51_REQUIRED_CASE_COUNT or data.get("reviewer_selection_count_matches_required_case_count") is not True:
                raise ValueError("R54 R9 capture-ready state requires 24 reviewer selections")
        else:
            if "r54_actual_review_operation_capture_ready_selection_count_missing" not in blockers:
                raise ValueError("R54 R9 missing capture-ready selections must be blocked")
    if state in P7_R54_R9_PURGE_REQUIRED_STATE_REFS:
        if data.get("purge_required_before_handoff") is not True or data.get("next_required_step") != P7_R54_R9_PURGE_REQUIRED_NEXT_STEP_REF:
            raise ValueError("R54 R9 abort/expired states must route to purge")
        if ready_for_capture:
            raise ValueError("R54 R9 purge-required state must not hand off to R54-10")
    if ready_for_capture:
        if not form_ready or blockers:
            raise ValueError("R54 R9 capture-ready must have ready R8 form and no blockers")
        if data.get("handoff_to_r54_10_allowed") is not True or data.get("next_required_step") != P7_R54_R9_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R9 capture-ready handoff changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_R9_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_R9_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 R9 capture-ready step lists changed")
    elif form_ready and state in {"not_started", "in_progress"} and not blockers:
        if data.get("operation_pending_without_rating_rows") is not True or data.get("next_required_step") != P7_R54_R9_OPERATION_PENDING_NEXT_STEP_REF:
            raise ValueError("R54 R9 pending operation next step changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_R9_IMPLEMENTED_STEPS:
            raise ValueError("R54 R9 pending implemented steps changed")
    else:
        if data.get("operation_state_capture_status") == "BLOCKED_BY_R54_8_FORM" and data.get("next_required_step") != P7_R54_R9_BLOCKED_NEXT_STEP_REF:
            raise ValueError("R54 R9 blocked form next step changed")
    if data.get("actual_review_operation_state_captured_here") is True and not form_ready:
        raise ValueError("R54 R9 cannot capture state before R8 form is ready")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_actual_human_review_operation_state_capture")
    return True



# ---------------------------------------------------------------------------
# R54-10 / R54-11 sanitized review result capture and rating-row normalization
# ---------------------------------------------------------------------------

P7_R54_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.sanitized_review_result_row.bodyfree.v1"
)
P7_R54_SANITIZED_ACTUAL_REVIEW_RESULT_CAPTURE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.sanitized_actual_review_result_capture.bodyfree.v1"
)
P7_R54_RATING_ROW_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.rating_row.bodyfree.v1"
)
P7_R54_RATING_ROW_NORMALIZATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.rating_row_normalization.bodyfree.v1"
)

P7_R54_R10_STEP_REF: Final = "R54-10_sanitized_actual_review_result_capture"
P7_R54_R11_STEP_REF: Final = "R54-11_rating_row_normalization"
P7_R54_R10_NEXT_REQUIRED_STEP_REF: Final = "R54-11_rating_row_normalization"
P7_R54_R10_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R54-10_sanitized_actual_review_result_capture_requirements"
P7_R54_R11_NEXT_REQUIRED_STEP_REF: Final = "R54-12_readfeel_blocker_execution_blocker_ingestion"
P7_R54_R11_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R54-10_sanitized_actual_review_result_capture_before_R54-11_rating_row_normalization"

P7_R54_FUTURE_STEPS_AFTER_R11: Final[tuple[str, ...]] = tuple(
    step for step in P7_R54_R9_NOT_YET_IMPLEMENTED_STEPS if step not in {P7_R54_R10_STEP_REF, P7_R54_R11_STEP_REF}
)
P7_R54_R10_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_R9_IMPLEMENTED_STEPS, P7_R54_R10_STEP_REF)
P7_R54_R10_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_R11_STEP_REF, *P7_R54_FUTURE_STEPS_AFTER_R11)
P7_R54_R11_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_R10_IMPLEMENTED_STEPS, P7_R54_R11_STEP_REF)
P7_R54_R11_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_FUTURE_STEPS_AFTER_R11

P7_R54_R10_R11_EXECUTION_BLOCKER_ID_REFS: Final[tuple[str, ...]] = (
    "r54_sanitized_review_operation_state_not_ready",
    "r54_sanitized_review_case_manifest_not_ready",
    "r54_sanitized_review_result_rows_missing",
    "r54_sanitized_review_result_rows_incomplete",
    "r54_sanitized_review_result_row_body_leak_detected",
    "r54_sanitized_review_result_row_question_text_detected",
    "r54_sanitized_review_result_row_machine_score_detected",
    "r54_sanitized_review_result_case_set_mismatch",
    "r54_rating_row_normalization_capture_not_ready",
    "r54_rating_rows_incomplete",
    "r54_rating_row_case_set_mismatch",
    "r54_rating_row_body_leak_detected",
    "r54_rating_row_machine_score_detected",
)
P7_R54_R10_R11_ALLOWED_EXECUTION_BLOCKER_ID_REFS: Final[frozenset[str]] = frozenset(
    (*P7_R54_R8_R9_ALLOWED_EXECUTION_BLOCKER_ID_REFS, *P7_R54_R10_R11_EXECUTION_BLOCKER_ID_REFS)
)

P7_R54_SANITIZED_REVIEW_RESULT_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "blind_case_id",
    "case_ref_id",
    "packet_ref_id",
    "case_family_ref",
    "case_role_ref",
    "subscription_boundary_ref",
    "axis_scores",
    "verdict",
    "sanitized_reason_ids",
    "readfeel_blocker_ids",
    "execution_blocker_ids",
    "question_need_primary_class",
    "ambiguity_kind_refs",
    "one_question_fit_ref",
    "repair_required_refs",
    "reviewer_free_text_included",
    "raw_input_included",
    "returned_surface_included",
    "comment_text_included",
    "history_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_absolute_path_included",
    "body_content_hash_included",
    "packet_content_hash_included",
    "machine_auto_score_used",
    "machine_metrics_used_for_readfeel",
    "body_removed",
    "body_free",
)

P7_R54_RATING_ROW_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "blind_case_id",
    "case_ref_id",
    "packet_ref_id",
    "case_family_ref",
    "case_role_ref",
    "subscription_boundary_ref",
    "axis_scores",
    "verdict",
    "sanitized_reason_ids",
    "readfeel_blocker_ids",
    "execution_blocker_ids",
    "body_removed",
    "rating_source_ref",
    "raw_input_included",
    "returned_surface_included",
    "comment_text_included",
    "history_body_included",
    "reviewer_free_text_included",
    "question_text_included",
    "draft_question_text_included",
    "local_absolute_path_included",
    "body_content_hash_included",
    "packet_content_hash_included",
    "machine_auto_score_used",
    "machine_metrics_used_for_readfeel",
    "body_free",
)

P7_R54_R10_FALSE_KEY_REFS: Final[tuple[str, ...]] = P7_R54_R9_FALSE_KEY_REFS
P7_R54_R11_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    key for key in P7_R54_R9_FALSE_KEY_REFS if key != "actual_rating_rows_materialized_here"
)

P7_R54_SANITIZED_ACTUAL_REVIEW_RESULT_CAPTURE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "r9_operation_state_schema_version", "r9_operation_state_material_ref", "r9_operation_state_capture_status", "r9_ready_for_sanitized_actual_review_result_capture", "r9_reviewer_selection_count",
    "r5_manifest_schema_version", "r5_manifest_material_ref", "r5_manifest_status", "r5_manifest_ready_for_result_capture",
    "current_received_snapshot_refs", "current_received_snapshot_ref_count", "r53_source_snapshot_refs", "r53_source_snapshot_ref_count", "r53_refs_are_current_received_refs",
    "required_case_count", "sanitized_review_result_row_schema_version", "sanitized_review_result_row_required_field_refs", "sanitized_review_result_rows", "sanitized_review_result_row_count",
    "reviewed_blind_case_id_count", "reviewed_case_ref_id_count", "reviewed_packet_ref_id_count", "review_result_case_set_matches_manifest", "all_24_cases_reviewed",
    "rating_selections_captured_bodyfree", "question_need_observation_selections_captured_bodyfree", "readfeel_blocker_selections_captured_bodyfree", "execution_blocker_selections_captured_bodyfree",
    "body_full_reader_protocol_local_only", "reviewer_ref", "reviewer_ref_is_pseudonymous", "reviewed_at_ref", "reviewer_free_text_local_only", "reviewer_free_text_bodyfree_export_allowed",
    "reviewer_free_text_included", "raw_input_included", "returned_surface_included", "history_body_included", "comment_text_included", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included",
    "machine_auto_score_used", "machine_metrics_used_for_readfeel", "body_full_packet_generated_here", "actual_body_full_packet_generated_here", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_review_result_rows_captured_here", "actual_rating_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_disposal_receipt_materialized_here", "p5_actual_review_still_not_run_by_helper",
    "capture_status", "capture_reason_refs", "execution_blocker_ids", "open_execution_blocker_ids",
    "r54_0_scope_current_received_snapshot_refrozen", "r54_1_r53_source_delta_current_snapshot_override_adopted", "r54_2_validation_evidence_intake_done", "r54_3_local_only_actual_review_preflight_built", "r54_4_actual_review_session_envelope_built", "r54_5_24_case_manifest_freeze_built", "r54_6_local_only_body_full_packet_generation_request_built", "r54_7_packet_completeness_export_denylist_scan_built", "r54_8_reviewer_instruction_rating_form_freeze_built", "r54_9_actual_human_review_operation_state_capture_built", "r54_10_sanitized_actual_review_result_capture_built",
    "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract", "r54_public_no_touch_contract", "body_free_markers", "body_free",
    *P7_R54_R10_FALSE_KEY_REFS,
    "validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here",
)

P7_R54_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "r10_sanitized_capture_schema_version", "r10_sanitized_capture_material_ref", "r10_capture_status", "r10_capture_ready_for_rating_normalization",
    "current_received_snapshot_refs", "current_received_snapshot_ref_count", "r53_source_snapshot_refs", "r53_source_snapshot_ref_count", "r53_refs_are_current_received_refs",
    "review_session_status", "rating_row_normalizer_status", "rating_row_normalizer_reason_refs", "required_case_count", "sanitized_review_result_row_count", "rating_row_count", "rating_rows",
    "rating_row_schema_version", "rating_row_required_field_refs", "rating_axis_refs", "rating_axis_target_refs", "rating_score_min", "rating_score_max", "missing_axis_scores_pass_allowed", "extra_rating_axis_allowed",
    "machine_auto_score_allowed", "machine_metrics_used_for_readfeel_allowed", "reviewer_free_text_bodyfree_allowed", "sanitized_reason_ids_only", "blocker_ids_only", "allowed_verdict_refs", "readfeel_blocker_id_refs", "execution_blocker_id_refs",
    "blocked_or_not_reviewable_must_use_execution_blocker_row", "red_or_repair_requires_blocker", "pass_requires_targets_and_no_blockers", "body_removed_may_be_false_before_disposal", "rating_rows_are_bodyfree", "all_required_rating_rows_present", "rating_case_ref_sets_match_review_capture",
    "verdict_counts", "rating_consistency_issue_rows", "rating_consistency_issue_count", "pass_with_critical_blocker_detected", "pass_with_any_blocker_detected", "pass_below_axis_target_detected", "red_or_repair_without_blocker_detected", "blocker_row_candidate_count", "execution_blocker_row_candidate_count",
    "body_full_packet_generated_here", "actual_body_full_packet_generated_here", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_disposal_receipt_materialized_here", "p5_actual_review_still_not_run_by_helper",
    "r54_0_scope_current_received_snapshot_refrozen", "r54_1_r53_source_delta_current_snapshot_override_adopted", "r54_2_validation_evidence_intake_done", "r54_3_local_only_actual_review_preflight_built", "r54_4_actual_review_session_envelope_built", "r54_5_24_case_manifest_freeze_built", "r54_6_local_only_body_full_packet_generation_request_built", "r54_7_packet_completeness_export_denylist_scan_built", "r54_8_reviewer_instruction_rating_form_freeze_built", "r54_9_actual_human_review_operation_state_capture_built", "r54_10_sanitized_actual_review_result_capture_built", "r54_11_rating_row_normalization_built",
    "execution_blocker_ids", "open_execution_blocker_ids", "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract", "r54_public_no_touch_contract", "body_free_markers", "body_free",
    *P7_R54_R11_FALSE_KEY_REFS,
    "actual_rating_rows_materialized_here",
    "validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here",
)

P7_R54_REVIEW_RESULT_INPUT_FORBIDDEN_KEY_REFS: Final[frozenset[str]] = frozenset(
    {
        "raw_input",
        "raw_memo",
        "memo",
        "memo_action",
        "raw_history_text",
        "history_body",
        "comment_text",
        "candidate_body",
        "returned_surface",
        "returned_emlis_surface",
        "current_input_review_surface",
        "bounded_owned_history_review_surface",
        "reviewer_free_text",
        "reviewer_notes",
        "reviewer_notes_body",
        "question_text",
        "draft_question_text",
        "local_absolute_path",
        "local_path",
        "body_content_hash",
        "packet_content_hash",
        "body_hash",
        "packet_hash",
        "terminal_output",
        "stdout",
        "stderr",
        "command_result_body",
    }
)


def _reject_r54_review_result_forbidden_keys(value: Mapping[str, Any], *, source: str) -> None:
    forbidden = sorted(set(value) & set(P7_R54_REVIEW_RESULT_INPUT_FORBIDDEN_KEY_REFS))
    if forbidden:
        raise ValueError(f"{source} contains body payload, local path, hash, question text, or reviewer note keys: {forbidden[:4]}")


def _allowed_identifier_sequence_r54(
    value: Any,
    *,
    source: str,
    allowed_refs: Sequence[str] | frozenset[str],
    limit: int = 12,
    max_length: int = 140,
) -> list[str]:
    allowed = set(allowed_refs)
    refs = dedupe_identifiers(_safe_sequence_r54(value), limit=limit, max_length=max_length)
    unknown = sorted(set(refs) - allowed)
    if unknown:
        raise ValueError(f"{source} has non-canonical refs: {unknown[:4]}")
    return refs


def _normalize_axis_scores_r54(value: Any) -> dict[str, float]:
    raw = safe_mapping(value)
    if set(raw) != set(P5_HUMAN_BLIND_QA_RATING_AXES):
        raise ValueError("R54 rating rows require all and only six P5 axes")
    normalized: dict[str, float] = {}
    for axis in P5_HUMAN_BLIND_QA_RATING_AXES:
        score = raw.get(axis)
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise ValueError("R54 axis scores must be numeric")
        score_float = float(score)
        if not P7_R54_RATING_SCORE_MIN <= score_float <= P7_R54_RATING_SCORE_MAX:
            raise ValueError("R54 axis scores must be between 0.0 and 1.0")
        normalized[axis] = score_float
    return normalized


def _assert_r54_verdict_score_blocker_consistency(
    *,
    verdict: str,
    axis_scores: Mapping[str, float],
    readfeel_blocker_ids: Sequence[str],
    execution_blocker_ids: Sequence[str],
    sanitized_reason_ids: Sequence[str],
) -> None:
    # R54-11 must *detect* score/verdict/blocker contradictions; it must not
    # reject otherwise body-free reviewer selections at R54-10/R54 rating-row
    # shape validation time.  This helper therefore only validates canonical
    # value shapes and leaves semantic contradictions to
    # _r54_rating_consistency_issue_rows.
    if verdict not in P7_R54_REVIEW_VERDICT_REFS:
        raise ValueError("R54 rating row verdict must be canonical")
    _normalize_axis_scores_r54(axis_scores)
    for ref in readfeel_blocker_ids:
        if ref not in P7_R48_READFEEL_BLOCKER_ID_REFS:
            raise ValueError("R54 rating row readfeel blocker must be canonical")
    for ref in execution_blocker_ids:
        if ref not in P7_R54_R10_R11_ALLOWED_EXECUTION_BLOCKER_ID_REFS:
            raise ValueError("R54 rating row execution blocker must be canonical")
    for ref in sanitized_reason_ids:
        if ref not in P7_R48_SANITIZED_REASON_ID_REFS:
            raise ValueError("R54 rating row sanitized reason must be canonical")


def _r54_rating_consistency_issue_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    critical_readfeel_blockers = {
        "p5_history_creepy_or_surveillance_feeling",
        "p5_history_scope_overclaim",
        "p5_history_line_self_blame_amplification",
        "p5_free_tier_history_boundary_violation",
        "p5_low_information_history_overread",
        "p5_current_input_overridden_by_history",
        "p5_boundary_history_line_leak_suspected",
    }
    for source_row in rows:
        row = safe_mapping(source_row)
        blind_case_id = clean_identifier(row.get("blind_case_id"), default="blind_case", max_length=160)
        verdict = clean_identifier(row.get("verdict"), default="", max_length=60)
        axis_scores = _normalize_axis_scores_r54(row.get("axis_scores"))
        readfeel_blocker_ids = _allowed_identifier_sequence_r54(row.get("readfeel_blocker_ids"), source="p7_r54_rating_consistency.readfeel_blocker_ids", allowed_refs=P7_R48_READFEEL_BLOCKER_ID_REFS)
        execution_blocker_ids = _allowed_identifier_sequence_r54(row.get("execution_blocker_ids"), source="p7_r54_rating_consistency.execution_blocker_ids", allowed_refs=P7_R54_R10_R11_ALLOWED_EXECUTION_BLOCKER_ID_REFS)
        critical_ids = [blocker for blocker in readfeel_blocker_ids if blocker in critical_readfeel_blockers]
        if verdict == "PASS" and critical_ids:
            issues.append({
                "blind_case_id": blind_case_id,
                "issue_id": "r54_pass_with_critical_blocker_detected",
                "issue_kind_ref": "verdict_blocker_contradiction",
                "body_free": True,
            })
        if verdict == "PASS" and (readfeel_blocker_ids or execution_blocker_ids):
            issues.append({
                "blind_case_id": blind_case_id,
                "issue_id": "r54_pass_with_any_blocker_detected",
                "issue_kind_ref": "pass_must_not_carry_open_blocker",
                "body_free": True,
            })
        below_target = [
            axis
            for axis, target in P5_HUMAN_BLIND_QA_TARGETS.items()
            if float(axis_scores.get(axis, 0.0)) < float(target)
        ]
        if verdict == "PASS" and below_target:
            issues.append({
                "blind_case_id": blind_case_id,
                "issue_id": "r54_pass_below_axis_target_detected",
                "issue_kind_ref": "pass_score_target_contradiction",
                "body_free": True,
            })
        if verdict in {"RED", "REPAIR_REQUIRED"} and not readfeel_blocker_ids and not execution_blocker_ids:
            issues.append({
                "blind_case_id": blind_case_id,
                "issue_id": "r54_red_or_repair_without_blocker_detected",
                "issue_kind_ref": "repair_verdict_requires_blocker_context",
                "body_free": True,
            })
    return issues


def _r54_default_axis_scores() -> dict[str, float]:
    return {axis: 1.0 for axis in P5_HUMAN_BLIND_QA_RATING_AXES}


def _r54_manifest_case_index(manifest: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    rows = [safe_mapping(row) for row in safe_mapping(manifest).get("case_rows") or []]
    index: dict[str, dict[str, Any]] = {}
    for row in rows:
        blind_case_id = clean_identifier(row.get("blind_case_id"), default="", max_length=160)
        if not blind_case_id:
            raise ValueError("R54 manifest row missing blind_case_id")
        if blind_case_id in index:
            raise ValueError("R54 manifest rows duplicate blind_case_id")
        index[blind_case_id] = row
    return index


def _r54_review_result_input_index(rows: Sequence[Mapping[str, Any]] | None) -> dict[str, Mapping[str, Any]]:
    index: dict[str, Mapping[str, Any]] = {}
    for row_raw in rows or []:
        row = safe_mapping(row_raw)
        _reject_r54_review_result_forbidden_keys(row, source="p7_r54_sanitized_review_result_input_row")
        assert_p7_no_body_payload_or_contract_mutation(row, source="p7_r54_sanitized_review_result_input_row")
        blind_case_id = clean_identifier(row.get("blind_case_id"), default="", max_length=160)
        if not blind_case_id:
            raise ValueError("R54 sanitized review result row missing blind_case_id")
        if blind_case_id in index:
            raise ValueError("R54 sanitized review result rows duplicate blind_case_id")
        index[blind_case_id] = row
    return index


def build_p7_r54_sanitized_review_result_row_bodyfree(
    *,
    review_session_id: Any = P7_R54_DEFAULT_REVIEW_SESSION_ID,
    blind_case_id: Any,
    case_ref_id: Any,
    packet_ref_id: Any,
    case_family_ref: Any = "history_line_eligible_input",
    case_role_ref: Any = "positive_history_line",
    subscription_boundary_ref: Any = "plus_or_premium_history_allowed",
    axis_scores: Mapping[str, Any] | None = None,
    verdict: Any = "PASS",
    sanitized_reason_ids: Sequence[Any] = (),
    readfeel_blocker_ids: Sequence[Any] = (),
    execution_blocker_ids: Sequence[Any] = (),
    question_need_primary_class: Any = "no_question_needed_emlis_can_observe",
    ambiguity_kind_refs: Sequence[Any] = ("no_material_ambiguity",),
    one_question_fit_ref: Any = "not_needed",
    repair_required_refs: Sequence[Any] = ("no_repair_required",),
    body_removed: Any = False,
    **forbidden_or_flag_values: Any,
) -> dict[str, Any]:
    """Normalize one sanitized external-local review result row for R54-10."""

    raw_flags = safe_mapping(forbidden_or_flag_values)
    _reject_r54_review_result_forbidden_keys(raw_flags, source="p7_r54_sanitized_review_result_row")
    for false_flag in (
        "reviewer_free_text_included",
        "raw_input_included",
        "returned_surface_included",
        "comment_text_included",
        "history_body_included",
        "question_text_included",
        "draft_question_text_included",
        "local_absolute_path_included",
        "body_content_hash_included",
        "packet_content_hash_included",
        "machine_auto_score_used",
        "machine_metrics_used_for_readfeel",
    ):
        if raw_flags.get(false_flag) is True:
            raise ValueError(f"R54 sanitized review result row must keep {false_flag}=False")
    normalized_scores = _normalize_axis_scores_r54(axis_scores if axis_scores is not None else _r54_default_axis_scores())
    verdict_ref = clean_identifier(verdict, default="", max_length=60)
    if verdict_ref not in P7_R54_REVIEW_VERDICT_REFS:
        raise ValueError("R54 sanitized review result row verdict must be canonical")
    family_ref = clean_identifier(case_family_ref, default="history_line_eligible_input", max_length=160)
    if family_ref not in {row[0] for row in P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION}:
        raise ValueError("R54 sanitized review result row family must be canonical")
    role_ref = clean_identifier(case_role_ref, default="positive_history_line", max_length=160)
    if role_ref not in P7_R48_P5_CASE_ROLE_REFS:
        raise ValueError("R54 sanitized review result row case role must be canonical")
    reason_ids = _allowed_identifier_sequence_r54(
        sanitized_reason_ids,
        source="p7_r54_sanitized_review_result_row.sanitized_reason_ids",
        allowed_refs=P7_R48_SANITIZED_REASON_ID_REFS,
        limit=12,
    )
    readfeel_ids = _allowed_identifier_sequence_r54(
        readfeel_blocker_ids,
        source="p7_r54_sanitized_review_result_row.readfeel_blocker_ids",
        allowed_refs=P7_R48_READFEEL_BLOCKER_ID_REFS,
        limit=12,
    )
    execution_ids = _allowed_identifier_sequence_r54(
        execution_blocker_ids,
        source="p7_r54_sanitized_review_result_row.execution_blocker_ids",
        allowed_refs=P7_R54_R10_R11_ALLOWED_EXECUTION_BLOCKER_ID_REFS,
        limit=12,
    )
    primary_class = clean_identifier(question_need_primary_class, default="", max_length=140)
    if primary_class not in P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS:
        raise ValueError("R54 sanitized review result row question primary class must be canonical")
    ambiguity_refs = _allowed_identifier_sequence_r54(
        ambiguity_kind_refs,
        source="p7_r54_sanitized_review_result_row.ambiguity_kind_refs",
        allowed_refs=P7_R49_AMBIGUITY_KIND_REFS,
        limit=12,
    )
    one_question_fit = clean_identifier(one_question_fit_ref, default="", max_length=140)
    if one_question_fit not in P7_R49_ONE_QUESTION_FIT_REFS:
        raise ValueError("R54 sanitized review result row one-question fit must be canonical")
    repair_refs = _allowed_identifier_sequence_r54(
        repair_required_refs,
        source="p7_r54_sanitized_review_result_row.repair_required_refs",
        allowed_refs=P7_R49_REPAIR_REQUIRED_REF_REFS,
        limit=6,
    )
    if not repair_refs:
        raise ValueError("R54 sanitized review result row repair refs must be explicit")
    _assert_r54_verdict_score_blocker_consistency(
        verdict=verdict_ref,
        axis_scores=normalized_scores,
        readfeel_blocker_ids=readfeel_ids,
        execution_blocker_ids=execution_ids,
        sanitized_reason_ids=reason_ids,
    )
    row = {
        "schema_version": P7_R54_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION,
        "review_session_id": _safe_review_session_id(review_session_id),
        "blind_case_id": clean_identifier(blind_case_id, default="blind_case", max_length=160),
        "case_ref_id": clean_identifier(case_ref_id, default="case_ref", max_length=160),
        "packet_ref_id": clean_identifier(packet_ref_id, default="packet_ref", max_length=160),
        "case_family_ref": family_ref,
        "case_role_ref": role_ref,
        "subscription_boundary_ref": clean_identifier(subscription_boundary_ref, default="subscription_boundary_ref", max_length=160),
        "axis_scores": normalized_scores,
        "verdict": verdict_ref,
        "sanitized_reason_ids": reason_ids,
        "readfeel_blocker_ids": readfeel_ids,
        "execution_blocker_ids": execution_ids,
        "question_need_primary_class": primary_class,
        "ambiguity_kind_refs": ambiguity_refs,
        "one_question_fit_ref": one_question_fit,
        "repair_required_refs": repair_refs,
        "reviewer_free_text_included": False,
        "raw_input_included": False,
        "returned_surface_included": False,
        "comment_text_included": False,
        "history_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_absolute_path_included": False,
        "body_content_hash_included": False,
        "packet_content_hash_included": False,
        "machine_auto_score_used": False,
        "machine_metrics_used_for_readfeel": False,
        "body_removed": _safe_bool_r54(body_removed, default=False),
        "body_free": True,
    }
    assert_p7_r54_sanitized_review_result_row_bodyfree_contract(row)
    return row


def assert_p7_r54_sanitized_review_result_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R54_SANITIZED_REVIEW_RESULT_ROW_REQUIRED_FIELD_REFS, source="p7_r54_sanitized_review_result_row")
    if data.get("schema_version") != P7_R54_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION:
        raise ValueError("R54 sanitized review result row schema changed")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_sanitized_review_result_row")
    if data.get("body_free") is not True:
        raise ValueError("R54 sanitized review result row must be body-free")
    _normalize_axis_scores_r54(data.get("axis_scores"))
    if data.get("verdict") not in P7_R54_REVIEW_VERDICT_REFS:
        raise ValueError("R54 sanitized review result row verdict changed")
    if data.get("case_family_ref") not in {row[0] for row in P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION}:
        raise ValueError("R54 sanitized review result row family changed")
    if data.get("case_role_ref") not in P7_R48_P5_CASE_ROLE_REFS:
        raise ValueError("R54 sanitized review result row role changed")
    reason_ids = _allowed_identifier_sequence_r54(data.get("sanitized_reason_ids"), source="p7_r54_sanitized_review_result_row.sanitized_reason_ids", allowed_refs=P7_R48_SANITIZED_REASON_ID_REFS)
    readfeel_ids = _allowed_identifier_sequence_r54(data.get("readfeel_blocker_ids"), source="p7_r54_sanitized_review_result_row.readfeel_blocker_ids", allowed_refs=P7_R48_READFEEL_BLOCKER_ID_REFS)
    execution_ids = _allowed_identifier_sequence_r54(data.get("execution_blocker_ids"), source="p7_r54_sanitized_review_result_row.execution_blocker_ids", allowed_refs=P7_R54_R10_R11_ALLOWED_EXECUTION_BLOCKER_ID_REFS)
    if data.get("question_need_primary_class") not in P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS:
        raise ValueError("R54 sanitized review result row question primary class changed")
    _allowed_identifier_sequence_r54(data.get("ambiguity_kind_refs"), source="p7_r54_sanitized_review_result_row.ambiguity_kind_refs", allowed_refs=P7_R49_AMBIGUITY_KIND_REFS)
    if data.get("one_question_fit_ref") not in P7_R49_ONE_QUESTION_FIT_REFS:
        raise ValueError("R54 sanitized review result row one-question fit changed")
    repair_refs = _allowed_identifier_sequence_r54(data.get("repair_required_refs"), source="p7_r54_sanitized_review_result_row.repair_required_refs", allowed_refs=P7_R49_REPAIR_REQUIRED_REF_REFS, limit=6)
    if not repair_refs:
        raise ValueError("R54 sanitized review result row repair refs must be explicit")
    for false_key in (
        "reviewer_free_text_included", "raw_input_included", "returned_surface_included", "comment_text_included", "history_body_included", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included", "machine_auto_score_used", "machine_metrics_used_for_readfeel",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 sanitized review result row must keep {false_key}=False")
    if not isinstance(data.get("body_removed"), bool):
        raise ValueError("R54 sanitized review result row body_removed must be boolean")
    _assert_r54_verdict_score_blocker_consistency(
        verdict=str(data.get("verdict")),
        axis_scores=safe_mapping(data.get("axis_scores")),
        readfeel_blocker_ids=readfeel_ids,
        execution_blocker_ids=execution_ids,
        sanitized_reason_ids=reason_ids,
    )
    return True


def _normalize_sanitized_review_result_row_from_manifest_r54(
    *,
    result: Mapping[str, Any],
    manifest_row: Mapping[str, Any],
    review_session_id: Any,
) -> dict[str, Any]:
    source = safe_mapping(result)
    manifest_data = safe_mapping(manifest_row)
    subscription_tier = clean_identifier(manifest_data.get("subscription_tier_ref"), default="unknown", max_length=80)
    subscription_boundary_ref = (
        "free_history_not_allowed"
        if subscription_tier == "free"
        else "plus_or_premium_history_allowed"
        if subscription_tier in {"plus", "premium"}
        else "subscription_boundary_unknown"
    )
    return build_p7_r54_sanitized_review_result_row_bodyfree(
        review_session_id=review_session_id,
        blind_case_id=source.get("blind_case_id") or manifest_data.get("blind_case_id"),
        case_ref_id=source.get("case_ref_id") or manifest_data.get("case_ref_id"),
        packet_ref_id=source.get("packet_ref_id") or manifest_data.get("packet_ref_id"),
        case_family_ref=source.get("case_family_ref") or source.get("family") or manifest_data.get("family"),
        case_role_ref=source.get("case_role_ref") or source.get("case_role") or manifest_data.get("case_role"),
        subscription_boundary_ref=source.get("subscription_boundary_ref") or subscription_boundary_ref,
        axis_scores=safe_mapping(source.get("axis_scores") or _r54_default_axis_scores()),
        verdict=source.get("verdict") or "PASS",
        sanitized_reason_ids=_safe_sequence_r54(source.get("sanitized_reason_ids") or ()),
        readfeel_blocker_ids=_safe_sequence_r54(source.get("readfeel_blocker_ids") or source.get("blocker_ids") or ()),
        execution_blocker_ids=_safe_sequence_r54(source.get("execution_blocker_ids") or ()),
        question_need_primary_class=source.get("question_need_primary_class") or "no_question_needed_emlis_can_observe",
        ambiguity_kind_refs=_safe_sequence_r54(source.get("ambiguity_kind_refs") or ("no_material_ambiguity",)),
        one_question_fit_ref=source.get("one_question_fit_ref") or "not_needed",
        repair_required_refs=_safe_sequence_r54(source.get("repair_required_refs") or ("no_repair_required",)),
        body_removed=source.get("body_removed", False),
        reviewer_free_text_included=source.get("reviewer_free_text_included", False),
        raw_input_included=source.get("raw_input_included", False),
        returned_surface_included=source.get("returned_surface_included", False),
        comment_text_included=source.get("comment_text_included", False),
        history_body_included=source.get("history_body_included", False),
        question_text_included=source.get("question_text_included", False),
        draft_question_text_included=source.get("draft_question_text_included", False),
        local_absolute_path_included=source.get("local_absolute_path_included", False),
        body_content_hash_included=source.get("body_content_hash_included", False),
        packet_content_hash_included=source.get("packet_content_hash_included", False),
        machine_auto_score_used=source.get("machine_auto_score_used", False),
        machine_metrics_used_for_readfeel=source.get("machine_metrics_used_for_readfeel", False),
    )


def _r54_verdict_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = {verdict: 0 for verdict in P7_R54_REVIEW_VERDICT_REFS}
    for row in rows:
        verdict = str(safe_mapping(row).get("verdict"))
        if verdict in counts:
            counts[verdict] += 1
    return counts


def build_p7_r54_sanitized_actual_review_result_capture_bodyfree(
    *,
    actual_human_review_operation_state_capture: Mapping[str, Any] | None = None,
    r9_actual_human_review_operation_state_capture: Mapping[str, Any] | None = None,
    case_manifest_freeze: Mapping[str, Any] | None = None,
    r5_24_case_manifest_freeze: Mapping[str, Any] | None = None,
    sanitized_review_result_rows: Sequence[Mapping[str, Any]] | None = None,
    reviewer_ref: Any = "pseudonymous_reviewer_r54_local_actual_review",
    reviewed_at: Any = "local_review_time_ref_only",
    material_id: Any = "p7_r54_sanitized_actual_review_result_capture",
) -> dict[str, Any]:
    """Build R54-10 body-free capture of sanitized external review selections."""

    if actual_human_review_operation_state_capture is not None and r9_actual_human_review_operation_state_capture is not None:
        raise ValueError("provide only one R54-9 operation state value")
    if case_manifest_freeze is not None and r5_24_case_manifest_freeze is not None:
        raise ValueError("provide only one R54-5 manifest value")
    r9 = safe_mapping(
        actual_human_review_operation_state_capture
        if actual_human_review_operation_state_capture is not None
        else r9_actual_human_review_operation_state_capture
    )
    if not r9:
        r9 = build_p7_r54_actual_human_review_operation_state_capture_bodyfree()
    assert_p7_r54_actual_human_review_operation_state_capture_bodyfree_contract(r9)
    r5 = safe_mapping(case_manifest_freeze if case_manifest_freeze is not None else r5_24_case_manifest_freeze)
    if not r5:
        r5 = build_p7_r54_24_case_manifest_freeze_bodyfree()
    assert_p7_r54_24_case_manifest_freeze_bodyfree_contract(r5)

    r9_ready = r9.get("ready_for_sanitized_actual_review_result_capture") is True and not r9.get("execution_blocker_ids")
    r5_ready = r5.get("manifest_status") == "READY_FOR_LOCAL_ONLY_PACKET_GENERATION_REQUEST" and not r5.get("execution_blocker_ids")
    blockers = dedupe_identifiers([*(r9.get("execution_blocker_ids") or []), *(r5.get("execution_blocker_ids") or [])], limit=80, max_length=140)
    reason_refs: list[str] = []
    if not r9_ready:
        blockers = dedupe_identifiers([*blockers, "r54_sanitized_review_operation_state_not_ready"], limit=80, max_length=140)
        reason_refs.append("r54_9_operation_state_not_ready_for_sanitized_capture")
    if not r5_ready:
        blockers = dedupe_identifiers([*blockers, "r54_sanitized_review_case_manifest_not_ready"], limit=80, max_length=140)
        reason_refs.append("r54_5_manifest_not_ready_for_sanitized_capture")
    manifest_index = _r54_manifest_case_index(r5) if r5_ready else {}
    result_index = _r54_review_result_input_index(sanitized_review_result_rows)
    if r9_ready and r5_ready and sanitized_review_result_rows is None:
        blockers = dedupe_identifiers([*blockers, "r54_sanitized_review_result_rows_missing"], limit=80, max_length=140)
        reason_refs.append("r54_sanitized_review_result_rows_missing")
    if r9_ready and r5_ready and len(result_index) != P7_R51_REQUIRED_CASE_COUNT:
        blockers = dedupe_identifiers([*blockers, "r54_sanitized_review_result_rows_incomplete"], limit=80, max_length=140)
        reason_refs.append("r54_sanitized_review_result_rows_incomplete")
    missing_blind_ids = sorted(set(manifest_index) - set(result_index)) if r5_ready else []
    extra_blind_ids = sorted(set(result_index) - set(manifest_index)) if r5_ready else []
    if r9_ready and r5_ready and (missing_blind_ids or extra_blind_ids):
        blockers = dedupe_identifiers([*blockers, "r54_sanitized_review_result_case_set_mismatch"], limit=80, max_length=140)
        reason_refs.append("r54_sanitized_review_result_case_set_mismatch")
    capture_rows: list[dict[str, Any]] = []
    if r9_ready and r5_ready and not blockers and len(result_index) == P7_R51_REQUIRED_CASE_COUNT:
        for blind_case_id in sorted(manifest_index):
            capture_rows.append(
                _normalize_sanitized_review_result_row_from_manifest_r54(
                    result=result_index[blind_case_id],
                    manifest_row=manifest_index[blind_case_id],
                    review_session_id=r9.get("review_session_id"),
                )
            )
    ready = r9_ready and r5_ready and len(capture_rows) == P7_R51_REQUIRED_CASE_COUNT and not blockers
    if ready:
        reason_refs = ["r54_sanitized_actual_review_result_rows_captured_bodyfree"]
    elif not reason_refs:
        reason_refs = ["r54_sanitized_actual_review_result_capture_blocked"]
    blind_ids = {row["blind_case_id"] for row in capture_rows}
    case_ids = {row["case_ref_id"] for row in capture_rows}
    packet_ids = {row["packet_ref_id"] for row in capture_rows}
    material = {
        "schema_version": P7_R54_SANITIZED_ACTUAL_REVIEW_RESULT_CAPTURE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_STEP,
        "scope": P7_R54_SCOPE,
        "policy_kind": P7_R54_POLICY_KIND,
        "policy_section": "R54-10_sanitized_actual_review_result_capture",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_sanitized_actual_review_result_capture", max_length=220),
        "review_session_id": _safe_review_session_id(r9.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r9_operation_state_schema_version": P7_R54_ACTUAL_HUMAN_REVIEW_OPERATION_STATE_CAPTURE_SCHEMA_VERSION,
        "r9_operation_state_material_ref": clean_identifier(r9.get("material_id"), default="p7_r54_actual_human_review_operation_state_capture", max_length=220),
        "r9_operation_state_capture_status": clean_identifier(r9.get("operation_state_capture_status"), default="R54_REVIEW_OPERATION_STATE_CAPTURED_PENDING", max_length=140),
        "r9_ready_for_sanitized_actual_review_result_capture": r9_ready,
        "r9_reviewer_selection_count": _safe_non_negative_int_r54(r9.get("reviewer_selection_count")),
        "r5_manifest_schema_version": P7_R54_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION,
        "r5_manifest_material_ref": clean_identifier(r5.get("material_id"), default="p7_r54_24_case_manifest_freeze", max_length=220),
        "r5_manifest_status": clean_identifier(r5.get("manifest_status"), default="BLOCKED_BY_R54_4_ENVELOPE", max_length=140),
        "r5_manifest_ready_for_result_capture": r5_ready,
        "current_received_snapshot_refs": safe_mapping(r9.get("current_received_snapshot_refs")),
        "current_received_snapshot_ref_count": len(safe_mapping(r9.get("current_received_snapshot_refs"))),
        "r53_source_snapshot_refs": safe_mapping(r9.get("r53_source_snapshot_refs")),
        "r53_source_snapshot_ref_count": len(safe_mapping(r9.get("r53_source_snapshot_refs"))),
        "r53_refs_are_current_received_refs": False,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "sanitized_review_result_row_schema_version": P7_R54_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION,
        "sanitized_review_result_row_required_field_refs": list(P7_R54_SANITIZED_REVIEW_RESULT_ROW_REQUIRED_FIELD_REFS),
        "sanitized_review_result_rows": capture_rows,
        "sanitized_review_result_row_count": len(capture_rows),
        "reviewed_blind_case_id_count": len(blind_ids),
        "reviewed_case_ref_id_count": len(case_ids),
        "reviewed_packet_ref_id_count": len(packet_ids),
        "review_result_case_set_matches_manifest": ready,
        "all_24_cases_reviewed": ready,
        "rating_selections_captured_bodyfree": ready,
        "question_need_observation_selections_captured_bodyfree": ready,
        "readfeel_blocker_selections_captured_bodyfree": ready,
        "execution_blocker_selections_captured_bodyfree": ready,
        "body_full_reader_protocol_local_only": True,
        "reviewer_ref": clean_identifier(reviewer_ref, default="pseudonymous_reviewer_r54_local_actual_review", max_length=140),
        "reviewer_ref_is_pseudonymous": True,
        "reviewed_at_ref": clean_identifier(reviewed_at, default="local_review_time_ref_only", max_length=140),
        "reviewer_free_text_local_only": True,
        "reviewer_free_text_bodyfree_export_allowed": False,
        "reviewer_free_text_included": False,
        "raw_input_included": False,
        "returned_surface_included": False,
        "history_body_included": False,
        "comment_text_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_absolute_path_included": False,
        "body_content_hash_included": False,
        "packet_content_hash_included": False,
        "machine_auto_score_used": False,
        "machine_metrics_used_for_readfeel": False,
        "body_full_packet_generated_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "actual_review_result_rows_captured_here": ready,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "p5_actual_review_still_not_run_by_helper": True,
        "capture_status": "READY_FOR_RATING_ROW_NORMALIZATION" if ready else "BLOCKED_BY_R54_9_OR_MISSING_SANITIZED_REVIEW_RESULTS",
        "capture_reason_refs": dedupe_identifiers(reason_refs, limit=40, max_length=160),
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        **_false_flags_except({"validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here"}),
        "r54_0_scope_current_received_snapshot_refrozen": r9.get("r54_0_scope_current_received_snapshot_refrozen") is True,
        "r54_1_r53_source_delta_current_snapshot_override_adopted": r9.get("r54_1_r53_source_delta_current_snapshot_override_adopted") is True,
        "r54_2_validation_evidence_intake_done": r9.get("r54_2_validation_evidence_intake_done") is True,
        "r54_3_local_only_actual_review_preflight_built": r9.get("r54_3_local_only_actual_review_preflight_built") is True,
        "r54_4_actual_review_session_envelope_built": r9.get("r54_4_actual_review_session_envelope_built") is True,
        "r54_5_24_case_manifest_freeze_built": r5.get("r54_5_24_case_manifest_freeze_built") is True,
        "r54_6_local_only_body_full_packet_generation_request_built": r9.get("r54_6_local_only_body_full_packet_generation_request_built") is True,
        "r54_7_packet_completeness_export_denylist_scan_built": r9.get("r54_7_packet_completeness_export_denylist_scan_built") is True,
        "r54_8_reviewer_instruction_rating_form_freeze_built": r9.get("r54_8_reviewer_instruction_rating_form_freeze_built") is True,
        "r54_9_actual_human_review_operation_state_capture_built": r9.get("r54_9_actual_human_review_operation_state_capture_built") is True,
        "r54_10_sanitized_actual_review_result_capture_built": ready,
        "implemented_steps": list(P7_R54_R10_IMPLEMENTED_STEPS if ready else P7_R54_R9_IMPLEMENTED_STEPS if r9_ready else P7_R54_R8_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_R10_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_R9_NOT_YET_IMPLEMENTED_STEPS if r9_ready else P7_R54_R8_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R54_R10_NEXT_REQUIRED_STEP_REF if ready else P7_R54_R10_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "next_required_step": P7_R54_R10_NEXT_REQUIRED_STEP_REF if ready else P7_R54_R10_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "validation_evidence_intake_done_here": r9.get("validation_evidence_intake_done_here") is True,
        "local_root_preflight_passed_here": r9.get("local_root_preflight_passed_here") is True,
        "explicit_allow_present_here": r9.get("explicit_allow_present_here") is True,
        "purge_plan_verified_here": r9.get("purge_plan_verified_here") is True,
    }
    assert_p7_r54_sanitized_actual_review_result_capture_bodyfree_contract(material)
    return material


def assert_p7_r54_sanitized_actual_review_result_capture_bodyfree_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_SANITIZED_ACTUAL_REVIEW_RESULT_CAPTURE_REQUIRED_FIELD_REFS, source="p7_r54_sanitized_actual_review_result_capture")
    _assert_body_free_common_with_false_keys(data, schema_version=P7_R54_SANITIZED_ACTUAL_REVIEW_RESULT_CAPTURE_SCHEMA_VERSION, source="p7_r54_sanitized_actual_review_result_capture", false_key_refs=P7_R54_R10_FALSE_KEY_REFS)
    _assert_current_refs(data, source="p7_r54_sanitized_actual_review_result_capture")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=80, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 R10 open blockers must match execution blockers")
    if set(blockers) - set(P7_R54_R10_R11_ALLOWED_EXECUTION_BLOCKER_ID_REFS):
        raise ValueError("R54 R10 has non-canonical blocker ids")
    for false_key in (
        "reviewer_free_text_bodyfree_export_allowed", "reviewer_free_text_included", "raw_input_included", "returned_surface_included", "history_body_included", "comment_text_included", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included", "machine_auto_score_used", "machine_metrics_used_for_readfeel", "body_full_packet_generated_here", "actual_body_full_packet_generated_here", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_rating_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_disposal_receipt_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 R10 must keep {false_key}=False")
    rows = [safe_mapping(row) for row in (data.get("sanitized_review_result_rows") or [])]
    for row in rows:
        assert_p7_r54_sanitized_review_result_row_bodyfree_contract(row)
    ready = data.get("capture_status") == "READY_FOR_RATING_ROW_NORMALIZATION"
    if data.get("sanitized_review_result_row_schema_version") != P7_R54_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION:
        raise ValueError("R54 R10 sanitized row schema reference changed")
    if tuple(data.get("sanitized_review_result_row_required_field_refs") or ()) != P7_R54_SANITIZED_REVIEW_RESULT_ROW_REQUIRED_FIELD_REFS:
        raise ValueError("R54 R10 sanitized row required fields changed")
    if ready:
        if data.get("r9_ready_for_sanitized_actual_review_result_capture") is not True or data.get("r5_manifest_ready_for_result_capture") is not True:
            raise ValueError("R54 R10 ready capture requires R54-9 and R54-5 ready")
        if len(rows) != P7_R51_REQUIRED_CASE_COUNT or data.get("sanitized_review_result_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 R10 ready capture must carry 24 sanitized rows")
        if data.get("reviewed_blind_case_id_count") != P7_R51_REQUIRED_CASE_COUNT or data.get("reviewed_case_ref_id_count") != P7_R51_REQUIRED_CASE_COUNT or data.get("reviewed_packet_ref_id_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 R10 ready capture must have 24 unique blind/case/packet refs")
        if data.get("review_result_case_set_matches_manifest") is not True or data.get("all_24_cases_reviewed") is not True:
            raise ValueError("R54 R10 ready capture case set must match manifest")
        if data.get("rating_selections_captured_bodyfree") is not True or data.get("question_need_observation_selections_captured_bodyfree") is not True:
            raise ValueError("R54 R10 ready capture must include rating and question observation selections")
        if data.get("actual_review_result_rows_captured_here") is not True or data.get("r54_10_sanitized_actual_review_result_capture_built") is not True:
            raise ValueError("R54 R10 ready capture built flag changed")
        if blockers:
            raise ValueError("R54 R10 ready capture must not carry blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_R10_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_R10_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 R10 ready step lists changed")
        if data.get("next_required_step") != P7_R54_R10_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R10 ready next step changed")
    else:
        if data.get("actual_review_result_rows_captured_here") is not False or data.get("r54_10_sanitized_actual_review_result_capture_built") is not False:
            raise ValueError("R54 R10 blocked capture must not claim built")
        if data.get("sanitized_review_result_row_count") != 0 or rows:
            raise ValueError("R54 R10 blocked capture must not expose partial sanitized rows")
        if not blockers or data.get("next_required_step") != P7_R54_R10_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R10 blocked capture next step changed")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_sanitized_actual_review_result_capture")
    return True


def build_p7_r54_rating_row_bodyfree(*, sanitized_review_result_row: Mapping[str, Any]) -> dict[str, Any]:
    source = safe_mapping(sanitized_review_result_row)
    assert_p7_r54_sanitized_review_result_row_bodyfree_contract(source)
    row = {
        "schema_version": P7_R54_RATING_ROW_BODYFREE_SCHEMA_VERSION,
        "review_session_id": _safe_review_session_id(source.get("review_session_id")),
        "blind_case_id": clean_identifier(source.get("blind_case_id"), default="blind_case", max_length=160),
        "case_ref_id": clean_identifier(source.get("case_ref_id"), default="case_ref", max_length=160),
        "packet_ref_id": clean_identifier(source.get("packet_ref_id"), default="packet_ref", max_length=160),
        "case_family_ref": clean_identifier(source.get("case_family_ref"), default="history_line_eligible_input", max_length=160),
        "case_role_ref": clean_identifier(source.get("case_role_ref"), default="positive_history_line", max_length=160),
        "subscription_boundary_ref": clean_identifier(source.get("subscription_boundary_ref"), default="subscription_boundary_ref", max_length=160),
        "axis_scores": _normalize_axis_scores_r54(source.get("axis_scores")),
        "verdict": clean_identifier(source.get("verdict"), default="PASS", max_length=60),
        "sanitized_reason_ids": _allowed_identifier_sequence_r54(source.get("sanitized_reason_ids"), source="p7_r54_rating_row.sanitized_reason_ids", allowed_refs=P7_R48_SANITIZED_REASON_ID_REFS),
        "readfeel_blocker_ids": _allowed_identifier_sequence_r54(source.get("readfeel_blocker_ids"), source="p7_r54_rating_row.readfeel_blocker_ids", allowed_refs=P7_R48_READFEEL_BLOCKER_ID_REFS),
        "execution_blocker_ids": _allowed_identifier_sequence_r54(source.get("execution_blocker_ids"), source="p7_r54_rating_row.execution_blocker_ids", allowed_refs=P7_R54_R10_R11_ALLOWED_EXECUTION_BLOCKER_ID_REFS),
        "body_removed": _safe_bool_r54(source.get("body_removed"), default=False),
        "rating_source_ref": "sanitized_external_local_reviewer_selection_only",
        "raw_input_included": False,
        "returned_surface_included": False,
        "comment_text_included": False,
        "history_body_included": False,
        "reviewer_free_text_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_absolute_path_included": False,
        "body_content_hash_included": False,
        "packet_content_hash_included": False,
        "machine_auto_score_used": False,
        "machine_metrics_used_for_readfeel": False,
        "body_free": True,
    }
    assert_p7_r54_rating_row_bodyfree_contract(row)
    return row


def assert_p7_r54_rating_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R54_RATING_ROW_BODYFREE_REQUIRED_FIELD_REFS, source="p7_r54_rating_row")
    if data.get("schema_version") != P7_R54_RATING_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R54 rating row schema changed")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_rating_row")
    if data.get("body_free") is not True:
        raise ValueError("R54 rating row must be body-free")
    axis_scores = _normalize_axis_scores_r54(data.get("axis_scores"))
    if data.get("verdict") not in P7_R54_REVIEW_VERDICT_REFS:
        raise ValueError("R54 rating row verdict changed")
    if data.get("case_family_ref") not in {row[0] for row in P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION}:
        raise ValueError("R54 rating row family changed")
    if data.get("case_role_ref") not in P7_R48_P5_CASE_ROLE_REFS:
        raise ValueError("R54 rating row role changed")
    reason_ids = _allowed_identifier_sequence_r54(data.get("sanitized_reason_ids"), source="p7_r54_rating_row.sanitized_reason_ids", allowed_refs=P7_R48_SANITIZED_REASON_ID_REFS)
    readfeel_ids = _allowed_identifier_sequence_r54(data.get("readfeel_blocker_ids"), source="p7_r54_rating_row.readfeel_blocker_ids", allowed_refs=P7_R48_READFEEL_BLOCKER_ID_REFS)
    execution_ids = _allowed_identifier_sequence_r54(data.get("execution_blocker_ids"), source="p7_r54_rating_row.execution_blocker_ids", allowed_refs=P7_R54_R10_R11_ALLOWED_EXECUTION_BLOCKER_ID_REFS)
    _assert_r54_verdict_score_blocker_consistency(
        verdict=str(data.get("verdict")),
        axis_scores=axis_scores,
        readfeel_blocker_ids=readfeel_ids,
        execution_blocker_ids=execution_ids,
        sanitized_reason_ids=reason_ids,
    )
    for false_key in (
        "raw_input_included", "returned_surface_included", "comment_text_included", "history_body_included", "reviewer_free_text_included", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included", "machine_auto_score_used", "machine_metrics_used_for_readfeel",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 rating row must keep {false_key}=False")
    if data.get("rating_source_ref") != "sanitized_external_local_reviewer_selection_only":
        raise ValueError("R54 rating row source ref changed")
    return True


def build_p7_r54_rating_row_normalization_bodyfree(
    *,
    sanitized_actual_review_result_capture: Mapping[str, Any] | None = None,
    r10_sanitized_actual_review_result_capture: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_rating_row_normalization",
) -> dict[str, Any]:
    """Build R54-11 body-free rating row normalization from R54-10 capture."""

    if sanitized_actual_review_result_capture is not None and r10_sanitized_actual_review_result_capture is not None:
        raise ValueError("provide only one R54-10 sanitized capture value")
    r10 = safe_mapping(
        sanitized_actual_review_result_capture
        if sanitized_actual_review_result_capture is not None
        else r10_sanitized_actual_review_result_capture
    )
    if not r10:
        r10 = build_p7_r54_sanitized_actual_review_result_capture_bodyfree()
    assert_p7_r54_sanitized_actual_review_result_capture_bodyfree_contract(r10)
    r10_ready = r10.get("capture_status") == "READY_FOR_RATING_ROW_NORMALIZATION" and not r10.get("execution_blocker_ids")
    blockers = dedupe_identifiers(r10.get("execution_blocker_ids") or [], limit=80, max_length=140)
    reason_refs: list[str] = []
    rating_rows: list[dict[str, Any]] = []
    if not r10_ready:
        blockers = dedupe_identifiers([*blockers, "r54_rating_row_normalization_capture_not_ready"], limit=80, max_length=140)
        reason_refs.append("r54_sanitized_capture_not_ready_for_rating_normalization")
    if r10_ready:
        for source_row in r10.get("sanitized_review_result_rows") or []:
            rating_rows.append(build_p7_r54_rating_row_bodyfree(sanitized_review_result_row=safe_mapping(source_row)))
        if len(rating_rows) != P7_R51_REQUIRED_CASE_COUNT:
            blockers = dedupe_identifiers([*blockers, "r54_rating_rows_incomplete"], limit=80, max_length=140)
            reason_refs.append("r54_rating_rows_incomplete")
        review_case_refs = {safe_mapping(row).get("case_ref_id") for row in r10.get("sanitized_review_result_rows") or []}
        rating_case_refs = {safe_mapping(row).get("case_ref_id") for row in rating_rows}
        if review_case_refs != rating_case_refs or len(rating_case_refs) != P7_R51_REQUIRED_CASE_COUNT:
            blockers = dedupe_identifiers([*blockers, "r54_rating_row_case_set_mismatch"], limit=80, max_length=140)
            reason_refs.append("r54_rating_row_case_set_mismatch")
    ready = r10_ready and len(rating_rows) == P7_R51_REQUIRED_CASE_COUNT and not blockers
    consistency_issues = _r54_rating_consistency_issue_rows(rating_rows) if ready else []
    if ready:
        reason_refs = ["r54_rating_rows_normalized_bodyfree"]
    elif not reason_refs:
        reason_refs = ["r54_rating_row_normalization_blocked"]
    material = {
        "schema_version": P7_R54_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_STEP,
        "scope": P7_R54_SCOPE,
        "policy_kind": P7_R54_POLICY_KIND,
        "policy_section": "R54-11_rating_row_normalization",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_rating_row_normalization", max_length=220),
        "review_session_id": _safe_review_session_id(r10.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r10_sanitized_capture_schema_version": P7_R54_SANITIZED_ACTUAL_REVIEW_RESULT_CAPTURE_SCHEMA_VERSION,
        "r10_sanitized_capture_material_ref": clean_identifier(r10.get("material_id"), default="p7_r54_sanitized_actual_review_result_capture", max_length=220),
        "r10_capture_status": clean_identifier(r10.get("capture_status"), default="BLOCKED_BY_R54_9_OR_MISSING_SANITIZED_REVIEW_RESULTS", max_length=140),
        "r10_capture_ready_for_rating_normalization": r10_ready,
        "current_received_snapshot_refs": safe_mapping(r10.get("current_received_snapshot_refs")),
        "current_received_snapshot_ref_count": len(safe_mapping(r10.get("current_received_snapshot_refs"))),
        "r53_source_snapshot_refs": safe_mapping(r10.get("r53_source_snapshot_refs")),
        "r53_source_snapshot_ref_count": len(safe_mapping(r10.get("r53_source_snapshot_refs"))),
        "r53_refs_are_current_received_refs": False,
        "review_session_status": "R54_RATING_ROW_NORMALIZATION_READY" if ready else "PRECHECK_BLOCKED",
        "rating_row_normalizer_status": "READY_FOR_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION" if ready else "BLOCKED_BY_R54_10_SANITIZED_CAPTURE",
        "rating_row_normalizer_reason_refs": dedupe_identifiers(reason_refs, limit=40, max_length=160),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "sanitized_review_result_row_count": _safe_non_negative_int_r54(r10.get("sanitized_review_result_row_count")) if ready else 0,
        "rating_row_count": len(rating_rows) if ready else 0,
        "rating_rows": rating_rows if ready else [],
        "rating_row_schema_version": P7_R54_RATING_ROW_BODYFREE_SCHEMA_VERSION,
        "rating_row_required_field_refs": list(P7_R54_RATING_ROW_BODYFREE_REQUIRED_FIELD_REFS),
        "rating_axis_refs": list(P5_HUMAN_BLIND_QA_RATING_AXES),
        "rating_axis_target_refs": dict(P5_HUMAN_BLIND_QA_TARGETS),
        "rating_score_min": P7_R54_RATING_SCORE_MIN,
        "rating_score_max": P7_R54_RATING_SCORE_MAX,
        "missing_axis_scores_pass_allowed": False,
        "extra_rating_axis_allowed": False,
        "machine_auto_score_allowed": False,
        "machine_metrics_used_for_readfeel_allowed": False,
        "reviewer_free_text_bodyfree_allowed": False,
        "sanitized_reason_ids_only": True,
        "blocker_ids_only": True,
        "allowed_verdict_refs": list(P7_R54_REVIEW_VERDICT_REFS),
        "readfeel_blocker_id_refs": list(P7_R48_READFEEL_BLOCKER_ID_REFS),
        "execution_blocker_id_refs": list(P7_R54_R10_R11_ALLOWED_EXECUTION_BLOCKER_ID_REFS),
        "blocked_or_not_reviewable_must_use_execution_blocker_row": True,
        "red_or_repair_requires_blocker": True,
        "pass_requires_targets_and_no_blockers": True,
        "body_removed_may_be_false_before_disposal": True,
        "rating_rows_are_bodyfree": True,
        "all_required_rating_rows_present": ready,
        "rating_case_ref_sets_match_review_capture": ready,
        "verdict_counts": _r54_verdict_counts(rating_rows) if ready else _r54_verdict_counts(()),
        "rating_consistency_issue_rows": consistency_issues if ready else [],
        "rating_consistency_issue_count": len(consistency_issues) if ready else 0,
        "pass_with_critical_blocker_detected": any(safe_mapping(row).get("issue_id") == "r54_pass_with_critical_blocker_detected" for row in consistency_issues) if ready else False,
        "pass_with_any_blocker_detected": any(safe_mapping(row).get("issue_id") == "r54_pass_with_any_blocker_detected" for row in consistency_issues) if ready else False,
        "pass_below_axis_target_detected": any(safe_mapping(row).get("issue_id") == "r54_pass_below_axis_target_detected" for row in consistency_issues) if ready else False,
        "red_or_repair_without_blocker_detected": any(safe_mapping(row).get("issue_id") == "r54_red_or_repair_without_blocker_detected" for row in consistency_issues) if ready else False,
        "blocker_row_candidate_count": sum(1 for row in rating_rows if safe_mapping(row).get("readfeel_blocker_ids")) if ready else 0,
        "execution_blocker_row_candidate_count": sum(1 for row in rating_rows if safe_mapping(row).get("execution_blocker_ids")) if ready else len(blockers),
        "body_full_packet_generated_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "actual_rating_rows_materialized_here": ready,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "p5_actual_review_still_not_run_by_helper": True,
        "r54_0_scope_current_received_snapshot_refrozen": r10.get("r54_0_scope_current_received_snapshot_refrozen") is True,
        "r54_1_r53_source_delta_current_snapshot_override_adopted": r10.get("r54_1_r53_source_delta_current_snapshot_override_adopted") is True,
        "r54_2_validation_evidence_intake_done": r10.get("r54_2_validation_evidence_intake_done") is True,
        "r54_3_local_only_actual_review_preflight_built": r10.get("r54_3_local_only_actual_review_preflight_built") is True,
        "r54_4_actual_review_session_envelope_built": r10.get("r54_4_actual_review_session_envelope_built") is True,
        "r54_5_24_case_manifest_freeze_built": r10.get("r54_5_24_case_manifest_freeze_built") is True,
        "r54_6_local_only_body_full_packet_generation_request_built": r10.get("r54_6_local_only_body_full_packet_generation_request_built") is True,
        "r54_7_packet_completeness_export_denylist_scan_built": r10.get("r54_7_packet_completeness_export_denylist_scan_built") is True,
        "r54_8_reviewer_instruction_rating_form_freeze_built": r10.get("r54_8_reviewer_instruction_rating_form_freeze_built") is True,
        "r54_9_actual_human_review_operation_state_capture_built": r10.get("r54_9_actual_human_review_operation_state_capture_built") is True,
        "r54_10_sanitized_actual_review_result_capture_built": r10.get("r54_10_sanitized_actual_review_result_capture_built") is True,
        "r54_11_rating_row_normalization_built": ready,
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        **_false_flags_except({"validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here", "actual_rating_rows_materialized_here"}),
        "implemented_steps": list(P7_R54_R11_IMPLEMENTED_STEPS if ready else P7_R54_R10_IMPLEMENTED_STEPS if r10_ready else P7_R54_R9_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_R11_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_R10_NOT_YET_IMPLEMENTED_STEPS if r10_ready else P7_R54_R9_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R54_R11_NEXT_REQUIRED_STEP_REF if ready else P7_R54_R11_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "next_required_step": P7_R54_R11_NEXT_REQUIRED_STEP_REF if ready else P7_R54_R11_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "validation_evidence_intake_done_here": r10.get("validation_evidence_intake_done_here") is True,
        "local_root_preflight_passed_here": r10.get("local_root_preflight_passed_here") is True,
        "explicit_allow_present_here": r10.get("explicit_allow_present_here") is True,
        "purge_plan_verified_here": r10.get("purge_plan_verified_here") is True,
    }
    assert_p7_r54_rating_row_normalization_bodyfree_contract(material)
    return material


def assert_p7_r54_rating_row_normalization_bodyfree_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS, source="p7_r54_rating_row_normalization")
    _assert_body_free_common_with_false_keys(data, schema_version=P7_R54_RATING_ROW_NORMALIZATION_SCHEMA_VERSION, source="p7_r54_rating_row_normalization", false_key_refs=P7_R54_R11_FALSE_KEY_REFS)
    _assert_current_refs(data, source="p7_r54_rating_row_normalization")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=80, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 R11 open blockers must match execution blockers")
    if set(blockers) - set(P7_R54_R10_R11_ALLOWED_EXECUTION_BLOCKER_ID_REFS):
        raise ValueError("R54 R11 has non-canonical blocker ids")
    rows = [safe_mapping(row) for row in (data.get("rating_rows") or [])]
    for row in rows:
        assert_p7_r54_rating_row_bodyfree_contract(row)
    for true_key in (
        "sanitized_reason_ids_only", "blocker_ids_only", "blocked_or_not_reviewable_must_use_execution_blocker_row", "red_or_repair_requires_blocker", "pass_requires_targets_and_no_blockers", "body_removed_may_be_false_before_disposal", "rating_rows_are_bodyfree",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R54 R11 must keep {true_key}=True")
    for false_key in (
        "missing_axis_scores_pass_allowed", "extra_rating_axis_allowed", "machine_auto_score_allowed", "machine_metrics_used_for_readfeel_allowed", "reviewer_free_text_bodyfree_allowed", "body_full_packet_generated_here", "actual_body_full_packet_generated_here", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_disposal_receipt_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 R11 must keep {false_key}=False")
    if data.get("rating_row_schema_version") != P7_R54_RATING_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R54 R11 rating row schema reference changed")
    if tuple(data.get("rating_row_required_field_refs") or ()) != P7_R54_RATING_ROW_BODYFREE_REQUIRED_FIELD_REFS:
        raise ValueError("R54 R11 rating row required fields changed")
    if tuple(data.get("rating_axis_refs") or ()) != P5_HUMAN_BLIND_QA_RATING_AXES:
        raise ValueError("R54 R11 rating axes changed")
    if safe_mapping(data.get("rating_axis_target_refs")) != dict(P5_HUMAN_BLIND_QA_TARGETS):
        raise ValueError("R54 R11 rating targets changed")
    if data.get("rating_score_min") != P7_R54_RATING_SCORE_MIN or data.get("rating_score_max") != P7_R54_RATING_SCORE_MAX:
        raise ValueError("R54 R11 rating score bounds changed")
    if tuple(data.get("allowed_verdict_refs") or ()) != P7_R54_REVIEW_VERDICT_REFS:
        raise ValueError("R54 R11 verdict refs changed")
    if tuple(data.get("readfeel_blocker_id_refs") or ()) != P7_R48_READFEEL_BLOCKER_ID_REFS:
        raise ValueError("R54 R11 readfeel blocker refs changed")
    ready = data.get("rating_row_normalizer_status") == "READY_FOR_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION"
    if data.get("actual_rating_rows_materialized_here") is not ready:
        raise ValueError("R54 R11 actual rating materialized flag must match readiness")
    issue_rows = [safe_mapping(row) for row in (data.get("rating_consistency_issue_rows") or [])]
    if data.get("rating_consistency_issue_count") != len(issue_rows):
        raise ValueError("R54 R11 consistency issue count mismatch")
    issue_ids = {row.get("issue_id") for row in issue_rows}
    if data.get("pass_with_critical_blocker_detected") is not ("r54_pass_with_critical_blocker_detected" in issue_ids):
        raise ValueError("R54 R11 pass-with-critical-blocker flag mismatch")
    if data.get("pass_with_any_blocker_detected") is not ("r54_pass_with_any_blocker_detected" in issue_ids):
        raise ValueError("R54 R11 pass-with-any-blocker flag mismatch")
    if data.get("pass_below_axis_target_detected") is not ("r54_pass_below_axis_target_detected" in issue_ids):
        raise ValueError("R54 R11 pass-below-target flag mismatch")
    if data.get("red_or_repair_without_blocker_detected") is not ("r54_red_or_repair_without_blocker_detected" in issue_ids):
        raise ValueError("R54 R11 red-or-repair-without-blocker flag mismatch")
    if ready:
        if data.get("r10_capture_ready_for_rating_normalization") is not True:
            raise ValueError("R54 R11 ready normalization requires ready R10 capture")
        if data.get("rating_row_count") != P7_R51_REQUIRED_CASE_COUNT or len(rows) != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 R11 ready normalization must carry 24 rating rows")
        if data.get("all_required_rating_rows_present") is not True or data.get("rating_case_ref_sets_match_review_capture") is not True:
            raise ValueError("R54 R11 ready normalization must be complete and case-set matched")
        if data.get("r54_11_rating_row_normalization_built") is not True:
            raise ValueError("R54 R11 ready built flag changed")
        if blockers:
            raise ValueError("R54 R11 ready normalization must not carry blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_R11_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_R11_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 R11 ready step lists changed")
        if data.get("next_required_step") != P7_R54_R11_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R11 ready next step changed")
    else:
        if data.get("actual_rating_rows_materialized_here") is not False or data.get("r54_11_rating_row_normalization_built") is not False:
            raise ValueError("R54 R11 blocked normalization must not claim built")
        if rows or data.get("rating_row_count") != 0:
            raise ValueError("R54 R11 blocked normalization must not expose partial rating rows")
        if not blockers or data.get("next_required_step") != P7_R54_R11_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R11 blocked normalization next step changed")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_rating_row_normalization")
    return True


# ---------------------------------------------------------------------------
# R54-12 / R54-13 blocker ingestion and question observation normalization
# ---------------------------------------------------------------------------

P7_R54_READFEEL_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.readfeel_execution_blocker_ingestion.bodyfree.v1"
)
P7_R54_READFEEL_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.readfeel_blocker_row.bodyfree.v1"
)
P7_R54_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.execution_blocker_row.bodyfree.v1"
)
P7_R54_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.question_need_observation_row.bodyfree.v1"
)
P7_R54_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.question_need_observation_row_normalization.bodyfree.v1"
)

P7_R54_R12_STEP_REF: Final = "R54-12_readfeel_blocker_execution_blocker_ingestion"
P7_R54_R13_STEP_REF: Final = "R54-13_question_need_observation_row_normalization"
P7_R54_R12_NEXT_REQUIRED_STEP_REF: Final = "R54-13_question_need_observation_row_normalization"
P7_R54_R12_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "resolve_R54-11_rating_row_normalization_before_R54-12_readfeel_blocker_execution_blocker_ingestion"
)
P7_R54_R13_NEXT_REQUIRED_STEP_REF: Final = "R54-14_rating_question_observation_consistency_guard"
P7_R54_R13_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "resolve_R54-12_readfeel_blocker_execution_blocker_ingestion_before_R54-13_question_need_observation_row_normalization"
)

P7_R54_FUTURE_STEPS_AFTER_R13: Final[tuple[str, ...]] = tuple(
    step for step in P7_R54_FUTURE_STEPS_AFTER_R11 if step not in {P7_R54_R12_STEP_REF, P7_R54_R13_STEP_REF}
)
P7_R54_R12_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_R11_IMPLEMENTED_STEPS, P7_R54_R12_STEP_REF)
P7_R54_R12_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_R13_STEP_REF, *P7_R54_FUTURE_STEPS_AFTER_R13)
P7_R54_R13_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_R12_IMPLEMENTED_STEPS, P7_R54_R13_STEP_REF)
P7_R54_R13_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_FUTURE_STEPS_AFTER_R13

P7_R54_READFEEL_BLOCKER_KIND_REFS: Final[tuple[str, ...]] = (
    "p5_product_readfeel_blocker",
    "p5_history_connection_readfeel_blocker",
)
P7_R54_EXECUTION_BLOCKER_KIND_REFS: Final[tuple[str, ...]] = (
    "review_execution_boundary_blocker",
    "local_only_safety_boundary_blocker",
    "purge_or_disposal_boundary_blocker",
)
P7_R54_BLOCKER_STATUS_REFS: Final[tuple[str, ...]] = ("open", "closed")
P7_R54_P8_MATERIAL_CANDIDATE_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = (
    "question_may_reduce_overread_risk",
    "plus_single_question_candidate_later",
    "premium_deep_dive_candidate_later",
)
P7_R54_NOT_QUESTION_REPAIR_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = (
    "not_question_emlis_readfeel_repair_required",
    "not_question_p5_surface_repair_required",
    "not_question_gate_boundary_required",
)
P7_R54_PLAN_CANDIDATE_FLAG_REFS: Final[tuple[str, ...]] = (
    "p8_design_material_candidate",
    "question_may_reduce_overread_risk",
    "plus_single_question_candidate_later",
    "premium_deep_dive_candidate_later",
    "p5_repair_return_not_p8_material",
    "insufficient_material_not_p8_material",
    "no_question_needed",
)

P7_R54_READFEEL_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "blind_case_id",
    "case_ref_id",
    "packet_ref_id",
    "case_family_ref",
    "case_role_ref",
    "subscription_boundary_ref",
    "blocker_id",
    "blocker_kind_ref",
    "blocker_status_ref",
    "source_rating_row_ref",
    "raw_input_included",
    "returned_surface_included",
    "comment_text_included",
    "history_body_included",
    "reviewer_free_text_included",
    "question_text_included",
    "draft_question_text_included",
    "local_absolute_path_included",
    "body_content_hash_included",
    "packet_content_hash_included",
    "machine_auto_score_used",
    "machine_metrics_used_for_readfeel",
    "body_free",
)
P7_R54_EXECUTION_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "blind_case_id",
    "case_ref_id",
    "packet_ref_id",
    "case_family_ref",
    "case_role_ref",
    "subscription_boundary_ref",
    "execution_blocker_id",
    "execution_blocker_kind_ref",
    "execution_blocker_status_ref",
    "source_rating_row_ref",
    "raw_input_included",
    "returned_surface_included",
    "comment_text_included",
    "history_body_included",
    "reviewer_free_text_included",
    "question_text_included",
    "draft_question_text_included",
    "local_absolute_path_included",
    "body_content_hash_included",
    "packet_content_hash_included",
    "machine_auto_score_used",
    "machine_metrics_used_for_readfeel",
    "body_free",
)
P7_R54_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "blind_case_id",
    "case_ref_id",
    "packet_ref_id",
    "case_family_ref",
    "case_role_ref",
    "subscription_boundary_ref",
    "question_need_primary_class",
    "ambiguity_kind_refs",
    "one_question_fit_ref",
    "repair_required_refs",
    "plan_candidate_flags",
    "p8_material_candidate_allowed",
    "not_question_repair_required",
    "insufficient_material_execution_blocker",
    "raw_input_included",
    "returned_surface_included",
    "comment_text_included",
    "history_body_included",
    "reviewer_free_text_included",
    "question_text_included",
    "draft_question_text_included",
    "local_absolute_path_included",
    "body_content_hash_included",
    "packet_content_hash_included",
    "machine_auto_score_used",
    "machine_metrics_used_for_readfeel",
    "body_free",
)

P7_R54_R12_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_R11_FALSE_KEY_REFS
    if key not in {"actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here"}
)
P7_R54_R13_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_R12_FALSE_KEY_REFS
    if key != "actual_question_need_observation_rows_materialized_here"
)

P7_R54_READFEEL_EXECUTION_BLOCKER_INGESTION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "r11_rating_row_normalization_schema_version", "r11_rating_row_normalization_material_ref", "r11_rating_row_normalizer_status", "r11_rating_rows_ready_for_blocker_ingestion",
    "current_received_snapshot_refs", "current_received_snapshot_ref_count", "r53_source_snapshot_refs", "r53_source_snapshot_ref_count", "r53_refs_are_current_received_refs",
    "review_session_status", "blocker_ingestion_status", "blocker_ingestion_reason_refs", "required_case_count", "rating_row_count",
    "readfeel_blocker_row_schema_version", "execution_blocker_row_schema_version", "readfeel_blocker_row_required_field_refs", "execution_blocker_row_required_field_refs",
    "readfeel_blocker_id_refs", "execution_blocker_id_refs", "readfeel_blocker_kind_refs", "execution_blocker_kind_refs", "blocker_status_refs",
    "readfeel_blocker_rows", "execution_blocker_rows", "rating_blind_case_ids", "rating_case_ref_ids", "rating_packet_ref_ids", "readfeel_blocker_row_count", "execution_blocker_row_count", "open_readfeel_blocker_count", "open_execution_blocker_count",
    "readfeel_blocker_counts", "execution_blocker_counts", "readfeel_and_execution_blockers_separated", "execution_blockers_do_not_assign_readfeel_verdict", "execution_blocker_cases_do_not_create_rating_rows",
    "execution_blocker_open_blocks_p5_confirmed_candidate", "p5_confirmed_candidate_blocked_by_open_execution_blockers", "rating_missing_maps_to_execution_blocker_not_red", "local_root_missing_maps_to_execution_blocker_not_red", "disposal_failed_maps_to_execution_blocker_not_red", "body_free_leak_maps_to_execution_blocker_not_red",
    "readfeel_blocker_row_builder_ready", "execution_blocker_row_builder_ready",
    "body_full_packet_generated_here", "actual_body_full_packet_generated_here", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_disposal_receipt_materialized_here", "p5_actual_review_still_not_run_by_helper",
    "r54_0_scope_current_received_snapshot_refrozen", "r54_1_r53_source_delta_current_snapshot_override_adopted", "r54_2_validation_evidence_intake_done", "r54_3_local_only_actual_review_preflight_built", "r54_4_actual_review_session_envelope_built", "r54_5_24_case_manifest_freeze_built", "r54_6_local_only_body_full_packet_generation_request_built", "r54_7_packet_completeness_export_denylist_scan_built", "r54_8_reviewer_instruction_rating_form_freeze_built", "r54_9_actual_human_review_operation_state_capture_built", "r54_10_sanitized_actual_review_result_capture_built", "r54_11_rating_row_normalization_built", "r54_12_readfeel_blocker_execution_blocker_ingestion_built",
    "execution_blocker_ids", "open_execution_blocker_ids", "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract", "r54_public_no_touch_contract", "body_free_markers", "body_free",
    *P7_R54_R12_FALSE_KEY_REFS,
    "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here",
    "validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here",
)
P7_R54_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "r12_blocker_ingestion_schema_version", "r12_blocker_ingestion_material_ref", "r12_blocker_ingestion_status", "r12_ready_for_question_need_observation_row_normalization",
    "r10_sanitized_capture_schema_version", "r10_sanitized_capture_material_ref", "r10_capture_status", "r10_capture_ready_for_question_observation",
    "current_received_snapshot_refs", "current_received_snapshot_ref_count", "r53_source_snapshot_refs", "r53_source_snapshot_ref_count", "r53_refs_are_current_received_refs",
    "review_session_status", "question_observation_normalizer_status", "question_observation_normalizer_reason_refs", "required_case_count", "review_result_capture_row_count", "rating_row_count", "question_observation_row_count", "question_need_observation_rows",
    "question_need_observation_row_schema_version", "question_need_observation_row_required_field_refs", "question_need_observation_row_forbidden_field_refs", "question_need_primary_class_refs", "ambiguity_kind_refs", "one_question_fit_refs", "plan_candidate_flag_refs", "repair_required_ref_refs", "question_need_observation_stage_ref", "review_kind",
    "question_need_observation_rows_must_be_bodyfree", "question_text_absent_for_all_rows", "draft_question_text_absent_for_all_rows", "reviewer_free_text_absent_for_all_rows", "raw_input_absent_for_all_rows", "returned_surface_absent_for_all_rows", "local_path_absent_for_all_rows", "body_hash_absent_for_all_rows",
    "question_text_included_allowed", "draft_question_text_included_allowed", "reviewer_free_text_included_allowed", "raw_input_allowed", "returned_surface_allowed", "local_path_allowed", "body_hash_allowed",
    "p8_question_implementation_spec_finalized_here", "question_trigger_logic_implemented", "question_trigger_logic_implemented_here", "api_db_rn_response_key_changed_here", "question_api_implemented", "question_db_schema_implemented", "question_rn_ui_implemented", "question_response_key_implemented", "question_storage_schema_implemented", "question_answer_persistence_implemented", "question_plan_guard_implemented",
    "row_case_ref_sets_match_review_capture", "row_case_ref_sets_match_rating_rows", "all_required_question_need_observation_rows_present", "primary_class_ambiguity_one_question_fit_are_canonical_refs", "not_question_repair_rows_misclassified_as_p8_material", "p5_weakness_not_hidden_by_question_candidates_here", "question_text_or_draft_text_saved_here",
    "question_need_primary_class_counts", "ambiguity_kind_counts", "one_question_fit_counts", "repair_required_counts", "plan_candidate_flag_counts", "p8_material_candidate_row_count", "not_question_repair_required_count", "insufficient_material_execution_blocker_count",
    "body_full_packet_generated_here", "actual_body_full_packet_generated_here", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_question_need_observation_summary_materialized_here", "actual_disposal_receipt_materialized_here", "p5_actual_review_still_not_run_by_helper",
    "r54_0_scope_current_received_snapshot_refrozen", "r54_1_r53_source_delta_current_snapshot_override_adopted", "r54_2_validation_evidence_intake_done", "r54_3_local_only_actual_review_preflight_built", "r54_4_actual_review_session_envelope_built", "r54_5_24_case_manifest_freeze_built", "r54_6_local_only_body_full_packet_generation_request_built", "r54_7_packet_completeness_export_denylist_scan_built", "r54_8_reviewer_instruction_rating_form_freeze_built", "r54_9_actual_human_review_operation_state_capture_built", "r54_10_sanitized_actual_review_result_capture_built", "r54_11_rating_row_normalization_built", "r54_12_readfeel_blocker_execution_blocker_ingestion_built", "r54_13_question_need_observation_row_normalization_built",
    "execution_blocker_ids", "open_execution_blocker_ids", "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract", "r54_public_no_touch_contract", "body_free_markers", "body_free",
    *P7_R54_R13_FALSE_KEY_REFS,
    "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here",
    "validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here",
)


def _r54_count_ids(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        for ref in _allowed_count_values_r54(safe_mapping(row).get(key)):
            counts[ref] = counts.get(ref, 0) + 1
    return counts


def _allowed_count_values_r54(value: Any) -> list[str]:
    return dedupe_identifiers(_safe_sequence_r54(value), limit=80, max_length=140)


def _r54_single_id_counts(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for source_row in rows:
        ref = clean_identifier(safe_mapping(source_row).get(key), default="", max_length=140)
        if ref:
            counts[ref] = counts.get(ref, 0) + 1
    return counts


def build_p7_r54_readfeel_blocker_row_bodyfree(*, rating_row: Mapping[str, Any], blocker_id: Any, blocker_status_ref: Any = "open") -> dict[str, Any]:
    row = safe_mapping(rating_row)
    assert_p7_r54_rating_row_bodyfree_contract(row)
    blocker_ref = clean_identifier(blocker_id, default="", max_length=140)
    if blocker_ref not in P7_R48_READFEEL_BLOCKER_ID_REFS:
        raise ValueError("R54 R12 readfeel blocker row must use canonical readfeel blocker id")
    status_ref = clean_identifier(blocker_status_ref, default="open", max_length=40)
    if status_ref not in P7_R54_BLOCKER_STATUS_REFS:
        raise ValueError("R54 R12 readfeel blocker row must use canonical blocker status")
    out = {
        "schema_version": P7_R54_READFEEL_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "review_session_id": clean_identifier(row.get("review_session_id"), default=P7_R54_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "blind_case_id": clean_identifier(row.get("blind_case_id"), default="blind_case", max_length=160),
        "case_ref_id": clean_identifier(row.get("case_ref_id"), default="case_ref", max_length=160),
        "packet_ref_id": clean_identifier(row.get("packet_ref_id"), default="packet_ref", max_length=160),
        "case_family_ref": clean_identifier(row.get("case_family_ref"), default="history_line_eligible_input", max_length=160),
        "case_role_ref": clean_identifier(row.get("case_role_ref"), default="positive_history_line", max_length=160),
        "subscription_boundary_ref": clean_identifier(row.get("subscription_boundary_ref"), default="plus_or_premium_history_allowed", max_length=160),
        "blocker_id": blocker_ref,
        "blocker_kind_ref": "p5_product_readfeel_blocker",
        "blocker_status_ref": status_ref,
        "source_rating_row_ref": clean_identifier(row.get("blind_case_id"), default="blind_case", max_length=160),
        "raw_input_included": False,
        "returned_surface_included": False,
        "comment_text_included": False,
        "history_body_included": False,
        "reviewer_free_text_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_absolute_path_included": False,
        "body_content_hash_included": False,
        "packet_content_hash_included": False,
        "machine_auto_score_used": False,
        "machine_metrics_used_for_readfeel": False,
        "body_free": True,
    }
    assert_p7_r54_readfeel_blocker_row_bodyfree_contract(out)
    return out


def assert_p7_r54_readfeel_blocker_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R54_READFEEL_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS, source="p7_r54_readfeel_blocker_row")
    if data.get("schema_version") != P7_R54_READFEEL_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R54 R12 readfeel blocker row schema changed")
    if data.get("blocker_id") not in P7_R48_READFEEL_BLOCKER_ID_REFS:
        raise ValueError("R54 R12 readfeel blocker row has non-canonical blocker id")
    if data.get("blocker_kind_ref") not in P7_R54_READFEEL_BLOCKER_KIND_REFS:
        raise ValueError("R54 R12 readfeel blocker row kind changed")
    if data.get("blocker_status_ref") not in P7_R54_BLOCKER_STATUS_REFS:
        raise ValueError("R54 R12 readfeel blocker row status changed")
    for false_key in (
        "raw_input_included", "returned_surface_included", "comment_text_included", "history_body_included", "reviewer_free_text_included", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included", "machine_auto_score_used", "machine_metrics_used_for_readfeel",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 R12 readfeel blocker row must keep {false_key}=False")
    if data.get("body_free") is not True:
        raise ValueError("R54 R12 readfeel blocker row must be body-free")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_readfeel_blocker_row")
    return True


def build_p7_r54_execution_blocker_row_bodyfree(*, rating_row: Mapping[str, Any], execution_blocker_id: Any, execution_blocker_status_ref: Any = "open") -> dict[str, Any]:
    row = safe_mapping(rating_row)
    assert_p7_r54_rating_row_bodyfree_contract(row)
    blocker_ref = clean_identifier(execution_blocker_id, default="", max_length=140)
    if blocker_ref not in P7_R54_R10_R11_ALLOWED_EXECUTION_BLOCKER_ID_REFS:
        raise ValueError("R54 R12 execution blocker row must use canonical execution blocker id")
    status_ref = clean_identifier(execution_blocker_status_ref, default="open", max_length=40)
    if status_ref not in P7_R54_BLOCKER_STATUS_REFS:
        raise ValueError("R54 R12 execution blocker row must use canonical blocker status")
    out = {
        "schema_version": P7_R54_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "review_session_id": clean_identifier(row.get("review_session_id"), default=P7_R54_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "blind_case_id": clean_identifier(row.get("blind_case_id"), default="blind_case", max_length=160),
        "case_ref_id": clean_identifier(row.get("case_ref_id"), default="case_ref", max_length=160),
        "packet_ref_id": clean_identifier(row.get("packet_ref_id"), default="packet_ref", max_length=160),
        "case_family_ref": clean_identifier(row.get("case_family_ref"), default="history_line_eligible_input", max_length=160),
        "case_role_ref": clean_identifier(row.get("case_role_ref"), default="positive_history_line", max_length=160),
        "subscription_boundary_ref": clean_identifier(row.get("subscription_boundary_ref"), default="plus_or_premium_history_allowed", max_length=160),
        "execution_blocker_id": blocker_ref,
        "execution_blocker_kind_ref": "review_execution_boundary_blocker",
        "execution_blocker_status_ref": status_ref,
        "source_rating_row_ref": clean_identifier(row.get("blind_case_id"), default="blind_case", max_length=160),
        "raw_input_included": False,
        "returned_surface_included": False,
        "comment_text_included": False,
        "history_body_included": False,
        "reviewer_free_text_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_absolute_path_included": False,
        "body_content_hash_included": False,
        "packet_content_hash_included": False,
        "machine_auto_score_used": False,
        "machine_metrics_used_for_readfeel": False,
        "body_free": True,
    }
    assert_p7_r54_execution_blocker_row_bodyfree_contract(out)
    return out


def assert_p7_r54_execution_blocker_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R54_EXECUTION_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS, source="p7_r54_execution_blocker_row")
    if data.get("schema_version") != P7_R54_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R54 R12 execution blocker row schema changed")
    if data.get("execution_blocker_id") not in P7_R54_R10_R11_ALLOWED_EXECUTION_BLOCKER_ID_REFS:
        raise ValueError("R54 R12 execution blocker row has non-canonical blocker id")
    if data.get("execution_blocker_kind_ref") not in P7_R54_EXECUTION_BLOCKER_KIND_REFS:
        raise ValueError("R54 R12 execution blocker row kind changed")
    if data.get("execution_blocker_status_ref") not in P7_R54_BLOCKER_STATUS_REFS:
        raise ValueError("R54 R12 execution blocker row status changed")
    for false_key in (
        "raw_input_included", "returned_surface_included", "comment_text_included", "history_body_included", "reviewer_free_text_included", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included", "machine_auto_score_used", "machine_metrics_used_for_readfeel",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 R12 execution blocker row must keep {false_key}=False")
    if data.get("body_free") is not True:
        raise ValueError("R54 R12 execution blocker row must be body-free")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_execution_blocker_row")
    return True


def _r54_blocker_rows_from_rating_rows(rating_rows: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    readfeel_rows: list[dict[str, Any]] = []
    execution_rows: list[dict[str, Any]] = []
    for source_row in rating_rows:
        row = safe_mapping(source_row)
        assert_p7_r54_rating_row_bodyfree_contract(row)
        for blocker_id in _allowed_identifier_sequence_r54(row.get("readfeel_blocker_ids"), source="p7_r54_r12.rating_row.readfeel_blocker_ids", allowed_refs=P7_R48_READFEEL_BLOCKER_ID_REFS, limit=12):
            readfeel_rows.append(build_p7_r54_readfeel_blocker_row_bodyfree(rating_row=row, blocker_id=blocker_id))
        for execution_blocker_id in _allowed_identifier_sequence_r54(row.get("execution_blocker_ids"), source="p7_r54_r12.rating_row.execution_blocker_ids", allowed_refs=P7_R54_R10_R11_ALLOWED_EXECUTION_BLOCKER_ID_REFS, limit=12):
            execution_rows.append(build_p7_r54_execution_blocker_row_bodyfree(rating_row=row, execution_blocker_id=execution_blocker_id))
    return readfeel_rows, execution_rows


def build_p7_r54_readfeel_blocker_execution_blocker_ingestion_bodyfree(
    *,
    rating_row_normalization: Mapping[str, Any] | None = None,
    r11_rating_row_normalization: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_readfeel_blocker_execution_blocker_ingestion_bodyfree",
) -> dict[str, Any]:
    if rating_row_normalization is not None and r11_rating_row_normalization is not None:
        raise ValueError("provide only one R54-11 rating row normalization value")
    r11 = safe_mapping(rating_row_normalization) if rating_row_normalization is not None else safe_mapping(r11_rating_row_normalization) if r11_rating_row_normalization is not None else build_p7_r54_rating_row_normalization_bodyfree()
    assert_p7_r54_rating_row_normalization_bodyfree_contract(r11)
    r11_ready = r11.get("rating_row_normalizer_status") == "READY_FOR_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION" and not r11.get("execution_blocker_ids")
    blockers = [] if r11_ready else ["r54_rating_row_normalization_not_ready_for_blocker_ingestion"]
    rating_rows = [safe_mapping(row) for row in (r11.get("rating_rows") or [])] if r11_ready else []
    readfeel_rows, execution_rows = _r54_blocker_rows_from_rating_rows(rating_rows) if r11_ready else ([], [])
    open_readfeel_count = sum(1 for row in readfeel_rows if row.get("blocker_status_ref") == "open")
    open_execution_count = sum(1 for row in execution_rows if row.get("execution_blocker_status_ref") == "open")
    ready = bool(r11_ready)
    reason_refs = ["r54_readfeel_execution_blockers_separated_bodyfree"] if ready else blockers
    material = {
        "schema_version": P7_R54_READFEEL_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_STEP,
        "scope": P7_R54_SCOPE,
        "policy_kind": P7_R54_POLICY_KIND,
        "policy_section": P7_R54_R12_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_readfeel_blocker_execution_blocker_ingestion_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r11.get("review_session_id"), default=P7_R54_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r11_rating_row_normalization_schema_version": P7_R54_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        "r11_rating_row_normalization_material_ref": clean_identifier(r11.get("material_id"), default="p7_r54_rating_row_normalization_bodyfree", max_length=180),
        "r11_rating_row_normalizer_status": clean_identifier(r11.get("rating_row_normalizer_status"), default="BLOCKED_BY_R54_10_SANITIZED_CAPTURE", max_length=140),
        "r11_rating_rows_ready_for_blocker_ingestion": bool(r11_ready),
        "current_received_snapshot_refs": dict(P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "r53_source_snapshot_refs": _r53_source_snapshot_refs(None),
        "r53_source_snapshot_ref_count": len(_r53_source_snapshot_refs(None)),
        "r53_refs_are_current_received_refs": False,
        "review_session_status": "R54_READFEEL_EXECUTION_BLOCKERS_INGESTED_BODYFREE" if ready else "PRECHECK_BLOCKED",
        "blocker_ingestion_status": "READY_FOR_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION" if ready else "BLOCKED_BY_R54_11_RATING_ROW_NORMALIZATION",
        "blocker_ingestion_reason_refs": reason_refs,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "rating_row_count": len(rating_rows),
        "readfeel_blocker_row_schema_version": P7_R54_READFEEL_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "execution_blocker_row_schema_version": P7_R54_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "readfeel_blocker_row_required_field_refs": list(P7_R54_READFEEL_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS),
        "execution_blocker_row_required_field_refs": list(P7_R54_EXECUTION_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS),
        "readfeel_blocker_id_refs": list(P7_R48_READFEEL_BLOCKER_ID_REFS),
        "execution_blocker_id_refs": list(P7_R54_R10_R11_ALLOWED_EXECUTION_BLOCKER_ID_REFS),
        "readfeel_blocker_kind_refs": list(P7_R54_READFEEL_BLOCKER_KIND_REFS),
        "execution_blocker_kind_refs": list(P7_R54_EXECUTION_BLOCKER_KIND_REFS),
        "blocker_status_refs": list(P7_R54_BLOCKER_STATUS_REFS),
        "readfeel_blocker_rows": readfeel_rows,
        "execution_blocker_rows": execution_rows,
        "rating_blind_case_ids": _r54_case_refs(rating_rows, "blind_case_id"),
        "rating_case_ref_ids": _r54_case_refs(rating_rows, "case_ref_id"),
        "rating_packet_ref_ids": _r54_case_refs(rating_rows, "packet_ref_id"),
        "readfeel_blocker_row_count": len(readfeel_rows),
        "execution_blocker_row_count": len(execution_rows),
        "open_readfeel_blocker_count": open_readfeel_count,
        "open_execution_blocker_count": open_execution_count,
        "readfeel_blocker_counts": _r54_single_id_counts(readfeel_rows, "blocker_id"),
        "execution_blocker_counts": _r54_single_id_counts(execution_rows, "execution_blocker_id"),
        "readfeel_and_execution_blockers_separated": True,
        "execution_blockers_do_not_assign_readfeel_verdict": True,
        "execution_blocker_cases_do_not_create_rating_rows": True,
        "execution_blocker_open_blocks_p5_confirmed_candidate": True,
        "p5_confirmed_candidate_blocked_by_open_execution_blockers": bool(open_execution_count > 0),
        "rating_missing_maps_to_execution_blocker_not_red": True,
        "local_root_missing_maps_to_execution_blocker_not_red": True,
        "disposal_failed_maps_to_execution_blocker_not_red": True,
        "body_free_leak_maps_to_execution_blocker_not_red": True,
        "readfeel_blocker_row_builder_ready": ready,
        "execution_blocker_row_builder_ready": ready,
        **_false_flags_except({"validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here"}),
        "body_full_packet_generated_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "actual_rating_rows_materialized_here": bool(ready and r11.get("actual_rating_rows_materialized_here") is True),
        "actual_blocker_rows_materialized_here": ready,
        "actual_execution_blocker_rows_materialized_here": ready,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "p5_actual_review_still_not_run_by_helper": True,
        "r54_0_scope_current_received_snapshot_refrozen": True,
        "r54_1_r53_source_delta_current_snapshot_override_adopted": True,
        "r54_2_validation_evidence_intake_done": r11.get("r54_2_validation_evidence_intake_done") is True,
        "r54_3_local_only_actual_review_preflight_built": r11.get("r54_3_local_only_actual_review_preflight_built") is True,
        "r54_4_actual_review_session_envelope_built": r11.get("r54_4_actual_review_session_envelope_built") is True,
        "r54_5_24_case_manifest_freeze_built": r11.get("r54_5_24_case_manifest_freeze_built") is True,
        "r54_6_local_only_body_full_packet_generation_request_built": r11.get("r54_6_local_only_body_full_packet_generation_request_built") is True,
        "r54_7_packet_completeness_export_denylist_scan_built": r11.get("r54_7_packet_completeness_export_denylist_scan_built") is True,
        "r54_8_reviewer_instruction_rating_form_freeze_built": r11.get("r54_8_reviewer_instruction_rating_form_freeze_built") is True,
        "r54_9_actual_human_review_operation_state_capture_built": r11.get("r54_9_actual_human_review_operation_state_capture_built") is True,
        "r54_10_sanitized_actual_review_result_capture_built": r11.get("r54_10_sanitized_actual_review_result_capture_built") is True,
        "r54_11_rating_row_normalization_built": r11.get("r54_11_rating_row_normalization_built") is True,
        "r54_12_readfeel_blocker_execution_blocker_ingestion_built": ready,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "implemented_steps": list(P7_R54_R12_IMPLEMENTED_STEPS if ready else P7_R54_R11_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_R12_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_R11_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R54_R12_NEXT_REQUIRED_STEP_REF if ready else P7_R54_R12_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "next_required_step": P7_R54_R12_NEXT_REQUIRED_STEP_REF if ready else P7_R54_R12_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "validation_evidence_intake_done_here": r11.get("validation_evidence_intake_done_here") is True,
        "local_root_preflight_passed_here": r11.get("local_root_preflight_passed_here") is True,
        "explicit_allow_present_here": r11.get("explicit_allow_present_here") is True,
        "purge_plan_verified_here": r11.get("purge_plan_verified_here") is True,
    }
    assert_p7_r54_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(material)
    return material


def assert_p7_r54_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_READFEEL_EXECUTION_BLOCKER_INGESTION_REQUIRED_FIELD_REFS, source="p7_r54_readfeel_execution_blocker_ingestion")
    ready = data.get("blocker_ingestion_status") == "READY_FOR_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION"
    _assert_body_free_common_with_false_keys(data, schema_version=P7_R54_READFEEL_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION, source="p7_r54_readfeel_execution_blocker_ingestion", false_key_refs=P7_R54_R12_FALSE_KEY_REFS)
    _assert_current_refs(data, source="p7_r54_readfeel_execution_blocker_ingestion")
    if data.get("policy_section") != P7_R54_R12_STEP_REF:
        raise ValueError("R54 R12 policy section changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=80, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 R12 open blockers must match materialization blockers")
    for row in data.get("readfeel_blocker_rows") or []:
        assert_p7_r54_readfeel_blocker_row_bodyfree_contract(safe_mapping(row))
    for row in data.get("execution_blocker_rows") or []:
        assert_p7_r54_execution_blocker_row_bodyfree_contract(safe_mapping(row))
    if data.get("readfeel_blocker_row_count") != len(data.get("readfeel_blocker_rows") or []):
        raise ValueError("R54 R12 readfeel row count mismatch")
    if data.get("execution_blocker_row_count") != len(data.get("execution_blocker_rows") or []):
        raise ValueError("R54 R12 execution row count mismatch")
    if data.get("open_readfeel_blocker_count") != sum(1 for row in data.get("readfeel_blocker_rows") or [] if safe_mapping(row).get("blocker_status_ref") == "open"):
        raise ValueError("R54 R12 open readfeel blocker count mismatch")
    if data.get("open_execution_blocker_count") != sum(1 for row in data.get("execution_blocker_rows") or [] if safe_mapping(row).get("execution_blocker_status_ref") == "open"):
        raise ValueError("R54 R12 open execution blocker count mismatch")
    for true_key in (
        "readfeel_and_execution_blockers_separated", "execution_blockers_do_not_assign_readfeel_verdict", "execution_blocker_cases_do_not_create_rating_rows", "execution_blocker_open_blocks_p5_confirmed_candidate", "rating_missing_maps_to_execution_blocker_not_red", "local_root_missing_maps_to_execution_blocker_not_red", "disposal_failed_maps_to_execution_blocker_not_red", "body_free_leak_maps_to_execution_blocker_not_red",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R54 R12 must keep {true_key}=True")
    if data.get("p5_confirmed_candidate_blocked_by_open_execution_blockers") is not (data.get("open_execution_blocker_count") > 0):
        raise ValueError("R54 R12 P5-confirmed blocker flag must reflect open execution blockers")
    if data.get("actual_human_review_run_here") is not False or data.get("actual_manual_review_run_here") is not False:
        raise ValueError("R54 R12 helper must not claim it ran the human review")
    if data.get("actual_question_need_observation_rows_materialized_here") is not False:
        raise ValueError("R54 R12 must not materialize question rows")
    if ready:
        if data.get("r11_rating_rows_ready_for_blocker_ingestion") is not True:
            raise ValueError("R54 R12 ready requires ready R11 rating rows")
        if data.get("rating_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 R12 ready ingestion requires 24 rating rows")
        if len(data.get("rating_blind_case_ids") or []) != P7_R51_REQUIRED_CASE_COUNT or len(data.get("rating_case_ref_ids") or []) != P7_R51_REQUIRED_CASE_COUNT or len(data.get("rating_packet_ref_ids") or []) != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 R12 ready ingestion must preserve 24 rating case refs")
        if data.get("actual_rating_rows_materialized_here") is not True or data.get("actual_blocker_rows_materialized_here") is not True or data.get("actual_execution_blocker_rows_materialized_here") is not True:
            raise ValueError("R54 R12 ready ingestion must materialize body-free blocker rows and preserve rating rows")
        if blockers:
            raise ValueError("R54 R12 ready ingestion must not carry materialization blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_R12_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_R12_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 R12 ready step lists changed")
        if data.get("next_required_step") != P7_R54_R12_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R12 ready next step changed")
    else:
        if data.get("actual_blocker_rows_materialized_here") is not False or data.get("actual_execution_blocker_rows_materialized_here") is not False:
            raise ValueError("R54 R12 blocked ingestion must not materialize blocker rows")
        if data.get("r54_12_readfeel_blocker_execution_blocker_ingestion_built") is not False:
            raise ValueError("R54 R12 blocked ingestion must not claim built")
        if not blockers or data.get("next_required_step") != P7_R54_R12_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R12 blocked next step changed")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_readfeel_execution_blocker_ingestion")
    return True


def _r54_question_plan_flags(primary_class: str, repair_required_refs: Sequence[str]) -> tuple[list[str], bool, bool, bool]:
    repair_set = set(repair_required_refs)
    not_question_repair = primary_class in P7_R54_NOT_QUESTION_REPAIR_PRIMARY_CLASS_REFS
    insufficient = primary_class == "insufficient_material_execution_blocker"
    p8_allowed = primary_class in P7_R54_P8_MATERIAL_CANDIDATE_PRIMARY_CLASS_REFS and not not_question_repair and not insufficient and not (repair_set - {"no_repair_required"})
    flags: list[str] = []
    if p8_allowed:
        flags.append("p8_design_material_candidate")
        flags.append(primary_class)
    elif not_question_repair or (repair_set - {"no_repair_required"}):
        flags.append("p5_repair_return_not_p8_material")
    elif insufficient:
        flags.append("insufficient_material_not_p8_material")
    else:
        flags.append("no_question_needed")
    return flags, p8_allowed, not_question_repair, insufficient


def build_p7_r54_question_need_observation_row_bodyfree(*, sanitized_review_result_row: Mapping[str, Any]) -> dict[str, Any]:
    source = safe_mapping(sanitized_review_result_row)
    assert_p7_r54_sanitized_review_result_row_bodyfree_contract(source)
    primary_class = clean_identifier(source.get("question_need_primary_class"), default="", max_length=140)
    if primary_class not in P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS:
        raise ValueError("R54 R13 question observation row primary class must be canonical")
    ambiguity_refs = _allowed_identifier_sequence_r54(source.get("ambiguity_kind_refs"), source="p7_r54_question_observation_row.ambiguity_kind_refs", allowed_refs=P7_R49_AMBIGUITY_KIND_REFS, limit=12)
    one_question_fit = clean_identifier(source.get("one_question_fit_ref"), default="", max_length=140)
    if one_question_fit not in P7_R49_ONE_QUESTION_FIT_REFS:
        raise ValueError("R54 R13 question observation row one-question fit must be canonical")
    repair_refs = _allowed_identifier_sequence_r54(source.get("repair_required_refs"), source="p7_r54_question_observation_row.repair_required_refs", allowed_refs=P7_R49_REPAIR_REQUIRED_REF_REFS, limit=12)
    plan_flags, p8_allowed, not_question_repair, insufficient = _r54_question_plan_flags(primary_class, repair_refs)
    out = {
        "schema_version": P7_R54_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION,
        "review_session_id": clean_identifier(source.get("review_session_id"), default=P7_R54_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "blind_case_id": clean_identifier(source.get("blind_case_id"), default="blind_case", max_length=160),
        "case_ref_id": clean_identifier(source.get("case_ref_id"), default="case_ref", max_length=160),
        "packet_ref_id": clean_identifier(source.get("packet_ref_id"), default="packet_ref", max_length=160),
        "case_family_ref": clean_identifier(source.get("case_family_ref"), default="history_line_eligible_input", max_length=160),
        "case_role_ref": clean_identifier(source.get("case_role_ref"), default="positive_history_line", max_length=160),
        "subscription_boundary_ref": clean_identifier(source.get("subscription_boundary_ref"), default="plus_or_premium_history_allowed", max_length=160),
        "question_need_primary_class": primary_class,
        "ambiguity_kind_refs": ambiguity_refs,
        "one_question_fit_ref": one_question_fit,
        "repair_required_refs": repair_refs,
        "plan_candidate_flags": plan_flags,
        "p8_material_candidate_allowed": p8_allowed,
        "not_question_repair_required": not_question_repair,
        "insufficient_material_execution_blocker": insufficient,
        "raw_input_included": False,
        "returned_surface_included": False,
        "comment_text_included": False,
        "history_body_included": False,
        "reviewer_free_text_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_absolute_path_included": False,
        "body_content_hash_included": False,
        "packet_content_hash_included": False,
        "machine_auto_score_used": False,
        "machine_metrics_used_for_readfeel": False,
        "body_free": True,
    }
    assert_p7_r54_question_need_observation_row_bodyfree_contract(out)
    return out


def assert_p7_r54_question_need_observation_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R54_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_REQUIRED_FIELD_REFS, source="p7_r54_question_need_observation_row")
    if data.get("schema_version") != P7_R54_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R54 R13 question observation row schema changed")
    primary_class = clean_identifier(data.get("question_need_primary_class"), default="", max_length=140)
    if primary_class not in P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS:
        raise ValueError("R54 R13 question observation row primary class changed")
    _allowed_identifier_sequence_r54(data.get("ambiguity_kind_refs"), source="p7_r54_question_need_observation_row.ambiguity_kind_refs", allowed_refs=P7_R49_AMBIGUITY_KIND_REFS, limit=12)
    if data.get("one_question_fit_ref") not in P7_R49_ONE_QUESTION_FIT_REFS:
        raise ValueError("R54 R13 question observation row fit ref changed")
    repair_refs = _allowed_identifier_sequence_r54(data.get("repair_required_refs"), source="p7_r54_question_need_observation_row.repair_required_refs", allowed_refs=P7_R49_REPAIR_REQUIRED_REF_REFS, limit=12)
    flags = _allowed_identifier_sequence_r54(data.get("plan_candidate_flags"), source="p7_r54_question_need_observation_row.plan_candidate_flags", allowed_refs=P7_R54_PLAN_CANDIDATE_FLAG_REFS, limit=12)
    should_p8 = primary_class in P7_R54_P8_MATERIAL_CANDIDATE_PRIMARY_CLASS_REFS and not (set(repair_refs) - {"no_repair_required"})
    if data.get("p8_material_candidate_allowed") is not should_p8:
        raise ValueError("R54 R13 question observation row P8 material flag misclassified")
    if primary_class in P7_R54_NOT_QUESTION_REPAIR_PRIMARY_CLASS_REFS and data.get("p8_material_candidate_allowed") is True:
        raise ValueError("R54 R13 not-question repair row must not become P8 material")
    if data.get("p8_material_candidate_allowed") and "p8_design_material_candidate" not in flags:
        raise ValueError("R54 R13 P8 material row must carry candidate flag")
    for false_key in (
        "raw_input_included", "returned_surface_included", "comment_text_included", "history_body_included", "reviewer_free_text_included", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included", "machine_auto_score_used", "machine_metrics_used_for_readfeel",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 R13 question observation row must keep {false_key}=False")
    if data.get("body_free") is not True:
        raise ValueError("R54 R13 question observation row must be body-free")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_question_need_observation_row")
    return True


def _r54_question_rows_from_capture(capture: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [build_p7_r54_question_need_observation_row_bodyfree(sanitized_review_result_row=safe_mapping(row)) for row in (capture.get("sanitized_review_result_rows") or [])]


def build_p7_r54_question_need_observation_row_normalization_bodyfree(
    *,
    readfeel_blocker_execution_blocker_ingestion: Mapping[str, Any] | None = None,
    r12_readfeel_blocker_execution_blocker_ingestion: Mapping[str, Any] | None = None,
    sanitized_actual_review_result_capture: Mapping[str, Any] | None = None,
    r10_sanitized_actual_review_result_capture: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_question_need_observation_row_normalization_bodyfree",
) -> dict[str, Any]:
    if readfeel_blocker_execution_blocker_ingestion is not None and r12_readfeel_blocker_execution_blocker_ingestion is not None:
        raise ValueError("provide only one R54-12 blocker ingestion value")
    if sanitized_actual_review_result_capture is not None and r10_sanitized_actual_review_result_capture is not None:
        raise ValueError("provide only one R54-10 sanitized capture value")
    r12 = safe_mapping(readfeel_blocker_execution_blocker_ingestion) if readfeel_blocker_execution_blocker_ingestion is not None else safe_mapping(r12_readfeel_blocker_execution_blocker_ingestion) if r12_readfeel_blocker_execution_blocker_ingestion is not None else build_p7_r54_readfeel_blocker_execution_blocker_ingestion_bodyfree()
    r10 = safe_mapping(sanitized_actual_review_result_capture) if sanitized_actual_review_result_capture is not None else safe_mapping(r10_sanitized_actual_review_result_capture) if r10_sanitized_actual_review_result_capture is not None else build_p7_r54_sanitized_actual_review_result_capture_bodyfree()
    assert_p7_r54_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(r12)
    assert_p7_r54_sanitized_actual_review_result_capture_bodyfree_contract(r10)
    r12_ready = r12.get("blocker_ingestion_status") == "READY_FOR_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION" and not r12.get("execution_blocker_ids")
    r10_ready = r10.get("capture_status") == "READY_FOR_RATING_ROW_NORMALIZATION" and not r10.get("execution_blocker_ids")
    question_rows = _r54_question_rows_from_capture(r10) if r12_ready and r10_ready else []
    rating_case_refs = {clean_identifier(ref, default="", max_length=160) for ref in (r12.get("rating_case_ref_ids") or [])}
    question_case_refs = {clean_identifier(row.get("case_ref_id"), default="", max_length=160) for row in question_rows}
    capture_case_refs = {clean_identifier(row.get("case_ref_id"), default="", max_length=160) for row in r10.get("sanitized_review_result_rows") or []}
    row_case_ref_sets_match_review_capture = bool(question_rows) and question_case_refs == capture_case_refs
    row_case_ref_sets_match_rating_rows = bool(question_rows) and question_case_refs == rating_case_refs
    all_required = len(question_rows) == P7_R51_REQUIRED_CASE_COUNT and row_case_ref_sets_match_review_capture and row_case_ref_sets_match_rating_rows
    canonical = True
    not_question_misclassified = any(row.get("not_question_repair_required") is True and row.get("p8_material_candidate_allowed") is True for row in question_rows)
    blockers: list[str] = []
    if not r12_ready:
        blockers.append("r54_blocker_ingestion_not_ready_for_question_observation")
    if not r10_ready:
        blockers.append("r54_sanitized_review_capture_not_ready_for_question_observation")
    if (r12_ready and r10_ready) and not all_required:
        blockers.append("r54_question_need_observation_rows_incomplete")
    if not_question_misclassified:
        blockers.append("r54_not_question_repair_misclassified_as_p8_material")
    ready = bool(r12_ready and r10_ready and all_required and canonical and not not_question_misclassified and not blockers)
    primary_counts = _r54_single_id_counts(question_rows, "question_need_primary_class")
    ambiguity_counts = _r54_count_ids(question_rows, "ambiguity_kind_refs")
    one_question_counts = _r54_single_id_counts(question_rows, "one_question_fit_ref")
    repair_counts = _r54_count_ids(question_rows, "repair_required_refs")
    plan_counts = _r54_count_ids(question_rows, "plan_candidate_flags")
    material = {
        "schema_version": P7_R54_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_STEP,
        "scope": P7_R54_SCOPE,
        "policy_kind": P7_R54_POLICY_KIND,
        "policy_section": P7_R54_R13_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_question_need_observation_row_normalization_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r12.get("review_session_id"), default=P7_R54_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r12_blocker_ingestion_schema_version": P7_R54_READFEEL_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION,
        "r12_blocker_ingestion_material_ref": clean_identifier(r12.get("material_id"), default="p7_r54_readfeel_blocker_execution_blocker_ingestion_bodyfree", max_length=180),
        "r12_blocker_ingestion_status": clean_identifier(r12.get("blocker_ingestion_status"), default="BLOCKED_BY_R54_11_RATING_ROW_NORMALIZATION", max_length=140),
        "r12_ready_for_question_need_observation_row_normalization": bool(r12_ready),
        "r10_sanitized_capture_schema_version": P7_R54_SANITIZED_ACTUAL_REVIEW_RESULT_CAPTURE_SCHEMA_VERSION,
        "r10_sanitized_capture_material_ref": clean_identifier(r10.get("material_id"), default="p7_r54_sanitized_actual_review_result_capture", max_length=180),
        "r10_capture_status": clean_identifier(r10.get("capture_status"), default="BLOCKED_BY_R54_9_OR_MISSING_SANITIZED_REVIEW_RESULTS", max_length=140),
        "r10_capture_ready_for_question_observation": bool(r10_ready),
        "current_received_snapshot_refs": dict(P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "r53_source_snapshot_refs": _r53_source_snapshot_refs(None),
        "r53_source_snapshot_ref_count": len(_r53_source_snapshot_refs(None)),
        "r53_refs_are_current_received_refs": False,
        "review_session_status": "R54_QUESTION_NEED_OBSERVATION_ROWS_NORMALIZED_BODYFREE" if ready else "PRECHECK_BLOCKED",
        "question_observation_normalizer_status": "READY_FOR_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD" if ready else "BLOCKED_BY_R54_12_OR_R54_10_PRECHECK",
        "question_observation_normalizer_reason_refs": ["r54_question_need_observation_rows_normalized_bodyfree"] if ready else blockers,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "review_result_capture_row_count": _safe_non_negative_int_r54(r10.get("sanitized_review_result_row_count")),
        "rating_row_count": _safe_non_negative_int_r54(r12.get("rating_row_count")),
        "question_observation_row_count": len(question_rows),
        "question_need_observation_rows": question_rows,
        "question_need_observation_row_schema_version": P7_R54_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION,
        "question_need_observation_row_required_field_refs": list(P7_R54_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_REQUIRED_FIELD_REFS),
        "question_need_observation_row_forbidden_field_refs": sorted(P7_R54_REVIEW_RESULT_INPUT_FORBIDDEN_KEY_REFS),
        "question_need_primary_class_refs": list(P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS),
        "ambiguity_kind_refs": list(P7_R49_AMBIGUITY_KIND_REFS),
        "one_question_fit_refs": list(P7_R49_ONE_QUESTION_FIT_REFS),
        "plan_candidate_flag_refs": list(P7_R54_PLAN_CANDIDATE_FLAG_REFS),
        "repair_required_ref_refs": list(P7_R49_REPAIR_REQUIRED_REF_REFS),
        "question_need_observation_stage_ref": P7_R50_QUESTION_NEED_OBSERVATION_STAGE_REF,
        "review_kind": "p5_human_blind_qa_actual_local_review_question_need_observation",
        "question_need_observation_rows_must_be_bodyfree": True,
        "question_text_absent_for_all_rows": True,
        "draft_question_text_absent_for_all_rows": True,
        "reviewer_free_text_absent_for_all_rows": True,
        "raw_input_absent_for_all_rows": True,
        "returned_surface_absent_for_all_rows": True,
        "local_path_absent_for_all_rows": True,
        "body_hash_absent_for_all_rows": True,
        "question_text_included_allowed": False,
        "draft_question_text_included_allowed": False,
        "reviewer_free_text_included_allowed": False,
        "raw_input_allowed": False,
        "returned_surface_allowed": False,
        "local_path_allowed": False,
        "body_hash_allowed": False,
        "p8_question_implementation_spec_finalized_here": False,
        "question_trigger_logic_implemented": False,
        "question_trigger_logic_implemented_here": False,
        "api_db_rn_response_key_changed_here": False,
        "question_api_implemented": False,
        "question_db_schema_implemented": False,
        "question_rn_ui_implemented": False,
        "question_response_key_implemented": False,
        "question_storage_schema_implemented": False,
        "question_answer_persistence_implemented": False,
        "question_plan_guard_implemented": False,
        "row_case_ref_sets_match_review_capture": row_case_ref_sets_match_review_capture,
        "row_case_ref_sets_match_rating_rows": row_case_ref_sets_match_rating_rows,
        "all_required_question_need_observation_rows_present": all_required,
        "primary_class_ambiguity_one_question_fit_are_canonical_refs": canonical,
        "not_question_repair_rows_misclassified_as_p8_material": not_question_misclassified,
        "p5_weakness_not_hidden_by_question_candidates_here": not not_question_misclassified,
        "question_text_or_draft_text_saved_here": False,
        "question_need_primary_class_counts": primary_counts,
        "ambiguity_kind_counts": ambiguity_counts,
        "one_question_fit_counts": one_question_counts,
        "repair_required_counts": repair_counts,
        "plan_candidate_flag_counts": plan_counts,
        "p8_material_candidate_row_count": sum(1 for row in question_rows if row.get("p8_material_candidate_allowed") is True),
        "not_question_repair_required_count": sum(1 for row in question_rows if row.get("not_question_repair_required") is True),
        "insufficient_material_execution_blocker_count": sum(1 for row in question_rows if row.get("insufficient_material_execution_blocker") is True),
        **_false_flags_except({"validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here"}),
        "body_full_packet_generated_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "actual_rating_rows_materialized_here": bool(ready and r12.get("actual_rating_rows_materialized_here") is True),
        "actual_blocker_rows_materialized_here": bool(ready and r12.get("actual_blocker_rows_materialized_here") is True),
        "actual_execution_blocker_rows_materialized_here": bool(ready and r12.get("actual_execution_blocker_rows_materialized_here") is True),
        "actual_question_need_observation_rows_materialized_here": ready,
        "actual_question_need_observation_summary_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "p5_actual_review_still_not_run_by_helper": True,
        "r54_0_scope_current_received_snapshot_refrozen": True,
        "r54_1_r53_source_delta_current_snapshot_override_adopted": True,
        "r54_2_validation_evidence_intake_done": r12.get("r54_2_validation_evidence_intake_done") is True,
        "r54_3_local_only_actual_review_preflight_built": r12.get("r54_3_local_only_actual_review_preflight_built") is True,
        "r54_4_actual_review_session_envelope_built": r12.get("r54_4_actual_review_session_envelope_built") is True,
        "r54_5_24_case_manifest_freeze_built": r12.get("r54_5_24_case_manifest_freeze_built") is True,
        "r54_6_local_only_body_full_packet_generation_request_built": r12.get("r54_6_local_only_body_full_packet_generation_request_built") is True,
        "r54_7_packet_completeness_export_denylist_scan_built": r12.get("r54_7_packet_completeness_export_denylist_scan_built") is True,
        "r54_8_reviewer_instruction_rating_form_freeze_built": r12.get("r54_8_reviewer_instruction_rating_form_freeze_built") is True,
        "r54_9_actual_human_review_operation_state_capture_built": r12.get("r54_9_actual_human_review_operation_state_capture_built") is True,
        "r54_10_sanitized_actual_review_result_capture_built": r12.get("r54_10_sanitized_actual_review_result_capture_built") is True,
        "r54_11_rating_row_normalization_built": r12.get("r54_11_rating_row_normalization_built") is True,
        "r54_12_readfeel_blocker_execution_blocker_ingestion_built": r12.get("r54_12_readfeel_blocker_execution_blocker_ingestion_built") is True,
        "r54_13_question_need_observation_row_normalization_built": ready,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "implemented_steps": list(P7_R54_R13_IMPLEMENTED_STEPS if ready else P7_R54_R12_IMPLEMENTED_STEPS if r12_ready else P7_R54_R11_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_R13_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_R12_NOT_YET_IMPLEMENTED_STEPS if r12_ready else P7_R54_R11_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R54_R13_NEXT_REQUIRED_STEP_REF if ready else P7_R54_R13_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "next_required_step": P7_R54_R13_NEXT_REQUIRED_STEP_REF if ready else P7_R54_R13_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "validation_evidence_intake_done_here": r12.get("validation_evidence_intake_done_here") is True,
        "local_root_preflight_passed_here": r12.get("local_root_preflight_passed_here") is True,
        "explicit_allow_present_here": r12.get("explicit_allow_present_here") is True,
        "purge_plan_verified_here": r12.get("purge_plan_verified_here") is True,
    }
    assert_p7_r54_question_need_observation_row_normalization_bodyfree_contract(material)
    return material


def assert_p7_r54_question_need_observation_row_normalization_bodyfree_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION_REQUIRED_FIELD_REFS, source="p7_r54_question_observation_normalization")
    ready = data.get("question_observation_normalizer_status") == "READY_FOR_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD"
    _assert_body_free_common_with_false_keys(data, schema_version=P7_R54_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION_SCHEMA_VERSION, source="p7_r54_question_observation_normalization", false_key_refs=P7_R54_R13_FALSE_KEY_REFS)
    _assert_current_refs(data, source="p7_r54_question_observation_normalization")
    if data.get("policy_section") != P7_R54_R13_STEP_REF:
        raise ValueError("R54 R13 policy section changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=80, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 R13 open blockers must match materialization blockers")
    rows = [safe_mapping(row) for row in (data.get("question_need_observation_rows") or [])]
    for row in rows:
        assert_p7_r54_question_need_observation_row_bodyfree_contract(row)
    if data.get("question_observation_row_count") != len(rows):
        raise ValueError("R54 R13 question row count mismatch")
    for true_key in (
        "question_need_observation_rows_must_be_bodyfree", "question_text_absent_for_all_rows", "draft_question_text_absent_for_all_rows", "reviewer_free_text_absent_for_all_rows", "raw_input_absent_for_all_rows", "returned_surface_absent_for_all_rows", "local_path_absent_for_all_rows", "body_hash_absent_for_all_rows",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R54 R13 must keep {true_key}=True")
    for false_key in (
        "question_text_included_allowed", "draft_question_text_included_allowed", "reviewer_free_text_included_allowed", "raw_input_allowed", "returned_surface_allowed", "local_path_allowed", "body_hash_allowed", "p8_question_implementation_spec_finalized_here", "question_trigger_logic_implemented", "question_trigger_logic_implemented_here", "api_db_rn_response_key_changed_here", "question_api_implemented", "question_db_schema_implemented", "question_rn_ui_implemented", "question_response_key_implemented", "question_storage_schema_implemented", "question_answer_persistence_implemented", "question_plan_guard_implemented", "question_text_or_draft_text_saved_here", "body_full_packet_generated_here", "actual_body_full_packet_generated_here", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_question_need_observation_summary_materialized_here", "actual_disposal_receipt_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 R13 must keep {false_key}=False")
    if data.get("question_need_observation_row_schema_version") != P7_R54_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R54 R13 row schema reference changed")
    if tuple(data.get("question_need_primary_class_refs") or ()) != P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS:
        raise ValueError("R54 R13 primary class refs changed")
    if tuple(data.get("ambiguity_kind_refs") or ()) != P7_R49_AMBIGUITY_KIND_REFS:
        raise ValueError("R54 R13 ambiguity refs changed")
    if tuple(data.get("one_question_fit_refs") or ()) != P7_R49_ONE_QUESTION_FIT_REFS:
        raise ValueError("R54 R13 one-question refs changed")
    if tuple(data.get("repair_required_ref_refs") or ()) != P7_R49_REPAIR_REQUIRED_REF_REFS:
        raise ValueError("R54 R13 repair refs changed")
    if data.get("question_need_observation_stage_ref") != P7_R50_QUESTION_NEED_OBSERVATION_STAGE_REF:
        raise ValueError("R54 R13 question observation stage changed")
    if data.get("not_question_repair_rows_misclassified_as_p8_material") is not False:
        raise ValueError("R54 R13 must not misclassify not-question repair rows as P8 material")
    if data.get("p5_weakness_not_hidden_by_question_candidates_here") is not True:
        raise ValueError("R54 R13 must keep P5 weakness separate from question candidates")
    if ready:
        if data.get("r12_ready_for_question_need_observation_row_normalization") is not True or data.get("r10_capture_ready_for_question_observation") is not True:
            raise ValueError("R54 R13 ready requires ready R12 and R10")
        if data.get("question_observation_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 R13 ready must carry 24 question observation rows")
        if data.get("row_case_ref_sets_match_review_capture") is not True or data.get("row_case_ref_sets_match_rating_rows") is not True:
            raise ValueError("R54 R13 ready row case sets must match capture and rating rows")
        if data.get("all_required_question_need_observation_rows_present") is not True or data.get("primary_class_ambiguity_one_question_fit_are_canonical_refs") is not True:
            raise ValueError("R54 R13 ready rows must be complete and canonical")
        if data.get("actual_rating_rows_materialized_here") is not True or data.get("actual_blocker_rows_materialized_here") is not True or data.get("actual_execution_blocker_rows_materialized_here") is not True:
            raise ValueError("R54 R13 ready must preserve rating and blocker rows")
        if data.get("actual_question_need_observation_rows_materialized_here") is not True:
            raise ValueError("R54 R13 ready must materialize body-free question rows")
        if blockers:
            raise ValueError("R54 R13 ready must not carry materialization blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_R13_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_R13_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 R13 ready step lists changed")
        if data.get("next_required_step") != P7_R54_R13_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R13 ready next step changed")
    else:
        if data.get("actual_question_need_observation_rows_materialized_here") is not False or data.get("r54_13_question_need_observation_row_normalization_built") is not False:
            raise ValueError("R54 R13 blocked must not claim question rows")
        if rows or data.get("question_observation_row_count") != 0:
            raise ValueError("R54 R13 blocked must not expose partial question rows")
        if not blockers or data.get("next_required_step") != P7_R54_R13_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R13 blocked next step changed")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_question_observation_normalization")
    return True


# ---------------------------------------------------------------------------
# R54-14 / R54-15 rating-question consistency and pause/abort protocol
# ---------------------------------------------------------------------------

P7_R54_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.rating_question_observation_consistency_issue_row.bodyfree.v1"
)
P7_R54_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.rating_question_observation_consistency_guard.bodyfree.v1"
)
P7_R54_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.pause_abort_expiration_protocol.bodyfree.v1"
)

P7_R54_R14_STEP_REF: Final = "R54-14_rating_question_observation_consistency_guard"
P7_R54_R15_STEP_REF: Final = "R54-15_pause_abort_expiration_protocol"
P7_R54_R14_NEXT_REQUIRED_STEP_REF: Final = "R54-15_pause_abort_expiration_protocol"
P7_R54_R14_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "resolve_R54-14_rating_question_observation_consistency_issues_before_R54-15_pause_abort_expiration_protocol"
)
P7_R54_R14_PRECHECK_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "resolve_R54-13_question_observation_and_R54-11_rating_rows_before_R54-14_consistency_guard"
)
P7_R54_R15_NEXT_REQUIRED_STEP_REF: Final = "R54-16_purge_disposal_receipt"
P7_R54_R15_PAUSED_NEXT_REQUIRED_STEP_REF: Final = "resume_or_abort_R54-15_paused_local_only_review_before_R54-16_purge_disposal_receipt"
P7_R54_R15_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R54-14_consistency_guard_before_R54-15_pause_abort_expiration_protocol"

P7_R54_FUTURE_STEPS_AFTER_R15: Final[tuple[str, ...]] = tuple(
    step for step in P7_R54_FUTURE_STEPS_AFTER_R13 if step not in {P7_R54_R14_STEP_REF, P7_R54_R15_STEP_REF}
)
P7_R54_R14_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_R13_IMPLEMENTED_STEPS, P7_R54_R14_STEP_REF)
P7_R54_R14_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_R15_STEP_REF, *P7_R54_FUTURE_STEPS_AFTER_R15)
P7_R54_R15_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_R14_IMPLEMENTED_STEPS, P7_R54_R15_STEP_REF)
P7_R54_R15_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_FUTURE_STEPS_AFTER_R15

P7_R54_R14_CONSISTENCY_ISSUE_ID_REFS: Final[tuple[str, ...]] = (
    "r54_rating_question_row_count_incomplete",
    "r54_rating_question_case_set_mismatch",
    "r54_red_with_no_question_needed_observation",
    "r54_repair_required_with_p8_question_candidate",
    "r54_pass_with_not_question_repair_required",
    "r54_insufficient_material_with_pass_or_no_execution_blocker",
)
P7_R54_R14_CONSISTENCY_ISSUE_KIND_REFS: Final[tuple[str, ...]] = (
    "rating_question_case_integrity_issue",
    "p5_repair_return_consistency_issue",
    "p5_inconclusive_consistency_issue",
    "p8_material_misclassification_issue",
)
P7_R54_R14_DECISION_DIRECTION_REFS: Final[tuple[str, ...]] = (
    "no_p5_decision_materialized_here",
    "p5_repair_return_required_later",
    "p5_inconclusive_required_later",
)
P7_R54_R15_PROTOCOL_ACTION_REFS: Final[tuple[str, ...]] = (
    "continue_after_consistency_guard",
    "paused_pending_reviewer_return",
    "aborted_purge_required",
    "expired_purge_required",
    "rating_incomplete_purge_required",
)
P7_R54_R15_PROTOCOL_STATUS_REFS: Final[tuple[str, ...]] = (
    "READY_FOR_PURGE_DISPOSAL_RECEIPT",
    "PAUSED_NO_HANDOFF_LOCAL_ONLY",
    "ABORTED_PURGE_REQUIRED",
    "EXPIRED_PURGE_REQUIRED",
    "RATING_INCOMPLETE_PURGE_REQUIRED",
    "BLOCKED_BY_R54_14_CONSISTENCY_GUARD",
)
P7_R54_R15_P5_DECISION_DIRECTION_REFS: Final[tuple[str, ...]] = (
    "no_p5_decision_materialized_here",
    "p5_inconclusive_due_to_pause_without_handoff",
    "p5_inconclusive_due_to_abort_or_expiration",
    "p5_inconclusive_due_to_rating_incomplete",
    "p5_inconclusive_due_to_r54_14_not_ready",
)

P7_R54_R14_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_R13_FALSE_KEY_REFS
    if key
    not in {
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
    }
)
P7_R54_R15_FALSE_KEY_REFS: Final[tuple[str, ...]] = P7_R54_R14_FALSE_KEY_REFS

P7_R54_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "blind_case_id",
    "case_ref_id",
    "packet_ref_id",
    "issue_id",
    "issue_kind_ref",
    "issue_status_ref",
    "verdict",
    "question_need_primary_class",
    "repair_required_refs",
    "decision_direction_ref",
    "raw_input_included",
    "returned_surface_included",
    "comment_text_included",
    "history_body_included",
    "reviewer_free_text_included",
    "question_text_included",
    "draft_question_text_included",
    "local_absolute_path_included",
    "body_content_hash_included",
    "packet_content_hash_included",
    "machine_auto_score_used",
    "machine_metrics_used_for_readfeel",
    "body_free",
)

P7_R54_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "r13_question_observation_schema_version", "r13_question_observation_material_ref", "r13_question_observation_normalizer_status", "r13_ready_for_rating_question_consistency_guard",
    "r11_rating_row_normalization_schema_version", "r11_rating_row_normalization_material_ref", "r11_rating_row_normalizer_status", "r11_ready_for_rating_question_consistency_guard",
    "current_received_snapshot_refs", "current_received_snapshot_ref_count", "r53_source_snapshot_refs", "r53_source_snapshot_ref_count", "r53_refs_are_current_received_refs",
    "review_session_status", "rating_question_consistency_guard_status", "rating_question_consistency_guard_reason_refs", "required_case_count", "rating_row_count", "question_observation_row_count",
    "rating_question_case_ref_sets_match", "all_required_rating_and_question_rows_present", "rating_question_consistency_issue_row_schema_version", "rating_question_consistency_issue_row_required_field_refs", "rating_question_consistency_issue_rows", "consistency_issue_count",
    "red_with_no_question_needed_observation_count", "repair_required_with_p8_question_candidate_count", "pass_with_not_question_repair_required_count", "insufficient_material_with_pass_or_no_execution_blocker_count",
    "consistency_issue_direction_counts", "p5_confirmed_candidate_blocked_by_consistency_issues", "p5_decision_candidate_not_materialized_here", "issues_route_to_p5_repair_return_or_inconclusive_later", "p8_material_candidates_do_not_hide_p5_repair_here", "ready_for_pause_abort_expiration_protocol",
    "body_full_packet_generated_here", "actual_body_full_packet_generated_here", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_question_need_observation_summary_materialized_here", "actual_disposal_receipt_materialized_here", "p5_actual_review_still_not_run_by_helper",
    "r54_0_scope_current_received_snapshot_refrozen", "r54_1_r53_source_delta_current_snapshot_override_adopted", "r54_2_validation_evidence_intake_done", "r54_3_local_only_actual_review_preflight_built", "r54_4_actual_review_session_envelope_built", "r54_5_24_case_manifest_freeze_built", "r54_6_local_only_body_full_packet_generation_request_built", "r54_7_packet_completeness_export_denylist_scan_built", "r54_8_reviewer_instruction_rating_form_freeze_built", "r54_9_actual_human_review_operation_state_capture_built", "r54_10_sanitized_actual_review_result_capture_built", "r54_11_rating_row_normalization_built", "r54_12_readfeel_blocker_execution_blocker_ingestion_built", "r54_13_question_need_observation_row_normalization_built", "r54_14_rating_question_observation_consistency_guard_built",
    "execution_blocker_ids", "open_execution_blocker_ids", "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract", "r54_public_no_touch_contract", "body_free_markers", "body_free",
    *P7_R54_R14_FALSE_KEY_REFS,
    "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here",
    "validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here",
)

P7_R54_PAUSE_ABORT_EXPIRATION_PROTOCOL_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "r14_consistency_guard_schema_version", "r14_consistency_guard_material_ref", "r14_consistency_guard_status", "r14_ready_for_pause_abort_expiration_protocol", "r14_consistency_issue_count",
    "current_received_snapshot_refs", "current_received_snapshot_ref_count", "r53_source_snapshot_refs", "r53_source_snapshot_ref_count", "r53_refs_are_current_received_refs",
    "review_session_status", "pause_abort_expiration_protocol_status", "pause_abort_expiration_protocol_reason_refs", "protocol_action_ref", "protocol_action_refs", "protocol_status_refs",
    "review_can_continue_to_purge_disposal_receipt", "review_paused_without_handoff", "review_aborted", "review_expired", "rating_rows_incomplete", "abort_or_expired_requires_purge", "rating_incomplete_requires_purge", "purge_required_before_any_handoff", "purge_before_handoff_required", "handoff_allowed_before_purge", "r52_reintake_handoff_allowed_before_purge", "body_full_local_material_must_remain_local_until_purge", "p5_decision_direction_ref", "p5_decision_materialized_here", "p5_inconclusive_direction_only_not_decision_materialized",
    "body_full_packet_generated_here", "actual_body_full_packet_generated_here", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_question_need_observation_summary_materialized_here", "actual_disposal_run_here", "disposal_receipt_materialized_here", "actual_disposal_receipt_materialized_here", "post_review_summary_materialized_here", "p5_actual_review_still_not_run_by_helper",
    "r54_0_scope_current_received_snapshot_refrozen", "r54_1_r53_source_delta_current_snapshot_override_adopted", "r54_2_validation_evidence_intake_done", "r54_3_local_only_actual_review_preflight_built", "r54_4_actual_review_session_envelope_built", "r54_5_24_case_manifest_freeze_built", "r54_6_local_only_body_full_packet_generation_request_built", "r54_7_packet_completeness_export_denylist_scan_built", "r54_8_reviewer_instruction_rating_form_freeze_built", "r54_9_actual_human_review_operation_state_capture_built", "r54_10_sanitized_actual_review_result_capture_built", "r54_11_rating_row_normalization_built", "r54_12_readfeel_blocker_execution_blocker_ingestion_built", "r54_13_question_need_observation_row_normalization_built", "r54_14_rating_question_observation_consistency_guard_built", "r54_15_pause_abort_expiration_protocol_built",
    "execution_blocker_ids", "open_execution_blocker_ids", "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract", "r54_public_no_touch_contract", "body_free_markers", "body_free",
    *P7_R54_R15_FALSE_KEY_REFS,
    "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here",
    "validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here",
)


def build_p7_r54_rating_question_consistency_issue_row_bodyfree(
    *,
    rating_row: Mapping[str, Any] | None = None,
    question_need_observation_row: Mapping[str, Any] | None = None,
    issue_id: Any,
    issue_kind_ref: Any,
    decision_direction_ref: Any,
) -> dict[str, Any]:
    rating = safe_mapping(rating_row)
    question = safe_mapping(question_need_observation_row)
    if rating:
        assert_p7_r54_rating_row_bodyfree_contract(rating)
    if question:
        assert_p7_r54_question_need_observation_row_bodyfree_contract(question)
    issue_ref = clean_identifier(issue_id, default="", max_length=140)
    if issue_ref not in P7_R54_R14_CONSISTENCY_ISSUE_ID_REFS:
        raise ValueError("R54 R14 consistency issue id must be canonical")
    kind_ref = clean_identifier(issue_kind_ref, default="", max_length=120)
    if kind_ref not in P7_R54_R14_CONSISTENCY_ISSUE_KIND_REFS:
        raise ValueError("R54 R14 consistency issue kind must be canonical")
    direction_ref = clean_identifier(decision_direction_ref, default="no_p5_decision_materialized_here", max_length=120)
    if direction_ref not in P7_R54_R14_DECISION_DIRECTION_REFS:
        raise ValueError("R54 R14 consistency issue decision direction must be canonical")
    source = rating or question
    out = {
        "schema_version": P7_R54_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION,
        "review_session_id": clean_identifier(source.get("review_session_id"), default=P7_R54_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "blind_case_id": clean_identifier(source.get("blind_case_id"), default="case_set", max_length=160),
        "case_ref_id": clean_identifier(source.get("case_ref_id"), default="case_set", max_length=160),
        "packet_ref_id": clean_identifier(source.get("packet_ref_id"), default="packet_set", max_length=160),
        "issue_id": issue_ref,
        "issue_kind_ref": kind_ref,
        "issue_status_ref": "open",
        "verdict": clean_identifier(rating.get("verdict"), default="not_available", max_length=60),
        "question_need_primary_class": clean_identifier(question.get("question_need_primary_class"), default="not_available", max_length=140),
        "repair_required_refs": dedupe_identifiers(question.get("repair_required_refs") or [], limit=12, max_length=140),
        "decision_direction_ref": direction_ref,
        "raw_input_included": False,
        "returned_surface_included": False,
        "comment_text_included": False,
        "history_body_included": False,
        "reviewer_free_text_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_absolute_path_included": False,
        "body_content_hash_included": False,
        "packet_content_hash_included": False,
        "machine_auto_score_used": False,
        "machine_metrics_used_for_readfeel": False,
        "body_free": True,
    }
    assert_p7_r54_rating_question_consistency_issue_row_bodyfree_contract(out)
    return out


def assert_p7_r54_rating_question_consistency_issue_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R54_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_ROW_REQUIRED_FIELD_REFS, source="p7_r54_rating_question_consistency_issue_row")
    if data.get("schema_version") != P7_R54_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION:
        raise ValueError("R54 R14 consistency issue row schema changed")
    if data.get("issue_id") not in P7_R54_R14_CONSISTENCY_ISSUE_ID_REFS:
        raise ValueError("R54 R14 consistency issue row id changed")
    if data.get("issue_kind_ref") not in P7_R54_R14_CONSISTENCY_ISSUE_KIND_REFS:
        raise ValueError("R54 R14 consistency issue row kind changed")
    if data.get("issue_status_ref") != "open":
        raise ValueError("R54 R14 consistency issue row must remain open")
    if data.get("decision_direction_ref") not in P7_R54_R14_DECISION_DIRECTION_REFS:
        raise ValueError("R54 R14 consistency issue row decision direction changed")
    for false_key in (
        "raw_input_included", "returned_surface_included", "comment_text_included", "history_body_included", "reviewer_free_text_included", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included", "machine_auto_score_used", "machine_metrics_used_for_readfeel",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 R14 consistency issue row must keep {false_key}=False")
    if data.get("body_free") is not True:
        raise ValueError("R54 R14 consistency issue row must be body-free")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_rating_question_consistency_issue_row")
    return True


def _r54_index_by_case_ref(rows: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for raw in rows or []:
        row = safe_mapping(raw)
        case_ref = clean_identifier(row.get("case_ref_id"), default="", max_length=160)
        if case_ref and case_ref not in index:
            index[case_ref] = row
    return index


def _r54_rating_question_consistency_issue_rows(
    *,
    rating_rows: Sequence[Mapping[str, Any]],
    question_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    rating_index = _r54_index_by_case_ref(rating_rows)
    question_index = _r54_index_by_case_ref(question_rows)
    if len(rating_rows) != P7_R51_REQUIRED_CASE_COUNT or len(question_rows) != P7_R51_REQUIRED_CASE_COUNT:
        issues.append(build_p7_r54_rating_question_consistency_issue_row_bodyfree(
            issue_id="r54_rating_question_row_count_incomplete",
            issue_kind_ref="rating_question_case_integrity_issue",
            decision_direction_ref="p5_inconclusive_required_later",
        ))
    if set(rating_index) != set(question_index):
        issues.append(build_p7_r54_rating_question_consistency_issue_row_bodyfree(
            issue_id="r54_rating_question_case_set_mismatch",
            issue_kind_ref="rating_question_case_integrity_issue",
            decision_direction_ref="p5_inconclusive_required_later",
        ))
    for case_ref in sorted(set(rating_index) & set(question_index)):
        rating = rating_index[case_ref]
        question = question_index[case_ref]
        verdict = clean_identifier(rating.get("verdict"), default="", max_length=60)
        primary = clean_identifier(question.get("question_need_primary_class"), default="", max_length=140)
        repair_refs = set(dedupe_identifiers(question.get("repair_required_refs") or [], limit=12, max_length=140))
        readfeel_blockers = dedupe_identifiers(rating.get("readfeel_blocker_ids") or [], limit=12, max_length=140)
        execution_blockers = dedupe_identifiers(rating.get("execution_blocker_ids") or [], limit=12, max_length=140)
        if verdict == "RED" and primary == "no_question_needed_emlis_can_observe":
            issues.append(build_p7_r54_rating_question_consistency_issue_row_bodyfree(
                rating_row=rating,
                question_need_observation_row=question,
                issue_id="r54_red_with_no_question_needed_observation",
                issue_kind_ref="p5_repair_return_consistency_issue",
                decision_direction_ref="p5_repair_return_required_later",
            ))
        if verdict == "REPAIR_REQUIRED" and (primary in P7_R54_P8_MATERIAL_CANDIDATE_PRIMARY_CLASS_REFS or question.get("p8_material_candidate_allowed") is True):
            issues.append(build_p7_r54_rating_question_consistency_issue_row_bodyfree(
                rating_row=rating,
                question_need_observation_row=question,
                issue_id="r54_repair_required_with_p8_question_candidate",
                issue_kind_ref="p8_material_misclassification_issue",
                decision_direction_ref="p5_repair_return_required_later",
            ))
        if verdict == "PASS" and (primary in P7_R54_NOT_QUESTION_REPAIR_PRIMARY_CLASS_REFS or bool(repair_refs - {"no_repair_required"})):
            issues.append(build_p7_r54_rating_question_consistency_issue_row_bodyfree(
                rating_row=rating,
                question_need_observation_row=question,
                issue_id="r54_pass_with_not_question_repair_required",
                issue_kind_ref="p5_repair_return_consistency_issue",
                decision_direction_ref="p5_repair_return_required_later",
            ))
        if primary == "insufficient_material_execution_blocker" and (verdict == "PASS" or not execution_blockers):
            issues.append(build_p7_r54_rating_question_consistency_issue_row_bodyfree(
                rating_row=rating,
                question_need_observation_row=question,
                issue_id="r54_insufficient_material_with_pass_or_no_execution_blocker",
                issue_kind_ref="p5_inconclusive_consistency_issue",
                decision_direction_ref="p5_inconclusive_required_later",
            ))
    return issues


def build_p7_r54_rating_question_observation_consistency_guard_bodyfree(
    *,
    question_need_observation_row_normalization: Mapping[str, Any] | None = None,
    r13_question_need_observation_row_normalization: Mapping[str, Any] | None = None,
    rating_row_normalization: Mapping[str, Any] | None = None,
    r11_rating_row_normalization: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_rating_question_observation_consistency_guard_bodyfree",
) -> dict[str, Any]:
    if question_need_observation_row_normalization is not None and r13_question_need_observation_row_normalization is not None:
        raise ValueError("provide only one R54-13 question observation normalization value")
    if rating_row_normalization is not None and r11_rating_row_normalization is not None:
        raise ValueError("provide only one R54-11 rating row normalization value")
    r13 = safe_mapping(question_need_observation_row_normalization) if question_need_observation_row_normalization is not None else safe_mapping(r13_question_need_observation_row_normalization) if r13_question_need_observation_row_normalization is not None else build_p7_r54_question_need_observation_row_normalization_bodyfree()
    r11 = safe_mapping(rating_row_normalization) if rating_row_normalization is not None else safe_mapping(r11_rating_row_normalization) if r11_rating_row_normalization is not None else build_p7_r54_rating_row_normalization_bodyfree()
    assert_p7_r54_question_need_observation_row_normalization_bodyfree_contract(r13)
    assert_p7_r54_rating_row_normalization_bodyfree_contract(r11)
    r13_ready = r13.get("question_observation_normalizer_status") == "READY_FOR_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD" and not r13.get("execution_blocker_ids")
    r11_ready = r11.get("rating_row_normalizer_status") == "READY_FOR_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION" and not r11.get("execution_blocker_ids")
    rating_rows = [safe_mapping(row) for row in (r11.get("rating_rows") or [])] if r11_ready else []
    question_rows = [safe_mapping(row) for row in (r13.get("question_need_observation_rows") or [])] if r13_ready else []
    rating_case_refs = {clean_identifier(row.get("case_ref_id"), default="", max_length=160) for row in rating_rows}
    question_case_refs = {clean_identifier(row.get("case_ref_id"), default="", max_length=160) for row in question_rows}
    case_sets_match = bool(rating_rows and question_rows and rating_case_refs == question_case_refs)
    all_required = len(rating_rows) == P7_R51_REQUIRED_CASE_COUNT and len(question_rows) == P7_R51_REQUIRED_CASE_COUNT and case_sets_match
    precheck_blockers: list[str] = []
    if not r13_ready:
        precheck_blockers.append("r54_question_observation_normalization_not_ready_for_consistency_guard")
    if not r11_ready:
        precheck_blockers.append("r54_rating_row_normalization_not_ready_for_consistency_guard")
    issue_rows = _r54_rating_question_consistency_issue_rows(rating_rows=rating_rows, question_rows=question_rows) if r13_ready and r11_ready else []
    issue_count = len(issue_rows)
    ready = bool(r13_ready and r11_ready and all_required and issue_count == 0 and not precheck_blockers)
    parent_ready = bool(r13_ready and r11_ready)
    direction_counts = _r54_single_id_counts(issue_rows, "decision_direction_ref")
    status = "READY_FOR_PAUSE_ABORT_EXPIRATION_PROTOCOL" if ready else "BLOCKED_BY_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUES" if parent_ready else "BLOCKED_BY_R54_13_OR_R54_11_PRECHECK"
    reason_refs = ["r54_rating_question_observation_consistency_guard_passed"] if ready else [*(precheck_blockers or []), *dedupe_identifiers((row.get("issue_id") for row in issue_rows), limit=40, max_length=140)]
    material = {
        "schema_version": P7_R54_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_STEP,
        "scope": P7_R54_SCOPE,
        "policy_kind": P7_R54_POLICY_KIND,
        "policy_section": P7_R54_R14_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_rating_question_observation_consistency_guard_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r13.get("review_session_id"), default=P7_R54_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r13_question_observation_schema_version": P7_R54_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION_SCHEMA_VERSION,
        "r13_question_observation_material_ref": clean_identifier(r13.get("material_id"), default="p7_r54_question_need_observation_row_normalization_bodyfree", max_length=180),
        "r13_question_observation_normalizer_status": clean_identifier(r13.get("question_observation_normalizer_status"), default="BLOCKED_BY_R54_12_OR_R54_10_PRECHECK", max_length=140),
        "r13_ready_for_rating_question_consistency_guard": bool(r13_ready),
        "r11_rating_row_normalization_schema_version": P7_R54_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        "r11_rating_row_normalization_material_ref": clean_identifier(r11.get("material_id"), default="p7_r54_rating_row_normalization_bodyfree", max_length=180),
        "r11_rating_row_normalizer_status": clean_identifier(r11.get("rating_row_normalizer_status"), default="BLOCKED_BY_R54_10_SANITIZED_CAPTURE", max_length=140),
        "r11_ready_for_rating_question_consistency_guard": bool(r11_ready),
        "current_received_snapshot_refs": dict(P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "r53_source_snapshot_refs": _r53_source_snapshot_refs(None),
        "r53_source_snapshot_ref_count": len(_r53_source_snapshot_refs(None)),
        "r53_refs_are_current_received_refs": False,
        "review_session_status": "R54_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_READY" if ready else "PRECHECK_BLOCKED" if not parent_ready else "CONSISTENCY_ISSUE_BLOCKED",
        "rating_question_consistency_guard_status": status,
        "rating_question_consistency_guard_reason_refs": reason_refs,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "rating_row_count": len(rating_rows),
        "question_observation_row_count": len(question_rows),
        "rating_question_case_ref_sets_match": case_sets_match,
        "all_required_rating_and_question_rows_present": all_required,
        "rating_question_consistency_issue_row_schema_version": P7_R54_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION,
        "rating_question_consistency_issue_row_required_field_refs": list(P7_R54_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_ROW_REQUIRED_FIELD_REFS),
        "rating_question_consistency_issue_rows": issue_rows,
        "consistency_issue_count": issue_count,
        "red_with_no_question_needed_observation_count": sum(1 for row in issue_rows if row.get("issue_id") == "r54_red_with_no_question_needed_observation"),
        "repair_required_with_p8_question_candidate_count": sum(1 for row in issue_rows if row.get("issue_id") == "r54_repair_required_with_p8_question_candidate"),
        "pass_with_not_question_repair_required_count": sum(1 for row in issue_rows if row.get("issue_id") == "r54_pass_with_not_question_repair_required"),
        "insufficient_material_with_pass_or_no_execution_blocker_count": sum(1 for row in issue_rows if row.get("issue_id") == "r54_insufficient_material_with_pass_or_no_execution_blocker"),
        "consistency_issue_direction_counts": direction_counts,
        "p5_confirmed_candidate_blocked_by_consistency_issues": issue_count > 0,
        "p5_decision_candidate_not_materialized_here": True,
        "issues_route_to_p5_repair_return_or_inconclusive_later": issue_count > 0,
        "p8_material_candidates_do_not_hide_p5_repair_here": True,
        "ready_for_pause_abort_expiration_protocol": ready,
        **_false_flags_except({"validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here"}),
        "body_full_packet_generated_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "actual_rating_rows_materialized_here": bool(parent_ready and r13.get("actual_rating_rows_materialized_here") is True and r11.get("actual_rating_rows_materialized_here") is True),
        "actual_blocker_rows_materialized_here": bool(parent_ready and r13.get("actual_blocker_rows_materialized_here") is True),
        "actual_execution_blocker_rows_materialized_here": bool(parent_ready and r13.get("actual_execution_blocker_rows_materialized_here") is True),
        "actual_question_need_observation_rows_materialized_here": bool(parent_ready and r13.get("actual_question_need_observation_rows_materialized_here") is True),
        "actual_question_need_observation_summary_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "p5_actual_review_still_not_run_by_helper": True,
        "r54_0_scope_current_received_snapshot_refrozen": True,
        "r54_1_r53_source_delta_current_snapshot_override_adopted": True,
        "r54_2_validation_evidence_intake_done": r13.get("r54_2_validation_evidence_intake_done") is True,
        "r54_3_local_only_actual_review_preflight_built": r13.get("r54_3_local_only_actual_review_preflight_built") is True,
        "r54_4_actual_review_session_envelope_built": r13.get("r54_4_actual_review_session_envelope_built") is True,
        "r54_5_24_case_manifest_freeze_built": r13.get("r54_5_24_case_manifest_freeze_built") is True,
        "r54_6_local_only_body_full_packet_generation_request_built": r13.get("r54_6_local_only_body_full_packet_generation_request_built") is True,
        "r54_7_packet_completeness_export_denylist_scan_built": r13.get("r54_7_packet_completeness_export_denylist_scan_built") is True,
        "r54_8_reviewer_instruction_rating_form_freeze_built": r13.get("r54_8_reviewer_instruction_rating_form_freeze_built") is True,
        "r54_9_actual_human_review_operation_state_capture_built": r13.get("r54_9_actual_human_review_operation_state_capture_built") is True,
        "r54_10_sanitized_actual_review_result_capture_built": r13.get("r54_10_sanitized_actual_review_result_capture_built") is True,
        "r54_11_rating_row_normalization_built": r13.get("r54_11_rating_row_normalization_built") is True and r11.get("r54_11_rating_row_normalization_built") is True,
        "r54_12_readfeel_blocker_execution_blocker_ingestion_built": r13.get("r54_12_readfeel_blocker_execution_blocker_ingestion_built") is True,
        "r54_13_question_need_observation_row_normalization_built": r13_ready,
        "r54_14_rating_question_observation_consistency_guard_built": parent_ready,
        "execution_blocker_ids": [] if parent_ready else precheck_blockers,
        "open_execution_blocker_ids": [] if parent_ready else precheck_blockers,
        "implemented_steps": list(P7_R54_R14_IMPLEMENTED_STEPS if parent_ready else P7_R54_R13_IMPLEMENTED_STEPS if r13_ready else P7_R54_R12_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_R14_NOT_YET_IMPLEMENTED_STEPS if parent_ready else P7_R54_R13_NOT_YET_IMPLEMENTED_STEPS if r13_ready else P7_R54_R12_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R54_R14_NEXT_REQUIRED_STEP_REF if ready else P7_R54_R14_BLOCKED_NEXT_REQUIRED_STEP_REF if parent_ready else P7_R54_R14_PRECHECK_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "next_required_step": P7_R54_R14_NEXT_REQUIRED_STEP_REF if ready else P7_R54_R14_BLOCKED_NEXT_REQUIRED_STEP_REF if parent_ready else P7_R54_R14_PRECHECK_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "validation_evidence_intake_done_here": r13.get("validation_evidence_intake_done_here") is True,
        "local_root_preflight_passed_here": r13.get("local_root_preflight_passed_here") is True,
        "explicit_allow_present_here": r13.get("explicit_allow_present_here") is True,
        "purge_plan_verified_here": r13.get("purge_plan_verified_here") is True,
    }
    assert_p7_r54_rating_question_observation_consistency_guard_bodyfree_contract(material)
    return material


def assert_p7_r54_rating_question_observation_consistency_guard_bodyfree_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS, source="p7_r54_rating_question_consistency_guard")
    ready = data.get("rating_question_consistency_guard_status") == "READY_FOR_PAUSE_ABORT_EXPIRATION_PROTOCOL"
    parent_ready = data.get("r13_ready_for_rating_question_consistency_guard") is True and data.get("r11_ready_for_rating_question_consistency_guard") is True
    _assert_body_free_common_with_false_keys(data, schema_version=P7_R54_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_SCHEMA_VERSION, source="p7_r54_rating_question_consistency_guard", false_key_refs=P7_R54_R14_FALSE_KEY_REFS)
    _assert_current_refs(data, source="p7_r54_rating_question_consistency_guard")
    if data.get("policy_section") != P7_R54_R14_STEP_REF:
        raise ValueError("R54 R14 policy section changed")
    if data.get("rating_question_consistency_guard_status") not in {"READY_FOR_PAUSE_ABORT_EXPIRATION_PROTOCOL", "BLOCKED_BY_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUES", "BLOCKED_BY_R54_13_OR_R54_11_PRECHECK"}:
        raise ValueError("R54 R14 status changed")
    issue_rows = [safe_mapping(row) for row in data.get("rating_question_consistency_issue_rows") or []]
    for row in issue_rows:
        assert_p7_r54_rating_question_consistency_issue_row_bodyfree_contract(row)
    if data.get("consistency_issue_count") != len(issue_rows):
        raise ValueError("R54 R14 consistency issue count mismatch")
    if data.get("p5_decision_candidate_not_materialized_here") is not True:
        raise ValueError("R54 R14 must not materialize P5 decision candidate")
    if data.get("p8_material_candidates_do_not_hide_p5_repair_here") is not True:
        raise ValueError("R54 R14 must keep P8 material candidates from hiding P5 repair")
    for false_key in (
        "body_full_packet_generated_here", "actual_body_full_packet_generated_here", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_question_need_observation_summary_materialized_here", "actual_disposal_receipt_materialized_here", "p5_human_blind_qa_confirmed_candidate", "p6_limited_human_readfeel_start_allowed", "p8_start_allowed", "release_allowed", "api_db_rn_response_key_changed_here", "runtime_changed_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 R14 must keep {false_key}=False")
    if ready:
        if not parent_ready:
            raise ValueError("R54 R14 ready requires R13 and R11 ready")
        if data.get("consistency_issue_count") != 0 or issue_rows:
            raise ValueError("R54 R14 ready requires zero consistency issues")
        if data.get("rating_row_count") != P7_R51_REQUIRED_CASE_COUNT or data.get("question_observation_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 R14 ready requires 24 rating and question rows")
        if data.get("rating_question_case_ref_sets_match") is not True or data.get("all_required_rating_and_question_rows_present") is not True:
            raise ValueError("R54 R14 ready case sets must match")
        if data.get("ready_for_pause_abort_expiration_protocol") is not True:
            raise ValueError("R54 R14 ready must allow R15")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_R14_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_R14_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 R14 ready step lists changed")
        if data.get("next_required_step") != P7_R54_R14_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R14 ready next step changed")
    elif parent_ready:
        if data.get("consistency_issue_count") <= 0:
            raise ValueError("R54 R14 issue-blocked state must carry consistency issues")
        if data.get("p5_confirmed_candidate_blocked_by_consistency_issues") is not True:
            raise ValueError("R54 R14 issues must block P5 confirmed candidate")
        if data.get("issues_route_to_p5_repair_return_or_inconclusive_later") is not True:
            raise ValueError("R54 R14 issues must route to repair or inconclusive later")
        if data.get("next_required_step") != P7_R54_R14_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R14 issue-blocked next step changed")
    else:
        blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=80, max_length=140)
        if not blockers or data.get("next_required_step") != P7_R54_R14_PRECHECK_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R14 precheck-blocked next step changed")
        if data.get("r54_14_rating_question_observation_consistency_guard_built") is not False:
            raise ValueError("R54 R14 precheck-blocked must not claim guard built")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_rating_question_consistency_guard")
    return True


def build_p7_r54_pause_abort_expiration_protocol_bodyfree(
    *,
    rating_question_observation_consistency_guard: Mapping[str, Any] | None = None,
    r14_rating_question_observation_consistency_guard: Mapping[str, Any] | None = None,
    protocol_action_ref: Any = "continue_after_consistency_guard",
    material_id: Any = "p7_r54_pause_abort_expiration_protocol_bodyfree",
) -> dict[str, Any]:
    if rating_question_observation_consistency_guard is not None and r14_rating_question_observation_consistency_guard is not None:
        raise ValueError("provide only one R54-14 consistency guard value")
    r14 = safe_mapping(rating_question_observation_consistency_guard) if rating_question_observation_consistency_guard is not None else safe_mapping(r14_rating_question_observation_consistency_guard) if r14_rating_question_observation_consistency_guard is not None else build_p7_r54_rating_question_observation_consistency_guard_bodyfree()
    assert_p7_r54_rating_question_observation_consistency_guard_bodyfree_contract(r14)
    action_ref = clean_identifier(protocol_action_ref, default="continue_after_consistency_guard", max_length=120)
    if action_ref not in P7_R54_R15_PROTOCOL_ACTION_REFS:
        raise ValueError("R54 R15 protocol action must be canonical")
    r14_ready = r14.get("rating_question_consistency_guard_status") == "READY_FOR_PAUSE_ABORT_EXPIRATION_PROTOCOL" and r14.get("consistency_issue_count") == 0 and not r14.get("execution_blocker_ids")
    review_paused = action_ref == "paused_pending_reviewer_return"
    review_aborted = action_ref == "aborted_purge_required"
    review_expired = action_ref == "expired_purge_required"
    rating_incomplete = action_ref == "rating_incomplete_purge_required"
    continue_ready = action_ref == "continue_after_consistency_guard" and r14_ready
    purge_required = bool(continue_ready or review_aborted or review_expired or rating_incomplete)
    if continue_ready:
        protocol_status = "READY_FOR_PURGE_DISPOSAL_RECEIPT"
        reason_refs = ["r54_15_continue_to_purge_after_consistency_guard"]
        p5_direction = "no_p5_decision_materialized_here"
        next_required_step = P7_R54_R15_NEXT_REQUIRED_STEP_REF
        implemented_steps = P7_R54_R15_IMPLEMENTED_STEPS
        not_yet_implemented_steps = P7_R54_R15_NOT_YET_IMPLEMENTED_STEPS
    elif review_paused:
        protocol_status = "PAUSED_NO_HANDOFF_LOCAL_ONLY"
        reason_refs = ["r54_15_review_paused_no_handoff_allowed"]
        p5_direction = "p5_inconclusive_due_to_pause_without_handoff"
        next_required_step = P7_R54_R15_PAUSED_NEXT_REQUIRED_STEP_REF
        implemented_steps = P7_R54_R15_IMPLEMENTED_STEPS
        not_yet_implemented_steps = P7_R54_R15_NOT_YET_IMPLEMENTED_STEPS
    elif review_aborted or review_expired:
        protocol_status = "ABORTED_PURGE_REQUIRED" if review_aborted else "EXPIRED_PURGE_REQUIRED"
        reason_refs = ["r54_15_abort_or_expired_requires_purge_before_any_handoff"]
        p5_direction = "p5_inconclusive_due_to_abort_or_expiration"
        next_required_step = P7_R54_R15_NEXT_REQUIRED_STEP_REF
        implemented_steps = P7_R54_R15_IMPLEMENTED_STEPS
        not_yet_implemented_steps = P7_R54_R15_NOT_YET_IMPLEMENTED_STEPS
    elif rating_incomplete:
        protocol_status = "RATING_INCOMPLETE_PURGE_REQUIRED"
        reason_refs = ["r54_15_rating_incomplete_requires_purge_and_inconclusive_direction"]
        p5_direction = "p5_inconclusive_due_to_rating_incomplete"
        next_required_step = P7_R54_R15_NEXT_REQUIRED_STEP_REF
        implemented_steps = P7_R54_R15_IMPLEMENTED_STEPS
        not_yet_implemented_steps = P7_R54_R15_NOT_YET_IMPLEMENTED_STEPS
    else:
        protocol_status = "BLOCKED_BY_R54_14_CONSISTENCY_GUARD"
        reason_refs = ["r54_15_consistency_guard_not_ready_for_continue"]
        p5_direction = "p5_inconclusive_due_to_r54_14_not_ready"
        next_required_step = P7_R54_R15_BLOCKED_NEXT_REQUIRED_STEP_REF
        implemented_steps = P7_R54_R14_IMPLEMENTED_STEPS if r14.get("r54_14_rating_question_observation_consistency_guard_built") is True else P7_R54_R13_IMPLEMENTED_STEPS
        not_yet_implemented_steps = P7_R54_R14_NOT_YET_IMPLEMENTED_STEPS
    material = {
        "schema_version": P7_R54_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_STEP,
        "scope": P7_R54_SCOPE,
        "policy_kind": P7_R54_POLICY_KIND,
        "policy_section": P7_R54_R15_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_pause_abort_expiration_protocol_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r14.get("review_session_id"), default=P7_R54_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r14_consistency_guard_schema_version": P7_R54_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        "r14_consistency_guard_material_ref": clean_identifier(r14.get("material_id"), default="p7_r54_rating_question_observation_consistency_guard_bodyfree", max_length=180),
        "r14_consistency_guard_status": clean_identifier(r14.get("rating_question_consistency_guard_status"), default="BLOCKED_BY_R54_13_OR_R54_11_PRECHECK", max_length=140),
        "r14_ready_for_pause_abort_expiration_protocol": bool(r14_ready),
        "r14_consistency_issue_count": _safe_non_negative_int_r54(r14.get("consistency_issue_count")),
        "current_received_snapshot_refs": dict(P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "r53_source_snapshot_refs": _r53_source_snapshot_refs(None),
        "r53_source_snapshot_ref_count": len(_r53_source_snapshot_refs(None)),
        "r53_refs_are_current_received_refs": False,
        "review_session_status": "R54_PAUSE_ABORT_EXPIRATION_PROTOCOL_CAPTURED_BODYFREE" if protocol_status != "BLOCKED_BY_R54_14_CONSISTENCY_GUARD" else "PRECHECK_BLOCKED",
        "pause_abort_expiration_protocol_status": protocol_status,
        "pause_abort_expiration_protocol_reason_refs": reason_refs,
        "protocol_action_ref": action_ref,
        "protocol_action_refs": list(P7_R54_R15_PROTOCOL_ACTION_REFS),
        "protocol_status_refs": list(P7_R54_R15_PROTOCOL_STATUS_REFS),
        "review_can_continue_to_purge_disposal_receipt": continue_ready,
        "review_paused_without_handoff": review_paused,
        "review_aborted": review_aborted,
        "review_expired": review_expired,
        "rating_rows_incomplete": rating_incomplete,
        "abort_or_expired_requires_purge": bool(review_aborted or review_expired),
        "rating_incomplete_requires_purge": rating_incomplete,
        "purge_required_before_any_handoff": purge_required,
        "purge_before_handoff_required": True,
        "handoff_allowed_before_purge": False,
        "r52_reintake_handoff_allowed_before_purge": False,
        "body_full_local_material_must_remain_local_until_purge": True,
        "p5_decision_direction_ref": p5_direction,
        "p5_decision_materialized_here": False,
        "p5_inconclusive_direction_only_not_decision_materialized": p5_direction != "no_p5_decision_materialized_here",
        **_false_flags_except({"validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here"}),
        "body_full_packet_generated_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "actual_rating_rows_materialized_here": r14.get("actual_rating_rows_materialized_here") is True,
        "actual_blocker_rows_materialized_here": r14.get("actual_blocker_rows_materialized_here") is True,
        "actual_execution_blocker_rows_materialized_here": r14.get("actual_execution_blocker_rows_materialized_here") is True,
        "actual_question_need_observation_rows_materialized_here": r14.get("actual_question_need_observation_rows_materialized_here") is True,
        "actual_question_need_observation_summary_materialized_here": False,
        "actual_disposal_run_here": False,
        "disposal_receipt_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "post_review_summary_materialized_here": False,
        "p5_actual_review_still_not_run_by_helper": True,
        "r54_0_scope_current_received_snapshot_refrozen": True,
        "r54_1_r53_source_delta_current_snapshot_override_adopted": True,
        "r54_2_validation_evidence_intake_done": r14.get("r54_2_validation_evidence_intake_done") is True,
        "r54_3_local_only_actual_review_preflight_built": r14.get("r54_3_local_only_actual_review_preflight_built") is True,
        "r54_4_actual_review_session_envelope_built": r14.get("r54_4_actual_review_session_envelope_built") is True,
        "r54_5_24_case_manifest_freeze_built": r14.get("r54_5_24_case_manifest_freeze_built") is True,
        "r54_6_local_only_body_full_packet_generation_request_built": r14.get("r54_6_local_only_body_full_packet_generation_request_built") is True,
        "r54_7_packet_completeness_export_denylist_scan_built": r14.get("r54_7_packet_completeness_export_denylist_scan_built") is True,
        "r54_8_reviewer_instruction_rating_form_freeze_built": r14.get("r54_8_reviewer_instruction_rating_form_freeze_built") is True,
        "r54_9_actual_human_review_operation_state_capture_built": r14.get("r54_9_actual_human_review_operation_state_capture_built") is True,
        "r54_10_sanitized_actual_review_result_capture_built": r14.get("r54_10_sanitized_actual_review_result_capture_built") is True,
        "r54_11_rating_row_normalization_built": r14.get("r54_11_rating_row_normalization_built") is True,
        "r54_12_readfeel_blocker_execution_blocker_ingestion_built": r14.get("r54_12_readfeel_blocker_execution_blocker_ingestion_built") is True,
        "r54_13_question_need_observation_row_normalization_built": r14.get("r54_13_question_need_observation_row_normalization_built") is True,
        "r54_14_rating_question_observation_consistency_guard_built": r14.get("r54_14_rating_question_observation_consistency_guard_built") is True,
        "r54_15_pause_abort_expiration_protocol_built": protocol_status != "BLOCKED_BY_R54_14_CONSISTENCY_GUARD",
        "execution_blocker_ids": [] if protocol_status != "BLOCKED_BY_R54_14_CONSISTENCY_GUARD" else ["r54_15_consistency_guard_not_ready"],
        "open_execution_blocker_ids": [] if protocol_status != "BLOCKED_BY_R54_14_CONSISTENCY_GUARD" else ["r54_15_consistency_guard_not_ready"],
        "implemented_steps": list(implemented_steps),
        "not_yet_implemented_steps": list(not_yet_implemented_steps),
        "first_next_work_ref": next_required_step,
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "r54_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "validation_evidence_intake_done_here": r14.get("validation_evidence_intake_done_here") is True,
        "local_root_preflight_passed_here": r14.get("local_root_preflight_passed_here") is True,
        "explicit_allow_present_here": r14.get("explicit_allow_present_here") is True,
        "purge_plan_verified_here": r14.get("purge_plan_verified_here") is True,
    }
    assert_p7_r54_pause_abort_expiration_protocol_bodyfree_contract(material)
    return material


def assert_p7_r54_pause_abort_expiration_protocol_bodyfree_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_PAUSE_ABORT_EXPIRATION_PROTOCOL_REQUIRED_FIELD_REFS, source="p7_r54_pause_abort_expiration_protocol")
    _assert_body_free_common_with_false_keys(data, schema_version=P7_R54_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION, source="p7_r54_pause_abort_expiration_protocol", false_key_refs=P7_R54_R15_FALSE_KEY_REFS)
    _assert_current_refs(data, source="p7_r54_pause_abort_expiration_protocol")
    status = clean_identifier(data.get("pause_abort_expiration_protocol_status"), default="", max_length=140)
    if data.get("policy_section") != P7_R54_R15_STEP_REF:
        raise ValueError("R54 R15 policy section changed")
    if data.get("protocol_action_ref") not in P7_R54_R15_PROTOCOL_ACTION_REFS:
        raise ValueError("R54 R15 protocol action changed")
    if status not in P7_R54_R15_PROTOCOL_STATUS_REFS:
        raise ValueError("R54 R15 protocol status changed")
    if tuple(data.get("protocol_action_refs") or ()) != P7_R54_R15_PROTOCOL_ACTION_REFS:
        raise ValueError("R54 R15 protocol action refs changed")
    if tuple(data.get("protocol_status_refs") or ()) != P7_R54_R15_PROTOCOL_STATUS_REFS:
        raise ValueError("R54 R15 protocol status refs changed")
    if data.get("p5_decision_direction_ref") not in P7_R54_R15_P5_DECISION_DIRECTION_REFS:
        raise ValueError("R54 R15 P5 decision direction changed")
    for false_key in (
        "handoff_allowed_before_purge", "r52_reintake_handoff_allowed_before_purge", "p5_decision_materialized_here", "disposal_receipt_materialized_here", "actual_disposal_receipt_materialized_here", "post_review_summary_materialized_here", "actual_human_review_run_here", "actual_manual_review_run_here", "p6_limited_human_readfeel_start_allowed", "p8_start_allowed", "release_allowed", "api_db_rn_response_key_changed_here", "runtime_changed_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 R15 must keep {false_key}=False")
    if data.get("purge_before_handoff_required") is not True or data.get("body_full_local_material_must_remain_local_until_purge") is not True:
        raise ValueError("R54 R15 must require purge before any handoff")
    if status == "READY_FOR_PURGE_DISPOSAL_RECEIPT":
        if data.get("r14_ready_for_pause_abort_expiration_protocol") is not True or data.get("review_can_continue_to_purge_disposal_receipt") is not True:
            raise ValueError("R54 R15 continue state requires R14 ready")
        if data.get("purge_required_before_any_handoff") is not True or data.get("next_required_step") != P7_R54_R15_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R15 continue state must move to purge")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_R15_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_R15_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 R15 continue step lists changed")
    elif status in {"ABORTED_PURGE_REQUIRED", "EXPIRED_PURGE_REQUIRED", "RATING_INCOMPLETE_PURGE_REQUIRED"}:
        if data.get("purge_required_before_any_handoff") is not True or data.get("next_required_step") != P7_R54_R15_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R15 abort/expired/incomplete must move to purge")
        if data.get("p5_inconclusive_direction_only_not_decision_materialized") is not True:
            raise ValueError("R54 R15 abort/expired/incomplete must mark inconclusive direction only")
        if status in {"ABORTED_PURGE_REQUIRED", "EXPIRED_PURGE_REQUIRED"} and data.get("abort_or_expired_requires_purge") is not True:
            raise ValueError("R54 R15 abort/expired must require purge")
        if status == "RATING_INCOMPLETE_PURGE_REQUIRED" and data.get("rating_incomplete_requires_purge") is not True:
            raise ValueError("R54 R15 rating incomplete must require purge")
    elif status == "PAUSED_NO_HANDOFF_LOCAL_ONLY":
        if data.get("review_paused_without_handoff") is not True or data.get("next_required_step") != P7_R54_R15_PAUSED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R15 paused state next step changed")
        if data.get("handoff_allowed_before_purge") is not False:
            raise ValueError("R54 R15 paused state must not handoff")
    else:
        blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=80, max_length=140)
        if not blockers or data.get("next_required_step") != P7_R54_R15_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R15 blocked state next step changed")
        if data.get("r54_15_pause_abort_expiration_protocol_built") is not False:
            raise ValueError("R54 R15 blocked state must not claim protocol built")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_pause_abort_expiration_protocol")
    return True



# ---------------------------------------------------------------------------
# R54-16 / R54-17 purge/disposal receipt and body-free post-review summary
# ---------------------------------------------------------------------------

P7_R54_PURGE_EVIDENCE_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.purge_evidence_row.bodyfree.v1"
)
P7_R54_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.purge_disposal_receipt.bodyfree.v1"
)
P7_R54_BODY_FREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.body_free_post_review_summary.bodyfree.v1"
)

P7_R54_R16_STEP_REF: Final = "R54-16_purge_disposal_receipt"
P7_R54_R17_STEP_REF: Final = "R54-17_body_free_post_review_summary"
P7_R54_R16_NEXT_REQUIRED_STEP_REF: Final = P7_R54_R17_STEP_REF
P7_R54_R16_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R54-16_purge_disposal_receipt_before_R54-17_body_free_post_review_summary"
P7_R54_R17_NEXT_REQUIRED_STEP_REF: Final = "R54-18_p5_decision_candidate_separation"
P7_R54_R17_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R54-17_body_free_post_review_summary_before_R54-18_p5_decision_candidate_separation"

P7_R54_FUTURE_STEPS_AFTER_R17: Final[tuple[str, ...]] = tuple(
    step for step in P7_R54_FUTURE_STEPS_AFTER_R15 if step not in {P7_R54_R16_STEP_REF, P7_R54_R17_STEP_REF}
)
P7_R54_R16_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_R15_IMPLEMENTED_STEPS, P7_R54_R16_STEP_REF)
P7_R54_R16_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_R17_STEP_REF, *P7_R54_FUTURE_STEPS_AFTER_R17)
P7_R54_R17_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_R16_IMPLEMENTED_STEPS, P7_R54_R17_STEP_REF)
P7_R54_R17_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_FUTURE_STEPS_AFTER_R17

P7_R54_R16_PURGE_DISPOSAL_STATUS_REFS: Final[tuple[str, ...]] = (
    "READY_FOR_BODY_FREE_POST_REVIEW_SUMMARY",
    "BLOCKED_BY_R54_15_PAUSE_ABORT_EXPIRATION_PROTOCOL",
    "BLOCKED_BY_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE",
    "BLOCKED_BY_DISPOSAL_RECEIPT_VERIFICATION",
)
P7_R54_R17_POST_REVIEW_SUMMARY_STATUS_REFS: Final[tuple[str, ...]] = (
    "READY_FOR_P5_DECISION_CANDIDATE_SEPARATION",
    "BLOCKED_BY_POST_REVIEW_SUMMARY_REQUIREMENTS",
)
P7_R54_R16_READY_R15_STATUS_REFS: Final[frozenset[str]] = frozenset(
    {
        "READY_FOR_PURGE_DISPOSAL_RECEIPT",
        "ABORTED_PURGE_REQUIRED",
        "EXPIRED_PURGE_REQUIRED",
        "RATING_INCOMPLETE_PURGE_REQUIRED",
    }
)
P7_R54_R16_PURGE_REMOVAL_KIND_REFS: Final[tuple[str, ...]] = (
    "local_only_controller_verified_removed",
    "local_only_controller_verified_absent",
)
P7_R54_R16_DISPOSAL_REASON_REF_REFS: Final[tuple[str, ...]] = (
    "r54_purge_disposal_receipt_bodyfree_verified",
    "r54_pause_abort_expiration_protocol_not_ready_for_purge",
    "r54_purge_evidence_missing_or_incomplete",
    "r54_disposal_receipt_blocked",
)
P7_R54_R17_SUMMARY_REASON_REF_REFS: Final[tuple[str, ...]] = (
    "r54_body_free_post_review_summary_counts_refs_materialized",
    "r54_post_review_summary_blocked",
    "r54_disposal_not_verified_before_summary",
    "r54_rating_rows_incomplete_for_summary",
    "r54_blocker_rows_incomplete_for_summary",
    "r54_question_observation_rows_incomplete_for_summary",
    "r54_rating_question_consistency_guard_not_ready_for_summary",
)

P7_R54_R16_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_R15_FALSE_KEY_REFS
    if key
    not in {
        "disposal_receipt_materialized_here",
        "actual_disposal_receipt_materialized_here",
    }
)
P7_R54_R17_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_R16_FALSE_KEY_REFS
    if key
    not in {
        "actual_question_need_observation_summary_materialized_here",
        "post_review_summary_materialized_here",
        "disposal_receipt_materialized_here",
        "actual_disposal_receipt_materialized_here",
    }
)

P7_R54_PURGE_EVIDENCE_ROW_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "purge_target_ref",
    "purge_removal_kind_ref",
    "purge_verified",
    "removed_file_count",
    "raw_input_included",
    "returned_surface_included",
    "comment_text_included",
    "history_body_included",
    "reviewer_free_text_included",
    "question_text_included",
    "draft_question_text_included",
    "local_absolute_path_included",
    "body_content_hash_included",
    "packet_content_hash_included",
    "terminal_output_included",
    "body_free",
)

P7_R54_PURGE_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "r15_pause_abort_expiration_protocol_schema_version", "r15_pause_abort_expiration_protocol_material_ref", "r15_pause_abort_expiration_protocol_status", "r15_ready_for_purge_disposal_receipt",
    "current_received_snapshot_refs", "current_received_snapshot_ref_count", "r53_source_snapshot_refs", "r53_source_snapshot_ref_count", "r53_refs_are_current_received_refs",
    "review_session_status", "purge_disposal_receipt_status", "purge_disposal_reason_refs", "required_case_count", "required_purge_target_refs", "purge_evidence_row_schema_version", "purge_evidence_row_required_field_refs", "purge_evidence_rows", "purge_evidence_row_count", "purge_target_count", "verified_purge_target_count", "missing_purge_target_refs", "failed_purge_target_refs", "not_verified_purge_target_refs", "deleted_file_count", "purge_started_at_ref", "purge_completed_at_ref", "disposal_receipt", "disposal_status", "disposal_verified", "disposal_failed", "disposal_receipt_missing", "summary_finalize_allowed", "body_removed", "reviewer_forms_removed", "reviewer_notes_removed", "body_full_packets_removed", "local_packet_exported", "content_hash_of_body_stored", "receipt_contains_body_full_material", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included", "deleted_body_preview_included", "terminal_output_included", "local_file_delete_ops_executed_by_helper", "actual_disposal_run_here", "disposal_receipt_materialized_here", "actual_disposal_receipt_materialized_here", "post_review_summary_materialized_here", "body_full_packet_generated_here", "actual_body_full_packet_generated_here", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_question_need_observation_summary_materialized_here", "p5_actual_review_still_not_run_by_helper", "p5_human_blind_qa_confirmed_candidate", "p5_repair_return_candidate", "p5_review_inconclusive", "p6_limited_human_readfeel_start_allowed", "p8_start_allowed", "p7_complete", "release_allowed", "r54_0_scope_current_received_snapshot_refrozen", "r54_1_r53_source_delta_current_snapshot_override_adopted", "r54_2_validation_evidence_intake_done", "r54_3_local_only_actual_review_preflight_built", "r54_4_actual_review_session_envelope_built", "r54_5_24_case_manifest_freeze_built", "r54_6_local_only_body_full_packet_generation_request_built", "r54_7_packet_completeness_export_denylist_scan_built", "r54_8_reviewer_instruction_rating_form_freeze_built", "r54_9_actual_human_review_operation_state_capture_built", "r54_10_sanitized_actual_review_result_capture_built", "r54_11_rating_row_normalization_built", "r54_12_readfeel_blocker_execution_blocker_ingestion_built", "r54_13_question_need_observation_row_normalization_built", "r54_14_rating_question_observation_consistency_guard_built", "r54_15_pause_abort_expiration_protocol_built", "r54_16_purge_disposal_receipt_built", "execution_blocker_ids", "open_execution_blocker_ids", "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract", "r54_public_no_touch_contract", "body_free_markers", "body_free",
    *P7_R54_R16_FALSE_KEY_REFS,
    "validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here",
)

P7_R54_BODY_FREE_POST_REVIEW_SUMMARY_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "r16_purge_disposal_receipt_schema_version", "r16_purge_disposal_receipt_material_ref", "r16_purge_disposal_receipt_status", "r16_ready_for_post_review_summary",
    "r11_rating_row_normalization_schema_version", "r11_rating_row_normalization_material_ref", "r11_rating_row_normalizer_status", "r11_ready_for_post_review_summary",
    "r12_blocker_ingestion_schema_version", "r12_blocker_ingestion_material_ref", "r12_blocker_ingestion_status", "r12_ready_for_post_review_summary",
    "r13_question_observation_schema_version", "r13_question_observation_material_ref", "r13_question_observation_normalizer_status", "r13_ready_for_post_review_summary",
    "r14_consistency_guard_schema_version", "r14_consistency_guard_material_ref", "r14_consistency_guard_status", "r14_ready_for_post_review_summary",
    "current_received_snapshot_refs", "current_received_snapshot_ref_count", "r53_source_snapshot_refs", "r53_source_snapshot_ref_count", "r53_refs_are_current_received_refs",
    "review_session_status", "post_review_summary_status", "post_review_summary_reason_refs", "required_case_count", "all_24_cases_reviewed", "rating_row_count", "question_observation_row_count", "open_execution_blocker_count", "open_readfeel_blocker_count", "summary_contains_rating_rows", "summary_contains_question_observation_rows", "summary_contains_review_body_rows", "execution_blocker_ids", "open_execution_blocker_ids", "verdict_counts", "axis_score_averages", "axis_target_refs", "axis_target_met_refs", "axis_target_missed_refs", "all_axis_targets_met", "readfeel_blocker_counts", "execution_blocker_counts", "question_need_primary_class_counts", "ambiguity_kind_counts", "one_question_fit_counts", "repair_required_counts", "red_count", "repair_required_count", "yellow_count", "pass_count", "critical_repair_blocker_count", "repair_observation_count", "disposal_verified", "body_removed", "reviewer_forms_removed", "reviewer_notes_removed", "body_free_summary_contains_only_counts_and_refs", "raw_input_included", "returned_surface_included", "comment_text_included", "reviewer_free_text_included", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included", "terminal_output_included", "local_packet_exported", "content_hash_of_body_stored", "p5_confirmed_requirements_met_by_summary", "p5_human_blind_qa_confirmed_candidate", "p5_repair_return_candidate", "p5_review_inconclusive", "p6_limited_human_readfeel_candidate", "p6_limited_human_readfeel_start_allowed", "p8_question_design_material_candidate", "p8_start_allowed", "p7_complete", "release_allowed", "hold004_close_allowed", "p8_question_implementation_spec_finalized_here", "question_trigger_logic_implemented_here", "api_db_rn_response_key_changed_here", "runtime_changed_here", "body_full_packet_generated_here", "actual_body_full_packet_generated_here", "actual_review_run_here", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_reviewer_notes_materialized_here", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_question_need_observation_summary_materialized_here", "actual_disposal_run_here", "disposal_receipt_materialized_here", "actual_disposal_receipt_materialized_here", "post_review_summary_materialized_here", "p5_actual_review_still_not_run_by_helper", "r54_0_scope_current_received_snapshot_refrozen", "r54_1_r53_source_delta_current_snapshot_override_adopted", "r54_2_validation_evidence_intake_done", "r54_3_local_only_actual_review_preflight_built", "r54_4_actual_review_session_envelope_built", "r54_5_24_case_manifest_freeze_built", "r54_6_local_only_body_full_packet_generation_request_built", "r54_7_packet_completeness_export_denylist_scan_built", "r54_8_reviewer_instruction_rating_form_freeze_built", "r54_9_actual_human_review_operation_state_capture_built", "r54_10_sanitized_actual_review_result_capture_built", "r54_11_rating_row_normalization_built", "r54_12_readfeel_blocker_execution_blocker_ingestion_built", "r54_13_question_need_observation_row_normalization_built", "r54_14_rating_question_observation_consistency_guard_built", "r54_15_pause_abort_expiration_protocol_built", "r54_16_purge_disposal_receipt_built", "r54_17_body_free_post_review_summary_built", "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract", "r54_public_no_touch_contract", "body_free_markers", "body_free",
    *P7_R54_R17_FALSE_KEY_REFS,
    "validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here",
)


def build_p7_r54_purge_evidence_row_bodyfree(
    *,
    purge_target_ref: Any,
    purge_verified: bool = True,
    removed_file_count: int = 1,
    purge_removal_kind_ref: Any = "local_only_controller_verified_removed",
    review_session_id: Any = P7_R54_DEFAULT_REVIEW_SESSION_ID,
) -> dict[str, Any]:
    row = {
        "schema_version": P7_R54_PURGE_EVIDENCE_ROW_SCHEMA_VERSION,
        "review_session_id": _safe_review_session_id(review_session_id),
        "purge_target_ref": clean_identifier(purge_target_ref, default="unknown_purge_target", max_length=180),
        "purge_removal_kind_ref": clean_identifier(purge_removal_kind_ref, default="local_only_controller_verified_removed", max_length=160),
        "purge_verified": bool(purge_verified),
        "removed_file_count": _safe_non_negative_int_r54(removed_file_count),
        "raw_input_included": False,
        "returned_surface_included": False,
        "comment_text_included": False,
        "history_body_included": False,
        "reviewer_free_text_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_absolute_path_included": False,
        "body_content_hash_included": False,
        "packet_content_hash_included": False,
        "terminal_output_included": False,
        "body_free": True,
    }
    assert_p7_r54_purge_evidence_row_bodyfree_contract(row)
    return row


def assert_p7_r54_purge_evidence_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R54_PURGE_EVIDENCE_ROW_BODYFREE_REQUIRED_FIELD_REFS, source="p7_r54_purge_evidence_row")
    if data.get("schema_version") != P7_R54_PURGE_EVIDENCE_ROW_SCHEMA_VERSION:
        raise ValueError("R54 R16 purge evidence row schema changed")
    if data.get("purge_target_ref") not in P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS:
        raise ValueError("R54 R16 purge evidence row target changed")
    if data.get("purge_removal_kind_ref") not in P7_R54_R16_PURGE_REMOVAL_KIND_REFS:
        raise ValueError("R54 R16 purge evidence row removal kind changed")
    for false_key in (
        "raw_input_included", "returned_surface_included", "comment_text_included", "history_body_included", "reviewer_free_text_included", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included", "terminal_output_included",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 R16 purge evidence row must keep {false_key}=False")
    if data.get("body_free") is not True:
        raise ValueError("R54 R16 purge evidence row must be body-free")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_purge_evidence_row")
    return True


def _r54_purge_rows_index(rows: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for raw in rows or []:
        row = safe_mapping(raw)
        assert_p7_r54_purge_evidence_row_bodyfree_contract(row)
        target = clean_identifier(row.get("purge_target_ref"), default="", max_length=180)
        if target and target not in indexed:
            indexed[target] = row
    return indexed


def _r54_axis_score_averages_from_rating_rows(rating_rows: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    averages: dict[str, float] = {}
    rows = [safe_mapping(row) for row in rating_rows or []]
    for axis in P5_HUMAN_BLIND_QA_RATING_AXES:
        values: list[float] = []
        for row in rows:
            score_map = safe_mapping(row.get("axis_scores"))
            try:
                values.append(float(score_map.get(axis)))
            except (TypeError, ValueError):
                continue
        averages[axis] = round(sum(values) / len(values), 4) if values else 0.0
    return averages


def _r54_axis_target_split(averages: Mapping[str, Any]) -> tuple[list[str], list[str]]:
    met: list[str] = []
    missed: list[str] = []
    for axis, target in P5_HUMAN_BLIND_QA_TARGETS.items():
        try:
            average = float(averages.get(axis, 0.0))
            threshold = float(target)
        except (TypeError, ValueError):
            average = 0.0
            threshold = 1.0
        (met if average >= threshold else missed).append(str(axis))
    return met, missed


def _r54_review_rows_present_for_summary(*, rating_rows: Sequence[Mapping[str, Any]], question_rows: Sequence[Mapping[str, Any]]) -> bool:
    return len(rating_rows or []) == P7_R51_REQUIRED_CASE_COUNT and len(question_rows or []) == P7_R51_REQUIRED_CASE_COUNT


def build_p7_r54_purge_disposal_receipt_bodyfree(
    *,
    pause_abort_expiration_protocol: Mapping[str, Any] | None = None,
    r15_pause_abort_expiration_protocol: Mapping[str, Any] | None = None,
    purge_evidence_rows: Sequence[Mapping[str, Any]] | None = None,
    purge_started_at_ref: Any = "r54_local_only_purge_started_at_local_controller",
    purge_completed_at_ref: Any = "r54_local_only_purge_completed_at_local_controller",
    material_id: Any = "p7_r54_purge_disposal_receipt_bodyfree",
) -> dict[str, Any]:
    if pause_abort_expiration_protocol is not None and r15_pause_abort_expiration_protocol is not None:
        raise ValueError("provide only one R54-15 pause/abort/expiration protocol value")
    r15 = safe_mapping(
        pause_abort_expiration_protocol
        if pause_abort_expiration_protocol is not None
        else r15_pause_abort_expiration_protocol
        if r15_pause_abort_expiration_protocol is not None
        else build_p7_r54_pause_abort_expiration_protocol_bodyfree()
    )
    assert_p7_r54_pause_abort_expiration_protocol_bodyfree_contract(r15)
    r15_status = clean_identifier(r15.get("pause_abort_expiration_protocol_status"), default="BLOCKED_BY_R54_14_CONSISTENCY_GUARD", max_length=160)
    r15_ready = (
        r15_status in P7_R54_R16_READY_R15_STATUS_REFS
        and r15.get("next_required_step") == P7_R54_R15_NEXT_REQUIRED_STEP_REF
        and r15.get("purge_required_before_any_handoff") is True
        and not r15.get("execution_blocker_ids")
    )
    purge_rows = [safe_mapping(row) for row in purge_evidence_rows or []]
    indexed_rows = _r54_purge_rows_index(purge_rows)
    required_targets = list(P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS)
    verified_targets = [target for target in required_targets if safe_mapping(indexed_rows.get(target)).get("purge_verified") is True]
    missing_targets = [target for target in required_targets if target not in indexed_rows]
    failed_targets = [target for target, row in indexed_rows.items() if row.get("purge_verified") is not True]
    not_verified_targets = dedupe_identifiers([*missing_targets, *failed_targets], limit=20, max_length=180)
    all_targets_verified = len(verified_targets) == len(required_targets) and not missing_targets and not failed_targets
    ready = bool(r15_ready and all_targets_verified)
    if not r15_ready:
        status = "BLOCKED_BY_R54_15_PAUSE_ABORT_EXPIRATION_PROTOCOL"
        reason_refs = ["r54_pause_abort_expiration_protocol_not_ready_for_purge"]
        blockers = ["r54_15_pause_abort_expiration_protocol_not_ready_for_purge"]
    elif not all_targets_verified:
        status = "BLOCKED_BY_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE"
        reason_refs = ["r54_purge_evidence_missing_or_incomplete"]
        blockers = ["r54_body_full_packet_reviewer_notes_purge_not_verified"]
    else:
        status = "READY_FOR_BODY_FREE_POST_REVIEW_SUMMARY"
        reason_refs = ["r54_purge_disposal_receipt_bodyfree_verified"]
        blockers = []
    deleted_file_count = sum(_safe_non_negative_int_r54(row.get("removed_file_count")) for row in indexed_rows.values()) if ready else 0
    receipt = {
        "schema_version": P7_R54_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION,
        "review_session_id": _safe_review_session_id(r15.get("review_session_id")),
        "purge_status": "PURGE_VERIFIED_BODYFREE" if ready else "PURGE_NOT_VERIFIED_BODYFREE",
        "purge_started_at_ref": clean_identifier(purge_started_at_ref, default="r54_local_only_purge_started_at_local_controller", max_length=180),
        "purge_completed_at_ref": clean_identifier(purge_completed_at_ref, default="r54_local_only_purge_completed_at_local_controller", max_length=180),
        "removed_packet_count": 1 if ready else 0,
        "removed_notes_count": 1 if ready else 0,
        "removed_form_count": 1 if ready else 0,
        "disposal_verified": ready,
        "body_removed": ready,
        "reviewer_forms_removed": ready,
        "reviewer_notes_removed": ready,
        "body_full_packets_removed": ready,
        "local_packet_exported": False,
        "body_content_hash_included": False,
        "packet_content_hash_included": False,
        "local_absolute_path_included": False,
        "terminal_output_included": False,
        "body_free": True,
    }
    material = {
        "schema_version": P7_R54_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_STEP,
        "scope": P7_R54_SCOPE,
        "policy_kind": P7_R54_POLICY_KIND,
        "policy_section": P7_R54_R16_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_purge_disposal_receipt_bodyfree", max_length=180),
        "review_session_id": _safe_review_session_id(r15.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r15_pause_abort_expiration_protocol_schema_version": P7_R54_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION,
        "r15_pause_abort_expiration_protocol_material_ref": clean_identifier(r15.get("material_id"), default="p7_r54_pause_abort_expiration_protocol_bodyfree", max_length=180),
        "r15_pause_abort_expiration_protocol_status": r15_status,
        "r15_ready_for_purge_disposal_receipt": bool(r15_ready),
        "current_received_snapshot_refs": dict(P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "r53_source_snapshot_refs": _r53_source_snapshot_refs(None),
        "r53_source_snapshot_ref_count": len(_r53_source_snapshot_refs(None)),
        "r53_refs_are_current_received_refs": False,
        "review_session_status": "R54_PURGE_DISPOSAL_RECEIPT_VERIFIED_BODYFREE" if ready else "R54_PURGE_DISPOSAL_RECEIPT_BLOCKED",
        "purge_disposal_receipt_status": status,
        "purge_disposal_reason_refs": reason_refs,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "required_purge_target_refs": required_targets,
        "purge_evidence_row_schema_version": P7_R54_PURGE_EVIDENCE_ROW_SCHEMA_VERSION,
        "purge_evidence_row_required_field_refs": list(P7_R54_PURGE_EVIDENCE_ROW_BODYFREE_REQUIRED_FIELD_REFS),
        "purge_evidence_rows": purge_rows,
        "purge_evidence_row_count": len(purge_rows),
        "purge_target_count": len(required_targets),
        "verified_purge_target_count": len(verified_targets),
        "missing_purge_target_refs": missing_targets,
        "failed_purge_target_refs": failed_targets,
        "not_verified_purge_target_refs": not_verified_targets,
        "deleted_file_count": deleted_file_count,
        "purge_started_at_ref": clean_identifier(purge_started_at_ref, default="r54_local_only_purge_started_at_local_controller", max_length=180),
        "purge_completed_at_ref": clean_identifier(purge_completed_at_ref, default="r54_local_only_purge_completed_at_local_controller", max_length=180),
        "disposal_receipt": receipt,
        "disposal_status": "DISPOSAL_VERIFIED" if ready else "DISPOSAL_FAILED",
        "disposal_verified": ready,
        "disposal_failed": not ready,
        "disposal_receipt_missing": False if receipt else True,
        "summary_finalize_allowed": ready,
        "body_removed": ready,
        "reviewer_forms_removed": ready,
        "reviewer_notes_removed": ready,
        "body_full_packets_removed": ready,
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "receipt_contains_body_full_material": False,
        "local_absolute_path_included": False,
        "body_content_hash_included": False,
        "packet_content_hash_included": False,
        "deleted_body_preview_included": False,
        "terminal_output_included": False,
        "local_file_delete_ops_executed_by_helper": False,
        "actual_disposal_run_here": False,
        "disposal_receipt_materialized_here": ready,
        "actual_disposal_receipt_materialized_here": ready,
        "post_review_summary_materialized_here": False,
        "body_full_packet_generated_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "actual_rating_rows_materialized_here": r15.get("actual_rating_rows_materialized_here") is True,
        "actual_blocker_rows_materialized_here": r15.get("actual_blocker_rows_materialized_here") is True,
        "actual_execution_blocker_rows_materialized_here": r15.get("actual_execution_blocker_rows_materialized_here") is True,
        "actual_question_need_observation_rows_materialized_here": r15.get("actual_question_need_observation_rows_materialized_here") is True,
        "actual_question_need_observation_summary_materialized_here": False,
        "p5_actual_review_still_not_run_by_helper": True,
        "p5_human_blind_qa_confirmed_candidate": False,
        "p5_repair_return_candidate": False,
        "p5_review_inconclusive": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "r54_0_scope_current_received_snapshot_refrozen": True,
        "r54_1_r53_source_delta_current_snapshot_override_adopted": True,
        "r54_2_validation_evidence_intake_done": r15.get("r54_2_validation_evidence_intake_done") is True,
        "r54_3_local_only_actual_review_preflight_built": r15.get("r54_3_local_only_actual_review_preflight_built") is True,
        "r54_4_actual_review_session_envelope_built": r15.get("r54_4_actual_review_session_envelope_built") is True,
        "r54_5_24_case_manifest_freeze_built": r15.get("r54_5_24_case_manifest_freeze_built") is True,
        "r54_6_local_only_body_full_packet_generation_request_built": r15.get("r54_6_local_only_body_full_packet_generation_request_built") is True,
        "r54_7_packet_completeness_export_denylist_scan_built": r15.get("r54_7_packet_completeness_export_denylist_scan_built") is True,
        "r54_8_reviewer_instruction_rating_form_freeze_built": r15.get("r54_8_reviewer_instruction_rating_form_freeze_built") is True,
        "r54_9_actual_human_review_operation_state_capture_built": r15.get("r54_9_actual_human_review_operation_state_capture_built") is True,
        "r54_10_sanitized_actual_review_result_capture_built": r15.get("r54_10_sanitized_actual_review_result_capture_built") is True,
        "r54_11_rating_row_normalization_built": r15.get("r54_11_rating_row_normalization_built") is True,
        "r54_12_readfeel_blocker_execution_blocker_ingestion_built": r15.get("r54_12_readfeel_blocker_execution_blocker_ingestion_built") is True,
        "r54_13_question_need_observation_row_normalization_built": r15.get("r54_13_question_need_observation_row_normalization_built") is True,
        "r54_14_rating_question_observation_consistency_guard_built": r15.get("r54_14_rating_question_observation_consistency_guard_built") is True,
        "r54_15_pause_abort_expiration_protocol_built": r15.get("r54_15_pause_abort_expiration_protocol_built") is True,
        "r54_16_purge_disposal_receipt_built": ready,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "implemented_steps": list(P7_R54_R16_IMPLEMENTED_STEPS if ready else P7_R54_R15_IMPLEMENTED_STEPS if r15_ready else P7_R54_R14_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_R16_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_R15_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R54_R16_NEXT_REQUIRED_STEP_REF if ready else P7_R54_R16_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "next_required_step": P7_R54_R16_NEXT_REQUIRED_STEP_REF if ready else P7_R54_R16_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_except({"validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "disposal_receipt_materialized_here", "actual_disposal_receipt_materialized_here"}),
        "validation_evidence_intake_done_here": r15.get("validation_evidence_intake_done_here") is True,
        "local_root_preflight_passed_here": r15.get("local_root_preflight_passed_here") is True,
        "explicit_allow_present_here": r15.get("explicit_allow_present_here") is True,
        "purge_plan_verified_here": r15.get("purge_plan_verified_here") is True,
    }
    # Restore the values that may have been overwritten by the false flag fill.
    material["actual_rating_rows_materialized_here"] = r15.get("actual_rating_rows_materialized_here") is True
    material["actual_blocker_rows_materialized_here"] = r15.get("actual_blocker_rows_materialized_here") is True
    material["actual_execution_blocker_rows_materialized_here"] = r15.get("actual_execution_blocker_rows_materialized_here") is True
    material["actual_question_need_observation_rows_materialized_here"] = r15.get("actual_question_need_observation_rows_materialized_here") is True
    material["disposal_receipt_materialized_here"] = ready
    material["actual_disposal_receipt_materialized_here"] = ready
    assert_p7_r54_purge_disposal_receipt_bodyfree_contract(material)
    return material


def assert_p7_r54_purge_disposal_receipt_bodyfree_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_PURGE_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS, source="p7_r54_purge_disposal_receipt")
    _assert_body_free_common_with_false_keys(data, schema_version=P7_R54_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION, source="p7_r54_purge_disposal_receipt", false_key_refs=P7_R54_R16_FALSE_KEY_REFS)
    _assert_current_refs(data, source="p7_r54_purge_disposal_receipt")
    if data.get("policy_section") != P7_R54_R16_STEP_REF:
        raise ValueError("R54 R16 policy section changed")
    status = clean_identifier(data.get("purge_disposal_receipt_status"), default="", max_length=160)
    if status not in P7_R54_R16_PURGE_DISPOSAL_STATUS_REFS:
        raise ValueError("R54 R16 purge/disposal status changed")
    for row in data.get("purge_evidence_rows") or []:
        assert_p7_r54_purge_evidence_row_bodyfree_contract(safe_mapping(row))
    if tuple(data.get("required_purge_target_refs") or ()) != P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS:
        raise ValueError("R54 R16 required purge target refs changed")
    if data.get("purge_evidence_row_count") != len(data.get("purge_evidence_rows") or []):
        raise ValueError("R54 R16 purge evidence row count mismatch")
    if data.get("purge_target_count") != len(P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS):
        raise ValueError("R54 R16 purge target count changed")
    for false_key in (
        "local_packet_exported", "content_hash_of_body_stored", "receipt_contains_body_full_material", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included", "deleted_body_preview_included", "terminal_output_included", "local_file_delete_ops_executed_by_helper", "actual_disposal_run_here", "post_review_summary_materialized_here", "body_full_packet_generated_here", "actual_body_full_packet_generated_here", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_question_need_observation_summary_materialized_here", "p5_human_blind_qa_confirmed_candidate", "p5_repair_return_candidate", "p5_review_inconclusive", "p6_limited_human_readfeel_start_allowed", "p8_start_allowed", "p7_complete", "release_allowed",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 R16 must keep {false_key}=False")
    ready = status == "READY_FOR_BODY_FREE_POST_REVIEW_SUMMARY"
    if ready:
        for true_key in ("r15_ready_for_purge_disposal_receipt", "disposal_verified", "summary_finalize_allowed", "body_removed", "reviewer_forms_removed", "reviewer_notes_removed", "body_full_packets_removed", "disposal_receipt_materialized_here", "actual_disposal_receipt_materialized_here", "r54_16_purge_disposal_receipt_built"):
            if data.get(true_key) is not True:
                raise ValueError(f"R54 R16 ready material must keep {true_key}=True")
        if data.get("verified_purge_target_count") != data.get("purge_target_count") or data.get("missing_purge_target_refs") or data.get("failed_purge_target_refs") or data.get("not_verified_purge_target_refs"):
            raise ValueError("R54 R16 ready material must verify all purge targets")
        if data.get("next_required_step") != P7_R54_R16_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R16 ready next step changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_R16_IMPLEMENTED_STEPS:
            raise ValueError("R54 R16 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_R16_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 R16 not-yet steps changed")
    else:
        if data.get("disposal_verified") is not False or data.get("disposal_failed") is not True:
            raise ValueError("R54 R16 blocked material must not verify disposal")
        if data.get("disposal_receipt_materialized_here") is not False or data.get("actual_disposal_receipt_materialized_here") is not False:
            raise ValueError("R54 R16 blocked material must not materialize receipt")
        if not data.get("execution_blocker_ids"):
            raise ValueError("R54 R16 blocked material requires execution blockers")
        if data.get("next_required_step") != P7_R54_R16_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R16 blocked next step changed")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_purge_disposal_receipt")
    return True


def build_p7_r54_body_free_post_review_summary_bodyfree(
    *,
    purge_disposal_receipt: Mapping[str, Any] | None = None,
    r16_purge_disposal_receipt: Mapping[str, Any] | None = None,
    rating_row_normalization: Mapping[str, Any] | None = None,
    r11_rating_row_normalization: Mapping[str, Any] | None = None,
    readfeel_blocker_execution_blocker_ingestion: Mapping[str, Any] | None = None,
    r12_readfeel_blocker_execution_blocker_ingestion: Mapping[str, Any] | None = None,
    question_need_observation_row_normalization: Mapping[str, Any] | None = None,
    r13_question_need_observation_row_normalization: Mapping[str, Any] | None = None,
    rating_question_observation_consistency_guard: Mapping[str, Any] | None = None,
    r14_rating_question_observation_consistency_guard: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_body_free_post_review_summary_bodyfree",
) -> dict[str, Any]:
    if purge_disposal_receipt is not None and r16_purge_disposal_receipt is not None:
        raise ValueError("provide only one R54-16 purge/disposal receipt value")
    if rating_row_normalization is not None and r11_rating_row_normalization is not None:
        raise ValueError("provide only one R54-11 rating normalization value")
    if readfeel_blocker_execution_blocker_ingestion is not None and r12_readfeel_blocker_execution_blocker_ingestion is not None:
        raise ValueError("provide only one R54-12 blocker ingestion value")
    if question_need_observation_row_normalization is not None and r13_question_need_observation_row_normalization is not None:
        raise ValueError("provide only one R54-13 question observation value")
    if rating_question_observation_consistency_guard is not None and r14_rating_question_observation_consistency_guard is not None:
        raise ValueError("provide only one R54-14 consistency guard value")
    r16 = safe_mapping(purge_disposal_receipt if purge_disposal_receipt is not None else r16_purge_disposal_receipt if r16_purge_disposal_receipt is not None else build_p7_r54_purge_disposal_receipt_bodyfree())
    r11 = safe_mapping(rating_row_normalization if rating_row_normalization is not None else r11_rating_row_normalization if r11_rating_row_normalization is not None else build_p7_r54_rating_row_normalization_bodyfree())
    r12 = safe_mapping(readfeel_blocker_execution_blocker_ingestion if readfeel_blocker_execution_blocker_ingestion is not None else r12_readfeel_blocker_execution_blocker_ingestion if r12_readfeel_blocker_execution_blocker_ingestion is not None else build_p7_r54_readfeel_blocker_execution_blocker_ingestion_bodyfree(rating_row_normalization=r11))
    r13 = safe_mapping(question_need_observation_row_normalization if question_need_observation_row_normalization is not None else r13_question_need_observation_row_normalization if r13_question_need_observation_row_normalization is not None else build_p7_r54_question_need_observation_row_normalization_bodyfree(readfeel_blocker_execution_blocker_ingestion=r12))
    r14 = safe_mapping(rating_question_observation_consistency_guard if rating_question_observation_consistency_guard is not None else r14_rating_question_observation_consistency_guard if r14_rating_question_observation_consistency_guard is not None else build_p7_r54_rating_question_observation_consistency_guard_bodyfree(question_need_observation_row_normalization=r13, rating_row_normalization=r11))
    assert_p7_r54_purge_disposal_receipt_bodyfree_contract(r16)
    assert_p7_r54_rating_row_normalization_bodyfree_contract(r11)
    assert_p7_r54_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(r12)
    assert_p7_r54_question_need_observation_row_normalization_bodyfree_contract(r13)
    assert_p7_r54_rating_question_observation_consistency_guard_bodyfree_contract(r14)
    r16_ready = r16.get("purge_disposal_receipt_status") == "READY_FOR_BODY_FREE_POST_REVIEW_SUMMARY" and not r16.get("execution_blocker_ids")
    r11_ready = r11.get("rating_row_normalizer_status") == "READY_FOR_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION" and not r11.get("execution_blocker_ids")
    r12_ready = r12.get("blocker_ingestion_status") == "READY_FOR_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION" and not r12.get("execution_blocker_ids")
    r13_ready = r13.get("question_observation_normalizer_status") == "READY_FOR_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD" and not r13.get("execution_blocker_ids")
    r14_ready = r14.get("rating_question_consistency_guard_status") == "READY_FOR_PAUSE_ABORT_EXPIRATION_PROTOCOL" and not r14.get("execution_blocker_ids")
    rating_rows = [safe_mapping(row) for row in r11.get("rating_rows") or []] if r11_ready else []
    question_rows = [safe_mapping(row) for row in r13.get("question_need_observation_rows") or []] if r13_ready else []
    all_24 = _r54_review_rows_present_for_summary(rating_rows=rating_rows, question_rows=question_rows)
    blockers: list[str] = []
    if not r16_ready:
        blockers.append("r54_disposal_not_verified_before_summary")
    if not r11_ready or _safe_non_negative_int_r54(r11.get("rating_row_count")) != P7_R51_REQUIRED_CASE_COUNT:
        blockers.append("r54_rating_rows_incomplete_for_summary")
    if not r12_ready:
        blockers.append("r54_blocker_rows_incomplete_for_summary")
    if not r13_ready or _safe_non_negative_int_r54(r13.get("question_observation_row_count")) != P7_R51_REQUIRED_CASE_COUNT:
        blockers.append("r54_question_observation_rows_incomplete_for_summary")
    if not r14_ready:
        blockers.append("r54_rating_question_consistency_guard_not_ready_for_summary")
    if not all_24:
        blockers.append("r54_all_24_cases_not_reviewed_for_summary")
    blockers = dedupe_identifiers(blockers, limit=80, max_length=180)
    summary_ready = bool(r16_ready and r11_ready and r12_ready and r13_ready and r14_ready and all_24 and not blockers)
    verdict_counts = dict(safe_mapping(r11.get("verdict_counts"))) if r11_ready else _r54_verdict_counts(())
    axis_averages = _r54_axis_score_averages_from_rating_rows(rating_rows) if r11_ready else {axis: 0.0 for axis in P5_HUMAN_BLIND_QA_RATING_AXES}
    axis_met, axis_missed = _r54_axis_target_split(axis_averages)
    readfeel_blocker_counts = dict(safe_mapping(r12.get("readfeel_blocker_counts"))) if r12_ready else {}
    execution_blocker_counts = dict(safe_mapping(r12.get("execution_blocker_counts"))) if r12_ready else {}
    question_primary_counts = dict(safe_mapping(r13.get("question_need_primary_class_counts"))) if r13_ready else {}
    ambiguity_counts = dict(safe_mapping(r13.get("ambiguity_kind_counts"))) if r13_ready else {}
    one_question_counts = dict(safe_mapping(r13.get("one_question_fit_counts"))) if r13_ready else {}
    repair_counts = dict(safe_mapping(r13.get("repair_required_counts"))) if r13_ready else {}
    red_count = _safe_non_negative_int_r54(verdict_counts.get("RED"))
    repair_required_count = _safe_non_negative_int_r54(verdict_counts.get("REPAIR_REQUIRED"))
    yellow_count = _safe_non_negative_int_r54(verdict_counts.get("YELLOW"))
    pass_count = _safe_non_negative_int_r54(verdict_counts.get("PASS"))
    critical_repair_blocker_count = sum(_safe_non_negative_int_r54(value) for value in readfeel_blocker_counts.values())
    repair_observation_count = sum(
        _safe_non_negative_int_r54(repair_counts.get(ref))
        for ref in ("emlis_readfeel_repair_required", "p5_surface_repair_required", "gate_boundary_repair_required")
    )
    open_execution_count = _safe_non_negative_int_r54(r12.get("open_execution_blocker_count")) if r12_ready else 0
    open_readfeel_count = _safe_non_negative_int_r54(r12.get("open_readfeel_blocker_count")) if r12_ready else 0
    p5_confirmed_requirements_met_by_summary = bool(
        summary_ready
        and open_execution_count == 0
        and open_readfeel_count == 0
        and red_count == 0
        and repair_required_count == 0
        and yellow_count == 0
        and not axis_missed
        and r16.get("disposal_verified") is True
    )
    reason_refs = ["r54_body_free_post_review_summary_counts_refs_materialized"] if summary_ready else dedupe_identifiers(["r54_post_review_summary_blocked", *blockers], limit=80, max_length=180)
    material = {
        "schema_version": P7_R54_BODY_FREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_STEP,
        "scope": P7_R54_SCOPE,
        "policy_kind": P7_R54_POLICY_KIND,
        "policy_section": P7_R54_R17_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_body_free_post_review_summary_bodyfree", max_length=180),
        "review_session_id": _safe_review_session_id(r16.get("review_session_id") or r11.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r16_purge_disposal_receipt_schema_version": P7_R54_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION,
        "r16_purge_disposal_receipt_material_ref": clean_identifier(r16.get("material_id"), default="p7_r54_purge_disposal_receipt_bodyfree", max_length=180),
        "r16_purge_disposal_receipt_status": clean_identifier(r16.get("purge_disposal_receipt_status"), default="BLOCKED_BY_DISPOSAL_RECEIPT_VERIFICATION", max_length=180),
        "r16_ready_for_post_review_summary": bool(r16_ready),
        "r11_rating_row_normalization_schema_version": P7_R54_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        "r11_rating_row_normalization_material_ref": clean_identifier(r11.get("material_id"), default="p7_r54_rating_row_normalization_bodyfree", max_length=180),
        "r11_rating_row_normalizer_status": clean_identifier(r11.get("rating_row_normalizer_status"), default="BLOCKED_BY_R54_10_SANITIZED_CAPTURE", max_length=180),
        "r11_ready_for_post_review_summary": bool(r11_ready),
        "r12_blocker_ingestion_schema_version": P7_R54_READFEEL_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION,
        "r12_blocker_ingestion_material_ref": clean_identifier(r12.get("material_id"), default="p7_r54_readfeel_blocker_execution_blocker_ingestion_bodyfree", max_length=180),
        "r12_blocker_ingestion_status": clean_identifier(r12.get("blocker_ingestion_status"), default="BLOCKED_BY_R54_11_RATING_ROW_NORMALIZATION", max_length=180),
        "r12_ready_for_post_review_summary": bool(r12_ready),
        "r13_question_observation_schema_version": P7_R54_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION_SCHEMA_VERSION,
        "r13_question_observation_material_ref": clean_identifier(r13.get("material_id"), default="p7_r54_question_need_observation_row_normalization_bodyfree", max_length=180),
        "r13_question_observation_normalizer_status": clean_identifier(r13.get("question_observation_normalizer_status"), default="BLOCKED_BY_R54_12_OR_R54_10_PRECHECK", max_length=180),
        "r13_ready_for_post_review_summary": bool(r13_ready),
        "r14_consistency_guard_schema_version": P7_R54_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        "r14_consistency_guard_material_ref": clean_identifier(r14.get("material_id"), default="p7_r54_rating_question_observation_consistency_guard_bodyfree", max_length=180),
        "r14_consistency_guard_status": clean_identifier(r14.get("rating_question_consistency_guard_status"), default="BLOCKED_BY_R54_13_OR_R54_11_PRECHECK", max_length=180),
        "r14_ready_for_post_review_summary": bool(r14_ready),
        "current_received_snapshot_refs": dict(P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "r53_source_snapshot_refs": _r53_source_snapshot_refs(None),
        "r53_source_snapshot_ref_count": len(_r53_source_snapshot_refs(None)),
        "r53_refs_are_current_received_refs": False,
        "review_session_status": "R54_BODY_FREE_POST_REVIEW_SUMMARY_READY" if summary_ready else "R54_BODY_FREE_POST_REVIEW_SUMMARY_BLOCKED",
        "post_review_summary_status": "READY_FOR_P5_DECISION_CANDIDATE_SEPARATION" if summary_ready else "BLOCKED_BY_POST_REVIEW_SUMMARY_REQUIREMENTS",
        "post_review_summary_reason_refs": reason_refs,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "all_24_cases_reviewed": bool(summary_ready and all_24),
        "rating_row_count": len(rating_rows) if r11_ready else _safe_non_negative_int_r54(r11.get("rating_row_count")),
        "question_observation_row_count": len(question_rows) if r13_ready else _safe_non_negative_int_r54(r13.get("question_observation_row_count")),
        "open_execution_blocker_count": open_execution_count,
        "open_readfeel_blocker_count": open_readfeel_count,
        "summary_contains_rating_rows": False,
        "summary_contains_question_observation_rows": False,
        "summary_contains_review_body_rows": False,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "verdict_counts": verdict_counts,
        "axis_score_averages": axis_averages,
        "axis_target_refs": dict(P5_HUMAN_BLIND_QA_TARGETS),
        "axis_target_met_refs": axis_met,
        "axis_target_missed_refs": axis_missed,
        "all_axis_targets_met": bool(summary_ready and not axis_missed),
        "readfeel_blocker_counts": readfeel_blocker_counts,
        "execution_blocker_counts": execution_blocker_counts,
        "question_need_primary_class_counts": question_primary_counts,
        "ambiguity_kind_counts": ambiguity_counts,
        "one_question_fit_counts": one_question_counts,
        "repair_required_counts": repair_counts,
        "red_count": red_count,
        "repair_required_count": repair_required_count,
        "yellow_count": yellow_count,
        "pass_count": pass_count,
        "critical_repair_blocker_count": critical_repair_blocker_count,
        "repair_observation_count": repair_observation_count,
        "disposal_verified": bool(summary_ready and r16.get("disposal_verified") is True),
        "body_removed": bool(summary_ready and r16.get("body_removed") is True),
        "reviewer_forms_removed": bool(summary_ready and r16.get("reviewer_forms_removed") is True),
        "reviewer_notes_removed": bool(summary_ready and r16.get("reviewer_notes_removed") is True),
        "body_free_summary_contains_only_counts_and_refs": bool(summary_ready),
        "raw_input_included": False,
        "returned_surface_included": False,
        "comment_text_included": False,
        "reviewer_free_text_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_absolute_path_included": False,
        "body_content_hash_included": False,
        "packet_content_hash_included": False,
        "terminal_output_included": False,
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "p5_confirmed_requirements_met_by_summary": p5_confirmed_requirements_met_by_summary,
        "p5_human_blind_qa_confirmed_candidate": False,
        "p5_repair_return_candidate": False,
        "p5_review_inconclusive": False,
        "p6_limited_human_readfeel_candidate": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_question_design_material_candidate": False,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "hold004_close_allowed": False,
        "p8_question_implementation_spec_finalized_here": False,
        "question_trigger_logic_implemented_here": False,
        "api_db_rn_response_key_changed_here": False,
        "runtime_changed_here": False,
        "body_full_packet_generated_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_review_run_here": bool(summary_ready and all_24),
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "actual_rating_rows_materialized_here": bool(summary_ready and r11.get("actual_rating_rows_materialized_here") is True),
        "actual_blocker_rows_materialized_here": bool(summary_ready and r12.get("actual_blocker_rows_materialized_here") is True),
        "actual_execution_blocker_rows_materialized_here": bool(summary_ready and r12.get("actual_execution_blocker_rows_materialized_here") is True),
        "actual_question_need_observation_rows_materialized_here": bool(summary_ready and r13.get("actual_question_need_observation_rows_materialized_here") is True),
        "actual_question_need_observation_summary_materialized_here": bool(summary_ready),
        "actual_disposal_run_here": False,
        "disposal_receipt_materialized_here": bool(summary_ready and r16.get("disposal_receipt_materialized_here") is True),
        "actual_disposal_receipt_materialized_here": bool(summary_ready and r16.get("actual_disposal_receipt_materialized_here") is True),
        "post_review_summary_materialized_here": bool(summary_ready),
        "p5_actual_review_still_not_run_by_helper": True,
        "r54_0_scope_current_received_snapshot_refrozen": True,
        "r54_1_r53_source_delta_current_snapshot_override_adopted": True,
        "r54_2_validation_evidence_intake_done": r16.get("r54_2_validation_evidence_intake_done") is True and r11.get("r54_2_validation_evidence_intake_done") is True,
        "r54_3_local_only_actual_review_preflight_built": r16.get("r54_3_local_only_actual_review_preflight_built") is True and r11.get("r54_3_local_only_actual_review_preflight_built") is True,
        "r54_4_actual_review_session_envelope_built": r16.get("r54_4_actual_review_session_envelope_built") is True and r11.get("r54_4_actual_review_session_envelope_built") is True,
        "r54_5_24_case_manifest_freeze_built": r16.get("r54_5_24_case_manifest_freeze_built") is True and r11.get("r54_5_24_case_manifest_freeze_built") is True,
        "r54_6_local_only_body_full_packet_generation_request_built": r16.get("r54_6_local_only_body_full_packet_generation_request_built") is True and r11.get("r54_6_local_only_body_full_packet_generation_request_built") is True,
        "r54_7_packet_completeness_export_denylist_scan_built": r16.get("r54_7_packet_completeness_export_denylist_scan_built") is True and r11.get("r54_7_packet_completeness_export_denylist_scan_built") is True,
        "r54_8_reviewer_instruction_rating_form_freeze_built": r16.get("r54_8_reviewer_instruction_rating_form_freeze_built") is True and r11.get("r54_8_reviewer_instruction_rating_form_freeze_built") is True,
        "r54_9_actual_human_review_operation_state_capture_built": r16.get("r54_9_actual_human_review_operation_state_capture_built") is True and r11.get("r54_9_actual_human_review_operation_state_capture_built") is True,
        "r54_10_sanitized_actual_review_result_capture_built": r16.get("r54_10_sanitized_actual_review_result_capture_built") is True and r11.get("r54_10_sanitized_actual_review_result_capture_built") is True,
        "r54_11_rating_row_normalization_built": r16.get("r54_11_rating_row_normalization_built") is True and r11.get("r54_11_rating_row_normalization_built") is True,
        "r54_12_readfeel_blocker_execution_blocker_ingestion_built": r16.get("r54_12_readfeel_blocker_execution_blocker_ingestion_built") is True and r12.get("r54_12_readfeel_blocker_execution_blocker_ingestion_built") is True,
        "r54_13_question_need_observation_row_normalization_built": r16.get("r54_13_question_need_observation_row_normalization_built") is True and r13.get("r54_13_question_need_observation_row_normalization_built") is True,
        "r54_14_rating_question_observation_consistency_guard_built": r16.get("r54_14_rating_question_observation_consistency_guard_built") is True and r14.get("r54_14_rating_question_observation_consistency_guard_built") is True,
        "r54_15_pause_abort_expiration_protocol_built": r16.get("r54_15_pause_abort_expiration_protocol_built") is True,
        "r54_16_purge_disposal_receipt_built": r16.get("r54_16_purge_disposal_receipt_built") is True,
        "r54_17_body_free_post_review_summary_built": summary_ready,
        "implemented_steps": list(P7_R54_R17_IMPLEMENTED_STEPS if summary_ready else P7_R54_R16_IMPLEMENTED_STEPS if r16_ready else P7_R54_R15_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_R17_NOT_YET_IMPLEMENTED_STEPS if summary_ready else P7_R54_R16_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R54_R17_NEXT_REQUIRED_STEP_REF if summary_ready else P7_R54_R17_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "next_required_step": P7_R54_R17_NEXT_REQUIRED_STEP_REF if summary_ready else P7_R54_R17_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_except({"validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_question_need_observation_summary_materialized_here", "disposal_receipt_materialized_here", "actual_disposal_receipt_materialized_here", "post_review_summary_materialized_here"}),
        "validation_evidence_intake_done_here": r16.get("validation_evidence_intake_done_here") is True and r11.get("validation_evidence_intake_done_here") is True,
        "local_root_preflight_passed_here": r16.get("local_root_preflight_passed_here") is True and r11.get("local_root_preflight_passed_here") is True,
        "explicit_allow_present_here": r16.get("explicit_allow_present_here") is True and r11.get("explicit_allow_present_here") is True,
        "purge_plan_verified_here": r16.get("purge_plan_verified_here") is True and r11.get("purge_plan_verified_here") is True,
    }
    for key in (
        "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_question_need_observation_summary_materialized_here", "disposal_receipt_materialized_here", "actual_disposal_receipt_materialized_here", "post_review_summary_materialized_here",
    ):
        material[key] = bool(material.get(key))
    assert_p7_r54_body_free_post_review_summary_bodyfree_contract(material)
    return material


def assert_p7_r54_body_free_post_review_summary_bodyfree_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_BODY_FREE_POST_REVIEW_SUMMARY_REQUIRED_FIELD_REFS, source="p7_r54_body_free_post_review_summary")
    _assert_body_free_common_with_false_keys(data, schema_version=P7_R54_BODY_FREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION, source="p7_r54_body_free_post_review_summary", false_key_refs=P7_R54_R17_FALSE_KEY_REFS)
    _assert_current_refs(data, source="p7_r54_body_free_post_review_summary")
    if data.get("policy_section") != P7_R54_R17_STEP_REF:
        raise ValueError("R54 R17 policy section changed")
    status = clean_identifier(data.get("post_review_summary_status"), default="", max_length=160)
    if status not in P7_R54_R17_POST_REVIEW_SUMMARY_STATUS_REFS:
        raise ValueError("R54 R17 summary status changed")
    for false_key in (
        "summary_contains_rating_rows", "summary_contains_question_observation_rows", "summary_contains_review_body_rows", "raw_input_included", "returned_surface_included", "comment_text_included", "reviewer_free_text_included", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included", "terminal_output_included", "local_packet_exported", "content_hash_of_body_stored", "p5_human_blind_qa_confirmed_candidate", "p5_repair_return_candidate", "p5_review_inconclusive", "p6_limited_human_readfeel_candidate", "p6_limited_human_readfeel_start_allowed", "p8_question_design_material_candidate", "p8_start_allowed", "p7_complete", "release_allowed", "hold004_close_allowed", "p8_question_implementation_spec_finalized_here", "question_trigger_logic_implemented_here", "api_db_rn_response_key_changed_here", "runtime_changed_here", "body_full_packet_generated_here", "actual_body_full_packet_generated_here", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_disposal_run_here", "actual_reviewer_notes_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 R17 must keep {false_key}=False")
    ready = status == "READY_FOR_P5_DECISION_CANDIDATE_SEPARATION"
    if ready:
        for true_key in (
            "r16_ready_for_post_review_summary", "r11_ready_for_post_review_summary", "r12_ready_for_post_review_summary", "r13_ready_for_post_review_summary", "r14_ready_for_post_review_summary", "all_24_cases_reviewed", "disposal_verified", "body_removed", "reviewer_forms_removed", "reviewer_notes_removed", "body_free_summary_contains_only_counts_and_refs", "actual_review_run_here", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_question_need_observation_summary_materialized_here", "disposal_receipt_materialized_here", "actual_disposal_receipt_materialized_here", "post_review_summary_materialized_here", "r54_17_body_free_post_review_summary_built",
        ):
            if data.get(true_key) is not True:
                raise ValueError(f"R54 R17 ready material must keep {true_key}=True")
        if data.get("rating_row_count") != P7_R51_REQUIRED_CASE_COUNT or data.get("question_observation_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R54 R17 ready summary requires all 24 rating/question rows")
        if data.get("body_free_summary_contains_only_counts_and_refs") is not True:
            raise ValueError("R54 R17 summary must contain only counts and refs")
        if data.get("next_required_step") != P7_R54_R17_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R17 ready next step changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_R17_IMPLEMENTED_STEPS:
            raise ValueError("R54 R17 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_R17_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 R17 not-yet steps changed")
    else:
        if data.get("body_free_summary_contains_only_counts_and_refs") is not False or data.get("post_review_summary_materialized_here") is not False:
            raise ValueError("R54 R17 blocked summary must not materialize post-review summary")
        if not data.get("execution_blocker_ids"):
            raise ValueError("R54 R17 blocked summary requires blockers")
        if data.get("next_required_step") != P7_R54_R17_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R17 blocked next step changed")
    if not isinstance(data.get("verdict_counts"), Mapping) or not isinstance(data.get("axis_score_averages"), Mapping):
        raise ValueError("R54 R17 summary counts must be mappings")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_body_free_post_review_summary")
    return True


# Compatibility aliases matching the shorter R54-16/R54-17 design wording.
build_p7_r54_purge_evidence_row = build_p7_r54_purge_evidence_row_bodyfree
assert_p7_r54_purge_evidence_row_contract = assert_p7_r54_purge_evidence_row_bodyfree_contract
build_p7_r54_purge_disposal_receipt = build_p7_r54_purge_disposal_receipt_bodyfree
assert_p7_r54_purge_disposal_receipt_contract = assert_p7_r54_purge_disposal_receipt_bodyfree_contract
build_p7_r54_body_free_post_review_summary = build_p7_r54_body_free_post_review_summary_bodyfree
assert_p7_r54_body_free_post_review_summary_contract = assert_p7_r54_body_free_post_review_summary_bodyfree_contract


# Compatibility aliases matching the shorter R54-14/R54-15 design wording.
build_p7_r54_rating_question_consistency_issue_row = build_p7_r54_rating_question_consistency_issue_row_bodyfree
assert_p7_r54_rating_question_consistency_issue_row_contract = assert_p7_r54_rating_question_consistency_issue_row_bodyfree_contract
build_p7_r54_rating_question_observation_consistency_guard = build_p7_r54_rating_question_observation_consistency_guard_bodyfree
assert_p7_r54_rating_question_observation_consistency_guard_contract = assert_p7_r54_rating_question_observation_consistency_guard_bodyfree_contract
build_p7_r54_pause_abort_expiration_protocol = build_p7_r54_pause_abort_expiration_protocol_bodyfree
assert_p7_r54_pause_abort_expiration_protocol_contract = assert_p7_r54_pause_abort_expiration_protocol_bodyfree_contract




# Compatibility aliases matching the shorter R54-12/R54-13 design wording.
build_p7_r54_readfeel_blocker_row = build_p7_r54_readfeel_blocker_row_bodyfree
assert_p7_r54_readfeel_blocker_row_contract = assert_p7_r54_readfeel_blocker_row_bodyfree_contract
build_p7_r54_execution_blocker_row = build_p7_r54_execution_blocker_row_bodyfree
assert_p7_r54_execution_blocker_row_contract = assert_p7_r54_execution_blocker_row_bodyfree_contract
build_p7_r54_readfeel_blocker_execution_blocker_ingestion = build_p7_r54_readfeel_blocker_execution_blocker_ingestion_bodyfree
assert_p7_r54_readfeel_blocker_execution_blocker_ingestion_contract = assert_p7_r54_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract
build_p7_r54_question_need_observation_row = build_p7_r54_question_need_observation_row_bodyfree
assert_p7_r54_question_need_observation_row_contract = assert_p7_r54_question_need_observation_row_bodyfree_contract
build_p7_r54_question_need_observation_row_normalization = build_p7_r54_question_need_observation_row_normalization_bodyfree
assert_p7_r54_question_need_observation_row_normalization_contract = assert_p7_r54_question_need_observation_row_normalization_bodyfree_contract


# Compatibility aliases matching the shorter R54-10/R54-11 design wording.
build_p7_r54_sanitized_review_result_row = build_p7_r54_sanitized_review_result_row_bodyfree
assert_p7_r54_sanitized_review_result_row_contract = assert_p7_r54_sanitized_review_result_row_bodyfree_contract
build_p7_r54_sanitized_actual_review_result_capture = build_p7_r54_sanitized_actual_review_result_capture_bodyfree
assert_p7_r54_sanitized_actual_review_result_capture_contract = assert_p7_r54_sanitized_actual_review_result_capture_bodyfree_contract
build_p7_r54_rating_row = build_p7_r54_rating_row_bodyfree
assert_p7_r54_rating_row_contract = assert_p7_r54_rating_row_bodyfree_contract
build_p7_r54_rating_row_normalization = build_p7_r54_rating_row_normalization_bodyfree
assert_p7_r54_rating_row_normalization_contract = assert_p7_r54_rating_row_normalization_bodyfree_contract


# Compatibility aliases matching the shorter R54-8/R54-9 design wording.
build_p7_r54_reviewer_instruction_rating_form_freeze = build_p7_r54_reviewer_instruction_rating_form_freeze_bodyfree
assert_p7_r54_reviewer_instruction_rating_form_freeze_contract = assert_p7_r54_reviewer_instruction_rating_form_freeze_bodyfree_contract
build_p7_r54_reviewer_rating_axis_instruction_row = build_p7_r54_reviewer_rating_axis_instruction_row_bodyfree
assert_p7_r54_reviewer_rating_axis_instruction_row_contract = assert_p7_r54_reviewer_rating_axis_instruction_row_bodyfree_contract
build_p7_r54_actual_human_review_operation_state_capture = build_p7_r54_actual_human_review_operation_state_capture_bodyfree
assert_p7_r54_actual_human_review_operation_state_capture_contract = assert_p7_r54_actual_human_review_operation_state_capture_bodyfree_contract


# ---------------------------------------------------------------------------
# R54-18 / R54-19 P5 decision candidate separation and P6 candidate handoff
# ---------------------------------------------------------------------------

P7_R54_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.p5_decision_candidate_separation.bodyfree.v1"
)
P7_R54_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.p6_limited_human_readfeel_candidate_handoff.bodyfree.v1"
)
P7_R54_R18_STEP_REF: Final = "R54-18_p5_decision_candidate_separation"
P7_R54_R19_STEP_REF: Final = "R54-19_p6_limited_human_readfeel_candidate_handoff"
P7_R54_R18_NEXT_REQUIRED_STEP_REF: Final = P7_R54_R19_STEP_REF
P7_R54_R18_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R54-17_body_free_post_review_summary_before_R54-18_p5_decision_candidate_separation"
P7_R54_R19_NEXT_REQUIRED_STEP_REF: Final = "R54-20_p8_question_design_material_candidate_handoff"
P7_R54_R19_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R54-18_p5_decision_candidate_separation_before_R54-19_p6_limited_human_readfeel_candidate_handoff"

P7_R54_FUTURE_STEPS_AFTER_R19: Final[tuple[str, ...]] = tuple(
    step for step in P7_R54_FUTURE_STEPS_AFTER_R17 if step not in {P7_R54_R18_STEP_REF, P7_R54_R19_STEP_REF}
)
P7_R54_R18_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_R17_IMPLEMENTED_STEPS, P7_R54_R18_STEP_REF)
P7_R54_R18_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_R19_STEP_REF, *P7_R54_FUTURE_STEPS_AFTER_R19)
P7_R54_R19_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_R18_IMPLEMENTED_STEPS, P7_R54_R19_STEP_REF)
P7_R54_R19_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_FUTURE_STEPS_AFTER_R19

P7_R54_P5_DECISION_CANDIDATE_STATUS_REFS: Final[tuple[str, ...]] = (
    "P5_CONFIRMED_CANDIDATE_SEPARATED",
    "P5_REPAIR_RETURN_CANDIDATE_SEPARATED",
    "P5_INCONCLUSIVE_CANDIDATE_SEPARATED",
    "BLOCKED_BY_R54_17_BODY_FREE_POST_REVIEW_SUMMARY",
)
P7_R54_P5_DECISION_CANDIDATE_REF_REFS: Final[tuple[str, ...]] = (
    "P5_CONFIRMED_CANDIDATE",
    "P5_REPAIR_RETURN",
    "P5_INCONCLUSIVE_EXECUTION_BLOCKED",
    "P5_INCONCLUSIVE_DISPOSAL_BLOCKED",
    "P5_INCONCLUSIVE_ROW_INCOMPLETE",
    "P5_INCONCLUSIVE_YELLOW_REQUIRES_HUMAN_DECISION",
    "P5_BLOCKED_BY_BODY_LEAK_VALIDATION",
    "P5_BLOCKED_BY_QUESTION_TEXT_VALIDATION",
    "P5_NOT_REVIEWED",
)
P7_R54_R18_CONFIRMED_REQUIREMENT_REFS: Final[tuple[str, ...]] = (
    "all_24_cases_reviewed",
    "rating_rows_24",
    "question_observation_rows_24",
    "all_axis_targets_met",
    "no_open_execution_blocker",
    "no_open_readfeel_blocker",
    "no_red_repair_or_yellow_verdict",
    "no_readfeel_repair_blocker",
    "no_not_question_repair_observation",
    "disposal_verified",
    "body_removed",
    "reviewer_notes_removed",
    "body_free_summary_counts_refs_only",
)
P7_R54_P6_CANDIDATE_HANDOFF_STATUS_REFS: Final[tuple[str, ...]] = (
    "P6_CANDIDATE_TRUE_FROM_P5_CONFIRMED_CANDIDATE",
    "P6_CANDIDATE_NOT_AVAILABLE_P5_REPAIR_RETURN",
    "P6_CANDIDATE_NOT_AVAILABLE_P5_INCONCLUSIVE",
    "BLOCKED_BY_R54_18_P5_DECISION_CANDIDATE_SEPARATION",
)

P7_R54_R18_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_R17_FALSE_KEY_REFS
    if key not in {"p5_human_blind_qa_confirmed_candidate", "p5_repair_return_candidate", "p5_review_inconclusive"}
)
P7_R54_R19_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_R18_FALSE_KEY_REFS
    if key not in {"p5_human_blind_qa_confirmed_candidate", "p5_repair_return_candidate", "p5_review_inconclusive", "p6_limited_human_readfeel_candidate"}
)

P7_R54_P5_DECISION_CANDIDATE_SEPARATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "r17_body_free_post_review_summary_schema_version", "r17_body_free_post_review_summary_material_ref", "r17_body_free_post_review_summary_status", "r17_ready_for_p5_decision_candidate_separation",
    "current_received_snapshot_refs", "current_received_snapshot_ref_count", "r53_source_snapshot_refs", "r53_source_snapshot_ref_count", "r53_refs_are_current_received_refs",
    "review_session_status", "p5_decision_candidate_status", "p5_decision_candidate_ref", "p5_decision_reason_refs", "p5_decision_candidate_materialized_here", "p5_decision_finalized_here",
    "required_case_count", "all_24_cases_reviewed", "rating_row_count", "question_observation_row_count", "all_axis_targets_met", "axis_target_missed_refs", "open_execution_blocker_count", "open_readfeel_blocker_count", "red_count", "repair_required_count", "yellow_count", "pass_count", "critical_repair_blocker_count", "repair_observation_count", "disposal_verified", "body_removed", "reviewer_forms_removed", "reviewer_notes_removed", "body_free_summary_contains_only_counts_and_refs", "p5_confirmed_requirements_met_by_summary",
    "confirmed_candidate_requirements_met", "repair_return_required", "inconclusive_required", "inconclusive_reason_refs", "p5_confirmed_requirement_met_refs", "p5_confirmed_requirement_missing_refs", "p5_repair_return_reason_refs", "p5_repair_return_target_refs", "p5_inconclusive_reason_refs",
    "raw_input_included", "returned_surface_included", "comment_text_included", "reviewer_free_text_included", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included", "terminal_output_included", "local_packet_exported", "content_hash_of_body_stored",
    "p5_human_blind_qa_confirmed_candidate", "p5_human_blind_qa_confirmed_final", "p5_repair_return_candidate", "p5_review_inconclusive", "p6_limited_human_readfeel_candidate", "p6_limited_human_readfeel_start_allowed", "p8_question_design_material_candidate", "p8_start_allowed", "p7_complete", "release_allowed", "hold004_close_allowed",
    "body_full_packet_generated_here", "actual_body_full_packet_generated_here", "actual_review_run_here", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_reviewer_notes_materialized_here", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_question_need_observation_summary_materialized_here", "actual_disposal_run_here", "disposal_receipt_materialized_here", "actual_disposal_receipt_materialized_here", "post_review_summary_materialized_here", "p5_actual_review_still_not_run_by_helper",
    "r54_0_scope_current_received_snapshot_refrozen", "r54_1_r53_source_delta_current_snapshot_override_adopted", "r54_2_validation_evidence_intake_done", "r54_3_local_only_actual_review_preflight_built", "r54_4_actual_review_session_envelope_built", "r54_5_24_case_manifest_freeze_built", "r54_6_local_only_body_full_packet_generation_request_built", "r54_7_packet_completeness_export_denylist_scan_built", "r54_8_reviewer_instruction_rating_form_freeze_built", "r54_9_actual_human_review_operation_state_capture_built", "r54_10_sanitized_actual_review_result_capture_built", "r54_11_rating_row_normalization_built", "r54_12_readfeel_blocker_execution_blocker_ingestion_built", "r54_13_question_need_observation_row_normalization_built", "r54_14_rating_question_observation_consistency_guard_built", "r54_15_pause_abort_expiration_protocol_built", "r54_16_purge_disposal_receipt_built", "r54_17_body_free_post_review_summary_built", "r54_18_p5_decision_candidate_separation_built",
    "execution_blocker_ids", "open_execution_blocker_ids", "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract", "r54_public_no_touch_contract", "body_free_markers", "body_free",
    *P7_R54_R18_FALSE_KEY_REFS,
    "validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here",
)

P7_R54_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "r18_p5_decision_candidate_separation_schema_version", "r18_p5_decision_candidate_separation_material_ref", "r18_p5_decision_candidate_status", "r18_p5_decision_candidate_ref", "r18_ready_for_p6_candidate_handoff",
    "current_received_snapshot_refs", "current_received_snapshot_ref_count", "r53_source_snapshot_refs", "r53_source_snapshot_ref_count", "r53_refs_are_current_received_refs",
    "review_session_status", "p6_candidate_handoff_status", "p6_candidate_handoff_reason_refs", "p6_candidate_handoff_materialized_here", "p6_start_allowed_false_reason_refs",
    "p5_human_blind_qa_confirmed_candidate", "p5_human_blind_qa_confirmed_final", "p5_repair_return_candidate", "p5_review_inconclusive", "p5_decision_candidate_ref", "p5_decision_candidate_status", "p5_decision_finalized_here",
    "required_case_count", "all_24_cases_reviewed", "rating_row_count", "question_observation_row_count", "all_axis_targets_met", "axis_target_missed_refs", "open_execution_blocker_count", "open_readfeel_blocker_count", "red_count", "repair_required_count", "yellow_count", "critical_repair_blocker_count", "repair_observation_count", "disposal_verified", "body_removed", "reviewer_notes_removed",
    "raw_input_included", "returned_surface_included", "comment_text_included", "reviewer_free_text_included", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included", "terminal_output_included", "local_packet_exported", "content_hash_of_body_stored",
    "p6_limited_human_readfeel_candidate", "p6_limited_human_readfeel_start_allowed", "p8_question_design_material_candidate", "p8_start_allowed", "p7_complete", "release_allowed", "hold004_close_allowed",
    "body_full_packet_generated_here", "actual_body_full_packet_generated_here", "actual_review_run_here", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_reviewer_notes_materialized_here", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_question_need_observation_summary_materialized_here", "actual_disposal_run_here", "disposal_receipt_materialized_here", "actual_disposal_receipt_materialized_here", "post_review_summary_materialized_here", "p5_actual_review_still_not_run_by_helper",
    "r54_0_scope_current_received_snapshot_refrozen", "r54_1_r53_source_delta_current_snapshot_override_adopted", "r54_2_validation_evidence_intake_done", "r54_3_local_only_actual_review_preflight_built", "r54_4_actual_review_session_envelope_built", "r54_5_24_case_manifest_freeze_built", "r54_6_local_only_body_full_packet_generation_request_built", "r54_7_packet_completeness_export_denylist_scan_built", "r54_8_reviewer_instruction_rating_form_freeze_built", "r54_9_actual_human_review_operation_state_capture_built", "r54_10_sanitized_actual_review_result_capture_built", "r54_11_rating_row_normalization_built", "r54_12_readfeel_blocker_execution_blocker_ingestion_built", "r54_13_question_need_observation_row_normalization_built", "r54_14_rating_question_observation_consistency_guard_built", "r54_15_pause_abort_expiration_protocol_built", "r54_16_purge_disposal_receipt_built", "r54_17_body_free_post_review_summary_built", "r54_18_p5_decision_candidate_separation_built", "r54_19_p6_limited_human_readfeel_candidate_handoff_built",
    "execution_blocker_ids", "open_execution_blocker_ids", "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract", "r54_public_no_touch_contract", "body_free_markers", "body_free",
    *P7_R54_R19_FALSE_KEY_REFS,
    "validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here",
)


def _r54_bool(value: Any) -> bool:
    return value is True


def _r54_decide_p5_from_summary(summary: Mapping[str, Any]) -> tuple[str, str, list[str], bool, bool, bool, bool, list[str], bool, bool, bool]:
    status = clean_identifier(summary.get("post_review_summary_status"), default="", max_length=160)
    ready = status == "READY_FOR_P5_DECISION_CANDIDATE_SEPARATION" and summary.get("r54_17_body_free_post_review_summary_built") is True
    if not ready:
        return (
            "BLOCKED_BY_R54_17_BODY_FREE_POST_REVIEW_SUMMARY",
            "P5_NOT_REVIEWED",
            ["r54_p5_not_reviewed_or_summary_blocked"],
            False,
            False,
            True,
            False,
            ["r54_p5_inconclusive_summary_not_ready"],
            False,
            False,
            True,
        )
    row_incomplete = not (
        summary.get("all_24_cases_reviewed") is True
        and _safe_non_negative_int_r54(summary.get("rating_row_count")) == P7_R51_REQUIRED_CASE_COUNT
        and _safe_non_negative_int_r54(summary.get("question_observation_row_count")) == P7_R51_REQUIRED_CASE_COUNT
    )
    execution_blocked = _safe_non_negative_int_r54(summary.get("open_execution_blocker_count")) > 0 or bool(summary.get("execution_blocker_ids"))
    disposal_blocked = not (
        summary.get("disposal_verified") is True
        and summary.get("body_removed") is True
        and summary.get("reviewer_forms_removed") is True
        and summary.get("reviewer_notes_removed") is True
    )
    yellow_or_axis = _safe_non_negative_int_r54(summary.get("yellow_count")) > 0 or summary.get("all_axis_targets_met") is not True or bool(summary.get("axis_target_missed_refs"))
    question_primary_counts = safe_mapping(summary.get("question_need_primary_class_counts"))
    not_question_repair_required_count = sum(
        _safe_non_negative_int_r54(question_primary_counts.get(ref))
        for ref in P7_R54_NOT_QUESTION_REPAIR_PRIMARY_CLASS_REFS
    )
    repair_required = (
        _safe_non_negative_int_r54(summary.get("red_count")) > 0
        or _safe_non_negative_int_r54(summary.get("repair_required_count")) > 0
        or _safe_non_negative_int_r54(summary.get("open_readfeel_blocker_count")) > 0
        or _safe_non_negative_int_r54(summary.get("critical_repair_blocker_count")) > 0
        or _safe_non_negative_int_r54(summary.get("repair_observation_count")) > 0
        or not_question_repair_required_count > 0
    )
    if execution_blocked:
        return ("P5_INCONCLUSIVE_CANDIDATE_SEPARATED", "P5_INCONCLUSIVE_EXECUTION_BLOCKED", ["r54_p5_inconclusive_execution_blocked"], False, False, True, True, ["r54_p5_inconclusive_execution_blocked"], False, True, False)
    if row_incomplete:
        return ("P5_INCONCLUSIVE_CANDIDATE_SEPARATED", "P5_INCONCLUSIVE_ROW_INCOMPLETE", ["r54_p5_inconclusive_row_incomplete"], False, False, True, True, ["r54_p5_inconclusive_row_incomplete"], False, True, False)
    if disposal_blocked:
        return ("P5_INCONCLUSIVE_CANDIDATE_SEPARATED", "P5_INCONCLUSIVE_DISPOSAL_BLOCKED", ["r54_p5_inconclusive_disposal_blocked"], False, False, True, True, ["r54_p5_inconclusive_disposal_blocked"], False, True, False)
    if repair_required:
        repair_reasons: list[str] = []
        if _safe_non_negative_int_r54(summary.get("red_count")) > 0 or _safe_non_negative_int_r54(summary.get("repair_required_count")) > 0:
            repair_reasons.append("r54_p5_repair_return_required_by_red_or_repair_verdict")
        if _safe_non_negative_int_r54(summary.get("open_readfeel_blocker_count")) > 0 or _safe_non_negative_int_r54(summary.get("critical_repair_blocker_count")) > 0:
            repair_reasons.append("r54_p5_repair_return_required_by_readfeel_blocker")
        if _safe_non_negative_int_r54(summary.get("repair_observation_count")) > 0 or not_question_repair_required_count > 0:
            repair_reasons.append("r54_p5_repair_return_required_by_not_question_repair_observation")
        return ("P5_REPAIR_RETURN_CANDIDATE_SEPARATED", "P5_REPAIR_RETURN", dedupe_identifiers(repair_reasons, limit=20, max_length=160), False, True, False, True, [], True, False, False)
    if yellow_or_axis:
        return ("P5_INCONCLUSIVE_CANDIDATE_SEPARATED", "P5_INCONCLUSIVE_YELLOW_REQUIRES_HUMAN_DECISION", ["r54_p5_inconclusive_yellow_or_axis_missed"], False, False, True, True, ["r54_p5_inconclusive_yellow_or_axis_missed"], False, True, False)
    if summary.get("p5_confirmed_requirements_met_by_summary") is True:
        return ("P5_CONFIRMED_CANDIDATE_SEPARATED", "P5_CONFIRMED_CANDIDATE", ["r54_p5_confirmed_candidate_conditions_met_not_final"], True, False, False, True, [], False, False, False)
    return ("P5_INCONCLUSIVE_CANDIDATE_SEPARATED", "P5_INCONCLUSIVE_ROW_INCOMPLETE", ["r54_p5_inconclusive_requirements_not_met"], False, False, True, True, ["r54_p5_inconclusive_requirements_not_met"], False, True, False)


def build_p7_r54_p5_decision_candidate_separation_bodyfree(
    *,
    body_free_post_review_summary: Mapping[str, Any] | None = None,
    r17_body_free_post_review_summary: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_p5_decision_candidate_separation_bodyfree",
) -> dict[str, Any]:
    """Build R54-18 body-free P5 decision candidate separation."""

    if body_free_post_review_summary is not None and r17_body_free_post_review_summary is not None:
        raise ValueError("provide only one R54-17 body-free post-review summary value")
    summary = safe_mapping(
        body_free_post_review_summary
        if body_free_post_review_summary is not None
        else r17_body_free_post_review_summary
        if r17_body_free_post_review_summary is not None
        else build_p7_r54_body_free_post_review_summary_bodyfree()
    )
    assert_p7_r54_body_free_post_review_summary_bodyfree_contract(summary)
    (
        status,
        decision_ref,
        reason_refs,
        confirmed,
        repair,
        inconclusive,
        materialized,
        inconclusive_reason_refs,
        repair_return_required,
        inconclusive_required,
        summary_blocked,
    ) = _r54_decide_p5_from_summary(summary)
    material = {
        "schema_version": P7_R54_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_STEP,
        "scope": P7_R54_SCOPE,
        "policy_kind": P7_R54_POLICY_KIND,
        "policy_section": P7_R54_R18_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_p5_decision_candidate_separation_bodyfree", max_length=180),
        "review_session_id": _safe_review_session_id(summary.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r17_body_free_post_review_summary_schema_version": P7_R54_BODY_FREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION,
        "r17_body_free_post_review_summary_material_ref": clean_identifier(summary.get("material_id"), default="p7_r54_body_free_post_review_summary_bodyfree", max_length=180),
        "r17_body_free_post_review_summary_status": clean_identifier(summary.get("post_review_summary_status"), default="BLOCKED_BY_POST_REVIEW_SUMMARY_REQUIREMENTS", max_length=180),
        "r17_ready_for_p5_decision_candidate_separation": summary.get("post_review_summary_status") == "READY_FOR_P5_DECISION_CANDIDATE_SEPARATION" and summary.get("r54_17_body_free_post_review_summary_built") is True,
        "current_received_snapshot_refs": dict(P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "r53_source_snapshot_refs": _r53_source_snapshot_refs(None),
        "r53_source_snapshot_ref_count": len(_r53_source_snapshot_refs(None)),
        "r53_refs_are_current_received_refs": False,
        "review_session_status": "R54_P5_DECISION_CANDIDATE_SEPARATED" if materialized else "R54_P5_DECISION_CANDIDATE_BLOCKED",
        "p5_decision_candidate_status": status,
        "p5_decision_candidate_ref": decision_ref,
        "p5_decision_reason_refs": reason_refs,
        "p5_decision_candidate_materialized_here": materialized,
        "p5_decision_finalized_here": False,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "all_24_cases_reviewed": _r54_bool(summary.get("all_24_cases_reviewed")),
        "rating_row_count": _safe_non_negative_int_r54(summary.get("rating_row_count")),
        "question_observation_row_count": _safe_non_negative_int_r54(summary.get("question_observation_row_count")),
        "all_axis_targets_met": _r54_bool(summary.get("all_axis_targets_met")),
        "axis_target_missed_refs": dedupe_identifiers(summary.get("axis_target_missed_refs") or (), limit=20, max_length=120),
        "open_execution_blocker_count": _safe_non_negative_int_r54(summary.get("open_execution_blocker_count")),
        "open_readfeel_blocker_count": _safe_non_negative_int_r54(summary.get("open_readfeel_blocker_count")),
        "red_count": _safe_non_negative_int_r54(summary.get("red_count")),
        "repair_required_count": _safe_non_negative_int_r54(summary.get("repair_required_count")),
        "yellow_count": _safe_non_negative_int_r54(summary.get("yellow_count")),
        "pass_count": _safe_non_negative_int_r54(summary.get("pass_count")),
        "critical_repair_blocker_count": _safe_non_negative_int_r54(summary.get("critical_repair_blocker_count")),
        "repair_observation_count": _safe_non_negative_int_r54(summary.get("repair_observation_count")),
        "disposal_verified": _r54_bool(summary.get("disposal_verified")),
        "body_removed": _r54_bool(summary.get("body_removed")),
        "reviewer_forms_removed": _r54_bool(summary.get("reviewer_forms_removed")),
        "reviewer_notes_removed": _r54_bool(summary.get("reviewer_notes_removed")),
        "body_free_summary_contains_only_counts_and_refs": _r54_bool(summary.get("body_free_summary_contains_only_counts_and_refs")),
        "p5_confirmed_requirements_met_by_summary": _r54_bool(summary.get("p5_confirmed_requirements_met_by_summary")),
        "confirmed_candidate_requirements_met": confirmed,
        "repair_return_required": repair_return_required,
        "inconclusive_required": inconclusive_required,
        "inconclusive_reason_refs": inconclusive_reason_refs,
        "p5_confirmed_requirement_met_refs": list(P7_R54_R18_CONFIRMED_REQUIREMENT_REFS) if confirmed else [],
        "p5_confirmed_requirement_missing_refs": [] if confirmed else list(P7_R54_R18_CONFIRMED_REQUIREMENT_REFS),
        "p5_repair_return_reason_refs": reason_refs if repair else [],
        "p5_repair_return_target_refs": ["p5_surface_repair"] if repair else [],
        "p5_inconclusive_reason_refs": inconclusive_reason_refs if inconclusive else [],
        "raw_input_included": False,
        "returned_surface_included": False,
        "comment_text_included": False,
        "reviewer_free_text_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_absolute_path_included": False,
        "body_content_hash_included": False,
        "packet_content_hash_included": False,
        "terminal_output_included": False,
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "p5_human_blind_qa_confirmed_candidate": confirmed,
        "p5_human_blind_qa_confirmed_final": False,
        "p5_repair_return_candidate": repair,
        "p5_review_inconclusive": inconclusive,
        "p6_limited_human_readfeel_candidate": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_question_design_material_candidate": False,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "hold004_close_allowed": False,
        "body_full_packet_generated_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_review_run_here": _r54_bool(summary.get("actual_review_run_here")) and materialized,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "actual_rating_rows_materialized_here": _r54_bool(summary.get("actual_rating_rows_materialized_here")) and materialized,
        "actual_blocker_rows_materialized_here": _r54_bool(summary.get("actual_blocker_rows_materialized_here")) and materialized,
        "actual_execution_blocker_rows_materialized_here": _r54_bool(summary.get("actual_execution_blocker_rows_materialized_here")) and materialized,
        "actual_question_need_observation_rows_materialized_here": _r54_bool(summary.get("actual_question_need_observation_rows_materialized_here")) and materialized,
        "actual_question_need_observation_summary_materialized_here": _r54_bool(summary.get("actual_question_need_observation_summary_materialized_here")) and materialized,
        "actual_disposal_run_here": False,
        "disposal_receipt_materialized_here": _r54_bool(summary.get("disposal_receipt_materialized_here")) and materialized,
        "actual_disposal_receipt_materialized_here": _r54_bool(summary.get("actual_disposal_receipt_materialized_here")) and materialized,
        "post_review_summary_materialized_here": _r54_bool(summary.get("post_review_summary_materialized_here")) and materialized,
        "p5_actual_review_still_not_run_by_helper": True,
        "r54_0_scope_current_received_snapshot_refrozen": True,
        "r54_1_r53_source_delta_current_snapshot_override_adopted": True,
        "r54_2_validation_evidence_intake_done": _r54_bool(summary.get("r54_2_validation_evidence_intake_done")) and materialized,
        "r54_3_local_only_actual_review_preflight_built": _r54_bool(summary.get("r54_3_local_only_actual_review_preflight_built")) and materialized,
        "r54_4_actual_review_session_envelope_built": _r54_bool(summary.get("r54_4_actual_review_session_envelope_built")) and materialized,
        "r54_5_24_case_manifest_freeze_built": _r54_bool(summary.get("r54_5_24_case_manifest_freeze_built")) and materialized,
        "r54_6_local_only_body_full_packet_generation_request_built": _r54_bool(summary.get("r54_6_local_only_body_full_packet_generation_request_built")) and materialized,
        "r54_7_packet_completeness_export_denylist_scan_built": _r54_bool(summary.get("r54_7_packet_completeness_export_denylist_scan_built")) and materialized,
        "r54_8_reviewer_instruction_rating_form_freeze_built": _r54_bool(summary.get("r54_8_reviewer_instruction_rating_form_freeze_built")) and materialized,
        "r54_9_actual_human_review_operation_state_capture_built": _r54_bool(summary.get("r54_9_actual_human_review_operation_state_capture_built")) and materialized,
        "r54_10_sanitized_actual_review_result_capture_built": _r54_bool(summary.get("r54_10_sanitized_actual_review_result_capture_built")) and materialized,
        "r54_11_rating_row_normalization_built": _r54_bool(summary.get("r54_11_rating_row_normalization_built")) and materialized,
        "r54_12_readfeel_blocker_execution_blocker_ingestion_built": _r54_bool(summary.get("r54_12_readfeel_blocker_execution_blocker_ingestion_built")) and materialized,
        "r54_13_question_need_observation_row_normalization_built": _r54_bool(summary.get("r54_13_question_need_observation_row_normalization_built")) and materialized,
        "r54_14_rating_question_observation_consistency_guard_built": _r54_bool(summary.get("r54_14_rating_question_observation_consistency_guard_built")) and materialized,
        "r54_15_pause_abort_expiration_protocol_built": _r54_bool(summary.get("r54_15_pause_abort_expiration_protocol_built")) and materialized,
        "r54_16_purge_disposal_receipt_built": _r54_bool(summary.get("r54_16_purge_disposal_receipt_built")) and materialized,
        "r54_17_body_free_post_review_summary_built": _r54_bool(summary.get("r54_17_body_free_post_review_summary_built")) and materialized,
        "r54_18_p5_decision_candidate_separation_built": materialized,
        "execution_blocker_ids": ["r54_p5_decision_blocked_by_post_review_summary"] if summary_blocked else [],
        "open_execution_blocker_ids": ["r54_p5_decision_blocked_by_post_review_summary"] if summary_blocked else [],
        "implemented_steps": list(P7_R54_R18_IMPLEMENTED_STEPS if materialized else P7_R54_R17_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_R18_NOT_YET_IMPLEMENTED_STEPS if materialized else P7_R54_R17_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R54_R18_NEXT_REQUIRED_STEP_REF if materialized else P7_R54_R18_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "next_required_step": P7_R54_R18_NEXT_REQUIRED_STEP_REF if materialized else P7_R54_R18_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_except({"validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here", "actual_review_run_here", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_question_need_observation_summary_materialized_here", "disposal_receipt_materialized_here", "actual_disposal_receipt_materialized_here", "post_review_summary_materialized_here", "p5_human_blind_qa_confirmed_candidate", "p5_repair_return_candidate", "p5_review_inconclusive"}),
        "validation_evidence_intake_done_here": _r54_bool(summary.get("validation_evidence_intake_done_here")) and materialized,
        "local_root_preflight_passed_here": _r54_bool(summary.get("local_root_preflight_passed_here")) and materialized,
        "explicit_allow_present_here": _r54_bool(summary.get("explicit_allow_present_here")) and materialized,
        "purge_plan_verified_here": _r54_bool(summary.get("purge_plan_verified_here")) and materialized,
    }
    assert_p7_r54_p5_decision_candidate_separation_bodyfree_contract(material)
    return material


def assert_p7_r54_p5_decision_candidate_separation_bodyfree_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_P5_DECISION_CANDIDATE_SEPARATION_REQUIRED_FIELD_REFS, source="p7_r54_p5_decision_candidate_separation")
    _assert_body_free_common_with_false_keys(data, schema_version=P7_R54_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION, source="p7_r54_p5_decision_candidate_separation", false_key_refs=P7_R54_R18_FALSE_KEY_REFS)
    _assert_current_refs(data, source="p7_r54_p5_decision_candidate_separation")
    if data.get("policy_section") != P7_R54_R18_STEP_REF:
        raise ValueError("R54 R18 policy section changed")
    if data.get("p5_decision_candidate_status") not in P7_R54_P5_DECISION_CANDIDATE_STATUS_REFS:
        raise ValueError("R54 R18 P5 decision candidate status changed")
    if data.get("p5_decision_candidate_ref") not in P7_R54_P5_DECISION_CANDIDATE_REF_REFS:
        raise ValueError("R54 R18 P5 decision candidate ref changed")
    for false_key in (
        "p5_human_blind_qa_confirmed_final", "p5_decision_finalized_here", "p6_limited_human_readfeel_candidate", "p6_limited_human_readfeel_start_allowed", "p8_question_design_material_candidate", "p8_start_allowed", "p7_complete", "release_allowed", "hold004_close_allowed", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_disposal_run_here", "actual_reviewer_notes_materialized_here", "body_full_packet_generated_here", "actual_body_full_packet_generated_here", "raw_input_included", "returned_surface_included", "comment_text_included", "reviewer_free_text_included", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included", "terminal_output_included", "local_packet_exported", "content_hash_of_body_stored",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 R18 must keep {false_key}=False")
    if data.get("p5_decision_candidate_status") == "P5_CONFIRMED_CANDIDATE_SEPARATED":
        if data.get("p5_decision_candidate_ref") != "P5_CONFIRMED_CANDIDATE" or data.get("p5_human_blind_qa_confirmed_candidate") is not True:
            raise ValueError("R54 R18 confirmed candidate mismatch")
        if data.get("p5_repair_return_candidate") is not False or data.get("p5_review_inconclusive") is not False:
            raise ValueError("R54 R18 confirmed candidate cannot also be repair/inconclusive")
    elif data.get("p5_decision_candidate_status") == "P5_REPAIR_RETURN_CANDIDATE_SEPARATED":
        if data.get("p5_decision_candidate_ref") != "P5_REPAIR_RETURN" or data.get("p5_repair_return_candidate") is not True:
            raise ValueError("R54 R18 repair candidate mismatch")
        if data.get("p5_human_blind_qa_confirmed_candidate") is not False or data.get("p5_review_inconclusive") is not False:
            raise ValueError("R54 R18 repair candidate cannot also be confirmed/inconclusive")
    elif data.get("p5_decision_candidate_status") == "P5_INCONCLUSIVE_CANDIDATE_SEPARATED":
        if not str(data.get("p5_decision_candidate_ref")).startswith("P5_INCONCLUSIVE") or data.get("p5_review_inconclusive") is not True:
            raise ValueError("R54 R18 inconclusive candidate mismatch")
        if data.get("p5_human_blind_qa_confirmed_candidate") is not False or data.get("p5_repair_return_candidate") is not False:
            raise ValueError("R54 R18 inconclusive candidate cannot also be confirmed/repair")
    else:
        if data.get("p5_decision_candidate_ref") != "P5_NOT_REVIEWED" or data.get("r54_18_p5_decision_candidate_separation_built") is not False:
            raise ValueError("R54 R18 blocked candidate mismatch")
        if data.get("next_required_step") != P7_R54_R18_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R18 blocked next step changed")
    if data.get("p5_decision_candidate_status") != "BLOCKED_BY_R54_17_BODY_FREE_POST_REVIEW_SUMMARY":
        if data.get("p5_decision_candidate_materialized_here") is not True or data.get("r54_18_p5_decision_candidate_separation_built") is not True:
            raise ValueError("R54 R18 separated candidate must materialize R18")
        if data.get("next_required_step") != P7_R54_R18_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R18 next step changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_R18_IMPLEMENTED_STEPS:
            raise ValueError("R54 R18 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_R18_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 R18 not-yet steps changed")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_p5_decision_candidate_separation")
    return True


def build_p7_r54_p6_limited_human_readfeel_candidate_handoff_bodyfree(
    *,
    p5_decision_candidate_separation: Mapping[str, Any] | None = None,
    r18_p5_decision_candidate_separation: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_p6_limited_human_readfeel_candidate_handoff_bodyfree",
) -> dict[str, Any]:
    """Build R54-19 body-free P6 limited human readfeel candidate handoff."""

    if p5_decision_candidate_separation is not None and r18_p5_decision_candidate_separation is not None:
        raise ValueError("provide only one R54-18 P5 decision candidate separation value")
    r18 = safe_mapping(
        p5_decision_candidate_separation
        if p5_decision_candidate_separation is not None
        else r18_p5_decision_candidate_separation
        if r18_p5_decision_candidate_separation is not None
        else build_p7_r54_p5_decision_candidate_separation_bodyfree()
    )
    assert_p7_r54_p5_decision_candidate_separation_bodyfree_contract(r18)
    r18_ready = r18.get("r54_18_p5_decision_candidate_separation_built") is True and r18.get("p5_decision_candidate_materialized_here") is True
    candidate = bool(r18.get("p5_human_blind_qa_confirmed_candidate") is True and r18.get("p5_decision_candidate_ref") == "P5_CONFIRMED_CANDIDATE")
    if not r18_ready:
        status = "BLOCKED_BY_R54_18_P5_DECISION_CANDIDATE_SEPARATION"
        reason_refs = ["r54_p6_handoff_blocked_by_r18_not_ready", "r54_p6_start_allowed_false_fixed_by_r54_scope"]
        built = False
        blockers = ["r54_p6_handoff_blocked_by_r18_not_ready"]
    elif candidate:
        status = "P6_CANDIDATE_TRUE_FROM_P5_CONFIRMED_CANDIDATE"
        reason_refs = ["r54_p6_candidate_true_from_p5_confirmed_candidate_bodyfree", "r54_p6_start_allowed_false_fixed_by_r54_scope"]
        built = True
        blockers = []
    elif r18.get("p5_repair_return_candidate") is True:
        status = "P6_CANDIDATE_NOT_AVAILABLE_P5_REPAIR_RETURN"
        reason_refs = ["r54_p6_candidate_false_p5_repair_return", "r54_p6_start_allowed_false_fixed_by_r54_scope"]
        built = True
        blockers = []
    else:
        status = "P6_CANDIDATE_NOT_AVAILABLE_P5_INCONCLUSIVE"
        reason_refs = ["r54_p6_candidate_false_p5_inconclusive", "r54_p6_start_allowed_false_fixed_by_r54_scope"]
        built = True
        blockers = []
    material = {
        "schema_version": P7_R54_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_STEP,
        "scope": P7_R54_SCOPE,
        "policy_kind": P7_R54_POLICY_KIND,
        "policy_section": P7_R54_R19_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_p6_limited_human_readfeel_candidate_handoff_bodyfree", max_length=180),
        "review_session_id": _safe_review_session_id(r18.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r18_p5_decision_candidate_separation_schema_version": P7_R54_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION,
        "r18_p5_decision_candidate_separation_material_ref": clean_identifier(r18.get("material_id"), default="p7_r54_p5_decision_candidate_separation_bodyfree", max_length=180),
        "r18_p5_decision_candidate_status": clean_identifier(r18.get("p5_decision_candidate_status"), default="BLOCKED_BY_R54_17_BODY_FREE_POST_REVIEW_SUMMARY", max_length=160),
        "r18_p5_decision_candidate_ref": clean_identifier(r18.get("p5_decision_candidate_ref"), default="P5_NOT_REVIEWED", max_length=160),
        "r18_ready_for_p6_candidate_handoff": bool(r18_ready),
        "current_received_snapshot_refs": dict(P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "r53_source_snapshot_refs": _r53_source_snapshot_refs(None),
        "r53_source_snapshot_ref_count": len(_r53_source_snapshot_refs(None)),
        "r53_refs_are_current_received_refs": False,
        "review_session_status": "R54_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_READY" if built else "R54_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_BLOCKED",
        "p6_candidate_handoff_status": status,
        "p6_candidate_handoff_reason_refs": reason_refs,
        "p6_candidate_handoff_materialized_here": built,
        "p6_start_allowed_false_reason_refs": ["r54_p6_start_allowed_false_fixed_by_r54_scope"],
        "p5_human_blind_qa_confirmed_candidate": r18.get("p5_human_blind_qa_confirmed_candidate") is True,
        "p5_human_blind_qa_confirmed_final": False,
        "p5_repair_return_candidate": r18.get("p5_repair_return_candidate") is True,
        "p5_review_inconclusive": r18.get("p5_review_inconclusive") is True,
        "p5_decision_candidate_ref": clean_identifier(r18.get("p5_decision_candidate_ref"), default="P5_NOT_REVIEWED", max_length=160),
        "p5_decision_candidate_status": clean_identifier(r18.get("p5_decision_candidate_status"), default="BLOCKED_BY_R54_17_BODY_FREE_POST_REVIEW_SUMMARY", max_length=160),
        "p5_decision_finalized_here": False,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "all_24_cases_reviewed": _r54_bool(r18.get("all_24_cases_reviewed")),
        "rating_row_count": _safe_non_negative_int_r54(r18.get("rating_row_count")),
        "question_observation_row_count": _safe_non_negative_int_r54(r18.get("question_observation_row_count")),
        "all_axis_targets_met": _r54_bool(r18.get("all_axis_targets_met")),
        "axis_target_missed_refs": dedupe_identifiers(r18.get("axis_target_missed_refs") or (), limit=20, max_length=120),
        "open_execution_blocker_count": _safe_non_negative_int_r54(r18.get("open_execution_blocker_count")),
        "open_readfeel_blocker_count": _safe_non_negative_int_r54(r18.get("open_readfeel_blocker_count")),
        "red_count": _safe_non_negative_int_r54(r18.get("red_count")),
        "repair_required_count": _safe_non_negative_int_r54(r18.get("repair_required_count")),
        "yellow_count": _safe_non_negative_int_r54(r18.get("yellow_count")),
        "critical_repair_blocker_count": _safe_non_negative_int_r54(r18.get("critical_repair_blocker_count")),
        "repair_observation_count": _safe_non_negative_int_r54(r18.get("repair_observation_count")),
        "disposal_verified": _r54_bool(r18.get("disposal_verified")),
        "body_removed": _r54_bool(r18.get("body_removed")),
        "reviewer_notes_removed": _r54_bool(r18.get("reviewer_notes_removed")),
        "raw_input_included": False,
        "returned_surface_included": False,
        "comment_text_included": False,
        "reviewer_free_text_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_absolute_path_included": False,
        "body_content_hash_included": False,
        "packet_content_hash_included": False,
        "terminal_output_included": False,
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "p6_limited_human_readfeel_candidate": candidate,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_question_design_material_candidate": False,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "hold004_close_allowed": False,
        "body_full_packet_generated_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_review_run_here": _r54_bool(r18.get("actual_review_run_here")) and built,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "actual_rating_rows_materialized_here": _r54_bool(r18.get("actual_rating_rows_materialized_here")) and built,
        "actual_blocker_rows_materialized_here": _r54_bool(r18.get("actual_blocker_rows_materialized_here")) and built,
        "actual_execution_blocker_rows_materialized_here": _r54_bool(r18.get("actual_execution_blocker_rows_materialized_here")) and built,
        "actual_question_need_observation_rows_materialized_here": _r54_bool(r18.get("actual_question_need_observation_rows_materialized_here")) and built,
        "actual_question_need_observation_summary_materialized_here": _r54_bool(r18.get("actual_question_need_observation_summary_materialized_here")) and built,
        "actual_disposal_run_here": False,
        "disposal_receipt_materialized_here": _r54_bool(r18.get("disposal_receipt_materialized_here")) and built,
        "actual_disposal_receipt_materialized_here": _r54_bool(r18.get("actual_disposal_receipt_materialized_here")) and built,
        "post_review_summary_materialized_here": _r54_bool(r18.get("post_review_summary_materialized_here")) and built,
        "p5_actual_review_still_not_run_by_helper": True,
        "r54_0_scope_current_received_snapshot_refrozen": True,
        "r54_1_r53_source_delta_current_snapshot_override_adopted": True,
        "r54_2_validation_evidence_intake_done": _r54_bool(r18.get("r54_2_validation_evidence_intake_done")) and built,
        "r54_3_local_only_actual_review_preflight_built": _r54_bool(r18.get("r54_3_local_only_actual_review_preflight_built")) and built,
        "r54_4_actual_review_session_envelope_built": _r54_bool(r18.get("r54_4_actual_review_session_envelope_built")) and built,
        "r54_5_24_case_manifest_freeze_built": _r54_bool(r18.get("r54_5_24_case_manifest_freeze_built")) and built,
        "r54_6_local_only_body_full_packet_generation_request_built": _r54_bool(r18.get("r54_6_local_only_body_full_packet_generation_request_built")) and built,
        "r54_7_packet_completeness_export_denylist_scan_built": _r54_bool(r18.get("r54_7_packet_completeness_export_denylist_scan_built")) and built,
        "r54_8_reviewer_instruction_rating_form_freeze_built": _r54_bool(r18.get("r54_8_reviewer_instruction_rating_form_freeze_built")) and built,
        "r54_9_actual_human_review_operation_state_capture_built": _r54_bool(r18.get("r54_9_actual_human_review_operation_state_capture_built")) and built,
        "r54_10_sanitized_actual_review_result_capture_built": _r54_bool(r18.get("r54_10_sanitized_actual_review_result_capture_built")) and built,
        "r54_11_rating_row_normalization_built": _r54_bool(r18.get("r54_11_rating_row_normalization_built")) and built,
        "r54_12_readfeel_blocker_execution_blocker_ingestion_built": _r54_bool(r18.get("r54_12_readfeel_blocker_execution_blocker_ingestion_built")) and built,
        "r54_13_question_need_observation_row_normalization_built": _r54_bool(r18.get("r54_13_question_need_observation_row_normalization_built")) and built,
        "r54_14_rating_question_observation_consistency_guard_built": _r54_bool(r18.get("r54_14_rating_question_observation_consistency_guard_built")) and built,
        "r54_15_pause_abort_expiration_protocol_built": _r54_bool(r18.get("r54_15_pause_abort_expiration_protocol_built")) and built,
        "r54_16_purge_disposal_receipt_built": _r54_bool(r18.get("r54_16_purge_disposal_receipt_built")) and built,
        "r54_17_body_free_post_review_summary_built": _r54_bool(r18.get("r54_17_body_free_post_review_summary_built")) and built,
        "r54_18_p5_decision_candidate_separation_built": _r54_bool(r18.get("r54_18_p5_decision_candidate_separation_built")) and built,
        "r54_19_p6_limited_human_readfeel_candidate_handoff_built": built,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "implemented_steps": list(P7_R54_R19_IMPLEMENTED_STEPS if built else P7_R54_R18_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_R19_NOT_YET_IMPLEMENTED_STEPS if built else P7_R54_R18_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R54_R19_NEXT_REQUIRED_STEP_REF if built else P7_R54_R19_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "next_required_step": P7_R54_R19_NEXT_REQUIRED_STEP_REF if built else P7_R54_R19_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_except({"validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here", "actual_review_run_here", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_question_need_observation_summary_materialized_here", "disposal_receipt_materialized_here", "actual_disposal_receipt_materialized_here", "post_review_summary_materialized_here", "p5_human_blind_qa_confirmed_candidate", "p5_repair_return_candidate", "p5_review_inconclusive", "p6_limited_human_readfeel_candidate"}),
        "validation_evidence_intake_done_here": _r54_bool(r18.get("validation_evidence_intake_done_here")) and built,
        "local_root_preflight_passed_here": _r54_bool(r18.get("local_root_preflight_passed_here")) and built,
        "explicit_allow_present_here": _r54_bool(r18.get("explicit_allow_present_here")) and built,
        "purge_plan_verified_here": _r54_bool(r18.get("purge_plan_verified_here")) and built,
    }
    assert_p7_r54_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract(material)
    return material


def assert_p7_r54_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_REQUIRED_FIELD_REFS, source="p7_r54_p6_limited_human_readfeel_candidate_handoff")
    _assert_body_free_common_with_false_keys(data, schema_version=P7_R54_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_SCHEMA_VERSION, source="p7_r54_p6_limited_human_readfeel_candidate_handoff", false_key_refs=P7_R54_R19_FALSE_KEY_REFS)
    _assert_current_refs(data, source="p7_r54_p6_limited_human_readfeel_candidate_handoff")
    if data.get("policy_section") != P7_R54_R19_STEP_REF:
        raise ValueError("R54 R19 policy section changed")
    if data.get("p6_candidate_handoff_status") not in P7_R54_P6_CANDIDATE_HANDOFF_STATUS_REFS:
        raise ValueError("R54 R19 candidate handoff status changed")
    for false_key in (
        "p5_human_blind_qa_confirmed_final", "p5_decision_finalized_here", "p6_limited_human_readfeel_start_allowed", "p8_question_design_material_candidate", "p8_start_allowed", "p7_complete", "release_allowed", "hold004_close_allowed", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_disposal_run_here", "actual_reviewer_notes_materialized_here", "body_full_packet_generated_here", "actual_body_full_packet_generated_here", "raw_input_included", "returned_surface_included", "comment_text_included", "reviewer_free_text_included", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included", "terminal_output_included", "local_packet_exported", "content_hash_of_body_stored",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 R19 must keep {false_key}=False")
    if data.get("p6_candidate_handoff_status") == "P6_CANDIDATE_TRUE_FROM_P5_CONFIRMED_CANDIDATE":
        if data.get("p6_limited_human_readfeel_candidate") is not True or data.get("p5_human_blind_qa_confirmed_candidate") is not True or data.get("p5_decision_candidate_ref") != "P5_CONFIRMED_CANDIDATE":
            raise ValueError("R54 R19 P6 candidate must be based on P5 confirmed candidate")
    elif data.get("p6_candidate_handoff_status") == "BLOCKED_BY_R54_18_P5_DECISION_CANDIDATE_SEPARATION":
        if data.get("p6_candidate_handoff_materialized_here") is not False or data.get("next_required_step") != P7_R54_R19_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R19 blocked handoff mismatch")
    else:
        if data.get("p6_limited_human_readfeel_candidate") is not False or data.get("p6_candidate_handoff_materialized_here") is not True:
            raise ValueError("R54 R19 false candidate handoff mismatch")
    if data.get("p6_candidate_handoff_status") != "BLOCKED_BY_R54_18_P5_DECISION_CANDIDATE_SEPARATION":
        if tuple(data.get("implemented_steps") or ()) != P7_R54_R19_IMPLEMENTED_STEPS:
            raise ValueError("R54 R19 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_R19_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 R19 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_R19_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R19 next step changed")
    if "r54_p6_start_allowed_false_fixed_by_r54_scope" not in tuple(data.get("p6_start_allowed_false_reason_refs") or ()):  # type: ignore[arg-type]
        raise ValueError("R54 R19 must keep P6 start_allowed=false reason")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_p6_limited_human_readfeel_candidate_handoff")
    return True



# ---------------------------------------------------------------------------
# R54-20 / R54-21 P8 material candidate handoff and final validation
# ---------------------------------------------------------------------------

P7_R54_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.p8_question_design_material_candidate_handoff.bodyfree.v1"
)
P7_R54_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.final_no_body_leak_no_question_text_no_touch_validation.bodyfree.v1"
)
P7_R54_R20_STEP_REF: Final = "R54-20_p8_question_design_material_candidate_handoff"
P7_R54_R21_STEP_REF: Final = "R54-21_final_no_body_leak_no_question_text_no_touch_validation"
P7_R54_R20_NEXT_REQUIRED_STEP_REF: Final = P7_R54_R21_STEP_REF
P7_R54_R20_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R54-19_p6_candidate_handoff_and_R54-17_summary_before_R54-20_p8_material_candidate_handoff"
P7_R54_R21_NEXT_REQUIRED_STEP_REF: Final = "R54-22_r52_reintake_handoff"
P7_R54_R21_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R54-21_final_body_free_no_touch_validation_before_R54-22_r52_reintake_handoff"

P7_R54_FUTURE_STEPS_AFTER_R21: Final[tuple[str, ...]] = tuple(
    step for step in P7_R54_FUTURE_STEPS_AFTER_R19 if step not in {P7_R54_R20_STEP_REF, P7_R54_R21_STEP_REF}
)
P7_R54_R20_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_R19_IMPLEMENTED_STEPS, P7_R54_R20_STEP_REF)
P7_R54_R20_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_R21_STEP_REF, *P7_R54_FUTURE_STEPS_AFTER_R21)
P7_R54_R21_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_R20_IMPLEMENTED_STEPS, P7_R54_R21_STEP_REF)
P7_R54_R21_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_FUTURE_STEPS_AFTER_R21

P7_R54_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_STATUS_REFS: Final[tuple[str, ...]] = (
    "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_TRUE",
    "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_NOT_AVAILABLE_NO_OBSERVATION",
    "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_NOT_AVAILABLE_P5_REPAIR_RETURN",
    "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_NOT_AVAILABLE_P5_INCONCLUSIVE",
    "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_NOT_AVAILABLE_NOT_QUESTION_REPAIR",
    "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_NOT_AVAILABLE_INSUFFICIENT_MATERIAL",
    "BLOCKED_BY_R54_19_P6_CANDIDATE_HANDOFF",
    "BLOCKED_BY_R54_17_BODY_FREE_POST_REVIEW_SUMMARY_FOR_P8_MATERIAL",
)
P7_R54_FINAL_VALIDATION_STATUS_REFS: Final[tuple[str, ...]] = (
    "FINAL_BODY_FREE_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_READY",
    "FINAL_VALIDATION_BLOCKED_BY_R54_20_P8_MATERIAL_HANDOFF",
    "FINAL_VALIDATION_BLOCKED_BY_BODY_LEAK",
    "FINAL_VALIDATION_BLOCKED_BY_QUESTION_TEXT",
    "FINAL_VALIDATION_BLOCKED_BY_NO_TOUCH_VIOLATION",
)
P7_R54_R20_P8_START_ALLOWED_FALSE_REASON_REF: Final = "r54_p8_start_allowed_false_fixed_by_r54_scope"
P7_R54_R20_NO_QUESTION_TEXT_REASON_REF: Final = "r54_no_question_text_or_draft_question_text_materialized"
P7_R54_R21_NO_TOUCH_REQUIRED_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    "api_route_changed_here",
    "db_schema_changed_here",
    "db_migration_changed_here",
    "rn_visible_contract_changed_here",
    "public_response_top_level_key_added_here",
    "public_response_key_changed_here",
    "api_db_rn_response_key_changed_here",
    "runtime_changed_here",
    "question_api_implemented",
    "question_db_schema_implemented",
    "question_rn_ui_implemented",
    "question_response_key_implemented",
    "question_trigger_logic_implemented",
    "question_storage_schema_implemented",
    "question_answer_persistence_implemented",
    "question_plan_guard_implemented",
    "question_implementation_started_here",
    "p8_question_implementation_spec_finalized_here",
    "p8_question_api_designed_here",
    "p8_question_db_schema_designed_here",
    "p8_question_rn_ui_designed_here",
    "p8_question_trigger_logic_designed_here",
    "p8_question_response_key_designed_here",
    "p8_question_plan_guard_designed_here",
)
P7_R54_R21_BODY_LEAK_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    "raw_input_included",
    "returned_surface_included",
    "comment_text_included",
    "history_body_included",
    "reviewer_free_text_included",
    "question_text_included",
    "draft_question_text_included",
    "local_absolute_path_included",
    "body_content_hash_included",
    "packet_content_hash_included",
    "terminal_output_included",
    "local_packet_exported",
    "content_hash_of_body_stored",
)
P7_R54_R20_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    key for key in P7_R54_R19_FALSE_KEY_REFS if key != "p8_question_design_material_candidate"
)
P7_R54_R21_FALSE_KEY_REFS: Final[tuple[str, ...]] = P7_R54_R20_FALSE_KEY_REFS

P7_R54_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "r19_p6_limited_human_readfeel_candidate_handoff_schema_version", "r19_p6_limited_human_readfeel_candidate_handoff_material_ref", "r19_p6_candidate_handoff_status", "r19_p5_decision_candidate_ref", "r19_ready_for_p8_material_candidate_handoff",
    "r17_body_free_post_review_summary_schema_version", "r17_body_free_post_review_summary_material_ref", "r17_body_free_post_review_summary_status", "r17_ready_for_p8_material_candidate_handoff",
    "current_received_snapshot_refs", "current_received_snapshot_ref_count", "r53_source_snapshot_refs", "r53_source_snapshot_ref_count", "r53_refs_are_current_received_refs",
    "review_session_status", "p8_question_design_material_candidate_status", "p8_question_design_material_candidate_reason_refs", "p8_question_design_material_candidate_materialized_here", "p8_start_allowed_false_reason_refs",
    "p5_human_blind_qa_confirmed_candidate", "p5_human_blind_qa_confirmed_final", "p5_repair_return_candidate", "p5_review_inconclusive", "p5_decision_candidate_ref", "p5_decision_finalized_here",
    "p6_limited_human_readfeel_candidate", "p6_limited_human_readfeel_start_allowed",
    "question_need_primary_class_counts", "p8_material_candidate_primary_class_refs", "p8_material_candidate_primary_class_counts", "p8_material_candidate_observation_count", "not_question_repair_primary_class_refs", "not_question_repair_primary_class_counts", "not_question_repair_observation_count", "insufficient_material_observation_count", "repair_observation_count", "p5_repair_or_inconclusive_not_p8_material", "question_need_observation_rows_available", "question_text_designed_here", "draft_question_text_designed_here", "p8_question_api_designed_here", "p8_question_db_schema_designed_here", "p8_question_rn_ui_designed_here", "p8_question_trigger_logic_designed_here", "p8_question_response_key_designed_here", "p8_question_plan_guard_designed_here",
    "raw_input_included", "returned_surface_included", "comment_text_included", "history_body_included", "reviewer_free_text_included", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included", "terminal_output_included", "local_packet_exported", "content_hash_of_body_stored",
    "p8_question_design_material_candidate", "p8_start_allowed", "p7_complete", "release_allowed", "hold004_close_allowed",
    "body_full_packet_generated_here", "actual_body_full_packet_generated_here", "actual_review_run_here", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_reviewer_notes_materialized_here", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_question_need_observation_summary_materialized_here", "actual_disposal_run_here", "disposal_receipt_materialized_here", "actual_disposal_receipt_materialized_here", "post_review_summary_materialized_here", "p5_actual_review_still_not_run_by_helper",
    "r54_0_scope_current_received_snapshot_refrozen", "r54_1_r53_source_delta_current_snapshot_override_adopted", "r54_2_validation_evidence_intake_done", "r54_3_local_only_actual_review_preflight_built", "r54_4_actual_review_session_envelope_built", "r54_5_24_case_manifest_freeze_built", "r54_6_local_only_body_full_packet_generation_request_built", "r54_7_packet_completeness_export_denylist_scan_built", "r54_8_reviewer_instruction_rating_form_freeze_built", "r54_9_actual_human_review_operation_state_capture_built", "r54_10_sanitized_actual_review_result_capture_built", "r54_11_rating_row_normalization_built", "r54_12_readfeel_blocker_execution_blocker_ingestion_built", "r54_13_question_need_observation_row_normalization_built", "r54_14_rating_question_observation_consistency_guard_built", "r54_15_pause_abort_expiration_protocol_built", "r54_16_purge_disposal_receipt_built", "r54_17_body_free_post_review_summary_built", "r54_18_p5_decision_candidate_separation_built", "r54_19_p6_limited_human_readfeel_candidate_handoff_built", "r54_20_p8_question_design_material_candidate_handoff_built",
    "execution_blocker_ids", "open_execution_blocker_ids", "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract", "r54_public_no_touch_contract", "body_free_markers", "body_free",
    *P7_R54_R20_FALSE_KEY_REFS,
    "validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here",
)

P7_R54_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "r20_p8_question_design_material_candidate_handoff_schema_version", "r20_p8_question_design_material_candidate_handoff_material_ref", "r20_p8_question_design_material_candidate_status", "r20_ready_for_final_validation",
    "current_received_snapshot_refs", "current_received_snapshot_ref_count", "r53_source_snapshot_refs", "r53_source_snapshot_ref_count", "r53_refs_are_current_received_refs",
    "review_session_status", "final_validation_status", "final_validation_reason_refs", "final_no_body_leak_no_question_text_no_touch_validation_materialized_here", "final_validation_passed", "ready_for_r52_reintake_handoff",
    "body_leak_detected", "question_text_detected", "no_touch_violation_detected", "no_touch_touched_refs", "additional_bodyfree_material_scan_count", "final_validation_scanned_material_count", "body_leak_checked_key_refs", "question_text_checked_key_refs", "no_touch_checked_key_refs",
    "raw_input_included", "returned_surface_included", "comment_text_included", "history_body_included", "reviewer_free_text_included", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included", "terminal_output_included", "local_packet_exported", "content_hash_of_body_stored",
    "api_route_changed_here", "db_schema_changed_here", "db_migration_changed_here", "rn_visible_contract_changed_here", "public_response_top_level_key_added_here", "public_response_key_changed_here", "api_db_rn_response_key_changed_here", "runtime_changed_here", "question_api_implemented", "question_db_schema_implemented", "question_rn_ui_implemented", "question_response_key_implemented", "question_trigger_logic_implemented", "question_storage_schema_implemented", "question_answer_persistence_implemented", "question_plan_guard_implemented", "question_implementation_started_here", "p8_question_implementation_spec_finalized_here", "p8_question_api_designed_here", "p8_question_db_schema_designed_here", "p8_question_rn_ui_designed_here", "p8_question_trigger_logic_designed_here", "p8_question_response_key_designed_here", "p8_question_plan_guard_designed_here",
    "p5_human_blind_qa_confirmed_candidate", "p5_human_blind_qa_confirmed_final", "p5_repair_return_candidate", "p5_review_inconclusive", "p5_decision_candidate_ref", "p5_decision_finalized_here", "p6_limited_human_readfeel_candidate", "p6_limited_human_readfeel_start_allowed", "p8_question_design_material_candidate", "p8_start_allowed", "p7_complete", "release_allowed", "hold004_close_allowed",
    "body_full_packet_generated_here", "actual_body_full_packet_generated_here", "actual_review_run_here", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_reviewer_notes_materialized_here", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_question_need_observation_summary_materialized_here", "actual_disposal_run_here", "disposal_receipt_materialized_here", "actual_disposal_receipt_materialized_here", "post_review_summary_materialized_here", "p5_actual_review_still_not_run_by_helper",
    "r54_0_scope_current_received_snapshot_refrozen", "r54_1_r53_source_delta_current_snapshot_override_adopted", "r54_2_validation_evidence_intake_done", "r54_3_local_only_actual_review_preflight_built", "r54_4_actual_review_session_envelope_built", "r54_5_24_case_manifest_freeze_built", "r54_6_local_only_body_full_packet_generation_request_built", "r54_7_packet_completeness_export_denylist_scan_built", "r54_8_reviewer_instruction_rating_form_freeze_built", "r54_9_actual_human_review_operation_state_capture_built", "r54_10_sanitized_actual_review_result_capture_built", "r54_11_rating_row_normalization_built", "r54_12_readfeel_blocker_execution_blocker_ingestion_built", "r54_13_question_need_observation_row_normalization_built", "r54_14_rating_question_observation_consistency_guard_built", "r54_15_pause_abort_expiration_protocol_built", "r54_16_purge_disposal_receipt_built", "r54_17_body_free_post_review_summary_built", "r54_18_p5_decision_candidate_separation_built", "r54_19_p6_limited_human_readfeel_candidate_handoff_built", "r54_20_p8_question_design_material_candidate_handoff_built", "r54_21_final_no_body_leak_no_question_text_no_touch_validation_built",
    "execution_blocker_ids", "open_execution_blocker_ids", "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract", "r54_public_no_touch_contract", "body_free_markers", "body_free",
    *P7_R54_R21_FALSE_KEY_REFS,
    "validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here",
)


def _r54_primary_class_counts_from_summary(summary: Mapping[str, Any]) -> dict[str, int]:
    raw_counts = safe_mapping(summary.get("question_need_primary_class_counts"))
    return {clean_identifier(key, default="unknown_primary_class", max_length=160): _safe_non_negative_int_r54(value) for key, value in raw_counts.items()}


def _r54_count_for_refs(counts: Mapping[str, int], refs: Sequence[str]) -> int:
    return sum(_safe_non_negative_int_r54(counts.get(ref)) for ref in refs)


def _r54_subset_counts(counts: Mapping[str, int], refs: Sequence[str]) -> dict[str, int]:
    return {ref: _safe_non_negative_int_r54(counts.get(ref)) for ref in refs}


P7_R54_R21_BODY_LEAK_FORBIDDEN_PAYLOAD_KEY_REFS: Final[tuple[str, ...]] = (
    "raw_input", "raw_memo", "raw_memo_action", "raw_history_text", "returned_emlis_surface",
    "returned_surface_body", "comment_text", "comment_text_body", "candidate_body",
    "reviewer_free_text", "reviewer_notes", "history_body", "local_absolute_path",
    "local_path", "body_content_hash", "packet_content_hash", "body_hash", "packet_hash",
    "terminal_output", "stdout", "stderr",
)
P7_R54_R21_QUESTION_TEXT_FORBIDDEN_PAYLOAD_KEY_REFS: Final[tuple[str, ...]] = (
    "question_text", "draft_question_text", "actual_question_text", "question_body", "draft_question_body",
)


def _r54_truthy_forbidden_key_refs(data: Any, *, key_refs: Sequence[str]) -> bool:
    if isinstance(data, Mapping):
        for key, value in data.items():
            if key in key_refs and bool(value):
                return True
            if _r54_truthy_forbidden_key_refs(value, key_refs=key_refs):
                return True
    elif isinstance(data, (list, tuple)):
        return any(_r54_truthy_forbidden_key_refs(item, key_refs=key_refs) for item in data)
    return False


def _r54_no_touch_touched_refs_from_mapping(data: Mapping[str, Any]) -> list[str]:
    touched = [key for key in P7_R54_R21_NO_TOUCH_REQUIRED_FALSE_KEY_REFS if data.get(key) is True]
    public_contract = safe_mapping(data.get("public_contract"))
    touched.extend(f"public_contract.{key}" for key, value in public_contract.items() if value is True)
    no_touch_contract = safe_mapping(data.get("r54_public_no_touch_contract"))
    touched.extend(f"r54_public_no_touch_contract.{key}" for key, value in no_touch_contract.items() if value is True)
    return dedupe_identifiers(touched, limit=80, max_length=180)


def _r54_body_leak_detected_from_mapping(data: Mapping[str, Any]) -> bool:
    return any(data.get(key) is True for key in P7_R54_R21_BODY_LEAK_FALSE_KEY_REFS) or _r54_truthy_forbidden_key_refs(data, key_refs=P7_R54_R21_BODY_LEAK_FORBIDDEN_PAYLOAD_KEY_REFS)


def _r54_question_text_detected_from_mapping(data: Mapping[str, Any]) -> bool:
    return (
        data.get("question_text_included") is True
        or data.get("draft_question_text_included") is True
        or _r54_truthy_forbidden_key_refs(data, key_refs=P7_R54_R21_QUESTION_TEXT_FORBIDDEN_PAYLOAD_KEY_REFS)
    )


def build_p7_r54_p8_question_design_material_candidate_handoff_bodyfree(
    *,
    p6_limited_human_readfeel_candidate_handoff: Mapping[str, Any] | None = None,
    r19_p6_limited_human_readfeel_candidate_handoff: Mapping[str, Any] | None = None,
    body_free_post_review_summary: Mapping[str, Any] | None = None,
    r17_body_free_post_review_summary: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_p8_question_design_material_candidate_handoff_bodyfree",
) -> dict[str, Any]:
    """Build R54-20 body-free P8 question-design material candidate handoff."""

    if p6_limited_human_readfeel_candidate_handoff is not None and r19_p6_limited_human_readfeel_candidate_handoff is not None:
        raise ValueError("provide only one R54-19 P6 limited human readfeel candidate handoff value")
    if body_free_post_review_summary is not None and r17_body_free_post_review_summary is not None:
        raise ValueError("provide only one R54-17 body-free post-review summary value")
    r19 = safe_mapping(
        p6_limited_human_readfeel_candidate_handoff
        if p6_limited_human_readfeel_candidate_handoff is not None
        else r19_p6_limited_human_readfeel_candidate_handoff
        if r19_p6_limited_human_readfeel_candidate_handoff is not None
        else build_p7_r54_p6_limited_human_readfeel_candidate_handoff_bodyfree()
    )
    assert_p7_r54_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract(r19)
    summary = safe_mapping(
        body_free_post_review_summary
        if body_free_post_review_summary is not None
        else r17_body_free_post_review_summary
        if r17_body_free_post_review_summary is not None
        else build_p7_r54_body_free_post_review_summary_bodyfree()
    )
    assert_p7_r54_body_free_post_review_summary_bodyfree_contract(summary)

    r19_ready = r19.get("r54_19_p6_limited_human_readfeel_candidate_handoff_built") is True and r19.get("p6_candidate_handoff_materialized_here") is True
    summary_ready = summary.get("r54_17_body_free_post_review_summary_built") is True and summary.get("post_review_summary_status") == "READY_FOR_P5_DECISION_CANDIDATE_SEPARATION"
    primary_counts = _r54_primary_class_counts_from_summary(summary)
    p8_primary_counts = _r54_subset_counts(primary_counts, P7_R54_P8_MATERIAL_CANDIDATE_PRIMARY_CLASS_REFS)
    not_question_counts = _r54_subset_counts(primary_counts, P7_R54_NOT_QUESTION_REPAIR_PRIMARY_CLASS_REFS)
    p8_observation_count = _r54_count_for_refs(primary_counts, P7_R54_P8_MATERIAL_CANDIDATE_PRIMARY_CLASS_REFS)
    not_question_repair_count = _r54_count_for_refs(primary_counts, P7_R54_NOT_QUESTION_REPAIR_PRIMARY_CLASS_REFS)
    insufficient_count = _safe_non_negative_int_r54(primary_counts.get("insufficient_material_execution_blocker"))
    repair_observation_count = _safe_non_negative_int_r54(summary.get("repair_observation_count"))
    p5_repair_or_inconclusive = r19.get("p5_repair_return_candidate") is True or r19.get("p5_review_inconclusive") is True

    if not r19_ready:
        status = "BLOCKED_BY_R54_19_P6_CANDIDATE_HANDOFF"
        reason_refs = ["r54_p8_material_handoff_blocked_by_r19_not_ready", P7_R54_R20_P8_START_ALLOWED_FALSE_REASON_REF]
        built = False
        candidate = False
        blockers = ["r54_p8_material_handoff_blocked_by_r19_not_ready"]
    elif not summary_ready:
        status = "BLOCKED_BY_R54_17_BODY_FREE_POST_REVIEW_SUMMARY_FOR_P8_MATERIAL"
        reason_refs = ["r54_p8_material_handoff_blocked_by_r17_summary_not_ready", P7_R54_R20_P8_START_ALLOWED_FALSE_REASON_REF]
        built = False
        candidate = False
        blockers = ["r54_p8_material_handoff_blocked_by_r17_summary_not_ready"]
    else:
        built = True
        blockers = []
        if r19.get("p5_repair_return_candidate") is True:
            status = "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_NOT_AVAILABLE_P5_REPAIR_RETURN"
            reason_refs = ["r54_p8_material_false_p5_repair_return_not_hidden_by_question", P7_R54_R20_P8_START_ALLOWED_FALSE_REASON_REF]
            candidate = False
        elif r19.get("p5_review_inconclusive") is True:
            status = "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_NOT_AVAILABLE_P5_INCONCLUSIVE"
            reason_refs = ["r54_p8_material_false_p5_inconclusive_not_hidden_by_question", P7_R54_R20_P8_START_ALLOWED_FALSE_REASON_REF]
            candidate = False
        elif not_question_repair_count > 0 or repair_observation_count > 0:
            status = "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_NOT_AVAILABLE_NOT_QUESTION_REPAIR"
            reason_refs = ["r54_p8_material_false_not_question_repair_required", P7_R54_R20_P8_START_ALLOWED_FALSE_REASON_REF]
            candidate = False
        elif insufficient_count > 0:
            status = "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_NOT_AVAILABLE_INSUFFICIENT_MATERIAL"
            reason_refs = ["r54_p8_material_false_insufficient_material_execution_blocker", P7_R54_R20_P8_START_ALLOWED_FALSE_REASON_REF]
            candidate = False
        elif p8_observation_count > 0:
            status = "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_TRUE"
            reason_refs = ["r54_p8_material_candidate_true_from_body_free_question_need_observation_counts", P7_R54_R20_P8_START_ALLOWED_FALSE_REASON_REF, P7_R54_R20_NO_QUESTION_TEXT_REASON_REF]
            candidate = True
        else:
            status = "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_NOT_AVAILABLE_NO_OBSERVATION"
            reason_refs = ["r54_p8_material_false_no_question_need_observation_candidate_count", P7_R54_R20_P8_START_ALLOWED_FALSE_REASON_REF]
            candidate = False

    allowed_truthy = {
        "validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here", "actual_review_run_here", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_question_need_observation_summary_materialized_here", "disposal_receipt_materialized_here", "actual_disposal_receipt_materialized_here", "post_review_summary_materialized_here", "p5_human_blind_qa_confirmed_candidate", "p5_repair_return_candidate", "p5_review_inconclusive", "p6_limited_human_readfeel_candidate", "p8_question_design_material_candidate",
    }
    material = {
        "schema_version": P7_R54_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_STEP,
        "scope": P7_R54_SCOPE,
        "policy_kind": P7_R54_POLICY_KIND,
        "policy_section": P7_R54_R20_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_p8_question_design_material_candidate_handoff_bodyfree", max_length=180),
        "review_session_id": _safe_review_session_id(r19.get("review_session_id") or summary.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r19_p6_limited_human_readfeel_candidate_handoff_schema_version": P7_R54_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        "r19_p6_limited_human_readfeel_candidate_handoff_material_ref": clean_identifier(r19.get("material_id"), default="p7_r54_p6_limited_human_readfeel_candidate_handoff_bodyfree", max_length=180),
        "r19_p6_candidate_handoff_status": clean_identifier(r19.get("p6_candidate_handoff_status"), default="BLOCKED_BY_R54_18_P5_DECISION_CANDIDATE_SEPARATION", max_length=180),
        "r19_p5_decision_candidate_ref": clean_identifier(r19.get("p5_decision_candidate_ref"), default="P5_NOT_REVIEWED", max_length=160),
        "r19_ready_for_p8_material_candidate_handoff": bool(r19_ready),
        "r17_body_free_post_review_summary_schema_version": P7_R54_BODY_FREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION,
        "r17_body_free_post_review_summary_material_ref": clean_identifier(summary.get("material_id"), default="p7_r54_body_free_post_review_summary_bodyfree", max_length=180),
        "r17_body_free_post_review_summary_status": clean_identifier(summary.get("post_review_summary_status"), default="BLOCKED_BY_POST_REVIEW_SUMMARY_REQUIREMENTS", max_length=180),
        "r17_ready_for_p8_material_candidate_handoff": bool(summary_ready),
        "current_received_snapshot_refs": dict(P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "r53_source_snapshot_refs": _r53_source_snapshot_refs(None),
        "r53_source_snapshot_ref_count": len(_r53_source_snapshot_refs(None)),
        "r53_refs_are_current_received_refs": False,
        "review_session_status": "R54_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_READY" if built else "R54_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_BLOCKED",
        "p8_question_design_material_candidate_status": status,
        "p8_question_design_material_candidate_reason_refs": reason_refs,
        "p8_question_design_material_candidate_materialized_here": built,
        "p8_start_allowed_false_reason_refs": [P7_R54_R20_P8_START_ALLOWED_FALSE_REASON_REF],
        "p5_human_blind_qa_confirmed_candidate": r19.get("p5_human_blind_qa_confirmed_candidate") is True and built,
        "p5_human_blind_qa_confirmed_final": False,
        "p5_repair_return_candidate": r19.get("p5_repair_return_candidate") is True and built,
        "p5_review_inconclusive": r19.get("p5_review_inconclusive") is True and built,
        "p5_decision_candidate_ref": clean_identifier(r19.get("p5_decision_candidate_ref"), default="P5_NOT_REVIEWED", max_length=160),
        "p5_decision_finalized_here": False,
        "p6_limited_human_readfeel_candidate": r19.get("p6_limited_human_readfeel_candidate") is True and built,
        "p6_limited_human_readfeel_start_allowed": False,
        "question_need_primary_class_counts": primary_counts if summary_ready else {},
        "p8_material_candidate_primary_class_refs": list(P7_R54_P8_MATERIAL_CANDIDATE_PRIMARY_CLASS_REFS),
        "p8_material_candidate_primary_class_counts": p8_primary_counts if summary_ready else {},
        "p8_material_candidate_observation_count": p8_observation_count if summary_ready else 0,
        "not_question_repair_primary_class_refs": list(P7_R54_NOT_QUESTION_REPAIR_PRIMARY_CLASS_REFS),
        "not_question_repair_primary_class_counts": not_question_counts if summary_ready else {},
        "not_question_repair_observation_count": not_question_repair_count if summary_ready else 0,
        "insufficient_material_observation_count": insufficient_count if summary_ready else 0,
        "repair_observation_count": repair_observation_count if summary_ready else 0,
        "p5_repair_or_inconclusive_not_p8_material": bool(p5_repair_or_inconclusive or not_question_repair_count > 0 or repair_observation_count > 0),
        "question_need_observation_rows_available": bool(summary_ready and _safe_non_negative_int_r54(summary.get("question_observation_row_count")) == P7_R51_REQUIRED_CASE_COUNT),
        "question_text_designed_here": False,
        "draft_question_text_designed_here": False,
        "p8_question_api_designed_here": False,
        "p8_question_db_schema_designed_here": False,
        "p8_question_rn_ui_designed_here": False,
        "p8_question_trigger_logic_designed_here": False,
        "p8_question_response_key_designed_here": False,
        "p8_question_plan_guard_designed_here": False,
        "raw_input_included": False,
        "returned_surface_included": False,
        "comment_text_included": False,
        "history_body_included": False,
        "reviewer_free_text_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_absolute_path_included": False,
        "body_content_hash_included": False,
        "packet_content_hash_included": False,
        "terminal_output_included": False,
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "p8_question_design_material_candidate": candidate,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "hold004_close_allowed": False,
        "body_full_packet_generated_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_review_run_here": _r54_bool(r19.get("actual_review_run_here")) and built,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "actual_rating_rows_materialized_here": _r54_bool(r19.get("actual_rating_rows_materialized_here")) and built,
        "actual_blocker_rows_materialized_here": _r54_bool(r19.get("actual_blocker_rows_materialized_here")) and built,
        "actual_execution_blocker_rows_materialized_here": _r54_bool(r19.get("actual_execution_blocker_rows_materialized_here")) and built,
        "actual_question_need_observation_rows_materialized_here": _r54_bool(r19.get("actual_question_need_observation_rows_materialized_here")) and built,
        "actual_question_need_observation_summary_materialized_here": _r54_bool(r19.get("actual_question_need_observation_summary_materialized_here")) and built,
        "actual_disposal_run_here": False,
        "disposal_receipt_materialized_here": _r54_bool(r19.get("disposal_receipt_materialized_here")) and built,
        "actual_disposal_receipt_materialized_here": _r54_bool(r19.get("actual_disposal_receipt_materialized_here")) and built,
        "post_review_summary_materialized_here": _r54_bool(r19.get("post_review_summary_materialized_here")) and built,
        "p5_actual_review_still_not_run_by_helper": True,
        "r54_0_scope_current_received_snapshot_refrozen": True,
        "r54_1_r53_source_delta_current_snapshot_override_adopted": True,
        "r54_2_validation_evidence_intake_done": _r54_bool(r19.get("r54_2_validation_evidence_intake_done")) and built,
        "r54_3_local_only_actual_review_preflight_built": _r54_bool(r19.get("r54_3_local_only_actual_review_preflight_built")) and built,
        "r54_4_actual_review_session_envelope_built": _r54_bool(r19.get("r54_4_actual_review_session_envelope_built")) and built,
        "r54_5_24_case_manifest_freeze_built": _r54_bool(r19.get("r54_5_24_case_manifest_freeze_built")) and built,
        "r54_6_local_only_body_full_packet_generation_request_built": _r54_bool(r19.get("r54_6_local_only_body_full_packet_generation_request_built")) and built,
        "r54_7_packet_completeness_export_denylist_scan_built": _r54_bool(r19.get("r54_7_packet_completeness_export_denylist_scan_built")) and built,
        "r54_8_reviewer_instruction_rating_form_freeze_built": _r54_bool(r19.get("r54_8_reviewer_instruction_rating_form_freeze_built")) and built,
        "r54_9_actual_human_review_operation_state_capture_built": _r54_bool(r19.get("r54_9_actual_human_review_operation_state_capture_built")) and built,
        "r54_10_sanitized_actual_review_result_capture_built": _r54_bool(r19.get("r54_10_sanitized_actual_review_result_capture_built")) and built,
        "r54_11_rating_row_normalization_built": _r54_bool(r19.get("r54_11_rating_row_normalization_built")) and built,
        "r54_12_readfeel_blocker_execution_blocker_ingestion_built": _r54_bool(r19.get("r54_12_readfeel_blocker_execution_blocker_ingestion_built")) and built,
        "r54_13_question_need_observation_row_normalization_built": _r54_bool(r19.get("r54_13_question_need_observation_row_normalization_built")) and built,
        "r54_14_rating_question_observation_consistency_guard_built": _r54_bool(r19.get("r54_14_rating_question_observation_consistency_guard_built")) and built,
        "r54_15_pause_abort_expiration_protocol_built": _r54_bool(r19.get("r54_15_pause_abort_expiration_protocol_built")) and built,
        "r54_16_purge_disposal_receipt_built": _r54_bool(r19.get("r54_16_purge_disposal_receipt_built")) and built,
        "r54_17_body_free_post_review_summary_built": _r54_bool(r19.get("r54_17_body_free_post_review_summary_built")) and summary_ready and built,
        "r54_18_p5_decision_candidate_separation_built": _r54_bool(r19.get("r54_18_p5_decision_candidate_separation_built")) and built,
        "r54_19_p6_limited_human_readfeel_candidate_handoff_built": _r54_bool(r19.get("r54_19_p6_limited_human_readfeel_candidate_handoff_built")) and built,
        "r54_20_p8_question_design_material_candidate_handoff_built": built,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "implemented_steps": list(P7_R54_R20_IMPLEMENTED_STEPS if built else P7_R54_R19_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_R20_NOT_YET_IMPLEMENTED_STEPS if built else P7_R54_R19_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R54_R20_NEXT_REQUIRED_STEP_REF if built else P7_R54_R20_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "next_required_step": P7_R54_R20_NEXT_REQUIRED_STEP_REF if built else P7_R54_R20_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_except(allowed_truthy),
        "validation_evidence_intake_done_here": _r54_bool(r19.get("validation_evidence_intake_done_here")) and built,
        "local_root_preflight_passed_here": _r54_bool(r19.get("local_root_preflight_passed_here")) and built,
        "explicit_allow_present_here": _r54_bool(r19.get("explicit_allow_present_here")) and built,
        "purge_plan_verified_here": _r54_bool(r19.get("purge_plan_verified_here")) and built,
    }
    assert_p7_r54_p8_question_design_material_candidate_handoff_bodyfree_contract(material)
    return material


def assert_p7_r54_p8_question_design_material_candidate_handoff_bodyfree_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_REQUIRED_FIELD_REFS, source="p7_r54_p8_question_design_material_candidate_handoff")
    _assert_body_free_common_with_false_keys(data, schema_version=P7_R54_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION, source="p7_r54_p8_question_design_material_candidate_handoff", false_key_refs=P7_R54_R20_FALSE_KEY_REFS)
    _assert_current_refs(data, source="p7_r54_p8_question_design_material_candidate_handoff")
    if data.get("policy_section") != P7_R54_R20_STEP_REF:
        raise ValueError("R54 R20 policy section changed")
    if data.get("p8_question_design_material_candidate_status") not in P7_R54_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_STATUS_REFS:
        raise ValueError("R54 R20 P8 material candidate status changed")
    for false_key in (
        "p8_start_allowed", "p7_complete", "release_allowed", "hold004_close_allowed", "p5_human_blind_qa_confirmed_final", "p5_decision_finalized_here", "p6_limited_human_readfeel_start_allowed", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_disposal_run_here", "actual_reviewer_notes_materialized_here", "body_full_packet_generated_here", "actual_body_full_packet_generated_here", "raw_input_included", "returned_surface_included", "comment_text_included", "history_body_included", "reviewer_free_text_included", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included", "terminal_output_included", "local_packet_exported", "content_hash_of_body_stored", "question_text_designed_here", "draft_question_text_designed_here", "p8_question_api_designed_here", "p8_question_db_schema_designed_here", "p8_question_rn_ui_designed_here", "p8_question_trigger_logic_designed_here", "p8_question_response_key_designed_here", "p8_question_plan_guard_designed_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 R20 must keep {false_key}=False")
    if P7_R54_R20_P8_START_ALLOWED_FALSE_REASON_REF not in tuple(data.get("p8_start_allowed_false_reason_refs") or ()):  # type: ignore[arg-type]
        raise ValueError("R54 R20 must keep P8 start_allowed=false reason")
    if data.get("p8_question_design_material_candidate") is True:
        if data.get("p8_question_design_material_candidate_status") != "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_TRUE":
            raise ValueError("R54 R20 candidate true status mismatch")
        if _safe_non_negative_int_r54(data.get("p8_material_candidate_observation_count")) <= 0:
            raise ValueError("R54 R20 candidate true requires candidate observation count")
        if data.get("p5_repair_return_candidate") is not False or data.get("p5_review_inconclusive") is not False or data.get("p5_human_blind_qa_confirmed_candidate") is not True:
            raise ValueError("R54 R20 candidate true must not hide P5 repair or inconclusive")
        if _safe_non_negative_int_r54(data.get("not_question_repair_observation_count")) != 0 or _safe_non_negative_int_r54(data.get("repair_observation_count")) != 0:
            raise ValueError("R54 R20 candidate true must not include not-question repair observations")
    else:
        if data.get("p8_question_design_material_candidate_status") == "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_TRUE":
            raise ValueError("R54 R20 candidate false cannot use true status")
    if data.get("p5_repair_or_inconclusive_not_p8_material") is True and data.get("p8_question_design_material_candidate") is True:
        raise ValueError("R54 R20 must not turn P5 repair/inconclusive into P8 material")
    if data.get("p8_question_design_material_candidate_status") in {"BLOCKED_BY_R54_19_P6_CANDIDATE_HANDOFF", "BLOCKED_BY_R54_17_BODY_FREE_POST_REVIEW_SUMMARY_FOR_P8_MATERIAL"}:
        if data.get("p8_question_design_material_candidate_materialized_here") is not False or data.get("r54_20_p8_question_design_material_candidate_handoff_built") is not False:
            raise ValueError("R54 R20 blocked materialization mismatch")
        if data.get("next_required_step") != P7_R54_R20_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R20 blocked next step changed")
    else:
        if data.get("p8_question_design_material_candidate_materialized_here") is not True or data.get("r54_20_p8_question_design_material_candidate_handoff_built") is not True:
            raise ValueError("R54 R20 ready handoff must materialize")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_R20_IMPLEMENTED_STEPS:
            raise ValueError("R54 R20 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_R20_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 R20 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_R20_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R20 next step changed")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_p8_question_design_material_candidate_handoff")
    return True


def build_p7_r54_final_no_body_leak_no_question_text_no_touch_validation_bodyfree(
    *,
    p8_question_design_material_candidate_handoff: Mapping[str, Any] | None = None,
    r20_p8_question_design_material_candidate_handoff: Mapping[str, Any] | None = None,
    additional_bodyfree_materials_to_scan: Iterable[Mapping[str, Any]] | None = None,
    material_id: Any = "p7_r54_final_no_body_leak_no_question_text_no_touch_validation_bodyfree",
) -> dict[str, Any]:
    """Build R54-21 final body-free no-leak/no-question-text/no-touch validation."""

    if p8_question_design_material_candidate_handoff is not None and r20_p8_question_design_material_candidate_handoff is not None:
        raise ValueError("provide only one R54-20 P8 material candidate handoff value")
    r20 = safe_mapping(
        p8_question_design_material_candidate_handoff
        if p8_question_design_material_candidate_handoff is not None
        else r20_p8_question_design_material_candidate_handoff
        if r20_p8_question_design_material_candidate_handoff is not None
        else build_p7_r54_p8_question_design_material_candidate_handoff_bodyfree()
    )
    assert_p7_r54_p8_question_design_material_candidate_handoff_bodyfree_contract(r20)
    r20_ready = r20.get("r54_20_p8_question_design_material_candidate_handoff_built") is True and r20.get("p8_question_design_material_candidate_materialized_here") is True
    additional_scan_materials = tuple(
        safe_mapping(material)
        for material in (additional_bodyfree_materials_to_scan or ())
    )
    scan_materials = (r20, *additional_scan_materials)
    body_leak = any(_r54_body_leak_detected_from_mapping(material) for material in scan_materials)
    question_text = any(_r54_question_text_detected_from_mapping(material) for material in scan_materials)
    no_touch_refs = dedupe_identifiers(
        [ref for material in scan_materials for ref in _r54_no_touch_touched_refs_from_mapping(material)],
        limit=80,
        max_length=180,
    )
    no_touch_violation = bool(no_touch_refs)
    if not r20_ready:
        status = "FINAL_VALIDATION_BLOCKED_BY_R54_20_P8_MATERIAL_HANDOFF"
        reason_refs = ["r54_final_validation_blocked_by_r20_not_ready"]
        built = False
        passed = False
        blockers = ["r54_final_validation_blocked_by_r20_not_ready"]
    elif question_text:
        status = "FINAL_VALIDATION_BLOCKED_BY_QUESTION_TEXT"
        reason_refs = ["r54_final_validation_question_text_detected"]
        built = False
        passed = False
        blockers = ["r54_final_validation_question_text_detected"]
    elif body_leak:
        status = "FINAL_VALIDATION_BLOCKED_BY_BODY_LEAK"
        reason_refs = ["r54_final_validation_body_leak_detected"]
        built = False
        passed = False
        blockers = ["r54_final_validation_body_leak_detected"]
    elif no_touch_violation:
        status = "FINAL_VALIDATION_BLOCKED_BY_NO_TOUCH_VIOLATION"
        reason_refs = ["r54_final_validation_no_touch_violation_detected"]
        built = False
        passed = False
        blockers = ["r54_final_validation_no_touch_violation_detected"]
    else:
        status = "FINAL_BODY_FREE_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_READY"
        reason_refs = ["r54_final_validation_no_body_leak_no_question_text_no_touch_ready"]
        built = True
        passed = True
        blockers = []

    allowed_truthy = {
        "validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here", "actual_review_run_here", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_question_need_observation_summary_materialized_here", "disposal_receipt_materialized_here", "actual_disposal_receipt_materialized_here", "post_review_summary_materialized_here", "p5_human_blind_qa_confirmed_candidate", "p5_repair_return_candidate", "p5_review_inconclusive", "p6_limited_human_readfeel_candidate", "p8_question_design_material_candidate",
    }
    material = {
        "schema_version": P7_R54_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_STEP,
        "scope": P7_R54_SCOPE,
        "policy_kind": P7_R54_POLICY_KIND,
        "policy_section": P7_R54_R21_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_final_no_body_leak_no_question_text_no_touch_validation_bodyfree", max_length=180),
        "review_session_id": _safe_review_session_id(r20.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r20_p8_question_design_material_candidate_handoff_schema_version": P7_R54_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        "r20_p8_question_design_material_candidate_handoff_material_ref": clean_identifier(r20.get("material_id"), default="p7_r54_p8_question_design_material_candidate_handoff_bodyfree", max_length=180),
        "r20_p8_question_design_material_candidate_status": clean_identifier(r20.get("p8_question_design_material_candidate_status"), default="BLOCKED_BY_R54_19_P6_CANDIDATE_HANDOFF", max_length=180),
        "r20_ready_for_final_validation": bool(r20_ready),
        "current_received_snapshot_refs": dict(P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "r53_source_snapshot_refs": _r53_source_snapshot_refs(None),
        "r53_source_snapshot_ref_count": len(_r53_source_snapshot_refs(None)),
        "r53_refs_are_current_received_refs": False,
        "review_session_status": "R54_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_READY" if built else "R54_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_BLOCKED",
        "final_validation_status": status,
        "final_validation_reason_refs": reason_refs,
        "final_no_body_leak_no_question_text_no_touch_validation_materialized_here": built,
        "final_validation_passed": passed,
        "ready_for_r52_reintake_handoff": passed,
        "body_leak_detected": body_leak,
        "question_text_detected": question_text,
        "no_touch_violation_detected": no_touch_violation,
        "no_touch_touched_refs": no_touch_refs,
        "additional_bodyfree_material_scan_count": len(additional_scan_materials),
        "final_validation_scanned_material_count": len(scan_materials),
        "body_leak_checked_key_refs": list(P7_R54_R21_BODY_LEAK_FALSE_KEY_REFS),
        "question_text_checked_key_refs": ["question_text_included", "draft_question_text_included"],
        "no_touch_checked_key_refs": list(P7_R54_R21_NO_TOUCH_REQUIRED_FALSE_KEY_REFS),
        "raw_input_included": False,
        "returned_surface_included": False,
        "comment_text_included": False,
        "history_body_included": False,
        "reviewer_free_text_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_absolute_path_included": False,
        "body_content_hash_included": False,
        "packet_content_hash_included": False,
        "terminal_output_included": False,
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "api_route_changed_here": False,
        "db_schema_changed_here": False,
        "db_migration_changed_here": False,
        "rn_visible_contract_changed_here": False,
        "public_response_top_level_key_added_here": False,
        "public_response_key_changed_here": False,
        "api_db_rn_response_key_changed_here": False,
        "runtime_changed_here": False,
        "question_api_implemented": False,
        "question_db_schema_implemented": False,
        "question_rn_ui_implemented": False,
        "question_response_key_implemented": False,
        "question_trigger_logic_implemented": False,
        "question_storage_schema_implemented": False,
        "question_answer_persistence_implemented": False,
        "question_plan_guard_implemented": False,
        "question_implementation_started_here": False,
        "p8_question_implementation_spec_finalized_here": False,
        "p8_question_api_designed_here": False,
        "p8_question_db_schema_designed_here": False,
        "p8_question_rn_ui_designed_here": False,
        "p8_question_trigger_logic_designed_here": False,
        "p8_question_response_key_designed_here": False,
        "p8_question_plan_guard_designed_here": False,
        "p5_human_blind_qa_confirmed_candidate": _r54_bool(r20.get("p5_human_blind_qa_confirmed_candidate")) and r20_ready,
        "p5_human_blind_qa_confirmed_final": False,
        "p5_repair_return_candidate": _r54_bool(r20.get("p5_repair_return_candidate")) and r20_ready,
        "p5_review_inconclusive": _r54_bool(r20.get("p5_review_inconclusive")) and r20_ready,
        "p5_decision_candidate_ref": clean_identifier(r20.get("p5_decision_candidate_ref"), default="P5_NOT_REVIEWED", max_length=160),
        "p5_decision_finalized_here": False,
        "p6_limited_human_readfeel_candidate": _r54_bool(r20.get("p6_limited_human_readfeel_candidate")) and r20_ready,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_question_design_material_candidate": _r54_bool(r20.get("p8_question_design_material_candidate")) and r20_ready,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "hold004_close_allowed": False,
        "body_full_packet_generated_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_review_run_here": _r54_bool(r20.get("actual_review_run_here")) and r20_ready,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "actual_rating_rows_materialized_here": _r54_bool(r20.get("actual_rating_rows_materialized_here")) and r20_ready,
        "actual_blocker_rows_materialized_here": _r54_bool(r20.get("actual_blocker_rows_materialized_here")) and r20_ready,
        "actual_execution_blocker_rows_materialized_here": _r54_bool(r20.get("actual_execution_blocker_rows_materialized_here")) and r20_ready,
        "actual_question_need_observation_rows_materialized_here": _r54_bool(r20.get("actual_question_need_observation_rows_materialized_here")) and r20_ready,
        "actual_question_need_observation_summary_materialized_here": _r54_bool(r20.get("actual_question_need_observation_summary_materialized_here")) and r20_ready,
        "actual_disposal_run_here": False,
        "disposal_receipt_materialized_here": _r54_bool(r20.get("disposal_receipt_materialized_here")) and r20_ready,
        "actual_disposal_receipt_materialized_here": _r54_bool(r20.get("actual_disposal_receipt_materialized_here")) and r20_ready,
        "post_review_summary_materialized_here": _r54_bool(r20.get("post_review_summary_materialized_here")) and r20_ready,
        "p5_actual_review_still_not_run_by_helper": True,
        "r54_0_scope_current_received_snapshot_refrozen": True,
        "r54_1_r53_source_delta_current_snapshot_override_adopted": True,
        "r54_2_validation_evidence_intake_done": _r54_bool(r20.get("r54_2_validation_evidence_intake_done")) and r20_ready,
        "r54_3_local_only_actual_review_preflight_built": _r54_bool(r20.get("r54_3_local_only_actual_review_preflight_built")) and r20_ready,
        "r54_4_actual_review_session_envelope_built": _r54_bool(r20.get("r54_4_actual_review_session_envelope_built")) and r20_ready,
        "r54_5_24_case_manifest_freeze_built": _r54_bool(r20.get("r54_5_24_case_manifest_freeze_built")) and r20_ready,
        "r54_6_local_only_body_full_packet_generation_request_built": _r54_bool(r20.get("r54_6_local_only_body_full_packet_generation_request_built")) and r20_ready,
        "r54_7_packet_completeness_export_denylist_scan_built": _r54_bool(r20.get("r54_7_packet_completeness_export_denylist_scan_built")) and r20_ready,
        "r54_8_reviewer_instruction_rating_form_freeze_built": _r54_bool(r20.get("r54_8_reviewer_instruction_rating_form_freeze_built")) and r20_ready,
        "r54_9_actual_human_review_operation_state_capture_built": _r54_bool(r20.get("r54_9_actual_human_review_operation_state_capture_built")) and r20_ready,
        "r54_10_sanitized_actual_review_result_capture_built": _r54_bool(r20.get("r54_10_sanitized_actual_review_result_capture_built")) and r20_ready,
        "r54_11_rating_row_normalization_built": _r54_bool(r20.get("r54_11_rating_row_normalization_built")) and r20_ready,
        "r54_12_readfeel_blocker_execution_blocker_ingestion_built": _r54_bool(r20.get("r54_12_readfeel_blocker_execution_blocker_ingestion_built")) and r20_ready,
        "r54_13_question_need_observation_row_normalization_built": _r54_bool(r20.get("r54_13_question_need_observation_row_normalization_built")) and r20_ready,
        "r54_14_rating_question_observation_consistency_guard_built": _r54_bool(r20.get("r54_14_rating_question_observation_consistency_guard_built")) and r20_ready,
        "r54_15_pause_abort_expiration_protocol_built": _r54_bool(r20.get("r54_15_pause_abort_expiration_protocol_built")) and r20_ready,
        "r54_16_purge_disposal_receipt_built": _r54_bool(r20.get("r54_16_purge_disposal_receipt_built")) and r20_ready,
        "r54_17_body_free_post_review_summary_built": _r54_bool(r20.get("r54_17_body_free_post_review_summary_built")) and r20_ready,
        "r54_18_p5_decision_candidate_separation_built": _r54_bool(r20.get("r54_18_p5_decision_candidate_separation_built")) and r20_ready,
        "r54_19_p6_limited_human_readfeel_candidate_handoff_built": _r54_bool(r20.get("r54_19_p6_limited_human_readfeel_candidate_handoff_built")) and r20_ready,
        "r54_20_p8_question_design_material_candidate_handoff_built": _r54_bool(r20.get("r54_20_p8_question_design_material_candidate_handoff_built")) and r20_ready,
        "r54_21_final_no_body_leak_no_question_text_no_touch_validation_built": built,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "implemented_steps": list(P7_R54_R21_IMPLEMENTED_STEPS if built else P7_R54_R20_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_R21_NOT_YET_IMPLEMENTED_STEPS if built else P7_R54_R20_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R54_R21_NEXT_REQUIRED_STEP_REF if built else P7_R54_R21_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "next_required_step": P7_R54_R21_NEXT_REQUIRED_STEP_REF if built else P7_R54_R21_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags_except(allowed_truthy),
        "validation_evidence_intake_done_here": _r54_bool(r20.get("validation_evidence_intake_done_here")) and r20_ready,
        "local_root_preflight_passed_here": _r54_bool(r20.get("local_root_preflight_passed_here")) and r20_ready,
        "explicit_allow_present_here": _r54_bool(r20.get("explicit_allow_present_here")) and r20_ready,
        "purge_plan_verified_here": _r54_bool(r20.get("purge_plan_verified_here")) and r20_ready,
    }
    assert_p7_r54_final_no_body_leak_no_question_text_no_touch_validation_bodyfree_contract(material)
    return material


def assert_p7_r54_final_no_body_leak_no_question_text_no_touch_validation_bodyfree_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_REQUIRED_FIELD_REFS, source="p7_r54_final_no_body_leak_no_question_text_no_touch_validation")
    _assert_body_free_common_with_false_keys(data, schema_version=P7_R54_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION, source="p7_r54_final_no_body_leak_no_question_text_no_touch_validation", false_key_refs=P7_R54_R21_FALSE_KEY_REFS)
    _assert_current_refs(data, source="p7_r54_final_no_body_leak_no_question_text_no_touch_validation")
    if data.get("policy_section") != P7_R54_R21_STEP_REF:
        raise ValueError("R54 R21 policy section changed")
    if data.get("final_validation_status") not in P7_R54_FINAL_VALIDATION_STATUS_REFS:
        raise ValueError("R54 R21 final validation status changed")
    for false_key in (*P7_R54_R21_BODY_LEAK_FALSE_KEY_REFS, *P7_R54_R21_NO_TOUCH_REQUIRED_FALSE_KEY_REFS, "p8_start_allowed", "p7_complete", "release_allowed", "hold004_close_allowed", "p5_human_blind_qa_confirmed_final", "p5_decision_finalized_here", "p6_limited_human_readfeel_start_allowed", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_disposal_run_here", "actual_reviewer_notes_materialized_here", "body_full_packet_generated_here", "actual_body_full_packet_generated_here"):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 R21 must keep {false_key}=False")
    if data.get("final_validation_status") == "FINAL_BODY_FREE_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_READY":
        if data.get("body_leak_detected") is not False or data.get("question_text_detected") is not False or data.get("no_touch_violation_detected") is not False:
            raise ValueError("R54 R21 ready validation must not have leak/question/no-touch violations")
        if data.get("no_touch_touched_refs") not in ([], ()):  # type: ignore[comparison-overlap]
            raise ValueError("R54 R21 ready no-touch touched refs must be empty")
        if data.get("final_validation_passed") is not True or data.get("ready_for_r52_reintake_handoff") is not True or data.get("final_no_body_leak_no_question_text_no_touch_validation_materialized_here") is not True or data.get("r54_21_final_no_body_leak_no_question_text_no_touch_validation_built") is not True:
            raise ValueError("R54 R21 ready validation must materialize")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_R21_IMPLEMENTED_STEPS:
            raise ValueError("R54 R21 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_R21_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 R21 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_R21_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R21 next step changed")
    else:
        if data.get("final_validation_passed") is not False or data.get("ready_for_r52_reintake_handoff") is not False or data.get("final_no_body_leak_no_question_text_no_touch_validation_materialized_here") is not False:
            raise ValueError("R54 R21 blocked validation must not materialize")
        if data.get("final_validation_status") == "FINAL_VALIDATION_BLOCKED_BY_BODY_LEAK" and data.get("body_leak_detected") is not True:
            raise ValueError("R54 R21 body-leak blocked status must carry detected=true")
        if data.get("final_validation_status") == "FINAL_VALIDATION_BLOCKED_BY_QUESTION_TEXT" and data.get("question_text_detected") is not True:
            raise ValueError("R54 R21 question-text blocked status must carry detected=true")
        if data.get("final_validation_status") == "FINAL_VALIDATION_BLOCKED_BY_NO_TOUCH_VIOLATION":
            if data.get("no_touch_violation_detected") is not True or not tuple(data.get("no_touch_touched_refs") or ()):  # type: ignore[arg-type]
                raise ValueError("R54 R21 no-touch blocked status must carry touched refs")
        if data.get("next_required_step") != P7_R54_R21_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R21 blocked next step changed")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_final_no_body_leak_no_question_text_no_touch_validation")
    return True

# Compatibility aliases matching the shorter R54-18 through R54-21 design wording.
build_p7_r54_p5_decision_candidate_separation = build_p7_r54_p5_decision_candidate_separation_bodyfree
assert_p7_r54_p5_decision_candidate_separation_contract = assert_p7_r54_p5_decision_candidate_separation_bodyfree_contract
build_p7_r54_p6_limited_human_readfeel_candidate_handoff = build_p7_r54_p6_limited_human_readfeel_candidate_handoff_bodyfree
assert_p7_r54_p6_limited_human_readfeel_candidate_handoff_contract = assert_p7_r54_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract
build_p7_r54_p8_question_design_material_candidate_handoff = build_p7_r54_p8_question_design_material_candidate_handoff_bodyfree
assert_p7_r54_p8_question_design_material_candidate_handoff_contract = assert_p7_r54_p8_question_design_material_candidate_handoff_bodyfree_contract
build_p7_r54_final_no_body_leak_no_question_text_no_touch_validation = build_p7_r54_final_no_body_leak_no_question_text_no_touch_validation_bodyfree
assert_p7_r54_final_no_body_leak_no_question_text_no_touch_validation_contract = assert_p7_r54_final_no_body_leak_no_question_text_no_touch_validation_bodyfree_contract



# ---------------------------------------------------------------------------
# R54-22 / R54-23 R52 re-intake handoff and validation documentation output
# ---------------------------------------------------------------------------

P7_R54_R52_REINTAKE_HANDOFF_SCHEMA_VERSION: Final = "cocolon.emlis.p7_r54.r52_reintake_handoff.bodyfree.v1"
P7_R54_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION: Final = "cocolon.emlis.p7_r54.validation_command_matrix_documentation_output.bodyfree.v1"
P7_R54_R22_STEP_REF: Final = "R54-22_r52_reintake_handoff"
P7_R54_R23_STEP_REF: Final = "R54-23_validation_command_matrix_documentation_output"
P7_R54_R22_NEXT_REQUIRED_STEP_REF: Final = P7_R54_R23_STEP_REF
P7_R54_R22_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R54-22_r52_reintake_handoff_before_R54-23_validation_documentation_output"
P7_R54_R23_NEXT_REQUIRED_STEP_REF: Final = "R54_IMPLEMENTATION_COMPLETE_AWAITING_R52_REINTAKE_DECISION_GATE_AND_ACTUAL_OPERATION_EVIDENCE"
P7_R54_R23_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R54-22_r52_reintake_handoff_before_R54-23_validation_documentation_output"
P7_R54_FUTURE_STEPS_AFTER_R23: Final[tuple[str, ...]] = tuple(step for step in P7_R54_FUTURE_STEPS_AFTER_R21 if step not in {P7_R54_R22_STEP_REF, P7_R54_R23_STEP_REF})
P7_R54_R22_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_R21_IMPLEMENTED_STEPS, P7_R54_R22_STEP_REF)
P7_R54_R22_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_R23_STEP_REF, *P7_R54_FUTURE_STEPS_AFTER_R23)
P7_R54_R23_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_R22_IMPLEMENTED_STEPS, P7_R54_R23_STEP_REF)
P7_R54_R23_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_FUTURE_STEPS_AFTER_R23

P7_R54_R52_REINTAKE_HANDOFF_STATUS_REFS: Final[tuple[str, ...]] = (
    "R54_R52_REINTAKE_HANDOFF_READY",
    "R54_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING",
    "R54_R52_REINTAKE_BLOCKED_BY_DISPOSAL_SAFETY",
    "R54_R52_REINTAKE_BLOCKED_BY_BODY_LEAK_OR_QUESTION_TEXT",
    "R54_R52_REINTAKE_BLOCKED_BY_NO_TOUCH_VIOLATION",
    "R54_R52_REINTAKE_BLOCKED_BY_INCONCLUSIVE",
)
P7_R54_VALIDATION_DOCUMENTATION_STATUS_REFS: Final[tuple[str, ...]] = (
    "VALIDATION_COMMAND_MATRIX_DOCUMENTATION_READY",
    "VALIDATION_DOCUMENTATION_BLOCKED_BY_R54_22_R52_REINTAKE_HANDOFF",
)
P7_R54_R23_R54_TARGET_TEST_REFS: Final[tuple[str, ...]] = (
    "py_compile_r54_result_handoff_helper",
    "pytest_r54_r0_r1_target",
    "pytest_r54_r2_r3_target",
    "pytest_r54_r4_r5_target",
    "pytest_r54_r6_r7_target",
    "pytest_r54_r8_r9_target",
    "pytest_r54_r10_r11_target",
    "pytest_r54_r12_r13_target",
    "pytest_r54_r14_r15_target",
    "pytest_r54_r16_r17_target",
    "pytest_r54_r18_r19_target",
    "pytest_r54_r20_r21_target",
    "pytest_r54_r22_r23_target",
)
P7_R54_R23_REGRESSION_COMMAND_REFS: Final[tuple[str, ...]] = (
    "pytest_r53_split_regression",
    "pytest_r52_target_regression",
    "pytest_r51_target_regression",
    "pytest_r50_target_regression",
    "pytest_r49_individual_split_regression",
)
P7_R54_R23_REQUIRED_COMMAND_GROUP_REFS: Final[tuple[str, ...]] = (
    "r54_target_split", "r53_split_regression", "r52_r51_r50_r49_regression", "rn_contract_no_touch", "backend_collect_only",
)

P7_R54_R52_REINTAKE_HANDOFF_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "r21_final_validation_schema_version", "r21_final_validation_material_ref", "r21_final_validation_status", "r21_ready_for_r52_reintake_handoff",
    "current_received_snapshot_refs", "current_received_snapshot_ref_count", "r53_source_snapshot_refs", "r53_source_snapshot_ref_count", "r53_refs_are_current_received_refs",
    "review_session_status", "r52_reintake_handoff_status", "r52_reintake_handoff_reason_refs", "r52_reintake_handoff_materialized_here", "r52_reintake_ready", "r52_reintake_material_refs", "r52_decision_gate_input_refs",
    "actual_review_evidence_complete", "disposal_safety_complete", "rating_question_consistency_complete", "p5_decision_recheck_available", "no_body_leak_validation_complete", "no_question_text_validation_complete", "no_touch_validation_complete",
    "body_leak_detected", "question_text_detected", "no_touch_violation_detected", "no_touch_touched_refs",
    "p5_human_blind_qa_confirmed_candidate", "p5_human_blind_qa_confirmed_final", "p5_repair_return_candidate", "p5_review_inconclusive", "p5_decision_candidate_ref", "p5_decision_finalized_here",
    "p6_limited_human_readfeel_candidate", "p6_limited_human_readfeel_start_allowed", "p6_start_allowed_true_passed_to_r52", "p8_question_design_material_candidate", "p8_start_allowed", "p8_start_allowed_true_passed_to_r52", "p7_complete", "release_allowed", "hold004_close_allowed",
    "body_full_packet_generated_here", "actual_body_full_packet_generated_here", "actual_review_run_here", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_reviewer_notes_materialized_here", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_question_need_observation_summary_materialized_here", "actual_disposal_run_here", "disposal_receipt_materialized_here", "actual_disposal_receipt_materialized_here", "post_review_summary_materialized_here", "p5_actual_review_still_not_run_by_helper",
    "raw_input_included", "returned_surface_included", "comment_text_included", "history_body_included", "reviewer_free_text_included", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included", "terminal_output_included", "local_packet_exported", "content_hash_of_body_stored",
    "api_route_changed_here", "db_schema_changed_here", "db_migration_changed_here", "rn_visible_contract_changed_here", "public_response_top_level_key_added_here", "public_response_key_changed_here", "api_db_rn_response_key_changed_here", "runtime_changed_here", "question_api_implemented", "question_db_schema_implemented", "question_rn_ui_implemented", "question_response_key_implemented", "question_trigger_logic_implemented", "question_storage_schema_implemented", "question_answer_persistence_implemented", "question_plan_guard_implemented", "question_implementation_started_here", "p8_question_implementation_spec_finalized_here", "p8_question_api_designed_here", "p8_question_db_schema_designed_here", "p8_question_rn_ui_designed_here", "p8_question_trigger_logic_designed_here", "p8_question_response_key_designed_here", "p8_question_plan_guard_designed_here",
    "r54_0_scope_current_received_snapshot_refrozen", "r54_1_r53_source_delta_current_snapshot_override_adopted", "r54_2_validation_evidence_intake_done", "r54_3_local_only_actual_review_preflight_built", "r54_4_actual_review_session_envelope_built", "r54_5_24_case_manifest_freeze_built", "r54_6_local_only_body_full_packet_generation_request_built", "r54_7_packet_completeness_export_denylist_scan_built", "r54_8_reviewer_instruction_rating_form_freeze_built", "r54_9_actual_human_review_operation_state_capture_built", "r54_10_sanitized_actual_review_result_capture_built", "r54_11_rating_row_normalization_built", "r54_12_readfeel_blocker_execution_blocker_ingestion_built", "r54_13_question_need_observation_row_normalization_built", "r54_14_rating_question_observation_consistency_guard_built", "r54_15_pause_abort_expiration_protocol_built", "r54_16_purge_disposal_receipt_built", "r54_17_body_free_post_review_summary_built", "r54_18_p5_decision_candidate_separation_built", "r54_19_p6_limited_human_readfeel_candidate_handoff_built", "r54_20_p8_question_design_material_candidate_handoff_built", "r54_21_final_no_body_leak_no_question_text_no_touch_validation_built", "r54_22_r52_reintake_handoff_built",
    "execution_blocker_ids", "open_execution_blocker_ids", "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract", "r54_public_no_touch_contract", "body_free_markers", "body_free",
    "validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here",
)
P7_R54_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "r22_r52_reintake_handoff_schema_version", "r22_r52_reintake_handoff_material_ref", "r22_r52_reintake_handoff_status", "r22_ready_for_validation_command_matrix_documentation",
    "review_session_status", "validation_documentation_status", "validation_command_matrix_materialized_here", "documentation_output_materialized_here", "command_matrix_body_free", "command_matrix_contains_local_absolute_path", "command_matrix_claims_full_backend_green", "validation_commands_ran_here", "actual_validation_execution_completed_here",
    "command_matrix_rows", "command_matrix_row_count", "command_groups_present", "required_command_groups_present", "r54_target_test_refs", "r54_target_test_ref_count", "regression_command_refs", "collect_only_command_ref", "backend_collect_only_is_full_suite_green", "rn_no_touch_confirmation_command_ref", "rn_no_touch_is_real_device_readfeel", "r54_target_tests_present", "r53_regression_split_present", "r52_r51_r50_r49_regression_present", "rn_contract_no_touch_present", "backend_collect_only_present",
    "p5_human_blind_qa_confirmed_candidate", "p5_human_blind_qa_confirmed_final", "p5_repair_return_candidate", "p5_review_inconclusive", "p5_decision_candidate_ref", "p5_decision_finalized_here", "p6_limited_human_readfeel_candidate", "p6_limited_human_readfeel_start_allowed", "p8_question_design_material_candidate", "p8_start_allowed", "p7_complete", "release_allowed", "hold004_close_allowed",
    "body_full_packet_generated_here", "actual_body_full_packet_generated_here", "actual_review_run_here", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_reviewer_notes_materialized_here", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_question_need_observation_summary_materialized_here", "actual_disposal_run_here", "disposal_receipt_materialized_here", "actual_disposal_receipt_materialized_here", "post_review_summary_materialized_here", "p5_actual_review_still_not_run_by_helper",
    "raw_input_included", "returned_surface_included", "comment_text_included", "history_body_included", "reviewer_free_text_included", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included", "terminal_output_included", "local_packet_exported", "content_hash_of_body_stored",
    "api_route_changed_here", "db_schema_changed_here", "db_migration_changed_here", "rn_visible_contract_changed_here", "public_response_top_level_key_added_here", "public_response_key_changed_here", "api_db_rn_response_key_changed_here", "runtime_changed_here", "question_api_implemented", "question_db_schema_implemented", "question_rn_ui_implemented", "question_response_key_implemented", "question_trigger_logic_implemented", "question_storage_schema_implemented", "question_answer_persistence_implemented", "question_plan_guard_implemented", "question_implementation_started_here", "p8_question_implementation_spec_finalized_here", "p8_question_api_designed_here", "p8_question_db_schema_designed_here", "p8_question_rn_ui_designed_here", "p8_question_trigger_logic_designed_here", "p8_question_response_key_designed_here", "p8_question_plan_guard_designed_here",
    "full_backend_suite_green_confirmed", "backend_collect_only_claimed_as_full_backend_green", "rn_contract_claimed_as_real_device_modal_readfeel",
    "r54_22_r52_reintake_handoff_built", "r54_23_validation_command_matrix_documentation_output_built", "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract", "r54_public_no_touch_contract", "body_free_markers", "body_free",
    "validation_evidence_intake_done_here", "local_root_preflight_passed_here", "explicit_allow_present_here", "purge_plan_verified_here",
)


def _r54_r22_status_from_r21(r21: Mapping[str, Any]) -> tuple[str, list[str]]:
    r21_ready = r21.get("final_validation_status") == "FINAL_BODY_FREE_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_READY" and r21.get("final_validation_passed") is True and r21.get("ready_for_r52_reintake_handoff") is True
    if not r21_ready:
        status = clean_identifier(r21.get("final_validation_status"), default="", max_length=180)
        if status in {"FINAL_VALIDATION_BLOCKED_BY_BODY_LEAK", "FINAL_VALIDATION_BLOCKED_BY_QUESTION_TEXT"}:
            return "R54_R52_REINTAKE_BLOCKED_BY_BODY_LEAK_OR_QUESTION_TEXT", ["r54_21_body_or_question_validation_blocked"]
        if status == "FINAL_VALIDATION_BLOCKED_BY_NO_TOUCH_VIOLATION":
            return "R54_R52_REINTAKE_BLOCKED_BY_NO_TOUCH_VIOLATION", ["r54_21_no_touch_validation_blocked"]
        return "R54_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING", ["r54_21_final_validation_not_ready"]
    actual_complete = all(r21.get(key) is True for key in ("actual_review_run_here", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_execution_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_question_need_observation_summary_materialized_here", "post_review_summary_materialized_here"))
    if not actual_complete:
        return "R54_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING", ["actual_review_evidence_incomplete_for_r52"]
    disposal_safe = r21.get("disposal_receipt_materialized_here") is True and r21.get("actual_disposal_receipt_materialized_here") is True and r21.get("local_packet_exported") is False
    if not disposal_safe:
        return "R54_R52_REINTAKE_BLOCKED_BY_DISPOSAL_SAFETY", ["disposal_safety_incomplete_for_r52"]
    if r21.get("p5_review_inconclusive") is True or str(r21.get("p5_decision_candidate_ref") or "").startswith("P5_INCONCLUSIVE"):
        return "R54_R52_REINTAKE_BLOCKED_BY_INCONCLUSIVE", ["p5_decision_candidate_inconclusive_before_r52_reintake"]
    return "R54_R52_REINTAKE_HANDOFF_READY", ["r54_r52_reintake_handoff_ready_bodyfree"]


def _r54_r23_command_matrix_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for command_ref in P7_R54_R23_R54_TARGET_TEST_REFS:
        rows.append({"command_group_ref": "r54_target_split", "command_ref": command_ref, "claim_level": "target_or_syntax_check", "full_backend_suite_green_claimed": False, "collect_only": False, "rn_no_touch_confirmation": False, "validation_executed_here": False, "local_absolute_path_included": False, "terminal_output_included": False, "body_free": True})
    for command_ref in P7_R54_R23_REGRESSION_COMMAND_REFS:
        rows.append({"command_group_ref": "r53_split_regression" if command_ref == "pytest_r53_split_regression" else "r52_r51_r50_r49_regression", "command_ref": command_ref, "claim_level": "regression_split_or_target", "full_backend_suite_green_claimed": False, "collect_only": False, "rn_no_touch_confirmation": False, "validation_executed_here": False, "local_absolute_path_included": False, "terminal_output_included": False, "body_free": True})
    rows.append({"command_group_ref": "backend_collect_only", "command_ref": "pytest_backend_collect_only_not_full_backend_green", "claim_level": "collect_only_not_full_backend_green", "full_backend_suite_green_claimed": False, "collect_only": True, "rn_no_touch_confirmation": False, "validation_executed_here": False, "local_absolute_path_included": False, "terminal_output_included": False, "body_free": True})
    rows.append({"command_group_ref": "rn_contract_no_touch", "command_ref": "npm_run_test_rn_screens_silent_no_touch_confirmation", "claim_level": "rn_contract_no_touch_not_real_device_readfeel", "full_backend_suite_green_claimed": False, "collect_only": False, "rn_no_touch_confirmation": True, "validation_executed_here": False, "local_absolute_path_included": False, "terminal_output_included": False, "body_free": True})
    return rows


def _r54_late_false_flags() -> dict[str, bool]:
    return {key: False for key in ("p5_human_blind_qa_confirmed_final", "p5_decision_finalized_here", "p6_limited_human_readfeel_start_allowed", "p8_start_allowed", "p7_complete", "release_allowed", "hold004_close_allowed", "body_full_packet_generated_here", "actual_body_full_packet_generated_here", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_disposal_run_here", "actual_reviewer_notes_materialized_here", "raw_input_included", "returned_surface_included", "comment_text_included", "history_body_included", "reviewer_free_text_included", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included", "terminal_output_included", "local_packet_exported", "content_hash_of_body_stored", "api_route_changed_here", "db_schema_changed_here", "db_migration_changed_here", "rn_visible_contract_changed_here", "public_response_top_level_key_added_here", "public_response_key_changed_here", "api_db_rn_response_key_changed_here", "runtime_changed_here", "question_api_implemented", "question_db_schema_implemented", "question_rn_ui_implemented", "question_response_key_implemented", "question_trigger_logic_implemented", "question_storage_schema_implemented", "question_answer_persistence_implemented", "question_plan_guard_implemented", "question_implementation_started_here", "p8_question_implementation_spec_finalized_here", "p8_question_api_designed_here", "p8_question_db_schema_designed_here", "p8_question_rn_ui_designed_here", "p8_question_trigger_logic_designed_here", "p8_question_response_key_designed_here", "p8_question_plan_guard_designed_here")}


def build_p7_r54_r52_reintake_handoff_bodyfree(*, final_no_body_leak_no_question_text_no_touch_validation: Mapping[str, Any] | None = None, material_id: str = "p7_r54_r52_reintake_handoff_bodyfree") -> dict[str, Any]:
    r21 = safe_mapping(final_no_body_leak_no_question_text_no_touch_validation)
    status, reason_refs = _r54_r22_status_from_r21(r21)
    built = status == "R54_R52_REINTAKE_HANDOFF_READY"
    material = {
        "schema_version": P7_R54_R52_REINTAKE_HANDOFF_SCHEMA_VERSION, "phase": P7_PHASE, "step": P7_R54_STEP, "scope": P7_R54_SCOPE, "policy_kind": P7_R54_POLICY_KIND, "policy_section": P7_R54_R22_STEP_REF, "current_phase": "P7", "material_id": clean_identifier(material_id, default="p7_r54_r52_reintake_handoff_bodyfree", max_length=180), "review_session_id": _safe_review_session_id(r21.get("review_session_id")), "source_mode": P7_SOURCE_MODE, "git_connection_required": False, "git_checked": False,
        "r21_final_validation_schema_version": clean_identifier(r21.get("schema_version"), default=P7_R54_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION, max_length=180), "r21_final_validation_material_ref": clean_identifier(r21.get("material_id"), default="p7_r54_final_no_body_leak_no_question_text_no_touch_validation_bodyfree", max_length=180), "r21_final_validation_status": clean_identifier(r21.get("final_validation_status"), default="FINAL_VALIDATION_BLOCKED_BY_R54_20_P8_MATERIAL_HANDOFF", max_length=180), "r21_ready_for_r52_reintake_handoff": _r54_bool(r21.get("ready_for_r52_reintake_handoff")),
        "current_received_snapshot_refs": dict(P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS), "current_received_snapshot_ref_count": len(P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS), "r53_source_snapshot_refs": _r53_source_snapshot_refs(None), "r53_source_snapshot_ref_count": len(_r53_source_snapshot_refs(None)), "r53_refs_are_current_received_refs": False,
        "review_session_status": "R54_R52_REINTAKE_HANDOFF_READY" if built else "R54_R52_REINTAKE_HANDOFF_BLOCKED", "r52_reintake_handoff_status": status, "r52_reintake_handoff_reason_refs": reason_refs, "r52_reintake_handoff_materialized_here": built, "r52_reintake_ready": built, "r52_reintake_material_refs": ["r54_21_final_validation_ref", "r54_17_post_review_summary_ref", "r54_18_p5_decision_candidate_ref", "r54_20_p8_material_candidate_ref"] if built else ["r54_21_final_validation_ref"], "r52_decision_gate_input_refs": ["actual_review_evidence_completeness", "disposal_safety", "p5_decision_candidate", "p6_candidate_only_start_false", "p8_material_candidate_only_start_false"],
        "actual_review_evidence_complete": built, "disposal_safety_complete": built, "rating_question_consistency_complete": built, "p5_decision_recheck_available": built, "no_body_leak_validation_complete": r21.get("body_leak_detected") is False, "no_question_text_validation_complete": r21.get("question_text_detected") is False, "no_touch_validation_complete": r21.get("no_touch_violation_detected") is False, "body_leak_detected": _r54_bool(r21.get("body_leak_detected")), "question_text_detected": _r54_bool(r21.get("question_text_detected")), "no_touch_violation_detected": _r54_bool(r21.get("no_touch_violation_detected")), "no_touch_touched_refs": list(_safe_sequence_r54(r21.get("no_touch_touched_refs"))),
        "p5_human_blind_qa_confirmed_candidate": _r54_bool(r21.get("p5_human_blind_qa_confirmed_candidate")) and built, "p5_repair_return_candidate": _r54_bool(r21.get("p5_repair_return_candidate")) and built, "p5_review_inconclusive": _r54_bool(r21.get("p5_review_inconclusive")), "p5_decision_candidate_ref": clean_identifier(r21.get("p5_decision_candidate_ref"), default="P5_NOT_REVIEWED", max_length=180), "p6_limited_human_readfeel_candidate": _r54_bool(r21.get("p6_limited_human_readfeel_candidate")) and built, "p6_start_allowed_true_passed_to_r52": False, "p8_question_design_material_candidate": _r54_bool(r21.get("p8_question_design_material_candidate")) and built, "p8_start_allowed_true_passed_to_r52": False,
        "actual_review_run_here": _r54_bool(r21.get("actual_review_run_here")) and built, "actual_rating_rows_materialized_here": _r54_bool(r21.get("actual_rating_rows_materialized_here")) and built, "actual_blocker_rows_materialized_here": _r54_bool(r21.get("actual_blocker_rows_materialized_here")) and built, "actual_execution_blocker_rows_materialized_here": _r54_bool(r21.get("actual_execution_blocker_rows_materialized_here")) and built, "actual_question_need_observation_rows_materialized_here": _r54_bool(r21.get("actual_question_need_observation_rows_materialized_here")) and built, "actual_question_need_observation_summary_materialized_here": _r54_bool(r21.get("actual_question_need_observation_summary_materialized_here")) and built, "disposal_receipt_materialized_here": _r54_bool(r21.get("disposal_receipt_materialized_here")) and built, "actual_disposal_receipt_materialized_here": _r54_bool(r21.get("actual_disposal_receipt_materialized_here")) and built, "post_review_summary_materialized_here": _r54_bool(r21.get("post_review_summary_materialized_here")) and built, "p5_actual_review_still_not_run_by_helper": True,
        "r54_0_scope_current_received_snapshot_refrozen": True, "r54_1_r53_source_delta_current_snapshot_override_adopted": True,
        "r54_2_validation_evidence_intake_done": _r54_bool(r21.get("r54_2_validation_evidence_intake_done")) and bool(r21), "r54_3_local_only_actual_review_preflight_built": _r54_bool(r21.get("r54_3_local_only_actual_review_preflight_built")) and bool(r21), "r54_4_actual_review_session_envelope_built": _r54_bool(r21.get("r54_4_actual_review_session_envelope_built")) and bool(r21), "r54_5_24_case_manifest_freeze_built": _r54_bool(r21.get("r54_5_24_case_manifest_freeze_built")) and bool(r21), "r54_6_local_only_body_full_packet_generation_request_built": _r54_bool(r21.get("r54_6_local_only_body_full_packet_generation_request_built")) and bool(r21), "r54_7_packet_completeness_export_denylist_scan_built": _r54_bool(r21.get("r54_7_packet_completeness_export_denylist_scan_built")) and bool(r21), "r54_8_reviewer_instruction_rating_form_freeze_built": _r54_bool(r21.get("r54_8_reviewer_instruction_rating_form_freeze_built")) and bool(r21), "r54_9_actual_human_review_operation_state_capture_built": _r54_bool(r21.get("r54_9_actual_human_review_operation_state_capture_built")) and bool(r21), "r54_10_sanitized_actual_review_result_capture_built": _r54_bool(r21.get("r54_10_sanitized_actual_review_result_capture_built")) and bool(r21), "r54_11_rating_row_normalization_built": _r54_bool(r21.get("r54_11_rating_row_normalization_built")) and bool(r21), "r54_12_readfeel_blocker_execution_blocker_ingestion_built": _r54_bool(r21.get("r54_12_readfeel_blocker_execution_blocker_ingestion_built")) and bool(r21), "r54_13_question_need_observation_row_normalization_built": _r54_bool(r21.get("r54_13_question_need_observation_row_normalization_built")) and bool(r21), "r54_14_rating_question_observation_consistency_guard_built": _r54_bool(r21.get("r54_14_rating_question_observation_consistency_guard_built")) and bool(r21), "r54_15_pause_abort_expiration_protocol_built": _r54_bool(r21.get("r54_15_pause_abort_expiration_protocol_built")) and bool(r21), "r54_16_purge_disposal_receipt_built": _r54_bool(r21.get("r54_16_purge_disposal_receipt_built")) and bool(r21), "r54_17_body_free_post_review_summary_built": _r54_bool(r21.get("r54_17_body_free_post_review_summary_built")) and bool(r21), "r54_18_p5_decision_candidate_separation_built": _r54_bool(r21.get("r54_18_p5_decision_candidate_separation_built")) and bool(r21), "r54_19_p6_limited_human_readfeel_candidate_handoff_built": _r54_bool(r21.get("r54_19_p6_limited_human_readfeel_candidate_handoff_built")) and bool(r21), "r54_20_p8_question_design_material_candidate_handoff_built": _r54_bool(r21.get("r54_20_p8_question_design_material_candidate_handoff_built")) and bool(r21), "r54_21_final_no_body_leak_no_question_text_no_touch_validation_built": _r54_bool(r21.get("r54_21_final_no_body_leak_no_question_text_no_touch_validation_built")) and bool(r21), "r54_22_r52_reintake_handoff_built": built,
        "execution_blocker_ids": [] if built else reason_refs, "open_execution_blocker_ids": [] if built else reason_refs, "implemented_steps": list(P7_R54_R22_IMPLEMENTED_STEPS if built else P7_R54_R21_IMPLEMENTED_STEPS), "not_yet_implemented_steps": list(P7_R54_R22_NOT_YET_IMPLEMENTED_STEPS if built else P7_R54_R21_NOT_YET_IMPLEMENTED_STEPS), "first_next_work_ref": P7_R54_R22_NEXT_REQUIRED_STEP_REF if built else P7_R54_R22_BLOCKED_NEXT_REQUIRED_STEP_REF, "next_required_step": P7_R54_R22_NEXT_REQUIRED_STEP_REF if built else P7_R54_R22_BLOCKED_NEXT_REQUIRED_STEP_REF, "public_contract": public_contract_flags(), "r54_public_no_touch_contract": _public_no_touch_contract(), "body_free_markers": _body_free_markers(), "body_free": True,
        "validation_evidence_intake_done_here": _r54_bool(r21.get("validation_evidence_intake_done_here")) and bool(r21), "local_root_preflight_passed_here": _r54_bool(r21.get("local_root_preflight_passed_here")) and bool(r21), "explicit_allow_present_here": _r54_bool(r21.get("explicit_allow_present_here")) and bool(r21), "purge_plan_verified_here": _r54_bool(r21.get("purge_plan_verified_here")) and bool(r21),
        **_r54_late_false_flags(),
    }
    # Restore intentionally propagated values after setting shared false flags.
    material["p5_human_blind_qa_confirmed_candidate"] = _r54_bool(r21.get("p5_human_blind_qa_confirmed_candidate")) and built
    material["p5_repair_return_candidate"] = _r54_bool(r21.get("p5_repair_return_candidate")) and built
    material["p5_review_inconclusive"] = _r54_bool(r21.get("p5_review_inconclusive"))
    material["p6_limited_human_readfeel_candidate"] = _r54_bool(r21.get("p6_limited_human_readfeel_candidate")) and built
    material["p8_question_design_material_candidate"] = _r54_bool(r21.get("p8_question_design_material_candidate")) and built
    assert_p7_r54_r52_reintake_handoff_bodyfree_contract(material)
    return material


def assert_p7_r54_r52_reintake_handoff_bodyfree_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_R52_REINTAKE_HANDOFF_REQUIRED_FIELD_REFS, source="p7_r54_r52_reintake_handoff")
    _assert_body_free_common_with_false_keys(data, schema_version=P7_R54_R52_REINTAKE_HANDOFF_SCHEMA_VERSION, source="p7_r54_r52_reintake_handoff", false_key_refs=())
    _assert_current_refs(data, source="p7_r54_r52_reintake_handoff")
    if data.get("policy_section") != P7_R54_R22_STEP_REF or data.get("r52_reintake_handoff_status") not in P7_R54_R52_REINTAKE_HANDOFF_STATUS_REFS:
        raise ValueError("R54 R22 handoff contract changed")
    for false_key in ("p6_limited_human_readfeel_start_allowed", "p6_start_allowed_true_passed_to_r52", "p8_start_allowed", "p8_start_allowed_true_passed_to_r52", "p7_complete", "release_allowed", "hold004_close_allowed", "p5_human_blind_qa_confirmed_final", "p5_decision_finalized_here", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_disposal_run_here", "actual_reviewer_notes_materialized_here", "body_full_packet_generated_here", "actual_body_full_packet_generated_here", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "body_content_hash_included", "packet_content_hash_included", "terminal_output_included", "runtime_changed_here", "api_route_changed_here", "db_schema_changed_here", "db_migration_changed_here", "rn_visible_contract_changed_here", "public_response_key_changed_here", "api_db_rn_response_key_changed_here", "question_api_implemented", "question_db_schema_implemented", "question_rn_ui_implemented", "question_response_key_implemented", "question_trigger_logic_implemented", "question_storage_schema_implemented", "question_answer_persistence_implemented", "question_plan_guard_implemented", "question_implementation_started_here", "p8_question_api_designed_here", "p8_question_db_schema_designed_here", "p8_question_rn_ui_designed_here", "p8_question_trigger_logic_designed_here", "p8_question_response_key_designed_here", "p8_question_plan_guard_designed_here"):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 R22 must keep {false_key}=False")
    if data.get("r52_reintake_handoff_status") == "R54_R52_REINTAKE_HANDOFF_READY":
        if data.get("r52_reintake_ready") is not True or data.get("actual_review_evidence_complete") is not True or data.get("disposal_safety_complete") is not True or data.get("r54_22_r52_reintake_handoff_built") is not True:
            raise ValueError("R54 R22 ready handoff must be complete")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_R22_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_R22_NOT_YET_IMPLEMENTED_STEPS or data.get("next_required_step") != P7_R54_R22_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R22 ready step markers changed")
    else:
        if data.get("r52_reintake_ready") is not False or data.get("r52_reintake_handoff_materialized_here") is not False or data.get("r54_22_r52_reintake_handoff_built") is not False:
            raise ValueError("R54 R22 blocked handoff must not materialize")
        if data.get("next_required_step") != P7_R54_R22_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R22 blocked next step changed")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_r52_reintake_handoff")
    return True


def build_p7_r54_validation_command_matrix_documentation_output_bodyfree(*, r52_reintake_handoff: Mapping[str, Any] | None = None, material_id: str = "p7_r54_validation_command_matrix_documentation_output_bodyfree") -> dict[str, Any]:
    r22 = safe_mapping(r52_reintake_handoff)
    built = r22.get("r52_reintake_handoff_status") == "R54_R52_REINTAKE_HANDOFF_READY" and r22.get("r52_reintake_ready") is True and r22.get("r54_22_r52_reintake_handoff_built") is True
    rows = _r54_r23_command_matrix_rows() if built else []
    groups = sorted({str(row.get("command_group_ref")) for row in rows})
    material = {
        "schema_version": P7_R54_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION, "phase": P7_PHASE, "step": P7_R54_STEP, "scope": P7_R54_SCOPE, "policy_kind": P7_R54_POLICY_KIND, "policy_section": P7_R54_R23_STEP_REF, "current_phase": "P7", "material_id": clean_identifier(material_id, default="p7_r54_validation_command_matrix_documentation_output_bodyfree", max_length=180), "review_session_id": _safe_review_session_id(r22.get("review_session_id")), "source_mode": P7_SOURCE_MODE, "git_connection_required": False, "git_checked": False,
        "r22_r52_reintake_handoff_schema_version": clean_identifier(r22.get("schema_version"), default=P7_R54_R52_REINTAKE_HANDOFF_SCHEMA_VERSION, max_length=180), "r22_r52_reintake_handoff_material_ref": clean_identifier(r22.get("material_id"), default="p7_r54_r52_reintake_handoff_bodyfree", max_length=180), "r22_r52_reintake_handoff_status": clean_identifier(r22.get("r52_reintake_handoff_status"), default="R54_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING", max_length=180), "r22_ready_for_validation_command_matrix_documentation": built,
        "review_session_status": "R54_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_READY" if built else "R54_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_BLOCKED", "validation_documentation_status": "VALIDATION_COMMAND_MATRIX_DOCUMENTATION_READY" if built else "VALIDATION_DOCUMENTATION_BLOCKED_BY_R54_22_R52_REINTAKE_HANDOFF", "validation_command_matrix_materialized_here": built, "documentation_output_materialized_here": built, "command_matrix_body_free": True, "command_matrix_contains_local_absolute_path": False, "command_matrix_claims_full_backend_green": False, "validation_commands_ran_here": False, "actual_validation_execution_completed_here": False,
        "command_matrix_rows": rows, "command_matrix_row_count": len(rows), "command_groups_present": groups, "required_command_groups_present": all(group in groups for group in P7_R54_R23_REQUIRED_COMMAND_GROUP_REFS) if built else False, "r54_target_test_refs": list(P7_R54_R23_R54_TARGET_TEST_REFS if built else ()), "r54_target_test_ref_count": len(P7_R54_R23_R54_TARGET_TEST_REFS) if built else 0, "regression_command_refs": list(P7_R54_R23_REGRESSION_COMMAND_REFS if built else ()), "collect_only_command_ref": "pytest_backend_collect_only_not_full_backend_green" if built else "", "backend_collect_only_is_full_suite_green": False, "rn_no_touch_confirmation_command_ref": "npm_run_test_rn_screens_silent_no_touch_confirmation" if built else "", "rn_no_touch_is_real_device_readfeel": False, "r54_target_tests_present": "r54_target_split" in groups, "r53_regression_split_present": "r53_split_regression" in groups, "r52_r51_r50_r49_regression_present": "r52_r51_r50_r49_regression" in groups, "rn_contract_no_touch_present": "rn_contract_no_touch" in groups, "backend_collect_only_present": "backend_collect_only" in groups,
        "p5_human_blind_qa_confirmed_candidate": _r54_bool(r22.get("p5_human_blind_qa_confirmed_candidate")) and built, "p5_repair_return_candidate": _r54_bool(r22.get("p5_repair_return_candidate")) and built, "p5_review_inconclusive": False, "p5_decision_candidate_ref": clean_identifier(r22.get("p5_decision_candidate_ref"), default="P5_NOT_REVIEWED", max_length=180), "p6_limited_human_readfeel_candidate": _r54_bool(r22.get("p6_limited_human_readfeel_candidate")) and built, "p8_question_design_material_candidate": _r54_bool(r22.get("p8_question_design_material_candidate")) and built,
        "actual_review_run_here": _r54_bool(r22.get("actual_review_run_here")) and built, "actual_rating_rows_materialized_here": _r54_bool(r22.get("actual_rating_rows_materialized_here")) and built, "actual_blocker_rows_materialized_here": _r54_bool(r22.get("actual_blocker_rows_materialized_here")) and built, "actual_execution_blocker_rows_materialized_here": _r54_bool(r22.get("actual_execution_blocker_rows_materialized_here")) and built, "actual_question_need_observation_rows_materialized_here": _r54_bool(r22.get("actual_question_need_observation_rows_materialized_here")) and built, "actual_question_need_observation_summary_materialized_here": _r54_bool(r22.get("actual_question_need_observation_summary_materialized_here")) and built, "disposal_receipt_materialized_here": _r54_bool(r22.get("disposal_receipt_materialized_here")) and built, "actual_disposal_receipt_materialized_here": _r54_bool(r22.get("actual_disposal_receipt_materialized_here")) and built, "post_review_summary_materialized_here": _r54_bool(r22.get("post_review_summary_materialized_here")) and built, "p5_actual_review_still_not_run_by_helper": True,
        "full_backend_suite_green_confirmed": False, "backend_collect_only_claimed_as_full_backend_green": False, "rn_contract_claimed_as_real_device_modal_readfeel": False, "r54_22_r52_reintake_handoff_built": _r54_bool(r22.get("r54_22_r52_reintake_handoff_built")) and bool(r22), "r54_23_validation_command_matrix_documentation_output_built": built, "implemented_steps": list(P7_R54_R23_IMPLEMENTED_STEPS if built else P7_R54_R22_IMPLEMENTED_STEPS), "not_yet_implemented_steps": list(P7_R54_R23_NOT_YET_IMPLEMENTED_STEPS if built else P7_R54_R22_NOT_YET_IMPLEMENTED_STEPS), "first_next_work_ref": P7_R54_R23_NEXT_REQUIRED_STEP_REF if built else P7_R54_R23_BLOCKED_NEXT_REQUIRED_STEP_REF, "next_required_step": P7_R54_R23_NEXT_REQUIRED_STEP_REF if built else P7_R54_R23_BLOCKED_NEXT_REQUIRED_STEP_REF, "public_contract": public_contract_flags(), "r54_public_no_touch_contract": _public_no_touch_contract(), "body_free_markers": _body_free_markers(), "body_free": True,
        "validation_evidence_intake_done_here": _r54_bool(r22.get("validation_evidence_intake_done_here")) and bool(r22), "local_root_preflight_passed_here": _r54_bool(r22.get("local_root_preflight_passed_here")) and bool(r22), "explicit_allow_present_here": _r54_bool(r22.get("explicit_allow_present_here")) and bool(r22), "purge_plan_verified_here": _r54_bool(r22.get("purge_plan_verified_here")) and bool(r22),
        **_r54_late_false_flags(),
    }
    material["p5_human_blind_qa_confirmed_candidate"] = _r54_bool(r22.get("p5_human_blind_qa_confirmed_candidate")) and built
    material["p5_repair_return_candidate"] = _r54_bool(r22.get("p5_repair_return_candidate")) and built
    material["p6_limited_human_readfeel_candidate"] = _r54_bool(r22.get("p6_limited_human_readfeel_candidate")) and built
    material["p8_question_design_material_candidate"] = _r54_bool(r22.get("p8_question_design_material_candidate")) and built
    material["actual_review_run_here"] = _r54_bool(r22.get("actual_review_run_here")) and built
    assert_p7_r54_validation_command_matrix_documentation_output_bodyfree_contract(material)
    return material


def assert_p7_r54_validation_command_matrix_documentation_output_bodyfree_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS, source="p7_r54_validation_command_matrix_documentation_output")
    _assert_body_free_common_with_false_keys(data, schema_version=P7_R54_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION, source="p7_r54_validation_command_matrix_documentation_output", false_key_refs=())
    if data.get("policy_section") != P7_R54_R23_STEP_REF or data.get("validation_documentation_status") not in P7_R54_VALIDATION_DOCUMENTATION_STATUS_REFS:
        raise ValueError("R54 R23 documentation contract changed")
    for false_key in ("validation_commands_ran_here", "actual_validation_execution_completed_here", "command_matrix_contains_local_absolute_path", "command_matrix_claims_full_backend_green", "backend_collect_only_is_full_suite_green", "rn_no_touch_is_real_device_readfeel", "full_backend_suite_green_confirmed", "backend_collect_only_claimed_as_full_backend_green", "rn_contract_claimed_as_real_device_modal_readfeel", "p5_human_blind_qa_confirmed_final", "p5_decision_finalized_here", "p6_limited_human_readfeel_start_allowed", "p8_start_allowed", "p7_complete", "release_allowed", "actual_human_review_run_here", "actual_manual_review_run_here", "question_text_included", "draft_question_text_included", "local_absolute_path_included", "runtime_changed_here", "api_route_changed_here", "db_schema_changed_here", "db_migration_changed_here", "rn_visible_contract_changed_here", "public_response_key_changed_here", "api_db_rn_response_key_changed_here", "question_api_implemented", "question_db_schema_implemented", "question_rn_ui_implemented", "question_response_key_implemented", "question_trigger_logic_implemented", "question_storage_schema_implemented", "question_answer_persistence_implemented", "question_plan_guard_implemented", "question_implementation_started_here", "p8_question_api_designed_here", "p8_question_db_schema_designed_here", "p8_question_rn_ui_designed_here", "p8_question_trigger_logic_designed_here", "p8_question_response_key_designed_here", "p8_question_plan_guard_designed_here"):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 R23 must keep {false_key}=False")
    if data.get("validation_documentation_status") == "VALIDATION_COMMAND_MATRIX_DOCUMENTATION_READY":
        if data.get("validation_command_matrix_materialized_here") is not True or data.get("documentation_output_materialized_here") is not True or data.get("required_command_groups_present") is not True:
            raise ValueError("R54 R23 ready documentation must materialize with required groups")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_R23_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_R23_NOT_YET_IMPLEMENTED_STEPS or data.get("next_required_step") != P7_R54_R23_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R23 ready step markers changed")
        for row in data.get("command_matrix_rows") or []:
            row_data = safe_mapping(row)
            if row_data.get("body_free") is not True or row_data.get("full_backend_suite_green_claimed") is not False:
                raise ValueError("R54 R23 command matrix row must stay body-free and non-inflated")
    else:
        if data.get("validation_command_matrix_materialized_here") is not False or data.get("documentation_output_materialized_here") is not False or data.get("next_required_step") != P7_R54_R23_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 R23 blocked documentation must not materialize")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_validation_command_matrix_documentation_output")
    return True


build_p7_r54_r52_reintake_handoff = build_p7_r54_r52_reintake_handoff_bodyfree
assert_p7_r54_r52_reintake_handoff_contract = assert_p7_r54_r52_reintake_handoff_bodyfree_contract
build_p7_r54_validation_command_matrix_documentation_output = build_p7_r54_validation_command_matrix_documentation_output_bodyfree
assert_p7_r54_validation_command_matrix_documentation_output_contract = assert_p7_r54_validation_command_matrix_documentation_output_bodyfree_contract
