# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import json

import pytest

from emlis_ai_p7_contracts import assert_p7_no_body_payload_or_contract_mutation
from emlis_ai_p7_hold004_active_baseline_adoption_evidence import (
    P7_HOLD004_LOCAL_ATTACHMENT_REF_OBSERVED,
    P7_HOLD004_LOCAL_REPEAT_COLLECT_EVIDENCE_SCHEMA_VERSION,
    P7_HOLD004_LOCAL_REPEAT_COLLECT_EVIDENCE_STEP,
    P7_HOLD004_SOURCE_IDENTITY_DECISION_SCHEMA_VERSION,
    P7_HOLD004_SOURCE_IDENTITY_DECISION_STEP,
    P7_HOLD004_SOURCE_IDENTITY_STATUS_RECEIVED_REF_ACCEPTED_ATTACHMENT_ALIAS_NOT_PROMOTED,
    assert_p7_hold004_local_repeat_collect_evidence_contract,
    assert_p7_hold004_source_identity_decision_contract,
    build_p7_hold004_local_repeat_collect_evidence,
    build_p7_hold004_source_identity_decision,
)
from emlis_ai_p7_hold004_received_snapshot_baseline_fingerprint_reconcile import (
    P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT,
    P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT,
    P7_HOLD004_RECEIVED_COLLECT_WARNINGS_COUNT,
    P7_HOLD004_RECEIVED_COLLECTED_TEST_FILE_COUNT,
    P7_HOLD004_RECEIVED_COLLECTED_TEST_ITEM_COUNT,
    P7_HOLD004_RECEIVED_SNAPSHOT_CANDIDATE_NEW_BASELINE_ID,
    P7_HOLD004_RECEIVED_TEST_FILES_FINGERPRINT_SHA256,
    P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256,
    P7_HOLD004_RECEIVED_ZIP_REF,
)

_SAMPLE_COMMENT_TEXT = "これは保存してはいけないcomment_text本文です。"
_SAMPLE_TERMINAL_OUTPUT = "============================= test session starts ============================="


def test_r30_local_repeat_collect_evidence_freezes_received_snapshot_collect_body_free() -> None:
    material = build_p7_hold004_local_repeat_collect_evidence()
    assert_p7_hold004_local_repeat_collect_evidence_contract(material)

    assert material["schema_version"] == P7_HOLD004_LOCAL_REPEAT_COLLECT_EVIDENCE_SCHEMA_VERSION
    assert material["phase"] == "P7_ProductQualityRunner_LongRunGate"
    assert material["implementation_step"] == P7_HOLD004_LOCAL_REPEAT_COLLECT_EVIDENCE_STEP
    assert material["hold_id"] == "P7-HOLD-004"
    assert material["source_mode"] == "local_snapshot"
    assert material["git_checked"] is False
    assert material["canonical_received_snapshot_ref"] == P7_HOLD004_RECEIVED_ZIP_REF
    assert material["local_attachment_ref_observed"] == P7_HOLD004_LOCAL_ATTACHMENT_REF_OBSERVED
    assert material["local_attachment_promoted_to_source_snapshot_ref"] is False
    assert material["collect_scope"] == "full_backend_collect_only"

    expected = material["expected"]
    assert expected["collected_test_file_count"] == P7_HOLD004_RECEIVED_COLLECTED_TEST_FILE_COUNT
    assert expected["collected_test_item_count"] == P7_HOLD004_RECEIVED_COLLECTED_TEST_ITEM_COUNT
    assert expected["warnings_count"] == P7_HOLD004_RECEIVED_COLLECT_WARNINGS_COUNT
    assert expected["test_items_fingerprint_sha256"] == P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256
    assert expected["test_files_fingerprint_sha256"] == P7_HOLD004_RECEIVED_TEST_FILES_FINGERPRINT_SHA256

    observed = material["observed"]
    assert material["collect_run_count"] == 2
    assert material["minimum_collect_run_count"] == 2
    assert observed["run_1_matches_expected"] is True
    assert observed["run_2_matches_expected"] is True
    assert observed["counts_warnings_fingerprints_stable"] is True
    assert observed["received_collect_matches_recorded_default"] is True

    assert material["counts_warnings_fingerprints_stable"] is True
    assert material["received_collect_matches_recorded_default"] is True
    assert material["satisfied"] is True
    assert material["collect_only_is_not_execution_green"] is True
    assert material["active_baseline_update_allowed"] is False
    assert material["official_group_02_capture_run_allowed"] is False
    assert material["can_claim_full_backend_suite_green"] is False
    assert material["release_allowed"] is False
    assert "P7-HOLD-004" in material["unresolved_hold_refs"]
    assert all(value is False for value in material["public_contract"].values())
    assert all(value is False for value in material["body_free_markers"].values())
    assert material["body_free"] is True

    serialized = json.dumps(material, ensure_ascii=False, sort_keys=True)
    assert _SAMPLE_COMMENT_TEXT not in serialized
    assert _SAMPLE_TERMINAL_OUTPUT not in serialized
    assert "::test_" not in serialized
    assert "tests/test_emlis_ai_p7_hold004" not in serialized
    assert_p7_no_body_payload_or_contract_mutation(material, source="r30_local_repeat_collect_evidence_test")


def test_r30_contract_blocks_manual_satisfaction_output_retention_and_local_alias_promotion() -> None:
    insufficient = build_p7_hold004_local_repeat_collect_evidence(collect_run_count=1)
    assert insufficient["satisfied"] is False
    assert insufficient["repeat_collect_evidence_satisfied"] is False
    assert_p7_hold004_local_repeat_collect_evidence_contract(insufficient)

    manual_satisfied = copy.deepcopy(insufficient)
    manual_satisfied["satisfied"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_local_repeat_collect_evidence_contract(manual_satisfied)

    retained_nodeids = build_p7_hold004_local_repeat_collect_evidence()
    retained_nodeids["nodeids_retained"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_local_repeat_collect_evidence_contract(retained_nodeids)

    promoted_alias = build_p7_hold004_local_repeat_collect_evidence()
    promoted_alias["local_attachment_promoted_to_source_snapshot_ref"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_local_repeat_collect_evidence_contract(promoted_alias)

    local_ref_claim = build_p7_hold004_local_repeat_collect_evidence()
    local_ref_claim["local_attachment_ref_observed"] = P7_HOLD004_RECEIVED_ZIP_REF
    with pytest.raises(ValueError):
        assert_p7_hold004_local_repeat_collect_evidence_contract(local_ref_claim)

    release_claim = build_p7_hold004_local_repeat_collect_evidence()
    release_claim["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_local_repeat_collect_evidence_contract(release_claim)


def test_r31_source_identity_decision_keeps_147_148_and_151_as_separate_refs() -> None:
    decision = build_p7_hold004_source_identity_decision()
    assert_p7_hold004_source_identity_decision_contract(decision)

    assert decision["schema_version"] == P7_HOLD004_SOURCE_IDENTITY_DECISION_SCHEMA_VERSION
    assert decision["implementation_step"] == P7_HOLD004_SOURCE_IDENTITY_DECISION_STEP
    assert decision["hold_id"] == "P7-HOLD-004"
    assert decision["active_baseline_id_at_receipt"] == P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT
    assert decision["active_source_snapshot_ref_at_receipt"] == P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT
    assert decision["canonical_received_snapshot_ref"] == P7_HOLD004_RECEIVED_ZIP_REF
    assert decision["local_attachment_ref_observed"] == P7_HOLD004_LOCAL_ATTACHMENT_REF_OBSERVED
    assert decision["candidate_active_baseline_id"] == P7_HOLD004_RECEIVED_SNAPSHOT_CANDIDATE_NEW_BASELINE_ID
    assert decision["candidate_source_snapshot_ref"] == P7_HOLD004_RECEIVED_ZIP_REF
    assert decision["source_identity_status"] == P7_HOLD004_SOURCE_IDENTITY_STATUS_RECEIVED_REF_ACCEPTED_ATTACHMENT_ALIAS_NOT_PROMOTED
    assert decision["source_identity_decision_recorded"] is True
    assert decision["source_identity_accepted"] is True
    assert decision["active_source_snapshot_ref_is_not_received_ref_at_receipt"] is True
    assert decision["local_attachment_promoted_to_source_snapshot_ref"] is False
    assert decision["received_zip_promoted_to_source_snapshot_ref_before_adoption"] is False
    assert decision["source_snapshot_ref_update_allowed_by_identity"] is True
    assert decision["same_baseline_id_hash_replacement_allowed"] is False
    assert decision["active_baseline_update_allowed"] is False
    assert decision["active_baseline_update_applied_to_runtime_builders"] is False
    assert decision["source_snapshot_ref_updated_in_active_builders"] is False
    assert decision["official_group_02_capture_run_allowed"] is False
    assert decision["release_allowed"] is False
    assert all(value is False for value in decision["public_contract"].values())
    assert all(value is False for value in decision["body_free_markers"].values())
    assert decision["body_free"] is True

    serialized = json.dumps(decision, ensure_ascii=False, sort_keys=True)
    assert _SAMPLE_COMMENT_TEXT not in serialized
    assert _SAMPLE_TERMINAL_OUTPUT not in serialized
    assert "::test_" not in serialized
    assert_p7_no_body_payload_or_contract_mutation(decision, source="r31_source_identity_decision_test")


def test_r31_contract_rejects_promoting_local_attachment_or_claiming_runtime_update() -> None:
    decision = build_p7_hold004_source_identity_decision()

    local_alias_promoted = copy.deepcopy(decision)
    local_alias_promoted["local_attachment_promoted_to_source_snapshot_ref"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_source_identity_decision_contract(local_alias_promoted)

    candidate_from_151 = copy.deepcopy(decision)
    candidate_from_151["candidate_source_snapshot_ref"] = P7_HOLD004_LOCAL_ATTACHMENT_REF_OBSERVED
    with pytest.raises(ValueError):
        assert_p7_hold004_source_identity_decision_contract(candidate_from_151)

    runtime_refresh_claim = copy.deepcopy(decision)
    runtime_refresh_claim["active_baseline_update_applied_to_runtime_builders"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_source_identity_decision_contract(runtime_refresh_claim)

    full_suite_claim = copy.deepcopy(decision)
    full_suite_claim["full_backend_suite_green_confirmed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_source_identity_decision_contract(full_suite_claim)

    accepted_mismatch = copy.deepcopy(decision)
    accepted_mismatch["source_identity_accepted"] = False
    with pytest.raises(ValueError):
        assert_p7_hold004_source_identity_decision_contract(accepted_mismatch)
