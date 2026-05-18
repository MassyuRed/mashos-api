from __future__ import annotations

import json

import pytest

from emlis_ai_observation_diagnostic_compare import (
    BACKEND_DIAGNOSTIC_MISSING_OR_NOT_CAPTURED,
    BACKEND_PUBLIC_PASSED_FRONTEND_UNCONFIRMED,
    BACKEND_LOG_PREFIX,
    COMPARISON_VERSION,
    DIAGNOSTIC_CAPTURE_STATUS_CAPTURED,
    DIAGNOSTIC_LOG_MISSING_OR_NOT_CAPTURED,
    FRONTEND_DIAGNOSTIC_MISSING_OR_NOT_CAPTURED,
    FRONTEND_MODAL_NOT_OPENED,
    FRONTEND_LOG_PREFIX,
    JOIN_SEMANTICS_VERSION,
    build_backend_frontend_join_semantics_summary,
    build_comparison_from_log_lines,
    build_observation_diagnostic_capture_summary,
    build_observation_diagnostic_comparison,
    determine_first_divergence_layer,
    dump_observation_diagnostic_comparison,
    format_observation_diagnostic_comparison_markdown,
    join_backend_frontend_diagnostics,
    parse_observation_diagnostic_log_line,
    parse_observation_diagnostic_logs,
    select_observation_comparison_pair,
)

_SECRET_COMMENT = "これは比較ログへ出してはいけない観測本文です"
_SECRET_RAW_INPUT = "これは比較ログへ出してはいけない入力本文です"


def _gate(passed: bool, reason: str = "") -> dict:
    return {
        "passed": passed,
        "primary_reason": "passed" if passed else reason,
        "rejection_reasons": [] if passed else [reason],
    }


def _backend_record(
    *,
    trace_id: str,
    emotion_log_id: str,
    created_at: str,
    status: str = "rejected",
    comment_len: int = 0,
    stage: str = "display",
    reason: str = "empty_comment_text",
    candidate_generated: bool = True,
    failed_gate: str = "display",
) -> dict:
    gates = {
        "reader": _gate(True),
        "grounding": _gate(True),
        "template_echo": _gate(True),
        "display": _gate(status == "passed", "" if status == "passed" else reason),
    }
    if status != "passed" and failed_gate in gates:
        gates[failed_gate] = _gate(False, reason)
        gates["display"] = _gate(False, reason)

    return {
        "version": "emlis.observation_diagnostic_lockdown.v1",
        "source": "backend_emotion_submit",
        "emotion_log_id": emotion_log_id,
        "created_at": created_at,
        "trace_id": trace_id,
        "observation_status": status,
        "comment_text_length": comment_len,
        "comment_text_present": comment_len > 0,
        "stage": stage,
        "primary_reason": reason,
        "secondary_reasons": [] if status == "passed" else [reason],
        "rejection_reasons": [] if status == "passed" else [reason],
        "coverage_group": "step7_compare_fixture",
        "composer_status": "generated" if candidate_generated else "unavailable",
        "composer_source": "ai_generated" if candidate_generated else "unavailable",
        "composer_client_resolution": {"connection_status": "connected"},
        "candidate": {
            "seen": candidate_generated,
            "generated": candidate_generated,
            "generated_before_display_gate": candidate_generated,
            "status": "generated" if candidate_generated else "unavailable",
            "source": "ai_generated" if candidate_generated else "unavailable",
        },
        "evidence_counts": {
            "evidence_span_count": 2,
            "used_evidence_span_count": 1 if candidate_generated else 0,
            "used_phrase_unit_count": 1 if candidate_generated else 0,
            "used_relation_count": 1 if candidate_generated else 0,
        },
        "gate_results": gates,
        "display_rejection_reasons": [] if status == "passed" else [reason],
        "self_repair": {
            "attempted": failed_gate == "grounding",
            "status": "attempted" if failed_gate == "grounding" else "not_attempted",
            "repair_trace_count": 1 if failed_gate == "grounding" else 0,
            "aborted_count": 0,
            "abort_reasons": [],
        },
        "raw_input_included": False,
        "comment_text_included": False,
    }


def _frontend_record(*, trace_id: str, emotion_log_id: str, status: str, comment_len: int, modal_opened: bool) -> dict:
    return {
        "version": "emlis.frontend_observation_diagnostic.v1",
        "source": "rn_input_screen",
        "emotion_log_id": emotion_log_id,
        "trace_id": trace_id,
        "observation_status": status,
        "comment_text_length": comment_len,
        "comment_text_present": comment_len > 0,
        "modal_opened": modal_opened,
        "raw_input_included": False,
        "comment_text_included": False,
    }


def _line(prefix: str, record: dict) -> str:
    return f"2026-05-17 INFO {prefix}{json.dumps(record, ensure_ascii=False, sort_keys=True)}"


def test_step7_parse_backend_and_frontend_one_line_diagnostics() -> None:
    backend = _backend_record(
        trace_id="emlisobs-parse-backend",
        emotion_log_id="emotion-parse",
        created_at="2026-05-17T02:35:05Z",
    )
    frontend = _frontend_record(
        trace_id="emlisobs-parse-frontend",
        emotion_log_id="emotion-parse-frontend",
        status="passed",
        comment_len=24,
        modal_opened=True,
    )

    parsed_backend = parse_observation_diagnostic_log_line(_line(BACKEND_LOG_PREFIX, backend))
    parsed_frontend = parse_observation_diagnostic_log_line(_line(FRONTEND_LOG_PREFIX, frontend))

    assert parsed_backend == {"kind": "backend", "record": backend}
    assert parsed_frontend == {"kind": "frontend", "record": frontend}
    assert parse_observation_diagnostic_log_line("not a diagnostic line") is None


def test_step7_parse_rejects_forbidden_text_payload_keys() -> None:
    unsafe = _backend_record(
        trace_id="emlisobs-unsafe",
        emotion_log_id="emotion-unsafe",
        created_at="2026-05-17T02:35:05Z",
    )
    unsafe["comment_text"] = _SECRET_COMMENT

    with pytest.raises(ValueError):
        parse_observation_diagnostic_log_line(_line(BACKEND_LOG_PREFIX, unsafe))


def test_step7_join_reclassifies_backend_passed_but_frontend_hidden() -> None:
    backend = _backend_record(
        trace_id="emlisobs-hidden",
        emotion_log_id="emotion-hidden",
        created_at="2026-05-17T02:36:22Z",
        status="passed",
        comment_len=142,
        stage="display",
        reason="passed",
    )
    frontend = _frontend_record(
        trace_id="emlisobs-hidden",
        emotion_log_id="emotion-hidden",
        status="passed",
        comment_len=142,
        modal_opened=False,
    )

    [joined] = join_backend_frontend_diagnostics([backend], [frontend])

    assert joined["frontend_joined"] is True
    assert joined["modal_opened"] is False
    assert joined["classification"] == "passed_backend_frontend_hidden"


def test_step7_builds_1135_1136_comparison_and_selects_grounding_as_first_difference() -> None:
    left_backend = _backend_record(
        trace_id="emlisobs-1135",
        emotion_log_id="emotion-1135",
        created_at="2026-05-17T02:35:05Z",
        status="rejected",
        comment_len=0,
        stage="grounding",
        reason="unsupported_sentence",
        failed_gate="grounding",
    )
    left_frontend = _frontend_record(
        trace_id="emlisobs-1135",
        emotion_log_id="emotion-1135",
        status="rejected",
        comment_len=0,
        modal_opened=False,
    )
    right_backend = _backend_record(
        trace_id="emlisobs-1136",
        emotion_log_id="emotion-1136",
        created_at="2026-05-17T02:36:22Z",
        status="passed",
        comment_len=142,
        stage="display",
        reason="passed",
    )
    right_frontend = _frontend_record(
        trace_id="emlisobs-1136",
        emotion_log_id="emotion-1136",
        status="passed",
        comment_len=142,
        modal_opened=True,
    )

    log_lines = [
        _line(BACKEND_LOG_PREFIX, left_backend),
        _line(FRONTEND_LOG_PREFIX, left_frontend),
        _line(BACKEND_LOG_PREFIX, right_backend),
        _line(FRONTEND_LOG_PREFIX, right_frontend),
    ]

    report = build_comparison_from_log_lines(log_lines)

    assert report["version"] == COMPARISON_VERSION
    assert report["first_divergence_layer"] == "grounding"
    assert report["next_action_target"] == "sentence binding / evidence binding / unsupported_sentence"
    assert report["rows"][0]["classification"] == "candidate_generated_but_grounding_rejected"
    assert report["rows"][1]["classification"] == "passed_displayed"
    assert report["rows"][0]["label"] == "11:35"
    assert report["rows"][0]["grounding"] == "fail"
    assert report["rows"][0]["modal_opened"] is False
    assert report["rows"][1]["label"] == "11:36"
    assert report["rows"][1]["modal_opened"] is True

    dumped = dump_observation_diagnostic_comparison(report)
    assert _SECRET_COMMENT not in dumped
    assert _SECRET_RAW_INPUT not in dumped
    parsed = json.loads(dumped)
    assert parsed["comment_text_included"] is False

    markdown = format_observation_diagnostic_comparison_markdown(report)
    assert "first_difference_layer: grounding" in markdown
    assert "| 11:35 | emlisobs-1135 | rejected | 0 | false | grounding | unsupported_sentence" in markdown
    assert "| 11:36 | emlisobs-1136 | passed | 142 | true | display | passed" in markdown


def test_step7_select_pair_prefers_first_non_display_then_next_display() -> None:
    records = join_backend_frontend_diagnostics(
        [
            _backend_record(
                trace_id="emlisobs-first-fail",
                emotion_log_id="emotion-first-fail",
                created_at="2026-05-17T02:35:05Z",
                failed_gate="reader",
                stage="reader",
                reason="relation_not_expressed",
            ),
            _backend_record(
                trace_id="emlisobs-first-pass",
                emotion_log_id="emotion-first-pass",
                created_at="2026-05-17T02:36:22Z",
                status="passed",
                comment_len=88,
                stage="display",
                reason="passed",
            ),
        ],
        [
            _frontend_record(
                trace_id="emlisobs-first-fail",
                emotion_log_id="emotion-first-fail",
                status="rejected",
                comment_len=0,
                modal_opened=False,
            ),
            _frontend_record(
                trace_id="emlisobs-first-pass",
                emotion_log_id="emotion-first-pass",
                status="passed",
                comment_len=88,
                modal_opened=True,
            ),
        ],
    )

    left, right = select_observation_comparison_pair(records)

    assert left["trace_id"] == "emlisobs-first-fail"
    assert right["trace_id"] == "emlisobs-first-pass"


def test_step7_explicit_trace_id_selection_overrides_auto_pair() -> None:
    records = join_backend_frontend_diagnostics(
        [
            _backend_record(
                trace_id="emlisobs-auto-fail",
                emotion_log_id="emotion-auto-fail",
                created_at="2026-05-17T02:35:00Z",
                failed_gate="reader",
                stage="reader",
                reason="relation_not_expressed",
            ),
            _backend_record(
                trace_id="emlisobs-target-fail",
                emotion_log_id="emotion-target-fail",
                created_at="2026-05-17T02:35:05Z",
                failed_gate="template_echo",
                stage="template",
                reason="template_like",
            ),
            _backend_record(
                trace_id="emlisobs-target-pass",
                emotion_log_id="emotion-target-pass",
                created_at="2026-05-17T02:36:22Z",
                status="passed",
                comment_len=96,
                stage="display",
                reason="passed",
            ),
        ],
        [],
    )

    left, right = select_observation_comparison_pair(
        records,
        left_trace_id="emlisobs-target-fail",
        right_trace_id="emlisobs-target-pass",
    )
    report = build_observation_diagnostic_comparison(left, right)

    assert left["trace_id"] == "emlisobs-target-fail"
    assert right["trace_id"] == "emlisobs-target-pass"
    assert report["first_divergence_layer"] == "template"


def test_step7_dump_rejects_forbidden_text_payload_keys() -> None:
    report = {
        "version": COMPARISON_VERSION,
        "rows": [],
        "commentText": _SECRET_COMMENT,
    }

    with pytest.raises(ValueError):
        dump_observation_diagnostic_comparison(report)


def test_step7_first_divergence_frontend_when_backend_passed_but_modal_hidden() -> None:
    hidden = join_backend_frontend_diagnostics(
        [
            _backend_record(
                trace_id="emlisobs-hidden-left",
                emotion_log_id="emotion-hidden-left",
                created_at="2026-05-17T02:35:05Z",
                status="passed",
                comment_len=120,
                stage="display",
                reason="passed",
            )
        ],
        [
            _frontend_record(
                trace_id="emlisobs-hidden-left",
                emotion_log_id="emotion-hidden-left",
                status="passed",
                comment_len=120,
                modal_opened=False,
            )
        ],
    )[0]
    displayed = join_backend_frontend_diagnostics(
        [
            _backend_record(
                trace_id="emlisobs-displayed-right",
                emotion_log_id="emotion-displayed-right",
                created_at="2026-05-17T02:36:22Z",
                status="passed",
                comment_len=120,
                stage="display",
                reason="passed",
            )
        ],
        [
            _frontend_record(
                trace_id="emlisobs-displayed-right",
                emotion_log_id="emotion-displayed-right",
                status="passed",
                comment_len=120,
                modal_opened=True,
            )
        ],
    )[0]

    assert determine_first_divergence_layer([hidden, displayed]) == "frontend"
    report = build_observation_diagnostic_comparison(hidden, displayed)
    assert report["next_action_target"] == "RN input_feedback receive / status reading / modal condition"


def test_step1_join_marks_frontend_capture_gap_without_reclassifying_as_reader_or_rn_cause() -> None:
    backend = _backend_record(
        trace_id="emlisobs-capture-gap",
        emotion_log_id="emotion-capture-gap",
        created_at="2026-05-17T02:35:05Z",
        status="passed",
        comment_len=120,
        stage="display",
        reason="passed",
    )

    [joined] = join_backend_frontend_diagnostics([backend], [])
    summary = build_observation_diagnostic_capture_summary([backend], [], rows=[joined])

    assert joined["frontend_joined"] is False
    assert joined["frontend_join_status"] == "missing"
    assert joined["backend_diagnostic_capture_status"] == DIAGNOSTIC_CAPTURE_STATUS_CAPTURED
    assert joined["frontend_diagnostic_capture_status"] == FRONTEND_DIAGNOSTIC_MISSING_OR_NOT_CAPTURED
    assert joined["diagnostic_capture_status"] == FRONTEND_DIAGNOSTIC_MISSING_OR_NOT_CAPTURED
    assert summary["diagnostic_capture_status"] == DIAGNOSTIC_LOG_MISSING_OR_NOT_CAPTURED
    assert summary["capture_blockers"] == [FRONTEND_DIAGNOSTIC_MISSING_OR_NOT_CAPTURED]
    assert summary["requires_diagnostic_enrichment"] is True


def test_step2_backend_passed_without_frontend_is_not_display_confirmed_or_scorecard_displayed() -> None:
    backend = _backend_record(
        trace_id="emlisobs-step2-backend-only",
        emotion_log_id="emotion-step2-backend-only",
        created_at="2026-05-17T02:36:22Z",
        status="passed",
        comment_len=144,
        stage="display",
        reason="passed",
    )

    [joined] = join_backend_frontend_diagnostics([backend], [])
    summary = build_observation_diagnostic_capture_summary([backend], [], rows=[joined])

    assert joined["backend_public_passed"] is True
    assert joined["frontend_joined"] is False
    assert joined["frontend_join_status"] == "missing"
    assert joined["display_confirmed"] is False
    assert joined["product_gate_display_counted"] is False
    assert joined["scorecard_passed_display_count"] == 0
    assert joined["measurement_classification"] == BACKEND_PUBLIC_PASSED_FRONTEND_UNCONFIRMED
    assert joined["display_count_blockers"] == [FRONTEND_DIAGNOSTIC_MISSING_OR_NOT_CAPTURED]
    assert joined["join_semantics"]["version"] == JOIN_SEMANTICS_VERSION
    assert summary["join_semantics_summary"]["scorecard_passed_display_count"] == 0
    assert summary["join_semantics_summary"]["backend_public_passed_frontend_unconfirmed_count"] == 1


def test_step2_backend_passed_modal_false_routes_to_frontend_hidden_but_not_display_counted() -> None:
    backend = _backend_record(
        trace_id="emlisobs-step2-hidden",
        emotion_log_id="emotion-step2-hidden",
        created_at="2026-05-17T02:36:22Z",
        status="passed",
        comment_len=120,
        stage="display",
        reason="passed",
    )
    frontend = _frontend_record(
        trace_id="emlisobs-step2-hidden",
        emotion_log_id="emotion-step2-hidden",
        status="passed",
        comment_len=120,
        modal_opened=False,
    )

    [joined] = join_backend_frontend_diagnostics([backend], [frontend])

    assert joined["classification"] == "passed_backend_frontend_hidden"
    assert joined["measurement_classification"] == "passed_backend_frontend_hidden"
    assert joined["backend_public_passed"] is True
    assert joined["frontend_joined"] is True
    assert joined["display_confirmed"] is False
    assert joined["product_gate_display_counted"] is False
    assert joined["scorecard_passed_display_count"] == 0
    assert joined["display_count_blockers"] == [FRONTEND_MODAL_NOT_OPENED]


def test_step2_backend_passed_modal_true_is_display_confirmed_and_scorecard_display_counted() -> None:
    backend = _backend_record(
        trace_id="emlisobs-step2-displayed",
        emotion_log_id="emotion-step2-displayed",
        created_at="2026-05-17T02:36:22Z",
        status="passed",
        comment_len=120,
        stage="display",
        reason="passed",
    )
    frontend = _frontend_record(
        trace_id="emlisobs-step2-displayed",
        emotion_log_id="emotion-step2-displayed",
        status="passed",
        comment_len=120,
        modal_opened=True,
    )

    [joined] = join_backend_frontend_diagnostics([backend], [frontend])
    semantics_summary = build_backend_frontend_join_semantics_summary([joined])

    assert joined["classification"] == "passed_displayed"
    assert joined["measurement_classification"] == "passed_displayed"
    assert joined["backend_public_passed"] is True
    assert joined["frontend_public_passed"] is True
    assert joined["frontend_joined"] is True
    assert joined["display_confirmed"] is True
    assert joined["product_gate_display_counted"] is True
    assert joined["scorecard_passed_display_count"] == 1
    assert joined["display_count_blockers"] == []
    assert semantics_summary["display_confirmed_count"] == 1
    assert semantics_summary["scorecard_passed_display_count"] == 1


def test_step2_join_by_emotion_log_id_still_confirms_display_when_trace_id_is_missing() -> None:
    backend = _backend_record(
        trace_id="",
        emotion_log_id="emotion-step2-emotion-id-only",
        created_at="2026-05-17T02:36:22Z",
        status="passed",
        comment_len=101,
        stage="display",
        reason="passed",
    )
    frontend = _frontend_record(
        trace_id="",
        emotion_log_id="emotion-step2-emotion-id-only",
        status="passed",
        comment_len=101,
        modal_opened=True,
    )

    [joined] = join_backend_frontend_diagnostics([backend], [frontend])

    assert joined["frontend_joined"] is True
    assert joined["frontend_join_status"] == "joined"
    assert joined["display_confirmed"] is True
    assert joined["scorecard_passed_display_count"] == 1


def test_step1_build_from_log_lines_routes_missing_backend_diagnostic_to_diagnostic_enrichment() -> None:
    frontend = _frontend_record(
        trace_id="emlisobs-only-frontend",
        emotion_log_id="emotion-only-frontend",
        status="passed",
        comment_len=120,
        modal_opened=True,
    )

    report = build_comparison_from_log_lines([_line(FRONTEND_LOG_PREFIX, frontend)])

    assert report["source"] == "emlis_observation_step1_diagnostic_capture_status"
    assert report["diagnostic_capture_status"] == DIAGNOSTIC_LOG_MISSING_OR_NOT_CAPTURED
    assert report["capture_summary"]["backend_diagnostic_capture_status"] == BACKEND_DIAGNOSTIC_MISSING_OR_NOT_CAPTURED
    assert report["capture_summary"]["frontend_diagnostic_capture_status"] == DIAGNOSTIC_CAPTURE_STATUS_CAPTURED
    assert report["next_action_classification"] == "unknown_diagnostic_missing"
    assert report["next_action_branch"]["target_layer"] == "diagnostic"
    assert report["ready_for_cause_repair"] is False
    assert report["requires_diagnostic_enrichment"] is True
    assert report["repair_allowed"] is False

    markdown = format_observation_diagnostic_comparison_markdown(report)
    assert "diagnostic_capture_status: diagnostic_log_missing_or_not_captured" in markdown
    assert "backend_diagnostic_capture_status: backend_diagnostic_missing_or_not_captured" in markdown


def test_step1_build_from_log_lines_routes_missing_frontend_diagnostic_to_capture_gap_before_cause_repair() -> None:
    left_backend = _backend_record(
        trace_id="emlisobs-backend-only-left",
        emotion_log_id="emotion-backend-only-left",
        created_at="2026-05-17T02:35:05Z",
        status="rejected",
        comment_len=0,
        stage="grounding",
        reason="unsupported_sentence",
        failed_gate="grounding",
    )
    right_backend = _backend_record(
        trace_id="emlisobs-backend-only-right",
        emotion_log_id="emotion-backend-only-right",
        created_at="2026-05-17T02:36:22Z",
        status="passed",
        comment_len=142,
        stage="display",
        reason="passed",
    )

    report = build_comparison_from_log_lines([
        _line(BACKEND_LOG_PREFIX, left_backend),
        _line(BACKEND_LOG_PREFIX, right_backend),
    ])

    assert report["diagnostic_capture_status"] == DIAGNOSTIC_LOG_MISSING_OR_NOT_CAPTURED
    assert report["capture_summary"]["backend_diagnostic_capture_status"] == DIAGNOSTIC_CAPTURE_STATUS_CAPTURED
    assert report["capture_summary"]["frontend_diagnostic_capture_status"] == FRONTEND_DIAGNOSTIC_MISSING_OR_NOT_CAPTURED
    assert report["capture_summary"]["unjoined_backend_count"] == 2
    assert report["next_action_classification"] == "unknown_diagnostic_missing"
    assert report["next_action_branch"]["requires_diagnostic_enrichment"] is True
    assert report["ready_for_cause_repair"] is False
    assert report["rows"][0]["classification"] == "candidate_generated_but_grounding_rejected"
    assert report["rows"][1]["classification"] == "passed_displayed"


def test_step1_capture_summary_for_empty_logs_marks_backend_and_frontend_missing() -> None:
    summary = build_observation_diagnostic_capture_summary([], [], rows=[])

    assert summary["diagnostic_capture_status"] == DIAGNOSTIC_LOG_MISSING_OR_NOT_CAPTURED
    assert summary["backend_diagnostic_capture_status"] == BACKEND_DIAGNOSTIC_MISSING_OR_NOT_CAPTURED
    assert summary["frontend_diagnostic_capture_status"] == FRONTEND_DIAGNOSTIC_MISSING_OR_NOT_CAPTURED
    assert summary["capture_blockers"] == [
        BACKEND_DIAGNOSTIC_MISSING_OR_NOT_CAPTURED,
        FRONTEND_DIAGNOSTIC_MISSING_OR_NOT_CAPTURED,
    ]
    assert summary["classification"] == "unknown_diagnostic_missing"
