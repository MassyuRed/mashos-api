# -*- coding: utf-8 -*-
"""R34/R35 contracts for P7-HOLD-004 active-baseline adoption evidence."""

from __future__ import annotations

import copy
import json

import pytest

from emlis_ai_p7_contracts import assert_p7_no_body_payload_or_contract_mutation
from emlis_ai_p7_hold004_active_baseline_adoption_evidence import (
    P7_HOLD004_ACTIVE_BASELINE_ADOPTION_EVIDENCE_BUNDLE_ID,
    P7_HOLD004_ACTIVE_BASELINE_ADOPTION_EVIDENCE_BUNDLE_SCHEMA_VERSION,
    P7_HOLD004_ACTIVE_BASELINE_ADOPTION_EVIDENCE_BUNDLE_STEP,
    P7_HOLD004_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_GATE_ID,
    P7_HOLD004_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_GATE_SCHEMA_VERSION,
    P7_HOLD004_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_GATE_STEP,
    P7_HOLD004_ITEM_FINGERPRINT_ROOT_CAUSE_REVIEW_ID,
    P7_HOLD004_LOCAL_REPEAT_COLLECT_EVIDENCE_ID,
    P7_HOLD004_ROOT_CAUSE_STATUS_BASELINE_CONSTANT_STALE,
    P7_HOLD004_SOURCE_IDENTITY_DECISION_ID,
    P7_HOLD004_TEST_SEMANTICS_REVIEW_ID,
    assert_p7_hold004_active_baseline_adoption_evidence_bundle_contract,
    assert_p7_hold004_conditional_active_baseline_adoption_gate_contract,
    build_p7_hold004_active_baseline_adoption_evidence_bundle,
    build_p7_hold004_conditional_active_baseline_adoption_gate,
    build_p7_hold004_item_fingerprint_root_cause_review,
    build_p7_hold004_local_repeat_collect_evidence,
    build_p7_hold004_source_identity_decision,
    build_p7_hold004_test_semantics_review,
)
from emlis_ai_p7_hold004_received_snapshot_baseline_fingerprint_reconcile import (
    P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT,
    P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT,
    P7_HOLD004_ACTIVE_TEST_ITEMS_FINGERPRINT_SHA256_AT_RECEIPT,
    P7_HOLD004_RECEIVED_ADOPTION_EVIDENCE_STATUS_SATISFIED_FOR_R27_CONDITIONAL_ADOPTION,
    P7_HOLD004_RECEIVED_ADOPTION_STATUS_ADOPTABLE_AS_RECEIVED_SNAPSHOT_BASELINE_REFRESH,
    P7_HOLD004_RECEIVED_SNAPSHOT_ADOPTION_EVIDENCE_FREEZE_ID,
    P7_HOLD004_RECEIVED_SNAPSHOT_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_ID,
    P7_HOLD004_RECEIVED_SNAPSHOT_CANDIDATE_NEW_BASELINE_ID,
    P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256,
    P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_ACCEPTED_AS_BASELINE_REFRESH,
    P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_NOT_REVIEWED,
    P7_HOLD004_RECEIVED_ZIP_REF,
    assert_p7_hold004_received_snapshot_adoption_evidence_freeze_contract,
    assert_p7_hold004_received_snapshot_conditional_active_baseline_adoption_contract,
)

_SAMPLE_COMMENT_TEXT = "これはユーザーに見える本文です。"
_SAMPLE_TERMINAL_OUTPUT = "tests/test_emlis_ai_p7_hold004_sample.py::test_sample PASSED"


def test_r30_to_r33_default_materials_are_present_before_r34() -> None:
    local = build_p7_hold004_local_repeat_collect_evidence()
    source_identity = build_p7_hold004_source_identity_decision(local_repeat_collect_evidence=local)
    root = build_p7_hold004_item_fingerprint_root_cause_review(
        local_repeat_collect_evidence=local,
        source_identity_decision=source_identity,
    )
    semantics = build_p7_hold004_test_semantics_review(root_cause_review=root)

    assert local["evidence_id"] == P7_HOLD004_LOCAL_REPEAT_COLLECT_EVIDENCE_ID
    assert source_identity["decision_id"] == P7_HOLD004_SOURCE_IDENTITY_DECISION_ID
    assert root["review_id"] == P7_HOLD004_ITEM_FINGERPRINT_ROOT_CAUSE_REVIEW_ID
    assert semantics["review_id"] == P7_HOLD004_TEST_SEMANTICS_REVIEW_ID
    assert local["satisfied"] is True
    assert source_identity["satisfied"] is True
    assert root["satisfied"] is True
    assert semantics["satisfied"] is True
    assert semantics["test_semantics_review_outcome"] == (
        P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_ACCEPTED_AS_BASELINE_REFRESH
    )
    assert semantics["active_baseline_update_allowed"] is False
    assert semantics["active_baseline_update_applied_to_runtime_builders"] is False
    assert semantics["release_allowed"] is False


def test_r34_adoption_evidence_bundle_connects_to_r27_without_allowing_update() -> None:
    bundle = build_p7_hold004_active_baseline_adoption_evidence_bundle()
    assert_p7_hold004_active_baseline_adoption_evidence_bundle_contract(bundle)

    assert bundle["schema_version"] == P7_HOLD004_ACTIVE_BASELINE_ADOPTION_EVIDENCE_BUNDLE_SCHEMA_VERSION
    assert bundle["implementation_step"] == P7_HOLD004_ACTIVE_BASELINE_ADOPTION_EVIDENCE_BUNDLE_STEP
    assert bundle["bundle_id"] == P7_HOLD004_ACTIVE_BASELINE_ADOPTION_EVIDENCE_BUNDLE_ID
    assert bundle["phase"] == "P7_ProductQualityRunner_LongRunGate"
    assert bundle["hold_id"] == "P7-HOLD-004"
    assert bundle["source_mode"] == "local_snapshot"
    assert bundle["git_checked"] is False
    assert bundle["local_repeat_collect_evidence_id"] == P7_HOLD004_LOCAL_REPEAT_COLLECT_EVIDENCE_ID
    assert bundle["source_identity_decision_id"] == P7_HOLD004_SOURCE_IDENTITY_DECISION_ID
    assert bundle["root_cause_review_id"] == P7_HOLD004_ITEM_FINGERPRINT_ROOT_CAUSE_REVIEW_ID
    assert bundle["test_semantics_review_id"] == P7_HOLD004_TEST_SEMANTICS_REVIEW_ID
    assert bundle["r27_adoption_evidence_freeze_id"] == P7_HOLD004_RECEIVED_SNAPSHOT_ADOPTION_EVIDENCE_FREEZE_ID
    assert_p7_hold004_received_snapshot_adoption_evidence_freeze_contract(bundle["r27_adoption_evidence_freeze"])

    assert bundle["previous_active_baseline"]["baseline_id"] == P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT
    assert bundle["previous_active_baseline"]["source_snapshot_ref"] == P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT
    assert bundle["previous_active_baseline"]["test_items_fingerprint_sha256"] == (
        P7_HOLD004_ACTIVE_TEST_ITEMS_FINGERPRINT_SHA256_AT_RECEIPT
    )
    assert bundle["candidate_active_baseline"]["baseline_id"] == P7_HOLD004_RECEIVED_SNAPSHOT_CANDIDATE_NEW_BASELINE_ID
    assert bundle["candidate_active_baseline"]["source_snapshot_ref"] == P7_HOLD004_RECEIVED_ZIP_REF
    assert bundle["candidate_active_baseline"]["test_items_fingerprint_sha256"] == P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256
    assert bundle["candidate_active_baseline"]["same_baseline_id_hash_replacement_allowed"] is False
    assert bundle["previous_active_baseline_retained"] is True
    assert bundle["same_baseline_id_hash_replacement_allowed"] is False

    assert bundle["r30_local_repeat_collect_evidence_satisfied"] is True
    assert bundle["r31_source_identity_decision_satisfied"] is True
    assert bundle["r32_root_cause_review_satisfied"] is True
    assert bundle["r33_test_semantics_review_satisfied"] is True
    assert bundle["adoption_evidence_freeze_satisfied"] is True
    assert bundle["can_mark_r27_conditions_satisfied"] is True
    assert bundle["adoption_evidence_status"] == P7_HOLD004_RECEIVED_ADOPTION_EVIDENCE_STATUS_SATISFIED_FOR_R27_CONDITIONAL_ADOPTION
    assert bundle["adoption_status_if_applied_to_r27"] == P7_HOLD004_RECEIVED_ADOPTION_STATUS_ADOPTABLE_AS_RECEIVED_SNAPSHOT_BASELINE_REFRESH
    assert bundle["r27_manual_boolean_only_adoption_ready_allowed"] is False

    assert bundle["active_baseline_update_allowed_by_evidence"] is False
    assert bundle["active_baseline_adoption_ready"] is False
    assert bundle["active_baseline_update_allowed"] is False
    assert bundle["source_snapshot_ref_update_allowed"] is False
    assert bundle["active_baseline_update_applied_to_runtime_builders"] is False
    assert bundle["source_snapshot_ref_updated_in_active_builders"] is False
    assert bundle["conditional_active_baseline_adoption_gate_not_built_in_r34"] is True
    assert bundle["official_group_02_capture_run_allowed"] is False
    assert bundle["can_claim_group_green"] is False
    assert bundle["can_claim_full_backend_suite_green"] is False
    assert bundle["full_backend_suite_green_confirmed"] is False
    assert bundle["hold004_close_allowed"] is False
    assert bundle["p7_complete"] is False
    assert bundle["p8_start_allowed"] is False
    assert bundle["release_allowed"] is False
    assert bundle["implementation_scope"]["r34_adoption_evidence_bundle_added"] is True
    assert bundle["implementation_scope"]["r35_conditional_active_baseline_adoption_gate_added"] is False
    assert "conditional_active_baseline_adoption_gate_required_after_r34" in bundle["required_followup_fixes"]
    assert all(value is False for value in bundle["public_contract"].values())
    assert all(value is False for value in bundle["body_free_markers"].values())
    assert bundle["body_free"] is True

    serialized = json.dumps(bundle, ensure_ascii=False, sort_keys=True)
    assert _SAMPLE_COMMENT_TEXT not in serialized
    assert _SAMPLE_TERMINAL_OUTPUT not in serialized
    assert "::test_" not in serialized
    assert "tests/test_emlis_ai_p7_hold004" not in serialized
    assert_p7_no_body_payload_or_contract_mutation(bundle, source="r34_bundle_test")


def test_r34_blocks_r27_connection_when_test_semantics_review_is_not_satisfied() -> None:
    not_reviewed = build_p7_hold004_test_semantics_review(
        test_semantics_reviewed=False,
        test_semantics_review_outcome=P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_NOT_REVIEWED,
    )
    bundle = build_p7_hold004_active_baseline_adoption_evidence_bundle(test_semantics_review=not_reviewed)
    assert_p7_hold004_active_baseline_adoption_evidence_bundle_contract(bundle)

    assert bundle["r33_test_semantics_review_satisfied"] is False
    assert bundle["adoption_evidence_freeze_satisfied"] is False
    assert bundle["can_mark_r27_conditions_satisfied"] is False
    assert bundle["adoption_status_if_applied_to_r27"] != P7_HOLD004_RECEIVED_ADOPTION_STATUS_ADOPTABLE_AS_RECEIVED_SNAPSHOT_BASELINE_REFRESH
    assert bundle["active_baseline_update_allowed"] is False
    assert bundle["source_snapshot_ref_update_allowed"] is False

    manual_ready = copy.deepcopy(bundle)
    manual_ready["can_mark_r27_conditions_satisfied"] = True
    manual_ready["adoption_evidence_freeze_satisfied"] = True
    manual_ready["adoption_status_if_applied_to_r27"] = P7_HOLD004_RECEIVED_ADOPTION_STATUS_ADOPTABLE_AS_RECEIVED_SNAPSHOT_BASELINE_REFRESH
    with pytest.raises(ValueError):
        assert_p7_hold004_active_baseline_adoption_evidence_bundle_contract(manual_ready)

    update_claim = build_p7_hold004_active_baseline_adoption_evidence_bundle()
    update_claim["active_baseline_update_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_active_baseline_adoption_evidence_bundle_contract(update_claim)


def test_r35_conditional_gate_allows_update_but_not_runtime_apply_or_green_claims() -> None:
    gate = build_p7_hold004_conditional_active_baseline_adoption_gate()
    assert_p7_hold004_conditional_active_baseline_adoption_gate_contract(gate)

    assert gate["schema_version"] == P7_HOLD004_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_GATE_SCHEMA_VERSION
    assert gate["implementation_step"] == P7_HOLD004_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_GATE_STEP
    assert gate["gate_id"] == P7_HOLD004_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_GATE_ID
    assert gate["phase"] == "P7_ProductQualityRunner_LongRunGate"
    assert gate["hold_id"] == "P7-HOLD-004"
    assert gate["source_mode"] == "local_snapshot"
    assert gate["git_checked"] is False
    assert gate["adoption_evidence_bundle_id"] == P7_HOLD004_ACTIVE_BASELINE_ADOPTION_EVIDENCE_BUNDLE_ID
    assert gate["r27_adoption_evidence_freeze_id"] == P7_HOLD004_RECEIVED_SNAPSHOT_ADOPTION_EVIDENCE_FREEZE_ID
    assert gate["r27_conditional_adoption_id"] == P7_HOLD004_RECEIVED_SNAPSHOT_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_ID
    assert_p7_hold004_received_snapshot_conditional_active_baseline_adoption_contract(
        gate["conditional_active_baseline_adoption"]
    )

    assert gate["previous_active_baseline"]["baseline_id"] == P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT
    assert gate["previous_active_baseline"]["source_snapshot_ref"] == P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT
    assert gate["candidate_active_baseline"]["baseline_id"] == P7_HOLD004_RECEIVED_SNAPSHOT_CANDIDATE_NEW_BASELINE_ID
    assert gate["candidate_active_baseline"]["source_snapshot_ref"] == P7_HOLD004_RECEIVED_ZIP_REF
    assert gate["candidate_active_baseline"]["test_items_fingerprint_sha256"] == P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256
    assert gate["root_cause_status"] == P7_HOLD004_ROOT_CAUSE_STATUS_BASELINE_CONSTANT_STALE
    assert gate["adoption_status"] == P7_HOLD004_RECEIVED_ADOPTION_STATUS_ADOPTABLE_AS_RECEIVED_SNAPSHOT_BASELINE_REFRESH
    assert gate["adoption_evidence_bundle_satisfied"] is True
    assert gate["adoption_evidence_freeze_satisfied"] is True
    assert gate["active_baseline_adoption_ready"] is True
    assert gate["active_baseline_update_allowed"] is True
    assert gate["source_snapshot_ref_update_allowed"] is True

    assert gate["same_baseline_id_hash_replacement_allowed"] is False
    assert gate["received_zip_promoted_to_source_snapshot_ref"] is False
    assert gate["active_baseline_update_applied_to_runtime_builders"] is False
    assert gate["source_snapshot_ref_updated_in_active_builders"] is False
    assert gate["official_group_02_capture_run_allowed"] is False
    assert gate["official_group_02_capture_result_recording_allowed"] is False
    assert gate["can_claim_group_green"] is False
    assert gate["can_claim_full_backend_suite_green"] is False
    assert gate["full_backend_suite_green_confirmed"] is False
    assert gate["hold004_close_allowed"] is False
    assert gate["p7_complete"] is False
    assert gate["p8_start_allowed"] is False
    assert gate["release_allowed"] is False
    assert gate["r35_is_gate_only_not_runtime_refresh"] is True
    assert gate["post_adoption_active_baseline_material_not_built_in_r35"] is True
    assert gate["runtime_builder_refresh_not_applied_in_r35"] is True
    assert gate["implementation_scope"]["r34_adoption_evidence_bundle_added"] is True
    assert gate["implementation_scope"]["r35_conditional_active_baseline_adoption_gate_added"] is True
    assert gate["implementation_scope"]["active_baseline_change_allowed"] is True
    assert gate["implementation_scope"]["runtime_builder_refresh_allowed"] is False
    assert "runtime_builder_refresh_required_after_r35" in gate["required_followup_fixes"]
    assert all(value is False for value in gate["public_contract"].values())
    assert all(value is False for value in gate["body_free_markers"].values())
    assert gate["body_free"] is True

    serialized = json.dumps(gate, ensure_ascii=False, sort_keys=True)
    assert _SAMPLE_COMMENT_TEXT not in serialized
    assert _SAMPLE_TERMINAL_OUTPUT not in serialized
    assert "::test_" not in serialized
    assert "tests/test_emlis_ai_p7_hold004" not in serialized
    assert_p7_no_body_payload_or_contract_mutation(gate, source="r35_gate_test")


def test_r35_contract_rejects_runtime_apply_release_and_manual_ready_without_evidence() -> None:
    not_reviewed = build_p7_hold004_test_semantics_review(
        test_semantics_reviewed=False,
        test_semantics_review_outcome=P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_NOT_REVIEWED,
    )
    blocked_bundle = build_p7_hold004_active_baseline_adoption_evidence_bundle(test_semantics_review=not_reviewed)
    blocked_gate = build_p7_hold004_conditional_active_baseline_adoption_gate(adoption_evidence_bundle=blocked_bundle)
    assert_p7_hold004_conditional_active_baseline_adoption_gate_contract(blocked_gate)
    assert blocked_gate["active_baseline_adoption_ready"] is False
    assert blocked_gate["active_baseline_update_allowed"] is False
    assert blocked_gate["source_snapshot_ref_update_allowed"] is False

    manual_ready = copy.deepcopy(blocked_gate)
    manual_ready["adoption_status"] = P7_HOLD004_RECEIVED_ADOPTION_STATUS_ADOPTABLE_AS_RECEIVED_SNAPSHOT_BASELINE_REFRESH
    manual_ready["active_baseline_adoption_ready"] = True
    manual_ready["active_baseline_update_allowed"] = True
    manual_ready["source_snapshot_ref_update_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_conditional_active_baseline_adoption_gate_contract(manual_ready)

    runtime_apply = build_p7_hold004_conditional_active_baseline_adoption_gate()
    runtime_apply["active_baseline_update_applied_to_runtime_builders"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_conditional_active_baseline_adoption_gate_contract(runtime_apply)

    source_updated = build_p7_hold004_conditional_active_baseline_adoption_gate()
    source_updated["source_snapshot_ref_updated_in_active_builders"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_conditional_active_baseline_adoption_gate_contract(source_updated)

    release_claim = build_p7_hold004_conditional_active_baseline_adoption_gate()
    release_claim["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_conditional_active_baseline_adoption_gate_contract(release_claim)
