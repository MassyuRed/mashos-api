# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 8 Validation Plan for EmlisAI Product Quality.

This module turns the Phase 0-7 internal QA materials into a fixed validation
plan and validation-readiness material.  It does not run tests, change public
responses, change RN contracts, mutate DB schema, relax gates, apply rollout, or
store raw/comment/candidate bodies.
"""

from collections.abc import Iterable, Mapping, Sequence
import json
from typing import Any, Final

from emlis_ai_product_quality_contract_freeze import (
    assert_emlis_ai_product_quality_contract_freeze_meta_only,
    build_emlis_ai_product_quality_contract_freeze,
)

PRODUCT_QUALITY_VALIDATION_PLAN_SCHEMA_VERSION: Final = (
    "cocolon.emlis.product_quality.validation_plan.v1"
)
PRODUCT_QUALITY_VALIDATION_PLAN_VERSION: Final = PRODUCT_QUALITY_VALIDATION_PLAN_SCHEMA_VERSION
PRODUCT_QUALITY_VALIDATION_PLAN_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.product_quality.validation_plan_row.v1"
)
PRODUCT_QUALITY_ACCEPTANCE_CRITERION_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.product_quality.acceptance_criterion_row.v1"
)
PRODUCT_QUALITY_VALIDATION_PLAN_PHASE: Final = "Phase8_ValidationPlan"
PRODUCT_QUALITY_VALIDATION_PLAN_TARGET_STEP: Final = "EmlisAI_ProductQuality_ValidationPlan"

GATE_RECOVERY_PUBLIC_SURFACE_LEAK_REPAIR_P12_SCHEMA_VERSION: Final = (
    "cocolon.emlis.gate_recovery_public_surface_leak_repair.validation_plan.v1"
)
GATE_RECOVERY_PUBLIC_SURFACE_LEAK_REPAIR_P12_PHASE: Final = (
    "GateRecoveryPublicSurfaceLeakRepair_P12_ValidationPlan"
)
P12_BACKEND_VALIDATION_COMMANDS: Final[tuple[str, ...]] = (
    "PYTHONPATH=services/ai_inference pytest -q tests/test_emlis_ai_gate_recovery_public_surface_boundary.py",
    "PYTHONPATH=services/ai_inference pytest -q tests/test_emlis_ai_gate_recovery_surface_phase20_15.py",
    "PYTHONPATH=services/ai_inference pytest -q tests/test_emlis_ai_post_final_gate_recovery_phase20_13.py",
    "PYTHONPATH=services/ai_inference pytest -q tests/test_emlis_ai_product_quality_measurement_event.py",
    "PYTHONPATH=services/ai_inference pytest -q tests/test_emlis_ai_product_quality_measurement_runner.py",
    "PYTHONPATH=services/ai_inference pytest -q tests/test_emlis_ai_product_quality_blocker_matrix.py",
    "PYTHONPATH=services/ai_inference pytest -q tests/test_emlis_ai_product_quality_generation_repair_design.py",
    "PYTHONPATH=services/ai_inference pytest -q tests/test_emotion_submit_phase18_product_quality_e2e.py",
)
P12_FRONTEND_VALIDATION_COMMANDS: Final[tuple[str, ...]] = (
    "cd Cocolon && npm run test:rn-screens",
)
P12_REAL_DEVICE_VALIDATION_CHECKS: Final[tuple[str, ...]] = (
    "composer_disabled_does_not_public_display_gate_recovery_template",
    "composer_enabled_public_observation_uses_allowed_source",
    "feg_inputs_do_not_emit_gate_recovery_template_fragments",
    "gate_failure_public_display_lineage_is_low_info_repaired_original_or_safe_state",
    "product_quality_measurement_keeps_blockers_until_all_p12_criteria_pass",
)
P12_FORBIDDEN_PUBLIC_SURFACE_FRAGMENTS: Final[tuple[str, ...]] = (
    "今回の入力では",
    "原因や結論までは決めず",
    "誰かを良い悪いで決めず",
)
P12_ALLOWED_PUBLIC_CANDIDATE_SOURCES: Final[tuple[str, ...]] = (
    "complete_initial_composer",
    "limited_composer",
    "low_information_observation_composer",
    "self_denial_safe_state_answer",
    "bounded_repaired_original_candidate",
    "complete_self_repair_candidate",
    "normal_observation_rebuild_candidate",
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

VALIDATION_GROUP_CONTRACT: Final = "contract"
VALIDATION_GROUP_UNIT: Final = "unit"
VALIDATION_GROUP_REGRESSION: Final = "regression"
VALIDATION_GROUP_PRODUCT_QUALITY: Final = "product_quality"
VALIDATION_GROUP_E2E_PUBLIC_BOUNDARY: Final = "e2e_public_boundary"
VALIDATION_GROUPS: Final = (
    VALIDATION_GROUP_CONTRACT,
    VALIDATION_GROUP_UNIT,
    VALIDATION_GROUP_REGRESSION,
    VALIDATION_GROUP_PRODUCT_QUALITY,
    VALIDATION_GROUP_E2E_PUBLIC_BOUNDARY,
)

DISPLAY_REACH_RATE_TARGET: Final = 0.90
BINDING_PASS_RATE_TARGET: Final = 0.98
REASON_COVERAGE_RATE_TARGET: Final = 1.0
REQUIRED_FAMILY_COVERAGE_RATE_TARGET: Final = 1.0
RUNTIME_SURFACE_BLIND_QA_COVERAGE_RATE_TARGET: Final = 1.0
RUNTIME_SURFACE_READ_FEELING_SCORE_TARGET: Final = 0.90
USER_LABEL_CONNECTION_QA_COVERAGE_RATE_TARGET: Final = 1.0
USER_LABEL_CONNECTION_QUALITY_SCORE_TARGET: Final = 0.90

BLOCKER_VALIDATION_EXECUTION_REQUIRED: Final = "phase8_validation_execution_required"
BLOCKER_REQUIRED_VALIDATION_INCOMPLETE: Final = "phase8_required_validation_incomplete"
BLOCKER_REQUIRED_VALIDATION_FAILED: Final = "phase8_required_validation_failed"
BLOCKER_ACCEPTANCE_CRITERION_NOT_MET: Final = "phase8_acceptance_criterion_not_met"
BLOCKER_RELEASE_DECISION_NOT_GREEN: Final = "phase8_release_decision_not_green"
BLOCKER_SOURCE_TEXT_PAYLOAD_DETECTED: Final = "phase8_source_text_payload_detected"
BLOCKER_CONTRACT_RELAXATION_DETECTED: Final = "phase8_contract_relaxation_detected"
BLOCKER_RELEASE_FLAG_DETECTED: Final = "phase8_release_flag_detected"

_TEXT_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
    {
        "raw_input", "rawInput", "raw_text", "rawText", "raw_user_text", "rawUserText",
        "source_text", "sourceText", "input", "input_text", "inputText", "user_input",
        "userInput", "current_input", "currentInput", "memo", "memo_text", "memoText",
        "memo_action", "memoAction", "comment_text", "commentText", "comment_text_body",
        "commentTextBody", "comment_body", "commentBody", "input_feedback_comment",
        "public_comment_text", "candidate_comment_text", "candidate_body", "candidateBody",
        "surface_body", "surfaceBody", "surface_text", "surfaceText", "visible_text",
        "visibleText", "reply_text", "replyText", "realized_text", "realizedText",
        "display_text", "displayText", "observation_text", "reception_text", "body", "text",
    }
)
_CONTRACT_TRUE_FLAGS: Final[frozenset[str]] = frozenset(
    {
        "api_route_changed", "request_key_changed", "response_shape_changed",
        "public_response_key_added", "public_response_key_change", "db_physical_name_changed",
        "rn_visible_contract_changed", "rn_visible_title_changed", "display_gate_relaxed",
        "grounding_gate_relaxed", "reader_gate_relaxed", "template_gate_relaxed", "gate_relaxed",
        "raw_input_included", "raw_text_included", "raw_user_text_included", "comment_text_included",
        "comment_text_body_included", "candidate_body_included", "surface_body_included",
        "machine_metrics_used_for_read_feeling", "read_feeling_auto_filled_from_machine_metrics",
        "read_feeling_auto_estimation_allowed", "fixed_sentence_template_added",
        "fixed_sentence_template_used", "input_specific_template_added",
        "runtime_fixture_branch_added", "runtime_fixture_branch_required", "external_ai_used", "local_llm_used",
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
_CONTRACT_KEYS: Final = (
    "api_route_changed", "response_shape_changed", "public_response_key_added",
    "db_physical_name_changed", "rn_visible_contract_changed", "rn_visible_title_changed",
    "display_gate_relaxed", "grounding_gate_relaxed", "template_gate_relaxed",
    "raw_input_included", "raw_text_included", "comment_text_body_included",
    "candidate_body_included", "surface_body_included",
)

_EXECUTION_ORDER: Final[tuple[dict[str, Any], ...]] = (
    {
        "order": 1,
        "validation_item_id": "public_boundary_and_rn_contract_tests",
        "validation_group": VALIDATION_GROUP_CONTRACT,
        "source_artifacts": [
            "Cocolon/tests/rn-screen-contracts.test.js",
            "ai/tests/test_emlis_ai_public_feedback_meta.py",
            "ai/tests/test_emotion_submit_public_feedback_meta_boundary.py",
        ],
        "owner_area": "public_boundary_contract",
    },
    {
        "order": 2,
        "validation_item_id": "product_quality_event_schema_tests",
        "validation_group": VALIDATION_GROUP_UNIT,
        "source_artifacts": ["ai/tests/test_emlis_ai_product_quality_measurement_event.py"],
        "owner_area": "product_quality_measurement_event",
    },
    {
        "order": 3,
        "validation_item_id": "measurement_runner_dry_run_tests",
        "validation_group": VALIDATION_GROUP_UNIT,
        "source_artifacts": ["ai/tests/test_emlis_ai_product_quality_measurement_runner.py"],
        "owner_area": "product_quality_measurement_runner",
    },
    {
        "order": 4,
        "validation_item_id": "product_readfeel_scorecard_tests",
        "validation_group": VALIDATION_GROUP_PRODUCT_QUALITY,
        "source_artifacts": ["ai/tests/test_emlis_ai_product_readfeel_scorecard.py"],
        "owner_area": "product_readfeel_scorecard",
    },
    {
        "order": 5,
        "validation_item_id": "runtime_surface_blind_qa_candidate_review_summary_tests",
        "validation_group": VALIDATION_GROUP_PRODUCT_QUALITY,
        "source_artifacts": [
            "ai/tests/test_emlis_ai_runtime_surface_blind_qa_long_run_step11.py",
            "ai/tests/test_emlis_ai_product_quality_blind_qa_integration.py",
        ],
        "owner_area": "runtime_surface_blind_qa",
    },
    {
        "order": 6,
        "validation_item_id": "user_label_connection_product_quality_qa_tests",
        "validation_group": VALIDATION_GROUP_PRODUCT_QUALITY,
        "source_artifacts": [
            "ai/tests/test_emlis_ai_user_label_connection_product_quality_qa.py",
            "ai/tests/test_emlis_ai_product_quality_blind_qa_integration.py",
        ],
        "owner_area": "user_label_connection_product_quality_qa",
    },
    {
        "order": 7,
        "validation_item_id": "phase11_long_run_product_gate_tests",
        "validation_group": VALIDATION_GROUP_PRODUCT_QUALITY,
        "source_artifacts": ["ai/tests/test_emlis_ai_product_readfeel_phase11_long_run_product_gate.py"],
        "owner_area": "phase11_long_run_product_gate",
    },
    {
        "order": 8,
        "validation_item_id": "blocker_matrix_tests",
        "validation_group": VALIDATION_GROUP_UNIT,
        "source_artifacts": ["ai/tests/test_emlis_ai_product_quality_blocker_matrix.py"],
        "owner_area": "product_quality_blocker_matrix",
    },
    {
        "order": 9,
        "validation_item_id": "release_decision_tests",
        "validation_group": VALIDATION_GROUP_UNIT,
        "source_artifacts": ["ai/tests/test_emlis_ai_product_release_decision.py"],
        "owner_area": "product_release_decision",
    },
    {
        "order": 10,
        "validation_item_id": "emotion_submit_public_boundary_e2e_tests",
        "validation_group": VALIDATION_GROUP_E2E_PUBLIC_BOUNDARY,
        "source_artifacts": [
            "ai/tests/test_emotion_submit_public_feedback_meta_boundary.py",
            "ai/tests/test_emlis_ai_public_boundary_phase20_7.py",
        ],
        "owner_area": "emotion_submit_public_boundary",
    },
    {
        "order": 11,
        "validation_item_id": "p12_gate_recovery_public_boundary_regression_tests",
        "validation_group": VALIDATION_GROUP_REGRESSION,
        "source_artifacts": [
            "ai/tests/test_emlis_ai_gate_recovery_public_surface_boundary.py",
            "ai/tests/test_emlis_ai_gate_recovery_public_boundary_decision.py",
        ],
        "owner_area": "gate_recovery_public_boundary",
    },
    {
        "order": 12,
        "validation_item_id": "p12_gate_recovery_phase20_surface_regression_tests",
        "validation_group": VALIDATION_GROUP_REGRESSION,
        "source_artifacts": [
            "ai/tests/test_emlis_ai_gate_recovery_loop_phase20_5.py",
            "ai/tests/test_emlis_ai_gate_recovery_surface_phase20_15.py",
        ],
        "owner_area": "gate_recovery_loop_surface_boundary",
    },
    {
        "order": 13,
        "validation_item_id": "p12_post_final_gate_recovery_boundary_regression_tests",
        "validation_group": VALIDATION_GROUP_REGRESSION,
        "source_artifacts": ["ai/tests/test_emlis_ai_post_final_gate_recovery_phase20_13.py"],
        "owner_area": "post_final_gate_recovery_boundary",
    },
    {
        "order": 14,
        "validation_item_id": "p12_allowed_recovery_source_regression_tests",
        "validation_group": VALIDATION_GROUP_REGRESSION,
        "source_artifacts": [
            "ai/tests/test_emlis_ai_gate_recovery_public_candidate_builder_p5.py",
            "ai/tests/test_emlis_ai_gate_recovery_low_information_recovery_p6.py",
            "ai/tests/test_emlis_ai_gate_recovery_original_candidate_repair_p7.py",
            "ai/tests/test_emlis_ai_reply_service_gate_recovery_public_boundary_p4.py",
        ],
        "owner_area": "gate_recovery_allowed_public_candidate_builder",
    },
    {
        "order": 15,
        "validation_item_id": "p12_surface_origin_measurement_regression_tests",
        "validation_group": VALIDATION_GROUP_PRODUCT_QUALITY,
        "source_artifacts": [
            "ai/tests/test_emlis_ai_product_quality_surface_origin_p8.py",
            "ai/tests/test_emlis_ai_product_quality_measurement_event.py",
            "ai/tests/test_emlis_ai_product_quality_measurement_runner.py",
        ],
        "owner_area": "product_quality_surface_origin",
    },
    {
        "order": 16,
        "validation_item_id": "p12_gate_recovery_repair_design_queue_tests",
        "validation_group": VALIDATION_GROUP_PRODUCT_QUALITY,
        "source_artifacts": [
            "ai/tests/test_emlis_ai_product_quality_gate_recovery_repair_design_p9.py",
            "ai/tests/test_emlis_ai_product_quality_blocker_matrix.py",
            "ai/tests/test_emlis_ai_product_quality_generation_repair_design.py",
        ],
        "owner_area": "gate_recovery_blocker_repair_design",
    },
    {
        "order": 17,
        "validation_item_id": "p12_real_device_regression_fixture_handling_tests",
        "validation_group": VALIDATION_GROUP_REGRESSION,
        "source_artifacts": ["ai/tests/test_emlis_ai_real_device_gate_recovery_regression_p11.py"],
        "owner_area": "real_device_regression_fixture_handling",
    },
    {
        "order": 18,
        "validation_item_id": "p12_emotion_submit_product_quality_e2e_tests",
        "validation_group": VALIDATION_GROUP_E2E_PUBLIC_BOUNDARY,
        "source_artifacts": ["ai/tests/test_emotion_submit_phase18_product_quality_e2e.py"],
        "owner_area": "emotion_submit_product_quality_e2e",
    },
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
    if text in {"true", "1", "yes", "y", "on", "green", "pass", "passed", "ready", "allow", "allowed"}:
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


def _float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None or value == "" or isinstance(value, bool):
            return default
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return default


def _rate(numerator: int, denominator: int) -> float:
    return round(float(numerator) / float(denominator), 6) if denominator > 0 else 0.0


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


def _status(value: Any) -> str:
    if isinstance(value, bool):
        return VALIDATION_STATUS_PASSED if value else VALIDATION_STATUS_FAILED
    safe = _safe_mapping(value)
    if safe:
        value = safe.get("status") or safe.get("validation_status") or safe.get("result") or safe.get("state")
    text = _clean(value).lower().replace(" ", "_").replace("-", "_")
    aliases = {
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
    }
    return aliases.get(text, VALIDATION_STATUS_NOT_EXECUTED)


def _result_details(value: Any) -> dict[str, Any]:
    safe = _safe_mapping(value)
    if not safe:
        return {
            "status": _status(value),
            "passed_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "warning_count": 0,
            "duration_seconds": None,
        }
    return {
        "status": _status(safe),
        "passed_count": max(0, _int(safe.get("passed_count") or safe.get("passed") or safe.get("ok_count"))),
        "failed_count": max(0, _int(safe.get("failed_count") or safe.get("failed") or safe.get("error_count"))),
        "skipped_count": max(0, _int(safe.get("skipped_count") or safe.get("skipped"))),
        "warning_count": max(0, _int(safe.get("warning_count") or safe.get("warnings"))),
        "duration_seconds": _float(safe.get("duration_seconds"), default=None),
    }


def _validation_result_for(item_id: str, validation_results: Mapping[str, Any] | None) -> dict[str, Any]:
    results = _safe_mapping(validation_results)
    result = results.get(item_id)
    if result is None:
        group_results = _safe_mapping(results.get("items")) or _safe_mapping(results.get("validation_items"))
        result = group_results.get(item_id)
    return _result_details(result)


def _validation_rows(validation_results: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for base in _EXECUTION_ORDER:
        item_id = str(base["validation_item_id"])
        result = _validation_result_for(item_id, validation_results)
        status = result["status"]
        required = True
        row = {
            "schema_version": PRODUCT_QUALITY_VALIDATION_PLAN_ROW_SCHEMA_VERSION,
            "version": PRODUCT_QUALITY_VALIDATION_PLAN_ROW_SCHEMA_VERSION,
            "phase": PRODUCT_QUALITY_VALIDATION_PLAN_PHASE,
            "target_step": PRODUCT_QUALITY_VALIDATION_PLAN_TARGET_STEP,
            "validation_item_id": item_id,
            "validation_group": base["validation_group"],
            "execution_order": base["order"],
            "required": required,
            "status": status,
            "passed": status == VALIDATION_STATUS_PASSED,
            "blocks_release_until_passed": required,
            "owner_area": base["owner_area"],
            "source_artifacts": list(base["source_artifacts"]),
            "passed_count": result["passed_count"],
            "failed_count": result["failed_count"],
            "skipped_count": result["skipped_count"],
            "warning_count": result["warning_count"],
            "duration_seconds": result["duration_seconds"],
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
            "raw_text_included": False,
            "comment_text_body_included": False,
            "candidate_body_included": False,
            "surface_body_included": False,
            "product_gate_ready": False,
            "public_release_applied": False,
        }
        assert_product_quality_validation_plan_meta_only(row, source=f"validation_plan_row.{item_id}", require_root_schema=False)
        rows.append(row)
    return rows


def _group_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}
    for group in VALIDATION_GROUPS:
        group_rows = [row for row in rows if row.get("validation_group") == group]
        required = [row for row in group_rows if row.get("required") is True]
        passed = [row for row in required if row.get("status") == VALIDATION_STATUS_PASSED]
        failed = [row for row in required if row.get("status") == VALIDATION_STATUS_FAILED]
        not_executed = [row for row in required if row.get("status") == VALIDATION_STATUS_NOT_EXECUTED]
        blocked = [row for row in required if row.get("status") == VALIDATION_STATUS_BLOCKED]
        summary[group] = {
            "required_count": len(required),
            "passed_count": len(passed),
            "failed_count": len(failed),
            "not_executed_count": len(not_executed),
            "blocked_count": len(blocked),
            "required_pass_rate": _rate(len(passed), len(required)),
            "group_ready": bool(required and len(passed) == len(required)),
        }
    return summary


def _contract_assertions() -> dict[str, bool]:
    return {
        "api_route_changed": False,
        "response_shape_changed": False,
        "public_response_key_added": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
    }


def _source_materials(*materials: Any) -> list[Any]:
    return [material for material in materials if material]


def _contract_violation_paths(materials: Sequence[Any]) -> list[str]:
    paths: list[str] = []
    for idx, material in enumerate(materials):
        paths.extend(_true_flag_paths(material, _CONTRACT_TRUE_FLAGS, path=f"source_materials[{idx}]"))
    return _dedupe(paths)


def _release_flag_paths(materials: Sequence[Any]) -> list[str]:
    paths: list[str] = []
    for idx, material in enumerate(materials):
        paths.extend(_true_flag_paths(material, _RELEASE_APPLY_TRUE_FLAGS, path=f"source_materials[{idx}]"))
    return _dedupe(paths)


def _summary_metrics_from_sources(
    *,
    measurement_run: Mapping[str, Any],
    summary_metrics: Mapping[str, Any] | None,
    runtime_surface_blind_qa_long_run_summary: Mapping[str, Any] | None,
    user_label_connection_qa_summary: Mapping[str, Any] | None,
    phase11_long_run_product_gate: Mapping[str, Any] | None,
    blind_qa_integration: Mapping[str, Any] | None,
) -> dict[str, Any]:
    run_metrics = _safe_mapping(measurement_run.get("summary_metrics"))
    metrics = dict(run_metrics)
    metrics.update(_safe_mapping(summary_metrics))
    runtime_summary = _safe_mapping(runtime_surface_blind_qa_long_run_summary) or _safe_mapping(measurement_run.get("runtime_surface_blind_qa_long_run_summary"))
    user_label_summary = _safe_mapping(user_label_connection_qa_summary) or _safe_mapping(measurement_run.get("user_label_connection_qa_summary"))
    phase11 = _safe_mapping(phase11_long_run_product_gate) or _safe_mapping(measurement_run.get("phase11_long_run_product_gate"))
    blind_qa = _safe_mapping(blind_qa_integration) or _safe_mapping(measurement_run.get("blind_qa_integration"))

    runtime_scope = _safe_mapping(blind_qa.get("runtime_surface"))
    user_label_scope = _safe_mapping(blind_qa.get("user_label_connection"))
    if "runtime_surface_blind_qa_read_feeling_score" not in metrics:
        metrics["runtime_surface_blind_qa_read_feeling_score"] = (
            runtime_scope.get("read_feeling_score")
            or runtime_summary.get("read_feeling_score")
            or runtime_summary.get("runtime_surface_read_feeling_score")
        )
    if "user_label_connection_quality_score" not in metrics:
        metrics["user_label_connection_quality_score"] = (
            user_label_scope.get("quality_score")
            or user_label_summary.get("quality_score")
            or user_label_summary.get("mean_score")
        )
    if "runtime_surface_blind_qa_coverage_rate" not in metrics:
        metrics["runtime_surface_blind_qa_coverage_rate"] = runtime_scope.get("review_coverage_rate") or runtime_summary.get("review_coverage_rate")
    if "user_label_connection_qa_coverage_rate" not in metrics:
        metrics["user_label_connection_qa_coverage_rate"] = user_label_scope.get("review_coverage_rate") or user_label_summary.get("review_coverage_rate")
    if "red_review_count" not in metrics:
        metrics["red_review_count"] = max(
            _int(runtime_scope.get("red_review_count")),
            _int(user_label_scope.get("red_review_count")),
            _int(runtime_summary.get("red_review_count")),
            _int(user_label_summary.get("red_review_count")),
        )
    if "repair_required_row_count" not in metrics:
        metrics["repair_required_row_count"] = _int(metrics.get("repair_required_count"))
    sequence = _safe_mapping(_safe_mapping(phase11.get("sequence_report")).get("v1_product_pass"))
    if "five_consecutive_product_pass" not in metrics:
        metrics["five_consecutive_product_pass"] = bool(sequence.get("consecutive_5_ready") or phase11.get("five_consecutive_product_pass"))
    if "ten_consecutive_product_pass" not in metrics:
        metrics["ten_consecutive_product_pass"] = bool(sequence.get("consecutive_10_ready") or phase11.get("ten_consecutive_product_pass"))
    repetition = _safe_mapping(phase11.get("surface_repetition_report"))
    if "family_cross_surface_repetition_detected" not in metrics:
        metrics["family_cross_surface_repetition_detected"] = bool(
            repetition.get("family_cross_surface_repetition_detected")
            or metrics.get("family_cross_surface_repetition_detected")
        )
    if "unsafe_insight_surface_detected" not in metrics:
        metrics["unsafe_insight_surface_detected"] = bool(metrics.get("unsafe_insight_surface_detected"))
    return metrics


def _required_family_coverage_rate(
    *,
    measurement_run: Mapping[str, Any],
    family_counts: Mapping[str, Any] | None,
    required_families: Sequence[Any] | None,
    missing_required_families: Sequence[Any] | Iterable[Any] | None,
) -> float:
    required = _dedupe(required_families or measurement_run.get("required_families"))
    counts = _safe_mapping(family_counts) or _safe_mapping(measurement_run.get("family_counts"))
    missing = _dedupe(missing_required_families or measurement_run.get("missing_required_families"))
    if required:
        observed = [family for family in required if _int(counts.get(family)) > 0 and family not in missing]
        return _rate(len(observed), len(required))
    if missing:
        return 0.0
    if counts:
        return 1.0
    return 0.0


def _p12_surface_origin_counts(
    *,
    measurement_run: Mapping[str, Any],
    summary_metrics: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    run_metrics = _safe_mapping(measurement_run.get("summary_metrics"))
    explicit_metrics = _safe_mapping(summary_metrics)
    machine_metrics = _safe_mapping(measurement_run.get("machine_metrics"))
    surface_origin_summary = _safe_mapping(measurement_run.get("surface_origin_summary"))

    def pick_int(*keys: str) -> int:
        for key in keys:
            for source in (machine_metrics, surface_origin_summary, explicit_metrics, run_metrics):
                if key in source:
                    return _int(source.get(key))
        return 0

    event_count = _int(measurement_run.get("event_count"))
    if event_count <= 0:
        event_count = pick_int("event_count")
    surface_origin_event_count = pick_int("surface_origin_event_count")
    return {
        "event_count": event_count,
        "surface_origin_event_count": surface_origin_event_count,
        "surface_origin_coverage_rate": _rate(surface_origin_event_count, event_count) if event_count else 0.0,
        "public_display_reached_via_gate_recovery_material_surface_count": pick_int(
            "public_display_reached_via_gate_recovery_material_surface_count",
        ),
        "public_display_reached_via_post_final_gate_recovery_material_surface_count": pick_int(
            "public_display_reached_via_post_final_gate_recovery_material_surface_count",
        ),
        "public_display_reached_via_diagnostic_recovery_surface_count": pick_int(
            "public_display_reached_via_diagnostic_recovery_surface_count",
            "public_diagnostic_recovery_surface_event_count",
        ),
        "template_meta_false_negative_risk_count": pick_int("template_meta_false_negative_risk_count"),
    }


def _p12_validation_bundle(
    *,
    rows: Sequence[Mapping[str, Any]],
    criteria: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    p12_rows = [
        row for row in rows
        if str(row.get("validation_item_id") or "").startswith("p12_")
    ]
    p12_criteria = [
        criterion for criterion in criteria
        if str(criterion.get("criterion_id") or "").startswith("p12_")
    ]
    required = [row for row in p12_rows if row.get("required") is True]
    passed_required = [row for row in required if row.get("status") == VALIDATION_STATUS_PASSED]
    failed_required = [row for row in required if row.get("status") == VALIDATION_STATUS_FAILED]
    blocked_or_pending = [
        row for row in required
        if row.get("status") in {VALIDATION_STATUS_BLOCKED, VALIDATION_STATUS_NOT_EXECUTED}
    ]
    failed_criteria = [criterion for criterion in p12_criteria if criterion.get("passed") is not True]
    bundle = {
        "schema_version": GATE_RECOVERY_PUBLIC_SURFACE_LEAK_REPAIR_P12_SCHEMA_VERSION,
        "version": GATE_RECOVERY_PUBLIC_SURFACE_LEAK_REPAIR_P12_SCHEMA_VERSION,
        "phase": GATE_RECOVERY_PUBLIC_SURFACE_LEAK_REPAIR_P12_PHASE,
        "validation_plan_ready": True,
        "validation_internal_only": True,
        "backend_validation_commands": list(P12_BACKEND_VALIDATION_COMMANDS),
        "frontend_validation_commands": list(P12_FRONTEND_VALIDATION_COMMANDS),
        "real_device_validation_checks": list(P12_REAL_DEVICE_VALIDATION_CHECKS),
        "forbidden_public_surface_fragments": list(P12_FORBIDDEN_PUBLIC_SURFACE_FRAGMENTS),
        "allowed_public_candidate_sources": list(P12_ALLOWED_PUBLIC_CANDIDATE_SOURCES),
        "p12_validation_item_count": len(p12_rows),
        "p12_required_validation_item_count": len(required),
        "p12_required_validation_passed_count": len(passed_required),
        "p12_required_validation_failed_count": len(failed_required),
        "p12_required_validation_pending_or_blocked_count": len(blocked_or_pending),
        "p12_acceptance_criterion_count": len(p12_criteria),
        "p12_acceptance_criterion_failed_count": len(failed_criteria),
        "p12_validation_passed": bool(required and len(passed_required) == len(required) and not failed_criteria),
        "case_specific_runtime_branch_allowed": False,
        "runtime_fixture_branch_allowed": False,
        "exact_comment_text_required": False,
        "gate_recovery_material_surface_public_fallback_allowed": False,
        "diagnostic_recovery_surface_public_display_allowed": False,
        "public_contract_changed": False,
        "rn_contract_changed": False,
        "db_schema_changed": False,
        "api_route_changed": False,
        "response_shape_changed": False,
        "public_response_key_added": False,
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
    assert_product_quality_validation_plan_meta_only(
        bundle,
        source="gate_recovery_public_surface_leak_repair_p12_validation",
        require_root_schema=False,
    )
    return bundle


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
        "schema_version": PRODUCT_QUALITY_ACCEPTANCE_CRITERION_ROW_SCHEMA_VERSION,
        "phase": PRODUCT_QUALITY_VALIDATION_PLAN_PHASE,
        "target_step": PRODUCT_QUALITY_VALIDATION_PLAN_TARGET_STEP,
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
    assert_product_quality_validation_plan_meta_only(row, source=f"acceptance_criterion.{criterion_id}", require_root_schema=False)
    return row


def _acceptance_criteria(
    *,
    measurement_run: Mapping[str, Any],
    summary_metrics: Mapping[str, Any] | None = None,
    family_counts: Mapping[str, Any] | None = None,
    required_families: Sequence[Any] | None = None,
    missing_required_families: Sequence[Any] | Iterable[Any] | None = None,
    runtime_surface_blind_qa_long_run_summary: Mapping[str, Any] | None = None,
    user_label_connection_qa_summary: Mapping[str, Any] | None = None,
    phase11_long_run_product_gate: Mapping[str, Any] | None = None,
    blind_qa_integration: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    metrics = _summary_metrics_from_sources(
        measurement_run=measurement_run,
        summary_metrics=summary_metrics,
        runtime_surface_blind_qa_long_run_summary=runtime_surface_blind_qa_long_run_summary,
        user_label_connection_qa_summary=user_label_connection_qa_summary,
        phase11_long_run_product_gate=phase11_long_run_product_gate,
        blind_qa_integration=blind_qa_integration,
    )
    required_family_rate = _required_family_coverage_rate(
        measurement_run=measurement_run,
        family_counts=family_counts,
        required_families=required_families,
        missing_required_families=missing_required_families,
    )
    p12_surface_origin_counts = _p12_surface_origin_counts(
        measurement_run=measurement_run,
        summary_metrics=summary_metrics,
    )

    rows = [
        _criterion_row(
            criterion_id="public_contract_unchanged",
            owner_area="public_contract",
            observed=not any(_bool(_safe_mapping(measurement_run.get("contract_assertions")).get(k), False) for k in _CONTRACT_KEYS),
            target=True,
            comparator="equals",
            passed=not any(_bool(_safe_mapping(measurement_run.get("contract_assertions")).get(k), False) for k in _CONTRACT_KEYS),
        ),
        _criterion_row(
            criterion_id="display_reach_rate",
            owner_area="product_readfeel_display_reach",
            observed=_float(metrics.get("display_reach_rate"), default=0.0),
            target=DISPLAY_REACH_RATE_TARGET,
            comparator=">=",
            passed=bool((_float(metrics.get("display_reach_rate"), default=0.0) or 0.0) >= DISPLAY_REACH_RATE_TARGET),
        ),
        _criterion_row(
            criterion_id="binding_pass_rate",
            owner_area="binding_grounding",
            observed=_float(metrics.get("binding_pass_rate"), default=0.0),
            target=BINDING_PASS_RATE_TARGET,
            comparator=">=",
            passed=bool((_float(metrics.get("binding_pass_rate"), default=0.0) or 0.0) >= BINDING_PASS_RATE_TARGET),
        ),
        _criterion_row(
            criterion_id="reason_coverage_rate",
            owner_area="reason_grounding",
            observed=_float(metrics.get("reason_coverage_rate"), default=0.0),
            target=REASON_COVERAGE_RATE_TARGET,
            comparator=">=",
            passed=bool((_float(metrics.get("reason_coverage_rate"), default=0.0) or 0.0) >= REASON_COVERAGE_RATE_TARGET),
        ),
        _criterion_row(
            criterion_id="required_family_coverage_rate",
            owner_area="input_family_coverage",
            observed=required_family_rate,
            target=REQUIRED_FAMILY_COVERAGE_RATE_TARGET,
            comparator=">=",
            passed=bool(required_family_rate >= REQUIRED_FAMILY_COVERAGE_RATE_TARGET),
        ),
        _criterion_row(
            criterion_id="runtime_surface_blind_qa_coverage_rate",
            owner_area="runtime_surface_blind_qa",
            observed=_float(metrics.get("runtime_surface_blind_qa_coverage_rate"), default=0.0),
            target=RUNTIME_SURFACE_BLIND_QA_COVERAGE_RATE_TARGET,
            comparator=">=",
            passed=bool((_float(metrics.get("runtime_surface_blind_qa_coverage_rate"), default=0.0) or 0.0) >= RUNTIME_SURFACE_BLIND_QA_COVERAGE_RATE_TARGET),
        ),
        _criterion_row(
            criterion_id="runtime_surface_read_feeling_score",
            owner_area="runtime_surface_blind_qa",
            observed=_float(metrics.get("runtime_surface_blind_qa_read_feeling_score"), default=0.0),
            target=RUNTIME_SURFACE_READ_FEELING_SCORE_TARGET,
            comparator=">=",
            passed=bool((_float(metrics.get("runtime_surface_blind_qa_read_feeling_score"), default=0.0) or 0.0) >= RUNTIME_SURFACE_READ_FEELING_SCORE_TARGET),
        ),
        _criterion_row(
            criterion_id="user_label_connection_qa_coverage_rate",
            owner_area="user_label_connection_product_quality_qa",
            observed=_float(metrics.get("user_label_connection_qa_coverage_rate"), default=0.0),
            target=USER_LABEL_CONNECTION_QA_COVERAGE_RATE_TARGET,
            comparator=">=",
            passed=bool((_float(metrics.get("user_label_connection_qa_coverage_rate"), default=0.0) or 0.0) >= USER_LABEL_CONNECTION_QA_COVERAGE_RATE_TARGET),
        ),
        _criterion_row(
            criterion_id="user_label_connection_quality_score",
            owner_area="user_label_connection_product_quality_qa",
            observed=_float(metrics.get("user_label_connection_quality_score"), default=0.0),
            target=USER_LABEL_CONNECTION_QUALITY_SCORE_TARGET,
            comparator=">=",
            passed=bool((_float(metrics.get("user_label_connection_quality_score"), default=0.0) or 0.0) >= USER_LABEL_CONNECTION_QUALITY_SCORE_TARGET),
        ),
        _criterion_row(
            criterion_id="red_review_count",
            owner_area="blind_qa_review",
            observed=_int(metrics.get("red_review_count")),
            target=0,
            comparator="==",
            passed=_int(metrics.get("red_review_count")) == 0,
        ),
        _criterion_row(
            criterion_id="repair_required_row_count",
            owner_area="product_readfeel_repair_rows",
            observed=_int(metrics.get("repair_required_row_count")),
            target=0,
            comparator="==",
            passed=_int(metrics.get("repair_required_row_count")) == 0,
        ),
        _criterion_row(
            criterion_id="five_consecutive_product_pass",
            owner_area="phase11_long_run_product_gate",
            observed=_bool(metrics.get("five_consecutive_product_pass"), False),
            target=True,
            comparator="equals",
            passed=_bool(metrics.get("five_consecutive_product_pass"), False),
        ),
        _criterion_row(
            criterion_id="ten_consecutive_product_pass",
            owner_area="phase11_long_run_product_gate",
            observed=_bool(metrics.get("ten_consecutive_product_pass"), False),
            target=True,
            comparator="equals",
            passed=_bool(metrics.get("ten_consecutive_product_pass"), False),
        ),
        _criterion_row(
            criterion_id="family_cross_surface_repetition_absent",
            owner_area="surface_repetition",
            observed=_bool(metrics.get("family_cross_surface_repetition_detected"), False),
            target=False,
            comparator="equals_false",
            passed=not _bool(metrics.get("family_cross_surface_repetition_detected"), False),
        ),
        _criterion_row(
            criterion_id="unsafe_insight_surface_absent",
            owner_area="structure_insight_safety",
            observed=_bool(metrics.get("unsafe_insight_surface_detected"), False),
            target=False,
            comparator="equals_false",
            passed=not _bool(metrics.get("unsafe_insight_surface_detected"), False),
        ),
        _criterion_row(
            criterion_id="p12_gate_recovery_public_leak_count_zero",
            owner_area="gate_recovery_public_boundary",
            observed=p12_surface_origin_counts["public_display_reached_via_gate_recovery_material_surface_count"],
            target=0,
            comparator="==",
            passed=p12_surface_origin_counts["public_display_reached_via_gate_recovery_material_surface_count"] == 0,
        ),
        _criterion_row(
            criterion_id="p12_post_final_gate_recovery_public_leak_count_zero",
            owner_area="post_final_gate_recovery_boundary",
            observed=p12_surface_origin_counts["public_display_reached_via_post_final_gate_recovery_material_surface_count"],
            target=0,
            comparator="==",
            passed=p12_surface_origin_counts["public_display_reached_via_post_final_gate_recovery_material_surface_count"] == 0,
        ),
        _criterion_row(
            criterion_id="p12_diagnostic_recovery_surface_public_count_zero",
            owner_area="gate_recovery_public_boundary",
            observed=p12_surface_origin_counts["public_display_reached_via_diagnostic_recovery_surface_count"],
            target=0,
            comparator="==",
            passed=p12_surface_origin_counts["public_display_reached_via_diagnostic_recovery_surface_count"] == 0,
        ),
        _criterion_row(
            criterion_id="p12_gate_recovery_template_meta_false_negative_count_zero",
            owner_area="product_quality_surface_origin",
            observed=p12_surface_origin_counts["template_meta_false_negative_risk_count"],
            target=0,
            comparator="==",
            passed=p12_surface_origin_counts["template_meta_false_negative_risk_count"] == 0,
        ),
        _criterion_row(
            criterion_id="p12_surface_origin_present_for_measured_events",
            owner_area="product_quality_surface_origin",
            observed=p12_surface_origin_counts["surface_origin_coverage_rate"],
            target=1.0,
            comparator=">=",
            passed=bool(p12_surface_origin_counts["surface_origin_coverage_rate"] >= 1.0),
        ),
    ]
    return rows


def _release_decision_blockers(release_decision: Mapping[str, Any] | None) -> list[str]:
    decision = _safe_mapping(release_decision)
    blockers = _dedupe(decision.get("release_blockers"))
    if decision and (decision.get("release_allowed") is not True or _clean(decision.get("release_stage")) not in {"release_candidate", "all_allowed"}):
        blockers.append(BLOCKER_RELEASE_DECISION_NOT_GREEN)
    elif not decision:
        blockers.append(BLOCKER_RELEASE_DECISION_NOT_GREEN)
    return _dedupe(blockers)


def _followup_checks(
    *,
    rows: Sequence[Mapping[str, Any]],
    criteria: Sequence[Mapping[str, Any]],
    release_blockers: Sequence[str],
) -> list[dict[str, Any]]:
    followups: list[dict[str, Any]] = []
    for row in rows:
        if row.get("required") is True and row.get("status") != VALIDATION_STATUS_PASSED:
            followups.append(
                {
                    "owner_area": row.get("owner_area"),
                    "validation_item_id": row.get("validation_item_id"),
                    "reason_code": BLOCKER_REQUIRED_VALIDATION_INCOMPLETE,
                    "required_status": VALIDATION_STATUS_PASSED,
                    "current_status": row.get("status"),
                    "contract_change_allowed": False,
                    "gate_relaxation_allowed": False,
                    "product_gate_ready": False,
                    "public_release_applied": False,
                }
            )
    for criterion in criteria:
        if criterion.get("passed") is not True:
            followups.append(
                {
                    "owner_area": criterion.get("owner_area"),
                    "criterion_id": criterion.get("criterion_id"),
                    "reason_code": BLOCKER_ACCEPTANCE_CRITERION_NOT_MET,
                    "target_value": criterion.get("target_value"),
                    "observed_value": criterion.get("observed_value"),
                    "contract_change_allowed": False,
                    "gate_relaxation_allowed": False,
                    "product_gate_ready": False,
                    "public_release_applied": False,
                }
            )
    for blocker in _dedupe(release_blockers):
        followups.append(
            {
                "owner_area": "release_decision",
                "release_blocker_id": blocker,
                "reason_code": BLOCKER_RELEASE_DECISION_NOT_GREEN,
                "contract_change_allowed": False,
                "gate_relaxation_allowed": False,
                "product_gate_ready": False,
                "public_release_applied": False,
            }
        )
    return followups


def assert_product_quality_validation_plan_meta_only(
    value: Mapping[str, Any],
    *,
    source: str = "product_quality_validation_plan",
    require_root_schema: bool = True,
) -> None:
    if not isinstance(value, Mapping):
        raise ValueError(f"{source} must be a mapping")
    if require_root_schema and value.get("schema_version") != PRODUCT_QUALITY_VALIDATION_PLAN_SCHEMA_VERSION:
        raise ValueError(f"{source} has invalid schema_version")
    if _contains_key(value, _TEXT_PAYLOAD_KEYS):
        raise ValueError(f"{source} contains a forbidden text payload key")
    if _true_flag_paths(value, _CONTRACT_TRUE_FLAGS):
        raise ValueError(f"{source} must not allow public/RN/DB/Gate contract changes")
    if _true_flag_paths(value, _RELEASE_APPLY_TRUE_FLAGS):
        raise ValueError(f"{source} must not apply product gate or release flags")
    if value.get("product_gate_ready") is True:
        raise ValueError(f"{source} must keep product_gate_ready false")
    if value.get("public_release_applied") is True:
        raise ValueError(f"{source} must keep public_release_applied false")
    contract_freeze = value.get("contract_freeze")
    if isinstance(contract_freeze, Mapping):
        assert_emlis_ai_product_quality_contract_freeze_meta_only(contract_freeze, source=f"{source}.contract_freeze")


def build_product_quality_validation_plan(
    *,
    run_id: Any = "",
    measurement_run: Mapping[str, Any] | None = None,
    run_status: Any = None,
    event_count: Any = None,
    family_counts: Mapping[str, Any] | None = None,
    required_families: Sequence[Any] | None = None,
    missing_required_families: Sequence[Any] | Iterable[Any] | None = None,
    summary_metrics: Mapping[str, Any] | None = None,
    product_readfeel_scorecard: Mapping[str, Any] | None = None,
    runtime_surface_blind_qa_long_run_summary: Mapping[str, Any] | None = None,
    user_label_connection_qa_summary: Mapping[str, Any] | None = None,
    phase11_long_run_product_gate: Mapping[str, Any] | None = None,
    blocker_matrix: Mapping[str, Any] | None = None,
    generation_repair_design: Mapping[str, Any] | None = None,
    blind_qa_integration: Mapping[str, Any] | None = None,
    release_decision: Mapping[str, Any] | None = None,
    composer_bootstrap: Mapping[str, Any] | None = None,
    validation_results: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    run = dict(_safe_mapping(measurement_run))
    if run_status is not None:
        run["run_status"] = run_status
    if event_count is not None:
        run["event_count"] = event_count
    if family_counts is not None:
        run["family_counts"] = dict(family_counts)
    if required_families is not None:
        run["required_families"] = list(required_families)
    if missing_required_families is not None:
        run["missing_required_families"] = list(missing_required_families)
    if summary_metrics is not None:
        run["summary_metrics"] = dict(summary_metrics)

    rows = _validation_rows(validation_results)
    groups = _group_summary(rows)
    criteria = _acceptance_criteria(
        measurement_run=run,
        summary_metrics=summary_metrics,
        family_counts=family_counts,
        required_families=required_families,
        missing_required_families=missing_required_families,
        runtime_surface_blind_qa_long_run_summary=runtime_surface_blind_qa_long_run_summary,
        user_label_connection_qa_summary=user_label_connection_qa_summary,
        phase11_long_run_product_gate=phase11_long_run_product_gate,
        blind_qa_integration=blind_qa_integration,
    )
    materials = _source_materials(
        run,
        product_readfeel_scorecard,
        runtime_surface_blind_qa_long_run_summary,
        user_label_connection_qa_summary,
        phase11_long_run_product_gate,
        blocker_matrix,
        generation_repair_design,
        blind_qa_integration,
        release_decision,
        composer_bootstrap,
        validation_results,
    )
    source_text_payload_detected = any(_contains_key(material, _TEXT_PAYLOAD_KEYS) for material in materials) or _contains_key(validation_results, _TEXT_PAYLOAD_KEYS)
    contract_violation_paths = _contract_violation_paths(materials)
    release_flag_paths = _release_flag_paths(materials)

    required_rows = [row for row in rows if row.get("required") is True]
    passed_rows = [row for row in required_rows if row.get("status") == VALIDATION_STATUS_PASSED]
    failed_rows = [row for row in required_rows if row.get("status") == VALIDATION_STATUS_FAILED]
    not_executed_rows = [row for row in required_rows if row.get("status") == VALIDATION_STATUS_NOT_EXECUTED]
    blocked_rows = [row for row in required_rows if row.get("status") == VALIDATION_STATUS_BLOCKED]
    failed_criteria = [criterion for criterion in criteria if criterion.get("passed") is not True]
    release_blockers = _release_decision_blockers(release_decision)

    blockers: list[str] = []
    if not validation_results:
        blockers.append(BLOCKER_VALIDATION_EXECUTION_REQUIRED)
    if not_executed_rows or blocked_rows:
        blockers.append(BLOCKER_REQUIRED_VALIDATION_INCOMPLETE)
    if failed_rows:
        blockers.append(BLOCKER_REQUIRED_VALIDATION_FAILED)
    if failed_criteria:
        blockers.append(BLOCKER_ACCEPTANCE_CRITERION_NOT_MET)
    blockers.extend(release_blockers)
    if source_text_payload_detected:
        blockers.append(BLOCKER_SOURCE_TEXT_PAYLOAD_DETECTED)
    if contract_violation_paths:
        blockers.append(BLOCKER_CONTRACT_RELAXATION_DETECTED)
    if release_flag_paths:
        blockers.append(BLOCKER_RELEASE_FLAG_DETECTED)
    blockers = _dedupe(blockers)

    all_required_validation_passed = bool(required_rows and len(passed_rows) == len(required_rows))
    all_acceptance_criteria_passed = bool(criteria and not failed_criteria)
    validation_ready = bool(all_required_validation_passed and all_acceptance_criteria_passed and not blockers)
    status = "ready" if validation_ready else "blocked"
    followups = _followup_checks(rows=rows, criteria=criteria, release_blockers=release_blockers)
    contract_freeze = build_emlis_ai_product_quality_contract_freeze()
    validation_material_ready = bool(not source_text_payload_detected and not contract_violation_paths and not release_flag_paths)
    validation_plan_ready = True
    validation_execution_required = bool(not validation_results or not_executed_rows or blocked_rows or failed_rows)
    validation_execution_order = [str(row["validation_item_id"]) for row in rows]
    required_test_files = _dedupe(
        artifact
        for row in rows
        for artifact in _listify(row.get("source_artifacts"))
    )
    p12_validation = _p12_validation_bundle(rows=rows, criteria=criteria)

    plan = {
        "schema_version": PRODUCT_QUALITY_VALIDATION_PLAN_SCHEMA_VERSION,
        "version": PRODUCT_QUALITY_VALIDATION_PLAN_VERSION,
        "phase": PRODUCT_QUALITY_VALIDATION_PLAN_PHASE,
        "target_step": PRODUCT_QUALITY_VALIDATION_PLAN_TARGET_STEP,
        "run_id": (_clean(run_id) or _clean(run.get("run_id")))[:96],
        "validation_status": status,
        "validation_ready": validation_ready,
        "validation_plan_ready": validation_plan_ready,
        "validation_material_ready": validation_material_ready,
        "validation_execution_required": validation_execution_required,
        "validation_passed": validation_ready,
        "release_allowed_by_validation_plan": validation_ready,
        "validation_plan_internal_only": True,
        "gate_recovery_public_surface_leak_repair_validation": p12_validation,
        "p12_gate_recovery_public_leak_validation_plan_ready": bool(p12_validation.get("validation_plan_ready")),
        "p12_gate_recovery_public_leak_validation_passed": bool(p12_validation.get("p12_validation_passed")),
        "p12_backend_validation_commands": list(P12_BACKEND_VALIDATION_COMMANDS),
        "p12_frontend_validation_commands": list(P12_FRONTEND_VALIDATION_COMMANDS),
        "p12_real_device_validation_checks": list(P12_REAL_DEVICE_VALIDATION_CHECKS),
        "p12_forbidden_public_surface_fragments": list(P12_FORBIDDEN_PUBLIC_SURFACE_FRAGMENTS),
        "p12_allowed_public_candidate_sources": list(P12_ALLOWED_PUBLIC_CANDIDATE_SOURCES),
        "contract_freeze": contract_freeze,
        "contract_assertions": _contract_assertions(),
        "source_contract_violation_paths": contract_violation_paths,
        "source_release_flag_paths": release_flag_paths,
        "source_text_payload_detected": source_text_payload_detected,
        "validation_items": rows,
        "validation_steps": rows,
        "validation_execution_order_ids": validation_execution_order,
        "validation_execution_order": validation_execution_order,
        "validation_execution_order_ids": validation_execution_order,
        "required_test_files": required_test_files,
        "validation_item_count": len(rows),
        "required_validation_item_count": len(required_rows),
        "required_validation_passed_count": len(passed_rows),
        "required_validation_failed_count": len(failed_rows),
        "required_validation_not_executed_count": len(not_executed_rows),
        "required_validation_blocked_count": len(blocked_rows),
        "required_validation_pass_rate": _rate(len(passed_rows), len(required_rows)),
        "validation_group_summary": groups,
        "acceptance_criteria": criteria,
        "acceptance_criterion_count": len(criteria),
        "acceptance_criterion_passed_count": len(criteria) - len(failed_criteria),
        "acceptance_criterion_failed_count": len(failed_criteria),
        "all_required_validation_passed": all_required_validation_passed,
        "all_acceptance_criteria_passed": all_acceptance_criteria_passed,
        "release_decision_candidate_or_all_green": bool(not release_blockers),
        "validation_blockers": blockers,
        "release_blockers": blockers,
        "phase8_validation_results_missing": BLOCKER_VALIDATION_EXECUTION_REQUIRED in blockers,
        "phase8_validation_internal_only": True,
        "validation_blocker_count": len(blockers),
        "required_followup_checks": followups,
        "required_followup_check_count": len(followups),
        "execution_order": [
            {
                "execution_order": row["execution_order"],
                "validation_item_id": row["validation_item_id"],
                "validation_group": row["validation_group"],
                "owner_area": row["owner_area"],
                "required": row["required"],
                "status": row["status"],
            }
            for row in rows
        ],
        "validation_execution_order_detail": [
            {
                "execution_order": row["execution_order"],
                "validation_item_id": row["validation_item_id"],
                "validation_group": row["validation_group"],
                "owner_area": row["owner_area"],
                "required": row["required"],
                "status": row["status"],
            }
            for row in rows
        ],
        "regression_policy": {
            "abcd_fixture_is_regression_only": True,
            "runtime_fixture_branch_allowed": False,
            "case_specific_mode_allowed": False,
            "case_specific_cue_allowed": False,
            "fixed_template_allowed": False,
            "product_material_meta_only_required": True,
            "phase11_release_judgment_deferred_required": True,
        },
        "product_quality_targets": {
            "display_reach_rate_target": DISPLAY_REACH_RATE_TARGET,
            "binding_pass_rate_target": BINDING_PASS_RATE_TARGET,
            "reason_coverage_rate_target": REASON_COVERAGE_RATE_TARGET,
            "required_family_coverage_rate_target": REQUIRED_FAMILY_COVERAGE_RATE_TARGET,
            "runtime_surface_blind_qa_coverage_rate_target": RUNTIME_SURFACE_BLIND_QA_COVERAGE_RATE_TARGET,
            "runtime_surface_read_feeling_score_target": RUNTIME_SURFACE_READ_FEELING_SCORE_TARGET,
            "user_label_connection_qa_coverage_rate_target": USER_LABEL_CONNECTION_QA_COVERAGE_RATE_TARGET,
            "user_label_connection_quality_score_target": USER_LABEL_CONNECTION_QUALITY_SCORE_TARGET,
            "red_review_count_target": 0,
            "repair_required_row_count_target": 0,
            "five_consecutive_product_pass_required": True,
            "ten_consecutive_product_pass_required": True,
            "family_cross_surface_repetition_absent_required": True,
            "unsafe_insight_surface_absent_required": True,
        },
        "source_material_status": {
            "measurement_run_connected": bool(run),
            "product_readfeel_scorecard_connected": bool(product_readfeel_scorecard or run.get("product_readfeel_scorecard")),
            "runtime_surface_blind_qa_summary_connected": bool(runtime_surface_blind_qa_long_run_summary or run.get("runtime_surface_blind_qa_long_run_summary")),
            "user_label_connection_qa_summary_connected": bool(user_label_connection_qa_summary or run.get("user_label_connection_qa_summary")),
            "phase11_long_run_product_gate_connected": bool(phase11_long_run_product_gate or run.get("phase11_long_run_product_gate")),
            "blocker_matrix_connected": bool(blocker_matrix or run.get("blocker_matrix")),
            "generation_repair_design_connected": bool(generation_repair_design or run.get("generation_repair_design")),
            "blind_qa_integration_connected": bool(blind_qa_integration or run.get("blind_qa_integration")),
            "composer_bootstrap_connected": bool(composer_bootstrap or run.get("composer_bootstrap")),
            "release_decision_connected": bool(release_decision),
        },
        "summary": {
            "validation_status": status,
            "validation_ready": validation_ready,
            "validation_plan_ready": validation_plan_ready,
            "validation_material_ready": validation_material_ready,
            "validation_execution_required": validation_execution_required,
            "validation_passed": validation_ready,
            "release_allowed_by_validation_plan": validation_ready,
            "required_validation_pass_rate": _rate(len(passed_rows), len(required_rows)),
            "acceptance_criterion_failed_count": len(failed_criteria),
            "validation_blocker_count": len(blockers),
            "p12_gate_recovery_public_leak_validation_passed": bool(p12_validation.get("p12_validation_passed")),
            "p12_required_validation_pending_or_blocked_count": p12_validation.get("p12_required_validation_pending_or_blocked_count"),
            "p12_acceptance_criterion_failed_count": p12_validation.get("p12_acceptance_criterion_failed_count"),
            "release_decision_candidate_or_all_green": bool(not release_blockers),
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
        "fixed_sentence_template_added": False,
        "fixed_sentence_template_used": False,
        "input_specific_template_added": False,
        "runtime_fixture_branch_added": False,
        "runtime_fixture_branch_required": False,
        "external_ai_used": False,
        "local_llm_used": False,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_auto_estimation_allowed": False,
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
    assert_product_quality_validation_plan_meta_only(plan)
    return plan


def build_product_quality_validation_results_stub(status: str = VALIDATION_STATUS_PASSED) -> dict[str, str]:
    normalized = _status(status)
    return {str(item["validation_item_id"]): normalized for item in _EXECUTION_ORDER}


def dump_product_quality_validation_plan(plan: Mapping[str, Any]) -> str:
    data = _safe_mapping(plan)
    assert_product_quality_validation_plan_meta_only(data)
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


build_emlis_ai_product_quality_validation_plan = build_product_quality_validation_plan
assert_emlis_ai_product_quality_validation_plan_meta_only = assert_product_quality_validation_plan_meta_only
dump_emlis_ai_product_quality_validation_plan = dump_product_quality_validation_plan

__all__ = [
    "BLOCKER_ACCEPTANCE_CRITERION_NOT_MET",
    "BLOCKER_REQUIRED_VALIDATION_FAILED",
    "BLOCKER_REQUIRED_VALIDATION_INCOMPLETE",
    "BLOCKER_VALIDATION_EXECUTION_REQUIRED",
    "PRODUCT_QUALITY_VALIDATION_PLAN_PHASE",
    "PRODUCT_QUALITY_VALIDATION_PLAN_SCHEMA_VERSION",
    "GATE_RECOVERY_PUBLIC_SURFACE_LEAK_REPAIR_P12_PHASE",
    "GATE_RECOVERY_PUBLIC_SURFACE_LEAK_REPAIR_P12_SCHEMA_VERSION",
    "P12_ALLOWED_PUBLIC_CANDIDATE_SOURCES",
    "P12_BACKEND_VALIDATION_COMMANDS",
    "P12_FORBIDDEN_PUBLIC_SURFACE_FRAGMENTS",
    "P12_FRONTEND_VALIDATION_COMMANDS",
    "P12_REAL_DEVICE_VALIDATION_CHECKS",
    "PRODUCT_QUALITY_VALIDATION_PLAN_TARGET_STEP",
    "PRODUCT_QUALITY_VALIDATION_PLAN_VERSION",
    "VALIDATION_GROUP_CONTRACT",
    "VALIDATION_GROUP_E2E_PUBLIC_BOUNDARY",
    "VALIDATION_GROUP_PRODUCT_QUALITY",
    "VALIDATION_GROUP_REGRESSION",
    "VALIDATION_GROUP_UNIT",
    "VALIDATION_STATUS_NOT_EXECUTED",
    "VALIDATION_STATUS_PASSED",
    "assert_emlis_ai_product_quality_validation_plan_meta_only",
    "assert_product_quality_validation_plan_meta_only",
    "build_emlis_ai_product_quality_validation_plan",
    "build_product_quality_validation_plan",
    "build_product_quality_validation_results_stub",
    "dump_emlis_ai_product_quality_validation_plan",
    "dump_product_quality_validation_plan",
]
