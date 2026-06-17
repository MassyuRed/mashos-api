# -*- coding: utf-8 -*-
"""R36/R37 contracts for P7-HOLD-004 active-baseline runtime-builder refresh."""

from __future__ import annotations

import copy
import json

import pytest

from emlis_ai_p7_contracts import assert_p7_no_body_payload_or_contract_mutation
from emlis_ai_p7_hold004_active_baseline_runtime_builder_refresh import (
    P7_HOLD004_ACTIVE_BASELINE_REFRESH_ID,
    P7_HOLD004_POST_ADOPTION_ACTIVE_BASELINE_SCHEMA_VERSION,
    P7_HOLD004_POST_ADOPTION_ACTIVE_BASELINE_STEP,
    P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_ID,
    P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_SCHEMA_VERSION,
    P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_ID,
    P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_SCHEMA_VERSION,
    P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_STEP,
    assert_p7_hold004_post_adoption_active_baseline_material_contract,
    assert_p7_hold004_post_adoption_received_snapshot_reconcile_contract,
    assert_p7_hold004_runtime_builder_refresh_status_contract,
    build_p7_hold004_post_adoption_active_baseline_material,
    build_p7_hold004_post_adoption_received_snapshot_reconcile,
    build_p7_hold004_runtime_builder_refresh_status,
)
from emlis_ai_p7_hold004_backend_suite_split_consistency import (
    P7_HOLD004_BACKEND_ACTIVE_BASELINE_REFRESH_APPLIED,
    P7_HOLD004_BACKEND_COLLECT_BASELINE_ID,
    P7_HOLD004_BACKEND_SOURCE_SNAPSHOT_REF,
    P7_HOLD004_BACKEND_TEST_ITEMS_FINGERPRINT_SHA256,
    P7_HOLD004_PREVIOUS_ACTIVE_COLLECT_BASELINE_ID,
    P7_HOLD004_PREVIOUS_ACTIVE_SOURCE_SNAPSHOT_REF,
    P7_HOLD004_PREVIOUS_ACTIVE_TEST_ITEMS_SHA256,
    build_p7_hold004_backend_collect_baseline,
)
from emlis_ai_p7_hold004_received_snapshot_baseline_fingerprint_reconcile import (
    P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT,
    P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT,
    P7_HOLD004_ACTIVE_TEST_ITEMS_FINGERPRINT_SHA256_AT_RECEIPT,
    P7_HOLD004_RECEIVED_RECONCILE_STATUS_MATCHES_ACTIVE_BASELINE,
    P7_HOLD004_RECEIVED_SNAPSHOT_CANDIDATE_NEW_BASELINE_ID,
    P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256,
    P7_HOLD004_RECEIVED_ZIP_REF,
    build_p7_hold004_received_snapshot_baseline_fingerprint_reconcile,
)

_SAMPLE_COMMENT_TEXT = "これはユーザーに見える本文です。"
_SAMPLE_TERMINAL_OUTPUT = "tests/test_emlis_ai_p7_hold004_sample.py::test_sample PASSED"


def test_r36_post_adoption_active_baseline_material_retains_previous_and_builds_new_active() -> None:
    material = build_p7_hold004_post_adoption_active_baseline_material()
    assert_p7_hold004_post_adoption_active_baseline_material_contract(material)

    assert material["schema_version"] == P7_HOLD004_POST_ADOPTION_ACTIVE_BASELINE_SCHEMA_VERSION
    assert material["implementation_step"] == P7_HOLD004_POST_ADOPTION_ACTIVE_BASELINE_STEP
    assert material["active_baseline_refresh_id"] == P7_HOLD004_ACTIVE_BASELINE_REFRESH_ID
    assert material["phase"] == "P7_ProductQualityRunner_LongRunGate"
    assert material["hold_id"] == "P7-HOLD-004"
    assert material["source_mode"] == "local_snapshot"
    assert material["git_checked"] is False

    previous = material["previous_active_baseline"]
    current = material["current_active_baseline"]
    assert previous["baseline_id"] == P7_HOLD004_PREVIOUS_ACTIVE_COLLECT_BASELINE_ID
    assert previous["baseline_id"] == P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT
    assert previous["source_snapshot_ref"] == P7_HOLD004_PREVIOUS_ACTIVE_SOURCE_SNAPSHOT_REF
    assert previous["source_snapshot_ref"] == P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT
    assert previous["test_items_fingerprint_sha256"] == P7_HOLD004_PREVIOUS_ACTIVE_TEST_ITEMS_SHA256
    assert previous["test_items_fingerprint_sha256"] == P7_HOLD004_ACTIVE_TEST_ITEMS_FINGERPRINT_SHA256_AT_RECEIPT

    assert current["baseline_id"] == P7_HOLD004_RECEIVED_SNAPSHOT_CANDIDATE_NEW_BASELINE_ID
    assert current["baseline_id"] == P7_HOLD004_BACKEND_COLLECT_BASELINE_ID
    assert current["source_snapshot_ref"] == P7_HOLD004_RECEIVED_ZIP_REF
    assert current["source_snapshot_ref"] == P7_HOLD004_BACKEND_SOURCE_SNAPSHOT_REF
    assert current["test_items_fingerprint_sha256"] == P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256
    assert current["test_items_fingerprint_sha256"] == P7_HOLD004_BACKEND_TEST_ITEMS_FINGERPRINT_SHA256
    assert current["baseline_id"] != previous["baseline_id"]

    assert material["previous_active_baseline_retained"] is True
    assert material["historical_r21_r29_material_rewritten"] is False
    assert material["same_baseline_id_hash_replacement_allowed"] is False
    assert material["same_baseline_id_hash_replacement_applied"] is False
    assert material["candidate_baseline_id_changes"] is True
    assert material["candidate_baseline_matches_r35_gate"] is True
    assert material["active_baseline_refresh_applied"] is True
    assert material["post_adoption_active_baseline_material_built"] is True
    assert material["active_baseline_update_allowed"] is True
    assert material["source_snapshot_ref_update_allowed"] is True
    assert material["active_baseline_update_applied_to_runtime_builders"] is False
    assert material["source_snapshot_ref_updated_in_active_builders"] is False
    assert material["runtime_builder_refresh_not_applied_in_r36"] is True

    assert material["official_group_02_capture_run_allowed"] is False
    assert material["official_group_02_capture_result_recording_allowed"] is False
    assert material["can_claim_group_green"] is False
    assert material["can_claim_full_backend_suite_green"] is False
    assert material["full_backend_suite_green_confirmed"] is False
    assert material["hold004_close_allowed"] is False
    assert material["p7_complete"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["implementation_scope"]["r36_post_adoption_active_baseline_material_added"] is True
    assert material["implementation_scope"]["r37_runtime_builder_refresh_added"] is False
    assert "runtime_builder_refresh_required_after_r36" in material["required_followup_fixes"]
    assert all(value is False for value in material["public_contract"].values())
    assert all(value is False for value in material["body_free_markers"].values())
    assert material["body_free"] is True

    serialized = json.dumps(material, ensure_ascii=False, sort_keys=True)
    assert _SAMPLE_COMMENT_TEXT not in serialized
    assert _SAMPLE_TERMINAL_OUTPUT not in serialized
    assert "::test_" not in serialized
    assert "tests/test_emlis_ai_p7_hold004" not in serialized
    assert_p7_no_body_payload_or_contract_mutation(material, source="r36_post_adoption_material_test")


def test_r36_post_adoption_reconcile_resolves_received_snapshot_without_execution_green() -> None:
    reconcile = build_p7_hold004_post_adoption_received_snapshot_reconcile()
    assert_p7_hold004_post_adoption_received_snapshot_reconcile_contract(reconcile)

    assert reconcile["schema_version"] == P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_SCHEMA_VERSION
    assert reconcile["reconcile_id"] == P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_ID
    assert reconcile["classification"]["status"] == P7_HOLD004_RECEIVED_RECONCILE_STATUS_MATCHES_ACTIVE_BASELINE
    assert reconcile["received_snapshot_baseline_fingerprint_reconciled"] is True
    assert reconcile["received_snapshot_item_fingerprint_mismatch_unresolved"] is False
    assert reconcile["source_snapshot_ref_current_for_received_zip"] is True
    assert reconcile["active_baseline_accepts_received_nodeids"] is True

    comparison = reconcile["comparison"]
    assert comparison["test_items_fingerprint_match"] is True
    assert comparison["test_files_fingerprint_match"] is True
    assert comparison["counts_match"] is True
    assert comparison["warning_count_match"] is True
    assert comparison["source_snapshot_ref_matches_received_zip_ref"] is True

    assert reconcile["historical_r21_r29_material_rewritten"] is False
    assert reconcile["active_baseline_update_applied_to_runtime_builders"] is False
    assert reconcile["source_snapshot_ref_updated_in_active_builders"] is False
    assert reconcile["execution_green_confirmed"] is False
    assert reconcile["official_group_02_capture_run_allowed"] is False
    assert reconcile["full_backend_suite_green_confirmed"] is False
    assert reconcile["release_allowed"] is False
    assert all(value is False for value in reconcile["public_contract"].values())
    assert all(value is False for value in reconcile["body_free_markers"].values())
    assert_p7_no_body_payload_or_contract_mutation(reconcile, source="r36_post_adoption_reconcile_test")


def test_r36_contract_rejects_historical_rewrite_same_baseline_and_runtime_apply_claims() -> None:
    material = build_p7_hold004_post_adoption_active_baseline_material()

    rewritten = copy.deepcopy(material)
    rewritten["historical_r21_r29_material_rewritten"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_post_adoption_active_baseline_material_contract(rewritten)

    same_baseline = copy.deepcopy(material)
    same_baseline["current_active_baseline"]["baseline_id"] = same_baseline["previous_active_baseline"]["baseline_id"]
    with pytest.raises(ValueError):
        assert_p7_hold004_post_adoption_active_baseline_material_contract(same_baseline)

    applied_too_early = copy.deepcopy(material)
    applied_too_early["active_baseline_update_applied_to_runtime_builders"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_post_adoption_active_baseline_material_contract(applied_too_early)

    release_claim = copy.deepcopy(material)
    release_claim["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_post_adoption_active_baseline_material_contract(release_claim)


def test_r37_runtime_builder_refresh_status_connects_core_builders_without_green_or_release_claims() -> None:
    status = build_p7_hold004_runtime_builder_refresh_status()
    assert_p7_hold004_runtime_builder_refresh_status_contract(status)

    assert status["schema_version"] == P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_SCHEMA_VERSION
    assert status["implementation_step"] == P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_STEP
    assert status["refresh_status_id"] == P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_ID
    assert status["active_baseline_refresh_id"] == P7_HOLD004_ACTIVE_BASELINE_REFRESH_ID
    assert status["previous_active_baseline_id"] == P7_HOLD004_PREVIOUS_ACTIVE_COLLECT_BASELINE_ID
    assert status["current_active_baseline_id"] == P7_HOLD004_BACKEND_COLLECT_BASELINE_ID
    assert status["current_active_source_snapshot_ref"] == P7_HOLD004_BACKEND_SOURCE_SNAPSHOT_REF
    assert status["active_baseline_refresh_applied"] is True
    assert status["backend_active_baseline_refresh_applied_constant"] is True
    assert P7_HOLD004_BACKEND_ACTIVE_BASELINE_REFRESH_APPLIED is True
    assert status["current_collect_baseline_connected"] is True
    assert status["active_baseline_update_applied_to_runtime_builders"] is True
    assert status["source_snapshot_ref_updated_in_active_builders"] is True
    assert status["backend_suite_execution_summary_collect_baseline_id"] == P7_HOLD004_BACKEND_COLLECT_BASELINE_ID
    assert status["matrix_consistency_report_collect_baseline_id"] == P7_HOLD004_BACKEND_COLLECT_BASELINE_ID
    assert status["matrix_consistency_report_current_baseline_connected"] is True
    assert status["matrix_consistency_report_received_snapshot_status_refresh_deferred_to_r38"] is True

    expected_builder_refs = {
        "backend_suite_split_consistency",
        "backend_suite_group_inventory_plan",
        "backend_suite_execution_plan",
        "backend_suite_execution_results",
        "matrix_consistency_report",
        "group_execution_minimal_order",
    }
    assert set(status["updated_builder_refs"]) == expected_builder_refs
    for connection in status["builder_connections"]:
        assert connection["builder_ref"] in expected_builder_refs
        assert connection["collect_baseline_id"] == P7_HOLD004_BACKEND_COLLECT_BASELINE_ID
        assert connection["source_snapshot_ref"] == P7_HOLD004_BACKEND_SOURCE_SNAPSHOT_REF
        assert connection["current_active_baseline_id_match"] is True
        assert connection["current_active_source_snapshot_ref_match"] is True
        assert connection["release_allowed"] is False
        assert connection["full_backend_suite_green_confirmed"] is False
        assert connection["body_free"] is True

    assert status["received_snapshot_baseline_fingerprint_reconciled"] is True
    assert status["received_snapshot_item_fingerprint_mismatch_unresolved"] is False
    assert status["source_snapshot_ref_current_for_received_zip"] is True
    assert status["active_baseline_accepts_received_nodeids"] is True
    assert status["same_baseline_id_hash_replacement_allowed"] is False
    assert status["historical_r21_r29_material_rewritten"] is False
    assert status["official_group_02_capture_run_allowed"] is False
    assert status["official_group_02_capture_result_recording_allowed"] is False
    assert status["can_claim_group_green"] is False
    assert status["can_claim_full_backend_suite_green"] is False
    assert status["full_backend_suite_green_confirmed"] is False
    assert status["hold004_close_allowed"] is False
    assert status["p7_complete"] is False
    assert status["p8_start_allowed"] is False
    assert status["release_allowed"] is False
    assert status["implementation_scope"]["r37_runtime_builder_refresh_added"] is True
    assert status["implementation_scope"]["runtime_builder_refresh_applied"] is True
    assert "matrix_release_validation_connection_refresh_required_after_r37" in status["required_followup_fixes"]
    assert "post_adoption_reconcile_projection_required_for_hold_matrix_release_validation_after_r37" in status["required_followup_fixes"]
    assert "official_group_02_capture_readiness_re_evaluation_required_after_r37" in status["required_followup_fixes"]
    assert "full_backend_suite_green_unconfirmed" in status["required_followup_fixes"]
    assert all(value is False for value in status["public_contract"].values())
    assert all(value is False for value in status["body_free_markers"].values())
    assert status["body_free"] is True

    serialized = json.dumps(status, ensure_ascii=False, sort_keys=True)
    assert _SAMPLE_COMMENT_TEXT not in serialized
    assert _SAMPLE_TERMINAL_OUTPUT not in serialized
    assert "::test_" not in serialized
    assert "tests/test_emlis_ai_p7_hold004" not in serialized
    assert_p7_no_body_payload_or_contract_mutation(status, source="r37_runtime_builder_refresh_test")


def test_r37_contract_rejects_builder_drift_and_green_or_release_claims() -> None:
    status = build_p7_hold004_runtime_builder_refresh_status()

    drifted_source = copy.deepcopy(status)
    drifted_source["builder_connections"][1]["source_snapshot_ref"] = "mashos-api(151).zip"
    with pytest.raises(ValueError):
        assert_p7_hold004_runtime_builder_refresh_status_contract(drifted_source)

    drifted_baseline = copy.deepcopy(status)
    drifted_baseline["builder_connections"][2]["collect_baseline_id"] = P7_HOLD004_PREVIOUS_ACTIVE_COLLECT_BASELINE_ID
    with pytest.raises(ValueError):
        assert_p7_hold004_runtime_builder_refresh_status_contract(drifted_baseline)

    group_green_claim = copy.deepcopy(status)
    group_green_claim["can_claim_group_green"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_runtime_builder_refresh_status_contract(group_green_claim)

    release_claim = copy.deepcopy(status)
    release_claim["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_runtime_builder_refresh_status_contract(release_claim)


def test_r36_r37_keep_historical_received_snapshot_reconcile_old_while_runtime_baseline_is_current() -> None:
    historical = build_p7_hold004_received_snapshot_baseline_fingerprint_reconcile()
    runtime_collect = build_p7_hold004_backend_collect_baseline()

    assert historical["active_baseline"]["baseline_id"] == P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT
    assert historical["active_baseline"]["source_snapshot_ref"] == P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT
    assert historical["active_baseline"]["test_items_fingerprint_sha256"] == (
        P7_HOLD004_ACTIVE_TEST_ITEMS_FINGERPRINT_SHA256_AT_RECEIPT
    )
    assert historical["received_snapshot_baseline_fingerprint_reconciled"] is False
    assert historical["received_snapshot_item_fingerprint_mismatch_unresolved"] is True

    assert runtime_collect["baseline_id"] == P7_HOLD004_BACKEND_COLLECT_BASELINE_ID
    assert runtime_collect["source_snapshot_ref"] == P7_HOLD004_BACKEND_SOURCE_SNAPSHOT_REF
    assert runtime_collect["test_items_fingerprint_sha256"] == P7_HOLD004_BACKEND_TEST_ITEMS_FINGERPRINT_SHA256
    assert runtime_collect["baseline_id"] != historical["active_baseline"]["baseline_id"]
    assert runtime_collect["source_snapshot_ref"] != historical["active_baseline"]["source_snapshot_ref"]
