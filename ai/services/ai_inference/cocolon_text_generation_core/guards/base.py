# -*- coding: utf-8 -*-
from __future__ import annotations

"""Shared result helpers for Cocolon common text-generation guards.

The guard layer is additive. It does not generate user-facing text and does not
change EmlisAI, Piece, Analysis, public API, DB, or visible-name contracts.
"""

from dataclasses import dataclass, field
import re
from typing import Any, Iterable, Mapping, Tuple

from cocolon_text_generation_core.policies import compact_tokens

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？!?])\s*|\n+")
_SPACE_RE = re.compile(r"\s+")
_NORMALIZE_RE = re.compile(r"[\s、。.!！?？「」『』（）()\[\]【】\"'`]+")
_PUNCT_TRIM = " \t\r\n　、,。.!！?？『』\"'「」（）()[]【】"
_GREETING_RE = re.compile(r"^(?:[^。！？!?\n]{1,36}さん、)?(?:おはようございます|こんにちは|こんばんは|Emlisです|.+Emlisです)[。.!！]?$")


def clean_text(value: object, *, limit: int = 0) -> str:
    text = _SPACE_RE.sub(" ", str(value or "").replace("\r", " ").replace("\n", " ")).strip(_PUNCT_TRIM)
    if limit > 0 and len(text) > limit:
        text = text[:limit].rstrip(_PUNCT_TRIM)
    return text


def clean_token(value: object) -> str:
    return str(value or "").strip()


def normalize_text(value: object) -> str:
    return _NORMALIZE_RE.sub("", str(value or "")).strip()


def split_sentences(value: object, *, skip_greeting: bool = True) -> Tuple[str, ...]:
    out: list[str] = []
    raw = str(value or "").replace("\r", "\n")
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        for sentence in _SENTENCE_SPLIT_RE.split(line):
            sentence = clean_text(sentence)
            if not sentence:
                continue
            if skip_greeting and _GREETING_RE.match(sentence):
                continue
            out.append(sentence)
    return tuple(out)


def _json_safe_value(item: Any) -> Any:
    if isinstance(item, (str, int, float, bool)) or item is None:
        return item
    if isinstance(item, Mapping):
        return json_safe_mapping(item)
    if isinstance(item, (list, tuple, set)):
        return [_json_safe_value(value) for value in item]
    return str(item)


def json_safe_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    out: dict[str, Any] = {}
    for key, item in value.items():
        key_text = clean_token(key)
        if not key_text:
            continue
        out[key_text] = _json_safe_value(item)
    return out


def char_ngrams(text: object, n: int = 3) -> set[str]:
    compact = normalize_text(text)
    if len(compact) < n:
        return {compact} if compact else set()
    return {compact[index : index + n] for index in range(len(compact) - n + 1)}


def ngram_overlap(left: object, right: object) -> float:
    left_grams = char_ngrams(left)
    right_grams = char_ngrams(right)
    if not left_grams or not right_grams:
        return 0.0
    return len(left_grams.intersection(right_grams)) / max(1, min(len(left_grams), len(right_grams)))


def token_list(value: Iterable[object] | object | None) -> Tuple[str, ...]:
    if value is None:
        return tuple()
    if isinstance(value, (str, bytes)):
        return compact_tokens((value,))
    return compact_tokens(value)  # type: ignore[arg-type]


@dataclass(frozen=True)
class GuardResult:
    guard_name: str
    passed: bool = True
    quality_flags: Iterable[str] = field(default_factory=tuple)
    rejection_reasons: Iterable[str] = field(default_factory=tuple)
    matched_texts: Iterable[str] = field(default_factory=tuple)
    coverage_ratio: float = 1.0
    used_evidence_span_ids: Iterable[str] = field(default_factory=tuple)
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        reasons = compact_tokens(self.rejection_reasons)
        try:
            ratio = float(self.coverage_ratio)
        except (TypeError, ValueError):
            ratio = 0.0
        object.__setattr__(self, "guard_name", clean_token(self.guard_name) or "cocolon_text_generation_guard")
        object.__setattr__(self, "passed", bool(self.passed) and not reasons)
        object.__setattr__(self, "quality_flags", compact_tokens(self.quality_flags))
        object.__setattr__(self, "rejection_reasons", reasons)
        object.__setattr__(self, "matched_texts", compact_tokens(self.matched_texts))
        object.__setattr__(self, "coverage_ratio", round(max(0.0, min(1.0, ratio)), 3))
        object.__setattr__(self, "used_evidence_span_ids", compact_tokens(self.used_evidence_span_ids))
        object.__setattr__(self, "meta", json_safe_mapping(self.meta))

    @property
    def failed(self) -> bool:
        return not self.passed

    @property
    def rejected(self) -> bool:
        return not self.passed

    @property
    def matched_surfaces(self) -> Tuple[str, ...]:
        return tuple(self.matched_texts)


    @property
    def sentence_claims(self) -> Any:
        return self.meta.get("sentence_claims", [])

    @property
    def limited_surface_repetition_score(self) -> float:
        try:
            return float(self.meta.get("limited_surface_repetition_score", 0.0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def missing_evidence_span_ids(self) -> Tuple[str, ...]:
        value = self.meta.get("missing_evidence_span_ids", ())
        if isinstance(value, (str, bytes)):
            return compact_tokens((value,))
        return compact_tokens(value)

    def __getattr__(self, name: str) -> Any:
        if name in self.meta:
            value = self.meta[name]
            if isinstance(value, list):
                return tuple(value)
            return value
        raise AttributeError(name)

    def as_meta(self) -> dict[str, Any]:
        return {
            "guard_name": self.guard_name,
            "passed": self.passed,
            "quality_flags": list(self.quality_flags),
            "rejection_reasons": list(self.rejection_reasons),
            "matched_texts": list(self.matched_texts),
            "matched_surfaces": list(self.matched_texts),
            "coverage_ratio": self.coverage_ratio,
            "used_evidence_span_ids": list(self.used_evidence_span_ids),
            "meta": dict(self.meta),
        }


def make_guard_result(
    *,
    guard_name: object,
    reasons: Iterable[object] = (),
    quality_flags: Iterable[object] = (),
    matched_texts: Iterable[object] = (),
    coverage_ratio: float = 1.0,
    used_evidence_span_ids: Iterable[object] = (),
    meta: Mapping[str, Any] | None = None,
) -> GuardResult:
    reason_tokens = compact_tokens(reasons)
    return GuardResult(
        guard_name=clean_token(guard_name),
        passed=not reason_tokens,
        quality_flags=compact_tokens(quality_flags),
        rejection_reasons=reason_tokens,
        matched_texts=compact_tokens(matched_texts),
        coverage_ratio=coverage_ratio,
        used_evidence_span_ids=compact_tokens(used_evidence_span_ids),
        meta=meta or {},
    )


def combine_guard_results(results: Iterable[GuardResult]) -> GuardResult:
    items = tuple(results or ())
    return GuardResult(
        guard_name="combined_text_generation_guards",
        passed=all(item.passed for item in items),
        quality_flags=tuple(flag for item in items for flag in item.quality_flags),
        rejection_reasons=tuple(reason for item in items for reason in item.rejection_reasons),
        matched_texts=tuple(text for item in items for text in item.matched_texts),
        coverage_ratio=min((item.coverage_ratio for item in items), default=1.0),
        used_evidence_span_ids=tuple(span_id for item in items for span_id in item.used_evidence_span_ids),
        meta={"guard_results": [item.as_meta() for item in items]},
    )


GuardReport = GuardResult
combine_guard_reports = combine_guard_results
merge_guard_reports = combine_guard_results

__all__ = [
    "GuardResult",
    "GuardReport",
    "char_ngrams",
    "clean_text",
    "clean_token",
    "combine_guard_reports",
    "combine_guard_results",
    "json_safe_mapping",
    "make_guard_result",
    "merge_guard_reports",
    "ngram_overlap",
    "normalize_text",
    "split_sentences",
    "token_list",
]
