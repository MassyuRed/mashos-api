# -*- coding: utf-8 -*-
from __future__ import annotations

"""P5-5 ratings-only Product Quality review for User Label Connection.

This module aggregates body-free numeric review ratings for P5 history-line
experience quality.  It does not retain reviewer free text, raw input,
``comment_text`` bodies, command output, or visible text, and it never converts
quality pass into public release.
"""

from collections.abc import Iterable, Mapping, Sequence
import json
from typing import Any, Final

from emlis_ai_user_label_connection_p5_safety_guard import (
    DECISION_ALLOW as P5_SAFETY_DECISION_ALLOW,
    assert_user_label_connection_p5_safety_guard_contract,
)


USER_LABEL_CONNECTION_P5_PRODUCT_QUALITY_REVIEW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.user_label_connection.p5_product_quality_review.v1"
)
USER_LABEL_CONNECTION_P5_PRODUCT_QUALITY_REVIEW_STEP: Final = (
    "P5-5_ProductQualityQA_RatingsOnlyReview"
)
USER_LABEL_CONNECTION_P5_PRODUCT_QUALITY_REVIEW_SOURCE: Final = (
    "Cocolon_EmlisAI_P5_UserLabelConnection_ProductQualityQA_RatingsOnlyReview_20260611"
)

DIMENSION_HISTORY_CONNECTION_NATURALNESS: Final = "history_connection_naturalness"
DIMENSION_CREEPY_ABSENCE: Final = "creepy_absence"
DIMENSION_OVERCLAIM_ABSENCE: Final = "overclaim_absence"
DIMENSION_SELF_BLAME_NON_AMPLIFICATION: Final = "self_blame_non_amplification"
DIMENSION_CURRENT_INPUT_NOT_MASKED_BY_HISTORY: Final = "current_input_not_masked_by_history"
DIMENSION_NON_TEMPLATE: Final = "non_template"
DIMENSION_SELF_INFORMATION_ORGANIZED: Final = "self_information_organized"
DIMENSION_WANTS_MORE_INPUT_OR_ACCUMULATION: Final = "wants_more_input_or_accumulation"
DIMENSION_SUBSCRIPTION_BOUNDARY_CORRECTNESS: Final = "subscription_boundary_correctness"
DIMENSION_NO_RAW_TEXT_META: Final = "no_raw_text_meta"

REQUIRED_DIMENSIONS: Final[tuple[str, ...]] = (
    DIMENSION_HISTORY_CONNECTION_NATURALNESS,
    DIMENSION_CREEPY_ABSENCE,
    DIMENSION_OVERCLAIM_ABSENCE,
    DIMENSION_SELF_BLAME_NON_AMPLIFICATION,
    DIMENSION_CURRENT_INPUT_NOT_MASKED_BY_HISTORY,
    DIMENSION_NON_TEMPLATE,
    DIMENSION_SELF_INFORMATION_ORGANIZED,
    DIMENSION_WANTS_MORE_INPUT_OR_ACCUMULATION,
    DIMENSION_SUBSCRIPTION_BOUNDARY_CORRECTNESS,
    DIMENSION_NO_RAW_TEXT_META,
)
DIMENSION_TARGETS: Final[dict[str, float]] = {
    DIMENSION_HISTORY_CONNECTION_NATURALNESS: 0.90,
    DIMENSION_CREEPY_ABSENCE: 0.95,
    DIMENSION_OVERCLAIM_ABSENCE: 0.95,
    DIMENSION_SELF_BLAME_NON_AMPLIFICATION: 0.95,
    DIMENSION_CURRENT_INPUT_NOT_MASKED_BY_HISTORY: 0.95,
    DIMENSION_NON_TEMPLATE: 0.90,
    DIMENSION_SELF_INFORMATION_ORGANIZED: 0.90,
    DIMENSION_WANTS_MORE_INPUT_OR_ACCUMULATION: 0.85,
    DIMENSION_SUBSCRIPTION_BOUNDARY_CORRECTNESS: 1.0,
    DIMENSION_NO_RAW_TEXT_META: 1.0,
}

BLOCKER_NO_REVIEW_ROWS: Final = "ratings_only_review_rows_missing"
BLOCKER_P5_SAFETY_GUARD_NOT_ALLOWED: Final = "p5_safety_guard_not_allowed"
BLOCKER_DIMENSION_MISSING: Final = "dimension_rating_missing"
BLOCKER_DIMENSION_BELOW_TARGET: Final = "dimension_below_target"
BLOCKER_RAW_TEXT_PAYLOAD_DETECTED: Final = "raw_text_payload_detected"
BLOCKER_REVIEWER_FREE_TEXT_DETECTED: Final = "reviewer_free_text_detected"
BLOCKER_CONTRACT_MUTATION_DETECTED: Final = "contract_mutation_detected"
BLOCKER_MACHINE_METRIC_AUTOFILL_DETECTED: Final = "machine_metric_autofill_detected"

_DIMENSION_ALIASES: Final[dict[str, str]] = {
    "history_connection_naturalness": DIMENSION_HISTORY_CONNECTION_NATURALNESS,
    "history_naturalness": DIMENSION_HISTORY_CONNECTION_NATURALNESS,
    "creepy_absence": DIMENSION_CREEPY_ABSENCE,
    "not_creepy": DIMENSION_CREEPY_ABSENCE,
    "creepiness_absence": DIMENSION_CREEPY_ABSENCE,
    "overclaim_absence": DIMENSION_OVERCLAIM_ABSENCE,
    "no_overclaim": DIMENSION_OVERCLAIM_ABSENCE,
    "self_blame_non_amplification": DIMENSION_SELF_BLAME_NON_AMPLIFICATION,
    "self_blame_absence": DIMENSION_SELF_BLAME_NON_AMPLIFICATION,
    "current_input_not_masked_by_history": DIMENSION_CURRENT_INPUT_NOT_MASKED_BY_HISTORY,
    "current_not_masked": DIMENSION_CURRENT_INPUT_NOT_MASKED_BY_HISTORY,
    "non_template": DIMENSION_NON_TEMPLATE,
    "not_template": DIMENSION_NON_TEMPLATE,
    "self_information_organized": DIMENSION_SELF_INFORMATION_ORGANIZED,
    "self_info_organized": DIMENSION_SELF_INFORMATION_ORGANIZED,
    "wants_more_input_or_accumulation": DIMENSION_WANTS_MORE_INPUT_OR_ACCUMULATION,
    "accumulation_motivation": DIMENSION_WANTS_MORE_INPUT_OR_ACCUMULATION,
    "want_more_input": DIMENSION_WANTS_MORE_INPUT_OR_ACCUMULATION,
    "subscription_boundary_correctness": DIMENSION_SUBSCRIPTION_BOUNDARY_CORRECTNESS,
    "subscription_boundary": DIMENSION_SUBSCRIPTION_BOUNDARY_CORRECTNESS,
    "no_raw_text_meta": DIMENSION_NO_RAW_TEXT_META,
    "raw_text_meta_absence": DIMENSION_NO_RAW_TEXT_META,
}
_VERDICT_SCORES: Final[dict[str, float]] = {
    "green": 1.0,
    "g": 1.0,
    "pass": 1.0,
    "passed": 1.0,
    "ok": 1.0,
    "yellow": 0.65,
    "y": 0.65,
    "warn": 0.65,
    "warning": 0.65,
    "review": 0.55,
    "repair": 0.45,
    "repair_required": 0.45,
    "red": 0.0,
    "r": 0.0,
    "fail": 0.0,
    "failed": 0.0,
    "ng": 0.0,
}

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
        "review_notes",
        "free_text_note",
        "reviewer_free_text",
        "blind_qa_free_text",
        "body",
        "text",
    }
)
_REVIEWER_FREE_TEXT_KEYS: Final[frozenset[str]] = frozenset(
    {"reviewer_note", "reviewer_notes", "review_notes", "free_text_note", "reviewer_free_text", "blind_qa_free_text"}
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
        "rn_contract_changed",
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
        "machine_metrics_used_for_read_feeling",
        "read_feeling_auto_filled_from_machine_metrics",
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
        "product_gate_ready",
        "product_gate_reached",
        "product_gate_public_release_applied",
        "product_quality_released",
        "p5_visible_surface_strengthened",
        "p5_runtime_change_applied",
        "external_ai_used",
        "local_llm_used",
    }
)


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).strip()


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
        return [value]
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


def _score(value: Any) -> float | None:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return max(0.0, min(1.0, round(float(value), 4)))
    text = _clean(value).lower()
    if not text:
        return None
    if text in _VERDICT_SCORES:
        return _VERDICT_SCORES[text]
    try:
        number = float(text)
    except ValueError:
        return None
    if number > 1.0 and number <= 100.0:
        number = number / 100.0
    return max(0.0, min(1.0, round(number, 4)))


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


def _contains_reviewer_free_text_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in _REVIEWER_FREE_TEXT_KEYS:
                return True
            if _contains_reviewer_free_text_key(child):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_contains_reviewer_free_text_key(child) for child in value)
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


def _dimension_scores_from_row(row: Mapping[str, Any]) -> dict[str, float]:
    scores: dict[str, float] = {}
    candidates = [
        _safe_mapping(row.get("ratings")),
        _safe_mapping(row.get("dimension_scores")),
        _safe_mapping(row.get("dimensions")),
        row,
    ]
    for source in candidates:
        for key, value in source.items():
            dimension = _DIMENSION_ALIASES.get(str(key))
            if not dimension:
                continue
            score = _score(value)
            if score is not None:
                scores[dimension] = score
    return scores


def _average(values: Sequence[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 4)


def _dimension_averages(rows: Sequence[Mapping[str, Any]]) -> tuple[dict[str, float | None], dict[str, int]]:
    buckets: dict[str, list[float]] = {dimension: [] for dimension in REQUIRED_DIMENSIONS}
    for row in rows:
        scores = _dimension_scores_from_row(row)
        for dimension, score in scores.items():
            if dimension in buckets:
                buckets[dimension].append(score)
    averages = {dimension: _average(values) for dimension, values in buckets.items()}
    counts = {dimension: len(values) for dimension, values in buckets.items()}
    return averages, counts


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
    }


def build_user_label_connection_p5_product_quality_review(
    *,
    p5_safety_guard: Mapping[str, Any] | None = None,
    review_rows: Sequence[Mapping[str, Any] | None] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Build a ratings-only P5 product quality review summary."""

    guard = _safe_mapping(p5_safety_guard)
    if guard:
        assert_user_label_connection_p5_safety_guard_contract(guard, allow_partial=True)

    rows = [row for row in (_listify(review_rows) if review_rows is not None else []) if isinstance(row, Mapping)]
    sources = [guard, *rows]
    unsafe_payload = any(_contains_text_payload_key(source) for source in sources)
    reviewer_free_text = any(_contains_reviewer_free_text_key(source) for source in sources)
    contract_mutation = any(_flag_true(source) for source in sources)
    machine_autofill = any(
        source.get("machine_metrics_used_for_read_feeling") is True
        or source.get("read_feeling_auto_filled_from_machine_metrics") is True
        for source in sources
        if isinstance(source, Mapping)
    )

    averages, counts = _dimension_averages(rows)
    blocker_reason_codes: list[str] = []
    if not rows:
        blocker_reason_codes.append(BLOCKER_NO_REVIEW_ROWS)
    if guard.get("decision") != P5_SAFETY_DECISION_ALLOW or guard.get("allow_limited_visible_candidate") is not True:
        blocker_reason_codes.append(BLOCKER_P5_SAFETY_GUARD_NOT_ALLOWED)
        blocker_reason_codes.extend(f"p5_safety_guard:{reason}" for reason in _dedupe(guard.get("rejection_reasons")))
    if unsafe_payload:
        blocker_reason_codes.append(BLOCKER_RAW_TEXT_PAYLOAD_DETECTED)
    if reviewer_free_text:
        blocker_reason_codes.append(BLOCKER_REVIEWER_FREE_TEXT_DETECTED)
    if contract_mutation:
        blocker_reason_codes.append(BLOCKER_CONTRACT_MUTATION_DETECTED)
    if machine_autofill:
        blocker_reason_codes.append(BLOCKER_MACHINE_METRIC_AUTOFILL_DETECTED)
    for dimension in REQUIRED_DIMENSIONS:
        average = averages.get(dimension)
        if average is None:
            blocker_reason_codes.append(f"{BLOCKER_DIMENSION_MISSING}:{dimension}")
            continue
        target = DIMENSION_TARGETS[dimension]
        if average < target:
            blocker_reason_codes.append(f"{BLOCKER_DIMENSION_BELOW_TARGET}:{dimension}")
    blocker_reason_codes = _dedupe(blocker_reason_codes)

    p5_limited_visible_allowed = bool(rows and not blocker_reason_codes)
    summary = {
        "schema_version": USER_LABEL_CONNECTION_P5_PRODUCT_QUALITY_REVIEW_SCHEMA_VERSION,
        "version": USER_LABEL_CONNECTION_P5_PRODUCT_QUALITY_REVIEW_SCHEMA_VERSION,
        "step": USER_LABEL_CONNECTION_P5_PRODUCT_QUALITY_REVIEW_STEP,
        "source": USER_LABEL_CONNECTION_P5_PRODUCT_QUALITY_REVIEW_SOURCE,
        "run_id": run_id or "p5_product_quality_review",
        "ratings_only": True,
        "review_count": len(rows),
        "dimension_averages": averages,
        "dimension_rating_counts": counts,
        "dimension_targets": dict(DIMENSION_TARGETS),
        "blocker_reason_codes": blocker_reason_codes,
        "p5_limited_visible_allowed": p5_limited_visible_allowed,
        "p5_safety_guard_allowed": guard.get("decision") == P5_SAFETY_DECISION_ALLOW and guard.get("allow_limited_visible_candidate") is True,
        "body_free_case_references_only": True,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "fixed_sentence_template_added": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "release_allowed": False,
        "public_contract": _public_contract(),
        "body_free": _body_free_contract(),
    }
    assert_user_label_connection_p5_product_quality_review_contract(summary)
    return summary


def user_label_connection_p5_product_quality_review_public_summary(value: Mapping[str, Any] | None) -> dict[str, Any]:
    meta = _safe_mapping(value)
    summary = {
        "schema_version": USER_LABEL_CONNECTION_P5_PRODUCT_QUALITY_REVIEW_SCHEMA_VERSION,
        "step": USER_LABEL_CONNECTION_P5_PRODUCT_QUALITY_REVIEW_STEP,
        "ratings_only": True,
        "review_count": max(0, int(meta.get("review_count") or 0)),
        "blocker_reason_codes": _dedupe(meta.get("blocker_reason_codes")),
        "p5_limited_visible_allowed": meta.get("p5_limited_visible_allowed") is True,
        "public_meta_summary_only": True,
        "public_response_key_added": False,
        "response_shape_changed": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "history_raw_text_included": False,
        "reviewer_free_text_included": False,
        "release_allowed": False,
    }
    assert_user_label_connection_p5_product_quality_review_contract(summary, allow_partial=True)
    return summary


def assert_user_label_connection_p5_product_quality_review_contract(value: Any, *, allow_partial: bool = False) -> None:
    if _contains_text_payload_key(value):
        raise ValueError("P5 product quality review must not include raw text/comment/reviewer payload keys")
    if _flag_true(value):
        raise ValueError("P5 product quality review contains a forbidden true flag")
    json.dumps(value, ensure_ascii=False, sort_keys=True)
    if allow_partial:
        return
    if not isinstance(value, Mapping):
        raise ValueError("P5 product quality review must be a mapping")
    if value.get("schema_version") != USER_LABEL_CONNECTION_P5_PRODUCT_QUALITY_REVIEW_SCHEMA_VERSION:
        raise ValueError("unexpected P5 product quality review schema_version")
    if value.get("step") != USER_LABEL_CONNECTION_P5_PRODUCT_QUALITY_REVIEW_STEP:
        raise ValueError("unexpected P5 product quality review step")
    if value.get("ratings_only") is not True:
        raise ValueError("P5 product quality review must be ratings_only")
    averages = _safe_mapping(value.get("dimension_averages"))
    for dimension in REQUIRED_DIMENSIONS:
        if dimension not in averages:
            raise ValueError(f"P5 product quality review missing dimension average: {dimension}")
    public_contract = _safe_mapping(value.get("public_contract"))
    body_free = _safe_mapping(value.get("body_free"))
    for key in ("rn_visible_contract_changed", "public_response_key_added", "response_shape_changed", "db_schema_changed", "release_allowed", "public_release_applied", "product_quality_released"):
        if public_contract.get(key) is not False:
            raise ValueError(f"P5 product quality public_contract.{key} must be false")
    for key in ("raw_text_included", "comment_text_body_included", "candidate_body_included", "surface_body_included", "history_raw_text_included", "reviewer_free_text_included"):
        if body_free.get(key) is not False:
            raise ValueError(f"P5 product quality body_free.{key} must be false")


__all__ = [
    "USER_LABEL_CONNECTION_P5_PRODUCT_QUALITY_REVIEW_SCHEMA_VERSION",
    "USER_LABEL_CONNECTION_P5_PRODUCT_QUALITY_REVIEW_STEP",
    "USER_LABEL_CONNECTION_P5_PRODUCT_QUALITY_REVIEW_SOURCE",
    "REQUIRED_DIMENSIONS",
    "DIMENSION_TARGETS",
    "build_user_label_connection_p5_product_quality_review",
    "user_label_connection_p5_product_quality_review_public_summary",
    "assert_user_label_connection_p5_product_quality_review_contract",
]
