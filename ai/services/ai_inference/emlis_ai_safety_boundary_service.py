# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step10 safety boundary policy for EmlisAI B-plan.

This helper is non-generative. It converts source-grounded safety evidence into
stable reason codes so the B-plan can stop before Composer execution. It never
creates user-facing observation text, advice, or fallback copy.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Sequence

from emlis_ai_types import EvidenceSpan, ObservationGraph, SafetyBoundaryReport

_POLICY_VERSION = "emlis.safety_boundary_policy.v1"
_TEXT_SOURCE_FIELDS = {"memo", "memo_action"}
_KIND_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "self_harm",
        re.compile(
            r"(死にたい|消えたい|生きていたくない|生きたくない|いなくなりたい|終わりにしたい|"
            r"自傷|自分を傷つけ|リスカ|OD|オーバードーズ|首を吊|首をつ|飛び降り|自殺)"
        ),
    ),
    ("harm_to_others", re.compile(r"(殺したい|刺したい|殴り殺|火をつけたい|危害を加えたい)", re.IGNORECASE)),
)


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("　", " ")).strip()


def _dedupe(values: Iterable[Any]) -> List[str]:
    out: List[str] = []
    for value in values or []:
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return out


def classify_safety_boundary_text(text: Any) -> List[str]:
    """Classify safety evidence into stable developer-facing kind codes."""

    value = _clean(text)
    if not value:
        return []
    if value in {"safety_boundary", "limited_scope_safety_boundary"}:
        return ["safety_risk"]
    kinds: List[str] = []
    for kind, pattern in _KIND_PATTERNS:
        if pattern.search(value):
            kinds.append(kind)
    return _dedupe(kinds)


def normalize_safety_boundary_codes(values: Iterable[Any]) -> List[str]:
    """Normalize safety inputs to graph-safe codes, not raw source text.

    Graph-level safety boundaries may already be raw unsafe source snippets or
    older boundary labels.  Any non-empty graph boundary is normalized to the
    stable code so raw user text never has to be carried through meta.
    """

    for value in values or []:
        item = _clean(value)
        if item:
            return ["safety_boundary"]
    return []


def _text_evidence_spans(evidence_spans: Sequence[EvidenceSpan] | None) -> List[EvidenceSpan]:
    return [
        span
        for span in list(evidence_spans or [])
        if _clean(getattr(span, "source_field", "")) in _TEXT_SOURCE_FIELDS
        and _clean(getattr(span, "span_id", ""))
    ]


@dataclass(frozen=True)
class EmlisSafetyBoundaryDecision:
    requires_block: bool = False
    reason_codes: List[str] = field(default_factory=list)
    boundary_types: List[str] = field(default_factory=list)
    evidence_span_ids: List[str] = field(default_factory=list)
    source_fields: List[str] = field(default_factory=list)
    graph_boundary_count: int = 0
    evidence_span_count: int = 0
    boundary_sources: List[str] = field(default_factory=list)

    def as_meta(self) -> Dict[str, Any]:
        requires = bool(self.requires_block)
        return {
            "version": "emlis.safety_boundary_decision.v1",
            "target_step": "Step10_safety_boundary",
            "phase": "B-S1",
            "requires_block": requires,
            "blocked_before_composer": requires,
            "composer_allowed": not requires,
            "composer_generation_allowed": not requires,
            "composer_must_not_run": requires,
            "normal_observation_allowed": not requires,
            "user_facing_text_allowed": not requires,
            "comment_text_allowed": False if requires else True,
            "primary_reason": "safety_boundary" if requires else "",
            "reason_codes": list(self.reason_codes or []),
            "normalized_safety_boundaries": ["safety_boundary"] if requires else [],
            "safety_boundaries": ["safety_boundary"] if requires else [],
            "boundary_types": list(self.boundary_types or []),
            "evidence_span_ids": list(self.evidence_span_ids or []),
            "evidence_span_count": int(self.evidence_span_count or len(self.evidence_span_ids or [])),
            "source_fields": list(self.source_fields or []),
            "graph_boundary_count": int(self.graph_boundary_count or 0),
            "boundary_count": int(max(self.graph_boundary_count or 0, self.evidence_span_count or 0, 1 if requires else 0)),
            "boundary_sources": list(self.boundary_sources or []),
            "safety_pre_generation_block": {
                "version": "emlis.safety_pre_generation_block.v1",
                "target_step": "Step10_safety_boundary",
                "phase": "B-S1",
                "blocked_before_composer": requires,
                "composer_generation_allowed": not requires,
                "comment_text_allowed": False if requires else True,
                "fixed_reply_allowed": False,
                "fallback_observation_allowed": False,
                "normal_observation_allowed": not requires,
                "user_facing_text_allowed": not requires,
                "raw_user_text_included": False,
                "primary_reason": "safety_boundary" if requires else "",
            },
            "raw_user_text_included": False,
            "policy": "fail_closed_before_composer",
        }


def build_emlis_safety_boundary_decision(
    *,
    graph: ObservationGraph | None = None,
    evidence_spans: Sequence[EvidenceSpan] | None = None,
) -> EmlisSafetyBoundaryDecision:
    graph_values = list(getattr(graph, "safety_boundaries", []) or []) if graph is not None else []
    graph_codes = normalize_safety_boundary_codes(graph_values)
    boundary_types: List[str] = []
    source_fields: List[str] = []
    span_ids: List[str] = []
    boundary_sources: List[str] = []
    if graph_codes:
        boundary_sources.append("observation_graph.safety_boundaries")
    for span in _text_evidence_spans(evidence_spans):
        raw_text = _clean(getattr(span, "raw_text", ""))
        detected_type = _clean(getattr(span, "detected_type", ""))
        types = classify_safety_boundary_text(raw_text)
        if detected_type == "safety_risk" and not types:
            types = ["safety_risk"]
        if not types:
            continue
        span_ids.append(_clean(getattr(span, "span_id", "")))
        source_fields.append(_clean(getattr(span, "source_field", "")))
        boundary_types.extend(types)
        boundary_sources.append("evidence_ledger.detected_type.safety_risk" if detected_type == "safety_risk" else "evidence_text.safety_pattern")
    requires = bool(graph_codes or span_ids)
    return EmlisSafetyBoundaryDecision(
        requires_block=requires,
        reason_codes=["safety_boundary"] if requires else [],
        boundary_types=_dedupe(boundary_types),
        evidence_span_ids=_dedupe(span_ids),
        source_fields=_dedupe(source_fields),
        graph_boundary_count=len(graph_codes),
        evidence_span_count=len(_dedupe(span_ids)),
        boundary_sources=_dedupe(boundary_sources),
    )


def build_emlis_safety_boundary_report(
    *,
    graph: ObservationGraph | None = None,
    evidence_spans: Sequence[EvidenceSpan] | None = None,
) -> SafetyBoundaryReport:
    decision = build_emlis_safety_boundary_decision(graph=graph, evidence_spans=evidence_spans)
    meta = decision.as_meta()
    requires = bool(meta.get("requires_block"))
    return SafetyBoundaryReport(
        requires_block=requires,
        reasons=["safety_boundary"] if requires else [],
        boundary_count=int(meta.get("boundary_count") or 0),
        boundary_kinds=list(meta.get("boundary_types") or []),
        source_span_ids=list(meta.get("evidence_span_ids") or []),
        source_fields=list(meta.get("source_fields") or []),
        policy_version=_POLICY_VERSION,
        blocks_before_composer=requires,
        normal_observation_allowed=not requires,
        user_facing_text_allowed=not requires,
    )


__all__ = [
    "EmlisSafetyBoundaryDecision",
    "build_emlis_safety_boundary_decision",
    "build_emlis_safety_boundary_report",
    "classify_safety_boundary_text",
    "normalize_safety_boundary_codes",
]
