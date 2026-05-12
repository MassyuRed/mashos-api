# -*- coding: utf-8 -*-
from __future__ import annotations

"""Adapter from EmlisAI EvidenceSpan to common evidence types.

This file is additive.  EmlisAI Phase8 continues to use its current runtime
``EvidenceSpan`` objects; this adapter only prepares common evidence shapes for
later CocolonTextGenerationCore connection phases.
"""

from typing import Any, Iterable, Mapping

from cocolon_text_generation_core.evidence import (
    EvidenceConversionResult,
    REJECTION_RAW_TEXT_MISSING,
    REJECTION_SPAN_ID_MISSING,
    clean_evidence_text,
    clean_evidence_token,
    evidence_rejection_reasons,
    make_evidence_span_like,
    source_anchors_for_evidence,
)
from cocolon_text_generation_core.policies import CORE_ID_EMLIS
from cocolon_text_generation_core.types import EvidenceSpanLike

ADAPTER_NAME = "emlis_evidence_adapter.v1"


def _mapping_get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


def _current_input_source_id(current_input: Mapping[str, Any] | None) -> str:
    if not isinstance(current_input, Mapping):
        return ""
    for key in ("id", "input_id", "emotion_id", "submission_id"):
        value = clean_evidence_token(current_input.get(key))
        if value:
            return value
    return ""


def _source_id_for(source_id: object = "", current_input: Mapping[str, Any] | None = None) -> str:
    return clean_evidence_token(source_id) or _current_input_source_id(current_input) or "current_input"


def _span_meta(span: Any) -> dict[str, Any]:
    return {
        "source_kind": "emlis_ai_evidence_span",
        "original_span_id": clean_evidence_token(_mapping_get(span, "span_id", "")),
        "source_field": clean_evidence_token(_mapping_get(span, "source_field", "")),
        "detected_type": clean_evidence_token(_mapping_get(span, "detected_type", "")),
        "start_index": _mapping_get(span, "start_index", None),
        "end_index": _mapping_get(span, "end_index", None),
        "confidence": _mapping_get(span, "confidence", None),
    }


def convert_emlis_evidence_span(
    span: Any,
    *,
    source_id: object = "",
    current_input: Mapping[str, Any] | None = None,
) -> EvidenceSpanLike | None:
    """Convert one Emlis ``EvidenceSpan`` into ``EvidenceSpanLike``.

    ``span_id`` is preserved.  Empty ``raw_text`` is returned as ``None`` so it
    cannot become a body candidate in the common text-generation core.
    """

    resolved_source_id = _source_id_for(source_id, current_input)
    span_id = clean_evidence_token(_mapping_get(span, "span_id", ""))
    field_name = clean_evidence_token(_mapping_get(span, "source_field", "")) or "current_input"
    raw_text = clean_evidence_text(_mapping_get(span, "raw_text", ""))
    reasons = evidence_rejection_reasons(
        source_id=resolved_source_id,
        field_name=field_name,
        span_id=span_id,
        raw_text=raw_text,
    )
    if REJECTION_RAW_TEXT_MISSING in reasons or REJECTION_SPAN_ID_MISSING in reasons:
        return None
    return make_evidence_span_like(
        span_id=span_id,
        source_id=resolved_source_id,
        field_name=field_name,
        raw_text=raw_text,
        role=clean_evidence_token(_mapping_get(span, "detected_type", "")),
        start_index=_mapping_get(span, "start_index", ""),
        end_index=_mapping_get(span, "end_index", ""),
        meta=_span_meta(span),
    )


def adapt_emlis_evidence_span(
    span: Any,
    *,
    source_id: object = "",
    current_input: Mapping[str, Any] | None = None,
) -> EvidenceSpanLike | None:
    """Alias for naming consistency with later adapter phases."""

    return convert_emlis_evidence_span(span, source_id=source_id, current_input=current_input)


def convert_emlis_evidence_spans(
    spans: Iterable[Any] | None,
    *,
    source_id: object = "",
    current_input: Mapping[str, Any] | None = None,
) -> EvidenceConversionResult:
    """Convert Emlis evidence spans into the common conversion result."""

    span_list = tuple(spans or ())
    resolved_source_id = _source_id_for(source_id, current_input)
    converted: list[EvidenceSpanLike] = []
    skipped: list[str] = []
    rejection_reasons: list[str] = []

    for index, span in enumerate(span_list, start=1):
        span_id = clean_evidence_token(_mapping_get(span, "span_id", ""))
        field_name = clean_evidence_token(_mapping_get(span, "source_field", "")) or "current_input"
        raw_text = clean_evidence_text(_mapping_get(span, "raw_text", ""))
        reasons = evidence_rejection_reasons(
            source_id=resolved_source_id,
            field_name=field_name,
            span_id=span_id,
            raw_text=raw_text,
        )
        if reasons:
            rejection_reasons.extend(reasons)
        adapted = convert_emlis_evidence_span(span, source_id=resolved_source_id)
        if adapted is None:
            skipped.append(span_id or f"index:{index}")
            continue
        converted.append(adapted)

    return EvidenceConversionResult(
        adapter_name=ADAPTER_NAME,
        core_id=CORE_ID_EMLIS,
        evidence_spans=tuple(converted),
        source_anchors=source_anchors_for_evidence(converted),
        skipped_span_ids=tuple(skipped),
        rejection_reasons=tuple(rejection_reasons),
        meta={
            "source_core": CORE_ID_EMLIS,
            "source_id": resolved_source_id,
            "input_span_count": len(span_list),
        },
    )


def adapt_emlis_evidence_spans(
    spans: Iterable[Any] | None,
    *,
    source_id: object = "",
    current_input: Mapping[str, Any] | None = None,
) -> EvidenceConversionResult:
    """Alias for naming consistency with later adapter phases."""

    return convert_emlis_evidence_spans(spans, source_id=source_id, current_input=current_input)


__all__ = [
    "ADAPTER_NAME",
    "adapt_emlis_evidence_span",
    "adapt_emlis_evidence_spans",
    "convert_emlis_evidence_span",
    "convert_emlis_evidence_spans",
]
