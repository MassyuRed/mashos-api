from __future__ import annotations

import json
import logging

import pytest

import emotion_submit_service as emotion_service
from emlis_ai_display_gate import decide_emlis_observation_display, phase8_display_gate_contract_ready
from emlis_ai_observation_diagnostic_lockdown import (
    DIAGNOSTIC_LOCKDOWN_VERSION,
    build_observation_diagnostic_lockdown,
    dump_observation_diagnostic,
)
from emlis_ai_types import GroundingReport, ListenerReaderReport, TemplateEchoReport

_SECRET_RAW_INPUT = "これは診断ログへ出してはいけない入力本文です"
_SECRET_COMMENT = "これは診断ログへ出してはいけないEmlis観測本文です"

_DIAGNOSTIC_ENV_NAMES = (
    "EMLIS_AI_OBSERVATION_DIAGNOSTIC_LOCKDOWN_LOG_ENABLED",
    "COCOLON_EMLIS_OBSERVATION_DIAGNOSTIC_LOCKDOWN_LOG_ENABLED",
    "EMLIS_AI_OBSERVATION_RESULT_LOG_ENABLED",
    "COCOLON_EMLIS_OBSERVATION_RESULT_LOG_ENABLED",
    "EMLIS_AI_OBSERVATION_DEBUG_LOG",
    "EMLIS_AI_OBSERVATION_DEBUG_LOGS",
)


def _clear_diagnostic_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in _DIAGNOSTIC_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)


def _backend_lockdown_records(caplog: pytest.LogCaptureFixture) -> list[dict]:
    prefix = "emlis_observation_diagnostic_lockdown "
    records: list[dict] = []
    for captured in caplog.records:
        message = captured.getMessage()
        if prefix not in message:
            continue
        records.append(json.loads(message.split(prefix, 1)[1]))
    return records


def _reader(passed: bool = True, reason: str = "") -> ListenerReaderReport:
    return ListenerReaderReport(
        understandable=passed,
        addressee_clear=True,
        speaker_integrity_ok=True,
        conversational=True,
        report_like=False,
        rejection_reasons=[] if passed else [reason or "reader_cannot_understand"],
    )


def _grounding(passed: bool = True, reason: str = "") -> GroundingReport:
    return GroundingReport(
        passed=passed,
        rejection_reasons=[] if passed else [reason or "unsupported_sentence"],
    )


def _template(passed: bool = True, reason: str = "") -> TemplateEchoReport:
    return TemplateEchoReport(
        passed=passed,
        rejection_reasons=[] if passed else [reason or "template_like"],
    )


def _meta_for_classification(*, status: str = "rejected", stage: str = "display", reason: str = "empty_comment_text", candidate_generated: bool = True, gate: str = "display", connection_status: str = "connected") -> dict:
    gate_results = {
        "reader": {"passed": True, "primary_reason": "passed", "rejection_reasons": []},
        "grounding": {"passed": True, "primary_reason": "passed", "rejection_reasons": []},
        "template_echo": {"passed": True, "primary_reason": "passed", "rejection_reasons": []},
        "display": {"passed": False, "primary_reason": reason, "rejection_reasons": [reason]},
    }
    if gate in {"reader", "grounding", "template_echo"}:
        gate_results[gate] = {"passed": False, "primary_reason": reason, "rejection_reasons": [reason]}
    if status == "passed":
        gate_results["display"] = {"passed": True, "primary_reason": "passed", "rejection_reasons": []}

    return {
        "observation_status": status,
        "observation_trace_id": f"emlisobs-step5-{gate}-{status}",
        "diagnostic_summary": {
            "observation_status": status,
            "stage": stage,
            "primary_reason": reason,
            "secondary_reasons": [reason] if reason != "passed" else [],
            "coverage_group": "step5_backend_contract",
            "composer_status": "generated" if candidate_generated else "unavailable",
            "composer_source": "ai_generated" if candidate_generated else "unavailable",
            "composer_client_resolution": {"connection_status": connection_status},
            "complete_candidate_seen": candidate_generated,
            "complete_candidate_generated": candidate_generated,
            "candidate_generated_before_display_gate": candidate_generated,
            "gate_results": gate_results,
            "display_rejection_reasons": [] if status == "passed" else [reason],
            "used_phrase_unit_ids": ["phrase-step5"] if candidate_generated else [],
            "relation_types": ["coexistence"] if candidate_generated else [],
            "repair_trace_count": 1 if gate == "grounding" else 0,
            "repair_aborted_count": 0,
        },
    }


def test_step5_helper_builds_required_backend_schema_and_never_serializes_text_payloads() -> None:
    meta = _meta_for_classification(gate="grounding", stage="grounding", reason="unsupported_sentence")
    meta["memo"] = _SECRET_RAW_INPUT
    meta["comment_text"] = _SECRET_COMMENT
    meta["diagnostic_summary"]["complete_reply_service_diagnostics"] = {
        "complete_candidate_seen": True,
        "complete_candidate_generated": True,
        "composer_status": "generated",
        "composer_source": "ai_generated",
        "used_evidence_span_count": 1,
        "used_phrase_unit_count": 1,
        "relation_types": ["coexistence"],
        "complete_repair_trace": [{"reason_code": "unsupported_sentence", "result": "not_repaired"}],
    }

    record = build_observation_diagnostic_lockdown(
        input_feedback_comment=_SECRET_COMMENT,
        input_feedback_meta=meta,
        emotion_log_id="emotion-step5-schema",
        created_at="2026-05-17T02:35:05.000000+00:00",
    )

    required_keys = {
        "version",
        "source",
        "emotion_log_id",
        "created_at",
        "trace_id",
        "observation_status",
        "comment_text_length",
        "comment_text_present",
        "stage",
        "primary_reason",
        "secondary_reasons",
        "composer_status",
        "composer_source",
        "composer_client_resolution",
        "candidate",
        "evidence_counts",
        "gate_results",
        "display_rejection_reasons",
        "self_repair",
        "classification",
        "raw_input_included",
        "comment_text_included",
    }
    assert required_keys.issubset(record.keys())
    assert record["version"] == DIAGNOSTIC_LOCKDOWN_VERSION
    assert record["classification"] == "candidate_generated_but_grounding_rejected"
    assert record["candidate"]["generated_before_display_gate"] is True
    assert record["gate_results"]["grounding"]["passed"] is False
    assert record["raw_input_included"] is False
    assert record["comment_text_included"] is False

    dumped = dump_observation_diagnostic(record)
    assert "\n" not in dumped
    assert _SECRET_RAW_INPUT not in dumped
    assert _SECRET_COMMENT not in dumped
    parsed = json.loads(dumped)
    assert parsed["comment_text_length"] == len(_SECRET_COMMENT)
    assert parsed["comment_text_included"] is False


@pytest.mark.parametrize(
    ("meta", "comment", "expected"),
    [
        (
            {
                "observation_status": "unavailable",
                "rejection_reasons": ["emlis_ai_timeout_or_error"],
                "diagnostic_summary": {"stage": "composer", "primary_reason": "emlis_ai_timeout_or_error"},
            },
            "",
            "backend_exception_or_timeout",
        ),
        (
            _meta_for_classification(
                status="unavailable",
                stage="flag",
                reason="default_limited_composer_feature_disabled",
                candidate_generated=False,
                connection_status="blocked_feature_flag",
            ),
            "",
            "pre_connection_stop",
        ),
        (_meta_for_classification(candidate_generated=False, reason="composer_source_unavailable"), "", "candidate_missing"),
        (_meta_for_classification(gate="reader", stage="reader", reason="relation_not_expressed"), "", "candidate_generated_but_reader_rejected"),
        (_meta_for_classification(gate="grounding", stage="grounding", reason="unsupported_sentence"), "", "candidate_generated_but_grounding_rejected"),
        (_meta_for_classification(gate="template_echo", stage="template", reason="template_like"), "", "candidate_generated_but_template_rejected"),
        (_meta_for_classification(gate="display", stage="display", reason="phase_not_complete"), "", "candidate_generated_but_display_rejected"),
        (_meta_for_classification(status="passed", stage="display", reason="passed"), _SECRET_COMMENT, "passed_displayed"),
    ],
)
def test_step5_backend_meta_fixtures_classify_all_next_step_branches(meta: dict, comment: str, expected: str) -> None:
    record = build_observation_diagnostic_lockdown(
        input_feedback_comment=comment,
        input_feedback_meta=meta,
        emotion_log_id="emotion-step5-branch",
        created_at="2026-05-17T02:36:22.000000+00:00",
    )

    assert record["classification"] == expected
    dumped = dump_observation_diagnostic(record)
    assert _SECRET_COMMENT not in dumped
    assert _SECRET_RAW_INPUT not in dumped


def test_step5_complete_meta_cannot_force_public_passed_status_or_comment_text() -> None:
    meta = _meta_for_classification(gate="display", status="rejected", stage="display", reason="empty_comment_text")
    meta["diagnostic_summary"].update(
        {
            "observation_diagnostic_lockdown_ready": True,
            "complete_candidate_seen": True,
            "complete_candidate_generated": True,
            "candidate_generated_before_display_gate": True,
            "complete_candidate_status": "generated",
            "complete_candidate_source": "ai_generated",
            "gate_results_extractable_for_observation_diagnostic": True,
            "repair_extractable_for_observation_diagnostic": True,
        }
    )

    record = build_observation_diagnostic_lockdown(
        input_feedback_comment="",
        input_feedback_meta=meta,
        emotion_log_id="emotion-step5-non-passed",
        created_at="2026-05-17T02:37:00.000000+00:00",
    )

    assert record["observation_status"] == "rejected"
    assert record["comment_text_length"] == 0
    assert record["candidate"]["generated"] is True
    assert record["classification"] == "candidate_generated_but_display_rejected"
    assert record["classification"] != "passed_displayed"


def test_step5_display_gate_contract_stays_fail_closed_for_non_passed_outputs() -> None:
    decision = decide_emlis_observation_display(
        comment_text=_SECRET_COMMENT,
        reader_report=_reader(True),
        grounding_report=_grounding(False, "unsupported_sentence"),
        template_echo_report=_template(True),
        composer_source="ai_generated",
        phase_completion_ready=True,
    )

    assert decision.observation_status == "rejected"
    assert decision.comment_text == ""
    assert "unsupported_sentence" in decision.rejection_reasons
    assert phase8_display_gate_contract_ready(decision) is True
    assert _SECRET_COMMENT not in json.dumps(decision.gate_trace, ensure_ascii=False)


def test_step5_display_gate_contract_allows_text_only_for_passed_outputs() -> None:
    decision = decide_emlis_observation_display(
        comment_text=_SECRET_COMMENT,
        reader_report=_reader(True),
        grounding_report=_grounding(True),
        template_echo_report=_template(True),
        composer_source="ai_generated",
        phase_completion_ready=True,
    )

    assert decision.observation_status == "passed"
    assert decision.comment_text == _SECRET_COMMENT
    assert decision.rejection_reasons == []
    assert phase8_display_gate_contract_ready(decision) is True


def test_step5_backend_lockdown_log_is_opt_in_one_line_and_meta_only(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    _clear_diagnostic_env(monkeypatch)
    caplog.set_level(logging.INFO)

    emotion_service._log_emlis_ai_observation_diagnostic_lockdown(
        input_feedback_comment=_SECRET_COMMENT,
        input_feedback_meta=_meta_for_classification(status="passed", stage="display", reason="passed"),
        emotion_log_id="emotion-step5-disabled",
        created_at="2026-05-17T02:38:00.000000+00:00",
    )
    assert _backend_lockdown_records(caplog) == []
    assert _SECRET_COMMENT not in caplog.text

    monkeypatch.setenv("EMLIS_AI_OBSERVATION_DIAGNOSTIC_LOCKDOWN_LOG_ENABLED", "1")
    caplog.clear()
    emotion_service._log_emlis_ai_observation_diagnostic_lockdown(
        input_feedback_comment=_SECRET_COMMENT,
        input_feedback_meta=_meta_for_classification(status="passed", stage="display", reason="passed"),
        emotion_log_id="emotion-step5-enabled",
        created_at="2026-05-17T02:38:01.000000+00:00",
    )

    records = _backend_lockdown_records(caplog)
    assert len(records) == 1
    assert records[0]["emotion_log_id"] == "emotion-step5-enabled"
    assert records[0]["classification"] == "passed_displayed"
    assert records[0]["comment_text_length"] == len(_SECRET_COMMENT)
    assert records[0]["comment_text_included"] is False
    assert _SECRET_COMMENT not in caplog.text


def test_step5_dict_reason_payloads_keep_codes_without_serializing_text_fields() -> None:
    meta = _meta_for_classification(gate="grounding", stage="grounding", reason="unsupported_sentence")
    meta["diagnostic_summary"]["gate_results"]["grounding"] = {
        "passed": False,
        "rejection_reasons": [
            {"reason_code": "unsupported_sentence", "text": _SECRET_RAW_INPUT},
            {"reason": {"code": "relation_not_expressed"}, "preview": _SECRET_COMMENT},
        ],
    }
    meta["diagnostic_summary"]["gate_results"]["display"] = {
        "passed": False,
        "rejection_reasons": [{"reason_code": "unsupported_sentence", "text": _SECRET_COMMENT}],
    }
    meta["diagnostic_summary"]["display_rejection_reasons"] = [
        {"reason_code": "unsupported_sentence", "text": _SECRET_COMMENT}
    ]
    meta["current_input"] = {"memo": _SECRET_RAW_INPUT}
    meta["comment_text"] = _SECRET_COMMENT

    record = build_observation_diagnostic_lockdown(
        input_feedback_comment="",
        input_feedback_meta=meta,
        emotion_log_id="emotion-step5-dict-reason",
        created_at="2026-05-17T02:39:00.000000+00:00",
    )
    dumped = dump_observation_diagnostic(record)
    parsed = json.loads(dumped)

    assert parsed["classification"] == "candidate_generated_but_grounding_rejected"
    assert parsed["gate_results"]["grounding"]["rejection_reasons"] == [
        "unsupported_sentence",
        "relation_not_expressed",
    ]
    assert parsed["display_rejection_reasons"] == ["unsupported_sentence"]
    assert _SECRET_RAW_INPUT not in dumped
    assert _SECRET_COMMENT not in dumped
    assert '"preview"' not in dumped
    assert '"text"' not in dumped
