# -*- coding: utf-8 -*-
"""P7 R10 manual HOLD matrix for real-device and full-suite checks.

R10 keeps the checks that cannot be closed by subset pytest green outside the
P7 core completion claim.  The material is body-free: it records check ids,
statuses, refs, booleans, and counts only.  It never serializes raw input,
comment text bodies, candidate bodies, surface bodies, reviewer text, or
terminal output.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import (
    P7_PHASE,
    assert_false_markers,
    assert_p7_no_body_payload_or_contract_mutation,
    body_free_flags,
    clean_identifier,
    dedupe_identifiers,
    public_contract_flags,
    safe_mapping,
)
from emlis_ai_p7_hold004_phase16_composer_classification import (
    P7_HOLD004_PHASE16_COMPOSER_CLASSIFICATION_SCHEMA_VERSION,
    P7_HOLD004_PHASE16_HOLD_ID,
    assert_p7_hold004_phase16_composer_classification_contract,
)
from emlis_ai_p7_hold004_path_matrix import (
    P7_HOLD004_PHASE16_DECISION_RULE_SCHEMA_VERSION,
    P7_HOLD004_PHASE16_PATH_MATRIX_SCHEMA_VERSION,
    P7_HOLD004_PHASE16_PUBLIC_ADJACENT_RED_REGISTRATION_SCHEMA_VERSION,
    assert_p7_hold004_phase16_decision_rule_contract,
    assert_p7_hold004_phase16_path_matrix_contract,
    assert_p7_hold004_phase16_public_adjacent_red_registration_contract,
)

from emlis_ai_p7_hold004_positive_public_shape_boundary import (
    P7_HOLD004_POSITIVE_PUBLIC_SHAPE_REPAIRED_STATUS,
    P7_HOLD004_POSITIVE_PUBLIC_SHAPE_SCHEMA_VERSION,
    assert_p7_hold004_positive_public_shape_boundary_contract,
)
from emlis_ai_p7_hold004_step5_candidate_gate_classification import (
    P7_HOLD004_STEP5_HOLD_ID,
    P7_HOLD004_STEP5_R5_META_EXTENSION_SCHEMA_VERSION,
    P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_SCHEMA_VERSION,
    P7_HOLD004_STEP5_RED_ID,
    assert_p7_hold004_step5_meta_extension_contract,
    assert_p7_hold004_step5_material_connection_contract,
)
from emlis_ai_p7_hold004_backend_suite_execution_results import (
    P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_ID,
    P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_SCHEMA_VERSION,
    P7_HOLD004_PREVIOUS_BACKEND_COLLECT_BASELINE_ID,
    P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION,
    P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION_V2,
    P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_ALLOWED_SCHEMA_VERSIONS,
    P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_ITEM_FINGERPRINT_MISMATCH,
    P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY,
    P7_HOLD004_RECEIVED_SNAPSHOT_ITEM_FINGERPRINT_MISMATCH_BLOCKER_REF,
    assert_p7_hold004_backend_suite_execution_summary_contract,
    assert_p7_hold004_official_group02_capture_readiness_contract,
    build_p7_hold004_official_group02_capture_readiness,
)
from emlis_ai_p7_hold004_backend_suite_group_inventory_plan import (
    P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID,
    P7_HOLD004_BACKEND_SUITE_GROUP_DEFINITIONS,
    P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID,
)
from emlis_ai_p7_hold004_backend_suite_split_consistency import (
    P7_HOLD004_BACKEND_COLLECT_BASELINE_ID,
    P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT,
    P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT,
)
from emlis_ai_p7_red_closure_classification import (
    P7_RED_CLOSURE_CLASSIFICATION_MATRIX_SCHEMA_VERSION,
    assert_p7_red_closure_classification_matrix_contract,
    build_p7_red_closure_classification_matrix,
    p7_closed_red_refs_from_classification,
    p7_unresolved_red_refs_from_classification,
)
from emlis_ai_p7_timeout_isolation import (
    P7_E2E_ISOLATION_RESULT_SCHEMA_VERSION,
    P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID,
    assert_p7_e2e_isolation_result_contract,
)

P7_REAL_DEVICE_MODAL_READFEEL_CHECK_SCHEMA_VERSION: Final = "cocolon.emlis.p7.real_device_modal_readfeel_check.v1"
P7_BACKEND_SUITE_SPLIT_MATRIX_SCHEMA_VERSION: Final = "cocolon.emlis.p7.backend_suite_split_matrix.v1"
P7_R10_HOLD_MATRIX_SCHEMA_VERSION: Final = "cocolon.emlis.p7.r10_hold_matrix.v1"
P7_HOLD_MATRIX_SCHEMA_VERSION: Final = P7_R10_HOLD_MATRIX_SCHEMA_VERSION
P7_R10_HOLD_MATRIX_STEP: Final = "P7-R10_RealDeviceFullBackendHoldMatrix_20260613"
P7_R10_HOLD_MATRIX_SCOPE: Final = "P7_real_device_submit_full_backend_suite_hold_matrix"

P7_REAL_DEVICE_CHECK_ID: Final = "p7_real_device_submit_modal_readfeel_20260613"
P7_BACKEND_SUITE_MATRIX_ID: Final = "p7_backend_suite_split_matrix_20260613"

_REAL_DEVICE_CHECKS: Final[tuple[str, ...]] = (
    "emotion_submit_reaches_public_feedback",
    "emlis_modal_title_preserved",
    "comment_text_readable_length",
    "modal_pressure_not_too_high",
    "reinput_motivation_human_readfeel",
)
_ALLOWED_CHECK_STATUSES: Final[frozenset[str]] = frozenset({"not_verified", "verified", "partial", "blocked"})
_ALLOWED_REAL_DEVICE_STATUSES: Final[frozenset[str]] = frozenset({"not_verified", "verified", "partial", "blocked"})
_ALLOWED_BACKEND_GROUP_STATUSES: Final[frozenset[str]] = frozenset(
    {
        "green_confirmed",
        "closed_confirmed",
        "timeout_or_unconfirmed",
        "timeout_isolated",
        "red_until_repaired",
        "not_run",
        "hold_unconfirmed",
        "blocked",
    }
)
_ALLOWED_BACKEND_GROUP_IDS: Final[tuple[str, ...]] = (
    "p7_core",
    "product_quality_reuse_subset",
    "positive_recovery_e2e",
    "product_quality_connection_e2e",
    "real_device_submit_modal_readfeel",
    "full_backend_suite",
)


def _result_kind(observed_results: Mapping[str, Any] | None, key: str) -> str:
    source = safe_mapping(observed_results)
    value = source.get(key)
    if isinstance(value, bool):
        return "passed" if value else "failed"
    if isinstance(value, str):
        return clean_identifier(value, default="not_run", max_length=80)
    data = safe_mapping(value)
    if data.get("passed") is True:
        return "passed"
    return clean_identifier(data.get("result_kind") or data.get("status"), default="not_run", max_length=80)


def _test_count(observed_results: Mapping[str, Any] | None, key: str, default: int = 0) -> int:
    data = safe_mapping(safe_mapping(observed_results).get(key))
    value = data.get("test_count_observed") or data.get("test_count") or data.get("count") or default
    try:
        if value is None or value == "" or isinstance(value, bool):
            return int(default)
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _group(
    group_id: str,
    *,
    status: str,
    green_scope: str,
    green_claim_allowed: bool,
    release_blocking: bool,
    test_count_observed: int = 0,
    red_refs: Sequence[Any] = (),
    hold_refs: Sequence[Any] = (),
    reason_codes: Sequence[Any] = (),
) -> dict[str, Any]:
    return {
        "group_id": clean_identifier(group_id, max_length=120),
        "status": clean_identifier(status, default="not_run", max_length=80),
        "green_scope": clean_identifier(green_scope, default="group_only", max_length=120),
        "green_claim_allowed": green_claim_allowed is True,
        "release_blocking": release_blocking is True,
        "test_count_observed": int(test_count_observed),
        "red_refs": dedupe_identifiers(red_refs, limit=40, max_length=120),
        "hold_refs": dedupe_identifiers(hold_refs, limit=40, max_length=120),
        "reason_codes": dedupe_identifiers(reason_codes, limit=80, max_length=160),
        "can_claim_full_backend_suite_green": False,
        "release_allowed": False,
        "body_free": True,
    }


def _green_or_not_run(kind: str) -> str:
    return "green_confirmed" if kind in {"passed", "green", "green_confirmed"} else "not_run"


def _positive_status(kind: str, *, positive_recovery_red_closed: bool) -> str:
    if positive_recovery_red_closed or kind in {"passed", "green", "closed", "closed_confirmed", "closed_by_r0_r5_positive_recovery_suite"}:
        return "closed_confirmed"
    if kind in {"failed", "red", "red_until_repaired", "2_failed", "failed_preserved"}:
        return "red_until_repaired"
    return "red_until_repaired"


def _connection_status(kind: str) -> str:
    if kind in {"timeout", "timeout_preserved", "timeout_isolated", "hang", "hang_preserved", "red_preserved"}:
        return "timeout_isolated"
    if kind in {"passed", "green"}:
        return "blocked"
    if kind == "not_run":
        return "timeout_or_unconfirmed"
    return "timeout_or_unconfirmed"




def _p7_hold004_group_02_current_counts() -> dict[str, int]:
    for definition in P7_HOLD004_BACKEND_SUITE_GROUP_DEFINITIONS:
        if definition.get("group_id") == "group_02_p7_hold004":
            return {
                "file_count": int(definition.get("file_count", 0) or 0),
                "test_item_count": int(definition.get("test_item_count", 0) or 0),
            }
    return {"file_count": 0, "test_item_count": 0}


def _matrix_current_baseline_connection(
    *,
    collect_baseline_id: Any = "",
    inventory_id: Any = "",
    plan_id: Any = "",
    summary_id: Any = "",
) -> dict[str, Any]:
    group_02_counts = _p7_hold004_group_02_current_counts()
    return {
        "collect_baseline_id": clean_identifier(collect_baseline_id, default=P7_HOLD004_BACKEND_COLLECT_BASELINE_ID, max_length=160),
        "group_inventory_id": clean_identifier(inventory_id, default=P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID, max_length=160),
        "execution_plan_id": clean_identifier(plan_id, default=P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID, max_length=160),
        "execution_summary_id": clean_identifier(summary_id, default=P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_ID, max_length=160),
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


def _backend_execution_summary_connection(
    summary: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Normalize optional R5 execution summary material for R6/R7.

    The summary is an observed split-run material, not a full backend-suite
    green proof.  This helper exposes only body-free identifiers, status enums,
    counts, and reason codes for matrix connection.
    """

    if summary is None:
        return {
            "connected": False,
            "schema_version": "",
            "summary_id": "",
            "collect_baseline_id": "",
            "inventory_id": "",
            "plan_id": "",
            "expected_group_count": 0,
            "expected_total_batch_count": 0,
            "current_collect_baseline_connected": False,
            "current_group_inventory_connected": False,
            "current_execution_plan_connected": False,
            "old_baseline_not_used_as_current": False,
            "backend_suite_group_02_file_count": 0,
            "backend_suite_group_02_test_item_count": 0,
            "backend_suite_group_02_count_current": False,
            "matrix_current_baseline_connection": {},
            "all_groups_executed": False,
            "split_all_groups_green_confirmed": False,
            "group_run_results_recorded": False,
            "group_statuses": {},
            "green_group_ids": [],
            "failed_group_ids": [],
            "timeout_group_ids": [],
            "collection_failed_group_ids": [],
            "interrupted_group_ids": [],
            "blocked_group_ids": [],
            "not_run_group_ids": [],
            "partial_group_ids": [],
            "first_red_present": False,
            "first_timeout_present": False,
            "required_followup_fixes": [],
            "full_suite_group_status": "",
            "reason_codes": [],
        }

    material = safe_mapping(summary)
    assert_p7_hold004_backend_suite_execution_summary_contract(material)
    assert_p7_no_body_payload_or_contract_mutation(
        material,
        source="p7_backend_suite_split_matrix.backend_suite_execution_summary",
    )

    group_statuses = {
        clean_identifier(group_id, max_length=120): clean_identifier(status, default="NOT_RUN", max_length=80).upper()
        for group_id, status in safe_mapping(material.get("group_statuses")).items()
    }
    failed_group_ids = dedupe_identifiers(material.get("failed_group_ids"), limit=40, max_length=120)
    timeout_group_ids = dedupe_identifiers(material.get("timeout_group_ids"), limit=40, max_length=120)
    collection_failed_group_ids = dedupe_identifiers(
        material.get("collection_failed_group_ids"),
        limit=40,
        max_length=120,
    )
    interrupted_group_ids = dedupe_identifiers(material.get("interrupted_group_ids"), limit=40, max_length=120)
    blocked_group_ids = dedupe_identifiers(material.get("blocked_group_ids"), limit=40, max_length=120)
    not_run_group_ids = dedupe_identifiers(material.get("not_run_group_ids"), limit=40, max_length=120)
    partial_group_ids = dedupe_identifiers(material.get("partial_group_ids"), limit=40, max_length=120)
    split_all_green = material.get("split_all_groups_green_confirmed") is True
    group_run_results_recorded = material.get("group_run_results_recorded") is True
    collect_baseline_id = clean_identifier(material.get("collect_baseline_id"), max_length=160)
    inventory_id = clean_identifier(material.get("inventory_id"), max_length=160)
    plan_id = clean_identifier(material.get("plan_id"), max_length=160)
    summary_id = clean_identifier(material.get("summary_id"), max_length=160)
    group_02_counts = _p7_hold004_group_02_current_counts()
    backend_suite_group_02_count_current = (
        group_02_counts.get("file_count") == 19
        and group_02_counts.get("test_item_count") == 252
    )

    if failed_group_ids:
        full_suite_group_status = "red_until_repaired"
    elif timeout_group_ids:
        full_suite_group_status = "timeout_isolated"
    elif collection_failed_group_ids or interrupted_group_ids or blocked_group_ids:
        full_suite_group_status = "blocked"
    elif group_run_results_recorded or split_all_green or partial_group_ids:
        full_suite_group_status = "hold_unconfirmed"
    else:
        full_suite_group_status = ""

    reason_codes = [
        "backend_suite_execution_summary_connected",
        "split_green_is_not_full_backend_suite_green" if split_all_green else "",
        "backend_suite_group_execution_partial" if partial_group_ids else "",
        "first_red_classification_required" if failed_group_ids else "",
        "timeout_classification_required" if timeout_group_ids else "",
        "timeout_isolated_not_green" if timeout_group_ids else "",
        "collection_failed_blocks_execution" if collection_failed_group_ids else "",
        "group_execution_interrupted" if interrupted_group_ids else "",
        "blocked_by_previous_red" if blocked_group_ids else "",
        "backend_suite_group_execution_not_run" if not_run_group_ids else "",
    ]

    first_red = safe_mapping(material.get("first_red"))
    first_timeout = safe_mapping(material.get("first_timeout"))
    return {
        "connected": True,
        "schema_version": clean_identifier(
            material.get("schema_version"),
            default=P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_SCHEMA_VERSION,
            max_length=160,
        ),
        "summary_id": summary_id,
        "collect_baseline_id": collect_baseline_id,
        "inventory_id": inventory_id,
        "plan_id": plan_id,
        "expected_group_count": int(material.get("expected_group_count", 0) or 0),
        "expected_total_batch_count": int(material.get("expected_total_batch_count", 0) or 0),
        "current_collect_baseline_connected": collect_baseline_id == P7_HOLD004_BACKEND_COLLECT_BASELINE_ID,
        "current_group_inventory_connected": inventory_id == P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID,
        "current_execution_plan_connected": plan_id == P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID,
        "old_baseline_not_used_as_current": collect_baseline_id != P7_HOLD004_PREVIOUS_BACKEND_COLLECT_BASELINE_ID,
        "backend_suite_group_02_file_count": group_02_counts.get("file_count", 0),
        "backend_suite_group_02_test_item_count": group_02_counts.get("test_item_count", 0),
        "backend_suite_group_02_count_current": backend_suite_group_02_count_current,
        "matrix_current_baseline_connection": _matrix_current_baseline_connection(
            collect_baseline_id=collect_baseline_id,
            inventory_id=inventory_id,
            plan_id=plan_id,
            summary_id=summary_id,
        ),
        "all_groups_executed": material.get("all_groups_executed") is True,
        "split_all_groups_green_confirmed": split_all_green,
        "group_run_results_recorded": group_run_results_recorded,
        "group_statuses": group_statuses,
        "green_group_ids": dedupe_identifiers(material.get("green_group_ids"), limit=40, max_length=120),
        "failed_group_ids": failed_group_ids,
        "timeout_group_ids": timeout_group_ids,
        "collection_failed_group_ids": collection_failed_group_ids,
        "interrupted_group_ids": interrupted_group_ids,
        "blocked_group_ids": blocked_group_ids,
        "not_run_group_ids": not_run_group_ids,
        "partial_group_ids": partial_group_ids,
        "first_red_present": first_red.get("present") is True,
        "first_timeout_present": first_timeout.get("present") is True,
        "required_followup_fixes": dedupe_identifiers(
            material.get("required_followup_fixes"),
            limit=160,
            max_length=180,
        ),
        "full_suite_group_status": full_suite_group_status,
        "reason_codes": dedupe_identifiers(reason_codes, limit=80, max_length=160),
    }


def _red_closure_connection(
    *,
    red_closure_classification_matrix: Mapping[str, Any] | None = None,
    connection_timeout_isolation_result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize optional RED closure material for backend/R10 matrix connection.

    RED closure material is the source of truth for P7-RED-003.  A raw
    Product Quality Connection E2E pass from legacy ``observed_results`` is not
    enough to close RED-003.
    """

    if red_closure_classification_matrix is None and connection_timeout_isolation_result is None:
        return {
            "connected": False,
            "classification_schema_version": "",
            "source_e2e_isolation_schema_version": "",
            "source_e2e_isolation_result_kind": "",
            "source_e2e_observed_status": "",
            "closed_red_refs": [],
            "unresolved_red_refs": [],
            "product_quality_connection_timeout_closed": False,
            "product_quality_connection_timeout_classified": False,
            "product_quality_connection_timeout_isolated": False,
            "positive_recovery_red_closed": None,
            "connection_e2e_group_status": "",
            "connection_e2e_release_blocking": True,
            "connection_e2e_reason_codes": [],
        }

    if connection_timeout_isolation_result is not None:
        isolation = safe_mapping(connection_timeout_isolation_result)
        assert_p7_e2e_isolation_result_contract(isolation)
        assert_p7_no_body_payload_or_contract_mutation(
            isolation,
            source="p7_backend_suite_split_matrix.connection_timeout_isolation_result",
        )
    else:
        isolation = None

    if red_closure_classification_matrix is not None:
        classification = safe_mapping(red_closure_classification_matrix)
    else:
        classification = build_p7_red_closure_classification_matrix(
            connection_timeout_isolation_result=isolation,
        )
    assert_p7_red_closure_classification_matrix_contract(classification)
    assert_p7_no_body_payload_or_contract_mutation(
        classification,
        source="p7_backend_suite_split_matrix.red_closure_classification_matrix",
    )

    closed_red_refs = p7_closed_red_refs_from_classification(classification)
    unresolved_red_refs = p7_unresolved_red_refs_from_classification(classification)
    red003_closed = P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID in set(closed_red_refs)
    red003_unresolved = P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID in set(unresolved_red_refs)
    if red003_closed:
        group_status = "closed_confirmed"
        release_blocking = False
        reason_codes = (
            "red003_closed_by_structured_classification",
            "product_quality_connection_e2e_closed_is_not_full_backend_suite_green",
        )
    elif red003_unresolved:
        kind = clean_identifier(classification.get("source_e2e_isolation_result_kind"), default="timeout", max_length=80)
        group_status = "timeout_isolated" if kind in {"timeout", "hang", "not_run"} else "red_until_repaired"
        release_blocking = True
        reason_codes = (
            "red003_unresolved_by_structured_classification",
            "product_quality_connection_e2e_timeout_or_unconfirmed",
        )
    else:
        group_status = "timeout_or_unconfirmed"
        release_blocking = True
        reason_codes = ("product_quality_connection_e2e_timeout_or_unconfirmed",)

    return {
        "connected": True,
        "classification_schema_version": clean_identifier(
            classification.get("schema_version"),
            default=P7_RED_CLOSURE_CLASSIFICATION_MATRIX_SCHEMA_VERSION,
            max_length=160,
        ),
        "source_e2e_isolation_schema_version": clean_identifier(
            classification.get("source_e2e_isolation_schema_version"),
            default=P7_E2E_ISOLATION_RESULT_SCHEMA_VERSION,
            max_length=160,
        ),
        "source_e2e_isolation_result_kind": clean_identifier(
            classification.get("source_e2e_isolation_result_kind"),
            default="",
            max_length=80,
        ),
        "source_e2e_observed_status": clean_identifier(
            classification.get("source_e2e_observed_status"),
            default="",
            max_length=120,
        ),
        "closed_red_refs": closed_red_refs,
        "unresolved_red_refs": unresolved_red_refs,
        "product_quality_connection_timeout_closed": red003_closed,
        "product_quality_connection_timeout_classified": classification.get("product_quality_connection_timeout_classified") is True,
        "product_quality_connection_timeout_isolated": classification.get("product_quality_connection_timeout_isolated") is True,
        "positive_recovery_red_closed": classification.get("positive_recovery_red_closed"),
        "connection_e2e_group_status": group_status,
        "connection_e2e_release_blocking": release_blocking,
        "connection_e2e_reason_codes": dedupe_identifiers(reason_codes, limit=20, max_length=160),
    }


def _hold004_phase16_material_summary(
    *,
    hold004_phase16_classification: Mapping[str, Any] | None = None,
    hold004_path_matrix: Mapping[str, Any] | None = None,
    hold004_decision_rule: Mapping[str, Any] | None = None,
    hold004_adjacent_public_red_registration: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize optional P7-HOLD-004 Phase16 material for P7 matrix handoff.

    R7 may connect the classified Phase16 red to the existing P7 HOLD,
    validation, and release-handoff layers.  This helper keeps that connection
    body-free and keeps P7-HOLD-004 unresolved; it never turns classified
    material into full backend-suite green.
    """

    classification = safe_mapping(hold004_phase16_classification)
    if hold004_phase16_classification is not None:
        assert_p7_hold004_phase16_composer_classification_contract(classification)
        assert_p7_no_body_payload_or_contract_mutation(
            classification,
            source="p7_hold004_phase16_material.classification",
        )

    path_matrix = safe_mapping(hold004_path_matrix)
    if hold004_path_matrix is not None:
        assert_p7_hold004_phase16_path_matrix_contract(path_matrix)
        assert_p7_no_body_payload_or_contract_mutation(
            path_matrix,
            source="p7_hold004_phase16_material.path_matrix",
        )

    decision_rule = safe_mapping(hold004_decision_rule)
    if hold004_decision_rule is not None:
        assert_p7_hold004_phase16_decision_rule_contract(decision_rule)
        assert_p7_no_body_payload_or_contract_mutation(
            decision_rule,
            source="p7_hold004_phase16_material.decision_rule",
        )

    adjacent_registration = safe_mapping(hold004_adjacent_public_red_registration)
    if hold004_adjacent_public_red_registration is not None:
        assert_p7_hold004_phase16_public_adjacent_red_registration_contract(adjacent_registration)
        assert_p7_no_body_payload_or_contract_mutation(
            adjacent_registration,
            source="p7_hold004_phase16_material.adjacent_registration",
        )

    classified_red_present = bool(classification or path_matrix or decision_rule or adjacent_registration)
    required_followup_fixes = dedupe_identifiers(
        [
            *classification.get("required_followup_fixes", []),
            *path_matrix.get("required_followup_fixes", []),
            *decision_rule.get("required_followup_fixes", []),
            *adjacent_registration.get("required_followup_fixes", []),
        ],
        limit=80,
        max_length=160,
    )
    candidate_boundary_registered = bool(
        "phase16_complete_composer_candidate_boundary" in required_followup_fixes
        or decision_rule.get("repair_branch") == "R4-A"
        or classification.get("direct_or_conversation_unavailable") is True
        or path_matrix.get("direct_or_conversation_unavailable") is True
    )
    adjacent_public_red_registered = bool(
        "positive_public_fixture_shape_boundary" in required_followup_fixes
        or path_matrix.get("adjacent_public_red_registered") is True
        or adjacent_registration.get("adjacent_public_red_registered") is True
    )
    if classified_red_present and not required_followup_fixes:
        required_followup_fixes = ["phase16_complete_composer_candidate_boundary"]

    return {
        "classified_red_present": classified_red_present,
        "classification_schema_version": clean_identifier(
            classification.get("schema_version"),
            default=P7_HOLD004_PHASE16_COMPOSER_CLASSIFICATION_SCHEMA_VERSION if classification else "",
            max_length=160,
        ),
        "path_matrix_schema_version": clean_identifier(
            path_matrix.get("schema_version"),
            default=P7_HOLD004_PHASE16_PATH_MATRIX_SCHEMA_VERSION if path_matrix else "",
            max_length=160,
        ),
        "decision_rule_schema_version": clean_identifier(
            decision_rule.get("schema_version"),
            default=P7_HOLD004_PHASE16_DECISION_RULE_SCHEMA_VERSION if decision_rule else "",
            max_length=160,
        ),
        "adjacent_registration_schema_version": clean_identifier(
            adjacent_registration.get("schema_version"),
            default=(
                P7_HOLD004_PHASE16_PUBLIC_ADJACENT_RED_REGISTRATION_SCHEMA_VERSION
                if adjacent_registration
                else ""
            ),
            max_length=160,
        ),
        "classification_status": clean_identifier(
            decision_rule.get("status") or classification.get("status"),
            default="not_connected",
            max_length=120,
        ),
        "decision_kind": clean_identifier(decision_rule.get("decision_kind"), default="not_connected", max_length=160),
        "repair_branch": clean_identifier(decision_rule.get("repair_branch"), default="none", max_length=80),
        "candidate_boundary_registered": candidate_boundary_registered,
        "public_adjacent_red_registered": adjacent_public_red_registered,
        "required_followup_fixes": required_followup_fixes,
        "unresolved_hold_refs": [P7_HOLD004_PHASE16_HOLD_ID] if classified_red_present else [],
        "release_allowed": False,
        "p8_start_allowed": False,
        "hold004_close_allowed": False,
        "full_backend_suite_green_confirmed": False,
        "full_backend_suite_green_claim_allowed": False,
        "body_free": True,
    }



def _hold004_positive_public_shape_material_summary(
    hold004_positive_public_shape_boundary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize the R6 positive public shape target-green material.

    This is a body-free handoff summary only.  It can show that the local target
    boundary is green, but it must not close P7-HOLD-004, claim full backend
    suite green, or allow release/P8.
    """

    material = safe_mapping(hold004_positive_public_shape_boundary)
    if hold004_positive_public_shape_boundary is not None:
        assert_p7_hold004_positive_public_shape_boundary_contract(material)
        assert_p7_no_body_payload_or_contract_mutation(
            material,
            source="p7_hold004_positive_public_shape.material",
        )

    connected = bool(material)
    status = clean_identifier(material.get("status"), default="not_connected", max_length=120)
    target_green = material.get("target_green_confirmed") is True
    repaired_pending_full_suite = bool(
        connected
        and status == P7_HOLD004_POSITIVE_PUBLIC_SHAPE_REPAIRED_STATUS
        and target_green
    )
    return {
        "connected": connected,
        "schema_version": clean_identifier(
            material.get("schema_version"),
            default=P7_HOLD004_POSITIVE_PUBLIC_SHAPE_SCHEMA_VERSION if connected else "",
            max_length=160,
        ),
        "status": status,
        "target_green_confirmed": target_green,
        "repaired_target_green_pending_full_suite": repaired_pending_full_suite,
        "true_self_denial_regression_preserved": material.get("true_self_denial_regression_preserved") is True,
        "emergency_safety_regression_preserved": material.get("emergency_safety_regression_preserved") is True,
        "support_required_regression_preserved": material.get("support_required_regression_preserved") is True,
        "r3_input_material_bundle_not_safety_triage_required": (
            material.get("r3_input_material_bundle_not_safety_triage_required") is True
        ),
        "r4_public_e2e_labelled_two_stage_confirmed": (
            material.get("r4_public_e2e_labelled_two_stage_confirmed") is True
        ),
        "full_backend_suite_green_confirmed": False,
        "hold004_close_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "unresolved_hold_refs": [P7_HOLD004_PHASE16_HOLD_ID] if connected else [],
        "reason_codes": dedupe_identifiers(material.get("reason_codes"), limit=80, max_length=160),
        "body_free": True,
    }


def _hold004_step5_material_summary(
    *,
    hold004_step5_meta_extension: Mapping[str, Any] | None = None,
    hold004_step5_material_connection: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize R5/R6 Step5 material for P7-HOLD-004 handoff layers.

    The connection is body-free and deliberately keeps P7-HOLD-004 unresolved.
    It can make the Step5 display-binding material visible to backend split,
    R10 HOLD matrix, validation matrix, and release handoff without claiming
    full backend-suite green.
    """

    r5 = safe_mapping(hold004_step5_meta_extension)
    if hold004_step5_meta_extension is not None:
        assert_p7_hold004_step5_meta_extension_contract(r5)
        assert_p7_no_body_payload_or_contract_mutation(r5, source="p7_hold004_step5_material.r5")

    r6 = safe_mapping(hold004_step5_material_connection)
    if hold004_step5_material_connection is not None:
        assert_p7_hold004_step5_material_connection_contract(r6)
        assert_p7_no_body_payload_or_contract_mutation(r6, source="p7_hold004_step5_material.r6")

    connected = bool(r5 or r6)
    step5_red_closed = bool(
        r6.get("step5_candidate_gate_red_closed") is True
        or r6.get("step5_candidate_gate_red_closed_by_r4c") is True
    )
    step5_red_present = bool(
        r6.get("step5_display_binding_red_present") is True
        or r5.get("display_binding_missing_without_exception") is True
        or P7_HOLD004_STEP5_RED_ID in dedupe_identifiers(r6.get("unresolved_red_refs"), limit=40, max_length=160)
        or P7_HOLD004_STEP5_RED_ID in dedupe_identifiers(r6.get("closed_red_refs"), limit=40, max_length=160)
    )
    required_followup_fixes = dedupe_identifiers(
        [
            *r5.get("required_followup_fixes", []),
            *r6.get("required_followup_fixes", []),
            "step5_display_binding_contract_consistency" if connected else "",
        ],
        limit=80,
        max_length=160,
    )
    # R8 keeps the Step5 display-binding red visible to downstream backend split
    # / release handoff material even when R4-C has replaced the stale target
    # expectation.  R4-C closes the old fail-closed test expectation; R4-D still
    # preserves the mixed contract conflict as HOLD material, so dropping the red
    # ref here would make subset validation lose the blocker.
    unresolved_red_refs = dedupe_identifiers(
        [
            *r5.get("unresolved_red_refs", []),
            *r6.get("unresolved_red_refs", []),
            P7_HOLD004_STEP5_RED_ID if step5_red_present else "",
        ],
        limit=40,
        max_length=160,
    )
    closed_red_refs = dedupe_identifiers(
        [*r6.get("closed_red_refs", []), P7_HOLD004_STEP5_RED_ID if step5_red_closed else ""],
        limit=40,
        max_length=160,
    )
    return {
        "connected": connected,
        "meta_extension_schema_version": clean_identifier(
            r5.get("schema_version") or r6.get("source_r5_meta_extension_schema_version"),
            default=P7_HOLD004_STEP5_R5_META_EXTENSION_SCHEMA_VERSION if (r5 or r6) else "",
            max_length=160,
        ),
        "material_connection_schema_version": clean_identifier(
            r6.get("schema_version"),
            default=P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_SCHEMA_VERSION if r6 else "",
            max_length=160,
        ),
        "material_connection_status": clean_identifier(r6.get("status"), default="not_connected", max_length=120),
        "step5_contract_classification": clean_identifier(
            r6.get("step5_contract_classification") or r5.get("classification") or r5.get("step5_contract_classification"),
            default="not_connected",
            max_length=160,
        ),
        "step5_display_binding_red_present": step5_red_present,
        "step5_candidate_gate_red_classified": bool(r6.get("step5_candidate_gate_red_classified") is True or connected),
        "step5_candidate_gate_red_closed": step5_red_closed,
        "step5_mixed_contract_conflict_held": bool(r6.get("step5_mixed_contract_conflict_held") is True),
        "release_blocker": bool(r6.get("release_blocker") is True or connected),
        "required_followup_fixes": required_followup_fixes,
        "unresolved_hold_refs": [P7_HOLD004_STEP5_HOLD_ID] if connected else [],
        "unresolved_red_refs": unresolved_red_refs,
        "closed_red_refs": closed_red_refs,
        "full_backend_suite_green_confirmed": False,
        "hold004_close_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "body_free": True,
    }


def build_p7_real_device_modal_readfeel_check(
    *,
    check_statuses: Mapping[str, Any] | None = None,
    check_id: Any = P7_REAL_DEVICE_CHECK_ID,
) -> dict[str, Any]:
    """Build body-free material for the real-device submit/modal read-feel HOLD.

    P7 cannot close this check with backend or RN unit tests.  A verified status
    may be recorded later, but this material still does not apply release.
    """

    source = safe_mapping(check_statuses)
    if check_statuses is not None:
        assert_p7_no_body_payload_or_contract_mutation(source, source="p7_real_device_modal_readfeel_check.input")
    checks: dict[str, str] = {}
    for check_name in _REAL_DEVICE_CHECKS:
        status = clean_identifier(source.get(check_name), default="not_verified", max_length=80)
        if status not in _ALLOWED_CHECK_STATUSES:
            status = "not_verified"
        checks[check_name] = status
    verified_count = sum(1 for status in checks.values() if status == "verified")
    blocked_count = sum(1 for status in checks.values() if status == "blocked")
    if verified_count == len(_REAL_DEVICE_CHECKS):
        status = "verified"
    elif blocked_count:
        status = "blocked"
    elif verified_count:
        status = "partial"
    else:
        status = "not_verified"
    hold_refs = [] if status == "verified" else ["P7-HOLD-003"]
    result = {
        "schema_version": P7_REAL_DEVICE_MODAL_READFEEL_CHECK_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R10_HOLD_MATRIX_STEP,
        "scope": "P7_real_device_submit_modal_readfeel_check",
        "check_id": clean_identifier(check_id, default=P7_REAL_DEVICE_CHECK_ID, max_length=120),
        "status": status,
        "platforms_required": ["ios_or_android_real_device"],
        "checks": checks,
        "verified_check_count": verified_count,
        "required_check_count": len(_REAL_DEVICE_CHECKS),
        "real_device_submit_confirmed": status == "verified",
        "manual_real_device_check_required": status != "verified",
        "automated_test_green_can_close": False,
        "hold_refs": hold_refs,
        "release_allowed": False,
        "body_free": True,
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=False, include_reviewer=True),
        "raw_input_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
    }
    assert_p7_real_device_modal_readfeel_check_contract(result)
    return result


def assert_p7_real_device_modal_readfeel_check_contract(check: Mapping[str, Any]) -> bool:
    data = safe_mapping(check)
    if data.get("schema_version") != P7_REAL_DEVICE_MODAL_READFEEL_CHECK_SCHEMA_VERSION:
        raise ValueError("unexpected P7 real-device check schema_version")
    if data.get("phase") != P7_PHASE:
        raise ValueError("unexpected P7 real-device check phase")
    if data.get("release_allowed") is not False or data.get("body_free") is not True:
        raise ValueError("P7 real-device check must stay body-free and release-closed")
    status = clean_identifier(data.get("status"), default="", max_length=80)
    if status not in _ALLOWED_REAL_DEVICE_STATUSES:
        raise ValueError("P7 real-device check status changed")
    checks = safe_mapping(data.get("checks"))
    if set(checks) != set(_REAL_DEVICE_CHECKS):
        raise ValueError("P7 real-device check must keep the fixed checklist")
    if any(clean_identifier(value, max_length=80) not in _ALLOWED_CHECK_STATUSES for value in checks.values()):
        raise ValueError("P7 real-device checklist has unsupported status")
    if data.get("automated_test_green_can_close") is not False:
        raise ValueError("P7 real-device HOLD must not close via automated test green")
    if status != "verified" and "P7-HOLD-003" not in dedupe_identifiers(data.get("hold_refs"), limit=20):
        raise ValueError("P7-HOLD-003 must remain while real-device submit/modal read-feel is unverified")
    if data.get("real_device_submit_confirmed") is True and status != "verified":
        raise ValueError("real_device_submit_confirmed requires verified status")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_real_device_check.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_real_device_check.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_real_device_check")
    return True


def _official_group02_readiness_connection(
    official_group02_capture_readiness: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    readiness = (
        safe_mapping(official_group02_capture_readiness)
        if official_group02_capture_readiness is not None
        else build_p7_hold004_official_group02_capture_readiness()
    )
    assert_p7_hold004_official_group02_capture_readiness_contract(readiness)
    blocked = readiness.get("official_group_02_capture_blocked") is True
    blocker_refs = dedupe_identifiers(readiness.get("blocker_refs"), limit=40, max_length=180)
    followups = dedupe_identifiers(readiness.get("required_followup_fixes"), limit=80, max_length=180)
    return {
        "schema_version": clean_identifier(
            readiness.get("schema_version"),
            default=P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION,
            max_length=160,
        ),
        "readiness_id": clean_identifier(readiness.get("readiness_id"), default="", max_length=160),
        "readiness_status": clean_identifier(readiness.get("readiness_status"), default="", max_length=160),
        "blocked": blocked,
        "run_allowed": readiness.get("official_capture_run_allowed") is True,
        "result_recording_allowed": readiness.get("official_capture_result_recording_allowed") is True,
        "baseline_fingerprint_reconciled": readiness.get("received_snapshot_baseline_fingerprint_reconciled") is True,
        "item_fingerprint_mismatch_unresolved": readiness.get("received_snapshot_item_fingerprint_mismatch_unresolved") is True,
        "source_snapshot_ref_current_for_received_zip": readiness.get("source_snapshot_ref_current_for_received_zip") is True,
        "active_baseline_accepts_received_nodeids": readiness.get("active_baseline_accepts_received_nodeids") is True,
        "active_baseline_refresh_schema_version": clean_identifier(
            readiness.get("active_baseline_refresh_schema_version"), default="", max_length=160
        ),
        "active_baseline_refresh_id": clean_identifier(readiness.get("active_baseline_refresh_id"), default="", max_length=180),
        "runtime_builder_refresh_status_id": clean_identifier(
            readiness.get("runtime_builder_refresh_status_id"), default="", max_length=180
        ),
        "post_adoption_received_snapshot_reconcile_id": clean_identifier(
            readiness.get("post_adoption_received_snapshot_reconcile_id"), default="", max_length=180
        ),
        "active_baseline_update_applied_to_runtime_builders": readiness.get(
            "active_baseline_update_applied_to_runtime_builders"
        ) is True,
        "source_snapshot_ref_updated_in_active_builders": readiness.get(
            "source_snapshot_ref_updated_in_active_builders"
        ) is True,
        "post_adoption_readiness_re_evaluated": readiness.get("post_adoption_readiness_re_evaluated") is True,
        "blocker_refs": blocker_refs,
        "required_followup_fixes": followups,
    }


def build_p7_backend_suite_split_matrix(
    *,
    observed_results: Mapping[str, Any] | None = None,
    backend_suite_execution_summary: Mapping[str, Any] | None = None,
    red_closure_classification_matrix: Mapping[str, Any] | None = None,
    connection_timeout_isolation_result: Mapping[str, Any] | None = None,
    real_device_check: Mapping[str, Any] | None = None,
    positive_recovery_red_closed: bool = True,
    hold004_phase16_classification: Mapping[str, Any] | None = None,
    hold004_path_matrix: Mapping[str, Any] | None = None,
    hold004_decision_rule: Mapping[str, Any] | None = None,
    hold004_adjacent_public_red_registration: Mapping[str, Any] | None = None,
    hold004_positive_public_shape_boundary: Mapping[str, Any] | None = None,
    hold004_step5_meta_extension: Mapping[str, Any] | None = None,
    hold004_step5_material_connection: Mapping[str, Any] | None = None,
    official_group02_capture_readiness: Mapping[str, Any] | None = None,
    matrix_id: Any = P7_BACKEND_SUITE_MATRIX_ID,
) -> dict[str, Any]:
    """Build the body-free split matrix for P7 backend/full-suite HOLDs."""

    if observed_results is not None:
        assert_p7_no_body_payload_or_contract_mutation(observed_results, source="p7_backend_suite_split_matrix.observed_results")
    real_device = safe_mapping(real_device_check) if real_device_check is not None else build_p7_real_device_modal_readfeel_check()
    assert_p7_real_device_modal_readfeel_check_contract(real_device)

    p7_core_kind = _result_kind(observed_results, "p7_core_contract")
    reuse_kind = _result_kind(observed_results, "existing_p7_reuse_contract")
    positive_kind = _result_kind(observed_results, "heavy_isolated_positive_recovery_red")
    connection_kind = _result_kind(observed_results, "heavy_isolated_product_quality_connection_timeout")
    full_kind = _result_kind(observed_results, "full_backend_suite")
    hold004_material = _hold004_phase16_material_summary(
        hold004_phase16_classification=hold004_phase16_classification,
        hold004_path_matrix=hold004_path_matrix,
        hold004_decision_rule=hold004_decision_rule,
        hold004_adjacent_public_red_registration=hold004_adjacent_public_red_registration,
    )
    hold004_positive_material = _hold004_positive_public_shape_material_summary(
        hold004_positive_public_shape_boundary
    )
    hold004_step5_material = _hold004_step5_material_summary(
        hold004_step5_meta_extension=hold004_step5_meta_extension,
        hold004_step5_material_connection=hold004_step5_material_connection,
    )
    execution_summary_material = _backend_execution_summary_connection(
        backend_suite_execution_summary,
    )
    red_closure_material = _red_closure_connection(
        red_closure_classification_matrix=red_closure_classification_matrix,
        connection_timeout_isolation_result=connection_timeout_isolation_result,
    )
    official_group02_readiness_material = _official_group02_readiness_connection(
        official_group02_capture_readiness
    )
    if isinstance(red_closure_material.get("positive_recovery_red_closed"), bool):
        positive_recovery_red_closed = red_closure_material["positive_recovery_red_closed"] is True

    p7_core_status = _green_or_not_run(p7_core_kind)
    reuse_status = _green_or_not_run(reuse_kind)
    positive_status = _positive_status(positive_kind, positive_recovery_red_closed=positive_recovery_red_closed)
    connection_status = (
        red_closure_material["connection_e2e_group_status"]
        if red_closure_material["connected"]
        else _connection_status(connection_kind)
    )
    if not red_closure_material["connected"] and connection_kind in {"passed", "green"}:
        connection_reason_codes = (
            "connection_e2e_passed_without_red_closure_material",
            "product_quality_connection_e2e_pass_is_not_red003_closure",
        )
    elif red_closure_material["connected"]:
        connection_reason_codes = tuple(red_closure_material["connection_e2e_reason_codes"])
    else:
        connection_reason_codes = ("product_quality_connection_e2e_timeout_or_unconfirmed",)
    summary_full_status = clean_identifier(
        execution_summary_material.get("full_suite_group_status"),
        default="",
        max_length=80,
    )
    full_suite_status = (
        summary_full_status
        if summary_full_status
        else ("not_run" if full_kind in {"not_run", "unconfirmed", "timeout", "hang"} else "hold_unconfirmed")
    )
    real_device_status = "green_confirmed" if real_device.get("status") == "verified" else "hold_unconfirmed"

    full_suite_reason_codes = dedupe_identifiers(
        [
            "full_backend_suite_green_unconfirmed",
            P7_HOLD004_RECEIVED_SNAPSHOT_ITEM_FINGERPRINT_MISMATCH_BLOCKER_REF
            if official_group02_readiness_material["item_fingerprint_mismatch_unresolved"]
            else "",
            *official_group02_readiness_material["required_followup_fixes"],
            "p7_hold004_phase16_classified_red_present"
            if hold004_material["classified_red_present"]
            else "",
            *hold004_material["required_followup_fixes"],
            "p7_hold004_step5_display_binding_red_present"
            if hold004_step5_material["step5_display_binding_red_present"]
            else "",
            *hold004_step5_material["required_followup_fixes"],
            "positive_public_shape_target_green_pending_full_suite"
            if hold004_positive_material["target_green_confirmed"]
            else "",
            *execution_summary_material["required_followup_fixes"],
            *execution_summary_material["reason_codes"],
            "red003_closed_pending_backend_suite_hold"
            if red_closure_material["product_quality_connection_timeout_closed"]
            else "",
        ],
        limit=80,
        max_length=160,
    )

    groups = [
        _group(
            "p7_core",
            status=p7_core_status,
            green_scope="group_only",
            green_claim_allowed=p7_core_status == "green_confirmed",
            release_blocking=False,
            test_count_observed=_test_count(observed_results, "p7_core_contract", 0),
            reason_codes=("p7_core_green_is_group_only",),
        ),
        _group(
            "product_quality_reuse_subset",
            status=reuse_status,
            green_scope="group_only",
            green_claim_allowed=reuse_status == "green_confirmed",
            release_blocking=False,
            test_count_observed=_test_count(observed_results, "existing_p7_reuse_contract", 0),
            reason_codes=("reuse_subset_green_is_group_only",),
        ),
        _group(
            "positive_recovery_e2e",
            status=positive_status,
            green_scope="isolated_red_closure_only",
            green_claim_allowed=False,
            release_blocking=False,
            test_count_observed=_test_count(observed_results, "heavy_isolated_positive_recovery_red", 0),
            red_refs=() if positive_status == "closed_confirmed" else ("P7-RED-001", "P7-RED-002"),
            reason_codes=("positive_recovery_red_closure_is_not_p7_complete",),
        ),
        _group(
            "product_quality_connection_e2e",
            status=connection_status,
            green_scope="isolated_red_closure_only"
            if red_closure_material["product_quality_connection_timeout_closed"]
            else "isolated_timeout_only",
            green_claim_allowed=False,
            release_blocking=red_closure_material["connection_e2e_release_blocking"],
            test_count_observed=_test_count(observed_results, "heavy_isolated_product_quality_connection_timeout", 0),
            red_refs=()
            if red_closure_material["product_quality_connection_timeout_closed"]
            else (P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID,),
            reason_codes=connection_reason_codes,
        ),
        _group(
            "real_device_submit_modal_readfeel",
            status=real_device_status,
            green_scope="manual_real_device_check_only",
            green_claim_allowed=False,
            release_blocking=real_device.get("status") != "verified",
            hold_refs=real_device.get("hold_refs", []),
            reason_codes=("real_device_submit_modal_readfeel_unverified",),
        ),
        _group(
            "full_backend_suite",
            status=full_suite_status,
            green_scope="not_claimable_from_split_groups",
            green_claim_allowed=False,
            release_blocking=True,
            hold_refs=dedupe_identifiers(
                [
                    "P7-HOLD-004",
                    *hold004_material["unresolved_hold_refs"],
                    *hold004_positive_material["unresolved_hold_refs"],
                    *hold004_step5_material["unresolved_hold_refs"],
                ],
                limit=40,
                max_length=120,
            ),
            red_refs=dedupe_identifiers(
                [
                    *hold004_step5_material["unresolved_red_refs"],
                    "p7_hold004_backend_suite_first_red"
                    if execution_summary_material["failed_group_ids"]
                    else "",
                ],
                limit=40,
                max_length=160,
            ),
            reason_codes=full_suite_reason_codes,
        ),
    ]
    unresolved_hold_refs = dedupe_identifiers(
        [
            *real_device.get("hold_refs", []),
            "P7-HOLD-004",
            *hold004_material["unresolved_hold_refs"],
            *hold004_positive_material["unresolved_hold_refs"],
            *hold004_step5_material["unresolved_hold_refs"],
        ],
        limit=40,
        max_length=120,
    )
    red003_source_unresolved_refs = (
        list(red_closure_material["unresolved_red_refs"])
        if red_closure_material["connected"]
        else [P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID]
    )
    unresolved_red_refs = dedupe_identifiers(
        [
            *red003_source_unresolved_refs,
            *hold004_step5_material["unresolved_red_refs"],
        ],
        limit=80,
        max_length=160,
    )
    closed_red_refs = dedupe_identifiers(
        red_closure_material["closed_red_refs"],
        limit=80,
        max_length=160,
    )
    matrix = {
        "schema_version": P7_BACKEND_SUITE_SPLIT_MATRIX_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R10_HOLD_MATRIX_STEP,
        "scope": "P7_backend_suite_split_matrix",
        "matrix_id": clean_identifier(matrix_id, default=P7_BACKEND_SUITE_MATRIX_ID, max_length=120),
        "real_device_check_schema_version": clean_identifier(
            real_device.get("schema_version"), default=P7_REAL_DEVICE_MODAL_READFEEL_CHECK_SCHEMA_VERSION, max_length=128
        ),
        "groups": groups,
        "group_statuses": {group["group_id"]: group["status"] for group in groups},
        "fine_group_statuses": execution_summary_material["group_statuses"],
        "backend_suite_execution_summary_connected": execution_summary_material["connected"],
        "backend_suite_execution_summary_schema_version": execution_summary_material["schema_version"],
        "backend_suite_execution_summary_id": execution_summary_material["summary_id"],
        "backend_suite_execution_summary_collect_baseline_id": execution_summary_material["collect_baseline_id"],
        "backend_suite_execution_summary_inventory_id": execution_summary_material["inventory_id"],
        "backend_suite_execution_summary_plan_id": execution_summary_material["plan_id"],
        "backend_suite_execution_summary_expected_group_count": execution_summary_material["expected_group_count"],
        "backend_suite_execution_summary_expected_total_batch_count": execution_summary_material["expected_total_batch_count"],
        "current_collect_baseline_connected": execution_summary_material["current_collect_baseline_connected"],
        "current_group_inventory_connected": execution_summary_material["current_group_inventory_connected"],
        "current_execution_plan_connected": execution_summary_material["current_execution_plan_connected"],
        "old_baseline_not_used_as_current": execution_summary_material["old_baseline_not_used_as_current"],
        "backend_suite_group_02_file_count": execution_summary_material["backend_suite_group_02_file_count"],
        "backend_suite_group_02_test_item_count": execution_summary_material["backend_suite_group_02_test_item_count"],
        "backend_suite_group_02_count_current": execution_summary_material["backend_suite_group_02_count_current"],
        "matrix_current_baseline_connection": execution_summary_material["matrix_current_baseline_connection"],
        "backend_suite_execution_summary_all_groups_executed": execution_summary_material["all_groups_executed"],
        "backend_suite_execution_summary_group_run_results_recorded": execution_summary_material["group_run_results_recorded"],
        "backend_suite_execution_summary_split_all_groups_green_confirmed": execution_summary_material["split_all_groups_green_confirmed"],
        "backend_suite_execution_summary_green_group_ids": execution_summary_material["green_group_ids"],
        "backend_suite_execution_summary_failed_group_ids": execution_summary_material["failed_group_ids"],
        "backend_suite_execution_summary_timeout_group_ids": execution_summary_material["timeout_group_ids"],
        "backend_suite_execution_summary_collection_failed_group_ids": execution_summary_material["collection_failed_group_ids"],
        "backend_suite_execution_summary_interrupted_group_ids": execution_summary_material["interrupted_group_ids"],
        "backend_suite_execution_summary_blocked_group_ids": execution_summary_material["blocked_group_ids"],
        "backend_suite_execution_summary_not_run_group_ids": execution_summary_material["not_run_group_ids"],
        "backend_suite_execution_summary_partial_group_ids": execution_summary_material["partial_group_ids"],
        "backend_suite_execution_summary_first_red_present": execution_summary_material["first_red_present"],
        "backend_suite_execution_summary_first_timeout_present": execution_summary_material["first_timeout_present"],
        "split_all_groups_green_confirmed": execution_summary_material["split_all_groups_green_confirmed"],
        "split_green_all_groups_confirmed": execution_summary_material["split_all_groups_green_confirmed"],
        "red_closure_classification_connected": red_closure_material["connected"],
        "red_closure_classification_schema_version": red_closure_material["classification_schema_version"],
        "red_closure_source_e2e_isolation_schema_version": red_closure_material["source_e2e_isolation_schema_version"],
        "red_closure_source_e2e_isolation_result_kind": red_closure_material["source_e2e_isolation_result_kind"],
        "red_closure_source_e2e_observed_status": red_closure_material["source_e2e_observed_status"],
        "closed_red_refs": closed_red_refs,
        "product_quality_connection_timeout_classified": red_closure_material["product_quality_connection_timeout_classified"],
        "product_quality_connection_timeout_closed": red_closure_material["product_quality_connection_timeout_closed"],
        "product_quality_connection_timeout_isolated": red_closure_material["product_quality_connection_timeout_isolated"],
        "product_quality_connection_e2e_status": connection_status,
        "unresolved_red_refs": unresolved_red_refs,
        "unresolved_hold_refs": unresolved_hold_refs,
        "required_followup_fixes": dedupe_identifiers(
            [
                *full_suite_reason_codes,
            ],
            limit=120,
            max_length=180,
        ),
        "hold004_phase16_classification_schema_version": hold004_material["classification_schema_version"],
        "hold004_phase16_path_matrix_schema_version": hold004_material["path_matrix_schema_version"],
        "hold004_phase16_decision_rule_schema_version": hold004_material["decision_rule_schema_version"],
        "hold004_phase16_adjacent_registration_schema_version": hold004_material["adjacent_registration_schema_version"],
        "hold004_phase16_classified_red_present": hold004_material["classified_red_present"],
        "hold004_phase16_classification_status": hold004_material["classification_status"],
        "hold004_phase16_decision_kind": hold004_material["decision_kind"],
        "hold004_phase16_repair_branch": hold004_material["repair_branch"],
        "hold004_phase16_candidate_boundary_registered": hold004_material["candidate_boundary_registered"],
        "hold004_public_adjacent_red_registered": hold004_material["public_adjacent_red_registered"],
        "hold004_required_followup_fixes": hold004_material["required_followup_fixes"],
        "hold004_step5_meta_extension_schema_version": hold004_step5_material["meta_extension_schema_version"],
        "hold004_step5_material_connection_schema_version": hold004_step5_material["material_connection_schema_version"],
        "hold004_step5_material_connection_status": hold004_step5_material["material_connection_status"],
        "hold004_step5_material_connected": hold004_step5_material["connected"],
        "hold004_step5_contract_classification": hold004_step5_material["step5_contract_classification"],
        "hold004_step5_display_binding_red_present": hold004_step5_material["step5_display_binding_red_present"],
        "hold004_step5_candidate_gate_red_classified": hold004_step5_material["step5_candidate_gate_red_classified"],
        "hold004_step5_candidate_gate_red_closed": hold004_step5_material["step5_candidate_gate_red_closed"],
        "hold004_step5_mixed_contract_conflict_held": hold004_step5_material["step5_mixed_contract_conflict_held"],
        "hold004_step5_release_blocker": hold004_step5_material["release_blocker"],
        "hold004_step5_required_followup_fixes": hold004_step5_material["required_followup_fixes"],
        "hold004_step5_unresolved_red_refs": hold004_step5_material["unresolved_red_refs"],
        "hold004_step5_closed_red_refs": hold004_step5_material["closed_red_refs"],
        "hold004_step5_material_connection_status": "connected" if hold004_step5_material["connected"] else "not_connected",
        "hold004_step5_full_backend_suite_green_confirmed": False,
        "hold004_step5_release_allowed": False,
        "hold004_positive_public_shape_boundary_schema_version": hold004_positive_material["schema_version"],
        "hold004_positive_public_shape_boundary_status": hold004_positive_material["status"],
        "hold004_positive_public_shape_target_green_confirmed": hold004_positive_material["target_green_confirmed"],
        "hold004_positive_public_shape_repaired_target_green_pending_full_suite": hold004_positive_material[
            "repaired_target_green_pending_full_suite"
        ],
        "hold004_positive_public_shape_true_self_denial_regression_preserved": hold004_positive_material[
            "true_self_denial_regression_preserved"
        ],
        "hold004_positive_public_shape_emergency_regression_preserved": hold004_positive_material[
            "emergency_safety_regression_preserved"
        ],
        "hold004_positive_public_shape_support_required_regression_preserved": hold004_positive_material[
            "support_required_regression_preserved"
        ],
        "hold004_positive_public_shape_input_material_bundle_confirmed": hold004_positive_material[
            "r3_input_material_bundle_not_safety_triage_required"
        ],
        "hold004_positive_public_shape_public_e2e_labelled_two_stage_confirmed": hold004_positive_material[
            "r4_public_e2e_labelled_two_stage_confirmed"
        ],
        "hold004_positive_public_shape_full_backend_suite_green_confirmed": False,
        "hold004_positive_public_shape_release_allowed": False,
        "official_group_02_capture_readiness_schema_version": official_group02_readiness_material["schema_version"],
        "official_group_02_capture_readiness_id": official_group02_readiness_material["readiness_id"],
        "official_group_02_capture_readiness_status": official_group02_readiness_material["readiness_status"],
        "official_group_02_capture_blocked": official_group02_readiness_material["blocked"],
        "official_group_02_capture_run_allowed": official_group02_readiness_material["run_allowed"],
        "official_group_02_capture_result_recording_allowed": official_group02_readiness_material["result_recording_allowed"],
        "received_snapshot_baseline_fingerprint_reconciled": official_group02_readiness_material["baseline_fingerprint_reconciled"],
        "received_snapshot_item_fingerprint_mismatch_unresolved": official_group02_readiness_material["item_fingerprint_mismatch_unresolved"],
        "source_snapshot_ref_current_for_received_zip": official_group02_readiness_material["source_snapshot_ref_current_for_received_zip"],
        "active_baseline_accepts_received_nodeids": official_group02_readiness_material["active_baseline_accepts_received_nodeids"],
        "active_baseline_refresh_schema_version": official_group02_readiness_material["active_baseline_refresh_schema_version"],
        "active_baseline_refresh_id": official_group02_readiness_material["active_baseline_refresh_id"],
        "runtime_builder_refresh_status_id": official_group02_readiness_material["runtime_builder_refresh_status_id"],
        "post_adoption_received_snapshot_reconcile_id": official_group02_readiness_material[
            "post_adoption_received_snapshot_reconcile_id"
        ],
        "active_baseline_update_applied_to_runtime_builders": official_group02_readiness_material[
            "active_baseline_update_applied_to_runtime_builders"
        ],
        "source_snapshot_ref_updated_in_active_builders": official_group02_readiness_material[
            "source_snapshot_ref_updated_in_active_builders"
        ],
        "post_adoption_readiness_re_evaluated": official_group02_readiness_material["post_adoption_readiness_re_evaluated"],
        "received_snapshot_blocker_refs": official_group02_readiness_material["blocker_refs"],
        "received_snapshot_required_followup_fixes": official_group02_readiness_material["required_followup_fixes"],
        "full_backend_suite_green_confirmed": False,
        "full_backend_suite_green_claim_allowed": False,
        "split_green_is_full_backend_suite_green": False,
        "split_green_can_close_p7_hold004": False,
        "real_device_submit_confirmed": real_device.get("real_device_submit_confirmed") is True,
        "real_device_submit_hold_preserved": "P7-HOLD-003" in unresolved_hold_refs,
        "p7_hold003_preserved": "P7-HOLD-003" in unresolved_hold_refs,
        "p7_hold004_preserved": "P7-HOLD-004" in unresolved_hold_refs,
        "release_allowed": False,
        "body_free": True,
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
    }
    assert_p7_backend_suite_split_matrix_contract(matrix)
    return matrix


def assert_p7_backend_suite_split_matrix_contract(matrix: Mapping[str, Any]) -> bool:
    data = safe_mapping(matrix)
    if data.get("schema_version") != P7_BACKEND_SUITE_SPLIT_MATRIX_SCHEMA_VERSION:
        raise ValueError("unexpected P7 backend suite split matrix schema_version")
    if data.get("phase") != P7_PHASE:
        raise ValueError("unexpected P7 backend suite split matrix phase")
    if data.get("release_allowed") is not False or data.get("body_free") is not True:
        raise ValueError("P7 backend suite split matrix must stay body-free and release-closed")
    if data.get("full_backend_suite_green_confirmed") is not False:
        raise ValueError("P7 R10 must not claim full backend suite green")
    if data.get("full_backend_suite_green_claim_allowed") is not False:
        raise ValueError("P7 R10 must not allow full backend suite green claim")
    if data.get("split_green_is_full_backend_suite_green") is not False:
        raise ValueError("P7 split green must not be treated as full backend suite green")
    if data.get("split_all_groups_green_confirmed") is True:
        if data.get("full_backend_suite_green_confirmed") is not False:
            raise ValueError("P7 split all-groups green must not become full backend suite green")
        if data.get("split_green_can_close_p7_hold004") is not False:
            raise ValueError("P7 split all-groups green must not close P7-HOLD-004")
    if data.get("backend_suite_execution_summary_connected") is True:
        if data.get("backend_suite_execution_summary_schema_version") != P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_SCHEMA_VERSION:
            raise ValueError("P7 backend split matrix execution summary schema_version mismatch")
        if not isinstance(data.get("fine_group_statuses"), Mapping) or not data.get("fine_group_statuses"):
            raise ValueError("P7 backend split matrix must expose fine group statuses when execution summary is connected")
        if data.get("backend_suite_execution_summary_collect_baseline_id") != P7_HOLD004_BACKEND_COLLECT_BASELINE_ID:
            raise ValueError("P7 backend split matrix must connect the current collect baseline id")
        if data.get("backend_suite_execution_summary_inventory_id") != P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID:
            raise ValueError("P7 backend split matrix must connect the current group inventory id")
        if data.get("backend_suite_execution_summary_plan_id") != P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID:
            raise ValueError("P7 backend split matrix must connect the current execution plan id")
        for key in ("current_collect_baseline_connected", "current_group_inventory_connected", "current_execution_plan_connected", "old_baseline_not_used_as_current", "backend_suite_group_02_count_current"):
            if data.get(key) is not True:
                raise ValueError(f"P7 backend split matrix must keep {key}=true")
        connection = safe_mapping(data.get("matrix_current_baseline_connection"))
        if connection.get("collect_baseline_id") != P7_HOLD004_BACKEND_COLLECT_BASELINE_ID:
            raise ValueError("P7 backend split matrix current baseline connection collect id mismatch")
        if connection.get("group_inventory_id") != P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID:
            raise ValueError("P7 backend split matrix current baseline connection inventory id mismatch")
        if connection.get("execution_plan_id") != P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID:
            raise ValueError("P7 backend split matrix current baseline connection plan id mismatch")
        if connection.get("old_baseline_used_as_current") is not False:
            raise ValueError("P7 backend split matrix must not use old baseline as current")
    if data.get("red_closure_classification_connected") is True:
        if data.get("red_closure_classification_schema_version") != P7_RED_CLOSURE_CLASSIFICATION_MATRIX_SCHEMA_VERSION:
            raise ValueError("P7 backend split matrix RED closure schema_version mismatch")
        if data.get("red_closure_source_e2e_isolation_schema_version") != P7_E2E_ISOLATION_RESULT_SCHEMA_VERSION:
            raise ValueError("P7 backend split matrix RED closure E2E source schema_version mismatch")
    groups = data.get("groups")
    if not isinstance(groups, list) or len(groups) != len(_ALLOWED_BACKEND_GROUP_IDS):
        raise ValueError("P7 backend suite split matrix must include the fixed groups")
    group_ids: set[str] = set()
    for raw_group in groups:
        group = safe_mapping(raw_group)
        group_id = clean_identifier(group.get("group_id"), max_length=120)
        if group_id not in _ALLOWED_BACKEND_GROUP_IDS or group_id in group_ids:
            raise ValueError("P7 backend suite split matrix group id changed")
        group_ids.add(group_id)
        if group.get("status") not in _ALLOWED_BACKEND_GROUP_STATUSES:
            raise ValueError("P7 backend suite split matrix group status changed")
        if group.get("release_allowed") is not False or group.get("body_free") is not True:
            raise ValueError("P7 backend suite split group must stay body-free and release-closed")
        if group.get("can_claim_full_backend_suite_green") is not False:
            raise ValueError("P7 split group must not claim full backend suite green")
        if group_id in {"positive_recovery_e2e", "product_quality_connection_e2e", "real_device_submit_modal_readfeel", "full_backend_suite"}:
            if group.get("green_claim_allowed") is not False:
                raise ValueError("P7 isolated/manual/full-suite groups must not allow green claim")
    if set(group_ids) != set(_ALLOWED_BACKEND_GROUP_IDS):
        raise ValueError("P7 backend suite split matrix missing a fixed group")
    unresolved_hold_refs = set(dedupe_identifiers(data.get("unresolved_hold_refs"), limit=80, max_length=120))
    if data.get("real_device_submit_confirmed") is not True and "P7-HOLD-003" not in unresolved_hold_refs:
        raise ValueError("P7-HOLD-003 must remain until real-device submit/modal read-feel is verified")
    if "P7-HOLD-004" not in unresolved_hold_refs:
        raise ValueError("P7-HOLD-004 must remain until full backend suite is actually confirmed")
    readiness_schema_version = clean_identifier(
        data.get("official_group_02_capture_readiness_schema_version"), default="", max_length=160
    )
    if readiness_schema_version not in P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_ALLOWED_SCHEMA_VERSIONS:
        raise ValueError("P7 backend split matrix official group_02 readiness schema_version mismatch")
    readiness_after_refresh = readiness_schema_version == P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION_V2
    if data.get("received_snapshot_item_fingerprint_mismatch_unresolved") is True:
        if data.get("official_group_02_capture_readiness_status") != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_ITEM_FINGERPRINT_MISMATCH:
            raise ValueError("P7 backend split matrix must expose unresolved received snapshot item mismatch")
        if data.get("official_group_02_capture_blocked") is not True:
            raise ValueError("P7 backend split matrix must keep official group_02 capture blocked")
        if data.get("official_group_02_capture_run_allowed") is not False:
            raise ValueError("P7 backend split matrix must not allow official capture run while received snapshot mismatch is unresolved")
        if data.get("official_group_02_capture_result_recording_allowed") is not False:
            raise ValueError("P7 backend split matrix must not allow official capture result recording while mismatch is unresolved")
        if P7_HOLD004_RECEIVED_SNAPSHOT_ITEM_FINGERPRINT_MISMATCH_BLOCKER_REF not in dedupe_identifiers(
            data.get("received_snapshot_blocker_refs"),
            limit=40,
            max_length=180,
        ):
            raise ValueError("P7 backend split matrix must carry received snapshot item mismatch blocker")
        if P7_HOLD004_RECEIVED_SNAPSHOT_ITEM_FINGERPRINT_MISMATCH_BLOCKER_REF not in dedupe_identifiers(
            data.get("required_followup_fixes"),
            limit=120,
            max_length=180,
        ):
            raise ValueError("P7 backend split matrix must expose received snapshot item mismatch follow-up")
    if readiness_after_refresh:
        if data.get("official_group_02_capture_readiness_status") != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY:
            raise ValueError("P7 backend split matrix must expose after-refresh group_02 readiness as READY")
        if data.get("received_snapshot_item_fingerprint_mismatch_unresolved") is not False:
            raise ValueError("P7 backend split matrix after-refresh readiness must resolve item mismatch")
        if data.get("received_snapshot_baseline_fingerprint_reconciled") is not True:
            raise ValueError("P7 backend split matrix after-refresh readiness must carry reconciled baseline")
        if data.get("official_group_02_capture_blocked") is not False:
            raise ValueError("P7 backend split matrix after-refresh readiness must unblock capture run")
        if data.get("official_group_02_capture_run_allowed") is not True:
            raise ValueError("P7 backend split matrix after-refresh readiness must allow capture run")
        if data.get("official_group_02_capture_result_recording_allowed") is not True:
            raise ValueError("P7 backend split matrix after-refresh readiness must allow result recording")
        if data.get("active_baseline_update_applied_to_runtime_builders") is not True:
            raise ValueError("P7 backend split matrix must carry runtime-builder refresh application")
        if data.get("source_snapshot_ref_updated_in_active_builders") is not True:
            raise ValueError("P7 backend split matrix must carry active builder source refresh")
        if data.get("official_group_02_capture_green_confirmed") is True:
            raise ValueError("P7 backend split matrix readiness must not claim group_02 green")
        if data.get("full_backend_suite_green_confirmed") is not False:
            raise ValueError("P7 backend split matrix readiness must not claim full backend suite green")
    if data.get("hold004_phase16_classified_red_present") is True:
        if data.get("hold004_phase16_candidate_boundary_registered") is not True:
            raise ValueError("classified HOLD-004 Phase16 material must register the candidate boundary")
        if not dedupe_identifiers(data.get("hold004_required_followup_fixes"), limit=80, max_length=160):
            raise ValueError("classified HOLD-004 Phase16 material must expose follow-up fixes")
    if data.get("hold004_step5_material_connected") is True:
        if data.get("hold004_step5_meta_extension_schema_version") != P7_HOLD004_STEP5_R5_META_EXTENSION_SCHEMA_VERSION:
            raise ValueError("P7 R10 HOLD matrix Step5 R5 schema_version mismatch")
        if data.get("hold004_step5_material_connection_schema_version") != P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_SCHEMA_VERSION:
            raise ValueError("P7 R10 HOLD matrix Step5 R6 schema_version mismatch")
        if data.get("hold004_step5_release_blocker") is not True:
            raise ValueError("P7 R10 HOLD matrix must keep Step5 material as release blocker")
        if "step5_display_binding_contract_consistency" not in dedupe_identifiers(
            data.get("hold004_step5_required_followup_fixes"), limit=80, max_length=160
        ):
            raise ValueError("P7 R10 HOLD matrix must expose Step5 display-binding follow-up")
        if data.get("hold004_step5_full_backend_suite_green_confirmed") is not False:
            raise ValueError("P7 R10 HOLD matrix must not promote Step5 material to full-suite green")
        if data.get("hold004_step5_release_allowed") is not False:
            raise ValueError("P7 R10 HOLD matrix must keep Step5 release_allowed=false")
        if data.get("hold004_step5_display_binding_red_present") is True and data.get("hold004_step5_candidate_gate_red_closed") is not True:
            if P7_HOLD004_STEP5_RED_ID not in dedupe_identifiers(data.get("unresolved_red_refs"), limit=80, max_length=160):
                raise ValueError("P7 matrix must expose the unresolved Step5 display-binding red ref")

    if data.get("hold004_positive_public_shape_boundary_schema_version"):
        if data.get("hold004_positive_public_shape_boundary_schema_version") != P7_HOLD004_POSITIVE_PUBLIC_SHAPE_SCHEMA_VERSION:
            raise ValueError("positive public shape boundary schema_version mismatch in backend split matrix")
        if data.get("hold004_positive_public_shape_boundary_status") != P7_HOLD004_POSITIVE_PUBLIC_SHAPE_REPAIRED_STATUS:
            raise ValueError("positive public shape boundary must be repaired-pending-full-suite in backend split matrix")
        for key in (
            "hold004_positive_public_shape_target_green_confirmed",
            "hold004_positive_public_shape_repaired_target_green_pending_full_suite",
            "hold004_positive_public_shape_true_self_denial_regression_preserved",
            "hold004_positive_public_shape_emergency_regression_preserved",
            "hold004_positive_public_shape_support_required_regression_preserved",
            "hold004_positive_public_shape_input_material_bundle_confirmed",
            "hold004_positive_public_shape_public_e2e_labelled_two_stage_confirmed",
        ):
            if data.get(key) is not True:
                raise ValueError(f"positive public shape backend split matrix must keep {key}=True")
        if data.get("hold004_positive_public_shape_full_backend_suite_green_confirmed") is not False:
            raise ValueError("positive public shape target green must not become full backend suite green")
        if data.get("hold004_positive_public_shape_release_allowed") is not False:
            raise ValueError("positive public shape target green must not allow release")
    if data.get("hold004_step5_material_connection_schema_version"):
        if data.get("hold004_step5_material_connection_schema_version") != P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_SCHEMA_VERSION:
            raise ValueError("Step5 material connection schema_version mismatch in backend split matrix")
        if data.get("hold004_step5_candidate_gate_red_classified") is not True:
            raise ValueError("Step5 material connection must classify the candidate-gate red")
        if "step5_display_binding_contract_consistency" not in dedupe_identifiers(
            data.get("hold004_step5_required_followup_fixes"),
            limit=80,
            max_length=160,
        ):
            raise ValueError("Step5 material connection must expose the display-binding follow-up")
        if data.get("hold004_step5_full_backend_suite_green_confirmed") is not False:
            raise ValueError("Step5 material connection must not claim full backend suite green")
        if data.get("hold004_step5_release_allowed") is not False:
            raise ValueError("Step5 material connection must not allow release")
        if data.get("hold004_step5_display_binding_red_present") is True and data.get("hold004_step5_candidate_gate_red_closed") is not True:
            if P7_HOLD004_STEP5_RED_ID not in dedupe_identifiers(data.get("hold004_step5_unresolved_red_refs"), limit=40, max_length=160):
                raise ValueError("unresolved Step5 display-binding red must stay visible")
    if data.get("hold004_step5_material_connected") is True:
        if data.get("hold004_step5_meta_extension_schema_version") != P7_HOLD004_STEP5_R5_META_EXTENSION_SCHEMA_VERSION:
            raise ValueError("P7 backend split matrix Step5 R5 schema_version mismatch")
        if data.get("hold004_step5_material_connection_schema_version") != P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_SCHEMA_VERSION:
            raise ValueError("P7 backend split matrix Step5 R6 schema_version mismatch")
        if data.get("hold004_step5_release_blocker") is not True:
            raise ValueError("P7 backend split matrix must keep Step5 material as release blocker")
        if "step5_display_binding_contract_consistency" not in dedupe_identifiers(
            data.get("hold004_step5_required_followup_fixes"), limit=80, max_length=160
        ):
            raise ValueError("P7 backend split matrix must expose Step5 display-binding follow-up")
        if data.get("hold004_step5_full_backend_suite_green_confirmed") is not False:
            raise ValueError("P7 backend split matrix must not promote Step5 material to full-suite green")
        if data.get("hold004_step5_release_allowed") is not False:
            raise ValueError("P7 backend split matrix must keep Step5 release_allowed=false")
        if data.get("hold004_step5_display_binding_red_present") is True and P7_HOLD004_STEP5_RED_ID not in dedupe_identifiers(
            data.get("unresolved_red_refs"), limit=80, max_length=160
        ):
            raise ValueError("P7 backend split matrix must expose the Step5 display-binding red ref")

    for key in (
        "full_backend_suite_green_confirmed",
        "full_backend_suite_green_claim_allowed",
        "hold004_close_allowed",
        "p8_start_allowed",
        "release_allowed",
    ):
        if safe_mapping({key: data.get(key)}).get(key) is True:
            raise ValueError(f"P7 backend split matrix must keep {key}=False")
    red003_ref = P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID
    unresolved_red_refs = set(dedupe_identifiers(data.get("unresolved_red_refs"), limit=80, max_length=160))
    closed_red_refs = set(dedupe_identifiers(data.get("closed_red_refs"), limit=80, max_length=160))
    product_quality_group = next(
        (safe_mapping(group) for group in groups if safe_mapping(group).get("group_id") == "product_quality_connection_e2e"),
        {},
    )
    if data.get("product_quality_connection_timeout_closed") is True:
        if red003_ref not in closed_red_refs or red003_ref in unresolved_red_refs:
            raise ValueError("P7-RED-003 must be closed, not unresolved, when structured RED closure material is connected")
        if product_quality_group.get("status") != "closed_confirmed":
            raise ValueError("P7 backend split matrix must mark Product Quality Connection E2E closed when RED-003 is closed")
        if red003_ref in dedupe_identifiers(product_quality_group.get("red_refs"), limit=40, max_length=160):
            raise ValueError("closed P7-RED-003 must not remain on the Product Quality Connection group red_refs")
    elif red003_ref not in unresolved_red_refs:
        raise ValueError("P7-RED-003 must remain visible in the R10 backend split matrix until structured closure material closes it")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_backend_suite_split_matrix.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_backend_suite_split_matrix.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_backend_suite_split_matrix")
    return True


def build_p7_r10_hold_matrix(
    *,
    real_device_check: Mapping[str, Any] | None = None,
    backend_suite_split_matrix: Mapping[str, Any] | None = None,
    observed_results: Mapping[str, Any] | None = None,
    backend_suite_execution_summary: Mapping[str, Any] | None = None,
    red_closure_classification_matrix: Mapping[str, Any] | None = None,
    connection_timeout_isolation_result: Mapping[str, Any] | None = None,
    hold004_phase16_classification: Mapping[str, Any] | None = None,
    hold004_path_matrix: Mapping[str, Any] | None = None,
    hold004_decision_rule: Mapping[str, Any] | None = None,
    hold004_adjacent_public_red_registration: Mapping[str, Any] | None = None,
    hold004_positive_public_shape_boundary: Mapping[str, Any] | None = None,
    hold004_step5_meta_extension: Mapping[str, Any] | None = None,
    hold004_step5_material_connection: Mapping[str, Any] | None = None,
    official_group02_capture_readiness: Mapping[str, Any] | None = None,
    matrix_id: Any = "p7_r10_hold_matrix",
) -> dict[str, Any]:
    """Build the composite R10 HOLD matrix."""

    real_device = safe_mapping(real_device_check) if real_device_check is not None else build_p7_real_device_modal_readfeel_check()
    assert_p7_real_device_modal_readfeel_check_contract(real_device)
    backend = (
        safe_mapping(backend_suite_split_matrix)
        if backend_suite_split_matrix is not None
        else build_p7_backend_suite_split_matrix(
            observed_results=observed_results,
            backend_suite_execution_summary=backend_suite_execution_summary,
            red_closure_classification_matrix=red_closure_classification_matrix,
            connection_timeout_isolation_result=connection_timeout_isolation_result,
            real_device_check=real_device,
            hold004_phase16_classification=hold004_phase16_classification,
            hold004_path_matrix=hold004_path_matrix,
            hold004_decision_rule=hold004_decision_rule,
            hold004_adjacent_public_red_registration=hold004_adjacent_public_red_registration,
            hold004_positive_public_shape_boundary=hold004_positive_public_shape_boundary,
            hold004_step5_meta_extension=hold004_step5_meta_extension,
            hold004_step5_material_connection=hold004_step5_material_connection,
            official_group02_capture_readiness=official_group02_capture_readiness,
        )
    )
    assert_p7_backend_suite_split_matrix_contract(backend)
    unresolved_hold_refs = dedupe_identifiers(
        [*real_device.get("hold_refs", []), *backend.get("unresolved_hold_refs", [])], limit=80, max_length=120
    )
    unresolved_red_refs = dedupe_identifiers(backend.get("unresolved_red_refs"), limit=80, max_length=120)
    matrix = {
        "schema_version": P7_R10_HOLD_MATRIX_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R10_HOLD_MATRIX_STEP,
        "scope": P7_R10_HOLD_MATRIX_SCOPE,
        "matrix_id": clean_identifier(matrix_id, default="p7_r10_hold_matrix", max_length=120),
        "real_device_check_schema_version": real_device.get("schema_version"),
        "real_device_modal_readfeel_check_schema_version": real_device.get("schema_version"),
        "backend_suite_split_matrix_schema_version": backend.get("schema_version"),
        "backend_suite_execution_summary_connected": backend.get("backend_suite_execution_summary_connected") is True,
        "backend_suite_execution_summary_schema_version": backend.get("backend_suite_execution_summary_schema_version", ""),
        "backend_suite_execution_summary_id": backend.get("backend_suite_execution_summary_id", ""),
        "backend_suite_execution_summary_collect_baseline_id": backend.get("backend_suite_execution_summary_collect_baseline_id", ""),
        "backend_suite_execution_summary_inventory_id": backend.get("backend_suite_execution_summary_inventory_id", ""),
        "backend_suite_execution_summary_plan_id": backend.get("backend_suite_execution_summary_plan_id", ""),
        "backend_suite_execution_summary_expected_group_count": int(backend.get("backend_suite_execution_summary_expected_group_count", 0) or 0),
        "backend_suite_execution_summary_expected_total_batch_count": int(backend.get("backend_suite_execution_summary_expected_total_batch_count", 0) or 0),
        "current_collect_baseline_connected": backend.get("current_collect_baseline_connected") is True,
        "current_group_inventory_connected": backend.get("current_group_inventory_connected") is True,
        "current_execution_plan_connected": backend.get("current_execution_plan_connected") is True,
        "old_baseline_not_used_as_current": backend.get("old_baseline_not_used_as_current") is True,
        "backend_suite_group_02_file_count": int(backend.get("backend_suite_group_02_file_count", 0) or 0),
        "backend_suite_group_02_test_item_count": int(backend.get("backend_suite_group_02_test_item_count", 0) or 0),
        "backend_suite_group_02_count_current": backend.get("backend_suite_group_02_count_current") is True,
        "matrix_current_baseline_connection": safe_mapping(backend.get("matrix_current_baseline_connection")),
        "backend_suite_execution_summary_all_groups_executed": backend.get("backend_suite_execution_summary_all_groups_executed") is True,
        "backend_suite_execution_summary_group_run_results_recorded": backend.get("backend_suite_execution_summary_group_run_results_recorded") is True,
        "backend_suite_execution_summary_split_all_groups_green_confirmed": backend.get("backend_suite_execution_summary_split_all_groups_green_confirmed") is True,
        "backend_suite_execution_summary_failed_group_ids": dedupe_identifiers(
            backend.get("backend_suite_execution_summary_failed_group_ids"),
            limit=40,
            max_length=120,
        ),
        "backend_suite_execution_summary_timeout_group_ids": dedupe_identifiers(
            backend.get("backend_suite_execution_summary_timeout_group_ids"),
            limit=40,
            max_length=120,
        ),
        "backend_suite_execution_summary_not_run_group_ids": dedupe_identifiers(
            backend.get("backend_suite_execution_summary_not_run_group_ids"),
            limit=40,
            max_length=120,
        ),
        "backend_suite_execution_summary_partial_group_ids": dedupe_identifiers(
            backend.get("backend_suite_execution_summary_partial_group_ids"),
            limit=40,
            max_length=120,
        ),
        "fine_group_statuses": safe_mapping(backend.get("fine_group_statuses")),
        "red_closure_classification_connected": backend.get("red_closure_classification_connected") is True,
        "red_closure_classification_schema_version": backend.get("red_closure_classification_schema_version", ""),
        "red_closure_source_e2e_isolation_schema_version": backend.get("red_closure_source_e2e_isolation_schema_version", ""),
        "red_closure_source_e2e_isolation_result_kind": backend.get("red_closure_source_e2e_isolation_result_kind", ""),
        "red_closure_source_e2e_observed_status": backend.get("red_closure_source_e2e_observed_status", ""),
        "product_quality_connection_timeout_classified": backend.get("product_quality_connection_timeout_classified") is True,
        "product_quality_connection_timeout_closed": backend.get("product_quality_connection_timeout_closed") is True,
        "product_quality_connection_timeout_isolated": backend.get("product_quality_connection_timeout_isolated") is True,
        "product_quality_connection_e2e_status": backend.get("product_quality_connection_e2e_status", ""),
        "closed_red_refs": dedupe_identifiers(backend.get("closed_red_refs"), limit=80, max_length=160),
        "split_all_groups_green_confirmed": backend.get("split_all_groups_green_confirmed") is True,
        "split_green_all_groups_confirmed": backend.get("split_green_all_groups_confirmed") is True,
        "hold004_phase16_classification_schema_version": backend.get("hold004_phase16_classification_schema_version", ""),
        "hold004_phase16_path_matrix_schema_version": backend.get("hold004_phase16_path_matrix_schema_version", ""),
        "hold004_phase16_decision_rule_schema_version": backend.get("hold004_phase16_decision_rule_schema_version", ""),
        "hold004_phase16_adjacent_registration_schema_version": backend.get("hold004_phase16_adjacent_registration_schema_version", ""),
        "hold004_phase16_classified_red_present": backend.get("hold004_phase16_classified_red_present") is True,
        "hold004_phase16_candidate_boundary_registered": backend.get("hold004_phase16_candidate_boundary_registered") is True,
        "hold004_public_adjacent_red_registered": backend.get("hold004_public_adjacent_red_registered") is True,
        "hold004_required_followup_fixes": dedupe_identifiers(
            backend.get("hold004_required_followup_fixes"),
            limit=80,
            max_length=160,
        ),
        "hold004_step5_meta_extension_schema_version": backend.get("hold004_step5_meta_extension_schema_version", ""),
        "hold004_step5_material_connection_schema_version": backend.get("hold004_step5_material_connection_schema_version", ""),
        "hold004_step5_material_connected": backend.get("hold004_step5_material_connected") is True,
        "hold004_step5_contract_classification": backend.get("hold004_step5_contract_classification", ""),
        "hold004_step5_display_binding_red_present": backend.get("hold004_step5_display_binding_red_present") is True,
        "hold004_step5_candidate_gate_red_classified": backend.get("hold004_step5_candidate_gate_red_classified") is True,
        "hold004_step5_candidate_gate_red_closed": backend.get("hold004_step5_candidate_gate_red_closed") is True,
        "hold004_step5_mixed_contract_conflict_held": backend.get("hold004_step5_mixed_contract_conflict_held") is True,
        "hold004_step5_release_blocker": backend.get("hold004_step5_release_blocker") is True,
        "hold004_step5_required_followup_fixes": dedupe_identifiers(
            backend.get("hold004_step5_required_followup_fixes"),
            limit=80,
            max_length=160,
        ),
        "hold004_step5_full_backend_suite_green_confirmed": False,
        "hold004_step5_release_allowed": False,
        "hold004_positive_public_shape_boundary_schema_version": backend.get(
            "hold004_positive_public_shape_boundary_schema_version", ""
        ),
        "hold004_positive_public_shape_boundary_status": backend.get(
            "hold004_positive_public_shape_boundary_status", ""
        ),
        "hold004_positive_public_shape_target_green_confirmed": backend.get(
            "hold004_positive_public_shape_target_green_confirmed"
        ) is True,
        "hold004_positive_public_shape_repaired_target_green_pending_full_suite": backend.get(
            "hold004_positive_public_shape_repaired_target_green_pending_full_suite"
        ) is True,
        "hold004_positive_public_shape_true_self_denial_regression_preserved": backend.get(
            "hold004_positive_public_shape_true_self_denial_regression_preserved"
        ) is True,
        "hold004_positive_public_shape_emergency_regression_preserved": backend.get(
            "hold004_positive_public_shape_emergency_regression_preserved"
        ) is True,
        "hold004_positive_public_shape_support_required_regression_preserved": backend.get(
            "hold004_positive_public_shape_support_required_regression_preserved"
        ) is True,
        "hold004_positive_public_shape_input_material_bundle_confirmed": backend.get(
            "hold004_positive_public_shape_input_material_bundle_confirmed"
        ) is True,
        "hold004_positive_public_shape_public_e2e_labelled_two_stage_confirmed": backend.get(
            "hold004_positive_public_shape_public_e2e_labelled_two_stage_confirmed"
        ) is True,
        "hold004_positive_public_shape_full_backend_suite_green_confirmed": False,
        "hold004_positive_public_shape_release_allowed": False,
        "hold004_step5_material_connection_schema_version": backend.get(
            "hold004_step5_material_connection_schema_version", ""
        ),
        "hold004_step5_material_connection_status": backend.get(
            "hold004_step5_material_connection_status", ""
        ),
        "hold004_step5_candidate_gate_red_classified": backend.get(
            "hold004_step5_candidate_gate_red_classified"
        ) is True,
        "hold004_step5_display_binding_red_present": backend.get(
            "hold004_step5_display_binding_red_present"
        ) is True,
        "hold004_step5_candidate_gate_red_closed": backend.get(
            "hold004_step5_candidate_gate_red_closed"
        ) is True,
        "hold004_step5_contract_classification": backend.get("hold004_step5_contract_classification", ""),
        "hold004_step5_required_followup_fixes": dedupe_identifiers(
            backend.get("hold004_step5_required_followup_fixes"),
            limit=80,
            max_length=160,
        ),
        "hold004_step5_unresolved_red_refs": dedupe_identifiers(
            backend.get("hold004_step5_unresolved_red_refs"),
            limit=40,
            max_length=160,
        ),
        "hold004_step5_closed_red_refs": dedupe_identifiers(
            backend.get("hold004_step5_closed_red_refs"),
            limit=40,
            max_length=160,
        ),
        "hold004_step5_full_backend_suite_green_confirmed": False,
        "hold004_step5_release_allowed": False,
        "official_group_02_capture_readiness_schema_version": backend.get("official_group_02_capture_readiness_schema_version", ""),
        "official_group_02_capture_readiness_id": backend.get("official_group_02_capture_readiness_id", ""),
        "official_group_02_capture_readiness_status": backend.get("official_group_02_capture_readiness_status", ""),
        "official_group_02_capture_blocked": backend.get("official_group_02_capture_blocked") is True,
        "official_group_02_capture_run_allowed": backend.get("official_group_02_capture_run_allowed") is True,
        "official_group_02_capture_result_recording_allowed": backend.get("official_group_02_capture_result_recording_allowed") is True,
        "received_snapshot_baseline_fingerprint_reconciled": backend.get("received_snapshot_baseline_fingerprint_reconciled") is True,
        "received_snapshot_item_fingerprint_mismatch_unresolved": backend.get("received_snapshot_item_fingerprint_mismatch_unresolved") is True,
        "source_snapshot_ref_current_for_received_zip": backend.get("source_snapshot_ref_current_for_received_zip") is True,
        "active_baseline_accepts_received_nodeids": backend.get("active_baseline_accepts_received_nodeids") is True,
        "active_baseline_refresh_schema_version": backend.get("active_baseline_refresh_schema_version", ""),
        "active_baseline_refresh_id": backend.get("active_baseline_refresh_id", ""),
        "runtime_builder_refresh_status_id": backend.get("runtime_builder_refresh_status_id", ""),
        "post_adoption_received_snapshot_reconcile_id": backend.get("post_adoption_received_snapshot_reconcile_id", ""),
        "active_baseline_update_applied_to_runtime_builders": backend.get(
            "active_baseline_update_applied_to_runtime_builders"
        ) is True,
        "source_snapshot_ref_updated_in_active_builders": backend.get("source_snapshot_ref_updated_in_active_builders") is True,
        "post_adoption_readiness_re_evaluated": backend.get("post_adoption_readiness_re_evaluated") is True,
        "received_snapshot_blocker_refs": dedupe_identifiers(backend.get("received_snapshot_blocker_refs"), limit=40, max_length=180),
        "received_snapshot_required_followup_fixes": dedupe_identifiers(backend.get("received_snapshot_required_followup_fixes"), limit=80, max_length=180),
        "real_device_submit_confirmed": real_device.get("real_device_submit_confirmed") is True,
        "real_device_submit_modal_readfeel_verified": real_device.get("status") == "verified",
        "full_backend_suite_green_confirmed": backend.get("full_backend_suite_green_confirmed") is True,
        "full_backend_suite_green_claim_allowed": False,
        "split_green_is_full_backend_suite_green": False,
        "split_green_promoted_to_full_suite_green": False,
        "unresolved_red_refs": unresolved_red_refs,
        "unresolved_hold_refs": unresolved_hold_refs,
        "release_blockers": dedupe_identifiers([*unresolved_red_refs, *unresolved_hold_refs], limit=120, max_length=120),
        "required_followup_fixes": dedupe_identifiers(
            [
                "real_device_submit_modal_readfeel_unverified" if "P7-HOLD-003" in unresolved_hold_refs else "",
                "full_backend_suite_green_unconfirmed" if "P7-HOLD-004" in unresolved_hold_refs else "",
                *backend.get("hold004_required_followup_fixes", []),
                *backend.get("hold004_step5_required_followup_fixes", []),
                *backend.get("received_snapshot_required_followup_fixes", []),
                P7_HOLD004_RECEIVED_SNAPSHOT_ITEM_FINGERPRINT_MISMATCH_BLOCKER_REF
                if backend.get("received_snapshot_item_fingerprint_mismatch_unresolved") is True
                else "",
                "positive_public_shape_target_green_pending_full_suite"
                if backend.get("hold004_positive_public_shape_target_green_confirmed") is True
                else "",
                *backend.get("hold004_step5_required_followup_fixes", []),
            ],
            limit=80,
            max_length=160,
        ),
        "manual_hold_boundary": {
            "automated_test_green_can_close_real_device_hold": False,
            "split_green_can_close_full_suite_hold": False,
            "p7_complete_claim_allowed": False,
            "p8_start_allowed": False,
            "release_allowed": False,
            "body_free": True,
        },
        "release_allowed": False,
        "body_free": True,
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
    }
    assert_p7_r10_hold_matrix_contract(matrix)
    return matrix


def assert_p7_r10_hold_matrix_contract(matrix: Mapping[str, Any]) -> bool:
    data = safe_mapping(matrix)
    if data.get("schema_version") != P7_R10_HOLD_MATRIX_SCHEMA_VERSION:
        raise ValueError("unexpected P7 R10 hold matrix schema_version")
    if data.get("phase") != P7_PHASE or data.get("scope") != P7_R10_HOLD_MATRIX_SCOPE:
        raise ValueError("unexpected P7 R10 hold matrix phase/scope")
    if data.get("real_device_check_schema_version") != P7_REAL_DEVICE_MODAL_READFEEL_CHECK_SCHEMA_VERSION:
        raise ValueError("P7 R10 hold matrix must reference the real-device check schema")
    if data.get("real_device_modal_readfeel_check_schema_version") != P7_REAL_DEVICE_MODAL_READFEEL_CHECK_SCHEMA_VERSION:
        raise ValueError("P7 R10 hold matrix must expose the real-device modal read-feel check schema")
    if data.get("backend_suite_split_matrix_schema_version") != P7_BACKEND_SUITE_SPLIT_MATRIX_SCHEMA_VERSION:
        raise ValueError("P7 R10 hold matrix must reference the backend-suite split matrix schema")
    if data.get("backend_suite_execution_summary_connected") is True:
        if data.get("backend_suite_execution_summary_schema_version") != P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_SCHEMA_VERSION:
            raise ValueError("P7 R10 hold matrix execution summary schema_version mismatch")
        if not isinstance(data.get("fine_group_statuses"), Mapping) or not data.get("fine_group_statuses"):
            raise ValueError("P7 R10 hold matrix must expose fine group statuses when execution summary is connected")
        if data.get("backend_suite_execution_summary_collect_baseline_id") != P7_HOLD004_BACKEND_COLLECT_BASELINE_ID:
            raise ValueError("P7 R10 hold matrix must connect the current collect baseline id")
        if data.get("backend_suite_execution_summary_inventory_id") != P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID:
            raise ValueError("P7 R10 hold matrix must connect the current group inventory id")
        if data.get("backend_suite_execution_summary_plan_id") != P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID:
            raise ValueError("P7 R10 hold matrix must connect the current execution plan id")
        for key in ("current_collect_baseline_connected", "current_group_inventory_connected", "current_execution_plan_connected", "old_baseline_not_used_as_current", "backend_suite_group_02_count_current"):
            if data.get(key) is not True:
                raise ValueError(f"P7 R10 hold matrix must keep {key}=true")
        connection = safe_mapping(data.get("matrix_current_baseline_connection"))
        if connection.get("collect_baseline_id") != P7_HOLD004_BACKEND_COLLECT_BASELINE_ID:
            raise ValueError("P7 R10 hold matrix current baseline connection collect id mismatch")
        if connection.get("old_baseline_used_as_current") is not False:
            raise ValueError("P7 R10 hold matrix must not use old baseline as current")
    if data.get("red_closure_classification_connected") is True:
        if data.get("red_closure_classification_schema_version") != P7_RED_CLOSURE_CLASSIFICATION_MATRIX_SCHEMA_VERSION:
            raise ValueError("P7 R10 hold matrix RED closure schema_version mismatch")
        if data.get("red_closure_source_e2e_isolation_schema_version") != P7_E2E_ISOLATION_RESULT_SCHEMA_VERSION:
            raise ValueError("P7 R10 hold matrix RED closure E2E source schema_version mismatch")
    if data.get("release_allowed") is not False or data.get("body_free") is not True:
        raise ValueError("P7 R10 hold matrix must stay body-free and release-closed")
    if data.get("full_backend_suite_green_confirmed") is not False:
        raise ValueError("P7 R10 hold matrix must keep full_backend_suite_green_confirmed=false")
    if data.get("full_backend_suite_green_claim_allowed") is not False:
        raise ValueError("P7 R10 hold matrix must keep full_backend_suite_green_claim_allowed=false")
    readiness_schema_version = clean_identifier(
        data.get("official_group_02_capture_readiness_schema_version"), default="", max_length=160
    )
    if readiness_schema_version:
        if readiness_schema_version not in P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_ALLOWED_SCHEMA_VERSIONS:
            raise ValueError("P7 R10 hold matrix official group_02 readiness schema_version mismatch")
        readiness_after_refresh = readiness_schema_version == P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_SCHEMA_VERSION_V2
        if data.get("received_snapshot_item_fingerprint_mismatch_unresolved") is True:
            if data.get("official_group_02_capture_readiness_status") != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_BLOCKED_BY_ITEM_FINGERPRINT_MISMATCH:
                raise ValueError("P7 R10 hold matrix must expose unresolved received snapshot item mismatch")
            if data.get("official_group_02_capture_blocked") is not True:
                raise ValueError("P7 R10 hold matrix must keep official group_02 capture blocked")
            if data.get("official_group_02_capture_run_allowed") is not False:
                raise ValueError("P7 R10 hold matrix must not allow official capture run while mismatch is unresolved")
            if data.get("official_group_02_capture_result_recording_allowed") is not False:
                raise ValueError("P7 R10 hold matrix must not allow official capture result recording while mismatch is unresolved")
            if P7_HOLD004_RECEIVED_SNAPSHOT_ITEM_FINGERPRINT_MISMATCH_BLOCKER_REF not in dedupe_identifiers(
                data.get("received_snapshot_blocker_refs"), limit=40, max_length=180
            ):
                raise ValueError("P7 R10 hold matrix must carry received snapshot item mismatch blocker")
        if readiness_after_refresh:
            if data.get("official_group_02_capture_readiness_status") != P7_HOLD004_OFFICIAL_GROUP02_CAPTURE_READINESS_STATUS_READY:
                raise ValueError("P7 R10 hold matrix after-refresh group_02 readiness must be READY")
            if data.get("received_snapshot_item_fingerprint_mismatch_unresolved") is not False:
                raise ValueError("P7 R10 hold matrix after-refresh readiness must resolve item mismatch")
            if data.get("received_snapshot_baseline_fingerprint_reconciled") is not True:
                raise ValueError("P7 R10 hold matrix after-refresh readiness must carry reconciled baseline")
            if data.get("official_group_02_capture_blocked") is not False:
                raise ValueError("P7 R10 hold matrix after-refresh readiness must unblock capture run")
            if data.get("official_group_02_capture_run_allowed") is not True:
                raise ValueError("P7 R10 hold matrix after-refresh readiness must allow capture run")
            if data.get("official_group_02_capture_result_recording_allowed") is not True:
                raise ValueError("P7 R10 hold matrix after-refresh readiness must allow result recording")
            if data.get("active_baseline_update_applied_to_runtime_builders") is not True:
                raise ValueError("P7 R10 hold matrix must carry runtime-builder refresh application")
            if data.get("source_snapshot_ref_updated_in_active_builders") is not True:
                raise ValueError("P7 R10 hold matrix must carry active builder source refresh")
            if data.get("official_group_02_capture_green_confirmed") is True:
                raise ValueError("P7 R10 hold matrix readiness must not claim group_02 green")
    if data.get("split_green_is_full_backend_suite_green") is not False:
        raise ValueError("P7 R10 hold matrix must not equate split green with full-suite green")
    if data.get("split_green_promoted_to_full_suite_green") is not False:
        raise ValueError("P7 R10 hold matrix must not promote split green to full-suite green")
    if data.get("split_all_groups_green_confirmed") is True:
        if data.get("full_backend_suite_green_confirmed") is not False:
            raise ValueError("P7 R10 split all-groups green must not become full backend suite green")
    red003_ref = P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID
    unresolved_red_refs_for_red003 = set(dedupe_identifiers(data.get("unresolved_red_refs"), limit=80, max_length=160))
    closed_red_refs_for_red003 = set(dedupe_identifiers(data.get("closed_red_refs"), limit=80, max_length=160))
    if data.get("product_quality_connection_timeout_closed") is True:
        if red003_ref not in closed_red_refs_for_red003 or red003_ref in unresolved_red_refs_for_red003:
            raise ValueError("P7 R10 hold matrix must align closed P7-RED-003 with backend split matrix")
        if data.get("product_quality_connection_e2e_status") != "closed_confirmed":
            raise ValueError("P7 R10 hold matrix must expose Product Quality Connection E2E as closed_confirmed")
    elif data.get("red_closure_classification_connected") is True and red003_ref not in unresolved_red_refs_for_red003:
        raise ValueError("P7 R10 hold matrix must keep P7-RED-003 unresolved when structured material has not closed it")
    if data.get("real_device_submit_modal_readfeel_verified") is True and data.get("real_device_submit_confirmed") is not True:
        raise ValueError("P7 R10 hold matrix verified modal read-feel requires real-device submit confirmation")
    hold_refs = set(dedupe_identifiers(data.get("unresolved_hold_refs"), limit=80, max_length=120))
    if data.get("real_device_submit_confirmed") is not True and "P7-HOLD-003" not in hold_refs:
        raise ValueError("P7 R10 hold matrix must keep P7-HOLD-003 when real-device submit is unverified")
    if "P7-HOLD-004" not in hold_refs:
        raise ValueError("P7 R10 hold matrix must keep P7-HOLD-004")
    if data.get("hold004_phase16_classified_red_present") is True:
        if data.get("hold004_phase16_candidate_boundary_registered") is not True:
            raise ValueError("P7 R10 HOLD matrix must preserve classified HOLD-004 candidate boundary")
        if "phase16_complete_composer_candidate_boundary" not in dedupe_identifiers(
            data.get("hold004_required_followup_fixes"),
            limit=80,
            max_length=160,
        ):
            raise ValueError("P7 R10 HOLD matrix must expose the Phase16 candidate-boundary follow-up")
    if data.get("hold004_positive_public_shape_boundary_schema_version"):
        if data.get("hold004_positive_public_shape_boundary_schema_version") != P7_HOLD004_POSITIVE_PUBLIC_SHAPE_SCHEMA_VERSION:
            raise ValueError("P7 R10 HOLD matrix positive public shape schema_version mismatch")
        if data.get("hold004_positive_public_shape_boundary_status") != P7_HOLD004_POSITIVE_PUBLIC_SHAPE_REPAIRED_STATUS:
            raise ValueError("P7 R10 HOLD matrix must keep positive public shape as repaired-pending-full-suite")
        for key in (
            "hold004_positive_public_shape_target_green_confirmed",
            "hold004_positive_public_shape_repaired_target_green_pending_full_suite",
            "hold004_positive_public_shape_true_self_denial_regression_preserved",
            "hold004_positive_public_shape_emergency_regression_preserved",
            "hold004_positive_public_shape_support_required_regression_preserved",
            "hold004_positive_public_shape_input_material_bundle_confirmed",
            "hold004_positive_public_shape_public_e2e_labelled_two_stage_confirmed",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7 R10 HOLD matrix must keep {key}=True")
        if data.get("hold004_positive_public_shape_full_backend_suite_green_confirmed") is not False:
            raise ValueError("P7 R10 HOLD matrix must not promote positive target green to full-suite green")
        if data.get("hold004_positive_public_shape_release_allowed") is not False:
            raise ValueError("P7 R10 HOLD matrix must keep positive public shape release_allowed=false")
    if data.get("hold004_step5_material_connection_schema_version"):
        if data.get("hold004_step5_material_connection_schema_version") != P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_SCHEMA_VERSION:
            raise ValueError("P7 R10 HOLD matrix Step5 material schema_version mismatch")
        if data.get("hold004_step5_candidate_gate_red_classified") is not True:
            raise ValueError("P7 R10 HOLD matrix must classify the Step5 candidate-gate material")
        if "step5_display_binding_contract_consistency" not in dedupe_identifiers(
            data.get("hold004_step5_required_followup_fixes"),
            limit=80,
            max_length=160,
        ):
            raise ValueError("P7 R10 HOLD matrix must expose the Step5 display-binding follow-up")
        if data.get("hold004_step5_full_backend_suite_green_confirmed") is not False:
            raise ValueError("P7 R10 HOLD matrix must not promote Step5 material to full-suite green")
        if data.get("hold004_step5_release_allowed") is not False:
            raise ValueError("P7 R10 HOLD matrix must keep Step5 release_allowed=false")
        if data.get("hold004_step5_display_binding_red_present") is True and data.get("hold004_step5_candidate_gate_red_closed") is not True:
            if P7_HOLD004_STEP5_RED_ID not in dedupe_identifiers(data.get("hold004_step5_unresolved_red_refs"), limit=40, max_length=160):
                raise ValueError("P7 R10 HOLD matrix must keep unresolved Step5 red visible")
    boundary = safe_mapping(data.get("manual_hold_boundary"))
    for key in (
        "automated_test_green_can_close_real_device_hold",
        "split_green_can_close_full_suite_hold",
        "p7_complete_claim_allowed",
        "p8_start_allowed",
        "release_allowed",
    ):
        if boundary.get(key) is not False:
            raise ValueError(f"P7 R10 manual hold boundary must keep {key}=False")
    if boundary.get("body_free") is not True:
        raise ValueError("P7 R10 manual hold boundary must be body-free")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_r10_hold_matrix.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_r10_hold_matrix.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r10_hold_matrix")
    return True


def build_p7_real_device_full_backend_hold_matrix(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Compatibility alias for the R10 composite HOLD matrix."""

    return build_p7_r10_hold_matrix(*args, **kwargs)


def assert_p7_real_device_full_backend_hold_matrix_contract(matrix: Mapping[str, Any]) -> bool:
    """Compatibility alias for the R10 composite HOLD matrix contract."""

    return assert_p7_r10_hold_matrix_contract(matrix)


def build_p7_hold_matrix(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return build_p7_r10_hold_matrix(*args, **kwargs)


def assert_p7_hold_matrix_contract(matrix: Mapping[str, Any]) -> bool:
    return assert_p7_r10_hold_matrix_contract(matrix)


__all__ = [
    "P7_BACKEND_SUITE_MATRIX_ID",
    "P7_BACKEND_SUITE_SPLIT_MATRIX_SCHEMA_VERSION",
    "P7_HOLD_MATRIX_SCHEMA_VERSION",
    "P7_R10_HOLD_MATRIX_SCHEMA_VERSION",
    "P7_R10_HOLD_MATRIX_SCOPE",
    "P7_R10_HOLD_MATRIX_STEP",
    "P7_REAL_DEVICE_CHECK_ID",
    "P7_REAL_DEVICE_MODAL_READFEEL_CHECK_SCHEMA_VERSION",
    "assert_p7_backend_suite_split_matrix_contract",
    "assert_p7_hold_matrix_contract",
    "assert_p7_r10_hold_matrix_contract",
    "assert_p7_real_device_full_backend_hold_matrix_contract",
    "assert_p7_real_device_modal_readfeel_check_contract",
    "build_p7_backend_suite_split_matrix",
    "build_p7_hold_matrix",
    "build_p7_r10_hold_matrix",
    "build_p7_real_device_full_backend_hold_matrix",
    "build_p7_real_device_modal_readfeel_check",
]
