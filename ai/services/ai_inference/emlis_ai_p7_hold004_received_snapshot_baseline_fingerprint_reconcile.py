# -*- coding: utf-8 -*-
"""P7-HOLD-004 received snapshot baseline fingerprint reconcile materials.

R21/R24 scope only:
- keep the active source snapshot reference and the newly received zip reference
  as separate identifiers;
- record the received ``pytest --collect-only`` summary as body-free material;
- compare the active baseline and received collect fingerprints without root
  cause overclaim;
- separate source identity and adoption decision so the received zip is not
  promoted to the active source_snapshot_ref while the item fingerprint mismatch
  remains unclassified;
- do not update the active baseline, group inventory, execution plan, matrices,
  release handoff, RN UI, API contract, DB schema, or Emlis runtime behavior.

This module stores identifiers, counts, booleans, enum-like statuses, and
SHA-256 hashes only.  It must never serialize raw input, comment_text bodies,
candidate bodies, surface bodies, pytest nodeid lists, terminal output,
stdout/stderr, or traceback bodies.
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
    public_contract_flags,
    safe_mapping,
)
from emlis_ai_p7_hold004_backend_suite_split_consistency import (
    P7_HOLD004_BACKEND_COLLECT_BASELINE_ID,
    P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM,
    P7_HOLD004_BACKEND_COLLECT_STATUS_COLLECTED,
    P7_HOLD004_BACKEND_COLLECT_WARNINGS_COUNT,
    P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT,
    P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT,
    P7_HOLD004_BACKEND_SOURCE_SNAPSHOT_REF,
    P7_HOLD004_BACKEND_SUITE_HOLD_ID,
    P7_HOLD004_BACKEND_TEST_FILES_FINGERPRINT_SHA256,
    P7_HOLD004_BACKEND_TEST_ITEMS_FINGERPRINT_SHA256,
    build_p7_hold004_backend_collect_summary_from_nodeids,
)

P7_HOLD004_RECEIVED_SNAPSHOT_SCOPE_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.received_snapshot_scope_freeze.v1"
)
P7_HOLD004_RECEIVED_SNAPSHOT_COLLECT_SUMMARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.received_snapshot_collect_summary.v1"
)
P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.received_snapshot_baseline_fingerprint_reconcile.v1"
)
P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_ADOPTION_DECISION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.received_snapshot_baseline_adoption_decision.v1"
)
P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_STEP: Final = (
    "P7-HOLD-004_ReceivedSnapshotBaselineFingerprintReconcile_R21_R24_20260615"
)
P7_HOLD004_RECEIVED_SNAPSHOT_SCOPE_FREEZE_ID: Final = (
    "p7_hold004_received_snapshot_scope_freeze_20260615"
)
P7_HOLD004_RECEIVED_SNAPSHOT_COLLECT_SUMMARY_ID: Final = (
    "p7_hold004_received_snapshot_collect_summary_20260615"
)
P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_ID: Final = (
    "p7_hold004_received_snapshot_baseline_fingerprint_reconcile_20260615"
)
P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_ADOPTION_DECISION_ID: Final = (
    "p7_hold004_received_snapshot_baseline_adoption_decision_20260615"
)
P7_HOLD004_RECEIVED_SNAPSHOT_CANDIDATE_NEW_BASELINE_ID: Final = (
    "p7_hold004_backend_collect_baseline_20260615_received_148"
)
P7_HOLD004_RECEIVED_COLLECT_COMMAND_ID: Final = "pytest_collect_only_backend_received_20260615"
P7_HOLD004_RECEIVED_ZIP_REF: Final = "mashos-api(148).zip"
P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT: Final = P7_HOLD004_BACKEND_COLLECT_BASELINE_ID
P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT: Final = P7_HOLD004_BACKEND_SOURCE_SNAPSHOT_REF
P7_HOLD004_ACTIVE_TEST_ITEMS_FINGERPRINT_SHA256_AT_RECEIPT: Final = (
    P7_HOLD004_BACKEND_TEST_ITEMS_FINGERPRINT_SHA256
)
P7_HOLD004_ACTIVE_TEST_FILES_FINGERPRINT_SHA256_AT_RECEIPT: Final = (
    P7_HOLD004_BACKEND_TEST_FILES_FINGERPRINT_SHA256
)

P7_HOLD004_RECEIVED_COLLECTED_TEST_FILE_COUNT: Final = 425
P7_HOLD004_RECEIVED_COLLECTED_TEST_ITEM_COUNT: Final = 2856
P7_HOLD004_RECEIVED_COLLECT_WARNINGS_COUNT: Final = 1
P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256: Final = (
    "4698ce5240707f71fc3678a0153a15626ba9718fbadad83294e57d11946c2e0d"
)
P7_HOLD004_RECEIVED_TEST_FILES_FINGERPRINT_SHA256: Final = (
    "6866231daf68427dca2de1b2011feea49450f7b4a8b3c5b9dec0f9ccd5f3e9c6"
)

P7_HOLD004_RECEIVED_RECONCILE_STATUS_MATCHES_ACTIVE_BASELINE: Final = (
    "RECEIVED_SNAPSHOT_MATCHES_ACTIVE_BASELINE"
)
P7_HOLD004_RECEIVED_RECONCILE_STATUS_ITEM_FINGERPRINT_MISMATCH_UNCLASSIFIED: Final = (
    "ITEM_FINGERPRINT_MISMATCH_UNCLASSIFIED"
)
P7_HOLD004_RECEIVED_RECONCILE_STATUS_SOURCE_SNAPSHOT_DIFFERS_ITEM_HASH_MATCHES: Final = (
    "SOURCE_SNAPSHOT_REF_DIFFERS_ITEM_HASH_MATCHES"
)
P7_HOLD004_RECEIVED_RECONCILE_STATUS_COUNT_MISMATCH_BLOCKER: Final = "COUNT_MISMATCH_BLOCKER"
P7_HOLD004_RECEIVED_RECONCILE_STATUS_FILE_FINGERPRINT_MISMATCH_BLOCKER: Final = (
    "FILE_FINGERPRINT_MISMATCH_BLOCKER"
)
P7_HOLD004_RECEIVED_RECONCILE_STATUS_COLLECTION_FAILED_BLOCKER: Final = "COLLECTION_FAILED_BLOCKER"
P7_HOLD004_RECEIVED_RECONCILE_STATUS_UNSTABLE_COLLECT_BLOCKER: Final = "UNSTABLE_COLLECT_BLOCKER"
P7_HOLD004_RECEIVED_RECONCILE_STATUSES: Final[frozenset[str]] = frozenset(
    {
        P7_HOLD004_RECEIVED_RECONCILE_STATUS_MATCHES_ACTIVE_BASELINE,
        P7_HOLD004_RECEIVED_RECONCILE_STATUS_ITEM_FINGERPRINT_MISMATCH_UNCLASSIFIED,
        P7_HOLD004_RECEIVED_RECONCILE_STATUS_SOURCE_SNAPSHOT_DIFFERS_ITEM_HASH_MATCHES,
        P7_HOLD004_RECEIVED_RECONCILE_STATUS_COUNT_MISMATCH_BLOCKER,
        P7_HOLD004_RECEIVED_RECONCILE_STATUS_FILE_FINGERPRINT_MISMATCH_BLOCKER,
        P7_HOLD004_RECEIVED_RECONCILE_STATUS_COLLECTION_FAILED_BLOCKER,
        P7_HOLD004_RECEIVED_RECONCILE_STATUS_UNSTABLE_COLLECT_BLOCKER,
    }
)
P7_HOLD004_RECEIVED_ROOT_CAUSE_STATUS_UNCLASSIFIED: Final = "UNCLASSIFIED"
P7_HOLD004_RECEIVED_ROOT_CAUSE_STATUSES: Final[frozenset[str]] = frozenset(
    {
        P7_HOLD004_RECEIVED_ROOT_CAUSE_STATUS_UNCLASSIFIED,
        "BASELINE_CONSTANT_STALE",
        "SOURCE_SNAPSHOT_REF_STALE",
        "PYTEST_NODEID_FORMAT_CHANGED",
        "PYTEST_PLUGIN_OR_ENVIRONMENT_CHANGED",
        "TEST_NODEID_SET_CHANGED_WITH_SAME_COUNTS",
        "TEST_SEMANTICS_CHANGED_WITHOUT_COUNT_DELTA",
        "FINGERPRINT_ALGORITHM_MISMATCH",
        "COLLECT_OUTPUT_PARSER_MISMATCH",
    }
)
P7_HOLD004_RECEIVED_ADOPTION_STATUS_BLOCKED_UNCLASSIFIED_ITEM_FINGERPRINT_MISMATCH: Final = (
    "BLOCKED_UNCLASSIFIED_ITEM_FINGERPRINT_MISMATCH"
)
P7_HOLD004_RECEIVED_ADOPTION_STATUS_BLOCKED_SOURCE_SNAPSHOT_IDENTITY_UNCLEAR: Final = (
    "BLOCKED_SOURCE_SNAPSHOT_IDENTITY_UNCLEAR"
)
P7_HOLD004_RECEIVED_ADOPTION_STATUS_BLOCKED_UNSTABLE_REPEAT_COLLECT: Final = (
    "BLOCKED_UNSTABLE_REPEAT_COLLECT"
)
P7_HOLD004_RECEIVED_ADOPTION_STATUS_REJECTED_COUNT_MISMATCH: Final = "REJECTED_COUNT_MISMATCH"
P7_HOLD004_RECEIVED_ADOPTION_STATUS_REJECTED_FILE_FINGERPRINT_MISMATCH: Final = (
    "REJECTED_FILE_FINGERPRINT_MISMATCH"
)
P7_HOLD004_RECEIVED_ADOPTION_STATUS_REQUIRES_TEST_SEMANTICS_REVIEW: Final = (
    "REQUIRES_TEST_SEMANTICS_REVIEW"
)
P7_HOLD004_RECEIVED_ADOPTION_STATUS_ADOPTABLE_AS_RECEIVED_SNAPSHOT_BASELINE_REFRESH: Final = (
    "ADOPTABLE_AS_RECEIVED_SNAPSHOT_BASELINE_REFRESH"
)
P7_HOLD004_RECEIVED_ADOPTION_STATUS_REFERENCE_ONLY_NO_ACTIVE_UPDATE: Final = "REFERENCE_ONLY_NO_ACTIVE_UPDATE"
P7_HOLD004_RECEIVED_ADOPTION_STATUSES: Final[frozenset[str]] = frozenset(
    {
        P7_HOLD004_RECEIVED_ADOPTION_STATUS_BLOCKED_UNCLASSIFIED_ITEM_FINGERPRINT_MISMATCH,
        P7_HOLD004_RECEIVED_ADOPTION_STATUS_BLOCKED_SOURCE_SNAPSHOT_IDENTITY_UNCLEAR,
        P7_HOLD004_RECEIVED_ADOPTION_STATUS_BLOCKED_UNSTABLE_REPEAT_COLLECT,
        P7_HOLD004_RECEIVED_ADOPTION_STATUS_REJECTED_COUNT_MISMATCH,
        P7_HOLD004_RECEIVED_ADOPTION_STATUS_REJECTED_FILE_FINGERPRINT_MISMATCH,
        P7_HOLD004_RECEIVED_ADOPTION_STATUS_REQUIRES_TEST_SEMANTICS_REVIEW,
        P7_HOLD004_RECEIVED_ADOPTION_STATUS_ADOPTABLE_AS_RECEIVED_SNAPSHOT_BASELINE_REFRESH,
        P7_HOLD004_RECEIVED_ADOPTION_STATUS_REFERENCE_ONLY_NO_ACTIVE_UPDATE,
    }
)

P7_HOLD004_RECEIVED_COLLECT_STATUS_COLLECTED: Final = P7_HOLD004_BACKEND_COLLECT_STATUS_COLLECTED
P7_HOLD004_RECEIVED_COLLECT_STATUS_COLLECTION_FAILED: Final = "COLLECTION_FAILED"
P7_HOLD004_RECEIVED_COLLECT_ALLOWED_STATUSES: Final[frozenset[str]] = frozenset(
    {
        P7_HOLD004_RECEIVED_COLLECT_STATUS_COLLECTED,
        P7_HOLD004_RECEIVED_COLLECT_STATUS_COLLECTION_FAILED,
    }
)

_SHA256_HEX_LENGTH: Final = 64
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
    "active_baseline_update_allowed",
    "official_group_02_capture_run_allowed",
    "official_group_02_capture_result_recording_allowed",
    "can_claim_group_green",
    "can_claim_full_backend_suite_green",
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
_IMPLEMENTATION_SCOPE_FLAGS: Final[dict[str, bool]] = {
    "r21_received_snapshot_constants_added": True,
    "r21_received_snapshot_scope_freeze_added": True,
    "r22_received_collect_summary_body_free_added": True,
    "r23_reconcile_material_added": True,
    "r24_adoption_decision_added": True,
    "r25_official_group02_readiness_guard_added": False,
    "r26_matrix_handoff_validation_connected": False,
    "runtime_behavior_change_allowed": False,
    "rn_change_allowed": False,
    "api_contract_change_allowed": False,
    "db_change_allowed": False,
    "active_baseline_change_allowed": False,
    "release_decision_change_allowed": False,
    "p8_implementation_allowed": False,
}
_REQUIRED_FOLLOWUP_FIXES: Final[tuple[str, ...]] = (
    "received_snapshot_collect_item_fingerprint_mismatch_unclassified",
    "received_snapshot_item_fingerprint_root_cause_classification_required",
    "received_snapshot_baseline_adoption_decision_blocked",
    "active_collect_baseline_not_updated_from_received_snapshot",
    "official_group_02_capture_blocked_until_received_snapshot_adoption",
    "full_backend_suite_green_unconfirmed",
)
_RECEIVED_SNAPSHOT_BLOCKER_REFS: Final[tuple[str, ...]] = (
    "received_snapshot_collect_item_fingerprint_mismatch",
    "source_snapshot_ref_identity_unclear",
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


def _coerce_non_negative_int(value: Any, *, default: int = 0) -> int:
    if value is None or value == "" or isinstance(value, bool):
        return int(default)
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return int(default)
    return max(0, number)


def _is_sha256_hex(value: Any) -> bool:
    text = str(value or "").strip()
    return len(text) == _SHA256_HEX_LENGTH and all(ch in "0123456789abcdef" for ch in text)


def _normalize_status_identifier(value: Any) -> str:
    return clean_identifier(value, default=P7_HOLD004_RECEIVED_COLLECT_STATUS_COLLECTION_FAILED, max_length=80).upper()


def _active_baseline_at_receipt_material() -> dict[str, Any]:
    return {
        "baseline_id": P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT,
        "source_snapshot_ref": P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT,
        "collected_test_file_count": P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT,
        "collected_test_item_count": P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT,
        "warnings_count": P7_HOLD004_BACKEND_COLLECT_WARNINGS_COUNT,
        "test_items_fingerprint_sha256": P7_HOLD004_BACKEND_TEST_ITEMS_FINGERPRINT_SHA256,
        "test_files_fingerprint_sha256": P7_HOLD004_BACKEND_TEST_FILES_FINGERPRINT_SHA256,
        "fingerprint_algorithm": P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM,
    }


def _received_default_collect_constants_material() -> dict[str, Any]:
    return {
        "received_zip_ref": P7_HOLD004_RECEIVED_ZIP_REF,
        "collected_test_file_count": P7_HOLD004_RECEIVED_COLLECTED_TEST_FILE_COUNT,
        "collected_test_item_count": P7_HOLD004_RECEIVED_COLLECTED_TEST_ITEM_COUNT,
        "warnings_count": P7_HOLD004_RECEIVED_COLLECT_WARNINGS_COUNT,
        "test_items_fingerprint_sha256": P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256,
        "test_files_fingerprint_sha256": P7_HOLD004_RECEIVED_TEST_FILES_FINGERPRINT_SHA256,
        "fingerprint_algorithm": P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM,
    }


def _received_snapshot_default_collect_match(data: Mapping[str, Any]) -> bool:
    return (
        data.get("received_zip_ref") == P7_HOLD004_RECEIVED_ZIP_REF
        and data.get("collected_test_file_count") == P7_HOLD004_RECEIVED_COLLECTED_TEST_FILE_COUNT
        and data.get("collected_test_item_count") == P7_HOLD004_RECEIVED_COLLECTED_TEST_ITEM_COUNT
        and data.get("warnings_count") == P7_HOLD004_RECEIVED_COLLECT_WARNINGS_COUNT
        and data.get("test_items_fingerprint_sha256") == P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256
        and data.get("test_files_fingerprint_sha256") == P7_HOLD004_RECEIVED_TEST_FILES_FINGERPRINT_SHA256
    )


def _active_baseline_for_reconcile(active_baseline: Mapping[str, Any] | None = None) -> dict[str, Any]:
    default = _active_baseline_at_receipt_material()
    data = safe_mapping(active_baseline) or default
    return {
        "baseline_id": clean_identifier(data.get("baseline_id", default["baseline_id"]), default=default["baseline_id"]),
        "source_snapshot_ref": clean_identifier(
            data.get("source_snapshot_ref", default["source_snapshot_ref"]),
            default=default["source_snapshot_ref"],
        ),
        "collected_test_file_count": _coerce_non_negative_int(
            data.get("collected_test_file_count", data.get("test_file_count", default["collected_test_file_count"])),
        ),
        "collected_test_item_count": _coerce_non_negative_int(
            data.get("collected_test_item_count", data.get("test_item_count", default["collected_test_item_count"])),
        ),
        "warnings_count": _coerce_non_negative_int(data.get("warnings_count", default["warnings_count"])),
        "test_items_fingerprint_sha256": clean_identifier(
            data.get("test_items_fingerprint_sha256", default["test_items_fingerprint_sha256"]),
            default=default["test_items_fingerprint_sha256"],
            max_length=_SHA256_HEX_LENGTH,
        ),
        "test_files_fingerprint_sha256": clean_identifier(
            data.get("test_files_fingerprint_sha256", default["test_files_fingerprint_sha256"]),
            default=default["test_files_fingerprint_sha256"],
            max_length=_SHA256_HEX_LENGTH,
        ),
        "fingerprint_algorithm": P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM,
    }


def _received_snapshot_for_reconcile(received_collect_summary: Mapping[str, Any] | None = None) -> dict[str, Any]:
    data = safe_mapping(received_collect_summary) or build_p7_hold004_received_snapshot_collect_summary()
    status = _normalize_status_identifier(data.get("collection_status", P7_HOLD004_RECEIVED_COLLECT_STATUS_COLLECTED))
    if status not in P7_HOLD004_RECEIVED_COLLECT_ALLOWED_STATUSES:
        status = P7_HOLD004_RECEIVED_COLLECT_STATUS_COLLECTION_FAILED
    return {
        "received_zip_ref": clean_identifier(
            data.get("received_zip_ref", P7_HOLD004_RECEIVED_ZIP_REF),
            default=P7_HOLD004_RECEIVED_ZIP_REF,
        ),
        "collection_status": status,
        "collected_test_file_count": _coerce_non_negative_int(
            data.get("collected_test_file_count", P7_HOLD004_RECEIVED_COLLECTED_TEST_FILE_COUNT),
        ),
        "collected_test_item_count": _coerce_non_negative_int(
            data.get("collected_test_item_count", P7_HOLD004_RECEIVED_COLLECTED_TEST_ITEM_COUNT),
        ),
        "warnings_count": _coerce_non_negative_int(data.get("warnings_count", P7_HOLD004_RECEIVED_COLLECT_WARNINGS_COUNT)),
        "test_items_fingerprint_sha256": clean_identifier(
            data.get("test_items_fingerprint_sha256", P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256),
            default=P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256,
            max_length=_SHA256_HEX_LENGTH,
        ),
        "test_files_fingerprint_sha256": clean_identifier(
            data.get("test_files_fingerprint_sha256", P7_HOLD004_RECEIVED_TEST_FILES_FINGERPRINT_SHA256),
            default=P7_HOLD004_RECEIVED_TEST_FILES_FINGERPRINT_SHA256,
            max_length=_SHA256_HEX_LENGTH,
        ),
        "fingerprint_algorithm": P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM,
        "pytest_output_retained": False,
        "nodeids_retained": False,
        "terminal_output_retained": False,
        "stdout_retained": False,
        "stderr_retained": False,
        "raw_traceback_included": False,
    }


def _comparison_material(active_baseline: Mapping[str, Any], received_snapshot: Mapping[str, Any]) -> dict[str, bool]:
    file_count_match = active_baseline.get("collected_test_file_count") == received_snapshot.get(
        "collected_test_file_count"
    )
    item_count_match = active_baseline.get("collected_test_item_count") == received_snapshot.get(
        "collected_test_item_count"
    )
    warnings_match = active_baseline.get("warnings_count") == received_snapshot.get("warnings_count")
    files_fingerprint_match = active_baseline.get("test_files_fingerprint_sha256") == received_snapshot.get(
        "test_files_fingerprint_sha256"
    )
    items_fingerprint_match = active_baseline.get("test_items_fingerprint_sha256") == received_snapshot.get(
        "test_items_fingerprint_sha256"
    )
    source_identity_match = active_baseline.get("source_snapshot_ref") == received_snapshot.get("received_zip_ref")
    active_baseline_accepts_received_nodeids = (
        file_count_match and item_count_match and warnings_match and files_fingerprint_match and items_fingerprint_match
    )
    return {
        "file_count_match": file_count_match,
        "item_count_match": item_count_match,
        "counts_match": file_count_match and item_count_match,
        "warning_count_match": warnings_match,
        "warnings_match": warnings_match,
        "test_files_fingerprint_match": files_fingerprint_match,
        "test_items_fingerprint_match": items_fingerprint_match,
        "source_snapshot_ref_matches_received_zip_ref": source_identity_match,
        "source_snapshot_ref_current_for_received_zip": source_identity_match,
        "active_baseline_accepts_received_nodeids": active_baseline_accepts_received_nodeids,
        "active_baseline_accepts_received_collect_nodeids": active_baseline_accepts_received_nodeids,
    }


def _reconcile_status_from_comparison(
    *,
    received_snapshot: Mapping[str, Any],
    comparison: Mapping[str, bool],
) -> str:
    if received_snapshot.get("collection_status") != P7_HOLD004_RECEIVED_COLLECT_STATUS_COLLECTED:
        return P7_HOLD004_RECEIVED_RECONCILE_STATUS_COLLECTION_FAILED_BLOCKER
    if not comparison.get("counts_match", False) or not comparison.get("warning_count_match", False):
        return P7_HOLD004_RECEIVED_RECONCILE_STATUS_COUNT_MISMATCH_BLOCKER
    if not comparison.get("test_files_fingerprint_match", False):
        return P7_HOLD004_RECEIVED_RECONCILE_STATUS_FILE_FINGERPRINT_MISMATCH_BLOCKER
    if not comparison.get("test_items_fingerprint_match", False):
        return P7_HOLD004_RECEIVED_RECONCILE_STATUS_ITEM_FINGERPRINT_MISMATCH_UNCLASSIFIED
    if not comparison.get("source_snapshot_ref_matches_received_zip_ref", False):
        return P7_HOLD004_RECEIVED_RECONCILE_STATUS_SOURCE_SNAPSHOT_DIFFERS_ITEM_HASH_MATCHES
    return P7_HOLD004_RECEIVED_RECONCILE_STATUS_MATCHES_ACTIVE_BASELINE


def _classification_material(status: str) -> dict[str, Any]:
    return {
        "status": status,
        "root_cause_status": P7_HOLD004_RECEIVED_ROOT_CAUSE_STATUS_UNCLASSIFIED,
        "classification_required": status != P7_HOLD004_RECEIVED_RECONCILE_STATUS_MATCHES_ACTIVE_BASELINE,
        "root_cause_classified": False,
        "item_fingerprint_mismatch_unclassified": (
            status == P7_HOLD004_RECEIVED_RECONCILE_STATUS_ITEM_FINGERPRINT_MISMATCH_UNCLASSIFIED
        ),
        "source_identity_unclear": status
        in {
            P7_HOLD004_RECEIVED_RECONCILE_STATUS_ITEM_FINGERPRINT_MISMATCH_UNCLASSIFIED,
            P7_HOLD004_RECEIVED_RECONCILE_STATUS_SOURCE_SNAPSHOT_DIFFERS_ITEM_HASH_MATCHES,
        },
    }


def _reconcile_decision_material(status: str) -> dict[str, Any]:
    official_blocked = status != P7_HOLD004_RECEIVED_RECONCILE_STATUS_MATCHES_ACTIVE_BASELINE
    return {
        "reconcile_status": status,
        "received_snapshot_baseline_fingerprint_reconciled": False,
        "received_snapshot_item_fingerprint_mismatch_unresolved": (
            status == P7_HOLD004_RECEIVED_RECONCILE_STATUS_ITEM_FINGERPRINT_MISMATCH_UNCLASSIFIED
        ),
        "active_baseline_update_allowed": False,
        "official_group_02_capture_run_allowed": False,
        "official_group_02_capture_result_recording_allowed": False,
        "official_group_02_capture_blocked": official_blocked,
        "can_claim_group_green": False,
        "can_claim_full_backend_suite_green": False,
        "full_backend_suite_green_confirmed": False,
        "hold004_close_allowed": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "release_allowed": False,
    }


def _adoption_status_from_reconcile(reconcile: Mapping[str, Any]) -> str:
    classification = safe_mapping(reconcile.get("classification"))
    comparison = safe_mapping(reconcile.get("comparison"))
    status = clean_identifier(classification.get("status"), max_length=120)
    if status == P7_HOLD004_RECEIVED_RECONCILE_STATUS_COUNT_MISMATCH_BLOCKER:
        return P7_HOLD004_RECEIVED_ADOPTION_STATUS_REJECTED_COUNT_MISMATCH
    if status == P7_HOLD004_RECEIVED_RECONCILE_STATUS_FILE_FINGERPRINT_MISMATCH_BLOCKER:
        return P7_HOLD004_RECEIVED_ADOPTION_STATUS_REJECTED_FILE_FINGERPRINT_MISMATCH
    if status == P7_HOLD004_RECEIVED_RECONCILE_STATUS_ITEM_FINGERPRINT_MISMATCH_UNCLASSIFIED:
        return P7_HOLD004_RECEIVED_ADOPTION_STATUS_BLOCKED_UNCLASSIFIED_ITEM_FINGERPRINT_MISMATCH
    if not comparison.get("source_snapshot_ref_matches_received_zip_ref", False):
        return P7_HOLD004_RECEIVED_ADOPTION_STATUS_BLOCKED_SOURCE_SNAPSHOT_IDENTITY_UNCLEAR
    return P7_HOLD004_RECEIVED_ADOPTION_STATUS_REFERENCE_ONLY_NO_ACTIVE_UPDATE


def build_p7_hold004_received_snapshot_scope_freeze() -> dict[str, Any]:
    """Build the R21/R24 scope-freeze material for the received snapshot."""

    material = {
        "schema_version": P7_HOLD004_RECEIVED_SNAPSHOT_SCOPE_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_STEP,
        "implementation_step": P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_STEP,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "scope_freeze_id": P7_HOLD004_RECEIVED_SNAPSHOT_SCOPE_FREEZE_ID,
        "source_mode": P7_SOURCE_MODE,
        "active_baseline_id_at_receipt": P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT,
        "active_source_snapshot_ref_at_receipt": P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT,
        "received_zip_ref": P7_HOLD004_RECEIVED_ZIP_REF,
        "reconcile_schema_version_reserved": P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_SCHEMA_VERSION,
        "reconcile_id_reserved": P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_ID,
        "adoption_decision_schema_version_reserved": P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_ADOPTION_DECISION_SCHEMA_VERSION,
        "adoption_decision_id_reserved": P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_ADOPTION_DECISION_ID,
        "git_checked": P7_GIT_CHECKED,
        "scope_status": "RECEIVED_SNAPSHOT_SCOPE_FROZEN_R21_R24",
        "source_identity_separated": True,
        "received_zip_promoted_to_source_snapshot_ref": False,
        "active_baseline_updated": False,
        "received_collect_summary_builder_added": True,
        "received_reconcile_material_builder_added": True,
        "received_adoption_decision_builder_added": True,
        "active_baseline": _active_baseline_at_receipt_material(),
        "received_collect_constants": _received_default_collect_constants_material(),
        "implementation_scope": dict(_IMPLEMENTATION_SCOPE_FLAGS),
        "boundary_flags": _false_boundary_flags(),
        **_release_closed_boundary(),
        **_capture_closed_boundary(),
        "unresolved_hold_refs": [P7_HOLD004_BACKEND_SUITE_HOLD_ID],
        "required_followup_fixes": list(_REQUIRED_FOLLOWUP_FIXES),
        "public_contract": _public_contract_boundary_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_hold004_received_snapshot_scope_freeze_contract(material)
    return material


def build_p7_hold004_received_snapshot_collect_summary(
    *,
    received_zip_ref: Any = P7_HOLD004_RECEIVED_ZIP_REF,
    collect_command_id: Any = P7_HOLD004_RECEIVED_COLLECT_COMMAND_ID,
    collection_status: Any = P7_HOLD004_RECEIVED_COLLECT_STATUS_COLLECTED,
    collected_test_file_count: Any = P7_HOLD004_RECEIVED_COLLECTED_TEST_FILE_COUNT,
    collected_test_item_count: Any = P7_HOLD004_RECEIVED_COLLECTED_TEST_ITEM_COUNT,
    warnings_count: Any = P7_HOLD004_RECEIVED_COLLECT_WARNINGS_COUNT,
    test_items_fingerprint_sha256: Any = P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256,
    test_files_fingerprint_sha256: Any = P7_HOLD004_RECEIVED_TEST_FILES_FINGERPRINT_SHA256,
    collected_test_nodeids: Iterable[Any] | None = None,
) -> dict[str, Any]:
    """Build the R22 received collect summary without retaining pytest bodies."""

    if collected_test_nodeids is not None:
        summary = build_p7_hold004_backend_collect_summary_from_nodeids(collected_test_nodeids)
        collected_test_file_count = summary["collected_test_file_count"]
        collected_test_item_count = summary["collected_test_item_count"]
        test_items_fingerprint_sha256 = summary["test_items_fingerprint_sha256"]
        test_files_fingerprint_sha256 = summary["test_files_fingerprint_sha256"]

    status = _normalize_status_identifier(collection_status)
    if status not in P7_HOLD004_RECEIVED_COLLECT_ALLOWED_STATUSES:
        status = P7_HOLD004_RECEIVED_COLLECT_STATUS_COLLECTION_FAILED

    if status != P7_HOLD004_RECEIVED_COLLECT_STATUS_COLLECTED:
        collected_test_file_count = 0
        collected_test_item_count = 0
        warnings_count = 0
        test_items_fingerprint_sha256 = ""
        test_files_fingerprint_sha256 = ""

    material = {
        "schema_version": P7_HOLD004_RECEIVED_SNAPSHOT_COLLECT_SUMMARY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_STEP,
        "implementation_step": P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_STEP,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "summary_id": P7_HOLD004_RECEIVED_SNAPSHOT_COLLECT_SUMMARY_ID,
        "source_mode": P7_SOURCE_MODE,
        "active_source_snapshot_ref_at_receipt": P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT,
        "active_baseline_id_at_receipt": P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT,
        "received_zip_ref": clean_identifier(received_zip_ref, default=P7_HOLD004_RECEIVED_ZIP_REF, max_length=160),
        "git_checked": P7_GIT_CHECKED,
        "collect_command_id": clean_identifier(
            collect_command_id,
            default=P7_HOLD004_RECEIVED_COLLECT_COMMAND_ID,
            max_length=160,
        ),
        "collection_status": status,
        "collected_test_file_count": _coerce_non_negative_int(collected_test_file_count),
        "collected_test_item_count": _coerce_non_negative_int(collected_test_item_count),
        "warnings_count": _coerce_non_negative_int(warnings_count),
        "test_items_fingerprint_sha256": clean_identifier(test_items_fingerprint_sha256, max_length=_SHA256_HEX_LENGTH),
        "test_files_fingerprint_sha256": clean_identifier(test_files_fingerprint_sha256, max_length=_SHA256_HEX_LENGTH),
        "fingerprint_algorithm": P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM,
        "received_snapshot_collect_matches_recorded_default": False,
        "pytest_output_retained": False,
        "nodeids_retained": False,
        "terminal_output_retained": False,
        "stdout_retained": False,
        "stderr_retained": False,
        "raw_traceback_included": False,
        "received_zip_promoted_to_source_snapshot_ref": False,
        "active_baseline_updated_from_received_snapshot": False,
        "collect_only_is_not_execution_green": True,
        **_release_closed_boundary(),
        **_capture_closed_boundary(),
        "unresolved_hold_refs": [P7_HOLD004_BACKEND_SUITE_HOLD_ID],
        "required_followup_fixes": list(_REQUIRED_FOLLOWUP_FIXES),
        "public_contract": _public_contract_boundary_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material["received_snapshot_collect_matches_recorded_default"] = _received_snapshot_default_collect_match(material)
    assert_p7_hold004_received_snapshot_collect_summary_contract(material)
    return material


def build_p7_hold004_received_snapshot_baseline_fingerprint_reconcile(
    *,
    active_baseline: Mapping[str, Any] | None = None,
    received_collect_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the R23 active-vs-received fingerprint reconcile material."""

    active = _active_baseline_for_reconcile(active_baseline)
    received = _received_snapshot_for_reconcile(received_collect_summary)
    comparison = _comparison_material(active, received)
    status = _reconcile_status_from_comparison(received_snapshot=received, comparison=comparison)
    material = {
        "schema_version": P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_STEP,
        "implementation_step": P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_STEP,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "reconcile_id": P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_ID,
        "source_mode": P7_SOURCE_MODE,
        "git_checked": P7_GIT_CHECKED,
        "active_baseline": active,
        "received_snapshot": received,
        "comparison": comparison,
        "classification": _classification_material(status),
        "decision": _reconcile_decision_material(status),
        "blocker_refs": list(_RECEIVED_SNAPSHOT_BLOCKER_REFS),
        "source_identity_separated": True,
        "received_zip_promoted_to_source_snapshot_ref": False,
        "active_baseline_updated_from_received_snapshot": False,
        "received_snapshot_baseline_fingerprint_reconciled": False,
        "received_snapshot_item_fingerprint_mismatch_unresolved": (
            status == P7_HOLD004_RECEIVED_RECONCILE_STATUS_ITEM_FINGERPRINT_MISMATCH_UNCLASSIFIED
        ),
        "official_group_02_capture_blocked": True,
        **_release_closed_boundary(),
        **_capture_closed_boundary(),
        "unresolved_hold_refs": [P7_HOLD004_BACKEND_SUITE_HOLD_ID],
        "required_followup_fixes": list(_REQUIRED_FOLLOWUP_FIXES),
        "public_contract": _public_contract_boundary_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_hold004_received_snapshot_baseline_fingerprint_reconcile_contract(material)
    return material


def build_p7_hold004_received_snapshot_baseline_adoption_decision(
    *,
    received_snapshot_reconcile: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the R24 source-identity/adoption decision material."""

    reconcile = safe_mapping(received_snapshot_reconcile) or build_p7_hold004_received_snapshot_baseline_fingerprint_reconcile()
    active = safe_mapping(reconcile.get("active_baseline")) or _active_baseline_for_reconcile()
    received = safe_mapping(reconcile.get("received_snapshot")) or _received_snapshot_for_reconcile()
    classification = safe_mapping(reconcile.get("classification"))
    comparison = safe_mapping(reconcile.get("comparison"))
    adoption_status = _adoption_status_from_reconcile(reconcile)
    material = {
        "schema_version": P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_ADOPTION_DECISION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_STEP,
        "implementation_step": P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_STEP,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "decision_id": P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_ADOPTION_DECISION_ID,
        "received_reconcile_id": clean_identifier(
            reconcile.get("reconcile_id"),
            default=P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_ID,
        ),
        "source_mode": P7_SOURCE_MODE,
        "git_checked": P7_GIT_CHECKED,
        "received_zip_ref": clean_identifier(received.get("received_zip_ref"), default=P7_HOLD004_RECEIVED_ZIP_REF),
        "active_baseline_id_at_receipt": clean_identifier(
            active.get("baseline_id"),
            default=P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT,
        ),
        "active_source_snapshot_ref_at_receipt": clean_identifier(
            active.get("source_snapshot_ref"),
            default=P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT,
        ),
        "candidate_new_baseline_id": P7_HOLD004_RECEIVED_SNAPSHOT_CANDIDATE_NEW_BASELINE_ID,
        "source_identity": {
            "received_zip_ref": clean_identifier(received.get("received_zip_ref"), default=P7_HOLD004_RECEIVED_ZIP_REF),
            "active_source_snapshot_ref_at_receipt": clean_identifier(
                active.get("source_snapshot_ref"),
                default=P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT,
            ),
            "source_snapshot_ref_matches_received_zip_ref": bool(
                comparison.get("source_snapshot_ref_matches_received_zip_ref", False)
            ),
            "source_snapshot_ref_current_for_received_zip": bool(
                comparison.get("source_snapshot_ref_current_for_received_zip", False)
            ),
            "received_zip_promoted_to_source_snapshot_ref": False,
            "source_snapshot_ref_update_allowed": False,
        },
        "received_reconcile_status": clean_identifier(
            classification.get("status"),
            default=P7_HOLD004_RECEIVED_RECONCILE_STATUS_ITEM_FINGERPRINT_MISMATCH_UNCLASSIFIED,
        ),
        "adoption_status": adoption_status,
        "root_cause_status": clean_identifier(
            classification.get("root_cause_status"),
            default=P7_HOLD004_RECEIVED_ROOT_CAUSE_STATUS_UNCLASSIFIED,
        ),
        "required_evidence": {
            "repeat_collect_stability_required": True,
            "source_snapshot_identity_review_required": True,
            "test_semantics_review_required": True,
            "baseline_id_or_revision_update_required": True,
            "item_fingerprint_root_cause_classification_required": True,
        },
        "active_baseline_update_allowed": False,
        "source_snapshot_ref_update_allowed": False,
        "same_baseline_id_hash_replacement_allowed": False,
        "received_zip_promoted_to_source_snapshot_ref": False,
        "official_group_02_capture_blocked_until_adopted": True,
        **_capture_closed_boundary(),
        **_release_closed_boundary(),
        "unresolved_hold_refs": [P7_HOLD004_BACKEND_SUITE_HOLD_ID],
        "required_followup_fixes": list(_REQUIRED_FOLLOWUP_FIXES),
        "public_contract": _public_contract_boundary_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_hold004_received_snapshot_baseline_adoption_decision_contract(material)
    return material


def _assert_release_capture_closed_and_body_free(data: Mapping[str, Any], *, source: str) -> None:
    for key in _RELEASE_CLOSED_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=false")
    for key in _CAPTURE_CLOSED_KEYS:
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


def _assert_capture_closed_mapping(data: Mapping[str, Any], *, source: str) -> None:
    for key in _CAPTURE_CLOSED_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=false")


def assert_p7_hold004_received_snapshot_scope_freeze_contract(material: Mapping[str, Any]) -> bool:
    """Validate the R21/R24 received snapshot source-identity freeze."""

    data = safe_mapping(material)
    source = "p7_hold004_received_snapshot_scope_freeze"
    if data.get("schema_version") != P7_HOLD004_RECEIVED_SNAPSHOT_SCOPE_FREEZE_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 received snapshot scope freeze schema_version mismatch")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError("P7-HOLD-004 received snapshot scope freeze scope mismatch")
    if data.get("implementation_step") != P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_STEP:
        raise ValueError("P7-HOLD-004 received snapshot scope freeze implementation_step mismatch")
    if data.get("scope_freeze_id") != P7_HOLD004_RECEIVED_SNAPSHOT_SCOPE_FREEZE_ID:
        raise ValueError("P7-HOLD-004 received snapshot scope freeze id mismatch")
    if data.get("source_mode") != P7_SOURCE_MODE:
        raise ValueError("P7-HOLD-004 received snapshot scope freeze source_mode mismatch")
    if data.get("git_checked") is not False:
        raise ValueError("P7-HOLD-004 received snapshot scope freeze must not claim GitHub verification")
    if data.get("active_baseline_id_at_receipt") != P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT:
        raise ValueError("P7-HOLD-004 received snapshot active baseline id at receipt mismatch")
    if data.get("active_source_snapshot_ref_at_receipt") != P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT:
        raise ValueError("P7-HOLD-004 received snapshot active source snapshot ref at receipt mismatch")
    if data.get("received_zip_ref") != P7_HOLD004_RECEIVED_ZIP_REF:
        raise ValueError("P7-HOLD-004 received snapshot received_zip_ref mismatch")
    if data.get("active_source_snapshot_ref_at_receipt") == data.get("received_zip_ref"):
        raise ValueError("received_zip_ref must remain separate from active source_snapshot_ref at receipt")
    if data.get("received_zip_promoted_to_source_snapshot_ref") is not False:
        raise ValueError("received zip must not be promoted to active source_snapshot_ref in R21/R24")
    if data.get("active_baseline_updated") is not False:
        raise ValueError("active baseline must not be updated in R21/R24")
    if data.get("source_identity_separated") is not True:
        raise ValueError("received snapshot source identity must be explicitly separated")
    if data.get("scope_status") != "RECEIVED_SNAPSHOT_SCOPE_FROZEN_R21_R24":
        raise ValueError("P7-HOLD-004 received snapshot scope status mismatch")
    if data.get("received_reconcile_material_builder_added") is not True:
        raise ValueError("P7-HOLD-004 received snapshot reconcile builder must be marked added")
    if data.get("received_adoption_decision_builder_added") is not True:
        raise ValueError("P7-HOLD-004 received snapshot adoption builder must be marked added")

    implementation_scope = safe_mapping(data.get("implementation_scope"))
    if set(implementation_scope) != set(_IMPLEMENTATION_SCOPE_FLAGS):
        raise ValueError("P7-HOLD-004 received snapshot implementation_scope keys mismatch")
    for key, expected in _IMPLEMENTATION_SCOPE_FLAGS.items():
        if implementation_scope.get(key) is not expected:
            raise ValueError(f"P7-HOLD-004 received snapshot implementation_scope.{key} mismatch")

    boundary_flags = safe_mapping(data.get("boundary_flags"))
    if set(boundary_flags) != set(_BOUNDARY_FLAG_KEYS):
        raise ValueError("P7-HOLD-004 received snapshot boundary_flags keys mismatch")
    assert_false_markers(boundary_flags, source=f"{source}.boundary_flags")

    active_baseline = safe_mapping(data.get("active_baseline"))
    expected_active = _active_baseline_at_receipt_material()
    for key, expected in expected_active.items():
        if active_baseline.get(key) != expected:
            raise ValueError(f"P7-HOLD-004 received snapshot active_baseline.{key} mismatch")

    received_constants = safe_mapping(data.get("received_collect_constants"))
    expected_received = _received_default_collect_constants_material()
    for key, expected in expected_received.items():
        if received_constants.get(key) != expected:
            raise ValueError(f"P7-HOLD-004 received snapshot received_collect_constants.{key} mismatch")

    _assert_release_capture_closed_and_body_free(data, source=source)
    return True


def assert_p7_hold004_received_snapshot_collect_summary_contract(material: Mapping[str, Any]) -> bool:
    """Validate the R22 received collect summary body-free contract."""

    data = safe_mapping(material)
    source = "p7_hold004_received_snapshot_collect_summary"
    if data.get("schema_version") != P7_HOLD004_RECEIVED_SNAPSHOT_COLLECT_SUMMARY_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 received collect summary schema_version mismatch")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError("P7-HOLD-004 received collect summary scope mismatch")
    if data.get("implementation_step") != P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_STEP:
        raise ValueError("P7-HOLD-004 received collect summary implementation_step mismatch")
    if data.get("summary_id") != P7_HOLD004_RECEIVED_SNAPSHOT_COLLECT_SUMMARY_ID:
        raise ValueError("P7-HOLD-004 received collect summary id mismatch")
    if data.get("source_mode") != P7_SOURCE_MODE:
        raise ValueError("P7-HOLD-004 received collect summary source_mode mismatch")
    if data.get("active_source_snapshot_ref_at_receipt") != P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT:
        raise ValueError("P7-HOLD-004 received collect summary active source snapshot ref mismatch")
    if data.get("active_baseline_id_at_receipt") != P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT:
        raise ValueError("P7-HOLD-004 received collect summary active baseline id mismatch")
    if data.get("received_zip_ref") != P7_HOLD004_RECEIVED_ZIP_REF:
        raise ValueError("P7-HOLD-004 received collect summary received_zip_ref mismatch")
    if data.get("git_checked") is not False:
        raise ValueError("P7-HOLD-004 received collect summary must not claim GitHub verification")
    if data.get("collect_command_id") != P7_HOLD004_RECEIVED_COLLECT_COMMAND_ID:
        raise ValueError("P7-HOLD-004 received collect summary collect_command_id mismatch")
    if data.get("collection_status") != P7_HOLD004_RECEIVED_COLLECT_STATUS_COLLECTED:
        raise ValueError("P7-HOLD-004 received collect summary must record the collected received snapshot")
    if data.get("fingerprint_algorithm") != P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM:
        raise ValueError("P7-HOLD-004 received collect summary fingerprint algorithm mismatch")

    for retained_key in (
        "pytest_output_retained",
        "nodeids_retained",
        "terminal_output_retained",
        "stdout_retained",
        "stderr_retained",
        "raw_traceback_included",
        "received_zip_promoted_to_source_snapshot_ref",
        "active_baseline_updated_from_received_snapshot",
    ):
        if data.get(retained_key) is not False:
            raise ValueError(f"P7-HOLD-004 received collect summary must keep {retained_key}=false")
    if data.get("collect_only_is_not_execution_green") is not True:
        raise ValueError("P7-HOLD-004 received collect summary must keep collect-only separate from execution green")

    warnings_count = _coerce_non_negative_int(data.get("warnings_count"), default=-1)
    if data.get("warnings_count") != warnings_count or warnings_count < 0:
        raise ValueError("P7-HOLD-004 received collect summary warnings_count must be a non-negative integer")

    if data.get("collected_test_file_count") != P7_HOLD004_RECEIVED_COLLECTED_TEST_FILE_COUNT:
        raise ValueError("P7-HOLD-004 received collect summary file count mismatch")
    if data.get("collected_test_item_count") != P7_HOLD004_RECEIVED_COLLECTED_TEST_ITEM_COUNT:
        raise ValueError("P7-HOLD-004 received collect summary item count mismatch")
    if data.get("warnings_count") != P7_HOLD004_RECEIVED_COLLECT_WARNINGS_COUNT:
        raise ValueError("P7-HOLD-004 received collect summary warning count mismatch")
    if not _is_sha256_hex(data.get("test_items_fingerprint_sha256")):
        raise ValueError("P7-HOLD-004 received collect summary requires test_items_fingerprint_sha256")
    if not _is_sha256_hex(data.get("test_files_fingerprint_sha256")):
        raise ValueError("P7-HOLD-004 received collect summary requires test_files_fingerprint_sha256")
    if data.get("test_items_fingerprint_sha256") != P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256:
        raise ValueError("P7-HOLD-004 received collect summary item fingerprint mismatch")
    if data.get("test_files_fingerprint_sha256") != P7_HOLD004_RECEIVED_TEST_FILES_FINGERPRINT_SHA256:
        raise ValueError("P7-HOLD-004 received collect summary file fingerprint mismatch")
    if data.get("received_snapshot_collect_matches_recorded_default") is not True:
        raise ValueError("P7-HOLD-004 received collect summary must match the recorded received snapshot constants")
    if data.get("received_snapshot_collect_matches_recorded_default") is not _received_snapshot_default_collect_match(data):
        raise ValueError("P7-HOLD-004 received collect summary default-match marker mismatch")

    _assert_release_capture_closed_and_body_free(data, source=source)
    return True


def assert_p7_hold004_received_snapshot_baseline_fingerprint_reconcile_contract(
    material: Mapping[str, Any],
) -> bool:
    """Validate the R23 active-vs-received fingerprint reconcile material."""

    data = safe_mapping(material)
    source = "p7_hold004_received_snapshot_baseline_fingerprint_reconcile"
    if data.get("schema_version") != P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 received snapshot reconcile schema_version mismatch")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError("P7-HOLD-004 received snapshot reconcile scope mismatch")
    if data.get("implementation_step") != P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_STEP:
        raise ValueError("P7-HOLD-004 received snapshot reconcile implementation_step mismatch")
    if data.get("reconcile_id") != P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_ID:
        raise ValueError("P7-HOLD-004 received snapshot reconcile id mismatch")
    if data.get("source_mode") != P7_SOURCE_MODE:
        raise ValueError("P7-HOLD-004 received snapshot reconcile source_mode mismatch")
    if data.get("git_checked") is not False:
        raise ValueError("P7-HOLD-004 received snapshot reconcile must not claim GitHub verification")

    active = safe_mapping(data.get("active_baseline"))
    expected_active = _active_baseline_at_receipt_material()
    for key, expected in expected_active.items():
        if active.get(key) != expected:
            raise ValueError(f"P7-HOLD-004 received snapshot reconcile active_baseline.{key} mismatch")

    received = safe_mapping(data.get("received_snapshot"))
    if received.get("received_zip_ref") != P7_HOLD004_RECEIVED_ZIP_REF:
        raise ValueError("P7-HOLD-004 received snapshot reconcile received_zip_ref mismatch")
    if received.get("collection_status") != P7_HOLD004_RECEIVED_COLLECT_STATUS_COLLECTED:
        raise ValueError("P7-HOLD-004 received snapshot reconcile collection_status mismatch")
    if received.get("collected_test_file_count") != P7_HOLD004_RECEIVED_COLLECTED_TEST_FILE_COUNT:
        raise ValueError("P7-HOLD-004 received snapshot reconcile received file count mismatch")
    if received.get("collected_test_item_count") != P7_HOLD004_RECEIVED_COLLECTED_TEST_ITEM_COUNT:
        raise ValueError("P7-HOLD-004 received snapshot reconcile received item count mismatch")
    if received.get("warnings_count") != P7_HOLD004_RECEIVED_COLLECT_WARNINGS_COUNT:
        raise ValueError("P7-HOLD-004 received snapshot reconcile received warnings count mismatch")
    if received.get("test_items_fingerprint_sha256") != P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256:
        raise ValueError("P7-HOLD-004 received snapshot reconcile received item fingerprint mismatch")
    if received.get("test_files_fingerprint_sha256") != P7_HOLD004_RECEIVED_TEST_FILES_FINGERPRINT_SHA256:
        raise ValueError("P7-HOLD-004 received snapshot reconcile received file fingerprint mismatch")
    if received.get("fingerprint_algorithm") != P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM:
        raise ValueError("P7-HOLD-004 received snapshot reconcile fingerprint algorithm mismatch")
    for retained_key in (
        "pytest_output_retained",
        "nodeids_retained",
        "terminal_output_retained",
        "stdout_retained",
        "stderr_retained",
        "raw_traceback_included",
    ):
        if received.get(retained_key) is not False:
            raise ValueError(f"P7-HOLD-004 received snapshot reconcile must keep received_snapshot.{retained_key}=false")

    comparison = safe_mapping(data.get("comparison"))
    expected_comparison = {
        "file_count_match": True,
        "item_count_match": True,
        "counts_match": True,
        "warning_count_match": True,
        "warnings_match": True,
        "test_files_fingerprint_match": True,
        "test_items_fingerprint_match": False,
        "source_snapshot_ref_matches_received_zip_ref": False,
        "source_snapshot_ref_current_for_received_zip": False,
        "active_baseline_accepts_received_nodeids": False,
        "active_baseline_accepts_received_collect_nodeids": False,
    }
    if set(comparison) != set(expected_comparison):
        raise ValueError("P7-HOLD-004 received snapshot reconcile comparison keys mismatch")
    for key, expected in expected_comparison.items():
        if comparison.get(key) is not expected:
            raise ValueError(f"P7-HOLD-004 received snapshot reconcile comparison.{key} mismatch")

    classification = safe_mapping(data.get("classification"))
    if classification.get("status") != P7_HOLD004_RECEIVED_RECONCILE_STATUS_ITEM_FINGERPRINT_MISMATCH_UNCLASSIFIED:
        raise ValueError("P7-HOLD-004 received snapshot reconcile status must remain unclassified item mismatch")
    if classification.get("root_cause_status") != P7_HOLD004_RECEIVED_ROOT_CAUSE_STATUS_UNCLASSIFIED:
        raise ValueError("P7-HOLD-004 received snapshot reconcile root cause must remain UNCLASSIFIED")
    if classification.get("classification_required") is not True:
        raise ValueError("P7-HOLD-004 received snapshot reconcile must require classification")
    if classification.get("root_cause_classified") is not False:
        raise ValueError("P7-HOLD-004 received snapshot reconcile root cause must not be classified in R23/R24")
    if classification.get("item_fingerprint_mismatch_unclassified") is not True:
        raise ValueError("P7-HOLD-004 received snapshot reconcile must mark item mismatch unclassified")
    if classification.get("source_identity_unclear") is not True:
        raise ValueError("P7-HOLD-004 received snapshot reconcile must mark source identity unclear")

    decision = safe_mapping(data.get("decision"))
    if decision.get("reconcile_status") != P7_HOLD004_RECEIVED_RECONCILE_STATUS_ITEM_FINGERPRINT_MISMATCH_UNCLASSIFIED:
        raise ValueError("P7-HOLD-004 received snapshot reconcile decision status mismatch")
    if decision.get("received_snapshot_baseline_fingerprint_reconciled") is not False:
        raise ValueError("P7-HOLD-004 received snapshot reconcile must not claim reconciled")
    if decision.get("received_snapshot_item_fingerprint_mismatch_unresolved") is not True:
        raise ValueError("P7-HOLD-004 received snapshot reconcile must keep item mismatch unresolved")
    if decision.get("official_group_02_capture_blocked") is not True:
        raise ValueError("P7-HOLD-004 received snapshot reconcile must block official group_02 capture")
    _assert_capture_closed_mapping(decision, source=f"{source}.decision")
    for key in ("full_backend_suite_green_confirmed", "hold004_close_allowed", "p7_complete", "p8_start_allowed", "release_allowed"):
        if decision.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 received snapshot reconcile decision must keep {key}=false")

    blockers = set(dedupe_identifiers(data.get("blocker_refs"), limit=20, max_length=160))
    for blocker in _RECEIVED_SNAPSHOT_BLOCKER_REFS:
        if blocker not in blockers:
            raise ValueError(f"P7-HOLD-004 received snapshot reconcile missing blocker {blocker}")
    if data.get("source_identity_separated") is not True:
        raise ValueError("P7-HOLD-004 received snapshot reconcile must keep source identity separated")
    if data.get("received_zip_promoted_to_source_snapshot_ref") is not False:
        raise ValueError("P7-HOLD-004 received snapshot reconcile must not promote received zip")
    if data.get("active_baseline_updated_from_received_snapshot") is not False:
        raise ValueError("P7-HOLD-004 received snapshot reconcile must not update active baseline")
    if data.get("received_snapshot_baseline_fingerprint_reconciled") is not False:
        raise ValueError("P7-HOLD-004 received snapshot reconcile must not claim full reconciliation")
    if data.get("received_snapshot_item_fingerprint_mismatch_unresolved") is not True:
        raise ValueError("P7-HOLD-004 received snapshot reconcile must keep item mismatch unresolved")
    if data.get("official_group_02_capture_blocked") is not True:
        raise ValueError("P7-HOLD-004 received snapshot reconcile must keep official capture blocked")

    _assert_release_capture_closed_and_body_free(data, source=source)
    return True


def assert_p7_hold004_received_snapshot_baseline_adoption_decision_contract(
    material: Mapping[str, Any],
) -> bool:
    """Validate the R24 source-identity/adoption decision material."""

    data = safe_mapping(material)
    source = "p7_hold004_received_snapshot_baseline_adoption_decision"
    if data.get("schema_version") != P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_ADOPTION_DECISION_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 received snapshot adoption decision schema_version mismatch")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError("P7-HOLD-004 received snapshot adoption decision scope mismatch")
    if data.get("implementation_step") != P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_STEP:
        raise ValueError("P7-HOLD-004 received snapshot adoption decision implementation_step mismatch")
    if data.get("decision_id") != P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_ADOPTION_DECISION_ID:
        raise ValueError("P7-HOLD-004 received snapshot adoption decision id mismatch")
    if data.get("received_reconcile_id") != P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_ID:
        raise ValueError("P7-HOLD-004 received snapshot adoption decision reconcile id mismatch")
    if data.get("source_mode") != P7_SOURCE_MODE:
        raise ValueError("P7-HOLD-004 received snapshot adoption decision source_mode mismatch")
    if data.get("git_checked") is not False:
        raise ValueError("P7-HOLD-004 received snapshot adoption decision must not claim GitHub verification")
    if data.get("received_zip_ref") != P7_HOLD004_RECEIVED_ZIP_REF:
        raise ValueError("P7-HOLD-004 received snapshot adoption decision received_zip_ref mismatch")
    if data.get("active_baseline_id_at_receipt") != P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT:
        raise ValueError("P7-HOLD-004 received snapshot adoption decision active baseline id mismatch")
    if data.get("active_source_snapshot_ref_at_receipt") != P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT:
        raise ValueError("P7-HOLD-004 received snapshot adoption decision active source snapshot ref mismatch")
    if data.get("candidate_new_baseline_id") != P7_HOLD004_RECEIVED_SNAPSHOT_CANDIDATE_NEW_BASELINE_ID:
        raise ValueError("P7-HOLD-004 received snapshot adoption decision candidate baseline id mismatch")
    if data.get("adoption_status") != P7_HOLD004_RECEIVED_ADOPTION_STATUS_BLOCKED_UNCLASSIFIED_ITEM_FINGERPRINT_MISMATCH:
        raise ValueError("P7-HOLD-004 received snapshot adoption decision must remain blocked by unclassified item mismatch")
    if data.get("received_reconcile_status") != P7_HOLD004_RECEIVED_RECONCILE_STATUS_ITEM_FINGERPRINT_MISMATCH_UNCLASSIFIED:
        raise ValueError("P7-HOLD-004 received snapshot adoption decision reconcile status mismatch")
    if data.get("root_cause_status") != P7_HOLD004_RECEIVED_ROOT_CAUSE_STATUS_UNCLASSIFIED:
        raise ValueError("P7-HOLD-004 received snapshot adoption decision root cause must remain UNCLASSIFIED")

    source_identity = safe_mapping(data.get("source_identity"))
    expected_source_identity = {
        "received_zip_ref": P7_HOLD004_RECEIVED_ZIP_REF,
        "active_source_snapshot_ref_at_receipt": P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT,
        "source_snapshot_ref_matches_received_zip_ref": False,
        "source_snapshot_ref_current_for_received_zip": False,
        "received_zip_promoted_to_source_snapshot_ref": False,
        "source_snapshot_ref_update_allowed": False,
    }
    if set(source_identity) != set(expected_source_identity):
        raise ValueError("P7-HOLD-004 received snapshot adoption source_identity keys mismatch")
    for key, expected in expected_source_identity.items():
        actual = source_identity.get(key)
        if isinstance(expected, bool):
            if actual is not expected:
                raise ValueError(f"P7-HOLD-004 received snapshot adoption source_identity.{key} mismatch")
        elif actual != expected:
            raise ValueError(f"P7-HOLD-004 received snapshot adoption source_identity.{key} mismatch")

    required_evidence = safe_mapping(data.get("required_evidence"))
    expected_required_evidence_keys = {
        "repeat_collect_stability_required",
        "source_snapshot_identity_review_required",
        "test_semantics_review_required",
        "baseline_id_or_revision_update_required",
        "item_fingerprint_root_cause_classification_required",
    }
    if set(required_evidence) != expected_required_evidence_keys:
        raise ValueError("P7-HOLD-004 received snapshot adoption required_evidence keys mismatch")
    for key in expected_required_evidence_keys:
        if required_evidence.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 received snapshot adoption required_evidence.{key} must be true")

    for key in (
        "active_baseline_update_allowed",
        "source_snapshot_ref_update_allowed",
        "same_baseline_id_hash_replacement_allowed",
        "received_zip_promoted_to_source_snapshot_ref",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 received snapshot adoption decision must keep {key}=false")
    if data.get("official_group_02_capture_blocked_until_adopted") is not True:
        raise ValueError("P7-HOLD-004 received snapshot adoption decision must block official group_02 capture")

    _assert_release_capture_closed_and_body_free(data, source=source)
    return True


__all__ = [
    "P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT",
    "P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT",
    "P7_HOLD004_ACTIVE_TEST_FILES_FINGERPRINT_SHA256_AT_RECEIPT",
    "P7_HOLD004_ACTIVE_TEST_ITEMS_FINGERPRINT_SHA256_AT_RECEIPT",
    "P7_HOLD004_RECEIVED_ADOPTION_STATUS_BLOCKED_UNCLASSIFIED_ITEM_FINGERPRINT_MISMATCH",
    "P7_HOLD004_RECEIVED_COLLECT_COMMAND_ID",
    "P7_HOLD004_RECEIVED_COLLECT_WARNINGS_COUNT",
    "P7_HOLD004_RECEIVED_COLLECTED_TEST_FILE_COUNT",
    "P7_HOLD004_RECEIVED_COLLECTED_TEST_ITEM_COUNT",
    "P7_HOLD004_RECEIVED_RECONCILE_STATUS_ITEM_FINGERPRINT_MISMATCH_UNCLASSIFIED",
    "P7_HOLD004_RECEIVED_ROOT_CAUSE_STATUS_UNCLASSIFIED",
    "P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_ADOPTION_DECISION_ID",
    "P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_ADOPTION_DECISION_SCHEMA_VERSION",
    "P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_ID",
    "P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_SCHEMA_VERSION",
    "P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_STEP",
    "P7_HOLD004_RECEIVED_SNAPSHOT_CANDIDATE_NEW_BASELINE_ID",
    "P7_HOLD004_RECEIVED_SNAPSHOT_COLLECT_SUMMARY_ID",
    "P7_HOLD004_RECEIVED_SNAPSHOT_COLLECT_SUMMARY_SCHEMA_VERSION",
    "P7_HOLD004_RECEIVED_SNAPSHOT_SCOPE_FREEZE_ID",
    "P7_HOLD004_RECEIVED_SNAPSHOT_SCOPE_FREEZE_SCHEMA_VERSION",
    "P7_HOLD004_RECEIVED_TEST_FILES_FINGERPRINT_SHA256",
    "P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256",
    "P7_HOLD004_RECEIVED_ZIP_REF",
    "assert_p7_hold004_received_snapshot_baseline_adoption_decision_contract",
    "assert_p7_hold004_received_snapshot_baseline_fingerprint_reconcile_contract",
    "assert_p7_hold004_received_snapshot_collect_summary_contract",
    "assert_p7_hold004_received_snapshot_scope_freeze_contract",
    "build_p7_hold004_received_snapshot_baseline_adoption_decision",
    "build_p7_hold004_received_snapshot_baseline_fingerprint_reconcile",
    "build_p7_hold004_received_snapshot_collect_summary",
    "build_p7_hold004_received_snapshot_scope_freeze",
]
