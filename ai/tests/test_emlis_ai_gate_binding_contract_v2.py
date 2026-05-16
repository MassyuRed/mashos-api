from __future__ import annotations

from emlis_ai_display_gate import GATE_BINDING_CONTRACT_VERSION, build_emlis_gate_trace, decide_emlis_observation_display
from emlis_ai_types import (
    GroundingReport,
    GroundingSentenceClaim,
    ListenerReaderReport,
    TemplateEchoReport,
)


def _reader() -> ListenerReaderReport:
    return ListenerReaderReport(
        understandable=True,
        addressee_clear=True,
        speaker_integrity_ok=True,
        conversational=True,
        report_like=False,
        confidence=1.0,
    )


def _template() -> TemplateEchoReport:
    return TemplateEchoReport(passed=True)


def test_gate_binding_contract_v2_keeps_pre_connection_binding_unused() -> None:
    trace = build_emlis_gate_trace(
        reader_report=_reader(),
        grounding_report=GroundingReport(passed=False, rejection_reasons=["composer_client_not_connected"]),
        template_echo_report=_template(),
        composer_source="unavailable",
        phase_completion_ready=False,
        binding_meta={},
    )

    for gate_name in ("reader", "grounding", "template_echo"):
        gate = trace[gate_name]
        assert gate["gate_binding_contract_version"] == GATE_BINDING_CONTRACT_VERSION
        assert gate["binding_present"] is False
        assert gate["binding_available"] is False
        assert gate["binding_required"] is False
        assert gate["binding_missing"] is False
        assert gate["binding_used"] is False
        assert gate["binding_support_source"] == "none"


def test_gate_binding_contract_v2_distinguishes_present_required_and_used() -> None:
    binding_meta = {
        "binding_present": True,
        "binding_required": True,
        "binding_count": 1,
        "expected_binding_count": 1,
        "sentence_count": 1,
        "binding_version": "test.binding.v2",
    }
    grounding = GroundingReport(
        passed=True,
        sentence_claims=[
            GroundingSentenceClaim(
                sentence_index=1,
                sentence="願いと怖さが同じところに残っています。",
                evidence_span_ids=["span_1"],
                relation_supported=True,
                binding_used=True,
                binding_sentence_id="s1",
                binding_evidence_span_ids=["span_1"],
                binding_phrase_unit_ids=["pu_1"],
                binding_relation_type="approach_avoidance",
                declared_evidence_span_ids=["span_1"],
                declared_phrase_unit_ids=["pu_1"],
                declared_relation_type="approach_avoidance",
            )
        ],
        coverage_ratio=1.0,
        confidence=1.0,
        binding_used=True,
        binding_present=True,
        binding_count=1,
        expected_binding_count=1,
        binding_version="test.binding.v2",
        binding_supported_sentence_count=1,
        declared_relation_types=["approach_avoidance"],
        declared_phrase_unit_ids=["pu_1"],
    )

    decision = decide_emlis_observation_display(
        comment_text="願いと怖さが同じところに残っています。",
        reader_report=_reader(),
        grounding_report=grounding,
        template_echo_report=_template(),
        composer_source="ai_generated",
        phase_completion_ready=True,
        binding_meta=binding_meta,
    )

    assert decision.observation_status == "passed"
    reader = decision.gate_trace["reader"]
    grounding_gate = decision.gate_trace["grounding"]
    template = decision.gate_trace["template_echo"]
    display = decision.gate_trace["display_gate"]

    assert reader["binding_present"] is True
    assert reader["binding_required"] is False
    assert reader["binding_used"] is False
    assert template["binding_present"] is True
    assert template["binding_required"] is False
    assert template["binding_used"] is False

    assert grounding_gate["binding_present"] is True
    assert grounding_gate["binding_required"] is True
    assert grounding_gate["binding_missing"] is False
    assert grounding_gate["binding_used"] is True
    assert grounding_gate["binding_support_source"] == "declared_relation_binding"

    assert display["binding_present"] is True
    assert display["binding_required"] is True
    assert display["binding_missing"] is False
    assert display["binding_used"] is True
    assert display["binding_support_source"] == "display_binding_aware_result"
