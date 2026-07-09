# -*- coding: utf-8 -*-
"""R54-AHR Post-MRB08 / DHR-OP04 result manual decision RDB-OP02/OP03 tests."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_20260705 as rdb
import emlis_ai_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_20260705 as mrb
import emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704 as dhr
from test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op06_op07_20260705 import (
    _op05_confirmed,
    _op05_invalid_result,
    _op05_not_confirmed,
    _op05_waiting_result,
)
from test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op08_result_20260705 import _op08_from_op05


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


def _op01_from_op05(op05: dict[str, object]) -> dict[str, object]:
    return rdb.build_p7_r54_ahr_post_mrb08_rdb_op01_mrb_op08_result_memo_closure_intake(
        mrb_op08_result_memo_closure=_op08_from_op05(op05),
    )


def _op02_from_op05(op05: dict[str, object]) -> dict[str, object]:
    return rdb.build_p7_r54_ahr_post_mrb08_rdb_op02_mrb_selected_branch_dhr_op04_result_status_consistency_check(
        mrb_op08_result_memo_closure_intake=_op01_from_op05(op05),
    )


def _op03_from_op05(op05: dict[str, object]) -> dict[str, object]:
    return rdb.build_p7_r54_ahr_post_mrb08_rdb_op03_dhr_op04_result_manual_decision_lane_resolver(
        mrb_branch_dhr_status_consistency_check=_op02_from_op05(op05),
    )


@pytest.mark.parametrize(
    ("op05", "expected_mrb_branch", "expected_dhr_status", "confirmed"),
    [
        (
            _op05_confirmed(),
            mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_CONFIRMED_BODYFREE_STOPPED_REF,
            dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_CONFIRMED_BODYFREE_REF,
            True,
        ),
        (
            _op05_not_confirmed(),
            mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_STOPPED_REF,
            dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_REF,
            False,
        ),
        (
            _op05_waiting_result(),
            mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_WAITING_EXTERNAL_CLAIM_STOPPED_REF,
            dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_WAITING_FOR_EXTERNAL_BODYFREE_CLAIM_REF,
            False,
        ),
        (
            _op05_invalid_result(),
            mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_INVALID_REPAIR_REQUIRED_STOPPED_REF,
            dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_INVALID_REPAIR_REQUIRED_REF,
            False,
        ),
    ],
)
def test_rdb_op02_maps_all_four_dhr_op04_status_refs_consistently(
    op05: dict[str, object],
    expected_mrb_branch: str,
    expected_dhr_status: str,
    confirmed: bool,
) -> None:
    material = _op02_from_op05(op05)

    assert set(material) == set(rdb.P7_R54_AHR_POST_MRB08_RDB_OP02_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP02_SCHEMA_VERSION
    assert material["operation_step_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP02_STEP_REF
    assert material["op01_contract_valid"] is True
    assert material["op01_ready_for_rdb_op02"] is True
    assert material["mrb_selected_branch_ref"] == expected_mrb_branch
    assert material["dhr_op04_result_status_ref"] == expected_dhr_status
    assert material["expected_mrb_selected_branch_ref_for_dhr_status"] == expected_mrb_branch
    assert material["expected_dhr_op04_result_status_ref_for_mrb_branch"] == expected_dhr_status
    assert material["branch_status_consistency_checked"] is True
    assert material["branch_status_consistent"] is True
    assert material["rdb_op02_status_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP02_STATUS_CONSISTENT_READY_FOR_OP03_REF
    assert material["rdb_op02_ready_for_rdb_op03"] is True
    assert material["branch_status_mismatch_refs"] == []
    assert material["op06_branch_matches_mrb_selected_branch"] is True
    assert material["op06_dhr_status_matches_dhr_op04_result_status"] is True
    assert material["dhr_status_maps_to_mrb_selected_branch"] is True
    assert material["mrb_selected_branch_maps_to_dhr_status"] is True
    assert material["actual_source_claim_confirmed_only_when_dhr_confirmed"] is True
    assert material["actual_source_claim_confirmed_required_for_confirmed_branch_satisfied"] is True
    assert material["actual_source_claim_confirmed_for_downstream_handoff"] is confirmed
    assert material["dhr_op04_manual_call_present_for_called_result_branch"] is True
    assert material["dhr_op04_result_captured_for_called_result_branch"] is True
    assert material["next_required_step"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP03_STEP_REF
    assert material["rdb_op02_does_not_call_dhr_op05"] is True
    assert material["rdb_op02_does_not_materialize_branch_specific_manual_decision"] is True
    assert material["dhr_op05_called_here"] is False
    assert material["dhr_op06_called_here"] is False
    assert material["p8_question_design_started"] is False
    assert material["release_allowed"] is False
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op02_mrb_selected_branch_dhr_op04_result_status_consistency_check_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rdb_op02_repairs_when_mrb_branch_and_dhr_status_mismatch() -> None:
    op01 = _op01_from_op05(_op05_not_confirmed())
    op01["dhr_op04_result_status_ref"] = dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_CONFIRMED_BODYFREE_REF
    material = rdb.build_p7_r54_ahr_post_mrb08_rdb_op02_mrb_selected_branch_dhr_op04_result_status_consistency_check(
        mrb_op08_result_memo_closure_intake=op01,
    )

    assert material["rdb_op02_status_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP02_STATUS_REPAIR_REQUIRED_FOR_BRANCH_STATUS_MISMATCH_REF
    assert material["branch_status_consistent"] is False
    assert material["rdb_op02_repair_required"] is True
    assert "dhr_op04_result_status_ref_does_not_map_to_mrb_selected_branch_ref" in material["branch_status_mismatch_refs"]
    assert "mrb_selected_branch_ref_does_not_map_to_dhr_op04_result_status_ref" in material["branch_status_mismatch_refs"]
    assert material["next_required_step"] == rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_REPAIR_RESULT_OR_MRB08_REF
    assert material["dhr_op05_called_here"] is False
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op02_mrb_selected_branch_dhr_op04_result_status_consistency_check_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rdb_op02_rejects_confirmed_flag_outside_confirmed_branch_without_promoting() -> None:
    op01 = _op01_from_op05(_op05_not_confirmed())
    op01["actual_source_claim_confirmed_for_downstream_handoff"] = True
    material = rdb.build_p7_r54_ahr_post_mrb08_rdb_op02_mrb_selected_branch_dhr_op04_result_status_consistency_check(
        mrb_op08_result_memo_closure_intake=op01,
    )

    assert material["op01_contract_valid"] is False
    assert material["branch_status_consistent"] is False
    assert material["actual_source_claim_confirmed_only_when_dhr_confirmed"] is False
    assert "actual_source_claim_confirmed_true_outside_dhr_confirmed_branch" in material["branch_status_mismatch_refs"]
    assert material["rdb_op02_status_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP02_STATUS_REPAIR_REQUIRED_FOR_BRANCH_STATUS_MISMATCH_REF
    assert material["dhr_op05_called_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op02_mrb_selected_branch_dhr_op04_result_status_consistency_check_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rdb_op02_repairs_when_op06_branch_or_status_diverges_from_op08_refs() -> None:
    op01 = _op01_from_op05(_op05_confirmed())
    op01["op06_mrb_selected_branch_ref"] = mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_STOPPED_REF
    material = rdb.build_p7_r54_ahr_post_mrb08_rdb_op02_mrb_selected_branch_dhr_op04_result_status_consistency_check(
        mrb_op08_result_memo_closure_intake=op01,
    )

    assert material["branch_status_consistent"] is False
    assert material["op06_branch_matches_mrb_selected_branch"] is False
    assert "op06_mrb_selected_branch_ref_mismatch_or_missing" in material["branch_status_mismatch_refs"]
    assert material["rdb_op02_status_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP02_STATUS_REPAIR_REQUIRED_FOR_BRANCH_STATUS_MISMATCH_REF
    assert material["dhr_op05_called_here"] is False
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op02_mrb_selected_branch_dhr_op04_result_status_consistency_check_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("op05", "expected_status", "expected_lane", "expected_next_ref", "candidate_key"),
    [
        (
            _op05_confirmed(),
            rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_CONFIRMED_DHR_OP05_MANUAL_HANDOFF_CANDIDATE_STOPPED_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_CONFIRMED_DHR_OP05_HANDOFF_CANDIDATE_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_PREPARE_DHR_OP05_MANUAL_HANDOFF_DECISION_REF,
            "dhr_op05_manual_handoff_candidate_present",
        ),
        (
            _op05_not_confirmed(),
            rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_NOT_CONFIRMED_RETRY_OR_START_DECISION_REQUIRED_STOPPED_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_RETRY_OR_START_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_PREPARE_RETRY_OR_START_DECISION_REF,
            "retry_or_start_candidate_present",
        ),
        (
            _op05_waiting_result(),
            rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_WAITING_EXTERNAL_CLAIM_REQUIRED_STOPPED_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_WAIT_EXTERNAL_CLAIM_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_WAIT_EXTERNAL_BODYFREE_CLAIM_REF,
            "external_claim_wait_candidate_present",
        ),
        (
            _op05_invalid_result(),
            rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_REPAIR_REQUIRED_AFTER_DHR_OP04_RESULT_STOPPED_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_REPAIR_RESULT_OR_MRB08_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_REPAIR_RESULT_OR_MRB08_REF,
            "repair_candidate_present",
        ),
    ],
)
def test_rdb_op03_resolves_exactly_one_manual_decision_lane_for_all_consistent_branches(
    op05: dict[str, object],
    expected_status: str,
    expected_lane: str,
    expected_next_ref: str,
    candidate_key: str,
) -> None:
    material = _op03_from_op05(op05)

    assert set(material) == set(rdb.P7_R54_AHR_POST_MRB08_RDB_OP03_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP03_SCHEMA_VERSION
    assert material["operation_step_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP03_STEP_REF
    assert material["op02_contract_valid"] is True
    assert material["op02_branch_status_consistent"] is True
    assert material["rdb_status_ref"] == expected_status
    assert material["result_manual_decision_lane_status_ref"] == expected_status
    assert material["decision_lane_ref"] == expected_lane
    assert material["selected_next_required_step_ref"] == expected_next_ref
    assert material[candidate_key] is True
    assert material["exactly_one_rdb_result_branch"] is True
    assert sum(
        1
        for key in (
            "rdb_op03_confirmed_dhr_op05_manual_handoff_candidate",
            "rdb_op03_not_confirmed_retry_or_start_decision_required",
            "rdb_op03_waiting_external_claim_required",
            "rdb_op03_repair_required_after_dhr_op04_result",
            "rdb_op03_incomplete_unresolved_manual_hold",
            "rdb_op03_waiting_for_mrb08_result_closure",
            "rdb_op03_blocked_bodyfree_leak_promotion_or_autorun",
            "rdb_op03_repair_required_for_mrb08_branch_status_mismatch",
        )
        if material[key] is True
    ) == 1
    assert material["manual_decision_lane_resolved"] is True
    assert material["manual_decision_lane_resolved_bodyfree"] is True
    assert material["manual_decision_lane_resolver_only_no_materialization"] is True
    assert material["selected_next_stage_candidate_not_executed"] is True
    assert material["rdb_op03_does_not_materialize_branch_specific_manual_decision"] is True
    assert material["dhr_op05_called_here"] is False
    assert material["dhr_op06_called_here"] is False
    assert material["dmd_execution_started_here"] is False
    assert material["r52_actual_execution_started_here"] is False
    assert material["p8_question_substitution_allowed"] is False
    assert material["question_text_materialized"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP04_STEP_REF
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op03_dhr_op04_result_manual_decision_lane_resolver_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rdb_op03_routes_branch_status_mismatch_to_repair_lane_without_dhr_op05() -> None:
    op01 = _op01_from_op05(_op05_not_confirmed())
    op01["dhr_op04_result_status_ref"] = dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_CONFIRMED_BODYFREE_REF
    op02 = rdb.build_p7_r54_ahr_post_mrb08_rdb_op02_mrb_selected_branch_dhr_op04_result_status_consistency_check(
        mrb_op08_result_memo_closure_intake=op01,
    )
    material = rdb.build_p7_r54_ahr_post_mrb08_rdb_op03_dhr_op04_result_manual_decision_lane_resolver(
        mrb_branch_dhr_status_consistency_check=op02,
    )

    assert material["rdb_status_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_REPAIR_REQUIRED_FOR_MRB08_BRANCH_STATUS_MISMATCH_REF
    assert material["decision_lane_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_REPAIR_BRANCH_STATUS_MISMATCH_REF
    assert material["repair_candidate_present"] is True
    assert "dhr_op04_result_status_ref_does_not_map_to_mrb_selected_branch_ref" in material["branch_status_mismatch_refs"]
    assert material["dhr_op05_called_here"] is False
    assert material["p8_question_design_started"] is False
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op03_dhr_op04_result_manual_decision_lane_resolver_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rdb_op03_prioritizes_blocked_bodyfree_leak_or_promotion_before_lane_resolution() -> None:
    blocked_op08 = _op08_from_op05(
        _op05_confirmed(),
        result_memo_bodyfree={"question_text": "must not be copied", "body_free": True},
    )
    material = rdb.build_p7_r54_ahr_post_mrb08_rdb_op03_dhr_op04_result_manual_decision_lane_resolver(
        mrb_op08_result_memo_closure=blocked_op08,
    )

    assert material["rdb_status_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF
    assert material["decision_lane_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_BLOCKED_REF
    assert material["blocked_candidate_present"] is True
    assert material["dhr_op05_called_here"] is False
    assert material["p8_start_allowed"] is False
    assert "must not be copied" not in repr(material)
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op03_dhr_op04_result_manual_decision_lane_resolver_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rdb_op03_waits_when_mrb_op08_closure_is_missing() -> None:
    material = rdb.build_p7_r54_ahr_post_mrb08_rdb_op03_dhr_op04_result_manual_decision_lane_resolver()

    assert material["rdb_status_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_WAITING_FOR_MRB08_RESULT_CLOSURE_REF
    assert material["decision_lane_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_WAIT_MRB08_CLOSURE_REF
    assert material["unresolved_manual_hold_candidate_present"] is True
    assert material["dhr_op05_called_here"] is False
    assert material["p8_question_design_started"] is False
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op03_dhr_op04_result_manual_decision_lane_resolver_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rdb_op02_op03_contracts_reject_promotion_or_next_step_mutations() -> None:
    op02 = _op02_from_op05(_op05_confirmed())
    op02["dhr_op05_called_here"] = True
    with pytest.raises(ValueError):
        rdb.assert_p7_r54_ahr_post_mrb08_rdb_op02_mrb_selected_branch_dhr_op04_result_status_consistency_check_contract(op02)

    op03 = _op03_from_op05(_op05_confirmed())
    op03["next_required_step"] = rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_PREPARE_DHR_OP05_MANUAL_HANDOFF_DECISION_REF
    with pytest.raises(ValueError):
        rdb.assert_p7_r54_ahr_post_mrb08_rdb_op03_dhr_op04_result_manual_decision_lane_resolver_contract(op03)

    op03 = _op03_from_op05(_op05_confirmed())
    op03["rdb_op03_not_confirmed_retry_or_start_decision_required"] = True
    op03["exactly_one_rdb_result_branch"] = False
    with pytest.raises(ValueError):
        rdb.assert_p7_r54_ahr_post_mrb08_rdb_op03_dhr_op04_result_manual_decision_lane_resolver_contract(op03)


def test_rdb_op02_op03_full_title_aliases_match_short_builders_and_asserts() -> None:
    assert (
        rdb.build_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op02_mrb_selected_branch_dhr_op04_result_status_consistency_check
        is rdb.build_p7_r54_ahr_post_mrb08_rdb_op02_mrb_selected_branch_dhr_op04_result_status_consistency_check
    )
    assert (
        rdb.assert_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op02_mrb_selected_branch_dhr_op04_result_status_consistency_check_contract
        is rdb.assert_p7_r54_ahr_post_mrb08_rdb_op02_mrb_selected_branch_dhr_op04_result_status_consistency_check_contract
    )
    assert (
        rdb.build_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op03_dhr_op04_result_manual_decision_lane_resolver
        is rdb.build_p7_r54_ahr_post_mrb08_rdb_op03_dhr_op04_result_manual_decision_lane_resolver
    )
    assert (
        rdb.assert_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op03_dhr_op04_result_manual_decision_lane_resolver_contract
        is rdb.assert_p7_r54_ahr_post_mrb08_rdb_op03_dhr_op04_result_manual_decision_lane_resolver_contract
    )
