# -*- coding: utf-8 -*-
from __future__ import annotations

from emlis_ai_safety_boundary_service import (
    build_emlis_safety_boundary_decision,
    normalize_safety_boundary_codes,
)
from emlis_ai_types import EvidenceSpan, GraphClaim, ObservationGraph


def _graph(boundaries=None):
    return ObservationGraph(
        primary_state=GraphClaim(
            claim_id="p1",
            claim_type="primary_state",
            text="",
            evidence_span_ids=[],
            confidence=0.0,
        ),
        safety_boundaries=list(boundaries or []),
    )


def test_normalize_safety_boundary_codes_collapses_to_stable_code():
    assert normalize_safety_boundary_codes(["死にたい気持ちが強い"]) == ["safety_boundary"]
    assert normalize_safety_boundary_codes([]) == []


def test_safety_boundary_decision_detects_graph_boundary_without_raw_text():
    decision = build_emlis_safety_boundary_decision(graph=_graph(["safety_boundary"]), evidence_spans=[])
    meta = decision.as_meta()
    assert meta["requires_block"] is True
    assert meta["safety_boundaries"] == ["safety_boundary"]
    assert meta["raw_user_text_included"] is False
    assert meta["safety_pre_generation_block"]["composer_generation_allowed"] is False


def test_safety_boundary_decision_detects_evidence_boundary_without_raw_text():
    spans = [
        EvidenceSpan(
            span_id="memo.1",
            raw_text="生きていたくない。",
            detected_type="event",
            source_field="memo",
        )
    ]
    decision = build_emlis_safety_boundary_decision(graph=_graph(), evidence_spans=spans)
    meta = decision.as_meta()
    assert meta["requires_block"] is True
    assert meta["evidence_span_ids"] == ["memo.1"]
    assert "self_harm" in meta["boundary_types"]
    assert "生きて" not in str(meta)
