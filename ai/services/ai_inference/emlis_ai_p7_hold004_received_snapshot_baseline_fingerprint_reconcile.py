# -*- coding: utf-8 -*-
"""P7-HOLD-004 received snapshot baseline fingerprint reconcile materials.

R21/R26 scope only:
- keep the active source snapshot reference and the newly received zip reference
  as separate identifiers;
- record the received ``pytest --collect-only`` summary as body-free material;
- compare the active baseline and received collect fingerprints without root
  cause overclaim;
- separate source identity and adoption decision so the received zip is not
  promoted to the active source_snapshot_ref while the item fingerprint mismatch
  remains unclassified;
- freeze the evidence required before any R27 boolean can be called
  adoption-ready;
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
P7_HOLD004_RECEIVED_SNAPSHOT_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.received_snapshot_conditional_active_baseline_adoption.v1"
)
P7_HOLD004_RECEIVED_SNAPSHOT_ADOPTION_EVIDENCE_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.received_snapshot_adoption_evidence_freeze.v1"
)
P7_HOLD004_RECEIVED_SNAPSHOT_R29_VERIFICATION_PROCEDURE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.received_snapshot_r29_verification_procedure.v1"
)
P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_STEP: Final = (
    "P7-HOLD-004_ReceivedSnapshotBaselineFingerprintReconcile_R21_R26_20260615"
)
P7_HOLD004_RECEIVED_SNAPSHOT_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_STEP: Final = (
    "P7-HOLD-004_ReceivedSnapshotBaselineFingerprintReconcile_R27_20260615"
)
P7_HOLD004_RECEIVED_SNAPSHOT_ADOPTION_EVIDENCE_FREEZE_STEP: Final = (
    "P7-HOLD-004_ReceivedSnapshotAdoptionEvidenceFreeze_PreR29_20260616"
)
P7_HOLD004_RECEIVED_SNAPSHOT_R29_VERIFICATION_PROCEDURE_STEP: Final = (
    "P7-HOLD-004_ReceivedSnapshotBaselineFingerprintReconcile_R29_20260616"
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
P7_HOLD004_RECEIVED_SNAPSHOT_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_ID: Final = (
    "p7_hold004_received_snapshot_conditional_active_baseline_adoption_20260615"
)
P7_HOLD004_RECEIVED_SNAPSHOT_ADOPTION_EVIDENCE_FREEZE_ID: Final = (
    "p7_hold004_received_snapshot_adoption_evidence_freeze_pre_r29_20260616"
)
P7_HOLD004_RECEIVED_SNAPSHOT_R29_VERIFICATION_PROCEDURE_ID: Final = (
    "p7_hold004_received_snapshot_r29_verification_procedure_20260616"
)
P7_HOLD004_RECEIVED_SNAPSHOT_CANDIDATE_NEW_BASELINE_ID: Final = (
    "p7_hold004_backend_collect_baseline_20260615_received_148"
)
P7_HOLD004_RECEIVED_COLLECT_COMMAND_ID: Final = "pytest_collect_only_backend_received_20260615"
P7_HOLD004_RECEIVED_ZIP_REF: Final = "mashos-api(148).zip"
P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT: Final = "p7_hold004_backend_collect_baseline_20260615"
P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT: Final = "mashos-api(147).zip"
P7_HOLD004_ACTIVE_TEST_ITEMS_FINGERPRINT_SHA256_AT_RECEIPT: Final = (
    "fee1eca805564d0840dc5b23f60a7e2d6c7297d658a76dc4ce175e0137c261f1"
)
P7_HOLD004_ACTIVE_TEST_FILES_FINGERPRINT_SHA256_AT_RECEIPT: Final = (
    "6866231daf68427dca2de1b2011feea49450f7b4a8b3c5b9dec0f9ccd5f3e9c6"
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
P7_HOLD004_RECEIVED_CONDITIONAL_ADOPTION_STATUS_BLOCKED_CONDITIONS_UNMET: Final = (
    "BLOCKED_CONDITIONS_UNMET"
)
P7_HOLD004_RECEIVED_ADOPTION_STATUS_BLOCKED_ADOPTION_EVIDENCE_NOT_FROZEN: Final = (
    "BLOCKED_ADOPTION_EVIDENCE_NOT_FROZEN"
)
P7_HOLD004_RECEIVED_ADOPTION_EVIDENCE_STATUS_BLOCKED_UNVERIFIED: Final = (
    "BLOCKED_ADOPTION_EVIDENCE_UNVERIFIED"
)
P7_HOLD004_RECEIVED_ADOPTION_EVIDENCE_STATUS_SATISFIED_FOR_R27_CONDITIONAL_ADOPTION: Final = (
    "SATISFIED_FOR_R27_CONDITIONAL_ADOPTION"
)
P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_NOT_REVIEWED: Final = "NOT_REVIEWED"
P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_NO_SEMANTIC_CHANGE_DETECTED: Final = (
    "NO_TEST_SEMANTIC_CHANGE_DETECTED"
)
P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_ACCEPTED_AS_BASELINE_REFRESH: Final = (
    "TEST_SEMANTIC_CHANGE_ACCEPTED_AS_BASELINE_REFRESH"
)
P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOMES: Final[frozenset[str]] = frozenset(
    {
        P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_NOT_REVIEWED,
        P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_NO_SEMANTIC_CHANGE_DETECTED,
        P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_ACCEPTED_AS_BASELINE_REFRESH,
    }
)
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
        P7_HOLD004_RECEIVED_CONDITIONAL_ADOPTION_STATUS_BLOCKED_CONDITIONS_UNMET,
        P7_HOLD004_RECEIVED_ADOPTION_STATUS_BLOCKED_ADOPTION_EVIDENCE_NOT_FROZEN,
    }
)

P7_HOLD004_RECEIVED_ADOPTABLE_ROOT_CAUSE_STATUSES: Final[frozenset[str]] = frozenset(
    status
    for status in P7_HOLD004_RECEIVED_ROOT_CAUSE_STATUSES
    if status != P7_HOLD004_RECEIVED_ROOT_CAUSE_STATUS_UNCLASSIFIED
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
    "r25_official_group02_readiness_guard_added": True,
    "r26_matrix_handoff_validation_connected": True,
    "r27_conditional_active_baseline_adoption_added": True,
    "r28_group02_timeout_long_run_policy_added": True,
    "pre_r29_received_snapshot_adoption_evidence_freeze_added": True,
    "r29_verification_procedure_fixed": True,
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
_R29_VERIFICATION_CHECKPOINT_IDS: Final[tuple[str, ...]] = (
    "py_compile_material_contract_modules",
    "p7_hold004_received_snapshot_focused_contract_subset",
    "full_backend_collect_only_fingerprint_check",
    "group_02_collect_only_boundary_check",
    "group_02_full_run_conditional_capture_check",
)
_R29_REQUIRED_GREEN_CLAIM_BOUNDARIES: Final[tuple[str, ...]] = (
    "target_contract_subset_green_is_full_backend_suite_green",
    "full_collect_only_is_execution_green",
    "group02_collect_only_is_group_green",
    "group02_timeout_is_green",
    "group02_timeout_is_immediate_fail",
    "group02_pass_is_full_backend_suite_green",
    "r27_adoptable_status_alone_updates_active_baseline",
    "r29_verification_procedure_closes_hold004",
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


def _coerce_bool(value: Any) -> bool:
    return value if isinstance(value, bool) else False


def _is_sha256_hex(value: Any) -> bool:
    text = str(value or "").strip()
    return len(text) == _SHA256_HEX_LENGTH and all(ch in "0123456789abcdef" for ch in text)


def _normalize_status_identifier(value: Any) -> str:
    return clean_identifier(value, default=P7_HOLD004_RECEIVED_COLLECT_STATUS_COLLECTION_FAILED, max_length=80).upper()


def _active_baseline_at_receipt_material() -> dict[str, Any]:
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


def _candidate_active_baseline_material() -> dict[str, Any]:
    return {
        "baseline_id": P7_HOLD004_RECEIVED_SNAPSHOT_CANDIDATE_NEW_BASELINE_ID,
        "source_snapshot_ref": P7_HOLD004_RECEIVED_ZIP_REF,
        "collected_test_file_count": P7_HOLD004_RECEIVED_COLLECTED_TEST_FILE_COUNT,
        "collected_test_item_count": P7_HOLD004_RECEIVED_COLLECTED_TEST_ITEM_COUNT,
        "warnings_count": P7_HOLD004_RECEIVED_COLLECT_WARNINGS_COUNT,
        "test_items_fingerprint_sha256": P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256,
        "test_files_fingerprint_sha256": P7_HOLD004_RECEIVED_TEST_FILES_FINGERPRINT_SHA256,
        "fingerprint_algorithm": P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM,
        "same_baseline_id_hash_replacement_allowed": False,
        "previous_active_baseline_retained": True,
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


def _normalize_root_cause_status(value: Any) -> str:
    status = clean_identifier(
        value,
        default=P7_HOLD004_RECEIVED_ROOT_CAUSE_STATUS_UNCLASSIFIED,
        max_length=120,
    ).upper()
    if status not in P7_HOLD004_RECEIVED_ROOT_CAUSE_STATUSES:
        return P7_HOLD004_RECEIVED_ROOT_CAUSE_STATUS_UNCLASSIFIED
    return status


def _normalize_test_semantics_review_outcome(value: Any) -> str:
    outcome = clean_identifier(
        value,
        default=P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_NOT_REVIEWED,
        max_length=120,
    ).upper()
    if outcome not in P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOMES:
        return P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_NOT_REVIEWED
    return outcome


def build_p7_hold004_received_snapshot_adoption_evidence_freeze(
    *,
    received_snapshot_reconcile: Mapping[str, Any] | None = None,
    repeat_collect_run_count: Any = 0,
    repeat_collect_counts_warnings_fingerprints_match: Any = False,
    root_cause_status: Any = None,
    root_cause_review_recorded: Any = False,
    source_identity_decision_recorded: Any = False,
    source_identity_accepted: Any = False,
    test_semantics_reviewed: Any = False,
    test_semantics_review_outcome: Any = None,
    baseline_id_or_revision_update_planned: Any = True,
    runtime_builder_update_plan_recorded: Any = False,
    matrix_handoff_update_plan_recorded: Any = False,
) -> dict[str, Any]:
    """Freeze the evidence required before R27 can be called adoption-ready.

    This pre-R29 material prevents a caller from satisfying the R27 booleans by
    assertion alone.  The material stores only counts, hashes, identifiers,
    booleans, and enum-like statuses; it does not retain nodeids, pytest output,
    traceback, or any Emlis/RN visible body.
    """

    reconcile = safe_mapping(received_snapshot_reconcile) or build_p7_hold004_received_snapshot_baseline_fingerprint_reconcile()
    assert_p7_hold004_received_snapshot_baseline_fingerprint_reconcile_contract(reconcile)
    active = safe_mapping(reconcile.get("active_baseline")) or _active_baseline_for_reconcile()
    received = safe_mapping(reconcile.get("received_snapshot")) or _received_snapshot_for_reconcile()
    comparison = safe_mapping(reconcile.get("comparison"))
    classification = safe_mapping(reconcile.get("classification"))
    candidate = _candidate_active_baseline_material()

    repeat_run_count = _coerce_non_negative_int(repeat_collect_run_count)
    repeat_fingerprint_match = _coerce_bool(repeat_collect_counts_warnings_fingerprints_match)
    normalized_root_cause = _normalize_root_cause_status(
        root_cause_status if root_cause_status is not None else classification.get("root_cause_status")
    )
    root_review_recorded = _coerce_bool(root_cause_review_recorded)
    source_decision_recorded = _coerce_bool(source_identity_decision_recorded)
    source_accepted = _coerce_bool(source_identity_accepted)
    semantics_reviewed = _coerce_bool(test_semantics_reviewed)
    semantics_outcome = _normalize_test_semantics_review_outcome(test_semantics_review_outcome)
    baseline_update_planned = _coerce_bool(baseline_id_or_revision_update_planned)
    runtime_plan_recorded = _coerce_bool(runtime_builder_update_plan_recorded)
    matrix_plan_recorded = _coerce_bool(matrix_handoff_update_plan_recorded)

    received_collect_is_expected = _received_snapshot_default_collect_match(received)
    repeat_collect_satisfied = bool(
        repeat_run_count >= 2 and repeat_fingerprint_match and received_collect_is_expected
    )
    root_cause_satisfied = bool(
        root_review_recorded and normalized_root_cause in P7_HOLD004_RECEIVED_ADOPTABLE_ROOT_CAUSE_STATUSES
    )
    source_identity_satisfied = bool(
        source_decision_recorded
        and source_accepted
        and received.get("received_zip_ref") == P7_HOLD004_RECEIVED_ZIP_REF
        and active.get("source_snapshot_ref") == P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT
        and candidate.get("source_snapshot_ref") == P7_HOLD004_RECEIVED_ZIP_REF
    )
    semantics_satisfied = bool(
        semantics_reviewed
        and semantics_outcome
        in {
            P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_NO_SEMANTIC_CHANGE_DETECTED,
            P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_ACCEPTED_AS_BASELINE_REFRESH,
        }
    )
    baseline_traceability_satisfied = bool(
        baseline_update_planned
        and candidate.get("baseline_id") != active.get("baseline_id")
        and candidate.get("same_baseline_id_hash_replacement_allowed") is False
        and candidate.get("previous_active_baseline_retained") is True
    )
    post_adoption_plan_satisfied = bool(runtime_plan_recorded and matrix_plan_recorded)

    r27_condition_inputs = {
        "root_cause_status": normalized_root_cause,
        "repeated_collect_stable": repeat_collect_satisfied,
        "source_identity_decision_recorded": source_decision_recorded,
        "source_identity_accepted": source_accepted,
        "test_semantics_reviewed": semantics_satisfied,
        "baseline_id_or_revision_update_planned": baseline_update_planned,
    }
    condition_projection = {
        "received_zip_ref_is_expected": received.get("received_zip_ref") == P7_HOLD004_RECEIVED_ZIP_REF,
        "received_collect_counts_match_expected": received_collect_is_expected,
        "counts_and_warnings_match_active_or_refresh_scope": bool(
            comparison.get("counts_match") is True and comparison.get("warning_count_match") is True
        ),
        "test_files_fingerprint_matches_active": bool(comparison.get("test_files_fingerprint_match") is True),
        "item_fingerprint_diff_recorded_as_refresh_candidate": bool(
            comparison.get("test_items_fingerprint_match") is not True
            and received.get("test_items_fingerprint_sha256") == P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256
        ),
        "root_cause_classified": root_cause_satisfied,
        "repeated_collect_stable": repeat_collect_satisfied,
        "source_identity_decision_recorded": source_decision_recorded,
        "source_identity_accepted": source_accepted,
        "test_semantics_reviewed": semantics_satisfied,
        "baseline_id_or_revision_update_planned": baseline_update_planned,
        "candidate_baseline_id_changes": candidate["baseline_id"] != active.get("baseline_id"),
        "same_baseline_id_hash_replacement_blocked": candidate["same_baseline_id_hash_replacement_allowed"] is False,
        "previous_active_baseline_retained": candidate["previous_active_baseline_retained"] is True,
        "public_contract_unchanged": True,
        "runtime_contract_unchanged": True,
    }
    can_mark_r27_conditions_satisfied = bool(
        repeat_collect_satisfied
        and root_cause_satisfied
        and source_identity_satisfied
        and semantics_satisfied
        and baseline_traceability_satisfied
        and post_adoption_plan_satisfied
        and all(condition_projection.values())
    )
    condition_projection["adoption_evidence_freeze_satisfied"] = can_mark_r27_conditions_satisfied
    adoption_status_if_applied = _conditional_active_baseline_adoption_status(condition_projection)

    material = {
        "schema_version": P7_HOLD004_RECEIVED_SNAPSHOT_ADOPTION_EVIDENCE_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_RECEIVED_SNAPSHOT_ADOPTION_EVIDENCE_FREEZE_STEP,
        "implementation_step": P7_HOLD004_RECEIVED_SNAPSHOT_ADOPTION_EVIDENCE_FREEZE_STEP,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "evidence_freeze_id": P7_HOLD004_RECEIVED_SNAPSHOT_ADOPTION_EVIDENCE_FREEZE_ID,
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
        "candidate_new_baseline_id": candidate["baseline_id"],
        "evidence_status": (
            P7_HOLD004_RECEIVED_ADOPTION_EVIDENCE_STATUS_SATISFIED_FOR_R27_CONDITIONAL_ADOPTION
            if can_mark_r27_conditions_satisfied
            else P7_HOLD004_RECEIVED_ADOPTION_EVIDENCE_STATUS_BLOCKED_UNVERIFIED
        ),
        "repeat_collect_evidence": {
            "required": True,
            "minimum_collect_run_count": 2,
            "provided_collect_run_count": repeat_run_count,
            "counts_warnings_fingerprints_stable": repeat_fingerprint_match,
            "received_collect_matches_recorded_default": received_collect_is_expected,
            "nodeids_retained": False,
            "pytest_output_retained": False,
            "satisfied": repeat_collect_satisfied,
        },
        "root_cause_evidence": {
            "required": True,
            "root_cause_status": normalized_root_cause,
            "root_cause_review_recorded": root_review_recorded,
            "root_cause_unclassified": normalized_root_cause == P7_HOLD004_RECEIVED_ROOT_CAUSE_STATUS_UNCLASSIFIED,
            "satisfied": root_cause_satisfied,
        },
        "source_identity_evidence": {
            "required": True,
            "source_identity_decision_recorded": source_decision_recorded,
            "source_identity_accepted": source_accepted,
            "received_zip_ref": P7_HOLD004_RECEIVED_ZIP_REF,
            "active_source_snapshot_ref_at_receipt": P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT,
            "candidate_source_snapshot_ref": candidate["source_snapshot_ref"],
            "received_zip_promoted_to_source_snapshot_ref": False,
            "satisfied": source_identity_satisfied,
        },
        "test_semantics_evidence": {
            "required": True,
            "test_semantics_reviewed": semantics_reviewed,
            "test_semantics_review_outcome": semantics_outcome,
            "nodeids_retained": False,
            "pytest_output_retained": False,
            "raw_traceback_included": False,
            "satisfied": semantics_satisfied,
        },
        "baseline_traceability_evidence": {
            "required": True,
            "baseline_id_or_revision_update_planned": baseline_update_planned,
            "candidate_baseline_id_changes": candidate["baseline_id"] != active.get("baseline_id"),
            "same_baseline_id_hash_replacement_blocked": candidate["same_baseline_id_hash_replacement_allowed"] is False,
            "previous_active_baseline_retained": candidate["previous_active_baseline_retained"] is True,
            "satisfied": baseline_traceability_satisfied,
        },
        "post_adoption_connection_plan_evidence": {
            "required_before_r29": True,
            "runtime_builder_update_plan_recorded": runtime_plan_recorded,
            "matrix_handoff_update_plan_recorded": matrix_plan_recorded,
            "active_baseline_update_applied_to_runtime_builders": False,
            "source_snapshot_ref_updated_in_active_builders": False,
            "satisfied": post_adoption_plan_satisfied,
        },
        "r27_condition_inputs": r27_condition_inputs,
        "r27_condition_projection": condition_projection,
        "r27_manual_boolean_only_adoption_ready_allowed": False,
        "can_mark_r27_conditions_satisfied": can_mark_r27_conditions_satisfied,
        "adoption_status_if_applied_to_r27": adoption_status_if_applied,
        "active_baseline_update_allowed": False,
        "official_group_02_capture_run_allowed": False,
        "official_group_02_capture_result_recording_allowed": False,
        "can_claim_group_green": False,
        "can_claim_full_backend_suite_green": False,
        **_release_closed_boundary(),
        "unresolved_hold_refs": [P7_HOLD004_BACKEND_SUITE_HOLD_ID],
        "required_followup_fixes": dedupe_identifiers(
            [
                "received_snapshot_adoption_evidence_freeze_required"
                if not can_mark_r27_conditions_satisfied
                else "received_snapshot_adoption_evidence_frozen_for_r27_conditions",
                "received_snapshot_repeat_collect_stability_required"
                if not repeat_collect_satisfied
                else "",
                "received_snapshot_item_fingerprint_root_cause_classification_required"
                if not root_cause_satisfied
                else "",
                "received_snapshot_source_identity_decision_required"
                if not source_identity_satisfied
                else "",
                "received_snapshot_test_semantics_review_required"
                if not semantics_satisfied
                else "",
                "received_snapshot_post_adoption_runtime_matrix_plan_required"
                if not post_adoption_plan_satisfied
                else "",
                "active_baseline_refresh_not_applied_to_runtime_builders",
                "official_group_02_capture_blocked_until_received_snapshot_adoption",
                "full_backend_suite_green_unconfirmed",
            ],
            limit=80,
            max_length=200,
        ),
        "public_contract": _public_contract_boundary_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_hold004_received_snapshot_adoption_evidence_freeze_contract(material)
    return material


def _conditional_active_baseline_adoption_status(conditions: Mapping[str, bool]) -> str:
    if not conditions.get("counts_and_warnings_match_active_or_refresh_scope", False):
        return P7_HOLD004_RECEIVED_ADOPTION_STATUS_REJECTED_COUNT_MISMATCH
    if not conditions.get("test_files_fingerprint_matches_active", False):
        return P7_HOLD004_RECEIVED_ADOPTION_STATUS_REJECTED_FILE_FINGERPRINT_MISMATCH
    if not conditions.get("root_cause_classified", False):
        return P7_HOLD004_RECEIVED_ADOPTION_STATUS_BLOCKED_UNCLASSIFIED_ITEM_FINGERPRINT_MISMATCH
    if not conditions.get("repeated_collect_stable", False):
        return P7_HOLD004_RECEIVED_ADOPTION_STATUS_BLOCKED_UNSTABLE_REPEAT_COLLECT
    if not conditions.get("source_identity_decision_recorded", False) or not conditions.get(
        "source_identity_accepted",
        False,
    ):
        return P7_HOLD004_RECEIVED_ADOPTION_STATUS_BLOCKED_SOURCE_SNAPSHOT_IDENTITY_UNCLEAR
    if not conditions.get("test_semantics_reviewed", False):
        return P7_HOLD004_RECEIVED_ADOPTION_STATUS_REQUIRES_TEST_SEMANTICS_REVIEW
    if not conditions.get("adoption_evidence_freeze_satisfied", False):
        return P7_HOLD004_RECEIVED_ADOPTION_STATUS_BLOCKED_ADOPTION_EVIDENCE_NOT_FROZEN
    if not conditions.get("baseline_id_or_revision_update_planned", False):
        return P7_HOLD004_RECEIVED_CONDITIONAL_ADOPTION_STATUS_BLOCKED_CONDITIONS_UNMET
    if not conditions.get("candidate_baseline_id_changes", False) or not conditions.get(
        "same_baseline_id_hash_replacement_blocked",
        False,
    ):
        return P7_HOLD004_RECEIVED_CONDITIONAL_ADOPTION_STATUS_BLOCKED_CONDITIONS_UNMET
    return P7_HOLD004_RECEIVED_ADOPTION_STATUS_ADOPTABLE_AS_RECEIVED_SNAPSHOT_BASELINE_REFRESH


def build_p7_hold004_received_snapshot_conditional_active_baseline_adoption(
    *,
    received_snapshot_reconcile: Mapping[str, Any] | None = None,
    adoption_decision: Mapping[str, Any] | None = None,
    adoption_evidence_freeze: Mapping[str, Any] | None = None,
    repeated_collect_stable: Any = False,
    root_cause_status: Any = None,
    source_identity_decision_recorded: Any = False,
    source_identity_accepted: Any = False,
    test_semantics_reviewed: Any = False,
    baseline_id_or_revision_update_planned: Any = True,
) -> dict[str, Any]:
    """Build the R27 conditional active-baseline adoption material.

    R27 records the exact conditions under which the received snapshot may
    become the next active baseline.  The default material intentionally remains
    blocked because the received item fingerprint mismatch is still
    unclassified and no repeat-collect/source-identity evidence has been
    supplied.
    """

    reconcile = safe_mapping(received_snapshot_reconcile) or build_p7_hold004_received_snapshot_baseline_fingerprint_reconcile()
    assert_p7_hold004_received_snapshot_baseline_fingerprint_reconcile_contract(reconcile)
    adoption = (
        safe_mapping(adoption_decision)
        if adoption_decision is not None
        else build_p7_hold004_received_snapshot_baseline_adoption_decision(
            received_snapshot_reconcile=reconcile,
        )
    )
    assert_p7_hold004_received_snapshot_baseline_adoption_decision_contract(adoption)

    active = safe_mapping(reconcile.get("active_baseline")) or _active_baseline_for_reconcile()
    received = safe_mapping(reconcile.get("received_snapshot")) or _received_snapshot_for_reconcile()
    comparison = safe_mapping(reconcile.get("comparison"))
    classification = safe_mapping(reconcile.get("classification"))
    normalized_root_cause = _normalize_root_cause_status(
        root_cause_status if root_cause_status is not None else classification.get("root_cause_status")
    )
    evidence = safe_mapping(adoption_evidence_freeze)
    if evidence:
        assert_p7_hold004_received_snapshot_adoption_evidence_freeze_contract(evidence)
        evidence_inputs = safe_mapping(evidence.get("r27_condition_inputs"))
        normalized_root_cause = _normalize_root_cause_status(evidence_inputs.get("root_cause_status"))
        repeated_collect_stable = evidence_inputs.get("repeated_collect_stable", repeated_collect_stable)
        source_identity_decision_recorded = evidence_inputs.get(
            "source_identity_decision_recorded",
            source_identity_decision_recorded,
        )
        source_identity_accepted = evidence_inputs.get("source_identity_accepted", source_identity_accepted)
        test_semantics_reviewed = evidence_inputs.get("test_semantics_reviewed", test_semantics_reviewed)
        baseline_id_or_revision_update_planned = evidence_inputs.get(
            "baseline_id_or_revision_update_planned",
            baseline_id_or_revision_update_planned,
        )
    evidence_freeze_satisfied = bool(evidence.get("can_mark_r27_conditions_satisfied") is True) if evidence else False

    candidate = _candidate_active_baseline_material()
    conditions = {
        "received_zip_ref_is_expected": received.get("received_zip_ref") == P7_HOLD004_RECEIVED_ZIP_REF,
        "received_collect_counts_match_expected": (
            received.get("collected_test_file_count") == P7_HOLD004_RECEIVED_COLLECTED_TEST_FILE_COUNT
            and received.get("collected_test_item_count") == P7_HOLD004_RECEIVED_COLLECTED_TEST_ITEM_COUNT
            and received.get("warnings_count") == P7_HOLD004_RECEIVED_COLLECT_WARNINGS_COUNT
        ),
        "counts_and_warnings_match_active_or_refresh_scope": bool(
            comparison.get("counts_match") is True and comparison.get("warning_count_match") is True
        ),
        "test_files_fingerprint_matches_active": bool(comparison.get("test_files_fingerprint_match") is True),
        "item_fingerprint_diff_recorded_as_refresh_candidate": bool(
            comparison.get("test_items_fingerprint_match") is not True
            and received.get("test_items_fingerprint_sha256") == P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256
        ),
        "root_cause_classified": normalized_root_cause in P7_HOLD004_RECEIVED_ADOPTABLE_ROOT_CAUSE_STATUSES,
        "repeated_collect_stable": _coerce_bool(repeated_collect_stable),
        "source_identity_decision_recorded": _coerce_bool(source_identity_decision_recorded),
        "source_identity_accepted": _coerce_bool(source_identity_accepted),
        "test_semantics_reviewed": _coerce_bool(test_semantics_reviewed),
        "baseline_id_or_revision_update_planned": _coerce_bool(baseline_id_or_revision_update_planned),
        "candidate_baseline_id_changes": candidate["baseline_id"] != active.get("baseline_id"),
        "same_baseline_id_hash_replacement_blocked": candidate["same_baseline_id_hash_replacement_allowed"] is False,
        "previous_active_baseline_retained": candidate["previous_active_baseline_retained"] is True,
        "public_contract_unchanged": True,
        "runtime_contract_unchanged": True,
        "adoption_evidence_freeze_satisfied": evidence_freeze_satisfied,
    }
    adoption_status = _conditional_active_baseline_adoption_status(conditions)
    adoption_ready = adoption_status == P7_HOLD004_RECEIVED_ADOPTION_STATUS_ADOPTABLE_AS_RECEIVED_SNAPSHOT_BASELINE_REFRESH

    material = {
        "schema_version": P7_HOLD004_RECEIVED_SNAPSHOT_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_RECEIVED_SNAPSHOT_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_STEP,
        "implementation_step": P7_HOLD004_RECEIVED_SNAPSHOT_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_STEP,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "adoption_id": P7_HOLD004_RECEIVED_SNAPSHOT_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_ID,
        "received_reconcile_id": clean_identifier(
            reconcile.get("reconcile_id"),
            default=P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_ID,
        ),
        "received_adoption_decision_id": clean_identifier(
            adoption.get("decision_id"),
            default=P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_ADOPTION_DECISION_ID,
        ),
        "source_mode": P7_SOURCE_MODE,
        "git_checked": P7_GIT_CHECKED,
        "received_zip_ref": clean_identifier(received.get("received_zip_ref"), default=P7_HOLD004_RECEIVED_ZIP_REF),
        "previous_active_baseline": active,
        "candidate_active_baseline": candidate,
        "root_cause_status": normalized_root_cause,
        "prior_r24_adoption_status": clean_identifier(
            adoption.get("adoption_status"),
            default=P7_HOLD004_RECEIVED_ADOPTION_STATUS_BLOCKED_UNCLASSIFIED_ITEM_FINGERPRINT_MISMATCH,
        ),
        "adoption_status": adoption_status,
        "adoption_conditions": conditions,
        "adoption_evidence_freeze_id": clean_identifier(
            evidence.get("evidence_freeze_id"),
            default="",
        ),
        "adoption_evidence_freeze_satisfied": evidence_freeze_satisfied,
        "r27_manual_boolean_only_adoption_ready_allowed": False,
        "active_baseline_adoption_ready": adoption_ready,
        "active_baseline_update_allowed": adoption_ready,
        "active_baseline_update_applied_to_runtime_builders": False,
        "source_snapshot_ref_update_allowed": adoption_ready,
        "source_snapshot_ref_updated_in_active_builders": False,
        "same_baseline_id_hash_replacement_allowed": False,
        "received_zip_promoted_to_source_snapshot_ref": False,
        "official_group_02_capture_blocked_until_adopted": True,
        "official_group_02_capture_run_allowed": False,
        "official_group_02_capture_result_recording_allowed": False,
        "can_claim_group_green": False,
        "can_claim_full_backend_suite_green": False,
        "full_backend_suite_green_confirmed": False,
        "hold004_close_allowed": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "unresolved_hold_refs": [P7_HOLD004_BACKEND_SUITE_HOLD_ID],
        "required_followup_fixes": dedupe_identifiers(
            [
                "received_snapshot_item_fingerprint_root_cause_classification_required"
                if not conditions["root_cause_classified"]
                else "",
                "received_snapshot_repeat_collect_stability_required"
                if not conditions["repeated_collect_stable"]
                else "",
                "received_snapshot_source_identity_decision_required"
                if not conditions["source_identity_decision_recorded"] or not conditions["source_identity_accepted"]
                else "",
                "received_snapshot_test_semantics_review_required"
                if not conditions["test_semantics_reviewed"]
                else "",
                "received_snapshot_adoption_evidence_freeze_required"
                if not conditions["adoption_evidence_freeze_satisfied"]
                else "",
                "active_baseline_refresh_not_applied_to_runtime_builders",
                "official_group_02_capture_blocked_until_received_snapshot_adoption",
                "full_backend_suite_green_unconfirmed",
            ],
            limit=80,
            max_length=200,
        ),
        "public_contract": _public_contract_boundary_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_hold004_received_snapshot_conditional_active_baseline_adoption_contract(material)
    return material




def _r29_body_free_command(
    *,
    checkpoint_id: str,
    command_id: str,
    command_kind: str,
    argv: tuple[str, ...],
    required: bool = True,
    execution_allowed_by_default: bool = True,
    allowed_when_readiness_status: str = "",
) -> dict[str, Any]:
    return {
        "checkpoint_id": checkpoint_id,
        "command_id": command_id,
        "command_kind": command_kind,
        "working_directory": "mashos-api/ai",
        "argv": list(argv),
        "required": bool(required),
        "execution_allowed_by_default": bool(execution_allowed_by_default),
        "allowed_when_readiness_status": allowed_when_readiness_status,
        "nodeids_retained": False,
        "pytest_output_retained": False,
        "terminal_output_retained": False,
        "stdout_retained": False,
        "stderr_retained": False,
        "raw_traceback_included": False,
        "body_free": True,
    }


def _r29_verification_sequence() -> list[dict[str, Any]]:
    return [
        _r29_body_free_command(
            checkpoint_id="py_compile_material_contract_modules",
            command_id="py_compile_p7_hold004_received_snapshot_r21_r29_materials_20260616",
            command_kind="py_compile",
            argv=(
                "python",
                "-m",
                "py_compile",
                "services/ai_inference/emlis_ai_p7_hold004_received_snapshot_baseline_fingerprint_reconcile.py",
                "services/ai_inference/emlis_ai_p7_hold004_backend_suite_execution_results.py",
                "services/ai_inference/emlis_ai_p7_hold004_matrix_consistency_report.py",
                "services/ai_inference/emlis_ai_p7_hold_matrix.py",
                "services/ai_inference/emlis_ai_p7_release_handoff.py",
                "services/ai_inference/emlis_ai_p7_validation_matrix.py",
            ),
        ),
        _r29_body_free_command(
            checkpoint_id="p7_hold004_received_snapshot_focused_contract_subset",
            command_id="pytest_p7_hold004_received_snapshot_r21_r29_focused_contract_subset_20260616",
            command_kind="pytest_focused_contract_subset",
            argv=(
                "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1",
                "PYTHONPATH=services/ai_inference",
                "pytest",
                "-q",
                "--tb=short",
                "-p",
                "pytest_asyncio.plugin",
                "tests/test_emlis_ai_p7_hold004_backend_suite_collect_baseline_20260614.py",
                "tests/test_emlis_ai_p7_hold004_backend_suite_group_result_20260614.py",
                "tests/test_emlis_ai_p7_hold004_backend_suite_matrix_connection_20260615.py",
                "tests/test_emlis_ai_p7_hold004_release_validation_connection_20260615.py",
                "tests/test_emlis_ai_p7_hold004_matrix_consistency_report_20260615.py",
            ),
        ),
        _r29_body_free_command(
            checkpoint_id="full_backend_collect_only_fingerprint_check",
            command_id="pytest_collect_only_backend_received_snapshot_r29_20260616",
            command_kind="pytest_collect_only_full_backend",
            argv=(
                "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1",
                "PYTHONPATH=services/ai_inference",
                "pytest",
                "--collect-only",
                "-q",
                "-p",
                "pytest_asyncio.plugin",
                "tests",
            ),
        ),
        _r29_body_free_command(
            checkpoint_id="group_02_collect_only_boundary_check",
            command_id="pytest_collect_only_group_02_p7_hold004_r29_20260616",
            command_kind="pytest_collect_only_group_02",
            argv=(
                "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1",
                "PYTHONPATH=services/ai_inference",
                "pytest",
                "--collect-only",
                "-q",
                "-p",
                "pytest_asyncio.plugin",
                "tests/test_emlis_ai_p7_hold004_*.py",
            ),
        ),
        _r29_body_free_command(
            checkpoint_id="group_02_full_run_conditional_capture_check",
            command_id="pytest_group_02_p7_hold004_full_run_conditional_r29_20260616",
            command_kind="pytest_group_02_full_run_conditional",
            argv=(
                "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1",
                "PYTHONPATH=services/ai_inference",
                "pytest",
                "-q",
                "--tb=short",
                "-p",
                "pytest_asyncio.plugin",
                "tests/test_emlis_ai_p7_hold004_*.py",
            ),
            required=False,
            execution_allowed_by_default=False,
            allowed_when_readiness_status="READY_FOR_OFFICIAL_CAPTURE_RUN",
        ),
    ]


def _r29_expected_full_collect_summary() -> dict[str, Any]:
    return {
        "collected_test_file_count": P7_HOLD004_RECEIVED_COLLECTED_TEST_FILE_COUNT,
        "collected_test_item_count": P7_HOLD004_RECEIVED_COLLECTED_TEST_ITEM_COUNT,
        "warnings_count": P7_HOLD004_RECEIVED_COLLECT_WARNINGS_COUNT,
        "test_items_fingerprint_sha256": P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256,
        "test_files_fingerprint_sha256": P7_HOLD004_RECEIVED_TEST_FILES_FINGERPRINT_SHA256,
        "active_baseline_item_fingerprint_sha256_at_receipt": (
            P7_HOLD004_ACTIVE_TEST_ITEMS_FINGERPRINT_SHA256_AT_RECEIPT
        ),
        "active_baseline_file_fingerprint_sha256_at_receipt": (
            P7_HOLD004_ACTIVE_TEST_FILES_FINGERPRINT_SHA256_AT_RECEIPT
        ),
        "active_baseline_item_fingerprint_match_expected": False,
        "active_baseline_file_fingerprint_match_expected": True,
        "collect_only_is_not_execution_green": True,
        "nodeids_retained": False,
        "pytest_output_retained": False,
        "body_free": True,
    }


def _r29_expected_group02_collect_summary() -> dict[str, Any]:
    return {
        "group_id": "group_02_p7_hold004",
        "batch_id": "group_02_p7_hold004_batch_01",
        "collected_test_file_count": 19,
        "collected_test_item_count": 252,
        "warnings_count": 1,
        "timeout_budget_sec": 120,
        "long_run_probe_budget_sec": 240,
        "collect_only_is_not_execution_green": True,
        "collect_only_is_not_group_green": True,
        "official_green_confirmed": False,
        "nodeids_retained": False,
        "pytest_output_retained": False,
        "body_free": True,
    }


def _r29_green_claim_boundaries() -> dict[str, bool]:
    boundaries = {key: False for key in _R29_REQUIRED_GREEN_CLAIM_BOUNDARIES}
    boundaries.update(
        {
            "target_contract_subset_green_is_contract_green_only": True,
            "full_backend_suite_green_requires_full_execution_green": True,
            "official_group02_capture_requires_readiness_ready": True,
            "official_group02_timeout_requires_body_free_timeout_material": True,
            "official_group02_fail_requires_first_failure_identifiers_only": True,
            "previous_active_baseline_must_remain_traceable_after_adoption": True,
            "same_baseline_id_hash_replacement_blocked": True,
        }
    )
    return boundaries


def _r29_adoption_readiness_inputs(
    *,
    adoption_evidence_freeze: Mapping[str, Any],
    conditional_active_baseline_adoption: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "adoption_evidence_freeze_id": clean_identifier(
            adoption_evidence_freeze.get("evidence_freeze_id"),
            default=P7_HOLD004_RECEIVED_SNAPSHOT_ADOPTION_EVIDENCE_FREEZE_ID,
        ),
        "adoption_evidence_status": clean_identifier(
            adoption_evidence_freeze.get("evidence_status"),
            default=P7_HOLD004_RECEIVED_ADOPTION_EVIDENCE_STATUS_BLOCKED_UNVERIFIED,
            max_length=160,
        ),
        "adoption_evidence_freeze_satisfied": bool(
            adoption_evidence_freeze.get("can_mark_r27_conditions_satisfied") is True
        ),
        "conditional_adoption_id": clean_identifier(
            conditional_active_baseline_adoption.get("adoption_id"),
            default=P7_HOLD004_RECEIVED_SNAPSHOT_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_ID,
        ),
        "conditional_adoption_status": clean_identifier(
            conditional_active_baseline_adoption.get("adoption_status"),
            default=P7_HOLD004_RECEIVED_ADOPTION_STATUS_BLOCKED_UNCLASSIFIED_ITEM_FINGERPRINT_MISMATCH,
            max_length=160,
        ),
        "conditional_active_baseline_adoption_ready": bool(
            conditional_active_baseline_adoption.get("active_baseline_adoption_ready") is True
        ),
        "conditional_material_update_allowed": bool(
            conditional_active_baseline_adoption.get("active_baseline_update_allowed") is True
        ),
        "active_baseline_update_applied_to_runtime_builders": False,
        "source_snapshot_ref_updated_in_active_builders": False,
        "r29_applies_active_baseline_refresh": False,
        "r29_closes_hold004": False,
        "release_allowed_after_r29": False,
    }


def build_p7_hold004_received_snapshot_r29_verification_procedure(
    *,
    adoption_evidence_freeze: Mapping[str, Any] | None = None,
    conditional_active_baseline_adoption: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the R29 body-free verification procedure material.

    R29 fixes how to read validation results.  It does not execute the commands,
    does not store command output, does not adopt the received snapshot, does not
    record group_02 official green, and does not close P7-HOLD-004.
    """

    evidence = (
        safe_mapping(adoption_evidence_freeze)
        if adoption_evidence_freeze is not None
        else build_p7_hold004_received_snapshot_adoption_evidence_freeze()
    )
    assert_p7_hold004_received_snapshot_adoption_evidence_freeze_contract(evidence)
    conditional = (
        safe_mapping(conditional_active_baseline_adoption)
        if conditional_active_baseline_adoption is not None
        else build_p7_hold004_received_snapshot_conditional_active_baseline_adoption(
            adoption_evidence_freeze=evidence,
        )
    )
    assert_p7_hold004_received_snapshot_conditional_active_baseline_adoption_contract(conditional)

    material = {
        "schema_version": P7_HOLD004_RECEIVED_SNAPSHOT_R29_VERIFICATION_PROCEDURE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_RECEIVED_SNAPSHOT_R29_VERIFICATION_PROCEDURE_STEP,
        "implementation_step": P7_HOLD004_RECEIVED_SNAPSHOT_R29_VERIFICATION_PROCEDURE_STEP,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "verification_id": P7_HOLD004_RECEIVED_SNAPSHOT_R29_VERIFICATION_PROCEDURE_ID,
        "source_mode": P7_SOURCE_MODE,
        "git_checked": P7_GIT_CHECKED,
        "received_zip_ref": P7_HOLD004_RECEIVED_ZIP_REF,
        "active_source_snapshot_ref_at_receipt": P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT,
        "scope_status": "R29_VERIFICATION_PROCEDURE_FIXED_RELEASE_CLOSED",
        "implementation_scope": dict(_IMPLEMENTATION_SCOPE_FLAGS),
        "verification_sequence": _r29_verification_sequence(),
        "expected_full_backend_collect_only": _r29_expected_full_collect_summary(),
        "expected_group02_collect_only": _r29_expected_group02_collect_summary(),
        "green_claim_boundaries": _r29_green_claim_boundaries(),
        "adoption_readiness_inputs": _r29_adoption_readiness_inputs(
            adoption_evidence_freeze=evidence,
            conditional_active_baseline_adoption=conditional,
        ),
        "result_recording_policy": {
            "r29_records_procedure_not_results": True,
            "command_output_retained": False,
            "pytest_output_retained": False,
            "nodeids_retained": False,
            "stdout_retained": False,
            "stderr_retained": False,
            "raw_traceback_included": False,
            "body_free": True,
        },
        "blocker_refs": dedupe_identifiers(
            [
                *_RECEIVED_SNAPSHOT_BLOCKER_REFS,
                "official_group_02_capture_green_unconfirmed",
                "full_backend_suite_green_unconfirmed",
            ],
            limit=40,
            max_length=200,
        ),
        "active_baseline_update_allowed": False,
        "official_group_02_capture_run_allowed": False,
        "official_group_02_capture_result_recording_allowed": False,
        "can_claim_group_green": False,
        "can_claim_full_backend_suite_green": False,
        **_release_closed_boundary(),
        "unresolved_hold_refs": [P7_HOLD004_BACKEND_SUITE_HOLD_ID],
        "required_followup_fixes": dedupe_identifiers(
            [
                *_REQUIRED_FOLLOWUP_FIXES,
                "r29_verification_procedure_fixed",
                "full_backend_collect_only_must_be_checked_before_any_baseline_refresh",
                "group_02_full_run_requires_readiness_ready_before_official_capture",
                "group_02_timeout_requires_body_free_timeout_material",
                "active_baseline_refresh_not_applied_to_runtime_builders",
            ],
            limit=80,
            max_length=200,
        ),
        "public_contract": _public_contract_boundary_flags(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_hold004_received_snapshot_r29_verification_procedure_contract(material)
    return material


def assert_p7_hold004_received_snapshot_r29_verification_procedure_contract(
    material: Mapping[str, Any],
) -> bool:
    """Validate the R29 verification-procedure material."""

    data = safe_mapping(material)
    source = "p7_hold004_received_snapshot_r29_verification_procedure"
    if data.get("schema_version") != P7_HOLD004_RECEIVED_SNAPSHOT_R29_VERIFICATION_PROCEDURE_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 R29 verification procedure schema_version mismatch")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError("P7-HOLD-004 R29 verification procedure scope mismatch")
    if data.get("implementation_step") != P7_HOLD004_RECEIVED_SNAPSHOT_R29_VERIFICATION_PROCEDURE_STEP:
        raise ValueError("P7-HOLD-004 R29 verification procedure implementation_step mismatch")
    if data.get("verification_id") != P7_HOLD004_RECEIVED_SNAPSHOT_R29_VERIFICATION_PROCEDURE_ID:
        raise ValueError("P7-HOLD-004 R29 verification procedure id mismatch")
    if data.get("source_mode") != P7_SOURCE_MODE or data.get("git_checked") is not False:
        raise ValueError("P7-HOLD-004 R29 verification procedure source mode mismatch")
    if data.get("received_zip_ref") != P7_HOLD004_RECEIVED_ZIP_REF:
        raise ValueError("P7-HOLD-004 R29 verification procedure received zip mismatch")
    if data.get("active_source_snapshot_ref_at_receipt") != P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT:
        raise ValueError("P7-HOLD-004 R29 verification procedure active source mismatch")
    if data.get("scope_status") != "R29_VERIFICATION_PROCEDURE_FIXED_RELEASE_CLOSED":
        raise ValueError("P7-HOLD-004 R29 verification procedure status mismatch")

    scope = safe_mapping(data.get("implementation_scope"))
    for key in (
        "r21_received_snapshot_constants_added",
        "r22_received_collect_summary_body_free_added",
        "r23_reconcile_material_added",
        "r24_adoption_decision_added",
        "r25_official_group02_readiness_guard_added",
        "r26_matrix_handoff_validation_connected",
        "r27_conditional_active_baseline_adoption_added",
        "r28_group02_timeout_long_run_policy_added",
        "pre_r29_received_snapshot_adoption_evidence_freeze_added",
        "r29_verification_procedure_fixed",
    ):
        if scope.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 R29 verification procedure missing scope flag {key}")
    for key in (
        "runtime_behavior_change_allowed",
        "rn_change_allowed",
        "api_contract_change_allowed",
        "db_change_allowed",
        "active_baseline_change_allowed",
        "release_decision_change_allowed",
        "p8_implementation_allowed",
    ):
        if scope.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 R29 verification procedure must keep {key}=false")

    sequence = list(data.get("verification_sequence") or [])
    if [safe_mapping(item).get("checkpoint_id") for item in sequence] != list(_R29_VERIFICATION_CHECKPOINT_IDS):
        raise ValueError("P7-HOLD-004 R29 verification sequence mismatch")
    for item in sequence:
        command = safe_mapping(item)
        if command.get("body_free") is not True:
            raise ValueError("P7-HOLD-004 R29 command must be body_free")
        if not command.get("command_id") or not command.get("command_kind"):
            raise ValueError("P7-HOLD-004 R29 command id/kind missing")
        if command.get("working_directory") != "mashos-api/ai":
            raise ValueError("P7-HOLD-004 R29 command working_directory mismatch")
        if not isinstance(command.get("argv"), list) or not command.get("argv"):
            raise ValueError("P7-HOLD-004 R29 command argv missing")
        for retained_key in (
            "nodeids_retained",
            "pytest_output_retained",
            "terminal_output_retained",
            "stdout_retained",
            "stderr_retained",
            "raw_traceback_included",
        ):
            if command.get(retained_key) is not False:
                raise ValueError(f"P7-HOLD-004 R29 command must keep {retained_key}=false")
    final_command = safe_mapping(sequence[-1])
    if final_command.get("execution_allowed_by_default") is not False:
        raise ValueError("P7-HOLD-004 R29 group_02 full run must be blocked by default")
    if final_command.get("allowed_when_readiness_status") != "READY_FOR_OFFICIAL_CAPTURE_RUN":
        raise ValueError("P7-HOLD-004 R29 group_02 full run readiness status mismatch")

    full_collect = safe_mapping(data.get("expected_full_backend_collect_only"))
    expected_full = _r29_expected_full_collect_summary()
    for key, expected in expected_full.items():
        if full_collect.get(key) != expected:
            raise ValueError(f"P7-HOLD-004 R29 full collect expectation {key} mismatch")
    group_collect = safe_mapping(data.get("expected_group02_collect_only"))
    expected_group = _r29_expected_group02_collect_summary()
    for key, expected in expected_group.items():
        if group_collect.get(key) != expected:
            raise ValueError(f"P7-HOLD-004 R29 group_02 collect expectation {key} mismatch")

    boundaries = safe_mapping(data.get("green_claim_boundaries"))
    for key in _R29_REQUIRED_GREEN_CLAIM_BOUNDARIES:
        if boundaries.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 R29 must keep {key}=false")
    for key in (
        "target_contract_subset_green_is_contract_green_only",
        "full_backend_suite_green_requires_full_execution_green",
        "official_group02_capture_requires_readiness_ready",
        "official_group02_timeout_requires_body_free_timeout_material",
        "official_group02_fail_requires_first_failure_identifiers_only",
        "previous_active_baseline_must_remain_traceable_after_adoption",
        "same_baseline_id_hash_replacement_blocked",
    ):
        if boundaries.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 R29 must keep {key}=true")

    adoption_inputs = safe_mapping(data.get("adoption_readiness_inputs"))
    if adoption_inputs.get("adoption_evidence_freeze_id") != P7_HOLD004_RECEIVED_SNAPSHOT_ADOPTION_EVIDENCE_FREEZE_ID:
        raise ValueError("P7-HOLD-004 R29 adoption evidence id mismatch")
    if adoption_inputs.get("conditional_adoption_id") != P7_HOLD004_RECEIVED_SNAPSHOT_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_ID:
        raise ValueError("P7-HOLD-004 R29 conditional adoption id mismatch")
    if adoption_inputs.get("adoption_evidence_freeze_satisfied") is True:
        if adoption_inputs.get("conditional_adoption_status") != (
            P7_HOLD004_RECEIVED_ADOPTION_STATUS_ADOPTABLE_AS_RECEIVED_SNAPSHOT_BASELINE_REFRESH
        ):
            raise ValueError("P7-HOLD-004 R29 satisfied evidence must project adoptable conditional status")
        if adoption_inputs.get("conditional_active_baseline_adoption_ready") is not True:
            raise ValueError("P7-HOLD-004 R29 satisfied evidence must project conditional adoption ready")
    else:
        if adoption_inputs.get("conditional_adoption_status") == (
            P7_HOLD004_RECEIVED_ADOPTION_STATUS_ADOPTABLE_AS_RECEIVED_SNAPSHOT_BASELINE_REFRESH
        ):
            raise ValueError("P7-HOLD-004 R29 blocked evidence must not project adoptable conditional status")
    for key in (
        "active_baseline_update_applied_to_runtime_builders",
        "source_snapshot_ref_updated_in_active_builders",
        "r29_applies_active_baseline_refresh",
        "r29_closes_hold004",
        "release_allowed_after_r29",
    ):
        if adoption_inputs.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 R29 adoption readiness must keep {key}=false")

    result_policy = safe_mapping(data.get("result_recording_policy"))
    if result_policy.get("r29_records_procedure_not_results") is not True:
        raise ValueError("P7-HOLD-004 R29 must record procedure, not results")
    for retained_key in (
        "command_output_retained",
        "pytest_output_retained",
        "nodeids_retained",
        "stdout_retained",
        "stderr_retained",
        "raw_traceback_included",
    ):
        if result_policy.get(retained_key) is not False:
            raise ValueError(f"P7-HOLD-004 R29 result policy must keep {retained_key}=false")
    if result_policy.get("body_free") is not True:
        raise ValueError("P7-HOLD-004 R29 result policy must be body_free")

    _assert_release_capture_closed_and_body_free(data, source=source)
    blockers = set(dedupe_identifiers(data.get("blocker_refs"), limit=40, max_length=200))
    for blocker in (
        "received_snapshot_collect_item_fingerprint_mismatch",
        "official_group_02_capture_green_unconfirmed",
        "full_backend_suite_green_unconfirmed",
    ):
        if blocker not in blockers:
            raise ValueError(f"P7-HOLD-004 R29 missing blocker {blocker}")
    followups = set(dedupe_identifiers(data.get("required_followup_fixes"), limit=80, max_length=200))
    for followup in (
        "r29_verification_procedure_fixed",
        "group_02_full_run_requires_readiness_ready_before_official_capture",
        "active_baseline_refresh_not_applied_to_runtime_builders",
    ):
        if followup not in followups:
            raise ValueError(f"P7-HOLD-004 R29 missing followup {followup}")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source=f"{source}.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)
    return True


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


def assert_p7_hold004_received_snapshot_adoption_evidence_freeze_contract(material: Mapping[str, Any]) -> bool:
    """Validate the pre-R29 adoption evidence freeze material."""

    data = safe_mapping(material)
    source = "p7_hold004_received_snapshot_adoption_evidence_freeze"
    if data.get("schema_version") != P7_HOLD004_RECEIVED_SNAPSHOT_ADOPTION_EVIDENCE_FREEZE_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 adoption evidence freeze schema_version mismatch")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError("P7-HOLD-004 adoption evidence freeze scope mismatch")
    if data.get("implementation_step") != P7_HOLD004_RECEIVED_SNAPSHOT_ADOPTION_EVIDENCE_FREEZE_STEP:
        raise ValueError("P7-HOLD-004 adoption evidence freeze implementation_step mismatch")
    if data.get("evidence_freeze_id") != P7_HOLD004_RECEIVED_SNAPSHOT_ADOPTION_EVIDENCE_FREEZE_ID:
        raise ValueError("P7-HOLD-004 adoption evidence freeze id mismatch")
    if data.get("received_reconcile_id") != P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_ID:
        raise ValueError("P7-HOLD-004 adoption evidence freeze reconcile id mismatch")
    if data.get("source_mode") != P7_SOURCE_MODE or data.get("git_checked") is not False:
        raise ValueError("P7-HOLD-004 adoption evidence freeze source mode mismatch")
    if data.get("received_zip_ref") != P7_HOLD004_RECEIVED_ZIP_REF:
        raise ValueError("P7-HOLD-004 adoption evidence freeze received zip mismatch")
    if data.get("candidate_new_baseline_id") != P7_HOLD004_RECEIVED_SNAPSHOT_CANDIDATE_NEW_BASELINE_ID:
        raise ValueError("P7-HOLD-004 adoption evidence freeze candidate baseline mismatch")

    repeat = safe_mapping(data.get("repeat_collect_evidence"))
    root = safe_mapping(data.get("root_cause_evidence"))
    source_identity = safe_mapping(data.get("source_identity_evidence"))
    semantics = safe_mapping(data.get("test_semantics_evidence"))
    traceability = safe_mapping(data.get("baseline_traceability_evidence"))
    connection_plan = safe_mapping(data.get("post_adoption_connection_plan_evidence"))
    for section_name, section in (
        ("repeat_collect_evidence", repeat),
        ("root_cause_evidence", root),
        ("source_identity_evidence", source_identity),
        ("test_semantics_evidence", semantics),
        ("baseline_traceability_evidence", traceability),
        ("post_adoption_connection_plan_evidence", connection_plan),
    ):
        if section.get("satisfied") not in {True, False}:
            raise ValueError(f"P7-HOLD-004 adoption evidence freeze {section_name}.satisfied must be bool")

    if repeat.get("minimum_collect_run_count") != 2:
        raise ValueError("P7-HOLD-004 adoption evidence freeze repeat collect minimum mismatch")
    if repeat.get("satisfied") is True:
        if repeat.get("provided_collect_run_count", 0) < 2:
            raise ValueError("P7-HOLD-004 adoption evidence freeze repeat collect satisfied too early")
        if repeat.get("counts_warnings_fingerprints_stable") is not True:
            raise ValueError("P7-HOLD-004 adoption evidence freeze repeat collect stability mismatch")
        if repeat.get("received_collect_matches_recorded_default") is not True:
            raise ValueError("P7-HOLD-004 adoption evidence freeze received collect default mismatch")
    for retained_key in ("nodeids_retained", "pytest_output_retained"):
        if repeat.get(retained_key) is not False:
            raise ValueError(f"P7-HOLD-004 adoption evidence freeze repeat collect must keep {retained_key}=false")

    normalized_root = _normalize_root_cause_status(root.get("root_cause_status"))
    if root.get("root_cause_status") != normalized_root:
        raise ValueError("P7-HOLD-004 adoption evidence freeze root cause invalid")
    if root.get("satisfied") is True:
        if root.get("root_cause_review_recorded") is not True:
            raise ValueError("P7-HOLD-004 adoption evidence freeze root cause review missing")
        if normalized_root not in P7_HOLD004_RECEIVED_ADOPTABLE_ROOT_CAUSE_STATUSES:
            raise ValueError("P7-HOLD-004 adoption evidence freeze cannot satisfy unclassified root cause")

    if source_identity.get("received_zip_ref") != P7_HOLD004_RECEIVED_ZIP_REF:
        raise ValueError("P7-HOLD-004 adoption evidence freeze source identity received zip mismatch")
    if source_identity.get("active_source_snapshot_ref_at_receipt") != P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT:
        raise ValueError("P7-HOLD-004 adoption evidence freeze source identity active snapshot mismatch")
    if source_identity.get("candidate_source_snapshot_ref") != P7_HOLD004_RECEIVED_ZIP_REF:
        raise ValueError("P7-HOLD-004 adoption evidence freeze candidate source snapshot mismatch")
    if source_identity.get("received_zip_promoted_to_source_snapshot_ref") is not False:
        raise ValueError("P7-HOLD-004 adoption evidence freeze must not promote source snapshot")
    if source_identity.get("satisfied") is True and (
        source_identity.get("source_identity_decision_recorded") is not True
        or source_identity.get("source_identity_accepted") is not True
    ):
        raise ValueError("P7-HOLD-004 adoption evidence freeze source identity satisfied without decision")

    outcome = _normalize_test_semantics_review_outcome(semantics.get("test_semantics_review_outcome"))
    if semantics.get("test_semantics_review_outcome") != outcome:
        raise ValueError("P7-HOLD-004 adoption evidence freeze test semantics outcome invalid")
    if semantics.get("satisfied") is True:
        if semantics.get("test_semantics_reviewed") is not True:
            raise ValueError("P7-HOLD-004 adoption evidence freeze test semantics review missing")
        if outcome == P7_HOLD004_RECEIVED_TEST_SEMANTICS_REVIEW_OUTCOME_NOT_REVIEWED:
            raise ValueError("P7-HOLD-004 adoption evidence freeze test semantics cannot be unreviewed")
    for retained_key in ("nodeids_retained", "pytest_output_retained", "raw_traceback_included"):
        if semantics.get(retained_key) is not False:
            raise ValueError(f"P7-HOLD-004 adoption evidence freeze semantics must keep {retained_key}=false")

    if traceability.get("satisfied") is True:
        for key in (
            "baseline_id_or_revision_update_planned",
            "candidate_baseline_id_changes",
            "same_baseline_id_hash_replacement_blocked",
            "previous_active_baseline_retained",
        ):
            if traceability.get(key) is not True:
                raise ValueError(f"P7-HOLD-004 adoption evidence freeze traceability requires {key}=true")
    if connection_plan.get("satisfied") is True:
        for key in ("runtime_builder_update_plan_recorded", "matrix_handoff_update_plan_recorded"):
            if connection_plan.get(key) is not True:
                raise ValueError(f"P7-HOLD-004 adoption evidence freeze connection plan requires {key}=true")
    for key in ("active_baseline_update_applied_to_runtime_builders", "source_snapshot_ref_updated_in_active_builders"):
        if connection_plan.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 adoption evidence freeze connection plan must keep {key}=false")

    can_mark = data.get("can_mark_r27_conditions_satisfied") is True
    if data.get("evidence_status") not in {
        P7_HOLD004_RECEIVED_ADOPTION_EVIDENCE_STATUS_BLOCKED_UNVERIFIED,
        P7_HOLD004_RECEIVED_ADOPTION_EVIDENCE_STATUS_SATISFIED_FOR_R27_CONDITIONAL_ADOPTION,
    }:
        raise ValueError("P7-HOLD-004 adoption evidence freeze status invalid")
    if can_mark:
        if data.get("evidence_status") != P7_HOLD004_RECEIVED_ADOPTION_EVIDENCE_STATUS_SATISFIED_FOR_R27_CONDITIONAL_ADOPTION:
            raise ValueError("P7-HOLD-004 adoption evidence freeze satisfied status mismatch")
        for section_name, section in (
            ("repeat_collect_evidence", repeat),
            ("root_cause_evidence", root),
            ("source_identity_evidence", source_identity),
            ("test_semantics_evidence", semantics),
            ("baseline_traceability_evidence", traceability),
            ("post_adoption_connection_plan_evidence", connection_plan),
        ):
            if section.get("satisfied") is not True:
                raise ValueError(f"P7-HOLD-004 adoption evidence freeze cannot satisfy without {section_name}")
        if data.get("adoption_status_if_applied_to_r27") != P7_HOLD004_RECEIVED_ADOPTION_STATUS_ADOPTABLE_AS_RECEIVED_SNAPSHOT_BASELINE_REFRESH:
            raise ValueError("P7-HOLD-004 adoption evidence freeze R27 status mismatch")
    else:
        if data.get("evidence_status") != P7_HOLD004_RECEIVED_ADOPTION_EVIDENCE_STATUS_BLOCKED_UNVERIFIED:
            raise ValueError("P7-HOLD-004 adoption evidence freeze blocked status mismatch")
        if data.get("adoption_status_if_applied_to_r27") == P7_HOLD004_RECEIVED_ADOPTION_STATUS_ADOPTABLE_AS_RECEIVED_SNAPSHOT_BASELINE_REFRESH:
            raise ValueError("P7-HOLD-004 adoption evidence freeze must not project adoptable while blocked")

    projection = safe_mapping(data.get("r27_condition_projection"))
    if projection.get("adoption_evidence_freeze_satisfied") is not can_mark:
        raise ValueError("P7-HOLD-004 adoption evidence freeze projection mismatch")
    if data.get("r27_manual_boolean_only_adoption_ready_allowed") is not False:
        raise ValueError("P7-HOLD-004 adoption evidence freeze must reject manual boolean-only readiness")

    for key in (
        "active_baseline_update_allowed",
        "official_group_02_capture_run_allowed",
        "official_group_02_capture_result_recording_allowed",
        "can_claim_group_green",
        "can_claim_full_backend_suite_green",
        "full_backend_suite_green_confirmed",
        "hold004_close_allowed",
        "p7_complete",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 adoption evidence freeze must keep {key}=false")
    unresolved_holds = set(dedupe_identifiers(data.get("unresolved_hold_refs"), limit=40, max_length=120))
    if P7_HOLD004_BACKEND_SUITE_HOLD_ID not in unresolved_holds:
        raise ValueError("P7-HOLD-004 adoption evidence freeze must keep P7-HOLD-004 unresolved")
    if data.get("body_free") is not True:
        raise ValueError("P7-HOLD-004 adoption evidence freeze must keep body_free=true")
    assert_false_markers(safe_mapping(data.get("public_contract")), source=f"{source}.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source=f"{source}.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)
    return True


def assert_p7_hold004_received_snapshot_conditional_active_baseline_adoption_contract(
    material: Mapping[str, Any],
) -> bool:
    """Validate the R27 conditional active-baseline adoption material."""

    data = safe_mapping(material)
    source = "p7_hold004_received_snapshot_conditional_active_baseline_adoption"
    if data.get("schema_version") != P7_HOLD004_RECEIVED_SNAPSHOT_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 conditional active baseline adoption schema_version mismatch")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError("P7-HOLD-004 conditional active baseline adoption scope mismatch")
    if data.get("implementation_step") != P7_HOLD004_RECEIVED_SNAPSHOT_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_STEP:
        raise ValueError("P7-HOLD-004 conditional active baseline adoption implementation_step mismatch")
    if data.get("adoption_id") != P7_HOLD004_RECEIVED_SNAPSHOT_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_ID:
        raise ValueError("P7-HOLD-004 conditional active baseline adoption id mismatch")
    if data.get("received_reconcile_id") != P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_FINGERPRINT_RECONCILE_ID:
        raise ValueError("P7-HOLD-004 conditional active baseline adoption reconcile id mismatch")
    if data.get("received_adoption_decision_id") != P7_HOLD004_RECEIVED_SNAPSHOT_BASELINE_ADOPTION_DECISION_ID:
        raise ValueError("P7-HOLD-004 conditional active baseline adoption R24 decision id mismatch")
    if data.get("source_mode") != P7_SOURCE_MODE or data.get("git_checked") is not False:
        raise ValueError("P7-HOLD-004 conditional active baseline adoption source mode mismatch")
    if data.get("received_zip_ref") != P7_HOLD004_RECEIVED_ZIP_REF:
        raise ValueError("P7-HOLD-004 conditional active baseline adoption received zip mismatch")

    previous = safe_mapping(data.get("previous_active_baseline"))
    expected_previous = _active_baseline_at_receipt_material()
    for key, expected in expected_previous.items():
        if previous.get(key) != expected:
            raise ValueError(f"P7-HOLD-004 conditional adoption previous_active_baseline.{key} mismatch")

    candidate = safe_mapping(data.get("candidate_active_baseline"))
    expected_candidate = _candidate_active_baseline_material()
    for key, expected in expected_candidate.items():
        if candidate.get(key) != expected:
            raise ValueError(f"P7-HOLD-004 conditional adoption candidate_active_baseline.{key} mismatch")
    if candidate.get("baseline_id") == previous.get("baseline_id"):
        raise ValueError("P7-HOLD-004 conditional adoption must not reuse the same baseline id")
    if candidate.get("source_snapshot_ref") != P7_HOLD004_RECEIVED_ZIP_REF:
        raise ValueError("P7-HOLD-004 conditional adoption candidate source snapshot mismatch")

    conditions = safe_mapping(data.get("adoption_conditions"))
    expected_condition_keys = {
        "received_zip_ref_is_expected",
        "received_collect_counts_match_expected",
        "counts_and_warnings_match_active_or_refresh_scope",
        "test_files_fingerprint_matches_active",
        "item_fingerprint_diff_recorded_as_refresh_candidate",
        "root_cause_classified",
        "repeated_collect_stable",
        "source_identity_decision_recorded",
        "source_identity_accepted",
        "test_semantics_reviewed",
        "baseline_id_or_revision_update_planned",
        "candidate_baseline_id_changes",
        "same_baseline_id_hash_replacement_blocked",
        "previous_active_baseline_retained",
        "public_contract_unchanged",
        "runtime_contract_unchanged",
        "adoption_evidence_freeze_satisfied",
    }
    if set(conditions) != expected_condition_keys:
        raise ValueError("P7-HOLD-004 conditional adoption condition keys mismatch")
    for key in expected_condition_keys:
        if not isinstance(conditions.get(key), bool):
            raise ValueError(f"P7-HOLD-004 conditional adoption condition {key} must be bool")
    for key in (
        "received_zip_ref_is_expected",
        "received_collect_counts_match_expected",
        "counts_and_warnings_match_active_or_refresh_scope",
        "test_files_fingerprint_matches_active",
        "item_fingerprint_diff_recorded_as_refresh_candidate",
        "baseline_id_or_revision_update_planned",
        "candidate_baseline_id_changes",
        "same_baseline_id_hash_replacement_blocked",
        "previous_active_baseline_retained",
        "public_contract_unchanged",
        "runtime_contract_unchanged",
    ):
        if conditions.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 conditional adoption required invariant {key} must stay true")

    root_cause = _normalize_root_cause_status(data.get("root_cause_status"))
    if data.get("root_cause_status") != root_cause:
        raise ValueError("P7-HOLD-004 conditional adoption root cause status invalid")
    status = clean_identifier(data.get("adoption_status"), max_length=160)
    if status not in P7_HOLD004_RECEIVED_ADOPTION_STATUSES:
        raise ValueError("P7-HOLD-004 conditional adoption status invalid")
    ready = status == P7_HOLD004_RECEIVED_ADOPTION_STATUS_ADOPTABLE_AS_RECEIVED_SNAPSHOT_BASELINE_REFRESH
    if data.get("active_baseline_adoption_ready") is not ready:
        raise ValueError("P7-HOLD-004 conditional adoption ready flag mismatch")
    if data.get("active_baseline_update_allowed") is not ready:
        raise ValueError("P7-HOLD-004 conditional adoption update_allowed mismatch")
    if data.get("source_snapshot_ref_update_allowed") is not ready:
        raise ValueError("P7-HOLD-004 conditional adoption source update_allowed mismatch")
    if data.get("adoption_evidence_freeze_satisfied") is not conditions.get("adoption_evidence_freeze_satisfied"):
        raise ValueError("P7-HOLD-004 conditional adoption evidence satisfied flag mismatch")
    if data.get("r27_manual_boolean_only_adoption_ready_allowed") is not False:
        raise ValueError("P7-HOLD-004 conditional adoption must reject manual boolean-only readiness")
    if ready:
        for required_key in (
            "root_cause_classified",
            "repeated_collect_stable",
            "source_identity_decision_recorded",
            "source_identity_accepted",
            "test_semantics_reviewed",
            "adoption_evidence_freeze_satisfied",
        ):
            if conditions.get(required_key) is not True:
                raise ValueError(f"P7-HOLD-004 conditional adoption ready requires {required_key}=true")
    else:
        if conditions.get("root_cause_classified") is not True and status != P7_HOLD004_RECEIVED_ADOPTION_STATUS_BLOCKED_UNCLASSIFIED_ITEM_FINGERPRINT_MISMATCH:
            raise ValueError("P7-HOLD-004 conditional adoption unclassified root cause must block adoption")

    for key in (
        "active_baseline_update_applied_to_runtime_builders",
        "source_snapshot_ref_updated_in_active_builders",
        "same_baseline_id_hash_replacement_allowed",
        "received_zip_promoted_to_source_snapshot_ref",
        "official_group_02_capture_run_allowed",
        "official_group_02_capture_result_recording_allowed",
        "can_claim_group_green",
        "can_claim_full_backend_suite_green",
        "full_backend_suite_green_confirmed",
        "hold004_close_allowed",
        "p7_complete",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 conditional active adoption must keep {key}=false")
    if data.get("official_group_02_capture_blocked_until_adopted") is not True:
        raise ValueError("P7-HOLD-004 conditional adoption must keep official capture blocked until builders are updated")

    unresolved_holds = set(dedupe_identifiers(data.get("unresolved_hold_refs"), limit=40, max_length=120))
    if P7_HOLD004_BACKEND_SUITE_HOLD_ID not in unresolved_holds:
        raise ValueError("P7-HOLD-004 conditional adoption must keep P7-HOLD-004 unresolved")
    followups = set(dedupe_identifiers(data.get("required_followup_fixes"), limit=80, max_length=200))
    if "active_baseline_refresh_not_applied_to_runtime_builders" not in followups:
        raise ValueError("P7-HOLD-004 conditional adoption must keep runtime builder refresh followup")
    if "full_backend_suite_green_unconfirmed" not in followups:
        raise ValueError("P7-HOLD-004 conditional adoption must keep full backend suite green unconfirmed")
    if data.get("body_free") is not True:
        raise ValueError("P7-HOLD-004 conditional adoption must keep body_free=true")
    assert_false_markers(safe_mapping(data.get("public_contract")), source=f"{source}.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source=f"{source}.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)
    return True


__all__ = [
    "P7_HOLD004_ACTIVE_BASELINE_ID_AT_RECEIPT",
    "P7_HOLD004_ACTIVE_SOURCE_SNAPSHOT_REF_AT_RECEIPT",
    "P7_HOLD004_ACTIVE_TEST_FILES_FINGERPRINT_SHA256_AT_RECEIPT",
    "P7_HOLD004_ACTIVE_TEST_ITEMS_FINGERPRINT_SHA256_AT_RECEIPT",
    "P7_HOLD004_RECEIVED_ADOPTION_STATUS_BLOCKED_UNCLASSIFIED_ITEM_FINGERPRINT_MISMATCH",
    "P7_HOLD004_RECEIVED_ADOPTION_STATUS_ADOPTABLE_AS_RECEIVED_SNAPSHOT_BASELINE_REFRESH",
    "P7_HOLD004_RECEIVED_ADOPTION_STATUS_BLOCKED_ADOPTION_EVIDENCE_NOT_FROZEN",
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
    "P7_HOLD004_RECEIVED_SNAPSHOT_ADOPTION_EVIDENCE_FREEZE_ID",
    "P7_HOLD004_RECEIVED_SNAPSHOT_ADOPTION_EVIDENCE_FREEZE_SCHEMA_VERSION",
    "P7_HOLD004_RECEIVED_SNAPSHOT_ADOPTION_EVIDENCE_FREEZE_STEP",
    "P7_HOLD004_RECEIVED_SNAPSHOT_R29_VERIFICATION_PROCEDURE_ID",
    "P7_HOLD004_RECEIVED_SNAPSHOT_R29_VERIFICATION_PROCEDURE_SCHEMA_VERSION",
    "P7_HOLD004_RECEIVED_SNAPSHOT_R29_VERIFICATION_PROCEDURE_STEP",
    "P7_HOLD004_RECEIVED_SNAPSHOT_CANDIDATE_NEW_BASELINE_ID",
    "P7_HOLD004_RECEIVED_SNAPSHOT_COLLECT_SUMMARY_ID",
    "P7_HOLD004_RECEIVED_SNAPSHOT_COLLECT_SUMMARY_SCHEMA_VERSION",
    "P7_HOLD004_RECEIVED_SNAPSHOT_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_ID",
    "P7_HOLD004_RECEIVED_SNAPSHOT_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_SCHEMA_VERSION",
    "P7_HOLD004_RECEIVED_SNAPSHOT_CONDITIONAL_ACTIVE_BASELINE_ADOPTION_STEP",
    "P7_HOLD004_RECEIVED_SNAPSHOT_SCOPE_FREEZE_ID",
    "P7_HOLD004_RECEIVED_SNAPSHOT_SCOPE_FREEZE_SCHEMA_VERSION",
    "P7_HOLD004_RECEIVED_TEST_FILES_FINGERPRINT_SHA256",
    "P7_HOLD004_RECEIVED_TEST_ITEMS_FINGERPRINT_SHA256",
    "P7_HOLD004_RECEIVED_ZIP_REF",
    "assert_p7_hold004_received_snapshot_baseline_adoption_decision_contract",
    "assert_p7_hold004_received_snapshot_baseline_fingerprint_reconcile_contract",
    "assert_p7_hold004_received_snapshot_adoption_evidence_freeze_contract",
    "assert_p7_hold004_received_snapshot_conditional_active_baseline_adoption_contract",
    "assert_p7_hold004_received_snapshot_r29_verification_procedure_contract",
    "assert_p7_hold004_received_snapshot_collect_summary_contract",
    "assert_p7_hold004_received_snapshot_scope_freeze_contract",
    "build_p7_hold004_received_snapshot_baseline_adoption_decision",
    "build_p7_hold004_received_snapshot_baseline_fingerprint_reconcile",
    "build_p7_hold004_received_snapshot_adoption_evidence_freeze",
    "build_p7_hold004_received_snapshot_conditional_active_baseline_adoption",
    "build_p7_hold004_received_snapshot_r29_verification_procedure",
    "build_p7_hold004_received_snapshot_collect_summary",
    "build_p7_hold004_received_snapshot_scope_freeze",
]
