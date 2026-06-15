# -*- coding: utf-8 -*-
"""P7-HOLD-004 R16 current-snapshot minimal group-execution order material.

R16 does not execute pytest and does not store terminal output.  It reconnects
the small-to-large capture order to the refreshed 20260615 collect baseline,
group inventory, and execution plan, so a FAIL/TIMEOUT can be materialized
before any later group is treated as confirmed green.
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
    P7_HOLD004_BACKEND_SUITE_DEFAULT_PYTEST_ARGS_ID,
    P7_HOLD004_BACKEND_SUITE_EXECUTION_MODE,
    P7_HOLD004_BACKEND_SUITE_EXECUTION_ORDER,
    P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID,
    P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_SCHEMA_VERSION,
    P7_HOLD004_BACKEND_SUITE_GROUP_DEFINITIONS,
    P7_HOLD004_BACKEND_SUITE_GROUP_IDS,
    P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID,
    P7_HOLD004_BACKEND_SUITE_PYTEST_ENV_ID,
    P7_HOLD004_BACKEND_SUITE_TOTAL_BATCH_COUNT,
    assert_p7_hold004_backend_suite_execution_plan_contract,
    build_p7_hold004_backend_suite_execution_plan,
)
from emlis_ai_p7_hold004_backend_suite_split_consistency import (
    P7_HOLD004_BACKEND_COLLECT_BASELINE_ID,
    P7_HOLD004_BACKEND_SUITE_HOLD_ID,
)
from emlis_ai_p7_hold004_matrix_consistency_report import (
    P7_HOLD004_MATRIX_CONSISTENCY_REPORT_SCHEMA_VERSION,
    assert_p7_hold004_matrix_consistency_report_contract,
    build_p7_hold004_matrix_consistency_report,
)

P7_HOLD004_GROUP_EXECUTION_MINIMAL_ORDER_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.group_execution_minimal_order.v1"
)
P7_HOLD004_GROUP_EXECUTION_MINIMAL_ORDER_STEP: Final = (
    "P7-HOLD-004_CurrentSnapshotBaselineReconcile_R16_20260615"
)
P7_HOLD004_GROUP_EXECUTION_MINIMAL_ORDER_ID: Final = (
    "p7_hold004_group_execution_minimal_confirmation_order_20260615_current_snapshot"
)
P7_HOLD004_GROUP_EXECUTION_MINIMAL_ORDER_SOURCE_SNAPSHOT_REF: Final = "mashos-api(147).zip"

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


def _definition_by_group_id() -> dict[str, dict[str, Any]]:
    return {clean_identifier(definition.get("group_id"), max_length=120): dict(definition) for definition in P7_HOLD004_BACKEND_SUITE_GROUP_DEFINITIONS}


def _plan_groups_by_id(plan: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        clean_identifier(group.get("group_id"), max_length=120): dict(safe_mapping(group))
        for group in listify(safe_mapping(plan).get("groups"))
    }


def _execution_records(plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    groups_by_id = _plan_groups_by_id(plan)
    definitions = _definition_by_group_id()
    records: list[dict[str, Any]] = []
    for index, group_id in enumerate(P7_HOLD004_BACKEND_SUITE_EXECUTION_ORDER, start=1):
        plan_group = safe_mapping(groups_by_id.get(group_id))
        definition = safe_mapping(definitions.get(group_id))
        batch_ids = dedupe_identifiers(plan_group.get("batch_ids"), limit=20, max_length=160)
        records.append(
            {
                "execution_order_index": index,
                "group_id": group_id,
                "owner_layer": clean_identifier(plan_group.get("owner_layer") or definition.get("owner_layer"), max_length=120),
                "assignment_order": _coerce_non_negative_int(plan_group.get("assignment_order") or definition.get("assignment_order")),
                "file_count": _coerce_non_negative_int(plan_group.get("file_count") or definition.get("file_count")),
                "test_item_count": _coerce_non_negative_int(plan_group.get("test_item_count") or definition.get("test_item_count")),
                "batch_count": _coerce_non_negative_int(plan_group.get("batch_count") or definition.get("planned_batch_count"), default=1),
                "batch_ids": batch_ids,
                "timeout_budget_sec": _coerce_non_negative_int(
                    plan_group.get("timeout_budget_sec") or definition.get("timeout_budget_sec"),
                    default=120,
                ),
                "capture_run_maxfail_1": True,
                "confirmation_run_maxfail_1": False,
                "run_kind_first": "capture_run",
                "run_kind_after_repair": "confirmation_run",
                "failure_or_timeout_policy": "materialize_first_red_or_timeout_then_stop_green_claims",
                "can_claim_group_green_only_after_recorded_pass": True,
                "can_claim_full_backend_suite_green": False,
                "split_green_can_close_p7_hold004": False,
                "terminal_output_retained": False,
                "execution_result_recorded": False,
                "release_allowed": False,
                "body_free": True,
            }
        )
    return records


def build_p7_hold004_group_execution_minimal_order(
    *,
    execution_plan: Mapping[str, Any] | None = None,
    matrix_consistency_report: Mapping[str, Any] | None = None,
    material_id: Any = P7_HOLD004_GROUP_EXECUTION_MINIMAL_ORDER_ID,
) -> dict[str, Any]:
    """Build R11 body-free material for the minimum safe group-run order."""

    plan = safe_mapping(execution_plan) if execution_plan is not None else build_p7_hold004_backend_suite_execution_plan()
    assert_p7_hold004_backend_suite_execution_plan_contract(plan)
    consistency = (
        safe_mapping(matrix_consistency_report)
        if matrix_consistency_report is not None
        else build_p7_hold004_matrix_consistency_report()
    )
    assert_p7_hold004_matrix_consistency_report_contract(consistency)

    records = _execution_records(plan)
    material = {
        "schema_version": P7_HOLD004_GROUP_EXECUTION_MINIMAL_ORDER_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_GROUP_EXECUTION_MINIMAL_ORDER_STEP,
        "implementation_step": P7_HOLD004_GROUP_EXECUTION_MINIMAL_ORDER_STEP,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "material_id": clean_identifier(material_id, default=P7_HOLD004_GROUP_EXECUTION_MINIMAL_ORDER_ID, max_length=160),
        "source_mode": P7_SOURCE_MODE,
        "source_snapshot_ref": P7_HOLD004_GROUP_EXECUTION_MINIMAL_ORDER_SOURCE_SNAPSHOT_REF,
        "git_checked": P7_GIT_CHECKED,
        "collect_baseline_id": P7_HOLD004_BACKEND_COLLECT_BASELINE_ID,
        "inventory_id": P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID,
        "execution_plan_id": P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID,
        "execution_plan_schema_version": P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_SCHEMA_VERSION,
        "matrix_consistency_report_schema_version": consistency.get("schema_version"),
        "matrix_consistency_report_id": clean_identifier(consistency.get("report_id"), max_length=160),
        "matrix_consistency_status": clean_identifier(consistency.get("consistency_status"), default="", max_length=80),
        "execution_mode": P7_HOLD004_BACKEND_SUITE_EXECUTION_MODE,
        "pytest_env_id": P7_HOLD004_BACKEND_SUITE_PYTEST_ENV_ID,
        "default_pytest_args_id": P7_HOLD004_BACKEND_SUITE_DEFAULT_PYTEST_ARGS_ID,
        "group_count": len(records),
        "total_batch_count": sum(_coerce_non_negative_int(record.get("batch_count"), default=0) for record in records),
        "minimal_execution_order": [record["group_id"] for record in records],
        "groups": records,
        "first_capture_group_id": records[0]["group_id"] if records else "",
        "large_runtime_group_id": "group_11_emlis_runtime_other",
        "stop_on_first_fail_or_timeout": True,
        "continue_after_fail_or_timeout_requires_new_repair_plan": True,
        "subsequent_groups_not_green_when_blocked": True,
        "capture_run_and_confirmation_run_separated": True,
        "current_collect_baseline_reconciled": True,
        "previous_baseline_is_not_current": True,
        "baseline_mismatch_blocks_execution": True,
        "group_execution_started": False,
        "group_run_results_recorded": False,
        "terminal_output_retained": False,
        "raw_traceback_included": False,
        **_release_closed_boundary(),
        "unresolved_hold_refs": [P7_HOLD004_BACKEND_SUITE_HOLD_ID],
        "required_followup_fixes": dedupe_identifiers(
            [
                "execute_group_02_p7_hold004_first",
                "materialize_first_red_or_timeout_before_continuing",
                "group_11_must_run_in_batches",
                "full_backend_suite_green_unconfirmed",
                "split_green_is_not_full_backend_suite_green",
            ],
            limit=80,
            max_length=180,
        ),
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
        "body_free": True,
    }
    assert_p7_hold004_group_execution_minimal_order_contract(material)
    return material


def assert_p7_hold004_group_execution_minimal_order_contract(material: Mapping[str, Any]) -> bool:
    """Validate R11 minimal group-execution order without run-result claims."""

    data = safe_mapping(material)
    if data.get("schema_version") != P7_HOLD004_GROUP_EXECUTION_MINIMAL_ORDER_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 group execution minimal order schema_version changed")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError("P7-HOLD-004 group execution minimal order must stay in P7-HOLD-004 scope")
    if data.get("implementation_step") != P7_HOLD004_GROUP_EXECUTION_MINIMAL_ORDER_STEP:
        raise ValueError("P7-HOLD-004 group execution minimal order implementation_step changed")
    if data.get("source_mode") != P7_SOURCE_MODE or data.get("source_snapshot_ref") != P7_HOLD004_GROUP_EXECUTION_MINIMAL_ORDER_SOURCE_SNAPSHOT_REF:
        raise ValueError("P7-HOLD-004 group execution minimal order must stay on the current local snapshot")
    if data.get("git_checked") is not False:
        raise ValueError("P7-HOLD-004 group execution minimal order must not claim GitHub verification")
    if data.get("collect_baseline_id") != P7_HOLD004_BACKEND_COLLECT_BASELINE_ID:
        raise ValueError("P7-HOLD-004 group execution minimal order must use the current collect baseline")
    if data.get("inventory_id") != P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID:
        raise ValueError("P7-HOLD-004 group execution minimal order must use the current group inventory")
    if data.get("execution_plan_id") != P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID:
        raise ValueError("P7-HOLD-004 group execution minimal order must use the current execution plan")
    for key in ("current_collect_baseline_reconciled", "previous_baseline_is_not_current", "baseline_mismatch_blocks_execution"):
        if data.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 group execution minimal order must keep {key}=true")
    if data.get("execution_plan_schema_version") != P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 group execution minimal order must source the R3 execution plan")
    if data.get("matrix_consistency_report_schema_version") != P7_HOLD004_MATRIX_CONSISTENCY_REPORT_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 group execution minimal order must source the R10 matrix consistency report")
    if data.get("execution_mode") != P7_HOLD004_BACKEND_SUITE_EXECUTION_MODE:
        raise ValueError("P7-HOLD-004 group execution minimal order execution_mode changed")
    if data.get("pytest_env_id") != P7_HOLD004_BACKEND_SUITE_PYTEST_ENV_ID:
        raise ValueError("P7-HOLD-004 group execution minimal order pytest_env_id changed")
    if data.get("default_pytest_args_id") != P7_HOLD004_BACKEND_SUITE_DEFAULT_PYTEST_ARGS_ID:
        raise ValueError("P7-HOLD-004 group execution minimal order pytest args changed")
    if data.get("minimal_execution_order") != list(P7_HOLD004_BACKEND_SUITE_EXECUTION_ORDER):
        raise ValueError("P7-HOLD-004 group execution minimal order changed")
    if data.get("first_capture_group_id") != "group_02_p7_hold004":
        raise ValueError("P7-HOLD-004 group execution minimal order must start from group_02")
    if data.get("group_count") != len(P7_HOLD004_BACKEND_SUITE_GROUP_IDS):
        raise ValueError("P7-HOLD-004 group execution minimal order group_count changed")
    if data.get("total_batch_count") != P7_HOLD004_BACKEND_SUITE_TOTAL_BATCH_COUNT:
        raise ValueError("P7-HOLD-004 group execution minimal order total_batch_count changed")
    for key in (
        "stop_on_first_fail_or_timeout",
        "continue_after_fail_or_timeout_requires_new_repair_plan",
        "subsequent_groups_not_green_when_blocked",
        "capture_run_and_confirmation_run_separated",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 group execution minimal order must keep {key}=true")
    for key in ("group_execution_started", "group_run_results_recorded", "terminal_output_retained", "raw_traceback_included"):
        if data.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 group execution minimal order must keep {key}=false")
    for key in _RELEASE_CLOSED_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"P7-HOLD-004 group execution minimal order must keep {key}=false")

    groups = [safe_mapping(group) for group in listify(data.get("groups"))]
    if len(groups) != len(P7_HOLD004_BACKEND_SUITE_EXECUTION_ORDER):
        raise ValueError("P7-HOLD-004 group execution minimal order groups length mismatch")
    for index, group in enumerate(groups, start=1):
        expected_group_id = P7_HOLD004_BACKEND_SUITE_EXECUTION_ORDER[index - 1]
        group_id = clean_identifier(group.get("group_id"), max_length=120)
        if group_id != expected_group_id:
            raise ValueError("P7-HOLD-004 group execution minimal order group order mismatch")
        if group.get("execution_order_index") != index:
            raise ValueError(f"P7-HOLD-004 group execution minimal order {group_id}.execution_order_index changed")
        definition = safe_mapping(_definition_by_group_id().get(group_id))
        if group.get("file_count") != definition.get("file_count"):
            raise ValueError(f"P7-HOLD-004 group execution minimal order {group_id}.file_count changed")
        if group.get("test_item_count") != definition.get("test_item_count"):
            raise ValueError(f"P7-HOLD-004 group execution minimal order {group_id}.test_item_count changed")
        batch_count = _coerce_non_negative_int(group.get("batch_count"), default=0)
        if batch_count < 1:
            raise ValueError(f"P7-HOLD-004 group execution minimal order {group_id} missing batch_count")
        expected_batch_ids = [f"{group_id}_batch_{batch_index:02d}" for batch_index in range(1, batch_count + 1)]
        if group.get("batch_ids") != expected_batch_ids:
            raise ValueError(f"P7-HOLD-004 group execution minimal order {group_id}.batch_ids changed")
        if group_id == "group_11_emlis_runtime_other" and batch_count <= 1:
            raise ValueError("P7-HOLD-004 group execution minimal order must keep group_11 batched")
        for key, expected in (
            ("capture_run_maxfail_1", True),
            ("confirmation_run_maxfail_1", False),
            ("can_claim_group_green_only_after_recorded_pass", True),
            ("can_claim_full_backend_suite_green", False),
            ("split_green_can_close_p7_hold004", False),
            ("terminal_output_retained", False),
            ("execution_result_recorded", False),
            ("release_allowed", False),
            ("body_free", True),
        ):
            if group.get(key) is not expected:
                raise ValueError(f"P7-HOLD-004 group execution minimal order {group_id} must keep {key}={expected}")
    hold_refs = set(dedupe_identifiers(data.get("unresolved_hold_refs"), limit=80, max_length=120))
    if P7_HOLD004_BACKEND_SUITE_HOLD_ID not in hold_refs:
        raise ValueError("P7-HOLD-004 group execution minimal order must keep P7-HOLD-004 unresolved")
    followups = set(dedupe_identifiers(data.get("required_followup_fixes"), limit=120, max_length=180))
    for required in (
        "materialize_first_red_or_timeout_before_continuing",
        "group_11_must_run_in_batches",
        "full_backend_suite_green_unconfirmed",
    ):
        if required not in followups:
            raise ValueError(f"P7-HOLD-004 group execution minimal order missing followup {required}")
    if data.get("body_free") is not True:
        raise ValueError("P7-HOLD-004 group execution minimal order must be body_free=true")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_hold004_group_execution_minimal_order.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_hold004_group_execution_minimal_order.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_hold004_group_execution_minimal_order")
    return True


__all__ = [
    "P7_HOLD004_GROUP_EXECUTION_MINIMAL_ORDER_ID",
    "P7_HOLD004_GROUP_EXECUTION_MINIMAL_ORDER_SCHEMA_VERSION",
    "P7_HOLD004_GROUP_EXECUTION_MINIMAL_ORDER_STEP",
    "assert_p7_hold004_group_execution_minimal_order_contract",
    "build_p7_hold004_group_execution_minimal_order",
]
