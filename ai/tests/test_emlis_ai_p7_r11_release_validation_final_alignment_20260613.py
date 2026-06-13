# -*- coding: utf-8 -*-

import copy

import pytest

from emlis_ai_p7_release_handoff import assert_p7_release_decision_handoff_contract, build_p7_release_decision_handoff
from emlis_ai_p7_validation_matrix import assert_p7_validation_matrix_contract, build_p7_validation_matrix


def test_r11_release_handoff_keeps_r10_holds_and_never_promotes_release():
    handoff = build_p7_release_decision_handoff()

    assert handoff["release_allowed"] is False
    assert handoff["release_decision_applied"] is False
    assert handoff["release_rollout_applied"] is False
    assert handoff["product_gate_ready"] is False
    assert handoff["product_gate_reached"] is False
    assert handoff["public_release_applied"] is False
    assert handoff["product_quality_released"] is False
    assert handoff["product_pass_is_release_ready"] is False
    assert handoff["product_pass_promoted_to_release_ready"] is False
    assert handoff["long_run_candidate_is_release_ready"] is False
    assert handoff["real_device_submit_confirmed"] is False
    assert handoff["real_device_submit_modal_readfeel_verified"] is False
    assert handoff["full_backend_suite_green_confirmed"] is False
    assert handoff["full_backend_suite_green_claim_allowed"] is False
    assert {"P7-HOLD-003", "P7-HOLD-004"}.issubset(set(handoff["unresolved_hold_refs"]))
    assert "real_device_submit_modal_readfeel_unverified" in handoff["release_blockers"]
    assert "full_backend_suite_green_unconfirmed" in handoff["release_blockers"]
    assert handoff["release_boundary"]["real_device_submit_required_before_release"] is True
    assert handoff["release_boundary"]["full_backend_suite_required_before_release"] is True
    assert handoff["target_input_projection"]["real_device_submit_confirmed"] is False
    assert handoff["target_input_projection"]["full_backend_suite_green_confirmed"] is False
    assert_p7_release_decision_handoff_contract(handoff)


def test_r11_validation_matrix_adds_real_device_backend_suite_and_final_summary_rows():
    matrix = build_p7_validation_matrix(
        observed_results={
            "p7_core_contract": {"result_kind": "passed", "test_count_observed": 50},
            "existing_p7_reuse_contract": {"result_kind": "passed", "test_count_observed": 31},
            "heavy_isolated_positive_recovery_red": {"result_kind": "closed_confirmed", "test_count_observed": 14},
            "heavy_isolated_product_quality_connection_timeout": {"result_kind": "passed"},
            "full_backend_suite": {"result_kind": "not_run"},
        }
    )

    rows_by_id = {row["row_id"]: row for row in matrix["matrix_rows"]}
    assert rows_by_id["P7-VAL-015"]["check_kind"] == "real_device_submit_modal_readfeel"
    assert rows_by_id["P7-VAL-015"]["observed_status"] == "HOLD_UNCONFIRMED"
    assert rows_by_id["P7-VAL-015"]["green_claim_allowed"] is False
    assert rows_by_id["P7-VAL-016"]["check_kind"] == "backend_suite_split_matrix"
    assert rows_by_id["P7-VAL-016"]["observed_status"] == "HOLD_UNCONFIRMED"
    assert rows_by_id["P7-VAL-017"]["check_kind"] == "r10_hold_matrix"
    assert rows_by_id["P7-VAL-017"]["green_claim_allowed"] is False

    summary = matrix["summary"]
    assert summary["positive_recovery_red_closed"] is True
    assert summary["product_quality_connection_timeout_closed"] is True
    assert summary["real_device_submit_confirmed"] is False
    assert summary["real_device_submit_modal_readfeel_verified"] is False
    assert summary["real_device_submit_hold_preserved"] is True
    assert summary["full_backend_suite_green_confirmed"] is False
    assert summary["full_backend_suite_green_claim_allowed"] is False
    assert summary["full_backend_suite_hold_preserved"] is True
    assert summary["release_handoff_final_consistent"] is True
    assert summary["p7_complete_claim_allowed"] is False
    assert summary["p8_start_allowed"] is False
    assert summary["release_allowed"] is False

    closure = matrix["red_hold_closure_validation_summary"]
    assert closure["p7_complete"] is False
    assert closure["p8_start_allowed"] is False
    assert closure["release_allowed"] is False
    assert "P7-RED-003" not in set(closure["release_blockers"])
    assert {"P7-HOLD-001", "P7-HOLD-002", "P7-HOLD-003", "P7-HOLD-004"}.issubset(set(closure["release_blockers"]))
    assert_p7_validation_matrix_contract(matrix)


def test_r11_validation_contract_rejects_release_full_suite_and_real_device_green_claims():
    matrix = build_p7_validation_matrix()

    release_mutated = copy.deepcopy(matrix)
    release_mutated["summary"]["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_validation_matrix_contract(release_mutated)

    real_device_mutated = copy.deepcopy(matrix)
    real_device_mutated["summary"]["real_device_submit_confirmed"] = True
    with pytest.raises(ValueError):
        assert_p7_validation_matrix_contract(real_device_mutated)

    full_suite_mutated = copy.deepcopy(matrix)
    full_suite_mutated["summary"]["full_backend_suite_green_confirmed"] = True
    with pytest.raises(ValueError):
        assert_p7_validation_matrix_contract(full_suite_mutated)

    policy_mutated = copy.deepcopy(matrix)
    policy_mutated["green_claim_policy"]["split_green_can_be_claimed_full_backend_suite_green"] = True
    with pytest.raises(ValueError):
        assert_p7_validation_matrix_contract(policy_mutated)


def test_r11_release_handoff_contract_rejects_release_ready_and_body_payload():
    handoff = build_p7_release_decision_handoff()

    release_mutated = copy.deepcopy(handoff)
    release_mutated["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_release_decision_handoff_contract(release_mutated)

    full_suite_mutated = copy.deepcopy(handoff)
    full_suite_mutated["full_backend_suite_green_claim_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_release_decision_handoff_contract(full_suite_mutated)

    body_mutated = copy.deepcopy(handoff)
    body_mutated["comment_text_body_included"] = True
    with pytest.raises(ValueError):
        assert_p7_release_decision_handoff_contract(body_mutated)
