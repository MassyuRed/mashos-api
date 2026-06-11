# -*- coding: utf-8 -*-
from __future__ import annotations

"""P6-9 regression handoff and P7 hold decision.

This module closes roadmap P6 without treating P6 as release-ready.  It checks
whether P6 preserved P4/P5/RN/public-contract boundaries and classifies the
next action as P7 ready, P7 hold, P6 continue, P5 return, or P4 return.  The
output is body-free and never contains raw input, comment bodies, candidate
bodies, surface bodies, reviewer free text, or terminal output.
"""

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
import json
from typing import Any, Final


STRUCTURE_INSIGHT_P6_REGRESSION_HANDOFF_SCHEMA_VERSION: Final = (
    "cocolon.emlis.structure_insight.p6_regression_handoff.v1"
)
STRUCTURE_INSIGHT_P6_REGRESSION_HANDOFF_SUMMARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.structure_insight.p6_regression_handoff_summary.v1"
)
STRUCTURE_INSIGHT_P6_REGRESSION_HANDOFF_STEP: Final = "P6-9_RegressionP7HoldDecision"
STRUCTURE_INSIGHT_P6_REGRESSION_HANDOFF_SOURCE: Final = (
    "Cocolon_EmlisAI_P6_StructureInsight_RegressionHandoff_20260612"
)

DECISION_P7_READY: Final = "p7_ready"
DECISION_P7_HOLD: Final = "p7_hold"
DECISION_P6_CONTINUE: Final = "p6_continue"
DECISION_P5_RETURN: Final = "p5_return"
DECISION_P4_RETURN: Final = "p4_return"
P6_REGRESSION_HANDOFF_DECISIONS: Final[tuple[str, ...]] = (
    DECISION_P7_READY,
    DECISION_P7_HOLD,
    DECISION_P6_CONTINUE,
    DECISION_P5_RETURN,
    DECISION_P4_RETURN,
)

STATUS_GREEN: Final = "green"
STATUS_RED: Final = "red"
STATUS_NOT_RUN: Final = "not_run"

REQUIRED_SUITE_P6_NEW_TESTS: Final = "p6_new_tests"
REQUIRED_SUITE_STRUCTURE_INSIGHT_EXISTING_TESTS: Final = "structure_insight_existing_tests"
REQUIRED_SUITE_P5_REGRESSION_HANDOFF_TESTS: Final = "p5_regression_handoff_tests"
REQUIRED_SUITE_P5_LIMITED_VISIBLE_CONNECTION_TESTS: Final = "p5_limited_visible_connection_tests"
REQUIRED_SUITE_P5_PRODUCT_QUALITY_REVIEW_TESTS: Final = "p5_product_quality_review_tests"
REQUIRED_SUITE_P4_REGRESSION_HANDOFF_TESTS: Final = "p4_regression_handoff_tests"
REQUIRED_SUITE_PRODUCT_READFEEL_P4_TESTS: Final = "product_readfeel_p4_tests"
REQUIRED_SUITE_PUBLIC_FEEDBACK_META_TESTS: Final = "public_feedback_meta_tests"
REQUIRED_SUITE_DISPLAY_CONTRACT_TESTS: Final = "display_contract_tests"
REQUIRED_SUITE_TWO_STAGE_RECEPTION_E2E: Final = "two_stage_reception_e2e"
REQUIRED_SUITE_RN_CONTRACT_TESTS: Final = "rn_contract_tests"
REQUIRED_SUITE_FREE_TIER_BOUNDARY_TESTS: Final = "free_tier_boundary_tests"
REQUIRED_SUITE_LOW_INFORMATION_BOUNDARY_TESTS: Final = "low_information_boundary_tests"
REQUIRED_SUITE_NO_RAW_TEXT_META_TESTS: Final = "no_raw_text_meta_tests"
REQUIRED_SUITE_NO_CONNECT_FAMILY_REGRESSION: Final = "no_connect_family_regression"

P6_REGRESSION_REQUIRED_SUITES: Final[tuple[str, ...]] = (
    REQUIRED_SUITE_P6_NEW_TESTS,
    REQUIRED_SUITE_STRUCTURE_INSIGHT_EXISTING_TESTS,
    REQUIRED_SUITE_P5_REGRESSION_HANDOFF_TESTS,
    REQUIRED_SUITE_P5_LIMITED_VISIBLE_CONNECTION_TESTS,
    REQUIRED_SUITE_P5_PRODUCT_QUALITY_REVIEW_TESTS,
    REQUIRED_SUITE_P4_REGRESSION_HANDOFF_TESTS,
    REQUIRED_SUITE_PRODUCT_READFEEL_P4_TESTS,
    REQUIRED_SUITE_PUBLIC_FEEDBACK_META_TESTS,
    REQUIRED_SUITE_DISPLAY_CONTRACT_TESTS,
    REQUIRED_SUITE_TWO_STAGE_RECEPTION_E2E,
    REQUIRED_SUITE_RN_CONTRACT_TESTS,
    REQUIRED_SUITE_FREE_TIER_BOUNDARY_TESTS,
    REQUIRED_SUITE_LOW_INFORMATION_BOUNDARY_TESTS,
    REQUIRED_SUITE_NO_RAW_TEXT_META_TESTS,
    REQUIRED_SUITE_NO_CONNECT_FAMILY_REGRESSION,
)
P4_RETURN_SUITES: Final[frozenset[str]] = frozenset(
    {
        REQUIRED_SUITE_P4_REGRESSION_HANDOFF_TESTS,
        REQUIRED_SUITE_PRODUCT_READFEEL_P4_TESTS,
        REQUIRED_SUITE_NO_CONNECT_FAMILY_REGRESSION,
    }
)
P5_RETURN_SUITES: Final[frozenset[str]] = frozenset(
    {
        REQUIRED_SUITE_P5_REGRESSION_HANDOFF_TESTS,
        REQUIRED_SUITE_P5_LIMITED_VISIBLE_CONNECTION_TESTS,
        REQUIRED_SUITE_P5_PRODUCT_QUALITY_REVIEW_TESTS,
    }
)

REASON_P6_ENTRY_NOT_ALLOWED: Final = "p6_entry_not_allowed"
REASON_P6_ENTRY_HOLD: Final = "p6_entry_hold"
REASON_P4_CURRENT_ONLY_REGRESSION_NOT_PRESERVED: Final = "p4_current_only_regression_not_preserved"
REASON_PRODUCT_READFEEL_P4_REGRESSION_NOT_GREEN: Final = "product_readfeel_p4_regression_not_green"
REASON_NO_CONNECT_FAMILY_REGRESSION_NOT_GREEN: Final = "no_connect_family_regression_not_green"
REASON_NO_CONNECT_FAMILY_DEEP_INSIGHT_LEAK: Final = "no_connect_family_deep_insight_leak_detected"
REASON_P5_LIMITED_VISIBLE_CONNECTION_NOT_PRESERVED: Final = "p5_limited_visible_connection_not_preserved"
REASON_CURRENT_INPUT_MASKED_BY_HISTORY_OR_INSIGHT: Final = "current_input_masked_by_history_or_insight"
REASON_CREEPY_RISK_INCREASED: Final = "creepy_risk_increased"
REASON_P6_USED_AS_HISTORY_LINE_SUBSTITUTE: Final = "p6_used_as_history_line_substitute"
REASON_REQUIRED_REGRESSION_SUITE_MISSING: Final = "required_regression_suite_missing"
REASON_REQUIRED_REGRESSION_NOT_EXECUTED: Final = "required_regression_not_executed"
REASON_REQUIRED_REGRESSION_NOT_GREEN: Final = "required_regression_not_green"
REASON_P6_FAMILY_BOUNDARY_NOT_GREEN: Final = "p6_target_family_boundary_not_green"
REASON_P6_RELATION_POLICY_NOT_GREEN: Final = "p6_relation_policy_not_green"
REASON_P6_GATE_HARDENING_NOT_GREEN: Final = "p6_gate_hardening_not_green"
REASON_P6_SURFACE_ROLE_PLAN_NOT_GREEN: Final = "p6_structure_question_surface_role_plan_not_green"
REASON_P6_PRODUCT_QA_READY_CANDIDATE_MISSING: Final = "p6_product_qa_ready_candidate_missing"
REASON_P6_PRODUCT_QA_UNSAFE_CANDIDATE_PRESENT: Final = "p6_product_qa_unsafe_candidate_present"
REASON_P6_PRODUCT_QA_WEAK_CANDIDATE_PRESENT: Final = "p6_product_qa_weak_candidate_present"
REASON_LONG_MEANING_ARC_REVIEW_MISSING: Final = "long_meaning_arc_review_missing"
REASON_SELF_UNDERSTANDING_FOLLOW_REVIEW_MISSING: Final = "self_understanding_follow_review_missing"
REASON_LONG_RUN_SEQUENCE_NOT_EVALUATED: Final = "long_run_sequence_not_evaluated"
REASON_MANUAL_READ_FEEL_NOT_CONFIRMED: Final = "manual_read_feel_not_confirmed"
REASON_PUBLIC_CONTRACT_MUTATION_DETECTED: Final = "public_contract_mutation_detected"
REASON_RAW_TEXT_PAYLOAD_DETECTED: Final = "raw_text_payload_detected"
REASON_COMMENT_TEXT_BODY_DETECTED: Final = "comment_text_body_detected"
REASON_REVIEWER_FREE_TEXT_DETECTED: Final = "reviewer_free_text_detected"
REASON_FIXED_SENTENCE_TEMPLATE_DETECTED: Final = "fixed_sentence_template_detected"
REASON_RELEASE_FLAG_DETECTED: Final = "release_flag_detected"
REASON_BODY_FREE_CONTRACT_NOT_CONFIRMED: Final = "body_free_contract_not_confirmed"

_GREEN_STATUS_VALUES: Final[frozenset[str]] = frozenset({"passed", "pass", "green", "ok", "success"})
_RED_STATUS_VALUES: Final[frozenset[str]] = frozenset({"failed", "fail", "red", "error", "broken"})
_NOT_RUN_STATUS_VALUES: Final[frozenset[str]] = frozenset(
    {"", "not_run", "not-run", "not executed", "not_executed", "pending", "unknown", "skipped"}
)

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
_COMMENT_TEXT_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
    {"comment_text", "commentText", "comment_text_body", "commentTextBody", "candidate_comment_text"}
)
_REVIEWER_FREE_TEXT_KEYS: Final[frozenset[str]] = frozenset(
    {"reviewer_note", "reviewer_notes", "review_notes", "free_text_note", "reviewer_free_text", "blind_qa_free_text"}
)
_PUBLIC_CONTRACT_TRUE_FLAGS: Final[frozenset[str]] = frozenset(
    {
        "api_route_changed",
        "request_key_changed",
        "response_shape_changed",
        "public_response_key_added",
        "public_response_key_change",
        "public_payload_changed",
        "db_schema_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "public_release_applied",
        "product_quality_released",
    }
)
_FIXED_TEMPLATE_TRUE_FLAGS: Final[frozenset[str]] = frozenset(
    {
        "fixed_sentence_template_added",
        "fixed_sentence_template_used",
        "fixed_template_added",
        "fixed_template_used",
        "input_specific_template_added",
        "input_specific_template_used",
        "completed_sentence_template_used",
        "completion_sentence_template_used",
        "role_completed_sentence_template_used",
        "fallback_observation_sentence_added",
    }
)
_FORBIDDEN_TRUE_FLAGS: Final[frozenset[str]] = (
    _PUBLIC_CONTRACT_TRUE_FLAGS
    | _FIXED_TEMPLATE_TRUE_FLAGS
    | frozenset(
        {
            "raw_input_included",
            "raw_text_included",
            "input_text_included",
            "comment_text_included",
            "comment_text_body_included",
            "candidate_body_included",
            "surface_body_included",
            "history_raw_text_included",
            "reviewer_free_text_included",
            "raw_test_output_included",
            "command_output_included",
            "terminal_output_included",
            "comment_text_generated",
            "comment_text_key_written",
            "surface_body_returned",
            "candidate_body_returned",
            "ungated_surface_connected",
            "release_allowed",
            "external_ai_used",
            "local_llm_used",
            "gate_relaxed",
            "display_gate_relaxed",
            "grounding_gate_relaxed",
            "reader_gate_relaxed",
            "template_gate_relaxed",
            "runtime_surface_gate_relaxed",
            "visible_surface_gate_relaxed",
            "safety_gate_relaxed",
            "structure_insight_gate_relaxed",
        }
    )
)


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).replace("\u3000", " ").strip()


def _safe_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
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


def _int(value: Any, *, default: int = 0) -> int:
    if isinstance(value, bool):
        return 1 if value else 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _canonical_id(value: Any) -> str:
    text = _clean(value).lower().replace(" ", "_").replace("-", "_")
    return "".join(ch if ch.isalnum() or ch in "._:" else "_" for ch in text).strip("_")


def _contains_key(value: Any, names: frozenset[str]) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in names:
                return True
            if _contains_key(child, names):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_contains_key(child, names) for child in value)
    return False


def _flag_true(value: Any, names: frozenset[str]) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in names and child is True:
                return True
            if _flag_true(child, names):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_flag_true(child, names) for child in value)
    return False


def _summary(value: Mapping[str, Any] | None) -> dict[str, Any]:
    data = _safe_mapping(value)
    return _safe_mapping(data.get("summary")) or dict(data)


def _public_contract() -> dict[str, bool]:
    return {
        "public_response_key_added": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "response_shape_changed": False,
        "api_route_changed": False,
        "request_key_changed": False,
        "db_schema_changed": False,
        "fixed_sentence_template_added": False,
        "input_specific_template_added": False,
        "release_allowed": False,
        "public_release_applied": False,
        "product_quality_released": False,
    }


def _body_free_contract() -> dict[str, bool]:
    return {
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "history_raw_text_included": False,
        "reviewer_free_text_included": False,
        "raw_test_output_included": False,
        "command_output_included": False,
        "terminal_output_included": False,
    }


def _source_meta_reasons(sources: Iterable[Mapping[str, Any]]) -> list[str]:
    reasons: list[str] = []
    for source in sources:
        if _contains_key(source, _TEXT_PAYLOAD_KEYS):
            reasons.append(REASON_RAW_TEXT_PAYLOAD_DETECTED)
        if _contains_key(source, _COMMENT_TEXT_PAYLOAD_KEYS):
            reasons.append(REASON_COMMENT_TEXT_BODY_DETECTED)
        if _contains_key(source, _REVIEWER_FREE_TEXT_KEYS):
            reasons.append(REASON_REVIEWER_FREE_TEXT_DETECTED)
        if _flag_true(source, _PUBLIC_CONTRACT_TRUE_FLAGS):
            reasons.append(REASON_PUBLIC_CONTRACT_MUTATION_DETECTED)
        if _flag_true(source, _FIXED_TEMPLATE_TRUE_FLAGS):
            reasons.append(REASON_FIXED_SENTENCE_TEMPLATE_DETECTED)
        if _flag_true(source, frozenset({"release_allowed", "public_release_applied", "product_quality_released"})):
            reasons.append(REASON_RELEASE_FLAG_DETECTED)
    return _dedupe(reasons)


def _normalize_regression_status(item: Mapping[str, Any]) -> dict[str, Any]:
    suite_id = _canonical_id(item.get("suite_id") or item.get("id") or item.get("name")) or "unknown_suite"
    raw_status = _clean(item.get("status")).lower()
    failed_count = _int(item.get("failed_count"), default=0)
    passed_count = _int(item.get("passed_count"), default=0)
    passed_flag = item.get("passed") is True or item.get("green") is True
    failed_flag = item.get("passed") is False or item.get("failed") is True or item.get("red") is True
    if passed_flag or (raw_status in _GREEN_STATUS_VALUES and failed_count == 0):
        status = STATUS_GREEN
        passed = True
    elif failed_flag or raw_status in _RED_STATUS_VALUES or failed_count > 0:
        status = STATUS_RED
        passed = False
    else:
        status = STATUS_NOT_RUN
        passed = False
    return {
        "suite_id": suite_id,
        "status": status,
        "passed": passed,
        "failed_count": failed_count,
        "passed_count": passed_count,
        "required": suite_id in P6_REGRESSION_REQUIRED_SUITES,
    }


def _regression_summary(
    statuses: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None,
    *,
    p7_review_meta: Mapping[str, Any],
) -> dict[str, Any]:
    normalized = [
        _normalize_regression_status(item)
        for item in _listify(statuses)
        if isinstance(item, Mapping)
    ]
    by_id = {row["suite_id"]: row for row in normalized}
    missing = [suite for suite in P6_REGRESSION_REQUIRED_SUITES if suite not in by_id]
    not_run = [row["suite_id"] for row in normalized if row["required"] and row["status"] == STATUS_NOT_RUN]
    red = [row["suite_id"] for row in normalized if row["required"] and row["status"] == STATUS_RED]
    explicit_all_green = p7_review_meta.get("all_required_regression_green") is True
    all_required_green = explicit_all_green or (not missing and not not_run and not red)
    no_connect = by_id.get(REQUIRED_SUITE_NO_CONNECT_FAMILY_REGRESSION)
    no_connect_green = (
        p7_review_meta.get("no_connect_family_regression_green") is True
        or (isinstance(no_connect, Mapping) and no_connect.get("status") == STATUS_GREEN)
    )
    no_connect_failed = isinstance(no_connect, Mapping) and no_connect.get("status") == STATUS_RED
    return {
        "normalized_statuses": normalized,
        "status_counts": dict(Counter(row["status"] for row in normalized)),
        "all_required_regression_green": all_required_green,
        "required_regression_missing_suites": missing,
        "required_regression_not_executed_suites": not_run,
        "required_regression_red_suites": red,
        "no_connect_family_regression_green": no_connect_green,
        "no_connect_family_regression_failed": no_connect_failed,
    }


def _source_reasons(*sources: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    for source in sources:
        data = _summary(source)
        reasons.extend(_dedupe(data.get("decision_reason_codes")))
        reasons.extend(_dedupe(data.get("blocker_reason_codes")))
        reasons.extend(_dedupe(data.get("safe_reason_codes")))
    return _dedupe(reasons)


def _entry_state(entry_freeze: Mapping[str, Any]) -> dict[str, bool]:
    data = _summary(entry_freeze)
    decision = _clean(data.get("handoff_decision"))
    return {
        "entry_allowed": data.get("p6_entry_allowed") is True or decision == "p6_entry_allowed",
        "entry_hold": data.get("p6_entry_hold") is True or decision == "p6_entry_hold",
        "p5_return": data.get("p5_return_required") is True or decision == "p5_return_required",
        "p4_return": data.get("p4_return_required") is True or decision == "p4_return_required",
        "p4_preserved": data.get("p4_current_only_readfeel_preserved") is not False,
        "p5_ready": data.get("p5_limited_visible_connection_ready") is True,
        "current_not_masked": data.get("current_input_not_masked_by_history") is True,
        "risk_not_increased": data.get("creepy_overclaim_self_blame_risk_not_increased") is True,
        "deep_insight_substitute": data.get("p5_deep_insight_substitute_used") is True,
    }


def _family_boundary_green(value: Mapping[str, Any]) -> bool:
    data = _summary(value)
    return (
        data.get("allow_limited_surface") is True
        or data.get("limited_surface_candidate") is True
        or _clean(data.get("decision")) == "allow_limited_surface"
    ) and data.get("block") is not True and data.get("hold") is not True


def _relation_policy_green(value: Mapping[str, Any]) -> bool:
    data = _summary(value)
    visibility = _clean(data.get("visibility_decision"))
    return visibility in {"allow_initial_visible", "review_required", "meta_only"} and data.get("blocked") is not True


def _relation_initial_visible(value: Mapping[str, Any]) -> bool:
    data = _summary(value)
    return data.get("allow_initial_visible") is True or _clean(data.get("visibility_decision")) == "allow_initial_visible"


def _gate_green(value: Mapping[str, Any]) -> bool:
    data = _summary(value)
    return data.get("passed") is True and data.get("blocked") is not True


def _surface_plan_green(value: Mapping[str, Any]) -> bool:
    data = _summary(value)
    planned_seed_count = _int(data.get("planned_insight_seed_count"), default=0)
    return (
        data.get("limited_surface_candidate") is True
        and data.get("gate_passed") is True
        and planned_seed_count <= 1
        and _clean(data.get("surface_plan_kind")) == "limited_structure_insight_seed"
    )


def _product_quality_state(value: Mapping[str, Any]) -> dict[str, Any]:
    data = _summary(value)
    ready_count = _int(data.get("structure_insight_ready_candidate_count"), default=0)
    unsafe_count = _int(data.get("unsafe_candidate_count"), default=0)
    weak_count = _int(data.get("weak_candidate_count"), default=0)
    review_count = _int(data.get("review_count"), default=0)
    p7_field_count = _int(data.get("p7_long_run_field_candidate_count"), default=0)
    return {
        "review_count": review_count,
        "ready_count": ready_count,
        "unsafe_count": unsafe_count,
        "weak_count": weak_count,
        "p7_field_count": p7_field_count,
        "ready_candidate_present": ready_count > 0 and p7_field_count > 0,
        "safe_for_p7_material": unsafe_count == 0,
        "p7_long_run_field_candidates": list(data.get("p7_long_run_field_candidates") or []),
    }


def _family_review_flags(
    *,
    p6_family_review: Mapping[str, Any],
    p6_product_quality_review: Mapping[str, Any],
    p7_review_meta: Mapping[str, Any],
) -> dict[str, bool]:
    product = _safe_mapping(p6_product_quality_review)
    rows = [row for row in _listify(product.get("rows")) if isinstance(row, Mapping)]
    row_families = {_canonical_id(row.get("family")) for row in rows}
    family_summary = _summary(p6_family_review)
    reviewed_family = _canonical_id(family_summary.get("family"))
    target_families = {_canonical_id(item) for item in _listify(p7_review_meta.get("family_review_targets_evaluated"))}
    long_reviewed = (
        p7_review_meta.get("long_meaning_arc_reviewed") is True
        or reviewed_family == "long_meaning_arc"
        or "long_meaning_arc" in row_families
        or "long_meaning_arc" in target_families
    )
    self_reviewed = (
        p7_review_meta.get("self_understanding_follow_reviewed") is True
        or reviewed_family == "self_understanding_follow"
        or "self_understanding_follow" in row_families
        or "self_understanding_follow" in target_families
    )
    return {
        "long_meaning_arc_reviewed": long_reviewed,
        "self_understanding_follow_reviewed": self_reviewed,
    }


def _bool_from_meta_or_status(
    *,
    p7_review_meta: Mapping[str, Any],
    regression_summary: Mapping[str, Any],
    field_name: str,
    suite_id: str,
) -> bool:
    if field_name in p7_review_meta:
        return p7_review_meta.get(field_name) is True
    for row in _listify(regression_summary.get("normalized_statuses")):
        if isinstance(row, Mapping) and row.get("suite_id") == suite_id:
            return row.get("status") == STATUS_GREEN
    return False


def _decision(
    *,
    p4_return_material: Sequence[str],
    p5_return_material: Sequence[str],
    p6_continue_material: Sequence[str],
    p7_hold_material: Sequence[str],
) -> str:
    if p4_return_material:
        return DECISION_P4_RETURN
    if p5_return_material:
        return DECISION_P5_RETURN
    if p6_continue_material:
        return DECISION_P6_CONTINUE
    if p7_hold_material:
        return DECISION_P7_HOLD
    return DECISION_P7_READY


def build_structure_insight_p6_regression_handoff(
    *,
    p6_entry_freeze: Mapping[str, Any] | None = None,
    p6_family_boundary: Mapping[str, Any] | None = None,
    p6_relation_policy: Mapping[str, Any] | None = None,
    p6_gate_hardening: Mapping[str, Any] | None = None,
    p6_surface_role_plan: Mapping[str, Any] | None = None,
    p6_family_review: Mapping[str, Any] | None = None,
    p6_product_quality_review: Mapping[str, Any] | None = None,
    regression_statuses: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None = None,
    p7_review_meta: Mapping[str, Any] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Build a body-free P6-9 regression and P7 hold decision report."""

    run = _clean(run_id) or "p6_regression_handoff"
    entry = _safe_mapping(p6_entry_freeze)
    family_boundary = _safe_mapping(p6_family_boundary)
    relation_policy = _safe_mapping(p6_relation_policy)
    gate_hardening = _safe_mapping(p6_gate_hardening)
    surface_role_plan = _safe_mapping(p6_surface_role_plan)
    family_review = _safe_mapping(p6_family_review)
    product_quality = _safe_mapping(p6_product_quality_review)
    review_meta = _safe_mapping(p7_review_meta)
    sources = [entry, family_boundary, relation_policy, gate_hardening, surface_role_plan, family_review, product_quality, review_meta]

    meta_reasons = _source_meta_reasons(sources)
    regression = _regression_summary(regression_statuses, p7_review_meta=review_meta)
    entry_state = _entry_state(entry)
    family_green = review_meta.get("p6_target_family_boundary_green") is True or _family_boundary_green(family_boundary)
    relation_green = review_meta.get("p6_relation_policy_green") is True or _relation_policy_green(relation_policy)
    relation_initial_visible = review_meta.get("p6_relation_policy_initial_visible") is True or _relation_initial_visible(
        relation_policy
    )
    gate_green = review_meta.get("p6_gate_hardening_green") is True or _gate_green(gate_hardening)
    surface_green = review_meta.get("p6_structure_question_surface_role_plan_green") is True or _surface_plan_green(
        surface_role_plan
    )
    product_state = _product_quality_state(product_quality)
    family_review_flags = _family_review_flags(
        p6_family_review=family_review,
        p6_product_quality_review=product_quality,
        p7_review_meta=review_meta,
    )
    manual_read_feel_confirmed = _bool_from_meta_or_status(
        p7_review_meta=review_meta,
        regression_summary=regression,
        field_name="manual_read_feel_confirmed",
        suite_id="manual_read_feel_review",
    )
    long_run_sequence_evaluated = _bool_from_meta_or_status(
        p7_review_meta=review_meta,
        regression_summary=regression,
        field_name="long_run_sequence_evaluated",
        suite_id="p7_long_run_sequence_probe",
    )

    p4_return_material: list[str] = []
    p5_return_material: list[str] = []
    p6_continue_material: list[str] = []
    p7_hold_material: list[str] = []

    if entry_state["p4_return"] or not entry_state["p4_preserved"]:
        p4_return_material.append(REASON_P4_CURRENT_ONLY_REGRESSION_NOT_PRESERVED)
    if entry_state["p5_return"]:
        p5_return_material.append(REASON_P5_LIMITED_VISIBLE_CONNECTION_NOT_PRESERVED)
    if not entry_state["current_not_masked"]:
        p5_return_material.append(REASON_CURRENT_INPUT_MASKED_BY_HISTORY_OR_INSIGHT)
    if not entry_state["risk_not_increased"]:
        p5_return_material.append(REASON_CREEPY_RISK_INCREASED)
    if entry_state["deep_insight_substitute"]:
        p5_return_material.append(REASON_P6_USED_AS_HISTORY_LINE_SUBSTITUTE)
    if not entry_state["entry_allowed"]:
        p7_hold_material.append(REASON_P6_ENTRY_HOLD if entry_state["entry_hold"] else REASON_P6_ENTRY_NOT_ALLOWED)

    for suite in regression["required_regression_red_suites"]:
        if suite in P4_RETURN_SUITES:
            if suite == REQUIRED_SUITE_NO_CONNECT_FAMILY_REGRESSION:
                p4_return_material.append(REASON_NO_CONNECT_FAMILY_REGRESSION_NOT_GREEN)
            elif suite == REQUIRED_SUITE_PRODUCT_READFEEL_P4_TESTS:
                p4_return_material.append(REASON_PRODUCT_READFEEL_P4_REGRESSION_NOT_GREEN)
            else:
                p4_return_material.append(REASON_P4_CURRENT_ONLY_REGRESSION_NOT_PRESERVED)
        elif suite in P5_RETURN_SUITES:
            p5_return_material.append(f"{REASON_REQUIRED_REGRESSION_NOT_GREEN}:{suite}")
        else:
            p6_continue_material.append(f"{REASON_REQUIRED_REGRESSION_NOT_GREEN}:{suite}")
    if regression.get("no_connect_family_regression_failed") is True:
        p4_return_material.append(REASON_NO_CONNECT_FAMILY_REGRESSION_NOT_GREEN)
    if review_meta.get("no_connect_family_deep_insight_leak_detected") is True:
        p4_return_material.append(REASON_NO_CONNECT_FAMILY_DEEP_INSIGHT_LEAK)

    for suite in regression["required_regression_missing_suites"]:
        p7_hold_material.append(f"{REASON_REQUIRED_REGRESSION_SUITE_MISSING}:{suite}")
    for suite in regression["required_regression_not_executed_suites"]:
        p7_hold_material.append(f"{REASON_REQUIRED_REGRESSION_NOT_EXECUTED}:{suite}")

    if REASON_RAW_TEXT_PAYLOAD_DETECTED in meta_reasons or REASON_COMMENT_TEXT_BODY_DETECTED in meta_reasons:
        p5_return_material.extend(
            reason for reason in meta_reasons if reason in {REASON_RAW_TEXT_PAYLOAD_DETECTED, REASON_COMMENT_TEXT_BODY_DETECTED}
        )
    if REASON_PUBLIC_CONTRACT_MUTATION_DETECTED in meta_reasons:
        p5_return_material.append(REASON_PUBLIC_CONTRACT_MUTATION_DETECTED)
    if REASON_FIXED_SENTENCE_TEMPLATE_DETECTED in meta_reasons:
        p6_continue_material.append(REASON_FIXED_SENTENCE_TEMPLATE_DETECTED)
    if REASON_REVIEWER_FREE_TEXT_DETECTED in meta_reasons:
        p6_continue_material.append(REASON_REVIEWER_FREE_TEXT_DETECTED)
    if REASON_RELEASE_FLAG_DETECTED in meta_reasons:
        p6_continue_material.append(REASON_RELEASE_FLAG_DETECTED)

    if not family_green:
        p6_continue_material.append(REASON_P6_FAMILY_BOUNDARY_NOT_GREEN)
    if not relation_green or not relation_initial_visible:
        p6_continue_material.append(REASON_P6_RELATION_POLICY_NOT_GREEN)
    if not gate_green:
        p6_continue_material.append(REASON_P6_GATE_HARDENING_NOT_GREEN)
    if not surface_green:
        p6_continue_material.append(REASON_P6_SURFACE_ROLE_PLAN_NOT_GREEN)

    if product_state["unsafe_count"] > 0:
        p6_continue_material.append(REASON_P6_PRODUCT_QA_UNSAFE_CANDIDATE_PRESENT)
    if product_state["weak_count"] > 0:
        p6_continue_material.append(REASON_P6_PRODUCT_QA_WEAK_CANDIDATE_PRESENT)
    if not product_state["ready_candidate_present"]:
        if product_state["review_count"] == 0:
            p7_hold_material.append(REASON_P6_PRODUCT_QA_READY_CANDIDATE_MISSING)
        else:
            p6_continue_material.append(REASON_P6_PRODUCT_QA_READY_CANDIDATE_MISSING)
    if regression.get("no_connect_family_regression_green") is not True:
        p7_hold_material.append(REASON_NO_CONNECT_FAMILY_REGRESSION_NOT_GREEN)
    if not family_review_flags["long_meaning_arc_reviewed"]:
        p7_hold_material.append(REASON_LONG_MEANING_ARC_REVIEW_MISSING)
    if not family_review_flags["self_understanding_follow_reviewed"]:
        p7_hold_material.append(REASON_SELF_UNDERSTANDING_FOLLOW_REVIEW_MISSING)
    if not long_run_sequence_evaluated:
        p7_hold_material.append(REASON_LONG_RUN_SEQUENCE_NOT_EVALUATED)
    if not manual_read_feel_confirmed:
        p7_hold_material.append(REASON_MANUAL_READ_FEEL_NOT_CONFIRMED)

    p4_return_material = _dedupe(p4_return_material)
    p5_return_material = _dedupe(p5_return_material)
    p6_continue_material = _dedupe(p6_continue_material)
    p7_hold_material = _dedupe(p7_hold_material)
    decision = _decision(
        p4_return_material=p4_return_material,
        p5_return_material=p5_return_material,
        p6_continue_material=p6_continue_material,
        p7_hold_material=p7_hold_material,
    )
    decision_reasons = _dedupe([*p4_return_material, *p5_return_material, *p6_continue_material, *p7_hold_material])
    source_reason_codes = _source_reasons(
        entry,
        family_boundary,
        relation_policy,
        gate_hardening,
        surface_role_plan,
        family_review,
        product_quality,
    )
    p7_long_run_field_candidates = product_state["p7_long_run_field_candidates"]

    summary = {
        "schema_version": STRUCTURE_INSIGHT_P6_REGRESSION_HANDOFF_SUMMARY_SCHEMA_VERSION,
        "version": STRUCTURE_INSIGHT_P6_REGRESSION_HANDOFF_SUMMARY_SCHEMA_VERSION,
        "source": STRUCTURE_INSIGHT_P6_REGRESSION_HANDOFF_SOURCE,
        "step": STRUCTURE_INSIGHT_P6_REGRESSION_HANDOFF_STEP,
        "run_id": run,
        "p6_regression_handoff_created": True,
        "p6_regression_handoff_only": True,
        "decision": decision,
        "p7_ready": decision == DECISION_P7_READY,
        "p7_hold": decision == DECISION_P7_HOLD,
        "p6_continue": decision == DECISION_P6_CONTINUE,
        "p5_return": decision == DECISION_P5_RETURN,
        "p4_return": decision == DECISION_P4_RETURN,
        "p7_handoff_ready": decision == DECISION_P7_READY,
        "p7_hold_required": decision == DECISION_P7_HOLD,
        "p6_entry_allowed": entry_state["entry_allowed"],
        "p6_target_family_boundary_green": family_green,
        "p6_relation_policy_green": relation_green,
        "p6_relation_policy_initial_visible": relation_initial_visible,
        "p6_gate_hardening_green": gate_green,
        "p6_structure_question_surface_role_plan_green": surface_green,
        "p6_ratings_qa_has_structure_ready_candidates": product_state["ready_candidate_present"],
        "structure_insight_ready_candidate_count": product_state["ready_count"],
        "unsafe_insight_count": product_state["unsafe_count"],
        "weak_insight_count": product_state["weak_count"],
        "p7_long_run_field_candidate_count": product_state["p7_field_count"],
        "p7_long_run_field_candidates": p7_long_run_field_candidates,
        "no_connect_family_regression_green": regression["no_connect_family_regression_green"],
        "all_required_regression_green": regression["all_required_regression_green"],
        "regression_status_counts": dict(regression["status_counts"]),
        "required_regression_missing_suites": list(regression["required_regression_missing_suites"]),
        "required_regression_not_executed_suites": list(regression["required_regression_not_executed_suites"]),
        "required_regression_red_suites": list(regression["required_regression_red_suites"]),
        "long_meaning_arc_reviewed": family_review_flags["long_meaning_arc_reviewed"],
        "self_understanding_follow_reviewed": family_review_flags["self_understanding_follow_reviewed"],
        "long_run_sequence_evaluated": long_run_sequence_evaluated,
        "manual_read_feel_confirmed": manual_read_feel_confirmed,
        "p4_return_material": p4_return_material,
        "p5_return_material": p5_return_material,
        "p6_continue_material": p6_continue_material,
        "p7_hold_material": p7_hold_material,
        "decision_reason_codes": decision_reasons,
        "source_reason_codes": source_reason_codes,
        "recommended_next_action": {
            DECISION_P7_READY: "continue_to_p7_product_quality_runner_long_run_gate",
            DECISION_P7_HOLD: "hold_before_p7_until_ratings_manual_or_long_run_material_is_confirmed",
            DECISION_P6_CONTINUE: "continue_p6_structure_insight_repair_or_ratings_review",
            DECISION_P5_RETURN: "return_to_p5_current_history_connection_boundary_repair",
            DECISION_P4_RETURN: "return_to_p4_current_only_readfeel_or_no_connect_regression_repair",
        }[decision],
        "release_allowed": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "ratings_only_payload": True,
        "body_free_summary_only": True,
        "public_text_payload_excluded": True,
        "public_contract": _public_contract(),
        "body_free": _body_free_contract(),
    }
    report = {
        "schema_version": STRUCTURE_INSIGHT_P6_REGRESSION_HANDOFF_SCHEMA_VERSION,
        "version": STRUCTURE_INSIGHT_P6_REGRESSION_HANDOFF_SCHEMA_VERSION,
        "source": STRUCTURE_INSIGHT_P6_REGRESSION_HANDOFF_SOURCE,
        "step": STRUCTURE_INSIGHT_P6_REGRESSION_HANDOFF_STEP,
        "run_id": run,
        "p6_regression_handoff_created": True,
        "p6_regression_handoff_only": True,
        "decision": decision,
        "p7_ready": decision == DECISION_P7_READY,
        "p7_hold": decision == DECISION_P7_HOLD,
        "p6_continue": decision == DECISION_P6_CONTINUE,
        "p5_return": decision == DECISION_P5_RETURN,
        "p4_return": decision == DECISION_P4_RETURN,
        "normalized_regression_statuses": list(regression["normalized_statuses"]),
        "decision_reason_codes": decision_reasons,
        "release_allowed": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "public_contract": _public_contract(),
        "body_free": _body_free_contract(),
        "summary": summary,
    }
    assert_structure_insight_p6_regression_handoff_contract(report)
    return report


def assert_structure_insight_p6_regression_handoff_contract(
    report: Mapping[str, Any],
    *,
    allow_partial: bool = False,
) -> bool:
    """Validate that P6-9 handoff remains body-free and non-release."""

    if not isinstance(report, Mapping):
        raise TypeError("P6 regression handoff must be a mapping")
    data = _safe_mapping(report)
    if not allow_partial and data.get("schema_version") != STRUCTURE_INSIGHT_P6_REGRESSION_HANDOFF_SCHEMA_VERSION:
        raise ValueError("Unexpected P6 regression handoff schema version")
    if not allow_partial and data.get("step") != STRUCTURE_INSIGHT_P6_REGRESSION_HANDOFF_STEP:
        raise ValueError("Unexpected P6 regression handoff step")
    decision = _clean(data.get("decision"))
    if decision and decision not in P6_REGRESSION_HANDOFF_DECISIONS:
        raise ValueError("Unexpected P6 regression handoff decision")
    if _contains_key(data, _TEXT_PAYLOAD_KEYS | _COMMENT_TEXT_PAYLOAD_KEYS | _REVIEWER_FREE_TEXT_KEYS):
        raise ValueError("P6 regression handoff must not include body or reviewer free text keys")
    if _flag_true(data, _FORBIDDEN_TRUE_FLAGS):
        raise ValueError("P6 regression handoff contains forbidden true flags")
    public_contract = _safe_mapping(data.get("public_contract"))
    if public_contract and _flag_true(public_contract, _PUBLIC_CONTRACT_TRUE_FLAGS | _FIXED_TEMPLATE_TRUE_FLAGS):
        raise ValueError("P6 regression handoff mutates public contract or adds templates")
    body_free = _safe_mapping(data.get("body_free"))
    if body_free and _flag_true(body_free, _FORBIDDEN_TRUE_FLAGS):
        raise ValueError("P6 regression handoff includes body payload flags")
    summary = _safe_mapping(data.get("summary"))
    if summary:
        if not allow_partial and summary.get("schema_version") != STRUCTURE_INSIGHT_P6_REGRESSION_HANDOFF_SUMMARY_SCHEMA_VERSION:
            raise ValueError("Unexpected P6 regression handoff summary schema version")
        if _contains_key(summary, _TEXT_PAYLOAD_KEYS | _COMMENT_TEXT_PAYLOAD_KEYS | _REVIEWER_FREE_TEXT_KEYS):
            raise ValueError("P6 regression handoff summary must not include body or reviewer free text keys")
        if _flag_true(summary, _FORBIDDEN_TRUE_FLAGS):
            raise ValueError("P6 regression handoff summary contains forbidden true flags")
    return True


def dump_structure_insight_p6_regression_handoff_public_summary(report: Mapping[str, Any]) -> str:
    """Serialize only the body-free P6-9 summary."""

    data = _safe_mapping(report)
    assert_structure_insight_p6_regression_handoff_contract(data)
    summary = _safe_mapping(data.get("summary")) or data
    assert_structure_insight_p6_regression_handoff_contract(summary, allow_partial=True)
    safe_summary = {
        "schema_version": summary.get("schema_version"),
        "step": summary.get("step"),
        "run_id": summary.get("run_id"),
        "decision": summary.get("decision"),
        "p7_ready": summary.get("p7_ready") is True,
        "p7_hold": summary.get("p7_hold") is True,
        "p6_continue": summary.get("p6_continue") is True,
        "p5_return": summary.get("p5_return") is True,
        "p4_return": summary.get("p4_return") is True,
        "all_required_regression_green": summary.get("all_required_regression_green") is True,
        "no_connect_family_regression_green": summary.get("no_connect_family_regression_green") is True,
        "structure_insight_ready_candidate_count": summary.get("structure_insight_ready_candidate_count"),
        "unsafe_insight_count": summary.get("unsafe_insight_count"),
        "weak_insight_count": summary.get("weak_insight_count"),
        "p7_long_run_field_candidate_count": summary.get("p7_long_run_field_candidate_count"),
        "long_meaning_arc_reviewed": summary.get("long_meaning_arc_reviewed") is True,
        "self_understanding_follow_reviewed": summary.get("self_understanding_follow_reviewed") is True,
        "long_run_sequence_evaluated": summary.get("long_run_sequence_evaluated") is True,
        "manual_read_feel_confirmed": summary.get("manual_read_feel_confirmed") is True,
        "p4_return_material": list(summary.get("p4_return_material") or []),
        "p5_return_material": list(summary.get("p5_return_material") or []),
        "p6_continue_material": list(summary.get("p6_continue_material") or []),
        "p7_hold_material": list(summary.get("p7_hold_material") or []),
        "decision_reason_codes": list(summary.get("decision_reason_codes") or []),
        "recommended_next_action": summary.get("recommended_next_action"),
        "release_allowed": False,
        "public_contract": _safe_mapping(summary.get("public_contract")),
        "body_free": _safe_mapping(summary.get("body_free")),
    }
    assert_structure_insight_p6_regression_handoff_contract(safe_summary, allow_partial=True)
    return json.dumps(safe_summary, ensure_ascii=False, sort_keys=True)
