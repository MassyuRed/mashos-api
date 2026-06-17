# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import json

import pytest

from emlis_ai_p7_contracts import assert_p7_no_body_payload_or_contract_mutation
from emlis_ai_p7_hold004_active_baseline_adoption_evidence import (
    P7_HOLD004_ITEM_FINGERPRINT_ROOT_CAUSE_REVIEW_SCHEMA_VERSION,
    P7_HOLD004_ITEM_FINGERPRINT_ROOT_CAUSE_REVIEW_STEP,
    P7_HOLD004_ROOT_CAUSE_STATUS_BASELINE_CONSTANT_STALE,
    P7_HOLD004_TEST_SEMANTICS_REVIEW_SCHEMA_VERSION,
    P7_HOLD004_TEST_SEMANTICS_REVIEW_STEP,
    assert_p7_hold004_item_fingerprint_root_cause_review_contract,
    assert_p7_hold004_test_semantics_review_contract,
    build_p7_hold004_item_fingerprint_root_cause_review,
    build_p7_hold004_test_semantics_review,
)
from emlis_ai_p7_hold004_received_snapshot_baseline_fingerprint_reconcile import (
    P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT,
    P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT,
    P7_HOLD004_ACTIVE_TEST_ITEMS_FINGERPRINT_SHA256_AT_RECEIPT,
    P7_HOLD004_RECEIVED_ROOT_CAUSE_STATUS_UNCLASSIFIED,
    P7_HOLD004_RECEIVED_SNAPSHOT_CANDIDATE_NEW_BASELINE_ID,
    P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256,
    P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_ACCEPTED_AS_BASELINE_REFRESH,
    P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_NO_SEMANTIC_CHANGE_DETECTED,
    P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_NOT_REVIEWED,
    P7_HOLD004_RECEIVED_ZIP_REF,
)

_SAMPLE_COMMENT_TEXT = "これは保存してはいけないcomment_text本文です。"
_SAMPLE_TERMINAL_OUTPUT = "============================= test session starts ============================="


def test_r32_root_cause_review_classifies_stale_active_baseline_constant_without_overclaim() -> None:
    review = build_p7_hold004_item_fingerprint_root_cause_review()
    assert_p7_hold004_item_fingerprint_root_cause_review_contract(review)

    assert review["schema_version"] == P7_HOLD004_ITEM_FINGERPRINT_ROOT_CAUSE_REVIEW_SCHEMA_VERSION
    assert review["implementation_step"] == P7_HOLD004_ITEM_FINGERPRINT_ROOT_CAUSE_REVIEW_STEP
    assert review["phase"] == "P7_ProductQualityRunner_LongRunGate"
    assert review["hold_id"] == "P7-HOLD-004"
    assert review["source_mode"] == "local_snapshot"
    assert review["git_checked"] is False
    assert review["active_baseline_id_at_receipt"] == P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT
    assert review["active_source_snapshot_ref_at_receipt"] == P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT
    assert review["canonical_received_snapshot_ref"] == P7_HOLD004_RECEIVED_ZIP_REF
    assert review["candidate_active_baseline_id"] == P7_HOLD004_RECEIVED_SNAPSHOT_CANDIDATE_NEW_BASELINE_ID
    assert review["candidate_source_snapshot_ref"] == P7_HOLD004_RECEIVED_ZIP_REF
    assert review["active_item_fingerprint_sha256_at_receipt"] == P7_HOLD004_ACTIVE_TEST_ITEMS_FINGERPRINT_SHA256_AT_RECEIPT
    assert review["received_item_fingerprint_sha256"] == P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256
    assert review["root_cause_status"] == P7_HOLD004_ROOT_CAUSE_STATUS_BASELINE_CONSTANT_STALE
    assert review["root_cause_review_recorded"] is True
    assert review["root_cause_classified"] is True
    assert review["root_cause_unclassified"] is False
    assert review["root_cause_overclaim_absent"] is True
    assert review["parser_mismatch_evidence_present"] is False
    assert review["fingerprint_algorithm_mismatch_present"] is False
    assert review["environment_cause_claimed"] is False
    assert review["implementation_regression_claimed"] is False
    assert review["semantic_no_change_claimed"] is False
    assert review["same_baseline_id_hash_replacement_allowed"] is False
    assert review["previous_active_baseline_retained"] is True
    assert review["satisfied"] is True
    assert review["root_cause_review_satisfied"] is True
    assert review["collect_only_is_not_execution_green"] is True
    assert review["execution_green_confirmed"] is False
    assert review["active_baseline_update_allowed"] is False
    assert review["active_baseline_update_applied_to_runtime_builders"] is False
    assert review["official_group_02_capture_run_allowed"] is False
    assert review["can_claim_group_green"] is False
    assert review["can_claim_full_backend_suite_green"] is False
    assert review["full_backend_suite_green_confirmed"] is False
    assert review["hold004_close_allowed"] is False
    assert review["release_allowed"] is False
    assert "P7-HOLD-004" in review["unresolved_hold_refs"]
    assert review["implementation_scope"]["r30_local_repeat_collect_evidence_freeze_added"] is True
    assert review["implementation_scope"]["r31_source_identity_decision_boundary_added"] is True
    assert review["implementation_scope"]["r32_root_cause_review_added"] is True
    assert review["implementation_scope"]["r33_test_semantics_review_added"] is False
    assert review["implementation_scope"]["r34_adoption_evidence_bundle_added"] is False
    assert "test_semantics_review_required" in review["required_followup_fixes"]
    assert all(value is False for value in review["public_contract"].values())
    assert all(value is False for value in review["body_free_markers"].values())
    assert review["body_free"] is True

    conditions = review["review_conditions"]
    assert conditions["repeat_collect_stable"] is True
    assert conditions["source_identity_accepted"] is True
    assert conditions["counts_match"] is True
    assert conditions["warning_count_match"] is True
    assert conditions["test_files_fingerprint_match"] is True
    assert conditions["test_items_fingerprint_diff_recorded"] is True
    assert conditions["received_item_fingerprint_matches_local_repeat_collect"] is True
    assert conditions["received_file_fingerprint_matches_local_repeat_collect"] is True
    assert conditions["fingerprint_algorithm_match"] is True
    assert conditions["parser_mismatch_absent"] is True
    assert conditions["semantic_no_change_not_claimed_in_r32"] is True
    assert conditions["same_baseline_id_hash_replacement_blocked"] is True

    serialized = json.dumps(review, ensure_ascii=False, sort_keys=True)
    assert _SAMPLE_COMMENT_TEXT not in serialized
    assert _SAMPLE_TERMINAL_OUTPUT not in serialized
    assert "::test_" not in serialized
    assert "tests/test_emlis_ai_p7_hold004" not in serialized
    assert_p7_no_body_payload_or_contract_mutation(review, source="r32_root_cause_review_test")


def test_r32_contract_blocks_unclassified_and_overclaimed_satisfied_material() -> None:
    unclassified = build_p7_hold004_item_fingerprint_root_cause_review(
        root_cause_status=P7_HOLD004_RECEIVED_ROOT_CAUSE_STATUS_UNCLASSIFIED
    )
    assert unclassified["satisfied"] is False
    assert unclassified["root_cause_unclassified"] is True
    assert_p7_hold004_item_fingerprint_root_cause_review_contract(unclassified)

    manual_satisfied = copy.deepcopy(unclassified)
    manual_satisfied["satisfied"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_item_fingerprint_root_cause_review_contract(manual_satisfied)

    with pytest.raises(ValueError):
        build_p7_hold004_item_fingerprint_root_cause_review(environment_cause_claimed=True)

    with pytest.raises(ValueError):
        build_p7_hold004_item_fingerprint_root_cause_review(semantic_no_change_claimed=True)

    release_claim = build_p7_hold004_item_fingerprint_root_cause_review()
    release_claim["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_item_fingerprint_root_cause_review_contract(release_claim)

    runtime_refresh_claim = build_p7_hold004_item_fingerprint_root_cause_review()
    runtime_refresh_claim["active_baseline_update_applied_to_runtime_builders"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_item_fingerprint_root_cause_review_contract(runtime_refresh_claim)


def test_r33_test_semantics_review_accepts_baseline_refresh_without_no_semantic_change_claim() -> None:
    review = build_p7_hold004_test_semantics_review()
    assert_p7_hold004_test_semantics_review_contract(review)

    assert review["schema_version"] == P7_HOLD004_TEST_SEMANTICS_REVIEW_SCHEMA_VERSION
    assert review["implementation_step"] == P7_HOLD004_TEST_SEMANTICS_REVIEW_STEP
    assert review["phase"] == "P7_ProductQualityRunner_LongRunGate"
    assert review["hold_id"] == "P7-HOLD-004"
    assert review["source_mode"] == "local_snapshot"
    assert review["git_checked"] is False
    assert review["active_baseline_id_at_receipt"] == P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT
    assert review["canonical_received_snapshot_ref"] == P7_HOLD004_RECEIVED_ZIP_REF
    assert review["candidate_active_baseline_id"] == P7_HOLD004_RECEIVED_SNAPSHOT_CANDIDATE_NEW_BASELINE_ID
    assert review["active_item_fingerprint_sha256_at_receipt"] == P7_HOLD004_ACTIVE_TEST_ITEMS_FINGERPRINT_SHA256_AT_RECEIPT
    assert review["received_item_fingerprint_sha256"] == P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256
    assert review["root_cause_status"] == P7_HOLD004_ROOT_CAUSE_STATUS_BASELINE_CONSTANT_STALE
    assert review["root_cause_review_satisfied"] is True
    assert review["test_semantics_reviewed"] is True
    assert review["test_semantics_review_outcome"] == P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_ACCEPTED_AS_BASELINE_REFRESH
    assert review["preferred_outcome"] == P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_ACCEPTED_AS_BASELINE_REFRESH
    assert review["optional_outcome_if_body_free_old_nodeid_review_exists"] == P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_NO_SEMANTIC_CHANGE_DETECTED
    assert review["old_nodeid_list_available"] is False
    assert review["body_free_nodeid_diff_review_available"] is False
    assert review["no_semantic_change_claimed"] is False
    assert review["accepted_as_baseline_refresh"] is True
    assert review["accepted_as_baseline_refresh_supported"] is True
    assert review["no_semantic_change_supported"] is False
    assert review["nodeids_retained"] is False
    assert review["pytest_output_retained"] is False
    assert review["test_body_retained"] is False
    assert review["satisfied"] is True
    assert review["test_semantics_review_satisfied"] is True
    assert review["adoption_evidence_bundle_not_built_in_r33"] is True
    assert review["collect_only_is_not_execution_green"] is True
    assert review["execution_green_confirmed"] is False
    assert review["active_baseline_update_allowed"] is False
    assert review["active_baseline_update_applied_to_runtime_builders"] is False
    assert review["official_group_02_capture_run_allowed"] is False
    assert review["can_claim_group_green"] is False
    assert review["can_claim_full_backend_suite_green"] is False
    assert review["full_backend_suite_green_confirmed"] is False
    assert review["hold004_close_allowed"] is False
    assert review["release_allowed"] is False
    assert review["implementation_scope"]["r30_local_repeat_collect_evidence_freeze_added"] is True
    assert review["implementation_scope"]["r31_source_identity_decision_boundary_added"] is True
    assert review["implementation_scope"]["r32_root_cause_review_added"] is True
    assert review["implementation_scope"]["r33_test_semantics_review_added"] is True
    assert review["implementation_scope"]["r34_adoption_evidence_bundle_added"] is False
    assert "adoption_evidence_bundle_required_before_active_baseline_update" in review["required_followup_fixes"]
    assert all(value is False for value in review["public_contract"].values())
    assert all(value is False for value in review["body_free_markers"].values())
    assert review["body_free"] is True

    serialized = json.dumps(review, ensure_ascii=False, sort_keys=True)
    assert _SAMPLE_COMMENT_TEXT not in serialized
    assert _SAMPLE_TERMINAL_OUTPUT not in serialized
    assert "::test_" not in serialized
    assert "tests/test_emlis_ai_p7_hold004" not in serialized
    assert_p7_no_body_payload_or_contract_mutation(review, source="r33_test_semantics_review_test")


def test_r33_contract_rejects_not_reviewed_no_change_without_body_free_review_and_body_retention() -> None:
    not_reviewed = build_p7_hold004_test_semantics_review(
        test_semantics_reviewed=False,
        test_semantics_review_outcome=P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_NOT_REVIEWED,
    )
    assert not_reviewed["satisfied"] is False
    assert_p7_hold004_test_semantics_review_contract(not_reviewed)

    manual_satisfied = copy.deepcopy(not_reviewed)
    manual_satisfied["satisfied"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_test_semantics_review_contract(manual_satisfied)

    with pytest.raises(ValueError):
        build_p7_hold004_test_semantics_review(
            test_semantics_review_outcome=P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_NO_SEMANTIC_CHANGE_DETECTED
        )

    no_change_with_body_free_old_nodeid_review = build_p7_hold004_test_semantics_review(
        test_semantics_review_outcome=P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_NO_SEMANTIC_CHANGE_DETECTED,
        old_nodeid_list_available=True,
        body_free_nodeid_diff_review_available=True,
    )
    assert no_change_with_body_free_old_nodeid_review["satisfied"] is True
    assert no_change_with_body_free_old_nodeid_review["no_semantic_change_supported"] is True
    assert no_change_with_body_free_old_nodeid_review["nodeids_retained"] is False
    assert_p7_hold004_test_semantics_review_contract(no_change_with_body_free_old_nodeid_review)

    retained_nodeids = build_p7_hold004_test_semantics_review()
    retained_nodeids["nodeids_retained"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_test_semantics_review_contract(retained_nodeids)

    release_claim = build_p7_hold004_test_semantics_review()
    release_claim["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_test_semantics_review_contract(release_claim)
