# -*- coding: utf-8 -*-
from __future__ import annotations

import json

from cocolon_text_generation_core.adapters.analysis_evidence_adapter import convert_analysis_evidence_spans
from cocolon_text_generation_core.adapters.emlis_evidence_adapter import convert_emlis_evidence_spans
from cocolon_text_generation_core.adapters.piece_evidence_adapter import convert_piece_evidence_spans
from cocolon_text_generation_core.evidence import (
    REJECTION_RAW_TEXT_MISSING,
    evidence_spans_by_id,
    make_evidence_span_like,
    make_source_anchor,
    stable_evidence_hash,
    usable_evidence_spans,
)
from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_types import EvidenceSpan


def test_emlis_evidence_adapter_preserves_span_id_source_field_and_hash() -> None:
    ledger = build_evidence_ledger(
        {
            "id": "emotion-input-1",
            "memo": "友達と笑えて少し元気になった。でも帰宅後に一人になると不安が戻った。",
            "emotion_details": [{"type": "喜び"}, {"type": "不安"}],
        }
    )

    result = convert_emlis_evidence_spans(ledger, source_id="emotion-input-1")

    assert result.has_usable_evidence is True
    assert len(result.evidence_spans) == len(ledger)
    assert result.skipped_span_ids == ()

    first = result.evidence_spans[0]
    assert first.span_id == ledger[0].span_id
    assert first.source_anchor.source_id == "emotion-input-1"
    assert first.source_anchor.field == ledger[0].source_field
    assert first.raw_text
    assert first.source_anchor.source_hash
    assert first.source_anchor.meta["original_span_id"] == ledger[0].span_id
    assert first.source_anchor.meta["source_field"] == ledger[0].source_field

    json.dumps(result.as_meta(), ensure_ascii=False)


def test_emlis_evidence_adapter_skips_empty_raw_text_before_body_candidates() -> None:
    spans = [
        EvidenceSpan(span_id="s1", raw_text="", source_field="memo", detected_type="event"),
        EvidenceSpan(span_id="s2", raw_text="ちゃんと考えて話したのに", source_field="memo", detected_type="event"),
    ]

    result = convert_emlis_evidence_spans(spans, source_id="emotion-input-2")

    assert [span.span_id for span in result.evidence_spans] == ["s2"]
    assert result.skipped_span_ids == ("s1",)
    assert REJECTION_RAW_TEXT_MISSING in result.rejection_reasons
    assert all(span.raw_text for span in result.usable_evidence_spans)


def test_emlis_evidence_hash_is_stable_for_same_source_span() -> None:
    span = EvidenceSpan(
        span_id="s7",
        raw_text="普通に生活したい気持ちと悪化する怖さがある",
        source_field="memo",
        start_index=10,
        end_index=35,
        detected_type="wish",
    )

    first = convert_emlis_evidence_spans([span], source_id="emotion-input-7").evidence_spans[0]
    second = convert_emlis_evidence_spans([span], source_id="emotion-input-7").evidence_spans[0]

    assert first.source_anchor.source_hash == second.source_anchor.source_hash
    assert first.source_anchor.source_hash == stable_evidence_hash(
        source_id="emotion-input-7",
        field_name="memo",
        span_id="s7",
        start_index=10,
        end_index=35,
        raw_text="普通に生活したい気持ちと悪化する怖さがある",
    )


def test_source_anchor_and_evidence_helpers_filter_unusable_evidence() -> None:
    anchor = make_source_anchor(source_id="input-1", field_name="memo", span_id="s1", raw_text="  頼りたいけど怖い。 ")
    usable = make_evidence_span_like(
        span_id="s1",
        source_id="input-1",
        field_name="memo",
        raw_text="頼りたいけど怖い",
        role="fear",
    )
    empty = make_evidence_span_like(span_id="s2", source_id="input-1", field_name="memo", raw_text=" ")

    assert anchor.field == "memo"
    assert anchor.raw_text == "頼りたいけど怖い"
    assert len(anchor.source_hash) == 64
    assert usable.usable is True
    assert empty.usable is False
    assert usable_evidence_spans((usable, empty)) == (usable,)
    assert evidence_spans_by_id((usable, empty)) == {"s1": usable}


def test_piece_and_analysis_adapters_are_skeleton_only_in_phase3() -> None:
    piece = convert_piece_evidence_spans([])
    analysis = convert_analysis_evidence_spans([])

    assert piece.has_usable_evidence is False
    assert analysis.has_usable_evidence is False
    assert piece.adapter_name == "piece_evidence_adapter.skeleton.v0"
    assert analysis.adapter_name == "analysis_evidence_adapter.skeleton.v0"
    assert "piece_evidence_adapter_not_connected" in piece.rejection_reasons
    assert "analysis_evidence_adapter_not_connected" in analysis.rejection_reasons
