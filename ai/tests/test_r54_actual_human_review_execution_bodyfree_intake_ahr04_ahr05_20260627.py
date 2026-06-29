# -*- coding: utf-8 -*-
"""Tests for R54-AHR04/AHR05 body-free evidence intake boundaries."""

from __future__ import annotations

from copy import deepcopy

import pytest

import emlis_ai_p7_r54_actual_human_review_execution_bodyfree_intake_20260627 as ahr
import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as r54op


FORBIDDEN_BODY_OR_QUESTION_REFS = (
    "raw_input_included",
    "raw_body_included",
    "returned_emlis_body_included",
    "history_surface_included",
    "reviewer_free_text_included",
    "reviewer_notes_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_absolute_path_included",
    "body_hash_included",
    "packet_content_included",
    "terminal_output_body_included",
)

NO_TOUCH_FALSE_REFS = (
    "api_changed",
    "db_changed",
    "rn_changed",
    "runtime_changed",
    "api_route_changed",
    "request_key_changed",
    "response_key_changed",
    "db_schema_changed",
    "db_migration_added",
    "rn_ui_changed",
    "public_response_key_changed",
    "question_implementation_started_here",
    "body_full_packet_generation_started_here",
    "body_full_packet_generation_requested_here",
    "body_full_packet_generated_here",
    "actual_human_review_run_here",
    "actual_human_review_executed_by_person",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "actual_r52_reintake_execution_confirmed",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_human_blind_qa_confirmed_final",
    "p6_start_allowed",
    "p8_start_allowed",
    "p7_complete",
    "release_allowed",
)


def _assert_bodyfree_no_touch(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    for key in FORBIDDEN_BODY_OR_QUESTION_REFS:
        assert material[key] is False
    for key in NO_TOUCH_FALSE_REFS:
        assert material[key] is False
    assert all(value is False for value in material["public_contract"].values())
    assert all(value is False for value in material["r54_ahr_no_touch_contract"].values())
    assert all(value is False for value in material["body_free_markers"].values())


def test_r54_ahr04_freezes_ready_local_only_preflight_without_generating_bodyfull() -> None:
    ahr03 = ahr.build_p7_r54_ahr03_r55_hold_evidence_missing_intake()
    material = ahr.build_p7_r54_ahr04_local_only_preflight(r55_hold_evidence_missing_intake=ahr03)

    assert set(material) == set(ahr.P7_R54_AHR_LOCAL_ONLY_PREFLIGHT_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == ahr.P7_R54_AHR_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION
    assert material["policy_section"] == ahr.P7_R54_AHR04_STEP_REF
    assert material["operation_step_ref"] == ahr.P7_R54_AHR04_STEP_REF
    assert material["ahr03_schema_version"] == ahr.P7_R54_AHR_R55_HOLD_EVIDENCE_MISSING_INTAKE_SCHEMA_VERSION
    assert material["ahr03_next_required_step"] == ahr.P7_R54_AHR04_STEP_REF
    assert material["ahr03_r55_gap_status_ref"] == ahr.P7_R54_AHR_R55_GAP_STATUS_REF
    assert material["ahr03_actual_review_evidence_missing_confirmed"] is True
    assert material["ahr03_r52_reintake_status_before_run"] == ahr.P7_R54_AHR_R52_REINTAKE_STATUS_BEFORE_RUN_REF
    assert material["current_execution_basis_refs"] == ahr.P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS
    assert material["current_execution_basis_refs_are_actual_execution_basis"] is True
    assert material["operation_current_refs_used_as_actual_execution_basis"] is True

    assert material["local_only"] is True
    assert material["must_not_export"] is True
    assert material["disposal_required"] is True
    assert material["local_only_root_ref"] == ahr.P7_R54_AHR04_LOCAL_ONLY_ROOT_AVAILABLE_REF
    assert material["local_only_root_available"] is True
    assert material["local_only_root_is_ref_only"] is True
    assert material["explicit_allow_token_ref"] == ahr.P7_R54_AHR04_EXPLICIT_LOCAL_ONLY_ALLOW_REF
    assert material["explicit_allow_token_present"] is True
    assert material["review_session_present"] is True
    assert material["current_execution_basis_refreeze_ready"] is True
    assert material["historical_helper_refs_reconciled_before_preflight"] is True
    assert material["r55_hold_intaken_before_preflight"] is True
    assert material["manifest_source_available"] is True
    assert material["export_denylist_ready"] is True
    assert tuple(material["export_denylist_refs"]) == ahr.P7_R54_AHR04_EXPORT_DENYLIST_REFS
    assert material["export_denylist_ref_count"] == len(ahr.P7_R54_AHR04_EXPORT_DENYLIST_REFS)
    assert tuple(material["forbidden_output_refs"]) == ahr.P7_R54_AHR04_FORBIDDEN_OUTPUT_REFS
    assert material["purge_plan_ready"] is True
    assert material["body_full_artifact_public_export_allowed"] is False
    assert material["terminal_output_body_allowed"] is False
    assert material["api_db_rn_runtime_touch_allowed"] is False
    assert material["api_db_rn_runtime_no_touch"] is True
    assert material["preflight_status"] == ahr.P7_R54_AHR04_PREFLIGHT_READY_STATUS_REF
    assert material["preflight_reason_refs"] == [ahr.P7_R54_AHR04_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["open_execution_blocker_ids"] == []
    assert material["body_full_packet_generation_allowed_before_preflight"] is False
    assert material["body_full_packet_generation_allowed_by_preflight"] is True
    assert material["body_full_packet_generation_request_allowed_next"] is False
    assert material["body_full_generation_blocked_until_manifest_freeze"] is True
    assert material["actual_review_execution_blocked_until_packet_and_manifest_ready"] is True
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR04_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ahr.P7_R54_AHR04_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ahr.P7_R54_AHR05_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert ahr.assert_p7_r54_ahr04_local_only_preflight_contract(material) is True


@pytest.mark.parametrize(
    "kwargs,expected_blocker",
    [
        ({"explicit_allow_token_ref": "missing"}, "explicit_local_only_allow_missing"),
        ({"local_only_root_ref": "missing"}, "local_only_root_missing"),
        ({"manifest_source_ref": "missing"}, "manifest_source_missing"),
        ({"export_denylist_ref": "missing"}, "export_denylist_missing"),
        ({"purge_plan_ref": "missing"}, "purge_plan_missing"),
    ],
)
def test_r54_ahr04_blocks_when_preflight_condition_is_missing(kwargs: dict[str, object], expected_blocker: str) -> None:
    material = ahr.build_p7_r54_ahr04_local_only_preflight(**kwargs)

    assert material["preflight_status"] == ahr.P7_R54_AHR04_PREFLIGHT_BLOCKED_STATUS_REF
    assert expected_blocker in material["execution_blocker_ids"]
    assert material["body_full_packet_generation_allowed_by_preflight"] is False
    assert material["body_full_packet_generation_request_allowed_next"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR04_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert ahr.assert_p7_r54_ahr04_local_only_preflight_contract(material) is True


@pytest.mark.parametrize(
    "key,value",
    [
        ("local_only", False),
        ("must_not_export", False),
        ("disposal_required", False),
        ("local_only_root_is_ref_only", False),
        ("review_session_present", False),
        ("current_execution_basis_refreeze_ready", False),
        ("historical_helper_refs_reconciled_before_preflight", False),
        ("r55_hold_intaken_before_preflight", False),
        ("body_full_generation_blocked_until_manifest_freeze", False),
        ("actual_review_execution_blocked_until_packet_and_manifest_ready", False),
        ("body_full_artifact_public_export_allowed", True),
        ("terminal_output_body_allowed", True),
        ("api_db_rn_runtime_touch_allowed", True),
        ("api_db_rn_runtime_no_touch", False),
        ("body_full_packet_generation_allowed_before_preflight", True),
        ("body_full_packet_generation_request_allowed_next", True),
        ("preflight_status", "OTHER"),
        ("next_required_step", ahr.P7_R54_AHR06_STEP_REF),
        ("raw_body_included", True),
        ("question_text_included", True),
        ("actual_human_review_executed_by_person", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_r54_ahr04_rejects_preflight_mutations(key: str, value: object) -> None:
    mutated = deepcopy(ahr.build_p7_r54_ahr04_local_only_preflight())
    mutated[key] = value
    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr04_local_only_preflight_contract(mutated)


def test_r54_ahr04_rejects_passing_ahr03_without_evidence_missing_hold() -> None:
    broken_ahr03 = deepcopy(ahr.build_p7_r54_ahr03_r55_hold_evidence_missing_intake())
    broken_ahr03["actual_review_evidence_missing_confirmed"] = False
    with pytest.raises(ValueError):
        ahr.build_p7_r54_ahr04_local_only_preflight(r55_hold_evidence_missing_intake=broken_ahr03)


def test_r54_ahr05_freezes_24_case_manifest_as_bodyfree_rows_only() -> None:
    ahr04 = ahr.build_p7_r54_ahr04_local_only_preflight()
    material = ahr.build_p7_r54_ahr05_24_case_manifest_freeze(local_only_preflight=ahr04)

    assert set(material) == set(ahr.P7_R54_AHR_24_CASE_MANIFEST_FREEZE_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == ahr.P7_R54_AHR_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION
    assert material["policy_section"] == ahr.P7_R54_AHR05_STEP_REF
    assert material["operation_step_ref"] == ahr.P7_R54_AHR05_STEP_REF
    assert material["ahr04_schema_version"] == ahr.P7_R54_AHR_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION
    assert material["ahr04_next_required_step"] == ahr.P7_R54_AHR05_STEP_REF
    assert material["ahr04_preflight_status"] == ahr.P7_R54_AHR04_PREFLIGHT_READY_STATUS_REF
    assert material["ahr04_body_full_packet_generation_allowed_by_preflight"] is True
    assert material["local_only_preflight_ready"] is True
    assert material["current_execution_basis_refs"] == ahr.P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS
    assert material["operation_current_refs_are_actual_execution_basis"] is True

    assert material["manifest_source_kind_ref"] == ahr.P7_R54_AHR05_MANIFEST_SOURCE_KIND_REF
    assert material["r48_case_matrix_schema_version"] == r54op.P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION
    assert material["required_case_count"] == 24
    assert material["case_distribution"] == ahr.P7_R54_AHR05_CASE_DISTRIBUTION
    assert material["case_distribution_total_count"] == 24
    assert material["case_distribution_matches_design"] is True
    assert material["manifest_status"] == ahr.P7_R54_AHR05_MANIFEST_READY_STATUS_REF
    assert material["manifest_reason_refs"] == [ahr.P7_R54_AHR05_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["open_execution_blocker_ids"] == []
    assert material["case_row_count"] == 24
    assert len(material["case_rows"]) == 24
    assert material["case_rows_bodyfree_only"] is True
    assert material["case_ref_id_count"] == 24
    assert material["case_ref_ids_unique"] is True
    assert material["blind_case_id_count"] == 24
    assert material["blind_case_ids_unique"] is True
    assert material["packet_ref_id_count"] == 24
    assert material["packet_ref_ids_unique"] is True
    assert material["blind_case_id_case_ref_separated"] is True
    assert material["blind_case_id_packet_ref_separated"] is True
    assert material["case_ref_id_packet_ref_separated"] is True
    assert material["family_case_counts"] == ahr.P7_R54_AHR05_CASE_DISTRIBUTION
    assert material["review_axis_profile_ref"] == ahr.P7_R54_AHR05_REVIEW_AXIS_PROFILE_REF
    assert tuple(material["rating_axis_refs"]) == ahr.P7_R54_AHR05_RATING_AXIS_REFS
    assert material["rating_axis_count"] == 6
    assert material["rating_axis_target_thresholds"] == ahr.P7_R54_AHR05_RATING_AXIS_TARGET_THRESHOLDS
    assert material["requires_history_line_review_count"] == 20
    assert material["current_only_boundary_case_count"] == 4
    assert material["reviewer_facing_family_exposed"] is False
    assert material["reviewer_facing_tier_exposed"] is False
    assert material["body_full_packet_materialized_here"] is False
    assert material["local_reviewer_payload_materialized_here"] is False
    assert material["body_full_packet_generation_requested_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_human_review_run_here"] is False
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["body_full_packet_generation_request_allowed_next"] is True
    assert material["body_full_generation_blocked_until_packet_generation_request"] is True
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR05_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ahr.P7_R54_AHR05_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ahr.P7_R54_AHR06_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert ahr.assert_p7_r54_ahr05_24_case_manifest_freeze_contract(material) is True


def test_r54_ahr05_case_rows_hide_family_tier_from_reviewer_and_keep_bodyfull_unmaterialized() -> None:
    material = ahr.build_p7_r54_ahr05_24_case_manifest_freeze()

    for index, row in enumerate(material["case_rows"], start=1):
        assert set(row) == set(ahr.P7_R54_AHR05_CASE_MANIFEST_ROW_REQUIRED_FIELD_REFS)
        assert row["case_index"] == index
        assert row["case_ref_id"] != row["blind_case_id"]
        assert row["packet_ref_id"] not in {row["case_ref_id"], row["blind_case_id"]}
        assert row["family"] in ahr.P7_R54_AHR05_CASE_DISTRIBUTION
        assert row["case_role"] == ahr.P7_R54_AHR05_CASE_ROLE_BY_FAMILY[row["family"]]
        assert row["review_axis_profile_ref"] == ahr.P7_R54_AHR05_REVIEW_AXIS_PROFILE_REF
        assert row["reviewer_facing_family_exposed"] is False
        assert row["reviewer_facing_tier_exposed"] is False
        assert row["body_full_packet_materialized_here"] is False
        assert row["local_reviewer_payload_materialized_here"] is False
        assert row["body_free"] is True
    assert ahr.assert_p7_r54_ahr05_24_case_manifest_freeze_contract(material) is True


def test_r54_ahr05_blocks_manifest_when_preflight_is_blocked() -> None:
    blocked_preflight = ahr.build_p7_r54_ahr04_local_only_preflight(explicit_allow_token_ref="missing")
    material = ahr.build_p7_r54_ahr05_24_case_manifest_freeze(local_only_preflight=blocked_preflight)

    assert material["manifest_status"] == ahr.P7_R54_AHR05_MANIFEST_BLOCKED_STATUS_REF
    assert "explicit_local_only_allow_missing" in material["execution_blocker_ids"]
    assert material["body_full_packet_generation_request_allowed_next"] is False
    assert material["case_rows"] == []
    assert material["case_row_count"] == 0
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR04_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ahr.P7_R54_AHR04_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ahr.P7_R54_AHR05_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert ahr.assert_p7_r54_ahr05_24_case_manifest_freeze_contract(material) is True


@pytest.mark.parametrize(
    "mutator",
    [
        lambda m: m.__setitem__("required_case_count", 23),
        lambda m: m.__setitem__("case_distribution", {"history_line_eligible_input": 24}),
        lambda m: m.__setitem__("case_distribution_matches_design", False),
        lambda m: m.__setitem__("case_row_count", 23),
        lambda m: m.__setitem__("case_rows", m["case_rows"][:-1]),
        lambda m: m.__setitem__("case_ref_ids_unique", False),
        lambda m: m.__setitem__("blind_case_ids_unique", False),
        lambda m: m.__setitem__("packet_ref_ids_unique", False),
        lambda m: m.__setitem__("blind_case_id_case_ref_separated", False),
        lambda m: m.__setitem__("blind_case_id_packet_ref_separated", False),
        lambda m: m.__setitem__("case_ref_id_packet_ref_separated", False),
        lambda m: m.__setitem__("family_case_counts", {"history_line_eligible_input": 24}),
        lambda m: m.__setitem__("case_rows_bodyfree_only", False),
        lambda m: m.__setitem__("requires_history_line_review_count", 24),
        lambda m: m.__setitem__("current_only_boundary_case_count", 0),
        lambda m: m.__setitem__("reviewer_facing_family_exposed", True),
        lambda m: m.__setitem__("reviewer_facing_tier_exposed", True),
        lambda m: m.__setitem__("body_full_packet_materialized_here", True),
        lambda m: m.__setitem__("local_reviewer_payload_materialized_here", True),
        lambda m: m.__setitem__("body_full_packet_generation_requested_here", True),
        lambda m: m.__setitem__("actual_human_review_run_here", True),
        lambda m: m.__setitem__("actual_rating_rows_materialized_here", True),
        lambda m: m.__setitem__("actual_question_need_observation_rows_materialized_here", True),
        lambda m: m.__setitem__("actual_disposal_receipt_materialized_here", True),
        lambda m: m.__setitem__("body_full_packet_generation_request_allowed_next", False),
        lambda m: m.__setitem__("next_required_step", ahr.P7_R54_AHR07_STEP_REF),
        lambda m: m.__setitem__("p8_start_allowed", True),
        lambda m: m.__setitem__("question_text_included", True),
    ],
)
def test_r54_ahr05_rejects_manifest_boundary_mutations(mutator) -> None:  # type: ignore[no-untyped-def]
    mutated = deepcopy(ahr.build_p7_r54_ahr05_24_case_manifest_freeze())
    mutator(mutated)
    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr05_24_case_manifest_freeze_contract(mutated)


@pytest.mark.parametrize(
    "row_key,value",
    [
        ("reviewer_facing_family_exposed", True),
        ("reviewer_facing_tier_exposed", True),
        ("body_full_packet_materialized_here", True),
        ("local_reviewer_payload_materialized_here", True),
        ("body_free", False),
        ("case_role", "wrong_role"),
        ("requires_history_line_review", False),
    ],
)
def test_r54_ahr05_rejects_case_row_mutations(row_key: str, value: object) -> None:
    mutated = deepcopy(ahr.build_p7_r54_ahr05_24_case_manifest_freeze())
    mutated["case_rows"][0][row_key] = value
    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr05_24_case_manifest_freeze_contract(mutated)


def test_r54_ahr05_rejects_case_ref_and_blind_case_id_collision() -> None:
    mutated = deepcopy(ahr.build_p7_r54_ahr05_24_case_manifest_freeze())
    mutated["case_rows"][0]["blind_case_id"] = mutated["case_rows"][0]["case_ref_id"]
    mutated["blind_case_ids"][0] = mutated["case_rows"][0]["case_ref_id"]
    mutated["blind_case_id_case_ref_separated"] = False
    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr05_24_case_manifest_freeze_contract(mutated)


def test_r54_ahr05_builds_blocked_manifest_for_incomplete_source_rows() -> None:
    rows = ahr._ahr05_default_case_manifest_rows()[:-1]
    material = ahr.build_p7_r54_ahr05_24_case_manifest_freeze(case_rows=rows)

    assert material["manifest_status"] == ahr.P7_R54_AHR05_MANIFEST_BLOCKED_STATUS_REF
    assert "case_count_not_24" in material["execution_blocker_ids"]
    assert material["case_rows"] == []
    assert material["body_full_packet_generation_request_allowed_next"] is False
    assert ahr.assert_p7_r54_ahr05_24_case_manifest_freeze_contract(material) is True


def test_r54_ahr04_ahr05_compatibility_aliases_match_primary_builders() -> None:
    assert ahr.build_p7_r54_ahr04_local_only_preflight_bodyfree is ahr.build_p7_r54_ahr04_local_only_preflight
    assert (
        ahr.assert_p7_r54_ahr04_local_only_preflight_bodyfree_contract
        is ahr.assert_p7_r54_ahr04_local_only_preflight_contract
    )
    assert ahr.build_p7_r54_ahr05_24_case_manifest_freeze_bodyfree is ahr.build_p7_r54_ahr05_24_case_manifest_freeze
    assert (
        ahr.assert_p7_r54_ahr05_24_case_manifest_freeze_bodyfree_contract
        is ahr.assert_p7_r54_ahr05_24_case_manifest_freeze_contract
    )
    assert (
        ahr.build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr04_local_only_preflight
        is ahr.build_p7_r54_ahr04_local_only_preflight
    )
    assert (
        ahr.build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr05_24_case_manifest_freeze
        is ahr.build_p7_r54_ahr05_24_case_manifest_freeze
    )
