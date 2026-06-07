# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 8 guards for complete-initial recomposition existing-gate passage.

A recomposition candidate may be generated after limited source-unavailable,
but it must only be adopted after the existing reader / grounding / template /
runtime surface / visible surface / display gates pass.  These tests keep that
boundary body-free and fail-closed without relaxing any gate.
"""

from types import SimpleNamespace

from emlis_ai_reply_service import _reply_service_recomposition_existing_gate_chain_summary


def _gate(passed: bool, *reasons: str) -> SimpleNamespace:
    return SimpleNamespace(passed=passed, rejection_reasons=list(reasons))


def test_p8_existing_gate_chain_marks_candidate_adopted_only_after_all_gates_pass() -> None:
    summary = _reply_service_recomposition_existing_gate_chain_summary(
        reader_report=_gate(True),
        grounding_report=_gate(True),
        template_echo_report=_gate(True),
        runtime_surface_pre_return_gate_report={"passed": True, "rejection_reasons": []},
        visible_surface_acceptance_gate_report={"passed": True, "rejection_reasons": []},
        display_decision=SimpleNamespace(observation_status="passed", rejection_reasons=[]),
        adopted=True,
    )

    assert summary["source_phase"] == "PublicObservationRecovery_P8_ReplyServiceExistingGateChain"
    assert summary["reader_gate_evaluated"] is True
    assert summary["reader_gate_passed"] is True
    assert summary["grounding_gate_evaluated"] is True
    assert summary["grounding_gate_passed"] is True
    assert summary["template_gate_evaluated"] is True
    assert summary["template_gate_passed"] is True
    assert summary["runtime_surface_pre_return_gate_evaluated"] is True
    assert summary["runtime_surface_pre_return_gate_passed"] is True
    assert summary["visible_surface_acceptance_gate_evaluated"] is True
    assert summary["visible_surface_acceptance_gate_passed"] is True
    assert summary["display_gate_evaluated"] is True
    assert summary["display_gate_passed"] is True
    assert summary["passed_by_all_existing_gates"] is True
    assert summary["candidate_adopted_after_existing_gates"] is True
    assert summary["fail_closed_when_gate_failed"] is False
    assert summary["display_gate_relaxed"] is False
    assert summary["grounding_gate_relaxed"] is False
    assert summary["template_gate_relaxed"] is False
    assert summary["reader_gate_relaxed"] is False
    assert summary["runtime_surface_gate_relaxed"] is False
    assert summary["visible_surface_gate_relaxed"] is False
    assert summary["raw_input_included"] is False
    assert summary["comment_text_body_included"] is False
    assert summary["candidate_body_in_meta"] is False


def test_p8_existing_gate_chain_fails_closed_when_any_existing_gate_fails_even_with_adoption_intent() -> None:
    summary = _reply_service_recomposition_existing_gate_chain_summary(
        reader_report=_gate(True),
        grounding_report=_gate(True),
        template_echo_report=_gate(True),
        runtime_surface_pre_return_gate_report={"passed": True, "rejection_reasons": []},
        visible_surface_acceptance_gate_report={
            "passed": False,
            "rejection_reasons": ["visible_surface_acceptance_gate_failed"],
        },
        display_decision=SimpleNamespace(
            observation_status="unavailable",
            rejection_reasons=["display_gate_failed"],
        ),
        adopted=True,
    )

    assert summary["visible_surface_acceptance_gate_evaluated"] is True
    assert summary["visible_surface_acceptance_gate_passed"] is False
    assert summary["display_gate_evaluated"] is True
    assert summary["display_gate_passed"] is False
    assert summary["passed_by_all_existing_gates"] is False
    assert summary["candidate_adopted_after_existing_gates"] is False
    assert summary["fail_closed_when_gate_failed"] is True
    assert "visible_surface_acceptance_gate_failed" in summary["blocked_reasons"]
    assert "display_gate_failed" in summary["blocked_reasons"]
    assert summary["display_gate_relaxed"] is False
    assert summary["grounding_gate_relaxed"] is False
    assert summary["raw_input_included"] is False
    assert summary["comment_text_body_included"] is False
    assert summary["candidate_body_in_meta"] is False
