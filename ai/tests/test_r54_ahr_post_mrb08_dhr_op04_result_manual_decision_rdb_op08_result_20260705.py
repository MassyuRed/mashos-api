# -*- coding: utf-8 -*-
"""R54-AHR Post-MRB08 / DHR-OP04 result manual decision RDB-OP08 tests."""

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
    _op04_from_op05,
)


def _validation_summary() -> dict[str, object]:
    return {
        "summary_kind_ref": "rdb_op08_bodyfree_validation_summary",
        "target_test_result_status_ref": "passed",
        "selected_regression_result_status_ref": "passed",
        "compileall_result_status_ref": "passed",
        "combined_run_status_ref": "passed",
        "full_backend_suite_green_confirmed": False,
        "rn_contract_green_confirmed": False,
        "rn_real_device_modal_verified_claimed_here": False,
    }


def _result_memo() -> dict[str, object]:
    return {
        "memo_kind_ref": "rdb_op08_bodyfree_result_manual_decision_memo",
        "memo_status_ref": "closed_bodyfree_stopped",
        "next_stage_candidate_execution_ref": "not_executed_here",
    }


def _op08_from_op05(op05: dict[str, object]) -> dict[str, object]:
    return rdb.build_p7_r54_ahr_post_mrb08_rdb_op08_bodyfree_result_manual_decision_memo_closure(
        branch_specific_manual_decision_materialization=_op04_from_op05(op05),
        validation_summary_bodyfree=_validation_summary(),
        result_memo_bodyfree=_result_memo(),
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


@pytest.mark.parametrize(
    ("op05", "expected_status", "expected_candidate_ref"),
    [
        (
            _op05_confirmed(),
            rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_CONFIRMED_DHR_OP05_MANUAL_HANDOFF_CANDIDATE_STOPPED_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_PREPARE_DHR_OP05_MANUAL_HANDOFF_DECISION_REF,
        ),
        (
            _op05_not_confirmed(),
            rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_NOT_CONFIRMED_RETRY_OR_START_DECISION_REQUIRED_STOPPED_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_PREPARE_RETRY_OR_START_DECISION_REF,
        ),
        (
            _op05_waiting_result(),
            rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_WAITING_EXTERNAL_CLAIM_REQUIRED_STOPPED_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_WAIT_EXTERNAL_BODYFREE_CLAIM_REF,
        ),
        (
            _op05_invalid_result(),
            rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_REPAIR_REQUIRED_AFTER_DHR_OP04_RESULT_STOPPED_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_REPAIR_RESULT_OR_MRB08_REF,
        ),
    ],
)
def test_rdb_op08_closes_bodyfree_result_manual_decision_memo_for_all_result_lanes(
    op05: dict[str, object],
    expected_status: str,
    expected_candidate_ref: str,
) -> None:
    material = _op08_from_op05(op05)

    assert set(material) == set(rdb.P7_R54_AHR_POST_MRB08_RDB_OP08_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP08_SCHEMA_VERSION
    assert material["operation_step_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP08_STEP_REF
    assert material["rdb_op08_status_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP08_STATUS_CLOSED_BODYFREE_STOPPED_REF
    assert material["bodyfree_result_manual_decision_memo_closure_status_ref"] == material["rdb_op08_status_ref"]
    assert material["rdb_op08_closed_bodyfree_stopped"] is True
    assert material["rdb_op08_waiting_for_op03_op04_op05_or_validation_refs"] is False
    assert material["rdb_op08_repair_required_for_result_manual_decision_closure_inputs"] is False
    assert material["rdb_op08_blocked_bodyfree_result_memo_leak_promotion_or_autorun"] is False
    assert material["op04_contract_valid"] is True
    assert material["op05_contract_valid"] is True
    assert material["op07_contract_valid"] is True
    assert material["op07_ready_for_op08"] is True
    assert material["validation_summary_bodyfree_accepted"] is True
    assert material["result_memo_bodyfree_accepted"] is True
    assert material["rdb_selected_status_ref"] == expected_status
    assert material["manual_decision_material_present"] is True
    assert material["selected_next_stage_candidate_ref"] == expected_candidate_ref
    assert material["selected_next_stage_candidate_not_executed"] is True
    assert material["next_required_step"] == expected_candidate_ref
    assert material["dhr_op05_not_called"] is True
    assert material["dhr_op06_not_called"] is True
    assert material["dmd_r52_not_executed"] is True
    assert material["p5_p6_p8_p7_release_not_started"] is True
    assert material["p8_question_design_not_started"] is True
    assert material["p8_question_implementation_not_started"] is True
    assert material["target_test_result_status_ref"] == "passed"
    assert material["selected_regression_result_status_ref"] == "passed"
    assert material["compileall_result_status_ref"] == "passed"
    assert material["full_backend_suite_green_confirmed"] is False
    assert material["rn_contract_green_confirmed"] is False
    assert material["rn_real_device_modal_verified_claimed_here"] is False
    assert material["implemented_steps"] == list(rdb.P7_R54_AHR_POST_MRB08_RDB_OP08_IMPLEMENTED_STEPS)
    assert material["not_yet_implemented_steps"] == []
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op08_bodyfree_result_manual_decision_memo_closure_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rdb_op08_records_next_candidate_but_never_executes_or_promotes_downstream() -> None:
    material = _op08_from_op05(_op05_confirmed())

    assert material["selected_next_stage_candidate_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_PREPARE_DHR_OP05_MANUAL_HANDOFF_DECISION_REF
    assert material["selected_next_stage_candidate_not_executed"] is True
    assert material["dhr_op05_not_called"] is True
    assert material["dhr_op06_not_called"] is True
    assert material["dmd_r52_not_executed"] is True
    assert material["dhr_op05_called_here"] is False
    assert material["dhr_op06_called_here"] is False
    assert material["dmd_execution_started_here"] is False
    assert material["r52_actual_execution_started_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op08_bodyfree_result_manual_decision_memo_closure_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rdb_op08_waits_when_validation_or_result_memo_refs_are_missing() -> None:
    material = rdb.build_p7_r54_ahr_post_mrb08_rdb_op08_bodyfree_result_manual_decision_memo_closure(
        branch_specific_manual_decision_materialization=_op04_from_op05(_op05_confirmed()),
    )

    assert material["rdb_op08_status_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP08_STATUS_WAITING_FOR_INPUT_REFS_REF
    assert material["rdb_op08_waiting_for_op03_op04_op05_or_validation_refs"] is True
    assert "validation_summary_bodyfree_missing" in material["rdb_op08_blocker_refs"]
    assert "result_memo_bodyfree_missing" in material["rdb_op08_blocker_refs"]
    assert material["next_required_step"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP08_NEXT_STEP_WAIT_REF
    assert material["dhr_op05_not_called"] is True
    assert material["release_allowed"] is False
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op08_bodyfree_result_manual_decision_memo_closure_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rdb_op08_repairs_when_op07_is_not_ready_for_closure() -> None:
    op04 = _op04_from_op05(_op05_confirmed())
    op05 = rdb.build_p7_r54_ahr_post_mrb08_rdb_op05_next_stage_candidate_envelope_without_execution(
        branch_specific_manual_decision_materialization=op04,
    )
    guard = rdb.build_p7_r54_ahr_post_mrb08_rdb_op06_bodyfree_no_touch_no_promotion_guard(
        next_stage_candidate_envelope_without_execution=op05,
    )
    op07 = rdb.build_p7_r54_ahr_post_mrb08_rdb_op07_selected_regression_compileall_validation_plan(
        bodyfree_no_touch_no_promotion_guard=guard,
        changed_file_refs=[
            "services/ai_inference/emlis_ai_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_20260705.py",
            "api/routes/p8_question_schema.py",
        ],
    )

    material = rdb.build_p7_r54_ahr_post_mrb08_rdb_op08_bodyfree_result_manual_decision_memo_closure(
        selected_regression_compileall_validation_plan=op07,
        next_stage_candidate_envelope_without_execution=op05,
        branch_specific_manual_decision_materialization=op04,
        validation_summary_bodyfree=_validation_summary(),
        result_memo_bodyfree=_result_memo(),
    )

    assert material["rdb_op08_status_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP08_STATUS_REPAIR_REQUIRED_REF
    assert material["op07_contract_valid"] is True
    assert material["op07_ready_for_op08"] is False
    assert "rdb_op07_not_ready_for_op08" in material["rdb_op08_blocker_refs"]
    assert material["next_required_step"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP08_NEXT_STEP_REPAIR_REF
    assert material["full_backend_suite_green_confirmed"] is False
    assert material["rn_contract_green_confirmed"] is False
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op08_bodyfree_result_manual_decision_memo_closure_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rdb_op08_blocks_body_like_result_memo_or_question_text_without_copying_values() -> None:
    result_memo = _result_memo()
    result_memo["question_text"] = "must not be copied into OP08 closure"
    material = rdb.build_p7_r54_ahr_post_mrb08_rdb_op08_bodyfree_result_manual_decision_memo_closure(
        branch_specific_manual_decision_materialization=_op04_from_op05(_op05_confirmed()),
        validation_summary_bodyfree=_validation_summary(),
        result_memo_bodyfree=result_memo,
    )

    assert material["rdb_op08_status_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP08_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
    assert material["rdb_op08_blocked_bodyfree_result_memo_leak_promotion_or_autorun"] is True
    assert "rdb_op08.result_memo.question_text" in material["result_memo_forbidden_payload_key_path_refs"]
    assert "rdb_op08.result_memo.question_text" in material["result_memo_body_like_value_path_refs"]
    assert "must not be copied" not in repr(material)
    assert material["result_memo_bodyfree_ref"] == {}
    assert material["dhr_op05_not_called"] is True
    assert material["p8_question_design_started"] is False
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op08_bodyfree_result_manual_decision_memo_closure_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rdb_op08_contract_rejects_downstream_or_green_claim_mutations() -> None:
    material = _op08_from_op05(_op05_confirmed())
    material["dhr_op05_not_called"] = False
    with pytest.raises(ValueError):
        rdb.assert_p7_r54_ahr_post_mrb08_rdb_op08_bodyfree_result_manual_decision_memo_closure_contract(material)

    material = _op08_from_op05(_op05_confirmed())
    material["full_backend_suite_green_confirmed"] = True
    with pytest.raises(ValueError):
        rdb.assert_p7_r54_ahr_post_mrb08_rdb_op08_bodyfree_result_manual_decision_memo_closure_contract(material)

    material = _op08_from_op05(_op05_confirmed())
    material["selected_next_stage_candidate_not_executed"] = False
    with pytest.raises(ValueError):
        rdb.assert_p7_r54_ahr_post_mrb08_rdb_op08_bodyfree_result_manual_decision_memo_closure_contract(material)


def test_rdb_op08_full_title_aliases_match_short_builders_and_asserts() -> None:
    assert (
        rdb.build_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op08_bodyfree_result_manual_decision_memo_closure
        is rdb.build_p7_r54_ahr_post_mrb08_rdb_op08_bodyfree_result_manual_decision_memo_closure
    )
    assert (
        rdb.assert_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op08_bodyfree_result_manual_decision_memo_closure_contract
        is rdb.assert_p7_r54_ahr_post_mrb08_rdb_op08_bodyfree_result_manual_decision_memo_closure_contract
    )
