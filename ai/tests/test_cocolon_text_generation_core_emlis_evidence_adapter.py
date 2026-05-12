# -*- coding: utf-8 -*-
from __future__ import annotations

import json

from cocolon_text_generation_core.adapters import (
    adapt_analysis_evidence_sources,
    adapt_emlis_evidence_span,
    adapt_emlis_evidence_spans,
    adapt_piece_evidence_sources,
)
from cocolon_text_generation_core.policies import CORE_ID_ANALYSIS, CORE_ID_EMLIS, CORE_ID_PIECE
from emlis_ai_types import EvidenceSpan


def _span(
    span_id: str = "s7",
    raw_text: str = "頼りたいけど、迷惑と思われそうで怖い",
    detected_type: str = "fear",
    source_field: str = "memo",
) -> EvidenceSpan:
    return EvidenceSpan(
        span_id=span_id,
        raw_text=raw_text,
        start_index=3,
        end_index=25,
        detected_type=detected_type,
        confidence=0.86,
        source_field=source_field,
    )


def test_adapt_emlis_evidence_span_preserves_required_fields() -> None:
    adapted = adapt_emlis_evidence_span(_span(), current_input={"id": "input-123"})

    assert adapted is not None
    assert adapted.span_id == "s7"
    assert adapted.raw_text == "頼りたいけど、迷惑と思われそうで怖い"
    assert adapted.role == "fear"
    assert adapted.source_anchor.source_id == "input-123"
    assert adapted.source_anchor.field == "memo"
    assert adapted.source_anchor.raw_text == adapted.raw_text
    assert len(adapted.source_anchor.source_hash) == 64
    assert adapted.meta["original_span_id"] == "s7"
    assert adapted.meta["source_field"] == "memo"
    assert adapted.meta["start_index"] == 3
    json.dumps(adapted.as_meta(), ensure_ascii=False)


def test_adapt_emlis_evidence_spans_skips_empty_raw_text() -> None:
    good = _span(span_id="s1", raw_text="家にいると休める", detected_type="value")
    empty = _span(span_id="s2", raw_text="   ", detected_type="event")

    result = adapt_emlis_evidence_spans((good, empty), source_id="input-1")

    assert result.core_id == CORE_ID_EMLIS
    assert result.usable is True
    assert [span.span_id for span in result.evidence_spans] == ["s1"]
    assert result.skipped_span_ids == ("s2",)
    assert "s2" not in [span.span_id for span in result.evidence_spans]


def test_piece_and_analysis_adapter_aliases_are_fail_closed_skeletons() -> None:
    piece = adapt_piece_evidence_sources()
    analysis = adapt_analysis_evidence_sources()

    assert piece.core_id == CORE_ID_PIECE
    assert analysis.core_id == CORE_ID_ANALYSIS
    assert piece.usable is False
    assert analysis.usable is False
    assert "piece_evidence_adapter_not_connected" in piece.rejection_reasons
    assert "analysis_evidence_adapter_not_connected" in analysis.rejection_reasons
