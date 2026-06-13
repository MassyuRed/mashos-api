# -*- coding: utf-8 -*-
"""P7-3 runner plan, command matrix, and timeout budget.

P7 runner planning is split into small contract groups and heavy isolated red
sources.  A timeout or hang is never green, heavy E2E tests do not participate in
P7 core pass conditions, and the plan never claims full backend-suite green or
release readiness.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import (
    P7_INITIAL_RED_IDS,
    P7_PHASE,
    P7_RED_LEDGER_SCHEMA_VERSION,
    assert_false_markers,
    assert_p7_no_body_payload_or_contract_mutation,
    body_free_flags,
    clean_identifier,
    dedupe_identifiers,
    public_contract_flags,
    safe_mapping,
)
from emlis_ai_p7_module_inventory import (
    P7_MODULE_INVENTORY_SCHEMA_VERSION,
    assert_p7_module_inventory_contract,
    build_p7_module_inventory,
)
from emlis_ai_p7_red_ledger import assert_p7_red_ledger_contract, build_p7_red_ledger
from emlis_ai_p7_timeout_isolation import (
    P7_E2E_ISOLATION_RESULT_SCHEMA_VERSION,
    assert_p7_e2e_isolation_result_contract,
    build_p7_connection_e2e_timeout_isolation_result,
)

P7_RUNNER_PLAN_SCHEMA_VERSION: Final = "cocolon.emlis.p7.runner_plan.v1"
P7_RUNNER_PLAN_ID: Final = "P7-3_runner_plan_command_matrix_timeout_budget_20260612"
P7_RUNNER_PLAN_SCOPE: Final = "P7_ProductQualityRunner_split_and_isolated_validation"
P7_RUNNER_PLAN_STEP: Final = "P7-3_RunnerPlanCommandMatrixTimeoutBudget_20260612"

P7_GROUP_KIND_CORE: Final = "p7_core"
P7_GROUP_KIND_EXISTING_REUSE: Final = "existing_reuse"
P7_GROUP_KIND_HEAVY_ISOLATED_RED: Final = "heavy_isolated_red"
P7_GROUP_KIND_MANUAL_HANDOFF: Final = "manual_handoff"

P7_GREEN_SCOPE_GROUP_ONLY: Final = "group_only"
P7_GREEN_SCOPE_ISOLATED_RED_ONLY: Final = "isolated_red_only"
P7_GREEN_SCOPE_MANUAL_ONLY: Final = "manual_only"

_HEAVY_E2E_TEST_FILES: Final[frozenset[str]] = frozenset(
    {
        "tests/test_emlis_ai_complete_product_quality_positive_recovery_e2e.py",
        "tests/test_emlis_ai_complete_product_quality_connection_e2e.py",
    }
)
_ALLOWED_GROUP_KINDS: Final[frozenset[str]] = frozenset(
    {P7_GROUP_KIND_CORE, P7_GROUP_KIND_EXISTING_REUSE, P7_GROUP_KIND_HEAVY_ISOLATED_RED, P7_GROUP_KIND_MANUAL_HANDOFF}
)
_ALLOWED_GREEN_SCOPES: Final[frozenset[str]] = frozenset(
    {P7_GREEN_SCOPE_GROUP_ONLY, P7_GREEN_SCOPE_ISOLATED_RED_ONLY, P7_GREEN_SCOPE_MANUAL_ONLY}
)
_ALLOWED_REPOSITORIES: Final[frozenset[str]] = frozenset({"mashos-api/ai", "Cocolon", "docs"})
_ALLOWED_COMMAND_KINDS: Final[frozenset[str]] = frozenset({"pytest", "npm", "manual_review"})


def _pytest_command(test_files: Sequence[str], *, timeout_budget_sec: int) -> str:
    joined = " ".join(dedupe_identifiers(test_files, limit=80, max_length=220))
    return f"PYTHONPATH=services/ai_inference timeout {timeout_budget_sec}s pytest -q --tb=short {joined}".strip()


def _group(
    group_id: str,
    *,
    group_kind: str,
    test_files: Sequence[str],
    timeout_budget_sec: int,
    green_claim_scope: str,
    red_refs: Sequence[str] = (),
    required_inventory_ids: Sequence[str] = (),
    mainline_pass_condition: bool,
    expected_result_kind: str,
) -> dict[str, Any]:
    files = dedupe_identifiers(test_files, limit=80, max_length=220)
    command = _pytest_command(files, timeout_budget_sec=timeout_budget_sec)
    return {
        "group_id": clean_identifier(group_id, max_length=120),
        "group_kind": clean_identifier(group_kind, max_length=64),
        "repository": "mashos-api/ai",
        "working_directory": "mashos-api/ai",
        "command_kind": "pytest",
        "command": command,
        "test_files": files,
        "timeout_budget_sec": int(timeout_budget_sec),
        "green_claim_scope": clean_identifier(green_claim_scope, max_length=64),
        "mainline_pass_condition": mainline_pass_condition is True,
        "timeout_hang_is_green": False,
        "full_backend_suite_green_claim_allowed": False,
        "combined_timeout_is_green": False,
        "red_refs": dedupe_identifiers(red_refs, limit=8),
        "required_inventory_ids": dedupe_identifiers(required_inventory_ids, limit=20, max_length=160),
        "expected_result_kind": clean_identifier(expected_result_kind, max_length=100),
        "body_free": True,
        "release_allowed": False,
    }


def _plan_groups() -> list[dict[str, Any]]:
    return [
        _group(
            "p7_core_contract",
            group_kind=P7_GROUP_KIND_CORE,
            test_files=(
                "tests/test_emlis_ai_p7_handoff_normalizer_20260612.py",
                "tests/test_emlis_ai_p7_red_ledger_20260612.py",
                "tests/test_emlis_ai_p7_module_inventory_20260612.py",
                "tests/test_emlis_ai_p7_runner_plan_20260612.py",
                "tests/test_emlis_ai_p7_event_bridge_20260612.py",
                "tests/test_emlis_ai_p7_evaluation_matrix_20260612.py",
                "tests/test_emlis_ai_p7_blind_qa_material_20260612.py",
                "tests/test_emlis_ai_p7_long_run_gate_handoff_20260612.py",
                "tests/test_emlis_ai_p7_release_handoff_20260612.py",
                "tests/test_emlis_ai_p7_validation_matrix_20260612.py",
            ),
            timeout_budget_sec=120,
            green_claim_scope=P7_GREEN_SCOPE_GROUP_ONLY,
            required_inventory_ids=(),
            mainline_pass_condition=True,
            expected_result_kind="p7_core_contract_green_only",
        ),
        _group(
            "existing_p7_reuse_contract",
            group_kind=P7_GROUP_KIND_EXISTING_REUSE,
            test_files=(
                "tests/test_emlis_ai_product_quality_measurement_event.py",
                "tests/test_emlis_ai_product_quality_measurement_runner.py",
                "tests/test_emlis_ai_product_quality_blocker_matrix.py",
                "tests/test_emlis_ai_product_readfeel_phase11_long_run_product_gate.py",
                "tests/test_emlis_ai_product_release_decision.py",
                "tests/test_emlis_ai_p5_p6_split_test_matrix_handoff_r9_20260612.py",
            ),
            timeout_budget_sec=180,
            green_claim_scope=P7_GREEN_SCOPE_GROUP_ONLY,
            required_inventory_ids=(
                "product_quality_measurement_event",
                "product_quality_measurement_runner",
                "product_quality_blocker_matrix",
                "product_readfeel_long_run_product_gate",
                "product_release_decision",
                "p5_p6_split_test_matrix_handoff",
            ),
            mainline_pass_condition=True,
            expected_result_kind="existing_reuse_contract_green_only_not_p7_complete",
        ),
        _group(
            "heavy_isolated_positive_recovery_red",
            group_kind=P7_GROUP_KIND_HEAVY_ISOLATED_RED,
            test_files=("tests/test_emlis_ai_complete_product_quality_positive_recovery_e2e.py",),
            timeout_budget_sec=120,
            green_claim_scope=P7_GREEN_SCOPE_ISOLATED_RED_ONLY,
            red_refs=("P7-RED-001", "P7-RED-002"),
            required_inventory_ids=("positive_recovery_e2e_red_source",),
            mainline_pass_condition=False,
            expected_result_kind="red_or_failed_preserved_not_core_green",
        ),
        _group(
            "heavy_isolated_product_quality_connection_timeout",
            group_kind=P7_GROUP_KIND_HEAVY_ISOLATED_RED,
            test_files=("tests/test_emlis_ai_complete_product_quality_connection_e2e.py",),
            timeout_budget_sec=120,
            green_claim_scope=P7_GREEN_SCOPE_ISOLATED_RED_ONLY,
            red_refs=("P7-RED-003",),
            required_inventory_ids=(
                "complete_product_quality_measurement_connection",
                "complete_product_quality_connection_e2e_red_source",
            ),
            mainline_pass_condition=False,
            expected_result_kind="timeout_or_red_preserved_not_core_green",
        ),
    ]


def build_p7_runner_plan(
    *,
    module_inventory: Mapping[str, Any] | None = None,
    red_ledger: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the P7-3 runner plan with split groups and heavy isolation."""

    inventory = safe_mapping(module_inventory) if module_inventory is not None else build_p7_module_inventory()
    assert_p7_module_inventory_contract(inventory)
    ledger = safe_mapping(red_ledger) if red_ledger is not None else build_p7_red_ledger()
    assert_p7_red_ledger_contract(ledger)

    entries = [safe_mapping(entry) for entry in ledger.get("entries", []) if isinstance(entry, Mapping)]
    release_blockers = [clean_identifier(entry.get("id")) for entry in entries if entry.get("release_blocker") is True]
    heavy_red_refs = sorted(
        {
            red_ref
            for group in _plan_groups()
            if group["group_kind"] == P7_GROUP_KIND_HEAVY_ISOLATED_RED
            for red_ref in group["red_refs"]
        }
    )
    connection_timeout_isolation = build_p7_connection_e2e_timeout_isolation_result()
    plan = {
        "schema_version": P7_RUNNER_PLAN_SCHEMA_VERSION,
        "plan_id": P7_RUNNER_PLAN_ID,
        "phase": P7_PHASE,
        "step": P7_RUNNER_PLAN_STEP,
        "scope": P7_RUNNER_PLAN_SCOPE,
        "module_inventory_schema_version": inventory.get("schema_version"),
        "red_ledger_schema_version": ledger.get("schema_version"),
        "groups": _plan_groups(),
        "heavy_isolated_test_files": sorted(_HEAVY_E2E_TEST_FILES),
        "heavy_isolated_red_refs": heavy_red_refs,
        "e2e_isolation_result_schema_version": P7_E2E_ISOLATION_RESULT_SCHEMA_VERSION,
        "connection_timeout_isolation_result": connection_timeout_isolation,
        "release_blockers": dedupe_identifiers(release_blockers, limit=12),
        "unresolved_red_refs": dedupe_identifiers(P7_INITIAL_RED_IDS, limit=12),
        "timeout_budget_policy": {
            "split_groups_have_explicit_timeout_budget": True,
            "heavy_e2e_has_explicit_timeout_budget": True,
            "timeout_hang_is_green": False,
            "combined_timeout_is_green": False,
            "timeout_claim_action": "keep_red_or_hang_in_ledger",
            "body_free": True,
        },
        "public_contract": public_contract_flags(),
        "body_free": body_free_flags(include_history=False, include_reviewer=True, include_terminal=True),
        "full_backend_suite_green_claim_allowed": False,
        "combined_timeout_is_green": False,
        "release_allowed": False,
    }
    assert_p7_runner_plan_contract(plan)
    return plan


def build_p7_runner_command_matrix(plan: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    data = safe_mapping(plan) if plan is not None else build_p7_runner_plan()
    assert_p7_runner_plan_contract(data)
    return [
        {
            "group_id": group["group_id"],
            "group_kind": group["group_kind"],
            "command": group["command"],
            "timeout_budget_sec": group["timeout_budget_sec"],
            "green_claim_scope": group["green_claim_scope"],
            "mainline_pass_condition": group["mainline_pass_condition"],
            "timeout_hang_is_green": group["timeout_hang_is_green"],
            "release_allowed": False,
            "body_free": True,
        }
        for group in data["groups"]
    ]


def assert_p7_runner_plan_contract(plan: Mapping[str, Any]) -> bool:
    data = safe_mapping(plan)
    if data.get("schema_version") != P7_RUNNER_PLAN_SCHEMA_VERSION:
        raise ValueError("unexpected P7 runner plan schema_version")
    if data.get("plan_id") != P7_RUNNER_PLAN_ID:
        raise ValueError("unexpected P7 runner plan id")
    if data.get("phase") != P7_PHASE:
        raise ValueError("unexpected P7 runner plan phase")
    if data.get("scope") != P7_RUNNER_PLAN_SCOPE:
        raise ValueError("unexpected P7 runner plan scope")
    if data.get("module_inventory_schema_version") != P7_MODULE_INVENTORY_SCHEMA_VERSION:
        raise ValueError("P7 runner plan must reference P7-2 module inventory")
    if data.get("red_ledger_schema_version") != P7_RED_LEDGER_SCHEMA_VERSION:
        raise ValueError("P7 runner plan must reference the P7 red ledger")
    if data.get("release_allowed") is not False:
        raise ValueError("P7 runner plan must not allow release")
    if data.get("full_backend_suite_green_claim_allowed") is not False:
        raise ValueError("P7 runner plan must not claim full backend suite green")
    if data.get("combined_timeout_is_green") is not False:
        raise ValueError("P7 runner plan must not treat combined timeout as green")
    if data.get("e2e_isolation_result_schema_version") != P7_E2E_ISOLATION_RESULT_SCHEMA_VERSION:
        raise ValueError("P7 runner plan must reference the R6 E2E isolation result schema")
    connection_isolation = safe_mapping(data.get("connection_timeout_isolation_result"))
    assert_p7_e2e_isolation_result_contract(connection_isolation)
    if "P7-RED-003" not in dedupe_identifiers(connection_isolation.get("red_refs"), limit=20):
        raise ValueError("P7 runner plan must keep P7-RED-003 in timeout isolation material")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_runner_plan.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free")), source="p7_runner_plan.body_free")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_runner_plan")

    groups = data.get("groups")
    if not isinstance(groups, list) or len(groups) < 3:
        raise ValueError("P7 runner plan must contain split and heavy isolated groups")
    seen_group_ids: set[str] = set()
    heavy_seen: set[str] = set()
    mainline_seen: set[str] = set()
    for raw_group in groups:
        group = safe_mapping(raw_group)
        group_id = clean_identifier(group.get("group_id"))
        if not group_id or group_id in seen_group_ids:
            raise ValueError("P7 runner plan groups must have unique ids")
        seen_group_ids.add(group_id)
        group_kind = clean_identifier(group.get("group_kind"))
        if group_kind not in _ALLOWED_GROUP_KINDS:
            raise ValueError(f"invalid P7 runner group kind: {group_id}")
        if clean_identifier(group.get("repository")) not in _ALLOWED_REPOSITORIES:
            raise ValueError(f"invalid P7 runner repository: {group_id}")
        if clean_identifier(group.get("command_kind")) not in _ALLOWED_COMMAND_KINDS:
            raise ValueError(f"invalid P7 runner command kind: {group_id}")
        if clean_identifier(group.get("green_claim_scope")) not in _ALLOWED_GREEN_SCOPES:
            raise ValueError(f"invalid P7 runner green claim scope: {group_id}")
        if group.get("timeout_hang_is_green") is not False:
            raise ValueError(f"runner group must not treat timeout/hang as green: {group_id}")
        if group.get("full_backend_suite_green_claim_allowed") is not False:
            raise ValueError(f"runner group must not claim full suite green: {group_id}")
        if group.get("combined_timeout_is_green") is not False:
            raise ValueError(f"runner group must not treat combined timeout as green: {group_id}")
        if group.get("release_allowed") is not False:
            raise ValueError(f"runner group must remain release-closed: {group_id}")
        if group.get("body_free") is not True:
            raise ValueError(f"runner group must be body-free: {group_id}")
        timeout_budget = group.get("timeout_budget_sec")
        if not isinstance(timeout_budget, int) or not 1 <= timeout_budget <= 600:
            raise ValueError(f"runner group timeout budget must be explicit and bounded: {group_id}")
        test_files = set(dedupe_identifiers(group.get("test_files"), limit=80, max_length=220))
        if not test_files:
            raise ValueError(f"runner group must contain test files: {group_id}")
        heavy_overlap = test_files & _HEAVY_E2E_TEST_FILES
        if group_kind == P7_GROUP_KIND_HEAVY_ISOLATED_RED:
            if group.get("mainline_pass_condition") is not False:
                raise ValueError(f"heavy group must not be a mainline pass condition: {group_id}")
            if group.get("green_claim_scope") != P7_GREEN_SCOPE_ISOLATED_RED_ONLY:
                raise ValueError(f"heavy group must have isolated-red green scope: {group_id}")
            if not heavy_overlap:
                raise ValueError(f"heavy group must contain a heavy E2E source: {group_id}")
            if not group.get("red_refs"):
                raise ValueError(f"heavy group must link P7 red refs: {group_id}")
            heavy_seen.update(heavy_overlap)
        else:
            if heavy_overlap:
                raise ValueError(f"heavy E2E files must not be in non-heavy group: {group_id}")
            if group.get("mainline_pass_condition") is True:
                mainline_seen.update(test_files)
    if heavy_seen != _HEAVY_E2E_TEST_FILES:
        raise ValueError("P7 runner plan must isolate every heavy E2E red source")
    if not {"p7_core_contract", "existing_p7_reuse_contract"}.issubset(seen_group_ids):
        raise ValueError("P7 runner plan must include core and existing-reuse split groups")
    if _HEAVY_E2E_TEST_FILES & mainline_seen:
        raise ValueError("heavy E2E files must not be mainline pass conditions")

    policy = safe_mapping(data.get("timeout_budget_policy"))
    if policy.get("timeout_hang_is_green") is not False or policy.get("combined_timeout_is_green") is not False:
        raise ValueError("P7 timeout budget policy must keep timeout/hang non-green")
    if policy.get("body_free") is not True:
        raise ValueError("P7 timeout budget policy must be body-free")
    if set(data.get("heavy_isolated_red_refs", [])) != set(P7_INITIAL_RED_IDS):
        raise ValueError("P7 runner plan must connect heavy isolated groups to the initial P7 RED refs")
    return True
