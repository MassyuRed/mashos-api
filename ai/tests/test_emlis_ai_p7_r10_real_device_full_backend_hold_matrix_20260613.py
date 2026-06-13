# -*- coding: utf-8 -*-

import copy

import pytest

from emlis_ai_p7_hold_matrix import (
    P7_BACKEND_SUITE_SPLIT_MATRIX_SCHEMA_VERSION,
    P7_R10_HOLD_MATRIX_SCHEMA_VERSION,
    P7_REAL_DEVICE_MODAL_READFEEL_CHECK_SCHEMA_VERSION,
    assert_p7_backend_suite_split_matrix_contract,
    assert_p7_r10_hold_matrix_contract,
    assert_p7_real_device_modal_readfeel_check_contract,
    build_p7_backend_suite_split_matrix,
    build_p7_r10_hold_matrix,
    build_p7_real_device_modal_readfeel_check,
)


def test_r10_real_device_modal_readfeel_default_stays_manual_hold_and_body_free():
    check = build_p7_real_device_modal_readfeel_check()

    assert check["schema_version"] == P7_REAL_DEVICE_MODAL_READFEEL_CHECK_SCHEMA_VERSION
    assert check["status"] == "not_verified"
    assert check["real_device_submit_confirmed"] is False
    assert check["manual_real_device_check_required"] is True
    assert check["automated_test_green_can_close"] is False
    assert check["hold_refs"] == ["P7-HOLD-003"]
    assert check["release_allowed"] is False
    assert check["body_free"] is True
    assert check["raw_input_included"] is False
    assert check["comment_text_body_included"] is False
    assert all(status == "not_verified" for status in check["checks"].values())
    assert_p7_real_device_modal_readfeel_check_contract(check)


def test_r10_backend_suite_split_matrix_keeps_split_green_out_of_full_suite_claim():
    real_device = build_p7_real_device_modal_readfeel_check()
    matrix = build_p7_backend_suite_split_matrix(
        real_device_check=real_device,
        positive_recovery_red_closed=True,
        observed_results={
            "p7_core_contract": {"result_kind": "passed", "test_count_observed": 50},
            "existing_p7_reuse_contract": {"result_kind": "passed", "test_count_observed": 31},
            "heavy_isolated_positive_recovery_red": {"result_kind": "closed_confirmed", "test_count_observed": 14},
            "heavy_isolated_product_quality_connection_timeout": {"result_kind": "timeout", "test_count_observed": 0},
            "full_backend_suite": {"result_kind": "not_run", "test_count_observed": 0},
        },
    )

    assert matrix["schema_version"] == P7_BACKEND_SUITE_SPLIT_MATRIX_SCHEMA_VERSION
    assert matrix["group_statuses"]["p7_core"] == "green_confirmed"
    assert matrix["group_statuses"]["product_quality_reuse_subset"] == "green_confirmed"
    assert matrix["group_statuses"]["positive_recovery_e2e"] == "closed_confirmed"
    assert matrix["group_statuses"]["product_quality_connection_e2e"] == "timeout_isolated"
    assert matrix["group_statuses"]["full_backend_suite"] == "not_run"
    assert matrix["full_backend_suite_green_confirmed"] is False
    assert matrix["full_backend_suite_green_claim_allowed"] is False
    assert matrix["split_green_is_full_backend_suite_green"] is False
    assert "P7-RED-003" in matrix["unresolved_red_refs"]
    assert {"P7-HOLD-003", "P7-HOLD-004"}.issubset(set(matrix["unresolved_hold_refs"]))
    assert matrix["release_allowed"] is False
    assert matrix["body_free"] is True
    assert_p7_backend_suite_split_matrix_contract(matrix)


def test_r10_composite_hold_matrix_keeps_red_hold_refs_and_release_closed():
    matrix = build_p7_r10_hold_matrix()

    assert matrix["schema_version"] == P7_R10_HOLD_MATRIX_SCHEMA_VERSION
    assert matrix["real_device_modal_readfeel_check_schema_version"] == P7_REAL_DEVICE_MODAL_READFEEL_CHECK_SCHEMA_VERSION
    assert matrix["backend_suite_split_matrix_schema_version"] == P7_BACKEND_SUITE_SPLIT_MATRIX_SCHEMA_VERSION
    assert matrix["real_device_submit_confirmed"] is False
    assert matrix["real_device_submit_modal_readfeel_verified"] is False
    assert matrix["full_backend_suite_green_confirmed"] is False
    assert matrix["full_backend_suite_green_claim_allowed"] is False
    assert matrix["split_green_is_full_backend_suite_green"] is False
    assert matrix["split_green_promoted_to_full_suite_green"] is False
    assert "P7-RED-003" in matrix["unresolved_red_refs"]
    assert {"P7-HOLD-003", "P7-HOLD-004"}.issubset(set(matrix["unresolved_hold_refs"]))
    assert "real_device_submit_modal_readfeel_unverified" in matrix["required_followup_fixes"]
    assert "full_backend_suite_green_unconfirmed" in matrix["required_followup_fixes"]
    assert matrix["release_allowed"] is False
    assert matrix["body_free"] is True
    assert_p7_r10_hold_matrix_contract(matrix)


def test_r10_contract_rejects_auto_green_claim_release_true_and_body_payload():
    matrix = build_p7_r10_hold_matrix()

    release_mutated = copy.deepcopy(matrix)
    release_mutated["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_r10_hold_matrix_contract(release_mutated)

    full_suite_mutated = copy.deepcopy(matrix)
    full_suite_mutated["full_backend_suite_green_claim_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_r10_hold_matrix_contract(full_suite_mutated)

    split_mutated = copy.deepcopy(matrix)
    split_mutated["split_green_promoted_to_full_suite_green"] = True
    with pytest.raises(ValueError):
        assert_p7_r10_hold_matrix_contract(split_mutated)

    body_mutated = copy.deepcopy(matrix)
    body_mutated["comment_text_body_included"] = True
    with pytest.raises(ValueError):
        assert_p7_r10_hold_matrix_contract(body_mutated)
