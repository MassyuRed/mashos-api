# -*- coding: utf-8 -*-
from __future__ import annotations

"""Evidence conversion helpers for the Cocolon text generation core.

Phase 3 keeps this layer additive.  It converts source-bound evidence into the
core-agnostic ``SourceAnchor`` / ``EvidenceSpanLike`` shapes without changing
EmlisAI runtime files, public API routes, response keys, or database names.
"""

from dataclasses import dataclass, field
import hashlib
import re
from typing import Any, Iterable, Mapping, Tuple

from .policies import REJECTION_EVIDENCE_MISSING, compact_tokens
from .types import EvidenceSpanLike, SourceAnchor

_SPACE_RE = re.compile(r"\s+")
_PUNCT_TRIM = " \t\r\n　、,。.!！?？『』\"'"

REJECTION_SOURCE_ID_MISSING = "source_id_missing"
REJECTION_SOURCE_FIELD_MISSING = "source_field_missing"
REJECTION_SPAN_ID_MISSING = "span_id_missing"
REJECTION_RAW_TEXT_MISSING = "raw_text_missing"
HASH_ALGORITHM = "sha256.source_id_field_span_offsets_raw_text.v1"


def clean_evidence_text(value: object) -> str:
    """Normalize source evidence text without completing or rephrasing it."""

    return _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ").replace("\r", " ").replace("\n", " ")).strip(_PUNCT_TRIM)


def clean_evidence_token(value: object) -> str:
    return str(value or "").strip()


def _json_safe_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    out: dict[str, Any] = {}
    for key, item in value.items():
        key_text = clean_evidence_token(key)
        if not key_text:
            continue
        if isinstance(item, (str, int, float, bool)) or item is None:
            out[key_text] = item
        elif isinstance(item, (list, tuple)):
            out[key_text] = [v if isinstance(v, (str, int, float, bool)) or v is None else str(v) for v in item]
        elif isinstance(item, Mapping):
            out[key_text] = _json_safe_mapping(item)
        else:
            out[key_text] = str(item)
    return out


def stable_evidence_hash(
    *,
    source_id: object,
    field_name: object,
    raw_text: object,
    span_id: object = "",
    start_index: object = "",
    end_index: object = "",
) -> str:
    """Return a deterministic hash for one source-bound evidence span.

    The hash includes the source identity, source field, span id, offsets when
    present, and normalized raw text.  Empty raw text intentionally returns an
    empty hash so the source cannot become a body-generation candidate.
    """

    cleaned_raw = clean_evidence_text(raw_text)
    if not cleaned_raw:
        return ""
    parts = (
        clean_evidence_token(source_id),
        clean_evidence_token(field_name),
        clean_evidence_token(span_id),
        clean_evidence_token(start_index),
        clean_evidence_token(end_index),
        cleaned_raw,
    )
    material = "\u241f".join(part for part in parts if part)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def stable_source_hash(*, source_id: object, field: object = "", field_name: object = "", raw_text: object) -> str:
    """Compatibility helper for callers that do not have span offsets yet."""

    return stable_evidence_hash(source_id=source_id, field_name=field_name or field, raw_text=raw_text)


def evidence_rejection_reasons(
    *,
    source_id: object,
    field_name: object,
    span_id: object,
    raw_text: object,
) -> Tuple[str, ...]:
    """Return fail-closed reasons for unusable source evidence."""

    reasons: list[str] = []
    if not clean_evidence_token(source_id):
        reasons.append(REJECTION_SOURCE_ID_MISSING)
    if not clean_evidence_token(field_name):
        reasons.append(REJECTION_SOURCE_FIELD_MISSING)
    if not clean_evidence_token(span_id):
        reasons.append(REJECTION_SPAN_ID_MISSING)
    if not clean_evidence_text(raw_text):
        reasons.append(REJECTION_RAW_TEXT_MISSING)
    return tuple(reasons)


def make_source_anchor(
    *,
    source_id: object,
    field_name: object = "",
    field: object = "",
    raw_text: object,
    span_id: object = "",
    start_index: object = "",
    end_index: object = "",
    source_hash: object = "",
    meta: Mapping[str, Any] | None = None,
) -> SourceAnchor:
    """Build a SourceAnchor while preserving source id, field, text and hash."""

    cleaned_source_id = clean_evidence_token(source_id) or "unknown_source"
    cleaned_field = clean_evidence_token(field_name or field) or "unknown_field"
    cleaned_raw = clean_evidence_text(raw_text)
    cleaned_hash = clean_evidence_token(source_hash) or stable_evidence_hash(
        source_id=cleaned_source_id,
        field_name=cleaned_field,
        span_id=span_id,
        start_index=start_index,
        end_index=end_index,
        raw_text=cleaned_raw,
    )
    anchor_meta = _json_safe_mapping(meta)
    anchor_meta.setdefault("hash_algorithm", HASH_ALGORITHM)
    if span_id:
        anchor_meta.setdefault("original_span_id", clean_evidence_token(span_id))
    if cleaned_field:
        anchor_meta.setdefault("source_field", cleaned_field)
    return SourceAnchor(
        source_id=cleaned_source_id,
        field=cleaned_field,
        raw_text=cleaned_raw,
        source_hash=cleaned_hash,
        meta=anchor_meta,
    )


def build_source_anchor(**kwargs: Any) -> SourceAnchor:
    """Alias kept for the Phase 2 naming style."""

    return make_source_anchor(**kwargs)


def make_evidence_span_like(
    *,
    span_id: object,
    source_id: object,
    field_name: object = "",
    field: object = "",
    raw_text: object,
    role: object = "",
    start_index: object = "",
    end_index: object = "",
    source_hash: object = "",
    meta: Mapping[str, Any] | None = None,
) -> EvidenceSpanLike:
    """Build an EvidenceSpanLike from source-bound data.

    Empty raw text is not repaired or inferred.  The resulting object remains
    unusable and can be filtered before body composition.
    """

    cleaned_field = clean_evidence_token(field_name or field)
    cleaned_span_id = clean_evidence_token(span_id)
    cleaned_meta = _json_safe_mapping(meta)
    cleaned_meta.setdefault("original_span_id", cleaned_span_id)
    cleaned_meta.setdefault("source_field", cleaned_field)
    if start_index != "":
        cleaned_meta.setdefault("start_index", start_index)
    if end_index != "":
        cleaned_meta.setdefault("end_index", end_index)
    anchor = make_source_anchor(
        source_id=source_id,
        field_name=cleaned_field,
        raw_text=raw_text,
        span_id=cleaned_span_id,
        start_index=start_index,
        end_index=end_index,
        source_hash=source_hash,
        meta=cleaned_meta,
    )
    return EvidenceSpanLike(
        span_id=cleaned_span_id,
        source_anchor=anchor,
        raw_text=clean_evidence_text(raw_text),
        role=clean_evidence_token(role),
        meta=cleaned_meta,
    )


def build_evidence_span_like(**kwargs: Any) -> EvidenceSpanLike:
    """Alias kept for the Phase 2 naming style."""

    return make_evidence_span_like(**kwargs)


def usable_evidence_spans(spans: Iterable[EvidenceSpanLike] | None) -> Tuple[EvidenceSpanLike, ...]:
    """Return only spans safe to use as body-generation evidence."""

    return tuple(span for span in spans or () if getattr(span, "usable", False))


def source_anchors_for_evidence(spans: Iterable[EvidenceSpanLike] | None) -> Tuple[SourceAnchor, ...]:
    """Return unique SourceAnchor objects from usable evidence spans."""

    anchors: list[SourceAnchor] = []
    seen: set[tuple[str, str, str]] = set()
    for span in usable_evidence_spans(spans):
        anchor = span.source_anchor
        key = (anchor.source_id, anchor.field, anchor.source_hash)
        if key in seen:
            continue
        seen.add(key)
        anchors.append(anchor)
    return tuple(anchors)


def evidence_spans_by_id(spans: Iterable[EvidenceSpanLike] | None) -> dict[str, EvidenceSpanLike]:
    """Index usable evidence spans by span_id, keeping the first occurrence."""

    out: dict[str, EvidenceSpanLike] = {}
    for span in usable_evidence_spans(spans):
        if span.span_id and span.span_id not in out:
            out[span.span_id] = span
    return out


@dataclass(frozen=True)
class EvidenceConversionResult:
    """Additive adapter result shared by core-specific evidence adapters."""

    adapter_name: str = ""
    evidence_spans: Iterable[EvidenceSpanLike] = field(default_factory=tuple)
    source_anchors: Iterable[SourceAnchor] = field(default_factory=tuple)
    skipped_span_ids: Iterable[str] = field(default_factory=tuple)
    rejection_reasons: Iterable[str] = field(default_factory=tuple)
    meta: Mapping[str, Any] = field(default_factory=dict)
    core_id: str = ""

    def __post_init__(self) -> None:
        evidence_spans = usable_evidence_spans(self.evidence_spans)
        source_anchors = tuple(self.source_anchors or ()) or source_anchors_for_evidence(evidence_spans)
        object.__setattr__(self, "adapter_name", clean_evidence_token(self.adapter_name))
        object.__setattr__(self, "core_id", clean_evidence_token(self.core_id))
        object.__setattr__(self, "evidence_spans", evidence_spans)
        object.__setattr__(self, "source_anchors", source_anchors)
        object.__setattr__(self, "skipped_span_ids", compact_tokens(self.skipped_span_ids))
        reasons = list(compact_tokens(self.rejection_reasons))
        if not evidence_spans and REJECTION_EVIDENCE_MISSING not in reasons:
            reasons.append(REJECTION_EVIDENCE_MISSING)
        object.__setattr__(self, "rejection_reasons", tuple(dict.fromkeys(reasons)))
        object.__setattr__(self, "meta", _json_safe_mapping(self.meta))

    @property
    def usable_evidence_spans(self) -> Tuple[EvidenceSpanLike, ...]:
        return tuple(self.evidence_spans)

    @property
    def has_usable_evidence(self) -> bool:
        return bool(self.evidence_spans)

    @property
    def usable(self) -> bool:
        return self.has_usable_evidence

    def as_meta(self) -> dict[str, Any]:
        return {
            "adapter_name": self.adapter_name,
            "core_id": self.core_id,
            "source_anchors": [anchor.as_meta() for anchor in self.source_anchors],
            "evidence_spans": [span.as_meta() for span in self.evidence_spans],
            "skipped_span_ids": list(self.skipped_span_ids),
            "rejection_reasons": list(self.rejection_reasons),
            "meta": dict(self.meta),
        }


EvidenceAdapterResult = EvidenceConversionResult


def empty_evidence_adapter_result(
    *,
    core_id: object = "",
    adapter_name: object = "",
    reason: object,
    meta: Mapping[str, Any] | None = None,
) -> EvidenceConversionResult:
    """Return a fail-closed adapter skeleton result for not-yet-connected cores."""

    return EvidenceConversionResult(
        adapter_name=clean_evidence_token(adapter_name),
        core_id=clean_evidence_token(core_id),
        evidence_spans=(),
        source_anchors=(),
        skipped_span_ids=(),
        rejection_reasons=(clean_evidence_token(reason) or REJECTION_EVIDENCE_MISSING,),
        meta=meta or {},
    )


__all__ = [
    "EvidenceAdapterResult",
    "EvidenceConversionResult",
    "HASH_ALGORITHM",
    "REJECTION_RAW_TEXT_MISSING",
    "REJECTION_SOURCE_FIELD_MISSING",
    "REJECTION_SOURCE_ID_MISSING",
    "REJECTION_SPAN_ID_MISSING",
    "build_evidence_span_like",
    "build_source_anchor",
    "clean_evidence_text",
    "clean_evidence_token",
    "empty_evidence_adapter_result",
    "evidence_rejection_reasons",
    "evidence_spans_by_id",
    "make_evidence_span_like",
    "make_source_anchor",
    "source_anchors_for_evidence",
    "stable_evidence_hash",
    "stable_source_hash",
    "usable_evidence_spans",
]
