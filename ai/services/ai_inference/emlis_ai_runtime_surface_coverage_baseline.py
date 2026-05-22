# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step4 Coverage Runtime Baseline for EmlisAI Runtime Surface Quality.

This module keeps the Step4 contract meta-only.  It aggregates already
normalized scorecard/surface-signature events by runtime coverage group so the
next branch can see where display, binding, surface, and grammar are blocked
without storing raw input bodies or public observation text.
"""

import json
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

RUNTIME_SURFACE_COVERAGE_BASELINE_VERSION = "emlis.runtime_surface_coverage_baseline.v1"
RUNTIME_SURFACE_COVERAGE_BASELINE_STEP = "Step4_Coverage_Runtime_Baseline"
RUNTIME_SURFACE_COVERAGE_GROUP_MISSING = "coverage_group_missing"
RUNTIME_SURFACE_COVERAGE_GROUP_ORDER: Sequence[str] = (
    "short_daily",
    "long_meaning_arc",
    "conflict",
    "recovery",
    "pressure",
    "desire_fear",
    "relationship",
)
RUNTIME_SURFACE_COVERAGE_GROUP_ALIASES: Mapping[str, str] = {
    "positive_recovery": "recovery",
    "energy_fatigue": "short_daily",
    "anxiety": "short_daily",
    "anger_hurt": "conflict",
    "limit_escape": "pressure",
    "value_wish": "short_daily",
    "wish_fear": "desire_fear",
    "desire_and_fear": "desire_fear",
    "desire-fear": "desire_fear",
    "approach_avoidance": "desire_fear",
    "history_cross_core": "long_meaning_arc",
    "safety_boundary": "pressure",
}
RUNTIME_SURFACE_RELATION_TO_COVERAGE_GROUP: Mapping[str, str] = {
    "contrast": "conflict",
    "coexistence": "conflict",
    "approach_avoidance": "desire_fear",
    "recovery": "recovery",
    "pressure": "pressure",
    "residue": "short_daily",
    "history_cross_core": "long_meaning_arc",
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
    "user_input",
    "userInput",
    "memo",
    "memo_text",
    "memoText",
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
    "realized_text",
    "body",
    "text",
}


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


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, (tuple, set)):
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


def assert_runtime_surface_coverage_baseline_meta_only(
    value: Mapping[str, Any],
    *,
    source: str = "runtime_surface_coverage_baseline",
) -> None:
    """Reject text payloads and any contract-relaxation marker."""

    if _contains_forbidden_text_payload_key(value):
        raise ValueError(f"{source} must stay meta-only and must not include text payload keys")
    forbidden_true_flags = (
        "raw_input_included",
        "raw_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "response_shape_changed",
        "public_response_key_change",
        "api_route_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "template_gate_relaxed",
        "reader_gate_relaxed",
        "gate_relaxed",
        "public_release_applied",
        "product_gate_achieved",
        "fixture_text_used_for_runtime_branching",
        "runtime_branching_uses_fixture_strings",
    )
    for key in forbidden_true_flags:
        if value.get(key) is True:
            raise ValueError(f"{source} violates fixed Step4 contract: {key}=true")


def normalize_runtime_surface_coverage_group(
    group: Any,
    *,
    relation_types: Sequence[Any] | Iterable[Any] | Any | None = None,
) -> str:
    """Normalize Step4 coverage without falling missing values back to short_daily."""

    raw = _clean(group).lower()
    relations = _dedupe(relation_types)
    if raw in RUNTIME_SURFACE_COVERAGE_GROUP_ORDER:
        return raw
    if raw in RUNTIME_SURFACE_COVERAGE_GROUP_ALIASES:
        return RUNTIME_SURFACE_COVERAGE_GROUP_ALIASES[raw]
    for relation in relations:
        mapped = RUNTIME_SURFACE_RELATION_TO_COVERAGE_GROUP.get(str(relation).lower())
        if mapped:
            return mapped
    if raw in {"", "unclassified", "unknown", "missing", "none", "null", RUNTIME_SURFACE_COVERAGE_GROUP_MISSING}:
        return RUNTIME_SURFACE_COVERAGE_GROUP_MISSING
    return RUNTIME_SURFACE_COVERAGE_GROUP_MISSING


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


def _surface_signature_family_key(event: Mapping[str, Any]) -> str:
    nested = _safe_mapping(event.get("surface_quality_signature")) or _safe_mapping(
        event.get("step2_surface_quality_signature")
    )
    for key in (
        "surface_signature_family_key",
        "signature_family_key",
        "surface_signature_id",
    ):
        text = _clean(event.get(key) or nested.get(key))
        if text:
            return text
    return ""


def _reason_values(event: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    for key in (
        "top_rejection_reasons",
        "release_blockers",
        "surface_major_reasons",
        "rejection_reasons",
        "secondary_reasons",
        "reason_codes",
        "gate_reasons",
        "unsupported_reasons",
    ):
        reasons.extend(_dedupe(event.get(key)))
    for key in (
        "primary_reason",
        "gate_primary_reason",
        "first_failed_reason",
        "failed_stage",
        "stage",
        "unavailable_reason",
        "reason_code",
    ):
        text = _clean(event.get(key))
        if text:
            reasons.append(text)
    reason_counter = _safe_mapping(event.get("reason_counter"))
    reasons.extend(str(reason) for reason in reason_counter)
    return _dedupe(reasons)


def _is_surface_ready(event: Mapping[str, Any], family_key: str) -> bool:
    if family_key:
        return True
    for key in (
        "surface_quality_signature_ready",
        "step2_surface_quality_signature_ready",
        "step2_surface_signature_measurement_ready",
        "surface_metrics_event_ready",
    ):
        if bool(event.get(key)):
            return True
    return False


def _normalize_runtime_surface_event(record: Any) -> dict[str, Any]:
    event = _safe_mapping(record)
    if not event:
        return {}

    relation_types = _event_relation_types(event)
    coverage_group = normalize_runtime_surface_coverage_group(
        event.get("coverage_group"),
        relation_types=relation_types,
    )
    observation_status = _clean(event.get("observation_status")).lower()
    eligible_count = _safe_int(event.get("eligible_count"), 0)
    if eligible_count <= 0 and (observation_status or event.get("complete_candidate_seen") or event.get("display_confirmed")):
        eligible_count = 1

    if "scorecard_passed_display_count" in event:
        passed_display_count = _safe_int(event.get("scorecard_passed_display_count"), 0)
    elif "passed_display_count" in event:
        passed_display_count = _safe_int(event.get("passed_display_count"), 0)
    elif event.get("display_confirmed") is True or observation_status == "passed":
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

    family_key = _surface_signature_family_key(event)
    surface_ready = _is_surface_ready(event, family_key)
    surface_signature_count = _safe_int(event.get("surface_signature_count"), 0)
    if surface_signature_count <= 0 and surface_ready and family_key:
        surface_signature_count = 1
    surface_template_major_count = max(
        _safe_int(event.get("surface_template_major_count"), 0),
        1 if event.get("surface_template_major") is True or event.get("template_major") is True else 0,
    )

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

    reasons = _reason_values(event)
    non_pass_count = rejected_count + unavailable_count + safety_blocked_count
    reason_required_count = _safe_int(event.get("reason_required_count"), 0)
    reason_covered_count = _safe_int(event.get("reason_covered_count"), 0)
    if reason_required_count <= 0 and non_pass_count:
        reason_required_count = non_pass_count
        reason_covered_count = non_pass_count if reasons else 0

    return {
        "coverage_group": coverage_group,
        "eligible_count": eligible_count,
        "event_count": 1,
        "candidate_generated_count": _safe_int(event.get("candidate_generated_count"), 0) or (1 if event.get("complete_candidate_seen") else 0),
        "passed_display_count": passed_display_count,
        "rejected_count": rejected_count,
        "unavailable_count": unavailable_count,
        "safety_blocked_count": safety_blocked_count,
        "binding_supported_sentence_count": binding_supported_count,
        "expected_binding_count": expected_binding_count,
        "repair_attempt_count": _safe_int(event.get("repair_attempt_count"), 0),
        "repair_success_count": _safe_int(event.get("repair_success_count"), 0),
        "template_major_count": _safe_int(event.get("template_major_count"), 0),
        "safety_major_count": _safe_int(event.get("safety_major_count"), 0),
        "reason_required_count": reason_required_count,
        "reason_covered_count": reason_covered_count,
        "surface_signature_count": surface_signature_count,
        "surface_signature_ready_count": 1 if surface_ready else 0,
        "surface_signature_family_key": family_key,
        "surface_template_major_count": surface_template_major_count,
        "surface_connector_repetition_event_count": _safe_int(event.get("surface_connector_repetition_event_count"), 0),
        "surface_predicate_family_repetition_event_count": _safe_int(event.get("surface_predicate_family_repetition_event_count"), 0),
        "surface_ending_repetition_event_count": _safe_int(event.get("surface_ending_repetition_event_count"), 0),
        "surface_generic_opening_event_count": _safe_int(event.get("surface_generic_opening_event_count"), 0),
        "surface_grammar_warning_event_count": _safe_int(event.get("surface_grammar_warning_event_count"), 0),
        "surface_grammar_warning_count": _safe_int(event.get("surface_grammar_warning_count"), 0),
        "surface_major_reasons": _dedupe(event.get("surface_major_reasons")),
        "surface_grammar_warning_codes": _dedupe(event.get("surface_grammar_warning_codes") or event.get("grammar_warning_codes")),
        "reasons": reasons,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
    }


def _empty_coverage_row(group: str) -> dict[str, Any]:
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
        "reason_counter": Counter(),
    }


def _finalize_coverage_row(row: Mapping[str, Any]) -> dict[str, Any]:
    item = dict(row)
    family_counter = Counter(_safe_mapping(item.get("surface_signature_family_counter")))
    reason_counter = Counter(_safe_mapping(item.get("reason_counter")))
    surface_reason_counter = Counter(_safe_mapping(item.get("surface_major_reason_counter")))
    grammar_counter = Counter(_safe_mapping(item.get("surface_grammar_warning_counter")))
    surface_signature_count = _safe_int(item.get("surface_signature_count"), 0)

    item["display_reach_rate"] = _rate(item.get("passed_display_count"), item.get("eligible_count"))
    item["binding_pass_rate"] = _rate(item.get("binding_supported_sentence_count"), item.get("expected_binding_count"))
    item["repair_success_rate"] = _rate(item.get("repair_success_count"), item.get("repair_attempt_count"))
    item["reason_coverage_rate"] = 1.0 if _safe_int(item.get("reason_required_count"), 0) <= 0 else _rate(item.get("reason_covered_count"), item.get("reason_required_count"))
    item["surface_signature_unique_count"] = len(family_counter)
    item["surface_signature_repeat_count"] = sum(max(0, count - 1) for count in family_counter.values())
    item["surface_signature_repeat_rate"] = _rate(item.get("surface_signature_repeat_count"), surface_signature_count)
    item["coverage_surface_diversity_rate"] = _rate(item.get("surface_signature_unique_count"), surface_signature_count)
    item["connector_repetition_rate"] = _rate(item.get("surface_connector_repetition_event_count"), surface_signature_count)
    item["predicate_family_repetition_rate"] = _rate(item.get("surface_predicate_family_repetition_event_count"), surface_signature_count)
    item["ending_repetition_rate"] = _rate(item.get("surface_ending_repetition_event_count"), surface_signature_count)
    item["generic_opening_rate"] = _rate(item.get("surface_generic_opening_event_count"), surface_signature_count)
    item["grammar_warning_rate"] = _rate(item.get("surface_grammar_warning_event_count"), surface_signature_count)
    item["surface_metrics_ready"] = surface_signature_count > 0
    item["surface_signature_family_counter"] = dict(family_counter)
    item["surface_major_reason_counter"] = dict(surface_reason_counter)
    item["surface_major_reasons"] = [reason for reason, _ in surface_reason_counter.most_common(8)]
    item["surface_grammar_warning_counter"] = dict(grammar_counter)
    item["surface_grammar_warning_codes"] = [code for code, _ in grammar_counter.most_common(8)]
    item["reason_counter"] = dict(reason_counter)
    item["top_rejection_reasons"] = [reason for reason, _ in reason_counter.most_common(8)]
    return item


def build_runtime_surface_coverage_matrix_contract() -> dict[str, Any]:
    """Return Step4 coverage matrix contract without raw fixture text."""

    contract = {
        "version": "emlis.runtime_surface_coverage_matrix_contract.v1",
        "source_step": RUNTIME_SURFACE_COVERAGE_BASELINE_STEP,
        "target_step": RUNTIME_SURFACE_COVERAGE_BASELINE_STEP,
        "required_coverage_groups": list(RUNTIME_SURFACE_COVERAGE_GROUP_ORDER),
        "coverage_group_missing_key": RUNTIME_SURFACE_COVERAGE_GROUP_MISSING,
        "missing_group_falls_back_to_short_daily": False,
        "fixture_text_used_for_runtime_branching": False,
        "runtime_branching_uses_fixture_strings": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
    }
    assert_runtime_surface_coverage_baseline_meta_only(contract, source="runtime_surface_coverage_matrix_contract")
    return contract


def build_runtime_surface_coverage_baseline(
    *,
    events: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Aggregate Step4 runtime surface metrics by required coverage group."""

    normalized_events = [_normalize_runtime_surface_event(event) for event in list(events or [])]
    normalized_events = [event for event in normalized_events if event]
    group_rows: dict[str, dict[str, Any]] = {
        group: _empty_coverage_row(group) for group in RUNTIME_SURFACE_COVERAGE_GROUP_ORDER
    }
    totals = _empty_coverage_row("__totals__")

    for event in normalized_events:
        group = str(event.get("coverage_group") or RUNTIME_SURFACE_COVERAGE_GROUP_MISSING)
        if group not in group_rows:
            group_rows[group] = _empty_coverage_row(group)
        row = group_rows[group]
        for target in (row, totals):
            for key, value in event.items():
                if key in {
                    "coverage_group",
                    "surface_signature_family_key",
                    "surface_major_reasons",
                    "surface_grammar_warning_codes",
                    "reasons",
                    "raw_input_included",
                    "raw_text_included",
                    "comment_text_included",
                    "comment_text_body_included",
                }:
                    continue
                if key in target:
                    target[key] = _safe_int(target.get(key), 0) + _safe_int(value, 0)
        family_key = _clean(event.get("surface_signature_family_key"))
        if family_key and _safe_int(event.get("surface_signature_count"), 0) > 0:
            row["surface_signature_family_counter"][family_key] += 1
            totals["surface_signature_family_counter"][family_key] += 1
        for reason in _dedupe(event.get("surface_major_reasons")):
            row["surface_major_reason_counter"][reason] += 1
            totals["surface_major_reason_counter"][reason] += 1
        for code in _dedupe(event.get("surface_grammar_warning_codes")):
            row["surface_grammar_warning_counter"][code] += 1
            totals["surface_grammar_warning_counter"][code] += 1
        for reason in _dedupe(event.get("reasons")):
            row["reason_counter"][reason] += 1
            totals["reason_counter"][reason] += 1

    def sort_key(group: str) -> tuple[int, str]:
        if group in RUNTIME_SURFACE_COVERAGE_GROUP_ORDER:
            return (RUNTIME_SURFACE_COVERAGE_GROUP_ORDER.index(group), group)
        if group == RUNTIME_SURFACE_COVERAGE_GROUP_MISSING:
            return (len(RUNTIME_SURFACE_COVERAGE_GROUP_ORDER), group)
        return (len(RUNTIME_SURFACE_COVERAGE_GROUP_ORDER) + 1, group)

    rows = [_finalize_coverage_row(group_rows[group]) for group in sorted(group_rows, key=sort_key)]
    by_coverage_group = {str(row.get("coverage_group")): dict(row) for row in rows}
    observed_groups = [
        group
        for group in RUNTIME_SURFACE_COVERAGE_GROUP_ORDER
        if _safe_int(by_coverage_group.get(group, {}).get("event_count"), 0) > 0
        or _safe_int(by_coverage_group.get(group, {}).get("eligible_count"), 0) > 0
    ]
    missing_groups = [group for group in RUNTIME_SURFACE_COVERAGE_GROUP_ORDER if group not in observed_groups]
    missing_row = dict(by_coverage_group.get(RUNTIME_SURFACE_COVERAGE_GROUP_MISSING, _finalize_coverage_row(_empty_coverage_row(RUNTIME_SURFACE_COVERAGE_GROUP_MISSING))))
    coverage_group_missing_count = _safe_int(missing_row.get("event_count"), 0)
    totals_final = _finalize_coverage_row(totals)

    groups_needing_attention: list[str] = []
    for row in rows:
        group = str(row.get("coverage_group"))
        if group == "__totals__":
            continue
        if (
            _safe_int(row.get("rejected_count"), 0) > 0
            or _safe_int(row.get("unavailable_count"), 0) > 0
            or _safe_int(row.get("safety_blocked_count"), 0) > 0
            or (_safe_int(row.get("expected_binding_count"), 0) > 0 and float(row.get("binding_pass_rate") or 0.0) < 1.0)
            or _safe_int(row.get("surface_signature_repeat_count"), 0) > 0
            or _safe_int(row.get("surface_template_major_count"), 0) > 0
            or _safe_int(row.get("surface_grammar_warning_event_count"), 0) > 0
            or _safe_int(row.get("surface_connector_repetition_event_count"), 0) > 0
            or _safe_int(row.get("surface_predicate_family_repetition_event_count"), 0) > 0
            or _safe_int(row.get("surface_ending_repetition_event_count"), 0) > 0
        ):
            groups_needing_attention.append(group)

    release_blockers: list[str] = []
    if coverage_group_missing_count > 0:
        release_blockers.append("coverage_group_missing")
    if missing_groups:
        release_blockers.append("coverage_groups_incomplete")
    if any(_safe_int(row.get("surface_signature_repeat_count"), 0) > 0 for row in rows):
        release_blockers.append("coverage_surface_signature_repeat_detected")
    if _safe_int(totals_final.get("surface_template_major_count"), 0) > 0:
        release_blockers.append("coverage_surface_template_major_detected")
    if _safe_int(totals_final.get("surface_grammar_warning_event_count"), 0) > 0:
        release_blockers.append("coverage_grammar_warning_detected")

    baseline = {
        "version": RUNTIME_SURFACE_COVERAGE_BASELINE_VERSION,
        "source_step": RUNTIME_SURFACE_COVERAGE_BASELINE_STEP,
        "target_step": RUNTIME_SURFACE_COVERAGE_BASELINE_STEP,
        "step": RUNTIME_SURFACE_COVERAGE_BASELINE_STEP,
        "coverage_runtime_baseline_ready": True,
        "step4_coverage_runtime_baseline_ready": True,
        "event_count": len(normalized_events),
        "record_count": len(normalized_events),
        "required_coverage_groups": list(RUNTIME_SURFACE_COVERAGE_GROUP_ORDER),
        "observed_coverage_groups": observed_groups,
        "missing_coverage_groups": missing_groups,
        "coverage_group_count": len(observed_groups),
        "coverage_group_missing_key": RUNTIME_SURFACE_COVERAGE_GROUP_MISSING,
        "coverage_group_missing_count": coverage_group_missing_count,
        "coverage_group_missing_blocker": coverage_group_missing_count > 0,
        "required_coverage_groups_complete": not missing_groups and coverage_group_missing_count == 0,
        "coverage_group_rows": rows,
        "by_coverage_group": by_coverage_group,
        "coverage_group_missing_row": missing_row,
        "totals": totals_final,
        "display_reach_rate": totals_final.get("display_reach_rate", 0.0),
        "binding_pass_rate": totals_final.get("binding_pass_rate", 0.0),
        "surface_signature_repeat_rate": totals_final.get("surface_signature_repeat_rate", 0.0),
        "coverage_surface_diversity_rate": totals_final.get("coverage_surface_diversity_rate", 0.0),
        "connector_repetition_rate": totals_final.get("connector_repetition_rate", 0.0),
        "predicate_family_repetition_rate": totals_final.get("predicate_family_repetition_rate", 0.0),
        "ending_repetition_rate": totals_final.get("ending_repetition_rate", 0.0),
        "generic_opening_rate": totals_final.get("generic_opening_rate", 0.0),
        "grammar_warning_rate": totals_final.get("grammar_warning_rate", 0.0),
        "surface_template_major_count": totals_final.get("surface_template_major_count", 0),
        "surface_signature_repeat_count": totals_final.get("surface_signature_repeat_count", 0),
        "groups_needing_attention": _dedupe(groups_needing_attention),
        "release_blockers": _dedupe(release_blockers),
        "fixture_text_used_for_runtime_branching": False,
        "runtime_branching_uses_fixture_strings": False,
        "missing_group_falls_back_to_short_daily": False,
        "machine_metrics_separated_from_blind_qa": True,
        "read_feeling_requires_blind_qa": True,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "gate_relaxed": False,
        "public_release_applied": False,
        "product_gate_achieved": False,
    }
    assert_runtime_surface_coverage_baseline_meta_only(baseline)
    return baseline


def dump_runtime_surface_coverage_baseline(
    baseline: Mapping[str, Any] | None = None,
    *,
    events: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None = None,
) -> str:
    data = dict(baseline or build_runtime_surface_coverage_baseline(events=events))
    assert_runtime_surface_coverage_baseline_meta_only(data)
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "RUNTIME_SURFACE_COVERAGE_BASELINE_VERSION",
    "RUNTIME_SURFACE_COVERAGE_BASELINE_STEP",
    "RUNTIME_SURFACE_COVERAGE_GROUP_ORDER",
    "RUNTIME_SURFACE_COVERAGE_GROUP_MISSING",
    "assert_runtime_surface_coverage_baseline_meta_only",
    "normalize_runtime_surface_coverage_group",
    "build_runtime_surface_coverage_matrix_contract",
    "build_runtime_surface_coverage_baseline",
    "dump_runtime_surface_coverage_baseline",
]
