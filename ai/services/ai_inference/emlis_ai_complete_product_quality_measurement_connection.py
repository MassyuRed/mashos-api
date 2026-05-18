# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step3-Step10 ProductGate measurement connection for EmlisAI.

Step3 converts joined backend/RN diagnostic rows into the existing
ProductQualityScorecard event schema.  Step4 builds one internal measurement
report that connects scorecard and release ladder outputs.  Step5 adds
coverage-group aggregation without relaxing public API/RN/DB/Gate contracts.
Step6 exposes meta-only Blind QA candidates and keeps read-feeling scores
separate from machine metrics.  Step7 routes the next action from diagnostic
classification, top rejection reasons, and release blockers before any
cause-repair branch is selected.  Step10 fixes the Exit Gate as measurement
connection completion only: it never declares Product Gate achieved and never
applies public release.  It is meta-only: raw input bodies and public
comment_text bodies are rejected.
"""

import json
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from emlis_ai_complete_product_quality_scorecard_service import (
    COMPLETE_PRODUCT_QUALITY_COVERAGE_GROUP_AGGREGATION_VERSION,
    COMPLETE_PRODUCT_QUALITY_COVERAGE_GROUP_MISSING,
    COMPLETE_PRODUCT_QUALITY_SCORECARD_EVENT_SCHEMA_VERSION,
    build_complete_product_quality_scorecard,
)
from emlis_ai_complete_scorecard_service import COMPLETE_COVERAGE_GROUP_ORDER
from emlis_ai_complete_release_ladder_service import (
    build_complete_product_quality_release_ladder,
)
from emlis_ai_observation_diagnostic_branching import (
    known_observation_branch_classifications,
    resolve_observation_diagnostic_next_branch,
)

COMPLETE_PRODUCT_QUALITY_MEASUREMENT_CONNECTION_VERSION = (
    "emlis.complete_product_quality_measurement_connection.v1"
)
COMPLETE_PRODUCT_QUALITY_MEASUREMENT_CONNECTION_STEP = (
    "Step3_joined_row_to_scorecard_event_adapter"
)
COMPLETE_PRODUCT_QUALITY_MEASUREMENT_RUN_BUILDER_STEP = (
    "Step4_measurement_run_builder"
)
COMPLETE_PRODUCT_QUALITY_MEASUREMENT_COVERAGE_GROUP_STEP = (
    "Step5_coverage_group_aggregation"
)
COMPLETE_PRODUCT_QUALITY_MEASUREMENT_BLIND_QA_STEP = (
    "Step6_Blind_QA_separation"
)
COMPLETE_PRODUCT_QUALITY_MEASUREMENT_BLIND_QA_SEPARATION_STEP = (
    COMPLETE_PRODUCT_QUALITY_MEASUREMENT_BLIND_QA_STEP
)
COMPLETE_PRODUCT_QUALITY_MEASUREMENT_NEXT_ACTION_ROUTING_STEP = (
    "Step7_next_action_routing"
)
COMPLETE_PRODUCT_QUALITY_MEASUREMENT_EXIT_GATE_STEP = "Step10_Exit_Gate"
COMPLETE_PRODUCT_QUALITY_MEASUREMENT_EXIT_GATE_REQUIRED_FIXTURE_CLASSES = (
    "diagnostic_missing",
    "backend_rejected",
    "passed_backend_frontend_hidden",
    "display_confirmed",
)
_BLIND_QA_REQUIRED_DIMENSIONS = (
    "read_feeling",
    "evidence_retention",
    "distance",
    "naturalness",
    "non_template",
)

_FORBIDDEN_TEXT_PAYLOAD_KEYS = {
    "raw_input",
    "rawInput",
    "raw_text",
    "rawText",
    "source_text",
    "body_text",
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
    "inputFeedbackComment",
    "public_comment_text",
    "candidate_comment_text",
    "reply_text",
    "replyText",
    "text",
}
_BACKEND_STATUS_VALUES = {"passed", "rejected", "unavailable", "safety_blocked"}
_SKIP_REASON_VALUES = {
    "",
    "pass",
    "passed",
    "ok",
    "true",
    "none",
    "displayed",
    "captured",
    "joined",
}
_NON_REJECTION_CLASSIFICATIONS = {"", "passed_displayed"}
_SUCCESS_REPAIR_STATUSES = {"success", "succeeded", "applied", "repaired", "passed", "completed"}
_BRANCH_KNOWN_CLASSIFICATIONS = set(known_observation_branch_classifications())
_CLASSIFICATION_ROUTING_ALIASES = {
    "backend_public_passed_frontend_unconfirmed": "unknown_diagnostic_missing",
    "diagnostic_log_missing_or_not_captured": "unknown_diagnostic_missing",
    "backend_diagnostic_missing_or_not_captured": "unknown_diagnostic_missing",
    "frontend_diagnostic_missing_or_not_captured": "unknown_diagnostic_missing",
    "unclassified": "unclassified_non_display",
    "unknown": "unknown_diagnostic_missing",
}
_RELEASE_BLOCKER_CLASSIFICATION_HINTS = {
    "measurement_rows_missing": "unknown_diagnostic_missing",
    "diagnostic_log_missing_or_not_captured": "unknown_diagnostic_missing",
    "backend_diagnostic_missing_or_not_captured": "unknown_diagnostic_missing",
    "frontend_diagnostic_missing_or_not_captured": "unknown_diagnostic_missing",
    "reason_missing": "unclassified_non_display",
    "reason_coverage_below_target": "unclassified_non_display",
    "reason_coverage_rate_below_target": "unclassified_non_display",
    "binding_pass_rate_below_target": "candidate_generated_but_grounding_rejected",
    "binding_contract_unresolved": "candidate_generated_but_grounding_rejected",
    "unsupported_sentence": "candidate_generated_but_grounding_rejected",
    "grounding:unsupported_sentence": "candidate_generated_but_grounding_rejected",
    "template_major_detected": "candidate_generated_but_template_rejected",
    "template_major": "candidate_generated_but_template_rejected",
    "raw_echo": "candidate_generated_but_template_rejected",
    "same_ending": "candidate_generated_but_template_rejected",
    "fixed_sentence": "candidate_generated_but_template_rejected",
    "frontend_modal_not_opened": "passed_backend_frontend_hidden",
    "coverage_group_missing": "passed_displayed",
    "coverage_groups_incomplete": "passed_displayed",
    "product_gate_coverage_groups_incomplete": "passed_displayed",
    "blind_qa_missing": "passed_displayed",
    "read_feeling_score_below_broader_target": "passed_displayed",
    "read_feeling_score_below_product_gate_target": "passed_displayed",
}
_RELEASE_BLOCKER_CLASSIFICATION_PREFIX_HINTS = (
    ("grounding:", "candidate_generated_but_grounding_rejected"),
    ("template:", "candidate_generated_but_template_rejected"),
    ("reader:", "candidate_generated_but_reader_rejected"),
    ("display:", "candidate_generated_but_display_rejected"),
)
_DIAGNOSTIC_CAPTURE_BLOCKERS = {
    "measurement_rows_missing",
    "diagnostic_log_missing_or_not_captured",
    "backend_diagnostic_missing_or_not_captured",
    "frontend_diagnostic_missing_or_not_captured",
}
_MEASURED_SURFACE_OR_TONE_REASON_MARKERS = {
    "candidate_generated_but_template_rejected",
    "template_major_detected",
    "template_major",
    "raw_echo",
    "same_ending",
    "fixed_sentence",
    "read_feeling_score_below_broader_target",
    "read_feeling_score_below_product_gate_target",
}


class ProductQualityMeasurementConnectionError(ValueError):
    """Raised when Step3 measurement connection violates meta-only contract."""


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).strip()


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        if isinstance(value, bool):
            return int(value)
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = _clean(value).lower()
    return text in {"1", "true", "yes", "y", "on", "passed", "generated", "success", "applied", "open", "opened"}


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


def _dedupe(values: Iterable[Any] | Any) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in _listify(values):
        text = _clean(value)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _contains_forbidden_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if _clean(key) in _FORBIDDEN_TEXT_PAYLOAD_KEYS:
                return True
            if _contains_forbidden_text_payload_key(nested):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_text_payload_key(item) for item in value)
    return False


def assert_product_quality_measurement_connection_meta_only(
    value: Mapping[str, Any],
    *,
    source: str = "product_quality_measurement_connection",
) -> None:
    """Reject raw input/public comment payloads in Step3 measurement data."""

    if _contains_forbidden_text_payload_key(value):
        raise ProductQualityMeasurementConnectionError(f"{source} contains a forbidden text payload key")
    if value.get("raw_input_included") is True or value.get("raw_text_included") is True or value.get("comment_text_included") is True:
        raise ProductQualityMeasurementConnectionError(f"{source} marks raw input or comment text as included")


def _backend_status(row: Mapping[str, Any]) -> str:
    status = _clean(row.get("backend_status") or row.get("backend_observation_status") or row.get("observation_status")).lower()
    return status if status in _BACKEND_STATUS_VALUES else status


def _backend_comment_length(row: Mapping[str, Any]) -> int:
    return _to_int(row.get("backend_len", row.get("comment_text_length")), 0)


def _classification(row: Mapping[str, Any]) -> str:
    return _clean(row.get("classification")) or _clean(row.get("measurement_classification")) or "unclassified_non_display"


def _measurement_classification(row: Mapping[str, Any]) -> str:
    return _clean(row.get("measurement_classification")) or _classification(row)


def _backend_public_passed(row: Mapping[str, Any], backend_status: str) -> bool:
    if "backend_public_passed" in row:
        return row.get("backend_public_passed") is True
    return backend_status == "passed" and _backend_comment_length(row) > 0


def _frontend_joined(row: Mapping[str, Any]) -> bool:
    return row.get("frontend_joined") is True


def _display_confirmed(row: Mapping[str, Any], *, backend_public_passed: bool) -> bool:
    if "display_confirmed" in row:
        return row.get("display_confirmed") is True
    return bool(backend_public_passed and _frontend_joined(row) and row.get("modal_opened") is True)


def _frontend_join_status(row: Mapping[str, Any], *, frontend_joined: bool) -> str:
    return _clean(row.get("frontend_join_status")) or ("joined" if frontend_joined else "missing")


def _diagnostic_capture_status(row: Mapping[str, Any], *, frontend_joined: bool) -> str:
    status = _clean(row.get("diagnostic_capture_status"))
    if status:
        return status
    return "captured" if frontend_joined else "frontend_diagnostic_missing_or_not_captured"


def _backend_diagnostic_captured(row: Mapping[str, Any], *, backend_status: str) -> bool:
    backend_capture = _clean(row.get("backend_diagnostic_capture_status"))
    if backend_capture == "backend_diagnostic_missing_or_not_captured":
        return False
    return bool(backend_status)


def _candidate_generated(row: Mapping[str, Any]) -> bool:
    if "candidate_generated" in row:
        return row.get("candidate_generated") is True
    if "complete_candidate_generated" in row:
        return row.get("complete_candidate_generated") is True
    candidate = _safe_mapping(row.get("candidate"))
    return candidate.get("generated") is True or candidate.get("seen") is True or candidate.get("generated_before_display_gate") is True


def _repair_attempted(row: Mapping[str, Any]) -> bool:
    if row.get("self_repair_attempted") is True or row.get("repair_attempted") is True:
        return True
    if _to_int(row.get("repair_trace_count"), 0) > 0:
        return True
    for key in ("self_repair", "limited_reader_repair"):
        data = _safe_mapping(row.get(key))
        if data.get("attempted") is True or data.get("repair_attempted") is True:
            return True
    return False


def _repair_success(row: Mapping[str, Any]) -> bool:
    if row.get("repair_success") is True or row.get("self_repair_success") is True or row.get("repair_applied") is True:
        return True
    for key in ("self_repair", "limited_reader_repair"):
        data = _safe_mapping(row.get(key))
        status = _clean(data.get("status")).lower()
        if data.get("success") is True or data.get("applied") is True or data.get("repair_applied") is True:
            return True
        if status in _SUCCESS_REPAIR_STATUSES:
            return True
    return False


def _display_count_blockers(row: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    blockers.extend(_dedupe(row.get("display_count_blockers")))
    join_semantics = _safe_mapping(row.get("join_semantics"))
    blockers.extend(_dedupe(join_semantics.get("display_count_blockers")))
    if row.get("backend_public_passed") is True and row.get("frontend_joined") is not True:
        blockers.append("frontend_diagnostic_missing_or_not_captured")
    if row.get("backend_public_passed") is True and row.get("frontend_joined") is True and row.get("modal_opened") is False:
        blockers.append("frontend_modal_not_opened")
    return _dedupe(blockers)


def _reason_value_allowed(value: Any) -> bool:
    return _clean(value).lower() not in _SKIP_REASON_VALUES


def _collect_reason_values(row: Mapping[str, Any], *, display_confirmed: bool) -> list[str]:
    if display_confirmed:
        return []
    reasons: list[str] = []

    measurement_classification = _measurement_classification(row)
    classification = _classification(row)
    if measurement_classification not in _NON_REJECTION_CLASSIFICATIONS:
        reasons.append(measurement_classification)
    if classification not in _NON_REJECTION_CLASSIFICATIONS and classification != measurement_classification:
        reasons.append(classification)

    for key in (
        "primary_reason",
        "reader_reason",
        "grounding_reason",
        "template_reason",
        "display_reason",
    ):
        text = _clean(row.get(key))
        if text and _reason_value_allowed(text):
            reasons.append(text)

    gate_results = _safe_mapping(row.get("gate_results"))
    for gate_name, gate in gate_results.items():
        gate_map = _safe_mapping(gate)
        if gate_map.get("passed") is False:
            reasons.append(f"{gate_name}_gate_failed")
        for reason_key in ("primary_reason", "first_failed_reason", "reason_code"):
            reason = _clean(gate_map.get(reason_key))
            if reason and _reason_value_allowed(reason):
                reasons.append(reason)
                reasons.append(f"{gate_name}:{reason}")
        for reason_key in ("rejection_reasons", "reasons", "unsupported_reasons"):
            for reason in _dedupe(gate_map.get(reason_key)):
                if _reason_value_allowed(reason):
                    reasons.append(reason)
                    reasons.append(f"{gate_name}:{reason}")

    for key in (
        "top_rejection_reasons",
        "rejection_reasons",
        "secondary_reasons",
        "reason_codes",
        "gate_rejection_reasons",
        "display_rejection_reasons",
        "display_count_blockers",
        "capture_blockers",
    ):
        for reason in _dedupe(row.get(key)):
            if _reason_value_allowed(reason):
                reasons.append(reason)

    for key in ("stage", "diagnostic_capture_status", "frontend_join_status"):
        text = _clean(row.get(key))
        if text and _reason_value_allowed(text):
            reasons.append(text)

    join_semantics = _safe_mapping(row.get("join_semantics"))
    nested_measurement = _clean(join_semantics.get("measurement_classification"))
    if nested_measurement and nested_measurement not in _NON_REJECTION_CLASSIFICATIONS:
        reasons.append(nested_measurement)
    for reason in _dedupe(join_semantics.get("display_count_blockers")):
        if _reason_value_allowed(reason):
            reasons.append(reason)

    reasons.extend(_display_count_blockers(row))

    backend_capture = _clean(row.get("backend_diagnostic_capture_status"))
    if backend_capture == "backend_diagnostic_missing_or_not_captured":
        reasons.append(backend_capture)
    frontend_capture = _clean(row.get("frontend_diagnostic_capture_status"))
    if frontend_capture == "frontend_diagnostic_missing_or_not_captured":
        reasons.append(frontend_capture)

    return _dedupe([reason for reason in reasons if _reason_value_allowed(reason)])[:12]


def _count_from_any(row: Mapping[str, Any], *keys: str) -> int:
    for key in keys:
        value = _to_int(row.get(key), 0)
        if value > 0:
            return value
    return 0


def normalize_observation_row_to_product_quality_event(row: Mapping[str, Any]) -> dict[str, Any]:
    """Convert one joined diagnostic row into a ProductQualityScorecard event.

    A backend ``passed`` row is not counted as displayed unless Step2
    ``display_confirmed`` is true.  Backend-only passes remain in the eligible
    denominator and carry blocker reasons for the measurement report.
    """

    source_row = dict(row or {})
    assert_product_quality_measurement_connection_meta_only(source_row, source="joined_row")

    backend_status = _backend_status(source_row)
    classification = _classification(source_row)
    measurement_classification = _measurement_classification(source_row)
    backend_public_passed = _backend_public_passed(source_row, backend_status)
    frontend_joined = _frontend_joined(source_row)
    display_confirmed = _display_confirmed(source_row, backend_public_passed=backend_public_passed)
    diagnostic_capture_status = _diagnostic_capture_status(source_row, frontend_joined=frontend_joined)
    backend_captured = _backend_diagnostic_captured(source_row, backend_status=backend_status)
    eligible = bool(backend_captured and classification != "unknown_diagnostic_missing")
    candidate_generated = _candidate_generated(source_row)
    repair_attempted = _repair_attempted(source_row)
    repair_success = _repair_success(source_row)
    reasons = _collect_reason_values(source_row, display_confirmed=display_confirmed)
    reason_counter = Counter(reasons)

    event = {
        "version": COMPLETE_PRODUCT_QUALITY_MEASUREMENT_CONNECTION_VERSION,
        "measurement_connection_version": COMPLETE_PRODUCT_QUALITY_MEASUREMENT_CONNECTION_VERSION,
        "scorecard_event_schema_version": COMPLETE_PRODUCT_QUALITY_SCORECARD_EVENT_SCHEMA_VERSION,
        "source": "emlis_product_gate_measurement_step3_joined_row_adapter",
        "source_step": COMPLETE_PRODUCT_QUALITY_MEASUREMENT_CONNECTION_STEP,
        "event_kind": "joined_observation_scorecard_event",
        "scorecard_event_adapter_ready": True,
        "row_id": _clean(source_row.get("row_id")) or _clean(source_row.get("trace_id")) or _clean(source_row.get("emotion_log_id")),
        "run_id": _clean(source_row.get("run_id")),
        "emotion_log_id": _clean(source_row.get("emotion_log_id")),
        "trace_id": _clean(source_row.get("trace_id")),
        "created_at": _clean(source_row.get("created_at")),
        "coverage_group": _clean(source_row.get("coverage_group")) or "coverage_group_missing",
        "eligible_for_scorecard": eligible,
        "eligible_count": 1 if eligible else 0,
        "candidate_generated_count": 1 if eligible and candidate_generated else 0,
        "complete_candidate_generated": candidate_generated,
        "passed_display_count": 1 if eligible and display_confirmed else 0,
        "scorecard_passed_display_count": 1 if eligible and display_confirmed else 0,
        "rejected_count": 1 if eligible and backend_status == "rejected" else 0,
        "unavailable_count": 1 if eligible and backend_status == "unavailable" else 0,
        "safety_blocked_count": 1 if eligible and backend_status == "safety_blocked" else 0,
        "observation_status": backend_status,
        "backend_observation_status": backend_status,
        "classification": classification,
        "measurement_classification": measurement_classification,
        "diagnostic_capture_status": diagnostic_capture_status,
        "backend_public_passed": backend_public_passed,
        "frontend_joined": frontend_joined,
        "frontend_join_status": _frontend_join_status(source_row, frontend_joined=frontend_joined),
        "frontend_public_passed": source_row.get("frontend_public_passed") is True,
        "modal_opened": source_row.get("modal_opened") if source_row.get("modal_opened") is None else _to_bool(source_row.get("modal_opened")),
        "display_confirmed": display_confirmed,
        "display_counting_rule": _clean(source_row.get("display_counting_rule")) or "display_confirmed_only",
        "display_count_blockers": _display_count_blockers(source_row),
        "product_gate_display_counted": bool(eligible and display_confirmed),
        "binding_supported_sentence_count": _count_from_any(
            source_row,
            "binding_supported_sentence_count",
            "binding_pass_count",
            "supported_sentence_count",
        ),
        "expected_binding_count": _count_from_any(
            source_row,
            "expected_binding_count",
            "binding_count",
            "sentence_count",
        ),
        "repair_attempt_count": 1 if repair_attempted else 0,
        "repair_success_count": 1 if repair_attempted and repair_success else 0,
        "repair_attempted": repair_attempted,
        "repair_success": repair_success,
        "template_major_count": _to_int(source_row.get("template_major_count"), 0),
        "safety_major_count": _to_int(source_row.get("safety_major_count"), 0),
        "top_rejection_reasons": reasons[:8],
        "reason_counter": dict(reason_counter),
        "machine_metrics_separated_from_blind_qa": True,
        "read_feeling_score": None,
        "read_feeling_source": "blind_qa_required_not_in_event",
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
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
        "public_release_applied": False,
    }
    assert_product_quality_measurement_connection_meta_only(event, source="scorecard_event")
    return event


def normalize_observation_rows_to_product_quality_events(
    rows: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None,
) -> list[dict[str, Any]]:
    return [normalize_observation_row_to_product_quality_event(row) for row in list(rows or [])]


def dump_product_quality_measurement_scorecard_event(event: Mapping[str, Any]) -> str:
    data = dict(event or {})
    data["raw_input_included"] = False
    data["raw_text_included"] = False
    data["comment_text_included"] = False
    assert_product_quality_measurement_connection_meta_only(data, source="scorecard_event")
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def dump_product_quality_measurement_connection_payload(payload: Mapping[str, Any]) -> str:
    data = dict(payload or {})
    data["raw_input_included"] = False
    data["raw_text_included"] = False
    data["comment_text_included"] = False
    assert_product_quality_measurement_connection_meta_only(data, source="measurement_connection_payload")
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _safe_first_non_empty(*values: Any) -> str:
    for value in values:
        text = _clean(value)
        if text:
            return text
    return ""


def _event_classification(event: Mapping[str, Any]) -> str:
    return _safe_first_non_empty(event.get("measurement_classification"), event.get("classification"))


def _capture_blockers_from_rows(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    blockers: list[str] = []
    if not rows:
        blockers.append("measurement_rows_missing")
    for row in rows:
        backend_capture = _clean(row.get("backend_diagnostic_capture_status"))
        frontend_capture = _clean(row.get("frontend_diagnostic_capture_status"))
        diagnostic_capture = _clean(row.get("diagnostic_capture_status"))
        if backend_capture == "backend_diagnostic_missing_or_not_captured":
            blockers.append("backend_diagnostic_missing_or_not_captured")
        if frontend_capture == "frontend_diagnostic_missing_or_not_captured":
            blockers.append("frontend_diagnostic_missing_or_not_captured")
        if diagnostic_capture == "backend_diagnostic_missing_or_not_captured":
            blockers.append("backend_diagnostic_missing_or_not_captured")
        if diagnostic_capture == "frontend_diagnostic_missing_or_not_captured":
            blockers.append("frontend_diagnostic_missing_or_not_captured")
        if diagnostic_capture == "diagnostic_log_missing_or_not_captured":
            blockers.append("diagnostic_log_missing_or_not_captured")
        if row.get("backend_public_passed") is True and row.get("frontend_joined") is not True:
            blockers.append("frontend_diagnostic_missing_or_not_captured")
    return _dedupe(blockers)


def _build_measurement_capture_summary(
    *,
    rows: Sequence[Mapping[str, Any]],
    events: Sequence[Mapping[str, Any]],
    run_id: str,
) -> dict[str, Any]:
    normalized_rows = [dict(row) for row in rows]
    normalized_events = [dict(event) for event in events]
    for row in normalized_rows:
        assert_product_quality_measurement_connection_meta_only(row, source="measurement_row")
    for event in normalized_events:
        assert_product_quality_measurement_connection_meta_only(event, source="measurement_event")

    backend_missing_count = sum(
        1
        for row in normalized_rows
        if _clean(row.get("backend_diagnostic_capture_status")) == "backend_diagnostic_missing_or_not_captured"
        or _clean(row.get("diagnostic_capture_status")) == "backend_diagnostic_missing_or_not_captured"
        or _event_classification(row) == "unknown_diagnostic_missing"
    )
    backend_diagnostic_count = max(0, len(normalized_rows) - backend_missing_count)
    frontend_diagnostic_count = sum(
        1
        for row in normalized_rows
        if row.get("frontend_joined") is True
        or _clean(row.get("frontend_diagnostic_capture_status")) == "captured"
    )
    joined_frontend_count = sum(1 for row in normalized_rows if row.get("frontend_joined") is True)
    unjoined_backend_count = sum(
        1
        for row in normalized_rows
        if _clean(row.get("backend_diagnostic_capture_status")) != "backend_diagnostic_missing_or_not_captured"
        and row.get("frontend_joined") is not True
    )
    backend_public_passed_count = sum(1 for event in normalized_events if event.get("backend_public_passed") is True)
    display_confirmed_count = sum(1 for event in normalized_events if event.get("display_confirmed") is True)
    scorecard_passed_display_count = sum(_to_int(event.get("scorecard_passed_display_count", event.get("passed_display_count")), 0) for event in normalized_events)
    blockers = _capture_blockers_from_rows(normalized_rows)
    backend_capture_status = "captured" if backend_diagnostic_count > 0 and "backend_diagnostic_missing_or_not_captured" not in blockers else "backend_diagnostic_missing_or_not_captured"
    frontend_capture_status = "captured" if (not normalized_rows or unjoined_backend_count == 0) and "frontend_diagnostic_missing_or_not_captured" not in blockers else "frontend_diagnostic_missing_or_not_captured"
    diagnostic_capture_status = "captured" if normalized_rows and not blockers else "diagnostic_log_missing_or_not_captured"

    join_semantics_summary = {
        "version": "emlis.backend_frontend_join_semantics.v1",
        "source": "emlis_product_gate_measurement_step4_join_semantics_summary",
        "row_count": len(normalized_rows),
        "backend_public_passed_count": backend_public_passed_count,
        "display_confirmed_count": display_confirmed_count,
        "scorecard_passed_display_count": scorecard_passed_display_count,
        "backend_public_passed_frontend_unconfirmed_count": sum(
            1 for event in normalized_events if event.get("backend_public_passed") is True and event.get("frontend_joined") is not True
        ),
        "passed_backend_frontend_hidden_count": sum(
            1 for event in normalized_events if event.get("backend_public_passed") is True and event.get("frontend_joined") is True and event.get("modal_opened") is False
        ),
        "display_counting_rule": "display_confirmed_only",
        "display_reach_rate_overestimation_guard": True,
        "raw_input_included": False,
        "comment_text_included": False,
    }
    summary = {
        "version": COMPLETE_PRODUCT_QUALITY_MEASUREMENT_CONNECTION_VERSION,
        "source": "emlis_product_gate_measurement_step4_capture_summary",
        "source_step": COMPLETE_PRODUCT_QUALITY_MEASUREMENT_RUN_BUILDER_STEP,
        "run_id": run_id,
        "diagnostic_capture_status": diagnostic_capture_status,
        "backend_diagnostic_capture_status": backend_capture_status,
        "frontend_diagnostic_capture_status": frontend_capture_status,
        "backend_diagnostic_count": backend_diagnostic_count,
        "frontend_diagnostic_count": frontend_diagnostic_count,
        "joined_frontend_count": joined_frontend_count,
        "unjoined_backend_count": unjoined_backend_count,
        "row_count": len(normalized_rows),
        "event_count": len(normalized_events),
        "eligible_event_count": sum(_to_int(event.get("eligible_count"), 0) for event in normalized_events),
        "backend_public_passed_count": backend_public_passed_count,
        "display_confirmed_count": display_confirmed_count,
        "scorecard_passed_display_count": scorecard_passed_display_count,
        "capture_blockers": blockers,
        "requires_diagnostic_enrichment": bool(blockers),
        "join_semantics_summary": join_semantics_summary,
        "raw_input_included": False,
        "comment_text_included": False,
    }
    assert_product_quality_measurement_connection_meta_only(summary, source="measurement_capture_summary")
    return summary


def _scorecard_machine_metrics(scorecard: Mapping[str, Any]) -> dict[str, Any]:
    return _safe_mapping(scorecard.get("machine_metrics"))


def _scorecard_coverage_group_rows(scorecard: Mapping[str, Any]) -> list[dict[str, Any]]:
    machine = _scorecard_machine_metrics(scorecard)
    rows = scorecard.get("coverage_group_rows") or machine.get("coverage_group_rows") or []
    return [dict(_safe_mapping(row)) for row in rows if _safe_mapping(row)]


def _scorecard_by_coverage_group(scorecard: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    machine = _scorecard_machine_metrics(scorecard)
    by_group = _safe_mapping(scorecard.get("by_coverage_group")) or _safe_mapping(machine.get("by_coverage_group"))
    return {str(group): dict(_safe_mapping(row)) for group, row in by_group.items() if _safe_mapping(row)}


def _build_measurement_coverage_group_summary(
    *,
    scorecard: Mapping[str, Any],
    events: Sequence[Mapping[str, Any]],
    run_id: str,
) -> dict[str, Any]:
    machine = _scorecard_machine_metrics(scorecard)
    by_group = _scorecard_by_coverage_group(scorecard)
    rows = _scorecard_coverage_group_rows(scorecard)
    observed = _dedupe(scorecard.get("observed_coverage_groups") or machine.get("observed_coverage_groups"))
    missing_groups = _dedupe(scorecard.get("missing_coverage_groups") or machine.get("missing_coverage_groups"))
    coverage_group_missing_count = _to_int(
        scorecard.get("coverage_group_missing_count", machine.get("coverage_group_missing_count")),
        0,
    )
    if COMPLETE_PRODUCT_QUALITY_COVERAGE_GROUP_MISSING in by_group:
        coverage_group_missing_count = max(
            coverage_group_missing_count,
            _to_int(by_group[COMPLETE_PRODUCT_QUALITY_COVERAGE_GROUP_MISSING].get("event_count"), 0),
        )
    summary = {
        "version": COMPLETE_PRODUCT_QUALITY_MEASUREMENT_CONNECTION_VERSION,
        "coverage_group_aggregation_version": COMPLETE_PRODUCT_QUALITY_COVERAGE_GROUP_AGGREGATION_VERSION,
        "source": "emlis_product_gate_measurement_step5_coverage_group_summary",
        "source_step": COMPLETE_PRODUCT_QUALITY_MEASUREMENT_COVERAGE_GROUP_STEP,
        "run_id": run_id,
        "coverage_group_aggregation_ready": True,
        "required_coverage_groups": list(COMPLETE_COVERAGE_GROUP_ORDER),
        "observed_coverage_groups": observed,
        "missing_coverage_groups": missing_groups,
        "coverage_group_count": len([group for group in observed if group in COMPLETE_COVERAGE_GROUP_ORDER]),
        "coverage_group_missing_count": coverage_group_missing_count,
        "coverage_group_missing_blocker": coverage_group_missing_count > 0,
        "required_coverage_groups_complete": not missing_groups and coverage_group_missing_count == 0,
        "by_coverage_group": by_group,
        "coverage_group_rows": rows,
        "event_count": len(events),
        "broader_beta_blocked_by_coverage": bool(missing_groups or coverage_group_missing_count > 0),
        "product_gate_blocked_by_coverage": bool(missing_groups or coverage_group_missing_count > 0),
        "raw_input_included": False,
        "comment_text_included": False,
    }
    assert_product_quality_measurement_connection_meta_only(summary, source="measurement_coverage_group_summary")
    return summary


def _blind_qa_candidate_from_event(event: Mapping[str, Any], *, index: int) -> dict[str, Any]:
    candidate_id = (
        _clean(event.get("row_id"))
        or _clean(event.get("trace_id"))
        or _clean(event.get("emotion_log_id"))
        or f"candidate-{index}"
    )
    classification = _safe_first_non_empty(event.get("measurement_classification"), event.get("classification"))
    public_passed = bool(event.get("display_confirmed") is True and event.get("backend_public_passed") is True)
    candidate = {
        "version": COMPLETE_PRODUCT_QUALITY_MEASUREMENT_CONNECTION_VERSION,
        "source": "emlis_product_gate_measurement_step6_blind_qa_candidate",
        "source_step": COMPLETE_PRODUCT_QUALITY_MEASUREMENT_BLIND_QA_STEP,
        "candidate_kind": "blind_qa_input_candidate_meta",
        "candidate_index": index,
        "candidate_id": candidate_id,
        "row_id": _clean(event.get("row_id")),
        "run_id": _clean(event.get("run_id")),
        "emotion_log_id": _clean(event.get("emotion_log_id")),
        "trace_id": _clean(event.get("trace_id")),
        "coverage_group": _clean(event.get("coverage_group")) or COMPLETE_PRODUCT_QUALITY_COVERAGE_GROUP_MISSING,
        "classification": classification,
        "measurement_classification": _clean(event.get("measurement_classification")) or classification,
        "observation_status": _clean(event.get("observation_status")),
        "eligible_for_scorecard": bool(event.get("eligible_for_scorecard") or _to_int(event.get("eligible_count"), 0) > 0),
        "backend_public_passed": event.get("backend_public_passed") is True,
        "frontend_joined": event.get("frontend_joined") is True,
        "modal_opened": event.get("modal_opened") is True,
        "display_confirmed": event.get("display_confirmed") is True,
        "public_passed": public_passed,
        "public_passed_for_blind_qa": public_passed,
        "public_pass_source": "display_confirmed",
        "reviewable_for_blind_qa": public_passed,
        "blind_qa_review_required": public_passed,
        "ratings_required": list(_BLIND_QA_REQUIRED_DIMENSIONS),
        "read_feeling_source": "blind_qa_review_only",
        "read_feeling_score": None,
        "machine_read_feeling_score": None,
        "machine_metrics_read_feeling_score": None,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_estimation_allowed": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
    }
    assert_product_quality_measurement_connection_meta_only(candidate, source="blind_qa_input_candidate")
    return candidate


def build_complete_product_quality_blind_qa_input_candidates(
    events: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for index, event in enumerate(list(events or []), start=1):
        event_data = dict(event or {})
        assert_product_quality_measurement_connection_meta_only(event_data, source="blind_qa_candidate_source_event")
        candidates.append(_blind_qa_candidate_from_event(event_data, index=index))
    return candidates


def assert_product_quality_measurement_blind_qa_reviews_meta_only(
    reviews: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None,
) -> None:
    for index, review in enumerate(list(reviews or [])):
        assert_product_quality_measurement_connection_meta_only(dict(review or {}), source=f"blind_qa_review[{index}]")


def _build_blind_qa_separation_summary(
    *,
    candidates: Sequence[Mapping[str, Any]],
    scorecard: Mapping[str, Any],
    run_id: str,
) -> dict[str, Any]:
    blind_metrics = _safe_mapping(scorecard.get("blind_qa_metrics"))
    machine_metrics = _safe_mapping(scorecard.get("machine_metrics"))
    review_count = _to_int(blind_metrics.get("review_count"), 0)
    reviewable_count = sum(1 for candidate in candidates if candidate.get("reviewable_for_blind_qa") is True)
    summary = {
        "version": COMPLETE_PRODUCT_QUALITY_MEASUREMENT_CONNECTION_VERSION,
        "source": "emlis_product_gate_measurement_step6_blind_qa_separation_summary",
        "source_step": COMPLETE_PRODUCT_QUALITY_MEASUREMENT_BLIND_QA_STEP,
        "run_id": run_id,
        "blind_qa_separation_ready": True,
        "blind_qa_required": True,
        "read_feeling_requires_blind_qa": True,
        "machine_metrics_separated_from_blind_qa": True,
        "machine_metrics_and_blind_qa_separated": True,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_estimation_allowed": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_source": _clean(scorecard.get("read_feeling_source")) or "not_evaluated",
        "read_feeling_score": scorecard.get("read_feeling_score"),
        "machine_read_feeling_score": machine_metrics.get("read_feeling_score"),
        "machine_metrics_read_feeling_score": machine_metrics.get("read_feeling_score"),
        "blind_qa_ready": bool(scorecard.get("blind_qa_ready") or blind_metrics.get("blind_qa_ready")),
        "blind_qa_missing": not bool(scorecard.get("blind_qa_ready") or blind_metrics.get("blind_qa_ready")),
        "blind_qa_candidate_count": len(candidates),
        "reviewable_candidate_count": reviewable_count,
        "non_reviewable_candidate_count": max(0, len(candidates) - reviewable_count),
        "display_confirmed_candidate_count": sum(1 for candidate in candidates if candidate.get("display_confirmed") is True),
        "public_passed_candidate_count": sum(1 for candidate in candidates if candidate.get("public_passed") is True),
        "blind_qa_review_count": review_count,
        "reviewed_candidate_count": min(review_count, reviewable_count),
        "unreviewed_reviewable_candidate_count": max(0, reviewable_count - review_count),
        "blind_qa_missing_count": max(0, reviewable_count - review_count),
        "candidate_ids": [_clean(candidate.get("candidate_id")) for candidate in candidates if _clean(candidate.get("candidate_id"))],
        "reviewable_candidate_ids": [
            _clean(candidate.get("candidate_id"))
            for candidate in candidates
            if candidate.get("reviewable_for_blind_qa") is True and _clean(candidate.get("candidate_id"))
        ],
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
    }
    assert_product_quality_measurement_connection_meta_only(summary, source="blind_qa_separation_summary")
    return summary


def _collect_release_blockers(
    *,
    capture_summary: Mapping[str, Any],
    scorecard: Mapping[str, Any],
    release_ladder: Mapping[str, Any],
) -> list[str]:
    blockers: list[str] = []
    blockers.extend(_dedupe(capture_summary.get("capture_blockers")))
    blockers.extend(_dedupe(scorecard.get("release_blockers")))
    if _to_int(scorecard.get("coverage_group_missing_count"), 0) > 0:
        blockers.append("coverage_group_missing")
    if _dedupe(scorecard.get("missing_coverage_groups")):
        blockers.append("coverage_groups_incomplete")
    blockers.extend(_dedupe(release_ladder.get("release_blockers")))
    blockers.extend(_dedupe(release_ladder.get("ladder_blockers")))
    stage_evaluations = _safe_mapping(release_ladder.get("stage_evaluations"))
    for stage in ("internal", "limited", "broader_beta", "product_gate"):
        stage_payload = _safe_mapping(stage_evaluations.get(stage))
        blockers.extend(_dedupe(stage_payload.get("blockers")))
    return _dedupe(blockers)


def _normalize_routing_classification(value: Any) -> str:
    classification = _clean(value)
    if not classification:
        return ""
    classification = _CLASSIFICATION_ROUTING_ALIASES.get(classification, classification)
    if classification in _BRANCH_KNOWN_CLASSIFICATIONS:
        return classification
    return "unclassified_non_display"


def _event_routing_classification(event: Mapping[str, Any]) -> str:
    classification = _normalize_routing_classification(_event_classification(event))
    if classification:
        return classification
    if event.get("backend_public_passed") is True and event.get("frontend_joined") is not True:
        return "unknown_diagnostic_missing"
    if event.get("backend_public_passed") is True and event.get("frontend_joined") is True and event.get("modal_opened") is False:
        return "passed_backend_frontend_hidden"
    if event.get("display_confirmed") is True:
        return "passed_displayed"
    return "unclassified_non_display"


def _classification_counter_for_next_action(events: Sequence[Mapping[str, Any]]) -> tuple[Counter[str], dict[str, int]]:
    counter: Counter[str] = Counter()
    first_seen: dict[str, int] = {}
    for index, event in enumerate(events):
        classification = _event_routing_classification(event)
        if not classification or classification == "passed_displayed":
            continue
        counter[classification] += 1
        first_seen.setdefault(classification, index)
    return counter, first_seen


def _most_frequent_classification(counter: Counter[str], first_seen: Mapping[str, int]) -> str:
    if not counter:
        return ""
    ranked = sorted(counter.items(), key=lambda item: (-item[1], first_seen.get(item[0], 10**9), item[0]))
    return ranked[0][0]


def _scorecard_top_rejection_reasons(scorecard: Mapping[str, Any]) -> list[str]:
    machine = _safe_mapping(scorecard.get("machine_metrics"))
    reasons: list[str] = []
    reasons.extend(_dedupe(scorecard.get("top_rejection_reasons")))
    reasons.extend(_dedupe(machine.get("top_rejection_reasons")))
    reasons.extend(_dedupe(scorecard.get("release_blockers")))
    return _dedupe(reasons)


def _event_top_rejection_reasons(events: Sequence[Mapping[str, Any]]) -> list[str]:
    reasons: list[str] = []
    for event in events:
        classification = _event_routing_classification(event)
        if classification and classification != "passed_displayed":
            reasons.append(classification)
        reasons.extend(_dedupe(event.get("top_rejection_reasons")))
        reasons.extend(_dedupe(event.get("display_count_blockers")))
    return _dedupe(reasons)


def _classification_hint_from_reason(value: Any) -> str:
    reason = _clean(value)
    if not reason:
        return ""
    if reason in _RELEASE_BLOCKER_CLASSIFICATION_HINTS:
        return _RELEASE_BLOCKER_CLASSIFICATION_HINTS[reason]
    lower_reason = reason.lower()
    if lower_reason in _RELEASE_BLOCKER_CLASSIFICATION_HINTS:
        return _RELEASE_BLOCKER_CLASSIFICATION_HINTS[lower_reason]
    for prefix, classification in _RELEASE_BLOCKER_CLASSIFICATION_PREFIX_HINTS:
        if lower_reason.startswith(prefix):
            return classification
    return ""


def _first_classification_hint(values: Sequence[Any]) -> tuple[str, str]:
    for value in _dedupe(values):
        classification = _classification_hint_from_reason(value)
        if classification:
            return classification, _clean(value)
    return "", ""


def _first_diagnostic_capture_blocker(values: Sequence[Any]) -> str:
    for blocker in _dedupe(values):
        if _clean(blocker) in _DIAGNOSTIC_CAPTURE_BLOCKERS:
            return _clean(blocker)
    return ""


def _measured_surface_or_tone_issue(
    *,
    classification: str,
    selected_reason: str,
    selected_release_blocker: str,
    top_rejection_reasons: Sequence[str],
) -> bool:
    markers = set(_MEASURED_SURFACE_OR_TONE_REASON_MARKERS)
    if classification in markers or selected_reason in markers or selected_release_blocker in markers:
        return True
    return any(_clean(reason) in markers for reason in top_rejection_reasons)


def _first_divergence_layer_for_classification(classification: str) -> str:
    mapping = {
        "backend_exception_or_timeout": "backend_exception_or_timeout",
        "pre_connection_stop": "pre_connection",
        "candidate_missing": "candidate",
        "candidate_generated_but_reader_rejected": "reader",
        "candidate_generated_but_grounding_rejected": "grounding",
        "candidate_generated_but_template_rejected": "template",
        "candidate_generated_but_display_rejected": "display",
        "passed_backend_frontend_hidden": "frontend",
        "passed_displayed": "passed",
        "unclassified_non_display": "diagnostic",
        "unknown_diagnostic_missing": "diagnostic",
    }
    return mapping.get(classification, "diagnostic")


def build_complete_product_quality_measurement_next_action_routing_summary(
    *,
    capture_summary: Mapping[str, Any],
    events: Sequence[Mapping[str, Any]],
    scorecard: Mapping[str, Any] | None = None,
    release_blockers: Sequence[Any] | None = None,
    run_id: str = "",
) -> dict[str, Any]:
    normalized_events = [dict(event or {}) for event in events]
    for event in normalized_events:
        assert_product_quality_measurement_connection_meta_only(event, source="next_action_routing_event")
    scorecard_data = dict(scorecard or {})
    assert_product_quality_measurement_connection_meta_only(scorecard_data, source="next_action_routing_scorecard")
    capture = dict(capture_summary or {})
    assert_product_quality_measurement_connection_meta_only(capture, source="next_action_routing_capture")

    capture_blockers = _dedupe(capture.get("capture_blockers"))
    blockers = _dedupe([*capture_blockers, *(release_blockers or [])])
    top_rejection_reasons = _dedupe([
        *_scorecard_top_rejection_reasons(scorecard_data),
        *_event_top_rejection_reasons(normalized_events),
    ])
    counter, first_seen = _classification_counter_for_next_action(normalized_events)
    diagnostic_blocker = _first_diagnostic_capture_blocker(blockers)
    selected_release_blocker = ""
    selected_top_reason = ""
    routing_basis = ""

    if diagnostic_blocker or capture.get("requires_diagnostic_enrichment") is True:
        classification = "unknown_diagnostic_missing"
        selected_release_blocker = diagnostic_blocker or (capture_blockers[0] if capture_blockers else "requires_diagnostic_enrichment")
        routing_basis = "diagnostic_capture_gap"
    else:
        most_frequent = _most_frequent_classification(counter, first_seen)
        if most_frequent:
            classification = most_frequent
            routing_basis = "most_frequent_classification"
        else:
            classification, selected_release_blocker = _first_classification_hint(blockers)
            if classification:
                routing_basis = "first_release_blocker"
            else:
                classification, selected_top_reason = _first_classification_hint(top_rejection_reasons)
                if classification:
                    routing_basis = "top_rejection_reason"
                elif normalized_events:
                    classification = "passed_displayed"
                    routing_basis = "displayed_scorecard_coverage_blind_qa"
                else:
                    classification = "unknown_diagnostic_missing"
                    selected_release_blocker = "measurement_rows_missing"
                    routing_basis = "diagnostic_capture_gap"

    classification = _normalize_routing_classification(classification) or "unknown_diagnostic_missing"
    selected_top_reason = selected_top_reason or (top_rejection_reasons[0] if top_rejection_reasons else "")
    measured_surface_or_tone_issue = _measured_surface_or_tone_issue(
        classification=classification,
        selected_reason=selected_top_reason,
        selected_release_blocker=selected_release_blocker,
        top_rejection_reasons=top_rejection_reasons,
    )
    passed_only = bool(normalized_events) and not counter and all(_event_routing_classification(event) == "passed_displayed" for event in normalized_events)
    summary = {
        "version": COMPLETE_PRODUCT_QUALITY_MEASUREMENT_CONNECTION_VERSION,
        "source": "emlis_product_gate_measurement_step7_next_action_routing",
        "source_step": COMPLETE_PRODUCT_QUALITY_MEASUREMENT_NEXT_ACTION_ROUTING_STEP,
        "next_action_routing_ready": True,
        "run_id": _clean(run_id or capture.get("run_id")),
        "routing_basis": routing_basis,
        "classification": classification,
        "selected_classification": classification,
        "classification_counter": dict(counter),
        "classification_first_seen_index": dict(first_seen),
        "selected_release_blocker": selected_release_blocker,
        "selected_top_rejection_reason": selected_top_reason,
        "release_blockers_considered": blockers,
        "top_rejection_reasons_considered": top_rejection_reasons,
        "passed_displayed_only": passed_only,
        "unknown_or_unclassified_returns_to_diagnostic_enrichment": classification in {"unknown_diagnostic_missing", "unclassified_non_display"},
        "classification_decided_before_cause_repair": True,
        "tone_or_surface_routing_requires_measured_issue": True,
        "measured_surface_or_tone_issue": measured_surface_or_tone_issue,
        "surface_or_tone_jump_blocked_without_measured_issue": not measured_surface_or_tone_issue,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
    }
    assert_product_quality_measurement_connection_meta_only(summary, source="next_action_routing_summary")
    return summary


def _build_measurement_next_action_branch(
    *,
    capture_summary: Mapping[str, Any],
    events: Sequence[Mapping[str, Any]],
    scorecard: Mapping[str, Any],
    release_blockers: Sequence[Any],
    run_id: str,
) -> dict[str, Any]:
    routing = build_complete_product_quality_measurement_next_action_routing_summary(
        capture_summary=capture_summary,
        events=events,
        scorecard=scorecard,
        release_blockers=release_blockers,
        run_id=run_id,
    )
    classification = _clean(routing.get("classification")) or "unknown_diagnostic_missing"
    branch = resolve_observation_diagnostic_next_branch(
        {
            "classification": classification,
            "raw_input_included": False,
            "comment_text_included": False,
        },
        first_divergence_layer=_first_divergence_layer_for_classification(classification),
    )
    branch.update(
        {
            "measurement_next_action_routing_ready": True,
            "source_step": COMPLETE_PRODUCT_QUALITY_MEASUREMENT_NEXT_ACTION_ROUTING_STEP,
            "routing_basis": routing.get("routing_basis"),
            "selected_release_blocker": routing.get("selected_release_blocker"),
            "selected_top_rejection_reason": routing.get("selected_top_rejection_reason"),
            "classification_counter": routing.get("classification_counter"),
            "release_blockers_considered": routing.get("release_blockers_considered"),
            "top_rejection_reasons_considered": routing.get("top_rejection_reasons_considered"),
            "passed_displayed_only": routing.get("passed_displayed_only"),
            "classification_decided_before_cause_repair": True,
            "tone_or_surface_routing_requires_measured_issue": True,
            "measured_surface_or_tone_issue": routing.get("measured_surface_or_tone_issue"),
            "surface_or_tone_jump_blocked_without_measured_issue": routing.get("surface_or_tone_jump_blocked_without_measured_issue"),
            "routing_summary": routing,
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_included": False,
        }
    )
    assert_product_quality_measurement_connection_meta_only(branch, source="next_action_branch")
    return branch



def _measurement_public_contract_unchanged(report: Mapping[str, Any]) -> bool:
    """Return true when Step10 did not mutate public API/RN/DB/Gate contracts."""

    return all(
        report.get(key) is not True
        for key in (
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
            "product_gate_public_release_applied",
            "product_quality_released",
        )
    )


def _exit_gate_fixture_class_for_event(event: Mapping[str, Any]) -> str:
    classification = _event_routing_classification(event)
    diagnostic_status = _clean(event.get("diagnostic_capture_status"))
    backend_status = _clean(event.get("backend_observation_status") or event.get("observation_status"))
    blockers = set(_dedupe(event.get("display_count_blockers"))) | set(_dedupe(event.get("top_rejection_reasons")))

    if (
        classification == "unknown_diagnostic_missing"
        or diagnostic_status in _DIAGNOSTIC_CAPTURE_BLOCKERS
        or bool(blockers & _DIAGNOSTIC_CAPTURE_BLOCKERS)
    ):
        return "diagnostic_missing"
    if classification == "passed_backend_frontend_hidden":
        return "passed_backend_frontend_hidden"
    if (
        event.get("backend_public_passed") is True
        and event.get("frontend_joined") is True
        and event.get("modal_opened") is False
    ):
        return "passed_backend_frontend_hidden"
    if event.get("display_confirmed") is True:
        return "display_confirmed"
    if backend_status == "rejected" or classification.endswith("_rejected"):
        return "backend_rejected"
    return "other_measured_submit"


def _observed_exit_gate_fixture_classes(events: Sequence[Mapping[str, Any]]) -> list[str]:
    return _dedupe([_exit_gate_fixture_class_for_event(event) for event in events])


def build_complete_product_quality_measurement_exit_gate_summary(report: Mapping[str, Any]) -> dict[str, Any]:
    """Build Step10 Exit Gate summary for one measurement report.

    Step10 confirms the measurement connection, not Product Gate achievement.
    It requires submit-level measurement fields, scorecard event wiring,
    aggregate scorecard/release ladder connection, next-action routing, and a
    closed public-release boundary. Minimum fixture coverage is reported for
    regression, but a single local measurement report may still be connected
    without covering all fixture classes.
    """

    data = dict(report or {})
    assert_product_quality_measurement_connection_meta_only(data, source="measurement_exit_gate_report")
    events = [dict(_safe_mapping(event)) for event in data.get("scorecard_events") or [] if _safe_mapping(event)]
    for event in events:
        assert_product_quality_measurement_connection_meta_only(event, source="measurement_exit_gate_event")

    capture = _safe_mapping(data.get("capture_summary"))
    scorecard = _safe_mapping(data.get("scorecard") or data.get("product_quality_scorecard"))
    release_ladder = _safe_mapping(data.get("release_ladder"))
    next_branch = _safe_mapping(data.get("next_action_branch") or data.get("next_branch"))
    observed_fixture_classes = _observed_exit_gate_fixture_classes(events)
    required_fixture_classes = list(COMPLETE_PRODUCT_QUALITY_MEASUREMENT_EXIT_GATE_REQUIRED_FIXTURE_CLASSES)
    missing_fixture_classes = [item for item in required_fixture_classes if item not in set(observed_fixture_classes)]

    row_count = _to_int(data.get("row_count"), 0)
    event_count = len(events)
    submit_level_event_fields_ready = bool(
        event_count > 0
        and all(
            _safe_first_non_empty(event.get("row_id"), event.get("trace_id"), event.get("emotion_log_id"))
            and _safe_first_non_empty(event.get("diagnostic_capture_status"), capture.get("diagnostic_capture_status"))
            and _safe_first_non_empty(event.get("measurement_classification"), event.get("classification"))
            and "display_confirmed" in event
            and event.get("scorecard_event_adapter_ready") is True
            for event in events
        )
    )
    scorecard_event_connection_ready = bool(
        event_count > 0
        and event_count == _to_int(data.get("scorecard_event_count"), event_count)
        and all(event.get("scorecard_event_adapter_ready") is True for event in events)
    )
    display_counting_rule_locked = bool(
        data.get("scorecard_passed_display_count") == data.get("passed_display_count")
        and data.get("display_confirmed_count") == data.get("scorecard_passed_display_count")
        and all(
            _to_int(event.get("passed_display_count"), 0)
            == (1 if event.get("display_confirmed") is True and event.get("eligible_for_scorecard") is True else 0)
            for event in events
        )
    )
    aggregate_scorecard_connected = bool(
        data.get("scorecard_ready") is True
        and data.get("scorecard_connected") is True
        and (scorecard.get("scorecard_ready") is True or scorecard.get("product_quality_scorecard_ready") is True)
    )
    release_ladder_connected = bool(
        data.get("release_ladder_connected") is True
        and release_ladder.get("release_ladder_connected") is True
    )
    next_action_routing_connected = bool(
        data.get("next_action_routing_ready") is True
        and next_branch.get("measurement_next_action_routing_ready") is True
        and bool(_clean(next_branch.get("classification")))
    )
    public_contract_unchanged = _measurement_public_contract_unchanged(data)
    product_release_closed = bool(
        data.get("product_gate_ready") is False
        and data.get("product_gate_reached") is False
        and data.get("product_gate_achieved") is False
        and data.get("product_gate_public_release_applied") is False
        and data.get("public_release_applied") is False
        and data.get("product_quality_released") is False
        and release_ladder.get("product_gate_public_release_applied") is not True
        and release_ladder.get("public_release_applied") is not True
        and release_ladder.get("product_quality_released") is not True
    )
    exit_gate_checks = {
        "row_or_diagnostic_fixture_available": row_count > 0,
        "scorecard_event_adapter_connected": scorecard_event_connection_ready,
        "capture_status_available": bool(capture.get("diagnostic_capture_status") or row_count > 0),
        "classification_available": bool(
            event_count > 0
            and all(_safe_first_non_empty(event.get("measurement_classification"), event.get("classification")) for event in events)
        ),
        "display_confirmed_count_available": "display_confirmed_count" in data,
        "submit_level_event_fields_ready": submit_level_event_fields_ready,
        "aggregate_scorecard_connected": aggregate_scorecard_connected,
        "release_ladder_connected": release_ladder_connected,
        "next_action_routing_connected": next_action_routing_connected,
        "display_counting_rule_locked": display_counting_rule_locked,
        "public_contract_unchanged": public_contract_unchanged,
        "product_release_closed": product_release_closed,
    }
    exit_gate_blockers = [name for name, passed in exit_gate_checks.items() if not passed]
    measurement_exit_gate_completed = not exit_gate_blockers
    product_gate_candidate_ready = bool(
        release_ladder.get("product_gate_candidate_ready")
        or release_ladder.get("product_gate_transition_allowed")
    )

    summary = {
        "version": COMPLETE_PRODUCT_QUALITY_MEASUREMENT_CONNECTION_VERSION,
        "source": "emlis_product_gate_measurement_step10_exit_gate",
        "source_step": COMPLETE_PRODUCT_QUALITY_MEASUREMENT_EXIT_GATE_STEP,
        "step": COMPLETE_PRODUCT_QUALITY_MEASUREMENT_EXIT_GATE_STEP,
        "run_id": _clean(data.get("run_id")),
        "exit_gate_summary_ready": True,
        "exit_gate_ready": measurement_exit_gate_completed,
        "measurement_exit_gate_ready": measurement_exit_gate_completed,
        "measurement_exit_gate_completed": measurement_exit_gate_completed,
        "measurement_connection_complete": measurement_exit_gate_completed,
        "measurement_connection_completed": measurement_exit_gate_completed,
        "product_gate_measurement_connection_complete": measurement_exit_gate_completed,
        "measurement_connection_only": True,
        "not_product_gate_achievement": True,
        "measurement_connection_complete_not_product_gate_achieved": True,
        "product_gate_candidate_ready": product_gate_candidate_ready,
        "product_gate_candidate_ready_but_public_release_not_applied": product_gate_candidate_ready,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "product_gate_achieved": False,
        "product_gate_public_release_applied": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "row_count": row_count,
        "event_count": event_count,
        "scorecard_event_connection_ready": scorecard_event_connection_ready,
        "scorecard_event_adapter_connected": scorecard_event_connection_ready,
        "submit_level_event_fields_ready": submit_level_event_fields_ready,
        "aggregate_scorecard_connected": aggregate_scorecard_connected,
        "release_ladder_connected": release_ladder_connected,
        "scorecard_connected_to_release_ladder": bool(aggregate_scorecard_connected and release_ladder_connected),
        "next_action_routing_connected": next_action_routing_connected,
        "display_counting_rule_locked": display_counting_rule_locked,
        "display_counting_rule": "display_confirmed_only",
        "next_step_from_top_rejection_reasons_ready": next_action_routing_connected,
        "public_contract_unchanged": public_contract_unchanged,
        "product_release_closed": product_release_closed,
        "diagnostic_capture_status": capture.get("diagnostic_capture_status"),
        "capture_status_available": bool(_clean(capture.get("diagnostic_capture_status"))),
        "classification_available": bool(event_count > 0 and all(_safe_first_non_empty(event.get("measurement_classification"), event.get("classification")) for event in events)),
        "display_confirmed_count_available": "display_confirmed_count" in data,
        "classification_counter": next_branch.get("classification_counter") or {},
        "next_action_classification": next_branch.get("classification"),
        "next_action_layer": next_branch.get("target_layer"),
        "top_rejection_reasons": _dedupe(_scorecard_top_rejection_reasons(scorecard) + _event_top_rejection_reasons(events)),
        "release_blockers": _dedupe(data.get("release_blockers")),
        "required_fixture_classes": required_fixture_classes,
        "observed_fixture_classes": observed_fixture_classes,
        "missing_fixture_classes": missing_fixture_classes,
        "minimum_fixture_coverage_ready": not missing_fixture_classes,
        "minimum_fixture_coverage_complete": not missing_fixture_classes,
        "fixture_coverage_required_for_regression": True,
        "unknown_or_unclassified_returns_to_diagnostic_enrichment": bool(
            next_branch.get("classification") in {"unknown_diagnostic_missing", "unclassified_non_display"}
            or next_branch.get("requires_diagnostic_enrichment") is True
        ),
        "next_action_from_top_reasons_or_classification": next_branch.get("routing_basis") in {
            "diagnostic_capture_gap",
            "most_frequent_classification",
            "first_release_blocker",
            "top_rejection_reason",
            "displayed_scorecard_coverage_blind_qa",
        },
        "next_step_from_top_rejection_reasons_ready": next_action_routing_connected,
        "next_action_reason_source_order": [
            "diagnostic_capture_gap",
            "classification_counter",
            "release_blockers",
            "top_rejection_reasons",
        ],
        "exit_gate_checks": exit_gate_checks,
        "exit_gate_blockers": exit_gate_blockers,
        "measurement_connection_complete_not_product_gate_achieved": measurement_exit_gate_completed,
        "exit_gate_decision": (
            "measurement_connection_complete_public_release_closed"
            if measurement_exit_gate_completed
            else "measurement_connection_incomplete_or_public_release_guard_failed"
        ),
        "release_judgment": {
            "release_allowed": False,
            "reason": "step10_exit_gate_measurement_connection_only_public_release_not_applied",
        },
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
    }
    assert_product_quality_measurement_connection_meta_only(summary, source="measurement_exit_gate_summary")
    return summary


def build_complete_product_quality_measurement_connection(
    *,
    rows: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None,
    blind_qa_reviews: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None = None,
    run_id: str = "",
) -> dict[str, Any]:
    """Build one internal Step4 ProductGate measurement report.

    The report connects joined diagnostic rows to ProductQualityScorecard and
    release ladder outputs.  It never writes public comment text, never changes
    public response/RN/DB contracts, and never applies public release.  Display
    counts are inherited from Step2/Step3: only ``display_confirmed`` can count
    as ``passed_display_count``.
    """

    normalized_rows = [dict(row) for row in list(rows or [])]
    for row in normalized_rows:
        assert_product_quality_measurement_connection_meta_only(row, source="measurement_connection_row")
    clean_run_id = _clean(run_id)
    blind_qa_review_records = list(blind_qa_reviews or [])
    assert_product_quality_measurement_blind_qa_reviews_meta_only(blind_qa_review_records)
    events = normalize_observation_rows_to_product_quality_events(normalized_rows)
    blind_qa_input_candidates = build_complete_product_quality_blind_qa_input_candidates(events)
    capture_summary = _build_measurement_capture_summary(rows=normalized_rows, events=events, run_id=clean_run_id)
    scorecard = build_complete_product_quality_scorecard(
        scorecard_events=events,
        blind_qa_reviews=blind_qa_review_records,
    )
    release_ladder = build_complete_product_quality_release_ladder(
        product_quality_scorecard=scorecard,
        diagnostic_summary=capture_summary,
    )
    coverage_group_summary = _build_measurement_coverage_group_summary(
        scorecard=scorecard,
        events=events,
        run_id=clean_run_id,
    )
    blind_qa_separation_summary = _build_blind_qa_separation_summary(
        candidates=blind_qa_input_candidates,
        scorecard=scorecard,
        run_id=clean_run_id,
    )
    release_blockers = _collect_release_blockers(
        capture_summary=capture_summary,
        scorecard=scorecard,
        release_ladder=release_ladder,
    )
    next_action_branch = _build_measurement_next_action_branch(
        capture_summary=capture_summary,
        events=events,
        scorecard=scorecard,
        release_blockers=release_blockers,
        run_id=clean_run_id,
    )
    next_action_routing_summary = _safe_mapping(next_action_branch.get("routing_summary"))
    report = {
        "version": COMPLETE_PRODUCT_QUALITY_MEASUREMENT_CONNECTION_VERSION,
        "measurement_connection_version": COMPLETE_PRODUCT_QUALITY_MEASUREMENT_CONNECTION_VERSION,
        "source": "emlis_product_gate_measurement_step4_run_builder",
        "source_step": COMPLETE_PRODUCT_QUALITY_MEASUREMENT_RUN_BUILDER_STEP,
        "step": COMPLETE_PRODUCT_QUALITY_MEASUREMENT_RUN_BUILDER_STEP,
        "measurement_latest_step": COMPLETE_PRODUCT_QUALITY_MEASUREMENT_EXIT_GATE_STEP,
        "blind_qa_separation_step": COMPLETE_PRODUCT_QUALITY_MEASUREMENT_BLIND_QA_STEP,
        "next_action_routing_step": COMPLETE_PRODUCT_QUALITY_MEASUREMENT_NEXT_ACTION_ROUTING_STEP,
        "exit_gate_step": COMPLETE_PRODUCT_QUALITY_MEASUREMENT_EXIT_GATE_STEP,
        "run_id": clean_run_id,
        "measurement_run_builder_ready": True,
        "measurement_report_ready": True,
        "scorecard_ready": bool(scorecard.get("scorecard_ready") or scorecard.get("product_quality_scorecard_ready")),
        "scorecard_connected": bool(scorecard.get("scorecard_ready") or scorecard.get("product_quality_scorecard_ready")),
        "release_ladder_connected": bool(release_ladder.get("release_ladder_connected")),
        "row_count": len(normalized_rows),
        "event_count": len(events),
        "scorecard_event_count": len(events),
        "scorecard_events": events,
        "capture_summary": capture_summary,
        "join_semantics_summary": capture_summary.get("join_semantics_summary"),
        "scorecard": scorecard,
        "product_quality_scorecard": scorecard,
        "release_ladder": release_ladder,
        "coverage_group_summary": coverage_group_summary,
        "coverage_group_aggregation_ready": coverage_group_summary.get("coverage_group_aggregation_ready"),
        "blind_qa_separation_summary": blind_qa_separation_summary,
        "blind_qa_separation_ready": blind_qa_separation_summary.get("blind_qa_separation_ready"),
        "blind_qa_required": True,
        "read_feeling_requires_blind_qa": True,
        "read_feeling_auto_estimation_allowed": False,
        "machine_metrics_separated_from_blind_qa": True,
        "machine_metrics_and_blind_qa_separated": True,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_source": scorecard.get("read_feeling_source"),
        "read_feeling_score": scorecard.get("read_feeling_score"),
        "machine_read_feeling_score": blind_qa_separation_summary.get("machine_read_feeling_score"),
        "machine_metrics_read_feeling_score": blind_qa_separation_summary.get("machine_metrics_read_feeling_score"),
        "blind_qa_ready": blind_qa_separation_summary.get("blind_qa_ready"),
        "blind_qa_missing": blind_qa_separation_summary.get("blind_qa_missing"),
        "blind_qa_input_candidates": blind_qa_input_candidates,
        "blind_qa_candidate_summary": blind_qa_separation_summary,
        "blind_qa_candidate_count": blind_qa_separation_summary.get("blind_qa_candidate_count", 0),
        "blind_qa_public_passed_candidate_count": blind_qa_separation_summary.get("public_passed_candidate_count", 0),
        "blind_qa_review_count": blind_qa_separation_summary.get("blind_qa_review_count", 0),
        "reviewable_blind_qa_candidate_count": blind_qa_separation_summary.get("reviewable_candidate_count", 0),
        "unreviewed_reviewable_candidate_count": blind_qa_separation_summary.get("unreviewed_reviewable_candidate_count", 0),
        "blind_qa_missing_count": blind_qa_separation_summary.get("blind_qa_missing_count", 0),
        "coverage_group_rows": coverage_group_summary.get("coverage_group_rows"),
        "by_coverage_group": coverage_group_summary.get("by_coverage_group"),
        "required_coverage_groups": coverage_group_summary.get("required_coverage_groups"),
        "observed_coverage_groups": coverage_group_summary.get("observed_coverage_groups"),
        "missing_coverage_groups": coverage_group_summary.get("missing_coverage_groups"),
        "coverage_group_missing_count": coverage_group_summary.get("coverage_group_missing_count", 0),
        "release_blockers": release_blockers,
        "next_action_branch": next_action_branch,
        "next_branch": next_action_branch,
        "next_action_routing_summary": next_action_routing_summary,
        "next_action_routing_ready": next_action_branch.get("measurement_next_action_routing_ready"),
        "next_action_routing_basis": next_action_branch.get("routing_basis"),
        "next_action_selected_release_blocker": next_action_branch.get("selected_release_blocker"),
        "next_action_selected_top_rejection_reason": next_action_branch.get("selected_top_rejection_reason"),
        "next_action_classification_counter": next_action_branch.get("classification_counter"),
        "classification_decided_before_cause_repair": next_action_branch.get("classification_decided_before_cause_repair"),
        "tone_or_surface_routing_requires_measured_issue": next_action_branch.get("tone_or_surface_routing_requires_measured_issue"),
        "next_action_classification": next_action_branch.get("classification"),
        "next_action_layer": next_action_branch.get("target_layer"),
        "next_action_target": next_action_branch.get("target_area"),
        "next_step": next_action_branch.get("next_work_unit"),
        "display_confirmed_count": capture_summary.get("display_confirmed_count", 0),
        "scorecard_passed_display_count": capture_summary.get("scorecard_passed_display_count", 0),
        "eligible_count": scorecard.get("eligible_count", 0),
        "passed_display_count": scorecard.get("passed_display_count", 0),
        "display_reach_rate": scorecard.get("display_reach_rate", 0.0),
        "coverage_group_count": coverage_group_summary.get("coverage_group_count", 0),
        "product_gate_ready": False,
        "product_gate_reached": False,
        "product_gate_achieved": False,
        "product_gate_public_release_applied": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "release_judgment": {
            "release_allowed": False,
            "reason": "step4_measurement_connection_only_public_release_not_applied",
        },
        "comment_text_contract": "passed_only",
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "comment_text_written_by_step4_measurement": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "gate_relaxed": False,
    }
    exit_gate_summary = build_complete_product_quality_measurement_exit_gate_summary(report)
    report.update(
        {
            "exit_gate_summary": exit_gate_summary,
            "measurement_exit_gate_summary": exit_gate_summary,
            "exit_gate_summary_ready": exit_gate_summary.get("exit_gate_summary_ready"),
            "exit_gate_ready": exit_gate_summary.get("exit_gate_ready"),
            "measurement_exit_gate_ready": exit_gate_summary.get("measurement_exit_gate_ready"),
            "measurement_exit_gate_completed": exit_gate_summary.get("measurement_exit_gate_completed"),
            "measurement_connection_complete": exit_gate_summary.get("measurement_connection_complete"),
            "measurement_connection_completed": exit_gate_summary.get("measurement_connection_completed"),
            "product_gate_measurement_connection_complete": exit_gate_summary.get("product_gate_measurement_connection_complete"),
            "scorecard_event_connection_ready": exit_gate_summary.get("scorecard_event_connection_ready"),
            "scorecard_event_adapter_connected": exit_gate_summary.get("scorecard_event_adapter_connected"),
            "submit_level_event_fields_ready": exit_gate_summary.get("submit_level_event_fields_ready"),
            "scorecard_connected_to_release_ladder": exit_gate_summary.get("scorecard_connected_to_release_ladder"),
            "minimum_exit_gate_fixture_coverage_complete": exit_gate_summary.get("minimum_fixture_coverage_complete"),
            "exit_gate_minimum_fixture_coverage_ready": exit_gate_summary.get("minimum_fixture_coverage_ready"),
            "exit_gate_observed_fixture_classes": exit_gate_summary.get("observed_fixture_classes"),
            "exit_gate_missing_fixture_classes": exit_gate_summary.get("missing_fixture_classes"),
            "exit_gate_required_fixture_classes": exit_gate_summary.get("required_fixture_classes"),
            "exit_gate_blockers": exit_gate_summary.get("exit_gate_blockers"),
            "release_judgment": exit_gate_summary.get("release_judgment"),
            "measurement_connection_complete_not_product_gate_achieved": exit_gate_summary.get("measurement_connection_complete_not_product_gate_achieved"),
            "product_gate_ready": False,
            "product_gate_reached": False,
            "product_gate_achieved": False,
            "product_gate_public_release_applied": False,
            "public_release_applied": False,
            "product_quality_released": False,
        }
    )
    assert_product_quality_measurement_connection_meta_only(report, source="measurement_report")
    return report


def dump_complete_product_quality_measurement_connection(report: Mapping[str, Any]) -> str:
    data = dict(report or {})
    data["raw_input_included"] = False
    data["raw_text_included"] = False
    data["comment_text_included"] = False
    assert_product_quality_measurement_connection_meta_only(data, source="measurement_report")
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


build_product_quality_scorecard_event_from_observation_row = normalize_observation_row_to_product_quality_event
build_product_quality_scorecard_events_from_observation_rows = normalize_observation_rows_to_product_quality_events
build_product_quality_scorecard_events_from_joined_rows = normalize_observation_rows_to_product_quality_events
dump_product_quality_measurement_event = dump_product_quality_measurement_scorecard_event
build_product_quality_measurement_connection = build_complete_product_quality_measurement_connection
build_product_quality_measurement_next_action_routing_summary = build_complete_product_quality_measurement_next_action_routing_summary
build_product_quality_measurement_exit_gate_summary = build_complete_product_quality_measurement_exit_gate_summary
build_complete_product_quality_measurement_connection_report = build_complete_product_quality_measurement_connection
dump_complete_product_quality_measurement_connection_report = dump_complete_product_quality_measurement_connection


__all__ = [
    "COMPLETE_PRODUCT_QUALITY_MEASUREMENT_CONNECTION_VERSION",
    "COMPLETE_PRODUCT_QUALITY_MEASUREMENT_CONNECTION_STEP",
    "COMPLETE_PRODUCT_QUALITY_MEASUREMENT_RUN_BUILDER_STEP",
    "COMPLETE_PRODUCT_QUALITY_MEASUREMENT_COVERAGE_GROUP_STEP",
    "COMPLETE_PRODUCT_QUALITY_MEASUREMENT_BLIND_QA_STEP",
    "COMPLETE_PRODUCT_QUALITY_MEASUREMENT_BLIND_QA_SEPARATION_STEP",
    "COMPLETE_PRODUCT_QUALITY_MEASUREMENT_NEXT_ACTION_ROUTING_STEP",
    "COMPLETE_PRODUCT_QUALITY_MEASUREMENT_EXIT_GATE_STEP",
    "COMPLETE_PRODUCT_QUALITY_MEASUREMENT_EXIT_GATE_REQUIRED_FIXTURE_CLASSES",
    "ProductQualityMeasurementConnectionError",
    "assert_product_quality_measurement_connection_meta_only",
    "normalize_observation_row_to_product_quality_event",
    "build_complete_product_quality_blind_qa_input_candidates",
    "assert_product_quality_measurement_blind_qa_reviews_meta_only",
    "normalize_observation_rows_to_product_quality_events",
    "build_product_quality_scorecard_event_from_observation_row",
    "build_product_quality_scorecard_events_from_observation_rows",
    "build_product_quality_scorecard_events_from_joined_rows",
    "build_complete_product_quality_measurement_connection",
    "build_product_quality_measurement_connection",
    "build_complete_product_quality_measurement_next_action_routing_summary",
    "build_product_quality_measurement_next_action_routing_summary",
    "build_complete_product_quality_measurement_exit_gate_summary",
    "build_product_quality_measurement_exit_gate_summary",
    "build_complete_product_quality_measurement_connection_report",
    "dump_complete_product_quality_measurement_connection",
    "dump_complete_product_quality_measurement_connection_report",
    "dump_product_quality_measurement_scorecard_event",
    "dump_product_quality_measurement_connection_payload",
    "dump_product_quality_measurement_event",
]
