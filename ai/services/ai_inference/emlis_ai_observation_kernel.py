# -*- coding: utf-8 -*-
from __future__ import annotations

"""Compatibility adapter for the retired single-kernel EmlisAI path.

The former implementation rendered user-facing observation text from role-based
fixed phrases.  The new EmlisAI path is multi-perspective and fail-closed, so
this module no longer owns sentence templates.  It keeps the historical public
function name for tests and internal imports, then delegates to the new evidence
ledger -> perspective observers -> graph -> composer -> judges pipeline.
"""

from dataclasses import dataclass
from typing import List, Optional

from emlis_ai_conversation_composer_service import compose_emlis_conversation
from emlis_ai_display_gate import decide_emlis_observation_display
from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_grounding_judge import judge_grounding
from emlis_ai_listener_reader_judge import judge_listener_readability
from emlis_ai_observation_integrator_service import integrate_perspective_board
from emlis_ai_perspective_board import build_perspective_board
from emlis_ai_perspective_observers import run_perspective_observers
from emlis_ai_template_echo_guard import guard_template_echo
from emlis_ai_types import (
    DerivedUserModel,
    EmlisAICapabilityConfig,
    EvidenceRef,
    ObservationCandidate,
    ObservationDecision,
    ReplyLengthPlan,
    ReplyLine,
    SentenceEvidence,
    SourceBundle,
    StyleProfile,
    WorldModel,
)


@dataclass
class ObservationKernelInput:
    capability: EmlisAICapabilityConfig
    bundle: SourceBundle
    world_model: WorldModel
    style_profile: StyleProfile
    working_model: Optional[DerivedUserModel] = None


def _current_ref(bundle: SourceBundle) -> EvidenceRef:
    current = bundle.current_input or {}
    return EvidenceRef(
        kind="emotion",
        ref_id=str(current.get("id") or current.get("created_at") or "current"),
        weight=1.0,
    )


def _selected_labels(world_model: Optional[WorldModel], bundle: SourceBundle) -> List[str]:
    labels: List[str] = []
    facts = getattr(world_model, "facts", None)
    for item in list(getattr(facts, "selected_emotions", []) or []):
        label = str(getattr(item, "type", "") or "").strip()
        if label and label not in labels:
            labels.append(label)
    for item in list(getattr(facts, "current_emotion_labels", []) or []):
        label = str(item or "").strip()
        if label and label not in labels:
            labels.append(label)
    current = bundle.current_input or {}
    for key in ("emotion_details", "emotions"):
        values = current.get(key) or []
        if not isinstance(values, list):
            values = [values]
        for item in values:
            if isinstance(item, dict):
                label = str(item.get("type") or item.get("name") or "").strip()
            else:
                label = str(item or "").strip()
            if label and label not in labels:
                labels.append(label)
    dominant = str(getattr(facts, "dominant_emotion", "") or "").strip()
    if dominant and dominant not in labels:
        labels.insert(0, dominant)
    return labels[:4]


def _center_label(labels: List[str], world_model: Optional[WorldModel]) -> str:
    facts = getattr(world_model, "facts", None)
    dominant = str(getattr(facts, "dominant_emotion", "") or "").strip()
    if dominant:
        return dominant
    return labels[0] if labels else ""


def _line_key(index: int, *, is_last: bool = False) -> str:
    if index == 0:
        return "receive"
    if is_last:
        return "receiving_close"
    return f"observation_{index}"


def _reply_lines_from_text(text: str, evidence: EvidenceRef) -> List[ReplyLine]:
    lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
    # Historical callers add the greeting separately.  Keep this adapter focused
    # on observation body lines when the first line is only the greeting.
    if lines and "Emlisです" in lines[0]:
        lines = lines[1:]
    reply_lines: List[ReplyLine] = []
    for idx, line in enumerate(lines):
        reply_lines.append(
            ReplyLine(
                key=_line_key(idx, is_last=idx == len(lines) - 1),
                text=line,
                sentence_evidence=SentenceEvidence(line_key=f"line_{idx}", evidence=[evidence]),
                candidate_key="multi_perspective_adapter",
            )
        )
    return reply_lines


def run_emlis_ai_observation_kernel(*, kernel_input: ObservationKernelInput) -> ObservationDecision:
    """Run the new multi-perspective path through the legacy return type.

    This function intentionally does not contain user-facing sentence templates
    and does not call the retired fixed fallback.
    """

    bundle = kernel_input.bundle
    current_ref = _current_ref(bundle)
    labels = _selected_labels(kernel_input.world_model, bundle)
    center = _center_label(labels, kernel_input.world_model)
    evidence_spans = build_evidence_ledger(bundle.current_input)
    reports = run_perspective_observers(evidence_spans)
    board = build_perspective_board(evidence_spans=evidence_spans, reports=reports)
    graph = integrate_perspective_board(board=board, display_name=bundle.display_name)
    candidate_text = compose_emlis_conversation(
        graph=graph,
        evidence_spans=evidence_spans,
        display_name=bundle.display_name,
        greeting_text=getattr(getattr(bundle, "greeting", None), "greeting_text", "") or "",
    )
    reader = judge_listener_readability(candidate_text)
    grounding = judge_grounding(comment_text=candidate_text, graph=graph, evidence_spans=evidence_spans)
    template_echo = guard_template_echo(comment_text=candidate_text, evidence_spans=evidence_spans)
    decision = decide_emlis_observation_display(
        comment_text=candidate_text,
        reader_report=reader,
        grounding_report=grounding,
        template_echo_report=template_echo,
        safety_report=None,
        trace_id="legacy-kernel-adapter",
    )
    final_text = decision.comment_text if decision.observation_status == "passed" else ""
    reply_lines = _reply_lines_from_text(final_text, current_ref)
    candidate = ObservationCandidate(
        candidate_key="multi_perspective_adapter",
        kind="receive",
        text="\n".join(line.text for line in reply_lines),
        evidence=[current_ref],
        confidence=0.8 if final_text else 0.0,
        notes={"observation_status": decision.observation_status, "rejection_reasons": decision.rejection_reasons},
    )
    max_lines = max(3, min(8, int(getattr(graph.addressee_notes, "sentence_target", 5) or 5) + 1))
    length_plan = ReplyLengthPlan(
        mode="input_scaled",
        max_lines=max_lines,
        target_lines=max(0, len(reply_lines)),
        reason="multi_perspective_adapter",
        input_effort_score=float((bundle.input_effort or {}).get("effort_score") or 0.0),
        history_usable=False,
        interpretive_frame_usable=False,
        cross_core_usable=False,
        clear_long_input=bool(len(evidence_spans) >= 6),
        meaning_block_count=len(evidence_spans),
        selected_meaning_block_count=len(evidence_spans),
        meaning_coverage_ratio=1.0 if evidence_spans else 0.0,
    )
    return ObservationDecision(
        accepted_candidates=[candidate] if final_text else [],
        rejected_candidates=[] if final_text else [candidate],
        unknowns=list(graph.missing_information),
        conflicts=[edge.relation_type for edge in graph.core_tensions],
        reply_lines=reply_lines,
        reply_length_plan=length_plan,
        debug={
            "kernel_version": "multi_perspective_adapter.v1",
            "observation_status": decision.observation_status,
            "rejection_reasons": decision.rejection_reasons,
            "observer_ids": [report.observer_id for report in reports],
            "reader_reasons": reader.rejection_reasons,
            "grounding_reasons": grounding.rejection_reasons,
            "template_reasons": template_echo.rejection_reasons,
        },
    )


__all__ = ["ObservationKernelInput", "run_emlis_ai_observation_kernel"]
