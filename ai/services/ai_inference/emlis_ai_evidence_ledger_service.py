# -*- coding: utf-8 -*-
from __future__ import annotations

"""Evidence Ledger for EmlisAI multi-perspective observation.

Phase 3 owns only source grounding.  It extracts spans from ``current_input``
and keeps their source field and source offsets so later layers can return to
what the user actually wrote.  It must not create observation text, companion
phrases, strengths, wishes, or any other interpretation.
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

from emlis_ai_types import EvidenceSpan
from emlis_ai_current_input_bundle import normalize_emlis_current_input

_SPACE_RE = re.compile(r"\s+")
_TEXT_BOUNDARY_RE = re.compile(r"[\n\r。.!！?？；;]+")
_SOFT_BOUNDARY_RE = re.compile(r"[、,]")
_RELATION_PREFIX_RE = re.compile(r"^(でも|だけど|けど|ただ|とはいえ|その中で|一方)(?=.+)")

_SELF_AWARENESS_RE = re.compile(r"(分かって|わかって|分かる|分かっ|自分でも|ちゃんと見|理解して|気づいて)")
_LIMIT_RE = re.compile(r"(逃げ出|投げ出|もう無理|限界|休みたい|疲れ|しんど|苦し|分からな|わからな|泣き|ボロボロ|崩れ|気が抜け|抱えるのも限界|面倒にな)")
_WISH_RE = re.compile(r"(したい|(?<!み)いたい|ありたい|欲しい|ほしい|願い|普通に生活|楽しみたい|繋がっていたい|つながっていたい|過ごしたい|優先したい|整え|頼りたい)")
_CONSTRAINT_RE = re.compile(r"(気をつけ|気を付け|不便|悪化|できない|出来ない|制約|我慢|無視|責め|ミス|怖|こわ|圧|来られる|追いつ|迷惑|嫌われ|重い|言えない)")
_FEAR_RE = re.compile(r"(怖|こわ|不安|心配|ダメージ|責め|ミス|迷惑|嫌われ|重い|大事に扱われなかった)")
_VALUE_RE = re.compile(r"(嬉し|うれし|リラックス|楽し|笑え|元気|片付け|気持ちが軽い|ちゃんとでき|大切|好き|整え|守り|安心|休ま|家のこと|優先|幸せ|役に立)")
_RELATION_RE = re.compile(r"(でも|だけど|けど|一方|同時に|その中で|ただ|なのに|からこそ|だからこそ|とはいえ)")
_EMOTION_WORD_RE = re.compile(r"(喜び|悲しみ|怒り|不安|平穏|自己理解|恐れ|焦り|寂し|さびし|嬉し|怖|こわ|しんど|苦し)")
_SAFETY_RISK_RE = re.compile(r"(死にたい|消えたい|自殺|自傷|自分を傷つけたい|殺したい|OD|過量服薬|首を吊|首吊|飛び降り|リスカ|生きていたくない|生きるのをやめたい)", re.IGNORECASE)

_STRUCTURED_TEXT_FIELDS: Tuple[str, ...] = ("memo", "memo_action")
_STRUCTURED_LIST_FIELDS: Tuple[str, ...] = ("emotion_details", "emotions", "category")
_CANONICAL_SPAN_ID_RE = re.compile(r"^s[1-9]\d*$")


@dataclass(frozen=True)
class EvidenceLedgerValidationReport:
    """Body-free validation result for the request-local Evidence Ledger.

    The report exposes identifiers and issue codes only. It deliberately does
    not copy ``raw_text`` or source slices into metadata.
    """

    valid: bool
    issue_codes: Tuple[str, ...] = ()
    canonical_span_ids: Tuple[str, ...] = ()
    duplicate_span_ids: Tuple[str, ...] = ()
    noncanonical_span_ids: Tuple[str, ...] = ()
    invalid_offset_span_ids: Tuple[str, ...] = ()
    source_mismatch_span_ids: Tuple[str, ...] = ()
    unknown_source_field_span_ids: Tuple[str, ...] = ()

    def as_body_free_meta(self) -> Dict[str, Any]:
        return {
            "valid": bool(self.valid),
            "issue_codes": list(self.issue_codes),
            "canonical_span_ids": list(self.canonical_span_ids),
            "duplicate_span_ids": list(self.duplicate_span_ids),
            "noncanonical_span_ids": list(self.noncanonical_span_ids),
            "invalid_offset_span_ids": list(self.invalid_offset_span_ids),
            "source_mismatch_span_ids": list(self.source_mismatch_span_ids),
            "unknown_source_field_span_ids": list(self.unknown_source_field_span_ids),
            "raw_user_text_included": False,
        }


class EvidenceLedgerResolutionError(ValueError):
    """Raised when a canonical plan references an invalid Evidence Ledger."""


class EvidenceSpanResolver:
    """Resolve existing request-local ``sN`` ids without creating new ids.

    The resolver is read-only. It owns no fallback id generator and therefore
    cannot manufacture evidence for a downstream sentence or plan.
    """

    def __init__(self, evidence_spans: Sequence[EvidenceSpan]) -> None:
        spans = tuple(evidence_spans or ())
        report = validate_evidence_ledger(spans)
        if not report.valid:
            raise EvidenceLedgerResolutionError(
                "invalid_evidence_ledger:" + ",".join(report.issue_codes)
            )
        self._spans: Tuple[EvidenceSpan, ...] = spans
        self._index: Dict[str, EvidenceSpan] = {span.span_id: span for span in spans}

    @property
    def span_ids(self) -> Tuple[str, ...]:
        return tuple(span.span_id for span in self._spans)

    def contains(self, span_id: Any) -> bool:
        return str(span_id or "").strip() in self._index

    def resolve(self, span_id: Any) -> EvidenceSpan:
        key = str(span_id or "").strip()
        span = self._index.get(key)
        if span is None:
            raise EvidenceLedgerResolutionError(f"unresolved_evidence_span_id:{key or '<empty>'}")
        return span

    def resolve_many(self, span_ids: Sequence[Any]) -> Tuple[EvidenceSpan, ...]:
        return tuple(self.resolve(span_id) for span_id in span_ids or ())

    def unresolved_ids(self, span_ids: Sequence[Any]) -> Tuple[str, ...]:
        out: List[str] = []
        for value in span_ids or ():
            key = str(value or "").strip()
            if key not in self._index and key not in out:
                out.append(key)
        return tuple(out)

    def source_fields_for(self, span_ids: Sequence[Any]) -> Tuple[str, ...]:
        fields: List[str] = []
        for span in self.resolve_many(span_ids):
            field = str(span.source_field or "").strip()
            if field and field not in fields:
                fields.append(field)
        return tuple(fields)


@dataclass(frozen=True)
class _RawSpan:
    text: str
    start: int
    end: int


def _clean_text(value: Any) -> str:
    return _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ")).strip()


def _trim_with_offsets(source: str, start: int, end: int) -> _RawSpan | None:
    """Trim whitespace/punctuation without losing exact source offsets."""

    while start < end and source[start] in " \t\r\n\u3000、,。.!！?？；;":
        start += 1
    while end > start and source[end - 1] in " \t\r\n\u3000、,。.!！?？；;":
        end -= 1
    if start >= end:
        return None
    text = source[start:end]
    return _RawSpan(text=_SPACE_RE.sub(" ", text).strip(), start=start, end=end)


def _split_long_segment(source: str, start: int, end: int, *, max_len: int) -> List[_RawSpan]:
    span = _trim_with_offsets(source, start, end)
    if span is None:
        return []
    if len(span.text) <= max_len:
        return [span]

    parts: List[_RawSpan] = []
    cursor = span.start
    for match in _SOFT_BOUNDARY_RE.finditer(source, span.start, span.end):
        piece = _trim_with_offsets(source, cursor, match.start())
        if piece is not None:
            if len(piece.text) <= max_len:
                parts.append(piece)
            else:
                parts.extend(_cut_by_length(source, piece.start, piece.end, max_len=max_len))
        cursor = match.end()
    tail = _trim_with_offsets(source, cursor, span.end)
    if tail is not None:
        if len(tail.text) <= max_len:
            parts.append(tail)
        else:
            parts.extend(_cut_by_length(source, tail.start, tail.end, max_len=max_len))
    return parts or [span]


def _cut_by_length(source: str, start: int, end: int, *, max_len: int) -> List[_RawSpan]:
    parts: List[_RawSpan] = []
    cursor = start
    while cursor < end:
        piece_end = min(end, cursor + max_len)
        piece = _trim_with_offsets(source, cursor, piece_end)
        if piece is not None:
            parts.append(piece)
        cursor = piece_end
    return parts


def _split_relation_prefix(span: _RawSpan, source: str) -> List[_RawSpan]:
    """Keep explicit relation markers as their own source-backed spans.

    This preserves evidence for later relation graph construction without
    turning the surrounding clause into an interpretation.
    """

    match = _RELATION_PREFIX_RE.match(span.text)
    if not match or len(span.text) <= len(match.group(1)):
        return [span]
    marker_text = match.group(1)
    marker = _RawSpan(text=marker_text, start=span.start, end=span.start + len(marker_text))
    rest = _trim_with_offsets(source, marker.end, span.end)
    return [marker, rest] if rest is not None else [marker]


def _split_source_text(text: Any, *, max_len: int = 72) -> List[_RawSpan]:
    """Return source-backed spans from a text field.

    The returned ``text`` is always a slice from the source field after trimming.
    No phrases are completed, normalized into meanings, or rewritten.
    """

    source = str(text or "")
    if not source.strip():
        return []
    spans: List[_RawSpan] = []
    cursor = 0
    for match in _TEXT_BOUNDARY_RE.finditer(source):
        spans.extend(_split_long_segment(source, cursor, match.start(), max_len=max_len))
        cursor = match.end()
    spans.extend(_split_long_segment(source, cursor, len(source), max_len=max_len))
    expanded: List[_RawSpan] = []
    for span in spans:
        expanded.extend(_split_relation_prefix(span, source))
    return [span for span in expanded if span.text]


def _structured_strings(value: Any) -> Iterable[str]:
    if value is None:
        return []
    if isinstance(value, dict):
        candidates = [value.get("type"), value.get("name"), value.get("label"), value.get("value")]
        return [_clean_text(item) for item in candidates if _clean_text(item)]
    if isinstance(value, (list, tuple, set)):
        out: List[str] = []
        for item in value:
            out.extend(_structured_strings(item))
        return out
    cleaned = _clean_text(value)
    return [cleaned] if cleaned else []


def _selected_emotion_labels(current_input: Dict[str, Any]) -> List[str]:
    labels: List[str] = []
    for key in ("emotion_details", "emotions"):
        for value in _structured_strings(current_input.get(key)):
            if value and value not in labels:
                labels.append(value)
    return labels


def _detect_type(text: str, selected_emotions: Sequence[str]) -> str:
    """Classify span type without adding semantic interpretation."""

    value = str(text or "")
    if _SAFETY_RISK_RE.search(value):
        return "safety_risk"
    if _SELF_AWARENESS_RE.search(value):
        return "self_awareness"
    if _LIMIT_RE.search(value):
        return "limit_signal"
    if _FEAR_RE.search(value):
        return "fear"
    if _CONSTRAINT_RE.search(value):
        return "constraint"
    if _WISH_RE.search(value):
        return "wish"
    if _VALUE_RE.search(value):
        return "value"
    if any(label and label in value for label in selected_emotions) or _EMOTION_WORD_RE.search(value):
        return "emotion"
    if _RELATION_RE.search(value):
        return "relation_marker"
    return "event"


def _confidence_for_type(detected_type: str, *, structured: bool = False) -> float:
    if structured:
        return 1.0 if detected_type == "emotion" else 0.78
    if detected_type == "event":
        return 0.72
    if detected_type == "relation_marker":
        return 0.74
    return 0.86


def build_evidence_ledger(current_input: Dict[str, Any] | None) -> List[EvidenceSpan]:
    """Build EvidenceSpan rows from ``current_input`` only.

    The ledger intentionally returns no user-facing text and no claims.  Later
    layers may use ``detected_type`` as a routing hint, but the raw text itself
    remains the source of truth.
    """

    data: Dict[str, Any] = normalize_emlis_current_input(current_input) if current_input is not None else {}
    selected_emotions = _selected_emotion_labels(data)
    spans: List[EvidenceSpan] = []

    def add_text_field(field: str) -> None:
        for raw in _split_source_text(data.get(field)):
            detected = _detect_type(raw.text, selected_emotions)
            spans.append(
                EvidenceSpan(
                    span_id=f"s{len(spans) + 1}",
                    raw_text=raw.text,
                    start_index=raw.start,
                    end_index=raw.end,
                    detected_type=detected,
                    confidence=_confidence_for_type(detected),
                    source_field=field,
                )
            )

    for field in _STRUCTURED_TEXT_FIELDS:
        add_text_field(field)

    # Structured current_input fields do not have character offsets inside memo,
    # so they are explicitly marked with -1 while keeping their source field.
    for field in _STRUCTURED_LIST_FIELDS:
        for value in _structured_strings(data.get(field)):
            if field == "emotion_details" and any(span.raw_text == value and span.source_field == "emotions" for span in spans):
                continue
            detected = "emotion" if field in {"emotion_details", "emotions"} else _detect_type(value, selected_emotions)
            spans.append(
                EvidenceSpan(
                    span_id=f"s{len(spans) + 1}",
                    raw_text=value,
                    start_index=-1,
                    end_index=-1,
                    detected_type=detected,
                    confidence=_confidence_for_type(detected, structured=True),
                    source_field=field,
                )
            )

    # Keep stable ids even if duplicate labels appeared in multiple structured fields.
    unique: List[EvidenceSpan] = []
    seen = set()
    for span in spans:
        key = (span.source_field, span.raw_text, span.start_index, span.end_index)
        if key in seen:
            continue
        seen.add(key)
        unique.append(
            EvidenceSpan(
                span_id=f"s{len(unique) + 1}",
                raw_text=span.raw_text,
                start_index=span.start_index,
                end_index=span.end_index,
                detected_type=span.detected_type,
                confidence=span.confidence,
                source_field=span.source_field,
            )
        )
    return unique


def _ordered_unique(values: Iterable[Any]) -> Tuple[str, ...]:
    out: List[str] = []
    for value in values or ():
        item = str(value or "").strip()
        if item and item not in out:
            out.append(item)
    return tuple(out)


def validate_evidence_ledger(
    evidence_spans: Sequence[EvidenceSpan],
    *,
    current_input: Mapping[str, Any] | None = None,
) -> EvidenceLedgerValidationReport:
    """Validate the existing ``sN`` id, source-field and offset contract.

    Passing ``current_input`` additionally checks that each text-field span can
    be resolved to the original source slice. No source text is copied into the
    returned report.
    """

    spans = tuple(evidence_spans or ())
    seen: set[str] = set()
    duplicate_ids: List[str] = []
    noncanonical_ids: List[str] = []
    invalid_offsets: List[str] = []
    source_mismatches: List[str] = []
    unknown_fields: List[str] = []
    canonical_ids: List[str] = []
    known_fields = set(_STRUCTURED_TEXT_FIELDS) | set(_STRUCTURED_LIST_FIELDS)

    normalized_input = (
        normalize_emlis_current_input(dict(current_input))
        if isinstance(current_input, Mapping)
        else None
    )

    for span in spans:
        span_id = str(getattr(span, "span_id", "") or "").strip()
        if span_id in seen:
            duplicate_ids.append(span_id or "<empty>")
        seen.add(span_id)
        if not _CANONICAL_SPAN_ID_RE.fullmatch(span_id):
            noncanonical_ids.append(span_id or "<empty>")
        else:
            canonical_ids.append(span_id)

        field = str(getattr(span, "source_field", "") or "").strip()
        if field not in known_fields:
            unknown_fields.append(span_id or "<empty>")

        start = int(getattr(span, "start_index", -1))
        end = int(getattr(span, "end_index", -1))
        if field in _STRUCTURED_TEXT_FIELDS:
            if start < 0 or end <= start:
                invalid_offsets.append(span_id or "<empty>")
                continue
            if normalized_input is not None:
                source = str(normalized_input.get(field) or "")
                if end > len(source):
                    invalid_offsets.append(span_id or "<empty>")
                    continue
                if _clean_text(source[start:end]) != _clean_text(getattr(span, "raw_text", "")):
                    source_mismatches.append(span_id or "<empty>")
        elif field in _STRUCTURED_LIST_FIELDS:
            if (start, end) != (-1, -1):
                invalid_offsets.append(span_id or "<empty>")

    expected_ids = tuple(f"s{index}" for index in range(1, len(spans) + 1))
    actual_ids = tuple(str(getattr(span, "span_id", "") or "").strip() for span in spans)
    issue_codes: List[str] = []
    if duplicate_ids:
        issue_codes.append("duplicate_span_id")
    if noncanonical_ids:
        issue_codes.append("noncanonical_span_id")
    if actual_ids != expected_ids:
        issue_codes.append("nonsequential_span_id")
    if invalid_offsets:
        issue_codes.append("invalid_source_offset")
    if source_mismatches:
        issue_codes.append("source_slice_mismatch")
    if unknown_fields:
        issue_codes.append("unknown_source_field")

    return EvidenceLedgerValidationReport(
        valid=not issue_codes,
        issue_codes=_ordered_unique(issue_codes),
        canonical_span_ids=tuple(canonical_ids),
        duplicate_span_ids=_ordered_unique(duplicate_ids),
        noncanonical_span_ids=_ordered_unique(noncanonical_ids),
        invalid_offset_span_ids=_ordered_unique(invalid_offsets),
        source_mismatch_span_ids=_ordered_unique(source_mismatches),
        unknown_source_field_span_ids=_ordered_unique(unknown_fields),
    )


def build_evidence_span_resolver(
    evidence_spans: Sequence[EvidenceSpan],
    *,
    current_input: Mapping[str, Any] | None = None,
) -> EvidenceSpanResolver:
    """Return a strict resolver for the existing request-local ledger."""

    report = validate_evidence_ledger(evidence_spans, current_input=current_input)
    if not report.valid:
        raise EvidenceLedgerResolutionError(
            "invalid_evidence_ledger:" + ",".join(report.issue_codes)
        )
    return EvidenceSpanResolver(evidence_spans)


def source_text_for_span(current_input: Dict[str, Any] | None, span: EvidenceSpan) -> str:
    """Return the original current_input slice represented by an EvidenceSpan.

    Structured fields such as emotions and categories have no local character
    offsets, so their raw_text is returned directly. This helper is for tests
    and later grounding layers; it does not infer or rewrite content.
    """

    data: Dict[str, Any] = normalize_emlis_current_input(current_input) if current_input is not None else {}
    field = str(getattr(span, "source_field", "") or "")
    if field in _STRUCTURED_TEXT_FIELDS and int(getattr(span, "start_index", -1) or -1) >= 0:
        source = str(data.get(field) or "")
        start = int(getattr(span, "start_index", 0) or 0)
        end = int(getattr(span, "end_index", 0) or 0)
        if 0 <= start <= end <= len(source):
            return source[start:end]
    return str(getattr(span, "raw_text", "") or "")


__all__ = [
    "EvidenceLedgerResolutionError",
    "EvidenceLedgerValidationReport",
    "EvidenceSpanResolver",
    "build_evidence_ledger",
    "build_evidence_span_resolver",
    "source_text_for_span",
    "validate_evidence_ledger",
]
