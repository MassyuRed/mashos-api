# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 5 Perspective Board for EmlisAI.

The board aggregates Specialist Observer reports into a single structural
workspace. It is not a writer: it never creates Emlis observation body text,
conversation lines, fallback text, or display-ready ``comment_text``.
"""

from typing import Dict, List, Sequence

from emlis_ai_types import EvidenceSpan, ObservationClaim, PerspectiveBoard, PerspectiveReport, RelationEdge
from emlis_ai_perspective_observers import SPECIALIST_OBSERVER_IDS, validate_perspective_reports


def _ordered_unique(values: Sequence[str]) -> List[str]:
    out: List[str] = []
    for value in values:
        item = str(value or "").strip()
        if item and item not in out:
            out.append(item)
    return out


def _build_claim_index(reports: Sequence[PerspectiveReport]) -> Dict[str, ObservationClaim]:
    index: Dict[str, ObservationClaim] = {}
    for report in reports or []:
        for claim in report.claims or []:
            if claim.claim_id:
                index[claim.claim_id] = claim
    return index


def _build_relation_index(reports: Sequence[PerspectiveReport]) -> Dict[str, RelationEdge]:
    index: Dict[str, RelationEdge] = {}
    for report in reports or []:
        for edge in report.relations or []:
            if edge.edge_id:
                index[edge.edge_id] = edge
    return index


def build_perspective_board(*, evidence_spans: Sequence[EvidenceSpan], reports: Sequence[PerspectiveReport]) -> PerspectiveBoard:
    """Collect Phase 4 PerspectiveReport objects for the integrator.

    ``PerspectiveBoard`` keeps ids and references so the integrator can verify
    the graph without re-reading final display text. This function deliberately
    avoids any user-facing sentence assembly.
    """

    span_list = list(evidence_spans or [])
    report_list = list(reports or [])
    claim_index = _build_claim_index(report_list)
    relation_index = _build_relation_index(report_list)
    evidence_span_index = {span.span_id: span for span in span_list if span.span_id}
    uncertainty = _ordered_unique([item for report in report_list for item in list(report.uncertainty or [])])
    do_not_say = _ordered_unique([item for report in report_list for item in list(report.do_not_say or [])])
    report_ids = _ordered_unique([report.observer_id for report in report_list])
    return PerspectiveBoard(
        evidence_spans=span_list,
        reports=report_list,
        report_ids=report_ids,
        claim_ids=_ordered_unique(list(claim_index.keys())),
        relation_ids=_ordered_unique(list(relation_index.keys())),
        evidence_span_ids=_ordered_unique(list(evidence_span_index.keys())),
        claim_index=claim_index,
        relation_index=relation_index,
        evidence_span_index=evidence_span_index,
        uncertainty=uncertainty,
        do_not_say=do_not_say,
        claims_by_id=claim_index,
        relations_by_id=relation_index,
    )


def validate_perspective_board(board: PerspectiveBoard) -> List[str]:
    """Validate that Phase 5 received a complete structural board.

    This is a phase-completion check, not a Display Gate approval. It verifies
    that observer reports were gathered, references remain inside the current
    evidence ledger, and no board item exposes display body fields.
    """

    issues: List[str] = []
    reports = list(getattr(board, "reports", []) or [])
    spans = list(getattr(board, "evidence_spans", []) or [])
    if tuple(report.observer_id for report in reports) != tuple(SPECIALIST_OBSERVER_IDS):
        issues.append("board_observer_order_or_count_mismatch")
    if not spans:
        issues.append("board_without_evidence_spans")
    if not reports:
        issues.append("board_without_reports")
    issues.extend(validate_perspective_reports(reports, spans))

    evidence_ids = {span.span_id for span in spans}
    claim_ids: Dict[str, str] = {}
    relation_ids: Dict[str, str] = {}
    for report in reports:
        for forbidden_attr in ("comment_text", "body", "reply_text", "emlis_text"):
            if hasattr(report, forbidden_attr):
                issues.append(f"{report.observer_id}:display_text_attr_present:{forbidden_attr}")
        for claim in report.claims:
            if claim.claim_id in claim_ids:
                issues.append(f"duplicate_claim_id:{claim.claim_id}")
            claim_ids[claim.claim_id] = report.observer_id
            for span_id in claim.evidence_span_ids:
                if span_id not in evidence_ids:
                    issues.append(f"{report.observer_id}:claim_unknown_evidence:{span_id}")
        for edge in report.relations:
            if edge.edge_id in relation_ids:
                issues.append(f"duplicate_relation_id:{edge.edge_id}")
            relation_ids[edge.edge_id] = report.observer_id
            for claim_id in (edge.from_claim_id, edge.to_claim_id):
                if claim_id not in claim_ids and all(claim.claim_id != claim_id for r in reports for claim in r.claims):
                    issues.append(f"{report.observer_id}:relation_unknown_claim:{edge.edge_id}:{claim_id}")
            for span_id in edge.evidence_span_ids:
                if span_id not in evidence_ids:
                    issues.append(f"{report.observer_id}:relation_unknown_evidence:{span_id}")

    if list(getattr(board, "report_ids", []) or []) and list(board.report_ids) != [report.observer_id for report in reports]:
        issues.append("board_report_ids_do_not_match_reports")
    if list(getattr(board, "claim_ids", []) or []) and set(board.claim_ids) != set(claim_ids.keys()):
        issues.append("board_claim_ids_do_not_match_claims")
    if list(getattr(board, "relation_ids", []) or []) and set(board.relation_ids) != set(relation_ids.keys()):
        issues.append("board_relation_ids_do_not_match_relations")
    if list(getattr(board, "evidence_span_ids", []) or []) and set(board.evidence_span_ids) != evidence_ids:
        issues.append("board_evidence_ids_do_not_match_spans")
    if list(getattr(board, "validation_issues", []) or []):
        issues.extend(str(item) for item in board.validation_issues if str(item or "").strip())
    return _ordered_unique(issues)


def phase5_board_contract_ready(board: PerspectiveBoard) -> bool:
    """Return True when Perspective Board aggregation is structurally ready."""

    return not validate_perspective_board(board)


__all__ = ["build_perspective_board", "validate_perspective_board", "phase5_board_contract_ready"]
