# -*- coding: utf-8 -*-
from __future__ import annotations

from emlis_ai_display_gate import decide_emlis_observation_display, phase8_display_gate_contract_ready
from emlis_ai_observation_display_repair_integration import integrate_observation_display_repair
from emlis_ai_types import DisplayDecision, GroundingReport, ListenerReaderReport, SafetyBoundaryReport, TemplateEchoReport
from emlis_ai_visible_surface_acceptance_gate import (
    ACTION_ALLOW,
    ACTION_RERENDER_SURFACE,
    CLASSIFICATION_PASS,
    CLASSIFICATION_REPAIR_REQUIRED,
    assert_visible_surface_acceptance_gate_meta_only,
    build_visible_surface_acceptance_gate_report,
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


def test_step4_display_gate_blocks_visible_surface_acceptance_failure_before_public_comment() -> None:
    comment_text = "Emlisです。\n今は、不安の重さが先に出ているように見えます。"
    visible_report = build_visible_surface_acceptance_gate_report(
        comment_text=comment_text,
        selected_emotions=(("悲しみ", "medium"), ("不安", "medium")),
    )

    decision = decide_emlis_observation_display(
        comment_text=comment_text,
        reader_report=_PASSING_READER,
        grounding_report=_PASSING_GROUNDING,
        template_echo_report=_PASSING_TEMPLATE,
        composer_source="ai_generated",
        phase_completion_ready=True,
        visible_surface_acceptance_gate_report=visible_report,
    )

    assert visible_report["passed"] is False
    assert visible_report["classification"] == CLASSIFICATION_REPAIR_REQUIRED
    assert visible_report["action"] == ACTION_RERENDER_SURFACE
    assert decision.observation_status == "rejected"
    assert decision.comment_text == ""
    assert "visible_surface_acceptance_gate_failed" in decision.rejection_reasons
    assert "emotion_focus_unbridged_secondary" in decision.rejection_reasons
    assert "visible_surface_acceptance_gate_action_rerender_surface" in decision.rejection_reasons
    assert phase8_display_gate_contract_ready(decision)

    gate = decision.gate_trace["visible_surface_acceptance_gate"]
    display_gate = decision.gate_trace["display_gate"]
    assert gate["passed"] is False
    assert gate["comment_text_body_included"] is False
    assert gate["raw_input_included"] is False
    assert gate["display_gate_relaxed"] is False
    assert display_gate["visible_surface_acceptance_gate_evaluated"] is True
    assert display_gate["visible_surface_acceptance_gate_blocked"] is True
    assert display_gate["comment_text_allowed"] is False


def test_step4_display_gate_allows_visible_surface_acceptance_pass() -> None:
    comment_text = "Emlisです。\n今は、悲しみを中心に、不安も近くにあるように見えます。"
    visible_report = build_visible_surface_acceptance_gate_report(
        comment_text=comment_text,
        selected_emotions=(("悲しみ", "medium"), ("不安", "medium")),
    )

    decision = decide_emlis_observation_display(
        comment_text=comment_text,
        reader_report=_PASSING_READER,
        grounding_report=_PASSING_GROUNDING,
        template_echo_report=_PASSING_TEMPLATE,
        composer_source="ai_generated",
        phase_completion_ready=True,
        visible_surface_acceptance_gate_report=visible_report,
    )

    assert visible_report["passed"] is True
    assert visible_report["classification"] == CLASSIFICATION_PASS
    assert visible_report["action"] == ACTION_ALLOW
    assert decision.observation_status == "passed"
    assert decision.comment_text == comment_text
    assert decision.rejection_reasons == []
    assert decision.gate_trace["visible_surface_acceptance_gate"]["passed"] is True
    assert decision.gate_trace["display_gate"]["visible_surface_acceptance_gate_passed"] is True
    assert phase8_display_gate_contract_ready(decision)


def test_step4_reply_service_visible_surface_report_builder_is_meta_only() -> None:
    from emlis_ai_reply_service import _build_visible_surface_acceptance_report_for_candidate

    report = _build_visible_surface_acceptance_report_for_candidate(
        comment_text="Emlisです。\n今は、不安の重さが先に出ているように見えます。",
        current_input={
            "emotion_details": [
                {"type": "悲しみ", "strength": "medium"},
                {"type": "不安", "strength": "medium"},
            ],
            "memo": "今日は短くしか残せない。",
        },
    )

    assert report["passed"] is False
    assert "emotion_focus_unbridged_secondary" in report["rejection_reasons"]
    assert report["comment_text_body_included"] is False
    assert report["raw_input_included"] is False
    assert report["display_gate_relaxed"] is False
    assert_visible_surface_acceptance_gate_meta_only(report)


def test_step4_low_information_repair_path_carries_visible_surface_gate_trace() -> None:
    original = DisplayDecision(
        observation_status="rejected",
        comment_text="",
        rejection_reasons=["too_short_for_observation"],
        trace_id="step4-visible-low-info",
    )
    result = integrate_observation_display_repair(
        current_input={"memo": "疲れた", "memo_action": ""},
        subscription_tier="free",
        safety_report=SafetyBoundaryReport(),
        trace_id="step4-visible-low-info",
        original_display_decision=original,
        original_reader_report=ListenerReaderReport(
            understandable=False,
            addressee_clear=False,
            speaker_integrity_ok=True,
            conversational=False,
            report_like=False,
            rejection_reasons=["too_short_for_observation"],
        ),
        original_grounding_report=GroundingReport(passed=False, rejection_reasons=["graph_evidence_not_used"]),
        original_template_echo_report=TemplateEchoReport(passed=True),
        original_composer_source="unavailable",
        original_composer_candidate=None,
    )

    assert result.applied is True
    assert result.display_decision.observation_status == "passed"
    assert "visible_surface_acceptance_gate" in result.display_decision.gate_trace
    gate = result.display_decision.gate_trace["visible_surface_acceptance_gate"]
    assert gate["evaluated"] is True
    assert gate["comment_text_body_included"] is False
    assert gate["raw_input_included"] is False
    assert result.display_decision.gate_trace["display_gate"]["visible_surface_acceptance_gate_evaluated"] is True
