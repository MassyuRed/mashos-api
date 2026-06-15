# -*- coding: utf-8 -*-
"""P7-HOLD-004 backend-suite R2/R3 inventory and execution-plan materials.

R15/R16 current-snapshot scope only:
- read the active R14 frozen collect baseline from
  ``emlis_ai_p7_hold004_backend_suite_split_consistency``;
- serialize the 13 deterministic backend-suite groups for the 425 files / 2856
  tests current baseline;
- serialize the split execution order, timeout budgets, and batch policy against
  the 20260615 current baseline;
- do not run groups, retain terminal output, close P7-HOLD-004, start P8, or
  allow release.

This module stores identifiers, counts, booleans, enum statuses, and rule ids
only. It must never serialize raw input, comment_text bodies, candidate bodies,
surface bodies, reviewer text, terminal output, stdout/stderr, or traceback
bodies.
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
from emlis_ai_p7_hold004_backend_suite_split_consistency import (
    P7_HOLD004_BACKEND_COLLECT_BASELINE_ID,
    P7_HOLD004_BACKEND_COLLECT_STATUS_COLLECTED,
    P7_HOLD004_BACKEND_COLLECT_STATUS_COLLECTION_FAILED,
    P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT,
    P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT,
    P7_HOLD004_BACKEND_SUITE_HOLD_ID,
    assert_p7_hold004_backend_collect_baseline_contract,
    build_p7_hold004_backend_collect_baseline,
)

P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_R2_R3_STEP: Final = (
    "P7-HOLD-004_CurrentSnapshotBaselineReconcile_R15_R16_20260615"
)
P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.backend_suite_group_inventory.v1"
)
P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.backend_suite_execution_plan.v1"
)
P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID: Final = (
    "p7_hold004_backend_suite_group_inventory_20260615"
)
P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID: Final = (
    "p7_hold004_backend_suite_execution_plan_20260615"
)
P7_HOLD004_BACKEND_SUITE_GROUPING_RULE_VERSION: Final = "p7_hold004_backend_grouping_rules.v1"
P7_HOLD004_BACKEND_SUITE_EXECUTION_MODE: Final = "split_group_capture_then_confirmation"
P7_HOLD004_BACKEND_SUITE_PYTEST_ENV_ID: Final = (
    "pytest_disable_plugin_autoload_with_ai_inference_path"
)
P7_HOLD004_BACKEND_SUITE_DEFAULT_PYTEST_ARGS_ID: Final = (
    "pytest_q_tb_short_pytest_asyncio_plugin"
)
P7_HOLD004_BACKEND_SUITE_COMMAND_SHAPE_ID: Final = (
    "pytest_group_or_batch_files_without_terminal_output_retention"
)
P7_HOLD004_BACKEND_R2_R3_SOURCE_SNAPSHOT_REF: Final = "mashos-api(147).zip"

P7_HOLD004_BACKEND_SUITE_GROUP_IDS: Final[tuple[str, ...]] = (
    "group_01_contract",
    "group_02_p7_hold004",
    "group_03_p7_core_matrix_handoff",
    "group_04_complete_product_quality",
    "group_05_user_label_connection_p5",
    "group_06_structure_insight_p6",
    "group_07_product_quality_legacy_runner",
    "group_08_complete_initial",
    "group_09_complete_composer_other",
    "group_10_two_stage_public_recovery",
    "group_11_emlis_runtime_other",
    "group_12_analysis_subscription_piece_self_structure",
    "group_13_remaining_backend_other",
)
P7_HOLD004_BACKEND_SUITE_EXECUTION_ORDER: Final[tuple[str, ...]] = (
    "group_02_p7_hold004",
    "group_03_p7_core_matrix_handoff",
    "group_04_complete_product_quality",
    "group_01_contract",
    "group_05_user_label_connection_p5",
    "group_06_structure_insight_p6",
    "group_07_product_quality_legacy_runner",
    "group_08_complete_initial",
    "group_09_complete_composer_other",
    "group_10_two_stage_public_recovery",
    "group_11_emlis_runtime_other",
    "group_12_analysis_subscription_piece_self_structure",
    "group_13_remaining_backend_other",
)

P7_HOLD004_BACKEND_SUITE_GROUP_DEFINITIONS: Final[tuple[dict[str, Any], ...]] = (
    {
        "group_id": "group_01_contract",
        "owner_layer": "contract_boundary",
        "match_rule_id": "tests_contract",
        "assignment_order": 1,
        "file_count": 18,
        "test_item_count": 119,
        "timeout_budget_sec": 120,
        "planned_batch_count": 1,
        "batch_policy": "single_batch_preferred",
        "match_hints": ("tests/contract/*",),
    },
    {
        "group_id": "group_02_p7_hold004",
        "owner_layer": "p7_hold004_target",
        "match_rule_id": "p7_hold004_tests",
        "assignment_order": 2,
        "file_count": 19,
        "test_item_count": 252,
        "timeout_budget_sec": 120,
        "planned_batch_count": 1,
        "batch_policy": "single_batch_preferred",
        "match_hints": ("tests/test_emlis_ai_p7_hold004_*.py",),
    },
    {
        "group_id": "group_03_p7_core_matrix_handoff",
        "owner_layer": "p7_core_matrix_handoff",
        "match_rule_id": "p7_tests_except_hold004",
        "assignment_order": 3,
        "file_count": 18,
        "test_item_count": 89,
        "timeout_budget_sec": 120,
        "planned_batch_count": 1,
        "batch_policy": "single_batch_preferred",
        "match_hints": ("tests/test_emlis_ai_p7_*.py", "except hold004"),
    },
    {
        "group_id": "group_04_complete_product_quality",
        "owner_layer": "complete_product_quality",
        "match_rule_id": "complete_product_quality_tests",
        "assignment_order": 4,
        "file_count": 9,
        "test_item_count": 49,
        "timeout_budget_sec": 150,
        "planned_batch_count": 1,
        "batch_policy": "single_batch_preferred",
        "match_hints": ("tests/test_emlis_ai_complete_product_quality*.py",),
    },
    {
        "group_id": "group_05_user_label_connection_p5",
        "owner_layer": "user_label_connection_p5",
        "match_rule_id": "user_label_connection_tests",
        "assignment_order": 5,
        "file_count": 24,
        "test_item_count": 182,
        "timeout_budget_sec": 150,
        "planned_batch_count": 1,
        "batch_policy": "single_batch_preferred_with_optional_split",
        "match_hints": ("*user_label_connection*",),
    },
    {
        "group_id": "group_06_structure_insight_p6",
        "owner_layer": "structure_insight_p6",
        "match_rule_id": "structure_insight_tests",
        "assignment_order": 6,
        "file_count": 16,
        "test_item_count": 131,
        "timeout_budget_sec": 150,
        "planned_batch_count": 1,
        "batch_policy": "single_batch_preferred",
        "match_hints": ("*structure_insight*",),
    },
    {
        "group_id": "group_07_product_quality_legacy_runner",
        "owner_layer": "product_quality_legacy_runner",
        "match_rule_id": "product_quality_tests_except_complete_product_quality",
        "assignment_order": 7,
        "file_count": 16,
        "test_item_count": 76,
        "timeout_budget_sec": 150,
        "planned_batch_count": 1,
        "batch_policy": "single_batch_preferred",
        "match_hints": ("*product_quality*", "except complete_product_quality"),
    },
    {
        "group_id": "group_08_complete_initial",
        "owner_layer": "complete_initial",
        "match_rule_id": "complete_initial_tests",
        "assignment_order": 8,
        "file_count": 8,
        "test_item_count": 44,
        "timeout_budget_sec": 120,
        "planned_batch_count": 1,
        "batch_policy": "single_batch_preferred",
        "match_hints": ("tests/test_emlis_ai_complete_initial*.py",),
    },
    {
        "group_id": "group_09_complete_composer_other",
        "owner_layer": "complete_composer_other",
        "match_rule_id": "complete_tests_remaining",
        "assignment_order": 9,
        "file_count": 25,
        "test_item_count": 149,
        "timeout_budget_sec": 150,
        "planned_batch_count": 1,
        "batch_policy": "single_batch_preferred_with_optional_split",
        "match_hints": ("tests/test_emlis_ai_complete_*.py", "except complete_initial and product_quality"),
    },
    {
        "group_id": "group_10_two_stage_public_recovery",
        "owner_layer": "two_stage_public_recovery",
        "match_rule_id": "two_stage_public_recovery_tests",
        "assignment_order": 10,
        "file_count": 38,
        "test_item_count": 272,
        "timeout_budget_sec": 180,
        "planned_batch_count": 2,
        "batch_policy": "batch_by_public_recovery_surface_family",
        "match_hints": (
            "*two_stage*",
            "*public_observation_recovery*",
            "*public_surface*",
            "*public_feedback*",
            "*public_meta*",
            "*gate_recovery*",
        ),
    },
    {
        "group_id": "group_11_emlis_runtime_other",
        "owner_layer": "emlis_runtime_other",
        "match_rule_id": "remaining_emlis_runtime",
        "assignment_order": 11,
        "file_count": 201,
        "test_item_count": 1352,
        "timeout_budget_sec": 240,
        "planned_batch_count": 6,
        "batch_policy": "required_batch_by_30_files_or_250_tests",
        "match_hints": (
            "tests/test_emlis_ai_*.py",
            "tests/test_emotion_submit*.py",
            "tests/test_emlis_observation*.py",
            "after prior rules",
        ),
    },
    {
        "group_id": "group_12_analysis_subscription_piece_self_structure",
        "owner_layer": "analysis_subscription_piece_self_structure",
        "match_rule_id": "analysis_subscription_piece_self_structure_tests",
        "assignment_order": 12,
        "file_count": 17,
        "test_item_count": 66,
        "timeout_budget_sec": 120,
        "planned_batch_count": 1,
        "batch_policy": "single_batch_preferred",
        "match_hints": (
            "*analysis*",
            "*subscription*",
            "*self_structure*",
            "*watashi*",
            "*piece_*",
            "*ranking*",
            "*reflection*",
        ),
    },
    {
        "group_id": "group_13_remaining_backend_other",
        "owner_layer": "remaining_backend_other",
        "match_rule_id": "remaining_backend_tests",
        "assignment_order": 13,
        "file_count": 16,
        "test_item_count": 75,
        "timeout_budget_sec": 120,
        "planned_batch_count": 1,
        "batch_policy": "single_batch_preferred",
        "match_hints": ("remaining backend tests",),
    },
)
P7_HOLD004_BACKEND_SUITE_GROUP_DEFINITION_BY_ID: Final[dict[str, dict[str, Any]]] = {
    str(definition["group_id"]): dict(definition)
    for definition in P7_HOLD004_BACKEND_SUITE_GROUP_DEFINITIONS
}
P7_HOLD004_BACKEND_SUITE_TOTAL_GROUP_FILE_COUNT: Final = sum(
    int(definition["file_count"]) for definition in P7_HOLD004_BACKEND_SUITE_GROUP_DEFINITIONS
)
P7_HOLD004_BACKEND_SUITE_TOTAL_GROUP_TEST_ITEM_COUNT: Final = sum(
    int(definition["test_item_count"]) for definition in P7_HOLD004_BACKEND_SUITE_GROUP_DEFINITIONS
)
P7_HOLD004_BACKEND_SUITE_TOTAL_BATCH_COUNT: Final = sum(
    int(definition["planned_batch_count"]) for definition in P7_HOLD004_BACKEND_SUITE_GROUP_DEFINITIONS
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
_R2_R3_REQUIRED_FOLLOWUP_FIXES: Final[tuple[str, ...]] = (
    "backend_suite_group_execution_not_run",
    "backend_suite_group_run_results_not_built",
    "full_backend_suite_green_unconfirmed",
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


def _assert_common_release_closed_and_body_free(data: Mapping[str, Any], *, source: str) -> None:
    for key in _RELEASE_CLOSED_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=false")
    unresolved_holds = set(dedupe_identifiers(data.get("unresolved_hold_refs"), limit=40, max_length=120))
    if P7_HOLD004_BACKEND_SUITE_HOLD_ID not in unresolved_holds:
        raise ValueError(f"{source} must keep P7-HOLD-004 unresolved")
    followups = set(dedupe_identifiers(data.get("required_followup_fixes"), limit=80, max_length=160))
    if "full_backend_suite_green_unconfirmed" not in followups:
        raise ValueError(f"{source} must keep full_backend_suite_green_unconfirmed followup")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must be body_free=true")
    assert_false_markers(safe_mapping(data.get("public_contract")), source=f"{source}.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source=f"{source}.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)


def classify_p7_hold004_backend_test_file_ref(file_ref: Any) -> str:
    """Classify a backend pytest file into the deterministic R2 group id.

    This helper implements the ordered rules from the R2 inventory material. It
    returns only a group id and never serializes the file path into material.
    """

    path = clean_identifier(file_ref, max_length=240).replace("\\", "/").lower()
    name = path.rsplit("/", 1)[-1]

    if path.startswith("tests/contract/"):
        return "group_01_contract"
    if name.startswith("test_emlis_ai_p7_hold004_"):
        return "group_02_p7_hold004"
    if name.startswith("test_emlis_ai_p7_"):
        return "group_03_p7_core_matrix_handoff"
    if name.startswith("test_emlis_ai_complete_product_quality"):
        return "group_04_complete_product_quality"
    if "user_label_connection" in path:
        return "group_05_user_label_connection_p5"
    if "structure_insight" in path:
        return "group_06_structure_insight_p6"
    if "product_quality" in path:
        return "group_07_product_quality_legacy_runner"
    if name.startswith("test_emlis_ai_complete_initial"):
        return "group_08_complete_initial"
    if name.startswith("test_emlis_ai_complete_"):
        return "group_09_complete_composer_other"
    if any(
        token in path
        for token in (
            "two_stage",
            "public_observation_recovery",
            "public_surface",
            "public_feedback",
            "public_meta",
            "gate_recovery",
        )
    ):
        return "group_10_two_stage_public_recovery"
    if (
        name.startswith("test_emlis_ai_")
        or name.startswith("test_emotion_submit")
        or name.startswith("test_emlis_observation")
    ):
        return "group_11_emlis_runtime_other"
    if any(
        token in path
        for token in (
            "analysis",
            "subscription",
            "self_structure",
            "watashi",
            "piece_",
            "ranking",
            "reflection",
        )
    ):
        return "group_12_analysis_subscription_piece_self_structure"
    return "group_13_remaining_backend_other"


def _group_inventory_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for definition in P7_HOLD004_BACKEND_SUITE_GROUP_DEFINITIONS:
        records.append(
            {
                "group_id": definition["group_id"],
                "owner_layer": definition["owner_layer"],
                "assignment_order": definition["assignment_order"],
                "match_rule_id": definition["match_rule_id"],
                "match_hints": list(definition["match_hints"]),
                "file_count": definition["file_count"],
                "test_item_count": definition["test_item_count"],
                "timeout_budget_sec": definition["timeout_budget_sec"],
                "batch_policy": definition["batch_policy"],
                "planned_batch_count": definition["planned_batch_count"],
                "can_claim_full_backend_suite_green": False,
                "release_allowed": False,
                "body_free": True,
            }
        )
    return records


def _assignment_rule_records() -> list[dict[str, Any]]:
    return [
        {
            "assignment_order": definition["assignment_order"],
            "match_rule_id": definition["match_rule_id"],
            "group_id": definition["group_id"],
            "owner_layer": definition["owner_layer"],
            "match_hints": list(definition["match_hints"]),
        }
        for definition in P7_HOLD004_BACKEND_SUITE_GROUP_DEFINITIONS
    ]


def build_p7_hold004_backend_suite_group_inventory(
    *,
    collect_baseline: Mapping[str, Any] | None = None,
    groups: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the R2 deterministic 13-group inventory material."""

    baseline = safe_mapping(collect_baseline) if collect_baseline is not None else build_p7_hold004_backend_collect_baseline()
    assert_p7_hold004_backend_collect_baseline_contract(baseline)
    if baseline.get("collection_status") != P7_HOLD004_BACKEND_COLLECT_STATUS_COLLECTED:
        raise ValueError("R2 group inventory requires the collected R1 baseline")

    group_records = [dict(group) for group in groups] if groups is not None else _group_inventory_records()
    material = {
        "schema_version": P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_R2_R3_STEP,
        "implementation_step": P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_R2_R3_STEP,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "inventory_id": P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID,
        "collect_baseline_id": baseline.get("baseline_id"),
        "source_mode": P7_SOURCE_MODE,
        "source_snapshot_ref": P7_HOLD004_BACKEND_R2_R3_SOURCE_SNAPSHOT_REF,
        "git_checked": P7_GIT_CHECKED,
        "grouping_rule_version": P7_HOLD004_BACKEND_SUITE_GROUPING_RULE_VERSION,
        "group_count": len(group_records),
        "total_group_file_count": sum(_coerce_non_negative_int(group.get("file_count")) for group in group_records),
        "total_group_test_item_count": sum(_coerce_non_negative_int(group.get("test_item_count")) for group in group_records),
        "unassigned_test_file_count": 0,
        "duplicate_assignment_count": 0,
        "assignment_rules": _assignment_rule_records(),
        "groups": group_records,
        "collection_status": baseline.get("collection_status"),
        "collected_test_file_count": baseline.get("collected_test_file_count"),
        "collected_test_item_count": baseline.get("collected_test_item_count"),
        "current_collect_baseline_reconciled": True,
        "previous_baseline_is_not_current": True,
        "baseline_mismatch_blocks_execution": True,
        **_release_closed_boundary(),
        "unresolved_hold_refs": [P7_HOLD004_BACKEND_SUITE_HOLD_ID],
        "required_followup_fixes": list(_R2_R3_REQUIRED_FOLLOWUP_FIXES),
        "public_contract": _public_contract_boundary_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
        "body_free": True,
    }
    assert_p7_hold004_backend_suite_group_inventory_contract(material)
    return material


def build_p7_hold004_current_backend_suite_group_inventory() -> dict[str, Any]:
    """Return the R2 group inventory for the current frozen R1 collect baseline."""

    return build_p7_hold004_backend_suite_group_inventory()


def _expected_group_ids() -> list[str]:
    return list(P7_HOLD004_BACKEND_SUITE_GROUP_IDS)


def _expected_group_definition(group_id: str) -> dict[str, Any]:
    definition = P7_HOLD004_BACKEND_SUITE_GROUP_DEFINITION_BY_ID.get(group_id)
    if not definition:
        raise ValueError(f"unknown backend suite group id: {group_id}")
    return definition


def assert_p7_hold004_backend_suite_group_inventory_contract(material: Mapping[str, Any]) -> bool:
    """Validate the R2 inventory without promoting any split result to release."""

    data = safe_mapping(material)
    source = "p7_hold004_backend_suite_group_inventory"
    if data.get("schema_version") != P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 backend group inventory schema_version changed")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError("P7-HOLD-004 backend group inventory must stay in P7-HOLD-004 scope")
    if data.get("implementation_step") != P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_R2_R3_STEP:
        raise ValueError("P7-HOLD-004 backend group inventory implementation_step changed")
    if data.get("inventory_id") != P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID:
        raise ValueError("P7-HOLD-004 backend group inventory id changed")
    if data.get("collect_baseline_id") != P7_HOLD004_BACKEND_COLLECT_BASELINE_ID:
        raise ValueError("P7-HOLD-004 backend group inventory must be tied to the R1 collect baseline")
    if data.get("source_mode") != P7_SOURCE_MODE or data.get("source_snapshot_ref") != P7_HOLD004_BACKEND_R2_R3_SOURCE_SNAPSHOT_REF:
        raise ValueError("P7-HOLD-004 backend group inventory must stay on the R2/R3 local snapshot")
    if data.get("git_checked") is not False:
        raise ValueError("P7-HOLD-004 backend group inventory must not claim GitHub verification")
    if data.get("grouping_rule_version") != P7_HOLD004_BACKEND_SUITE_GROUPING_RULE_VERSION:
        raise ValueError("P7-HOLD-004 backend group inventory grouping rule version changed")
    if data.get("collection_status") != P7_HOLD004_BACKEND_COLLECT_STATUS_COLLECTED:
        raise ValueError("P7-HOLD-004 backend group inventory requires collected baseline status")
    for key in ("current_collect_baseline_reconciled", "previous_baseline_is_not_current", "baseline_mismatch_blocks_execution"):
        if data.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 backend group inventory must keep {key}=true")

    groups = [safe_mapping(group) for group in listify(data.get("groups"))]
    group_ids = [clean_identifier(group.get("group_id"), max_length=120) for group in groups]
    expected_group_ids = _expected_group_ids()
    if group_ids != expected_group_ids:
        raise ValueError("P7-HOLD-004 backend group inventory group ids/order changed")
    if data.get("group_count") != len(expected_group_ids):
        raise ValueError("P7-HOLD-004 backend group inventory group_count must be 13")
    if data.get("unassigned_test_file_count") != 0 or data.get("duplicate_assignment_count") != 0:
        raise ValueError("P7-HOLD-004 backend group inventory must have no missing or duplicate assignments")
    if data.get("collected_test_file_count") != P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT:
        raise ValueError("P7-HOLD-004 backend group inventory collected file count mismatch")
    if data.get("collected_test_item_count") != P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT:
        raise ValueError("P7-HOLD-004 backend group inventory collected item count mismatch")
    if data.get("total_group_file_count") != P7_HOLD004_BACKEND_SUITE_TOTAL_GROUP_FILE_COUNT:
        raise ValueError("P7-HOLD-004 backend group inventory total file count mismatch")
    if data.get("total_group_test_item_count") != P7_HOLD004_BACKEND_SUITE_TOTAL_GROUP_TEST_ITEM_COUNT:
        raise ValueError("P7-HOLD-004 backend group inventory total item count mismatch")
    if data.get("total_group_file_count") != P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT:
        raise ValueError("P7-HOLD-004 backend group inventory must match collect baseline file count")
    if data.get("total_group_test_item_count") != P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT:
        raise ValueError("P7-HOLD-004 backend group inventory must match collect baseline item count")

    rule_ids = [clean_identifier(rule.get("group_id"), max_length=120) for rule in listify(data.get("assignment_rules"))]
    if rule_ids != expected_group_ids:
        raise ValueError("P7-HOLD-004 backend group inventory assignment rules changed")

    for group in groups:
        group_id = clean_identifier(group.get("group_id"), max_length=120)
        definition = _expected_group_definition(group_id)
        for key in ("owner_layer", "match_rule_id", "assignment_order", "file_count", "test_item_count", "timeout_budget_sec", "batch_policy", "planned_batch_count"):
            if group.get(key) != definition.get(key):
                raise ValueError(f"P7-HOLD-004 backend group inventory {group_id}.{key} changed")
        if group.get("can_claim_full_backend_suite_green") is not False:
            raise ValueError(f"P7-HOLD-004 backend group inventory {group_id} must not claim full suite green")
        if group.get("release_allowed") is not False:
            raise ValueError(f"P7-HOLD-004 backend group inventory {group_id} must keep release_allowed=false")
        if group.get("body_free") is not True:
            raise ValueError(f"P7-HOLD-004 backend group inventory {group_id} must be body_free=true")

    _assert_common_release_closed_and_body_free(data, source=source)
    return True


def _batch_ids_for_group(group_id: str, batch_count: int) -> list[str]:
    return [f"{group_id}_batch_{index:02d}" for index in range(1, batch_count + 1)]


def _plan_group_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for execution_index, group_id in enumerate(P7_HOLD004_BACKEND_SUITE_EXECUTION_ORDER, start=1):
        definition = _expected_group_definition(group_id)
        batch_count = _coerce_non_negative_int(definition.get("planned_batch_count"), default=1) or 1
        records.append(
            {
                "group_id": group_id,
                "owner_layer": definition["owner_layer"],
                "execution_order_index": execution_index,
                "assignment_order": definition["assignment_order"],
                "file_count": definition["file_count"],
                "test_item_count": definition["test_item_count"],
                "batch_count": batch_count,
                "batch_ids": _batch_ids_for_group(group_id, batch_count),
                "timeout_budget_sec": definition["timeout_budget_sec"],
                "batch_policy": definition["batch_policy"],
                "capture_run_maxfail_1": True,
                "confirmation_run_maxfail_1": False,
                "execution_required": True,
                "terminal_output_retained": False,
                "can_claim_full_backend_suite_green": False,
                "split_green_can_close_p7_hold004": False,
                "release_allowed": False,
                "body_free": True,
            }
        )
    return records


def build_p7_hold004_backend_suite_execution_plan(
    *,
    inventory: Mapping[str, Any] | None = None,
    groups: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the R3 split execution plan material without executing groups."""

    inventory_material = safe_mapping(inventory) if inventory is not None else build_p7_hold004_backend_suite_group_inventory()
    assert_p7_hold004_backend_suite_group_inventory_contract(inventory_material)

    group_records = [dict(group) for group in groups] if groups is not None else _plan_group_records()
    material = {
        "schema_version": P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_R2_R3_STEP,
        "implementation_step": P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_R2_R3_STEP,
        "hold_id": P7_HOLD004_BACKEND_SUITE_HOLD_ID,
        "plan_id": P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID,
        "inventory_id": inventory_material.get("inventory_id"),
        "collect_baseline_id": inventory_material.get("collect_baseline_id"),
        "source_mode": P7_SOURCE_MODE,
        "source_snapshot_ref": P7_HOLD004_BACKEND_R2_R3_SOURCE_SNAPSHOT_REF,
        "git_checked": P7_GIT_CHECKED,
        "execution_mode": P7_HOLD004_BACKEND_SUITE_EXECUTION_MODE,
        "pytest_env_id": P7_HOLD004_BACKEND_SUITE_PYTEST_ENV_ID,
        "default_pytest_args_id": P7_HOLD004_BACKEND_SUITE_DEFAULT_PYTEST_ARGS_ID,
        "command_shape_id": P7_HOLD004_BACKEND_SUITE_COMMAND_SHAPE_ID,
        "group_count": len(group_records),
        "total_batch_count": sum(_coerce_non_negative_int(group.get("batch_count")) for group in group_records),
        "groups": group_records,
        "execution_started": False,
        "group_run_results_recorded": False,
        "terminal_output_retained": False,
        "capture_run_and_confirmation_run_separated": True,
        "current_collect_baseline_reconciled": True,
        "previous_baseline_is_not_current": True,
        "baseline_mismatch_blocks_execution": True,
        **_release_closed_boundary(),
        "unresolved_hold_refs": [P7_HOLD004_BACKEND_SUITE_HOLD_ID],
        "required_followup_fixes": list(_R2_R3_REQUIRED_FOLLOWUP_FIXES),
        "public_contract": _public_contract_boundary_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
        "body_free": True,
    }
    assert_p7_hold004_backend_suite_execution_plan_contract(material)
    return material


def build_p7_hold004_current_backend_suite_execution_plan() -> dict[str, Any]:
    """Return the R3 execution plan for the current R2 group inventory."""

    return build_p7_hold004_backend_suite_execution_plan()


def assert_p7_hold004_backend_suite_execution_plan_contract(material: Mapping[str, Any]) -> bool:
    """Validate the R3 plan while keeping every group non-release and non-green-promoting."""

    data = safe_mapping(material)
    source = "p7_hold004_backend_suite_execution_plan"
    if data.get("schema_version") != P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_SCHEMA_VERSION:
        raise ValueError("P7-HOLD-004 backend execution plan schema_version changed")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_BACKEND_SUITE_HOLD_ID:
        raise ValueError("P7-HOLD-004 backend execution plan must stay in P7-HOLD-004 scope")
    if data.get("implementation_step") != P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_R2_R3_STEP:
        raise ValueError("P7-HOLD-004 backend execution plan implementation_step changed")
    if data.get("plan_id") != P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID:
        raise ValueError("P7-HOLD-004 backend execution plan id changed")
    if data.get("inventory_id") != P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID:
        raise ValueError("P7-HOLD-004 backend execution plan must be tied to the R2 inventory")
    if data.get("collect_baseline_id") != P7_HOLD004_BACKEND_COLLECT_BASELINE_ID:
        raise ValueError("P7-HOLD-004 backend execution plan must be tied to the R1 collect baseline")
    if data.get("source_mode") != P7_SOURCE_MODE or data.get("source_snapshot_ref") != P7_HOLD004_BACKEND_R2_R3_SOURCE_SNAPSHOT_REF:
        raise ValueError("P7-HOLD-004 backend execution plan must stay on the R2/R3 local snapshot")
    if data.get("git_checked") is not False:
        raise ValueError("P7-HOLD-004 backend execution plan must not claim GitHub verification")
    if data.get("execution_mode") != P7_HOLD004_BACKEND_SUITE_EXECUTION_MODE:
        raise ValueError("P7-HOLD-004 backend execution plan execution_mode changed")
    if data.get("pytest_env_id") != P7_HOLD004_BACKEND_SUITE_PYTEST_ENV_ID:
        raise ValueError("P7-HOLD-004 backend execution plan pytest env changed")
    if data.get("default_pytest_args_id") != P7_HOLD004_BACKEND_SUITE_DEFAULT_PYTEST_ARGS_ID:
        raise ValueError("P7-HOLD-004 backend execution plan pytest args changed")
    if data.get("command_shape_id") != P7_HOLD004_BACKEND_SUITE_COMMAND_SHAPE_ID:
        raise ValueError("P7-HOLD-004 backend execution plan command shape changed")
    if data.get("execution_started") is not False or data.get("group_run_results_recorded") is not False:
        raise ValueError("R3 execution plan must not claim group execution results")
    if data.get("terminal_output_retained") is not False:
        raise ValueError("R3 execution plan must not retain terminal output")
    if data.get("capture_run_and_confirmation_run_separated") is not True:
        raise ValueError("R3 execution plan must separate capture run and confirmation run")
    for key in ("current_collect_baseline_reconciled", "previous_baseline_is_not_current", "baseline_mismatch_blocks_execution"):
        if data.get(key) is not True:
            raise ValueError(f"P7-HOLD-004 backend execution plan must keep {key}=true")

    groups = [safe_mapping(group) for group in listify(data.get("groups"))]
    group_ids = [clean_identifier(group.get("group_id"), max_length=120) for group in groups]
    expected_order = list(P7_HOLD004_BACKEND_SUITE_EXECUTION_ORDER)
    if group_ids != expected_order:
        raise ValueError("P7-HOLD-004 backend execution plan group execution order changed")
    if data.get("group_count") != len(expected_order):
        raise ValueError("P7-HOLD-004 backend execution plan group_count must be 13")
    if data.get("total_batch_count") != P7_HOLD004_BACKEND_SUITE_TOTAL_BATCH_COUNT:
        raise ValueError("P7-HOLD-004 backend execution plan total batch count changed")

    for expected_index, group in enumerate(groups, start=1):
        group_id = clean_identifier(group.get("group_id"), max_length=120)
        definition = _expected_group_definition(group_id)
        batch_count = _coerce_non_negative_int(group.get("batch_count"), default=0)
        if group.get("execution_order_index") != expected_index:
            raise ValueError(f"P7-HOLD-004 backend execution plan {group_id}.execution_order_index changed")
        if group.get("assignment_order") != definition.get("assignment_order"):
            raise ValueError(f"P7-HOLD-004 backend execution plan {group_id}.assignment_order changed")
        if group.get("owner_layer") != definition.get("owner_layer"):
            raise ValueError(f"P7-HOLD-004 backend execution plan {group_id}.owner_layer changed")
        if group.get("file_count") != definition.get("file_count"):
            raise ValueError(f"P7-HOLD-004 backend execution plan {group_id}.file_count changed")
        if group.get("test_item_count") != definition.get("test_item_count"):
            raise ValueError(f"P7-HOLD-004 backend execution plan {group_id}.test_item_count changed")
        if batch_count != definition.get("planned_batch_count"):
            raise ValueError(f"P7-HOLD-004 backend execution plan {group_id}.batch_count changed")
        if batch_count < 1:
            raise ValueError(f"P7-HOLD-004 backend execution plan {group_id} needs at least one batch")
        if group_id == "group_11_emlis_runtime_other" and batch_count <= 1:
            raise ValueError("P7-HOLD-004 backend execution plan group_11 must not be a single batch")
        if group.get("batch_ids") != _batch_ids_for_group(group_id, batch_count):
            raise ValueError(f"P7-HOLD-004 backend execution plan {group_id}.batch_ids changed")
        if group.get("timeout_budget_sec") != definition.get("timeout_budget_sec"):
            raise ValueError(f"P7-HOLD-004 backend execution plan {group_id}.timeout_budget_sec changed")
        if group.get("batch_policy") != definition.get("batch_policy"):
            raise ValueError(f"P7-HOLD-004 backend execution plan {group_id}.batch_policy changed")
        if group.get("capture_run_maxfail_1") is not True:
            raise ValueError(f"P7-HOLD-004 backend execution plan {group_id} must keep capture_run_maxfail_1=true")
        if group.get("confirmation_run_maxfail_1") is not False:
            raise ValueError(f"P7-HOLD-004 backend execution plan {group_id} must keep confirmation_run_maxfail_1=false")
        if group.get("execution_required") is not True:
            raise ValueError(f"P7-HOLD-004 backend execution plan {group_id} must remain execution_required=true")
        if group.get("terminal_output_retained") is not False:
            raise ValueError(f"P7-HOLD-004 backend execution plan {group_id} must not retain terminal output")
        if group.get("can_claim_full_backend_suite_green") is not False:
            raise ValueError(f"P7-HOLD-004 backend execution plan {group_id} must not claim full suite green")
        if group.get("split_green_can_close_p7_hold004") is not False:
            raise ValueError(f"P7-HOLD-004 backend execution plan {group_id} must not close HOLD004")
        if group.get("release_allowed") is not False:
            raise ValueError(f"P7-HOLD-004 backend execution plan {group_id} must keep release_allowed=false")
        if group.get("body_free") is not True:
            raise ValueError(f"P7-HOLD-004 backend execution plan {group_id} must be body_free=true")

    _assert_common_release_closed_and_body_free(data, source=source)
    return True


__all__ = [
    "P7_HOLD004_BACKEND_COLLECT_STATUS_COLLECTION_FAILED",
    "P7_HOLD004_BACKEND_R2_R3_SOURCE_SNAPSHOT_REF",
    "P7_HOLD004_BACKEND_SUITE_COMMAND_SHAPE_ID",
    "P7_HOLD004_BACKEND_SUITE_DEFAULT_PYTEST_ARGS_ID",
    "P7_HOLD004_BACKEND_SUITE_EXECUTION_MODE",
    "P7_HOLD004_BACKEND_SUITE_EXECUTION_ORDER",
    "P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID",
    "P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_SCHEMA_VERSION",
    "P7_HOLD004_BACKEND_SUITE_GROUP_DEFINITIONS",
    "P7_HOLD004_BACKEND_SUITE_GROUP_IDS",
    "P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID",
    "P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_SCHEMA_VERSION",
    "P7_HOLD004_BACKEND_SUITE_GROUPING_RULE_VERSION",
    "P7_HOLD004_BACKEND_SUITE_PYTEST_ENV_ID",
    "P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_R2_R3_STEP",
    "P7_HOLD004_BACKEND_SUITE_TOTAL_BATCH_COUNT",
    "P7_HOLD004_BACKEND_SUITE_TOTAL_GROUP_FILE_COUNT",
    "P7_HOLD004_BACKEND_SUITE_TOTAL_GROUP_TEST_ITEM_COUNT",
    "assert_p7_hold004_backend_suite_execution_plan_contract",
    "assert_p7_hold004_backend_suite_group_inventory_contract",
    "build_p7_hold004_backend_suite_execution_plan",
    "build_p7_hold004_backend_suite_group_inventory",
    "build_p7_hold004_current_backend_suite_execution_plan",
    "build_p7_hold004_current_backend_suite_group_inventory",
    "classify_p7_hold004_backend_test_file_ref",
]
