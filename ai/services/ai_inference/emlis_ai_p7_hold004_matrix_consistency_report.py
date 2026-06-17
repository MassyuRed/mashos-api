# -*- coding: utf-8 -*-
"""P7-HOLD-004 current-snapshot R18 matrix-consistency report material.

R18 compares the same body-free observed materials across the backend suite
split matrix, R10 HOLD matrix, release handoff, and validation matrix.  The
report is deliberately a comparison material only: a PASS report means the
matrices agree about RED/HOLD/release-false boundaries, not that P7-HOLD-004 is
closed, not that full backend-suite green is confirmed, and not that release is
allowed.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final

from emlis_ai_p7_contracts import (
    P7_INITIAL_HOLD_IDS,
    P7_PHASE,
    assert_false_markers,
    assert_p7_no_body_payload_or_contract_mutation,
    body_free_flags,
    clean_identifier,
    dedupe_identifiers,
    public_contract_flags,
    safe_mapping,
)
from emlis_ai_p7_hold004_backend_suite_execution_results import (
    P7_HOLD004_ACTIVE_BASELINE_REFRESH_ID,
    P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_SCHEMA_VERSION,
    P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_ALLOWED_SCHEMA_VERSIONS,
    P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION,
    P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION_V2,
    P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_ITEM_FINGERPRINT_MISMATCH,
    P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY,
    P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_ID,
    P7_HOLD004_RECEIVED_SNAPSHOT_ITEM_FINGERPRINT_MISMATCH_BLOCKER_REF,
    P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_ID,
    P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_SCHEMA_VERSION,
    assert_p7_hold004_backend_suite_execution_summary_contract,
    build_p7_hold004_current_backend_suite_execution_summary,
)
from emlis_ai_p7_hold004_backend_suite_group_inventory_plan import (
    P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID,
    P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID,
)
from emlis_ai_p7_hold004_backend_suite_split_consistency import (
    P7_HOLD004_BACKEND_COLLECT_BASELINE_ID,
    P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT,
    P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT,
)
from emlis_ai_p7_hold_matrix import (
    P7_BACKEND_SUITE_SPLIT_MATRIX_SCHEMA_VERSION,
    P7_R10_HOLD_MATRIX_SCHEMA_VERSION,
    assert_p7_backend_suite_split_matrix_contract,
    assert_p7_r10_hold_matrix_contract,
    build_p7_backend_suite_split_matrix,
    build_p7_r10_hold_matrix,
)
from emlis_ai_p7_red_closure_classification import (
    P7_RED_CLOSURE_CLASSIFICATION_MATRIX_SCHEMA_VERSION,
    assert_p7_red_closure_classification_matrix_contract,
    build_p7_red_closure_classification_matrix,
)
from emlis_ai_p7_release_handoff import (
    P7_RELEASE_HANDOFF_SCHEMA_VERSION,
    assert_p7_release_decision_handoff_contract,
    build_p7_release_decision_handoff,
)
from emlis_ai_p7_timeout_isolation import P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID
from emlis_ai_p7_validation_matrix import (
    P7_HOLD004_MATRIX_CONSISTENCY_REPORT_SCHEMA_VERSION,
    P7_VALIDATION_MATRIX_SCHEMA_VERSION,
    assert_p7_validation_regression_matrix_contract,
    build_p7_validation_regression_matrix,
)

P7_HOLD004_MATRIX_CONSISTENCY_REPORT_STEP: Final = (
    "P7-HOLD-004_CurrentSnapshotBaselineReconcile_R18_20260615"
)
P7_HOLD004_MATRIX_CONSISTENCY_REPORT_ID: Final = (
    "p7_hold004_matrix_consistency_report_20260615_current_snapshot"
)
P7_HOLD004_MATRIX_CONSISTENCY_HOLD_ID: Final = "P7-HOLD-004"
P7_HOLD004_MATRIX_CONSISTENCY_SOURCE_SNAPSHOT_REF: Final = "mashos-api(148).zip"
P7_HOLD004_PREVIOUS_BACKEND_COLLECT_BASELINE_ID: Final = "p7_hold004_backend_collect_baseline_20260614"

P7_HOLD004_MATRIX_CONSISTENCY_STATUS_PASS: Final = "PASS"
P7_HOLD004_MATRIX_CONSISTENCY_STATUS_REVIEW_REQUIRED: Final = "REVIEW_REQUIRED"
P7_HOLD004_MATRIX_CONSISTENCY_STATUS_BLOCKED: Final = "BLOCKED"
P7_HOLD004_MATRIX_CONSISTENCY_STATUS_NOT_RUN: Final = "NOT_RUN"
P7_HOLD004_MATRIX_CONSISTENCY_ALLOWED_STATUSES: Final[frozenset[str]] = frozenset(
    {
        P7_HOLD004_MATRIX_CONSISTENCY_STATUS_PASS,
        P7_HOLD004_MATRIX_CONSISTENCY_STATUS_REVIEW_REQUIRED,
        P7_HOLD004_MATRIX_CONSISTENCY_STATUS_BLOCKED,
        P7_HOLD004_MATRIX_CONSISTENCY_STATUS_NOT_RUN,
    }
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
    "split_green_promoted_to_full_suite_green",
)
_REQUIRED_PASS_CHECKS: Final[tuple[str, ...]] = (
    "red003_closure_consistent",
    "step5_red_consistent",
    "hold004_preserved_across_matrices",
    "current_collect_baseline_connected",
    "current_group_inventory_connected",
    "current_execution_plan_connected",
    "old_baseline_not_used_as_current",
    "backend_suite_group_02_count_current",
    "full_backend_suite_green_false_across_matrices",
    "split_green_not_promoted",
    "release_allowed_false_across_matrices",
    "p8_start_allowed_false_across_matrices",
    "body_free_markers_false_across_matrices",
    "received_snapshot_blocking_status_consistent",
    "received_snapshot_item_fingerprint_mismatch_resolved",
    "active_baseline_refresh_projection_consistent",
)


def _release_closed_boundary() -> dict[str, bool]:
    return {key: False for key in _RELEASE_CLOSED_KEYS}


def _bool_field(material: Mapping[str, Any], key: str) -> bool:
    return safe_mapping(material).get(key) is True


def _field_false_or_missing(material: Mapping[str, Any], key: str) -> bool:
    return safe_mapping(material).get(key) is not True


def _summary_field(material: Mapping[str, Any], key: str) -> Any:
    data = safe_mapping(material)
    if key in data:
        return data.get(key)
    return safe_mapping(data.get("summary")).get(key)


def _refs(material: Mapping[str, Any], key: str) -> list[str]:
    return dedupe_identifiers(safe_mapping(material).get(key), limit=160, max_length=160)


def _red_ref_state(material: Mapping[str, Any], red_id: str) -> tuple[bool, bool]:
    closed = red_id in set(_refs(material, "closed_red_refs"))
    unresolved = red_id in set(_refs(material, "unresolved_red_refs"))
    return closed, unresolved


def _red003_closure_consistent(materials: Mapping[str, Mapping[str, Any]]) -> bool:
    states = [_red_ref_state(material, P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID) for material in materials.values()]
    closed_states = [state[0] for state in states]
    unresolved_states = [state[1] for state in states]
    if len(set(closed_states)) != 1 or len(set(unresolved_states)) != 1:
        return False
    # P7-RED-003 must be exactly one of closed/unresolved across all matrices.
    return closed_states[0] != unresolved_states[0]


def _step5_state(material: Mapping[str, Any]) -> tuple[bool, bool, bool, bool]:
    step5_red_id = "P7-RED-HOLD004-STEP5-CANDIDATE-GATE-DISPLAY-BINDING"
    present = _summary_field(material, "hold004_step5_display_binding_red_present") is True
    closed = _summary_field(material, "hold004_step5_candidate_gate_red_closed") is True
    unresolved_ref = step5_red_id in set(_refs(material, "hold004_step5_unresolved_red_refs")) or step5_red_id in set(
        _refs(material, "unresolved_red_refs")
    )
    closed_ref = step5_red_id in set(_refs(material, "hold004_step5_closed_red_refs")) or step5_red_id in set(
        _refs(material, "closed_red_refs")
    )
    return present, closed, unresolved_ref, closed_ref


def _step5_red_consistent(materials: Mapping[str, Mapping[str, Any]]) -> bool:
    states = [_step5_state(material) for material in materials.values()]
    if not any(any(state) for state in states):
        return True
    return len(set(states)) == 1


def _hold004_preserved(materials: Mapping[str, Mapping[str, Any]]) -> bool:
    return all(P7_HOLD004_MATRIX_CONSISTENCY_HOLD_ID in set(_refs(material, "unresolved_hold_refs")) for material in materials.values())


def _full_backend_suite_green_false(materials: Mapping[str, Mapping[str, Any]]) -> bool:
    return all(_field_false_or_missing(material, "full_backend_suite_green_confirmed") for material in materials.values())


def _split_green_not_promoted(materials: Mapping[str, Mapping[str, Any]]) -> bool:
    promotion_keys = (
        "split_green_is_full_backend_suite_green",
        "split_green_can_close_p7_hold004",
        "split_green_promoted_to_full_suite_green",
    )
    return all(_field_false_or_missing(material, key) for material in materials.values() for key in promotion_keys)


def _release_allowed_false(materials: Mapping[str, Mapping[str, Any]]) -> bool:
    return all(_field_false_or_missing(material, "release_allowed") for material in materials.values())


def _p8_start_allowed_false(materials: Mapping[str, Mapping[str, Any]]) -> bool:
    return all(_field_false_or_missing(material, "p8_start_allowed") for material in materials.values())


def _body_free_markers_false(materials: Mapping[str, Mapping[str, Any]]) -> bool:
    for name, raw_material in materials.items():
        material = safe_mapping(raw_material)
        if material.get("body_free") is not True:
            return False
        try:
            assert_false_markers(safe_mapping(material.get("public_contract")), source=f"{name}.public_contract")
        except ValueError:
            return False
        if material.get("body_free_markers") is not None:
            try:
                assert_false_markers(safe_mapping(material.get("body_free_markers")), source=f"{name}.body_free_markers")
            except ValueError:
                return False
        try:
            assert_p7_no_body_payload_or_contract_mutation(material, source=f"{name}.material")
        except ValueError:
            return False
    return True


def _current_bool_true_across_matrices(materials: Mapping[str, Mapping[str, Any]], key: str) -> bool:
    return all(safe_mapping(material).get(key) is True for material in materials.values())


def _current_collect_baseline_connected(materials: Mapping[str, Mapping[str, Any]]) -> bool:
    return _current_bool_true_across_matrices(materials, "current_collect_baseline_connected")


def _current_group_inventory_connected(materials: Mapping[str, Mapping[str, Any]]) -> bool:
    return _current_bool_true_across_matrices(materials, "current_group_inventory_connected")


def _current_execution_plan_connected(materials: Mapping[str, Mapping[str, Any]]) -> bool:
    return _current_bool_true_across_matrices(materials, "current_execution_plan_connected")


def _old_baseline_not_used_as_current(materials: Mapping[str, Mapping[str, Any]]) -> bool:
    return all(
        safe_mapping(material).get("old_baseline_not_used_as_current") is True
        and safe_mapping(safe_mapping(material).get("matrix_current_baseline_connection")).get("old_baseline_used_as_current") is not True
        for material in materials.values()
    )


def _backend_suite_group_02_count_current(materials: Mapping[str, Mapping[str, Any]]) -> bool:
    return _current_bool_true_across_matrices(materials, "backend_suite_group_02_count_current")


_RECEIVED_SNAPSHOT_CONNECTION_MATERIAL_NAMES: Final[tuple[str, ...]] = (
    "backend_suite_split_matrix",
    "r10_hold_matrix",
    "release_handoff",
    "validation_matrix",
)


def _received_snapshot_connection_materials(
    materials: Mapping[str, Mapping[str, Any]],
) -> dict[str, Mapping[str, Any]]:
    return {
        name: safe_mapping(materials.get(name))
        for name in _RECEIVED_SNAPSHOT_CONNECTION_MATERIAL_NAMES
        if isinstance(materials.get(name), Mapping)
    }


def _received_snapshot_blocking_status_consistent(materials: Mapping[str, Mapping[str, Any]]) -> bool:
    connection_materials = _received_snapshot_connection_materials(materials)
    if set(connection_materials) != set(_RECEIVED_SNAPSHOT_CONNECTION_MATERIAL_NAMES):
        return False
    statuses = {
        clean_identifier(
            _summary_field(material, "official_group_02_capture_readiness_status"),
            default="",
            max_length=160,
        )
        for material in connection_materials.values()
    }
    capture_blocked_flags = {
        _summary_field(material, "official_group_02_capture_blocked") is True
        for material in connection_materials.values()
    }
    run_allowed_flags = {
        _summary_field(material, "official_group_02_capture_run_allowed") is True
        for material in connection_materials.values()
    }
    recording_allowed_flags = {
        _summary_field(material, "official_group_02_capture_result_recording_allowed") is True
        for material in connection_materials.values()
    }
    mismatch_flags = {
        _summary_field(material, "received_snapshot_item_fingerprint_mismatch_unresolved") is True
        for material in connection_materials.values()
    }
    blocked_state_consistent = (
        statuses == {P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_ITEM_FINGERPRINT_MISMATCH}
        and capture_blocked_flags == {True}
        and run_allowed_flags == {False}
        and recording_allowed_flags == {False}
        and mismatch_flags == {True}
    )
    post_adoption_ready_state_consistent = (
        statuses == {P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY}
        and capture_blocked_flags == {False}
        and run_allowed_flags == {True}
        and recording_allowed_flags == {True}
        and mismatch_flags == {False}
    )
    return blocked_state_consistent or post_adoption_ready_state_consistent


def _active_baseline_refresh_projection_consistent(materials: Mapping[str, Mapping[str, Any]]) -> bool:
    connection_materials = _received_snapshot_connection_materials(materials)
    if set(connection_materials) != set(_RECEIVED_SNAPSHOT_CONNECTION_MATERIAL_NAMES):
        return False
    schema_versions = {
        clean_identifier(_summary_field(material, "active_baseline_refresh_schema_version"), default="", max_length=160)
        for material in connection_materials.values()
    }
    refresh_ids = {
        clean_identifier(_summary_field(material, "active_baseline_refresh_id"), default="", max_length=180)
        for material in connection_materials.values()
    }
    runtime_status_ids = {
        clean_identifier(_summary_field(material, "runtime_builder_refresh_status_id"), default="", max_length=180)
        for material in connection_materials.values()
    }
    reconcile_ids = {
        clean_identifier(_summary_field(material, "post_adoption_received_snapshot_reconcile_id"), default="", max_length=180)
        for material in connection_materials.values()
    }
    applied_flags = {
        _summary_field(material, "active_baseline_update_applied_to_runtime_builders") is True
        for material in connection_materials.values()
    }
    source_refresh_flags = {
        _summary_field(material, "source_snapshot_ref_updated_in_active_builders") is True
        for material in connection_materials.values()
    }
    if schema_versions == {""} and refresh_ids == {""} and runtime_status_ids == {""} and reconcile_ids == {""}:
        return applied_flags == {False} and source_refresh_flags == {False}
    return (
        schema_versions == {P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_SCHEMA_VERSION}
        and refresh_ids == {P7_HOLD004_ACTIVE_BASELINE_REFRESH_ID}
        and runtime_status_ids == {P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_ID}
        and reconcile_ids == {P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_ID}
        and applied_flags == {True}
        and source_refresh_flags == {True}
    )

def _received_snapshot_item_fingerprint_mismatch_resolved(materials: Mapping[str, Mapping[str, Any]]) -> bool:
    connection_materials = _received_snapshot_connection_materials(materials)
    if set(connection_materials) != set(_RECEIVED_SNAPSHOT_CONNECTION_MATERIAL_NAMES):
        return False
    return all(
        _summary_field(material, "received_snapshot_item_fingerprint_mismatch_unresolved") is not True
        for material in connection_materials.values()
    )


def _first_received_snapshot_field(materials: Mapping[str, Mapping[str, Any]], key: str) -> Any:
    for material in _received_snapshot_connection_materials(materials).values():
        value = _summary_field(material, key)
        if value is not None:
            return value
    return None


def _matrix_current_baseline_connection_from_sources(
    *,
    execution_summary: Mapping[str, Any],
    backend_split: Mapping[str, Any],
    r10_matrix: Mapping[str, Any],
    handoff: Mapping[str, Any],
    validation: Mapping[str, Any],
) -> dict[str, Any]:
    for material in (backend_split, r10_matrix, handoff, validation):
        connection = safe_mapping(safe_mapping(material).get("matrix_current_baseline_connection"))
        if connection.get("collect_baseline_id"):
            return dict(connection)
    return {
        "collect_baseline_id": clean_identifier(execution_summary.get("collect_baseline_id"), max_length=160),
        "group_inventory_id": clean_identifier(execution_summary.get("inventory_id"), max_length=160),
        "execution_plan_id": clean_identifier(execution_summary.get("plan_id"), max_length=160),
        "execution_summary_id": clean_identifier(execution_summary.get("summary_id"), max_length=160),
        "current_collect_file_count": P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT,
        "current_collect_test_item_count": P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT,
        "group_02_file_count": int(backend_split.get("backend_suite_group_02_file_count", 0) or 0),
        "group_02_test_item_count": int(backend_split.get("backend_suite_group_02_test_item_count", 0) or 0),
        "old_baseline_id": P7_HOLD004_PREVIOUS_BACKEND_COLLECT_BASELINE_ID,
        "old_baseline_used_as_current": False,
        "full_backend_suite_green_confirmed": False,
        "release_allowed": False,
        "body_free": True,
    }


def _source_materials_for_consistency(
    *,
    backend_suite_execution_summary: Mapping[str, Any] | None = None,
    red_closure_classification_matrix: Mapping[str, Any] | None = None,
    backend_suite_split_matrix: Mapping[str, Any] | None = None,
    r10_hold_matrix: Mapping[str, Any] | None = None,
    release_handoff: Mapping[str, Any] | None = None,
    validation_matrix: Mapping[str, Any] | None = None,
) -> dict[str, Mapping[str, Any]]:
    execution_summary = (
        safe_mapping(backend_suite_execution_summary)
        if backend_suite_execution_summary is not None
        else build_p7_hold004_current_backend_suite_execution_summary()
    )
    assert_p7_hold004_backend_suite_execution_summary_contract(execution_summary)

    red_closure = (
        safe_mapping(red_closure_classification_matrix)
        if red_closure_classification_matrix is not None
        else build_p7_red_closure_classification_matrix()
    )
    assert_p7_red_closure_classification_matrix_contract(red_closure)

    backend_split = (
        safe_mapping(backend_suite_split_matrix)
        if backend_suite_split_matrix is not None
        else build_p7_backend_suite_split_matrix(
            backend_suite_execution_summary=execution_summary,
            red_closure_classification_matrix=red_closure,
        )
    )
    assert_p7_backend_suite_split_matrix_contract(backend_split)

    r10_matrix = (
        safe_mapping(r10_hold_matrix)
        if r10_hold_matrix is not None
        else build_p7_r10_hold_matrix(backend_suite_split_matrix=backend_split)
    )
    assert_p7_r10_hold_matrix_contract(r10_matrix)

    handoff = (
        safe_mapping(release_handoff)
        if release_handoff is not None
        else build_p7_release_decision_handoff(
            backend_suite_execution_summary=execution_summary,
            red_closure_classification_matrix=red_closure,
            backend_suite_split_matrix=backend_split,
            r10_hold_matrix=r10_matrix,
        )
    )
    assert_p7_release_decision_handoff_contract(handoff)

    validation = (
        safe_mapping(validation_matrix)
        if validation_matrix is not None
        else build_p7_validation_regression_matrix(
            backend_suite_execution_summary=execution_summary,
            red_closure_classification_matrix=red_closure,
            backend_suite_split_matrix=backend_split,
            r10_hold_matrix=r10_matrix,
            release_handoff=handoff,
        )
    )
    assert_p7_validation_regression_matrix_contract(validation)

    return {
        "backend_suite_execution_summary": execution_summary,
        "red_closure_classification_matrix": red_closure,
        "backend_suite_split_matrix": backend_split,
        "r10_hold_matrix": r10_matrix,
        "release_handoff": handoff,
        "validation_matrix": validation,
    }


def _determine_consistency_status(*, checks: Mapping[str, bool], source_materials: Mapping[str, Mapping[str, Any]]) -> str:
    if not source_materials:
        return P7_HOLD004_MATRIX_CONSISTENCY_STATUS_NOT_RUN
    if not (
        checks.get("release_allowed_false_across_matrices")
        and checks.get("p8_start_allowed_false_across_matrices")
        and checks.get("full_backend_suite_green_false_across_matrices")
        and checks.get("split_green_not_promoted")
        and checks.get("body_free_markers_false_across_matrices")
    ):
        return P7_HOLD004_MATRIX_CONSISTENCY_STATUS_BLOCKED
    if all(checks.get(key) is True for key in _REQUIRED_PASS_CHECKS):
        return P7_HOLD004_MATRIX_CONSISTENCY_STATUS_PASS
    return P7_HOLD004_MATRIX_CONSISTENCY_STATUS_REVIEW_REQUIRED


def build_p7_hold004_matrix_consistency_report(
    *,
    backend_suite_execution_summary: Mapping[str, Any] | None = None,
    red_closure_classification_matrix: Mapping[str, Any] | None = None,
    backend_suite_split_matrix: Mapping[str, Any] | None = None,
    r10_hold_matrix: Mapping[str, Any] | None = None,
    release_handoff: Mapping[str, Any] | None = None,
    validation_matrix: Mapping[str, Any] | None = None,
    report_id: Any = P7_HOLD004_MATRIX_CONSISTENCY_REPORT_ID,
) -> dict[str, Any]:
    """Build the body-free R10 report comparing P7 matrix readings."""

    source_materials = _source_materials_for_consistency(
        backend_suite_execution_summary=backend_suite_execution_summary,
        red_closure_classification_matrix=red_closure_classification_matrix,
        backend_suite_split_matrix=backend_suite_split_matrix,
        r10_hold_matrix=r10_hold_matrix,
        release_handoff=release_handoff,
        validation_matrix=validation_matrix,
    )
    comparison_materials = {
        key: source_materials[key]
        for key in (
            "backend_suite_split_matrix",
            "r10_hold_matrix",
            "release_handoff",
            "validation_matrix",
        )
    }
    red_comparison_materials = {
        "red_closure_classification_matrix": source_materials["red_closure_classification_matrix"],
        **comparison_materials,
    }
    checks = {
        "red003_closure_consistent": _red003_closure_consistent(red_comparison_materials),
        "step5_red_consistent": _step5_red_consistent(comparison_materials),
        "hold004_preserved_across_matrices": _hold004_preserved(comparison_materials),
        "current_collect_baseline_connected": _current_collect_baseline_connected(comparison_materials),
        "current_group_inventory_connected": _current_group_inventory_connected(comparison_materials),
        "current_execution_plan_connected": _current_execution_plan_connected(comparison_materials),
        "old_baseline_not_used_as_current": _old_baseline_not_used_as_current(comparison_materials),
        "backend_suite_group_02_count_current": _backend_suite_group_02_count_current(comparison_materials),
        "full_backend_suite_green_false_across_matrices": _full_backend_suite_green_false(source_materials),
        "split_green_not_promoted": _split_green_not_promoted(source_materials),
        "release_allowed_false_across_matrices": _release_allowed_false(source_materials),
        "p8_start_allowed_false_across_matrices": _p8_start_allowed_false(source_materials),
        "body_free_markers_false_across_matrices": _body_free_markers_false(source_materials),
        "received_snapshot_blocking_status_consistent": _received_snapshot_blocking_status_consistent(source_materials),
        "received_snapshot_item_fingerprint_mismatch_resolved": _received_snapshot_item_fingerprint_mismatch_resolved(source_materials),
        "active_baseline_refresh_projection_consistent": _active_baseline_refresh_projection_consistent(source_materials),
    }
    consistency_status = _determine_consistency_status(checks=checks, source_materials=source_materials)

    red_closure = source_materials["red_closure_classification_matrix"]
    backend_split = source_materials["backend_suite_split_matrix"]
    r10_matrix = source_materials["r10_hold_matrix"]
    handoff = source_materials["release_handoff"]
    validation = source_materials["validation_matrix"]
    execution_summary = source_materials["backend_suite_execution_summary"]
    matrix_current_baseline_connection = _matrix_current_baseline_connection_from_sources(
        execution_summary=execution_summary,
        backend_split=backend_split,
        r10_matrix=r10_matrix,
        handoff=handoff,
        validation=validation,
    )
    official_group_02_capture_readiness_schema_version = clean_identifier(
        _first_received_snapshot_field(source_materials, "official_group_02_capture_readiness_schema_version"),
        default=P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION,
        max_length=160,
    )
    official_group_02_capture_readiness_status = clean_identifier(
        _first_received_snapshot_field(source_materials, "official_group_02_capture_readiness_status"),
        default=P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_ITEM_FINGERPRINT_MISMATCH,
        max_length=160,
    )
    official_group_02_capture_blocked = (
        _first_received_snapshot_field(source_materials, "official_group_02_capture_blocked") is True
    )
    official_group_02_capture_run_allowed = (
        _first_received_snapshot_field(source_materials, "official_group_02_capture_run_allowed") is True
    )
    official_group_02_capture_result_recording_allowed = (
        _first_received_snapshot_field(source_materials, "official_group_02_capture_result_recording_allowed") is True
    )
    received_snapshot_baseline_fingerprint_reconciled = (
        _first_received_snapshot_field(source_materials, "received_snapshot_baseline_fingerprint_reconciled") is True
    )
    received_snapshot_item_fingerprint_mismatch_unresolved = (
        _first_received_snapshot_field(source_materials, "received_snapshot_item_fingerprint_mismatch_unresolved") is True
    )
    received_snapshot_blocker_refs = dedupe_identifiers(
        [
            *_refs(backend_split, "received_snapshot_blocker_refs"),
            *_refs(r10_matrix, "received_snapshot_blocker_refs"),
            *_refs(handoff, "received_snapshot_blocker_refs"),
            *_refs(validation, "received_snapshot_blocker_refs"),
            P7_HOLD004_RECEIVED_SNAPSHOT_ITEM_FINGERPRINT_MISMATCH_BLOCKER_REF
            if received_snapshot_item_fingerprint_mismatch_unresolved
            else "",
        ],
        limit=120,
        max_length=160,
    )

    active_baseline_refresh_schema_version = clean_identifier(
        _first_received_snapshot_field(source_materials, "active_baseline_refresh_schema_version"),
        default="",
        max_length=160,
    )
    active_baseline_refresh_id = clean_identifier(
        _first_received_snapshot_field(source_materials, "active_baseline_refresh_id"),
        default="",
        max_length=180,
    )
    runtime_builder_refresh_status_id = clean_identifier(
        _first_received_snapshot_field(source_materials, "runtime_builder_refresh_status_id"),
        default="",
        max_length=180,
    )
    post_adoption_received_snapshot_reconcile_id = clean_identifier(
        _first_received_snapshot_field(source_materials, "post_adoption_received_snapshot_reconcile_id"),
        default="",
        max_length=180,
    )
    active_baseline_update_applied_to_runtime_builders = (
        _first_received_snapshot_field(source_materials, "active_baseline_update_applied_to_runtime_builders") is True
    )
    source_snapshot_ref_updated_in_active_builders = (
        _first_received_snapshot_field(source_materials, "source_snapshot_ref_updated_in_active_builders") is True
    )
    post_adoption_readiness_re_evaluated = (
        _first_received_snapshot_field(source_materials, "post_adoption_readiness_re_evaluated") is True
        or official_group_02_capture_readiness_schema_version
        == P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION_V2
    )

    closed_red_refs = dedupe_identifiers(
        [
            *_refs(red_closure, "closed_red_refs"),
            *_refs(backend_split, "closed_red_refs"),
            *_refs(r10_matrix, "closed_red_refs"),
            *_refs(handoff, "closed_red_refs"),
            *_refs(validation, "closed_red_refs"),
        ],
        limit=160,
        max_length=160,
    )
    unresolved_red_refs = dedupe_identifiers(
        [
            *_refs(red_closure, "unresolved_red_refs"),
            *_refs(backend_split, "unresolved_red_refs"),
            *_refs(r10_matrix, "unresolved_red_refs"),
            *_refs(handoff, "unresolved_red_refs"),
            *_refs(validation, "unresolved_red_refs"),
        ],
        limit=160,
        max_length=160,
    )
    if checks["red003_closure_consistent"]:
        closed_set = set(closed_red_refs)
        unresolved_red_refs = dedupe_identifiers(
            [ref for ref in unresolved_red_refs if ref not in closed_set],
            limit=160,
            max_length=160,
        )

    unresolved_hold_refs = dedupe_identifiers(
        [
            *P7_INITIAL_HOLD_IDS,
            *_refs(backend_split, "unresolved_hold_refs"),
            *_refs(r10_matrix, "unresolved_hold_refs"),
            *_refs(handoff, "unresolved_hold_refs"),
            *_refs(validation, "unresolved_hold_refs"),
        ],
        limit=160,
        max_length=160,
    )
    followups = dedupe_identifiers(
        [
            "matrix_consistency_report_passed_not_release_ready" if consistency_status == "PASS" else "matrix_consistency_review_required",
            "red003_closure_inconsistent" if checks["red003_closure_consistent"] is not True else "",
            "step5_red_inconsistent" if checks["step5_red_consistent"] is not True else "",
            "hold004_preservation_inconsistent" if checks["hold004_preserved_across_matrices"] is not True else "",
            "full_backend_suite_green_unconfirmed",
            "real_device_submit_modal_readfeel_unverified",
            "p5_human_qa_review_required",
            *safe_mapping(execution_summary).get("required_followup_fixes", []),
            *safe_mapping(backend_split).get("required_followup_fixes", []),
            *safe_mapping(r10_matrix).get("required_followup_fixes", []),
            *safe_mapping(handoff).get("required_followup_fixes", []),
            *safe_mapping(validation).get("required_followup_fixes", []),
        ],
        limit=200,
        max_length=180,
    )

    report = {
        "schema_version": P7_HOLD004_MATRIX_CONSISTENCY_REPORT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_MATRIX_CONSISTENCY_REPORT_STEP,
        "implementation_step": P7_HOLD004_MATRIX_CONSISTENCY_REPORT_STEP,
        "hold_id": P7_HOLD004_MATRIX_CONSISTENCY_HOLD_ID,
        "report_id": clean_identifier(report_id, default=P7_HOLD004_MATRIX_CONSISTENCY_REPORT_ID, max_length=160),
        "source_mode": "local_snapshot",
        "source_snapshot_ref": P7_HOLD004_MATRIX_CONSISTENCY_SOURCE_SNAPSHOT_REF,
        "git_checked": False,
        "inputs": {
            "backend_suite_execution_summary_schema_version": execution_summary.get("schema_version"),
            "red_closure_classification_schema_version": red_closure.get("schema_version"),
            "backend_suite_split_matrix_schema_version": backend_split.get("schema_version"),
            "r10_hold_matrix_schema_version": r10_matrix.get("schema_version"),
            "release_handoff_schema_version": handoff.get("schema_version"),
            "validation_matrix_schema_version": validation.get("schema_version"),
            "official_group_02_capture_readiness_schema_version": official_group_02_capture_readiness_schema_version,
        },
        "source_material_ids": {
            "backend_suite_execution_summary_id": clean_identifier(execution_summary.get("summary_id"), max_length=160),
            "backend_suite_split_matrix_id": clean_identifier(backend_split.get("matrix_id"), max_length=160),
            "r10_hold_matrix_id": clean_identifier(r10_matrix.get("matrix_id"), max_length=160),
            "release_handoff_source_runner_result_id": clean_identifier(
                handoff.get("source_runner_result_id"),
                max_length=160,
            ),
            "validation_matrix_id": clean_identifier(validation.get("matrix_id"), max_length=160),
        },
        "consistency_status": consistency_status,
        "checks": checks,
        "official_group_02_capture_readiness_schema_version": official_group_02_capture_readiness_schema_version,
        "official_group_02_capture_readiness_status": official_group_02_capture_readiness_status,
        "official_group_02_capture_blocked": official_group_02_capture_blocked,
        "official_group_02_capture_run_allowed": official_group_02_capture_run_allowed,
        "official_group_02_capture_result_recording_allowed": official_group_02_capture_result_recording_allowed,
        "received_snapshot_baseline_fingerprint_reconciled": received_snapshot_baseline_fingerprint_reconciled,
        "received_snapshot_item_fingerprint_mismatch_unresolved": received_snapshot_item_fingerprint_mismatch_unresolved,
        "received_snapshot_blocker_refs": received_snapshot_blocker_refs,
        "active_baseline_refresh_schema_version": active_baseline_refresh_schema_version,
        "active_baseline_refresh_id": active_baseline_refresh_id,
        "runtime_builder_refresh_status_id": runtime_builder_refresh_status_id,
        "post_adoption_received_snapshot_reconcile_id": post_adoption_received_snapshot_reconcile_id,
        "active_baseline_update_applied_to_runtime_builders": active_baseline_update_applied_to_runtime_builders,
        "source_snapshot_ref_updated_in_active_builders": source_snapshot_ref_updated_in_active_builders,
        "post_adoption_readiness_re_evaluated": post_adoption_readiness_re_evaluated,
        "current_collect_baseline_connected": checks["current_collect_baseline_connected"],
        "current_group_inventory_connected": checks["current_group_inventory_connected"],
        "current_execution_plan_connected": checks["current_execution_plan_connected"],
        "old_baseline_not_used_as_current": checks["old_baseline_not_used_as_current"],
        "backend_suite_group_02_count_current": checks["backend_suite_group_02_count_current"],
        "backend_suite_execution_summary_collect_baseline_id": matrix_current_baseline_connection.get("collect_baseline_id"),
        "backend_suite_execution_summary_inventory_id": matrix_current_baseline_connection.get("group_inventory_id"),
        "backend_suite_execution_summary_plan_id": matrix_current_baseline_connection.get("execution_plan_id"),
        "matrix_current_baseline_connection": matrix_current_baseline_connection,
        "closed_red_refs": closed_red_refs,
        "unresolved_red_refs": unresolved_red_refs,
        "unresolved_hold_refs": unresolved_hold_refs,
        "required_followup_fixes": followups,
        "backend_suite_execution_summary_connected": execution_summary.get("schema_version")
        == P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_SCHEMA_VERSION,
        "backend_suite_execution_summary_split_all_groups_green_confirmed": execution_summary.get(
            "split_all_groups_green_confirmed"
        )
        is True,
        "red003_closed": P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID in set(closed_red_refs),
        "red003_unresolved": P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID in set(unresolved_red_refs),
        **_release_closed_boundary(),
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
        "body_free": True,
    }
    assert_p7_hold004_matrix_consistency_report_contract(report)
    return report


def assert_p7_hold004_matrix_consistency_report_contract(report: Mapping[str, Any]) -> bool:
    """Validate the R10 matrix-consistency report and release-closed boundary."""

    data = safe_mapping(report)
    if data.get("schema_version") != P7_HOLD004_MATRIX_CONSISTENCY_REPORT_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 matrix consistency report schema_version changed")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_MATRIX_CONSISTENCY_HOLD_ID:
        raise ValueError("P7-HOLD-004 matrix consistency report must stay in P7-HOLD-004 scope")
    if data.get("implementation_step") != P7_HOLD004_MATRIX_CONSISTENCY_REPORT_STEP:
        raise ValueError("P7-HOLD-004 matrix consistency report implementation_step changed")
    if clean_identifier(data.get("report_id"), max_length=160) == "":
        raise ValueError("P7-HOLD-004 matrix consistency report id missing")
    if data.get("source_mode") != "local_snapshot" or data.get("source_snapshot_ref") != P7_HOLD004_MATRIX_CONSISTENCY_SOURCE_SNAPSHOT_REF:
        raise ValueError("P7-HOLD-004 matrix consistency report must stay on the current local snapshot")
    if data.get("git_checked") is not False:
        raise ValueError("P7-HOLD-004 matrix consistency report must not claim GitHub verification")
    for key in (
        "current_collect_baseline_connected",
        "current_group_inventory_connected",
        "current_execution_plan_connected",
        "old_baseline_not_used_as_current",
        "backend_suite_group_02_count_current",
    ):
        if not isinstance(data.get(key), bool):
            raise ValueError(f"P7-HOLD-004 matrix consistency report current baseline marker {key} must be boolean")
    connection = safe_mapping(data.get("matrix_current_baseline_connection"))
    if connection.get("collect_baseline_id") != P7_HOLD004_BACKEND_COLLECT_BASELINE_ID:
        raise ValueError("P7-HOLD-004 matrix consistency report must connect current collect baseline id")
    if connection.get("group_inventory_id") != P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID:
        raise ValueError("P7-HOLD-004 matrix consistency report must connect current group inventory id")
    if connection.get("execution_plan_id") != P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID:
        raise ValueError("P7-HOLD-004 matrix consistency report must connect current execution plan id")
    if connection.get("current_collect_file_count") != P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT:
        raise ValueError("P7-HOLD-004 matrix consistency report current collect file count changed")
    if connection.get("current_collect_test_item_count") != P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT:
        raise ValueError("P7-HOLD-004 matrix consistency report current collect test count changed")
    if connection.get("old_baseline_id") != P7_HOLD004_PREVIOUS_BACKEND_COLLECT_BASELINE_ID:
        raise ValueError("P7-HOLD-004 matrix consistency report must retain previous baseline id")
    if connection.get("old_baseline_used_as_current") is not False:
        raise ValueError("P7-HOLD-004 matrix consistency report must not use old baseline as current")

    inputs = safe_mapping(data.get("inputs"))
    expected_input_versions = {
        "backend_suite_execution_summary_schema_version": P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_SCHEMA_VERSION,
        "red_closure_classification_schema_version": P7_RED_CLOSURE_CLASSIFICATION_MATRIX_SCHEMA_VERSION,
        "backend_suite_split_matrix_schema_version": P7_BACKEND_SUITE_SPLIT_MATRIX_SCHEMA_VERSION,
        "r10_hold_matrix_schema_version": P7_R10_HOLD_MATRIX_SCHEMA_VERSION,
        "release_handoff_schema_version": P7_RELEASE_HANDOFF_SCHEMA_VERSION,
        "validation_matrix_schema_version": P7_VALIDATION_MATRIX_SCHEMA_VERSION,
    }
    for key, expected in expected_input_versions.items():
        if inputs.get(key) != expected:
            raise ValueError(f"P7-HOLD-004 matrix consistency report input {key} mismatch")
    input_readiness_schema = clean_identifier(
        inputs.get("official_group_02_capture_readiness_schema_version"),
        default="",
        max_length=160,
    )
    if input_readiness_schema not in P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_ALLOWED_SCHEMA_VERSIONS:
        raise ValueError("P7-HOLD-004 matrix consistency report input official group_02 readiness schema mismatch")

    status = clean_identifier(data.get("consistency_status"), max_length=80)
    if status not in P7_HOLD004_MATRIX_CONSISTENCY_ALLOWED_STATUSES:
        raise ValueError("P7-HOLD-004 matrix consistency report status invalid")
    checks = safe_mapping(data.get("checks"))
    for key in _REQUIRED_PASS_CHECKS:
        if not isinstance(checks.get(key), bool):
            raise ValueError(f"P7-HOLD-004 matrix consistency report check {key} must be boolean")
    if status == P7_HOLD004_MATRIX_CONSISTENCY_STATUS_PASS:
        missing = [key for key in _REQUIRED_PASS_CHECKS if checks.get(key) is not True]
        if missing:
            raise ValueError(f"P7-HOLD-004 matrix consistency PASS report has false checks: {missing}")

    readiness_schema_version = clean_identifier(
        data.get("official_group_02_capture_readiness_schema_version"),
        default="",
        max_length=160,
    )
    if readiness_schema_version not in P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_ALLOWED_SCHEMA_VERSIONS:
        raise ValueError("P7-HOLD-004 matrix consistency report must carry official group_02 readiness schema")
    readiness_after_refresh = readiness_schema_version == P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION_V2
    if data.get("received_snapshot_item_fingerprint_mismatch_unresolved") is True:
        if status == P7_HOLD004_MATRIX_CONSISTENCY_STATUS_PASS:
            raise ValueError("P7-HOLD-004 matrix consistency report cannot PASS unresolved received snapshot mismatch")
        if data.get("official_group_02_capture_readiness_status") != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_ITEM_FINGERPRINT_MISMATCH:
            raise ValueError("P7-HOLD-004 matrix consistency report must expose received snapshot readiness blocker")
        if data.get("official_group_02_capture_blocked") is not True:
            raise ValueError("P7-HOLD-004 matrix consistency report must keep official group_02 capture blocked")
        if data.get("official_group_02_capture_run_allowed") is not False:
            raise ValueError("P7-HOLD-004 matrix consistency report must keep group_02 run disallowed")
        if data.get("official_group_02_capture_result_recording_allowed") is not False:
            raise ValueError("P7-HOLD-004 matrix consistency report must keep group_02 result recording disallowed")
        blocker_refs = set(dedupe_identifiers(data.get("received_snapshot_blocker_refs"), limit=120, max_length=160))
        if P7_HOLD004_RECEIVED_SNAPSHOT_ITEM_FINGERPRINT_MISMATCH_BLOCKER_REF not in blocker_refs:
            raise ValueError("P7-HOLD-004 matrix consistency report missing received snapshot blocker ref")
        if checks.get("received_snapshot_blocking_status_consistent") is not True:
            raise ValueError("P7-HOLD-004 matrix consistency report received snapshot blocking status must be consistent")
        if checks.get("received_snapshot_item_fingerprint_mismatch_resolved") is not False:
            raise ValueError("P7-HOLD-004 matrix consistency report must not mark unresolved mismatch as resolved")
    if readiness_after_refresh:
        if data.get("official_group_02_capture_readiness_status") != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY:
            raise ValueError("P7-HOLD-004 matrix consistency report after refresh must expose official group_02 readiness as READY")
        if data.get("received_snapshot_baseline_fingerprint_reconciled") is not True:
            raise ValueError("P7-HOLD-004 matrix consistency report after refresh must carry reconciled received snapshot baseline")
        if data.get("received_snapshot_item_fingerprint_mismatch_unresolved") is not False:
            raise ValueError("P7-HOLD-004 matrix consistency report after refresh must resolve received snapshot item mismatch")
        if data.get("official_group_02_capture_blocked") is not False:
            raise ValueError("P7-HOLD-004 matrix consistency report after refresh must unblock official group_02 capture readiness")
        if data.get("official_group_02_capture_run_allowed") is not True:
            raise ValueError("P7-HOLD-004 matrix consistency report after refresh must allow official group_02 capture run")
        if data.get("official_group_02_capture_result_recording_allowed") is not True:
            raise ValueError("P7-HOLD-004 matrix consistency report after refresh must allow official group_02 result recording")
        if checks.get("received_snapshot_blocking_status_consistent") is not True:
            raise ValueError("P7-HOLD-004 matrix consistency report after refresh must keep readiness state consistent")
        if checks.get("received_snapshot_item_fingerprint_mismatch_resolved") is not True:
            raise ValueError("P7-HOLD-004 matrix consistency report after refresh must mark item mismatch resolved")
        if checks.get("active_baseline_refresh_projection_consistent") is not True:
            raise ValueError("P7-HOLD-004 matrix consistency report after refresh must project active baseline consistently")
        for key in (
            "active_baseline_update_applied_to_runtime_builders",
            "source_snapshot_ref_updated_in_active_builders",
            "post_adoption_readiness_re_evaluated",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-HOLD-004 matrix consistency report after refresh must keep {key}=true")
        if data.get("active_baseline_refresh_schema_version") != P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_SCHEMA_VERSION:
            raise ValueError("P7-HOLD-004 matrix consistency report active refresh schema mismatch")
        if data.get("active_baseline_refresh_id") != P7_HOLD004_ACTIVE_BASELINE_REFRESH_ID:
            raise ValueError("P7-HOLD-004 matrix consistency report active refresh id mismatch")
        if data.get("runtime_builder_refresh_status_id") != P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_ID:
            raise ValueError("P7-HOLD-004 matrix consistency report runtime refresh id mismatch")
        if data.get("post_adoption_received_snapshot_reconcile_id") != P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_ID:
            raise ValueError("P7-HOLD-004 matrix consistency report post-adoption reconcile id mismatch")

    for key in _RELEASE_CLOSED_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 matrix consistency report must keep {key}=false")
    if data.get("body_free") is not True:
        raise ValueError("P7-HOLD-004 matrix consistency report must be body_free=true")
    hold_refs = set(dedupe_identifiers(data.get("unresolved_hold_refs"), limit=160, max_length=160))
    if P7_HOLD004_MATRIX_CONSISTENCY_HOLD_ID not in hold_refs:
        raise ValueError("P7-HOLD-004 matrix consistency report must keep P7-HOLD-004 unresolved")
    followups = set(dedupe_identifiers(data.get("required_followup_fixes"), limit=220, max_length=180))
    for required in (
        "full_backend_suite_green_unconfirmed",
        "real_device_submit_modal_readfeel_unverified",
        "p5_human_qa_review_required",
    ):
        if required not in followups:
            raise ValueError(f"P7-HOLD-004 matrix consistency report missing followup {required}")
    closed_red_refs = set(dedupe_identifiers(data.get("closed_red_refs"), limit=160, max_length=160))
    unresolved_red_refs = set(dedupe_identifiers(data.get("unresolved_red_refs"), limit=160, max_length=160))
    if P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID in closed_red_refs and P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID in unresolved_red_refs:
        if status == P7_HOLD004_MATRIX_CONSISTENCY_STATUS_PASS or checks.get("red003_closure_consistent") is True:
            raise ValueError("P7-HOLD-004 matrix consistency PASS report cannot keep P7-RED-003 closed and unresolved")
    if checks.get("red003_closure_consistent") is True:
        if P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID not in closed_red_refs | unresolved_red_refs:
            raise ValueError("P7-HOLD-004 matrix consistency report must expose P7-RED-003 state")
    if checks.get("hold004_preserved_across_matrices") is True and P7_HOLD004_MATRIX_CONSISTENCY_HOLD_ID not in hold_refs:
        raise ValueError("P7-HOLD-004 matrix consistency report must expose HOLD-004 when preservation check passes")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_hold004_matrix_consistency_report.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_hold004_matrix_consistency_report.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_hold004_matrix_consistency_report")
    return True


__all__ = [
    "P7_HOLD004_MATRIX_CONSISTENCY_ALLOWED_STATUSES",
    "P7_HOLD004_MATRIX_CONSISTENCY_HOLD_ID",
    "P7_HOLD004_MATRIX_CONSISTENCY_REPORT_ID",
    "P7_HOLD004_MATRIX_CONSISTENCY_REPORT_SCHEMA_VERSION",
    "P7_HOLD004_MATRIX_CONSISTENCY_REPORT_STEP",
    "P7_HOLD004_MATRIX_CONSISTENCY_STATUS_BLOCKED",
    "P7_HOLD004_MATRIX_CONSISTENCY_STATUS_NOT_RUN",
    "P7_HOLD004_MATRIX_CONSISTENCY_STATUS_PASS",
    "P7_HOLD004_MATRIX_CONSISTENCY_STATUS_REVIEW_REQUIRED",
    "assert_p7_hold004_matrix_consistency_report_contract",
    "build_p7_hold004_matrix_consistency_report",
]
