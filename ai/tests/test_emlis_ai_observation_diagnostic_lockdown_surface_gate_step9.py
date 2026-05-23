# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step9 submit-level diagnostic lockdown coverage for runtime surface gate.

Render screenshots usually expose the ``emlis_observation_diagnostic_lockdown``
row. These regressions keep runtime surface blocks visible there without logging
raw input or candidate body text and without converting blocked candidates into
``passed + comment_text``.
"""

import json

from emlis_ai_complete_reply_diagnostics_service import build_complete_reply_service_diagnostics
from emlis_ai_display_gate import decide_emlis_observation_display, phase8_display_gate_contract_ready
from emlis_ai_observation_diagnostic_lockdown import (
    DIAGNOSTIC_LOCKDOWN_VERSION,
    build_observation_diagnostic_lockdown,
    classify_observation_diagnostic,
    dump_observation_diagnostic,
)
from emlis_ai_runtime_surface_pre_return_gate import build_runtime_surface_pre_return_gate_report
from emlis_ai_types import GroundingReport, ListenerReaderReport, TemplateEchoReport
from fixtures.emlis_ai_runtime_surface_red_fixtures import RUNTIME_SURFACE_BASELINE_RED_FIXTURES


_BAD_SURFACE = (
    "Emlisです。\n"
    "今までことが中心にあります。\n"
    "その中でも、大丈夫ことも見えています。\n"
    "その中でも、創作をする時にリアルさを求めることも重なっています。"
)
_SECRET_RAW_INPUT = "これはdiagnostic lockdownへ出してはいけない入力本文です"
_FORBIDDEN_SURFACE_MARKERS = (
    "今までこと",
    "大丈夫こと",
    "まだないかこと",
    "しれないどれこと",
    "上手になせなくてこと",
    "が中心にあります",
    "その中でも",
)

_PASSING_READER = ListenerReaderReport(
    understandable=True,
    addressee_clear=True,
    speaker_integrity_ok=True,
    conversational=True,
    report_like=False,
    confidence=1.0,
)
_PASSING_GROUNDING = GroundingReport(passed=True, coverage_ratio=1.0, confidence=1.0)
_PASSING_TEMPLATE = TemplateEchoReport(passed=True)


def _gate(passed: bool, reason: str = "") -> dict:
    return {
        "passed": passed,
        "primary_reason": "passed" if passed else reason,
        "rejection_reasons": [] if passed else [reason],
    }


def _surface_step8_meta() -> dict:
    return {
        "version": "emlis.runtime_surface_diagnostics_scorecard.v1",
        "step8_runtime_surface_diagnostics_ready": True,
        "runtime_surface_diagnostics_scorecard_updated": True,
        "runtime_surface_pre_return_gate_evaluated": True,
        "runtime_surface_pre_return_gate_passed": False,
        "runtime_surface_pre_return_gate_final_passed": False,
        "runtime_surface_pre_return_gate_action": "rerender_shallow_v2",
        "runtime_surface_pre_return_gate_rejection_reasons": [
            "surface_template_major",
            "malformed_phrase_unit",
            "same_connector_run",
        ],
        "runtime_surface_pre_return_gate_scorecard_connected": True,
        "surface_template_major_blocked": True,
        "malformed_phrase_unit_blocked_count": 2,
        "shallow_realizer_version": "shallow_surface_realizer.v2",
        "shallow_v2_used": True,
        "low_information_specificity_used": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
    }


def _candidate(surface_report: dict) -> dict:
    return {
        "status": "generated",
        "composer_source": "ai_generated",
        "composer_model": "emlis.limited_composer.v1",
        "generation_method": "limited_current_input_core",
        "coverage_scope": "current_input_core",
        "used_evidence_span_ids": ["ev-step9-surface-lockdown"],
        "used_relation_ids": ["rel-step9-surface-lockdown"],
        "composer_meta": {
            "profile_key": "current_input_core",
            "coverage_scope": "current_input_core",
            "shallow_observation_path": True,
            "composer_source": "ai_generated",
            "shallow_realizer_version": "shallow_surface_realizer.v2",
            "shallow_v2_used": True,
            "malformed_phrase_unit_blocked_count": int(surface_report.get("malformed_phrase_unit_count") or 0),
            "runtime_surface_pre_return_gate": surface_report,
            "runtime_surface_pre_return_gate_evaluated": bool(surface_report.get("evaluated")),
            "runtime_surface_pre_return_gate_passed": bool(surface_report.get("passed")),
            "runtime_surface_pre_return_gate_action": str(surface_report.get("action") or ""),
            "runtime_surface_pre_return_gate_rejection_reasons": list(surface_report.get("rejection_reasons") or []),
            "surface_template_major_blocked": "surface_template_major" in set(surface_report.get("rejection_reasons") or []),
            "raw_input_included": False,
            "comment_text_body_included": False,
            "display_gate_relaxed": False,
        },
    }


def test_step9_diagnostic_lockdown_classifies_runtime_surface_block_without_text_payload() -> None:
    meta = {
        "observation_status": "rejected",
        "observation_trace_id": "emlisobs-step9-surface",
        "rejection_reasons": ["runtime_surface_pre_return_gate_failed"],
        "diagnostic_summary": {
            "observation_status": "rejected",
            "stage": "display",
            "primary_reason": "runtime_surface_pre_return_gate_failed",
            "display_rejection_reasons": ["runtime_surface_pre_return_gate_failed", "surface_template_major"],
            "complete_candidate_seen": True,
            "complete_candidate_generated": True,
            "complete_candidate_status": "generated",
            "complete_candidate_source": "ai_generated",
            "composer_status": "generated",
            "composer_source": "ai_generated",
            "registry_resolution": {"connection_status": "connected"},
            "runtime_surface_step8_diagnostics": _surface_step8_meta(),
            "gate_results": {
                "reader": _gate(True),
                "grounding": _gate(True),
                "template_echo": _gate(True),
                "display": _gate(False, "runtime_surface_pre_return_gate_failed"),
            },
        },
        # Hostile accidental payloads. The lockdown row must not copy these.
        "comment_text": _BAD_SURFACE,
        "current_input": {"memo": _SECRET_RAW_INPUT},
    }

    record = build_observation_diagnostic_lockdown(
        input_feedback_comment="",
        input_feedback_meta=meta,
        emotion_log_id="emotion-step9-surface",
        created_at="2026-05-23T00:00:00Z",
    )

    assert record["version"] == DIAGNOSTIC_LOCKDOWN_VERSION
    assert record["classification"] == "surface_quality_blocked"
    assert classify_observation_diagnostic(record) == "surface_quality_blocked"
    assert record["comment_text_present"] is False
    assert record["candidate"]["generated"] is True
    assert record["runtime_surface_pre_return_gate_evaluated"] is True
    assert record["runtime_surface_pre_return_gate_passed"] is False
    assert record["runtime_surface_pre_return_gate_action"] == "rerender_shallow_v2"
    assert "surface_template_major" in record["runtime_surface_pre_return_gate_rejection_reasons"]
    assert record["surface_template_major_blocked"] is True
    assert record["malformed_phrase_unit_blocked_count"] >= 2
    assert record["runtime_surface_diagnostics_scorecard_updated"] is True
    assert record["runtime_surface_pre_return_gate_scorecard_connected"] is True
    assert record["raw_input_included"] is False
    assert record["comment_text_included"] is False
    assert record["runtime_surface"]["raw_input_included"] is False
    assert record["runtime_surface"]["comment_text_body_included"] is False

    dumped = dump_observation_diagnostic(record)
    parsed = json.loads(dumped)
    assert parsed["classification"] == "surface_quality_blocked"
    assert _BAD_SURFACE not in dumped
    assert _SECRET_RAW_INPUT not in dumped
    for marker in _FORBIDDEN_SURFACE_MARKERS:
        assert marker not in dumped
    assert '"comment_text":' not in dumped
    assert '"raw_input":' not in dumped


def test_step9_observation_diagnostic_lockdown_reports_actual_surface_gate_block_meta_only() -> None:
    fixture = RUNTIME_SURFACE_BASELINE_RED_FIXTURES[1]
    surface_report = build_runtime_surface_pre_return_gate_report(
        comment_text=fixture.public_body,
        composer_meta=fixture.composer_meta,
        rerender_allowed=True,
        rerender_attempted=True,
    )
    decision = decide_emlis_observation_display(
        comment_text=fixture.public_body,
        reader_report=_PASSING_READER,
        grounding_report=_PASSING_GROUNDING,
        template_echo_report=_PASSING_TEMPLATE,
        composer_source="ai_generated",
        phase_completion_ready=True,
        runtime_surface_pre_return_gate_report=surface_report,
    )
    diagnostics = build_complete_reply_service_diagnostics(
        composer_candidate=_candidate(surface_report),
        display_decision=decision,
        gate_trace=decision.gate_trace,
        diagnostic_summary={
            "trace_id": "step9-diagnostic-lockdown-surface-gate",
            "emotion_log_id": "emotion-step9-surface-gate",
            "coverage_scope": "current_input_core",
        },
    )
    input_feedback_meta = {
        "observation_status": decision.observation_status,
        "rejection_reasons": list(decision.rejection_reasons),
        "diagnostic_summary": {
            "trace_id": "step9-diagnostic-lockdown-surface-gate",
            "emotion_log_id": "emotion-step9-surface-gate",
            "coverage_scope": "current_input_core",
            "complete_reply_service_diagnostics": diagnostics,
            "scorecard_event": diagnostics.get("scorecard_event", {}),
            "runtime_surface_step8_diagnostics": diagnostics.get("runtime_surface_step8_diagnostics", {}),
        },
        "complete_reply_service_diagnostics": diagnostics,
        "scorecard_event": diagnostics.get("scorecard_event", {}),
        "runtime_surface_pre_return_gate": surface_report,
    }

    record = build_observation_diagnostic_lockdown(
        input_feedback_comment=decision.comment_text,
        input_feedback_meta=input_feedback_meta,
        emotion_log_id="emotion-step9-surface-gate",
        created_at="2026-05-23T00:00:00Z",
    )

    assert decision.observation_status != "passed"
    assert decision.comment_text == ""
    assert phase8_display_gate_contract_ready(decision)
    assert record["version"] == DIAGNOSTIC_LOCKDOWN_VERSION
    assert record["classification"] == "surface_quality_blocked"
    assert record["comment_text_present"] is False
    assert record["comment_text_length"] == 0
    assert record["runtime_surface_pre_return_gate_evaluated"] is True
    assert record["runtime_surface_pre_return_gate_passed"] is False
    assert record["surface_template_major_blocked"] is True
    assert record["malformed_phrase_unit_blocked_count"] >= 1
    assert "surface_template_major" in record["runtime_surface_pre_return_gate_rejection_reasons"]
    assert "runtime_surface_pre_return_gate_failed" in record["display_rejection_reasons"]
    assert record["gate_results"]["display"]["passed"] is False
    assert record["raw_input_included"] is False
    assert record["comment_text_included"] is False

    dumped = dump_observation_diagnostic(record)
    parsed = json.loads(dumped)
    assert parsed["runtime_surface_pre_return_gate_evaluated"] is True
    assert parsed["runtime_surface_pre_return_gate_passed"] is False
    for marker in _FORBIDDEN_SURFACE_MARKERS:
        assert marker not in dumped
    assert '"comment_text":' not in dumped
    assert '"raw_input":' not in dumped
    assert '"memo":' not in dumped


def test_step9_diagnostic_lockdown_keeps_ordinary_display_rejection_classification() -> None:
    record = build_observation_diagnostic_lockdown(
        input_feedback_comment="",
        input_feedback_meta={
            "observation_status": "rejected",
            "diagnostic_summary": {
                "stage": "display",
                "primary_reason": "empty_comment_text",
                "display_rejection_reasons": ["empty_comment_text"],
                "complete_candidate_generated": True,
                "complete_candidate_status": "generated",
                "complete_candidate_source": "ai_generated",
                "registry_resolution": {"connection_status": "connected"},
                "gate_results": {
                    "reader": _gate(True),
                    "grounding": _gate(True),
                    "template_echo": _gate(True),
                    "display": _gate(False, "empty_comment_text"),
                },
            },
        },
        emotion_log_id="emotion-step9-display",
        created_at="2026-05-23T00:01:00Z",
    )

    assert record["classification"] == "candidate_generated_but_display_rejected"
    assert record["runtime_surface_pre_return_gate_evaluated"] is False
    assert record["surface_template_major_blocked"] is False
