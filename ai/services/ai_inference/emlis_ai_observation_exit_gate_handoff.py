# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 14 Exit Gate / Handoff for EmlisAI observation replies.

Step 14 is the final observation-reply handoff boundary for this implementation
order.  It verifies that Step12 Scorecard / Blind QA and Step13 Regression
Fixture Coverage satisfy the product-quality thresholds, records rollback
conditions, and exposes a meta-only handoff package.  It deliberately does not
change public response shape, RN display contracts, API routes, DB physical
names, Display Gate policy, or public release state.
"""

import json
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Final

from emlis_ai_observation_scorecard_blind_qa import (
    OBSERVATION_ALWAYS_DISPLAY_TARGET,
    OBSERVATION_ELIGIBLE_REPLY_TARGET,
    OBSERVATION_LOW_INFO_REPLY_TARGET,
    OBSERVATION_SCORECARD_BLIND_QA_STEP,
    OBSERVATION_SCORECARD_BLIND_QA_VERSION,
    build_observation_scorecard_blind_qa,
    normalize_observation_scorecard_blind_qa_to_scorecard_fields,
)
from emlis_ai_observation_regression_fixture_coverage import (
    OBSERVATION_REGRESSION_FIXTURE_COVERAGE_STEP,
    OBSERVATION_REGRESSION_FIXTURE_COVERAGE_VERSION,
    build_observation_regression_fixture_coverage,
    normalize_observation_regression_fixture_coverage_to_scorecard_fields,
)

OBSERVATION_EXIT_GATE_HANDOFF_VERSION: Final = "emlis.observation_exit_gate_handoff.v1"
OBSERVATION_EXIT_GATE_HANDOFF_STEP: Final = "Step14_Exit_Gate_Handoff"
OBSERVATION_EXIT_GATE_HANDOFF_SOURCE: Final = "emlis_observation_reply_step14_exit_gate_handoff"
OBSERVATION_EXIT_GATE_HANDOFF_TARGET_STEP: Final = "ObservationReply_ProductQuality_Handoff"

OBSERVATION_EXIT_GATE_REQUIRED_CHECKS: tuple[str, ...] = (
    "observation_scorecard_ready",
    "observation_blind_qa_ready",
    "step13_regression_fixture_coverage_ready",
    "always_display_rate_target_met",
    "eligible_observation_rate_target_met",
    "low_info_observation_rate_target_met",
    "false_eligible_zero",
    "free_user_fact_violation_zero",
    "blind_qa_fatal_zero",
    "public_contract_unchanged",
    "api_route_unchanged",
    "db_physical_name_unchanged",
    "rn_public_contract_unchanged",
    "display_gate_not_relaxed",
    "fixed_fallback_not_used",
    "external_ai_not_used",
    "product_release_closed",
)

_FORBIDDEN_TEXT_PAYLOAD_KEYS: frozenset[str] = frozenset(
    {
        "raw_input",
        "rawInput",
        "raw_text",
        "rawText",
        "source_text",
        "sourceText",
        "input",
        "input_text",
        "inputText",
        "user_input",
        "userInput",
        "memo",
        "memo_text",
        "memoText",
        "current_input",
        "currentInput",
        "comment_text",
        "commentText",
        "input_feedback_comment",
        "inputFeedbackComment",
        "public_comment_text",
        "candidate_comment_text",
        "reply_text",
        "replyText",
        "surface_text",
        "realized_text",
        "body",
        "text",
    }
)

_PUBLIC_CONTRACT_FLAGS: tuple[str, ...] = (
    "public_status_extended",
    "observation_status_enum_extended",
    "response_shape_changed",
    "public_response_key_change",
    "api_route_changed",
    "db_physical_name_changed",
    "rn_visible_contract_changed",
    "rn_visible_title_changed",
    "rn_public_contract_changed",
)
_GATE_RELAXATION_FLAGS: tuple[str, ...] = (
    "display_gate_relaxed",
    "grounding_gate_relaxed",
    "template_gate_relaxed",
    "reader_gate_relaxed",
    "gate_relaxed",
)
_RELEASE_APPLIED_FLAGS: tuple[str, ...] = (
    "product_gate_ready",
    "product_gate_reached",
    "product_gate_achieved",
    "product_gate_public_release_applied",
    "public_release_applied",
    "product_quality_released",
)
_FORBIDDEN_RUNTIME_FLAGS: tuple[str, ...] = (
    "fixed_fallback_used",
    "fixed_sentence_template_used",
    "external_ai_used",
    "local_llm_used",
    "raw_input_included",
    "raw_text_included",
    "comment_text_included",
    "comment_text_body_included",
)

ROLLBACK_CONDITION_IDS: tuple[str, ...] = (
    "always_display_rate_below_100_percent",
    "eligible_observation_rate_below_90_percent",
    "low_info_observation_rate_below_100_percent",
    "false_eligible_detected",
    "free_user_fact_violation_detected",
    "blind_qa_fatal_detected",
    "public_contract_changed",
    "api_route_changed",
    "db_physical_name_changed",
    "rn_public_contract_changed",
    "display_gate_relaxed",
    "fixed_fallback_used",
    "external_ai_or_local_llm_used",
)


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).strip()


def _safe_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, (tuple, set)):
        return list(value)
    return [value]


def _dedupe(values: Iterable[Any] | Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in _listify(values):
        text = _clean(item)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _contains_forbidden_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in _FORBIDDEN_TEXT_PAYLOAD_KEYS:
                return True
            if _contains_forbidden_text_payload_key(item):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_text_payload_key(item) for item in value)
    return False


def assert_observation_exit_gate_handoff_meta_only(
    value: Mapping[str, Any] | None,
    *,
    source: str = "observation_exit_gate_handoff",
) -> None:
    """Reject raw input/comment bodies and public side effects in Step14 outputs."""

    data = _safe_mapping(value)
    if _contains_forbidden_text_payload_key(data):
        raise ValueError(f"{source} must stay meta-only and must not include raw input or comment_text bodies")
    for flag in _FORBIDDEN_RUNTIME_FLAGS:
        if data.get(flag) is True:
            raise ValueError(f"{source} violates Step14 meta-only contract: {flag}=true")
    for flag in _RELEASE_APPLIED_FLAGS:
        if data.get(flag) is True:
            raise ValueError(f"{source} must not apply public release or declare Product Gate: {flag}=true")


def _true_flags(source: Mapping[str, Any], flags: Sequence[str]) -> list[str]:
    return [flag for flag in flags if source.get(flag) is True]


def _extract_scorecard(
    *,
    scorecard: Mapping[str, Any] | None = None,
    events: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
    scorecard_events: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
    blind_qa_reviews: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
    run_id: str = "",
) -> dict[str, Any]:
    data = _safe_mapping(scorecard)
    if data:
        if _contains_forbidden_text_payload_key(data):
            raise ValueError("Step14 scorecard source must be meta-only")
        return data
    return build_observation_scorecard_blind_qa(
        events=events,
        scorecard_events=scorecard_events,
        blind_qa_reviews=blind_qa_reviews,
        run_id=run_id,
    )


def _scorecard_fields(scorecard: Mapping[str, Any]) -> dict[str, Any]:
    fields = normalize_observation_scorecard_blind_qa_to_scorecard_fields(scorecard)
    return {**fields, **_safe_mapping(scorecard)}


def _regression_coverage(
    scorecard: Mapping[str, Any],
    regression_fixture_coverage: Mapping[str, Any] | None,
) -> dict[str, Any]:
    explicit = _safe_mapping(regression_fixture_coverage)
    if explicit:
        if _contains_forbidden_text_payload_key(explicit):
            raise ValueError("Step14 regression fixture coverage source must be meta-only")
        return explicit
    for key in (
        "step13_observation_regression_fixture_coverage",
        "step13_regression_fixture_coverage",
        "observation_regression_fixture_coverage",
    ):
        nested = _safe_mapping(scorecard.get(key))
        if nested:
            return nested
    return build_observation_regression_fixture_coverage(scorecard_events=[])


def _regression_fields(coverage: Mapping[str, Any]) -> dict[str, Any]:
    fields = normalize_observation_regression_fixture_coverage_to_scorecard_fields(coverage)
    return {**fields, **_safe_mapping(coverage)}


def build_observation_exit_gate_rollback_conditions() -> list[dict[str, Any]]:
    """Return the fixed rollback condition catalog for Step14 handoff."""

    return [
        {
            "condition_id": "always_display_rate_below_100_percent",
            "trigger_signal": "always_display_rate < 1.0 for normal observation fixtures",
            "rollback_target": "Step10_Display_Repair_Integration",
        },
        {
            "condition_id": "eligible_observation_rate_below_90_percent",
            "trigger_signal": "eligible_observation_rate < 0.90",
            "rollback_target": "Step2_Eligibility_Router_or_Eligible_Surface",
        },
        {
            "condition_id": "low_info_observation_rate_below_100_percent",
            "trigger_signal": "low_info_observation_rate < 1.0",
            "rollback_target": "Step8_Low_Information_Composer_or_Step10_Display_Integration",
        },
        {
            "condition_id": "false_eligible_detected",
            "trigger_signal": "false_eligible_count > 0 or false_eligible_rate > 0",
            "rollback_target": "Step2_Eligibility_Router_and_Step3_User_Fact_Boundary",
        },
        {
            "condition_id": "free_user_fact_violation_detected",
            "trigger_signal": "free_user_fact_violation_count > 0",
            "rollback_target": "Step3_User_Fact_Grounding_Boundary",
        },
        {
            "condition_id": "blind_qa_fatal_detected",
            "trigger_signal": "Blind QA red/fatal dimension count > 0",
            "rollback_target": "Step12_Blind_QA_and_Surface_Realizer",
        },
        {
            "condition_id": "public_contract_changed",
            "trigger_signal": "public status enum or response shape changed",
            "rollback_target": "Step11_RN_Optional_Meta_Contract",
        },
        {
            "condition_id": "api_route_changed",
            "trigger_signal": "api_route_changed=true",
            "rollback_target": "Public_API_Contract",
        },
        {
            "condition_id": "db_physical_name_changed",
            "trigger_signal": "db_physical_name_changed=true",
            "rollback_target": "DB_Physical_Contract",
        },
        {
            "condition_id": "rn_public_contract_changed",
            "trigger_signal": "RN visible title or visible condition changed",
            "rollback_target": "RN_Display_Contract",
        },
        {
            "condition_id": "display_gate_relaxed",
            "trigger_signal": "Display/Grounding/Template/Reader Gate relaxed",
            "rollback_target": "Display_Gate_and_Repair_Integration",
        },
        {
            "condition_id": "fixed_fallback_used",
            "trigger_signal": "fixed fallback or fixed completed sentence template used",
            "rollback_target": "Observation_Dictionary_and_Surface_Realizer",
        },
        {
            "condition_id": "external_ai_or_local_llm_used",
            "trigger_signal": "external_ai_used=true or local_llm_used=true",
            "rollback_target": "Runtime_AI_Boundary",
        },
    ]


def _blind_qa_fatal_count(scorecard: Mapping[str, Any]) -> int:
    blind_qa = _safe_mapping(scorecard.get("blind_qa") or scorecard.get("blind_qa_metrics"))
    return max(
        _as_int(scorecard.get("blind_qa_fatal_count"), 0),
        _as_int(scorecard.get("fatal_count"), 0),
        _as_int(scorecard.get("fatal_review_count"), 0),
        _as_int(blind_qa.get("fatal_count"), 0),
        _as_int(blind_qa.get("fatal_review_count"), 0),
        _as_int(blind_qa.get("red_review_count"), 0),
        _as_int(blind_qa.get("red_dimension_count"), 0),
    )


def _release_blockers_from_metrics(
    *,
    scorecard: Mapping[str, Any],
    scorecard_fields: Mapping[str, Any],
    regression_coverage: Mapping[str, Any],
    regression_fields: Mapping[str, Any],
    contract_observations: Mapping[str, Any],
) -> tuple[list[str], dict[str, bool], list[str]]:
    always_display_rate = _as_float(scorecard_fields.get("always_display_rate"), 0.0)
    eligible_rate = _as_float(scorecard_fields.get("eligible_observation_rate"), 0.0)
    low_info_rate = _as_float(scorecard_fields.get("low_info_observation_rate"), 0.0)
    false_eligible_count = _as_int(scorecard_fields.get("false_eligible_count"), _as_int(scorecard.get("false_eligible_count"), 0))
    false_eligible_rate = _as_float(scorecard_fields.get("false_eligible_rate"), 0.0)
    free_violation_count = _as_int(scorecard_fields.get("free_user_fact_violation_count"), 0)
    fatal_count = _blind_qa_fatal_count(scorecard)

    normal_input_count = _as_int(scorecard.get("normal_input_count"), 0)
    eligible_expected_count = _as_int(scorecard.get("eligible_expected_count"), 0)
    low_info_expected_count = _as_int(scorecard.get("low_info_expected_count"), 0)

    public_contract_violations = _true_flags(contract_observations, _PUBLIC_CONTRACT_FLAGS) + _true_flags(scorecard, _PUBLIC_CONTRACT_FLAGS)
    gate_relaxation_violations = _true_flags(contract_observations, _GATE_RELAXATION_FLAGS) + _true_flags(scorecard, _GATE_RELAXATION_FLAGS)
    fallback_violations = _true_flags(contract_observations, ("fixed_fallback_used", "fixed_sentence_template_used")) + _true_flags(scorecard, ("fixed_fallback_used", "fixed_sentence_template_used"))
    external_ai_violations = _true_flags(contract_observations, ("external_ai_used", "local_llm_used")) + _true_flags(scorecard, ("external_ai_used", "local_llm_used"))
    release_violations = _true_flags(contract_observations, _RELEASE_APPLIED_FLAGS) + _true_flags(scorecard, _RELEASE_APPLIED_FLAGS)

    checks = {
        "observation_scorecard_ready": bool(scorecard.get("observation_scorecard_ready") or scorecard.get("scorecard_ready") or scorecard.get("step12_observation_scorecard_ready")),
        "observation_blind_qa_ready": bool(scorecard.get("observation_blind_qa_ready") or _safe_mapping(scorecard.get("blind_qa")).get("blind_qa_ready")),
        "step13_regression_fixture_coverage_ready": bool(regression_coverage.get("step13_regression_fixture_coverage_ready") or regression_fields.get("step13_regression_fixture_coverage_ready")),
        "always_display_rate_target_met": bool(normal_input_count > 0 and always_display_rate >= OBSERVATION_ALWAYS_DISPLAY_TARGET),
        "eligible_observation_rate_target_met": bool(eligible_expected_count > 0 and eligible_rate >= OBSERVATION_ELIGIBLE_REPLY_TARGET),
        "low_info_observation_rate_target_met": bool(low_info_expected_count > 0 and low_info_rate >= OBSERVATION_LOW_INFO_REPLY_TARGET),
        "false_eligible_zero": bool(false_eligible_count == 0 and false_eligible_rate == 0.0),
        "free_user_fact_violation_zero": bool(free_violation_count == 0),
        "blind_qa_fatal_zero": bool(fatal_count == 0),
        "public_contract_unchanged": not public_contract_violations,
        "api_route_unchanged": "api_route_changed" not in public_contract_violations,
        "db_physical_name_unchanged": "db_physical_name_changed" not in public_contract_violations,
        "rn_public_contract_unchanged": not any(flag in public_contract_violations for flag in ("rn_visible_contract_changed", "rn_visible_title_changed", "rn_public_contract_changed")),
        "display_gate_not_relaxed": not gate_relaxation_violations,
        "fixed_fallback_not_used": not fallback_violations,
        "external_ai_not_used": not external_ai_violations,
        "product_release_closed": not release_violations,
    }

    blockers: list[str] = []
    for check, ok in checks.items():
        if ok is not True:
            blockers.append(check)
    blockers.extend(_dedupe(scorecard.get("release_blockers")))
    blockers.extend(_dedupe(regression_coverage.get("release_blockers")))
    blockers.extend(_dedupe(regression_fields.get("observation_regression_fixture_release_blockers")))
    blockers.extend([f"public_contract_changed:{flag}" for flag in _dedupe(public_contract_violations)])
    blockers.extend([f"gate_relaxed:{flag}" for flag in _dedupe(gate_relaxation_violations)])
    blockers.extend([f"fallback_violation:{flag}" for flag in _dedupe(fallback_violations)])
    blockers.extend([f"runtime_ai_boundary_violation:{flag}" for flag in _dedupe(external_ai_violations)])
    blockers.extend([f"public_release_side_effect:{flag}" for flag in _dedupe(release_violations)])

    rollback_triggered: list[str] = []
    if not checks["always_display_rate_target_met"]:
        rollback_triggered.append("always_display_rate_below_100_percent")
    if not checks["eligible_observation_rate_target_met"]:
        rollback_triggered.append("eligible_observation_rate_below_90_percent")
    if not checks["low_info_observation_rate_target_met"]:
        rollback_triggered.append("low_info_observation_rate_below_100_percent")
    if not checks["false_eligible_zero"]:
        rollback_triggered.append("false_eligible_detected")
    if not checks["free_user_fact_violation_zero"]:
        rollback_triggered.append("free_user_fact_violation_detected")
    if not checks["blind_qa_fatal_zero"]:
        rollback_triggered.append("blind_qa_fatal_detected")
    if not checks["public_contract_unchanged"]:
        rollback_triggered.append("public_contract_changed")
    if not checks["api_route_unchanged"]:
        rollback_triggered.append("api_route_changed")
    if not checks["db_physical_name_unchanged"]:
        rollback_triggered.append("db_physical_name_changed")
    if not checks["rn_public_contract_unchanged"]:
        rollback_triggered.append("rn_public_contract_changed")
    if not checks["display_gate_not_relaxed"]:
        rollback_triggered.append("display_gate_relaxed")
    if not checks["fixed_fallback_not_used"]:
        rollback_triggered.append("fixed_fallback_used")
    if not checks["external_ai_not_used"]:
        rollback_triggered.append("external_ai_or_local_llm_used")
    return _dedupe(blockers), checks, _dedupe(rollback_triggered)


def build_observation_exit_gate_handoff(
    *,
    scorecard: Mapping[str, Any] | None = None,
    events: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
    scorecard_events: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
    blind_qa_reviews: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
    regression_fixture_coverage: Mapping[str, Any] | None = None,
    contract_observations: Mapping[str, Any] | None = None,
    run_id: str = "",
) -> dict[str, Any]:
    """Build the Step14 meta-only exit gate and handoff summary."""

    contract_data = _safe_mapping(contract_observations)
    if _contains_forbidden_text_payload_key(contract_data):
        raise ValueError("Step14 contract observations must not include raw input or comment_text bodies")
    scorecard_data = _extract_scorecard(
        scorecard=scorecard,
        events=events,
        scorecard_events=scorecard_events,
        blind_qa_reviews=blind_qa_reviews,
        run_id=run_id,
    )
    scorecard_fields = _scorecard_fields(scorecard_data)
    coverage = _regression_coverage(scorecard_data, regression_fixture_coverage)
    coverage_fields = _regression_fields(coverage)
    release_blockers, checks, rollback_triggered = _release_blockers_from_metrics(
        scorecard=scorecard_data,
        scorecard_fields=scorecard_fields,
        regression_coverage=coverage,
        regression_fields=coverage_fields,
        contract_observations=contract_data,
    )
    handoff_ready = not release_blockers and all(checks.get(check) is True for check in OBSERVATION_EXIT_GATE_REQUIRED_CHECKS)

    metrics = {
        "always_display_rate": _as_float(scorecard_fields.get("always_display_rate"), 0.0),
        "eligible_observation_rate": _as_float(scorecard_fields.get("eligible_observation_rate"), 0.0),
        "low_info_observation_rate": _as_float(scorecard_fields.get("low_info_observation_rate"), 0.0),
        "false_eligible_rate": _as_float(scorecard_fields.get("false_eligible_rate"), 0.0),
        "false_eligible_count": _as_int(scorecard_fields.get("false_eligible_count"), _as_int(scorecard_data.get("false_eligible_count"), 0)),
        "free_user_fact_violation_count": _as_int(scorecard_fields.get("free_user_fact_violation_count"), 0),
        "blind_qa_fatal_count": _blind_qa_fatal_count(scorecard_data),
        "read_feeling_score": scorecard_data.get("read_feeling_score") or scorecard_fields.get("observation_read_feeling_score"),
        "regression_fixture_coverage_rate": coverage_fields.get("observation_regression_fixture_coverage_rate") or coverage.get("fixture_coverage_rate"),
        "regression_fixture_success_coverage_rate": coverage_fields.get("observation_regression_fixture_success_coverage_rate") or coverage.get("fixture_success_coverage_rate"),
    }

    summary = {
        "version": OBSERVATION_EXIT_GATE_HANDOFF_VERSION,
        "schema_version": OBSERVATION_EXIT_GATE_HANDOFF_VERSION,
        "source": OBSERVATION_EXIT_GATE_HANDOFF_SOURCE,
        "source_step": OBSERVATION_EXIT_GATE_HANDOFF_STEP,
        "step": OBSERVATION_EXIT_GATE_HANDOFF_STEP,
        "target_step": OBSERVATION_EXIT_GATE_HANDOFF_TARGET_STEP,
        "run_id": _clean(run_id) or _clean(scorecard_data.get("run_id")),
        "handoff_only": True,
        "observation_exit_gate_handoff_connected": True,
        "observation_exit_gate_handoff_ready": handoff_ready,
        "step14_observation_exit_gate_handoff_ready": handoff_ready,
        "exit_gate_ready": handoff_ready,
        "exit_gate_completed": handoff_ready,
        "handoff_ready": handoff_ready,
        "ready_for_next_observation_reply_handoff": handoff_ready,
        "observation_scorecard_blind_qa_version": OBSERVATION_SCORECARD_BLIND_QA_VERSION,
        "observation_scorecard_blind_qa_step": OBSERVATION_SCORECARD_BLIND_QA_STEP,
        "observation_regression_fixture_coverage_version": OBSERVATION_REGRESSION_FIXTURE_COVERAGE_VERSION,
        "observation_regression_fixture_coverage_step": OBSERVATION_REGRESSION_FIXTURE_COVERAGE_STEP,
        "metrics": metrics,
        "thresholds": {
            "always_display_rate": OBSERVATION_ALWAYS_DISPLAY_TARGET,
            "eligible_observation_rate": OBSERVATION_ELIGIBLE_REPLY_TARGET,
            "low_info_observation_rate": OBSERVATION_LOW_INFO_REPLY_TARGET,
            "false_eligible_count": 0,
            "free_user_fact_violation_count": 0,
            "blind_qa_fatal_count": 0,
            "public_contract_change_count": 0,
        },
        "exit_gate_checks": checks,
        "required_checks": list(OBSERVATION_EXIT_GATE_REQUIRED_CHECKS),
        "release_blockers": release_blockers,
        "exit_gate_blockers": release_blockers,
        "handoff_blockers": release_blockers,
        "rollback_conditions": build_observation_exit_gate_rollback_conditions(),
        "rollback_condition_ids": list(ROLLBACK_CONDITION_IDS),
        "rollback_triggered_conditions": rollback_triggered,
        "rollback_required": bool(rollback_triggered or release_blockers),
        "regression_fixture_coverage_ready": checks.get("step13_regression_fixture_coverage_ready"),
        "regression_fixture_coverage": {
            "ready": checks.get("step13_regression_fixture_coverage_ready"),
            "coverage_rate": metrics["regression_fixture_coverage_rate"],
            "success_coverage_rate": metrics["regression_fixture_success_coverage_rate"],
            "missing_fixture_groups": list(coverage.get("missing_fixture_groups") or coverage_fields.get("observation_regression_missing_fixture_groups") or []),
            "failed_fixture_groups": list(coverage.get("failed_fixture_groups") or coverage_fields.get("observation_regression_failed_fixture_groups") or []),
            "observed_fixture_groups": list(coverage.get("observed_fixture_groups") or coverage_fields.get("observation_regression_observed_fixture_groups") or []),
        },
        "handoff_package": {
            "handoff_scope": "emlis_ai_observation_reply_product_quality",
            "next_work_unit": OBSERVATION_EXIT_GATE_HANDOFF_TARGET_STEP,
            "scorecard_ready": checks.get("observation_scorecard_ready"),
            "blind_qa_ready": checks.get("observation_blind_qa_ready"),
            "regression_fixture_coverage_ready": checks.get("step13_regression_fixture_coverage_ready"),
            "release_decision_required_outside_step14": True,
        },
        "public_contract_unchanged": checks.get("public_contract_unchanged"),
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "public_status_extended": False,
        "observation_status_enum_extended": False,
        "response_shape_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "gate_relaxed": False,
        "fixed_fallback_used": False,
        "fixed_sentence_template_used": False,
        "external_ai_used": False,
        "local_llm_used": False,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "product_gate_achieved": False,
        "product_gate_public_release_applied": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "release_judgment": {
            "release_allowed": False,
            "reason": "step14_observation_exit_gate_handoff_only_public_release_not_applied",
            "handoff_ready": handoff_ready,
            "release_decision_required_outside_step14": True,
        },
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "comment_text_written_by_step14_exit_gate": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "meta_only": True,
    }
    assert_observation_exit_gate_handoff_meta_only(summary)
    return summary


def normalize_observation_exit_gate_handoff_to_scorecard_fields(summary: Mapping[str, Any] | None) -> dict[str, Any]:
    data = _safe_mapping(summary)
    return {
        "observation_exit_gate_handoff_version": data.get("version") or OBSERVATION_EXIT_GATE_HANDOFF_VERSION,
        "observation_exit_gate_handoff_step": data.get("step") or OBSERVATION_EXIT_GATE_HANDOFF_STEP,
        "step14_observation_exit_gate_handoff_ready": bool(data.get("step14_observation_exit_gate_handoff_ready")),
        "observation_exit_gate_handoff_ready": bool(data.get("observation_exit_gate_handoff_ready")),
        "observation_exit_gate_release_blockers": list(data.get("release_blockers") or []),
        "observation_exit_gate_rollback_required": bool(data.get("rollback_required")),
        "observation_exit_gate_rollback_triggered_conditions": list(data.get("rollback_triggered_conditions") or []),
        "observation_exit_gate_public_contract_unchanged": bool(data.get("public_contract_unchanged")),
        "observation_exit_gate_product_gate_ready": False,
        "observation_exit_gate_public_release_applied": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
    }


def dump_observation_exit_gate_handoff(summary: Mapping[str, Any] | None = None) -> str:
    data = dict(summary or build_observation_exit_gate_handoff(scorecard={}))
    data["raw_input_included"] = False
    data["raw_text_included"] = False
    data["comment_text_included"] = False
    data["comment_text_body_included"] = False
    assert_observation_exit_gate_handoff_meta_only(data)
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


build_emlis_ai_observation_exit_gate_handoff = build_observation_exit_gate_handoff
build_observation_reply_exit_gate_handoff = build_observation_exit_gate_handoff
build_observation_exit_gate_rollback_catalog = build_observation_exit_gate_rollback_conditions
assert_observation_reply_exit_gate_handoff_meta_only = assert_observation_exit_gate_handoff_meta_only

__all__ = [
    "OBSERVATION_EXIT_GATE_HANDOFF_VERSION",
    "OBSERVATION_EXIT_GATE_HANDOFF_STEP",
    "OBSERVATION_EXIT_GATE_HANDOFF_SOURCE",
    "OBSERVATION_EXIT_GATE_HANDOFF_TARGET_STEP",
    "OBSERVATION_EXIT_GATE_REQUIRED_CHECKS",
    "ROLLBACK_CONDITION_IDS",
    "assert_observation_exit_gate_handoff_meta_only",
    "assert_observation_reply_exit_gate_handoff_meta_only",
    "build_observation_exit_gate_rollback_conditions",
    "build_observation_exit_gate_rollback_catalog",
    "build_observation_exit_gate_handoff",
    "build_emlis_ai_observation_exit_gate_handoff",
    "build_observation_reply_exit_gate_handoff",
    "normalize_observation_exit_gate_handoff_to_scorecard_fields",
    "dump_observation_exit_gate_handoff",
]
