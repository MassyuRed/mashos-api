# -*- coding: utf-8 -*-
"""Submit-level Emlis observation diagnostic lockdown helpers.

This module is intentionally meta-only. It does not relax any EmlisAI gate,
change public response keys, or expose raw input / public comment text.  It
normalizes the existing EmlisAI reply meta into a one-line record that can be
joined with the RN frontend diagnostic by ``trace_id``.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

DIAGNOSTIC_LOCKDOWN_VERSION = "emlis.observation_diagnostic_lockdown.v1"
DEFAULT_SOURCE = "backend_emotion_submit"
_MAX_REASON_COUNT = 20

_REDACTED_TEXT_KEYS = {
    "raw_input",
    "input",
    "input_text",
    "memo",
    "memo_text",
    "current_input",
    "comment_text",
    "public_comment_text",
    "candidate_comment_text",
    "reply_text",
    "text",
}

_CONNECTED_STATUSES = {
    "",
    "connected",
    "resolved",
    "ready",
    "provided",
    "provided_client",
    "explicit_client_provided",
    "explicit_client_resolved",
    "default_client_resolved",
    "client_resolved",
    "complete_initial_client_resolved",
}

_PRE_CONNECTION_STAGES = {"flag", "rollout", "scope"}


class _Missing:
    pass


_MISSING = _Missing()


def _is_mapping(value: Any) -> bool:
    return isinstance(value, Mapping)


def _safe_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _clean(value: Any) -> str:
    if value is None:
        return ""
    # Diagnostic logs must never stringify containers.  A dict/list may carry
    # raw input or public comment text under a nested key; converting it with
    # str(...) would leak the payload into the one-line diagnostic row.
    if isinstance(value, Mapping) or isinstance(value, (list, tuple, set)):
        return ""
    return str(value).strip()


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on", "passed", "generated", "connected"}
    return bool(value)


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if isinstance(value, bool):
            return int(value)
        return int(value)
    except Exception:
        return default


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return list(value)
    if isinstance(value, str):
        return [value] if value.strip() else []
    return [value]


_SAFE_STRING_KEYS = (
    "reason_code",
    "reason",
    "primary_reason",
    "code",
    "key",
    "name",
    "status",
    "relation_type",
    "type",
    "id",
    "span_id",
    "phrase_unit_id",
    "relation_id",
    "sentence_id",
)


def _safe_string_tokens(value: Any) -> list[str]:
    """Return log-safe string tokens without stringifying raw containers.

    Some existing diagnostic meta stores reasons as dictionaries.  Those
    dictionaries may also contain preview text or raw-text-like fields.  Step 5
    keeps only code/id style fields and intentionally drops unknown mapping
    payloads instead of serializing the full object.
    """

    text = _clean(value)
    if text:
        return [text]
    if isinstance(value, Mapping):
        tokens: list[str] = []
        for key in _SAFE_STRING_KEYS:
            if key in value:
                tokens.extend(_safe_string_tokens(value.get(key)))
        return tokens
    if isinstance(value, (list, tuple, set)):
        tokens: list[str] = []
        for item in value:
            tokens.extend(_safe_string_tokens(item))
        return tokens
    return []


def _dedupe_strings(values: Any, *, limit: int | None = None) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in _as_list(values):
        for text in _safe_string_tokens(item):
            if not text or text in seen:
                continue
            seen.add(text)
            result.append(text)
            if limit is not None and len(result) >= limit:
                return result
    return result


def _first_nonempty(*values: Any) -> str:
    for value in values:
        text = _clean(value)
        if text:
            return text
    return ""


def _first_mapping(*values: Any) -> dict[str, Any]:
    for value in values:
        if isinstance(value, Mapping) and value:
            return dict(value)
    return {}


def _get_path(source: Mapping[str, Any] | None, *keys: str, default: Any = _MISSING) -> Any:
    value: Any = source
    for key in keys:
        if not isinstance(value, Mapping) or key not in value:
            return None if default is _MISSING else default
        value = value.get(key)
    return value


def _extract_diagnostic_summary(input_feedback_meta: Mapping[str, Any]) -> dict[str, Any]:
    direct = input_feedback_meta.get("diagnostic_summary")
    if isinstance(direct, Mapping):
        return dict(direct)

    multi_perspective = input_feedback_meta.get("multi_perspective")
    nested = _get_path(multi_perspective if isinstance(multi_perspective, Mapping) else {}, "diagnostic_summary")
    if isinstance(nested, Mapping):
        return dict(nested)

    return {}


def _extract_complete_reply_diagnostics(
    input_feedback_meta: Mapping[str, Any],
    diagnostic_summary: Mapping[str, Any],
) -> dict[str, Any]:
    candidates = (
        diagnostic_summary.get("complete_reply_service_diagnostics"),
        diagnostic_summary.get("step11_complete_reply_service_diagnostics"),
        diagnostic_summary.get("complete_reply_diagnostics"),
        input_feedback_meta.get("complete_reply_service_diagnostics"),
        input_feedback_meta.get("step11_complete_reply_service_diagnostics"),
        input_feedback_meta.get("complete_reply_diagnostics"),
    )
    return _first_mapping(*candidates)


def _extract_scorecard_event(
    input_feedback_meta: Mapping[str, Any],
    diagnostic_summary: Mapping[str, Any],
    complete_diagnostics: Mapping[str, Any],
) -> dict[str, Any]:
    candidates = (
        complete_diagnostics.get("scorecard_event"),
        complete_diagnostics.get("complete_scorecard_event"),
        diagnostic_summary.get("scorecard_event"),
        diagnostic_summary.get("complete_scorecard_event"),
        diagnostic_summary.get("complete_composer_scorecard_event"),
        diagnostic_summary.get("complete_composer_initial_scorecard_event"),
        input_feedback_meta.get("scorecard_event"),
        input_feedback_meta.get("complete_scorecard_event"),
    )
    return _first_mapping(*candidates)


def _extract_runtime_meta(
    diagnostic_summary: Mapping[str, Any],
    complete_diagnostics: Mapping[str, Any],
) -> dict[str, Any]:
    candidates = (
        complete_diagnostics.get("complete_runtime_meta"),
        complete_diagnostics.get("complete_composer_meta"),
        complete_diagnostics.get("complete_composer_initial_meta"),
        diagnostic_summary.get("complete_composer_initial_runtime"),
        diagnostic_summary.get("complete_composer_initial_meta"),
        diagnostic_summary.get("complete_composer_meta"),
    )
    return _first_mapping(*candidates)


def _extract_connection_resolution(diagnostic_summary: Mapping[str, Any]) -> dict[str, Any]:
    pre_connection = _safe_mapping(diagnostic_summary.get("pre_connection"))
    nested_b_plan = _safe_mapping(pre_connection.get("b_plan_connection"))
    source = _first_mapping(
        diagnostic_summary.get("composer_client_resolution"),
        diagnostic_summary.get("registry_resolution"),
        diagnostic_summary.get("normal_connection"),
        diagnostic_summary.get("b_plan_connection"),
        nested_b_plan,
        diagnostic_summary.get("default_composer_resolution"),
    )

    release_decision = _safe_mapping(diagnostic_summary.get("release_decision"))
    rollout_decision = _safe_mapping(diagnostic_summary.get("rollout_decision"))

    connection_status = _first_nonempty(
        source.get("connection_status"),
        source.get("status"),
        source.get("client_status"),
        source.get("composer_connection_status"),
    )
    pre_stop_stage = _first_nonempty(
        source.get("pre_connection_stop_stage"),
        source.get("stop_stage"),
        source.get("stage"),
        diagnostic_summary.get("stage") if _clean(diagnostic_summary.get("stage")) in _PRE_CONNECTION_STAGES else "",
    )
    reason_group = _first_nonempty(
        source.get("reason_group"),
        source.get("reason_category"),
        release_decision.get("reason_group"),
        rollout_decision.get("reason_group"),
        diagnostic_summary.get("composer_reason_category"),
    )
    not_connected_reason = _first_nonempty(
        source.get("not_connected_reason"),
        source.get("reason_code"),
        source.get("primary_reason"),
        release_decision.get("reason_code"),
        rollout_decision.get("reason_code"),
        diagnostic_summary.get("primary_reason") if _clean(diagnostic_summary.get("stage")) in _PRE_CONNECTION_STAGES else "",
    )

    return {
        "connection_status": connection_status,
        "pre_connection_stop_stage": pre_stop_stage,
        "reason_group": reason_group,
        "not_connected_reason": not_connected_reason,
    }


def _normalize_gate_result(value: Any, *, fallback_passed: bool | None = None, fallback_reason: str = "") -> dict[str, Any]:
    raw = _safe_mapping(value)
    if "passed" in raw:
        passed: bool | None = _to_bool(raw.get("passed"))
    elif "status" in raw:
        status = _clean(raw.get("status")).lower()
        passed = True if status == "passed" else False if status in {"failed", "rejected", "blocked"} else fallback_passed
    else:
        passed = fallback_passed

    primary_reason = _first_nonempty(raw.get("primary_reason"), raw.get("reason"), fallback_reason)
    rejection_reasons = _dedupe_strings(raw.get("rejection_reasons") or raw.get("reasons"), limit=_MAX_REASON_COUNT)
    if passed is False and primary_reason and primary_reason != "passed" and primary_reason not in rejection_reasons:
        rejection_reasons.insert(0, primary_reason)
        rejection_reasons = rejection_reasons[:_MAX_REASON_COUNT]
    if passed is True and not primary_reason:
        primary_reason = "passed"

    return {
        "passed": passed,
        "primary_reason": primary_reason,
        "rejection_reasons": rejection_reasons,
    }


def _extract_gate_results(
    diagnostic_summary: Mapping[str, Any],
    complete_diagnostics: Mapping[str, Any],
    display_rejection_reasons: list[str],
    observation_status: str,
) -> dict[str, dict[str, Any]]:
    source = _safe_mapping(diagnostic_summary.get("gate_results"))
    complete_source = _safe_mapping(complete_diagnostics.get("gate_results"))
    gate_diagnostic = _safe_mapping(diagnostic_summary.get("gate_diagnostic"))

    def gate(*names: str) -> Any:
        for name in names:
            if name in source:
                return source.get(name)
        for name in names:
            if name in complete_source:
                return complete_source.get(name)
        return {}

    display_fallback_passed: bool | None = True if observation_status == "passed" else False
    display_fallback_reason = "passed" if observation_status == "passed" else _first_nonempty(
        display_rejection_reasons[0] if display_rejection_reasons else "",
        gate_diagnostic.get("primary_reason"),
    )
    display_gate = _normalize_gate_result(
        gate("display", "display_gate"),
        fallback_passed=display_fallback_passed,
        fallback_reason=display_fallback_reason,
    )
    if observation_status != "passed" and display_rejection_reasons and display_gate["passed"] is not False:
        display_gate = {
            "passed": False,
            "primary_reason": display_fallback_reason,
            "rejection_reasons": display_rejection_reasons[:_MAX_REASON_COUNT],
        }

    return {
        "reader": _normalize_gate_result(gate("reader")),
        "grounding": _normalize_gate_result(gate("grounding")),
        "template_echo": _normalize_gate_result(gate("template_echo", "template")),
        "display": display_gate,
    }


def _extract_display_rejection_reasons(
    input_feedback_meta: Mapping[str, Any],
    diagnostic_summary: Mapping[str, Any],
    complete_diagnostics: Mapping[str, Any],
) -> list[str]:
    gate_results = _safe_mapping(diagnostic_summary.get("gate_results"))
    display_gate = _first_mapping(gate_results.get("display"), gate_results.get("display_gate"))
    values: list[Any] = []
    for source in (
        input_feedback_meta,
        diagnostic_summary,
        complete_diagnostics,
        display_gate,
        diagnostic_summary.get("gate_diagnostic"),
    ):
        if isinstance(source, Mapping):
            values.extend(_as_list(source.get("rejection_reasons")))
            values.extend(_as_list(source.get("display_rejection_reasons")))
            values.extend(_as_list(source.get("display_gate_rejection_reasons")))
            gate_rejections = source.get("gate_rejection_reasons")
            if isinstance(gate_rejections, Mapping):
                for nested_reasons in gate_rejections.values():
                    values.extend(_as_list(nested_reasons))
            else:
                values.extend(_as_list(gate_rejections))
            values.extend(_as_list(source.get("reason_codes")))
    return _dedupe_strings(values, limit=_MAX_REASON_COUNT)


def _extract_candidate(
    *,
    diagnostic_summary: Mapping[str, Any],
    complete_diagnostics: Mapping[str, Any],
    scorecard_event: Mapping[str, Any],
    runtime_meta: Mapping[str, Any],
    observation_status: str,
    comment_text_length: int,
) -> dict[str, Any]:
    composer_status = _first_nonempty(
        complete_diagnostics.get("composer_status"),
        scorecard_event.get("composer_status"),
        diagnostic_summary.get("composer_status"),
        diagnostic_summary.get("complete_candidate_status"),
        diagnostic_summary.get("candidate_status"),
        runtime_meta.get("candidate_status"),
        runtime_meta.get("composer_status"),
        diagnostic_summary.get("candidate_status_before_display_gate"),
    )
    composer_source = _first_nonempty(
        complete_diagnostics.get("composer_source"),
        scorecard_event.get("composer_source"),
        diagnostic_summary.get("composer_source"),
        diagnostic_summary.get("complete_candidate_source"),
        diagnostic_summary.get("candidate_source"),
        _get_path(diagnostic_summary, "composer_diagnostic", "composer_source"),
        runtime_meta.get("composer_source"),
    )
    candidate_status = _first_nonempty(
        complete_diagnostics.get("candidate_status"),
        scorecard_event.get("candidate_status"),
        diagnostic_summary.get("complete_candidate_status"),
        diagnostic_summary.get("candidate_status"),
        runtime_meta.get("candidate_status"),
        composer_status,
    )

    explicit_seen = any(
        _to_bool(value)
        for value in (
            complete_diagnostics.get("complete_candidate_seen"),
            scorecard_event.get("complete_candidate_seen"),
            diagnostic_summary.get("complete_candidate_seen"),
            diagnostic_summary.get("candidate_seen"),
            scorecard_event.get("complete_candidate_generated"),
            diagnostic_summary.get("complete_candidate_generated"),
            diagnostic_summary.get("candidate_generated"),
            diagnostic_summary.get("candidate_generated_before_display_gate"),
            diagnostic_summary.get("complete_candidate_generated_before_display_gate"),
            diagnostic_summary.get("candidate_seen_before_display_gate"),
            diagnostic_summary.get("complete_candidate_seen_before_display_gate"),
            runtime_meta.get("candidate_generation_attempted"),
            runtime_meta.get("complete_composer_client_generate_called"),
        )
    )
    explicit_generated = any(
        _to_bool(value)
        for value in (
            complete_diagnostics.get("complete_candidate_generated"),
            scorecard_event.get("complete_candidate_generated"),
            diagnostic_summary.get("complete_candidate_generated"),
            diagnostic_summary.get("candidate_generated"),
            diagnostic_summary.get("candidate_generated_before_display_gate"),
            diagnostic_summary.get("complete_candidate_generated_before_display_gate"),
            runtime_meta.get("candidate_generated"),
        )
    )
    explicit_generated_before_display_gate = any(
        _to_bool(value)
        for value in (
            complete_diagnostics.get("candidate_generated_before_display_gate"),
            complete_diagnostics.get("complete_candidate_generated_before_display_gate"),
            scorecard_event.get("candidate_generated_before_display_gate"),
            scorecard_event.get("complete_candidate_generated_before_display_gate"),
            diagnostic_summary.get("candidate_generated_before_display_gate"),
            diagnostic_summary.get("complete_candidate_generated_before_display_gate"),
            runtime_meta.get("candidate_generated_before_display_gate"),
        )
    )
    status_generated = composer_status == "generated" or candidate_status == "generated"
    source_ai_generated = composer_source == "ai_generated"
    generated = bool(explicit_generated or explicit_generated_before_display_gate or (status_generated and (source_ai_generated or not composer_source)) or (observation_status == "passed" and comment_text_length > 0))
    seen = bool(explicit_seen or generated or composer_status or candidate_status)

    return {
        "seen": seen,
        "generated": generated,
        "generated_before_display_gate": bool(generated or explicit_generated or explicit_generated_before_display_gate),
        "status": candidate_status,
        "source": composer_source,
        "composer_status": composer_status,
        "composer_source": composer_source,
        "used_evidence_span_count": _to_int(
            complete_diagnostics.get("used_evidence_span_count")
            or scorecard_event.get("used_evidence_span_count")
            or diagnostic_summary.get("used_evidence_span_count")
            or runtime_meta.get("used_evidence_span_count")
        ),
        "used_phrase_unit_count": _to_int(
            complete_diagnostics.get("used_phrase_unit_count")
            or scorecard_event.get("used_phrase_unit_count")
            or diagnostic_summary.get("used_phrase_unit_count")
            or runtime_meta.get("used_phrase_unit_count")
        ),
        "used_relation_count": _to_int(
            complete_diagnostics.get("used_relation_count")
            or diagnostic_summary.get("used_relation_count")
            or len(_dedupe_strings(complete_diagnostics.get("relation_types") or scorecard_event.get("relation_types") or diagnostic_summary.get("relation_types") or runtime_meta.get("relation_types")))
        ),
    }


def _extract_evidence_counts(
    *,
    diagnostic_summary: Mapping[str, Any],
    complete_diagnostics: Mapping[str, Any],
    scorecard_event: Mapping[str, Any],
    runtime_meta: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> dict[str, int]:
    return {
        "evidence_span_count": _to_int(
            diagnostic_summary.get("evidence_span_count")
            or _get_path(diagnostic_summary, "complete_initial_pre_generation_diagnostic_seed", "evidence_span_count")
            or runtime_meta.get("evidence_span_count")
        ),
        "used_evidence_span_count": _to_int(
            candidate.get("used_evidence_span_count")
            or complete_diagnostics.get("used_evidence_span_count")
            or scorecard_event.get("used_evidence_span_count")
            or runtime_meta.get("used_evidence_span_count")
            or diagnostic_summary.get("used_evidence_span_count")
        ),
        "used_phrase_unit_count": _to_int(
            candidate.get("used_phrase_unit_count")
            or complete_diagnostics.get("used_phrase_unit_count")
            or scorecard_event.get("used_phrase_unit_count")
            or runtime_meta.get("used_phrase_unit_count")
        ),
        "used_relation_count": _to_int(
            candidate.get("used_relation_count")
            or len(_dedupe_strings(complete_diagnostics.get("relation_types") or scorecard_event.get("relation_types") or runtime_meta.get("relation_types")))
        ),
    }


def _extract_self_repair(
    *,
    complete_diagnostics: Mapping[str, Any],
    diagnostic_summary: Mapping[str, Any],
    runtime_meta: Mapping[str, Any],
) -> dict[str, Any]:
    self_repair_source = _first_mapping(
        complete_diagnostics.get("self_repair"),
        runtime_meta.get("self_repair_report_v2"),
        runtime_meta.get("self_repair"),
        diagnostic_summary.get("self_repair"),
    )
    repair_trace = _as_list(
        complete_diagnostics.get("complete_repair_trace")
        or complete_diagnostics.get("repair_trace")
        or diagnostic_summary.get("complete_repair_trace")
        or diagnostic_summary.get("complete_composer_repair_trace")
        or diagnostic_summary.get("repair_trace")
        or runtime_meta.get("repair_trace_v2")
        or runtime_meta.get("repair_trace")
    )
    trace_count = _to_int(
        complete_diagnostics.get("repair_trace_count")
        or diagnostic_summary.get("repair_trace_count"),
        len(repair_trace),
    )
    aborted_count = _to_int(
        complete_diagnostics.get("repair_aborted_count")
        or diagnostic_summary.get("repair_aborted_count")
        or self_repair_source.get("repair_aborted_count")
        or self_repair_source.get("aborted_count")
    )
    abort_reasons = _dedupe_strings(
        complete_diagnostics.get("repair_abort_reasons")
        or diagnostic_summary.get("repair_abort_reasons")
        or self_repair_source.get("repair_abort_reasons")
        or self_repair_source.get("abort_reasons"),
        limit=_MAX_REASON_COUNT,
    )
    attempted = bool(trace_count or _to_bool(self_repair_source.get("attempted")) or _to_bool(self_repair_source.get("repair_attempted")))
    status = _first_nonempty(
        diagnostic_summary.get("self_repair_status"),
        self_repair_source.get("status"),
        "aborted" if aborted_count else "attempted" if attempted else "not_attempted",
    )
    return {
        "attempted": attempted,
        "status": status,
        "repair_trace_count": trace_count,
        "aborted_count": aborted_count,
        "abort_reasons": abort_reasons,
    }


def classify_observation_diagnostic(record: Mapping[str, Any]) -> str:
    """Classify a normalized submit-level Emlis observation diagnostic record."""

    rejection_reasons = set(_dedupe_strings(record.get("rejection_reasons")))
    rejection_reasons.update(_dedupe_strings(record.get("display_rejection_reasons")))
    if "emlis_ai_timeout_or_error" in rejection_reasons:
        return "backend_exception_or_timeout"

    observation_status = _clean(record.get("observation_status"))
    comment_text_length = _to_int(record.get("comment_text_length"))
    frontend = _safe_mapping(record.get("frontend"))
    if observation_status == "passed" and comment_text_length > 0:
        if frontend and frontend.get("modal_opened") is False:
            return "passed_backend_frontend_hidden"
        return "passed_displayed"

    stage = _clean(record.get("stage"))
    connection = _safe_mapping(record.get("composer_client_resolution"))
    connection_status = _clean(connection.get("connection_status"))
    if stage in _PRE_CONNECTION_STAGES:
        return "pre_connection_stop"
    if connection_status not in _CONNECTED_STATUSES:
        return "pre_connection_stop"

    candidate = _safe_mapping(record.get("candidate"))
    if not _to_bool(candidate.get("generated")):
        return "candidate_missing"

    gate_results = _safe_mapping(record.get("gate_results"))
    for gate_name, classification in (
        ("reader", "candidate_generated_but_reader_rejected"),
        ("grounding", "candidate_generated_but_grounding_rejected"),
        ("template_echo", "candidate_generated_but_template_rejected"),
    ):
        gate = _safe_mapping(gate_results.get(gate_name))
        if gate.get("passed") is False:
            return classification

    display_gate = _safe_mapping(gate_results.get("display"))
    if display_gate.get("passed") is False:
        return "candidate_generated_but_display_rejected"

    return "unclassified_non_display"


def _contains_forbidden_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if _clean(key) in _REDACTED_TEXT_KEYS:
                return True
            if _contains_forbidden_text_payload_key(nested):
                return True
    elif isinstance(value, list):
        return any(_contains_forbidden_text_payload_key(item) for item in value)
    return False


def build_observation_diagnostic_lockdown(
    *,
    input_feedback_comment: str,
    input_feedback_meta: Mapping[str, Any] | None,
    emotion_log_id: str,
    created_at: str,
    source: str = DEFAULT_SOURCE,
) -> dict[str, Any]:
    """Build a meta-only submit-level Emlis observation diagnostic record.

    ``input_feedback_comment`` is only used to calculate length and presence.
    The comment body is never returned in this record.
    """

    meta = _safe_mapping(input_feedback_meta)
    diagnostic_summary = _extract_diagnostic_summary(meta)
    complete_diagnostics = _extract_complete_reply_diagnostics(meta, diagnostic_summary)
    scorecard_event = _extract_scorecard_event(meta, diagnostic_summary, complete_diagnostics)
    runtime_meta = _extract_runtime_meta(diagnostic_summary, complete_diagnostics)
    comment_text_length = len(_clean(input_feedback_comment))
    observation_status = _first_nonempty(meta.get("observation_status"), diagnostic_summary.get("observation_status"), "unavailable")
    display_rejection_reasons = _extract_display_rejection_reasons(meta, diagnostic_summary, complete_diagnostics)
    gate_results = _extract_gate_results(diagnostic_summary, complete_diagnostics, display_rejection_reasons, observation_status)
    connection_resolution = _extract_connection_resolution(diagnostic_summary)
    candidate = _extract_candidate(
        diagnostic_summary=diagnostic_summary,
        complete_diagnostics=complete_diagnostics,
        scorecard_event=scorecard_event,
        runtime_meta=runtime_meta,
        observation_status=observation_status,
        comment_text_length=comment_text_length,
    )
    evidence_counts = _extract_evidence_counts(
        diagnostic_summary=diagnostic_summary,
        complete_diagnostics=complete_diagnostics,
        scorecard_event=scorecard_event,
        runtime_meta=runtime_meta,
        candidate=candidate,
    )
    secondary_reasons = _dedupe_strings(
        diagnostic_summary.get("secondary_reasons")
        or [
            diagnostic_summary.get("primary_reason"),
            *display_rejection_reasons,
            *(_as_list(meta.get("rejection_reasons"))),
        ],
        limit=_MAX_REASON_COUNT,
    )
    used_phrase_unit_ids = _dedupe_strings(
        complete_diagnostics.get("used_phrase_unit_ids")
        or scorecard_event.get("used_phrase_unit_ids")
        or diagnostic_summary.get("used_phrase_unit_ids")
        or runtime_meta.get("used_phrase_unit_ids"),
        limit=_MAX_REASON_COUNT,
    )
    relation_types = _dedupe_strings(
        complete_diagnostics.get("relation_types")
        or scorecard_event.get("relation_types")
        or diagnostic_summary.get("relation_types")
        or runtime_meta.get("relation_types")
        or diagnostic_summary.get("reader_relation_signal_relation_types")
        or diagnostic_summary.get("expected_relation_types"),
        limit=_MAX_REASON_COUNT,
    )

    record: dict[str, Any] = {
        "version": DIAGNOSTIC_LOCKDOWN_VERSION,
        "source": _clean(source) or DEFAULT_SOURCE,
        "emotion_log_id": _clean(emotion_log_id),
        "created_at": _clean(created_at),
        "trace_id": _first_nonempty(meta.get("observation_trace_id"), diagnostic_summary.get("observation_trace_id"), complete_diagnostics.get("observation_trace_id")),
        "observation_status": observation_status,
        "comment_text_length": comment_text_length,
        "comment_text_present": bool(comment_text_length > 0),
        "stage": _clean(diagnostic_summary.get("stage")),
        "primary_reason": _clean(diagnostic_summary.get("primary_reason")),
        "secondary_reasons": secondary_reasons,
        "rejection_reasons": _dedupe_strings(meta.get("rejection_reasons"), limit=_MAX_REASON_COUNT),
        "coverage_group": _first_nonempty(
            diagnostic_summary.get("coverage_group"),
            diagnostic_summary.get("coverage_primary_group"),
            scorecard_event.get("coverage_group"),
            complete_diagnostics.get("coverage_group"),
        ),
        "coverage_scope": _first_nonempty(
            diagnostic_summary.get("coverage_scope"),
            complete_diagnostics.get("coverage_scope"),
            runtime_meta.get("coverage_scope"),
        ),
        "composer_status": candidate.get("composer_status") or _clean(diagnostic_summary.get("composer_status")),
        "composer_source": candidate.get("composer_source") or _clean(_get_path(diagnostic_summary, "composer_diagnostic", "composer_source")),
        "composer_client_resolution": connection_resolution,
        "pre_connection_stop_stage": connection_resolution.get("pre_connection_stop_stage", ""),
        "candidate": candidate,
        "evidence_counts": evidence_counts,
        "used_phrase_unit_ids": used_phrase_unit_ids,
        "relation_types": relation_types,
        "relation_type": relation_types[0] if relation_types else "",
        "gate_results": gate_results,
        "display_rejection_reasons": display_rejection_reasons,
        "self_repair": _extract_self_repair(
            complete_diagnostics=complete_diagnostics,
            diagnostic_summary=diagnostic_summary,
            runtime_meta=runtime_meta,
        ),
        "raw_input_included": False,
        "comment_text_included": False,
    }
    record["classification"] = classify_observation_diagnostic(record)
    return record


def dump_observation_diagnostic(record: Mapping[str, Any]) -> str:
    """Serialize a diagnostic record as stable compact JSON.

    The helper rejects records that accidentally contain raw-input or public
    comment-text payload keys.  This keeps the one-line log contract enforceable
    at the call site.
    """

    data = dict(record or {})
    data["raw_input_included"] = False
    data["comment_text_included"] = False
    if _contains_forbidden_text_payload_key(data):
        raise ValueError("observation diagnostic record contains a forbidden text payload key")
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "DIAGNOSTIC_LOCKDOWN_VERSION",
    "build_observation_diagnostic_lockdown",
    "classify_observation_diagnostic",
    "dump_observation_diagnostic",
]
