# -*- coding: utf-8 -*-
"""DHC R5 OP06/OP07 target tests.

These tests cover only the no-touch / no-promotion / no-auto-downstream guard
and the count-only validation-plan/result-memo draft material. They must not
execute DHR-OP06, DHR-OP07, DMD/R52, actual review, P8, release, validation
commands, API/DB/RN/runtime/response-key changes, or json/schema file creation.
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
from test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_op04_op05_20260709 import (
    _build_op04,
    _classify,
    _op03_allowed,
    _op03_not_requested,
)
from test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op04_op05_20260704 import (
    _op04_confirmed_separation,
    _op04_not_confirmed_separation,
)

OP06_PASSED = dhc.P7_R54_AHR_POST_DHB_DHC_OP06_ALLOWED_STATUS_REFS[0]
OP06_REPAIR = dhc.P7_R54_AHR_POST_DHB_DHC_OP06_ALLOWED_STATUS_REFS[1]
OP06_BLOCKED = dhc.P7_R54_AHR_POST_DHB_DHC_OP06_ALLOWED_STATUS_REFS[2]
OP07_MATERIALIZED = dhc.P7_R54_AHR_POST_DHB_DHC_OP07_ALLOWED_STATUS_REFS[0]
OP07_REPAIR = dhc.P7_R54_AHR_POST_DHB_DHC_OP07_ALLOWED_STATUS_REFS[1]
OP07_BLOCKED = dhc.P7_R54_AHR_POST_DHB_DHC_OP07_ALLOWED_STATUS_REFS[2]
OP05_SCAN_CLEAR = dhc.P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[0]
OP05_WAITING = dhc.P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[1]
OP05_REPAIR = dhc.P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[2]
OP05_NOT_CALLED = dhc.P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[3]


def _op05_scan_clear() -> dict[str, Any]:
    op04_input = _op04_confirmed_separation()
    op04 = _build_op04(_op03_allowed(op04_input), op04_input)
    op05 = _classify(op04)
    assert op05["dhc_result_classification_ref"] == OP05_SCAN_CLEAR
    return op05


def _op05_waiting() -> dict[str, Any]:
    op04_input = _op04_not_confirmed_separation()
    op04 = _build_op04(_op03_allowed(op04_input), op04_input)
    op05 = _classify(op04)
    assert op05["dhc_result_classification_ref"] == OP05_WAITING
    return op05


def _op05_repair() -> dict[str, Any]:
    op04_input = _op04_confirmed_separation()
    broken_op04 = deepcopy(op04_input)
    broken_op04["dhr_op04_ready_for_bodyfree_leak_promotion_claim_preflight_scan"] = False
    op04 = _build_op04(_op03_allowed(op04_input), broken_op04)
    op05 = _classify(op04)
    assert op05["dhc_result_classification_ref"] == OP05_REPAIR
    return op05


def _op05_not_called() -> dict[str, Any]:
    op04_input = _op04_confirmed_separation()
    op04 = _build_op04(_op03_not_requested(op04_input), op04_input)
    op05 = _classify(op04)
    assert op05["dhc_result_classification_ref"] == OP05_NOT_CALLED
    return op05


def _op06(op05: dict[str, Any] | None = None) -> dict[str, Any]:
    material = dhc.build_p7_r54_ahr_post_dhb_dhc_op06_no_touch_no_promotion_no_auto_downstream_guard(op05)
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op06_no_touch_no_promotion_no_auto_downstream_guard_contract(material) is True
    return material


def _op07(op06: dict[str, Any] | None = None) -> dict[str, Any]:
    material = dhc.build_p7_r54_ahr_post_dhb_dhc_op07_validation_plan_result_memo_draft_material(op06)
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op07_validation_plan_result_memo_draft_material_contract(material) is True
    return material


def _assert_no_downstream(data: dict[str, Any]) -> None:
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
        "full_backend_suite_green_claimed_here",
        "rn_contract_green_claimed_here",
        "rn_real_device_modal_verified_claimed_here",
    ):
        assert data[key] is False, key


def _assert_no_validation_green(data: dict[str, Any]) -> None:
    for key in (
        "validation_commands_executed_here",
        "target_validation_green_confirmed_here",
        "selected_regression_green_confirmed_here",
        "compileall_green_confirmed_here",
        "full_backend_suite_green_confirmed",
        "rn_contract_green_confirmed",
        "rn_real_device_modal_verified_claimed_here",
        "full_backend_suite_green_claimed_here",
        "rn_contract_green_claimed_here",
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


def test_r5_keeps_r0_to_r4_present_and_valid() -> None:
    op05 = _op05_scan_clear()
    op06 = _op06(op05)
    op07 = _op07(op06)

    assert op06["dhc_op00_implemented"] is True
    assert op06["dhc_op05_implemented"] is True
    assert op06["dhc_op06_implemented"] is True
    assert op06["dhc_op07_implemented"] is False
    assert op07["dhc_op06_implemented"] is True
    assert op07["dhc_op07_implemented"] is True
    assert op07["dhc_op08_implemented"] is False


@pytest.mark.parametrize(
    "builder, expected_classification",
    [
        (_op05_scan_clear, OP05_SCAN_CLEAR),
        (_op05_waiting, OP05_WAITING),
        (_op05_repair, OP05_REPAIR),
        (_op05_not_called, OP05_NOT_CALLED),
    ],
)
def test_op06_passes_for_all_stopped_op05_classifications_without_downstream_promotion(
    builder: Any,
    expected_classification: str,
) -> None:
    op06 = _op06(builder())

    assert op06["dhc_op06_status_ref"] == OP06_PASSED
    assert op06["op05_classification_ref"] == expected_classification
    assert op06["dhc_op06_no_touch_no_promotion_no_auto_downstream_guard_passed"] is True
    assert op06["next_required_step"] == dhc.P7_R54_AHR_POST_DHB_DHC_OP07_STEP_REF
    _assert_no_downstream(op06)


def test_op06_scan_clear_keeps_existing_dhr_op05_call_record_but_does_not_call_dhr_op06() -> None:
    op06 = _op06(_op05_scan_clear())

    assert op06["existing_dhr_op05_builder_called_here"] is True
    assert op06["existing_dhr_op05_result_present"] is True
    assert op06["existing_dhr_op05_contract_valid"] is True
    assert op06["dhr_op05_called_here"] is True
    assert op06["dhr_op05_builder_called_here"] is True
    assert op06["dhr_op06_call_allowed_here"] is False
    assert op06["dhr_op06_called_here"] is False
    assert op06["dhr_op07_materialized_here"] is False


def test_op06_waiting_and_repair_do_not_start_p8_or_release() -> None:
    for op05 in (_op05_waiting(), _op05_repair()):
        op06 = _op06(op05)
        assert op06["dhc_op06_status_ref"] == OP06_PASSED
        assert op06["p8_question_design_started"] is False
        assert op06["p8_question_implementation_started"] is False
        assert op06["release_allowed"] is False
        assert op06["p7_complete"] is False


def test_op06_missing_op05_material_is_repair_not_execution() -> None:
    op06 = _op06(None)

    assert op06["dhc_op06_status_ref"] == OP06_REPAIR
    assert op06["op05_material_present"] is False
    assert op06["op05_contract_valid"] is False
    assert op06["next_required_step"] == dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_OP06_NO_TOUCH_GUARD_INPUTS_REF
    _assert_no_downstream(op06)


def test_op06_invalid_op05_material_is_repair_not_execution() -> None:
    op05 = _op05_scan_clear()
    del op05["body_free"]
    op06 = _op06(op05)

    assert op06["dhc_op06_status_ref"] == OP06_REPAIR
    assert op06["op05_material_present"] is True
    assert op06["op05_contract_valid"] is False
    _assert_no_downstream(op06)


@pytest.mark.parametrize(
    "flag",
    [
        "dhr_op06_called_here",
        "dhr_op07_materialized_here",
        "dmd_execution_started_here",
        "dmd_r52_executed_here",
        "actual_review_started_here",
        "actual_rows_created_here",
        "question_need_observation_rows_created_here",
        "p8_question_design_started",
        "question_text_materialized_here",
        "api_db_rn_runtime_response_key_changed",
        "release_allowed",
        "full_backend_suite_green_claimed_here",
    ],
)
def test_op06_blocks_any_downstream_or_green_claim_in_op05_input(flag: str) -> None:
    op05 = _op05_scan_clear()
    op05[flag] = True
    op06 = _op06(op05)

    assert op06["dhc_op06_status_ref"] == OP06_BLOCKED
    assert op06["dhc_op06_blocked_no_touch_no_promotion_no_auto_downstream_guard"] is True
    assert op06["op06_input_downstream_promotion_claim_ref_count"] >= 1
    assert op06["next_required_step"] == dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_BLOCKED_OP06_NO_TOUCH_NO_PROMOTION_GUARD_REF
    _assert_no_downstream(op06)


@pytest.mark.parametrize("payload_key", ["stdout", "stderr", "traceback", "comment_text", "question_text", "raw_input"])
def test_op06_blocks_raw_or_body_payload_keys_without_carrying_payload(payload_key: str) -> None:
    op05 = _op05_scan_clear()
    op05[payload_key] = "must_not_be_carried"
    op06 = _op06(op05)

    assert op06["dhc_op06_status_ref"] == OP06_BLOCKED
    assert op06["op06_input_forbidden_payload_key_path_count"] >= 1
    assert payload_key not in op06
    _assert_no_downstream(op06)


def test_op06_count_fields_and_public_contract_are_stable() -> None:
    op06 = _op06(_op05_scan_clear())

    for field, count_field in (
        ("op06_input_forbidden_payload_key_path_refs", "op06_input_forbidden_payload_key_path_count"),
        ("op06_input_body_like_value_path_refs", "op06_input_body_like_value_path_count"),
        ("op06_input_downstream_promotion_claim_refs", "op06_input_downstream_promotion_claim_ref_count"),
        ("op06_input_no_touch_mutation_path_refs", "op06_input_no_touch_mutation_path_count"),
        ("dhc_op06_reason_refs", "dhc_op06_reason_ref_count"),
        ("dhc_op06_blocker_refs", "dhc_op06_blocker_ref_count"),
    ):
        assert op06[count_field] == len(op06[field])
    assert op06["public_contract"] == dhc.public_contract_flags()
    assert all(value is False for value in op06["dhc_no_touch_contract"].values())


def test_op07_materializes_count_only_validation_plan_after_op06_passed() -> None:
    op07 = _op07(_op06(_op05_scan_clear()))

    assert op07["dhc_op07_status_ref"] == OP07_MATERIALIZED
    assert op07["dhc_op07_validation_plan_result_memo_draft_materialized_stopped"] is True
    assert op07["validation_plan_is_not_validation_result"] is True
    assert op07["validation_plan_does_not_claim_green"] is True
    assert op07["next_required_step"] == dhc.P7_R54_AHR_POST_DHB_DHC_OP08_STEP_REF
    _assert_no_validation_green(op07)
    _assert_no_downstream(op07)


def test_op07_keeps_validation_commands_as_refs_only() -> None:
    op07 = _op07(_op06(_op05_scan_clear()))

    assert op07["target_validation_command_ref_count"] == 1
    assert op07["selected_regression_command_ref_count"] == 1
    assert op07["compileall_command_ref_count"] == 1
    assert op07["validation_commands_executed_here"] is False
    assert op07["target_validation_test_ref_refs"] == dhc.P7_R54_AHR_POST_DHB_DHC_R5_TARGET_TEST_REF_REFS
    assert op07["selected_regression_test_ref_refs"] == dhc.P7_R54_AHR_POST_DHB_DHC_R5_SELECTED_REGRESSION_TEST_REF_REFS
    assert op07["compileall_target_ref_refs"] == dhc.P7_R54_AHR_POST_DHB_DHC_R5_COMPILEALL_TARGET_REF_REFS


def test_op07_result_memo_refs_are_expected_count_only_files() -> None:
    op07 = _op07(_op06(_op05_scan_clear()))

    assert op07["result_memo_expected_file_refs"] == dhc.P7_R54_AHR_POST_DHB_DHC_R5_RESULT_MEMO_EXPECTED_FILE_REFS
    assert op07["result_memo_expected_file_ref_count"] == len(dhc.P7_R54_AHR_POST_DHB_DHC_R5_RESULT_MEMO_EXPECTED_FILE_REFS)
    assert all(ref.endswith(".md") for ref in op07["result_memo_expected_file_refs"])
    assert op07["result_memo_policy_count_only_bodyfree"] is True


def test_op07_missing_op06_material_is_repair_not_validation_execution() -> None:
    op07 = _op07(None)

    assert op07["dhc_op07_status_ref"] == OP07_REPAIR
    assert op07["op06_material_present"] is False
    assert op07["op06_contract_valid"] is False
    assert op07["validation_commands_executed_here"] is False
    _assert_no_validation_green(op07)
    _assert_no_downstream(op07)


def test_op07_repair_op06_material_stays_repair() -> None:
    op06 = _op06(None)
    op07 = _op07(op06)

    assert op06["dhc_op06_status_ref"] == OP06_REPAIR
    assert op07["dhc_op07_status_ref"] == OP07_REPAIR
    assert op07["op06_repair_required"] is True
    assert op07["next_required_step"] == dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_OP07_VALIDATION_PLAN_INPUTS_REF
    _assert_no_validation_green(op07)


def test_op07_blocked_op06_material_stays_blocked() -> None:
    op05 = _op05_scan_clear()
    op05["dhr_op06_called_here"] = True
    op06 = _op06(op05)
    op07 = _op07(op06)

    assert op06["dhc_op06_status_ref"] == OP06_BLOCKED
    assert op07["dhc_op07_status_ref"] == OP07_BLOCKED
    assert op07["op06_blocked"] is True
    assert op07["dhc_op07_blocker_ref_count"] >= 1
    _assert_no_validation_green(op07)
    _assert_no_downstream(op07)


@pytest.mark.parametrize("payload_key", ["stdout", "stderr", "traceback", "comment_text", "question_text"])
def test_op07_blocks_raw_output_payload_keys_without_carrying_payload(payload_key: str) -> None:
    op06 = _op06(_op05_scan_clear())
    op06[payload_key] = "must_not_be_carried"
    op07 = _op07(op06)

    assert op07["dhc_op07_status_ref"] == OP07_BLOCKED
    assert op07["op07_input_forbidden_payload_key_path_count"] >= 1
    assert payload_key not in op07
    _assert_no_validation_green(op07)
    _assert_no_downstream(op07)


@pytest.mark.parametrize(
    "green_flag",
    [
        "target_validation_green_confirmed_here",
        "selected_regression_green_confirmed_here",
        "compileall_green_confirmed_here",
        "full_backend_suite_green_claimed_here",
        "rn_contract_green_claimed_here",
        "rn_real_device_modal_verified_claimed_here",
    ],
)
def test_op07_blocks_validation_green_claims_in_input(green_flag: str) -> None:
    op06 = _op06(_op05_scan_clear())
    op06[green_flag] = True
    op07 = _op07(op06)

    assert op07["dhc_op07_status_ref"] == OP07_BLOCKED
    assert op07["op07_input_downstream_promotion_claim_ref_count"] >= 1
    assert op07[green_flag] is False
    _assert_no_validation_green(op07)
    _assert_no_downstream(op07)


def test_op07_preserves_upstream_dhr_op05_call_but_not_downstream_execution() -> None:
    op07 = _op07(_op06(_op05_scan_clear()))

    assert op07["op06_upstream_existing_dhr_op05_builder_called_here"] is True
    assert op07["existing_dhr_op05_builder_called_here"] is True
    assert op07["existing_dhr_op05_result_present"] is True
    assert op07["dhr_op05_called_here"] is True
    assert op07["dhr_op06_called_here"] is False
    assert op07["dhr_op07_materialized_here"] is False


def test_op06_op07_do_not_include_raw_body_comment_text_question_text_or_traceback_keys() -> None:
    op06 = _op06(_op05_scan_clear())
    op07 = _op07(op06)
    forbidden = {"raw_input", "raw_answer", "raw_evidence", "body", "comment_text", "question_text", "stdout", "stderr", "traceback"}

    assert not (_collect_keys(op06) & forbidden)
    assert not (_collect_keys(op07) & forbidden)
    assert op07["raw_pytest_stdout_included"] is False
    assert op07["raw_pytest_stderr_included"] is False
    assert op07["raw_traceback_included"] is False


def test_op06_and_op07_allowed_status_refs_and_counts_are_stable() -> None:
    op06 = _op06(_op05_scan_clear())
    op07 = _op07(op06)

    assert op06["dhc_op06_allowed_status_refs"] == dhc.P7_R54_AHR_POST_DHB_DHC_OP06_ALLOWED_STATUS_REFS
    assert op06["dhc_op06_allowed_status_ref_count"] == len(dhc.P7_R54_AHR_POST_DHB_DHC_OP06_ALLOWED_STATUS_REFS)
    assert op07["dhc_op07_allowed_status_refs"] == dhc.P7_R54_AHR_POST_DHB_DHC_OP07_ALLOWED_STATUS_REFS
    assert op07["dhc_op07_allowed_status_ref_count"] == len(dhc.P7_R54_AHR_POST_DHB_DHC_OP07_ALLOWED_STATUS_REFS)


def test_op06_and_op07_step_progression_stops_before_op08() -> None:
    op06 = _op06(_op05_scan_clear())
    op07 = _op07(op06)

    assert op06["implemented_steps"] == dhc.P7_R54_AHR_POST_DHB_DHC_OP06_IMPLEMENTED_STEPS
    assert op06["not_yet_implemented_steps"] == dhc.P7_R54_AHR_POST_DHB_DHC_OP06_NOT_YET_IMPLEMENTED_STEPS
    assert op07["implemented_steps"] == dhc.P7_R54_AHR_POST_DHB_DHC_OP07_IMPLEMENTED_STEPS
    assert op07["not_yet_implemented_steps"] == dhc.P7_R54_AHR_POST_DHB_DHC_OP07_NOT_YET_IMPLEMENTED_STEPS
    assert op07["dhc_op08_implemented"] is False


def test_op07_public_contract_and_no_touch_contract_are_stable() -> None:
    op07 = _op07(_op06(_op05_scan_clear()))

    assert op07["public_contract"] == dhc.public_contract_flags()
    assert all(value is False for value in op07["dhc_no_touch_contract"].values())
    for key in ("api_changed", "db_changed", "rn_changed", "runtime_changed", "response_key_changed", "api_db_rn_runtime_response_key_changed"):
        assert op07[key] is False
