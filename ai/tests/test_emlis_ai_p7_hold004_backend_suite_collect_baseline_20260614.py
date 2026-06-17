# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json

import pytest

from emlis_ai_p7_contracts import assert_p7_no_body_payload_or_contract_mutation
from emlis_ai_p7_hold004_backend_suite_split_consistency import (
    P7_HOLD004_BACKEND_COLLECT_BASELINE_ID,
    P7_HOLD004_BACKEND_COLLECT_BASELINE_SCHEMA_VERSION,
    P7_HOLD004_BACKEND_COLLECT_BASELINE_STEP,
    P7_HOLD004_BACKEND_COLLECT_COMMAND_ID,
    P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM,
    P7_HOLD004_BACKEND_COLLECT_STATUS_COLLECTED,
    P7_HOLD004_BACKEND_CONTRACT_BOUNDARY_FREEZE_SCHEMA_VERSION,
    P7_HOLD004_CURRENT_BACKEND_COLLECT_WARNINGS_COUNT,
    P7_HOLD004_CURRENT_BACKEND_COLLECTED_TEST_FILE_COUNT,
    P7_HOLD004_CURRENT_BACKEND_COLLECTED_TEST_ITEM_COUNT,
    P7_HOLD004_CURRENT_TEST_FILES_FINGERPRINT_SHA256,
    P7_HOLD004_CURRENT_TEST_ITEMS_FINGERPRINT_SHA256,
    assert_p7_hold004_backend_collect_baseline_contract,
    assert_p7_hold004_backend_suite_contract_boundary_freeze_contract,
    build_p7_hold004_backend_collect_baseline,
    build_p7_hold004_backend_collect_summary_from_nodeids,
    build_p7_hold004_backend_suite_contract_boundary_freeze,
)
from emlis_ai_p7_hold004_current_snapshot_baseline_reconcile import (
    assert_p7_hold004_current_snapshot_baseline_reconcile_contract,
    build_p7_hold004_current_snapshot_baseline_reconcile,
)
from emlis_ai_p7_hold004_received_snapshot_baseline_fingerprint_reconcile import (
    P7_HOLD004_RECEIVED_ADOPTION_STATUS_ADOPTABLE_AS_RECEIVED_SNAPSHOT_BASELINE_REFRESH,
    P7_HOLD004_RECEIVED_ADOPTION_STATUS_BLOCKED_ADOPTION_EVIDENCE_NOT_FROZEN,
    P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT,
    P7_HOLD004_RECEIVED_ADOPTION_STATUS_BLOCKED_UNCLASSIFIED_ITEM_FINGERPRINT_MISMATCH,
    P7_HOLD004_RECEIVED_COLLECT_COMMAND_ID,
    P7_HOLD004_RECEIVED_COLLECT_WARNINGS_COUNT,
    P7_HOLD004_RECEIVED_COLLECTED_TEST_FILE_COUNT,
    P7_HOLD004_RECEIVED_COLLECTED_TEST_ITEM_COUNT,
    P7_HOLD004_RECEIVED_RECONCILE_STATUS_ITEM_FINGERPRINT_MISMATCH_UNCLASSIFIED,
    P7_HOLD004_RECEIVED_ROOT_CAUSE_STATUS_UNCLASSIFIED,
    P7_HOLD004_RECEIVED_SNAPSHOT_ADOPTION_EVIDENCE_FREEZE_SCHEMA_VERSION,
    P7_HOLD004_RECEIVED_SNAPSHOT_ADOPTION_EVIDENCE_FREEZE_STEP,
    P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_ADOPTION_DECISION_SCHEMA_VERSION,
    P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_SCHEMA_VERSION,
    P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_STEP,
    P7_HOLD004_RECEIVED_SNAPSHOT_COLLECT_SUMMARY_SCHEMA_VERSION,
    P7_HOLD004_RECEIVED_SNAPSHOT_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_SCHEMA_VERSION,
    P7_HOLD004_RECEIVED_SNAPSHOT_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_STEP,
    P7_HOLD004_RECEIVED_SNAPSHOT_R29_VERIFICATION_PROCEDURE_SCHEMA_VERSION,
    P7_HOLD004_RECEIVED_SNAPSHOT_R29_VERIFICATION_PROCEDURE_STEP,
    P7_HOLD004_RECEIVED_SNAPSHOT_SCOPE_FREEZE_SCHEMA_VERSION,
    P7_HOLD004_RECEIVED_TEST_FILES_FINGERPRINT_SHA256,
    P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256,
    P7_HOLD004_RECEIVED_ZIP_REF,
    assert_p7_hold004_received_snapshot_adoption_evidence_freeze_contract,
    assert_p7_hold004_received_snapshot_baseline_adoption_decision_contract,
    assert_p7_hold004_received_snapshot_baseline_fingerprint_reconcile_contract,
    assert_p7_hold004_received_snapshot_conditional_active_baseline_adoption_contract,
    assert_p7_hold004_received_snapshot_r29_verification_procedure_contract,
    assert_p7_hold004_received_snapshot_collect_summary_contract,
    assert_p7_hold004_received_snapshot_scope_freeze_contract,
    build_p7_hold004_received_snapshot_adoption_evidence_freeze,
    build_p7_hold004_received_snapshot_baseline_adoption_decision,
    build_p7_hold004_received_snapshot_baseline_fingerprint_reconcile,
    build_p7_hold004_received_snapshot_conditional_active_baseline_adoption,
    build_p7_hold004_received_snapshot_r29_verification_procedure,
    build_p7_hold004_received_snapshot_collect_summary,
    build_p7_hold004_received_snapshot_scope_freeze,
)

_SAMPLE_COMMENT_TEXT = "これは保存してはいけないcomment_text本文です。"
_SAMPLE_TERMINAL_OUTPUT = "============================= test session starts ============================="


def _sha256_joined(values: list[str]) -> str:
    return hashlib.sha256("\n".join(values).encode("utf-8")).hexdigest()


def _assert_r13_current_snapshot_baseline_reconcile_material() -> None:
    material = build_p7_hold004_current_snapshot_baseline_reconcile()

    assert material["schema_version"] == "cocolon.emlis.p7.hold004.current_snapshot_baseline_reconcile.v1"
    assert material["phase"] == "P7_ProductQualityRunner_LongRunGate"
    assert material["step"] == "P7-HOLD-004_CurrentSnapshotBaselineReconcile_R13_20260615"
    assert material["hold_id"] == "P7-HOLD-004"
    assert material["reconcile_id"] == "p7_hold004_current_snapshot_baseline_reconcile_20260615"
    assert material["source_mode"] == "local_snapshot"
    assert material["source_snapshot_ref"] == "mashos-api(147).zip"
    assert material["git_checked"] is False

    previous = material["previous_baseline"]
    assert previous["baseline_id"] == "p7_hold004_backend_collect_baseline_20260614"
    assert previous["source_snapshot_ref"] == "mashos-api(146).zip"
    assert previous["test_file_count"] == 416
    assert previous["test_item_count"] == 2673
    assert previous["warnings_count"] == 1
    assert previous["group_02_file_count"] == 10
    assert previous["group_02_test_item_count"] == 69

    current = material["current_baseline"]
    assert current["baseline_id"] == "p7_hold004_backend_collect_baseline_20260615"
    assert current["source_snapshot_ref"] == "mashos-api(147).zip"
    assert current["test_file_count"] == 425
    assert current["test_item_count"] == 2856
    assert current["warnings_count"] == 1
    assert current["test_items_fingerprint_sha256"] == (
        "fee1eca805564d0840dc5b23f60a7e2d6c7297d658a76dc4ce175e0137c261f1"
    )
    assert current["test_files_fingerprint_sha256"] == (
        "6866231daf68427dca2de1b2011feea49450f7b4a8b3c5b9dec0f9ccd5f3e9c6"
    )
    assert previous["baseline_id"] != current["baseline_id"]

    delta = material["delta"]
    assert delta["test_file_count_delta"] == 9
    assert delta["test_item_count_delta"] == 183
    assert delta["warnings_count_delta"] == 0
    assert delta["affected_group_ids"] == ["group_02_p7_hold004"]
    assert delta["file_level_delta_refs_included"] is False
    assert delta["nodeid_refs_included"] is False

    group_delta = delta["group_deltas"][0]
    assert group_delta["group_id"] == "group_02_p7_hold004"
    assert group_delta["old_file_count"] == 10
    assert group_delta["old_test_item_count"] == 69
    assert group_delta["current_file_count"] == 19
    assert group_delta["current_test_item_count"] == 252
    assert group_delta["file_count_delta"] == 9
    assert group_delta["test_item_count_delta"] == 183

    decision = material["decision"]
    assert decision["current_baseline_should_replace_active_baseline"] is True
    assert decision["previous_baseline_retained_as_previous"] is True
    assert decision["group_inventory_refresh_required"] is True
    assert decision["execution_plan_refresh_required"] is True
    assert decision["matrix_reconnect_required"] is True
    assert decision["official_group_execution_blocked_until_refresh"] is True
    assert decision["collect_only_is_not_execution_green"] is True
    assert decision["ad_hoc_group_02_run_is_not_official_result"] is True
    assert decision["subset_green_is_not_full_backend_suite_green"] is True

    assert material["full_backend_suite_green_confirmed"] is False
    assert material["full_backend_suite_green_claim_allowed"] is False
    assert material["hold004_close_allowed"] is False
    assert material["p7_complete"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["split_green_is_full_backend_suite_green"] is False
    assert material["split_green_can_close_p7_hold004"] is False
    assert "P7-HOLD-004" in material["unresolved_hold_refs"]
    assert "active_collect_baseline_refresh_required" in material["required_followup_fixes"]
    assert "official_group_execution_blocked_until_current_baseline_refresh" in material["required_followup_fixes"]
    assert all(value is False for value in material["public_contract"].values())
    assert all(value is False for value in material["body_free_markers"].values())
    assert material["body_free"] is True

    serialized = json.dumps(material, ensure_ascii=False, sort_keys=True)
    assert _SAMPLE_COMMENT_TEXT not in serialized
    assert _SAMPLE_TERMINAL_OUTPUT not in serialized
    assert "tests/test_emlis_ai_p7_hold004" not in serialized
    assert "::test_" not in serialized

    assert_p7_hold004_current_snapshot_baseline_reconcile_contract(material)
    assert_p7_no_body_payload_or_contract_mutation(material, source="r13_current_snapshot_baseline_reconcile_test")

    current_mismatch = build_p7_hold004_current_snapshot_baseline_reconcile()
    current_mismatch["current_baseline"]["test_item_count"] = 2673
    with pytest.raises(ValueError):
        assert_p7_hold004_current_snapshot_baseline_reconcile_contract(current_mismatch)

    affected_group_mismatch = build_p7_hold004_current_snapshot_baseline_reconcile()
    affected_group_mismatch["delta"]["affected_group_ids"].append("group_03_p7_core_matrix_handoff")
    with pytest.raises(ValueError):
        assert_p7_hold004_current_snapshot_baseline_reconcile_contract(affected_group_mismatch)

    official_boundary_mismatch = build_p7_hold004_current_snapshot_baseline_reconcile()
    official_boundary_mismatch["decision"]["official_group_execution_blocked_until_refresh"] = False
    with pytest.raises(ValueError):
        assert_p7_hold004_current_snapshot_baseline_reconcile_contract(official_boundary_mismatch)

    release_mismatch = build_p7_hold004_current_snapshot_baseline_reconcile()
    release_mismatch["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_current_snapshot_baseline_reconcile_contract(release_mismatch)

    contract_mismatch = build_p7_hold004_current_snapshot_baseline_reconcile()
    contract_mismatch["public_contract"]["api_response_key_added"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_current_snapshot_baseline_reconcile_contract(contract_mismatch)


def test_r0_backend_suite_contract_boundary_freeze_is_body_free_and_release_closed() -> None:
    material = build_p7_hold004_backend_suite_contract_boundary_freeze()

    assert material["schema_version"] == P7_HOLD004_BACKEND_CONTRACT_BOUNDARY_FREEZE_SCHEMA_VERSION
    assert material["phase"] == "P7_ProductQualityRunner_LongRunGate"
    assert material["step"] == "P7-HOLD-004_BackendSuiteSplit_MatrixConsistency_R0_R1_20260614"
    assert material["implementation_step"] == "P7-HOLD-004_BackendSuiteSplit_MatrixConsistency_R0_R1_20260614"
    assert material["hold_id"] == "P7-HOLD-004"
    assert material["source_mode"] == "local_snapshot"
    assert material["git_checked"] is False
    assert material["scope_status"] == "R0_CONTRACT_BOUNDARY_FROZEN"
    assert material["implementation_scope"]["r0_contract_boundary_fixed"] is True
    assert material["implementation_scope"]["r1_collect_baseline_material_allowed"] is True
    assert material["implementation_scope"]["runtime_behavior_change_allowed"] is False
    assert material["implementation_scope"]["rn_change_allowed"] is False
    assert material["implementation_scope"]["api_contract_change_allowed"] is False
    assert material["implementation_scope"]["db_change_allowed"] is False
    assert material["implementation_scope"]["release_decision_change_allowed"] is False
    assert material["implementation_scope"]["p8_implementation_allowed"] is False
    assert material["full_backend_suite_green_confirmed"] is False
    assert material["full_backend_suite_green_claim_allowed"] is False
    assert material["hold004_close_allowed"] is False
    assert material["p7_complete"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert all(value is False for value in material["boundary_flags"].values())
    assert all(value is False for value in material["public_contract"].values())
    assert all(value is False for value in material["body_free_markers"].values())
    assert material["body_free"] is True

    assert_p7_hold004_backend_suite_contract_boundary_freeze_contract(material)
    assert_p7_no_body_payload_or_contract_mutation(material, source="r0_backend_suite_contract_boundary_freeze_test")


def test_r0_backend_suite_contract_boundary_freeze_rejects_contract_release_or_p8_mutation() -> None:
    material = build_p7_hold004_backend_suite_contract_boundary_freeze()
    material["boundary_flags"]["api_route_changed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_contract_boundary_freeze_contract(material)

    material = build_p7_hold004_backend_suite_contract_boundary_freeze()
    material["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_contract_boundary_freeze_contract(material)

    material = build_p7_hold004_backend_suite_contract_boundary_freeze()
    material["implementation_scope"]["p8_implementation_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_contract_boundary_freeze_contract(material)


def test_r1_collect_baseline_records_current_collect_only_counts_and_fingerprints_body_free() -> None:
    material = build_p7_hold004_backend_collect_baseline()

    assert material["schema_version"] == P7_HOLD004_BACKEND_COLLECT_BASELINE_SCHEMA_VERSION
    assert material["phase"] == "P7_ProductQualityRunner_LongRunGate"
    assert material["step"] == P7_HOLD004_BACKEND_COLLECT_BASELINE_STEP
    assert material["implementation_step"] == P7_HOLD004_BACKEND_COLLECT_BASELINE_STEP
    assert material["hold_id"] == "P7-HOLD-004"
    assert material["baseline_id"] == P7_HOLD004_BACKEND_COLLECT_BASELINE_ID
    assert P7_HOLD004_BACKEND_COLLECT_BASELINE_ID == "p7_hold004_backend_collect_baseline_20260615_received_148"
    assert material["source_mode"] == "local_snapshot"
    assert material["source_snapshot_ref"] == "mashos-api(148).zip"
    assert material["git_checked"] is False
    assert material["collect_command_id"] == P7_HOLD004_BACKEND_COLLECT_COMMAND_ID
    assert P7_HOLD004_BACKEND_COLLECT_COMMAND_ID == "pytest_collect_only_backend_20260615"
    assert material["collection_status"] == P7_HOLD004_BACKEND_COLLECT_STATUS_COLLECTED
    assert material["collected_test_file_count"] == P7_HOLD004_CURRENT_BACKEND_COLLECTED_TEST_FILE_COUNT == 425
    assert material["collected_test_item_count"] == P7_HOLD004_CURRENT_BACKEND_COLLECTED_TEST_ITEM_COUNT == 2856
    assert material["warnings_count"] == P7_HOLD004_CURRENT_BACKEND_COLLECT_WARNINGS_COUNT == 1
    assert material["test_items_fingerprint_sha256"] == P7_HOLD004_CURRENT_TEST_ITEMS_FINGERPRINT_SHA256
    assert material["test_files_fingerprint_sha256"] == P7_HOLD004_CURRENT_TEST_FILES_FINGERPRINT_SHA256
    assert P7_HOLD004_CURRENT_TEST_ITEMS_FINGERPRINT_SHA256 == (
        "4698ce5240707f71fc3678a0153a15626ba9718fbadad83294e57d11946c2e0d"
    )
    assert P7_HOLD004_CURRENT_TEST_FILES_FINGERPRINT_SHA256 == (
        "6866231daf68427dca2de1b2011feea49450f7b4a8b3c5b9dec0f9ccd5f3e9c6"
    )
    assert material["fingerprint_algorithm"] == P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM
    assert material["pytest_output_retained"] is False
    assert material["first_red_captured"] is False
    assert material["next_red_captured"] is False
    assert material["full_backend_suite_green_confirmed"] is False
    assert material["full_backend_suite_green_claim_allowed"] is False
    assert material["hold004_close_allowed"] is False
    assert material["p7_complete"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert "backend_suite_group_inventory_refresh_required" in material["required_followup_fixes"]
    assert "backend_suite_execution_plan_refresh_required" in material["required_followup_fixes"]
    assert "backend_suite_matrix_reconnect_required" in material["required_followup_fixes"]
    assert "backend_suite_group_execution_not_run" in material["required_followup_fixes"]
    assert "full_backend_suite_green_unconfirmed" in material["required_followup_fixes"]
    assert "active_collect_baseline_refresh_required" not in material["required_followup_fixes"]
    assert all(value is False for value in material["public_contract"].values())
    assert all(value is False for value in material["body_free_markers"].values())
    assert material["body_free"] is True

    serialized = json.dumps(material, ensure_ascii=False, sort_keys=True)
    assert _SAMPLE_COMMENT_TEXT not in serialized
    assert _SAMPLE_TERMINAL_OUTPUT not in serialized
    assert "comment_text" not in material
    assert "candidate_body" not in material
    assert "surface_body" not in material
    assert "terminal_output" not in material
    assert "stdout" not in material
    assert "stderr" not in material
    assert "traceback" not in material

    assert_p7_hold004_backend_collect_baseline_contract(material)
    assert_p7_no_body_payload_or_contract_mutation(material, source="r14_backend_collect_baseline_test")
    _assert_r13_current_snapshot_baseline_reconcile_material()


def test_r1_collect_summary_from_nodeids_keeps_only_counts_and_fingerprints() -> None:
    nodeids = [
        "tests/z_sample.py::test_beta",
        "tests/a_sample.py::test_alpha",
        "tests/z_sample.py::test_alpha",
    ]

    summary = build_p7_hold004_backend_collect_summary_from_nodeids(nodeids)

    assert summary["collected_test_file_count"] == 2
    assert summary["collected_test_item_count"] == 3
    assert summary["test_items_fingerprint_sha256"] == _sha256_joined(sorted(nodeids))
    assert summary["test_files_fingerprint_sha256"] == _sha256_joined(["tests/z_sample.py", "tests/a_sample.py"])
    assert summary["fingerprint_algorithm"] == P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM
    assert summary["body_free"] is True

    serialized = json.dumps(summary, ensure_ascii=False, sort_keys=True)
    assert "test_alpha" not in serialized
    assert "tests/z_sample.py" not in serialized

    received_scope = build_p7_hold004_received_snapshot_scope_freeze()

    assert received_scope["schema_version"] == P7_HOLD004_RECEIVED_SNAPSHOT_SCOPE_FREEZE_SCHEMA_VERSION
    assert received_scope["phase"] == "P7_ProductQualityRunner_LongRunGate"
    assert received_scope["step"] == P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_STEP
    assert received_scope["hold_id"] == "P7-HOLD-004"
    assert received_scope["source_mode"] == "local_snapshot"
    assert received_scope["active_source_snapshot_ref_at_receipt"] == (
        P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT
    )
    assert received_scope["active_source_snapshot_ref_at_receipt"] == "mashos-api(147).zip"
    assert received_scope["received_zip_ref"] == P7_HOLD004_RECEIVED_ZIP_REF == "mashos-api(148).zip"
    assert received_scope["active_source_snapshot_ref_at_receipt"] != received_scope["received_zip_ref"]
    assert received_scope["source_identity_separated"] is True
    assert received_scope["received_zip_promoted_to_source_snapshot_ref"] is False
    assert received_scope["active_baseline_updated"] is False
    assert received_scope["received_collect_summary_builder_added"] is True
    assert received_scope["implementation_scope"]["r21_received_snapshot_constants_added"] is True
    assert received_scope["implementation_scope"]["r22_received_collect_summary_body_free_added"] is True
    assert received_scope["implementation_scope"]["r23_reconcile_material_added"] is True
    assert received_scope["implementation_scope"]["r24_adoption_decision_added"] is True
    assert received_scope["implementation_scope"]["r25_official_group02_readiness_guard_added"] is True
    assert received_scope["implementation_scope"]["r26_matrix_handoff_validation_connected"] is True
    assert received_scope["implementation_scope"]["active_baseline_change_allowed"] is False
    assert received_scope["full_backend_suite_green_confirmed"] is False
    assert received_scope["hold004_close_allowed"] is False
    assert received_scope["p7_complete"] is False
    assert received_scope["p8_start_allowed"] is False
    assert received_scope["release_allowed"] is False
    assert received_scope["active_baseline_update_allowed"] is False
    assert received_scope["official_group_02_capture_run_allowed"] is False
    assert received_scope["official_group_02_capture_result_recording_allowed"] is False
    assert received_scope["can_claim_group_green"] is False
    assert received_scope["can_claim_full_backend_suite_green"] is False
    assert all(value is False for value in received_scope["public_contract"].values())
    assert all(value is False for value in received_scope["body_free_markers"].values())
    assert received_scope["body_free"] is True

    received_scope_serialized = json.dumps(received_scope, ensure_ascii=False, sort_keys=True)
    assert _SAMPLE_COMMENT_TEXT not in received_scope_serialized
    assert _SAMPLE_TERMINAL_OUTPUT not in received_scope_serialized
    assert "::test_" not in received_scope_serialized
    assert "tests/z_sample.py" not in received_scope_serialized

    assert_p7_hold004_received_snapshot_scope_freeze_contract(received_scope)
    assert_p7_no_body_payload_or_contract_mutation(
        received_scope,
        source="r21_received_snapshot_scope_freeze_test",
    )

    received_summary = build_p7_hold004_received_snapshot_collect_summary()

    assert received_summary["schema_version"] == P7_HOLD004_RECEIVED_SNAPSHOT_COLLECT_SUMMARY_SCHEMA_VERSION
    assert received_summary["phase"] == "P7_ProductQualityRunner_LongRunGate"
    assert received_summary["step"] == P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_STEP
    assert received_summary["hold_id"] == "P7-HOLD-004"
    assert received_summary["source_mode"] == "local_snapshot"
    assert received_summary["active_source_snapshot_ref_at_receipt"] == "mashos-api(147).zip"
    assert received_summary["received_zip_ref"] == P7_HOLD004_RECEIVED_ZIP_REF
    assert received_summary["collect_command_id"] == P7_HOLD004_RECEIVED_COLLECT_COMMAND_ID
    assert received_summary["collection_status"] == "COLLECTED"
    assert received_summary["collected_test_file_count"] == P7_HOLD004_RECEIVED_COLLECTED_TEST_FILE_COUNT == 425
    assert received_summary["collected_test_item_count"] == P7_HOLD004_RECEIVED_COLLECTED_TEST_ITEM_COUNT == 2856
    assert received_summary["warnings_count"] == P7_HOLD004_RECEIVED_COLLECT_WARNINGS_COUNT == 1
    assert received_summary["test_items_fingerprint_sha256"] == (
        P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256
    )
    assert received_summary["test_items_fingerprint_sha256"] == (
        "4698ce5240707f71fc3678a0153a15626ba9718fbadad83294e57d11946c2e0d"
    )
    assert received_summary["test_files_fingerprint_sha256"] == (
        P7_HOLD004_RECEIVED_TEST_FILES_FINGERPRINT_SHA256
    )
    assert received_summary["test_files_fingerprint_sha256"] == (
        "6866231daf68427dca2de1b2011feea49450f7b4a8b3c5b9dec0f9ccd5f3e9c6"
    )
    assert received_summary["fingerprint_algorithm"] == P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM
    assert received_summary["received_snapshot_collect_matches_recorded_default"] is True
    assert received_summary["pytest_output_retained"] is False
    assert received_summary["nodeids_retained"] is False
    assert received_summary["terminal_output_retained"] is False
    assert received_summary["stdout_retained"] is False
    assert received_summary["stderr_retained"] is False
    assert received_summary["raw_traceback_included"] is False
    assert received_summary["full_backend_suite_green_confirmed"] is False
    assert received_summary["hold004_close_allowed"] is False
    assert received_summary["p7_complete"] is False
    assert received_summary["p8_start_allowed"] is False
    assert received_summary["release_allowed"] is False
    assert received_summary["active_baseline_update_allowed"] is False
    assert received_summary["official_group_02_capture_run_allowed"] is False
    assert received_summary["official_group_02_capture_result_recording_allowed"] is False
    assert received_summary["can_claim_group_green"] is False
    assert received_summary["can_claim_full_backend_suite_green"] is False
    assert all(value is False for value in received_summary["public_contract"].values())
    assert all(value is False for value in received_summary["body_free_markers"].values())
    assert received_summary["body_free"] is True

    received_summary_serialized = json.dumps(received_summary, ensure_ascii=False, sort_keys=True)
    assert _SAMPLE_COMMENT_TEXT not in received_summary_serialized
    assert _SAMPLE_TERMINAL_OUTPUT not in received_summary_serialized
    assert "::test_" not in received_summary_serialized
    assert "tests/test_emlis_ai_p7_hold004" not in received_summary_serialized
    assert "comment_text" not in received_summary
    assert "candidate_body" not in received_summary
    assert "surface_body" not in received_summary
    assert "terminal_output" not in received_summary
    assert "stdout" not in received_summary
    assert "stderr" not in received_summary
    assert "traceback" not in received_summary

    assert_p7_hold004_received_snapshot_collect_summary_contract(received_summary)
    assert_p7_no_body_payload_or_contract_mutation(
        received_summary,
        source="r22_received_snapshot_collect_summary_test",
    )

    received_reconcile = build_p7_hold004_received_snapshot_baseline_fingerprint_reconcile()

    assert received_reconcile["schema_version"] == (
        P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_SCHEMA_VERSION
    )
    assert received_reconcile["phase"] == "P7_ProductQualityRunner_LongRunGate"
    assert received_reconcile["step"] == P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_STEP
    assert received_reconcile["hold_id"] == "P7-HOLD-004"
    assert received_reconcile["source_mode"] == "local_snapshot"
    assert received_reconcile["active_baseline"]["source_snapshot_ref"] == "mashos-api(147).zip"
    assert received_reconcile["received_snapshot"]["received_zip_ref"] == "mashos-api(148).zip"
    assert received_reconcile["received_snapshot"]["collected_test_file_count"] == 425
    assert received_reconcile["received_snapshot"]["collected_test_item_count"] == 2856
    assert received_reconcile["received_snapshot"]["warnings_count"] == 1
    assert received_reconcile["received_snapshot"]["test_items_fingerprint_sha256"] == (
        P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256
    )
    assert received_reconcile["received_snapshot"]["test_files_fingerprint_sha256"] == (
        P7_HOLD004_RECEIVED_TEST_FILES_FINGERPRINT_SHA256
    )

    comparison = received_reconcile["comparison"]
    assert comparison["counts_match"] is True
    assert comparison["warning_count_match"] is True
    assert comparison["test_files_fingerprint_match"] is True
    assert comparison["test_items_fingerprint_match"] is False
    assert comparison["source_snapshot_ref_matches_received_zip_ref"] is False
    assert comparison["active_baseline_accepts_received_collect_nodeids"] is False

    classification = received_reconcile["classification"]
    assert classification["status"] == P7_HOLD004_RECEIVED_RECONCILE_STATUS_ITEM_FINGERPRINT_MISMATCH_UNCLASSIFIED
    assert classification["root_cause_status"] == P7_HOLD004_RECEIVED_ROOT_CAUSE_STATUS_UNCLASSIFIED
    assert classification["classification_required"] is True
    assert classification["item_fingerprint_mismatch_unclassified"] is True
    assert classification["source_identity_unclear"] is True

    decision = received_reconcile["decision"]
    assert decision["active_baseline_update_allowed"] is False
    assert decision["official_group_02_capture_run_allowed"] is False
    assert decision["official_group_02_capture_result_recording_allowed"] is False
    assert decision["official_group_02_capture_blocked"] is True
    assert decision["can_claim_group_green"] is False
    assert decision["can_claim_full_backend_suite_green"] is False
    assert received_reconcile["received_snapshot_baseline_fingerprint_reconciled"] is False
    assert received_reconcile["received_snapshot_item_fingerprint_mismatch_unresolved"] is True
    assert received_reconcile["official_group_02_capture_blocked"] is True
    assert received_reconcile["full_backend_suite_green_confirmed"] is False
    assert received_reconcile["hold004_close_allowed"] is False
    assert received_reconcile["p7_complete"] is False
    assert received_reconcile["p8_start_allowed"] is False
    assert received_reconcile["release_allowed"] is False
    assert all(value is False for value in received_reconcile["public_contract"].values())
    assert all(value is False for value in received_reconcile["body_free_markers"].values())
    assert received_reconcile["body_free"] is True

    received_reconcile_serialized = json.dumps(received_reconcile, ensure_ascii=False, sort_keys=True)
    assert _SAMPLE_COMMENT_TEXT not in received_reconcile_serialized
    assert _SAMPLE_TERMINAL_OUTPUT not in received_reconcile_serialized
    assert "::test_" not in received_reconcile_serialized
    assert "tests/test_emlis_ai_p7_hold004" not in received_reconcile_serialized

    assert_p7_hold004_received_snapshot_baseline_fingerprint_reconcile_contract(received_reconcile)
    assert_p7_no_body_payload_or_contract_mutation(
        received_reconcile,
        source="r23_received_snapshot_baseline_fingerprint_reconcile_test",
    )

    received_adoption = build_p7_hold004_received_snapshot_baseline_adoption_decision(
        received_snapshot_reconcile=received_reconcile,
    )

    assert received_adoption["schema_version"] == P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_ADOPTION_DECISION_SCHEMA_VERSION
    assert received_adoption["phase"] == "P7_ProductQualityRunner_LongRunGate"
    assert received_adoption["step"] == P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_STEP
    assert received_adoption["hold_id"] == "P7-HOLD-004"
    assert received_adoption["received_zip_ref"] == "mashos-api(148).zip"
    assert received_adoption["active_source_snapshot_ref_at_receipt"] == "mashos-api(147).zip"
    assert received_adoption["candidate_new_baseline_id"] == "p7_hold004_backend_collect_baseline_20260615_received_148"
    assert received_adoption["received_reconcile_status"] == (
        P7_HOLD004_RECEIVED_RECONCILE_STATUS_ITEM_FINGERPRINT_MISMATCH_UNCLASSIFIED
    )
    assert received_adoption["adoption_status"] == (
        P7_HOLD004_RECEIVED_ADOPTION_STATUS_BLOCKED_UNCLASSIFIED_ITEM_FINGERPRINT_MISMATCH
    )
    assert received_adoption["root_cause_status"] == P7_HOLD004_RECEIVED_ROOT_CAUSE_STATUS_UNCLASSIFIED
    assert received_adoption["required_evidence"]["repeat_collect_stability_required"] is True
    assert received_adoption["required_evidence"]["source_snapshot_identity_review_required"] is True
    assert received_adoption["required_evidence"]["test_semantics_review_required"] is True
    assert received_adoption["required_evidence"]["baseline_id_or_revision_update_required"] is True
    assert received_adoption["required_evidence"]["item_fingerprint_root_cause_classification_required"] is True
    assert received_adoption["active_baseline_update_allowed"] is False
    assert received_adoption["source_snapshot_ref_update_allowed"] is False
    assert received_adoption["same_baseline_id_hash_replacement_allowed"] is False
    assert received_adoption["received_zip_promoted_to_source_snapshot_ref"] is False
    assert received_adoption["official_group_02_capture_blocked_until_adopted"] is True
    assert received_adoption["official_group_02_capture_run_allowed"] is False
    assert received_adoption["official_group_02_capture_result_recording_allowed"] is False
    assert received_adoption["full_backend_suite_green_confirmed"] is False
    assert received_adoption["hold004_close_allowed"] is False
    assert received_adoption["p7_complete"] is False
    assert received_adoption["p8_start_allowed"] is False
    assert received_adoption["release_allowed"] is False
    assert all(value is False for value in received_adoption["public_contract"].values())
    assert all(value is False for value in received_adoption["body_free_markers"].values())
    assert received_adoption["body_free"] is True

    received_adoption_serialized = json.dumps(received_adoption, ensure_ascii=False, sort_keys=True)
    assert _SAMPLE_COMMENT_TEXT not in received_adoption_serialized
    assert _SAMPLE_TERMINAL_OUTPUT not in received_adoption_serialized
    assert "::test_" not in received_adoption_serialized
    assert "tests/test_emlis_ai_p7_hold004" not in received_adoption_serialized

    assert_p7_hold004_received_snapshot_baseline_adoption_decision_contract(received_adoption)
    assert_p7_no_body_payload_or_contract_mutation(
        received_adoption,
        source="r24_received_snapshot_baseline_adoption_decision_test",
    )

    conditional_adoption = build_p7_hold004_received_snapshot_conditional_active_baseline_adoption(
        received_snapshot_reconcile=received_reconcile,
        adoption_decision=received_adoption,
    )
    assert conditional_adoption["schema_version"] == (
        P7_HOLD004_RECEIVED_SNAPSHOT_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_SCHEMA_VERSION
    )
    assert conditional_adoption["step"] == P7_HOLD004_RECEIVED_SNAPSHOT_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_STEP
    assert conditional_adoption["hold_id"] == "P7-HOLD-004"
    assert conditional_adoption["received_zip_ref"] == "mashos-api(148).zip"
    assert conditional_adoption["previous_active_baseline"]["baseline_id"] == (
        "p7_hold004_backend_collect_baseline_20260615"
    )
    assert conditional_adoption["candidate_active_baseline"]["baseline_id"] == (
        "p7_hold004_backend_collect_baseline_20260615_received_148"
    )
    assert conditional_adoption["candidate_active_baseline"]["source_snapshot_ref"] == "mashos-api(148).zip"
    assert conditional_adoption["candidate_active_baseline"]["test_items_fingerprint_sha256"] == (
        "4698ce5240707f71fc3678a0153a15626ba9718fbadad83294e57d11946c2e0d"
    )
    assert conditional_adoption["candidate_active_baseline"]["test_files_fingerprint_sha256"] == (
        "6866231daf68427dca2de1b2011feea49450f7b4a8b3c5b9dec0f9ccd5f3e9c6"
    )
    assert conditional_adoption["adoption_status"] == (
        P7_HOLD004_RECEIVED_ADOPTION_STATUS_BLOCKED_UNCLASSIFIED_ITEM_FINGERPRINT_MISMATCH
    )
    assert conditional_adoption["adoption_conditions"]["root_cause_classified"] is False
    assert conditional_adoption["adoption_conditions"]["repeated_collect_stable"] is False
    assert conditional_adoption["active_baseline_adoption_ready"] is False
    assert conditional_adoption["active_baseline_update_allowed"] is False
    assert conditional_adoption["active_baseline_update_applied_to_runtime_builders"] is False
    assert conditional_adoption["source_snapshot_ref_update_allowed"] is False
    assert conditional_adoption["received_zip_promoted_to_source_snapshot_ref"] is False
    assert conditional_adoption["official_group_02_capture_blocked_until_adopted"] is True
    assert conditional_adoption["official_group_02_capture_run_allowed"] is False
    assert conditional_adoption["official_group_02_capture_result_recording_allowed"] is False
    assert conditional_adoption["full_backend_suite_green_confirmed"] is False
    assert conditional_adoption["hold004_close_allowed"] is False
    assert conditional_adoption["p7_complete"] is False
    assert conditional_adoption["p8_start_allowed"] is False
    assert conditional_adoption["release_allowed"] is False
    assert "received_snapshot_item_fingerprint_root_cause_classification_required" in conditional_adoption[
        "required_followup_fixes"
    ]
    assert "active_baseline_refresh_not_applied_to_runtime_builders" in conditional_adoption[
        "required_followup_fixes"
    ]
    assert all(value is False for value in conditional_adoption["public_contract"].values())
    assert all(value is False for value in conditional_adoption["body_free_markers"].values())
    assert conditional_adoption["body_free"] is True
    assert_p7_hold004_received_snapshot_conditional_active_baseline_adoption_contract(conditional_adoption)
    assert_p7_no_body_payload_or_contract_mutation(
        conditional_adoption,
        source="r27_conditional_active_baseline_adoption_test",
    )
    assert conditional_adoption["adoption_conditions"]["adoption_evidence_freeze_satisfied"] is False
    assert conditional_adoption["adoption_evidence_freeze_satisfied"] is False
    assert conditional_adoption["r27_manual_boolean_only_adoption_ready_allowed"] is False
    assert "received_snapshot_adoption_evidence_freeze_required" in conditional_adoption[
        "required_followup_fixes"
    ]

    adoption_evidence_default = build_p7_hold004_received_snapshot_adoption_evidence_freeze(
        received_snapshot_reconcile=received_reconcile,
    )
    assert adoption_evidence_default["schema_version"] == (
        P7_HOLD004_RECEIVED_SNAPSHOT_ADOPTION_EVIDENCE_FREEZE_SCHEMA_VERSION
    )
    assert adoption_evidence_default["step"] == P7_HOLD004_RECEIVED_SNAPSHOT_ADOPTION_EVIDENCE_FREEZE_STEP
    assert adoption_evidence_default["hold_id"] == "P7-HOLD-004"
    assert adoption_evidence_default["received_zip_ref"] == "mashos-api(148).zip"
    assert adoption_evidence_default["evidence_status"] == "BLOCKED_ADOPTION_EVIDENCE_UNVERIFIED"
    assert adoption_evidence_default["can_mark_r27_conditions_satisfied"] is False
    assert adoption_evidence_default["repeat_collect_evidence"]["provided_collect_run_count"] == 0
    assert adoption_evidence_default["repeat_collect_evidence"]["satisfied"] is False
    assert adoption_evidence_default["root_cause_evidence"]["root_cause_status"] == "UNCLASSIFIED"
    assert adoption_evidence_default["root_cause_evidence"]["satisfied"] is False
    assert adoption_evidence_default["source_identity_evidence"]["satisfied"] is False
    assert adoption_evidence_default["test_semantics_evidence"]["test_semantics_review_outcome"] == "NOT_REVIEWED"
    assert adoption_evidence_default["test_semantics_evidence"]["satisfied"] is False
    assert adoption_evidence_default["post_adoption_connection_plan_evidence"][
        "active_baseline_update_applied_to_runtime_builders"
    ] is False
    assert adoption_evidence_default["post_adoption_connection_plan_evidence"][
        "source_snapshot_ref_updated_in_active_builders"
    ] is False
    assert adoption_evidence_default["r27_manual_boolean_only_adoption_ready_allowed"] is False
    assert adoption_evidence_default["active_baseline_update_allowed"] is False
    assert adoption_evidence_default["official_group_02_capture_run_allowed"] is False
    assert adoption_evidence_default["release_allowed"] is False
    assert all(value is False for value in adoption_evidence_default["public_contract"].values())
    assert all(value is False for value in adoption_evidence_default["body_free_markers"].values())
    assert adoption_evidence_default["body_free"] is True
    assert_p7_hold004_received_snapshot_adoption_evidence_freeze_contract(adoption_evidence_default)
    assert_p7_no_body_payload_or_contract_mutation(
        adoption_evidence_default,
        source="pre_r29_received_snapshot_adoption_evidence_freeze_default_test",
    )

    manual_boolean_only_material = build_p7_hold004_received_snapshot_conditional_active_baseline_adoption(
        received_snapshot_reconcile=received_reconcile,
        adoption_decision=received_adoption,
        repeated_collect_stable=True,
        root_cause_status="BASELINE_CONSTANT_STALE",
        source_identity_decision_recorded=True,
        source_identity_accepted=True,
        test_semantics_reviewed=True,
        baseline_id_or_revision_update_planned=True,
    )
    assert manual_boolean_only_material["adoption_status"] == (
        P7_HOLD004_RECEIVED_ADOPTION_STATUS_BLOCKED_ADOPTION_EVIDENCE_NOT_FROZEN
    )
    assert manual_boolean_only_material["adoption_conditions"]["adoption_evidence_freeze_satisfied"] is False
    assert manual_boolean_only_material["active_baseline_adoption_ready"] is False
    assert manual_boolean_only_material["active_baseline_update_allowed"] is False
    assert manual_boolean_only_material["source_snapshot_ref_update_allowed"] is False
    assert manual_boolean_only_material["release_allowed"] is False
    assert_p7_hold004_received_snapshot_conditional_active_baseline_adoption_contract(
        manual_boolean_only_material
    )

    adoption_evidence_ready = build_p7_hold004_received_snapshot_adoption_evidence_freeze(
        received_snapshot_reconcile=received_reconcile,
        repeat_collect_run_count=2,
        repeat_collect_counts_warnings_fingerprints_match=True,
        root_cause_status="BASELINE_CONSTANT_STALE",
        root_cause_review_recorded=True,
        source_identity_decision_recorded=True,
        source_identity_accepted=True,
        test_semantics_reviewed=True,
        test_semantics_review_outcome="NO_TEST_SEMANTIC_CHANGE_DETECTED",
        baseline_id_or_revision_update_planned=True,
        runtime_builder_update_plan_recorded=True,
        matrix_handoff_update_plan_recorded=True,
    )
    assert adoption_evidence_ready["evidence_status"] == "SATISFIED_FOR_R27_CONDITIONAL_ADOPTION"
    assert adoption_evidence_ready["can_mark_r27_conditions_satisfied"] is True
    assert adoption_evidence_ready["repeat_collect_evidence"]["provided_collect_run_count"] == 2
    assert adoption_evidence_ready["repeat_collect_evidence"]["satisfied"] is True
    assert adoption_evidence_ready["root_cause_evidence"]["root_cause_status"] == "BASELINE_CONSTANT_STALE"
    assert adoption_evidence_ready["root_cause_evidence"]["satisfied"] is True
    assert adoption_evidence_ready["source_identity_evidence"]["satisfied"] is True
    assert adoption_evidence_ready["test_semantics_evidence"]["test_semantics_review_outcome"] == (
        "NO_TEST_SEMANTIC_CHANGE_DETECTED"
    )
    assert adoption_evidence_ready["test_semantics_evidence"]["satisfied"] is True
    assert adoption_evidence_ready["baseline_traceability_evidence"]["satisfied"] is True
    assert adoption_evidence_ready["post_adoption_connection_plan_evidence"]["satisfied"] is True
    assert adoption_evidence_ready["r27_condition_inputs"] == {
        "root_cause_status": "BASELINE_CONSTANT_STALE",
        "repeated_collect_stable": True,
        "source_identity_decision_recorded": True,
        "source_identity_accepted": True,
        "test_semantics_reviewed": True,
        "baseline_id_or_revision_update_planned": True,
    }
    assert adoption_evidence_ready["r27_condition_projection"]["adoption_evidence_freeze_satisfied"] is True
    assert adoption_evidence_ready["adoption_status_if_applied_to_r27"] == (
        P7_HOLD004_RECEIVED_ADOPTION_STATUS_ADOPTABLE_AS_RECEIVED_SNAPSHOT_BASELINE_REFRESH
    )
    assert adoption_evidence_ready["active_baseline_update_allowed"] is False
    assert adoption_evidence_ready["release_allowed"] is False
    assert_p7_hold004_received_snapshot_adoption_evidence_freeze_contract(adoption_evidence_ready)

    adoption_ready_material = build_p7_hold004_received_snapshot_conditional_active_baseline_adoption(
        received_snapshot_reconcile=received_reconcile,
        adoption_decision=received_adoption,
        adoption_evidence_freeze=adoption_evidence_ready,
    )
    assert adoption_ready_material["adoption_status"] == (
        P7_HOLD004_RECEIVED_ADOPTION_STATUS_ADOPTABLE_AS_RECEIVED_SNAPSHOT_BASELINE_REFRESH
    )
    assert adoption_ready_material["root_cause_status"] == "BASELINE_CONSTANT_STALE"
    assert adoption_ready_material["adoption_evidence_freeze_satisfied"] is True
    assert adoption_ready_material["adoption_conditions"]["adoption_evidence_freeze_satisfied"] is True
    assert adoption_ready_material["adoption_conditions"]["root_cause_classified"] is True
    assert adoption_ready_material["adoption_conditions"]["repeated_collect_stable"] is True
    assert adoption_ready_material["adoption_conditions"]["source_identity_decision_recorded"] is True
    assert adoption_ready_material["adoption_conditions"]["source_identity_accepted"] is True
    assert adoption_ready_material["adoption_conditions"]["test_semantics_reviewed"] is True
    assert adoption_ready_material["active_baseline_adoption_ready"] is True
    assert adoption_ready_material["active_baseline_update_allowed"] is True
    assert adoption_ready_material["source_snapshot_ref_update_allowed"] is True
    assert adoption_ready_material["same_baseline_id_hash_replacement_allowed"] is False
    assert adoption_ready_material["active_baseline_update_applied_to_runtime_builders"] is False
    assert adoption_ready_material["source_snapshot_ref_updated_in_active_builders"] is False
    assert adoption_ready_material["official_group_02_capture_blocked_until_adopted"] is True
    assert adoption_ready_material["official_group_02_capture_run_allowed"] is False
    assert adoption_ready_material["can_claim_group_green"] is False
    assert adoption_ready_material["can_claim_full_backend_suite_green"] is False
    assert adoption_ready_material["release_allowed"] is False
    assert_p7_hold004_received_snapshot_conditional_active_baseline_adoption_contract(adoption_ready_material)

    r29_default = build_p7_hold004_received_snapshot_r29_verification_procedure()
    assert r29_default["schema_version"] == (
        P7_HOLD004_RECEIVED_SNAPSHOT_R29_VERIFICATION_PROCEDURE_SCHEMA_VERSION
    )
    assert r29_default["step"] == P7_HOLD004_RECEIVED_SNAPSHOT_R29_VERIFICATION_PROCEDURE_STEP
    assert r29_default["hold_id"] == "P7-HOLD-004"
    assert r29_default["scope_status"] == "R29_VERIFICATION_PROCEDURE_FIXED_RELEASE_CLOSED"
    assert r29_default["received_zip_ref"] == "mashos-api(148).zip"
    assert r29_default["active_source_snapshot_ref_at_receipt"] == "mashos-api(147).zip"
    assert r29_default["implementation_scope"]["r29_verification_procedure_fixed"] is True
    assert r29_default["implementation_scope"]["active_baseline_change_allowed"] is False
    assert r29_default["implementation_scope"]["release_decision_change_allowed"] is False

    checkpoint_ids = [entry["checkpoint_id"] for entry in r29_default["verification_sequence"]]
    assert checkpoint_ids == [
        "py_compile_material_contract_modules",
        "p7_hold004_received_snapshot_focused_contract_subset",
        "full_backend_collect_only_fingerprint_check",
        "group_02_collect_only_boundary_check",
        "group_02_full_run_conditional_capture_check",
    ]
    assert r29_default["verification_sequence"][-1]["execution_allowed_by_default"] is False
    assert r29_default["verification_sequence"][-1]["allowed_when_readiness_status"] == (
        "READY_FOR_OFFICIAL_CAPTURE_RUN"
    )
    assert all(entry["body_free"] is True for entry in r29_default["verification_sequence"])
    assert all(entry["pytest_output_retained"] is False for entry in r29_default["verification_sequence"])
    assert all(entry["nodeids_retained"] is False for entry in r29_default["verification_sequence"])
    assert all(entry["stdout_retained"] is False for entry in r29_default["verification_sequence"])
    assert all(entry["stderr_retained"] is False for entry in r29_default["verification_sequence"])
    assert all(entry["raw_traceback_included"] is False for entry in r29_default["verification_sequence"])

    full_collect_expectation = r29_default["expected_full_backend_collect_only"]
    assert full_collect_expectation["collected_test_file_count"] == 425
    assert full_collect_expectation["collected_test_item_count"] == 2856
    assert full_collect_expectation["warnings_count"] == 1
    assert full_collect_expectation["test_items_fingerprint_sha256"] == (
        "4698ce5240707f71fc3678a0153a15626ba9718fbadad83294e57d11946c2e0d"
    )
    assert full_collect_expectation["test_files_fingerprint_sha256"] == (
        "6866231daf68427dca2de1b2011feea49450f7b4a8b3c5b9dec0f9ccd5f3e9c6"
    )
    assert full_collect_expectation["active_baseline_item_fingerprint_match_expected"] is False
    assert full_collect_expectation["active_baseline_file_fingerprint_match_expected"] is True
    assert full_collect_expectation["collect_only_is_not_execution_green"] is True

    group_collect_expectation = r29_default["expected_group02_collect_only"]
    assert group_collect_expectation["group_id"] == "group_02_p7_hold004"
    assert group_collect_expectation["collected_test_file_count"] == 19
    assert group_collect_expectation["collected_test_item_count"] == 252
    assert group_collect_expectation["warnings_count"] == 1
    assert group_collect_expectation["timeout_budget_sec"] == 120
    assert group_collect_expectation["long_run_probe_budget_sec"] == 240
    assert group_collect_expectation["collect_only_is_not_group_green"] is True
    assert group_collect_expectation["official_green_confirmed"] is False

    boundaries = r29_default["green_claim_boundaries"]
    assert boundaries["target_contract_subset_green_is_contract_green_only"] is True
    assert boundaries["target_contract_subset_green_is_full_backend_suite_green"] is False
    assert boundaries["full_collect_only_is_execution_green"] is False
    assert boundaries["group02_collect_only_is_group_green"] is False
    assert boundaries["group02_timeout_is_green"] is False
    assert boundaries["group02_timeout_is_immediate_fail"] is False
    assert boundaries["group02_pass_is_full_backend_suite_green"] is False
    assert boundaries["official_group02_capture_requires_readiness_ready"] is True
    assert boundaries["same_baseline_id_hash_replacement_blocked"] is True

    adoption_inputs = r29_default["adoption_readiness_inputs"]
    assert adoption_inputs["adoption_evidence_freeze_satisfied"] is False
    assert adoption_inputs["conditional_active_baseline_adoption_ready"] is False
    assert adoption_inputs["r29_applies_active_baseline_refresh"] is False
    assert adoption_inputs["r29_closes_hold004"] is False
    assert adoption_inputs["release_allowed_after_r29"] is False
    assert r29_default["active_baseline_update_allowed"] is False
    assert r29_default["official_group_02_capture_run_allowed"] is False
    assert r29_default["official_group_02_capture_result_recording_allowed"] is False
    assert r29_default["can_claim_group_green"] is False
    assert r29_default["can_claim_full_backend_suite_green"] is False
    assert r29_default["full_backend_suite_green_confirmed"] is False
    assert r29_default["hold004_close_allowed"] is False
    assert r29_default["p7_complete"] is False
    assert r29_default["p8_start_allowed"] is False
    assert r29_default["release_allowed"] is False
    assert "r29_verification_procedure_fixed" in r29_default["required_followup_fixes"]
    assert "active_baseline_refresh_not_applied_to_runtime_builders" in r29_default[
        "required_followup_fixes"
    ]
    assert all(value is False for value in r29_default["public_contract"].values())
    assert all(value is False for value in r29_default["body_free_markers"].values())
    assert r29_default["body_free"] is True

    r29_default_serialized = json.dumps(r29_default, ensure_ascii=False, sort_keys=True)
    assert _SAMPLE_COMMENT_TEXT not in r29_default_serialized
    assert _SAMPLE_TERMINAL_OUTPUT not in r29_default_serialized
    assert "::test_" not in r29_default_serialized
    assert_p7_hold004_received_snapshot_r29_verification_procedure_contract(r29_default)
    assert_p7_no_body_payload_or_contract_mutation(
        r29_default,
        source="r29_received_snapshot_verification_procedure_default_test",
    )

    r29_ready_projection = build_p7_hold004_received_snapshot_r29_verification_procedure(
        adoption_evidence_freeze=adoption_evidence_ready,
        conditional_active_baseline_adoption=adoption_ready_material,
    )
    assert r29_ready_projection["adoption_readiness_inputs"]["adoption_evidence_freeze_satisfied"] is True
    assert r29_ready_projection["adoption_readiness_inputs"]["conditional_adoption_status"] == (
        P7_HOLD004_RECEIVED_ADOPTION_STATUS_ADOPTABLE_AS_RECEIVED_SNAPSHOT_BASELINE_REFRESH
    )
    assert r29_ready_projection["adoption_readiness_inputs"][
        "conditional_active_baseline_adoption_ready"
    ] is True
    assert r29_ready_projection["adoption_readiness_inputs"]["conditional_material_update_allowed"] is True
    assert r29_ready_projection["adoption_readiness_inputs"][
        "active_baseline_update_applied_to_runtime_builders"
    ] is False
    assert r29_ready_projection["adoption_readiness_inputs"][
        "source_snapshot_ref_updated_in_active_builders"
    ] is False
    assert r29_ready_projection["adoption_readiness_inputs"]["r29_applies_active_baseline_refresh"] is False
    assert r29_ready_projection["release_allowed"] is False
    assert_p7_hold004_received_snapshot_r29_verification_procedure_contract(r29_ready_projection)

    r29_timeout_claim = build_p7_hold004_received_snapshot_r29_verification_procedure()
    r29_timeout_claim["green_claim_boundaries"]["group02_timeout_is_green"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_received_snapshot_r29_verification_procedure_contract(r29_timeout_claim)

    r29_release_claim = build_p7_hold004_received_snapshot_r29_verification_procedure()
    r29_release_claim["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_received_snapshot_r29_verification_procedure_contract(r29_release_claim)

    r29_output_retention_claim = build_p7_hold004_received_snapshot_r29_verification_procedure()
    r29_output_retention_claim["verification_sequence"][0]["stdout_retained"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_received_snapshot_r29_verification_procedure_contract(r29_output_retention_claim)

    evidence_claim = json.loads(json.dumps(adoption_evidence_default))
    evidence_claim["can_mark_r27_conditions_satisfied"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_received_snapshot_adoption_evidence_freeze_contract(evidence_claim)

    reconcile_claim = build_p7_hold004_received_snapshot_baseline_fingerprint_reconcile()
    reconcile_claim["comparison"]["test_items_fingerprint_match"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_received_snapshot_baseline_fingerprint_reconcile_contract(reconcile_claim)

    reconcile_update = build_p7_hold004_received_snapshot_baseline_fingerprint_reconcile()
    reconcile_update["active_baseline_update_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_received_snapshot_baseline_fingerprint_reconcile_contract(reconcile_update)

    adoption_update = build_p7_hold004_received_snapshot_baseline_adoption_decision()
    adoption_update["source_snapshot_ref_update_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_received_snapshot_baseline_adoption_decision_contract(adoption_update)

    with pytest.raises(ValueError):
        build_p7_hold004_received_snapshot_collect_summary(
            collected_test_nodeids=nodeids,
            warnings_count=0,
        )

    mismatch = build_p7_hold004_received_snapshot_collect_summary()
    mismatch["test_items_fingerprint_sha256"] = P7_HOLD004_CURRENT_TEST_ITEMS_FINGERPRINT_SHA256
    mismatch["received_snapshot_collect_matches_recorded_default"] = False
    with pytest.raises(ValueError):
        assert_p7_hold004_received_snapshot_collect_summary_contract(mismatch)

    retained_nodeids = build_p7_hold004_received_snapshot_collect_summary()
    retained_nodeids["nodeids_retained"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_received_snapshot_collect_summary_contract(retained_nodeids)


def test_r1_collect_baseline_rejects_nodeids_that_do_not_match_frozen_collect_baseline() -> None:
    nodeids = [
        "tests/z_sample.py::test_beta",
        "tests/a_sample.py::test_alpha",
        "tests/z_sample.py::test_alpha",
    ]

    with pytest.raises(ValueError):
        build_p7_hold004_backend_collect_baseline(collected_test_nodeids=nodeids, warnings_count=0)

    with pytest.raises(ValueError):
        build_p7_hold004_backend_collect_baseline(
            baseline_id="p7_hold004_backend_collect_baseline_20260614",
        )

    with pytest.raises(ValueError):
        build_p7_hold004_backend_collect_baseline(
            collect_command_id="pytest_collect_only_backend_20260614",
        )

    with pytest.raises(ValueError):
        build_p7_hold004_backend_collect_baseline(collected_test_file_count=416)

    with pytest.raises(ValueError):
        build_p7_hold004_backend_collect_baseline(collected_test_item_count=2673)


@pytest.mark.parametrize(
    "mutation_key",
    (
        "full_backend_suite_green_confirmed",
        "full_backend_suite_green_claim_allowed",
        "hold004_close_allowed",
        "p7_complete",
        "p7_complete_claim_allowed",
        "p8_start_allowed",
        "release_allowed",
    ),
)
def test_r0_contract_rejects_release_or_completion_promotion(mutation_key: str) -> None:
    material = build_p7_hold004_backend_collect_baseline()
    material[mutation_key] = True

    with pytest.raises(ValueError):
        assert_p7_hold004_backend_collect_baseline_contract(material)


def test_r0_contract_rejects_public_contract_mutation_and_body_payload() -> None:
    material = build_p7_hold004_backend_collect_baseline()
    material["public_contract"]["api_response_key_added"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_backend_collect_baseline_contract(material)

    material = build_p7_hold004_backend_collect_baseline()
    material["comment_text"] = _SAMPLE_COMMENT_TEXT
    with pytest.raises(ValueError):
        assert_p7_hold004_backend_collect_baseline_contract(material)

    material = build_p7_hold004_backend_collect_baseline()
    material["terminal_output"] = _SAMPLE_TERMINAL_OUTPUT
    with pytest.raises(ValueError):
        assert_p7_hold004_backend_collect_baseline_contract(material)


@pytest.mark.parametrize(
    "marker_key",
    (
        "raw_input_included",
        "history_raw_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "reviewer_free_text_included",
        "terminal_output_included",
    ),
)
def test_r0_contract_rejects_any_body_free_marker_becoming_true(marker_key: str) -> None:
    material = build_p7_hold004_backend_collect_baseline()
    material["body_free_markers"][marker_key] = True

    with pytest.raises(ValueError):
        assert_p7_hold004_backend_collect_baseline_contract(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    (
        ("collected_test_file_count", 415),
        ("collected_test_item_count", 2672),
        ("warnings_count", 0),
        ("test_items_fingerprint_sha256", ""),
        ("test_files_fingerprint_sha256", ""),
        ("test_items_fingerprint_sha256", "0" * 64),
        ("test_files_fingerprint_sha256", "0" * 64),
    ),
)
def test_r1_contract_rejects_current_baseline_count_warning_or_fingerprint_mismatch(
    field: str,
    bad_value: object,
) -> None:
    material = build_p7_hold004_backend_collect_baseline()
    material[field] = bad_value

    with pytest.raises(ValueError):
        assert_p7_hold004_backend_collect_baseline_contract(material)
