# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as op
from emlis_ai_p7_r47_local_review_packet_policy import (
    P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS,
    P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
    P7_R47_EXPORT_DENYLIST_PATTERNS,
    P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR,
    P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
)
from emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet import (
    P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION,
    P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION,
)
from emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run import P7_R51_REQUIRED_CASE_COUNT


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
    '"question_text":',
    '"draft_question_text":',
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
    '"actual_rating_rows_materialized_here": true',
    '"actual_question_need_observation_rows_materialized_here": true',
    '"actual_disposal_receipt_materialized_here": true',
    '"p4_r11_rows_mixed_in": true',
)


def _assert_body_free_no_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_DUMP_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_TRUE_TOKENS:
        assert forbidden not in dumped


@lru_cache(maxsize=1)
def _cached_op03() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op03_r55_hold_intake()
    assert op.assert_p7_r54_op03_r55_hold_intake_contract(material) is True
    return (material,)


def _op03() -> dict[str, object]:
    return deepcopy(_cached_op03()[0])


@lru_cache(maxsize=1)
def _cached_op04_blocked() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op04_local_only_preflight(r55_hold_intake=_op03())
    assert op.assert_p7_r54_op04_local_only_preflight_contract(material) is True
    return (material,)


def _op04_blocked() -> dict[str, object]:
    return deepcopy(_cached_op04_blocked()[0])


@lru_cache(maxsize=1)
def _cached_op04_ready() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op04_local_only_preflight(
        r55_hold_intake=_op03(),
        local_review_root_presence_ref=op.P7_R54_OP04_LOCAL_REVIEW_ROOT_READY_REF,
        explicit_allow_token_ref=op.P7_R54_OP04_EXPLICIT_ALLOW_TOKEN_REF,
        purge_plan_ref=op.P7_R54_OP04_PURGE_PLAN_READY_REF,
        retention_policy_ref=op.P7_R54_OP04_RETENTION_POLICY_READY_REF,
        export_denylist_policy_ref=op.P7_R54_OP04_EXPORT_DENYLIST_POLICY_READY_REF,
    )
    assert op.assert_p7_r54_op04_local_only_preflight_contract(material) is True
    return (material,)


def _op04_ready() -> dict[str, object]:
    return deepcopy(_cached_op04_ready()[0])


@lru_cache(maxsize=1)
def _cached_op05_ready() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op05_24_case_manifest_freeze(local_only_preflight=_op04_ready())
    assert op.assert_p7_r54_op05_24_case_manifest_freeze_contract(material) is True
    return (material,)


def _op05_ready() -> dict[str, object]:
    return deepcopy(_cached_op05_ready()[0])


@lru_cache(maxsize=1)
def _cached_op05_blocked() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op05_24_case_manifest_freeze(local_only_preflight=_op04_blocked())
    assert op.assert_p7_r54_op05_24_case_manifest_freeze_contract(material) is True
    return (material,)


def _op05_blocked() -> dict[str, object]:
    return deepcopy(_cached_op05_blocked()[0])


def test_r54_op04_default_preflight_fails_closed_without_generating_body_full_packets() -> None:
    material = _op04_blocked()

    assert material["schema_version"] == op.P7_R54_OPERATION_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION
    assert set(material) == set(op.P7_R54_OPERATION_LOCAL_ONLY_PREFLIGHT_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == op.P7_R54_OP04_STEP_REF
    assert material["operation_step_ref"] == op.P7_R54_OP04_STEP_REF
    assert material["op03_schema_version"] == op.P7_R54_OPERATION_R55_HOLD_INTAKE_SCHEMA_VERSION
    assert material["op03_next_required_step"] == op.P7_R54_OP04_STEP_REF
    assert material["operation_current_refs"] == op.P7_R54_OPERATION_CURRENT_REFS
    assert material["r55_hold_intake_status_ref"] == op.P7_R54_R55_HOLD_INTAKE_STATUS_REF
    assert material["required_case_count"] == P7_R51_REQUIRED_CASE_COUNT
    assert material["rating_row_count"] == 0
    assert material["question_observation_row_count"] == 0
    assert material["disposal_verified"] is False
    assert material["p6_hold"] is True
    assert material["p8_hold"] is True
    assert material["release_hold"] is True
    assert material["actual_review_evidence_complete"] is False

    assert material["local_review_root_env_var"] == P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR
    assert material["local_review_root_declared"] is False
    assert material["local_review_root_outside_repo_export_scope"] is False
    assert material["local_review_root_path_included"] is False
    assert material["explicit_allow_present"] is False
    assert material["explicit_allow_token_body_stored_here"] is False
    assert material["purge_plan_present"] is False
    assert material["purge_plan_ready"] is False
    assert material["retention_policy_present"] is False
    assert material["export_denylist_present"] is False
    assert material["preflight_status"] == op.P7_R54_OP04_PREFLIGHT_BLOCKED_STATUS_REF
    assert material["body_full_packet_generation_allowed_before_preflight"] is False
    assert material["body_full_packet_generation_allowed_by_preflight"] is False
    assert material["body_full_packet_generation_request_allowed_next"] is False
    assert material["next_required_step"] == op.P7_R54_OP04_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert set(material["execution_blocker_ids"]) >= {
        "review_packet_generation_blocked_missing_local_root",
        "review_packet_generation_blocked_missing_explicit_allow",
        "review_packet_generation_blocked_missing_purge_plan",
        "review_packet_generation_blocked_missing_retention_policy",
        "review_packet_generation_blocked_missing_export_denylist",
    }
    assert material["actual_human_review_run_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["question_text_included"] is False
    assert material["draft_question_text_included"] is False
    assert material["local_path_included"] is False
    _assert_body_free_no_promotion(material)


def test_r54_op04_ready_preflight_is_bodyfree_and_allows_only_next_request_boundary() -> None:
    material = _op04_ready()

    assert material["preflight_status"] == op.P7_R54_OP04_PREFLIGHT_READY_STATUS_REF
    assert material["preflight_reason_refs"] == [op.P7_R54_OP04_PREFLIGHT_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["open_execution_blocker_ids"] == []
    assert material["local_review_root_presence_ref"] == op.P7_R54_OP04_LOCAL_REVIEW_ROOT_READY_REF
    assert material["local_review_root_declared"] is True
    assert material["local_review_root_outside_repo_export_scope"] is True
    assert material["local_review_root_path_included"] is False
    assert material["explicit_allow_token_ref"] == op.P7_R54_OP04_EXPLICIT_ALLOW_TOKEN_REF
    assert material["explicit_allow_present"] is True
    assert material["purge_plan_ref"] == op.P7_R54_OP04_PURGE_PLAN_READY_REF
    assert material["purge_plan_present"] is True
    assert material["purge_plan_ready"] is True
    assert tuple(material["purge_plan_required_delete_target_refs"]) == op.P7_R54_OP04_REQUIRED_DELETE_TARGET_REFS
    assert material["retention_policy_ref"] == op.P7_R54_OP04_RETENTION_POLICY_READY_REF
    assert material["retention_policy_present"] is True
    assert material["body_full_packet_retention_max_hours"] == P7_R47_BODY_FULL_PACKET_RETENTION_HOURS
    assert material["reviewer_notes_retention_after_rating_finalized_max_hours"] == P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS
    assert tuple(material["delete_trigger_refs"]) == P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS
    assert material["export_denylist_policy_ref"] == op.P7_R54_OP04_EXPORT_DENYLIST_POLICY_READY_REF
    assert material["export_denylist_present"] is True
    assert tuple(material["export_denylist_patterns"]) == P7_R47_EXPORT_DENYLIST_PATTERNS
    assert material["export_denylist_violation_refs"] == []
    assert material["export_denylist_violation_count"] == 0

    assert material["body_full_packet_generation_allowed_before_preflight"] is False
    assert material["body_full_packet_generation_allowed_by_preflight"] is True
    assert material["body_full_packet_generation_request_allowed_next"] is True
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_human_review_run_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert tuple(material["implemented_steps"]) == op.P7_R54_OP04_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == op.P7_R54_OP04_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == op.P7_R54_OP05_STEP_REF
    _assert_body_free_no_promotion(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("op03_next_required_step", "R54-OP-05_24_case_manifest_freeze"),
        ("r55_hold_intake_status_ref", "not_hold"),
        ("r55_actual_review_evidence_complete", True),
        ("required_case_count", 0),
        ("rating_row_count", 1),
        ("question_observation_row_count", 1),
        ("disposal_verified", True),
        ("p6_hold", False),
        ("p8_hold", False),
        ("release_hold", False),
        ("actual_review_evidence_complete", True),
        ("local_review_root_path_included", True),
        ("explicit_allow_token_body_stored_here", True),
        ("purge_plan_required_before_body_full_generation", False),
        ("body_full_packet_generation_allowed_before_preflight", True),
        ("body_full_generation_blocked_until_manifest_freeze", False),
        ("human_review_completion_claim_blocked_here", False),
        ("p6_p8_release_promotion_blocked_here", False),
        ("actual_human_review_run_here", True),
        ("body_full_packet_generated_here", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("local_path_included", True),
    ],
)
def test_r54_op04_rejects_preflight_review_claim_promotion_or_body_boundary_mutation(
    key: str,
    value: object,
) -> None:
    material = _op04_ready()
    material[key] = value
    with pytest.raises(ValueError):
        op.assert_p7_r54_op04_local_only_preflight_contract(material)


def test_r54_op04_rejects_ready_status_with_blocker_or_missing_policy() -> None:
    material = _op04_ready()
    material["execution_blocker_ids"] = ["review_packet_generation_blocked_missing_local_root"]
    material["open_execution_blocker_ids"] = ["review_packet_generation_blocked_missing_local_root"]
    with pytest.raises(ValueError):
        op.assert_p7_r54_op04_local_only_preflight_contract(material)

    material = _op04_ready()
    material["export_denylist_violation_refs"] = ["body_full_packets.local_only/"]
    material["export_denylist_violation_count"] = 1
    with pytest.raises(ValueError):
        op.assert_p7_r54_op04_local_only_preflight_contract(material)

    material = _op04_ready()
    material["next_required_step"] = op.P7_R54_OP04_BLOCKED_NEXT_REQUIRED_STEP_REF
    with pytest.raises(ValueError):
        op.assert_p7_r54_op04_local_only_preflight_contract(material)


def test_r54_op05_blocked_manifest_does_not_freeze_cases_before_preflight() -> None:
    material = _op05_blocked()

    assert material["schema_version"] == op.P7_R54_OPERATION_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION
    assert set(material) == set(op.P7_R54_OPERATION_24_CASE_MANIFEST_FREEZE_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == op.P7_R54_OP05_STEP_REF
    assert material["operation_step_ref"] == op.P7_R54_OP05_STEP_REF
    assert material["op04_preflight_status"] == op.P7_R54_OP04_PREFLIGHT_BLOCKED_STATUS_REF
    assert material["op04_preflight_ready"] is False
    assert material["manifest_status"] == op.P7_R54_OP05_MANIFEST_BLOCKED_STATUS_REF
    assert material["case_distribution"] == op.P7_R54_OP05_CASE_DISTRIBUTION
    assert material["case_distribution_total_count"] == P7_R51_REQUIRED_CASE_COUNT
    assert material["case_distribution_matches_design"] is False
    assert material["case_rows"] == []
    assert material["case_count"] == 0
    assert material["controller_manifest_rows"] == []
    assert material["reviewer_facing_case_index_rows"] == []
    assert material["controller_manifest_row_count"] == 0
    assert material["reviewer_facing_row_count"] == 0
    assert material["p4_r11_rows_mixed_in"] is False
    assert material["p4_r11_rows_mixed_in_count"] == 0
    assert material["body_full_packet_generation_request_allowed_next"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["p5_actual_review_still_not_run"] is True
    assert tuple(material["implemented_steps"]) == op.P7_R54_OP04_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == op.P7_R54_OP04_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == op.P7_R54_OP05_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_body_free_no_promotion(material)


def test_r54_op05_freezes_24_case_manifest_with_controller_and_reviewer_boundaries_separated() -> None:
    material = _op05_ready()

    assert material["schema_version"] == op.P7_R54_OPERATION_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION
    assert set(material) == set(op.P7_R54_OPERATION_24_CASE_MANIFEST_FREEZE_REQUIRED_FIELD_REFS)
    assert material["op04_schema_version"] == op.P7_R54_OPERATION_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION
    assert material["op04_next_required_step"] == op.P7_R54_OP05_STEP_REF
    assert material["op04_preflight_status"] == op.P7_R54_OP04_PREFLIGHT_READY_STATUS_REF
    assert material["op04_preflight_ready"] is True
    assert material["operation_current_refs"] == op.P7_R54_OPERATION_CURRENT_REFS
    assert material["operation_current_refs_are_actual_review_basis"] is True
    assert material["required_case_count"] == P7_R51_REQUIRED_CASE_COUNT
    assert material["r48_case_matrix_schema_version"] == P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION
    assert material["case_distribution"] == {family: count for family, count, _role in P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION}
    assert material["case_distribution_total_count"] == 24
    assert material["case_distribution_matches_design"] is True
    assert material["manifest_status"] == op.P7_R54_OP05_MANIFEST_READY_STATUS_REF
    assert material["manifest_reason_refs"] == ["r54_24_case_manifest_frozen_bodyfree"]
    assert material["execution_blocker_ids"] == []
    assert material["open_execution_blocker_ids"] == []
    assert material["case_count"] == 24
    assert material["family_case_counts"] == op.P7_R54_OP05_CASE_DISTRIBUTION
    assert material["case_role_counts"] == {"positive_history_line": 4, "positive_owned_history": 16, "boundary_no_history_line": 4}
    assert material["subscription_tier_ref_counts"] == {"plus": 11, "premium": 11, "free": 2}
    assert material["boundary_case_count"] == 4
    assert material["low_information_boundary_case_count"] == 2
    assert material["free_tier_boundary_case_count"] == 2
    assert material["case_ref_ids_unique"] is True
    assert material["blind_case_ids_unique"] is True
    assert material["packet_ref_ids_unique"] is True
    assert material["blind_case_id_case_ref_separated"] is True
    assert material["blind_case_id_packet_ref_separated"] is True
    assert material["case_ref_id_packet_ref_separated"] is True
    assert material["controller_manifest_row_count"] == 24
    assert material["reviewer_facing_row_count"] == 24
    assert material["reviewer_identifier_policy_ref"] == op.P7_R54_OP05_REVIEWER_IDENTIFIER_POLICY_REF
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
    assert material["body_full_packet_generated_here"] is False
    assert material["body_full_generation_blocked_until_request_step"] is True
    assert material["p5_actual_review_still_not_run"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["rating_row_count"] == 0
    assert material["question_observation_row_count"] == 0
    assert material["disposal_verified"] is False
    assert tuple(material["implemented_steps"]) == op.P7_R54_OP05_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == op.P7_R54_OP05_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == op.P7_R54_OP06_STEP_REF

    case_rows = material["case_rows"]
    controller_rows = material["controller_manifest_rows"]
    reviewer_rows = material["reviewer_facing_case_index_rows"]
    assert len(case_rows) == len(controller_rows) == len(reviewer_rows) == 24
    assert controller_rows[0]["case_ref_id"] == case_rows[0]["case_ref_id"]
    assert controller_rows[0]["family"] == case_rows[0]["family"]
    assert controller_rows[0]["subscription_tier_ref"] == case_rows[0]["subscription_tier_ref"]
    assert reviewer_rows[0] == {
        "reviewer_case_order": 1,
        "blind_case_id": case_rows[0]["blind_case_id"],
        "reviewer_receives_blind_case_id_only": True,
        "family_exposed": False,
        "tier_exposed": False,
        "case_ref_exposed": False,
        "packet_ref_exposed": False,
        "expected_result_exposed": False,
        "hidden_metadata_exposed": False,
        "body_free": True,
    }
    assert "case_ref_id" not in reviewer_rows[0]
    assert "packet_ref_id" not in reviewer_rows[0]
    assert "family" not in reviewer_rows[0]
    assert "subscription_tier_ref" not in reviewer_rows[0]
    _assert_body_free_no_promotion(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("op04_preflight_ready", False),
        ("case_distribution_matches_design", False),
        ("p4_r11_rows_mixed_in", True),
        ("p4_r11_rows_mixed_in_count", 1),
        ("reviewer_facing_family_exposed", True),
        ("reviewer_facing_tier_exposed", True),
        ("reviewer_facing_case_ref_exposed", True),
        ("reviewer_facing_packet_ref_exposed", True),
        ("reviewer_facing_expected_result_exposed", True),
        ("reviewer_facing_hidden_metadata_exposed", True),
        ("body_full_packet_generation_request_allowed_next", False),
        ("body_full_packet_generated_here", True),
        ("body_full_generation_blocked_until_request_step", False),
        ("p5_actual_review_still_not_run", False),
        ("actual_review_evidence_complete", True),
        ("rating_row_count", 1),
        ("question_observation_row_count", 1),
        ("disposal_verified", True),
        ("human_review_completion_claim_blocked_here", False),
        ("p6_p8_release_promotion_blocked_here", False),
        ("actual_human_review_run_here", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("local_path_included", True),
    ],
)
def test_r54_op05_rejects_manifest_review_claim_promotion_or_boundary_mutation(
    key: str,
    value: object,
) -> None:
    material = _op05_ready()
    material[key] = value
    with pytest.raises(ValueError):
        op.assert_p7_r54_op05_24_case_manifest_freeze_contract(material)


def test_r54_op05_rejects_case_distribution_row_removal_or_identifier_mixing() -> None:
    material = _op05_ready()
    material["case_rows"] = material["case_rows"][:23]
    material["case_count"] = 23
    with pytest.raises(ValueError):
        op.assert_p7_r54_op05_24_case_manifest_freeze_contract(material)

    material = _op05_ready()
    material["family_case_counts"]["history_line_eligible_input"] = 3
    with pytest.raises(ValueError):
        op.assert_p7_r54_op05_24_case_manifest_freeze_contract(material)

    material = _op05_ready()
    material["case_rows"][0]["blind_case_id"] = material["case_rows"][0]["case_ref_id"]
    with pytest.raises(ValueError):
        op.assert_p7_r54_op05_24_case_manifest_freeze_contract(material)

    material = _op05_ready()
    material["controller_manifest_rows"][0]["reviewer_facing_family_exposed"] = True
    with pytest.raises(ValueError):
        op.assert_p7_r54_op05_24_case_manifest_freeze_contract(material)

    material = _op05_ready()
    material["reviewer_facing_case_index_rows"][0]["case_ref_id"] = material["case_rows"][0]["case_ref_id"]
    with pytest.raises(ValueError):
        op.assert_p7_r54_op05_24_case_manifest_freeze_contract(material)
