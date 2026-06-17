# -*- coding: utf-8 -*-
"""Contract tests for P7-HOLD-004 R41/R42 group_02 result recording reconcile.

The test filename intentionally avoids ``test_emlis_ai_p7_hold004_*.py`` so that
adding this wrapper test does not change the frozen official group_02 glob whose
R41 evidence records 252 passed / 1 warning.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from emlis_ai_p7_hold004_active_baseline_runtime_builder_refresh import (
    P7_HOLD004_GROUP02_RESULT_STATUS_NOT_RUN,
    P7_HOLD004_GROUP02_RESULT_STATUS_PASSED_ISOLATED,
    assert_p7_hold004_official_group02_result_recording_contract,
    build_p7_hold004_official_group02_result_recording,
)
from emlis_ai_p7_hold004_backend_suite_execution_results import (
    P7_HOLD004_GROUP02_OFFICIAL_BATCH_ID,
    P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID,
    P7_HOLD004_GROUP02_OFFICIAL_TEST_ITEM_COUNT,
    P7_HOLD004_GROUP02_OFFICIAL_WARNINGS_COUNT,
)
from emlis_ai_p7_hold004_backend_suite_group_inventory_plan import (
    P7_HOLD004_BACKEND_SUITE_GROUP_IDS,
)
from emlis_ai_p7_hold004_group02_result_current_snapshot_reconcile import (
    P7_HOLD004_GROUP02_LOCAL_EXECUTION_COMMAND_SCOPE_ID,
    P7_HOLD004_GROUP02_LOCAL_EXECUTION_EVIDENCE_ID,
    P7_HOLD004_GROUP02_RECONCILE_SCOPE_GROUP02_ISOLATED_ONLY,
    P7_HOLD004_GROUP02_RECONCILE_SCOPE_NON_OFFICIAL_LOCAL_EVIDENCE,
    P7_HOLD004_GROUP02_SOURCE_STATUS_ACCEPTED_AFTER_EXPLICIT_LOCAL_RERUN,
    P7_HOLD004_GROUP02_SOURCE_STATUS_REQUIRES_DECISION,
    assert_p7_hold004_group02_local_execution_evidence_contract,
    assert_p7_hold004_group02_official_result_recording_reconcile_contract,
    build_p7_hold004_group02_local_execution_evidence,
    build_p7_hold004_group02_official_result_recording_reconcile,
)


def test_r41_group02_local_execution_evidence_freezes_252_passed_one_warning_body_free() -> None:
    evidence = build_p7_hold004_group02_local_execution_evidence()

    assert evidence["evidence_id"] == P7_HOLD004_GROUP02_LOCAL_EXECUTION_EVIDENCE_ID
    assert evidence["group_id"] == P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID
    assert evidence["batch_id"] == P7_HOLD004_GROUP02_OFFICIAL_BATCH_ID
    assert evidence["command_scope_id"] == P7_HOLD004_GROUP02_LOCAL_EXECUTION_COMMAND_SCOPE_ID
    assert evidence["status"] == "PASS"
    assert evidence["pytest_exit_code"] == 0
    assert evidence["observed_counts"] == {
        "passed": P7_HOLD004_GROUP02_OFFICIAL_TEST_ITEM_COUNT,
        "failed": 0,
        "skipped": 0,
        "warnings": P7_HOLD004_GROUP02_OFFICIAL_WARNINGS_COUNT,
        "errors": 0,
        "deselected": 0,
    }
    assert evidence["source_identity_status"] == P7_HOLD004_GROUP02_SOURCE_STATUS_REQUIRES_DECISION
    assert evidence["source_ref_differs_from_active_snapshot"] is True
    assert evidence["local_execution_passed"] is True
    assert evidence["official_result_recording_applied"] is False
    assert evidence["body_free"] is True
    assert all(value is False for value in evidence["public_contract"].values())
    assert all(value is False for value in evidence["body_free_markers"].values())
    assert_p7_hold004_group02_local_execution_evidence_contract(evidence)


def test_r41_local_execution_evidence_does_not_claim_official_group_green_or_release() -> None:
    evidence = build_p7_hold004_group02_local_execution_evidence()

    assert evidence["can_claim_group_green"] is False
    assert evidence["group_green_scope"] == P7_HOLD004_GROUP02_RECONCILE_SCOPE_NON_OFFICIAL_LOCAL_EVIDENCE
    assert evidence["can_claim_full_backend_suite_green"] is False
    assert evidence["full_backend_suite_green_confirmed"] is False
    assert evidence["hold004_close_allowed"] is False
    assert evidence["p7_complete"] is False
    assert evidence["p8_start_allowed"] is False
    assert evidence["release_allowed"] is False


def test_r41_contract_rejects_terminal_output_traceback_nodeids_or_comment_body() -> None:
    evidence = build_p7_hold004_group02_local_execution_evidence()

    retained_terminal = deepcopy(evidence)
    retained_terminal["terminal_output_retained"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_group02_local_execution_evidence_contract(retained_terminal)

    retained_traceback = deepcopy(evidence)
    retained_traceback["raw_traceback_included"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_group02_local_execution_evidence_contract(retained_traceback)

    retained_nodeids = deepcopy(evidence)
    retained_nodeids["nodeids_retained"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_group02_local_execution_evidence_contract(retained_nodeids)

    nodeid_collection = deepcopy(evidence)
    nodeid_collection["nodeids"] = ["tests/example.py::test_should_not_be_retained"]
    with pytest.raises(ValueError):
        assert_p7_hold004_group02_local_execution_evidence_contract(nodeid_collection)

    retained_comment_body = deepcopy(evidence)
    retained_comment_body["comment_text"] = "body must not be retained"
    with pytest.raises(ValueError):
        assert_p7_hold004_group02_local_execution_evidence_contract(retained_comment_body)


def test_r42_default_source_unaccepted_keeps_r40_not_run_and_local_pass_non_official() -> None:
    reconcile = build_p7_hold004_group02_official_result_recording_reconcile()

    assert reconcile["source_identity_status"] == P7_HOLD004_GROUP02_SOURCE_STATUS_REQUIRES_DECISION
    assert reconcile["apply_to_r40_official_recording_requested"] is False
    assert reconcile["official_recording_applied"] is False
    assert reconcile["group02_local_pass_recorded_as_non_official_evidence"] is True
    assert reconcile["official_group_02_result_recording_status"] == P7_HOLD004_GROUP02_RESULT_STATUS_NOT_RUN
    assert reconcile["can_claim_group_green"] is False
    assert reconcile["group_green_scope"] == P7_HOLD004_GROUP02_RECONCILE_SCOPE_NON_OFFICIAL_LOCAL_EVIDENCE
    assert reconcile["remaining_backend_group_count"] == len(P7_HOLD004_BACKEND_SUITE_GROUP_IDS)
    assert reconcile["r40_result_recording_projection"]["official_group_02_capture_result_recorded"] is False
    assert reconcile["full_backend_suite_green_confirmed"] is False
    assert reconcile["release_allowed"] is False
    assert "official_group02_source_identity_decision_required" in reconcile["required_followup_fixes"]
    assert_p7_hold004_group02_official_result_recording_reconcile_contract(reconcile)


def test_r42_apply_requested_without_source_acceptance_still_keeps_r40_not_run() -> None:
    reconcile = build_p7_hold004_group02_official_result_recording_reconcile(
        apply_to_r40_official_recording=True,
    )

    assert reconcile["apply_to_r40_official_recording_requested"] is True
    assert reconcile["source_identity_accepted_for_official_recording"] is False
    assert reconcile["official_recording_applied"] is False
    assert reconcile["official_group_02_result_recording_status"] == P7_HOLD004_GROUP02_RESULT_STATUS_NOT_RUN
    assert reconcile["remaining_backend_group_count"] == len(P7_HOLD004_BACKEND_SUITE_GROUP_IDS)
    assert reconcile["can_claim_group_green"] is False
    assert reconcile["release_allowed"] is False


def test_r42_explicit_source_accepted_records_passed_isolated_without_full_suite_promotion() -> None:
    evidence = build_p7_hold004_group02_local_execution_evidence(
        source_identity_status=P7_HOLD004_GROUP02_SOURCE_STATUS_ACCEPTED_AFTER_EXPLICIT_LOCAL_RERUN,
    )
    reconcile = build_p7_hold004_group02_official_result_recording_reconcile(
        local_execution_evidence=evidence,
        source_identity_status=P7_HOLD004_GROUP02_SOURCE_STATUS_ACCEPTED_AFTER_EXPLICIT_LOCAL_RERUN,
        apply_to_r40_official_recording=True,
    )

    assert reconcile["official_recording_applied"] is True
    assert reconcile["group02_local_pass_recorded_as_non_official_evidence"] is False
    assert reconcile["official_group_02_result_recording_status"] == P7_HOLD004_GROUP02_RESULT_STATUS_PASSED_ISOLATED
    assert reconcile["official_group_02_capture_green_confirmed"] is True
    assert reconcile["can_claim_group_green"] is True
    assert reconcile["group_green_scope"] == P7_HOLD004_GROUP02_RECONCILE_SCOPE_GROUP02_ISOLATED_ONLY
    assert reconcile["group02_pass_is_not_full_backend_suite_green"] is True
    assert reconcile["can_claim_full_backend_suite_green"] is False
    assert reconcile["full_backend_suite_green_confirmed"] is False
    assert reconcile["hold004_close_allowed"] is False
    assert reconcile["p7_complete"] is False
    assert reconcile["p8_start_allowed"] is False
    assert reconcile["release_allowed"] is False
    assert_p7_hold004_group02_official_result_recording_reconcile_contract(reconcile)


def test_r42_passed_isolated_full_backend_suite_gate_remains_blocked_remaining_groups() -> None:
    reconcile = build_p7_hold004_group02_official_result_recording_reconcile(
        local_execution_evidence=build_p7_hold004_group02_local_execution_evidence(
            source_identity_status=P7_HOLD004_GROUP02_SOURCE_STATUS_ACCEPTED_AFTER_EXPLICIT_LOCAL_RERUN,
        ),
        source_identity_status=P7_HOLD004_GROUP02_SOURCE_STATUS_ACCEPTED_AFTER_EXPLICIT_LOCAL_RERUN,
        apply_to_r40_official_recording=True,
    )

    assert reconcile["remaining_backend_group_count"] == len(P7_HOLD004_BACKEND_SUITE_GROUP_IDS) - 1
    assert reconcile["r40_full_backend_suite_gate_projection"]["remaining_backend_group_count"] == (
        len(P7_HOLD004_BACKEND_SUITE_GROUP_IDS) - 1
    )
    assert reconcile["r40_full_backend_suite_gate_projection"]["full_backend_suite_green_confirmed"] is False
    assert reconcile["r40_full_backend_suite_gate_projection"]["can_claim_full_backend_suite_green"] is False
    assert reconcile["r40_full_backend_suite_gate_projection"]["hold004_close_allowed"] is False
    assert reconcile["r40_full_backend_suite_gate_projection"]["release_allowed"] is False
    assert "remaining_backend_groups_official_execution_required" in reconcile["required_followup_fixes"]
    assert "current_snapshot_collect_drift_classification_required" in reconcile["required_followup_fixes"]


def test_r42_contract_rejects_release_p7_p8_hold004_or_full_suite_promotion() -> None:
    reconcile = build_p7_hold004_group02_official_result_recording_reconcile(
        local_execution_evidence=build_p7_hold004_group02_local_execution_evidence(
            source_identity_status=P7_HOLD004_GROUP02_SOURCE_STATUS_ACCEPTED_AFTER_EXPLICIT_LOCAL_RERUN,
        ),
        source_identity_status=P7_HOLD004_GROUP02_SOURCE_STATUS_ACCEPTED_AFTER_EXPLICIT_LOCAL_RERUN,
        apply_to_r40_official_recording=True,
    )

    promoted_full_suite = deepcopy(reconcile)
    promoted_full_suite["full_backend_suite_green_confirmed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_group02_official_result_recording_reconcile_contract(promoted_full_suite)

    promoted_release = deepcopy(reconcile)
    promoted_release["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_group02_official_result_recording_reconcile_contract(promoted_release)

    promoted_p7 = deepcopy(reconcile)
    promoted_p7["p7_complete"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_group02_official_result_recording_reconcile_contract(promoted_p7)

    promoted_p8 = deepcopy(reconcile)
    promoted_p8["p8_start_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_group02_official_result_recording_reconcile_contract(promoted_p8)

    closed_hold = deepcopy(reconcile)
    closed_hold["hold004_close_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_group02_official_result_recording_reconcile_contract(closed_hold)


def test_existing_r40_default_not_run_still_passes_without_wrapper_run_result() -> None:
    recording = build_p7_hold004_official_group02_result_recording()

    assert recording["official_group_02_result_recording_status"] == P7_HOLD004_GROUP02_RESULT_STATUS_NOT_RUN
    assert recording["official_group_02_capture_result_recorded"] is False
    assert recording["can_claim_group_green"] is False
    assert recording["can_claim_full_backend_suite_green"] is False
    assert recording["release_allowed"] is False
    assert_p7_hold004_official_group02_result_recording_contract(recording)
