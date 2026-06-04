# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step6 Product Quality Scorecard / Blind QA for EmlisAI Complete Composer.

This module is intentionally meta-only.  It measures machine metrics and Blind
QA separately, then exposes a ProductQualityScorecard for the next release
ladder step.  It does not write ``comment_text``, relax gates, or change public
response/API/DB/RN contracts.
"""

from collections import Counter
from typing import Any, Iterable, Mapping, Sequence

from emlis_ai_complete_scorecard_service import (
    COMPLETE_COVERAGE_GROUP_ORDER,
    _normalize_coverage_group,
)
from emlis_ai_runtime_surface_coverage_baseline import (
    RUNTIME_SURFACE_COVERAGE_BASELINE_STEP,
    RUNTIME_SURFACE_COVERAGE_BASELINE_VERSION,
    build_runtime_surface_coverage_baseline,
)
from emlis_ai_runtime_surface_tone_engine_2_1 import (
    RUNTIME_SURFACE_TONE_ENGINE_2_1_VERSION,
    normalize_tone_engine_2_1_to_scorecard_event,
)
from emlis_ai_runtime_surface_self_repair import (
    RUNTIME_SURFACE_SELF_REPAIR_STEP,
    RUNTIME_SURFACE_SELF_REPAIR_VERSION,
    normalize_runtime_surface_self_repair_to_scorecard_event,
)
from emlis_ai_runtime_surface_blind_qa_long_run import (
    RUNTIME_SURFACE_BLIND_QA_LONG_RUN_STEP,
    RUNTIME_SURFACE_BLIND_QA_LONG_RUN_VERSION,
    build_runtime_surface_blind_qa_long_run_summary,
    normalize_runtime_surface_blind_qa_long_run_to_scorecard_fields,
)
from emlis_ai_observation_scorecard_blind_qa import (
    OBSERVATION_SCORECARD_BLIND_QA_STEP,
    OBSERVATION_SCORECARD_BLIND_QA_VERSION,
    build_observation_scorecard_blind_qa,
    extract_observation_reply_meta,
    normalize_observation_scorecard_blind_qa_to_scorecard_fields,
)
from emlis_ai_observation_regression_fixture_coverage import (
    OBSERVATION_REGRESSION_FIXTURE_COVERAGE_STEP,
    OBSERVATION_REGRESSION_FIXTURE_COVERAGE_VERSION,
    build_observation_regression_fixture_coverage,
    normalize_observation_regression_fixture_coverage_to_scorecard_fields,
)
from emlis_ai_observation_exit_gate_handoff import (
    OBSERVATION_EXIT_GATE_HANDOFF_STEP,
    OBSERVATION_EXIT_GATE_HANDOFF_VERSION,
    build_observation_exit_gate_handoff,
    normalize_observation_exit_gate_handoff_to_scorecard_fields,
)
from emlis_ai_product_readfeel_current_output_inventory import (
    PRODUCT_READFEEL_CURRENT_OUTPUT_INVENTORY_STEP,
    PRODUCT_READFEEL_CURRENT_OUTPUT_INVENTORY_VERSION,
    build_product_readfeel_current_output_inventory,
    normalize_product_readfeel_current_output_inventory_to_scorecard_fields,
)
from emlis_ai_product_readfeel_rubric import (
    PRODUCT_READFEEL_RUBRIC_STEP,
    PRODUCT_READFEEL_RUBRIC_VERSION,
    aggregate_product_readfeel_blind_qa_reviews,
    build_product_readfeel_rubric,
    normalize_product_readfeel_rubric_to_scorecard_fields,
)
from emlis_ai_product_readfeel_scorecard import (
    PRODUCT_READFEEL_SCORECARD_STEP,
    PRODUCT_READFEEL_SCORECARD_VERSION,
    build_product_readfeel_scorecard,
    normalize_product_readfeel_scorecard_to_scorecard_fields,
)
from emlis_ai_product_readfeel_long_run_product_gate import (
    PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_STEP,
    PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_VERSION,
    build_product_readfeel_long_run_product_gate,
    normalize_product_readfeel_long_run_product_gate_to_scorecard_fields,
)
from emlis_ai_mirror_only_surface_detector import (
    MIRROR_ONLY_SURFACE_DETECTOR_STEP,
    MIRROR_ONLY_SURFACE_DETECTOR_VERSION,
    build_mirror_only_surface_detector_summary,
    enrich_events_with_mirror_only_surface_detection,
    normalize_mirror_only_surface_detector_summary_to_scorecard_fields,
)

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
COMPLETE_PRODUCT_QUALITY_COVERAGE_GROUP_AGGREGATION_VERSION = "emlis.complete_product_quality_coverage_group_aggregation.v1"
COMPLETE_PRODUCT_QUALITY_SURFACE_METRICS_VERSION = "emlis.complete_product_quality_surface_metrics.v1"
COMPLETE_PRODUCT_QUALITY_SURFACE_METRICS_STEP = "Step3_Scorecard_Surface_Metrics_Connection"
COMPLETE_PRODUCT_QUALITY_COVERAGE_GROUP_MISSING = "coverage_group_missing"
COMPLETE_PRODUCT_QUALITY_COVERAGE_RUNTIME_BASELINE_VERSION = RUNTIME_SURFACE_COVERAGE_BASELINE_VERSION
COMPLETE_PRODUCT_QUALITY_COVERAGE_RUNTIME_BASELINE_STEP = RUNTIME_SURFACE_COVERAGE_BASELINE_STEP
COMPLETE_PRODUCT_QUALITY_RUNTIME_SURFACE_SELF_REPAIR_VERSION = RUNTIME_SURFACE_SELF_REPAIR_VERSION
COMPLETE_PRODUCT_QUALITY_RUNTIME_SURFACE_SELF_REPAIR_STEP = RUNTIME_SURFACE_SELF_REPAIR_STEP
COMPLETE_PRODUCT_QUALITY_RUNTIME_SURFACE_BLIND_QA_LONG_RUN_VERSION = RUNTIME_SURFACE_BLIND_QA_LONG_RUN_VERSION
COMPLETE_PRODUCT_QUALITY_RUNTIME_SURFACE_BLIND_QA_LONG_RUN_STEP = RUNTIME_SURFACE_BLIND_QA_LONG_RUN_STEP
COMPLETE_PRODUCT_QUALITY_PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_VERSION = PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_VERSION
COMPLETE_PRODUCT_QUALITY_PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_STEP = PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_STEP

COMPLETE_PRODUCT_QUALITY_CONNECTION_DISPLAY_TARGET = 0.80
COMPLETE_PRODUCT_GATE_DISPLAY_TARGET = 0.90
COMPLETE_PRODUCT_QUALITY_BINDING_TARGET = 0.98
COMPLETE_PRODUCT_QUALITY_READ_FEELING_INITIAL_TARGET = 0.85
COMPLETE_PRODUCT_QUALITY_READ_FEELING_PRODUCT_TARGET = 0.90
COMPLETE_PRODUCT_QUALITY_REASON_COVERAGE_TARGET = 1.0

_PRODUCT_QUALITY_META_ONLY_TEXT_PAYLOAD_KEYS = frozenset({
    "raw_input",
    "raw_text",
    "memo",
    "memo_body",
    "memo_action",
    "memo_action_body",
    "emotion_details",
    "emotion_details_body",
    "evidence_text",
    "comment_text",
    "comment_text_body",
    "surface_text",
    "display_body",
    "observation_text",
    "reception_text",
    "response_body",
    "text_body",
    "body",
})


def _strip_product_quality_text_payload_keys(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _strip_product_quality_text_payload_keys(item)
            for key, item in value.items()
            if str(key) not in _PRODUCT_QUALITY_META_ONLY_TEXT_PAYLOAD_KEYS
        }
    if isinstance(value, list):
        return [_strip_product_quality_text_payload_keys(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_strip_product_quality_text_payload_keys(item) for item in value)
    return value

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
    "connector_repetition",
    "predicate_family_repetition",
    "generic_center_phrase",
    "grammar_warning",
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


def _event_relation_types(event: Mapping[str, Any]) -> list[str]:
    relations: list[str] = []
    for key in (
        "relation_types",
        "expected_relation_types",
        "used_relation_ids",
        "used_relation_types",
        "relation_type",
    ):
        relations.extend(_dedupe(event.get(key)))
    return _dedupe(relations)


def _normalize_product_quality_coverage_group(event: Mapping[str, Any]) -> str:
    raw = _clean(event.get("coverage_group"))
    raw_lower = raw.lower()
    if raw_lower in {"", "unclassified", "unknown", "missing", "none", "null", COMPLETE_PRODUCT_QUALITY_COVERAGE_GROUP_MISSING}:
        return COMPLETE_PRODUCT_QUALITY_COVERAGE_GROUP_MISSING
    normalized = _normalize_coverage_group(raw, relation_types=_event_relation_types(event))
    return normalized or COMPLETE_PRODUCT_QUALITY_COVERAGE_GROUP_MISSING


def _empty_coverage_group_row(group: str) -> dict[str, Any]:
    return {
        "coverage_group": group,
        "event_count": 0,
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
        "reason_counter": Counter(),
        "top_rejection_reasons": [],
        "surface_signature_count": 0,
        "surface_signature_ready_count": 0,
        "surface_signature_unique_count": 0,
        "surface_signature_repeat_count": 0,
        "surface_template_major_count": 0,
        "surface_connector_repetition_event_count": 0,
        "surface_predicate_family_repetition_event_count": 0,
        "surface_ending_repetition_event_count": 0,
        "surface_generic_opening_event_count": 0,
        "surface_grammar_warning_event_count": 0,
        "surface_grammar_warning_count": 0,
        "surface_signature_family_counter": Counter(),
        "surface_major_reason_counter": Counter(),
        "surface_grammar_warning_counter": Counter(),
    }



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


def _first_text(*values: Any) -> str:
    for value in values:
        text = _clean(value)
        if text:
            return text
    return ""


def _first_int(event: Mapping[str, Any], nested: Mapping[str, Any], keys: Sequence[str], default: int = 0) -> int:
    for key in keys:
        if key in event:
            return _safe_int(event.get(key), default)
        if key in nested:
            return _safe_int(nested.get(key), default)
    return default


def _first_bool(event: Mapping[str, Any], nested: Mapping[str, Any], keys: Sequence[str]) -> bool:
    for key in keys:
        if key in event:
            return bool(event.get(key))
        if key in nested:
            return bool(nested.get(key))
    return False


def _surface_quality_signature_payload(event: Mapping[str, Any]) -> dict[str, Any]:
    nested = _safe_mapping(event.get("surface_quality_signature")) or _safe_mapping(event.get("step2_surface_quality_signature"))
    return nested


def _surface_metric_event_fields(event: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize Step2 signature keys into Step3 scorecard metrics fields.

    The event may contain a full SurfaceQualitySignatureV1 payload or only its
    meta-only projection.  This helper never reads or returns observation text.
    """

    nested = _surface_quality_signature_payload(event)
    surface_signature_id = _first_text(event.get("surface_signature_id"), nested.get("surface_signature_id"))
    surface_signature_family_key = _first_text(
        event.get("surface_signature_family_key"),
        event.get("signature_family_key"),
        nested.get("surface_signature_family_key"),
        nested.get("signature_family_key"),
        surface_signature_id,
    )
    surface_ready = bool(
        event.get("surface_quality_signature_ready")
        or event.get("step2_surface_quality_signature_ready")
        or event.get("step2_surface_signature_measurement_ready")
        or nested.get("surface_quality_signature_ready")
        or surface_signature_id
    )

    generic_center_count = _first_int(
        event,
        nested,
        ("surface_generic_center_phrase_count", "generic_center_phrase_count"),
    )
    same_connector_run_max = _first_int(
        event,
        nested,
        ("surface_same_connector_run_max", "same_connector_run_max"),
    )
    same_connector_family_count = _first_int(
        event,
        nested,
        ("surface_same_connector_family_count", "same_connector_family_count"),
    )
    same_connector_repetition_count = _first_int(
        event,
        nested,
        ("surface_same_connector_repetition_count", "same_connector_repetition_count"),
    )
    same_connector_repetition_count = max(
        same_connector_repetition_count,
        max(0, same_connector_run_max - 1),
        max(0, same_connector_family_count - 1),
    )
    same_predicate_family_count = _first_int(
        event,
        nested,
        ("surface_same_predicate_family_count", "same_predicate_family_count"),
    )
    observation_predicate_family_count = _first_int(
        event,
        nested,
        ("surface_observation_predicate_family_count", "observation_predicate_family_count"),
    )
    same_ending_family_count = _first_int(
        event,
        nested,
        ("surface_same_ending_family_count", "same_ending_family_count"),
    )
    grammar_warning_codes = _dedupe(
        [
            *(_dedupe(event.get("surface_grammar_warning_codes"))),
            *(_dedupe(event.get("grammar_warning_codes"))),
            *(_dedupe(nested.get("surface_grammar_warning_codes"))),
            *(_dedupe(nested.get("grammar_warning_codes"))),
        ]
    )
    grammar_warning_count = max(
        _first_int(event, nested, ("surface_grammar_warning_count", "grammar_warning_count")),
        len(grammar_warning_codes),
    )
    malformed_nominalization_risk = _first_bool(
        event,
        nested,
        ("surface_malformed_nominalization_risk", "malformed_nominalization_risk"),
    )
    raw_echo_risk = _first_bool(event, nested, ("surface_raw_echo_risk", "raw_echo_risk"))
    opening_family_key = _first_text(event.get("surface_opening_family_key"), nested.get("opening_family_key"), "none")
    surface_major_reasons = _dedupe(
        [
            *(_dedupe(event.get("surface_major_reasons"))),
            *(_dedupe(event.get("template_major_reasons"))),
            *(_dedupe(nested.get("surface_major_reasons"))),
            *(_dedupe(nested.get("template_major_reasons"))),
        ]
    )

    connector_repetition_event = bool(same_connector_repetition_count > 0 or same_connector_run_max >= 2)
    predicate_repetition_event = bool(same_predicate_family_count >= 2 or observation_predicate_family_count >= 3)
    ending_repetition_event = bool(same_ending_family_count >= 3)
    generic_opening_event = bool(generic_center_count > 0 or opening_family_key == "center_phrase")
    grammar_warning_event = bool(grammar_warning_count > 0 or malformed_nominalization_risk)
    surface_template_major = bool(
        _first_bool(event, nested, ("surface_template_major", "template_major"))
        or _safe_int(event.get("surface_template_major_count"), 0) > 0
        or _safe_int(event.get("template_major_count"), 0) > 0
    )

    if connector_repetition_event and "connector_repetition" not in surface_major_reasons:
        surface_major_reasons.append("connector_repetition")
    if predicate_repetition_event and "predicate_family_repetition" not in surface_major_reasons:
        surface_major_reasons.append("predicate_family_repetition")
    if ending_repetition_event and "same_ending_family" not in surface_major_reasons:
        surface_major_reasons.append("same_ending_family")
    if generic_opening_event and "generic_center_phrase" not in surface_major_reasons:
        surface_major_reasons.append("generic_center_phrase")
    if grammar_warning_event and "grammar_warning" not in surface_major_reasons:
        surface_major_reasons.append("grammar_warning")
    if raw_echo_risk and "raw_echo_risk" not in surface_major_reasons:
        surface_major_reasons.append("raw_echo_risk")

    return {
        "surface_metrics_event_ready": surface_ready,
        "surface_quality_signature_ready": surface_ready,
        "step2_surface_quality_signature_ready": surface_ready,
        "step3_scorecard_surface_metrics_event_ready": surface_ready,
        "surface_signature_id": surface_signature_id,
        "surface_signature_family_key": surface_signature_family_key,
        "surface_signature_count": 1 if surface_ready and surface_signature_family_key else 0,
        "surface_signature_ready_count": 1 if surface_ready else 0,
        "surface_major_reasons": surface_major_reasons,
        "surface_grammar_warning_codes": grammar_warning_codes,
        "grammar_warning_codes": grammar_warning_codes,
        "surface_grammar_warning_count": grammar_warning_count,
        "grammar_warning_count": grammar_warning_count,
        "surface_template_major": surface_template_major,
        "surface_template_major_count": 1 if surface_template_major else 0,
        "surface_generic_center_phrase_count": generic_center_count,
        "surface_same_connector_run_max": same_connector_run_max,
        "surface_same_connector_family_count": same_connector_family_count,
        "surface_same_connector_repetition_count": same_connector_repetition_count,
        "surface_same_predicate_family_count": same_predicate_family_count,
        "surface_observation_predicate_family_count": observation_predicate_family_count,
        "surface_same_ending_family_count": same_ending_family_count,
        "surface_malformed_nominalization_risk": malformed_nominalization_risk,
        "surface_raw_echo_risk": raw_echo_risk,
        "surface_connector_repetition_event_count": 1 if connector_repetition_event else 0,
        "surface_predicate_family_repetition_event_count": 1 if predicate_repetition_event else 0,
        "surface_ending_repetition_event_count": 1 if ending_repetition_event else 0,
        "surface_generic_opening_event_count": 1 if generic_opening_event else 0,
        "surface_grammar_warning_event_count": 1 if grammar_warning_event else 0,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
    }


def _normalize_product_quality_event(record: Any) -> dict[str, Any]:
    event = _source_event(record)
    if not event:
        return {}

    coverage_group = _normalize_product_quality_coverage_group(event)
    observation_status = _clean(event.get("observation_status")).lower()
    eligible_count = _safe_int(event.get("eligible_count"), 0)
    if eligible_count <= 0 and (observation_status or event.get("complete_candidate_seen") or event.get("complete_candidate_generated")):
        eligible_count = 1

    # Step3 ProductGate measurement events may keep backend observation_status=passed
    # while display_confirmed=false.  Respect explicit display counting fields
    # so backend-only passes are not over-counted as confirmed RN display.
    if "scorecard_passed_display_count" in event:
        passed_display_count = _safe_int(event.get("scorecard_passed_display_count"), 0)
    elif "passed_display_count" in event:
        passed_display_count = _safe_int(event.get("passed_display_count"), 0)
    elif event.get("display_confirmed") is True:
        passed_display_count = 1 if eligible_count else 0
    elif observation_status == "passed":
        passed_display_count = 1 if eligible_count else 0
    else:
        passed_display_count = 0

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

    surface_metric_fields = _surface_metric_event_fields(event)
    tone_report = _safe_mapping(event.get("tone_engine_2_1_report")) or _safe_mapping(event.get("step9_tone_engine_2_1_report"))
    if not tone_report:
        legacy_tone_report = _safe_mapping(event.get("tone_guard_report"))
        nested = legacy_tone_report.get("tone_engine_2_1_report") or legacy_tone_report.get("step9_tone_engine_2_1_report")
        tone_report = _safe_mapping(nested) or legacy_tone_report
    tone_engine_2_1_fields = normalize_tone_engine_2_1_to_scorecard_event(tone_report or event)
    runtime_surface_self_repair_report = (
        _safe_mapping(event.get("runtime_surface_self_repair"))
        or _safe_mapping(event.get("step10_surface_aware_self_repair"))
        or _safe_mapping(event.get("surface_aware_self_repair_report"))
    )
    runtime_surface_self_repair_fields = normalize_runtime_surface_self_repair_to_scorecard_event(runtime_surface_self_repair_report or event)
    template_major_count = _safe_int(event.get("template_major_count"), 0)
    template_major_count += _safe_int(event.get("surface_variation_major_count"), 0)
    template_major_count = max(template_major_count, _safe_int(surface_metric_fields.get("surface_template_major_count"), 0))
    safety_major_count = _safe_int(event.get("safety_major_count"), 0)
    safety_major_count += _safe_int(event.get("tone_diagnostic_count"), 0)
    safety_major_count += _safe_int(event.get("tone_advice_count"), 0)
    safety_major_count += _safe_int(tone_engine_2_1_fields.get("tone_safety_major_count"), 0)

    if template_major_count <= 0:
        template_major_count = _count_marker_hits(reasons, _TEMPLATE_REASON_MARKERS)
    if safety_major_count <= 0:
        safety_major_count = _count_marker_hits(reasons, _SAFETY_REASON_MARKERS)

    repair_attempt_count = max(
        _safe_int(event.get("repair_attempt_count"), 0),
        _safe_int(runtime_surface_self_repair_fields.get("repair_attempt_count"), 0),
    )
    if repair_attempt_count <= 0 and (event.get("repair_attempted") or runtime_surface_self_repair_fields.get("surface_aware_self_repair_attempted")):
        repair_attempt_count = 1
    repair_success_count = max(
        _safe_int(event.get("repair_success_count"), 0),
        _safe_int(runtime_surface_self_repair_fields.get("repair_success_count"), 0),
    )
    if repair_success_count <= 0 and (event.get("repair_success") or runtime_surface_self_repair_fields.get("surface_aware_self_repair_success")):
        repair_success_count = 1

    candidate_generated_count = _safe_int(event.get("candidate_generated_count"), 0)
    if candidate_generated_count <= 0 and event.get("complete_candidate_generated"):
        candidate_generated_count = 1

    observation_reply_meta = extract_observation_reply_meta(event)
    observation_reply_kind = _clean(
        observation_reply_meta.get("observation_reply_kind") or event.get("observation_reply_kind")
    )
    eligibility_status = _clean(
        observation_reply_meta.get("eligibility_status") or event.get("eligibility_status") or event.get("status")
    )
    unknown_slots = list(observation_reply_meta.get("unknown_slots") or event.get("unknown_slots") or [])
    sentence_plan_observation_roles = list(
        observation_reply_meta.get("sentence_plan_observation_roles")
        or event.get("sentence_plan_observation_roles")
        or event.get("observation_roles")
        or []
    )
    facts_used = list(observation_reply_meta.get("facts_used") or event.get("facts_used") or [])

    return {
        "row_id": _first_text(event.get("row_id"), event.get("candidate_id"), event.get("trace_id"), event.get("emotion_log_id")),
        "trace_id": _clean(event.get("trace_id")),
        "emotion_log_id": _clean(event.get("emotion_log_id")),
        "run_id": _clean(event.get("run_id")),
        "coverage_group": coverage_group,
        "observation_status": observation_status,
        "observation_scorecard_blind_qa_version": OBSERVATION_SCORECARD_BLIND_QA_VERSION,
        "observation_scorecard_blind_qa_step": OBSERVATION_SCORECARD_BLIND_QA_STEP,
        "observation_reply_meta": observation_reply_meta,
        "observation_reply_kind": observation_reply_kind,
        "eligibility_status": eligibility_status,
        "expected_observation_reply_kind": _clean(event.get("expected_observation_reply_kind") or event.get("expected_reply_kind")),
        "expected_eligibility_status": _clean(event.get("expected_eligibility_status") or event.get("expected_status")),
        "eligible_for_full_observation": bool(observation_reply_meta.get("eligible_for_full_observation") is True or event.get("eligible_for_full_observation") is True),
        "question_required": bool(observation_reply_meta.get("question_required") is True or event.get("question_required") is True),
        "unknown_slots": unknown_slots,
        "sentence_plan_observation_roles": sentence_plan_observation_roles,
        "user_fact_grounding_mode": _clean(observation_reply_meta.get("user_fact_grounding_mode") or event.get("user_fact_grounding_mode")),
        "user_fact_allowed": bool(observation_reply_meta.get("user_fact_allowed") is True or event.get("user_fact_allowed") is True),
        "user_fact_may_hint": bool(observation_reply_meta.get("user_fact_may_hint") is True or event.get("user_fact_may_hint") is True),
        "user_fact_may_promote_to_eligible": bool(event.get("user_fact_may_promote_to_eligible") is True),
        "facts_used": facts_used,
        "plan": _clean(observation_reply_meta.get("plan") or event.get("plan") or event.get("subscription_tier")),
        "free_user_fact_violation": bool(event.get("free_user_fact_violation") is True),
        "overclaim_count": _safe_int(event.get("overclaim_count"), 0),
        "template_skeleton_repeat_count": _safe_int(event.get("template_skeleton_repeat_count"), 0),
        "surface_signature_family_key": _clean(event.get("surface_signature_family_key") or event.get("template_skeleton_key") or event.get("surface_skeleton_id")),
        "template_skeleton_key": _clean(event.get("template_skeleton_key") or event.get("surface_signature_family_key") or event.get("surface_skeleton_id")),
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
        **surface_metric_fields,
        **tone_engine_2_1_fields,
        "tone_engine_2_1_report": tone_report,
        "step9_tone_engine_2_1_ready": bool(tone_engine_2_1_fields.get("step9_tone_engine_2_1_ready")),
        **runtime_surface_self_repair_fields,
        "runtime_surface_self_repair": runtime_surface_self_repair_report,
        "repair_attempt_count": repair_attempt_count,
        "repair_success_count": repair_success_count,
        "tone_completion_requires_blind_qa": True,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
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
        "candidate_id": _clean(data.get("candidate_id")) or _clean(data.get("row_id")) or _clean(data.get("trace_id")) or _clean(data.get("emotion_log_id")),
        "row_id": _clean(data.get("row_id")),
        "trace_id": _clean(data.get("trace_id")),
        "emotion_log_id": _clean(data.get("emotion_log_id")),
        "public_passed": data.get("public_passed") if "public_passed" in data else None,
        "dimension_scores": dimension_scores,
        "dimension_verdicts": dimension_verdicts,
        "score": score,
        "read_feeling_score": read_score,
        "read_feeling_source": "blind_qa_review_rating",
        "ratings_only_payload": True,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "green_count": green_count,
        "yellow_count": yellow_count,
        "red_count": red_count,
        "read_feeling_pass": bool(read_score is not None and read_score >= COMPLETE_PRODUCT_QUALITY_READ_FEELING_INITIAL_TARGET),
        "passed": bool(score is not None and read_score is not None and read_score >= COMPLETE_PRODUCT_QUALITY_READ_FEELING_INITIAL_TARGET and red_count == 0),
        "machine_metrics_separated": True,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
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
        "read_feeling_source": "blind_qa_review_ratings" if normalized else "not_evaluated",
        "overall_score": _avg(overall_scores),
        "dimension_scores": dimension_scores,
        "reviews": normalized,
        "read_feeling_connection_target": COMPLETE_PRODUCT_QUALITY_READ_FEELING_INITIAL_TARGET,
        "read_feeling_product_gate_target": COMPLETE_PRODUCT_QUALITY_READ_FEELING_PRODUCT_TARGET,
        "read_feeling_pass_rate": _rate(read_pass_count, review_count),
        "machine_metrics_separated": True,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
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
        item = _normalize_product_quality_event(_strip_product_quality_text_payload_keys(record))
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
        "surface_signature_count": 0,
        "surface_signature_ready_count": 0,
        "surface_template_major_count": 0,
        "surface_connector_repetition_event_count": 0,
        "surface_predicate_family_repetition_event_count": 0,
        "surface_ending_repetition_event_count": 0,
        "surface_generic_opening_event_count": 0,
        "surface_grammar_warning_event_count": 0,
        "surface_grammar_warning_count": 0,
        "tone_guard_major_count": 0,
        "tone_engine_2_1_major_count": 0,
        "tone_safety_major_count": 0,
        "tone_distance_major_count": 0,
        "tone_naturalness_major_count": 0,
        "tone_read_feeling_machine_warning_count": 0,
        "runtime_surface_self_repair_attempt_count": 0,
        "runtime_surface_self_repair_success_count": 0,
        "runtime_surface_self_repair_aborted_count": 0,
        "runtime_surface_self_repair_policy_violation_count": 0,
        "runtime_surface_self_repair_meaning_added_count": 0,
    }
    reason_counter: Counter[str] = Counter()
    surface_signature_family_counter: Counter[str] = Counter()
    surface_major_reason_counter: Counter[str] = Counter()
    surface_grammar_warning_counter: Counter[str] = Counter()
    group_rows: dict[str, dict[str, Any]] = {
        group: _empty_coverage_group_row(group) for group in COMPLETE_COVERAGE_GROUP_ORDER
    }
    for event in events:
        group = _normalize_product_quality_coverage_group(event)
        if group not in group_rows:
            group_rows[group] = _empty_coverage_group_row(group)
        row = group_rows[group]
        row["event_count"] += 1
        for key in totals:
            value = _safe_int(event.get(key), 0)
            totals[key] += value
            row[key] = _safe_int(row.get(key), 0) + value
        row_reason_counter = row.get("reason_counter")
        if not isinstance(row_reason_counter, Counter):
            row_reason_counter = Counter(_safe_mapping(row_reason_counter))
            row["reason_counter"] = row_reason_counter
        for reason, count in _safe_mapping(event.get("reason_counter")).items():
            normalized_reason = str(reason)
            normalized_count = _safe_int(count, 0)
            reason_counter[normalized_reason] += normalized_count
            row_reason_counter[normalized_reason] += normalized_count

        surface_family_key = _clean(event.get("surface_signature_family_key") or event.get("surface_signature_id"))
        if surface_family_key and _safe_int(event.get("surface_signature_count"), 0) > 0:
            surface_signature_family_counter[surface_family_key] += 1
            row_family_counter = row.get("surface_signature_family_counter")
            if not isinstance(row_family_counter, Counter):
                row_family_counter = Counter(_safe_mapping(row_family_counter))
                row["surface_signature_family_counter"] = row_family_counter
            row_family_counter[surface_family_key] += 1

        row_surface_reason_counter = row.get("surface_major_reason_counter")
        if not isinstance(row_surface_reason_counter, Counter):
            row_surface_reason_counter = Counter(_safe_mapping(row_surface_reason_counter))
            row["surface_major_reason_counter"] = row_surface_reason_counter
        for reason in _dedupe(event.get("surface_major_reasons")):
            surface_major_reason_counter[reason] += 1
            row_surface_reason_counter[reason] += 1

        row_grammar_counter = row.get("surface_grammar_warning_counter")
        if not isinstance(row_grammar_counter, Counter):
            row_grammar_counter = Counter(_safe_mapping(row_grammar_counter))
            row["surface_grammar_warning_counter"] = row_grammar_counter
        for code in _dedupe(event.get("surface_grammar_warning_codes") or event.get("grammar_warning_codes")):
            surface_grammar_warning_counter[code] += 1
            row_grammar_counter[code] += 1

    display_reach_rate = _rate(totals["passed_display_count"], totals["eligible_count"])
    binding_pass_rate = _rate(totals["binding_supported_sentence_count"], totals["expected_binding_count"])
    repair_success_rate = _rate(totals["repair_success_count"], totals["repair_attempt_count"])
    reason_coverage_rate = 1.0 if totals["reason_required_count"] <= 0 else _rate(totals["reason_covered_count"], totals["reason_required_count"])

    surface_signature_unique_count = len(surface_signature_family_counter)
    surface_signature_repeat_count = sum(max(0, count - 1) for count in surface_signature_family_counter.values())
    surface_signature_repeat_rate = _rate(surface_signature_repeat_count, totals["surface_signature_count"])
    coverage_surface_diversity_rate = _rate(surface_signature_unique_count, totals["surface_signature_count"])
    connector_repetition_rate = _rate(totals["surface_connector_repetition_event_count"], totals["surface_signature_count"])
    predicate_family_repetition_rate = _rate(totals["surface_predicate_family_repetition_event_count"], totals["surface_signature_count"])
    ending_repetition_rate = _rate(totals["surface_ending_repetition_event_count"], totals["surface_signature_count"])
    generic_opening_rate = _rate(totals["surface_generic_opening_event_count"], totals["surface_signature_count"])
    grammar_warning_rate = _rate(totals["surface_grammar_warning_event_count"], totals["surface_signature_count"])

    def sort_key(group: str) -> tuple[int, str]:
        if group in COMPLETE_COVERAGE_GROUP_ORDER:
            return (COMPLETE_COVERAGE_GROUP_ORDER.index(group), group)
        if group == COMPLETE_PRODUCT_QUALITY_COVERAGE_GROUP_MISSING:
            return (len(COMPLETE_COVERAGE_GROUP_ORDER), group)
        return (len(COMPLETE_COVERAGE_GROUP_ORDER) + 1, group)

    rows: list[dict[str, Any]] = []
    for group in sorted(group_rows, key=sort_key):
        row = dict(group_rows[group])
        row_counter = row.get("reason_counter")
        if not isinstance(row_counter, Counter):
            row_counter = Counter(_safe_mapping(row_counter))
        row["display_reach_rate"] = _rate(row.get("passed_display_count"), row.get("eligible_count"))
        row["binding_pass_rate"] = _rate(row.get("binding_supported_sentence_count"), row.get("expected_binding_count"))
        row["repair_success_rate"] = _rate(row.get("repair_success_count"), row.get("repair_attempt_count"))
        row["reason_coverage_rate"] = 1.0 if _safe_int(row.get("reason_required_count"), 0) <= 0 else _rate(row.get("reason_covered_count"), row.get("reason_required_count"))
        row_family_counter = row.get("surface_signature_family_counter")
        if not isinstance(row_family_counter, Counter):
            row_family_counter = Counter(_safe_mapping(row_family_counter))
        row_surface_reason_counter = row.get("surface_major_reason_counter")
        if not isinstance(row_surface_reason_counter, Counter):
            row_surface_reason_counter = Counter(_safe_mapping(row_surface_reason_counter))
        row_grammar_counter = row.get("surface_grammar_warning_counter")
        if not isinstance(row_grammar_counter, Counter):
            row_grammar_counter = Counter(_safe_mapping(row_grammar_counter))
        row_surface_signature_count = _safe_int(row.get("surface_signature_count"), 0)
        row["surface_signature_unique_count"] = len(row_family_counter)
        row["surface_signature_repeat_count"] = sum(max(0, count - 1) for count in row_family_counter.values())
        row["surface_signature_repeat_rate"] = _rate(row.get("surface_signature_repeat_count"), row_surface_signature_count)
        row["coverage_surface_diversity_rate"] = _rate(row.get("surface_signature_unique_count"), row_surface_signature_count)
        row["connector_repetition_rate"] = _rate(row.get("surface_connector_repetition_event_count"), row_surface_signature_count)
        row["predicate_family_repetition_rate"] = _rate(row.get("surface_predicate_family_repetition_event_count"), row_surface_signature_count)
        row["ending_repetition_rate"] = _rate(row.get("surface_ending_repetition_event_count"), row_surface_signature_count)
        row["generic_opening_rate"] = _rate(row.get("surface_generic_opening_event_count"), row_surface_signature_count)
        row["grammar_warning_rate"] = _rate(row.get("surface_grammar_warning_event_count"), row_surface_signature_count)
        row["surface_signature_family_counter"] = dict(row_family_counter)
        row["surface_major_reason_counter"] = dict(row_surface_reason_counter)
        row["surface_major_reasons"] = [reason for reason, _ in row_surface_reason_counter.most_common(8)]
        row["surface_grammar_warning_counter"] = dict(row_grammar_counter)
        row["surface_grammar_warning_codes"] = [code for code, _ in row_grammar_counter.most_common(8)]
        row["surface_metrics_ready"] = row_surface_signature_count > 0
        row["reason_counter"] = dict(row_counter)
        row["top_rejection_reasons"] = [reason for reason, _ in row_counter.most_common(8)]
        rows.append(row)

    by_coverage_group = {str(row.get("coverage_group")): dict(row) for row in rows}
    observed_coverage_groups = [
        group for group in COMPLETE_COVERAGE_GROUP_ORDER
        if _safe_int(by_coverage_group.get(group, {}).get("event_count"), 0) > 0
        or _safe_int(by_coverage_group.get(group, {}).get("eligible_count"), 0) > 0
    ]
    missing_coverage_groups = [group for group in COMPLETE_COVERAGE_GROUP_ORDER if group not in observed_coverage_groups]
    coverage_group_missing_count = _safe_int(by_coverage_group.get(COMPLETE_PRODUCT_QUALITY_COVERAGE_GROUP_MISSING, {}).get("event_count"), 0)
    top_rejection_reasons = [reason for reason, _ in reason_counter.most_common(8)]
    coverage_runtime_baseline = build_runtime_surface_coverage_baseline(events=events)
    return {
        "version": COMPLETE_PRODUCT_QUALITY_MACHINE_METRICS_VERSION,
        "coverage_group_aggregation_version": COMPLETE_PRODUCT_QUALITY_COVERAGE_GROUP_AGGREGATION_VERSION,
        "coverage_runtime_baseline_version": RUNTIME_SURFACE_COVERAGE_BASELINE_VERSION,
        "coverage_runtime_baseline_step": RUNTIME_SURFACE_COVERAGE_BASELINE_STEP,
        "target_step": COMPLETE_PRODUCT_QUALITY_SCORECARD_STEP,
        "machine_metrics_ready": bool(events),
        "coverage_group_aggregation_ready": True,
        "coverage_runtime_baseline_ready": bool(coverage_runtime_baseline.get("coverage_runtime_baseline_ready")),
        "step4_coverage_runtime_baseline_ready": bool(coverage_runtime_baseline.get("step4_coverage_runtime_baseline_ready")),
        "event_count": len(events),
        "record_count": len(events),
        **totals,
        "display_reach_rate": display_reach_rate,
        "binding_pass_rate": binding_pass_rate,
        "repair_success_rate": repair_success_rate,
        "reason_coverage_rate": reason_coverage_rate,
        "surface_metrics_version": COMPLETE_PRODUCT_QUALITY_SURFACE_METRICS_VERSION,
        "surface_metrics_step": COMPLETE_PRODUCT_QUALITY_SURFACE_METRICS_STEP,
        "surface_metrics_ready": totals["surface_signature_count"] > 0,
        "step3_scorecard_surface_metrics_connected": True,
        "surface_signature_count": totals["surface_signature_count"],
        "surface_signature_ready_count": totals["surface_signature_ready_count"],
        "surface_signature_unique_count": surface_signature_unique_count,
        "surface_signature_repeat_count": surface_signature_repeat_count,
        "surface_signature_repeat_rate": surface_signature_repeat_rate,
        "coverage_surface_diversity_rate": coverage_surface_diversity_rate,
        "connector_repetition_rate": connector_repetition_rate,
        "predicate_family_repetition_rate": predicate_family_repetition_rate,
        "ending_repetition_rate": ending_repetition_rate,
        "generic_opening_rate": generic_opening_rate,
        "grammar_warning_rate": grammar_warning_rate,
        "surface_template_major_count": totals["surface_template_major_count"],
        "surface_connector_repetition_event_count": totals["surface_connector_repetition_event_count"],
        "surface_predicate_family_repetition_event_count": totals["surface_predicate_family_repetition_event_count"],
        "surface_ending_repetition_event_count": totals["surface_ending_repetition_event_count"],
        "surface_generic_opening_event_count": totals["surface_generic_opening_event_count"],
        "surface_grammar_warning_event_count": totals["surface_grammar_warning_event_count"],
        "surface_grammar_warning_count": totals["surface_grammar_warning_count"],
        "surface_signature_family_counter": dict(surface_signature_family_counter),
        "surface_major_reason_counter": dict(surface_major_reason_counter),
        "surface_major_reasons": [reason for reason, _ in surface_major_reason_counter.most_common(8)],
        "surface_grammar_warning_counter": dict(surface_grammar_warning_counter),
        "surface_grammar_warning_codes": [code for code, _ in surface_grammar_warning_counter.most_common(8)],
        "tone_engine_2_1_version": RUNTIME_SURFACE_TONE_ENGINE_2_1_VERSION,
        "tone_engine_2_1_ready": totals["tone_engine_2_1_major_count"] >= 0,
        "step9_tone_engine_2_1_connected": True,
        "tone_guard_major_count": totals["tone_guard_major_count"],
        "tone_engine_2_1_major_count": totals["tone_engine_2_1_major_count"],
        "tone_safety_major_count": totals["tone_safety_major_count"],
        "tone_distance_major_count": totals["tone_distance_major_count"],
        "tone_naturalness_major_count": totals["tone_naturalness_major_count"],
        "tone_read_feeling_machine_warning_count": totals["tone_read_feeling_machine_warning_count"],
        "tone_completion_requires_blind_qa": True,
        "runtime_surface_self_repair_version": RUNTIME_SURFACE_SELF_REPAIR_VERSION,
        "runtime_surface_self_repair_step": RUNTIME_SURFACE_SELF_REPAIR_STEP,
        "runtime_surface_self_repair_ready": totals["runtime_surface_self_repair_attempt_count"] > 0,
        "step10_surface_aware_self_repair_connected": True,
        "step10_surface_aware_self_repair_ready": totals["runtime_surface_self_repair_attempt_count"] > 0,
        "runtime_surface_self_repair_attempt_count": totals["runtime_surface_self_repair_attempt_count"],
        "runtime_surface_self_repair_success_count": totals["runtime_surface_self_repair_success_count"],
        "runtime_surface_self_repair_aborted_count": totals["runtime_surface_self_repair_aborted_count"],
        "runtime_surface_self_repair_policy_violation_count": totals["runtime_surface_self_repair_policy_violation_count"],
        "runtime_surface_self_repair_meaning_added_count": totals["runtime_surface_self_repair_meaning_added_count"],
        "runtime_surface_self_repair_success_rate": _rate(totals["runtime_surface_self_repair_success_count"], totals["runtime_surface_self_repair_attempt_count"]),
        "read_feeling_requires_blind_qa": True,
        "surface_metrics": {
            "version": COMPLETE_PRODUCT_QUALITY_SURFACE_METRICS_VERSION,
            "source_step": COMPLETE_PRODUCT_QUALITY_SURFACE_METRICS_STEP,
            "surface_metrics_ready": totals["surface_signature_count"] > 0,
            "surface_signature_count": totals["surface_signature_count"],
            "surface_signature_unique_count": surface_signature_unique_count,
            "surface_signature_repeat_count": surface_signature_repeat_count,
            "surface_signature_repeat_rate": surface_signature_repeat_rate,
            "coverage_surface_diversity_rate": coverage_surface_diversity_rate,
            "connector_repetition_rate": connector_repetition_rate,
            "predicate_family_repetition_rate": predicate_family_repetition_rate,
            "ending_repetition_rate": ending_repetition_rate,
            "generic_opening_rate": generic_opening_rate,
            "grammar_warning_rate": grammar_warning_rate,
            "surface_template_major_count": totals["surface_template_major_count"],
            "surface_major_reasons": [reason for reason, _ in surface_major_reason_counter.most_common(8)],
            "grammar_warning_codes": [code for code, _ in surface_grammar_warning_counter.most_common(8)],
            "coverage_runtime_baseline_ready": bool(coverage_runtime_baseline.get("coverage_runtime_baseline_ready")),
            "read_feeling_auto_filled_from_surface_metrics": False,
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        "top_rejection_reasons": top_rejection_reasons,
        "coverage_group_rows": rows,
        "by_coverage_group": by_coverage_group,
        "required_coverage_groups": list(COMPLETE_COVERAGE_GROUP_ORDER),
        "observed_coverage_groups": observed_coverage_groups,
        "missing_coverage_groups": missing_coverage_groups,
        "coverage_group_count": len(observed_coverage_groups),
        "coverage_group_missing_count": coverage_group_missing_count,
        "coverage_group_missing_blocker": coverage_group_missing_count > 0,
        "coverage_runtime_baseline": coverage_runtime_baseline,
        "coverage_runtime_baseline_rows": list(coverage_runtime_baseline.get("coverage_group_rows") or []),
        "coverage_runtime_baseline_by_group": dict(coverage_runtime_baseline.get("by_coverage_group") or {}),
        "coverage_runtime_baseline_groups_needing_attention": list(coverage_runtime_baseline.get("groups_needing_attention") or []),
        "fixture_text_used_for_runtime_branching": False,
        "runtime_branching_uses_fixture_strings": False,
        "machine_metrics_separated_from_blind_qa": True,
        "machine_metrics_only": True,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_requires_blind_qa": True,
        "read_feeling_auto_filled_from_machine_metrics": False,
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
        "surface_signature_id": "surface_signature_identifier_from_step2",
        "surface_major_reasons": "surface_template_grammar_or_repetition_reason_codes",
        "grammar_warning_codes": "surface_grammar_warning_codes",
        "surface_signature_repeat_rate": "repeated_surface_signature_family_rate",
        "connector_repetition_rate": "connector_repetition_event_rate",
        "grammar_warning_rate": "surface_grammar_warning_event_rate",
        "coverage_surface_diversity_rate": "unique_surface_signature_family_rate",
        "tone_engine_2_1_major_count": "step9_tone_engine_2_1_major_detection_count",
        "tone_safety_major_count": "step9_tone_safety_major_detection_count",
        "tone_distance_major_count": "step9_tone_distance_major_detection_count",
        "tone_naturalness_major_count": "step9_tone_naturalness_major_detection_count",
        "coverage_runtime_baseline": "step4_coverage_group_surface_binding_grammar_baseline",
        "coverage_runtime_baseline_rows": "step4_coverage_group_baseline_rows",
        "step11_blind_qa_long_run_ready": "step11_blind_qa_long_run_summary_ready",
        "long_run_surface_signature_diversity_rate": "step11_long_run_surface_signature_diversity_rate",
        "long_run_surface_signature_repeat_rate": "step11_long_run_surface_signature_repeat_rate",
        "long_run_surface_signature_repeat_detected": "step11_long_run_surface_signature_repeat_detected",
        "reviewable_blind_qa_candidate_count": "step11_reviewable_candidate_count",
        "unreviewed_reviewable_candidate_count": "step11_unreviewed_reviewable_candidate_count",
        "top_rejection_reasons": "next_implementation_priority_reasons",
        "observation_fixture_group": "step13_observation_reply_regression_fixture_group",
        "expected_observation_reply_kind": "expected_step13_observation_reply_branch",
        "expected_eligibility_status": "expected_step13_observation_eligibility_status",
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
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_requires_blind_qa": True,
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
    events: Sequence[Any] | Iterable[Any] | None = None,
    records: Sequence[Any] | Iterable[Any] | None = None,
    scorecard_harness: Mapping[str, Any] | None = None,
    fixture_qa_run: Mapping[str, Any] | None = None,
    diagnostic_summary: Mapping[str, Any] | None = None,
    blind_qa_reviews: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
) -> dict[str, Any]:
    observation_scorecard_source_events: list[Any] = []
    if scorecard_event:
        observation_scorecard_source_events.append(scorecard_event)
    observation_scorecard_source_events.extend(list(scorecard_events or []))
    observation_scorecard_source_events.extend(list(events or []))
    observation_scorecard_source_events.extend(list(records or []))
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
                observation_scorecard_source_events.append(dict(nested))
                break

    events = _normalize_records(
        scorecard_event=scorecard_event,
        scorecard_events=list(scorecard_events or []) + list(events or []),
        records=records,
        scorecard_harness=scorecard_harness,
        fixture_qa_run=fixture_qa_run,
        diagnostic_summary=diagnostic_summary,
    )
    machine = _aggregate_machine_metrics(events)
    coverage_runtime_baseline = _safe_mapping(machine.get("coverage_runtime_baseline"))
    blind_qa_review_records = list(blind_qa_reviews or [])
    blind_qa = aggregate_complete_product_quality_blind_qa_reviews(blind_qa_review_records)
    runtime_surface_blind_qa_long_run = build_runtime_surface_blind_qa_long_run_summary(
        events=events,
        blind_qa_reviews=blind_qa_review_records,
    )
    runtime_surface_blind_qa_long_run_fields = normalize_runtime_surface_blind_qa_long_run_to_scorecard_fields(
        runtime_surface_blind_qa_long_run
    )
    observation_scorecard_blind_qa = build_observation_scorecard_blind_qa(
        scorecard_events=observation_scorecard_source_events or events,
        blind_qa_reviews=blind_qa_review_records,
    )
    observation_scorecard_blind_qa_fields = normalize_observation_scorecard_blind_qa_to_scorecard_fields(
        observation_scorecard_blind_qa
    )

    observation_regression_fixture_sources: list[Any] = []
    for source in (fixture_qa_run, diagnostic_summary):
        data = _safe_mapping(source)
        if not data:
            continue
        for key in (
            "step13_observation_regression_fixture_results",
            "observation_regression_fixture_results",
            "observation_reply_regression_fixture_results",
            "regression_fixture_results",
        ):
            value = data.get(key)
            if isinstance(value, (list, tuple)):
                observation_regression_fixture_sources.extend(list(value))
        nested = _safe_mapping(data.get("step13_observation_regression_fixture_coverage"))
        if nested:
            value = nested.get("results")
            if isinstance(value, (list, tuple)):
                observation_regression_fixture_sources.extend(list(value))
    for event in observation_scorecard_source_events:
        data = _safe_mapping(event)
        if data.get("fixture_group") or data.get("observation_fixture_group"):
            observation_regression_fixture_sources.append(data)
    observation_regression_fixture_coverage = build_observation_regression_fixture_coverage(
        fixture_results=observation_regression_fixture_sources,
    )
    observation_regression_fixture_fields = normalize_observation_regression_fixture_coverage_to_scorecard_fields(
        observation_regression_fixture_coverage
    )
    observation_regression_fixture_requested = bool(observation_regression_fixture_sources)
    observation_exit_gate_handoff = build_observation_exit_gate_handoff(
        scorecard=observation_scorecard_blind_qa,
        regression_fixture_coverage=(
            observation_regression_fixture_coverage if observation_regression_fixture_requested else None
        ),
    )
    observation_exit_gate_handoff_fields = normalize_observation_exit_gate_handoff_to_scorecard_fields(
        observation_exit_gate_handoff
    )
    product_readfeel_source_events = list(observation_scorecard_source_events or events)
    product_readfeel_mirror_only_surface_detector_summary = build_mirror_only_surface_detector_summary(
        events=product_readfeel_source_events,
    )
    product_readfeel_mirror_only_surface_detector_fields = (
        normalize_mirror_only_surface_detector_summary_to_scorecard_fields(
            product_readfeel_mirror_only_surface_detector_summary
        )
    )
    product_readfeel_events_with_phase6_mirror_detector = enrich_events_with_mirror_only_surface_detection(
        product_readfeel_source_events,
    )
    product_readfeel_current_output_inventory = build_product_readfeel_current_output_inventory(
        events=product_readfeel_events_with_phase6_mirror_detector,
        blind_qa_reviews=blind_qa_review_records,
    )
    product_readfeel_current_output_inventory_fields = (
        normalize_product_readfeel_current_output_inventory_to_scorecard_fields(
            product_readfeel_current_output_inventory
        )
    )
    product_readfeel_rubric = build_product_readfeel_rubric()
    product_readfeel_blind_qa = aggregate_product_readfeel_blind_qa_reviews(blind_qa_review_records)
    product_readfeel_rubric_fields = normalize_product_readfeel_rubric_to_scorecard_fields(
        product_readfeel_rubric,
        product_readfeel_blind_qa,
    )
    product_readfeel_scorecard_current_output_inventory = build_product_readfeel_current_output_inventory(
        events=product_readfeel_events_with_phase6_mirror_detector,
    )
    product_readfeel_scorecard = build_product_readfeel_scorecard(
        events=product_readfeel_events_with_phase6_mirror_detector,
        blind_qa_reviews=blind_qa_review_records,
        machine_metrics=machine,
        current_output_inventory=product_readfeel_scorecard_current_output_inventory,
        blind_qa_aggregate=product_readfeel_blind_qa,
    )
    product_readfeel_scorecard_fields = normalize_product_readfeel_scorecard_to_scorecard_fields(
        product_readfeel_scorecard
    )
    product_readfeel_long_run_product_gate = build_product_readfeel_long_run_product_gate(
        events=product_readfeel_events_with_phase6_mirror_detector,
        product_readfeel_scorecard=product_readfeel_scorecard,
        runtime_long_run_summary=runtime_surface_blind_qa_long_run,
        blind_qa_aggregate=product_readfeel_blind_qa,
    )
    product_readfeel_long_run_product_gate_fields = (
        normalize_product_readfeel_long_run_product_gate_to_scorecard_fields(
            product_readfeel_long_run_product_gate
        )
    )
    rubric = build_complete_product_quality_blind_qa_rubric()

    display_reach_rate = float(machine.get("display_reach_rate") or 0.0)
    binding_pass_rate = float(machine.get("binding_pass_rate") or 0.0)
    reason_coverage_rate = float(machine.get("reason_coverage_rate") or 0.0)
    read_feeling_score = blind_qa.get("read_feeling_score")
    template_major_count = _safe_int(machine.get("template_major_count"), 0)
    safety_major_count = _safe_int(machine.get("safety_major_count"), 0)
    surface_template_major_count = _safe_int(machine.get("surface_template_major_count"), 0)
    surface_signature_repeat_rate = float(machine.get("surface_signature_repeat_rate") or 0.0)
    connector_repetition_rate = float(machine.get("connector_repetition_rate") or 0.0)
    grammar_warning_rate = float(machine.get("grammar_warning_rate") or 0.0)
    coverage_surface_diversity_rate = float(machine.get("coverage_surface_diversity_rate") or 0.0)
    template_major_count = max(template_major_count, surface_template_major_count)
    missing_coverage_groups = list(machine.get("missing_coverage_groups") or [])
    coverage_group_missing_count = _safe_int(machine.get("coverage_group_missing_count"), 0)

    threshold_checks = {
        "display_reach_rate_connection": display_reach_rate >= COMPLETE_PRODUCT_QUALITY_CONNECTION_DISPLAY_TARGET,
        "display_reach_rate_product_gate": display_reach_rate >= COMPLETE_PRODUCT_GATE_DISPLAY_TARGET,
        "binding_pass_rate": binding_pass_rate >= COMPLETE_PRODUCT_QUALITY_BINDING_TARGET,
        "read_feeling_score_connection": bool(read_feeling_score is not None and float(read_feeling_score) >= COMPLETE_PRODUCT_QUALITY_READ_FEELING_INITIAL_TARGET),
        "read_feeling_score_product_gate": bool(read_feeling_score is not None and float(read_feeling_score) >= COMPLETE_PRODUCT_QUALITY_READ_FEELING_PRODUCT_TARGET),
        "template_major_count_zero": template_major_count == 0,
        "surface_template_major_count_zero": surface_template_major_count == 0,
        "safety_major_count_zero": safety_major_count == 0,
        "reason_coverage_rate": reason_coverage_rate >= COMPLETE_PRODUCT_QUALITY_REASON_COVERAGE_TARGET,
        "coverage_group_aggregation_ready": bool(machine.get("coverage_group_aggregation_ready")),
        "coverage_runtime_baseline_ready": bool(coverage_runtime_baseline.get("coverage_runtime_baseline_ready")),
        "step4_coverage_runtime_baseline_ready": bool(coverage_runtime_baseline.get("step4_coverage_runtime_baseline_ready")),
        "required_coverage_groups_complete": not missing_coverage_groups and coverage_group_missing_count == 0,
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
    if surface_template_major_count > 0:
        release_blockers.append("surface_template_major_detected")
    if safety_major_count > 0:
        release_blockers.append("safety_major_detected")
    if _safe_int(machine.get("runtime_surface_self_repair_policy_violation_count"), 0) > 0:
        release_blockers.append("surface_aware_self_repair_policy_violation")
    if _safe_int(machine.get("runtime_surface_self_repair_meaning_added_count"), 0) > 0:
        release_blockers.append("surface_aware_self_repair_meaning_added")
    if _safe_int(machine.get("runtime_surface_self_repair_aborted_count"), 0) > 0:
        release_blockers.append("surface_aware_self_repair_unresolved")
    if coverage_group_missing_count > 0:
        release_blockers.append("coverage_group_missing")
    if missing_coverage_groups:
        release_blockers.append("coverage_groups_incomplete")
    for blocker in _dedupe(coverage_runtime_baseline.get("release_blockers")):
        if blocker not in release_blockers:
            release_blockers.append(blocker)
    if blind_qa.get("blind_qa_ready") and not threshold_checks["read_feeling_score_connection"]:
        release_blockers.append("read_feeling_score_below_connection_target")
    if blind_qa.get("blind_qa_ready") and not threshold_checks["read_feeling_score_product_gate"]:
        release_blockers.append("read_feeling_score_below_product_gate_target")
    if observation_regression_fixture_requested and not observation_regression_fixture_coverage.get("step13_regression_fixture_coverage_ready"):
        release_blockers.append("observation_regression_fixture_coverage_incomplete")
        for blocker in _dedupe(observation_regression_fixture_coverage.get("release_blockers")):
            release_blockers.append(blocker)
    product_gate_thresholds_met = all(threshold_checks.values()) and bool(events) and bool(blind_qa.get("blind_qa_ready"))
    read_feeling_source = "blind_qa" if blind_qa.get("blind_qa_ready") else "blind_qa_required_not_evaluated"

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
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "machine_metrics": machine,
        "blind_qa_metrics": blind_qa,
        "blind_qa_rubric": rubric,
        "surface_metrics_version": COMPLETE_PRODUCT_QUALITY_SURFACE_METRICS_VERSION,
        "surface_metrics_step": COMPLETE_PRODUCT_QUALITY_SURFACE_METRICS_STEP,
        "surface_metrics_ready": bool(machine.get("surface_metrics_ready")),
        "step3_scorecard_surface_metrics_connected": bool(machine.get("step3_scorecard_surface_metrics_connected")),
        "coverage_runtime_baseline_version": RUNTIME_SURFACE_COVERAGE_BASELINE_VERSION,
        "coverage_runtime_baseline_step": RUNTIME_SURFACE_COVERAGE_BASELINE_STEP,
        "coverage_runtime_baseline_ready": bool(coverage_runtime_baseline.get("coverage_runtime_baseline_ready")),
        "step4_coverage_runtime_baseline_ready": bool(coverage_runtime_baseline.get("step4_coverage_runtime_baseline_ready")),
        "coverage_runtime_baseline": coverage_runtime_baseline,
        "coverage_runtime_baseline_rows": list(coverage_runtime_baseline.get("coverage_group_rows") or []),
        "coverage_runtime_baseline_by_group": dict(coverage_runtime_baseline.get("by_coverage_group") or {}),
        "coverage_runtime_baseline_groups_needing_attention": list(coverage_runtime_baseline.get("groups_needing_attention") or []),
        "fixture_text_used_for_runtime_branching": False,
        "runtime_branching_uses_fixture_strings": False,
        "surface_metrics": dict(machine.get("surface_metrics") or {}),
        "surface_signature_count": _safe_int(machine.get("surface_signature_count"), 0),
        "surface_signature_unique_count": _safe_int(machine.get("surface_signature_unique_count"), 0),
        "surface_signature_repeat_count": _safe_int(machine.get("surface_signature_repeat_count"), 0),
        "surface_signature_repeat_rate": surface_signature_repeat_rate,
        "connector_repetition_rate": connector_repetition_rate,
        "predicate_family_repetition_rate": float(machine.get("predicate_family_repetition_rate") or 0.0),
        "ending_repetition_rate": float(machine.get("ending_repetition_rate") or 0.0),
        "generic_opening_rate": float(machine.get("generic_opening_rate") or 0.0),
        "grammar_warning_rate": grammar_warning_rate,
        "coverage_surface_diversity_rate": coverage_surface_diversity_rate,
        "surface_template_major_count": surface_template_major_count,
        "surface_major_reasons": list(machine.get("surface_major_reasons") or []),
        "surface_grammar_warning_codes": list(machine.get("surface_grammar_warning_codes") or []),
        "tone_engine_2_1_version": RUNTIME_SURFACE_TONE_ENGINE_2_1_VERSION,
        "step9_tone_engine_2_1_connected": bool(machine.get("step9_tone_engine_2_1_connected")),
        "tone_guard_major_count": _safe_int(machine.get("tone_guard_major_count"), 0),
        "tone_engine_2_1_major_count": _safe_int(machine.get("tone_engine_2_1_major_count"), 0),
        "tone_safety_major_count": _safe_int(machine.get("tone_safety_major_count"), 0),
        "tone_distance_major_count": _safe_int(machine.get("tone_distance_major_count"), 0),
        "tone_naturalness_major_count": _safe_int(machine.get("tone_naturalness_major_count"), 0),
        "tone_read_feeling_machine_warning_count": _safe_int(machine.get("tone_read_feeling_machine_warning_count"), 0),
        "tone_completion_requires_blind_qa": True,
        "runtime_surface_self_repair_version": RUNTIME_SURFACE_SELF_REPAIR_VERSION,
        "runtime_surface_self_repair_step": RUNTIME_SURFACE_SELF_REPAIR_STEP,
        "step10_surface_aware_self_repair_connected": bool(machine.get("step10_surface_aware_self_repair_connected")),
        "step10_surface_aware_self_repair_ready": bool(machine.get("step10_surface_aware_self_repair_ready")),
        "runtime_surface_self_repair_attempt_count": _safe_int(machine.get("runtime_surface_self_repair_attempt_count"), 0),
        "runtime_surface_self_repair_success_count": _safe_int(machine.get("runtime_surface_self_repair_success_count"), 0),
        "runtime_surface_self_repair_aborted_count": _safe_int(machine.get("runtime_surface_self_repair_aborted_count"), 0),
        "runtime_surface_self_repair_policy_violation_count": _safe_int(machine.get("runtime_surface_self_repair_policy_violation_count"), 0),
        "runtime_surface_self_repair_meaning_added_count": _safe_int(machine.get("runtime_surface_self_repair_meaning_added_count"), 0),
        "runtime_surface_self_repair_success_rate": float(machine.get("runtime_surface_self_repair_success_rate") or 0.0),
        "runtime_surface_blind_qa_long_run_version": RUNTIME_SURFACE_BLIND_QA_LONG_RUN_VERSION,
        "runtime_surface_blind_qa_long_run_step": RUNTIME_SURFACE_BLIND_QA_LONG_RUN_STEP,
        "step11_blind_qa_long_run_ready": bool(runtime_surface_blind_qa_long_run.get("step11_blind_qa_long_run_ready")),
        "runtime_surface_blind_qa_long_run_ready": bool(runtime_surface_blind_qa_long_run.get("runtime_surface_blind_qa_long_run_ready")),
        "runtime_surface_blind_qa_long_run_summary": runtime_surface_blind_qa_long_run,
        "step11_blind_qa_long_run_summary": runtime_surface_blind_qa_long_run,
        "step11_scorecard_fields": runtime_surface_blind_qa_long_run_fields,
        "long_run_signature_diversity": dict(runtime_surface_blind_qa_long_run.get("long_run_signature_diversity") or {}),
        "long_run_surface_signature_diversity_ready": runtime_surface_blind_qa_long_run_fields.get("long_run_surface_signature_diversity_ready"),
        "long_run_surface_signature_diversity_rate": runtime_surface_blind_qa_long_run_fields.get("long_run_surface_signature_diversity_rate"),
        "long_run_surface_signature_repeat_rate": runtime_surface_blind_qa_long_run_fields.get("long_run_surface_signature_repeat_rate"),
        "long_run_surface_signature_repeat_detected": runtime_surface_blind_qa_long_run_fields.get("long_run_surface_signature_repeat_detected"),
        "long_run_groups_needing_attention": list(runtime_surface_blind_qa_long_run_fields.get("long_run_groups_needing_attention") or []),
        "blind_qa_candidate_count": runtime_surface_blind_qa_long_run_fields.get("blind_qa_candidate_count"),
        "reviewable_blind_qa_candidate_count": runtime_surface_blind_qa_long_run_fields.get("reviewable_blind_qa_candidate_count"),
        "unreviewed_reviewable_candidate_count": runtime_surface_blind_qa_long_run_fields.get("unreviewed_reviewable_candidate_count"),
        "blind_qa_missing_count": runtime_surface_blind_qa_long_run_fields.get("blind_qa_missing_count"),
        "step11_qa_gaps": list(runtime_surface_blind_qa_long_run_fields.get("qa_gaps") or []),
        "step11_release_blockers": list(runtime_surface_blind_qa_long_run_fields.get("step11_release_blockers") or []),
        "product_readfeel_current_output_inventory_version": PRODUCT_READFEEL_CURRENT_OUTPUT_INVENTORY_VERSION,
        "product_readfeel_current_output_inventory_step": PRODUCT_READFEEL_CURRENT_OUTPUT_INVENTORY_STEP,
        "phase1_product_readfeel_current_output_inventory": product_readfeel_current_output_inventory,
        "phase1_product_readfeel_current_output_inventory_fields": product_readfeel_current_output_inventory_fields,
        "phase1_product_readfeel_current_output_inventory_ready": bool(
            product_readfeel_current_output_inventory_fields.get(
                "phase1_product_readfeel_current_output_inventory_ready"
            )
        ),
        "product_readfeel_phase1_ready": bool(
            product_readfeel_current_output_inventory_fields.get("product_readfeel_phase1_ready")
        ),
        "product_readfeel_family_verdicts": dict(
            product_readfeel_current_output_inventory_fields.get("product_readfeel_family_verdicts") or {}
        ),
        "product_readfeel_observed_families": list(
            product_readfeel_current_output_inventory_fields.get("product_readfeel_observed_families") or []
        ),
        "product_readfeel_missing_families": list(
            product_readfeel_current_output_inventory_fields.get("product_readfeel_missing_families") or []
        ),
        "product_readfeel_failure_bucket_counts": dict(
            product_readfeel_current_output_inventory_fields.get("product_readfeel_failure_bucket_counts") or {}
        ),
        "product_readfeel_display_not_reached_count": product_readfeel_current_output_inventory_fields.get(
            "product_readfeel_display_not_reached_count"
        ),
        "product_readfeel_contract_violation_count": product_readfeel_current_output_inventory_fields.get(
            "product_readfeel_contract_violation_count"
        ),
        "product_readfeel_surface_breakage_count": product_readfeel_current_output_inventory_fields.get(
            "product_readfeel_surface_breakage_count"
        ),
        "product_readfeel_readfeel_gap_count": product_readfeel_current_output_inventory_fields.get(
            "product_readfeel_readfeel_gap_count"
        ),
        "product_readfeel_structure_insight_gap_count": product_readfeel_current_output_inventory_fields.get(
            "product_readfeel_structure_insight_gap_count"
        ),
        "product_readfeel_mirror_only_detected_count": product_readfeel_current_output_inventory_fields.get(
            "product_readfeel_mirror_only_detected_count"
        ),
        "product_readfeel_v1_fix_families": list(
            product_readfeel_current_output_inventory_fields.get("product_readfeel_v1_fix_families") or []
        ),
        "product_readfeel_v2_structure_insight_backlog_families": list(
            product_readfeel_current_output_inventory_fields.get(
                "product_readfeel_v2_structure_insight_backlog_families"
            )
            or []
        ),
        "product_readfeel_mirror_only_surface_detector_version": MIRROR_ONLY_SURFACE_DETECTOR_VERSION,
        "product_readfeel_mirror_only_surface_detector_step": MIRROR_ONLY_SURFACE_DETECTOR_STEP,
        "phase6_product_readfeel_mirror_only_surface_detector": product_readfeel_mirror_only_surface_detector_summary,
        "phase6_product_readfeel_mirror_only_surface_detector_fields": product_readfeel_mirror_only_surface_detector_fields,
        "phase6_mirror_only_detector_ready": bool(
            product_readfeel_mirror_only_surface_detector_fields.get("phase6_mirror_only_detector_ready")
        ),
        "phase6_product_readfeel_mirror_only_detector_ready": bool(
            product_readfeel_mirror_only_surface_detector_fields.get(
                "phase6_product_readfeel_mirror_only_detector_ready"
            )
        ),
        "product_readfeel_phase6_ready": bool(
            product_readfeel_mirror_only_surface_detector_fields.get("product_readfeel_phase6_ready")
        ),
        "product_readfeel_mirror_only_report_count": product_readfeel_mirror_only_surface_detector_fields.get(
            "product_readfeel_mirror_only_report_count"
        ),
        "product_readfeel_mirror_only_evaluated_count": product_readfeel_mirror_only_surface_detector_fields.get(
            "product_readfeel_mirror_only_evaluated_count"
        ),
        "product_readfeel_mirror_only_surface_detected_count": product_readfeel_mirror_only_surface_detector_fields.get(
            "product_readfeel_mirror_only_detected_count"
        ),
        "product_readfeel_mirror_only_v1_yellow_or_repair_connected_count": (
            product_readfeel_mirror_only_surface_detector_fields.get(
                "product_readfeel_mirror_only_v1_yellow_or_repair_connected_count"
            )
        ),
        "product_readfeel_mirror_only_v1_repair_required_count": (
            product_readfeel_mirror_only_surface_detector_fields.get(
                "product_readfeel_mirror_only_v1_repair_required_count"
            )
        ),
        "product_readfeel_mirror_only_v2_insight_delta_gap_count": (
            product_readfeel_mirror_only_surface_detector_fields.get(
                "product_readfeel_mirror_only_v2_insight_delta_gap_count"
            )
        ),
        "product_readfeel_mirror_only_detected_families": list(
            product_readfeel_mirror_only_surface_detector_fields.get(
                "product_readfeel_mirror_only_detected_families"
            )
            or []
        ),
        "product_readfeel_mirror_only_family_detected_counts": dict(
            product_readfeel_mirror_only_surface_detector_fields.get(
                "product_readfeel_mirror_only_family_detected_counts"
            )
            or {}
        ),
        "product_readfeel_rubric_version": PRODUCT_READFEEL_RUBRIC_VERSION,
        "product_readfeel_rubric_step": PRODUCT_READFEEL_RUBRIC_STEP,
        "phase2_product_readfeel_rubric": product_readfeel_rubric,
        "phase2_product_readfeel_blind_qa_metrics": product_readfeel_blind_qa,
        "phase2_product_readfeel_rubric_fields": product_readfeel_rubric_fields,
        "phase2_product_readfeel_rubric_ready": bool(
            product_readfeel_rubric_fields.get("phase2_product_readfeel_rubric_ready")
        ),
        "product_readfeel_phase2_ready": bool(
            product_readfeel_rubric_fields.get("product_readfeel_phase2_ready")
        ),
        "product_readfeel_rubric_implementation_decision": (
            product_readfeel_rubric_fields.get("product_readfeel_rubric_implementation_decision")
            or product_readfeel_rubric.get("implementation_decision")
        ),
        "product_readfeel_machine_metrics_separated_from_blind_qa": product_readfeel_rubric_fields.get(
            "product_readfeel_machine_metrics_separated_from_blind_qa"
        ),
        "product_readfeel_read_feeling_requires_blind_qa": product_readfeel_rubric_fields.get(
            "product_readfeel_read_feeling_requires_blind_qa"
        ),
        "product_readfeel_read_feeling_source": product_readfeel_rubric_fields.get(
            "product_readfeel_read_feeling_source"
        ),
        "product_readfeel_read_feeling_score": product_readfeel_rubric_fields.get(
            "product_readfeel_read_feeling_score"
        ),
        "product_readfeel_v1_score": product_readfeel_rubric_fields.get("product_readfeel_v1_score"),
        "product_readfeel_v1_pass_rate": product_readfeel_rubric_fields.get("product_readfeel_v1_pass_rate"),
        "product_readfeel_v1_product_pass_candidate_rate": product_readfeel_rubric_fields.get(
            "product_readfeel_v1_product_pass_candidate_rate"
        ),
        "product_readfeel_v2_structure_insight_ready_candidate_rate": product_readfeel_rubric_fields.get(
            "product_readfeel_v2_structure_insight_ready_candidate_rate"
        ),
        "product_readfeel_required_dimensions": list(
            product_readfeel_rubric_fields.get("product_readfeel_required_dimensions") or []
        ),
        "product_readfeel_optional_v2_dimensions": list(
            product_readfeel_rubric_fields.get("product_readfeel_optional_v2_dimensions") or []
        ),
        "product_readfeel_dimension_scores": dict(
            product_readfeel_rubric_fields.get("product_readfeel_dimension_scores") or {}
        ),
        "product_readfeel_missing_required_dimension_counts": dict(
            product_readfeel_rubric_fields.get("product_readfeel_missing_required_dimension_counts") or {}
        ),
        "product_readfeel_machine_metrics_used_for_read_feeling": product_readfeel_rubric_fields.get(
            "product_readfeel_machine_metrics_used_for_read_feeling"
        ),
        "product_readfeel_read_feeling_auto_filled_from_machine_metrics": product_readfeel_rubric_fields.get(
            "product_readfeel_read_feeling_auto_filled_from_machine_metrics"
        ),
        "product_readfeel_blind_qa_review_count": product_readfeel_rubric_fields.get(
            "product_readfeel_blind_qa_review_count"
        ),
        "product_readfeel_blind_qa_ready": bool(
            product_readfeel_rubric_fields.get("product_readfeel_blind_qa_ready")
        ),
        "product_readfeel_scorecard_version": PRODUCT_READFEEL_SCORECARD_VERSION,
        "product_readfeel_scorecard_step": PRODUCT_READFEEL_SCORECARD_STEP,
        "phase4_product_readfeel_scorecard": product_readfeel_scorecard,
        "phase4_product_readfeel_scorecard_fields": product_readfeel_scorecard_fields,
        "phase4_product_readfeel_scorecard_ready": bool(
            product_readfeel_scorecard_fields.get("phase4_product_readfeel_scorecard_ready")
        ),
        "product_readfeel_phase4_ready": bool(
            product_readfeel_scorecard_fields.get("product_readfeel_phase4_ready")
        ),
        "product_readfeel_scorecard_ready": bool(
            product_readfeel_scorecard_fields.get("product_readfeel_scorecard_ready")
        ),
        "product_readfeel_aggregate_verdict": product_readfeel_scorecard_fields.get(
            "product_readfeel_aggregate_verdict"
        ),
        "product_readfeel_scorecard_aggregate_verdict": product_readfeel_scorecard_fields.get(
            "product_readfeel_scorecard_aggregate_verdict"
        ),
        "product_readfeel_scorecard_verdict": product_readfeel_scorecard_fields.get(
            "product_readfeel_scorecard_verdict"
        ),
        "product_readfeel_scorecard_family_verdict_counts": dict(
            product_readfeel_scorecard_fields.get("product_readfeel_scorecard_family_verdict_counts") or {}
        ),
        "product_readfeel_verdict_counts": dict(
            product_readfeel_scorecard_fields.get("product_readfeel_verdict_counts") or {}
        ),
        "product_readfeel_scorecard_release_blockers": list(
            product_readfeel_scorecard_fields.get("product_readfeel_scorecard_release_blockers") or []
        ),
        "product_readfeel_scorecard_v2_readiness_gaps": list(
            product_readfeel_scorecard_fields.get("product_readfeel_scorecard_v2_readiness_gaps") or []
        ),
        "product_readfeel_v2_readiness_gaps": list(
            product_readfeel_scorecard_fields.get("product_readfeel_v2_readiness_gaps") or []
        ),
        "product_readfeel_scorecard_next_action": product_readfeel_scorecard_fields.get(
            "product_readfeel_scorecard_next_action"
        ),
        "product_readfeel_aggregate_verdict_counts": dict(
            product_readfeel_scorecard_fields.get("product_readfeel_aggregate_verdict_counts") or {}
        ),
        "product_readfeel_family_verdict_counts": dict(
            product_readfeel_scorecard_fields.get("product_readfeel_family_verdict_counts") or {}
        ),
        "product_readfeel_required_family_verdict_counts": dict(
            product_readfeel_scorecard_fields.get("product_readfeel_required_family_verdict_counts") or {}
        ),
        "product_readfeel_family_results": list(
            product_readfeel_scorecard_fields.get("product_readfeel_family_results") or []
        ),
        "product_readfeel_family_coverage_rate": product_readfeel_scorecard_fields.get(
            "product_readfeel_family_coverage_rate"
        ),
        "product_readfeel_family_pass_rate": product_readfeel_scorecard_fields.get(
            "product_readfeel_family_pass_rate"
        ),
        "product_readfeel_red_family_count": product_readfeel_scorecard_fields.get(
            "product_readfeel_red_family_count"
        ),
        "product_readfeel_repair_required_family_count": product_readfeel_scorecard_fields.get(
            "product_readfeel_repair_required_family_count"
        ),
        "product_readfeel_yellow_family_count": product_readfeel_scorecard_fields.get(
            "product_readfeel_yellow_family_count"
        ),
        "product_readfeel_pass_family_count": product_readfeel_scorecard_fields.get(
            "product_readfeel_pass_family_count"
        ),
        "product_readfeel_product_pass_count": product_readfeel_scorecard_fields.get(
            "product_readfeel_product_pass_count"
        ),
        "product_readfeel_v1_product_pass_candidate": bool(
            product_readfeel_scorecard_fields.get("product_readfeel_v1_product_pass_candidate")
        ),
        "product_readfeel_v2_structure_insight_ready_candidate": bool(
            product_readfeel_scorecard_fields.get("product_readfeel_v2_structure_insight_ready_candidate")
        ),
        "product_readfeel_v2_readiness_not_release_blocker": True,
        "product_readfeel_insight_delta_release_blocker": False,
        "product_readfeel_release_blockers_include_insight_delta": False,
        "product_readfeel_phase4_internal_gaps": list(
            product_readfeel_scorecard_fields.get("product_readfeel_phase4_internal_gaps") or []
        ),
        "product_readfeel_phase11_long_run_product_gate_version": PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_VERSION,
        "product_readfeel_phase11_long_run_product_gate_step": PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_STEP,
        "phase11_product_readfeel_long_run_product_gate": product_readfeel_long_run_product_gate,
        "phase11_product_readfeel_long_run_product_gate_fields": product_readfeel_long_run_product_gate_fields,
        "phase11_product_readfeel_long_run_product_gate_ready": bool(
            product_readfeel_long_run_product_gate_fields.get(
                "phase11_product_readfeel_long_run_product_gate_ready"
            )
        ),
        "product_readfeel_phase11_ready": bool(
            product_readfeel_long_run_product_gate_fields.get("product_readfeel_phase11_ready")
        ),
        "product_readfeel_phase11_v1_product_pass_candidate": bool(
            product_readfeel_long_run_product_gate_fields.get(
                "product_readfeel_phase11_v1_product_pass_candidate"
            )
        ),
        "product_readfeel_phase11_v2_structure_insight_ready": bool(
            product_readfeel_long_run_product_gate_fields.get(
                "product_readfeel_phase11_v2_structure_insight_ready"
            )
        ),
        "product_readfeel_phase11_v1_product_pass_blockers": list(
            product_readfeel_long_run_product_gate_fields.get(
                "product_readfeel_phase11_v1_product_pass_blockers"
            ) or []
        ),
        "product_readfeel_phase11_v2_structure_insight_ready_blockers": list(
            product_readfeel_long_run_product_gate_fields.get(
                "product_readfeel_phase11_v2_structure_insight_ready_blockers"
            ) or []
        ),
        "product_readfeel_phase11_max_consecutive_v1_product_pass_count": (
            product_readfeel_long_run_product_gate_fields.get(
                "product_readfeel_phase11_max_consecutive_v1_product_pass_count"
            )
        ),
        "product_readfeel_phase11_max_consecutive_v2_structure_insight_ready_count": (
            product_readfeel_long_run_product_gate_fields.get(
                "product_readfeel_phase11_max_consecutive_v2_structure_insight_ready_count"
            )
        ),
        "product_readfeel_phase11_consecutive_5_v1_product_pass_ready": bool(
            product_readfeel_long_run_product_gate_fields.get(
                "product_readfeel_phase11_consecutive_5_v1_product_pass_ready"
            )
        ),
        "product_readfeel_phase11_consecutive_10_v1_product_pass_ready": bool(
            product_readfeel_long_run_product_gate_fields.get(
                "product_readfeel_phase11_consecutive_10_v1_product_pass_ready"
            )
        ),
        "product_readfeel_phase11_family_cross_surface_repetition_detected": bool(
            product_readfeel_long_run_product_gate_fields.get(
                "product_readfeel_phase11_family_cross_surface_repetition_detected"
            )
        ),
        "product_readfeel_phase11_insight_surface_same_syntax_repetition_detected": bool(
            product_readfeel_long_run_product_gate_fields.get(
                "product_readfeel_phase11_insight_surface_same_syntax_repetition_detected"
            )
        ),
        "product_readfeel_phase11_release_judgment_deferred": True,
        "product_readfeel_phase11_product_gate_ready": False,
        "product_readfeel_phase11_public_release_applied": False,
        "observation_scorecard_blind_qa_version": OBSERVATION_SCORECARD_BLIND_QA_VERSION,
        "observation_reply_scorecard_blind_qa_version": OBSERVATION_SCORECARD_BLIND_QA_VERSION,
        "observation_scorecard_blind_qa_step": OBSERVATION_SCORECARD_BLIND_QA_STEP,
        "observation_reply_scorecard_blind_qa_step": OBSERVATION_SCORECARD_BLIND_QA_STEP,
        "observation_scorecard_ready": bool(observation_scorecard_blind_qa.get("observation_scorecard_ready")),
        "observation_blind_qa_ready": bool(observation_scorecard_blind_qa.get("observation_blind_qa_ready")),
        "step12_observation_scorecard_ready": bool(observation_scorecard_blind_qa.get("observation_scorecard_ready")),
        "step12_observation_scorecard_blind_qa_ready": bool(observation_scorecard_blind_qa.get("step12_scorecard_blind_qa_ready")),
        "observation_scorecard_blind_qa": observation_scorecard_blind_qa,
        "step12_observation_scorecard": observation_scorecard_blind_qa,
        "step12_observation_scorecard_fields": observation_scorecard_blind_qa_fields,
        "step13_regression_fixture_coverage": dict(
            observation_scorecard_blind_qa.get("step13_regression_fixture_coverage") or {}
        ),
        "observation_regression_fixture_coverage": dict(
            observation_scorecard_blind_qa.get("observation_regression_fixture_coverage") or {}
        ),
        "step13_regression_fixture_coverage_ready": bool(
            observation_scorecard_blind_qa_fields.get("step13_regression_fixture_coverage_ready")
        ),
        "observation_regression_fixture_coverage_rate": observation_scorecard_blind_qa_fields.get(
            "observation_regression_fixture_coverage_rate"
        ),
        "observation_regression_fixture_success_coverage_rate": observation_scorecard_blind_qa_fields.get(
            "observation_regression_fixture_success_coverage_rate"
        ),
        "observation_regression_missing_fixture_groups": list(
            observation_scorecard_blind_qa_fields.get("observation_regression_missing_fixture_groups") or []
        ),
        "observation_regression_observed_fixture_groups": list(
            observation_scorecard_blind_qa_fields.get("observation_regression_observed_fixture_groups") or []
        ),
        "observation_regression_release_blockers": list(
            observation_scorecard_blind_qa_fields.get("observation_regression_release_blockers") or []
        ),
        "observation_metrics": dict(observation_scorecard_blind_qa.get("machine_metrics") or {}),
        "observation_always_display_rate": observation_scorecard_blind_qa_fields.get("always_display_rate"),
        "observation_eligible_observation_rate": observation_scorecard_blind_qa_fields.get("eligible_observation_rate"),
        "observation_low_info_observation_rate": observation_scorecard_blind_qa_fields.get("low_info_observation_rate"),
        "observation_false_eligible_rate": observation_scorecard_blind_qa_fields.get("false_eligible_rate"),
        "observation_free_user_fact_violation_count": observation_scorecard_blind_qa_fields.get("free_user_fact_violation_count"),
        "observation_overclaim_count": observation_scorecard_blind_qa_fields.get("overclaim_count"),
        "observation_template_skeleton_repeat_rate": observation_scorecard_blind_qa_fields.get("template_skeleton_repeat_rate"),
        "observation_read_feeling_score": observation_scorecard_blind_qa_fields.get("observation_read_feeling_score"),
        "observation_machine_metrics_used_for_read_feeling": False,
        "observation_release_blockers": list(observation_scorecard_blind_qa_fields.get("observation_scorecard_blockers") or []),
        "observation_regression_fixture_coverage_version": OBSERVATION_REGRESSION_FIXTURE_COVERAGE_VERSION,
        "observation_regression_fixture_coverage_step": OBSERVATION_REGRESSION_FIXTURE_COVERAGE_STEP,
        "step13_observation_regression_fixture_coverage_requested": observation_regression_fixture_requested,
        "step13_observation_regression_fixture_coverage_ready": bool(observation_regression_fixture_coverage.get("step13_regression_fixture_coverage_ready")),
        "observation_regression_fixture_coverage_ready": bool(observation_regression_fixture_coverage.get("observation_regression_fixture_coverage_ready")),
        "step13_observation_regression_fixture_coverage": observation_regression_fixture_coverage,
        "step13_observation_regression_fixture_fields": observation_regression_fixture_fields,
        "observation_regression_required_fixture_group_count": observation_regression_fixture_fields.get("observation_regression_required_fixture_group_count"),
        "observation_regression_observed_required_fixture_group_count": observation_regression_fixture_fields.get("observation_regression_observed_required_fixture_group_count"),
        "observation_regression_missing_fixture_groups": list(observation_regression_fixture_fields.get("observation_regression_missing_fixture_groups") or []),
        "observation_regression_fixture_failure_count": observation_regression_fixture_fields.get("observation_regression_fixture_failure_count"),
        "observation_regression_fixture_coverage_rate": observation_regression_fixture_fields.get("observation_regression_fixture_coverage_rate"),
        "observation_regression_fixture_pass_rate": observation_regression_fixture_fields.get("observation_regression_fixture_pass_rate"),
        "observation_regression_fixture_release_blockers": list(observation_regression_fixture_fields.get("observation_regression_fixture_release_blockers") or []),
        "observation_exit_gate_handoff_version": OBSERVATION_EXIT_GATE_HANDOFF_VERSION,
        "observation_exit_gate_handoff_step": OBSERVATION_EXIT_GATE_HANDOFF_STEP,
        "step14_observation_exit_gate_handoff": observation_exit_gate_handoff,
        "observation_exit_gate_handoff": observation_exit_gate_handoff,
        "step14_observation_exit_gate_handoff_fields": observation_exit_gate_handoff_fields,
        "observation_exit_gate_handoff_ready": bool(
            observation_exit_gate_handoff_fields.get("observation_exit_gate_handoff_ready")
        ),
        "step14_observation_exit_gate_handoff_ready": bool(
            observation_exit_gate_handoff_fields.get("step14_observation_exit_gate_handoff_ready")
        ),
        "observation_exit_gate_release_blockers": list(
            observation_exit_gate_handoff_fields.get("observation_exit_gate_release_blockers") or []
        ),
        "observation_exit_gate_rollback_required": bool(
            observation_exit_gate_handoff_fields.get("observation_exit_gate_rollback_required")
        ),
        "observation_exit_gate_rollback_triggered_conditions": list(
            observation_exit_gate_handoff_fields.get("observation_exit_gate_rollback_triggered_conditions") or []
        ),
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
        "coverage_group_aggregation_ready": bool(machine.get("coverage_group_aggregation_ready")),
        "required_coverage_groups": list(COMPLETE_COVERAGE_GROUP_ORDER),
        "observed_coverage_groups": list(machine.get("observed_coverage_groups") or []),
        "missing_coverage_groups": missing_coverage_groups,
        "coverage_group_count": int(machine.get("coverage_group_count") or 0),
        "coverage_group_missing_count": coverage_group_missing_count,
        "coverage_group_missing_blocker": coverage_group_missing_count > 0,
        "threshold_checks": threshold_checks,
        "targets": {
            "version": COMPLETE_PRODUCT_QUALITY_TARGETS_VERSION,
            "connection_display_target": COMPLETE_PRODUCT_QUALITY_CONNECTION_DISPLAY_TARGET,
            "product_gate_display_target": COMPLETE_PRODUCT_GATE_DISPLAY_TARGET,
            "binding_pass_rate": COMPLETE_PRODUCT_QUALITY_BINDING_TARGET,
            "connection_read_feeling_target": COMPLETE_PRODUCT_QUALITY_READ_FEELING_INITIAL_TARGET,
            "product_gate_read_feeling_target": COMPLETE_PRODUCT_QUALITY_READ_FEELING_PRODUCT_TARGET,
            "reason_coverage_rate": COMPLETE_PRODUCT_QUALITY_REASON_COVERAGE_TARGET,
            "required_coverage_groups": list(COMPLETE_COVERAGE_GROUP_ORDER),
            "coverage_group_missing_count": 0,
            "coverage_runtime_baseline_required": True,
            "coverage_runtime_baseline_groups_complete": True,
            "template_major_count": 0,
            "surface_template_major_count": 0,
            "safety_major_count": 0,
            "surface_signature_repeat_rate": 0.0,
            "connector_repetition_rate": 0.0,
            "grammar_warning_rate": 0.0,
        },
        "release_blockers": _dedupe(release_blockers),
        "product_gate_thresholds_met": product_gate_thresholds_met,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "product_gate_public_release_applied": False,
        "public_release_applied": False,
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
    "COMPLETE_PRODUCT_QUALITY_SURFACE_METRICS_VERSION",
    "COMPLETE_PRODUCT_QUALITY_SURFACE_METRICS_STEP",
    "COMPLETE_PRODUCT_QUALITY_COVERAGE_RUNTIME_BASELINE_VERSION",
    "COMPLETE_PRODUCT_QUALITY_COVERAGE_RUNTIME_BASELINE_STEP",
    "COMPLETE_PRODUCT_QUALITY_RUNTIME_SURFACE_BLIND_QA_LONG_RUN_VERSION",
    "COMPLETE_PRODUCT_QUALITY_RUNTIME_SURFACE_BLIND_QA_LONG_RUN_STEP",
    "COMPLETE_PRODUCT_QUALITY_PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_VERSION",
    "COMPLETE_PRODUCT_QUALITY_PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_STEP",
    "PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_VERSION",
    "PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_STEP",
    "PRODUCT_READFEEL_CURRENT_OUTPUT_INVENTORY_VERSION",
    "PRODUCT_READFEEL_CURRENT_OUTPUT_INVENTORY_STEP",
    "PRODUCT_READFEEL_RUBRIC_VERSION",
    "PRODUCT_READFEEL_RUBRIC_STEP",
    "PRODUCT_READFEEL_SCORECARD_VERSION",
    "PRODUCT_READFEEL_SCORECARD_STEP",
    "OBSERVATION_SCORECARD_BLIND_QA_VERSION",
    "OBSERVATION_SCORECARD_BLIND_QA_STEP",
    "OBSERVATION_EXIT_GATE_HANDOFF_VERSION",
    "OBSERVATION_EXIT_GATE_HANDOFF_STEP",
    "build_complete_product_quality_scorecard_event_schema",
    "build_complete_product_quality_blind_qa_rubric",
    "normalize_complete_product_quality_blind_qa_review",
    "aggregate_complete_product_quality_blind_qa_reviews",
    "build_complete_product_quality_blind_qa_aggregate",
    "build_complete_product_quality_scorecard",
    "build_complete_product_quality_scorecard_report",
    "build_complete_product_quality_scorecard_event_schema",
]
