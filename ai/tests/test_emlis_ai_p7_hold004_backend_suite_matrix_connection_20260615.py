# -*- coding: utf-8 -*-

import copy

import pytest

from emlis_ai_p7_hold004_backend_suite_execution_results import (
    P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_SCHEMA_VERSION,
    assert_p7_hold004_backend_suite_execution_summary_contract,
    build_p7_hold004_backend_suite_execution_summary,
    build_p7_hold004_backend_suite_group_run_result,
)
from emlis_ai_p7_hold004_backend_suite_group_inventory_plan import (
    P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID,
    P7_HOLD004_BACKEND_SUITE_GROUP_DEFINITIONS,
    P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID,
)
from emlis_ai_p7_hold004_backend_suite_split_consistency import (
    P7_HOLD004_BACKEND_COLLECT_BASELINE_ID,
    P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT,
    P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT,
)
from emlis_ai_p7_hold_matrix import (
    P7_BACKEND_SUITE_SPLIT_MATRIX_SCHEMA_VERSION,
    P7_R10_HOLD_MATRIX_SCHEMA_VERSION,
    assert_p7_backend_suite_split_matrix_contract,
    assert_p7_r10_hold_matrix_contract,
    build_p7_backend_suite_split_matrix,
    build_p7_r10_hold_matrix,
)
from emlis_ai_p7_red_closure_classification import (
    P7_RED_CLOSURE_CLASSIFICATION_MATRIX_SCHEMA_VERSION,
    build_p7_red_closure_classification_matrix,
)
from emlis_ai_p7_timeout_isolation import build_p7_connection_e2e_r13_passed_observation_result


def _observed_connection_pass_without_red_closure_material() -> dict[str, object]:
    return {
        "p7_core_contract": {"result_kind": "passed", "test_count_observed": 50},
        "existing_p7_reuse_contract": {"result_kind": "passed", "test_count_observed": 31},
        "heavy_isolated_positive_recovery_red": {"result_kind": "closed_confirmed", "test_count_observed": 14},
        "heavy_isolated_product_quality_connection_timeout": {
            "result_kind": "passed",
            "test_count_observed": 1,
        },
        "full_backend_suite": {"result_kind": "not_run", "test_count_observed": 0},
    }


def _red003_closed_matrix() -> dict[str, object]:
    return build_p7_red_closure_classification_matrix(
        connection_timeout_isolation_result=build_p7_connection_e2e_r13_passed_observation_result()
    )


def _assert_current_baseline_connection(material: dict[str, object]) -> None:
    assert material["backend_suite_execution_summary_collect_baseline_id"] == P7_HOLD004_BACKEND_COLLECT_BASELINE_ID
    assert material["backend_suite_execution_summary_inventory_id"] == P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID
    assert material["backend_suite_execution_summary_plan_id"] == P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID
    assert material["current_collect_baseline_connected"] is True
    assert material["current_group_inventory_connected"] is True
    assert material["current_execution_plan_connected"] is True
    assert material["old_baseline_not_used_as_current"] is True
    assert material["backend_suite_group_02_file_count"] == 19
    assert material["backend_suite_group_02_test_item_count"] == 252
    assert material["backend_suite_group_02_count_current"] is True
    connection = material["matrix_current_baseline_connection"]
    assert connection["collect_baseline_id"] == P7_HOLD004_BACKEND_COLLECT_BASELINE_ID
    assert connection["group_inventory_id"] == P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID
    assert connection["execution_plan_id"] == P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID
    assert connection["current_collect_file_count"] == P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT
    assert connection["current_collect_test_item_count"] == P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT
    assert connection["group_02_file_count"] == 19
    assert connection["group_02_test_item_count"] == 252
    assert connection["old_baseline_used_as_current"] is False


def _all_split_groups_green_summary() -> dict[str, object]:
    results = []
    for definition in P7_HOLD004_BACKEND_SUITE_GROUP_DEFINITIONS:
        group_id = str(definition["group_id"])
        batch_count = int(definition["planned_batch_count"])
        for batch_index in range(1, batch_count + 1):
            results.append(
                build_p7_hold004_backend_suite_group_run_result(
                    group_id=group_id,
                    batch_id=f"{group_id}_batch_{batch_index:02d}",
                    status="PASS",
                    passed=1,
                    failed=0,
                    skipped=0,
                    warnings=0,
                    errors=0,
                )
            )
    summary = build_p7_hold004_backend_suite_execution_summary(run_results=results)
    assert_p7_hold004_backend_suite_execution_summary_contract(summary)
    assert summary["split_all_groups_green_confirmed"] is True
    return summary


def test_r6_default_backend_split_does_not_close_red003_from_connection_e2e_pass_alone():
    matrix = build_p7_backend_suite_split_matrix(
        observed_results=_observed_connection_pass_without_red_closure_material()
    )
    assert_p7_backend_suite_split_matrix_contract(matrix)

    assert matrix["schema_version"] == P7_BACKEND_SUITE_SPLIT_MATRIX_SCHEMA_VERSION
    assert matrix["red_closure_classification_connected"] is False
    assert matrix["group_statuses"]["product_quality_connection_e2e"] == "blocked"
    assert "P7-RED-003" in matrix["unresolved_red_refs"]
    assert "P7-RED-003" not in matrix["closed_red_refs"]
    connection_group = next(group for group in matrix["groups"] if group["group_id"] == "product_quality_connection_e2e")
    assert "connection_e2e_passed_without_red_closure_material" in connection_group["reason_codes"]
    assert matrix["full_backend_suite_green_confirmed"] is False
    assert matrix["release_allowed"] is False


def test_r6_backend_split_consumes_structured_red003_closure_but_keeps_hold004_and_full_suite_false():
    matrix = build_p7_backend_suite_split_matrix(
        observed_results=_observed_connection_pass_without_red_closure_material(),
        red_closure_classification_matrix=_red003_closed_matrix(),
    )
    assert_p7_backend_suite_split_matrix_contract(matrix)

    assert matrix["red_closure_classification_connected"] is True
    assert matrix["red_closure_classification_schema_version"] == P7_RED_CLOSURE_CLASSIFICATION_MATRIX_SCHEMA_VERSION
    assert matrix["product_quality_connection_timeout_closed"] is True
    assert matrix["product_quality_connection_e2e_status"] == "closed_confirmed"
    assert matrix["group_statuses"]["product_quality_connection_e2e"] == "closed_confirmed"
    assert "P7-RED-003" in matrix["closed_red_refs"]
    assert "P7-RED-003" not in matrix["unresolved_red_refs"]
    connection_group = next(group for group in matrix["groups"] if group["group_id"] == "product_quality_connection_e2e")
    assert connection_group["red_refs"] == []
    assert connection_group["green_claim_allowed"] is False
    assert connection_group["can_claim_full_backend_suite_green"] is False
    assert "P7-HOLD-004" in matrix["unresolved_hold_refs"]
    assert matrix["full_backend_suite_green_confirmed"] is False
    assert matrix["split_green_is_full_backend_suite_green"] is False
    assert matrix["split_green_can_close_p7_hold004"] is False
    assert matrix["release_allowed"] is False


def test_r6_backend_split_connects_execution_summary_without_promoting_split_all_green():
    summary = _all_split_groups_green_summary()
    matrix = build_p7_backend_suite_split_matrix(
        backend_suite_execution_summary=summary,
        red_closure_classification_matrix=_red003_closed_matrix(),
    )
    assert_p7_backend_suite_split_matrix_contract(matrix)

    assert matrix["backend_suite_execution_summary_connected"] is True
    assert matrix["backend_suite_execution_summary_schema_version"] == P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_SCHEMA_VERSION
    _assert_current_baseline_connection(matrix)
    assert matrix["backend_suite_execution_summary_split_all_groups_green_confirmed"] is True
    assert matrix["split_all_groups_green_confirmed"] is True
    assert matrix["group_statuses"]["full_backend_suite"] == "hold_unconfirmed"
    assert matrix["full_backend_suite_green_confirmed"] is False
    assert matrix["split_green_is_full_backend_suite_green"] is False
    assert matrix["split_green_can_close_p7_hold004"] is False
    assert "split_green_is_not_full_backend_suite_green" in matrix["required_followup_fixes"]
    assert "P7-HOLD-004" in matrix["unresolved_hold_refs"]
    assert matrix["release_allowed"] is False


def test_r7_r10_hold_matrix_mirrors_backend_split_red003_closure_and_execution_summary():
    summary = _all_split_groups_green_summary()
    matrix = build_p7_r10_hold_matrix(
        backend_suite_execution_summary=summary,
        red_closure_classification_matrix=_red003_closed_matrix(),
    )
    assert_p7_r10_hold_matrix_contract(matrix)

    assert matrix["schema_version"] == P7_R10_HOLD_MATRIX_SCHEMA_VERSION
    assert matrix["backend_suite_execution_summary_connected"] is True
    assert matrix["backend_suite_execution_summary_schema_version"] == P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_SCHEMA_VERSION
    _assert_current_baseline_connection(matrix)
    assert matrix["backend_suite_execution_summary_split_all_groups_green_confirmed"] is True
    assert matrix["red_closure_classification_connected"] is True
    assert matrix["product_quality_connection_timeout_closed"] is True
    assert matrix["product_quality_connection_e2e_status"] == "closed_confirmed"
    assert "P7-RED-003" in matrix["closed_red_refs"]
    assert "P7-RED-003" not in matrix["unresolved_red_refs"]
    assert {"P7-HOLD-003", "P7-HOLD-004"}.issubset(set(matrix["unresolved_hold_refs"]))
    assert matrix["full_backend_suite_green_confirmed"] is False
    assert matrix["split_green_is_full_backend_suite_green"] is False
    assert matrix["split_green_promoted_to_full_suite_green"] is False
    assert matrix["release_allowed"] is False


def test_r7_r10_contract_rejects_red003_closed_unresolved_mismatch_and_split_promotion():
    matrix = build_p7_r10_hold_matrix(
        backend_suite_execution_summary=_all_split_groups_green_summary(),
        red_closure_classification_matrix=_red003_closed_matrix(),
    )

    red_mismatch = copy.deepcopy(matrix)
    red_mismatch["unresolved_red_refs"] = ["P7-RED-003"]
    with pytest.raises(ValueError):
        assert_p7_r10_hold_matrix_contract(red_mismatch)

    split_mutated = copy.deepcopy(matrix)
    split_mutated["split_green_promoted_to_full_suite_green"] = True
    with pytest.raises(ValueError):
        assert_p7_r10_hold_matrix_contract(split_mutated)

    release_mutated = copy.deepcopy(matrix)
    release_mutated["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_r10_hold_matrix_contract(release_mutated)
