# -*- coding: utf-8 -*-
"""R16 contract tests for P7-HOLD-004 current backend-suite split execution plan material."""

from __future__ import annotations

import json

import pytest

from emlis_ai_p7_contracts import assert_p7_no_body_payload_or_contract_mutation
from emlis_ai_p7_hold004_backend_suite_group_inventory_plan import (
    P7_HOLD004_BACKEND_R2_R3_SOURCE_SNAPSHOT_REF,
    P7_HOLD004_BACKEND_SUITE_COMMAND_SHAPE_ID,
    P7_HOLD004_BACKEND_SUITE_DEFAULT_PYTEST_ARGS_ID,
    P7_HOLD004_BACKEND_SUITE_EXECUTION_MODE,
    P7_HOLD004_BACKEND_SUITE_EXECUTION_ORDER,
    P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID,
    P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_SCHEMA_VERSION,
    P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID,
    P7_HOLD004_BACKEND_SUITE_PYTEST_ENV_ID,
    P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_R2_R3_STEP,
    P7_HOLD004_BACKEND_SUITE_TOTAL_BATCH_COUNT,
    assert_p7_hold004_backend_suite_execution_plan_contract,
    build_p7_hold004_backend_suite_execution_plan,
    build_p7_hold004_backend_suite_group_inventory,
)

_SAMPLE_COMMENT_BODY = "これは実行plan materialに入れてはいけない本文です"
_SAMPLE_TERMINAL_OUTPUT = "pytest terminal output should not be retained"


def _plan_group_by_id(plan: dict[str, object], group_id: str) -> dict[str, object]:
    for group in plan["groups"]:  # type: ignore[index]
        if group["group_id"] == group_id:
            return group
    raise AssertionError(f"missing group: {group_id}")


def test_r16_execution_plan_material_defines_current_order_timeout_budget_and_batch_policy_without_execution_claims() -> None:
    inventory = build_p7_hold004_backend_suite_group_inventory()
    plan = build_p7_hold004_backend_suite_execution_plan(inventory=inventory)

    assert plan["schema_version"] == P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_SCHEMA_VERSION
    assert plan["phase"] == "P7_ProductQualityRunner_LongRunGate"
    assert plan["step"] == P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_R2_R3_STEP
    assert plan["implementation_step"] == P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_R2_R3_STEP
    assert plan["hold_id"] == "P7-HOLD-004"
    assert plan["plan_id"] == P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID
    assert plan["inventory_id"] == P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID
    assert plan["collect_baseline_id"] == "p7_hold004_backend_collect_baseline_20260615"
    assert plan["source_mode"] == "local_snapshot"
    assert plan["source_snapshot_ref"] == P7_HOLD004_BACKEND_R2_R3_SOURCE_SNAPSHOT_REF
    assert plan["git_checked"] is False
    assert plan["execution_mode"] == P7_HOLD004_BACKEND_SUITE_EXECUTION_MODE
    assert plan["pytest_env_id"] == P7_HOLD004_BACKEND_SUITE_PYTEST_ENV_ID
    assert plan["default_pytest_args_id"] == P7_HOLD004_BACKEND_SUITE_DEFAULT_PYTEST_ARGS_ID
    assert plan["command_shape_id"] == P7_HOLD004_BACKEND_SUITE_COMMAND_SHAPE_ID
    assert plan["group_count"] == 13
    assert plan["total_batch_count"] == P7_HOLD004_BACKEND_SUITE_TOTAL_BATCH_COUNT == 19
    assert [group["group_id"] for group in plan["groups"]] == list(P7_HOLD004_BACKEND_SUITE_EXECUTION_ORDER)

    assert plan["execution_started"] is False
    assert plan["group_run_results_recorded"] is False
    assert plan["terminal_output_retained"] is False
    assert plan["capture_run_and_confirmation_run_separated"] is True
    assert plan["current_collect_baseline_reconciled"] is True
    assert plan["previous_baseline_is_not_current"] is True
    assert plan["baseline_mismatch_blocks_execution"] is True

    group_02 = _plan_group_by_id(plan, "group_02_p7_hold004")
    assert group_02["execution_order_index"] == 1
    assert group_02["file_count"] == 19
    assert group_02["test_item_count"] == 252
    assert group_02["timeout_budget_sec"] == 120
    assert group_02["batch_count"] == 1
    assert group_02["batch_ids"] == ["group_02_p7_hold004_batch_01"]

    group_10 = _plan_group_by_id(plan, "group_10_two_stage_public_recovery")
    assert group_10["timeout_budget_sec"] == 180
    assert group_10["batch_count"] == 2

    group_11 = _plan_group_by_id(plan, "group_11_emlis_runtime_other")
    assert group_11["timeout_budget_sec"] == 240
    assert group_11["batch_count"] == 6
    assert group_11["batch_policy"] == "required_batch_by_30_files_or_250_tests"
    assert group_11["batch_ids"] == [
        "group_11_emlis_runtime_other_batch_01",
        "group_11_emlis_runtime_other_batch_02",
        "group_11_emlis_runtime_other_batch_03",
        "group_11_emlis_runtime_other_batch_04",
        "group_11_emlis_runtime_other_batch_05",
        "group_11_emlis_runtime_other_batch_06",
    ]

    assert all(group["capture_run_maxfail_1"] is True for group in plan["groups"])
    assert all(group["confirmation_run_maxfail_1"] is False for group in plan["groups"])
    assert all(group["execution_required"] is True for group in plan["groups"])
    assert all(group["terminal_output_retained"] is False for group in plan["groups"])
    assert all(group["can_claim_full_backend_suite_green"] is False for group in plan["groups"])
    assert all(group["split_green_can_close_p7_hold004"] is False for group in plan["groups"])
    assert all(group["release_allowed"] is False for group in plan["groups"])
    assert all(group["body_free"] is True for group in plan["groups"])

    assert plan["full_backend_suite_green_confirmed"] is False
    assert plan["full_backend_suite_green_claim_allowed"] is False
    assert plan["split_green_is_full_backend_suite_green"] is False
    assert plan["split_green_can_close_p7_hold004"] is False
    assert plan["hold004_close_allowed"] is False
    assert plan["p7_complete"] is False
    assert plan["p8_start_allowed"] is False
    assert plan["release_allowed"] is False
    assert "P7-HOLD-004" in plan["unresolved_hold_refs"]
    assert "full_backend_suite_green_unconfirmed" in plan["required_followup_fixes"]
    assert all(value is False for value in plan["public_contract"].values())
    assert all(value is False for value in plan["body_free_markers"].values())
    assert plan["body_free"] is True

    serialized = json.dumps(plan, ensure_ascii=False, sort_keys=True)
    assert _SAMPLE_COMMENT_BODY not in serialized
    assert _SAMPLE_TERMINAL_OUTPUT not in serialized
    assert "terminal_output" not in plan
    assert "stdout" not in plan
    assert "stderr" not in plan
    assert "traceback" not in plan

    assert_p7_hold004_backend_suite_execution_plan_contract(plan)
    assert_p7_no_body_payload_or_contract_mutation(plan, source="r3_backend_execution_plan_test")


def test_r16_execution_plan_rejects_invalid_inventory_before_building_plan() -> None:
    inventory = build_p7_hold004_backend_suite_group_inventory()
    inventory["total_group_test_item_count"] = 2855

    with pytest.raises(ValueError):
        build_p7_hold004_backend_suite_execution_plan(inventory=inventory)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    (
        ("group_count", 12),
        ("total_batch_count", 18),
        ("execution_started", True),
        ("group_run_results_recorded", True),
        ("terminal_output_retained", True),
        ("capture_run_and_confirmation_run_separated", False),
        ("full_backend_suite_green_confirmed", True),
        ("split_green_is_full_backend_suite_green", True),
        ("split_green_can_close_p7_hold004", True),
        ("hold004_close_allowed", True),
        ("p7_complete", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ),
)
def test_r16_execution_plan_contract_rejects_execution_or_release_mutation(field: str, bad_value: object) -> None:
    plan = build_p7_hold004_backend_suite_execution_plan()
    plan[field] = bad_value

    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_execution_plan_contract(plan)


def test_r16_execution_plan_contract_rejects_group_order_batch_count_or_timeout_mutation() -> None:
    plan = build_p7_hold004_backend_suite_execution_plan()
    plan["groups"] = list(reversed(plan["groups"]))
    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_execution_plan_contract(plan)

    plan = build_p7_hold004_backend_suite_execution_plan()
    _plan_group_by_id(plan, "group_11_emlis_runtime_other")["batch_count"] = 1
    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_execution_plan_contract(plan)

    plan = build_p7_hold004_backend_suite_execution_plan()
    _plan_group_by_id(plan, "group_11_emlis_runtime_other")["batch_ids"] = ["group_11_emlis_runtime_other_batch_01"]
    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_execution_plan_contract(plan)

    plan = build_p7_hold004_backend_suite_execution_plan()
    _plan_group_by_id(plan, "group_02_p7_hold004")["file_count"] = 10
    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_execution_plan_contract(plan)

    plan = build_p7_hold004_backend_suite_execution_plan()
    _plan_group_by_id(plan, "group_02_p7_hold004")["test_item_count"] = 69
    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_execution_plan_contract(plan)

    plan = build_p7_hold004_backend_suite_execution_plan()
    _plan_group_by_id(plan, "group_02_p7_hold004")["timeout_budget_sec"] = 1
    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_execution_plan_contract(plan)

    for flag in (
        "current_collect_baseline_reconciled",
        "previous_baseline_is_not_current",
        "baseline_mismatch_blocks_execution",
    ):
        plan = build_p7_hold004_backend_suite_execution_plan()
        plan[flag] = False
        with pytest.raises(ValueError):
            assert_p7_hold004_backend_suite_execution_plan_contract(plan)


@pytest.mark.parametrize(
    ("group_id", "field", "bad_value"),
    (
        ("group_02_p7_hold004", "capture_run_maxfail_1", False),
        ("group_02_p7_hold004", "confirmation_run_maxfail_1", True),
        ("group_02_p7_hold004", "execution_required", False),
        ("group_02_p7_hold004", "terminal_output_retained", True),
        ("group_02_p7_hold004", "can_claim_full_backend_suite_green", True),
        ("group_02_p7_hold004", "split_green_can_close_p7_hold004", True),
        ("group_02_p7_hold004", "release_allowed", True),
    ),
)
def test_r16_execution_plan_contract_rejects_group_level_promotion_or_run_shape_mutation(
    group_id: str, field: str, bad_value: object
) -> None:
    plan = build_p7_hold004_backend_suite_execution_plan()
    _plan_group_by_id(plan, group_id)[field] = bad_value

    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_execution_plan_contract(plan)


@pytest.mark.parametrize(
    "marker_key",
    (
        "raw_input_included",
        "history_raw_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "reviewer_free_text_included",
        "terminal_output_included",
    ),
)
def test_r16_execution_plan_contract_rejects_body_free_marker_or_body_payload(marker_key: str) -> None:
    plan = build_p7_hold004_backend_suite_execution_plan()
    plan["body_free_markers"][marker_key] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_execution_plan_contract(plan)

    plan = build_p7_hold004_backend_suite_execution_plan()
    plan["terminal_output"] = _SAMPLE_TERMINAL_OUTPUT
    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_execution_plan_contract(plan)
