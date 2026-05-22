from __future__ import annotations

from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
from emlis_ai_display_gate import decide_emlis_observation_display, phase8_display_gate_contract_ready
from emlis_ai_observation_reply_contract import (
    OBSERVATION_PUBLIC_STATUS_FOR_DISPLAY,
    OBSERVATION_REPLY_KIND_LOW_INFORMATION,
    build_observation_reply_meta,
)
from emlis_ai_types import GroundingReport, ListenerReaderReport, SafetyBoundaryReport, TemplateEchoReport


PASSING_TEXT = (
    "Mashさん、Emlisです。\n"
    "今の入力では、変えたい気持ちと動けない状態が同時に残っているように見えます。"
)


def _reader(*, passed: bool = True) -> ListenerReaderReport:
    return ListenerReaderReport(
        understandable=passed,
        addressee_clear=True,
        speaker_integrity_ok=True,
        conversational=True,
        report_like=False,
        rejection_reasons=[] if passed else ["reader_cannot_understand"],
        confidence=0.92 if passed else 0.2,
    )


def _grounding(*, passed: bool = True) -> GroundingReport:
    return GroundingReport(
        passed=passed,
        rejection_reasons=[] if passed else ["unsupported_relation"],
        coverage_ratio=1.0 if passed else 0.0,
        confidence=0.92 if passed else 0.1,
    )


def _template(*, passed: bool = True) -> TemplateEchoReport:
    return TemplateEchoReport(
        passed=passed,
        rejection_reasons=[] if passed else ["template_or_echo_detected"],
    )


def test_step0_display_gate_keeps_passed_status_and_body_as_the_only_visible_contract() -> None:
    decision = decide_emlis_observation_display(
        comment_text=PASSING_TEXT,
        reader_report=_reader(),
        grounding_report=_grounding(),
        template_echo_report=_template(),
        safety_report=SafetyBoundaryReport(),
        trace_id="obs-step0-display-passed",
        composer_source="ai_generated",
        phase_completion_ready=True,
    )

    assert decision.observation_status == OBSERVATION_PUBLIC_STATUS_FOR_DISPLAY
    assert decision.comment_text == PASSING_TEXT
    assert decision.rejection_reasons == []
    assert decision.gate_trace["display_gate"]["passed"] is True
    assert decision.gate_trace["display_gate"]["comment_text_allowed"] is True
    assert phase8_display_gate_contract_ready(decision) is True


def test_step0_display_gate_suppresses_body_for_every_non_passed_public_status() -> None:
    cases = [
        decide_emlis_observation_display(
            comment_text=PASSING_TEXT,
            reader_report=_reader(passed=False),
            grounding_report=_grounding(),
            template_echo_report=_template(),
            trace_id="obs-step0-reader-rejected",
            composer_source="ai_generated",
            phase_completion_ready=True,
        ),
        decide_emlis_observation_display(
            comment_text=PASSING_TEXT,
            reader_report=_reader(),
            grounding_report=_grounding(passed=False),
            template_echo_report=_template(),
            trace_id="obs-step0-grounding-rejected",
            composer_source="ai_generated",
            phase_completion_ready=True,
        ),
        decide_emlis_observation_display(
            comment_text=PASSING_TEXT,
            reader_report=_reader(),
            grounding_report=_grounding(),
            template_echo_report=_template(passed=False),
            trace_id="obs-step0-template-rejected",
            composer_source="ai_generated",
            phase_completion_ready=True,
        ),
        decide_emlis_observation_display(
            comment_text="",
            reader_report=_reader(),
            grounding_report=_grounding(),
            template_echo_report=_template(),
            trace_id="obs-step0-unavailable",
            composer_source="unavailable",
            phase_completion_ready=False,
        ),
        decide_emlis_observation_display(
            comment_text=PASSING_TEXT,
            reader_report=_reader(),
            grounding_report=_grounding(),
            template_echo_report=_template(),
            safety_report=SafetyBoundaryReport(requires_block=True, reasons=["safety_boundary"]),
            trace_id="obs-step0-safety",
            composer_source="ai_generated",
            phase_completion_ready=True,
        ),
    ]

    statuses = [decision.observation_status for decision in cases]
    assert statuses == ["rejected", "rejected", "rejected", "unavailable", "safety_blocked"]
    for decision in cases:
        assert decision.comment_text == ""
        assert decision.rejection_reasons
        assert decision.gate_trace["display_gate"]["comment_text_allowed"] is False
        assert phase8_display_gate_contract_ready(decision) is True


def test_step0_free_capability_keeps_user_dictionary_disabled_for_observation_reply() -> None:
    free = resolve_emlis_ai_capability_for_tier("free")
    plus = resolve_emlis_ai_capability_for_tier("plus")
    premium = resolve_emlis_ai_capability_for_tier("premium")

    assert free.history_mode == "none"
    assert free.model_read_enabled is False
    assert free.model_write_enabled is False
    assert free.include_derived_user_model is False
    assert free.source_scope == "current_input_only"

    assert plus.model_read_enabled is True
    assert plus.include_derived_user_model is True
    assert premium.model_read_enabled is True
    assert premium.include_derived_user_model is True


def test_step0_low_information_reply_kind_does_not_require_new_public_status() -> None:
    meta = build_observation_reply_meta(
        observation_reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        plan="free",
    )

    assert meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    assert meta["public_observation_status"] == "passed"
    assert meta["observation_status_enum_extended"] is False
    assert meta["rn_visible_contract_changed"] is False
