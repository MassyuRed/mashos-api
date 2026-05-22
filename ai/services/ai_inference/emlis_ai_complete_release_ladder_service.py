# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step7 Release ladder connection for EmlisAI Complete Composer.

This module turns the Step6 ProductQualityScorecard into release-ladder
criteria for internal -> limited -> broader beta -> Product Gate.  It is
intentionally meta-only: it never writes ``comment_text``, never relaxes any
Gate, and never changes public API/RN/DB contracts.
"""

from collections import Counter
from typing import Any, Iterable, Mapping, Sequence

from emlis_ai_complete_scorecard_service import COMPLETE_COVERAGE_GROUP_ORDER
from emlis_ai_complete_product_quality_scorecard_service import (
    COMPLETE_PRODUCT_GATE_DISPLAY_TARGET,
    COMPLETE_PRODUCT_QUALITY_BINDING_TARGET,
    COMPLETE_PRODUCT_QUALITY_CONNECTION_DISPLAY_TARGET,
    COMPLETE_PRODUCT_QUALITY_READ_FEELING_INITIAL_TARGET,
    COMPLETE_PRODUCT_QUALITY_READ_FEELING_PRODUCT_TARGET,
    COMPLETE_PRODUCT_QUALITY_REASON_COVERAGE_TARGET,
    COMPLETE_PRODUCT_QUALITY_SURFACE_METRICS_STEP,
    COMPLETE_PRODUCT_QUALITY_SURFACE_METRICS_VERSION,
)
from emlis_ai_display_gate import GATE_BINDING_CONTRACT_VERSION
from emlis_ai_runtime_surface_exit_gate import (
    RUNTIME_SURFACE_EXIT_GATE_STEP,
    RUNTIME_SURFACE_EXIT_GATE_VERSION,
)

COMPLETE_PRODUCT_QUALITY_RELEASE_LADDER_VERSION = "emlis.complete_product_quality_release_ladder.v1"
COMPLETE_PRODUCT_QUALITY_RELEASE_LADDER_STAGE = "Step7_Release_ladder_connection"
COMPLETE_PRODUCT_QUALITY_RELEASE_LADDER_STEP = COMPLETE_PRODUCT_QUALITY_RELEASE_LADDER_STAGE
COMPLETE_PRODUCT_QUALITY_RELEASE_LADDER_IMPLEMENTATION_UNIT = "ProductQualityConnection.Step7"
COMPLETE_PRODUCT_QUALITY_RELEASE_LADDER_CRITERIA_VERSION = "emlis.complete_product_quality_release_ladder_criteria.v1"
COMPLETE_PRODUCT_QUALITY_RELEASE_LADDER_GUARD_VERSION = "emlis.complete_product_quality_release_ladder_guard.v1"

COMPLETE_RELEASE_LADDER_STAGES: Sequence[str] = (
    "internal",
    "limited",
    "broader_beta",
    "product_gate",
)

# A single reply attempt is enough to prove the connection is wired, but not
# enough to graduate to user-facing ladder stages.  The release ladder consumes
# aggregate scorecards; this prevents one green request from looking like a
# Product Gate decision.
COMPLETE_RELEASE_LADDER_LIMITED_MIN_COVERAGE_GROUPS = 3
COMPLETE_RELEASE_LADDER_BROADER_MIN_COVERAGE_GROUPS = len(COMPLETE_COVERAGE_GROUP_ORDER)
COMPLETE_RELEASE_LADDER_PRODUCT_MIN_COVERAGE_GROUPS = len(COMPLETE_COVERAGE_GROUP_ORDER)

_BROADER_STOP_MARKERS = (
    "overinterpret",
    "over_interpretation",
    "overclaim",
    "generic_comfort",
    "general_comfort",
    "diagnostic_tone",
    "diagnosis",
)
_TEMPLATE_STOP_MARKERS = (
    "template",
    "fixed_fallback",
    "fixed_sentence",
    "role_fixed",
    "raw_echo",
    "same_ending",
    "surface_signature_repeat",
    "surface_template_major",
    "surface_connector_repetition",
    "connector_repetition",
    "predicate_family_repetition",
    "generic_center_phrase",
    "grammar_warning",
)
_UNSUPPORTED_STOP_MARKERS = (
    "unsupported_sentence",
    "unsupported",
)
_GATE_RELAXED_KEYS = (
    "display_gate_relaxed",
    "grounding_gate_relaxed",
    "template_gate_relaxed",
    "reader_gate_relaxed",
    "gate_relaxed",
)
_CONTRACT_BREAK_KEYS = (
    "response_shape_changed",
    "public_response_key_change",
    "api_route_changed",
    "db_physical_name_changed",
    "rn_visible_title_changed",
)
_FORBIDDEN_GENERATION_KEYS = (
    "fixed_fallback_used",
    "fixed_sentence_template_used",
    "fixed_completed_sentence_template_added",
    "input_specific_template_added",
    "external_ai_used",
    "local_llm_used",
)
_RAW_INPUT_DEPENDENCY_KEYS = (
    "raw_input_included",
    "raw_text_included",
    "raw_input_required_for_improvement",
    "raw_input_dependency",
)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _safe_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(k): v for k, v in value.items()}
    return {}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple) or isinstance(value, set):
        return list(value)
    return [value]


def _dedupe(values: Iterable[Any] | Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in _as_list(values):
        text = _clean(item)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _bool_any(*sources: Mapping[str, Any], keys: Sequence[str]) -> bool:
    for source in sources:
        data = _safe_mapping(source)
        for key in keys:
            if bool(data.get(key)):
                return True
    return False


def _collect_reasons(*sources: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    for source in sources:
        data = _safe_mapping(source)
        for key in (
            "release_blockers",
            "blocking_reasons",
            "top_rejection_reasons",
            "gate_rejection_reasons",
            "rejection_reasons",
            "secondary_reasons",
            "unsupported_reasons",
            "tone_guard_reasons",
        ):
            reasons.extend(_dedupe(data.get(key)))
        for key in (
            "primary_reason",
            "gate_primary_reason",
            "first_failed_reason",
            "stage",
            "failed_stage",
            "product_gate_decision",
        ):
            value = _clean(data.get(key))
            if value:
                reasons.append(value)
        nested = data.get("machine_metrics")
        if isinstance(nested, Mapping):
            reasons.extend(_collect_reasons(nested))
        nested = data.get("blind_qa_metrics")
        if isinstance(nested, Mapping):
            reasons.extend(_collect_reasons(nested))
    return _dedupe(reasons)


def _count_marker_hits(reasons: Sequence[str], markers: Sequence[str]) -> int:
    count = 0
    for reason in reasons:
        lower = reason.lower()
        if any(marker in lower for marker in markers):
            count += 1
    return count


def _coverage_groups_from_scorecard(scorecard: Mapping[str, Any]) -> list[str]:
    groups: list[str] = []

    for key in ("observed_coverage_groups", "coverage_groups"):
        for group in _dedupe(scorecard.get(key)):
            if group in COMPLETE_COVERAGE_GROUP_ORDER:
                groups.append(group)

    by_group = scorecard.get("by_coverage_group")
    if isinstance(by_group, Mapping):
        for group, row in by_group.items():
            normalized_group = _clean(group)
            if normalized_group not in COMPLETE_COVERAGE_GROUP_ORDER:
                continue
            row_data = _safe_mapping(row)
            if _safe_int(row_data.get("eligible_count"), 0) > 0 or _safe_int(row_data.get("event_count"), 0) > 0:
                groups.append(normalized_group)

    rows = scorecard.get("coverage_group_rows")
    if isinstance(rows, list):
        for row in rows:
            data = _safe_mapping(row)
            group = _clean(data.get("coverage_group"))
            if group not in COMPLETE_COVERAGE_GROUP_ORDER:
                continue
            if _safe_int(data.get("eligible_count"), 0) > 0 or _safe_int(data.get("event_count"), 0) > 0:
                groups.append(group)

    machine = _safe_mapping(scorecard.get("machine_metrics"))
    if machine:
        groups.extend(_coverage_groups_from_scorecard(machine))

    if not groups:
        group = _clean(scorecard.get("coverage_group"))
        if group in COMPLETE_COVERAGE_GROUP_ORDER:
            groups.append(group)

    ordered: list[str] = []
    seen: set[str] = set()
    for group in groups:
        if group and group not in seen:
            seen.add(group)
            ordered.append(group)
    return ordered


def _coverage_group_missing_count_from_scorecard(scorecard: Mapping[str, Any]) -> int:
    machine = _safe_mapping(scorecard.get("machine_metrics"))
    explicit = _safe_int(scorecard.get("coverage_group_missing_count"), -1)
    if explicit >= 0:
        return explicit
    explicit = _safe_int(machine.get("coverage_group_missing_count"), -1)
    if explicit >= 0:
        return explicit
    by_group = _safe_mapping(scorecard.get("by_coverage_group")) or _safe_mapping(machine.get("by_coverage_group"))
    missing_row = _safe_mapping(by_group.get("coverage_group_missing"))
    return _safe_int(missing_row.get("event_count"), 0)


def _missing_coverage_groups_from_scorecard(scorecard: Mapping[str, Any], observed_groups: Sequence[str]) -> list[str]:
    machine = _safe_mapping(scorecard.get("machine_metrics"))
    explicit = _dedupe(scorecard.get("missing_coverage_groups")) or _dedupe(machine.get("missing_coverage_groups"))
    if explicit:
        return [group for group in explicit if group in COMPLETE_COVERAGE_GROUP_ORDER]
    observed = set(observed_groups)
    return [group for group in COMPLETE_COVERAGE_GROUP_ORDER if group not in observed]


def _required_coverage_complete(groups: Sequence[str]) -> bool:
    present = set(groups)
    return all(group in present for group in COMPLETE_COVERAGE_GROUP_ORDER)


def _stage_payload(stage: str, *, allowed: bool, blockers: Sequence[str], criteria: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "stage": stage,
        "allowed": bool(allowed),
        "passed": bool(allowed),
        "blockers": _dedupe(blockers),
        "criteria": dict(criteria),
    }


def _highest_allowed_stage(evaluations: Mapping[str, Mapping[str, Any]]) -> str:
    highest = "blocked"
    for stage in COMPLETE_RELEASE_LADDER_STAGES:
        if _safe_mapping(evaluations.get(stage)).get("allowed") is True:
            highest = stage
    return highest


def build_complete_product_quality_release_ladder_criteria() -> dict[str, Any]:
    return {
        "version": COMPLETE_PRODUCT_QUALITY_RELEASE_LADDER_CRITERIA_VERSION,
        "target_step": COMPLETE_PRODUCT_QUALITY_RELEASE_LADDER_STEP,
        "step": COMPLETE_PRODUCT_QUALITY_RELEASE_LADDER_STEP,
        "stage_order": list(COMPLETE_RELEASE_LADDER_STAGES),
        "required_coverage_groups": list(COMPLETE_COVERAGE_GROUP_ORDER),
        "internal": {
            "allowed_scope": "development_fixtures_and_local_qa_only",
            "promotion_conditions": ("step0_to_step6_contracts_green", "safety_major_count_zero"),
            "stop_conditions": ("binding_contract_unresolved", "reason_missing", "rn_contract_failure"),
        },
        "limited": {
            "allowed_scope": "partial_eligible_normal_input_coverage",
            "promotion_conditions": ("display_reach_rate_at_least_0_80", "binding_pass_rate_at_least_0_98", "template_major_count_zero", "safety_major_count_zero"),
            "stop_conditions": ("unsupported_sentence_increase", "fixed_fallback_mixed"),
        },
        "broader_beta": {
            "allowed_scope": "major_coverage_groups",
            "promotion_conditions": ("blind_qa_read_feeling_at_least_0_85", "reason_coverage_100_percent"),
            "stop_conditions": ("overinterpretation", "generic_comfort", "diagnostic_tone"),
        },
        "product_gate": {
            "allowed_scope": "product_quality_gate_judgment_material",
            "promotion_conditions": ("display_reach_rate_at_least_0_90", "binding_pass_rate_at_least_0_98", "read_feeling_at_least_0_90", "safety_major_count_zero", "template_major_count_zero"),
            "stop_conditions": ("gate_relaxed", "raw_input_dependency", "fixed_fallback", "public_contract_changed"),
        },
        "targets": {
            "connection_display_target": COMPLETE_PRODUCT_QUALITY_CONNECTION_DISPLAY_TARGET,
            "product_gate_display_target": COMPLETE_PRODUCT_GATE_DISPLAY_TARGET,
            "binding_pass_rate": COMPLETE_PRODUCT_QUALITY_BINDING_TARGET,
            "broader_read_feeling_target": COMPLETE_PRODUCT_QUALITY_READ_FEELING_INITIAL_TARGET,
            "product_gate_read_feeling_target": COMPLETE_PRODUCT_QUALITY_READ_FEELING_PRODUCT_TARGET,
            "reason_coverage_rate": COMPLETE_PRODUCT_QUALITY_REASON_COVERAGE_TARGET,
            "limited_min_coverage_group_count": COMPLETE_RELEASE_LADDER_LIMITED_MIN_COVERAGE_GROUPS,
            "broader_min_coverage_group_count": COMPLETE_RELEASE_LADDER_BROADER_MIN_COVERAGE_GROUPS,
            "product_gate_min_coverage_group_count": COMPLETE_RELEASE_LADDER_PRODUCT_MIN_COVERAGE_GROUPS,
            "surface_metrics_version": COMPLETE_PRODUCT_QUALITY_SURFACE_METRICS_VERSION,
            "surface_signature_repeat_rate": 0.0,
            "connector_repetition_rate": 0.0,
            "grammar_warning_rate": 0.0,
            "surface_template_major_count": 0,
        },
        "runtime_surface_exit_gate_step": RUNTIME_SURFACE_EXIT_GATE_STEP,
        "runtime_surface_exit_gate_version": RUNTIME_SURFACE_EXIT_GATE_VERSION,
        "runtime_surface_exit_gate_handoff_only": True,
        "runtime_surface_exit_gate_required_before_public_release": True,
        "step12_exit_gate_required_before_public_release": True,
        "comment_text_contract": "passed_only",
        "meta_only": True,
        "raw_input_included": False,
        "comment_text_included": False,
        "response_shape_changed": False,
    }


def build_complete_product_quality_release_ladder(
    *,
    product_quality_scorecard: Mapping[str, Any] | None = None,
    diagnostic_summary: Mapping[str, Any] | None = None,
    phase_gate: Mapping[str, Any] | None = None,
    contract_checks: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate Step7 release-ladder criteria from Step6 scorecard meta."""

    scorecard = _safe_mapping(product_quality_scorecard)
    diagnostic = _safe_mapping(diagnostic_summary)
    phase = _safe_mapping(phase_gate)
    checks_override = _safe_mapping(contract_checks)
    machine = _safe_mapping(scorecard.get("machine_metrics"))
    blind = _safe_mapping(scorecard.get("blind_qa_metrics"))
    criteria = build_complete_product_quality_release_ladder_criteria()

    display_reach_rate = _safe_float(scorecard.get("display_reach_rate"), _safe_float(machine.get("display_reach_rate"), 0.0))
    binding_pass_rate = _safe_float(scorecard.get("binding_pass_rate"), _safe_float(machine.get("binding_pass_rate"), 0.0))
    repair_success_rate = _safe_float(scorecard.get("repair_success_rate"), _safe_float(machine.get("repair_success_rate"), 0.0))
    reason_coverage_rate = _safe_float(scorecard.get("reason_coverage_rate"), _safe_float(machine.get("reason_coverage_rate"), 0.0))
    read_feeling_score_value = scorecard.get("read_feeling_score")
    if read_feeling_score_value is None:
        read_feeling_score_value = blind.get("read_feeling_score")
    read_feeling_score = _safe_float(read_feeling_score_value, -1.0)

    safety_major_count = _safe_int(scorecard.get("safety_major_count"), _safe_int(machine.get("safety_major_count"), 0))
    template_major_count = _safe_int(scorecard.get("template_major_count"), _safe_int(machine.get("template_major_count"), 0))
    surface_metrics = _safe_mapping(scorecard.get("surface_metrics")) or _safe_mapping(machine.get("surface_metrics"))
    surface_template_major_count = _safe_int(
        scorecard.get("surface_template_major_count"),
        _safe_int(machine.get("surface_template_major_count"), _safe_int(surface_metrics.get("surface_template_major_count"), 0)),
    )
    template_major_count = max(template_major_count, surface_template_major_count)
    surface_signature_count = _safe_int(
        scorecard.get("surface_signature_count"),
        _safe_int(machine.get("surface_signature_count"), _safe_int(surface_metrics.get("surface_signature_count"), 0)),
    )
    surface_signature_repeat_count = _safe_int(
        scorecard.get("surface_signature_repeat_count"),
        _safe_int(machine.get("surface_signature_repeat_count"), _safe_int(surface_metrics.get("surface_signature_repeat_count"), 0)),
    )
    surface_signature_repeat_rate = _safe_float(
        scorecard.get("surface_signature_repeat_rate"),
        _safe_float(machine.get("surface_signature_repeat_rate"), _safe_float(surface_metrics.get("surface_signature_repeat_rate"), 0.0)),
    )
    connector_repetition_rate = _safe_float(
        scorecard.get("connector_repetition_rate"),
        _safe_float(machine.get("connector_repetition_rate"), _safe_float(surface_metrics.get("connector_repetition_rate"), 0.0)),
    )
    grammar_warning_rate = _safe_float(
        scorecard.get("grammar_warning_rate"),
        _safe_float(machine.get("grammar_warning_rate"), _safe_float(surface_metrics.get("grammar_warning_rate"), 0.0)),
    )
    coverage_surface_diversity_rate = _safe_float(
        scorecard.get("coverage_surface_diversity_rate"),
        _safe_float(machine.get("coverage_surface_diversity_rate"), _safe_float(surface_metrics.get("coverage_surface_diversity_rate"), 0.0)),
    )
    surface_metrics_ready = bool(scorecard.get("surface_metrics_ready") or machine.get("surface_metrics_ready") or surface_metrics.get("surface_metrics_ready"))
    eligible_count = _safe_int(scorecard.get("eligible_count"), _safe_int(machine.get("eligible_count"), 0))
    passed_display_count = _safe_int(scorecard.get("passed_display_count"), _safe_int(machine.get("passed_display_count"), 0))
    coverage_groups = _coverage_groups_from_scorecard(scorecard)
    coverage_group_count = len(coverage_groups)
    missing_coverage_groups = _missing_coverage_groups_from_scorecard(scorecard, coverage_groups)
    coverage_group_missing_count = _coverage_group_missing_count_from_scorecard(scorecard)
    required_coverage_complete = (
        _required_coverage_complete(coverage_groups)
        and not missing_coverage_groups
        and coverage_group_missing_count == 0
    )
    blind_qa_ready = bool(scorecard.get("blind_qa_ready") or blind.get("blind_qa_ready"))
    machine_metrics_ready = bool(scorecard.get("machine_metrics_ready") or machine.get("machine_metrics_ready"))
    scorecard_ready = bool(scorecard.get("product_quality_scorecard_ready") or scorecard.get("scorecard_ready") or scorecard.get("ready"))

    all_reasons = _collect_reasons(scorecard, machine, diagnostic, phase)
    reason_counter = dict(Counter(all_reasons))
    unsupported_stop = _count_marker_hits(all_reasons, _UNSUPPORTED_STOP_MARKERS) > 0
    template_reason_stop = _count_marker_hits(all_reasons, _TEMPLATE_STOP_MARKERS) > 0
    broader_reason_stop = _count_marker_hits(all_reasons, _BROADER_STOP_MARKERS) > 0

    gate_relaxed = _bool_any(scorecard, diagnostic, phase, keys=_GATE_RELAXED_KEYS)
    contract_changed = _bool_any(scorecard, diagnostic, phase, keys=_CONTRACT_BREAK_KEYS)
    forbidden_generation_used = _bool_any(scorecard, diagnostic, phase, keys=_FORBIDDEN_GENERATION_KEYS)
    raw_input_dependency = _bool_any(scorecard, diagnostic, phase, keys=_RAW_INPUT_DEPENDENCY_KEYS)

    binding_contract_version = _clean(
        diagnostic.get("gate_binding_contract_version")
        or scorecard.get("gate_binding_contract_version")
        or checks_override.get("gate_binding_contract_version")
    )
    binding_contract_ready = bool(
        checks_override.get("binding_contract_ready")
        if "binding_contract_ready" in checks_override
        else (not binding_contract_version or binding_contract_version == GATE_BINDING_CONTRACT_VERSION)
    )
    rn_contract_ready = bool(
        checks_override.get("rn_contract_ready")
        if "rn_contract_ready" in checks_override
        else (not contract_changed and phase.get("step6_product_quality_response_shape_changed") is not True and phase.get("step6_product_quality_comment_text_written") is not True)
    )
    reason_contract_ready = bool(
        checks_override.get("reason_coverage_ready")
        if "reason_coverage_ready" in checks_override
        else (reason_coverage_rate >= COMPLETE_PRODUCT_QUALITY_REASON_COVERAGE_TARGET)
    )
    step0_6_contract_tests_green = bool(
        checks_override.get("step0_6_contract_tests_green")
        if "step0_6_contract_tests_green" in checks_override
        else (scorecard_ready and machine_metrics_ready and binding_contract_ready and rn_contract_ready and reason_contract_ready and not gate_relaxed and not forbidden_generation_used)
    )

    internal_blockers: list[str] = []
    if not scorecard_ready:
        internal_blockers.append("product_quality_scorecard_missing")
    if not machine_metrics_ready:
        internal_blockers.append("machine_metrics_missing")
    if not binding_contract_ready:
        internal_blockers.append("binding_contract_unresolved")
    if not reason_contract_ready:
        internal_blockers.append("reason_coverage_missing")
    if not rn_contract_ready or contract_changed:
        internal_blockers.append("rn_contract_failure")
    if gate_relaxed:
        internal_blockers.append("gate_relaxed")
    if forbidden_generation_used:
        internal_blockers.append("forbidden_generation_used")
    if safety_major_count > 0:
        internal_blockers.append("safety_major_detected")
    internal_allowed = bool(step0_6_contract_tests_green and safety_major_count == 0 and not internal_blockers)

    limited_blockers = list(internal_blockers)
    if coverage_group_count < COMPLETE_RELEASE_LADDER_LIMITED_MIN_COVERAGE_GROUPS:
        limited_blockers.append("limited_coverage_group_count_below_minimum")
    if display_reach_rate < COMPLETE_PRODUCT_QUALITY_CONNECTION_DISPLAY_TARGET:
        limited_blockers.append("display_reach_rate_below_limited_target")
    if binding_pass_rate < COMPLETE_PRODUCT_QUALITY_BINDING_TARGET:
        limited_blockers.append("binding_pass_rate_below_target")
    if template_major_count > 0:
        limited_blockers.append("template_major_detected")
    if surface_template_major_count > 0:
        limited_blockers.append("surface_template_major_detected")
    if safety_major_count > 0:
        limited_blockers.append("safety_major_detected")
    if unsupported_stop:
        limited_blockers.append("unsupported_sentence_detected")
    if forbidden_generation_used or template_reason_stop:
        limited_blockers.append("fixed_or_template_fallback_detected")
    limited_allowed = bool(internal_allowed and not limited_blockers)

    broader_blockers = list(limited_blockers)
    if coverage_group_count < COMPLETE_RELEASE_LADDER_BROADER_MIN_COVERAGE_GROUPS or not required_coverage_complete:
        broader_blockers.append("major_coverage_groups_incomplete")
    if coverage_group_missing_count > 0:
        broader_blockers.append("coverage_group_missing")
    if missing_coverage_groups:
        broader_blockers.append("required_coverage_groups_missing")
    if not blind_qa_ready:
        broader_blockers.append("blind_qa_missing")
    if read_feeling_score < COMPLETE_PRODUCT_QUALITY_READ_FEELING_INITIAL_TARGET:
        broader_blockers.append("read_feeling_score_below_broader_target")
    if reason_coverage_rate < COMPLETE_PRODUCT_QUALITY_REASON_COVERAGE_TARGET:
        broader_blockers.append("reason_coverage_incomplete")
    if broader_reason_stop:
        broader_blockers.append("overinterpretation_generic_or_diagnostic_tone_detected")
    broader_allowed = bool(limited_allowed and not broader_blockers)

    product_blockers = list(broader_blockers)
    if coverage_group_count < COMPLETE_RELEASE_LADDER_PRODUCT_MIN_COVERAGE_GROUPS or not required_coverage_complete:
        product_blockers.append("product_gate_coverage_groups_incomplete")
    if coverage_group_missing_count > 0 and "coverage_group_missing" not in product_blockers:
        product_blockers.append("coverage_group_missing")
    if display_reach_rate < COMPLETE_PRODUCT_GATE_DISPLAY_TARGET:
        product_blockers.append("display_reach_rate_below_product_gate_target")
    if binding_pass_rate < COMPLETE_PRODUCT_QUALITY_BINDING_TARGET:
        product_blockers.append("binding_pass_rate_below_target")
    if read_feeling_score < COMPLETE_PRODUCT_QUALITY_READ_FEELING_PRODUCT_TARGET:
        product_blockers.append("read_feeling_score_below_product_gate_target")
    if safety_major_count > 0:
        product_blockers.append("safety_major_detected")
    if template_major_count > 0:
        product_blockers.append("template_major_detected")
    if surface_template_major_count > 0:
        product_blockers.append("surface_template_major_detected")
    if gate_relaxed:
        product_blockers.append("gate_relaxed")
    if raw_input_dependency:
        product_blockers.append("raw_input_dependency")
    if forbidden_generation_used:
        product_blockers.append("fixed_fallback_or_external_generation_detected")
    if contract_changed:
        product_blockers.append("public_contract_changed")
    product_allowed = bool(broader_allowed and not product_blockers)

    stage_evaluations = {
        "internal": _stage_payload(
            "internal",
            allowed=internal_allowed,
            blockers=internal_blockers,
            criteria={
                "step0_6_contract_tests_green": step0_6_contract_tests_green,
                "safety_major_count": safety_major_count,
                "binding_contract_ready": binding_contract_ready,
                "reason_contract_ready": reason_contract_ready,
                "rn_contract_ready": rn_contract_ready,
                "surface_metrics_ready": surface_metrics_ready,
            },
        ),
        "limited": _stage_payload(
            "limited",
            allowed=limited_allowed,
            blockers=limited_blockers,
            criteria={
                "coverage_group_count": coverage_group_count,
                "min_coverage_group_count": COMPLETE_RELEASE_LADDER_LIMITED_MIN_COVERAGE_GROUPS,
                "display_reach_rate": display_reach_rate,
                "display_target": COMPLETE_PRODUCT_QUALITY_CONNECTION_DISPLAY_TARGET,
                "binding_pass_rate": binding_pass_rate,
                "binding_target": COMPLETE_PRODUCT_QUALITY_BINDING_TARGET,
                "template_major_count": template_major_count,
                "surface_template_major_count": surface_template_major_count,
                "surface_signature_repeat_rate": surface_signature_repeat_rate,
                "connector_repetition_rate": connector_repetition_rate,
                "grammar_warning_rate": grammar_warning_rate,
                "safety_major_count": safety_major_count,
            },
        ),
        "broader_beta": _stage_payload(
            "broader_beta",
            allowed=broader_allowed,
            blockers=broader_blockers,
            criteria={
                "coverage_group_count": coverage_group_count,
                "required_coverage_complete": required_coverage_complete,
                "missing_coverage_groups": list(missing_coverage_groups),
                "coverage_group_missing_count": coverage_group_missing_count,
                "blind_qa_ready": blind_qa_ready,
                "read_feeling_score": None if read_feeling_score < 0 else read_feeling_score,
                "read_feeling_target": COMPLETE_PRODUCT_QUALITY_READ_FEELING_INITIAL_TARGET,
                "reason_coverage_rate": reason_coverage_rate,
                "reason_coverage_target": COMPLETE_PRODUCT_QUALITY_REASON_COVERAGE_TARGET,
                "coverage_surface_diversity_rate": coverage_surface_diversity_rate,
                "surface_signature_count": surface_signature_count,
            },
        ),
        "product_gate": _stage_payload(
            "product_gate",
            allowed=product_allowed,
            blockers=product_blockers,
            criteria={
                "coverage_group_count": coverage_group_count,
                "required_coverage_complete": required_coverage_complete,
                "missing_coverage_groups": list(missing_coverage_groups),
                "coverage_group_missing_count": coverage_group_missing_count,
                "display_reach_rate": display_reach_rate,
                "display_target": COMPLETE_PRODUCT_GATE_DISPLAY_TARGET,
                "binding_pass_rate": binding_pass_rate,
                "binding_target": COMPLETE_PRODUCT_QUALITY_BINDING_TARGET,
                "read_feeling_score": None if read_feeling_score < 0 else read_feeling_score,
                "read_feeling_target": COMPLETE_PRODUCT_QUALITY_READ_FEELING_PRODUCT_TARGET,
                "safety_major_count": safety_major_count,
                "template_major_count": template_major_count,
                "surface_template_major_count": surface_template_major_count,
                "surface_signature_repeat_count": surface_signature_repeat_count,
                "surface_signature_repeat_rate": surface_signature_repeat_rate,
                "connector_repetition_rate": connector_repetition_rate,
                "grammar_warning_rate": grammar_warning_rate,
                "gate_relaxed": gate_relaxed,
                "raw_input_dependency": raw_input_dependency,
            },
        ),
    }
    max_allowed_stage = _highest_allowed_stage(stage_evaluations)
    next_stage = "internal" if max_allowed_stage == "blocked" else (
        COMPLETE_RELEASE_LADDER_STAGES[min(len(COMPLETE_RELEASE_LADDER_STAGES) - 1, COMPLETE_RELEASE_LADDER_STAGES.index(max_allowed_stage) + 1)]
    )
    product_gate_candidate_ready = bool(product_allowed)
    product_gate_decision = (
        "product_gate_candidate_ready_step7_requires_explicit_release_judgment"
        if product_gate_candidate_ready
        else "blocked_before_product_gate"
    )

    return {
        "version": COMPLETE_PRODUCT_QUALITY_RELEASE_LADDER_VERSION,
        "target_step": COMPLETE_PRODUCT_QUALITY_RELEASE_LADDER_STEP,
        "step": COMPLETE_PRODUCT_QUALITY_RELEASE_LADDER_STEP,
        "implementation_unit": COMPLETE_PRODUCT_QUALITY_RELEASE_LADDER_IMPLEMENTATION_UNIT,
        "guard_version": COMPLETE_PRODUCT_QUALITY_RELEASE_LADDER_GUARD_VERSION,
        "release_ladder_connected": True,
        "runtime_surface_quality_exit_gate_required": True,
        "runtime_surface_quality_exit_gate_supported": True,
        "runtime_surface_quality_exit_gate_step": RUNTIME_SURFACE_EXIT_GATE_STEP,
        "runtime_surface_quality_exit_gate_version": RUNTIME_SURFACE_EXIT_GATE_VERSION,
        "runtime_surface_quality_exit_gate_handoff_only": True,
        "runtime_surface_quality_exit_gate_release_ladder_connected": True,
        "step12_exit_gate_release_ladder_connected": True,
        "runtime_surface_quality_exit_gate_requires_explicit_release_judgment": True,
        "runtime_surface_quality_exit_gate_release_allowed": False,
        "runtime_surface_quality_exit_gate_product_gate_achieved": False,
        "runtime_surface_quality_exit_gate_public_release_applied": False,
        "release_ladder_guard_ready": bool(scorecard_ready),
        "release_ladder_stage_order": list(COMPLETE_RELEASE_LADDER_STAGES),
        "current_stage": max_allowed_stage,
        "max_allowed_stage": max_allowed_stage,
        "next_stage": next_stage,
        "stage_evaluations": stage_evaluations,
        "criteria": criteria,
        "rollout_criteria": criteria,
        "metrics": {
            "eligible_count": eligible_count,
            "passed_display_count": passed_display_count,
            "display_reach_rate": display_reach_rate,
            "binding_pass_rate": binding_pass_rate,
            "repair_success_rate": repair_success_rate,
            "read_feeling_score": None if read_feeling_score < 0 else read_feeling_score,
            "read_feeling_source": _clean(scorecard.get("read_feeling_source")) or ("blind_qa" if blind_qa_ready else "not_evaluated"),
            "safety_major_count": safety_major_count,
            "template_major_count": template_major_count,
            "surface_metrics_version": COMPLETE_PRODUCT_QUALITY_SURFACE_METRICS_VERSION,
            "surface_metrics_step": COMPLETE_PRODUCT_QUALITY_SURFACE_METRICS_STEP,
            "surface_metrics_ready": surface_metrics_ready,
            "surface_signature_count": surface_signature_count,
            "surface_signature_repeat_count": surface_signature_repeat_count,
            "surface_signature_repeat_rate": surface_signature_repeat_rate,
            "connector_repetition_rate": connector_repetition_rate,
            "grammar_warning_rate": grammar_warning_rate,
            "coverage_surface_diversity_rate": coverage_surface_diversity_rate,
            "surface_template_major_count": surface_template_major_count,
            "reason_coverage_rate": reason_coverage_rate,
            "coverage_group_count": coverage_group_count,
            "coverage_groups": list(coverage_groups),
            "required_coverage_groups": list(COMPLETE_COVERAGE_GROUP_ORDER),
            "missing_coverage_groups": list(missing_coverage_groups),
            "coverage_group_missing_count": coverage_group_missing_count,
            "required_coverage_complete": required_coverage_complete,
            "blind_qa_ready": blind_qa_ready,
            "machine_metrics_ready": machine_metrics_ready,
        },
        "contract_checks": {
            "step0_6_contract_tests_green": step0_6_contract_tests_green,
            "binding_contract_ready": binding_contract_ready,
            "binding_contract_version": binding_contract_version,
            "expected_binding_contract_version": GATE_BINDING_CONTRACT_VERSION,
            "rn_contract_ready": rn_contract_ready,
            "reason_contract_ready": reason_contract_ready,
            "scorecard_ready": scorecard_ready,
            "machine_metrics_ready": machine_metrics_ready,
            "surface_metrics_ready": surface_metrics_ready,
            "blind_qa_ready": blind_qa_ready,
        },
        "stop_conditions": {
            "gate_relaxed": gate_relaxed,
            "contract_changed": contract_changed,
            "fixed_fallback_or_template_used": forbidden_generation_used or template_reason_stop,
            "raw_input_dependency": raw_input_dependency,
            "surface_template_major_detected": surface_template_major_count > 0,
            "surface_signature_repeat_detected": surface_signature_repeat_count > 0,
            "surface_connector_repetition_detected": connector_repetition_rate > 0,
            "surface_grammar_warning_detected": grammar_warning_rate > 0,
            "unsupported_sentence_detected": unsupported_stop,
            "overinterpretation_generic_or_diagnostic_tone_detected": broader_reason_stop,
        },
        "reason_counter": reason_counter,
        "release_blockers": _dedupe(product_blockers if not product_allowed else []),
        "runtime_surface_quality_exit_gate_release_blockers": _dedupe(product_blockers if not product_allowed else []),
        "ladder_blockers": _dedupe(stage_evaluations.get(max_allowed_stage, {}).get("blockers") if max_allowed_stage != "blocked" else internal_blockers),
        "product_gate_candidate_ready": product_gate_candidate_ready,
        "product_gate_transition_allowed": product_gate_candidate_ready,
        "product_gate_ready": product_gate_candidate_ready,
        "product_gate_reached": False,
        "product_gate_decision": product_gate_decision,
        "product_gate_public_release_applied": False,
        "public_release_applied": False,
        "release_ladder_public_release_applied": False,
        "product_quality_released": False,
        "release_judgment": {
            "release_allowed": False,
            "stage_transition_allowed": bool(max_allowed_stage != "blocked"),
            "max_allowed_stage": max_allowed_stage,
            "reason": "step7_release_ladder_connection_only_public_release_not_applied",
        },
        "comment_text_contract": "passed_only",
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "comment_text_written_by_step7_release_ladder": False,
        "meta_only": True,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "fixed_fallback_used": False,
        "external_ai_used": False,
        "local_llm_used": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
    }


build_complete_product_quality_release_ladder_guard = build_complete_product_quality_release_ladder
build_complete_product_quality_release_ladder_report = build_complete_product_quality_release_ladder


__all__ = [
    "COMPLETE_PRODUCT_QUALITY_RELEASE_LADDER_VERSION",
    "COMPLETE_PRODUCT_QUALITY_RELEASE_LADDER_STAGE",
    "COMPLETE_PRODUCT_QUALITY_RELEASE_LADDER_STEP",
    "COMPLETE_PRODUCT_QUALITY_RELEASE_LADDER_IMPLEMENTATION_UNIT",
    "COMPLETE_PRODUCT_QUALITY_RELEASE_LADDER_CRITERIA_VERSION",
    "COMPLETE_PRODUCT_QUALITY_RELEASE_LADDER_GUARD_VERSION",
    "COMPLETE_RELEASE_LADDER_STAGES",
    "build_complete_product_quality_release_ladder_criteria",
    "build_complete_product_quality_release_ladder",
    "build_complete_product_quality_release_ladder_guard",
    "build_complete_product_quality_release_ladder_report",
]
