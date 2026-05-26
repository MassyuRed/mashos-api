from __future__ import annotations

import json
from types import SimpleNamespace

from emlis_ai_complete_composer_initial_meta import COMPLETE_COMPOSER_INITIAL_MODEL
from emlis_ai_complete_composer_types import COMPLETE_COMPOSER_GENERATION_METHOD
from emlis_ai_complete_reply_diagnostics_service import (
    build_complete_reply_service_diagnostics,
    build_positive_recovery_relation_diagnostic,
)
from emlis_ai_display_gate import build_emlis_gate_trace
from emlis_ai_listener_reader_judge import judge_listener_readability
from emlis_ai_relation_surface_contract import RELATION_SURFACE_CONTRACT_VERSION
from emlis_ai_types import DisplayDecision, GroundingReport, TemplateEchoReport


def _positive_recovery_text() -> str:
    return "\n".join(
        [
            "Emlisです。",
            "小さな回復が少し戻ってきています。",
            "中心にある感覚として形を取り直しています。",
            "戻ってくる動きと前段の負荷が同じ流れの中でつながっています。",
        ]
    )


def _fake_complete_candidate() -> SimpleNamespace:
    relation_report = {
        "relation_surface_contract_version": RELATION_SURFACE_CONTRACT_VERSION,
        "surface_recovery_relation_line_aligned": True,
        "surface_relation_marker_keys": ["recovery_load_bridge_v1"],
        "reader_relation_signal_detected": True,
        "reader_relation_signal_count": 1,
        "reader_relation_signal_keys": ["recovery_load_bridge"],
        "reader_relation_signal_relation_types": ["recovery"],
        "raw_input_included": False,
    }
    self_repair = {
        "self_repair_relation_marker_applied": True,
        "self_repair_relation_marker_key": "recovery_load_bridge_v1",
        "self_repair_relation_marker_keys": ["recovery_load_bridge_v1"],
        "self_repair_relation_marker_count": 1,
        "self_repair_relation_marker_signal_detected": True,
        "self_repair_relation_marker_signal_count": 1,
        "self_repair_relation_marker_signal_keys": ["recovery_load_bridge"],
        "self_repair_relation_marker_signal_relation_types": ["recovery"],
        "self_repair_relation_marker_meaning_added": False,
        "self_repair_relation_marker_gate_relaxed": False,
        "raw_input_included": False,
    }
    return SimpleNamespace(
        status="generated",
        composer_source="ai_generated",
        composer_model=COMPLETE_COMPOSER_INITIAL_MODEL,
        generation_method=COMPLETE_COMPOSER_GENERATION_METHOD,
        generation_scope="scoped_graph_evidence_composer",
        coverage_scope="positive_recovery",
        used_evidence_span_ids=["span-load", "span-repair"],
        used_relation_ids=["recovery"],
        composer_meta={
            "complete_composer_client_added": True,
            "composer_model": COMPLETE_COMPOSER_INITIAL_MODEL,
            "generation_method": COMPLETE_COMPOSER_GENERATION_METHOD,
            "coverage_group": "positive_recovery",
            "relation_types": ["recovery"],
            "relation_surface_contract_version": RELATION_SURFACE_CONTRACT_VERSION,
            "surface_realizer": {
                "relation_surface_contract_version": RELATION_SURFACE_CONTRACT_VERSION,
                "relation_surface_report": relation_report,
                "raw_input_included": False,
            },
            "surface_signature": relation_report,
            "self_repair": self_repair,
            "self_repair_report_v2": self_repair,
            "repair_trace_v2": [
                {
                    "reason_code": "relation_not_expressed",
                    "self_repair_relation_marker_applied": True,
                    "self_repair_relation_marker_key": "recovery_load_bridge_v1",
                    "self_repair_relation_marker_signal_keys": ["recovery_load_bridge"],
                    "meaning_added": False,
                    "gate_relaxed": False,
                    "raw_input_included": False,
                }
            ],
            "raw_input_included": False,
        },
    )


def test_step5_reader_report_exposes_relation_signal_meta_without_gate_relaxation() -> None:
    report = judge_listener_readability(_positive_recovery_text(), expected_relation_types=("positive_recovery",))

    assert report.understandable is True
    assert report.relation_surface_contract_version == RELATION_SURFACE_CONTRACT_VERSION
    assert report.reader_relation_signal_detected is True
    assert report.reader_relation_signal_count >= 1
    assert "recovery_load_bridge" in report.reader_relation_signal_keys
    assert "recovery" in report.reader_relation_signal_relation_types
    assert report.expected_relation_types == ["recovery"]
    assert report.raw_input_included is False
    assert "relation_not_expressed" not in report.rejection_reasons


def test_step5_reader_gate_trace_carries_relation_signal_to_diagnostics() -> None:
    reader = judge_listener_readability(_positive_recovery_text(), expected_relation_types=("positive_recovery",))
    gate_trace = build_emlis_gate_trace(
        reader_report=reader,
        grounding_report=GroundingReport(passed=True, coverage_ratio=1.0),
        template_echo_report=TemplateEchoReport(passed=True),
        composer_source="ai_generated",
        phase_completion_ready=True,
    )

    reader_gate = gate_trace["reader"]
    assert reader_gate["passed"] is True
    assert reader_gate["relation_surface_contract_version"] == RELATION_SURFACE_CONTRACT_VERSION
    assert reader_gate["reader_relation_signal_detected"] is True
    assert "recovery_load_bridge" in reader_gate["reader_relation_signal_keys"]
    assert reader_gate["reader_relation_signal_raw_input_included"] is False


def test_step5_complete_reply_diagnostics_connects_reader_and_self_repair_relation_meta() -> None:
    reader = judge_listener_readability(_positive_recovery_text(), expected_relation_types=("positive_recovery",))
    gate_trace = build_emlis_gate_trace(
        reader_report=reader,
        grounding_report=GroundingReport(passed=True, coverage_ratio=1.0),
        template_echo_report=TemplateEchoReport(passed=True),
        composer_source="ai_generated",
        phase_completion_ready=True,
    )
    candidate = _fake_complete_candidate()
    display_decision = DisplayDecision(
        observation_status="rejected",
        comment_text="",
        rejection_reasons=["display_gate_rejected"],
        gate_trace=gate_trace,
    )

    diagnostic = build_positive_recovery_relation_diagnostic(
        composer_candidate=candidate,
        gate_trace=gate_trace,
    )
    reply_diagnostics = build_complete_reply_service_diagnostics(
        composer_candidate=candidate,
        display_decision=display_decision,
        gate_trace=gate_trace,
        diagnostic_summary={"coverage_group": "positive_recovery"},
    )

    assert diagnostic["diagnostic_connected"] is True
    assert diagnostic["reader_relation_signal_detected"] is True
    assert diagnostic["self_repair_relation_marker_applied"] is True
    assert diagnostic["self_repair_relation_marker_key"] == "recovery_load_bridge_v1"
    assert diagnostic["self_repair_relation_marker_meaning_added"] is False
    assert diagnostic["self_repair_relation_marker_gate_relaxed"] is False
    assert diagnostic["raw_input_included"] is False

    relation_diagnostic = reply_diagnostics["positive_recovery_relation_diagnostic"]
    assert relation_diagnostic == reply_diagnostics["step5_relation_diagnostic"]
    assert relation_diagnostic["reader_relation_signal_detected"] is True
    assert "recovery_load_bridge" in relation_diagnostic["reader_relation_signal_keys"]
    assert relation_diagnostic["self_repair_relation_marker_applied"] is True
    assert relation_diagnostic["self_repair_relation_marker_key"] == "recovery_load_bridge_v1"
    assert reply_diagnostics["reader_relation_signal_detected"] is True
    assert reply_diagnostics["self_repair_relation_marker_applied"] is True
    assert reply_diagnostics["response_shape_changed"] is False
    assert reply_diagnostics["display_gate_relaxed"] is False

    serialized = json.dumps(reply_diagnostics, ensure_ascii=False, sort_keys=True)
    assert "\"raw_text\":" not in serialized
    assert "current_input" not in serialized
    assert "source_text" not in serialized
    assert "comment_text\":" not in serialized
