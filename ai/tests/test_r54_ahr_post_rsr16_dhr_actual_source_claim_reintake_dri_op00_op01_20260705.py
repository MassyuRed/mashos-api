# -*- coding: utf-8 -*-
"""R54-AHR Post-RSR16 DRI-OP00/OP01 result memo intake tests."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_20260704 as rsr
import emlis_ai_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_20260705 as dri
from test_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op16_result_20260704 import (
    _op15_complete_candidate,
    _op15_wait_for_allow,
    _op16_closed,
    _op16_green_kwargs,
)


def _assert_common_bodyfree_no_touch_no_promotion(material: dict[str, object]) -> None:
    assert material["source_mode"] == dri.P7_R54_AHR_POST_RSR16_DRI_SOURCE_MODE
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True
    assert all(value is False for value in material["public_contract"].values())
    assert all(value is False for value in material["post_rsr16_no_touch_contract"].values())
    assert all(value is False for value in material["body_free_markers"].values())
    for key in dri.P7_R54_AHR_POST_RSR16_DRI_REQUIRED_FALSE_FLAG_REFS:
        assert material[key] is False
    assert all(value is False for value in material["not_claimed_boundary"].values())


def _op16_waiting_for_op15() -> dict[str, object]:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op16_result_memo_tests_selected_regression_closure(
        **_op16_green_kwargs()
    )
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op16_result_memo_tests_selected_regression_closure_contract(material) is True
    assert material["rsr_op16_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_WAITING_FOR_OP15_REF
    return material


def _op16_repair_required() -> dict[str, object]:
    kwargs = _op16_green_kwargs()
    kwargs["target_test_summary"] = {
        "status_ref": "rsr_op16_target_failed",
        "passed_count": 30,
        "failed_count": 1,
        "timed_out": False,
        "body_free": True,
    }
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op16_result_memo_tests_selected_regression_closure(
        branch_resolution=_op15_complete_candidate(),
        **kwargs,
    )
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op16_result_memo_tests_selected_regression_closure_contract(material) is True
    assert material["rsr_op16_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_REPAIR_REQUIRED_REF
    return material


def _op16_body_leak_blocked() -> dict[str, object]:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op16_result_memo_tests_selected_regression_closure(
        branch_resolution=_op15_complete_candidate(),
        additional_bodyfree_materials={"bad_material": {"release_allowed": True}},
        **_op16_green_kwargs(),
    )
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op16_result_memo_tests_selected_regression_closure_contract(material) is True
    assert material["rsr_op16_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_BODY_LEAK_OR_PROMOTION_BLOCKED_REF
    return material


def test_dri_op00_refreezes_scope_no_touch_no_promotion_after_rsr_op16() -> None:
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op00_scope_no_touch_no_promotion_refreeze_after_rsr_op16()

    assert set(material) == set(dri.P7_R54_AHR_POST_RSR16_DRI_OP00_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP00_SCHEMA_VERSION
    assert material["operation_step_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP00_STEP_REF
    assert material["selected_stage_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_SELECTED_STAGE_REF
    assert material["selected_design_target_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_SELECTED_DESIGN_TARGET_REF
    assert material["expected_next_required_step_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_CURRENT_EXPECTED_NEXT_REQUIRED_STEP_REF
    assert material["dri_op00_scope_confirmed"] is True
    assert material["dri_op00_no_touch_boundary_confirmed"] is True
    assert material["dri_op00_no_promotion_boundary_confirmed"] is True
    assert material["dri_op00_does_not_intake_rsr_op16_result_memo"] is True
    assert material["dri_op00_does_not_materialize_dhr_op04_adapter_candidate"] is True
    assert material["dri_op00_does_not_call_dhr_op04"] is True
    assert material["dri_op00_does_not_execute_dhr_reintake_dmd_or_r52"] is True
    assert material["dri_op00_does_not_run_actual_local_human_review"] is True
    assert material["dri_op00_does_not_start_p5_p6_p8_p7_or_release"] is True
    assert material["implemented_steps"] == list(dri.P7_R54_AHR_POST_RSR16_DRI_OP00_IMPLEMENTED_STEPS)
    assert material["not_yet_implemented_steps"] == list(dri.P7_R54_AHR_POST_RSR16_DRI_OP00_NOT_YET_IMPLEMENTED_STEPS)
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP01_STEP_REF
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op00_scope_no_touch_no_promotion_refreeze_after_rsr_op16_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("schema_version", "bad_schema"),
        ("source_mode", "github_remote"),
        ("git_checked", True),
        ("dri_op00_no_touch_boundary_confirmed", False),
        ("dri_op00_no_promotion_boundary_confirmed", False),
        ("dri_op00_does_not_call_dhr_op04", False),
        ("body_free", False),
        ("dhr_op04_called_here", True),
        ("dhr_actual_source_claim_reintake_executed_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", dri.P7_R54_AHR_POST_RSR16_DRI_OP02_STEP_REF),
    ],
)
def test_dri_op00_contract_rejects_scope_touch_or_promotion_mutations(field: str, bad_value: object) -> None:
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op00_scope_no_touch_no_promotion_refreeze_after_rsr_op16()
    material[field] = bad_value

    with pytest.raises(ValueError):
        dri.assert_p7_r54_ahr_post_rsr16_dri_op00_scope_no_touch_no_promotion_refreeze_after_rsr_op16_contract(material)


def test_dri_op00_contract_rejects_public_contract_marker_mutation() -> None:
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op00_scope_no_touch_no_promotion_refreeze_after_rsr_op16()
    material["public_contract"]["api_response_key_added"] = True

    with pytest.raises(ValueError):
        dri.assert_p7_r54_ahr_post_rsr16_dri_op00_scope_no_touch_no_promotion_refreeze_after_rsr_op16_contract(material)


def test_dri_op00_contract_rejects_forbidden_top_level_payload_key() -> None:
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op00_scope_no_touch_no_promotion_refreeze_after_rsr_op16()
    material["raw_input"] = "must never pass"

    with pytest.raises(ValueError):
        dri.assert_p7_r54_ahr_post_rsr16_dri_op00_scope_no_touch_no_promotion_refreeze_after_rsr_op16_contract(material)


def test_dri_op01_accepts_valid_rsr_op16_closed_bodyfree_without_actual_or_dhr_claim() -> None:
    op00 = dri.build_p7_r54_ahr_post_rsr16_dri_op00_scope_no_touch_no_promotion_refreeze_after_rsr_op16()
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op01_rsr_op16_result_memo_intake(
        scope_no_touch_no_promotion_refreeze=op00,
        rsr_op16_result_memo=_op16_closed(),
    )

    assert set(material) == set(dri.P7_R54_AHR_POST_RSR16_DRI_OP01_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP01_SCHEMA_VERSION
    assert material["operation_step_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP01_STEP_REF
    assert material["op00_contract_valid"] is True
    assert material["rsr_op16_result_memo_present"] is True
    assert material["rsr_op16_contract_valid"] is True
    assert material["rsr_op16_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_CLOSED_BODYFREE_REF
    assert material["rsr_op16_result_memo_bodyfree_closed"] is True
    assert material["rsr_op16_op15_actual_evidence_complete_candidate"] is True
    assert material["rsr_op16_target_tests_passed_count"] == 31
    assert material["rsr_op16_accumulated_target_passed_count"] == 338
    assert material["rsr_op16_dhr_selected_regression_passed_count"] == 139
    assert material["dri_op01_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_CLOSED_BODYFREE_INTAKE_READY_REF
    assert material["rsr_op16_intake_status_ref"] == material["dri_op01_status_ref"]
    assert material["dri_op01_ready"] is True
    assert material["dri_op01_ready_for_rsr_op15_branch_alignment"] is True
    assert material["rsr_op16_forbidden_payload_key_path_refs"] == []
    assert material["rsr_op16_body_like_value_path_refs"] == []
    assert material["rsr_op16_promotion_claim_refs"] == []
    assert material["actual_review_execution_claimed_by_dri_op01"] is False
    assert material["actual_review_evidence_completed_by_dri_op01"] is False
    assert material["dhr_actual_source_claim_confirmed_by_dri_op01"] is False
    assert material["dhr_op04_adapter_candidate_materialized_by_dri_op01"] is False
    assert material["dhr_op04_called_here"] is False
    assert material["dhr_actual_source_claim_reintake_executed_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP02_STEP_REF
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op01_rsr_op16_result_memo_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op01_accepts_rsr_op16_closed_bodyfree_even_when_op15_branch_waits_for_allow() -> None:
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op01_rsr_op16_result_memo_intake(
        rsr_op16_result_memo=_op16_closed(_op15_wait_for_allow()),
    )

    assert material["rsr_op16_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_CLOSED_BODYFREE_REF
    assert material["rsr_op16_op15_actual_evidence_complete_candidate"] is False
    assert material["dri_op01_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_CLOSED_BODYFREE_INTAKE_READY_REF
    assert material["dri_op01_ready_for_rsr_op15_branch_alignment"] is True
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP02_STEP_REF
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op01_rsr_op16_result_memo_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op01_waits_when_rsr_op16_result_memo_is_missing() -> None:
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op01_rsr_op16_result_memo_intake()

    assert material["dri_op01_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_WAITING_FOR_RSR_OP16_CLOSURE_REF
    assert material["rsr_op16_result_memo_present"] is False
    assert material["rsr_op16_contract_valid"] is False
    assert material["dri_op01_waiting_for_rsr_op16_closure"] is True
    assert material["dri_op01_ready"] is False
    assert "rsr_op16_result_memo_missing" in material["dri_op01_blocker_refs"]
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_RSR_OP16_CLOSURE_REF
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op01_rsr_op16_result_memo_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op01_waits_when_rsr_op16_waits_for_op15_closure() -> None:
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op01_rsr_op16_result_memo_intake(
        rsr_op16_result_memo=_op16_waiting_for_op15(),
    )

    assert material["dri_op01_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_WAITING_FOR_RSR_OP16_CLOSURE_REF
    assert material["rsr_op16_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_WAITING_FOR_OP15_REF
    assert material["rsr_op16_contract_valid"] is True
    assert material["dri_op01_waiting_for_rsr_op16_closure"] is True
    assert material["dri_op01_ready"] is False
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_RSR_OP16_CLOSURE_REF
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op01_rsr_op16_result_memo_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op01_repairs_when_rsr_op16_reports_repair_required() -> None:
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op01_rsr_op16_result_memo_intake(
        rsr_op16_result_memo=_op16_repair_required(),
    )

    assert material["dri_op01_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_REPAIR_RSR_OP16_RESULT_MEMO_REF
    assert material["rsr_op16_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_REPAIR_REQUIRED_REF
    assert material["rsr_op16_contract_valid"] is True
    assert material["dri_op01_repair_required"] is True
    assert material["dri_op01_ready"] is False
    assert "rsr_op16_result_memo_repair_required" in material["dri_op01_blocker_refs"]
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_RSR_OP16_RESULT_MEMO_REF
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op01_rsr_op16_result_memo_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op01_blocks_when_rsr_op16_reports_body_leak_or_promotion() -> None:
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op01_rsr_op16_result_memo_intake(
        rsr_op16_result_memo=_op16_body_leak_blocked(),
    )

    assert material["dri_op01_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_BLOCKED_RSR_OP16_BODY_LEAK_OR_PROMOTION_REF
    assert material["rsr_op16_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_BODY_LEAK_OR_PROMOTION_BLOCKED_REF
    assert material["dri_op01_body_leak_or_promotion_blocked"] is True
    assert material["dri_op01_ready"] is False
    assert material["rsr_op16_promotion_claim_refs"]
    assert "rsr_op16_promotion_claim_detected" in material["dri_op01_blocker_refs"]
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_RSR_OP16_BODY_LEAK_OR_PROMOTION_REF
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op01_rsr_op16_result_memo_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op01_blocks_forbidden_rsr_op16_payload_key_without_leaking_body_value() -> None:
    op16 = _op16_closed()
    op16["question_text"] = "this question text must not leak"
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op01_rsr_op16_result_memo_intake(
        rsr_op16_result_memo=op16,
    )

    assert material["dri_op01_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_BLOCKED_RSR_OP16_BODY_LEAK_OR_PROMOTION_REF
    assert material["rsr_op16_contract_valid"] is False
    assert material["rsr_op16_forbidden_payload_key_path_count"] > 0
    assert material["rsr_op16_body_like_value_path_count"] > 0
    assert "rsr_op16_forbidden_payload_key_detected" in material["dri_op01_blocker_refs"]
    assert "this question text must not leak" not in repr(material)
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_RSR_OP16_BODY_LEAK_OR_PROMOTION_REF
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op01_rsr_op16_result_memo_intake_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("dri_op01_status_ref", dri.P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_WAITING_FOR_RSR_OP16_CLOSURE_REF),
        ("dri_op01_ready_for_rsr_op15_branch_alignment", False),
        ("actual_review_execution_claimed_by_dri_op01", True),
        ("actual_review_evidence_completed_by_dri_op01", True),
        ("dhr_actual_source_claim_confirmed_by_dri_op01", True),
        ("dhr_op04_adapter_candidate_materialized_by_dri_op01", True),
        ("dhr_op04_called_here", True),
        ("dhr_actual_source_claim_reintake_executed_here", True),
        ("dmd_execution_started_here", True),
        ("r52_actual_execution_started_here", True),
        ("p8_start_allowed", True),
        ("p8_question_design_started", True),
        ("release_allowed", True),
        ("next_required_step", "P8_START"),
    ],
)
def test_dri_op01_contract_rejects_ready_intake_mutations(field: str, bad_value: object) -> None:
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op01_rsr_op16_result_memo_intake(
        rsr_op16_result_memo=_op16_closed(),
    )
    material[field] = bad_value

    with pytest.raises(ValueError):
        dri.assert_p7_r54_ahr_post_rsr16_dri_op01_rsr_op16_result_memo_intake_contract(material)


def test_dri_op00_op01_full_title_aliases_match_canonical_builders() -> None:
    canonical_op00 = dri.build_p7_r54_ahr_post_rsr16_dri_op00_scope_no_touch_no_promotion_refreeze_after_rsr_op16()
    alias_op00 = dri.build_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op00_scope_no_touch_no_promotion_refreeze_after_rsr_op16()
    canonical_op01 = dri.build_p7_r54_ahr_post_rsr16_dri_op01_rsr_op16_result_memo_intake(
        rsr_op16_result_memo=_op16_closed(),
    )
    alias_op01 = dri.build_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op01_rsr_op16_result_memo_intake(
        rsr_op16_result_memo=_op16_closed(),
    )

    assert canonical_op00 == alias_op00
    assert canonical_op01 == alias_op01
    assert dri.assert_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op00_scope_no_touch_no_promotion_refreeze_after_rsr_op16_contract(alias_op00) is True
    assert dri.assert_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op01_rsr_op16_result_memo_intake_contract(alias_op01) is True
