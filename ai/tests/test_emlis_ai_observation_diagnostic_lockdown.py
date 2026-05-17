from __future__ import annotations

import json

import pytest

from emlis_ai_observation_diagnostic_lockdown import (
    DIAGNOSTIC_LOCKDOWN_VERSION,
    build_observation_diagnostic_lockdown,
    classify_observation_diagnostic,
    dump_observation_diagnostic,
)


SECRET_COMMENT = "これはログへ出してはいけない観測本文です"
SECRET_RAW_INPUT = "これはログへ出してはいけない入力本文です"


def _gate(passed: bool, reason: str = "") -> dict:
    return {
        "passed": passed,
        "primary_reason": "passed" if passed else reason,
        "rejection_reasons": [] if passed else [reason],
    }


def _base_record(**overrides):
    record = {
        "observation_status": "rejected",
        "comment_text_length": 0,
        "rejection_reasons": [],
        "stage": "display",
        "composer_client_resolution": {"connection_status": "connected"},
        "candidate": {"generated": True},
        "gate_results": {
            "reader": _gate(True),
            "grounding": _gate(True),
            "template_echo": _gate(True),
            "display": _gate(False, "empty_comment_text"),
        },
        "display_rejection_reasons": ["empty_comment_text"],
    }
    record.update(overrides)
    return record


def test_classify_backend_exception_or_timeout():
    record = _base_record(rejection_reasons=["emlis_ai_timeout_or_error"])

    assert classify_observation_diagnostic(record) == "backend_exception_or_timeout"


@pytest.mark.parametrize(
    ("record", "expected"),
    [
        (
            _base_record(
                observation_status="passed",
                comment_text_length=32,
                gate_results={
                    "reader": _gate(True),
                    "grounding": _gate(True),
                    "template_echo": _gate(True),
                    "display": _gate(True),
                },
            ),
            "passed_displayed",
        ),
        (
            _base_record(
                observation_status="passed",
                comment_text_length=32,
                frontend={"modal_opened": False},
                gate_results={
                    "reader": _gate(True),
                    "grounding": _gate(True),
                    "template_echo": _gate(True),
                    "display": _gate(True),
                },
            ),
            "passed_backend_frontend_hidden",
        ),
        (_base_record(stage="flag"), "pre_connection_stop"),
        (_base_record(composer_client_resolution={"connection_status": "blocked_feature_flag"}), "pre_connection_stop"),
        (_base_record(candidate={"generated": False}), "candidate_missing"),
        (
            _base_record(
                gate_results={
                    "reader": _gate(False, "relation_not_expressed"),
                    "grounding": _gate(True),
                    "template_echo": _gate(True),
                    "display": _gate(False, "relation_not_expressed"),
                }
            ),
            "candidate_generated_but_reader_rejected",
        ),
        (
            _base_record(
                gate_results={
                    "reader": _gate(True),
                    "grounding": _gate(False, "unsupported_sentence"),
                    "template_echo": _gate(True),
                    "display": _gate(False, "unsupported_sentence"),
                }
            ),
            "candidate_generated_but_grounding_rejected",
        ),
        (
            _base_record(
                gate_results={
                    "reader": _gate(True),
                    "grounding": _gate(True),
                    "template_echo": _gate(False, "template_like"),
                    "display": _gate(False, "template_like"),
                }
            ),
            "candidate_generated_but_template_rejected",
        ),
        (_base_record(), "candidate_generated_but_display_rejected"),
    ],
)
def test_classify_observation_diagnostic_categories(record, expected):
    assert classify_observation_diagnostic(record) == expected


def test_build_lockdown_normalizes_existing_meta_without_text_payloads():
    meta = {
        "observation_status": "rejected",
        "observation_trace_id": "emlisobs-test-001",
        "rejection_reasons": ["unsupported_sentence"],
        "diagnostic_summary": {
            "observation_status": "rejected",
            "stage": "grounding",
            "primary_reason": "unsupported_sentence",
            "secondary_reasons": ["unsupported_sentence"],
            "coverage_group": "conflict_recovery",
            "coverage_scope": "current_input_core",
            "composer_status": "generated",
            "registry_resolution": {"connection_status": "connected"},
            "used_evidence_span_count": 2,
            "gate_results": {
                "reader": _gate(True),
                "grounding": _gate(False, "unsupported_sentence"),
                "template_echo": _gate(True),
                "display": _gate(False, "unsupported_sentence"),
            },
            "complete_reply_service_diagnostics": {
                "complete_candidate_seen": True,
                "complete_candidate_generated": True,
                "composer_status": "generated",
                "composer_source": "ai_generated",
                "used_evidence_span_count": 2,
                "used_phrase_unit_count": 2,
                "relation_types": ["contrast", "recovery"],
                "repair_trace_count": 1,
                "repair_aborted_count": 0,
                "self_repair": {"attempted": True, "status": "completed"},
            },
        },
        # This deliberately mimics hostile accidental meta. The builder must not
        # copy text payload keys into the lockdown record.
        "comment_text": SECRET_COMMENT,
        "current_input": {"memo": SECRET_RAW_INPUT},
    }

    record = build_observation_diagnostic_lockdown(
        input_feedback_comment=SECRET_COMMENT,
        input_feedback_meta=meta,
        emotion_log_id="emotion-001",
        created_at="2026-05-17T02:35:05Z",
    )

    assert record["version"] == DIAGNOSTIC_LOCKDOWN_VERSION
    assert record["trace_id"] == "emlisobs-test-001"
    assert record["classification"] == "candidate_generated_but_grounding_rejected"
    assert record["comment_text_length"] == len(SECRET_COMMENT)
    assert record["comment_text_present"] is True
    assert record["candidate"]["generated"] is True
    assert record["candidate"]["source"] == "ai_generated"
    assert record["evidence_counts"]["used_evidence_span_count"] == 2
    assert record["evidence_counts"]["used_phrase_unit_count"] == 2
    assert record["relation_types"] == ["contrast", "recovery"]
    assert record["self_repair"]["attempted"] is True
    assert record["raw_input_included"] is False
    assert record["comment_text_included"] is False
    assert "comment_text" not in record
    assert "current_input" not in record

    dumped = dump_observation_diagnostic(record)
    parsed = json.loads(dumped)
    assert parsed["comment_text_included"] is False
    assert SECRET_COMMENT not in dumped
    assert SECRET_RAW_INPUT not in dumped


def test_build_lockdown_falls_back_to_nested_multi_perspective_summary():
    meta = {
        "observation_status": "unavailable",
        "multi_perspective": {
            "diagnostic_summary": {
                "observation_status": "unavailable",
                "stage": "flag",
                "primary_reason": "default_limited_composer_feature_disabled",
                "registry_resolution": {"connection_status": "blocked_feature_flag"},
            }
        },
    }

    record = build_observation_diagnostic_lockdown(
        input_feedback_comment="",
        input_feedback_meta=meta,
        emotion_log_id="emotion-flag",
        created_at="2026-05-17T02:35:05Z",
    )

    assert record["stage"] == "flag"
    assert record["classification"] == "pre_connection_stop"
    assert record["comment_text_length"] == 0


def test_build_lockdown_reads_step3_reply_meta_aliases_without_text_payload():
    meta = {
        "observation_status": "rejected",
        "observation_trace_id": "emlisobs-step3-reply-meta",
        "diagnostic_summary": {
            "observation_diagnostic_lockdown_ready": True,
            "candidate_generated_before_display_gate": True,
            "complete_candidate_seen": True,
            "complete_candidate_generated": True,
            "complete_candidate_status": "generated",
            "complete_candidate_source": "ai_generated",
            "stage": "grounding",
            "primary_reason": "unsupported_sentence",
            "coverage_group": "conflict",
            "display_rejection_reasons": ["unsupported_sentence"],
            "used_phrase_unit_ids": ["phrase-step3"],
            "relation_types": ["contrast"],
            "self_repair_status": "aborted",
            "repair_trace_count": 1,
            "repair_aborted_count": 1,
            "repair_abort_reasons": ["non_repairable_gate_reason"],
            "gate_results": {
                "reader": {"passed": True, "primary_reason": "passed"},
                "grounding": {
                    "passed": False,
                    "primary_reason": "unsupported_sentence",
                    "rejection_reasons": ["unsupported_sentence"],
                },
                "template_echo": {"passed": True, "primary_reason": "passed"},
                "display": {
                    "passed": False,
                    "primary_reason": "unsupported_sentence",
                    "rejection_reasons": ["unsupported_sentence"],
                },
            },
        },
    }

    record = build_observation_diagnostic_lockdown(
        input_feedback_comment="",
        input_feedback_meta=meta,
        emotion_log_id="emotion-step3",
        created_at="2026-05-17T03:00:00Z",
    )

    assert record["classification"] == "candidate_generated_but_grounding_rejected"
    assert record["candidate"]["generated"] is True
    assert record["candidate"]["generated_before_display_gate"] is True
    assert record["candidate"]["status"] == "generated"
    assert record["candidate"]["source"] == "ai_generated"
    assert record["used_phrase_unit_ids"] == ["phrase-step3"]
    assert record["relation_types"] == ["contrast"]
    assert record["self_repair"]["status"] == "aborted"
    assert record["self_repair"]["repair_trace_count"] == 1
    assert record["self_repair"]["aborted_count"] == 1
    dumped = dump_observation_diagnostic(record)
    assert "これはログへ出してはいけない" not in dumped
    assert record["raw_input_included"] is False


def test_dump_rejects_forbidden_text_payload_key():
    with pytest.raises(ValueError):
        dump_observation_diagnostic({"version": DIAGNOSTIC_LOCKDOWN_VERSION, "memo": SECRET_RAW_INPUT})
