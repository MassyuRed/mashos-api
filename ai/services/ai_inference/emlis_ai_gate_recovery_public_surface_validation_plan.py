# -*- coding: utf-8 -*-
from __future__ import annotations

"""P12 post-implementation validation plan for Gate Recovery public-surface repair.

This module is internal QA material.  It records which backend/frontend/manual
checks must pass after P0-P11, and it normalizes their results into a meta-only
validation plan.  It does not run pytest/npm commands, change public responses,
mutate RN contracts, apply rollout, or store raw/comment/candidate bodies.
"""

from collections.abc import Iterable, Mapping, Sequence
import json
from typing import Any, Final

from emlis_ai_gate_recovery_public_constants import (
    ALLOWED_PUBLIC_CANDIDATE_SOURCE_KINDS,
    BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC,
    BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
    BLOCKER_POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
    GATE_RECOVERY_PUBLIC_LEAK_BLOCKERS,
)

GATE_RECOVERY_PUBLIC_SURFACE_P12_VALIDATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.gate_recovery_public_surface.validation_plan.p12.v1"
)
GATE_RECOVERY_PUBLIC_SURFACE_P12_VALIDATION_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.gate_recovery_public_surface.validation_plan_row.p12.v1"
)
GATE_RECOVERY_PUBLIC_SURFACE_P12_ACCEPTANCE_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.gate_recovery_public_surface.acceptance_criterion.p12.v1"
)
GATE_RECOVERY_PUBLIC_SURFACE_P12_VALIDATION_PHASE: Final = (
    "GateRecoveryPublicSurfaceLeakRepair_P12_PostImplementationValidationPlan"
)
GATE_RECOVERY_PUBLIC_SURFACE_P12_TARGET_STEP: Final = (
    "P12_ImplementationAfterValidationPlan"
)

GATE_RECOVERY_PUBLIC_SURFACE_VALIDATION_SCHEMA_VERSION: Final = (
    GATE_RECOVERY_PUBLIC_SURFACE_P12_VALIDATION_SCHEMA_VERSION
)
GATE_RECOVERY_PUBLIC_SURFACE_VALIDATION_PLAN_SCHEMA_VERSION: Final = (
    GATE_RECOVERY_PUBLIC_SURFACE_P12_VALIDATION_SCHEMA_VERSION
)
GATE_RECOVERY_PUBLIC_SURFACE_VALIDATION_PHASE: Final = (
    GATE_RECOVERY_PUBLIC_SURFACE_P12_VALIDATION_PHASE
)
GATE_RECOVERY_PUBLIC_SURFACE_VALIDATION_TARGET_STEP: Final = (
    GATE_RECOVERY_PUBLIC_SURFACE_P12_TARGET_STEP
)

VALIDATION_STATUS_PASSED: Final = "passed"
VALIDATION_STATUS_FAILED: Final = "failed"
VALIDATION_STATUS_NOT_EXECUTED: Final = "not_executed"
VALIDATION_STATUS_BLOCKED: Final = "blocked"
VALIDATION_STATUS_SKIPPED: Final = "skipped"
VALIDATION_STATUSES: Final = (
    VALIDATION_STATUS_PASSED,
    VALIDATION_STATUS_FAILED,
    VALIDATION_STATUS_NOT_EXECUTED,
    VALIDATION_STATUS_BLOCKED,
    VALIDATION_STATUS_SKIPPED,
)

VALIDATION_GROUP_BACKEND: Final = "backend_pytest"
VALIDATION_GROUP_FRONTEND: Final = "frontend_rn_contract"
VALIDATION_GROUP_REAL_DEVICE: Final = "real_device_manual_regression"
VALIDATION_GROUP_PRODUCT_QUALITY: Final = "product_quality_surface_origin"

BLOCKER_P12_VALIDATION_EXECUTION_REQUIRED: Final = "p12_validation_execution_required"
BLOCKER_P12_REQUIRED_VALIDATION_FAILED: Final = "p12_required_validation_failed"
BLOCKER_P12_REQUIRED_VALIDATION_INCOMPLETE: Final = "p12_required_validation_incomplete"
BLOCKER_P12_ACCEPTANCE_CRITERION_NOT_MET: Final = "p12_acceptance_criterion_not_met"
BLOCKER_P12_SOURCE_TEXT_PAYLOAD_DETECTED: Final = "p12_source_text_payload_detected"
BLOCKER_P12_CONTRACT_RELAXATION_DETECTED: Final = "p12_contract_relaxation_detected"
BLOCKER_P12_RELEASE_FLAG_DETECTED: Final = "p12_release_flag_detected"

_TEXT_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
    {
        "raw_input", "rawInput", "raw_text", "rawText", "raw_user_text", "rawUserText",
        "source_text", "sourceText", "input", "input_text", "inputText", "user_input",
        "userInput", "current_input", "currentInput", "memo", "memo_text", "memoText",
        "memo_action", "memoAction", "comment_text", "commentText", "comment_text_body",
        "commentTextBody", "comment_body", "commentBody", "public_comment_text",
        "candidate_comment_text", "candidate_body", "candidateBody", "surface_body",
        "surfaceBody", "surface_text", "surfaceText", "visible_text", "visibleText",
        "reply_text", "replyText", "realized_text", "realizedText", "display_text",
        "displayText", "observation_text", "reception_text", "body", "text",
    }
)
_CONTRACT_TRUE_FLAGS: Final[frozenset[str]] = frozenset(
    {
        "api_route_changed", "request_key_changed", "response_shape_changed",
        "public_response_key_added", "public_response_key_change", "db_physical_name_changed",
        "rn_visible_contract_changed", "rn_visible_title_changed", "display_gate_relaxed",
        "grounding_gate_relaxed", "reader_gate_relaxed", "template_gate_relaxed", "gate_relaxed",
        "safety_gate_relaxed", "raw_input_included", "raw_text_included",
        "raw_user_text_included", "comment_text_included", "comment_text_body_included",
        "candidate_body_included", "surface_body_included", "fixed_sentence_template_added",
        "fixed_sentence_template_used", "input_specific_template_added",
        "runtime_fixture_branch_added", "runtime_fixture_branch_required",
        "case_specific_runtime_branch", "case_specific_runtime_condition_allowed",
        "runtime_branching_uses_fixture_strings", "fixture_text_used_for_runtime_branching",
        "external_ai_used", "local_llm_used",
    }
)
_RELEASE_APPLY_TRUE_FLAGS: Final[frozenset[str]] = frozenset(
    {
        "product_gate_ready", "product_gate_reached", "product_gate_achieved",
        "product_gate_public_release_applied", "product_quality_released", "public_release_applied",
        "release_decision_applied", "release_rollout_applied", "rollout_config_changed",
        "rollout_stage_mutated", "all_rollout_applied", "release_material_import_allowed",
        "public_meta_import_allowed",
    }
)

_EXECUTION_ITEMS: Final[tuple[dict[str, Any], ...]] = (
    {
        "execution_order": 1,
        "validation_item_id": "p0_p2_public_surface_boundary_contract",
        "validation_group": VALIDATION_GROUP_BACKEND,
        "command": "PYTHONPATH=services/ai_inference pytest -q tests/test_emlis_ai_gate_recovery_public_surface_boundary.py tests/test_emlis_ai_gate_recovery_public_boundary_decision.py",
        "source_artifacts": [
            "ai/tests/test_emlis_ai_gate_recovery_public_surface_boundary.py",
            "ai/tests/test_emlis_ai_gate_recovery_public_boundary_decision.py",
        ],
        "owner_area": "gate_recovery_public_boundary",
    },
    {
        "execution_order": 2,
        "validation_item_id": "p3_gate_recovery_loop_boundary_runtime",
        "validation_group": VALIDATION_GROUP_BACKEND,
        "command": "PYTHONPATH=services/ai_inference pytest -q tests/test_emlis_ai_gate_recovery_loop_phase20_5.py tests/test_emlis_ai_gate_recovery_surface_phase20_15.py tests/test_emlis_ai_post_final_gate_recovery_phase20_13.py",
        "source_artifacts": [
            "ai/tests/test_emlis_ai_gate_recovery_loop_phase20_5.py",
            "ai/tests/test_emlis_ai_gate_recovery_surface_phase20_15.py",
            "ai/tests/test_emlis_ai_post_final_gate_recovery_phase20_13.py",
        ],
        "owner_area": "gate_recovery_loop",
    },
    {
        "execution_order": 3,
        "validation_item_id": "p4_reply_service_public_boundary_guard",
        "validation_group": VALIDATION_GROUP_BACKEND,
        "command": "PYTHONPATH=services/ai_inference pytest -q tests/test_emlis_ai_reply_service_gate_recovery_public_boundary_p4.py",
        "source_artifacts": ["ai/tests/test_emlis_ai_reply_service_gate_recovery_public_boundary_p4.py"],
        "owner_area": "emlis_ai_reply_service",
    },
    {
        "execution_order": 4,
        "validation_item_id": "p5_public_candidate_builder",
        "validation_group": VALIDATION_GROUP_BACKEND,
        "command": "PYTHONPATH=services/ai_inference pytest -q tests/test_emlis_ai_gate_recovery_public_candidate_builder_p5.py",
        "source_artifacts": ["ai/tests/test_emlis_ai_gate_recovery_public_candidate_builder_p5.py"],
        "owner_area": "gate_recovery_public_candidate_builder",
    },
    {
        "execution_order": 5,
        "validation_item_id": "p6_low_information_recovery_connection",
        "validation_group": VALIDATION_GROUP_BACKEND,
        "command": "PYTHONPATH=services/ai_inference pytest -q tests/test_emlis_ai_gate_recovery_low_information_recovery_p6.py",
        "source_artifacts": ["ai/tests/test_emlis_ai_gate_recovery_low_information_recovery_p6.py"],
        "owner_area": "low_information_observation_composer_recovery",
    },
    {
        "execution_order": 6,
        "validation_item_id": "p7_bounded_original_repair_connection",
        "validation_group": VALIDATION_GROUP_BACKEND,
        "command": "PYTHONPATH=services/ai_inference pytest -q tests/test_emlis_ai_gate_recovery_original_candidate_repair_p7.py",
        "source_artifacts": ["ai/tests/test_emlis_ai_gate_recovery_original_candidate_repair_p7.py"],
        "owner_area": "bounded_original_candidate_repair",
    },
    {
        "execution_order": 7,
        "validation_item_id": "p8_surface_origin_measurement_runner",
        "validation_group": VALIDATION_GROUP_PRODUCT_QUALITY,
        "command": "PYTHONPATH=services/ai_inference pytest -q tests/test_emlis_ai_product_quality_surface_origin_p8.py tests/test_emlis_ai_product_quality_measurement_event.py tests/test_emlis_ai_product_quality_measurement_runner.py",
        "source_artifacts": [
            "ai/tests/test_emlis_ai_product_quality_surface_origin_p8.py",
            "ai/tests/test_emlis_ai_product_quality_measurement_event.py",
            "ai/tests/test_emlis_ai_product_quality_measurement_runner.py",
        ],
        "owner_area": "product_quality_surface_origin",
    },
    {
        "execution_order": 8,
        "validation_item_id": "p9_blocker_matrix_generation_repair_design",
        "validation_group": VALIDATION_GROUP_PRODUCT_QUALITY,
        "command": "PYTHONPATH=services/ai_inference pytest -q tests/test_emlis_ai_product_quality_gate_recovery_repair_design_p9.py tests/test_emlis_ai_product_quality_blocker_matrix.py tests/test_emlis_ai_product_quality_generation_repair_design.py",
        "source_artifacts": [
            "ai/tests/test_emlis_ai_product_quality_gate_recovery_repair_design_p9.py",
            "ai/tests/test_emlis_ai_product_quality_blocker_matrix.py",
            "ai/tests/test_emlis_ai_product_quality_generation_repair_design.py",
        ],
        "owner_area": "product_quality_blocker_matrix_and_generation_repair_design",
    },
    {
        "execution_order": 9,
        "validation_item_id": "p10_rn_contract_regression",
        "validation_group": VALIDATION_GROUP_FRONTEND,
        "command": "cd Cocolon && npm run test:rn-screens",
        "source_artifacts": ["Cocolon/tests/rn-screen-contracts.test.js"],
        "owner_area": "rn_public_feedback_contract",
    },
    {
        "execution_order": 10,
        "validation_item_id": "p11_real_device_regression_fixture_handling",
        "validation_group": VALIDATION_GROUP_REAL_DEVICE,
        "command": "PYTHONPATH=services/ai_inference pytest -q tests/test_emlis_ai_real_device_gate_recovery_regression_p11.py",
        "source_artifacts": [
            "ai/tests/test_emlis_ai_real_device_gate_recovery_regression_p11.py",
            "ai/tests/fixtures/emlis_ai_real_device_gate_recovery_regression_cases_p11.py",
        ],
        "owner_area": "real_device_regression_fixtures",
    },
    {
        "execution_order": 11,
        "validation_item_id": "emotion_submit_product_quality_e2e_regression",
        "validation_group": VALIDATION_GROUP_BACKEND,
        "command": "PYTHONPATH=services/ai_inference pytest -q tests/test_emotion_submit_phase18_product_quality_e2e.py",
        "source_artifacts": ["ai/tests/test_emotion_submit_phase18_product_quality_e2e.py"],
        "owner_area": "emotion_submit_product_quality_e2e",
    },
)

_REAL_DEVICE_CHECK_IDS: Final[tuple[str, ...]] = (
    "composer_disabled_gate_recovery_template_not_displayed",
    "composer_enabled_allowed_source_displayed",
    "feg_forbidden_fragments_absent",
    "gate_failure_display_source_lineage_allowed",
    "product_quality_not_green_while_blockers_remain",
)


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).strip()


def _safe_mapping(value: Any) -> dict[str, Any]:
    return {str(k): v for k, v in value.items()} if isinstance(value, Mapping) else {}


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (str, bytes, bytearray)):
        return [value]
    if isinstance(value, Mapping):
        return list(value.values())
    if isinstance(value, Iterable):
        return list(value)
    return [value]


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in _listify(values):
        text = _clean(item)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y", "on", "green", "pass", "passed", "ready", "allow", "allowed", "ok"}:
        return True
    if text in {"false", "0", "no", "n", "off", "red", "fail", "failed", "block", "blocked"}:
        return False
    return default


def _int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "" or isinstance(value, bool):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _status(value: Any) -> str:
    if isinstance(value, bool):
        return VALIDATION_STATUS_PASSED if value else VALIDATION_STATUS_FAILED
    safe = _safe_mapping(value)
    if safe:
        value = safe.get("status") or safe.get("validation_status") or safe.get("result") or safe.get("state")
    text = _clean(value).lower().replace(" ", "_").replace("-", "_")
    return {
        "pass": VALIDATION_STATUS_PASSED,
        "passed": VALIDATION_STATUS_PASSED,
        "green": VALIDATION_STATUS_PASSED,
        "ok": VALIDATION_STATUS_PASSED,
        "success": VALIDATION_STATUS_PASSED,
        "fail": VALIDATION_STATUS_FAILED,
        "failed": VALIDATION_STATUS_FAILED,
        "red": VALIDATION_STATUS_FAILED,
        "error": VALIDATION_STATUS_FAILED,
        "not_run": VALIDATION_STATUS_NOT_EXECUTED,
        "not_executed": VALIDATION_STATUS_NOT_EXECUTED,
        "pending": VALIDATION_STATUS_NOT_EXECUTED,
        "planned": VALIDATION_STATUS_NOT_EXECUTED,
        "blocked": VALIDATION_STATUS_BLOCKED,
        "skip": VALIDATION_STATUS_SKIPPED,
        "skipped": VALIDATION_STATUS_SKIPPED,
    }.get(text, VALIDATION_STATUS_NOT_EXECUTED)


def _contains_key(value: Any, keys: set[str] | frozenset[str]) -> bool:
    if isinstance(value, Mapping):
        for k, child in value.items():
            if str(k) in keys or _contains_key(child, keys):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_key(child, keys) for child in value)
    return False


def _true_flag_paths(value: Any, flags: set[str] | frozenset[str], *, path: str = "payload") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for k, child in value.items():
            child_path = f"{path}.{k}"
            if str(k) in flags and child is True:
                paths.append(child_path)
            paths.extend(_true_flag_paths(child, flags, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for i, child in enumerate(value):
            paths.extend(_true_flag_paths(child, flags, path=f"{path}[{i}]"))
    return paths


def _source_materials(*materials: Any) -> list[Any]:
    return [material for material in materials if material]


def _validation_result_for(item_id: str, validation_results: Mapping[str, Any] | None) -> dict[str, Any]:
    results = _safe_mapping(validation_results)
    result = results.get(item_id)
    if result is None:
        nested = _safe_mapping(results.get("items")) or _safe_mapping(results.get("validation_items"))
        result = nested.get(item_id)
    safe = _safe_mapping(result)
    return {
        "status": _status(safe or result),
        "passed_count": max(0, _int(safe.get("passed_count") or safe.get("passed") or safe.get("ok_count"))),
        "failed_count": max(0, _int(safe.get("failed_count") or safe.get("failed") or safe.get("error_count"))),
        "skipped_count": max(0, _int(safe.get("skipped_count") or safe.get("skipped"))),
        "warning_count": max(0, _int(safe.get("warning_count") or safe.get("warnings"))),
    }


def _validation_rows(validation_results: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for base in _EXECUTION_ITEMS:
        item_id = str(base["validation_item_id"])
        result = _validation_result_for(item_id, validation_results)
        status = result["status"]
        row = {
            "schema_version": GATE_RECOVERY_PUBLIC_SURFACE_P12_VALIDATION_ROW_SCHEMA_VERSION,
            "phase": GATE_RECOVERY_PUBLIC_SURFACE_P12_VALIDATION_PHASE,
            "target_step": GATE_RECOVERY_PUBLIC_SURFACE_P12_TARGET_STEP,
            "validation_item_id": item_id,
            "validation_group": base["validation_group"],
            "execution_order": int(base["execution_order"]),
            "required": True,
            "status": status,
            "passed": status == VALIDATION_STATUS_PASSED,
            "blocks_release_until_passed": True,
            "owner_area": base["owner_area"],
            "command": base["command"],
            "source_artifacts": list(base["source_artifacts"]),
            "passed_count": result["passed_count"],
            "failed_count": result["failed_count"],
            "skipped_count": result["skipped_count"],
            "warning_count": result["warning_count"],
            "contract_change_allowed": False,
            "gate_relaxation_allowed": False,
            "fixed_template_allowed": False,
            "runtime_fixture_branch_allowed": False,
            "public_response_key_added": False,
            "response_shape_changed": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "rn_visible_title_changed": False,
            "display_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "template_gate_relaxed": False,
            "raw_input_included": False,
            "comment_text_body_included": False,
            "candidate_body_included": False,
            "surface_body_included": False,
            "product_gate_ready": False,
            "public_release_applied": False,
        }
        assert_gate_recovery_public_surface_p12_validation_plan_meta_only(
            row,
            source=f"p12_validation_row.{item_id}",
            require_root_schema=False,
        )
        rows.append(row)
    return rows


def _real_device_check_rows(real_device_check_results: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    results = _safe_mapping(real_device_check_results)
    rows: list[dict[str, Any]] = []
    for index, check_id in enumerate(_REAL_DEVICE_CHECK_IDS, start=1):
        status = _status(results.get(check_id))
        row = {
            "schema_version": GATE_RECOVERY_PUBLIC_SURFACE_P12_VALIDATION_ROW_SCHEMA_VERSION,
            "phase": GATE_RECOVERY_PUBLIC_SURFACE_P12_VALIDATION_PHASE,
            "target_step": GATE_RECOVERY_PUBLIC_SURFACE_P12_TARGET_STEP,
            "validation_item_id": check_id,
            "validation_group": VALIDATION_GROUP_REAL_DEVICE,
            "execution_order": 100 + index,
            "required": True,
            "status": status,
            "passed": status == VALIDATION_STATUS_PASSED,
            "blocks_release_until_passed": True,
            "owner_area": "real_device_manual_regression",
            "command": "manual_real_device_check",
            "source_artifacts": ["F/E/G real-device observation screenshots/logs as local QA reference only"],
            "contract_change_allowed": False,
            "gate_relaxation_allowed": False,
            "runtime_fixture_branch_allowed": False,
            "fixed_template_allowed": False,
            "raw_input_included": False,
            "comment_text_body_included": False,
            "candidate_body_included": False,
            "surface_body_included": False,
            "product_gate_ready": False,
            "public_release_applied": False,
        }
        assert_gate_recovery_public_surface_p12_validation_plan_meta_only(
            row,
            source=f"p12_real_device_check.{check_id}",
            require_root_schema=False,
        )
        rows.append(row)
    return rows


def _blockers_from_measurement(measurement_run: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    blockers.extend(_dedupe(measurement_run.get("blockers")))
    blockers.extend(_dedupe(measurement_run.get("run_blockers")))
    blockers.extend(_dedupe(measurement_run.get("validation_blockers")))
    return _dedupe(blockers)


def _public_display_events(measurement_run: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    events = _listify(measurement_run.get("measurement_events"))
    return [event for event in events if isinstance(event, Mapping) and event.get("public_display_reached") is True]


def _surface_origin_present_for_displayed_candidates(measurement_run: Mapping[str, Any]) -> bool:
    public_events = _public_display_events(measurement_run)
    if public_events:
        return all(isinstance(event.get("surface_origin"), Mapping) and bool(event.get("surface_origin")) for event in public_events)
    machine_metrics = _safe_mapping(measurement_run.get("machine_metrics"))
    event_count = _int(machine_metrics.get("event_count") or measurement_run.get("event_count"))
    display_rate = machine_metrics.get("display_reach_rate")
    try:
        display_count = round(float(display_rate) * event_count) if display_rate is not None else 0
    except (TypeError, ValueError):
        display_count = 0
    surface_origin_count = _int(machine_metrics.get("surface_origin_event_count")) or _int(
        _safe_mapping(measurement_run.get("surface_origin_summary")).get("surface_origin_event_count")
    )
    return bool(display_count > 0 and surface_origin_count >= display_count)


def _display_reached_only_from_allowed_public_candidate_source(measurement_run: Mapping[str, Any]) -> bool:
    public_events = _public_display_events(measurement_run)
    if not public_events:
        return False
    for event in public_events:
        origin = _safe_mapping(event.get("surface_origin"))
        if _clean(origin.get("candidate_source_kind")) not in ALLOWED_PUBLIC_CANDIDATE_SOURCE_KINDS:
            return False
        if origin.get("public_display_allowed_by_boundary") is False:
            return False
    return True


def _metric_value(measurement_run: Mapping[str, Any], *keys: str) -> int:
    machine_metrics = _safe_mapping(measurement_run.get("machine_metrics"))
    surface_summary = _safe_mapping(measurement_run.get("surface_origin_summary"))
    summary_metrics = _safe_mapping(measurement_run.get("summary_metrics"))
    for key in keys:
        for source in (machine_metrics, surface_summary, summary_metrics, measurement_run):
            value = source.get(key) if isinstance(source, Mapping) else None
            if value is not None:
                return _int(value)
    return 0


def _criterion_row(
    *,
    criterion_id: str,
    owner_area: str,
    observed: Any,
    target: Any,
    passed: bool,
    comparator: str,
) -> dict[str, Any]:
    row = {
        "schema_version": GATE_RECOVERY_PUBLIC_SURFACE_P12_ACCEPTANCE_ROW_SCHEMA_VERSION,
        "phase": GATE_RECOVERY_PUBLIC_SURFACE_P12_VALIDATION_PHASE,
        "target_step": GATE_RECOVERY_PUBLIC_SURFACE_P12_TARGET_STEP,
        "criterion_id": criterion_id,
        "owner_area": owner_area,
        "observed_value": observed,
        "target_value": target,
        "comparator": comparator,
        "passed": bool(passed),
        "release_blocking": True,
        "contract_change_allowed": False,
        "gate_relaxation_allowed": False,
        "product_gate_ready": False,
        "public_release_applied": False,
    }
    assert_gate_recovery_public_surface_p12_validation_plan_meta_only(
        row,
        source=f"p12_acceptance_criterion.{criterion_id}",
        require_root_schema=False,
    )
    return row


def _acceptance_criteria(
    *,
    measurement_run: Mapping[str, Any],
    validation_rows: Sequence[Mapping[str, Any]],
    real_device_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    blockers = set(_blockers_from_measurement(measurement_run))
    gate_leak_blockers = sorted(blockers.intersection(GATE_RECOVERY_PUBLIC_LEAK_BLOCKERS))
    public_gate_recovery_count = _metric_value(
        measurement_run,
        "public_display_reached_via_gate_recovery_material_surface_count",
    )
    public_post_final_count = _metric_value(
        measurement_run,
        "public_display_reached_via_post_final_gate_recovery_material_surface_count",
    )
    public_diagnostic_count = _metric_value(
        measurement_run,
        "public_display_reached_via_diagnostic_recovery_surface_count",
        "public_diagnostic_recovery_surface_event_count",
    )
    p10_row = next((row for row in validation_rows if row.get("validation_item_id") == "p10_rn_contract_regression"), {})
    return [
        _criterion_row(
            criterion_id="gate_recovery_public_leak_blockers_zero",
            owner_area="product_quality_surface_origin",
            observed=len(gate_leak_blockers),
            target=0,
            comparator="==",
            passed=not gate_leak_blockers,
        ),
        _criterion_row(
            criterion_id="public_display_via_gate_recovery_material_surface_zero",
            owner_area="gate_recovery_public_boundary",
            observed=public_gate_recovery_count,
            target=0,
            comparator="==",
            passed=public_gate_recovery_count == 0,
        ),
        _criterion_row(
            criterion_id="public_display_via_post_final_gate_recovery_material_surface_zero",
            owner_area="post_final_gate_recovery_boundary",
            observed=public_post_final_count,
            target=0,
            comparator="==",
            passed=public_post_final_count == 0,
        ),
        _criterion_row(
            criterion_id="public_display_via_diagnostic_recovery_surface_zero",
            owner_area="diagnostic_recovery_surface_boundary",
            observed=public_diagnostic_count,
            target=0,
            comparator="==",
            passed=public_diagnostic_count == 0,
        ),
        _criterion_row(
            criterion_id="surface_origin_present_for_displayed_candidates",
            owner_area="product_quality_surface_origin",
            observed=_surface_origin_present_for_displayed_candidates(measurement_run),
            target=True,
            comparator="equals",
            passed=_surface_origin_present_for_displayed_candidates(measurement_run),
        ),
        _criterion_row(
            criterion_id="display_reached_only_from_allowed_public_candidate_source",
            owner_area="public_candidate_source_lineage",
            observed=_display_reached_only_from_allowed_public_candidate_source(measurement_run),
            target=True,
            comparator="equals",
            passed=_display_reached_only_from_allowed_public_candidate_source(measurement_run),
        ),
        _criterion_row(
            criterion_id="rn_contract_regression_passed",
            owner_area="rn_public_feedback_contract",
            observed=p10_row.get("status") == VALIDATION_STATUS_PASSED,
            target=True,
            comparator="equals",
            passed=p10_row.get("status") == VALIDATION_STATUS_PASSED,
        ),
        _criterion_row(
            criterion_id="real_device_manual_checks_passed",
            owner_area="real_device_manual_regression",
            observed=sum(1 for row in real_device_rows if row.get("passed") is True),
            target=len(real_device_rows),
            comparator="==",
            passed=bool(real_device_rows and all(row.get("passed") is True for row in real_device_rows)),
        ),
    ]


def assert_gate_recovery_public_surface_p12_validation_plan_meta_only(
    value: Mapping[str, Any],
    *,
    source: str = "gate_recovery_public_surface_p12_validation_plan",
    require_root_schema: bool = True,
) -> None:
    if not isinstance(value, Mapping):
        raise ValueError(f"{source} must be a mapping")
    if require_root_schema and value.get("schema_version") != GATE_RECOVERY_PUBLIC_SURFACE_P12_VALIDATION_SCHEMA_VERSION:
        raise ValueError(f"{source} has invalid schema_version")
    if _contains_key(value, _TEXT_PAYLOAD_KEYS):
        raise ValueError(f"{source} contains a forbidden source/body text payload key")
    if _true_flag_paths(value, _CONTRACT_TRUE_FLAGS):
        raise ValueError(f"{source} must not relax public/RN/DB/Gate contracts")
    if _true_flag_paths(value, _RELEASE_APPLY_TRUE_FLAGS):
        raise ValueError(f"{source} must not apply product gate or rollout release")
    if value.get("product_gate_ready") is True:
        raise ValueError(f"{source} must keep product_gate_ready false")
    if value.get("public_release_applied") is True:
        raise ValueError(f"{source} must keep public_release_applied false")


def build_gate_recovery_public_surface_p12_validation_results_stub(
    status: str = VALIDATION_STATUS_PASSED,
) -> dict[str, str]:
    normalized = _status(status)
    return {str(item["validation_item_id"]): normalized for item in _EXECUTION_ITEMS}


def build_gate_recovery_public_surface_p12_real_device_check_results_stub(
    status: str = VALIDATION_STATUS_PASSED,
) -> dict[str, str]:
    normalized = _status(status)
    return {check_id: normalized for check_id in _REAL_DEVICE_CHECK_IDS}


def build_gate_recovery_public_surface_p12_validation_plan(
    *,
    run_id: Any = "",
    measurement_run: Mapping[str, Any] | None = None,
    validation_results: Mapping[str, Any] | None = None,
    real_device_check_results: Mapping[str, Any] | None = None,
    frontend_validation_results: Mapping[str, Any] | None = None,
    product_quality_validation_plan: Mapping[str, Any] | None = None,
    extra_materials: Sequence[Any] | None = None,
) -> dict[str, Any]:
    run = dict(_safe_mapping(measurement_run))
    merged_results = dict(_safe_mapping(validation_results))
    if frontend_validation_results:
        merged_results.update(_safe_mapping(frontend_validation_results))
    rows = _validation_rows(merged_results)
    real_device_rows = _real_device_check_rows(real_device_check_results)
    all_rows = rows + real_device_rows
    criteria = _acceptance_criteria(
        measurement_run=run,
        validation_rows=rows,
        real_device_rows=real_device_rows,
    )
    materials = _source_materials(
        run,
        validation_results,
        frontend_validation_results,
        real_device_check_results,
        product_quality_validation_plan,
        *(extra_materials or []),
    )
    source_text_payload_detected = any(_contains_key(material, _TEXT_PAYLOAD_KEYS) for material in materials)
    contract_violation_paths = _dedupe(
        path
        for index, material in enumerate(materials)
        for path in _true_flag_paths(material, _CONTRACT_TRUE_FLAGS, path=f"source_materials[{index}]")
    )
    release_flag_paths = _dedupe(
        path
        for index, material in enumerate(materials)
        for path in _true_flag_paths(material, _RELEASE_APPLY_TRUE_FLAGS, path=f"source_materials[{index}]")
    )
    required_rows = [row for row in all_rows if row.get("required") is True]
    passed_rows = [row for row in required_rows if row.get("status") == VALIDATION_STATUS_PASSED]
    failed_rows = [row for row in required_rows if row.get("status") == VALIDATION_STATUS_FAILED]
    incomplete_rows = [
        row
        for row in required_rows
        if row.get("status") in {VALIDATION_STATUS_NOT_EXECUTED, VALIDATION_STATUS_BLOCKED}
    ]
    failed_criteria = [criterion for criterion in criteria if criterion.get("passed") is not True]
    measurement_blockers = _blockers_from_measurement(run)
    gate_leak_blockers = _dedupe(blocker for blocker in measurement_blockers if blocker in GATE_RECOVERY_PUBLIC_LEAK_BLOCKERS)

    blockers: list[str] = []
    if not validation_results or not frontend_validation_results or not real_device_check_results:
        blockers.append(BLOCKER_P12_VALIDATION_EXECUTION_REQUIRED)
    if incomplete_rows:
        blockers.append(BLOCKER_P12_REQUIRED_VALIDATION_INCOMPLETE)
    if failed_rows:
        blockers.append(BLOCKER_P12_REQUIRED_VALIDATION_FAILED)
    if failed_criteria:
        blockers.append(BLOCKER_P12_ACCEPTANCE_CRITERION_NOT_MET)
    blockers.extend(gate_leak_blockers)
    if source_text_payload_detected:
        blockers.append(BLOCKER_P12_SOURCE_TEXT_PAYLOAD_DETECTED)
    if contract_violation_paths:
        blockers.append(BLOCKER_P12_CONTRACT_RELAXATION_DETECTED)
    if release_flag_paths:
        blockers.append(BLOCKER_P12_RELEASE_FLAG_DETECTED)
    blockers = _dedupe(blockers)

    all_required_validation_passed = bool(required_rows and len(passed_rows) == len(required_rows))
    all_acceptance_criteria_passed = bool(criteria and not failed_criteria)
    validation_ready = bool(all_required_validation_passed and all_acceptance_criteria_passed and not blockers)
    execution_order = [str(row["validation_item_id"]) for row in all_rows]
    required_artifacts = _dedupe(artifact for row in rows for artifact in _listify(row.get("source_artifacts")))
    plan = {
        "schema_version": GATE_RECOVERY_PUBLIC_SURFACE_P12_VALIDATION_SCHEMA_VERSION,
        "version": GATE_RECOVERY_PUBLIC_SURFACE_P12_VALIDATION_SCHEMA_VERSION,
        "phase": GATE_RECOVERY_PUBLIC_SURFACE_P12_VALIDATION_PHASE,
        "target_step": GATE_RECOVERY_PUBLIC_SURFACE_P12_TARGET_STEP,
        "run_id": (_clean(run_id) or _clean(run.get("run_id")))[:96],
        "validation_status": "ready" if validation_ready else "blocked",
        "validation_plan_ready": True,
        "validation_ready": validation_ready,
        "validation_passed": validation_ready,
        "release_allowed_by_validation_plan": validation_ready,
        "release_allowed_by_p12_validation_plan": validation_ready,
        "validation_plan_internal_only": True,
        "validation_execution_required": bool(blockers),
        "validation_items": rows,
        "manual_validation_items": real_device_rows,
        "validation_steps": all_rows,
        "validation_execution_order": execution_order,
        "validation_execution_order_ids": execution_order,
        "required_test_files": required_artifacts,
        "validation_item_count": len(all_rows),
        "required_validation_item_count": len(required_rows),
        "required_validation_passed_count": len(passed_rows),
        "required_validation_failed_count": len(failed_rows),
        "required_validation_incomplete_count": len(incomplete_rows),
        "acceptance_criteria": criteria,
        "acceptance_criterion_count": len(criteria),
        "acceptance_criterion_failed_count": len(failed_criteria),
        "all_required_validation_passed": all_required_validation_passed,
        "all_acceptance_criteria_passed": all_acceptance_criteria_passed,
        "validation_blockers": blockers,
        "release_blockers": blockers,
        "validation_blocker_count": len(blockers),
        "gate_recovery_public_leak_blockers": gate_leak_blockers,
        "source_text_payload_detected": source_text_payload_detected,
        "source_contract_violation_paths": contract_violation_paths,
        "source_release_flag_paths": release_flag_paths,
        "expected_runtime_policy": {
            "composer_disabled_gate_recovery_template_not_displayed": True,
            "composer_enabled_public_candidate_source_required": True,
            "feg_exact_body_lock_allowed": False,
            "runtime_fixture_branch_allowed": False,
            "gate_recovery_material_surface_public_candidate_allowed": False,
            "post_final_direct_material_surface_promotion_allowed": False,
            "diagnostic_recovery_surface_to_comment_text_allowed": False,
            "public_response_shape_changed": False,
            "rn_contract_changed": False,
        },
        "allowed_public_candidate_source_kinds": sorted(ALLOWED_PUBLIC_CANDIDATE_SOURCE_KINDS),
        "blocked_public_leak_blockers": sorted(GATE_RECOVERY_PUBLIC_LEAK_BLOCKERS),
        "source_material_status": {
            "measurement_run_connected": bool(run),
            "product_quality_validation_plan_connected": bool(product_quality_validation_plan),
            "backend_validation_results_connected": bool(validation_results),
            "frontend_validation_results_connected": bool(frontend_validation_results),
            "real_device_check_results_connected": bool(real_device_check_results),
        },
        "surface_origin_observed_counts": {
            "public_display_reached_via_gate_recovery_material_surface_count": _metric_value(
                run,
                "public_display_reached_via_gate_recovery_material_surface_count",
            ),
            "public_display_reached_via_post_final_gate_recovery_material_surface_count": _metric_value(
                run,
                "public_display_reached_via_post_final_gate_recovery_material_surface_count",
            ),
            "public_display_reached_via_diagnostic_recovery_surface_count": _metric_value(
                run,
                "public_display_reached_via_diagnostic_recovery_surface_count",
                "public_diagnostic_recovery_surface_event_count",
            ),
            "surface_origin_event_count": _metric_value(run, "surface_origin_event_count"),
        },
        "contract_assertions": {
            "api_route_changed": False,
            "response_shape_changed": False,
            "public_response_key_added": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "rn_visible_title_changed": False,
            "display_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "template_gate_relaxed": False,
            "safety_gate_relaxed": False,
            "raw_input_included": False,
            "comment_text_body_included": False,
            "candidate_body_included": False,
            "surface_body_included": False,
        },
        "summary": {
            "validation_status": "ready" if validation_ready else "blocked",
            "validation_ready": validation_ready,
            "validation_passed": validation_ready,
            "release_allowed_by_validation_plan": validation_ready,
            "release_allowed_by_p12_validation_plan": validation_ready,
            "validation_blocker_count": len(blockers),
            "acceptance_criterion_failed_count": len(failed_criteria),
            "product_gate_ready": False,
            "public_release_applied": False,
        },
        "public_contract_changed": False,
        "rn_contract_changed": False,
        "db_schema_changed": False,
        "public_response_key_added": False,
        "api_route_changed": False,
        "response_shape_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "safety_gate_relaxed": False,
        "fixed_sentence_template_added": False,
        "fixed_sentence_template_used": False,
        "input_specific_template_added": False,
        "runtime_fixture_branch_added": False,
        "runtime_fixture_branch_required": False,
        "external_ai_used": False,
        "local_llm_used": False,
        "release_decision_applied": False,
        "release_rollout_applied": False,
        "rollout_config_changed": False,
        "rollout_stage_mutated": False,
        "all_rollout_applied": False,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "product_gate_public_release_applied": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "raw_user_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
    }
    assert_gate_recovery_public_surface_p12_validation_plan_meta_only(plan)
    return plan


def dump_gate_recovery_public_surface_p12_validation_plan(plan: Mapping[str, Any]) -> str:
    data = _safe_mapping(plan)
    assert_gate_recovery_public_surface_p12_validation_plan_meta_only(data)
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def assert_gate_recovery_public_surface_validation_plan_meta_only(
    value: Mapping[str, Any],
    *,
    source: str = "gate_recovery_public_surface_validation_plan",
    require_root_schema: bool = True,
) -> None:
    assert_gate_recovery_public_surface_p12_validation_plan_meta_only(
        value,
        source=source,
        require_root_schema=require_root_schema,
    )


def build_gate_recovery_public_surface_validation_plan(
    *,
    run_id: Any = "",
    measurement_run: Mapping[str, Any] | None = None,
    validation_results: Mapping[str, Any] | None = None,
    real_device_check_results: Mapping[str, Any] | None = None,
    real_device_results: Mapping[str, Any] | None = None,
    frontend_validation_results: Mapping[str, Any] | None = None,
    product_quality_validation_plan: Mapping[str, Any] | None = None,
    extra_materials: Sequence[Any] | None = None,
) -> dict[str, Any]:
    return build_gate_recovery_public_surface_p12_validation_plan(
        run_id=run_id,
        measurement_run=measurement_run,
        validation_results=validation_results,
        real_device_check_results=real_device_check_results or real_device_results,
        frontend_validation_results=frontend_validation_results,
        product_quality_validation_plan=product_quality_validation_plan,
        extra_materials=extra_materials,
    )


def build_gate_recovery_public_surface_validation_results_stub(
    status: str = VALIDATION_STATUS_PASSED,
) -> dict[str, str]:
    return build_gate_recovery_public_surface_p12_validation_results_stub(status)


def build_gate_recovery_public_surface_real_device_results_stub(
    status: str = VALIDATION_STATUS_PASSED,
) -> dict[str, str]:
    return build_gate_recovery_public_surface_p12_real_device_check_results_stub(status)


def build_gate_recovery_public_surface_real_device_check_results_stub(
    status: str = VALIDATION_STATUS_PASSED,
) -> dict[str, str]:
    return build_gate_recovery_public_surface_p12_real_device_check_results_stub(status)


def dump_gate_recovery_public_surface_validation_plan(plan: Mapping[str, Any]) -> str:
    return dump_gate_recovery_public_surface_p12_validation_plan(plan)


__all__ = [
    "BLOCKER_P12_ACCEPTANCE_CRITERION_NOT_MET",
    "BLOCKER_P12_CONTRACT_RELAXATION_DETECTED",
    "BLOCKER_P12_RELEASE_FLAG_DETECTED",
    "BLOCKER_P12_REQUIRED_VALIDATION_FAILED",
    "BLOCKER_P12_REQUIRED_VALIDATION_INCOMPLETE",
    "BLOCKER_P12_SOURCE_TEXT_PAYLOAD_DETECTED",
    "BLOCKER_P12_VALIDATION_EXECUTION_REQUIRED",
    "GATE_RECOVERY_PUBLIC_SURFACE_P12_ACCEPTANCE_ROW_SCHEMA_VERSION",
    "GATE_RECOVERY_PUBLIC_SURFACE_P12_TARGET_STEP",
    "GATE_RECOVERY_PUBLIC_SURFACE_P12_VALIDATION_PHASE",
    "GATE_RECOVERY_PUBLIC_SURFACE_P12_VALIDATION_ROW_SCHEMA_VERSION",
    "GATE_RECOVERY_PUBLIC_SURFACE_P12_VALIDATION_SCHEMA_VERSION",
    "GATE_RECOVERY_PUBLIC_SURFACE_VALIDATION_PHASE",
    "GATE_RECOVERY_PUBLIC_SURFACE_VALIDATION_PLAN_SCHEMA_VERSION",
    "GATE_RECOVERY_PUBLIC_SURFACE_VALIDATION_SCHEMA_VERSION",
    "GATE_RECOVERY_PUBLIC_SURFACE_VALIDATION_TARGET_STEP",
    "assert_gate_recovery_public_surface_validation_plan_meta_only",
    "build_gate_recovery_public_surface_real_device_results_stub",
    "build_gate_recovery_public_surface_real_device_check_results_stub",
    "build_gate_recovery_public_surface_validation_plan",
    "build_gate_recovery_public_surface_validation_results_stub",
    "dump_gate_recovery_public_surface_validation_plan",
    "VALIDATION_STATUS_FAILED",
    "VALIDATION_STATUS_NOT_EXECUTED",
    "VALIDATION_STATUS_PASSED",
    "assert_gate_recovery_public_surface_p12_validation_plan_meta_only",
    "build_gate_recovery_public_surface_p12_real_device_check_results_stub",
    "build_gate_recovery_public_surface_p12_validation_plan",
    "build_gate_recovery_public_surface_p12_validation_results_stub",
    "dump_gate_recovery_public_surface_p12_validation_plan",
]
