# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from types import SimpleNamespace

from emlis_ai_complete_reply_diagnostics_service import (
    build_complete_reply_service_diagnostics,
    build_runtime_surface_step8_diagnostics_meta,
    attach_complete_reply_service_diagnostics,
)
from emlis_ai_runtime_surface_pre_return_gate import build_runtime_surface_pre_return_gate_report
from emlis_ai_types import DisplayDecision

_BAD_SURFACE = (
    "Emlisです。\n"
    "今までことが中心にあります。\n"
    "その中でも、大丈夫ことも見えています。\n"
    "その中でも、創作をする時にリアルさを求めることも重なっています。"
)


def _runtime_meta() -> dict:
    return {
        "version": "emlis.complete_runtime_meta.v1",
        "composer_model": "complete_composer_initial",
        "generation_method": "ai_generated",
        "coverage_scope": "current_input_core",
        "profile_key": "current_input_core",
        "shallow_observation_path": True,
        "step4_shallow_phrase_unit_guard": {
            "version": "emlis.shallow_phrase_unit_guard.v1",
            "malformed_phrase_unit_blocked_count": 2,
            "malformed_nominalization_blocked_count": 2,
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        "step5_shallow_surface_realizer_v2": {
            "version": "emlis.shallow_surface_realizer_plan.v2",
            "eligible": True,
            "realizer_version": "shallow_surface_realizer.v2",
            "generic_center_phrase_count": 0,
            "same_connector_run_max": 1,
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        "shallow_realizer_version": "shallow_surface_realizer.v2",
        "shallow_v2_used": True,
        "low_information_specificity_plan": {
            "version": "emlis.low_information_specificity_plan.v1",
            "eligible": True,
            "safe_anchor_count": 1,
            "uses_safe_anchor": True,
            "safe_anchor_role": "question",
            "safe_anchor_surface_kind": "safety_confirmation",
            "safe_anchor_evidence_ids": ["ev-safe-1"],
            "unsupported_event_assertion_present": False,
            "user_fact_promotion_attempt": False,
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        "low_information_specificity_used": True,
        "step6_low_information_specificity_ready": True,
        "safe_anchor_count": 1,
        "uses_safe_anchor": True,
        "safe_anchor_role": "question",
        "safe_anchor_surface_kind": "safety_confirmation",
        "safe_anchor_evidence_ids": ["ev-safe-1"],
        "raw_input_included": False,
        "comment_text_body_included": False,
    }


def _candidate() -> SimpleNamespace:
    return SimpleNamespace(
        status="generated",
        composer_source="ai_generated",
        composer_model="complete_composer_initial",
        generation_method="ai_generated",
        coverage_scope="current_input_core",
        composer_meta=_runtime_meta(),
        used_evidence_span_ids=["ev-safe-1"],
        used_relation_ids=[],
    )


def _gate_report() -> dict:
    return build_runtime_surface_pre_return_gate_report(
        comment_text=_BAD_SURFACE,
        composer_meta={
            "profile_key": "current_input_core",
            "coverage_scope": "current_input_core",
            "shallow_observation_path": True,
        },
        rerender_allowed=True,
    )


def test_step8_runtime_surface_meta_is_scorecard_ready_and_meta_only() -> None:
    gate_report = _gate_report()
    meta = build_runtime_surface_step8_diagnostics_meta(
        runtime_meta=_runtime_meta(),
        gate_trace={"runtime_surface_pre_return_gate": gate_report},
        diagnostic_summary={"trace_id": "t-step8"},
    )

    assert meta["version"] == "emlis.runtime_surface_diagnostics_scorecard.v1"
    assert meta["step8_runtime_surface_diagnostics_ready"] is True
    assert meta["runtime_surface_diagnostics_scorecard_updated"] is True
    assert meta["runtime_surface_pre_return_gate_evaluated"] is True
    assert meta["runtime_surface_pre_return_gate_passed"] is False
    assert meta["runtime_surface_pre_return_gate_action"] == "rerender_shallow_v2"
    assert meta["surface_template_major_blocked"] is True
    assert meta["malformed_phrase_unit_blocked_count"] >= 2
    assert meta["shallow_realizer_version"] == "shallow_surface_realizer.v2"
    assert meta["shallow_v2_used"] is True
    assert meta["low_information_specificity_used"] is True
    assert meta["step6_low_information_specificity_ready"] is True
    assert meta["uses_safe_anchor"] is True
    assert meta["safe_anchor_role"] == "question"

    dumped = json.dumps(meta, ensure_ascii=False, sort_keys=True)
    assert _BAD_SURFACE not in dumped
    assert "今までこと" not in dumped
    assert '"comment_text"' not in dumped
    assert '"raw_input"' not in dumped
    assert meta["raw_input_included"] is False
    assert meta["comment_text_body_included"] is False
    assert meta["display_gate_relaxed"] is False


def test_step8_complete_reply_diagnostics_and_attach_propagate_meta_only_scorecard() -> None:
    gate_report = _gate_report()
    display_decision = DisplayDecision(
        observation_status="rejected",
        comment_text="",
        rejection_reasons=["runtime_surface_pre_return_gate_failed"],
        trace_id="t-step8",
        gate_trace={"runtime_surface_pre_return_gate": gate_report},
    )
    diagnostics = build_complete_reply_service_diagnostics(
        composer_candidate=_candidate(),
        display_decision=display_decision,
        gate_trace={"runtime_surface_pre_return_gate": gate_report},
        diagnostic_summary={"trace_id": "t-step8"},
    )

    step8 = diagnostics["runtime_surface_step8_diagnostics"]
    scorecard_step8 = diagnostics["scorecard_event"]["runtime_surface_diagnostics_scorecard"]
    assert step8["runtime_surface_pre_return_gate_evaluated"] is True
    assert step8["runtime_surface_pre_return_gate_passed"] is False
    assert scorecard_step8["runtime_surface_pre_return_gate_action"] == "rerender_shallow_v2"
    assert diagnostics["surface_template_major_blocked"] is True
    assert diagnostics["malformed_phrase_unit_blocked_count"] >= 2
    assert diagnostics["shallow_v2_used"] is True
    assert diagnostics["low_information_specificity_used"] is True

    diagnostic_summary: dict = {}
    phase_gate: dict = {}
    attach_complete_reply_service_diagnostics(
        diagnostic_summary=diagnostic_summary,
        phase_gate=phase_gate,
        diagnostics=diagnostics,
    )
    assert diagnostic_summary["runtime_surface_pre_return_gate_evaluated"] is True
    assert diagnostic_summary["runtime_surface_pre_return_gate_passed"] is False
    assert phase_gate["runtime_surface_step8_diagnostics_ready"] is True
    assert phase_gate["surface_template_major_blocked"] is True
    assert phase_gate["shallow_v2_used"] is True
    assert phase_gate["low_information_specificity_used"] is True

    dumped = json.dumps({"diagnostics": diagnostics, "summary": diagnostic_summary, "phase": phase_gate}, ensure_ascii=False, sort_keys=True)
    assert _BAD_SURFACE not in dumped
    assert "今までこと" not in dumped
    assert '"comment_text":' not in dumped
    assert '"raw_input":' not in dumped
