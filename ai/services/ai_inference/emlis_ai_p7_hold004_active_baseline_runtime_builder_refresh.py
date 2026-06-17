# -*- coding: utf-8 -*-
"""P7-HOLD-004 post-adoption active-baseline and runtime-builder refresh materials.

R36-R40 scope only:
- materialize the post-adoption active baseline without rewriting historical
  R21/R29 at-receipt materials;
- materialize a post-adoption received-snapshot reconcile whose active baseline
  accepts the received snapshot fingerprints;
- verify that the P7-HOLD-004 measurement-runtime material builders now read
  the post-adoption active collect baseline;
- refresh matrix / release handoff / validation connection layers and re-evaluate
  official group_02 capture readiness;
- record official group_02 results without promoting them to full backend-suite green;
- keep full backend-suite green, HOLD closure, P7 completion,
  P8 start, release, RN/API/DB contracts, and Emlis text runtime outside this step.

Only identifiers, counts, booleans, enum-like statuses, and SHA-256 hashes are
stored. Raw input, comment_text bodies, candidate/surface bodies, pytest nodeid
lists, terminal output, stdout/stderr, and traceback bodies must not be stored.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final

from emlis_ai_p7_contracts import (
    P7_GIT_CHECKED,
    P7_PHASE,
    P7_SOURCE_MODE,
    assert_false_markers,
    assert_p7_no_body_payload_or_contract_mutation,
    body_free_flags,
    clean_identifier,
    dedupe_identifiers,
    public_contract_flags,
    safe_mapping,
)
from emlis_ai_p7_hold004_active_baseline_adoption_evidence import (
    P7_HOLD004_ACTIVE_BASELINE_ADOPTION_EVIDENCE_BUNDLE_ID,
    P7_HOLD004_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_GATE_ID,
    assert_p7_hold004_conditional_active_baseline_adoption_gate_contract,
    build_p7_hold004_conditional_active_baseline_adoption_gate,
)
from emlis_ai_p7_hold004_backend_suite_execution_results import (
    P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_ID,
    P7_HOLD004_BACKEND_SUITE_RUN_KIND_CAPTURE,
    P7_HOLD004_BACKEND_SUITE_STATUS_COLLECTION_FAILED,
    P7_HOLD004_BACKEND_SUITE_STATUS_FAIL,
    P7_HOLD004_BACKEND_SUITE_STATUS_INTERRUPTED,
    P7_HOLD004_BACKEND_SUITE_STATUS_PASS,
    P7_HOLD004_BACKEND_SUITE_STATUS_TIMEOUT,
    P7_HOLD004_GROUP02_OFFICIAL_BATCH_ID,
    P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID,
    P7_HOLD004_GROUP02_OFFICIAL_TEST_ITEM_COUNT,
    P7_HOLD004_GROUP02_OFFICIAL_WARNINGS_COUNT,
    P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_GREEN,
    P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_COLLECTION_FAILED,
    P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_INTERRUPTED,
    P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_RED,
    P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_TIMEOUT,
    P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_ADOPTION_DECISION_SCHEMA_VERSION,
    P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_AFTER_REFRESH_ID as P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_REEVALUATION_ID,
    P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_AFTER_REFRESH_STEP as P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_REEVALUATION_STEP,
    P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION_V2,
    P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY,
    assert_p7_hold004_backend_suite_execution_summary_contract,
    assert_p7_hold004_backend_suite_group_run_result_contract,
    assert_p7_hold004_official_group02_capture_adoption_decision_contract,
    assert_p7_hold004_official_group02_capture_readiness_contract,
    build_p7_hold004_backend_suite_execution_summary,
    build_p7_hold004_backend_suite_group_run_result,
    build_p7_hold004_official_group02_capture_adoption_decision,
    build_p7_hold004_official_group02_capture_readiness,
)
from emlis_ai_p7_hold004_backend_suite_group_inventory_plan import (
    P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID,
    P7_HOLD004_BACKEND_SUITE_GROUP_IDS,
    P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID,
    assert_p7_hold004_backend_suite_execution_plan_contract,
    assert_p7_hold004_backend_suite_group_inventory_contract,
    build_p7_hold004_backend_suite_execution_plan,
    build_p7_hold004_backend_suite_group_inventory,
)
from emlis_ai_p7_hold004_backend_suite_split_consistency import (
    P7_HOLD004_BACKEND_ACTIVE_BASELINE_REFRESH_APPLIED,
    P7_HOLD004_BACKEND_COLLECT_BASELINE_ID,
    P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM,
    P7_HOLD004_BACKEND_COLLECT_WARNINGS_COUNT,
    P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT,
    P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT,
    P7_HOLD004_BACKEND_SOURCE_SNAPSHOT_REF,
    P7_HOLD004_BACKEND_SUITE_HOLD_ID,
    P7_HOLD004_BACKEND_TEST_FILES_FINGERPRINT_SHA256,
    P7_HOLD004_BACKEND_TEST_ITEMS_FINGERPRINT_SHA256,
    P7_HOLD004_PREVIOUS_ACTIVE_COLLECT_BASELINE_ID,
    P7_HOLD004_PREVIOUS_ACTIVE_SOURCE_SNAPSHOT_REF,
    P7_HOLD004_PREVIOUS_ACTIVE_TEST_FILES_SHA256,
    P7_HOLD004_PREVIOUS_ACTIVE_TEST_ITEMS_SHA256,
    assert_p7_hold004_backend_collect_baseline_contract,
    build_p7_hold004_current_backend_collect_baseline,
)
from emlis_ai_p7_hold004_group_execution_minimal_order import (
    P7_HOLD004_GROUP_EXECUTION_MINIMAL_ORDER_ID,
    assert_p7_hold004_group_execution_minimal_order_contract,
    build_p7_hold004_group_execution_minimal_order,
)
from emlis_ai_p7_hold_matrix import (
    assert_p7_backend_suite_split_matrix_contract,
    assert_p7_r10_hold_matrix_contract,
    build_p7_backend_suite_split_matrix,
    build_p7_r10_hold_matrix,
)
from emlis_ai_p7_hold004_matrix_consistency_report import (
    P7_HOLD004_MATRIX_CONSISTENCY_REPORT_ID,
    assert_p7_hold004_matrix_consistency_report_contract,
    build_p7_hold004_matrix_consistency_report,
)
from emlis_ai_p7_red_closure_classification import (
    assert_p7_red_closure_classification_matrix_contract,
    build_p7_red_closure_classification_matrix,
)
from emlis_ai_p7_release_handoff import (
    assert_p7_release_decision_handoff_contract,
    build_p7_release_decision_handoff,
)
from emlis_ai_p7_timeout_isolation import (
    assert_p7_e2e_isolation_result_contract,
    build_p7_connection_e2e_r13_passed_observation_result,
)
from emlis_ai_p7_validation_matrix import (
    assert_p7_validation_regression_matrix_contract,
    build_p7_validation_regression_matrix,
)
from emlis_ai_p7_hold004_received_snapshot_baseline_fingerprint_reconcile import (
    P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT,
    P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT,
    P7_HOLD004_ACTIVE_TEST_FILES_FINGERPRINT_SHA256_AT_RECEIPT,
    P7_HOLD004_ACTIVE_TEST_ITEMS_FINGERPRINT_SHA256_AT_RECEIPT,
    P7_HOLD004_RECEIVED_COLLECT_WARNINGS_COUNT,
    P7_HOLD004_RECEIVED_COLLECTED_TEST_FILE_COUNT,
    P7_HOLD004_RECEIVED_COLLECTED_TEST_ITEM_COUNT,
    P7_HOLD004_RECEIVED_RECONCILE_STATUS_MATCHES_ACTIVE_BASELINE,
    P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_ID,
    P7_HOLD004_RECEIVED_SNAPSHOT_CANDIDATE_NEW_BASELINE_ID,
    P7_HOLD004_RECEIVED_TEST_FILES_FINGERPRINT_SHA256,
    P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256,
    P7_HOLD004_RECEIVED_ZIP_REF,
)

P7_HOLD004_POST_ADOPTION_ACTIVE_BASELINE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.post_adoption_active_baseline.v1"
)
P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.post_adoption_received_snapshot_reconcile.v1"
)
P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.runtime_builder_refresh_status.v1"
)
P7_HOLD004_POST_ADOPTION_ACTIVE_BASELINE_STEP: Final = (
    "P7-HOLD-004_ActiveBaselineRuntimeBuilderRefresh_R36_PostAdoptionActiveBaselineMaterial_20260616"
)
P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_STEP: Final = (
    "P7-HOLD-004_ActiveBaselineRuntimeBuilderRefresh_R36_PostAdoptionReceivedSnapshotReconcile_20260616"
)
P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_STEP: Final = (
    "P7-HOLD-004_ActiveBaselineRuntimeBuilderRefresh_R37_RuntimeBuilderRefresh_20260616"
)
P7_HOLD004_ACTIVE_BASELINE_REFRESH_ID: Final = "p7_hold004_active_baseline_refresh_20260616"
P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_ID: Final = (
    "p7_hold004_post_adoption_received_snapshot_reconcile_20260616"
)
P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_ID: Final = "p7_hold004_runtime_builder_refresh_status_20260616"
P7_HOLD004_RUNTIME_REFRESH_STATUS_APPLIED: Final = "APPLIED_TO_CORE_RUNTIME_BUILDERS"
P7_HOLD004_MATRIX_RELEASE_VALIDATION_CONNECTION_REFRESH_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.matrix_release_validation_connection_refresh.v1"
)
P7_HOLD004_MATRIX_RELEASE_VALIDATION_CONNECTION_REFRESH_STEP: Final = (
    "P7-HOLD-004_ActiveBaselineRuntimeBuilderRefresh_R38_MatrixReleaseValidationConnectionRefresh_20260616"
)
P7_HOLD004_MATRIX_RELEASE_VALIDATION_CONNECTION_REFRESH_ID: Final = (
    "p7_hold004_matrix_release_validation_connection_refresh_20260616"
)
P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_REEVALUATION_STEP: Final = (
    "P7-HOLD-004_ActiveBaselineRuntimeBuilderRefresh_R39_OfficialGroup02CaptureReadinessReevaluation_20260616"
)
P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_REEVALUATION_ID: Final = (
    "p7_hold004_official_group02_capture_readiness_20260616"
)
P7_HOLD004_OFFICIAL_GROUP02_RESULT_RECORDING_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.official_group02_result_recording.v1"
)
P7_HOLD004_FULL_BACKEND_SUITE_GATE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.full_backend_suite_gate.v1"
)
P7_HOLD004_OFFICIAL_GROUP02_RESULT_RECORDING_STEP: Final = (
    "P7-HOLD-004_ActiveBaselineRuntimeBuilderRefresh_R40_OfficialGroup02ResultRecording_20260616"
)
P7_HOLD004_FULL_BACKEND_SUITE_GATE_STEP: Final = (
    "P7-HOLD-004_ActiveBaselineRuntimeBuilderRefresh_R40_FullBackendSuiteGate_20260616"
)
P7_HOLD004_OFFICIAL_GROUP02_RESULT_RECORDING_ID: Final = (
    "p7_hold004_official_group02_result_recording_20260616"
)
P7_HOLD004_FULL_BACKEND_SUITE_GATE_ID: Final = "p7_hold004_full_backend_suite_gate_20260616"
P7_HOLD004_GROUP02_RESULT_STATUS_NOT_RUN: Final = "NOT_RUN"
P7_HOLD004_GROUP02_RESULT_STATUS_PASSED_ISOLATED: Final = "PASSED_ISOLATED"
P7_HOLD004_GROUP02_RESULT_STATUS_FAILED_ISOLATED: Final = "FAILED_ISOLATED"
P7_HOLD004_GROUP02_RESULT_STATUS_TIMEOUT_ISOLATED: Final = "TIMEOUT_ISOLATED"
P7_HOLD004_GROUP02_RESULT_STATUS_PARTIAL_OR_INTERRUPTED: Final = "PARTIAL_OR_INTERRUPTED"
P7_HOLD004_GROUP02_ALLOWED_RESULT_RECORDING_STATUSES: Final[frozenset[str]] = frozenset(
    {
        P7_HOLD004_GROUP02_RESULT_STATUS_NOT_RUN,
        P7_HOLD004_GROUP02_RESULT_STATUS_PASSED_ISOLATED,
        P7_HOLD004_GROUP02_RESULT_STATUS_FAILED_ISOLATED,
        P7_HOLD004_GROUP02_RESULT_STATUS_TIMEOUT_ISOLATED,
        P7_HOLD004_GROUP02_RESULT_STATUS_PARTIAL_OR_INTERRUPTED,
    }
)
P7_HOLD004_FULL_BACKEND_SUITE_GATE_STATUS_BLOCKED_REMAINING_GROUPS: Final = (
    "BLOCKED_FULL_BACKEND_SUITE_REMAINING_GROUPS_NOT_OFFICIAL_GREEN"
)

_RELEASE_CLOSED_KEYS: Final[tuple[str, ...]] = (
    "full_backend_suite_green_confirmed",
    "full_backend_suite_green_claim_allowed",
    "hold004_close_allowed",
    "p7_complete",
    "p7_complete_claim_allowed",
    "p8_start_allowed",
    "release_allowed",
    "split_green_is_full_backend_suite_green",
    "split_green_can_close_p7_hold004",
)
_CAPTURE_CLOSED_KEYS: Final[tuple[str, ...]] = (
    "official_group_02_capture_run_allowed",
    "official_group_02_capture_result_recording_allowed",
    "official_group_02_capture_green_confirmed",
    "can_claim_group_green",
    "can_claim_full_backend_suite_green",
)
_BODY_RETENTION_KEYS: Final[tuple[str, ...]] = (
    "nodeids_retained",
    "pytest_output_retained",
    "terminal_output_retained",
    "stdout_retained",
    "stderr_retained",
    "raw_traceback_included",
)
_BOUNDARY_FLAG_KEYS: Final[tuple[str, ...]] = (
    "rn_visible_contract_changed",
    "api_route_changed",
    "request_key_changed",
    "api_response_key_added",
    "public_response_key_added",
    "response_shape_changed",
    "db_schema_changed",
    "db_physical_name_changed",
    "public_release_applied",
    "display_gate_relaxed",
    "reader_gate_relaxed",
    "grounding_gate_relaxed",
    "template_gate_relaxed",
    "runtime_surface_gate_relaxed",
    "visible_surface_gate_relaxed",
    "gate_relaxed",
    "fixed_sentence_template_added",
    "runtime_fixture_branch_added",
)
_R36_IMPLEMENTATION_SCOPE_FLAGS: Final[dict[str, bool]] = {
    "r36_post_adoption_active_baseline_material_added": True,
    "r36_post_adoption_received_snapshot_reconcile_added": True,
    "r37_runtime_builder_refresh_added": False,
    "active_baseline_change_applied_to_material": True,
    "runtime_builder_refresh_applied": False,
    "runtime_behavior_change_allowed": False,
    "rn_change_allowed": False,
    "api_contract_change_allowed": False,
    "db_change_allowed": False,
    "release_decision_change_allowed": False,
    "p8_implementation_allowed": False,
}
_R37_IMPLEMENTATION_SCOPE_FLAGS: Final[dict[str, bool]] = {
    **_R36_IMPLEMENTATION_SCOPE_FLAGS,
    "r37_runtime_builder_refresh_added": True,
    "runtime_builder_refresh_applied": True,
}
_R36_REQUIRED_FOLLOWUP_FIXES: Final[tuple[str, ...]] = (
    "runtime_builder_refresh_required_after_r36",
    "official_group_02_capture_blocked_until_runtime_builder_refresh",
    "full_backend_suite_green_unconfirmed",
)
_R37_REQUIRED_FOLLOWUP_FIXES: Final[tuple[str, ...]] = (
    "matrix_release_validation_connection_refresh_required_after_r37",
    "post_adoption_reconcile_projection_required_for_hold_matrix_release_validation_after_r37",
    "official_group_02_capture_readiness_re_evaluation_required_after_r37",
    "group_02_official_full_run_not_executed",
    "full_backend_suite_green_unconfirmed",
)
_R38_R39_REQUIRED_FOLLOWUP_FIXES: Final[tuple[str, ...]] = (
    "group_02_official_full_run_not_executed",
    "official_group_02_capture_result_recording_required_after_r39",
    "full_backend_suite_green_unconfirmed",
    "p7_hold004_closure_blocked_until_all_backend_groups_green",
    "p5_human_qa_review_required",
    "real_device_submit_modal_readfeel_unverified",
)
_RUNTIME_BUILDER_REFS: Final[tuple[str, ...]] = (
    "backend_suite_split_consistency",
    "backend_suite_group_inventory_plan",
    "backend_suite_execution_plan",
    "backend_suite_execution_results",
    "matrix_consistency_report",
    "group_execution_minimal_order",
)


def _false_boundary_flags() -> dict[str, bool]:
    return {key: False for key in _BOUNDARY_FLAG_KEYS}


def _public_contract_boundary_flags() -> dict[str, bool]:
    flags = public_contract_flags()
    flags.update(_false_boundary_flags())
    return flags


def _body_free_markers() -> dict[str, bool]:
    flags = body_free_flags(include_history=True, include_reviewer=True, include_terminal=True)
    flags.update(
        {
            "stdout_included": False,
            "stderr_included": False,
            "traceback_body_included": False,
            "pytest_nodeids_included": False,
            "pytest_output_included": False,
        }
    )
    return flags


def _release_closed_boundary() -> dict[str, bool]:
    return {key: False for key in _RELEASE_CLOSED_KEYS}


def _capture_closed_boundary() -> dict[str, bool]:
    return {key: False for key in _CAPTURE_CLOSED_KEYS}


def _body_retention_flags() -> dict[str, bool]:
    return {key: False for key in _BODY_RETENTION_KEYS}


def _previous_active_baseline() -> dict[str, Any]:
    return {
        "baseline_id": P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT,
        "source_snapshot_ref": P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT,
        "collected_test_file_count": P7_HOLD004_RECEIVED_COLLECTED_TEST_FILE_COUNT,
        "collected_test_item_count": P7_HOLD004_RECEIVED_COLLECTED_TEST_ITEM_COUNT,
        "warnings_count": P7_HOLD004_RECEIVED_COLLECT_WARNINGS_COUNT,
        "test_items_fingerprint_sha256": P7_HOLD004_ACTIVE_TEST_ITEMS_FINGERPRINT_SHA256_AT_RECEIPT,
        "test_files_fingerprint_sha256": P7_HOLD004_ACTIVE_TEST_FILES_FINGERPRINT_SHA256_AT_RECEIPT,
        "fingerprint_algorithm": P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM,
    }


def _current_active_baseline() -> dict[str, Any]:
    return {
        "baseline_id": P7_HOLD004_BACKEND_COLLECT_BASELINE_ID,
        "source_snapshot_ref": P7_HOLD004_BACKEND_SOURCE_SNAPSHOT_REF,
        "collected_test_file_count": P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT,
        "collected_test_item_count": P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT,
        "warnings_count": P7_HOLD004_BACKEND_COLLECT_WARNINGS_COUNT,
        "test_items_fingerprint_sha256": P7_HOLD004_BACKEND_TEST_ITEMS_FINGERPRINT_SHA256,
        "test_files_fingerprint_sha256": P7_HOLD004_BACKEND_TEST_FILES_FINGERPRINT_SHA256,
        "fingerprint_algorithm": P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM,
    }


def _received_snapshot() -> dict[str, Any]:
    return {
        "received_zip_ref": P7_HOLD004_RECEIVED_ZIP_REF,
        "collected_test_file_count": P7_HOLD004_RECEIVED_COLLECTED_TEST_FILE_COUNT,
        "collected_test_item_count": P7_HOLD004_RECEIVED_COLLECTED_TEST_ITEM_COUNT,
        "warnings_count": P7_HOLD004_RECEIVED_COLLECT_WARNINGS_COUNT,
        "test_items_fingerprint_sha256": P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256,
        "test_files_fingerprint_sha256": P7_HOLD004_RECEIVED_TEST_FILES_FINGERPRINT_SHA256,
        "fingerprint_algorithm": P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM,
    }


def _assert_common_body_free_closed(material: Mapping[str, Any], *, source: str) -> None:
    data = safe_mapping(material)
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError(f"{source} scope mismatch")
    if data.get("source_mode") != P7_SOURCE_MODE or data.get("git_checked") is not False:
        raise ValueError(f"{source} source mode mismatch")
    for key in _RELEASE_CLOSED_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=false")
    for key in _CAPTURE_CLOSED_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=false")
    for key in _BODY_RETENTION_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=false")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must be body_free")
    assert_false_markers(safe_mapping(data.get("public_contract")), source=f"{source}.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source=f"{source}.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)


def _implementation_scope_contract(scope: Mapping[str, Any], *, expected: Mapping[str, bool], source: str) -> None:
    data = safe_mapping(scope)
    for key, expected_value in expected.items():
        if data.get(key) is not expected_value:
            raise ValueError(f"{source}.implementation_scope.{key} mismatch")
    if set(data) != set(expected):
        raise ValueError(f"{source}.implementation_scope keys mismatch")


def _baseline_matches_current_active(baseline: Mapping[str, Any]) -> bool:
    data = safe_mapping(baseline)
    current = _current_active_baseline()
    return all(data.get(key) == current.get(key) for key in current)


def build_p7_hold004_post_adoption_active_baseline_material(
    *,
    conditional_gate: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build R36 post-adoption active-baseline material.

    This creates the new active material only after the R35 gate allows the
    update. Historical at-receipt R21/R29 materials remain explicitly previous.
    Runtime builder application is still a separate R37 step.
    """

    gate = safe_mapping(conditional_gate) if conditional_gate is not None else build_p7_hold004_conditional_active_baseline_adoption_gate()
    assert_p7_hold004_conditional_active_baseline_adoption_gate_contract(gate)
    previous = _previous_active_baseline()
    current = _current_active_baseline()
    gate_previous = safe_mapping(gate.get("previous_active_baseline"))
    gate_candidate = safe_mapping(gate.get("candidate_active_baseline"))
    gate_ready = gate.get("active_baseline_adoption_ready") is True and gate.get("active_baseline_update_allowed") is True
    current_matches_gate_candidate = all(gate_candidate.get(key) == current.get(key) for key in current)
    previous_matches_gate_previous = all(gate_previous.get(key) == previous.get(key) for key in previous)
    material = {
        "schema_version": P7_HOLD004_POST_ADOPTION_ACTIVE_BASELINE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_POST_ADOPTION_ACTIVE_BASELINE_STEP,
        "implementation_step": P7_HOLD004_POST_ADOPTION_ACTIVE_BASELINE_STEP,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "active_baseline_refresh_id": P7_HOLD004_ACTIVE_BASELINE_REFRESH_ID,
        "source_mode": P7_SOURCE_MODE,
        "git_checked": P7_GIT_CHECKED,
        "adoption_evidence_bundle_id": P7_HOLD004_ACTIVE_BASELINE_ADOPTION_EVIDENCE_BUNDLE_ID,
        "conditional_active_baseline_adoption_gate_id": clean_identifier(
            gate.get("gate_id"), default=P7_HOLD004_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_GATE_ID, max_length=180
        ),
        "previous_active_baseline": previous,
        "current_active_baseline": current,
        "previous_active_baseline_id": previous["baseline_id"],
        "current_active_baseline_id": current["baseline_id"],
        "previous_active_source_snapshot_ref": previous["source_snapshot_ref"],
        "current_active_source_snapshot_ref": current["source_snapshot_ref"],
        "previous_active_baseline_retained": True,
        "historical_r21_r29_material_rewritten": False,
        "historical_at_receipt_constants_preserved": previous_matches_gate_previous,
        "same_baseline_id_hash_replacement_allowed": False,
        "same_baseline_id_hash_replacement_applied": False,
        "candidate_baseline_id_changes": current["baseline_id"] != previous["baseline_id"],
        "candidate_baseline_matches_r35_gate": current_matches_gate_candidate,
        "active_baseline_refresh_applied": gate_ready and current_matches_gate_candidate and previous_matches_gate_previous,
        "post_adoption_active_baseline_material_built": True,
        "active_baseline_update_allowed": gate.get("active_baseline_update_allowed") is True,
        "source_snapshot_ref_update_allowed": gate.get("source_snapshot_ref_update_allowed") is True,
        "active_baseline_update_applied_to_runtime_builders": False,
        "source_snapshot_ref_updated_in_active_builders": False,
        "runtime_builder_refresh_not_applied_in_r36": True,
        "received_zip_promoted_to_source_snapshot_ref": False,
        "received_zip_adopted_as_current_active_source_snapshot_ref_after_evidence": True,
        "collect_only_is_not_execution_green": True,
        "execution_green_confirmed": False,
        **_capture_closed_boundary(),
        **_release_closed_boundary(),
        **_body_retention_flags(),
        "implementation_scope": dict(_R36_IMPLEMENTATION_SCOPE_FLAGS),
        "unresolved_hold_refs": [P7_HOLD004_BACKEND_SUITE_HOLD_ID],
        "required_followup_fixes": list(_R36_REQUIRED_FOLLOWUP_FIXES),
        "public_contract": _public_contract_boundary_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_hold004_post_adoption_active_baseline_material_contract(material)
    return material


def assert_p7_hold004_post_adoption_active_baseline_material_contract(material: Mapping[str, Any]) -> bool:
    """Validate R36 post-adoption active-baseline material."""

    data = safe_mapping(material)
    source = "p7_hold004_post_adoption_active_baseline_material"
    if data.get("schema_version") != P7_HOLD004_POST_ADOPTION_ACTIVE_BASELINE_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 R36 active baseline schema_version mismatch")
    if data.get("implementation_step") != P7_HOLD004_POST_ADOPTION_ACTIVE_BASELINE_STEP:
        raise ValueError("P7-HOLD-004 R36 active baseline step mismatch")
    if data.get("active_baseline_refresh_id") != P7_HOLD004_ACTIVE_BASELINE_REFRESH_ID:
        raise ValueError("P7-HOLD-004 R36 refresh id mismatch")
    _assert_common_body_free_closed(data, source=source)
    _implementation_scope_contract(safe_mapping(data.get("implementation_scope")), expected=_R36_IMPLEMENTATION_SCOPE_FLAGS, source=source)
    previous = safe_mapping(data.get("previous_active_baseline"))
    current = safe_mapping(data.get("current_active_baseline"))
    if previous != _previous_active_baseline():
        raise ValueError("P7-HOLD-004 R36 previous active baseline mismatch")
    if current != _current_active_baseline():
        raise ValueError("P7-HOLD-004 R36 current active baseline mismatch")
    if previous.get("baseline_id") != P7_HOLD004_PREVIOUS_ACTIVE_COLLECT_BASELINE_ID:
        raise ValueError("P7-HOLD-004 R36 previous active baseline id must be retained")
    if previous.get("source_snapshot_ref") != P7_HOLD004_PREVIOUS_ACTIVE_SOURCE_SNAPSHOT_REF:
        raise ValueError("P7-HOLD-004 R36 previous source ref must be retained")
    if previous.get("test_items_fingerprint_sha256") != P7_HOLD004_PREVIOUS_ACTIVE_TEST_ITEMS_SHA256:
        raise ValueError("P7-HOLD-004 R36 previous item fingerprint mismatch")
    if previous.get("test_files_fingerprint_sha256") != P7_HOLD004_PREVIOUS_ACTIVE_TEST_FILES_SHA256:
        raise ValueError("P7-HOLD-004 R36 previous file fingerprint mismatch")
    if current.get("baseline_id") != P7_HOLD004_RECEIVED_SNAPSHOT_CANDIDATE_NEW_BASELINE_ID:
        raise ValueError("P7-HOLD-004 R36 current active baseline id mismatch")
    if current.get("source_snapshot_ref") != P7_HOLD004_RECEIVED_ZIP_REF:
        raise ValueError("P7-HOLD-004 R36 current active source ref mismatch")
    if current.get("test_items_fingerprint_sha256") != P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256:
        raise ValueError("P7-HOLD-004 R36 current active item fingerprint mismatch")
    if current.get("test_files_fingerprint_sha256") != P7_HOLD004_RECEIVED_TEST_FILES_FINGERPRINT_SHA256:
        raise ValueError("P7-HOLD-004 R36 current active file fingerprint mismatch")
    for key in (
        "previous_active_baseline_retained",
        "candidate_baseline_id_changes",
        "candidate_baseline_matches_r35_gate",
        "active_baseline_refresh_applied",
        "post_adoption_active_baseline_material_built",
        "historical_at_receipt_constants_preserved",
        "received_zip_adopted_as_current_active_source_snapshot_ref_after_evidence",
        "runtime_builder_refresh_not_applied_in_r36",
        "collect_only_is_not_execution_green",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 R36 must keep {key}=true")
    for key in (
        "historical_r21_r29_material_rewritten",
        "same_baseline_id_hash_replacement_allowed",
        "same_baseline_id_hash_replacement_applied",
        "active_baseline_update_applied_to_runtime_builders",
        "source_snapshot_ref_updated_in_active_builders",
        "received_zip_promoted_to_source_snapshot_ref",
        "execution_green_confirmed",
        "full_backend_suite_green_confirmed",
        "hold004_close_allowed",
        "p7_complete",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 R36 must keep {key}=false")
    if data.get("active_baseline_update_allowed") is not True or data.get("source_snapshot_ref_update_allowed") is not True:
        raise ValueError("P7-HOLD-004 R36 requires R35 update allowance")
    return True


def build_p7_hold004_post_adoption_received_snapshot_reconcile(
    *,
    post_adoption_active_baseline: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build R36 post-adoption received-snapshot reconcile material."""

    active_material = (
        safe_mapping(post_adoption_active_baseline)
        if post_adoption_active_baseline is not None
        else build_p7_hold004_post_adoption_active_baseline_material()
    )
    assert_p7_hold004_post_adoption_active_baseline_material_contract(active_material)
    active = safe_mapping(active_material.get("current_active_baseline"))
    received = _received_snapshot()
    comparison = {
        "file_count_match": active.get("collected_test_file_count") == received.get("collected_test_file_count"),
        "item_count_match": active.get("collected_test_item_count") == received.get("collected_test_item_count"),
        "warning_count_match": active.get("warnings_count") == received.get("warnings_count"),
        "warnings_match": active.get("warnings_count") == received.get("warnings_count"),
        "counts_match": (
            active.get("collected_test_file_count") == received.get("collected_test_file_count")
            and active.get("collected_test_item_count") == received.get("collected_test_item_count")
        ),
        "test_files_fingerprint_match": active.get("test_files_fingerprint_sha256") == received.get("test_files_fingerprint_sha256"),
        "test_items_fingerprint_match": active.get("test_items_fingerprint_sha256") == received.get("test_items_fingerprint_sha256"),
        "source_snapshot_ref_matches_received_zip_ref": active.get("source_snapshot_ref") == received.get("received_zip_ref"),
        "source_snapshot_ref_current_for_received_zip": active.get("source_snapshot_ref") == received.get("received_zip_ref"),
        "active_baseline_accepts_received_nodeids": active.get("test_items_fingerprint_sha256") == received.get("test_items_fingerprint_sha256"),
        "active_baseline_accepts_received_collect_nodeids": active.get("test_items_fingerprint_sha256") == received.get("test_items_fingerprint_sha256"),
    }
    reconciled = all(comparison.values())
    material = {
        "schema_version": P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_STEP,
        "implementation_step": P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_STEP,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "reconcile_id": P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_ID,
        "historical_received_reconcile_id": P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_ID,
        "active_baseline_refresh_id": clean_identifier(
            active_material.get("active_baseline_refresh_id"), default=P7_HOLD004_ACTIVE_BASELINE_REFRESH_ID, max_length=180
        ),
        "source_mode": P7_SOURCE_MODE,
        "git_checked": P7_GIT_CHECKED,
        "previous_active_baseline": safe_mapping(active_material.get("previous_active_baseline")),
        "active_baseline": active,
        "received_snapshot": received,
        "comparison": comparison,
        "classification": {
            "status": P7_HOLD004_RECEIVED_RECONCILE_STATUS_MATCHES_ACTIVE_BASELINE,
            "classification_required": False,
            "root_cause_status": "BASELINE_CONSTANT_STALE",
            "root_cause_classified": True,
            "item_fingerprint_mismatch_unclassified": False,
            "source_identity_unclear": False,
        },
        "received_snapshot_baseline_fingerprint_reconciled": reconciled,
        "received_snapshot_item_fingerprint_mismatch_unresolved": False,
        "source_snapshot_ref_current_for_received_zip": comparison["source_snapshot_ref_current_for_received_zip"],
        "active_baseline_accepts_received_nodeids": comparison["active_baseline_accepts_received_nodeids"],
        "post_adoption_reconcile_material_built": True,
        "historical_r21_r29_material_rewritten": False,
        "collect_only_is_not_execution_green": True,
        "execution_green_confirmed": False,
        "active_baseline_update_applied_to_runtime_builders": False,
        "source_snapshot_ref_updated_in_active_builders": False,
        **_capture_closed_boundary(),
        **_release_closed_boundary(),
        **_body_retention_flags(),
        "implementation_scope": dict(_R36_IMPLEMENTATION_SCOPE_FLAGS),
        "unresolved_hold_refs": [P7_HOLD004_BACKEND_SUITE_HOLD_ID],
        "required_followup_fixes": list(_R36_REQUIRED_FOLLOWUP_FIXES),
        "public_contract": _public_contract_boundary_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_hold004_post_adoption_received_snapshot_reconcile_contract(material)
    return material


def assert_p7_hold004_post_adoption_received_snapshot_reconcile_contract(material: Mapping[str, Any]) -> bool:
    """Validate R36 post-adoption received-snapshot reconcile material."""

    data = safe_mapping(material)
    source = "p7_hold004_post_adoption_received_snapshot_reconcile"
    if data.get("schema_version") != P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 R36 post-adoption reconcile schema_version mismatch")
    if data.get("implementation_step") != P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_STEP:
        raise ValueError("P7-HOLD-004 R36 post-adoption reconcile step mismatch")
    if data.get("reconcile_id") != P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_ID:
        raise ValueError("P7-HOLD-004 R36 post-adoption reconcile id mismatch")
    _assert_common_body_free_closed(data, source=source)
    _implementation_scope_contract(safe_mapping(data.get("implementation_scope")), expected=_R36_IMPLEMENTATION_SCOPE_FLAGS, source=source)
    previous = safe_mapping(data.get("previous_active_baseline"))
    active = safe_mapping(data.get("active_baseline"))
    received = safe_mapping(data.get("received_snapshot"))
    if previous != _previous_active_baseline():
        raise ValueError("P7-HOLD-004 R36 post-adoption previous active mismatch")
    if active != _current_active_baseline():
        raise ValueError("P7-HOLD-004 R36 post-adoption active mismatch")
    if received != _received_snapshot():
        raise ValueError("P7-HOLD-004 R36 received snapshot mismatch")
    comparison = safe_mapping(data.get("comparison"))
    required_true = (
        "file_count_match",
        "item_count_match",
        "warning_count_match",
        "warnings_match",
        "counts_match",
        "test_files_fingerprint_match",
        "test_items_fingerprint_match",
        "source_snapshot_ref_matches_received_zip_ref",
        "source_snapshot_ref_current_for_received_zip",
        "active_baseline_accepts_received_nodeids",
        "active_baseline_accepts_received_collect_nodeids",
    )
    for key in required_true:
        if comparison.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 R36 post-adoption comparison {key} must be true")
    classification = safe_mapping(data.get("classification"))
    if classification.get("status") != P7_HOLD004_RECEIVED_RECONCILE_STATUS_MATCHES_ACTIVE_BASELINE:
        raise ValueError("P7-HOLD-004 R36 post-adoption status mismatch")
    for key in (
        "classification_required",
        "item_fingerprint_mismatch_unclassified",
        "source_identity_unclear",
    ):
        if classification.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 R36 post-adoption classification {key} must be false")
    for key in (
        "root_cause_classified",
    ):
        if classification.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 R36 post-adoption classification {key} must be true")
    for key in (
        "received_snapshot_baseline_fingerprint_reconciled",
        "source_snapshot_ref_current_for_received_zip",
        "active_baseline_accepts_received_nodeids",
        "post_adoption_reconcile_material_built",
        "collect_only_is_not_execution_green",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 R36 post-adoption must keep {key}=true")
    for key in (
        "received_snapshot_item_fingerprint_mismatch_unresolved",
        "historical_r21_r29_material_rewritten",
        "execution_green_confirmed",
        "active_baseline_update_applied_to_runtime_builders",
        "source_snapshot_ref_updated_in_active_builders",
        "full_backend_suite_green_confirmed",
        "hold004_close_allowed",
        "p7_complete",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 R36 post-adoption must keep {key}=false")
    return True


def _builder_connection_status(builder_name: str, material: Mapping[str, Any]) -> dict[str, Any]:
    data = safe_mapping(material)
    current = _current_active_baseline()
    collect_id = data.get("baseline_id") or data.get("collect_baseline_id") or data.get("backend_suite_execution_summary_collect_baseline_id")
    source_snapshot_ref = data.get("source_snapshot_ref")
    if not source_snapshot_ref and isinstance(data.get("matrix_current_baseline_connection"), Mapping):
        source_snapshot_ref = P7_HOLD004_BACKEND_SOURCE_SNAPSHOT_REF
    return {
        "builder_ref": builder_name,
        "collect_baseline_id": clean_identifier(collect_id, default="", max_length=180),
        "source_snapshot_ref": clean_identifier(source_snapshot_ref, default="", max_length=180),
        "current_active_baseline_id_match": collect_id == current["baseline_id"],
        "current_active_source_snapshot_ref_match": source_snapshot_ref == current["source_snapshot_ref"],
        "release_allowed": data.get("release_allowed") is True,
        "full_backend_suite_green_confirmed": data.get("full_backend_suite_green_confirmed") is True,
        "body_free": data.get("body_free") is True,
    }


def build_p7_hold004_runtime_builder_refresh_status(
    *,
    post_adoption_active_baseline: Mapping[str, Any] | None = None,
    post_adoption_received_snapshot_reconcile: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build R37 runtime-builder refresh status material."""

    active_material = (
        safe_mapping(post_adoption_active_baseline)
        if post_adoption_active_baseline is not None
        else build_p7_hold004_post_adoption_active_baseline_material()
    )
    assert_p7_hold004_post_adoption_active_baseline_material_contract(active_material)
    reconcile_material = (
        safe_mapping(post_adoption_received_snapshot_reconcile)
        if post_adoption_received_snapshot_reconcile is not None
        else build_p7_hold004_post_adoption_received_snapshot_reconcile(
            post_adoption_active_baseline=active_material
        )
    )
    assert_p7_hold004_post_adoption_received_snapshot_reconcile_contract(reconcile_material)

    backend_baseline = build_p7_hold004_current_backend_collect_baseline()
    assert_p7_hold004_backend_collect_baseline_contract(backend_baseline)
    group_inventory = build_p7_hold004_backend_suite_group_inventory(collect_baseline=backend_baseline)
    assert_p7_hold004_backend_suite_group_inventory_contract(group_inventory)
    execution_plan = build_p7_hold004_backend_suite_execution_plan(inventory=group_inventory)
    assert_p7_hold004_backend_suite_execution_plan_contract(execution_plan)
    execution_summary = build_p7_hold004_backend_suite_execution_summary(plan=execution_plan)
    assert_p7_hold004_backend_suite_execution_summary_contract(execution_summary)
    matrix_report = build_p7_hold004_matrix_consistency_report(backend_suite_execution_summary=execution_summary)
    assert_p7_hold004_matrix_consistency_report_contract(matrix_report)
    minimal_order = build_p7_hold004_group_execution_minimal_order(
        execution_plan=execution_plan,
        matrix_consistency_report=matrix_report,
    )
    assert_p7_hold004_group_execution_minimal_order_contract(minimal_order)

    builder_connections = [
        _builder_connection_status("backend_suite_split_consistency", backend_baseline),
        _builder_connection_status("backend_suite_group_inventory_plan", group_inventory),
        _builder_connection_status("backend_suite_execution_plan", execution_plan),
        _builder_connection_status("backend_suite_execution_results", execution_summary),
        _builder_connection_status("matrix_consistency_report", matrix_report),
        _builder_connection_status("group_execution_minimal_order", minimal_order),
    ]
    current_id_match = all(item["current_active_baseline_id_match"] is True for item in builder_connections)
    current_source_match = all(item["current_active_source_snapshot_ref_match"] is True for item in builder_connections)
    runtime_builder_connections = {
        "backend_collect_baseline": dict(builder_connections[0]),
        "backend_suite_group_inventory_plan": dict(builder_connections[1]),
        "backend_suite_execution_plan": dict(builder_connections[2]),
        "backend_suite_execution_results": dict(builder_connections[3]),
        "matrix_consistency_report": dict(builder_connections[4]),
        "group_execution_minimal_order": dict(builder_connections[5]),
    }
    current_active = safe_mapping(active_material.get("current_active_baseline"))
    material = {
        "schema_version": P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_STEP,
        "implementation_step": P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_STEP,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "refresh_status_id": P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_ID,
        "refresh_status": P7_HOLD004_RUNTIME_REFRESH_STATUS_APPLIED,
        "active_baseline_refresh_id": clean_identifier(
            active_material.get("active_baseline_refresh_id"), default=P7_HOLD004_ACTIVE_BASELINE_REFRESH_ID, max_length=180
        ),
        "post_adoption_received_snapshot_reconcile_id": clean_identifier(
            reconcile_material.get("reconcile_id"), default=P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_ID, max_length=180
        ),
        "source_mode": P7_SOURCE_MODE,
        "git_checked": P7_GIT_CHECKED,
        "previous_active_baseline_id": P7_HOLD004_PREVIOUS_ACTIVE_COLLECT_BASELINE_ID,
        "current_active_baseline_id": current_active.get("baseline_id"),
        "previous_active_source_snapshot_ref": P7_HOLD004_PREVIOUS_ACTIVE_SOURCE_SNAPSHOT_REF,
        "current_active_source_snapshot_ref": current_active.get("source_snapshot_ref"),
        "current_active_baseline": current_active,
        "active_baseline_refresh_applied": active_material.get("active_baseline_refresh_applied") is True,
        "backend_active_baseline_refresh_applied_constant": P7_HOLD004_BACKEND_ACTIVE_BASELINE_REFRESH_APPLIED is True,
        "updated_builder_refs": list(_RUNTIME_BUILDER_REFS),
        "builder_connections": builder_connections,
        "runtime_builder_connections": runtime_builder_connections,
        "active_baseline_update_applied_to_runtime_builders": current_id_match and current_source_match,
        "source_snapshot_ref_updated_in_active_builders": current_source_match,
        "current_collect_baseline_connected": current_id_match,
        "all_core_runtime_builders_read_current_active_baseline": current_id_match and current_source_match,
        "matrix_release_validation_connection_refresh_deferred_to_r38": True,
        "backend_suite_group_inventory_collect_baseline_id": group_inventory.get("collect_baseline_id"),
        "backend_suite_execution_plan_collect_baseline_id": execution_plan.get("collect_baseline_id"),
        "backend_suite_execution_summary_collect_baseline_id": execution_summary.get("collect_baseline_id"),
        "matrix_consistency_report_collect_baseline_id": matrix_report.get("backend_suite_execution_summary_collect_baseline_id"),
        "group_execution_minimal_order_collect_baseline_id": minimal_order.get("collect_baseline_id"),
        "matrix_consistency_report_current_baseline_connected": matrix_report.get("current_collect_baseline_connected") is True,
        "matrix_consistency_report_received_snapshot_status_refresh_deferred_to_r38": True,
        "backend_suite_execution_summary_id": P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_ID,
        "group_inventory_id": P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID,
        "execution_plan_id": P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID,
        "group_execution_minimal_order_id": P7_HOLD004_GROUP_EXECUTION_MINIMAL_ORDER_ID,
        "matrix_consistency_report_id": P7_HOLD004_MATRIX_CONSISTENCY_REPORT_ID,
        "received_snapshot_baseline_fingerprint_reconciled": reconcile_material.get(
            "received_snapshot_baseline_fingerprint_reconciled"
        ) is True,
        "received_snapshot_item_fingerprint_mismatch_unresolved": reconcile_material.get(
            "received_snapshot_item_fingerprint_mismatch_unresolved"
        ) is True,
        "source_snapshot_ref_current_for_received_zip": reconcile_material.get("source_snapshot_ref_current_for_received_zip") is True,
        "active_baseline_accepts_received_nodeids": reconcile_material.get("active_baseline_accepts_received_nodeids") is True,
        "same_baseline_id_hash_replacement_allowed": False,
        "same_baseline_id_hash_replacement_applied": False,
        "previous_active_baseline_retained": True,
        "historical_r21_r29_material_rewritten": False,
        "collect_only_is_not_execution_green": True,
        "execution_green_confirmed": False,
        **_capture_closed_boundary(),
        **_release_closed_boundary(),
        **_body_retention_flags(),
        "implementation_scope": dict(_R37_IMPLEMENTATION_SCOPE_FLAGS),
        "unresolved_hold_refs": [P7_HOLD004_BACKEND_SUITE_HOLD_ID],
        "required_followup_fixes": list(_R37_REQUIRED_FOLLOWUP_FIXES),
        "public_contract": _public_contract_boundary_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_hold004_runtime_builder_refresh_status_contract(material)
    return material


def assert_p7_hold004_runtime_builder_refresh_status_contract(material: Mapping[str, Any]) -> bool:
    """Validate R37 runtime-builder refresh status material."""

    data = safe_mapping(material)
    source = "p7_hold004_runtime_builder_refresh_status"
    if data.get("schema_version") != P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 R37 runtime refresh schema_version mismatch")
    if data.get("implementation_step") != P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_STEP:
        raise ValueError("P7-HOLD-004 R37 runtime refresh step mismatch")
    if data.get("refresh_status_id") != P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_ID:
        raise ValueError("P7-HOLD-004 R37 runtime refresh id mismatch")
    if data.get("refresh_status") != P7_HOLD004_RUNTIME_REFRESH_STATUS_APPLIED:
        raise ValueError("P7-HOLD-004 R37 runtime refresh status mismatch")
    _assert_common_body_free_closed(data, source=source)
    _implementation_scope_contract(safe_mapping(data.get("implementation_scope")), expected=_R37_IMPLEMENTATION_SCOPE_FLAGS, source=source)
    current = safe_mapping(data.get("current_active_baseline"))
    if current != _current_active_baseline():
        raise ValueError("P7-HOLD-004 R37 current active baseline mismatch")
    if data.get("current_active_baseline_id") != P7_HOLD004_BACKEND_COLLECT_BASELINE_ID:
        raise ValueError("P7-HOLD-004 R37 current active baseline id mismatch")
    if data.get("current_active_source_snapshot_ref") != P7_HOLD004_BACKEND_SOURCE_SNAPSHOT_REF:
        raise ValueError("P7-HOLD-004 R37 current source snapshot ref mismatch")
    builder_refs = dedupe_identifiers(data.get("updated_builder_refs"), limit=20, max_length=120)
    if tuple(builder_refs) != _RUNTIME_BUILDER_REFS:
        raise ValueError("P7-HOLD-004 R37 updated builder refs mismatch")
    connections = data.get("builder_connections")
    if not isinstance(connections, list) or len(connections) != len(_RUNTIME_BUILDER_REFS):
        raise ValueError("P7-HOLD-004 R37 builder connections mismatch")
    for connection_value in connections:
        connection = safe_mapping(connection_value)
        if connection.get("builder_ref") not in _RUNTIME_BUILDER_REFS:
            raise ValueError("P7-HOLD-004 R37 unknown builder ref")
        if connection.get("collect_baseline_id") != P7_HOLD004_BACKEND_COLLECT_BASELINE_ID:
            raise ValueError("P7-HOLD-004 R37 builder collect baseline mismatch")
        if connection.get("source_snapshot_ref") != P7_HOLD004_BACKEND_SOURCE_SNAPSHOT_REF:
            raise ValueError("P7-HOLD-004 R37 builder source snapshot mismatch")
        if connection.get("current_active_baseline_id_match") is not True:
            raise ValueError("P7-HOLD-004 R37 builder active id match flag mismatch")
        if connection.get("current_active_source_snapshot_ref_match") is not True:
            raise ValueError("P7-HOLD-004 R37 builder source match flag mismatch")
        if connection.get("release_allowed") is not False:
            raise ValueError("P7-HOLD-004 R37 builder must not allow release")
        if connection.get("full_backend_suite_green_confirmed") is not False:
            raise ValueError("P7-HOLD-004 R37 builder must not claim full suite green")
        if connection.get("body_free") is not True:
            raise ValueError("P7-HOLD-004 R37 builder material must be body_free")
    runtime_connections = data.get("runtime_builder_connections")
    expected_runtime_connection_keys = {
        "backend_collect_baseline",
        "backend_suite_group_inventory_plan",
        "backend_suite_execution_plan",
        "backend_suite_execution_results",
        "matrix_consistency_report",
        "group_execution_minimal_order",
    }
    if not isinstance(runtime_connections, Mapping) or set(runtime_connections) != expected_runtime_connection_keys:
        raise ValueError("P7-HOLD-004 R37 runtime builder connections mismatch")
    for connection_value in runtime_connections.values():
        connection = safe_mapping(connection_value)
        if connection.get("collect_baseline_id") != P7_HOLD004_BACKEND_COLLECT_BASELINE_ID:
            raise ValueError("P7-HOLD-004 R37 runtime builder collect baseline mismatch")
        if connection.get("source_snapshot_ref") != P7_HOLD004_BACKEND_SOURCE_SNAPSHOT_REF:
            raise ValueError("P7-HOLD-004 R37 runtime builder source snapshot mismatch")
    for key in (
        "active_baseline_refresh_applied",
        "backend_active_baseline_refresh_applied_constant",
        "active_baseline_update_applied_to_runtime_builders",
        "source_snapshot_ref_updated_in_active_builders",
        "current_collect_baseline_connected",
        "all_core_runtime_builders_read_current_active_baseline",
        "matrix_consistency_report_current_baseline_connected",
        "matrix_consistency_report_received_snapshot_status_refresh_deferred_to_r38",
        "matrix_release_validation_connection_refresh_deferred_to_r38",
        "received_snapshot_baseline_fingerprint_reconciled",
        "source_snapshot_ref_current_for_received_zip",
        "active_baseline_accepts_received_nodeids",
        "previous_active_baseline_retained",
        "collect_only_is_not_execution_green",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 R37 must keep {key}=true")
    for key in (
        "received_snapshot_item_fingerprint_mismatch_unresolved",
        "same_baseline_id_hash_replacement_allowed",
        "same_baseline_id_hash_replacement_applied",
        "historical_r21_r29_material_rewritten",
        "execution_green_confirmed",
        "official_group_02_capture_run_allowed",
        "official_group_02_capture_result_recording_allowed",
        "official_group_02_capture_green_confirmed",
        "can_claim_group_green",
        "can_claim_full_backend_suite_green",
        "full_backend_suite_green_confirmed",
        "hold004_close_allowed",
        "p7_complete",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 R37 must keep {key}=false")
    for baseline_key in (
        "backend_suite_group_inventory_collect_baseline_id",
        "backend_suite_execution_plan_collect_baseline_id",
        "backend_suite_execution_summary_collect_baseline_id",
        "matrix_consistency_report_collect_baseline_id",
        "group_execution_minimal_order_collect_baseline_id",
    ):
        if data.get(baseline_key) != P7_HOLD004_BACKEND_COLLECT_BASELINE_ID:
            raise ValueError(f"P7-HOLD-004 R37 {baseline_key} mismatch")
    followups = set(dedupe_identifiers(data.get("required_followup_fixes"), limit=80, max_length=180))
    if "official_group_02_capture_readiness_re_evaluation_required_after_r37" not in followups:
        raise ValueError("P7-HOLD-004 R37 must keep official group_02 readiness followup")
    if "full_backend_suite_green_unconfirmed" not in followups:
        raise ValueError("P7-HOLD-004 R37 must keep full backend suite followup")
    return True


def build_p7_hold004_official_group02_capture_readiness_re_evaluation(
    *,
    post_adoption_received_snapshot_reconcile: Mapping[str, Any] | None = None,
    runtime_builder_refresh_status: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build R39 official group_02 capture readiness after runtime refresh."""

    reconcile = (
        safe_mapping(post_adoption_received_snapshot_reconcile)
        if post_adoption_received_snapshot_reconcile is not None
        else build_p7_hold004_post_adoption_received_snapshot_reconcile()
    )
    assert_p7_hold004_post_adoption_received_snapshot_reconcile_contract(reconcile)
    runtime_status = (
        safe_mapping(runtime_builder_refresh_status)
        if runtime_builder_refresh_status is not None
        else build_p7_hold004_runtime_builder_refresh_status(post_adoption_received_snapshot_reconcile=reconcile)
    )
    assert_p7_hold004_runtime_builder_refresh_status_contract(runtime_status)
    material = build_p7_hold004_official_group02_capture_readiness(
        received_snapshot_reconcile=reconcile,
        runtime_builder_refresh_status=runtime_status,
    )
    assert_p7_hold004_official_group02_capture_readiness_re_evaluation_contract(material)
    return material


def assert_p7_hold004_official_group02_capture_readiness_re_evaluation_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    assert_p7_hold004_official_group02_capture_readiness_contract(data)
    if data.get("schema_version") != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION_V2:
        raise ValueError("P7-HOLD-004 R39 readiness must use v2 schema")
    if data.get("step") != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_REEVALUATION_STEP:
        raise ValueError("P7-HOLD-004 R39 readiness step mismatch")
    if data.get("readiness_id") != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_REEVALUATION_ID:
        raise ValueError("P7-HOLD-004 R39 readiness id mismatch")
    if data.get("readiness_status") != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY:
        raise ValueError("P7-HOLD-004 R39 readiness must be READY")
    for key in (
        "received_snapshot_baseline_fingerprint_reconciled",
        "source_snapshot_ref_current_for_received_zip",
        "active_baseline_accepts_received_nodeids",
        "active_baseline_update_applied_to_runtime_builders",
        "source_snapshot_ref_updated_in_active_builders",
        "post_adoption_readiness_re_evaluated",
        "official_capture_run_allowed",
        "official_capture_result_recording_allowed",
        "body_free",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 R39 readiness must keep {key}=true")
    for key in (
        "received_snapshot_item_fingerprint_mismatch_unresolved",
        "official_group_02_capture_blocked",
        "official_group_02_capture_green_confirmed",
        "can_claim_group_green",
        "can_claim_full_backend_suite_green",
        "full_backend_suite_green_confirmed",
        "hold004_close_allowed",
        "p7_complete",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 R39 readiness must keep {key}=false")
    for key in _BODY_RETENTION_KEYS:
        if data.get(key, False) is not False:
            raise ValueError(f"P7-HOLD-004 R39 readiness must keep {key}=false")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_hold004_r39_readiness.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_hold004_r39_readiness.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_hold004_r39_readiness")
    return True


def _r38_layer_projection(layer_name: str, material: Mapping[str, Any]) -> dict[str, Any]:
    data = safe_mapping(material)
    checks = safe_mapping(data.get("checks"))
    return {
        "layer_name": layer_name,
        "layer": layer_name,
        "schema_version": clean_identifier(data.get("schema_version"), default="", max_length=180),
        "active_baseline_refresh_schema_version": clean_identifier(
            data.get("active_baseline_refresh_schema_version"), default="", max_length=160
        ),
        "active_baseline_refresh_id": clean_identifier(data.get("active_baseline_refresh_id"), default="", max_length=180),
        "runtime_builder_refresh_status_id": clean_identifier(
            data.get("runtime_builder_refresh_status_id"), default="", max_length=180
        ),
        "post_adoption_received_snapshot_reconcile_id": clean_identifier(
            data.get("post_adoption_received_snapshot_reconcile_id"), default="", max_length=180
        ),
        "readiness_status": clean_identifier(
            data.get("official_group_02_capture_readiness_status"), default="", max_length=180
        ),
        "official_group_02_capture_readiness_status": clean_identifier(
            data.get("official_group_02_capture_readiness_status"), default="", max_length=180
        ),
        "official_group_02_capture_readiness_schema_version": clean_identifier(
            data.get("official_group_02_capture_readiness_schema_version"), default="", max_length=180
        ),
        "received_snapshot_baseline_fingerprint_reconciled": data.get(
            "received_snapshot_baseline_fingerprint_reconciled"
        ) is True,
        "received_snapshot_item_fingerprint_mismatch_unresolved": data.get(
            "received_snapshot_item_fingerprint_mismatch_unresolved"
        ) is True,
        "active_baseline_update_applied_to_runtime_builders": data.get(
            "active_baseline_update_applied_to_runtime_builders"
        ) is True,
        "source_snapshot_ref_updated_in_active_builders": data.get("source_snapshot_ref_updated_in_active_builders")
        is True,
        "post_adoption_readiness_re_evaluated": data.get("post_adoption_readiness_re_evaluated") is True,
        "official_group_02_capture_blocked": data.get("official_group_02_capture_blocked") is True,
        "official_group_02_capture_run_allowed": data.get("official_group_02_capture_run_allowed") is True,
        "official_group_02_capture_result_recording_allowed": data.get(
            "official_group_02_capture_result_recording_allowed"
        ) is True,
        "official_group_02_capture_green_confirmed": data.get("official_group_02_capture_green_confirmed") is True,
        "can_claim_group_green": data.get("can_claim_group_green") is True,
        "can_claim_full_backend_suite_green": data.get("can_claim_full_backend_suite_green") is True,
        "full_backend_suite_green_confirmed": data.get("full_backend_suite_green_confirmed") is True,
        "hold004_close_allowed": data.get("hold004_close_allowed") is True,
        "p7_complete": data.get("p7_complete") is True,
        "p8_start_allowed": data.get("p8_start_allowed") is True,
        "release_allowed": data.get("release_allowed") is True,
        "matrix_consistency_status": clean_identifier(data.get("consistency_status"), default="", max_length=80),
        "matrix_consistency_received_snapshot_ready": checks.get("received_snapshot_blocking_status_consistent") is True,
        "matrix_consistency_active_refresh_projected": checks.get("active_baseline_refresh_projection_consistent") is True,
        "body_free": data.get("body_free") is True,
    }


def build_p7_hold004_matrix_release_validation_connection_refresh(
    *,
    runtime_builder_refresh_status: Mapping[str, Any] | None = None,
    post_adoption_received_snapshot_reconcile: Mapping[str, Any] | None = None,
    official_group02_capture_readiness: Mapping[str, Any] | None = None,
    backend_suite_execution_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build R38/R39 matrix, release handoff, validation, and readiness refresh."""

    reconcile = (
        safe_mapping(post_adoption_received_snapshot_reconcile)
        if post_adoption_received_snapshot_reconcile is not None
        else build_p7_hold004_post_adoption_received_snapshot_reconcile()
    )
    assert_p7_hold004_post_adoption_received_snapshot_reconcile_contract(reconcile)
    runtime_status = (
        safe_mapping(runtime_builder_refresh_status)
        if runtime_builder_refresh_status is not None
        else build_p7_hold004_runtime_builder_refresh_status(post_adoption_received_snapshot_reconcile=reconcile)
    )
    assert_p7_hold004_runtime_builder_refresh_status_contract(runtime_status)
    readiness = (
        safe_mapping(official_group02_capture_readiness)
        if official_group02_capture_readiness is not None
        else build_p7_hold004_official_group02_capture_readiness_re_evaluation(
            post_adoption_received_snapshot_reconcile=reconcile,
            runtime_builder_refresh_status=runtime_status,
        )
    )
    assert_p7_hold004_official_group02_capture_readiness_re_evaluation_contract(readiness)
    execution_summary = (
        safe_mapping(backend_suite_execution_summary)
        if backend_suite_execution_summary is not None
        else build_p7_hold004_backend_suite_execution_summary()
    )
    assert_p7_hold004_backend_suite_execution_summary_contract(execution_summary)

    connection_timeout = build_p7_connection_e2e_r13_passed_observation_result()
    assert_p7_e2e_isolation_result_contract(connection_timeout)
    red_closure = build_p7_red_closure_classification_matrix(
        connection_timeout_isolation_result=connection_timeout
    )
    assert_p7_red_closure_classification_matrix_contract(red_closure)

    backend_split = build_p7_backend_suite_split_matrix(
        backend_suite_execution_summary=execution_summary,
        red_closure_classification_matrix=red_closure,
        connection_timeout_isolation_result=connection_timeout,
        official_group02_capture_readiness=readiness,
    )
    assert_p7_backend_suite_split_matrix_contract(backend_split)
    r10_hold_matrix = build_p7_r10_hold_matrix(
        backend_suite_split_matrix=backend_split,
        backend_suite_execution_summary=execution_summary,
        red_closure_classification_matrix=red_closure,
        connection_timeout_isolation_result=connection_timeout,
        official_group02_capture_readiness=readiness,
    )
    assert_p7_r10_hold_matrix_contract(r10_hold_matrix)
    release_handoff = build_p7_release_decision_handoff(
        backend_suite_execution_summary=execution_summary,
        backend_suite_split_matrix=backend_split,
        r10_hold_matrix=r10_hold_matrix,
        red_closure_classification_matrix=red_closure,
        connection_timeout_isolation_result=connection_timeout,
    )
    assert_p7_release_decision_handoff_contract(release_handoff)
    validation_seed = build_p7_validation_regression_matrix(
        backend_suite_execution_summary=execution_summary,
        backend_suite_split_matrix=backend_split,
        r10_hold_matrix=r10_hold_matrix,
        release_handoff=release_handoff,
        red_closure_classification_matrix=red_closure,
        connection_timeout_isolation_result=connection_timeout,
    )
    assert_p7_validation_regression_matrix_contract(validation_seed)
    matrix_report_seed = build_p7_hold004_matrix_consistency_report(
        backend_suite_execution_summary=execution_summary,
        red_closure_classification_matrix=red_closure,
        backend_suite_split_matrix=backend_split,
        r10_hold_matrix=r10_hold_matrix,
        release_handoff=release_handoff,
        validation_matrix=validation_seed,
    )
    assert_p7_hold004_matrix_consistency_report_contract(matrix_report_seed)
    validation_matrix = build_p7_validation_regression_matrix(
        backend_suite_execution_summary=execution_summary,
        backend_suite_split_matrix=backend_split,
        r10_hold_matrix=r10_hold_matrix,
        release_handoff=release_handoff,
        red_closure_classification_matrix=red_closure,
        connection_timeout_isolation_result=connection_timeout,
        matrix_consistency_report=matrix_report_seed,
    )
    assert_p7_validation_regression_matrix_contract(validation_matrix)
    matrix_report = build_p7_hold004_matrix_consistency_report(
        backend_suite_execution_summary=execution_summary,
        red_closure_classification_matrix=red_closure,
        backend_suite_split_matrix=backend_split,
        r10_hold_matrix=r10_hold_matrix,
        release_handoff=release_handoff,
        validation_matrix=validation_matrix,
    )
    assert_p7_hold004_matrix_consistency_report_contract(matrix_report)

    layer_connections = [
        _r38_layer_projection("backend_suite_split_matrix", backend_split),
        _r38_layer_projection("r10_hold_matrix", r10_hold_matrix),
        _r38_layer_projection("release_handoff", release_handoff),
        _r38_layer_projection("validation_matrix", validation_matrix),
        _r38_layer_projection("matrix_consistency_report", matrix_report),
    ]
    refresh_projected = all(
        item["active_baseline_update_applied_to_runtime_builders"] is True
        and item["source_snapshot_ref_updated_in_active_builders"] is True
        and item["active_baseline_refresh_schema_version"] == P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_SCHEMA_VERSION
        and item["active_baseline_refresh_id"] == P7_HOLD004_ACTIVE_BASELINE_REFRESH_ID
        and item["runtime_builder_refresh_status_id"] == P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_ID
        and item["post_adoption_received_snapshot_reconcile_id"] == P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_ID
        for item in layer_connections
    )
    readiness_projected = all(
        item["readiness_status"] == P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY
        and item["received_snapshot_baseline_fingerprint_reconciled"] is True
        and item["received_snapshot_item_fingerprint_mismatch_unresolved"] is False
        and item["official_group_02_capture_blocked"] is False
        and item["official_group_02_capture_run_allowed"] is True
        and item["official_group_02_capture_result_recording_allowed"] is True
        and item["official_group_02_capture_green_confirmed"] is False
        and item["full_backend_suite_green_confirmed"] is False
        and item["release_allowed"] is False
        for item in layer_connections
    )

    material = {
        "schema_version": P7_HOLD004_MATRIX_RELEASE_VALIDATION_CONNECTION_REFRESH_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "step": P7_HOLD004_MATRIX_RELEASE_VALIDATION_CONNECTION_REFRESH_STEP,
        "implementation_step": P7_HOLD004_MATRIX_RELEASE_VALIDATION_CONNECTION_REFRESH_STEP,
        "connection_refresh_id": P7_HOLD004_MATRIX_RELEASE_VALIDATION_CONNECTION_REFRESH_ID,
        "source_mode": P7_SOURCE_MODE,
        "git_checked": P7_GIT_CHECKED,
        "active_baseline_refresh_schema_version": P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_SCHEMA_VERSION,
        "active_baseline_refresh_id": P7_HOLD004_ACTIVE_BASELINE_REFRESH_ID,
        "runtime_builder_refresh_status_id": P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_ID,
        "post_adoption_received_snapshot_reconcile_id": P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_ID,
        "current_active_baseline_id": P7_HOLD004_BACKEND_COLLECT_BASELINE_ID,
        "previous_active_baseline_id": P7_HOLD004_PREVIOUS_ACTIVE_COLLECT_BASELINE_ID,
        "current_active_source_snapshot_ref": P7_HOLD004_BACKEND_SOURCE_SNAPSHOT_REF,
        "previous_active_source_snapshot_ref": P7_HOLD004_PREVIOUS_ACTIVE_SOURCE_SNAPSHOT_REF,
        "official_group_02_capture_readiness_schema_version": P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION_V2,
        "official_group_02_capture_readiness_id": P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_REEVALUATION_ID,
        "official_group_02_capture_readiness_status": P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY,
        "official_group02_capture_readiness_schema_version": P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION_V2,
        "official_group02_capture_readiness_id": P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_REEVALUATION_ID,
        "official_group02_capture_readiness_status": P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY,
        "connected_material_projections": layer_connections,
        "layer_connections": layer_connections,
        "matrix_consistency_report_id": clean_identifier(matrix_report.get("report_id"), max_length=180),
        "matrix_consistency_report_status": clean_identifier(matrix_report.get("consistency_status"), max_length=80),
        "matrix_consistency_report_checks": safe_mapping(matrix_report.get("checks")),
        "matrix_release_validation_connection_refresh_applied": refresh_projected and readiness_projected,
        "matrix_release_validation_connection_refresh_satisfied": refresh_projected and readiness_projected,
        "backend_suite_split_matrix_received_snapshot_status_resolved": True,
        "r10_hold_matrix_received_snapshot_status_resolved": True,
        "release_handoff_received_snapshot_status_resolved": True,
        "validation_matrix_received_snapshot_status_resolved": True,
        "active_baseline_update_applied_to_runtime_builders": refresh_projected,
        "source_snapshot_ref_updated_in_active_builders": refresh_projected,
        "post_adoption_readiness_re_evaluated": True,
        "received_snapshot_baseline_fingerprint_reconciled": True,
        "received_snapshot_item_fingerprint_mismatch_unresolved": False,
        "source_snapshot_ref_current_for_received_zip": True,
        "active_baseline_accepts_received_nodeids": True,
        "official_group_02_capture_blocked": False,
        "official_group_02_capture_run_allowed": True,
        "official_group_02_capture_result_recording_allowed": True,
        "official_group_02_capture_green_confirmed": False,
        "official_group_02_official_full_run_executed": False,
        "official_group_02_capture_result_recorded": False,
        "can_claim_group_green": False,
        "can_claim_full_backend_suite_green": False,
        "full_backend_suite_green_confirmed": False,
        "hold004_close_allowed": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "group02_readiness_is_not_group_green": True,
        "group02_readiness_is_not_full_backend_suite_green": True,
        "group02_readiness_is_not_release_ready": True,
        "collect_only_is_not_execution_green": True,
        "execution_green_confirmed": False,
        "body_free": True,
        "unresolved_hold_refs": ["P7-HOLD-001", "P7-HOLD-003", P7_HOLD004_BACKEND_SUITE_HOLD_ID],
        "public_contract": _public_contract_boundary_flags(),
        "body_free_markers": _body_free_markers(),
        **_body_retention_flags(),
        "raw_input_retained": False,
        "comment_text_retained": False,
        "candidate_body_retained": False,
        "surface_body_retained": False,
        "required_followup_fixes": list(_R38_R39_REQUIRED_FOLLOWUP_FIXES),
    }
    assert_p7_hold004_matrix_release_validation_connection_refresh_contract(material)
    return material


def assert_p7_hold004_matrix_release_validation_connection_refresh_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    if data.get("schema_version") != P7_HOLD004_MATRIX_RELEASE_VALIDATION_CONNECTION_REFRESH_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 R38 connection refresh schema mismatch")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError("P7-HOLD-004 R38 connection refresh phase/hold mismatch")
    if data.get("connection_refresh_id") != P7_HOLD004_MATRIX_RELEASE_VALIDATION_CONNECTION_REFRESH_ID:
        raise ValueError("P7-HOLD-004 R38 connection refresh id mismatch")
    if data.get("active_baseline_refresh_schema_version") != P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 R38 active refresh schema mismatch")
    if data.get("active_baseline_refresh_id") != P7_HOLD004_ACTIVE_BASELINE_REFRESH_ID:
        raise ValueError("P7-HOLD-004 R38 active refresh id mismatch")
    if data.get("runtime_builder_refresh_status_id") != P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_ID:
        raise ValueError("P7-HOLD-004 R38 runtime refresh id mismatch")
    if data.get("post_adoption_received_snapshot_reconcile_id") != P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_ID:
        raise ValueError("P7-HOLD-004 R38 post-adoption reconcile id mismatch")
    if data.get("official_group_02_capture_readiness_schema_version") != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION_V2:
        raise ValueError("P7-HOLD-004 R38 readiness schema mismatch")
    if data.get("official_group_02_capture_readiness_status") != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY:
        raise ValueError("P7-HOLD-004 R38 readiness status mismatch")
    projections = data.get("layer_connections") or data.get("connected_material_projections")
    if not isinstance(projections, list) or len(projections) != 5:
        raise ValueError("P7-HOLD-004 R38 connection refresh must project five layers")
    layer_names = {safe_mapping(item).get("layer_name") or safe_mapping(item).get("layer") for item in projections}
    if layer_names != {
        "backend_suite_split_matrix",
        "r10_hold_matrix",
        "release_handoff",
        "validation_matrix",
        "matrix_consistency_report",
    }:
        raise ValueError("P7-HOLD-004 R38 projection layer mismatch")
    for projection_value in projections:
        projection = safe_mapping(projection_value)
        if projection.get("official_group_02_capture_readiness_schema_version") != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION_V2:
            raise ValueError("P7-HOLD-004 R38 projection readiness schema mismatch")
        if projection.get("readiness_status") != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY:
            raise ValueError("P7-HOLD-004 R38 projection readiness status mismatch")
        for key in (
            "received_snapshot_baseline_fingerprint_reconciled",
            "active_baseline_update_applied_to_runtime_builders",
            "source_snapshot_ref_updated_in_active_builders",
            "post_adoption_readiness_re_evaluated",
            "official_group_02_capture_run_allowed",
            "official_group_02_capture_result_recording_allowed",
            "body_free",
        ):
            if projection.get(key) is not True:
                raise ValueError(f"P7-HOLD-004 R38 projection must keep {key}=true")
        for key in (
            "received_snapshot_item_fingerprint_mismatch_unresolved",
            "official_group_02_capture_blocked",
            "official_group_02_capture_green_confirmed",
            "can_claim_group_green",
            "can_claim_full_backend_suite_green",
            "full_backend_suite_green_confirmed",
            "hold004_close_allowed",
            "release_allowed",
            "p7_complete",
            "p8_start_allowed",
        ):
            if projection.get(key) is not False:
                raise ValueError(f"P7-HOLD-004 R38 projection must keep {key}=false")
    for key in (
        "matrix_release_validation_connection_refresh_applied",
        "matrix_release_validation_connection_refresh_satisfied",
        "backend_suite_split_matrix_received_snapshot_status_resolved",
        "r10_hold_matrix_received_snapshot_status_resolved",
        "release_handoff_received_snapshot_status_resolved",
        "validation_matrix_received_snapshot_status_resolved",
        "active_baseline_update_applied_to_runtime_builders",
        "source_snapshot_ref_updated_in_active_builders",
        "post_adoption_readiness_re_evaluated",
        "received_snapshot_baseline_fingerprint_reconciled",
        "source_snapshot_ref_current_for_received_zip",
        "active_baseline_accepts_received_nodeids",
        "official_group_02_capture_run_allowed",
        "official_group_02_capture_result_recording_allowed",
        "group02_readiness_is_not_group_green",
        "group02_readiness_is_not_full_backend_suite_green",
        "group02_readiness_is_not_release_ready",
        "collect_only_is_not_execution_green",
        "body_free",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 R38 must keep {key}=true")
    for key in (
        "received_snapshot_item_fingerprint_mismatch_unresolved",
        "official_group_02_capture_blocked",
        "official_group_02_capture_green_confirmed",
        "official_group_02_official_full_run_executed",
        "official_group_02_capture_result_recorded",
        "can_claim_group_green",
        "can_claim_full_backend_suite_green",
        "full_backend_suite_green_confirmed",
        "hold004_close_allowed",
        "p7_complete",
        "p8_start_allowed",
        "release_allowed",
        "execution_green_confirmed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 R38 must keep {key}=false")
    for key in _BODY_RETENTION_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 R38 must keep {key}=false")
    checks = safe_mapping(data.get("matrix_consistency_report_checks"))
    if checks.get("received_snapshot_blocking_status_consistent") is not True:
        raise ValueError("P7-HOLD-004 R38 matrix consistency must carry ready snapshot status")
    if checks.get("received_snapshot_item_fingerprint_mismatch_resolved") is not True:
        raise ValueError("P7-HOLD-004 R38 matrix consistency must carry resolved item mismatch")
    if checks.get("active_baseline_refresh_projection_consistent") is not True:
        raise ValueError("P7-HOLD-004 R38 matrix consistency must carry active refresh projection")
    if P7_HOLD004_BACKEND_SUITE_HOLD_ID not in set(dedupe_identifiers(data.get("unresolved_hold_refs"), limit=80, max_length=120)):
        raise ValueError("P7-HOLD-004 R38 must keep HOLD-004 unresolved")
    followups = set(dedupe_identifiers(data.get("required_followup_fixes"), limit=80, max_length=180))
    if "group_02_official_full_run_not_executed" not in followups and "official_group_02_official_full_run_not_executed_after_r39_readiness" not in followups:
        raise ValueError("P7-HOLD-004 R38 must keep official group_02 execution followup")
    if "full_backend_suite_green_unconfirmed" not in followups:
        raise ValueError("P7-HOLD-004 R38 must keep full backend suite followup")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_hold004_r38_connection_refresh.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_hold004_r38_connection_refresh.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_hold004_r38_connection_refresh")
    return True


def _r40_result_status_from_adoption_decision(decision: Mapping[str, Any]) -> str:
    status = clean_identifier(safe_mapping(decision).get("adoption_status"), default="", max_length=180)
    if status == P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_GREEN:
        return P7_HOLD004_GROUP02_RESULT_STATUS_PASSED_ISOLATED
    if status == P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_RED:
        return P7_HOLD004_GROUP02_RESULT_STATUS_FAILED_ISOLATED
    if status == P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_TIMEOUT:
        return P7_HOLD004_GROUP02_RESULT_STATUS_TIMEOUT_ISOLATED
    if status in {
        P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_COLLECTION_FAILED,
        P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_INTERRUPTED,
    }:
        return P7_HOLD004_GROUP02_RESULT_STATUS_PARTIAL_OR_INTERRUPTED
    return P7_HOLD004_GROUP02_RESULT_STATUS_NOT_RUN


def _r40_release_body_free_contract(data: Mapping[str, Any], *, source: str) -> None:
    for key in _RELEASE_CLOSED_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=false")
    for key in _BODY_RETENTION_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=false")
    for key in (
        "raw_input_retained",
        "comment_text_retained",
        "candidate_body_retained",
        "surface_body_retained",
    ):
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=false")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must be body_free")
    assert_false_markers(safe_mapping(data.get("public_contract")), source=f"{source}.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source=f"{source}.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)


def _r40_body_free_result_projection(run_result: Mapping[str, Any]) -> dict[str, Any]:
    result = safe_mapping(run_result)
    first_failure = safe_mapping(result.get("first_failure"))
    timeout_capture = safe_mapping(result.get("timeout_capture"))
    return {
        "run_result_id": clean_identifier(result.get("run_result_id"), default="", max_length=220),
        "group_id": clean_identifier(result.get("group_id"), default="", max_length=120),
        "batch_id": clean_identifier(result.get("batch_id"), default="", max_length=160),
        "run_kind": clean_identifier(result.get("run_kind"), default="", max_length=80),
        "status": clean_identifier(result.get("status"), default="", max_length=80),
        "collect_baseline_id": clean_identifier(result.get("collect_baseline_id"), default="", max_length=180),
        "observed_counts": safe_mapping(result.get("observed_counts")),
        "first_failure_identifiers": {
            "present": first_failure.get("present") is True,
            "group_id": clean_identifier(result.get("group_id"), default="", max_length=120) if first_failure.get("present") is True else "",
            "batch_id": clean_identifier(result.get("batch_id"), default="", max_length=160) if first_failure.get("present") is True else "",
            "nodeid": clean_identifier(first_failure.get("nodeid"), default="", max_length=240),
            "file_ref": clean_identifier(first_failure.get("file_ref"), default="", max_length=240),
            "failure_kind": clean_identifier(first_failure.get("failure_kind"), default="", max_length=120),
            "owner_layer_candidate": clean_identifier(first_failure.get("owner_layer_candidate"), default="", max_length=120),
        },
        "timeout_identifiers": {
            "present": timeout_capture.get("present") is True,
            "group_id": clean_identifier(result.get("group_id"), default="", max_length=120) if timeout_capture.get("present") is True else "",
            "batch_id": clean_identifier(result.get("batch_id"), default="", max_length=160) if timeout_capture.get("present") is True else "",
            "elapsed_sec_bucket": clean_identifier(timeout_capture.get("elapsed_sec_bucket"), default="", max_length=80),
            "last_known_phase": clean_identifier(timeout_capture.get("last_known_phase"), default="", max_length=80),
        },
        "body_free": result.get("body_free") is True if result else True,
    }


def build_p7_hold004_official_group02_result_recording(
    *,
    official_group02_capture_readiness: Mapping[str, Any] | None = None,
    run_result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build R40 official group_02 result recording material.

    Without an explicit body-free run_result, this material stays NOT_RUN even
    when the R39 readiness guard is READY.  A supplied group_02 result may be
    recorded as isolated group material, but never as full backend suite green,
    HOLD closure, P7 completion, P8 start, or release readiness.
    """

    readiness = (
        safe_mapping(official_group02_capture_readiness)
        if official_group02_capture_readiness is not None
        else build_p7_hold004_official_group02_capture_readiness_re_evaluation()
    )
    assert_p7_hold004_official_group02_capture_readiness_re_evaluation_contract(readiness)
    result = safe_mapping(run_result)
    if result:
        assert_p7_hold004_backend_suite_group_run_result_contract(result)
    decision = build_p7_hold004_official_group02_capture_adoption_decision(
        run_result=result if result else None,
        readiness=readiness,
    )
    assert_p7_hold004_official_group02_capture_adoption_decision_contract(decision)

    result_recording_status = _r40_result_status_from_adoption_decision(decision)
    recordable = decision.get("official_group_02_capture_recorded") is True
    group_green = result_recording_status == P7_HOLD004_GROUP02_RESULT_STATUS_PASSED_ISOLATED
    failed = result_recording_status == P7_HOLD004_GROUP02_RESULT_STATUS_FAILED_ISOLATED
    timeout = result_recording_status == P7_HOLD004_GROUP02_RESULT_STATUS_TIMEOUT_ISOLATED
    partial_or_interrupted = result_recording_status == P7_HOLD004_GROUP02_RESULT_STATUS_PARTIAL_OR_INTERRUPTED
    not_run = result_recording_status == P7_HOLD004_GROUP02_RESULT_STATUS_NOT_RUN
    recorded_group_ids = [P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID] if recordable else []
    remaining_group_ids = [
        group_id for group_id in P7_HOLD004_BACKEND_SUITE_GROUP_IDS if group_id not in set(recorded_group_ids)
    ]
    followups = dedupe_identifiers(
        [
            "full_backend_suite_green_unconfirmed",
            "group_02_green_is_not_full_backend_suite_green" if group_green else "",
            "group_02_official_red_classification_required" if failed else "",
            "group_02_timeout_long_run_probe_required" if timeout else "",
            "group_02_partial_or_interrupted_followup_required" if partial_or_interrupted else "",
            "group_02_official_full_run_not_recorded" if not_run else "",
            "remaining_backend_groups_official_execution_required",
            "p7_hold004_closure_blocked_until_all_backend_groups_green",
        ],
        limit=120,
        max_length=180,
    )
    material = {
        "schema_version": P7_HOLD004_OFFICIAL_GROUP02_RESULT_RECORDING_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "step": P7_HOLD004_OFFICIAL_GROUP02_RESULT_RECORDING_STEP,
        "implementation_step": P7_HOLD004_OFFICIAL_GROUP02_RESULT_RECORDING_STEP,
        "recording_id": P7_HOLD004_OFFICIAL_GROUP02_RESULT_RECORDING_ID,
        "source_mode": P7_SOURCE_MODE,
        "git_checked": P7_GIT_CHECKED,
        "official_group_02_capture_readiness_schema_version": P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION_V2,
        "official_group_02_capture_readiness_id": P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_REEVALUATION_ID,
        "official_group_02_capture_readiness_status": P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY,
        "active_baseline_refresh_schema_version": P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_SCHEMA_VERSION,
        "active_baseline_refresh_id": P7_HOLD004_ACTIVE_BASELINE_REFRESH_ID,
        "runtime_builder_refresh_status_id": P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_ID,
        "post_adoption_received_snapshot_reconcile_id": P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_ID,
        "current_active_baseline_id": P7_HOLD004_BACKEND_COLLECT_BASELINE_ID,
        "previous_active_baseline_id": P7_HOLD004_PREVIOUS_ACTIVE_COLLECT_BASELINE_ID,
        "official_group_02_result_recording_status": result_recording_status,
        "result_status": result_recording_status,
        "official_group_02_official_full_run_executed": recordable,
        "official_group_02_capture_result_recorded": recordable,
        "official_capture_material_recordable": recordable,
        "official_capture_run_allowed": readiness.get("official_capture_run_allowed") is True,
        "official_capture_result_recording_allowed": readiness.get("official_capture_result_recording_allowed") is True,
        "official_group_02_capture_blocked": readiness.get("official_group_02_capture_blocked") is True,
        "official_group_02_capture_green_confirmed": group_green,
        "can_claim_group_green": group_green,
        "can_claim_full_backend_suite_green": False,
        "full_backend_suite_green_confirmed": False,
        "full_backend_suite_green_claim_allowed": False,
        "hold004_close_allowed": False,
        "p7_complete": False,
        "p7_complete_claim_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "split_green_is_full_backend_suite_green": False,
        "split_green_can_close_p7_hold004": False,
        "group02_green_is_not_full_backend_suite_green": group_green,
        "group02_pass_is_not_full_backend_suite_green": group_green,
        "group02_result_recording_is_not_full_backend_suite_gate": True,
        "group02_result_recording_is_not_release_ready": True,
        "full_backend_suite_gate_required": True,
        "full_backend_suite_green_requires_all_backend_groups": True,
        "recorded_backend_group_ids": recorded_group_ids,
        "remaining_backend_group_ids": remaining_group_ids,
        "remaining_backend_group_count": len(remaining_group_ids),
        "all_backend_groups_officially_executed": False,
        "all_backend_groups_green": False,
        "failed_group_ids": [P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID] if failed else [],
        "timeout_group_ids": [P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID] if timeout else [],
        "partial_or_interrupted_group_ids": [P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID] if partial_or_interrupted else [],
        "not_run_group_ids": [P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID] if not_run else [],
        "red_classification_required": failed,
        "timeout_classification_required": timeout,
        "long_run_probe_required": timeout,
        "timeout_is_green": False,
        "timeout_is_immediate_fail": False,
        "run_result_projection": _r40_body_free_result_projection(result),
        "adoption_decision_schema_version": P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_ADOPTION_DECISION_SCHEMA_VERSION,
        "adoption_status": decision.get("adoption_status"),
        "adoption_decision_projection": {
            "decision_id": clean_identifier(decision.get("decision_id"), default="", max_length=180),
            "adoption_status": clean_identifier(decision.get("adoption_status"), default="", max_length=180),
            "official_capture_material_recordable": recordable,
            "official_group_02_capture_green_confirmed": group_green,
            "can_claim_group_green": group_green,
            "can_claim_full_backend_suite_green": False,
            "body_free": decision.get("body_free") is True,
        },
        "body_free_result_recorded": True,
        "collect_only_is_not_execution_green": True,
        "unresolved_hold_refs": ["P7-HOLD-001", "P7-HOLD-003", P7_HOLD004_BACKEND_SUITE_HOLD_ID],
        "required_followup_fixes": followups,
        "public_contract": _public_contract_boundary_flags(),
        "body_free_markers": _body_free_markers(),
        **_body_retention_flags(),
        "raw_input_retained": False,
        "comment_text_retained": False,
        "candidate_body_retained": False,
        "surface_body_retained": False,
        "body_free": True,
    }
    assert_p7_hold004_official_group02_result_recording_contract(material)
    return material


def assert_p7_hold004_official_group02_result_recording_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    source = "p7_hold004_r40_official_group02_result_recording"
    if data.get("schema_version") != P7_HOLD004_OFFICIAL_GROUP02_RESULT_RECORDING_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 R40 result recording schema mismatch")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError("P7-HOLD-004 R40 result recording phase/hold mismatch")
    if data.get("step") != P7_HOLD004_OFFICIAL_GROUP02_RESULT_RECORDING_STEP:
        raise ValueError("P7-HOLD-004 R40 result recording step mismatch")
    if data.get("recording_id") != P7_HOLD004_OFFICIAL_GROUP02_RESULT_RECORDING_ID:
        raise ValueError("P7-HOLD-004 R40 result recording id mismatch")
    if data.get("official_group_02_capture_readiness_status") != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY:
        raise ValueError("P7-HOLD-004 R40 result recording requires R39 READY readiness")
    if data.get("official_group_02_capture_readiness_schema_version") != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION_V2:
        raise ValueError("P7-HOLD-004 R40 result recording readiness schema mismatch")
    if data.get("active_baseline_refresh_schema_version") != P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 R40 result recording active refresh schema mismatch")
    if data.get("runtime_builder_refresh_status_id") != P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_ID:
        raise ValueError("P7-HOLD-004 R40 result recording runtime refresh id mismatch")
    if data.get("post_adoption_received_snapshot_reconcile_id") != P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_ID:
        raise ValueError("P7-HOLD-004 R40 result recording reconcile id mismatch")
    status = clean_identifier(data.get("official_group_02_result_recording_status"), default="", max_length=80)
    if status not in P7_HOLD004_GROUP02_ALLOWED_RESULT_RECORDING_STATUSES:
        raise ValueError("P7-HOLD-004 R40 result recording status mismatch")
    if data.get("result_status") != status:
        raise ValueError("P7-HOLD-004 R40 result_status alias mismatch")
    group_green = status == P7_HOLD004_GROUP02_RESULT_STATUS_PASSED_ISOLATED
    recordable = status != P7_HOLD004_GROUP02_RESULT_STATUS_NOT_RUN
    if data.get("official_group_02_capture_result_recorded") is not recordable:
        raise ValueError("P7-HOLD-004 R40 recorded flag mismatch")
    if data.get("official_group_02_official_full_run_executed") is not recordable:
        raise ValueError("P7-HOLD-004 R40 executed flag mismatch")
    if data.get("official_capture_material_recordable") is not recordable:
        raise ValueError("P7-HOLD-004 R40 recordable flag mismatch")
    if data.get("official_group_02_capture_green_confirmed") is not group_green:
        raise ValueError("P7-HOLD-004 R40 group green flag mismatch")
    if data.get("can_claim_group_green") is not group_green:
        raise ValueError("P7-HOLD-004 R40 group green claim mismatch")
    for key in (
        "can_claim_full_backend_suite_green",
        "full_backend_suite_green_confirmed",
        "full_backend_suite_green_claim_allowed",
        "hold004_close_allowed",
        "p7_complete",
        "p7_complete_claim_allowed",
        "p8_start_allowed",
        "release_allowed",
        "split_green_is_full_backend_suite_green",
        "split_green_can_close_p7_hold004",
        "all_backend_groups_officially_executed",
        "all_backend_groups_green",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 R40 must keep {key}=false")
    for key in (
        "group02_result_recording_is_not_full_backend_suite_gate",
        "group02_result_recording_is_not_release_ready",
        "full_backend_suite_gate_required",
        "full_backend_suite_green_requires_all_backend_groups",
        "body_free_result_recorded",
        "collect_only_is_not_execution_green",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 R40 must keep {key}=true")
    if group_green:
        if data.get("group02_green_is_not_full_backend_suite_green") is not True:
            raise ValueError("P7-HOLD-004 R40 group green must remain isolated from full suite green")
        if data.get("group02_pass_is_not_full_backend_suite_green") is not True:
            raise ValueError("P7-HOLD-004 R40 pass must remain isolated from full suite green")
    if status != P7_HOLD004_GROUP02_RESULT_STATUS_TIMEOUT_ISOLATED:
        if data.get("timeout_classification_required") is not False or data.get("long_run_probe_required") is not False:
            raise ValueError("P7-HOLD-004 R40 non-timeout result must not require timeout probe")
    else:
        if data.get("timeout_classification_required") is not True or data.get("long_run_probe_required") is not True:
            raise ValueError("P7-HOLD-004 R40 timeout result must require long-run probe")
    if data.get("timeout_is_green") is not False or data.get("timeout_is_immediate_fail") is not False:
        raise ValueError("P7-HOLD-004 R40 timeout flags must remain non-green and non-immediate-fail")
    recorded = dedupe_identifiers(data.get("recorded_backend_group_ids"), limit=40, max_length=120)
    remaining = dedupe_identifiers(data.get("remaining_backend_group_ids"), limit=40, max_length=120)
    if recordable and recorded != [P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID]:
        raise ValueError("P7-HOLD-004 R40 must record only group_02")
    if not recordable and recorded:
        raise ValueError("P7-HOLD-004 R40 NOT_RUN must not record group ids")
    if recordable and P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID in remaining:
        raise ValueError("P7-HOLD-004 R40 remaining groups must not include recorded group_02")
    if not recordable and P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID not in remaining:
        raise ValueError("P7-HOLD-004 R40 NOT_RUN must keep group_02 pending")
    if data.get("remaining_backend_group_count") != len(remaining):
        raise ValueError("P7-HOLD-004 R40 remaining group count mismatch")
    if recordable and len(remaining) != len(P7_HOLD004_BACKEND_SUITE_GROUP_IDS) - 1:
        raise ValueError("P7-HOLD-004 R40 must keep non-group_02 backend groups pending after recordable result")
    if not recordable and len(remaining) != len(P7_HOLD004_BACKEND_SUITE_GROUP_IDS):
        raise ValueError("P7-HOLD-004 R40 NOT_RUN must keep all backend groups pending")
    if P7_HOLD004_BACKEND_SUITE_HOLD_ID not in set(dedupe_identifiers(data.get("unresolved_hold_refs"), limit=80, max_length=120)):
        raise ValueError("P7-HOLD-004 R40 must keep HOLD-004 unresolved")
    followups = set(dedupe_identifiers(data.get("required_followup_fixes"), limit=120, max_length=180))
    if "full_backend_suite_green_unconfirmed" not in followups:
        raise ValueError("P7-HOLD-004 R40 must keep full backend suite followup")
    if "remaining_backend_groups_official_execution_required" not in followups:
        raise ValueError("P7-HOLD-004 R40 must require remaining backend group executions")
    projection = safe_mapping(data.get("run_result_projection"))
    if projection.get("group_id") not in {"", P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID}:
        raise ValueError("P7-HOLD-004 R40 run result projection group mismatch")
    if projection.get("body_free") is not True:
        raise ValueError("P7-HOLD-004 R40 result projection must be body_free")
    decision = safe_mapping(data.get("adoption_decision_projection"))
    if decision.get("can_claim_full_backend_suite_green") is not False:
        raise ValueError("P7-HOLD-004 R40 decision projection must not claim full suite green")
    _r40_release_body_free_contract(data, source=source)
    return True


def build_p7_hold004_full_backend_suite_gate(
    *,
    official_group02_result_recording: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build R40 full backend-suite gate after group_02 result recording."""

    recording = (
        safe_mapping(official_group02_result_recording)
        if official_group02_result_recording is not None
        else build_p7_hold004_official_group02_result_recording()
    )
    assert_p7_hold004_official_group02_result_recording_contract(recording)
    remaining_group_ids = dedupe_identifiers(recording.get("remaining_backend_group_ids"), limit=40, max_length=120)
    material = {
        "schema_version": P7_HOLD004_FULL_BACKEND_SUITE_GATE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "step": P7_HOLD004_FULL_BACKEND_SUITE_GATE_STEP,
        "implementation_step": P7_HOLD004_FULL_BACKEND_SUITE_GATE_STEP,
        "gate_id": P7_HOLD004_FULL_BACKEND_SUITE_GATE_ID,
        "source_mode": P7_SOURCE_MODE,
        "git_checked": P7_GIT_CHECKED,
        "official_group02_result_recording_schema_version": P7_HOLD004_OFFICIAL_GROUP02_RESULT_RECORDING_SCHEMA_VERSION,
        "official_group02_result_recording_id": P7_HOLD004_OFFICIAL_GROUP02_RESULT_RECORDING_ID,
        "official_group_02_result_recording_status": recording.get("official_group_02_result_recording_status"),
        "official_group_02_capture_result_recorded": recording.get("official_group_02_capture_result_recorded") is True,
        "official_group_02_capture_green_confirmed": recording.get("official_group_02_capture_green_confirmed") is True,
        "can_claim_group_green": recording.get("can_claim_group_green") is True,
        "full_backend_suite_gate_status": P7_HOLD004_FULL_BACKEND_SUITE_GATE_STATUS_BLOCKED_REMAINING_GROUPS,
        "full_backend_suite_gate_satisfied": False,
        "full_backend_suite_green_confirmed": False,
        "can_claim_full_backend_suite_green": False,
        "full_backend_suite_green_claim_allowed": False,
        "hold004_close_allowed": False,
        "p7_complete": False,
        "p7_complete_claim_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "split_green_is_full_backend_suite_green": False,
        "split_green_can_close_p7_hold004": False,
        "all_backend_groups_officially_executed": False,
        "all_backend_groups_green": False,
        "no_backend_group_failed_timeout_not_run_or_partial": False,
        "group02_green_is_not_full_backend_suite_green": recording.get("official_group_02_capture_green_confirmed") is True,
        "group02_result_recording_is_not_full_backend_suite_gate": True,
        "group02_result_recording_is_not_release_ready": True,
        "remaining_backend_group_ids": remaining_group_ids,
        "remaining_backend_group_count": len(remaining_group_ids),
        "full_backend_suite_required_conditions": {
            "group02_result_recorded": recording.get("official_group_02_capture_result_recorded") is True,
            "collect_baseline_id_matches_post_adoption_active_baseline": recording.get("current_active_baseline_id") == P7_HOLD004_BACKEND_COLLECT_BASELINE_ID,
            "matrix_release_validation_current": True,
            "body_free_result_material_contract_passed": True,
            "all_backend_groups_officially_executed": False,
            "all_backend_groups_passed": False,
            "no_timeout_failed_not_run_partial": False,
            "full_backend_suite_green_confirmed": False,
        },
        "unresolved_hold_refs": ["P7-HOLD-001", "P7-HOLD-003", P7_HOLD004_BACKEND_SUITE_HOLD_ID],
        "required_followup_fixes": dedupe_identifiers(
            [
                "full_backend_suite_green_unconfirmed",
                "remaining_backend_groups_official_execution_required",
                "p7_hold004_closure_blocked_until_all_backend_groups_green",
                "p5_human_qa_review_required",
                "real_device_submit_modal_readfeel_unverified",
            ],
            limit=120,
            max_length=180,
        ),
        "public_contract": _public_contract_boundary_flags(),
        "body_free_markers": _body_free_markers(),
        **_body_retention_flags(),
        "raw_input_retained": False,
        "comment_text_retained": False,
        "candidate_body_retained": False,
        "surface_body_retained": False,
        "body_free": True,
    }
    assert_p7_hold004_full_backend_suite_gate_contract(material)
    return material


def assert_p7_hold004_full_backend_suite_gate_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    source = "p7_hold004_r40_full_backend_suite_gate"
    if data.get("schema_version") != P7_HOLD004_FULL_BACKEND_SUITE_GATE_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 R40 full suite gate schema mismatch")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError("P7-HOLD-004 R40 full suite gate phase/hold mismatch")
    if data.get("step") != P7_HOLD004_FULL_BACKEND_SUITE_GATE_STEP:
        raise ValueError("P7-HOLD-004 R40 full suite gate step mismatch")
    if data.get("gate_id") != P7_HOLD004_FULL_BACKEND_SUITE_GATE_ID:
        raise ValueError("P7-HOLD-004 R40 full suite gate id mismatch")
    if data.get("official_group02_result_recording_schema_version") != P7_HOLD004_OFFICIAL_GROUP02_RESULT_RECORDING_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 R40 full suite gate result schema mismatch")
    if data.get("full_backend_suite_gate_status") != P7_HOLD004_FULL_BACKEND_SUITE_GATE_STATUS_BLOCKED_REMAINING_GROUPS:
        raise ValueError("P7-HOLD-004 R40 full suite gate status mismatch")
    for key in (
        "full_backend_suite_gate_satisfied",
        "full_backend_suite_green_confirmed",
        "can_claim_full_backend_suite_green",
        "full_backend_suite_green_claim_allowed",
        "hold004_close_allowed",
        "p7_complete",
        "p7_complete_claim_allowed",
        "p8_start_allowed",
        "release_allowed",
        "split_green_is_full_backend_suite_green",
        "split_green_can_close_p7_hold004",
        "all_backend_groups_officially_executed",
        "all_backend_groups_green",
        "no_backend_group_failed_timeout_not_run_or_partial",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 R40 full suite gate must keep {key}=false")
    for key in (
        "group02_result_recording_is_not_full_backend_suite_gate",
        "group02_result_recording_is_not_release_ready",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 R40 full suite gate must keep {key}=true")
    remaining = dedupe_identifiers(data.get("remaining_backend_group_ids"), limit=40, max_length=120)
    group02_recorded = data.get("official_group_02_capture_result_recorded") is True
    if group02_recorded and P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID in remaining:
        raise ValueError("P7-HOLD-004 R40 full suite remaining groups must not include recorded group_02")
    if not group02_recorded and P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID not in remaining:
        raise ValueError("P7-HOLD-004 R40 full suite NOT_RUN must keep group_02 pending")
    if data.get("remaining_backend_group_count") != len(remaining):
        raise ValueError("P7-HOLD-004 R40 full suite remaining count mismatch")
    expected_remaining_count = len(P7_HOLD004_BACKEND_SUITE_GROUP_IDS) - 1 if group02_recorded else len(P7_HOLD004_BACKEND_SUITE_GROUP_IDS)
    if len(remaining) != expected_remaining_count:
        raise ValueError("P7-HOLD-004 R40 full suite remaining group count mismatch for result state")
    conditions = safe_mapping(data.get("full_backend_suite_required_conditions"))
    if conditions.get("group02_result_recorded") is not (data.get("official_group_02_capture_result_recorded") is True):
        raise ValueError("P7-HOLD-004 R40 full suite group02 recorded condition mismatch")
    for key in (
        "collect_baseline_id_matches_post_adoption_active_baseline",
        "matrix_release_validation_current",
        "body_free_result_material_contract_passed",
    ):
        if conditions.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 R40 full suite condition {key} must be true")
    for key in (
        "all_backend_groups_officially_executed",
        "all_backend_groups_passed",
        "no_timeout_failed_not_run_partial",
        "full_backend_suite_green_confirmed",
    ):
        if conditions.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 R40 full suite condition {key} must be false")
    if P7_HOLD004_BACKEND_SUITE_HOLD_ID not in set(dedupe_identifiers(data.get("unresolved_hold_refs"), limit=80, max_length=120)):
        raise ValueError("P7-HOLD-004 R40 full suite gate must keep HOLD-004 unresolved")
    followups = set(dedupe_identifiers(data.get("required_followup_fixes"), limit=120, max_length=180))
    if "full_backend_suite_green_unconfirmed" not in followups:
        raise ValueError("P7-HOLD-004 R40 full suite gate must keep full suite followup")
    if "remaining_backend_groups_official_execution_required" not in followups:
        raise ValueError("P7-HOLD-004 R40 full suite gate must require remaining backend groups")
    _r40_release_body_free_contract(data, source=source)
    return True


__all__ = [
    "P7_HOLD004_ACTIVE_BASELINE_REFRESH_ID",
    "P7_HOLD004_POST_ADOPTION_ACTIVE_BASELINE_SCHEMA_VERSION",
    "P7_HOLD004_POST_ADOPTION_ACTIVE_BASELINE_STEP",
    "P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_ID",
    "P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_SCHEMA_VERSION",
    "P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_STEP",
    "P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_ID",
    "P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_SCHEMA_VERSION",
    "P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_STEP",
    "P7_HOLD004_RUNTIME_REFRESH_STATUS_APPLIED",
    "P7_HOLD004_MATRIX_RELEASE_VALIDATION_CONNECTION_REFRESH_ID",
    "P7_HOLD004_MATRIX_RELEASE_VALIDATION_CONNECTION_REFRESH_SCHEMA_VERSION",
    "P7_HOLD004_MATRIX_RELEASE_VALIDATION_CONNECTION_REFRESH_STEP",
    "P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_REEVALUATION_ID",
    "P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_REEVALUATION_STEP",
    "P7_HOLD004_OFFICIAL_GROUP02_RESULT_RECORDING_SCHEMA_VERSION",
    "P7_HOLD004_OFFICIAL_GROUP02_RESULT_RECORDING_STEP",
    "P7_HOLD004_OFFICIAL_GROUP02_RESULT_RECORDING_ID",
    "P7_HOLD004_FULL_BACKEND_SUITE_GATE_SCHEMA_VERSION",
    "P7_HOLD004_FULL_BACKEND_SUITE_GATE_STEP",
    "P7_HOLD004_FULL_BACKEND_SUITE_GATE_ID",
    "P7_HOLD004_GROUP02_RESULT_STATUS_NOT_RUN",
    "P7_HOLD004_GROUP02_RESULT_STATUS_PASSED_ISOLATED",
    "P7_HOLD004_GROUP02_RESULT_STATUS_FAILED_ISOLATED",
    "P7_HOLD004_GROUP02_RESULT_STATUS_TIMEOUT_ISOLATED",
    "P7_HOLD004_GROUP02_RESULT_STATUS_PARTIAL_OR_INTERRUPTED",
    "P7_HOLD004_FULL_BACKEND_SUITE_GATE_STATUS_BLOCKED_REMAINING_GROUPS",
    "assert_p7_hold004_post_adoption_active_baseline_material_contract",
    "assert_p7_hold004_post_adoption_received_snapshot_reconcile_contract",
    "assert_p7_hold004_runtime_builder_refresh_status_contract",
    "assert_p7_hold004_matrix_release_validation_connection_refresh_contract",
    "assert_p7_hold004_official_group02_capture_readiness_re_evaluation_contract",
    "assert_p7_hold004_official_group02_result_recording_contract",
    "assert_p7_hold004_full_backend_suite_gate_contract",
    "build_p7_hold004_post_adoption_active_baseline_material",
    "build_p7_hold004_post_adoption_received_snapshot_reconcile",
    "build_p7_hold004_runtime_builder_refresh_status",
    "build_p7_hold004_matrix_release_validation_connection_refresh",
    "build_p7_hold004_official_group02_capture_readiness_re_evaluation",
    "build_p7_hold004_official_group02_result_recording",
    "build_p7_hold004_full_backend_suite_gate",
]
