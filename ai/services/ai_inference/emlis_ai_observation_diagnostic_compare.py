# -*- coding: utf-8 -*-
"""Step 7 helpers for comparing Emlis observation diagnostics.

The comparison is meta-only. It joins backend/RN one-line diagnostics by
trace_id or emotion_log_id and identifies the first failed layer between the
11:35 non-display submit and the 11:36 displayed submit.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from emlis_ai_observation_diagnostic_lockdown import classify_observation_diagnostic
from emlis_ai_observation_diagnostic_branching import (
    attach_observation_diagnostic_next_branch,
    resolve_observation_diagnostic_next_branch,
)

BACKEND_LOG_PREFIX = "emlis_observation_diagnostic_lockdown "
FRONTEND_LOG_PREFIX = "emlis_observation_frontend_result "
COMPARISON_VERSION = "emlis.observation_diagnostic_comparison.v1"
DIAGNOSTIC_CAPTURE_STATUS_CAPTURED = "captured"
DIAGNOSTIC_LOG_MISSING_OR_NOT_CAPTURED = "diagnostic_log_missing_or_not_captured"
BACKEND_DIAGNOSTIC_MISSING_OR_NOT_CAPTURED = "backend_diagnostic_missing_or_not_captured"
FRONTEND_DIAGNOSTIC_MISSING_OR_NOT_CAPTURED = "frontend_diagnostic_missing_or_not_captured"
JOIN_SEMANTICS_VERSION = "emlis.backend_frontend_join_semantics.v1"
FRONTEND_MODAL_NOT_OPENED = "frontend_modal_not_opened"
BACKEND_PUBLIC_PASSED_FRONTEND_UNCONFIRMED = "backend_public_passed_frontend_unconfirmed"

_FORBIDDEN_TEXT_PAYLOAD_KEYS = {
    "raw_input", "rawInput", "input", "input_text", "inputText",
    "memo", "memo_text", "memoText", "current_input", "currentInput",
    "comment_text", "commentText", "input_feedback_comment", "inputFeedbackComment",
    "public_comment_text", "candidate_comment_text", "reply_text", "text",
}
_DISPLAYED_CLASSIFICATIONS = {"passed_displayed"}
_CLASSIFICATION_TO_LAYER = {
    "backend_exception_or_timeout": "backend_exception_or_timeout",
    "pre_connection_stop": "pre_connection",
    "candidate_missing": "candidate",
    "candidate_generated_but_reader_rejected": "reader",
    "candidate_generated_but_grounding_rejected": "grounding",
    "candidate_generated_but_template_rejected": "template",
    "candidate_generated_but_display_rejected": "display",
    "passed_backend_frontend_hidden": "frontend",
    "passed_displayed": "passed",
    "unclassified_non_display": "unclassified",
    "unknown_diagnostic_missing": "diagnostic",
}
_NEXT_STEP = {
    "backend_exception_or_timeout": "timeout / error / dependency",
    "pre_connection_stop": "Composer connection / release / AP0 / rollout",
    "candidate_missing": "CompleteComposerClient material / focus / relation / sentence plan",
    "candidate_generated_but_reader_rejected": "Reader / relation surface / relation_not_expressed",
    "candidate_generated_but_grounding_rejected": "sentence binding / evidence binding / unsupported_sentence",
    "candidate_generated_but_template_rejected": "Surface variation / echo guard",
    "candidate_generated_but_display_rejected": "phase readiness / composer source / empty text wiring",
    "passed_backend_frontend_hidden": "RN input_feedback receive / status reading / modal condition",
    "passed_displayed": "scorecard / coverage suite / blind QA",
    "unclassified_non_display": "diagnostic schema enrichment before repair",
    "unknown_diagnostic_missing": "diagnostic schema enrichment before repair",
}
_FIELD_DIFF_LAYERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("pre_connection", ("pre_connection_status", "pre_connection_stop_stage")),
    ("candidate", ("candidate_generated", "candidate_status")),
    ("reader", ("reader", "reader_reason")),
    ("grounding", ("grounding", "grounding_reason")),
    ("template", ("template", "template_reason")),
    ("display", ("display", "display_reason")),
    ("backend_public_result", ("backend_status", "backend_len", "backend_public_passed")),
    ("frontend", ("rn_status", "rn_len", "modal_opened", "frontend_join_status")),
    ("display_confirmation", ("display_confirmed", "measurement_classification", "scorecard_passed_display_count")),
)


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).strip()


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if isinstance(value, bool):
            return int(value)
        return int(value)
    except Exception:
        return default


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on", "passed", "generated"}
    return bool(value)


def _safe_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _contains_forbidden_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if _clean(key) in _FORBIDDEN_TEXT_PAYLOAD_KEYS:
                return True
            if _contains_forbidden_text_payload_key(nested):
                return True
    elif isinstance(value, list):
        return any(_contains_forbidden_text_payload_key(item) for item in value)
    return False


def _assert_meta_only(value: Mapping[str, Any], *, source: str) -> None:
    if _contains_forbidden_text_payload_key(value):
        raise ValueError(f"{source} diagnostic contains a forbidden text payload key")
    if value.get("raw_input_included") is True or value.get("comment_text_included") is True:
        raise ValueError(f"{source} diagnostic marks raw input or comment text as included")


def _json_payload_after_prefix(line: str, prefix: str) -> dict[str, Any] | None:
    if prefix not in line:
        return None
    payload = line.split(prefix, 1)[1].strip()
    if not payload:
        return None
    decoder = json.JSONDecoder()
    try:
        parsed, _end = decoder.raw_decode(payload)
    except json.JSONDecodeError:
        start = payload.find("{")
        end = payload.rfind("}")
        if start < 0 or end <= start:
            raise
        parsed = json.loads(payload[start : end + 1])
    if not isinstance(parsed, Mapping):
        raise ValueError("diagnostic log payload must be a JSON object")
    return dict(parsed)


def parse_observation_diagnostic_log_line(line: str) -> dict[str, Any] | None:
    """Parse one backend/RN diagnostic log line.

    Returns ``{"kind": "backend", "record": record}``,
    ``{"kind": "frontend", "record": record}``, or ``None``. Raw input and
    public comment text payload keys are rejected immediately.
    """

    backend = _json_payload_after_prefix(str(line or ""), BACKEND_LOG_PREFIX)
    if backend is not None:
        _assert_meta_only(backend, source="backend")
        return {"kind": "backend", "record": backend}
    frontend = _json_payload_after_prefix(str(line or ""), FRONTEND_LOG_PREFIX)
    if frontend is not None:
        _assert_meta_only(frontend, source="frontend")
        return {"kind": "frontend", "record": frontend}
    return None

def parse_observation_diagnostic_logs(lines: Iterable[str]) -> dict[str, list[dict[str, Any]]]:
    records: dict[str, list[dict[str, Any]]] = {"backend": [], "frontend": []}
    for line in lines:
        parsed = parse_observation_diagnostic_log_line(str(line))
        if parsed is None:
            continue
        kind = _clean(parsed.get("kind"))
        record = _safe_mapping(parsed.get("record"))
        if kind in records:
            records[kind].append(record)
    return records

def _frontend_join_key(record: Mapping[str, Any]) -> tuple[str, str]:
    return _clean(record.get("trace_id")), _clean(record.get("emotion_log_id"))


def _frontend_index(frontend_records: Sequence[Mapping[str, Any]] | None) -> tuple[dict[str, Mapping[str, Any]], dict[str, Mapping[str, Any]]]:
    by_trace_id: dict[str, Mapping[str, Any]] = {}
    by_emotion_log_id: dict[str, Mapping[str, Any]] = {}
    for record in frontend_records or []:
        trace_id, emotion_log_id = _frontend_join_key(record)
        if trace_id and trace_id not in by_trace_id:
            by_trace_id[trace_id] = record
        if emotion_log_id and emotion_log_id not in by_emotion_log_id:
            by_emotion_log_id[emotion_log_id] = record
    return by_trace_id, by_emotion_log_id


def _matching_frontend(backend_record: Mapping[str, Any], by_trace_id: Mapping[str, Mapping[str, Any]], by_emotion_log_id: Mapping[str, Mapping[str, Any]]) -> Mapping[str, Any] | None:
    trace_id = _clean(backend_record.get("trace_id"))
    emotion_log_id = _clean(backend_record.get("emotion_log_id"))
    if trace_id and trace_id in by_trace_id:
        return by_trace_id[trace_id]
    if emotion_log_id and emotion_log_id in by_emotion_log_id:
        return by_emotion_log_id[emotion_log_id]
    return None


def _frontend_projection(frontend_record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "version": _clean(frontend_record.get("version")),
        "source": _clean(frontend_record.get("source")),
        "emotion_log_id": _clean(frontend_record.get("emotion_log_id")),
        "trace_id": _clean(frontend_record.get("trace_id")),
        "observation_status": _clean(frontend_record.get("observation_status")),
        "comment_text_length": _to_int(frontend_record.get("comment_text_length")),
        "comment_text_present": _to_bool(frontend_record.get("comment_text_present")),
        "modal_opened": _to_bool(frontend_record.get("modal_opened")),
        "raw_input_included": False,
        "comment_text_included": False,
    }


def _gate_status(record: Mapping[str, Any], gate_name: str) -> str:
    gate = _safe_mapping(_safe_mapping(record.get("gate_results")).get(gate_name))
    if gate.get("passed") is True:
        return "pass"
    if gate.get("passed") is False:
        return "fail"
    return "unknown"


def _gate_reason(record: Mapping[str, Any], gate_name: str) -> str:
    gate = _safe_mapping(_safe_mapping(record.get("gate_results")).get(gate_name))
    return _clean(gate.get("primary_reason"))


def _classification(record: Mapping[str, Any]) -> str:
    return _clean(record.get("classification")) or classify_observation_diagnostic(record)


def _backend_public_passed_from_values(status: Any, length: Any) -> bool:
    """Return the Step2 backend-public-pass boolean.

    ProductGate measurement intentionally separates backend public pass from
    confirmed RN display.  A backend pass requires the public status to be
    ``passed`` and the public comment length to be non-zero.  This helper does
    not inspect the comment body.
    """

    return _clean(status) == "passed" and _to_int(length) > 0


def _frontend_public_passed_from_values(status: Any, length: Any) -> bool:
    return _clean(status) == "passed" and _to_int(length) > 0


def _display_confirmed_from_values(*, backend_public_passed: bool, frontend_joined: bool, modal_opened: Any) -> bool:
    return bool(backend_public_passed and frontend_joined and _to_bool(modal_opened))


def _measurement_classification_for_join(row: Mapping[str, Any], base_classification: str) -> str:
    """Return the Step2 measurement classification for counting semantics.

    The existing diagnostic classifier may still return ``passed_displayed`` for
    a backend-only pass.  Step2 keeps that base classification available but
    adds a measurement classification so scorecard adapters can count only
    ``display_confirmed`` rows as displayed.
    """

    if row.get("display_confirmed") is True:
        return "passed_displayed"
    if row.get("backend_public_passed") is True and row.get("frontend_joined") is not True:
        return BACKEND_PUBLIC_PASSED_FRONTEND_UNCONFIRMED
    if row.get("backend_public_passed") is True and row.get("frontend_joined") is True and row.get("modal_opened") is False:
        return "passed_backend_frontend_hidden"
    return _clean(base_classification) or "unclassified_non_display"


def build_backend_frontend_join_semantics(row: Mapping[str, Any]) -> dict[str, Any]:
    """Build Step2 backend/frontend join semantics for one joined row.

    This is the counting contract used by ProductGate measurement: backend
    ``passed`` + non-empty text is not the same as RN display confirmation.
    ``scorecard_passed_display_count`` is 1 only when ``display_confirmed`` is
    true.  The function is meta-only and never accepts raw input/comment text
    payload keys.
    """

    _assert_meta_only(row, source="join_semantics_row")
    frontend_joined = row.get("frontend_joined") is True
    backend_public_passed = _backend_public_passed_from_values(
        row.get("backend_status"),
        row.get("backend_len"),
    )
    frontend_public_passed = _frontend_public_passed_from_values(
        row.get("rn_status"),
        row.get("rn_len"),
    )
    display_confirmed = _display_confirmed_from_values(
        backend_public_passed=backend_public_passed,
        frontend_joined=frontend_joined,
        modal_opened=row.get("modal_opened"),
    )
    blockers: list[str] = []
    if backend_public_passed and not frontend_joined:
        blockers.append(FRONTEND_DIAGNOSTIC_MISSING_OR_NOT_CAPTURED)
    elif backend_public_passed and frontend_joined and row.get("modal_opened") is False:
        blockers.append(FRONTEND_MODAL_NOT_OPENED)
    semantics = {
        "version": JOIN_SEMANTICS_VERSION,
        "source": "emlis_observation_step2_backend_frontend_join_semantics",
        "backend_public_passed": backend_public_passed,
        "frontend_public_passed": frontend_public_passed,
        "frontend_joined": frontend_joined,
        "frontend_join_status": _row_frontend_join_status(row),
        "display_confirmed": display_confirmed,
        "display_counting_rule": "display_confirmed_requires_backend_public_pass_and_frontend_modal_opened",
        "scorecard_passed_display_count": 1 if display_confirmed else 0,
        "product_gate_display_counted": display_confirmed,
        "display_count_blockers": blockers,
        "measurement_classification": "",
        "raw_input_included": False,
        "comment_text_included": False,
    }
    semantics["measurement_classification"] = _measurement_classification_for_join(
        {**dict(row), **semantics},
        _classification(row),
    )
    _assert_meta_only(semantics, source="join_semantics")
    return semantics


def build_backend_frontend_join_semantics_summary(rows: Sequence[Mapping[str, Any]] | None) -> dict[str, Any]:
    """Summarize Step2 display counting semantics for joined rows."""

    normalized: list[dict[str, Any]] = []
    for source_row in rows or []:
        row = dict(source_row)
        _assert_meta_only(row, source="join_semantics_summary_row")
        if "backend_public_passed" not in row or "display_confirmed" not in row:
            semantics = build_backend_frontend_join_semantics(row)
            row["backend_public_passed"] = semantics["backend_public_passed"]
            row["frontend_public_passed"] = semantics["frontend_public_passed"]
            row["display_confirmed"] = semantics["display_confirmed"]
            row["scorecard_passed_display_count"] = semantics["scorecard_passed_display_count"]
            row["measurement_classification"] = semantics["measurement_classification"]
        normalized.append(row)
    backend_public_passed_count = sum(1 for row in normalized if row.get("backend_public_passed") is True)
    display_confirmed_count = sum(1 for row in normalized if row.get("display_confirmed") is True)
    frontend_unconfirmed_count = sum(
        1
        for row in normalized
        if row.get("backend_public_passed") is True and row.get("frontend_joined") is not True
    )
    frontend_hidden_count = sum(
        1
        for row in normalized
        if row.get("backend_public_passed") is True and row.get("frontend_joined") is True and row.get("modal_opened") is False
    )
    blockers: list[str] = []
    if frontend_unconfirmed_count:
        blockers.append(FRONTEND_DIAGNOSTIC_MISSING_OR_NOT_CAPTURED)
    if frontend_hidden_count:
        blockers.append(FRONTEND_MODAL_NOT_OPENED)
    summary = {
        "version": JOIN_SEMANTICS_VERSION,
        "source": "emlis_observation_step2_backend_frontend_join_semantics_summary",
        "row_count": len(normalized),
        "backend_public_passed_count": backend_public_passed_count,
        "display_confirmed_count": display_confirmed_count,
        "scorecard_passed_display_count": display_confirmed_count,
        "backend_public_passed_frontend_unconfirmed_count": frontend_unconfirmed_count,
        "passed_backend_frontend_hidden_count": frontend_hidden_count,
        "display_counting_rule": "display_confirmed_only",
        "display_reach_rate_overestimation_guard": True,
        "join_semantics_blockers": blockers,
        "raw_input_included": False,
        "comment_text_included": False,
    }
    _assert_meta_only(summary, source="join_semantics_summary")
    return summary


def _row_frontend_join_status(row: Mapping[str, Any]) -> str:
    if row.get("frontend_joined") is True:
        return "joined"
    trace_id = _clean(row.get("trace_id"))
    emotion_log_id = _clean(row.get("emotion_log_id"))
    if not trace_id and not emotion_log_id:
        return "join_key_missing"
    if not trace_id:
        return "trace_id_missing"
    if not emotion_log_id:
        return "emotion_log_id_missing"
    return "missing"


def _capture_status_for_joined_row(row: Mapping[str, Any]) -> str:
    if row.get("frontend_joined") is True:
        return DIAGNOSTIC_CAPTURE_STATUS_CAPTURED
    return FRONTEND_DIAGNOSTIC_MISSING_OR_NOT_CAPTURED


def build_observation_diagnostic_capture_summary(
    backend_records: Sequence[Mapping[str, Any]] | None = None,
    frontend_records: Sequence[Mapping[str, Any]] | None = None,
    *,
    rows: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Summarize whether backend/RN diagnostic lines were captured.

    This is Step1-only measurement metadata.  A missing diagnostic line is not
    treated as Reader/Grounding/Template/RN cause evidence; it is routed back to
    diagnostic enrichment.
    """

    backend_count = len(backend_records or [])
    frontend_count = len(frontend_records or [])
    joined_rows = [dict(row) for row in rows or []]
    joined_frontend_count = sum(1 for row in joined_rows if row.get("frontend_joined") is True)
    unjoined_backend_count = max(0, backend_count - joined_frontend_count)
    join_semantics_summary = build_backend_frontend_join_semantics_summary(joined_rows)

    backend_status = (
        DIAGNOSTIC_CAPTURE_STATUS_CAPTURED
        if backend_count > 0
        else BACKEND_DIAGNOSTIC_MISSING_OR_NOT_CAPTURED
    )
    frontend_status = (
        DIAGNOSTIC_CAPTURE_STATUS_CAPTURED
        if frontend_count > 0 and unjoined_backend_count == 0
        else FRONTEND_DIAGNOSTIC_MISSING_OR_NOT_CAPTURED
    )
    blockers: list[str] = []
    if backend_status != DIAGNOSTIC_CAPTURE_STATUS_CAPTURED:
        blockers.append(BACKEND_DIAGNOSTIC_MISSING_OR_NOT_CAPTURED)
    if frontend_status != DIAGNOSTIC_CAPTURE_STATUS_CAPTURED:
        blockers.append(FRONTEND_DIAGNOSTIC_MISSING_OR_NOT_CAPTURED)

    diagnostic_capture_status = (
        DIAGNOSTIC_CAPTURE_STATUS_CAPTURED
        if not blockers
        else DIAGNOSTIC_LOG_MISSING_OR_NOT_CAPTURED
    )
    summary = {
        "version": COMPARISON_VERSION,
        "source": "emlis_observation_step1_diagnostic_capture_status",
        "diagnostic_capture_status": diagnostic_capture_status,
        "backend_diagnostic_capture_status": backend_status,
        "frontend_diagnostic_capture_status": frontend_status,
        "backend_diagnostic_count": backend_count,
        "frontend_diagnostic_count": frontend_count,
        "joined_frontend_count": joined_frontend_count,
        "unjoined_backend_count": unjoined_backend_count,
        "join_semantics_summary": join_semantics_summary,
        "backend_public_passed_count": join_semantics_summary["backend_public_passed_count"],
        "display_confirmed_count": join_semantics_summary["display_confirmed_count"],
        "scorecard_passed_display_count": join_semantics_summary["scorecard_passed_display_count"],
        "backend_public_passed_frontend_unconfirmed_count": join_semantics_summary["backend_public_passed_frontend_unconfirmed_count"],
        "passed_backend_frontend_hidden_count": join_semantics_summary["passed_backend_frontend_hidden_count"],
        "capture_blockers": blockers,
        "requires_diagnostic_enrichment": bool(blockers),
        "classification": "unknown_diagnostic_missing" if blockers else "",
        "raw_input_included": False,
        "comment_text_included": False,
    }
    _assert_meta_only(summary, source="capture_summary")
    return summary


def _capture_summary_requires_gap_report(summary: Mapping[str, Any]) -> bool:
    return bool(summary.get("requires_diagnostic_enrichment"))


def build_observation_diagnostic_capture_status_report(
    *,
    capture_summary: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]] | None = None,
    left_label: str = "11:35",
    right_label: str = "11:36",
) -> dict[str, Any]:
    """Build a fail-closed Step1 report for missing diagnostic capture."""

    summary = dict(capture_summary or {})
    _assert_meta_only(summary, source="capture_summary")
    classification = "unknown_diagnostic_missing"
    join_semantics_summary = _safe_mapping(summary.get("join_semantics_summary")) or build_backend_frontend_join_semantics_summary(rows)
    report = {
        "version": COMPARISON_VERSION,
        "source": "emlis_observation_step1_diagnostic_capture_status",
        "left_label": _clean(left_label),
        "right_label": _clean(right_label),
        "rows": [dict(row) for row in rows or []],
        "capture_summary": summary,
        "join_semantics_summary": join_semantics_summary,
        "diagnostic_capture_status": _clean(summary.get("diagnostic_capture_status")) or DIAGNOSTIC_LOG_MISSING_OR_NOT_CAPTURED,
        "capture_blockers": list(summary.get("capture_blockers") or []),
        "first_divergence_layer": "diagnostic",
        "first_difference_layer": "diagnostic",
        "first_differing_fields": None,
        "all_differing_fields": [],
        "next_action_classification": classification,
        "next_action_layer": "diagnostic",
        "next_action_target": _NEXT_STEP[classification],
        "next_step": _NEXT_STEP[classification] + " の修正",
        "raw_input_included": False,
        "comment_text_included": False,
    }
    report = attach_observation_diagnostic_next_branch(report)
    report["ready_for_cause_repair"] = False
    report["requires_diagnostic_enrichment"] = True
    report["repair_allowed"] = False
    _assert_meta_only(report, source="capture_status_report")
    return report


def summarize_observation_diagnostic_row(backend_record: Mapping[str, Any], *, frontend_record: Mapping[str, Any] | None = None, label: str = "") -> dict[str, Any]:
    _assert_meta_only(backend_record, source="backend")
    frontend = _safe_mapping(frontend_record)
    if frontend:
        _assert_meta_only(frontend, source="frontend")
    classification_input = dict(backend_record)
    if frontend:
        classification_input["frontend"] = _frontend_projection(frontend)
    classification = classify_observation_diagnostic(classification_input)
    candidate = _safe_mapping(backend_record.get("candidate"))
    connection = _safe_mapping(backend_record.get("composer_client_resolution"))
    self_repair = _safe_mapping(backend_record.get("self_repair"))
    branch = resolve_observation_diagnostic_next_branch(
        {"classification": classification},
        first_divergence_layer=_CLASSIFICATION_TO_LAYER.get(classification, "unclassified"),
    )
    row = {
        "time": _clean(label),
        "label": _clean(label),
        "created_at": _clean(backend_record.get("created_at")),
        "emotion_log_id": _clean(backend_record.get("emotion_log_id")),
        "trace_id": _clean(backend_record.get("trace_id")),
        "backend_status": _clean(backend_record.get("observation_status")),
        "backend_len": _to_int(backend_record.get("comment_text_length")),
        "backend_comment_text_present": _to_bool(backend_record.get("comment_text_present")),
        "rn_status": _clean(frontend.get("observation_status")),
        "rn_len": _to_int(frontend.get("comment_text_length")) if frontend else None,
        "modal_opened": _to_bool(frontend.get("modal_opened")) if frontend else None,
        "frontend_joined": bool(frontend),
        "frontend_join_status": "joined" if frontend else "missing",
        "backend_diagnostic_capture_status": DIAGNOSTIC_CAPTURE_STATUS_CAPTURED,
        "frontend_diagnostic_capture_status": DIAGNOSTIC_CAPTURE_STATUS_CAPTURED if frontend else FRONTEND_DIAGNOSTIC_MISSING_OR_NOT_CAPTURED,
        "diagnostic_capture_status": DIAGNOSTIC_CAPTURE_STATUS_CAPTURED if frontend else FRONTEND_DIAGNOSTIC_MISSING_OR_NOT_CAPTURED,
        "frontend": _frontend_projection(frontend) if frontend else {},
        "stage": _clean(backend_record.get("stage")),
        "primary_reason": _clean(backend_record.get("primary_reason")),
        "coverage_group": _clean(backend_record.get("coverage_group")),
        "pre_connection_status": _clean(connection.get("connection_status")),
        "pre_connection_stop_stage": _clean(backend_record.get("pre_connection_stop_stage") or connection.get("pre_connection_stop_stage")),
        "candidate_generated": _to_bool(candidate.get("generated")),
        "candidate_status": _clean(candidate.get("status")),
        "reader": _gate_status(backend_record, "reader"),
        "reader_reason": _gate_reason(backend_record, "reader"),
        "grounding": _gate_status(backend_record, "grounding"),
        "grounding_reason": _gate_reason(backend_record, "grounding"),
        "template": _gate_status(backend_record, "template_echo"),
        "template_reason": _gate_reason(backend_record, "template_echo"),
        "display": _gate_status(backend_record, "display"),
        "display_reason": _gate_reason(backend_record, "display"),
        "self_repair_status": _clean(self_repair.get("status")),
        "self_repair_attempted": _to_bool(self_repair.get("attempted")),
        "repair_trace_count": _to_int(self_repair.get("repair_trace_count")),
        "repair_aborted_count": _to_int(self_repair.get("aborted_count")),
        "classification": classification,
        "next_action_layer": branch["target_layer"],
        "next_action_target": branch["target_area"],
        "next_step": branch["next_work_unit"],
        "next_action_branch": branch,
        "branch_locked": branch["branch_locked"],
        "ready_for_cause_repair": branch["ready_for_cause_repair"],
        "raw_input_included": False,
        "comment_text_included": False,
    }
    row["frontend_join_status"] = _row_frontend_join_status(row)
    row["diagnostic_capture_status"] = _capture_status_for_joined_row(row)
    join_semantics = build_backend_frontend_join_semantics(row)
    row["backend_public_passed"] = join_semantics["backend_public_passed"]
    row["frontend_public_passed"] = join_semantics["frontend_public_passed"]
    row["display_confirmed"] = join_semantics["display_confirmed"]
    row["display_counting_rule"] = join_semantics["display_counting_rule"]
    row["scorecard_passed_display_count"] = join_semantics["scorecard_passed_display_count"]
    row["product_gate_display_counted"] = join_semantics["product_gate_display_counted"]
    row["display_count_blockers"] = list(join_semantics["display_count_blockers"])
    row["measurement_classification"] = join_semantics["measurement_classification"]
    row["join_semantics"] = join_semantics
    _assert_meta_only(row, source="comparison_row")
    return row


def join_backend_frontend_diagnostics(backend_records: Sequence[Mapping[str, Any]], frontend_records: Sequence[Mapping[str, Any]] | None = None) -> list[dict[str, Any]]:
    by_trace_id, by_emotion_log_id = _frontend_index(frontend_records)
    rows: list[dict[str, Any]] = []
    for backend_record in backend_records:
        frontend_record = _matching_frontend(backend_record, by_trace_id, by_emotion_log_id)
        rows.append(summarize_observation_diagnostic_row(backend_record, frontend_record=frontend_record))
    return rows


def _first_non_displayed_row(rows: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    for row in rows:
        if _classification(row) not in _DISPLAYED_CLASSIFICATIONS:
            return row
    return None


def determine_first_divergence_layer(
    rows_or_left: Sequence[Mapping[str, Any]] | Mapping[str, Any],
    right: Mapping[str, Any] | None = None,
) -> str:
    if right is None:
        rows = list(rows_or_left) if not isinstance(rows_or_left, Mapping) else [rows_or_left]
    else:
        rows = [rows_or_left, right]  # type: ignore[list-item]
    non_displayed = _first_non_displayed_row(rows)
    if non_displayed is not None:
        return _CLASSIFICATION_TO_LAYER.get(_classification(non_displayed), "unclassified")
    if len(rows) >= 2 and rows[0].get("modal_opened") != rows[1].get("modal_opened"):
        return "frontend"
    return "none"


def _field_differences(left_row: Mapping[str, Any], right_row: Mapping[str, Any]) -> list[dict[str, Any]]:
    differences: list[dict[str, Any]] = []
    for layer, fields in _FIELD_DIFF_LAYERS:
        changed = [field for field in fields if left_row.get(field) != right_row.get(field)]
        if changed:
            differences.append({"layer": layer, "fields": changed, "left": {field: left_row.get(field) for field in changed}, "right": {field: right_row.get(field) for field in changed}})
    return differences


def build_observation_diagnostic_comparison(left_row: Mapping[str, Any], right_row: Mapping[str, Any], *, left_label: str = "11:35", right_label: str = "11:36") -> dict[str, Any]:
    left = dict(left_row)
    right = dict(right_row)
    left["label"] = _clean(left_label)
    right["label"] = _clean(right_label)
    _assert_meta_only(left, source="left_row")
    _assert_meta_only(right, source="right_row")
    rows = [left, right]
    first_divergence_layer = determine_first_divergence_layer(rows)
    non_displayed = _first_non_displayed_row(rows)
    classification = _classification(non_displayed or left)
    field_differences = _field_differences(left, right)
    join_semantics_summary = build_backend_frontend_join_semantics_summary(rows)
    report = {
        "version": COMPARISON_VERSION,
        "source": "emlis_observation_step7_11_35_11_36_comparison",
        "left_label": _clean(left_label),
        "right_label": _clean(right_label),
        "rows": rows,
        "join_semantics_summary": join_semantics_summary,
        "first_divergence_layer": first_divergence_layer,
        "first_difference_layer": first_divergence_layer,
        "first_differing_fields": field_differences[0] if field_differences else None,
        "all_differing_fields": field_differences,
        "next_action_classification": classification,
        "next_action_layer": first_divergence_layer,
        "next_action_target": _NEXT_STEP.get(classification, _NEXT_STEP["unclassified_non_display"]),
        "next_step": _NEXT_STEP.get(classification, _NEXT_STEP["unclassified_non_display"]) + " の修正" if classification != "passed_displayed" else _NEXT_STEP["passed_displayed"],
        "raw_input_included": False,
        "comment_text_included": False,
    }
    report = attach_observation_diagnostic_next_branch(report)
    _assert_meta_only(report, source="comparison")
    return report


def _matches(record: Mapping[str, Any], *, trace_id: str = "", emotion_log_id: str = "") -> bool:
    trace = _clean(trace_id)
    emotion = _clean(emotion_log_id)
    return bool((trace and _clean(record.get("trace_id")) == trace) or (emotion and _clean(record.get("emotion_log_id")) == emotion))


def select_observation_comparison_pair(rows: Sequence[Mapping[str, Any]], *, left_trace_id: str = "", right_trace_id: str = "", left_emotion_log_id: str = "", right_emotion_log_id: str = "") -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    normalized = [dict(row) for row in rows]
    if len(normalized) < 2:
        raise ValueError("at least two backend diagnostic records are required for Step 7 comparison")
    left: Mapping[str, Any] | None = None
    right: Mapping[str, Any] | None = None
    if left_trace_id or left_emotion_log_id:
        left = next((record for record in normalized if _matches(record, trace_id=left_trace_id, emotion_log_id=left_emotion_log_id)), None)
    if right_trace_id or right_emotion_log_id:
        right = next((record for record in normalized if _matches(record, trace_id=right_trace_id, emotion_log_id=right_emotion_log_id)), None)
    if left is None:
        left = next((record for record in normalized if _classification(record) not in _DISPLAYED_CLASSIFICATIONS), None)
    if right is None:
        start = normalized.index(left) + 1 if left in normalized else 0
        right = next((record for record in normalized[start:] if _classification(record) in _DISPLAYED_CLASSIFICATIONS), None)
        if right is None:
            right = next((record for record in normalized if record is not left and _classification(record) in _DISPLAYED_CLASSIFICATIONS), None)
    if left is None or right is None:
        raise ValueError("could not select a non-display/display comparison pair from diagnostic records")
    return left, right


def build_comparison_from_log_lines(lines: Iterable[str], *, left_label: str = "11:35", right_label: str = "11:36", left_trace_id: str = "", right_trace_id: str = "", left_emotion_log_id: str = "", right_emotion_log_id: str = "") -> dict[str, Any]:
    parsed = parse_observation_diagnostic_logs(lines)
    rows = join_backend_frontend_diagnostics(parsed["backend"], parsed["frontend"])
    capture_summary = build_observation_diagnostic_capture_summary(parsed["backend"], parsed["frontend"], rows=rows)
    if _capture_summary_requires_gap_report(capture_summary):
        return build_observation_diagnostic_capture_status_report(
            capture_summary=capture_summary,
            rows=rows,
            left_label=left_label,
            right_label=right_label,
        )
    left, right = select_observation_comparison_pair(rows, left_trace_id=left_trace_id, right_trace_id=right_trace_id, left_emotion_log_id=left_emotion_log_id, right_emotion_log_id=right_emotion_log_id)
    report = build_observation_diagnostic_comparison(left, right, left_label=left_label, right_label=right_label)
    report["capture_summary"] = capture_summary
    report["join_semantics_summary"] = capture_summary["join_semantics_summary"]
    report["diagnostic_capture_status"] = capture_summary["diagnostic_capture_status"]
    report["capture_blockers"] = list(capture_summary.get("capture_blockers") or [])
    _assert_meta_only(report, source="comparison")
    return report


def dump_observation_diagnostic_comparison(report: Mapping[str, Any]) -> str:
    data = dict(report or {})
    data["raw_input_included"] = False
    data["comment_text_included"] = False
    _assert_meta_only(data, source="comparison")
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def format_observation_diagnostic_comparison_markdown(report: Mapping[str, Any]) -> str:
    rows = [dict(row) for row in report.get("rows", []) if isinstance(row, Mapping)]
    headers = ["time", "trace_id", "status", "len", "modal", "stage", "reason", "candidate", "reader", "grounding", "template", "display", "repair", "classification"]
    def cell(value: Any) -> str:
        if value is None:
            return ""
        return str(value).replace("|", "\\|").replace("\n", " ")
    layer = report.get("first_difference_layer") or report.get("first_divergence_layer")
    branch = _safe_mapping(report.get("next_action_branch") or report.get("next_branch"))
    lines = [
        f"first_difference_layer: {cell(layer)}",
        f"first_divergence_layer: {cell(layer)}",
        f"next_step: {cell(report.get('next_action_target'))}",
        f"next_work_unit: {cell(branch.get('next_work_unit') or report.get('next_step'))}",
        f"branch_locked: {cell(report.get('branch_locked'))}",
        f"ready_for_cause_repair: {cell(report.get('ready_for_cause_repair'))}",
        f"touch_files: {cell(', '.join(branch.get('touch_files', [])) if isinstance(branch.get('touch_files'), list) else '')}",
        f"do_not_touch: {cell(', '.join(branch.get('do_not_touch', [])) if isinstance(branch.get('do_not_touch'), list) else '')}",
    ]
    capture_summary = _safe_mapping(report.get("capture_summary"))
    if capture_summary:
        lines.extend([
            f"diagnostic_capture_status: {cell(capture_summary.get('diagnostic_capture_status'))}",
            f"backend_diagnostic_capture_status: {cell(capture_summary.get('backend_diagnostic_capture_status'))}",
            f"frontend_diagnostic_capture_status: {cell(capture_summary.get('frontend_diagnostic_capture_status'))}",
            f"capture_blockers: {cell(', '.join(capture_summary.get('capture_blockers', [])) if isinstance(capture_summary.get('capture_blockers'), list) else '')}",
        ])
    join_semantics_summary = _safe_mapping(report.get("join_semantics_summary") or capture_summary.get("join_semantics_summary"))
    if join_semantics_summary:
        lines.extend([
            f"backend_public_passed_count: {cell(join_semantics_summary.get('backend_public_passed_count'))}",
            f"display_confirmed_count: {cell(join_semantics_summary.get('display_confirmed_count'))}",
            f"scorecard_passed_display_count: {cell(join_semantics_summary.get('scorecard_passed_display_count'))}",
            f"display_counting_rule: {cell(join_semantics_summary.get('display_counting_rule'))}",
        ])
    lines.extend([
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ])
    for row in rows:
        candidate = "true" if row.get("candidate_generated") else "false"
        modal = "" if row.get("modal_opened") is None else "true" if row.get("modal_opened") else "false"
        lines.append("| " + " | ".join([cell(row.get("label")), cell(row.get("trace_id")), cell(row.get("backend_status")), cell(row.get("backend_len")), cell(modal), cell(row.get("stage")), cell(row.get("primary_reason")), cell(candidate), cell(row.get("reader")), cell(row.get("grounding")), cell(row.get("template")), cell(row.get("display")), cell(row.get("self_repair_status")), cell(row.get("classification"))]) + " |")
    return "\n".join(lines)


# Backward-compatible aliases for earlier Step7 drafts / tests.
def parse_observation_diagnostic_log_lines(lines: Iterable[str]) -> dict[str, list[dict[str, Any]]]:
    return parse_observation_diagnostic_logs(lines)


def build_observation_comparison_row(backend_record: Mapping[str, Any], frontend_record: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return summarize_observation_diagnostic_row(backend_record, frontend_record=frontend_record)


def build_observation_comparison_rows(backend_records: Sequence[Mapping[str, Any]], frontend_records: Sequence[Mapping[str, Any]] | None = None) -> list[dict[str, Any]]:
    return join_backend_frontend_diagnostics(backend_records, frontend_records)


def compare_observation_diagnostic_records(backend_records: Sequence[Mapping[str, Any]], frontend_records: Sequence[Mapping[str, Any]] | None = None, *, left_label: str = "11:35", right_label: str = "11:36") -> dict[str, Any]:
    rows = join_backend_frontend_diagnostics(backend_records, frontend_records)
    left, right = select_observation_comparison_pair(rows)
    return build_observation_diagnostic_comparison(left, right, left_label=left_label, right_label=right_label)


def compare_observation_diagnostic_log_lines(lines: Iterable[str], *, left_label: str = "11:35", right_label: str = "11:36") -> dict[str, Any]:
    return build_comparison_from_log_lines(lines, left_label=left_label, right_label=right_label)


def dump_observation_comparison(report: Mapping[str, Any]) -> str:
    return dump_observation_diagnostic_comparison(report)


__all__ = [
    "BACKEND_DIAGNOSTIC_MISSING_OR_NOT_CAPTURED", "BACKEND_LOG_PREFIX", "COMPARISON_VERSION",
    "DIAGNOSTIC_CAPTURE_STATUS_CAPTURED", "DIAGNOSTIC_LOG_MISSING_OR_NOT_CAPTURED",
    "FRONTEND_DIAGNOSTIC_MISSING_OR_NOT_CAPTURED", "FRONTEND_LOG_PREFIX",
    "JOIN_SEMANTICS_VERSION", "FRONTEND_MODAL_NOT_OPENED",
    "BACKEND_PUBLIC_PASSED_FRONTEND_UNCONFIRMED",
    "build_backend_frontend_join_semantics", "build_backend_frontend_join_semantics_summary",
    "build_comparison_from_log_lines", "build_observation_diagnostic_capture_status_report",
    "build_observation_diagnostic_capture_summary", "build_observation_diagnostic_comparison",
    "determine_first_divergence_layer", "dump_observation_diagnostic_comparison",
    "format_observation_diagnostic_comparison_markdown", "join_backend_frontend_diagnostics",
    "parse_observation_diagnostic_log_line", "parse_observation_diagnostic_logs",
    "select_observation_comparison_pair", "summarize_observation_diagnostic_row",
    "parse_observation_diagnostic_log_lines", "build_observation_comparison_row",
    "build_observation_comparison_rows", "compare_observation_diagnostic_records",
    "compare_observation_diagnostic_log_lines", "dump_observation_comparison",
    "attach_observation_diagnostic_next_branch", "resolve_observation_diagnostic_next_branch",
]
