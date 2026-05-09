# -*- coding: utf-8 -*-
from __future__ import annotations

"""Fail-closed display gate for EmlisAI observation."""

from typing import List

from emlis_ai_types import DisplayDecision, GroundingReport, ListenerReaderReport, SafetyBoundaryReport, TemplateEchoReport


def decide_emlis_observation_display(
    *,
    comment_text: str,
    reader_report: ListenerReaderReport,
    grounding_report: GroundingReport,
    template_echo_report: TemplateEchoReport,
    safety_report: SafetyBoundaryReport | None = None,
    trace_id: str = "",
) -> DisplayDecision:
    safety = safety_report or SafetyBoundaryReport()
    reasons: List[str] = []
    if safety.requires_block:
        reasons.extend(safety.reasons or ["safety_boundary"])
        return DisplayDecision(observation_status="safety_blocked", comment_text="", rejection_reasons=reasons, trace_id=trace_id)
    if not reader_report.understandable:
        reasons.extend(reader_report.rejection_reasons or ["reader_cannot_understand"])
    if not grounding_report.passed:
        reasons.extend(grounding_report.rejection_reasons or ["ungrounded_or_relation_broken"])
    if not template_echo_report.passed:
        reasons.extend(template_echo_report.rejection_reasons or ["template_or_echo_detected"])
    if not str(comment_text or "").strip():
        reasons.append("empty_comment_text")
    if reasons:
        deduped = list(dict.fromkeys(reasons))
        return DisplayDecision(observation_status="rejected", comment_text="", rejection_reasons=deduped, trace_id=trace_id)
    return DisplayDecision(observation_status="passed", comment_text=str(comment_text or "").strip(), rejection_reasons=[], trace_id=trace_id)


__all__ = ["decide_emlis_observation_display"]
