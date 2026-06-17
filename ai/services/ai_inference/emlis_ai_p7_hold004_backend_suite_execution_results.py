# -*- coding: utf-8 -*-
"""P7-HOLD-004 current-snapshot R17 execution-result materials.

R17 current-snapshot scope only:
- normalize split pytest group/batch outcomes into body-free status material;
- capture first red and first timeout as identifiers/enums/counts only;
- aggregate group run results into one execution summary material;
- never retain terminal output, stdout/stderr, traceback bodies, raw input,
  comment_text bodies, candidate bodies, or surface bodies;
- never promote split green, group green, or run-result green to full backend
  suite green, P7 completion, P8 start, or release readiness.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
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
    listify,
    public_contract_flags,
    safe_mapping,
)
from emlis_ai_p7_hold004_backend_suite_group_inventory_plan import (
    P7_HOLD004_BACKEND_SUITE_EXECUTION_ORDER,
    P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID,
    P7_HOLD004_BACKEND_SUITE_GROUP_DEFINITIONS,
    P7_HOLD004_BACKEND_SUITE_GROUP_IDS,
    P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID,
    P7_HOLD004_BACKEND_SUITE_TOTAL_BATCH_COUNT,
    assert_p7_hold004_backend_suite_execution_plan_contract,
    build_p7_hold004_backend_suite_execution_plan,
)
from emlis_ai_p7_hold004_backend_suite_split_consistency import (
    P7_HOLD004_BACKEND_COLLECT_BASELINE_ID,
    P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT,
    P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT,
    P7_HOLD004_BACKEND_SUITE_HOLD_ID,
)
from emlis_ai_p7_hold004_received_snapshot_baseline_fingerprint_reconcile import (
    P7_HOLD004_RECEIVED_ADOPTION_STATUS_BLOCKED_UNCLASSIFIED_ITEM_FINGERPRINT_MISMATCH,
    P7_HOLD004_RECEIVED_RECONCILE_STATUS_ITEM_FINGERPRINT_MISMATCH_UNCLASSIFIED,
    P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_ADOPTION_DECISION_ID,
    P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_ADOPTION_DECISION_SCHEMA_VERSION,
    P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_ID,
    P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_SCHEMA_VERSION,
    assert_p7_hold004_received_snapshot_baseline_adoption_decision_contract,
    assert_p7_hold004_received_snapshot_baseline_fingerprint_reconcile_contract,
    build_p7_hold004_received_snapshot_baseline_adoption_decision,
    build_p7_hold004_received_snapshot_baseline_fingerprint_reconcile,
)

P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_R4_R5_STEP: Final = (
    "P7-HOLD-004_CurrentSnapshotBaselineReconcile_R17_20260615"
)
P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_ADOPTION_STEP: Final = (
    "P7-HOLD-004_CurrentSnapshotBaselineReconcile_R19_20260615"
)
P7_HOLD004_BACKEND_SUITE_GROUP_RUN_RESULT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.backend_suite_group_run_result.v1"
)
P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_ADOPTION_RULE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.official_group02_capture_adoption_rule.v1"
)
P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_ADOPTION_DECISION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.official_group02_capture_adoption_decision.v1"
)
P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.official_group02_capture_readiness.v1"
)
P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION_V2: Final = (
    "cocolon.emlis.p7.hold004.official_group02_capture_readiness.v2"
)
P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_ALLOWED_SCHEMA_VERSIONS: Final[frozenset[str]] = frozenset(
    {
        P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION,
        P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION_V2,
    }
)
P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.post_adoption_received_snapshot_reconcile.v1"
)
P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_ID: Final = (
    "p7_hold004_post_adoption_received_snapshot_reconcile_20260616"
)
P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.runtime_builder_refresh_status.v1"
)
P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_ID: Final = (
    "p7_hold004_runtime_builder_refresh_status_20260616"
)
P7_HOLD004_ACTIVE_BASELINE_REFRESH_ID: Final = "p7_hold004_active_baseline_refresh_20260616"
P7_HOLD004_GROUP02_TIMEOUT_CLASSIFICATION_PLAN_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.group02_timeout_classification_plan.v1"
)
P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_ADOPTION_RULE_ID: Final = (
    "p7_hold004_group_02_official_capture_adoption_rule_20260615"
)
P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_DECISION_ID: Final = (
    "p7_hold004_group_02_official_capture_adoption_decision_20260615"
)
P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STEP: Final = (
    "P7-HOLD-004_ReceivedSnapshotBaselineFingerprintReconcile_R25_20260615"
)
P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_AFTER_REFRESH_STEP: Final = (
    "P7-HOLD-004_ActiveBaselineRuntimeBuilderRefresh_R39_OfficialGroup02CaptureReadinessReevaluation_20260616"
)
P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_ID: Final = (
    "p7_hold004_group_02_official_capture_readiness_20260615"
)
P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_AFTER_REFRESH_ID: Final = (
    "p7_hold004_official_group02_capture_readiness_20260616"
)
P7_HOLD004_GROUP02_TIMEOUT_CLASSIFICATION_PLAN_STEP: Final = (
    "P7-HOLD-004_ReceivedSnapshotBaselineFingerprintReconcile_R28_20260615"
)
P7_HOLD004_GROUP02_TIMEOUT_CLASSIFICATION_PLAN_ID: Final = (
    "p7_hold004_group_02_timeout_classification_plan_20260615"
)
P7_HOLD004_GROUP02_OFFICIAL_CAPTURE_COMMAND_ID: Final = (
    "pytest_group_02_p7_hold004_capture_run_20260615"
)
P7_HOLD004_GROUP02_OFFICIAL_COLLECT_COMMAND_ID: Final = (
    "pytest_collect_only_group_02_p7_hold004_20260615"
)
P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID: Final = "group_02_p7_hold004"
P7_HOLD004_GROUP02_OFFICIAL_BATCH_ID: Final = "group_02_p7_hold004_batch_01"
P7_HOLD004_GROUP02_OFFICIAL_FILE_COUNT: Final = 19
P7_HOLD004_GROUP02_OFFICIAL_TEST_ITEM_COUNT: Final = 252
P7_HOLD004_GROUP02_OFFICIAL_WARNINGS_COUNT: Final = 1
P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.backend_suite_execution_summary.v1"
)
P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_ID: Final = (
    "p7_hold004_backend_suite_execution_summary_20260615"
)
P7_HOLD004_BACKEND_R4_R5_SOURCE_SNAPSHOT_REF: Final = "mashos-api(148).zip"
P7_HOLD004_PREVIOUS_BACKEND_COLLECT_BASELINE_ID: Final = "p7_hold004_backend_collect_baseline_20260614"

P7_HOLD004_BACKEND_SUITE_RUN_KIND_CAPTURE: Final = "capture_run"
P7_HOLD004_BACKEND_SUITE_RUN_KIND_CONFIRMATION: Final = "confirmation_run"
P7_HOLD004_BACKEND_SUITE_RUN_KIND_NOT_RUN: Final = "not_run"
P7_HOLD004_BACKEND_SUITE_ALLOWED_RUN_KINDS: Final[frozenset[str]] = frozenset(
    {
        P7_HOLD004_BACKEND_SUITE_RUN_KIND_CAPTURE,
        P7_HOLD004_BACKEND_SUITE_RUN_KIND_CONFIRMATION,
        P7_HOLD004_BACKEND_SUITE_RUN_KIND_NOT_RUN,
    }
)

P7_HOLD004_BACKEND_SUITE_STATUS_PASS: Final = "PASS"
P7_HOLD004_BACKEND_SUITE_STATUS_PASS_WITH_SKIPS: Final = "PASS_WITH_SKIPS"
P7_HOLD004_BACKEND_SUITE_STATUS_FAIL: Final = "FAIL"
P7_HOLD004_BACKEND_SUITE_STATUS_TIMEOUT: Final = "TIMEOUT"
P7_HOLD004_BACKEND_SUITE_STATUS_COLLECTION_FAILED: Final = "COLLECTION_FAILED"
P7_HOLD004_BACKEND_SUITE_STATUS_NOT_RUN: Final = "NOT_RUN"
P7_HOLD004_BACKEND_SUITE_STATUS_INTERRUPTED: Final = "INTERRUPTED"
P7_HOLD004_BACKEND_SUITE_STATUS_BLOCKED_BY_PREVIOUS_RED: Final = "BLOCKED_BY_PREVIOUS_RED"
P7_HOLD004_BACKEND_SUITE_ALLOWED_STATUSES: Final[frozenset[str]] = frozenset(
    {
        P7_HOLD004_BACKEND_SUITE_STATUS_PASS,
        P7_HOLD004_BACKEND_SUITE_STATUS_PASS_WITH_SKIPS,
        P7_HOLD004_BACKEND_SUITE_STATUS_FAIL,
        P7_HOLD004_BACKEND_SUITE_STATUS_TIMEOUT,
        P7_HOLD004_BACKEND_SUITE_STATUS_COLLECTION_FAILED,
        P7_HOLD004_BACKEND_SUITE_STATUS_NOT_RUN,
        P7_HOLD004_BACKEND_SUITE_STATUS_INTERRUPTED,
        P7_HOLD004_BACKEND_SUITE_STATUS_BLOCKED_BY_PREVIOUS_RED,
    }
)
P7_HOLD004_BACKEND_SUITE_GREEN_STATUSES: Final[frozenset[str]] = frozenset(
    {P7_HOLD004_BACKEND_SUITE_STATUS_PASS, P7_HOLD004_BACKEND_SUITE_STATUS_PASS_WITH_SKIPS}
)
P7_HOLD004_BACKEND_SUITE_TERMINAL_NON_GREEN_STATUSES: Final[frozenset[str]] = frozenset(
    {
        P7_HOLD004_BACKEND_SUITE_STATUS_FAIL,
        P7_HOLD004_BACKEND_SUITE_STATUS_TIMEOUT,
        P7_HOLD004_BACKEND_SUITE_STATUS_COLLECTION_FAILED,
        P7_HOLD004_BACKEND_SUITE_STATUS_INTERRUPTED,
    }
)
P7_HOLD004_BACKEND_SUITE_BACKEND_SPLIT_COMPATIBLE_STATUS_BY_STATUS: Final[dict[str, str]] = {
    P7_HOLD004_BACKEND_SUITE_STATUS_PASS: "green_confirmed",
    P7_HOLD004_BACKEND_SUITE_STATUS_PASS_WITH_SKIPS: "green_confirmed",
    P7_HOLD004_BACKEND_SUITE_STATUS_FAIL: "red_until_repaired",
    P7_HOLD004_BACKEND_SUITE_STATUS_TIMEOUT: "timeout_isolated",
    P7_HOLD004_BACKEND_SUITE_STATUS_COLLECTION_FAILED: "blocked",
    P7_HOLD004_BACKEND_SUITE_STATUS_NOT_RUN: "not_run",
    P7_HOLD004_BACKEND_SUITE_STATUS_INTERRUPTED: "blocked",
    P7_HOLD004_BACKEND_SUITE_STATUS_BLOCKED_BY_PREVIOUS_RED: "blocked",
}

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
P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_BLOCKED: Final = "BLOCKED_UNTIL_OFFICIAL_CAPTURE_RUN"
P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_GREEN: Final = "ADOPTABLE_OFFICIAL_GROUP_GREEN"
P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_RED: Final = "RECORDABLE_OFFICIAL_RED"
P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_TIMEOUT: Final = "RECORDABLE_OFFICIAL_TIMEOUT"
P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_COLLECTION_FAILED: Final = (
    "RECORDABLE_OFFICIAL_COLLECTION_FAILED"
)
P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_INTERRUPTED: Final = "RECORDABLE_OFFICIAL_INTERRUPTED"
P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_REJECTED_BASELINE_MISMATCH: Final = "REJECTED_BASELINE_MISMATCH"
P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_REJECTED_PLAN_MISMATCH: Final = "REJECTED_PLAN_MISMATCH"
P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_REJECTED_GROUP_OR_BATCH_MISMATCH: Final = (
    "REJECTED_GROUP_OR_BATCH_MISMATCH"
)
P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_REJECTED_COLLECT_COUNT_MISMATCH: Final = (
    "REJECTED_COLLECT_COUNT_MISMATCH"
)
P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_REJECTED_STATUS_OR_COUNTS_MISMATCH: Final = (
    "REJECTED_STATUS_OR_COUNTS_MISMATCH"
)
P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_REJECTED_BODY_OR_CONTRACT: Final = (
    "REJECTED_BODY_PAYLOAD_OR_CONTRACT_MUTATION"
)
P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_BLOCKED_BY_READINESS_GUARD: Final = (
    "BLOCKED_BY_RECEIVED_SNAPSHOT_READINESS_GUARD"
)
P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY: Final = "READY_FOR_OFFICIAL_CAPTURE_RUN"
P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_ITEM_FINGERPRINT_MISMATCH: Final = (
    "BLOCKED_BY_RECEIVED_SNAPSHOT_ITEM_FINGERPRINT_MISMATCH"
)
P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_SOURCE_IDENTITY_UNCLEAR: Final = (
    "BLOCKED_BY_RECEIVED_SNAPSHOT_SOURCE_IDENTITY_UNCLEAR"
)
P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_ACTIVE_BASELINE_NOT_CURRENT: Final = (
    "BLOCKED_BY_ACTIVE_BASELINE_NOT_RECEIVED_CURRENT"
)
P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_COLLECT_COUNT_MISMATCH: Final = (
    "BLOCKED_BY_COLLECT_COUNT_MISMATCH"
)
P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_FILE_FINGERPRINT_MISMATCH: Final = (
    "BLOCKED_BY_FILE_FINGERPRINT_MISMATCH"
)
P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_UNSTABLE_COLLECT: Final = (
    "BLOCKED_BY_UNSTABLE_COLLECT"
)
P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_ALLOWED_STATUSES: Final[frozenset[str]] = frozenset(
    {
        P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY,
        P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_ITEM_FINGERPRINT_MISMATCH,
        P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_SOURCE_IDENTITY_UNCLEAR,
        P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_ACTIVE_BASELINE_NOT_CURRENT,
        P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_COLLECT_COUNT_MISMATCH,
        P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_FILE_FINGERPRINT_MISMATCH,
        P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_UNSTABLE_COLLECT,
    }
)
P7_HOLD004_RECEIVED_SNAPSHOT_ITEM_FINGERPRINT_MISMATCH_BLOCKER_REF: Final = (
    "received_snapshot_collect_item_fingerprint_mismatch"
)
P7_HOLD004_RECEIVED_SNAPSHOT_SOURCE_IDENTITY_BLOCKER_REF: Final = "source_snapshot_ref_identity_unclear"
P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_GUARD_BLOCKER_REF: Final = (
    "official_group_02_capture_readiness_guard_blocked"
)
P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_ALLOWED_STATUSES: Final[frozenset[str]] = frozenset(
    {
        P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_BLOCKED,
        P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_GREEN,
        P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_RED,
        P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_TIMEOUT,
        P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_COLLECTION_FAILED,
        P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_INTERRUPTED,
        P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_REJECTED_BASELINE_MISMATCH,
        P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_REJECTED_PLAN_MISMATCH,
        P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_REJECTED_GROUP_OR_BATCH_MISMATCH,
        P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_REJECTED_COLLECT_COUNT_MISMATCH,
        P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_REJECTED_STATUS_OR_COUNTS_MISMATCH,
        P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_REJECTED_BODY_OR_CONTRACT,
        P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_BLOCKED_BY_READINESS_GUARD,
    }
)
P7_HOLD004_OFFICIAL_CAPTURE_RECORDABLE_ADOPTION_STATUSES: Final[frozenset[str]] = frozenset(
    {
        P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_GREEN,
        P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_RED,
        P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_TIMEOUT,
        P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_COLLECTION_FAILED,
        P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_INTERRUPTED,
    }
)

_REQUIRED_BASE_FOLLOWUP_FIXES: Final[tuple[str, ...]] = (
    "full_backend_suite_green_unconfirmed",
)
_STATUS_DEFAULT_FOLLOWUP_FIXES: Final[dict[str, tuple[str, ...]]] = {
    P7_HOLD004_BACKEND_SUITE_STATUS_PASS: ("full_backend_suite_green_unconfirmed",),
    P7_HOLD004_BACKEND_SUITE_STATUS_PASS_WITH_SKIPS: (
        "group_green_with_skips_is_not_full_backend_suite_green",
        "full_backend_suite_green_unconfirmed",
    ),
    P7_HOLD004_BACKEND_SUITE_STATUS_FAIL: (
        "first_red_classification_required",
        "full_backend_suite_green_unconfirmed",
    ),
    P7_HOLD004_BACKEND_SUITE_STATUS_TIMEOUT: (
        "timeout_classification_required",
        "timeout_isolated_not_green",
        "full_backend_suite_green_unconfirmed",
    ),
    P7_HOLD004_BACKEND_SUITE_STATUS_COLLECTION_FAILED: (
        "collection_failed_blocks_execution",
        "full_backend_suite_green_unconfirmed",
    ),
    P7_HOLD004_BACKEND_SUITE_STATUS_NOT_RUN: (
        "backend_suite_group_execution_not_run",
        "full_backend_suite_green_unconfirmed",
    ),
    P7_HOLD004_BACKEND_SUITE_STATUS_INTERRUPTED: (
        "group_execution_interrupted",
        "full_backend_suite_green_unconfirmed",
    ),
    P7_HOLD004_BACKEND_SUITE_STATUS_BLOCKED_BY_PREVIOUS_RED: (
        "blocked_by_previous_red",
        "full_backend_suite_green_unconfirmed",
    ),
}
_STATUS_DEFAULT_REASON_CODES: Final[dict[str, tuple[str, ...]]] = {
    P7_HOLD004_BACKEND_SUITE_STATUS_PASS: ("group_green_confirmed_only",),
    P7_HOLD004_BACKEND_SUITE_STATUS_PASS_WITH_SKIPS: ("group_green_confirmed_with_skips_only",),
    P7_HOLD004_BACKEND_SUITE_STATUS_FAIL: (
        "backend_suite_group_failed",
        "first_red_classification_required",
    ),
    P7_HOLD004_BACKEND_SUITE_STATUS_TIMEOUT: (
        "backend_suite_group_timeout",
        "timeout_isolated_not_green",
    ),
    P7_HOLD004_BACKEND_SUITE_STATUS_COLLECTION_FAILED: ("backend_suite_group_collection_failed",),
    P7_HOLD004_BACKEND_SUITE_STATUS_NOT_RUN: ("backend_suite_group_not_run",),
    P7_HOLD004_BACKEND_SUITE_STATUS_INTERRUPTED: ("backend_suite_group_interrupted",),
    P7_HOLD004_BACKEND_SUITE_STATUS_BLOCKED_BY_PREVIOUS_RED: ("blocked_by_previous_red",),
}
_ALLOWED_TIMEOUT_PHASES: Final[frozenset[str]] = frozenset({"collect", "run", "teardown", "unknown"})
_ALLOWED_ELAPSED_BUCKETS: Final[frozenset[str]] = frozenset(
    {"", "under_budget", "near_budget", "over_budget", "unknown"}
)
_GROUP_DEFINITION_BY_ID: Final[dict[str, dict[str, Any]]] = {
    clean_identifier(definition.get("group_id"), max_length=120): dict(definition)
    for definition in P7_HOLD004_BACKEND_SUITE_GROUP_DEFINITIONS
}


def _release_closed_boundary() -> dict[str, bool]:
    return {key: False for key in _RELEASE_CLOSED_KEYS}


def _false_boundary_flags() -> dict[str, bool]:
    return {key: False for key in _BOUNDARY_FLAG_KEYS}


def _public_contract_boundary_flags() -> dict[str, bool]:
    flags = public_contract_flags()
    flags.update(_false_boundary_flags())
    return flags


def _coerce_non_negative_int(value: Any, *, default: int = 0) -> int:
    if value is None or value == "" or isinstance(value, bool):
        return int(default)
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return int(default)
    return max(0, number)


def _coerce_bool(value: Any) -> bool:
    return bool(value) if isinstance(value, bool) else False


def _normalize_status_identifier(value: Any) -> str:
    return clean_identifier(value, default="", max_length=80).upper()


def _normalize_run_kind(value: Any, *, status: str) -> str:
    if status == P7_HOLD004_BACKEND_SUITE_STATUS_NOT_RUN:
        return P7_HOLD004_BACKEND_SUITE_RUN_KIND_NOT_RUN
    run_kind = clean_identifier(value, default="", max_length=80).lower()
    if run_kind in P7_HOLD004_BACKEND_SUITE_ALLOWED_RUN_KINDS:
        return run_kind
    return P7_HOLD004_BACKEND_SUITE_RUN_KIND_CAPTURE


def _batch_ids_for_group(group_id: str, batch_count: int) -> list[str]:
    return [f"{group_id}_batch_{index:02d}" for index in range(1, batch_count + 1)]


def _definition_for_group(group_id: str) -> dict[str, Any]:
    definition = _GROUP_DEFINITION_BY_ID.get(group_id)
    if not definition:
        raise ValueError(f"unknown P7-HOLD-004 backend suite group id: {group_id}")
    return definition


def _expected_batch_ids_for_group(group_id: str) -> list[str]:
    definition = _definition_for_group(group_id)
    return _batch_ids_for_group(group_id, _coerce_non_negative_int(definition.get("planned_batch_count"), default=1))


def _default_batch_id_for_group(group_id: str) -> str:
    return _expected_batch_ids_for_group(group_id)[0]


def _timeout_budget_for_group(group_id: str) -> int:
    return _coerce_non_negative_int(_definition_for_group(group_id).get("timeout_budget_sec"), default=120)


def _execution_order_index_by_group_id() -> dict[str, int]:
    return {group_id: index for index, group_id in enumerate(P7_HOLD004_BACKEND_SUITE_EXECUTION_ORDER)}


def _current_group_02_counts() -> dict[str, int]:
    definition = _definition_for_group("group_02_p7_hold004")
    return {
        "file_count": _coerce_non_negative_int(definition.get("file_count"), default=0),
        "test_item_count": _coerce_non_negative_int(definition.get("test_item_count"), default=0),
    }


def _current_baseline_connection_payload(*, execution_summary_id: Any = "") -> dict[str, Any]:
    group_02_counts = _current_group_02_counts()
    return {
        "collect_baseline_id": P7_HOLD004_BACKEND_COLLECT_BASELINE_ID,
        "group_inventory_id": P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID,
        "execution_plan_id": P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID,
        "execution_summary_id": clean_identifier(
            execution_summary_id or P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_ID,
            max_length=160,
        ),
        "current_collect_file_count": P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT,
        "current_collect_test_item_count": P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT,
        "group_02_file_count": group_02_counts["file_count"],
        "group_02_test_item_count": group_02_counts["test_item_count"],
        "old_baseline_id": P7_HOLD004_PREVIOUS_BACKEND_COLLECT_BASELINE_ID,
        "old_baseline_used_as_current": False,
        "full_backend_suite_green_confirmed": False,
        "release_allowed": False,
        "body_free": True,
    }


def _current_baseline_boundary_fields(*, execution_summary_id: Any = "") -> dict[str, Any]:
    connection = _current_baseline_connection_payload(execution_summary_id=execution_summary_id)
    return {
        "current_collect_baseline_reconciled": True,
        "current_collect_baseline_connected": True,
        "current_group_inventory_connected": True,
        "current_execution_plan_connected": True,
        "previous_baseline_is_not_current": True,
        "old_baseline_not_used_as_current": True,
        "baseline_mismatch_blocks_execution": True,
        "current_collect_file_count": P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT,
        "current_collect_test_item_count": P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT,
        "backend_suite_group_02_file_count": connection["group_02_file_count"],
        "backend_suite_group_02_test_item_count": connection["group_02_test_item_count"],
        "backend_suite_group_02_count_current": (
            connection["group_02_file_count"] == 19
            and connection["group_02_test_item_count"] == 252
        ),
        "matrix_current_baseline_connection": connection,
    }


def _batch_sort_index(batch_id: Any, expected_batch_ids: list[str]) -> int:
    batch = clean_identifier(batch_id, max_length=160)
    try:
        return expected_batch_ids.index(batch)
    except ValueError:
        return len(expected_batch_ids) + 1


def _status_default_followups(status: str) -> list[str]:
    return list(_STATUS_DEFAULT_FOLLOWUP_FIXES.get(status, _REQUIRED_BASE_FOLLOWUP_FIXES))


def _status_default_reasons(status: str) -> list[str]:
    return list(_STATUS_DEFAULT_REASON_CODES.get(status, ("backend_suite_group_status_unknown",)))


def _observed_counts(observed_counts: Mapping[str, Any] | None, **overrides: Any) -> dict[str, int]:
    source = safe_mapping(observed_counts)
    keys = ("passed", "failed", "skipped", "warnings", "errors", "deselected")
    out = {key: _coerce_non_negative_int(source.get(key), default=0) for key in keys}
    for key in keys:
        if key in overrides and overrides[key] is not None:
            out[key] = _coerce_non_negative_int(overrides[key], default=0)
    return out


def normalize_p7_hold004_backend_suite_group_run_status(
    *,
    status: Any = None,
    pytest_exit_code: Any = None,
    observed_counts: Mapping[str, Any] | None = None,
    passed: Any = None,
    failed: Any = None,
    skipped: Any = None,
    warnings: Any = None,
    errors: Any = None,
    deselected: Any = None,
    timed_out: bool = False,
    interrupted: bool = False,
    collection_failed: bool = False,
) -> str:
    """Normalize a pytest group/batch outcome into the R4 status enum."""

    counts = _observed_counts(
        observed_counts,
        passed=passed,
        failed=failed,
        skipped=skipped,
        warnings=warnings,
        errors=errors,
        deselected=deselected,
    )
    if timed_out is True:
        return P7_HOLD004_BACKEND_SUITE_STATUS_TIMEOUT
    if interrupted is True:
        return P7_HOLD004_BACKEND_SUITE_STATUS_INTERRUPTED
    if collection_failed is True:
        return P7_HOLD004_BACKEND_SUITE_STATUS_COLLECTION_FAILED

    explicit_status = _normalize_status_identifier(status)
    if explicit_status in P7_HOLD004_BACKEND_SUITE_ALLOWED_STATUSES:
        return explicit_status

    exit_code = _coerce_non_negative_int(pytest_exit_code, default=-1)
    if exit_code == 0:
        if counts.get("skipped", 0) > 0:
            return P7_HOLD004_BACKEND_SUITE_STATUS_PASS_WITH_SKIPS
        return P7_HOLD004_BACKEND_SUITE_STATUS_PASS
    if exit_code == 1:
        return P7_HOLD004_BACKEND_SUITE_STATUS_FAIL
    if exit_code == 2:
        return P7_HOLD004_BACKEND_SUITE_STATUS_INTERRUPTED
    if exit_code == 4:
        return P7_HOLD004_BACKEND_SUITE_STATUS_COLLECTION_FAILED

    if counts.get("failed", 0) > 0 or counts.get("errors", 0) > 0:
        return P7_HOLD004_BACKEND_SUITE_STATUS_FAIL
    if counts.get("passed", 0) > 0:
        if counts.get("skipped", 0) > 0:
            return P7_HOLD004_BACKEND_SUITE_STATUS_PASS_WITH_SKIPS
        return P7_HOLD004_BACKEND_SUITE_STATUS_PASS
    return P7_HOLD004_BACKEND_SUITE_STATUS_NOT_RUN


def _build_first_failure(
    *,
    status: str,
    nodeid: Any,
    file_ref: Any,
    failure_kind: Any,
    owner_layer_candidate: Any,
) -> dict[str, Any]:
    present = status == P7_HOLD004_BACKEND_SUITE_STATUS_FAIL
    return {
        "present": present,
        "nodeid": clean_identifier(nodeid, max_length=240) if present else "",
        "file_ref": clean_identifier(file_ref, max_length=240) if present else "",
        "failure_kind": clean_identifier(failure_kind, default="", max_length=120) if present else "",
        "owner_layer_candidate": clean_identifier(owner_layer_candidate, default="", max_length=120)
        if present
        else "",
    }


def _build_timeout_capture(
    *,
    status: str,
    elapsed_sec_bucket: Any,
    last_known_phase: Any,
) -> dict[str, Any]:
    present = status == P7_HOLD004_BACKEND_SUITE_STATUS_TIMEOUT
    bucket = clean_identifier(elapsed_sec_bucket, default="unknown", max_length=80) if present else ""
    phase = clean_identifier(last_known_phase, default="unknown", max_length=80).lower() if present else ""
    if present and bucket not in _ALLOWED_ELAPSED_BUCKETS:
        bucket = "unknown"
    if present and phase not in _ALLOWED_TIMEOUT_PHASES:
        phase = "unknown"
    return {
        "present": present,
        "elapsed_sec_bucket": bucket,
        "last_known_phase": phase,
        "first_timeout_capture": present,
        "slow_group_candidate": present,
    }


def _assert_common_release_closed_and_body_free(data: Mapping[str, Any], *, source: str) -> None:
    for key in _RELEASE_CLOSED_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=false")
    unresolved_holds = set(dedupe_identifiers(data.get("unresolved_hold_refs"), limit=40, max_length=120))
    if P7_HOLD004_BACKEND_SUITE_HOLD_ID not in unresolved_holds:
        raise ValueError(f"{source} must keep P7-HOLD-004 unresolved")
    followups = set(dedupe_identifiers(data.get("required_followup_fixes"), limit=120, max_length=180))
    if "full_backend_suite_green_unconfirmed" not in followups:
        raise ValueError(f"{source} must keep full_backend_suite_green_unconfirmed followup")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must be body_free=true")
    assert_false_markers(safe_mapping(data.get("public_contract")), source=f"{source}.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source=f"{source}.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)


def build_p7_hold004_backend_suite_group_run_result(
    *,
    group_id: Any,
    batch_id: Any = None,
    run_kind: Any = P7_HOLD004_BACKEND_SUITE_RUN_KIND_CAPTURE,
    status: Any = None,
    pytest_exit_code: Any = None,
    observed_counts: Mapping[str, Any] | None = None,
    passed: Any = None,
    failed: Any = None,
    skipped: Any = None,
    warnings: Any = None,
    errors: Any = None,
    deselected: Any = None,
    timed_out: bool = False,
    interrupted: bool = False,
    collection_failed: bool = False,
    timeout_budget_sec: Any = None,
    first_failure_nodeid: Any = "",
    first_failure_file_ref: Any = "",
    failure_kind: Any = "",
    owner_layer_candidate: Any = "",
    elapsed_sec_bucket: Any = "unknown",
    last_known_phase: Any = "unknown",
    reason_codes: Iterable[Any] | None = None,
    required_followup_fixes: Iterable[Any] | None = None,
    plan: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one body-free R4 group/batch run result material."""

    plan_material = safe_mapping(plan) if plan is not None else build_p7_hold004_backend_suite_execution_plan()
    assert_p7_hold004_backend_suite_execution_plan_contract(plan_material)

    normalized_group_id = clean_identifier(group_id, default="", max_length=120)
    if normalized_group_id not in P7_HOLD004_BACKEND_SUITE_GROUP_IDS:
        raise ValueError("R4 group run result requires a known group_id")
    expected_batch_ids = _expected_batch_ids_for_group(normalized_group_id)
    normalized_batch_id = clean_identifier(
        batch_id,
        default=_default_batch_id_for_group(normalized_group_id),
        max_length=160,
    )
    counts = _observed_counts(
        observed_counts,
        passed=passed,
        failed=failed,
        skipped=skipped,
        warnings=warnings,
        errors=errors,
        deselected=deselected,
    )
    normalized_status = normalize_p7_hold004_backend_suite_group_run_status(
        status=status,
        pytest_exit_code=pytest_exit_code,
        observed_counts=counts,
        timed_out=timed_out,
        interrupted=interrupted,
        collection_failed=collection_failed,
    )
    normalized_run_kind = _normalize_run_kind(run_kind, status=normalized_status)
    timeout_budget = _coerce_non_negative_int(timeout_budget_sec, default=_timeout_budget_for_group(normalized_group_id))
    if timeout_budget <= 0:
        timeout_budget = _timeout_budget_for_group(normalized_group_id)

    first_failure = _build_first_failure(
        status=normalized_status,
        nodeid=first_failure_nodeid,
        file_ref=first_failure_file_ref,
        failure_kind=failure_kind,
        owner_layer_candidate=owner_layer_candidate,
    )
    timeout_capture = _build_timeout_capture(
        status=normalized_status,
        elapsed_sec_bucket=elapsed_sec_bucket,
        last_known_phase=last_known_phase,
    )
    default_reasons = _status_default_reasons(normalized_status)
    default_followups = _status_default_followups(normalized_status)
    green_status = normalized_status in P7_HOLD004_BACKEND_SUITE_GREEN_STATUSES

    material = {
        "schema_version": P7_HOLD004_BACKEND_SUITE_GROUP_RUN_RESULT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_R4_R5_STEP,
        "implementation_step": P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_R4_R5_STEP,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "run_result_id": f"p7_hold004_{normalized_group_id}_{normalized_batch_id}_{normalized_run_kind}_20260615",
        "plan_id": plan_material.get("plan_id"),
        "inventory_id": plan_material.get("inventory_id"),
        "collect_baseline_id": plan_material.get("collect_baseline_id"),
        "source_mode": P7_SOURCE_MODE,
        "source_snapshot_ref": P7_HOLD004_BACKEND_R4_R5_SOURCE_SNAPSHOT_REF,
        "git_checked": P7_GIT_CHECKED,
        **_current_baseline_boundary_fields(execution_summary_id=""),
        "group_id": normalized_group_id,
        "batch_id": normalized_batch_id,
        "expected_batch_ids": list(expected_batch_ids),
        "run_kind": normalized_run_kind,
        "status": normalized_status,
        "backend_split_compatible_status": P7_HOLD004_BACKEND_SUITE_BACKEND_SPLIT_COMPATIBLE_STATUS_BY_STATUS[
            normalized_status
        ],
        "timeout_budget_sec": timeout_budget,
        "observed_counts": counts,
        "first_failure": first_failure,
        "timeout_capture": timeout_capture,
        "red_classification_required": normalized_status == P7_HOLD004_BACKEND_SUITE_STATUS_FAIL,
        "timeout_classification_required": normalized_status == P7_HOLD004_BACKEND_SUITE_STATUS_TIMEOUT,
        "timeout_is_green": False,
        "timeout_is_immediate_fail": False,
        "timeout_requires_long_run_classification": normalized_status == P7_HOLD004_BACKEND_SUITE_STATUS_TIMEOUT,
        "reason_codes": dedupe_identifiers(list(reason_codes or []) + default_reasons, limit=80, max_length=160),
        "can_claim_group_green": green_status,
        "can_claim_full_backend_suite_green": False,
        "raw_traceback_included": False,
        "terminal_output_retained": False,
        "stdout_retained": False,
        "stderr_retained": False,
        **_release_closed_boundary(),
        "unresolved_hold_refs": [P7_HOLD004_BACKEND_SUITE_HOLD_ID],
        "required_followup_fixes": dedupe_identifiers(
            list(required_followup_fixes or []) + default_followups,
            limit=120,
            max_length=180,
        ),
        "public_contract": _public_contract_boundary_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
        "body_free": True,
    }
    assert_p7_hold004_backend_suite_group_run_result_contract(material)
    return material


def assert_p7_hold004_backend_suite_group_run_result_contract(material: Mapping[str, Any]) -> bool:
    """Validate a R4 group/batch run result without leaking output bodies."""

    data = safe_mapping(material)
    source = "p7_hold004_backend_suite_group_run_result"
    if data.get("schema_version") != P7_HOLD004_BACKEND_SUITE_GROUP_RUN_RESULT_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 backend group run result schema_version changed")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError("P7-HOLD-004 backend group run result must stay in P7-HOLD-004 scope")
    if data.get("implementation_step") != P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_R4_R5_STEP:
        raise ValueError("P7-HOLD-004 backend group run result implementation_step changed")
    if data.get("plan_id") != P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID:
        raise ValueError("P7-HOLD-004 backend group run result must be tied to the R3 execution plan")
    if data.get("inventory_id") != P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID:
        raise ValueError("P7-HOLD-004 backend group run result must be tied to the R2 inventory")
    if data.get("collect_baseline_id") != P7_HOLD004_BACKEND_COLLECT_BASELINE_ID:
        raise ValueError("P7-HOLD-004 backend group run result must be tied to the R1 collect baseline")
    if data.get("source_mode") != P7_SOURCE_MODE or data.get("source_snapshot_ref") != P7_HOLD004_BACKEND_R4_R5_SOURCE_SNAPSHOT_REF:
        raise ValueError("P7-HOLD-004 backend group run result must stay on the R4/R5 local snapshot")
    if data.get("git_checked") is not False:
        raise ValueError("P7-HOLD-004 backend group run result must not claim GitHub verification")

    for key in (
        "current_collect_baseline_reconciled",
        "current_collect_baseline_connected",
        "current_group_inventory_connected",
        "current_execution_plan_connected",
        "previous_baseline_is_not_current",
        "old_baseline_not_used_as_current",
        "baseline_mismatch_blocks_execution",
        "backend_suite_group_02_count_current",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 backend execution material current baseline boundary {key} must be true")
    if data.get("current_collect_file_count") != P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT:
        raise ValueError("P7-HOLD-004 backend execution material current collect file count changed")
    if data.get("current_collect_test_item_count") != P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT:
        raise ValueError("P7-HOLD-004 backend execution material current collect test item count changed")
    if data.get("backend_suite_group_02_file_count") != 19 or data.get("backend_suite_group_02_test_item_count") != 252:
        raise ValueError("P7-HOLD-004 backend execution material must keep current group_02 counts")
    connection = safe_mapping(data.get("matrix_current_baseline_connection"))
    if connection.get("collect_baseline_id") != P7_HOLD004_BACKEND_COLLECT_BASELINE_ID:
        raise ValueError("P7-HOLD-004 backend execution material current baseline connection collect id mismatch")
    if connection.get("old_baseline_used_as_current") is not False:
        raise ValueError("P7-HOLD-004 backend execution material must not use old baseline as current")

    group_id = clean_identifier(data.get("group_id"), max_length=120)
    if group_id not in P7_HOLD004_BACKEND_SUITE_GROUP_IDS:
        raise ValueError("P7-HOLD-004 backend group run result group_id changed")
    expected_batch_ids = _expected_batch_ids_for_group(group_id)
    batch_id = clean_identifier(data.get("batch_id"), max_length=160)
    if batch_id not in expected_batch_ids:
        raise ValueError("P7-HOLD-004 backend group run result batch_id must belong to its group")
    if data.get("expected_batch_ids") != expected_batch_ids:
        raise ValueError("P7-HOLD-004 backend group run result expected_batch_ids changed")

    run_kind = clean_identifier(data.get("run_kind"), max_length=80).lower()
    status = _normalize_status_identifier(data.get("status"))
    if run_kind not in P7_HOLD004_BACKEND_SUITE_ALLOWED_RUN_KINDS:
        raise ValueError("P7-HOLD-004 backend group run result run_kind changed")
    if status not in P7_HOLD004_BACKEND_SUITE_ALLOWED_STATUSES:
        raise ValueError("P7-HOLD-004 backend group run result status changed")
    if data.get("backend_split_compatible_status") != P7_HOLD004_BACKEND_SUITE_BACKEND_SPLIT_COMPATIBLE_STATUS_BY_STATUS[status]:
        raise ValueError("P7-HOLD-004 backend group run result compatible status changed")
    if status == P7_HOLD004_BACKEND_SUITE_STATUS_NOT_RUN and run_kind != P7_HOLD004_BACKEND_SUITE_RUN_KIND_NOT_RUN:
        raise ValueError("NOT_RUN group result must use run_kind=not_run")
    if status != P7_HOLD004_BACKEND_SUITE_STATUS_NOT_RUN and run_kind == P7_HOLD004_BACKEND_SUITE_RUN_KIND_NOT_RUN:
        raise ValueError("executed group result must not use run_kind=not_run")

    timeout_budget = _coerce_non_negative_int(data.get("timeout_budget_sec"), default=0)
    if data.get("timeout_budget_sec") != timeout_budget or timeout_budget <= 0:
        raise ValueError("P7-HOLD-004 backend group run result timeout_budget_sec must be a positive integer")
    counts = safe_mapping(data.get("observed_counts"))
    for count_key in ("passed", "failed", "skipped", "warnings", "errors", "deselected"):
        count = _coerce_non_negative_int(counts.get(count_key), default=-1)
        if counts.get(count_key) != count or count < 0:
            raise ValueError(f"P7-HOLD-004 backend group run result observed_counts.{count_key} invalid")

    first_failure = safe_mapping(data.get("first_failure"))
    timeout_capture = safe_mapping(data.get("timeout_capture"))
    if first_failure.get("present") is not (status == P7_HOLD004_BACKEND_SUITE_STATUS_FAIL):
        raise ValueError("P7-HOLD-004 backend group run result first_failure.present mismatch")
    if timeout_capture.get("present") is not (status == P7_HOLD004_BACKEND_SUITE_STATUS_TIMEOUT):
        raise ValueError("P7-HOLD-004 backend group run result timeout_capture.present mismatch")

    if status == P7_HOLD004_BACKEND_SUITE_STATUS_FAIL:
        if counts.get("failed", 0) + counts.get("errors", 0) <= 0:
            raise ValueError("FAIL group result must record at least one failed/error count")
        for key in ("nodeid", "file_ref", "failure_kind", "owner_layer_candidate"):
            if not clean_identifier(first_failure.get(key), max_length=240):
                raise ValueError(f"FAIL group result must keep body-free first_failure.{key}")
        if data.get("red_classification_required") is not True:
            raise ValueError("FAIL group result must require red classification")
    else:
        if any(first_failure.get(key) for key in ("nodeid", "file_ref", "failure_kind", "owner_layer_candidate")):
            raise ValueError("non-FAIL group result must not keep first failure identifiers")
        if data.get("red_classification_required") is not False:
            raise ValueError("non-FAIL group result must not require red classification")

    if status == P7_HOLD004_BACKEND_SUITE_STATUS_TIMEOUT:
        if timeout_capture.get("first_timeout_capture") is not True:
            raise ValueError("TIMEOUT group result must record first_timeout_capture=true")
        if timeout_capture.get("slow_group_candidate") is not True:
            raise ValueError("TIMEOUT group result must record slow_group_candidate=true")
        if timeout_capture.get("elapsed_sec_bucket") not in _ALLOWED_ELAPSED_BUCKETS - {""}:
            raise ValueError("TIMEOUT group result elapsed_sec_bucket invalid")
        if timeout_capture.get("last_known_phase") not in _ALLOWED_TIMEOUT_PHASES:
            raise ValueError("TIMEOUT group result last_known_phase invalid")
        if data.get("timeout_classification_required") is not True:
            raise ValueError("TIMEOUT group result must require timeout classification")
        if data.get("timeout_requires_long_run_classification") is not True:
            raise ValueError("TIMEOUT group result must require long-run timeout classification")
    else:
        if timeout_capture.get("elapsed_sec_bucket") not in ("", None):
            raise ValueError("non-TIMEOUT group result must not retain timeout elapsed bucket")
        if timeout_capture.get("last_known_phase") not in ("", None):
            raise ValueError("non-TIMEOUT group result must not retain timeout phase")
        if timeout_capture.get("first_timeout_capture") not in (False, None):
            raise ValueError("non-TIMEOUT group result must not claim first timeout capture")
        if timeout_capture.get("slow_group_candidate") not in (False, None):
            raise ValueError("non-TIMEOUT group result must not claim slow group candidate")
        if data.get("timeout_classification_required") is not False:
            raise ValueError("non-TIMEOUT group result must not require timeout classification")
        if data.get("timeout_requires_long_run_classification") is not False:
            raise ValueError("non-TIMEOUT group result must not require long-run timeout classification")

    if data.get("timeout_is_green") is not False:
        raise ValueError("P7-HOLD-004 backend group run result must never mark timeout as green")
    if data.get("timeout_is_immediate_fail") is not False:
        raise ValueError("P7-HOLD-004 backend group run result must not treat timeout as immediate fail")

    green_status = status in P7_HOLD004_BACKEND_SUITE_GREEN_STATUSES
    if data.get("can_claim_group_green") is not green_status:
        raise ValueError("P7-HOLD-004 backend group result group-green claim mismatch")
    if status == P7_HOLD004_BACKEND_SUITE_STATUS_PASS and (counts.get("failed", 0) or counts.get("errors", 0)):
        raise ValueError("PASS group result must not include failed/error counts")
    if status == P7_HOLD004_BACKEND_SUITE_STATUS_PASS_WITH_SKIPS and counts.get("skipped", 0) <= 0:
        raise ValueError("PASS_WITH_SKIPS group result must record skipped_count")
    if status in (P7_HOLD004_BACKEND_SUITE_STATUS_NOT_RUN, P7_HOLD004_BACKEND_SUITE_STATUS_BLOCKED_BY_PREVIOUS_RED):
        if data.get("can_claim_group_green") is not False:
            raise ValueError("NOT_RUN/BLOCKED result must not claim group green")

    for forbidden_flag in ("raw_traceback_included", "terminal_output_retained", "stdout_retained", "stderr_retained"):
        if data.get(forbidden_flag) is not False:
            raise ValueError(f"P7-HOLD-004 backend group run result must keep {forbidden_flag}=false")
    if data.get("can_claim_full_backend_suite_green") is not False:
        raise ValueError("P7-HOLD-004 backend group run result must not claim full backend suite green")

    reason_codes = dedupe_identifiers(data.get("reason_codes"), limit=80, max_length=160)
    if not reason_codes:
        raise ValueError("P7-HOLD-004 backend group run result must keep body-free reason_codes")
    followups = set(dedupe_identifiers(data.get("required_followup_fixes"), limit=120, max_length=180))
    for required_followup in _STATUS_DEFAULT_FOLLOWUP_FIXES[status]:
        if required_followup not in followups:
            raise ValueError(f"P7-HOLD-004 backend group run result missing followup {required_followup}")

    _assert_common_release_closed_and_body_free(data, source=source)
    return True


def _group_results_sorted(run_results: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    order_by_group = _execution_order_index_by_group_id()
    normalized: list[dict[str, Any]] = []
    for result in run_results:
        material = safe_mapping(result)
        assert_p7_hold004_backend_suite_group_run_result_contract(material)
        normalized.append(material)

    def sort_key(material: Mapping[str, Any]) -> tuple[int, int, str]:
        group_id = clean_identifier(material.get("group_id"), max_length=120)
        expected_batches = _expected_batch_ids_for_group(group_id)
        return (
            order_by_group.get(group_id, 10_000),
            _batch_sort_index(material.get("batch_id"), expected_batches),
            clean_identifier(material.get("batch_id"), max_length=160),
        )

    return sorted(normalized, key=sort_key)


def _aggregate_group_status(group_id: str, results: list[dict[str, Any]]) -> tuple[str, bool]:
    if not results:
        return P7_HOLD004_BACKEND_SUITE_STATUS_NOT_RUN, False

    statuses = [_normalize_status_identifier(result.get("status")) for result in results]
    priority = (
        P7_HOLD004_BACKEND_SUITE_STATUS_FAIL,
        P7_HOLD004_BACKEND_SUITE_STATUS_TIMEOUT,
        P7_HOLD004_BACKEND_SUITE_STATUS_COLLECTION_FAILED,
        P7_HOLD004_BACKEND_SUITE_STATUS_INTERRUPTED,
        P7_HOLD004_BACKEND_SUITE_STATUS_BLOCKED_BY_PREVIOUS_RED,
    )
    for status in priority:
        if status in statuses:
            return status, False

    expected_batch_ids = set(_expected_batch_ids_for_group(group_id))
    recorded_batch_ids = {clean_identifier(result.get("batch_id"), max_length=160) for result in results}
    all_expected_batches_recorded = expected_batch_ids.issubset(recorded_batch_ids)
    if all_expected_batches_recorded and all(status in P7_HOLD004_BACKEND_SUITE_GREEN_STATUSES for status in statuses):
        if P7_HOLD004_BACKEND_SUITE_STATUS_PASS_WITH_SKIPS in statuses:
            return P7_HOLD004_BACKEND_SUITE_STATUS_PASS_WITH_SKIPS, False
        return P7_HOLD004_BACKEND_SUITE_STATUS_PASS, False
    return P7_HOLD004_BACKEND_SUITE_STATUS_NOT_RUN, bool(results)


def _status_list(group_statuses: Mapping[str, str], target_status: str) -> list[str]:
    return [group_id for group_id in P7_HOLD004_BACKEND_SUITE_GROUP_IDS if group_statuses.get(group_id) == target_status]


def _first_failure_from_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    for result in results:
        if result.get("status") == P7_HOLD004_BACKEND_SUITE_STATUS_FAIL:
            first_failure = safe_mapping(result.get("first_failure"))
            return {
                "present": True,
                "group_id": clean_identifier(result.get("group_id"), max_length=120),
                "batch_id": clean_identifier(result.get("batch_id"), max_length=160),
                "nodeid": clean_identifier(first_failure.get("nodeid"), max_length=240),
                "file_ref": clean_identifier(first_failure.get("file_ref"), max_length=240),
                "failure_kind": clean_identifier(first_failure.get("failure_kind"), max_length=120),
                "owner_layer_candidate": clean_identifier(first_failure.get("owner_layer_candidate"), max_length=120),
            }
    return {
        "present": False,
        "group_id": "",
        "batch_id": "",
        "nodeid": "",
        "file_ref": "",
        "failure_kind": "",
        "owner_layer_candidate": "",
    }


def _first_timeout_from_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    for result in results:
        if result.get("status") == P7_HOLD004_BACKEND_SUITE_STATUS_TIMEOUT:
            timeout_capture = safe_mapping(result.get("timeout_capture"))
            return {
                "present": True,
                "group_id": clean_identifier(result.get("group_id"), max_length=120),
                "batch_id": clean_identifier(result.get("batch_id"), max_length=160),
                "timeout_budget_sec": _coerce_non_negative_int(result.get("timeout_budget_sec"), default=0),
                "elapsed_sec_bucket": clean_identifier(timeout_capture.get("elapsed_sec_bucket"), max_length=80),
                "last_known_phase": clean_identifier(timeout_capture.get("last_known_phase"), max_length=80),
            }
    return {
        "present": False,
        "group_id": "",
        "batch_id": "",
        "timeout_budget_sec": 0,
        "elapsed_sec_bucket": "",
        "last_known_phase": "",
    }


def build_p7_hold004_backend_suite_execution_summary(
    *,
    plan: Mapping[str, Any] | None = None,
    run_results: Iterable[Mapping[str, Any]] | None = None,
    required_followup_fixes: Iterable[Any] | None = None,
) -> dict[str, Any]:
    """Build the body-free R5 execution summary from R4 group results."""

    plan_material = safe_mapping(plan) if plan is not None else build_p7_hold004_backend_suite_execution_plan()
    assert_p7_hold004_backend_suite_execution_plan_contract(plan_material)
    sorted_results = _group_results_sorted(run_results or [])
    results_by_group: dict[str, list[dict[str, Any]]] = {group_id: [] for group_id in P7_HOLD004_BACKEND_SUITE_GROUP_IDS}
    for result in sorted_results:
        results_by_group[clean_identifier(result.get("group_id"), max_length=120)].append(result)

    group_statuses: dict[str, str] = {}
    partial_group_ids: list[str] = []
    for group_id in P7_HOLD004_BACKEND_SUITE_GROUP_IDS:
        status, partial = _aggregate_group_status(group_id, results_by_group[group_id])
        group_statuses[group_id] = status
        if partial:
            partial_group_ids.append(group_id)

    failed_group_ids = _status_list(group_statuses, P7_HOLD004_BACKEND_SUITE_STATUS_FAIL)
    timeout_group_ids = _status_list(group_statuses, P7_HOLD004_BACKEND_SUITE_STATUS_TIMEOUT)
    collection_failed_group_ids = _status_list(group_statuses, P7_HOLD004_BACKEND_SUITE_STATUS_COLLECTION_FAILED)
    interrupted_group_ids = _status_list(group_statuses, P7_HOLD004_BACKEND_SUITE_STATUS_INTERRUPTED)
    blocked_group_ids = _status_list(group_statuses, P7_HOLD004_BACKEND_SUITE_STATUS_BLOCKED_BY_PREVIOUS_RED)
    not_run_group_ids = _status_list(group_statuses, P7_HOLD004_BACKEND_SUITE_STATUS_NOT_RUN)
    green_group_ids = [
        group_id
        for group_id in P7_HOLD004_BACKEND_SUITE_GROUP_IDS
        if group_statuses[group_id] in P7_HOLD004_BACKEND_SUITE_GREEN_STATUSES
    ]
    all_groups_executed = not (not_run_group_ids or blocked_group_ids or partial_group_ids)
    split_all_groups_green_confirmed = (
        all_groups_executed
        and len(green_group_ids) == len(P7_HOLD004_BACKEND_SUITE_GROUP_IDS)
        and not (failed_group_ids or timeout_group_ids or collection_failed_group_ids or interrupted_group_ids)
    )

    followups = ["full_backend_suite_green_unconfirmed"]
    if not_run_group_ids:
        followups.append("backend_suite_group_execution_not_run")
    if partial_group_ids:
        followups.append("backend_suite_group_execution_partial")
    if failed_group_ids:
        followups.append("first_red_classification_required")
    if timeout_group_ids:
        followups.append("timeout_classification_required")
        followups.append("timeout_isolated_not_green")
    if collection_failed_group_ids:
        followups.append("collection_failed_blocks_execution")
    if interrupted_group_ids:
        followups.append("group_execution_interrupted")
    if blocked_group_ids:
        followups.append("blocked_by_previous_red")
    if split_all_groups_green_confirmed:
        followups.append("split_green_is_not_full_backend_suite_green")
        followups.append("un_split_full_backend_suite_green_not_confirmed")

    material = {
        "schema_version": P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_R4_R5_STEP,
        "implementation_step": P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_R4_R5_STEP,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "summary_id": P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_ID,
        "collect_baseline_id": plan_material.get("collect_baseline_id"),
        "inventory_id": plan_material.get("inventory_id"),
        "plan_id": plan_material.get("plan_id"),
        "source_mode": P7_SOURCE_MODE,
        "source_snapshot_ref": P7_HOLD004_BACKEND_R4_R5_SOURCE_SNAPSHOT_REF,
        "git_checked": P7_GIT_CHECKED,
        **_current_baseline_boundary_fields(execution_summary_id=P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_ID),
        "expected_group_count": len(P7_HOLD004_BACKEND_SUITE_GROUP_IDS),
        "expected_total_batch_count": P7_HOLD004_BACKEND_SUITE_TOTAL_BATCH_COUNT,
        "recorded_run_result_count": len(sorted_results),
        "recorded_batch_statuses": [
            {
                "group_id": clean_identifier(result.get("group_id"), max_length=120),
                "batch_id": clean_identifier(result.get("batch_id"), max_length=160),
                "status": _normalize_status_identifier(result.get("status")),
            }
            for result in sorted_results
        ],
        "group_statuses": group_statuses,
        "all_groups_executed": all_groups_executed,
        "split_all_groups_green_confirmed": split_all_groups_green_confirmed,
        "green_group_ids": green_group_ids,
        "failed_group_ids": failed_group_ids,
        "timeout_group_ids": timeout_group_ids,
        "collection_failed_group_ids": collection_failed_group_ids,
        "interrupted_group_ids": interrupted_group_ids,
        "blocked_group_ids": blocked_group_ids,
        "not_run_group_ids": not_run_group_ids,
        "partial_group_ids": partial_group_ids,
        "first_red": _first_failure_from_results(sorted_results),
        "first_timeout": _first_timeout_from_results(sorted_results),
        "group_run_results_recorded": bool(sorted_results),
        "terminal_output_retained": False,
        "raw_traceback_included": False,
        "stdout_retained": False,
        "stderr_retained": False,
        **_release_closed_boundary(),
        "unresolved_hold_refs": [P7_HOLD004_BACKEND_SUITE_HOLD_ID],
        "required_followup_fixes": dedupe_identifiers(
            list(required_followup_fixes or []) + followups,
            limit=160,
            max_length=180,
        ),
        "public_contract": _public_contract_boundary_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
        "body_free": True,
    }
    assert_p7_hold004_backend_suite_execution_summary_contract(material)
    return material



def _official_group02_definition() -> dict[str, Any]:
    return _definition_for_group(P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID)


def _official_group02_expected_counts() -> dict[str, int]:
    definition = _official_group02_definition()
    return {
        "file_count": _coerce_non_negative_int(definition.get("file_count"), default=0),
        "test_item_count": _coerce_non_negative_int(definition.get("test_item_count"), default=0),
        "warnings_count": P7_HOLD004_GROUP02_OFFICIAL_WARNINGS_COUNT,
    }


def _official_group02_command_shape() -> dict[str, Any]:
    return {
        "collect_command_id": P7_HOLD004_GROUP02_OFFICIAL_COLLECT_COMMAND_ID,
        "capture_command_id": P7_HOLD004_GROUP02_OFFICIAL_CAPTURE_COMMAND_ID,
        "cwd_ref": "mashos-api/ai",
        "environment_refs": [
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1",
            "PYTHONPATH=services/ai_inference",
        ],
        "args": [
            "pytest",
            "-q",
            "--tb=short",
            "-p",
            "pytest_asyncio.plugin",
            "tests/test_emlis_ai_p7_hold004_*.py",
        ],
        "terminal_output_retained": False,
        "stdout_retained": False,
        "stderr_retained": False,
        "raw_traceback_included": False,
        "body_free": True,
    }


def _official_group02_adoption_rule_conditions(plan_material: Mapping[str, Any]) -> dict[str, bool]:
    expected = _official_group02_expected_counts()
    first_group_id = clean_identifier(P7_HOLD004_BACKEND_SUITE_EXECUTION_ORDER[0], max_length=120)
    return {
        "collect_baseline_builder_current": plan_material.get("collect_baseline_id")
        == P7_HOLD004_BACKEND_COLLECT_BASELINE_ID,
        "group_inventory_total_matches_current_collect": plan_material.get("inventory_id")
        == P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID,
        "execution_plan_current": plan_material.get("plan_id") == P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID,
        "first_capture_group_is_group_02": first_group_id == P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID,
        "group_02_inventory_current": expected["file_count"] == P7_HOLD004_GROUP02_OFFICIAL_FILE_COUNT
        and expected["test_item_count"] == P7_HOLD004_GROUP02_OFFICIAL_TEST_ITEM_COUNT,
        "group_02_collect_only_count_required": True,
        "run_result_material_required": True,
        "terminal_output_excluded_from_material": True,
        "stdout_stderr_excluded_from_material": True,
        "traceback_body_excluded_from_material": True,
        "pass_result_group_green_only": True,
    }


def build_p7_hold004_official_group02_capture_adoption_rule(
    *,
    plan: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the R19 body-free rule for adopting a refreshed group_02 capture."""

    plan_material = safe_mapping(plan) if plan is not None else build_p7_hold004_backend_suite_execution_plan()
    assert_p7_hold004_backend_suite_execution_plan_contract(plan_material)
    expected = _official_group02_expected_counts()
    group_definition = _official_group02_definition()
    material = {
        "schema_version": P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_ADOPTION_RULE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_ADOPTION_STEP,
        "implementation_step": P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_ADOPTION_STEP,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "adoption_rule_id": P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_ADOPTION_RULE_ID,
        "collect_baseline_id": plan_material.get("collect_baseline_id"),
        "inventory_id": plan_material.get("inventory_id"),
        "plan_id": plan_material.get("plan_id"),
        "source_mode": P7_SOURCE_MODE,
        "source_snapshot_ref": P7_HOLD004_BACKEND_R4_R5_SOURCE_SNAPSHOT_REF,
        "git_checked": P7_GIT_CHECKED,
        **_current_baseline_boundary_fields(execution_summary_id=P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_ID),
        "group_id": P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID,
        "batch_id": P7_HOLD004_GROUP02_OFFICIAL_BATCH_ID,
        "run_kind": P7_HOLD004_BACKEND_SUITE_RUN_KIND_CAPTURE,
        "first_capture_group_id": clean_identifier(P7_HOLD004_BACKEND_SUITE_EXECUTION_ORDER[0], max_length=120),
        "expected_group_file_count": expected["file_count"],
        "expected_group_test_item_count": expected["test_item_count"],
        "expected_collect_only_test_item_count": P7_HOLD004_GROUP02_OFFICIAL_TEST_ITEM_COUNT,
        "expected_warning_count": expected["warnings_count"],
        "expected_timeout_budget_sec": _coerce_non_negative_int(group_definition.get("timeout_budget_sec"), default=120),
        "expected_batch_ids": _expected_batch_ids_for_group(P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID),
        "official_command_shape": _official_group02_command_shape(),
        "accepted_recordable_statuses": [
            P7_HOLD004_BACKEND_SUITE_STATUS_PASS,
            P7_HOLD004_BACKEND_SUITE_STATUS_FAIL,
            P7_HOLD004_BACKEND_SUITE_STATUS_TIMEOUT,
            P7_HOLD004_BACKEND_SUITE_STATUS_COLLECTION_FAILED,
            P7_HOLD004_BACKEND_SUITE_STATUS_INTERRUPTED,
        ],
        "pass_result_expected_counts": {
            "passed": P7_HOLD004_GROUP02_OFFICIAL_TEST_ITEM_COUNT,
            "failed": 0,
            "skipped": 0,
            "warnings": P7_HOLD004_GROUP02_OFFICIAL_WARNINGS_COUNT,
            "errors": 0,
            "deselected": 0,
        },
        "capture_adoption_conditions": _official_group02_adoption_rule_conditions(plan_material),
        "official_capture_run_executed": False,
        "official_capture_result_recorded": False,
        "official_group_02_capture_green_confirmed": False,
        "can_claim_group_green": False,
        "can_claim_full_backend_suite_green": False,
        **_release_closed_boundary(),
        "unresolved_hold_refs": [P7_HOLD004_BACKEND_SUITE_HOLD_ID],
        "required_followup_fixes": [
            "official_group_02_capture_run_not_recorded",
            "full_backend_suite_green_unconfirmed",
        ],
        "public_contract": _public_contract_boundary_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
        "body_free": True,
    }
    assert_p7_hold004_official_group02_capture_adoption_rule_contract(material)
    return material


def assert_p7_hold004_official_group02_capture_adoption_rule_contract(material: Mapping[str, Any]) -> bool:
    """Validate the R19 official group_02 capture adoption rule material."""

    data = safe_mapping(material)
    source = "p7_hold004_official_group02_capture_adoption_rule"
    if data.get("schema_version") != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_ADOPTION_RULE_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 official group_02 adoption rule schema_version changed")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError("P7-HOLD-004 official group_02 adoption rule scope changed")
    if data.get("implementation_step") != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_ADOPTION_STEP:
        raise ValueError("P7-HOLD-004 official group_02 adoption rule implementation_step changed")
    if data.get("adoption_rule_id") != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_ADOPTION_RULE_ID:
        raise ValueError("P7-HOLD-004 official group_02 adoption rule id changed")
    if data.get("collect_baseline_id") != P7_HOLD004_BACKEND_COLLECT_BASELINE_ID:
        raise ValueError("P7-HOLD-004 official group_02 adoption rule must use current collect baseline")
    if data.get("inventory_id") != P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID:
        raise ValueError("P7-HOLD-004 official group_02 adoption rule must use current inventory")
    if data.get("plan_id") != P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID:
        raise ValueError("P7-HOLD-004 official group_02 adoption rule must use current execution plan")
    if data.get("source_mode") != P7_SOURCE_MODE or data.get("source_snapshot_ref") != P7_HOLD004_BACKEND_R4_R5_SOURCE_SNAPSHOT_REF:
        raise ValueError("P7-HOLD-004 official group_02 adoption rule local snapshot changed")
    if data.get("git_checked") is not False:
        raise ValueError("P7-HOLD-004 official group_02 adoption rule must not claim GitHub verification")
    for key in (
        "current_collect_baseline_reconciled",
        "current_collect_baseline_connected",
        "current_group_inventory_connected",
        "current_execution_plan_connected",
        "previous_baseline_is_not_current",
        "old_baseline_not_used_as_current",
        "baseline_mismatch_blocks_execution",
        "backend_suite_group_02_count_current",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 official group_02 adoption rule boundary {key} must be true")
    if data.get("group_id") != P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID:
        raise ValueError("P7-HOLD-004 official adoption rule must target group_02")
    if data.get("batch_id") != P7_HOLD004_GROUP02_OFFICIAL_BATCH_ID:
        raise ValueError("P7-HOLD-004 official adoption rule must target group_02 batch_01")
    if data.get("run_kind") != P7_HOLD004_BACKEND_SUITE_RUN_KIND_CAPTURE:
        raise ValueError("P7-HOLD-004 official adoption rule must require capture_run")
    if data.get("first_capture_group_id") != P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID:
        raise ValueError("P7-HOLD-004 official adoption rule first group changed")
    if data.get("expected_group_file_count") != P7_HOLD004_GROUP02_OFFICIAL_FILE_COUNT:
        raise ValueError("P7-HOLD-004 official adoption rule group_02 file count changed")
    if data.get("expected_group_test_item_count") != P7_HOLD004_GROUP02_OFFICIAL_TEST_ITEM_COUNT:
        raise ValueError("P7-HOLD-004 official adoption rule group_02 test count changed")
    if data.get("expected_collect_only_test_item_count") != P7_HOLD004_GROUP02_OFFICIAL_TEST_ITEM_COUNT:
        raise ValueError("P7-HOLD-004 official adoption rule collect-only count changed")
    if data.get("expected_warning_count") != P7_HOLD004_GROUP02_OFFICIAL_WARNINGS_COUNT:
        raise ValueError("P7-HOLD-004 official adoption rule warning count changed")
    if data.get("expected_timeout_budget_sec") != 120:
        raise ValueError("P7-HOLD-004 official adoption rule timeout budget changed")
    if data.get("expected_batch_ids") != [P7_HOLD004_GROUP02_OFFICIAL_BATCH_ID]:
        raise ValueError("P7-HOLD-004 official adoption rule expected batch changed")
    command_shape = safe_mapping(data.get("official_command_shape"))
    if command_shape.get("collect_command_id") != P7_HOLD004_GROUP02_OFFICIAL_COLLECT_COMMAND_ID:
        raise ValueError("P7-HOLD-004 official adoption rule collect command id changed")
    if command_shape.get("capture_command_id") != P7_HOLD004_GROUP02_OFFICIAL_CAPTURE_COMMAND_ID:
        raise ValueError("P7-HOLD-004 official adoption rule capture command id changed")
    for forbidden_flag in ("terminal_output_retained", "stdout_retained", "stderr_retained", "raw_traceback_included"):
        if command_shape.get(forbidden_flag) is not False:
            raise ValueError("P7-HOLD-004 official adoption command must remain body-free")
    conditions = safe_mapping(data.get("capture_adoption_conditions"))
    for key in (
        "collect_baseline_builder_current",
        "group_inventory_total_matches_current_collect",
        "execution_plan_current",
        "first_capture_group_is_group_02",
        "group_02_inventory_current",
        "group_02_collect_only_count_required",
        "run_result_material_required",
        "terminal_output_excluded_from_material",
        "stdout_stderr_excluded_from_material",
        "traceback_body_excluded_from_material",
        "pass_result_group_green_only",
    ):
        if conditions.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 official adoption rule condition {key} must be true")
    pass_counts = safe_mapping(data.get("pass_result_expected_counts"))
    if pass_counts != {
        "passed": P7_HOLD004_GROUP02_OFFICIAL_TEST_ITEM_COUNT,
        "failed": 0,
        "skipped": 0,
        "warnings": P7_HOLD004_GROUP02_OFFICIAL_WARNINGS_COUNT,
        "errors": 0,
        "deselected": 0,
    }:
        raise ValueError("P7-HOLD-004 official adoption rule pass counts changed")
    if data.get("official_capture_run_executed") is not False or data.get("official_capture_result_recorded") is not False:
        raise ValueError("P7-HOLD-004 official adoption rule must not claim run execution")
    if data.get("official_group_02_capture_green_confirmed") is not False:
        raise ValueError("P7-HOLD-004 official adoption rule must not claim group_02 green")
    if data.get("can_claim_group_green") is not False or data.get("can_claim_full_backend_suite_green") is not False:
        raise ValueError("P7-HOLD-004 official adoption rule must not claim green")
    _assert_common_release_closed_and_body_free(data, source=source)
    return True



def _is_post_adoption_received_snapshot_reconcile(material: Mapping[str, Any]) -> bool:
    return safe_mapping(material).get("schema_version") == P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_SCHEMA_VERSION


def _assert_post_adoption_received_snapshot_reconcile_like(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    source = "p7_hold004_post_adoption_received_snapshot_reconcile_like"
    if data.get("schema_version") != P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 post-adoption reconcile schema_version mismatch")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError("P7-HOLD-004 post-adoption reconcile scope mismatch")
    if data.get("reconcile_id") != P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_ID:
        raise ValueError("P7-HOLD-004 post-adoption reconcile id mismatch")
    if data.get("source_mode") != P7_SOURCE_MODE or data.get("git_checked") is not False:
        raise ValueError("P7-HOLD-004 post-adoption reconcile source boundary mismatch")
    for key in (
        "received_snapshot_baseline_fingerprint_reconciled",
        "source_snapshot_ref_current_for_received_zip",
        "active_baseline_accepts_received_nodeids",
        "post_adoption_reconcile_material_built",
        "collect_only_is_not_execution_green",
        "body_free",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 post-adoption reconcile must keep {key}=true")
    for key in (
        "received_snapshot_item_fingerprint_mismatch_unresolved",
        "historical_r21_r29_material_rewritten",
        "execution_green_confirmed",
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
            raise ValueError(f"P7-HOLD-004 post-adoption reconcile must keep {key}=false")
    comparison = safe_mapping(data.get("comparison"))
    for key in (
        "counts_match",
        "warnings_match",
        "test_files_fingerprint_match",
        "test_items_fingerprint_match",
        "source_snapshot_ref_matches_received_zip_ref",
        "source_snapshot_ref_current_for_received_zip",
        "active_baseline_accepts_received_nodeids",
    ):
        if comparison.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 post-adoption reconcile comparison {key} must be true")
    assert_false_markers(safe_mapping(data.get("public_contract")), source=f"{source}.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source=f"{source}.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)
    return True


def _assert_runtime_builder_refresh_status_like(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    source = "p7_hold004_runtime_builder_refresh_status_like"
    if data.get("schema_version") != P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 runtime builder refresh status schema_version mismatch")
    if data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID or data.get("phase") != P7_PHASE:
        raise ValueError("P7-HOLD-004 runtime builder refresh status scope mismatch")
    if data.get("refresh_status_id") != P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_ID:
        raise ValueError("P7-HOLD-004 runtime builder refresh status id mismatch")
    for key in (
        "active_baseline_update_applied_to_runtime_builders",
        "source_snapshot_ref_updated_in_active_builders",
        "current_collect_baseline_connected",
        "received_snapshot_baseline_fingerprint_reconciled",
        "source_snapshot_ref_current_for_received_zip",
        "active_baseline_accepts_received_nodeids",
        "collect_only_is_not_execution_green",
        "body_free",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 runtime builder refresh status must keep {key}=true")
    for key in (
        "received_snapshot_item_fingerprint_mismatch_unresolved",
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
            raise ValueError(f"P7-HOLD-004 runtime builder refresh status must keep {key}=false")
    if data.get("current_active_baseline_id") != P7_HOLD004_BACKEND_COLLECT_BASELINE_ID:
        raise ValueError("P7-HOLD-004 runtime builder refresh must use current collect baseline")
    assert_false_markers(safe_mapping(data.get("public_contract")), source=f"{source}.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source=f"{source}.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)
    return True


def _readiness_status_and_blockers(
    *,
    received_snapshot_reconcile: Mapping[str, Any],
    adoption_decision: Mapping[str, Any],
) -> tuple[str, list[str]]:
    comparison = safe_mapping(received_snapshot_reconcile.get("comparison"))
    classification = safe_mapping(received_snapshot_reconcile.get("classification"))
    blockers: list[str] = []

    if not comparison.get("counts_match") or not comparison.get("warnings_match"):
        blockers.extend(["received_snapshot_collect_count_mismatch", "received_snapshot_warning_count_mismatch"])
        return P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_COLLECT_COUNT_MISMATCH, blockers
    if not comparison.get("test_files_fingerprint_match"):
        blockers.append("received_snapshot_collect_file_fingerprint_mismatch")
        return P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_FILE_FINGERPRINT_MISMATCH, blockers

    item_mismatch = bool(
        comparison.get("test_items_fingerprint_match") is not True
        or received_snapshot_reconcile.get("received_snapshot_item_fingerprint_mismatch_unresolved") is True
        or classification.get("status") == P7_HOLD004_RECEIVED_RECONCILE_STATUS_ITEM_FINGERPRINT_MISMATCH_UNCLASSIFIED
        or adoption_decision.get("adoption_status")
        == P7_HOLD004_RECEIVED_ADOPTION_STATUS_BLOCKED_UNCLASSIFIED_ITEM_FINGERPRINT_MISMATCH
    )
    if item_mismatch:
        blockers.append(P7_HOLD004_RECEIVED_SNAPSHOT_ITEM_FINGERPRINT_MISMATCH_BLOCKER_REF)
        blockers.append(P7_HOLD004_RECEIVED_SNAPSHOT_SOURCE_IDENTITY_BLOCKER_REF)
        return P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_ITEM_FINGERPRINT_MISMATCH, blockers

    if not comparison.get("source_snapshot_ref_matches_received_zip_ref"):
        blockers.append(P7_HOLD004_RECEIVED_SNAPSHOT_SOURCE_IDENTITY_BLOCKER_REF)
        return P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_SOURCE_IDENTITY_UNCLEAR, blockers
    if not received_snapshot_reconcile.get("active_baseline_accepts_received_nodeids"):
        blockers.append("active_baseline_does_not_accept_received_snapshot_nodeids")
        return P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_ACTIVE_BASELINE_NOT_CURRENT, blockers

    return P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY, []


def build_p7_hold004_official_group02_capture_readiness(
    *,
    received_snapshot_reconcile: Mapping[str, Any] | None = None,
    adoption_decision: Mapping[str, Any] | None = None,
    adoption_rule: Mapping[str, Any] | None = None,
    runtime_builder_refresh_status: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the official group_02 readiness guard.

    Default behavior preserves the historical R25 guard.  When a R36
    post-adoption reconcile and R37 runtime-builder refresh status are supplied,
    this same readiness concept is re-evaluated for R39 without creating a
    second readiness concept.  Ready means only that official capture may be
    run and recorded; it is not group green, full backend-suite green, HOLD
    closure, P7 completion, P8 start, or release readiness.
    """

    rule_material = (
        safe_mapping(adoption_rule)
        if adoption_rule is not None
        else build_p7_hold004_official_group02_capture_adoption_rule()
    )
    assert_p7_hold004_official_group02_capture_adoption_rule_contract(rule_material)
    reconcile_material = (
        safe_mapping(received_snapshot_reconcile)
        if received_snapshot_reconcile is not None
        else build_p7_hold004_received_snapshot_baseline_fingerprint_reconcile()
    )
    runtime_refresh_material = safe_mapping(runtime_builder_refresh_status)
    post_adoption_reconcile = _is_post_adoption_received_snapshot_reconcile(reconcile_material)

    if post_adoption_reconcile:
        _assert_post_adoption_received_snapshot_reconcile_like(reconcile_material)
        _assert_runtime_builder_refresh_status_like(runtime_refresh_material)
        readiness_status = P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY
        blockers: list[str] = []
        ready = True
        schema_version = P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION_V2
        step = P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_AFTER_REFRESH_STEP
        readiness_id = P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_AFTER_REFRESH_ID
        received_reconcile_schema_version = P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_SCHEMA_VERSION
        received_reconcile_id = P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_ID
        adoption_decision_schema_version = ""
        adoption_decision_id = ""
        refresh_fields = {
            "active_baseline_refresh_schema_version": P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_SCHEMA_VERSION,
            "active_baseline_refresh_id": clean_identifier(
                runtime_refresh_material.get("active_baseline_refresh_id"),
                default=P7_HOLD004_ACTIVE_BASELINE_REFRESH_ID,
                max_length=180,
            ),
            "runtime_builder_refresh_status_id": clean_identifier(
                runtime_refresh_material.get("refresh_status_id"),
                default=P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_ID,
                max_length=180,
            ),
            "active_baseline_update_applied_to_runtime_builders": True,
            "source_snapshot_ref_updated_in_active_builders": True,
            "post_adoption_received_snapshot_reconcile_id": clean_identifier(
                reconcile_material.get("reconcile_id"),
                default=P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_ID,
                max_length=180,
            ),
            "post_adoption_readiness_re_evaluated": True,
        }
    else:
        assert_p7_hold004_received_snapshot_baseline_fingerprint_reconcile_contract(reconcile_material)
        adoption_material = (
            safe_mapping(adoption_decision)
            if adoption_decision is not None
            else build_p7_hold004_received_snapshot_baseline_adoption_decision(
                received_snapshot_reconcile=reconcile_material
            )
        )
        assert_p7_hold004_received_snapshot_baseline_adoption_decision_contract(adoption_material)
        readiness_status, blockers = _readiness_status_and_blockers(
            received_snapshot_reconcile=reconcile_material,
            adoption_decision=adoption_material,
        )
        ready = readiness_status == P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY
        schema_version = P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION
        step = P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STEP
        readiness_id = P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_ID
        received_reconcile_schema_version = P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_SCHEMA_VERSION
        received_reconcile_id = P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_ID
        adoption_decision_schema_version = P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_ADOPTION_DECISION_SCHEMA_VERSION
        adoption_decision_id = P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_ADOPTION_DECISION_ID
        refresh_fields = {
            "active_baseline_refresh_schema_version": "",
            "active_baseline_refresh_id": "",
            "runtime_builder_refresh_status_id": "",
            "active_baseline_update_applied_to_runtime_builders": False,
            "source_snapshot_ref_updated_in_active_builders": False,
            "post_adoption_received_snapshot_reconcile_id": "",
            "post_adoption_readiness_re_evaluated": False,
        }

    blocker_refs = dedupe_identifiers(blockers, limit=40, max_length=180)
    followups = dedupe_identifiers(
        [
            *blocker_refs,
            "received_snapshot_baseline_fingerprint_reconcile_required" if not ready else "",
            "received_snapshot_baseline_adoption_decision_required" if (not ready and not post_adoption_reconcile) else "",
            "official_group_02_capture_blocked_until_received_snapshot_adoption" if not ready else "",
            "group_02_official_full_run_not_executed" if ready else "",
            "full_backend_suite_green_unconfirmed",
        ],
        limit=80,
        max_length=180,
    )

    material = {
        "schema_version": schema_version,
        "phase": P7_PHASE,
        "step": step,
        "implementation_step": step,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "readiness_id": readiness_id,
        "received_reconcile_schema_version": received_reconcile_schema_version,
        "received_reconcile_id": received_reconcile_id,
        "received_adoption_decision_schema_version": adoption_decision_schema_version,
        "received_adoption_decision_id": adoption_decision_id,
        "adoption_rule_id": rule_material.get("adoption_rule_id"),
        "collect_baseline_id": rule_material.get("collect_baseline_id"),
        "inventory_id": rule_material.get("inventory_id"),
        "plan_id": rule_material.get("plan_id"),
        "source_mode": P7_SOURCE_MODE,
        "source_snapshot_ref": P7_HOLD004_BACKEND_R4_R5_SOURCE_SNAPSHOT_REF,
        "git_checked": P7_GIT_CHECKED,
        **_current_baseline_boundary_fields(execution_summary_id=P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_ID),
        **refresh_fields,
        "readiness_status": readiness_status,
        "blocker_refs": blocker_refs,
        "received_snapshot_baseline_fingerprint_reconciled": bool(
            reconcile_material.get("received_snapshot_baseline_fingerprint_reconciled") is True
        ),
        "received_snapshot_item_fingerprint_mismatch_unresolved": bool(
            reconcile_material.get("received_snapshot_item_fingerprint_mismatch_unresolved") is True
        ),
        "source_snapshot_ref_current_for_received_zip": bool(
            reconcile_material.get("source_snapshot_ref_current_for_received_zip") is True
        ),
        "active_baseline_accepts_received_nodeids": bool(
            reconcile_material.get("active_baseline_accepts_received_nodeids") is True
        ),
        "group_id": P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID,
        "batch_id": P7_HOLD004_GROUP02_OFFICIAL_BATCH_ID,
        "expected_group_file_count": rule_material.get("expected_group_file_count"),
        "expected_group_test_item_count": rule_material.get("expected_group_test_item_count"),
        "expected_warning_count": rule_material.get("expected_warning_count"),
        "expected_timeout_budget_sec": rule_material.get("expected_timeout_budget_sec"),
        "official_capture_run_allowed": ready,
        "official_capture_result_recording_allowed": ready,
        "official_group_02_capture_blocked": not ready,
        "official_group_02_capture_green_confirmed": False,
        "can_claim_group_green": False,
        "can_claim_full_backend_suite_green": False,
        **_release_closed_boundary(),
        "unresolved_hold_refs": [P7_HOLD004_BACKEND_SUITE_HOLD_ID],
        "required_followup_fixes": followups,
        "terminal_output_retained": False,
        "stdout_retained": False,
        "stderr_retained": False,
        "raw_traceback_included": False,
        "public_contract": _public_contract_boundary_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
        "body_free": True,
    }
    assert_p7_hold004_official_group02_capture_readiness_contract(material)
    return material


def assert_p7_hold004_official_group02_capture_readiness_contract(material: Mapping[str, Any]) -> bool:
    """Validate the R25 official group_02 readiness guard material."""

    data = safe_mapping(material)
    source = "p7_hold004_official_group02_capture_readiness"
    schema_version = clean_identifier(data.get("schema_version"), max_length=160)
    if schema_version not in P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_ALLOWED_SCHEMA_VERSIONS:
        raise ValueError("P7-HOLD-004 official group_02 readiness schema_version changed")
    after_refresh = schema_version == P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION_V2
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError("P7-HOLD-004 official group_02 readiness scope changed")
    expected_step = (
        P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_AFTER_REFRESH_STEP
        if after_refresh
        else P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STEP
    )
    expected_id = (
        P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_AFTER_REFRESH_ID
        if after_refresh
        else P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_ID
    )
    if data.get("implementation_step") != expected_step:
        raise ValueError("P7-HOLD-004 official group_02 readiness implementation_step changed")
    if data.get("readiness_id") != expected_id:
        raise ValueError("P7-HOLD-004 official group_02 readiness id changed")
    if after_refresh:
        if data.get("received_reconcile_schema_version") != P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_SCHEMA_VERSION:
            raise ValueError("P7-HOLD-004 after-refresh readiness received reconcile schema mismatch")
        if data.get("received_reconcile_id") != P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_ID:
            raise ValueError("P7-HOLD-004 after-refresh readiness received reconcile id mismatch")
        if data.get("received_adoption_decision_schema_version") != "" or data.get("received_adoption_decision_id") != "":
            raise ValueError("P7-HOLD-004 after-refresh readiness must not pretend to use historical adoption decision")
        if data.get("active_baseline_refresh_schema_version") != P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_SCHEMA_VERSION:
            raise ValueError("P7-HOLD-004 after-refresh readiness runtime refresh schema mismatch")
        if data.get("runtime_builder_refresh_status_id") != P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_ID:
            raise ValueError("P7-HOLD-004 after-refresh readiness runtime refresh id mismatch")
        if data.get("active_baseline_refresh_id") != P7_HOLD004_ACTIVE_BASELINE_REFRESH_ID:
            raise ValueError("P7-HOLD-004 after-refresh readiness active refresh id mismatch")
        for key in (
            "active_baseline_update_applied_to_runtime_builders",
            "source_snapshot_ref_updated_in_active_builders",
            "post_adoption_readiness_re_evaluated",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-HOLD-004 after-refresh readiness must keep {key}=true")
    else:
        if data.get("received_reconcile_schema_version") != P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_SCHEMA_VERSION:
            raise ValueError("P7-HOLD-004 official group_02 readiness received reconcile schema mismatch")
        if data.get("received_reconcile_id") != P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_ID:
            raise ValueError("P7-HOLD-004 official group_02 readiness received reconcile id mismatch")
        if data.get("received_adoption_decision_schema_version") != P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_ADOPTION_DECISION_SCHEMA_VERSION:
            raise ValueError("P7-HOLD-004 official group_02 readiness adoption schema mismatch")
        if data.get("received_adoption_decision_id") != P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_ADOPTION_DECISION_ID:
            raise ValueError("P7-HOLD-004 official group_02 readiness adoption id mismatch")
    if data.get("adoption_rule_id") != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_ADOPTION_RULE_ID:
        raise ValueError("P7-HOLD-004 official group_02 readiness rule id mismatch")
    if data.get("group_id") != P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID or data.get("batch_id") != P7_HOLD004_GROUP02_OFFICIAL_BATCH_ID:
        raise ValueError("P7-HOLD-004 official group_02 readiness target changed")
    if data.get("expected_group_file_count") != P7_HOLD004_GROUP02_OFFICIAL_FILE_COUNT:
        raise ValueError("P7-HOLD-004 official group_02 readiness file count changed")
    if data.get("expected_group_test_item_count") != P7_HOLD004_GROUP02_OFFICIAL_TEST_ITEM_COUNT:
        raise ValueError("P7-HOLD-004 official group_02 readiness test item count changed")
    if data.get("expected_warning_count") != P7_HOLD004_GROUP02_OFFICIAL_WARNINGS_COUNT:
        raise ValueError("P7-HOLD-004 official group_02 readiness warning count changed")
    status = clean_identifier(data.get("readiness_status"), max_length=160)
    if status not in P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_ALLOWED_STATUSES:
        raise ValueError("P7-HOLD-004 official group_02 readiness status changed")
    ready = status == P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY
    if data.get("official_capture_run_allowed") is not ready:
        raise ValueError("P7-HOLD-004 official group_02 readiness run_allowed mismatch")
    if data.get("official_capture_result_recording_allowed") is not ready:
        raise ValueError("P7-HOLD-004 official group_02 readiness result_recording_allowed mismatch")
    if data.get("official_group_02_capture_blocked") is not (not ready):
        raise ValueError("P7-HOLD-004 official group_02 readiness blocked flag mismatch")
    blockers = dedupe_identifiers(data.get("blocker_refs"), limit=40, max_length=180)
    if not ready and not blockers:
        raise ValueError("P7-HOLD-004 blocked readiness must keep blocker refs")
    if ready and blockers:
        raise ValueError("P7-HOLD-004 ready capture must not keep blocker refs")
    if data.get("received_snapshot_item_fingerprint_mismatch_unresolved") is True:
        if status != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_ITEM_FINGERPRINT_MISMATCH:
            raise ValueError("P7-HOLD-004 unresolved item mismatch must block official capture")
        if P7_HOLD004_RECEIVED_SNAPSHOT_ITEM_FINGERPRINT_MISMATCH_BLOCKER_REF not in blockers:
            raise ValueError("P7-HOLD-004 unresolved item mismatch blocker missing")
    if after_refresh:
        if status != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY:
            raise ValueError("P7-HOLD-004 after-refresh readiness must be READY")
        for key in (
            "received_snapshot_baseline_fingerprint_reconciled",
            "source_snapshot_ref_current_for_received_zip",
            "active_baseline_accepts_received_nodeids",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-HOLD-004 after-refresh readiness must keep {key}=true")
        for key in (
            "received_snapshot_item_fingerprint_mismatch_unresolved",
            "official_group_02_capture_blocked",
            "official_group_02_capture_green_confirmed",
            "full_backend_suite_green_confirmed",
            "hold004_close_allowed",
            "p7_complete",
            "p8_start_allowed",
            "release_allowed",
        ):
            if data.get(key) is not False:
                raise ValueError(f"P7-HOLD-004 after-refresh readiness must keep {key}=false")
        followups = set(dedupe_identifiers(data.get("required_followup_fixes"), limit=80, max_length=180))
        if "group_02_official_full_run_not_executed" not in followups:
            raise ValueError("P7-HOLD-004 after-refresh readiness must keep group_02 run followup")
        if "full_backend_suite_green_unconfirmed" not in followups:
            raise ValueError("P7-HOLD-004 after-refresh readiness must keep full backend suite followup")
    if data.get("can_claim_group_green") is not False or data.get("can_claim_full_backend_suite_green") is not False:
        raise ValueError("P7-HOLD-004 readiness guard must not claim green")
    for forbidden_flag in ("raw_traceback_included", "terminal_output_retained", "stdout_retained", "stderr_retained"):
        if data.get(forbidden_flag) is not False:
            raise ValueError(f"P7-HOLD-004 readiness guard must keep {forbidden_flag}=false")
    _assert_common_release_closed_and_body_free(data, source=source)
    return True


def _official_group02_decision_status_from_result(
    *,
    result: Mapping[str, Any],
    collect_only_test_item_count: int,
) -> tuple[str, list[str]]:
    blockers: list[str] = []
    try:
        assert_false_markers(safe_mapping(result.get("public_contract")), source="official_group02_result.public_contract")
        assert_false_markers(safe_mapping(result.get("body_free_markers")), source="official_group02_result.body_free_markers")
        assert_p7_no_body_payload_or_contract_mutation(result, source="official_group02_result")
    except ValueError:
        return P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_REJECTED_BODY_OR_CONTRACT, [
            "body_payload_or_contract_mutation_detected"
        ]
    if result.get("collect_baseline_id") != P7_HOLD004_BACKEND_COLLECT_BASELINE_ID:
        return P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_REJECTED_BASELINE_MISMATCH, [
            "collect_baseline_id_mismatch"
        ]
    if (
        result.get("inventory_id") != P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID
        or result.get("plan_id") != P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID
    ):
        return P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_REJECTED_PLAN_MISMATCH, [
            "inventory_or_execution_plan_id_mismatch"
        ]
    if (
        result.get("group_id") != P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID
        or result.get("batch_id") != P7_HOLD004_GROUP02_OFFICIAL_BATCH_ID
        or result.get("run_kind") != P7_HOLD004_BACKEND_SUITE_RUN_KIND_CAPTURE
    ):
        return P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_REJECTED_GROUP_OR_BATCH_MISMATCH, [
            "group_batch_or_run_kind_mismatch"
        ]
    if collect_only_test_item_count != P7_HOLD004_GROUP02_OFFICIAL_TEST_ITEM_COUNT:
        return P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_REJECTED_COLLECT_COUNT_MISMATCH, [
            "group_02_collect_only_count_mismatch"
        ]
    try:
        assert_p7_hold004_backend_suite_group_run_result_contract(result)
    except ValueError:
        return P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_REJECTED_BODY_OR_CONTRACT, [
            "group_run_result_contract_rejected"
        ]

    status = _normalize_status_identifier(result.get("status"))
    counts = safe_mapping(result.get("observed_counts"))
    if status == P7_HOLD004_BACKEND_SUITE_STATUS_PASS:
        expected_pass_counts = {
            "passed": P7_HOLD004_GROUP02_OFFICIAL_TEST_ITEM_COUNT,
            "failed": 0,
            "skipped": 0,
            "warnings": P7_HOLD004_GROUP02_OFFICIAL_WARNINGS_COUNT,
            "errors": 0,
            "deselected": 0,
        }
        if counts == expected_pass_counts:
            return P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_GREEN, []
        return P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_REJECTED_STATUS_OR_COUNTS_MISMATCH, [
            "pass_result_counts_do_not_match_group_02_current_snapshot"
        ]
    if status == P7_HOLD004_BACKEND_SUITE_STATUS_FAIL:
        return P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_RED, []
    if status == P7_HOLD004_BACKEND_SUITE_STATUS_TIMEOUT:
        return P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_TIMEOUT, []
    if status == P7_HOLD004_BACKEND_SUITE_STATUS_COLLECTION_FAILED:
        return P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_COLLECTION_FAILED, []
    if status == P7_HOLD004_BACKEND_SUITE_STATUS_INTERRUPTED:
        return P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_INTERRUPTED, []
    if status == P7_HOLD004_BACKEND_SUITE_STATUS_NOT_RUN:
        return P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_BLOCKED, ["official_group_02_capture_run_not_recorded"]
    return P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_REJECTED_STATUS_OR_COUNTS_MISMATCH, [
        "group_02_official_capture_status_not_adoptable"
    ]


def build_p7_hold004_official_group02_capture_adoption_decision(
    *,
    run_result: Mapping[str, Any] | None = None,
    collect_only_test_item_count: Any = P7_HOLD004_GROUP02_OFFICIAL_TEST_ITEM_COUNT,
    rule: Mapping[str, Any] | None = None,
    readiness: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build an R19/R25 decision for whether a group_02 result may be official."""

    rule_material = safe_mapping(rule) if rule is not None else build_p7_hold004_official_group02_capture_adoption_rule()
    assert_p7_hold004_official_group02_capture_adoption_rule_contract(rule_material)
    readiness_material = (
        safe_mapping(readiness)
        if readiness is not None
        else build_p7_hold004_official_group02_capture_readiness(adoption_rule=rule_material)
    )
    assert_p7_hold004_official_group02_capture_readiness_contract(readiness_material)

    collect_count = _coerce_non_negative_int(collect_only_test_item_count, default=0)
    result = safe_mapping(run_result)
    result_present = bool(result)
    status = _normalize_status_identifier(result.get("status")) if result_present else ""
    counts = _observed_counts(safe_mapping(result.get("observed_counts"))) if result_present else _observed_counts({})

    readiness_status = clean_identifier(readiness_material.get("readiness_status"), max_length=160)
    if readiness_status != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY:
        adoption_status = P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_BLOCKED_BY_READINESS_GUARD
        blockers = dedupe_identifiers(
            [
                P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_GUARD_BLOCKER_REF,
                *readiness_material.get("blocker_refs", []),
                "official_group_02_capture_run_not_recorded" if not result_present else "",
            ],
            limit=60,
            max_length=180,
        )
    elif not result_present:
        adoption_status = P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_BLOCKED
        blockers = ["official_group_02_capture_run_not_recorded"]
    else:
        adoption_status, blockers = _official_group02_decision_status_from_result(
            result=result,
            collect_only_test_item_count=collect_count,
        )

    recordable = adoption_status in P7_HOLD004_OFFICIAL_CAPTURE_RECORDABLE_ADOPTION_STATUSES
    green = adoption_status == P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_GREEN
    followups = ["full_backend_suite_green_unconfirmed"]
    if blockers:
        followups.extend(blockers)
    if readiness_status != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY:
        followups.extend(readiness_material.get("required_followup_fixes", []))
        followups.append("official_group_02_capture_blocked_until_received_snapshot_adoption")
    if adoption_status == P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_RED:
        followups.append("first_red_classification_required")
    if adoption_status == P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_TIMEOUT:
        followups.append("timeout_classification_required")
        followups.append("timeout_isolated_not_green")
    if adoption_status == P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_GREEN:
        followups.append("group_02_green_is_not_full_backend_suite_green")

    material = {
        "schema_version": P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_ADOPTION_DECISION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_ADOPTION_STEP,
        "implementation_step": P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_ADOPTION_STEP,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "adoption_rule_id": P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_ADOPTION_RULE_ID,
        "decision_id": P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_DECISION_ID,
        "official_capture_readiness_schema_version": P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION,
        "official_capture_readiness_id": readiness_material.get("readiness_id"),
        "official_capture_readiness_status": readiness_status,
        "received_reconcile_schema_version": readiness_material.get("received_reconcile_schema_version"),
        "received_reconcile_id": readiness_material.get("received_reconcile_id"),
        "received_adoption_decision_schema_version": readiness_material.get("received_adoption_decision_schema_version"),
        "received_adoption_decision_id": readiness_material.get("received_adoption_decision_id"),
        "collect_baseline_id": rule_material.get("collect_baseline_id"),
        "inventory_id": rule_material.get("inventory_id"),
        "plan_id": rule_material.get("plan_id"),
        "source_mode": P7_SOURCE_MODE,
        "source_snapshot_ref": P7_HOLD004_BACKEND_R4_R5_SOURCE_SNAPSHOT_REF,
        "git_checked": P7_GIT_CHECKED,
        **_current_baseline_boundary_fields(execution_summary_id=P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_ID),
        "group_id": P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID,
        "batch_id": P7_HOLD004_GROUP02_OFFICIAL_BATCH_ID,
        "run_kind": P7_HOLD004_BACKEND_SUITE_RUN_KIND_CAPTURE,
        "collect_only_test_item_count": collect_count,
        "expected_collect_only_test_item_count": P7_HOLD004_GROUP02_OFFICIAL_TEST_ITEM_COUNT,
        "run_result_present": result_present,
        "run_result_status": status,
        "run_result_observed_counts": counts,
        "adoption_status": adoption_status,
        "adoption_blockers": dedupe_identifiers(blockers, limit=60, max_length=180),
        "official_capture_run_allowed": readiness_material.get("official_capture_run_allowed") is True,
        "official_capture_result_recording_allowed": readiness_material.get("official_capture_result_recording_allowed") is True,
        "official_group_02_capture_blocked": readiness_material.get("official_group_02_capture_blocked") is True,
        "received_snapshot_baseline_fingerprint_reconciled": readiness_material.get("received_snapshot_baseline_fingerprint_reconciled") is True,
        "received_snapshot_item_fingerprint_mismatch_unresolved": readiness_material.get("received_snapshot_item_fingerprint_mismatch_unresolved") is True,
        "received_snapshot_blocker_refs": dedupe_identifiers(readiness_material.get("blocker_refs"), limit=60, max_length=180),
        "official_capture_material_recordable": recordable,
        "official_group_02_capture_recorded": recordable,
        "official_group_02_capture_green_confirmed": green,
        "can_claim_group_green": green,
        "can_claim_full_backend_suite_green": False,
        "red_classification_required": adoption_status == P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_RED,
        "timeout_classification_required": adoption_status == P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_TIMEOUT,
        "collection_failed_classification_required": adoption_status
        == P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_COLLECTION_FAILED,
        "interrupted_classification_required": adoption_status
        == P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_INTERRUPTED,
        "terminal_output_retained": False,
        "raw_traceback_included": False,
        "stdout_retained": False,
        "stderr_retained": False,
        **_release_closed_boundary(),
        "unresolved_hold_refs": [P7_HOLD004_BACKEND_SUITE_HOLD_ID],
        "required_followup_fixes": dedupe_identifiers(followups, limit=140, max_length=180),
        "public_contract": _public_contract_boundary_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
        "body_free": True,
    }
    assert_p7_hold004_official_group02_capture_adoption_decision_contract(material)
    return material


def assert_p7_hold004_official_group02_capture_adoption_decision_contract(material: Mapping[str, Any]) -> bool:
    """Validate the R19 official group_02 adoption decision material."""

    data = safe_mapping(material)
    source = "p7_hold004_official_group02_capture_adoption_decision"
    if data.get("schema_version") != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_ADOPTION_DECISION_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 official group_02 adoption decision schema_version changed")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError("P7-HOLD-004 official group_02 adoption decision scope changed")
    if data.get("implementation_step") != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_ADOPTION_STEP:
        raise ValueError("P7-HOLD-004 official group_02 adoption decision implementation_step changed")
    if data.get("adoption_rule_id") != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_ADOPTION_RULE_ID:
        raise ValueError("P7-HOLD-004 official group_02 adoption decision rule id changed")
    if data.get("decision_id") != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_DECISION_ID:
        raise ValueError("P7-HOLD-004 official group_02 adoption decision id changed")
    if data.get("collect_baseline_id") != P7_HOLD004_BACKEND_COLLECT_BASELINE_ID:
        raise ValueError("P7-HOLD-004 official group_02 adoption decision must use current collect baseline")
    if data.get("inventory_id") != P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID:
        raise ValueError("P7-HOLD-004 official group_02 adoption decision must use current inventory")
    if data.get("plan_id") != P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID:
        raise ValueError("P7-HOLD-004 official group_02 adoption decision must use current execution plan")
    for key in (
        "current_collect_baseline_reconciled",
        "current_collect_baseline_connected",
        "current_group_inventory_connected",
        "current_execution_plan_connected",
        "previous_baseline_is_not_current",
        "old_baseline_not_used_as_current",
        "baseline_mismatch_blocks_execution",
        "backend_suite_group_02_count_current",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 official group_02 adoption decision boundary {key} must be true")
    if data.get("group_id") != P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID:
        raise ValueError("P7-HOLD-004 official group_02 adoption decision group changed")
    if data.get("batch_id") != P7_HOLD004_GROUP02_OFFICIAL_BATCH_ID:
        raise ValueError("P7-HOLD-004 official group_02 adoption decision batch changed")
    if data.get("run_kind") != P7_HOLD004_BACKEND_SUITE_RUN_KIND_CAPTURE:
        raise ValueError("P7-HOLD-004 official group_02 adoption decision run_kind changed")
    if data.get("expected_collect_only_test_item_count") != P7_HOLD004_GROUP02_OFFICIAL_TEST_ITEM_COUNT:
        raise ValueError("P7-HOLD-004 official group_02 adoption decision expected collect count changed")
    status = clean_identifier(data.get("adoption_status"), max_length=160)
    if status not in P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_ALLOWED_STATUSES:
        raise ValueError("P7-HOLD-004 official group_02 adoption decision status changed")
    recordable = status in P7_HOLD004_OFFICIAL_CAPTURE_RECORDABLE_ADOPTION_STATUSES
    if data.get("official_capture_material_recordable") is not recordable:
        raise ValueError("P7-HOLD-004 official group_02 adoption decision recordable mismatch")
    if data.get("official_group_02_capture_recorded") is not recordable:
        raise ValueError("P7-HOLD-004 official group_02 adoption decision recorded mismatch")
    green = status == P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_GREEN
    if data.get("official_group_02_capture_green_confirmed") is not green:
        raise ValueError("P7-HOLD-004 official group_02 adoption decision group green mismatch")
    if data.get("can_claim_group_green") is not green:
        raise ValueError("P7-HOLD-004 official group_02 adoption decision group green claim mismatch")
    if data.get("can_claim_full_backend_suite_green") is not False:
        raise ValueError("P7-HOLD-004 official group_02 adoption decision must not claim full suite green")
    counts = safe_mapping(data.get("run_result_observed_counts"))
    for count_key in ("passed", "failed", "skipped", "warnings", "errors", "deselected"):
        count = _coerce_non_negative_int(counts.get(count_key), default=-1)
        if counts.get(count_key) != count or count < 0:
            raise ValueError(f"P7-HOLD-004 official group_02 adoption decision count {count_key} invalid")
    if green and counts != {
        "passed": P7_HOLD004_GROUP02_OFFICIAL_TEST_ITEM_COUNT,
        "failed": 0,
        "skipped": 0,
        "warnings": P7_HOLD004_GROUP02_OFFICIAL_WARNINGS_COUNT,
        "errors": 0,
        "deselected": 0,
    }:
        raise ValueError("P7-HOLD-004 official group_02 adoption decision green counts mismatch")
    blockers = dedupe_identifiers(data.get("adoption_blockers"), limit=40, max_length=180)
    if recordable and blockers:
        raise ValueError("P7-HOLD-004 official group_02 adoption decision recordable result must not keep blockers")
    if not recordable and not blockers:
        raise ValueError("P7-HOLD-004 official group_02 adoption decision blocked/rejected result must keep blockers")
    if data.get("red_classification_required") is not (
        status == P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_RED
    ):
        raise ValueError("P7-HOLD-004 official group_02 adoption decision red classification mismatch")
    if data.get("timeout_classification_required") is not (
        status == P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_TIMEOUT
    ):
        raise ValueError("P7-HOLD-004 official group_02 adoption decision timeout classification mismatch")
    for forbidden_flag in ("raw_traceback_included", "terminal_output_retained", "stdout_retained", "stderr_retained"):
        if data.get(forbidden_flag) is not False:
            raise ValueError(f"P7-HOLD-004 official group_02 adoption decision must keep {forbidden_flag}=false")
    _assert_common_release_closed_and_body_free(data, source=source)
    return True


def build_p7_hold004_group02_timeout_classification_plan(
    *,
    readiness: Mapping[str, Any] | None = None,
    attempt_120_sec_completed: Any = False,
    attempt_240_sec_completed: Any = False,
) -> dict[str, Any]:
    """Build the R28 body-free timeout/long-run policy for group_02.

    The plan is recordable even while the R25 readiness guard is blocked, but
    it does not authorize an official capture run until readiness becomes READY.
    A timeout is neither green nor an immediate failure; it is routed to timeout
    classification without retaining terminal output.
    """

    readiness_material = safe_mapping(readiness) if readiness is not None else build_p7_hold004_official_group02_capture_readiness()
    assert_p7_hold004_official_group02_capture_readiness_contract(readiness_material)
    readiness_status = clean_identifier(readiness_material.get("readiness_status"), max_length=160)
    readiness_ready = readiness_status == P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY
    blocker_refs = dedupe_identifiers(readiness_material.get("blocker_refs"), limit=60, max_length=180)

    material = {
        "schema_version": P7_HOLD004_GROUP02_TIMEOUT_CLASSIFICATION_PLAN_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_GROUP02_TIMEOUT_CLASSIFICATION_PLAN_STEP,
        "implementation_step": P7_HOLD004_GROUP02_TIMEOUT_CLASSIFICATION_PLAN_STEP,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "plan_id": P7_HOLD004_GROUP02_TIMEOUT_CLASSIFICATION_PLAN_ID,
        "official_capture_readiness_schema_version": P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION,
        "official_capture_readiness_id": readiness_material.get("readiness_id"),
        "official_capture_readiness_status": readiness_status,
        "readiness_blocker_refs": blocker_refs,
        "source_mode": P7_SOURCE_MODE,
        "source_snapshot_ref": P7_HOLD004_BACKEND_R4_R5_SOURCE_SNAPSHOT_REF,
        "git_checked": P7_GIT_CHECKED,
        "group_id": P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID,
        "batch_id": P7_HOLD004_GROUP02_OFFICIAL_BATCH_ID,
        "timeout_budget_sec": 120,
        "long_run_probe_budget_sec": 240,
        "official_capture_run_allowed": readiness_ready,
        "official_capture_result_recording_allowed": readiness_ready,
        "official_capture_blocked_until_readiness_ready": not readiness_ready,
        "prior_local_attempts": {
            "attempt_120_sec_completed": _coerce_bool(attempt_120_sec_completed),
            "attempt_240_sec_completed": _coerce_bool(attempt_240_sec_completed),
            "official_green_confirmed": False,
        },
        "timeout_result_policy": {
            "timeout_is_green": False,
            "timeout_is_immediate_fail": False,
            "timeout_classification_required": True,
            "timeout_material_body_free_required": True,
            "batch_split_requires_new_design": True,
            "batch_green_is_group_green": False,
            "collect_only_is_not_execution_green": True,
            "readiness_guard_required_before_official_capture_run": True,
        },
        "timeout_material_allowed_after_readiness_ready": readiness_ready,
        "can_claim_group_green": False,
        "can_claim_full_backend_suite_green": False,
        "full_backend_suite_green_confirmed": False,
        "hold004_close_allowed": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "terminal_output_retained": False,
        "stdout_retained": False,
        "stderr_retained": False,
        "raw_traceback_included": False,
        **_release_closed_boundary(),
        "unresolved_hold_refs": [P7_HOLD004_BACKEND_SUITE_HOLD_ID],
        "required_followup_fixes": dedupe_identifiers(
            [
                *blocker_refs,
                "official_group_02_capture_blocked_until_received_snapshot_adoption"
                if not readiness_ready
                else "",
                "group_02_timeout_classification_required_when_timeout_occurs",
                "group_02_long_run_or_batch_split_requires_separate_design",
                "full_backend_suite_green_unconfirmed",
            ],
            limit=100,
            max_length=180,
        ),
        "public_contract": _public_contract_boundary_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
        "body_free": True,
    }
    assert_p7_hold004_group02_timeout_classification_plan_contract(material)
    return material


def assert_p7_hold004_group02_timeout_classification_plan_contract(material: Mapping[str, Any]) -> bool:
    """Validate the R28 group_02 timeout/long-run classification plan."""

    data = safe_mapping(material)
    source = "p7_hold004_group02_timeout_classification_plan"
    if data.get("schema_version") != P7_HOLD004_GROUP02_TIMEOUT_CLASSIFICATION_PLAN_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 group_02 timeout plan schema_version changed")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError("P7-HOLD-004 group_02 timeout plan scope changed")
    if data.get("implementation_step") != P7_HOLD004_GROUP02_TIMEOUT_CLASSIFICATION_PLAN_STEP:
        raise ValueError("P7-HOLD-004 group_02 timeout plan implementation_step changed")
    if data.get("plan_id") != P7_HOLD004_GROUP02_TIMEOUT_CLASSIFICATION_PLAN_ID:
        raise ValueError("P7-HOLD-004 group_02 timeout plan id changed")
    if data.get("official_capture_readiness_schema_version") != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 group_02 timeout plan readiness schema mismatch")
    if data.get("official_capture_readiness_id") != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_ID:
        raise ValueError("P7-HOLD-004 group_02 timeout plan readiness id mismatch")
    readiness_status = clean_identifier(data.get("official_capture_readiness_status"), max_length=160)
    if readiness_status not in P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_ALLOWED_STATUSES:
        raise ValueError("P7-HOLD-004 group_02 timeout plan readiness status invalid")
    readiness_ready = readiness_status == P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY
    if data.get("official_capture_run_allowed") is not readiness_ready:
        raise ValueError("P7-HOLD-004 group_02 timeout plan official run allowed mismatch")
    if data.get("official_capture_result_recording_allowed") is not readiness_ready:
        raise ValueError("P7-HOLD-004 group_02 timeout plan official result recording mismatch")
    if data.get("official_capture_blocked_until_readiness_ready") is not (not readiness_ready):
        raise ValueError("P7-HOLD-004 group_02 timeout plan readiness blocker mismatch")
    blockers = dedupe_identifiers(data.get("readiness_blocker_refs"), limit=60, max_length=180)
    if readiness_ready and blockers:
        raise ValueError("P7-HOLD-004 group_02 timeout plan ready state must not keep blockers")
    if not readiness_ready and not blockers:
        raise ValueError("P7-HOLD-004 group_02 timeout plan blocked state must keep readiness blockers")
    if data.get("source_mode") != P7_SOURCE_MODE or data.get("source_snapshot_ref") != P7_HOLD004_BACKEND_R4_R5_SOURCE_SNAPSHOT_REF:
        raise ValueError("P7-HOLD-004 group_02 timeout plan source snapshot changed")
    if data.get("git_checked") is not False:
        raise ValueError("P7-HOLD-004 group_02 timeout plan must not claim GitHub verification")
    if data.get("group_id") != P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID:
        raise ValueError("P7-HOLD-004 group_02 timeout plan group changed")
    if data.get("batch_id") != P7_HOLD004_GROUP02_OFFICIAL_BATCH_ID:
        raise ValueError("P7-HOLD-004 group_02 timeout plan batch changed")
    if data.get("timeout_budget_sec") != 120 or data.get("long_run_probe_budget_sec") != 240:
        raise ValueError("P7-HOLD-004 group_02 timeout plan budgets changed")

    attempts = safe_mapping(data.get("prior_local_attempts"))
    if set(attempts) != {"attempt_120_sec_completed", "attempt_240_sec_completed", "official_green_confirmed"}:
        raise ValueError("P7-HOLD-004 group_02 timeout plan prior attempt keys changed")
    for key in ("attempt_120_sec_completed", "attempt_240_sec_completed", "official_green_confirmed"):
        if not isinstance(attempts.get(key), bool):
            raise ValueError(f"P7-HOLD-004 group_02 timeout prior attempt {key} must be bool")
    if attempts.get("official_green_confirmed") is not False:
        raise ValueError("P7-HOLD-004 group_02 timeout plan must not claim official green")

    policy = safe_mapping(data.get("timeout_result_policy"))
    expected_policy = {
        "timeout_is_green": False,
        "timeout_is_immediate_fail": False,
        "timeout_classification_required": True,
        "timeout_material_body_free_required": True,
        "batch_split_requires_new_design": True,
        "batch_green_is_group_green": False,
        "collect_only_is_not_execution_green": True,
        "readiness_guard_required_before_official_capture_run": True,
    }
    if set(policy) != set(expected_policy):
        raise ValueError("P7-HOLD-004 group_02 timeout policy keys changed")
    for key, expected in expected_policy.items():
        if policy.get(key) is not expected:
            raise ValueError(f"P7-HOLD-004 group_02 timeout policy {key} mismatch")
    if data.get("timeout_material_allowed_after_readiness_ready") is not readiness_ready:
        raise ValueError("P7-HOLD-004 group_02 timeout material allowance mismatch")
    for key in (
        "can_claim_group_green",
        "can_claim_full_backend_suite_green",
        "full_backend_suite_green_confirmed",
        "hold004_close_allowed",
        "p7_complete",
        "p8_start_allowed",
        "release_allowed",
        "terminal_output_retained",
        "stdout_retained",
        "stderr_retained",
        "raw_traceback_included",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 group_02 timeout plan must keep {key}=false")
    followups = set(dedupe_identifiers(data.get("required_followup_fixes"), limit=100, max_length=180))
    if "group_02_timeout_classification_required_when_timeout_occurs" not in followups:
        raise ValueError("P7-HOLD-004 group_02 timeout plan must keep timeout classification followup")
    if "group_02_long_run_or_batch_split_requires_separate_design" not in followups:
        raise ValueError("P7-HOLD-004 group_02 timeout plan must keep split design followup")
    _assert_common_release_closed_and_body_free(data, source=source)
    return True


def build_p7_hold004_current_backend_suite_execution_summary() -> dict[str, Any]:
    """Return the default R5 execution summary before any group run results are recorded."""

    return build_p7_hold004_backend_suite_execution_summary()


def assert_p7_hold004_backend_suite_execution_summary_contract(material: Mapping[str, Any]) -> bool:
    """Validate the R5 execution summary and non-promotion boundary."""

    data = safe_mapping(material)
    source = "p7_hold004_backend_suite_execution_summary"
    if data.get("schema_version") != P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 backend execution summary schema_version changed")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError("P7-HOLD-004 backend execution summary must stay in P7-HOLD-004 scope")
    if data.get("implementation_step") != P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_R4_R5_STEP:
        raise ValueError("P7-HOLD-004 backend execution summary implementation_step changed")
    if data.get("summary_id") != P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_ID:
        raise ValueError("P7-HOLD-004 backend execution summary id changed")
    if data.get("plan_id") != P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID:
        raise ValueError("P7-HOLD-004 backend execution summary must be tied to the R3 execution plan")
    if data.get("inventory_id") != P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID:
        raise ValueError("P7-HOLD-004 backend execution summary must be tied to the R2 inventory")
    if data.get("collect_baseline_id") != P7_HOLD004_BACKEND_COLLECT_BASELINE_ID:
        raise ValueError("P7-HOLD-004 backend execution summary must be tied to the R1 collect baseline")
    if data.get("source_mode") != P7_SOURCE_MODE or data.get("source_snapshot_ref") != P7_HOLD004_BACKEND_R4_R5_SOURCE_SNAPSHOT_REF:
        raise ValueError("P7-HOLD-004 backend execution summary must stay on the R4/R5 local snapshot")
    if data.get("git_checked") is not False:
        raise ValueError("P7-HOLD-004 backend execution summary must not claim GitHub verification")

    for key in (
        "current_collect_baseline_reconciled",
        "current_collect_baseline_connected",
        "current_group_inventory_connected",
        "current_execution_plan_connected",
        "previous_baseline_is_not_current",
        "old_baseline_not_used_as_current",
        "baseline_mismatch_blocks_execution",
        "backend_suite_group_02_count_current",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 backend execution material current baseline boundary {key} must be true")
    if data.get("current_collect_file_count") != P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT:
        raise ValueError("P7-HOLD-004 backend execution material current collect file count changed")
    if data.get("current_collect_test_item_count") != P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT:
        raise ValueError("P7-HOLD-004 backend execution material current collect test item count changed")
    if data.get("backend_suite_group_02_file_count") != 19 or data.get("backend_suite_group_02_test_item_count") != 252:
        raise ValueError("P7-HOLD-004 backend execution material must keep current group_02 counts")
    connection = safe_mapping(data.get("matrix_current_baseline_connection"))
    if connection.get("collect_baseline_id") != P7_HOLD004_BACKEND_COLLECT_BASELINE_ID:
        raise ValueError("P7-HOLD-004 backend execution material current baseline connection collect id mismatch")
    if connection.get("old_baseline_used_as_current") is not False:
        raise ValueError("P7-HOLD-004 backend execution material must not use old baseline as current")

    if data.get("expected_group_count") != len(P7_HOLD004_BACKEND_SUITE_GROUP_IDS):
        raise ValueError("P7-HOLD-004 backend execution summary expected_group_count changed")
    if data.get("expected_total_batch_count") != P7_HOLD004_BACKEND_SUITE_TOTAL_BATCH_COUNT:
        raise ValueError("P7-HOLD-004 backend execution summary expected_total_batch_count changed")

    group_statuses = safe_mapping(data.get("group_statuses"))
    if list(group_statuses.keys()) != list(P7_HOLD004_BACKEND_SUITE_GROUP_IDS):
        raise ValueError("P7-HOLD-004 backend execution summary group_statuses keys/order changed")
    normalized_group_statuses: dict[str, str] = {}
    for group_id in P7_HOLD004_BACKEND_SUITE_GROUP_IDS:
        status = _normalize_status_identifier(group_statuses.get(group_id))
        if status not in P7_HOLD004_BACKEND_SUITE_ALLOWED_STATUSES:
            raise ValueError(f"P7-HOLD-004 backend execution summary {group_id} status invalid")
        normalized_group_statuses[group_id] = status

    expected_failed = _status_list(normalized_group_statuses, P7_HOLD004_BACKEND_SUITE_STATUS_FAIL)
    expected_timeout = _status_list(normalized_group_statuses, P7_HOLD004_BACKEND_SUITE_STATUS_TIMEOUT)
    expected_collection_failed = _status_list(
        normalized_group_statuses,
        P7_HOLD004_BACKEND_SUITE_STATUS_COLLECTION_FAILED,
    )
    expected_interrupted = _status_list(normalized_group_statuses, P7_HOLD004_BACKEND_SUITE_STATUS_INTERRUPTED)
    expected_blocked = _status_list(
        normalized_group_statuses,
        P7_HOLD004_BACKEND_SUITE_STATUS_BLOCKED_BY_PREVIOUS_RED,
    )
    expected_not_run = _status_list(normalized_group_statuses, P7_HOLD004_BACKEND_SUITE_STATUS_NOT_RUN)
    expected_green = [
        group_id
        for group_id in P7_HOLD004_BACKEND_SUITE_GROUP_IDS
        if normalized_group_statuses[group_id] in P7_HOLD004_BACKEND_SUITE_GREEN_STATUSES
    ]
    if data.get("failed_group_ids") != expected_failed:
        raise ValueError("P7-HOLD-004 backend execution summary failed_group_ids mismatch")
    if data.get("timeout_group_ids") != expected_timeout:
        raise ValueError("P7-HOLD-004 backend execution summary timeout_group_ids mismatch")
    if data.get("collection_failed_group_ids") != expected_collection_failed:
        raise ValueError("P7-HOLD-004 backend execution summary collection_failed_group_ids mismatch")
    if data.get("interrupted_group_ids") != expected_interrupted:
        raise ValueError("P7-HOLD-004 backend execution summary interrupted_group_ids mismatch")
    if data.get("blocked_group_ids") != expected_blocked:
        raise ValueError("P7-HOLD-004 backend execution summary blocked_group_ids mismatch")
    if data.get("not_run_group_ids") != expected_not_run:
        raise ValueError("P7-HOLD-004 backend execution summary not_run_group_ids mismatch")
    if data.get("green_group_ids") != expected_green:
        raise ValueError("P7-HOLD-004 backend execution summary green_group_ids mismatch")

    partial_group_ids = dedupe_identifiers(data.get("partial_group_ids"), limit=40, max_length=120)
    if any(group_id not in P7_HOLD004_BACKEND_SUITE_GROUP_IDS for group_id in partial_group_ids):
        raise ValueError("P7-HOLD-004 backend execution summary partial_group_ids invalid")
    expected_all_groups_executed = not (expected_not_run or expected_blocked or partial_group_ids)
    if data.get("all_groups_executed") is not expected_all_groups_executed:
        raise ValueError("P7-HOLD-004 backend execution summary all_groups_executed mismatch")
    expected_split_all_green = (
        expected_all_groups_executed
        and len(expected_green) == len(P7_HOLD004_BACKEND_SUITE_GROUP_IDS)
        and not (expected_failed or expected_timeout or expected_collection_failed or expected_interrupted)
    )
    if data.get("split_all_groups_green_confirmed") is not expected_split_all_green:
        raise ValueError("P7-HOLD-004 backend execution summary split_all_groups_green_confirmed mismatch")

    first_red = safe_mapping(data.get("first_red"))
    if expected_failed:
        if first_red.get("present") is not True:
            raise ValueError("P7-HOLD-004 backend execution summary must expose first_red when failed groups exist")
        if clean_identifier(first_red.get("group_id"), max_length=120) not in expected_failed:
            raise ValueError("P7-HOLD-004 backend execution summary first_red group mismatch")
        for key in ("batch_id", "nodeid", "file_ref", "failure_kind", "owner_layer_candidate"):
            if not clean_identifier(first_red.get(key), max_length=240):
                raise ValueError(f"P7-HOLD-004 backend execution summary first_red.{key} missing")
    else:
        if first_red.get("present") is not False:
            raise ValueError("P7-HOLD-004 backend execution summary must not expose first_red without failed groups")
        if any(first_red.get(key) for key in ("group_id", "batch_id", "nodeid", "file_ref", "failure_kind", "owner_layer_candidate")):
            raise ValueError("P7-HOLD-004 backend execution summary first_red identifiers must be empty")

    first_timeout = safe_mapping(data.get("first_timeout"))
    if expected_timeout:
        if first_timeout.get("present") is not True:
            raise ValueError("P7-HOLD-004 backend execution summary must expose first_timeout when timeout groups exist")
        if clean_identifier(first_timeout.get("group_id"), max_length=120) not in expected_timeout:
            raise ValueError("P7-HOLD-004 backend execution summary first_timeout group mismatch")
        if clean_identifier(first_timeout.get("batch_id"), max_length=160) == "":
            raise ValueError("P7-HOLD-004 backend execution summary first_timeout.batch_id missing")
        if _coerce_non_negative_int(first_timeout.get("timeout_budget_sec"), default=0) <= 0:
            raise ValueError("P7-HOLD-004 backend execution summary first_timeout.timeout_budget_sec missing")
    else:
        if first_timeout.get("present") is not False:
            raise ValueError("P7-HOLD-004 backend execution summary must not expose first_timeout without timeout groups")
        if any(first_timeout.get(key) for key in ("group_id", "batch_id", "elapsed_sec_bucket", "last_known_phase")):
            raise ValueError("P7-HOLD-004 backend execution summary first_timeout identifiers must be empty")
        if first_timeout.get("timeout_budget_sec") != 0:
            raise ValueError("P7-HOLD-004 backend execution summary first_timeout timeout budget must be 0")

    recorded_statuses = [safe_mapping(item) for item in listify(data.get("recorded_batch_statuses"))]
    recorded_run_result_count = _coerce_non_negative_int(data.get("recorded_run_result_count"), default=-1)
    if data.get("recorded_run_result_count") != recorded_run_result_count or recorded_run_result_count < 0:
        raise ValueError("P7-HOLD-004 backend execution summary recorded_run_result_count invalid")
    if recorded_run_result_count != len(recorded_statuses):
        raise ValueError("P7-HOLD-004 backend execution summary recorded_run_result_count mismatch")
    if data.get("group_run_results_recorded") is not bool(recorded_statuses):
        raise ValueError("P7-HOLD-004 backend execution summary group_run_results_recorded mismatch")
    for item in recorded_statuses:
        group_id = clean_identifier(item.get("group_id"), max_length=120)
        status = _normalize_status_identifier(item.get("status"))
        if group_id not in P7_HOLD004_BACKEND_SUITE_GROUP_IDS:
            raise ValueError("P7-HOLD-004 backend execution summary recorded batch group invalid")
        if clean_identifier(item.get("batch_id"), max_length=160) not in _expected_batch_ids_for_group(group_id):
            raise ValueError("P7-HOLD-004 backend execution summary recorded batch id invalid")
        if status not in P7_HOLD004_BACKEND_SUITE_ALLOWED_STATUSES:
            raise ValueError("P7-HOLD-004 backend execution summary recorded batch status invalid")

    for forbidden_flag in ("raw_traceback_included", "terminal_output_retained", "stdout_retained", "stderr_retained"):
        if data.get(forbidden_flag) is not False:
            raise ValueError(f"P7-HOLD-004 backend execution summary must keep {forbidden_flag}=false")
    if data.get("split_all_groups_green_confirmed") is True:
        if data.get("full_backend_suite_green_confirmed") is not False:
            raise ValueError("split green must not become full backend suite green")
        followups = set(dedupe_identifiers(data.get("required_followup_fixes"), limit=160, max_length=180))
        if "split_green_is_not_full_backend_suite_green" not in followups:
            raise ValueError("split green summary must keep non-promotion followup")

    _assert_common_release_closed_and_body_free(data, source=source)
    return True


__all__ = [
    "P7_HOLD004_BACKEND_R4_R5_SOURCE_SNAPSHOT_REF",
    "P7_HOLD004_PREVIOUS_BACKEND_COLLECT_BASELINE_ID",
    "P7_HOLD004_BACKEND_SUITE_ALLOWED_STATUSES",
    "P7_HOLD004_BACKEND_SUITE_BACKEND_SPLIT_COMPATIBLE_STATUS_BY_STATUS",
    "P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_ID",
    "P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_SCHEMA_VERSION",
    "P7_HOLD004_BACKEND_SUITE_GROUP_RUN_RESULT_SCHEMA_VERSION",
    "P7_HOLD004_BACKEND_SUITE_GREEN_STATUSES",
    "P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_R4_R5_STEP",
    "P7_HOLD004_BACKEND_SUITE_STATUS_BLOCKED_BY_PREVIOUS_RED",
    "P7_HOLD004_BACKEND_SUITE_STATUS_COLLECTION_FAILED",
    "P7_HOLD004_BACKEND_SUITE_STATUS_FAIL",
    "P7_HOLD004_BACKEND_SUITE_STATUS_INTERRUPTED",
    "P7_HOLD004_BACKEND_SUITE_STATUS_NOT_RUN",
    "P7_HOLD004_BACKEND_SUITE_STATUS_PASS",
    "P7_HOLD004_BACKEND_SUITE_STATUS_PASS_WITH_SKIPS",
    "P7_HOLD004_BACKEND_SUITE_STATUS_TIMEOUT",
    "P7_HOLD004_GROUP02_OFFICIAL_BATCH_ID",
    "P7_HOLD004_GROUP02_OFFICIAL_FILE_COUNT",
    "P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID",
    "P7_HOLD004_GROUP02_OFFICIAL_TEST_ITEM_COUNT",
    "P7_HOLD004_GROUP02_OFFICIAL_WARNINGS_COUNT",
    "P7_HOLD004_GROUP02_TIMEOUT_CLASSIFICATION_PLAN_ID",
    "P7_HOLD004_GROUP02_TIMEOUT_CLASSIFICATION_PLAN_SCHEMA_VERSION",
    "P7_HOLD004_GROUP02_TIMEOUT_CLASSIFICATION_PLAN_STEP",
    "P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_BLOCKED",
    "P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_BLOCKED_BY_READINESS_GUARD",
    "P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_GREEN",
    "P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_COLLECTION_FAILED",
    "P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_INTERRUPTED",
    "P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_RED",
    "P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_TIMEOUT",
    "P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_REJECTED_BASELINE_MISMATCH",
    "P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_REJECTED_BODY_OR_CONTRACT",
    "P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_REJECTED_COLLECT_COUNT_MISMATCH",
    "P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_REJECTED_GROUP_OR_BATCH_MISMATCH",
    "P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_REJECTED_PLAN_MISMATCH",
    "P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_REJECTED_STATUS_OR_COUNTS_MISMATCH",
    "P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_ADOPTION_DECISION_SCHEMA_VERSION",
    "P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_ADOPTION_RULE_ID",
    "P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_ADOPTION_RULE_SCHEMA_VERSION",
    "P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_ADOPTION_STEP",
    "P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION",
    "P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION_V2",
    "P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_ALLOWED_SCHEMA_VERSIONS",
    "P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_ID",
    "P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_AFTER_REFRESH_ID",
    "P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STEP",
    "P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_AFTER_REFRESH_STEP",
    "P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY",
    "P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_ITEM_FINGERPRINT_MISMATCH",
    "P7_HOLD004_RECEIVED_SNAPSHOT_ITEM_FINGERPRINT_MISMATCH_BLOCKER_REF",
    "P7_HOLD004_RECEIVED_SNAPSHOT_SOURCE_IDENTITY_BLOCKER_REF",
    "P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_GUARD_BLOCKER_REF",
    "P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_SCHEMA_VERSION",
    "P7_HOLD004_POST_ADOPTION_RECEIVED_SNAPSHOT_RECONCILE_ID",
    "P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_SCHEMA_VERSION",
    "P7_HOLD004_RUNTIME_BUILDER_REFRESH_STATUS_ID",
    "P7_HOLD004_ACTIVE_BASELINE_REFRESH_ID",
    "assert_p7_hold004_backend_suite_execution_summary_contract",
    "assert_p7_hold004_group02_timeout_classification_plan_contract",
    "assert_p7_hold004_official_group02_capture_adoption_decision_contract",
    "assert_p7_hold004_official_group02_capture_adoption_rule_contract",
    "assert_p7_hold004_official_group02_capture_readiness_contract",
    "assert_p7_hold004_backend_suite_group_run_result_contract",
    "build_p7_hold004_backend_suite_execution_summary",
    "build_p7_hold004_backend_suite_group_run_result",
    "build_p7_hold004_current_backend_suite_execution_summary",
    "build_p7_hold004_group02_timeout_classification_plan",
    "build_p7_hold004_official_group02_capture_adoption_decision",
    "build_p7_hold004_official_group02_capture_adoption_rule",
    "build_p7_hold004_official_group02_capture_readiness",
    "normalize_p7_hold004_backend_suite_group_run_status",
]
