# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_p7_release_handoff import build_p7_release_decision_handoff
from emlis_ai_p7_validation_matrix import (
    P7_VALIDATION_MATRIX_SCHEMA_VERSION,
    assert_p7_validation_regression_matrix_contract,
    build_p7_validation_regression_matrix,
)
from test_emlis_ai_p7_release_handoff_20260612 import _ready_long_run_handoff

SECRET_INPUT = "P7-9 raw input must never be serialized"
SECRET_COMMENT = "P7-9 comment_text body must never be serialized"

OBSERVED_RESULTS = {
    "p7_core_contract": {"result_kind": "passed", "passed": True},
    "existing_p7_reuse_contract": {"result_kind": "passed", "passed": True},
    "heavy_isolated_positive_recovery_red": {"result_kind": "passed", "passed": True},
    "heavy_isolated_product_quality_connection_timeout": {"result_kind": "passed", "test_count_observed": 1},
    "full_backend_suite": {"result_kind": "not_run"},
}


def _rows_by_kind(matrix: dict[str, object]) -> dict[str, dict[str, object]]:
    return {str(row["check_kind"]): row for row in matrix["matrix_rows"]}  # type: ignore[index]


def test_p7_9_validation_matrix_defines_green_red_hold_boundaries_without_release_claim() -> None:
    matrix = build_p7_validation_regression_matrix(observed_results=OBSERVED_RESULTS)
    assert_p7_validation_regression_matrix_contract(matrix)

    assert matrix["schema_version"] == P7_VALIDATION_MATRIX_SCHEMA_VERSION
    assert matrix["scope"] == "P7_validation_regression_matrix"
    assert matrix["release_allowed"] is False
    assert matrix["summary"]["p7_core_contract_green"] is True
    assert matrix["summary"]["existing_reuse_subset_green"] is True
    assert matrix["summary"]["positive_recovery_red_closed"] is True
    assert matrix["summary"]["positive_recovery_red_remains_ledgered_or_classified"] is True
    assert matrix["summary"]["product_quality_connection_timeout_classified"] is True
    assert matrix["summary"]["product_quality_connection_timeout_closed"] is True
    assert matrix["summary"]["product_quality_connection_timeout_remains_ledgered_or_isolated"] is False
    assert matrix["summary"]["full_backend_suite_green_confirmed"] is False
    assert matrix["summary"]["full_backend_suite_green_claim_allowed"] is False
    assert matrix["summary"]["p7_complete_claim_allowed"] is False
    assert matrix["summary"]["product_pass_is_release_ready"] is False

    rows = _rows_by_kind(matrix)
    assert rows["p7_core_contract"]["observed_status"] == "PASS"
    assert rows["existing_reuse_subset"]["observed_status"] == "PASS"
    assert rows["heavy_positive_recovery_red"]["observed_status"] == "PASS"
    assert rows["heavy_positive_recovery_red"]["green_claim_allowed"] is False
    assert rows["heavy_connection_timeout"]["observed_status"] == "PASSED_ISOLATED"
    assert rows["heavy_connection_timeout"]["green_claim_allowed"] is False
    assert rows["full_backend_suite"]["observed_status"] == "HOLD_UNCONFIRMED"
    assert rows["full_backend_suite"]["green_claim_allowed"] is False
    assert "P7-HOLD-004" in rows["full_backend_suite"]["hold_refs"]
    assert rows["red_closure_classification"]["observed_status"] == "PASS"
    assert rows["red_closure_classification"]["red_refs"] == []
    assert rows["connection_timeout_isolation"]["observed_status"] == "PASSED_ISOLATED"
    assert rows["connection_timeout_isolation"]["green_claim_allowed"] is False


def test_p7_9_release_handoff_source_ready_still_waits_on_holds_after_r13_red003_closure_not_release_ready() -> None:
    ready_handoff = build_p7_release_decision_handoff(
        long_run_gate_handoff=_ready_long_run_handoff(),
        p7_runner_result={
            "runner_result_id": "p7_runner_ready_for_release_handoff_material",
            "release_decision_input_ready": True,
            "full_backend_suite_green_confirmed": True,
        },
    )
    assert ready_handoff["source_material_status"]["release_decision_input_ready_from_long_run"] is True
    assert ready_handoff["release_decision_input_ready"] is False
    assert ready_handoff["release_allowed"] is False
    assert set(ready_handoff["closed_red_refs"]) >= {"P7-RED-001", "P7-RED-002"}
    assert ready_handoff["unresolved_red_refs"] == []
    assert set(ready_handoff["closed_red_refs"]) >= {"P7-RED-001", "P7-RED-002", "P7-RED-003"}

    matrix = build_p7_validation_regression_matrix(release_handoff=ready_handoff, observed_results=OBSERVED_RESULTS)
    assert_p7_validation_regression_matrix_contract(matrix)

    assert matrix["summary"]["release_decision_input_ready"] is False
    assert matrix["summary"]["release_allowed"] is False
    assert matrix["summary"]["p7_complete_claim_allowed"] is False
    assert matrix["green_claim_policy"]["release_ready_claim_allowed"] is False
    assert matrix["green_claim_policy"]["full_backend_suite_green_claim_allowed"] is False
    rows = _rows_by_kind(matrix)
    assert rows["release_handoff"]["observed_status"] == "PASS"
    assert rows["release_handoff"]["green_claim_scope"] == "handoff_material_only_not_release"


def test_p7_9_default_matrix_carries_r13_red003_closure_and_keeps_hold_refs_visible() -> None:
    matrix = build_p7_validation_regression_matrix()
    assert_p7_validation_regression_matrix_contract(matrix)

    assert matrix["unresolved_red_refs"] == []
    assert set(matrix["closed_red_refs"]) >= {"P7-RED-001", "P7-RED-002", "P7-RED-003"}
    assert set(matrix["unresolved_hold_refs"]) >= {"P7-HOLD-001", "P7-HOLD-002", "P7-HOLD-003", "P7-HOLD-004"}
    assert matrix["summary"]["positive_recovery_red_closed"] is True
    assert matrix["summary"]["positive_recovery_red_remains_ledgered_or_classified"] is True
    assert matrix["summary"]["product_quality_connection_timeout_classified"] is True
    assert matrix["summary"]["product_quality_connection_timeout_closed"] is True
    assert matrix["summary"]["product_quality_connection_timeout_remains_ledgered_or_isolated"] is False
    assert matrix["summary"]["release_allowed"] is False


def test_p7_9_matrix_is_body_free_and_never_serializes_bodies_or_release_true() -> None:
    matrix = build_p7_validation_regression_matrix(observed_results=OBSERVED_RESULTS)
    dumped = json.dumps(matrix, ensure_ascii=False, sort_keys=True)

    assert SECRET_INPUT not in dumped
    assert SECRET_COMMENT not in dumped
    assert '"raw_input":' not in dumped
    assert '"comment_text":' not in dumped
    assert '"candidate_body":' not in dumped
    assert '"surface_body":' not in dumped
    assert '"reviewer_free_text":' not in dumped
    assert '"terminal_output":' not in dumped
    assert '"release_allowed": true' not in dumped.lower()


def test_p7_9_contract_rejects_release_full_suite_green_claim_and_body_payload() -> None:
    matrix = build_p7_validation_regression_matrix(observed_results=OBSERVED_RESULTS)

    unsafe_release = dict(matrix)
    unsafe_release["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_validation_regression_matrix_contract(unsafe_release)

    unsafe_summary = dict(matrix)
    unsafe_summary["summary"] = dict(matrix["summary"])
    unsafe_summary["summary"]["full_backend_suite_green_claim_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_validation_regression_matrix_contract(unsafe_summary)

    unsafe_policy = dict(matrix)
    unsafe_policy["green_claim_policy"] = dict(matrix["green_claim_policy"])
    unsafe_policy["green_claim_policy"]["timeout_or_hang_can_be_claimed_green"] = True
    with pytest.raises(ValueError):
        assert_p7_validation_regression_matrix_contract(unsafe_policy)

    unsafe_body = dict(matrix)
    unsafe_body["comment_text"] = SECRET_COMMENT
    with pytest.raises(ValueError):
        assert_p7_validation_regression_matrix_contract(unsafe_body)

    with pytest.raises(ValueError):
        build_p7_validation_regression_matrix(observed_results={"p7_core_contract": {"raw_input": SECRET_INPUT}})
