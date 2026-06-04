# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 4 meta-only scorecard for EmlisAI Product Read Feel.

The Phase 4 evaluator aggregates Product Read Feel family verdicts, machine
metrics, and ratings-only Blind QA metrics without touching runtime surfaces.
It is intentionally a scorecard material layer: it does not write
``comment_text``, does not add public response keys, and does not turn
``product_gate_ready`` or public release flags on.  ``insight_delta`` is kept as
Structure Insight v2 readiness material only, never as an initial release
blocker.
"""

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
import json
from typing import Any, Final

from emlis_ai_product_readfeel_current_output_inventory import (
    PRODUCT_READFEEL_CURRENT_OUTPUT_INVENTORY_STEP,
    PRODUCT_READFEEL_CURRENT_OUTPUT_INVENTORY_VERSION,
    PRODUCT_READFEEL_REQUIRED_FAMILIES,
    build_product_readfeel_current_output_inventory,
    normalize_product_readfeel_current_output_inventory_to_scorecard_fields,
)
from emlis_ai_product_readfeel_rubric import (
    DIMENSION_EMOTION_TEMPERATURE_RETENTION,
    DIMENSION_FOLLOW_DEPTH,
    DIMENSION_INSIGHT_DELTA,
    DIMENSION_READ_FEELING,
    DIMENSION_SELF_REPORT_RETENTION,
    DIMENSION_STATE_STRUCTURE_RETENTION,
    PRODUCT_READFEEL_PRODUCT_READ_FEELING_TARGET,
    PRODUCT_READFEEL_RUBRIC_STEP,
    PRODUCT_READFEEL_RATING_DIMENSIONS,
    PRODUCT_READFEEL_RUBRIC_VERSION,
    PRODUCT_READFEEL_V1_REQUIRED_DIMENSIONS,
    PRODUCT_READFEEL_V2_INSIGHT_READY_TARGET,
    VERDICT_NOT_EVALUATED,
    VERDICT_PASS,
    VERDICT_PRODUCT_PASS,
    VERDICT_RED,
    VERDICT_REPAIR_REQUIRED,
    VERDICT_STRUCTURE_INSIGHT_READY,
    VERDICT_YELLOW,
    aggregate_product_readfeel_blind_qa_reviews,
    assert_product_readfeel_rubric_meta_only,
    normalize_product_readfeel_machine_metrics_boundary,
    normalize_product_readfeel_rubric_to_scorecard_fields,
)

PRODUCT_READFEEL_SCORECARD_VERSION: Final = "cocolon.emlis.product_readfeel.scorecard.v1"
PRODUCT_READFEEL_SCORECARD_FIELDS_VERSION: Final = "cocolon.emlis.product_readfeel.scorecard_fields.v1"
PRODUCT_READFEEL_SCORECARD_PHASE4_STEP: Final = "Phase4_Product_Read_Feel_Evaluator_Meta_Only"
PRODUCT_READFEEL_SCORECARD_STEP: Final = PRODUCT_READFEEL_SCORECARD_PHASE4_STEP
PRODUCT_READFEEL_SCORECARD_SOURCE: Final = "Cocolon_EmlisAI_ProductReadFeel_Phase4_MetaOnlyScorecard"
PRODUCT_READFEEL_SCORECARD_TYPE: Final = "product_readfeel_evaluation"
PRODUCT_READFEEL_TARGET_STEP: Final = "ProductReadFeel_v1"

PRODUCT_READFEEL_DISPLAY_REACH_TARGET: Final = 0.90
PRODUCT_READFEEL_BINDING_PASS_TARGET: Final = 0.98
PRODUCT_READFEEL_REASON_COVERAGE_TARGET: Final = 1.0

class ProductReadFeelScorecardMetaOnlyError(ValueError):
    """Raised when Phase 4 Product Read Feel scorecard material is not meta-only."""


_VERDICT_ORDER: Final[dict[str, int]] = {
    VERDICT_PRODUCT_PASS: 0,
    VERDICT_PASS: 1,
    VERDICT_YELLOW: 2,
    VERDICT_NOT_EVALUATED: 2,
    VERDICT_REPAIR_REQUIRED: 3,
    VERDICT_RED: 4,
}
_VERDICT_KEYS: Final[tuple[str, ...]] = (
    VERDICT_RED,
    VERDICT_REPAIR_REQUIRED,
    VERDICT_YELLOW,
    VERDICT_PASS,
    VERDICT_PRODUCT_PASS,
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
        "memo",
        "memo_text",
        "memoText",
        "memo_action",
        "memoAction",
        "emotion_details",
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
        "surfaceText",
        "accepted_surface_probe",
        "blocked_surface_probe",
        "realized_text",
        "display_text",
        "candidate_body",
        "body",
        "text",
    }
)
_FORBIDDEN_TRUE_FLAGS: Final[tuple[str, ...]] = (
    "raw_input_included",
    "raw_text_included",
    "input_text_included",
    "comment_text_included",
    "comment_text_body_included",
    "candidate_body_included",
    "machine_metrics_used_for_read_feeling",
    "read_feeling_auto_filled_from_machine_metrics",
    "read_feeling_auto_estimation_allowed",
    "comment_text_generated",
    "comment_text_key_written",
    "comment_text_written_by_scorecard",
    "public_response_key_added",
    "public_response_key_change",
    "response_shape_changed",
    "api_route_changed",
    "db_physical_name_changed",
    "rn_visible_contract_changed",
    "rn_visible_title_changed",
    "display_gate_relaxed",
    "grounding_gate_relaxed",
    "reader_gate_relaxed",
    "template_gate_relaxed",
    "gate_relaxed",
    "product_gate_ready",
    "product_gate_reached",
    "product_gate_public_release_applied",
    "public_release_applied",
    "product_quality_released",
    "fixed_sentence_template_used",
    "fixed_completed_sentence_template_added",
    "input_specific_template_added",
    "external_ai_used",
    "local_llm_used",
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


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in _listify(values):
        text = _clean(value)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(max(0.0, min(1.0, float(numerator) / float(denominator))), 4)


def _avg(values: Iterable[Any]) -> float | None:
    scores: list[float] = []
    for value in values:
        score = _safe_float(value)
        if score is not None:
            scores.append(max(0.0, min(1.0, score)))
    if not scores:
        return None
    return round(sum(scores) / len(scores), 4)


def _contains_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in _TEXT_PAYLOAD_KEYS:
                return True
            if _contains_text_payload_key(item):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_text_payload_key(item) for item in value)
    return False


def _strip_text_payload_keys(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _strip_text_payload_keys(item)
            for key, item in value.items()
            if str(key) not in _TEXT_PAYLOAD_KEYS
        }
    if isinstance(value, list):
        return [_strip_text_payload_keys(item) for item in value]
    if isinstance(value, tuple):
        return [_strip_text_payload_keys(item) for item in value]
    return value


def _normalize_verdict(value: Any) -> str:
    text = _clean(value).upper().replace(" ", "_").replace("-", "_")
    aliases = {
        "REPAIR": VERDICT_REPAIR_REQUIRED,
        "REPAIR_REQUIRED": VERDICT_REPAIR_REQUIRED,
        "PRODUCTPASS": VERDICT_PRODUCT_PASS,
        "PRODUCT_PASS": VERDICT_PRODUCT_PASS,
        "STRUCTURE_INSIGHT_READY": VERDICT_STRUCTURE_INSIGHT_READY,
        "PASS": VERDICT_PASS,
        "PASSED": VERDICT_PASS,
        "GREEN": VERDICT_PASS,
        "YELLOW": VERDICT_YELLOW,
        "WARN": VERDICT_YELLOW,
        "WARNING": VERDICT_YELLOW,
        "RED": VERDICT_RED,
        "FAIL": VERDICT_RED,
        "FAILED": VERDICT_RED,
        "NOT_EVALUATED": VERDICT_NOT_EVALUATED,
    }
    return aliases.get(text, VERDICT_NOT_EVALUATED)


def _worst_verdict(values: Iterable[Any]) -> str:
    normalized = [_normalize_verdict(value) for value in values]
    normalized = [value for value in normalized if value]
    if not normalized:
        return VERDICT_NOT_EVALUATED
    return max(normalized, key=lambda value: _VERDICT_ORDER.get(value, _VERDICT_ORDER[VERDICT_NOT_EVALUATED]))


def assert_product_readfeel_scorecard_meta_only(
    value: Any,
    *,
    source: str = "product_readfeel_scorecard",
) -> None:
    """Raise when the Phase 4 scorecard keeps unsafe text or changes contracts."""

    if _contains_text_payload_key(value):
        raise ProductReadFeelScorecardMetaOnlyError(f"{source}: raw input/comment display body key must not be retained")
    if isinstance(value, Mapping):
        for flag in _FORBIDDEN_TRUE_FLAGS:
            if value.get(flag) is True:
                raise ProductReadFeelScorecardMetaOnlyError(f"{source}: forbidden true flag {flag}")
        for item in value.values():
            assert_product_readfeel_scorecard_meta_only(item, source=source)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_product_readfeel_scorecard_meta_only(item, source=source)


def _normalize_machine_metrics(machine_metrics: Mapping[str, Any] | None) -> dict[str, Any]:
    source = _strip_text_payload_keys(_safe_mapping(machine_metrics))
    metrics = normalize_product_readfeel_machine_metrics_boundary(source)
    metrics["version"] = "cocolon.emlis.product_readfeel.phase4.machine_metrics.v1"
    metrics["schema_version"] = "cocolon.emlis.product_readfeel.phase4.machine_metrics.v1"
    metrics["source_step"] = PRODUCT_READFEEL_SCORECARD_PHASE4_STEP
    metrics["target_step"] = PRODUCT_READFEEL_TARGET_STEP
    metrics["display_reach_rate"] = _safe_float(source.get("display_reach_rate"), metrics.get("display_reach_rate"))
    metrics["binding_pass_rate"] = _safe_float(source.get("binding_pass_rate"), metrics.get("binding_pass_rate"))
    metrics["reason_coverage_rate"] = _safe_float(source.get("reason_coverage_rate"), metrics.get("reason_coverage_rate"))
    metrics["template_major_count"] = _safe_int(source.get("template_major_count", metrics.get("template_major_count")), 0)
    metrics["safety_major_count"] = _safe_int(source.get("safety_major_count", metrics.get("safety_major_count")), 0)
    metrics["surface_signature_repeat_rate"] = _safe_float(
        source.get("surface_signature_repeat_rate"), metrics.get("surface_signature_repeat_rate")
    )
    metrics["machine_metrics_ready"] = bool(source) or bool(metrics.get("machine_metrics_ready"))
    metrics["read_feeling_score"] = None
    metrics["read_feeling_source"] = "blind_qa_required_not_machine_metric"
    metrics["read_feeling_requires_blind_qa"] = True
    metrics["machine_metrics_separated_from_blind_qa"] = True
    metrics["machine_metrics_used_for_read_feeling"] = False
    metrics["read_feeling_auto_filled_from_machine_metrics"] = False
    metrics["read_feeling_auto_estimation_allowed"] = False
    metrics["raw_input_included"] = False
    metrics["raw_text_included"] = False
    metrics["comment_text_included"] = False
    metrics["comment_text_body_included"] = False
    metrics["candidate_body_included"] = False
    metrics["comment_text_generated"] = False
    metrics["comment_text_key_written"] = False
    metrics["comment_text_written_by_scorecard"] = False
    metrics["public_response_key_added"] = False
    metrics["public_response_key_change"] = False
    metrics["product_gate_ready"] = False
    metrics["public_release_applied"] = False
    assert_product_readfeel_scorecard_meta_only(metrics, source="product_readfeel_phase4_machine_metrics")
    return metrics


def _review_groups(blind_qa_aggregate: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for review in blind_qa_aggregate.get("reviews") or []:
        data = _safe_mapping(review)
        family = _clean(data.get("product_readfeel_family")) or _clean(data.get("fixture_family"))
        if family:
            groups.setdefault(family, []).append(data)
    return groups


def _dimension_family_score(reviews: Sequence[Mapping[str, Any]], dimension: str) -> float | None:
    return _avg((_safe_mapping(review.get("dimension_scores")).get(dimension) for review in reviews))


def _family_results(
    *,
    inventory: Mapping[str, Any],
    blind_qa_aggregate: Mapping[str, Any],
) -> list[dict[str, Any]]:
    summaries = {
        _clean(summary.get("family")) or _clean(summary.get("product_readfeel_family")): _safe_mapping(summary)
        for summary in inventory.get("family_summaries") or []
        if _safe_mapping(summary)
    }
    family_verdicts = {
        _clean(family): _normalize_verdict(verdict)
        for family, verdict in _safe_mapping(inventory.get("family_verdicts")).items()
    }
    review_groups = _review_groups(blind_qa_aggregate)
    families = []
    for family in PRODUCT_READFEEL_REQUIRED_FAMILIES:
        if family not in families:
            families.append(family)
    for family in sorted(set(summaries) | set(family_verdicts) | set(review_groups)):
        if family and family not in families:
            families.append(family)

    results: list[dict[str, Any]] = []
    for family in families:
        summary = summaries.get(family, {})
        reviews = review_groups.get(family, [])
        inventory_verdict = _normalize_verdict(
            summary.get("verdict") or family_verdicts.get(family) or VERDICT_NOT_EVALUATED
        )
        review_v1_verdict = _worst_verdict(review.get("v1_verdict") for review in reviews)
        if not reviews:
            review_v1_verdict = VERDICT_NOT_EVALUATED
        v1_verdict = _worst_verdict(
            [value for value in (inventory_verdict, review_v1_verdict) if value != VERDICT_NOT_EVALUATED]
            or [inventory_verdict, review_v1_verdict]
        )
        v2_verdict = _worst_verdict(review.get("v2_verdict") for review in reviews)
        if summary.get("v2_structure_insight_backlog") is True and v2_verdict not in {VERDICT_RED, VERDICT_REPAIR_REQUIRED}:
            v2_verdict = VERDICT_YELLOW
        if not reviews and summary.get("v2_structure_insight_backlog") is not True:
            v2_verdict = VERDICT_NOT_EVALUATED
        dimension_scores = {
            DIMENSION_READ_FEELING: _dimension_family_score(reviews, DIMENSION_READ_FEELING),
            DIMENSION_SELF_REPORT_RETENTION: _dimension_family_score(reviews, DIMENSION_SELF_REPORT_RETENTION),
            DIMENSION_STATE_STRUCTURE_RETENTION: _dimension_family_score(reviews, DIMENSION_STATE_STRUCTURE_RETENTION),
            DIMENSION_EMOTION_TEMPERATURE_RETENTION: _dimension_family_score(
                reviews, DIMENSION_EMOTION_TEMPERATURE_RETENTION
            ),
            DIMENSION_FOLLOW_DEPTH: _dimension_family_score(reviews, DIMENSION_FOLLOW_DEPTH),
            DIMENSION_INSIGHT_DELTA: _dimension_family_score(reviews, DIMENSION_INSIGHT_DELTA),
        }
        result = {
            "version": "cocolon.emlis.product_readfeel.phase4.family_result.v1",
            "schema_version": "cocolon.emlis.product_readfeel.phase4.family_result.v1",
            "source_step": PRODUCT_READFEEL_SCORECARD_PHASE4_STEP,
            "product_readfeel_family": family,
            "inventory_item_count": _safe_int(summary.get("item_count"), 0),
            "blind_qa_review_count": len(reviews),
            "inventory_verdict": inventory_verdict,
            "blind_qa_v1_verdict": review_v1_verdict,
            "v1_verdict": v1_verdict,
            "v2_verdict": v2_verdict,
            "dimension_scores": dimension_scores,
            "failure_bucket_counts": dict(summary.get("failure_bucket_counts") or {}),
            "v1_repair_required": v1_verdict in {VERDICT_RED, VERDICT_REPAIR_REQUIRED}
            or summary.get("v1_repair_required") is True,
            "v2_structure_insight_backlog": summary.get("v2_structure_insight_backlog") is True,
            "display_not_reached_count": _safe_int(summary.get("display_not_reached_count"), 0),
            "contract_violation_count": _safe_int(summary.get("contract_violation_count"), 0),
            "surface_breakage_count": _safe_int(summary.get("surface_breakage_count"), 0),
            "readfeel_gap_count": _safe_int(summary.get("readfeel_gap_count"), 0),
            "structure_insight_gap_count": _safe_int(summary.get("structure_insight_gap_count"), 0),
            "mirror_only_detected_count": _safe_int(summary.get("mirror_only_detected_count"), 0),
            "insight_delta_release_blocker": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
            "comment_text_generated": False,
            "comment_text_written_by_scorecard": False,
            "public_response_key_added": False,
            "public_response_key_change": False,
            "product_gate_ready": False,
            "public_release_applied": False,
        }
        assert_product_readfeel_scorecard_meta_only(result, source="product_readfeel_phase4_family_result")
        results.append(result)
    return results


def _threshold_checks(
    *,
    machine: Mapping[str, Any],
    blind_qa: Mapping[str, Any],
    inventory: Mapping[str, Any],
    family_results: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    verdict_counts = Counter(_normalize_verdict(row.get("v1_verdict")) for row in family_results)
    observed_families = set(inventory.get("observed_families") or [])
    missing_families = [family for family in PRODUCT_READFEEL_REQUIRED_FAMILIES if family not in observed_families]
    read_feeling_score = _safe_float(blind_qa.get("read_feeling_score"))
    insight_delta_score = _safe_float(blind_qa.get("insight_delta_score"))
    display_reach_rate = _safe_float(machine.get("display_reach_rate"))
    binding_pass_rate = _safe_float(machine.get("binding_pass_rate"))
    reason_coverage_rate = _safe_float(machine.get("reason_coverage_rate"))
    machine_metrics_ready = bool(machine.get("machine_metrics_ready"))
    machine_thresholds = {
        "display_reach_rate_product_target": bool(
            display_reach_rate is not None and display_reach_rate >= PRODUCT_READFEEL_DISPLAY_REACH_TARGET
        ),
        "binding_pass_rate_product_target": bool(
            binding_pass_rate is not None and binding_pass_rate >= PRODUCT_READFEEL_BINDING_PASS_TARGET
        ),
        "reason_coverage_rate_complete": bool(
            reason_coverage_rate is not None and reason_coverage_rate >= PRODUCT_READFEEL_REASON_COVERAGE_TARGET
        ),
        "template_major_count_zero": _safe_int(machine.get("template_major_count"), 0) == 0,
        "safety_major_count_zero": _safe_int(machine.get("safety_major_count"), 0) == 0,
    }
    v1_family_pass_ready = bool(
        family_results
        and not missing_families
        and verdict_counts.get(VERDICT_RED, 0) == 0
        and verdict_counts.get(VERDICT_REPAIR_REQUIRED, 0) == 0
        and verdict_counts.get(VERDICT_YELLOW, 0) == 0
        and verdict_counts.get(VERDICT_NOT_EVALUATED, 0) == 0
    )
    v1_product_pass_ready = bool(
        v1_family_pass_ready
        and bool(blind_qa.get("blind_qa_ready"))
        and read_feeling_score is not None
        and read_feeling_score >= PRODUCT_READFEEL_PRODUCT_READ_FEELING_TARGET
        and bool(blind_qa.get("v1_product_pass_candidate"))
        and machine_metrics_ready
        and all(machine_thresholds.values())
    )
    v2_structure_insight_ready = bool(
        bool(blind_qa.get("v2_structure_insight_ready_candidate"))
        and insight_delta_score is not None
        and insight_delta_score >= PRODUCT_READFEEL_V2_INSIGHT_READY_TARGET
        and not inventory.get("v2_structure_insight_backlog_families")
        and v1_family_pass_ready
    )
    checks = {
        "machine_metrics_ready": machine_metrics_ready,
        "blind_qa_ready": bool(blind_qa.get("blind_qa_ready")),
        "family_evaluation_ready": bool(family_results),
        "all_required_families_observed": not missing_families,
        "missing_families": missing_families,
        "red_family_count_zero": verdict_counts.get(VERDICT_RED, 0) == 0,
        "repair_required_family_count_zero": verdict_counts.get(VERDICT_REPAIR_REQUIRED, 0) == 0,
        "yellow_family_count_zero": verdict_counts.get(VERDICT_YELLOW, 0) == 0,
        "read_feeling_score_product_target": bool(
            read_feeling_score is not None and read_feeling_score >= PRODUCT_READFEEL_PRODUCT_READ_FEELING_TARGET
        ),
        "read_feeling_source_is_blind_qa": _clean(blind_qa.get("read_feeling_source")) == "blind_qa_review_ratings",
        "v1_product_pass_ready": v1_product_pass_ready,
        "v2_structure_insight_ready": v2_structure_insight_ready,
        "insight_delta_release_blocker": False,
        "public_contract_unchanged": True,
        "comment_text_untouched": True,
        "public_response_key_unchanged": True,
        **machine_thresholds,
    }
    return checks


def _release_blockers(checks: Mapping[str, Any], verdict_counts: Mapping[str, int]) -> list[str]:
    blockers: list[str] = []
    if not checks.get("machine_metrics_ready"):
        blockers.append("product_readfeel_machine_metrics_missing")
    if not checks.get("blind_qa_ready"):
        blockers.append("product_readfeel_blind_qa_missing")
    if not checks.get("all_required_families_observed"):
        blockers.append("product_readfeel_family_coverage_incomplete")
    if verdict_counts.get(VERDICT_RED, 0) > 0:
        blockers.append("product_readfeel_red_family_detected")
    if verdict_counts.get(VERDICT_REPAIR_REQUIRED, 0) > 0:
        blockers.append("product_readfeel_repair_required_family_detected")
    if verdict_counts.get(VERDICT_YELLOW, 0) > 0:
        blockers.append("product_readfeel_yellow_family_detected")
    if not checks.get("read_feeling_score_product_target") and checks.get("blind_qa_ready"):
        blockers.append("product_readfeel_read_feeling_below_product_target")
    if checks.get("machine_metrics_ready"):
        if not checks.get("display_reach_rate_product_target"):
            blockers.append("product_readfeel_display_reach_rate_below_target")
        if not checks.get("binding_pass_rate_product_target"):
            blockers.append("product_readfeel_binding_pass_rate_below_target")
        if not checks.get("reason_coverage_rate_complete"):
            blockers.append("product_readfeel_reason_coverage_incomplete")
        if not checks.get("template_major_count_zero"):
            blockers.append("product_readfeel_template_major_detected")
        if not checks.get("safety_major_count_zero"):
            blockers.append("product_readfeel_safety_major_detected")
    return _dedupe(blockers)


def _v2_readiness_gaps(checks: Mapping[str, Any], blind_qa: Mapping[str, Any], inventory: Mapping[str, Any]) -> list[str]:
    gaps: list[str] = []
    insight_score = _safe_float(blind_qa.get("insight_delta_score"))
    if not blind_qa.get("blind_qa_ready"):
        gaps.append("blind_qa_missing")
    if insight_score is None:
        gaps.append("insight_delta_not_evaluated")
    elif insight_score < PRODUCT_READFEEL_V2_INSIGHT_READY_TARGET:
        gaps.append("insight_delta_below_structure_insight_target")
    if inventory.get("v2_structure_insight_backlog_families"):
        gaps.append("structure_insight_backlog_families_present")
    if not checks.get("v2_structure_insight_ready"):
        gaps.append("structure_insight_v2_not_ready")
    return _dedupe(gaps)


def _aggregate_verdict(
    *,
    checks: Mapping[str, Any],
    verdict_counts: Mapping[str, int],
    family_results: Sequence[Mapping[str, Any]],
) -> str:
    if not family_results:
        return VERDICT_NOT_EVALUATED
    if verdict_counts.get(VERDICT_RED, 0) > 0:
        return VERDICT_RED
    if verdict_counts.get(VERDICT_REPAIR_REQUIRED, 0) > 0 or not checks.get("all_required_families_observed"):
        return VERDICT_REPAIR_REQUIRED
    if checks.get("v1_product_pass_ready"):
        return VERDICT_PRODUCT_PASS
    if verdict_counts.get(VERDICT_YELLOW, 0) > 0 or not checks.get("read_feeling_score_product_target"):
        return VERDICT_YELLOW
    return VERDICT_PASS


def build_product_readfeel_scorecard(
    *,
    events: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
    scorecard_events: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
    records: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
    blind_qa_reviews: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
    machine_metrics: Mapping[str, Any] | None = None,
    current_output_inventory: Mapping[str, Any] | None = None,
    blind_qa_aggregate: Mapping[str, Any] | None = None,
    run_id: str = "",
) -> dict[str, Any]:
    """Build the Phase 4 Product Read Feel evaluator scorecard.

    The result is internal meta-only material.  ``product_gate_ready`` and
    ``public_release_applied`` intentionally remain false even when the v1
    Product Read Feel thresholds are met.
    """

    raw_events: list[Mapping[str, Any] | None] = []
    raw_events.extend(list(events or []))
    raw_events.extend(list(scorecard_events or []))
    raw_events.extend(list(records or []))
    # Phase 4 keeps current-output inventory and ratings-only Blind QA separate.
    # Blind QA reviews may carry v2-only ``insight_delta`` gaps; feeding them
    # into the Phase 1 current-output inventory would incorrectly turn v2
    # readiness material into a v1 family repair bucket.
    inventory = _safe_mapping(current_output_inventory) or build_product_readfeel_current_output_inventory(
        events=raw_events,
        run_id=run_id,
    )
    inventory_fields = normalize_product_readfeel_current_output_inventory_to_scorecard_fields(inventory)
    mirror_only_detector_ready = bool(
        inventory.get("phase6_mirror_only_detector_ready")
        or inventory.get("mirror_only_detector_ready")
        or inventory_fields.get("phase6_product_readfeel_mirror_only_detector_ready")
        or inventory_fields.get("product_readfeel_mirror_only_detector_ready")
    )
    mirror_only_detected_count = _safe_int(inventory.get("mirror_only_detected_count"), 0)
    mirror_only_v2_insight_delta_gap_count = sum(
        1
        for item in inventory.get("items") or []
        if _safe_mapping(item).get("mirror_only_v2_insight_delta_gap") is True
        or _safe_mapping(item).get("v2_insight_delta_gap") is True
    )
    blind_qa = _safe_mapping(blind_qa_aggregate) or aggregate_product_readfeel_blind_qa_reviews(blind_qa_reviews)
    rubric_fields = normalize_product_readfeel_rubric_to_scorecard_fields(blind_qa)
    machine = _normalize_machine_metrics(machine_metrics)
    families = _family_results(inventory=inventory, blind_qa_aggregate=blind_qa)
    family_verdicts = {row["product_readfeel_family"]: row["v1_verdict"] for row in families}
    family_verdict_counter = Counter(row["v1_verdict"] for row in families)
    family_verdict_counts = {key: int(family_verdict_counter.get(key, 0)) for key in _VERDICT_KEYS}
    checks = _threshold_checks(machine=machine, blind_qa=blind_qa, inventory=inventory, family_results=families)
    blockers = _release_blockers(checks, family_verdict_counts)
    v2_gaps = _v2_readiness_gaps(checks, blind_qa, inventory)
    scorecard_verdict = _aggregate_verdict(
        checks=checks,
        verdict_counts=family_verdict_counts,
        family_results=families,
    )
    observed_required_family_count = sum(
        1 for family in PRODUCT_READFEEL_REQUIRED_FAMILIES if family in set(inventory.get("observed_families") or [])
    )
    family_coverage_rate = _rate(observed_required_family_count, len(PRODUCT_READFEEL_REQUIRED_FAMILIES))
    pass_family_count = sum(
        1
        for row in families
        if row.get("product_readfeel_family") in PRODUCT_READFEEL_REQUIRED_FAMILIES
        and row.get("v1_verdict") == VERDICT_PASS
    )
    family_pass_rate = _rate(pass_family_count, len(PRODUCT_READFEEL_REQUIRED_FAMILIES))
    if scorecard_verdict == VERDICT_PRODUCT_PASS:
        family_verdict_counts[VERDICT_PRODUCT_PASS] = max(1, family_verdict_counts.get(VERDICT_PRODUCT_PASS, 0))
    completion_conditions = {
        "family_results_aggregated": bool(families),
        "verdict_counts_aggregated": True,
        "product_pass_aggregated_without_release": True,
        "machine_metrics_and_blind_qa_separated": True,
        "insight_delta_v2_readiness_only": True,
        "comment_text_untouched": True,
        "public_response_key_unchanged": True,
        "phase6_mirror_only_detector_meta_only_connected": mirror_only_detector_ready,
    }
    scorecard_ready = bool(completion_conditions["family_results_aggregated"])
    next_action = "evaluate_structure_insight_candidates"
    if not checks.get("all_required_families_observed"):
        next_action = "complete_product_readfeel_family_coverage"
    elif family_verdict_counts.get(VERDICT_RED, 0) or family_verdict_counts.get(VERDICT_REPAIR_REQUIRED, 0):
        next_action = "repair_product_readfeel_v1_surfaces"
    elif scorecard_verdict == VERDICT_PRODUCT_PASS and checks.get("v2_structure_insight_ready"):
        next_action = "connect_long_run_product_gate_ladder_without_public_release"
    scorecard = {
        "version": PRODUCT_READFEEL_SCORECARD_VERSION,
        "schema_version": PRODUCT_READFEEL_SCORECARD_VERSION,
        "scorecard_fields_version": PRODUCT_READFEEL_SCORECARD_FIELDS_VERSION,
        "source": PRODUCT_READFEEL_SCORECARD_SOURCE,
        "step": PRODUCT_READFEEL_SCORECARD_PHASE4_STEP,
        "target_step": PRODUCT_READFEEL_TARGET_STEP,
        "scorecard_type": PRODUCT_READFEEL_SCORECARD_TYPE,
        "run_id": _clean(run_id),
        "phase4_product_readfeel_scorecard_ready": scorecard_ready,
        "product_readfeel_phase4_ready": scorecard_ready,
        "product_readfeel_scorecard_ready": scorecard_ready,
        "phase6_mirror_only_detector_ready": mirror_only_detector_ready,
        "phase6_product_readfeel_mirror_only_detector_ready": mirror_only_detector_ready,
        "product_readfeel_phase6_ready": mirror_only_detector_ready,
        "product_readfeel_mirror_only_detected_count": mirror_only_detected_count,
        "product_readfeel_mirror_only_v2_insight_delta_gap_count": mirror_only_v2_insight_delta_gap_count,
        "completion_conditions": completion_conditions,
        "current_output_inventory_version": _clean(inventory.get("version"))
        or PRODUCT_READFEEL_CURRENT_OUTPUT_INVENTORY_VERSION,
        "current_output_inventory_step": _clean(inventory.get("step"))
        or PRODUCT_READFEEL_CURRENT_OUTPUT_INVENTORY_STEP,
        "rubric_version": PRODUCT_READFEEL_RUBRIC_VERSION,
        "rubric_step": PRODUCT_READFEEL_RUBRIC_STEP,
        "current_output_inventory_fields": inventory_fields,
        "rubric_fields": rubric_fields,
        "machine_metrics": machine,
        "blind_qa_metrics": blind_qa,
        "machine_metrics_ready": bool(machine.get("machine_metrics_ready")),
        "blind_qa_ready": bool(blind_qa.get("blind_qa_ready")),
        "machine_metrics_separated_from_blind_qa": True,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_requires_blind_qa": True,
        "read_feeling_score": blind_qa.get("read_feeling_score"),
        "read_feeling_source": blind_qa.get("read_feeling_source"),
        "self_report_retention_score": blind_qa.get("self_report_retention_score"),
        "state_structure_retention_score": blind_qa.get("state_structure_retention_score"),
        "emotion_temperature_retention_score": blind_qa.get("emotion_temperature_retention_score"),
        "follow_depth_score": blind_qa.get("follow_depth_score"),
        "insight_delta_score": blind_qa.get("insight_delta_score"),
        "insight_delta_release_blocker": False,
        "v2_insight_delta_release_blocker": False,
        "release_blockers_include_insight_delta": False,
        "rating_dimensions": list(PRODUCT_READFEEL_RATING_DIMENSIONS),
        "v2_readiness_only_dimensions": [DIMENSION_INSIGHT_DELTA],
        "family_results": families,
        "family_verdicts": family_verdicts,
        "family_verdict_counts": family_verdict_counts,
        "verdict_counts": dict(family_verdict_counts),
        "required_families": list(PRODUCT_READFEEL_REQUIRED_FAMILIES),
        "required_family_count": len(PRODUCT_READFEEL_REQUIRED_FAMILIES),
        "observed_required_family_count": observed_required_family_count,
        "family_coverage_rate": family_coverage_rate,
        "family_pass_rate": family_pass_rate,
        "observed_families": list(inventory.get("observed_families") or []),
        "missing_families": list(inventory.get("missing_families") or []),
        "failure_bucket_counts": dict(inventory.get("failure_bucket_counts") or {}),
        "v1_fix_families": list(inventory.get("v1_fix_families") or []),
        "v2_structure_insight_backlog_families": list(
            inventory.get("v2_structure_insight_backlog_families") or []
        ),
        "threshold_checks": checks,
        "v1_product_pass_ready": bool(checks.get("v1_product_pass_ready")),
        "product_pass_candidate": bool(checks.get("v1_product_pass_ready")),
        "v1_product_pass_candidate": bool(checks.get("v1_product_pass_ready")),
        "v2_structure_insight_ready": bool(checks.get("v2_structure_insight_ready")),
        "v2_structure_insight_ready_candidate": bool(blind_qa.get("v2_structure_insight_ready_candidate")),
        "v2_readiness_gaps": v2_gaps,
        "scorecard_verdict": scorecard_verdict,
        "aggregate_verdict": scorecard_verdict,
        "release_blockers": blockers,
        "release_judgment": {
            "release_allowed": False,
            "product_gate_ready": False,
            "public_release_applied": False,
            "insight_delta_release_blocker": False,
        },
        "next_action": next_action,
        "public_text_payload_excluded": True,
        "ratings_only_payload": True,
        "exact_comment_text_required": False,
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "comment_text_written_by_scorecard": False,
        "comment_text_written_by_product_readfeel_scorecard": False,
        "public_response_key_added": False,
        "public_response_key_change": False,
        "response_shape_changed": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "template_gate_relaxed": False,
        "gate_relaxed": False,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "product_gate_public_release_applied": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "external_ai_used": False,
        "local_llm_used": False,
    }
    assert_product_readfeel_scorecard_meta_only(scorecard, source="product_readfeel_phase4_scorecard")
    assert_product_readfeel_rubric_meta_only(blind_qa, source="product_readfeel_phase4_blind_qa_metrics")
    return scorecard


def normalize_product_readfeel_scorecard_to_scorecard_fields(
    scorecard: Mapping[str, Any] | None,
) -> dict[str, Any]:
    data = _safe_mapping(scorecard) or build_product_readfeel_scorecard()
    assert_product_readfeel_scorecard_meta_only(data, source="product_readfeel_phase4_scorecard_fields_source")
    fields = {
        "product_readfeel_scorecard_version": _clean(data.get("version")) or PRODUCT_READFEEL_SCORECARD_VERSION,
        "product_readfeel_scorecard_step": _clean(data.get("step")) or PRODUCT_READFEEL_SCORECARD_PHASE4_STEP,
        "phase4_product_readfeel_scorecard_ready": bool(data.get("phase4_product_readfeel_scorecard_ready")),
        "product_readfeel_phase4_ready": bool(data.get("product_readfeel_phase4_ready")),
        "product_readfeel_scorecard_ready": bool(data.get("product_readfeel_scorecard_ready")),
        "phase6_product_readfeel_mirror_only_detector_ready": bool(data.get("phase6_product_readfeel_mirror_only_detector_ready") or data.get("phase6_mirror_only_detector_ready")),
        "product_readfeel_phase6_ready": bool(data.get("product_readfeel_phase6_ready") or data.get("phase6_product_readfeel_mirror_only_detector_ready")),
        "product_readfeel_mirror_only_detected_count": _safe_int(data.get("product_readfeel_mirror_only_detected_count"), 0),
        "product_readfeel_mirror_only_v2_insight_delta_gap_count": _safe_int(data.get("product_readfeel_mirror_only_v2_insight_delta_gap_count"), 0),
        "product_readfeel_scorecard_type": PRODUCT_READFEEL_SCORECARD_TYPE,
        "product_readfeel_scorecard_verdict": _clean(data.get("scorecard_verdict")),
        "product_readfeel_scorecard_aggregate_verdict": _clean(data.get("aggregate_verdict")),
        "product_readfeel_aggregate_verdict": _clean(data.get("aggregate_verdict")),
        "product_readfeel_v1_verdict": _clean(data.get("aggregate_verdict")),
        "product_readfeel_scorecard_family_verdicts": dict(data.get("family_verdicts") or {}),
        "product_readfeel_scorecard_family_verdict_counts": dict(data.get("family_verdict_counts") or {}),
        "product_readfeel_family_verdict_counts": dict(data.get("family_verdict_counts") or {}),
        "product_readfeel_scorecard_verdict_counts": dict(data.get("verdict_counts") or {}),
        "product_readfeel_verdict_counts": dict(data.get("verdict_counts") or {}),
        "product_readfeel_scorecard_family_results": list(data.get("family_results") or []),
        "product_readfeel_family_results": list(data.get("family_results") or []),
        "product_readfeel_required_family_count": int(data.get("required_family_count") or 0),
        "product_readfeel_observed_required_family_count": int(data.get("observed_required_family_count") or 0),
        "product_readfeel_family_coverage_rate": data.get("family_coverage_rate"),
        "product_readfeel_family_pass_rate": data.get("family_pass_rate"),
        "product_readfeel_aggregate_verdict_counts": dict(data.get("verdict_counts") or {}),
        "product_readfeel_required_family_verdict_counts": dict(data.get("family_verdict_counts") or {}),
        "product_readfeel_red_family_count": int((data.get("family_verdict_counts") or {}).get(VERDICT_RED, 0)),
        "product_readfeel_repair_required_family_count": int(
            (data.get("family_verdict_counts") or {}).get(VERDICT_REPAIR_REQUIRED, 0)
        ),
        "product_readfeel_yellow_family_count": int((data.get("family_verdict_counts") or {}).get(VERDICT_YELLOW, 0)),
        "product_readfeel_pass_family_count": int((data.get("family_verdict_counts") or {}).get(VERDICT_PASS, 0)),
        "product_readfeel_product_pass_count": int((data.get("family_verdict_counts") or {}).get(VERDICT_PRODUCT_PASS, 0)),
        "product_readfeel_scorecard_release_blockers": list(data.get("release_blockers") or []),
        "product_readfeel_scorecard_next_action": _clean(data.get("next_action")),
        "product_readfeel_scorecard_threshold_checks": dict(data.get("threshold_checks") or {}),
        "product_readfeel_scorecard_v1_product_pass_ready": bool(data.get("v1_product_pass_ready")),
        "product_readfeel_v1_product_pass_ready": bool(data.get("v1_product_pass_ready")),
        "product_readfeel_product_pass_candidate": bool(data.get("v1_product_pass_ready")),
        "product_readfeel_v1_product_pass_candidate": bool(data.get("v1_product_pass_ready")),
        "product_readfeel_scorecard_v2_structure_insight_ready": bool(
            data.get("v2_structure_insight_ready")
        ),
        "product_readfeel_v2_structure_insight_ready": bool(data.get("v2_structure_insight_ready")),
        "product_readfeel_v2_structure_insight_ready_candidate": bool(
            data.get("v2_structure_insight_ready_candidate")
        ),
        "product_readfeel_v2_readiness_not_release_blocker": True,
        "product_readfeel_scorecard_v2_readiness_gaps": list(data.get("v2_readiness_gaps") or []),
        "product_readfeel_v2_readiness_gaps": list(data.get("v2_readiness_gaps") or []),
        "product_readfeel_scorecard_insight_delta_release_blocker": False,
        "product_readfeel_insight_delta_release_blocker": False,
        "product_readfeel_v2_insight_delta_release_blocker": False,
        "product_readfeel_release_blockers_include_insight_delta": False,
        "product_readfeel_phase4_internal_gaps": list(data.get("v2_readiness_gaps") or []),
        "product_readfeel_scorecard_machine_metrics_ready": bool(data.get("machine_metrics_ready")),
        "product_readfeel_scorecard_blind_qa_ready": bool(data.get("blind_qa_ready")),
        "product_readfeel_scorecard_machine_metrics_separated_from_blind_qa": True,
        "product_readfeel_scorecard_machine_metrics_used_for_read_feeling": False,
        "product_readfeel_scorecard_read_feeling_auto_filled_from_machine_metrics": False,
        "product_readfeel_scorecard_read_feeling_requires_blind_qa": True,
        "product_readfeel_scorecard_read_feeling_score": data.get("read_feeling_score"),
        "product_readfeel_read_feeling_score": data.get("read_feeling_score"),
        "product_readfeel_scorecard_insight_delta_score": data.get("insight_delta_score"),
        "product_readfeel_insight_delta_score": data.get("insight_delta_score"),
        "product_readfeel_scorecard_comment_text_written_by_scorecard": False,
        "product_readfeel_scorecard_public_response_key_added": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "comment_text_written_by_scorecard": False,
        "public_response_key_added": False,
        "public_response_key_change": False,
        "response_shape_changed": False,
        "product_gate_ready": False,
        "public_release_applied": False,
    }
    assert_product_readfeel_scorecard_meta_only(fields, source="product_readfeel_phase4_scorecard_fields")
    return fields


def dump_product_readfeel_scorecard(scorecard: Mapping[str, Any] | None = None) -> str:
    data = dict(scorecard or build_product_readfeel_scorecard())
    assert_product_readfeel_scorecard_meta_only(data)
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "PRODUCT_READFEEL_SCORECARD_VERSION",
    "PRODUCT_READFEEL_SCORECARD_FIELDS_VERSION",
    "PRODUCT_READFEEL_SCORECARD_PHASE4_STEP",
    "PRODUCT_READFEEL_SCORECARD_STEP",
    "PRODUCT_READFEEL_SCORECARD_TYPE",
    "PRODUCT_READFEEL_DISPLAY_REACH_TARGET",
    "PRODUCT_READFEEL_BINDING_PASS_TARGET",
    "PRODUCT_READFEEL_REASON_COVERAGE_TARGET",
    "ProductReadFeelScorecardMetaOnlyError",
    "assert_product_readfeel_scorecard_meta_only",
    "build_product_readfeel_scorecard",
    "normalize_product_readfeel_scorecard_to_scorecard_fields",
    "dump_product_readfeel_scorecard",
]
