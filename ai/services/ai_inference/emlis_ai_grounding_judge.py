# -*- coding: utf-8 -*-
from __future__ import annotations

"""Grounding judge for EmlisAI output."""

import re
from typing import Any, List, Sequence, Set

from emlis_ai_types import EvidenceSpan, GroundingReport, GroundingSentenceClaim, ObservationGraph

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？!?])\s*|\n+")
_FUNCTION_WORD_RE = re.compile(r"^(入力全体|Emlis|言葉|気持ち|状態|場所|重さ|力|願い|自覚|負荷|部分)$")
_FUNCTIONAL_CLOSE_RE = re.compile(r"^(Emlisは|言葉の流れには|まだ決めきれない揺れも|今ここに出した言葉は)")


def _sentences(text: Any) -> List[str]:
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(str(text or "")) if s.strip()]


def _terms(text: str) -> Set[str]:
    cleaned = re.sub(r"[「」『』、。.!！?？\s]", " ", str(text or ""))
    chunks = [c.strip() for c in re.split(r"[ /・,，]+", cleaned) if c.strip()]
    out: Set[str] = set()
    for chunk in chunks:
        if _FUNCTION_WORD_RE.match(chunk):
            continue
        if len(chunk) >= 2:
            out.add(chunk[:18])
        # Add compact substrings for long Japanese clauses.
        if len(chunk) >= 6:
            out.add(chunk[:6])
            out.add(chunk[-6:])
    return out


def judge_grounding(*, comment_text: Any, graph: ObservationGraph, evidence_spans: Sequence[EvidenceSpan]) -> GroundingReport:
    sentences = _sentences(comment_text)
    evidence_terms_by_span = {span.span_id: _terms(span.raw_text) for span in evidence_spans}
    all_terms: Set[str] = set()
    for terms in evidence_terms_by_span.values():
        all_terms.update(terms)

    graph_evidence_ids = set(graph.primary_state.evidence_span_ids)
    for group in (graph.pressure_sources, graph.limit_signals, graph.self_awareness, graph.value_or_strength_signals):
        for claim in group:
            graph_evidence_ids.update(claim.evidence_span_ids)
    for edge in graph.core_tensions:
        graph_evidence_ids.update(edge.evidence_span_ids)

    claims: List[GroundingSentenceClaim] = []
    unsupported = 0
    relation_supported_count = 0
    for idx, sentence in enumerate(sentences):
        if "Emlisです" in sentence:
            claims.append(GroundingSentenceClaim(sentence_index=idx, sentence=sentence, evidence_span_ids=[], relation_supported=True))
            continue
        sentence_terms = _terms(sentence)
        matched_ids: List[str] = []
        for span_id, terms in evidence_terms_by_span.items():
            if sentence_terms.intersection(terms):
                matched_ids.append(span_id)
        relation_supported = bool(re.search(r"(同じ場所|並んで|せめぎ合|重なって|だけではなく|一方|簡単には|その中でも|そこに)", sentence))
        if relation_supported:
            relation_supported_count += 1
        functional_supported = bool(_FUNCTIONAL_CLOSE_RE.search(sentence) and graph_evidence_ids)
        unsupported_reason = ""
        if not matched_ids and not relation_supported and not functional_supported:
            unsupported += 1
            unsupported_reason = "no_evidence_span_or_relation"
        claims.append(
            GroundingSentenceClaim(
                sentence_index=idx,
                sentence=sentence,
                evidence_span_ids=matched_ids[:5],
                relation_supported=relation_supported,
                unsupported_reason=unsupported_reason,
            )
        )

    content_sentence_count = max(1, len([s for s in sentences if "Emlisです" not in s]))
    coverage_ratio = 1.0 - (unsupported / content_sentence_count)
    reasons: List[str] = []
    if unsupported > 1:
        reasons.append("too_many_unsupported_sentences")
    if graph.core_tensions and relation_supported_count < 1:
        reasons.append("core_relation_not_reflected")
    if graph_evidence_ids and not any(set(c.evidence_span_ids).intersection(graph_evidence_ids) for c in claims):
        reasons.append("graph_evidence_not_used")

    return GroundingReport(
        passed=not reasons and coverage_ratio >= 0.55,
        sentence_claims=claims,
        rejection_reasons=reasons,
        coverage_ratio=round(coverage_ratio, 3),
        confidence=0.84 if not reasons else 0.44,
    )


__all__ = ["judge_grounding"]
