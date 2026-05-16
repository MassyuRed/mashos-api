from __future__ import annotations

from emlis_ai_display_gate import build_emlis_gate_trace, decide_emlis_observation_display
from emlis_ai_types import (
    GroundingReport,
    GroundingSentenceClaim,
    ListenerReaderReport,
    TemplateEchoReport,
)


BINDING_META = {
    "binding_present": True,
    "binding_required": True,
    "binding_count": 1,
    "expected_binding_count": 1,
    "sentence_count": 1,
    "binding_version": "test.binding.v1",
}


def _reader() -> ListenerReaderReport:
    return ListenerReaderReport(
        understandable=True,
        addressee_clear=True,
        speaker_integrity_ok=True,
        conversational=True,
        report_like=False,
        confidence=1.0,
    )


def _grounding(*, binding_used: bool = True) -> GroundingReport:
    return GroundingReport(
        passed=True,
        sentence_claims=[
            GroundingSentenceClaim(
                sentence_index=1,
                sentence="負荷が続く中で、余力が細くなっています。",
                evidence_span_ids=["e1"],
                relation_supported=True,
                binding_used=binding_used,
                binding_sentence_id="s1",
                binding_evidence_span_ids=["e1"],
                binding_phrase_unit_ids=["pu1"],
                binding_relation_type="pressure",
            )
        ],
        coverage_ratio=1.0,
        confidence=1.0,
        binding_present=True,
        binding_used=binding_used,
        binding_count=1,
        expected_binding_count=1,
        binding_version="test.binding.v1",
        binding_supported_sentence_count=1 if binding_used else 0,
        binding_diagnostics={"version": "test.binding_aware_grounding.v1"},
    )


def _template() -> TemplateEchoReport:
    return TemplateEchoReport(passed=True)


def test_step7_gate_trace_records_binding_used_on_reader_grounding_template_and_display() -> None:
    decision = decide_emlis_observation_display(
        comment_text="Mashさん、Emlisです。\n負荷が続く中で、余力が細くなっています。",
        reader_report=_reader(),
        grounding_report=_grounding(binding_used=True),
        template_echo_report=_template(),
        composer_source="ai_generated",
        phase_completion_ready=True,
        binding_meta=BINDING_META,
    )

    assert decision.observation_status == "passed"
    for gate_name in ("reader", "grounding", "template_echo", "display_gate"):
        gate = decision.gate_trace[gate_name]
        assert "binding_used" in gate
        assert "binding_present" in gate
        assert "binding_available" in gate
        assert "binding_count" in gate
        assert gate["binding_present"] is True
        assert gate["binding_available"] is True
        step7 = gate["step7_gate_binding_reflection"]
        assert step7["target_step"] == "7_Gate_binding_reflection"
        assert step7["gate"] == ("display" if gate_name == "display_gate" else gate_name)
        assert step7["raw_text_included"] is False
        assert step7["display_contract_relaxed"] is False

    assert decision.gate_trace["reader"]["binding_used"] is False
    assert decision.gate_trace["grounding"]["binding_used"] is True
    assert decision.gate_trace["template_echo"]["binding_used"] is False
    assert decision.gate_trace["display_gate"]["binding_used"] is True


def test_step7_build_gate_trace_keeps_binding_meta_even_when_grounding_did_not_use_it() -> None:
    trace = build_emlis_gate_trace(
        reader_report=_reader(),
        grounding_report=_grounding(binding_used=False),
        template_echo_report=_template(),
        composer_source="ai_generated",
        phase_completion_ready=True,
        binding_meta=BINDING_META,
    )

    assert trace["reader"]["binding_present"] is True
    assert trace["reader"]["binding_used"] is False
    assert trace["grounding"]["binding_present"] is True
    assert trace["grounding"]["binding_used"] is False
    assert trace["template_echo"]["binding_present"] is True
    assert trace["template_echo"]["binding_used"] is False
    assert trace["grounding"]["step7_gate_binding_reflection"]["gate_threshold_relaxed"] is False
