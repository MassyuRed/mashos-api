# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_p7_runner_plan import build_p7_runner_plan
from emlis_ai_p7_timeout_isolation import (
    P7_CONNECTION_E2E_TEST_FILE,
    P7_E2E_ISOLATION_RESULT_SCHEMA_VERSION,
    assert_p7_e2e_isolation_result_contract,
    build_p7_connection_e2e_r13_passed_observation_result,
    build_p7_connection_e2e_timeout_isolation_result,
)

SECRET_TERMINAL_OUTPUT = "pytest terminal output body must not enter P7 release material"
SECRET_COMMENT = "comment_text body must not enter timeout isolation"


def test_r6_connection_e2e_timeout_is_body_free_isolated_red_not_core_green() -> None:
    result = build_p7_connection_e2e_timeout_isolation_result(
        result_kind="timeout",
        timeout_budget_sec=30,
        last_completed_stage="unknown",
        owner_layer="unknown",
    )
    assert_p7_e2e_isolation_result_contract(result)

    assert result["schema_version"] == P7_E2E_ISOLATION_RESULT_SCHEMA_VERSION
    assert result["source_test_file"] == P7_CONNECTION_E2E_TEST_FILE
    assert result["command_kind"] == "pytest_timeout"
    assert result["timeout_budget_sec"] == 30
    assert result["result_kind"] == "timeout"
    assert result["observed_status"] == "TIMEOUT_ISOLATED"
    assert result["last_completed_stage"] == "unknown"
    assert result["owner_layer"] == "unknown"
    assert result["red_refs"] == ["P7-RED-003"]
    assert result["unresolved_timeout_refs"] == ["P7-RED-003"]
    assert result["release_blocker"] is True
    assert result["body_free_guard_contract_connected"] is False
    assert result["default_pytest_timeout_resolved"] is False
    assert result["r13_closure_candidate"] is False
    assert result["can_join_p7_core_green"] is False
    assert result["can_claim_full_backend_suite_green"] is False
    assert result["full_backend_suite_green_confirmed"] is False
    assert result["release_decision_input_ready"] is False
    assert result["release_allowed"] is False
    assert result["body_free"] is True


def test_r13_6_connection_e2e_passed_observation_is_body_free_closure_candidate() -> None:
    result = build_p7_connection_e2e_r13_passed_observation_result(timeout_budget_sec=30)
    assert_p7_e2e_isolation_result_contract(result)

    assert result["schema_version"] == P7_E2E_ISOLATION_RESULT_SCHEMA_VERSION
    assert result["source_test_file"] == P7_CONNECTION_E2E_TEST_FILE
    assert result["command_kind"] == "pytest_timeout"
    assert result["timeout_budget_sec"] == 30
    assert result["result_kind"] == "passed"
    assert result["observed_status"] == "PASSED_ISOLATED"
    assert result["summary_code"] == "product_quality_connection_e2e_body_free_guard_structured_and_default_pytest_passed"
    assert result["last_completed_stage"] == "product_quality_connection_e2e_default_pytest_passed"
    assert result["owner_layer"] == "product_quality_scorecard_body_free_guard"
    assert result["red_refs"] == []
    assert result["unresolved_timeout_refs"] == []
    assert result["release_blocker"] is False
    assert result["body_free_guard_contract_connected"] is True
    assert result["default_pytest_timeout_resolved"] is True
    assert result["r13_closure_candidate"] is True
    assert result["can_join_p7_core_green"] is False
    assert result["can_claim_full_backend_suite_green"] is False
    assert result["release_decision_input_ready"] is False
    assert result["release_allowed"] is False
    assert result["p7_complete"] is False
    assert result["p8_start_allowed"] is False
    assert result["body_free"] is True

    dumped = json.dumps(result, ensure_ascii=False, sort_keys=True)
    assert SECRET_TERMINAL_OUTPUT not in dumped
    assert SECRET_COMMENT not in dumped
    assert '"release_allowed": true' not in dumped.lower()


def test_r6_isolation_contract_rejects_green_or_body_payload_claims() -> None:
    result = build_p7_connection_e2e_timeout_isolation_result()

    unsafe_release = dict(result)
    unsafe_release["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_e2e_isolation_result_contract(unsafe_release)

    unsafe_core_green = dict(result)
    unsafe_core_green["can_join_p7_core_green"] = True
    with pytest.raises(ValueError):
        assert_p7_e2e_isolation_result_contract(unsafe_core_green)

    unsafe_terminal = dict(result)
    unsafe_terminal["terminal_output"] = SECRET_TERMINAL_OUTPUT
    with pytest.raises(ValueError):
        assert_p7_e2e_isolation_result_contract(unsafe_terminal)

    unsafe_comment = dict(result)
    unsafe_comment["comment_text"] = SECRET_COMMENT
    with pytest.raises(ValueError):
        assert_p7_e2e_isolation_result_contract(unsafe_comment)

    unsafe_passed_owner = build_p7_connection_e2e_r13_passed_observation_result()
    unsafe_passed_owner["owner_layer"] = "unknown"
    with pytest.raises(ValueError):
        assert_p7_e2e_isolation_result_contract(unsafe_passed_owner)


def test_r6_runner_plan_carries_connection_isolation_without_core_green_claim() -> None:
    plan = build_p7_runner_plan()
    isolation = plan["connection_timeout_isolation_result"]
    assert_p7_e2e_isolation_result_contract(isolation)

    assert plan["e2e_isolation_result_schema_version"] == P7_E2E_ISOLATION_RESULT_SCHEMA_VERSION
    assert isolation["observed_status"] == "TIMEOUT_ISOLATED"
    assert isolation["can_join_p7_core_green"] is False
    assert isolation["release_allowed"] is False
    dumped = json.dumps(plan, ensure_ascii=False, sort_keys=True)
    assert SECRET_TERMINAL_OUTPUT not in dumped
    assert SECRET_COMMENT not in dumped
    assert '"release_allowed": true' not in dumped.lower()
