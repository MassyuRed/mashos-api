# -*- coding: utf-8 -*-
from __future__ import annotations

from types import SimpleNamespace

from emlis_ai_display_gate import decide_emlis_observation_display, phase8_display_gate_contract_ready
from emlis_ai_runtime_surface_pre_return_gate import (
    ACTION_ALLOW,
    ACTION_RERENDER_SHALLOW_V2,
    build_runtime_surface_pre_return_gate_report,
)
from emlis_ai_types import GroundingReport, ListenerReaderReport, TemplateEchoReport
from fixtures.emlis_ai_runtime_surface_red_fixtures import RUNTIME_SURFACE_BASELINE_RED_FIXTURES


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

_CLEAN_SURFACE = (
    "Emlisです。\n"
    "今は、自分の特技を探そうとしている感じが出ています。\n"
    "好きで続けているものはあるのに、それを得意と呼べるかで止まっているように見えます。"
)


def test_step2_display_gate_blocks_surface_pre_return_failure_before_public_comment() -> None:
    fixture = RUNTIME_SURFACE_BASELINE_RED_FIXTURES[0]
    surface_report = build_runtime_surface_pre_return_gate_report(
        comment_text=fixture.public_body,
        composer_meta=fixture.composer_meta,
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

    assert surface_report["passed"] is False
    assert surface_report["action"] == ACTION_RERENDER_SHALLOW_V2
    assert decision.observation_status == "rejected"
    assert decision.comment_text == ""
    assert "runtime_surface_pre_return_gate_failed" in decision.rejection_reasons
    assert "surface_template_major" in decision.rejection_reasons
    assert "malformed_phrase_unit" in decision.rejection_reasons
    assert phase8_display_gate_contract_ready(decision)

    runtime_gate = decision.gate_trace["runtime_surface_pre_return_gate"]
    display_gate = decision.gate_trace["display_gate"]
    assert runtime_gate["passed"] is False
    assert runtime_gate["comment_text_body_included"] is False
    assert runtime_gate["raw_input_included"] is False
    assert runtime_gate["display_gate_relaxed"] is False
    assert display_gate["runtime_surface_pre_return_gate_evaluated"] is True
    assert display_gate["runtime_surface_pre_return_gate_passed"] is False
    assert display_gate["surface_template_major_blocked"] is True
    assert display_gate["malformed_phrase_unit_blocked_count"] >= 1
    assert display_gate["comment_text_allowed"] is False


def test_step2_display_gate_allows_clean_surface_when_surface_report_passes() -> None:
    surface_report = build_runtime_surface_pre_return_gate_report(
        comment_text=_CLEAN_SURFACE,
        composer_meta={"profile_key": "complete_initial", "composer_source": "ai_generated"},
    )

    decision = decide_emlis_observation_display(
        comment_text=_CLEAN_SURFACE,
        reader_report=_PASSING_READER,
        grounding_report=_PASSING_GROUNDING,
        template_echo_report=_PASSING_TEMPLATE,
        composer_source="ai_generated",
        phase_completion_ready=True,
        runtime_surface_pre_return_gate_report=surface_report,
    )

    assert surface_report["passed"] is True
    assert surface_report["action"] == ACTION_ALLOW
    assert decision.observation_status == "passed"
    assert decision.comment_text == _CLEAN_SURFACE
    assert decision.rejection_reasons == []
    assert decision.gate_trace["runtime_surface_pre_return_gate"]["passed"] is True
    assert decision.gate_trace["display_gate"]["runtime_surface_pre_return_gate_passed"] is True
    assert phase8_display_gate_contract_ready(decision)


def test_step2_reply_service_candidate_report_builder_sets_shallow_context_meta_only() -> None:
    from emlis_ai_reply_service import _build_runtime_surface_pre_return_report_for_candidate

    fixture = RUNTIME_SURFACE_BASELINE_RED_FIXTURES[1]
    candidate = SimpleNamespace(
        composer_source="ai_generated",
        composer_model="emlis.limited_composer.v1",
        generation_method="limited_current_input_core",
        generation_scope="current_input_core",
        coverage_scope="current_input_core",
        status="generated",
        composer_meta={"profile_key": "current_input_core"},
    )

    report = _build_runtime_surface_pre_return_report_for_candidate(
        comment_text=fixture.public_body,
        composer_candidate=candidate,
        composer_source="ai_generated",
    )

    assert report["passed"] is False
    assert report["shallow_observation_path"] is True
    assert report["action"] == ACTION_RERENDER_SHALLOW_V2
    assert report["raw_input_included"] is False
    assert report["comment_text_body_included"] is False
    assert "surface_template_major" in report["rejection_reasons"]
