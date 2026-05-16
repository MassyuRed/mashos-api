# -*- coding: utf-8 -*-
from __future__ import annotations

"""Fail-closed common text composer boundary.

CoreTextComposer does not decide EmlisAI/Piece/Analysis purpose, tone, or final
structure. It only receives a caller-supplied candidate and lets the common
Guard layer decide whether that candidate can become a TextGenerationResult.
"""

from typing import Any

from cocolon_text_generation_core.guards import (
    GuardResult,
    combine_guard_results,
    guard_grounding,
    guard_japanese_coherence,
    guard_must_keep_coverage,
    guard_overclaim_diagnosis,
    guard_template_echo,
)
from cocolon_text_generation_core.policies import DEFAULT_COMPOSER_MODEL, QUALITY_FLAG_PAYLOAD_INVALID
from cocolon_text_generation_core.result import (
    CoreTextCandidate,
    QUALITY_FLAG_CANDIDATE_MISSING,
    QUALITY_FLAG_CANDIDATE_PRE_REJECTED,
    QUALITY_FLAG_CORE_COMPOSER_REJECTED,
    QUALITY_FLAG_CORE_PAYLOAD_INVALID,
    QUALITY_FLAG_GUARD_REJECTED,
    REJECTION_CANDIDATE_PRE_REJECTED,
    REJECTION_CANDIDATE_TEXT_MISSING,
    REJECTION_INVALID_CORE_TEXT_PAYLOAD,
    REJECTION_PAYLOAD_MINIMUM_NOT_MET,
    generated_result,
    rejected_result,
    unavailable_result,
)
from cocolon_text_generation_core.types import CoreTextPayload, TextGenerationResult

CORE_TEXT_COMPOSER_NAME = "cocolon_text_generation_core.core_text_composer.v1"


def _composer_model(payload: CoreTextPayload | None, candidate: CoreTextCandidate | None = None, default: str = DEFAULT_COMPOSER_MODEL) -> str:
    if candidate and candidate.composer_model:
        return candidate.composer_model
    if payload and getattr(payload, "composer_model", ""):
        return payload.composer_model
    return default


def _payload_meta(payload: CoreTextPayload, *, candidate: CoreTextCandidate | None = None) -> dict[str, Any]:
    return {
        "core_id": payload.core_id,
        "composer": CORE_TEXT_COMPOSER_NAME,
        "candidate": candidate.as_meta() if candidate else {},
    }


class CoreTextComposer:
    """Validate caller-supplied text candidates and fail closed on every gap."""

    composer_name = CORE_TEXT_COMPOSER_NAME

    def __init__(self, *, composer_model: str = DEFAULT_COMPOSER_MODEL) -> None:
        self.composer_model = composer_model or DEFAULT_COMPOSER_MODEL

    def _resolve_candidate(self, payload: CoreTextPayload, candidate: Any = None) -> CoreTextCandidate:
        if candidate is not None:
            return CoreTextCandidate.from_value(candidate)
        return CoreTextCandidate.from_payload_meta(payload.meta)

    def _run_guards(self, payload: CoreTextPayload, candidate: CoreTextCandidate) -> tuple[GuardResult, ...]:
        text = candidate.text
        return (
            guard_japanese_coherence(text, forbidden_surface_patterns=payload.forbidden_surface_patterns),
            guard_template_echo(
                text,
                evidence_spans=payload.evidence_spans,
                used_evidence_span_ids=candidate.used_evidence_span_ids,
                composer_meta=candidate.meta,
            ),
            guard_overclaim_diagnosis(text, core_id=payload.core_id, policy=payload.safety_policy),
            guard_grounding(
                text,
                evidence_spans=payload.evidence_spans,
                used_evidence_span_ids=candidate.used_evidence_span_ids,
                phrase_units=payload.phrase_units,
                used_phrase_unit_ids=candidate.used_phrase_unit_ids,
                sentence_bindings=payload.sentence_bindings,
            ),
            guard_must_keep_coverage(
                text,
                phrase_units=payload.phrase_units,
                sentence_plans=payload.sentence_plans,
                must_keep_roles=payload.must_keep_roles,
                used_evidence_span_ids=candidate.used_evidence_span_ids,
                used_phrase_unit_ids=candidate.used_phrase_unit_ids,
                require_text_for_must_keep=bool(payload.safety_policy.get("require_text_for_must_keep", False)),
            ),
        )

    def generate(self, payload: CoreTextPayload, candidate: Any = None) -> TextGenerationResult:
        """Return generated only when payload, candidate, and all guards pass.

        ``candidate`` is optional so the planned ``generate(payload)`` boundary
        works. When omitted, the candidate is read from ``payload.meta``. If no
        candidate is supplied, the result is fail-closed and text remains empty.
        """

        if not isinstance(payload, CoreTextPayload):
            return unavailable_result(
                (REJECTION_INVALID_CORE_TEXT_PAYLOAD,),
                composer_model=self.composer_model,
                quality_flags=(QUALITY_FLAG_PAYLOAD_INVALID, QUALITY_FLAG_CORE_PAYLOAD_INVALID),
                meta={"composer": CORE_TEXT_COMPOSER_NAME},
            )

        payload_reasons = payload.validate_minimum()
        if payload_reasons:
            return unavailable_result(
                (REJECTION_PAYLOAD_MINIMUM_NOT_MET,) + tuple(payload_reasons),
                composer_model=_composer_model(payload, default=self.composer_model),
                quality_flags=(QUALITY_FLAG_PAYLOAD_INVALID, QUALITY_FLAG_CORE_PAYLOAD_INVALID),
                meta={"core_id": payload.core_id, "composer": CORE_TEXT_COMPOSER_NAME, "payload_rejection_reasons": list(payload_reasons)},
            )

        resolved_candidate = self._resolve_candidate(payload, candidate)
        model = _composer_model(payload, resolved_candidate, self.composer_model)
        if not resolved_candidate.usable_text:
            return unavailable_result(
                (REJECTION_CANDIDATE_TEXT_MISSING,),
                composer_model=model,
                quality_flags=(QUALITY_FLAG_CANDIDATE_MISSING,),
                meta=_payload_meta(payload, candidate=resolved_candidate),
            )

        if resolved_candidate.pre_rejected:
            return rejected_result(
                (REJECTION_CANDIDATE_PRE_REJECTED,) + tuple(resolved_candidate.rejection_reasons),
                composer_model=model,
                quality_flags=tuple(resolved_candidate.quality_flags) + (QUALITY_FLAG_CANDIDATE_PRE_REJECTED,),
                meta=_payload_meta(payload, candidate=resolved_candidate),
            )

        guard_results = self._run_guards(payload, resolved_candidate)
        combined = combine_guard_results(guard_results)
        meta = _payload_meta(payload, candidate=resolved_candidate)
        meta.update(
            {
                "guard_results": [guard.as_meta() for guard in guard_results],
                "combined_guard_result": combined.as_meta(),
                "declared_used_evidence_span_ids": list(resolved_candidate.used_evidence_span_ids),
                "declared_used_phrase_unit_ids": list(resolved_candidate.used_phrase_unit_ids),
            }
        )
        if not combined.passed:
            return rejected_result(
                combined.rejection_reasons,
                composer_model=model,
                quality_flags=tuple(resolved_candidate.quality_flags)
                + tuple(combined.quality_flags)
                + (QUALITY_FLAG_CORE_COMPOSER_REJECTED, QUALITY_FLAG_GUARD_REJECTED),
                meta=meta,
            )

        return generated_result(
            resolved_candidate,
            composer_model=model,
            quality_flags=tuple(resolved_candidate.quality_flags),
            meta=meta,
        )

    def evaluate_candidate(self, payload: CoreTextPayload, candidate: Any) -> TextGenerationResult:
        """Explicit alias for callers that want to show the candidate boundary."""

        return self.generate(payload, candidate=candidate)

    def __call__(self, payload: CoreTextPayload, candidate: Any = None) -> TextGenerationResult:
        return self.generate(payload, candidate=candidate)


def generate_core_text(payload: CoreTextPayload, candidate: Any = None) -> TextGenerationResult:
    """Functional helper for tests and future adapters."""

    return CoreTextComposer().generate(payload, candidate=candidate)


__all__ = ["CORE_TEXT_COMPOSER_NAME", "CoreTextComposer", "generate_core_text"]
