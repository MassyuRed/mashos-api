# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 9 Product Quality QA / Blind QA for User Label Connection.

This module evaluates whether the limited visible history-line connection is
moving toward the intended product experience: being read, organizing self
information, and making the user want to keep accumulating Cocolon records.
It is deliberately a QA material layer only.  It does not generate or store
``comment_text`` bodies, does not add public response keys, does not change
RN/API/DB contracts, and does not convert pytest green into product success.
"""

from collections.abc import Iterable, Mapping, Sequence
import json
from typing import Any, Final

try:  # Keep this module usable in the same flat import style as ai_inference tests.
    from emlis_ai_user_label_connection_surface import (
        CONNECTABLE_FAMILY_LONG_MEANING_ARC,
        CONNECTABLE_FAMILY_SELF_UNDERSTANDING_FOLLOW,
        CONNECTABLE_FAMILY_STRUCTURE_QUESTION,
        USER_LABEL_CONNECTION_VISIBLE_SURFACE_PHASE,
        USER_LABEL_CONNECTION_VISIBLE_SURFACE_SCHEMA_VERSION,
        USER_LABEL_CONNECTION_VISIBLE_SURFACE_STEP,
    )
except Exception:  # pragma: no cover - defensive fallback for standalone linting.
    CONNECTABLE_FAMILY_LONG_MEANING_ARC = "long_meaning_arc"
    CONNECTABLE_FAMILY_SELF_UNDERSTANDING_FOLLOW = "self_understanding_follow"
    CONNECTABLE_FAMILY_STRUCTURE_QUESTION = "structure_question"
    USER_LABEL_CONNECTION_VISIBLE_SURFACE_PHASE = "Phase8_LimitedVisibleSurfaceConnection"
    USER_LABEL_CONNECTION_VISIBLE_SURFACE_SCHEMA_VERSION = "cocolon.emlis.user_label_connection.visible_surface_connection.v1"
    USER_LABEL_CONNECTION_VISIBLE_SURFACE_STEP = "UserLabelConnection_LimitedVisibleSurfaceConnection_v1"

USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_SCHEMA_VERSION: Final = (
    "cocolon.emlis.user_label_connection.product_quality_qa.v1"
)
USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_CANDIDATE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.user_label_connection.product_quality_qa_candidate.v1"
)
USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_REVIEW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.user_label_connection.product_quality_qa_review.v1"
)
USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_STEP: Final = "UserLabelConnection_ProductQualityQA_BlindQA_v1"
USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_PHASE: Final = "Phase9_ProductQualityQA_BlindQA"

DIMENSION_READ_FEELING: Final = "read_feeling"
DIMENSION_SELF_INFORMATION_ORGANIZED: Final = "self_information_organized"
DIMENSION_HISTORY_CONNECTION_NATURALNESS: Final = "history_connection_naturalness"
DIMENSION_CREEPY_ABSENCE: Final = "creepy_absence"
DIMENSION_OVERCLAIM_ABSENCE: Final = "overclaim_absence"
DIMENSION_SELF_BLAME_NON_AMPLIFICATION: Final = "self_blame_non_amplification"
DIMENSION_WANTS_MORE_INPUT_OR_ACCUMULATION: Final = "wants_more_input_or_accumulation"
DIMENSION_NON_SHALLOW_REPEAT: Final = "non_shallow_repeat"

USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_REQUIRED_DIMENSIONS: Final = (
    DIMENSION_READ_FEELING,
    DIMENSION_SELF_INFORMATION_ORGANIZED,
    DIMENSION_HISTORY_CONNECTION_NATURALNESS,
    DIMENSION_CREEPY_ABSENCE,
    DIMENSION_OVERCLAIM_ABSENCE,
    DIMENSION_SELF_BLAME_NON_AMPLIFICATION,
    DIMENSION_WANTS_MORE_INPUT_OR_ACCUMULATION,
    DIMENSION_NON_SHALLOW_REPEAT,
)
USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_TARGET: Final = 0.90
USER_LABEL_CONNECTION_PRODUCT_QUALITY_REVIEW_COVERAGE_TARGET: Final = 1.0

BLOCKER_NO_REVIEWABLE_CANDIDATES: Final = "no_reviewable_user_label_connection_candidates"
BLOCKER_BLIND_QA_REVIEW_REQUIRED: Final = "blind_qa_review_required"
BLOCKER_REVIEW_COVERAGE_BELOW_TARGET: Final = "blind_qa_review_coverage_below_target"
BLOCKER_READ_FEELING_BELOW_TARGET: Final = "read_feeling_below_product_quality_target"
BLOCKER_SELF_INFORMATION_ORGANIZATION_BELOW_TARGET: Final = "self_information_organization_below_target"
BLOCKER_HISTORY_CONNECTION_CREEPY_RISK: Final = "history_connection_creepiness_risk"
BLOCKER_HISTORY_CONNECTION_NATURALNESS_BELOW_TARGET: Final = "history_connection_naturalness_below_target"
BLOCKER_OVERCLAIM_OR_DECIDING_RISK: Final = "overclaim_or_deciding_risk"
BLOCKER_SELF_BLAME_AMPLIFICATION_RISK: Final = "self_blame_amplification_risk"
BLOCKER_ACCUMULATION_MOTIVATION_NOT_CONFIRMED: Final = "accumulation_motivation_not_confirmed"
BLOCKER_SHALLOW_REPEAT_RISK: Final = "shallow_repeat_risk"
BLOCKER_TEXT_PAYLOAD_DETECTED: Final = "product_quality_qa_text_payload_detected"
BLOCKER_CONTRACT_RELAXATION_DETECTED: Final = "product_quality_qa_contract_relaxation_detected"
BLOCKER_NON_LIMITED_VISIBLE_CONNECTION: Final = "non_limited_visible_connection"

_LIMITED_CONNECTABLE_FAMILIES: Final = frozenset(
    {
        CONNECTABLE_FAMILY_STRUCTURE_QUESTION,
        CONNECTABLE_FAMILY_LONG_MEANING_ARC,
        CONNECTABLE_FAMILY_SELF_UNDERSTANDING_FOLLOW,
    }
)

_TEXT_PAYLOAD_KEYS: Final = frozenset(
    {
        "raw_input",
        "rawInput",
        "raw_text",
        "rawText",
        "raw_user_text",
        "rawUserText",
        "source_text",
        "sourceText",
        "input",
        "input_text",
        "inputText",
        "user_input",
        "userInput",
        "current_input",
        "currentInput",
        "history_input",
        "historyInput",
        "memo",
        "memo_text",
        "memoText",
        "memo_action",
        "memoAction",
        "memo_action_text",
        "memoActionText",
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
        "realized_text",
        "realizedText",
        "display_text",
        "displayText",
        "observation_text",
        "reception_text",
        "body",
        "text",
    }
)
_FORBIDDEN_TRUE_FLAGS: Final = frozenset(
    {
        "api_route_changed",
        "request_key_changed",
        "response_shape_changed",
        "public_response_key_added",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "raw_input_included",
        "raw_text_included",
        "history_raw_text_included",
        "raw_fact_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "surface_text_body_included",
        "diagnosis_allowed",
        "personality_claim_allowed",
        "cause_claim_allowed",
        "advice_allowed",
        "future_prediction_allowed",
        "always_claim_allowed",
        "should_statement_allowed",
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "reader_gate_relaxed",
        "template_gate_relaxed",
        "gate_relaxed",
        "product_gate_ready",
        "product_gate_reached",
        "product_gate_public_release_applied",
        "product_quality_released",
        "public_release_applied",
        "machine_metrics_used_for_read_feeling",
        "read_feeling_auto_filled_from_machine_metrics",
        "fixed_sentence_template_added",
        "fixed_sentence_template_used",
        "input_specific_template_added",
        "external_ai_used",
        "local_llm_used",
    }
)

_DIMENSION_ALIASES: Final = {
    "read_feeling": DIMENSION_READ_FEELING,
    "read_feeling_score": DIMENSION_READ_FEELING,
    "read": DIMENSION_READ_FEELING,
    "読まれた感": DIMENSION_READ_FEELING,
    "self_information_organized": DIMENSION_SELF_INFORMATION_ORGANIZED,
    "self_info_organized": DIMENSION_SELF_INFORMATION_ORGANIZED,
    "self_information_arranged": DIMENSION_SELF_INFORMATION_ORGANIZED,
    "自己情報整理": DIMENSION_SELF_INFORMATION_ORGANIZED,
    "history_connection_naturalness": DIMENSION_HISTORY_CONNECTION_NATURALNESS,
    "history_naturalness": DIMENSION_HISTORY_CONNECTION_NATURALNESS,
    "履歴自然さ": DIMENSION_HISTORY_CONNECTION_NATURALNESS,
    "creepy_absence": DIMENSION_CREEPY_ABSENCE,
    "not_creepy": DIMENSION_CREEPY_ABSENCE,
    "creepiness_absence": DIMENSION_CREEPY_ABSENCE,
    "気味悪さなし": DIMENSION_CREEPY_ABSENCE,
    "overclaim_absence": DIMENSION_OVERCLAIM_ABSENCE,
    "no_overclaim": DIMENSION_OVERCLAIM_ABSENCE,
    "no_deciding": DIMENSION_OVERCLAIM_ABSENCE,
    "決めつけなし": DIMENSION_OVERCLAIM_ABSENCE,
    "self_blame_non_amplification": DIMENSION_SELF_BLAME_NON_AMPLIFICATION,
    "self_blame_absence": DIMENSION_SELF_BLAME_NON_AMPLIFICATION,
    "no_self_blame_amplification": DIMENSION_SELF_BLAME_NON_AMPLIFICATION,
    "自己責め増幅なし": DIMENSION_SELF_BLAME_NON_AMPLIFICATION,
    "wants_more_input_or_accumulation": DIMENSION_WANTS_MORE_INPUT_OR_ACCUMULATION,
    "accumulation_motivation": DIMENSION_WANTS_MORE_INPUT_OR_ACCUMULATION,
    "want_more_input": DIMENSION_WANTS_MORE_INPUT_OR_ACCUMULATION,
    "もっと入力したい": DIMENSION_WANTS_MORE_INPUT_OR_ACCUMULATION,
    "non_shallow_repeat": DIMENSION_NON_SHALLOW_REPEAT,
    "not_shallow_repeat": DIMENSION_NON_SHALLOW_REPEAT,
    "no_shallow_repeat": DIMENSION_NON_SHALLOW_REPEAT,
    "浅い復唱なし": DIMENSION_NON_SHALLOW_REPEAT,
}
_VERDICT_SCORES: Final = {
    "green": 1.0,
    "g": 1.0,
    "pass": 1.0,
    "passed": 1.0,
    "ok": 1.0,
    "product_pass": 1.0,
    "yellow": 0.65,
    "y": 0.65,
    "warn": 0.65,
    "warning": 0.65,
    "repair": 0.45,
    "repair_required": 0.45,
    "red": 0.0,
    "r": 0.0,
    "fail": 0.0,
    "failed": 0.0,
    "ng": 0.0,
}


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).replace("\u3000", " ").strip()


def _safe_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    as_meta = getattr(value, "as_meta", None)
    if callable(as_meta):
        try:
            meta = as_meta()
            if isinstance(meta, Mapping):
                return {str(key): item for key, item in meta.items()}
        except Exception:
            return {}
    return {}


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, (tuple, set)):
        return list(value)
    return [value]


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in _listify(values):
        text = _clean(value)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        if isinstance(value, bool):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        if isinstance(value, bool):
            return None
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return None


def _score(value: Any) -> float | None:
    text = _clean(value).lower().replace(" ", "_").replace("-", "_")
    if text in _VERDICT_SCORES:
        return _VERDICT_SCORES[text]
    return _float(value)


def _avg(values: Iterable[Any]) -> float | None:
    scores: list[float] = []
    for value in values:
        score = _score(value)
        if score is not None:
            scores.append(score)
    if not scores:
        return None
    return round(sum(scores) / len(scores), 4)


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(max(0.0, min(1.0, float(numerator) / float(denominator))), 4)


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


def _strip_text_payload_keys(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _strip_text_payload_keys(child)
            for key, child in value.items()
            if str(key) not in _TEXT_PAYLOAD_KEYS
        }
    if isinstance(value, list):
        return [_strip_text_payload_keys(child) for child in value]
    if isinstance(value, tuple):
        return [_strip_text_payload_keys(child) for child in value]
    if isinstance(value, set):
        return [_strip_text_payload_keys(child) for child in value]
    return value


def _forbidden_true_flag(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in _FORBIDDEN_TRUE_FLAGS and child is True:
                return True
            if _forbidden_true_flag(child):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_forbidden_true_flag(child) for child in value)
    return False


def assert_user_label_connection_product_quality_qa_meta_only(value: Any, *, source: str = "user_label_connection_product_quality_qa") -> None:
    """Keep Phase 9 QA objects ratings/counts/booleans only."""

    if _contains_text_payload_key(value):
        raise ValueError(f"{source} must not include raw input/comment/surface body keys")
    if _forbidden_true_flag(value):
        raise ValueError(f"{source} must not relax contracts or turn release/public flags on")
    json.dumps(value, ensure_ascii=False, sort_keys=True)


def _source_id(event: Mapping[str, Any], index: int) -> str:
    for key in ("candidate_id", "row_id", "trace_id", "event_id", "emotion_log_id"):
        value = _clean(event.get(key))
        if value:
            return value[:96]
    return f"ulc-phase9-{index + 1:03d}"


def _visible_meta_from_event(event: Mapping[str, Any]) -> dict[str, Any]:
    for key in (
        "user_label_connection_visible_surface",
        "visible_surface_meta",
        "phase8_limited_visible_surface_connection",
        "user_label_connection",
    ):
        meta = _safe_mapping(event.get(key))
        if meta:
            return meta
    if event.get("schema_version") == USER_LABEL_CONNECTION_VISIBLE_SURFACE_SCHEMA_VERSION:
        return _safe_mapping(event)
    return {}


def _event_has_contract_relaxation(event: Mapping[str, Any]) -> bool:
    return _forbidden_true_flag(event)


def build_user_label_connection_product_quality_qa_candidates(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Build Blind QA candidates from Phase 8 visible-surface metadata.

    Candidate rows intentionally keep row id, coverage/classification, safe
    booleans, counts, and family identifiers only.  Public/visible text bodies
    are stripped before the row is normalized.
    """

    candidates: list[dict[str, Any]] = []
    for index, raw_event in enumerate(events):
        source_event = _safe_mapping(raw_event)
        text_payload_stripped = _contains_text_payload_key(source_event)
        safe_event = _safe_mapping(_strip_text_payload_keys(source_event))
        visible_meta = _visible_meta_from_event(safe_event)
        if not visible_meta and raw_event.get("schema_version") == USER_LABEL_CONNECTION_VISIBLE_SURFACE_SCHEMA_VERSION:
            visible_meta = safe_event
        connectable_family = _clean(visible_meta.get("connectable_family") or safe_event.get("connectable_family"))
        applied = bool(
            visible_meta.get("applied") is True
            or visible_meta.get("limited_visible_surface_connection_applied") is True
            or safe_event.get("limited_visible_surface_connection_applied") is True
        )
        history_connection = bool(
            visible_meta.get("history_connection_applied") is True
            or visible_meta.get("history_line_surface_connected") is True
            or safe_event.get("history_connection_applied") is True
        )
        existing_gates_passed = bool(
            visible_meta.get("existing_surface_gates_passed") is True
            or safe_event.get("existing_surface_gates_passed") is True
        )
        evidence_record_count = _int(
            visible_meta.get("evidence_record_count")
            or visible_meta.get("history_connection_evidence_record_count")
            or safe_event.get("evidence_record_count")
        )
        history_record_count = _int(visible_meta.get("history_record_count") or safe_event.get("history_record_count"))
        contract_relaxation = _event_has_contract_relaxation(safe_event)
        reviewable = bool(
            applied
            and history_connection
            and existing_gates_passed
            and connectable_family in _LIMITED_CONNECTABLE_FAMILIES
            and evidence_record_count >= 2
            and not contract_relaxation
        )
        blockers: list[str] = []
        warnings: list[str] = []
        if connectable_family and connectable_family not in _LIMITED_CONNECTABLE_FAMILIES:
            blockers.append(BLOCKER_NON_LIMITED_VISIBLE_CONNECTION)
        if contract_relaxation:
            blockers.append(BLOCKER_CONTRACT_RELAXATION_DETECTED)
        if text_payload_stripped:
            # Text body presence in source rows is not carried forward. It is a
            # source hygiene warning, not product failure after successful strip.
            warnings.append(BLOCKER_TEXT_PAYLOAD_DETECTED)
        if not reviewable and not blockers:
            blockers.append(BLOCKER_NON_LIMITED_VISIBLE_CONNECTION)
        candidate = {
            "schema_version": USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_CANDIDATE_SCHEMA_VERSION,
            "step": USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_STEP,
            "phase": USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_PHASE,
            "candidate_id": _source_id(safe_event, index),
            "source_phase": USER_LABEL_CONNECTION_VISIBLE_SURFACE_PHASE,
            "visible_surface_schema_version": _clean(visible_meta.get("schema_version")),
            "visible_surface_step": _clean(visible_meta.get("step")),
            "connectable_family": connectable_family,
            "reviewable_for_blind_qa": reviewable,
            "limited_visible_surface_connection_applied": applied,
            "history_connection_applied": history_connection,
            "existing_surface_gates_passed": existing_gates_passed,
            "evidence_record_count": evidence_record_count,
            "history_record_count": history_record_count,
            "ratings_required": list(USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_REQUIRED_DIMENSIONS),
            "product_value_connection_checked": True,
            "pytest_green_only_is_not_product_result": True,
            "blind_qa_required": True,
            "machine_metrics_used_for_read_feeling": False,
            "read_feeling_auto_filled_from_machine_metrics": False,
            "source_text_payload_stripped": text_payload_stripped,
            "source_contract_relaxation_detected": contract_relaxation,
            "candidate_blockers": blockers,
            "candidate_warnings": warnings,
            "comment_text_body_included": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "public_response_key_added": False,
            "api_route_changed": False,
            "request_key_changed": False,
            "response_shape_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "rn_visible_title_changed": False,
            "product_gate_ready": False,
            "public_release_applied": False,
        }
        assert_user_label_connection_product_quality_qa_meta_only(candidate, source="user_label_connection_product_quality_qa_candidate")
        candidates.append(candidate)
    return candidates


def _normalize_dimension_name(name: Any) -> str:
    text = _clean(name).lower().replace(" ", "_").replace("-", "_")
    return _DIMENSION_ALIASES.get(text, text)


def _ratings_from_review(review: Mapping[str, Any]) -> dict[str, Any]:
    source = _safe_mapping(review.get("ratings") or review.get("scores") or review.get("dimensions"))
    if not source:
        source = {key: value for key, value in review.items() if _normalize_dimension_name(key) in USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_REQUIRED_DIMENSIONS}
    ratings: dict[str, Any] = {}
    for key, value in source.items():
        dimension = _normalize_dimension_name(key)
        if dimension in USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_REQUIRED_DIMENSIONS:
            ratings[dimension] = value
    return ratings


def normalize_user_label_connection_product_quality_blind_qa_review(review: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize a ratings-only Blind QA review and strip any body payload."""

    source = _safe_mapping(review)
    text_payload_stripped = _contains_text_payload_key(source)
    safe = _safe_mapping(_strip_text_payload_keys(source))
    ratings = _ratings_from_review(safe)
    dimension_scores = {
        dimension: _score(ratings.get(dimension))
        for dimension in USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_REQUIRED_DIMENSIONS
    }
    failed_dimensions = [
        dimension
        for dimension, score in dimension_scores.items()
        if score is None or score < USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_TARGET
    ]
    review_meta = {
        "schema_version": USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_REVIEW_SCHEMA_VERSION,
        "step": USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_STEP,
        "phase": USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_PHASE,
        "review_id": _clean(safe.get("review_id"))[:96],
        "candidate_id": _clean(safe.get("candidate_id") or safe.get("row_id"))[:96],
        "ratings_only_payload": True,
        "ratings_dimensions_present": [
            dimension
            for dimension in USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_REQUIRED_DIMENSIONS
            if dimension_scores[dimension] is not None
        ],
        "ratings_required": list(USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_REQUIRED_DIMENSIONS),
        "dimension_scores": dimension_scores,
        "read_feeling_score": dimension_scores[DIMENSION_READ_FEELING],
        "self_information_organized_score": dimension_scores[DIMENSION_SELF_INFORMATION_ORGANIZED],
        "history_connection_naturalness_score": dimension_scores[DIMENSION_HISTORY_CONNECTION_NATURALNESS],
        "creepy_absence_score": dimension_scores[DIMENSION_CREEPY_ABSENCE],
        "overclaim_absence_score": dimension_scores[DIMENSION_OVERCLAIM_ABSENCE],
        "self_blame_non_amplification_score": dimension_scores[DIMENSION_SELF_BLAME_NON_AMPLIFICATION],
        "wants_more_input_or_accumulation_score": dimension_scores[DIMENSION_WANTS_MORE_INPUT_OR_ACCUMULATION],
        "non_shallow_repeat_score": dimension_scores[DIMENSION_NON_SHALLOW_REPEAT],
        "product_value_connection_score": _avg(dimension_scores.values()),
        "passed": not failed_dimensions,
        "failed_dimensions": failed_dimensions,
        "source_text_payload_stripped": text_payload_stripped,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "comment_text_body_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "public_response_key_added": False,
        "api_route_changed": False,
        "request_key_changed": False,
        "response_shape_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "product_gate_ready": False,
        "public_release_applied": False,
    }
    assert_user_label_connection_product_quality_qa_meta_only(review_meta, source="user_label_connection_product_quality_blind_qa_review")
    return review_meta


def _reviews_by_candidate(normalized_reviews: Sequence[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for review in normalized_reviews:
        candidate_id = _clean(review.get("candidate_id"))
        if candidate_id:
            grouped.setdefault(candidate_id, []).append(review)
    return grouped


def _dimension_averages(reviews: Sequence[Mapping[str, Any]]) -> dict[str, float | None]:
    averages: dict[str, float | None] = {}
    for dimension in USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_REQUIRED_DIMENSIONS:
        averages[dimension] = _avg(_safe_mapping(review.get("dimension_scores")).get(dimension) for review in reviews)
    return averages


def _blockers_from_dimension_scores(averages: Mapping[str, float | None]) -> list[str]:
    blockers: list[str] = []
    target = USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_TARGET
    checks = (
        (DIMENSION_READ_FEELING, BLOCKER_READ_FEELING_BELOW_TARGET),
        (DIMENSION_SELF_INFORMATION_ORGANIZED, BLOCKER_SELF_INFORMATION_ORGANIZATION_BELOW_TARGET),
        (DIMENSION_HISTORY_CONNECTION_NATURALNESS, BLOCKER_HISTORY_CONNECTION_NATURALNESS_BELOW_TARGET),
        (DIMENSION_CREEPY_ABSENCE, BLOCKER_HISTORY_CONNECTION_CREEPY_RISK),
        (DIMENSION_OVERCLAIM_ABSENCE, BLOCKER_OVERCLAIM_OR_DECIDING_RISK),
        (DIMENSION_SELF_BLAME_NON_AMPLIFICATION, BLOCKER_SELF_BLAME_AMPLIFICATION_RISK),
        (DIMENSION_WANTS_MORE_INPUT_OR_ACCUMULATION, BLOCKER_ACCUMULATION_MOTIVATION_NOT_CONFIRMED),
        (DIMENSION_NON_SHALLOW_REPEAT, BLOCKER_SHALLOW_REPEAT_RISK),
    )
    for dimension, blocker in checks:
        score = averages.get(dimension)
        if score is None or score < target:
            blockers.append(blocker)
    return blockers


def build_user_label_connection_product_quality_qa_summary(
    *,
    events: Sequence[Mapping[str, Any]] | None = None,
    blind_qa_reviews: Sequence[Mapping[str, Any]] | None = None,
    qa_candidates: Sequence[Mapping[str, Any]] | None = None,
    run_id: Any = "",
) -> dict[str, Any]:
    """Aggregate Phase 9 product-value QA without making a release decision."""

    candidates = [dict(candidate) for candidate in (qa_candidates or [])]
    if not candidates:
        candidates = build_user_label_connection_product_quality_qa_candidates(list(events or []))
    for candidate in candidates:
        assert_user_label_connection_product_quality_qa_meta_only(candidate, source="user_label_connection_product_quality_qa_candidate_source")
    normalized_reviews = [normalize_user_label_connection_product_quality_blind_qa_review(review) for review in (blind_qa_reviews or [])]
    grouped_reviews = _reviews_by_candidate(normalized_reviews)
    reviewable_candidates = [candidate for candidate in candidates if candidate.get("reviewable_for_blind_qa") is True]
    reviewed_candidate_ids = {
        _clean(candidate.get("candidate_id"))
        for candidate in reviewable_candidates
        if _clean(candidate.get("candidate_id")) in grouped_reviews
    }
    candidate_blockers = _dedupe([
        blocker
        for candidate in candidates
        for blocker in _listify(candidate.get("candidate_blockers"))
    ])
    candidate_warnings = _dedupe([
        warning
        for candidate in candidates
        for warning in _listify(candidate.get("candidate_warnings"))
    ])
    review_coverage_rate = _rate(len(reviewed_candidate_ids), len(reviewable_candidates))
    dimension_averages = _dimension_averages(normalized_reviews)
    release_blockers: list[str] = []
    if not reviewable_candidates:
        release_blockers.append(BLOCKER_NO_REVIEWABLE_CANDIDATES)
    if not normalized_reviews:
        release_blockers.append(BLOCKER_BLIND_QA_REVIEW_REQUIRED)
    if reviewable_candidates and review_coverage_rate < USER_LABEL_CONNECTION_PRODUCT_QUALITY_REVIEW_COVERAGE_TARGET:
        release_blockers.append(BLOCKER_REVIEW_COVERAGE_BELOW_TARGET)
    release_blockers.extend(candidate_blockers)
    if normalized_reviews:
        release_blockers.extend(_blockers_from_dimension_scores(dimension_averages))
    qa_passed = not release_blockers
    summary = {
        "schema_version": USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_SCHEMA_VERSION,
        "step": USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_STEP,
        "phase": USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_PHASE,
        "run_id": _clean(run_id)[:96],
        "source_phase": USER_LABEL_CONNECTION_VISIBLE_SURFACE_PHASE,
        "candidate_schema_version": USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_CANDIDATE_SCHEMA_VERSION,
        "review_schema_version": USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_REVIEW_SCHEMA_VERSION,
        "candidate_count": len(candidates),
        "reviewable_candidate_count": len(reviewable_candidates),
        "reviewed_candidate_count": len(reviewed_candidate_ids),
        "blind_qa_review_count": len(normalized_reviews),
        "blind_qa_review_coverage_rate": review_coverage_rate,
        "blind_qa_required": True,
        "pytest_green_only_is_not_product_result": True,
        "product_value_connection_checked": True,
        "phase9_product_quality_qa_passed": qa_passed,
        "product_quality_qa_ready": qa_passed,
        "product_value_connected_by_qa": qa_passed,
        "read_feeling_score": dimension_averages[DIMENSION_READ_FEELING],
        "self_information_organized_score": dimension_averages[DIMENSION_SELF_INFORMATION_ORGANIZED],
        "history_connection_naturalness_score": dimension_averages[DIMENSION_HISTORY_CONNECTION_NATURALNESS],
        "creepy_absence_score": dimension_averages[DIMENSION_CREEPY_ABSENCE],
        "overclaim_absence_score": dimension_averages[DIMENSION_OVERCLAIM_ABSENCE],
        "self_blame_non_amplification_score": dimension_averages[DIMENSION_SELF_BLAME_NON_AMPLIFICATION],
        "wants_more_input_or_accumulation_score": dimension_averages[DIMENSION_WANTS_MORE_INPUT_OR_ACCUMULATION],
        "non_shallow_repeat_score": dimension_averages[DIMENSION_NON_SHALLOW_REPEAT],
        "dimension_scores": dict(dimension_averages),
        "quality_target": USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_TARGET,
        "release_blockers": _dedupe(release_blockers),
        "qa_blockers": _dedupe(release_blockers),
        "candidate_blockers": candidate_blockers,
        "candidate_warnings": candidate_warnings,
        "ratings_required": list(USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_REQUIRED_DIMENSIONS),
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "comment_text_body_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "public_response_key_added": False,
        "api_route_changed": False,
        "request_key_changed": False,
        "response_shape_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "product_gate_public_release_applied": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "fixed_sentence_template_added": False,
        "external_ai_used": False,
        "local_llm_used": False,
    }
    assert_user_label_connection_product_quality_qa_meta_only(summary, source="user_label_connection_product_quality_qa_summary")
    return summary


# Compatibility aliases for tests/later integration naming.
build_user_label_connection_product_quality_blind_qa_candidates = build_user_label_connection_product_quality_qa_candidates
build_user_label_connection_product_quality_blind_qa_summary = build_user_label_connection_product_quality_qa_summary
normalize_user_label_connection_product_quality_qa_review = normalize_user_label_connection_product_quality_blind_qa_review


__all__ = [
    "USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_SCHEMA_VERSION",
    "USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_CANDIDATE_SCHEMA_VERSION",
    "USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_REVIEW_SCHEMA_VERSION",
    "USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_STEP",
    "USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_PHASE",
    "USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_REQUIRED_DIMENSIONS",
    "USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_TARGET",
    "DIMENSION_READ_FEELING",
    "DIMENSION_SELF_INFORMATION_ORGANIZED",
    "DIMENSION_HISTORY_CONNECTION_NATURALNESS",
    "DIMENSION_CREEPY_ABSENCE",
    "DIMENSION_OVERCLAIM_ABSENCE",
    "DIMENSION_SELF_BLAME_NON_AMPLIFICATION",
    "DIMENSION_WANTS_MORE_INPUT_OR_ACCUMULATION",
    "DIMENSION_NON_SHALLOW_REPEAT",
    "BLOCKER_NO_REVIEWABLE_CANDIDATES",
    "BLOCKER_BLIND_QA_REVIEW_REQUIRED",
    "BLOCKER_REVIEW_COVERAGE_BELOW_TARGET",
    "BLOCKER_READ_FEELING_BELOW_TARGET",
    "BLOCKER_SELF_INFORMATION_ORGANIZATION_BELOW_TARGET",
    "BLOCKER_HISTORY_CONNECTION_CREEPY_RISK",
    "BLOCKER_HISTORY_CONNECTION_NATURALNESS_BELOW_TARGET",
    "BLOCKER_OVERCLAIM_OR_DECIDING_RISK",
    "BLOCKER_SELF_BLAME_AMPLIFICATION_RISK",
    "BLOCKER_ACCUMULATION_MOTIVATION_NOT_CONFIRMED",
    "BLOCKER_SHALLOW_REPEAT_RISK",
    "BLOCKER_TEXT_PAYLOAD_DETECTED",
    "BLOCKER_CONTRACT_RELAXATION_DETECTED",
    "BLOCKER_NON_LIMITED_VISIBLE_CONNECTION",
    "assert_user_label_connection_product_quality_qa_meta_only",
    "build_user_label_connection_product_quality_qa_candidates",
    "build_user_label_connection_product_quality_blind_qa_candidates",
    "normalize_user_label_connection_product_quality_blind_qa_review",
    "normalize_user_label_connection_product_quality_qa_review",
    "build_user_label_connection_product_quality_qa_summary",
    "build_user_label_connection_product_quality_blind_qa_summary",
]
