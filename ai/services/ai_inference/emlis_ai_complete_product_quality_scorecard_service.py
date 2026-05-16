# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step6 Product Quality Scorecard / Blind QA for EmlisAI Complete Composer.

This module is intentionally meta-only.  It measures machine metrics and Blind
QA separately, then exposes a ProductQualityScorecard for the next release
ladder step.  It does not write ``comment_text``, relax gates, or change public
response/API/DB/RN contracts.
"""

from collections import Counter, defaultdict
from typing import Any, Iterable, Mapping, Sequence

COMPLETE_PRODUCT_QUALITY_SCORECARD_VERSION = "emlis.complete_product_quality_scorecard.v1"
COMPLETE_PRODUCT_QUALITY_SCORECARD_STAGE = "Step6_Scorecard_Blind_QA"
COMPLETE_PRODUCT_QUALITY_SCORECARD_STEP = COMPLETE_PRODUCT_QUALITY_SCORECARD_STAGE
COMPLETE_PRODUCT_QUALITY_SCORECARD_IMPLEMENTATION_UNIT = "ProductQualityConnection.Step6"
COMPLETE_PRODUCT_QUALITY_BLIND_QA_RUBRIC_VERSION = "emlis.complete_product_quality_blind_qa_rubric.v1"
COMPLETE_PRODUCT_QUALITY_SCORECARD_EVENT_SCHEMA_VERSION = "emlis.complete_product_quality_scorecard_event_schema.v1"
COMPLETE_PRODUCT_QUALITY_BLIND_QA_REVIEW_VERSION = "emlis.complete_product_quality_blind_qa_review.v1"
COMPLETE_PRODUCT_QUALITY_BLIND_QA_AGGREGATE_VERSION = "emlis.complete_product_quality_blind_qa_aggregate.v1"
COMPLETE_PRODUCT_QUALITY_MACHINE_METRICS_VERSION = "emlis.complete_product_quality_machine_metrics.v1"
COMPLETE_PRODUCT_QUALITY_TARGETS_VERSION = "emlis.complete_product_quality_targets.v1"

COMPLETE_PRODUCT_QUALITY_CONNECTION_DISPLAY_TARGET = 0.80
COMPLETE_PRODUCT_GATE_DISPLAY_TARGET = 0.90
COMPLETE_PRODUCT_QUALITY_BINDING_TARGET = 0.98
COMPLETE_PRODUCT_QUALITY_READ_FEELING_INITIAL_TARGET = 0.85
COMPLETE_PRODUCT_QUALITY_READ_FEELING_PRODUCT_TARGET = 0.90
COMPLETE_PRODUCT_QUALITY_REASON_COVERAGE_TARGET = 1.0

_PRODUCT_QUALITY_DIMENSIONS: Sequence[str] = (
    "read_feeling",
    "evidence_retention",
    "distance",
    "naturalness",
    "non_template",
)

_DIMENSION_ALIASES = {
    "read_feeling": "read_feeling",
    "evidence_retention": "evidence_retention",
    "distance": "distance",
    "naturalness": "naturalness",
    "non_template": "non_template",
    "read": "read_feeling",
    "read_feeling_score": "read_feeling",
    "read-feeling": "read_feeling",
    "evidence": "evidence_retention",
    "evidence_retention": "evidence_retention",
    "grounding": "evidence_retention",
    "rooting": "evidence_retention",
    "tone_distance": "distance",
    "distance": "distance",
    "natural": "naturalness",
    "naturalness": "naturalness",
    "surface_naturalness": "naturalness",
    "template": "non_template",
    "non_template": "non_template",
    "non-template": "non_template",
    # Backward-compatible labels used by early Step6 rubric drafts.
    "input_specific_structure_reflected": "read_feeling",
    "relation_kept": "evidence_retention",
    "evidence_bound": "evidence_retention",
    "tone_distance_stable": "distance",
    "natural_but_not_template": "non_template",
    "no_diagnosis_or_personality_claim": "distance",
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

_TEMPLATE_REASON_MARKERS = (
    "template",
    "fixed",
    "role_fixed",
    "raw_echo",
    "over_echo",
    "same_ending",
    "surface_signature_repeat",
    "surface_connector_repetition",
    "signature_repeat",
    "emotion_label_only",
)
_SAFETY_REASON_MARKERS = (
    "safety",
    "diagnosis",
    "diagnostic_tone",
    "overclaim",
    "personality",
    "personality_claim",
    "advice",
    "advice_like",
    "action_instruction",
    "medical",
    "unsafe",
)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _rate(numerator: Any, denominator: Any) -> float:
    den = _safe_int(denominator, 0)
    if den <= 0:
        return 0.0
    return round(max(0.0, min(1.0, float(_safe_int(numerator, 0)) / float(den))), 4)


def _avg(values: Iterable[Any]) -> float | None:
    scores: list[float] = []
    for value in values:
        score = _safe_float(value)
        if score is not None:
            scores.append(max(0.0, min(1.0, score)))
    if not scores:
        return None
    return round(sum(scores) / len(scores), 4)


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple) or isinstance(value, set):
        return list(value)
    return [value]


def _dedupe(values: Iterable[Any] | Any) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in _listify(values):
        text = _clean(item)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _safe_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(k): v for k, v in value.items()}
    return {}



def _strip_forbidden_serialized_payload_key_names(value: Any) -> Any:
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if "raw_text" in key_text:
                continue
            result[key_text] = _strip_forbidden_serialized_payload_key_names(item)
        return result
    if isinstance(value, list):
        return [_strip_forbidden_serialized_payload_key_names(item) for item in value]
    if isinstance(value, tuple):
        return [_strip_forbidden_serialized_payload_key_names(item) for item in value]
    return value

def _score_from_verdict(value: Any) -> float | None:
    text = _clean(value).lower()
    if text in _VERDICT_SCORES:
        return _VERDICT_SCORES[text]
    return _safe_float(value)


def _verdict_from_score(score: float | None) -> str:
    if score is None:
        return "not_evaluated"
    if score >= 0.90:
        return "green"
    if score > 0.0:
        return "yellow"
    return "red"


def _collect_reason_values(record: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    for key in (
        "top_rejection_reasons",
        "rejection_reasons",
        "secondary_reasons",
        "reason_codes",
        "gate_reasons",
        "unsupported_reasons",
    ):
        reasons.extend(_dedupe(record.get(key)))
    for key in (
        "primary_reason",
        "gate_primary_reason",
        "first_failed_reason",
        "failed_stage",
        "stage",
        "unavailable_reason",
        "reason_code",
    ):
        text = _clean(record.get(key))
        if text:
            reasons.append(text)
    gate_results = record.get("gate_results")
    if isinstance(gate_results, Mapping):
        for gate_name, gate in gate_results.items():
            if isinstance(gate, Mapping):
                reasons.extend(_dedupe(gate.get("rejection_reasons")))
                reasons.extend(_dedupe(gate.get("reasons")))
                first = _clean(gate.get("first_failed_reason"))
                if first:
                    reasons.append(f"{gate_name}:{first}")
    return _dedupe(reasons)


def _count_marker_hits(reasons: Sequence[str], markers: Sequence[str]) -> int:
    count = 0
    for reason in reasons:
        lower = reason.lower()
        if any(marker in lower for marker in markers):
            count += 1
    return count


def _source_event(record: Any) -> dict[str, Any]:
    data = _safe_mapping(record)
    if not data:
        return {}
    for key in (
        "product_quality_scorecard_event",
        "complete_product_quality_scorecard_event",
        "complete_scorecard_event",
        "complete_composer_scorecard_event",
        "complete_composer_initial_scorecard_event",
        "scorecard_event",
        "normalized_event",
        "event",
    ):
        nested = data.get(key)
        if isinstance(nested, Mapping):
            return dict(nested)
    return data


def _normalize_product_quality_event(record: Any) -> dict[str, Any]:
    event = _source_event(record)
    if not event:
        return {}

    coverage_group = _clean(event.get("coverage_group")) or "short_daily"
    observation_status = _clean(event.get("observation_status")).lower()
    eligible_count = _safe_int(event.get("eligible_count"), 0)
    if eligible_count <= 0 and (observation_status or event.get("complete_candidate_seen") or event.get("complete_candidate_generated")):
        eligible_count = 1

    passed_display_count = _safe_int(event.get("passed_display_count"), 0)
    if passed_display_count <= 0 and observation_status == "passed":
        passed_display_count = 1 if eligible_count else 0

    rejected_count = _safe_int(event.get("rejected_count"), 0)
    unavailable_count = _safe_int(event.get("unavailable_count"), 0)
    safety_blocked_count = _safe_int(event.get("safety_blocked_count"), 0)
    if eligible_count:
        if observation_status == "rejected" and rejected_count <= 0:
            rejected_count = 1
        if observation_status == "unavailable" and unavailable_count <= 0:
            unavailable_count = 1
        if observation_status == "safety_blocked" and safety_blocked_count <= 0:
            safety_blocked_count = 1

    expected_binding_count = _safe_int(event.get("expected_binding_count"), 0)
    if expected_binding_count <= 0:
        expected_binding_count = _safe_int(event.get("binding_count"), 0)
    binding_supported_count = _safe_int(event.get("binding_supported_sentence_count"), 0)
    if binding_supported_count <= 0:
        binding_supported_count = _safe_int(event.get("binding_pass_count"), 0)
    if expected_binding_count <= 0:
        rate = _safe_float(event.get("sentence_binding_pass_rate"))
        if rate is not None and eligible_count:
            expected_binding_count = eligible_count
            binding_supported_count = int(round(rate * expected_binding_count))

    reasons = _collect_reason_values(event)
    non_pass_count = rejected_count + unavailable_count + safety_blocked_count
    reason_covered = bool(reasons) if non_pass_count else True

    template_major_count = _safe_int(event.get("template_major_count"), 0)
    template_major_count += _safe_int(event.get("surface_variation_major_count"), 0)
    safety_major_count = _safe_int(event.get("safety_major_count"), 0)
    safety_major_count += _safe_int(event.get("tone_diagnostic_count"), 0)
    safety_major_count += _safe_int(event.get("tone_advice_count"), 0)

    if template_major_count <= 0:
        template_major_count = _count_marker_hits(reasons, _TEMPLATE_REASON_MARKERS)
    if safety_major_count <= 0:
        safety_major_count = _count_marker_hits(reasons, _SAFETY_REASON_MARKERS)

    repair_attempt_count = _safe_int(event.get("repair_attempt_count"), 0)
    if repair_attempt_count <= 0 and event.get("repair_attempted"):
        repair_attempt_count = 1
    repair_success_count = _safe_int(event.get("repair_success_count"), 0)
    if repair_success_count <= 0 and event.get("repair_success"):
        repair_success_count = 1

    candidate_generated_count = _safe_int(event.get("candidate_generated_count"), 0)
    if candidate_generated_count <= 0 and event.get("complete_candidate_generated"):
        candidate_generated_count = 1

    return {
        "coverage_group": coverage_group,
        "observation_status": observation_status,
        "eligible_count": eligible_count,
        "candidate_generated_count": candidate_generated_count,
        "passed_display_count": passed_display_count,
        "rejected_count": rejected_count,
        "unavailable_count": unavailable_count,
        "safety_blocked_count": safety_blocked_count,
        "binding_supported_sentence_count": binding_supported_count,
        "expected_binding_count": expected_binding_count,
        "repair_attempt_count": repair_attempt_count,
        "repair_success_count": repair_success_count,
        "template_major_count": template_major_count,
        "safety_major_count": safety_major_count,
        "non_pass_count": non_pass_count,
        "reason_covered_count": 1 if reason_covered and non_pass_count else 0,
        "reason_required_count": non_pass_count,
        "top_rejection_reasons": reasons[:8],
        "reason_counter": dict(Counter(reasons)),
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
    }


def build_complete_product_quality_blind_qa_rubric() -> dict[str, Any]:
    return {
        "version": COMPLETE_PRODUCT_QUALITY_BLIND_QA_RUBRIC_VERSION,
        "target_step": COMPLETE_PRODUCT_QUALITY_SCORECARD_STEP,
        "step": COMPLETE_PRODUCT_QUALITY_SCORECARD_STEP,
        "purpose": "measure_read_feeling_separately_from_machine_metrics",
        "machine_metrics_separated": True,
        "machine_metrics_are_separate": True,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "exact_comment_text_required": False,
        "exact_comment_text_locked": False,
        "read_feeling_connection_target": COMPLETE_PRODUCT_QUALITY_READ_FEELING_INITIAL_TARGET,
        "read_feeling_product_gate_target": COMPLETE_PRODUCT_QUALITY_READ_FEELING_PRODUCT_TARGET,
        "dimensions": {
            "read_feeling": {
                "green": "input_specific_waver_pressure_recovery_or_residue_reflected_within_evidence",
                "yellow": "natural_but_somewhat_generic",
                "red": "generic_comfort_or_unrelated_to_input",
            },
            "evidence_retention": {
                "green": "each_sentence_traces_to_evidence_phrase_or_relation",
                "yellow": "main_sentence_traces_but_closing_is_weak",
                "red": "unsupported_completion_or_cause_claim",
            },
            "distance": {
                "green": "not_too_close_no_command_observation_style",
                "yellow": "comfort_is_somewhat_strong",
                "red": "diagnosis_lecture_action_instruction_or_personality_claim",
            },
            "naturalness": {
                "green": "particles_connectors_and_endings_are_natural_without_noticeable_repetition",
                "yellow": "somewhat_awkward_but_meaning_is_preserved",
                "red": "fragment_connection_emotion_label_only_or_excessive_same_ending",
            },
            "non_template": {
                "green": "same_coverage_does_not_lock_expression_too_much",
                "yellow": "some_endings_or_connectors_are_similar",
                "red": "completed_template_role_fixed_text_or_raw_echo",
            },
        },
    }


def normalize_complete_product_quality_blind_qa_review(review: Mapping[str, Any] | None) -> dict[str, Any]:
    data = _safe_mapping(review)
    ratings = _safe_mapping(data.get("ratings")) or _safe_mapping(data.get("dimension_ratings"))
    if not ratings:
        ratings = {key: value for key, value in data.items() if _DIMENSION_ALIASES.get(str(key))}

    dimension_scores: dict[str, float | None] = {dimension: None for dimension in _PRODUCT_QUALITY_DIMENSIONS}
    dimension_verdicts: dict[str, str] = {dimension: "not_evaluated" for dimension in _PRODUCT_QUALITY_DIMENSIONS}
    for raw_key, raw_value in ratings.items():
        dimension = _DIMENSION_ALIASES.get(str(raw_key).strip().lower())
        if not dimension:
            continue
        score = _score_from_verdict(raw_value)
        if score is None:
            continue
        score = max(0.0, min(1.0, score))
        dimension_scores[dimension] = score
        dimension_verdicts[dimension] = _verdict_from_score(score)

    evaluated_scores = [score for score in dimension_scores.values() if score is not None]
    red_count = sum(1 for verdict in dimension_verdicts.values() if verdict == "red")
    yellow_count = sum(1 for verdict in dimension_verdicts.values() if verdict == "yellow")
    green_count = sum(1 for verdict in dimension_verdicts.values() if verdict == "green")
    score = _avg(evaluated_scores)
    read_score = dimension_scores.get("read_feeling")

    return {
        "version": COMPLETE_PRODUCT_QUALITY_BLIND_QA_REVIEW_VERSION,
        "target_step": COMPLETE_PRODUCT_QUALITY_SCORECARD_STEP,
        "review_id": _clean(data.get("review_id")) or _clean(data.get("id")),
        "fixture_set_id": _clean(data.get("fixture_set_id")),
        "coverage_group": _clean(data.get("coverage_group")),
        "dimension_scores": dimension_scores,
        "dimension_verdicts": dimension_verdicts,
        "score": score,
        "read_feeling_score": read_score,
        "green_count": green_count,
        "yellow_count": yellow_count,
        "red_count": red_count,
        "read_feeling_pass": bool(read_score is not None and read_score >= COMPLETE_PRODUCT_QUALITY_READ_FEELING_INITIAL_TARGET),
        "passed": bool(score is not None and read_score is not None and read_score >= COMPLETE_PRODUCT_QUALITY_READ_FEELING_INITIAL_TARGET and red_count == 0),
        "machine_metrics_separated": True,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
    }


def aggregate_complete_product_quality_blind_qa_reviews(
    reviews: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
) -> dict[str, Any]:
    normalized = [normalize_complete_product_quality_blind_qa_review(review) for review in list(reviews or [])]
    read_scores = [item.get("read_feeling_score") for item in normalized if item.get("read_feeling_score") is not None]
    overall_scores = [item.get("score") for item in normalized if item.get("score") is not None]
    dimension_scores: dict[str, float | None] = {}
    for dimension in _PRODUCT_QUALITY_DIMENSIONS:
        dimension_scores[dimension] = _avg((item.get("dimension_scores") or {}).get(dimension) for item in normalized)
    read_feeling_score = _avg(read_scores)
    review_count = len(normalized)
    red_review_count = sum(1 for item in normalized if _safe_int(item.get("red_count"), 0) > 0)
    pass_count = sum(1 for item in normalized if item.get("passed"))
    read_pass_count = sum(1 for score in read_scores if _safe_float(score, 0.0) >= COMPLETE_PRODUCT_QUALITY_READ_FEELING_INITIAL_TARGET)
    return {
        "version": COMPLETE_PRODUCT_QUALITY_BLIND_QA_AGGREGATE_VERSION,
        "target_step": COMPLETE_PRODUCT_QUALITY_SCORECARD_STEP,
        "blind_qa_ready": bool(normalized),
        "review_count": review_count,
        "pass_count": pass_count,
        "read_feeling_pass_count": read_pass_count,
        "red_review_count": red_review_count,
        "read_feeling_score": read_feeling_score,
        "overall_score": _avg(overall_scores),
        "dimension_scores": dimension_scores,
        "reviews": normalized,
        "read_feeling_connection_target": COMPLETE_PRODUCT_QUALITY_READ_FEELING_INITIAL_TARGET,
        "read_feeling_product_gate_target": COMPLETE_PRODUCT_QUALITY_READ_FEELING_PRODUCT_TARGET,
        "read_feeling_pass_rate": _rate(read_pass_count, review_count),
        "machine_metrics_separated": True,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
    }


def _normalize_records(
    *,
    scorecard_event: Mapping[str, Any] | None,
    scorecard_events: Sequence[Any] | Iterable[Any] | None,
    records: Sequence[Any] | Iterable[Any] | None,
    scorecard_harness: Mapping[str, Any] | None,
    fixture_qa_run: Mapping[str, Any] | None,
    diagnostic_summary: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    raw_records: list[Any] = []
    if scorecard_event:
        raw_records.append(scorecard_event)
    raw_records.extend(list(scorecard_events or []))
    raw_records.extend(list(records or []))
    for source in (scorecard_harness, fixture_qa_run, diagnostic_summary):
        data = _safe_mapping(source)
        if not data:
            continue
        for key in (
            "event",
            "normalized_event",
            "complete_scorecard_event",
            "scorecard_event",
            "complete_composer_scorecard_event",
            "complete_composer_initial_scorecard_event",
        ):
            nested = data.get(key)
            if isinstance(nested, Mapping):
                raw_records.append(dict(nested))
                break
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in raw_records:
        item = _normalize_product_quality_event(record)
        if not item:
            continue
        signature = repr(sorted((k, v) for k, v in item.items() if k != "reason_counter"))
        if signature in seen:
            continue
        seen.add(signature)
        normalized.append(item)
    return normalized


def _aggregate_machine_metrics(events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    totals = {
        "eligible_count": 0,
        "candidate_generated_count": 0,
        "passed_display_count": 0,
        "rejected_count": 0,
        "unavailable_count": 0,
        "safety_blocked_count": 0,
        "binding_supported_sentence_count": 0,
        "expected_binding_count": 0,
        "repair_attempt_count": 0,
        "repair_success_count": 0,
        "template_major_count": 0,
        "safety_major_count": 0,
        "reason_required_count": 0,
        "reason_covered_count": 0,
    }
    reason_counter: Counter[str] = Counter()
    group_rows: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "coverage_group": "",
        "event_count": 0,
        "eligible_count": 0,
        "passed_display_count": 0,
        "rejected_count": 0,
        "unavailable_count": 0,
        "safety_blocked_count": 0,
        "binding_supported_sentence_count": 0,
        "expected_binding_count": 0,
        "template_major_count": 0,
        "safety_major_count": 0,
        "reason_required_count": 0,
        "reason_covered_count": 0,
    })
    for event in events:
        group = _clean(event.get("coverage_group")) or "short_daily"
        row = group_rows[group]
        row["coverage_group"] = group
        row["event_count"] += 1
        for key in totals:
            value = _safe_int(event.get(key), 0)
            totals[key] += value
            row[key] = _safe_int(row.get(key), 0) + value
        for reason, count in _safe_mapping(event.get("reason_counter")).items():
            reason_counter[str(reason)] += _safe_int(count, 0)

    display_reach_rate = _rate(totals["passed_display_count"], totals["eligible_count"])
    binding_pass_rate = _rate(totals["binding_supported_sentence_count"], totals["expected_binding_count"])
    repair_success_rate = _rate(totals["repair_success_count"], totals["repair_attempt_count"])
    reason_coverage_rate = 1.0 if totals["reason_required_count"] <= 0 else _rate(totals["reason_covered_count"], totals["reason_required_count"])
    rows: list[dict[str, Any]] = []
    for group, row in sorted(group_rows.items()):
        row = dict(row)
        row["display_reach_rate"] = _rate(row.get("passed_display_count"), row.get("eligible_count"))
        row["binding_pass_rate"] = _rate(row.get("binding_supported_sentence_count"), row.get("expected_binding_count"))
        row["reason_coverage_rate"] = 1.0 if _safe_int(row.get("reason_required_count"), 0) <= 0 else _rate(row.get("reason_covered_count"), row.get("reason_required_count"))
        rows.append(row)

    top_rejection_reasons = [reason for reason, _ in reason_counter.most_common(8)]
    return {
        "version": COMPLETE_PRODUCT_QUALITY_MACHINE_METRICS_VERSION,
        "target_step": COMPLETE_PRODUCT_QUALITY_SCORECARD_STEP,
        "machine_metrics_ready": bool(events),
        "event_count": len(events),
        "record_count": len(events),
        **totals,
        "display_reach_rate": display_reach_rate,
        "binding_pass_rate": binding_pass_rate,
        "repair_success_rate": repair_success_rate,
        "reason_coverage_rate": reason_coverage_rate,
        "top_rejection_reasons": top_rejection_reasons,
        "coverage_group_rows": rows,
        "by_coverage_group": {str(row.get("coverage_group")): dict(row) for row in rows},
        "machine_metrics_separated_from_blind_qa": True,
        "machine_metrics_only": True,
        "read_feeling_score": None,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
    }



def build_complete_product_quality_scorecard_event_schema() -> dict[str, Any]:
    fields = {
        "run_id": "qa_run_identifier",
        "fixture_set_id": "fixture_set_identifier",
        "coverage_group": "structural_input_group",
        "eligible_count": "product_gate_eligible_item_count",
        "passed_display_count": "passed_comment_text_display_count",
        "rejected_count": "fail_closed_rejected_count",
        "unavailable_count": "fail_closed_unavailable_count",
        "binding_pass_rate": "sentence_binding_success_rate",
        "repair_success_rate": "safe_repair_success_rate",
        "read_feeling_score": "blind_qa_read_feeling_score",
        "safety_major_count": "major_safety_detection_count",
        "template_major_count": "major_template_detection_count",
        "top_rejection_reasons": "next_implementation_priority_reasons",
    }
    return {
        "version": "emlis.complete_product_quality_scorecard_event_schema.v1",
        "target_step": COMPLETE_PRODUCT_QUALITY_SCORECARD_STEP,
        "step": COMPLETE_PRODUCT_QUALITY_SCORECARD_STEP,
        "schema_kind": "product_quality_scorecard_event",
        "fields": fields,
        "field_order": list(fields.keys()),
        "required_fields": list(fields.keys()),
        "machine_metrics_separated_from_blind_qa": True,
        "machine_metrics_and_blind_qa_separated": True,
        "read_feeling_source": "blind_qa",
        "comment_text_contract": "passed_only",
        "raw_input_included": False,
        "comment_text_included": False,
        "response_shape_changed": False,
    }

def build_complete_product_quality_scorecard(
    *,
    scorecard_event: Mapping[str, Any] | None = None,
    scorecard_events: Sequence[Any] | Iterable[Any] | None = None,
    records: Sequence[Any] | Iterable[Any] | None = None,
    scorecard_harness: Mapping[str, Any] | None = None,
    fixture_qa_run: Mapping[str, Any] | None = None,
    diagnostic_summary: Mapping[str, Any] | None = None,
    blind_qa_reviews: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
) -> dict[str, Any]:
    events = _normalize_records(
        scorecard_event=scorecard_event,
        scorecard_events=scorecard_events,
        records=records,
        scorecard_harness=scorecard_harness,
        fixture_qa_run=fixture_qa_run,
        diagnostic_summary=diagnostic_summary,
    )
    machine = _aggregate_machine_metrics(events)
    blind_qa = aggregate_complete_product_quality_blind_qa_reviews(blind_qa_reviews or [])
    rubric = build_complete_product_quality_blind_qa_rubric()

    display_reach_rate = float(machine.get("display_reach_rate") or 0.0)
    binding_pass_rate = float(machine.get("binding_pass_rate") or 0.0)
    reason_coverage_rate = float(machine.get("reason_coverage_rate") or 0.0)
    read_feeling_score = blind_qa.get("read_feeling_score")
    template_major_count = _safe_int(machine.get("template_major_count"), 0)
    safety_major_count = _safe_int(machine.get("safety_major_count"), 0)

    threshold_checks = {
        "display_reach_rate_connection": display_reach_rate >= COMPLETE_PRODUCT_QUALITY_CONNECTION_DISPLAY_TARGET,
        "display_reach_rate_product_gate": display_reach_rate >= COMPLETE_PRODUCT_GATE_DISPLAY_TARGET,
        "binding_pass_rate": binding_pass_rate >= COMPLETE_PRODUCT_QUALITY_BINDING_TARGET,
        "read_feeling_score_connection": bool(read_feeling_score is not None and float(read_feeling_score) >= COMPLETE_PRODUCT_QUALITY_READ_FEELING_INITIAL_TARGET),
        "read_feeling_score_product_gate": bool(read_feeling_score is not None and float(read_feeling_score) >= COMPLETE_PRODUCT_QUALITY_READ_FEELING_PRODUCT_TARGET),
        "template_major_count_zero": template_major_count == 0,
        "safety_major_count_zero": safety_major_count == 0,
        "reason_coverage_rate": reason_coverage_rate >= COMPLETE_PRODUCT_QUALITY_REASON_COVERAGE_TARGET,
    }

    release_blockers: list[str] = []
    if not events:
        release_blockers.append("machine_metrics_missing")
    if not blind_qa.get("blind_qa_ready"):
        release_blockers.append("blind_qa_missing")
        release_blockers.append("blind_qa_not_evaluated")
    if not threshold_checks["reason_coverage_rate"]:
        release_blockers.append("reason_coverage_missing")
        release_blockers.append("reason_coverage_incomplete")
    if not threshold_checks["binding_pass_rate"] and events:
        release_blockers.append("binding_pass_rate_below_target")
        release_blockers.append("binding_target_not_met")
    if template_major_count > 0:
        release_blockers.append("template_major_detected")
    if safety_major_count > 0:
        release_blockers.append("safety_major_detected")
    if blind_qa.get("blind_qa_ready") and not threshold_checks["read_feeling_score_connection"]:
        release_blockers.append("read_feeling_score_below_connection_target")

    product_gate_thresholds_met = all(threshold_checks.values()) and bool(events) and bool(blind_qa.get("blind_qa_ready"))
    read_feeling_source = "blind_qa" if blind_qa.get("blind_qa_ready") else "not_evaluated"

    return _strip_forbidden_serialized_payload_key_names({
        "version": COMPLETE_PRODUCT_QUALITY_SCORECARD_VERSION,
        "target_step": COMPLETE_PRODUCT_QUALITY_SCORECARD_STEP,
        "step": COMPLETE_PRODUCT_QUALITY_SCORECARD_STEP,
        "implementation_unit": COMPLETE_PRODUCT_QUALITY_SCORECARD_IMPLEMENTATION_UNIT,
        "phase": "complete_composer_initial_product_quality_connection",
        "scorecard_type": "product_quality_scorecard_blind_qa",
        "product_quality_scorecard_ready": bool(events),
        "scorecard_ready": bool(events),
        "ready": bool(events),
        "scorecard_event_schema": build_complete_product_quality_scorecard_event_schema(),
        "machine_metrics_ready": bool(machine.get("machine_metrics_ready")),
        "blind_qa_required": True,
        "blind_qa_ready": bool(blind_qa.get("blind_qa_ready")),
        "read_feeling_requires_blind_qa": True,
        "machine_metrics_separated_from_blind_qa": True,
        "machine_metrics": machine,
        "blind_qa_metrics": blind_qa,
        "blind_qa_rubric": rubric,
        "eligible_count": _safe_int(machine.get("eligible_count"), 0),
        "passed_display_count": _safe_int(machine.get("passed_display_count"), 0),
        "rejected_count": _safe_int(machine.get("rejected_count"), 0),
        "unavailable_count": _safe_int(machine.get("unavailable_count"), 0),
        "display_reach_rate": display_reach_rate,
        "binding_pass_rate": binding_pass_rate,
        "repair_success_rate": float(machine.get("repair_success_rate") or 0.0),
        "read_feeling_score": read_feeling_score,
        "read_feeling_source": read_feeling_source,
        "safety_major_count": safety_major_count,
        "template_major_count": template_major_count,
        "reason_required_count": _safe_int(machine.get("reason_required_count"), 0),
        "reason_covered_count": _safe_int(machine.get("reason_covered_count"), 0),
        "reason_coverage_rate": reason_coverage_rate,
        "reason_required_count": int(machine.get("reason_required_count") or 0),
        "reason_covered_count": int(machine.get("reason_covered_count") or 0),
        "top_rejection_reasons": list(machine.get("top_rejection_reasons") or []),
        "coverage_group_rows": list(machine.get("coverage_group_rows") or []),
        "by_coverage_group": dict(machine.get("by_coverage_group") or {}),
        "threshold_checks": threshold_checks,
        "targets": {
            "version": COMPLETE_PRODUCT_QUALITY_TARGETS_VERSION,
            "connection_display_target": COMPLETE_PRODUCT_QUALITY_CONNECTION_DISPLAY_TARGET,
            "product_gate_display_target": COMPLETE_PRODUCT_GATE_DISPLAY_TARGET,
            "binding_pass_rate": COMPLETE_PRODUCT_QUALITY_BINDING_TARGET,
            "connection_read_feeling_target": COMPLETE_PRODUCT_QUALITY_READ_FEELING_INITIAL_TARGET,
            "product_gate_read_feeling_target": COMPLETE_PRODUCT_QUALITY_READ_FEELING_PRODUCT_TARGET,
            "reason_coverage_rate": COMPLETE_PRODUCT_QUALITY_REASON_COVERAGE_TARGET,
            "template_major_count": 0,
            "safety_major_count": 0,
        },
        "release_blockers": release_blockers,
        "product_gate_thresholds_met": product_gate_thresholds_met,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "product_gate_decision": "not_released_step6_scorecard_only",
        "product_gate_evaluation": "scorecard_material_only_not_release_decision",
        "release_ladder_stage": "not_started_step6_scorecard_only",
        "release_judgment": {
            "release_allowed": False,
            "reason": "scorecard_material_only_not_release_decision",
        },
        "ready_for_release_ladder_step7": bool(events and not release_blockers),
        "next_step": "Step7_Release_ladder_connection",
        "comment_text_contract": "passed_only",
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "comment_text_written_by_step6_product_quality": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "input_specific_template_added": False,
        "fixed_completed_sentence_template_added": False,
        "fixed_sentence_template_used": False,
        "fixed_fallback_used": False,
        "external_ai_used": False,
        "local_llm_used": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
    })


build_complete_product_quality_scorecard_report = build_complete_product_quality_scorecard
build_complete_product_quality_blind_qa_aggregate = aggregate_complete_product_quality_blind_qa_reviews


__all__ = [
    "COMPLETE_PRODUCT_QUALITY_SCORECARD_VERSION",
    "COMPLETE_PRODUCT_QUALITY_SCORECARD_STAGE",
    "COMPLETE_PRODUCT_QUALITY_SCORECARD_STEP",
    "COMPLETE_PRODUCT_QUALITY_BLIND_QA_RUBRIC_VERSION",
    "COMPLETE_PRODUCT_QUALITY_SCORECARD_EVENT_SCHEMA_VERSION",
    "COMPLETE_PRODUCT_QUALITY_BLIND_QA_REVIEW_VERSION",
    "COMPLETE_PRODUCT_QUALITY_BLIND_QA_AGGREGATE_VERSION",
    "build_complete_product_quality_scorecard_event_schema",
    "build_complete_product_quality_blind_qa_rubric",
    "normalize_complete_product_quality_blind_qa_review",
    "aggregate_complete_product_quality_blind_qa_reviews",
    "build_complete_product_quality_blind_qa_aggregate",
    "build_complete_product_quality_scorecard",
    "build_complete_product_quality_scorecard_report",
    "build_complete_product_quality_scorecard_event_schema",
]
