# -*- coding: utf-8 -*-
from __future__ import annotations

"""Result helpers for the fail-closed CoreTextComposer boundary.

This module is additive. It does not generate user-facing text, change public
API contracts, or connect the common core to any runtime route.
"""

from dataclasses import dataclass, field
import re
from typing import Any, Iterable, Mapping

from cocolon_text_generation_core.policies import (
    DEFAULT_COMPOSER_MODEL,
    DEFAULT_COVERAGE_SCOPE,
    FAIL_CLOSED_COVERAGE_SCOPE,
    STATUS_GENERATED,
    STATUS_REJECTED,
    STATUS_UNAVAILABLE,
    compact_tokens,
)
from cocolon_text_generation_core.types import TextGenerationResult

_SPACE_RE = re.compile(r"\s+")
_PUNCT_TRIM = " \t\r\n　、,。.!！?？『』\"'"

REJECTION_CANDIDATE_TEXT_MISSING = "candidate_text_missing"
REJECTION_CANDIDATE_PRE_REJECTED = "candidate_pre_rejected"
REJECTION_INVALID_CORE_TEXT_PAYLOAD = "invalid_core_text_payload"
REJECTION_PAYLOAD_MINIMUM_NOT_MET = "payload_minimum_not_met"

QUALITY_FLAG_CANDIDATE_MISSING = "candidate_missing"
QUALITY_FLAG_CANDIDATE_PRE_REJECTED = "candidate_pre_rejected"
QUALITY_FLAG_CORE_COMPOSER_REJECTED = "core_text_composer_rejected"
QUALITY_FLAG_CORE_PAYLOAD_INVALID = "core_payload_invalid"
QUALITY_FLAG_GUARD_REJECTED = "guard_rejected"


def _clean_text(value: object, *, limit: int = 0) -> str:
    text = _SPACE_RE.sub(" ", str(value or "").replace("\r", " ").replace("\n", " ")).strip(_PUNCT_TRIM)
    if limit > 0 and len(text) > limit:
        text = text[:limit].rstrip(_PUNCT_TRIM)
    return text


def _clean_token(value: object) -> str:
    return str(value or "").strip()


def _json_safe_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Mapping):
        return json_safe_mapping(value)
    if isinstance(value, (list, tuple, set)):
        return [_json_safe_value(item) for item in value]
    return str(value)


def json_safe_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    out: dict[str, Any] = {}
    for key, item in value.items():
        key_text = _clean_token(key)
        if not key_text:
            continue
        out[key_text] = _json_safe_value(item)
    return out


@dataclass(frozen=True)
class CoreTextCandidate:
    """A body candidate supplied by a core-specific composer.

    The common core validates this candidate; it does not invent fallback text
    from phrase units, sentence plans, tone policy, or evidence.
    """

    text: str = ""
    used_evidence_span_ids: Iterable[str] = field(default_factory=tuple)
    used_phrase_unit_ids: Iterable[str] = field(default_factory=tuple)
    coverage_scope: str = DEFAULT_COVERAGE_SCOPE
    quality_flags: Iterable[str] = field(default_factory=tuple)
    rejection_reasons: Iterable[str] = field(default_factory=tuple)
    composer_model: str = DEFAULT_COMPOSER_MODEL
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "text", _clean_text(self.text, limit=0))
        object.__setattr__(self, "used_evidence_span_ids", compact_tokens(self.used_evidence_span_ids))
        object.__setattr__(self, "used_phrase_unit_ids", compact_tokens(self.used_phrase_unit_ids))
        object.__setattr__(self, "coverage_scope", _clean_token(self.coverage_scope) or DEFAULT_COVERAGE_SCOPE)
        object.__setattr__(self, "quality_flags", compact_tokens(self.quality_flags))
        object.__setattr__(self, "rejection_reasons", compact_tokens(self.rejection_reasons))
        object.__setattr__(self, "composer_model", _clean_token(self.composer_model) or DEFAULT_COMPOSER_MODEL)
        object.__setattr__(self, "meta", json_safe_mapping(self.meta))

    @property
    def usable_text(self) -> bool:
        return bool(self.text)

    @property
    def pre_rejected(self) -> bool:
        return bool(self.rejection_reasons)

    def as_meta(self) -> dict[str, Any]:
        return {
            "text_length": len(self.text),
            "used_evidence_span_ids": list(self.used_evidence_span_ids),
            "used_phrase_unit_ids": list(self.used_phrase_unit_ids),
            "coverage_scope": self.coverage_scope,
            "quality_flags": list(self.quality_flags),
            "rejection_reasons": list(self.rejection_reasons),
            "composer_model": self.composer_model,
            "meta": dict(self.meta),
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any] | None) -> "CoreTextCandidate":
        if not isinstance(value, Mapping):
            return cls()
        text = value.get("candidate_text") or value.get("text") or value.get("comment_text") or ""
        used_evidence = (
            value.get("candidate_used_evidence_span_ids")
            or value.get("used_evidence_span_ids")
            or value.get("evidence_span_ids")
            or ()
        )
        used_units = value.get("candidate_used_phrase_unit_ids") or value.get("used_phrase_unit_ids") or ()
        quality_flags = value.get("candidate_quality_flags") or value.get("quality_flags") or ()
        rejection_reasons = value.get("candidate_rejection_reasons") or value.get("rejection_reasons") or ()
        return cls(
            text=str(text or ""),
            used_evidence_span_ids=used_evidence,
            used_phrase_unit_ids=used_units,
            coverage_scope=str(value.get("coverage_scope") or DEFAULT_COVERAGE_SCOPE),
            quality_flags=quality_flags,
            rejection_reasons=rejection_reasons,
            composer_model=str(value.get("composer_model") or DEFAULT_COMPOSER_MODEL),
            meta=value.get("meta") if isinstance(value.get("meta"), Mapping) else {},
        )

    @classmethod
    def from_payload_meta(cls, meta: Mapping[str, Any] | None) -> "CoreTextCandidate":
        if not isinstance(meta, Mapping):
            return cls()
        nested = meta.get("candidate")
        if isinstance(nested, Mapping):
            return cls.from_mapping(nested)
        return cls.from_mapping(meta)

    @classmethod
    def from_value(cls, value: Any) -> "CoreTextCandidate":
        if isinstance(value, CoreTextCandidate):
            return value
        if isinstance(value, Mapping):
            return cls.from_mapping(value)
        if isinstance(value, str):
            return cls(text=value)
        return cls()


def unavailable_result(
    reasons: Iterable[object],
    *,
    composer_model: str = DEFAULT_COMPOSER_MODEL,
    quality_flags: Iterable[object] = (),
    meta: Mapping[str, Any] | None = None,
) -> TextGenerationResult:
    reason_tokens = compact_tokens(reasons) or (REJECTION_PAYLOAD_MINIMUM_NOT_MET,)
    return TextGenerationResult(
        status=STATUS_UNAVAILABLE,
        text="",
        used_evidence_span_ids=(),
        coverage_scope=FAIL_CLOSED_COVERAGE_SCOPE,
        quality_flags=compact_tokens(quality_flags),
        rejection_reasons=reason_tokens,
        composer_model=composer_model,
        meta=meta or {},
    )


def rejected_result(
    reasons: Iterable[object],
    *,
    composer_model: str = DEFAULT_COMPOSER_MODEL,
    quality_flags: Iterable[object] = (),
    meta: Mapping[str, Any] | None = None,
) -> TextGenerationResult:
    reason_tokens = compact_tokens(reasons) or (QUALITY_FLAG_CORE_COMPOSER_REJECTED,)
    return TextGenerationResult(
        status=STATUS_REJECTED,
        text="",
        used_evidence_span_ids=(),
        coverage_scope=FAIL_CLOSED_COVERAGE_SCOPE,
        quality_flags=compact_tokens(quality_flags),
        rejection_reasons=reason_tokens,
        composer_model=composer_model,
        meta=meta or {},
    )


def generated_result(
    candidate: CoreTextCandidate,
    *,
    composer_model: str = DEFAULT_COMPOSER_MODEL,
    quality_flags: Iterable[object] = (),
    meta: Mapping[str, Any] | None = None,
) -> TextGenerationResult:
    return TextGenerationResult(
        status=STATUS_GENERATED,
        text=candidate.text,
        used_evidence_span_ids=candidate.used_evidence_span_ids,
        coverage_scope=candidate.coverage_scope or DEFAULT_COVERAGE_SCOPE,
        quality_flags=compact_tokens(tuple(candidate.quality_flags) + tuple(quality_flags or ())),
        rejection_reasons=(),
        composer_model=composer_model or candidate.composer_model,
        meta=meta or {},
    )


__all__ = [
    "CoreTextCandidate",
    "QUALITY_FLAG_CANDIDATE_MISSING",
    "QUALITY_FLAG_CANDIDATE_PRE_REJECTED",
    "QUALITY_FLAG_CORE_COMPOSER_REJECTED",
    "QUALITY_FLAG_CORE_PAYLOAD_INVALID",
    "QUALITY_FLAG_GUARD_REJECTED",
    "REJECTION_CANDIDATE_PRE_REJECTED",
    "REJECTION_CANDIDATE_TEXT_MISSING",
    "REJECTION_INVALID_CORE_TEXT_PAYLOAD",
    "REJECTION_PAYLOAD_MINIMUM_NOT_MET",
    "generated_result",
    "json_safe_mapping",
    "rejected_result",
    "unavailable_result",
]
