# -*- coding: utf-8 -*-
"""P7-HOLD-004 R8/R9 release handoff / validation matrix connection tests."""

from __future__ import annotations

import copy
import json

import pytest

from emlis_ai_p7_hold004_backend_suite_execution_results import (
    P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_SCHEMA_VERSION,
    P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_ITEM_FINGERPRINT_MISMATCH,
    P7_HOLD004_RECEIVED_SNAPSHOT_ITEM_FINGERPRINT_MISMATCH_BLOCKER_REF,
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
from emlis_ai_p7_red_closure_classification import build_p7_red_closure_classification_matrix
from emlis_ai_p7_release_handoff import assert_p7_release_decision_handoff_contract, build_p7_release_decision_handoff
from emlis_ai_p7_timeout_isolation import build_p7_connection_e2e_r13_passed_observation_result
from emlis_ai_p7_validation_matrix import (
    P7_HOLD004_MATRIX_CONSISTENCY_REPORT_SCHEMA_VERSION,
    assert_p7_validation_regression_matrix_contract,
    build_p7_validation_regression_matrix,
)

_SECRET_BODY_SENTINEL = "R8/R9 raw body must never be serialized"


def _assert_current_baseline_connection(material: dict[str, object]) -> None:
    assert material["backend_suite_execution_summary_collect_baseline_id"] == P7_HOLD004_BACKEND_COLLECT_BASELINE_ID
    assert material["backend_suite_execution_summary_inventory_id"] == P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID
    assert material["backend_suite_execution_summary_plan_id"] == P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID
    assert material["current_collect_baseline_connected"] is True
    assert material["current_group_inventory_connected"] is True
    assert material["current_execution_plan_connected"] is True
    assert material["old_baseline_not_used_as_current"] is True
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
    assert material["official_group_02_capture_readiness_status"] == (
        P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_ITEM_FINGERPRINT_MISMATCH
    )
    assert material["official_group_02_capture_blocked"] is True
    assert material["official_group_02_capture_run_allowed"] is False
    assert material["official_group_02_capture_result_recording_allowed"] is False
    assert material["received_snapshot_baseline_fingerprint_reconciled"] is False
    assert material["received_snapshot_item_fingerprint_mismatch_unresolved"] is True
    assert P7_HOLD004_RECEIVED_SNAPSHOT_ITEM_FINGERPRINT_MISMATCH_BLOCKER_REF in material["received_snapshot_blocker_refs"]
    followup_fixes = material.get(
        "required_followup_fixes",
        material.get("summary", {}).get("hold004_required_followup_fixes", []),
    )
    assert P7_HOLD004_RECEIVED_SNAPSHOT_ITEM_FINGERPRINT_MISMATCH_BLOCKER_REF in followup_fixes


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


def _red003_closed_matrix() -> dict[str, object]:
    return build_p7_red_closure_classification_matrix(
        connection_timeout_isolation_result=build_p7_connection_e2e_r13_passed_observation_result()
    )


def _matrix_consistency_pass_report() -> dict[str, object]:
    return {
        "schema_version": P7_HOLD004_MATRIX_CONSISTENCY_REPORT_SCHEMA_VERSION,
        "phase": "P7_ProductQualityRunner_LongRunGate",
        "hold_id": "P7-HOLD-004",
        "report_id": "p7_hold004_matrix_consistency_report_test_material_20260615",
        "consistency_status": "PASS",
        "checks": {
            "red003_closure_consistent": True,
            "step5_red_consistent": True,
            "hold004_preserved_across_matrices": True,
            "current_collect_baseline_connected": True,
            "current_group_inventory_connected": True,
            "current_execution_plan_connected": True,
            "old_baseline_not_used_as_current": True,
            "backend_suite_group_02_count_current": True,
            "full_backend_suite_green_false_across_matrices": True,
            "split_green_not_promoted": True,
            "release_allowed_false_across_matrices": True,
            "p8_start_allowed_false_across_matrices": True,
            "body_free_markers_false_across_matrices": True,
        },
        "unresolved_red_refs": [],
        "unresolved_hold_refs": ["P7-HOLD-001", "P7-HOLD-002", "P7-HOLD-003", "P7-HOLD-004"],
        "required_followup_fixes": [
            "full_backend_suite_green_unconfirmed",
            "real_device_submit_modal_readfeel_unverified",
            "p5_human_qa_review_required",
        ],
        "current_collect_baseline_connected": True,
        "current_group_inventory_connected": True,
        "current_execution_plan_connected": True,
        "old_baseline_not_used_as_current": True,
        "backend_suite_group_02_count_current": True,
        "backend_suite_execution_summary_collect_baseline_id": P7_HOLD004_BACKEND_COLLECT_BASELINE_ID,
        "backend_suite_execution_summary_inventory_id": P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID,
        "backend_suite_execution_summary_plan_id": P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID,
        "matrix_current_baseline_connection": {
            "collect_baseline_id": P7_HOLD004_BACKEND_COLLECT_BASELINE_ID,
            "group_inventory_id": P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID,
            "execution_plan_id": P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID,
            "execution_summary_id": "p7_hold004_backend_suite_execution_summary_20260615",
            "current_collect_file_count": P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT,
            "current_collect_test_item_count": P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT,
            "group_02_file_count": 19,
            "group_02_test_item_count": 252,
            "old_baseline_id": "p7_hold004_backend_collect_baseline_20260614",
            "old_baseline_used_as_current": False,
            "full_backend_suite_green_confirmed": False,
            "release_allowed": False,
            "body_free": True,
        },
        "release_allowed": False,
        "p8_start_allowed": False,
        "body_free": True,
    }


def _rows_by_kind(matrix: dict[str, object]) -> dict[str, dict[str, object]]:
    return {str(row["check_kind"]): row for row in matrix["matrix_rows"]}  # type: ignore[index]


def test_r8_release_handoff_connects_execution_summary_without_promoting_release_or_full_suite() -> None:
    handoff = build_p7_release_decision_handoff(
        backend_suite_execution_summary=_all_split_groups_green_summary(),
        red_closure_classification=_red003_closed_matrix(),
    )
    assert_p7_release_decision_handoff_contract(handoff)

    assert handoff["backend_suite_execution_summary_connected"] is True
    assert handoff["backend_suite_execution_summary_schema_version"] == P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_SCHEMA_VERSION
    _assert_current_baseline_connection(handoff)
    assert handoff["backend_suite_execution_summary_split_all_groups_green_confirmed"] is True
    assert handoff["split_all_groups_green_confirmed"] is True
    assert handoff["full_backend_suite_green_confirmed"] is False
    assert handoff["split_green_is_full_backend_suite_green"] is False
    assert handoff["split_green_can_close_p7_hold004"] is False
    assert handoff["hold004_close_allowed"] is False
    assert handoff["manual_hold_status"]["p7_complete_claim_allowed"] is False
    assert handoff["manual_hold_status"]["p8_start_allowed"] is False
    assert handoff["release_allowed"] is False
    assert "P7-RED-003" in handoff["closed_red_refs"]
    assert "P7-RED-003" not in handoff["unresolved_red_refs"]
    assert "P7-HOLD-004" in handoff["unresolved_hold_refs"]
    assert "split_green_is_not_full_backend_suite_green" in handoff["required_followup_fixes"]


def test_r9_validation_matrix_connects_execution_summary_row_and_keeps_hold004_open() -> None:
    matrix = build_p7_validation_regression_matrix(
        backend_suite_execution_summary=_all_split_groups_green_summary(),
        red_closure_classification_matrix=_red003_closed_matrix(),
    )
    assert_p7_validation_regression_matrix_contract(matrix)

    rows_by_kind = _rows_by_kind(matrix)
    readiness_row = rows_by_kind["official_group02_capture_readiness"]
    assert readiness_row["observed_status"] == "BLOCKED"
    assert readiness_row["green_claim_allowed"] is False
    assert readiness_row["release_allowed"] is False
    assert "P7-HOLD-004" in readiness_row["hold_refs"]
    assert P7_HOLD004_RECEIVED_SNAPSHOT_ITEM_FINGERPRINT_MISMATCH_BLOCKER_REF in readiness_row["reason_codes"]

    execution_row = rows_by_kind["backend_suite_split_execution_summary"]
    assert execution_row["observed_status"] == "PASSED_ISOLATED"
    assert execution_row["green_claim_allowed"] is False
    assert execution_row["release_allowed"] is False
    assert "P7-HOLD-004" in execution_row["hold_refs"]
    assert "split_green_is_not_full_backend_suite_green" in execution_row["reason_codes"]

    assert matrix["backend_suite_execution_summary_connected"] is True
    assert matrix["backend_suite_execution_summary_schema_version"] == P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_SCHEMA_VERSION
    _assert_current_baseline_connection(matrix)
    assert matrix["backend_suite_execution_summary_split_all_groups_green_confirmed"] is True
    assert matrix["summary"]["full_backend_suite_green_confirmed"] is False
    assert matrix["summary"]["split_green_can_close_p7_hold004"] is False
    assert matrix["summary"]["split_green_promoted_to_full_suite_green"] is False
    assert matrix["summary"]["p7_complete_claim_allowed"] is False
    assert matrix["summary"]["p8_start_allowed"] is False
    assert matrix["release_allowed"] is False
    assert "P7-HOLD-004" in matrix["unresolved_hold_refs"]


def test_r9_validation_matrix_accepts_matrix_consistency_report_as_material_not_release_permission() -> None:
    matrix = build_p7_validation_regression_matrix(
        backend_suite_execution_summary=_all_split_groups_green_summary(),
        red_closure_classification_matrix=_red003_closed_matrix(),
        matrix_consistency_report=_matrix_consistency_pass_report(),
    )
    assert_p7_validation_regression_matrix_contract(matrix)

    rows_by_kind = _rows_by_kind(matrix)
    readiness_row = rows_by_kind["official_group02_capture_readiness"]
    assert readiness_row["observed_status"] == "BLOCKED"
    assert P7_HOLD004_RECEIVED_SNAPSHOT_ITEM_FINGERPRINT_MISMATCH_BLOCKER_REF in readiness_row["reason_codes"]

    consistency_row = rows_by_kind["matrix_consistency_report"]
    assert consistency_row["observed_status"] == "PASS"
    assert consistency_row["green_claim_allowed"] is False
    assert consistency_row["release_allowed"] is False
    assert "P7-HOLD-004" in consistency_row["hold_refs"]
    assert matrix["matrix_consistency_report_connected"] is True
    assert matrix["matrix_consistency_report_schema_version"] == P7_HOLD004_MATRIX_CONSISTENCY_REPORT_SCHEMA_VERSION
    assert matrix["summary"]["matrix_consistency_report_can_allow_release"] is False
    assert matrix["summary"]["current_collect_baseline_connected"] is True
    assert matrix["summary"]["current_group_inventory_connected"] is True
    assert matrix["summary"]["current_execution_plan_connected"] is True
    assert matrix["summary"]["old_baseline_not_used_as_current"] is True
    assert matrix["summary"]["backend_suite_group_02_count_current"] is True
    assert matrix["summary"]["release_allowed"] is False


def test_r8_r9_contracts_reject_split_green_release_or_full_suite_promotion_mutations() -> None:
    handoff = build_p7_release_decision_handoff(backend_suite_execution_summary=_all_split_groups_green_summary())

    schema_mutated = copy.deepcopy(handoff)
    schema_mutated["backend_suite_execution_summary_schema_version"] = "bad.schema"
    with pytest.raises(ValueError):
        assert_p7_release_decision_handoff_contract(schema_mutated)

    split_close_mutated = copy.deepcopy(handoff)
    split_close_mutated["split_green_can_close_p7_hold004"] = True
    with pytest.raises(ValueError):
        assert_p7_release_decision_handoff_contract(split_close_mutated)

    matrix = build_p7_validation_regression_matrix(
        backend_suite_execution_summary=_all_split_groups_green_summary(),
        matrix_consistency_report=_matrix_consistency_pass_report(),
    )

    matrix_release_mutated = copy.deepcopy(matrix)
    matrix_release_mutated["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_validation_regression_matrix_contract(matrix_release_mutated)

    matrix_consistency_mutated = copy.deepcopy(matrix)
    matrix_consistency_mutated["summary"]["matrix_consistency_report_can_allow_release"] = True
    with pytest.raises(ValueError):
        assert_p7_validation_regression_matrix_contract(matrix_consistency_mutated)

    matrix_full_suite_mutated = copy.deepcopy(matrix)
    matrix_full_suite_mutated["summary"]["split_green_promoted_to_full_suite_green"] = True
    with pytest.raises(ValueError):
        assert_p7_validation_regression_matrix_contract(matrix_full_suite_mutated)


def test_r8_r9_materials_remain_body_free_and_do_not_serialize_runtime_bodies() -> None:
    summary = _all_split_groups_green_summary()
    handoff = build_p7_release_decision_handoff(backend_suite_execution_summary=summary)
    matrix = build_p7_validation_regression_matrix(
        backend_suite_execution_summary=summary,
        matrix_consistency_report=_matrix_consistency_pass_report(),
    )

    serialized = json.dumps({"handoff": handoff, "matrix": matrix}, ensure_ascii=False, sort_keys=True)
    for fragment in (_SECRET_BODY_SENTINEL, "terminal output should not be retained", "traceback body should not be retained"):
        assert fragment not in serialized

    assert handoff["body_free"] is True
    assert matrix["body_free"] is True
    assert handoff["release_allowed"] is False
    assert matrix["release_allowed"] is False
