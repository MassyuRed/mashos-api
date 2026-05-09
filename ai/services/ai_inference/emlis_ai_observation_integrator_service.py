# -*- coding: utf-8 -*-
from __future__ import annotations

"""Observation integrator for EmlisAI multi-perspective pipeline.

The integrator creates an ObservationGraph. It still does not create final
user-facing sentences.
"""

import re
from typing import Dict, List, Sequence

from emlis_ai_types import (
    AddresseeNotes,
    EvidenceSpan,
    GraphClaim,
    ObservationClaim,
    ObservationGraph,
    PerspectiveBoard,
    PerspectiveReport,
    RelationEdge,
)
from emlis_ai_user_address_service import display_name_call


def _clean(value: object, limit: int = 52) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip(" 、,。.!！?？")
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip("、,") + "…"


def _claim_index(reports: Sequence[PerspectiveReport]) -> Dict[str, ObservationClaim]:
    out: Dict[str, ObservationClaim] = {}
    for report in reports:
        for claim in report.claims:
            out[claim.claim_id] = claim
    return out


def _span_index(spans: Sequence[EvidenceSpan]) -> Dict[str, EvidenceSpan]:
    return {span.span_id: span for span in spans}


def _claim_to_graph(claim: ObservationClaim, *, prefix: str) -> GraphClaim:
    return GraphClaim(
        claim_id=f"{prefix}.{claim.claim_id}",
        claim_type=claim.claim_type,
        text=_clean(claim.object or claim.subject),
        evidence_span_ids=list(claim.evidence_span_ids),
        confidence=float(claim.confidence or 0.0),
    )


def _select_claims(reports: Sequence[PerspectiveReport], *types: str, limit: int = 4) -> List[ObservationClaim]:
    wanted = set(types)
    claims: List[ObservationClaim] = []
    for report in reports:
        for claim in report.claims:
            if claim.claim_type in wanted:
                claims.append(claim)
    claims.sort(key=lambda item: (-float(item.confidence or 0.0), item.claim_id))
    return claims[:limit]


def _primary_state_from_board(board: PerspectiveBoard, claims: Dict[str, ObservationClaim]) -> GraphClaim:
    conflict_report = next((report for report in board.reports if report.observer_id == "conflict_coexistence"), None)
    if conflict_report and conflict_report.relations:
        edge = conflict_report.relations[0]
        left = claims.get(edge.from_claim_id)
        right = claims.get(edge.to_claim_id)
        left_text = _clean(left.object if left else "")
        right_text = _clean(right.object if right else "")
        if left_text and right_text:
            return GraphClaim(
                claim_id="graph.primary.coexistence",
                claim_type="primary_state",
                text=f"{left_text} / {right_text}",
                evidence_span_ids=list(dict.fromkeys(edge.evidence_span_ids)),
                confidence=float(edge.confidence or 0.0),
            )
    # Fallback: strongest explicit content or selected emotion as a shallow state.
    for report in board.reports:
        for claim in report.claims:
            if claim.object:
                return GraphClaim(
                    claim_id="graph.primary.explicit",
                    claim_type="primary_state",
                    text=_clean(claim.object),
                    evidence_span_ids=list(claim.evidence_span_ids),
                    confidence=float(claim.confidence or 0.0),
                )
    return GraphClaim(
        claim_id="graph.primary.missing",
        claim_type="primary_state",
        text="",
        evidence_span_ids=[],
        confidence=0.0,
    )


def integrate_perspective_board(*, board: PerspectiveBoard, display_name: object = None) -> ObservationGraph:
    reports = list(board.reports or [])
    claim_by_id = _claim_index(reports)
    spans_by_id = _span_index(board.evidence_spans)

    core_tensions: List[RelationEdge] = []
    for report in reports:
        if report.observer_id == "conflict_coexistence":
            core_tensions.extend(report.relations)
    relation_priority = {"tension": 0, "limit_tension": 1, "explicit_transition": 2, "coexistence": 3}
    core_tensions.sort(key=lambda edge: (relation_priority.get(edge.relation_type, 9), -float(edge.confidence or 0.0), edge.edge_id))

    pressure_sources = [
        _claim_to_graph(claim, prefix="graph.pressure")
        for claim in _select_claims(reports, "pressure_source", limit=4)
    ]
    limit_signals = [
        _claim_to_graph(claim, prefix="graph.limit")
        for claim in _select_claims(reports, "limit_signal", limit=3)
    ]
    self_awareness = [
        _claim_to_graph(claim, prefix="graph.self")
        for claim in _select_claims(reports, "self_awareness", limit=4)
    ]
    value_or_strength = [
        _claim_to_graph(claim, prefix="graph.value")
        for claim in _select_claims(reports, "value_signal", "grounded_strength_signal", limit=5)
    ]

    safety_boundaries: List[str] = []
    for claim in _select_claims(reports, "safety_boundary", limit=3):
        for span_id in claim.evidence_span_ids:
            span = spans_by_id.get(span_id)
            if span and span.raw_text not in safety_boundaries:
                safety_boundaries.append(span.raw_text)

    addressee_claim = next(
        (claim for report in reports if report.observer_id == "addressee_model" for claim in report.claims),
        None,
    )
    memo_len = sum(len(span.raw_text) for span in board.evidence_spans if span.source_field in {"memo", "memo_action"})
    sentence_target = 4 if memo_len < 90 else 5 if memo_len < 260 else 6
    if addressee_claim and str(addressee_claim.object or "") == "paced_conversational":
        sentence_target = max(sentence_target, 5)

    forbidden_claims: List[str] = []
    for report in reports:
        for item in report.do_not_say:
            if item and item not in forbidden_claims:
                forbidden_claims.append(item)

    missing_information: List[str] = []
    if not board.evidence_spans:
        missing_information.append("no_current_input_text")
    if not core_tensions and len([s for s in board.evidence_spans if s.source_field in {"memo", "memo_action"}]) >= 2:
        missing_information.append("relation_not_confident")

    return ObservationGraph(
        primary_state=_primary_state_from_board(board, claim_by_id),
        core_tensions=core_tensions[:4],
        pressure_sources=pressure_sources,
        limit_signals=limit_signals,
        self_awareness=self_awareness,
        value_or_strength_signals=value_or_strength,
        addressee_notes=AddresseeNotes(
            display_name_call=display_name_call(display_name),
            sentence_target=sentence_target,
            voice_distance="close",
            needs_gentle_pacing=True,
            avoid_report_like=True,
        ),
        safety_boundaries=safety_boundaries,
        forbidden_claims=forbidden_claims,
        missing_information=missing_information,
    )


__all__ = ["integrate_perspective_board"]
