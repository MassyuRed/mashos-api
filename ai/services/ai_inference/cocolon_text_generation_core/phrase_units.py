# -*- coding: utf-8 -*-
from __future__ import annotations

"""Core-agnostic PhraseUnit helpers for Cocolon text generation.

Phase 4 extracts only the common, mechanical checks from the EmlisAI Phase8
middle layer. Role names are kept as plain strings; this module does not decide
what a role means for EmlisAI, Piece, or Analysis.
"""

from dataclasses import dataclass, field
import re
from typing import Any, Callable, Iterable, Mapping, Tuple

from cocolon_text_generation_core.policies import compact_tokens
from cocolon_text_generation_core.types import EvidenceSpanLike, PhraseUnit

PHRASE_UNIT_BUILDER_NAME = "cocolon_text_generation_core.phrase_units.v1"

QUALITY_FLAG_EMPTY_TEXT = "empty_text"
QUALITY_FLAG_EMOTION_LABEL_ONLY = "emotion_label_only"
QUALITY_FLAG_UNFINISHED_PHRASE = "unfinished_phrase"
QUALITY_FLAG_ORPHAN_PARTICLE = "orphan_particle"
QUALITY_FLAG_TOO_LONG_QUOTE = "too_long_quote"

REJECTION_PHRASE_UNIT_UNSAFE = "phrase_unit_unsafe"

_EMOTION_LABELS = frozenset(
    {
        "喜び",
        "悲しみ",
        "怒り",
        "不安",
        "平穏",
        "安心",
        "焦り",
        "恐れ",
        "怖さ",
        "自己理解",
        "期待",
        "疲労",
    }
)
_SPACE_RE = re.compile(r"\s+")
_PUNCT_TRIM = " \t\r\n　、,。.!！?？『』「」\"'"
_ORPHAN_PARTICLE_RE = re.compile(r"(?:を|が|に|は|へ|で)$")
_UNFINISHED_PHRASE_RE = re.compile(
    r"(?:なんであ|考え始め|悪化するが|悪化する|先のことを考え始め|現実と|自分のことを|普通に)$"
)
_TRAILING_CONNECTIVE_RE = re.compile(r"(?:けど|だけど|でも|のに|から|なら|すると|したら|そうしたら|または|あるいは)$")

RoleResolver = Callable[[EvidenceSpanLike], object]
TextResolver = Callable[[EvidenceSpanLike], object]


def _clean_token(value: object) -> str:
    return str(value or "").strip()


def normalize_phrase_text(value: object, *, max_chars: int = 180) -> str:
    """Normalize whitespace and surrounding punctuation without repairing meaning."""

    text = _SPACE_RE.sub(" ", str(value or "").replace("\r", " ").replace("\n", " ")).strip(_PUNCT_TRIM)
    if max_chars > 0 and len(text) > max_chars:
        text = text[:max_chars].rstrip(_PUNCT_TRIM)
    return text


def compact_phrase_text(value: object) -> str:
    return re.sub(r"\s+", "", normalize_phrase_text(value, max_chars=0))


def is_emotion_label_only(value: object) -> bool:
    """Return True when a phrase is only a body label, not a body candidate."""

    compact = compact_phrase_text(value).strip(_PUNCT_TRIM)
    return compact in _EMOTION_LABELS


def phrase_unit_quality_flags(value: object, *, max_quote_chars: int = 64) -> Tuple[str, ...]:
    """Return common quality flags for a possible PhraseUnit body.

    The checks are intentionally narrow and mechanical. They do not infer a
    core-specific role; they only block fragments that should not become shared
    body material.
    """

    text = normalize_phrase_text(value, max_chars=0)
    compact = compact_phrase_text(text)
    flags: list[str] = []
    if not text:
        flags.append(QUALITY_FLAG_EMPTY_TEXT)
    if text and is_emotion_label_only(text):
        flags.append(QUALITY_FLAG_EMOTION_LABEL_ONLY)
    if text and (_UNFINISHED_PHRASE_RE.search(compact) or _TRAILING_CONNECTIVE_RE.search(compact)):
        flags.append(QUALITY_FLAG_UNFINISHED_PHRASE)
    if text and _ORPHAN_PARTICLE_RE.search(compact):
        flags.append(QUALITY_FLAG_ORPHAN_PARTICLE)
    if max_quote_chars > 0 and len(compact) > max_quote_chars:
        flags.append(QUALITY_FLAG_TOO_LONG_QUOTE)
    return tuple(dict.fromkeys(flags))


def is_phrase_unit_body_candidate(value: object, *, max_quote_chars: int = 64) -> bool:
    """Return whether text can become a common PhraseUnit body."""

    return not phrase_unit_quality_flags(value, max_quote_chars=max_quote_chars)


def _mapping_get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


def _json_safe_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    out: dict[str, Any] = {}
    for key, item in value.items():
        key_text = _clean_token(key)
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


def _evidence_span_id(span: EvidenceSpanLike | Mapping[str, Any] | Any) -> str:
    return _clean_token(_mapping_get(span, "span_id", ""))


def _evidence_role(span: EvidenceSpanLike | Mapping[str, Any] | Any) -> str:
    return _clean_token(_mapping_get(span, "role", ""))


def _evidence_raw_text(span: EvidenceSpanLike | Mapping[str, Any] | Any) -> str:
    raw = _mapping_get(span, "raw_text", "")
    if not raw:
        anchor = _mapping_get(span, "source_anchor", None)
        raw = _mapping_get(anchor, "raw_text", "")
    return normalize_phrase_text(raw, max_chars=0)


def _evidence_meta(span: EvidenceSpanLike | Mapping[str, Any] | Any) -> dict[str, Any]:
    return _json_safe_mapping(_mapping_get(span, "meta", {}))


def _meta_must_keep(meta: Mapping[str, Any]) -> bool:
    value = meta.get("must_keep")
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "must_keep"}
    return False


@dataclass(frozen=True)
class PhraseUnitBuildResult:
    """Result of common PhraseUnit extraction."""

    phrase_units: Iterable[PhraseUnit] = field(default_factory=tuple)
    skipped_span_ids: Iterable[str] = field(default_factory=tuple)
    rejection_reasons: Iterable[str] = field(default_factory=tuple)
    rejected_candidates: Iterable[Mapping[str, Any]] = field(default_factory=tuple)
    builder_name: str = PHRASE_UNIT_BUILDER_NAME
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        phrase_units = tuple(unit for unit in self.phrase_units or () if getattr(unit, "usable", False))
        object.__setattr__(self, "phrase_units", phrase_units)
        object.__setattr__(self, "skipped_span_ids", compact_tokens(self.skipped_span_ids))
        object.__setattr__(self, "rejection_reasons", compact_tokens(self.rejection_reasons))
        object.__setattr__(self, "rejected_candidates", tuple(_json_safe_mapping(item) for item in self.rejected_candidates or ()))
        object.__setattr__(self, "builder_name", _clean_token(self.builder_name) or PHRASE_UNIT_BUILDER_NAME)
        object.__setattr__(self, "meta", _json_safe_mapping(self.meta))

    @property
    def usable(self) -> bool:
        return bool(self.phrase_units)

    def as_meta(self) -> dict[str, Any]:
        return {
            "builder_name": self.builder_name,
            "phrase_units": [unit.as_meta() for unit in self.phrase_units],
            "skipped_span_ids": list(self.skipped_span_ids),
            "rejection_reasons": list(self.rejection_reasons),
            "rejected_candidates": [dict(item) for item in self.rejected_candidates],
            "meta": dict(self.meta),
        }


def build_phrase_unit(
    evidence_span: EvidenceSpanLike | Mapping[str, Any] | Any,
    *,
    phrase_unit_id: object = "",
    phrase_text: object | None = None,
    role: object | None = None,
    must_keep: bool | None = None,
    unit_index: int = 1,
    max_quote_chars: int = 64,
) -> PhraseUnit | None:
    """Build one common PhraseUnit, or return None when it is unsafe.

    ``role`` is stored as a string and is not interpreted here. The caller can
    pass any core-specific role name and keep meaning decisions in its Composer.
    """

    span_id = _evidence_span_id(evidence_span)
    raw_text = _evidence_raw_text(evidence_span)
    text = normalize_phrase_text(raw_text if phrase_text is None else phrase_text, max_chars=180)
    flags = phrase_unit_quality_flags(text, max_quote_chars=max_quote_chars)
    if flags or not span_id:
        return None

    meta = _evidence_meta(evidence_span)
    meta.update(
        {
            "source_builder": PHRASE_UNIT_BUILDER_NAME,
            "source_evidence_span_id": span_id,
            "role_meaning_interpreted": False,
        }
    )
    resolved_role = _clean_token(_evidence_role(evidence_span) if role is None else role)
    resolved_must_keep = _meta_must_keep(meta) if must_keep is None else bool(must_keep)
    resolved_id = _clean_token(phrase_unit_id) or f"pu{max(1, int(unit_index or 1))}"
    return PhraseUnit(
        phrase_unit_id=resolved_id,
        evidence_span_id=span_id,
        text=text,
        role=resolved_role,
        quality_flags=(),
        must_keep=resolved_must_keep,
        meta=meta,
    )


def build_phrase_units(
    evidence_spans: Iterable[EvidenceSpanLike | Mapping[str, Any] | Any] | None,
    *,
    role_resolver: RoleResolver | None = None,
    text_resolver: TextResolver | None = None,
    must_keep_roles: Iterable[object] | None = None,
    max_quote_chars: int = 64,
    start_index: int = 1,
) -> PhraseUnitBuildResult:
    """Build safe common PhraseUnits from source evidence.

    Common extraction keeps role strings but never maps them to EmlisAI, Piece,
    or Analysis semantics. Optional resolvers are supplied by core-specific
    adapters when they need to choose role or text candidates.
    """

    span_items = tuple(evidence_spans or ())
    phrase_units: list[PhraseUnit] = []
    skipped: list[str] = []
    rejected: list[dict[str, Any]] = []
    reasons: list[str] = []
    must_keep_role_set = set(compact_tokens(must_keep_roles))

    for source_index, span in enumerate(span_items, start=1):
        span_id = _evidence_span_id(span)
        raw_text = _evidence_raw_text(span)
        try:
            resolved_role = _clean_token(role_resolver(span)) if role_resolver else _evidence_role(span)  # type: ignore[arg-type]
        except Exception:
            resolved_role = _evidence_role(span)
        try:
            resolved_text = text_resolver(span) if text_resolver else raw_text  # type: ignore[arg-type]
        except Exception:
            resolved_text = raw_text

        flags = phrase_unit_quality_flags(resolved_text, max_quote_chars=max_quote_chars)
        if flags or not span_id:
            skipped.append(span_id or f"index:{source_index}")
            reasons.append(REJECTION_PHRASE_UNIT_UNSAFE)
            rejected.append(
                {
                    "span_id": span_id,
                    "raw_text": raw_text,
                    "candidate_text": normalize_phrase_text(resolved_text, max_chars=180),
                    "quality_flags": list(flags) or ([QUALITY_FLAG_EMPTY_TEXT] if not span_id else []),
                }
            )
            continue

        unit = build_phrase_unit(
            span,
            phrase_unit_id=f"pu{start_index + len(phrase_units)}",
            phrase_text=resolved_text,
            role=resolved_role,
            must_keep=(resolved_role in must_keep_role_set) if resolved_role else False,
            unit_index=start_index + len(phrase_units),
            max_quote_chars=max_quote_chars,
        )
        if unit is None:
            skipped.append(span_id or f"index:{source_index}")
            reasons.append(REJECTION_PHRASE_UNIT_UNSAFE)
            continue
        phrase_units.append(unit)

    return PhraseUnitBuildResult(
        phrase_units=tuple(phrase_units),
        skipped_span_ids=tuple(skipped),
        rejection_reasons=tuple(dict.fromkeys(reasons)),
        rejected_candidates=tuple(rejected),
        meta={"input_evidence_count": len(span_items), "role_meaning_interpreted": False},
    )


def usable_phrase_units(units: Iterable[PhraseUnit] | None) -> Tuple[PhraseUnit, ...]:
    return tuple(unit for unit in units or () if getattr(unit, "usable", False))


def phrase_units_by_id(units: Iterable[PhraseUnit] | None) -> dict[str, PhraseUnit]:
    out: dict[str, PhraseUnit] = {}
    for unit in usable_phrase_units(units):
        if unit.phrase_unit_id and unit.phrase_unit_id not in out:
            out[unit.phrase_unit_id] = unit
    return out


__all__ = [
    "PHRASE_UNIT_BUILDER_NAME",
    "QUALITY_FLAG_EMOTION_LABEL_ONLY",
    "QUALITY_FLAG_EMPTY_TEXT",
    "QUALITY_FLAG_ORPHAN_PARTICLE",
    "QUALITY_FLAG_TOO_LONG_QUOTE",
    "QUALITY_FLAG_UNFINISHED_PHRASE",
    "REJECTION_PHRASE_UNIT_UNSAFE",
    "PhraseUnitBuildResult",
    "build_phrase_unit",
    "build_phrase_units",
    "compact_phrase_text",
    "is_emotion_label_only",
    "is_phrase_unit_body_candidate",
    "normalize_phrase_text",
    "phrase_unit_quality_flags",
    "phrase_units_by_id",
    "usable_phrase_units",
]
