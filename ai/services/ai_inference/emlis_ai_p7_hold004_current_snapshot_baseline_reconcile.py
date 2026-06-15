# -*- coding: utf-8 -*-
"""P7-HOLD-004 current snapshot baseline reconcile material.

R13 scope only:
- keep the previous 20260614 backend collect baseline as previous evidence;
- record the 20260615 local snapshot collect baseline as the current snapshot
  to be adopted by later R14+ refresh work;
- record the aggregate delta as body-free counts and group identifiers only;
- block official group execution until the collect baseline, group inventory,
  execution plan, and matrices are refreshed to the same current snapshot.

This module intentionally does not update the active collect baseline, group
inventory, execution plan, matrix, release handoff, RN UI, API route, public
response shape, DB schema, or Emlis runtime behavior.  It stores identifiers,
counts, booleans, enum-like decisions, and SHA-256 hashes only.  It must never
serialize raw input, comment_text bodies, candidate bodies, surface bodies,
file-level nodeid deltas, terminal output, stdout/stderr, or traceback bodies.
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

P7_HOLD004_CURRENT_SNAPSHOT_BASELINE_RECONCILE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.current_snapshot_baseline_reconcile.v1"
)
P7_HOLD004_CURRENT_SNAPSHOT_BASELINE_RECONCILE_STEP: Final = (
    "P7-HOLD-004_CurrentSnapshotBaselineReconcile_R13_20260615"
)
P7_HOLD004_CURRENT_SNAPSHOT_BASELINE_RECONCILE_ID: Final = (
    "p7_hold004_current_snapshot_baseline_reconcile_20260615"
)
P7_HOLD004_BACKEND_SUITE_HOLD_ID: Final = "P7-HOLD-004"

P7_HOLD004_PREVIOUS_BACKEND_COLLECT_BASELINE_ID: Final = (
    "p7_hold004_backend_collect_baseline_20260614"
)
P7_HOLD004_PREVIOUS_BACKEND_SOURCE_SNAPSHOT_REF: Final = "mashos-api(146).zip"
P7_HOLD004_PREVIOUS_BACKEND_COLLECTED_TEST_FILE_COUNT: Final = 416
P7_HOLD004_PREVIOUS_BACKEND_COLLECTED_TEST_ITEM_COUNT: Final = 2673
P7_HOLD004_PREVIOUS_BACKEND_COLLECT_WARNINGS_COUNT: Final = 1
P7_HOLD004_PREVIOUS_GROUP_02_FILE_COUNT: Final = 10
P7_HOLD004_PREVIOUS_GROUP_02_TEST_ITEM_COUNT: Final = 69

P7_HOLD004_CURRENT_BACKEND_COLLECT_BASELINE_ID: Final = (
    "p7_hold004_backend_collect_baseline_20260615"
)
P7_HOLD004_CURRENT_BACKEND_SOURCE_SNAPSHOT_REF: Final = "mashos-api(147).zip"
P7_HOLD004_CURRENT_BACKEND_COLLECTED_TEST_FILE_COUNT: Final = 425
P7_HOLD004_CURRENT_BACKEND_COLLECTED_TEST_ITEM_COUNT: Final = 2856
P7_HOLD004_CURRENT_BACKEND_COLLECT_WARNINGS_COUNT: Final = 1
P7_HOLD004_CURRENT_BACKEND_TEST_ITEMS_FINGERPRINT_SHA256: Final = (
    "fee1eca805564d0840dc5b23f60a7e2d6c7297d658a76dc4ce175e0137c261f1"
)
P7_HOLD004_CURRENT_BACKEND_TEST_FILES_FINGERPRINT_SHA256: Final = (
    "6866231daf68427dca2de1b2011feea49450f7b4a8b3c5b9dec0f9ccd5f3e9c6"
)
P7_HOLD004_CURRENT_GROUP_02_FILE_COUNT: Final = 19
P7_HOLD004_CURRENT_GROUP_02_TEST_ITEM_COUNT: Final = 252

P7_HOLD004_BACKEND_COLLECT_BASELINE_FILE_COUNT_DELTA: Final = (
    P7_HOLD004_CURRENT_BACKEND_COLLECTED_TEST_FILE_COUNT
    - P7_HOLD004_PREVIOUS_BACKEND_COLLECTED_TEST_FILE_COUNT
)
P7_HOLD004_BACKEND_COLLECT_BASELINE_TEST_ITEM_COUNT_DELTA: Final = (
    P7_HOLD004_CURRENT_BACKEND_COLLECTED_TEST_ITEM_COUNT
    - P7_HOLD004_PREVIOUS_BACKEND_COLLECTED_TEST_ITEM_COUNT
)
P7_HOLD004_BACKEND_COLLECT_BASELINE_WARNINGS_COUNT_DELTA: Final = (
    P7_HOLD004_CURRENT_BACKEND_COLLECT_WARNINGS_COUNT
    - P7_HOLD004_PREVIOUS_BACKEND_COLLECT_WARNINGS_COUNT
)
P7_HOLD004_GROUP_02_FILE_COUNT_DELTA: Final = (
    P7_HOLD004_CURRENT_GROUP_02_FILE_COUNT - P7_HOLD004_PREVIOUS_GROUP_02_FILE_COUNT
)
P7_HOLD004_GROUP_02_TEST_ITEM_COUNT_DELTA: Final = (
    P7_HOLD004_CURRENT_GROUP_02_TEST_ITEM_COUNT
    - P7_HOLD004_PREVIOUS_GROUP_02_TEST_ITEM_COUNT
)
P7_HOLD004_CURRENT_SNAPSHOT_AFFECTED_GROUP_IDS: Final[tuple[str, ...]] = (
    "group_02_p7_hold004",
)
P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM: Final = (
    "test_items=sha256(sorted_pytest_nodeids_joined_by_lf);"
    "test_files=sha256(ordered_unique_test_files_joined_by_lf)"
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
_REQUIRED_FOLLOWUP_FIXES: Final[tuple[str, ...]] = (
    "active_collect_baseline_refresh_required",
    "backend_suite_group_inventory_refresh_required",
    "backend_suite_execution_plan_refresh_required",
    "backend_suite_matrix_reconnect_required",
    "official_group_execution_blocked_until_current_baseline_refresh",
    "full_backend_suite_green_unconfirmed",
)
_DECISION_FLAGS: Final[dict[str, bool]] = {
    "current_baseline_should_replace_active_baseline": True,
    "previous_baseline_retained_as_previous": True,
    "group_inventory_refresh_required": True,
    "execution_plan_refresh_required": True,
    "matrix_reconnect_required": True,
    "official_group_execution_blocked_until_refresh": True,
    "collect_only_is_not_execution_green": True,
    "ad_hoc_group_02_run_is_not_official_result": True,
    "subset_green_is_not_full_backend_suite_green": True,
}


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
            "file_level_delta_refs_included": False,
            "nodeid_refs_included": False,
        }
    )
    return flags


def _release_closed_boundary() -> dict[str, bool]:
    return {key: False for key in _RELEASE_CLOSED_KEYS}


def _previous_baseline_material() -> dict[str, Any]:
    return {
        "baseline_id": P7_HOLD004_PREVIOUS_BACKEND_COLLECT_BASELINE_ID,
        "source_snapshot_ref": P7_HOLD004_PREVIOUS_BACKEND_SOURCE_SNAPSHOT_REF,
        "test_file_count": P7_HOLD004_PREVIOUS_BACKEND_COLLECTED_TEST_FILE_COUNT,
        "test_item_count": P7_HOLD004_PREVIOUS_BACKEND_COLLECTED_TEST_ITEM_COUNT,
        "warnings_count": P7_HOLD004_PREVIOUS_BACKEND_COLLECT_WARNINGS_COUNT,
        "group_02_file_count": P7_HOLD004_PREVIOUS_GROUP_02_FILE_COUNT,
        "group_02_test_item_count": P7_HOLD004_PREVIOUS_GROUP_02_TEST_ITEM_COUNT,
    }


def _current_baseline_material() -> dict[str, Any]:
    return {
        "baseline_id": P7_HOLD004_CURRENT_BACKEND_COLLECT_BASELINE_ID,
        "source_snapshot_ref": P7_HOLD004_CURRENT_BACKEND_SOURCE_SNAPSHOT_REF,
        "test_file_count": P7_HOLD004_CURRENT_BACKEND_COLLECTED_TEST_FILE_COUNT,
        "test_item_count": P7_HOLD004_CURRENT_BACKEND_COLLECTED_TEST_ITEM_COUNT,
        "warnings_count": P7_HOLD004_CURRENT_BACKEND_COLLECT_WARNINGS_COUNT,
        "test_items_fingerprint_sha256": P7_HOLD004_CURRENT_BACKEND_TEST_ITEMS_FINGERPRINT_SHA256,
        "test_files_fingerprint_sha256": P7_HOLD004_CURRENT_BACKEND_TEST_FILES_FINGERPRINT_SHA256,
        "fingerprint_algorithm": P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM,
    }


def _group_delta_material() -> dict[str, Any]:
    return {
        "group_id": "group_02_p7_hold004",
        "old_file_count": P7_HOLD004_PREVIOUS_GROUP_02_FILE_COUNT,
        "old_test_item_count": P7_HOLD004_PREVIOUS_GROUP_02_TEST_ITEM_COUNT,
        "current_file_count": P7_HOLD004_CURRENT_GROUP_02_FILE_COUNT,
        "current_test_item_count": P7_HOLD004_CURRENT_GROUP_02_TEST_ITEM_COUNT,
        "file_count_delta": P7_HOLD004_GROUP_02_FILE_COUNT_DELTA,
        "test_item_count_delta": P7_HOLD004_GROUP_02_TEST_ITEM_COUNT_DELTA,
    }


def build_p7_hold004_current_snapshot_baseline_reconcile() -> dict[str, Any]:
    """Build the R13 old/current baseline reconcile material.

    The material is a handoff guard, not an active baseline update.  R14+ must
    still refresh the active collect baseline and downstream inventory/plan
    builders before any official group execution result can be recorded.
    """

    material = {
        "schema_version": P7_HOLD004_CURRENT_SNAPSHOT_BASELINE_RECONCILE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_CURRENT_SNAPSHOT_BASELINE_RECONCILE_STEP,
        "implementation_step": P7_HOLD004_CURRENT_SNAPSHOT_BASELINE_RECONCILE_STEP,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "reconcile_id": P7_HOLD004_CURRENT_SNAPSHOT_BASELINE_RECONCILE_ID,
        "source_mode": P7_SOURCE_MODE,
        "source_snapshot_ref": P7_HOLD004_CURRENT_BACKEND_SOURCE_SNAPSHOT_REF,
        "git_checked": P7_GIT_CHECKED,
        "previous_baseline": _previous_baseline_material(),
        "current_baseline": _current_baseline_material(),
        "delta": {
            "test_file_count_delta": P7_HOLD004_BACKEND_COLLECT_BASELINE_FILE_COUNT_DELTA,
            "test_item_count_delta": P7_HOLD004_BACKEND_COLLECT_BASELINE_TEST_ITEM_COUNT_DELTA,
            "warnings_count_delta": P7_HOLD004_BACKEND_COLLECT_BASELINE_WARNINGS_COUNT_DELTA,
            "affected_group_ids": list(P7_HOLD004_CURRENT_SNAPSHOT_AFFECTED_GROUP_IDS),
            "group_deltas": [_group_delta_material()],
            "file_level_delta_refs_included": False,
            "nodeid_refs_included": False,
        },
        "decision": dict(_DECISION_FLAGS),
        **_release_closed_boundary(),
        "unresolved_hold_refs": [P7_HOLD004_BACKEND_SUITE_HOLD_ID],
        "required_followup_fixes": list(_REQUIRED_FOLLOWUP_FIXES),
        "public_contract": _public_contract_boundary_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_hold004_current_snapshot_baseline_reconcile_contract(material)
    return material


def _assert_baseline(
    baseline: Mapping[str, Any],
    *,
    source: str,
    expected_baseline_id: str,
    expected_snapshot_ref: str,
    expected_file_count: int,
    expected_test_item_count: int,
    expected_warnings_count: int,
) -> None:
    data = safe_mapping(baseline)
    if data.get("baseline_id") != expected_baseline_id:
        raise ValueError(f"{source}.baseline_id mismatch")
    if data.get("source_snapshot_ref") != expected_snapshot_ref:
        raise ValueError(f"{source}.source_snapshot_ref mismatch")
    if data.get("test_file_count") != expected_file_count:
        raise ValueError(f"{source}.test_file_count mismatch")
    if data.get("test_item_count") != expected_test_item_count:
        raise ValueError(f"{source}.test_item_count mismatch")
    if data.get("warnings_count") != expected_warnings_count:
        raise ValueError(f"{source}.warnings_count mismatch")


def _assert_release_closed_and_body_free(data: Mapping[str, Any], *, source: str) -> None:
    for key in _RELEASE_CLOSED_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=false")
    unresolved_holds = set(dedupe_identifiers(data.get("unresolved_hold_refs"), limit=40, max_length=120))
    if P7_HOLD004_BACKEND_SUITE_HOLD_ID not in unresolved_holds:
        raise ValueError(f"{source} must keep P7-HOLD-004 unresolved")
    followups = set(dedupe_identifiers(data.get("required_followup_fixes"), limit=80, max_length=200))
    for followup in _REQUIRED_FOLLOWUP_FIXES:
        if followup not in followups:
            raise ValueError(f"{source} missing followup {followup}")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must keep body_free=true")
    assert_false_markers(safe_mapping(data.get("public_contract")), source=f"{source}.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source=f"{source}.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)


def assert_p7_hold004_current_snapshot_baseline_reconcile_contract(material: Mapping[str, Any]) -> bool:
    """Validate the R13 old/current baseline reconcile material."""

    data = safe_mapping(material)
    source = "p7_hold004_current_snapshot_baseline_reconcile"
    if data.get("schema_version") != P7_HOLD004_CURRENT_SNAPSHOT_BASELINE_RECONCILE_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 current snapshot baseline reconcile schema_version mismatch")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError("P7-HOLD-004 current snapshot baseline reconcile scope mismatch")
    if data.get("implementation_step") != P7_HOLD004_CURRENT_SNAPSHOT_BASELINE_RECONCILE_STEP:
        raise ValueError("P7-HOLD-004 current snapshot baseline reconcile implementation_step mismatch")
    if data.get("reconcile_id") != P7_HOLD004_CURRENT_SNAPSHOT_BASELINE_RECONCILE_ID:
        raise ValueError("P7-HOLD-004 current snapshot baseline reconcile id mismatch")
    if data.get("source_mode") != P7_SOURCE_MODE:
        raise ValueError("P7-HOLD-004 current snapshot baseline reconcile source_mode mismatch")
    if data.get("source_snapshot_ref") != P7_HOLD004_CURRENT_BACKEND_SOURCE_SNAPSHOT_REF:
        raise ValueError("P7-HOLD-004 current snapshot baseline reconcile source snapshot mismatch")
    if data.get("git_checked") is not False:
        raise ValueError("P7-HOLD-004 current snapshot baseline reconcile must not claim GitHub verification")

    previous = safe_mapping(data.get("previous_baseline"))
    current = safe_mapping(data.get("current_baseline"))
    _assert_baseline(
        previous,
        source=f"{source}.previous_baseline",
        expected_baseline_id=P7_HOLD004_PREVIOUS_BACKEND_COLLECT_BASELINE_ID,
        expected_snapshot_ref=P7_HOLD004_PREVIOUS_BACKEND_SOURCE_SNAPSHOT_REF,
        expected_file_count=P7_HOLD004_PREVIOUS_BACKEND_COLLECTED_TEST_FILE_COUNT,
        expected_test_item_count=P7_HOLD004_PREVIOUS_BACKEND_COLLECTED_TEST_ITEM_COUNT,
        expected_warnings_count=P7_HOLD004_PREVIOUS_BACKEND_COLLECT_WARNINGS_COUNT,
    )
    if previous.get("group_02_file_count") != P7_HOLD004_PREVIOUS_GROUP_02_FILE_COUNT:
        raise ValueError("previous baseline group_02 file count mismatch")
    if previous.get("group_02_test_item_count") != P7_HOLD004_PREVIOUS_GROUP_02_TEST_ITEM_COUNT:
        raise ValueError("previous baseline group_02 test item count mismatch")

    _assert_baseline(
        current,
        source=f"{source}.current_baseline",
        expected_baseline_id=P7_HOLD004_CURRENT_BACKEND_COLLECT_BASELINE_ID,
        expected_snapshot_ref=P7_HOLD004_CURRENT_BACKEND_SOURCE_SNAPSHOT_REF,
        expected_file_count=P7_HOLD004_CURRENT_BACKEND_COLLECTED_TEST_FILE_COUNT,
        expected_test_item_count=P7_HOLD004_CURRENT_BACKEND_COLLECTED_TEST_ITEM_COUNT,
        expected_warnings_count=P7_HOLD004_CURRENT_BACKEND_COLLECT_WARNINGS_COUNT,
    )
    if current.get("test_items_fingerprint_sha256") != P7_HOLD004_CURRENT_BACKEND_TEST_ITEMS_FINGERPRINT_SHA256:
        raise ValueError("current baseline test item fingerprint mismatch")
    if current.get("test_files_fingerprint_sha256") != P7_HOLD004_CURRENT_BACKEND_TEST_FILES_FINGERPRINT_SHA256:
        raise ValueError("current baseline test file fingerprint mismatch")
    if current.get("fingerprint_algorithm") != P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM:
        raise ValueError("current baseline fingerprint algorithm mismatch")
    if previous.get("baseline_id") == current.get("baseline_id"):
        raise ValueError("previous and current baselines must not share one baseline_id")

    delta = safe_mapping(data.get("delta"))
    if delta.get("test_file_count_delta") != P7_HOLD004_BACKEND_COLLECT_BASELINE_FILE_COUNT_DELTA:
        raise ValueError("current snapshot file count delta mismatch")
    if delta.get("test_item_count_delta") != P7_HOLD004_BACKEND_COLLECT_BASELINE_TEST_ITEM_COUNT_DELTA:
        raise ValueError("current snapshot test item count delta mismatch")
    if delta.get("warnings_count_delta") != P7_HOLD004_BACKEND_COLLECT_BASELINE_WARNINGS_COUNT_DELTA:
        raise ValueError("current snapshot warnings delta mismatch")
    affected_group_ids = tuple(
        dedupe_identifiers(delta.get("affected_group_ids"), limit=20, max_length=120)
    )
    if affected_group_ids != P7_HOLD004_CURRENT_SNAPSHOT_AFFECTED_GROUP_IDS:
        raise ValueError("current snapshot affected_group_ids must only include group_02_p7_hold004")
    if delta.get("file_level_delta_refs_included") is not False:
        raise ValueError("current snapshot reconcile must not include file-level delta refs")
    if delta.get("nodeid_refs_included") is not False:
        raise ValueError("current snapshot reconcile must not include nodeid refs")

    group_deltas = list(delta.get("group_deltas") or [])
    if len(group_deltas) != 1:
        raise ValueError("current snapshot reconcile must keep exactly one group delta")
    group_delta = safe_mapping(group_deltas[0])
    expected_group_delta = _group_delta_material()
    for key, expected in expected_group_delta.items():
        if group_delta.get(key) != expected:
            raise ValueError(f"current snapshot group delta {key} mismatch")

    decision = safe_mapping(data.get("decision"))
    if set(decision) != set(_DECISION_FLAGS):
        raise ValueError("current snapshot reconcile decision keys mismatch")
    for key, expected in _DECISION_FLAGS.items():
        if decision.get(key) is not expected:
            raise ValueError(f"current snapshot reconcile decision {key} mismatch")

    _assert_release_closed_and_body_free(data, source=source)
    return True


__all__ = [
    "P7_HOLD004_BACKEND_COLLECT_BASELINE_FILE_COUNT_DELTA",
    "P7_HOLD004_BACKEND_COLLECT_BASELINE_TEST_ITEM_COUNT_DELTA",
    "P7_HOLD004_BACKEND_COLLECT_BASELINE_WARNINGS_COUNT_DELTA",
    "P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM",
    "P7_HOLD004_BACKEND_SUITE_HOLD_ID",
    "P7_HOLD004_CURRENT_BACKEND_COLLECT_BASELINE_ID",
    "P7_HOLD004_CURRENT_BACKEND_COLLECT_WARNINGS_COUNT",
    "P7_HOLD004_CURRENT_BACKEND_COLLECTED_TEST_FILE_COUNT",
    "P7_HOLD004_CURRENT_BACKEND_COLLECTED_TEST_ITEM_COUNT",
    "P7_HOLD004_CURRENT_BACKEND_SOURCE_SNAPSHOT_REF",
    "P7_HOLD004_CURRENT_BACKEND_TEST_FILES_FINGERPRINT_SHA256",
    "P7_HOLD004_CURRENT_BACKEND_TEST_ITEMS_FINGERPRINT_SHA256",
    "P7_HOLD004_CURRENT_GROUP_02_FILE_COUNT",
    "P7_HOLD004_CURRENT_GROUP_02_TEST_ITEM_COUNT",
    "P7_HOLD004_CURRENT_SNAPSHOT_AFFECTED_GROUP_IDS",
    "P7_HOLD004_CURRENT_SNAPSHOT_BASELINE_RECONCILE_ID",
    "P7_HOLD004_CURRENT_SNAPSHOT_BASELINE_RECONCILE_SCHEMA_VERSION",
    "P7_HOLD004_CURRENT_SNAPSHOT_BASELINE_RECONCILE_STEP",
    "P7_HOLD004_GROUP_02_FILE_COUNT_DELTA",
    "P7_HOLD004_GROUP_02_TEST_ITEM_COUNT_DELTA",
    "P7_HOLD004_PREVIOUS_BACKEND_COLLECT_BASELINE_ID",
    "P7_HOLD004_PREVIOUS_BACKEND_COLLECT_WARNINGS_COUNT",
    "P7_HOLD004_PREVIOUS_BACKEND_COLLECTED_TEST_FILE_COUNT",
    "P7_HOLD004_PREVIOUS_BACKEND_COLLECTED_TEST_ITEM_COUNT",
    "P7_HOLD004_PREVIOUS_BACKEND_SOURCE_SNAPSHOT_REF",
    "P7_HOLD004_PREVIOUS_GROUP_02_FILE_COUNT",
    "P7_HOLD004_PREVIOUS_GROUP_02_TEST_ITEM_COUNT",
    "assert_p7_hold004_current_snapshot_baseline_reconcile_contract",
    "build_p7_hold004_current_snapshot_baseline_reconcile",
]
