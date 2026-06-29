# -*- coding: utf-8 -*-
"""R54 current snapshot local review run CLR04-CLR05 contract tests."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as r54op
import emlis_ai_p7_r54_current_snapshot_local_review_run_20260627 as clr03
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr04_clr05_20260627 as clr


FORBIDDEN_BODY_OR_QUESTION_KEYS = (
    "raw_input",
    "returned_emlis_body",
    "history_surface",
    "reviewer_free_text",
    "reviewer_note",
    "reviewer_notes",
    "question_text",
    "draft_question_text",
    "local_absolute_path",
    "body_hash",
    "packet_content",
    "terminal_output_body",
)


def _assert_bodyfree_no_touch(material: dict[str, Any]) -> None:
    assert material["body_free"] is True
    for key in clr03.P7_R54_CLR_FALSE_FLAG_REFS:
        assert material[key] is False, key
    for flag_map_key in ("public_contract", "r54_clr_no_touch_contract", "body_free_markers"):
        assert material[flag_map_key]
        assert all(value is False for value in material[flag_map_key].values()), flag_map_key
    for forbidden_key in FORBIDDEN_BODY_OR_QUESTION_KEYS:
        assert forbidden_key not in material


def test_r54_clr00_to_clr03_are_present_before_clr04_clr05() -> None:
    clr00 = clr03.build_p7_r54_clr00_scope_no_touch_boundary_freeze()
    clr01 = clr03.build_p7_r54_clr01_current_snapshot_basis_refreeze(scope_no_touch_boundary_freeze=clr00)
    clr02 = clr03.build_p7_r54_clr02_historical_helper_refs_reconcile(current_snapshot_basis_refreeze=clr01)
    clr03_material = clr03.build_p7_r54_clr03_r55_hold_evidence_missing_intake(historical_helper_refs_reconcile=clr02)

    assert clr03.assert_p7_r54_clr00_scope_no_touch_boundary_freeze_contract(clr00) is True
    assert clr03.assert_p7_r54_clr01_current_snapshot_basis_refreeze_contract(clr01) is True
    assert clr03.assert_p7_r54_clr02_historical_helper_refs_reconcile_contract(clr02) is True
    assert clr03.assert_p7_r54_clr03_r55_hold_evidence_missing_intake_contract(clr03_material) is True
    assert clr03_material["next_required_step"] == clr.P7_R54_CLR04_STEP_REF
    assert clr03_material["r52_reintake_handoff_status_ref"] == clr03.P7_R54_CLR03_R52_REINTAKE_BLOCKED_STATUS_REF
    assert clr03_material["actual_review_evidence_missing_before_run"] is True


def test_r54_clr04_local_only_preflight_ready_is_bodyfree_and_does_not_generate_packet() -> None:
    material = clr.build_p7_r54_clr04_local_only_preflight()

    assert set(material) == set(clr.P7_R54_CLR04_LOCAL_ONLY_PREFLIGHT_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == clr.P7_R54_CLR04_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION
    assert material["policy_section"] == clr.P7_R54_CLR04_STEP_REF
    assert material["operation_step_ref"] == clr.P7_R54_CLR04_STEP_REF
    assert material["clr03_next_required_step"] == clr.P7_R54_CLR04_STEP_REF
    assert material["clr03_r55_hold_state_preserved"] is True
    assert material["clr03_actual_review_evidence_missing_before_run"] is True

    assert material["explicit_local_only_allow_present"] is True
    assert material["review_session_present"] is True
    assert material["current_snapshot_basis_refreeze_ready"] is True
    assert material["historical_helper_refs_reconciled_before_preflight"] is True
    assert material["r55_hold_intaken_before_preflight"] is True
    assert material["manifest_source_available"] is True
    assert material["export_denylist_ready"] is True
    assert material["purge_plan_ready"] is True
    assert material["no_api_db_rn_runtime_touch"] is True
    assert material["preflight_status"] == clr.P7_R54_CLR04_PREFLIGHT_READY_STATUS_REF
    assert material["preflight_reason_refs"] == [clr.P7_R54_CLR04_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []

    assert material["body_full_packet_generation_allowed_before_preflight"] is False
    assert material["body_full_packet_generation_allowed_by_preflight"] is True
    assert material["body_full_packet_generation_request_allowed_next"] is False
    assert material["body_full_generation_blocked_until_manifest_freeze"] is True
    assert material["actual_review_execution_blocked_until_packet_and_manifest_ready"] is True
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_human_review_run_here"] is False
    assert tuple(material["implemented_steps"]) == clr.P7_R54_CLR04_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == clr.P7_R54_CLR04_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == clr.P7_R54_CLR05_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr04_local_only_preflight_contract(material) is True


@pytest.mark.parametrize(
    "kwargs,expected_blocker",
    [
        ({"explicit_local_only_allow_ref": "missing"}, "review_packet_generation_blocked_missing_explicit_allow"),
        ({"manifest_source_ref": "missing"}, "review_case_material_missing"),
        ({"export_denylist_ref": "missing"}, "body_free_validation_failed"),
        ({"purge_plan_ref": "missing"}, "body_purge_not_verified"),
        ({"no_api_db_rn_runtime_touch": False}, "no_touch_violation_detected"),
    ],
)
def test_r54_clr04_blocks_preflight_when_required_local_only_conditions_are_missing(
    kwargs: dict[str, object], expected_blocker: str
) -> None:
    material = clr.build_p7_r54_clr04_local_only_preflight(**kwargs)

    assert material["preflight_status"] == clr.P7_R54_CLR04_PREFLIGHT_BLOCKED_STATUS_REF
    assert expected_blocker in material["execution_blocker_ids"]
    assert material["body_full_packet_generation_allowed_by_preflight"] is False
    assert material["body_full_packet_generation_request_allowed_next"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_human_review_run_here"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR04_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert clr.assert_p7_r54_clr04_local_only_preflight_contract(material) is True


def test_r54_clr05_freezes_24_case_manifest_without_p4_r11_mixing_or_body_payload() -> None:
    preflight = clr.build_p7_r54_clr04_local_only_preflight()
    material = clr.build_p7_r54_clr05_24_case_manifest_freeze(local_only_preflight=preflight)

    assert set(material) == set(clr.P7_R54_CLR05_24_CASE_MANIFEST_FREEZE_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == clr.P7_R54_CLR05_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION
    assert material["policy_section"] == clr.P7_R54_CLR05_STEP_REF
    assert material["operation_step_ref"] == clr.P7_R54_CLR05_STEP_REF
    assert material["clr04_next_required_step"] == clr.P7_R54_CLR05_STEP_REF
    assert material["clr04_preflight_status"] == clr.P7_R54_CLR04_PREFLIGHT_READY_STATUS_REF
    assert material["clr04_body_full_packet_generation_allowed_by_preflight"] is True
    assert material["local_only_preflight_ready"] is True

    assert material["manifest_status"] == clr.P7_R54_CLR05_MANIFEST_READY_STATUS_REF
    assert material["manifest_reason_refs"] == [clr.P7_R54_CLR05_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["r48_case_matrix_schema_version"] == r54op.P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION
    assert material["r48_case_matrix_case_count"] == 24
    assert material["required_case_count"] == 24
    assert material["manifest_row_count"] == 24
    assert material["manifest_rows_bodyfree_only"] is True
    assert material["case_ref_id_unique"] is True
    assert material["blind_case_id_unique"] is True
    assert material["packet_ref_id_unique"] is True
    assert material["case_distribution"] == clr.P7_R54_CLR05_CASE_DISTRIBUTION
    assert material["case_distribution_total_count"] == 24
    assert material["case_distribution_matches_design"] is True
    assert material["case_role_family_counts"] == clr.P7_R54_CLR05_CASE_DISTRIBUTION
    assert material["rating_axis_refs"] == list(clr.P7_R54_CLR05_RATING_AXIS_REFS)
    assert material["rating_axis_count"] == 6
    assert material["rating_axis_target_thresholds"] == clr.P7_R54_CLR05_RATING_AXIS_TARGET_THRESHOLDS
    assert material["requires_history_line_review_count"] == 20
    assert material["current_only_boundary_case_count"] == 4
    assert material["p4_r11_rows_mixed_in"] is False
    assert material["p4_r11_audit_rows_converted_to_r54_actual_review_cases"] is False

    assert len(material["manifest_rows"]) == 24
    for index, row in enumerate(material["manifest_rows"], start=1):
        assert set(row) == set(clr.P7_R54_CLR05_CASE_ROW_REQUIRED_FIELD_REFS)
        assert row["case_index"] == index
        assert row["body_free"] is True
        assert row["review_axis_profile_ref"] == clr.P7_R54_CLR05_REVIEW_AXIS_PROFILE_REF
        assert row["current_only_boundary_case"] is (row["case_role_family_ref"] in clr.P7_R54_CLR05_CURRENT_ONLY_BOUNDARY_FAMILY_REFS)
        assert row["requires_history_line_review"] is (not row["current_only_boundary_case"])
        for forbidden_key in FORBIDDEN_BODY_OR_QUESTION_KEYS:
            assert forbidden_key not in row

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
    assert tuple(material["implemented_steps"]) == clr.P7_R54_CLR05_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == clr.P7_R54_CLR05_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == clr.P7_R54_CLR06_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr05_24_case_manifest_freeze_contract(material) is True


def test_r54_clr05_blocks_manifest_when_preflight_is_blocked() -> None:
    preflight = clr.build_p7_r54_clr04_local_only_preflight(explicit_local_only_allow_ref="missing")
    material = clr.build_p7_r54_clr05_24_case_manifest_freeze(local_only_preflight=preflight)

    assert material["manifest_status"] == clr.P7_R54_CLR05_MANIFEST_BLOCKED_STATUS_REF
    assert material["local_only_preflight_ready"] is False
    assert material["manifest_rows"] == []
    assert material["manifest_row_count"] == 0
    assert material["case_ref_ids"] == []
    assert material["blind_case_ids"] == []
    assert material["packet_ref_ids"] == []
    assert "review_case_matrix_minimum_not_met" in material["execution_blocker_ids"]
    assert "review_packet_generation_blocked_missing_explicit_allow" in material["execution_blocker_ids"]
    assert material["p4_r11_rows_mixed_in"] is False
    assert material["body_full_packet_generation_request_allowed_next"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_human_review_run_here"] is False
    assert tuple(material["implemented_steps"]) == clr.P7_R54_CLR04_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == clr.P7_R54_CLR04_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == clr.P7_R54_CLR05_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert clr.assert_p7_r54_clr05_24_case_manifest_freeze_contract(material) is True


@pytest.mark.parametrize(
    "key,value",
    [
        ("body_full_packet_generation_allowed_before_preflight", True),
        ("body_full_packet_generation_request_allowed_next", True),
        ("body_full_generation_blocked_until_manifest_freeze", False),
        ("actual_review_execution_blocked_until_packet_and_manifest_ready", False),
        ("body_full_packet_generated_here", True),
        ("actual_human_review_run_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_r54_clr04_rejects_generation_review_or_promotion_mutations(key: str, value: object) -> None:
    material = clr.build_p7_r54_clr04_local_only_preflight()
    mutated = deepcopy(material)
    mutated[key] = value
    with pytest.raises(ValueError):
        clr.assert_p7_r54_clr04_local_only_preflight_contract(mutated)


@pytest.mark.parametrize(
    "key,value",
    [
        ("manifest_row_count", 23),
        ("case_ref_id_unique", False),
        ("blind_case_id_unique", False),
        ("packet_ref_id_unique", False),
        ("case_distribution_matches_design", False),
        ("requires_history_line_review_count", 19),
        ("current_only_boundary_case_count", 5),
        ("p4_r11_rows_mixed_in", True),
        ("p4_r11_audit_rows_converted_to_r54_actual_review_cases", True),
        ("body_full_packet_materialized_here", True),
        ("body_full_packet_generation_requested_here", True),
        ("body_full_packet_generated_here", True),
        ("actual_human_review_run_here", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_r54_clr05_rejects_manifest_bodyfull_review_or_promotion_mutations(key: str, value: object) -> None:
    material = clr.build_p7_r54_clr05_24_case_manifest_freeze()
    mutated = deepcopy(material)
    mutated[key] = value
    with pytest.raises(ValueError):
        clr.assert_p7_r54_clr05_24_case_manifest_freeze_contract(mutated)


def test_r54_clr04_clr05_reject_forbidden_payload_or_question_keys() -> None:
    preflight = clr.build_p7_r54_clr04_local_only_preflight()
    mutated_preflight = deepcopy(preflight)
    mutated_preflight["question_text"] = "forbidden"
    with pytest.raises(ValueError):
        clr.assert_p7_r54_clr04_local_only_preflight_contract(mutated_preflight)

    manifest = clr.build_p7_r54_clr05_24_case_manifest_freeze(local_only_preflight=preflight)
    mutated_manifest = deepcopy(manifest)
    mutated_manifest["manifest_rows"][0]["raw_input"] = "forbidden"
    with pytest.raises(ValueError):
        clr.assert_p7_r54_clr05_24_case_manifest_freeze_contract(mutated_manifest)


def test_r54_clr04_clr05_aliases_remain_available() -> None:
    preflight = clr.build_p7_r54_current_snapshot_local_run_clr04_local_only_preflight()
    assert clr.assert_p7_r54_current_snapshot_local_run_clr04_local_only_preflight_contract(preflight) is True
    assert clr.assert_p7_r54_current_snapshot_local_only_preflight_bodyfree_contract(preflight) is True

    manifest = clr.build_p7_r54_current_snapshot_local_run_clr05_24_case_manifest_freeze(local_only_preflight=preflight)
    assert clr.assert_p7_r54_current_snapshot_local_run_clr05_24_case_manifest_freeze_contract(manifest) is True
    assert clr.assert_p7_r54_current_snapshot_24_case_manifest_freeze_bodyfree_contract(manifest) is True
