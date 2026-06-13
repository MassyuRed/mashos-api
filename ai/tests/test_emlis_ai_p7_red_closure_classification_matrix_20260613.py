# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_p7_red_closure_classification import (
    P7_RED_CLOSURE_CLASSIFICATION_MATRIX_SCHEMA_VERSION,
    assert_p7_red_closure_classification_matrix_contract,
    build_p7_red_closure_classification_index,
    build_p7_red_closure_classification_matrix,
)
from emlis_ai_p7_release_handoff import build_p7_release_decision_handoff
from emlis_ai_p7_timeout_isolation import build_p7_connection_e2e_r13_passed_observation_result
from emlis_ai_p7_validation_matrix import build_p7_validation_regression_matrix

SECRET_BODY = "raw or comment body must not appear in classification material"


def test_r7_red_closure_matrix_closes_positive_recovery_but_keeps_timeout_unresolved() -> None:
    matrix = build_p7_red_closure_classification_matrix()
    assert_p7_red_closure_classification_matrix_contract(matrix)

    assert matrix["schema_version"] == P7_RED_CLOSURE_CLASSIFICATION_MATRIX_SCHEMA_VERSION
    assert matrix["positive_recovery_red_closed"] is True
    assert matrix["product_quality_connection_timeout_classified"] is True
    assert matrix["product_quality_connection_timeout_isolated"] is True
    assert matrix["product_quality_connection_timeout_closed"] is False
    assert matrix["closed_red_refs"] == ["P7-RED-001", "P7-RED-002"]
    assert matrix["unresolved_red_refs"] == ["P7-RED-003"]
    assert matrix["release_blockers"] == ["P7-RED-003"]
    assert matrix["p7_complete"] is False
    assert matrix["p8_start_allowed"] is False
    assert matrix["release_allowed"] is False

    index = build_p7_red_closure_classification_index(matrix)
    assert index["P7-RED-001"]["status"] == "CLOSED"
    assert index["P7-RED-002"]["status"] == "CLOSED"
    assert index["P7-RED-003"]["status"] == "CLASSIFIED"
    assert index["P7-RED-003"]["classification"] == "timeout_owner_unknown"
    assert index["P7-RED-003"]["observed_status"] == "TIMEOUT_ISOLATED"


def test_r13_7_red003_closes_when_passed_body_free_observation_is_supplied() -> None:
    observation = build_p7_connection_e2e_r13_passed_observation_result(timeout_budget_sec=30)
    matrix = build_p7_red_closure_classification_matrix(connection_timeout_isolation_result=observation)
    assert_p7_red_closure_classification_matrix_contract(matrix)

    assert matrix["positive_recovery_red_closed"] is True
    assert matrix["product_quality_connection_timeout_classified"] is True
    assert matrix["product_quality_connection_timeout_isolated"] is False
    assert matrix["product_quality_connection_timeout_closed"] is True
    assert matrix["source_e2e_isolation_result_kind"] == "passed"
    assert matrix["source_e2e_observed_status"] == "PASSED_ISOLATED"
    assert matrix["closed_red_refs"] == ["P7-RED-001", "P7-RED-002", "P7-RED-003"]
    assert matrix["unresolved_red_refs"] == []
    assert matrix["release_blockers"] == []
    assert matrix["p7_complete"] is False
    assert matrix["p8_start_allowed"] is False
    assert matrix["release_allowed"] is False

    index = build_p7_red_closure_classification_index(matrix)
    red003 = index["P7-RED-003"]
    assert red003["status"] == "CLOSED"
    assert red003["classification"] == "body_free_guard_repaired"
    assert red003["owner_layer"] == "product_quality_scorecard_body_free_guard"
    assert red003["summary_code"] == "product_quality_connection_e2e_body_free_guard_structured_and_default_pytest_passed"
    assert red003["observed_status"] == "PASSED_ISOLATED"
    assert red003["release_blocker"] is False
    assert red003["closure_allowed"] is True
    assert red003["body_free"] is True

    dumped = json.dumps(matrix, ensure_ascii=False, sort_keys=True)
    assert SECRET_BODY not in dumped
    assert '"comment_text":' not in dumped
    assert '"terminal_output":' not in dumped
    assert '"release_allowed": true' not in dumped.lower()


def test_r7_classification_feeds_handoff_and_validation_without_release_claim() -> None:
    classification = build_p7_red_closure_classification_matrix()
    handoff = build_p7_release_decision_handoff(red_closure_classification=classification)

    assert handoff["closed_red_refs"] == ["P7-RED-001", "P7-RED-002"]
    assert handoff["unresolved_red_refs"] == ["P7-RED-003"]
    assert handoff["unresolved_timeout_refs"] == ["P7-RED-003"]
    assert handoff["release_decision_input_ready"] is False
    assert handoff["release_allowed"] is False

    validation = build_p7_validation_regression_matrix(red_closure_classification_matrix=classification)
    assert validation["summary"]["positive_recovery_red_closed"] is True
    assert validation["summary"]["product_quality_connection_timeout_classified"] is True
    assert validation["summary"]["product_quality_connection_timeout_closed"] is False
    assert validation["closed_red_refs"] == ["P7-RED-001", "P7-RED-002"]
    assert validation["unresolved_red_refs"] == ["P7-RED-003"]
    assert validation["release_allowed"] is False
    assert validation["green_claim_policy"]["positive_recovery_closed_can_be_claimed_release_ready"] is False
    assert validation["green_claim_policy"]["timeout_or_hang_can_be_claimed_green"] is False


def test_r7_contract_rejects_release_or_body_payload_claims() -> None:
    matrix = build_p7_red_closure_classification_matrix()
    unsafe_release = dict(matrix)
    unsafe_release["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_red_closure_classification_matrix_contract(unsafe_release)

    unsafe_body = dict(matrix)
    unsafe_body["raw_input"] = SECRET_BODY
    with pytest.raises(ValueError):
        assert_p7_red_closure_classification_matrix_contract(unsafe_body)

    unsafe_conflict = dict(matrix)
    unsafe_conflict["closed_red_refs"] = ["P7-RED-001", "P7-RED-002", "P7-RED-003"]
    with pytest.raises(ValueError):
        assert_p7_red_closure_classification_matrix_contract(unsafe_conflict)

    dumped = json.dumps(matrix, ensure_ascii=False, sort_keys=True)
    assert SECRET_BODY not in dumped
    assert '"comment_text":' not in dumped
    assert '"terminal_output":' not in dumped
    assert '"release_allowed": true' not in dumped.lower()
