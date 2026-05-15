# -*- coding: utf-8 -*-
from __future__ import annotations

"""Common, core-agnostic text generation types for Cocolon.

Phase 2 only defines additive data contracts.  Existing EmlisAI types stay in
place and are not replaced by these classes yet.
"""

from dataclasses import dataclass, field
import hashlib
import re
from typing import Any, Iterable, Mapping, Tuple

from .policies import (
    DEFAULT_COMPOSER_MODEL,
    DEFAULT_COVERAGE_SCOPE,
    FAIL_CLOSED_COVERAGE_SCOPE,
    PASSING_STATUSES,
    REJECTION_CORE_ID_MISSING,
    REJECTION_EVIDENCE_MISSING,
    REJECTION_MUST_KEEP_ROLE_MISSING,
    REJECTION_PHRASE_UNIT_MISSING,
    REJECTION_RESULT_EVIDENCE_MISSING,
    REJECTION_RESULT_TEXT_MISSING,
    REJECTION_SENTENCE_PLAN_MISSING,
    STATUS_REJECTED,
    STATUS_UNAVAILABLE,
    compact_tokens,
    normalize_status,
)

_SPACE_RE = re.compile(r"\s+")
_PUNCT_TRIM = " \t\r\n　、,。.!！?？『』\"'"


def _clean_text(value: object, *, limit: int = 0) -> str:
    text = _SPACE_RE.sub(" ", str(value or "").replace("\r", " ").replace("\n", " ")).strip(_PUNCT_TRIM)
    if limit > 0 and len(text) > limit:
        text = text[:limit].rstrip(_PUNCT_TRIM)
    return text


def _clean_token(value: object) -> str:
    return str(value or "").strip()


def _stable_hash(*parts: object) -> str:
    material = "\u241f".join(_clean_text(part, limit=0) for part in parts if _clean_text(part, limit=0))
    if not material:
        return ""
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _json_safe_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Mapping):
        return _json_safe_mapping(value)
    if isinstance(value, (list, tuple, set)):
        return [_json_safe_value(item) for item in value]
    return str(value)


def _json_safe_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
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
class SourceAnchor:
    """A source-bound text anchor used by any Cocolon core.

    ``source_hash`` is derived from field + raw_text when not supplied.  It is
    intentionally not tied to a database table name.
    """

    source_id: str
    field: str
    raw_text: str
    source_hash: str = ""
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        source_id = _clean_token(self.source_id)
        field_name = _clean_token(self.field)
        raw_text = _clean_text(self.raw_text, limit=0)
        source_hash = _clean_token(self.source_hash) or _stable_hash(field_name, raw_text)
        object.__setattr__(self, "source_id", source_id)
        object.__setattr__(self, "field", field_name)
        object.__setattr__(self, "raw_text", raw_text)
        object.__setattr__(self, "source_hash", source_hash)
        object.__setattr__(self, "meta", _json_safe_mapping(self.meta))

    @property
    def usable(self) -> bool:
        return bool(self.source_id and self.field and self.raw_text and self.source_hash)

    def as_meta(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "field": self.field,
            "raw_text": self.raw_text,
            "source_hash": self.source_hash,
            "meta": dict(self.meta),
        }


@dataclass(frozen=True)
class EvidenceSpanLike:
    """Core-agnostic evidence span shape.

    Existing EmlisAI ``EvidenceSpan`` is not replaced in Phase 2; adapters can
    convert into this shape in a later phase.
    """

    span_id: str
    source_anchor: SourceAnchor
    raw_text: str = ""
    role: str = ""
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        span_id = _clean_token(self.span_id)
        raw_text = _clean_text(self.raw_text or self.source_anchor.raw_text, limit=0)
        object.__setattr__(self, "span_id", span_id)
        object.__setattr__(self, "raw_text", raw_text)
        object.__setattr__(self, "role", _clean_token(self.role))
        object.__setattr__(self, "meta", _json_safe_mapping(self.meta))

    @property
    def usable(self) -> bool:
        return bool(self.span_id and self.source_anchor.usable and self.raw_text)

    def as_meta(self) -> dict[str, Any]:
        return {
            "span_id": self.span_id,
            "source_anchor": self.source_anchor.as_meta(),
            "raw_text": self.raw_text,
            "role": self.role,
            "meta": dict(self.meta),
        }


@dataclass(frozen=True)
class PhraseUnit:
    """A minimal phrase candidate that can be used by a core-specific composer."""

    phrase_unit_id: str
    evidence_span_id: str
    text: str
    role: str = ""
    quality_flags: Iterable[str] = field(default_factory=tuple)
    must_keep: bool = False
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "phrase_unit_id", _clean_token(self.phrase_unit_id))
        object.__setattr__(self, "evidence_span_id", _clean_token(self.evidence_span_id))
        object.__setattr__(self, "text", _clean_text(self.text, limit=180))
        object.__setattr__(self, "role", _clean_token(self.role))
        object.__setattr__(self, "quality_flags", compact_tokens(self.quality_flags))
        object.__setattr__(self, "must_keep", bool(self.must_keep))
        object.__setattr__(self, "meta", _json_safe_mapping(self.meta))

    @property
    def usable(self) -> bool:
        return bool(self.phrase_unit_id and self.evidence_span_id and self.text)

    def as_meta(self) -> dict[str, Any]:
        return {
            "phrase_unit_id": self.phrase_unit_id,
            "evidence_span_id": self.evidence_span_id,
            "text": self.text,
            "role": self.role,
            "quality_flags": list(self.quality_flags),
            "must_keep": self.must_keep,
            "meta": dict(self.meta),
        }


@dataclass(frozen=True)
class SentencePlan:
    """A plan for composing one sentence from phrase units.

    This is not a user-facing fixed sentence template.
    """

    sentence_plan_id: str
    phrase_unit_ids: Iterable[str]
    relation_type: str = ""
    line_role: str = ""
    max_chars: int = 120
    must_include: bool = True
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "sentence_plan_id", _clean_token(self.sentence_plan_id))
        object.__setattr__(self, "phrase_unit_ids", compact_tokens(self.phrase_unit_ids))
        object.__setattr__(self, "relation_type", _clean_token(self.relation_type))
        object.__setattr__(self, "line_role", _clean_token(self.line_role))
        try:
            max_chars = int(self.max_chars)
        except (TypeError, ValueError):
            max_chars = 120
        object.__setattr__(self, "max_chars", max(1, min(max_chars, 240)))
        object.__setattr__(self, "must_include", bool(self.must_include))
        object.__setattr__(self, "meta", _json_safe_mapping(self.meta))

    @property
    def usable(self) -> bool:
        return bool(self.sentence_plan_id and self.phrase_unit_ids)

    def as_meta(self) -> dict[str, Any]:
        return {
            "sentence_plan_id": self.sentence_plan_id,
            "phrase_unit_ids": list(self.phrase_unit_ids),
            "relation_type": self.relation_type,
            "line_role": self.line_role,
            "max_chars": self.max_chars,
            "must_include": self.must_include,
            "meta": dict(self.meta),
        }


@dataclass(frozen=True)
class TextGenerationResult:
    """Common result envelope with fail-closed behavior."""

    status: str = STATUS_UNAVAILABLE
    text: str = ""
    used_evidence_span_ids: Iterable[str] = field(default_factory=tuple)
    coverage_scope: str = FAIL_CLOSED_COVERAGE_SCOPE
    quality_flags: Iterable[str] = field(default_factory=tuple)
    rejection_reasons: Iterable[str] = field(default_factory=tuple)
    composer_model: str = DEFAULT_COMPOSER_MODEL
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        status = normalize_status(self.status)
        text = _clean_text(self.text, limit=0)
        used_evidence_span_ids = compact_tokens(self.used_evidence_span_ids)
        rejection_reasons = list(compact_tokens(self.rejection_reasons))
        quality_flags = list(compact_tokens(self.quality_flags))
        coverage_scope = _clean_token(self.coverage_scope) or FAIL_CLOSED_COVERAGE_SCOPE
        composer_model = _clean_token(self.composer_model) or DEFAULT_COMPOSER_MODEL

        if status in PASSING_STATUSES:
            if not text:
                status = STATUS_UNAVAILABLE
                rejection_reasons.append(REJECTION_RESULT_TEXT_MISSING)
            elif not used_evidence_span_ids:
                status = STATUS_UNAVAILABLE
                rejection_reasons.append(REJECTION_RESULT_EVIDENCE_MISSING)

        if status not in PASSING_STATUSES:
            text = ""
            used_evidence_span_ids = tuple()
            if status == STATUS_UNAVAILABLE and not rejection_reasons:
                rejection_reasons.append("fail_closed_unavailable")
            coverage_scope = FAIL_CLOSED_COVERAGE_SCOPE if coverage_scope == DEFAULT_COVERAGE_SCOPE else coverage_scope

        object.__setattr__(self, "status", status)
        object.__setattr__(self, "text", text)
        object.__setattr__(self, "used_evidence_span_ids", used_evidence_span_ids)
        object.__setattr__(self, "coverage_scope", coverage_scope)
        object.__setattr__(self, "quality_flags", tuple(dict.fromkeys(quality_flags)))
        object.__setattr__(self, "rejection_reasons", tuple(dict.fromkeys(rejection_reasons)))
        object.__setattr__(self, "composer_model", composer_model)
        object.__setattr__(self, "meta", _json_safe_mapping(self.meta))

    @property
    def passed(self) -> bool:
        return self.status in PASSING_STATUSES

    @classmethod
    def unavailable(
        cls,
        reason: str,
        *,
        composer_model: str = DEFAULT_COMPOSER_MODEL,
        quality_flags: Iterable[str] = (),
        meta: Mapping[str, Any] | None = None,
    ) -> "TextGenerationResult":
        return cls(
            status=STATUS_UNAVAILABLE,
            text="",
            used_evidence_span_ids=(),
            coverage_scope=FAIL_CLOSED_COVERAGE_SCOPE,
            quality_flags=quality_flags,
            rejection_reasons=(reason,),
            composer_model=composer_model,
            meta=meta or {},
        )

    @classmethod
    def rejected(
        cls,
        reason: str,
        *,
        composer_model: str = DEFAULT_COMPOSER_MODEL,
        quality_flags: Iterable[str] = (),
        meta: Mapping[str, Any] | None = None,
    ) -> "TextGenerationResult":
        return cls(
            status=STATUS_REJECTED,
            text="",
            used_evidence_span_ids=(),
            coverage_scope=FAIL_CLOSED_COVERAGE_SCOPE,
            quality_flags=quality_flags,
            rejection_reasons=(reason,),
            composer_model=composer_model,
            meta=meta or {},
        )

    def as_meta(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "used_evidence_span_ids": list(self.used_evidence_span_ids),
            "coverage_scope": self.coverage_scope,
            "quality_flags": list(self.quality_flags),
            "rejection_reasons": list(self.rejection_reasons),
            "composer_model": self.composer_model,
            "meta": dict(self.meta),
        }

    def as_dict(self) -> dict[str, Any]:
        data = self.as_meta()
        data["text"] = self.text
        return data


@dataclass(frozen=True)
class CoreTextPayload:
    """Core-agnostic input envelope for future text generation."""

    core_id: str
    source_anchors: Iterable[SourceAnchor] = field(default_factory=tuple)
    evidence_spans: Iterable[EvidenceSpanLike] = field(default_factory=tuple)
    phrase_units: Iterable[PhraseUnit] = field(default_factory=tuple)
    sentence_plans: Iterable[SentencePlan] = field(default_factory=tuple)
    tone_policy: Mapping[str, Any] = field(default_factory=dict)
    safety_policy: Mapping[str, Any] = field(default_factory=dict)
    must_keep_roles: Iterable[str] = field(default_factory=tuple)
    forbidden_surface_patterns: Iterable[str] = field(default_factory=tuple)
    composer_model: str = DEFAULT_COMPOSER_MODEL
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "core_id", _clean_token(self.core_id))
        object.__setattr__(self, "source_anchors", tuple(self.source_anchors or ()))
        object.__setattr__(self, "evidence_spans", tuple(self.evidence_spans or ()))
        object.__setattr__(self, "phrase_units", tuple(self.phrase_units or ()))
        object.__setattr__(self, "sentence_plans", tuple(self.sentence_plans or ()))
        object.__setattr__(self, "tone_policy", _json_safe_mapping(self.tone_policy))
        object.__setattr__(self, "safety_policy", _json_safe_mapping(self.safety_policy))
        object.__setattr__(self, "must_keep_roles", compact_tokens(self.must_keep_roles))
        object.__setattr__(self, "forbidden_surface_patterns", compact_tokens(self.forbidden_surface_patterns))
        object.__setattr__(self, "composer_model", _clean_token(self.composer_model) or DEFAULT_COMPOSER_MODEL)
        object.__setattr__(self, "meta", _json_safe_mapping(self.meta))

    def validate_minimum(self) -> Tuple[str, ...]:
        reasons: list[str] = []
        if not self.core_id:
            reasons.append(REJECTION_CORE_ID_MISSING)

        usable_evidence = [span for span in self.evidence_spans if getattr(span, "usable", False)]
        if not usable_evidence:
            reasons.append(REJECTION_EVIDENCE_MISSING)

        evidence_ids = {span.span_id for span in usable_evidence}
        usable_units = [unit for unit in self.phrase_units if getattr(unit, "usable", False) and unit.evidence_span_id in evidence_ids]
        if not usable_units:
            reasons.append(REJECTION_PHRASE_UNIT_MISSING)

        usable_unit_ids = {unit.phrase_unit_id for unit in usable_units}
        usable_plans = [
            plan
            for plan in self.sentence_plans
            if getattr(plan, "usable", False) and all(unit_id in usable_unit_ids for unit_id in plan.phrase_unit_ids)
        ]
        if not usable_plans:
            reasons.append(REJECTION_SENTENCE_PLAN_MISSING)

        covered_roles = {unit.role for unit in usable_units if unit.role}
        missing_roles = [role for role in self.must_keep_roles if role not in covered_roles]
        if missing_roles:
            reasons.append(f"{REJECTION_MUST_KEEP_ROLE_MISSING}:{','.join(missing_roles)}")

        return tuple(dict.fromkeys(reasons))

    @property
    def valid_minimum(self) -> bool:
        return not self.validate_minimum()

    def to_fail_closed_result(self) -> TextGenerationResult:
        reasons = self.validate_minimum()
        if not reasons:
            return TextGenerationResult.unavailable(
                "composer_not_connected",
                composer_model=self.composer_model,
                meta={"core_id": self.core_id, "phase": "core_types_only"},
            )
        return TextGenerationResult.unavailable(
            reasons[0],
            composer_model=self.composer_model,
            quality_flags=("payload_minimum_not_met",),
            meta={"core_id": self.core_id, "all_rejection_reasons": list(reasons)},
        )

    def as_meta(self) -> dict[str, Any]:
        return {
            "core_id": self.core_id,
            "source_anchors": [anchor.as_meta() for anchor in self.source_anchors],
            "evidence_spans": [span.as_meta() for span in self.evidence_spans],
            "phrase_units": [unit.as_meta() for unit in self.phrase_units],
            "sentence_plans": [plan.as_meta() for plan in self.sentence_plans],
            "tone_policy": dict(self.tone_policy),
            "safety_policy": dict(self.safety_policy),
            "must_keep_roles": list(self.must_keep_roles),
            "forbidden_surface_patterns": list(self.forbidden_surface_patterns),
            "composer_model": self.composer_model,
            "meta": dict(self.meta),
        }
