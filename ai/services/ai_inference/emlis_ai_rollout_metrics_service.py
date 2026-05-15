# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step16 rollout metrics for EmlisAI B-R1.

Developer / internal-QA meta only.  This module converts release gate meta and
``diagnostic_summary`` into measurable rollout records for A-P0 judgement.  It
never changes user-facing text, public routes, response keys, or DB names.
"""

from collections import Counter
from typing import Any, Dict, Iterable, List, Mapping, Sequence

STEP16_PHASE = "B-R1"
STEP16_STEP = "Step16_rollout_metrics"
STEP16_ROLLOUT_METRICS_VERSION = "emlis.step16_rollout_metrics.v1"
STEP16_ROLLOUT_METRIC_EVENT_VERSION = "emlis.step16_rollout_metrics_event.v1"
STEP16_ROLLOUT_METRICS_AGGREGATE_VERSION = "emlis.step16_rollout_metrics_aggregate.v1"
STEP16_ROLLOUT_SUMMARY_VERSION = STEP16_ROLLOUT_METRICS_AGGREGATE_VERSION

OBSERVATION_STATUSES = ("passed", "rejected", "unavailable", "safety_blocked")
ROLLOUT_STAGES = ("off", "internal", "tutorial", "limited_cases", "all")
STEP16_REQUIRED_EVENT_FIELDS = (
    "attempted",
    "passed",
    "rejected",
    "unavailable",
    "safety_blocked",
    "primary_reason",
    "coverage_group",
    "composer_model",
)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _mapping(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _dedupe(values: Iterable[Any]) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for value in values:
        item = _clean(value)
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return _dedupe(value)
    return _dedupe([value])


def _counter_dict(counter: Counter[str]) -> Dict[str, int]:
    return {key: int(counter[key]) for key in sorted(counter) if key}


def _nested(source: Mapping[str, Any], key: str) -> Dict[str, Any]:
    value = source.get(key)
    return dict(value) if isinstance(value, Mapping) else {}


def _status(value: Any) -> str:
    status = _clean(value)
    return status if status in OBSERVATION_STATUSES else "unavailable"


def _status_counts(status: str) -> Dict[str, int]:
    return {key: 1 if status == key else 0 for key in OBSERVATION_STATUSES}


def _release_decision(release: Mapping[str, Any]) -> Dict[str, Any]:
    return _nested(release, "rollout_decision") or _nested(release, "release_decision")


def _coverage_matrix(summary: Mapping[str, Any]) -> Dict[str, Any]:
    return _nested(summary, "coverage_matrix")


def _coverage_groups(summary: Mapping[str, Any]) -> List[str]:
    matrix = _coverage_matrix(summary)
    groups = _list(summary.get("coverage_groups")) or _list(matrix.get("coverage_groups")) or _list(matrix.get("active_groups"))
    primary = _clean(summary.get("coverage_primary_group")) or _clean(matrix.get("primary_coverage_group"))
    if primary and primary not in groups:
        groups.insert(0, primary)
    return groups or ["unclassified"]


def _coverage_group(summary: Mapping[str, Any]) -> str:
    matrix = _coverage_matrix(summary)
    return (
        _clean(summary.get("coverage_primary_group"))
        or _clean(matrix.get("primary_coverage_group"))
        or (_coverage_groups(summary)[0] if _coverage_groups(summary) else "unclassified")
    )


def _unclassified_reasons(summary: Mapping[str, Any]) -> List[str]:
    matrix = _coverage_matrix(summary)
    return _dedupe([
        *_list(summary.get("coverage_unclassified_reasons")),
        *_list(summary.get("coverage_unmapped_reasons")),
        *_list(matrix.get("unclassified_reasons")),
        *_list(matrix.get("unmapped_reason_codes")),
    ])


def _stage(summary: Mapping[str, Any], release: Mapping[str, Any], phase7: Mapping[str, Any]) -> str:
    decision = _release_decision(release)
    return (
        _clean(summary.get("rollout_stage"))
        or _clean(release.get("stage"))
        or _clean(decision.get("stage"))
        or _clean(phase7.get("stage"))
        or "limited_cases"
    )


def _attempted(summary: Mapping[str, Any], release: Mapping[str, Any], phase7: Mapping[str, Any]) -> bool:
    decision = _release_decision(release)
    return bool(
        summary.get("rollout_attempted")
        or summary.get("composer_connection_attempted")
        or phase7.get("attempted")
        or release.get("attempted")
        or release.get("enabled")
        or decision.get("attempted")
        or decision.get("enabled")
    )


def _cohort(summary: Mapping[str, Any], release: Mapping[str, Any], phase7: Mapping[str, Any], attempted: bool) -> str:
    decision = _release_decision(release)
    return (
        _clean(summary.get("release_cohort"))
        or _clean(release.get("cohort"))
        or _clean(decision.get("cohort"))
        or _clean(phase7.get("cohort"))
        or ("attempted" if attempted else "blocked")
    )


def _primary_reason(summary: Mapping[str, Any], release: Mapping[str, Any], phase7: Mapping[str, Any], status: str) -> str:
    decision = _release_decision(release)
    values: List[Any] = [
        summary.get("primary_reason"),
        phase7.get("primary_reason"),
        release.get("reason_code"),
        decision.get("reason_code"),
    ]
    values.extend(_list(phase7.get("rejection_reasons")))
    values.extend(_list(summary.get("secondary_reasons")))
    for value in values:
        reason = _clean(value)
        if reason:
            return reason
    return status or "unavailable"


def _reason_codes(summary: Mapping[str, Any], release: Mapping[str, Any], phase7: Mapping[str, Any], primary_reason: str) -> List[str]:
    decision = _release_decision(release)
    values: List[Any] = [primary_reason]
    for key in (
        "secondary_reasons",
        "scope_rejection_reasons",
        "scope_safety_boundaries",
        "scope_excluded_reason_codes",
        "composer_rejection_reasons",
        "gate_rejection_reasons",
        "coverage_unclassified_reasons",
        "coverage_unmapped_reasons",
    ):
        values.extend(_list(summary.get(key)))
    values.extend(_list(release.get("rejection_reasons")))
    values.extend(_list(decision.get("rejection_reasons")))
    values.extend(_list(phase7.get("rejection_reasons")))
    return _dedupe(values)


def build_emlis_rollout_metric_event(
    *,
    diagnostic_summary: Mapping[str, Any] | None,
    release_meta: Mapping[str, Any] | None = None,
    phase7_rollout_metrics: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build one normalized Step16 metric event."""

    summary = _mapping(diagnostic_summary)
    release = _mapping(release_meta)
    phase7 = _mapping(phase7_rollout_metrics)
    status = _status(summary.get("observation_status") or phase7.get("observation_status"))
    attempted = _attempted(summary, release, phase7)
    primary_reason = _primary_reason(summary, release, phase7, status)
    reason_codes = _reason_codes(summary, release, phase7, primary_reason)
    coverage_group = _coverage_group(summary)
    coverage_groups = _coverage_groups(summary)
    composer_model = _clean(summary.get("composer_model") or phase7.get("composer_model")) or "not_connected"
    composer_status = _clean(summary.get("composer_status")) or ("not_attempted" if not attempted else "unknown")
    stage = _stage(summary, release, phase7)
    cohort = _cohort(summary, release, phase7, attempted)
    unclassified = _unclassified_reasons(summary)
    passed_rate_denominator = 1 if attempted else 0
    passed_rate_numerator = 1 if attempted and status == "passed" else 0
    metric_complete = bool(stage and status and primary_reason and coverage_group and composer_model)

    return {
        "version": STEP16_ROLLOUT_METRIC_EVENT_VERSION,
        "phase": STEP16_PHASE,
        "step": STEP16_STEP,
        "purpose": "staged_release_measurement_for_ap0_judgement",
        "ready": metric_complete,
        "metric_complete": metric_complete,
        "aggregation_ready": True,
        "record_count": 1,
        "metric_fields": list(STEP16_REQUIRED_EVENT_FIELDS),
        "stage": stage,
        "rollout_stage": stage,
        "cohort": cohort,
        "release_enabled": bool(release.get("enabled")),
        "release_reason_code": _clean(release.get("reason_code")),
        "attempted": attempted,
        "attempted_count": 1 if attempted else 0,
        "not_attempted_count": 0 if attempted else 1,
        "blocked_before_attempt": not attempted,
        "blocked_before_attempt_count": 0 if attempted else 1,
        "observation_status": status,
        "passed": attempted and status == "passed",
        "rejected": attempted and status == "rejected",
        "unavailable": status == "unavailable",
        "safety_blocked": status == "safety_blocked",
        "passed_count": 1 if attempted and status == "passed" else 0,
        "rejected_count": 1 if attempted and status == "rejected" else 0,
        "unavailable_count": 1 if status == "unavailable" else 0,
        "safety_blocked_count": 1 if status == "safety_blocked" else 0,
        "status_counts": _status_counts(status),
        "status_denominator": 1,
        "passed_rate_numerator": passed_rate_numerator,
        "passed_rate_denominator": passed_rate_denominator,
        "passed_rate": (passed_rate_numerator / passed_rate_denominator) if passed_rate_denominator else 0.0,
        "primary_reason": primary_reason,
        "primary_reason_counts": {primary_reason: 1} if primary_reason else {},
        "reason_codes": reason_codes,
        "reason_counts": {reason: 1 for reason in reason_codes},
        "secondary_reasons": _list(summary.get("secondary_reasons")),
        "rejection_reasons": [reason for reason in reason_codes if reason != "passed"],
        "rejection_reason_counts": {reason: 1 for reason in reason_codes if reason != "passed"},
        "coverage_group": coverage_group,
        "coverage_primary_group": coverage_group,
        "coverage_groups": coverage_groups,
        "coverage_group_counts": {group: 1 for group in coverage_groups},
        "coverage_scope": _clean(summary.get("coverage_scope") or release.get("scope_coverage")),
        "coverage_next_steps": _dedupe([*_list(summary.get("coverage_next_steps")), *_list(_coverage_matrix(summary).get("next_steps"))]),
        "coverage_unclassified_reasons": unclassified,
        "coverage_unmapped_reasons": _list(summary.get("coverage_unmapped_reasons")) or _list(_coverage_matrix(summary).get("unmapped_reason_codes")),
        "coverage_unclassified_reason_count": len(unclassified),
        "unclassified_reasons": unclassified,
        "unclassified_reason_count": len(unclassified),
        "scope_status": _clean(summary.get("scope_status") or release.get("scope_status")),
        "composer_model": composer_model,
        "composer_model_counts": {composer_model: 1},
        "composer_status": composer_status,
        "comment_text_allowed": bool(summary.get("comment_text_allowed")),
        "feature_flag_enabled": bool(summary.get("feature_flag_enabled") or release.get("feature_flag_enabled")),
        "diagnostic_stage": _clean(summary.get("stage")),
        "diagnostic_summary_version": _clean(summary.get("version")),
        "release_gate_version": _clean(release.get("version")),
        "phase7_metric_version": _clean(phase7.get("version")),
        "aggregation_key": ":".join([stage, cohort, status, coverage_group, composer_model, primary_reason]),
        "aggregation_dimensions": {
            "rollout_stage": stage,
            "cohort": cohort,
            "observation_status": status,
            "primary_reason": primary_reason,
            "coverage_group": coverage_group,
            "composer_model": composer_model,
        },
        "a_p0_decision_material": {
            "stage": stage,
            "attempted": attempted,
            "observation_status": status,
            "primary_reason": primary_reason,
            "coverage_group": coverage_group,
            "composer_model": composer_model,
            "unclassified_reason_count": len(unclassified),
        },
    }


def build_emlis_rollout_metrics_event(**kwargs: Any) -> Dict[str, Any]:
    """Backward-compatible plural alias."""
    return build_emlis_rollout_metric_event(**kwargs)


def _normalize_event(value: Any) -> Dict[str, Any]:
    event = _mapping(value)
    if _clean(event.get("version")) in {STEP16_ROLLOUT_METRIC_EVENT_VERSION, STEP16_ROLLOUT_METRICS_VERSION}:
        nested_event = event.get("metric_event") or event.get("rollout_metric_event")
        if isinstance(nested_event, Mapping):
            return dict(nested_event)
        return dict(event)
    summary = event.get("diagnostic_summary") if isinstance(event.get("diagnostic_summary"), Mapping) else event
    release = event.get("release_meta") if isinstance(event.get("release_meta"), Mapping) else event.get("limited_composer_release")
    phase7 = event.get("phase7_rollout_metrics") if isinstance(event.get("phase7_rollout_metrics"), Mapping) else {}
    return build_emlis_rollout_metric_event(
        diagnostic_summary=summary if isinstance(summary, Mapping) else {},
        release_meta=release if isinstance(release, Mapping) else {},
        phase7_rollout_metrics=phase7 if isinstance(phase7, Mapping) else {},
    )


def _bucket() -> Dict[str, Any]:
    return {
        "total": 0,
        "attempted": 0,
        "attempted_count": 0,
        "not_attempted": 0,
        "blocked_before_attempt_count": 0,
        "passed": 0,
        "passed_count": 0,
        "rejected": 0,
        "rejected_count": 0,
        "unavailable": 0,
        "unavailable_count": 0,
        "safety_blocked": 0,
        "safety_blocked_count": 0,
        "passed_rate_numerator": 0,
        "passed_rate_denominator": 0,
        "passed_rate": 0.0,
        "primary_reason_counts": {},
        "reason_counts": {},
        "rejection_reason_counts": {},
        "coverage_group_counts": {},
        "composer_model_counts": {},
        "unclassified_reason_count": 0,
    }


def _merge_counts(bucket: Dict[str, Any], event: Mapping[str, Any]) -> None:
    bucket["total"] += 1
    attempted = int(event.get("attempted_count") or (1 if event.get("attempted") else 0))
    not_attempted = int(event.get("not_attempted_count") or event.get("blocked_before_attempt_count") or (0 if event.get("attempted") else 1))
    bucket["attempted"] += attempted
    bucket["attempted_count"] += attempted
    bucket["not_attempted"] += not_attempted
    bucket["blocked_before_attempt_count"] += not_attempted
    status_counts = event.get("status_counts") if isinstance(event.get("status_counts"), Mapping) else {}
    for status in OBSERVATION_STATUSES:
        count = int(status_counts.get(status) or (1 if event.get("observation_status") == status else 0))
        bucket[status] += count
        bucket[f"{status}_count"] += count
    bucket["passed_rate_numerator"] += int(event.get("passed_rate_numerator") or 0)
    bucket["passed_rate_denominator"] += int(event.get("passed_rate_denominator") or 0)
    bucket["unclassified_reason_count"] += int(event.get("unclassified_reason_count") or event.get("coverage_unclassified_reason_count") or 0)
    for field in ("primary_reason_counts", "reason_counts", "rejection_reason_counts", "coverage_group_counts", "composer_model_counts"):
        merged = Counter(bucket.get(field) or {})
        incoming = event.get(field)
        if isinstance(incoming, Mapping):
            merged.update({str(k): int(v) for k, v in dict(incoming).items() if str(k)})
        bucket[field] = _counter_dict(merged)
    denom = int(bucket.get("passed_rate_denominator") or 0)
    bucket["passed_rate"] = float(bucket.get("passed_rate_numerator") or 0) / float(denom) if denom else 0.0


def aggregate_emlis_rollout_metrics(events: Sequence[Any] | Iterable[Any] | None = None) -> Dict[str, Any]:
    """Aggregate Step16 metric events for internal QA / A-P0 judgement."""

    normalized = [_normalize_event(item) for item in list(events or [])]
    totals = _bucket()
    by_stage: Dict[str, Dict[str, Any]] = {}
    by_coverage_group: Dict[str, Dict[str, Any]] = {}
    by_composer_model: Dict[str, Dict[str, Any]] = {}
    status_counts: Counter[str] = Counter({status: 0 for status in OBSERVATION_STATUSES})
    stage_counts: Counter[str] = Counter()
    cohort_counts: Counter[str] = Counter()
    primary_reason_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    coverage_group_counts: Counter[str] = Counter()
    composer_model_counts: Counter[str] = Counter()

    for event in normalized:
        _merge_counts(totals, event)
        stage = _clean(event.get("rollout_stage") or event.get("stage")) or "unknown"
        coverage_group = _clean(event.get("coverage_group")) or "unclassified"
        composer_model = _clean(event.get("composer_model")) or "not_connected"
        by_stage.setdefault(stage, _bucket())
        by_coverage_group.setdefault(coverage_group, _bucket())
        by_composer_model.setdefault(composer_model, _bucket())
        _merge_counts(by_stage[stage], event)
        _merge_counts(by_coverage_group[coverage_group], event)
        _merge_counts(by_composer_model[composer_model], event)
        status = _status(event.get("observation_status"))
        status_counts[status] += 1
        stage_counts[stage] += 1
        cohort_counts[_clean(event.get("cohort")) or "unknown"] += 1
        primary = _clean(event.get("primary_reason")) or status
        primary_reason_counts[primary] += 1
        reason_counts.update(_list(event.get("rejection_reasons")) or ([primary] if primary != "passed" else []))
        coverage_group_counts.update(_list(event.get("coverage_groups")) or [coverage_group])
        composer_model_counts[composer_model] += 1

    failed_total = totals["rejected"] + totals["unavailable"] + totals["safety_blocked"]
    unclassified_count = totals["unclassified_reason_count"]
    top_reasons = sorted(reason_counts.items(), key=lambda item: (-int(item[1]), str(item[0])))[:10]
    ready_for_ap0 = bool(normalized) and bool(primary_reason_counts or totals["passed"]) and unclassified_count < max(1, failed_total)

    return {
        "version": STEP16_ROLLOUT_METRICS_AGGREGATE_VERSION,
        "phase": STEP16_PHASE,
        "step": STEP16_STEP,
        "purpose": "aggregate_staged_release_metrics_for_ap0_judgement",
        "ready": True,
        "metric_complete": True,
        "event_count": len(normalized),
        "record_count": len(normalized),
        "required_fields": list(STEP16_REQUIRED_EVENT_FIELDS),
        "rollout_stage_order": list(ROLLOUT_STAGES),
        "totals": totals,
        "attempted": totals["attempted"],
        "attempted_count": totals["attempted"],
        "blocked_before_attempt_count": totals["blocked_before_attempt_count"],
        "passed": totals["passed"],
        "passed_count": totals["passed"],
        "rejected": totals["rejected"],
        "rejected_count": totals["rejected"],
        "unavailable": totals["unavailable"],
        "unavailable_count": totals["unavailable"],
        "safety_blocked": totals["safety_blocked"],
        "safety_blocked_count": totals["safety_blocked"],
        "passed_rate_numerator": totals["passed_rate_numerator"],
        "passed_rate_denominator": totals["passed_rate_denominator"],
        "passed_rate": totals["passed_rate"],
        "status_counts": _counter_dict(status_counts),
        "stage_counts": _counter_dict(stage_counts),
        "cohort_counts": _counter_dict(cohort_counts),
        "primary_reason_counts": _counter_dict(primary_reason_counts),
        "rejection_reason_counts": _counter_dict(reason_counts),
        "coverage_group_counts": _counter_dict(coverage_group_counts),
        "composer_model_counts": _counter_dict(composer_model_counts),
        "by_observation_status": _counter_dict(status_counts),
        "by_stage": by_stage,
        "by_rollout_stage": _counter_dict(stage_counts),
        "by_cohort": _counter_dict(cohort_counts),
        "by_primary_reason": _counter_dict(primary_reason_counts),
        "by_coverage_group": _counter_dict(coverage_group_counts),
        "by_coverage_group_detail": by_coverage_group,
        "by_composer_model": _counter_dict(composer_model_counts),
        "by_composer_model_detail": by_composer_model,
        "top_rejection_reasons": [{"reason": reason, "count": count} for reason, count in top_reasons if reason != "passed"],
        "unclassified_reason_count": unclassified_count,
        "coverage_unclassified_reason_count": unclassified_count,
        "ap0_judgement": {
            "usable_for_ap0": ready_for_ap0,
            "has_attempt_distribution": totals["attempted"] > 0,
            "has_failure_distribution": failed_total > 0,
            "unclassified_reason_count": unclassified_count,
            "do_not_promote_from_passed_only": failed_total > 0 or totals["not_attempted"] > 0,
        },
        "a_p0_decision_material": {
            "record_count": len(normalized),
            "attempted_count": totals["attempted"],
            "passed_rate": totals["passed_rate"],
            "primary_reason_counts": _counter_dict(primary_reason_counts),
            "coverage_group_counts": _counter_dict(coverage_group_counts),
            "composer_model_counts": _counter_dict(composer_model_counts),
            "unclassified_reason_count": unclassified_count,
        },
    }


def aggregate_step16_rollout_metrics(events: Sequence[Any] | Iterable[Any] | None = None) -> Dict[str, Any]:
    """Backward-compatible alias."""
    return aggregate_emlis_rollout_metrics(events)


def build_step16_rollout_metrics(
    *,
    release_meta: Mapping[str, Any] | None = None,
    diagnostic_summary: Mapping[str, Any] | None = None,
    phase7_rollout_metrics: Mapping[str, Any] | None = None,
    composer_candidate: Any = None,
) -> Dict[str, Any]:
    """Return the Step16 meta block used by ``emlis_ai_reply_service``."""

    event = build_emlis_rollout_metric_event(
        diagnostic_summary=diagnostic_summary,
        release_meta=release_meta,
        phase7_rollout_metrics=phase7_rollout_metrics,
    )
    candidate_model = _clean(getattr(composer_candidate, "composer_model", ""))
    if candidate_model and event.get("composer_model") == "not_connected":
        event["composer_model"] = candidate_model
        event["composer_model_counts"] = {candidate_model: 1}
        dimensions = event.get("aggregation_dimensions")
        if isinstance(dimensions, dict):
            dimensions["composer_model"] = candidate_model
    aggregate = aggregate_emlis_rollout_metrics([event])
    return {
        "version": STEP16_ROLLOUT_METRICS_VERSION,
        "phase": STEP16_PHASE,
        "step": STEP16_STEP,
        "ready": bool(event.get("ready") or event.get("metric_complete")),
        "aggregation_ready": bool(aggregate.get("ready") or aggregate.get("metric_complete")),
        "metric_fields": list(STEP16_REQUIRED_EVENT_FIELDS),
        "attempted": bool(event.get("attempted")),
        "passed": bool(event.get("passed")),
        "rejected": bool(event.get("rejected")),
        "unavailable": bool(event.get("unavailable")),
        "safety_blocked": bool(event.get("safety_blocked")),
        "attempted_count": int(event.get("attempted_count") or 0),
        "blocked_before_attempt": bool(event.get("blocked_before_attempt")),
        "blocked_before_attempt_count": int(event.get("blocked_before_attempt_count") or 0),
        "passed_count": int(event.get("passed_count") or 0),
        "rejected_count": int(event.get("rejected_count") or 0),
        "unavailable_count": int(event.get("unavailable_count") or 0),
        "safety_blocked_count": int(event.get("safety_blocked_count") or 0),
        "passed_rate_numerator": int(event.get("passed_rate_numerator") or 0),
        "passed_rate_denominator": int(event.get("passed_rate_denominator") or 0),
        "passed_rate": float(event.get("passed_rate") or 0.0),
        "rollout_stage": str(event.get("rollout_stage") or event.get("stage") or ""),
        "stage": str(event.get("stage") or event.get("rollout_stage") or ""),
        "cohort": str(event.get("cohort") or ""),
        "observation_status": str(event.get("observation_status") or ""),
        "primary_reason": str(event.get("primary_reason") or ""),
        "secondary_reasons": list(event.get("secondary_reasons") or []),
        "rejection_reasons": list(event.get("rejection_reasons") or []),
        "coverage_group": str(event.get("coverage_group") or ""),
        "coverage_primary_group": str(event.get("coverage_primary_group") or event.get("coverage_group") or ""),
        "coverage_groups": list(event.get("coverage_groups") or []),
        "coverage_scope": str(event.get("coverage_scope") or ""),
        "coverage_next_steps": list(event.get("coverage_next_steps") or []),
        "coverage_unclassified_reasons": list(event.get("coverage_unclassified_reasons") or []),
        "coverage_unclassified_reason_count": int(event.get("coverage_unclassified_reason_count") or 0),
        "unclassified_reasons": list(event.get("unclassified_reasons") or []),
        "unclassified_reason_count": int(event.get("unclassified_reason_count") or 0),
        "composer_model": str(event.get("composer_model") or ""),
        "composer_status": str(event.get("composer_status") or ""),
        "metric_event": event,
        "rollout_metric_event": event,
        "aggregate": aggregate,
        "rollout_metrics_aggregate": aggregate,
        "internal_qa_aggregate": aggregate,
        "aggregation_dimensions": dict(event.get("aggregation_dimensions") or {}),
        "aggregation_key": str(event.get("aggregation_key") or ""),
        "a_p0_decision_material": dict(event.get("a_p0_decision_material") or {}),
    }


__all__ = [
    "OBSERVATION_STATUSES",
    "ROLLOUT_STAGES",
    "STEP16_PHASE",
    "STEP16_REQUIRED_EVENT_FIELDS",
    "STEP16_ROLLOUT_METRIC_EVENT_VERSION",
    "STEP16_ROLLOUT_METRICS_AGGREGATE_VERSION",
    "STEP16_ROLLOUT_METRICS_VERSION",
    "STEP16_ROLLOUT_SUMMARY_VERSION",
    "STEP16_STEP",
    "aggregate_emlis_rollout_metrics",
    "aggregate_step16_rollout_metrics",
    "build_emlis_rollout_metric_event",
    "build_emlis_rollout_metrics_event",
    "build_step16_rollout_metrics",
]
