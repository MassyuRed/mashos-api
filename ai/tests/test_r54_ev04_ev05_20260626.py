# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as r54op
import emlis_ai_p7_r54_actual_review_execution_evidence_materialization_20260626 as ev
from emlis_ai_p7_r55_r54_evidence_reconcile_r52_reintake_decision_materialization import (
    P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
)


FORBIDDEN_DUMP_TOKENS = (
    '"raw_input":',
    '"raw_answer":',
    '"comment_text":',
    '"comment_text_body":',
    '"returned_emlis_surface":',
    '"current_input_review_surface":',
    '"bounded_owned_history_review_surface":',
    '"reviewer_free_text":',
    '"reviewer_note":',
    '"reviewer_notes":',
    '"question_text": "',
    '"draft_question_text": "',
    '"question_body":',
    '"local_absolute_path":',
    '"body_content_hash":',
    '"packet_content_hash":',
    '"terminal_output": "',
    '"stdout":',
    '"stderr":',
    '"traceback":',
)
FORBIDDEN_TRUE_TOKENS = (
    '"api_changed": true',
    '"db_changed": true',
    '"rn_changed": true',
    '"runtime_changed": true',
    '"api_route_changed": true',
    '"db_schema_changed": true',
    '"rn_visible_contract_changed": true',
    '"public_response_top_level_key_added": true',
    '"release_allowed": true',
    '"p7_complete": true',
    '"p8_start_allowed": true',
    '"p6_limited_human_readfeel_start_allowed": true',
    '"question_trigger_logic_implemented": true',
    '"p8_question_implementation_spec_finalized_here": true',
    '"actual_human_review_run_here": true',
    '"actual_manual_review_run_here": true',
    '"body_full_packet_generated_here": true',
    '"body_full_generation_requested_here": true',
    '"actual_rating_rows_materialized_here": true',
    '"actual_question_need_observation_rows_materialized_here": true',
    '"actual_disposal_receipt_materialized_here": true',
    '"disposal_verified": true',
    '"existing_op04_reused_as_actual_preflight_basis": true',
    '"existing_op05_reused_as_actual_manifest_basis": true',
    '"historical_helper_refs_used_as_actual_review_basis": true',
    '"old_helper_refs_allowed_as_actual_review_basis": true',
    '"r55_current_refs_used_as_actual_review_basis": true',
    '"actual_review_evidence_complete": true',
)


def _assert_body_free_no_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_DUMP_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_TRUE_TOKENS:
        assert forbidden not in dumped


@lru_cache(maxsize=1)
def _cached_ev03() -> tuple[dict[str, object]]:
    ev00 = ev.build_p7_r54_ev00_scope_no_touch_boundary_confirmation()
    ev01 = ev.build_p7_r54_ev01_existing_helper_capability_inspection(
        scope_no_touch_boundary_confirmation=ev00,
    )
    ev02 = ev.build_p7_r54_ev02_operation_current_refs_20260626_refreeze(
        existing_helper_capability_inspection=ev01,
    )
    material = ev.build_p7_r54_ev03_r55_hold_intake_refreeze(
        operation_current_refs_refreeze=ev02,
    )
    assert ev.assert_p7_r54_ev03_r55_hold_intake_refreeze_contract(material) is True
    return (material,)


def _ev03() -> dict[str, object]:
    return deepcopy(_cached_ev03()[0])


@lru_cache(maxsize=1)
def _cached_ev04_blocked() -> tuple[dict[str, object]]:
    material = ev.build_p7_r54_ev04_local_only_preflight_implementation_confirmation(
        r55_hold_intake_refreeze=_ev03(),
    )
    assert ev.assert_p7_r54_ev04_local_only_preflight_implementation_confirmation_contract(material) is True
    return (material,)


def _ev04_blocked() -> dict[str, object]:
    return deepcopy(_cached_ev04_blocked()[0])


@lru_cache(maxsize=1)
def _cached_ev04_ready() -> tuple[dict[str, object]]:
    material = ev.build_p7_r54_ev04_local_only_preflight_implementation_confirmation(
        r55_hold_intake_refreeze=_ev03(),
        local_review_root_presence_ref=ev.P7_R54_EV04_LOCAL_REVIEW_ROOT_READY_REF,
        explicit_allow_token_ref=ev.P7_R54_EV04_EXPLICIT_ALLOW_TOKEN_REF,
        purge_plan_ref=ev.P7_R54_EV04_PURGE_PLAN_READY_REF,
        retention_policy_ref=ev.P7_R54_EV04_RETENTION_POLICY_READY_REF,
        export_denylist_policy_ref=ev.P7_R54_EV04_EXPORT_DENYLIST_POLICY_READY_REF,
    )
    assert ev.assert_p7_r54_ev04_local_only_preflight_implementation_confirmation_contract(material) is True
    return (material,)


def _ev04_ready() -> dict[str, object]:
    return deepcopy(_cached_ev04_ready()[0])


@lru_cache(maxsize=1)
def _cached_ev05_blocked() -> tuple[dict[str, object]]:
    material = ev.build_p7_r54_ev05_24_case_manifest_refreeze(
        local_only_preflight_implementation_confirmation=_ev04_blocked(),
    )
    assert ev.assert_p7_r54_ev05_24_case_manifest_refreeze_contract(material) is True
    return (material,)


def _ev05_blocked() -> dict[str, object]:
    return deepcopy(_cached_ev05_blocked()[0])


@lru_cache(maxsize=1)
def _cached_ev05_ready() -> tuple[dict[str, object]]:
    material = ev.build_p7_r54_ev05_24_case_manifest_refreeze(
        local_only_preflight_implementation_confirmation=_ev04_ready(),
    )
    assert ev.assert_p7_r54_ev05_24_case_manifest_refreeze_contract(material) is True
    return (material,)


def _ev05_ready() -> dict[str, object]:
    return deepcopy(_cached_ev05_ready()[0])


def test_r54_ev04_default_blocks_without_local_only_preflight_refs_or_allow_token() -> None:
    material = _ev04_blocked()

    assert material["schema_version"] == ev.P7_R54_EV_LOCAL_ONLY_PREFLIGHT_IMPLEMENTATION_CONFIRMATION_SCHEMA_VERSION
    assert set(material) == set(ev.P7_R54_EV_LOCAL_ONLY_PREFLIGHT_IMPLEMENTATION_CONFIRMATION_REQUIRED_FIELD_REFS)
    assert material["phase"].startswith("P7_")
    assert material["policy_section"] == ev.P7_R54_EV04_STEP_REF
    assert material["operation_step_ref"] == ev.P7_R54_EV04_STEP_REF
    assert material["source_mode"] == "local_snapshot"
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True

    assert material["ev03_schema_version"] == ev.P7_R54_EV_R55_HOLD_INTAKE_REFREEZE_SCHEMA_VERSION
    assert material["ev03_next_required_step"] == ev.P7_R54_EV04_STEP_REF
    assert material["operation_current_refs"] == ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["operation_current_refs"]["backend_zip_ref"] == "mashos-api(167).zip"
    assert material["operation_current_refs_used_as_actual_review_basis"] is True

    assert material["existing_op04_operation_current_refs"] == r54op.P7_R54_OPERATION_CURRENT_REFS
    assert material["existing_op04_operation_current_refs"]["backend_zip_ref"] == "mashos-api(166).zip"
    assert material["existing_op04_current_refs_are_historical_here"] is True
    assert material["existing_op04_allow_token_is_historical_here"] is True
    assert material["existing_op04_reused_as_actual_preflight_basis"] is False
    assert material["existing_op04_structural_contract_reused"] is True

    assert material["preflight_status"] == ev.P7_R54_EV04_PREFLIGHT_BLOCKED_STATUS_REF
    assert material["local_review_root_declared"] is False
    assert material["explicit_allow_present"] is False
    assert material["explicit_allow_token_matches_20260626"] is False
    assert material["purge_plan_ready"] is False
    assert material["retention_policy_present"] is False
    assert material["export_denylist_present"] is False
    assert material["body_full_packet_generation_allowed_before_preflight"] is False
    assert material["body_full_packet_generation_allowed_by_preflight"] is False
    assert material["body_full_packet_generation_request_allowed_next"] is False
    assert material["body_full_generation_requested_here"] is False
    assert material["local_path_included"] is False
    assert material["local_review_root_path_included"] is False
    assert material["local_review_root_path_materialized_here"] is False
    assert set(material["execution_blocker_ids"]) >= {
        "review_packet_generation_blocked_missing_local_root",
        "review_packet_generation_blocked_missing_explicit_allow",
        "review_packet_generation_blocked_missing_purge_plan",
        "review_packet_generation_blocked_missing_retention_policy",
        "review_packet_generation_blocked_missing_export_denylist",
    }
    assert material["open_execution_blocker_ids"] == material["execution_blocker_ids"]
    assert material["required_case_count"] == P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT == 24
    assert material["rating_row_count"] == 0
    assert material["question_observation_row_count"] == 0
    assert material["actual_review_evidence_complete"] is False
    assert material["r55_hold_preserved"] is True
    assert material["p6_hold"] is True
    assert material["p8_hold"] is True
    assert material["release_hold"] is True
    assert tuple(material["implemented_steps"]) == ev.P7_R54_EV04_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ev.P7_R54_EV04_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ev.P7_R54_EV04_BLOCKED_NEXT_REQUIRED_STEP_REF
    for key in ev.P7_R54_EV_FALSE_FLAG_REFS:
        assert material[key] is False
    _assert_body_free_no_promotion(material)


def test_r54_ev04_ready_confirms_20260626_local_only_preflight_without_paths_or_packets() -> None:
    material = _ev04_ready()

    assert material["preflight_status"] == ev.P7_R54_EV04_PREFLIGHT_READY_STATUS_REF
    assert material["preflight_reason_refs"] == [ev.P7_R54_EV04_PREFLIGHT_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["open_execution_blocker_ids"] == []
    assert material["local_review_root_presence_ref"] == ev.P7_R54_EV04_LOCAL_REVIEW_ROOT_READY_REF
    assert material["local_review_root_declared"] is True
    assert material["local_review_root_outside_repo_export_scope"] is True
    assert material["local_review_root_env_var"] == r54op.P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR
    assert material["local_review_root_path_included"] is False
    assert material["local_review_root_path_materialized_here"] is False
    assert material["explicit_allow_token_ref"] == ev.P7_R54_EV04_EXPLICIT_ALLOW_TOKEN_REF
    assert material["explicit_allow_present"] is True
    assert material["explicit_allow_token_matches_20260626"] is True
    assert material["existing_op04_explicit_allow_token_ref"] == r54op.P7_R54_OP04_EXPLICIT_ALLOW_TOKEN_REF
    assert material["existing_op04_explicit_allow_token_ref"] != ev.P7_R54_EV04_EXPLICIT_ALLOW_TOKEN_REF
    assert material["purge_plan_ref"] == ev.P7_R54_EV04_PURGE_PLAN_READY_REF
    assert material["purge_plan_present"] is True
    assert material["purge_plan_ready"] is True
    assert tuple(material["purge_plan_required_delete_target_refs"]) == ev.P7_R54_EV04_REQUIRED_DELETE_TARGET_REFS
    assert material["retention_policy_ref"] == ev.P7_R54_EV04_RETENTION_POLICY_READY_REF
    assert material["retention_policy_present"] is True
    assert material["body_full_packet_retention_max_hours"] == r54op.P7_R47_BODY_FULL_PACKET_RETENTION_HOURS
    assert material["reviewer_notes_retention_after_rating_finalized_max_hours"] == r54op.P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS
    assert tuple(material["delete_trigger_refs"]) == r54op.P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS
    assert material["export_denylist_policy_ref"] == ev.P7_R54_EV04_EXPORT_DENYLIST_POLICY_READY_REF
    assert material["export_denylist_present"] is True
    assert tuple(material["export_denylist_patterns"]) == r54op.P7_R47_EXPORT_DENYLIST_PATTERNS
    assert material["export_denylist_violation_refs"] == []
    assert material["export_denylist_violation_count"] == 0
    assert material["body_full_packet_generation_allowed_before_preflight"] is False
    assert material["body_full_packet_generation_allowed_by_preflight"] is True
    assert material["body_full_packet_generation_request_allowed_next"] is True
    assert material["body_full_generation_blocked_until_manifest_freeze"] is True
    assert material["body_full_generation_requested_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_human_review_run_here"] is False
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["human_review_completion_claim_blocked_here"] is True
    assert material["actual_human_review_completion_claim_blocked_here"] is True
    assert material["p6_p8_release_promotion_blocked_here"] is True
    assert material["next_required_step"] == ev.P7_R54_EV05_STEP_REF
    _assert_body_free_no_promotion(material)


def test_r54_ev04_old_20260625_allow_token_remains_blocked_even_with_other_ready_refs() -> None:
    material = ev.build_p7_r54_ev04_local_only_preflight_implementation_confirmation(
        r55_hold_intake_refreeze=_ev03(),
        local_review_root_presence_ref=ev.P7_R54_EV04_LOCAL_REVIEW_ROOT_READY_REF,
        explicit_allow_token_ref=r54op.P7_R54_OP04_EXPLICIT_ALLOW_TOKEN_REF,
        purge_plan_ref=ev.P7_R54_EV04_PURGE_PLAN_READY_REF,
        retention_policy_ref=ev.P7_R54_EV04_RETENTION_POLICY_READY_REF,
        export_denylist_policy_ref=ev.P7_R54_EV04_EXPORT_DENYLIST_POLICY_READY_REF,
    )

    assert material["preflight_status"] == ev.P7_R54_EV04_PREFLIGHT_BLOCKED_STATUS_REF
    assert material["explicit_allow_present"] is False
    assert material["explicit_allow_token_matches_20260626"] is False
    assert "review_packet_generation_blocked_missing_explicit_allow" in material["execution_blocker_ids"]
    assert material["body_full_packet_generation_allowed_by_preflight"] is False
    assert material["next_required_step"] == ev.P7_R54_EV04_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_body_free_no_promotion(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("git_connection_required", True),
        ("git_checked", True),
        ("operation_current_refs_used_as_actual_review_basis", False),
        ("existing_op04_current_refs_are_historical_here", False),
        ("existing_op04_allow_token_is_historical_here", False),
        ("existing_op04_reused_as_actual_preflight_basis", True),
        ("existing_op04_structural_contract_reused", False),
        ("local_review_root_path_included", True),
        ("local_review_root_path_materialized_here", True),
        ("explicit_allow_token_body_stored_here", True),
        ("explicit_allow_token_matches_20260626", False),
        ("body_full_packet_generation_allowed_before_preflight", True),
        ("body_full_packet_generation_allowed_by_preflight", False),
        ("body_full_packet_generation_request_allowed_next", False),
        ("body_full_generation_requested_here", True),
        ("required_case_count", 23),
        ("rating_row_count", 1),
        ("question_observation_row_count", 1),
        ("actual_review_evidence_complete", True),
        ("r55_hold_preserved", False),
        ("p6_hold", False),
        ("p8_hold", False),
        ("release_hold", False),
        ("actual_human_review_completion_claim_blocked_here", False),
        ("p6_p8_release_promotion_blocked_here", False),
        ("api_changed", True),
        ("db_changed", True),
        ("rn_changed", True),
        ("runtime_changed", True),
        ("question_trigger_logic_implemented", True),
        ("actual_human_review_run_here", True),
        ("body_full_packet_generated_here", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("local_path_included", True),
    ],
)
def test_r54_ev04_rejects_ready_preflight_boundary_mutations(key: str, value: object) -> None:
    material = _ev04_ready()
    material[key] = value
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev04_local_only_preflight_implementation_confirmation_contract(material)


def test_r54_ev04_rejects_old_operation_refs_or_fake_ready_status() -> None:
    material = _ev04_ready()
    material["operation_current_refs"] = dict(r54op.P7_R54_OPERATION_CURRENT_REFS)
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev04_local_only_preflight_implementation_confirmation_contract(material)

    material = _ev04_blocked()
    material["preflight_status"] = ev.P7_R54_EV04_PREFLIGHT_READY_STATUS_REF
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev04_local_only_preflight_implementation_confirmation_contract(material)

    material = _ev04_ready()
    material["explicit_allow_token_ref"] = r54op.P7_R54_OP04_EXPLICIT_ALLOW_TOKEN_REF
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev04_local_only_preflight_implementation_confirmation_contract(material)


def test_r54_ev05_default_blocks_manifest_when_ev04_preflight_is_blocked() -> None:
    material = _ev05_blocked()

    assert material["schema_version"] == ev.P7_R54_EV_24_CASE_MANIFEST_REFREEZE_SCHEMA_VERSION
    assert set(material) == set(ev.P7_R54_EV_24_CASE_MANIFEST_REFREEZE_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == ev.P7_R54_EV05_STEP_REF
    assert material["operation_step_ref"] == ev.P7_R54_EV05_STEP_REF
    assert material["operation_current_refs"] == ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["operation_current_refs_used_as_actual_review_basis"] is True
    assert material["existing_op05_operation_current_refs"] == r54op.P7_R54_OPERATION_CURRENT_REFS
    assert material["existing_op05_current_refs_are_historical_here"] is True
    assert material["existing_op05_reused_as_actual_manifest_basis"] is False
    assert material["existing_op05_structural_contract_reused"] is True
    assert material["ev04_preflight_status"] == ev.P7_R54_EV04_PREFLIGHT_BLOCKED_STATUS_REF
    assert material["ev04_preflight_ready"] is False
    assert material["manifest_status"] == ev.P7_R54_EV05_MANIFEST_BLOCKED_STATUS_REF
    assert material["case_rows"] == []
    assert material["case_count"] == 0
    assert material["controller_manifest_rows"] == []
    assert material["reviewer_facing_case_index_rows"] == []
    assert material["controller_manifest_row_count"] == 0
    assert material["reviewer_facing_row_count"] == 0
    assert material["body_full_packet_generation_request_allowed_next"] is False
    assert material["body_full_generation_requested_here"] is False
    assert material["body_full_packet_zip_inclusion_allowed"] is False
    assert material["p5_actual_review_still_not_run"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["rating_row_count"] == 0
    assert material["question_observation_row_count"] == 0
    assert material["disposal_verified"] is False
    assert tuple(material["implemented_steps"]) == ev.P7_R54_EV04_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ev.P7_R54_EV04_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ev.P7_R54_EV05_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_body_free_no_promotion(material)


def test_r54_ev05_ready_refreezes_24_case_manifest_without_p4_r11_rows_or_body_full_packets() -> None:
    material = _ev05_ready()

    assert material["manifest_status"] == ev.P7_R54_EV05_MANIFEST_READY_STATUS_REF
    assert material["manifest_reason_refs"] == ["r54_ev05_24_case_manifest_refrozen_bodyfree_20260626"]
    assert material["execution_blocker_ids"] == []
    assert material["open_execution_blocker_ids"] == []
    assert material["ev04_preflight_status"] == ev.P7_R54_EV04_PREFLIGHT_READY_STATUS_REF
    assert material["ev04_preflight_ready"] is True
    assert material["ev04_next_required_step"] == ev.P7_R54_EV05_STEP_REF
    assert material["r48_case_matrix_schema_version"] == r54op.P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION
    assert material["r48_case_matrix_material_ref"] == "p7_r54_ev05_r48_first_formal_case_matrix_basis"
    assert material["required_case_count"] == P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT == 24
    assert material["case_distribution"] == ev.P7_R54_EV05_CASE_DISTRIBUTION
    assert material["case_distribution_total_count"] == 24
    assert material["case_distribution_matches_design"] is True
    assert material["case_count"] == 24
    assert len(material["case_rows"]) == 24
    assert material["family_case_counts"] == ev.P7_R54_EV05_CASE_DISTRIBUTION
    assert material["boundary_case_count"] == 4
    assert material["low_information_boundary_case_count"] == 2
    assert material["free_tier_boundary_case_count"] == 2
    assert material["case_ref_ids_unique"] is True
    assert material["blind_case_ids_unique"] is True
    assert material["packet_ref_ids_unique"] is True
    assert len(material["case_ref_ids"]) == 24
    assert len(material["blind_case_ids"]) == 24
    assert len(material["packet_ref_ids"]) == 24
    assert material["blind_case_id_case_ref_separated"] is True
    assert material["blind_case_id_packet_ref_separated"] is True
    assert material["case_ref_id_packet_ref_separated"] is True
    assert material["controller_manifest_row_count"] == 24
    assert material["reviewer_facing_row_count"] == 24
    assert len(material["controller_manifest_rows"]) == 24
    assert len(material["reviewer_facing_case_index_rows"]) == 24
    assert material["reviewer_identifier_policy_ref"] == ev.P7_R54_EV05_REVIEWER_IDENTIFIER_POLICY_REF
    assert material["controller_keeps_family_tier_expected_refs"] is True
    assert material["reviewer_receives_blind_case_id_only"] is True
    assert material["reviewer_facing_family_exposed"] is False
    assert material["reviewer_facing_tier_exposed"] is False
    assert material["reviewer_facing_case_ref_exposed"] is False
    assert material["reviewer_facing_packet_ref_exposed"] is False
    assert material["reviewer_facing_expected_result_exposed"] is False
    assert material["reviewer_facing_hidden_metadata_exposed"] is False
    assert material["p4_r11_rows_mixed_in"] is False
    assert material["p4_r11_rows_mixed_in_count"] == 0
    assert material["body_full_packet_generation_request_allowed_next"] is True
    assert material["body_full_generation_blocked_until_request_step"] is True
    assert material["body_full_generation_requested_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["body_full_packet_zip_inclusion_allowed"] is False
    assert material["p5_actual_review_still_not_run"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["actual_human_review_run_here"] is False
    assert material["rating_row_count"] == 0
    assert material["question_observation_row_count"] == 0
    assert material["disposal_verified"] is False
    assert material["human_review_completion_claim_blocked_here"] is True
    assert material["actual_human_review_completion_claim_blocked_here"] is True
    assert material["p6_p8_release_promotion_blocked_here"] is True
    assert tuple(material["implemented_steps"]) == ev.P7_R54_EV05_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ev.P7_R54_EV05_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ev.P7_R54_EV06_NEXT_REQUIRED_STEP_REF

    for row in material["case_rows"]:
        assert row["controller_only"] is True
        assert row["body_full_packet_materialized_here"] is False
        assert row["local_reviewer_payload_materialized_here"] is False
        assert row["body_free"] is True
    for row in material["controller_manifest_rows"]:
        assert row["controller_only"] is True
        assert row["reviewer_facing_family_exposed"] is False
        assert row["reviewer_facing_tier_exposed"] is False
        assert row["reviewer_facing_case_ref_exposed"] is False
        assert row["reviewer_facing_packet_ref_exposed"] is False
        assert row["body_free"] is True
    for row in material["reviewer_facing_case_index_rows"]:
        assert set(row) == {
            "reviewer_case_order",
            "blind_case_id",
            "reviewer_receives_blind_case_id_only",
            "family_exposed",
            "tier_exposed",
            "case_ref_exposed",
            "packet_ref_exposed",
            "expected_result_exposed",
            "hidden_metadata_exposed",
            "body_free",
        }
        assert row["reviewer_receives_blind_case_id_only"] is True
        assert row["family_exposed"] is False
        assert row["tier_exposed"] is False
        assert row["case_ref_exposed"] is False
        assert row["packet_ref_exposed"] is False
        assert row["hidden_metadata_exposed"] is False
        assert row["body_free"] is True
    for key in ev.P7_R54_EV_FALSE_FLAG_REFS:
        assert material[key] is False
    _assert_body_free_no_promotion(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("git_connection_required", True),
        ("git_checked", True),
        ("operation_current_refs_used_as_actual_review_basis", False),
        ("existing_op05_current_refs_are_historical_here", False),
        ("existing_op05_reused_as_actual_manifest_basis", True),
        ("existing_op05_structural_contract_reused", False),
        ("required_case_count", 23),
        ("case_distribution_total_count", 23),
        ("case_distribution_matches_design", False),
        ("manifest_status", ev.P7_R54_EV05_MANIFEST_BLOCKED_STATUS_REF),
        ("p4_r11_rows_mixed_in", True),
        ("p4_r11_rows_mixed_in_count", 1),
        ("body_full_packet_generation_request_allowed_next", False),
        ("body_full_generation_blocked_until_request_step", False),
        ("body_full_generation_requested_here", True),
        ("body_full_packet_zip_inclusion_allowed", True),
        ("p5_actual_review_still_not_run", False),
        ("actual_review_evidence_complete", True),
        ("rating_row_count", 1),
        ("question_observation_row_count", 1),
        ("human_review_completion_claim_blocked_here", False),
        ("actual_human_review_completion_claim_blocked_here", False),
        ("p6_p8_release_promotion_blocked_here", False),
        ("api_changed", True),
        ("db_changed", True),
        ("rn_changed", True),
        ("runtime_changed", True),
        ("question_trigger_logic_implemented", True),
        ("actual_human_review_run_here", True),
        ("body_full_packet_generated_here", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("local_path_included", True),
    ],
)
def test_r54_ev05_rejects_ready_manifest_boundary_mutations(key: str, value: object) -> None:
    material = _ev05_ready()
    material[key] = value
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev05_24_case_manifest_refreeze_contract(material)


def test_r54_ev05_rejects_tampered_rows_old_refs_or_body_leak_keys() -> None:
    material = _ev05_ready()
    material["operation_current_refs"] = dict(r54op.P7_R54_OPERATION_CURRENT_REFS)
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev05_24_case_manifest_refreeze_contract(material)

    material = _ev05_ready()
    material["case_rows"] = material["case_rows"][:-1]
    material["case_count"] = 23
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev05_24_case_manifest_refreeze_contract(material)

    material = _ev05_ready()
    material["case_rows"][0]["body_full_packet_materialized_here"] = True
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev05_24_case_manifest_refreeze_contract(material)

    material = _ev05_ready()
    material["controller_manifest_rows"][0]["reviewer_facing_family_exposed"] = True
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev05_24_case_manifest_refreeze_contract(material)

    material = _ev05_ready()
    material["reviewer_facing_case_index_rows"][0]["family_exposed"] = True
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev05_24_case_manifest_refreeze_contract(material)

    material = _ev05_ready()
    material["raw_input"] = "body must not be present"
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev05_24_case_manifest_refreeze_contract(material)

    material = _ev05_blocked()
    material["manifest_status"] = ev.P7_R54_EV05_MANIFEST_READY_STATUS_REF
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev05_24_case_manifest_refreeze_contract(material)
