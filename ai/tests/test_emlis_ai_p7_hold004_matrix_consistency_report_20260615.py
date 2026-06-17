# -*- coding: utf-8 -*-
"""P7-HOLD-004 R10 matrix consistency report tests."""

from __future__ import annotations

import copy
import json

import pytest

from emlis_ai_p7_hold004_backend_suite_execution_results import (
    P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_ITEM_FINGERPRINT_MISMATCH,
    P7_HOLD004_RECEIVED_SNAPSHOT_ITEM_FINGERPRINT_MISMATCH_BLOCKER_REF,
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
from emlis_ai_p7_hold004_matrix_consistency_report import (
    P7_HOLD004_MATRIX_CONSISTENCY_REPORT_ID,
    P7_HOLD004_MATRIX_CONSISTENCY_REPORT_STEP,
    assert_p7_hold004_matrix_consistency_report_contract,
    build_p7_hold004_matrix_consistency_report,
)
from emlis_ai_p7_hold_matrix import build_p7_backend_suite_split_matrix, build_p7_r10_hold_matrix
from emlis_ai_p7_red_closure_classification import build_p7_red_closure_classification_matrix
from emlis_ai_p7_release_handoff import build_p7_release_decision_handoff
from emlis_ai_p7_timeout_isolation import build_p7_connection_e2e_r13_passed_observation_result
from emlis_ai_p7_validation_matrix import (
    P7_HOLD004_MATRIX_CONSISTENCY_REPORT_SCHEMA_VERSION,
    assert_p7_validation_regression_matrix_contract,
    build_p7_validation_regression_matrix,
)

_SECRET_BODY_SENTINEL = "R10 raw body must never be serialized"


def _assert_report_current_baseline_connection(report: dict[str, object]) -> None:
    assert report["current_collect_baseline_connected"] is True
    assert report["current_group_inventory_connected"] is True
    assert report["current_execution_plan_connected"] is True
    assert report["old_baseline_not_used_as_current"] is True
    assert report["backend_suite_group_02_count_current"] is True
    assert report["backend_suite_execution_summary_collect_baseline_id"] == P7_HOLD004_BACKEND_COLLECT_BASELINE_ID
    assert report["backend_suite_execution_summary_inventory_id"] == P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID
    assert report["backend_suite_execution_summary_plan_id"] == P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID
    connection = report["matrix_current_baseline_connection"]
    assert connection["collect_baseline_id"] == P7_HOLD004_BACKEND_COLLECT_BASELINE_ID
    assert connection["group_inventory_id"] == P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID
    assert connection["execution_plan_id"] == P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID
    assert connection["current_collect_file_count"] == P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT
    assert connection["current_collect_test_item_count"] == P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT
    assert connection["group_02_file_count"] == 19
    assert connection["group_02_test_item_count"] == 252
    assert connection["old_baseline_id"] == "p7_hold004_backend_collect_baseline_20260614"
    assert connection["old_baseline_used_as_current"] is False
    assert connection["full_backend_suite_green_confirmed"] is False
    assert connection["release_allowed"] is False
    assert connection["body_free"] is True
    assert report["official_group_02_capture_readiness_status"] == (
        P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_ITEM_FINGERPRINT_MISMATCH
    )
    assert report["official_group_02_capture_blocked"] is True
    assert report["official_group_02_capture_run_allowed"] is False
    assert report["official_group_02_capture_result_recording_allowed"] is False
    assert report["received_snapshot_baseline_fingerprint_reconciled"] is False
    assert report["received_snapshot_item_fingerprint_mismatch_unresolved"] is True
    assert P7_HOLD004_RECEIVED_SNAPSHOT_ITEM_FINGERPRINT_MISMATCH_BLOCKER_REF in report["received_snapshot_blocker_refs"]
    assert P7_HOLD004_RECEIVED_SNAPSHOT_ITEM_FINGERPRINT_MISMATCH_BLOCKER_REF in report["required_followup_fixes"]


def _all_split_groups_green_summary() -> dict[str, object]:
    results: list[dict[str, object]] = []
    for definition in P7_HOLD004_BACKEND_SUITE_GROUP_DEFINITIONS:
        group_id = str(definition["group_id"])
        for batch_index in range(1, int(definition["planned_batch_count"]) + 1):
            results.append(
                build_p7_hold004_backend_suite_group_run_result(
                    group_id=group_id,
                    batch_id=f"{group_id}_batch_{batch_index:02d}",
                    status="PASS",
                    passed=1,
                )
            )
    summary = build_p7_hold004_backend_suite_execution_summary(run_results=results)
    assert summary["split_all_groups_green_confirmed"] is True
    return summary


def _red003_closed_matrix() -> dict[str, object]:
    return build_p7_red_closure_classification_matrix(
        connection_timeout_isolation_result=build_p7_connection_e2e_r13_passed_observation_result()
    )


def _consistent_material_bundle(summary: dict[str, object] | None = None) -> tuple[dict[str, object], ...]:
    summary_material = summary or build_p7_hold004_backend_suite_execution_summary()
    red_closure = _red003_closed_matrix()
    backend = build_p7_backend_suite_split_matrix(
        backend_suite_execution_summary=summary_material,
        red_closure_classification_matrix=red_closure,
    )
    r10 = build_p7_r10_hold_matrix(backend_suite_split_matrix=backend)
    handoff = build_p7_release_decision_handoff(
        backend_suite_execution_summary=summary_material,
        backend_suite_split_matrix=backend,
        r10_hold_matrix=r10,
        red_closure_classification_matrix=red_closure,
    )
    validation = build_p7_validation_regression_matrix(
        backend_suite_execution_summary=summary_material,
        backend_suite_split_matrix=backend,
        r10_hold_matrix=r10,
        release_handoff=handoff,
        red_closure_classification_matrix=red_closure,
    )
    return summary_material, red_closure, backend, r10, handoff, validation


def _rows_by_kind(matrix: dict[str, object]) -> dict[str, dict[str, object]]:
    return {str(row["check_kind"]): row for row in matrix["matrix_rows"]}  # type: ignore[index]


def test_r10_default_matrix_consistency_report_passes_while_preserving_hold004_and_release_false() -> None:
    report = build_p7_hold004_matrix_consistency_report()
    assert_p7_hold004_matrix_consistency_report_contract(report)

    assert report["schema_version"] == P7_HOLD004_MATRIX_CONSISTENCY_REPORT_SCHEMA_VERSION
    assert report["implementation_step"] == P7_HOLD004_MATRIX_CONSISTENCY_REPORT_STEP
    assert report["report_id"] == P7_HOLD004_MATRIX_CONSISTENCY_REPORT_ID
    assert report["consistency_status"] == "REVIEW_REQUIRED"
    assert report["checks"]["received_snapshot_blocking_status_consistent"] is True
    assert report["checks"]["received_snapshot_item_fingerprint_mismatch_resolved"] is False
    _assert_report_current_baseline_connection(report)
    assert report["checks"]["hold004_preserved_across_matrices"] is True
    assert report["checks"]["current_collect_baseline_connected"] is True
    assert report["checks"]["current_group_inventory_connected"] is True
    assert report["checks"]["current_execution_plan_connected"] is True
    assert report["checks"]["old_baseline_not_used_as_current"] is True
    assert report["checks"]["backend_suite_group_02_count_current"] is True
    assert report["checks"]["full_backend_suite_green_false_across_matrices"] is True
    assert report["checks"]["split_green_not_promoted"] is True
    assert report["checks"]["release_allowed_false_across_matrices"] is True
    assert report["red003_unresolved"] is True
    assert "P7-RED-003" in report["unresolved_red_refs"]
    assert "P7-HOLD-004" in report["unresolved_hold_refs"]
    assert report["full_backend_suite_green_confirmed"] is False
    assert report["split_green_is_full_backend_suite_green"] is False
    assert report["split_green_can_close_p7_hold004"] is False
    assert report["hold004_close_allowed"] is False
    assert report["p8_start_allowed"] is False
    assert report["release_allowed"] is False


def test_r10_report_accepts_structured_red003_closure_and_all_split_groups_green_without_promoting_full_suite() -> None:
    report = build_p7_hold004_matrix_consistency_report(
        backend_suite_execution_summary=_all_split_groups_green_summary(),
        red_closure_classification_matrix=_red003_closed_matrix(),
    )
    assert_p7_hold004_matrix_consistency_report_contract(report)

    assert report["consistency_status"] == "REVIEW_REQUIRED"
    assert report["checks"]["received_snapshot_blocking_status_consistent"] is True
    assert report["checks"]["received_snapshot_item_fingerprint_mismatch_resolved"] is False
    _assert_report_current_baseline_connection(report)
    assert report["backend_suite_execution_summary_split_all_groups_green_confirmed"] is True
    assert report["red003_closed"] is True
    assert "P7-RED-003" in report["closed_red_refs"]
    assert "P7-RED-003" not in report["unresolved_red_refs"]
    assert report["checks"]["full_backend_suite_green_false_across_matrices"] is True
    assert report["checks"]["split_green_not_promoted"] is True
    assert report["full_backend_suite_green_confirmed"] is False
    assert report["split_green_can_close_p7_hold004"] is False
    assert report["release_allowed"] is False
    assert "full_backend_suite_green_unconfirmed" in report["required_followup_fixes"]


def test_r10_report_connects_to_validation_matrix_as_material_not_release_permission() -> None:
    summary = _all_split_groups_green_summary()
    red_closure = _red003_closed_matrix()
    report = build_p7_hold004_matrix_consistency_report(
        backend_suite_execution_summary=summary,
        red_closure_classification_matrix=red_closure,
    )
    matrix = build_p7_validation_regression_matrix(
        backend_suite_execution_summary=summary,
        red_closure_classification_matrix=red_closure,
        matrix_consistency_report=report,
    )
    assert_p7_validation_regression_matrix_contract(matrix)

    rows_by_kind = _rows_by_kind(matrix)
    readiness_row = rows_by_kind["official_group02_capture_readiness"]
    assert readiness_row["observed_status"] == "BLOCKED"
    assert P7_HOLD004_RECEIVED_SNAPSHOT_ITEM_FINGERPRINT_MISMATCH_BLOCKER_REF in readiness_row["reason_codes"]

    row = rows_by_kind["matrix_consistency_report"]
    assert row["observed_status"] == "BLOCKED"
    assert row["green_claim_allowed"] is False
    assert row["release_allowed"] is False
    assert "P7-HOLD-004" in row["hold_refs"]
    assert matrix["matrix_consistency_report_connected"] is True
    assert matrix["matrix_consistency_report_status"] == "REVIEW_REQUIRED"
    assert matrix["summary"]["matrix_consistency_report_can_allow_release"] is False
    assert matrix["summary"]["current_collect_baseline_connected"] is True
    assert matrix["summary"]["current_group_inventory_connected"] is True
    assert matrix["summary"]["current_execution_plan_connected"] is True
    assert matrix["summary"]["old_baseline_not_used_as_current"] is True
    assert matrix["summary"]["backend_suite_group_02_count_current"] is True
    assert matrix["summary"]["release_allowed"] is False


def test_r10_report_marks_review_required_when_red003_closure_read_differs_across_valid_matrices() -> None:
    summary, red_closed, backend, r10, handoff, validation = _consistent_material_bundle()
    red_default_unresolved = build_p7_red_closure_classification_matrix()

    report = build_p7_hold004_matrix_consistency_report(
        backend_suite_execution_summary=summary,
        red_closure_classification_matrix=red_default_unresolved,
        backend_suite_split_matrix=backend,
        r10_hold_matrix=r10,
        release_handoff=handoff,
        validation_matrix=validation,
    )
    assert_p7_hold004_matrix_consistency_report_contract(report)

    assert report["consistency_status"] == "REVIEW_REQUIRED"
    _assert_report_current_baseline_connection(report)
    assert report["checks"]["red003_closure_consistent"] is False
    assert "P7-RED-003" in report["closed_red_refs"]
    assert "P7-RED-003" in report["unresolved_red_refs"]
    assert "red003_closure_inconsistent" in report["required_followup_fixes"]
    assert report["release_allowed"] is False


def test_r10_report_contract_rejects_report_mutations_that_promote_release_or_body_payloads() -> None:
    report = build_p7_hold004_matrix_consistency_report()

    release_mutated = copy.deepcopy(report)
    release_mutated["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_matrix_consistency_report_contract(release_mutated)

    full_suite_mutated = copy.deepcopy(report)
    full_suite_mutated["full_backend_suite_green_confirmed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_matrix_consistency_report_contract(full_suite_mutated)

    marker_mutated = copy.deepcopy(report)
    marker_mutated["body_free_markers"]["terminal_output_included"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_matrix_consistency_report_contract(marker_mutated)

    body_mutated = copy.deepcopy(report)
    body_mutated["comment_text"] = _SECRET_BODY_SENTINEL
    with pytest.raises(ValueError):
        assert_p7_hold004_matrix_consistency_report_contract(body_mutated)


def test_r10_report_remains_body_free_and_does_not_serialize_runtime_bodies() -> None:
    report = build_p7_hold004_matrix_consistency_report()
    serialized = json.dumps(report, ensure_ascii=False, sort_keys=True)

    for fragment in (_SECRET_BODY_SENTINEL, "terminal output should not be retained", "traceback body should not be retained"):
        assert fragment not in serialized
    assert "comment_text" not in report
    assert "terminal_output" not in report
    assert report["body_free"] is True
    assert all(value is False for value in report["public_contract"].values())
    assert all(value is False for value in report["body_free_markers"].values())
