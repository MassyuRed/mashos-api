# -*- coding: utf-8 -*-
"""R54-AHR Post-DHR09 RSR-OP00/OP01 retry/start intake tests."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_20260704 as rsr
import emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704 as dhr
from test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op08_op09_result_20260704 import (
    _op08_handoff_materialized,
    _op08_retry_not_materialized,
    _passed_summary,
)


def _assert_common_bodyfree_no_touch_no_promotion(material: dict[str, object]) -> None:
    assert material["source_mode"] == rsr.P7_R54_AHR_POST_DHR09_RSR_SOURCE_MODE
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True
    assert all(value is False for value in material["public_contract"].values())
    assert all(value is False for value in material["post_dhr09_no_touch_contract"].values())
    assert all(value is False for value in material["body_free_markers"].values())
    for key in rsr.P7_R54_AHR_POST_DHR09_RSR_REQUIRED_FALSE_FLAG_REFS:
        assert material[key] is False
    assert all(value is False for value in material["not_claimed_boundary"].values())


def _dhr_op09_retry_closed() -> dict[str, object]:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op09_bodyfree_result_memo_target_tests_regression_closure(
        dmd_handoff_plan_candidate_materialization=_op08_retry_not_materialized(),
        target_tests_summary_bodyfree=_passed_summary(143),
        selected_regression_summary_bodyfree=_passed_summary(251),
        compileall_summary_bodyfree=_passed_summary(1),
    )
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op09_bodyfree_result_memo_target_tests_regression_closure_contract(material)
    assert material["selected_branch_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_BRANCH_RETRY_OR_START_REQUIRED_BEFORE_DOWNSTREAM_HANDOFF_REF
    return material


def _dhr_op09_handoff_closed() -> dict[str, object]:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op09_bodyfree_result_memo_target_tests_regression_closure(
        dmd_handoff_plan_candidate_materialization=_op08_handoff_materialized(),
        target_tests_summary_bodyfree=_passed_summary(143),
        selected_regression_summary_bodyfree=_passed_summary(251),
        compileall_summary_bodyfree=_passed_summary(1),
    )
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op09_bodyfree_result_memo_target_tests_regression_closure_contract(material)
    assert material["selected_branch_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_BRANCH_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED_NO_AUTO_EXECUTION_REF
    return material


def _dhr_op09_retry_incomplete() -> dict[str, object]:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op09_bodyfree_result_memo_target_tests_regression_closure(
        dmd_handoff_plan_candidate_materialization=_op08_retry_not_materialized()
    )
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op09_bodyfree_result_memo_target_tests_regression_closure_contract(material)
    assert material["selected_branch_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_BRANCH_RETRY_OR_START_REQUIRED_BEFORE_DOWNSTREAM_HANDOFF_REF
    assert material["result_memo_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP09_STATUS_INCOMPLETE_OR_UNVERIFIED_REF
    return material


def test_rsr_op00_refreezes_post_dhr09_scope_without_touch_or_promotion() -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op00_scope_no_touch_no_promotion_refreeze_after_dhr_op09()

    assert set(material) == set(rsr.P7_R54_AHR_POST_DHR09_RSR_OP00_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP00_SCHEMA_VERSION
    assert material["operation_step_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP00_STEP_REF
    assert material["selected_stage_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_SELECTED_STAGE_REF
    assert material["expected_default_branch_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_EXPECTED_DEFAULT_BRANCH_REF
    assert material["expected_default_next_required_step_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_EXPECTED_DEFAULT_NEXT_REQUIRED_STEP_REF
    assert material["rsr_op00_scope_confirmed"] is True
    assert material["rsr_op00_no_touch_boundary_confirmed"] is True
    assert material["rsr_op00_no_promotion_boundary_confirmed"] is True
    assert material["rsr_op00_does_not_intake_dhr_op09_result_memo"] is True
    assert material["rsr_op00_does_not_accept_explicit_local_only_allow"] is True
    assert material["rsr_op00_does_not_run_actual_local_human_review"] is True
    assert material["rsr_op00_does_not_execute_dmd_or_r52"] is True
    assert material["rsr_op00_does_not_start_p5_p6_p8_p7_or_release"] is True
    assert material["implemented_steps"] == list(rsr.P7_R54_AHR_POST_DHR09_RSR_OP00_IMPLEMENTED_STEPS)
    assert material["not_yet_implemented_steps"] == list(rsr.P7_R54_AHR_POST_DHR09_RSR_OP00_NOT_YET_IMPLEMENTED_STEPS)
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP01_STEP_REF
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op00_scope_no_touch_no_promotion_refreeze_after_dhr_op09_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("schema_version", "bad_schema"),
        ("source_mode", "github_remote"),
        ("git_checked", True),
        ("rsr_op00_no_touch_boundary_confirmed", False),
        ("rsr_op00_no_promotion_boundary_confirmed", False),
        ("rsr_op00_does_not_accept_explicit_local_only_allow", False),
        ("body_free", False),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", rsr.P7_R54_AHR_POST_DHR09_RSR_OP02_STEP_REF),
    ],
)
def test_rsr_op00_contract_rejects_scope_touch_or_promotion_mutations(field: str, bad_value: object) -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op00_scope_no_touch_no_promotion_refreeze_after_dhr_op09()
    material[field] = bad_value

    with pytest.raises(ValueError):
        rsr.assert_p7_r54_ahr_post_dhr09_rsr_op00_scope_no_touch_no_promotion_refreeze_after_dhr_op09_contract(material)


def test_rsr_op00_contract_rejects_public_contract_marker_mutation() -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op00_scope_no_touch_no_promotion_refreeze_after_dhr_op09()
    material["public_contract"]["api_response_key_added"] = True

    with pytest.raises(ValueError):
        rsr.assert_p7_r54_ahr_post_dhr09_rsr_op00_scope_no_touch_no_promotion_refreeze_after_dhr_op09_contract(material)


def test_rsr_op00_contract_rejects_forbidden_top_level_payload_key() -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op00_scope_no_touch_no_promotion_refreeze_after_dhr_op09()
    material["raw_input"] = "must never pass"

    with pytest.raises(ValueError):
        rsr.assert_p7_r54_ahr_post_dhr09_rsr_op00_scope_no_touch_no_promotion_refreeze_after_dhr_op09_contract(material)


def test_rsr_op01_accepts_dhr_op09_retry_start_default_without_actual_execution_or_allow_claim() -> None:
    op00 = rsr.build_p7_r54_ahr_post_dhr09_rsr_op00_scope_no_touch_no_promotion_refreeze_after_dhr_op09()
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op01_dhr_op09_result_memo_selected_branch_next_step_intake(
        scope_no_touch_no_promotion_refreeze=op00,
        dhr_op09_result_memo=_dhr_op09_retry_closed(),
    )

    assert set(material) == set(rsr.P7_R54_AHR_POST_DHR09_RSR_OP01_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP01_SCHEMA_VERSION
    assert material["operation_step_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP01_STEP_REF
    assert material["op00_contract_valid"] is True
    assert material["dhr_op09_result_memo_present"] is True
    assert material["dhr_op09_contract_valid"] is True
    assert material["dhr_op09_result_memo_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP09_STATUS_CLOSED_BODYFREE_REF
    assert material["dhr_op09_selected_branch_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_EXPECTED_DEFAULT_BRANCH_REF
    assert material["dhr_op09_next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_EXPECTED_DEFAULT_NEXT_REQUIRED_STEP_REF
    assert material["dhr_op09_dmd_handoff_plan_materialized"] is False
    assert material["rsr_op01_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_DHR09_INTAKE_RETRY_OR_START_REQUIRED_REF
    assert material["dhr_op09_intake_status_ref"] == material["rsr_op01_status_ref"]
    assert material["rsr_op01_ready"] is True
    assert material["rsr_op01_ready_for_upstream_relationship_verification"] is True
    assert material["rsr_op01_retry_or_start_required"] is True
    assert material["rsr_op01_waiting_or_incomplete"] is False
    assert material["target_tests_passed_count"] == 143
    assert material["selected_regression_passed_count"] == 251
    assert material["compileall_passed"] is True
    assert material["dhr_op09_forbidden_payload_key_path_refs"] == []
    assert material["dhr_op09_body_like_value_path_refs"] == []
    assert material["dhr_op09_promotion_claim_refs"] == []
    assert material["actual_review_execution_claimed_by_rsr_op01"] is False
    assert material["explicit_local_only_allow_accepted_by_rsr_op01"] is False
    assert material["dmd_execution_started_here"] is False
    assert material["r52_actual_execution_started_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP02_STEP_REF
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op01_dhr_op09_result_memo_selected_branch_next_step_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rsr_op01_holds_unexpected_dhr_handoff_branch_without_auto_dmd_execution() -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op01_dhr_op09_result_memo_selected_branch_next_step_intake(
        dhr_op09_result_memo=_dhr_op09_handoff_closed(),
    )

    assert material["rsr_op01_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_DHR09_INTAKE_UNEXPECTED_HANDOFF_BRANCH_MANUAL_HOLD_REF
    assert material["dhr_op09_selected_branch_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_DHR_HANDOFF_BRANCH_REF
    assert material["dhr_op09_dmd_handoff_plan_materialized"] is True
    assert material["rsr_op01_unexpected_handoff_branch_manual_hold"] is True
    assert material["rsr_op01_ready"] is False
    assert material["dmd_execution_started_here"] is False
    assert material["dmd_auto_execution_allowed"] is False
    assert material["manual_decision_auto_executes_downstream"] is False
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_MANUAL_HOLD_UNEXPECTED_DHR_HANDOFF_BRANCH_REF
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op01_dhr_op09_result_memo_selected_branch_next_step_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rsr_op01_waits_when_dhr_op09_retry_branch_is_not_closed_yet() -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op01_dhr_op09_result_memo_selected_branch_next_step_intake(
        dhr_op09_result_memo=_dhr_op09_retry_incomplete(),
    )

    assert material["rsr_op01_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_DHR09_INTAKE_WAITING_OR_INCOMPLETE_REF
    assert material["dhr_op09_selected_branch_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_EXPECTED_DEFAULT_BRANCH_REF
    assert material["dhr_op09_contract_valid"] is True
    assert material["rsr_op01_waiting_or_incomplete"] is True
    assert material["rsr_op01_ready"] is False
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_DHR_OP09_CLOSED_RETRY_BRANCH_REF
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op01_dhr_op09_result_memo_selected_branch_next_step_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rsr_op01_waits_when_dhr_op09_material_is_missing() -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op01_dhr_op09_result_memo_selected_branch_next_step_intake()

    assert material["rsr_op01_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_DHR09_INTAKE_WAITING_OR_INCOMPLETE_REF
    assert material["dhr_op09_result_memo_present"] is False
    assert material["dhr_op09_contract_valid"] is False
    assert material["rsr_op01_waiting_or_incomplete"] is True
    assert material["rsr_op01_ready"] is False
    assert "dhr_op09_result_memo_missing" in material["rsr_op01_blocker_refs"]
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_DHR_OP09_CLOSED_RETRY_BRANCH_REF
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op01_dhr_op09_result_memo_selected_branch_next_step_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rsr_op01_repairs_when_dhr_op09_carries_promotion_claim() -> None:
    op09 = _dhr_op09_retry_closed()
    op09["release_allowed"] = True
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op01_dhr_op09_result_memo_selected_branch_next_step_intake(
        dhr_op09_result_memo=op09,
    )

    assert material["rsr_op01_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_DHR09_INTAKE_REPAIR_REQUIRED_REF
    assert material["dhr_op09_contract_valid"] is False
    assert material["dhr_op09_promotion_claim_ref_count"] > 0
    assert "dhr_op09_promotion_claim_detected" in material["rsr_op01_blocker_refs"]
    assert material["rsr_op01_repair_required"] is True
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_DHR_OP09_RESULT_MEMO_BOUNDARY_REF
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op01_dhr_op09_result_memo_selected_branch_next_step_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rsr_op01_repairs_forbidden_dhr_op09_payload_key_without_leaking_body_value() -> None:
    op09 = _dhr_op09_retry_closed()
    op09["question_text"] = "this question body must not leak"
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op01_dhr_op09_result_memo_selected_branch_next_step_intake(
        dhr_op09_result_memo=op09,
    )

    assert material["rsr_op01_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_DHR09_INTAKE_REPAIR_REQUIRED_REF
    assert material["dhr_op09_forbidden_payload_key_path_count"] > 0
    assert material["dhr_op09_body_like_value_path_count"] > 0
    assert "dhr_op09_forbidden_payload_key_detected" in material["rsr_op01_blocker_refs"]
    assert "this question body must not leak" not in repr(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op01_dhr_op09_result_memo_selected_branch_next_step_intake_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("rsr_op01_status_ref", rsr.P7_R54_AHR_POST_DHR09_RSR_DHR09_INTAKE_WAITING_OR_INCOMPLETE_REF),
        ("rsr_op01_ready_for_upstream_relationship_verification", False),
        ("explicit_local_only_allow_accepted_by_rsr_op01", True),
        ("actual_review_execution_claimed_by_rsr_op01", True),
        ("actual_local_human_review_executed_here", True),
        ("actual_operation_receipt_created_here", True),
        ("dmd_execution_started_here", True),
        ("r52_actual_execution_started_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", "P8_START"),
    ],
)
def test_rsr_op01_contract_rejects_retry_start_intake_mutations(field: str, bad_value: object) -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op01_dhr_op09_result_memo_selected_branch_next_step_intake(
        dhr_op09_result_memo=_dhr_op09_retry_closed(),
    )
    material[field] = bad_value

    with pytest.raises(ValueError):
        rsr.assert_p7_r54_ahr_post_dhr09_rsr_op01_dhr_op09_result_memo_selected_branch_next_step_intake_contract(material)


def test_rsr_op00_op01_full_title_aliases_match_canonical_builders() -> None:
    canonical_op00 = rsr.build_p7_r54_ahr_post_dhr09_rsr_op00_scope_no_touch_no_promotion_refreeze_after_dhr_op09()
    alias_op00 = rsr.build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op00_scope_no_touch_no_promotion_refreeze_after_dhr_op09()
    canonical_op01 = rsr.build_p7_r54_ahr_post_dhr09_rsr_op01_dhr_op09_result_memo_selected_branch_next_step_intake(
        dhr_op09_result_memo=_dhr_op09_retry_closed(),
    )
    alias_op01 = rsr.build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op01_dhr_op09_result_memo_selected_branch_next_step_intake(
        dhr_op09_result_memo=_dhr_op09_retry_closed(),
    )

    assert canonical_op00 == alias_op00
    assert canonical_op01 == alias_op01
    assert rsr.assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op00_scope_no_touch_no_promotion_refreeze_after_dhr_op09_contract(alias_op00) is True
    assert rsr.assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op01_dhr_op09_result_memo_selected_branch_next_step_intake_contract(alias_op01) is True
