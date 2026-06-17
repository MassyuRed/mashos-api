# -*- coding: utf-8 -*-
"""Contract tests for P7-HOLD-004 R40 result recording and full-suite gate.

R40 may record a body-free official group_02 result after R39 readiness, but it
must not promote that isolated group result to full backend-suite green, HOLD
closure, P7 completion, P8 start, or release readiness.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from emlis_ai_p7_hold004_active_baseline_runtime_builder_refresh import (
    P7_HOLD004_GROUP02_RESULT_STATUS_FAILED_ISOLATED,
    P7_HOLD004_GROUP02_RESULT_STATUS_NOT_RUN,
    P7_HOLD004_GROUP02_RESULT_STATUS_PARTIAL_OR_INTERRUPTED,
    P7_HOLD004_GROUP02_RESULT_STATUS_PASSED_ISOLATED,
    P7_HOLD004_GROUP02_RESULT_STATUS_TIMEOUT_ISOLATED,
    assert_p7_hold004_full_backend_suite_gate_contract,
    assert_p7_hold004_official_group02_result_recording_contract,
    build_p7_hold004_full_backend_suite_gate,
    build_p7_hold004_official_group02_result_recording,
)
from emlis_ai_p7_hold004_backend_suite_execution_results import (
    P7_HOLD004_BACKEND_SUITE_RUN_KIND_CAPTURE,
    P7_HOLD004_BACKEND_SUITE_STATUS_FAIL,
    P7_HOLD004_BACKEND_SUITE_STATUS_INTERRUPTED,
    P7_HOLD004_BACKEND_SUITE_STATUS_PASS,
    P7_HOLD004_BACKEND_SUITE_STATUS_TIMEOUT,
    P7_HOLD004_GROUP02_OFFICIAL_BATCH_ID,
    P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID,
    P7_HOLD004_GROUP02_OFFICIAL_TEST_ITEM_COUNT,
    P7_HOLD004_GROUP02_OFFICIAL_WARNINGS_COUNT,
    build_p7_hold004_backend_suite_group_run_result,
)
from emlis_ai_p7_hold004_backend_suite_group_inventory_plan import (
    P7_HOLD004_BACKEND_SUITE_GROUP_IDS,
)


def _group02_run_result(status: str, **overrides: object) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "group_id": P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID,
        "batch_id": P7_HOLD004_GROUP02_OFFICIAL_BATCH_ID,
        "run_kind": P7_HOLD004_BACKEND_SUITE_RUN_KIND_CAPTURE,
        "status": status,
        "warnings": P7_HOLD004_GROUP02_OFFICIAL_WARNINGS_COUNT,
    }
    kwargs.update(overrides)
    return build_p7_hold004_backend_suite_group_run_result(**kwargs)


def test_r40_default_not_run_keeps_group02_pending_and_full_suite_closed() -> None:
    recording = build_p7_hold004_official_group02_result_recording()

    assert recording["result_status"] == P7_HOLD004_GROUP02_RESULT_STATUS_NOT_RUN
    assert recording["official_group_02_official_full_run_executed"] is False
    assert recording["official_group_02_capture_result_recorded"] is False
    assert recording["official_group_02_capture_green_confirmed"] is False
    assert recording["can_claim_group_green"] is False
    assert recording["can_claim_full_backend_suite_green"] is False
    assert recording["full_backend_suite_green_confirmed"] is False
    assert recording["release_allowed"] is False
    assert P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID in recording["remaining_backend_group_ids"]
    assert recording["remaining_backend_group_count"] == len(P7_HOLD004_BACKEND_SUITE_GROUP_IDS)

    gate = build_p7_hold004_full_backend_suite_gate(official_group02_result_recording=recording)
    assert gate["official_group_02_capture_result_recorded"] is False
    assert gate["full_backend_suite_required_conditions"]["group02_result_recorded"] is False
    assert gate["full_backend_suite_green_confirmed"] is False
    assert gate["can_claim_full_backend_suite_green"] is False
    assert gate["hold004_close_allowed"] is False
    assert gate["release_allowed"] is False
    assert P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID in gate["remaining_backend_group_ids"]


def test_r40_passed_isolated_group_green_is_not_full_backend_suite_green() -> None:
    run_result = _group02_run_result(
        P7_HOLD004_BACKEND_SUITE_STATUS_PASS,
        passed=P7_HOLD004_GROUP02_OFFICIAL_TEST_ITEM_COUNT,
        failed=0,
        errors=0,
    )
    recording = build_p7_hold004_official_group02_result_recording(run_result=run_result)

    assert recording["result_status"] == P7_HOLD004_GROUP02_RESULT_STATUS_PASSED_ISOLATED
    assert recording["official_group_02_capture_result_recorded"] is True
    assert recording["official_group_02_capture_green_confirmed"] is True
    assert recording["can_claim_group_green"] is True
    assert recording["group02_pass_is_not_full_backend_suite_green"] is True
    assert recording["can_claim_full_backend_suite_green"] is False
    assert recording["full_backend_suite_green_confirmed"] is False
    assert recording["hold004_close_allowed"] is False
    assert recording["release_allowed"] is False
    assert P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID not in recording["remaining_backend_group_ids"]
    assert recording["remaining_backend_group_count"] == len(P7_HOLD004_BACKEND_SUITE_GROUP_IDS) - 1

    gate = build_p7_hold004_full_backend_suite_gate(official_group02_result_recording=recording)
    assert gate["official_group_02_capture_green_confirmed"] is True
    assert gate["can_claim_group_green"] is True
    assert gate["full_backend_suite_required_conditions"]["group02_result_recorded"] is True
    assert gate["full_backend_suite_green_confirmed"] is False
    assert gate["can_claim_full_backend_suite_green"] is False
    assert gate["remaining_backend_group_count"] == len(P7_HOLD004_BACKEND_SUITE_GROUP_IDS) - 1


def test_r40_failed_timeout_and_interrupted_results_are_recorded_without_green_claims() -> None:
    failed_result = _group02_run_result(
        P7_HOLD004_BACKEND_SUITE_STATUS_FAIL,
        passed=P7_HOLD004_GROUP02_OFFICIAL_TEST_ITEM_COUNT - 1,
        failed=1,
        first_failure_nodeid="group02_failure_identifier",
        first_failure_file_ref="tests/test_emlis_ai_p7_hold004_group02_identifier.py",
        failure_kind="assertion",
        owner_layer_candidate="p7_hold004",
    )
    failed_recording = build_p7_hold004_official_group02_result_recording(run_result=failed_result)
    assert failed_recording["result_status"] == P7_HOLD004_GROUP02_RESULT_STATUS_FAILED_ISOLATED
    assert failed_recording["official_group_02_capture_result_recorded"] is True
    assert failed_recording["red_classification_required"] is True
    assert failed_recording["failed_group_ids"] == [P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID]
    assert failed_recording["can_claim_group_green"] is False
    assert failed_recording["can_claim_full_backend_suite_green"] is False
    assert failed_recording["release_allowed"] is False

    timeout_result = _group02_run_result(
        P7_HOLD004_BACKEND_SUITE_STATUS_TIMEOUT,
        passed=100,
        timed_out=True,
        elapsed_sec_bucket="over_budget",
        last_known_phase="run",
    )
    timeout_recording = build_p7_hold004_official_group02_result_recording(run_result=timeout_result)
    assert timeout_recording["result_status"] == P7_HOLD004_GROUP02_RESULT_STATUS_TIMEOUT_ISOLATED
    assert timeout_recording["official_group_02_capture_result_recorded"] is True
    assert timeout_recording["timeout_classification_required"] is True
    assert timeout_recording["long_run_probe_required"] is True
    assert timeout_recording["timeout_is_green"] is False
    assert timeout_recording["timeout_group_ids"] == [P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID]
    assert timeout_recording["can_claim_group_green"] is False
    assert timeout_recording["full_backend_suite_green_confirmed"] is False

    interrupted_result = _group02_run_result(
        P7_HOLD004_BACKEND_SUITE_STATUS_INTERRUPTED,
        passed=100,
        interrupted=True,
    )
    interrupted_recording = build_p7_hold004_official_group02_result_recording(run_result=interrupted_result)
    assert interrupted_recording["result_status"] == P7_HOLD004_GROUP02_RESULT_STATUS_PARTIAL_OR_INTERRUPTED
    assert interrupted_recording["official_group_02_capture_result_recorded"] is True
    assert interrupted_recording["partial_or_interrupted_group_ids"] == [P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID]
    assert interrupted_recording["can_claim_group_green"] is False
    assert interrupted_recording["can_claim_full_backend_suite_green"] is False
    assert interrupted_recording["hold004_close_allowed"] is False


def test_r40_contract_rejects_promotion_to_release_or_body_payload_retention() -> None:
    run_result = _group02_run_result(
        P7_HOLD004_BACKEND_SUITE_STATUS_PASS,
        passed=P7_HOLD004_GROUP02_OFFICIAL_TEST_ITEM_COUNT,
    )
    recording = build_p7_hold004_official_group02_result_recording(run_result=run_result)

    promoted_full_suite = deepcopy(recording)
    promoted_full_suite["can_claim_full_backend_suite_green"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_official_group02_result_recording_contract(promoted_full_suite)

    promoted_release = deepcopy(recording)
    promoted_release["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_official_group02_result_recording_contract(promoted_release)

    retained_body = deepcopy(recording)
    retained_body["raw_input_retained"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_official_group02_result_recording_contract(retained_body)

    public_contract_changed = deepcopy(recording)
    public_contract_changed["public_contract"]["api_response_key_added"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_official_group02_result_recording_contract(public_contract_changed)

    gate = build_p7_hold004_full_backend_suite_gate(official_group02_result_recording=recording)
    promoted_gate = deepcopy(gate)
    promoted_gate["full_backend_suite_green_confirmed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_full_backend_suite_gate_contract(promoted_gate)

    release_gate = deepcopy(gate)
    release_gate["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_full_backend_suite_gate_contract(release_gate)
