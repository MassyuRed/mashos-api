# -*- coding: utf-8 -*-
from __future__ import annotations

"""P3-5 Blind QA ratings-only review for EmlisAI Product Read Feel baseline.

P3-5 is the bridge between local human review and the body-free Product Read
Feel scorecard.  Reviewers may read the local P3-2 review packet outside this
module, but the material accepted here is ratings-only: safe identifiers,
family, coverage slices, numeric dimension ratings, red flags, and repair
reason codes.  It never accepts raw input, rendered ``comment_text`` bodies, or
candidate display bodies, and it never derives ``read_feeling`` from machine
metrics or P3-4 verdict rows.
"""

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
import json
from typing import Any, Final

from emlis_ai_product_quality_contract_freeze import (
    assert_emlis_ai_product_quality_contract_freeze_meta_only,
)
from emlis_ai_product_readfeel_current_output_inventory import PRODUCT_READFEEL_REQUIRED_FAMILIES
from emlis_ai_product_readfeel_p3_verdict_split import (
    PRODUCT_READFEEL_P3_VERDICT_SPLIT_VERSION_20260609,
    VERDICT_LAYER_NOT_EVALUATED,
    VERDICT_LAYER_P1_DISPLAY_REPAIR,
    VERDICT_LAYER_P2_RED,
    VERDICT_LAYER_P3_PASS,
    VERDICT_LAYER_P3_REPAIR_REQUIRED,
    VERDICT_LAYER_P3_YELLOW,
    assert_product_readfeel_p3_verdict_split_meta_only_20260609,
)
from emlis_ai_product_readfeel_rubric import (
    DIMENSION_EMOTION_TEMPERATURE_RETENTION,
    DIMENSION_EVIDENCE_BOUNDARY,
    DIMENSION_FOLLOW_DEPTH,
    DIMENSION_INSIGHT_DELTA,
    DIMENSION_NATURALNESS,
    DIMENSION_NON_TEMPLATE,
    DIMENSION_READ_FEELING,
    DIMENSION_SELF_REPORT_RETENTION,
    DIMENSION_SOFT_INFERENCE_SURFACE,
    DIMENSION_STATE_STRUCTURE_RETENTION,
    DIMENSION_STRUCTURE_INSIGHT_CANDIDATE_QUALITY,
    PRODUCT_READFEEL_PRODUCT_READ_FEELING_TARGET,
    PRODUCT_READFEEL_RATING_DIMENSIONS,
    PRODUCT_READFEEL_V1_RATING_DIMENSIONS,
    PRODUCT_READFEEL_V1_REQUIRED_DIMENSIONS,
    PRODUCT_READFEEL_V2_CANDIDATE_DIMENSIONS,
    VERDICT_NOT_EVALUATED,
    aggregate_product_readfeel_blind_qa_reviews,
    assert_product_readfeel_rubric_meta_only,
    normalize_product_readfeel_blind_qa_review,
)
from emlis_ai_product_readfeel_scorecard import (
    assert_product_readfeel_scorecard_meta_only,
    build_product_readfeel_scorecard,
)

PRODUCT_READFEEL_P3_BLIND_QA_REVIEW_VERSION_20260609: Final = (
    "cocolon.emlis.product_readfeel.p3.blind_qa_review.20260609.v1"
)
PRODUCT_READFEEL_P3_BLIND_QA_MATERIAL_VERSION_20260609: Final = (
    "cocolon.emlis.product_readfeel.p3.blind_qa_ratings_material.20260609.v1"
)
PRODUCT_READFEEL_P3_BLIND_QA_SUMMARY_VERSION_20260609: Final = (
    "cocolon.emlis.product_readfeel.p3.blind_qa_ratings_summary.20260609.v1"
)
PRODUCT_READFEEL_P3_BLIND_QA_STEP_20260609: Final = "P3-5_Blind_QA_Ratings_Only_Review"
PRODUCT_READFEEL_P3_BLIND_QA_SOURCE_20260609: Final = (
    "Cocolon_EmlisAI_P3_ProductReadFeel_BlindQARatingsOnlyReview_20260609"
)
PRODUCT_READFEEL_P3_BLIND_QA_PROFILE_20260609: Final = (
    "local_product_readfeel_p3_blind_qa_ratings_only_review"
)

FORBIDDEN_BODY_KEYS_20260609: Final[frozenset[str]] = frozenset(
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
        "memo",
        "memo_text",
        "memoText",
        "memo_action",
        "memoAction",
        "comment_text",
        "commentText",
        "comment_text_body",
        "commentTextBody",
        "candidate_body",
        "candidateBody",
        "reply_text",
        "replyText",
        "surface_text",
        "surfaceText",
        "display_text",
        "displayText",
        "reviewer_note",
        "reviewer_notes",
        "review_notes",
        "free_text_note",
        "body",
        "text",
    }
)
FORBIDDEN_TRUE_FLAGS_20260609: Final[frozenset[str]] = frozenset(
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
        "input_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "source_text_payload_retained",
        "exact_comment_text_required",
        "exact_comment_text_locked",
        "case_specific_runtime_branch",
        "case_specific_runtime_branch_allowed",
        "case_specific_runtime_condition_allowed",
        "runtime_branching_uses_fixture_strings",
        "fixture_text_used_for_runtime_branching",
        "fixed_sentence_template_added",
        "fixed_sentence_template_used",
        "input_specific_template_added",
        "product_gate_ready",
        "product_gate_reached",
        "product_gate_public_release_applied",
        "public_release_applied",
        "product_quality_released",
        "machine_metrics_used_for_read_feeling",
        "read_feeling_auto_filled_from_machine_metrics",
        "read_feeling_auto_estimation_allowed",
        "external_ai_used",
        "local_llm_used",
    }
)

_NUMERIC_DIMENSIONS_20260609: Final[tuple[str, ...]] = tuple(PRODUCT_READFEEL_RATING_DIMENSIONS)
_V1_DIMENSIONS_20260609: Final[tuple[str, ...]] = tuple(PRODUCT_READFEEL_V1_RATING_DIMENSIONS)
_V2_DIMENSIONS_20260609: Final[tuple[str, ...]] = tuple(PRODUCT_READFEEL_V2_CANDIDATE_DIMENSIONS)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _safe_identifier(value: Any, *, default: str = "", max_length: int = 96) -> str:
    text = _clean(value) or default
    safe = "".join(ch if ch.isalnum() or ch in "._:-" else "_" for ch in text)
    safe = safe.strip("_")
    return (safe or default)[:max_length]


def _as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}


def _listify(value: Iterable[Any] | Any | None) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple) or isinstance(value, set):
        return list(value)
    return [value]


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in _listify(values):
        text = _clean(value)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        score = float(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(1.0, score))


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _avg(values: Iterable[Any]) -> float | None:
    scores = [_safe_float(value) for value in values]
    present = [score for score in scores if score is not None]
    if not present:
        return None
    return round(sum(present) / len(present), 4)


def _min(values: Iterable[Any]) -> float | None:
    scores = [_safe_float(value) for value in values]
    present = [score for score in scores if score is not None]
    if not present:
        return None
    return round(min(present), 4)


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(max(0.0, min(1.0, float(numerator) / float(denominator))), 4)


def _body_key_path(value: Any, *, path: str = "payload") -> str | None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            next_path = f"{path}.{key_text}"
            if key_text in FORBIDDEN_BODY_KEYS_20260609:
                return next_path
            found = _body_key_path(item, path=next_path)
            if found:
                return found
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            found = _body_key_path(item, path=f"{path}[{index}]")
            if found:
                return found
    return None


def _forbidden_true_flag_path(value: Any, *, path: str = "payload") -> str | None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            next_path = f"{path}.{key_text}"
            if key_text in FORBIDDEN_TRUE_FLAGS_20260609 and item is True:
                return next_path
            found = _forbidden_true_flag_path(item, path=next_path)
            if found:
                return found
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            found = _forbidden_true_flag_path(item, path=f"{path}[{index}]")
            if found:
                return found
    return None


def assert_product_readfeel_p3_blind_qa_ratings_review_meta_only_20260609(
    payload: Any,
    *,
    source: str = "product_readfeel_p3_blind_qa_ratings_review",
) -> None:
    """Fail if a P3-5 ratings material retains display bodies or contract mutations."""

    body_path = _body_key_path(payload, path=source)
    if body_path:
        raise ValueError(f"P3-5 ratings-only review must not retain display/raw body key: {body_path}")
    true_flag_path = _forbidden_true_flag_path(payload, path=source)
    if true_flag_path:
        raise ValueError(f"P3-5 ratings-only review has forbidden true flag: {true_flag_path}")
    if isinstance(payload, Mapping):
        if payload.get("product_gate_ready") is True:
            raise ValueError(f"{source} must keep product_gate_ready false")
        if payload.get("public_release_applied") is True:
            raise ValueError(f"{source} must keep public_release_applied false")
        # Existing contract-freeze guard keeps the same P0/P1/P2 boundary here.
        assert_emlis_ai_product_quality_contract_freeze_meta_only(payload, source=f"{source}.contract_freeze")
    assert_product_readfeel_rubric_meta_only(payload, source=f"{source}.rubric")


def _lookup_key(record: Mapping[str, Any]) -> str:
    for key in ("case_id", "fixture_id", "candidate_id", "row_id", "review_id"):
        value = _safe_identifier(record.get(key), default="")
        if value:
            return value
    return ""


def _extract_verdict_rows(
    verdict_split_or_rows: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None,
) -> list[dict[str, Any]]:
    if verdict_split_or_rows is None:
        return []
    if isinstance(verdict_split_or_rows, Mapping):
        if verdict_split_or_rows.get("schema_version") == PRODUCT_READFEEL_P3_VERDICT_SPLIT_VERSION_20260609:
            assert_product_readfeel_p3_verdict_split_meta_only_20260609(verdict_split_or_rows)
        rows = verdict_split_or_rows.get("verdict_rows") or verdict_split_or_rows.get("rows") or []
    else:
        rows = verdict_split_or_rows
    result: list[dict[str, Any]] = []
    for index, row in enumerate(rows or []):
        if not isinstance(row, Mapping):
            raise ValueError(f"P3-5 source verdict row[{index}] must be a mapping")
        body_path = _body_key_path(row, path=f"source_verdict_rows[{index}]")
        if body_path:
            raise ValueError(f"P3-5 source verdict row retained display/raw body key: {body_path}")
        assert_product_readfeel_p3_verdict_split_meta_only_20260609(row, source=f"p3_5.source_verdict_rows[{index}]")
        result.append(dict(row))
    return result


def _verdict_row_lookup(rows: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    lookup: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        for key_name in ("case_id", "fixture_id", "candidate_id", "row_id"):
            key = _safe_identifier(row.get(key_name), default="")
            if key and key not in lookup:
                lookup[key] = row
    return lookup


def _matched_verdict_row(review_data: Mapping[str, Any], lookup: Mapping[str, Mapping[str, Any]]) -> Mapping[str, Any]:
    for key_name in ("case_id", "fixture_id", "candidate_id", "row_id"):
        key = _safe_identifier(review_data.get(key_name), default="")
        if key and key in lookup:
            return lookup[key]
    return {}


def normalize_product_readfeel_p3_blind_qa_ratings_review_20260609(
    review: Mapping[str, Any] | None,
    *,
    verdict_rows_by_key: Mapping[str, Mapping[str, Any]] | None = None,
    run_id: str | None = None,
    index: int = 0,
) -> dict[str, Any]:
    """Normalize one P3-5 review row without accepting any textual bodies."""

    source = _as_mapping(review)
    if not source:
        raise ValueError("P3-5 Blind QA review row must be a mapping")
    body_path = _body_key_path(source, path="blind_qa_review")
    if body_path:
        raise ValueError(f"P3-5 Blind QA review row must be ratings-only: {body_path}")
    true_flag_path = _forbidden_true_flag_path(source, path="blind_qa_review")
    if true_flag_path:
        raise ValueError(f"P3-5 Blind QA review row has forbidden true flag: {true_flag_path}")

    matched = _matched_verdict_row(source, verdict_rows_by_key or {})
    normalized = normalize_product_readfeel_blind_qa_review(source)
    dimension_scores = {
        dimension: normalized.get("dimension_scores", {}).get(dimension)
        for dimension in _NUMERIC_DIMENSIONS_20260609
        if normalized.get("dimension_scores", {}).get(dimension) is not None
    }
    ratings = {dimension: score for dimension, score in dimension_scores.items() if score is not None}

    case_id = (
        _safe_identifier(source.get("case_id"), default="")
        or _safe_identifier(source.get("fixture_id"), default="")
        or _safe_identifier(matched.get("case_id"), default="")
        or _safe_identifier(normalized.get("candidate_id"), default="")
    )
    candidate_id = (
        _safe_identifier(source.get("candidate_id"), default="")
        or _safe_identifier(source.get("row_id"), default="")
        or _safe_identifier(matched.get("row_id"), default="")
        or case_id
    )
    family = (
        _clean(source.get("product_readfeel_family"))
        or _clean(source.get("family"))
        or _clean(normalized.get("product_readfeel_family"))
        or _clean(matched.get("product_readfeel_family"))
        or _clean(matched.get("family"))
    )
    source_verdict_layer = _clean(source.get("source_verdict_layer")) or _clean(source.get("verdict_layer")) or _clean(matched.get("verdict_layer"))
    source_verdict = _clean(source.get("source_verdict")) or _clean(source.get("verdict")) or _clean(matched.get("verdict"))
    review_row = {
        "schema_version": PRODUCT_READFEEL_P3_BLIND_QA_REVIEW_VERSION_20260609,
        "version": PRODUCT_READFEEL_P3_BLIND_QA_REVIEW_VERSION_20260609,
        "source": PRODUCT_READFEEL_P3_BLIND_QA_SOURCE_20260609,
        "source_step": PRODUCT_READFEEL_P3_BLIND_QA_STEP_20260609,
        "run_id": _safe_identifier(run_id or source.get("run_id") or matched.get("run_id"), default="p3_5_blind_qa"),
        "review_id": _safe_identifier(source.get("review_id") or normalized.get("review_id"), default=f"p3_5_review_{index:03d}"),
        "candidate_id": candidate_id,
        "case_id": case_id,
        "fixture_id": case_id,
        "product_readfeel_family": family,
        "family": family,
        "coverage_group": _clean(source.get("coverage_group")) or family,
        "coverage_slices": _dedupe(source.get("coverage_slices") or matched.get("coverage_slices")),
        "reviewer_kind": _clean(source.get("reviewer_kind")) or _clean(normalized.get("reviewer_kind")) or "human_blind_qa",
        "ratings": ratings,
        "dimension_scores": dict(normalized.get("dimension_scores") or {}),
        "dimension_verdicts": dict(normalized.get("dimension_verdicts") or {}),
        "v1_score": normalized.get("v1_score"),
        "v2_score": normalized.get("v2_score"),
        "read_feeling_score": normalized.get("read_feeling_score"),
        "read_feeling_source": normalized.get("read_feeling_source"),
        "self_report_retention_score": normalized.get("self_report_retention_score"),
        "state_structure_retention_score": normalized.get("state_structure_retention_score"),
        "emotion_temperature_retention_score": normalized.get("emotion_temperature_retention_score"),
        "follow_depth_score": normalized.get("follow_depth_score"),
        "insight_delta_score": normalized.get("insight_delta_score"),
        "v1_verdict": normalized.get("v1_verdict"),
        "v2_verdict": normalized.get("v2_verdict"),
        "missing_v1_dimensions": list(normalized.get("missing_v1_dimensions") or []),
        "missing_required_dimensions": list(normalized.get("missing_required_dimensions") or []),
        "missing_v2_dimensions": list(normalized.get("missing_v2_dimensions") or []),
        "red_flags": list(normalized.get("red_flags") or []),
        "repair_reasons": _dedupe([*(normalized.get("repair_reasons") or []), *(source.get("repair_reason_codes") or [])]),
        "hard_fail_detected": bool(normalized.get("hard_fail_detected")),
        "product_readfeel_v1_pass": bool(normalized.get("product_readfeel_v1_pass")),
        "product_readfeel_v1_product_pass_candidate": bool(normalized.get("product_readfeel_v1_product_pass_candidate")),
        "structure_insight_v2_ready_candidate": bool(normalized.get("structure_insight_v2_ready_candidate")),
        "insight_delta_release_blocker": False,
        "v2_insight_delta_release_blocker": False,
        "v2_dimensions_release_blocker": False,
        "source_verdict": source_verdict,
        "source_verdict_layer": source_verdict_layer,
        "source_failure_buckets": _dedupe(source.get("source_failure_buckets") or matched.get("failure_buckets")),
        "source_reason_codes": _dedupe(source.get("source_reason_codes") or matched.get("reason_codes")),
        "source_blocker_ids": _dedupe(source.get("source_blocker_ids") or matched.get("blocker_ids")),
        "source_target_layers": _dedupe(source.get("source_target_layers") or matched.get("target_layers")),
        "verdict_reason_rating_connected": bool(matched),
        "p2_red_review_context": source_verdict_layer == VERDICT_LAYER_P2_RED,
        "p3_repair_required_context": source_verdict_layer == VERDICT_LAYER_P3_REPAIR_REQUIRED,
        "p3_yellow_context": source_verdict_layer == VERDICT_LAYER_P3_YELLOW,
        "p3_pass_context": source_verdict_layer == VERDICT_LAYER_P3_PASS,
        "p3_not_evaluated_context": source_verdict_layer == VERDICT_LAYER_NOT_EVALUATED,
        "ratings_only_payload": True,
        "public_text_payload_excluded": True,
        "comment_text_body_included": False,
        "comment_text_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "machine_metrics_separated_from_blind_qa": True,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_auto_estimation_allowed": False,
        "exact_comment_text_required": False,
        "case_specific_runtime_branch": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "comment_text_written_by_scorecard": False,
        "public_response_key_added": False,
        "public_response_key_change": False,
        "response_shape_changed": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "gate_relaxed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "template_gate_relaxed": False,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "public_release_applied": False,
        "product_quality_released": False,
    }
    assert_product_readfeel_p3_blind_qa_ratings_review_meta_only_20260609(review_row)
    return review_row


def _family_rating_summary(review_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_family: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in review_rows:
        family = _clean(row.get("product_readfeel_family")) or _clean(row.get("family")) or "unknown"
        by_family[family].append(row)

    summary_rows: list[dict[str, Any]] = []
    for family in sorted(by_family):
        rows = by_family[family]
        dim_average = {
            dimension: _avg((row.get("dimension_scores") or {}).get(dimension) for row in rows)
            for dimension in _NUMERIC_DIMENSIONS_20260609
        }
        dim_min = {
            dimension: _min((row.get("dimension_scores") or {}).get(dimension) for row in rows)
            for dimension in _NUMERIC_DIMENSIONS_20260609
        }
        lowest_v1 = min(
            rows,
            key=lambda row: _safe_float(row.get("v1_score")) if _safe_float(row.get("v1_score")) is not None else 2.0,
        )
        layer_counts = Counter(_clean(row.get("source_verdict_layer")) for row in rows)
        summary_rows.append(
            {
                "product_readfeel_family": family,
                "review_count": len(rows),
                "case_ids": sorted(_safe_identifier(row.get("case_id"), default="") for row in rows if row.get("case_id")),
                "v1_score_average": _avg(row.get("v1_score") for row in rows),
                "v1_score_min": _min(row.get("v1_score") for row in rows),
                "read_feeling_average": dim_average.get(DIMENSION_READ_FEELING),
                "read_feeling_min": dim_min.get(DIMENSION_READ_FEELING),
                "naturalness_average": dim_average.get(DIMENSION_NATURALNESS),
                "naturalness_min": dim_min.get(DIMENSION_NATURALNESS),
                "non_template_average": dim_average.get(DIMENSION_NON_TEMPLATE),
                "non_template_min": dim_min.get(DIMENSION_NON_TEMPLATE),
                "dimension_averages": dim_average,
                "dimension_minimums": dim_min,
                "lowest_v1_case_id": _safe_identifier(lowest_v1.get("case_id"), default=""),
                "source_verdict_layer_counts": {key: int(value) for key, value in layer_counts.items() if key},
                "source_blocker_ids": sorted({
                    blocker
                    for row in rows
                    for blocker in _dedupe(row.get("source_blocker_ids"))
                }),
                "ratings_only_payload": True,
                "comment_text_body_included": False,
                "raw_input_included": False,
                "candidate_body_included": False,
            }
        )
    return summary_rows


def _public_summary(
    *,
    run_id: str,
    review_rows: Sequence[Mapping[str, Any]],
    verdict_rows: Sequence[Mapping[str, Any]],
    blind_qa_aggregate: Mapping[str, Any],
    family_summary: Sequence[Mapping[str, Any]],
    source_verdict_summary: Mapping[str, Any],
) -> dict[str, Any]:
    expected_review_count = len(verdict_rows)
    reviewed_case_ids = {_safe_identifier(row.get("case_id"), default="") for row in review_rows if row.get("case_id")}
    expected_case_ids = {_safe_identifier(row.get("case_id"), default="") for row in verdict_rows if row.get("case_id")}
    unreviewed_case_count = max(0, len(expected_case_ids - reviewed_case_ids)) if expected_case_ids else 0
    required_observed = sorted({
        _clean(row.get("product_readfeel_family") or row.get("family"))
        for row in review_rows
        if _clean(row.get("product_readfeel_family") or row.get("family")) in PRODUCT_READFEEL_REQUIRED_FAMILIES
    })
    missing_review_families = [family for family in PRODUCT_READFEEL_REQUIRED_FAMILIES if family not in set(required_observed)]
    layer_counts = Counter(_clean(row.get("source_verdict_layer")) for row in review_rows)
    p2_red_count = _safe_int(source_verdict_summary.get("p2_red_count"), 0)
    review_count = len(review_rows)
    read_feeling_score = blind_qa_aggregate.get("read_feeling_score")
    naturalness_score = (blind_qa_aggregate.get("dimension_scores") or {}).get(DIMENSION_NATURALNESS)
    non_template_score = (blind_qa_aggregate.get("dimension_scores") or {}).get(DIMENSION_NON_TEMPLATE)
    if p2_red_count > 0:
        decision = "return_to_p2_surface_safety"
    elif review_count == 0:
        decision = "wait_for_blind_qa_ratings"
    elif read_feeling_score is None:
        decision = "wait_for_blind_qa_ratings"
    elif float(read_feeling_score) < PRODUCT_READFEEL_PRODUCT_READ_FEELING_TARGET:
        decision = "continue_p3_readfeel_repair"
    else:
        decision = "advance_to_p4_family_tuning_candidate"

    summary = {
        "schema_version": PRODUCT_READFEEL_P3_BLIND_QA_SUMMARY_VERSION_20260609,
        "version": PRODUCT_READFEEL_P3_BLIND_QA_SUMMARY_VERSION_20260609,
        "source": PRODUCT_READFEEL_P3_BLIND_QA_SOURCE_20260609,
        "source_step": PRODUCT_READFEEL_P3_BLIND_QA_STEP_20260609,
        "run_id": run_id,
        "run_profile": PRODUCT_READFEEL_P3_BLIND_QA_PROFILE_20260609,
        "expected_review_count": expected_review_count,
        "review_count": review_count,
        "reviewed_case_count": len(reviewed_case_ids),
        "unreviewed_case_count": unreviewed_case_count,
        "all_expected_cases_reviewed": bool(expected_case_ids and expected_case_ids <= reviewed_case_ids),
        "blind_qa_ready": bool(blind_qa_aggregate.get("blind_qa_ready")),
        "blind_qa_ratings_applied": bool(review_rows),
        "ratings_only_review_ready": bool(review_rows),
        "required_families": list(PRODUCT_READFEEL_REQUIRED_FAMILIES),
        "observed_review_families": required_observed,
        "missing_review_families": missing_review_families,
        "all_required_families_reviewed": not missing_review_families and bool(required_observed),
        "family_review_counts": {
            row.get("product_readfeel_family"): int(row.get("review_count") or 0)
            for row in family_summary
        },
        "family_score_minimums_visible": bool(family_summary),
        "family_score_averages_visible": bool(family_summary),
        "family_rating_summary": list(family_summary),
        "source_verdict_layer_review_counts": {key: int(value) for key, value in layer_counts.items() if key},
        "p2_red_count": p2_red_count,
        "p2_red_present": p2_red_count > 0,
        "p2_red_blocks_product_readfeel_repair": p2_red_count > 0,
        "ratings_do_not_override_p2_red": True,
        "red_repair_yellow_reasons_connected_to_ratings": all(
            bool(row.get("verdict_reason_rating_connected")) for row in review_rows
        ) if review_rows else False,
        "review_rows_have_source_verdict_context": all(
            bool(row.get("source_verdict_layer")) for row in review_rows
        ) if review_rows else False,
        "read_feeling_score": read_feeling_score,
        "read_feeling_source": blind_qa_aggregate.get("read_feeling_source"),
        "naturalness_score": naturalness_score,
        "non_template_score": non_template_score,
        "v1_score": blind_qa_aggregate.get("v1_score"),
        "v1_pass_rate": blind_qa_aggregate.get("v1_pass_rate"),
        "read_feeling_pass_rate": blind_qa_aggregate.get("read_feeling_pass_rate"),
        "read_feeling_product_target": PRODUCT_READFEEL_PRODUCT_READ_FEELING_TARGET,
        "read_feeling_product_target_met": bool(
            read_feeling_score is not None and float(read_feeling_score) >= PRODUCT_READFEEL_PRODUCT_READ_FEELING_TARGET
        ),
        "dimension_scores": dict(blind_qa_aggregate.get("dimension_scores") or {}),
        "dimension_pass_rates": dict(blind_qa_aggregate.get("dimension_pass_rates") or {}),
        "v2_dimensions_are_backlog_only": True,
        "insight_delta_release_blocker": False,
        "v2_insight_delta_release_blocker": False,
        "release_blockers_include_insight_delta": False,
        "decision": decision,
        "p3_0_contract_freeze_respected": True,
        "p3_1_baseline_case_matrix_used": expected_review_count >= 60,
        "p3_2_local_review_packet_read_outside_scorecard": True,
        "p3_3_inventory_connection_used": bool(source_verdict_summary),
        "p3_4_verdict_split_used": bool(verdict_rows),
        "p3_5_blind_qa_ratings_only_review_applied": True,
        "local_review_packet_retained": False,
        "local_review_packet_body_retained": False,
        "ratings_only_payload": True,
        "public_text_payload_excluded": True,
        "comment_text_body_included": False,
        "comment_text_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "machine_metrics_separated_from_blind_qa": True,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_auto_estimation_allowed": False,
        "exact_comment_text_required": False,
        "case_specific_runtime_branch": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "comment_text_written_by_scorecard": False,
        "public_response_key_added": False,
        "public_response_key_change": False,
        "response_shape_changed": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "gate_relaxed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "template_gate_relaxed": False,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "public_release_applied": False,
        "product_quality_released": False,
    }
    assert_product_readfeel_p3_blind_qa_ratings_review_meta_only_20260609(summary)
    return summary


def build_product_readfeel_p3_blind_qa_ratings_review_20260609(
    *,
    blind_qa_reviews: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
    reviews: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
    verdict_split: Mapping[str, Any] | None = None,
    verdict_rows: Sequence[Mapping[str, Any]] | None = None,
    current_output_inventory: Mapping[str, Any] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Build the P3-5 ratings-only material and connect it to scorecard.

    ``blind_qa_reviews`` must already be ratings-only.  This function does not
    create ratings from machine metrics or from P3-4 verdicts.
    """

    rows_source = verdict_rows if verdict_rows is not None else verdict_split
    source_verdict_rows = _extract_verdict_rows(rows_source)
    source_summary = _as_mapping(verdict_split.get("summary") if isinstance(verdict_split, Mapping) else {})
    if isinstance(verdict_split, Mapping) and not source_summary:
        source_summary = _as_mapping(verdict_split.get("public_summary"))
    lookup = _verdict_row_lookup(source_verdict_rows)
    raw_reviews = list(blind_qa_reviews if blind_qa_reviews is not None else reviews or [])
    run_id_value = _safe_identifier(
        run_id
        or (source_summary.get("run_id") if source_summary else None)
        or (source_verdict_rows[0].get("run_id") if source_verdict_rows else None),
        default="p3_5_blind_qa_ratings_review",
    )
    normalized_reviews = [
        normalize_product_readfeel_p3_blind_qa_ratings_review_20260609(
            review,
            verdict_rows_by_key=lookup,
            run_id=run_id_value,
            index=index + 1,
        )
        for index, review in enumerate(raw_reviews)
    ]
    blind_qa_aggregate = aggregate_product_readfeel_blind_qa_reviews(normalized_reviews)
    family_summary = _family_rating_summary(normalized_reviews)
    inventory = _as_mapping(current_output_inventory)
    if not inventory and isinstance(verdict_split, Mapping):
        inventory = _as_mapping(verdict_split.get("current_output_inventory_after_verdict_split")) or _as_mapping(
            verdict_split.get("source_current_output_inventory")
        )
    scorecard = build_product_readfeel_scorecard(
        current_output_inventory=inventory,
        blind_qa_reviews=normalized_reviews,
        blind_qa_aggregate=blind_qa_aggregate,
        run_id=run_id_value,
    )
    assert_product_readfeel_scorecard_meta_only(scorecard, source="p3_5.product_readfeel_scorecard")
    summary = _public_summary(
        run_id=run_id_value,
        review_rows=normalized_reviews,
        verdict_rows=source_verdict_rows,
        blind_qa_aggregate=blind_qa_aggregate,
        family_summary=family_summary,
        source_verdict_summary=source_summary,
    )
    payload = {
        "schema_version": PRODUCT_READFEEL_P3_BLIND_QA_MATERIAL_VERSION_20260609,
        "version": PRODUCT_READFEEL_P3_BLIND_QA_MATERIAL_VERSION_20260609,
        "source": PRODUCT_READFEEL_P3_BLIND_QA_SOURCE_20260609,
        "source_step": PRODUCT_READFEEL_P3_BLIND_QA_STEP_20260609,
        "run_id": run_id_value,
        "run_profile": PRODUCT_READFEEL_P3_BLIND_QA_PROFILE_20260609,
        "review_rows": normalized_reviews,
        "review_row_count": len(normalized_reviews),
        "blind_qa_aggregate": blind_qa_aggregate,
        "family_rating_summary": family_summary,
        "product_readfeel_scorecard": scorecard,
        "public_summary": summary,
        "summary": summary,
        "source_verdict_row_count": len(source_verdict_rows),
        "source_verdict_summary": {
            "p2_red_count": _safe_int(source_summary.get("p2_red_count"), 0),
            "p3_repair_required_count": _safe_int(source_summary.get("p3_repair_required_count"), 0),
            "p3_yellow_count": _safe_int(source_summary.get("p3_yellow_count"), 0),
            "pass_count": _safe_int(source_summary.get("pass_count"), 0),
            "not_evaluated_count": _safe_int(source_summary.get("not_evaluated_count"), 0),
            "decision": _clean(source_summary.get("decision")),
        },
        "p3_5_blind_qa_ratings_only_review_applied": True,
        "ratings_only_payload": True,
        "public_text_payload_excluded": True,
        "local_review_packet_retained": False,
        "local_review_packet_body_retained": False,
        "comment_text_body_included": False,
        "comment_text_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "machine_metrics_separated_from_blind_qa": True,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_auto_estimation_allowed": False,
        "exact_comment_text_required": False,
        "case_specific_runtime_branch": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "comment_text_written_by_scorecard": False,
        "public_response_key_added": False,
        "public_response_key_change": False,
        "response_shape_changed": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "gate_relaxed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "template_gate_relaxed": False,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "public_release_applied": False,
        "product_quality_released": False,
    }
    assert_product_readfeel_p3_blind_qa_ratings_review_meta_only_20260609(payload)
    assert_product_readfeel_rubric_meta_only(blind_qa_aggregate, source="p3_5.blind_qa_aggregate")
    return payload


def build_product_readfeel_p3_blind_qa_ratings_public_summary_20260609(
    material_or_reviews: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    if isinstance(material_or_reviews, Mapping) and material_or_reviews.get("schema_version") == PRODUCT_READFEEL_P3_BLIND_QA_MATERIAL_VERSION_20260609:
        summary = dict(material_or_reviews.get("public_summary") or material_or_reviews.get("summary") or {})
    else:
        summary = build_product_readfeel_p3_blind_qa_ratings_review_20260609(
            blind_qa_reviews=material_or_reviews if isinstance(material_or_reviews, Sequence) else None,
        )["public_summary"]
    assert_product_readfeel_p3_blind_qa_ratings_review_meta_only_20260609(summary)
    return summary


def dump_product_readfeel_p3_blind_qa_ratings_public_summary_20260609(
    material_or_reviews: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None = None,
) -> str:
    summary = build_product_readfeel_p3_blind_qa_ratings_public_summary_20260609(material_or_reviews)
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "PRODUCT_READFEEL_P3_BLIND_QA_REVIEW_VERSION_20260609",
    "PRODUCT_READFEEL_P3_BLIND_QA_MATERIAL_VERSION_20260609",
    "PRODUCT_READFEEL_P3_BLIND_QA_SUMMARY_VERSION_20260609",
    "PRODUCT_READFEEL_P3_BLIND_QA_STEP_20260609",
    "assert_product_readfeel_p3_blind_qa_ratings_review_meta_only_20260609",
    "normalize_product_readfeel_p3_blind_qa_ratings_review_20260609",
    "build_product_readfeel_p3_blind_qa_ratings_review_20260609",
    "build_product_readfeel_p3_blind_qa_ratings_public_summary_20260609",
    "dump_product_readfeel_p3_blind_qa_ratings_public_summary_20260609",
]
