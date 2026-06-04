# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 6 Blind QA integration for EmlisAI Product Quality measurement.

This module unifies Runtime Surface Blind QA and User Label Connection Product
Quality QA into one internal, meta-only release-blocking material.  It keeps
reviews ratings-only, strips raw/comment/surface bodies before normalization,
and never turns Product Gate or public release flags on.
"""

from collections.abc import Iterable, Mapping, Sequence
import json
from typing import Any, Final

from emlis_ai_product_quality_contract_freeze import (
    assert_emlis_ai_product_quality_contract_freeze_meta_only,
    build_emlis_ai_product_quality_contract_freeze,
)
from emlis_ai_runtime_surface_blind_qa_long_run import (
    RUNTIME_SURFACE_BLIND_QA_LONG_RUN_READ_FEELING_PRODUCT_TARGET,
    RUNTIME_SURFACE_BLIND_QA_LONG_RUN_REQUIRED_DIMENSIONS,
    RUNTIME_SURFACE_BLIND_QA_LONG_RUN_VERSION,
    assert_runtime_surface_blind_qa_long_run_meta_only,
    normalize_runtime_surface_blind_qa_review,
)
from emlis_ai_user_label_connection_product_quality_qa import (
    USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_REQUIRED_DIMENSIONS,
    USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_TARGET,
    USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_SCHEMA_VERSION,
    assert_user_label_connection_product_quality_qa_meta_only,
    normalize_user_label_connection_product_quality_blind_qa_review,
)

PRODUCT_QUALITY_BLIND_QA_INTEGRATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.product_quality.blind_qa_integration.v1"
)
PRODUCT_QUALITY_BLIND_QA_INTEGRATION_VERSION: Final = (
    PRODUCT_QUALITY_BLIND_QA_INTEGRATION_SCHEMA_VERSION
)
PRODUCT_QUALITY_BLIND_QA_REVIEW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.product_quality.blind_qa_review.v1"
)
PRODUCT_QUALITY_BLIND_QA_REVIEW_QUEUE_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.product_quality.blind_qa_review_queue_row.v1"
)
PRODUCT_QUALITY_BLIND_QA_INTEGRATION_PHASE: Final = "Phase6_BlindQAIntegration"
PRODUCT_QUALITY_BLIND_QA_INTEGRATION_TARGET_STEP: Final = (
    "ProductQuality_BlindQAIntegration"
)

BLIND_QA_REVIEW_COVERAGE_TARGET: Final = 1.0
RUNTIME_SURFACE_SCOPE: Final = "runtime_surface"
USER_LABEL_CONNECTION_SCOPE: Final = "user_label_connection"

BLOCKER_BLIND_QA_REVIEW_REQUIRED: Final = "blind_qa_review_required"
BLOCKER_BLIND_QA_REVIEW_COVERAGE_BELOW_TARGET: Final = (
    "blind_qa_review_coverage_below_target"
)
BLOCKER_RUNTIME_SURFACE_BLIND_QA_LONG_RUN_NOT_READY: Final = (
    "runtime_surface_blind_qa_long_run_not_ready"
)
BLOCKER_USER_LABEL_CONNECTION_QA_NOT_READY: Final = (
    "user_label_connection_product_quality_qa_not_ready"
)
BLOCKER_RUNTIME_SURFACE_READ_FEELING_BELOW_TARGET: Final = (
    "read_feeling_score_below_product_gate_target"
)
BLOCKER_USER_LABEL_READ_FEELING_BELOW_TARGET: Final = (
    "read_feeling_below_product_quality_target"
)
BLOCKER_BLIND_QA_TEXT_PAYLOAD_STRIPPED: Final = "blind_qa_text_payload_stripped"
BLOCKER_BLIND_QA_CONTRACT_RELAXATION_DETECTED: Final = (
    "blind_qa_contract_relaxation_detected"
)

_TEXT_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
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
        "input_text_for_local_review_only",
        "user_input",
        "userInput",
        "current_input",
        "currentInput",
        "memo",
        "memo_text",
        "memoText",
        "memo_action",
        "memoAction",
        "comment_text",
        "commentText",
        "comment_text_for_local_review_only",
        "comment_body",
        "commentBody",
        "input_feedback_comment",
        "public_comment_text",
        "candidate_comment_text",
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
_FORBIDDEN_TRUE_FLAGS: Final[frozenset[str]] = frozenset(
    {
        "api_route_changed",
        "request_key_changed",
        "response_shape_changed",
        "public_response_key_added",
        "public_response_key_change",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "reader_gate_relaxed",
        "template_gate_relaxed",
        "gate_relaxed",
        "raw_input_included",
        "raw_text_included",
        "raw_user_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "machine_metrics_used_for_read_feeling",
        "read_feeling_auto_filled_from_machine_metrics",
        "read_feeling_auto_estimation_allowed",
        "product_gate_ready",
        "product_gate_reached",
        "product_gate_achieved",
        "product_gate_public_release_applied",
        "product_quality_released",
        "public_release_applied",
        "release_allowed",
        "fixed_sentence_template_added",
        "fixed_sentence_template_used",
        "input_specific_template_added",
        "runtime_fixture_branch_added",
        "runtime_fixture_branch_required",
        "external_ai_used",
        "local_llm_used",
        "release_material_import_allowed",
        "public_meta_import_allowed",
    }
)
_SCOPE_ALIASES: Final[dict[str, str]] = {
    "runtime": RUNTIME_SURFACE_SCOPE,
    "runtime_surface": RUNTIME_SURFACE_SCOPE,
    "surface": RUNTIME_SURFACE_SCOPE,
    "step11": RUNTIME_SURFACE_SCOPE,
    "runtime_surface_blind_qa": RUNTIME_SURFACE_SCOPE,
    "user_label": USER_LABEL_CONNECTION_SCOPE,
    "user_label_connection": USER_LABEL_CONNECTION_SCOPE,
    "ulc": USER_LABEL_CONNECTION_SCOPE,
    "user_label_connection_product_quality": USER_LABEL_CONNECTION_SCOPE,
}


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


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "" or isinstance(value, bool):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _to_float(value: Any) -> float | None:
    try:
        if value is None or value == "" or isinstance(value, bool):
            return None
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return None


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(max(0.0, min(1.0, float(numerator) / float(denominator))), 4)


def _avg(values: Iterable[Any]) -> float | None:
    scores: list[float] = []
    for value in values:
        score = _to_float(value)
        if score is not None:
            scores.append(score)
    if not scores:
        return None
    return round(sum(scores) / len(scores), 4)


def _normalize_scope(value: Any, default: str = RUNTIME_SURFACE_SCOPE) -> str:
    text = _clean(value).lower().replace(" ", "_").replace("-", "_")
    return _SCOPE_ALIASES.get(text, default)


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


def assert_product_quality_blind_qa_integration_meta_only(
    value: Any,
    *,
    source: str = "product_quality_blind_qa_integration",
) -> None:
    """Assert Phase 6 material stays ratings/counts/ids only."""

    if _contains_text_payload_key(value):
        raise ValueError(f"{source} must not include raw input/comment/surface body keys")
    if _forbidden_true_flag(value):
        raise ValueError(f"{source} must not relax contracts, use machine read-feeling, or turn release flags on")
    json.dumps(value, ensure_ascii=False, sort_keys=True)


def _candidate_id(candidate: Mapping[str, Any]) -> str:
    for key in ("candidate_id", "row_id", "trace_id", "emotion_log_id"):
        value = _clean(candidate.get(key))
        if value:
            return value[:96]
    return ""


def _candidate_reviewable(candidate: Mapping[str, Any]) -> bool:
    return candidate.get("reviewable_for_blind_qa") is True or candidate.get("blind_qa_review_required") is True


def _source_candidate_scope(candidate: Mapping[str, Any], default: str) -> str:
    return _normalize_scope(candidate.get("review_scope") or candidate.get("blind_qa_scope") or candidate.get("candidate_scope"), default)


def normalize_product_quality_blind_qa_review(
    review: Mapping[str, Any] | None,
    *,
    review_scope: str | None = None,
) -> dict[str, Any]:
    """Normalize a ratings-only review into the shared Phase 6 schema.

    Raw input, visible surface, and public ``comment_text`` bodies are stripped
    before delegating to the existing domain-specific normalizer.
    """

    source = _safe_mapping(review)
    source_text_payload_stripped = _contains_text_payload_key(source)
    source_contract_relaxation_detected = _forbidden_true_flag(source)
    safe = _safe_mapping(_strip_text_payload_keys(source))
    scope = _normalize_scope(review_scope or safe.get("review_scope") or safe.get("scope"), RUNTIME_SURFACE_SCOPE)

    if scope == USER_LABEL_CONNECTION_SCOPE:
        normalized_source = normalize_user_label_connection_product_quality_blind_qa_review(safe)
        dimension_scores = _safe_mapping(normalized_source.get("dimension_scores"))
        required_dimensions = list(USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_REQUIRED_DIMENSIONS)
        product_target = USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_TARGET
        source_schema_version = USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_SCHEMA_VERSION
        read_feeling_score = normalized_source.get("read_feeling_score")
        quality_score = normalized_source.get("product_value_connection_score")
        passed = normalized_source.get("passed") is True
        red_reason_codes = _dedupe(normalized_source.get("failed_dimensions"))
    else:
        scope = RUNTIME_SURFACE_SCOPE
        normalized_source = normalize_runtime_surface_blind_qa_review(safe)
        dimension_scores = _safe_mapping(normalized_source.get("dimension_scores"))
        required_dimensions = list(RUNTIME_SURFACE_BLIND_QA_LONG_RUN_REQUIRED_DIMENSIONS)
        product_target = RUNTIME_SURFACE_BLIND_QA_LONG_RUN_READ_FEELING_PRODUCT_TARGET
        source_schema_version = RUNTIME_SURFACE_BLIND_QA_LONG_RUN_VERSION
        read_feeling_score = normalized_source.get("read_feeling_score")
        quality_score = normalized_source.get("score")
        passed = normalized_source.get("passed") is True
        red_reason_codes = [
            dimension
            for dimension, score in dimension_scores.items()
            if score is None or _to_float(score) is None or float(score) < product_target
        ]

    missing_dimensions = [dimension for dimension in required_dimensions if dimension_scores.get(dimension) is None]
    review_meta = {
        "schema_version": PRODUCT_QUALITY_BLIND_QA_REVIEW_SCHEMA_VERSION,
        "version": PRODUCT_QUALITY_BLIND_QA_REVIEW_SCHEMA_VERSION,
        "phase": PRODUCT_QUALITY_BLIND_QA_INTEGRATION_PHASE,
        "target_step": PRODUCT_QUALITY_BLIND_QA_INTEGRATION_TARGET_STEP,
        "review_scope": scope,
        "source_review_schema_version": source_schema_version,
        "review_id": _clean(safe.get("review_id") or safe.get("id"))[:96],
        "candidate_id": _clean(normalized_source.get("candidate_id") or safe.get("candidate_id") or safe.get("row_id"))[:96],
        "row_id": _clean(normalized_source.get("row_id") or safe.get("row_id"))[:96],
        "ratings_only_payload": True,
        "ratings_dimensions_present": [
            dimension for dimension in required_dimensions if dimension_scores.get(dimension) is not None
        ],
        "ratings_required": required_dimensions,
        "dimension_scores": {dimension: dimension_scores.get(dimension) for dimension in required_dimensions},
        "read_feeling_score": read_feeling_score,
        "quality_score": quality_score,
        "product_target": product_target,
        "verdict": "green" if passed else "red",
        "passed": passed,
        "red_reason_codes": red_reason_codes,
        "missing_dimensions": missing_dimensions,
        "source_text_payload_stripped": source_text_payload_stripped,
        "source_contract_relaxation_detected": source_contract_relaxation_detected,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_auto_estimation_allowed": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "raw_user_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "response_shape_changed": False,
        "public_response_key_added": False,
        "api_route_changed": False,
        "request_key_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "product_gate_public_release_applied": False,
        "public_release_applied": False,
    }
    assert_product_quality_blind_qa_integration_meta_only(review_meta, source="product_quality_blind_qa_review")
    return review_meta


def _normalized_reviews_for_scope(
    reviews: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None,
    *,
    scope: str,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for review in list(reviews or []):
        normalized.append(normalize_product_quality_blind_qa_review(review, review_scope=scope))
    return normalized


def _reviews_by_candidate(reviews: Sequence[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for review in reviews:
        candidate_id = _clean(review.get("candidate_id"))
        if candidate_id:
            grouped.setdefault(candidate_id, []).append(review)
    return grouped


def _review_queue_rows(
    *,
    scope: str,
    candidates: Sequence[Mapping[str, Any]],
    reviews: Sequence[Mapping[str, Any]],
    required_dimensions: Sequence[str],
) -> list[dict[str, Any]]:
    grouped = _reviews_by_candidate(reviews)
    rows: list[dict[str, Any]] = []
    for index, raw_candidate in enumerate(candidates, start=1):
        candidate = _safe_mapping(raw_candidate)
        candidate_id = _candidate_id(candidate) or f"{scope}_candidate_{index:03d}"
        reviewable = _candidate_reviewable(candidate)
        row = {
            "schema_version": PRODUCT_QUALITY_BLIND_QA_REVIEW_QUEUE_ROW_SCHEMA_VERSION,
            "phase": PRODUCT_QUALITY_BLIND_QA_INTEGRATION_PHASE,
            "target_step": PRODUCT_QUALITY_BLIND_QA_INTEGRATION_TARGET_STEP,
            "review_scope": scope,
            "candidate_id": candidate_id,
            "row_id": _clean(candidate.get("row_id"))[:96],
            "coverage_group": _clean(candidate.get("coverage_group") or candidate.get("connectable_family"))[:96],
            "reviewable_for_blind_qa": reviewable,
            "blind_qa_review_required": reviewable,
            "reviewed": bool(candidate_id in grouped),
            "review_count": len(grouped.get(candidate_id, [])),
            "ratings_required": list(required_dimensions),
            "ratings_only_payload_required": True,
            "local_review_packet_included": False,
            "release_material_import_allowed": False,
            "public_meta_import_allowed": False,
            "delete_after_review_required_if_local_packet_created": True,
            "machine_metrics_used_for_read_feeling": False,
            "read_feeling_auto_filled_from_machine_metrics": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
            "candidate_body_included": False,
            "surface_body_included": False,
            "product_gate_ready": False,
            "public_release_applied": False,
        }
        assert_product_quality_blind_qa_integration_meta_only(row, source="product_quality_blind_qa_review_queue_row")
        rows.append(row)
    return rows


def _scope_summary(
    *,
    scope: str,
    candidates: Sequence[Mapping[str, Any]],
    reviews: Sequence[Mapping[str, Any]],
    required_dimensions: Sequence[str],
    product_target: float,
    source_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    summary = _safe_mapping(source_summary)
    safe_candidates = [_safe_mapping(_strip_text_payload_keys(candidate)) for candidate in candidates]
    reviewable_candidates = [candidate for candidate in safe_candidates if _candidate_reviewable(candidate)]
    reviewable_ids = [_candidate_id(candidate) for candidate in reviewable_candidates if _candidate_id(candidate)]
    grouped = _reviews_by_candidate(reviews)
    reviewed_ids = [candidate_id for candidate_id in reviewable_ids if candidate_id in grouped]
    coverage_rate = _rate(len(reviewed_ids), len(reviewable_ids))
    read_feeling_score = _to_float(summary.get("read_feeling_score"))
    if read_feeling_score is None:
        read_feeling_score = _avg(review.get("read_feeling_score") for review in reviews)
    red_review_count = _to_int(summary.get("red_review_count"))
    if not red_review_count:
        red_review_count = sum(1 for review in reviews if _clean(review.get("verdict")).lower() == "red" or review.get("passed") is False)
    missing_reviewable_ids = [candidate_id for candidate_id in reviewable_ids if candidate_id not in grouped]
    existing_blockers = _dedupe(
        summary.get("release_blockers")
        or summary.get("step11_release_blockers")
        or summary.get("qa_blockers")
        or summary.get("product_gate_candidate_blockers")
        or summary.get("qa_gaps")
    )
    blockers = list(existing_blockers)
    if reviewable_candidates and coverage_rate < BLIND_QA_REVIEW_COVERAGE_TARGET:
        blockers.append(BLOCKER_BLIND_QA_REVIEW_REQUIRED if not reviews else BLOCKER_BLIND_QA_REVIEW_COVERAGE_BELOW_TARGET)
    if not reviewable_candidates:
        if scope == USER_LABEL_CONNECTION_SCOPE:
            blockers.append("no_reviewable_user_label_connection_candidates")
        else:
            blockers.append(BLOCKER_RUNTIME_SURFACE_BLIND_QA_LONG_RUN_NOT_READY)
    if read_feeling_score is not None and read_feeling_score < product_target:
        blockers.append(
            BLOCKER_USER_LABEL_READ_FEELING_BELOW_TARGET
            if scope == USER_LABEL_CONNECTION_SCOPE
            else BLOCKER_RUNTIME_SURFACE_READ_FEELING_BELOW_TARGET
        )
    if red_review_count > 0:
        blockers.append("blind_qa_red_review_detected")
    if any(review.get("source_text_payload_stripped") is True for review in reviews):
        blockers.append(BLOCKER_BLIND_QA_TEXT_PAYLOAD_STRIPPED)
    if any(review.get("source_contract_relaxation_detected") is True for review in reviews):
        blockers.append(BLOCKER_BLIND_QA_CONTRACT_RELAXATION_DETECTED)
    queue_rows = _review_queue_rows(
        scope=scope,
        candidates=safe_candidates,
        reviews=reviews,
        required_dimensions=required_dimensions,
    )
    ready_from_source = bool(
        summary.get("runtime_surface_blind_qa_long_run_ready")
        or summary.get("step11_blind_qa_long_run_ready")
        or summary.get("product_quality_qa_ready")
        or summary.get("phase9_product_quality_qa_passed")
    )
    coverage_ready = bool(reviewable_candidates and coverage_rate >= BLIND_QA_REVIEW_COVERAGE_TARGET)
    read_ready = bool(read_feeling_score is not None and read_feeling_score >= product_target)
    ready = bool(coverage_ready and read_ready and red_review_count == 0 and not _dedupe(blockers) and (ready_from_source or reviews))
    scope_meta = {
        "review_scope": scope,
        "candidate_count": len(safe_candidates),
        "reviewable_candidate_count": len(reviewable_candidates),
        "reviewed_candidate_count": len(reviewed_ids),
        "blind_qa_review_count": len(reviews),
        "blind_qa_review_coverage_rate": coverage_rate,
        "blind_qa_review_coverage_target": BLIND_QA_REVIEW_COVERAGE_TARGET,
        "missing_reviewable_candidate_count": len(missing_reviewable_ids),
        "missing_reviewable_candidate_ids": missing_reviewable_ids,
        "reviewable_candidate_ids": reviewable_ids,
        "reviewed_candidate_ids": reviewed_ids,
        "ratings_required": list(required_dimensions),
        "ratings_only_payload_required": True,
        "read_feeling_score": read_feeling_score,
        "read_feeling_product_target": product_target,
        "read_feeling_product_target_met": bool(read_ready),
        "red_review_count": red_review_count,
        "ready": ready,
        "release_blockers": _dedupe(blockers),
        "review_queue": queue_rows,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_auto_estimation_allowed": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "product_gate_ready": False,
        "public_release_applied": False,
    }
    assert_product_quality_blind_qa_integration_meta_only(scope_meta, source=f"product_quality_blind_qa_{scope}_summary")
    return scope_meta


def build_product_quality_blind_qa_integration(
    *,
    run_id: Any = "",
    runtime_surface_candidates: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None = None,
    runtime_surface_reviews: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None = None,
    runtime_surface_summary: Mapping[str, Any] | None = None,
    user_label_connection_candidates: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None = None,
    user_label_connection_reviews: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None = None,
    user_label_connection_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build Phase 6 unified Blind QA integration material."""

    runtime_candidates = [
        _safe_mapping(_strip_text_payload_keys(candidate))
        for candidate in list(runtime_surface_candidates or [])
    ]
    user_label_candidates = [
        _safe_mapping(_strip_text_payload_keys(candidate))
        for candidate in list(user_label_connection_candidates or [])
    ]
    for candidate in runtime_candidates:
        assert_runtime_surface_blind_qa_long_run_meta_only(candidate, source="phase6_runtime_surface_candidate_source")
    for candidate in user_label_candidates:
        assert_user_label_connection_product_quality_qa_meta_only(candidate, source="phase6_user_label_candidate_source")
    runtime_reviews = _normalized_reviews_for_scope(runtime_surface_reviews, scope=RUNTIME_SURFACE_SCOPE)
    user_label_reviews = _normalized_reviews_for_scope(user_label_connection_reviews, scope=USER_LABEL_CONNECTION_SCOPE)
    runtime_scope = _scope_summary(
        scope=RUNTIME_SURFACE_SCOPE,
        candidates=runtime_candidates,
        reviews=runtime_reviews,
        required_dimensions=RUNTIME_SURFACE_BLIND_QA_LONG_RUN_REQUIRED_DIMENSIONS,
        product_target=RUNTIME_SURFACE_BLIND_QA_LONG_RUN_READ_FEELING_PRODUCT_TARGET,
        source_summary=runtime_surface_summary,
    )
    user_label_scope = _scope_summary(
        scope=USER_LABEL_CONNECTION_SCOPE,
        candidates=user_label_candidates,
        reviews=user_label_reviews,
        required_dimensions=USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_REQUIRED_DIMENSIONS,
        product_target=USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_TARGET,
        source_summary=user_label_connection_summary,
    )
    release_blockers = _dedupe(
        list(runtime_scope.get("release_blockers") or [])
        + list(user_label_scope.get("release_blockers") or [])
    )
    ready = bool(runtime_scope.get("ready") is True and user_label_scope.get("ready") is True and not release_blockers)
    review_queue = list(runtime_scope.get("review_queue") or []) + list(user_label_scope.get("review_queue") or [])
    integration = {
        "schema_version": PRODUCT_QUALITY_BLIND_QA_INTEGRATION_SCHEMA_VERSION,
        "version": PRODUCT_QUALITY_BLIND_QA_INTEGRATION_VERSION,
        "phase": PRODUCT_QUALITY_BLIND_QA_INTEGRATION_PHASE,
        "target_step": PRODUCT_QUALITY_BLIND_QA_INTEGRATION_TARGET_STEP,
        "run_id": _clean(run_id)[:96],
        "contract_freeze": build_emlis_ai_product_quality_contract_freeze(),
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
            "raw_input_included": False,
            "comment_text_body_included": False,
            "candidate_body_included": False,
            "surface_body_included": False,
        },
        "blind_qa_required": True,
        "blind_qa_integration_ready": ready,
        "product_quality_blind_qa_ready": ready,
        "pytest_green_only_is_not_product_result": True,
        "machine_metrics_can_not_fill_read_feeling": True,
        "runtime_surface": runtime_scope,
        "user_label_connection": user_label_scope,
        "runtime_surface_normalized_reviews": runtime_reviews,
        "user_label_connection_normalized_reviews": user_label_reviews,
        "blind_qa_review_queue": review_queue,
        "blind_qa_review_queue_count": len(review_queue),
        "review_scope_counts": {
            RUNTIME_SURFACE_SCOPE: runtime_scope.get("reviewable_candidate_count"),
            USER_LABEL_CONNECTION_SCOPE: user_label_scope.get("reviewable_candidate_count"),
        },
        "summary": {
            "runtime_surface_review_coverage_rate": runtime_scope.get("blind_qa_review_coverage_rate"),
            "user_label_connection_review_coverage_rate": user_label_scope.get("blind_qa_review_coverage_rate"),
            "runtime_surface_read_feeling_score": runtime_scope.get("read_feeling_score"),
            "user_label_connection_read_feeling_score": user_label_scope.get("read_feeling_score"),
            "release_blocker_count": len(release_blockers),
            "blind_qa_integration_ready": ready,
        },
        "release_blockers": release_blockers,
        "qa_blockers": release_blockers,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "product_gate_public_release_applied": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_auto_estimation_allowed": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "raw_user_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "public_response_key_added": False,
        "response_shape_changed": False,
        "api_route_changed": False,
        "request_key_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "release_material_import_allowed": False,
        "public_meta_import_allowed": False,
        "local_review_packet_materialized": False,
        "local_review_packet_release_material_import_allowed": False,
        "local_review_packet_public_meta_import_allowed": False,
    }
    assert_emlis_ai_product_quality_contract_freeze_meta_only(integration, source="product_quality_blind_qa_integration_contract")
    assert_product_quality_blind_qa_integration_meta_only(integration)
    return integration


def dump_product_quality_blind_qa_integration(integration: Mapping[str, Any]) -> str:
    data = _safe_mapping(_strip_text_payload_keys(integration))
    assert_product_quality_blind_qa_integration_meta_only(data, source="product_quality_blind_qa_integration_dump")
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "BLIND_QA_REVIEW_COVERAGE_TARGET",
    "BLOCKER_BLIND_QA_CONTRACT_RELAXATION_DETECTED",
    "BLOCKER_BLIND_QA_REVIEW_COVERAGE_BELOW_TARGET",
    "BLOCKER_BLIND_QA_REVIEW_REQUIRED",
    "BLOCKER_BLIND_QA_TEXT_PAYLOAD_STRIPPED",
    "BLOCKER_RUNTIME_SURFACE_BLIND_QA_LONG_RUN_NOT_READY",
    "BLOCKER_RUNTIME_SURFACE_READ_FEELING_BELOW_TARGET",
    "BLOCKER_USER_LABEL_CONNECTION_QA_NOT_READY",
    "BLOCKER_USER_LABEL_READ_FEELING_BELOW_TARGET",
    "PRODUCT_QUALITY_BLIND_QA_INTEGRATION_PHASE",
    "PRODUCT_QUALITY_BLIND_QA_INTEGRATION_SCHEMA_VERSION",
    "PRODUCT_QUALITY_BLIND_QA_INTEGRATION_TARGET_STEP",
    "PRODUCT_QUALITY_BLIND_QA_INTEGRATION_VERSION",
    "PRODUCT_QUALITY_BLIND_QA_REVIEW_QUEUE_ROW_SCHEMA_VERSION",
    "PRODUCT_QUALITY_BLIND_QA_REVIEW_SCHEMA_VERSION",
    "RUNTIME_SURFACE_SCOPE",
    "USER_LABEL_CONNECTION_SCOPE",
    "assert_product_quality_blind_qa_integration_meta_only",
    "build_product_quality_blind_qa_integration",
    "dump_product_quality_blind_qa_integration",
    "normalize_product_quality_blind_qa_review",
]
