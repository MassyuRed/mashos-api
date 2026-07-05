# -*- coding: utf-8 -*-
"""R54-AHR Post-ELR19 DHR-OP08/OP09 handoff plan and result memo tests."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704 as dhr
from test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op04_op05_20260704 import (
    _assert_bodyfree_no_touch_no_promotion,
    _op03_shape_valid_extraction,
)
from test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op06_op07_20260704 import (
    _op06_handoff_ready_branch,
    _op06_retry_or_start_branch,
)


def _op07_retry_manual_decision() -> dict[str, object]:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op07_manual_decision_materialization(
        handoff_or_retry_deterministic_branch_resolver=_op06_retry_or_start_branch(),
    )
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op07_manual_decision_materialization_contract(material)
    assert material["selected_branch_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_BRANCH_RETRY_OR_START_REQUIRED_BEFORE_DOWNSTREAM_HANDOFF_REF
    return material


def _op07_handoff_manual_decision() -> dict[str, object]:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op07_manual_decision_materialization(
        handoff_or_retry_deterministic_branch_resolver=_op06_handoff_ready_branch(),
    )
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op07_manual_decision_materialization_contract(material)
    assert material["selected_branch_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_BRANCH_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED_NO_AUTO_EXECUTION_REF
    return material


def _op08_retry_not_materialized() -> dict[str, object]:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op08_dmd_handoff_plan_candidate_materialization_without_execution(
        manual_decision_materialization=_op07_retry_manual_decision(),
        elr_op17_dmd_compatible_receipt_candidate_extraction=_op03_shape_valid_extraction(),
    )
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op08_dmd_handoff_plan_candidate_materialization_without_execution_contract(material)
    return material


def _op08_handoff_materialized() -> dict[str, object]:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op08_dmd_handoff_plan_candidate_materialization_without_execution(
        manual_decision_materialization=_op07_handoff_manual_decision(),
        elr_op17_dmd_compatible_receipt_candidate_extraction=_op03_shape_valid_extraction(),
    )
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op08_dmd_handoff_plan_candidate_materialization_without_execution_contract(material)
    return material


def _passed_summary(passed_count: int) -> dict[str, object]:
    return {
        "status_ref": "passed",
        "passed_count": passed_count,
        "failed_count": 0,
        "timed_out": False,
        "body_free": True,
    }


def test_dhr_op08_does_not_materialize_dmd_plan_for_current_retry_default() -> None:
    material = _op08_retry_not_materialized()

    assert set(material) == set(dhr.P7_R54_AHR_POST_ELR19_DHR_OP08_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP08_SCHEMA_VERSION
    assert material["operation_step_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP08_STEP_REF
    assert material["dhr_op08_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP08_STATUS_NOT_MATERIALIZED_BRANCH_NOT_READY_REF
    assert material["selected_branch_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_BRANCH_RETRY_OR_START_REQUIRED_BEFORE_DOWNSTREAM_HANDOFF_REF
    assert material["dmd_handoff_plan_materialized"] is False
    assert material["actual_operation_evidence_receipt_bodyfree"] == {}
    assert material["actual_operation_evidence_receipt_bodyfree_present"] is False
    assert material["actual_source_claim_confirmed_for_downstream_handoff"] is False
    assert material["dhr_op08_reason_refs"] == ["dhr_op08_selected_branch_is_not_dmd_handoff_ready"]
    assert material["dmd_execution_started_here"] is False
    assert material["dmd_auto_execution_allowed"] is False
    assert material["dmh_op18_finalizer_fake_generation_allowed"] is False
    assert material["dmd_direct_call_safe_without_adapter"] is False
    assert material["next_required_step"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP09_STEP_REF
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dhr_op08_materializes_handoff_plan_only_for_handoff_ready_branch_without_dmd_execution() -> None:
    material = _op08_handoff_materialized()

    assert material["dhr_op08_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP08_STATUS_MATERIALIZED_BODYFREE_NO_EXECUTION_REF
    assert material["selected_branch_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_BRANCH_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED_NO_AUTO_EXECUTION_REF
    assert material["dmd_handoff_plan_materialized"] is True
    assert material["dmd_handoff_ready_manual_decision_required"] is True
    assert material["actual_operation_evidence_receipt_bodyfree_present"] is True
    assert material["actual_source_claim_confirmed_for_downstream_handoff"] is True
    assert material["receipt_schema_version_matches_dmd"] is True
    assert material["receipt_source_kind_valid"] is True
    assert material["receipt_count_fields_are_24"] is True
    assert material["receipt_required_true_fields_passed"] is True
    assert material["receipt_body_free"] is True
    assert material["receipt_forbidden_payload_key_path_refs"] == []
    assert material["receipt_body_like_value_path_refs"] == []
    assert material["receipt_promotion_claim_refs"] == []
    assert material["dmd_execution_started_here"] is False
    assert material["dmd_auto_execution_allowed"] is False
    assert material["dmd_direct_call_safe_without_adapter"] is False
    assert material["dmh_op18_finalizer_fake_generation_allowed"] is False
    assert material["manual_operator_must_confirm_dmd_handoff"] is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dhr_op08_repairs_handoff_branch_when_safe_receipt_is_missing_or_body_leaking_without_leaking_value() -> None:
    op03 = _op03_shape_valid_extraction()
    receipt = dict(op03["dmd_compatible_actual_operation_evidence_receipt_bodyfree"])
    receipt["question_text"] = "must not leak into op08 result"
    op03["dmd_compatible_actual_operation_evidence_receipt_bodyfree"] = receipt
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op08_dmd_handoff_plan_candidate_materialization_without_execution(
        manual_decision_materialization=_op07_handoff_manual_decision(),
        elr_op17_dmd_compatible_receipt_candidate_extraction=op03,
    )

    assert material["dhr_op08_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP08_STATUS_REPAIR_REQUIRED_REF
    assert material["dhr_op08_ready"] is False
    assert material["dmd_handoff_plan_materialized"] is False
    assert material["actual_operation_evidence_receipt_bodyfree"] == {}
    assert material["receipt_forbidden_payload_key_path_count"] > 0
    assert material["receipt_body_like_value_path_count"] > 0
    assert "dhr_op08_handoff_ready_branch_missing_or_invalid_safe_bodyfree_receipt_candidate" in material["dhr_op08_blocker_refs"]
    assert "must not leak into op08 result" not in repr(material)
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op08_dmd_handoff_plan_candidate_materialization_without_execution_contract(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("dmd_execution_started_here", True),
        ("dmd_auto_execution_allowed", True),
        ("dmd_direct_call_safe_without_adapter", True),
        ("dmh_op18_finalizer_fake_generation_allowed", True),
        ("manual_decision_auto_executes_downstream", True),
        ("release_allowed", True),
        ("p8_start_allowed", True),
        ("next_required_step", "DMD_EXECUTE_NOW"),
    ],
)
def test_dhr_op08_contract_rejects_dmd_execution_or_promotion_mutations(field: str, bad_value: object) -> None:
    material = _op08_retry_not_materialized()
    material[field] = bad_value

    with pytest.raises(ValueError):
        dhr.assert_p7_r54_ahr_post_elr19_dhr_op08_dmd_handoff_plan_candidate_materialization_without_execution_contract(material)


def test_dhr_op09_closes_bodyfree_result_memo_for_retry_default_without_dmd_plan() -> None:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op09_bodyfree_result_memo_target_tests_regression_closure(
        dmd_handoff_plan_candidate_materialization=_op08_retry_not_materialized(),
        target_tests_summary_bodyfree=_passed_summary(143),
        selected_regression_summary_bodyfree=_passed_summary(251),
        compileall_summary_bodyfree=_passed_summary(1),
    )

    assert set(material) == set(dhr.P7_R54_AHR_POST_ELR19_DHR_OP09_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP09_SCHEMA_VERSION
    assert material["operation_step_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP09_STEP_REF
    assert material["result_memo_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP09_STATUS_CLOSED_BODYFREE_REF
    assert material["result_memo_bodyfree_closed"] is True
    assert material["selected_branch_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_BRANCH_RETRY_OR_START_REQUIRED_BEFORE_DOWNSTREAM_HANDOFF_REF
    assert material["dmd_handoff_plan_materialized"] is False
    assert material["target_tests_passed_count"] == 143
    assert material["selected_regression_passed_count"] == 251
    assert material["compileall_passed"] is True
    assert material["result_memo_forbidden_payload_key_path_refs"] == []
    assert material["result_memo_body_like_value_path_refs"] == []
    assert material["result_memo_promotion_claim_refs"] == []
    assert material["actual_local_human_review_execution_verified_here"] is False
    assert material["actual_rows_created_verified_here"] is False
    assert material["actual_disposal_purge_execution_verified_here"] is False
    assert material["dmd_execution_started_here"] is False
    assert material["r52_actual_execution_started_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == dhr.P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_RETRY_OR_START_ACTUAL_LOCAL_ONLY_HUMAN_REVIEW_OPERATION_REF
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op09_bodyfree_result_memo_target_tests_regression_closure_contract(material)
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dhr_op09_closes_bodyfree_result_memo_for_handoff_plan_without_execution() -> None:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op09_bodyfree_result_memo_target_tests_regression_closure(
        dmd_handoff_plan_candidate_materialization=_op08_handoff_materialized(),
        target_tests_summary_bodyfree=_passed_summary(143),
        selected_regression_summary_bodyfree=_passed_summary(251),
        compileall_summary_bodyfree=_passed_summary(1),
    )

    assert material["result_memo_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP09_STATUS_CLOSED_BODYFREE_REF
    assert material["selected_branch_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_BRANCH_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED_NO_AUTO_EXECUTION_REF
    assert material["dmd_handoff_plan_materialized"] is True
    assert material["dmd_handoff_ready_manual_decision_required"] is True
    assert material["dmd_execution_started_here"] is False
    assert material["dmd_auto_execution_allowed"] is False
    assert material["r52_actual_execution_started_here"] is False
    assert material["p8_question_design_started"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == dhr.P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_MANUAL_DECISION_EXECUTE_OR_DECLINE_DMD_HANDOFF_WITHOUT_AUTO_PROMOTION_REF
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op09_bodyfree_result_memo_target_tests_regression_closure_contract(material)
    _assert_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("actual_local_human_review_execution_verified_here", True),
        ("actual_rows_created_verified_here", True),
        ("actual_disposal_purge_execution_verified_here", True),
        ("dmd_execution_started_here", True),
        ("r52_actual_execution_started_here", True),
        ("p8_start_allowed", True),
        ("p8_question_design_started", True),
        ("release_allowed", True),
        ("result_memo_body_like_value_path_refs", ["result_memo.raw_input"]),
    ],
)
def test_dhr_op09_contract_rejects_result_memo_execution_verification_or_leak_mutations(field: str, bad_value: object) -> None:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op09_bodyfree_result_memo_target_tests_regression_closure(
        dmd_handoff_plan_candidate_materialization=_op08_retry_not_materialized(),
        target_tests_summary_bodyfree=_passed_summary(143),
        selected_regression_summary_bodyfree=_passed_summary(251),
        compileall_summary_bodyfree=_passed_summary(1),
    )
    material[field] = bad_value
    if field == "result_memo_body_like_value_path_refs":
        material["result_memo_body_like_value_path_count"] = 1

    with pytest.raises(ValueError):
        dhr.assert_p7_r54_ahr_post_elr19_dhr_op09_bodyfree_result_memo_target_tests_regression_closure_contract(material)


def test_dhr_op08_op09_full_operation_aliases_match_canonical_builders() -> None:
    op07 = _op07_retry_manual_decision()
    op03 = _op03_shape_valid_extraction()
    canonical_op08 = dhr.build_p7_r54_ahr_post_elr19_dhr_op08_dmd_handoff_plan_candidate_materialization_without_execution(
        manual_decision_materialization=op07,
        elr_op17_dmd_compatible_receipt_candidate_extraction=op03,
    )
    alias_op08 = dhr.build_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op08_dmd_handoff_plan_candidate_materialization_without_execution(
        manual_decision_materialization=op07,
        elr_op17_dmd_compatible_receipt_candidate_extraction=op03,
    )
    assert alias_op08 == canonical_op08
    assert dhr.assert_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op08_dmd_handoff_plan_candidate_materialization_without_execution_contract(alias_op08)

    canonical_op09 = dhr.build_p7_r54_ahr_post_elr19_dhr_op09_bodyfree_result_memo_target_tests_regression_closure(
        dmd_handoff_plan_candidate_materialization=canonical_op08,
        target_tests_summary_bodyfree=_passed_summary(143),
        selected_regression_summary_bodyfree=_passed_summary(251),
        compileall_summary_bodyfree=_passed_summary(1),
    )
    alias_op09 = dhr.build_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op09_bodyfree_result_memo_target_tests_regression_closure(
        dmd_handoff_plan_candidate_materialization=canonical_op08,
        target_tests_summary_bodyfree=_passed_summary(143),
        selected_regression_summary_bodyfree=_passed_summary(251),
        compileall_summary_bodyfree=_passed_summary(1),
    )
    assert alias_op09 == canonical_op09
    assert dhr.assert_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op09_bodyfree_result_memo_target_tests_regression_closure_contract(alias_op09)
