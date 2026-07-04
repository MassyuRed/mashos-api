# -*- coding: utf-8 -*-
"""R54-AHR Post-DMD08 actual local review operation ALR-OP12 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_20260703 as alr
from test_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op02_op03_20260703 import (
    _assert_common_bodyfree_no_touch_no_promotion,
)
from test_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op10_op11_20260703 import (
    _complete_disposal_purge_receipt,
    _op09_complete,
    _op10,
    _op11,
)


def _target_pass_statuses() -> dict[str, str]:
    return {key: alr.P7_R54_AHR_POST_DMD08_ALR_OP12_PASS_STATUS_REF for key in alr.P7_R54_AHR_POST_DMD08_ALR_OP12_TARGET_TEST_GROUP_REFS}


def _target_pass_counts() -> dict[str, int]:
    return {key: 1 for key in alr.P7_R54_AHR_POST_DMD08_ALR_OP12_TARGET_TEST_GROUP_REFS}


def _regression_pass_statuses() -> dict[str, str]:
    return {key: alr.P7_R54_AHR_POST_DMD08_ALR_OP12_PASS_STATUS_REF for key in alr.P7_R54_AHR_POST_DMD08_ALR_OP12_SELECTED_REGRESSION_GROUP_REFS}


def _regression_pass_counts() -> dict[str, int]:
    return {key: 1 for key in alr.P7_R54_AHR_POST_DMD08_ALR_OP12_SELECTED_REGRESSION_GROUP_REFS}


def _closed_validation_kwargs() -> dict[str, object]:
    return {
        "target_test_result_status_refs": _target_pass_statuses(),
        "target_test_result_count_refs": _target_pass_counts(),
        "selected_regression_result_status_refs": _regression_pass_statuses(),
        "selected_regression_result_count_refs": _regression_pass_counts(),
        "compileall_result_status_ref": alr.P7_R54_AHR_POST_DMD08_ALR_OP12_PASS_STATUS_REF,
        "compileall_result_count_ref": "passed",
    }


def _op12(op11: dict[str, object] | None = None, **overrides: object) -> dict[str, object]:
    kwargs = dict(overrides)
    if op11 is not None:
        kwargs["alr_op11_downstream_non_promotion_manual_decision_hold_finalizer"] = op11
    return alr.build_p7_r54_ahr_post_dmd08_alr_op12_result_memo_target_tests_selected_regression_closure(**kwargs)


def _assert_op12_does_not_execute_or_promote(material: dict[str, object]) -> None:
    for key in (
        "alr_op12_helper_does_not_run_pytest_or_compileall",
        "alr_op12_does_not_generate_body_full_packet",
        "alr_op12_does_not_run_actual_local_human_review",
        "alr_op12_does_not_create_receipts_rows_or_disposal",
        "alr_op12_does_not_execute_postcr22_ex_reentry_or_r52",
        "alr_op12_does_not_start_p5_p6_p8_p7_or_release",
        "alr_op12_does_not_change_api_db_rn_runtime_response_key",
    ):
        assert material[key] is True, key
    for key in (
        "manual_decision_auto_executes_downstream",
        "p5_final_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "r52_actual_execution_started_here",
        "p7_complete",
        "release_allowed",
        "full_backend_suite_green_claimed_here",
        "rn_contract_green_claimed_here",
        "rn_real_device_modal_verified_claimed_here",
    ):
        assert material[key] is False, key


def test_alr_op12_default_current_path_records_unverified_result_memo_without_closing_or_promoting() -> None:
    material = _op12()

    assert set(material) == set(alr.P7_R54_AHR_POST_DMD08_ALR_OP12_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP12_SCHEMA_VERSION
    assert material["operation_step_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP12_STEP_REF
    assert material["alr_op12_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP12_STATUS_INCOMPLETE_OR_UNVERIFIED_REF
    assert material["result_memo_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP12_RESULT_MEMO_REF
    assert material["result_memo_bodyfree_closed"] is False
    assert material["alr_op12_ready"] is False
    assert material["target_tests_closed"] is False
    assert material["selected_regression_closed"] is False
    assert material["compileall_closed"] is False
    assert material["selected_action_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED_REF
    assert material["retry_or_start_required"] is True
    assert material["actual_local_review_operation_must_continue_or_retry"] is True
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_RETRY_OR_START_REVIEW_WITH_ALLOW_REF
    assert tuple(material["implemented_steps"]) == alr.P7_R54_AHR_POST_DMD08_ALR_OP12_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ()
    assert material["next_implementation_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP12_NEXT_IMPLEMENTATION_STEP_REF
    _assert_op12_does_not_execute_or_promote(material)
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op12_result_memo_target_tests_selected_regression_closure_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op12_closes_bodyfree_result_memo_when_external_validation_summaries_are_supplied() -> None:
    material = _op12(**_closed_validation_kwargs())

    assert material["alr_op12_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP12_STATUS_CLOSED_REF
    assert material["alr_op12_ready"] is True
    assert material["result_memo_bodyfree_closed"] is True
    assert material["target_tests_closed_by_external_status_summary"] is True
    assert material["selected_regression_closed_by_external_status_summary"] is True
    assert material["compileall_closed_by_external_status_summary"] is True
    assert material["target_tests"]["target_tests_closed"] is True
    assert material["selected_regression"]["selected_regression_closed"] is True
    assert material["compileall"]["compileall_closed"] is True
    assert tuple(material["target_test_group_refs"]) == alr.P7_R54_AHR_POST_DMD08_ALR_OP12_TARGET_TEST_GROUP_REFS
    assert tuple(material["selected_regression_group_refs"]) == alr.P7_R54_AHR_POST_DMD08_ALR_OP12_SELECTED_REGRESSION_GROUP_REFS
    assert material["selected_action_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED_REF
    _assert_op12_does_not_execute_or_promote(material)
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op12_result_memo_target_tests_selected_regression_closure_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op12_partial_external_validation_keeps_result_memo_unclosed() -> None:
    statuses = _target_pass_statuses()
    statuses["alr_op12_target"] = "not_run_by_helper"
    material = _op12(
        target_test_result_status_refs=statuses,
        target_test_result_count_refs=_target_pass_counts(),
        selected_regression_result_status_refs=_regression_pass_statuses(),
        selected_regression_result_count_refs=_regression_pass_counts(),
        compileall_result_status_ref=alr.P7_R54_AHR_POST_DMD08_ALR_OP12_PASS_STATUS_REF,
        compileall_result_count_ref="passed",
    )

    assert material["alr_op12_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP12_STATUS_INCOMPLETE_OR_UNVERIFIED_REF
    assert material["target_tests_closed"] is False
    assert material["selected_regression_closed"] is True
    assert material["compileall_closed"] is True
    assert material["result_memo_bodyfree_closed"] is False
    assert material["selected_action_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED_REF
    assert "alr_op12_external_validation_status_not_closed" in material["branch_blocker_refs"]
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op12_result_memo_target_tests_selected_regression_closure_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op12_complete_receipt_candidate_closes_to_manual_decision_hold_without_auto_execution() -> None:
    op10 = _op10(_op09_complete(), receipt=_complete_disposal_purge_receipt())
    op11 = _op11(op10)
    material = _op12(op11, **_closed_validation_kwargs())

    assert material["alr_op12_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP12_STATUS_CLOSED_REF
    assert material["selected_action_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_ACTION_COMPLETE_RECEIPT_DOWNSTREAM_MANUAL_DECISION_REQUIRED_REF
    assert material["complete_receipt_manual_decision_required"] is True
    assert material["downstream_manual_decision_required"] is True
    assert material["complete_receipt_branch_requires_manual_decision"] is True
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_DOWNSTREAM_MANUAL_DECISION_NO_AUTO_EXEC_REF
    assert material["manual_decision_auto_executes_downstream"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    _assert_op12_does_not_execute_or_promote(material)
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op12_result_memo_target_tests_selected_regression_closure_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op12_repair_branch_can_be_recorded_bodyfree_without_running_actual_review() -> None:
    op10 = _op10(_op09_complete(), receipt=_complete_disposal_purge_receipt(raw_input="body-value-must-not-survive"))
    op11 = _op11(op10)
    material = _op12(op11, **_closed_validation_kwargs())

    assert material["alr_op12_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP12_STATUS_CLOSED_REF
    assert material["selected_action_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_ACTION_REPAIR_STOP_REQUIRED_REF
    assert material["repair_stop_required"] is True
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF
    assert "body-value-must-not-survive" not in repr(material)
    _assert_op12_does_not_execute_or_promote(material)
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op12_result_memo_target_tests_selected_regression_closure_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op12_invalid_op11_material_becomes_repair_required_without_closing_result_memo() -> None:
    op11 = deepcopy(_op11())
    op11["p8_start_allowed"] = True
    material = _op12(op11, **_closed_validation_kwargs())

    assert material["alr_op12_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP12_STATUS_REPAIR_REQUIRED_REF
    assert material["alr_op12_ready"] is False
    assert material["result_memo_bodyfree_closed"] is False
    assert material["selected_action_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_ACTION_REPAIR_STOP_REQUIRED_REF
    assert material["repair_stop_required"] is True
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF
    assert "alr_op12_op11_downstream_hold_material_missing_or_invalid" in material["branch_blocker_refs"]
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op12_result_memo_target_tests_selected_regression_closure_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op12_contract_rejects_closed_result_without_validation_summaries() -> None:
    material = _op12()
    material["alr_op12_status_ref"] = alr.P7_R54_AHR_POST_DMD08_ALR_OP12_STATUS_CLOSED_REF
    material["alr_op12_ready"] = True
    material["result_memo_bodyfree_closed"] = True

    with pytest.raises(ValueError):
        alr.assert_p7_r54_ahr_post_dmd08_alr_op12_result_memo_target_tests_selected_regression_closure_contract(material)


def test_alr_op12_contract_rejects_not_executed_boundary_opening() -> None:
    material = _op12(**_closed_validation_kwargs())
    material["not_executed_boundary"]["actual_local_human_review_execution"] = True

    with pytest.raises(ValueError):
        alr.assert_p7_r54_ahr_post_dmd08_alr_op12_result_memo_target_tests_selected_regression_closure_contract(material)


def test_alr_op12_aliases_match_full_design_title_names() -> None:
    material = alr.build_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op12_result_memo_target_tests_selected_regression_closure(
        **_closed_validation_kwargs()
    )

    assert alr.assert_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op12_result_memo_target_tests_selected_regression_closure_contract(material) is True
    assert material["operation_step_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP12_STEP_REF
    assert material["alr_op12_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP12_STATUS_CLOSED_REF
    assert material["selected_action_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED_REF


def test_alr_op12_result_memo_exists_and_remains_bodyfree() -> None:
    memo = TEST_DIR / alr.P7_R54_AHR_POST_DMD08_ALR_OP12_RESULT_MEMO_REF
    text = memo.read_text(encoding="utf-8")

    assert "ALR-OP12" in text
    assert "ALR-OP00〜OP12 target" in text
    assert "actual_local_human_review_execution: false" in text
    assert "actual_body_full_packet_generation: false" in text
    assert "release_allowed: false" in text
    assert "body-value-must-not-survive" not in text
    assert "raw input body" not in text.lower()
