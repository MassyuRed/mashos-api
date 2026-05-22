from __future__ import annotations

from emlis_ai_observation_display_repair_integration import (
    attach_observation_display_repair_meta,
    integrate_observation_display_repair,
)
from emlis_ai_observation_reply_contract import OBSERVATION_REPLY_KIND_LOW_INFORMATION
from emlis_ai_types import DisplayDecision, GroundingReport, ListenerReaderReport, SafetyBoundaryReport, TemplateEchoReport


def _rejected_display(*reasons: str) -> DisplayDecision:
    return DisplayDecision(
        observation_status="rejected",
        comment_text="",
        rejection_reasons=list(reasons),
        trace_id="step11-rn-contract",
    )


def _reader(*reasons: str) -> ListenerReaderReport:
    return ListenerReaderReport(
        understandable=False,
        addressee_clear=False,
        speaker_integrity_ok=True,
        conversational=False,
        report_like=False,
        rejection_reasons=list(reasons),
    )


def _grounding(*reasons: str) -> GroundingReport:
    return GroundingReport(passed=False, rejection_reasons=list(reasons))


def test_step11_backend_exposes_low_information_reply_kind_as_optional_meta_only() -> None:
    result = integrate_observation_display_repair(
        current_input={"memo": "疲れた", "memo_action": ""},
        subscription_tier="free",
        safety_report=SafetyBoundaryReport(),
        trace_id="step11-rn-contract",
        original_display_decision=_rejected_display("too_short_for_observation"),
        original_reader_report=_reader("too_short_for_observation"),
        original_grounding_report=_grounding("graph_evidence_not_used"),
        original_template_echo_report=TemplateEchoReport(passed=True),
        original_composer_source="unavailable",
        original_composer_candidate=None,
    )

    assert result.applied is True
    assert result.display_decision.observation_status == "passed"
    assert result.display_decision.comment_text.strip()

    response_meta = attach_observation_display_repair_meta(
        {
            "observation_status": result.display_decision.observation_status,
            "diagnostic_summary": {},
            "multi_perspective": {"phase_gate": {}},
        },
        result,
    )
    input_feedback_payload = {
        "comment_text": result.display_decision.comment_text,
        "emlis_ai": response_meta,
    }

    assert input_feedback_payload["comment_text"].strip()
    assert input_feedback_payload["emlis_ai"]["observation_status"] == "passed"

    optional_reply_meta = input_feedback_payload["emlis_ai"]["observation_reply_meta"]
    assert optional_reply_meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    assert optional_reply_meta["eligible_for_full_observation"] is False
    assert optional_reply_meta["question_required"] is True
    assert optional_reply_meta["user_fact_may_promote_to_eligible"] is False

    step10_meta = input_feedback_payload["emlis_ai"]["step10_observation_display_repair_integration"]
    assert step10_meta["final_observation_status"] == "passed"
    assert step10_meta["public_status_extended"] is False
    assert step10_meta["observation_status_enum_extended"] is False
    assert step10_meta["rn_visible_contract_changed"] is False
    assert step10_meta["rn_visible_title_changed"] is False
    assert step10_meta["response_shape_changed"] is False
    assert step10_meta["display_gate_relaxed"] is False
    assert step10_meta["fixed_fallback_used"] is False
    assert step10_meta["external_ai_used"] is False
