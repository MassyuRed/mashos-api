# -*- coding: utf-8 -*-
"""R38/R39 contracts for P7-HOLD-004 matrix/validation refresh and group_02 readiness."""

from __future__ import annotations

import copy
import json

import pytest

from emlis_ai_p7_contracts import assert_p7_no_body_payload_or_contract_mutation
from emlis_ai_p7_hold004_active_baseline_runtime_builder_refresh import (
    P7_HOLD004_ACTIVE_BASELINE_REFRESH_ID,
    P7_HOLD004_MATRIX_RELEASE_VALIDATION_CONNECTION_REFRESH_ID,
    P7_HOLD004_MATRIX_RELEASE_VALIDATION_CONNECTION_REFRESH_SCHEMA_VERSION,
    P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_ID,
    P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_ID,
    P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_SCHEMA_VERSION,
    assert_p7_hold004_matrix_release_validation_connection_refresh_contract,
    build_p7_hold004_matrix_release_validation_connection_refresh,
    build_p7_hold004_post_adoption_received_snapshot_reconcile,
    build_p7_hold004_runtime_builder_refresh_status,
)
from emlis_ai_p7_hold004_backend_suite_execution_results import (
    P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION_V2,
    P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY,
    assert_p7_hold004_official_group02_capture_readiness_contract,
    build_p7_hold004_official_group02_capture_readiness,
)
from emlis_ai_p7_hold004_backend_suite_split_consistency import (
    P7_HOLD004_BACKEND_COLLECT_BASELINE_ID,
    P7_HOLD004_PREVIOUS_ACTIVE_COLLECT_BASELINE_ID,
)

_SAMPLE_COMMENT_TEXT = "これはユーザーに見える本文です。"
_SAMPLE_TERMINAL_OUTPUT = "tests/test_emlis_ai_p7_hold004_sample.py::test_sample PASSED"


def test_r39_group02_capture_readiness_after_refresh_is_ready_but_not_green() -> None:
    reconcile = build_p7_hold004_post_adoption_received_snapshot_reconcile()
    runtime_status = build_p7_hold004_runtime_builder_refresh_status(
        post_adoption_received_snapshot_reconcile=reconcile
    )
    readiness = build_p7_hold004_official_group02_capture_readiness(
        received_snapshot_reconcile=reconcile,
        runtime_builder_refresh_status=runtime_status,
    )
    assert_p7_hold004_official_group02_capture_readiness_contract(readiness)

    assert readiness["schema_version"] == P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION_V2
    assert readiness["readiness_status"] == P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY
    assert readiness["received_snapshot_baseline_fingerprint_reconciled"] is True
    assert readiness["received_snapshot_item_fingerprint_mismatch_unresolved"] is False
    assert readiness["source_snapshot_ref_current_for_received_zip"] is True
    assert readiness["active_baseline_accepts_received_nodeids"] is True
    assert readiness["active_baseline_refresh_schema_version"] == P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_SCHEMA_VERSION
    assert readiness["active_baseline_refresh_id"] == P7_HOLD004_ACTIVE_BASELINE_REFRESH_ID
    assert readiness["runtime_builder_refresh_status_id"] == P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_ID
    assert readiness["post_adoption_received_snapshot_reconcile_id"] == P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_ID
    assert readiness["active_baseline_update_applied_to_runtime_builders"] is True
    assert readiness["source_snapshot_ref_updated_in_active_builders"] is True
    assert readiness["official_capture_run_allowed"] is True
    assert readiness["official_capture_result_recording_allowed"] is True
    assert readiness["official_group_02_capture_blocked"] is False
    assert readiness["official_group_02_capture_green_confirmed"] is False
    assert readiness["can_claim_group_green"] is False
    assert readiness["can_claim_full_backend_suite_green"] is False
    assert readiness["full_backend_suite_green_confirmed"] is False
    assert readiness["hold004_close_allowed"] is False
    assert readiness["p7_complete"] is False
    assert readiness["p8_start_allowed"] is False
    assert readiness["release_allowed"] is False
    assert "group_02_official_full_run_not_executed" in readiness["required_followup_fixes"]
    assert "full_backend_suite_green_unconfirmed" in readiness["required_followup_fixes"]

    serialized = json.dumps(readiness, ensure_ascii=False, sort_keys=True)
    assert _SAMPLE_COMMENT_TEXT not in serialized
    assert _SAMPLE_TERMINAL_OUTPUT not in serialized
    assert "::test_" not in serialized
    assert "tests/test_emlis_ai_p7_hold004" not in serialized
    assert all(value is False for value in readiness["public_contract"].values())
    assert all(value is False for value in readiness["body_free_markers"].values())
    assert_p7_no_body_payload_or_contract_mutation(readiness, source="r39_group02_readiness_test")


def test_r38_matrix_release_validation_refresh_projects_post_adoption_reconcile_without_release_claim() -> None:
    material = build_p7_hold004_matrix_release_validation_connection_refresh()
    assert_p7_hold004_matrix_release_validation_connection_refresh_contract(material)

    assert material["schema_version"] == P7_HOLD004_MATRIX_RELEASE_VALIDATION_CONNECTION_REFRESH_SCHEMA_VERSION
    assert material["connection_refresh_id"] == P7_HOLD004_MATRIX_RELEASE_VALIDATION_CONNECTION_REFRESH_ID
    assert material["current_active_baseline_id"] == P7_HOLD004_BACKEND_COLLECT_BASELINE_ID
    assert material["previous_active_baseline_id"] == P7_HOLD004_PREVIOUS_ACTIVE_COLLECT_BASELINE_ID
    assert material["active_baseline_refresh_schema_version"] == P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_SCHEMA_VERSION
    assert material["active_baseline_refresh_id"] == P7_HOLD004_ACTIVE_BASELINE_REFRESH_ID
    assert material["runtime_builder_refresh_status_id"] == P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_ID
    assert material["post_adoption_received_snapshot_reconcile_id"] == P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_ID
    assert material["matrix_release_validation_connection_refresh_satisfied"] is True
    assert material["post_adoption_readiness_re_evaluated"] is True
    assert material["received_snapshot_baseline_fingerprint_reconciled"] is True
    assert material["received_snapshot_item_fingerprint_mismatch_unresolved"] is False
    assert material["official_group_02_capture_run_allowed"] is True
    assert material["official_group_02_capture_result_recording_allowed"] is True
    assert material["official_group_02_capture_blocked"] is False
    assert material["official_group_02_capture_green_confirmed"] is False
    assert material["official_group_02_official_full_run_executed"] is False
    assert material["official_group_02_capture_result_recorded"] is False
    assert material["can_claim_group_green"] is False
    assert material["can_claim_full_backend_suite_green"] is False
    assert material["full_backend_suite_green_confirmed"] is False
    assert material["hold004_close_allowed"] is False
    assert material["p7_complete"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["matrix_consistency_report_status"] == "PASS"

    checks = material["matrix_consistency_report_checks"]
    assert checks["received_snapshot_blocking_status_consistent"] is True
    assert checks["received_snapshot_item_fingerprint_mismatch_resolved"] is True
    assert checks["active_baseline_refresh_projection_consistent"] is True
    assert checks["full_backend_suite_green_false_across_matrices"] is True
    assert checks["release_allowed_false_across_matrices"] is True

    expected_layers = {
        "backend_suite_split_matrix",
        "r10_hold_matrix",
        "release_handoff",
        "validation_matrix",
        "matrix_consistency_report",
    }
    assert {layer["layer_name"] for layer in material["layer_connections"]} == expected_layers
    assert {layer["layer"] for layer in material["connected_material_projections"]} == expected_layers
    for layer in material["layer_connections"]:
        assert layer["active_baseline_refresh_schema_version"] == P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_SCHEMA_VERSION
        assert layer["active_baseline_refresh_id"] == P7_HOLD004_ACTIVE_BASELINE_REFRESH_ID
        assert layer["runtime_builder_refresh_status_id"] == P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_ID
        assert layer["post_adoption_received_snapshot_reconcile_id"] == P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_ID
        assert layer["readiness_status"] == P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY
        assert layer["received_snapshot_baseline_fingerprint_reconciled"] is True
        assert layer["received_snapshot_item_fingerprint_mismatch_unresolved"] is False
        assert layer["official_group_02_capture_blocked"] is False
        assert layer["official_group_02_capture_run_allowed"] is True
        assert layer["official_group_02_capture_result_recording_allowed"] is True
        assert layer["official_group_02_capture_green_confirmed"] is False
        assert layer["can_claim_group_green"] is False
        assert layer["can_claim_full_backend_suite_green"] is False
        assert layer["full_backend_suite_green_confirmed"] is False
        assert layer["hold004_close_allowed"] is False
        assert layer["release_allowed"] is False
        assert layer["p7_complete"] is False
        assert layer["p8_start_allowed"] is False
        assert layer["body_free"] is True

    assert "P7-HOLD-004" in material["unresolved_hold_refs"]
    assert "group_02_official_full_run_not_executed" in material["required_followup_fixes"]
    assert "full_backend_suite_green_unconfirmed" in material["required_followup_fixes"]
    assert all(value is False for value in material["public_contract"].values())
    assert all(value is False for value in material["body_free_markers"].values())
    assert_p7_no_body_payload_or_contract_mutation(material, source="r38_connection_refresh_test")


def test_r38_contract_rejects_ready_as_group_green_full_green_or_release() -> None:
    material = build_p7_hold004_matrix_release_validation_connection_refresh()

    group_green = copy.deepcopy(material)
    group_green["official_group_02_capture_green_confirmed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_matrix_release_validation_connection_refresh_contract(group_green)

    full_green = copy.deepcopy(material)
    full_green["full_backend_suite_green_confirmed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_matrix_release_validation_connection_refresh_contract(full_green)

    release_claim = copy.deepcopy(material)
    release_claim["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_matrix_release_validation_connection_refresh_contract(release_claim)

    layer_claim = copy.deepcopy(material)
    layer_claim["layer_connections"][0]["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_matrix_release_validation_connection_refresh_contract(layer_claim)


def test_r39_readiness_contract_rejects_green_claims_and_missing_runtime_refresh() -> None:
    reconcile = build_p7_hold004_post_adoption_received_snapshot_reconcile()
    runtime_status = build_p7_hold004_runtime_builder_refresh_status(
        post_adoption_received_snapshot_reconcile=reconcile
    )
    readiness = build_p7_hold004_official_group02_capture_readiness(
        received_snapshot_reconcile=reconcile,
        runtime_builder_refresh_status=runtime_status,
    )

    green_claim = copy.deepcopy(readiness)
    green_claim["can_claim_group_green"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_official_group02_capture_readiness_contract(green_claim)

    release_claim = copy.deepcopy(readiness)
    release_claim["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_official_group02_capture_readiness_contract(release_claim)

    missing_runtime = copy.deepcopy(readiness)
    missing_runtime["active_baseline_update_applied_to_runtime_builders"] = False
    with pytest.raises(ValueError):
        assert_p7_hold004_official_group02_capture_readiness_contract(missing_runtime)
