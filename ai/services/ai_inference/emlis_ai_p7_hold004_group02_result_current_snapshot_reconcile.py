# -*- coding: utf-8 -*-
"""P7-HOLD-004 R41-R46 group_02 result / current snapshot reconcile materials.

R41-R46 scope only:
- freeze the locally observed group_02 P7-HOLD-004 execution result as
  body-free evidence;
- reconcile that local evidence with the existing R40 official group_02 result
  recording without changing the R40 default NOT_RUN behavior;
- allow an explicit source-accepted wrapper to feed a body-free group_02 PASS
  run_result into R40 as PASSED_ISOLATED;
- never promote group_02 isolated PASS to full backend-suite green, HOLD closure,
  P7 completion, P8 start, release readiness, or Emlis runtime changes;
- freeze the current working snapshot collect-only drift as body-free evidence;
- classify active-baseline vs current-working-snapshot drift without updating
  the active baseline or treating collect-only as execution green;
- project the reconciled group_02 isolated result and current snapshot drift into
  matrix/release/validation material while keeping release closed;
- materialize the next-step decision to return to P5/P6 human readfeel and real
  device modal review instead of auto-continuing backend group execution.

Only identifiers, counts, booleans, enum-like statuses, and projection IDs are
stored. Raw input, comment_text bodies, candidate/surface bodies, pytest nodeid
lists, terminal output, stdout/stderr, and traceback bodies must not be stored.
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
from emlis_ai_p7_hold004_active_baseline_runtime_builder_refresh import (
    P7_HOLD004_FULL_BACKEND_SUITE_GATE_ID,
    P7_HOLD004_FULL_BACKEND_SUITE_GATE_STATUS_BLOCKED_REMAINING_GROUPS,
    P7_HOLD004_GROUP02_RESULT_STATUS_NOT_RUN,
    P7_HOLD004_GROUP02_RESULT_STATUS_PASSED_ISOLATED,
    P7_HOLD004_OFFICIAL_GROUP02_RESULT_RECORDING_ID,
    assert_p7_hold004_full_backend_suite_gate_contract,
    assert_p7_hold004_official_group02_result_recording_contract,
    build_p7_hold004_full_backend_suite_gate,
    build_p7_hold004_official_group02_result_recording,
)
from emlis_ai_p7_hold004_backend_suite_execution_results import (
    P7_HOLD004_BACKEND_SUITE_RUN_KIND_CAPTURE,
    P7_HOLD004_BACKEND_SUITE_STATUS_PASS,
    P7_HOLD004_GROUP02_OFFICIAL_BATCH_ID,
    P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID,
    P7_HOLD004_GROUP02_OFFICIAL_TEST_ITEM_COUNT,
    P7_HOLD004_GROUP02_OFFICIAL_WARNINGS_COUNT,
    assert_p7_hold004_backend_suite_group_run_result_contract,
    build_p7_hold004_backend_suite_group_run_result,
)
from emlis_ai_p7_hold004_backend_suite_group_inventory_plan import (
    P7_HOLD004_BACKEND_SUITE_GROUP_IDS,
)
from emlis_ai_p7_hold004_backend_suite_split_consistency import (
    P7_HOLD004_BACKEND_COLLECT_BASELINE_ID,
    P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM,
    P7_HOLD004_BACKEND_COLLECT_WARNINGS_COUNT,
    P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT,
    P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT,
    P7_HOLD004_BACKEND_SOURCE_SNAPSHOT_REF,
    P7_HOLD004_BACKEND_SUITE_HOLD_ID,
    P7_HOLD004_BACKEND_TEST_FILES_SHA256,
    P7_HOLD004_BACKEND_TEST_ITEMS_SHA256,
)

P7_HOLD004_GROUP02_LOCAL_EXECUTION_EVIDENCE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.group02_local_execution_evidence.v1"
)
P7_HOLD004_GROUP02_OFFICIAL_RESULT_RECORDING_RECONCILE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.group02_official_result_recording_reconcile.v1"
)
P7_HOLD004_GROUP02_LOCAL_EXECUTION_EVIDENCE_STEP: Final = (
    "P7-HOLD-004_Group02ResultCurrentSnapshotReconcile_R41_LocalExecutionEvidenceFreeze_20260617"
)
P7_HOLD004_GROUP02_OFFICIAL_RESULT_RECORDING_RECONCILE_STEP: Final = (
    "P7-HOLD-004_Group02ResultCurrentSnapshotReconcile_R42_OfficialResultRecordingReconcile_20260617"
)
P7_HOLD004_GROUP02_LOCAL_EXECUTION_EVIDENCE_ID: Final = (
    "p7_hold004_group02_local_execution_evidence_20260617"
)
P7_HOLD004_GROUP02_OFFICIAL_RESULT_RECORDING_RECONCILE_ID: Final = (
    "p7_hold004_group02_official_result_recording_reconcile_20260617"
)
P7_HOLD004_GROUP02_LOCAL_EXECUTION_COMMAND_ID: Final = (
    "pytest_group_02_p7_hold004_local_execution_20260617"
)
P7_HOLD004_GROUP02_LOCAL_EXECUTION_COMMAND_SCOPE_ID: Final = (
    "tests_test_emlis_ai_p7_hold004_glob"
)
P7_HOLD004_GROUP02_LOCAL_EXECUTION_STATUS_PASS: Final = "PASS"
P7_HOLD004_GROUP02_OBSERVED_EXECUTION_SOURCE_REF: Final = "mashos-api(152).zip"

P7_HOLD004_GROUP02_SOURCE_STATUS_REQUIRES_DECISION: Final = (
    "CURRENT_LOCAL_ATTACHMENT_EXECUTION_REQUIRES_OFFICIAL_RECORDING_SOURCE_DECISION"
)
P7_HOLD004_GROUP02_SOURCE_STATUS_ACCEPTED_AFTER_EXPLICIT_LOCAL_RERUN: Final = (
    "ACCEPTED_AS_OFFICIAL_GROUP02_CAPTURE_AFTER_EXPLICIT_LOCAL_RERUN"
)
P7_HOLD004_GROUP02_SOURCE_STATUS_BLOCKED_SOURCE_REF_DIFFERS: Final = (
    "BLOCKED_SOURCE_REF_DIFFERS_FROM_ACTIVE_BASELINE"
)
P7_HOLD004_GROUP02_SOURCE_STATUS_BLOCKED_CURRENT_COLLECT_DRIFT: Final = (
    "BLOCKED_CURRENT_COLLECT_DRIFT_UNCLASSIFIED"
)
P7_HOLD004_GROUP02_SOURCE_STATUS_BLOCKED_COMMAND_SCOPE: Final = "BLOCKED_COMMAND_SCOPE_MISMATCH"
P7_HOLD004_GROUP02_SOURCE_STATUS_BLOCKED_COUNTS: Final = "BLOCKED_COUNTS_MISMATCH"
P7_HOLD004_GROUP02_SOURCE_IDENTITY_STATUSES: Final[tuple[str, ...]] = (
    P7_HOLD004_GROUP02_SOURCE_STATUS_REQUIRES_DECISION,
    P7_HOLD004_GROUP02_SOURCE_STATUS_ACCEPTED_AFTER_EXPLICIT_LOCAL_RERUN,
    P7_HOLD004_GROUP02_SOURCE_STATUS_BLOCKED_SOURCE_REF_DIFFERS,
    P7_HOLD004_GROUP02_SOURCE_STATUS_BLOCKED_CURRENT_COLLECT_DRIFT,
    P7_HOLD004_GROUP02_SOURCE_STATUS_BLOCKED_COMMAND_SCOPE,
    P7_HOLD004_GROUP02_SOURCE_STATUS_BLOCKED_COUNTS,
)


P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_DRIFT_EVIDENCE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.current_working_snapshot_collect_drift_evidence.v1"
)
P7_HOLD004_ACTIVE_BASELINE_CURRENT_SNAPSHOT_DRIFT_CLASSIFICATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.active_baseline_current_snapshot_drift_classification.v1"
)
P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_DRIFT_EVIDENCE_STEP: Final = (
    "P7-HOLD-004_Group02ResultCurrentSnapshotReconcile_R43_CurrentWorkingSnapshotCollectDriftEvidence_20260617"
)
P7_HOLD004_ACTIVE_BASELINE_CURRENT_SNAPSHOT_DRIFT_CLASSIFICATION_STEP: Final = (
    "P7-HOLD-004_Group02ResultCurrentSnapshotReconcile_R44_DriftClassification_20260617"
)
P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_DRIFT_EVIDENCE_ID: Final = (
    "p7_hold004_current_working_snapshot_collect_drift_evidence_20260617"
)
P7_HOLD004_ACTIVE_BASELINE_CURRENT_SNAPSHOT_DRIFT_CLASSIFICATION_ID: Final = (
    "p7_hold004_active_baseline_current_snapshot_drift_classification_20260617"
)
P7_HOLD004_CURRENT_WORKING_SNAPSHOT_REF: Final = "mashos-api_2(97).zip"
P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_COMMAND_ID: Final = (
    "pytest_collect_only_backend_current_working_snapshot_after_r41_r42_20260617"
)
P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_SCOPE: Final = "full_backend_collect_only"
P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECTED_TEST_FILE_COUNT: Final = 432
P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECTED_TEST_ITEM_COUNT: Final = 2892
P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_WARNINGS_COUNT: Final = 1
P7_HOLD004_CURRENT_WORKING_SNAPSHOT_TEST_ITEMS_SHA256: Final = (
    "ae01c9f99025c065d29543b3b97508b9a9080ef1058c172fcee77181a66695f1"
)
P7_HOLD004_CURRENT_WORKING_SNAPSHOT_TEST_FILES_SHA256: Final = (
    "97a8c0a77c18f63920deeb750c54228ed36f8714c5677c15449a6beedb301125"
)
P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DELTA_TEST_FILE_COUNT: Final = (
    P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECTED_TEST_FILE_COUNT
    - P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT
)
P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DELTA_TEST_ITEM_COUNT: Final = (
    P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECTED_TEST_ITEM_COUNT
    - P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT
)
P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DELTA_WARNINGS_COUNT: Final = (
    P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_WARNINGS_COUNT - P7_HOLD004_BACKEND_COLLECT_WARNINGS_COUNT
)
P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DRIFT_STATUS_UNCLASSIFIED: Final = (
    "UNCLASSIFIED_CURRENT_WORKING_SNAPSHOT_COLLECT_DRIFT"
)
P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DRIFT_STATUS_R30_R42_TEST_ADDITION_ACCEPTED: Final = (
    "R30_R42_CONTRACT_TEST_ADDITION_DRIFT_ACCEPTED_AS_CURRENT_WORKING_SNAPSHOT_ONLY"
)
P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DRIFT_CLASSIFICATION_STATUSES: Final[tuple[str, ...]] = (
    P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DRIFT_STATUS_UNCLASSIFIED,
    P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DRIFT_STATUS_R30_R42_TEST_ADDITION_ACCEPTED,
)
P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_FILE_REFS: Final[tuple[str, ...]] = (
    "tests/test_emlis_ai_p7_active_baseline_adoption_evidence_r30_r31_20260616.py",
    "tests/test_emlis_ai_p7_active_baseline_adoption_evidence_r32_r33_20260616.py",
    "tests/test_emlis_ai_p7_active_baseline_adoption_evidence_r34_r35_20260616.py",
    "tests/test_emlis_ai_p7_active_baseline_runtime_builder_refresh_r36_r37_20260616.py",
    "tests/test_emlis_ai_p7_active_baseline_runtime_builder_refresh_r38_r39_20260616.py",
    "tests/test_emlis_ai_p7_active_baseline_runtime_builder_refresh_r40_20260616.py",
    "tests/test_emlis_ai_p7_group02_current_snapshot_reconcile_r41_r42_20260617.py",
)
P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_FILE_COUNT: Final = len(
    P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_FILE_REFS
)
P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_ITEM_COUNT: Final = 36
_SHA256_HEX_LENGTH: Final = 64

P7_HOLD004_GROUP02_RECONCILE_SCOPE_NON_OFFICIAL_LOCAL_EVIDENCE: Final = (
    "non_official_local_evidence_only"
)
P7_HOLD004_GROUP02_RECONCILE_SCOPE_GROUP02_ISOLATED_ONLY: Final = "group_02_isolated_only"

P7_HOLD004_GROUP02_CURRENT_SNAPSHOT_RELEASE_PROJECTION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.group02_current_snapshot_release_projection.v1"
)
P7_HOLD004_NEXT_EXECUTION_OR_P5_P6_RETURN_DECISION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.next_execution_or_p5_p6_return_decision.v1"
)
P7_HOLD004_GROUP02_CURRENT_SNAPSHOT_RELEASE_PROJECTION_STEP: Final = (
    "P7-HOLD-004_Group02ResultCurrentSnapshotReconcile_R45_ReleaseProjection_20260617"
)
P7_HOLD004_NEXT_EXECUTION_OR_P5_P6_RETURN_DECISION_STEP: Final = (
    "P7-HOLD-004_Group02ResultCurrentSnapshotReconcile_R46_NextDecision_20260617"
)
P7_HOLD004_GROUP02_CURRENT_SNAPSHOT_RELEASE_PROJECTION_ID: Final = (
    "p7_hold004_group02_current_snapshot_release_projection_20260617"
)
P7_HOLD004_NEXT_EXECUTION_OR_P5_P6_RETURN_DECISION_ID: Final = (
    "p7_hold004_next_execution_or_p5_p6_return_decision_20260617"
)
P7_HOLD004_GROUP02_CURRENT_SNAPSHOT_RELEASE_PROJECTION_STATUS: Final = (
    "R41_R44_PROJECTED_RELEASE_CLOSED_P5_P6_RETURN_REQUIRED"
)
P7_HOLD004_NEXT_DECISION_STATUS_P5_P6_RETURN_RECOMMENDED: Final = (
    "P5_P6_HUMAN_READFEEL_AND_REAL_DEVICE_MODAL_REVIEW_RECOMMENDED_AFTER_R41_R45"
)
P7_HOLD004_NEXT_RECOMMENDED_WORK_P5_P6_HUMAN_READFEEL_REAL_DEVICE_MODAL: Final = (
    "P5_P6_HUMAN_READFEEL_AND_REAL_DEVICE_MODAL_REVIEW"
)
P7_HOLD004_BACKEND_GROUP03_BLOCK_REASON_P5_P6_RETURN_PRIORITIZED: Final = (
    "P5_P6_RETURN_PRIORITIZED_AFTER_GROUP02_RESULT_AND_CURRENT_DRIFT_RECONCILE"
)
P7_HOLD004_BACKEND_GROUP03_DEFERRED_STATUS_NOT_PERMANENTLY_FORBIDDEN: Final = (
    "DEFERRED_NOW_NOT_PERMANENTLY_FORBIDDEN"
)
P7_HOLD004_GROUP02_VALIDATION_SCOPE_ISOLATED_NOT_FULL_SUITE: Final = (
    "group_02_isolated_only_not_full_backend_suite"
)
P7_HOLD004_P5_P6_RETURN_SCOPE: Final = "p5_p6_human_readfeel_real_device_modal_review"
P7_HOLD004_P5_P6_RETURN_REQUIRED_HOLD_REFS: Final[tuple[str, ...]] = (
    "P7-HOLD-001",
    "P7-HOLD-002",
    "P7-HOLD-003",
    "P7-HOLD-004",
)
P7_HOLD004_P5_P6_RETURN_REQUIRED_WORK_ITEMS: Final[tuple[str, ...]] = (
    "p5_human_blind_qa_review",
    "p6_limited_visible_expansion_human_readfeel_review",
    "real_device_submit_modal_readfeel_review",
    "remaining_backend_groups_official_execution_later",
)

_RELEASE_CLOSED_KEYS: Final[tuple[str, ...]] = (
    "can_claim_full_backend_suite_green",
    "full_backend_suite_green_confirmed",
    "full_backend_suite_green_claim_allowed",
    "hold004_close_allowed",
    "p7_complete",
    "p7_complete_claim_allowed",
    "p8_start_allowed",
    "release_allowed",
)
_BODY_RETENTION_KEYS: Final[tuple[str, ...]] = (
    "terminal_output_retained",
    "stdout_retained",
    "stderr_retained",
    "raw_traceback_included",
    "nodeids_retained",
    "raw_input_retained",
    "comment_text_retained",
    "candidate_body_retained",
    "surface_body_retained",
)
_FORBIDDEN_NODEID_COLLECTION_KEYS: Final[frozenset[str]] = frozenset(
    {"nodeids", "nodeid_list", "full_nodeid_list", "pytest_nodeids", "pytest_nodeid_list"}
)


def _release_closed_flags() -> dict[str, bool]:
    return {key: False for key in _RELEASE_CLOSED_KEYS}


def _body_retention_flags() -> dict[str, bool]:
    return {key: False for key in _BODY_RETENTION_KEYS}


def _observed_counts(
    *,
    passed: Any,
    failed: Any,
    skipped: Any,
    warnings: Any,
    errors: Any,
    deselected: Any,
) -> dict[str, int]:
    return {
        "passed": _coerce_non_negative_int(passed, default=0),
        "failed": _coerce_non_negative_int(failed, default=0),
        "skipped": _coerce_non_negative_int(skipped, default=0),
        "warnings": _coerce_non_negative_int(warnings, default=0),
        "errors": _coerce_non_negative_int(errors, default=0),
        "deselected": _coerce_non_negative_int(deselected, default=0),
    }


def _coerce_non_negative_int(value: Any, *, default: int = 0) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return number if number >= 0 else default


def _source_identity_status(value: Any) -> str:
    status = clean_identifier(
        value,
        default=P7_HOLD004_GROUP02_SOURCE_STATUS_REQUIRES_DECISION,
        max_length=180,
    )
    return status if status in P7_HOLD004_GROUP02_SOURCE_IDENTITY_STATUSES else P7_HOLD004_GROUP02_SOURCE_STATUS_REQUIRES_DECISION


def _assert_release_closed_and_body_free(data: Mapping[str, Any], *, source: str) -> None:
    for key in _RELEASE_CLOSED_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=false")
    for key in _BODY_RETENTION_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=false")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must be body_free=true")
    if any(key in data for key in _FORBIDDEN_NODEID_COLLECTION_KEYS):
        raise ValueError(f"{source} must not retain pytest nodeid collections")
    assert_false_markers(safe_mapping(data.get("public_contract")), source=f"{source}.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source=f"{source}.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)


def _counts_match_group02_pass(counts: Mapping[str, Any]) -> bool:
    observed = safe_mapping(counts)
    return (
        observed.get("passed") == P7_HOLD004_GROUP02_OFFICIAL_TEST_ITEM_COUNT
        and observed.get("failed") == 0
        and observed.get("skipped") == 0
        and observed.get("warnings") == P7_HOLD004_GROUP02_OFFICIAL_WARNINGS_COUNT
        and observed.get("errors") == 0
        and observed.get("deselected") == 0
    )


def build_p7_hold004_group02_local_execution_evidence(
    *,
    observed_execution_source_ref: str = P7_HOLD004_GROUP02_OBSERVED_EXECUTION_SOURCE_REF,
    active_source_snapshot_ref: str = P7_HOLD004_BACKEND_SOURCE_SNAPSHOT_REF,
    source_identity_status: str = P7_HOLD004_GROUP02_SOURCE_STATUS_REQUIRES_DECISION,
    passed: Any = P7_HOLD004_GROUP02_OFFICIAL_TEST_ITEM_COUNT,
    warnings: Any = P7_HOLD004_GROUP02_OFFICIAL_WARNINGS_COUNT,
    failed: Any = 0,
    skipped: Any = 0,
    errors: Any = 0,
    deselected: Any = 0,
    pytest_exit_code: Any = 0,
) -> dict[str, Any]:
    """Freeze the R41 locally observed group_02 execution as body-free evidence."""

    counts = _observed_counts(
        passed=passed,
        failed=failed,
        skipped=skipped,
        warnings=warnings,
        errors=errors,
        deselected=deselected,
    )
    normalized_source_status = _source_identity_status(source_identity_status)
    observed_source = clean_identifier(
        observed_execution_source_ref,
        default=P7_HOLD004_GROUP02_OBSERVED_EXECUTION_SOURCE_REF,
        max_length=180,
    )
    active_source = clean_identifier(
        active_source_snapshot_ref,
        default=P7_HOLD004_BACKEND_SOURCE_SNAPSHOT_REF,
        max_length=180,
    )
    source_ref_differs = observed_source != active_source
    source_accepted = normalized_source_status == P7_HOLD004_GROUP02_SOURCE_STATUS_ACCEPTED_AFTER_EXPLICIT_LOCAL_RERUN
    material = {
        "schema_version": P7_HOLD004_GROUP02_LOCAL_EXECUTION_EVIDENCE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "step": P7_HOLD004_GROUP02_LOCAL_EXECUTION_EVIDENCE_STEP,
        "implementation_step": P7_HOLD004_GROUP02_LOCAL_EXECUTION_EVIDENCE_STEP,
        "evidence_id": P7_HOLD004_GROUP02_LOCAL_EXECUTION_EVIDENCE_ID,
        "source_mode": P7_SOURCE_MODE,
        "git_checked": P7_GIT_CHECKED,
        "observed_execution_source_ref": observed_source,
        "active_source_snapshot_ref": active_source,
        "active_baseline_id": P7_HOLD004_BACKEND_COLLECT_BASELINE_ID,
        "group_id": P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID,
        "batch_id": P7_HOLD004_GROUP02_OFFICIAL_BATCH_ID,
        "command_id": P7_HOLD004_GROUP02_LOCAL_EXECUTION_COMMAND_ID,
        "command_scope_id": P7_HOLD004_GROUP02_LOCAL_EXECUTION_COMMAND_SCOPE_ID,
        "run_kind": P7_HOLD004_BACKEND_SUITE_RUN_KIND_CAPTURE,
        "status": P7_HOLD004_GROUP02_LOCAL_EXECUTION_STATUS_PASS,
        "pytest_exit_code": _coerce_non_negative_int(pytest_exit_code, default=0),
        "observed_counts": counts,
        "source_identity_status": normalized_source_status,
        "source_ref_differs_from_active_snapshot": source_ref_differs,
        "source_identity_accepted_for_official_recording": source_accepted,
        "official_recording_source_decision_required": not source_accepted,
        "local_execution_passed": True,
        "official_result_recording_applied": False,
        "can_claim_group_green": False,
        "group_green_scope": P7_HOLD004_GROUP02_RECONCILE_SCOPE_NON_OFFICIAL_LOCAL_EVIDENCE,
        "local_pass_is_not_full_backend_suite_green": True,
        **_release_closed_flags(),
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
        **_body_retention_flags(),
        "body_free": True,
    }
    assert_p7_hold004_group02_local_execution_evidence_contract(material)
    return material


def assert_p7_hold004_group02_local_execution_evidence_contract(material: Mapping[str, Any]) -> bool:
    """Validate R41 local execution evidence without promoting it to official green."""

    data = safe_mapping(material)
    source = "p7_hold004_r41_group02_local_execution_evidence"
    if data.get("schema_version") != P7_HOLD004_GROUP02_LOCAL_EXECUTION_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 R41 local evidence schema mismatch")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError("P7-HOLD-004 R41 local evidence phase/hold mismatch")
    if data.get("step") != P7_HOLD004_GROUP02_LOCAL_EXECUTION_EVIDENCE_STEP:
        raise ValueError("P7-HOLD-004 R41 local evidence step mismatch")
    if data.get("evidence_id") != P7_HOLD004_GROUP02_LOCAL_EXECUTION_EVIDENCE_ID:
        raise ValueError("P7-HOLD-004 R41 local evidence id mismatch")
    if data.get("source_mode") != P7_SOURCE_MODE or data.get("git_checked") is not P7_GIT_CHECKED:
        raise ValueError("P7-HOLD-004 R41 local evidence source boundary mismatch")
    if not clean_identifier(data.get("observed_execution_source_ref"), max_length=180):
        raise ValueError("P7-HOLD-004 R41 local evidence observed source ref required")
    if data.get("active_source_snapshot_ref") != P7_HOLD004_BACKEND_SOURCE_SNAPSHOT_REF:
        raise ValueError("P7-HOLD-004 R41 local evidence active source ref mismatch")
    if data.get("active_baseline_id") != P7_HOLD004_BACKEND_COLLECT_BASELINE_ID:
        raise ValueError("P7-HOLD-004 R41 local evidence active baseline id mismatch")
    if data.get("group_id") != P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID:
        raise ValueError("P7-HOLD-004 R41 local evidence group_id mismatch")
    if data.get("batch_id") != P7_HOLD004_GROUP02_OFFICIAL_BATCH_ID:
        raise ValueError("P7-HOLD-004 R41 local evidence batch_id mismatch")
    if data.get("command_id") != P7_HOLD004_GROUP02_LOCAL_EXECUTION_COMMAND_ID:
        raise ValueError("P7-HOLD-004 R41 local evidence command id mismatch")
    if data.get("command_scope_id") != P7_HOLD004_GROUP02_LOCAL_EXECUTION_COMMAND_SCOPE_ID:
        raise ValueError("P7-HOLD-004 R41 local evidence command scope mismatch")
    if data.get("run_kind") != P7_HOLD004_BACKEND_SUITE_RUN_KIND_CAPTURE:
        raise ValueError("P7-HOLD-004 R41 local evidence must be capture_run")
    if data.get("status") != P7_HOLD004_GROUP02_LOCAL_EXECUTION_STATUS_PASS:
        raise ValueError("P7-HOLD-004 R41 local evidence must freeze PASS")
    if data.get("pytest_exit_code") != 0:
        raise ValueError("P7-HOLD-004 R41 local evidence pytest_exit_code must be 0")
    counts = safe_mapping(data.get("observed_counts"))
    if not _counts_match_group02_pass(counts):
        raise ValueError("P7-HOLD-004 R41 local evidence counts must stay 252 passed / 1 warning")
    status = clean_identifier(data.get("source_identity_status"), max_length=180)
    if status not in P7_HOLD004_GROUP02_SOURCE_IDENTITY_STATUSES:
        raise ValueError("P7-HOLD-004 R41 local evidence source identity status mismatch")
    source_accepted = status == P7_HOLD004_GROUP02_SOURCE_STATUS_ACCEPTED_AFTER_EXPLICIT_LOCAL_RERUN
    if data.get("source_identity_accepted_for_official_recording") is not source_accepted:
        raise ValueError("P7-HOLD-004 R41 local evidence source accepted flag mismatch")
    if data.get("official_recording_source_decision_required") is not (not source_accepted):
        raise ValueError("P7-HOLD-004 R41 local evidence source decision flag mismatch")
    if data.get("source_ref_differs_from_active_snapshot") is not (
        data.get("observed_execution_source_ref") != data.get("active_source_snapshot_ref")
    ):
        raise ValueError("P7-HOLD-004 R41 local evidence source diff flag mismatch")
    if data.get("local_execution_passed") is not True:
        raise ValueError("P7-HOLD-004 R41 local evidence must record local pass")
    for key in ("official_result_recording_applied", "can_claim_group_green"):
        if data.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 R41 local evidence must keep {key}=false")
    if data.get("group_green_scope") != P7_HOLD004_GROUP02_RECONCILE_SCOPE_NON_OFFICIAL_LOCAL_EVIDENCE:
        raise ValueError("P7-HOLD-004 R41 local evidence scope must stay non-official")
    if data.get("local_pass_is_not_full_backend_suite_green") is not True:
        raise ValueError("P7-HOLD-004 R41 local pass must not become full suite green")
    _assert_release_closed_and_body_free(data, source=source)
    return True


def _build_group02_pass_run_result_from_evidence(evidence: Mapping[str, Any]) -> dict[str, Any]:
    data = safe_mapping(evidence)
    assert_p7_hold004_group02_local_execution_evidence_contract(data)
    counts = safe_mapping(data.get("observed_counts"))
    result = build_p7_hold004_backend_suite_group_run_result(
        group_id=P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID,
        batch_id=P7_HOLD004_GROUP02_OFFICIAL_BATCH_ID,
        run_kind=P7_HOLD004_BACKEND_SUITE_RUN_KIND_CAPTURE,
        status=P7_HOLD004_BACKEND_SUITE_STATUS_PASS,
        pytest_exit_code=0,
        passed=counts.get("passed"),
        failed=counts.get("failed"),
        skipped=counts.get("skipped"),
        warnings=counts.get("warnings"),
        errors=counts.get("errors"),
        deselected=counts.get("deselected"),
        reason_codes=("r42_group02_source_identity_accepted_explicit_wrapper",),
        required_followup_fixes=("group_02_green_is_not_full_backend_suite_green",),
    )
    assert_p7_hold004_backend_suite_group_run_result_contract(result)
    return result


def _r40_recording_projection(recording: Mapping[str, Any]) -> dict[str, Any]:
    data = safe_mapping(recording)
    return {
        "recording_id": clean_identifier(data.get("recording_id"), max_length=180),
        "result_status": clean_identifier(data.get("result_status"), max_length=80),
        "official_group_02_capture_result_recorded": data.get("official_group_02_capture_result_recorded") is True,
        "official_group_02_capture_green_confirmed": data.get("official_group_02_capture_green_confirmed") is True,
        "can_claim_group_green": data.get("can_claim_group_green") is True,
        "can_claim_full_backend_suite_green": data.get("can_claim_full_backend_suite_green") is True,
        "full_backend_suite_green_confirmed": data.get("full_backend_suite_green_confirmed") is True,
        "remaining_backend_group_count": _coerce_non_negative_int(data.get("remaining_backend_group_count"), default=0),
        "body_free": data.get("body_free") is True,
    }


def _r40_gate_projection(gate: Mapping[str, Any]) -> dict[str, Any]:
    data = safe_mapping(gate)
    return {
        "gate_id": clean_identifier(data.get("gate_id"), max_length=180),
        "full_backend_suite_gate_status": clean_identifier(data.get("full_backend_suite_gate_status"), max_length=180),
        "full_backend_suite_green_confirmed": data.get("full_backend_suite_green_confirmed") is True,
        "can_claim_full_backend_suite_green": data.get("can_claim_full_backend_suite_green") is True,
        "remaining_backend_group_count": _coerce_non_negative_int(data.get("remaining_backend_group_count"), default=0),
        "hold004_close_allowed": data.get("hold004_close_allowed") is True,
        "p7_complete": data.get("p7_complete") is True,
        "p8_start_allowed": data.get("p8_start_allowed") is True,
        "release_allowed": data.get("release_allowed") is True,
        "body_free": data.get("body_free") is True,
    }


def build_p7_hold004_group02_official_result_recording_reconcile(
    *,
    local_execution_evidence: Mapping[str, Any] | None = None,
    source_identity_status: str | None = None,
    apply_to_r40_official_recording: bool = False,
) -> dict[str, Any]:
    """Safely reconcile R41 local evidence with the existing R40 recording.

    The R40 builder itself keeps default NOT_RUN. This wrapper applies a
    PASSED_ISOLATED result only when the caller explicitly requests recording
    and supplies/chooses the accepted source-identity status.
    """

    evidence = (
        safe_mapping(local_execution_evidence)
        if local_execution_evidence is not None
        else build_p7_hold004_group02_local_execution_evidence()
    )
    assert_p7_hold004_group02_local_execution_evidence_contract(evidence)
    final_source_status = _source_identity_status(source_identity_status or evidence.get("source_identity_status"))
    source_accepted = final_source_status == P7_HOLD004_GROUP02_SOURCE_STATUS_ACCEPTED_AFTER_EXPLICIT_LOCAL_RERUN
    official_recording_applied = bool(apply_to_r40_official_recording and source_accepted)

    run_result = _build_group02_pass_run_result_from_evidence(evidence) if official_recording_applied else None
    recording = build_p7_hold004_official_group02_result_recording(run_result=run_result)
    assert_p7_hold004_official_group02_result_recording_contract(recording)
    gate = build_p7_hold004_full_backend_suite_gate(official_group02_result_recording=recording)
    assert_p7_hold004_full_backend_suite_gate_contract(gate)

    recording_status = clean_identifier(recording.get("result_status"), max_length=80)
    group_green = recording_status == P7_HOLD004_GROUP02_RESULT_STATUS_PASSED_ISOLATED
    group_green_scope = (
        P7_HOLD004_GROUP02_RECONCILE_SCOPE_GROUP02_ISOLATED_ONLY
        if group_green
        else P7_HOLD004_GROUP02_RECONCILE_SCOPE_NON_OFFICIAL_LOCAL_EVIDENCE
    )
    followups = dedupe_identifiers(
        [
            "official_group02_source_identity_decision_required" if not source_accepted else "",
            "official_group02_result_recording_not_applied" if not official_recording_applied else "",
            "group_02_green_is_not_full_backend_suite_green" if group_green else "",
            "remaining_backend_groups_official_execution_required",
            "full_backend_suite_green_unconfirmed",
            "current_snapshot_collect_drift_classification_required",
            "p5_human_qa_review_required",
            "p6_human_readfeel_review_required",
            "real_device_submit_modal_readfeel_unverified",
        ],
        limit=120,
        max_length=180,
    )
    material = {
        "schema_version": P7_HOLD004_GROUP02_OFFICIAL_RESULT_RECORDING_RECONCILE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "step": P7_HOLD004_GROUP02_OFFICIAL_RESULT_RECORDING_RECONCILE_STEP,
        "implementation_step": P7_HOLD004_GROUP02_OFFICIAL_RESULT_RECORDING_RECONCILE_STEP,
        "reconcile_id": P7_HOLD004_GROUP02_OFFICIAL_RESULT_RECORDING_RECONCILE_ID,
        "source_mode": P7_SOURCE_MODE,
        "git_checked": P7_GIT_CHECKED,
        "local_execution_evidence_id": clean_identifier(evidence.get("evidence_id"), max_length=180),
        "local_evidence_source_identity_status": clean_identifier(evidence.get("source_identity_status"), max_length=180),
        "source_identity_status": final_source_status,
        "source_identity_accepted_for_official_recording": source_accepted,
        "apply_to_r40_official_recording_requested": bool(apply_to_r40_official_recording),
        "official_recording_applied": official_recording_applied,
        "group02_local_pass_recorded_as_non_official_evidence": not official_recording_applied,
        "observed_execution_source_ref": clean_identifier(evidence.get("observed_execution_source_ref"), max_length=180),
        "active_source_snapshot_ref": clean_identifier(evidence.get("active_source_snapshot_ref"), max_length=180),
        "active_baseline_id": P7_HOLD004_BACKEND_COLLECT_BASELINE_ID,
        "group_id": P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID,
        "batch_id": P7_HOLD004_GROUP02_OFFICIAL_BATCH_ID,
        "r40_default_not_run_preserved": True,
        "r40_explicit_run_result_required_for_passed_isolated": True,
        "r40_recording_id": P7_HOLD004_OFFICIAL_GROUP02_RESULT_RECORDING_ID,
        "r40_full_backend_suite_gate_id": P7_HOLD004_FULL_BACKEND_SUITE_GATE_ID,
        "official_group_02_result_recording_status": recording_status,
        "r40_result_status": recording_status,
        "official_group_02_capture_green_confirmed": group_green,
        "can_claim_group_green": group_green,
        "group_green_scope": group_green_scope,
        "group02_pass_is_not_full_backend_suite_green": True,
        "group02_result_recording_is_not_full_backend_suite_gate": True,
        "group02_result_recording_is_not_release_ready": True,
        "remaining_backend_group_count": _coerce_non_negative_int(gate.get("remaining_backend_group_count"), default=0),
        "remaining_backend_group_count_expected": len(P7_HOLD004_BACKEND_SUITE_GROUP_IDS) - 1
        if official_recording_applied
        else len(P7_HOLD004_BACKEND_SUITE_GROUP_IDS),
        "full_backend_suite_gate_status": clean_identifier(gate.get("full_backend_suite_gate_status"), max_length=180),
        "r40_result_recording_projection": _r40_recording_projection(recording),
        "r40_full_backend_suite_gate_projection": _r40_gate_projection(gate),
        "required_followup_fixes": followups,
        **_release_closed_flags(),
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
        **_body_retention_flags(),
        "body_free": True,
    }
    assert_p7_hold004_group02_official_result_recording_reconcile_contract(material)
    return material


def assert_p7_hold004_group02_official_result_recording_reconcile_contract(material: Mapping[str, Any]) -> bool:
    """Validate R42 official group_02 recording reconcile material."""

    data = safe_mapping(material)
    source = "p7_hold004_r42_group02_official_result_recording_reconcile"
    if data.get("schema_version") != P7_HOLD004_GROUP02_OFFICIAL_RESULT_RECORDING_RECONCILE_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 R42 reconcile schema mismatch")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError("P7-HOLD-004 R42 reconcile phase/hold mismatch")
    if data.get("step") != P7_HOLD004_GROUP02_OFFICIAL_RESULT_RECORDING_RECONCILE_STEP:
        raise ValueError("P7-HOLD-004 R42 reconcile step mismatch")
    if data.get("reconcile_id") != P7_HOLD004_GROUP02_OFFICIAL_RESULT_RECORDING_RECONCILE_ID:
        raise ValueError("P7-HOLD-004 R42 reconcile id mismatch")
    if data.get("source_mode") != P7_SOURCE_MODE or data.get("git_checked") is not P7_GIT_CHECKED:
        raise ValueError("P7-HOLD-004 R42 reconcile source boundary mismatch")
    if data.get("local_execution_evidence_id") != P7_HOLD004_GROUP02_LOCAL_EXECUTION_EVIDENCE_ID:
        raise ValueError("P7-HOLD-004 R42 reconcile local evidence id mismatch")
    if data.get("group_id") != P7_HOLD004_GROUP02_OFFICIAL_GROUP_ID:
        raise ValueError("P7-HOLD-004 R42 reconcile group_id mismatch")
    if data.get("batch_id") != P7_HOLD004_GROUP02_OFFICIAL_BATCH_ID:
        raise ValueError("P7-HOLD-004 R42 reconcile batch_id mismatch")
    if data.get("active_baseline_id") != P7_HOLD004_BACKEND_COLLECT_BASELINE_ID:
        raise ValueError("P7-HOLD-004 R42 reconcile active baseline id mismatch")
    if data.get("active_source_snapshot_ref") != P7_HOLD004_BACKEND_SOURCE_SNAPSHOT_REF:
        raise ValueError("P7-HOLD-004 R42 reconcile active source ref mismatch")
    status = clean_identifier(data.get("source_identity_status"), max_length=180)
    if status not in P7_HOLD004_GROUP02_SOURCE_IDENTITY_STATUSES:
        raise ValueError("P7-HOLD-004 R42 reconcile source identity status mismatch")
    source_accepted = status == P7_HOLD004_GROUP02_SOURCE_STATUS_ACCEPTED_AFTER_EXPLICIT_LOCAL_RERUN
    if data.get("source_identity_accepted_for_official_recording") is not source_accepted:
        raise ValueError("P7-HOLD-004 R42 reconcile source accepted flag mismatch")
    if data.get("r40_default_not_run_preserved") is not True:
        raise ValueError("P7-HOLD-004 R42 reconcile must preserve R40 default NOT_RUN")
    if data.get("r40_explicit_run_result_required_for_passed_isolated") is not True:
        raise ValueError("P7-HOLD-004 R42 reconcile must require explicit R40 run_result")
    if data.get("r40_recording_id") != P7_HOLD004_OFFICIAL_GROUP02_RESULT_RECORDING_ID:
        raise ValueError("P7-HOLD-004 R42 reconcile R40 recording id mismatch")
    if data.get("r40_full_backend_suite_gate_id") != P7_HOLD004_FULL_BACKEND_SUITE_GATE_ID:
        raise ValueError("P7-HOLD-004 R42 reconcile R40 full gate id mismatch")

    applied = data.get("official_recording_applied") is True
    requested = data.get("apply_to_r40_official_recording_requested") is True
    result_status = clean_identifier(data.get("official_group_02_result_recording_status"), max_length=80)
    if data.get("r40_result_status") != result_status:
        raise ValueError("P7-HOLD-004 R42 reconcile R40 result status alias mismatch")
    if applied and not (requested and source_accepted):
        raise ValueError("P7-HOLD-004 R42 reconcile applied without explicit accepted source decision")
    if applied and result_status != P7_HOLD004_GROUP02_RESULT_STATUS_PASSED_ISOLATED:
        raise ValueError("P7-HOLD-004 R42 reconcile applied state must be PASSED_ISOLATED")
    if not applied and result_status != P7_HOLD004_GROUP02_RESULT_STATUS_NOT_RUN:
        raise ValueError("P7-HOLD-004 R42 reconcile non-applied state must keep R40 NOT_RUN")
    group_green = result_status == P7_HOLD004_GROUP02_RESULT_STATUS_PASSED_ISOLATED
    if data.get("official_group_02_capture_green_confirmed") is not group_green:
        raise ValueError("P7-HOLD-004 R42 reconcile group green flag mismatch")
    if data.get("can_claim_group_green") is not group_green:
        raise ValueError("P7-HOLD-004 R42 reconcile group green claim mismatch")
    expected_scope = (
        P7_HOLD004_GROUP02_RECONCILE_SCOPE_GROUP02_ISOLATED_ONLY
        if group_green
        else P7_HOLD004_GROUP02_RECONCILE_SCOPE_NON_OFFICIAL_LOCAL_EVIDENCE
    )
    if data.get("group_green_scope") != expected_scope:
        raise ValueError("P7-HOLD-004 R42 reconcile group scope mismatch")
    if data.get("group02_local_pass_recorded_as_non_official_evidence") is not (not applied):
        raise ValueError("P7-HOLD-004 R42 reconcile non-official local evidence flag mismatch")
    if data.get("group02_pass_is_not_full_backend_suite_green") is not True:
        raise ValueError("P7-HOLD-004 R42 reconcile group_02 pass must not be full suite green")
    if data.get("group02_result_recording_is_not_full_backend_suite_gate") is not True:
        raise ValueError("P7-HOLD-004 R42 reconcile must separate result recording from full suite gate")
    if data.get("group02_result_recording_is_not_release_ready") is not True:
        raise ValueError("P7-HOLD-004 R42 reconcile must not become release ready")
    if data.get("full_backend_suite_gate_status") != P7_HOLD004_FULL_BACKEND_SUITE_GATE_STATUS_BLOCKED_REMAINING_GROUPS:
        raise ValueError("P7-HOLD-004 R42 reconcile full suite gate status mismatch")
    expected_remaining = len(P7_HOLD004_BACKEND_SUITE_GROUP_IDS) - 1 if applied else len(P7_HOLD004_BACKEND_SUITE_GROUP_IDS)
    if data.get("remaining_backend_group_count") != expected_remaining:
        raise ValueError("P7-HOLD-004 R42 reconcile remaining group count mismatch")
    if data.get("remaining_backend_group_count_expected") != expected_remaining:
        raise ValueError("P7-HOLD-004 R42 reconcile expected remaining group count mismatch")

    recording_projection = safe_mapping(data.get("r40_result_recording_projection"))
    if recording_projection.get("result_status") != result_status:
        raise ValueError("P7-HOLD-004 R42 reconcile recording projection status mismatch")
    if recording_projection.get("can_claim_full_backend_suite_green") is not False:
        raise ValueError("P7-HOLD-004 R42 reconcile recording projection must not claim full suite green")
    if recording_projection.get("full_backend_suite_green_confirmed") is not False:
        raise ValueError("P7-HOLD-004 R42 reconcile recording projection must keep full suite green false")
    gate_projection = safe_mapping(data.get("r40_full_backend_suite_gate_projection"))
    if gate_projection.get("full_backend_suite_green_confirmed") is not False:
        raise ValueError("P7-HOLD-004 R42 reconcile gate projection must keep full suite green false")
    if gate_projection.get("can_claim_full_backend_suite_green") is not False:
        raise ValueError("P7-HOLD-004 R42 reconcile gate projection must not claim full suite green")
    if gate_projection.get("hold004_close_allowed") is not False:
        raise ValueError("P7-HOLD-004 R42 reconcile gate projection must not close HOLD-004")
    if gate_projection.get("p7_complete") is not False or gate_projection.get("p8_start_allowed") is not False:
        raise ValueError("P7-HOLD-004 R42 reconcile gate projection must not complete P7/P8")
    if gate_projection.get("release_allowed") is not False:
        raise ValueError("P7-HOLD-004 R42 reconcile gate projection must keep release false")

    followups = set(dedupe_identifiers(data.get("required_followup_fixes"), limit=120, max_length=180))
    for required in (
        "remaining_backend_groups_official_execution_required",
        "full_backend_suite_green_unconfirmed",
        "current_snapshot_collect_drift_classification_required",
        "p5_human_qa_review_required",
        "p6_human_readfeel_review_required",
        "real_device_submit_modal_readfeel_unverified",
    ):
        if required not in followups:
            raise ValueError(f"P7-HOLD-004 R42 reconcile missing followup {required}")
    if not source_accepted and "official_group02_source_identity_decision_required" not in followups:
        raise ValueError("P7-HOLD-004 R42 reconcile must keep source identity followup until accepted")
    if applied and "group_02_green_is_not_full_backend_suite_green" not in followups:
        raise ValueError("P7-HOLD-004 R42 reconcile applied pass must keep isolated green followup")
    _assert_release_closed_and_body_free(data, source=source)
    return True



def _clean_sha256(value: Any, *, default: str = "") -> str:
    digest = clean_identifier(value, default=default, max_length=_SHA256_HEX_LENGTH)
    if len(digest) != _SHA256_HEX_LENGTH:
        return default
    try:
        int(digest, 16)
    except ValueError:
        return default
    return digest


def _current_working_snapshot_collect(
    *,
    files: Any = P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECTED_TEST_FILE_COUNT,
    tests: Any = P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECTED_TEST_ITEM_COUNT,
    warnings: Any = P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_WARNINGS_COUNT,
    items_sha256: Any = P7_HOLD004_CURRENT_WORKING_SNAPSHOT_TEST_ITEMS_SHA256,
    files_sha256: Any = P7_HOLD004_CURRENT_WORKING_SNAPSHOT_TEST_FILES_SHA256,
) -> dict[str, Any]:
    return {
        "files": _coerce_non_negative_int(files),
        "tests": _coerce_non_negative_int(tests),
        "warnings": _coerce_non_negative_int(warnings),
        "items_sha256": _clean_sha256(
            items_sha256,
            default=P7_HOLD004_CURRENT_WORKING_SNAPSHOT_TEST_ITEMS_SHA256,
        ),
        "files_sha256": _clean_sha256(
            files_sha256,
            default=P7_HOLD004_CURRENT_WORKING_SNAPSHOT_TEST_FILES_SHA256,
        ),
    }


def _active_baseline_collect() -> dict[str, Any]:
    return {
        "files": P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT,
        "tests": P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT,
        "warnings": P7_HOLD004_BACKEND_COLLECT_WARNINGS_COUNT,
        "items_sha256": P7_HOLD004_BACKEND_TEST_ITEMS_SHA256,
        "files_sha256": P7_HOLD004_BACKEND_TEST_FILES_SHA256,
    }


def _collect_delta(current: Mapping[str, Any], active: Mapping[str, Any]) -> dict[str, int]:
    current_map = safe_mapping(current)
    active_map = safe_mapping(active)
    return {
        "files": _coerce_non_negative_int(current_map.get("files"))
        - _coerce_non_negative_int(active_map.get("files")),
        "tests": _coerce_non_negative_int(current_map.get("tests"))
        - _coerce_non_negative_int(active_map.get("tests")),
        "warnings": _coerce_non_negative_int(current_map.get("warnings"))
        - _coerce_non_negative_int(active_map.get("warnings")),
    }


def _snapshot_drift_status(value: Any) -> str:
    status = clean_identifier(
        value,
        default=P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DRIFT_STATUS_UNCLASSIFIED,
        max_length=180,
    )
    return (
        status
        if status in P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DRIFT_CLASSIFICATION_STATUSES
        else P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DRIFT_STATUS_UNCLASSIFIED
    )


def _normalize_added_test_file_refs(value: Iterable[Any] | Any | None) -> list[str]:
    return dedupe_identifiers(value, limit=30, max_length=220)


def _added_test_refs_match_expected(refs: Iterable[str]) -> bool:
    return tuple(refs) == P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_FILE_REFS


def build_p7_hold004_current_working_snapshot_collect_drift_evidence(
    *,
    current_files: Any = P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECTED_TEST_FILE_COUNT,
    current_tests: Any = P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECTED_TEST_ITEM_COUNT,
    current_warnings: Any = P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_WARNINGS_COUNT,
    current_items_sha256: Any = P7_HOLD004_CURRENT_WORKING_SNAPSHOT_TEST_ITEMS_SHA256,
    current_files_sha256: Any = P7_HOLD004_CURRENT_WORKING_SNAPSHOT_TEST_FILES_SHA256,
    current_working_snapshot_ref: str = P7_HOLD004_CURRENT_WORKING_SNAPSHOT_REF,
) -> dict[str, Any]:
    """Freeze the R43 current working snapshot collect-only drift evidence."""

    current_collect = _current_working_snapshot_collect(
        files=current_files,
        tests=current_tests,
        warnings=current_warnings,
        items_sha256=current_items_sha256,
        files_sha256=current_files_sha256,
    )
    active_collect = _active_baseline_collect()
    delta = _collect_delta(current_collect, active_collect)
    material = {
        "schema_version": P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_DRIFT_EVIDENCE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "step": P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_DRIFT_EVIDENCE_STEP,
        "implementation_step": P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_DRIFT_EVIDENCE_STEP,
        "evidence_id": P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_DRIFT_EVIDENCE_ID,
        "source_mode": P7_SOURCE_MODE,
        "git_checked": P7_GIT_CHECKED,
        "current_working_snapshot_ref": clean_identifier(
            current_working_snapshot_ref,
            default=P7_HOLD004_CURRENT_WORKING_SNAPSHOT_REF,
            max_length=180,
        ),
        "active_source_snapshot_ref": P7_HOLD004_BACKEND_SOURCE_SNAPSHOT_REF,
        "active_baseline_id": P7_HOLD004_BACKEND_COLLECT_BASELINE_ID,
        "collect_scope": P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_SCOPE,
        "collect_command_id": P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_COMMAND_ID,
        "fingerprint_algorithm": P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM,
        "current_collect_only": current_collect,
        "active_baseline_collect": active_collect,
        "delta": delta,
        "current_collect_only_recorded": True,
        "active_baseline_differs_from_current_collect": current_collect != active_collect,
        "collect_only_is_not_execution_green": True,
        "current_collect_is_not_full_backend_suite_green": True,
        "current_collect_is_not_official_backend_execution": True,
        "active_baseline_update_allowed": False,
        "active_baseline_update_applied": False,
        "current_snapshot_baseline_adoption_allowed": False,
        "full_backend_execution_result_recorded": False,
        "full_backend_suite_execution_green_confirmed": False,
        **_release_closed_flags(),
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
        **_body_retention_flags(),
        "body_free": True,
    }
    assert_p7_hold004_current_working_snapshot_collect_drift_evidence_contract(material)
    return material


def assert_p7_hold004_current_working_snapshot_collect_drift_evidence_contract(
    material: Mapping[str, Any],
) -> bool:
    """Validate R43 current collect drift without turning it into execution green."""

    data = safe_mapping(material)
    source = "p7_hold004_r43_current_working_snapshot_collect_drift_evidence"
    if data.get("schema_version") != P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_DRIFT_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 R43 current collect drift evidence schema mismatch")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError("P7-HOLD-004 R43 current collect drift evidence phase/hold mismatch")
    if data.get("step") != P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_DRIFT_EVIDENCE_STEP:
        raise ValueError("P7-HOLD-004 R43 current collect drift evidence step mismatch")
    if data.get("evidence_id") != P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_DRIFT_EVIDENCE_ID:
        raise ValueError("P7-HOLD-004 R43 current collect drift evidence id mismatch")
    if data.get("source_mode") != P7_SOURCE_MODE or data.get("git_checked") is not P7_GIT_CHECKED:
        raise ValueError("P7-HOLD-004 R43 current collect drift source boundary mismatch")
    if not clean_identifier(data.get("current_working_snapshot_ref"), max_length=180):
        raise ValueError("P7-HOLD-004 R43 current working snapshot ref required")
    if data.get("active_source_snapshot_ref") != P7_HOLD004_BACKEND_SOURCE_SNAPSHOT_REF:
        raise ValueError("P7-HOLD-004 R43 active source snapshot ref mismatch")
    if data.get("active_baseline_id") != P7_HOLD004_BACKEND_COLLECT_BASELINE_ID:
        raise ValueError("P7-HOLD-004 R43 active baseline id mismatch")
    if data.get("collect_scope") != P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_SCOPE:
        raise ValueError("P7-HOLD-004 R43 collect scope mismatch")
    if data.get("collect_command_id") != P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_COMMAND_ID:
        raise ValueError("P7-HOLD-004 R43 collect command mismatch")
    if data.get("fingerprint_algorithm") != P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM:
        raise ValueError("P7-HOLD-004 R43 fingerprint algorithm mismatch")

    current_collect = safe_mapping(data.get("current_collect_only"))
    active_collect = safe_mapping(data.get("active_baseline_collect"))
    expected_current = _current_working_snapshot_collect()
    expected_active = _active_baseline_collect()
    if current_collect != expected_current:
        raise ValueError("P7-HOLD-004 R43 current collect values must stay frozen at 432/2892/1")
    if active_collect != expected_active:
        raise ValueError("P7-HOLD-004 R43 active baseline collect values mismatch")
    expected_delta = _collect_delta(expected_current, expected_active)
    if safe_mapping(data.get("delta")) != expected_delta:
        raise ValueError("P7-HOLD-004 R43 current collect delta mismatch")
    if data.get("current_collect_only_recorded") is not True:
        raise ValueError("P7-HOLD-004 R43 must record current collect-only evidence")
    if data.get("active_baseline_differs_from_current_collect") is not True:
        raise ValueError("P7-HOLD-004 R43 must record active/current drift")
    for key in (
        "collect_only_is_not_execution_green",
        "current_collect_is_not_full_backend_suite_green",
        "current_collect_is_not_official_backend_execution",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 R43 must keep {key}=true")
    for key in (
        "active_baseline_update_allowed",
        "active_baseline_update_applied",
        "current_snapshot_baseline_adoption_allowed",
        "full_backend_execution_result_recorded",
        "full_backend_suite_execution_green_confirmed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 R43 must keep {key}=false")
    _assert_release_closed_and_body_free(data, source=source)
    return True


def build_p7_hold004_active_baseline_current_snapshot_drift_classification(
    *,
    collect_drift_evidence: Mapping[str, Any] | None = None,
    added_test_file_refs: Iterable[Any] | None = None,
    added_test_item_count: Any | None = None,
    classification_status: str = P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DRIFT_STATUS_UNCLASSIFIED,
) -> dict[str, Any]:
    """Classify R44 active-baseline/current-snapshot drift without adopting it."""

    evidence = dict(
        collect_drift_evidence
        if collect_drift_evidence is not None
        else build_p7_hold004_current_working_snapshot_collect_drift_evidence()
    )
    assert_p7_hold004_current_working_snapshot_collect_drift_evidence_contract(evidence)
    status = _snapshot_drift_status(classification_status)
    refs = _normalize_added_test_file_refs(added_test_file_refs)
    normalized_item_count = _coerce_non_negative_int(added_test_item_count, default=0)
    positive_status = status == P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DRIFT_STATUS_R30_R42_TEST_ADDITION_ACCEPTED
    refs_match = _added_test_refs_match_expected(refs)
    count_matches = normalized_item_count == P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_ITEM_COUNT
    delta = safe_mapping(evidence.get("delta"))
    delta_matches = (
        delta.get("files") == P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DELTA_TEST_FILE_COUNT
        and delta.get("tests") == P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DELTA_TEST_ITEM_COUNT
        and delta.get("warnings") == P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DELTA_WARNINGS_COUNT
    )
    material = {
        "schema_version": P7_HOLD004_ACTIVE_BASELINE_CURRENT_SNAPSHOT_DRIFT_CLASSIFICATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "step": P7_HOLD004_ACTIVE_BASELINE_CURRENT_SNAPSHOT_DRIFT_CLASSIFICATION_STEP,
        "implementation_step": P7_HOLD004_ACTIVE_BASELINE_CURRENT_SNAPSHOT_DRIFT_CLASSIFICATION_STEP,
        "classification_id": P7_HOLD004_ACTIVE_BASELINE_CURRENT_SNAPSHOT_DRIFT_CLASSIFICATION_ID,
        "source_mode": P7_SOURCE_MODE,
        "git_checked": P7_GIT_CHECKED,
        "input_evidence_id": P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_DRIFT_EVIDENCE_ID,
        "current_working_snapshot_ref": evidence.get("current_working_snapshot_ref"),
        "active_source_snapshot_ref": P7_HOLD004_BACKEND_SOURCE_SNAPSHOT_REF,
        "active_baseline_id": P7_HOLD004_BACKEND_COLLECT_BASELINE_ID,
        "classification_status": status,
        "default_status_if_unverified": P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DRIFT_STATUS_UNCLASSIFIED,
        "current_collect_only": dict(safe_mapping(evidence.get("current_collect_only"))),
        "active_baseline_collect": dict(safe_mapping(evidence.get("active_baseline_collect"))),
        "delta": dict(delta),
        "added_test_file_refs": refs,
        "added_test_file_count": len(refs),
        "added_test_item_count": normalized_item_count,
        "expected_added_test_file_refs": list(P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_FILE_REFS),
        "expected_added_test_file_count": P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_FILE_COUNT,
        "expected_added_test_item_count": P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_ITEM_COUNT,
        "added_test_refs_match_expected": refs_match,
        "added_test_item_count_matches_expected": count_matches,
        "collect_delta_matches_added_contract_tests": delta_matches,
        "drift_classified": positive_status,
        "added_file_refs_are_contract_tests_only": positive_status and refs_match,
        "classification_is_current_working_snapshot_only": positive_status,
        "collect_only_is_not_execution_green": True,
        "classification_is_not_full_backend_suite_green": True,
        "classification_is_not_active_baseline_adoption": True,
        "classification_is_not_release_permission": True,
        "semantic_no_change_claimed": False,
        "production_runtime_source_change_claimed": False,
        "active_baseline_update_allowed": False,
        "active_baseline_update_applied": False,
        "current_snapshot_baseline_adoption_allowed": False,
        "group03_execution_allowed_by_this_classification": False,
        **_release_closed_flags(),
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
        **_body_retention_flags(),
        "body_free": True,
    }
    assert_p7_hold004_active_baseline_current_snapshot_drift_classification_contract(material)
    return material


def assert_p7_hold004_active_baseline_current_snapshot_drift_classification_contract(
    material: Mapping[str, Any],
) -> bool:
    """Validate R44 drift classification without adopting a new baseline."""

    data = safe_mapping(material)
    source = "p7_hold004_r44_active_baseline_current_snapshot_drift_classification"
    if data.get("schema_version") != P7_HOLD004_ACTIVE_BASELINE_CURRENT_SNAPSHOT_DRIFT_CLASSIFICATION_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 R44 drift classification schema mismatch")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError("P7-HOLD-004 R44 drift classification phase/hold mismatch")
    if data.get("step") != P7_HOLD004_ACTIVE_BASELINE_CURRENT_SNAPSHOT_DRIFT_CLASSIFICATION_STEP:
        raise ValueError("P7-HOLD-004 R44 drift classification step mismatch")
    if data.get("classification_id") != P7_HOLD004_ACTIVE_BASELINE_CURRENT_SNAPSHOT_DRIFT_CLASSIFICATION_ID:
        raise ValueError("P7-HOLD-004 R44 drift classification id mismatch")
    if data.get("source_mode") != P7_SOURCE_MODE or data.get("git_checked") is not P7_GIT_CHECKED:
        raise ValueError("P7-HOLD-004 R44 drift classification source boundary mismatch")
    if data.get("input_evidence_id") != P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_DRIFT_EVIDENCE_ID:
        raise ValueError("P7-HOLD-004 R44 input evidence id mismatch")
    if data.get("active_source_snapshot_ref") != P7_HOLD004_BACKEND_SOURCE_SNAPSHOT_REF:
        raise ValueError("P7-HOLD-004 R44 active source ref mismatch")
    if data.get("active_baseline_id") != P7_HOLD004_BACKEND_COLLECT_BASELINE_ID:
        raise ValueError("P7-HOLD-004 R44 active baseline id mismatch")
    status = _snapshot_drift_status(data.get("classification_status"))
    if data.get("classification_status") != status:
        raise ValueError("P7-HOLD-004 R44 drift classification status mismatch")
    if data.get("default_status_if_unverified") != P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DRIFT_STATUS_UNCLASSIFIED:
        raise ValueError("P7-HOLD-004 R44 default unverified status mismatch")
    current_collect = safe_mapping(data.get("current_collect_only"))
    active_collect = safe_mapping(data.get("active_baseline_collect"))
    if current_collect != _current_working_snapshot_collect():
        raise ValueError("P7-HOLD-004 R44 current collect values mismatch")
    if active_collect != _active_baseline_collect():
        raise ValueError("P7-HOLD-004 R44 active baseline collect values mismatch")
    if safe_mapping(data.get("delta")) != _collect_delta(_current_working_snapshot_collect(), _active_baseline_collect()):
        raise ValueError("P7-HOLD-004 R44 collect delta mismatch")

    refs = _normalize_added_test_file_refs(data.get("added_test_file_refs"))
    if data.get("added_test_file_count") != len(refs):
        raise ValueError("P7-HOLD-004 R44 added test file count mismatch")
    if data.get("expected_added_test_file_refs") != list(P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_FILE_REFS):
        raise ValueError("P7-HOLD-004 R44 expected added file refs mismatch")
    if data.get("expected_added_test_file_count") != P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_FILE_COUNT:
        raise ValueError("P7-HOLD-004 R44 expected added file count mismatch")
    if data.get("expected_added_test_item_count") != P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_ITEM_COUNT:
        raise ValueError("P7-HOLD-004 R44 expected added item count mismatch")
    refs_match = _added_test_refs_match_expected(refs)
    item_count = _coerce_non_negative_int(data.get("added_test_item_count"))
    item_count_matches = item_count == P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_ITEM_COUNT
    delta = safe_mapping(data.get("delta"))
    delta_matches = (
        delta.get("files") == P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DELTA_TEST_FILE_COUNT
        and delta.get("tests") == P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DELTA_TEST_ITEM_COUNT
        and delta.get("warnings") == P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DELTA_WARNINGS_COUNT
    )
    if data.get("added_test_refs_match_expected") is not refs_match:
        raise ValueError("P7-HOLD-004 R44 added refs match flag mismatch")
    if data.get("added_test_item_count_matches_expected") is not item_count_matches:
        raise ValueError("P7-HOLD-004 R44 added item count match flag mismatch")
    if data.get("collect_delta_matches_added_contract_tests") is not delta_matches:
        raise ValueError("P7-HOLD-004 R44 delta match flag mismatch")

    positive_status = status == P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DRIFT_STATUS_R30_R42_TEST_ADDITION_ACCEPTED
    if data.get("drift_classified") is not positive_status:
        raise ValueError("P7-HOLD-004 R44 drift classified flag mismatch")
    if positive_status:
        if not (refs_match and item_count_matches and delta_matches):
            raise ValueError("P7-HOLD-004 R44 positive classification requires exact 7 file refs / 36 items / matching delta")
        if data.get("added_file_refs_are_contract_tests_only") is not True:
            raise ValueError("P7-HOLD-004 R44 positive classification must be contract-test-only")
        if data.get("classification_is_current_working_snapshot_only") is not True:
            raise ValueError("P7-HOLD-004 R44 positive classification must stay current snapshot only")
    else:
        if data.get("classification_is_current_working_snapshot_only") is not False:
            raise ValueError("P7-HOLD-004 R44 default classification must not claim accepted current snapshot status")
        if data.get("added_file_refs_are_contract_tests_only") is not False:
            raise ValueError("P7-HOLD-004 R44 default classification must not claim contract-test-only proof")

    for key in (
        "collect_only_is_not_execution_green",
        "classification_is_not_full_backend_suite_green",
        "classification_is_not_active_baseline_adoption",
        "classification_is_not_release_permission",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 R44 must keep {key}=true")
    for key in (
        "semantic_no_change_claimed",
        "production_runtime_source_change_claimed",
        "active_baseline_update_allowed",
        "active_baseline_update_applied",
        "current_snapshot_baseline_adoption_allowed",
        "group03_execution_allowed_by_this_classification",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 R44 must keep {key}=false")
    _assert_release_closed_and_body_free(data, source=source)
    return True

def _default_source_accepted_group02_reconcile() -> dict[str, Any]:
    evidence = build_p7_hold004_group02_local_execution_evidence(
        source_identity_status=P7_HOLD004_GROUP02_SOURCE_STATUS_ACCEPTED_AFTER_EXPLICIT_LOCAL_RERUN,
    )
    return build_p7_hold004_group02_official_result_recording_reconcile(
        local_execution_evidence=evidence,
        source_identity_status=P7_HOLD004_GROUP02_SOURCE_STATUS_ACCEPTED_AFTER_EXPLICIT_LOCAL_RERUN,
        apply_to_r40_official_recording=True,
    )


def _default_positive_current_snapshot_drift_classification() -> dict[str, Any]:
    return build_p7_hold004_active_baseline_current_snapshot_drift_classification(
        added_test_file_refs=P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_FILE_REFS,
        added_test_item_count=P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_ITEM_COUNT,
        classification_status=P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DRIFT_STATUS_R30_R42_TEST_ADDITION_ACCEPTED,
    )


def _p7_hold004_projection_followups() -> list[str]:
    return dedupe_identifiers(
        (
            "remaining_backend_groups_official_execution_required",
            "full_backend_suite_green_unconfirmed",
            "p7_hold004_closure_unconfirmed",
            "p5_human_qa_review_required",
            "p6_human_readfeel_review_required",
            "real_device_submit_modal_readfeel_unverified",
            "p5_p6_human_readfeel_return_recommended",
            "backend_group03_not_auto_continued_by_r45_r46",
        ),
        limit=120,
        max_length=180,
    )


def build_p7_hold004_group02_current_snapshot_release_projection(
    *,
    group02_reconcile: Mapping[str, Any] | None = None,
    drift_classification: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Project R41-R44 into matrix/release/validation material without release promotion.

    The default projection uses the explicit R42 source-accepted wrapper and the
    R44 current-working-snapshot-only classification. It still keeps release,
    P7 completion, P8 start, active-baseline adoption, and backend group auto-
    continuation closed.
    """

    group02 = safe_mapping(group02_reconcile) if group02_reconcile is not None else _default_source_accepted_group02_reconcile()
    assert_p7_hold004_group02_official_result_recording_reconcile_contract(group02)
    drift = (
        safe_mapping(drift_classification)
        if drift_classification is not None
        else _default_positive_current_snapshot_drift_classification()
    )
    assert_p7_hold004_active_baseline_current_snapshot_drift_classification_contract(drift)

    group02_status = clean_identifier(
        group02.get("official_group_02_result_recording_status"),
        default=P7_HOLD004_GROUP02_RESULT_STATUS_NOT_RUN,
        max_length=80,
    )
    group02_scope = clean_identifier(
        group02.get("group_green_scope"),
        default=P7_HOLD004_GROUP02_RECONCILE_SCOPE_NON_OFFICIAL_LOCAL_EVIDENCE,
        max_length=120,
    )
    group02_pass_is_isolated = (
        group02_status == P7_HOLD004_GROUP02_RESULT_STATUS_PASSED_ISOLATED
        and group02_scope == P7_HOLD004_GROUP02_RECONCILE_SCOPE_GROUP02_ISOLATED_ONLY
        and group02.get("official_recording_applied") is True
    )
    drift_status = _snapshot_drift_status(drift.get("classification_status"))
    drift_classified = drift.get("drift_classified") is True
    followups = _p7_hold004_projection_followups()

    material = {
        "schema_version": P7_HOLD004_GROUP02_CURRENT_SNAPSHOT_RELEASE_PROJECTION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "step": P7_HOLD004_GROUP02_CURRENT_SNAPSHOT_RELEASE_PROJECTION_STEP,
        "implementation_step": P7_HOLD004_GROUP02_CURRENT_SNAPSHOT_RELEASE_PROJECTION_STEP,
        "projection_id": P7_HOLD004_GROUP02_CURRENT_SNAPSHOT_RELEASE_PROJECTION_ID,
        "projection_status": P7_HOLD004_GROUP02_CURRENT_SNAPSHOT_RELEASE_PROJECTION_STATUS,
        "source_mode": P7_SOURCE_MODE,
        "git_checked": P7_GIT_CHECKED,
        "p7_hold004_group02_local_execution_evidence_id": clean_identifier(
            group02.get("local_execution_evidence_id"),
            max_length=180,
        ),
        "p7_hold004_group02_official_recording_reconcile_id": clean_identifier(
            group02.get("reconcile_id"),
            max_length=180,
        ),
        "p7_hold004_group02_result_recording_status": group02_status,
        "group02_result_recording_status": group02_status,
        "p7_hold004_group02_result_scope": group02_scope,
        "group02_result_scope": group02_scope,
        "p7_hold004_group02_pass_is_isolated": group02_pass_is_isolated,
        "group02_pass_is_isolated": group02_pass_is_isolated,
        "p7_hold004_group02_pass_is_not_full_backend_suite_green": True,
        "group02_pass_is_not_full_backend_suite_green": True,
        "group02_result_recording_is_not_release_permission": True,
        "group02_result_recording_is_not_p7_completion": True,
        "p7_hold004_current_working_snapshot_collect_drift_evidence_id": clean_identifier(
            drift.get("input_evidence_id"),
            max_length=180,
        ),
        "p7_hold004_active_baseline_current_snapshot_drift_classification_id": clean_identifier(
            drift.get("classification_id"),
            max_length=180,
        ),
        "p7_hold004_active_baseline_current_snapshot_drift_classification_status": drift_status,
        "current_snapshot_collect_drift_status": drift_status,
        "current_snapshot_collect_drift_classified": drift_classified,
        "current_snapshot_drift_is_current_working_snapshot_only": drift.get(
            "classification_is_current_working_snapshot_only"
        )
        is True,
        "current_snapshot_collect_is_not_execution_green": True,
        "current_snapshot_collect_is_not_full_backend_suite_green": True,
        "current_snapshot_baseline_adoption_allowed": False,
        "current_snapshot_baseline_adoption_applied": False,
        "active_baseline_update_allowed": False,
        "active_baseline_update_applied": False,
        "matrix_projection": {
            "projection_scope": P7_HOLD004_GROUP02_VALIDATION_SCOPE_ISOLATED_NOT_FULL_SUITE,
            "group02_isolated_result_projected": group02_pass_is_isolated,
            "current_snapshot_collect_drift_projected": drift_classified,
            "p7_hold004_remaining": True,
            "p7_complete": False,
            "p8_start_allowed": False,
            "release_allowed": False,
            "body_free": True,
        },
        "release_handoff_projection": {
            "projection_scope": "p7_hold004_release_closed_projection_only",
            "full_backend_suite_green_confirmed": False,
            "full_backend_suite_green_claim_allowed": False,
            "can_claim_full_backend_suite_green": False,
            "hold004_close_allowed": False,
            "p7_complete": False,
            "p8_start_allowed": False,
            "release_allowed": False,
            "body_free": True,
        },
        "validation_projection": {
            "validation_scope": P7_HOLD004_GROUP02_VALIDATION_SCOPE_ISOLATED_NOT_FULL_SUITE,
            "group02_isolated_result_recorded": group02_pass_is_isolated,
            "current_snapshot_collect_drift_classified": drift_classified,
            "p5_human_qa_review_required": True,
            "p6_human_readfeel_review_required": True,
            "real_device_submit_modal_readfeel_unverified": True,
            "full_backend_suite_green_confirmed": False,
            "release_allowed": False,
            "body_free": True,
        },
        "hold_matrix_projection": {
            "p7_hold001_remaining": True,
            "p7_hold002_remaining": True,
            "p7_hold003_remaining": True,
            "p7_hold004_remaining": True,
            "p7_hold004_closed": False,
            "hold004_close_allowed": False,
            "body_free": True,
        },
        "backend_remaining_groups_official_execution_required": True,
        "backend_group03_execution_allowed_by_this_projection": False,
        "backend_group03_execution_permanently_forbidden": False,
        "backend_group03_execution_required_later": True,
        "p5_human_qa_review_required": True,
        "p6_human_readfeel_review_required": True,
        "real_device_submit_modal_readfeel_unverified": True,
        "p7_hold004_closed": False,
        "p7_hold004_remaining": True,
        "projection_is_not_release_permission": True,
        "projection_is_not_p7_completion": True,
        "projection_is_not_p8_start_permission": True,
        "p5_p6_return_recommended": True,
        "p7_hold004_next_p5_p6_return_recommended": True,
        "required_followup_fixes": followups,
        **_release_closed_flags(),
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
        **_body_retention_flags(),
        "body_free": True,
    }
    assert_p7_hold004_group02_current_snapshot_release_projection_contract(material)
    return material


def assert_p7_hold004_group02_current_snapshot_release_projection_contract(
    material: Mapping[str, Any],
) -> bool:
    """Validate R45 projection while keeping release/P7/P8 closed."""

    data = safe_mapping(material)
    source = "p7_hold004_r45_group02_current_snapshot_release_projection"
    if data.get("schema_version") != P7_HOLD004_GROUP02_CURRENT_SNAPSHOT_RELEASE_PROJECTION_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 R45 release projection schema mismatch")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError("P7-HOLD-004 R45 release projection phase/hold mismatch")
    if data.get("step") != P7_HOLD004_GROUP02_CURRENT_SNAPSHOT_RELEASE_PROJECTION_STEP:
        raise ValueError("P7-HOLD-004 R45 release projection step mismatch")
    if data.get("projection_id") != P7_HOLD004_GROUP02_CURRENT_SNAPSHOT_RELEASE_PROJECTION_ID:
        raise ValueError("P7-HOLD-004 R45 release projection id mismatch")
    if data.get("projection_status") != P7_HOLD004_GROUP02_CURRENT_SNAPSHOT_RELEASE_PROJECTION_STATUS:
        raise ValueError("P7-HOLD-004 R45 release projection status mismatch")
    if data.get("source_mode") != P7_SOURCE_MODE or data.get("git_checked") is not P7_GIT_CHECKED:
        raise ValueError("P7-HOLD-004 R45 release projection source boundary mismatch")
    if data.get("p7_hold004_group02_official_recording_reconcile_id") != (
        P7_HOLD004_GROUP02_OFFICIAL_RESULT_RECORDING_RECONCILE_ID
    ):
        raise ValueError("P7-HOLD-004 R45 release projection group02 reconcile id mismatch")
    if data.get("p7_hold004_group02_local_execution_evidence_id") != P7_HOLD004_GROUP02_LOCAL_EXECUTION_EVIDENCE_ID:
        raise ValueError("P7-HOLD-004 R45 release projection local evidence id mismatch")

    group02_status = clean_identifier(data.get("group02_result_recording_status"), max_length=80)
    if group02_status != P7_HOLD004_GROUP02_RESULT_STATUS_PASSED_ISOLATED:
        raise ValueError("P7-HOLD-004 R45 requires group_02 PASSED_ISOLATED projection")
    if data.get("p7_hold004_group02_result_recording_status") != group02_status:
        raise ValueError("P7-HOLD-004 R45 group02 status alias mismatch")
    group02_scope = clean_identifier(data.get("group02_result_scope"), max_length=120)
    if group02_scope != P7_HOLD004_GROUP02_RECONCILE_SCOPE_GROUP02_ISOLATED_ONLY:
        raise ValueError("P7-HOLD-004 R45 group02 scope must be isolated only")
    if data.get("p7_hold004_group02_result_scope") != group02_scope:
        raise ValueError("P7-HOLD-004 R45 group02 scope alias mismatch")
    for key in (
        "p7_hold004_group02_pass_is_isolated",
        "group02_pass_is_isolated",
        "p7_hold004_group02_pass_is_not_full_backend_suite_green",
        "group02_pass_is_not_full_backend_suite_green",
        "group02_result_recording_is_not_release_permission",
        "group02_result_recording_is_not_p7_completion",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 R45 must keep {key}=true")

    if data.get("p7_hold004_current_working_snapshot_collect_drift_evidence_id") != (
        P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_DRIFT_EVIDENCE_ID
    ):
        raise ValueError("P7-HOLD-004 R45 drift evidence id mismatch")
    if data.get("p7_hold004_active_baseline_current_snapshot_drift_classification_id") != (
        P7_HOLD004_ACTIVE_BASELINE_CURRENT_SNAPSHOT_DRIFT_CLASSIFICATION_ID
    ):
        raise ValueError("P7-HOLD-004 R45 drift classification id mismatch")
    drift_status = _snapshot_drift_status(data.get("current_snapshot_collect_drift_status"))
    if drift_status != P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DRIFT_STATUS_R30_R42_TEST_ADDITION_ACCEPTED:
        raise ValueError("P7-HOLD-004 R45 requires classified R30-R42 current snapshot drift")
    if data.get("p7_hold004_active_baseline_current_snapshot_drift_classification_status") != drift_status:
        raise ValueError("P7-HOLD-004 R45 drift status alias mismatch")
    for key in (
        "current_snapshot_collect_drift_classified",
        "current_snapshot_drift_is_current_working_snapshot_only",
        "current_snapshot_collect_is_not_execution_green",
        "current_snapshot_collect_is_not_full_backend_suite_green",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 R45 must keep {key}=true")
    for key in (
        "current_snapshot_baseline_adoption_allowed",
        "current_snapshot_baseline_adoption_applied",
        "active_baseline_update_allowed",
        "active_baseline_update_applied",
        "backend_group03_execution_allowed_by_this_projection",
        "backend_group03_execution_permanently_forbidden",
        "p7_hold004_closed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 R45 must keep {key}=false")
    for key in (
        "backend_remaining_groups_official_execution_required",
        "backend_group03_execution_required_later",
        "p5_human_qa_review_required",
        "p6_human_readfeel_review_required",
        "real_device_submit_modal_readfeel_unverified",
        "p7_hold004_remaining",
        "projection_is_not_release_permission",
        "projection_is_not_p7_completion",
        "projection_is_not_p8_start_permission",
        "p5_p6_return_recommended",
        "p7_hold004_next_p5_p6_return_recommended",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 R45 must keep {key}=true")

    matrix_projection = safe_mapping(data.get("matrix_projection"))
    release_projection = safe_mapping(data.get("release_handoff_projection"))
    validation_projection = safe_mapping(data.get("validation_projection"))
    hold_projection = safe_mapping(data.get("hold_matrix_projection"))
    if matrix_projection.get("projection_scope") != P7_HOLD004_GROUP02_VALIDATION_SCOPE_ISOLATED_NOT_FULL_SUITE:
        raise ValueError("P7-HOLD-004 R45 matrix projection scope mismatch")
    if matrix_projection.get("group02_isolated_result_projected") is not True:
        raise ValueError("P7-HOLD-004 R45 matrix projection must include group02 isolated result")
    if matrix_projection.get("current_snapshot_collect_drift_projected") is not True:
        raise ValueError("P7-HOLD-004 R45 matrix projection must include current snapshot drift")
    for key in ("p7_complete", "p8_start_allowed", "release_allowed"):
        if matrix_projection.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 R45 matrix projection must keep {key}=false")
    for key in (
        "full_backend_suite_green_confirmed",
        "full_backend_suite_green_claim_allowed",
        "can_claim_full_backend_suite_green",
        "hold004_close_allowed",
        "p7_complete",
        "p8_start_allowed",
        "release_allowed",
    ):
        if release_projection.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 R45 release handoff projection must keep {key}=false")
    if validation_projection.get("validation_scope") != P7_HOLD004_GROUP02_VALIDATION_SCOPE_ISOLATED_NOT_FULL_SUITE:
        raise ValueError("P7-HOLD-004 R45 validation projection scope mismatch")
    for key in (
        "group02_isolated_result_recorded",
        "current_snapshot_collect_drift_classified",
        "p5_human_qa_review_required",
        "p6_human_readfeel_review_required",
        "real_device_submit_modal_readfeel_unverified",
    ):
        if validation_projection.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 R45 validation projection must keep {key}=true")
    for key in ("full_backend_suite_green_confirmed", "release_allowed"):
        if validation_projection.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 R45 validation projection must keep {key}=false")
    for key in ("p7_hold001_remaining", "p7_hold002_remaining", "p7_hold003_remaining", "p7_hold004_remaining"):
        if hold_projection.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 R45 hold matrix projection must keep {key}=true")
    if hold_projection.get("p7_hold004_closed") is not False or hold_projection.get("hold004_close_allowed") is not False:
        raise ValueError("P7-HOLD-004 R45 hold matrix projection must keep HOLD-004 open")

    followups = set(dedupe_identifiers(data.get("required_followup_fixes"), limit=120, max_length=180))
    for required in _p7_hold004_projection_followups():
        if required not in followups:
            raise ValueError(f"P7-HOLD-004 R45 release projection missing followup {required}")
    _assert_release_closed_and_body_free(data, source=source)
    return True


def build_p7_hold004_next_execution_or_p5_p6_return_decision(
    *,
    release_projection: Mapping[str, Any] | None = None,
    prefer_p5_p6_return: bool = True,
    backend_group03_auto_continue_requested: bool = False,
) -> dict[str, Any]:
    """Materialize R46 next-work decision after the R45 projection.

    This decision does not finish P7-HOLD-004 and does not permanently forbid
    backend group_03. It only stops the immediate auto-chain so the next work can
    return to P5/P6 human readfeel and real-device modal review.
    """

    projection = (
        safe_mapping(release_projection)
        if release_projection is not None
        else build_p7_hold004_group02_current_snapshot_release_projection()
    )
    assert_p7_hold004_group02_current_snapshot_release_projection_contract(projection)
    if prefer_p5_p6_return is not True:
        raise ValueError("P7-HOLD-004 R46 must prefer P5/P6 return in this implementation step")
    group03_requested = bool(backend_group03_auto_continue_requested)
    material = {
        "schema_version": P7_HOLD004_NEXT_EXECUTION_OR_P5_P6_RETURN_DECISION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "step": P7_HOLD004_NEXT_EXECUTION_OR_P5_P6_RETURN_DECISION_STEP,
        "implementation_step": P7_HOLD004_NEXT_EXECUTION_OR_P5_P6_RETURN_DECISION_STEP,
        "decision_id": P7_HOLD004_NEXT_EXECUTION_OR_P5_P6_RETURN_DECISION_ID,
        "decision_status": P7_HOLD004_NEXT_DECISION_STATUS_P5_P6_RETURN_RECOMMENDED,
        "source_mode": P7_SOURCE_MODE,
        "git_checked": P7_GIT_CHECKED,
        "release_projection_id": clean_identifier(projection.get("projection_id"), max_length=180),
        "prefer_p5_p6_return_requested": True,
        "next_recommended_work": P7_HOLD004_NEXT_RECOMMENDED_WORK_P5_P6_HUMAN_READFEEL_REAL_DEVICE_MODAL,
        "next_recommended_work_scope": P7_HOLD004_P5_P6_RETURN_SCOPE,
        "p5_p6_return_recommended": True,
        "p5_human_qa_review_required": True,
        "p6_human_readfeel_review_required": True,
        "real_device_submit_modal_readfeel_required": True,
        "real_device_submit_modal_readfeel_unverified": True,
        "backend_group03_execution_allowed_now": False,
        "backend_group03_execution_block_reason": P7_HOLD004_BACKEND_GROUP03_BLOCK_REASON_P5_P6_RETURN_PRIORITIZED,
        "backend_group03_execution_deferred_status": P7_HOLD004_BACKEND_GROUP03_DEFERRED_STATUS_NOT_PERMANENTLY_FORBIDDEN,
        "backend_group03_execution_permanently_forbidden": False,
        "backend_group03_execution_required_later": True,
        "backend_group03_auto_continue_requested": group03_requested,
        "backend_group03_auto_continue_rejected_as_completion": group03_requested,
        "backend_group03_auto_continue_is_not_p7_completion": True,
        "remaining_backend_groups_official_execution_required_later": True,
        "p7_hold004_closed": False,
        "p7_hold004_remaining": True,
        "p7_hold004_closure_claim_rejected": True,
        "p7_hold004_remaining_after_r46": True,
        "p7_complete_claim_allowed": False,
        "p8_start_claim_allowed": False,
        "release_claim_allowed": False,
        "decision_is_not_release_permission": True,
        "decision_is_not_p7_completion": True,
        "decision_is_not_p8_start_permission": True,
        "decision_does_not_update_active_baseline": True,
        "decision_does_not_convert_collect_only_to_execution_green": True,
        "required_hold_refs_for_return": list(P7_HOLD004_P5_P6_RETURN_REQUIRED_HOLD_REFS),
        "required_work_items_for_return": list(P7_HOLD004_P5_P6_RETURN_REQUIRED_WORK_ITEMS),
        "required_followup_fixes": _p7_hold004_projection_followups(),
        **_release_closed_flags(),
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
        **_body_retention_flags(),
        "body_free": True,
    }
    assert_p7_hold004_next_execution_or_p5_p6_return_decision_contract(material)
    return material


def assert_p7_hold004_next_execution_or_p5_p6_return_decision_contract(material: Mapping[str, Any]) -> bool:
    """Validate R46 next-work decision without closing P7-HOLD-004."""

    data = safe_mapping(material)
    source = "p7_hold004_r46_next_execution_or_p5_p6_return_decision"
    if data.get("schema_version") != P7_HOLD004_NEXT_EXECUTION_OR_P5_P6_RETURN_DECISION_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 R46 next decision schema mismatch")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError("P7-HOLD-004 R46 next decision phase/hold mismatch")
    if data.get("step") != P7_HOLD004_NEXT_EXECUTION_OR_P5_P6_RETURN_DECISION_STEP:
        raise ValueError("P7-HOLD-004 R46 next decision step mismatch")
    if data.get("decision_id") != P7_HOLD004_NEXT_EXECUTION_OR_P5_P6_RETURN_DECISION_ID:
        raise ValueError("P7-HOLD-004 R46 next decision id mismatch")
    if data.get("decision_status") != P7_HOLD004_NEXT_DECISION_STATUS_P5_P6_RETURN_RECOMMENDED:
        raise ValueError("P7-HOLD-004 R46 next decision status mismatch")
    if data.get("source_mode") != P7_SOURCE_MODE or data.get("git_checked") is not P7_GIT_CHECKED:
        raise ValueError("P7-HOLD-004 R46 next decision source boundary mismatch")
    if data.get("release_projection_id") != P7_HOLD004_GROUP02_CURRENT_SNAPSHOT_RELEASE_PROJECTION_ID:
        raise ValueError("P7-HOLD-004 R46 release projection id mismatch")
    if data.get("prefer_p5_p6_return_requested") is not True:
        raise ValueError("P7-HOLD-004 R46 must prefer P5/P6 return")
    if data.get("next_recommended_work") != P7_HOLD004_NEXT_RECOMMENDED_WORK_P5_P6_HUMAN_READFEEL_REAL_DEVICE_MODAL:
        raise ValueError("P7-HOLD-004 R46 next recommended work mismatch")
    if data.get("next_recommended_work_scope") != P7_HOLD004_P5_P6_RETURN_SCOPE:
        raise ValueError("P7-HOLD-004 R46 next recommended work scope mismatch")
    for key in (
        "p5_p6_return_recommended",
        "p5_human_qa_review_required",
        "p6_human_readfeel_review_required",
        "real_device_submit_modal_readfeel_required",
        "real_device_submit_modal_readfeel_unverified",
        "backend_group03_auto_continue_is_not_p7_completion",
        "remaining_backend_groups_official_execution_required_later",
        "p7_hold004_remaining",
        "p7_hold004_closure_claim_rejected",
        "p7_hold004_remaining_after_r46",
        "decision_is_not_release_permission",
        "decision_is_not_p7_completion",
        "decision_is_not_p8_start_permission",
        "decision_does_not_update_active_baseline",
        "decision_does_not_convert_collect_only_to_execution_green",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 R46 must keep {key}=true")
    for key in (
        "backend_group03_execution_allowed_now",
        "backend_group03_execution_permanently_forbidden",
        "p7_hold004_closed",
        "p7_complete_claim_allowed",
        "p8_start_claim_allowed",
        "release_claim_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 R46 must keep {key}=false")
    if data.get("backend_group03_execution_block_reason") != (
        P7_HOLD004_BACKEND_GROUP03_BLOCK_REASON_P5_P6_RETURN_PRIORITIZED
    ):
        raise ValueError("P7-HOLD-004 R46 backend group03 block reason mismatch")
    if data.get("backend_group03_execution_deferred_status") != P7_HOLD004_BACKEND_GROUP03_DEFERRED_STATUS_NOT_PERMANENTLY_FORBIDDEN:
        raise ValueError("P7-HOLD-004 R46 backend group03 deferred status mismatch")
    if data.get("backend_group03_execution_required_later") is not True:
        raise ValueError("P7-HOLD-004 R46 must keep backend group03 required later")
    if data.get("backend_group03_auto_continue_rejected_as_completion") is not (
        data.get("backend_group03_auto_continue_requested") is True
    ):
        raise ValueError("P7-HOLD-004 R46 group03 auto-continue rejection flag mismatch")
    if data.get("required_hold_refs_for_return") != list(P7_HOLD004_P5_P6_RETURN_REQUIRED_HOLD_REFS):
        raise ValueError("P7-HOLD-004 R46 return hold refs mismatch")
    if data.get("required_work_items_for_return") != list(P7_HOLD004_P5_P6_RETURN_REQUIRED_WORK_ITEMS):
        raise ValueError("P7-HOLD-004 R46 return work items mismatch")
    followups = set(dedupe_identifiers(data.get("required_followup_fixes"), limit=120, max_length=180))
    for required in _p7_hold004_projection_followups():
        if required not in followups:
            raise ValueError(f"P7-HOLD-004 R46 next decision missing followup {required}")
    _assert_release_closed_and_body_free(data, source=source)
    return True


__all__ = [
    "P7_HOLD004_GROUP02_LOCAL_EXECUTION_EVIDENCE_SCHEMA_VERSION",
    "P7_HOLD004_GROUP02_OFFICIAL_RESULT_RECORDING_RECONCILE_SCHEMA_VERSION",
    "P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_DRIFT_EVIDENCE_SCHEMA_VERSION",
    "P7_HOLD004_ACTIVE_BASELINE_CURRENT_SNAPSHOT_DRIFT_CLASSIFICATION_SCHEMA_VERSION",
    "P7_HOLD004_GROUP02_CURRENT_SNAPSHOT_RELEASE_PROJECTION_SCHEMA_VERSION",
    "P7_HOLD004_NEXT_EXECUTION_OR_P5_P6_RETURN_DECISION_SCHEMA_VERSION",
    "P7_HOLD004_GROUP02_LOCAL_EXECUTION_EVIDENCE_STEP",
    "P7_HOLD004_GROUP02_OFFICIAL_RESULT_RECORDING_RECONCILE_STEP",
    "P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_DRIFT_EVIDENCE_STEP",
    "P7_HOLD004_ACTIVE_BASELINE_CURRENT_SNAPSHOT_DRIFT_CLASSIFICATION_STEP",
    "P7_HOLD004_GROUP02_CURRENT_SNAPSHOT_RELEASE_PROJECTION_STEP",
    "P7_HOLD004_NEXT_EXECUTION_OR_P5_P6_RETURN_DECISION_STEP",
    "P7_HOLD004_GROUP02_LOCAL_EXECUTION_EVIDENCE_ID",
    "P7_HOLD004_GROUP02_OFFICIAL_RESULT_RECORDING_RECONCILE_ID",
    "P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_DRIFT_EVIDENCE_ID",
    "P7_HOLD004_ACTIVE_BASELINE_CURRENT_SNAPSHOT_DRIFT_CLASSIFICATION_ID",
    "P7_HOLD004_GROUP02_CURRENT_SNAPSHOT_RELEASE_PROJECTION_ID",
    "P7_HOLD004_NEXT_EXECUTION_OR_P5_P6_RETURN_DECISION_ID",
    "P7_HOLD004_GROUP02_LOCAL_EXECUTION_COMMAND_ID",
    "P7_HOLD004_GROUP02_LOCAL_EXECUTION_COMMAND_SCOPE_ID",
    "P7_HOLD004_GROUP02_LOCAL_EXECUTION_STATUS_PASS",
    "P7_HOLD004_GROUP02_OBSERVED_EXECUTION_SOURCE_REF",
    "P7_HOLD004_GROUP02_SOURCE_STATUS_REQUIRES_DECISION",
    "P7_HOLD004_GROUP02_SOURCE_STATUS_ACCEPTED_AFTER_EXPLICIT_LOCAL_RERUN",
    "P7_HOLD004_GROUP02_SOURCE_STATUS_BLOCKED_SOURCE_REF_DIFFERS",
    "P7_HOLD004_GROUP02_SOURCE_STATUS_BLOCKED_CURRENT_COLLECT_DRIFT",
    "P7_HOLD004_GROUP02_SOURCE_STATUS_BLOCKED_COMMAND_SCOPE",
    "P7_HOLD004_GROUP02_SOURCE_STATUS_BLOCKED_COUNTS",
    "P7_HOLD004_GROUP02_SOURCE_IDENTITY_STATUSES",
    "P7_HOLD004_GROUP02_RECONCILE_SCOPE_NON_OFFICIAL_LOCAL_EVIDENCE",
    "P7_HOLD004_GROUP02_RECONCILE_SCOPE_GROUP02_ISOLATED_ONLY",
    "P7_HOLD004_GROUP02_CURRENT_SNAPSHOT_RELEASE_PROJECTION_STATUS",
    "P7_HOLD004_NEXT_DECISION_STATUS_P5_P6_RETURN_RECOMMENDED",
    "P7_HOLD004_NEXT_RECOMMENDED_WORK_P5_P6_HUMAN_READFEEL_REAL_DEVICE_MODAL",
    "P7_HOLD004_BACKEND_GROUP03_BLOCK_REASON_P5_P6_RETURN_PRIORITIZED",
    "P7_HOLD004_BACKEND_GROUP03_DEFERRED_STATUS_NOT_PERMANENTLY_FORBIDDEN",
    "P7_HOLD004_GROUP02_VALIDATION_SCOPE_ISOLATED_NOT_FULL_SUITE",
    "P7_HOLD004_P5_P6_RETURN_SCOPE",
    "P7_HOLD004_P5_P6_RETURN_REQUIRED_HOLD_REFS",
    "P7_HOLD004_P5_P6_RETURN_REQUIRED_WORK_ITEMS",
    "P7_HOLD004_CURRENT_WORKING_SNAPSHOT_REF",
    "P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_COMMAND_ID",
    "P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_SCOPE",
    "P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECTED_TEST_FILE_COUNT",
    "P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECTED_TEST_ITEM_COUNT",
    "P7_HOLD004_CURRENT_WORKING_SNAPSHOT_COLLECT_WARNINGS_COUNT",
    "P7_HOLD004_CURRENT_WORKING_SNAPSHOT_TEST_ITEMS_SHA256",
    "P7_HOLD004_CURRENT_WORKING_SNAPSHOT_TEST_FILES_SHA256",
    "P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DELTA_TEST_FILE_COUNT",
    "P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DELTA_TEST_ITEM_COUNT",
    "P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DELTA_WARNINGS_COUNT",
    "P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DRIFT_STATUS_UNCLASSIFIED",
    "P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DRIFT_STATUS_R30_R42_TEST_ADDITION_ACCEPTED",
    "P7_HOLD004_CURRENT_WORKING_SNAPSHOT_DRIFT_CLASSIFICATION_STATUSES",
    "P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_FILE_REFS",
    "P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_FILE_COUNT",
    "P7_HOLD004_CURRENT_WORKING_SNAPSHOT_ADDED_TEST_ITEM_COUNT",
    "assert_p7_hold004_group02_local_execution_evidence_contract",
    "assert_p7_hold004_group02_official_result_recording_reconcile_contract",
    "assert_p7_hold004_current_working_snapshot_collect_drift_evidence_contract",
    "assert_p7_hold004_active_baseline_current_snapshot_drift_classification_contract",
    "assert_p7_hold004_group02_current_snapshot_release_projection_contract",
    "assert_p7_hold004_next_execution_or_p5_p6_return_decision_contract",
    "build_p7_hold004_group02_local_execution_evidence",
    "build_p7_hold004_group02_official_result_recording_reconcile",
    "build_p7_hold004_current_working_snapshot_collect_drift_evidence",
    "build_p7_hold004_active_baseline_current_snapshot_drift_classification",
    "build_p7_hold004_group02_current_snapshot_release_projection",
    "build_p7_hold004_next_execution_or_p5_p6_return_decision",
]
