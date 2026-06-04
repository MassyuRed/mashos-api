# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 7 internal Release Decision Layer for EmlisAI Product Quality.

This module combines existing internal QA materials into ProductReleaseDecisionV1.
It only makes an internal release judgment.  It never mutates public response
shape, RN display contracts, DB names, gates, or rollout flags.
"""

from collections.abc import Iterable, Mapping, Sequence
import json
from typing import Any, Final
from uuid import uuid4

from emlis_ai_product_quality_contract_freeze import (
    assert_emlis_ai_product_quality_contract_freeze_meta_only,
    build_emlis_ai_product_quality_contract_freeze,
)
from emlis_ai_product_readfeel_current_output_inventory import PRODUCT_READFEEL_REQUIRED_FAMILIES

PRODUCT_RELEASE_DECISION_SCHEMA_VERSION: Final = "cocolon.emlis.product_release_decision.v1"
PRODUCT_RELEASE_DECISION_VERSION: Final = PRODUCT_RELEASE_DECISION_SCHEMA_VERSION
PRODUCT_RELEASE_DECISION_PHASE: Final = "Phase7_ReleaseDecisionLayer"
PRODUCT_RELEASE_DECISION_TARGET_STEP: Final = "EmlisAI_ProductQuality_InternalReleaseDecision"

RELEASE_STAGE_NOT_READY: Final = "not_ready"
RELEASE_STAGE_INTERNAL_QA: Final = "internal_qa"
RELEASE_STAGE_LIMITED_INTERNAL_GREEN: Final = "limited_internal_green"
RELEASE_STAGE_LIMITED_USER_SHADOW: Final = "limited_user_shadow"
RELEASE_STAGE_RELEASE_CANDIDATE: Final = "release_candidate"
RELEASE_STAGE_ALL_ALLOWED: Final = "all_allowed"
RELEASE_STAGES: Final = (
    RELEASE_STAGE_NOT_READY,
    RELEASE_STAGE_INTERNAL_QA,
    RELEASE_STAGE_LIMITED_INTERNAL_GREEN,
    RELEASE_STAGE_LIMITED_USER_SHADOW,
    RELEASE_STAGE_RELEASE_CANDIDATE,
    RELEASE_STAGE_ALL_ALLOWED,
)

DISPLAY_REACH_RATE_TARGET: Final = 0.90
BINDING_PASS_RATE_TARGET: Final = 0.98
REASON_COVERAGE_TARGET: Final = 1.0
REQUIRED_FAMILY_COVERAGE_TARGET: Final = 1.0
RUNTIME_BLIND_QA_READ_FEELING_TARGET: Final = 0.90
USER_LABEL_CONNECTION_QUALITY_TARGET: Final = 0.90
BLIND_QA_REVIEW_COVERAGE_TARGET: Final = 1.0
TIMEOUT_RATE_TARGET: Final = 0.02
UNAVAILABLE_RATE_TARGET: Final = 0.05

BLOCKER_RELEASE_CONTRACT_VIOLATION_DETECTED: Final = "release_decision_contract_violation_detected"
BLOCKER_RELEASE_TEXT_PAYLOAD_DETECTED: Final = "release_decision_text_payload_detected"
BLOCKER_RELEASE_COMPOSER_NOT_OPEN: Final = "composer_generation_path_not_open_for_product_qa"
BLOCKER_RELEASE_CANDIDATE_SHADOW_EVIDENCE_MISSING: Final = "release_candidate_shadow_evidence_missing"
BLOCKER_RELEASE_OPERATIONAL_NOT_READY: Final = "operational_rollout_and_rollback_not_confirmed"

_TEXT_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
    {
        "raw_input", "rawInput", "raw_text", "rawText", "source_text", "sourceText",
        "input", "input_text", "inputText", "user_input", "userInput", "current_input",
        "currentInput", "memo", "memo_text", "memoText", "memo_action", "memoAction",
        "comment_text", "commentText", "comment_text_body", "commentTextBody",
        "comment_body", "commentBody", "input_feedback_comment", "public_comment_text",
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
        "raw_input_included", "raw_text_included", "raw_user_text_included", "comment_text_included",
        "comment_text_body_included", "candidate_body_included", "surface_body_included",
        "machine_metrics_used_for_read_feeling", "read_feeling_auto_filled_from_machine_metrics",
        "read_feeling_auto_estimation_allowed", "fixed_sentence_template_added",
        "fixed_sentence_template_used", "input_specific_template_added", "runtime_fixture_branch_added",
        "runtime_fixture_branch_required", "external_ai_used", "local_llm_used",
    }
)
_RELEASE_APPLY_TRUE_FLAGS: Final[frozenset[str]] = frozenset(
    {
        "product_gate_ready", "product_gate_reached", "product_gate_achieved",
        "product_gate_public_release_applied", "public_release_applied", "product_quality_released",
        "release_decision_applied", "release_rollout_applied", "rollout_stage_mutated",
        "all_rollout_applied", "rollout_config_changed", "public_meta_import_allowed",
        "release_material_import_allowed",
    }
)
_CONTRACT_KEYS: Final = (
    "api_route_changed", "response_shape_changed", "public_response_key_added",
    "db_physical_name_changed", "rn_visible_contract_changed", "rn_visible_title_changed",
    "display_gate_relaxed", "grounding_gate_relaxed", "template_gate_relaxed",
    "raw_input_included", "raw_text_included", "comment_text_body_included",
    "candidate_body_included", "surface_body_included",
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


def assert_product_release_decision_meta_only(value: Mapping[str, Any], *, source: str = "product_release_decision") -> None:
    if not isinstance(value, Mapping):
        raise ValueError(f"{source} must be a mapping")
    if value.get("schema_version") != PRODUCT_RELEASE_DECISION_SCHEMA_VERSION:
        raise ValueError(f"{source} has invalid schema_version")
    if _contains_key(value, _TEXT_PAYLOAD_KEYS):
        raise ValueError(f"{source} contains a forbidden text payload key")
    if _true_flag_paths(value, _RELEASE_APPLY_TRUE_FLAGS):
        raise ValueError(f"{source} must not apply release/product gate flags")
    if _true_flag_paths(value, _CONTRACT_TRUE_FLAGS):
        raise ValueError(f"{source} must not allow public/RN/DB/Gate contract changes")
    if value.get("product_gate_ready") is not False:
        raise ValueError(f"{source} must keep product_gate_ready false")
    if value.get("public_release_applied") is not False:
        raise ValueError(f"{source} must keep public_release_applied false")
    stage = _clean(value.get("release_stage"))
    if stage not in RELEASE_STAGES:
        raise ValueError(f"{source} has invalid release_stage")
    blockers = _dedupe(value.get("release_blockers"))
    if value.get("release_allowed") is True and (stage not in {RELEASE_STAGE_RELEASE_CANDIDATE, RELEASE_STAGE_ALL_ALLOWED} or blockers):
        raise ValueError(f"{source} cannot allow release unless candidate/all stage has no blockers")
    contract_freeze = value.get("contract_freeze")
    if isinstance(contract_freeze, Mapping):
        assert_emlis_ai_product_quality_contract_freeze_meta_only(contract_freeze, source=f"{source}.contract_freeze")


def _contract_assertions() -> dict[str, bool]:
    return {key: False for key in _CONTRACT_KEYS}


def _source_materials(*materials: Any) -> list[Mapping[str, Any]]:
    return [m for m in materials if isinstance(m, Mapping)]


def _contract_violations(materials: Iterable[Mapping[str, Any]]) -> list[str]:
    violations: list[str] = []
    for i, material in enumerate(materials):
        for path in _true_flag_paths(material, _CONTRACT_TRUE_FLAGS | _RELEASE_APPLY_TRUE_FLAGS, path=f"source_material[{i}]"):
            violations.append(path)
    return _dedupe(violations)


def _blockers_from_contract(source_contract_violations: Sequence[str], source_text_payload_detected: bool) -> list[str]:
    blockers: list[str] = []
    if source_contract_violations:
        blockers.append(BLOCKER_RELEASE_CONTRACT_VIOLATION_DETECTED)
    if source_text_payload_detected:
        blockers.append(BLOCKER_RELEASE_TEXT_PAYLOAD_DETECTED)
    return _dedupe(blockers)


def _nested(mapping: Mapping[str, Any], key: str) -> dict[str, Any]:
    return _safe_mapping(mapping.get(key))


def _metric(key: str, *sources: Mapping[str, Any], default: float | None = None) -> float | None:
    for source in sources:
        value = _float(source.get(key), None)
        if value is not None:
            return value
    return default


def _family_coverage(run: Mapping[str, Any], scorecard: Mapping[str, Any], summary: Mapping[str, Any]) -> float | None:
    direct = _metric("required_family_coverage_rate", summary, scorecard)
    if direct is not None:
        return direct
    direct = _metric("family_coverage_rate", scorecard)
    if direct is not None:
        return direct
    if "missing_required_families" in run:
        missing = [_clean(item) for item in _listify(run.get("missing_required_families"))]
        if not [item for item in missing if item]:
            return 1.0
    required = list(run.get("required_families") or PRODUCT_READFEEL_REQUIRED_FAMILIES)
    counts = _safe_mapping(run.get("family_counts"))
    return _rate(sum(1 for f in required if _int(counts.get(f)) > 0), len(required)) if required else None


def _phase11_sequence(phase11: Mapping[str, Any]) -> dict[str, Any]:
    seq = _nested(phase11, "sequence_report")
    return _nested(seq, "v1_product_pass") or _nested(_nested(phase11, "sequence_evaluation"), "v1_product_pass")


def _surface_repetition_detected(phase11: Mapping[str, Any], runtime_summary: Mapping[str, Any], summary: Mapping[str, Any]) -> bool:
    surface = _nested(phase11, "surface_repetition_report")
    return bool(
        surface.get("family_cross_surface_repetition_detected")
        or surface.get("repeat_detected")
        or runtime_summary.get("family_cross_surface_repetition_detected")
        or runtime_summary.get("long_run_surface_signature_repeat_detected")
        or (_float(summary.get("surface_signature_repeat_rate"), 0.0) or 0.0) > 0.0
    )


def _user_label_quality(user_label_summary: Mapping[str, Any], blind_qa: Mapping[str, Any], summary: Mapping[str, Any]) -> float | None:
    direct = _metric("user_label_connection_quality_score", summary)
    if direct is not None:
        return direct
    direct = _metric("user_label_connection_read_feeling_score", summary)
    if direct is not None:
        return direct
    scope = _nested(blind_qa, "user_label_connection")
    direct = _metric("quality_score", user_label_summary, scope)
    if direct is not None:
        return direct
    scores: list[float] = []
    for source in (_safe_mapping(user_label_summary.get("dimension_scores")), _safe_mapping(scope.get("dimension_scores"))):
        for value in source.values():
            score = _float(value, None)
            if score is not None:
                scores.append(score)
    return round(sum(scores) / len(scores), 6) if scores else _metric("read_feeling_score", user_label_summary, scope)


def _evaluated_metrics(
    *,
    run: Mapping[str, Any],
    scorecard: Mapping[str, Any],
    phase11: Mapping[str, Any],
    runtime_summary: Mapping[str, Any],
    user_label_summary: Mapping[str, Any],
    blind_qa: Mapping[str, Any],
    timeout_stats: Mapping[str, Any],
) -> dict[str, Any]:
    summary = _safe_mapping(run.get("summary_metrics"))
    machine = _safe_mapping(run.get("machine_metrics")) or _nested(scorecard, "machine_metrics")
    runtime_scope = _nested(blind_qa, "runtime_surface")
    user_scope = _nested(blind_qa, "user_label_connection")
    seq = _phase11_sequence(phase11)
    return {
        "display_reach_rate": _metric("display_reach_rate", summary, machine),
        "binding_pass_rate": _metric("binding_pass_rate", summary, machine),
        "reason_coverage_rate": _metric("reason_coverage_rate", summary, machine),
        "required_family_coverage_rate": _family_coverage(run, scorecard, summary),
        "runtime_surface_blind_qa_coverage_rate": _metric("runtime_surface_blind_qa_coverage_rate", summary, runtime_scope, runtime_summary),
        "user_label_connection_qa_coverage_rate": _metric("user_label_connection_qa_coverage_rate", summary, user_scope, user_label_summary),
        "runtime_surface_read_feeling_score": _metric("runtime_surface_blind_qa_read_feeling_score", summary, runtime_scope, runtime_summary),
        "user_label_connection_quality_score": _user_label_quality(user_label_summary, blind_qa, summary),
        "red_review_count": _int(summary.get("red_review_count")) + _int(runtime_scope.get("red_review_count")) + _int(user_scope.get("red_review_count")),
        "repair_required_row_count": _int(summary.get("repair_required_row_count")) + _int(scorecard.get("repair_required_row_count")) + _int(_safe_mapping(scorecard.get("family_verdict_counts")).get("REPAIR_REQUIRED")),
        "template_major_count": _int(summary.get("template_major_count")) + _int(machine.get("template_major_count")),
        "safety_major_count": _int(summary.get("safety_major_count")) + _int(timeout_stats.get("safety_major_count")) + _int(machine.get("safety_major_count")),
        "family_cross_surface_repetition_detected": _surface_repetition_detected(phase11, runtime_summary, summary),
        "five_consecutive_product_pass": _bool(summary.get("five_consecutive_product_pass")) or _bool(seq.get("consecutive_5_ready")) or _bool(phase11.get("product_readfeel_phase11_consecutive_5_v1_product_pass_ready")),
        "ten_consecutive_product_pass": _bool(summary.get("ten_consecutive_product_pass")) or _bool(seq.get("consecutive_10_ready")) or _bool(phase11.get("product_readfeel_phase11_consecutive_10_v1_product_pass_ready")),
        "timeout_rate": _float(timeout_stats.get("timeout_rate"), 0.0),
        "unavailable_rate": _float(timeout_stats.get("unavailable_rate"), 0.0),
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
    }


def _target_checks(metrics: Mapping[str, Any], *, blind_qa: Mapping[str, Any], phase11: Mapping[str, Any]) -> dict[str, bool]:
    return {
        "display_reach_rate_target_met": bool((_float(metrics.get("display_reach_rate"), 0.0) or 0.0) >= DISPLAY_REACH_RATE_TARGET),
        "binding_pass_rate_target_met": bool((_float(metrics.get("binding_pass_rate"), 0.0) or 0.0) >= BINDING_PASS_RATE_TARGET),
        "reason_coverage_target_met": bool((_float(metrics.get("reason_coverage_rate"), 0.0) or 0.0) >= REASON_COVERAGE_TARGET),
        "required_family_coverage_target_met": bool((_float(metrics.get("required_family_coverage_rate"), 0.0) or 0.0) >= REQUIRED_FAMILY_COVERAGE_TARGET),
        "runtime_blind_qa_coverage_target_met": bool((_float(metrics.get("runtime_surface_blind_qa_coverage_rate"), 0.0) or 0.0) >= BLIND_QA_REVIEW_COVERAGE_TARGET),
        "user_label_connection_qa_coverage_target_met": bool((_float(metrics.get("user_label_connection_qa_coverage_rate"), 0.0) or 0.0) >= BLIND_QA_REVIEW_COVERAGE_TARGET),
        "runtime_read_feeling_target_met": bool((_float(metrics.get("runtime_surface_read_feeling_score"), -1.0) or -1.0) >= RUNTIME_BLIND_QA_READ_FEELING_TARGET),
        "user_label_connection_quality_target_met": bool((_float(metrics.get("user_label_connection_quality_score"), -1.0) or -1.0) >= USER_LABEL_CONNECTION_QUALITY_TARGET),
        "blind_qa_integration_ready": bool(blind_qa.get("blind_qa_integration_ready")),
        "phase11_long_run_ready": bool(phase11.get("v1_product_pass_candidate") or phase11.get("product_gate_candidate_material_ready") or phase11.get("phase11_long_run_ready")),
        "five_consecutive_product_pass": bool(metrics.get("five_consecutive_product_pass")),
        "ten_consecutive_product_pass": bool(metrics.get("ten_consecutive_product_pass")),
        "family_cross_surface_repetition_absent": not bool(metrics.get("family_cross_surface_repetition_detected")),
        "red_review_absent": _int(metrics.get("red_review_count")) == 0,
        "repair_required_absent": _int(metrics.get("repair_required_row_count")) == 0,
        "safety_major_absent": _int(metrics.get("safety_major_count")) == 0,
        "template_major_absent": _int(metrics.get("template_major_count")) == 0,
        "timeout_rate_target_met": bool((_float(metrics.get("timeout_rate"), 0.0) or 0.0) <= TIMEOUT_RATE_TARGET),
        "unavailable_rate_target_met": bool((_float(metrics.get("unavailable_rate"), 0.0) or 0.0) <= UNAVAILABLE_RATE_TARGET),
    }


def _blockers_from_targets(checks: Mapping[str, bool]) -> list[str]:
    names = {
        "display_reach_rate_target_met": "product_readfeel_display_reach_rate_below_target",
        "binding_pass_rate_target_met": "product_readfeel_binding_pass_rate_below_target",
        "reason_coverage_target_met": "product_readfeel_reason_coverage_below_target",
        "required_family_coverage_target_met": "required_family_cross_coverage_incomplete",
        "runtime_blind_qa_coverage_target_met": "runtime_surface_blind_qa_review_coverage_below_target",
        "user_label_connection_qa_coverage_target_met": "user_label_connection_qa_review_coverage_below_target",
        "runtime_read_feeling_target_met": "runtime_surface_read_feeling_below_product_target",
        "user_label_connection_quality_target_met": "user_label_connection_quality_below_product_target",
        "blind_qa_integration_ready": "blind_qa_review_required",
        "phase11_long_run_ready": "phase11_v1_product_pass_candidate_not_ready",
        "five_consecutive_product_pass": "five_consecutive_v1_product_pass_not_observed",
        "ten_consecutive_product_pass": "ten_consecutive_v1_product_pass_not_observed",
        "family_cross_surface_repetition_absent": "family_cross_surface_repetition_detected",
        "red_review_absent": "red_review_present",
        "repair_required_absent": "repair_required_row_present",
        "safety_major_absent": "safety_major_detected",
        "template_major_absent": "template_major_detected",
        "timeout_rate_target_met": "timeout_rate_above_product_release_target",
        "unavailable_rate_target_met": "unavailable_rate_above_product_release_target",
    }
    return [blocker for key, blocker in names.items() if checks.get(key) is False]


def _composer_open(run: Mapping[str, Any], composer_summary: Mapping[str, Any]) -> bool | None:
    bootstrap = _safe_mapping(run.get("composer_bootstrap"))
    for source in (composer_summary, bootstrap):
        if source.get("composer_generation_path_open") is not None:
            return _bool(source.get("composer_generation_path_open"))
        if source.get("measurement_can_continue") is not None:
            return _bool(source.get("measurement_can_continue"))
        resolution = _nested(source, "composer_resolution")
        if resolution.get("default_client_used") is not None:
            return _bool(resolution.get("default_client_used"))
    return None


def _operational_summary(stats: Mapping[str, Any]) -> dict[str, Any]:
    completed = _bool(stats.get("limited_user_shadow_ready") or stats.get("limited_user_shadow_completed") or stats.get("shadow_run_completed"))
    timeout_rate = _float(stats.get("timeout_rate"), 0.0) or 0.0
    unavailable_rate = _float(stats.get("unavailable_rate"), 0.0) or 0.0
    return {
        "limited_user_shadow_ready": bool(completed and timeout_rate <= TIMEOUT_RATE_TARGET and unavailable_rate <= UNAVAILABLE_RATE_TARGET),
        "timeout_rate": timeout_rate,
        "timeout_rate_target": TIMEOUT_RATE_TARGET,
        "unavailable_rate": unavailable_rate,
        "unavailable_rate_target": UNAVAILABLE_RATE_TARGET,
        "operational_rollout_ready": _bool(stats.get("operational_rollout_ready")),
        "rollback_plan_confirmed": _bool(stats.get("rollback_plan_confirmed")),
        "rollout_config_changed": False,
        "all_rollout_applied": False,
    }


def _all_internal_green(checks: Mapping[str, bool]) -> bool:
    internal_keys = (
        "display_reach_rate_target_met", "binding_pass_rate_target_met", "reason_coverage_target_met",
        "required_family_coverage_target_met", "runtime_blind_qa_coverage_target_met",
        "user_label_connection_qa_coverage_target_met", "runtime_read_feeling_target_met",
        "user_label_connection_quality_target_met", "blind_qa_integration_ready", "phase11_long_run_ready",
        "five_consecutive_product_pass", "ten_consecutive_product_pass", "family_cross_surface_repetition_absent",
        "red_review_absent", "repair_required_absent", "safety_major_absent", "template_major_absent",
    )
    return all(checks.get(k) is True for k in internal_keys)


def _stage(
    *,
    blockers: Sequence[str],
    checks: Mapping[str, bool],
    composer_open: bool | None,
    events_present: bool,
    operational: Mapping[str, Any],
    all_allowed_requested: bool,
) -> str:
    blocker_set = set(_dedupe(blockers))
    hard = {
        BLOCKER_RELEASE_CONTRACT_VIOLATION_DETECTED,
        BLOCKER_RELEASE_TEXT_PAYLOAD_DETECTED,
        BLOCKER_RELEASE_COMPOSER_NOT_OPEN,
        "phase3_events_missing",
        "phase11_events_missing",
        "required_family_cross_coverage_incomplete",
        "red_review_present",
        "repair_required_row_present",
        "safety_major_detected",
    }
    if composer_open is False or not events_present or blocker_set & hard:
        return RELEASE_STAGE_NOT_READY
    if not _all_internal_green(checks):
        return RELEASE_STAGE_INTERNAL_QA
    if operational.get("limited_user_shadow_ready") is not True:
        return RELEASE_STAGE_LIMITED_INTERNAL_GREEN
    if operational.get("operational_rollout_ready") is not True or operational.get("rollback_plan_confirmed") is not True:
        return RELEASE_STAGE_LIMITED_USER_SHADOW
    if all_allowed_requested:
        return RELEASE_STAGE_ALL_ALLOWED
    return RELEASE_STAGE_RELEASE_CANDIDATE


def _score_targets() -> dict[str, float]:
    return {
        "display_reach_rate_target": DISPLAY_REACH_RATE_TARGET,
        "binding_pass_rate_target": BINDING_PASS_RATE_TARGET,
        "reason_coverage_target": REASON_COVERAGE_TARGET,
        "runtime_blind_qa_read_feeling_target": RUNTIME_BLIND_QA_READ_FEELING_TARGET,
        "user_label_connection_quality_target": USER_LABEL_CONNECTION_QUALITY_TARGET,
        "blind_qa_review_coverage_target": BLIND_QA_REVIEW_COVERAGE_TARGET,
        "required_family_coverage_target": REQUIRED_FAMILY_COVERAGE_TARGET,
        "timeout_rate_target": TIMEOUT_RATE_TARGET,
        "unavailable_rate_target": UNAVAILABLE_RATE_TARGET,
    }


def _owner_area_for_blocker(blocker: str) -> str:
    if "composer" in blocker:
        return "composer_qa_bootstrap"
    if "display_reach" in blocker or blocker == "display_not_reached":
        return "display_reach_repair"
    if "binding" in blocker:
        return "evidence_binding_grounding"
    if "reason_coverage" in blocker:
        return "reason_coverage_planner"
    if "required_family" in blocker or "coverage_incomplete" in blocker:
        return "measurement_input_family_coverage"
    if "blind_qa" in blocker or "read_feeling" in blocker:
        return "runtime_surface_blind_qa"
    if "user_label" in blocker or "history_connection" in blocker or "overclaim" in blocker or "creepiness" in blocker:
        return "user_label_connection_quality_qa"
    if "phase11" in blocker or "consecutive" in blocker or "surface_repetition" in blocker:
        return "phase11_long_run_product_gate"
    if "red_review" in blocker or "repair_required" in blocker or "safety" in blocker:
        return "safety_and_repair_boundary"
    if "template" in blocker:
        return "surface_repetition_template_repair"
    if "shadow" in blocker:
        return "limited_user_shadow_validation"
    if "operational" in blocker or "rollback" in blocker or "timeout" in blocker or "unavailable" in blocker:
        return "operational_release_boundary"
    if "contract" in blocker or "payload" in blocker:
        return "public_contract_boundary"
    return "product_release_decision_triage"


def _repair_policy_for_blocker(blocker: str) -> str:
    if blocker == BLOCKER_RELEASE_CANDIDATE_SHADOW_EVIDENCE_MISSING:
        return "商品release候補化前に、本番相当または明示されたshadow evidenceを別作業で確認する"
    if blocker == BLOCKER_RELEASE_COMPOSER_NOT_OPEN:
        return "QA生成経路が開いていない状態を成功扱いせず、local product QA profileで明示的に起動確認する"
    if blocker in {BLOCKER_RELEASE_CONTRACT_VIOLATION_DETECTED, BLOCKER_RELEASE_TEXT_PAYLOAD_DETECTED}:
        return "public/RN/DB契約とmeta-only境界を戻し、raw/comment/candidate bodyをrelease materialへ入れない"
    if "display_reach" in blocker:
        return "Gateを緩めず、表示可能な観測文へ戻す生成・repair経路を修正する"
    if "blind_qa" in blocker or "read_feeling" in blocker:
        return "機械指標で代替せず、ratings-only Blind QAを完了してyellow/redを生成修正へ戻す"
    if "phase11" in blocker or "consecutive" in blocker:
        return "長期安定性と5/10連続product passが揃うまでrelease不可として再計測する"
    return "Blocker Matrixのowner_areaに戻し、Gate緩和・固定テンプレートなしで生成面から修正する"


def _matrix_row_index(matrix: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    rows = _listify(matrix.get("rows") or matrix.get("blocker_matrix_rows"))
    indexed: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        if isinstance(row, Mapping):
            blocker_id = _clean(row.get("blocker_id"))
            if blocker_id:
                indexed[blocker_id] = row
    return indexed


def _followups(blockers: Sequence[str], matrix: Mapping[str, Any]) -> list[dict[str, Any]]:
    row_index = _matrix_row_index(matrix)
    followups: list[dict[str, Any]] = []
    for blocker in _dedupe(blockers):
        row = row_index.get(blocker, {})
        owner = _clean(row.get("likely_owner_area") or row.get("owner_area")) or _owner_area_for_blocker(blocker)
        modules = _dedupe(row.get("candidate_modules"))
        followups.append(
            {
                "blocker_id": blocker,
                "owner_area": owner,
                "candidate_modules": modules,
                "repair_policy": _clean(row.get("repair_policy")) or _repair_policy_for_blocker(blocker),
                "contract_change_allowed": False,
                "public_response_change_allowed": False,
                "rn_contract_change_allowed": False,
                "db_schema_change_allowed": False,
                "gate_relaxation_allowed": False,
                "fixed_template_allowed": False,
                "runtime_fixture_branch_allowed": False,
                "product_gate_ready": False,
                "public_release_applied": False,
            }
        )
    return followups


def build_product_release_decision(
    *,
    run_id: Any = "",
    decision_id: Any = "",
    measurement_run: Mapping[str, Any] | None = None,
    run_status: Any = None,
    event_count: Any = None,
    family_counts: Mapping[str, Any] | None = None,
    required_families: Sequence[str] | None = None,
    missing_required_families: Sequence[Any] | None = None,
    summary_metrics: Mapping[str, Any] | None = None,
    machine_metrics: Mapping[str, Any] | None = None,
    product_readfeel_scorecard: Mapping[str, Any] | None = None,
    phase11_long_run_product_gate: Mapping[str, Any] | None = None,
    runtime_surface_blind_qa_long_run_summary: Mapping[str, Any] | None = None,
    user_label_connection_qa_summary: Mapping[str, Any] | None = None,
    blind_qa_integration: Mapping[str, Any] | None = None,
    blocker_matrix: Mapping[str, Any] | None = None,
    composer_resolution_summary: Mapping[str, Any] | None = None,
    composer_bootstrap: Mapping[str, Any] | None = None,
    public_feedback_boundary_summary: Mapping[str, Any] | None = None,
    rn_contract_assertion_summary: Mapping[str, Any] | None = None,
    timeout_unavailable_safety_stats: Mapping[str, Any] | None = None,
    run_blockers: Sequence[Any] | Iterable[Any] | None = None,
    release_candidate_evidence_confirmed: bool = False,
    all_allowed_requested: bool = False,
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
    if machine_metrics is not None:
        run["machine_metrics"] = dict(machine_metrics)
    if composer_bootstrap is not None:
        run["composer_bootstrap"] = dict(composer_bootstrap)

    if release_candidate_evidence_confirmed and timeout_unavailable_safety_stats is None:
        timeout_unavailable_safety_stats = {
            "limited_user_shadow_ready": True,
            "operational_rollout_ready": True,
            "rollback_plan_confirmed": True,
            "timeout_rate": 0.0,
            "unavailable_rate": 0.0,
            "safety_major_count": 0,
        }

    scorecard = _safe_mapping(product_readfeel_scorecard) or _nested(run, "product_readfeel_scorecard")
    phase11 = _safe_mapping(phase11_long_run_product_gate) or _nested(run, "phase11_long_run_product_gate")
    runtime_summary = _safe_mapping(runtime_surface_blind_qa_long_run_summary) or _nested(run, "runtime_surface_blind_qa_long_run_summary")
    user_label_summary = _safe_mapping(user_label_connection_qa_summary) or _nested(run, "user_label_connection_qa_summary")
    blind_qa = _safe_mapping(blind_qa_integration) or _nested(run, "blind_qa_integration")
    matrix = _safe_mapping(blocker_matrix) or _nested(run, "blocker_matrix")
    composer_summary = _safe_mapping(composer_resolution_summary) or _safe_mapping(composer_bootstrap) or _nested(run, "composer_bootstrap") or _nested(run, "composer_resolution")
    timeout_stats = _safe_mapping(timeout_unavailable_safety_stats) or _nested(run, "timeout_unavailable_safety_stats")
    public_boundary = _safe_mapping(public_feedback_boundary_summary)
    rn_contract = _safe_mapping(rn_contract_assertion_summary)

    materials = _source_materials(run, scorecard, phase11, runtime_summary, user_label_summary, blind_qa, matrix, composer_summary, timeout_stats, public_boundary, rn_contract)
    source_text_payload_detected = any(_contains_key(material, _TEXT_PAYLOAD_KEYS) for material in materials)
    source_contract_violations = _contract_violations(materials)
    metrics = _evaluated_metrics(
        run=run,
        scorecard=scorecard,
        phase11=phase11,
        runtime_summary=runtime_summary,
        user_label_summary=user_label_summary,
        blind_qa=blind_qa,
        timeout_stats=timeout_stats,
    )
    checks = _target_checks(metrics, blind_qa=blind_qa, phase11=phase11)
    composer_open = _composer_open(run, composer_summary)
    operational = _operational_summary(timeout_stats)
    events_present = bool(_int(run.get("event_count")) > 0 or _safe_mapping(run.get("family_counts")))

    blockers: list[str] = []
    blockers.extend(_dedupe(run_blockers))
    blockers.extend(_dedupe(run.get("blockers")))
    blockers.extend(_dedupe(scorecard.get("release_blockers") or scorecard.get("blockers")))
    blockers.extend(_dedupe(phase11.get("v1_product_pass_blockers") or phase11.get("release_blockers") or phase11.get("blockers")))
    blockers.extend(_dedupe(runtime_summary.get("release_blockers") or runtime_summary.get("step11_release_blockers") or runtime_summary.get("blockers")))
    blockers.extend(_dedupe(user_label_summary.get("release_blockers") or user_label_summary.get("qa_blockers") or user_label_summary.get("blockers")))
    blockers.extend(_dedupe(blind_qa.get("release_blockers") or blind_qa.get("qa_blockers") or blind_qa.get("blockers")))
    blockers.extend(_dedupe(matrix.get("blocker_ids")))
    for row in _listify(matrix.get("rows") or matrix.get("blocker_matrix_rows")):
        if isinstance(row, Mapping) and _bool(row.get("release_blocking"), True):
            blockers.extend(_dedupe(row.get("blocker_id")))
    blockers.extend(_blockers_from_contract(source_contract_violations, source_text_payload_detected))
    blockers.extend(_blockers_from_targets(checks))
    if composer_open is not True:
        blockers.append(BLOCKER_RELEASE_COMPOSER_NOT_OPEN)
    if not events_present:
        blockers.append("phase3_events_missing")
    if _all_internal_green(checks) and operational.get("limited_user_shadow_ready") is not True:
        blockers.append(BLOCKER_RELEASE_CANDIDATE_SHADOW_EVIDENCE_MISSING)
    if operational.get("limited_user_shadow_ready") is True and (
        operational.get("operational_rollout_ready") is not True or operational.get("rollback_plan_confirmed") is not True
    ):
        blockers.append(BLOCKER_RELEASE_OPERATIONAL_NOT_READY)
    blockers = _dedupe(blockers)

    stage = _stage(
        blockers=blockers,
        checks=checks,
        composer_open=composer_open,
        events_present=events_present,
        operational=operational,
        all_allowed_requested=all_allowed_requested,
    )
    release_allowed = bool(stage in {RELEASE_STAGE_RELEASE_CANDIDATE, RELEASE_STAGE_ALL_ALLOWED} and not blockers)
    followups = _followups(blockers, matrix)
    internal_green = _all_internal_green(checks)
    contract_freeze = build_emlis_ai_product_quality_contract_freeze()

    decision = {
        "schema_version": PRODUCT_RELEASE_DECISION_SCHEMA_VERSION,
        "version": PRODUCT_RELEASE_DECISION_VERSION,
        "phase": PRODUCT_RELEASE_DECISION_PHASE,
        "target_step": PRODUCT_RELEASE_DECISION_TARGET_STEP,
        "run_id": (_clean(run_id) or _clean(run.get("run_id")))[:96],
        "decision_id": (_clean(decision_id) or f"decision_{uuid4().hex[:12]}")[:96],
        "decision_status": "green" if release_allowed else "blocked",
        "release_allowed": release_allowed,
        "release_stage": stage,
        "release_blockers": blockers,
        "release_blocker_count": len(blockers),
        "required_followup_fixes": followups,
        "required_followup_fix_count": len(followups),
        "summary": {
            "release_allowed": release_allowed,
            "release_stage": stage,
            "release_blocker_count": len(blockers),
            "required_followup_fix_count": len(followups),
            "internal_quality_targets_met": internal_green,
            "blind_qa_integration_ready": bool(checks.get("blind_qa_integration_ready")),
            "phase11_long_run_ready": bool(checks.get("phase11_long_run_ready")),
            "composer_generation_path_open": bool(composer_open is True),
            "public_contract_changed": False,
            "rn_contract_changed": False,
            "db_schema_changed": False,
            "product_gate_ready": False,
            "public_release_applied": False,
        },
        "contract_freeze": contract_freeze,
        "contract_assertions": _contract_assertions(),
        "source_contract_violations": source_contract_violations,
        "source_text_payload_detected": source_text_payload_detected,
        "score_targets": _score_targets(),
        "evaluated_metrics": metrics,
        "target_checks": checks,
        "readiness_flags": {
            "all_score_targets_met": internal_green,
            "release_candidate_evidence_confirmed": bool(release_candidate_evidence_confirmed or operational.get("limited_user_shadow_ready")),
            "limited_user_shadow_ready": bool(operational.get("limited_user_shadow_ready")),
            "operational_rollout_ready": bool(operational.get("operational_rollout_ready")),
            "rollback_plan_confirmed": bool(operational.get("rollback_plan_confirmed")),
        },
        "operational_boundary_summary": operational,
        "composer_generation_path_open": bool(composer_open is True),
        "source_material_status": {
            "measurement_run_connected": bool(run),
            "product_readfeel_scorecard_connected": bool(scorecard),
            "phase11_long_run_product_gate_connected": bool(phase11),
            "runtime_surface_blind_qa_summary_connected": bool(runtime_summary),
            "user_label_connection_qa_summary_connected": bool(user_label_summary),
            "blind_qa_integration_connected": bool(blind_qa),
            "blocker_matrix_connected": bool(matrix),
            "composer_resolution_connected": bool(composer_summary),
        },
        "stage_checks": {
            "internal_quality_targets_met": internal_green,
            "release_allowed_requires_release_candidate_or_all_allowed": True,
            "actual_rollout_remains_separate": True,
            "limited_user_shadow_ready": bool(operational.get("limited_user_shadow_ready")),
            "operational_rollout_ready": bool(operational.get("operational_rollout_ready")),
            "rollback_plan_confirmed": bool(operational.get("rollback_plan_confirmed")),
            "release_candidate_evidence_confirmed": bool(release_candidate_evidence_confirmed or operational.get("limited_user_shadow_ready")),
            "all_allowed_requested": bool(all_allowed_requested),
        },
        "runtime_read_feeling_source": "blind_qa_required_not_machine_metric",
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
    }
    assert_product_release_decision_meta_only(decision)
    return decision


def build_product_release_decision_from_measurement_run(measurement_run: Mapping[str, Any], **kwargs: Any) -> dict[str, Any]:
    return build_product_release_decision(measurement_run=measurement_run, **kwargs)


def dump_product_release_decision(decision: Mapping[str, Any]) -> str:
    data = _safe_mapping(decision)
    assert_product_release_decision_meta_only(data)
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


build_emlis_ai_product_release_decision = build_product_release_decision
build_emlis_ai_product_release_decision_from_measurement_run = build_product_release_decision_from_measurement_run
assert_emlis_ai_product_release_decision_meta_only = assert_product_release_decision_meta_only
dump_emlis_ai_product_release_decision = dump_product_release_decision

__all__ = [
    "BINDING_PASS_RATE_TARGET",
    "BLIND_QA_REVIEW_COVERAGE_TARGET",
    "DISPLAY_REACH_RATE_TARGET",
    "PRODUCT_RELEASE_DECISION_PHASE",
    "PRODUCT_RELEASE_DECISION_SCHEMA_VERSION",
    "PRODUCT_RELEASE_DECISION_TARGET_STEP",
    "PRODUCT_RELEASE_DECISION_VERSION",
    "REASON_COVERAGE_TARGET",
    "RELEASE_STAGE_ALL_ALLOWED",
    "RELEASE_STAGE_INTERNAL_QA",
    "RELEASE_STAGE_LIMITED_INTERNAL_GREEN",
    "RELEASE_STAGE_LIMITED_USER_SHADOW",
    "RELEASE_STAGE_NOT_READY",
    "RELEASE_STAGE_RELEASE_CANDIDATE",
    "RELEASE_STAGES",
    "USER_LABEL_CONNECTION_QUALITY_TARGET",
    "assert_emlis_ai_product_release_decision_meta_only",
    "assert_product_release_decision_meta_only",
    "build_emlis_ai_product_release_decision",
    "build_emlis_ai_product_release_decision_from_measurement_run",
    "build_product_release_decision",
    "build_product_release_decision_from_measurement_run",
    "dump_emlis_ai_product_release_decision",
    "dump_product_release_decision",
]
