# -*- coding: utf-8 -*-
"""P7-HOLD-004 backend-suite split consistency materials.

R0/R1/R14/R37 scope only:
- keep the original R0 public/runtime boundary freeze closed;
- retain the 20260615 active baseline as previous active evidence;
- expose the post-adoption received snapshot baseline as the current active
  backend ``pytest --collect-only`` baseline for runtime material builders;
- keep P7-HOLD-004, P7 completion, P8 start, full backend-suite green, and
  release readiness closed.

This module stores identifiers, counts, booleans, enum statuses, and hashes
only. It must never serialize raw input, comment_text bodies, candidate bodies,
surface bodies, reviewer text, terminal output, stdout/stderr, or traceback
bodies.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from hashlib import sha256
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

P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_STEP: Final = (
    "P7-HOLD-004_BackendSuiteSplit_MatrixConsistency_R0_R1_20260614"
)
P7_HOLD004_BACKEND_SUITE_HOLD_ID: Final = "P7-HOLD-004"
P7_HOLD004_ID: Final = P7_HOLD004_BACKEND_SUITE_HOLD_ID

P7_HOLD004_BACKEND_CONTRACT_BOUNDARY_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.backend_suite_contract_boundary_freeze.v1"
)
P7_HOLD004_BACKEND_COLLECT_BASELINE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.backend_collect_baseline.v1"
)
P7_HOLD004_BACKEND_COLLECT_BASELINE_STEP: Final = (
    "P7-HOLD-004_ActiveBaselineRuntimeBuilderRefresh_R37_20260616"
)

P7_HOLD004_BACKEND_CONTRACT_BOUNDARY_FREEZE_ID: Final = (
    "p7_hold004_backend_suite_contract_boundary_freeze_20260614"
)
P7_HOLD004_BACKEND_CONTRACT_BOUNDARY_SOURCE_SNAPSHOT_REF: Final = "mashos-api(147).zip"
P7_HOLD004_PREVIOUS_ACTIVE_COLLECT_BASELINE_ID: Final = "p7_hold004_backend_collect_baseline_20260615"
P7_HOLD004_PREVIOUS_ACTIVE_SOURCE_SNAPSHOT_REF: Final = "mashos-api(147).zip"
P7_HOLD004_PREVIOUS_ACTIVE_TEST_ITEMS_SHA256: Final = (
    "fee1eca805564d0840dc5b23f60a7e2d6c7297d658a76dc4ce175e0137c261f1"
)
P7_HOLD004_PREVIOUS_ACTIVE_TEST_FILES_SHA256: Final = (
    "6866231daf68427dca2de1b2011feea49450f7b4a8b3c5b9dec0f9ccd5f3e9c6"
)
P7_HOLD004_BACKEND_COLLECT_BASELINE_ID: Final = "p7_hold004_backend_collect_baseline_20260615_received_148"
P7_HOLD004_BACKEND_COLLECT_COMMAND_ID: Final = "pytest_collect_only_backend_20260615"
P7_HOLD004_BACKEND_SOURCE_SNAPSHOT_REF: Final = "mashos-api(148).zip"
P7_HOLD004_BACKEND_ACTIVE_BASELINE_REFRESH_APPLIED: Final = True

P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT: Final = 425
P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT: Final = 2856
P7_HOLD004_BACKEND_COLLECT_WARNINGS_COUNT: Final = 1
P7_HOLD004_BACKEND_TEST_ITEMS_SHA256: Final = (
    "4698ce5240707f71fc3678a0153a15626ba9718fbadad83294e57d11946c2e0d"
)
P7_HOLD004_BACKEND_TEST_FILES_SHA256: Final = (
    "6866231daf68427dca2de1b2011feea49450f7b4a8b3c5b9dec0f9ccd5f3e9c6"
)
P7_HOLD004_BACKEND_TEST_ITEMS_FINGERPRINT_SHA256: Final = P7_HOLD004_BACKEND_TEST_ITEMS_SHA256
P7_HOLD004_BACKEND_TEST_FILES_FINGERPRINT_SHA256: Final = P7_HOLD004_BACKEND_TEST_FILES_SHA256

# Compatibility aliases used by follow-up R2+ tests/design material.
P7_HOLD004_CURRENT_BACKEND_TEST_FILE_COUNT: Final = P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT
P7_HOLD004_CURRENT_BACKEND_TEST_ITEM_COUNT: Final = P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT
P7_HOLD004_CURRENT_BACKEND_WARNINGS_COUNT: Final = P7_HOLD004_BACKEND_COLLECT_WARNINGS_COUNT
P7_HOLD004_CURRENT_BACKEND_COLLECTED_TEST_FILE_COUNT: Final = P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT
P7_HOLD004_CURRENT_BACKEND_COLLECTED_TEST_ITEM_COUNT: Final = P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT
P7_HOLD004_CURRENT_BACKEND_COLLECT_WARNINGS_COUNT: Final = P7_HOLD004_BACKEND_COLLECT_WARNINGS_COUNT
P7_HOLD004_CURRENT_BACKEND_TEST_ITEMS_FINGERPRINT_SHA256: Final = P7_HOLD004_BACKEND_TEST_ITEMS_SHA256
P7_HOLD004_CURRENT_BACKEND_TEST_FILES_FINGERPRINT_SHA256: Final = P7_HOLD004_BACKEND_TEST_FILES_SHA256
P7_HOLD004_CURRENT_TEST_ITEMS_FINGERPRINT_SHA256: Final = P7_HOLD004_BACKEND_TEST_ITEMS_SHA256
P7_HOLD004_CURRENT_TEST_FILES_FINGERPRINT_SHA256: Final = P7_HOLD004_BACKEND_TEST_FILES_SHA256

P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM: Final = (
    "test_items=sha256(sorted_pytest_nodeids_joined_by_lf);"
    "test_files=sha256(ordered_unique_test_files_joined_by_lf)"
)
P7_HOLD004_BACKEND_COLLECT_STATUS_COLLECTED: Final = "COLLECTED"
P7_HOLD004_BACKEND_COLLECT_STATUS_COLLECTION_FAILED: Final = "COLLECTION_FAILED"
P7_HOLD004_BACKEND_COLLECT_ALLOWED_STATUSES: Final[frozenset[str]] = frozenset(
    {
        P7_HOLD004_BACKEND_COLLECT_STATUS_COLLECTED,
        P7_HOLD004_BACKEND_COLLECT_STATUS_COLLECTION_FAILED,
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
_ALLOWED_IMPLEMENTATION_SCOPE: Final[dict[str, bool]] = {
    "r0_contract_boundary_fixed": True,
    "r1_collect_baseline_material_allowed": True,
    "runtime_behavior_change_allowed": False,
    "rn_change_allowed": False,
    "api_contract_change_allowed": False,
    "db_change_allowed": False,
    "release_decision_change_allowed": False,
    "p8_implementation_allowed": False,
}
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
_REQUIRED_HOLD_REF: Final = P7_HOLD004_BACKEND_SUITE_HOLD_ID
_REQUIRED_FOLLOWUP_FIXES: Final[tuple[str, ...]] = (
    "backend_suite_group_inventory_refresh_required",
    "backend_suite_execution_plan_refresh_required",
    "backend_suite_matrix_reconnect_required",
    "backend_suite_group_execution_not_run",
    "full_backend_suite_green_unconfirmed",
)


def _false_boundary_flags() -> dict[str, bool]:
    return {key: False for key in _BOUNDARY_FLAG_KEYS}


def _public_contract_boundary_flags() -> dict[str, bool]:
    flags = public_contract_flags()
    flags.update(_false_boundary_flags())
    return flags


def _release_closed_boundary() -> dict[str, bool]:
    return {key: False for key in _RELEASE_CLOSED_KEYS}


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


def _normalized_nodeids(collected_test_nodeids: Iterable[Any]) -> list[str]:
    nodeids: list[str] = []
    for value in collected_test_nodeids:
        if value is None or isinstance(value, (Mapping, list, tuple, set)):
            continue
        nodeid = str(value).strip()
        if nodeid:
            nodeids.append(nodeid)
    return nodeids


def _sha256_joined(values: Iterable[str]) -> str:
    return sha256("\n".join(values).encode("utf-8")).hexdigest()


def build_p7_hold004_backend_collect_summary_from_nodeids(
    collected_test_nodeids: Iterable[Any],
) -> dict[str, Any]:
    """Return count/fingerprint summary from pytest collect node ids.

    The returned summary is intentionally body-free: it does not include the
    node ids themselves, only counts and SHA-256 fingerprints.  This helper does
    not claim that an arbitrary input set is the active current R14 baseline.
    """

    nodeids = _normalized_nodeids(collected_test_nodeids)
    files: list[str] = []
    seen_files: set[str] = set()
    for nodeid in nodeids:
        file_ref = nodeid.split("::", 1)[0]
        if file_ref and file_ref not in seen_files:
            seen_files.add(file_ref)
            files.append(file_ref)

    return {
        "collected_test_file_count": len(files),
        "collected_test_item_count": len(nodeids),
        "test_items_fingerprint_sha256": _sha256_joined(sorted(nodeids)) if nodeids else "",
        "test_files_fingerprint_sha256": _sha256_joined(files) if files else "",
        "fingerprint_algorithm": P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM,
        "body_free": True,
    }


def build_p7_hold004_backend_suite_contract_boundary_freeze() -> dict[str, Any]:
    """Build R0 material that freezes the existing public/runtime boundary."""

    material = {
        "schema_version": P7_HOLD004_BACKEND_CONTRACT_BOUNDARY_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_STEP,
        "implementation_step": P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_STEP,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "boundary_id": P7_HOLD004_BACKEND_CONTRACT_BOUNDARY_FREEZE_ID,
        "source_mode": P7_SOURCE_MODE,
        "source_snapshot_ref": P7_HOLD004_BACKEND_CONTRACT_BOUNDARY_SOURCE_SNAPSHOT_REF,
        "git_checked": P7_GIT_CHECKED,
        "scope_status": "R0_CONTRACT_BOUNDARY_FROZEN",
        "implementation_scope": dict(_ALLOWED_IMPLEMENTATION_SCOPE),
        "boundary_flags": _false_boundary_flags(),
        **_release_closed_boundary(),
        "unresolved_hold_refs": [P7_HOLD004_BACKEND_SUITE_HOLD_ID],
        "required_followup_fixes": list(_REQUIRED_FOLLOWUP_FIXES),
        "public_contract": _public_contract_boundary_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
        "body_free": True,
    }
    assert_p7_hold004_backend_suite_contract_boundary_freeze_contract(material)
    return material


def build_p7_hold004_backend_collect_baseline(
    *,
    baseline_id: Any = P7_HOLD004_BACKEND_COLLECT_BASELINE_ID,
    collect_command_id: Any = P7_HOLD004_BACKEND_COLLECT_COMMAND_ID,
    collection_status: Any = P7_HOLD004_BACKEND_COLLECT_STATUS_COLLECTED,
    collected_test_file_count: Any = P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT,
    collected_test_item_count: Any = P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT,
    warnings_count: Any = P7_HOLD004_BACKEND_COLLECT_WARNINGS_COUNT,
    test_items_fingerprint_sha256: Any = P7_HOLD004_BACKEND_TEST_ITEMS_SHA256,
    test_files_fingerprint_sha256: Any = P7_HOLD004_BACKEND_TEST_FILES_SHA256,
    collected_test_nodeids: Iterable[Any] | None = None,
) -> dict[str, Any]:
    """Build the R14 active current local snapshot collect baseline material."""

    if collected_test_nodeids is not None:
        summary = build_p7_hold004_backend_collect_summary_from_nodeids(collected_test_nodeids)
        collected_test_file_count = summary["collected_test_file_count"]
        collected_test_item_count = summary["collected_test_item_count"]
        test_items_fingerprint_sha256 = summary["test_items_fingerprint_sha256"]
        test_files_fingerprint_sha256 = summary["test_files_fingerprint_sha256"]

    status = clean_identifier(
        collection_status,
        default=P7_HOLD004_BACKEND_COLLECT_STATUS_COLLECTION_FAILED,
        max_length=80,
    ).upper()
    if status not in P7_HOLD004_BACKEND_COLLECT_ALLOWED_STATUSES:
        status = P7_HOLD004_BACKEND_COLLECT_STATUS_COLLECTION_FAILED

    if status != P7_HOLD004_BACKEND_COLLECT_STATUS_COLLECTED:
        collected_test_file_count = 0
        collected_test_item_count = 0
        warnings_count = 0
        test_items_fingerprint_sha256 = ""
        test_files_fingerprint_sha256 = ""

    material = {
        "schema_version": P7_HOLD004_BACKEND_COLLECT_BASELINE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_BACKEND_COLLECT_BASELINE_STEP,
        "implementation_step": P7_HOLD004_BACKEND_COLLECT_BASELINE_STEP,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "baseline_id": clean_identifier(
            baseline_id,
            default=P7_HOLD004_BACKEND_COLLECT_BASELINE_ID,
            max_length=160,
        ),
        "source_mode": P7_SOURCE_MODE,
        "source_snapshot_ref": P7_HOLD004_BACKEND_SOURCE_SNAPSHOT_REF,
        "git_checked": P7_GIT_CHECKED,
        "collect_command_id": clean_identifier(
            collect_command_id,
            default=P7_HOLD004_BACKEND_COLLECT_COMMAND_ID,
            max_length=160,
        ),
        "collection_status": status,
        "collected_test_file_count": _coerce_non_negative_int(collected_test_file_count),
        "collected_test_item_count": _coerce_non_negative_int(collected_test_item_count),
        "warnings_count": _coerce_non_negative_int(warnings_count),
        "test_items_fingerprint_sha256": clean_identifier(
            test_items_fingerprint_sha256,
            max_length=_SHA256_HEX_LENGTH,
        ),
        "test_files_fingerprint_sha256": clean_identifier(
            test_files_fingerprint_sha256,
            max_length=_SHA256_HEX_LENGTH,
        ),
        "fingerprint_algorithm": P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM,
        "pytest_output_retained": False,
        "first_red_captured": False,
        "next_red_captured": False,
        **_release_closed_boundary(),
        "unresolved_hold_refs": [P7_HOLD004_BACKEND_SUITE_HOLD_ID],
        "required_followup_fixes": list(_REQUIRED_FOLLOWUP_FIXES),
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
        "body_free": True,
    }
    assert_p7_hold004_backend_collect_baseline_contract(material)
    return material


def build_p7_hold004_current_backend_collect_baseline() -> dict[str, Any]:
    """Return the active 20260615 current local snapshot collect baseline."""

    return build_p7_hold004_backend_collect_baseline()


def _assert_common_release_closed_and_body_free(data: Mapping[str, Any], *, source: str) -> None:
    for key in _RELEASE_CLOSED_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=false")
    unresolved_holds = set(dedupe_identifiers(data.get("unresolved_hold_refs"), limit=40, max_length=120))
    if _REQUIRED_HOLD_REF not in unresolved_holds:
        raise ValueError(f"{source} must keep P7-HOLD-004 unresolved")
    followups = set(dedupe_identifiers(data.get("required_followup_fixes"), limit=80, max_length=160))
    if "full_backend_suite_green_unconfirmed" not in followups:
        raise ValueError(f"{source} must keep full_backend_suite_green_unconfirmed followup")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must be body_free=true")
    assert_false_markers(safe_mapping(data.get("public_contract")), source=f"{source}.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source=f"{source}.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)


def assert_p7_hold004_backend_suite_contract_boundary_freeze_contract(material: Mapping[str, Any]) -> bool:
    """Validate that R0 freezes scope without mutating public/product contracts."""

    data = safe_mapping(material)
    source = "p7_hold004_backend_suite_contract_boundary_freeze"
    if data.get("schema_version") != P7_HOLD004_BACKEND_CONTRACT_BOUNDARY_FREEZE_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 backend contract boundary schema_version changed")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError("P7-HOLD-004 backend contract boundary must stay in P7-HOLD-004 scope")
    if data.get("implementation_step") != P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_STEP:
        raise ValueError("P7-HOLD-004 backend contract boundary implementation_step changed")
    if data.get("boundary_id") != P7_HOLD004_BACKEND_CONTRACT_BOUNDARY_FREEZE_ID:
        raise ValueError("P7-HOLD-004 backend contract boundary id changed")
    if data.get("source_mode") != P7_SOURCE_MODE or data.get("source_snapshot_ref") != P7_HOLD004_BACKEND_CONTRACT_BOUNDARY_SOURCE_SNAPSHOT_REF:
        raise ValueError("P7-HOLD-004 backend contract boundary must stay on the R0 local snapshot")
    if data.get("git_checked") is not False:
        raise ValueError("P7-HOLD-004 backend contract boundary must not claim GitHub verification")
    if data.get("scope_status") != "R0_CONTRACT_BOUNDARY_FROZEN":
        raise ValueError("P7-HOLD-004 backend contract boundary scope_status changed")

    implementation_scope = safe_mapping(data.get("implementation_scope"))
    for key, expected in _ALLOWED_IMPLEMENTATION_SCOPE.items():
        if implementation_scope.get(key) is not expected:
            raise ValueError(f"P7-HOLD-004 backend contract boundary implementation_scope.{key} changed")
    if set(implementation_scope) != set(_ALLOWED_IMPLEMENTATION_SCOPE):
        raise ValueError("P7-HOLD-004 backend contract boundary implementation_scope keys changed")

    boundary_flags = safe_mapping(data.get("boundary_flags"))
    if set(boundary_flags) != set(_BOUNDARY_FLAG_KEYS):
        raise ValueError("P7-HOLD-004 backend contract boundary flags changed")
    assert_false_markers(boundary_flags, source=f"{source}.boundary_flags")
    _assert_common_release_closed_and_body_free(data, source=source)
    return True


def assert_p7_hold004_backend_collect_baseline_contract(material: Mapping[str, Any]) -> bool:
    """Validate the R14 active current collect baseline boundary."""

    data = safe_mapping(material)
    source = "p7_hold004_backend_collect_baseline"
    if data.get("schema_version") != P7_HOLD004_BACKEND_COLLECT_BASELINE_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 backend collect baseline schema_version changed")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError("P7-HOLD-004 backend collect baseline must stay in P7-HOLD-004 scope")
    if data.get("implementation_step") != P7_HOLD004_BACKEND_COLLECT_BASELINE_STEP:
        raise ValueError("P7-HOLD-004 backend collect baseline implementation_step changed")
    if data.get("baseline_id") != P7_HOLD004_BACKEND_COLLECT_BASELINE_ID:
        raise ValueError("P7-HOLD-004 backend collect baseline_id changed")
    if data.get("source_mode") != P7_SOURCE_MODE or data.get("source_snapshot_ref") != P7_HOLD004_BACKEND_SOURCE_SNAPSHOT_REF:
        raise ValueError("P7-HOLD-004 backend collect baseline must stay on the local snapshot")
    if data.get("git_checked") is not False:
        raise ValueError("P7-HOLD-004 backend collect baseline must not claim GitHub verification")
    if data.get("collect_command_id") != P7_HOLD004_BACKEND_COLLECT_COMMAND_ID:
        raise ValueError("P7-HOLD-004 backend collect command id changed")

    status = data.get("collection_status")
    if status not in P7_HOLD004_BACKEND_COLLECT_ALLOWED_STATUSES:
        raise ValueError("P7-HOLD-004 backend collect baseline collection_status changed")
    if data.get("fingerprint_algorithm") != P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM:
        raise ValueError("P7-HOLD-004 backend collect fingerprint algorithm changed")
    if data.get("pytest_output_retained") is not False:
        raise ValueError("P7-HOLD-004 backend collect baseline must not retain pytest output")
    if data.get("first_red_captured") is not False or data.get("next_red_captured") is not False:
        raise ValueError("R1 collect baseline must not claim red capture")

    warnings_count = _coerce_non_negative_int(data.get("warnings_count"), default=-1)
    if data.get("warnings_count") != warnings_count or warnings_count < 0:
        raise ValueError("P7-HOLD-004 backend collect warnings_count must be a non-negative integer")

    if status == P7_HOLD004_BACKEND_COLLECT_STATUS_COLLECTED:
        if data.get("collected_test_file_count") != P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT:
            raise ValueError("COLLECTED baseline current file count mismatch")
        if data.get("collected_test_item_count") != P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT:
            raise ValueError("COLLECTED baseline current item count mismatch")
        if data.get("warnings_count") != P7_HOLD004_BACKEND_COLLECT_WARNINGS_COUNT:
            raise ValueError("COLLECTED baseline current warning count mismatch")
        if not _is_sha256_hex(data.get("test_items_fingerprint_sha256")):
            raise ValueError("COLLECTED baseline requires test_items_fingerprint_sha256")
        if not _is_sha256_hex(data.get("test_files_fingerprint_sha256")):
            raise ValueError("COLLECTED baseline requires test_files_fingerprint_sha256")
        if data.get("test_items_fingerprint_sha256") != P7_HOLD004_BACKEND_TEST_ITEMS_SHA256:
            raise ValueError("COLLECTED baseline current item fingerprint mismatch")
        if data.get("test_files_fingerprint_sha256") != P7_HOLD004_BACKEND_TEST_FILES_SHA256:
            raise ValueError("COLLECTED baseline current file fingerprint mismatch")
    else:
        if data.get("collected_test_file_count") != 0 or data.get("collected_test_item_count") != 0:
            raise ValueError("non-collected baseline must keep collected counts zero")
        if data.get("test_items_fingerprint_sha256") or data.get("test_files_fingerprint_sha256"):
            raise ValueError("non-collected baseline must not carry collected fingerprints")

    _assert_common_release_closed_and_body_free(data, source=source)
    return True


__all__ = [
    "P7_HOLD004_BACKEND_ACTIVE_BASELINE_REFRESH_APPLIED",
    "P7_HOLD004_BACKEND_COLLECT_BASELINE_ID",
    "P7_HOLD004_BACKEND_CONTRACT_BOUNDARY_SOURCE_SNAPSHOT_REF",
    "P7_HOLD004_PREVIOUS_ACTIVE_COLLECT_BASELINE_ID",
    "P7_HOLD004_PREVIOUS_ACTIVE_SOURCE_SNAPSHOT_REF",
    "P7_HOLD004_PREVIOUS_ACTIVE_TEST_ITEMS_SHA256",
    "P7_HOLD004_PREVIOUS_ACTIVE_TEST_FILES_SHA256",
    "P7_HOLD004_BACKEND_COLLECT_BASELINE_SCHEMA_VERSION",
    "P7_HOLD004_BACKEND_COLLECT_BASELINE_STEP",
    "P7_HOLD004_BACKEND_COLLECT_COMMAND_ID",
    "P7_HOLD004_BACKEND_COLLECT_FINGERPRINT_ALGORITHM",
    "P7_HOLD004_BACKEND_COLLECT_WARNINGS_COUNT",
    "P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT",
    "P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT",
    "P7_HOLD004_BACKEND_CONTRACT_BOUNDARY_FREEZE_ID",
    "P7_HOLD004_BACKEND_CONTRACT_BOUNDARY_FREEZE_SCHEMA_VERSION",
    "P7_HOLD004_BACKEND_SOURCE_SNAPSHOT_REF",
    "P7_HOLD004_BACKEND_SUITE_HOLD_ID",
    "P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_STEP",
    "P7_HOLD004_BACKEND_TEST_FILES_SHA256",
    "P7_HOLD004_BACKEND_TEST_FILES_FINGERPRINT_SHA256",
    "P7_HOLD004_BACKEND_TEST_ITEMS_SHA256",
    "P7_HOLD004_BACKEND_TEST_ITEMS_FINGERPRINT_SHA256",
    "P7_HOLD004_CURRENT_BACKEND_TEST_FILE_COUNT",
    "P7_HOLD004_CURRENT_BACKEND_TEST_FILES_FINGERPRINT_SHA256",
    "P7_HOLD004_CURRENT_BACKEND_TEST_ITEM_COUNT",
    "P7_HOLD004_CURRENT_BACKEND_TEST_ITEMS_FINGERPRINT_SHA256",
    "P7_HOLD004_CURRENT_BACKEND_WARNINGS_COUNT",
    "P7_HOLD004_CURRENT_BACKEND_COLLECTED_TEST_FILE_COUNT",
    "P7_HOLD004_CURRENT_BACKEND_COLLECTED_TEST_ITEM_COUNT",
    "P7_HOLD004_CURRENT_BACKEND_COLLECT_WARNINGS_COUNT",
    "P7_HOLD004_CURRENT_TEST_FILES_FINGERPRINT_SHA256",
    "P7_HOLD004_CURRENT_TEST_ITEMS_FINGERPRINT_SHA256",
    "P7_HOLD004_ID",
    "assert_p7_hold004_backend_collect_baseline_contract",
    "assert_p7_hold004_backend_suite_contract_boundary_freeze_contract",
    "build_p7_hold004_backend_collect_baseline",
    "build_p7_hold004_backend_collect_summary_from_nodeids",
    "build_p7_hold004_backend_suite_contract_boundary_freeze",
    "build_p7_hold004_current_backend_collect_baseline",
]
