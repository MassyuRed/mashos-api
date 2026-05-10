# -*- coding: utf-8 -*-
from __future__ import annotations

"""Grounding judge for EmlisAI output."""

import re
from typing import Any, List, Sequence, Set

from emlis_ai_types import EvidenceSpan, GroundingReport, GroundingSentenceClaim, ObservationGraph

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？!?])\s*|\n+")
_FUNCTION_WORD_RE = re.compile(
    r"^(入力全体|Emlis|言葉|気持ち|状態|場所|重さ|力|願い|自覚|負荷|部分|反応|感覚|中|二つ|その二つ|今|今回)$"
)
_RELATION_RE = re.compile(
    r"(同じ場所|同じ中|並んで|せめぎ合|重なって|だけではなく|一方|簡単には|その中でも|そこに|離れていない|二つの間|つながって|同時に)"
)
_GENERIC_RELATION_SENTENCE_RE = re.compile(r"(その二つ|二つの間|同じ場所|同じ中|並んで|重なって|離れていない|同時に)")
_OVERCLAIM_RE = re.compile(r"(本当は|本当の願い|頼りたい|愛されたい|前向き|強い人|性格|診断|病気|治療|医療|弱さではなく)")


def _sentences(text: Any) -> List[str]:
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(str(text or "")) if s.strip()]


def _normalize(text: Any) -> str:
    return re.sub(r"[\s、。.!！?？「」『』（）()]+", "", str(text or "")).strip()


def _char_ngrams(text: str, n: int = 3) -> Set[str]:
    compact = _normalize(text)
    if len(compact) < n:
        return {compact} if compact else set()
    return {compact[i : i + n] for i in range(len(compact) - n + 1)}


def _ngram_overlap(a: str, b: str) -> float:
    aa = _char_ngrams(a)
    bb = _char_ngrams(b)
    if not aa or not bb:
        return 0.0
    return len(aa.intersection(bb)) / max(1, min(len(aa), len(bb)))


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


def _span_matches_sentence(sentence: str, span: EvidenceSpan) -> bool:
    raw = str(span.raw_text or "").strip()
    if not raw:
        return False
    sentence_norm = _normalize(sentence)
    raw_norm = _normalize(raw)
    if len(raw_norm) >= 3 and (raw_norm in sentence_norm or sentence_norm in raw_norm):
        return True
    sentence_terms = _terms(sentence)
    span_terms = _terms(raw)
    if sentence_terms.intersection(span_terms):
        return True
    return _ngram_overlap(sentence, raw) >= 0.18


def _relation_edge_evidence(graph: ObservationGraph) -> List[str]:
    out: List[str] = []
    for edge in graph.core_tensions:
        for span_id in edge.evidence_span_ids:
            if span_id and span_id not in out:
                out.append(span_id)
    return out


def judge_grounding(*, comment_text: Any, graph: ObservationGraph, evidence_spans: Sequence[EvidenceSpan]) -> GroundingReport:
    sentences = _sentences(comment_text)
    evidence_text = "\n".join(str(span.raw_text or "") for span in evidence_spans)
    relation_edge_ids = _relation_edge_evidence(graph)

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
        relation_supported = bool(_RELATION_RE.search(sentence))
        if relation_supported:
            relation_supported_count += 1
        matched_ids = [span.span_id for span in evidence_spans if _span_matches_sentence(sentence, span)]
        if not matched_ids and relation_supported and _GENERIC_RELATION_SENTENCE_RE.search(sentence):
            matched_ids = relation_edge_ids[:5]

        unsupported_reason = ""
        if _OVERCLAIM_RE.search(sentence) and not _OVERCLAIM_RE.search(evidence_text):
            unsupported_reason = "unsupported_overclaim"
        elif not matched_ids:
            unsupported_reason = "no_evidence_span_or_relation"

        if unsupported_reason:
            unsupported += 1
        claims.append(
            GroundingSentenceClaim(
                sentence_index=idx,
                sentence=sentence,
                evidence_span_ids=list(dict.fromkeys(matched_ids))[:5],
                relation_supported=relation_supported,
                unsupported_reason=unsupported_reason,
            )
        )

    content_sentence_count = len([s for s in sentences if "Emlisです" not in s])
    coverage_ratio = 0.0 if content_sentence_count <= 0 else 1.0 - (unsupported / max(1, content_sentence_count))
    reasons: List[str] = []
    if content_sentence_count <= 0:
        reasons.append("empty_text")
    if unsupported > 0:
        reasons.append("unsupported_sentence")
    if graph.core_tensions and relation_supported_count < 1:
        reasons.append("core_relation_not_reflected")
    if graph_evidence_ids and not any(set(c.evidence_span_ids).intersection(graph_evidence_ids) for c in claims):
        reasons.append("graph_evidence_not_used")

    reasons = list(dict.fromkeys(reasons))
    return GroundingReport(
        passed=not reasons and coverage_ratio >= 0.65,
        sentence_claims=claims,
        rejection_reasons=reasons,
        coverage_ratio=round(coverage_ratio, 3),
        confidence=0.86 if not reasons else 0.42,
    )


__all__ = ["judge_grounding"]
