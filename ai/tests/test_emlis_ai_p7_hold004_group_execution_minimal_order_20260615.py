# -*- coding: utf-8 -*-
"""P7-HOLD-004 R16 current minimal group execution confirmation-order tests."""

from __future__ import annotations

import copy
import json

import pytest

from emlis_ai_p7_hold004_backend_suite_group_inventory_plan import (
    P7_HOLD004_BACKEND_SUITE_EXECUTION_ORDER,
    P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID,
    P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_SCHEMA_VERSION,
    P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID,
    P7_HOLD004_BACKEND_SUITE_TOTAL_BATCH_COUNT,
)
from emlis_ai_p7_hold004_group_execution_minimal_order import (
    P7_HOLD004_GROUP_EXECUTION_MINIMAL_ORDER_ID,
    P7_HOLD004_GROUP_EXECUTION_MINIMAL_ORDER_SCHEMA_VERSION,
    P7_HOLD004_GROUP_EXECUTION_MINIMAL_ORDER_STEP,
    assert_p7_hold004_group_execution_minimal_order_contract,
    build_p7_hold004_group_execution_minimal_order,
)

_SECRET_BODY_SENTINEL = "R11 raw body must never be serialized"


def test_r16_minimal_confirmation_order_matches_current_design_order_and_keeps_execution_not_started() -> None:
    order = build_p7_hold004_group_execution_minimal_order()
    assert_p7_hold004_group_execution_minimal_order_contract(order)

    assert order["schema_version"] == P7_HOLD004_GROUP_EXECUTION_MINIMAL_ORDER_SCHEMA_VERSION
    assert order["implementation_step"] == P7_HOLD004_GROUP_EXECUTION_MINIMAL_ORDER_STEP
    assert order["material_id"] == P7_HOLD004_GROUP_EXECUTION_MINIMAL_ORDER_ID
    assert order["execution_plan_schema_version"] == P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_SCHEMA_VERSION
    assert order["execution_plan_id"] == P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID
    assert order["inventory_id"] == P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID
    assert order["collect_baseline_id"] == "p7_hold004_backend_collect_baseline_20260615_received_148"
    assert order["minimal_execution_order"] == list(P7_HOLD004_BACKEND_SUITE_EXECUTION_ORDER)
    assert order["group_count"] == 13
    assert order["total_batch_count"] == P7_HOLD004_BACKEND_SUITE_TOTAL_BATCH_COUNT
    assert order["group_execution_started"] is False
    assert order["group_run_results_recorded"] is False
    assert order["terminal_output_retained"] is False
    assert order["raw_traceback_included"] is False
    assert order["stop_on_first_fail_or_timeout"] is True
    assert order["continue_after_fail_or_timeout_requires_new_repair_plan"] is True
    assert order["subsequent_groups_not_green_when_blocked"] is True
    assert order["capture_run_and_confirmation_run_separated"] is True
    assert order["current_collect_baseline_reconciled"] is True
    assert order["previous_baseline_is_not_current"] is True
    assert order["baseline_mismatch_blocks_execution"] is True
    assert "P7-HOLD-004" in order["unresolved_hold_refs"]
    assert order["release_allowed"] is False


def test_r16_minimal_confirmation_groups_are_capture_first_current_counted_and_batched_for_group_11() -> None:
    order = build_p7_hold004_group_execution_minimal_order()
    groups = order["groups"]

    assert [group["group_id"] for group in groups] == list(P7_HOLD004_BACKEND_SUITE_EXECUTION_ORDER)
    assert groups[0]["group_id"] == "group_02_p7_hold004"
    assert groups[0]["file_count"] == 19
    assert groups[0]["test_item_count"] == 252
    assert groups[1]["group_id"] == "group_03_p7_core_matrix_handoff"
    assert groups[2]["group_id"] == "group_04_complete_product_quality"
    assert groups[3]["group_id"] == "group_01_contract"

    group_10 = next(group for group in groups if group["group_id"] == "group_10_two_stage_public_recovery")
    group_11 = next(group for group in groups if group["group_id"] == "group_11_emlis_runtime_other")
    assert group_10["batch_count"] == 2
    assert group_11["batch_count"] == 6
    assert len(group_11["batch_ids"]) == 6

    for group in groups:
        assert group["capture_run_maxfail_1"] is True
        assert group["confirmation_run_maxfail_1"] is False
        assert group["run_kind_first"] == "capture_run"
        assert group["run_kind_after_repair"] == "confirmation_run"
        assert group["failure_or_timeout_policy"] == "materialize_first_red_or_timeout_then_stop_green_claims"
        assert group["can_claim_group_green_only_after_recorded_pass"] is True
        assert group["can_claim_full_backend_suite_green"] is False
        assert group["split_green_can_close_p7_hold004"] is False
        assert group["terminal_output_retained"] is False
        assert group["execution_result_recorded"] is False
        assert group["release_allowed"] is False
        assert group["body_free"] is True


def test_r16_contract_rejects_order_mutations_that_skip_group_split_or_promote_release() -> None:
    order = build_p7_hold004_group_execution_minimal_order()

    reordered = copy.deepcopy(order)
    reordered["minimal_execution_order"][0], reordered["minimal_execution_order"][1] = (
        reordered["minimal_execution_order"][1],
        reordered["minimal_execution_order"][0],
    )
    with pytest.raises(ValueError):
        assert_p7_hold004_group_execution_minimal_order_contract(reordered)

    one_shot_like = copy.deepcopy(order)
    one_shot_like["stop_on_first_fail_or_timeout"] = False
    with pytest.raises(ValueError):
        assert_p7_hold004_group_execution_minimal_order_contract(one_shot_like)

    single_batch_group_11 = copy.deepcopy(order)
    group_11 = next(group for group in single_batch_group_11["groups"] if group["group_id"] == "group_11_emlis_runtime_other")
    group_11["batch_count"] = 1
    group_11["batch_ids"] = ["group_11_emlis_runtime_other_batch_01"]
    single_batch_group_11["total_batch_count"] = P7_HOLD004_BACKEND_SUITE_TOTAL_BATCH_COUNT - 5
    with pytest.raises(ValueError):
        assert_p7_hold004_group_execution_minimal_order_contract(single_batch_group_11)

    stale_baseline_like = copy.deepcopy(order)
    stale_baseline_like["collect_baseline_id"] = "p7_hold004_backend_collect_baseline_20260614"
    with pytest.raises(ValueError):
        assert_p7_hold004_group_execution_minimal_order_contract(stale_baseline_like)

    mismatch_not_blocked = copy.deepcopy(order)
    mismatch_not_blocked["baseline_mismatch_blocks_execution"] = False
    with pytest.raises(ValueError):
        assert_p7_hold004_group_execution_minimal_order_contract(mismatch_not_blocked)

    group_02_old_count_like = copy.deepcopy(order)
    group_02 = next(group for group in group_02_old_count_like["groups"] if group["group_id"] == "group_02_p7_hold004")
    group_02["test_item_count"] = 69
    with pytest.raises(ValueError):
        assert_p7_hold004_group_execution_minimal_order_contract(group_02_old_count_like)

    release_mutated = copy.deepcopy(order)
    release_mutated["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_group_execution_minimal_order_contract(release_mutated)

    body_mutated = copy.deepcopy(order)
    body_mutated["comment_text"] = _SECRET_BODY_SENTINEL
    with pytest.raises(ValueError):
        assert_p7_hold004_group_execution_minimal_order_contract(body_mutated)


def test_r16_minimal_confirmation_order_remains_body_free_and_contains_no_terminal_output() -> None:
    order = build_p7_hold004_group_execution_minimal_order()
    serialized = json.dumps(order, ensure_ascii=False, sort_keys=True)

    assert _SECRET_BODY_SENTINEL not in serialized
    assert "comment_text" not in order
    assert "traceback" not in order
    assert "terminal_output" not in order
    assert order["body_free"] is True
    assert all(value is False for value in order["public_contract"].values())
    assert all(value is False for value in order["body_free_markers"].values())
