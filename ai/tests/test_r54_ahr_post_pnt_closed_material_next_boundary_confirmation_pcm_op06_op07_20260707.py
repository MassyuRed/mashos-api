# -*- coding: utf-8 -*-
"""R54-AHR Post-PNT closed material next boundary confirmation PCM-OP06/OP07 tests."""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_20260707 as pcm
from r54_ahr_post_pnt_pcm_compact_pnt_op08_fixture_20260708 import (
    compact_closed_pnt_op08_for_pcm_regression,
)


PCM_R5_FORBIDDEN_EXECUTION_KEYS = (
    "pnt_op08_default_builder_called_here",
    "pnt_op08_default_material_synthesized_here",
    "pnt_op08_builder_called_here",
    "pnt_op08_material_synthesized_here",
    "pnt_r11_decision_table_used_as_single_lane_here",
    "selected_post_nci_next_boundary_executed_here",
    "selected_pcm_next_boundary_executed_here",
    "selected_pcm_next_boundary_execution_allowed_here",
    "execution_allowed_here",
    "validation_commands_executed_here",
    "pytest_executed_here",
    "pcm_target_tests_executed_here",
    "selected_regression_executed_here",
    "compileall_executed_here",
    "post_pnt_closed_material_confirmation_result_memo_draft_execution_allowed_here",
    "dhr_op05_called_here",
    "dhr_op05_builder_called_here",
    "dhr_op06_called_here",
    "dhr_op07_materialized_here",
    "dmd_execution_started_here",
    "r52_actual_execution_started_here",
    "actual_body_full_packet_generated_here",
    "actual_review_started_here",
    "actual_rows_created_here",
    "actual_question_need_observation_rows_created_here",
    "actual_disposal_or_purge_executed_here",
    "raw_evidence_request_created_here",
    "repair_executed_here",
    "p8_start_allowed",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "question_text_materialized",
    "api_changed",
    "db_changed",
    "rn_changed",
    "runtime_changed",
    "response_key_changed",
    "json_schema_file_created_here",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_confirmed",
    "rn_contract_green_confirmed",
    "rn_real_device_modal_verified_claimed_here",
)


PCM_R5_SIX_LANE_EXPECTED_LANE_REFS = (
    pcm.P7_R54_AHR_POST_PNT_PCM_LANE_DHR_OP05_MANUAL_HANDOFF_BOUNDARY_DESIGN_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_LANE_RETRY_OR_START_ACTUAL_LOCAL_ONLY_REVIEW_ROUTE_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REINTAKE_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_LANE_REPAIR_RDB_CANDIDATE_OR_UPSTREAM_RESULT_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_LANE_MANUAL_HOLD_UNRESOLVED_POST_RDB08_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_LANE_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_CANDIDATE_REF,
)


PCM_R5_EXPECTED_NEXT_WORK_CLASS_REFS = (
    pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_NEXT_DESIGN_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_NEXT_DESIGN_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_WAIT_HOLD_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_NEXT_DESIGN_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_STOP_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_STOP_REF,
)


@lru_cache(maxsize=6)
def _cached_closed_pnt_op08(index: int = 0) -> tuple[tuple[str, object], ...]:
    return tuple(compact_closed_pnt_op08_for_pcm_regression(index).items())


def _closed_pnt_op08(index: int = 0) -> dict[str, object]:
    return dict(_cached_closed_pnt_op08(index))


@lru_cache(maxsize=6)
def _cached_pcm_op05_from_closed(index: int = 0) -> tuple[tuple[str, object], ...]:
    op01 = pcm.build_p7_r54_ahr_post_pnt_pcm_op01_explicit_closed_pnt_op08_material_intake(
        pnt_op08_bodyfree_result_memo_closure_material=_closed_pnt_op08(index),
    )
    op02 = pcm.build_p7_r54_ahr_post_pnt_pcm_op02_closed_material_contract_validation(op01)
    op03 = pcm.build_p7_r54_ahr_post_pnt_pcm_op03_single_selected_lane_confirmation(op02)
    op04 = pcm.build_p7_r54_ahr_post_pnt_pcm_op04_next_work_class_resolver(op03)
    op05 = pcm.build_p7_r54_ahr_post_pnt_pcm_op05_next_design_candidate_envelope_materialization(op04)
    return tuple(op05.items())


def _pcm_op05_from_closed(index: int = 0) -> dict[str, object]:
    return deepcopy(dict(_cached_pcm_op05_from_closed(index)))


def _pcm_op06_from_closed(index: int = 0) -> dict[str, object]:
    return pcm.build_p7_r54_ahr_post_pnt_pcm_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard(_pcm_op05_from_closed(index))


def _assert_pcm_r5_no_execution_or_claim(material: dict[str, object]) -> None:
    for key in PCM_R5_FORBIDDEN_EXECUTION_KEYS:
        if key in material:
            assert material[key] is False, key
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True
    assert material["dhr_op05_call_allowed_here"] is False
    assert material["dhr_op05_builder_call_allowed_here"] is False
    assert material["actual_review_start_allowed_here"] is False
    assert material["repair_execution_allowed_here"] is False
    assert material["raw_evidence_request_allowed_here"] is False
    assert material["p8_question_design_allowed_here"] is False
    assert material["api_db_rn_response_key_change_allowed_here"] is False
    assert material["json_schema_file_creation_allowed_here"] is False
    assert material["full_backend_suite_green_confirmed"] is False
    assert material["rn_contract_green_confirmed"] is False
    assert material["rn_real_device_modal_verified_claimed_here"] is False


@pytest.mark.parametrize(
    ("case_index", "expected_lane", "expected_next_work_class"),
    [
        (index, lane, next_work_class)
        for index, (lane, next_work_class) in enumerate(zip(PCM_R5_SIX_LANE_EXPECTED_LANE_REFS, PCM_R5_EXPECTED_NEXT_WORK_CLASS_REFS))
    ],
    ids=["dhr", "retry", "wait", "repair", "unresolved", "blocked"],
)
def test_pcm_op06_guard_passes_all_valid_op05_outcomes_without_execution_or_claim(
    case_index: int,
    expected_lane: str,
    expected_next_work_class: str,
) -> None:
    op06 = pcm.build_p7_r54_ahr_post_pnt_pcm_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard(_pcm_op05_from_closed(case_index))

    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract(op06) is True
    assert op06["pcm_op06_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP06_STATUS_GUARD_PASSED_REF
    assert op06["pcm_op06_guard_passed"] is True
    assert op06["selected_pnt_lane_ref"] == expected_lane
    assert op06["selected_pcm_next_work_class_ref"] == expected_next_work_class
    assert op06["selected_pcm_next_boundary_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_LANE_TO_SELECTED_PCM_NEXT_BOUNDARY_REF_MAP[expected_lane]
    assert op06["selected_post_nci_next_boundary_not_executed"] is True
    assert op06["selected_handoff_or_stop_not_executed"] is True
    assert op06["selected_pcm_next_boundary_not_executed"] is True
    assert op06["selected_pcm_next_boundary_envelope_materialized_here"] is True
    assert op06["validation_commands_executed_here"] is False
    assert op06["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP07_STEP_REF
    assert op06["pcm_op06_blocker_refs"] == []
    _assert_pcm_r5_no_execution_or_claim(op06)


@pytest.mark.parametrize(
    ("case_index", "expected_lane", "expected_next_work_class"),
    [
        (index, lane, next_work_class)
        for index, (lane, next_work_class) in enumerate(zip(PCM_R5_SIX_LANE_EXPECTED_LANE_REFS, PCM_R5_EXPECTED_NEXT_WORK_CLASS_REFS))
    ],
    ids=["dhr", "retry", "wait", "repair", "unresolved", "blocked"],
)
def test_pcm_op07_records_validation_plan_and_result_memo_draft_without_running_validation(
    case_index: int,
    expected_lane: str,
    expected_next_work_class: str,
) -> None:
    op07 = pcm.build_p7_r54_ahr_post_pnt_pcm_op07_validation_plan_result_memo_draft_material(_pcm_op06_from_closed(case_index))

    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op07_validation_plan_result_memo_draft_material_contract(op07) is True
    assert op07["selected_pnt_lane_ref"] == expected_lane
    assert op07["selected_pcm_next_work_class_ref"] == expected_next_work_class
    assert op07["validation_plan_recorded"] is True
    assert op07["validation_plan_bodyfree"] is True
    assert op07["validation_commands_executed_here"] is False
    assert op07["pytest_executed_here"] is False
    assert op07["pcm_target_tests_executed_here"] is False
    assert op07["selected_regression_executed_here"] is False
    assert op07["compileall_executed_here"] is False
    assert tuple(op07["target_test_ref_refs"]) == pcm.P7_R54_AHR_POST_PNT_PCM_TARGET_TEST_REF_REFS
    assert tuple(op07["selected_regression_test_ref_refs"]) == pcm.P7_R54_AHR_POST_PNT_PCM_SELECTED_REGRESSION_TEST_REF_REFS
    assert tuple(op07["compileall_target_ref_refs"]) == pcm.P7_R54_AHR_POST_PNT_PCM_COMPILEALL_TARGET_REF_REFS
    assert tuple(op07["validation_command_summary_refs"]) == pcm.P7_R54_AHR_POST_PNT_PCM_VALIDATION_COMMAND_SUMMARY_REFS
    assert op07["post_pnt_closed_material_confirmation_result_memo_draft_bodyfree"] is True
    assert op07["post_pnt_closed_material_confirmation_result_memo_draft_materialized_here"] is True
    assert op07["post_pnt_closed_material_confirmation_result_memo_draft_execution_allowed_here"] is False
    assert op07["pcm_op07_ready_for_op08"] is True
    assert op07["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP08_STEP_REF
    assert op07["pcm_op07_blocker_refs"] == []
    if expected_next_work_class in (pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_WAIT_HOLD_REF, pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_STOP_REF):
        assert op07["pcm_op07_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP07_STATUS_WAIT_OR_STOP_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED_REF
    else:
        assert op07["pcm_op07_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP07_STATUS_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED_REF
    _assert_pcm_r5_no_execution_or_claim(op07)


@pytest.mark.parametrize(
    ("mutation_key", "mutation_value", "expected_blocker"),
    [
        ("question_text", "do not materialize", "op06_guard_forbidden_payload_key_detected"),
        ("raw_evidence", "raw", "op06_guard_forbidden_payload_key_detected"),
        ("pnt_op08_builder_called_here", True, "op06_guard_promotion_or_autorun_claim_detected"),
        ("dhr_op05_called_here", True, "op06_guard_promotion_or_autorun_claim_detected"),
        ("p8_question_design_started", True, "op06_guard_promotion_or_autorun_claim_detected"),
        ("release_allowed", True, "op06_guard_promotion_or_autorun_claim_detected"),
        ("api_changed", True, "op06_guard_promotion_or_autorun_claim_detected"),
        ("response_key_changed", True, "op06_guard_promotion_or_autorun_claim_detected"),
        ("stdout", "not allowed", "op06_guard_forbidden_payload_key_detected"),
    ],
)
def test_pcm_op06_blocks_body_payload_promotion_validation_and_public_contract_mutation_claims(
    mutation_key: str,
    mutation_value: object,
    expected_blocker: str,
) -> None:
    op05 = deepcopy(_pcm_op05_from_closed(0))
    op05[mutation_key] = mutation_value

    op06 = pcm.build_p7_r54_ahr_post_pnt_pcm_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard(op05)

    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract(op06) is True
    assert op06["pcm_op06_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP06_STATUS_BLOCKED_GUARD_REF
    assert op06["pcm_op06_bodyfree_leak_promotion_or_autorun_blocked"] is True
    assert expected_blocker in op06["pcm_op06_blocker_refs"]
    assert op06["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_BODYFREE_NO_TOUCH_NO_PROMOTION_GUARD_REF
    _assert_pcm_r5_no_execution_or_claim(op06)


@pytest.mark.parametrize(
    ("mutation_key", "mutation_value", "expected_blocker"),
    [
        ("question_text", "do not materialize", "op07_result_memo_draft_forbidden_payload_key_detected"),
        ("raw_evidence", "raw", "op07_result_memo_draft_forbidden_payload_key_detected"),
        ("stdout", "not allowed", "op07_result_memo_draft_forbidden_payload_key_detected"),
        ("dhr_op05_called_here", True, "op07_result_memo_draft_promotion_or_autorun_claim_detected"),
        ("p8_question_design_started", True, "op07_result_memo_draft_promotion_or_autorun_claim_detected"),
        ("release_allowed", True, "op07_result_memo_draft_promotion_or_autorun_claim_detected"),
        ("rn_changed", True, "op07_result_memo_draft_promotion_or_autorun_claim_detected"),
    ],
)
def test_pcm_op07_blocks_body_payload_promotion_and_no_touch_claims_before_draft_materialization(
    mutation_key: str,
    mutation_value: object,
    expected_blocker: str,
) -> None:
    op06 = deepcopy(_pcm_op06_from_closed(0))
    op06[mutation_key] = mutation_value

    op07 = pcm.build_p7_r54_ahr_post_pnt_pcm_op07_validation_plan_result_memo_draft_material(op06)

    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op07_validation_plan_result_memo_draft_material_contract(op07) is True
    assert op07["pcm_op07_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP07_STATUS_BLOCKED_RESULT_MEMO_DRAFT_REF
    assert op07["pcm_op07_bodyfree_leak_promotion_or_autorun_blocked"] is True
    assert expected_blocker in op07["pcm_op07_blocker_refs"]
    assert op07["post_pnt_closed_material_confirmation_result_memo_draft_materialized_here"] is False
    assert op07["pcm_op07_ready_for_op08"] is False
    assert op07["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_RESULT_MEMO_DRAFT_REF
    _assert_pcm_r5_no_execution_or_claim(op07)


def test_pcm_op06_and_op07_repair_missing_or_invalid_input_without_synthesizing_or_promoting() -> None:
    missing_op06 = pcm.build_p7_r54_ahr_post_pnt_pcm_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard()
    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract(missing_op06) is True
    assert missing_op06["pcm_op06_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP06_STATUS_REPAIR_REQUIRED_FOR_GUARD_INPUTS_REF
    assert "pcm_op05_next_design_candidate_envelope_material_missing" in missing_op06["pcm_op06_blocker_refs"]
    assert missing_op06["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_BODYFREE_NO_TOUCH_NO_PROMOTION_GUARD_INPUTS_REF
    _assert_pcm_r5_no_execution_or_claim(missing_op06)

    invalid_op05 = deepcopy(_pcm_op05_from_closed(0))
    invalid_op05["selected_pcm_next_boundary_envelope_materialized_here"] = False
    repaired_op06 = pcm.build_p7_r54_ahr_post_pnt_pcm_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard(invalid_op05)
    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract(repaired_op06) is True
    assert repaired_op06["pcm_op06_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP06_STATUS_REPAIR_REQUIRED_FOR_GUARD_INPUTS_REF
    assert "pcm_op05_next_design_candidate_envelope_contract_invalid" in repaired_op06["pcm_op06_blocker_refs"]
    _assert_pcm_r5_no_execution_or_claim(repaired_op06)

    missing_op07 = pcm.build_p7_r54_ahr_post_pnt_pcm_op07_validation_plan_result_memo_draft_material()
    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op07_validation_plan_result_memo_draft_material_contract(missing_op07) is True
    assert missing_op07["pcm_op07_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP07_STATUS_REPAIR_REQUIRED_FOR_RESULT_MEMO_DRAFT_INPUTS_REF
    assert "pcm_op06_guard_material_missing" in missing_op07["pcm_op07_blocker_refs"]
    assert missing_op07["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_RESULT_MEMO_DRAFT_INPUTS_REF
    _assert_pcm_r5_no_execution_or_claim(missing_op07)

    invalid_op06 = deepcopy(_pcm_op06_from_closed(0))
    invalid_op06["pcm_op06_guard_passed"] = False
    repaired_op07 = pcm.build_p7_r54_ahr_post_pnt_pcm_op07_validation_plan_result_memo_draft_material(invalid_op06)
    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op07_validation_plan_result_memo_draft_material_contract(repaired_op07) is True
    assert repaired_op07["pcm_op07_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP07_STATUS_REPAIR_REQUIRED_FOR_RESULT_MEMO_DRAFT_INPUTS_REF
    assert "pcm_op06_guard_contract_invalid" in repaired_op07["pcm_op07_blocker_refs"]
    _assert_pcm_r5_no_execution_or_claim(repaired_op07)


def test_pcm_op06_op07_full_title_aliases_match_short_builders_and_contracts() -> None:
    op05 = _pcm_op05_from_closed(0)
    short_op06 = pcm.build_p7_r54_ahr_post_pnt_pcm_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard(op05)
    long_op06 = pcm.build_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard(op05)
    assert short_op06 == long_op06
    assert pcm.assert_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract(long_op06) is True

    short_op07 = pcm.build_p7_r54_ahr_post_pnt_pcm_op07_validation_plan_result_memo_draft_material(short_op06)
    long_op07 = pcm.build_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op07_validation_plan_result_memo_draft_material(short_op06)
    assert short_op07 == long_op07
    assert pcm.assert_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op07_validation_plan_result_memo_draft_material_contract(long_op07) is True
