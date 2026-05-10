# -*- coding: utf-8 -*-
from __future__ import annotations

"""Observation Integrator for the EmlisAI multi-perspective pipeline.

Phase 5 turns the Perspective Board into an ObservationGraph.  The output is a
structural graph for later Composer/Judge phases; it is not final Emlis
observation text and must not be used as ``comment_text``.
"""

import re
from typing import Dict, Iterable, List, Sequence

from emlis_ai_perspective_board import phase5_board_contract_ready, validate_perspective_board
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

_TEXT_FIELDS = {"memo", "memo_action"}
_STRUCTURE_LABEL_SEPARATOR = " | "


def _clean(value: object, limit: int = 52) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip(" 、,。.!！?？")
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip("、,") + "…"


def _claim_index(reports: Sequence[PerspectiveReport]) -> Dict[str, ObservationClaim]:
    out: Dict[str, ObservationClaim] = {}
    for report in reports or []:
        for claim in report.claims or []:
            if claim.claim_id and claim.claim_id not in out:
                out[claim.claim_id] = claim
    return out


def _span_index(spans: Sequence[EvidenceSpan]) -> Dict[str, EvidenceSpan]:
    return {span.span_id: span for span in spans or [] if span.span_id}


def _unique(values: Iterable[str]) -> List[str]:
    out: List[str] = []
    for value in values or []:
        text = str(value or "").strip()
        if text and text not in out:
            out.append(text)
    return out


def _claim_to_graph(claim: ObservationClaim, *, prefix: str) -> GraphClaim:
    return GraphClaim(
        claim_id=f"{prefix}.{claim.claim_id}",
        claim_type=claim.claim_type,
        text=_clean(claim.object or claim.subject),
        evidence_span_ids=_unique(claim.evidence_span_ids),
        confidence=float(claim.confidence or 0.0),
    )


def _select_claims(reports: Sequence[PerspectiveReport], *types: str, limit: int = 4) -> List[ObservationClaim]:
    wanted = set(types)
    claims: List[ObservationClaim] = []
    for report in reports or []:
        for claim in report.claims or []:
            if claim.claim_type in wanted:
                claims.append(claim)
    claims.sort(key=lambda item: (-float(item.confidence or 0.0), str(item.claim_id)))
    return claims[:limit]


def _text_span_count(spans: Sequence[EvidenceSpan]) -> int:
    return len([span for span in spans or [] if span.source_field in _TEXT_FIELDS])


def _primary_state_from_board(board: PerspectiveBoard, claims: Dict[str, ObservationClaim]) -> GraphClaim:
    """Create a source-bound primary state claim without composing body text."""

    conflict_report = next((report for report in board.reports if report.observer_id == "conflict_coexistence"), None)
    if conflict_report and conflict_report.relations:
        ranked_edges = sorted(
            conflict_report.relations,
            key=lambda edge: (
                {"tension": 0, "limit_tension": 1, "explicit_transition": 2, "coexistence": 3}.get(edge.relation_type, 9),
                -float(edge.confidence or 0.0),
                str(edge.edge_id),
            ),
        )
        for edge in ranked_edges:
            left = claims.get(edge.from_claim_id)
            right = claims.get(edge.to_claim_id)
            left_text = _clean(left.object if left else "")
            right_text = _clean(right.object if right else "")
            if left_text and right_text:
                return GraphClaim(
                    claim_id="graph.primary.relation",
                    claim_type="primary_state",
                    text=_STRUCTURE_LABEL_SEPARATOR.join([left_text, right_text]),
                    evidence_span_ids=_unique(edge.evidence_span_ids),
                    confidence=float(edge.confidence or 0.0),
                )

    # Fallback: strongest explicit content or selected emotion as a shallow state.
    ranked_claims: List[ObservationClaim] = []
    for report in board.reports or []:
        for claim in report.claims or []:
            if claim.object:
                ranked_claims.append(claim)
    ranked_claims.sort(key=lambda item: (-float(item.confidence or 0.0), str(item.claim_id)))
    if ranked_claims:
        claim = ranked_claims[0]
        return GraphClaim(
            claim_id="graph.primary.explicit",
            claim_type="primary_state",
            text=_clean(claim.object),
            evidence_span_ids=_unique(claim.evidence_span_ids),
            confidence=float(claim.confidence or 0.0),
        )

    return GraphClaim(
        claim_id="graph.primary.missing",
        claim_type="primary_state",
        text="",
        evidence_span_ids=[],
        confidence=0.0,
    )


def _core_tensions_from_reports(reports: Sequence[PerspectiveReport]) -> List[RelationEdge]:
    out: List[RelationEdge] = []
    for report in reports or []:
        if report.observer_id == "conflict_coexistence":
            out.extend(report.relations or [])
    priority = {"tension": 0, "limit_tension": 1, "explicit_transition": 2, "coexistence": 3}
    out.sort(key=lambda edge: (priority.get(edge.relation_type, 9), -float(edge.confidence or 0.0), str(edge.edge_id)))
    return out[:6]


def integrate_perspective_board(*, board: PerspectiveBoard, display_name: object = None) -> ObservationGraph:
    """Integrate reports into an ObservationGraph without generating final text."""

    reports = list(board.reports or [])
    claim_by_id = dict(getattr(board, "claims_by_id", {}) or {}) or _claim_index(reports)
    spans_by_id = _span_index(board.evidence_spans)

    core_tensions = _core_tensions_from_reports(reports)
    pressure_sources = [_claim_to_graph(claim, prefix="graph.pressure") for claim in _select_claims(reports, "pressure_source", limit=4)]
    limit_signals = [_claim_to_graph(claim, prefix="graph.limit") for claim in _select_claims(reports, "limit_signal", limit=3)]
    self_awareness = [_claim_to_graph(claim, prefix="graph.self") for claim in _select_claims(reports, "self_awareness", limit=4)]
    value_or_strength = [
        _claim_to_graph(claim, prefix="graph.value")
        for claim in _select_claims(reports, "value_signal", "grounded_strength_signal", limit=5)
    ]

    safety_boundaries: List[str] = []
    for claim in _select_claims(reports, "safety_boundary", limit=3):
        for span_id in claim.evidence_span_ids or []:
            span = spans_by_id.get(span_id)
            if span and span.raw_text and span.raw_text not in safety_boundaries:
                safety_boundaries.append(span.raw_text)

    addressee_claim = next((claim for report in reports if report.observer_id == "addressee_model" for claim in report.claims), None)
    memo_len = sum(len(span.raw_text) for span in board.evidence_spans if span.source_field in _TEXT_FIELDS)
    sentence_target = 4 if memo_len < 90 else 5 if memo_len < 260 else 6
    if addressee_claim and str(addressee_claim.object or "") == "paced_conversational":
        sentence_target = max(sentence_target, 5)

    forbidden_claims: List[str] = []
    for report in reports:
        forbidden_claims.extend(report.do_not_say or [])
    forbidden_claims.extend(getattr(board, "validation_issues", []) or [])
    forbidden_claims = _unique(forbidden_claims)

    missing_information: List[str] = []
    if not board.evidence_spans:
        missing_information.append("no_current_input_text")
    if not core_tensions and _text_span_count(board.evidence_spans) >= 2:
        missing_information.append("relation_not_confident")
    if not phase5_board_contract_ready(board):
        missing_information.append("perspective_board_contract_not_ready")

    return ObservationGraph(
        primary_state=_primary_state_from_board(board, claim_by_id),
        core_tensions=core_tensions,
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


def validate_observation_graph(graph: ObservationGraph, board: PerspectiveBoard) -> List[str]:
    """Validate Phase 5 graph structure without approving display text."""

    issues: List[str] = []
    issues.extend(validate_perspective_board(board))
    evidence_ids = {span.span_id for span in board.evidence_spans if span.span_id}
    claim_ids = set((getattr(board, "claims_by_id", {}) or _claim_index(board.reports)).keys())

    if board.evidence_spans and not str(graph.primary_state.text or "").strip():
        issues.append("graph_primary_state_missing")

    graph_claims = [
        graph.primary_state,
        *list(graph.pressure_sources or []),
        *list(graph.limit_signals or []),
        *list(graph.self_awareness or []),
        *list(graph.value_or_strength_signals or []),
    ]
    for claim in graph_claims:
        if not claim.claim_id:
            issues.append("graph_claim_without_id")
        for span_id in claim.evidence_span_ids or []:
            if evidence_ids and span_id not in evidence_ids:
                issues.append(f"graph_claim_unknown_evidence:{span_id}")

    for edge in graph.core_tensions or []:
        if not edge.edge_id:
            issues.append("graph_relation_without_id")
        if edge.from_claim_id not in claim_ids or edge.to_claim_id not in claim_ids:
            issues.append(f"graph_relation_unknown_claim:{edge.edge_id}")
        if not edge.evidence_span_ids:
            issues.append(f"graph_relation_without_evidence:{edge.edge_id}")
        for span_id in edge.evidence_span_ids or []:
            if evidence_ids and span_id not in evidence_ids:
                issues.append(f"graph_relation_unknown_evidence:{span_id}")

    report_ids = {report.observer_id for report in board.reports}
    if report_ids and "addressee_model" in report_ids and not graph.addressee_notes:
        issues.append("graph_addressee_notes_missing")

    # If a specialist report produced these claim types, the Integrator must keep
    # them in the corresponding graph field.  Empty input is allowed to remain
    # shallow rather than invent structure.
    produced_types = {claim.claim_type for report in board.reports for claim in report.claims}
    if "pressure_source" in produced_types and not graph.pressure_sources:
        issues.append("graph_pressure_sources_missing")
    if "limit_signal" in produced_types and not graph.limit_signals:
        issues.append("graph_limit_signals_missing")
    if "self_awareness" in produced_types and not graph.self_awareness:
        issues.append("graph_self_awareness_missing")
    if ({"value_signal", "grounded_strength_signal"} & produced_types) and not graph.value_or_strength_signals:
        issues.append("graph_value_or_strength_missing")

    return list(dict.fromkeys(issues))


def phase5_observation_graph_ready(board: PerspectiveBoard, graph: ObservationGraph) -> bool:
    """Return True when Phase 5 board and graph contracts are satisfied."""

    return not validate_observation_graph(graph, board)


def phase5_integrator_contract_ready(board: PerspectiveBoard, graph: ObservationGraph) -> bool:
    """Alias used by the phase-gated implementation plan."""

    return phase5_observation_graph_ready(board, graph)


__all__ = [
    "integrate_perspective_board",
    "phase5_observation_graph_ready",
    "phase5_integrator_contract_ready",
    "validate_observation_graph",
]
