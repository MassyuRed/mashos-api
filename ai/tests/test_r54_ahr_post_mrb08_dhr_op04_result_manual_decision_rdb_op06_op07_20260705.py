# -*- coding: utf-8 -*-
"""R54-AHR Post-MRB08 / DHR-OP04 result manual decision RDB-OP06/OP07 tests."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_20260705 as rdb
from test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op06_op07_20260705 import (
    _op05_confirmed,
    _op05_invalid_result,
    _op05_not_confirmed,
    _op05_waiting_result,
)
from test_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op04_op05_20260705 import (
    _op05_from_op05,
)


def _assert_common_bodyfree_no_touch_no_promotion(material: dict[str, object]) -> None:
    assert material["source_mode"] == rdb.P7_R54_AHR_POST_MRB08_RDB_SOURCE_MODE
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True
    assert all(value is False for value in material["public_contract"].values())
    assert all(value is False for value in material["rdb_no_touch_contract"].values())
    assert all(value is False for value in material["body_free_markers"].values())
    assert all(value is False for value in material["not_claimed_boundary"].values())
    for key in rdb.P7_R54_AHR_POST_MRB08_RDB_REQUIRED_FALSE_FLAG_REFS:
        assert material[key] is False, key


def _op06_from_op05(op05: dict[str, object]) -> dict[str, object]:
    return rdb.build_p7_r54_ahr_post_mrb08_rdb_op06_bodyfree_no_touch_no_promotion_guard(
        next_stage_candidate_envelope_without_execution=_op05_from_op05(op05),
    )


def _op07_from_op05(op05: dict[str, object]) -> dict[str, object]:
    return rdb.build_p7_r54_ahr_post_mrb08_rdb_op07_selected_regression_compileall_validation_plan(
        bodyfree_no_touch_no_promotion_guard=_op06_from_op05(op05),
    )


@pytest.mark.parametrize(
    "op05",
    [
        _op05_confirmed(),
        _op05_not_confirmed(),
        _op05_waiting_result(),
        _op05_invalid_result(),
    ],
)
def test_rdb_op06_passes_bodyfree_no_touch_no_promotion_guard_for_all_candidate_lanes(op05: dict[str, object]) -> None:
    material = _op06_from_op05(op05)

    assert set(material) == set(rdb.P7_R54_AHR_POST_MRB08_RDB_OP06_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP06_SCHEMA_VERSION
    assert material["operation_step_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP06_STEP_REF
    assert material["op05_contract_valid"] is True
    assert material["rdb_op06_status_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP06_STATUS_PASSED_READY_FOR_OP07_REF
    assert material["bodyfree_no_touch_no_promotion_guard_status_ref"] == material["rdb_op06_status_ref"]
    assert material["rdb_op06_guard_checked"] is True
    assert material["body_free_guard_checked"] is True
    assert material["no_touch_guard_checked"] is True
    assert material["no_promotion_guard_checked"] is True
    assert material["no_auto_execution_guard_checked"] is True
    assert material["rdb_bodyfree_guard_passed"] is True
    assert material["rdb_no_touch_guard_passed"] is True
    assert material["rdb_no_promotion_guard_passed"] is True
    assert material["rdb_no_auto_execution_guard_passed"] is True
    assert material["rdb_public_contract_guard_passed"] is True
    assert material["rdb_candidate_not_executed_guard_passed"] is True
    assert material["rdb_op06_ready_for_rdb_op07"] is True
    assert material["rdb_op06_blocked_bodyfree_leak_promotion_or_autorun"] is False
    assert material["forbidden_payload_key_path_refs"] == []
    assert material["body_like_value_path_refs"] == []
    assert material["promotion_claim_refs"] == []
    assert material["op06_guard_blocker_refs"] == []
    assert material["selected_next_stage_candidate_not_executed"] is True
    assert material["downstream_auto_execution_allowed"] is False
    assert material["manual_decision_auto_executes_downstream"] is False
    assert material["p8_question_substitution_allowed"] is False
    assert material["question_text_materialized"] is False
    assert material["dhr_op05_called_here"] is False
    assert material["dhr_op06_called_here"] is False
    assert material["dmd_execution_started_here"] is False
    assert material["r52_actual_execution_started_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["implemented_steps"] == list(rdb.P7_R54_AHR_POST_MRB08_RDB_OP06_IMPLEMENTED_STEPS)
    assert material["not_yet_implemented_steps"] == list(rdb.P7_R54_AHR_POST_MRB08_RDB_OP06_NOT_YET_IMPLEMENTED_STEPS)
    assert material["next_required_step"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP07_STEP_REF
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op06_bodyfree_no_touch_no_promotion_guard_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rdb_op06_blocks_body_like_question_text_and_promotion_mutations_without_copying_values() -> None:
    envelope = _op05_from_op05(_op05_confirmed())
    envelope["question_text"] = "must not be copied into OP06 material"
    envelope["dhr_op05_builder_called_here"] = True

    material = rdb.build_p7_r54_ahr_post_mrb08_rdb_op06_bodyfree_no_touch_no_promotion_guard(
        next_stage_candidate_envelope_without_execution=envelope,
    )

    assert material["rdb_op06_status_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP06_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
    assert material["rdb_op06_ready_for_rdb_op07"] is False
    assert "op05.question_text" in material["forbidden_payload_key_path_refs"]
    assert "op05.question_text" in material["body_like_value_path_refs"]
    assert "op05.dhr_op05_builder_called_here" in material["promotion_claim_refs"]
    assert material["op06_guard_blocker_refs"]
    assert "must not be copied" not in repr(material)
    assert material["dhr_op05_called_here"] is False
    assert material["next_required_step"] == rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_BLOCKED_POST_MRB08_REF
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op06_bodyfree_no_touch_no_promotion_guard_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rdb_op06_repairs_when_op05_candidate_execution_flag_is_mutated() -> None:
    envelope = _op05_from_op05(_op05_confirmed())
    envelope["selected_next_stage_candidate_not_executed"] = False

    material = rdb.build_p7_r54_ahr_post_mrb08_rdb_op06_bodyfree_no_touch_no_promotion_guard(
        next_stage_candidate_envelope_without_execution=envelope,
    )

    assert material["rdb_op06_status_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP06_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
    assert material["rdb_candidate_not_executed_guard_passed"] is False
    assert "op05.selected_next_stage_candidate_not_executed" in material["op06_guard_blocker_refs"]
    assert material["next_required_step"] == rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_BLOCKED_POST_MRB08_REF
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op06_bodyfree_no_touch_no_promotion_guard_contract(material) is True


def test_rdb_op06_contract_rejects_guard_promotion_mutations() -> None:
    material = _op06_from_op05(_op05_confirmed())
    material["dhr_op05_called_here"] = True
    with pytest.raises(ValueError):
        rdb.assert_p7_r54_ahr_post_mrb08_rdb_op06_bodyfree_no_touch_no_promotion_guard_contract(material)

    material = _op06_from_op05(_op05_confirmed())
    material["rdb_op06_ready_for_rdb_op07"] = False
    with pytest.raises(ValueError):
        rdb.assert_p7_r54_ahr_post_mrb08_rdb_op06_bodyfree_no_touch_no_promotion_guard_contract(material)


@pytest.mark.parametrize(
    "op05",
    [
        _op05_confirmed(),
        _op05_not_confirmed(),
        _op05_waiting_result(),
        _op05_invalid_result(),
    ],
)
def test_rdb_op07_records_selected_regression_and_compileall_plan_without_claiming_full_backend_or_rn(op05: dict[str, object]) -> None:
    material = _op07_from_op05(op05)

    assert set(material) == set(rdb.P7_R54_AHR_POST_MRB08_RDB_OP07_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP07_SCHEMA_VERSION
    assert material["operation_step_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP07_STEP_REF
    assert material["op06_contract_valid"] is True
    assert material["op06_ready_for_rdb_op07"] is True
    assert material["op06_bodyfree_guard_passed"] is True
    assert material["op06_no_touch_guard_passed"] is True
    assert material["op06_no_promotion_guard_passed"] is True
    assert material["op06_no_auto_execution_guard_passed"] is True
    assert material["rdb_op07_status_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP07_STATUS_READY_FOR_OP08_REF
    assert material["selected_regression_compileall_validation_plan_status_ref"] == material["rdb_op07_status_ref"]
    assert material["target_test_refs"] == list(rdb.P7_R54_AHR_POST_MRB08_RDB_OP07_TARGET_TEST_REFS)
    assert "tests/test_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op06_op07_20260705.py" in material["target_test_refs"]
    assert material["selected_regression_refs"] == list(rdb.P7_R54_AHR_POST_MRB08_RDB_OP07_SELECTED_REGRESSION_REFS)
    assert material["compileall_refs"] == list(rdb.P7_R54_AHR_POST_MRB08_RDB_OP07_COMPILEALL_REFS)
    assert material["selected_regression_refs_recorded"] is True
    assert material["compileall_refs_recorded"] is True
    assert material["changed_files_within_allowed_refs"] is True
    assert material["api_db_rn_runtime_response_key_or_p8_question_touch_blocked"] is True
    assert material["api_db_rn_runtime_response_key_or_p8_question_touch_detected"] is False
    assert material["full_backend_suite_green_confirmed"] is False
    assert material["rn_contract_green_confirmed"] is False
    assert material["rn_real_device_modal_verified_claimed_here"] is False
    assert material["rdb_op07_does_not_run_target_tests_here"] is True
    assert material["rdb_op07_does_not_run_selected_regression_here"] is True
    assert material["rdb_op07_does_not_run_compileall_here"] is True
    assert material["rdb_op07_does_not_claim_full_backend_green"] is True
    assert material["rdb_op07_does_not_claim_rn_contract_green"] is True
    assert material["rdb_op07_does_not_start_dhr_op05"] is True
    assert material["rdb_op07_does_not_start_p8"] is True
    assert material["p8_question_substitution_allowed"] is False
    assert material["question_text_materialized"] is False
    assert material["next_required_step"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP08_STEP_REF
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op07_selected_regression_compileall_validation_plan_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rdb_op07_blocks_forbidden_changed_file_tokens_without_claiming_validation_green() -> None:
    guard = _op06_from_op05(_op05_confirmed())
    material = rdb.build_p7_r54_ahr_post_mrb08_rdb_op07_selected_regression_compileall_validation_plan(
        bodyfree_no_touch_no_promotion_guard=guard,
        changed_file_refs=[
            "services/ai_inference/emlis_ai_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_20260705.py",
            "api/routes/p8_question_schema.py",
        ],
    )

    assert material["rdb_op07_status_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP07_STATUS_BLOCKED_CHANGED_FILE_SCOPE_REF
    assert material["changed_files_within_allowed_refs"] is False
    assert material["api_db_rn_runtime_response_key_or_p8_question_touch_blocked"] is True
    assert material["forbidden_changed_file_token_refs"]
    assert material["disallowed_changed_file_refs"]
    assert any("p8_question" in ref for ref in material["forbidden_changed_file_token_refs"])
    assert material["full_backend_suite_green_confirmed"] is False
    assert material["rn_contract_green_confirmed"] is False
    assert material["rdb_op07_does_not_run_selected_regression_here"] is True
    assert material["rdb_op07_does_not_run_compileall_here"] is True
    assert material["next_required_step"] == rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_BLOCKED_POST_MRB08_REF
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op07_selected_regression_compileall_validation_plan_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rdb_op07_waits_when_op06_guard_is_not_ready() -> None:
    envelope = _op05_from_op05(_op05_confirmed())
    envelope["dhr_op05_builder_called_here"] = True
    guard = rdb.build_p7_r54_ahr_post_mrb08_rdb_op06_bodyfree_no_touch_no_promotion_guard(
        next_stage_candidate_envelope_without_execution=envelope,
    )
    material = rdb.build_p7_r54_ahr_post_mrb08_rdb_op07_selected_regression_compileall_validation_plan(
        bodyfree_no_touch_no_promotion_guard=guard,
    )

    assert material["rdb_op07_status_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP07_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
    assert material["op06_ready_for_rdb_op07"] is False
    assert material["op07_validation_blocker_refs"]
    assert material["next_required_step"] == rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_BLOCKED_POST_MRB08_REF
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op07_selected_regression_compileall_validation_plan_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rdb_op07_contract_rejects_green_or_boundary_claim_mutations() -> None:
    material = _op07_from_op05(_op05_confirmed())
    material["full_backend_suite_green_confirmed"] = True
    with pytest.raises(ValueError):
        rdb.assert_p7_r54_ahr_post_mrb08_rdb_op07_selected_regression_compileall_validation_plan_contract(material)

    material = _op07_from_op05(_op05_confirmed())
    material["rdb_op07_does_not_run_compileall_here"] = False
    with pytest.raises(ValueError):
        rdb.assert_p7_r54_ahr_post_mrb08_rdb_op07_selected_regression_compileall_validation_plan_contract(material)


def test_rdb_op06_op07_full_title_aliases_match_short_builders_and_asserts() -> None:
    assert (
        rdb.build_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op06_bodyfree_no_touch_no_promotion_guard
        is rdb.build_p7_r54_ahr_post_mrb08_rdb_op06_bodyfree_no_touch_no_promotion_guard
    )
    assert (
        rdb.assert_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op06_bodyfree_no_touch_no_promotion_guard_contract
        is rdb.assert_p7_r54_ahr_post_mrb08_rdb_op06_bodyfree_no_touch_no_promotion_guard_contract
    )
    assert (
        rdb.build_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op07_selected_regression_compileall_validation_plan
        is rdb.build_p7_r54_ahr_post_mrb08_rdb_op07_selected_regression_compileall_validation_plan
    )
    assert (
        rdb.assert_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op07_selected_regression_compileall_validation_plan_contract
        is rdb.assert_p7_r54_ahr_post_mrb08_rdb_op07_selected_regression_compileall_validation_plan_contract
    )
