# -*- coding: utf-8 -*-
from __future__ import annotations

"""Runtime Surface Quality Step11 Blind QA / Long-run connection.

Step11 prepares Product Gate candidate material without making a release
judgment.  Blind QA candidates are row/coverage/classification metadata,
reviews are ratings-only, and Long-run uses surface signature keys instead of
raw input or public ``comment_text`` bodies.
"""

import json
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from emlis_ai_long_term_quality_service import (
    RUNTIME_SURFACE_LONG_RUN_SIGNATURE_STEP,
    RUNTIME_SURFACE_LONG_RUN_SIGNATURE_VERSION,
    assert_runtime_surface_long_run_signature_meta_only,
    build_runtime_surface_long_run_signature_report,
)

from emlis_ai_product_readfeel_long_run_product_gate import (
    PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_STEP,
    PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_VERSION,
    build_product_readfeel_long_run_product_gate,
    normalize_product_readfeel_long_run_product_gate_to_scorecard_fields,
)
from emlis_ai_product_readfeel_rubric import aggregate_product_readfeel_blind_qa_reviews
from emlis_ai_product_readfeel_scorecard import build_product_readfeel_scorecard

RUNTIME_SURFACE_BLIND_QA_LONG_RUN_VERSION = "emlis.runtime_surface_blind_qa_long_run.v1"
RUNTIME_SURFACE_BLIND_QA_CANDIDATE_VERSION = "emlis.runtime_surface_blind_qa_candidate.v1"
RUNTIME_SURFACE_LONG_RUN_SIGNATURE_DIVERSITY_VERSION = "emlis.runtime_surface_long_run_signature_diversity.v1"
RUNTIME_SURFACE_BLIND_QA_LONG_RUN_STEP = "Step11_Blind_QA_Long_run"
RUNTIME_SURFACE_BLIND_QA_LONG_RUN_READ_FEELING_PRODUCT_TARGET = 0.90
RUNTIME_SURFACE_BLIND_QA_LONG_RUN_REQUIRED_DIMENSIONS: tuple[str, ...] = (
    "read_feeling",
    "evidence_retention",
    "distance",
    "naturalness",
    "non_template",
)

_DIMENSION_ALIASES = {
    "read_feeling": "read_feeling",
    "read_feeling_score": "read_feeling",
    "read": "read_feeling",
    "input_specific_structure_reflected": "read_feeling",
    "evidence_retention": "evidence_retention",
    "evidence": "evidence_retention",
    "evidence_bound": "evidence_retention",
    "grounding": "evidence_retention",
    "distance": "distance",
    "tone_distance": "distance",
    "tone_distance_stable": "distance",
    "naturalness": "naturalness",
    "natural": "naturalness",
    "surface_naturalness": "naturalness",
    "non_template": "non_template",
    "non-template": "non_template",
    "template": "non_template",
    "natural_but_not_template": "non_template",
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
    "memo",
    "memo_text",
    "memoText",
    "current_input",
    "currentInput",
    "comment_text",
    "commentText",
    "input_feedback_comment",
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
    "machine_metrics_used_for_read_feeling",
    "read_feeling_auto_filled_from_machine_metrics",
    "read_feeling_auto_estimation_allowed",
    "display_gate_relaxed",
    "grounding_gate_relaxed",
    "template_gate_relaxed",
    "reader_gate_relaxed",
    "gate_relaxed",
    "response_shape_changed",
    "public_response_key_change",
    "api_route_changed",
    "db_physical_name_changed",
    "rn_visible_contract_changed",
    "product_gate_ready",
    "product_gate_reached",
    "product_gate_achieved",
    "product_gate_public_release_applied",
    "public_release_applied",
    "product_quality_released",
)
_REQUIRED_COVERAGE_GROUPS = (
    "short_daily",
    "long_meaning_arc",
    "conflict",
    "recovery",
    "pressure",
    "desire_fear",
    "relationship",
)


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).strip()


def _safe_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(k): v for k, v in value.items()}
    return {}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, (tuple, set)):
        return list(value)
    return [value]


def _dedupe(values: Iterable[Any] | Any) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in _as_list(values):
        text = _clean(item)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(value: Any) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(max(0.0, min(1.0, numerator / denominator)), 4)


def _phase11_product_readfeel_machine_metrics(events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    eligible = 0
    displayed = 0
    expected_binding = 0
    supported_binding = 0
    reason_required = 0
    reason_covered = 0
    template_major = 0
    safety_major = 0
    signatures: list[str] = []
    for event in events:
        eligible += _int(event.get("eligible_count") or 1)
        if (
            event.get("display_confirmed") is True
            or event.get("public_passed") is True
            or event.get("backend_public_passed") is True
            or _clean(event.get("observation_status")).lower() == "passed"
            or _int(event.get("passed_display_count")) > 0
        ):
            displayed += max(1, _int(event.get("passed_display_count") or 1))
        expected_binding += _int(event.get("expected_binding_count") or event.get("binding_count"))
        supported_binding += _int(event.get("binding_supported_sentence_count") or event.get("binding_count"))
        reason_required += _int(event.get("reason_required_count"))
        reason_covered += _int(event.get("reason_covered_count"))
        template_major += _int(event.get("template_major_count")) + _int(event.get("surface_template_major_count"))
        safety_major += _int(event.get("safety_major_count"))
        signature = _surface_signature_family_key(event)
        if signature:
            signatures.append(signature)
    repeat_count = sum(max(0, signatures.count(signature) - 1) for signature in set(signatures))
    return {
        "display_reach_rate": _rate(displayed, eligible),
        "binding_pass_rate": _rate(supported_binding, expected_binding) if expected_binding else 1.0,
        "reason_coverage_rate": _rate(reason_covered, reason_required) if reason_required else 1.0,
        "template_major_count": template_major,
        "safety_major_count": safety_major,
        "surface_signature_repeat_rate": _rate(repeat_count, len(signatures)),
        "surface_signature_repeat_count": repeat_count,
    }


def _avg(values: Iterable[Any]) -> float | None:
    scores: list[float] = []
    for value in values:
        score = _float(value)
        if score is not None:
            scores.append(max(0.0, min(1.0, score)))
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


def assert_runtime_surface_blind_qa_long_run_meta_only(
    value: Mapping[str, Any],
    *,
    source: str = "runtime_surface_blind_qa_long_run",
) -> None:
    if _contains_forbidden_text_payload_key(value):
        raise ValueError(f"{source} must stay meta-only and must not include text payload keys")
    for flag in _FORBIDDEN_TRUE_FLAGS:
        if value.get(flag) is True:
            raise ValueError(f"{source} violates fixed contract: {flag}=true")


def _coverage_group(event: Mapping[str, Any]) -> str:
    raw = _clean(event.get("coverage_group"))
    if raw and raw.lower() not in {"unknown", "unclassified", "missing", "none", "null"}:
        return raw
    return "coverage_group_missing"


def _surface_signature_family_key(event: Mapping[str, Any]) -> str:
    nested = _safe_mapping(event.get("surface_quality_signature")) or _safe_mapping(event.get("step2_surface_quality_signature"))
    return (
        _clean(event.get("surface_signature_family_key"))
        or _clean(event.get("signature_family_key"))
        or _clean(nested.get("surface_signature_family_key"))
        or _clean(nested.get("signature_family_key"))
        or _clean(event.get("surface_signature_id"))
        or _clean(nested.get("surface_signature_id"))
    )


def _candidate_id(event: Mapping[str, Any], index: int) -> str:
    return (
        _clean(event.get("row_id"))
        or _clean(event.get("candidate_id"))
        or _clean(event.get("trace_id"))
        or _clean(event.get("emotion_log_id"))
        or f"blindqa-candidate-{index}"
    )


def _display_confirmed(event: Mapping[str, Any]) -> bool:
    return bool(event.get("display_confirmed") is True or _int(event.get("passed_display_count")) > 0 or _int(event.get("scorecard_passed_display_count")) > 0)


def _public_passed(event: Mapping[str, Any]) -> bool:
    if event.get("public_passed") is True or event.get("public_passed_for_blind_qa") is True:
        return True
    if _display_confirmed(event) and (event.get("backend_public_passed") is True or _clean(event.get("observation_status")).lower() == "passed"):
        return True
    return _clean(event.get("observation_status")).lower() == "passed" and _int(event.get("passed_display_count")) > 0


def build_runtime_surface_blind_qa_candidates(
    events: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for index, raw in enumerate(list(events or []), start=1):
        event = _safe_mapping(raw)
        assert_runtime_surface_blind_qa_long_run_meta_only(event, source=f"step11_candidate_source_event[{index}]")
        public_passed = _public_passed(event)
        candidate = {
            "version": RUNTIME_SURFACE_BLIND_QA_CANDIDATE_VERSION,
            "source_step": RUNTIME_SURFACE_BLIND_QA_LONG_RUN_STEP,
            "candidate_kind": "runtime_surface_blind_qa_candidate_meta",
            "candidate_index": index,
            "candidate_id": _candidate_id(event, index),
            "row_id": _clean(event.get("row_id")),
            "trace_id": _clean(event.get("trace_id")),
            "emotion_log_id": _clean(event.get("emotion_log_id")),
            "coverage_group": _coverage_group(event),
            "classification": _clean(event.get("measurement_classification") or event.get("classification")),
            "observation_status": _clean(event.get("observation_status")),
            "public_passed": public_passed,
            "display_confirmed": _display_confirmed(event),
            "reviewable_for_blind_qa": public_passed,
            "blind_qa_review_required": public_passed,
            "ratings_required": list(RUNTIME_SURFACE_BLIND_QA_LONG_RUN_REQUIRED_DIMENSIONS),
            "surface_signature_id": _clean(event.get("surface_signature_id")) or _surface_signature_family_key(event),
            "surface_signature_family_key": _surface_signature_family_key(event),
            "composer_source": _clean(event.get("composer_source") or event.get("runtime_composer_source")),
            "read_feeling_score": None,
            "read_feeling_source": "blind_qa_review_only",
            "machine_metrics_used_for_read_feeling": False,
            "read_feeling_auto_filled_from_machine_metrics": False,
            "read_feeling_auto_estimation_allowed": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
        }
        assert_runtime_surface_blind_qa_long_run_meta_only(candidate, source="runtime_surface_blind_qa_candidate")
        candidates.append(candidate)
    return candidates


def normalize_runtime_surface_blind_qa_review(review: Mapping[str, Any] | None) -> dict[str, Any]:
    data = _safe_mapping(_strip_forbidden_text_payload_keys(_safe_mapping(review)))
    assert_runtime_surface_blind_qa_long_run_meta_only(data, source="runtime_surface_blind_qa_review")
    ratings = _safe_mapping(data.get("ratings")) or _safe_mapping(data.get("dimension_ratings"))
    if not ratings:
        ratings = {key: value for key, value in data.items() if _DIMENSION_ALIASES.get(str(key).strip().lower())}
    dimension_scores: dict[str, float | None] = {dimension: None for dimension in RUNTIME_SURFACE_BLIND_QA_LONG_RUN_REQUIRED_DIMENSIONS}
    for raw_key, raw_value in ratings.items():
        dimension = _DIMENSION_ALIASES.get(str(raw_key).strip().lower())
        if not dimension:
            continue
        score = _score_from_verdict(raw_value)
        if score is None:
            continue
        dimension_scores[dimension] = max(0.0, min(1.0, score))
    red_count = sum(1 for score in dimension_scores.values() if score == 0.0)
    evaluated_scores = [score for score in dimension_scores.values() if score is not None]
    read_score = dimension_scores.get("read_feeling")
    overall = _avg(evaluated_scores)
    candidate_id = _clean(data.get("candidate_id")) or _clean(data.get("row_id")) or _clean(data.get("trace_id")) or _clean(data.get("emotion_log_id"))
    normalized = {
        "version": RUNTIME_SURFACE_BLIND_QA_LONG_RUN_VERSION,
        "source_step": RUNTIME_SURFACE_BLIND_QA_LONG_RUN_STEP,
        "review_kind": "runtime_surface_blind_qa_rating_only_review",
        "review_id": _clean(data.get("review_id") or data.get("id")),
        "candidate_id": candidate_id,
        "row_id": _clean(data.get("row_id")),
        "trace_id": _clean(data.get("trace_id")),
        "emotion_log_id": _clean(data.get("emotion_log_id")),
        "coverage_group": _coverage_group(data),
        "dimension_scores": dimension_scores,
        "read_feeling_score": read_score,
        "score": overall,
        "red_count": red_count,
        "passed": bool(overall is not None and read_score is not None and read_score >= RUNTIME_SURFACE_BLIND_QA_LONG_RUN_READ_FEELING_PRODUCT_TARGET and red_count == 0),
        "ratings_only_payload": True,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_auto_estimation_allowed": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
    }
    assert_runtime_surface_blind_qa_long_run_meta_only(normalized, source="normalized_runtime_surface_blind_qa_review")
    return normalized


def _aggregate_reviews(reviews: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    normalized = [normalize_runtime_surface_blind_qa_review(review) for review in reviews]
    read_scores = [review.get("read_feeling_score") for review in normalized if review.get("read_feeling_score") is not None]
    overall_scores = [review.get("score") for review in normalized if review.get("score") is not None]
    read_score = _avg(read_scores)
    review_count = len(normalized)
    pass_count = sum(1 for review in normalized if review.get("passed") is True)
    red_review_count = sum(1 for review in normalized if _int(review.get("red_count")) > 0)
    return {
        "version": RUNTIME_SURFACE_BLIND_QA_LONG_RUN_VERSION,
        "source_step": RUNTIME_SURFACE_BLIND_QA_LONG_RUN_STEP,
        "blind_qa_ready": bool(normalized),
        "review_count": review_count,
        "pass_count": pass_count,
        "red_review_count": red_review_count,
        "read_feeling_score": read_score,
        "overall_score": _avg(overall_scores),
        "read_feeling_pass_rate": _rate(sum(1 for score in read_scores if float(score) >= RUNTIME_SURFACE_BLIND_QA_LONG_RUN_READ_FEELING_PRODUCT_TARGET), review_count),
        "read_feeling_product_gate_target": RUNTIME_SURFACE_BLIND_QA_LONG_RUN_READ_FEELING_PRODUCT_TARGET,
        "reviews": normalized,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
    }


def build_runtime_surface_long_run_signature_diversity(
    *,
    events: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None = None,
    previous_signature_records: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    base = build_runtime_surface_long_run_signature_report(
        events=events,
        previous_signature_records=previous_signature_records,
        required_coverage_groups=list(_REQUIRED_COVERAGE_GROUPS),
    )
    assert_runtime_surface_long_run_signature_meta_only(base)
    rows = list(base.get("coverage_rows") or [])
    sample_count = _int(base.get("current_signature_sample_count"))
    unique_count = sum(_int(row.get("unique_current_signature_count")) for row in rows if isinstance(row, Mapping))
    repeat_count = _int(base.get("surface_signature_repeat_count"))
    groups_needing_attention = [
        _clean(row.get("coverage_group"))
        for row in rows
        if isinstance(row, Mapping) and (_int(row.get("surface_signature_repeat_count")) > 0 or not row.get("passed"))
    ]
    augmented = dict(base)
    augmented.update(
        {
            "version": RUNTIME_SURFACE_LONG_RUN_SIGNATURE_DIVERSITY_VERSION,
            "base_long_run_signature_version": RUNTIME_SURFACE_LONG_RUN_SIGNATURE_VERSION,
            "source_step": RUNTIME_SURFACE_BLIND_QA_LONG_RUN_STEP,
            "step": RUNTIME_SURFACE_BLIND_QA_LONG_RUN_STEP,
            "long_run_surface_signature_diversity_ready": bool(base.get("long_run_ready")),
            "long_run_surface_signature_diversity_rate": _rate(unique_count, sample_count),
            "long_run_surface_signature_repeat_rate": float(base.get("surface_signature_repeat_rate") or 0.0),
            "long_run_surface_signature_repeat_detected": repeat_count > 0,
            "long_run_surface_signature_repeat_count": repeat_count,
            "long_run_groups_needing_attention": groups_needing_attention,
            "long_run_uses_comment_text": False,
            "long_run_uses_raw_input": False,
            "raw_input_included": False,
            "comment_text_body_included": False,
        }
    )
    assert_runtime_surface_blind_qa_long_run_meta_only(augmented, source="runtime_surface_long_run_signature_diversity")
    return augmented


def build_runtime_surface_blind_qa_long_run_report(
    *,
    events: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None = None,
    blind_qa_reviews: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None = None,
    blind_qa_candidates: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None = None,
    previous_signature_records: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None = None,
    run_id: str = "",
) -> dict[str, Any]:
    events_list = [dict(_safe_mapping(event)) for event in list(events or []) if _safe_mapping(event)]
    for index, event in enumerate(events_list, start=1):
        assert_runtime_surface_blind_qa_long_run_meta_only(event, source=f"runtime_surface_step11_event[{index}]")
    candidates = [dict(_safe_mapping(candidate)) for candidate in list(blind_qa_candidates or []) if _safe_mapping(candidate)]
    if not candidates:
        candidates = build_runtime_surface_blind_qa_candidates(events_list)
    for index, candidate in enumerate(candidates, start=1):
        assert_runtime_surface_blind_qa_long_run_meta_only(candidate, source=f"runtime_surface_step11_candidate[{index}]")
    reviews_list = [dict(_safe_mapping(review)) for review in list(blind_qa_reviews or []) if _safe_mapping(review)]
    qa = _aggregate_reviews(reviews_list)
    review_ids = {
        _clean(review.get("candidate_id")) or _clean(review.get("row_id")) or _clean(review.get("trace_id")) or _clean(review.get("emotion_log_id"))
        for review in qa.get("reviews", [])
    }
    review_ids.discard("")
    reviewable_ids = [_clean(candidate.get("candidate_id")) for candidate in candidates if candidate.get("reviewable_for_blind_qa") is True and _clean(candidate.get("candidate_id"))]
    unreviewed_ids = [candidate_id for candidate_id in reviewable_ids if candidate_id not in review_ids]
    long_run = build_runtime_surface_long_run_signature_diversity(
        events=events_list,
        previous_signature_records=previous_signature_records,
    )
    product_readfeel_blind_qa = aggregate_product_readfeel_blind_qa_reviews(reviews_list)
    product_readfeel_scorecard = build_product_readfeel_scorecard(
        events=events_list,
        blind_qa_reviews=reviews_list,
        blind_qa_aggregate=product_readfeel_blind_qa,
        machine_metrics=_phase11_product_readfeel_machine_metrics(events_list),
        run_id=run_id,
    )
    product_readfeel_phase11_gate = build_product_readfeel_long_run_product_gate(
        events=events_list,
        product_readfeel_scorecard=product_readfeel_scorecard,
        runtime_long_run_summary=long_run,
        blind_qa_aggregate=product_readfeel_blind_qa,
    )
    product_readfeel_phase11_gate_fields = normalize_product_readfeel_long_run_product_gate_to_scorecard_fields(
        product_readfeel_phase11_gate
    )
    blockers: list[str] = []
    if unreviewed_ids:
        blockers.append("blind_qa_missing")
    if not qa["blind_qa_ready"]:
        blockers.append("blind_qa_not_evaluated")
    if qa["blind_qa_ready"] and (qa.get("read_feeling_score") is None or float(qa.get("read_feeling_score") or 0.0) < RUNTIME_SURFACE_BLIND_QA_LONG_RUN_READ_FEELING_PRODUCT_TARGET):
        blockers.append("read_feeling_score_below_product_gate_target")
    if qa.get("red_review_count", 0):
        blockers.append("blind_qa_red_review_detected")
    for blocker in _dedupe(long_run.get("product_gate_candidate_blockers") or long_run.get("release_blockers")):
        if blocker not in blockers:
            blockers.append(blocker)
    blind_qa_ready = bool(candidates and qa["blind_qa_ready"] and not unreviewed_ids)
    long_run_ready = bool(long_run.get("long_run_surface_signature_diversity_ready") or long_run.get("long_run_ready"))
    read_pass = bool(qa.get("read_feeling_score") is not None and float(qa.get("read_feeling_score") or 0.0) >= RUNTIME_SURFACE_BLIND_QA_LONG_RUN_READ_FEELING_PRODUCT_TARGET)
    material_ready = bool(blind_qa_ready and long_run_ready and read_pass and not blockers)
    report = {
        "version": RUNTIME_SURFACE_BLIND_QA_LONG_RUN_VERSION,
        "source_step": RUNTIME_SURFACE_BLIND_QA_LONG_RUN_STEP,
        "step": RUNTIME_SURFACE_BLIND_QA_LONG_RUN_STEP,
        "run_id": _clean(run_id),
        "runtime_surface_blind_qa_long_run_connected": True,
        "step11_blind_qa_long_run_connected": True,
        "runtime_surface_blind_qa_long_run_ready": material_ready,
        "step11_blind_qa_long_run_ready": material_ready,
        "step11_blind_qa_long_run_summary_ready": material_ready,
        "product_gate_candidate_material_ready": material_ready,
        "product_gate_candidate_ready": material_ready,
        "blind_qa_candidate_count": len(candidates),
        "candidate_count": len(candidates),
        "reviewable_blind_qa_candidate_count": len(reviewable_ids),
        "reviewable_candidate_count": len(reviewable_ids),
        "blind_qa_review_count": qa["review_count"],
        "blind_qa_missing_count": len(unreviewed_ids),
        "unreviewed_reviewable_candidate_count": len(unreviewed_ids),
        "unreviewed_reviewable_candidate_ids": unreviewed_ids,
        "candidate_ids": [candidate.get("candidate_id") for candidate in candidates if candidate.get("candidate_id")],
        "reviewable_candidate_ids": reviewable_ids,
        "blind_qa_candidates": candidates,
        "blind_qa_review_summary": qa,
        "blind_qa_metrics": qa,
        "blind_qa_ready": blind_qa_ready,
        "read_feeling_score": qa.get("read_feeling_score"),
        "read_feeling_source": "blind_qa_review_ratings" if qa["blind_qa_ready"] else "not_evaluated",
        "read_feeling_product_target": RUNTIME_SURFACE_BLIND_QA_LONG_RUN_READ_FEELING_PRODUCT_TARGET,
        "read_feeling_product_target_met": read_pass,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_auto_estimation_allowed": False,
        "long_run_signature_version": RUNTIME_SURFACE_LONG_RUN_SIGNATURE_VERSION,
        "long_run_signature_step": RUNTIME_SURFACE_LONG_RUN_SIGNATURE_STEP,
        "long_run_signature_report": long_run,
        "long_run_signature_diversity": long_run,
        "long_run_ready": long_run_ready,
        "long_run_surface_signature_diversity_ready": bool(long_run.get("long_run_surface_signature_diversity_ready")),
        "long_run_surface_signature_diversity_rate": float(long_run.get("long_run_surface_signature_diversity_rate") or 0.0),
        "long_run_surface_signature_repeat_rate": float(long_run.get("long_run_surface_signature_repeat_rate") or 0.0),
        "long_run_surface_signature_repeat_count": _int(long_run.get("long_run_surface_signature_repeat_count")),
        "long_run_surface_signature_repeat_detected": bool(long_run.get("long_run_surface_signature_repeat_detected")),
        "long_run_groups_needing_attention": list(long_run.get("long_run_groups_needing_attention") or []),
        "surface_signature_repeat_rate": float(long_run.get("long_run_surface_signature_repeat_rate") or 0.0),
        "surface_signature_repeat_count": _int(long_run.get("long_run_surface_signature_repeat_count")),
        "product_readfeel_phase11_long_run_product_gate_version": PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_VERSION,
        "product_readfeel_phase11_long_run_product_gate_step": PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_STEP,
        "phase11_product_readfeel_long_run_product_gate": product_readfeel_phase11_gate,
        "phase11_product_readfeel_long_run_product_gate_fields": product_readfeel_phase11_gate_fields,
        "phase11_product_readfeel_long_run_product_gate_ready": bool(
            product_readfeel_phase11_gate_fields.get("phase11_product_readfeel_long_run_product_gate_ready")
        ),
        "product_readfeel_phase11_ready": bool(
            product_readfeel_phase11_gate_fields.get("product_readfeel_phase11_ready")
        ),
        "product_readfeel_phase11_v1_product_pass_candidate": bool(
            product_readfeel_phase11_gate_fields.get("product_readfeel_phase11_v1_product_pass_candidate")
        ),
        "product_readfeel_phase11_v2_structure_insight_ready": bool(
            product_readfeel_phase11_gate_fields.get("product_readfeel_phase11_v2_structure_insight_ready")
        ),
        "product_readfeel_phase11_v1_product_pass_blockers": list(
            product_readfeel_phase11_gate_fields.get("product_readfeel_phase11_v1_product_pass_blockers") or []
        ),
        "product_readfeel_phase11_v2_structure_insight_ready_blockers": list(
            product_readfeel_phase11_gate_fields.get("product_readfeel_phase11_v2_structure_insight_ready_blockers") or []
        ),
        "product_readfeel_phase11_consecutive_5_v1_product_pass_ready": bool(
            product_readfeel_phase11_gate_fields.get("product_readfeel_phase11_consecutive_5_v1_product_pass_ready")
        ),
        "product_readfeel_phase11_consecutive_10_v1_product_pass_ready": bool(
            product_readfeel_phase11_gate_fields.get("product_readfeel_phase11_consecutive_10_v1_product_pass_ready")
        ),
        "product_readfeel_phase11_family_cross_surface_repetition_detected": bool(
            product_readfeel_phase11_gate_fields.get("product_readfeel_phase11_family_cross_surface_repetition_detected")
        ),
        "product_readfeel_phase11_insight_surface_same_syntax_repetition_detected": bool(
            product_readfeel_phase11_gate_fields.get("product_readfeel_phase11_insight_surface_same_syntax_repetition_detected")
        ),
        "product_readfeel_phase11_release_judgment_deferred": bool(
            product_readfeel_phase11_gate_fields.get("product_readfeel_phase11_release_judgment_deferred")
        ),
        "product_readfeel_phase11_product_gate_ready": False,
        "product_readfeel_phase11_public_release_applied": False,
        "qa_gaps": blockers,
        "step11_qa_gaps": blockers,
        "step11_release_blockers": blockers,
        "release_blockers": blockers,
        "product_gate_candidate_blockers": blockers,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "product_gate_achieved": False,
        "product_gate_public_release_applied": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "comment_text_contract": "passed_only",
        "blind_qa_candidate_includes_text": False,
        "blind_qa_review_includes_text": False,
        "long_run_uses_comment_text": False,
        "long_run_uses_raw_input": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "gate_relaxed": False,
    }
    assert_runtime_surface_blind_qa_long_run_meta_only(report)
    return report


def build_runtime_surface_blind_qa_long_run_summary(
    *,
    events: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None = None,
    blind_qa_reviews: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None = None,
    blind_qa_candidates: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None = None,
    previous_signature_records: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None = None,
    run_id: str = "",
) -> dict[str, Any]:
    return build_runtime_surface_blind_qa_long_run_report(
        events=events,
        blind_qa_reviews=blind_qa_reviews,
        blind_qa_candidates=blind_qa_candidates,
        previous_signature_records=previous_signature_records,
        run_id=run_id,
    )


def normalize_runtime_surface_blind_qa_long_run_to_scorecard_fields(summary: Mapping[str, Any]) -> dict[str, Any]:
    data = _safe_mapping(summary)
    assert_runtime_surface_blind_qa_long_run_meta_only(data, source="runtime_surface_blind_qa_long_run_scorecard_source")
    fields = {
        "version": RUNTIME_SURFACE_BLIND_QA_LONG_RUN_VERSION,
        "source_step": RUNTIME_SURFACE_BLIND_QA_LONG_RUN_STEP,
        "step11_blind_qa_long_run_ready": bool(data.get("step11_blind_qa_long_run_ready")),
        "runtime_surface_blind_qa_long_run_ready": bool(data.get("runtime_surface_blind_qa_long_run_ready")),
        "runtime_surface_blind_qa_long_run_version": _clean(data.get("version")) or RUNTIME_SURFACE_BLIND_QA_LONG_RUN_VERSION,
        "runtime_surface_blind_qa_long_run_step": _clean(data.get("step") or data.get("source_step")) or RUNTIME_SURFACE_BLIND_QA_LONG_RUN_STEP,
        "long_run_surface_signature_diversity_ready": bool(data.get("long_run_surface_signature_diversity_ready")),
        "long_run_surface_signature_diversity_rate": float(data.get("long_run_surface_signature_diversity_rate") or 0.0),
        "long_run_surface_signature_repeat_rate": float(data.get("long_run_surface_signature_repeat_rate") or data.get("surface_signature_repeat_rate") or 0.0),
        "long_run_surface_signature_repeat_detected": bool(data.get("long_run_surface_signature_repeat_detected") or _int(data.get("surface_signature_repeat_count")) > 0),
        "long_run_groups_needing_attention": _dedupe(data.get("long_run_groups_needing_attention")),
        "long_run_signature_diversity": _safe_mapping(data.get("long_run_signature_diversity")),
        "blind_qa_candidate_count": _int(data.get("blind_qa_candidate_count") or data.get("candidate_count")),
        "reviewable_blind_qa_candidate_count": _int(data.get("reviewable_blind_qa_candidate_count") or data.get("reviewable_candidate_count")),
        "blind_qa_review_count": _int(data.get("blind_qa_review_count")),
        "unreviewed_reviewable_candidate_count": _int(data.get("unreviewed_reviewable_candidate_count") or data.get("blind_qa_missing_count")),
        "blind_qa_missing_count": _int(data.get("blind_qa_missing_count")),
        "read_feeling_score": data.get("read_feeling_score"),
        "read_feeling_source": data.get("read_feeling_source"),
        "read_feeling_product_target_met": bool(data.get("read_feeling_product_target_met")),
        "qa_gaps": _dedupe(data.get("qa_gaps")),
        "step11_release_blockers": _dedupe(data.get("step11_release_blockers") or data.get("release_blockers")),
        "product_readfeel_phase11_long_run_product_gate_version": _clean(
            data.get("product_readfeel_phase11_long_run_product_gate_version")
        ) or PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_VERSION,
        "product_readfeel_phase11_long_run_product_gate_step": _clean(
            data.get("product_readfeel_phase11_long_run_product_gate_step")
        ) or PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_STEP,
        "phase11_product_readfeel_long_run_product_gate_ready": bool(
            data.get("phase11_product_readfeel_long_run_product_gate_ready")
        ),
        "product_readfeel_phase11_ready": bool(data.get("product_readfeel_phase11_ready")),
        "product_readfeel_phase11_v1_product_pass_candidate": bool(
            data.get("product_readfeel_phase11_v1_product_pass_candidate")
        ),
        "product_readfeel_phase11_v2_structure_insight_ready": bool(
            data.get("product_readfeel_phase11_v2_structure_insight_ready")
        ),
        "product_readfeel_phase11_v1_product_pass_blockers": _dedupe(
            data.get("product_readfeel_phase11_v1_product_pass_blockers")
        ),
        "product_readfeel_phase11_v2_structure_insight_ready_blockers": _dedupe(
            data.get("product_readfeel_phase11_v2_structure_insight_ready_blockers")
        ),
        "product_readfeel_phase11_consecutive_5_v1_product_pass_ready": bool(
            data.get("product_readfeel_phase11_consecutive_5_v1_product_pass_ready")
        ),
        "product_readfeel_phase11_consecutive_10_v1_product_pass_ready": bool(
            data.get("product_readfeel_phase11_consecutive_10_v1_product_pass_ready")
        ),
        "product_readfeel_phase11_family_cross_surface_repetition_detected": bool(
            data.get("product_readfeel_phase11_family_cross_surface_repetition_detected")
        ),
        "product_readfeel_phase11_insight_surface_same_syntax_repetition_detected": bool(
            data.get("product_readfeel_phase11_insight_surface_same_syntax_repetition_detected")
        ),
        "product_readfeel_phase11_release_judgment_deferred": bool(
            data.get("product_readfeel_phase11_release_judgment_deferred")
        ),
        "product_readfeel_phase11_product_gate_ready": False,
        "product_readfeel_phase11_public_release_applied": False,
        "phase11_product_readfeel_long_run_product_gate_fields": _safe_mapping(
            data.get("phase11_product_readfeel_long_run_product_gate_fields")
        ),
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "product_gate_achieved": False,
        "public_release_applied": False,
        "product_gate_public_release_applied": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
    }
    assert_runtime_surface_blind_qa_long_run_meta_only(fields, source="runtime_surface_blind_qa_long_run_scorecard_fields")
    return fields


def dump_runtime_surface_blind_qa_long_run_summary(summary: Mapping[str, Any]) -> str:
    data = _strip_forbidden_text_payload_keys(_safe_mapping(summary))
    assert_runtime_surface_blind_qa_long_run_meta_only(data, source="runtime_surface_blind_qa_long_run_dump")
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "RUNTIME_SURFACE_BLIND_QA_CANDIDATE_VERSION",
    "RUNTIME_SURFACE_BLIND_QA_LONG_RUN_READ_FEELING_PRODUCT_TARGET",
    "RUNTIME_SURFACE_BLIND_QA_LONG_RUN_REQUIRED_DIMENSIONS",
    "RUNTIME_SURFACE_BLIND_QA_LONG_RUN_STEP",
    "RUNTIME_SURFACE_BLIND_QA_LONG_RUN_VERSION",
    "RUNTIME_SURFACE_LONG_RUN_SIGNATURE_DIVERSITY_VERSION",
    "PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_VERSION",
    "PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_STEP",
    "assert_runtime_surface_blind_qa_long_run_meta_only",
    "build_runtime_surface_blind_qa_candidates",
    "build_runtime_surface_blind_qa_long_run_report",
    "build_runtime_surface_blind_qa_long_run_summary",
    "build_runtime_surface_long_run_signature_diversity",
    "dump_runtime_surface_blind_qa_long_run_summary",
    "normalize_runtime_surface_blind_qa_long_run_to_scorecard_fields",
    "normalize_runtime_surface_blind_qa_review",
]
