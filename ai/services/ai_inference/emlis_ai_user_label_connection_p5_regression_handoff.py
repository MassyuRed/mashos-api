# -*- coding: utf-8 -*-
from __future__ import annotations

"""P5-7 regression handoff and P6 hold decision for User Label Connection.

This module is a body-free exit boundary for P5.  It checks whether P5 limited
visible connection is safe enough to keep, whether P4/current-only regressions
remain intact, and whether P6 Structure Insight v2 should remain on hold.  It
does not promote Product QA into release, generate visible text, or change
RN/API/DB/public response contracts.
"""

from collections.abc import Iterable, Mapping, Sequence
import json
from typing import Any, Final

from emlis_ai_user_label_connection_p5_limited_visible_connection import (
    assert_user_label_connection_p5_limited_visible_connection_contract,
    user_label_connection_p5_limited_visible_connection_public_summary,
)
from emlis_ai_user_label_connection_p5_product_quality_review import (
    DIMENSION_CREEPY_ABSENCE,
    DIMENSION_CURRENT_INPUT_NOT_MASKED_BY_HISTORY,
    DIMENSION_OVERCLAIM_ABSENCE,
    DIMENSION_SELF_BLAME_NON_AMPLIFICATION,
    DIMENSION_TARGETS,
    assert_user_label_connection_p5_product_quality_review_contract,
)
from emlis_ai_user_label_connection_p5_safety_guard import (
    assert_user_label_connection_p5_safety_guard_contract,
)


USER_LABEL_CONNECTION_P5_REGRESSION_HANDOFF_SCHEMA_VERSION: Final = (
    "cocolon.emlis.user_label_connection.p5_regression_handoff.v1"
)
USER_LABEL_CONNECTION_P5_REGRESSION_HANDOFF_SUMMARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.user_label_connection.p5_regression_handoff_summary.v1"
)
USER_LABEL_CONNECTION_P5_REGRESSION_SUITE_STATUS_SCHEMA_VERSION: Final = (
    "cocolon.emlis.user_label_connection.p5_regression_suite_status.v1"
)
USER_LABEL_CONNECTION_P5_REGRESSION_HANDOFF_STEP: Final = "P5-7_Regression_P6HoldDecision"
USER_LABEL_CONNECTION_P5_REGRESSION_HANDOFF_SOURCE: Final = (
    "Cocolon_EmlisAI_P5_UserLabelConnection_RegressionP6HoldDecision_20260611"
)

STATUS_PASSED: Final = "passed"
STATUS_FAILED: Final = "failed"
STATUS_TIMEOUT: Final = "timeout"
STATUS_NOT_EXECUTED: Final = "not_executed"
STATUS_BLOCKED: Final = "blocked"

DECISION_P6_READY: Final = "p6_ready"
DECISION_P6_HOLD: Final = "p6_hold"
DECISION_P5_CONTINUE: Final = "p5_continue"
DECISION_P4_RETURN: Final = "p4_return"

P5_7_REQUIRED_REGRESSION_SUITES: Final[tuple[str, ...]] = (
    "user_label_connection_existing_tests",
    "p5_new_tests",
    "p4_regression_handoff_tests",
    "product_readfeel_p4_tests",
    "public_feedback_meta_tests",
    "display_contract_tests",
    "two_stage_reception_e2e",
    "rn_contract_tests",
    "free_tier_boundary_tests",
    "low_information_boundary_tests",
    "no_raw_text_meta_tests",
)
P5_7_OPTIONAL_REGRESSION_SUITES: Final[tuple[str, ...]] = (
    "full_backend_suite",
    "manual_device_smoke",
    "long_running_e2e",
)
P5_7_P4_RETURN_SUITES: Final[frozenset[str]] = frozenset(
    {"p4_regression_handoff_tests", "product_readfeel_p4_tests"}
)
P5_7_P5_CONTINUE_SUITES: Final[frozenset[str]] = frozenset(
    {
        "user_label_connection_existing_tests",
        "p5_new_tests",
        "free_tier_boundary_tests",
        "low_information_boundary_tests",
        "no_raw_text_meta_tests",
    }
)

P6_ALLOWED_TARGET_FAMILIES: Final[frozenset[str]] = frozenset(
    {"structure_question", "long_meaning_arc", "self_understanding_follow"}
)

REASON_REQUIRED_REGRESSION_MISSING: Final = "required_regression_missing"
REASON_REQUIRED_REGRESSION_NOT_GREEN: Final = "required_regression_not_green"
REASON_COMMAND_TIMEOUT: Final = "command_timeout_recorded"
REASON_P5_LIMITED_VISIBLE_CONNECTION_NOT_READY: Final = "p5_limited_visible_connection_not_ready"
REASON_CURRENT_INPUT_MASKED_BY_HISTORY: Final = "current_input_masked_by_history"
REASON_CREEPY_OVERCLAIM_SELF_BLAME_RISK_INCREASED: Final = "creepy_overclaim_self_blame_risk_increased"
REASON_P5_DEEP_INSIGHT_SUBSTITUTE_RISK: Final = "p5_deep_insight_substitute_risk"
REASON_P6_TARGET_FAMILY_MISSING: Final = "p6_target_family_missing"
REASON_P6_TARGET_FAMILY_OUT_OF_SCOPE: Final = "p6_target_family_out_of_scope"
REASON_P4_CURRENT_ONLY_REGRESSION_NOT_PRESERVED: Final = "p4_current_only_regression_not_preserved"
REASON_RAW_TEXT_PAYLOAD_DETECTED: Final = "raw_text_payload_detected"
REASON_CONTRACT_MUTATION_DETECTED: Final = "contract_mutation_detected"
REASON_UPSTREAM_CONTRACT_INVALID: Final = "upstream_contract_invalid"

_TEXT_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
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
        "current_input",
        "currentInput",
        "history_context",
        "historyContext",
        "history_records",
        "historyRecords",
        "history_raw_text",
        "historyRawText",
        "memo",
        "memo_text",
        "memoText",
        "memo_action",
        "memoAction",
        "thought_text",
        "thoughtText",
        "action_text",
        "actionText",
        "comment_text",
        "commentText",
        "comment_text_body",
        "commentTextBody",
        "candidate_body",
        "candidateBody",
        "surface_body",
        "surfaceBody",
        "surface_text",
        "surfaceText",
        "visible_text",
        "visibleText",
        "reply_text",
        "replyText",
        "display_text",
        "displayText",
        "observation_text",
        "reception_text",
        "reviewer_note",
        "reviewer_notes",
        "reviewer_free_text",
        "raw_test_output",
        "test_output",
        "command_output",
        "terminal_output",
        "stdout",
        "stderr",
        "traceback",
        "body",
        "text",
    }
)
_FORBIDDEN_TRUE_FLAGS: Final[frozenset[str]] = frozenset(
    {
        "api_route_changed",
        "request_key_changed",
        "response_shape_changed",
        "public_response_key_added",
        "public_response_key_change",
        "db_schema_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "reader_gate_relaxed",
        "template_gate_relaxed",
        "runtime_surface_gate_relaxed",
        "visible_surface_gate_relaxed",
        "safety_gate_relaxed",
        "gate_relaxed",
        "existing_gate_relaxed",
        "raw_input_included",
        "raw_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "history_raw_text_included",
        "reviewer_free_text_included",
        "raw_test_output_included",
        "command_output_included",
        "terminal_output_included",
        "fixed_sentence_template_added",
        "input_specific_template_added",
        "diagnosis_allowed",
        "personality_claim_allowed",
        "cause_claim_allowed",
        "advice_allowed",
        "future_prediction_allowed",
        "always_claim_allowed",
        "should_statement_allowed",
        "public_release_applied",
        "release_allowed",
        "product_quality_released",
        "machine_metrics_used_for_read_feeling",
        "read_feeling_auto_filled_from_machine_metrics",
        "external_ai_used",
        "local_llm_used",
    }
)


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).replace("\u3000", " ").strip()


def _safe_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    as_meta = getattr(value, "as_meta", None)
    if callable(as_meta):
        meta = as_meta()
        if isinstance(meta, Mapping):
            return {str(key): item for key, item in meta.items()}
    return {}


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        return list(value.values())
    if isinstance(value, list):
        return list(value)
    if isinstance(value, (tuple, set)):
        return list(value)
    if isinstance(value, (str, bytes, bytearray)):
        return [value]
    try:
        return list(value)
    except TypeError:
        return [value]


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    out: list[str] = []
    for value in _listify(values):
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return out


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def _contains_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in _TEXT_PAYLOAD_KEYS:
                return True
            if _contains_text_payload_key(child):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_contains_text_payload_key(child) for child in value)
    return False


def _flag_true(value: Any, names: frozenset[str] = _FORBIDDEN_TRUE_FLAGS) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in names and child is True:
                return True
            if _flag_true(child, names):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_flag_true(child, names) for child in value)
    return False


def _score(value: Any) -> float | None:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return max(0.0, min(1.0, round(float(value), 4)))
    text = _clean(value)
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    if 1.0 < number <= 100.0:
        number = number / 100.0
    return max(0.0, min(1.0, round(number, 4)))


def _contract_invalid(name: str, value: Mapping[str, Any], checker: Any) -> list[str]:
    if not value:
        return []
    try:
        checker(value, allow_partial=True)
    except (TypeError, ValueError):
        return [f"{REASON_UPSTREAM_CONTRACT_INVALID}:{name}"]
    return []


def normalize_user_label_connection_p5_regression_suite_status(
    suite_status: Mapping[str, Any] | None,
    *,
    index: int = 0,
) -> dict[str, Any]:
    if not isinstance(suite_status, Mapping):
        raise TypeError("P5-7 regression suite status must be a mapping")
    assert_user_label_connection_p5_regression_handoff_contract(suite_status, allow_partial=True)
    suite_id = _clean(suite_status.get("suite_id") or suite_status.get("id")) or f"suite-{index:03d}"
    status = _clean(suite_status.get("status")).lower() or STATUS_NOT_EXECUTED
    if status not in {STATUS_PASSED, STATUS_FAILED, STATUS_TIMEOUT, STATUS_NOT_EXECUTED, STATUS_BLOCKED}:
        status = STATUS_NOT_EXECUTED
    required = suite_status.get("required")
    is_required = suite_id in P5_7_REQUIRED_REGRESSION_SUITES if required is None else _bool(required)
    passed_count = _int(suite_status.get("passed_count"), 0)
    failed_count = _int(suite_status.get("failed_count"), 0)
    warning_count = _int(suite_status.get("warning_count"), 0)
    timed_out = status == STATUS_TIMEOUT or suite_status.get("timed_out") is True
    passed = status == STATUS_PASSED and failed_count == 0 and not timed_out
    reason_codes = _dedupe(suite_status.get("reason_codes") or suite_status.get("failure_codes"))
    if timed_out:
        reason_codes.append(REASON_COMMAND_TIMEOUT)
    if status == STATUS_FAILED:
        reason_codes.append("suite_failed")
    if status in {STATUS_NOT_EXECUTED, STATUS_BLOCKED}:
        reason_codes.append(status)
    if is_required and not passed:
        reason_codes.append(REASON_REQUIRED_REGRESSION_NOT_GREEN)
    normalized = {
        "schema_version": USER_LABEL_CONNECTION_P5_REGRESSION_SUITE_STATUS_SCHEMA_VERSION,
        "version": USER_LABEL_CONNECTION_P5_REGRESSION_SUITE_STATUS_SCHEMA_VERSION,
        "source": USER_LABEL_CONNECTION_P5_REGRESSION_HANDOFF_SOURCE,
        "source_step": USER_LABEL_CONNECTION_P5_REGRESSION_HANDOFF_STEP,
        "suite_id": suite_id,
        "status": status,
        "required": is_required,
        "passed": passed,
        "timed_out": timed_out,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "warning_count": warning_count,
        "reason_codes": _dedupe(reason_codes),
        "body_free_suite_status_only": True,
        "local_command_packet_retained": False,
        "local_command_packet_body_retained": False,
        "raw_test_output_included": False,
        "command_output_included": False,
        "terminal_output_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "history_raw_text_included": False,
        "public_response_key_added": False,
        "response_shape_changed": False,
        "rn_visible_contract_changed": False,
        "gate_relaxed": False,
        "public_release_applied": False,
        "release_allowed": False,
    }
    assert_user_label_connection_p5_regression_handoff_contract(normalized, allow_partial=True)
    return normalized


def _required_regression_status(suites: Sequence[Mapping[str, Any]]) -> tuple[bool, list[str], list[str]]:
    by_suite = {_clean(item.get("suite_id")): item for item in suites}
    blockers: list[str] = []
    missing: list[str] = []
    for suite_id in P5_7_REQUIRED_REGRESSION_SUITES:
        item = by_suite.get(suite_id)
        if not item:
            missing.append(suite_id)
            blockers.append(f"{REASON_REQUIRED_REGRESSION_MISSING}:{suite_id}")
            continue
        if item.get("passed") is not True:
            blockers.append(f"{REASON_REQUIRED_REGRESSION_NOT_GREEN}:{suite_id}")
    return not blockers, blockers, missing


def _suite_ids_with_blockers(suites: Sequence[Mapping[str, Any]], suite_ids: frozenset[str]) -> list[str]:
    return [
        _clean(item.get("suite_id"))
        for item in suites
        if _clean(item.get("suite_id")) in suite_ids and item.get("passed") is not True
    ]


def _optional_notes(suites: Sequence[Mapping[str, Any]]) -> list[str]:
    notes: list[str] = []
    for item in suites:
        if item.get("required") is True:
            continue
        suite_id = _clean(item.get("suite_id"))
        if item.get("timed_out") is True:
            notes.append(f"{REASON_COMMAND_TIMEOUT}:{suite_id}")
        elif item.get("passed") is not True and _clean(item.get("status")) != STATUS_NOT_EXECUTED:
            notes.append(f"optional_regression_not_green:{suite_id}")
    return _dedupe(notes)


def _p5_connection_ready(meta: Mapping[str, Any]) -> bool:
    return (
        meta.get("applied") is True
        and meta.get("limited_visible_connection_applied") is True
        and meta.get("p5_visibility_boundary_allowed") is True
        and meta.get("p5_eligibility_connectable") is True
        and meta.get("p5_surface_role_plan_ready") is True
        and meta.get("p5_safety_guard_allowed") is True
        and meta.get("p5_product_quality_allowed") is True
    )


def _current_not_masked(
    *,
    p5_limited_visible_connection: Mapping[str, Any],
    p5_product_quality_review: Mapping[str, Any],
) -> bool:
    connection_shape = _safe_mapping(p5_limited_visible_connection.get("connection_shape"))
    connection_ok = connection_shape.get("current_input_not_masked_by_history") is True
    averages = _safe_mapping(p5_product_quality_review.get("dimension_averages"))
    score = _score(averages.get(DIMENSION_CURRENT_INPUT_NOT_MASKED_BY_HISTORY))
    if score is None:
        return connection_ok
    return connection_ok and score >= DIMENSION_TARGETS[DIMENSION_CURRENT_INPUT_NOT_MASKED_BY_HISTORY]


def _risk_not_increased(
    *,
    p5_safety_guard: Mapping[str, Any],
    p5_product_quality_review: Mapping[str, Any],
) -> bool:
    risks = _safe_mapping(p5_safety_guard.get("risk_summary"))
    if any(value is True for value in risks.values()):
        return False
    averages = _safe_mapping(p5_product_quality_review.get("dimension_averages"))
    for dimension in (
        DIMENSION_CREEPY_ABSENCE,
        DIMENSION_OVERCLAIM_ABSENCE,
        DIMENSION_SELF_BLAME_NON_AMPLIFICATION,
    ):
        score = _score(averages.get(dimension))
        if score is not None and score < DIMENSION_TARGETS[dimension]:
            return False
    return True


def _families_from_sources(
    *,
    p5_limited_visible_connection: Mapping[str, Any],
    p6_candidate_families: Sequence[Any] | None,
    p6_scope_meta: Mapping[str, Any],
) -> list[str]:
    if p6_candidate_families is not None:
        return _dedupe(p6_candidate_families)
    explicit = _dedupe(p6_scope_meta.get("p6_candidate_families") or p6_scope_meta.get("target_families"))
    if explicit:
        return explicit
    phase8 = _safe_mapping(p5_limited_visible_connection.get("phase8_visible_surface_connection"))
    family = _clean(phase8.get("connectable_family"))
    return [family] if family else []


def _p4_current_only_preserved(p4_regression_handoff: Mapping[str, Any]) -> bool:
    if not p4_regression_handoff:
        return True
    summary = _safe_mapping(p4_regression_handoff.get("summary")) or p4_regression_handoff
    if summary.get("p4_return_required") is True:
        return False
    if summary.get("post_p4_current_only_readfeel_minimum_met") is False:
        return False
    if summary.get("p5_visible_surface_strengthened") is True or summary.get("p5_runtime_change_applied") is True:
        return False
    return True


def _public_contract() -> dict[str, bool]:
    return {
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "api_route_changed": False,
        "request_key_changed": False,
        "response_shape_changed": False,
        "public_response_key_added": False,
        "db_schema_changed": False,
        "fixed_sentence_template_added": False,
        "release_allowed": False,
        "public_release_applied": False,
        "product_quality_released": False,
    }


def _body_free_contract() -> dict[str, bool]:
    return {
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "history_raw_text_included": False,
        "reviewer_free_text_included": False,
        "raw_test_output_included": False,
        "command_output_included": False,
        "terminal_output_included": False,
    }


def _decision(
    *,
    p4_return_material: Sequence[str],
    p5_continue_material: Sequence[str],
    p6_hold_material: Sequence[str],
) -> str:
    if p4_return_material:
        return DECISION_P4_RETURN
    if p5_continue_material:
        return DECISION_P5_CONTINUE
    if p6_hold_material:
        return DECISION_P6_HOLD
    return DECISION_P6_READY


def build_user_label_connection_p5_regression_handoff(
    *,
    p5_limited_visible_connection: Mapping[str, Any] | Any | None = None,
    p5_product_quality_review: Mapping[str, Any] | None = None,
    p5_safety_guard: Mapping[str, Any] | None = None,
    p4_regression_handoff: Mapping[str, Any] | None = None,
    regression_suite_statuses: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
    p6_candidate_families: Sequence[Any] | None = None,
    p6_scope_meta: Mapping[str, Any] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Build the body-free P5 regression handoff and P6 hold decision."""

    run = _clean(run_id) or "p5_regression_handoff"
    limited = _safe_mapping(p5_limited_visible_connection)
    quality = _safe_mapping(p5_product_quality_review)
    safety = _safe_mapping(p5_safety_guard)
    p4_handoff = _safe_mapping(p4_regression_handoff)
    p6_scope = _safe_mapping(p6_scope_meta)

    if limited:
        assert_user_label_connection_p5_limited_visible_connection_contract(limited, allow_partial=True)
    if quality:
        assert_user_label_connection_p5_product_quality_review_contract(quality, allow_partial=True)
    if safety:
        assert_user_label_connection_p5_safety_guard_contract(safety, allow_partial=True)

    suites = [
        normalize_user_label_connection_p5_regression_suite_status(item, index=index)
        for index, item in enumerate(list(regression_suite_statuses or []), start=1)
        if isinstance(item, Mapping)
    ]
    all_required_green, regression_blockers, missing_required = _required_regression_status(suites)
    optional_notes = _optional_notes(suites)
    p4_suite_blockers = _suite_ids_with_blockers(suites, P5_7_P4_RETURN_SUITES)
    p5_suite_blockers = _suite_ids_with_blockers(suites, P5_7_P5_CONTINUE_SUITES)

    sources = [limited, quality, safety, p4_handoff, p6_scope, *suites]
    unsafe_payload = any(_contains_text_payload_key(source) for source in sources)
    contract_mutation = any(_flag_true(source) for source in sources)

    p5_connection_ready = _p5_connection_ready(limited)
    current_not_masked = _current_not_masked(
        p5_limited_visible_connection=limited,
        p5_product_quality_review=quality,
    )
    risk_not_increased = _risk_not_increased(
        p5_safety_guard=safety,
        p5_product_quality_review=quality,
    )
    deep_insight_substitute = any(
        source.get("p5_deep_insight_substitute_used") is True
        or source.get("deep_insight_substitute_used") is True
        or source.get("structure_insight_substitute_used") is True
        for source in (limited, quality, safety, p6_scope)
        if isinstance(source, Mapping)
    )
    p6_families = _families_from_sources(
        p5_limited_visible_connection=limited,
        p6_candidate_families=p6_candidate_families,
        p6_scope_meta=p6_scope,
    )
    p6_family_missing = not p6_families
    p6_family_out_of_scope = sorted(set(p6_families) - set(P6_ALLOWED_TARGET_FAMILIES))
    p6_family_scope_limited = bool(p6_families and not p6_family_out_of_scope)
    p4_preserved = _p4_current_only_preserved(p4_handoff)

    p4_return_material: list[str] = []
    p5_continue_material: list[str] = []
    p6_hold_material: list[str] = []
    decision_reasons: list[str] = []

    if unsafe_payload:
        p5_continue_material.append(REASON_RAW_TEXT_PAYLOAD_DETECTED)
    if contract_mutation:
        p5_continue_material.append(REASON_CONTRACT_MUTATION_DETECTED)
    if not p4_preserved:
        p4_return_material.append(REASON_P4_CURRENT_ONLY_REGRESSION_NOT_PRESERVED)
    for suite_id in p4_suite_blockers:
        p4_return_material.append(f"{REASON_REQUIRED_REGRESSION_NOT_GREEN}:{suite_id}")
    if not p5_connection_ready:
        p5_continue_material.append(REASON_P5_LIMITED_VISIBLE_CONNECTION_NOT_READY)
        p5_continue_material.extend(f"p5_limited_visible:{reason}" for reason in _dedupe(limited.get("rejection_reasons")))
    if not current_not_masked:
        p5_continue_material.append(REASON_CURRENT_INPUT_MASKED_BY_HISTORY)
    if not risk_not_increased:
        p5_continue_material.append(REASON_CREEPY_OVERCLAIM_SELF_BLAME_RISK_INCREASED)
    if deep_insight_substitute:
        p5_continue_material.append(REASON_P5_DEEP_INSIGHT_SUBSTITUTE_RISK)
    for suite_id in p5_suite_blockers:
        p5_continue_material.append(f"{REASON_REQUIRED_REGRESSION_NOT_GREEN}:{suite_id}")
    for blocker in regression_blockers:
        suite_id = blocker.split(":", 1)[-1] if ":" in blocker else ""
        if suite_id in P5_7_P4_RETURN_SUITES or suite_id in P5_7_P5_CONTINUE_SUITES:
            continue
        p6_hold_material.append(blocker)
    if missing_required:
        p6_hold_material.extend(f"{REASON_REQUIRED_REGRESSION_MISSING}:{suite_id}" for suite_id in missing_required)
    if p6_family_missing:
        p6_hold_material.append(REASON_P6_TARGET_FAMILY_MISSING)
    if p6_family_out_of_scope:
        p6_hold_material.extend(f"{REASON_P6_TARGET_FAMILY_OUT_OF_SCOPE}:{family}" for family in p6_family_out_of_scope)

    p4_return_material = _dedupe(p4_return_material)
    p5_continue_material = _dedupe(p5_continue_material)
    p6_hold_material = _dedupe(p6_hold_material)
    handoff_decision = _decision(
        p4_return_material=p4_return_material,
        p5_continue_material=p5_continue_material,
        p6_hold_material=p6_hold_material,
    )
    decision_reasons.extend(p4_return_material)
    decision_reasons.extend(p5_continue_material)
    decision_reasons.extend(p6_hold_material)
    decision_reasons = _dedupe(decision_reasons)

    suite_counts = {
        "total": len(suites),
        "required": sum(1 for item in suites if item.get("required") is True),
        "passed": sum(1 for item in suites if item.get("passed") is True),
        "failed": sum(1 for item in suites if item.get("status") == STATUS_FAILED),
        "timeout": sum(1 for item in suites if item.get("timed_out") is True),
        "not_executed": sum(1 for item in suites if item.get("status") == STATUS_NOT_EXECUTED),
    }
    summary = {
        "schema_version": USER_LABEL_CONNECTION_P5_REGRESSION_HANDOFF_SUMMARY_SCHEMA_VERSION,
        "version": USER_LABEL_CONNECTION_P5_REGRESSION_HANDOFF_SUMMARY_SCHEMA_VERSION,
        "source": USER_LABEL_CONNECTION_P5_REGRESSION_HANDOFF_SOURCE,
        "step": USER_LABEL_CONNECTION_P5_REGRESSION_HANDOFF_STEP,
        "run_id": run,
        "p5_regression_handoff_created": True,
        "p5_regression_handoff_only": True,
        "handoff_decision": handoff_decision,
        "p6_ready": handoff_decision == DECISION_P6_READY,
        "p6_hold": handoff_decision == DECISION_P6_HOLD,
        "p5_continue": handoff_decision == DECISION_P5_CONTINUE,
        "p4_return": handoff_decision == DECISION_P4_RETURN,
        "decision_reason_codes": decision_reasons,
        "required_regression_suites": list(P5_7_REQUIRED_REGRESSION_SUITES),
        "optional_regression_ledger_suites": list(P5_7_OPTIONAL_REGRESSION_SUITES),
        "regression_suite_counts": suite_counts,
        "all_required_regression_green": all_required_green,
        "missing_required_regression_suites": missing_required,
        "required_regression_blockers": regression_blockers,
        "non_blocking_regression_notes": optional_notes,
        "p5_limited_visible_connection_ready": p5_connection_ready,
        "p5_limited_visible_connection_applied": limited.get("limited_visible_connection_applied") is True,
        "current_input_not_masked_by_history": current_not_masked,
        "creepy_overclaim_self_blame_risk_not_increased": risk_not_increased,
        "p5_deep_insight_substitute_used": deep_insight_substitute,
        "p6_target_families": p6_families,
        "p6_target_family_scope_limited": p6_family_scope_limited,
        "p6_allowed_target_families": sorted(P6_ALLOWED_TARGET_FAMILIES),
        "p4_current_only_readfeel_preserved": p4_preserved,
        "p4_return_material": p4_return_material,
        "p5_continue_material": p5_continue_material,
        "p6_hold_material": p6_hold_material,
        "recommended_next_action": {
            DECISION_P6_READY: "prepare_p6_structure_insight_v2_design_with_family_scope_limit",
            DECISION_P6_HOLD: "hold_p6_until_regression_and_family_scope_are_green",
            DECISION_P5_CONTINUE: "continue_p5_limited_visible_connection_repair_or_review",
            DECISION_P4_RETURN: "return_to_p4_current_only_readfeel_regression_repair",
        }[handoff_decision],
        "p5_limited_visible_public_summary": user_label_connection_p5_limited_visible_connection_public_summary(limited),
        "ratings_only_payload": True,
        "public_text_payload_excluded": True,
        "body_free_case_references_only": True,
        "body_free_regression_status_only": True,
        "local_command_packet_retained": False,
        "local_command_packet_body_retained": False,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "fixed_sentence_template_added": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "release_allowed": False,
        "public_contract": _public_contract(),
        "body_free": _body_free_contract(),
    }
    payload = {
        "schema_version": USER_LABEL_CONNECTION_P5_REGRESSION_HANDOFF_SCHEMA_VERSION,
        "version": USER_LABEL_CONNECTION_P5_REGRESSION_HANDOFF_SCHEMA_VERSION,
        "source": USER_LABEL_CONNECTION_P5_REGRESSION_HANDOFF_SOURCE,
        "step": USER_LABEL_CONNECTION_P5_REGRESSION_HANDOFF_STEP,
        "run_id": run,
        "summary": summary,
        "regression_suite_statuses": suites,
        "public_summary": {},
        "p5_regression_handoff_created": True,
        "p5_regression_handoff_only": True,
        "ratings_only_payload": True,
        "public_text_payload_excluded": True,
        "body_free_case_references_only": True,
        "body_free_regression_status_only": True,
        "local_command_packet_retained": False,
        "local_command_packet_body_retained": False,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "fixed_sentence_template_added": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "release_allowed": False,
        "public_contract": _public_contract(),
        "body_free": _body_free_contract(),
    }
    payload["public_summary"] = user_label_connection_p5_regression_handoff_public_summary(payload)
    assert_user_label_connection_p5_regression_handoff_contract(payload)
    return payload


def user_label_connection_p5_regression_handoff_public_summary(
    handoff_payload_or_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = _safe_mapping(handoff_payload_or_summary)
    source = _safe_mapping(payload.get("summary")) or payload
    suites = [item for item in _listify(payload.get("regression_suite_statuses")) if isinstance(item, Mapping)]
    summary = {
        "schema_version": USER_LABEL_CONNECTION_P5_REGRESSION_HANDOFF_SUMMARY_SCHEMA_VERSION,
        "version": USER_LABEL_CONNECTION_P5_REGRESSION_HANDOFF_SUMMARY_SCHEMA_VERSION,
        "source": USER_LABEL_CONNECTION_P5_REGRESSION_HANDOFF_SOURCE,
        "step": USER_LABEL_CONNECTION_P5_REGRESSION_HANDOFF_STEP,
        "run_id": _clean(source.get("run_id")),
        "p5_regression_handoff_created": source.get("p5_regression_handoff_created") is True,
        "handoff_decision": _clean(source.get("handoff_decision")) or DECISION_P6_HOLD,
        "p6_ready": source.get("p6_ready") is True,
        "p6_hold": source.get("p6_hold") is True,
        "p5_continue": source.get("p5_continue") is True,
        "p4_return": source.get("p4_return") is True,
        "decision_reason_codes": _dedupe(source.get("decision_reason_codes")),
        "all_required_regression_green": source.get("all_required_regression_green") is True,
        "missing_required_regression_suites": _dedupe(source.get("missing_required_regression_suites")),
        "required_regression_blockers": _dedupe(source.get("required_regression_blockers")),
        "p5_limited_visible_connection_ready": source.get("p5_limited_visible_connection_ready") is True,
        "current_input_not_masked_by_history": source.get("current_input_not_masked_by_history") is True,
        "creepy_overclaim_self_blame_risk_not_increased": source.get("creepy_overclaim_self_blame_risk_not_increased")
        is True,
        "p5_deep_insight_substitute_used": source.get("p5_deep_insight_substitute_used") is True,
        "p6_target_families": _dedupe(source.get("p6_target_families")),
        "p6_target_family_scope_limited": source.get("p6_target_family_scope_limited") is True,
        "p4_current_only_readfeel_preserved": source.get("p4_current_only_readfeel_preserved") is not False,
        "recommended_next_action": _clean(source.get("recommended_next_action")),
        "regression_suite_summary": [
            {
                "suite_id": _clean(item.get("suite_id")),
                "status": _clean(item.get("status")),
                "required": item.get("required") is True,
                "passed": item.get("passed") is True,
                "timed_out": item.get("timed_out") is True,
                "warning_count": _int(item.get("warning_count")),
                "reason_codes": _dedupe(item.get("reason_codes")),
            }
            for item in suites
        ],
        "ratings_only_payload": True,
        "public_text_payload_excluded": True,
        "body_free_case_references_only": True,
        "body_free_regression_status_only": True,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "history_raw_text_included": False,
        "raw_test_output_included": False,
        "command_output_included": False,
        "terminal_output_included": False,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "fixed_sentence_template_added": False,
        "public_response_key_added": False,
        "response_shape_changed": False,
        "rn_visible_contract_changed": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "release_allowed": False,
    }
    assert_user_label_connection_p5_regression_handoff_contract(summary, allow_partial=True)
    return summary


def dump_user_label_connection_p5_regression_handoff_public_summary(
    handoff_payload_or_summary: Mapping[str, Any] | None = None,
) -> str:
    summary = user_label_connection_p5_regression_handoff_public_summary(handoff_payload_or_summary)
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def assert_user_label_connection_p5_regression_handoff_contract(value: Any, *, allow_partial: bool = False) -> None:
    meta = _safe_mapping(value)
    if not meta:
        raise ValueError("P5 regression handoff must be a mapping")
    if _contains_text_payload_key(meta):
        raise ValueError("P5 regression handoff must not include raw/comment/history/test body keys")
    if _flag_true(meta):
        raise ValueError("P5 regression handoff contains a forbidden true flag")
    json.dumps(meta, ensure_ascii=False, sort_keys=True)
    if allow_partial:
        return
    if meta.get("schema_version") != USER_LABEL_CONNECTION_P5_REGRESSION_HANDOFF_SCHEMA_VERSION:
        raise ValueError("unexpected P5 regression handoff schema_version")
    if meta.get("step") != USER_LABEL_CONNECTION_P5_REGRESSION_HANDOFF_STEP:
        raise ValueError("unexpected P5 regression handoff step")
    summary = _safe_mapping(meta.get("summary"))
    if summary.get("schema_version") != USER_LABEL_CONNECTION_P5_REGRESSION_HANDOFF_SUMMARY_SCHEMA_VERSION:
        raise ValueError("unexpected P5 regression handoff summary schema_version")
    if summary.get("handoff_decision") not in {
        DECISION_P6_READY,
        DECISION_P6_HOLD,
        DECISION_P5_CONTINUE,
        DECISION_P4_RETURN,
    }:
        raise ValueError("unexpected P5 regression handoff decision")
    if summary.get("release_allowed") is not False or meta.get("release_allowed") is not False:
        raise ValueError("P5 regression handoff must not allow release")
    for source_name, source in (("payload", meta), ("summary", summary)):
        public_contract = _safe_mapping(source.get("public_contract"))
        body_free = _safe_mapping(source.get("body_free"))
        for key in (
            "rn_visible_contract_changed",
            "rn_visible_title_changed",
            "public_response_key_added",
            "response_shape_changed",
            "api_route_changed",
            "request_key_changed",
            "db_schema_changed",
            "fixed_sentence_template_added",
            "release_allowed",
            "public_release_applied",
            "product_quality_released",
        ):
            if public_contract.get(key) is not False:
                raise ValueError(f"P5 regression {source_name}.public_contract.{key} must be false")
        for key in (
            "raw_input_included",
            "raw_text_included",
            "comment_text_body_included",
            "candidate_body_included",
            "surface_body_included",
            "history_raw_text_included",
            "raw_test_output_included",
            "command_output_included",
            "terminal_output_included",
        ):
            if body_free.get(key) is not False:
                raise ValueError(f"P5 regression {source_name}.body_free.{key} must be false")


__all__ = [
    "USER_LABEL_CONNECTION_P5_REGRESSION_HANDOFF_SCHEMA_VERSION",
    "USER_LABEL_CONNECTION_P5_REGRESSION_HANDOFF_SUMMARY_SCHEMA_VERSION",
    "USER_LABEL_CONNECTION_P5_REGRESSION_SUITE_STATUS_SCHEMA_VERSION",
    "USER_LABEL_CONNECTION_P5_REGRESSION_HANDOFF_STEP",
    "STATUS_PASSED",
    "STATUS_FAILED",
    "STATUS_TIMEOUT",
    "STATUS_NOT_EXECUTED",
    "STATUS_BLOCKED",
    "DECISION_P6_READY",
    "DECISION_P6_HOLD",
    "DECISION_P5_CONTINUE",
    "DECISION_P4_RETURN",
    "P5_7_REQUIRED_REGRESSION_SUITES",
    "P6_ALLOWED_TARGET_FAMILIES",
    "assert_user_label_connection_p5_regression_handoff_contract",
    "normalize_user_label_connection_p5_regression_suite_status",
    "build_user_label_connection_p5_regression_handoff",
    "user_label_connection_p5_regression_handoff_public_summary",
    "dump_user_label_connection_p5_regression_handoff_public_summary",
]
