# -*- coding: utf-8 -*-
"""P7-HOLD-004 R43/R44 current snapshot collect drift contracts.

This test file is intentionally named outside the official group_02 glob
(``tests/test_emlis_ai_p7_hold004_*.py``) so validating R43/R44 does not change
the R41 frozen group_02 local execution count.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from emlis_ai_p7_hold004_backend_suite_split_consistency import (
    P7_HOLD004_BACKEND_COLLECT_BASELINE_ID,
    P7_HOLD004_BACKEND_COLLECT_WARNINGS_COUNT,
    P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT,
    P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT,
    P7_HOLD004_BACKEND_SOURCE_SNAPSHOT_REF,
    P7_HOLD004_BACKEND_TEST_FILES_SHA256,
    P7_HOLD004_BACKEND_TEST_ITEMS_SHA256,
)
from emlis_ai_p7_hold004_group02_result_current_snapshot_reconcile import (
    P7_HOLD004_ACTIVE_BASELINE_CURRENT_SNAPSHOT_DRIFT_CLASSIFICATION_ID,
    P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_FILE_COUNT,
    P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_FILE_REFS,
    P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_ITEM_COUNT,
    P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_DRIFT_EVIDENCE_ID,
    P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_WARNINGS_COUNT,
    P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECTED_TEST_FILE_COUNT,
    P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECTED_TEST_ITEM_COUNT,
    P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DELTA_TEST_FILE_COUNT,
    P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DELTA_TEST_ITEM_COUNT,
    P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DELTA_WARNINGS_COUNT,
    P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DRIFT_STATUS_R30_R42_TEST_ADDITION_ACCEPTED,
    P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DRIFT_STATUS_UNCLASSIFIED,
    P7_HOLD004_CURRENT_WORKING_SNAPSHOT_REF,
    P7_HOLD004_CURRENT_WORKING_SNAPSHOT_TEST_FILES_SHA256,
    P7_HOLD004_CURRENT_WORKING_SNAPSHOT_TEST_ITEMS_SHA256,
    assert_p7_hold004_active_baseline_current_snapshot_drift_classification_contract,
    assert_p7_hold004_current_working_snapshot_collect_drift_evidence_contract,
    build_p7_hold004_active_baseline_current_snapshot_drift_classification,
    build_p7_hold004_current_working_snapshot_collect_drift_evidence,
)


def test_r43_current_snapshot_collect_drift_freezes_432_2892_hashes_body_free() -> None:
    evidence = build_p7_hold004_current_working_snapshot_collect_drift_evidence()

    assert evidence["evidence_id"] == P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_DRIFT_EVIDENCE_ID
    assert evidence["current_working_snapshot_ref"] == P7_HOLD004_CURRENT_WORKING_SNAPSHOT_REF
    assert evidence["active_source_snapshot_ref"] == P7_HOLD004_BACKEND_SOURCE_SNAPSHOT_REF
    assert evidence["active_baseline_id"] == P7_HOLD004_BACKEND_COLLECT_BASELINE_ID
    assert evidence["current_collect_only"] == {
        "files": P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECTED_TEST_FILE_COUNT,
        "tests": P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECTED_TEST_ITEM_COUNT,
        "warnings": P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_WARNINGS_COUNT,
        "items_sha256": P7_HOLD004_CURRENT_WORKING_SNAPSHOT_TEST_ITEMS_SHA256,
        "files_sha256": P7_HOLD004_CURRENT_WORKING_SNAPSHOT_TEST_FILES_SHA256,
    }
    assert evidence["active_baseline_collect"] == {
        "files": P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT,
        "tests": P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT,
        "warnings": P7_HOLD004_BACKEND_COLLECT_WARNINGS_COUNT,
        "items_sha256": P7_HOLD004_BACKEND_TEST_ITEMS_SHA256,
        "files_sha256": P7_HOLD004_BACKEND_TEST_FILES_SHA256,
    }
    assert evidence["delta"] == {
        "files": P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DELTA_TEST_FILE_COUNT,
        "tests": P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DELTA_TEST_ITEM_COUNT,
        "warnings": P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DELTA_WARNINGS_COUNT,
    }
    assert evidence["body_free"] is True
    assert all(value is False for value in evidence["public_contract"].values())
    assert all(value is False for value in evidence["body_free_markers"].values())
    assert_p7_hold004_current_working_snapshot_collect_drift_evidence_contract(evidence)


def test_r43_collect_only_is_not_execution_green_and_not_active_baseline_update() -> None:
    evidence = build_p7_hold004_current_working_snapshot_collect_drift_evidence()

    assert evidence["current_collect_only_recorded"] is True
    assert evidence["active_baseline_differs_from_current_collect"] is True
    assert evidence["collect_only_is_not_execution_green"] is True
    assert evidence["current_collect_is_not_full_backend_suite_green"] is True
    assert evidence["current_collect_is_not_official_backend_execution"] is True
    assert evidence["active_baseline_update_allowed"] is False
    assert evidence["active_baseline_update_applied"] is False
    assert evidence["current_snapshot_baseline_adoption_allowed"] is False
    assert evidence["full_backend_execution_result_recorded"] is False
    assert evidence["full_backend_suite_execution_green_confirmed"] is False
    assert evidence["can_claim_full_backend_suite_green"] is False
    assert evidence["release_allowed"] is False


def test_r43_contract_rejects_full_suite_green_release_or_baseline_update_claim() -> None:
    evidence = build_p7_hold004_current_working_snapshot_collect_drift_evidence()

    promoted_full_suite = deepcopy(evidence)
    promoted_full_suite["full_backend_suite_green_confirmed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_current_working_snapshot_collect_drift_evidence_contract(promoted_full_suite)

    promoted_release = deepcopy(evidence)
    promoted_release["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_current_working_snapshot_collect_drift_evidence_contract(promoted_release)

    promoted_baseline_update = deepcopy(evidence)
    promoted_baseline_update["active_baseline_update_applied"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_current_working_snapshot_collect_drift_evidence_contract(promoted_baseline_update)


def test_r44_default_drift_classification_is_unclassified_until_file_diff_verified() -> None:
    classification = build_p7_hold004_active_baseline_current_snapshot_drift_classification()

    assert classification["classification_id"] == P7_HOLD004_ACTIVE_BASELINE_CURRENT_SNAPSHOT_DRIFT_CLASSIFICATION_ID
    assert classification["input_evidence_id"] == P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_DRIFT_EVIDENCE_ID
    assert classification["classification_status"] == P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DRIFT_STATUS_UNCLASSIFIED
    assert classification["drift_classified"] is False
    assert classification["added_test_file_refs"] == []
    assert classification["added_test_file_count"] == 0
    assert classification["added_test_item_count"] == 0
    assert classification["classification_is_current_working_snapshot_only"] is False
    assert classification["added_file_refs_are_contract_tests_only"] is False
    assert classification["active_baseline_update_allowed"] is False
    assert classification["release_allowed"] is False
    assert_p7_hold004_active_baseline_current_snapshot_drift_classification_contract(classification)


def test_r44_r30_r42_test_addition_classification_requires_exact_seven_file_refs_and_36_items() -> None:
    classification = build_p7_hold004_active_baseline_current_snapshot_drift_classification(
        added_test_file_refs=P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_FILE_REFS,
        added_test_item_count=P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_ITEM_COUNT,
        classification_status=P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DRIFT_STATUS_R30_R42_TEST_ADDITION_ACCEPTED,
    )

    assert classification["classification_status"] == (
        P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DRIFT_STATUS_R30_R42_TEST_ADDITION_ACCEPTED
    )
    assert classification["added_test_file_count"] == P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_FILE_COUNT
    assert classification["added_test_item_count"] == P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_ITEM_COUNT
    assert classification["added_test_refs_match_expected"] is True
    assert classification["added_test_item_count_matches_expected"] is True
    assert classification["collect_delta_matches_added_contract_tests"] is True
    assert classification["drift_classified"] is True
    assert classification["added_file_refs_are_contract_tests_only"] is True
    assert classification["classification_is_current_working_snapshot_only"] is True

    with pytest.raises(ValueError):
        build_p7_hold004_active_baseline_current_snapshot_drift_classification(
            added_test_file_refs=P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_FILE_REFS[:-1],
            added_test_item_count=P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_ITEM_COUNT,
            classification_status=P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DRIFT_STATUS_R30_R42_TEST_ADDITION_ACCEPTED,
        )

    with pytest.raises(ValueError):
        build_p7_hold004_active_baseline_current_snapshot_drift_classification(
            added_test_file_refs=P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_FILE_REFS,
            added_test_item_count=P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_ITEM_COUNT - 1,
            classification_status=P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DRIFT_STATUS_R30_R42_TEST_ADDITION_ACCEPTED,
        )


def test_r44_positive_classification_still_does_not_allow_active_baseline_update_or_release() -> None:
    classification = build_p7_hold004_active_baseline_current_snapshot_drift_classification(
        added_test_file_refs=P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_FILE_REFS,
        added_test_item_count=P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_ITEM_COUNT,
        classification_status=P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DRIFT_STATUS_R30_R42_TEST_ADDITION_ACCEPTED,
    )

    assert classification["collect_only_is_not_execution_green"] is True
    assert classification["classification_is_not_full_backend_suite_green"] is True
    assert classification["classification_is_not_active_baseline_adoption"] is True
    assert classification["classification_is_not_release_permission"] is True
    assert classification["active_baseline_update_allowed"] is False
    assert classification["active_baseline_update_applied"] is False
    assert classification["current_snapshot_baseline_adoption_allowed"] is False
    assert classification["group03_execution_allowed_by_this_classification"] is False
    assert classification["full_backend_suite_green_confirmed"] is False
    assert classification["hold004_close_allowed"] is False
    assert classification["p7_complete"] is False
    assert classification["p8_start_allowed"] is False
    assert classification["release_allowed"] is False


def test_r44_contract_rejects_semantic_no_change_claim_without_review() -> None:
    classification = build_p7_hold004_active_baseline_current_snapshot_drift_classification(
        added_test_file_refs=P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_FILE_REFS,
        added_test_item_count=P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_ITEM_COUNT,
        classification_status=P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DRIFT_STATUS_R30_R42_TEST_ADDITION_ACCEPTED,
    )

    semantic_claim = deepcopy(classification)
    semantic_claim["semantic_no_change_claimed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_active_baseline_current_snapshot_drift_classification_contract(semantic_claim)

    runtime_source_claim = deepcopy(classification)
    runtime_source_claim["production_runtime_source_change_claimed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_active_baseline_current_snapshot_drift_classification_contract(runtime_source_claim)
