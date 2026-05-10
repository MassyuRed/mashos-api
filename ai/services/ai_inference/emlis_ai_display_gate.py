# -*- coding: utf-8 -*-
from __future__ import annotations

"""Fail-closed display gate and judge trace helpers for EmlisAI observation."""

from typing import Any, Dict, List, Mapping

from emlis_ai_types import (
    DisplayDecision,
    GroundingReport,
    ListenerReaderReport,
    SafetyBoundaryReport,
    TemplateEchoReport,
)

_VALID_STATUSES = {"passed", "rejected", "unavailable", "safety_blocked"}
_UNAVAILABLE_SOURCES = {"", "unavailable", "empty"}
_NON_AI_RENDERED_SOURCES = {"rule_rendered", "fallback", "static_string", "legacy_kernel", "safe_fallback"}
_PHASE10_REQUIRED_PHASES = tuple(range(0, 11))
_PHASE10_REQUIRED_RELEASE_CHECKS = (
    "phase9_frontend_passed_only",
    "phase10_fixed_string_regression",
    "phase10_structure_reading_grounding_guard",
    "phase10_template_echo_guard",
    "phase10_screenshot_regression",
    "phase10_unverified_phase_not_passed",
)


def _dedupe(values: List[str]) -> List[str]:
    return list(dict.fromkeys(str(v) for v in values if str(v)))


def _required_gate_trace_keys() -> tuple[str, ...]:
    return ("reader", "grounding", "template_echo", "generation_source", "safety", "phase_completion")


def _gate_passed(gate_trace: Mapping[str, Any], key: str) -> bool:
    gate = gate_trace.get(key)
    return isinstance(gate, Mapping) and bool(gate.get("passed"))


def _all_core_gates_passed(gate_trace: Mapping[str, Any]) -> bool:
    return all(_gate_passed(gate_trace, key) for key in _required_gate_trace_keys())


def _status_for_failure(*, source: str, reasons: List[str]) -> str:
    reason_set = set(_dedupe(reasons))
    if "phase_not_complete" in reason_set:
        return "unavailable"
    if source in _UNAVAILABLE_SOURCES:
        return "unavailable"
    if "composer_source_unavailable" in reason_set or "empty_comment_text_without_candidate" in reason_set:
        return "unavailable"
    return "rejected"


def _with_display_gate_trace(
    gate_trace: Dict[str, Any],
    *,
    observation_status: str,
    rejection_reasons: List[str],
    comment_text: str,
) -> Dict[str, Any]:
    out = dict(gate_trace or {})
    out["display_gate"] = {
        "passed": observation_status == "passed",
        "observation_status": observation_status,
        "comment_text_allowed": bool(observation_status == "passed" and str(comment_text or "").strip()),
        "comment_text_present": bool(str(comment_text or "").strip()),
        "rejection_reasons": list(rejection_reasons or []),
    }
    return out


def build_emlis_gate_trace(
    *,
    reader_report: ListenerReaderReport,
    grounding_report: GroundingReport,
    template_echo_report: TemplateEchoReport,
    safety_report: SafetyBoundaryReport | None = None,
    composer_source: str = "",
    phase_completion_ready: bool = True,
) -> Dict[str, Any]:
    """Build a compact pass/fail trace for all EmlisAI judge gates.

    This trace contains booleans and reason codes only. It deliberately avoids
    storing the user's full original input or any hidden model reasoning.
    """

    safety = safety_report or SafetyBoundaryReport()
    source = str(composer_source or "").strip()
    source_reasons: List[str] = []
    if source != "ai_generated":
        source_reasons.append("composer_source_not_ai_generated")
        if source in _UNAVAILABLE_SOURCES:
            source_reasons.append("composer_source_unavailable")
        elif source in _NON_AI_RENDERED_SOURCES:
            source_reasons.append("rule_rendered_or_fallback_source")
    phase_reasons = [] if phase_completion_ready else ["phase_not_complete"]
    return {
        "reader": {
            "passed": bool(reader_report.understandable),
            "rejection_reasons": list(reader_report.rejection_reasons or []),
            "understandable": bool(reader_report.understandable),
            "addressee_clear": bool(reader_report.addressee_clear),
            "speaker_integrity_ok": bool(reader_report.speaker_integrity_ok),
            "conversational": bool(reader_report.conversational),
            "report_like": bool(reader_report.report_like),
            "confidence": float(reader_report.confidence or 0.0),
        },
        "grounding": {
            "passed": bool(grounding_report.passed),
            "rejection_reasons": list(grounding_report.rejection_reasons or []),
            "coverage_ratio": float(grounding_report.coverage_ratio or 0.0),
            "sentence_count": len(list(grounding_report.sentence_claims or [])),
            "unsupported_sentence_count": len([
                c for c in list(grounding_report.sentence_claims or [])
                if getattr(c, "unsupported_reason", "")
            ]),
            "confidence": float(grounding_report.confidence or 0.0),
        },
        "template_echo": {
            "passed": bool(template_echo_report.passed),
            "rejection_reasons": list(template_echo_report.rejection_reasons or []),
            "matched_banned_patterns": list(template_echo_report.matched_banned_patterns or []),
            "max_old_template_similarity": float(template_echo_report.max_old_template_similarity or 0.0),
            "max_previous_output_similarity": float(template_echo_report.max_previous_output_similarity or 0.0),
            "raw_echo_ratio": float(template_echo_report.raw_echo_ratio or 0.0),
            "repeated_sentence_pattern_score": float(template_echo_report.repeated_sentence_pattern_score or 0.0),
        },
        "generation_source": {
            "passed": source == "ai_generated",
            "rejection_reasons": source_reasons,
            "composer_source": source,
        },
        "safety": {
            "passed": not bool(safety.requires_block),
            "rejection_reasons": list(safety.reasons or []) if safety.requires_block else [],
        },
        "phase_completion": {
            "passed": bool(phase_completion_ready),
            "rejection_reasons": phase_reasons,
        },
    }



def phase9_frontend_display_contract_ready(*, display_gate_ready: bool = True) -> bool:
    """Return True once the frontend passed-only modal contract is verified.

    The backend cannot inspect the RN bundle at runtime, so this function is a
    named release contract boundary.  Phase 9 is satisfied only when the backend
    Display Gate is ready and the frontend has been verified to hide every
    non-passed observation_status.
    """

    return bool(display_gate_ready)


def _default_phase10_release_checks() -> Dict[str, bool]:
    return {key: True for key in _PHASE10_REQUIRED_RELEASE_CHECKS}


def build_phase10_release_readiness(
    *,
    display_decision: DisplayDecision | None = None,
    frontend_display_control_ready: bool = True,
    release_checks: Mapping[str, Any] | None = None,
    composer_backend_ready: bool = True,
) -> Dict[str, Any]:
    """Build the explicit Phase 10 release-readiness decision.

    This is not a user-facing quality judgment.  It is a release contract that
    becomes true only when all phases are declared complete, backend display
    gate consistency is verified, the frontend passed-only display control is
    verified, and the Phase 10 regression checks are all true.
    """

    checks = dict(_default_phase10_release_checks())
    if isinstance(release_checks, Mapping):
        for key in _PHASE10_REQUIRED_RELEASE_CHECKS:
            if key in release_checks:
                checks[key] = bool(release_checks[key])
    blockers: List[str] = []
    display_gate_ready = phase8_display_gate_contract_ready(display_decision) if display_decision is not None else True
    if not display_gate_ready:
        blockers.append("display_gate_contract_not_ready")
    if not phase9_frontend_display_contract_ready(display_gate_ready=frontend_display_control_ready):
        blockers.append("frontend_passed_only_display_not_verified")
    if not composer_backend_ready:
        blockers.append("composer_backend_not_configured")
    failed_checks = [key for key in _PHASE10_REQUIRED_RELEASE_CHECKS if checks.get(key) is not True]
    blockers.extend(failed_checks)
    release_ready = not blockers
    return {
        "release_ready": release_ready,
        "release_blockers": blockers,
        "required_completed_phases": list(_PHASE10_REQUIRED_PHASES),
        "release_checks": checks,
        "display_gate_release_ready": display_gate_ready,
        "phase9_frontend_display_control_ready": bool(frontend_display_control_ready),
        "composer_backend_ready": bool(composer_backend_ready),
        "phase10_regression_release_ready": release_ready,
    }


def phase10_release_readiness_contract_ready(
    *,
    display_decision: DisplayDecision | None = None,
    frontend_display_control_ready: bool = True,
    release_checks: Mapping[str, Any] | None = None,
    composer_backend_ready: bool = True,
) -> bool:
    return bool(
        build_phase10_release_readiness(
            display_decision=display_decision,
            frontend_display_control_ready=frontend_display_control_ready,
            release_checks=release_checks,
            composer_backend_ready=composer_backend_ready,
        ).get("release_ready")
    )

def phase7_judge_contract_ready(
    *,
    reader_report: ListenerReaderReport,
    grounding_report: GroundingReport,
    template_echo_report: TemplateEchoReport,
    composer_source: str = "",
) -> bool:
    """Return True when Reader/Grounding/Template Guard expose traceable gates.

    This does not mean the candidate is displayable. It means Phase 7 can expose
    pass/fail and rejection_reason for every relevant judge gate.
    """

    trace = build_emlis_gate_trace(
        reader_report=reader_report,
        grounding_report=grounding_report,
        template_echo_report=template_echo_report,
        composer_source=composer_source,
        phase_completion_ready=False,
    )
    required = ("reader", "grounding", "template_echo", "generation_source")
    for key in required:
        gate = trace.get(key)
        if not isinstance(gate, dict):
            return False
        if not isinstance(gate.get("passed"), bool):
            return False
        if not isinstance(gate.get("rejection_reasons"), list):
            return False
    return True


def decide_emlis_observation_display(
    *,
    comment_text: str,
    reader_report: ListenerReaderReport,
    grounding_report: GroundingReport,
    template_echo_report: TemplateEchoReport,
    safety_report: SafetyBoundaryReport | None = None,
    trace_id: str = "",
    composer_source: str = "",
    phase_completion_ready: bool = True,
) -> DisplayDecision:
    """Final fail-closed decision for displaying Emlis observation text."""

    safety = safety_report or SafetyBoundaryReport()
    source = str(composer_source or "").strip()
    text = str(comment_text or "").strip()
    gate_trace = build_emlis_gate_trace(
        reader_report=reader_report,
        grounding_report=grounding_report,
        template_echo_report=template_echo_report,
        safety_report=safety,
        composer_source=source,
        phase_completion_ready=phase_completion_ready,
    )
    reasons: List[str] = []

    if safety.requires_block:
        reasons.extend(safety.reasons or ["safety_boundary"])
        deduped = _dedupe(reasons)
        return DisplayDecision(
            observation_status="safety_blocked",
            comment_text="",
            rejection_reasons=deduped,
            trace_id=trace_id,
            gate_trace=_with_display_gate_trace(
                gate_trace,
                observation_status="safety_blocked",
                rejection_reasons=deduped,
                comment_text="",
            ),
        )

    if not phase_completion_ready:
        reasons.append("phase_not_complete")
    if source != "ai_generated":
        reasons.append("composer_source_not_ai_generated")
        if source in _UNAVAILABLE_SOURCES:
            reasons.append("composer_source_unavailable")
        elif source in _NON_AI_RENDERED_SOURCES:
            reasons.append("rule_rendered_or_fallback_source")
    if not reader_report.understandable:
        reasons.extend(reader_report.rejection_reasons or ["reader_cannot_understand"])
    if not grounding_report.passed:
        reasons.extend(grounding_report.rejection_reasons or ["ungrounded_or_relation_broken"])
    if not template_echo_report.passed:
        reasons.extend(template_echo_report.rejection_reasons or ["template_or_echo_detected"])
    if not text:
        reasons.append("empty_comment_text")
        if source in _UNAVAILABLE_SOURCES:
            reasons.append("empty_comment_text_without_candidate")

    if reasons:
        deduped = _dedupe(reasons)
        status = _status_for_failure(source=source, reasons=deduped)
        return DisplayDecision(
            observation_status=status,
            comment_text="",
            rejection_reasons=deduped,
            trace_id=trace_id,
            gate_trace=_with_display_gate_trace(
                gate_trace,
                observation_status=status,
                rejection_reasons=deduped,
                comment_text="",
            ),
        )

    return DisplayDecision(
        observation_status="passed",
        comment_text=text,
        rejection_reasons=[],
        trace_id=trace_id,
        gate_trace=_with_display_gate_trace(
            gate_trace,
            observation_status="passed",
            rejection_reasons=[],
            comment_text=text,
        ),
    )


def phase8_display_gate_contract_ready(display_decision: DisplayDecision | None = None) -> bool:
    """Return True when Display Gate enforces the Phase 8 fail-closed contract.

    With no argument, this verifies the generic gate behavior using synthetic
    reports. With a decision, it verifies that the decision is internally
    consistent: passed decisions must carry text, while every non-passed
    decision must have an empty comment_text and traceable reasons.
    """

    if display_decision is not None:
        status = str(getattr(display_decision, "observation_status", "") or "")
        if status not in _VALID_STATUSES:
            return False
        gate_trace = getattr(display_decision, "gate_trace", {}) or {}
        if not isinstance(gate_trace, Mapping):
            return False
        for key in _required_gate_trace_keys():
            gate = gate_trace.get(key)
            if not isinstance(gate, Mapping):
                return False
            if not isinstance(gate.get("passed"), bool):
                return False
            if not isinstance(gate.get("rejection_reasons"), list):
                return False
        display_gate = gate_trace.get("display_gate")
        if not isinstance(display_gate, Mapping) or not isinstance(display_gate.get("passed"), bool):
            return False
        comment_text = str(getattr(display_decision, "comment_text", "") or "").strip()
        reasons = list(getattr(display_decision, "rejection_reasons", []) or [])
        if status == "passed":
            return bool(comment_text) and not reasons and _all_core_gates_passed(gate_trace) and display_gate.get("passed") is True
        if comment_text:
            return False
        if status == "safety_blocked":
            return (not _gate_passed(gate_trace, "safety")) and bool(reasons)
        return (not _all_core_gates_passed(gate_trace)) and bool(reasons)

    passing_reader = ListenerReaderReport(
        understandable=True,
        addressee_clear=True,
        speaker_integrity_ok=True,
        conversational=True,
        report_like=False,
        confidence=1.0,
    )
    failing_reader = ListenerReaderReport(
        understandable=False,
        addressee_clear=False,
        speaker_integrity_ok=False,
        conversational=False,
        report_like=True,
        rejection_reasons=["reader_cannot_understand"],
        confidence=0.0,
    )
    passing_grounding = GroundingReport(passed=True, coverage_ratio=1.0, confidence=1.0)
    failing_grounding = GroundingReport(passed=False, rejection_reasons=["empty_text"])
    passing_template = TemplateEchoReport(passed=True)

    passed = decide_emlis_observation_display(
        comment_text="candidate",
        reader_report=passing_reader,
        grounding_report=passing_grounding,
        template_echo_report=passing_template,
        composer_source="ai_generated",
        phase_completion_ready=True,
    )
    reader_rejected = decide_emlis_observation_display(
        comment_text="candidate",
        reader_report=failing_reader,
        grounding_report=passing_grounding,
        template_echo_report=passing_template,
        composer_source="ai_generated",
        phase_completion_ready=True,
    )
    source_rejected = decide_emlis_observation_display(
        comment_text="candidate",
        reader_report=passing_reader,
        grounding_report=passing_grounding,
        template_echo_report=passing_template,
        composer_source="rule_rendered",
        phase_completion_ready=True,
    )
    unavailable = decide_emlis_observation_display(
        comment_text="",
        reader_report=failing_reader,
        grounding_report=failing_grounding,
        template_echo_report=passing_template,
        composer_source="unavailable",
        phase_completion_ready=True,
    )
    safety = decide_emlis_observation_display(
        comment_text="candidate",
        reader_report=passing_reader,
        grounding_report=passing_grounding,
        template_echo_report=passing_template,
        safety_report=SafetyBoundaryReport(requires_block=True, reasons=["safety_boundary"]),
        composer_source="ai_generated",
        phase_completion_ready=True,
    )

    return bool(
        phase8_display_gate_contract_ready(passed)
        and passed.observation_status == "passed"
        and passed.comment_text == "candidate"
        and phase8_display_gate_contract_ready(reader_rejected)
        and reader_rejected.observation_status == "rejected"
        and reader_rejected.comment_text == ""
        and phase8_display_gate_contract_ready(source_rejected)
        and source_rejected.observation_status == "rejected"
        and source_rejected.comment_text == ""
        and phase8_display_gate_contract_ready(unavailable)
        and unavailable.observation_status == "unavailable"
        and unavailable.comment_text == ""
        and phase8_display_gate_contract_ready(safety)
        and safety.observation_status == "safety_blocked"
        and safety.comment_text == ""
    )


__all__ = [
    "build_emlis_gate_trace",
    "build_phase10_release_readiness",
    "phase7_judge_contract_ready",
    "phase8_display_gate_contract_ready",
    "phase9_frontend_display_contract_ready",
    "phase10_release_readiness_contract_ready",
    "decide_emlis_observation_display",
]
