from __future__ import annotations

"""Phase20-5 Gate Recovery Loop contract tests.

Gate failures must first be classified into bounded recovery policies instead
of being treated as a valid empty public observation.  The loop records repair
intent/attempts and, when the material bundle is observable, may attempt one
bounded current-input recovery through the existing gates. Display, Safety,
Grounding, Template and RN public boundaries must stay unchanged.
"""

from types import SimpleNamespace

from emlis_ai_gate_recovery_loop import (
    GATE_RECOVERY_LOOP_META_KEY,
    POLICY_EXIT_INFRA,
    POLICY_EXIT_SAFETY_EMERGENCY,
    POLICY_NARROW_GROUNDING_SCOPE,
    POLICY_REROUTE_LOW_INFORMATION,
    POLICY_REROUTE_SELF_DENIAL_SAFE_STATE_ANSWER,
    POLICY_SHORTEN_SURFACE,
    POLICY_SOFTEN_ASSERTION,
    assert_gate_recovery_loop_meta,
    attach_gate_recovery_loop_meta,
    build_gate_recovery_loop_decision,
    recover_emlis_gate_failure,
)
from emlis_ai_response_contract import (
    build_emlis_internal_response_contract_from_legacy_state,
    validate_emlis_internal_response_contract,
)
from emlis_ai_types import DisplayDecision, GroundingReport, ListenerReaderReport, SafetyBoundaryReport, TemplateEchoReport


def _failed_display(*reasons: str, status: str = "rejected", gate_trace: dict | None = None) -> DisplayDecision:
    return DisplayDecision(
        observation_status=status,
        comment_text="",
        rejection_reasons=list(reasons),
        trace_id="phase20-5-gate-recovery",
        gate_trace=gate_trace or {},
    )


def _passed_display() -> DisplayDecision:
    return DisplayDecision(
        observation_status="passed",
        comment_text="表示される本文",
        rejection_reasons=[],
        trace_id="phase20-5-gate-recovery",
        gate_trace={},
    )


def _policies(meta: dict) -> list[str]:
    return [event["recovery_policy"] for event in meta["events"]]


def test_phase20_5_surface_and_overclaim_failures_become_repair_plan_not_empty_exit() -> None:
    decision = build_gate_recovery_loop_decision(
        original_display_decision=_failed_display(
            "surface_relation_skeleton_major",
            "candidate_overclaim",
            gate_trace={
                "visible_surface_acceptance_gate": {
                    "passed": False,
                    "action": "rerender_surface",
                    "classification": "repair_required",
                    "rejection_reasons": ["surface_relation_skeleton_major"],
                }
            },
        ),
        final_display_decision=_failed_display("surface_relation_skeleton_major", "candidate_overclaim"),
    )
    meta = decision.as_meta()

    assert_gate_recovery_loop_meta(meta)
    assert POLICY_SHORTEN_SURFACE in _policies(meta)
    assert POLICY_SOFTEN_ASSERTION in _policies(meta)
    assert meta["first_reaction_empty_comment_text"] is False
    assert meta["non_terminal_recovery_available"] is True
    assert meta["final_empty_comment_text_allowed"] is False
    assert meta["display_gate_relaxed"] is False
    assert meta["fixed_fallback_used"] is False
    assert meta["public_response_key_change"] is False

    first_attempt = meta["internal_response_repair_attempts"][0]
    assert first_attempt["repair_kind"] == "surface_shorten"
    assert first_attempt["from_gate"] in {"visible_surface_acceptance_gate", "runtime_surface_gate"}
    assert first_attempt["result"] in {"not_run", "failed"}


def test_phase20_5_grounding_failure_narrows_scope_without_gate_relaxation() -> None:
    decision = build_gate_recovery_loop_decision(
        original_display_decision=_failed_display(
            "graph_evidence_not_used",
            "unsupported_sentence",
            gate_trace={
                "grounding": {
                    "passed": False,
                    "rejection_reasons": ["graph_evidence_not_used", "unsupported_sentence"],
                }
            },
        ),
        final_display_decision=_failed_display("graph_evidence_not_used"),
    )
    meta = decision.as_meta()

    assert POLICY_NARROW_GROUNDING_SCOPE in _policies(meta)
    assert meta["final_empty_comment_text_allowed"] is False
    assert all(event["final_exit_allowed"] is False for event in meta["events"])
    assert meta["grounding_gate_relaxed"] is False


def test_phase20_5_low_information_repair_records_passed_attempt() -> None:
    repair_result = SimpleNamespace(applied=True)
    decision = build_gate_recovery_loop_decision(
        original_display_decision=_failed_display("too_short_for_observation", "missing_information"),
        final_display_decision=_passed_display(),
        material_quality="low_information",
        observation_display_repair_result=repair_result,
    )
    meta = decision.as_meta()

    assert POLICY_REROUTE_LOW_INFORMATION in _policies(meta)
    assert (meta["repair_attempts"] and meta["repair_attempts"][-1]["result"] == "passed") is True
    assert meta["events"][-1]["repair_result"] == "passed"
    low_info_attempts = [
        attempt for attempt in meta["internal_response_repair_attempts"]
        if attempt["repair_kind"] == "low_information_reroute"
    ]
    assert low_info_attempts
    assert low_info_attempts[0]["result"] == "passed"

    contract = build_emlis_internal_response_contract_from_legacy_state(
        observation_status="passed",
        observation_reply_kind="low_information_observation",
        reason="phase20_5_low_information_recovery_contract",
        repair_attempts=decision.repair_attempts_for_internal_contract(),
    )
    assert validate_emlis_internal_response_contract(contract) == []
    assert contract["repair_attempts"] == meta["internal_response_repair_attempts"]


def test_phase20_5_self_denial_uses_safe_state_reroute_not_emergency_exit() -> None:
    decision = build_gate_recovery_loop_decision(
        original_display_decision=_failed_display("self_denial_safe_state_answer"),
        final_display_decision=_passed_display(),
        safety_triage_kind="self_denial_safe_state_answer",
    )
    meta = decision.as_meta()

    assert POLICY_REROUTE_SELF_DENIAL_SAFE_STATE_ANSWER in _policies(meta)
    assert POLICY_EXIT_SAFETY_EMERGENCY not in _policies(meta)
    assert meta["final_empty_comment_text_allowed"] is False
    assert meta["internal_response_repair_attempts"][0]["repair_kind"] == "self_denial_safe_reroute"
    assert meta["internal_response_repair_attempts"][0]["result"] == "passed"


def test_phase20_5_only_emergency_and_infra_may_end_with_absent_comment_text() -> None:
    emergency = build_gate_recovery_loop_decision(
        original_display_decision=_failed_display("self_harm_imminent", status="safety_blocked"),
        final_display_decision=_failed_display("self_harm_imminent", status="safety_blocked"),
        safety_report=SafetyBoundaryReport(requires_block=True, reasons=["self_harm_imminent"]),
        safety_triage_kind="safety_blocked_emergency",
    ).as_meta()
    infra = build_gate_recovery_loop_decision(
        original_display_decision=_failed_display(
            "composer_source_unavailable",
            "empty_comment_text_without_candidate",
            status="unavailable",
        ),
        final_display_decision=_failed_display("composer_source_unavailable", status="unavailable"),
    ).as_meta()

    assert _policies(emergency) == [POLICY_EXIT_SAFETY_EMERGENCY]
    assert emergency["final_empty_comment_text_allowed"] is True
    assert emergency["comment_text_absent_allowed_only_for_emergency_or_infra"] is True
    assert _policies(infra) == [POLICY_EXIT_INFRA]
    assert infra["final_empty_comment_text_allowed"] is True



class _MaterialRoute:
    material_quality = "eligible"
    visible_material_slots = ("event", "action", "emotion_direction", "target", "change", "value")
    unknown_slots = ("cause",)
    generic_relation_material_ids = ("self_understanding_learning", "value_or_self_understanding_material")

    def as_meta(self) -> dict:
        return {
            "material_quality": self.material_quality,
            "visible_material_slots": list(self.visible_material_slots),
            "unknown_slots": list(self.unknown_slots),
            "generic_relation_material_ids": list(self.generic_relation_material_ids),
            "safety_triage_kind": "safe_observation",
        }


def test_phase20_5_recover_emlis_gate_failure_blocks_diagnostic_surface_before_public_display() -> None:
    current_input = {
        "memo": "長い入力本文は公開本文へそのまま写さない",
        "memo_action": "具体的な行動本文もそのまま写さない",
        "emotions": ["自己理解"],
        "category": ["学習"],
    }
    result = recover_emlis_gate_failure(
        current_input=current_input,
        display_decision=_failed_display("phase8_repeated_sentence_tail", "repeated_surface"),
        reader_report=ListenerReaderReport(
            understandable=False,
            addressee_clear=False,
            speaker_integrity_ok=True,
            conversational=False,
            report_like=True,
            rejection_reasons=["original_gate_failed"],
        ),
        grounding_report=GroundingReport(passed=False, rejection_reasons=["graph_evidence_not_used"]),
        template_echo_report=TemplateEchoReport(passed=False, rejection_reasons=["phase8_repeated_sentence_tail"]),
        material_route=_MaterialRoute(),
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=False),
        trace_id="phase20-5-recovery-actual",
    )

    assert result.applied is False
    assert result.display_decision.observation_status != "passed"
    assert result.composer_candidate is None
    assert result.runtime_surface_pre_return_gate_report == {}
    assert result.visible_surface_acceptance_gate_report == {}
    assert "gate_recovery_material_surface_public_leak" in result.blocked_reasons
    assert "gate_recovery_diagnostic_surface_promoted_to_public" in result.blocked_reasons
    assert result.surface_binding_meta["public_surface_role"] == "diagnostic_recovery_surface"
    assert result.surface_binding_meta["public_display_allowed"] is False
    assert result.surface_binding_meta["public_boundary_blocked"] is True
    boundary = result.surface_binding_meta["gate_recovery_public_boundary_decision"]
    assert boundary["public_display_allowed"] is False
    assert boundary["contract_flags"]["comment_text_body_included"] is False
    assert "見えたこと：" not in result.display_decision.comment_text
    assert "Emlisから：" not in result.display_decision.comment_text
    assert "長い入力本文は公開本文へそのまま写さない" not in result.display_decision.comment_text
    assert "具体的な行動本文もそのまま写さない" not in result.display_decision.comment_text

def test_phase20_5_attach_meta_keeps_internal_boundaries_and_phase_gate_flags() -> None:
    decision = build_gate_recovery_loop_decision(
        original_display_decision=_failed_display("too_short_for_observation"),
        final_display_decision=_passed_display(),
        material_quality="low_information",
        observation_display_repair_result=SimpleNamespace(applied=True),
    )
    meta = attach_gate_recovery_loop_meta(
        {
            "phase_gate": {},
            "diagnostic_summary": {},
        },
        decision,
    )

    assert GATE_RECOVERY_LOOP_META_KEY in meta
    assert GATE_RECOVERY_LOOP_META_KEY in meta["diagnostic_summary"]
    assert meta["phase_gate"]["phase20_5_gate_recovery_loop_ready"] is True
    assert meta["phase_gate"]["phase20_5_first_reaction_empty_comment_text"] is False
    assert meta["phase_gate"]["phase20_5_comment_text_absent_allowed_only_for_emergency_or_infra"] is True
    assert meta["phase_gate"]["phase20_5_gate_threshold_relaxed"] is False
    assert meta["phase_gate"]["phase20_5_fixed_fallback_used"] is False
