# -*- coding: utf-8 -*-
"""P7-R52 R51 body-free handoff evidence decision-gate helpers.

R52-0 refreezes the *current received* local snapshot and keeps it separate
from the R51 helper's own source snapshot refs.  R52-1 freezes only the
validation evidence matrix used before the later R51 body-free handoff intake.

This module intentionally implements only R52-0 through R52-15.  It does not
run an actual human review, generate body-full packets, create rating/question
rows, write schema files, change API/DB/RN/public response contracts, start
P6/P8, complete P7, or claim release readiness.
"""

from __future__ import annotations

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
from emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution import (
    P7_R49_RN_CONTRACT_OPTIONAL_NO_TOUCH_TEST_REFS,
    P7_R49_VALIDATION_DISPLAY_API_TEST_FILE_REFS,
    P7_R49_VALIDATION_P5_CORE_TEST_FILE_REFS,
    P7_R49_VALIDATION_R46_HANDOFF_TEST_FILE_REFS,
    P7_R49_VALIDATION_R47_REGRESSION_TEST_FILE_REFS,
    P7_R49_VALIDATION_R48_REGRESSION_TEST_FILE_REFS,
    P7_R49_VALIDATION_R49_TARGET_TEST_FILE_REFS,
)
from emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision import (
    P7_R50_VALIDATION_R50_TARGET_TEST_FILE_REFS,
)
from emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run import (
    P7_R51_BODY_FREE_POST_REVIEW_SUMMARY_BUILDER_SCHEMA_VERSION,
    P7_R51_CURRENT_SOURCE_R50_HANDOFF_REFREEZE_SCHEMA_VERSION,
    P7_R51_NO_BODY_LEAK_FORBIDDEN_KEY_REFS,
    P7_R51_NO_BODY_LEAK_FORBIDDEN_TRUE_FLAG_REFS,
    P7_R51_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_BOUNDARY_VALIDATION_SCHEMA_VERSION,
    P7_R51_NO_TOUCH_MUTATION_TRUE_FLAG_REFS,
    P7_R51_P5_CONFIRMED_REPAIR_RETURN_INCONCLUSIVE_DECISION_SCHEMA_VERSION,
    P7_R51_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
    P7_R51_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
    P7_R51_R20_BOUNDARY_STATUS_REFS,
    P7_R51_R20_NEXT_REQUIRED_STEP_REF,
    P7_R51_REQUIRED_CASE_COUNT,
    P7_R51_SCOPE,
    P7_R51_SOURCE_SNAPSHOT_REFS,
    P7_R51_STEP,
    P7_R51_VALIDATION_EVIDENCE_R49_TIMEOUT_HANDLING_FREEZE_SCHEMA_VERSION,
)

P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r52.current_received_snapshot_refreeze.bodyfree.v1"
)
P7_R52_VALIDATION_EVIDENCE_MATRIX_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r52.validation_evidence_matrix_freeze.bodyfree.v1"
)

P7_R52_STEP: Final = "R52_R51BodyFreeHandoffEvidenceDecisionGate_20260621"
P7_R52_SCOPE: Final = "r51_bodyfree_handoff_p6_p8_start_decision_gate"
P7_R52_POLICY_KIND: Final = "r51_bodyfree_handoff_evidence_decision_gate"
P7_R52_DEFAULT_REVIEW_SESSION_ID: Final = "p7_r52_r51_bodyfree_handoff_evidence_decision_gate_session"
P7_R52_FIRST_NEXT_WORK_REF: Final = "r51_bodyfree_handoff_evidence_decision_gate_without_auto_allow"

P7_R52_R0_NEXT_REQUIRED_STEP_REF: Final = "R52-1_validation_evidence_matrix_freeze"
P7_R52_R1_NEXT_REQUIRED_STEP_REF: Final = "R52-2_r51_bodyfree_handoff_intake_contract"
P7_R52_R1_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R52-1_validation_evidence_before_R52-2_intake"

P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFS: Final[dict[str, str]] = {
    "premise_zip_ref": "Cocolon_前提資料(243).zip",
    "implemented_materials_zip_ref": "EmlisAIの実装済み資料(74).zip",
    "rn_zip_ref": "Cocolon(247).zip",
    "backend_zip_ref": "mashos-api(160).zip",
    "roadmap_ref": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619(4).md",
    "pre_design_memo_ref": "Cocolon_EmlisAI_P7_R52_R51Handoff_P6P8StartDecision_PreDesignMemo_20260621(1).md",
    "detailed_design_ref": "Cocolon_EmlisAI_P7_R52_R51HandoffEvidenceDecisionGate_DetailedDesign_ImplementationOrder_20260621(1).md",
}

P7_R52_R0_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R52-0_current_received_snapshot_r51_source_ref_separation",
)
P7_R52_FUTURE_STEPS_AFTER_R1: Final[tuple[str, ...]] = (
    "R52-2_r51_bodyfree_handoff_intake_contract",
    "R52-3_forbidden_payload_deep_scan",
    "R52-4_actual_review_evidence_completeness_checker",
    "R52-5_evidence_missing_no_go_branch",
    "R52-6_disposal_safety_gate",
    "R52-7_execution_blocker_gate",
    "R52-8_rating_question_consistency_gate",
    "R52-9_p5_readfeel_blocker_gate",
    "R52-10_p5_confirmed_candidate_decision",
    "R52-11_p6_limited_human_readfeel_candidate_separation",
    "R52-12_p8_question_material_candidate_separation",
    "R52-13_final_decision_composer",
    "R52-14_no_touch_boundary_validation",
    "R52-15_documentation_output",
)
P7_R52_R0_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R52-1_validation_evidence_matrix_freeze",
    *P7_R52_FUTURE_STEPS_AFTER_R1,
)
P7_R52_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R52_R0_IMPLEMENTED_STEPS,
    "R52-1_validation_evidence_matrix_freeze",
)
P7_R52_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R52_FUTURE_STEPS_AFTER_R1

P7_R52_VALIDATION_EVIDENCE_GROUP_REFS: Final[tuple[str, ...]] = (
    "rn_contract",
    "r51_target",
    "r50_target_regression",
    "r49_split_matrix",
    "r49_combined_command",
    "r48_regression",
    "r47_regression",
    "r46_display_p5_core_subset",
    "backend_collect_only",
)
P7_R52_VALIDATION_EVIDENCE_REQUIRED_GROUP_REFS: Final[tuple[str, ...]] = (
    "rn_contract",
    "r51_target",
    "r50_target_regression",
    "r49_split_matrix",
    "r48_regression",
    "r47_regression",
    "r46_display_p5_core_subset",
    "backend_collect_only",
)
P7_R52_R49_COMBINED_COMMAND_TEST_FILE_REFS: Final[tuple[str, ...]] = (
    "tests/test_emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution_*.py",
)
P7_R52_R51_TARGET_TEST_FILE_REFS: Final[tuple[str, ...]] = (
    "tests/test_emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run_*.py",
)

P7_R52_EXECUTION_BLOCKER_ID_REFS: Final[tuple[str, ...]] = (
    "r52_missing_rn_contract_green_evidence",
    "r52_missing_r51_target_green_evidence",
    "r52_missing_r50_target_green_evidence",
    "r52_missing_r49_split_green_evidence",
    "r52_missing_r48_regression_green_evidence",
    "r52_missing_r47_regression_green_evidence",
    "r52_missing_r46_display_p5_core_green_evidence",
    "r52_missing_backend_collect_only_evidence",
    "r52_validation_evidence_not_ready",
)

P7_R52_QUESTION_IMPLEMENTATION_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    "question_api_implemented",
    "question_db_schema_implemented",
    "question_rn_ui_implemented",
    "question_response_key_implemented",
    "question_trigger_logic_implemented",
    "question_storage_schema_implemented",
    "question_answer_persistence_implemented",
    "question_plan_guard_implemented",
    "p8_question_implementation_spec_finalized_here",
)
P7_R52_REVIEW_RELEASE_CLOSED_KEY_REFS: Final[tuple[str, ...]] = (
    "r52_body_full_packet_generated_here",
    "r52_body_full_packets_created_local_only",
    "r52_actual_human_review_run_here",
    "r52_actual_manual_review_run_here",
    "r52_actual_rating_rows_materialized_here",
    "r52_actual_blocker_rows_materialized_here",
    "r52_actual_execution_blocker_rows_materialized_here",
    "r52_actual_question_need_observation_rows_materialized_here",
    "r52_actual_question_need_observation_summary_materialized_here",
    "r52_actual_reviewer_notes_materialized_here",
    "r52_actual_disposal_run_here",
    "r52_disposal_receipt_materialized_here",
    "r52_actual_disposal_receipt_materialized_here",
    "r52_post_review_summary_materialized_here",
    "p5_human_blind_qa_confirmed",
    "p5_human_blind_qa_confirmed_final",
    "p6_limited_human_readfeel_start_allowed",
    "p8_start_allowed",
    "p7_complete",
    "release_allowed",
    "hold004_close_allowed",
)
P7_R52_SCHEMA_MUTATION_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    "json_schema_file_created_here",
    "schema_files_materialized_here",
    "api_db_rn_response_key_changed_here",
    "runtime_changed_here",
    "api_route_changed_here",
    "db_schema_changed_here",
    "db_migration_changed_here",
    "rn_visible_contract_changed_here",
    "public_response_top_level_key_added_here",
)
P7_R52_R0_R1_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    *P7_R52_QUESTION_IMPLEMENTATION_FALSE_KEY_REFS,
    *P7_R52_REVIEW_RELEASE_CLOSED_KEY_REFS,
    *P7_R52_SCHEMA_MUTATION_FALSE_KEY_REFS,
)

P7_R52_VALIDATION_EVIDENCE_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "evidence_group_ref",
    "evidence_status_ref",
    "evidence_present",
    "passed_count",
    "collected_count",
    "warning_count",
    "timeout_unclassified",
    "split_only",
    "combined_green_claimed",
    "required_for_r52_2_intake",
    "optional",
    "test_file_refs",
    "evidence_source_ref",
    "claim_boundary_ref",
    "evidence_created_here",
    "validation_commands_executed_here",
    "command_result_body_stored_here",
    "terminal_output_stored_here",
    "body_free",
)
P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "required_case_count",
    "source_mode",
    "git_check_required",
    "git_check_performed",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "r51_helper_source_snapshot_refs",
    "r51_helper_source_snapshot_ref_count",
    "source_refs_are_separated",
    "current_received_refs_reuse_r51_helper_refs",
    "source_ref_separation_reason_refs",
    "r51_helper_step",
    "r51_helper_scope",
    "r51_helper_refreeze_schema_version",
    "r51_helper_validation_schema_version",
    "r51_actual_review_evidence_expected_from_r51_later",
    "r51_actual_review_evidence_complete",
    "r52_0_current_received_snapshot_refrozen",
    "r52_1_validation_evidence_matrix_frozen",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r52_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R52_R0_R1_FALSE_KEY_REFS,
)
P7_R52_VALIDATION_EVIDENCE_MATRIX_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "required_case_count",
    "r0_refreeze_schema_version",
    "r0_refreeze_material_ref",
    "current_received_snapshot_refs",
    "r51_helper_source_snapshot_refs",
    "source_refs_are_separated",
    "validation_evidence_group_refs",
    "validation_evidence_rows",
    "validation_evidence_row_count",
    "validation_evidence_required_group_refs",
    "validation_evidence_required_groups_present",
    "rn_contract_green_evidence_present",
    "r51_target_green_evidence_present",
    "r50_target_green_evidence_present",
    "r49_split_matrix_green_evidence_present",
    "r49_split_matrix_green_required_for_r52_2_intake",
    "r49_combined_timeout_unclassified",
    "r49_combined_green_claim_allowed",
    "r49_combined_green_claimed",
    "r49_combined_required_for_r52_2_intake",
    "r49_split_evidence_claimed_as_combined_green",
    "r48_regression_green_evidence_present",
    "r47_regression_green_evidence_present",
    "r46_display_p5_core_green_evidence_present",
    "backend_collect_only_evidence_present",
    "full_backend_suite_green_confirmed",
    "backend_collect_only_claimed_as_full_backend_green",
    "rn_contract_claimed_as_real_device_modal_readfeel",
    "validation_commands_executed_here",
    "command_result_body_stored_here",
    "terminal_output_stored_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "r52_0_current_received_snapshot_refrozen",
    "r52_1_validation_evidence_matrix_frozen",
    "validation_evidence_ready_for_r52_2_intake",
    "execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r52_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R52_R0_R1_FALSE_KEY_REFS,
)


def _false_flags() -> dict[str, bool]:
    return {key: False for key in P7_R52_R0_R1_FALSE_KEY_REFS}


def _safe_bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return bool(value)


def _safe_non_negative_int(value: Any) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return 0
    return max(number, 0)


def _safe_review_session_id(value: Any) -> str:
    return clean_identifier(value, default=P7_R52_DEFAULT_REVIEW_SESSION_ID, max_length=140)


def _snapshot_refs(base: Mapping[str, str], overrides: Mapping[str, Any] | None = None) -> dict[str, str]:
    refs = dict(base)
    for key, value in safe_mapping(overrides).items():
        if key in refs:
            refs[key] = clean_identifier(value, default=refs[key], max_length=240)
    return refs


def _current_received_snapshot_refs(overrides: Mapping[str, Any] | None = None) -> dict[str, str]:
    return _snapshot_refs(P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFS, overrides)


def _r51_helper_snapshot_refs(overrides: Mapping[str, Any] | None = None) -> dict[str, str]:
    return _snapshot_refs(P7_R51_SOURCE_SNAPSHOT_REFS, overrides)


def _refs_are_separated(current_refs: Mapping[str, Any], r51_refs: Mapping[str, Any]) -> bool:
    if not current_refs or not r51_refs:
        return False
    shared_keys = set(current_refs) & set(r51_refs)
    if not shared_keys:
        return False
    return any(str(current_refs.get(key)) != str(r51_refs.get(key)) for key in shared_keys)


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
    if data.get("step") != P7_R52_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R52_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("source_mode", P7_SOURCE_MODE) != P7_SOURCE_MODE:
        raise ValueError(f"{source} must remain local snapshot")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must be body-free")
    assert_false_markers(data.get("public_contract") or {}, source=f"{source}.public_contract")
    assert_false_markers(data.get("r52_public_no_touch_contract") or {}, source=f"{source}.r52_public_no_touch_contract")
    assert_false_markers(data.get("body_free_markers") or {}, source=f"{source}.body_free_markers")
    for false_key in P7_R52_R0_R1_FALSE_KEY_REFS:
        if data.get(false_key) is not False:
            raise ValueError(f"{source} must keep {false_key}=False")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)


def _evidence_row(
    *,
    evidence_group_ref: str,
    evidence_status_ref: str,
    evidence_present: bool,
    passed_count: int = 0,
    collected_count: int = 0,
    warning_count: int = 0,
    timeout_unclassified: bool = False,
    split_only: bool = False,
    combined_green_claimed: bool = False,
    required_for_r52_2_intake: bool = True,
    optional: bool = False,
    test_file_refs: Sequence[Any] | Any | None = (),
    evidence_source_ref: str = "p7_r52_validation_evidence_matrix_freeze",
    claim_boundary_ref: str = "validation evidence only",
) -> dict[str, Any]:
    row = {
        "evidence_group_ref": clean_identifier(evidence_group_ref, default="unknown_evidence_group", max_length=120),
        "evidence_status_ref": clean_identifier(evidence_status_ref, default="UNKNOWN", max_length=120),
        "evidence_present": bool(evidence_present),
        "passed_count": _safe_non_negative_int(passed_count),
        "collected_count": _safe_non_negative_int(collected_count),
        "warning_count": _safe_non_negative_int(warning_count),
        "timeout_unclassified": bool(timeout_unclassified),
        "split_only": bool(split_only),
        "combined_green_claimed": bool(combined_green_claimed),
        "required_for_r52_2_intake": bool(required_for_r52_2_intake),
        "optional": bool(optional),
        "test_file_refs": dedupe_identifiers(test_file_refs, limit=100, max_length=280),
        "evidence_source_ref": clean_identifier(evidence_source_ref, default="p7_r52_validation_evidence_matrix_freeze", max_length=240),
        "claim_boundary_ref": clean_identifier(claim_boundary_ref, default="validation evidence only", max_length=280),
        "evidence_created_here": False,
        "validation_commands_executed_here": False,
        "command_result_body_stored_here": False,
        "terminal_output_stored_here": False,
        "body_free": True,
    }
    assert_p7_r52_validation_evidence_row_contract(row)
    return row


def _default_validation_evidence_rows() -> list[dict[str, Any]]:
    return [
        _evidence_row(
            evidence_group_ref="rn_contract",
            evidence_status_ref="PASSED",
            evidence_present=True,
            passed_count=36,
            test_file_refs=P7_R49_RN_CONTRACT_OPTIONAL_NO_TOUCH_TEST_REFS,
            evidence_source_ref="R52_pre_design_memo_20260621_current_local_validation",
            claim_boundary_ref="RN contract only; not real-device modal readfeel",
        ),
        _evidence_row(
            evidence_group_ref="r51_target",
            evidence_status_ref="PASSED",
            evidence_present=True,
            passed_count=125,
            test_file_refs=P7_R52_R51_TARGET_TEST_FILE_REFS,
            evidence_source_ref="R52_pre_design_memo_20260621_current_local_validation",
            claim_boundary_ref="R51 target helper green only; not P5 actual human review completion",
        ),
        _evidence_row(
            evidence_group_ref="r50_target_regression",
            evidence_status_ref="PASSED",
            evidence_present=True,
            passed_count=99,
            test_file_refs=P7_R50_VALIDATION_R50_TARGET_TEST_FILE_REFS,
            evidence_source_ref="R52_pre_design_memo_20260621_current_local_validation",
            claim_boundary_ref="R50 target regression only; not P5 actual human review completion",
        ),
        _evidence_row(
            evidence_group_ref="r49_split_matrix",
            evidence_status_ref="PASSED_BY_SPLIT_EXECUTION",
            evidence_present=True,
            passed_count=76,
            split_only=True,
            test_file_refs=P7_R49_VALIDATION_R49_TARGET_TEST_FILE_REFS,
            evidence_source_ref="R52_pre_design_memo_20260621_current_local_validation",
            claim_boundary_ref="R49 split evidence only; combined green is not claimed",
        ),
        _evidence_row(
            evidence_group_ref="r49_combined_command",
            evidence_status_ref="TIMEOUT_UNCLASSIFIED",
            evidence_present=True,
            timeout_unclassified=True,
            required_for_r52_2_intake=False,
            optional=True,
            test_file_refs=P7_R52_R49_COMBINED_COMMAND_TEST_FILE_REFS,
            evidence_source_ref="R52_pre_design_memo_20260621_current_local_validation",
            claim_boundary_ref="combined command timeout remains visible; not green evidence",
        ),
        _evidence_row(
            evidence_group_ref="r48_regression",
            evidence_status_ref="PASSED",
            evidence_present=True,
            passed_count=82,
            test_file_refs=P7_R49_VALIDATION_R48_REGRESSION_TEST_FILE_REFS,
            evidence_source_ref="R52_pre_design_memo_20260621_current_local_validation",
            claim_boundary_ref="R48 review-packet regression only; not P5 confirmed",
        ),
        _evidence_row(
            evidence_group_ref="r47_regression",
            evidence_status_ref="PASSED",
            evidence_present=True,
            passed_count=275,
            test_file_refs=P7_R49_VALIDATION_R47_REGRESSION_TEST_FILE_REFS,
            evidence_source_ref="R52_pre_design_memo_20260621_current_local_validation",
            claim_boundary_ref="R47 local-only/body-free policy regression only",
        ),
        _evidence_row(
            evidence_group_ref="r46_display_p5_core_subset",
            evidence_status_ref="PASSED_WITH_KNOWN_WARNING",
            evidence_present=True,
            passed_count=94,
            warning_count=1,
            test_file_refs=(
                *P7_R49_VALIDATION_R46_HANDOFF_TEST_FILE_REFS,
                *P7_R49_VALIDATION_DISPLAY_API_TEST_FILE_REFS,
                *P7_R49_VALIDATION_P5_CORE_TEST_FILE_REFS,
            ),
            evidence_source_ref="R52_pre_design_memo_20260621_current_local_validation",
            claim_boundary_ref="R46/display/P5 core subset only; not real-device modal readfeel or full backend suite green",
        ),
        _evidence_row(
            evidence_group_ref="backend_collect_only",
            evidence_status_ref="COLLECT_ONLY_PASSED_WITH_KNOWN_WARNING",
            evidence_present=True,
            collected_count=3591,
            warning_count=1,
            test_file_refs=("pytest --collect-only -q",),
            evidence_source_ref="R52_pre_design_memo_20260621_current_local_validation",
            claim_boundary_ref="collect-only only; must not be claimed as full backend suite execution green",
        ),
    ]


def _is_sequence_not_string(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _validation_evidence_rows_with_overrides(overrides: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    rows = _default_validation_evidence_rows()
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
            "evidence_status_ref",
            "evidence_present",
            "passed_count",
            "collected_count",
            "warning_count",
            "timeout_unclassified",
            "split_only",
            "combined_green_claimed",
            "required_for_r52_2_intake",
            "optional",
            "test_file_refs",
            "evidence_source_ref",
            "claim_boundary_ref",
        ):
            if key in patch:
                merged[key] = patch[key]
        out.append(
            _evidence_row(
                evidence_group_ref=group_ref,
                evidence_status_ref=clean_identifier(merged.get("evidence_status_ref"), default="UNKNOWN", max_length=120),
                evidence_present=_safe_bool(merged.get("evidence_present")),
                passed_count=_safe_non_negative_int(merged.get("passed_count")),
                collected_count=_safe_non_negative_int(merged.get("collected_count")),
                warning_count=_safe_non_negative_int(merged.get("warning_count")),
                timeout_unclassified=_safe_bool(merged.get("timeout_unclassified")),
                split_only=_safe_bool(merged.get("split_only")),
                combined_green_claimed=_safe_bool(merged.get("combined_green_claimed")),
                required_for_r52_2_intake=_safe_bool(merged.get("required_for_r52_2_intake"), default=True),
                optional=_safe_bool(merged.get("optional")),
                test_file_refs=merged.get("test_file_refs") if _is_sequence_not_string(merged.get("test_file_refs")) else row["test_file_refs"],
                evidence_source_ref=clean_identifier(merged.get("evidence_source_ref"), default="p7_r52_validation_evidence_matrix_freeze", max_length=240),
                claim_boundary_ref=clean_identifier(merged.get("claim_boundary_ref"), default="validation evidence only", max_length=280),
            )
        )
    return out


def _validation_flags(rows: Sequence[Mapping[str, Any]]) -> dict[str, bool]:
    by_group = {str(row.get("evidence_group_ref")): row for row in rows}
    required_present = all(
        by_group.get(group_ref, {}).get("evidence_present") is True
        for group_ref in P7_R52_VALIDATION_EVIDENCE_REQUIRED_GROUP_REFS
    )
    return {
        "validation_evidence_required_groups_present": required_present,
        "rn_contract_green_evidence_present": by_group.get("rn_contract", {}).get("evidence_present") is True,
        "r51_target_green_evidence_present": by_group.get("r51_target", {}).get("evidence_present") is True,
        "r50_target_green_evidence_present": by_group.get("r50_target_regression", {}).get("evidence_present") is True,
        "r49_split_matrix_green_evidence_present": by_group.get("r49_split_matrix", {}).get("evidence_present") is True,
        "r49_combined_timeout_unclassified": by_group.get("r49_combined_command", {}).get("timeout_unclassified") is True,
        "r48_regression_green_evidence_present": by_group.get("r48_regression", {}).get("evidence_present") is True,
        "r47_regression_green_evidence_present": by_group.get("r47_regression", {}).get("evidence_present") is True,
        "r46_display_p5_core_green_evidence_present": by_group.get("r46_display_p5_core_subset", {}).get("evidence_present") is True,
        "backend_collect_only_evidence_present": by_group.get("backend_collect_only", {}).get("evidence_present") is True,
    }


def _validation_execution_blockers(flags: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    if flags.get("rn_contract_green_evidence_present") is not True:
        blockers.append("r52_missing_rn_contract_green_evidence")
    if flags.get("r51_target_green_evidence_present") is not True:
        blockers.append("r52_missing_r51_target_green_evidence")
    if flags.get("r50_target_green_evidence_present") is not True:
        blockers.append("r52_missing_r50_target_green_evidence")
    if flags.get("r49_split_matrix_green_evidence_present") is not True:
        blockers.append("r52_missing_r49_split_green_evidence")
    if flags.get("r48_regression_green_evidence_present") is not True:
        blockers.append("r52_missing_r48_regression_green_evidence")
    if flags.get("r47_regression_green_evidence_present") is not True:
        blockers.append("r52_missing_r47_regression_green_evidence")
    if flags.get("r46_display_p5_core_green_evidence_present") is not True:
        blockers.append("r52_missing_r46_display_p5_core_green_evidence")
    if flags.get("backend_collect_only_evidence_present") is not True:
        blockers.append("r52_missing_backend_collect_only_evidence")
    return blockers


def assert_p7_r52_validation_evidence_row_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(
        data,
        required=P7_R52_VALIDATION_EVIDENCE_ROW_REQUIRED_FIELD_REFS,
        source="p7_r52_validation_evidence_row",
    )
    group_ref = data.get("evidence_group_ref")
    if group_ref not in P7_R52_VALIDATION_EVIDENCE_GROUP_REFS:
        raise ValueError("R52 evidence group ref is not canonical")
    for int_key in ("passed_count", "collected_count", "warning_count"):
        if not isinstance(data.get(int_key), int) or data[int_key] < 0:
            raise ValueError(f"R52 evidence row must keep non-negative {int_key}")
    for false_key in (
        "evidence_created_here",
        "validation_commands_executed_here",
        "command_result_body_stored_here",
        "terminal_output_stored_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R52 evidence row must keep {false_key}=False")
    if data.get("body_free") is not True:
        raise ValueError("R52 evidence row must be body-free")
    if group_ref == "r49_split_matrix":
        if data.get("split_only") is not True:
            raise ValueError("R52 R49 split row must remain split_only")
        if data.get("evidence_present") is True and data.get("evidence_status_ref") != "PASSED_BY_SPLIT_EXECUTION":
            raise ValueError("R52 R49 split row must remain split execution evidence")
        if data.get("evidence_present") is False and data.get("evidence_status_ref") not in {"MISSING", "UNCONFIRMED"}:
            raise ValueError("R52 missing R49 split evidence must be explicit")
        if data.get("combined_green_claimed") is not False:
            raise ValueError("R52 R49 split row must not claim combined green")
        if data.get("required_for_r52_2_intake") is not True:
            raise ValueError("R52 R49 split row must be required before R52-2")
    elif group_ref == "r49_combined_command":
        if data.get("evidence_status_ref") != "TIMEOUT_UNCLASSIFIED":
            raise ValueError("R52 R49 combined command must remain TIMEOUT_UNCLASSIFIED")
        if data.get("timeout_unclassified") is not True:
            raise ValueError("R52 R49 combined command timeout must remain visible")
        if data.get("required_for_r52_2_intake") is not False:
            raise ValueError("R52 R49 combined command must not be required before R52-2")
        if data.get("combined_green_claimed") is not False:
            raise ValueError("R52 R49 combined command must not claim green")
    else:
        if data.get("timeout_unclassified") is not False:
            raise ValueError("R52 non-combined rows must not carry timeout_unclassified")
        if data.get("combined_green_claimed") is not False:
            raise ValueError("R52 non-combined rows must not claim combined green")
    if group_ref == "backend_collect_only":
        if data.get("evidence_present") is True:
            if data.get("evidence_status_ref") != "COLLECT_ONLY_PASSED_WITH_KNOWN_WARNING":
                raise ValueError("R52 backend collect-only row must not become full-suite green")
            if data.get("collected_count", 0) < 1:
                raise ValueError("R52 backend collect-only row must keep collected_count evidence")
        elif data.get("evidence_status_ref") not in {"MISSING", "UNCONFIRMED"}:
            raise ValueError("R52 missing backend collect-only evidence must be explicit")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r52_validation_evidence_row")
    return True


def build_p7_r52_current_received_snapshot_refreeze(
    *,
    current_received_snapshot_refs: Mapping[str, Any] | None = None,
    r51_helper_source_snapshot_refs: Mapping[str, Any] | None = None,
    review_session_id: Any = P7_R52_DEFAULT_REVIEW_SESSION_ID,
    material_id: Any = "p7_r52_current_received_snapshot_refreeze",
) -> dict[str, Any]:
    """Build R52-0 current received snapshot / R51 source ref separation."""

    current_refs = _current_received_snapshot_refs(current_received_snapshot_refs)
    r51_refs = _r51_helper_snapshot_refs(r51_helper_source_snapshot_refs)
    separated = _refs_are_separated(current_refs, r51_refs)
    refreeze = {
        "schema_version": P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R52_STEP,
        "scope": P7_R52_SCOPE,
        "policy_kind": P7_R52_POLICY_KIND,
        "policy_section": "R52-0_current_received_snapshot_r51_source_ref_separation",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r52_current_received_snapshot_refreeze", max_length=180),
        "review_session_id": _safe_review_session_id(review_session_id),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "source_mode": P7_SOURCE_MODE,
        "git_check_required": False,
        "git_check_performed": False,
        "current_received_snapshot_refs": current_refs,
        "current_received_snapshot_ref_count": len(current_refs),
        "r51_helper_source_snapshot_refs": r51_refs,
        "r51_helper_source_snapshot_ref_count": len(r51_refs),
        "source_refs_are_separated": separated,
        "current_received_refs_reuse_r51_helper_refs": not separated,
        "source_ref_separation_reason_refs": [
            "r52_received_snapshot_must_not_overwrite_r51_helper_source_refs",
            "r51_helper_refs_are_historical_input_to_r52_not_current_source_truth",
        ],
        "r51_helper_step": P7_R51_STEP,
        "r51_helper_scope": P7_R51_SCOPE,
        "r51_helper_refreeze_schema_version": P7_R51_CURRENT_SOURCE_R50_HANDOFF_REFREEZE_SCHEMA_VERSION,
        "r51_helper_validation_schema_version": P7_R51_VALIDATION_EVIDENCE_R49_TIMEOUT_HANDLING_FREEZE_SCHEMA_VERSION,
        "r51_actual_review_evidence_expected_from_r51_later": True,
        "r51_actual_review_evidence_complete": False,
        "r52_0_current_received_snapshot_refrozen": True,
        "r52_1_validation_evidence_matrix_frozen": False,
        "implemented_steps": list(P7_R52_R0_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R52_R0_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R52_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R52_R0_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r52_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r52_current_received_snapshot_refreeze_contract(refreeze)
    return refreeze


def assert_p7_r52_current_received_snapshot_refreeze_contract(refreeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(refreeze)
    _assert_required_fields(
        data,
        required=P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_REQUIRED_FIELD_REFS,
        source="p7_r52_r0_current_received_snapshot_refreeze",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION,
        source="p7_r52_r0_current_received_snapshot_refreeze",
    )
    if data.get("policy_section") != "R52-0_current_received_snapshot_r51_source_ref_separation":
        raise ValueError("R52 R0 policy section changed")
    if data.get("source_mode") != P7_SOURCE_MODE or data.get("git_check_required") is not False or data.get("git_check_performed") is not False:
        raise ValueError("R52 R0 must remain local snapshot without Git check")
    current_refs = safe_mapping(data.get("current_received_snapshot_refs"))
    r51_refs = safe_mapping(data.get("r51_helper_source_snapshot_refs"))
    if current_refs != P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("R52 R0 current received snapshot refs changed")
    if r51_refs != P7_R51_SOURCE_SNAPSHOT_REFS:
        raise ValueError("R52 R0 R51 helper source snapshot refs changed")
    if data.get("current_received_snapshot_ref_count") != len(P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFS):
        raise ValueError("R52 R0 current received snapshot ref count changed")
    if data.get("r51_helper_source_snapshot_ref_count") != len(P7_R51_SOURCE_SNAPSHOT_REFS):
        raise ValueError("R52 R0 R51 helper source snapshot ref count changed")
    if data.get("source_refs_are_separated") is not True:
        raise ValueError("R52 R0 must keep current received refs separated from R51 helper refs")
    if data.get("current_received_refs_reuse_r51_helper_refs") is not False:
        raise ValueError("R52 R0 must not reuse R51 helper refs as current received refs")
    if data.get("r51_actual_review_evidence_expected_from_r51_later") is not True:
        raise ValueError("R52 R0 must expect actual review evidence from R51 later")
    if data.get("r51_actual_review_evidence_complete") is not False:
        raise ValueError("R52 R0 must not claim R51 actual review evidence complete")
    if data.get("r52_0_current_received_snapshot_refrozen") is not True:
        raise ValueError("R52 R0 must mark current received snapshot refrozen")
    if data.get("r52_1_validation_evidence_matrix_frozen") is not False:
        raise ValueError("R52 R0 must not claim R52-1")
    if tuple(data.get("implemented_steps") or ()) != P7_R52_R0_IMPLEMENTED_STEPS:
        raise ValueError("R52 R0 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R52_R0_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R52 R0 not-yet steps changed")
    if data.get("next_required_step") != P7_R52_R0_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R52 R0 must point to R52-1")
    return True


def build_p7_r52_validation_evidence_matrix_freeze(
    *,
    current_received_snapshot_refreeze: Mapping[str, Any] | None = None,
    validation_evidence_overrides: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r52_validation_evidence_matrix_freeze",
) -> dict[str, Any]:
    """Build R52-1 validation evidence matrix freeze."""

    r0 = safe_mapping(current_received_snapshot_refreeze) if current_received_snapshot_refreeze is not None else build_p7_r52_current_received_snapshot_refreeze()
    assert_p7_r52_current_received_snapshot_refreeze_contract(r0)
    rows = _validation_evidence_rows_with_overrides(validation_evidence_overrides)
    flags = _validation_flags(rows)
    blockers = _validation_execution_blockers(flags)
    ready_for_intake = flags["validation_evidence_required_groups_present"] and not blockers
    freeze = {
        "schema_version": P7_R52_VALIDATION_EVIDENCE_MATRIX_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R52_STEP,
        "scope": P7_R52_SCOPE,
        "policy_kind": P7_R52_POLICY_KIND,
        "policy_section": "R52-1_validation_evidence_matrix_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r52_validation_evidence_matrix_freeze", max_length=180),
        "review_session_id": clean_identifier(r0.get("review_session_id"), default=P7_R52_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "r0_refreeze_schema_version": P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION,
        "r0_refreeze_material_ref": clean_identifier(r0.get("material_id"), default="p7_r52_current_received_snapshot_refreeze", max_length=180),
        "current_received_snapshot_refs": safe_mapping(r0.get("current_received_snapshot_refs")),
        "r51_helper_source_snapshot_refs": safe_mapping(r0.get("r51_helper_source_snapshot_refs")),
        "source_refs_are_separated": True,
        "validation_evidence_group_refs": list(P7_R52_VALIDATION_EVIDENCE_GROUP_REFS),
        "validation_evidence_rows": rows,
        "validation_evidence_row_count": len(rows),
        "validation_evidence_required_group_refs": list(P7_R52_VALIDATION_EVIDENCE_REQUIRED_GROUP_REFS),
        "validation_evidence_required_groups_present": flags["validation_evidence_required_groups_present"],
        "rn_contract_green_evidence_present": flags["rn_contract_green_evidence_present"],
        "r51_target_green_evidence_present": flags["r51_target_green_evidence_present"],
        "r50_target_green_evidence_present": flags["r50_target_green_evidence_present"],
        "r49_split_matrix_green_evidence_present": flags["r49_split_matrix_green_evidence_present"],
        "r49_split_matrix_green_required_for_r52_2_intake": True,
        "r49_combined_timeout_unclassified": flags["r49_combined_timeout_unclassified"],
        "r49_combined_green_claim_allowed": False,
        "r49_combined_green_claimed": False,
        "r49_combined_required_for_r52_2_intake": False,
        "r49_split_evidence_claimed_as_combined_green": False,
        "r48_regression_green_evidence_present": flags["r48_regression_green_evidence_present"],
        "r47_regression_green_evidence_present": flags["r47_regression_green_evidence_present"],
        "r46_display_p5_core_green_evidence_present": flags["r46_display_p5_core_green_evidence_present"],
        "backend_collect_only_evidence_present": flags["backend_collect_only_evidence_present"],
        "full_backend_suite_green_confirmed": False,
        "backend_collect_only_claimed_as_full_backend_green": False,
        "rn_contract_claimed_as_real_device_modal_readfeel": False,
        "validation_commands_executed_here": False,
        "command_result_body_stored_here": False,
        "terminal_output_stored_here": False,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "r52_0_current_received_snapshot_refrozen": True,
        "r52_1_validation_evidence_matrix_frozen": True,
        "validation_evidence_ready_for_r52_2_intake": ready_for_intake,
        "execution_blocker_ids": blockers,
        "implemented_steps": list(P7_R52_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R52_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R52_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R52_R1_NEXT_REQUIRED_STEP_REF if ready_for_intake else P7_R52_R1_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r52_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r52_validation_evidence_matrix_freeze_contract(freeze)
    return freeze


def assert_p7_r52_validation_evidence_matrix_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_required_fields(
        data,
        required=P7_R52_VALIDATION_EVIDENCE_MATRIX_FREEZE_REQUIRED_FIELD_REFS,
        source="p7_r52_r1_validation_evidence_matrix_freeze",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R52_VALIDATION_EVIDENCE_MATRIX_FREEZE_SCHEMA_VERSION,
        source="p7_r52_r1_validation_evidence_matrix_freeze",
    )
    if data.get("policy_section") != "R52-1_validation_evidence_matrix_freeze":
        raise ValueError("R52 R1 policy section changed")
    if safe_mapping(data.get("current_received_snapshot_refs")) != P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("R52 R1 current received snapshot refs changed")
    if safe_mapping(data.get("r51_helper_source_snapshot_refs")) != P7_R51_SOURCE_SNAPSHOT_REFS:
        raise ValueError("R52 R1 R51 helper source snapshot refs changed")
    if data.get("source_refs_are_separated") is not True:
        raise ValueError("R52 R1 must keep source refs separated")
    rows = data.get("validation_evidence_rows")
    if not isinstance(rows, list) or len(rows) != len(P7_R52_VALIDATION_EVIDENCE_GROUP_REFS):
        raise ValueError("R52 R1 evidence rows changed")
    for row in rows:
        assert_p7_r52_validation_evidence_row_contract(safe_mapping(row))
    if [row.get("evidence_group_ref") for row in rows] != list(P7_R52_VALIDATION_EVIDENCE_GROUP_REFS):
        raise ValueError("R52 R1 evidence row order changed")
    flags = _validation_flags([safe_mapping(row) for row in rows])
    for key, value in flags.items():
        if data.get(key) is not value:
            raise ValueError(f"R52 R1 top-level flag mismatch for {key}")
    if data.get("r49_split_matrix_green_required_for_r52_2_intake") is not True:
        raise ValueError("R52 R1 must require R49 split evidence before R52-2")
    for false_key in (
        "r49_combined_green_claim_allowed",
        "r49_combined_green_claimed",
        "r49_combined_required_for_r52_2_intake",
        "r49_split_evidence_claimed_as_combined_green",
        "full_backend_suite_green_confirmed",
        "backend_collect_only_claimed_as_full_backend_green",
        "rn_contract_claimed_as_real_device_modal_readfeel",
        "validation_commands_executed_here",
        "command_result_body_stored_here",
        "terminal_output_stored_here",
        "actual_manual_review_run_here",
        "body_full_packet_generated_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R52 R1 must keep {false_key}=False")
    for true_key in ("r52_0_current_received_snapshot_refrozen", "r52_1_validation_evidence_matrix_frozen"):
        if data.get(true_key) is not True:
            raise ValueError(f"R52 R1 must keep {true_key}=True")
    blockers = _validation_execution_blockers(flags)
    if tuple(data.get("execution_blocker_ids") or ()) != tuple(blockers):
        raise ValueError("R52 R1 execution blockers do not match validation flags")
    ready = flags["validation_evidence_required_groups_present"] and not blockers
    if data.get("validation_evidence_ready_for_r52_2_intake") is not ready:
        raise ValueError("R52 R1 evidence readiness does not match required evidence")
    if ready:
        if data.get("next_required_step") != P7_R52_R1_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R52 R1 ready evidence must point to R52-2")
    else:
        if data.get("next_required_step") != P7_R52_R1_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R52 R1 blocked evidence must point to evidence resolution")
    if tuple(data.get("implemented_steps") or ()) != P7_R52_IMPLEMENTED_STEPS:
        raise ValueError("R52 R1 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R52_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R52 R1 not-yet steps changed")
    return True


def build_p7_r52_r0_r1_current_snapshot_validation_evidence_freeze(
    *,
    current_received_snapshot_refreeze: Mapping[str, Any] | None = None,
    validation_evidence_matrix_freeze: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the R52-1 material after validating the R52-0/R52-1 chain."""

    r0 = safe_mapping(current_received_snapshot_refreeze) if current_received_snapshot_refreeze is not None else build_p7_r52_current_received_snapshot_refreeze()
    assert_p7_r52_current_received_snapshot_refreeze_contract(r0)
    r1 = (
        safe_mapping(validation_evidence_matrix_freeze)
        if validation_evidence_matrix_freeze is not None
        else build_p7_r52_validation_evidence_matrix_freeze(current_received_snapshot_refreeze=r0)
    )
    assert_p7_r52_validation_evidence_matrix_freeze_contract(r1)
    if r1.get("r0_refreeze_material_ref") != r0.get("material_id"):
        raise ValueError("R52 R0/R1 chain material refs do not match")
    return r1

# ---------------------------------------------------------------------------
# R52-2 / R52-3: R51 body-free handoff intake + forbidden payload deep scan.
# ---------------------------------------------------------------------------

P7_R52_R51_BODYFREE_HANDOFF_INTAKE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r52.r51_bodyfree_handoff_intake.bodyfree.v1"
)
P7_R52_FORBIDDEN_PAYLOAD_DEEP_SCAN_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r52.forbidden_payload_deep_scan.bodyfree.v1"
)

P7_R52_R2_STEP_REF: Final = "R52-2_r51_bodyfree_handoff_intake_contract"
P7_R52_R3_STEP_REF: Final = "R52-3_forbidden_payload_deep_scan"
P7_R52_R2_NEXT_REQUIRED_STEP_REF: Final = P7_R52_R3_STEP_REF
P7_R52_R2_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R52-2_r51_bodyfree_handoff_intake_contract"
P7_R52_R3_NEXT_REQUIRED_STEP_REF: Final = "R52-4_actual_review_evidence_completeness_checker"
P7_R52_R3_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R52-3_forbidden_payload_deep_scan_boundary_risk"

P7_R52_FUTURE_STEPS_AFTER_R3: Final[tuple[str, ...]] = P7_R52_FUTURE_STEPS_AFTER_R1[2:]
P7_R52_R2_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R52_IMPLEMENTED_STEPS,
    P7_R52_R2_STEP_REF,
)
P7_R52_R2_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R52_R3_STEP_REF,
    *P7_R52_FUTURE_STEPS_AFTER_R3,
)
P7_R52_R3_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R52_R2_IMPLEMENTED_STEPS,
    P7_R52_R3_STEP_REF,
)
P7_R52_R3_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R52_FUTURE_STEPS_AFTER_R3
P7_R52_CURRENT_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R52_R3_IMPLEMENTED_STEPS
P7_R52_CURRENT_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R52_R3_NOT_YET_IMPLEMENTED_STEPS

P7_R52_R51_REQUIRED_HANDOFF_COMPONENT_REFS: Final[tuple[str, ...]] = (
    "r16_body_free_post_review_summary",
    "r17_p5_confirmed_repair_return_inconclusive_decision",
    "r18_p6_limited_human_readfeel_candidate_handoff",
    "r19_p8_question_design_material_candidate_handoff",
    "r20_no_body_leak_no_question_text_no_touch_boundary_validation",
)
P7_R52_R51_REQUIRED_HANDOFF_SCHEMA_VERSION_BY_COMPONENT_REF: Final[dict[str, str]] = {
    "r16_body_free_post_review_summary": P7_R51_BODY_FREE_POST_REVIEW_SUMMARY_BUILDER_SCHEMA_VERSION,
    "r17_p5_confirmed_repair_return_inconclusive_decision": P7_R51_P5_CONFIRMED_REPAIR_RETURN_INCONCLUSIVE_DECISION_SCHEMA_VERSION,
    "r18_p6_limited_human_readfeel_candidate_handoff": P7_R51_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
    "r19_p8_question_design_material_candidate_handoff": P7_R51_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
    "r20_no_body_leak_no_question_text_no_touch_boundary_validation": P7_R51_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_BOUNDARY_VALIDATION_SCHEMA_VERSION,
}
P7_R52_R51_COMPONENT_REF_BY_SCHEMA_VERSION: Final[dict[str, str]] = {
    schema_version: component_ref
    for component_ref, schema_version in P7_R52_R51_REQUIRED_HANDOFF_SCHEMA_VERSION_BY_COMPONENT_REF.items()
}

P7_R52_R51_ALLOWED_BODYFREE_PAYLOAD_KIND_REFS: Final[tuple[str, ...]] = (
    "counts",
    "booleans",
    "enum_refs",
    "sanitized_reason_ids",
    "axis_averages",
    "case_counts",
    "blocker_counts",
    "question_primary_class_counts",
    "decision_refs",
)
P7_R52_R51_BODYFREE_HANDOFF_STATUS_REFS: Final[tuple[str, ...]] = (
    "R52_R51_BODYFREE_HANDOFF_INTAKE_ACCEPTED",
    "R52_BLOCKED_BY_R51_HANDOFF_COMPONENTS_MISSING",
    "R52_BLOCKED_BY_R51_VALIDATION_EVIDENCE_NOT_READY",
    "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK",
    "R52_BLOCKED_BY_R51_R20_BOUNDARY_NOT_VALIDATED",
)
P7_R52_FORBIDDEN_PAYLOAD_DEEP_SCAN_STATUS_REFS: Final[tuple[str, ...]] = (
    "R52_FORBIDDEN_PAYLOAD_DEEP_SCAN_PASSED",
    "R52_FORBIDDEN_PAYLOAD_DEEP_SCAN_BLOCKED_BY_BOUNDARY_RISK",
    "R52_FORBIDDEN_PAYLOAD_DEEP_SCAN_BLOCKED_BY_INTAKE_NOT_READY",
)

P7_R52_FORBIDDEN_PAYLOAD_KEY_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        (
            *P7_R51_NO_BODY_LEAK_FORBIDDEN_KEY_REFS,
            "raw_answer",
            "rawAnswer",
            "returned_emlis_surface",
            "returnedEmlisSurface",
            "current_input_review_surface",
            "currentInputReviewSurface",
            "bounded_owned_history_review_surface",
            "boundedOwnedHistoryReviewSurface",
            "local_absolute_path",
            "localAbsolutePath",
            "body_content_hash",
            "bodyContentHash",
            "packet_content_hash",
            "packetContentHash",
            "question_text",
            "questionText",
            "draft_question_text",
            "draftQuestionText",
            "question_body",
            "questionBody",
            "terminal_output",
            "stdout",
            "stderr",
            "traceback",
        )
    )
)
P7_R52_FORBIDDEN_TRUE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        (
            *P7_R51_NO_BODY_LEAK_FORBIDDEN_TRUE_FLAG_REFS,
            *P7_R51_NO_TOUCH_MUTATION_TRUE_FLAG_REFS,
            *P7_R52_R0_R1_FALSE_KEY_REFS,
            "api_db_rn_response_key_changed_here",
            "runtime_changed_here",
            "api_route_changed_here",
            "db_schema_changed_here",
            "db_migration_changed_here",
            "rn_visible_contract_changed_here",
            "public_response_top_level_key_added_here",
        )
    )
)
P7_R52_R51_REPORTED_ACTUAL_TRUE_FLAG_REFS: Final[tuple[str, ...]] = (
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_question_need_observation_summary_materialized_here",
    "actual_disposal_run_here",
    "actual_disposal_receipt_materialized_here",
    "post_review_summary_materialized_here",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_repair_return_candidate",
    "p5_review_inconclusive",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p8_question_design_material_candidate",
)
P7_R52_R51_REPORTED_ACTUAL_FLAG_PREFIX: Final = "r51_reported_"

P7_R52_R2_R3_EXTRA_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    "question_trigger_logic_implemented_here",
    "p8_question_detail_design_started_here",
    "r51_unprefixed_actual_report_flags_copied_to_output",
    "r51_bodyfree_material_body_stored_here",
    "r51_raw_material_payload_stored_here",
    "r52_copied_r51_bodyfree_materials_to_output",
)
P7_R52_R2_R3_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    *P7_R52_R0_R1_FALSE_KEY_REFS,
    *P7_R52_R2_R3_EXTRA_FALSE_KEY_REFS,
)

P7_R52_R51_BODYFREE_HANDOFF_INTAKE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "required_case_count",
    "r1_validation_schema_version",
    "r1_validation_material_ref",
    "r1_validation_evidence_ready_for_r52_2_intake",
    "r51_handoff_source_scope",
    "r51_handoff_source_step",
    "r51_required_handoff_component_refs",
    "r51_present_handoff_component_refs",
    "r51_missing_handoff_component_refs",
    "r51_handoff_material_refs",
    "r51_handoff_material_ref_count",
    "r51_bodyfree_material_count_scanned",
    "r51_r20_boundary_validation_status",
    "r51_next_required_step",
    "r51_body_free",
    "r51_allowed_bodyfree_payload_kind_refs",
    "r51_reported_actual_true_flag_refs_normalized",
    "r51_unprefixed_actual_report_true_flag_paths_detected",
    "r51_unprefixed_actual_report_flags_copied_to_output",
    "forbidden_payload_key_refs",
    "forbidden_true_flag_refs",
    "detected_forbidden_payload_key_paths",
    "detected_forbidden_true_flag_paths",
    "forbidden_payload_keys_absent",
    "forbidden_true_flags_absent",
    "body_free_boundary_passed",
    "r51_handoff_intake_status",
    "r51_handoff_intake_reason_refs",
    "r51_handoff_intake_ready_for_r52_3_deep_scan",
    "r52_0_current_received_snapshot_refrozen",
    "r52_1_validation_evidence_matrix_frozen",
    "r52_2_r51_bodyfree_handoff_intake_contract_built",
    "r52_3_forbidden_payload_deep_scan_built",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r52_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R52_R2_R3_FALSE_KEY_REFS,
)
P7_R52_FORBIDDEN_PAYLOAD_DEEP_SCAN_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "required_case_count",
    "r2_intake_schema_version",
    "r2_intake_material_ref",
    "r2_intake_status",
    "r2_intake_ready_for_r52_3_deep_scan",
    "scan_material_ref_count",
    "scan_material_count",
    "forbidden_payload_key_refs",
    "forbidden_true_flag_refs",
    "detected_forbidden_payload_key_paths",
    "detected_forbidden_true_flag_paths",
    "forbidden_payload_keys_absent",
    "forbidden_true_flags_absent",
    "body_free_boundary_passed",
    "boundary_risk_detected",
    "decision_ref",
    "decision_status",
    "decision_reason_refs",
    "r52_0_current_received_snapshot_refrozen",
    "r52_1_validation_evidence_matrix_frozen",
    "r52_2_r51_bodyfree_handoff_intake_contract_built",
    "r52_3_forbidden_payload_deep_scan_built",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r52_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R52_R2_R3_FALSE_KEY_REFS,
)


def _r52_find_forbidden_key_paths(
    value: Any,
    *,
    forbidden_keys: Sequence[str],
    path: str = "payload",
) -> list[str]:
    paths: list[str] = []
    forbidden = {str(key) for key in forbidden_keys}
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in forbidden:
                paths.append(child_path)
            paths.extend(_r52_find_forbidden_key_paths(child, forbidden_keys=forbidden_keys, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_r52_find_forbidden_key_paths(child, forbidden_keys=forbidden_keys, path=f"{path}[{index}]"))
    return paths


def _r52_find_forbidden_true_flag_paths(
    value: Any,
    *,
    forbidden_flags: Sequence[str],
    path: str = "payload",
) -> list[str]:
    paths: list[str] = []
    forbidden = {str(flag) for flag in forbidden_flags}
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in forbidden and child is True:
                paths.append(child_path)
            paths.extend(_r52_find_forbidden_true_flag_paths(child, forbidden_flags=forbidden_flags, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_r52_find_forbidden_true_flag_paths(child, forbidden_flags=forbidden_flags, path=f"{path}[{index}]"))
    return paths


def _r52_find_r51_reported_actual_true_flag_paths(value: Any, *, path: str = "r51_material") -> list[str]:
    paths: list[str] = []
    report_flags = set(P7_R52_R51_REPORTED_ACTUAL_TRUE_FLAG_REFS)
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in report_flags and child is True:
                paths.append(child_path)
            paths.extend(_r52_find_r51_reported_actual_true_flag_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_r52_find_r51_reported_actual_true_flag_paths(child, path=f"{path}[{index}]"))
    return paths


def _r52_normalized_r51_reported_actual_flag_refs(paths: Sequence[str]) -> list[str]:
    normalized: list[str] = []
    for path in paths:
        key = str(path).split(".")[-1]
        if key in P7_R52_R51_REPORTED_ACTUAL_TRUE_FLAG_REFS:
            normalized.append(f"{P7_R52_R51_REPORTED_ACTUAL_FLAG_PREFIX}{key}")
    return dedupe_identifiers(normalized, limit=80, max_length=180)


def _r52_component_ref_for_material(material: Mapping[str, Any]) -> str:
    explicit = clean_identifier(material.get("r51_handoff_component_ref"), max_length=140)
    if explicit in P7_R52_R51_REQUIRED_HANDOFF_COMPONENT_REFS:
        return explicit
    schema_version = clean_identifier(material.get("schema_version"), max_length=220)
    return P7_R52_R51_COMPONENT_REF_BY_SCHEMA_VERSION.get(schema_version, "")


def _r52_material_refs(materials: Sequence[Mapping[str, Any]]) -> list[str]:
    refs: list[str] = []
    for index, material in enumerate(materials):
        refs.append(
            clean_identifier(
                material.get("material_id"),
                default=f"r51_bodyfree_handoff_material_{index + 1}",
                max_length=180,
            )
        )
    return dedupe_identifiers(refs, limit=80, max_length=180)


def _r52_status_from_intake_scan(
    *,
    r1_ready: bool,
    missing_components: Sequence[str],
    r20_boundary_validation_status: str,
    forbidden_payload_key_paths: Sequence[str],
    forbidden_true_flag_paths: Sequence[str],
) -> tuple[str, list[str], bool, str]:
    reasons: list[str] = []
    if forbidden_payload_key_paths or forbidden_true_flag_paths:
        reasons.append("r51_bodyfree_handoff_material_contains_forbidden_payload_or_true_flag")
        return (
            "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK",
            reasons,
            False,
            P7_R52_R2_BLOCKED_NEXT_REQUIRED_STEP_REF,
        )
    if not r1_ready:
        reasons.append("r52_r1_validation_evidence_not_ready_for_r52_2_intake")
        return (
            "R52_BLOCKED_BY_R51_VALIDATION_EVIDENCE_NOT_READY",
            reasons,
            False,
            P7_R52_R2_BLOCKED_NEXT_REQUIRED_STEP_REF,
        )
    if missing_components:
        reasons.extend(f"missing_{ref}" for ref in missing_components)
        return (
            "R52_BLOCKED_BY_R51_HANDOFF_COMPONENTS_MISSING",
            reasons,
            False,
            P7_R52_R2_BLOCKED_NEXT_REQUIRED_STEP_REF,
        )
    if r20_boundary_validation_status != "R51_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_BOUNDARY_VALIDATED":
        reasons.append("r51_r20_boundary_validation_not_validated")
        return (
            "R52_BLOCKED_BY_R51_R20_BOUNDARY_NOT_VALIDATED",
            reasons,
            False,
            P7_R52_R2_BLOCKED_NEXT_REQUIRED_STEP_REF,
        )
    return (
        "R52_R51_BODYFREE_HANDOFF_INTAKE_ACCEPTED",
        ["r51_bodyfree_handoff_material_accepted_for_forbidden_payload_deep_scan"],
        True,
        P7_R52_R2_NEXT_REQUIRED_STEP_REF,
    )


def _r52_assert_false_keys(data: Mapping[str, Any], *, source: str) -> None:
    for false_key in P7_R52_R2_R3_FALSE_KEY_REFS:
        if data.get(false_key) is not False:
            raise ValueError(f"{source} must keep {false_key}=False")


def _r52_false_flags_r2_r3() -> dict[str, bool]:
    return {key: False for key in P7_R52_R2_R3_FALSE_KEY_REFS}


def _r52_material_sequence(value: Sequence[Mapping[str, Any]] | Sequence[Any] | None) -> list[dict[str, Any]]:
    if value is None:
        return []
    out: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, Mapping):
            out.append(safe_mapping(item))
    return out


def build_p7_r52_r51_bodyfree_handoff_intake(
    *,
    validation_evidence_matrix_freeze: Mapping[str, Any] | None = None,
    current_received_snapshot_refreeze: Mapping[str, Any] | None = None,
    r51_bodyfree_handoff_materials: Sequence[Mapping[str, Any]] | None = None,
    material_id: str = "p7_r52_r51_bodyfree_handoff_intake",
) -> dict[str, Any]:
    """Build the R52-2 body-free intake contract for R51 handoff material.

    The returned material never copies R51 raw materials into the R52 output.  It
    records only refs, component coverage, sanitized path ids for any boundary
    risk, and normalized ``r51_reported_*`` flag refs for R51-reported actual
    review facts.
    """

    r1 = (
        safe_mapping(validation_evidence_matrix_freeze)
        if validation_evidence_matrix_freeze is not None
        else build_p7_r52_validation_evidence_matrix_freeze(
            current_received_snapshot_refreeze=current_received_snapshot_refreeze
        )
    )
    assert_p7_r52_validation_evidence_matrix_freeze_contract(r1)
    materials = _r52_material_sequence(r51_bodyfree_handoff_materials)
    present_components = [
        component_ref
        for component_ref in (_r52_component_ref_for_material(material) for material in materials)
        if component_ref
    ]
    present_components = dedupe_identifiers(present_components, limit=20, max_length=160)
    missing_components = [
        component_ref
        for component_ref in P7_R52_R51_REQUIRED_HANDOFF_COMPONENT_REFS
        if component_ref not in set(present_components)
    ]
    r20_materials = [
        material
        for material in materials
        if _r52_component_ref_for_material(material) == "r20_no_body_leak_no_question_text_no_touch_boundary_validation"
    ]
    r20_status = clean_identifier(
        r20_materials[0].get("boundary_validation_status") if r20_materials else "",
        default="R51_BODY_FREE_BOUNDARY_NOT_READY",
        max_length=140,
    )
    if r20_status not in (*P7_R51_R20_BOUNDARY_STATUS_REFS, "R51_BODY_FREE_BOUNDARY_NOT_READY"):
        r20_status = "R51_BODY_FREE_BOUNDARY_NOT_READY"
    forbidden_key_paths = _r52_find_forbidden_key_paths(
        materials,
        forbidden_keys=P7_R52_FORBIDDEN_PAYLOAD_KEY_REFS,
        path="r51_bodyfree_handoff_materials",
    )
    forbidden_true_paths = _r52_find_forbidden_true_flag_paths(
        materials,
        forbidden_flags=P7_R52_FORBIDDEN_TRUE_FLAG_REFS,
        path="r51_bodyfree_handoff_materials",
    )
    reported_actual_paths = _r52_find_r51_reported_actual_true_flag_paths(
        materials,
        path="r51_bodyfree_handoff_materials",
    )
    normalized_reported_flags = _r52_normalized_r51_reported_actual_flag_refs(reported_actual_paths)
    r1_ready = bool(r1.get("validation_evidence_ready_for_r52_2_intake"))
    status, reasons, ready, next_step = _r52_status_from_intake_scan(
        r1_ready=r1_ready,
        missing_components=missing_components,
        r20_boundary_validation_status=r20_status,
        forbidden_payload_key_paths=forbidden_key_paths,
        forbidden_true_flag_paths=forbidden_true_paths,
    )
    intake = {
        "schema_version": P7_R52_R51_BODYFREE_HANDOFF_INTAKE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R52_STEP,
        "scope": P7_R52_SCOPE,
        "policy_kind": P7_R52_POLICY_KIND,
        "policy_section": P7_R52_R2_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r52_r51_bodyfree_handoff_intake", max_length=180),
        "review_session_id": clean_identifier(r1.get("review_session_id"), default=P7_R52_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "r1_validation_schema_version": P7_R52_VALIDATION_EVIDENCE_MATRIX_FREEZE_SCHEMA_VERSION,
        "r1_validation_material_ref": clean_identifier(r1.get("material_id"), default="p7_r52_validation_evidence_matrix_freeze", max_length=180),
        "r1_validation_evidence_ready_for_r52_2_intake": r1_ready,
        "r51_handoff_source_scope": P7_R51_SCOPE,
        "r51_handoff_source_step": P7_R51_STEP,
        "r51_required_handoff_component_refs": list(P7_R52_R51_REQUIRED_HANDOFF_COMPONENT_REFS),
        "r51_present_handoff_component_refs": present_components,
        "r51_missing_handoff_component_refs": missing_components,
        "r51_handoff_material_refs": _r52_material_refs(materials),
        "r51_handoff_material_ref_count": len(_r52_material_refs(materials)),
        "r51_bodyfree_material_count_scanned": len(materials),
        "r51_r20_boundary_validation_status": r20_status,
        "r51_next_required_step": clean_identifier(
            r20_materials[0].get("next_required_step") if r20_materials else "",
            default="R51_body_free_handoff_material_not_ready_for_R52_intake",
            max_length=220,
        ),
        "r51_body_free": not (forbidden_key_paths or forbidden_true_paths),
        "r51_allowed_bodyfree_payload_kind_refs": list(P7_R52_R51_ALLOWED_BODYFREE_PAYLOAD_KIND_REFS),
        "r51_reported_actual_true_flag_refs_normalized": normalized_reported_flags,
        "r51_unprefixed_actual_report_true_flag_paths_detected": dedupe_identifiers(reported_actual_paths, limit=80, max_length=240),
        "r51_unprefixed_actual_report_flags_copied_to_output": False,
        "forbidden_payload_key_refs": list(P7_R52_FORBIDDEN_PAYLOAD_KEY_REFS),
        "forbidden_true_flag_refs": list(P7_R52_FORBIDDEN_TRUE_FLAG_REFS),
        "detected_forbidden_payload_key_paths": dedupe_identifiers(forbidden_key_paths, limit=80, max_length=240),
        "detected_forbidden_true_flag_paths": dedupe_identifiers(forbidden_true_paths, limit=80, max_length=240),
        "forbidden_payload_keys_absent": not bool(forbidden_key_paths),
        "forbidden_true_flags_absent": not bool(forbidden_true_paths),
        "body_free_boundary_passed": not (forbidden_key_paths or forbidden_true_paths),
        "r51_handoff_intake_status": status,
        "r51_handoff_intake_reason_refs": reasons,
        "r51_handoff_intake_ready_for_r52_3_deep_scan": ready,
        "r52_0_current_received_snapshot_refrozen": True,
        "r52_1_validation_evidence_matrix_frozen": True,
        "r52_2_r51_bodyfree_handoff_intake_contract_built": True,
        "r52_3_forbidden_payload_deep_scan_built": False,
        "implemented_steps": list(P7_R52_R2_IMPLEMENTED_STEPS if ready else P7_R52_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R52_R2_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R52_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R52_FIRST_NEXT_WORK_REF,
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "r52_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_r52_false_flags_r2_r3(),
    }
    assert_p7_r52_r51_bodyfree_handoff_intake_contract(intake)
    return intake


def assert_p7_r52_r51_bodyfree_handoff_intake_contract(intake: Mapping[str, Any]) -> bool:
    data = safe_mapping(intake)
    _assert_required_fields(
        data,
        required=P7_R52_R51_BODYFREE_HANDOFF_INTAKE_REQUIRED_FIELD_REFS,
        source="p7_r52_r2_r51_bodyfree_handoff_intake",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R52_R51_BODYFREE_HANDOFF_INTAKE_SCHEMA_VERSION,
        source="p7_r52_r2_r51_bodyfree_handoff_intake",
    )
    _r52_assert_false_keys(data, source="p7_r52_r2_r51_bodyfree_handoff_intake")
    if data.get("policy_section") != P7_R52_R2_STEP_REF:
        raise ValueError("R52 R2 policy section changed")
    if data.get("r1_validation_schema_version") != P7_R52_VALIDATION_EVIDENCE_MATRIX_FREEZE_SCHEMA_VERSION:
        raise ValueError("R52 R2 must intake R52-1 validation evidence freeze")
    if data.get("r51_handoff_source_scope") != P7_R51_SCOPE or data.get("r51_handoff_source_step") != P7_R51_STEP:
        raise ValueError("R52 R2 R51 source refs changed")
    if tuple(data.get("r51_required_handoff_component_refs") or ()) != P7_R52_R51_REQUIRED_HANDOFF_COMPONENT_REFS:
        raise ValueError("R52 R2 required R51 handoff components changed")
    present = set(dedupe_identifiers(data.get("r51_present_handoff_component_refs") or [], limit=20, max_length=160))
    missing = [component for component in P7_R52_R51_REQUIRED_HANDOFF_COMPONENT_REFS if component not in present]
    if tuple(data.get("r51_missing_handoff_component_refs") or ()) != tuple(missing):
        raise ValueError("R52 R2 missing component refs do not match present component refs")
    if data.get("r51_r20_boundary_validation_status") not in (*P7_R51_R20_BOUNDARY_STATUS_REFS, "R51_BODY_FREE_BOUNDARY_NOT_READY"):
        raise ValueError("R52 R2 R51 R20 boundary validation status changed")
    payload_absent = not bool(data.get("detected_forbidden_payload_key_paths"))
    true_flags_absent = not bool(data.get("detected_forbidden_true_flag_paths"))
    boundary_passed = payload_absent and true_flags_absent
    if data.get("forbidden_payload_keys_absent") is not payload_absent:
        raise ValueError("R52 R2 forbidden_payload_keys_absent does not match detected forbidden paths")
    if data.get("forbidden_true_flags_absent") is not true_flags_absent:
        raise ValueError("R52 R2 forbidden_true_flags_absent does not match detected forbidden paths")
    if data.get("body_free_boundary_passed") is not boundary_passed:
        raise ValueError("R52 R2 body_free_boundary_passed does not match detected forbidden paths")
    if tuple(data.get("forbidden_payload_key_refs") or ()) != P7_R52_FORBIDDEN_PAYLOAD_KEY_REFS:
        raise ValueError("R52 R2 forbidden payload key refs changed")
    if tuple(data.get("forbidden_true_flag_refs") or ()) != P7_R52_FORBIDDEN_TRUE_FLAG_REFS:
        raise ValueError("R52 R2 forbidden true flag refs changed")
    status = data.get("r51_handoff_intake_status")
    if status not in P7_R52_R51_BODYFREE_HANDOFF_STATUS_REFS:
        raise ValueError("R52 R2 intake status changed")
    if status == "R52_R51_BODYFREE_HANDOFF_INTAKE_ACCEPTED":
        if data.get("r1_validation_evidence_ready_for_r52_2_intake") is not True:
            raise ValueError("R52 R2 accepted intake requires ready R52-1 evidence")
        if missing:
            raise ValueError("R52 R2 accepted intake cannot have missing R51 components")
        if data.get("r51_r20_boundary_validation_status") != "R51_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_BOUNDARY_VALIDATED":
            raise ValueError("R52 R2 accepted intake requires R51 R20 boundary validated")
        if data.get("r51_next_required_step") != P7_R51_R20_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R52 R2 accepted intake requires R51 next step to be body-free handoff ready")
        if data.get("r51_handoff_intake_ready_for_r52_3_deep_scan") is not True:
            raise ValueError("R52 R2 accepted intake must be ready for R52-3")
        if data.get("next_required_step") != P7_R52_R2_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R52 R2 accepted intake must point to R52-3")
        if tuple(data.get("implemented_steps") or ()) != P7_R52_R2_IMPLEMENTED_STEPS:
            raise ValueError("R52 R2 accepted implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R52_R2_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R52 R2 accepted not-yet steps changed")
    else:
        if data.get("r51_handoff_intake_ready_for_r52_3_deep_scan") is not False:
            raise ValueError("R52 R2 blocked intake must not be ready for R52-3")
        if not data.get("r51_handoff_intake_reason_refs"):
            raise ValueError("R52 R2 blocked intake must explain reason refs")
        if data.get("next_required_step") != P7_R52_R2_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R52 R2 blocked intake must point to R52-2 resolution")
    if data.get("r52_2_r51_bodyfree_handoff_intake_contract_built") is not True:
        raise ValueError("R52 R2 must mark intake contract built")
    if data.get("r52_3_forbidden_payload_deep_scan_built") is not False:
        raise ValueError("R52 R2 must not mark R52-3 built")
    if data.get("p6_limited_human_readfeel_start_allowed") is not False or data.get("p8_start_allowed") is not False:
        raise ValueError("R52 R2 must not start P6/P8")
    if data.get("p7_complete") is not False or data.get("release_allowed") is not False:
        raise ValueError("R52 R2 must not complete P7 or allow release")
    return True


def build_p7_r52_forbidden_payload_deep_scan(
    *,
    r51_bodyfree_handoff_intake: Mapping[str, Any] | None = None,
    validation_evidence_matrix_freeze: Mapping[str, Any] | None = None,
    current_received_snapshot_refreeze: Mapping[str, Any] | None = None,
    r51_bodyfree_handoff_materials: Sequence[Mapping[str, Any]] | None = None,
    material_id: str = "p7_r52_forbidden_payload_deep_scan",
) -> dict[str, Any]:
    """Build R52-3, the recursive forbidden payload/no-touch scan summary."""

    intake = (
        safe_mapping(r51_bodyfree_handoff_intake)
        if r51_bodyfree_handoff_intake is not None
        else build_p7_r52_r51_bodyfree_handoff_intake(
            validation_evidence_matrix_freeze=validation_evidence_matrix_freeze,
            current_received_snapshot_refreeze=current_received_snapshot_refreeze,
            r51_bodyfree_handoff_materials=r51_bodyfree_handoff_materials,
        )
    )
    assert_p7_r52_r51_bodyfree_handoff_intake_contract(intake)
    forbidden_key_paths = list(intake.get("detected_forbidden_payload_key_paths") or [])
    forbidden_true_paths = list(intake.get("detected_forbidden_true_flag_paths") or [])
    boundary_risk = bool(forbidden_key_paths or forbidden_true_paths)
    intake_ready = bool(intake.get("r51_handoff_intake_ready_for_r52_3_deep_scan"))
    if boundary_risk:
        scan_status = "R52_FORBIDDEN_PAYLOAD_DEEP_SCAN_BLOCKED_BY_BOUNDARY_RISK"
        decision_ref = "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK"
        decision_status = "BLOCKED"
        reasons = ["r51_bodyfree_handoff_material_contains_forbidden_payload_or_true_flag"]
        next_step = P7_R52_R3_BLOCKED_NEXT_REQUIRED_STEP_REF
        implemented_steps = P7_R52_R2_IMPLEMENTED_STEPS
        not_yet_steps = P7_R52_R2_NOT_YET_IMPLEMENTED_STEPS
    elif not intake_ready:
        scan_status = "R52_FORBIDDEN_PAYLOAD_DEEP_SCAN_BLOCKED_BY_INTAKE_NOT_READY"
        decision_ref = "R52_RETURN_TO_R51_BODYFREE_HANDOFF_INTAKE_REQUIRED"
        decision_status = "RETURN_REQUIRED"
        reasons = list(intake.get("r51_handoff_intake_reason_refs") or ["r51_bodyfree_handoff_intake_not_ready"])
        next_step = P7_R52_R2_BLOCKED_NEXT_REQUIRED_STEP_REF
        implemented_steps = P7_R52_R2_IMPLEMENTED_STEPS
        not_yet_steps = P7_R52_R2_NOT_YET_IMPLEMENTED_STEPS
    else:
        scan_status = "R52_FORBIDDEN_PAYLOAD_DEEP_SCAN_PASSED"
        decision_ref = "R52_R51_BODYFREE_HANDOFF_ACCEPTED_FOR_ACTUAL_REVIEW_EVIDENCE_CHECK"
        decision_status = "CANDIDATE_ONLY"
        reasons = ["r51_bodyfree_handoff_material_contains_no_forbidden_payload_or_true_flag"]
        next_step = P7_R52_R3_NEXT_REQUIRED_STEP_REF
        implemented_steps = P7_R52_R3_IMPLEMENTED_STEPS
        not_yet_steps = P7_R52_R3_NOT_YET_IMPLEMENTED_STEPS
    scan = {
        "schema_version": P7_R52_FORBIDDEN_PAYLOAD_DEEP_SCAN_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R52_STEP,
        "scope": P7_R52_SCOPE,
        "policy_kind": P7_R52_POLICY_KIND,
        "policy_section": P7_R52_R3_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r52_forbidden_payload_deep_scan", max_length=180),
        "review_session_id": clean_identifier(intake.get("review_session_id"), default=P7_R52_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "r2_intake_schema_version": P7_R52_R51_BODYFREE_HANDOFF_INTAKE_SCHEMA_VERSION,
        "r2_intake_material_ref": clean_identifier(intake.get("material_id"), default="p7_r52_r51_bodyfree_handoff_intake", max_length=180),
        "r2_intake_status": clean_identifier(intake.get("r51_handoff_intake_status"), default="R52_BLOCKED_BY_R51_HANDOFF_COMPONENTS_MISSING", max_length=140),
        "r2_intake_ready_for_r52_3_deep_scan": intake_ready,
        "scan_material_ref_count": _safe_non_negative_int(intake.get("r51_handoff_material_ref_count")),
        "scan_material_count": _safe_non_negative_int(intake.get("r51_bodyfree_material_count_scanned")),
        "forbidden_payload_key_refs": list(P7_R52_FORBIDDEN_PAYLOAD_KEY_REFS),
        "forbidden_true_flag_refs": list(P7_R52_FORBIDDEN_TRUE_FLAG_REFS),
        "detected_forbidden_payload_key_paths": dedupe_identifiers(forbidden_key_paths, limit=80, max_length=240),
        "detected_forbidden_true_flag_paths": dedupe_identifiers(forbidden_true_paths, limit=80, max_length=240),
        "forbidden_payload_keys_absent": not bool(forbidden_key_paths),
        "forbidden_true_flags_absent": not bool(forbidden_true_paths),
        "body_free_boundary_passed": not boundary_risk,
        "boundary_risk_detected": boundary_risk,
        "decision_ref": decision_ref,
        "decision_status": decision_status,
        "decision_reason_refs": reasons,
        "r52_0_current_received_snapshot_refrozen": True,
        "r52_1_validation_evidence_matrix_frozen": True,
        "r52_2_r51_bodyfree_handoff_intake_contract_built": True,
        "r52_3_forbidden_payload_deep_scan_built": not boundary_risk,
        "implemented_steps": list(implemented_steps),
        "not_yet_implemented_steps": list(not_yet_steps),
        "first_next_work_ref": P7_R52_FIRST_NEXT_WORK_REF,
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "r52_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_r52_false_flags_r2_r3(),
    }
    assert_p7_r52_forbidden_payload_deep_scan_contract(scan)
    return scan


def assert_p7_r52_forbidden_payload_deep_scan_contract(scan: Mapping[str, Any]) -> bool:
    data = safe_mapping(scan)
    _assert_required_fields(
        data,
        required=P7_R52_FORBIDDEN_PAYLOAD_DEEP_SCAN_REQUIRED_FIELD_REFS,
        source="p7_r52_r3_forbidden_payload_deep_scan",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R52_FORBIDDEN_PAYLOAD_DEEP_SCAN_SCHEMA_VERSION,
        source="p7_r52_r3_forbidden_payload_deep_scan",
    )
    _r52_assert_false_keys(data, source="p7_r52_r3_forbidden_payload_deep_scan")
    if data.get("policy_section") != P7_R52_R3_STEP_REF:
        raise ValueError("R52 R3 policy section changed")
    if data.get("r2_intake_schema_version") != P7_R52_R51_BODYFREE_HANDOFF_INTAKE_SCHEMA_VERSION:
        raise ValueError("R52 R3 must scan R52-2 intake material")
    if data.get("decision_ref") in {
        "R52_RELEASE_ALLOWED",
        "R52_P7_COMPLETE",
        "R52_P8_START_ALLOWED",
        "R52_P6_START_ALLOWED",
        "R52_P5_CONFIRMED_FINAL",
        "R52_QUESTION_IMPLEMENTATION_ALLOWED",
        "R52_API_DB_RN_CHANGE_ALLOWED",
    }:
        raise ValueError("R52 R3 must not produce auto-allow decision refs")
    if tuple(data.get("forbidden_payload_key_refs") or ()) != P7_R52_FORBIDDEN_PAYLOAD_KEY_REFS:
        raise ValueError("R52 R3 forbidden payload key refs changed")
    if tuple(data.get("forbidden_true_flag_refs") or ()) != P7_R52_FORBIDDEN_TRUE_FLAG_REFS:
        raise ValueError("R52 R3 forbidden true flag refs changed")
    boundary_risk = bool(data.get("detected_forbidden_payload_key_paths") or data.get("detected_forbidden_true_flag_paths"))
    if data.get("boundary_risk_detected") is not boundary_risk:
        raise ValueError("R52 R3 boundary risk does not match detected forbidden paths")
    if data.get("forbidden_payload_keys_absent") is not (not bool(data.get("detected_forbidden_payload_key_paths"))):
        raise ValueError("R52 R3 payload key absence does not match detected paths")
    if data.get("forbidden_true_flags_absent") is not (not bool(data.get("detected_forbidden_true_flag_paths"))):
        raise ValueError("R52 R3 true flag absence does not match detected paths")
    if data.get("body_free_boundary_passed") is not (not boundary_risk):
        raise ValueError("R52 R3 body-free boundary flag does not match detected paths")
    if data.get("r2_intake_ready_for_r52_3_deep_scan") is True and not boundary_risk:
        if data.get("decision_ref") != "R52_R51_BODYFREE_HANDOFF_ACCEPTED_FOR_ACTUAL_REVIEW_EVIDENCE_CHECK":
            raise ValueError("R52 R3 passed scan must point to actual review evidence check only")
        if data.get("decision_status") != "CANDIDATE_ONLY":
            raise ValueError("R52 R3 passed scan must remain candidate-only")
        if data.get("next_required_step") != P7_R52_R3_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R52 R3 passed scan must point to R52-4")
        if data.get("r52_3_forbidden_payload_deep_scan_built") is not True:
            raise ValueError("R52 R3 passed scan must mark R52-3 built")
        if tuple(data.get("implemented_steps") or ()) != P7_R52_R3_IMPLEMENTED_STEPS:
            raise ValueError("R52 R3 passed implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R52_R3_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R52 R3 passed not-yet steps changed")
    elif boundary_risk:
        if data.get("decision_ref") != "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK":
            raise ValueError("R52 R3 boundary risk must use R51 body-free boundary risk decision")
        if data.get("decision_status") != "BLOCKED":
            raise ValueError("R52 R3 boundary risk must be blocked")
        if data.get("next_required_step") != P7_R52_R3_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R52 R3 boundary risk must point to deep-scan resolution")
        if data.get("r52_3_forbidden_payload_deep_scan_built") is not False:
            raise ValueError("R52 R3 blocked risk must not mark R52-3 built")
    else:
        if data.get("decision_ref") != "R52_RETURN_TO_R51_BODYFREE_HANDOFF_INTAKE_REQUIRED":
            raise ValueError("R52 R3 intake-not-ready must return to intake")
        if data.get("decision_status") != "RETURN_REQUIRED":
            raise ValueError("R52 R3 intake-not-ready must be return-required")
        if data.get("next_required_step") != P7_R52_R2_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R52 R3 intake-not-ready must point to R52-2 resolution")
    if data.get("p6_limited_human_readfeel_start_allowed") is not False or data.get("p8_start_allowed") is not False:
        raise ValueError("R52 R3 must not start P6/P8")
    if data.get("p7_complete") is not False or data.get("release_allowed") is not False:
        raise ValueError("R52 R3 must not complete P7 or allow release")
    return True


def build_p7_r52_r0_r3_r51_bodyfree_intake_forbidden_scan_chain(
    *,
    current_received_snapshot_refreeze: Mapping[str, Any] | None = None,
    validation_evidence_matrix_freeze: Mapping[str, Any] | None = None,
    r51_bodyfree_handoff_materials: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return R52-3 material after validating the R52-0/R52-3 chain."""

    r0 = (
        safe_mapping(current_received_snapshot_refreeze)
        if current_received_snapshot_refreeze is not None
        else build_p7_r52_current_received_snapshot_refreeze()
    )
    assert_p7_r52_current_received_snapshot_refreeze_contract(r0)
    r1 = (
        safe_mapping(validation_evidence_matrix_freeze)
        if validation_evidence_matrix_freeze is not None
        else build_p7_r52_validation_evidence_matrix_freeze(current_received_snapshot_refreeze=r0)
    )
    assert_p7_r52_validation_evidence_matrix_freeze_contract(r1)
    r2 = build_p7_r52_r51_bodyfree_handoff_intake(
        validation_evidence_matrix_freeze=r1,
        r51_bodyfree_handoff_materials=r51_bodyfree_handoff_materials,
    )
    assert_p7_r52_r51_bodyfree_handoff_intake_contract(r2)
    r3 = build_p7_r52_forbidden_payload_deep_scan(r51_bodyfree_handoff_intake=r2)
    assert_p7_r52_forbidden_payload_deep_scan_contract(r3)
    return r3


# ---------------------------------------------------------------------------
# R52-4 / R52-5: actual review evidence completeness + missing-evidence NO_GO.
# ---------------------------------------------------------------------------

P7_R52_ACTUAL_REVIEW_EVIDENCE_COMPLETENESS_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r52.actual_review_evidence_completeness.bodyfree.v1"
)
P7_R52_EVIDENCE_MISSING_NO_GO_BRANCH_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r52.evidence_missing_no_go_branch.bodyfree.v1"
)

P7_R52_R4_STEP_REF: Final = "R52-4_actual_review_evidence_completeness_checker"
P7_R52_R5_STEP_REF: Final = "R52-5_evidence_missing_no_go_branch"
P7_R52_R4_NEXT_REQUIRED_STEP_REF: Final = P7_R52_R5_STEP_REF
P7_R52_R4_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R52-4_actual_review_evidence_body_free_boundary"
P7_R52_R5_RETURN_TO_R51_NEXT_REQUIRED_STEP_REF: Final = (
    "R51_actual_local_only_human_review_required_with_explicit_allow_local_root_purge_plan"
)
P7_R52_R5_NEXT_REQUIRED_STEP_REF: Final = "R52-6_disposal_safety_gate"

P7_R52_FUTURE_STEPS_AFTER_R5: Final[tuple[str, ...]] = P7_R52_FUTURE_STEPS_AFTER_R1[4:]
P7_R52_R4_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R52_R3_IMPLEMENTED_STEPS,
    P7_R52_R4_STEP_REF,
)
P7_R52_R4_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R52_R5_STEP_REF,
    *P7_R52_FUTURE_STEPS_AFTER_R5,
)
P7_R52_R5_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R52_R4_IMPLEMENTED_STEPS,
    P7_R52_R5_STEP_REF,
)
P7_R52_R5_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R52_FUTURE_STEPS_AFTER_R5
P7_R52_CURRENT_IMPLEMENTED_STEPS = P7_R52_R5_IMPLEMENTED_STEPS
P7_R52_CURRENT_NOT_YET_IMPLEMENTED_STEPS = P7_R52_R5_NOT_YET_IMPLEMENTED_STEPS

P7_R52_ACCEPTABLE_REVIEW_SESSION_STATUS_REFS: Final[tuple[str, ...]] = (
    "R51_ACTUAL_REVIEW_COMPLETED",
    "R51_POST_REVIEW_SUMMARY_READY",
)
P7_R52_KNOWN_REVIEW_SESSION_STATUS_REFS: Final[tuple[str, ...]] = (
    *P7_R52_ACCEPTABLE_REVIEW_SESSION_STATUS_REFS,
    "R51_ACTUAL_REVIEW_NOT_RUN",
    "R51_ACTUAL_REVIEW_EVIDENCE_MISSING",
    "R51_ACTUAL_REVIEW_INCOMPLETE",
)
P7_R52_ACTUAL_REVIEW_EVIDENCE_COMPLETENESS_STATUS_REFS: Final[tuple[str, ...]] = (
    "R52_R51_ACTUAL_REVIEW_EVIDENCE_COMPLETE",
    "R52_R51_ACTUAL_REVIEW_EVIDENCE_MISSING",
    "R52_R51_ACTUAL_REVIEW_EVIDENCE_BLOCKED_BY_R3",
    "R52_R51_ACTUAL_REVIEW_EVIDENCE_BLOCKED_BY_BODY_FREE_BOUNDARY_RISK",
)
P7_R52_P5_DECISION_STATUS_REFS: Final[tuple[str, ...]] = (
    "R52_P5_NOT_REVIEWED_EVIDENCE_MISSING",
    "R52_P5_CONFIRMED_CANDIDATE_REVIEWED_NOT_FINAL",
    "R52_P5_REPAIR_REQUIRED",
    "R52_P5_INCONCLUSIVE_REVIEW_REQUIRED",
    "R52_P5_BLOCKED_BY_BOUNDARY_RISK",
    "R52_P5_BLOCKED_BY_DISPOSAL_NOT_VERIFIED",
    "R52_P5_BLOCKED_BY_EXECUTION_BLOCKER",
    "R52_P5_BLOCKED_BY_CONSISTENCY_ISSUE",
)
P7_R52_R5_DECISION_REF_REFS: Final[tuple[str, ...]] = (
    "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED",
    "R52_BLOCKED_BY_R51_EVIDENCE_MISSING",
    "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK",
    "R52_NO_GO_P6_P8_START",
)
P7_R52_R5_DECISION_STATUS_REFS: Final[tuple[str, ...]] = (
    "NO_GO",
    "BLOCKED",
    "RETURN_REQUIRED",
    "CANDIDATE_ONLY",
    "INCONCLUSIVE",
)

P7_R52_R4_R5_EXTRA_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    "r51_target_green_claimed_as_actual_review_complete",
    "r51_helper_ready_claimed_as_actual_review_complete",
    "r51_actual_review_evidence_created_here",
    "r51_actual_review_evidence_body_stored_here",
    "r51_bodyfull_packet_opened_here",
    "rating_rows_created_here",
    "question_observation_rows_created_here",
    "disposal_receipt_created_here",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p8_question_design_material_candidate",
)
P7_R52_R4_R5_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    *P7_R52_R2_R3_FALSE_KEY_REFS,
    *P7_R52_R4_R5_EXTRA_FALSE_KEY_REFS,
)

P7_R52_ACTUAL_REVIEW_EVIDENCE_COMPLETENESS_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "required_case_count",
    "r3_scan_schema_version",
    "r3_scan_material_ref",
    "r3_scan_decision_ref",
    "r3_scan_decision_status",
    "r3_scan_ready_for_r52_4_evidence_check",
    "r3_body_free_boundary_passed",
    "review_session_status",
    "acceptable_review_session_status_refs",
    "rating_row_count",
    "question_observation_row_count",
    "r8_actual_human_review_run_recorded",
    "r9_rating_row_normalizer_built",
    "r10_readfeel_blocker_execution_blocker_ingestion_built",
    "r11_question_need_observation_row_normalizer_built",
    "r12_rating_question_observation_consistency_guard_built",
    "r14_body_full_packet_reviewer_notes_purge_built",
    "r15_disposal_receipt_builder_verifier_built",
    "r16_body_free_post_review_summary_builder_built",
    "r17_p5_confirmed_repair_return_inconclusive_decision_built",
    "r20_no_body_leak_no_question_text_no_touch_boundary_validation_built",
    "disposal_verified",
    "body_removed",
    "reviewer_notes_removed",
    "local_packet_exported",
    "content_hash_of_body_stored",
    "open_execution_blocker_count",
    "r51_actual_review_evidence_input_body_free",
    "forbidden_payload_key_refs",
    "forbidden_true_flag_refs",
    "detected_forbidden_payload_key_paths",
    "detected_forbidden_true_flag_paths",
    "forbidden_payload_keys_absent",
    "forbidden_true_flags_absent",
    "body_free_boundary_passed",
    "r51_actual_review_evidence_complete",
    "missing_evidence_refs",
    "missing_evidence_count",
    "r51_actual_review_evidence_completeness_status",
    "r52_0_current_received_snapshot_refrozen",
    "r52_1_validation_evidence_matrix_frozen",
    "r52_2_r51_bodyfree_handoff_intake_contract_built",
    "r52_3_forbidden_payload_deep_scan_built",
    "r52_4_actual_review_evidence_completeness_checker_built",
    "r52_5_evidence_missing_no_go_branch_built",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r52_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R52_R4_R5_FALSE_KEY_REFS,
)
P7_R52_EVIDENCE_MISSING_NO_GO_BRANCH_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "required_case_count",
    "r4_completeness_schema_version",
    "r4_completeness_material_ref",
    "r4_completeness_status",
    "r4_completeness_checker_built",
    "r51_actual_review_evidence_complete",
    "missing_evidence_refs",
    "missing_evidence_count",
    "body_free_boundary_passed",
    "boundary_risk_detected",
    "decision_ref",
    "decision_status",
    "decision_reason_refs",
    "next_required_step",
    "p5_decision_status",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "p8_question_design_material_candidate",
    "p8_start_allowed",
    "p7_complete",
    "release_allowed",
    "r52_0_current_received_snapshot_refrozen",
    "r52_1_validation_evidence_matrix_frozen",
    "r52_2_r51_bodyfree_handoff_intake_contract_built",
    "r52_3_forbidden_payload_deep_scan_built",
    "r52_4_actual_review_evidence_completeness_checker_built",
    "r52_5_evidence_missing_no_go_branch_built",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "public_contract",
    "r52_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R52_R4_R5_FALSE_KEY_REFS,
)


def _r52_false_flags_r4_r5() -> dict[str, bool]:
    return {key: False for key in P7_R52_R4_R5_FALSE_KEY_REFS}


def _r52_evidence_bool(evidence: Mapping[str, Any], *keys: str, default: bool = False) -> bool:
    for key in keys:
        if key in evidence:
            return _safe_bool(evidence.get(key), default=default)
    return default


def _r52_evidence_int(evidence: Mapping[str, Any], *keys: str) -> int:
    for key in keys:
        if key in evidence:
            return _safe_non_negative_int(evidence.get(key))
    return 0


def _r52_actual_review_evidence_values(r51_actual_review_evidence: Mapping[str, Any] | None) -> dict[str, Any]:
    evidence = safe_mapping(r51_actual_review_evidence)
    status = clean_identifier(
        evidence.get("review_session_status"),
        default="R51_ACTUAL_REVIEW_EVIDENCE_MISSING",
        max_length=140,
    )
    if status not in P7_R52_KNOWN_REVIEW_SESSION_STATUS_REFS:
        status = "R51_ACTUAL_REVIEW_INCOMPLETE"
    return {
        "review_session_status": status,
        "rating_row_count": _r52_evidence_int(evidence, "rating_row_count", "r51_rating_row_count"),
        "question_observation_row_count": _r52_evidence_int(
            evidence,
            "question_observation_row_count",
            "question_need_observation_row_count",
            "r51_question_observation_row_count",
        ),
        "r8_actual_human_review_run_recorded": _r52_evidence_bool(
            evidence,
            "r8_actual_human_review_run_recorded",
            "r51_actual_human_review_run_recorded",
            "actual_human_review_run_recorded",
        ),
        "r9_rating_row_normalizer_built": _r52_evidence_bool(evidence, "r9_rating_row_normalizer_built"),
        "r10_readfeel_blocker_execution_blocker_ingestion_built": _r52_evidence_bool(
            evidence, "r10_readfeel_blocker_execution_blocker_ingestion_built"
        ),
        "r11_question_need_observation_row_normalizer_built": _r52_evidence_bool(
            evidence, "r11_question_need_observation_row_normalizer_built"
        ),
        "r12_rating_question_observation_consistency_guard_built": _r52_evidence_bool(
            evidence, "r12_rating_question_observation_consistency_guard_built"
        ),
        "r14_body_full_packet_reviewer_notes_purge_built": _r52_evidence_bool(
            evidence, "r14_body_full_packet_reviewer_notes_purge_built"
        ),
        "r15_disposal_receipt_builder_verifier_built": _r52_evidence_bool(
            evidence, "r15_disposal_receipt_builder_verifier_built"
        ),
        "r16_body_free_post_review_summary_builder_built": _r52_evidence_bool(
            evidence, "r16_body_free_post_review_summary_builder_built"
        ),
        "r17_p5_confirmed_repair_return_inconclusive_decision_built": _r52_evidence_bool(
            evidence, "r17_p5_confirmed_repair_return_inconclusive_decision_built"
        ),
        "r20_no_body_leak_no_question_text_no_touch_boundary_validation_built": _r52_evidence_bool(
            evidence, "r20_no_body_leak_no_question_text_no_touch_boundary_validation_built"
        ),
        "disposal_verified": _r52_evidence_bool(evidence, "disposal_verified"),
        "body_removed": _r52_evidence_bool(evidence, "body_removed"),
        "reviewer_notes_removed": _r52_evidence_bool(evidence, "reviewer_notes_removed"),
        "local_packet_exported": _r52_evidence_bool(evidence, "local_packet_exported"),
        "content_hash_of_body_stored": _r52_evidence_bool(evidence, "content_hash_of_body_stored"),
        "open_execution_blocker_count": _r52_evidence_int(evidence, "open_execution_blocker_count"),
        "r51_actual_review_evidence_input_body_free": _r52_evidence_bool(evidence, "body_free"),
    }


def _r52_missing_actual_review_evidence_refs(values: Mapping[str, Any]) -> list[str]:
    missing: list[str] = []
    if values.get("review_session_status") not in P7_R52_ACCEPTABLE_REVIEW_SESSION_STATUS_REFS:
        missing.append("r51_review_session_status_not_completed")
    if values.get("r8_actual_human_review_run_recorded") is not True:
        missing.append("r51_actual_human_review_run_missing")
    if _safe_non_negative_int(values.get("rating_row_count")) < P7_R51_REQUIRED_CASE_COUNT:
        missing.append("r51_rating_rows_missing")
    if _safe_non_negative_int(values.get("question_observation_row_count")) < P7_R51_REQUIRED_CASE_COUNT:
        missing.append("r51_question_need_observation_rows_missing")
    build_flag_missing_ref_by_key = {
        "r9_rating_row_normalizer_built": "r51_rating_row_normalizer_missing",
        "r10_readfeel_blocker_execution_blocker_ingestion_built": "r51_readfeel_blocker_execution_blocker_ingestion_missing",
        "r11_question_need_observation_row_normalizer_built": "r51_question_need_observation_row_normalizer_missing",
        "r12_rating_question_observation_consistency_guard_built": "r51_rating_question_observation_consistency_guard_missing",
        "r14_body_full_packet_reviewer_notes_purge_built": "r51_body_full_packet_reviewer_notes_purge_missing",
        "r15_disposal_receipt_builder_verifier_built": "r51_disposal_receipt_missing",
        "r16_body_free_post_review_summary_builder_built": "r51_post_review_summary_missing",
        "r17_p5_confirmed_repair_return_inconclusive_decision_built": "r51_p5_decision_missing",
        "r20_no_body_leak_no_question_text_no_touch_boundary_validation_built": "r51_r20_boundary_validation_missing",
    }
    for key, missing_ref in build_flag_missing_ref_by_key.items():
        if values.get(key) is not True:
            missing.append(missing_ref)
    if values.get("disposal_verified") is not True:
        missing.append("r51_disposal_verified_missing")
        missing.append("r51_disposal_receipt_missing")
    if values.get("body_removed") is not True:
        missing.append("r51_body_removed_missing")
    if values.get("reviewer_notes_removed") is not True:
        missing.append("r51_reviewer_notes_removed_missing")
    if values.get("local_packet_exported") is not False:
        missing.append("r51_local_packet_export_deny_missing")
    if values.get("content_hash_of_body_stored") is not False:
        missing.append("r51_body_content_hash_storage_deny_missing")
    if _safe_non_negative_int(values.get("open_execution_blocker_count")) > 0:
        missing.append("r51_execution_blocker_open")
    if values.get("r51_actual_review_evidence_input_body_free") is not True:
        missing.append("r51_actual_review_evidence_bodyfree_marker_missing")
    return dedupe_identifiers(missing, limit=120, max_length=220)


def _r52_r3_ready_for_actual_review_evidence_check(scan: Mapping[str, Any]) -> bool:
    return (
        scan.get("decision_ref") == "R52_R51_BODYFREE_HANDOFF_ACCEPTED_FOR_ACTUAL_REVIEW_EVIDENCE_CHECK"
        and scan.get("decision_status") == "CANDIDATE_ONLY"
        and scan.get("body_free_boundary_passed") is True
        and scan.get("r52_3_forbidden_payload_deep_scan_built") is True
    )


def build_p7_r52_actual_review_evidence_completeness(
    *,
    forbidden_payload_deep_scan: Mapping[str, Any] | None = None,
    r52_forbidden_payload_deep_scan: Mapping[str, Any] | None = None,
    r51_actual_review_evidence: Mapping[str, Any] | None = None,
    validation_evidence_matrix_freeze: Mapping[str, Any] | None = None,
    current_received_snapshot_refreeze: Mapping[str, Any] | None = None,
    r51_bodyfree_handoff_materials: Sequence[Mapping[str, Any]] | None = None,
    material_id: str = "p7_r52_actual_review_evidence_completeness",
) -> dict[str, Any]:
    """Build R52-4 actual review evidence completeness without running review."""

    r3_source = forbidden_payload_deep_scan if forbidden_payload_deep_scan is not None else r52_forbidden_payload_deep_scan
    r3 = (
        safe_mapping(r3_source)
        if r3_source is not None
        else build_p7_r52_r0_r3_r51_bodyfree_intake_forbidden_scan_chain(
            current_received_snapshot_refreeze=current_received_snapshot_refreeze,
            validation_evidence_matrix_freeze=validation_evidence_matrix_freeze,
            r51_bodyfree_handoff_materials=r51_bodyfree_handoff_materials,
        )
    )
    assert_p7_r52_forbidden_payload_deep_scan_contract(r3)
    evidence = safe_mapping(r51_actual_review_evidence)
    values = _r52_actual_review_evidence_values(evidence)
    forbidden_key_paths = _r52_find_forbidden_key_paths(
        evidence,
        forbidden_keys=P7_R52_FORBIDDEN_PAYLOAD_KEY_REFS,
        path="r51_actual_review_evidence",
    )
    forbidden_true_paths = _r52_find_forbidden_true_flag_paths(
        evidence,
        forbidden_flags=P7_R52_FORBIDDEN_TRUE_FLAG_REFS,
        path="r51_actual_review_evidence",
    )
    r3_ready = _r52_r3_ready_for_actual_review_evidence_check(r3)
    boundary_risk = bool(forbidden_key_paths or forbidden_true_paths)
    missing_refs = _r52_missing_actual_review_evidence_refs(values)
    complete = bool(r3_ready and not boundary_risk and not missing_refs)
    if boundary_risk:
        status = "R52_R51_ACTUAL_REVIEW_EVIDENCE_BLOCKED_BY_BODY_FREE_BOUNDARY_RISK"
        next_step = P7_R52_R4_BLOCKED_NEXT_REQUIRED_STEP_REF
        implemented_steps = P7_R52_R3_IMPLEMENTED_STEPS
        not_yet_steps = P7_R52_R3_NOT_YET_IMPLEMENTED_STEPS
        r4_built = False
    elif not r3_ready:
        status = "R52_R51_ACTUAL_REVIEW_EVIDENCE_BLOCKED_BY_R3"
        next_step = P7_R52_R4_BLOCKED_NEXT_REQUIRED_STEP_REF
        implemented_steps = P7_R52_R3_IMPLEMENTED_STEPS
        not_yet_steps = P7_R52_R3_NOT_YET_IMPLEMENTED_STEPS
        r4_built = False
    elif complete:
        status = "R52_R51_ACTUAL_REVIEW_EVIDENCE_COMPLETE"
        next_step = P7_R52_R4_NEXT_REQUIRED_STEP_REF
        implemented_steps = P7_R52_R4_IMPLEMENTED_STEPS
        not_yet_steps = P7_R52_R4_NOT_YET_IMPLEMENTED_STEPS
        r4_built = True
    else:
        status = "R52_R51_ACTUAL_REVIEW_EVIDENCE_MISSING"
        next_step = P7_R52_R4_NEXT_REQUIRED_STEP_REF
        implemented_steps = P7_R52_R4_IMPLEMENTED_STEPS
        not_yet_steps = P7_R52_R4_NOT_YET_IMPLEMENTED_STEPS
        r4_built = True
    completeness = {
        "schema_version": P7_R52_ACTUAL_REVIEW_EVIDENCE_COMPLETENESS_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R52_STEP,
        "scope": P7_R52_SCOPE,
        "policy_kind": P7_R52_POLICY_KIND,
        "policy_section": P7_R52_R4_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r52_actual_review_evidence_completeness", max_length=180),
        "review_session_id": clean_identifier(r3.get("review_session_id"), default=P7_R52_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "r3_scan_schema_version": P7_R52_FORBIDDEN_PAYLOAD_DEEP_SCAN_SCHEMA_VERSION,
        "r3_scan_material_ref": clean_identifier(r3.get("material_id"), default="p7_r52_forbidden_payload_deep_scan", max_length=180),
        "r3_scan_decision_ref": clean_identifier(r3.get("decision_ref"), default="R52_RETURN_TO_R51_BODYFREE_HANDOFF_INTAKE_REQUIRED", max_length=180),
        "r3_scan_decision_status": clean_identifier(r3.get("decision_status"), default="RETURN_REQUIRED", max_length=80),
        "r3_scan_ready_for_r52_4_evidence_check": r3_ready,
        "r3_body_free_boundary_passed": r3.get("body_free_boundary_passed") is True,
        "acceptable_review_session_status_refs": list(P7_R52_ACCEPTABLE_REVIEW_SESSION_STATUS_REFS),
        "forbidden_payload_key_refs": list(P7_R52_FORBIDDEN_PAYLOAD_KEY_REFS),
        "forbidden_true_flag_refs": list(P7_R52_FORBIDDEN_TRUE_FLAG_REFS),
        "detected_forbidden_payload_key_paths": dedupe_identifiers(forbidden_key_paths, limit=80, max_length=240),
        "detected_forbidden_true_flag_paths": dedupe_identifiers(forbidden_true_paths, limit=80, max_length=240),
        "forbidden_payload_keys_absent": not bool(forbidden_key_paths),
        "forbidden_true_flags_absent": not bool(forbidden_true_paths),
        "body_free_boundary_passed": r3_ready and not boundary_risk,
        "r51_actual_review_evidence_complete": complete,
        "missing_evidence_refs": missing_refs,
        "missing_evidence_count": len(missing_refs),
        "r51_actual_review_evidence_completeness_status": status,
        "r52_0_current_received_snapshot_refrozen": True,
        "r52_1_validation_evidence_matrix_frozen": True,
        "r52_2_r51_bodyfree_handoff_intake_contract_built": True,
        "r52_3_forbidden_payload_deep_scan_built": r3.get("r52_3_forbidden_payload_deep_scan_built") is True,
        "r52_4_actual_review_evidence_completeness_checker_built": r4_built,
        "r52_5_evidence_missing_no_go_branch_built": False,
        "implemented_steps": list(implemented_steps),
        "not_yet_implemented_steps": list(not_yet_steps),
        "first_next_work_ref": P7_R52_FIRST_NEXT_WORK_REF,
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "r52_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **values,
        **_r52_false_flags_r4_r5(),
    }
    assert_p7_r52_actual_review_evidence_completeness_contract(completeness)
    return completeness


def assert_p7_r52_actual_review_evidence_completeness_contract(completeness: Mapping[str, Any]) -> bool:
    data = safe_mapping(completeness)
    _assert_required_fields(
        data,
        required=P7_R52_ACTUAL_REVIEW_EVIDENCE_COMPLETENESS_REQUIRED_FIELD_REFS,
        source="p7_r52_r4_actual_review_evidence_completeness",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R52_ACTUAL_REVIEW_EVIDENCE_COMPLETENESS_SCHEMA_VERSION,
        source="p7_r52_r4_actual_review_evidence_completeness",
    )
    for false_key in P7_R52_R4_R5_FALSE_KEY_REFS:
        if data.get(false_key) is not False:
            raise ValueError(f"R52 R4 must keep {false_key}=False")
    if data.get("policy_section") != P7_R52_R4_STEP_REF:
        raise ValueError("R52 R4 policy section changed")
    if data.get("r3_scan_schema_version") != P7_R52_FORBIDDEN_PAYLOAD_DEEP_SCAN_SCHEMA_VERSION:
        raise ValueError("R52 R4 must read R52-3 scan material")
    if tuple(data.get("acceptable_review_session_status_refs") or ()) != P7_R52_ACCEPTABLE_REVIEW_SESSION_STATUS_REFS:
        raise ValueError("R52 R4 acceptable review session statuses changed")
    if data.get("review_session_status") not in P7_R52_KNOWN_REVIEW_SESSION_STATUS_REFS:
        raise ValueError("R52 R4 review session status changed")
    for int_key in ("rating_row_count", "question_observation_row_count", "open_execution_blocker_count", "missing_evidence_count"):
        if not isinstance(data.get(int_key), int) or data[int_key] < 0:
            raise ValueError(f"R52 R4 must keep non-negative {int_key}")
    payload_absent = not bool(data.get("detected_forbidden_payload_key_paths"))
    true_flags_absent = not bool(data.get("detected_forbidden_true_flag_paths"))
    boundary_passed = data.get("r3_scan_ready_for_r52_4_evidence_check") is True and payload_absent and true_flags_absent
    if data.get("forbidden_payload_keys_absent") is not payload_absent:
        raise ValueError("R52 R4 payload key absence does not match detected paths")
    if data.get("forbidden_true_flags_absent") is not true_flags_absent:
        raise ValueError("R52 R4 true flag absence does not match detected paths")
    if data.get("body_free_boundary_passed") is not boundary_passed:
        raise ValueError("R52 R4 body-free boundary flag does not match R3 readiness and evidence scan")
    if tuple(data.get("forbidden_payload_key_refs") or ()) != P7_R52_FORBIDDEN_PAYLOAD_KEY_REFS:
        raise ValueError("R52 R4 forbidden payload key refs changed")
    if tuple(data.get("forbidden_true_flag_refs") or ()) != P7_R52_FORBIDDEN_TRUE_FLAG_REFS:
        raise ValueError("R52 R4 forbidden true flag refs changed")
    missing_refs = list(data.get("missing_evidence_refs") or [])
    if data.get("missing_evidence_count") != len(missing_refs):
        raise ValueError("R52 R4 missing evidence count does not match refs")
    expected_missing = _r52_missing_actual_review_evidence_refs(data)
    if tuple(missing_refs) != tuple(expected_missing):
        raise ValueError("R52 R4 missing evidence refs do not match evidence values")
    complete = bool(
        data.get("r3_scan_ready_for_r52_4_evidence_check") is True
        and data.get("body_free_boundary_passed") is True
        and not expected_missing
    )
    if data.get("r51_actual_review_evidence_complete") is not complete:
        raise ValueError("R52 R4 completeness flag does not match required evidence")
    status = data.get("r51_actual_review_evidence_completeness_status")
    if status not in P7_R52_ACTUAL_REVIEW_EVIDENCE_COMPLETENESS_STATUS_REFS:
        raise ValueError("R52 R4 completeness status changed")
    if complete:
        if status != "R52_R51_ACTUAL_REVIEW_EVIDENCE_COMPLETE":
            raise ValueError("R52 R4 complete evidence must use complete status")
        if data.get("next_required_step") != P7_R52_R4_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R52 R4 complete evidence must still go through R52-5")
    elif data.get("detected_forbidden_payload_key_paths") or data.get("detected_forbidden_true_flag_paths"):
        if status != "R52_R51_ACTUAL_REVIEW_EVIDENCE_BLOCKED_BY_BODY_FREE_BOUNDARY_RISK":
            raise ValueError("R52 R4 forbidden evidence must use boundary risk status")
    elif data.get("r3_scan_ready_for_r52_4_evidence_check") is not True:
        if status != "R52_R51_ACTUAL_REVIEW_EVIDENCE_BLOCKED_BY_R3":
            raise ValueError("R52 R4 not-ready R3 must use R3 blocked status")
    else:
        if status != "R52_R51_ACTUAL_REVIEW_EVIDENCE_MISSING":
            raise ValueError("R52 R4 missing evidence must use missing status")
        if data.get("next_required_step") != P7_R52_R4_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R52 R4 missing evidence must point to R52-5")
    if data.get("r52_4_actual_review_evidence_completeness_checker_built") is not (status in {"R52_R51_ACTUAL_REVIEW_EVIDENCE_COMPLETE", "R52_R51_ACTUAL_REVIEW_EVIDENCE_MISSING"}):
        raise ValueError("R52 R4 built flag must match boundary readiness")
    if data.get("r52_5_evidence_missing_no_go_branch_built") is not False:
        raise ValueError("R52 R4 must not mark R52-5 built")
    if data.get("p6_limited_human_readfeel_start_allowed") is not False or data.get("p8_start_allowed") is not False:
        raise ValueError("R52 R4 must not start P6/P8")
    if data.get("p7_complete") is not False or data.get("release_allowed") is not False:
        raise ValueError("R52 R4 must not complete P7 or allow release")
    return True


def build_p7_r52_evidence_missing_no_go_branch(
    *,
    actual_review_evidence_completeness: Mapping[str, Any] | None = None,
    forbidden_payload_deep_scan: Mapping[str, Any] | None = None,
    r52_forbidden_payload_deep_scan: Mapping[str, Any] | None = None,
    r51_actual_review_evidence: Mapping[str, Any] | None = None,
    validation_evidence_matrix_freeze: Mapping[str, Any] | None = None,
    current_received_snapshot_refreeze: Mapping[str, Any] | None = None,
    r51_bodyfree_handoff_materials: Sequence[Mapping[str, Any]] | None = None,
    material_id: str = "p7_r52_evidence_missing_no_go_branch",
) -> dict[str, Any]:
    """Build R52-5 evidence-missing NO_GO branch without starting P6/P8."""

    r4 = (
        safe_mapping(actual_review_evidence_completeness)
        if actual_review_evidence_completeness is not None
        else build_p7_r52_actual_review_evidence_completeness(
            forbidden_payload_deep_scan=forbidden_payload_deep_scan,
            r52_forbidden_payload_deep_scan=r52_forbidden_payload_deep_scan,
            r51_actual_review_evidence=r51_actual_review_evidence,
            validation_evidence_matrix_freeze=validation_evidence_matrix_freeze,
            current_received_snapshot_refreeze=current_received_snapshot_refreeze,
            r51_bodyfree_handoff_materials=r51_bodyfree_handoff_materials,
        )
    )
    assert_p7_r52_actual_review_evidence_completeness_contract(r4)
    complete = r4.get("r51_actual_review_evidence_complete") is True
    boundary_risk = (
        r4.get("body_free_boundary_passed") is False
        or r4.get("r51_actual_review_evidence_completeness_status")
        in {
            "R52_R51_ACTUAL_REVIEW_EVIDENCE_BLOCKED_BY_BODY_FREE_BOUNDARY_RISK",
            "R52_R51_ACTUAL_REVIEW_EVIDENCE_BLOCKED_BY_R3",
        }
    )
    missing_refs = list(r4.get("missing_evidence_refs") or [])
    if boundary_risk:
        decision_ref = "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK"
        decision_status = "BLOCKED"
        p5_status = "R52_P5_BLOCKED_BY_BOUNDARY_RISK"
        reasons = dedupe_identifiers(
            [*missing_refs, "r51_actual_review_evidence_body_free_boundary_risk"],
            limit=120,
            max_length=220,
        )
        next_step = P7_R52_R4_BLOCKED_NEXT_REQUIRED_STEP_REF
        implemented_steps = P7_R52_R4_IMPLEMENTED_STEPS
        not_yet_steps = P7_R52_R4_NOT_YET_IMPLEMENTED_STEPS
        r5_built = False
    elif not complete:
        decision_ref = "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED"
        decision_status = "RETURN_REQUIRED"
        p5_status = "R52_P5_NOT_REVIEWED_EVIDENCE_MISSING"
        reasons = dedupe_identifiers(
            [*missing_refs, "r51_p5_confirmed_final_missing"],
            limit=120,
            max_length=220,
        )
        next_step = P7_R52_R5_RETURN_TO_R51_NEXT_REQUIRED_STEP_REF
        implemented_steps = P7_R52_R5_IMPLEMENTED_STEPS
        not_yet_steps = P7_R52_R5_NOT_YET_IMPLEMENTED_STEPS
        r5_built = True
    else:
        decision_ref = "R52_NO_GO_P6_P8_START"
        decision_status = "CANDIDATE_ONLY"
        p5_status = "R52_P5_CONFIRMED_CANDIDATE_REVIEWED_NOT_FINAL"
        reasons = ["r51_actual_review_evidence_complete_continue_to_r52_6_disposal_safety_gate_without_auto_allow"]
        next_step = P7_R52_R5_NEXT_REQUIRED_STEP_REF
        implemented_steps = P7_R52_R5_IMPLEMENTED_STEPS
        not_yet_steps = P7_R52_R5_NOT_YET_IMPLEMENTED_STEPS
        r5_built = True
    branch = {
        "schema_version": P7_R52_EVIDENCE_MISSING_NO_GO_BRANCH_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R52_STEP,
        "scope": P7_R52_SCOPE,
        "policy_kind": P7_R52_POLICY_KIND,
        "policy_section": P7_R52_R5_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r52_evidence_missing_no_go_branch", max_length=180),
        "review_session_id": clean_identifier(r4.get("review_session_id"), default=P7_R52_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "r4_completeness_schema_version": P7_R52_ACTUAL_REVIEW_EVIDENCE_COMPLETENESS_SCHEMA_VERSION,
        "r4_completeness_material_ref": clean_identifier(r4.get("material_id"), default="p7_r52_actual_review_evidence_completeness", max_length=180),
        "r4_completeness_status": clean_identifier(r4.get("r51_actual_review_evidence_completeness_status"), default="R52_R51_ACTUAL_REVIEW_EVIDENCE_MISSING", max_length=160),
        "r4_completeness_checker_built": r4.get("r52_4_actual_review_evidence_completeness_checker_built") is True,
        "r51_actual_review_evidence_complete": complete,
        "missing_evidence_refs": dedupe_identifiers(missing_refs, limit=120, max_length=220),
        "missing_evidence_count": len(dedupe_identifiers(missing_refs, limit=120, max_length=220)),
        "body_free_boundary_passed": r4.get("body_free_boundary_passed") is True,
        "boundary_risk_detected": boundary_risk,
        "decision_ref": decision_ref,
        "decision_status": decision_status,
        "decision_reason_refs": reasons,
        "next_required_step": next_step,
        "p5_decision_status": p5_status,
        "p6_limited_human_readfeel_start_allowed_candidate": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_question_design_material_candidate": False,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "r52_0_current_received_snapshot_refrozen": True,
        "r52_1_validation_evidence_matrix_frozen": True,
        "r52_2_r51_bodyfree_handoff_intake_contract_built": True,
        "r52_3_forbidden_payload_deep_scan_built": r4.get("r52_3_forbidden_payload_deep_scan_built") is True,
        "r52_4_actual_review_evidence_completeness_checker_built": r4.get("r52_4_actual_review_evidence_completeness_checker_built") is True,
        "r52_5_evidence_missing_no_go_branch_built": r5_built,
        "implemented_steps": list(implemented_steps),
        "not_yet_implemented_steps": list(not_yet_steps),
        "first_next_work_ref": P7_R52_FIRST_NEXT_WORK_REF,
        "public_contract": public_contract_flags(),
        "r52_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_r52_false_flags_r4_r5(),
    }
    assert_p7_r52_evidence_missing_no_go_branch_contract(branch)
    return branch


def assert_p7_r52_evidence_missing_no_go_branch_contract(branch: Mapping[str, Any]) -> bool:
    data = safe_mapping(branch)
    _assert_required_fields(
        data,
        required=P7_R52_EVIDENCE_MISSING_NO_GO_BRANCH_REQUIRED_FIELD_REFS,
        source="p7_r52_r5_evidence_missing_no_go_branch",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R52_EVIDENCE_MISSING_NO_GO_BRANCH_SCHEMA_VERSION,
        source="p7_r52_r5_evidence_missing_no_go_branch",
    )
    for false_key in P7_R52_R4_R5_FALSE_KEY_REFS:
        if data.get(false_key) is not False:
            raise ValueError(f"R52 R5 must keep {false_key}=False")
    if data.get("policy_section") != P7_R52_R5_STEP_REF:
        raise ValueError("R52 R5 policy section changed")
    if data.get("r4_completeness_schema_version") != P7_R52_ACTUAL_REVIEW_EVIDENCE_COMPLETENESS_SCHEMA_VERSION:
        raise ValueError("R52 R5 must read R52-4 completeness material")
    if data.get("decision_ref") not in P7_R52_R5_DECISION_REF_REFS:
        raise ValueError("R52 R5 decision ref changed")
    if data.get("decision_status") not in P7_R52_R5_DECISION_STATUS_REFS:
        raise ValueError("R52 R5 decision status changed")
    if data.get("p5_decision_status") not in P7_R52_P5_DECISION_STATUS_REFS:
        raise ValueError("R52 R5 P5 decision status changed")
    missing_refs = list(data.get("missing_evidence_refs") or [])
    if data.get("missing_evidence_count") != len(missing_refs):
        raise ValueError("R52 R5 missing evidence count does not match refs")
    if data.get("r51_actual_review_evidence_complete") is True:
        if missing_refs:
            raise ValueError("R52 R5 complete evidence cannot keep missing refs")
        if data.get("decision_ref") != "R52_NO_GO_P6_P8_START":
            raise ValueError("R52 R5 complete evidence still must keep P6/P8 no-go")
        if data.get("decision_status") != "CANDIDATE_ONLY":
            raise ValueError("R52 R5 complete evidence is candidate-only for later gates")
        if data.get("next_required_step") != P7_R52_R5_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R52 R5 complete evidence must move only to disposal gate")
    elif data.get("boundary_risk_detected") is True:
        if data.get("decision_ref") != "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK":
            raise ValueError("R52 R5 boundary risk must use boundary-risk decision")
        if data.get("decision_status") != "BLOCKED":
            raise ValueError("R52 R5 boundary risk must be blocked")
        if data.get("r52_5_evidence_missing_no_go_branch_built") is not False:
            raise ValueError("R52 R5 boundary risk must not mark missing NO_GO branch built")
    else:
        if not missing_refs:
            raise ValueError("R52 R5 missing branch requires missing evidence refs")
        if data.get("decision_ref") != "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED":
            raise ValueError("R52 R5 missing evidence must return to R51 actual review")
        if data.get("decision_status") != "RETURN_REQUIRED":
            raise ValueError("R52 R5 missing evidence must be return-required")
        if data.get("p5_decision_status") != "R52_P5_NOT_REVIEWED_EVIDENCE_MISSING":
            raise ValueError("R52 R5 missing evidence must keep P5 not reviewed")
        if "r51_p5_confirmed_final_missing" not in data.get("decision_reason_refs", []):
            raise ValueError("R52 R5 missing evidence must keep P5 final missing explicit")
        if data.get("next_required_step") != P7_R52_R5_RETURN_TO_R51_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R52 R5 missing evidence must point back to R51 actual review")
        if data.get("r52_5_evidence_missing_no_go_branch_built") is not True:
            raise ValueError("R52 R5 missing evidence must mark R52-5 built")
    if data.get("p6_limited_human_readfeel_start_allowed_candidate") is not False:
        raise ValueError("R52 R5 must not expose P6 start candidate from missing evidence")
    if data.get("p8_question_design_material_candidate") is not False:
        raise ValueError("R52 R5 must not expose P8 material candidate from missing evidence")
    if data.get("p6_limited_human_readfeel_start_allowed") is not False or data.get("p8_start_allowed") is not False:
        raise ValueError("R52 R5 must not start P6/P8")
    if data.get("p7_complete") is not False or data.get("release_allowed") is not False:
        raise ValueError("R52 R5 must not complete P7 or allow release")
    blocked_decision_refs = {
        "R52_RELEASE_ALLOWED",
        "R52_P7_COMPLETE",
        "R52_P8_START_ALLOWED",
        "R52_P6_START_ALLOWED",
        "R52_P5_CONFIRMED_FINAL",
        "R52_QUESTION_IMPLEMENTATION_ALLOWED",
        "R52_API_DB_RN_CHANGE_ALLOWED",
    }
    if data.get("decision_ref") in blocked_decision_refs:
        raise ValueError("R52 R5 must not produce auto-allow decision refs")
    return True


def build_p7_r52_r0_r5_actual_review_evidence_missing_no_go_chain(
    *,
    current_received_snapshot_refreeze: Mapping[str, Any] | None = None,
    validation_evidence_matrix_freeze: Mapping[str, Any] | None = None,
    r51_bodyfree_handoff_materials: Sequence[Mapping[str, Any]] | None = None,
    r51_actual_review_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return R52-5 material after validating the R52-0/R52-5 body-free chain."""

    r0 = (
        safe_mapping(current_received_snapshot_refreeze)
        if current_received_snapshot_refreeze is not None
        else build_p7_r52_current_received_snapshot_refreeze()
    )
    assert_p7_r52_current_received_snapshot_refreeze_contract(r0)
    r1 = (
        safe_mapping(validation_evidence_matrix_freeze)
        if validation_evidence_matrix_freeze is not None
        else build_p7_r52_validation_evidence_matrix_freeze(current_received_snapshot_refreeze=r0)
    )
    assert_p7_r52_validation_evidence_matrix_freeze_contract(r1)
    r3 = build_p7_r52_r0_r3_r51_bodyfree_intake_forbidden_scan_chain(
        current_received_snapshot_refreeze=r0,
        validation_evidence_matrix_freeze=r1,
        r51_bodyfree_handoff_materials=r51_bodyfree_handoff_materials,
    )
    assert_p7_r52_forbidden_payload_deep_scan_contract(r3)
    r4 = build_p7_r52_actual_review_evidence_completeness(
        forbidden_payload_deep_scan=r3,
        r51_actual_review_evidence=r51_actual_review_evidence,
    )
    assert_p7_r52_actual_review_evidence_completeness_contract(r4)
    r5 = build_p7_r52_evidence_missing_no_go_branch(actual_review_evidence_completeness=r4)
    assert_p7_r52_evidence_missing_no_go_branch_contract(r5)
    return r5


# ---------------------------------------------------------------------------
# R52-6 / R52-7: disposal safety gate + execution blocker gate.
# ---------------------------------------------------------------------------

P7_R52_DISPOSAL_SAFETY_GATE_SCHEMA_VERSION: Final = "cocolon.emlis.p7_r52.disposal_safety_gate.bodyfree.v1"
P7_R52_EXECUTION_BLOCKER_GATE_SCHEMA_VERSION: Final = "cocolon.emlis.p7_r52.execution_blocker_gate.bodyfree.v1"

P7_R52_R6_STEP_REF: Final = "R52-6_disposal_safety_gate"
P7_R52_R7_STEP_REF: Final = "R52-7_execution_blocker_gate"
P7_R52_R6_NEXT_REQUIRED_STEP_REF: Final = P7_R52_R7_STEP_REF
P7_R52_R6_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R52-6_disposal_not_verified_before_decision_material"
P7_R52_R7_NEXT_REQUIRED_STEP_REF: Final = "R52-8_rating_question_consistency_gate"
P7_R52_R7_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R52-7_execution_blocker_open_before_p5_p6_p8_decision"

P7_R52_FUTURE_STEPS_AFTER_R7: Final[tuple[str, ...]] = P7_R52_FUTURE_STEPS_AFTER_R5[2:]
P7_R52_R6_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R52_R5_IMPLEMENTED_STEPS, P7_R52_R6_STEP_REF)
P7_R52_R6_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R52_R7_STEP_REF, *P7_R52_FUTURE_STEPS_AFTER_R7)
P7_R52_R7_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R52_R6_IMPLEMENTED_STEPS, P7_R52_R7_STEP_REF)
P7_R52_R7_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R52_FUTURE_STEPS_AFTER_R7
P7_R52_CURRENT_IMPLEMENTED_STEPS = P7_R52_R7_IMPLEMENTED_STEPS
P7_R52_CURRENT_NOT_YET_IMPLEMENTED_STEPS = P7_R52_R7_NOT_YET_IMPLEMENTED_STEPS

P7_R52_R6_DECISION_REF_REFS: Final[tuple[str, ...]] = (
    "R52_NO_GO_P6_P8_START",
    "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED",
    "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK",
    "R52_BLOCKED_BY_DISPOSAL_NOT_VERIFIED",
)
P7_R52_R7_DECISION_REF_REFS: Final[tuple[str, ...]] = (
    *P7_R52_R6_DECISION_REF_REFS,
    "R52_BLOCKED_BY_EXECUTION_BLOCKER_OPEN",
)
P7_R52_DISPOSAL_SAFETY_GATE_STATUS_REFS: Final[tuple[str, ...]] = (
    "R52_DISPOSAL_SAFETY_GATE_PASSED",
    "R52_DISPOSAL_SAFETY_GATE_BLOCKED_BY_DISPOSAL_NOT_VERIFIED",
    "R52_DISPOSAL_SAFETY_GATE_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED",
    "R52_DISPOSAL_SAFETY_GATE_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK",
    "R52_DISPOSAL_SAFETY_GATE_NOT_APPLICABLE_ACTUAL_REVIEW_NOT_STARTED",
)
P7_R52_EXECUTION_BLOCKER_GATE_STATUS_REFS: Final[tuple[str, ...]] = (
    "R52_EXECUTION_BLOCKER_GATE_PASSED",
    "R52_EXECUTION_BLOCKER_GATE_BLOCKED_BY_EXECUTION_BLOCKER_OPEN",
    "R52_EXECUTION_BLOCKER_GATE_BLOCKED_BY_DISPOSAL_NOT_VERIFIED",
    "R52_EXECUTION_BLOCKER_GATE_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED",
    "R52_EXECUTION_BLOCKER_GATE_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK",
    "R52_EXECUTION_BLOCKER_GATE_NOT_REACHED_BY_R6",
)

P7_R52_R6_R7_EXTRA_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    "r52_disposal_verification_created_here",
    "r52_disposal_gate_created_bodyfull_receipt_here",
    "r52_execution_blocker_rows_created_here",
    "r52_execution_blocker_resolution_run_here",
    "r52_p5_p6_p8_decision_material_auto_promoted_here",
    "r51_disposal_receipt_created_here",
    "execution_blocker_cleared_here",
)
P7_R52_R6_R7_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    *P7_R52_R4_R5_FALSE_KEY_REFS,
    *P7_R52_R6_R7_EXTRA_FALSE_KEY_REFS,
)

P7_R52_DISPOSAL_SAFETY_GATE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "current_phase",
    "material_id", "review_session_id", "required_case_count",
    "r5_no_go_schema_version", "r5_no_go_material_ref", "r5_decision_ref", "r5_decision_status",
    "r5_next_required_step", "r5_ready_for_r52_6_disposal_gate",
    "r4_completeness_schema_version", "r4_completeness_material_ref", "r4_completeness_status",
    "r51_actual_review_evidence_complete", "r51_actual_human_review_run_recorded",
    "r51_actual_body_full_material_created", "r51_actual_review_or_body_full_material_created",
    "disposal_safety_required", "disposal_verified", "body_removed", "reviewer_notes_removed",
    "missing_evidence_refs", "disposal_not_verified", "disposal_not_verified_reason_refs",
    "disposal_safety_gate_status", "decision_ref", "decision_status", "decision_reason_refs",
    "next_required_step", "p5_decision_status",
    "p6_limited_human_readfeel_start_allowed_candidate", "p6_limited_human_readfeel_start_allowed",
    "p8_question_design_material_candidate", "p8_start_allowed", "p7_complete", "release_allowed",
    "r52_0_current_received_snapshot_refrozen", "r52_1_validation_evidence_matrix_frozen",
    "r52_2_r51_bodyfree_handoff_intake_contract_built", "r52_3_forbidden_payload_deep_scan_built",
    "r52_4_actual_review_evidence_completeness_checker_built", "r52_5_evidence_missing_no_go_branch_built",
    "r52_6_disposal_safety_gate_built", "r52_6_ready_for_r52_7_execution_blocker_gate",
    "r52_7_execution_blocker_gate_built", "implemented_steps", "not_yet_implemented_steps",
    "first_next_work_ref", "public_contract", "r52_public_no_touch_contract", "body_free_markers", "body_free",
    *P7_R52_R6_R7_FALSE_KEY_REFS,
)
P7_R52_EXECUTION_BLOCKER_GATE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "current_phase",
    "material_id", "review_session_id", "required_case_count",
    "r6_disposal_schema_version", "r6_disposal_material_ref", "r6_decision_ref", "r6_decision_status",
    "r6_disposal_safety_gate_status", "r6_disposal_gate_status", "r6_ready_for_r52_7_execution_blocker_gate",
    "r4_completeness_schema_version", "r4_completeness_material_ref", "r51_actual_review_evidence_complete",
    "open_execution_blocker_count", "execution_blocker_open", "execution_blocker_gate_status",
    "execution_blocker_reason_refs", "decision_ref", "decision_status", "decision_reason_refs",
    "next_required_step", "p5_decision_status",
    "p6_limited_human_readfeel_start_allowed_candidate", "p6_limited_human_readfeel_start_allowed",
    "p8_question_design_material_candidate", "p8_start_allowed", "p7_complete", "release_allowed",
    "r52_0_current_received_snapshot_refrozen", "r52_1_validation_evidence_matrix_frozen",
    "r52_2_r51_bodyfree_handoff_intake_contract_built", "r52_3_forbidden_payload_deep_scan_built",
    "r52_4_actual_review_evidence_completeness_checker_built", "r52_5_evidence_missing_no_go_branch_built",
    "r52_6_disposal_safety_gate_built", "r52_7_execution_blocker_gate_built",
    "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref",
    "public_contract", "r52_public_no_touch_contract", "body_free_markers", "body_free",
    *P7_R52_R6_R7_FALSE_KEY_REFS,
)


def _r52_false_flags_r6_r7() -> dict[str, bool]:
    return {key: False for key in P7_R52_R6_R7_FALSE_KEY_REFS}


def _r52_body_full_material_created_reported(evidence: Mapping[str, Any] | None) -> bool:
    material = safe_mapping(evidence)
    return _r52_evidence_bool(
        material,
        "r51_actual_body_full_material_created",
        "actual_body_full_material_created",
        "r51_body_full_material_created",
        "body_full_material_created",
        "r51_body_full_packet_generated",
        "body_full_packet_generated",
        "r51_body_full_packet_created",
        "body_full_packet_created",
        default=False,
    )


def _r52_r5_ready_for_disposal_gate(branch: Mapping[str, Any]) -> bool:
    return (
        branch.get("r51_actual_review_evidence_complete") is True
        and branch.get("decision_ref") == "R52_NO_GO_P6_P8_START"
        and branch.get("decision_status") == "CANDIDATE_ONLY"
        and branch.get("next_required_step") == P7_R52_R5_NEXT_REQUIRED_STEP_REF
        and branch.get("r52_5_evidence_missing_no_go_branch_built") is True
    )


def _r52_r6_ready_for_execution_gate(gate: Mapping[str, Any]) -> bool:
    return (
        gate.get("disposal_safety_gate_status") == "R52_DISPOSAL_SAFETY_GATE_PASSED"
        and gate.get("decision_ref") == "R52_NO_GO_P6_P8_START"
        and gate.get("decision_status") == "CANDIDATE_ONLY"
        and gate.get("next_required_step") == P7_R52_R6_NEXT_REQUIRED_STEP_REF
        and gate.get("r52_6_disposal_safety_gate_built") is True
    )


def build_p7_r52_disposal_safety_gate(
    *,
    evidence_missing_no_go_branch: Mapping[str, Any] | None = None,
    actual_review_evidence_completeness: Mapping[str, Any] | None = None,
    r51_actual_review_evidence: Mapping[str, Any] | None = None,
    forbidden_payload_deep_scan: Mapping[str, Any] | None = None,
    r52_forbidden_payload_deep_scan: Mapping[str, Any] | None = None,
    validation_evidence_matrix_freeze: Mapping[str, Any] | None = None,
    current_received_snapshot_refreeze: Mapping[str, Any] | None = None,
    r51_bodyfree_handoff_materials: Sequence[Mapping[str, Any]] | None = None,
    material_id: str = "p7_r52_disposal_safety_gate",
) -> dict[str, Any]:
    """Build R52-6 without creating body-full material, receipts, or review rows."""

    r4 = (
        safe_mapping(actual_review_evidence_completeness)
        if actual_review_evidence_completeness is not None
        else build_p7_r52_actual_review_evidence_completeness(
            forbidden_payload_deep_scan=forbidden_payload_deep_scan,
            r52_forbidden_payload_deep_scan=r52_forbidden_payload_deep_scan,
            r51_actual_review_evidence=r51_actual_review_evidence,
            validation_evidence_matrix_freeze=validation_evidence_matrix_freeze,
            current_received_snapshot_refreeze=current_received_snapshot_refreeze,
            r51_bodyfree_handoff_materials=r51_bodyfree_handoff_materials,
        )
    )
    assert_p7_r52_actual_review_evidence_completeness_contract(r4)
    r5 = (
        safe_mapping(evidence_missing_no_go_branch)
        if evidence_missing_no_go_branch is not None
        else build_p7_r52_evidence_missing_no_go_branch(actual_review_evidence_completeness=r4)
    )
    assert_p7_r52_evidence_missing_no_go_branch_contract(r5)

    r5_ready = _r52_r5_ready_for_disposal_gate(r5)
    actual_review_recorded = r4.get("r8_actual_human_review_run_recorded") is True
    body_full_created = _r52_body_full_material_created_reported(r51_actual_review_evidence)
    actual_or_bodyfull_created = actual_review_recorded or body_full_created
    disposal_verified = r4.get("disposal_verified") is True
    body_removed = r4.get("body_removed") is True
    reviewer_notes_removed = r4.get("reviewer_notes_removed") is True
    disposal_safety_required = bool(actual_or_bodyfull_created)
    disposal_not_verified = bool(actual_or_bodyfull_created and not (disposal_verified and body_removed and reviewer_notes_removed))
    disposal_not_verified_reason_refs: list[str] = []
    if disposal_not_verified:
        if not disposal_verified:
            disposal_not_verified_reason_refs.append("r51_disposal_verified_missing_after_body_full_material_created")
        if not body_removed:
            disposal_not_verified_reason_refs.append("r51_body_full_packet_body_removed_not_verified")
        if not reviewer_notes_removed:
            disposal_not_verified_reason_refs.append("r51_reviewer_notes_removed_not_verified")

    if r5.get("decision_ref") == "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK":
        decision_ref = "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK"
        decision_status = "BLOCKED"
        gate_status = "R52_DISPOSAL_SAFETY_GATE_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK"
        p5_status = "R52_P5_BLOCKED_BY_BOUNDARY_RISK"
        reasons = dedupe_identifiers(
            [*(r5.get("decision_reason_refs") or []), "r52_6_blocked_by_prior_body_free_boundary_risk"],
            limit=120,
            max_length=220,
        )
        next_step = clean_identifier(r5.get("next_required_step"), default=P7_R52_R4_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220)
        implemented_steps = P7_R52_R5_IMPLEMENTED_STEPS
        not_yet_steps = P7_R52_R5_NOT_YET_IMPLEMENTED_STEPS
        r6_built = False
    elif disposal_not_verified:
        decision_ref = "R52_BLOCKED_BY_DISPOSAL_NOT_VERIFIED"
        decision_status = "BLOCKED"
        gate_status = "R52_DISPOSAL_SAFETY_GATE_BLOCKED_BY_DISPOSAL_NOT_VERIFIED"
        p5_status = "R52_P5_BLOCKED_BY_DISPOSAL_NOT_VERIFIED"
        reasons = dedupe_identifiers(
            [
                "r51_actual_review_or_body_full_material_created_without_verified_disposal",
                *disposal_not_verified_reason_refs,
                *(r5.get("decision_reason_refs") or []),
            ],
            limit=120,
            max_length=220,
        )
        next_step = P7_R52_R6_BLOCKED_NEXT_REQUIRED_STEP_REF
        implemented_steps = P7_R52_R6_IMPLEMENTED_STEPS
        not_yet_steps = P7_R52_R6_NOT_YET_IMPLEMENTED_STEPS
        r6_built = True
    elif not actual_or_bodyfull_created:
        decision_ref = "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED"
        decision_status = "RETURN_REQUIRED"
        gate_status = "R52_DISPOSAL_SAFETY_GATE_NOT_APPLICABLE_ACTUAL_REVIEW_NOT_STARTED"
        p5_status = "R52_P5_NOT_REVIEWED_EVIDENCE_MISSING"
        reasons = dedupe_identifiers(
            [*(r5.get("decision_reason_refs") or []), "r52_6_disposal_gate_not_applicable_until_actual_review_or_body_full_material_exists"],
            limit=120,
            max_length=220,
        )
        next_step = clean_identifier(r5.get("next_required_step"), default=P7_R52_R5_RETURN_TO_R51_NEXT_REQUIRED_STEP_REF, max_length=220)
        implemented_steps = P7_R52_R6_IMPLEMENTED_STEPS
        not_yet_steps = P7_R52_R6_NOT_YET_IMPLEMENTED_STEPS
        r6_built = True
    else:
        decision_ref = "R52_NO_GO_P6_P8_START"
        decision_status = "CANDIDATE_ONLY"
        gate_status = "R52_DISPOSAL_SAFETY_GATE_PASSED"
        p5_status = "R52_P5_CONFIRMED_CANDIDATE_REVIEWED_NOT_FINAL" if r5_ready else "R52_P5_NOT_REVIEWED_EVIDENCE_MISSING"
        reasons = ["r51_disposal_verified_continue_to_r52_7_execution_blocker_gate_without_auto_allow"]
        next_step = P7_R52_R6_NEXT_REQUIRED_STEP_REF
        implemented_steps = P7_R52_R6_IMPLEMENTED_STEPS
        not_yet_steps = P7_R52_R6_NOT_YET_IMPLEMENTED_STEPS
        r6_built = True

    gate = {
        "schema_version": P7_R52_DISPOSAL_SAFETY_GATE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R52_STEP,
        "scope": P7_R52_SCOPE,
        "policy_kind": P7_R52_POLICY_KIND,
        "policy_section": P7_R52_R6_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r52_disposal_safety_gate", max_length=180),
        "review_session_id": clean_identifier(r5.get("review_session_id"), default=P7_R52_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "r5_no_go_schema_version": P7_R52_EVIDENCE_MISSING_NO_GO_BRANCH_SCHEMA_VERSION,
        "r5_no_go_material_ref": clean_identifier(r5.get("material_id"), default="p7_r52_evidence_missing_no_go_branch", max_length=180),
        "r5_decision_ref": clean_identifier(r5.get("decision_ref"), default="R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED", max_length=180),
        "r5_decision_status": clean_identifier(r5.get("decision_status"), default="RETURN_REQUIRED", max_length=80),
        "r5_next_required_step": clean_identifier(r5.get("next_required_step"), default=P7_R52_R5_RETURN_TO_R51_NEXT_REQUIRED_STEP_REF, max_length=220),
        "r5_ready_for_r52_6_disposal_gate": r5_ready,
        "r4_completeness_schema_version": P7_R52_ACTUAL_REVIEW_EVIDENCE_COMPLETENESS_SCHEMA_VERSION,
        "r4_completeness_material_ref": clean_identifier(r4.get("material_id"), default="p7_r52_actual_review_evidence_completeness", max_length=180),
        "r4_completeness_status": clean_identifier(r4.get("r51_actual_review_evidence_completeness_status"), default="R52_R51_ACTUAL_REVIEW_EVIDENCE_MISSING", max_length=160),
        "r51_actual_review_evidence_complete": r4.get("r51_actual_review_evidence_complete") is True,
        "r51_actual_human_review_run_recorded": actual_review_recorded,
        "r51_actual_body_full_material_created": body_full_created,
        "r51_actual_review_or_body_full_material_created": actual_or_bodyfull_created,
        "disposal_safety_required": disposal_safety_required,
        "disposal_verified": disposal_verified,
        "body_removed": body_removed,
        "reviewer_notes_removed": reviewer_notes_removed,
        "missing_evidence_refs": dedupe_identifiers(r4.get("missing_evidence_refs") or [], limit=120, max_length=220),
        "disposal_not_verified": disposal_not_verified,
        "disposal_not_verified_reason_refs": dedupe_identifiers(disposal_not_verified_reason_refs, limit=20, max_length=220),
        "disposal_safety_gate_status": gate_status,
        "decision_ref": decision_ref,
        "decision_status": decision_status,
        "decision_reason_refs": reasons,
        "next_required_step": next_step,
        "p5_decision_status": p5_status,
        "p6_limited_human_readfeel_start_allowed_candidate": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_question_design_material_candidate": False,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "r52_0_current_received_snapshot_refrozen": True,
        "r52_1_validation_evidence_matrix_frozen": True,
        "r52_2_r51_bodyfree_handoff_intake_contract_built": True,
        "r52_3_forbidden_payload_deep_scan_built": r4.get("r52_3_forbidden_payload_deep_scan_built") is True,
        "r52_4_actual_review_evidence_completeness_checker_built": r4.get("r52_4_actual_review_evidence_completeness_checker_built") is True,
        "r52_5_evidence_missing_no_go_branch_built": r5.get("r52_5_evidence_missing_no_go_branch_built") is True,
        "r52_6_disposal_safety_gate_built": r6_built,
        "r52_6_ready_for_r52_7_execution_blocker_gate": _r52_r6_ready_for_execution_gate(
            {
                "decision_ref": decision_ref,
                "decision_status": decision_status,
                "disposal_safety_gate_status": gate_status,
                "next_required_step": next_step,
                "r52_6_disposal_safety_gate_built": r6_built,
            }
        ),
        "r52_7_execution_blocker_gate_built": False,
        "implemented_steps": list(implemented_steps),
        "not_yet_implemented_steps": list(not_yet_steps),
        "first_next_work_ref": P7_R52_FIRST_NEXT_WORK_REF,
        "public_contract": public_contract_flags(),
        "r52_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_r52_false_flags_r6_r7(),
    }
    assert_p7_r52_disposal_safety_gate_contract(gate)
    return gate


def assert_p7_r52_disposal_safety_gate_contract(gate: Mapping[str, Any]) -> bool:
    data = safe_mapping(gate)
    _assert_required_fields(data, required=P7_R52_DISPOSAL_SAFETY_GATE_REQUIRED_FIELD_REFS, source="p7_r52_r6_disposal_safety_gate")
    _assert_body_free_common(data, schema_version=P7_R52_DISPOSAL_SAFETY_GATE_SCHEMA_VERSION, source="p7_r52_r6_disposal_safety_gate")
    for false_key in P7_R52_R6_R7_FALSE_KEY_REFS:
        if data.get(false_key) is not False:
            raise ValueError(f"R52 R6 must keep {false_key}=False")
    if data.get("policy_section") != P7_R52_R6_STEP_REF:
        raise ValueError("R52 R6 policy section changed")
    if data.get("r5_no_go_schema_version") != P7_R52_EVIDENCE_MISSING_NO_GO_BRANCH_SCHEMA_VERSION:
        raise ValueError("R52 R6 must read R52-5 branch material")
    if data.get("r4_completeness_schema_version") != P7_R52_ACTUAL_REVIEW_EVIDENCE_COMPLETENESS_SCHEMA_VERSION:
        raise ValueError("R52 R6 must keep R52-4 source ref")
    if data.get("disposal_safety_gate_status") not in P7_R52_DISPOSAL_SAFETY_GATE_STATUS_REFS:
        raise ValueError("R52 R6 disposal status changed")
    if data.get("decision_ref") not in P7_R52_R6_DECISION_REF_REFS or data.get("decision_status") not in P7_R52_R5_DECISION_STATUS_REFS:
        raise ValueError("R52 R6 decision changed")
    expected_not_verified = bool(data.get("r51_actual_review_or_body_full_material_created") is True and not (data.get("disposal_verified") is True and data.get("body_removed") is True and data.get("reviewer_notes_removed") is True))
    if data.get("disposal_not_verified") is not expected_not_verified:
        raise ValueError("R52 R6 disposal_not_verified does not match evidence")
    if data.get("disposal_safety_required") is not (data.get("r51_actual_review_or_body_full_material_created") is True):
        raise ValueError("R52 R6 disposal_safety_required must match actual/body-full material existence")
    if data.get("r52_6_ready_for_r52_7_execution_blocker_gate") is not _r52_r6_ready_for_execution_gate(data):
        raise ValueError("R52 R6 ready-for-R7 flag must match gate status")
    if expected_not_verified:
        if not data.get("disposal_not_verified_reason_refs"):
            raise ValueError("R52 R6 disposal blocker must keep body-free reason refs")
        if data.get("decision_ref") != "R52_BLOCKED_BY_DISPOSAL_NOT_VERIFIED" or data.get("decision_status") != "BLOCKED":
            raise ValueError("R52 R6 unverified disposal must block")
        if data.get("p5_decision_status") != "R52_P5_BLOCKED_BY_DISPOSAL_NOT_VERIFIED":
            raise ValueError("R52 R6 unverified disposal must set P5 disposal blocker")
        if data.get("next_required_step") != P7_R52_R6_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R52 R6 unverified disposal must point to disposal resolution")
        if data.get("r52_6_disposal_safety_gate_built") is not True:
            raise ValueError("R52 R6 disposal blocker must mark gate built")
    elif data.get("r51_actual_review_or_body_full_material_created") is False:
        if data.get("decision_ref") != "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED":
            raise ValueError("R52 R6 not-started material must return to R51 actual review")
        if data.get("disposal_safety_gate_status") != "R52_DISPOSAL_SAFETY_GATE_NOT_APPLICABLE_ACTUAL_REVIEW_NOT_STARTED":
            raise ValueError("R52 R6 not-started material must be explicitly not applicable")
        if data.get("r52_6_disposal_safety_gate_built") is not True:
            raise ValueError("R52 R6 not-started classification must mark gate built")
    elif data.get("decision_ref") == "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK":
        if data.get("r52_6_disposal_safety_gate_built") is not False:
            raise ValueError("R52 R6 prior boundary risk must not mark gate built")
    else:
        if data.get("decision_ref") != "R52_NO_GO_P6_P8_START" or data.get("decision_status") != "CANDIDATE_ONLY":
            raise ValueError("R52 R6 verified disposal must remain candidate-only no-go")
        if data.get("disposal_safety_gate_status") != "R52_DISPOSAL_SAFETY_GATE_PASSED":
            raise ValueError("R52 R6 verified disposal must pass")
        if data.get("next_required_step") != P7_R52_R6_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R52 R6 verified disposal must continue to R52-7")
        if data.get("r52_6_disposal_safety_gate_built") is not True:
            raise ValueError("R52 R6 verified disposal must mark gate built")
    if data.get("r52_7_execution_blocker_gate_built") is not False:
        raise ValueError("R52 R6 must not mark R52-7 built")
    if data.get("p6_limited_human_readfeel_start_allowed_candidate") is not False or data.get("p8_question_design_material_candidate") is not False:
        raise ValueError("R52 R6 must not expose P6/P8 candidates")
    if data.get("p6_limited_human_readfeel_start_allowed") is not False or data.get("p8_start_allowed") is not False or data.get("p7_complete") is not False or data.get("release_allowed") is not False:
        raise ValueError("R52 R6 must not allow P6/P8/P7/release")
    return True


def build_p7_r52_execution_blocker_gate(
    *,
    disposal_safety_gate: Mapping[str, Any] | None = None,
    actual_review_evidence_completeness: Mapping[str, Any] | None = None,
    r51_actual_review_evidence: Mapping[str, Any] | None = None,
    **chain_kwargs: Any,
) -> dict[str, Any]:
    """Build R52-7 without clearing blockers or creating reviewer/blocker rows."""

    r4 = (
        safe_mapping(actual_review_evidence_completeness)
        if actual_review_evidence_completeness is not None
        else build_p7_r52_actual_review_evidence_completeness(
            r51_actual_review_evidence=r51_actual_review_evidence,
            **chain_kwargs,
        )
    )
    assert_p7_r52_actual_review_evidence_completeness_contract(r4)
    r6 = (
        safe_mapping(disposal_safety_gate)
        if disposal_safety_gate is not None
        else build_p7_r52_disposal_safety_gate(
            actual_review_evidence_completeness=r4,
            r51_actual_review_evidence=r51_actual_review_evidence,
            **chain_kwargs,
        )
    )
    assert_p7_r52_disposal_safety_gate_contract(r6)

    r6_ready = _r52_r6_ready_for_execution_gate(r6)
    open_count = _safe_non_negative_int(r4.get("open_execution_blocker_count"))
    execution_open = open_count > 0

    if r6.get("decision_ref") == "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK":
        decision_ref = "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK"
        decision_status = "BLOCKED"
        gate_status = "R52_EXECUTION_BLOCKER_GATE_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK"
        p5_status = "R52_P5_BLOCKED_BY_BOUNDARY_RISK"
        reasons = dedupe_identifiers([*(r6.get("decision_reason_refs") or []), "r52_7_blocked_by_prior_body_free_boundary_risk"], limit=120, max_length=220)
        next_step = clean_identifier(r6.get("next_required_step"), default=P7_R52_R4_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220)
        implemented_steps = P7_R52_R6_IMPLEMENTED_STEPS
        not_yet_steps = P7_R52_R6_NOT_YET_IMPLEMENTED_STEPS
        r7_built = False
    elif r6.get("decision_ref") == "R52_BLOCKED_BY_DISPOSAL_NOT_VERIFIED":
        decision_ref = "R52_BLOCKED_BY_DISPOSAL_NOT_VERIFIED"
        decision_status = "BLOCKED"
        gate_status = "R52_EXECUTION_BLOCKER_GATE_BLOCKED_BY_DISPOSAL_NOT_VERIFIED"
        p5_status = "R52_P5_BLOCKED_BY_DISPOSAL_NOT_VERIFIED"
        reasons = dedupe_identifiers([*(r6.get("decision_reason_refs") or []), "r52_7_not_evaluated_until_disposal_verified"], limit=120, max_length=220)
        next_step = clean_identifier(r6.get("next_required_step"), default=P7_R52_R6_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220)
        implemented_steps = P7_R52_R6_IMPLEMENTED_STEPS
        not_yet_steps = P7_R52_R6_NOT_YET_IMPLEMENTED_STEPS
        r7_built = False
    elif not r6_ready:
        decision_ref = "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED"
        decision_status = "RETURN_REQUIRED"
        gate_status = "R52_EXECUTION_BLOCKER_GATE_NOT_REACHED_BY_R6"
        p5_status = "R52_P5_NOT_REVIEWED_EVIDENCE_MISSING"
        reasons = dedupe_identifiers([*(r6.get("decision_reason_refs") or []), "r52_7_not_evaluated_until_disposal_gate_passed"], limit=120, max_length=220)
        next_step = clean_identifier(r6.get("next_required_step"), default=P7_R52_R5_RETURN_TO_R51_NEXT_REQUIRED_STEP_REF, max_length=220)
        implemented_steps = P7_R52_R6_IMPLEMENTED_STEPS if r6.get("r52_6_disposal_safety_gate_built") is True else P7_R52_R5_IMPLEMENTED_STEPS
        not_yet_steps = P7_R52_R6_NOT_YET_IMPLEMENTED_STEPS if r6.get("r52_6_disposal_safety_gate_built") is True else P7_R52_R5_NOT_YET_IMPLEMENTED_STEPS
        r7_built = False
    elif execution_open:
        decision_ref = "R52_BLOCKED_BY_EXECUTION_BLOCKER_OPEN"
        decision_status = "BLOCKED"
        gate_status = "R52_EXECUTION_BLOCKER_GATE_BLOCKED_BY_EXECUTION_BLOCKER_OPEN"
        p5_status = "R52_P5_BLOCKED_BY_EXECUTION_BLOCKER"
        reasons = dedupe_identifiers(["r51_execution_blocker_open", "r51_execution_blocker_open_before_p5_p6_p8_decision"], limit=40, max_length=220)
        next_step = P7_R52_R7_BLOCKED_NEXT_REQUIRED_STEP_REF
        implemented_steps = P7_R52_R7_IMPLEMENTED_STEPS
        not_yet_steps = P7_R52_R7_NOT_YET_IMPLEMENTED_STEPS
        r7_built = True
    elif r4.get("r51_actual_review_evidence_complete") is not True:
        decision_ref = "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED"
        decision_status = "RETURN_REQUIRED"
        gate_status = "R52_EXECUTION_BLOCKER_GATE_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED"
        p5_status = "R52_P5_NOT_REVIEWED_EVIDENCE_MISSING"
        reasons = dedupe_identifiers([*(r4.get("missing_evidence_refs") or []), "r52_7_no_open_execution_blocker_but_actual_review_evidence_still_incomplete"], limit=120, max_length=220)
        next_step = P7_R52_R5_RETURN_TO_R51_NEXT_REQUIRED_STEP_REF
        implemented_steps = P7_R52_R7_IMPLEMENTED_STEPS
        not_yet_steps = P7_R52_R7_NOT_YET_IMPLEMENTED_STEPS
        r7_built = True
    else:
        decision_ref = "R52_NO_GO_P6_P8_START"
        decision_status = "CANDIDATE_ONLY"
        gate_status = "R52_EXECUTION_BLOCKER_GATE_PASSED"
        p5_status = "R52_P5_CONFIRMED_CANDIDATE_REVIEWED_NOT_FINAL"
        reasons = ["r51_execution_blocker_absent_continue_to_r52_8_rating_question_consistency_without_auto_allow"]
        next_step = P7_R52_R7_NEXT_REQUIRED_STEP_REF
        implemented_steps = P7_R52_R7_IMPLEMENTED_STEPS
        not_yet_steps = P7_R52_R7_NOT_YET_IMPLEMENTED_STEPS
        r7_built = True

    gate = {
        "schema_version": P7_R52_EXECUTION_BLOCKER_GATE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R52_STEP,
        "scope": P7_R52_SCOPE,
        "policy_kind": P7_R52_POLICY_KIND,
        "policy_section": P7_R52_R7_STEP_REF,
        "current_phase": "P7",
        "material_id": "p7_r52_execution_blocker_gate",
        "review_session_id": clean_identifier(r6.get("review_session_id"), default=P7_R52_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "r6_disposal_schema_version": P7_R52_DISPOSAL_SAFETY_GATE_SCHEMA_VERSION,
        "r6_disposal_material_ref": clean_identifier(r6.get("material_id"), default="p7_r52_disposal_safety_gate", max_length=180),
        "r6_decision_ref": clean_identifier(r6.get("decision_ref"), default="R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED", max_length=180),
        "r6_decision_status": clean_identifier(r6.get("decision_status"), default="RETURN_REQUIRED", max_length=80),
        "r6_disposal_safety_gate_status": clean_identifier(r6.get("disposal_safety_gate_status"), default="R52_DISPOSAL_SAFETY_GATE_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED", max_length=160),
        "r6_disposal_gate_status": clean_identifier(r6.get("disposal_safety_gate_status"), default="R52_DISPOSAL_SAFETY_GATE_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED", max_length=160),
        "r6_ready_for_r52_7_execution_blocker_gate": r6_ready,
        "r4_completeness_schema_version": P7_R52_ACTUAL_REVIEW_EVIDENCE_COMPLETENESS_SCHEMA_VERSION,
        "r4_completeness_material_ref": clean_identifier(r4.get("material_id"), default="p7_r52_actual_review_evidence_completeness", max_length=180),
        "r51_actual_review_evidence_complete": r4.get("r51_actual_review_evidence_complete") is True,
        "open_execution_blocker_count": open_count,
        "execution_blocker_open": execution_open,
        "execution_blocker_gate_status": gate_status,
        "execution_blocker_reason_refs": dedupe_identifiers(reasons if execution_open else [], limit=40, max_length=220),
        "decision_ref": decision_ref,
        "decision_status": decision_status,
        "decision_reason_refs": reasons,
        "next_required_step": next_step,
        "p5_decision_status": p5_status,
        "p6_limited_human_readfeel_start_allowed_candidate": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_question_design_material_candidate": False,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "r52_0_current_received_snapshot_refrozen": True,
        "r52_1_validation_evidence_matrix_frozen": True,
        "r52_2_r51_bodyfree_handoff_intake_contract_built": True,
        "r52_3_forbidden_payload_deep_scan_built": r4.get("r52_3_forbidden_payload_deep_scan_built") is True,
        "r52_4_actual_review_evidence_completeness_checker_built": r4.get("r52_4_actual_review_evidence_completeness_checker_built") is True,
        "r52_5_evidence_missing_no_go_branch_built": r6.get("r52_5_evidence_missing_no_go_branch_built") is True,
        "r52_6_disposal_safety_gate_built": r6.get("r52_6_disposal_safety_gate_built") is True,
        "r52_7_execution_blocker_gate_built": r7_built,
        "implemented_steps": list(implemented_steps),
        "not_yet_implemented_steps": list(not_yet_steps),
        "first_next_work_ref": P7_R52_FIRST_NEXT_WORK_REF,
        "public_contract": public_contract_flags(),
        "r52_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_r52_false_flags_r6_r7(),
    }
    assert_p7_r52_execution_blocker_gate_contract(gate)
    return gate


def assert_p7_r52_execution_blocker_gate_contract(gate: Mapping[str, Any]) -> bool:
    data = safe_mapping(gate)
    _assert_required_fields(data, required=P7_R52_EXECUTION_BLOCKER_GATE_REQUIRED_FIELD_REFS, source="p7_r52_r7_execution_blocker_gate")
    _assert_body_free_common(data, schema_version=P7_R52_EXECUTION_BLOCKER_GATE_SCHEMA_VERSION, source="p7_r52_r7_execution_blocker_gate")
    for false_key in P7_R52_R6_R7_FALSE_KEY_REFS:
        if data.get(false_key) is not False:
            raise ValueError(f"R52 R7 must keep {false_key}=False")
    if data.get("policy_section") != P7_R52_R7_STEP_REF:
        raise ValueError("R52 R7 policy section changed")
    if data.get("r6_disposal_schema_version") != P7_R52_DISPOSAL_SAFETY_GATE_SCHEMA_VERSION:
        raise ValueError("R52 R7 must read R52-6 material")
    if data.get("execution_blocker_gate_status") not in P7_R52_EXECUTION_BLOCKER_GATE_STATUS_REFS:
        raise ValueError("R52 R7 status changed")
    if data.get("decision_ref") not in P7_R52_R7_DECISION_REF_REFS or data.get("decision_status") not in P7_R52_R5_DECISION_STATUS_REFS:
        raise ValueError("R52 R7 decision changed")
    if not isinstance(data.get("open_execution_blocker_count"), int) or data["open_execution_blocker_count"] < 0:
        raise ValueError("R52 R7 open blocker count must be non-negative")
    if data.get("execution_blocker_open") is not (data["open_execution_blocker_count"] > 0):
        raise ValueError("R52 R7 open blocker flag must match count")
    if data.get("r6_decision_ref") == "R52_BLOCKED_BY_DISPOSAL_NOT_VERIFIED":
        if data.get("decision_ref") != "R52_BLOCKED_BY_DISPOSAL_NOT_VERIFIED" or data.get("r52_7_execution_blocker_gate_built") is not False:
            raise ValueError("R52 R7 must preserve disposal blocker and not build")
    elif data.get("r6_decision_ref") == "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK":
        if data.get("decision_ref") != "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK" or data.get("r52_7_execution_blocker_gate_built") is not False:
            raise ValueError("R52 R7 must preserve boundary blocker and not build")
    elif data.get("r6_ready_for_r52_7_execution_blocker_gate") is not True:
        if data.get("decision_ref") == "R52_BLOCKED_BY_EXECUTION_BLOCKER_OPEN" or data.get("r52_7_execution_blocker_gate_built") is not False:
            raise ValueError("R52 R7 must not evaluate before R52-6 passes")
    elif data.get("execution_blocker_open") is True:
        if data.get("execution_blocker_gate_status") != "R52_EXECUTION_BLOCKER_GATE_BLOCKED_BY_EXECUTION_BLOCKER_OPEN":
            raise ValueError("R52 R7 open execution blocker status must block")
        if data.get("decision_ref") != "R52_BLOCKED_BY_EXECUTION_BLOCKER_OPEN" or data.get("decision_status") != "BLOCKED":
            raise ValueError("R52 R7 open execution blocker must block")
        if "r51_execution_blocker_open" not in data.get("execution_blocker_reason_refs", []):
            raise ValueError("R52 R7 open execution blocker must keep body-free reason ref")
        if data.get("p5_decision_status") != "R52_P5_BLOCKED_BY_EXECUTION_BLOCKER":
            raise ValueError("R52 R7 must set execution blocker P5 status")
        if data.get("next_required_step") != P7_R52_R7_BLOCKED_NEXT_REQUIRED_STEP_REF or data.get("r52_7_execution_blocker_gate_built") is not True:
            raise ValueError("R52 R7 execution blocker must point to resolution and mark built")
    elif data.get("r51_actual_review_evidence_complete") is not True:
        if data.get("decision_ref") != "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED" or data.get("decision_status") != "RETURN_REQUIRED":
            raise ValueError("R52 R7 incomplete evidence without open blockers must return to R51")
        if data.get("execution_blocker_gate_status") != "R52_EXECUTION_BLOCKER_GATE_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED":
            raise ValueError("R52 R7 incomplete evidence status must return to R51")
        if data.get("r52_7_execution_blocker_gate_built") is not True:
            raise ValueError("R52 R7 incomplete evidence check must mark built")
    else:
        if data.get("decision_ref") != "R52_NO_GO_P6_P8_START" or data.get("decision_status") != "CANDIDATE_ONLY":
            raise ValueError("R52 R7 passed gate must remain no-go candidate-only")
        if data.get("next_required_step") != P7_R52_R7_NEXT_REQUIRED_STEP_REF or data.get("r52_7_execution_blocker_gate_built") is not True:
            raise ValueError("R52 R7 passed gate must continue to R52-8 and mark built")
    if data.get("p6_limited_human_readfeel_start_allowed_candidate") is not False or data.get("p8_question_design_material_candidate") is not False:
        raise ValueError("R52 R7 must not expose P6/P8 candidates")
    if data.get("p6_limited_human_readfeel_start_allowed") is not False or data.get("p8_start_allowed") is not False or data.get("p7_complete") is not False or data.get("release_allowed") is not False:
        raise ValueError("R52 R7 must not allow P6/P8/P7/release")
    return True


def build_p7_r52_r0_r7_disposal_execution_gate_chain(
    *,
    current_received_snapshot_refreeze: Mapping[str, Any] | None = None,
    validation_evidence_matrix_freeze: Mapping[str, Any] | None = None,
    r51_bodyfree_handoff_materials: Sequence[Mapping[str, Any]] | None = None,
    r51_actual_review_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return R52-7 material after validating the R52-0/R52-7 body-free chain."""

    r0 = (
        safe_mapping(current_received_snapshot_refreeze)
        if current_received_snapshot_refreeze is not None
        else build_p7_r52_current_received_snapshot_refreeze()
    )
    assert_p7_r52_current_received_snapshot_refreeze_contract(r0)
    r1 = (
        safe_mapping(validation_evidence_matrix_freeze)
        if validation_evidence_matrix_freeze is not None
        else build_p7_r52_validation_evidence_matrix_freeze(current_received_snapshot_refreeze=r0)
    )
    assert_p7_r52_validation_evidence_matrix_freeze_contract(r1)
    r3 = build_p7_r52_r0_r3_r51_bodyfree_intake_forbidden_scan_chain(
        current_received_snapshot_refreeze=r0,
        validation_evidence_matrix_freeze=r1,
        r51_bodyfree_handoff_materials=r51_bodyfree_handoff_materials,
    )
    assert_p7_r52_forbidden_payload_deep_scan_contract(r3)
    r4 = build_p7_r52_actual_review_evidence_completeness(
        forbidden_payload_deep_scan=r3,
        r51_actual_review_evidence=r51_actual_review_evidence,
    )
    assert_p7_r52_actual_review_evidence_completeness_contract(r4)
    r5 = build_p7_r52_evidence_missing_no_go_branch(actual_review_evidence_completeness=r4)
    assert_p7_r52_evidence_missing_no_go_branch_contract(r5)
    r6 = build_p7_r52_disposal_safety_gate(
        evidence_missing_no_go_branch=r5,
        actual_review_evidence_completeness=r4,
        r51_actual_review_evidence=r51_actual_review_evidence,
    )
    assert_p7_r52_disposal_safety_gate_contract(r6)
    r7 = build_p7_r52_execution_blocker_gate(
        disposal_safety_gate=r6,
        actual_review_evidence_completeness=r4,
        r51_actual_review_evidence=r51_actual_review_evidence,
    )
    assert_p7_r52_execution_blocker_gate_contract(r7)
    return r7


# ---------------------------------------------------------------------------
# R52-8 / R52-9: rating-question consistency gate + P5 readfeel blocker gate.
# ---------------------------------------------------------------------------

P7_R52_RATING_QUESTION_CONSISTENCY_GATE_SCHEMA_VERSION: Final = "cocolon.emlis.p7_r52.rating_question_consistency_gate.bodyfree.v1"
P7_R52_P5_READFEEL_BLOCKER_GATE_SCHEMA_VERSION: Final = "cocolon.emlis.p7_r52.p5_readfeel_blocker_gate.bodyfree.v1"

P7_R52_R8_STEP_REF: Final = "R52-8_rating_question_consistency_gate"
P7_R52_R9_STEP_REF: Final = "R52-9_p5_readfeel_blocker_gate"
P7_R52_R8_NEXT_REQUIRED_STEP_REF: Final = P7_R52_R9_STEP_REF
P7_R52_R8_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "return_to_P5_repair_or_R51_review_before_P8_question_material_candidate"
P7_R52_R9_NEXT_REQUIRED_STEP_REF: Final = "R52-10_p5_confirmed_candidate_decision"
P7_R52_R9_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "return_to_P5_readfeel_repair_before_P6_P8_decision"

P7_R52_FUTURE_STEPS_AFTER_R9: Final[tuple[str, ...]] = P7_R52_FUTURE_STEPS_AFTER_R7[2:]
P7_R52_R8_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R52_R7_IMPLEMENTED_STEPS, P7_R52_R8_STEP_REF)
P7_R52_R8_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R52_R9_STEP_REF, *P7_R52_FUTURE_STEPS_AFTER_R9)
P7_R52_R9_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R52_R8_IMPLEMENTED_STEPS, P7_R52_R9_STEP_REF)
P7_R52_R9_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R52_FUTURE_STEPS_AFTER_R9
P7_R52_CURRENT_IMPLEMENTED_STEPS = P7_R52_R9_IMPLEMENTED_STEPS
P7_R52_CURRENT_NOT_YET_IMPLEMENTED_STEPS = P7_R52_R9_NOT_YET_IMPLEMENTED_STEPS

P7_R52_R8_DECISION_REF_REFS: Final[tuple[str, ...]] = (
    "R52_NO_GO_P6_P8_START",
    "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED",
    "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK",
    "R52_BLOCKED_BY_DISPOSAL_NOT_VERIFIED",
    "R52_BLOCKED_BY_EXECUTION_BLOCKER_OPEN",
    "R52_BLOCKED_BY_RATING_QUESTION_OBSERVATION_INCONSISTENCY",
)
P7_R52_R9_DECISION_REF_REFS: Final[tuple[str, ...]] = (
    *P7_R52_R8_DECISION_REF_REFS,
    "R52_RETURN_TO_P5_REPAIR_REQUIRED",
)

P7_R52_R8_GATE_STATUS_REFS: Final[tuple[str, ...]] = (
    "R52_RATING_QUESTION_CONSISTENCY_GATE_PASSED",
    "R52_RATING_QUESTION_CONSISTENCY_GATE_BLOCKED_BY_CONSISTENCY_ISSUE",
    "R52_RATING_QUESTION_CONSISTENCY_GATE_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED",
    "R52_RATING_QUESTION_CONSISTENCY_GATE_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK",
    "R52_RATING_QUESTION_CONSISTENCY_GATE_BLOCKED_BY_DISPOSAL_NOT_VERIFIED",
    "R52_RATING_QUESTION_CONSISTENCY_GATE_BLOCKED_BY_EXECUTION_BLOCKER_OPEN",
    "R52_RATING_QUESTION_CONSISTENCY_GATE_NOT_REACHED_BY_R7",
)
P7_R52_R9_GATE_STATUS_REFS: Final[tuple[str, ...]] = (
    "R52_P5_READFEEL_BLOCKER_GATE_PASSED",
    "R52_P5_READFEEL_BLOCKER_GATE_RETURN_TO_P5_REPAIR_REQUIRED",
    "R52_P5_READFEEL_BLOCKER_GATE_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED",
    "R52_P5_READFEEL_BLOCKER_GATE_BLOCKED_BY_CONSISTENCY_ISSUE",
    "R52_P5_READFEEL_BLOCKER_GATE_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK",
    "R52_P5_READFEEL_BLOCKER_GATE_BLOCKED_BY_DISPOSAL_NOT_VERIFIED",
    "R52_P5_READFEEL_BLOCKER_GATE_BLOCKED_BY_EXECUTION_BLOCKER_OPEN",
    "R52_P5_READFEEL_BLOCKER_GATE_NOT_REACHED_BY_R8",
)

P7_R52_R8_R9_EXTRA_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    "r52_rating_question_consistency_repaired_here",
    "r52_rating_question_observation_rows_materialized_here",
    "repair_required_not_question_promoted_to_p8_candidate_here",
    "red_or_repair_required_question_candidate_promoted_here",
    "r52_p5_readfeel_blocker_resolved_here",
    "p5_readfeel_blocker_ignored_for_p6_p8_start_here",
    "p5_readfeel_blocker_ignored_for_p8_material_here",
    "p5_repair_required_hidden_by_p6_or_p8_candidate_here",
    "p5_repair_return_candidate",
    "p5_human_blind_qa_confirmed_candidate",
)
P7_R52_R8_R9_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    *P7_R52_R6_R7_FALSE_KEY_REFS,
    *P7_R52_R8_R9_EXTRA_FALSE_KEY_REFS,
)

P7_R52_R8_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "current_phase", "material_id",
    "review_session_id", "required_case_count", "r7_execution_schema_version", "r7_execution_material_ref",
    "r7_decision_ref", "r7_decision_status", "r7_execution_blocker_gate_status", "r7_ready_for_r52_8_rating_question_consistency_gate",
    "r51_actual_review_evidence_complete", "rating_question_consistency_status", "rating_question_consistency_passed",
    "repair_required_not_question_count", "p8_candidate_repair_required_not_question_count", "red_or_repair_required_question_candidate_count",
    "red_question_candidate_count", "repair_required_question_candidate_count", "repair_required_not_question_mixed_into_p8_candidate",
    "red_or_repair_required_treated_as_question_candidate", "p5_weakness_not_hidden_by_question_candidate", "rating_question_consistency_issue_detected",
    "rating_question_consistency_issue_reason_refs", "rating_question_consistency_gate_status", "decision_ref", "decision_status", "decision_reason_refs",
    "next_required_step", "p5_decision_status", "p6_limited_human_readfeel_start_allowed_candidate", "p6_limited_human_readfeel_start_allowed",
    "p8_question_design_material_candidate", "p8_start_allowed", "p7_complete", "release_allowed", "r52_0_current_received_snapshot_refrozen",
    "r52_1_validation_evidence_matrix_frozen", "r52_2_r51_bodyfree_handoff_intake_contract_built", "r52_3_forbidden_payload_deep_scan_built",
    "r52_4_actual_review_evidence_completeness_checker_built", "r52_5_evidence_missing_no_go_branch_built", "r52_6_disposal_safety_gate_built",
    "r52_7_execution_blocker_gate_built", "r52_8_rating_question_consistency_gate_built", "r52_8_ready_for_r52_9_p5_readfeel_blocker_gate",
    "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "public_contract", "r52_public_no_touch_contract", "body_free_markers", "body_free",
    *P7_R52_R8_R9_FALSE_KEY_REFS,
)

P7_R52_R9_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "current_phase", "material_id",
    "review_session_id", "required_case_count", "r8_consistency_schema_version", "r8_consistency_material_ref", "r8_decision_ref",
    "r8_decision_status", "r8_rating_question_consistency_gate_status", "r8_ready_for_r52_9_p5_readfeel_blocker_gate",
    "r51_actual_review_evidence_complete", "all_axis_targets_met", "axis_target_missed_refs", "axis_target_missed_count",
    "red_count", "repair_required_count", "critical_repair_blocker_count", "creepy_or_surveillance_blocker_count", "overclaim_blocker_count",
    "self_blame_amplification_blocker_count", "p5_surface_or_gate_repair_observation_count", "emlis_readfeel_repair_observation_count",
    "history_connection_naturalness_below_target_count", "p5_readfeel_blocker_present", "p5_readfeel_blocker_detected", "p5_readfeel_repair_required", "p5_readfeel_blocker_reason_refs",
    "p5_readfeel_blocker_gate_status", "decision_ref", "decision_status", "decision_reason_refs", "next_required_step", "p5_decision_status",
    "p6_limited_human_readfeel_start_allowed_candidate", "p6_limited_human_readfeel_start_allowed", "p8_question_design_material_candidate", "p8_start_allowed",
    "p7_complete", "release_allowed", "r52_0_current_received_snapshot_refrozen", "r52_1_validation_evidence_matrix_frozen", "r52_2_r51_bodyfree_handoff_intake_contract_built",
    "r52_3_forbidden_payload_deep_scan_built", "r52_4_actual_review_evidence_completeness_checker_built", "r52_5_evidence_missing_no_go_branch_built",
    "r52_6_disposal_safety_gate_built", "r52_7_execution_blocker_gate_built", "r52_8_rating_question_consistency_gate_built", "r52_9_p5_readfeel_blocker_gate_built",
    "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "public_contract", "r52_public_no_touch_contract", "body_free_markers", "body_free",
    *P7_R52_R8_R9_FALSE_KEY_REFS,
)

# Backward-compatible long names used by the split R52-8/R52-9 tests.
P7_R52_RATING_QUESTION_CONSISTENCY_GATE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = P7_R52_R8_REQUIRED_FIELD_REFS
P7_R52_P5_READFEEL_BLOCKER_GATE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = P7_R52_R9_REQUIRED_FIELD_REFS


def _r52_false_flags_r8_r9() -> dict[str, bool]:
    return {key: False for key in P7_R52_R8_R9_FALSE_KEY_REFS}


def _r52_clean_sequence(value: Any, *, limit: int = 80, max_length: int = 220) -> list[str]:
    if isinstance(value, str):
        return dedupe_identifiers([value], limit=limit, max_length=max_length)
    if _is_sequence_not_string(value):
        return dedupe_identifiers([clean_identifier(item, default="", max_length=max_length) for item in value], limit=limit, max_length=max_length)
    return []


def _r52_r7_ready_for_rating_question_consistency_gate(r7: Mapping[str, Any]) -> bool:
    return (
        r7.get("decision_ref") == "R52_NO_GO_P6_P8_START"
        and r7.get("decision_status") == "CANDIDATE_ONLY"
        and r7.get("execution_blocker_open") is False
        and r7.get("r51_actual_review_evidence_complete") is True
        and r7.get("r52_7_execution_blocker_gate_built") is True
    )


def _r52_rating_question_consistency_values(evidence: Mapping[str, Any] | None) -> dict[str, Any]:
    material = safe_mapping(evidence)
    status = clean_identifier(material.get("rating_question_consistency_status"), default="missing", max_length=120).lower()
    passed = status == "passed"
    repair_required_not_question_count = _r52_evidence_int(material, "repair_required_not_question_count")
    p8_candidate_repair_count = _r52_evidence_int(material, "p8_candidate_repair_required_not_question_count", "repair_required_not_question_p8_candidate_count")
    red_question_count = _r52_evidence_int(material, "red_question_candidate_count")
    repair_question_count = _r52_evidence_int(material, "repair_required_question_candidate_count")
    red_or_repair_question_count = _r52_evidence_int(material, "red_or_repair_required_question_candidate_count") + red_question_count + repair_question_count
    mixed = _r52_evidence_bool(material, "repair_required_not_question_mixed_into_p8_candidate", default=False)
    treated = _r52_evidence_bool(material, "red_or_repair_required_treated_as_question_candidate", default=False)
    p5_not_hidden = _r52_evidence_bool(material, "p5_weakness_not_hidden_by_question_candidate", default=True)
    reasons: list[str] = []
    if not passed:
        reasons.extend(["r51_rating_question_consistency_status_not_passed", "r51_rating_question_consistency_not_passed"])
    if repair_required_not_question_count > 0:
        reasons.append("repair_required_not_question_must_not_be_classified_as_p8_material")
    if p8_candidate_repair_count > 0 or mixed:
        reasons.extend(["repair_required_not_question_misclassified_as_p8_candidate", "repair_required_not_question_mixed_into_p8_candidate"])
    if red_or_repair_question_count > 0 or treated:
        reasons.extend(["red_or_repair_required_routed_to_question_candidate", "red_or_repair_required_treated_as_question_candidate"])
    if not p5_not_hidden:
        reasons.append("p5_weakness_hidden_by_question_candidate")
    reason_refs = dedupe_identifiers(reasons, limit=80, max_length=220)
    return {
        "rating_question_consistency_status": status,
        "rating_question_consistency_passed": passed,
        "repair_required_not_question_count": repair_required_not_question_count,
        "p8_candidate_repair_required_not_question_count": p8_candidate_repair_count,
        "red_or_repair_required_question_candidate_count": red_or_repair_question_count,
        "red_question_candidate_count": red_question_count,
        "repair_required_question_candidate_count": repair_question_count,
        "repair_required_not_question_mixed_into_p8_candidate": mixed,
        "red_or_repair_required_treated_as_question_candidate": treated,
        "p5_weakness_not_hidden_by_question_candidate": p5_not_hidden,
        "rating_question_consistency_issue_detected": bool(reason_refs),
        "rating_question_consistency_issue_reason_refs": reason_refs,
    }


def _r52_p5_readfeel_blocker_values(evidence: Mapping[str, Any] | None) -> dict[str, Any]:
    material = safe_mapping(evidence)
    axis_missed_refs = _r52_clean_sequence(material.get("axis_target_missed_refs"), limit=80, max_length=220)
    all_axis_targets_met = _r52_evidence_bool(material, "all_axis_targets_met", default=False)
    counts = {
        "red_count": _r52_evidence_int(material, "red_count"),
        "repair_required_count": _r52_evidence_int(material, "repair_required_count"),
        "critical_repair_blocker_count": _r52_evidence_int(material, "critical_repair_blocker_count"),
        "creepy_or_surveillance_blocker_count": _r52_evidence_int(material, "creepy_or_surveillance_blocker_count"),
        "overclaim_blocker_count": _r52_evidence_int(material, "overclaim_blocker_count"),
        "self_blame_amplification_blocker_count": _r52_evidence_int(material, "self_blame_amplification_blocker_count"),
        "p5_surface_or_gate_repair_observation_count": _r52_evidence_int(material, "p5_surface_or_gate_repair_observation_count"),
        "emlis_readfeel_repair_observation_count": _r52_evidence_int(material, "emlis_readfeel_repair_observation_count"),
        "history_connection_naturalness_below_target_count": _r52_evidence_int(material, "history_connection_naturalness_below_target_count"),
    }
    reasons: list[str] = []
    if counts["red_count"] > 0:
        reasons.extend(["r51_red_count_positive", "r51_red_verdict_present"])
    if counts["repair_required_count"] > 0:
        reasons.extend(["r51_repair_required_count_positive", "r51_repair_required_verdict_present"])
    if counts["critical_repair_blocker_count"] > 0:
        reasons.extend(["r51_critical_repair_blocker_count_positive", "r51_critical_repair_blocker_present"])
    if counts["creepy_or_surveillance_blocker_count"] > 0:
        reasons.extend(["r51_creepy_or_surveillance_blocker_count_positive", "r51_creepy_or_surveillance_blocker_present"])
    if counts["overclaim_blocker_count"] > 0:
        reasons.extend(["r51_overclaim_blocker_count_positive", "r51_overclaim_blocker_present"])
    if counts["self_blame_amplification_blocker_count"] > 0:
        reasons.extend(["r51_self_blame_amplification_blocker_count_positive", "r51_self_blame_amplification_blocker_present"])
    if counts["p5_surface_or_gate_repair_observation_count"] > 0:
        reasons.extend(["r51_p5_surface_or_gate_repair_observation_count_positive", "r51_p5_surface_or_gate_repair_observation_present"])
    if counts["emlis_readfeel_repair_observation_count"] > 0:
        reasons.extend(["r51_emlis_readfeel_repair_observation_count_positive", "r51_emlis_readfeel_repair_observation_present"])
    if counts["history_connection_naturalness_below_target_count"] > 0:
        reasons.append("history_connection_naturalness_below_target")
    if axis_missed_refs:
        reasons.append("r51_axis_target_missed")
        reasons.extend(axis_missed_refs)
    if not all_axis_targets_met:
        reasons.append("r51_axis_targets_not_met")
    reason_refs = dedupe_identifiers(reasons, limit=160, max_length=220)
    return {
        "all_axis_targets_met": all_axis_targets_met,
        "axis_target_missed_refs": axis_missed_refs,
        "axis_target_missed_count": len(axis_missed_refs),
        **counts,
        "p5_readfeel_blocker_present": bool(reason_refs),
        "p5_readfeel_blocker_detected": bool(reason_refs),
        "p5_readfeel_repair_required": bool(reason_refs),
        "p5_readfeel_blocker_reason_refs": reason_refs,
    }


def build_p7_r52_rating_question_consistency_gate(
    *,
    execution_blocker_gate: Mapping[str, Any] | None = None,
    r51_actual_review_evidence: Mapping[str, Any] | None = None,
    current_received_snapshot_refreeze: Mapping[str, Any] | None = None,
    validation_evidence_matrix_freeze: Mapping[str, Any] | None = None,
    r51_bodyfree_handoff_materials: Sequence[Mapping[str, Any]] | None = None,
    material_id: str = "p7_r52_rating_question_consistency_gate",
) -> dict[str, Any]:
    """Build R52-8 without creating question text, P8 material, or review rows."""

    r7 = safe_mapping(execution_blocker_gate) if execution_blocker_gate is not None else build_p7_r52_r0_r7_disposal_execution_gate_chain(
        current_received_snapshot_refreeze=current_received_snapshot_refreeze,
        validation_evidence_matrix_freeze=validation_evidence_matrix_freeze,
        r51_bodyfree_handoff_materials=r51_bodyfree_handoff_materials,
        r51_actual_review_evidence=r51_actual_review_evidence,
    )
    assert_p7_r52_execution_blocker_gate_contract(r7)
    values = _r52_rating_question_consistency_values(r51_actual_review_evidence)
    r7_ready = _r52_r7_ready_for_rating_question_consistency_gate(r7)
    prior = clean_identifier(r7.get("decision_ref"), default="R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED", max_length=180)

    if prior == "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK":
        decision_ref, decision_status = prior, "BLOCKED"
        gate_status = "R52_RATING_QUESTION_CONSISTENCY_GATE_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK"
        p5_status = "R52_P5_BLOCKED_BY_BOUNDARY_RISK"
        reasons = dedupe_identifiers([*(r7.get("decision_reason_refs") or []), "r52_8_blocked_by_prior_body_free_boundary_risk"], limit=120, max_length=220)
        next_step = clean_identifier(r7.get("next_required_step"), default=P7_R52_R4_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220)
        implemented_steps, not_yet_steps, built = P7_R52_R7_IMPLEMENTED_STEPS, P7_R52_R7_NOT_YET_IMPLEMENTED_STEPS, False
    elif prior == "R52_BLOCKED_BY_DISPOSAL_NOT_VERIFIED":
        decision_ref, decision_status = prior, "BLOCKED"
        gate_status = "R52_RATING_QUESTION_CONSISTENCY_GATE_BLOCKED_BY_DISPOSAL_NOT_VERIFIED"
        p5_status = "R52_P5_BLOCKED_BY_DISPOSAL_NOT_VERIFIED"
        reasons = dedupe_identifiers([*(r7.get("decision_reason_refs") or []), "r52_8_blocked_by_prior_disposal_not_verified"], limit=120, max_length=220)
        next_step = clean_identifier(r7.get("next_required_step"), default=P7_R52_R6_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220)
        implemented_steps, not_yet_steps, built = P7_R52_R7_IMPLEMENTED_STEPS, P7_R52_R7_NOT_YET_IMPLEMENTED_STEPS, False
    elif prior == "R52_BLOCKED_BY_EXECUTION_BLOCKER_OPEN":
        decision_ref, decision_status = prior, "BLOCKED"
        gate_status = "R52_RATING_QUESTION_CONSISTENCY_GATE_BLOCKED_BY_EXECUTION_BLOCKER_OPEN"
        p5_status = "R52_P5_BLOCKED_BY_EXECUTION_BLOCKER"
        reasons = dedupe_identifiers([*(r7.get("decision_reason_refs") or []), "r52_8_blocked_by_prior_execution_blocker_open"], limit=120, max_length=220)
        next_step = clean_identifier(r7.get("next_required_step"), default=P7_R52_R7_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220)
        implemented_steps, not_yet_steps, built = P7_R52_R7_IMPLEMENTED_STEPS, P7_R52_R7_NOT_YET_IMPLEMENTED_STEPS, False
    elif not r7_ready:
        decision_ref = prior
        decision_status = clean_identifier(r7.get("decision_status"), default="RETURN_REQUIRED", max_length=80)
        gate_status = "R52_RATING_QUESTION_CONSISTENCY_GATE_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED" if prior == "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED" else "R52_RATING_QUESTION_CONSISTENCY_GATE_NOT_REACHED_BY_R7"
        p5_status = clean_identifier(r7.get("p5_decision_status"), default="R52_P5_NOT_REVIEWED_EVIDENCE_MISSING", max_length=180)
        reasons = dedupe_identifiers([*(r7.get("decision_reason_refs") or []), "r52_8_not_reached_until_r7_execution_blocker_gate_passes"], limit=120, max_length=220)
        next_step = clean_identifier(r7.get("next_required_step"), default=P7_R52_R5_RETURN_TO_R51_NEXT_REQUIRED_STEP_REF, max_length=220)
        implemented_steps, not_yet_steps, built = P7_R52_R7_IMPLEMENTED_STEPS, P7_R52_R7_NOT_YET_IMPLEMENTED_STEPS, False
    elif values["rating_question_consistency_issue_detected"] is True:
        decision_ref, decision_status = "R52_BLOCKED_BY_RATING_QUESTION_OBSERVATION_INCONSISTENCY", "BLOCKED"
        gate_status = "R52_RATING_QUESTION_CONSISTENCY_GATE_BLOCKED_BY_CONSISTENCY_ISSUE"
        p5_status = "R52_P5_BLOCKED_BY_CONSISTENCY_ISSUE"
        reasons = values["rating_question_consistency_issue_reason_refs"]
        next_step = P7_R52_R8_BLOCKED_NEXT_REQUIRED_STEP_REF
        implemented_steps, not_yet_steps, built = P7_R52_R8_IMPLEMENTED_STEPS, P7_R52_R8_NOT_YET_IMPLEMENTED_STEPS, True
    else:
        decision_ref, decision_status = "R52_NO_GO_P6_P8_START", "CANDIDATE_ONLY"
        gate_status = "R52_RATING_QUESTION_CONSISTENCY_GATE_PASSED"
        p5_status = "R52_P5_CONFIRMED_CANDIDATE_REVIEWED_NOT_FINAL"
        reasons = ["r51_rating_question_consistency_passed_continue_to_r52_9_p5_readfeel_blocker_without_auto_allow"]
        next_step = P7_R52_R8_NEXT_REQUIRED_STEP_REF
        implemented_steps, not_yet_steps, built = P7_R52_R8_IMPLEMENTED_STEPS, P7_R52_R8_NOT_YET_IMPLEMENTED_STEPS, True

    gate = {
        "schema_version": P7_R52_RATING_QUESTION_CONSISTENCY_GATE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R52_STEP,
        "scope": P7_R52_SCOPE,
        "policy_kind": P7_R52_POLICY_KIND,
        "policy_section": P7_R52_R8_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r52_rating_question_consistency_gate", max_length=180),
        "review_session_id": clean_identifier(r7.get("review_session_id"), default=P7_R52_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "r7_execution_schema_version": P7_R52_EXECUTION_BLOCKER_GATE_SCHEMA_VERSION,
        "r7_execution_material_ref": clean_identifier(r7.get("material_id"), default="p7_r52_execution_blocker_gate", max_length=180),
        "r7_decision_ref": prior,
        "r7_decision_status": clean_identifier(r7.get("decision_status"), default="RETURN_REQUIRED", max_length=80),
        "r7_execution_blocker_gate_status": clean_identifier(r7.get("execution_blocker_gate_status"), default="R52_EXECUTION_BLOCKER_GATE_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED", max_length=180),
        "r7_ready_for_r52_8_rating_question_consistency_gate": r7_ready,
        "r51_actual_review_evidence_complete": r7.get("r51_actual_review_evidence_complete") is True,
        **values,
        "rating_question_consistency_gate_status": gate_status,
        "decision_ref": decision_ref,
        "decision_status": decision_status,
        "decision_reason_refs": reasons,
        "next_required_step": next_step,
        "p5_decision_status": p5_status,
        "p6_limited_human_readfeel_start_allowed_candidate": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_question_design_material_candidate": False,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "r52_0_current_received_snapshot_refrozen": True,
        "r52_1_validation_evidence_matrix_frozen": True,
        "r52_2_r51_bodyfree_handoff_intake_contract_built": True,
        "r52_3_forbidden_payload_deep_scan_built": r7.get("r52_3_forbidden_payload_deep_scan_built") is True,
        "r52_4_actual_review_evidence_completeness_checker_built": r7.get("r52_4_actual_review_evidence_completeness_checker_built") is True,
        "r52_5_evidence_missing_no_go_branch_built": r7.get("r52_5_evidence_missing_no_go_branch_built") is True,
        "r52_6_disposal_safety_gate_built": r7.get("r52_6_disposal_safety_gate_built") is True,
        "r52_7_execution_blocker_gate_built": r7.get("r52_7_execution_blocker_gate_built") is True,
        "r52_8_rating_question_consistency_gate_built": built,
        "r52_8_ready_for_r52_9_p5_readfeel_blocker_gate": built and not values["rating_question_consistency_issue_detected"] and r7_ready,
        "implemented_steps": list(implemented_steps),
        "not_yet_implemented_steps": list(not_yet_steps),
        "first_next_work_ref": P7_R52_FIRST_NEXT_WORK_REF,
        "public_contract": public_contract_flags(),
        "r52_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_r52_false_flags_r8_r9(),
    }
    assert_p7_r52_rating_question_consistency_gate_contract(gate)
    return gate


def assert_p7_r52_rating_question_consistency_gate_contract(gate: Mapping[str, Any]) -> bool:
    data = safe_mapping(gate)
    forbidden_paths = _r52_find_forbidden_key_paths(data, forbidden_keys=P7_R52_FORBIDDEN_PAYLOAD_KEY_REFS, path="p7_r52_r8_rating_question_consistency_gate")
    if forbidden_paths:
        raise ValueError(f"R52 R8 must remain body-free: {forbidden_paths[:6]}")
    missing = [field for field in P7_R52_R8_REQUIRED_FIELD_REFS if field not in data]
    if missing:
        raise ValueError(f"p7_r52_r8_rating_question_consistency_gate missing required fields: {missing[:6]}")
    if set(data) != set(P7_R52_R8_REQUIRED_FIELD_REFS):
        raise ValueError("R52 R8 must not contain body payload, question text, path, hash, or extra fields")
    _assert_body_free_common(data, schema_version=P7_R52_RATING_QUESTION_CONSISTENCY_GATE_SCHEMA_VERSION, source="p7_r52_r8_rating_question_consistency_gate")
    if data.get("policy_section") != P7_R52_R8_STEP_REF:
        raise ValueError("R52 R8 policy section changed")
    for false_key in P7_R52_R8_R9_FALSE_KEY_REFS:
        if data.get(false_key) is not False:
            raise ValueError(f"R52 R8 must keep {false_key}=False")
    if data.get("decision_ref") not in P7_R52_R8_DECISION_REF_REFS or data.get("decision_status") not in P7_R52_R5_DECISION_STATUS_REFS:
        raise ValueError("R52 R8 decision changed")
    if data.get("rating_question_consistency_gate_status") not in P7_R52_R8_GATE_STATUS_REFS:
        raise ValueError("R52 R8 gate status changed")
    expected = _r52_rating_question_consistency_values(data)
    for key in (
        "rating_question_consistency_passed", "repair_required_not_question_count", "p8_candidate_repair_required_not_question_count",
        "red_or_repair_required_question_candidate_count", "red_question_candidate_count", "repair_required_question_candidate_count",
        "repair_required_not_question_mixed_into_p8_candidate", "red_or_repair_required_treated_as_question_candidate",
        "p5_weakness_not_hidden_by_question_candidate", "rating_question_consistency_issue_detected", "rating_question_consistency_issue_reason_refs",
    ):
        if data.get(key) != expected.get(key):
            raise ValueError("R52 R8 consistency values do not match evidence")
    if data.get("r7_ready_for_r52_8_rating_question_consistency_gate") is True and expected["rating_question_consistency_issue_detected"]:
        if data.get("decision_ref") != "R52_BLOCKED_BY_RATING_QUESTION_OBSERVATION_INCONSISTENCY" or data.get("decision_status") != "BLOCKED" or data.get("p5_decision_status") != "R52_P5_BLOCKED_BY_CONSISTENCY_ISSUE" or data.get("next_required_step") != P7_R52_R8_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R52 R8 consistency issue must block")
    if data.get("r7_ready_for_r52_8_rating_question_consistency_gate") is True and not expected["rating_question_consistency_issue_detected"]:
        if data.get("decision_ref") != "R52_NO_GO_P6_P8_START" or data.get("decision_status") != "CANDIDATE_ONLY" or data.get("next_required_step") != P7_R52_R8_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R52 R8 clean gate must continue without auto allow")
    if data.get("p6_limited_human_readfeel_start_allowed_candidate") is not False or data.get("p8_question_design_material_candidate") is not False or data.get("p6_limited_human_readfeel_start_allowed") is not False or data.get("p8_start_allowed") is not False or data.get("p7_complete") is not False or data.get("release_allowed") is not False:
        raise ValueError("R52 R8 must not expose P6/P8 candidates or allow start/release")
    return True


def build_p7_r52_p5_readfeel_blocker_gate(
    *,
    rating_question_consistency_gate: Mapping[str, Any] | None = None,
    r51_actual_review_evidence: Mapping[str, Any] | None = None,
    current_received_snapshot_refreeze: Mapping[str, Any] | None = None,
    validation_evidence_matrix_freeze: Mapping[str, Any] | None = None,
    r51_bodyfree_handoff_materials: Sequence[Mapping[str, Any]] | None = None,
    material_id: str = "p7_r52_p5_readfeel_blocker_gate",
) -> dict[str, Any]:
    """Build R52-9 without fixing P5 or allowing P6/P8 start."""

    r8 = safe_mapping(rating_question_consistency_gate) if rating_question_consistency_gate is not None else build_p7_r52_rating_question_consistency_gate(
        r51_actual_review_evidence=r51_actual_review_evidence,
        current_received_snapshot_refreeze=current_received_snapshot_refreeze,
        validation_evidence_matrix_freeze=validation_evidence_matrix_freeze,
        r51_bodyfree_handoff_materials=r51_bodyfree_handoff_materials,
    )
    assert_p7_r52_rating_question_consistency_gate_contract(r8)
    values = _r52_p5_readfeel_blocker_values(r51_actual_review_evidence)
    r8_ready = r8.get("r52_8_ready_for_r52_9_p5_readfeel_blocker_gate") is True
    prior = clean_identifier(r8.get("decision_ref"), default="R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED", max_length=180)

    if prior == "R52_BLOCKED_BY_RATING_QUESTION_OBSERVATION_INCONSISTENCY":
        decision_ref, decision_status = prior, "BLOCKED"
        gate_status = "R52_P5_READFEEL_BLOCKER_GATE_BLOCKED_BY_CONSISTENCY_ISSUE"
        p5_status = "R52_P5_BLOCKED_BY_CONSISTENCY_ISSUE"
        reasons = dedupe_identifiers([*(r8.get("decision_reason_refs") or []), "r52_9_blocked_by_prior_rating_question_consistency_issue"], limit=160, max_length=220)
        next_step = clean_identifier(r8.get("next_required_step"), default=P7_R52_R8_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220)
        implemented_steps, not_yet_steps, built = P7_R52_R8_IMPLEMENTED_STEPS, P7_R52_R8_NOT_YET_IMPLEMENTED_STEPS, False
    elif prior == "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK":
        decision_ref, decision_status = prior, "BLOCKED"
        gate_status = "R52_P5_READFEEL_BLOCKER_GATE_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK"
        p5_status = "R52_P5_BLOCKED_BY_BOUNDARY_RISK"
        reasons = dedupe_identifiers([*(r8.get("decision_reason_refs") or []), "r52_9_blocked_by_prior_body_free_boundary_risk"], limit=160, max_length=220)
        next_step = clean_identifier(r8.get("next_required_step"), default=P7_R52_R4_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220)
        implemented_steps, not_yet_steps, built = P7_R52_R8_IMPLEMENTED_STEPS, P7_R52_R8_NOT_YET_IMPLEMENTED_STEPS, False
    elif prior == "R52_BLOCKED_BY_DISPOSAL_NOT_VERIFIED":
        decision_ref, decision_status = prior, "BLOCKED"
        gate_status = "R52_P5_READFEEL_BLOCKER_GATE_BLOCKED_BY_DISPOSAL_NOT_VERIFIED"
        p5_status = "R52_P5_BLOCKED_BY_DISPOSAL_NOT_VERIFIED"
        reasons = dedupe_identifiers([*(r8.get("decision_reason_refs") or []), "r52_9_blocked_by_prior_disposal_not_verified"], limit=160, max_length=220)
        next_step = clean_identifier(r8.get("next_required_step"), default=P7_R52_R6_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220)
        implemented_steps, not_yet_steps, built = P7_R52_R8_IMPLEMENTED_STEPS, P7_R52_R8_NOT_YET_IMPLEMENTED_STEPS, False
    elif prior == "R52_BLOCKED_BY_EXECUTION_BLOCKER_OPEN":
        decision_ref, decision_status = prior, "BLOCKED"
        gate_status = "R52_P5_READFEEL_BLOCKER_GATE_BLOCKED_BY_EXECUTION_BLOCKER_OPEN"
        p5_status = "R52_P5_BLOCKED_BY_EXECUTION_BLOCKER"
        reasons = dedupe_identifiers([*(r8.get("decision_reason_refs") or []), "r52_9_blocked_by_prior_execution_blocker_open"], limit=160, max_length=220)
        next_step = clean_identifier(r8.get("next_required_step"), default=P7_R52_R7_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220)
        implemented_steps, not_yet_steps, built = P7_R52_R8_IMPLEMENTED_STEPS, P7_R52_R8_NOT_YET_IMPLEMENTED_STEPS, False
    elif not r8_ready:
        decision_ref = prior
        decision_status = clean_identifier(r8.get("decision_status"), default="RETURN_REQUIRED", max_length=80)
        gate_status = "R52_P5_READFEEL_BLOCKER_GATE_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED" if prior == "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED" else "R52_P5_READFEEL_BLOCKER_GATE_NOT_REACHED_BY_R8"
        p5_status = clean_identifier(r8.get("p5_decision_status"), default="R52_P5_NOT_REVIEWED_EVIDENCE_MISSING", max_length=180)
        reasons = dedupe_identifiers([*(r8.get("decision_reason_refs") or []), "r52_9_not_reached_until_r52_8_rating_question_consistency_passes"], limit=160, max_length=220)
        next_step = clean_identifier(r8.get("next_required_step"), default=P7_R52_R5_RETURN_TO_R51_NEXT_REQUIRED_STEP_REF, max_length=220)
        implemented_steps, not_yet_steps, built = P7_R52_R8_IMPLEMENTED_STEPS, P7_R52_R8_NOT_YET_IMPLEMENTED_STEPS, False
    elif values["p5_readfeel_blocker_detected"] is True:
        decision_ref, decision_status = "R52_RETURN_TO_P5_REPAIR_REQUIRED", "RETURN_REQUIRED"
        gate_status = "R52_P5_READFEEL_BLOCKER_GATE_RETURN_TO_P5_REPAIR_REQUIRED"
        p5_status = "R52_P5_REPAIR_REQUIRED"
        reasons = values["p5_readfeel_blocker_reason_refs"]
        next_step = P7_R52_R9_BLOCKED_NEXT_REQUIRED_STEP_REF
        implemented_steps, not_yet_steps, built = P7_R52_R9_IMPLEMENTED_STEPS, P7_R52_R9_NOT_YET_IMPLEMENTED_STEPS, True
    else:
        decision_ref, decision_status = "R52_NO_GO_P6_P8_START", "CANDIDATE_ONLY"
        gate_status = "R52_P5_READFEEL_BLOCKER_GATE_PASSED"
        p5_status = "R52_P5_CONFIRMED_CANDIDATE_REVIEWED_NOT_FINAL"
        reasons = ["r51_p5_readfeel_no_blocker_continue_to_r52_10_without_auto_allow"]
        next_step = P7_R52_R9_NEXT_REQUIRED_STEP_REF
        implemented_steps, not_yet_steps, built = P7_R52_R9_IMPLEMENTED_STEPS, P7_R52_R9_NOT_YET_IMPLEMENTED_STEPS, True

    gate = {
        "schema_version": P7_R52_P5_READFEEL_BLOCKER_GATE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R52_STEP,
        "scope": P7_R52_SCOPE,
        "policy_kind": P7_R52_POLICY_KIND,
        "policy_section": P7_R52_R9_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r52_p5_readfeel_blocker_gate", max_length=180),
        "review_session_id": clean_identifier(r8.get("review_session_id"), default=P7_R52_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "r8_consistency_schema_version": P7_R52_RATING_QUESTION_CONSISTENCY_GATE_SCHEMA_VERSION,
        "r8_consistency_material_ref": clean_identifier(r8.get("material_id"), default="p7_r52_rating_question_consistency_gate", max_length=180),
        "r8_decision_ref": prior,
        "r8_decision_status": clean_identifier(r8.get("decision_status"), default="RETURN_REQUIRED", max_length=80),
        "r8_rating_question_consistency_gate_status": clean_identifier(r8.get("rating_question_consistency_gate_status"), default="R52_RATING_QUESTION_CONSISTENCY_GATE_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED", max_length=180),
        "r8_ready_for_r52_9_p5_readfeel_blocker_gate": r8_ready,
        "r51_actual_review_evidence_complete": r8.get("r51_actual_review_evidence_complete") is True,
        **values,
        "p5_readfeel_blocker_gate_status": gate_status,
        "decision_ref": decision_ref,
        "decision_status": decision_status,
        "decision_reason_refs": reasons,
        "next_required_step": next_step,
        "p5_decision_status": p5_status,
        "p6_limited_human_readfeel_start_allowed_candidate": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_question_design_material_candidate": False,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "r52_0_current_received_snapshot_refrozen": True,
        "r52_1_validation_evidence_matrix_frozen": True,
        "r52_2_r51_bodyfree_handoff_intake_contract_built": True,
        "r52_3_forbidden_payload_deep_scan_built": r8.get("r52_3_forbidden_payload_deep_scan_built") is True,
        "r52_4_actual_review_evidence_completeness_checker_built": r8.get("r52_4_actual_review_evidence_completeness_checker_built") is True,
        "r52_5_evidence_missing_no_go_branch_built": r8.get("r52_5_evidence_missing_no_go_branch_built") is True,
        "r52_6_disposal_safety_gate_built": r8.get("r52_6_disposal_safety_gate_built") is True,
        "r52_7_execution_blocker_gate_built": r8.get("r52_7_execution_blocker_gate_built") is True,
        "r52_8_rating_question_consistency_gate_built": r8.get("r52_8_rating_question_consistency_gate_built") is True,
        "r52_9_p5_readfeel_blocker_gate_built": built,
        "implemented_steps": list(implemented_steps),
        "not_yet_implemented_steps": list(not_yet_steps),
        "first_next_work_ref": P7_R52_FIRST_NEXT_WORK_REF,
        "public_contract": public_contract_flags(),
        "r52_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_r52_false_flags_r8_r9(),
    }
    assert_p7_r52_p5_readfeel_blocker_gate_contract(gate)
    return gate


def assert_p7_r52_p5_readfeel_blocker_gate_contract(gate: Mapping[str, Any]) -> bool:
    data = safe_mapping(gate)
    forbidden_paths = _r52_find_forbidden_key_paths(data, forbidden_keys=P7_R52_FORBIDDEN_PAYLOAD_KEY_REFS, path="p7_r52_r9_p5_readfeel_blocker_gate")
    if forbidden_paths:
        raise ValueError(f"R52 R9 must remain body-free: {forbidden_paths[:6]}")
    missing = [field for field in P7_R52_R9_REQUIRED_FIELD_REFS if field not in data]
    if missing:
        raise ValueError(f"p7_r52_r9_p5_readfeel_blocker_gate missing required fields: {missing[:6]}")
    if set(data) != set(P7_R52_R9_REQUIRED_FIELD_REFS):
        raise ValueError("R52 R9 must not contain body payload, question text, path, hash, or extra fields")
    _assert_body_free_common(data, schema_version=P7_R52_P5_READFEEL_BLOCKER_GATE_SCHEMA_VERSION, source="p7_r52_r9_p5_readfeel_blocker_gate")
    if data.get("policy_section") != P7_R52_R9_STEP_REF:
        raise ValueError("R52 R9 policy section changed")
    for false_key in P7_R52_R8_R9_FALSE_KEY_REFS:
        if data.get(false_key) is not False:
            raise ValueError(f"R52 R9 must keep {false_key}=False")
    if data.get("decision_ref") not in P7_R52_R9_DECISION_REF_REFS or data.get("decision_status") not in P7_R52_R5_DECISION_STATUS_REFS:
        raise ValueError("R52 R9 decision changed")
    if data.get("p5_readfeel_blocker_gate_status") not in P7_R52_R9_GATE_STATUS_REFS:
        raise ValueError("R52 R9 gate status changed")
    expected = _r52_p5_readfeel_blocker_values(data)
    for key in (
        "all_axis_targets_met", "axis_target_missed_refs", "axis_target_missed_count", "red_count", "repair_required_count",
        "critical_repair_blocker_count", "creepy_or_surveillance_blocker_count", "overclaim_blocker_count", "self_blame_amplification_blocker_count",
        "p5_surface_or_gate_repair_observation_count", "emlis_readfeel_repair_observation_count", "history_connection_naturalness_below_target_count",
        "p5_readfeel_blocker_present", "p5_readfeel_blocker_detected", "p5_readfeel_blocker_reason_refs",
    ):
        if data.get(key) != expected.get(key):
            raise ValueError("R52 R9 readfeel blocker values do not match evidence")
    if data.get("r8_ready_for_r52_9_p5_readfeel_blocker_gate") is True and expected["p5_readfeel_blocker_detected"]:
        if data.get("decision_ref") != "R52_RETURN_TO_P5_REPAIR_REQUIRED" or data.get("decision_status") != "RETURN_REQUIRED" or data.get("p5_decision_status") != "R52_P5_REPAIR_REQUIRED" or data.get("next_required_step") != P7_R52_R9_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R52 R9 P5 readfeel blocker must return to P5 repair")
    if data.get("r8_ready_for_r52_9_p5_readfeel_blocker_gate") is True and not expected["p5_readfeel_blocker_detected"]:
        if data.get("decision_ref") != "R52_NO_GO_P6_P8_START" or data.get("decision_status") != "CANDIDATE_ONLY" or data.get("next_required_step") != P7_R52_R9_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R52 R9 clean gate must continue without auto allow")
    if data.get("p6_limited_human_readfeel_start_allowed_candidate") is not False or data.get("p8_question_design_material_candidate") is not False or data.get("p6_limited_human_readfeel_start_allowed") is not False or data.get("p8_start_allowed") is not False or data.get("p7_complete") is not False or data.get("release_allowed") is not False:
        raise ValueError("R52 R9 must not expose P6/P8 candidates or allow start/release")
    return True


def build_p7_r52_r0_r9_rating_question_p5_readfeel_gate_chain(
    *,
    current_received_snapshot_refreeze: Mapping[str, Any] | None = None,
    validation_evidence_matrix_freeze: Mapping[str, Any] | None = None,
    r51_bodyfree_handoff_materials: Sequence[Mapping[str, Any]] | None = None,
    r51_actual_review_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return R52-9 material after validating R52-0/R52-9 body-free gates."""
    r7 = build_p7_r52_r0_r7_disposal_execution_gate_chain(
        current_received_snapshot_refreeze=current_received_snapshot_refreeze,
        validation_evidence_matrix_freeze=validation_evidence_matrix_freeze,
        r51_bodyfree_handoff_materials=r51_bodyfree_handoff_materials,
        r51_actual_review_evidence=r51_actual_review_evidence,
    )
    assert_p7_r52_execution_blocker_gate_contract(r7)
    r8 = build_p7_r52_rating_question_consistency_gate(execution_blocker_gate=r7, r51_actual_review_evidence=r51_actual_review_evidence)
    assert_p7_r52_rating_question_consistency_gate_contract(r8)
    r9 = build_p7_r52_p5_readfeel_blocker_gate(rating_question_consistency_gate=r8, r51_actual_review_evidence=r51_actual_review_evidence)
    assert_p7_r52_p5_readfeel_blocker_gate_contract(r9)
    return r9

# R52-8/R52-9 final wrapper: preserve body-free boundary failures that occur
# before the R7 chain can materialize, without copying forbidden body values.
_p7_r52_r0_r9_rating_question_p5_readfeel_gate_chain_without_boundary_wrapper = build_p7_r52_r0_r9_rating_question_p5_readfeel_gate_chain


def _build_p7_r52_r9_bodyfree_boundary_blocked_result(
    *,
    r51_bodyfree_handoff_materials: Sequence[Mapping[str, Any]] | None = None,
    r51_actual_review_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    materials = [safe_mapping(item) for item in (r51_bodyfree_handoff_materials or [])]
    forbidden_key_paths = _r52_find_forbidden_key_paths(
        materials,
        forbidden_keys=P7_R52_FORBIDDEN_PAYLOAD_KEY_REFS,
        path="r51_bodyfree_handoff_materials",
    )
    forbidden_true_paths = _r52_find_forbidden_true_flag_paths(
        materials,
        forbidden_flags=P7_R52_FORBIDDEN_TRUE_FLAG_REFS,
        path="r51_bodyfree_handoff_materials",
    )
    values = _r52_p5_readfeel_blocker_values(r51_actual_review_evidence)
    reasons = dedupe_identifiers(
        [*forbidden_key_paths, *forbidden_true_paths, "r52_r0_r9_blocked_by_body_free_boundary_before_r7_chain"],
        limit=120,
        max_length=240,
    )
    gate = {
        "schema_version": P7_R52_P5_READFEEL_BLOCKER_GATE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R52_STEP,
        "scope": P7_R52_SCOPE,
        "policy_kind": P7_R52_POLICY_KIND,
        "policy_section": P7_R52_R9_STEP_REF,
        "current_phase": "P7",
        "material_id": "p7_r52_p5_readfeel_blocker_gate_bodyfree_boundary_blocked",
        "review_session_id": P7_R52_DEFAULT_REVIEW_SESSION_ID,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "r8_consistency_schema_version": P7_R52_RATING_QUESTION_CONSISTENCY_GATE_SCHEMA_VERSION,
        "r8_consistency_material_ref": "p7_r52_rating_question_consistency_gate_bodyfree_boundary_blocked",
        "r8_decision_ref": "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK",
        "r8_decision_status": "BLOCKED",
        "r8_rating_question_consistency_gate_status": "R52_RATING_QUESTION_CONSISTENCY_GATE_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK",
        "r8_ready_for_r52_9_p5_readfeel_blocker_gate": False,
        "r51_actual_review_evidence_complete": False,
        **values,
        "p5_readfeel_blocker_present": False,
        "p5_readfeel_blocker_detected": False,
        "p5_readfeel_repair_required": False,
        "p5_readfeel_blocker_reason_refs": [],
        "p5_readfeel_blocker_gate_status": "R52_P5_READFEEL_BLOCKER_GATE_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK",
        "decision_ref": "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK",
        "decision_status": "BLOCKED",
        "decision_reason_refs": reasons,
        "next_required_step": P7_R52_R4_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "p5_decision_status": "R52_P5_BLOCKED_BY_BOUNDARY_RISK",
        "p6_limited_human_readfeel_start_allowed_candidate": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_question_design_material_candidate": False,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "r52_0_current_received_snapshot_refrozen": True,
        "r52_1_validation_evidence_matrix_frozen": True,
        "r52_2_r51_bodyfree_handoff_intake_contract_built": True,
        "r52_3_forbidden_payload_deep_scan_built": True,
        "r52_4_actual_review_evidence_completeness_checker_built": False,
        "r52_5_evidence_missing_no_go_branch_built": False,
        "r52_6_disposal_safety_gate_built": False,
        "r52_7_execution_blocker_gate_built": False,
        "r52_8_rating_question_consistency_gate_built": False,
        "r52_9_p5_readfeel_blocker_gate_built": False,
        "implemented_steps": list(P7_R52_R3_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R52_R3_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R52_FIRST_NEXT_WORK_REF,
        "public_contract": public_contract_flags(),
        "r52_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_r52_false_flags_r8_r9(),
    }
    # Keep the output exactly on the public R9 body-free schema surface.
    return {key: gate[key] for key in P7_R52_P5_READFEEL_BLOCKER_GATE_REQUIRED_FIELD_REFS}


def build_p7_r52_r0_r9_rating_question_p5_readfeel_gate_chain(
    *,
    current_received_snapshot_refreeze: Mapping[str, Any] | None = None,
    validation_evidence_matrix_freeze: Mapping[str, Any] | None = None,
    r51_bodyfree_handoff_materials: Sequence[Mapping[str, Any]] | None = None,
    r51_actual_review_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    materials = [safe_mapping(item) for item in (r51_bodyfree_handoff_materials or [])]
    forbidden_key_paths = _r52_find_forbidden_key_paths(
        materials,
        forbidden_keys=P7_R52_FORBIDDEN_PAYLOAD_KEY_REFS,
        path="r51_bodyfree_handoff_materials",
    )
    forbidden_true_paths = _r52_find_forbidden_true_flag_paths(
        materials,
        forbidden_flags=P7_R52_FORBIDDEN_TRUE_FLAG_REFS,
        path="r51_bodyfree_handoff_materials",
    )
    if forbidden_key_paths or forbidden_true_paths:
        return _build_p7_r52_r9_bodyfree_boundary_blocked_result(
            r51_bodyfree_handoff_materials=materials,
            r51_actual_review_evidence=r51_actual_review_evidence,
        )
    return _p7_r52_r0_r9_rating_question_p5_readfeel_gate_chain_without_boundary_wrapper(
        current_received_snapshot_refreeze=current_received_snapshot_refreeze,
        validation_evidence_matrix_freeze=validation_evidence_matrix_freeze,
        r51_bodyfree_handoff_materials=r51_bodyfree_handoff_materials,
        r51_actual_review_evidence=r51_actual_review_evidence,
    )

_p7_r52_p5_readfeel_blocker_gate_contract_without_extra_forbidden_key_guard = assert_p7_r52_p5_readfeel_blocker_gate_contract


def assert_p7_r52_p5_readfeel_blocker_gate_contract(gate: Mapping[str, Any]) -> bool:
    data = safe_mapping(gate)
    forbidden_extra_keys = {
        "raw_input", "raw_answer", "comment_text", "comment_text_body",
        "reviewer_free_text", "reviewer_note", "reviewer_notes",
        "question_text", "draft_question_text", "question_body",
        "local_absolute_path", "body_content_hash", "packet_content_hash",
        "terminal_output", "stdout", "stderr", "traceback",
    }
    present_forbidden = sorted(key for key in forbidden_extra_keys if key in data)
    if present_forbidden:
        raise ValueError(f"R52 R9 body-free contract forbids keys: {present_forbidden[:4]}")
    return _p7_r52_p5_readfeel_blocker_gate_contract_without_extra_forbidden_key_guard(data)

# ---------------------------------------------------------------------------
# R52-10 / R52-11: P5 confirmed candidate + P6 candidate separation.
# ---------------------------------------------------------------------------

P7_R52_P5_CONFIRMED_CANDIDATE_DECISION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r52.p5_confirmed_candidate_decision.bodyfree.v1"
)
P7_R52_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_SEPARATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r52.p6_limited_human_readfeel_candidate_separation.bodyfree.v1"
)

P7_R52_R10_STEP_REF: Final = "R52-10_p5_confirmed_candidate_decision"
P7_R52_R11_STEP_REF: Final = "R52-11_p6_limited_human_readfeel_candidate_separation"
P7_R52_R10_NEXT_REQUIRED_STEP_REF: Final = P7_R52_R11_STEP_REF
P7_R52_R10_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "return_to_R51_review_or_P5_repair_before_P5_confirmed_candidate"
P7_R52_R11_NEXT_REQUIRED_STEP_REF: Final = "R52-12_p8_question_material_candidate_separation"
P7_R52_R11_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "do_not_start_P6_until_explicit_human_readfeel_gate"

P7_R52_FUTURE_STEPS_AFTER_R11: Final[tuple[str, ...]] = P7_R52_FUTURE_STEPS_AFTER_R9[2:]
P7_R52_R10_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R52_R9_IMPLEMENTED_STEPS, P7_R52_R10_STEP_REF)
P7_R52_R10_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R52_R11_STEP_REF, *P7_R52_FUTURE_STEPS_AFTER_R11)
P7_R52_R11_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R52_R10_IMPLEMENTED_STEPS, P7_R52_R11_STEP_REF)
P7_R52_R11_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R52_FUTURE_STEPS_AFTER_R11
P7_R52_CURRENT_IMPLEMENTED_STEPS = P7_R52_R11_IMPLEMENTED_STEPS
P7_R52_CURRENT_NOT_YET_IMPLEMENTED_STEPS = P7_R52_R11_NOT_YET_IMPLEMENTED_STEPS

P7_R52_R10_DECISION_REF_REFS: Final[tuple[str, ...]] = (
    *P7_R52_R9_DECISION_REF_REFS,
    "R52_GO_P5_CONFIRMED_CANDIDATE_REVIEWED_BUT_NOT_RELEASE",
    "R52_INCONCLUSIVE_RETURN_TO_R51_REVIEW_OR_RECHECK",
)
P7_R52_R11_DECISION_REF_REFS: Final[tuple[str, ...]] = (
    *P7_R52_R10_DECISION_REF_REFS,
    "R52_P6_LIMITED_READFEEL_START_CANDIDATE_ONLY",
)

P7_R52_R10_CANDIDATE_STATUS_REFS: Final[tuple[str, ...]] = (
    "R52_P5_CONFIRMED_CANDIDATE_DECISION_PASSED",
    "R52_P5_CONFIRMED_CANDIDATE_DECISION_NOT_REACHED_BY_R9",
    "R52_P5_CONFIRMED_CANDIDATE_DECISION_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED",
    "R52_P5_CONFIRMED_CANDIDATE_DECISION_RETURN_TO_P5_REPAIR_REQUIRED",
    "R52_P5_CONFIRMED_CANDIDATE_DECISION_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK",
    "R52_P5_CONFIRMED_CANDIDATE_DECISION_BLOCKED_BY_DISPOSAL_NOT_VERIFIED",
    "R52_P5_CONFIRMED_CANDIDATE_DECISION_BLOCKED_BY_EXECUTION_BLOCKER_OPEN",
    "R52_P5_CONFIRMED_CANDIDATE_DECISION_BLOCKED_BY_CONSISTENCY_ISSUE",
    "R52_P5_CONFIRMED_CANDIDATE_DECISION_INCONCLUSIVE",
)
P7_R52_R11_CANDIDATE_STATUS_REFS: Final[tuple[str, ...]] = (
    "R52_P6_LIMITED_READFEEL_CANDIDATE_SEPARATION_PASSED_WITH_CANDIDATE",
    "R52_P6_LIMITED_READFEEL_CANDIDATE_SEPARATION_PASSED_WITHOUT_CANDIDATE",
    "R52_P6_LIMITED_READFEEL_CANDIDATE_SEPARATION_NOT_REACHED_BY_R10",
    "R52_P6_LIMITED_READFEEL_CANDIDATE_SEPARATION_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED",
    "R52_P6_LIMITED_READFEEL_CANDIDATE_SEPARATION_RETURN_TO_P5_REPAIR_REQUIRED",
    "R52_P6_LIMITED_READFEEL_CANDIDATE_SEPARATION_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK",
    "R52_P6_LIMITED_READFEEL_CANDIDATE_SEPARATION_BLOCKED_BY_DISPOSAL_NOT_VERIFIED",
    "R52_P6_LIMITED_READFEEL_CANDIDATE_SEPARATION_BLOCKED_BY_EXECUTION_BLOCKER_OPEN",
    "R52_P6_LIMITED_READFEEL_CANDIDATE_SEPARATION_BLOCKED_BY_CONSISTENCY_ISSUE",
    "R52_P6_LIMITED_READFEEL_CANDIDATE_SEPARATION_INCONCLUSIVE",
)

P7_R52_R10_EXTRA_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    "r52_p5_confirmed_final_promoted_here",
    "p5_confirmed_candidate_claimed_as_final_here",
    "p5_confirmed_candidate_released_here",
    "p5_confirmed_candidate_used_to_complete_p7_here",
    "p5_confirmed_candidate_used_to_start_p6_here",
    "p5_confirmed_candidate_used_to_start_p8_here",
)
P7_R52_R10_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    *(key for key in P7_R52_R8_R9_FALSE_KEY_REFS if key != "p5_human_blind_qa_confirmed_candidate"),
    *P7_R52_R10_EXTRA_FALSE_KEY_REFS,
)
P7_R52_R11_EXTRA_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    "p6_limited_human_readfeel_start_allowed_promoted_here",
    "p6_limited_human_readfeel_runtime_started_here",
    "p6_limited_human_readfeel_review_run_here",
    "p6_limited_human_readfeel_notes_materialized_here",
    "p6_limited_human_readfeel_candidate_used_to_complete_p7_here",
    "p6_limited_human_readfeel_candidate_used_to_release_here",
    "p6_limited_human_readfeel_candidate_used_to_start_p8_here",
)
P7_R52_R11_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    *(key for key in P7_R52_R10_FALSE_KEY_REFS if key != "p6_limited_human_readfeel_start_allowed_candidate"),
    *P7_R52_R11_EXTRA_FALSE_KEY_REFS,
)

P7_R52_R10_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "current_phase", "material_id",
    "review_session_id", "required_case_count", "r9_readfeel_schema_version", "r9_readfeel_material_ref", "r9_decision_ref",
    "r9_decision_status", "r9_p5_readfeel_blocker_gate_status", "r9_ready_for_r52_10_p5_confirmed_candidate_decision",
    "r51_actual_review_evidence_complete", "all_axis_targets_met", "p5_readfeel_blocker_detected", "p5_confirmed_candidate_criteria_met",
    "p5_confirmed_candidate_reason_refs", "p5_confirmed_candidate_decision_status", "p5_decision_status", "p5_human_blind_qa_confirmed_candidate",
    "p5_human_blind_qa_confirmed", "p5_human_blind_qa_confirmed_final", "decision_ref", "decision_status", "decision_reason_refs", "next_required_step",
    "p6_limited_human_readfeel_start_allowed_candidate", "p6_limited_human_readfeel_start_allowed", "p8_question_design_material_candidate", "p8_start_allowed",
    "p7_complete", "release_allowed", "r52_0_current_received_snapshot_refrozen", "r52_1_validation_evidence_matrix_frozen", "r52_2_r51_bodyfree_handoff_intake_contract_built",
    "r52_3_forbidden_payload_deep_scan_built", "r52_4_actual_review_evidence_completeness_checker_built", "r52_5_evidence_missing_no_go_branch_built",
    "r52_6_disposal_safety_gate_built", "r52_7_execution_blocker_gate_built", "r52_8_rating_question_consistency_gate_built", "r52_9_p5_readfeel_blocker_gate_built",
    "r52_10_p5_confirmed_candidate_decision_built", "r52_10_ready_for_r52_11_p6_limited_human_readfeel_candidate_separation",
    "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "public_contract", "r52_public_no_touch_contract", "body_free_markers", "body_free",
    *P7_R52_R10_FALSE_KEY_REFS,
)
P7_R52_R11_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "current_phase", "material_id",
    "review_session_id", "required_case_count", "r10_p5_candidate_schema_version", "r10_p5_candidate_material_ref", "r10_decision_ref",
    "r10_decision_status", "r10_p5_confirmed_candidate_decision_status", "r10_ready_for_r52_11_p6_limited_human_readfeel_candidate_separation",
    "r51_actual_review_evidence_complete", "p5_decision_status", "p5_human_blind_qa_confirmed_candidate", "p5_human_blind_qa_confirmed", "p5_human_blind_qa_confirmed_final",
    "r51_p6_limited_human_readfeel_candidate_handoff_reported", "p6_limited_family_scope_supported", "p5_weakness_not_hidden_by_p6_candidate",
    "p6_candidate_critical_repair_blocker_count", "p6_candidate_creepy_or_surveillance_blocker_count", "p6_candidate_overclaim_blocker_count", "p6_candidate_self_blame_amplification_blocker_count",
    "p6_candidate_blocker_detected", "p6_limited_human_readfeel_candidate_supported", "p6_limited_human_readfeel_candidate_reason_refs", "p6_limited_human_readfeel_candidate_separation_status",
    "decision_ref", "decision_status", "decision_reason_refs", "next_required_step", "p6_limited_human_readfeel_start_allowed_candidate", "p6_limited_human_readfeel_start_allowed",
    "p8_question_design_material_candidate", "p8_start_allowed", "p7_complete", "release_allowed", "r52_0_current_received_snapshot_refrozen", "r52_1_validation_evidence_matrix_frozen",
    "r52_2_r51_bodyfree_handoff_intake_contract_built", "r52_3_forbidden_payload_deep_scan_built", "r52_4_actual_review_evidence_completeness_checker_built",
    "r52_5_evidence_missing_no_go_branch_built", "r52_6_disposal_safety_gate_built", "r52_7_execution_blocker_gate_built", "r52_8_rating_question_consistency_gate_built",
    "r52_9_p5_readfeel_blocker_gate_built", "r52_10_p5_confirmed_candidate_decision_built", "r52_11_p6_limited_human_readfeel_candidate_separation_built",
    "r52_11_ready_for_r52_12_p8_question_material_candidate_separation", "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "public_contract", "r52_public_no_touch_contract", "body_free_markers", "body_free",
    *P7_R52_R11_FALSE_KEY_REFS,
)

# Backward-compatible long names for the split R52-10/R52-11 tests.
P7_R52_P5_CONFIRMED_CANDIDATE_DECISION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = P7_R52_R10_REQUIRED_FIELD_REFS
P7_R52_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_SEPARATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = P7_R52_R11_REQUIRED_FIELD_REFS


def _r52_false_flags_r10() -> dict[str, bool]:
    return {key: False for key in P7_R52_R10_FALSE_KEY_REFS}


def _r52_false_flags_r11() -> dict[str, bool]:
    return {key: False for key in P7_R52_R11_FALSE_KEY_REFS}


def _r52_r9_ready_for_p5_confirmed_candidate_decision(r9: Mapping[str, Any]) -> bool:
    return (
        r9.get("decision_ref") == "R52_NO_GO_P6_P8_START"
        and r9.get("decision_status") == "CANDIDATE_ONLY"
        and r9.get("p5_decision_status") == "R52_P5_CONFIRMED_CANDIDATE_REVIEWED_NOT_FINAL"
        and r9.get("r51_actual_review_evidence_complete") is True
        and r9.get("p5_readfeel_blocker_detected") is False
        and r9.get("r52_9_p5_readfeel_blocker_gate_built") is True
    )


def _r52_r10_ready_for_p6_limited_human_readfeel_candidate_separation(r10: Mapping[str, Any]) -> bool:
    return (
        r10.get("decision_ref") == "R52_GO_P5_CONFIRMED_CANDIDATE_REVIEWED_BUT_NOT_RELEASE"
        and r10.get("decision_status") == "CANDIDATE_ONLY"
        and r10.get("p5_decision_status") == "R52_P5_CONFIRMED_CANDIDATE_REVIEWED_NOT_FINAL"
        and r10.get("p5_human_blind_qa_confirmed_candidate") is True
        and r10.get("p5_human_blind_qa_confirmed") is False
        and r10.get("p5_human_blind_qa_confirmed_final") is False
        and r10.get("r52_10_p5_confirmed_candidate_decision_built") is True
    )


def _r52_p5_confirmed_candidate_values(r9: Mapping[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    if r9.get("r51_actual_review_evidence_complete") is not True:
        reasons.append("r51_actual_review_evidence_not_complete_for_p5_candidate")
    if r9.get("all_axis_targets_met") is not True:
        reasons.append("r51_axis_targets_not_met_for_p5_candidate")
    if r9.get("p5_readfeel_blocker_detected") is True:
        reasons.append("r51_p5_readfeel_blocker_present_for_p5_candidate")
    if r9.get("p5_decision_status") != "R52_P5_CONFIRMED_CANDIDATE_REVIEWED_NOT_FINAL":
        reasons.append("r52_9_p5_decision_status_not_confirmed_candidate")
    if r9.get("decision_ref") != "R52_NO_GO_P6_P8_START" or r9.get("decision_status") != "CANDIDATE_ONLY":
        reasons.append("r52_9_not_clean_candidate_only_for_p5_candidate")
    reason_refs = dedupe_identifiers(reasons, limit=80, max_length=220)
    return {
        "p5_confirmed_candidate_criteria_met": not bool(reason_refs),
        "p5_confirmed_candidate_reason_refs": reason_refs or ["r51_actual_review_complete_and_p5_readfeel_no_blocker_candidate_only"],
    }


def _r52_reported_flag_refs_from_materials(materials: Sequence[Mapping[str, Any]] | None) -> list[str]:
    material_items = _r52_material_sequence(materials)
    paths = _r52_find_r51_reported_actual_true_flag_paths(material_items, path="r51_bodyfree_handoff_materials")
    return _r52_normalized_r51_reported_actual_flag_refs(paths)


def _r52_p6_candidate_values(
    *,
    p5_confirmed_candidate_decision: Mapping[str, Any],
    r51_actual_review_evidence: Mapping[str, Any] | None,
    r51_bodyfree_handoff_materials: Sequence[Mapping[str, Any]] | None,
) -> dict[str, Any]:
    r10 = safe_mapping(p5_confirmed_candidate_decision)
    evidence = safe_mapping(r51_actual_review_evidence)
    normalized_reported_flags = _r52_reported_flag_refs_from_materials(r51_bodyfree_handoff_materials)
    handoff_reported = (
        "r51_reported_p6_limited_human_readfeel_start_allowed_candidate" in normalized_reported_flags
        or _r52_evidence_bool(evidence, "r51_p6_limited_human_readfeel_candidate_handoff_reported", default=False)
        or _r52_evidence_bool(evidence, "p6_limited_human_readfeel_candidate_supported_by_handoff", default=False)
    )
    limited_family_supported = _r52_evidence_bool(evidence, "p6_limited_family_scope_supported", default=True)
    p5_weakness_not_hidden = _r52_evidence_bool(evidence, "p5_weakness_not_hidden_by_p6_candidate", default=True)
    counts = {
        "p6_candidate_critical_repair_blocker_count": _r52_evidence_int(evidence, "critical_repair_blocker_count", "p6_candidate_critical_repair_blocker_count"),
        "p6_candidate_creepy_or_surveillance_blocker_count": _r52_evidence_int(evidence, "creepy_or_surveillance_blocker_count", "p6_candidate_creepy_or_surveillance_blocker_count"),
        "p6_candidate_overclaim_blocker_count": _r52_evidence_int(evidence, "overclaim_blocker_count", "p6_candidate_overclaim_blocker_count"),
        "p6_candidate_self_blame_amplification_blocker_count": _r52_evidence_int(evidence, "self_blame_amplification_blocker_count", "p6_candidate_self_blame_amplification_blocker_count"),
    }
    reasons: list[str] = []
    if not _r52_r10_ready_for_p6_limited_human_readfeel_candidate_separation(r10):
        reasons.append("r52_10_p5_confirmed_candidate_not_ready_for_p6_candidate")
    if not handoff_reported:
        reasons.append("r51_p6_limited_human_readfeel_candidate_handoff_not_reported")
    if not limited_family_supported:
        reasons.append("p6_limited_family_scope_not_supported")
    if not p5_weakness_not_hidden:
        reasons.append("p5_weakness_would_be_hidden_by_p6_candidate")
    if counts["p6_candidate_critical_repair_blocker_count"] > 0:
        reasons.append("p6_candidate_blocked_by_critical_repair_blocker")
    if counts["p6_candidate_creepy_or_surveillance_blocker_count"] > 0:
        reasons.append("p6_candidate_blocked_by_creepy_or_surveillance_blocker")
    if counts["p6_candidate_overclaim_blocker_count"] > 0:
        reasons.append("p6_candidate_blocked_by_overclaim_blocker")
    if counts["p6_candidate_self_blame_amplification_blocker_count"] > 0:
        reasons.append("p6_candidate_blocked_by_self_blame_amplification_blocker")
    reason_refs = dedupe_identifiers(reasons, limit=120, max_length=220)
    supported = not bool(reason_refs)
    return {
        "r51_p6_limited_human_readfeel_candidate_handoff_reported": handoff_reported,
        "p6_limited_family_scope_supported": limited_family_supported,
        "p5_weakness_not_hidden_by_p6_candidate": p5_weakness_not_hidden,
        **counts,
        "p6_candidate_blocker_detected": bool(reason_refs),
        "p6_limited_human_readfeel_candidate_supported": supported,
        "p6_limited_human_readfeel_candidate_reason_refs": reason_refs or ["r51_p6_limited_handoff_and_p5_confirmed_candidate_clean_candidate_only"],
    }


def build_p7_r52_p5_confirmed_candidate_decision(
    *,
    p5_readfeel_blocker_gate: Mapping[str, Any] | None = None,
    r51_actual_review_evidence: Mapping[str, Any] | None = None,
    current_received_snapshot_refreeze: Mapping[str, Any] | None = None,
    validation_evidence_matrix_freeze: Mapping[str, Any] | None = None,
    r51_bodyfree_handoff_materials: Sequence[Mapping[str, Any]] | None = None,
    material_id: str = "p7_r52_p5_confirmed_candidate_decision",
) -> dict[str, Any]:
    """Build R52-10: P5 confirmed candidate reviewed, never final or release."""

    r9 = safe_mapping(p5_readfeel_blocker_gate) if p5_readfeel_blocker_gate is not None else build_p7_r52_r0_r9_rating_question_p5_readfeel_gate_chain(
        current_received_snapshot_refreeze=current_received_snapshot_refreeze,
        validation_evidence_matrix_freeze=validation_evidence_matrix_freeze,
        r51_bodyfree_handoff_materials=r51_bodyfree_handoff_materials,
        r51_actual_review_evidence=r51_actual_review_evidence,
    )
    assert_p7_r52_p5_readfeel_blocker_gate_contract(r9)
    values = _r52_p5_confirmed_candidate_values(r9)
    r9_ready = _r52_r9_ready_for_p5_confirmed_candidate_decision(r9)
    prior = clean_identifier(r9.get("decision_ref"), default="R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED", max_length=180)

    if prior == "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK":
        decision_ref, decision_status = prior, "BLOCKED"
        p5_status = "R52_P5_BLOCKED_BY_BOUNDARY_RISK"
        status = "R52_P5_CONFIRMED_CANDIDATE_DECISION_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK"
        reasons = dedupe_identifiers([*(r9.get("decision_reason_refs") or []), "r52_10_blocked_by_prior_body_free_boundary_risk"], limit=160, max_length=220)
        next_step = clean_identifier(r9.get("next_required_step"), default=P7_R52_R4_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220)
        implemented_steps, not_yet_steps, built, candidate = P7_R52_R9_IMPLEMENTED_STEPS, P7_R52_R9_NOT_YET_IMPLEMENTED_STEPS, False, False
    elif prior == "R52_BLOCKED_BY_DISPOSAL_NOT_VERIFIED":
        decision_ref, decision_status = prior, "BLOCKED"
        p5_status = "R52_P5_BLOCKED_BY_DISPOSAL_NOT_VERIFIED"
        status = "R52_P5_CONFIRMED_CANDIDATE_DECISION_BLOCKED_BY_DISPOSAL_NOT_VERIFIED"
        reasons = dedupe_identifiers([*(r9.get("decision_reason_refs") or []), "r52_10_blocked_by_prior_disposal_not_verified"], limit=160, max_length=220)
        next_step = clean_identifier(r9.get("next_required_step"), default=P7_R52_R6_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220)
        implemented_steps, not_yet_steps, built, candidate = P7_R52_R9_IMPLEMENTED_STEPS, P7_R52_R9_NOT_YET_IMPLEMENTED_STEPS, False, False
    elif prior == "R52_BLOCKED_BY_EXECUTION_BLOCKER_OPEN":
        decision_ref, decision_status = prior, "BLOCKED"
        p5_status = "R52_P5_BLOCKED_BY_EXECUTION_BLOCKER"
        status = "R52_P5_CONFIRMED_CANDIDATE_DECISION_BLOCKED_BY_EXECUTION_BLOCKER_OPEN"
        reasons = dedupe_identifiers([*(r9.get("decision_reason_refs") or []), "r52_10_blocked_by_prior_execution_blocker_open"], limit=160, max_length=220)
        next_step = clean_identifier(r9.get("next_required_step"), default=P7_R52_R7_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220)
        implemented_steps, not_yet_steps, built, candidate = P7_R52_R9_IMPLEMENTED_STEPS, P7_R52_R9_NOT_YET_IMPLEMENTED_STEPS, False, False
    elif prior == "R52_BLOCKED_BY_RATING_QUESTION_OBSERVATION_INCONSISTENCY":
        decision_ref, decision_status = prior, "BLOCKED"
        p5_status = "R52_P5_BLOCKED_BY_CONSISTENCY_ISSUE"
        status = "R52_P5_CONFIRMED_CANDIDATE_DECISION_BLOCKED_BY_CONSISTENCY_ISSUE"
        reasons = dedupe_identifiers([*(r9.get("decision_reason_refs") or []), "r52_10_blocked_by_prior_rating_question_consistency_issue"], limit=160, max_length=220)
        next_step = clean_identifier(r9.get("next_required_step"), default=P7_R52_R8_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220)
        implemented_steps, not_yet_steps, built, candidate = P7_R52_R9_IMPLEMENTED_STEPS, P7_R52_R9_NOT_YET_IMPLEMENTED_STEPS, False, False
    elif prior == "R52_RETURN_TO_P5_REPAIR_REQUIRED":
        decision_ref, decision_status = prior, "RETURN_REQUIRED"
        p5_status = "R52_P5_REPAIR_REQUIRED"
        status = "R52_P5_CONFIRMED_CANDIDATE_DECISION_RETURN_TO_P5_REPAIR_REQUIRED"
        reasons = dedupe_identifiers([*(r9.get("decision_reason_refs") or []), "r52_10_return_to_p5_repair_before_confirmed_candidate"], limit=160, max_length=220)
        next_step = clean_identifier(r9.get("next_required_step"), default=P7_R52_R9_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220)
        implemented_steps, not_yet_steps, built, candidate = P7_R52_R9_IMPLEMENTED_STEPS, P7_R52_R9_NOT_YET_IMPLEMENTED_STEPS, False, False
    elif prior == "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED" or not r9_ready:
        decision_ref = prior
        decision_status = clean_identifier(r9.get("decision_status"), default="RETURN_REQUIRED", max_length=80)
        p5_status = clean_identifier(r9.get("p5_decision_status"), default="R52_P5_NOT_REVIEWED_EVIDENCE_MISSING", max_length=180)
        status = "R52_P5_CONFIRMED_CANDIDATE_DECISION_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED" if prior == "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED" else "R52_P5_CONFIRMED_CANDIDATE_DECISION_NOT_REACHED_BY_R9"
        reasons = dedupe_identifiers([*(r9.get("decision_reason_refs") or []), *values["p5_confirmed_candidate_reason_refs"], "r52_10_not_reached_until_r52_9_p5_readfeel_gate_passes"], limit=180, max_length=220)
        next_step = clean_identifier(r9.get("next_required_step"), default=P7_R52_R5_RETURN_TO_R51_NEXT_REQUIRED_STEP_REF, max_length=220)
        implemented_steps, not_yet_steps, built, candidate = P7_R52_R9_IMPLEMENTED_STEPS, P7_R52_R9_NOT_YET_IMPLEMENTED_STEPS, False, False
    elif values["p5_confirmed_candidate_criteria_met"] is True:
        decision_ref, decision_status = "R52_GO_P5_CONFIRMED_CANDIDATE_REVIEWED_BUT_NOT_RELEASE", "CANDIDATE_ONLY"
        p5_status = "R52_P5_CONFIRMED_CANDIDATE_REVIEWED_NOT_FINAL"
        status = "R52_P5_CONFIRMED_CANDIDATE_DECISION_PASSED"
        reasons = values["p5_confirmed_candidate_reason_refs"]
        next_step = P7_R52_R10_NEXT_REQUIRED_STEP_REF
        implemented_steps, not_yet_steps, built, candidate = P7_R52_R10_IMPLEMENTED_STEPS, P7_R52_R10_NOT_YET_IMPLEMENTED_STEPS, True, True
    else:
        decision_ref, decision_status = "R52_INCONCLUSIVE_RETURN_TO_R51_REVIEW_OR_RECHECK", "INCONCLUSIVE"
        p5_status = "R52_P5_INCONCLUSIVE_REVIEW_REQUIRED"
        status = "R52_P5_CONFIRMED_CANDIDATE_DECISION_INCONCLUSIVE"
        reasons = values["p5_confirmed_candidate_reason_refs"]
        next_step = P7_R52_R10_BLOCKED_NEXT_REQUIRED_STEP_REF
        implemented_steps, not_yet_steps, built, candidate = P7_R52_R10_IMPLEMENTED_STEPS, P7_R52_R10_NOT_YET_IMPLEMENTED_STEPS, True, False

    gate = {
        "schema_version": P7_R52_P5_CONFIRMED_CANDIDATE_DECISION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R52_STEP,
        "scope": P7_R52_SCOPE,
        "policy_kind": P7_R52_POLICY_KIND,
        "policy_section": P7_R52_R10_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r52_p5_confirmed_candidate_decision", max_length=180),
        "review_session_id": clean_identifier(r9.get("review_session_id"), default=P7_R52_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "r9_readfeel_schema_version": P7_R52_P5_READFEEL_BLOCKER_GATE_SCHEMA_VERSION,
        "r9_readfeel_material_ref": clean_identifier(r9.get("material_id"), default="p7_r52_p5_readfeel_blocker_gate", max_length=180),
        "r9_decision_ref": prior,
        "r9_decision_status": clean_identifier(r9.get("decision_status"), default="RETURN_REQUIRED", max_length=80),
        "r9_p5_readfeel_blocker_gate_status": clean_identifier(r9.get("p5_readfeel_blocker_gate_status"), default="R52_P5_READFEEL_BLOCKER_GATE_NOT_REACHED_BY_R8", max_length=180),
        "r9_ready_for_r52_10_p5_confirmed_candidate_decision": r9_ready,
        "r51_actual_review_evidence_complete": r9.get("r51_actual_review_evidence_complete") is True,
        "all_axis_targets_met": r9.get("all_axis_targets_met") is True,
        "p5_readfeel_blocker_detected": r9.get("p5_readfeel_blocker_detected") is True,
        **values,
        "p5_confirmed_candidate_decision_status": status,
        "p5_decision_status": p5_status,
        "p5_human_blind_qa_confirmed_candidate": candidate,
        "p5_human_blind_qa_confirmed": False,
        "p5_human_blind_qa_confirmed_final": False,
        "decision_ref": decision_ref,
        "decision_status": decision_status,
        "decision_reason_refs": reasons,
        "next_required_step": next_step,
        "p6_limited_human_readfeel_start_allowed_candidate": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_question_design_material_candidate": False,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "r52_0_current_received_snapshot_refrozen": True,
        "r52_1_validation_evidence_matrix_frozen": True,
        "r52_2_r51_bodyfree_handoff_intake_contract_built": True,
        "r52_3_forbidden_payload_deep_scan_built": r9.get("r52_3_forbidden_payload_deep_scan_built") is True,
        "r52_4_actual_review_evidence_completeness_checker_built": r9.get("r52_4_actual_review_evidence_completeness_checker_built") is True,
        "r52_5_evidence_missing_no_go_branch_built": r9.get("r52_5_evidence_missing_no_go_branch_built") is True,
        "r52_6_disposal_safety_gate_built": r9.get("r52_6_disposal_safety_gate_built") is True,
        "r52_7_execution_blocker_gate_built": r9.get("r52_7_execution_blocker_gate_built") is True,
        "r52_8_rating_question_consistency_gate_built": r9.get("r52_8_rating_question_consistency_gate_built") is True,
        "r52_9_p5_readfeel_blocker_gate_built": r9.get("r52_9_p5_readfeel_blocker_gate_built") is True,
        "r52_10_p5_confirmed_candidate_decision_built": built,
        "r52_10_ready_for_r52_11_p6_limited_human_readfeel_candidate_separation": built and candidate,
        "implemented_steps": list(implemented_steps),
        "not_yet_implemented_steps": list(not_yet_steps),
        "first_next_work_ref": P7_R52_FIRST_NEXT_WORK_REF,
        "public_contract": public_contract_flags(),
        "r52_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_r52_false_flags_r10(),
    }
    assert_p7_r52_p5_confirmed_candidate_decision_contract(gate)
    return gate


def assert_p7_r52_p5_confirmed_candidate_decision_contract(gate: Mapping[str, Any]) -> bool:
    data = safe_mapping(gate)
    forbidden_paths = _r52_find_forbidden_key_paths(data, forbidden_keys=P7_R52_FORBIDDEN_PAYLOAD_KEY_REFS, path="p7_r52_r10_p5_confirmed_candidate_decision")
    if forbidden_paths:
        raise ValueError(f"R52 R10 must remain body-free: {forbidden_paths[:6]}")
    missing = [field for field in P7_R52_R10_REQUIRED_FIELD_REFS if field not in data]
    if missing:
        raise ValueError(f"p7_r52_r10_p5_confirmed_candidate_decision missing required fields: {missing[:6]}")
    if set(data) != set(P7_R52_R10_REQUIRED_FIELD_REFS):
        raise ValueError("R52 R10 must not contain body payload, question text, path, hash, or extra fields")
    _assert_body_free_common(data, schema_version=P7_R52_P5_CONFIRMED_CANDIDATE_DECISION_SCHEMA_VERSION, source="p7_r52_r10_p5_confirmed_candidate_decision")
    if data.get("policy_section") != P7_R52_R10_STEP_REF:
        raise ValueError("R52 R10 policy section changed")
    for false_key in P7_R52_R10_FALSE_KEY_REFS:
        if data.get(false_key) is not False:
            raise ValueError(f"R52 R10 must keep {false_key}=False")
    if data.get("decision_ref") not in P7_R52_R10_DECISION_REF_REFS or data.get("decision_status") not in P7_R52_R5_DECISION_STATUS_REFS:
        raise ValueError("R52 R10 decision changed")
    if data.get("p5_confirmed_candidate_decision_status") not in P7_R52_R10_CANDIDATE_STATUS_REFS:
        raise ValueError("R52 R10 candidate status changed")
    if data.get("p5_human_blind_qa_confirmed") is not False or data.get("p5_human_blind_qa_confirmed_final") is not False:
        raise ValueError("R52 R10 must not finalize P5")
    if data.get("p6_limited_human_readfeel_start_allowed_candidate") is not False or data.get("p6_limited_human_readfeel_start_allowed") is not False:
        raise ValueError("R52 R10 must not expose or start P6")
    if data.get("p8_question_design_material_candidate") is not False or data.get("p8_start_allowed") is not False or data.get("p7_complete") is not False or data.get("release_allowed") is not False:
        raise ValueError("R52 R10 must not expose P8, complete P7, or release")
    if data.get("r9_ready_for_r52_10_p5_confirmed_candidate_decision") is True and data.get("p5_confirmed_candidate_criteria_met") is True:
        if data.get("decision_ref") != "R52_GO_P5_CONFIRMED_CANDIDATE_REVIEWED_BUT_NOT_RELEASE" or data.get("decision_status") != "CANDIDATE_ONLY":
            raise ValueError("R52 R10 clean P5 candidate must be candidate-only")
        if data.get("p5_decision_status") != "R52_P5_CONFIRMED_CANDIDATE_REVIEWED_NOT_FINAL" or data.get("p5_human_blind_qa_confirmed_candidate") is not True:
            raise ValueError("R52 R10 clean P5 candidate status changed")
        if data.get("next_required_step") != P7_R52_R10_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R52 R10 clean P5 candidate must point to R52-11")
        if tuple(data.get("implemented_steps") or ()) != P7_R52_R10_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R52_R10_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R52 R10 implemented/not-yet steps changed")
    if data.get("r9_ready_for_r52_10_p5_confirmed_candidate_decision") is not True:
        if data.get("p5_human_blind_qa_confirmed_candidate") is not False or data.get("r52_10_p5_confirmed_candidate_decision_built") is not False:
            raise ValueError("R52 R10 not reached must not create a P5 candidate")
    return True


def build_p7_r52_p6_limited_human_readfeel_candidate_separation(
    *,
    p5_confirmed_candidate_decision: Mapping[str, Any] | None = None,
    r51_actual_review_evidence: Mapping[str, Any] | None = None,
    current_received_snapshot_refreeze: Mapping[str, Any] | None = None,
    validation_evidence_matrix_freeze: Mapping[str, Any] | None = None,
    r51_bodyfree_handoff_materials: Sequence[Mapping[str, Any]] | None = None,
    material_id: str = "p7_r52_p6_limited_human_readfeel_candidate_separation",
) -> dict[str, Any]:
    """Build R52-11: separate P6 candidate from any P6 start permission."""

    r10 = safe_mapping(p5_confirmed_candidate_decision) if p5_confirmed_candidate_decision is not None else build_p7_r52_p5_confirmed_candidate_decision(
        current_received_snapshot_refreeze=current_received_snapshot_refreeze,
        validation_evidence_matrix_freeze=validation_evidence_matrix_freeze,
        r51_bodyfree_handoff_materials=r51_bodyfree_handoff_materials,
        r51_actual_review_evidence=r51_actual_review_evidence,
    )
    assert_p7_r52_p5_confirmed_candidate_decision_contract(r10)
    values = _r52_p6_candidate_values(
        p5_confirmed_candidate_decision=r10,
        r51_actual_review_evidence=r51_actual_review_evidence,
        r51_bodyfree_handoff_materials=r51_bodyfree_handoff_materials,
    )
    r10_ready = _r52_r10_ready_for_p6_limited_human_readfeel_candidate_separation(r10)
    prior = clean_identifier(r10.get("decision_ref"), default="R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED", max_length=180)

    if prior in {
        "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK",
        "R52_BLOCKED_BY_DISPOSAL_NOT_VERIFIED",
        "R52_BLOCKED_BY_EXECUTION_BLOCKER_OPEN",
        "R52_BLOCKED_BY_RATING_QUESTION_OBSERVATION_INCONSISTENCY",
    }:
        decision_ref = prior
        decision_status = "BLOCKED"
        status_by_ref = {
            "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK": "R52_P6_LIMITED_READFEEL_CANDIDATE_SEPARATION_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK",
            "R52_BLOCKED_BY_DISPOSAL_NOT_VERIFIED": "R52_P6_LIMITED_READFEEL_CANDIDATE_SEPARATION_BLOCKED_BY_DISPOSAL_NOT_VERIFIED",
            "R52_BLOCKED_BY_EXECUTION_BLOCKER_OPEN": "R52_P6_LIMITED_READFEEL_CANDIDATE_SEPARATION_BLOCKED_BY_EXECUTION_BLOCKER_OPEN",
            "R52_BLOCKED_BY_RATING_QUESTION_OBSERVATION_INCONSISTENCY": "R52_P6_LIMITED_READFEEL_CANDIDATE_SEPARATION_BLOCKED_BY_CONSISTENCY_ISSUE",
        }
        separation_status = status_by_ref[prior]
        reasons = dedupe_identifiers([*(r10.get("decision_reason_refs") or []), "r52_11_blocked_by_prior_gate"], limit=180, max_length=220)
        next_step = clean_identifier(r10.get("next_required_step"), default=P7_R52_R10_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220)
        implemented_steps, not_yet_steps, built, p6_candidate = P7_R52_R10_IMPLEMENTED_STEPS, P7_R52_R10_NOT_YET_IMPLEMENTED_STEPS, False, False
    elif prior == "R52_RETURN_TO_P5_REPAIR_REQUIRED":
        decision_ref, decision_status = prior, "RETURN_REQUIRED"
        separation_status = "R52_P6_LIMITED_READFEEL_CANDIDATE_SEPARATION_RETURN_TO_P5_REPAIR_REQUIRED"
        reasons = dedupe_identifiers([*(r10.get("decision_reason_refs") or []), "r52_11_return_to_p5_repair_before_p6_candidate"], limit=180, max_length=220)
        next_step = clean_identifier(r10.get("next_required_step"), default=P7_R52_R9_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220)
        implemented_steps, not_yet_steps, built, p6_candidate = P7_R52_R10_IMPLEMENTED_STEPS, P7_R52_R10_NOT_YET_IMPLEMENTED_STEPS, False, False
    elif prior == "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED" or not r10_ready:
        decision_ref = prior
        decision_status = clean_identifier(r10.get("decision_status"), default="RETURN_REQUIRED", max_length=80)
        separation_status = "R52_P6_LIMITED_READFEEL_CANDIDATE_SEPARATION_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED" if prior == "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED" else "R52_P6_LIMITED_READFEEL_CANDIDATE_SEPARATION_NOT_REACHED_BY_R10"
        reasons = dedupe_identifiers([*(r10.get("decision_reason_refs") or []), "r52_11_not_reached_until_r52_10_p5_confirmed_candidate_passes"], limit=180, max_length=220)
        next_step = clean_identifier(r10.get("next_required_step"), default=P7_R52_R5_RETURN_TO_R51_NEXT_REQUIRED_STEP_REF, max_length=220)
        implemented_steps, not_yet_steps, built, p6_candidate = P7_R52_R10_IMPLEMENTED_STEPS, P7_R52_R10_NOT_YET_IMPLEMENTED_STEPS, False, False
    elif values["p6_limited_human_readfeel_candidate_supported"] is True:
        decision_ref, decision_status = "R52_P6_LIMITED_READFEEL_START_CANDIDATE_ONLY", "CANDIDATE_ONLY"
        separation_status = "R52_P6_LIMITED_READFEEL_CANDIDATE_SEPARATION_PASSED_WITH_CANDIDATE"
        reasons = values["p6_limited_human_readfeel_candidate_reason_refs"]
        next_step = P7_R52_R11_NEXT_REQUIRED_STEP_REF
        implemented_steps, not_yet_steps, built, p6_candidate = P7_R52_R11_IMPLEMENTED_STEPS, P7_R52_R11_NOT_YET_IMPLEMENTED_STEPS, True, True
    else:
        decision_ref, decision_status = "R52_NO_GO_P6_P8_START", "CANDIDATE_ONLY"
        separation_status = "R52_P6_LIMITED_READFEEL_CANDIDATE_SEPARATION_PASSED_WITHOUT_CANDIDATE"
        reasons = values["p6_limited_human_readfeel_candidate_reason_refs"]
        next_step = P7_R52_R11_NEXT_REQUIRED_STEP_REF
        implemented_steps, not_yet_steps, built, p6_candidate = P7_R52_R11_IMPLEMENTED_STEPS, P7_R52_R11_NOT_YET_IMPLEMENTED_STEPS, True, False

    gate = {
        "schema_version": P7_R52_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_SEPARATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R52_STEP,
        "scope": P7_R52_SCOPE,
        "policy_kind": P7_R52_POLICY_KIND,
        "policy_section": P7_R52_R11_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r52_p6_limited_human_readfeel_candidate_separation", max_length=180),
        "review_session_id": clean_identifier(r10.get("review_session_id"), default=P7_R52_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "r10_p5_candidate_schema_version": P7_R52_P5_CONFIRMED_CANDIDATE_DECISION_SCHEMA_VERSION,
        "r10_p5_candidate_material_ref": clean_identifier(r10.get("material_id"), default="p7_r52_p5_confirmed_candidate_decision", max_length=180),
        "r10_decision_ref": prior,
        "r10_decision_status": clean_identifier(r10.get("decision_status"), default="RETURN_REQUIRED", max_length=80),
        "r10_p5_confirmed_candidate_decision_status": clean_identifier(r10.get("p5_confirmed_candidate_decision_status"), default="R52_P5_CONFIRMED_CANDIDATE_DECISION_NOT_REACHED_BY_R9", max_length=180),
        "r10_ready_for_r52_11_p6_limited_human_readfeel_candidate_separation": r10_ready,
        "r51_actual_review_evidence_complete": r10.get("r51_actual_review_evidence_complete") is True,
        "p5_decision_status": clean_identifier(r10.get("p5_decision_status"), default="R52_P5_NOT_REVIEWED_EVIDENCE_MISSING", max_length=180),
        "p5_human_blind_qa_confirmed_candidate": r10.get("p5_human_blind_qa_confirmed_candidate") is True,
        "p5_human_blind_qa_confirmed": False,
        "p5_human_blind_qa_confirmed_final": False,
        **values,
        "p6_limited_human_readfeel_candidate_separation_status": separation_status,
        "decision_ref": decision_ref,
        "decision_status": decision_status,
        "decision_reason_refs": reasons,
        "next_required_step": next_step,
        "p6_limited_human_readfeel_start_allowed_candidate": p6_candidate,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_question_design_material_candidate": False,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "r52_0_current_received_snapshot_refrozen": True,
        "r52_1_validation_evidence_matrix_frozen": True,
        "r52_2_r51_bodyfree_handoff_intake_contract_built": True,
        "r52_3_forbidden_payload_deep_scan_built": r10.get("r52_3_forbidden_payload_deep_scan_built") is True,
        "r52_4_actual_review_evidence_completeness_checker_built": r10.get("r52_4_actual_review_evidence_completeness_checker_built") is True,
        "r52_5_evidence_missing_no_go_branch_built": r10.get("r52_5_evidence_missing_no_go_branch_built") is True,
        "r52_6_disposal_safety_gate_built": r10.get("r52_6_disposal_safety_gate_built") is True,
        "r52_7_execution_blocker_gate_built": r10.get("r52_7_execution_blocker_gate_built") is True,
        "r52_8_rating_question_consistency_gate_built": r10.get("r52_8_rating_question_consistency_gate_built") is True,
        "r52_9_p5_readfeel_blocker_gate_built": r10.get("r52_9_p5_readfeel_blocker_gate_built") is True,
        "r52_10_p5_confirmed_candidate_decision_built": r10.get("r52_10_p5_confirmed_candidate_decision_built") is True,
        "r52_11_p6_limited_human_readfeel_candidate_separation_built": built,
        "r52_11_ready_for_r52_12_p8_question_material_candidate_separation": built,
        "implemented_steps": list(implemented_steps),
        "not_yet_implemented_steps": list(not_yet_steps),
        "first_next_work_ref": P7_R52_FIRST_NEXT_WORK_REF,
        "public_contract": public_contract_flags(),
        "r52_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_r52_false_flags_r11(),
    }
    assert_p7_r52_p6_limited_human_readfeel_candidate_separation_contract(gate)
    return gate


def assert_p7_r52_p6_limited_human_readfeel_candidate_separation_contract(gate: Mapping[str, Any]) -> bool:
    data = safe_mapping(gate)
    forbidden_paths = _r52_find_forbidden_key_paths(data, forbidden_keys=P7_R52_FORBIDDEN_PAYLOAD_KEY_REFS, path="p7_r52_r11_p6_limited_human_readfeel_candidate_separation")
    if forbidden_paths:
        raise ValueError(f"R52 R11 must remain body-free: {forbidden_paths[:6]}")
    missing = [field for field in P7_R52_R11_REQUIRED_FIELD_REFS if field not in data]
    if missing:
        raise ValueError(f"p7_r52_r11_p6_limited_human_readfeel_candidate_separation missing required fields: {missing[:6]}")
    if set(data) != set(P7_R52_R11_REQUIRED_FIELD_REFS):
        raise ValueError("R52 R11 must not contain body payload, question text, path, hash, or extra fields")
    _assert_body_free_common(data, schema_version=P7_R52_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_SEPARATION_SCHEMA_VERSION, source="p7_r52_r11_p6_limited_human_readfeel_candidate_separation")
    if data.get("policy_section") != P7_R52_R11_STEP_REF:
        raise ValueError("R52 R11 policy section changed")
    for false_key in P7_R52_R11_FALSE_KEY_REFS:
        if data.get(false_key) is not False:
            raise ValueError(f"R52 R11 must keep {false_key}=False")
    if data.get("decision_ref") not in P7_R52_R11_DECISION_REF_REFS or data.get("decision_status") not in P7_R52_R5_DECISION_STATUS_REFS:
        raise ValueError("R52 R11 decision changed")
    if data.get("p6_limited_human_readfeel_candidate_separation_status") not in P7_R52_R11_CANDIDATE_STATUS_REFS:
        raise ValueError("R52 R11 candidate separation status changed")
    if data.get("p5_human_blind_qa_confirmed") is not False or data.get("p5_human_blind_qa_confirmed_final") is not False:
        raise ValueError("R52 R11 must not finalize P5")
    if data.get("p6_limited_human_readfeel_start_allowed") is not False:
        raise ValueError("R52 R11 must not start P6")
    if data.get("p8_question_design_material_candidate") is not False or data.get("p8_start_allowed") is not False or data.get("p7_complete") is not False or data.get("release_allowed") is not False:
        raise ValueError("R52 R11 must not expose P8, complete P7, or release")
    if data.get("r10_ready_for_r52_11_p6_limited_human_readfeel_candidate_separation") is True and data.get("p6_limited_human_readfeel_candidate_supported") is True:
        if data.get("decision_ref") != "R52_P6_LIMITED_READFEEL_START_CANDIDATE_ONLY" or data.get("decision_status") != "CANDIDATE_ONLY":
            raise ValueError("R52 R11 supported P6 candidate must remain candidate-only")
        if data.get("p6_limited_human_readfeel_start_allowed_candidate") is not True or data.get("p6_limited_human_readfeel_start_allowed") is not False:
            raise ValueError("R52 R11 supported P6 candidate must not become start allowed")
        if data.get("next_required_step") != P7_R52_R11_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R52 R11 supported P6 candidate must point to R52-12")
        if tuple(data.get("implemented_steps") or ()) != P7_R52_R11_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R52_R11_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R52 R11 implemented/not-yet steps changed")
    if data.get("r10_ready_for_r52_11_p6_limited_human_readfeel_candidate_separation") is not True:
        if data.get("p6_limited_human_readfeel_start_allowed_candidate") is not False or data.get("r52_11_p6_limited_human_readfeel_candidate_separation_built") is not False:
            raise ValueError("R52 R11 not reached must not create a P6 candidate")
    return True


def build_p7_r52_r0_r10_p5_confirmed_candidate_decision_chain(
    *,
    current_received_snapshot_refreeze: Mapping[str, Any] | None = None,
    validation_evidence_matrix_freeze: Mapping[str, Any] | None = None,
    r51_bodyfree_handoff_materials: Sequence[Mapping[str, Any]] | None = None,
    r51_actual_review_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return R52-10 material after validating R52-0/R52-10 body-free gates."""
    r9 = build_p7_r52_r0_r9_rating_question_p5_readfeel_gate_chain(
        current_received_snapshot_refreeze=current_received_snapshot_refreeze,
        validation_evidence_matrix_freeze=validation_evidence_matrix_freeze,
        r51_bodyfree_handoff_materials=r51_bodyfree_handoff_materials,
        r51_actual_review_evidence=r51_actual_review_evidence,
    )
    assert_p7_r52_p5_readfeel_blocker_gate_contract(r9)
    r10 = build_p7_r52_p5_confirmed_candidate_decision(
        p5_readfeel_blocker_gate=r9,
        r51_actual_review_evidence=r51_actual_review_evidence,
        r51_bodyfree_handoff_materials=r51_bodyfree_handoff_materials,
    )
    assert_p7_r52_p5_confirmed_candidate_decision_contract(r10)
    return r10


def build_p7_r52_r0_r11_p6_limited_human_readfeel_candidate_separation_chain(
    *,
    current_received_snapshot_refreeze: Mapping[str, Any] | None = None,
    validation_evidence_matrix_freeze: Mapping[str, Any] | None = None,
    r51_bodyfree_handoff_materials: Sequence[Mapping[str, Any]] | None = None,
    r51_actual_review_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return R52-11 material after validating R52-0/R52-11 body-free gates."""
    r10 = build_p7_r52_r0_r10_p5_confirmed_candidate_decision_chain(
        current_received_snapshot_refreeze=current_received_snapshot_refreeze,
        validation_evidence_matrix_freeze=validation_evidence_matrix_freeze,
        r51_bodyfree_handoff_materials=r51_bodyfree_handoff_materials,
        r51_actual_review_evidence=r51_actual_review_evidence,
    )
    assert_p7_r52_p5_confirmed_candidate_decision_contract(r10)
    r11 = build_p7_r52_p6_limited_human_readfeel_candidate_separation(
        p5_confirmed_candidate_decision=r10,
        r51_actual_review_evidence=r51_actual_review_evidence,
        r51_bodyfree_handoff_materials=r51_bodyfree_handoff_materials,
    )
    assert_p7_r52_p6_limited_human_readfeel_candidate_separation_contract(r11)
    return r11


# ---------------------------------------------------------------------------
# R52-12 / R52-13: P8 material candidate separation + final decision composer.
# ---------------------------------------------------------------------------

P7_R52_P8_QUESTION_MATERIAL_CANDIDATE_SEPARATION_SCHEMA_VERSION: Final = "cocolon.emlis.p7_r52.p8_question_material_candidate_separation.bodyfree.v1"
P7_R52_FINAL_DECISION_COMPOSER_SCHEMA_VERSION: Final = "cocolon.emlis.p7_r52.final_decision_composer.bodyfree.v1"

P7_R52_R12_STEP_REF: Final = "R52-12_p8_question_material_candidate_separation"
P7_R52_R13_STEP_REF: Final = "R52-13_final_decision_composer"
P7_R52_R12_NEXT_REQUIRED_STEP_REF: Final = P7_R52_R13_STEP_REF
P7_R52_R13_NEXT_REQUIRED_STEP_REF: Final = "R52-14_no_touch_boundary_validation"
P7_R52_FUTURE_STEPS_AFTER_R13: Final[tuple[str, ...]] = P7_R52_FUTURE_STEPS_AFTER_R11[2:]
P7_R52_R12_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R52_R11_IMPLEMENTED_STEPS, P7_R52_R12_STEP_REF)
P7_R52_R12_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R52_R13_STEP_REF, *P7_R52_FUTURE_STEPS_AFTER_R13)
P7_R52_R13_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R52_R12_IMPLEMENTED_STEPS, P7_R52_R13_STEP_REF)
P7_R52_R13_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R52_FUTURE_STEPS_AFTER_R13
P7_R52_CURRENT_IMPLEMENTED_STEPS = P7_R52_R13_IMPLEMENTED_STEPS
P7_R52_CURRENT_NOT_YET_IMPLEMENTED_STEPS = P7_R52_R13_NOT_YET_IMPLEMENTED_STEPS

P7_R52_R12_DECISION_REF_REFS: Final[tuple[str, ...]] = (*P7_R52_R11_DECISION_REF_REFS, "R52_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_ONLY")
P7_R52_R13_DECISION_REF_REFS: Final[tuple[str, ...]] = (*P7_R52_R12_DECISION_REF_REFS, "R52_NO_GO_P6_P8_START")
P7_R52_R12_CANDIDATE_STATUS_REFS: Final[tuple[str, ...]] = (
    "R52_P8_QUESTION_MATERIAL_CANDIDATE_SEPARATION_PASSED_WITH_CANDIDATE",
    "R52_P8_QUESTION_MATERIAL_CANDIDATE_SEPARATION_PASSED_WITHOUT_CANDIDATE",
    "R52_P8_QUESTION_MATERIAL_CANDIDATE_SEPARATION_NOT_REACHED_BY_R11",
    "R52_P8_QUESTION_MATERIAL_CANDIDATE_SEPARATION_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED",
    "R52_P8_QUESTION_MATERIAL_CANDIDATE_SEPARATION_RETURN_TO_P5_REPAIR_REQUIRED",
    "R52_P8_QUESTION_MATERIAL_CANDIDATE_SEPARATION_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK",
    "R52_P8_QUESTION_MATERIAL_CANDIDATE_SEPARATION_BLOCKED_BY_DISPOSAL_NOT_VERIFIED",
    "R52_P8_QUESTION_MATERIAL_CANDIDATE_SEPARATION_BLOCKED_BY_EXECUTION_BLOCKER_OPEN",
    "R52_P8_QUESTION_MATERIAL_CANDIDATE_SEPARATION_BLOCKED_BY_CONSISTENCY_ISSUE",
    "R52_P8_QUESTION_MATERIAL_CANDIDATE_SEPARATION_INCONCLUSIVE",
)
P7_R52_R13_COMPOSER_STATUS_REFS: Final[tuple[str, ...]] = (
    "R52_FINAL_DECISION_COMPOSED_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED",
    "R52_FINAL_DECISION_COMPOSED_RETURN_TO_P5_REPAIR_REQUIRED",
    "R52_FINAL_DECISION_COMPOSED_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK",
    "R52_FINAL_DECISION_COMPOSED_BLOCKED_BY_DISPOSAL_NOT_VERIFIED",
    "R52_FINAL_DECISION_COMPOSED_BLOCKED_BY_EXECUTION_BLOCKER_OPEN",
    "R52_FINAL_DECISION_COMPOSED_BLOCKED_BY_CONSISTENCY_ISSUE",
    "R52_FINAL_DECISION_COMPOSED_INCONCLUSIVE",
    "R52_FINAL_DECISION_COMPOSED_CANDIDATE_ONLY_WITH_P8_MATERIAL",
    "R52_FINAL_DECISION_COMPOSED_CANDIDATE_ONLY_WITH_P6_READFEEL",
    "R52_FINAL_DECISION_COMPOSED_CANDIDATE_ONLY_WITH_P5_REVIEWED_NOT_FINAL",
    "R52_FINAL_DECISION_COMPOSED_NO_GO_P6_P8_START",
)

P7_R52_R12_EXTRA_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    "p8_question_material_candidate_promoted_to_start_allowed_here", "p8_question_detail_design_started_here",
    "p8_question_detail_design_finalized_here", "p8_question_runtime_started_here", "question_text_generated_here",
    "draft_question_text_generated_here", "question_trigger_logic_finalized_here", "question_trigger_logic_implemented_here",
    "question_api_db_rn_contract_designed_here", "p8_api_db_rn_response_key_design_finalized_here", "question_response_key_designed_here", "question_storage_schema_materialized_here",
    "question_need_observation_rows_created_here", "p8_question_material_candidate_used_to_complete_p7_here",
    "p8_question_material_candidate_used_to_release_here",
)
P7_R52_R12_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(dict.fromkeys((
    *(key for key in P7_R52_R11_FALSE_KEY_REFS if key != "p8_question_design_material_candidate"),
    *P7_R52_R12_EXTRA_FALSE_KEY_REFS,
)))
P7_R52_R13_EXTRA_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    "r52_final_decision_composer_promoted_p5_candidate_to_final_here", "r52_final_decision_composer_started_p6_here",
    "r52_final_decision_composer_started_p8_here", "r52_final_decision_composer_completed_p7_here",
    "r52_final_decision_composer_allowed_release_here", "r52_final_decision_composer_changed_api_db_rn_or_runtime_here",
    "r52_final_decision_composer_materialized_schema_file_here", "final_decision_claimed_as_p8_start_allowed_here", "final_decision_claimed_as_p6_start_allowed_here", "final_decision_claimed_as_release_allowed_here",
)
P7_R52_R13_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(dict.fromkeys((*P7_R52_R12_FALSE_KEY_REFS, *P7_R52_R13_EXTRA_FALSE_KEY_REFS)))

P7_R52_R12_BASE_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "current_phase", "material_id",
    "review_session_id", "required_case_count", "r11_p6_candidate_schema_version", "r11_p6_candidate_material_ref", "r11_decision_ref",
    "r11_decision_status", "r11_p6_limited_human_readfeel_candidate_separation_status", "r11_ready_for_r52_12_p8_question_material_candidate_separation",
    "r51_actual_review_evidence_complete", "p5_decision_status", "p5_human_blind_qa_confirmed_candidate", "p5_human_blind_qa_confirmed", "p5_human_blind_qa_confirmed_final",
    "p6_limited_human_readfeel_start_allowed_candidate", "p6_limited_human_readfeel_start_allowed",
    "r51_p8_question_design_material_candidate_handoff_reported", "question_observation_row_count", "question_need_primary_class_counts",
    "question_need_primary_class_count_refs", "question_need_primary_class_counts_body_free", "question_need_primary_class_counts_present",
    "one_question_fit_count", "ambiguity_kind_counts", "plus_one_question_candidate_count", "premium_deepening_candidate_count",
    "repair_required_not_question_count", "p8_candidate_repair_required_not_question_count", "red_or_repair_required_question_candidate_count",
    "p5_repair_target_mixed_into_p8_candidate", "repair_required_not_question_mixed_into_p8_candidate", "red_or_repair_required_treated_as_question_candidate",
    "p5_weakness_not_hidden_by_question_candidate", "p8_candidate_critical_repair_blocker_count", "p8_candidate_creepy_or_surveillance_blocker_count",
    "p8_candidate_overclaim_blocker_count", "p8_candidate_self_blame_amplification_blocker_count", "p8_candidate_blocker_detected",
    "p8_question_design_material_candidate_supported", "p8_question_design_material_candidate_reason_refs", "p8_question_material_candidate_separation_status",
    "decision_ref", "decision_status", "decision_reason_refs", "next_required_step", "p8_question_design_material_candidate", "p8_start_allowed", "p7_complete", "release_allowed",
    "r52_0_current_received_snapshot_refrozen", "r52_1_validation_evidence_matrix_frozen", "r52_2_r51_bodyfree_handoff_intake_contract_built", "r52_3_forbidden_payload_deep_scan_built",
    "r52_4_actual_review_evidence_completeness_checker_built", "r52_5_evidence_missing_no_go_branch_built", "r52_6_disposal_safety_gate_built", "r52_7_execution_blocker_gate_built",
    "r52_8_rating_question_consistency_gate_built", "r52_9_p5_readfeel_blocker_gate_built", "r52_10_p5_confirmed_candidate_decision_built",
    "r52_11_p6_limited_human_readfeel_candidate_separation_built", "r52_12_p8_question_material_candidate_separation_built", "r52_12_ready_for_r52_13_final_decision_composer",
    "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "public_contract", "r52_public_no_touch_contract", "body_free_markers", "body_free",
)
P7_R52_R12_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = tuple(dict.fromkeys((*P7_R52_R12_BASE_FIELD_REFS, *P7_R52_R12_FALSE_KEY_REFS)))
P7_R52_R13_BASE_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "current_phase", "material_id",
    "review_session_id", "required_case_count", "r12_p8_candidate_schema_version", "r12_p8_candidate_material_ref", "r12_decision_ref",
    "r12_decision_status", "r12_p8_question_material_candidate_separation_status", "r12_ready_for_r52_13_final_decision_composer",
    "r51_actual_review_evidence_complete", "p5_decision_status", "p5_human_blind_qa_confirmed_candidate", "p5_human_blind_qa_confirmed", "p5_human_blind_qa_confirmed_final",
    "p6_limited_human_readfeel_start_allowed_candidate", "p6_limited_human_readfeel_start_allowed", "p8_question_design_material_candidate", "p8_start_allowed", "p7_complete", "release_allowed",
    "candidate_summary_refs", "no_auto_allow_summary_refs", "decision_ref", "decision_status", "decision_reason_refs", "next_required_step", "final_decision_composer_status",
    "public_contract", "r52_public_no_touch_contract", "body_free_markers", "body_free", "r52_0_current_received_snapshot_refrozen", "r52_1_validation_evidence_matrix_frozen",
    "r52_2_r51_bodyfree_handoff_intake_contract_built", "r52_3_forbidden_payload_deep_scan_built", "r52_4_actual_review_evidence_completeness_checker_built",
    "r52_5_evidence_missing_no_go_branch_built", "r52_6_disposal_safety_gate_built", "r52_7_execution_blocker_gate_built", "r52_8_rating_question_consistency_gate_built",
    "r52_9_p5_readfeel_blocker_gate_built", "r52_10_p5_confirmed_candidate_decision_built", "r52_11_p6_limited_human_readfeel_candidate_separation_built",
    "r52_12_p8_question_material_candidate_separation_built", "r52_13_final_decision_composer_built", "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref",
)
P7_R52_R13_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = tuple(dict.fromkeys((*P7_R52_R13_BASE_FIELD_REFS, *P7_R52_R13_FALSE_KEY_REFS)))
P7_R52_P8_QUESTION_MATERIAL_CANDIDATE_SEPARATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = P7_R52_R12_REQUIRED_FIELD_REFS
P7_R52_FINAL_DECISION_COMPOSER_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = P7_R52_R13_REQUIRED_FIELD_REFS


def _r52_false_flags_r12() -> dict[str, bool]:
    return {key: False for key in P7_R52_R12_FALSE_KEY_REFS}


def _r52_false_flags_r13() -> dict[str, bool]:
    return {key: False for key in P7_R52_R13_FALSE_KEY_REFS}


def _r52_safe_count_mapping(value: Any, *, limit: int = 40) -> dict[str, int]:
    if not isinstance(value, Mapping):
        return {}
    out: dict[str, int] = {}
    for key, raw_count in value.items():
        safe_key = clean_identifier(key, default="unknown_question_need_class", max_length=120)
        if safe_key:
            out[safe_key] = _safe_non_negative_int(raw_count)
        if len(out) >= limit:
            break
    return out


def _r52_evidence_count_mapping(evidence: Mapping[str, Any], *keys: str, limit: int = 40) -> dict[str, int]:
    for key in keys:
        if key in evidence:
            return _r52_safe_count_mapping(evidence.get(key), limit=limit)
    return {}


def _r52_r11_ready_for_p8_question_material_candidate_separation(r11: Mapping[str, Any]) -> bool:
    return (
        r11.get("r52_11_ready_for_r52_12_p8_question_material_candidate_separation") is True
        and r11.get("r51_actual_review_evidence_complete") is True
        and r11.get("p5_decision_status") == "R52_P5_CONFIRMED_CANDIDATE_REVIEWED_NOT_FINAL"
        and r11.get("p5_human_blind_qa_confirmed_candidate") is True
        and r11.get("decision_status") == "CANDIDATE_ONLY"
        and r11.get("decision_ref") in {"R52_P6_LIMITED_READFEEL_START_CANDIDATE_ONLY", "R52_NO_GO_P6_P8_START"}
    )


def _r52_p8_candidate_values(
    *,
    p6_limited_human_readfeel_candidate_separation: Mapping[str, Any],
    r51_actual_review_evidence: Mapping[str, Any] | None,
    r51_bodyfree_handoff_materials: Sequence[Mapping[str, Any]] | None,
) -> dict[str, Any]:
    r11 = safe_mapping(p6_limited_human_readfeel_candidate_separation)
    evidence = safe_mapping(r51_actual_review_evidence)
    normalized_reported_flags = _r52_reported_flag_refs_from_materials(r51_bodyfree_handoff_materials)
    handoff_reported = (
        "r51_reported_p8_question_design_material_candidate" in normalized_reported_flags
        or _r52_evidence_bool(evidence, "r51_p8_question_design_material_candidate_handoff_reported", default=False)
        or _r52_evidence_bool(evidence, "p8_question_design_material_candidate_supported_by_handoff", default=False)
    )
    question_observation_row_count = _r52_evidence_int(evidence, "question_observation_row_count", "r51_question_observation_row_count")
    primary_counts = _r52_evidence_count_mapping(evidence, "question_need_primary_class_counts", "question_primary_class_counts", "p8_question_need_primary_class_counts")
    ambiguity_counts = _r52_evidence_count_mapping(evidence, "ambiguity_kind_counts", "p8_ambiguity_kind_counts")
    primary_count_refs = dedupe_identifiers(primary_counts.keys(), limit=80, max_length=120)
    primary_counts_present = bool(primary_counts)
    primary_counts_body_free = _r52_evidence_bool(evidence, "question_need_primary_class_counts_body_free", default=primary_counts_present)
    consistency_passed = clean_identifier(evidence.get("rating_question_consistency_status"), default="missing", max_length=80) == "passed"
    repair_required_not_question_count = _r52_evidence_int(evidence, "repair_required_not_question_count")
    p8_repair_required_not_question_count = _r52_evidence_int(evidence, "p8_candidate_repair_required_not_question_count")
    red_or_repair_question_candidate_count = _r52_evidence_int(evidence, "red_or_repair_required_question_candidate_count")
    p5_repair_target_mixed = _r52_evidence_bool(evidence, "p5_repair_target_mixed_into_p8_candidate", "p5_repair_return_target_mixed_into_p8_candidate")
    repair_not_question_mixed = _r52_evidence_bool(evidence, "repair_required_not_question_mixed_into_p8_candidate")
    red_or_repair_treated = _r52_evidence_bool(evidence, "red_or_repair_required_treated_as_question_candidate")
    p5_weakness_not_hidden = _r52_evidence_bool(evidence, "p5_weakness_not_hidden_by_question_candidate", default=True)
    blocker_counts = {
        "p8_candidate_critical_repair_blocker_count": _r52_evidence_int(evidence, "critical_repair_blocker_count", "p8_candidate_critical_repair_blocker_count"),
        "p8_candidate_creepy_or_surveillance_blocker_count": _r52_evidence_int(evidence, "creepy_or_surveillance_blocker_count", "p8_candidate_creepy_or_surveillance_blocker_count"),
        "p8_candidate_overclaim_blocker_count": _r52_evidence_int(evidence, "overclaim_blocker_count", "p8_candidate_overclaim_blocker_count"),
        "p8_candidate_self_blame_amplification_blocker_count": _r52_evidence_int(evidence, "self_blame_amplification_blocker_count", "p8_candidate_self_blame_amplification_blocker_count"),
    }
    reasons: list[str] = []
    if not _r52_r11_ready_for_p8_question_material_candidate_separation(r11):
        reasons.append("r52_11_not_ready_for_p8_question_material_candidate_separation")
    if not handoff_reported:
        reasons.append("r51_p8_question_design_material_candidate_handoff_not_reported")
    if question_observation_row_count < P7_R51_REQUIRED_CASE_COUNT:
        reasons.append("r51_question_observation_rows_missing_or_below_required_case_count")
    if not consistency_passed:
        reasons.append("rating_question_consistency_not_passed_for_p8_material_candidate")
    if not primary_counts_present:
        reasons.append("question_need_primary_class_counts_missing")
    if not primary_counts_body_free:
        reasons.append("question_need_primary_class_counts_not_body_free")
    if repair_required_not_question_count > 0 or p8_repair_required_not_question_count > 0 or repair_not_question_mixed:
        reasons.append("repair_required_not_question_mixed_or_present_for_p8_candidate")
    if red_or_repair_question_candidate_count > 0 or red_or_repair_treated:
        reasons.append("red_or_repair_required_treated_as_question_candidate")
    if p5_repair_target_mixed:
        reasons.append("p5_repair_target_mixed_into_p8_candidate")
    if not p5_weakness_not_hidden:
        reasons.append("p5_weakness_would_be_hidden_by_p8_question_candidate")
    if blocker_counts["p8_candidate_critical_repair_blocker_count"] > 0:
        reasons.append("p8_candidate_blocked_by_critical_repair_blocker")
    if blocker_counts["p8_candidate_creepy_or_surveillance_blocker_count"] > 0:
        reasons.append("p8_candidate_blocked_by_creepy_or_surveillance_blocker")
    if blocker_counts["p8_candidate_overclaim_blocker_count"] > 0:
        reasons.append("p8_candidate_blocked_by_overclaim_blocker")
    if blocker_counts["p8_candidate_self_blame_amplification_blocker_count"] > 0:
        reasons.append("p8_candidate_blocked_by_self_blame_amplification_blocker")
    reason_refs = dedupe_identifiers(reasons, limit=160, max_length=220)
    return {
        "r51_p8_question_design_material_candidate_handoff_reported": handoff_reported,
        "question_observation_row_count": question_observation_row_count,
        "question_need_primary_class_counts": primary_counts,
        "question_need_primary_class_count_refs": primary_count_refs,
        "question_need_primary_class_counts_body_free": primary_counts_body_free,
        "question_need_primary_class_counts_present": primary_counts_present,
        "one_question_fit_count": _r52_evidence_int(evidence, "one_question_fit_count", "p8_one_question_fit_count"),
        "ambiguity_kind_counts": ambiguity_counts,
        "plus_one_question_candidate_count": _r52_evidence_int(evidence, "plus_one_question_candidate_count", "p8_plus_one_question_candidate_count"),
        "premium_deepening_candidate_count": _r52_evidence_int(evidence, "premium_deepening_candidate_count", "p8_premium_deepening_candidate_count"),
        "repair_required_not_question_count": repair_required_not_question_count,
        "p8_candidate_repair_required_not_question_count": p8_repair_required_not_question_count,
        "red_or_repair_required_question_candidate_count": red_or_repair_question_candidate_count,
        "p5_repair_target_mixed_into_p8_candidate": p5_repair_target_mixed,
        "repair_required_not_question_mixed_into_p8_candidate": repair_not_question_mixed,
        "red_or_repair_required_treated_as_question_candidate": red_or_repair_treated,
        "p5_weakness_not_hidden_by_question_candidate": p5_weakness_not_hidden,
        **blocker_counts,
        "p8_candidate_blocker_detected": bool(reason_refs),
        "p8_question_design_material_candidate_supported": not bool(reason_refs),
        "p8_question_design_material_candidate_reason_refs": reason_refs or ["r51_p8_question_material_handoff_bodyfree_counts_consistent_candidate_only"],
    }


def build_p7_r52_p8_question_material_candidate_separation(
    *,
    p6_limited_human_readfeel_candidate_separation: Mapping[str, Any] | None = None,
    r51_actual_review_evidence: Mapping[str, Any] | None = None,
    current_received_snapshot_refreeze: Mapping[str, Any] | None = None,
    validation_evidence_matrix_freeze: Mapping[str, Any] | None = None,
    r51_bodyfree_handoff_materials: Sequence[Mapping[str, Any]] | None = None,
    material_id: str = "p7_r52_p8_question_material_candidate_separation",
) -> dict[str, Any]:
    """Build R52-12: separate P8 material candidate from P8 start permission."""
    r11 = safe_mapping(p6_limited_human_readfeel_candidate_separation) if p6_limited_human_readfeel_candidate_separation is not None else build_p7_r52_r0_r11_p6_limited_human_readfeel_candidate_separation_chain(
        current_received_snapshot_refreeze=current_received_snapshot_refreeze,
        validation_evidence_matrix_freeze=validation_evidence_matrix_freeze,
        r51_bodyfree_handoff_materials=r51_bodyfree_handoff_materials,
        r51_actual_review_evidence=r51_actual_review_evidence,
    )
    assert_p7_r52_p6_limited_human_readfeel_candidate_separation_contract(r11)
    values = _r52_p8_candidate_values(p6_limited_human_readfeel_candidate_separation=r11, r51_actual_review_evidence=r51_actual_review_evidence, r51_bodyfree_handoff_materials=r51_bodyfree_handoff_materials)
    prior = clean_identifier(r11.get("decision_ref"), default="R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED", max_length=180)
    r11_ready = _r52_r11_ready_for_p8_question_material_candidate_separation(r11)
    if prior == "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK":
        decision_ref, decision_status, separation_status = prior, "BLOCKED", "R52_P8_QUESTION_MATERIAL_CANDIDATE_SEPARATION_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK"
        reasons = dedupe_identifiers([*(r11.get("decision_reason_refs") or []), "r52_12_blocked_by_prior_body_free_boundary_risk"], limit=180, max_length=220)
        next_step = clean_identifier(r11.get("next_required_step"), default=P7_R52_R4_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220)
        implemented_steps, not_yet_steps, built, p8_candidate = P7_R52_R11_IMPLEMENTED_STEPS, P7_R52_R11_NOT_YET_IMPLEMENTED_STEPS, False, False
    elif prior == "R52_BLOCKED_BY_DISPOSAL_NOT_VERIFIED":
        decision_ref, decision_status, separation_status = prior, "BLOCKED", "R52_P8_QUESTION_MATERIAL_CANDIDATE_SEPARATION_BLOCKED_BY_DISPOSAL_NOT_VERIFIED"
        reasons = dedupe_identifiers([*(r11.get("decision_reason_refs") or []), "r52_12_blocked_by_prior_disposal_not_verified"], limit=180, max_length=220)
        next_step = clean_identifier(r11.get("next_required_step"), default=P7_R52_R6_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220)
        implemented_steps, not_yet_steps, built, p8_candidate = P7_R52_R11_IMPLEMENTED_STEPS, P7_R52_R11_NOT_YET_IMPLEMENTED_STEPS, False, False
    elif prior == "R52_BLOCKED_BY_EXECUTION_BLOCKER_OPEN":
        decision_ref, decision_status, separation_status = prior, "BLOCKED", "R52_P8_QUESTION_MATERIAL_CANDIDATE_SEPARATION_BLOCKED_BY_EXECUTION_BLOCKER_OPEN"
        reasons = dedupe_identifiers([*(r11.get("decision_reason_refs") or []), "r52_12_blocked_by_prior_execution_blocker_open"], limit=180, max_length=220)
        next_step = clean_identifier(r11.get("next_required_step"), default=P7_R52_R7_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220)
        implemented_steps, not_yet_steps, built, p8_candidate = P7_R52_R11_IMPLEMENTED_STEPS, P7_R52_R11_NOT_YET_IMPLEMENTED_STEPS, False, False
    elif prior == "R52_BLOCKED_BY_RATING_QUESTION_OBSERVATION_INCONSISTENCY":
        decision_ref, decision_status, separation_status = prior, "BLOCKED", "R52_P8_QUESTION_MATERIAL_CANDIDATE_SEPARATION_BLOCKED_BY_CONSISTENCY_ISSUE"
        reasons = dedupe_identifiers([*(r11.get("decision_reason_refs") or []), "r52_12_blocked_by_prior_rating_question_consistency_issue"], limit=180, max_length=220)
        next_step = clean_identifier(r11.get("next_required_step"), default=P7_R52_R8_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220)
        implemented_steps, not_yet_steps, built, p8_candidate = P7_R52_R11_IMPLEMENTED_STEPS, P7_R52_R11_NOT_YET_IMPLEMENTED_STEPS, False, False
    elif prior == "R52_RETURN_TO_P5_REPAIR_REQUIRED":
        decision_ref, decision_status, separation_status = prior, "RETURN_REQUIRED", "R52_P8_QUESTION_MATERIAL_CANDIDATE_SEPARATION_RETURN_TO_P5_REPAIR_REQUIRED"
        reasons = dedupe_identifiers([*(r11.get("decision_reason_refs") or []), "r52_12_return_to_p5_repair_before_p8_material_candidate"], limit=180, max_length=220)
        next_step = clean_identifier(r11.get("next_required_step"), default=P7_R52_R9_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220)
        implemented_steps, not_yet_steps, built, p8_candidate = P7_R52_R11_IMPLEMENTED_STEPS, P7_R52_R11_NOT_YET_IMPLEMENTED_STEPS, False, False
    elif prior == "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED" or not r11_ready:
        decision_ref = prior
        decision_status = clean_identifier(r11.get("decision_status"), default="RETURN_REQUIRED", max_length=80)
        separation_status = "R52_P8_QUESTION_MATERIAL_CANDIDATE_SEPARATION_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED" if prior == "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED" else "R52_P8_QUESTION_MATERIAL_CANDIDATE_SEPARATION_NOT_REACHED_BY_R11"
        reasons = dedupe_identifiers([*(r11.get("decision_reason_refs") or []), *values["p8_question_design_material_candidate_reason_refs"]], limit=180, max_length=220)
        next_step = clean_identifier(r11.get("next_required_step"), default=P7_R52_R5_RETURN_TO_R51_NEXT_REQUIRED_STEP_REF, max_length=220)
        implemented_steps, not_yet_steps, built, p8_candidate = P7_R52_R11_IMPLEMENTED_STEPS, P7_R52_R11_NOT_YET_IMPLEMENTED_STEPS, False, False
    elif prior == "R52_INCONCLUSIVE_RETURN_TO_R51_REVIEW_OR_RECHECK":
        decision_ref, decision_status, separation_status = prior, "INCONCLUSIVE", "R52_P8_QUESTION_MATERIAL_CANDIDATE_SEPARATION_INCONCLUSIVE"
        reasons = dedupe_identifiers([*(r11.get("decision_reason_refs") or []), "r52_12_inconclusive_before_p8_material_candidate"], limit=180, max_length=220)
        next_step = clean_identifier(r11.get("next_required_step"), default=P7_R52_R10_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220)
        implemented_steps, not_yet_steps, built, p8_candidate = P7_R52_R11_IMPLEMENTED_STEPS, P7_R52_R11_NOT_YET_IMPLEMENTED_STEPS, False, False
    elif values["p8_question_design_material_candidate_supported"] is True:
        decision_ref, decision_status, separation_status = "R52_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_ONLY", "CANDIDATE_ONLY", "R52_P8_QUESTION_MATERIAL_CANDIDATE_SEPARATION_PASSED_WITH_CANDIDATE"
        reasons, next_step = values["p8_question_design_material_candidate_reason_refs"], P7_R52_R12_NEXT_REQUIRED_STEP_REF
        implemented_steps, not_yet_steps, built, p8_candidate = P7_R52_R12_IMPLEMENTED_STEPS, P7_R52_R12_NOT_YET_IMPLEMENTED_STEPS, True, True
    else:
        decision_ref = prior if prior == "R52_P6_LIMITED_READFEEL_START_CANDIDATE_ONLY" else "R52_NO_GO_P6_P8_START"
        decision_status, separation_status = "CANDIDATE_ONLY", "R52_P8_QUESTION_MATERIAL_CANDIDATE_SEPARATION_PASSED_WITHOUT_CANDIDATE"
        reasons, next_step = values["p8_question_design_material_candidate_reason_refs"], P7_R52_R12_NEXT_REQUIRED_STEP_REF
        implemented_steps, not_yet_steps, built, p8_candidate = P7_R52_R12_IMPLEMENTED_STEPS, P7_R52_R12_NOT_YET_IMPLEMENTED_STEPS, True, False
    gate = {
        "schema_version": P7_R52_P8_QUESTION_MATERIAL_CANDIDATE_SEPARATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R52_STEP,
        "scope": P7_R52_SCOPE,
        "policy_kind": P7_R52_POLICY_KIND,
        "policy_section": P7_R52_R12_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r52_p8_question_material_candidate_separation", max_length=180),
        "review_session_id": clean_identifier(r11.get("review_session_id"), default=P7_R52_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "r11_p6_candidate_schema_version": P7_R52_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_SEPARATION_SCHEMA_VERSION,
        "r11_p6_candidate_material_ref": clean_identifier(r11.get("material_id"), default="p7_r52_p6_limited_human_readfeel_candidate_separation", max_length=180),
        "r11_decision_ref": prior,
        "r11_decision_status": clean_identifier(r11.get("decision_status"), default="RETURN_REQUIRED", max_length=80),
        "r11_p6_limited_human_readfeel_candidate_separation_status": clean_identifier(r11.get("p6_limited_human_readfeel_candidate_separation_status"), default="R52_P6_LIMITED_READFEEL_CANDIDATE_SEPARATION_NOT_REACHED_BY_R10", max_length=180),
        "r11_ready_for_r52_12_p8_question_material_candidate_separation": r11_ready,
        "r51_actual_review_evidence_complete": r11.get("r51_actual_review_evidence_complete") is True,
        "p5_decision_status": clean_identifier(r11.get("p5_decision_status"), default="R52_P5_NOT_REVIEWED_EVIDENCE_MISSING", max_length=180),
        "p5_human_blind_qa_confirmed_candidate": r11.get("p5_human_blind_qa_confirmed_candidate") is True,
        "p5_human_blind_qa_confirmed": False,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_start_allowed_candidate": r11.get("p6_limited_human_readfeel_start_allowed_candidate") is True,
        "p6_limited_human_readfeel_start_allowed": False,
        **values,
        "p8_question_material_candidate_separation_status": separation_status,
        "decision_ref": decision_ref,
        "decision_status": decision_status,
        "decision_reason_refs": reasons,
        "next_required_step": next_step,
        "p8_question_design_material_candidate": p8_candidate,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "r52_0_current_received_snapshot_refrozen": True,
        "r52_1_validation_evidence_matrix_frozen": True,
        "r52_2_r51_bodyfree_handoff_intake_contract_built": True,
        "r52_3_forbidden_payload_deep_scan_built": r11.get("r52_3_forbidden_payload_deep_scan_built") is True,
        "r52_4_actual_review_evidence_completeness_checker_built": r11.get("r52_4_actual_review_evidence_completeness_checker_built") is True,
        "r52_5_evidence_missing_no_go_branch_built": r11.get("r52_5_evidence_missing_no_go_branch_built") is True,
        "r52_6_disposal_safety_gate_built": r11.get("r52_6_disposal_safety_gate_built") is True,
        "r52_7_execution_blocker_gate_built": r11.get("r52_7_execution_blocker_gate_built") is True,
        "r52_8_rating_question_consistency_gate_built": r11.get("r52_8_rating_question_consistency_gate_built") is True,
        "r52_9_p5_readfeel_blocker_gate_built": r11.get("r52_9_p5_readfeel_blocker_gate_built") is True,
        "r52_10_p5_confirmed_candidate_decision_built": r11.get("r52_10_p5_confirmed_candidate_decision_built") is True,
        "r52_11_p6_limited_human_readfeel_candidate_separation_built": r11.get("r52_11_p6_limited_human_readfeel_candidate_separation_built") is True,
        "r52_12_p8_question_material_candidate_separation_built": built,
        "r52_12_ready_for_r52_13_final_decision_composer": True,
        "implemented_steps": list(implemented_steps),
        "not_yet_implemented_steps": list(not_yet_steps),
        "first_next_work_ref": P7_R52_FIRST_NEXT_WORK_REF,
        "public_contract": public_contract_flags(),
        "r52_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_r52_false_flags_r12(),
    }
    assert_p7_r52_p8_question_material_candidate_separation_contract(gate)
    return gate


def assert_p7_r52_p8_question_material_candidate_separation_contract(gate: Mapping[str, Any]) -> bool:
    data = safe_mapping(gate)
    forbidden_paths = _r52_find_forbidden_key_paths(data, forbidden_keys=P7_R52_FORBIDDEN_PAYLOAD_KEY_REFS, path="p7_r52_r12_p8_question_material_candidate_separation")
    if forbidden_paths:
        raise ValueError(f"R52 R12 must remain body-free and question-text-free: {forbidden_paths[:6]}")
    missing = [field for field in P7_R52_R12_REQUIRED_FIELD_REFS if field not in data]
    if missing:
        raise ValueError(f"p7_r52_r12_p8_question_material_candidate_separation missing required fields: {missing[:6]}")
    if set(data) != set(P7_R52_R12_REQUIRED_FIELD_REFS):
        raise ValueError("R52 R12 must not contain body payload, question text, path, hash, or extra fields")
    _assert_body_free_common(data, schema_version=P7_R52_P8_QUESTION_MATERIAL_CANDIDATE_SEPARATION_SCHEMA_VERSION, source="p7_r52_r12_p8_question_material_candidate_separation")
    if data.get("policy_section") != P7_R52_R12_STEP_REF:
        raise ValueError("R52 R12 policy section changed")
    for false_key in P7_R52_R12_FALSE_KEY_REFS:
        if data.get(false_key) is not False:
            raise ValueError(f"R52 R12 must keep {false_key}=False")
    if data.get("decision_ref") not in P7_R52_R12_DECISION_REF_REFS or data.get("decision_status") not in P7_R52_R5_DECISION_STATUS_REFS:
        raise ValueError("R52 R12 decision changed")
    if data.get("p8_question_material_candidate_separation_status") not in P7_R52_R12_CANDIDATE_STATUS_REFS:
        raise ValueError("R52 R12 candidate separation status changed")
    if data.get("p5_human_blind_qa_confirmed") is not False or data.get("p5_human_blind_qa_confirmed_final") is not False:
        raise ValueError("R52 R12 must not finalize P5")
    if data.get("p6_limited_human_readfeel_start_allowed") is not False:
        raise ValueError("R52 R12 must not start P6")
    if data.get("p8_start_allowed") is not False or data.get("p7_complete") is not False or data.get("release_allowed") is not False:
        raise ValueError("R52 R12 must not start P8, complete P7, or release")
    if data.get("p8_question_design_material_candidate") is True:
        if data.get("decision_ref") != "R52_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_ONLY" or data.get("decision_status") != "CANDIDATE_ONLY":
            raise ValueError("R52 R12 P8 material candidate must remain candidate-only")
        if data.get("question_observation_row_count") < P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R52 R12 P8 candidate requires complete question observation rows")
        if data.get("question_need_primary_class_counts_present") is not True or data.get("question_need_primary_class_counts_body_free") is not True:
            raise ValueError("R52 R12 P8 candidate requires body-free primary class counts")
        if data.get("next_required_step") != P7_R52_R12_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R52 R12 P8 candidate must point to R52-13")
    if data.get("repair_required_not_question_mixed_into_p8_candidate") is True or data.get("red_or_repair_required_treated_as_question_candidate") is True:
        if data.get("p8_question_design_material_candidate") is not False:
            raise ValueError("R52 R12 must not turn repair-required material into P8 candidate")
    return True


def _r52_candidate_summary_refs_from_r12(r12: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    if r12.get("p5_human_blind_qa_confirmed_candidate") is True:
        refs.append("p5_confirmed_candidate_reviewed_not_final")
    if r12.get("p6_limited_human_readfeel_start_allowed_candidate") is True:
        refs.append("p6_limited_human_readfeel_candidate_only_not_start_allowed")
    if r12.get("p8_question_design_material_candidate") is True:
        refs.append("p8_question_design_material_candidate_only_not_start_allowed")
    return dedupe_identifiers(refs or ["no_p6_or_p8_start_candidate_after_r52_gate"], limit=20, max_length=180)


def _r52_final_composer_status_for_decision(decision_ref: str, r12: Mapping[str, Any]) -> str:
    if decision_ref == "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED":
        return "R52_FINAL_DECISION_COMPOSED_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED"
    if decision_ref == "R52_RETURN_TO_P5_REPAIR_REQUIRED":
        return "R52_FINAL_DECISION_COMPOSED_RETURN_TO_P5_REPAIR_REQUIRED"
    if decision_ref == "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK":
        return "R52_FINAL_DECISION_COMPOSED_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK"
    if decision_ref == "R52_BLOCKED_BY_DISPOSAL_NOT_VERIFIED":
        return "R52_FINAL_DECISION_COMPOSED_BLOCKED_BY_DISPOSAL_NOT_VERIFIED"
    if decision_ref == "R52_BLOCKED_BY_EXECUTION_BLOCKER_OPEN":
        return "R52_FINAL_DECISION_COMPOSED_BLOCKED_BY_EXECUTION_BLOCKER_OPEN"
    if decision_ref == "R52_BLOCKED_BY_RATING_QUESTION_OBSERVATION_INCONSISTENCY":
        return "R52_FINAL_DECISION_COMPOSED_BLOCKED_BY_CONSISTENCY_ISSUE"
    if decision_ref == "R52_INCONCLUSIVE_RETURN_TO_R51_REVIEW_OR_RECHECK":
        return "R52_FINAL_DECISION_COMPOSED_INCONCLUSIVE"
    if r12.get("p8_question_design_material_candidate") is True:
        return "R52_FINAL_DECISION_COMPOSED_CANDIDATE_ONLY_WITH_P8_MATERIAL"
    if r12.get("p6_limited_human_readfeel_start_allowed_candidate") is True:
        return "R52_FINAL_DECISION_COMPOSED_CANDIDATE_ONLY_WITH_P6_READFEEL"
    if r12.get("p5_human_blind_qa_confirmed_candidate") is True:
        return "R52_FINAL_DECISION_COMPOSED_CANDIDATE_ONLY_WITH_P5_REVIEWED_NOT_FINAL"
    return "R52_FINAL_DECISION_COMPOSED_NO_GO_P6_P8_START"


def build_p7_r52_final_decision_composer(
    *,
    p8_question_material_candidate_separation: Mapping[str, Any] | None = None,
    r51_actual_review_evidence: Mapping[str, Any] | None = None,
    current_received_snapshot_refreeze: Mapping[str, Any] | None = None,
    validation_evidence_matrix_freeze: Mapping[str, Any] | None = None,
    r51_bodyfree_handoff_materials: Sequence[Mapping[str, Any]] | None = None,
    material_id: str = "p7_r52_final_decision_composer",
) -> dict[str, Any]:
    """Build R52-13: final body-free decision summary without any auto-allow."""
    r12 = safe_mapping(p8_question_material_candidate_separation) if p8_question_material_candidate_separation is not None else build_p7_r52_p8_question_material_candidate_separation(
        current_received_snapshot_refreeze=current_received_snapshot_refreeze,
        validation_evidence_matrix_freeze=validation_evidence_matrix_freeze,
        r51_bodyfree_handoff_materials=r51_bodyfree_handoff_materials,
        r51_actual_review_evidence=r51_actual_review_evidence,
    )
    assert_p7_r52_p8_question_material_candidate_separation_contract(r12)
    prior = clean_identifier(r12.get("decision_ref"), default="R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED", max_length=180)
    if prior in {"R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK", "R52_BLOCKED_BY_DISPOSAL_NOT_VERIFIED", "R52_BLOCKED_BY_EXECUTION_BLOCKER_OPEN", "R52_BLOCKED_BY_RATING_QUESTION_OBSERVATION_INCONSISTENCY", "R52_RETURN_TO_P5_REPAIR_REQUIRED", "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED", "R52_INCONCLUSIVE_RETURN_TO_R51_REVIEW_OR_RECHECK"}:
        decision_ref = prior
        decision_status = clean_identifier(r12.get("decision_status"), default="RETURN_REQUIRED", max_length=80)
        next_step = clean_identifier(r12.get("next_required_step"), default=P7_R52_R13_NEXT_REQUIRED_STEP_REF, max_length=240)
    elif r12.get("p8_question_design_material_candidate") is True:
        decision_ref, decision_status, next_step = "R52_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_ONLY", "CANDIDATE_ONLY", P7_R52_R13_NEXT_REQUIRED_STEP_REF
    elif r12.get("p6_limited_human_readfeel_start_allowed_candidate") is True:
        decision_ref, decision_status, next_step = "R52_P6_LIMITED_READFEEL_START_CANDIDATE_ONLY", "CANDIDATE_ONLY", P7_R52_R13_NEXT_REQUIRED_STEP_REF
    elif r12.get("p5_human_blind_qa_confirmed_candidate") is True:
        decision_ref, decision_status, next_step = "R52_GO_P5_CONFIRMED_CANDIDATE_REVIEWED_BUT_NOT_RELEASE", "CANDIDATE_ONLY", P7_R52_R13_NEXT_REQUIRED_STEP_REF
    else:
        decision_ref, decision_status, next_step = "R52_NO_GO_P6_P8_START", "CANDIDATE_ONLY", P7_R52_R13_NEXT_REQUIRED_STEP_REF
    final_status = _r52_final_composer_status_for_decision(decision_ref, r12)
    reasons = dedupe_identifiers([*(r12.get("decision_reason_refs") or []), "r52_final_decision_composed_without_auto_allow", "p6_start_allowed_false", "p8_start_allowed_false", "p7_complete_false", "release_allowed_false"], limit=220, max_length=220)
    gate = {
        "schema_version": P7_R52_FINAL_DECISION_COMPOSER_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R52_STEP,
        "scope": P7_R52_SCOPE,
        "policy_kind": P7_R52_POLICY_KIND,
        "policy_section": P7_R52_R13_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r52_final_decision_composer", max_length=180),
        "review_session_id": clean_identifier(r12.get("review_session_id"), default=P7_R52_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "r12_p8_candidate_schema_version": P7_R52_P8_QUESTION_MATERIAL_CANDIDATE_SEPARATION_SCHEMA_VERSION,
        "r12_p8_candidate_material_ref": clean_identifier(r12.get("material_id"), default="p7_r52_p8_question_material_candidate_separation", max_length=180),
        "r12_decision_ref": prior,
        "r12_decision_status": clean_identifier(r12.get("decision_status"), default="RETURN_REQUIRED", max_length=80),
        "r12_p8_question_material_candidate_separation_status": clean_identifier(r12.get("p8_question_material_candidate_separation_status"), default="R52_P8_QUESTION_MATERIAL_CANDIDATE_SEPARATION_NOT_REACHED_BY_R11", max_length=180),
        "r12_ready_for_r52_13_final_decision_composer": r12.get("r52_12_ready_for_r52_13_final_decision_composer") is True,
        "r51_actual_review_evidence_complete": r12.get("r51_actual_review_evidence_complete") is True,
        "p5_decision_status": clean_identifier(r12.get("p5_decision_status"), default="R52_P5_NOT_REVIEWED_EVIDENCE_MISSING", max_length=180),
        "p5_human_blind_qa_confirmed_candidate": r12.get("p5_human_blind_qa_confirmed_candidate") is True,
        "p5_human_blind_qa_confirmed": False,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_start_allowed_candidate": r12.get("p6_limited_human_readfeel_start_allowed_candidate") is True,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_question_design_material_candidate": r12.get("p8_question_design_material_candidate") is True,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "candidate_summary_refs": _r52_candidate_summary_refs_from_r12(r12),
        "no_auto_allow_summary_refs": ["p5_candidate_is_not_p5_confirmed_final", "p6_candidate_is_not_p6_start_allowed", "p8_material_candidate_is_not_p8_start_allowed", "p7_complete_false", "release_allowed_false"],
        "decision_ref": decision_ref,
        "decision_status": decision_status,
        "decision_reason_refs": reasons,
        "next_required_step": next_step,
        "final_decision_composer_status": final_status,
        "public_contract": public_contract_flags(),
        "r52_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "r52_0_current_received_snapshot_refrozen": True,
        "r52_1_validation_evidence_matrix_frozen": True,
        "r52_2_r51_bodyfree_handoff_intake_contract_built": True,
        "r52_3_forbidden_payload_deep_scan_built": r12.get("r52_3_forbidden_payload_deep_scan_built") is True,
        "r52_4_actual_review_evidence_completeness_checker_built": r12.get("r52_4_actual_review_evidence_completeness_checker_built") is True,
        "r52_5_evidence_missing_no_go_branch_built": r12.get("r52_5_evidence_missing_no_go_branch_built") is True,
        "r52_6_disposal_safety_gate_built": r12.get("r52_6_disposal_safety_gate_built") is True,
        "r52_7_execution_blocker_gate_built": r12.get("r52_7_execution_blocker_gate_built") is True,
        "r52_8_rating_question_consistency_gate_built": r12.get("r52_8_rating_question_consistency_gate_built") is True,
        "r52_9_p5_readfeel_blocker_gate_built": r12.get("r52_9_p5_readfeel_blocker_gate_built") is True,
        "r52_10_p5_confirmed_candidate_decision_built": r12.get("r52_10_p5_confirmed_candidate_decision_built") is True,
        "r52_11_p6_limited_human_readfeel_candidate_separation_built": r12.get("r52_11_p6_limited_human_readfeel_candidate_separation_built") is True,
        "r52_12_p8_question_material_candidate_separation_built": r12.get("r52_12_p8_question_material_candidate_separation_built") is True,
        "r52_13_final_decision_composer_built": True,
        "implemented_steps": list(P7_R52_R13_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R52_R13_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R52_FIRST_NEXT_WORK_REF,
        **_r52_false_flags_r13(),
    }
    assert_p7_r52_final_decision_composer_contract(gate)
    return gate


def assert_p7_r52_final_decision_composer_contract(gate: Mapping[str, Any]) -> bool:
    data = safe_mapping(gate)
    forbidden_paths = _r52_find_forbidden_key_paths(data, forbidden_keys=P7_R52_FORBIDDEN_PAYLOAD_KEY_REFS, path="p7_r52_r13_final_decision_composer")
    if forbidden_paths:
        raise ValueError(f"R52 R13 must remain body-free and question-text-free: {forbidden_paths[:6]}")
    missing = [field for field in P7_R52_R13_REQUIRED_FIELD_REFS if field not in data]
    if missing:
        raise ValueError(f"p7_r52_r13_final_decision_composer missing required fields: {missing[:6]}")
    if set(data) != set(P7_R52_R13_REQUIRED_FIELD_REFS):
        raise ValueError("R52 R13 must not contain body payload, question text, path, hash, or extra fields")
    _assert_body_free_common(data, schema_version=P7_R52_FINAL_DECISION_COMPOSER_SCHEMA_VERSION, source="p7_r52_r13_final_decision_composer")
    if data.get("policy_section") != P7_R52_R13_STEP_REF:
        raise ValueError("R52 R13 policy section changed")
    for false_key in P7_R52_R13_FALSE_KEY_REFS:
        if data.get(false_key) is not False:
            raise ValueError(f"R52 R13 must keep {false_key}=False")
    if data.get("decision_ref") not in P7_R52_R13_DECISION_REF_REFS or data.get("decision_status") not in P7_R52_R5_DECISION_STATUS_REFS:
        raise ValueError("R52 R13 decision changed")
    if data.get("final_decision_composer_status") not in P7_R52_R13_COMPOSER_STATUS_REFS:
        raise ValueError("R52 R13 composer status changed")
    if data.get("p5_human_blind_qa_confirmed") is not False or data.get("p5_human_blind_qa_confirmed_final") is not False:
        raise ValueError("R52 R13 must not finalize P5")
    if data.get("p6_limited_human_readfeel_start_allowed") is not False:
        raise ValueError("R52 R13 must not start P6")
    if data.get("p8_start_allowed") is not False or data.get("p7_complete") is not False or data.get("release_allowed") is not False:
        raise ValueError("R52 R13 must not start P8, complete P7, or release")
    if tuple(data.get("implemented_steps") or ()) != P7_R52_R13_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R52_R13_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R52 R13 implemented/not-yet steps changed")
    if data.get("r52_13_final_decision_composer_built") is not True:
        raise ValueError("R52 R13 final decision composer must be built when called")
    return True


def build_p7_r52_r0_r12_p8_question_material_candidate_separation_chain(
    *,
    current_received_snapshot_refreeze: Mapping[str, Any] | None = None,
    validation_evidence_matrix_freeze: Mapping[str, Any] | None = None,
    r51_bodyfree_handoff_materials: Sequence[Mapping[str, Any]] | None = None,
    r51_actual_review_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    r11 = build_p7_r52_r0_r11_p6_limited_human_readfeel_candidate_separation_chain(current_received_snapshot_refreeze=current_received_snapshot_refreeze, validation_evidence_matrix_freeze=validation_evidence_matrix_freeze, r51_bodyfree_handoff_materials=r51_bodyfree_handoff_materials, r51_actual_review_evidence=r51_actual_review_evidence)
    assert_p7_r52_p6_limited_human_readfeel_candidate_separation_contract(r11)
    r12 = build_p7_r52_p8_question_material_candidate_separation(p6_limited_human_readfeel_candidate_separation=r11, r51_actual_review_evidence=r51_actual_review_evidence, r51_bodyfree_handoff_materials=r51_bodyfree_handoff_materials)
    assert_p7_r52_p8_question_material_candidate_separation_contract(r12)
    return r12


def build_p7_r52_r0_r13_final_decision_composer_chain(
    *,
    current_received_snapshot_refreeze: Mapping[str, Any] | None = None,
    validation_evidence_matrix_freeze: Mapping[str, Any] | None = None,
    r51_bodyfree_handoff_materials: Sequence[Mapping[str, Any]] | None = None,
    r51_actual_review_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    r12 = build_p7_r52_r0_r12_p8_question_material_candidate_separation_chain(current_received_snapshot_refreeze=current_received_snapshot_refreeze, validation_evidence_matrix_freeze=validation_evidence_matrix_freeze, r51_bodyfree_handoff_materials=r51_bodyfree_handoff_materials, r51_actual_review_evidence=r51_actual_review_evidence)
    assert_p7_r52_p8_question_material_candidate_separation_contract(r12)
    r13 = build_p7_r52_final_decision_composer(p8_question_material_candidate_separation=r12)
    assert_p7_r52_final_decision_composer_contract(r13)
    return r13



# ---------------------------------------------------------------------------
# R52-14 / R52-15: no-touch boundary validation + documentation output.
# ---------------------------------------------------------------------------

P7_R52_NO_TOUCH_BOUNDARY_VALIDATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r52.no_touch_boundary_validation.bodyfree.v1"
)
P7_R52_DOCUMENTATION_OUTPUT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r52.documentation_output.bodyfree.v1"
)

P7_R52_R14_STEP_REF: Final = "R52-14_no_touch_boundary_validation"
P7_R52_R15_STEP_REF: Final = "R52-15_documentation_output"
P7_R52_R14_NEXT_REQUIRED_STEP_REF: Final = P7_R52_R15_STEP_REF
P7_R52_R14_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "resolve_R52-14_no_touch_boundary_before_documentation_output"
)
P7_R52_R15_RETURN_TO_R51_NEXT_REQUIRED_STEP_REF: Final = (
    "R51_actual_local_only_human_review_required_with_explicit_allow_local_root_purge_plan"
)
P7_R52_R15_HUMAN_DECISION_NEXT_REQUIRED_STEP_REF: Final = (
    "separate_manual_decision_required_before_P6_or_P8_start_allowed"
)

P7_R52_R14_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R52_R13_IMPLEMENTED_STEPS,
    P7_R52_R14_STEP_REF,
)
P7_R52_R14_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R52_R15_STEP_REF,)
P7_R52_R15_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R52_R14_IMPLEMENTED_STEPS,
    P7_R52_R15_STEP_REF,
)
P7_R52_R15_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = ()
P7_R52_CURRENT_IMPLEMENTED_STEPS = P7_R52_R15_IMPLEMENTED_STEPS
P7_R52_CURRENT_NOT_YET_IMPLEMENTED_STEPS = P7_R52_R15_NOT_YET_IMPLEMENTED_STEPS

P7_R52_PRODUCTION_HELPER_CANDIDATE_FILE_REF: Final = (
    "services/ai_inference/emlis_ai_p7_r52_r51_handoff_p6_p8_start_decision_gate.py"
)
P7_R52_ALLOWED_R52_TEST_FILE_REF_PREFIX: Final = (
    "tests/test_emlis_ai_p7_r52_r51_handoff_p6_p8_start_decision_gate_"
)
P7_R52_DEFAULT_CHANGED_FILE_REFS: Final[tuple[str, ...]] = (
    P7_R52_PRODUCTION_HELPER_CANDIDATE_FILE_REF,
    "tests/test_emlis_ai_p7_r52_r51_handoff_p6_p8_start_decision_gate_r12_r13_20260621.py",
    "tests/test_emlis_ai_p7_r52_r51_handoff_p6_p8_start_decision_gate_r14_r15_20260621.py",
)
P7_R52_NO_TOUCH_TARGET_FILE_REFS: Final[tuple[str, ...]] = (
    "Cocolon/screens/InputScreen.js",
    "Cocolon/screens/input/useInputFeedbackModal.js",
    "Cocolon/screens/input/inputFeedbackModel.js",
    "Cocolon/screens/input/InputFeedbackReplyModal.js",
    "Cocolon/tests/rn-screen-contracts.test.js",
    "tests/rn-screen-contracts.test.js",
    "services/ai_inference/api_emotion_submit.py",
    "services/ai_inference/emotion_submit_service.py",
    "services/ai_inference/emlis_ai_reply_service.py",
    "services/ai_inference/emlis_ai_public_feedback_meta.py",
    "services/ai_inference/emlis_ai_user_label_connection_material.py",
    "services/ai_inference/emlis_ai_user_label_connection_candidate.py",
    "services/ai_inference/emlis_ai_user_label_connection_gate.py",
    "services/ai_inference/emlis_ai_user_label_connection_surface.py",
    "alembic/versions/*",
    "migrations/*",
    "models/*",
    "schemas/*",
)
P7_R52_DOCUMENTATION_MATERIAL_REFS: Final[tuple[str, ...]] = (
    "Cocolon_EmlisAI_P7_R52_R51HandoffEvidenceDecisionGate_DetailedDesign_ImplementationOrder_20260621.md",
    "Cocolon_EmlisAI_P7_R52_R51Handoff_P6P8StartDecision_PreDesignMemo_20260621.md",
    "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619.md",
)
P7_R52_DOCUMENTATION_OUTPUT_KIND_REFS: Final[tuple[str, ...]] = (
    "r52_detailed_design",
    "implementation_order",
    "schema_proposal_only",
    "validation_matrix",
    "acceptance_criteria",
    "no_touch_boundary",
)
P7_R52_R14_STATUS_REFS: Final[tuple[str, ...]] = (
    "R52_NO_TOUCH_BOUNDARY_VALIDATED",
    "R52_NO_TOUCH_BOUNDARY_BLOCKED_BY_R13_NOT_READY",
    "R52_NO_TOUCH_BOUNDARY_BLOCKED_BY_PROHIBITED_CHANGED_FILE_REF",
)
P7_R52_R15_DOCUMENTATION_STATUS_REFS: Final[tuple[str, ...]] = (
    "R52_DOCUMENTATION_OUTPUT_RECORDED_WITH_NO_AUTO_ALLOW",
    "R52_DOCUMENTATION_OUTPUT_BLOCKED_BY_NO_TOUCH_BOUNDARY",
)
P7_R52_R14_DECISION_REF_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys((*P7_R52_R13_DECISION_REF_REFS, "R52_BLOCKED_BY_NO_TOUCH_BOUNDARY_RISK"))
)
P7_R52_R15_DECISION_REF_REFS: Final[tuple[str, ...]] = P7_R52_R14_DECISION_REF_REFS

P7_R52_R14_EXTRA_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    "rn_production_files_changed_here",
    "rn_contract_tests_changed_here",
    "api_route_changed_here",
    "db_schema_changed_here",
    "db_migration_changed_here",
    "public_response_top_level_key_added_here",
    "emlis_runtime_changed_here",
    "user_label_connection_runtime_changed_here",
    "p8_question_implementation_changed_here",
    "schema_files_materialized_here",
    "body_full_review_packet_generated_here",
    "r52_no_touch_validation_changed_contract_here",
    "r52_15_documentation_output_built",
)
P7_R52_R14_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys((*P7_R52_R13_FALSE_KEY_REFS, *P7_R52_R14_EXTRA_FALSE_KEY_REFS))
)
P7_R52_R15_EXTRA_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    "documentation_file_created_here",
    "documentation_file_modified_here",
    "json_schema_files_materialized_here",
    "schema_files_materialized_here",
    "body_full_packet_materialized_here",
    "review_packet_materialized_here",
    "question_text_documented_here",
    "question_trigger_logic_documented_as_final_here",
    "p8_api_db_rn_response_key_documented_as_final_here",
)
P7_R52_R15_FALSE_KEY_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        (
            *(key for key in P7_R52_R14_FALSE_KEY_REFS if key != "r52_15_documentation_output_built"),
            *P7_R52_R15_EXTRA_FALSE_KEY_REFS,
        )
    )
)

P7_R52_R14_BASE_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "required_case_count",
    "r13_final_decision_schema_version",
    "r13_final_decision_material_ref",
    "r13_decision_ref",
    "r13_decision_status",
    "r13_final_decision_composer_status",
    "r13_next_required_step",
    "r13_ready_for_r52_14_no_touch_boundary_validation",
    "changed_file_refs",
    "changed_file_ref_count",
    "allowed_changed_file_refs",
    "allowed_changed_file_ref_count",
    "prohibited_changed_file_refs",
    "prohibited_changed_file_ref_count",
    "production_helper_candidate_file_ref",
    "production_helper_candidate_only_changed",
    "r52_test_file_changes_only_outside_helper",
    "no_touch_target_file_refs",
    "rn_production_files_no_touch",
    "rn_contract_tests_no_touch",
    "api_route_no_touch",
    "db_schema_no_touch",
    "db_migration_no_touch",
    "public_response_top_level_key_no_touch",
    "emlis_runtime_no_touch",
    "user_label_connection_runtime_no_touch",
    "runtime_no_touch",
    "p8_question_implementation_no_touch",
    "no_touch_boundary_passed",
    "no_touch_validation_status",
    "no_touch_reason_refs",
    "r51_actual_review_evidence_complete",
    "p5_decision_status",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_human_blind_qa_confirmed",
    "p5_human_blind_qa_confirmed_final",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "p8_question_design_material_candidate",
    "p8_start_allowed",
    "p7_complete",
    "release_allowed",
    "decision_ref",
    "decision_status",
    "decision_reason_refs",
    "next_required_step",
    "public_contract",
    "r52_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    "r52_0_current_received_snapshot_refrozen",
    "r52_1_validation_evidence_matrix_frozen",
    "r52_2_r51_bodyfree_handoff_intake_contract_built",
    "r52_3_forbidden_payload_deep_scan_built",
    "r52_4_actual_review_evidence_completeness_checker_built",
    "r52_5_evidence_missing_no_go_branch_built",
    "r52_6_disposal_safety_gate_built",
    "r52_7_execution_blocker_gate_built",
    "r52_8_rating_question_consistency_gate_built",
    "r52_9_p5_readfeel_blocker_gate_built",
    "r52_10_p5_confirmed_candidate_decision_built",
    "r52_11_p6_limited_human_readfeel_candidate_separation_built",
    "r52_12_p8_question_material_candidate_separation_built",
    "r52_13_final_decision_composer_built",
    "r52_14_no_touch_boundary_validation_built",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
)
P7_R52_R14_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys((*P7_R52_R14_BASE_FIELD_REFS, *P7_R52_R14_FALSE_KEY_REFS))
)
P7_R52_R15_BASE_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "required_case_count",
    "r14_no_touch_schema_version",
    "r14_no_touch_material_ref",
    "r14_decision_ref",
    "r14_decision_status",
    "r14_no_touch_validation_status",
    "r14_no_touch_boundary_passed",
    "documentation_material_refs",
    "documentation_material_ref_count",
    "documentation_output_kind_refs",
    "documentation_output_kind_count",
    "documentation_acceptance_criteria_recorded",
    "validation_matrix_recorded",
    "schema_proposal_recorded",
    "implementation_order_recorded",
    "markdown_documentation_output_present",
    "documentation_is_existing_design_md",
    "documentation_file_materialized_here",
    "json_schema_files_materialized_here",
    "schema_files_materialized_here",
    "r51_actual_review_evidence_complete",
    "p5_decision_status",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_human_blind_qa_confirmed",
    "p5_human_blind_qa_confirmed_final",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "p8_question_design_material_candidate",
    "p8_start_allowed",
    "p7_complete",
    "release_allowed",
    "decision_ref",
    "decision_status",
    "decision_reason_refs",
    "next_required_step",
    "documentation_output_status",
    "public_contract",
    "r52_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    "r52_0_current_received_snapshot_refrozen",
    "r52_1_validation_evidence_matrix_frozen",
    "r52_2_r51_bodyfree_handoff_intake_contract_built",
    "r52_3_forbidden_payload_deep_scan_built",
    "r52_4_actual_review_evidence_completeness_checker_built",
    "r52_5_evidence_missing_no_go_branch_built",
    "r52_6_disposal_safety_gate_built",
    "r52_7_execution_blocker_gate_built",
    "r52_8_rating_question_consistency_gate_built",
    "r52_9_p5_readfeel_blocker_gate_built",
    "r52_10_p5_confirmed_candidate_decision_built",
    "r52_11_p6_limited_human_readfeel_candidate_separation_built",
    "r52_12_p8_question_material_candidate_separation_built",
    "r52_13_final_decision_composer_built",
    "r52_14_no_touch_boundary_validation_built",
    "r52_15_documentation_output_built",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
)
P7_R52_R15_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys((*P7_R52_R15_BASE_FIELD_REFS, *P7_R52_R15_FALSE_KEY_REFS))
)
P7_R52_NO_TOUCH_BOUNDARY_VALIDATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = P7_R52_R14_REQUIRED_FIELD_REFS
P7_R52_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = P7_R52_R15_REQUIRED_FIELD_REFS


def _r52_false_flags_r14() -> dict[str, bool]:
    return {key: False for key in P7_R52_R14_FALSE_KEY_REFS}


def _r52_false_flags_r15() -> dict[str, bool]:
    return {key: False for key in P7_R52_R15_FALSE_KEY_REFS}


def _r52_normalized_file_ref(value: Any) -> str:
    text = clean_identifier(value, default="", max_length=280).replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    for prefix in ("mashos-api/ai/", "mashos-api/", "ai/"):
        if text.startswith(prefix):
            text = text[len(prefix):]
    return text


def _r52_changed_file_refs(changed_file_refs: Sequence[Any] | Any | None) -> list[str]:
    refs = changed_file_refs if changed_file_refs is not None else P7_R52_DEFAULT_CHANGED_FILE_REFS
    if isinstance(refs, (str, bytes, bytearray)):
        raw_refs = [refs]
    elif isinstance(refs, Mapping):
        raw_refs = list(refs.values())
    elif isinstance(refs, Iterable):
        raw_refs = list(refs)
    else:
        raw_refs = [refs]
    return dedupe_identifiers([_r52_normalized_file_ref(ref) for ref in raw_refs], limit=80, max_length=260)


def _r52_allowed_changed_file_refs(changed_refs: Sequence[str]) -> list[str]:
    return [
        ref
        for ref in changed_refs
        if ref == P7_R52_PRODUCTION_HELPER_CANDIDATE_FILE_REF
        or ref.startswith(P7_R52_ALLOWED_R52_TEST_FILE_REF_PREFIX)
    ]


def _r52_prohibited_changed_file_refs(changed_refs: Sequence[str]) -> list[str]:
    allowed = set(_r52_allowed_changed_file_refs(changed_refs))
    return [ref for ref in changed_refs if ref not in allowed]


def _r52_changed_ref_has_prefix_or_exact(changed_refs: Sequence[str], refs: Sequence[str]) -> bool:
    for changed_ref in changed_refs:
        for target_ref in refs:
            target = _r52_normalized_file_ref(target_ref)
            if target.endswith("/*"):
                if changed_ref.startswith(target[:-1]):
                    return True
            elif changed_ref == target or changed_ref.endswith("/" + target):
                return True
    return False


def _r52_no_touch_flags(changed_refs: Sequence[str]) -> dict[str, bool]:
    rn_production_targets = (
        "Cocolon/screens/InputScreen.js",
        "Cocolon/screens/input/useInputFeedbackModal.js",
        "Cocolon/screens/input/inputFeedbackModel.js",
        "Cocolon/screens/input/InputFeedbackReplyModal.js",
        "screens/InputScreen.js",
        "screens/input/useInputFeedbackModal.js",
        "screens/input/inputFeedbackModel.js",
        "screens/input/InputFeedbackReplyModal.js",
    )
    api_targets = (
        "services/ai_inference/api_emotion_submit.py",
        "services/ai_inference/api_contract_registry.py",
    )
    runtime_targets = (
        "services/ai_inference/emotion_submit_service.py",
        "services/ai_inference/emlis_ai_reply_service.py",
    )
    public_contract_targets = (
        "services/ai_inference/api_emotion_submit.py",
        "services/ai_inference/api_contract_registry.py",
        "services/ai_inference/emlis_ai_public_feedback_meta.py",
    )
    user_label_targets = tuple(ref for ref in P7_R52_NO_TOUCH_TARGET_FILE_REFS if "emlis_ai_user_label_connection_" in ref)
    p8_question_targets = (
        "services/ai_inference/emlis_ai_p8_observation_question.py",
        "services/ai_inference/emlis_ai_observation_clarification_question.py",
        "services/ai_inference/emlis_ai_question_trigger.py",
    )
    return {
        "rn_production_files_no_touch": not _r52_changed_ref_has_prefix_or_exact(changed_refs, rn_production_targets),
        "rn_contract_tests_no_touch": not _r52_changed_ref_has_prefix_or_exact(changed_refs, ("Cocolon/tests/rn-screen-contracts.test.js", "tests/rn-screen-contracts.test.js")),
        "api_route_no_touch": not _r52_changed_ref_has_prefix_or_exact(changed_refs, api_targets),
        "db_schema_no_touch": not _r52_changed_ref_has_prefix_or_exact(changed_refs, ("alembic/versions/*", "migrations/*", "models/*", "schemas/*")),
        "db_migration_no_touch": not _r52_changed_ref_has_prefix_or_exact(changed_refs, ("alembic/versions/*", "migrations/*")),
        "public_response_top_level_key_no_touch": not _r52_changed_ref_has_prefix_or_exact(changed_refs, public_contract_targets),
        "emlis_runtime_no_touch": not _r52_changed_ref_has_prefix_or_exact(changed_refs, runtime_targets),
        "user_label_connection_runtime_no_touch": not _r52_changed_ref_has_prefix_or_exact(changed_refs, user_label_targets),
        "p8_question_implementation_no_touch": not _r52_changed_ref_has_prefix_or_exact(changed_refs, p8_question_targets),
    }


def _r52_r13_ready_for_no_touch_validation(r13: Mapping[str, Any]) -> bool:
    return r13.get("r52_13_final_decision_composer_built") is True and r13.get("body_free") is True


def _r52_no_touch_reason_refs(
    *,
    r13_ready: bool,
    prohibited_refs: Sequence[str],
    production_helper_candidate_only_changed: bool,
    r52_test_file_changes_only_outside_helper: bool,
    no_touch_flags: Mapping[str, bool],
) -> list[str]:
    reasons: list[str] = []
    if not r13_ready:
        reasons.append("r13_final_decision_composer_not_ready_for_no_touch_validation")
    if prohibited_refs:
        reasons.append("prohibited_changed_file_refs_present")
    if not production_helper_candidate_only_changed:
        reasons.append("production_change_outside_r52_helper_detected")
    if not r52_test_file_changes_only_outside_helper:
        reasons.append("test_change_outside_r52_test_scope_detected")
    for key, value in no_touch_flags.items():
        if value is not True:
            reasons.append(f"{key}_failed")
    if not reasons:
        reasons.extend(
            [
                "r52_helper_change_only_for_production",
                "r52_tests_only_outside_helper",
                "rn_api_db_runtime_public_contract_no_touch",
                "p8_question_implementation_no_touch",
            ]
        )
    return dedupe_identifiers(reasons, limit=80, max_length=220)


def build_p7_r52_no_touch_boundary_validation(
    *,
    final_decision_composer: Mapping[str, Any] | None = None,
    current_received_snapshot_refreeze: Mapping[str, Any] | None = None,
    validation_evidence_matrix_freeze: Mapping[str, Any] | None = None,
    r51_bodyfree_handoff_materials: Sequence[Mapping[str, Any]] | None = None,
    r51_actual_review_evidence: Mapping[str, Any] | None = None,
    changed_file_refs: Sequence[Any] | Any | None = None,
    material_id: str = "p7_r52_no_touch_boundary_validation",
) -> dict[str, Any]:
    """Build R52-14, fixing the no-touch boundary before documentation output."""
    r13 = safe_mapping(final_decision_composer) if final_decision_composer is not None else build_p7_r52_r0_r13_final_decision_composer_chain(
        current_received_snapshot_refreeze=current_received_snapshot_refreeze,
        validation_evidence_matrix_freeze=validation_evidence_matrix_freeze,
        r51_bodyfree_handoff_materials=r51_bodyfree_handoff_materials,
        r51_actual_review_evidence=r51_actual_review_evidence,
    )
    assert_p7_r52_final_decision_composer_contract(r13)
    changed_refs = _r52_changed_file_refs(changed_file_refs)
    allowed_refs = _r52_allowed_changed_file_refs(changed_refs)
    prohibited_refs = _r52_prohibited_changed_file_refs(changed_refs)
    no_touch_flags = _r52_no_touch_flags(changed_refs)
    no_touch_flags["runtime_no_touch"] = (
        no_touch_flags["emlis_runtime_no_touch"] and no_touch_flags["user_label_connection_runtime_no_touch"]
    )
    production_refs = [ref for ref in changed_refs if not ref.startswith("tests/")]
    production_helper_candidate_only_changed = all(ref == P7_R52_PRODUCTION_HELPER_CANDIDATE_FILE_REF for ref in production_refs)
    r52_test_file_changes_only_outside_helper = all(
        ref == P7_R52_PRODUCTION_HELPER_CANDIDATE_FILE_REF
        or ref.startswith(P7_R52_ALLOWED_R52_TEST_FILE_REF_PREFIX)
        for ref in changed_refs
    )
    r13_ready = _r52_r13_ready_for_no_touch_validation(r13)
    no_touch_passed = (
        r13_ready
        and not prohibited_refs
        and production_helper_candidate_only_changed
        and r52_test_file_changes_only_outside_helper
        and all(no_touch_flags.values())
    )
    if not r13_ready:
        status = "R52_NO_TOUCH_BOUNDARY_BLOCKED_BY_R13_NOT_READY"
        decision_ref = "R52_BLOCKED_BY_NO_TOUCH_BOUNDARY_RISK"
        decision_status = "BLOCKED"
        next_step = P7_R52_R14_BLOCKED_NEXT_REQUIRED_STEP_REF
    elif not no_touch_passed:
        status = "R52_NO_TOUCH_BOUNDARY_BLOCKED_BY_PROHIBITED_CHANGED_FILE_REF"
        decision_ref = "R52_BLOCKED_BY_NO_TOUCH_BOUNDARY_RISK"
        decision_status = "BLOCKED"
        next_step = P7_R52_R14_BLOCKED_NEXT_REQUIRED_STEP_REF
    else:
        status = "R52_NO_TOUCH_BOUNDARY_VALIDATED"
        decision_ref = clean_identifier(r13.get("decision_ref"), default="R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED", max_length=180)
        decision_status = clean_identifier(r13.get("decision_status"), default="RETURN_REQUIRED", max_length=80)
        next_step = P7_R52_R14_NEXT_REQUIRED_STEP_REF
    reasons = _r52_no_touch_reason_refs(
        r13_ready=r13_ready,
        prohibited_refs=prohibited_refs,
        production_helper_candidate_only_changed=production_helper_candidate_only_changed,
        r52_test_file_changes_only_outside_helper=r52_test_file_changes_only_outside_helper,
        no_touch_flags=no_touch_flags,
    )
    if no_touch_passed:
        reasons = dedupe_identifiers([*(r13.get("decision_reason_refs") or []), *reasons], limit=160, max_length=220)
    gate = {
        "schema_version": P7_R52_NO_TOUCH_BOUNDARY_VALIDATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R52_STEP,
        "scope": P7_R52_SCOPE,
        "policy_kind": P7_R52_POLICY_KIND,
        "policy_section": P7_R52_R14_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r52_no_touch_boundary_validation", max_length=180),
        "review_session_id": clean_identifier(r13.get("review_session_id"), default=P7_R52_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "r13_final_decision_schema_version": P7_R52_FINAL_DECISION_COMPOSER_SCHEMA_VERSION,
        "r13_final_decision_material_ref": clean_identifier(r13.get("material_id"), default="p7_r52_final_decision_composer", max_length=180),
        "r13_decision_ref": clean_identifier(r13.get("decision_ref"), default="R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED", max_length=180),
        "r13_decision_status": clean_identifier(r13.get("decision_status"), default="RETURN_REQUIRED", max_length=80),
        "r13_final_decision_composer_status": clean_identifier(r13.get("final_decision_composer_status"), default="R52_FINAL_DECISION_COMPOSED", max_length=180),
        "r13_next_required_step": clean_identifier(r13.get("next_required_step"), default=P7_R52_R13_NEXT_REQUIRED_STEP_REF, max_length=240),
        "r13_ready_for_r52_14_no_touch_boundary_validation": r13_ready,
        "changed_file_refs": changed_refs,
        "changed_file_ref_count": len(changed_refs),
        "allowed_changed_file_refs": allowed_refs,
        "allowed_changed_file_ref_count": len(allowed_refs),
        "prohibited_changed_file_refs": prohibited_refs,
        "prohibited_changed_file_ref_count": len(prohibited_refs),
        "production_helper_candidate_file_ref": P7_R52_PRODUCTION_HELPER_CANDIDATE_FILE_REF,
        "production_helper_candidate_only_changed": production_helper_candidate_only_changed,
        "r52_test_file_changes_only_outside_helper": r52_test_file_changes_only_outside_helper,
        "no_touch_target_file_refs": list(P7_R52_NO_TOUCH_TARGET_FILE_REFS),
        **no_touch_flags,
        "no_touch_boundary_passed": no_touch_passed,
        "no_touch_validation_status": status,
        "no_touch_reason_refs": reasons,
        "r51_actual_review_evidence_complete": r13.get("r51_actual_review_evidence_complete") is True,
        "p5_decision_status": clean_identifier(r13.get("p5_decision_status"), default="R52_P5_NOT_REVIEWED_EVIDENCE_MISSING", max_length=180),
        "p5_human_blind_qa_confirmed_candidate": r13.get("p5_human_blind_qa_confirmed_candidate") is True,
        "p5_human_blind_qa_confirmed": False,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_start_allowed_candidate": r13.get("p6_limited_human_readfeel_start_allowed_candidate") is True,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_question_design_material_candidate": r13.get("p8_question_design_material_candidate") is True,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "decision_ref": decision_ref,
        "decision_status": decision_status,
        "decision_reason_refs": reasons,
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "r52_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "r52_0_current_received_snapshot_refrozen": True,
        "r52_1_validation_evidence_matrix_frozen": True,
        "r52_2_r51_bodyfree_handoff_intake_contract_built": True,
        "r52_3_forbidden_payload_deep_scan_built": r13.get("r52_3_forbidden_payload_deep_scan_built") is True,
        "r52_4_actual_review_evidence_completeness_checker_built": r13.get("r52_4_actual_review_evidence_completeness_checker_built") is True,
        "r52_5_evidence_missing_no_go_branch_built": r13.get("r52_5_evidence_missing_no_go_branch_built") is True,
        "r52_6_disposal_safety_gate_built": r13.get("r52_6_disposal_safety_gate_built") is True,
        "r52_7_execution_blocker_gate_built": r13.get("r52_7_execution_blocker_gate_built") is True,
        "r52_8_rating_question_consistency_gate_built": r13.get("r52_8_rating_question_consistency_gate_built") is True,
        "r52_9_p5_readfeel_blocker_gate_built": r13.get("r52_9_p5_readfeel_blocker_gate_built") is True,
        "r52_10_p5_confirmed_candidate_decision_built": r13.get("r52_10_p5_confirmed_candidate_decision_built") is True,
        "r52_11_p6_limited_human_readfeel_candidate_separation_built": r13.get("r52_11_p6_limited_human_readfeel_candidate_separation_built") is True,
        "r52_12_p8_question_material_candidate_separation_built": r13.get("r52_12_p8_question_material_candidate_separation_built") is True,
        "r52_13_final_decision_composer_built": r13.get("r52_13_final_decision_composer_built") is True,
        "r52_14_no_touch_boundary_validation_built": True,
        "implemented_steps": list(P7_R52_R14_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R52_R14_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R52_FIRST_NEXT_WORK_REF,
        **_r52_false_flags_r14(),
    }
    assert_p7_r52_no_touch_boundary_validation_contract(gate)
    return gate


def assert_p7_r52_no_touch_boundary_validation_contract(gate: Mapping[str, Any]) -> bool:
    data = safe_mapping(gate)
    forbidden_paths = _r52_find_forbidden_key_paths(
        data,
        forbidden_keys=P7_R52_FORBIDDEN_PAYLOAD_KEY_REFS,
        path="p7_r52_r14_no_touch_boundary_validation",
    )
    if forbidden_paths:
        raise ValueError(f"R52 R14 must remain body-free: {forbidden_paths[:6]}")
    _assert_required_fields(data, required=P7_R52_R14_REQUIRED_FIELD_REFS, source="p7_r52_r14_no_touch_boundary_validation")
    _assert_body_free_common(
        data,
        schema_version=P7_R52_NO_TOUCH_BOUNDARY_VALIDATION_SCHEMA_VERSION,
        source="p7_r52_r14_no_touch_boundary_validation",
    )
    if data.get("policy_section") != P7_R52_R14_STEP_REF:
        raise ValueError("R52 R14 policy section changed")
    for false_key in P7_R52_R14_FALSE_KEY_REFS:
        if data.get(false_key) is not False:
            raise ValueError(f"R52 R14 must keep {false_key}=False")
    if data.get("no_touch_validation_status") not in P7_R52_R14_STATUS_REFS:
        raise ValueError("R52 R14 no-touch validation status changed")
    if data.get("decision_ref") not in P7_R52_R14_DECISION_REF_REFS or data.get("decision_status") not in P7_R52_R5_DECISION_STATUS_REFS:
        raise ValueError("R52 R14 decision changed")
    if data.get("p6_limited_human_readfeel_start_allowed") is not False or data.get("p8_start_allowed") is not False:
        raise ValueError("R52 R14 must not start P6/P8")
    if data.get("p7_complete") is not False or data.get("release_allowed") is not False:
        raise ValueError("R52 R14 must not complete P7 or release")
    if data.get("p5_human_blind_qa_confirmed") is not False or data.get("p5_human_blind_qa_confirmed_final") is not False:
        raise ValueError("R52 R14 must not finalize P5")
    if data.get("no_touch_boundary_passed") is True:
        if data.get("prohibited_changed_file_ref_count") != 0:
            raise ValueError("R52 R14 passed with prohibited changed file refs")
        for key in (
            "rn_production_files_no_touch",
            "rn_contract_tests_no_touch",
            "api_route_no_touch",
            "db_schema_no_touch",
            "db_migration_no_touch",
            "public_response_top_level_key_no_touch",
            "emlis_runtime_no_touch",
            "user_label_connection_runtime_no_touch",
            "runtime_no_touch",
            "p8_question_implementation_no_touch",
        ):
            if data.get(key) is not True:
                raise ValueError(f"R52 R14 passed while {key} was not true")
        if tuple(data.get("implemented_steps") or ()) != P7_R52_R14_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R52_R14_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R52 R14 implemented/not-yet steps changed")
    else:
        if data.get("decision_ref") != "R52_BLOCKED_BY_NO_TOUCH_BOUNDARY_RISK" or data.get("decision_status") != "BLOCKED":
            raise ValueError("R52 R14 blocked no-touch must use no-touch blocked decision")
    return True


def _r52_r15_next_required_step_from_r14(r14: Mapping[str, Any]) -> str:
    decision_ref = clean_identifier(r14.get("decision_ref"), default="R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED", max_length=180)
    if r14.get("no_touch_boundary_passed") is not True:
        return P7_R52_R14_BLOCKED_NEXT_REQUIRED_STEP_REF
    if decision_ref in {"R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED", "R52_BLOCKED_BY_R51_EVIDENCE_MISSING"}:
        return P7_R52_R15_RETURN_TO_R51_NEXT_REQUIRED_STEP_REF
    return P7_R52_R15_HUMAN_DECISION_NEXT_REQUIRED_STEP_REF


def build_p7_r52_documentation_output(
    *,
    no_touch_boundary_validation: Mapping[str, Any] | None = None,
    final_decision_composer: Mapping[str, Any] | None = None,
    current_received_snapshot_refreeze: Mapping[str, Any] | None = None,
    validation_evidence_matrix_freeze: Mapping[str, Any] | None = None,
    r51_bodyfree_handoff_materials: Sequence[Mapping[str, Any]] | None = None,
    r51_actual_review_evidence: Mapping[str, Any] | None = None,
    changed_file_refs: Sequence[Any] | Any | None = None,
    material_id: str = "p7_r52_documentation_output",
) -> dict[str, Any]:
    """Build R52-15, a body-free documentation output summary without writing files."""
    r14 = safe_mapping(no_touch_boundary_validation) if no_touch_boundary_validation is not None else build_p7_r52_no_touch_boundary_validation(
        final_decision_composer=final_decision_composer,
        current_received_snapshot_refreeze=current_received_snapshot_refreeze,
        validation_evidence_matrix_freeze=validation_evidence_matrix_freeze,
        r51_bodyfree_handoff_materials=r51_bodyfree_handoff_materials,
        r51_actual_review_evidence=r51_actual_review_evidence,
        changed_file_refs=changed_file_refs,
    )
    assert_p7_r52_no_touch_boundary_validation_contract(r14)
    no_touch_passed = r14.get("no_touch_boundary_passed") is True
    documentation_status = (
        "R52_DOCUMENTATION_OUTPUT_RECORDED_WITH_NO_AUTO_ALLOW"
        if no_touch_passed
        else "R52_DOCUMENTATION_OUTPUT_BLOCKED_BY_NO_TOUCH_BOUNDARY"
    )
    decision_ref = clean_identifier(
        r14.get("decision_ref"),
        default="R52_BLOCKED_BY_NO_TOUCH_BOUNDARY_RISK" if not no_touch_passed else "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED",
        max_length=180,
    )
    decision_status = clean_identifier(r14.get("decision_status"), default="BLOCKED" if not no_touch_passed else "RETURN_REQUIRED", max_length=80)
    reasons = dedupe_identifiers(
        [
            *(r14.get("decision_reason_refs") or []),
            "r52_documentation_output_recorded_body_free",
            "json_schema_files_not_materialized_here",
            "no_p6_p8_start_allowed",
            "no_api_db_rn_runtime_change",
        ],
        limit=180,
        max_length=220,
    )
    gate = {
        "schema_version": P7_R52_DOCUMENTATION_OUTPUT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R52_STEP,
        "scope": P7_R52_SCOPE,
        "policy_kind": P7_R52_POLICY_KIND,
        "policy_section": P7_R52_R15_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r52_documentation_output", max_length=180),
        "review_session_id": clean_identifier(r14.get("review_session_id"), default=P7_R52_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "r14_no_touch_schema_version": P7_R52_NO_TOUCH_BOUNDARY_VALIDATION_SCHEMA_VERSION,
        "r14_no_touch_material_ref": clean_identifier(r14.get("material_id"), default="p7_r52_no_touch_boundary_validation", max_length=180),
        "r14_decision_ref": clean_identifier(r14.get("decision_ref"), default="R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED", max_length=180),
        "r14_decision_status": clean_identifier(r14.get("decision_status"), default="RETURN_REQUIRED", max_length=80),
        "r14_no_touch_validation_status": clean_identifier(r14.get("no_touch_validation_status"), default="R52_NO_TOUCH_BOUNDARY_VALIDATED", max_length=180),
        "r14_no_touch_boundary_passed": no_touch_passed,
        "documentation_material_refs": list(P7_R52_DOCUMENTATION_MATERIAL_REFS),
        "documentation_material_ref_count": len(P7_R52_DOCUMENTATION_MATERIAL_REFS),
        "documentation_output_kind_refs": list(P7_R52_DOCUMENTATION_OUTPUT_KIND_REFS),
        "documentation_output_kind_count": len(P7_R52_DOCUMENTATION_OUTPUT_KIND_REFS),
        "documentation_acceptance_criteria_recorded": True,
        "validation_matrix_recorded": True,
        "schema_proposal_recorded": True,
        "implementation_order_recorded": True,
        "markdown_documentation_output_present": True,
        "documentation_is_existing_design_md": True,
        "documentation_file_materialized_here": False,
        "json_schema_files_materialized_here": False,
        "schema_files_materialized_here": False,
        "r51_actual_review_evidence_complete": r14.get("r51_actual_review_evidence_complete") is True,
        "p5_decision_status": clean_identifier(r14.get("p5_decision_status"), default="R52_P5_NOT_REVIEWED_EVIDENCE_MISSING", max_length=180),
        "p5_human_blind_qa_confirmed_candidate": r14.get("p5_human_blind_qa_confirmed_candidate") is True,
        "p5_human_blind_qa_confirmed": False,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_start_allowed_candidate": r14.get("p6_limited_human_readfeel_start_allowed_candidate") is True,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_question_design_material_candidate": r14.get("p8_question_design_material_candidate") is True,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "decision_ref": decision_ref,
        "decision_status": decision_status,
        "decision_reason_refs": reasons,
        "next_required_step": _r52_r15_next_required_step_from_r14(r14),
        "documentation_output_status": documentation_status,
        "public_contract": public_contract_flags(),
        "r52_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "r52_0_current_received_snapshot_refrozen": True,
        "r52_1_validation_evidence_matrix_frozen": True,
        "r52_2_r51_bodyfree_handoff_intake_contract_built": True,
        "r52_3_forbidden_payload_deep_scan_built": r14.get("r52_3_forbidden_payload_deep_scan_built") is True,
        "r52_4_actual_review_evidence_completeness_checker_built": r14.get("r52_4_actual_review_evidence_completeness_checker_built") is True,
        "r52_5_evidence_missing_no_go_branch_built": r14.get("r52_5_evidence_missing_no_go_branch_built") is True,
        "r52_6_disposal_safety_gate_built": r14.get("r52_6_disposal_safety_gate_built") is True,
        "r52_7_execution_blocker_gate_built": r14.get("r52_7_execution_blocker_gate_built") is True,
        "r52_8_rating_question_consistency_gate_built": r14.get("r52_8_rating_question_consistency_gate_built") is True,
        "r52_9_p5_readfeel_blocker_gate_built": r14.get("r52_9_p5_readfeel_blocker_gate_built") is True,
        "r52_10_p5_confirmed_candidate_decision_built": r14.get("r52_10_p5_confirmed_candidate_decision_built") is True,
        "r52_11_p6_limited_human_readfeel_candidate_separation_built": r14.get("r52_11_p6_limited_human_readfeel_candidate_separation_built") is True,
        "r52_12_p8_question_material_candidate_separation_built": r14.get("r52_12_p8_question_material_candidate_separation_built") is True,
        "r52_13_final_decision_composer_built": r14.get("r52_13_final_decision_composer_built") is True,
        "r52_14_no_touch_boundary_validation_built": r14.get("r52_14_no_touch_boundary_validation_built") is True,
        "r52_15_documentation_output_built": True,
        "implemented_steps": list(P7_R52_R15_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R52_R15_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R52_FIRST_NEXT_WORK_REF,
        **_r52_false_flags_r15(),
    }
    assert_p7_r52_documentation_output_contract(gate)
    return gate


def assert_p7_r52_documentation_output_contract(gate: Mapping[str, Any]) -> bool:
    data = safe_mapping(gate)
    forbidden_paths = _r52_find_forbidden_key_paths(
        data,
        forbidden_keys=P7_R52_FORBIDDEN_PAYLOAD_KEY_REFS,
        path="p7_r52_r15_documentation_output",
    )
    if forbidden_paths:
        raise ValueError(f"R52 R15 must remain body-free: {forbidden_paths[:6]}")
    _assert_required_fields(data, required=P7_R52_R15_REQUIRED_FIELD_REFS, source="p7_r52_r15_documentation_output")
    _assert_body_free_common(
        data,
        schema_version=P7_R52_DOCUMENTATION_OUTPUT_SCHEMA_VERSION,
        source="p7_r52_r15_documentation_output",
    )
    if data.get("policy_section") != P7_R52_R15_STEP_REF:
        raise ValueError("R52 R15 policy section changed")
    for false_key in P7_R52_R15_FALSE_KEY_REFS:
        if data.get(false_key) is not False:
            raise ValueError(f"R52 R15 must keep {false_key}=False")
    if data.get("documentation_output_status") not in P7_R52_R15_DOCUMENTATION_STATUS_REFS:
        raise ValueError("R52 R15 documentation output status changed")
    if data.get("decision_ref") not in P7_R52_R15_DECISION_REF_REFS or data.get("decision_status") not in P7_R52_R5_DECISION_STATUS_REFS:
        raise ValueError("R52 R15 decision changed")
    if data.get("p6_limited_human_readfeel_start_allowed") is not False or data.get("p8_start_allowed") is not False:
        raise ValueError("R52 R15 must not start P6/P8")
    if data.get("p7_complete") is not False or data.get("release_allowed") is not False:
        raise ValueError("R52 R15 must not complete P7 or release")
    if data.get("p5_human_blind_qa_confirmed") is not False or data.get("p5_human_blind_qa_confirmed_final") is not False:
        raise ValueError("R52 R15 must not finalize P5")
    if data.get("documentation_file_materialized_here") is not False or data.get("json_schema_files_materialized_here") is not False or data.get("schema_files_materialized_here") is not False:
        raise ValueError("R52 R15 must not materialize documentation/schema files from helper")
    if data.get("r52_15_documentation_output_built") is not True:
        raise ValueError("R52 R15 documentation output must be built when called")
    if tuple(data.get("implemented_steps") or ()) != P7_R52_R15_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R52_R15_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R52 R15 implemented/not-yet steps changed")
    return True


def build_p7_r52_r0_r14_no_touch_boundary_validation_chain(
    *,
    current_received_snapshot_refreeze: Mapping[str, Any] | None = None,
    validation_evidence_matrix_freeze: Mapping[str, Any] | None = None,
    r51_bodyfree_handoff_materials: Sequence[Mapping[str, Any]] | None = None,
    r51_actual_review_evidence: Mapping[str, Any] | None = None,
    changed_file_refs: Sequence[Any] | Any | None = None,
) -> dict[str, Any]:
    r13 = build_p7_r52_r0_r13_final_decision_composer_chain(
        current_received_snapshot_refreeze=current_received_snapshot_refreeze,
        validation_evidence_matrix_freeze=validation_evidence_matrix_freeze,
        r51_bodyfree_handoff_materials=r51_bodyfree_handoff_materials,
        r51_actual_review_evidence=r51_actual_review_evidence,
    )
    assert_p7_r52_final_decision_composer_contract(r13)
    r14 = build_p7_r52_no_touch_boundary_validation(final_decision_composer=r13, changed_file_refs=changed_file_refs)
    assert_p7_r52_no_touch_boundary_validation_contract(r14)
    return r14


def build_p7_r52_r0_r15_documentation_output_chain(
    *,
    current_received_snapshot_refreeze: Mapping[str, Any] | None = None,
    validation_evidence_matrix_freeze: Mapping[str, Any] | None = None,
    r51_bodyfree_handoff_materials: Sequence[Mapping[str, Any]] | None = None,
    r51_actual_review_evidence: Mapping[str, Any] | None = None,
    changed_file_refs: Sequence[Any] | Any | None = None,
) -> dict[str, Any]:
    r14 = build_p7_r52_r0_r14_no_touch_boundary_validation_chain(
        current_received_snapshot_refreeze=current_received_snapshot_refreeze,
        validation_evidence_matrix_freeze=validation_evidence_matrix_freeze,
        r51_bodyfree_handoff_materials=r51_bodyfree_handoff_materials,
        r51_actual_review_evidence=r51_actual_review_evidence,
        changed_file_refs=changed_file_refs,
    )
    assert_p7_r52_no_touch_boundary_validation_contract(r14)
    r15 = build_p7_r52_documentation_output(no_touch_boundary_validation=r14)
    assert_p7_r52_documentation_output_contract(r15)
    return r15
