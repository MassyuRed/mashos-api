# -*- coding: utf-8 -*-
"""DHC R6 OP08 target tests.

These tests cover only body-free DHC-OP08 result-memo closure material and
stopped next-work candidates. They must not execute validation commands, create
result memo files, call DHR-OP06/DHR-OP07, execute DMD/R52, start actual review,
start P8, make API/DB/RN/runtime/response-key changes, or make release claims.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
from typing import Any

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_20260709 as dhc
from test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_op06_op07_20260709 import (
    _op05_not_called,
    _op05_repair,
    _op05_scan_clear,
    _op05_waiting,
    _op06,
    _op07,
)

OP08_SCAN_CLEAR = dhc.P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[0]
OP08_WAITING = dhc.P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[1]
OP08_REPAIR = dhc.P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[2]
OP08_NOT_CALLED = dhc.P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[3]
OP08_NON_DHR = dhc.P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[4]
OP08_BLOCKED = dhc.P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[5]
OP05_SCAN_CLEAR = dhc.P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[0]
OP05_WAITING = dhc.P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[1]
OP05_REPAIR = dhc.P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[2]
OP05_NOT_CALLED = dhc.P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[3]


def _op07_from_op05(op05: dict[str, Any]) -> dict[str, Any]:
    return _op07(_op06(op05))


def _op08(
    op07: dict[str, Any] | None = None,
    op05: dict[str, Any] | None = None,
    *,
    non_dhr_lane_route_preserved: bool = False,
) -> dict[str, Any]:
    material = dhc.build_p7_r54_ahr_post_dhb_dhc_op08_result_memo_closure_stopped_next_work_candidate(
        op07,
        op05_existing_dhr_op05_result_classification=op05,
        non_dhr_lane_route_preserved=non_dhr_lane_route_preserved,
    )
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op08_result_memo_closure_stopped_next_work_candidate_contract(material) is True
    return material


def _assert_no_downstream_or_green_or_files(data: dict[str, Any]) -> None:
    for key in (
        "dhr_op06_call_allowed_here",
        "dhr_op06_called_here",
        "dhr_op07_materialized_here",
        "dmd_r52_execution_allowed_here",
        "dmd_execution_started_here",
        "dmd_r52_executed_here",
        "r52_actual_execution_started_here",
        "actual_review_started_here",
        "actual_rows_created_here",
        "question_need_observation_rows_created_here",
        "p8_start_allowed",
        "p8_question_design_started",
        "p8_question_implementation_started",
        "question_text_materialized_here",
        "api_changed",
        "db_changed",
        "rn_changed",
        "runtime_changed",
        "response_key_changed",
        "api_db_rn_runtime_response_key_changed",
        "json_schema_file_created_here",
        "p7_complete",
        "release_allowed",
        "validation_commands_executed_here",
        "target_validation_green_confirmed_here",
        "selected_regression_green_confirmed_here",
        "compileall_green_confirmed_here",
        "full_backend_suite_green_confirmed",
        "rn_contract_green_confirmed",
        "rn_real_device_modal_verified_claimed_here",
        "full_backend_suite_green_claimed_here",
        "rn_contract_green_claimed_here",
        "result_memo_files_created_here",
    ):
        assert data[key] is False, key


def _collect_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        keys = set(value)
        for child in value.values():
            keys.update(_collect_keys(child))
        return keys
    if isinstance(value, (list, tuple)):
        keys: set[str] = set()
        for child in value:
            keys.update(_collect_keys(child))
        return keys
    return set()


@pytest.mark.parametrize(
    ("builder", "expected_status", "expected_classification", "expected_candidate"),
    [
        (_op05_scan_clear, OP08_SCAN_CLEAR, OP05_SCAN_CLEAR, dhc.P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_SCAN_CLEAR_REF),
        (_op05_waiting, OP08_WAITING, OP05_WAITING, dhc.P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_WAITING_OR_INCOMPLETE_REF),
        (_op05_repair, OP08_REPAIR, OP05_REPAIR, dhc.P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_REPAIR_REQUIRED_REF),
        (_op05_not_called, OP08_NOT_CALLED, OP05_NOT_CALLED, dhc.P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_NOT_CALLED_REF),
    ],
)
def test_op08_closes_each_op05_result_classification_as_stopped_next_work_candidate(
    builder: Any,
    expected_status: str,
    expected_classification: str,
    expected_candidate: str,
) -> None:
    op05 = builder()
    op08 = _op08(_op07_from_op05(op05), op05)

    assert op08["dhc_op08_status_ref"] == expected_status
    assert op08["dhc_result_classification_ref"] == expected_classification
    assert op08["next_work_candidate_ref"] == expected_candidate
    assert op08["next_required_step"] == expected_candidate
    assert op08["bodyfree_result_memo_closure_status_ref"] == expected_status
    _assert_no_downstream_or_green_or_files(op08)


def test_op08_scan_clear_preserves_existing_dhr_op05_call_record_but_does_not_call_dhr_op06() -> None:
    op05 = _op05_scan_clear()
    op08 = _op08(_op07_from_op05(op05), op05)

    assert op08["dhr_op05_call_attempted"] is True
    assert op08["existing_dhr_op05_builder_called_here"] is True
    assert op08["existing_dhr_op05_result_present"] is True
    assert op08["existing_dhr_op05_contract_valid"] is True
    assert op08["dhr_op05_called_here"] is True
    assert op08["dhr_op05_builder_called_here"] is True
    assert op08["dhr_op06_call_allowed_here"] is False
    assert op08["dhr_op06_called_here"] is False
    assert op08["dhr_op07_materialized_here"] is False


def test_op08_waiting_repair_and_not_called_do_not_promote_to_p8_or_release() -> None:
    for op05 in (_op05_waiting(), _op05_repair(), _op05_not_called()):
        op08 = _op08(_op07_from_op05(op05), op05)
        assert op08["p8_question_design_started"] is False
        assert op08["p8_question_implementation_started"] is False
        assert op08["question_text_materialized_here"] is False
        assert op08["p7_complete"] is False
        assert op08["release_allowed"] is False


def test_op08_non_dhr_lane_route_preserved_closes_without_dhr_op05_call() -> None:
    op08 = _op08(non_dhr_lane_route_preserved=True)

    assert op08["dhc_op08_status_ref"] == OP08_NON_DHR
    assert op08["op08_non_dhr_lane_route_preserved"] is True
    assert op08["next_work_candidate_ref"] == dhc.P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_NON_DHR_LANE_REF
    assert op08["dhr_op05_called_here"] is False
    assert op08["existing_dhr_op05_builder_called_here"] is False
    _assert_no_downstream_or_green_or_files(op08)


def test_op08_missing_op07_material_is_not_called_closure_not_execution() -> None:
    op05 = _op05_scan_clear()
    op08 = _op08(None, op05)

    assert op08["dhc_op08_status_ref"] == OP08_NOT_CALLED
    assert op08["op07_material_present"] is False
    assert op08["op07_contract_valid"] is False
    assert op08["next_work_candidate_ref"] == dhc.P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_NOT_CALLED_REF
    _assert_no_downstream_or_green_or_files(op08)


def test_op08_can_close_from_valid_op07_material_without_requiring_repeated_op05_input() -> None:
    op05 = _op05_scan_clear()
    op07 = _op07_from_op05(op05)
    op08 = _op08(op07, None)

    assert op08["dhc_op08_status_ref"] == OP08_SCAN_CLEAR
    assert op08["op07_contract_valid"] is True
    assert op08["dhc_result_classification_ref"] == dhc.P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[0]
    assert op08["op08_explicit_classification_input_ref"] == dhc.P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[0]
    _assert_no_downstream_or_green_or_files(op08)


def test_op08_invalid_op05_classification_is_repair_closure() -> None:
    op05 = _op05_scan_clear()
    broken = deepcopy(op05)
    del broken["body_free"]
    op08 = _op08(_op07_from_op05(op05), broken)

    assert op08["dhc_op08_status_ref"] == OP08_REPAIR
    assert op08["op08_explicit_classification_input_ref"] == "dhc_result_classification_missing"


def test_op08_op07_repair_closes_as_repair_without_validation_or_downstream_execution() -> None:
    op07 = _op07(None)
    op08 = _op08(op07, _op05_scan_clear())

    assert op07["dhc_op07_repair_required_for_validation_plan_inputs"] is True
    assert op08["dhc_op08_status_ref"] == OP08_REPAIR
    assert op08["op07_repair_required"] is True
    _assert_no_downstream_or_green_or_files(op08)


def test_op08_op07_blocked_closes_as_blocked_without_carrying_downstream() -> None:
    op05 = _op05_scan_clear()
    poisoned = deepcopy(op05)
    poisoned["dhr_op06_called_here"] = True
    op07 = _op07(_op06(poisoned))
    op08 = _op08(op07, op05)

    assert op07["dhc_op07_blocked_validation_plan_bodyfree_leak_promotion_or_autorun"] is True
    assert op08["dhc_op08_status_ref"] == OP08_BLOCKED
    assert op08["dhc_op08_blocked_bodyfree_leak_promotion_or_autorun"] is True
    assert op08["dhc_op08_blocker_ref_count"] >= 1
    _assert_no_downstream_or_green_or_files(op08)


@pytest.mark.parametrize("payload_key", ["stdout", "stderr", "traceback", "comment_text", "question_text", "raw_input"])
def test_op08_blocks_raw_payload_keys_without_carrying_payload(payload_key: str) -> None:
    op05 = _op05_scan_clear()
    op07 = _op07_from_op05(op05)
    op07[payload_key] = "must_not_be_carried"
    op08 = _op08(op07, op05)

    assert op08["dhc_op08_status_ref"] == OP08_BLOCKED
    assert op08["op08_input_forbidden_payload_key_path_count"] >= 1
    assert payload_key not in op08
    _assert_no_downstream_or_green_or_files(op08)


@pytest.mark.parametrize(
    "promotion_flag",
    [
        "dhr_op06_called_here",
        "dhr_op07_materialized_here",
        "dmd_execution_started_here",
        "actual_review_started_here",
        "actual_rows_created_here",
        "question_need_observation_rows_created_here",
        "p8_question_design_started",
        "question_text_materialized_here",
        "api_db_rn_runtime_response_key_changed",
        "release_allowed",
        "target_validation_green_confirmed_here",
        "selected_regression_green_confirmed_here",
        "compileall_green_confirmed_here",
        "full_backend_suite_green_claimed_here",
        "rn_contract_green_claimed_here",
        "rn_real_device_modal_verified_claimed_here",
    ],
)
def test_op08_blocks_downstream_or_green_claims_in_inputs(promotion_flag: str) -> None:
    op05 = _op05_scan_clear()
    op07 = _op07_from_op05(op05)
    op07[promotion_flag] = True
    op08 = _op08(op07, op05)

    assert op08["dhc_op08_status_ref"] == OP08_BLOCKED
    assert op08["op08_input_downstream_promotion_claim_ref_count"] >= 1
    assert op08[promotion_flag] is False
    _assert_no_downstream_or_green_or_files(op08)


def test_op08_keeps_validation_and_result_memo_refs_as_count_only_material() -> None:
    op05 = _op05_scan_clear()
    op08 = _op08(_op07_from_op05(op05), op05)

    assert op08["target_validation_test_ref_refs"] == dhc.P7_R54_AHR_POST_DHB_DHC_R6_TARGET_TEST_REF_REFS
    assert op08["selected_regression_test_ref_refs"] == dhc.P7_R54_AHR_POST_DHB_DHC_R6_SELECTED_REGRESSION_TEST_REF_REFS
    assert op08["compileall_target_ref_refs"] == dhc.P7_R54_AHR_POST_DHB_DHC_R6_COMPILEALL_TARGET_REF_REFS
    assert op08["result_memo_expected_file_refs"] == dhc.P7_R54_AHR_POST_DHB_DHC_R6_RESULT_MEMO_EXPECTED_FILE_REFS
    assert op08["result_memo_expected_file_ref_count"] == len(dhc.P7_R54_AHR_POST_DHB_DHC_R6_RESULT_MEMO_EXPECTED_FILE_REFS)
    assert op08["result_memo_policy_count_only_bodyfree"] is True
    assert op08["result_memo_closure_is_not_validation_result"] is True
    assert op08["result_memo_files_created_here"] is False


def test_op08_allowed_status_refs_next_candidates_and_counts_are_stable() -> None:
    op05 = _op05_scan_clear()
    op08 = _op08(_op07_from_op05(op05), op05)

    assert op08["dhc_op08_allowed_status_refs"] == dhc.P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS
    assert op08["dhc_op08_allowed_status_ref_count"] == len(dhc.P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS)
    assert op08["next_work_candidate_refs"] == dhc.P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_CANDIDATE_REFS
    assert op08["next_work_candidate_ref_count"] == len(dhc.P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_CANDIDATE_REFS)
    for field, count_field in (
        ("op08_input_forbidden_payload_key_path_refs", "op08_input_forbidden_payload_key_path_count"),
        ("op08_input_body_like_value_path_refs", "op08_input_body_like_value_path_count"),
        ("op08_input_downstream_promotion_claim_refs", "op08_input_downstream_promotion_claim_ref_count"),
        ("op08_input_no_touch_mutation_path_refs", "op08_input_no_touch_mutation_path_count"),
        ("dhc_op08_reason_refs", "dhc_op08_reason_ref_count"),
        ("dhc_op08_blocker_refs", "dhc_op08_blocker_ref_count"),
    ):
        assert op08[count_field] == len(op08[field])


def test_op08_step_progression_has_no_not_yet_implemented_dhc_ops() -> None:
    op05 = _op05_scan_clear()
    op08 = _op08(_op07_from_op05(op05), op05)

    assert op08["implemented_steps"] == dhc.P7_R54_AHR_POST_DHB_DHC_OP08_IMPLEMENTED_STEPS
    assert op08["not_yet_implemented_steps"] == ()
    assert op08["dhc_op00_implemented"] is True
    assert op08["dhc_op07_implemented"] is True
    assert op08["dhc_op08_implemented"] is True


def test_op08_public_contract_no_touch_and_bodyfree_policy_are_stable() -> None:
    op05 = _op05_scan_clear()
    op08 = _op08(_op07_from_op05(op05), op05)

    assert op08["public_contract"] == dhc.public_contract_flags()
    assert all(value is False for value in op08["dhc_no_touch_contract"].values())
    assert op08["body_free_markers"]["body_free"] is True
    assert op08["body_free"] is True


def test_op08_does_not_include_raw_body_comment_text_question_text_or_traceback_keys() -> None:
    op05 = _op05_scan_clear()
    op08 = _op08(_op07_from_op05(op05), op05)
    forbidden = {"raw_input", "raw_answer", "raw_evidence", "body", "comment_text", "question_text", "stdout", "stderr", "traceback"}

    assert not (_collect_keys(op08) & forbidden)
    assert op08["dhc_op08_does_not_create_result_memo_files"] is True
    assert op08["dhc_op08_does_not_make_release_decision"] is True
