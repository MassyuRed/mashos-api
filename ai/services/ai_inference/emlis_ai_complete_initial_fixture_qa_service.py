# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step9 fixture / QA run meta for Complete Composer initial E2E opening.

This module is intentionally meta-only.  It aggregates sanitized Complete
Composer scorecard events against the structural fixture suite so the next
product-quality scorecard work has visible display / binding / Gate / template
metrics without exposing raw input text, writing ``comment_text``, or changing
public response shape.
"""

from collections import Counter
from typing import Any, Iterable, Mapping, Sequence

from emlis_ai_complete_scorecard_service import (
    COMPLETE_BINDING_TARGET_RATE,
    COMPLETE_COVERAGE_GROUP_ORDER,
    COMPLETE_INITIAL_DISPLAY_TARGET_MAX,
    COMPLETE_INITIAL_DISPLAY_TARGET_MIN,
    COMPLETE_PRODUCT_GATE_DISPLAY_TARGET,
    COMPLETE_READ_FEELING_INITIAL_TARGET,
    COMPLETE_READ_FEELING_PRODUCT_TARGET,
    aggregate_complete_scorecard_events,
    build_complete_initial_fixture_suite,
    build_complete_scorecard_contract_meta,
    normalize_complete_scorecard_event,
)

COMPLETE_INITIAL_STEP9_FIXTURE_QA_RUN_VERSION = "emlis.complete_initial.step9.fixture_qa_run.v1"
COMPLETE_INITIAL_STEP9_PRODUCT_SCORECARD_SEED_VERSION = "emlis.complete_initial.step9.product_scorecard_seed.v1"
COMPLETE_INITIAL_STEP9_FIXTURE_QA_STEP = "Step9_fixture_QA_run"
# Compatibility alias used by the E2E Step9 implementation docs/tests.
COMPLETE_INITIAL_FIXTURE_QA_RUN_VERSION = COMPLETE_INITIAL_STEP9_FIXTURE_QA_RUN_VERSION

_TEXT_PAYLOAD_KEYS = {
    "raw_text",
    "raw_input",
    "input_text",
    "user_input",
    "current_input",
    "memo",
    "memo_text",
    "memo_action",
    "raw_user_text",
    "original_text",
    "source_text",
    "material_text",
    "surface_text",
    "realized_text",
    "comment_text",
    "text",
    "phrase",
    "sentence",
    "sentences",
    "line_text",
    "body",
    "reply_text",
    "summary_of_output",
}

_REASON_KEYS = (
    "top_rejection_reasons",
    "gate_rejection_reasons",
    "rejection_reasons",
    "release_blockers",
    "return_steps",
    "unmet_checks",
)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value if value is not None else default)
    except (TypeError, ValueError):
        return int(default)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value if value is not None else default)
    except (TypeError, ValueError):
        return float(default)


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    if values is None:
        return []
    if isinstance(values, (str, bytes)):
        source: Iterable[Any] = [values]
    elif isinstance(values, Iterable):
        source = values
    else:
        source = [values]
    out: list[str] = []
    seen: set[str] = set()
    for value in source:
        item = _clean(value)
        if item and item not in seen:
            out.append(item)
            seen.add(item)
    return out


def _safe_json(value: Any, *, depth: int = 0) -> Any:
    if depth > 8:
        return None
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            key_text = _clean(key)
            if not key_text or key_text in _TEXT_PAYLOAD_KEYS:
                continue
            safe_item = _safe_json(item, depth=depth + 1)
            if safe_item is not None:
                out[key_text] = safe_item
        return out
    if isinstance(value, (list, tuple, set)):
        return [item for item in (_safe_json(row, depth=depth + 1) for row in value) if item is not None]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _safe_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    safe = _safe_json(value)
    return safe if isinstance(safe, dict) else {}


def _source_event(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    for key in ("scorecard_event", "complete_scorecard_event", "normalized_event", "event"):
        nested = value.get(key)
        if isinstance(nested, Mapping):
            return nested
    return value


def _collect_events(
    *,
    scorecard_event: Mapping[str, Any] | None = None,
    scorecard_harness: Mapping[str, Any] | None = None,
    scorecard_events: Sequence[Any] | Iterable[Any] | None = None,
    records: Sequence[Any] | Iterable[Any] | None = None,
    diagnostic_summary: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    raw_events: list[Any] = []
    if isinstance(scorecard_event, Mapping) and scorecard_event:
        raw_events.append(scorecard_event)
    if isinstance(scorecard_harness, Mapping):
        harness_event = scorecard_harness.get("normalized_event") or scorecard_harness.get("event")
        if isinstance(harness_event, Mapping) and harness_event and not raw_events:
            raw_events.append(harness_event)
    raw_events.extend(list(scorecard_events or []))
    raw_events.extend(list(records or []))
    if not raw_events and isinstance(diagnostic_summary, Mapping):
        for key in (
            "complete_initial_final_scorecard_event",
            "complete_scorecard_event",
            "complete_composer_scorecard_event",
            "scorecard_event",
        ):
            item = diagnostic_summary.get(key)
            if isinstance(item, Mapping) and item:
                raw_events.append(item)
                break
    normalized: list[dict[str, Any]] = []
    for event in raw_events:
        source = _source_event(event)
        if not isinstance(source, Mapping) or not source:
            continue
        normalized_event = normalize_complete_scorecard_event(_safe_mapping(source))
        normalized_event["raw_input_included"] = False
        normalized_event["raw_text_included"] = False
        normalized_event["comment_text_included"] = False
        normalized.append(normalized_event)
    return normalized


def _event_reasons(event: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    for key in _REASON_KEYS:
        reasons.extend(_dedupe(event.get(key)))
    for key in ("primary_reason", "gate_primary_reason", "observation_status"):
        reasons.extend(_dedupe(event.get(key)))
    return _dedupe(reasons)


def _build_gate_reason_summary(events: Sequence[Mapping[str, Any]], aggregate: Mapping[str, Any]) -> dict[str, Any]:
    counter: Counter[str] = Counter()
    by_group: dict[str, Counter[str]] = {}
    for event in events:
        group = _clean(event.get("coverage_group")) or "short_daily"
        group_counter = by_group.setdefault(group, Counter())
        for reason in _event_reasons(event):
            counter[reason] += 1
            group_counter[reason] += 1
    top_reasons = [reason for reason, _count in counter.most_common(8)]
    if not top_reasons:
        top_reasons = _dedupe(aggregate.get("release_blockers"))
    return {
        "version": "emlis.complete_initial.step9.gate_reason_summary.v1",
        "ready": bool(events),
        "reason_count": sum(counter.values()),
        "top_rejection_reasons": top_reasons,
        "top_gate_reasons": top_reasons,
        "by_reason": {reason: count for reason, count in counter.most_common()},
        "by_coverage_group": {
            group: {reason: count for reason, count in row.most_common()}
            for group, row in sorted(by_group.items())
        },
        "raw_input_required": False,
        "raw_input_included": False,
        "comment_text_included": False,
    }


def build_complete_initial_step9_fixture_qa_run(
    *,
    scorecard_event: Mapping[str, Any] | None = None,
    scorecard_harness: Mapping[str, Any] | None = None,
    scorecard_events: Sequence[Any] | Iterable[Any] | None = None,
    records: Sequence[Any] | Iterable[Any] | None = None,
    fixture_suite: Mapping[str, Any] | None = None,
    diagnostic_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the Step9 fixture / QA run meta for Complete Composer initial.

    ``scorecard_events`` and ``records`` are expected to be sanitized scorecard
    event dictionaries, not raw fixture inputs.  The returned payload is safe to
    attach to diagnostic_summary and multi_perspective meta.
    """

    harness = dict(scorecard_harness or {}) if isinstance(scorecard_harness, Mapping) else {}
    suite_source = fixture_suite or harness.get("fixture_suite") or build_complete_initial_fixture_suite()
    suite = _safe_mapping(suite_source if isinstance(suite_source, Mapping) else build_complete_initial_fixture_suite())
    if not suite:
        suite = build_complete_initial_fixture_suite()
    events = _collect_events(
        scorecard_event=scorecard_event,
        scorecard_harness=harness,
        scorecard_events=scorecard_events,
        records=records,
        diagnostic_summary=diagnostic_summary,
    )
    aggregate = aggregate_complete_scorecard_events(events, fixture_suite=suite)
    gate_reason_summary = _build_gate_reason_summary(events, aggregate)

    event_count = _safe_int(aggregate.get("record_count") or aggregate.get("event_count"), len(events))
    display_reach_rate = _safe_float(aggregate.get("display_reach_rate"), 0.0)
    binding_pass_rate = _safe_float(aggregate.get("binding_pass_rate"), 0.0)
    read_feeling_pass_rate = _safe_float(aggregate.get("read_feeling_pass_rate"), 0.0)
    safety_major_count = _safe_int(aggregate.get("safety_major_count"), 0)
    template_major_count = _safe_int(aggregate.get("template_major_count"), 0)
    fixture_suite_ready = bool(suite.get("fixture_suite_ready") or suite.get("ready"))
    release_blockers = _dedupe(aggregate.get("release_blockers"))
    groups_needing_attention = _dedupe(aggregate.get("groups_needing_attention"))
    missing_fixture_groups = _dedupe(aggregate.get("missing_fixture_groups"))
    groups_with_events = _dedupe(aggregate.get("groups_with_events"))
    fixture_coverage_complete = bool(event_count and not missing_fixture_groups)
    fixture_coverage_rate = _safe_float(aggregate.get("fixture_coverage_rate"), 0.0)
    read_feeling_evaluated_count = _safe_int(aggregate.get("read_feeling_evaluated_count"), 0)
    gate_reason_counts = dict(gate_reason_summary.get("by_reason") or {})
    major_quality_clear = bool(template_major_count == 0 and safety_major_count == 0)
    scorecard_input_ready = bool(event_count)
    product_scorecard_quality_ready = bool(
        event_count
        and fixture_suite_ready
        and fixture_coverage_complete
        and major_quality_clear
        and not release_blockers
    )

    product_scorecard_seed = {
        "version": COMPLETE_INITIAL_STEP9_PRODUCT_SCORECARD_SEED_VERSION,
        "source_step": COMPLETE_INITIAL_STEP9_FIXTURE_QA_STEP,
        "ready": scorecard_input_ready,
        "meta_only": True,
        "can_feed_complete_composer_product_scorecard": scorecard_input_ready,
        "quality_ready": product_scorecard_quality_ready,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "product_gate_evaluation": "not_product_gate_initial_version",
        "event_count": event_count,
        "fixture_count": _safe_int(suite.get("fixture_count"), 0),
        "display_reach_rate": display_reach_rate,
        "initial_display_target_range": [COMPLETE_INITIAL_DISPLAY_TARGET_MIN, COMPLETE_INITIAL_DISPLAY_TARGET_MAX],
        "product_gate_display_target": COMPLETE_PRODUCT_GATE_DISPLAY_TARGET,
        "binding_pass_rate": binding_pass_rate,
        "binding_target_rate": COMPLETE_BINDING_TARGET_RATE,
        "read_feeling_pass_rate": read_feeling_pass_rate,
        "read_feeling_initial_target": COMPLETE_READ_FEELING_INITIAL_TARGET,
        "read_feeling_product_target": COMPLETE_READ_FEELING_PRODUCT_TARGET,
        "read_feeling_requires_blind_qa": True,
        "safety_major_count": safety_major_count,
        "template_major_count": template_major_count,
        "non_template_major_clear": template_major_count == 0,
        "safety_major_clear": safety_major_count == 0,
        "gate_reason_summary_ready": bool(gate_reason_summary.get("ready")),
        "top_rejection_reasons": list(gate_reason_summary.get("top_rejection_reasons") or []),
        "groups_needing_attention": groups_needing_attention,
        "missing_fixture_groups": missing_fixture_groups,
        "release_blockers": release_blockers,
        "next_step": "complete_composer_product_quality_scorecard_data_expansion",
        "raw_input_required_for_improvement": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "display_gate_relaxed": False,
        "input_specific_template_added": False,
        "fixed_completed_sentence_template_added": False,
    }

    contract = build_complete_scorecard_contract_meta()
    return {
        **contract,
        "version": COMPLETE_INITIAL_STEP9_FIXTURE_QA_RUN_VERSION,
        "target_step": COMPLETE_INITIAL_STEP9_FIXTURE_QA_STEP,
        "step": COMPLETE_INITIAL_STEP9_FIXTURE_QA_STEP,
        "implementation_unit": "CompleteComposerInitialE2E.Step9",
        "phase": "complete_composer_initial_e2e_opening",
        "purpose": "fixture_qa_run_display_binding_gate_reason_non_template_metrics_for_product_scorecard",
        "ready": bool(event_count),
        "fixture_qa_run_ready": bool(event_count),
        "fixture_qa_data_ready": bool(event_count),
        "qa_run_ready": bool(event_count),
        "scorecard_input_ready": scorecard_input_ready,
        "product_scorecard_input_ready": scorecard_input_ready,
        "product_scorecard_quality_ready": product_scorecard_quality_ready,
        "ready_for_product_scorecard": scorecard_input_ready,
        "fixture_coverage_complete": fixture_coverage_complete,
        "fixture_coverage_rate": fixture_coverage_rate,
        "meta_only": True,
        "additive": True,
        "built_after_step8_rn_contract_regression": True,
        "public_comment_text_written_by_step9": False,
        "comment_text_written_by_step9": False,
        "comment_text_generated_by_step9": False,
        "comment_text_key_written": False,
        "comment_text_contract": "passed_only",
        "passed_only_contract_preserved": True,
        "fixture_suite": suite,
        "fixture_suite_ready": fixture_suite_ready,
        "fixture_count": _safe_int(suite.get("fixture_count"), 0),
        "fixture_counts_by_group": dict(suite.get("fixture_counts_by_group") or {}),
        "coverage_groups": list(COMPLETE_COVERAGE_GROUP_ORDER),
        "scorecard_events": events,
        "event_count": event_count,
        "eligible_fixture_event_count": _safe_int((aggregate.get("totals") or {}).get("eligible_count"), 0),
        "candidate_generated_count": _safe_int((aggregate.get("totals") or {}).get("candidate_generated_count"), 0),
        "passed_display_count": _safe_int((aggregate.get("totals") or {}).get("passed_display_count"), 0),
        "display_reach_rate": display_reach_rate,
        "candidate_generation_rate": _safe_float(aggregate.get("candidate_generation_rate"), 0.0),
        "binding_pass_rate": binding_pass_rate,
        "read_feeling_pass_rate": read_feeling_pass_rate,
        "read_feeling_requires_blind_qa": True,
        "safety_major_count": safety_major_count,
        "template_major_count": template_major_count,
        "non_template_major_clear": template_major_count == 0,
        "safety_major_clear": safety_major_count == 0,
        "aggregate": _safe_mapping(aggregate),
        "by_coverage_group": _safe_mapping(aggregate.get("by_coverage_group") if isinstance(aggregate, Mapping) else {}),
        "coverage_group_rows": _safe_json(aggregate.get("coverage_group_rows") if isinstance(aggregate, Mapping) else []) or [],
        "groups_needing_attention": groups_needing_attention,
        "groups_with_events": groups_with_events,
        "missing_fixture_groups": missing_fixture_groups,
        "fixture_coverage_complete": fixture_coverage_complete,
        "fixture_coverage_rate": fixture_coverage_rate,
        "read_feeling_evaluated_count": read_feeling_evaluated_count,
        "gate_reason_counts": gate_reason_counts,
        "gate_reason_summary": gate_reason_summary,
        "top_rejection_reasons": list(gate_reason_summary.get("top_rejection_reasons") or []),
        "top_gate_reasons": list(gate_reason_summary.get("top_gate_reasons") or gate_reason_summary.get("top_rejection_reasons") or []),
        "release_blockers": release_blockers,
        "product_scorecard_seed": product_scorecard_seed,
        "product_scorecard_data_ready": bool(event_count),
        "product_scorecard_input_ready": scorecard_input_ready,
        "product_scorecard_quality_ready": product_scorecard_quality_ready,
        "ready_for_product_scorecard": scorecard_input_ready,
        "ready_for_complete_product_scorecard_data_expansion": scorecard_input_ready,
        "product_gate_evaluation": "not_product_gate_initial_version",
        "ready_for_product_gate": False,
        "product_gate_ready": False,
        "complete_product_gate_ready": False,
        "product_gate_reached": False,
        "raw_input_required_for_improvement": False,
        "raw_input_required": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "fallback_used": False,
        "fixed_fallback_used": False,
        "input_specific_template_added": False,
        "fixed_completed_sentence_template_added": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
    }


build_complete_initial_fixture_qa_run = build_complete_initial_step9_fixture_qa_run
build_step9_complete_initial_fixture_qa_run = build_complete_initial_step9_fixture_qa_run


__all__ = [
    "COMPLETE_INITIAL_STEP9_FIXTURE_QA_RUN_VERSION",
    "COMPLETE_INITIAL_FIXTURE_QA_RUN_VERSION",
    "COMPLETE_INITIAL_STEP9_PRODUCT_SCORECARD_SEED_VERSION",
    "COMPLETE_INITIAL_STEP9_FIXTURE_QA_STEP",
    "build_complete_initial_fixture_qa_run",
    "build_complete_initial_step9_fixture_qa_run",
    "build_step9_complete_initial_fixture_qa_run",
]
