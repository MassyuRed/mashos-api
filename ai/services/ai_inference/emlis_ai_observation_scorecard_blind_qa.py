# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 12 Scorecard / Blind QA for EmlisAI observation replies.

This module is the observation-reply specific evaluation layer.  It consumes
meta-only runtime/scorecard events and ratings-only Blind QA reviews, then
reports observation metrics without changing public API/RN/DB contracts and
without writing public ``comment_text``.
"""

import json
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Final

from emlis_ai_observation_reply_contract import (
    OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE,
    OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
    OBSERVATION_REPLY_KIND_ELIGIBLE,
    OBSERVATION_REPLY_KIND_LOW_INFORMATION,
    USER_FACT_GROUNDING_MODE_DISABLED,
    assert_observation_reply_meta_contract,
)
from emlis_ai_observation_regression_fixture_coverage import (
    OBSERVATION_REGRESSION_FIXTURE_COVERAGE_STEP,
    OBSERVATION_REGRESSION_FIXTURE_COVERAGE_VERSION,
    build_observation_regression_fixture_coverage,
    normalize_observation_regression_fixture_coverage_to_scorecard_fields,
)

OBSERVATION_SCORECARD_BLIND_QA_VERSION: Final = "emlis.observation_scorecard_blind_qa.v1"
OBSERVATION_SCORECARD_BLIND_QA_STEP: Final = "Step12_Scorecard_Blind_QA"
OBSERVATION_BLIND_QA_REVIEW_VERSION: Final = "emlis.observation_blind_qa_review.v1"
OBSERVATION_BLIND_QA_RUBRIC_VERSION: Final = "emlis.observation_blind_qa_rubric.v1"
OBSERVATION_SCORECARD_EVENT_VERSION: Final = "emlis.observation_scorecard_event.v1"
OBSERVATION_ALWAYS_DISPLAY_TARGET: Final = 1.0
OBSERVATION_ELIGIBLE_REPLY_TARGET: Final = 0.90
OBSERVATION_LOW_INFO_REPLY_TARGET: Final = 1.0
OBSERVATION_FALSE_ELIGIBLE_TARGET: Final = 0.0
OBSERVATION_BLIND_QA_READ_FEELING_TARGET: Final = 0.90

OBSERVATION_BLIND_QA_REQUIRED_DIMENSIONS: tuple[str, ...] = (
    "read_feeling",
    "input_arrangement",
    "state_verbalization",
    "low_info_question_quality",
    "user_fact_boundary",
    "overclaim_absence",
    "non_template",
)

_DIMENSION_ALIASES = {
    "read_feeling": "read_feeling",
    "read_feeling_score": "read_feeling",
    "read": "read_feeling",
    "read-feeling": "read_feeling",
    "input_arrangement": "input_arrangement",
    "arrangement": "input_arrangement",
    "input整理": "input_arrangement",
    "state_verbalization": "state_verbalization",
    "state": "state_verbalization",
    "状態言語化": "state_verbalization",
    "low_info_question_quality": "low_info_question_quality",
    "low_information_question_quality": "low_info_question_quality",
    "question_quality": "low_info_question_quality",
    "低情報質問": "low_info_question_quality",
    "user_fact_boundary": "user_fact_boundary",
    "user_dictionary_boundary": "user_fact_boundary",
    "free_boundary": "user_fact_boundary",
    "ユーザー辞書境界": "user_fact_boundary",
    "overclaim_absence": "overclaim_absence",
    "overclaim": "overclaim_absence",
    "no_overclaim": "overclaim_absence",
    "過剰補完なし": "overclaim_absence",
    "non_template": "non_template",
    "non-template": "non_template",
    "input_specific_structure_reflected": "read_feeling",
    "relation_verbalization": "state_verbalization",
    "low_information_question": "low_info_question_quality",
    "free_user_fact_boundary": "user_fact_boundary",
    "natural_but_not_template": "non_template",
    "no_overclaim": "overclaim_absence",
    "template": "non_template",
    "非テンプレ": "non_template",
}
_VERDICT_SCORES = {
    "green": 1.0,
    "g": 1.0,
    "pass": 1.0,
    "passed": 1.0,
    "ok": 1.0,
    "yellow": 0.65,
    "y": 0.65,
    "warn": 0.65,
    "warning": 0.65,
    "red": 0.0,
    "r": 0.0,
    "fail": 0.0,
    "failed": 0.0,
    "ng": 0.0,
}
_FORBIDDEN_TEXT_PAYLOAD_KEYS = {
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
_FORBIDDEN_TRUE_FLAGS = (
    "raw_input_included",
    "raw_text_included",
    "comment_text_included",
    "comment_text_body_included",
    "display_gate_relaxed",
    "grounding_gate_relaxed",
    "reader_gate_relaxed",
    "template_gate_relaxed",
    "gate_relaxed",
    "public_status_extended",
    "observation_status_enum_extended",
    "response_shape_changed",
    "public_response_key_change",
    "api_route_changed",
    "db_physical_name_changed",
    "rn_visible_contract_changed",
    "rn_visible_title_changed",
    "product_gate_ready",
    "product_gate_reached",
    "product_gate_achieved",
    "product_gate_public_release_applied",
    "public_release_applied",
    "product_quality_released",
    "fixed_fallback_used",
    "fixed_sentence_template_used",
    "external_ai_used",
    "local_llm_used",
)
_SAFETY_OR_INFRA_MARKERS = (
    "safety",
    "self_harm",
    "harm",
    "policy_blocked",
    "infra",
    "infrastructure",
    "timeout",
    "server_error",
    "exception",
    "network_error",
    "system_error",
)
_OVERCLAIM_MARKERS = (
    "overclaim",
    "unsupported_current_event",
    "assert_current_event",
    "personality",
    "personality_tendency",
    "diagnosis",
    "diagnostic",
    "background_added",
    "unsupported_background",
    "medical",
    "action_instruction",
)
_TEMPLATE_MARKERS = (
    "template",
    "fixed_sentence",
    "fixed_fallback",
    "skeleton_repeat",
    "surface_signature_repeat",
    "same_ending",
    "raw_echo",
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


def _int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return None


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(max(0.0, min(1.0, numerator / denominator)), 4)


def _avg(values: Iterable[Any]) -> float | None:
    scores: list[float] = []
    for value in values:
        score = _float(value)
        if score is not None:
            scores.append(score)
    if not scores:
        return None
    return round(sum(scores) / len(scores), 4)


def _score_from_verdict(value: Any) -> float | None:
    text = _clean(value).lower()
    if text in _VERDICT_SCORES:
        return _VERDICT_SCORES[text]
    return _float(value)


def _contains_forbidden_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in _FORBIDDEN_TEXT_PAYLOAD_KEYS:
                return True
            if _contains_forbidden_text_payload_key(item):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_text_payload_key(item) for item in value)
    return False


def _strip_forbidden_text_payload_keys(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _strip_forbidden_text_payload_keys(item)
            for key, item in value.items()
            if str(key) not in _FORBIDDEN_TEXT_PAYLOAD_KEYS
        }
    if isinstance(value, list):
        return [_strip_forbidden_text_payload_keys(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_strip_forbidden_text_payload_keys(item) for item in value)
    if isinstance(value, set):
        return {_strip_forbidden_text_payload_keys(item) for item in value}
    return value


def assert_observation_scorecard_blind_qa_contract(
    value: Mapping[str, Any],
    *,
    source: str = "observation_scorecard_blind_qa",
) -> None:
    """Keep Step 12 scorecard payloads meta-only and side-effect free."""

    if _contains_forbidden_text_payload_key(value):
        raise ValueError(f"{source} must stay meta-only and must not include text payload keys")
    for flag in _FORBIDDEN_TRUE_FLAGS:
        if value.get(flag) is True:
            raise ValueError(f"{source} violates fixed contract: {flag}=true")


def _find_observation_reply_meta(value: Any, *, depth: int = 0) -> dict[str, Any]:
    if depth > 5 or not isinstance(value, Mapping):
        return {}
    data = _safe_mapping(value)
    if data.get("observation_reply_kind") or data.get("eligibility_status"):
        return data
    for key in (
        "observation_reply_meta",
        "observation_reply_contract",
        "step10_observation_display_repair_integration",
        "emlis_ai",
        "input_feedback",
        "diagnostic_summary",
        "multi_perspective",
        "phase_gate",
        "runtime_meta",
        "composer_meta",
    ):
        nested = _find_observation_reply_meta(data.get(key), depth=depth + 1)
        if nested:
            return nested
    return {}


def extract_observation_reply_meta(source: Mapping[str, Any] | None) -> dict[str, Any]:
    """Extract the sanitized optional observation reply meta from a row/event."""

    data = _safe_mapping(source)
    assert_observation_scorecard_blind_qa_contract(data, source="observation_reply_meta_source")
    raw_meta = _find_observation_reply_meta(data)
    if not raw_meta:
        return {}
    kind = _clean(raw_meta.get("observation_reply_kind"))
    status = _clean(raw_meta.get("eligibility_status") or raw_meta.get("status"))
    if not kind:
        if status == OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION:
            kind = OBSERVATION_REPLY_KIND_LOW_INFORMATION
        elif status == OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE:
            kind = OBSERVATION_REPLY_KIND_ELIGIBLE
    if kind not in {OBSERVATION_REPLY_KIND_ELIGIBLE, OBSERVATION_REPLY_KIND_LOW_INFORMATION}:
        return {}
    if not status:
        status = (
            OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
            if kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION
            else OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE
        )
    meta = {
        "observation_reply_kind": kind,
        "eligibility_status": status,
        "eligible_for_full_observation": bool(raw_meta.get("eligible_for_full_observation") is True),
        "question_required": bool(raw_meta.get("question_required") is True),
        "unknown_slots": _dedupe(raw_meta.get("unknown_slots")),
        "sentence_plan_observation_roles": _dedupe(
            raw_meta.get("sentence_plan_observation_roles") or raw_meta.get("observation_roles")
        ),
        "inference_depths": [
            _int(depth)
            for depth in _listify(raw_meta.get("inference_depths") or raw_meta.get("inference_depth"))
            if _int(depth) > 0
        ],
        "plan": _clean(raw_meta.get("plan") or raw_meta.get("subscription_tier")) or "free",
        "user_fact_allowed": bool(raw_meta.get("user_fact_allowed") is True),
        "user_fact_read_enabled": bool(raw_meta.get("user_fact_read_enabled") is True),
        "user_fact_may_hint": bool(raw_meta.get("user_fact_may_hint") is True),
        "user_fact_may_promote_to_eligible": bool(raw_meta.get("user_fact_may_promote_to_eligible") is True),
        "user_fact_grounding_mode": _clean(raw_meta.get("user_fact_grounding_mode") or raw_meta.get("mode")) or USER_FACT_GROUNDING_MODE_DISABLED,
        "facts_used": [
            {k: v for k, v in _safe_mapping(item).items() if k not in _FORBIDDEN_TEXT_PAYLOAD_KEYS}
            if isinstance(item, Mapping)
            else {"fact_id": _clean(item)}
            for item in _listify(raw_meta.get("facts_used"))
            if _clean(item) or isinstance(item, Mapping)
        ],
        "free_user_fact_blocked": bool(raw_meta.get("free_user_fact_blocked") is True),
        "surface_disclosure_required": bool(raw_meta.get("surface_disclosure_required") is True),
        "must_not_assert_current_event_from_user_fact": raw_meta.get("must_not_assert_current_event_from_user_fact") is not False,
        "must_not_promote_low_info_to_eligible": raw_meta.get("must_not_promote_low_info_to_eligible") is not False,
    }
    # Validate only when a full Step1 contract is present; imported rows may be
    # partial, but still must keep the same boundary flags.
    if raw_meta.get("version") and raw_meta.get("comment_text_contract"):
        assert_observation_reply_meta_contract(raw_meta, source="extracted_observation_reply_meta")
    assert_observation_scorecard_blind_qa_contract(meta, source="extracted_observation_reply_meta")
    return meta


def _event_reasons(event: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    for key in (
        "top_rejection_reasons",
        "rejection_reasons",
        "display_count_blockers",
        "surface_major_reasons",
        "surface_grammar_warning_codes",
        "grammar_warning_codes",
        "reason_counter",
        "release_blockers",
    ):
        value = event.get(key)
        if isinstance(value, Mapping):
            reasons.extend(value.keys())
        else:
            reasons.extend(_dedupe(value))
    return _dedupe(reasons)


def _has_marker(values: Iterable[Any], markers: Sequence[str]) -> bool:
    for value in values:
        text = _clean(value).lower()
        if any(marker in text for marker in markers):
            return True
    return False


def _normal_input(event: Mapping[str, Any], reasons: Sequence[str]) -> bool:
    status = _clean(event.get("observation_status") or event.get("backend_observation_status")).lower()
    if status == "safety_blocked":
        return False
    if event.get("safety_blocked_count") and _int(event.get("safety_blocked_count")) > 0:
        return False
    if event.get("safety_or_infra_excluded") is True or event.get("normal_input") is False:
        return False
    if _has_marker(reasons, _SAFETY_OR_INFRA_MARKERS):
        return False
    return True


def _passed_body_returned(event: Mapping[str, Any]) -> bool:
    status = _clean(event.get("observation_status") or event.get("backend_observation_status")).lower()
    if status != "passed":
        return False
    if event.get("backend_public_passed") is True or event.get("public_passed") is True:
        return True
    if event.get("display_confirmed") is True or _int(event.get("passed_display_count")) > 0:
        return True
    if event.get("comment_text_present") is True or event.get("backend_comment_text_present") is True:
        return True
    return False


def _expected_branch(meta: Mapping[str, Any], event: Mapping[str, Any]) -> str:
    expected_status = _clean(event.get("expected_eligibility_status") or event.get("expected_status"))
    expected_kind = _clean(event.get("expected_observation_reply_kind") or event.get("expected_reply_kind"))
    if expected_status in {OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE, OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION}:
        return expected_status
    if expected_kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION:
        return OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
    if expected_kind == OBSERVATION_REPLY_KIND_ELIGIBLE:
        return OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE
    status = _clean(meta.get("eligibility_status") or event.get("eligibility_status") or event.get("status"))
    kind = _clean(meta.get("observation_reply_kind") or event.get("observation_reply_kind"))
    if status == OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION or kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION:
        return OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
    if status == OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE or kind == OBSERVATION_REPLY_KIND_ELIGIBLE:
        return OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE
    if event.get("eligible_for_full_observation") is True:
        return OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE
    if event.get("question_required") is True or _dedupe(event.get("unknown_slots")):
        return OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
    return "unknown"


def _actual_reply_kind(meta: Mapping[str, Any], event: Mapping[str, Any]) -> str:
    return _clean(meta.get("observation_reply_kind") or event.get("observation_reply_kind"))


def _free_user_fact_violation(meta: Mapping[str, Any], event: Mapping[str, Any]) -> bool:
    plan = _clean(meta.get("plan") or event.get("plan") or event.get("subscription_tier")).lower()
    if plan in {"", "free"}:
        return bool(
            event.get("free_user_fact_violation") is True
            or meta.get("user_fact_allowed") is True
            or meta.get("user_fact_read_enabled") is True
            or _clean(meta.get("user_fact_grounding_mode")) not in {"", USER_FACT_GROUNDING_MODE_DISABLED}
            or bool(meta.get("facts_used"))
            or bool(event.get("facts_used"))
        )
    return bool(event.get("free_user_fact_violation") is True)


def _overclaim(event: Mapping[str, Any], reasons: Sequence[str]) -> bool:
    return bool(
        _int(event.get("overclaim_count")) > 0
        or event.get("unsupported_current_event_assertion") is True
        or event.get("assert_current_event_from_user_fact") is True
        or event.get("personality_tendency_allowed") is True
        or _has_marker(reasons, _OVERCLAIM_MARKERS)
    )


def _template_repeat(event: Mapping[str, Any], reasons: Sequence[str]) -> bool:
    return bool(
        _int(event.get("template_skeleton_repeat_count")) > 0
        or _int(event.get("surface_signature_repeat_count")) > 0
        or _int(event.get("same_skeleton_repeat_count")) > 0
        or event.get("surface_signature_repeat_detected") is True
        or event.get("template_skeleton_repeat_detected") is True
        or _has_marker(reasons, _TEMPLATE_MARKERS)
    )


def _template_skeleton_key(event: Mapping[str, Any]) -> str:
    signature = _safe_mapping(event.get("surface_quality_signature") or event.get("step2_surface_quality_signature"))
    return (
        _clean(event.get("template_skeleton_key"))
        or _clean(event.get("surface_skeleton_key"))
        or _clean(event.get("surface_signature_family_key"))
        or _clean(event.get("signature_family_key"))
        or _clean(signature.get("surface_skeleton_key"))
        or _clean(signature.get("surface_signature_family_key"))
        or _clean(signature.get("signature_family_key"))
        or _clean(signature.get("surface_signature_id"))
    )


def _false_eligible(meta: Mapping[str, Any], event: Mapping[str, Any], expected_branch: str, actual_kind: str) -> bool:
    if expected_branch != OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION:
        return False
    inference_depths = [
        _int(depth)
        for depth in _listify(meta.get("inference_depths") or event.get("inference_depths") or event.get("inference_depth"))
        if _int(depth) > 0
    ]
    max_depth = max(inference_depths or [_int(event.get("max_inference_depth_used"), 0)])
    roles = set(_dedupe(meta.get("sentence_plan_observation_roles") or event.get("sentence_plan_observation_roles") or event.get("observation_roles")))
    return bool(
        actual_kind == OBSERVATION_REPLY_KIND_ELIGIBLE
        or meta.get("eligible_for_full_observation") is True
        or event.get("eligible_for_full_observation") is True
        or event.get("deep_relation_allowed") is True
        or max_depth > 1
        or "state_verbalization" in roles
    )


def normalize_observation_scorecard_event(event: Mapping[str, Any] | None) -> dict[str, Any]:
    data = _strip_forbidden_text_payload_keys(_safe_mapping(event))
    assert_observation_scorecard_blind_qa_contract(data, source="observation_scorecard_event_source")
    meta = extract_observation_reply_meta(data)
    reasons = _event_reasons(data)
    expected = _expected_branch(meta, data)
    actual_kind = _actual_reply_kind(meta, data)
    normal_input = _normal_input(data, reasons)
    passed_body = _passed_body_returned(data)
    normalized = {
        "version": OBSERVATION_SCORECARD_EVENT_VERSION,
        "source_step": OBSERVATION_SCORECARD_BLIND_QA_STEP,
        "event_kind": "observation_reply_scorecard_event",
        "row_id": _clean(data.get("row_id") or data.get("candidate_id") or data.get("trace_id") or data.get("emotion_log_id")),
        "trace_id": _clean(data.get("trace_id")),
        "emotion_log_id": _clean(data.get("emotion_log_id")),
        "coverage_group": _clean(data.get("coverage_group")) or "coverage_group_missing",
        "fixture_group": _clean(data.get("fixture_group") or data.get("observation_fixture_group") or data.get("regression_fixture_group")),
        "fixture_id": _clean(data.get("fixture_id") or data.get("row_id") or data.get("candidate_id") or data.get("trace_id")),
        "observation_status": _clean(data.get("observation_status") or data.get("backend_observation_status")),
        "normal_input": normal_input,
        "safety_or_infra_excluded": not normal_input,
        "passed_body_returned": passed_body,
        "always_display_success": bool(normal_input and passed_body),
        "observation_reply_kind": actual_kind,
        "expected_observation_branch": expected,
        "expected_eligible": expected == OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE,
        "expected_low_information": expected == OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
        "eligible_observation_success": bool(expected == OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE and actual_kind == OBSERVATION_REPLY_KIND_ELIGIBLE and passed_body),
        "low_info_observation_success": bool(expected == OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION and actual_kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION and passed_body),
        "false_eligible": _false_eligible(meta, data, expected, actual_kind),
        "free_user_fact_violation": _free_user_fact_violation(meta, data),
        "overclaim": _overclaim(data, reasons),
        "template_skeleton_repeat": _template_repeat(data, reasons),
        "template_skeleton_key": _template_skeleton_key(data),
        "question_required": bool(meta.get("question_required") or data.get("question_required")),
        "unknown_slots": _dedupe(meta.get("unknown_slots") or data.get("unknown_slots")),
        "user_fact_grounding_mode": _clean(meta.get("user_fact_grounding_mode") or data.get("user_fact_grounding_mode")) or USER_FACT_GROUNDING_MODE_DISABLED,
        "facts_used_count": len(meta.get("facts_used") or _listify(data.get("facts_used"))),
        "observation_reply_meta_present": bool(meta),
        "reasons": reasons,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
    }
    assert_observation_scorecard_blind_qa_contract(normalized, source="normalized_observation_scorecard_event")
    return normalized


def normalize_observation_blind_qa_review(review: Mapping[str, Any] | None) -> dict[str, Any]:
    data = _safe_mapping(_strip_forbidden_text_payload_keys(_safe_mapping(review)))
    assert_observation_scorecard_blind_qa_contract(data, source="observation_blind_qa_review")
    ratings = _safe_mapping(data.get("ratings")) or _safe_mapping(data.get("dimension_ratings"))
    if not ratings:
        ratings = {key: value for key, value in data.items() if _DIMENSION_ALIASES.get(str(key).strip().lower())}
    dimension_scores: dict[str, float | None] = {dimension: None for dimension in OBSERVATION_BLIND_QA_REQUIRED_DIMENSIONS}
    for raw_key, raw_value in ratings.items():
        dimension = _DIMENSION_ALIASES.get(str(raw_key).strip().lower())
        if not dimension:
            continue
        score = _score_from_verdict(raw_value)
        if score is not None:
            dimension_scores[dimension] = score
    evaluated = [score for score in dimension_scores.values() if score is not None]
    red_count = sum(1 for score in dimension_scores.values() if score == 0.0)
    read_score = dimension_scores.get("read_feeling")
    branch = _clean(data.get("observation_reply_kind") or data.get("reply_kind"))
    missing_dimensions = [dimension for dimension, score in dimension_scores.items() if score is None]
    normalized = {
        "version": OBSERVATION_BLIND_QA_REVIEW_VERSION,
        "source_step": OBSERVATION_SCORECARD_BLIND_QA_STEP,
        "review_kind": "observation_reply_blind_qa_rating_only_review",
        "review_id": _clean(data.get("review_id") or data.get("id")),
        "candidate_id": _clean(data.get("candidate_id") or data.get("row_id") or data.get("trace_id") or data.get("emotion_log_id")),
        "row_id": _clean(data.get("row_id")),
        "trace_id": _clean(data.get("trace_id")),
        "emotion_log_id": _clean(data.get("emotion_log_id")),
        "coverage_group": _clean(data.get("coverage_group")) or "coverage_group_missing",
        "observation_reply_kind": branch,
        "dimension_scores": dimension_scores,
        "read_feeling_score": read_score,
        "score": _avg(evaluated),
        "red_count": red_count,
        "missing_dimensions": missing_dimensions,
        "ratings_only_payload": True,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "passed": bool(read_score is not None and read_score >= OBSERVATION_BLIND_QA_READ_FEELING_TARGET and red_count == 0),
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
    }
    assert_observation_scorecard_blind_qa_contract(normalized, source="normalized_observation_blind_qa_review")
    return normalized


def aggregate_observation_blind_qa_reviews(
    reviews: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
) -> dict[str, Any]:
    normalized = [normalize_observation_blind_qa_review(review) for review in list(reviews or [])]
    read_scores = [review.get("read_feeling_score") for review in normalized if review.get("read_feeling_score") is not None]
    scores = [review.get("score") for review in normalized if review.get("score") is not None]
    red_count = sum(_int(review.get("red_count")) for review in normalized)
    missing_dimension_counter: dict[str, int] = {}
    for review in normalized:
        for dimension in review.get("missing_dimensions") or []:
            missing_dimension_counter[dimension] = missing_dimension_counter.get(dimension, 0) + 1
    aggregate = {
        "version": OBSERVATION_SCORECARD_BLIND_QA_VERSION,
        "source_step": OBSERVATION_SCORECARD_BLIND_QA_STEP,
        "blind_qa_ready": bool(normalized),
        "review_count": len(normalized),
        "pass_count": sum(1 for review in normalized if review.get("passed") is True),
        "red_review_count": sum(1 for review in normalized if _int(review.get("red_count")) > 0),
        "red_dimension_count": red_count,
        "read_feeling_score": _avg(read_scores),
        "overall_score": _avg(scores),
        "read_feeling_target": OBSERVATION_BLIND_QA_READ_FEELING_TARGET,
        "read_feeling_pass_rate": _rate(sum(1 for score in read_scores if float(score) >= OBSERVATION_BLIND_QA_READ_FEELING_TARGET), len(normalized)),
        "missing_dimension_counter": missing_dimension_counter,
        "reviews": normalized,
        "ratings_only_payload": True,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
    }
    assert_observation_scorecard_blind_qa_contract(aggregate, source="observation_blind_qa_aggregate")
    return aggregate


def build_observation_blind_qa_rubric() -> dict[str, Any]:
    rubric = {
        "version": OBSERVATION_BLIND_QA_RUBRIC_VERSION,
        "source_step": OBSERVATION_SCORECARD_BLIND_QA_STEP,
        "target_step": OBSERVATION_SCORECARD_BLIND_QA_STEP,
        "purpose": "evaluate_observation_reply_read_feeling_branch_quality_and_boundaries",
        "ratings_only_payload": True,
        "machine_metrics_separated": True,
        "machine_metrics_are_separate": True,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_requires_blind_qa": True,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "exact_comment_text_locked": False,
        "required_dimensions": list(OBSERVATION_BLIND_QA_REQUIRED_DIMENSIONS),
        "dimensions": {
            "read_feeling": "the reply feels read as this input rather than generic comfort",
            "input_arrangement": "states wishes stuckness and burden are arranged without mere repetition",
            "state_verbalization": "eligible replies express the relation/state without adding background",
            "low_info_question_quality": "low information replies observe known scope and ask for the missing slot",
            "user_fact_boundary": "Free never uses user facts; subscription facts do not assert current events",
            "overclaim_absence": "no unsupported background personality diagnosis or action instruction",
            "non_template": "not a fixed fallback skeleton or raw echo with observation endings",
        },
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
    }
    assert_observation_scorecard_blind_qa_contract(rubric, source="observation_blind_qa_rubric")
    return rubric


def build_observation_scorecard_blind_qa(
    *,
    events: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
    scorecard_events: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
    blind_qa_reviews: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
    run_id: str = "",
) -> dict[str, Any]:
    source_events = list(events or []) + list(scorecard_events or [])
    normalized_events = [normalize_observation_scorecard_event(event) for event in source_events]
    normal_events = [event for event in normalized_events if event.get("normal_input") is True]
    expected_eligible = [event for event in normal_events if event.get("expected_eligible") is True]
    expected_low_info = [event for event in normal_events if event.get("expected_low_information") is True]
    always_display_success_count = sum(1 for event in normal_events if event.get("always_display_success") is True)
    eligible_success_count = sum(1 for event in expected_eligible if event.get("eligible_observation_success") is True)
    low_info_success_count = sum(1 for event in expected_low_info if event.get("low_info_observation_success") is True)
    false_eligible_count = sum(1 for event in expected_low_info if event.get("false_eligible") is True)
    free_user_fact_violation_count = sum(1 for event in normalized_events if event.get("free_user_fact_violation") is True)
    overclaim_count = sum(1 for event in normalized_events if event.get("overclaim") is True)
    explicit_template_repeat_count = sum(1 for event in normalized_events if event.get("template_skeleton_repeat") is True)
    skeleton_counter = Counter(
        event.get("template_skeleton_key")
        for event in normal_events
        if event.get("template_skeleton_key")
    )
    repeated_skeleton_count = sum(max(0, count - 1) for count in skeleton_counter.values())
    template_skeleton_repeat_count = max(explicit_template_repeat_count, repeated_skeleton_count)
    blind_qa = aggregate_observation_blind_qa_reviews(blind_qa_reviews)
    regression_fixture_coverage = build_observation_regression_fixture_coverage(
        scorecard_events=source_events,
        run_id=run_id,
    )
    regression_fixture_fields = normalize_observation_regression_fixture_coverage_to_scorecard_fields(
        regression_fixture_coverage
    )
    always_display_rate = _rate(always_display_success_count, len(normal_events))
    eligible_observation_rate = _rate(eligible_success_count, len(expected_eligible))
    low_info_observation_rate = _rate(low_info_success_count, len(expected_low_info))
    false_eligible_rate = _rate(false_eligible_count, len(expected_low_info))
    template_skeleton_repeat_rate = _rate(template_skeleton_repeat_count, len(normal_events))
    read_score = blind_qa.get("read_feeling_score")
    regression_fixture_requested = bool(regression_fixture_coverage.get("fixture_event_count"))

    qa_gaps: list[str] = []
    if not normalized_events:
        qa_gaps.append("observation_scorecard_events_missing")
    if normal_events and always_display_rate < OBSERVATION_ALWAYS_DISPLAY_TARGET:
        qa_gaps.append("always_display_rate_below_target")
    if expected_eligible and eligible_observation_rate < OBSERVATION_ELIGIBLE_REPLY_TARGET:
        qa_gaps.append("eligible_observation_rate_below_target")
    if expected_low_info and low_info_observation_rate < OBSERVATION_LOW_INFO_REPLY_TARGET:
        qa_gaps.append("low_info_observation_rate_below_target")
    if false_eligible_count > 0:
        qa_gaps.append("false_eligible_detected")
    if free_user_fact_violation_count > 0:
        qa_gaps.append("free_user_fact_violation_detected")
    if overclaim_count > 0:
        qa_gaps.append("overclaim_detected")
    if template_skeleton_repeat_count > 0:
        qa_gaps.append("template_skeleton_repeat_detected")
    if not blind_qa.get("blind_qa_ready"):
        qa_gaps.append("observation_blind_qa_missing")
    if blind_qa.get("blind_qa_ready") and not (read_score is not None and float(read_score) >= OBSERVATION_BLIND_QA_READ_FEELING_TARGET):
        qa_gaps.append("observation_read_feeling_score_below_target")
    if _int(blind_qa.get("red_dimension_count")) > 0:
        qa_gaps.append("observation_blind_qa_red_dimension_detected")
    if regression_fixture_requested and not regression_fixture_coverage.get("step13_regression_fixture_coverage_ready"):
        qa_gaps.extend(list(regression_fixture_coverage.get("release_blockers") or []))

    summary = {
        "version": OBSERVATION_SCORECARD_BLIND_QA_VERSION,
        "schema_version": OBSERVATION_SCORECARD_BLIND_QA_VERSION,
        "source_step": OBSERVATION_SCORECARD_BLIND_QA_STEP,
        "step": OBSERVATION_SCORECARD_BLIND_QA_STEP,
        "run_id": _clean(run_id),
        "observation_scorecard_blind_qa_ready": bool(normalized_events and blind_qa.get("blind_qa_ready") and not qa_gaps),
        "step12_scorecard_blind_qa_ready": bool(normalized_events and blind_qa.get("blind_qa_ready") and not qa_gaps),
        "observation_scorecard_ready": bool(normalized_events),
        "observation_blind_qa_ready": bool(blind_qa.get("blind_qa_ready")),
        "event_count": len(normalized_events),
        "normal_input_count": len(normal_events),
        "safety_or_infra_excluded_count": len(normalized_events) - len(normal_events),
        "always_display_success_count": always_display_success_count,
        "always_display_rate": always_display_rate,
        "eligible_expected_count": len(expected_eligible),
        "eligible_observation_success_count": eligible_success_count,
        "eligible_observation_rate": eligible_observation_rate,
        "low_info_expected_count": len(expected_low_info),
        "low_info_observation_success_count": low_info_success_count,
        "low_info_observation_rate": low_info_observation_rate,
        "false_eligible_count": false_eligible_count,
        "false_eligible_rate": false_eligible_rate,
        "free_user_fact_violation_count": free_user_fact_violation_count,
        "overclaim_count": overclaim_count,
        "template_skeleton_repeat_count": template_skeleton_repeat_count,
        "template_skeleton_repeat_rate": template_skeleton_repeat_rate,
        "machine_metrics": {
            "version": OBSERVATION_SCORECARD_EVENT_VERSION,
            "source_step": OBSERVATION_SCORECARD_BLIND_QA_STEP,
            "event_count": len(normalized_events),
            "normal_input_count": len(normal_events),
            "always_display_rate": always_display_rate,
            "eligible_observation_rate": eligible_observation_rate,
            "low_info_observation_rate": low_info_observation_rate,
            "false_eligible_rate": false_eligible_rate,
            "free_user_fact_violation_count": free_user_fact_violation_count,
            "overclaim_count": overclaim_count,
            "template_skeleton_repeat_rate": template_skeleton_repeat_rate,
            "machine_metrics_used_for_read_feeling": False,
            "read_feeling_auto_filled_from_machine_metrics": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
        },
        "step12_observation_scorecard_ready": bool(normalized_events),
        "step13_observation_regression_fixture_coverage": regression_fixture_coverage,
        "step13_regression_fixture_coverage": regression_fixture_coverage,
        "observation_regression_fixture_coverage": regression_fixture_coverage,
        "step13_observation_regression_fixture_fields": regression_fixture_fields,
        "step13_regression_fixture_coverage_fields": regression_fixture_fields,
        "step13_observation_regression_fixture_coverage_ready": bool(
            regression_fixture_coverage.get("step13_regression_fixture_coverage_ready")
        ),
        "step13_regression_fixture_coverage_ready": bool(
            regression_fixture_coverage.get("step13_regression_fixture_coverage_ready")
        ),
        "observation_regression_fixture_coverage_version": OBSERVATION_REGRESSION_FIXTURE_COVERAGE_VERSION,
        "observation_regression_fixture_coverage_step": OBSERVATION_REGRESSION_FIXTURE_COVERAGE_STEP,
        "observation_regression_fixture_coverage_rate": regression_fixture_coverage.get("fixture_coverage_rate"),
        "observation_regression_fixture_success_coverage_rate": regression_fixture_coverage.get("fixture_success_coverage_rate"),
        "observation_regression_missing_fixture_groups": list(regression_fixture_coverage.get("missing_fixture_groups") or []),
        "observation_regression_failed_fixture_groups": list(regression_fixture_coverage.get("failed_fixture_groups") or []),
        "observation_regression_observed_fixture_groups": list(regression_fixture_coverage.get("observed_fixture_groups") or []),
        "observation_regression_release_blockers": list(regression_fixture_coverage.get("release_blockers") or []),
        "blind_qa": blind_qa,
        "blind_qa_metrics": blind_qa,
        "blind_qa_rubric": build_observation_blind_qa_rubric(),
        "read_feeling_score": read_score,
        "read_feeling_source": "observation_blind_qa_review_ratings" if blind_qa.get("blind_qa_ready") else "observation_blind_qa_required_not_evaluated",
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "events": normalized_events,
        "qa_gaps": _dedupe(qa_gaps),
        "release_blockers": _dedupe(qa_gaps),
        "targets": {
            "always_display_rate": OBSERVATION_ALWAYS_DISPLAY_TARGET,
            "eligible_observation_rate": OBSERVATION_ELIGIBLE_REPLY_TARGET,
            "low_info_observation_rate": OBSERVATION_LOW_INFO_REPLY_TARGET,
            "false_eligible_rate": OBSERVATION_FALSE_ELIGIBLE_TARGET,
            "free_user_fact_violation_count": 0,
            "overclaim_count": 0,
            "template_skeleton_repeat_rate": 0.0,
            "blind_qa_read_feeling_score": OBSERVATION_BLIND_QA_READ_FEELING_TARGET,
        },
        "product_gate_ready": False,
        "product_gate_reached": False,
        "product_gate_achieved": False,
        "product_gate_public_release_applied": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "gate_relaxed": False,
        "fixed_fallback_used": False,
        "external_ai_used": False,
        "local_llm_used": False,
    }
    assert_observation_scorecard_blind_qa_contract(summary, source="observation_scorecard_blind_qa_summary")
    return summary


def normalize_observation_scorecard_blind_qa_to_scorecard_fields(summary: Mapping[str, Any] | None) -> dict[str, Any]:
    data = _safe_mapping(summary)
    assert_observation_scorecard_blind_qa_contract(data, source="observation_scorecard_fields_source")
    return {
        "observation_scorecard_blind_qa_version": _clean(data.get("version")) or OBSERVATION_SCORECARD_BLIND_QA_VERSION,
        "observation_scorecard_blind_qa_step": _clean(data.get("step")) or OBSERVATION_SCORECARD_BLIND_QA_STEP,
        "step12_observation_scorecard_blind_qa_ready": bool(data.get("step12_scorecard_blind_qa_ready")),
        "observation_scorecard_ready": bool(data.get("observation_scorecard_ready")),
        "observation_blind_qa_ready": bool(data.get("observation_blind_qa_ready")),
        "always_display_rate": data.get("always_display_rate", 0.0),
        "eligible_observation_rate": data.get("eligible_observation_rate", 0.0),
        "low_info_observation_rate": data.get("low_info_observation_rate", 0.0),
        "false_eligible_rate": data.get("false_eligible_rate", 0.0),
        "free_user_fact_violation_count": data.get("free_user_fact_violation_count", 0),
        "overclaim_count": data.get("overclaim_count", 0),
        "template_skeleton_repeat_rate": data.get("template_skeleton_repeat_rate", 0.0),
        "observation_read_feeling_score": data.get("read_feeling_score"),
        "observation_regression_fixture_coverage_version": _clean(data.get("observation_regression_fixture_coverage_version")) or OBSERVATION_REGRESSION_FIXTURE_COVERAGE_VERSION,
        "observation_regression_fixture_coverage_step": _clean(data.get("observation_regression_fixture_coverage_step")) or OBSERVATION_REGRESSION_FIXTURE_COVERAGE_STEP,
        "step13_observation_regression_fixture_coverage_ready": bool(data.get("step13_observation_regression_fixture_coverage_ready")),
        "step13_regression_fixture_coverage_ready": bool(data.get("step13_regression_fixture_coverage_ready") or data.get("step13_observation_regression_fixture_coverage_ready")),
        "observation_regression_fixture_coverage_rate": data.get("observation_regression_fixture_coverage_rate", 0.0),
        "observation_regression_fixture_success_coverage_rate": data.get("observation_regression_fixture_success_coverage_rate", 0.0),
        "observation_regression_missing_fixture_groups": list(data.get("observation_regression_missing_fixture_groups") or []),
        "observation_regression_failed_fixture_groups": list(data.get("observation_regression_failed_fixture_groups") or []),
        "observation_regression_observed_fixture_groups": list(data.get("observation_regression_observed_fixture_groups") or []),
        "observation_regression_release_blockers": list(data.get("observation_regression_release_blockers") or []),
        "observation_qa_gaps": list(data.get("qa_gaps") or []),
        "observation_scorecard_blockers": list(data.get("release_blockers") or []),
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
    }


def dump_observation_scorecard_blind_qa(summary: Mapping[str, Any] | None = None) -> str:
    data = dict(summary or build_observation_scorecard_blind_qa(events=[], blind_qa_reviews=[]))
    data["raw_input_included"] = False
    data["raw_text_included"] = False
    data["comment_text_included"] = False
    data["comment_text_body_included"] = False
    assert_observation_scorecard_blind_qa_contract(data)
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


build_emlis_ai_observation_scorecard_blind_qa = build_observation_scorecard_blind_qa
build_observation_reply_scorecard_blind_qa = build_observation_scorecard_blind_qa

# ---------------------------------------------------------------------------
# ObservationReply Step12 compatibility / product-quality connection
# ---------------------------------------------------------------------------
# The canonical Step12 implementation above uses the shorter observation
# scorecard names.  Keep the explicit observation_reply names available for
# reply_service, product quality scorecard, and Step12 contract tests without
# changing public API/RN/DB contracts.

OBSERVATION_REPLY_SCORECARD_BLIND_QA_VERSION: Final = OBSERVATION_SCORECARD_BLIND_QA_VERSION
OBSERVATION_REPLY_SCORECARD_BLIND_QA_STEP: Final = OBSERVATION_SCORECARD_BLIND_QA_STEP
OBSERVATION_REPLY_SCORECARD_EVENT_VERSION: Final = OBSERVATION_SCORECARD_EVENT_VERSION
OBSERVATION_REPLY_BLIND_QA_RUBRIC_VERSION: Final = OBSERVATION_BLIND_QA_RUBRIC_VERSION
OBSERVATION_REPLY_BLIND_QA_REVIEW_VERSION: Final = "emlis.observation_reply_blind_qa_review.v1"
OBSERVATION_REPLY_MACHINE_METRICS_VERSION: Final = "emlis.observation_reply_machine_metrics.v1"


def assert_observation_reply_scorecard_meta_only(
    payload: Mapping[str, Any],
    *,
    source: str = "observation_reply_scorecard",
) -> None:
    assert_observation_scorecard_blind_qa_contract(payload, source=source)


def _reply_dimension_name(dimension: str) -> str:
    if dimension == "overclaim_absence":
        return "no_overclaim"
    return dimension


def build_observation_reply_blind_qa_rubric() -> dict[str, Any]:
    rubric = dict(build_observation_blind_qa_rubric())
    required = [_reply_dimension_name(item) for item in list(rubric.get("required_dimensions") or [])]
    rubric.update(
        {
            "version": OBSERVATION_REPLY_BLIND_QA_RUBRIC_VERSION,
            "schema_version": OBSERVATION_REPLY_BLIND_QA_RUBRIC_VERSION,
            "target_step": OBSERVATION_REPLY_SCORECARD_BLIND_QA_STEP,
            "source_step": OBSERVATION_REPLY_SCORECARD_BLIND_QA_STEP,
            "required_dimensions": required,
            "machine_metrics_are_separate": True,
            "machine_metrics_separated": True,
            "read_feeling_requires_blind_qa": True,
            "exact_comment_text_locked": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
        }
    )
    assert_observation_scorecard_blind_qa_contract(rubric, source="observation_reply_blind_qa_rubric")
    return rubric


def normalize_observation_reply_blind_qa_review(review: Mapping[str, Any] | None) -> dict[str, Any]:
    normalized = dict(normalize_observation_blind_qa_review(review))
    scores = dict(normalized.get("dimension_scores") or {})
    if "overclaim_absence" in scores and "no_overclaim" not in scores:
        scores["no_overclaim"] = scores["overclaim_absence"]
    normalized.update(
        {
            "version": OBSERVATION_REPLY_BLIND_QA_REVIEW_VERSION,
            "schema_version": OBSERVATION_REPLY_BLIND_QA_REVIEW_VERSION,
            "target_step": OBSERVATION_REPLY_SCORECARD_BLIND_QA_STEP,
            "source_step": OBSERVATION_REPLY_SCORECARD_BLIND_QA_STEP,
            "dimension_scores": scores,
            "ratings_only_payload": True,
            "machine_metrics_used_for_read_feeling": False,
            "read_feeling_auto_filled_from_machine_metrics": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
        }
    )
    assert_observation_scorecard_blind_qa_contract(normalized, source="observation_reply_blind_qa_review")
    return normalized


def normalize_observation_reply_scorecard_event(row: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    data = _strip_forbidden_text_payload_keys(_safe_mapping(row))
    if overrides:
        data.update(_strip_forbidden_text_payload_keys(overrides))
    normalized = dict(normalize_observation_scorecard_event(data))
    normalized.update(
        {
            "version": OBSERVATION_REPLY_SCORECARD_EVENT_VERSION,
            "schema_version": OBSERVATION_REPLY_SCORECARD_EVENT_VERSION,
            "target_step": OBSERVATION_REPLY_SCORECARD_BLIND_QA_STEP,
            "source_step": OBSERVATION_REPLY_SCORECARD_BLIND_QA_STEP,
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
        }
    )
    assert_observation_scorecard_blind_qa_contract(normalized, source="observation_reply_scorecard_event")
    return normalized


def _augment_observation_reply_scorecard(summary: Mapping[str, Any]) -> dict[str, Any]:
    data = _strip_forbidden_text_payload_keys(dict(summary or {}))
    machine_metrics = dict(data.get("machine_metrics") or {})
    machine_metrics.update(
        {
            "version": OBSERVATION_REPLY_MACHINE_METRICS_VERSION,
            "event_count": data.get("event_count", 0),
            "normal_input_count": data.get("normal_input_count", 0),
            "safety_or_infra_excluded_count": data.get("safety_or_infra_excluded_count", 0),
            "always_display_rate": data.get("always_display_rate", 0.0),
            "eligible_observation_rate": data.get("eligible_observation_rate", 0.0),
            "low_info_observation_rate": data.get("low_info_observation_rate", 0.0),
            "false_eligible_rate": data.get("false_eligible_rate", 0.0),
            "free_user_fact_violation_count": data.get("free_user_fact_violation_count", 0),
            "overclaim_count": data.get("overclaim_count", 0),
            "template_skeleton_repeat_rate": data.get("template_skeleton_repeat_rate", 0.0),
            "machine_metrics_used_for_read_feeling": False,
            "read_feeling_auto_filled_from_machine_metrics": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
        }
    )
    scorecard_ready = bool(data.get("observation_scorecard_ready"))
    blind_qa_ready = bool(data.get("observation_blind_qa_ready"))
    step12_ready = bool(data.get("step12_scorecard_blind_qa_ready"))
    data.update(
        {
            "version": OBSERVATION_REPLY_SCORECARD_BLIND_QA_VERSION,
            "schema_version": OBSERVATION_REPLY_SCORECARD_BLIND_QA_VERSION,
            "target_step": OBSERVATION_REPLY_SCORECARD_BLIND_QA_STEP,
            "source_step": OBSERVATION_REPLY_SCORECARD_BLIND_QA_STEP,
            "step": OBSERVATION_REPLY_SCORECARD_BLIND_QA_STEP,
            "scorecard_type": "observation_reply_scorecard_blind_qa",
            "scorecard_ready": scorecard_ready,
            "blind_qa_ready": blind_qa_ready,
            "step12_observation_scorecard_ready": scorecard_ready,
            "step12_observation_scorecard_blind_qa_ready": step12_ready,
            "step12_observation_reply_scorecard_ready": scorecard_ready,
            "machine_metrics": machine_metrics,
            "blind_qa_rubric": build_observation_reply_blind_qa_rubric(),
            "machine_metrics_separated_from_blind_qa": True,
            "machine_metrics_used_for_read_feeling": False,
            "read_feeling_auto_filled_from_machine_metrics": False,
            "product_gate_ready": False,
            "product_gate_reached": False,
            "product_gate_achieved": False,
            "public_release_applied": False,
            "product_gate_public_release_applied": False,
            "product_quality_released": False,
            "comment_text_generated": False,
            "comment_text_key_written": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
        }
    )
    assert_observation_scorecard_blind_qa_contract(data, source="observation_reply_scorecard")
    return data


def build_observation_reply_scorecard(
    *,
    scorecard_event: Mapping[str, Any] | None = None,
    scorecard_events: Iterable[Mapping[str, Any]] | None = None,
    rows: Iterable[Mapping[str, Any]] | None = None,
    events: Iterable[Mapping[str, Any]] | None = None,
    blind_qa_reviews: Iterable[Mapping[str, Any] | None] | None = None,
    run_id: str = "",
) -> dict[str, Any]:
    raw_events: list[Mapping[str, Any]] = []
    if scorecard_event is not None:
        raw_events.append(scorecard_event)
    raw_events.extend(list(scorecard_events or []))
    raw_events.extend(list(rows or []))
    raw_events.extend(list(events or []))
    safe_events = [normalize_observation_reply_scorecard_event(event) for event in raw_events]
    safe_reviews = [normalize_observation_reply_blind_qa_review(review) for review in list(blind_qa_reviews or [])]
    summary = build_observation_scorecard_blind_qa(events=safe_events, blind_qa_reviews=safe_reviews, run_id=run_id)
    return _augment_observation_reply_scorecard(summary)


def normalize_observation_reply_scorecard_to_product_quality_fields(summary: Mapping[str, Any] | None) -> dict[str, Any]:
    data = _augment_observation_reply_scorecard(
        summary or build_observation_scorecard_blind_qa(events=[], blind_qa_reviews=[])
    )
    base = normalize_observation_scorecard_blind_qa_to_scorecard_fields(data)
    return {
        **base,
        "observation_reply_scorecard_blind_qa_version": data.get("version") or OBSERVATION_REPLY_SCORECARD_BLIND_QA_VERSION,
        "observation_reply_scorecard_step": data.get("step") or OBSERVATION_REPLY_SCORECARD_BLIND_QA_STEP,
        "step12_observation_scorecard_ready": bool(data.get("step12_observation_scorecard_ready")),
        "step12_observation_scorecard_blind_qa_ready": bool(data.get("step12_observation_scorecard_blind_qa_ready")),
        "observation_scorecard_ready": bool(data.get("observation_scorecard_ready")),
        "observation_blind_qa_ready": bool(data.get("observation_blind_qa_ready")),
        "observation_always_display_rate": data.get("always_display_rate", 0.0),
        "observation_eligible_observation_rate": data.get("eligible_observation_rate", 0.0),
        "observation_low_info_observation_rate": data.get("low_info_observation_rate", 0.0),
        "observation_false_eligible_rate": data.get("false_eligible_rate", 0.0),
        "observation_free_user_fact_violation_count": data.get("free_user_fact_violation_count", 0),
        "observation_overclaim_count": data.get("overclaim_count", 0),
        "observation_template_skeleton_repeat_rate": data.get("template_skeleton_repeat_rate", 0.0),
        "observation_read_feeling_score": data.get("read_feeling_score"),
        "observation_release_blockers": list(data.get("release_blockers") or []),
        "observation_machine_metrics_used_for_read_feeling": False,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
    }


def dump_observation_reply_scorecard(scorecard: Mapping[str, Any] | None = None) -> str:
    data = _strip_forbidden_text_payload_keys(_safe_mapping(scorecard))
    if not data:
        data = build_observation_reply_scorecard(scorecard_events=[], blind_qa_reviews=[])
    assert_observation_scorecard_blind_qa_contract(data, source="observation_reply_scorecard_dump")
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def attach_observation_scorecard_blind_qa_meta(
    meta: Mapping[str, Any] | None,
    *,
    blind_qa_reviews: Iterable[Mapping[str, Any] | None] | None = None,
    run_id: str = "",
) -> dict[str, Any]:
    """Attach Step12 meta-only scorecard diagnostics to runtime meta.

    This does not generate or mutate public comment text and does not relax the
    Display Gate.  Runtime calls normally pass no Blind QA reviews, so machine
    metrics remain separated from read-feeling judgement.
    """

    payload = _strip_forbidden_text_payload_keys(_safe_mapping(meta))
    event = normalize_observation_reply_scorecard_event(payload)
    scorecard = build_observation_reply_scorecard(
        scorecard_events=[event],
        blind_qa_reviews=blind_qa_reviews or [],
        run_id=run_id or _clean(payload.get("trace_id")),
    )
    attached = dict(payload)
    attached["step12_observation_scorecard_blind_qa"] = scorecard
    attached["step12_observation_scorecard"] = scorecard
    diagnostic_summary = dict(_safe_mapping(attached.get("diagnostic_summary")))
    diagnostic_summary["step12_observation_scorecard_blind_qa"] = {
        "version": scorecard.get("version"),
        "step": scorecard.get("step"),
        "scorecard_ready": bool(scorecard.get("scorecard_ready")),
        "blind_qa_ready": bool(scorecard.get("blind_qa_ready")),
        "always_display_rate": scorecard.get("always_display_rate"),
        "eligible_observation_rate": scorecard.get("eligible_observation_rate"),
        "low_info_observation_rate": scorecard.get("low_info_observation_rate"),
        "false_eligible_rate": scorecard.get("false_eligible_rate"),
        "free_user_fact_violation_count": scorecard.get("free_user_fact_violation_count"),
        "overclaim_count": scorecard.get("overclaim_count"),
        "template_skeleton_repeat_rate": scorecard.get("template_skeleton_repeat_rate"),
        "machine_metrics_used_for_read_feeling": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
    }
    attached["diagnostic_summary"] = diagnostic_summary
    multi_perspective = dict(_safe_mapping(attached.get("multi_perspective")))
    multi_perspective["step12_observation_scorecard_blind_qa"] = diagnostic_summary["step12_observation_scorecard_blind_qa"]
    attached["multi_perspective"] = multi_perspective
    attached["step12_observation_scorecard_ready"] = bool(scorecard.get("scorecard_ready"))
    attached["observation_machine_metrics_used_for_read_feeling"] = False
    attached["machine_metrics_used_for_read_feeling"] = False
    attached["read_feeling_auto_filled_from_machine_metrics"] = False
    attached["comment_text_generated"] = False
    attached["comment_text_key_written"] = False
    attached["raw_input_included"] = False
    attached["raw_text_included"] = False
    attached["comment_text_included"] = False
    attached["comment_text_body_included"] = False
    assert_observation_scorecard_blind_qa_contract(attached, source="observation_scorecard_attach_meta")
    return attached


build_emlis_ai_observation_reply_scorecard = build_observation_reply_scorecard
build_observation_reply_scorecard_blind_qa = build_observation_reply_scorecard

__all__ = [
    "OBSERVATION_SCORECARD_BLIND_QA_VERSION",
    "OBSERVATION_SCORECARD_BLIND_QA_STEP",
    "OBSERVATION_BLIND_QA_REVIEW_VERSION",
    "OBSERVATION_BLIND_QA_RUBRIC_VERSION",
    "OBSERVATION_SCORECARD_EVENT_VERSION",
    "OBSERVATION_BLIND_QA_REQUIRED_DIMENSIONS",
    "OBSERVATION_REPLY_SCORECARD_BLIND_QA_VERSION",
    "OBSERVATION_REPLY_SCORECARD_BLIND_QA_STEP",
    "OBSERVATION_REPLY_SCORECARD_EVENT_VERSION",
    "OBSERVATION_REPLY_BLIND_QA_RUBRIC_VERSION",
    "OBSERVATION_REPLY_BLIND_QA_REVIEW_VERSION",
    "OBSERVATION_REPLY_MACHINE_METRICS_VERSION",
    "assert_observation_scorecard_blind_qa_contract",
    "assert_observation_reply_scorecard_meta_only",
    "extract_observation_reply_meta",
    "normalize_observation_scorecard_event",
    "normalize_observation_reply_scorecard_event",
    "normalize_observation_blind_qa_review",
    "normalize_observation_reply_blind_qa_review",
    "aggregate_observation_blind_qa_reviews",
    "build_observation_blind_qa_rubric",
    "build_observation_reply_blind_qa_rubric",
    "build_observation_scorecard_blind_qa",
    "build_emlis_ai_observation_scorecard_blind_qa",
    "build_observation_reply_scorecard",
    "build_emlis_ai_observation_reply_scorecard",
    "build_observation_reply_scorecard_blind_qa",
    "normalize_observation_scorecard_blind_qa_to_scorecard_fields",
    "normalize_observation_reply_scorecard_to_product_quality_fields",
    "dump_observation_scorecard_blind_qa",
    "dump_observation_reply_scorecard",
    "attach_observation_scorecard_blind_qa_meta",
]

