# -*- coding: utf-8 -*-
"""P7-HOLD-004 R45/R46 projection and P5/P6 return decision contracts.

The filename intentionally avoids ``tests/test_emlis_ai_p7_hold004_*.py`` so
this R45/R46 validation does not change the frozen official group_02 glob whose
R41 evidence records 252 passed / 1 warning.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from emlis_ai_p7_hold004_active_baseline_runtime_builder_refresh import (
    P7_HOLD004_GROUP02_RESULT_STATUS_PASSED_ISOLATED,
)
from emlis_ai_p7_hold004_group02_result_current_snapshot_reconcile import (
    P7_HOLD004_BACKEND_GROUP03_BLOCK_REASON_P5_P6_RETURN_PRIORITIZED,
    P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_FILE_REFS,
    P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_ITEM_COUNT,
    P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DRIFT_STATUS_R30_R42_TEST_ADDITION_ACCEPTED,
    P7_HOLD004_GROUP02_CURRENT_SNAPSHOT_RELEASE_PROJECTION_ID,
    P7_HOLD004_GROUP02_RECONCILE_SCOPE_GROUP02_ISOLATED_ONLY,
    P7_HOLD004_GROUP02_SOURCE_STATUS_ACCEPTED_AFTER_EXPLICIT_LOCAL_RERUN,
    P7_HOLD004_GROUP02_VALIDATION_SCOPE_ISOLATED_NOT_FULL_SUITE,
    P7_HOLD004_NEXT_DECISION_STATUS_P5_P6_RETURN_RECOMMENDED,
    P7_HOLD004_NEXT_EXECUTION_OR_P5_P6_RETURN_DECISION_ID,
    P7_HOLD004_NEXT_RECOMMENDED_WORK_P5_P6_HUMAN_READFEEL_REAL_DEVICE_MODAL,
    assert_p7_hold004_group02_current_snapshot_release_projection_contract,
    assert_p7_hold004_next_execution_or_p5_p6_return_decision_contract,
    build_p7_hold004_active_baseline_current_snapshot_drift_classification,
    build_p7_hold004_group02_current_snapshot_release_projection,
    build_p7_hold004_group02_local_execution_evidence,
    build_p7_hold004_group02_official_result_recording_reconcile,
    build_p7_hold004_next_execution_or_p5_p6_return_decision,
)


def _accepted_group02_reconcile() -> dict:
    evidence = build_p7_hold004_group02_local_execution_evidence(
        source_identity_status=P7_HOLD004_GROUP02_SOURCE_STATUS_ACCEPTED_AFTER_EXPLICIT_LOCAL_RERUN,
    )
    return build_p7_hold004_group02_official_result_recording_reconcile(
        local_execution_evidence=evidence,
        source_identity_status=P7_HOLD004_GROUP02_SOURCE_STATUS_ACCEPTED_AFTER_EXPLICIT_LOCAL_RERUN,
        apply_to_r40_official_recording=True,
    )


def _positive_drift_classification() -> dict:
    return build_p7_hold004_active_baseline_current_snapshot_drift_classification(
        added_test_file_refs=P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_FILE_REFS,
        added_test_item_count=P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_ITEM_COUNT,
        classification_status=P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DRIFT_STATUS_R30_R42_TEST_ADDITION_ACCEPTED,
    )


def test_r45_projection_records_group02_isolated_pass_and_current_drift_without_release() -> None:
    projection = build_p7_hold004_group02_current_snapshot_release_projection(
        group02_reconcile=_accepted_group02_reconcile(),
        drift_classification=_positive_drift_classification(),
    )

    assert projection["projection_id"] == P7_HOLD004_GROUP02_CURRENT_SNAPSHOT_RELEASE_PROJECTION_ID
    assert projection["group02_result_recording_status"] == P7_HOLD004_GROUP02_RESULT_STATUS_PASSED_ISOLATED
    assert projection["p7_hold004_group02_result_recording_status"] == P7_HOLD004_GROUP02_RESULT_STATUS_PASSED_ISOLATED
    assert projection["group02_result_scope"] == P7_HOLD004_GROUP02_RECONCILE_SCOPE_GROUP02_ISOLATED_ONLY
    assert projection["group02_pass_is_isolated"] is True
    assert projection["group02_pass_is_not_full_backend_suite_green"] is True
    assert projection["current_snapshot_collect_drift_status"] == (
        P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DRIFT_STATUS_R30_R42_TEST_ADDITION_ACCEPTED
    )
    assert projection["current_snapshot_collect_drift_classified"] is True
    assert projection["current_snapshot_baseline_adoption_allowed"] is False
    assert projection["full_backend_suite_green_confirmed"] is False
    assert projection["hold004_close_allowed"] is False
    assert projection["p7_complete"] is False
    assert projection["p8_start_allowed"] is False
    assert projection["release_allowed"] is False
    assert_p7_hold004_group02_current_snapshot_release_projection_contract(projection)


def test_r45_projection_keeps_matrix_release_handoff_validation_release_closed() -> None:
    projection = build_p7_hold004_group02_current_snapshot_release_projection()

    assert projection["matrix_projection"]["projection_scope"] == P7_HOLD004_GROUP02_VALIDATION_SCOPE_ISOLATED_NOT_FULL_SUITE
    assert projection["matrix_projection"]["p7_complete"] is False
    assert projection["matrix_projection"]["p8_start_allowed"] is False
    assert projection["matrix_projection"]["release_allowed"] is False
    assert projection["release_handoff_projection"]["full_backend_suite_green_confirmed"] is False
    assert projection["release_handoff_projection"]["can_claim_full_backend_suite_green"] is False
    assert projection["release_handoff_projection"]["hold004_close_allowed"] is False
    assert projection["release_handoff_projection"]["release_allowed"] is False
    assert projection["validation_projection"]["validation_scope"] == (
        P7_HOLD004_GROUP02_VALIDATION_SCOPE_ISOLATED_NOT_FULL_SUITE
    )
    assert projection["validation_projection"]["full_backend_suite_green_confirmed"] is False
    assert projection["validation_projection"]["release_allowed"] is False


def test_r45_projection_preserves_p5_p6_and_real_device_followups() -> None:
    projection = build_p7_hold004_group02_current_snapshot_release_projection()

    assert projection["p5_human_qa_review_required"] is True
    assert projection["p6_human_readfeel_review_required"] is True
    assert projection["real_device_submit_modal_readfeel_unverified"] is True
    assert projection["p7_hold004_remaining"] is True
    assert projection["p7_hold004_next_p5_p6_return_recommended"] is True
    assert "p5_human_qa_review_required" in projection["required_followup_fixes"]
    assert "p6_human_readfeel_review_required" in projection["required_followup_fixes"]
    assert "real_device_submit_modal_readfeel_unverified" in projection["required_followup_fixes"]


def test_r45_contract_rejects_not_run_reconcile_as_ready_projection() -> None:
    with pytest.raises(ValueError):
        build_p7_hold004_group02_current_snapshot_release_projection(
            group02_reconcile=build_p7_hold004_group02_official_result_recording_reconcile(),
            drift_classification=_positive_drift_classification(),
        )


def test_r46_next_decision_recommends_p5_p6_human_readfeel_after_r41_r45() -> None:
    projection = build_p7_hold004_group02_current_snapshot_release_projection()
    decision = build_p7_hold004_next_execution_or_p5_p6_return_decision(release_projection=projection)

    assert decision["decision_id"] == P7_HOLD004_NEXT_EXECUTION_OR_P5_P6_RETURN_DECISION_ID
    assert decision["release_projection_id"] == P7_HOLD004_GROUP02_CURRENT_SNAPSHOT_RELEASE_PROJECTION_ID
    assert decision["decision_status"] == P7_HOLD004_NEXT_DECISION_STATUS_P5_P6_RETURN_RECOMMENDED
    assert decision["next_recommended_work"] == P7_HOLD004_NEXT_RECOMMENDED_WORK_P5_P6_HUMAN_READFEEL_REAL_DEVICE_MODAL
    assert decision["p5_p6_return_recommended"] is True
    assert decision["backend_group03_execution_allowed_now"] is False
    assert decision["backend_group03_execution_block_reason"] == (
        P7_HOLD004_BACKEND_GROUP03_BLOCK_REASON_P5_P6_RETURN_PRIORITIZED
    )
    assert_p7_hold004_next_execution_or_p5_p6_return_decision_contract(decision)


def test_r46_next_decision_does_not_close_p7_hold004_or_start_p8() -> None:
    decision = build_p7_hold004_next_execution_or_p5_p6_return_decision()

    assert decision["p7_hold004_closed"] is False
    assert decision["p7_hold004_remaining"] is True
    assert decision["hold004_close_allowed"] is False
    assert decision["p7_complete"] is False
    assert decision["p8_start_allowed"] is False
    assert decision["release_allowed"] is False
    assert decision["backend_group03_execution_permanently_forbidden"] is False
    assert decision["backend_group03_execution_required_later"] is True
    assert decision["remaining_backend_groups_official_execution_required_later"] is True


def test_r46_contract_rejects_backend_group03_auto_continue_as_completion() -> None:
    decision = build_p7_hold004_next_execution_or_p5_p6_return_decision(
        backend_group03_auto_continue_requested=True,
    )
    assert decision["backend_group03_auto_continue_requested"] is True
    assert decision["backend_group03_auto_continue_rejected_as_completion"] is True
    assert_p7_hold004_next_execution_or_p5_p6_return_decision_contract(decision)

    promoted_group03 = deepcopy(decision)
    promoted_group03["backend_group03_execution_allowed_now"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_next_execution_or_p5_p6_return_decision_contract(promoted_group03)

    completion_claim = deepcopy(decision)
    completion_claim["backend_group03_auto_continue_rejected_as_completion"] = False
    with pytest.raises(ValueError):
        assert_p7_hold004_next_execution_or_p5_p6_return_decision_contract(completion_claim)
