# -*- coding: utf-8 -*-
from __future__ import annotations

"""Compatibility service for Step 8 Complete Binding-aware Grounding.

The primary implementation lives in ``emlis_ai_complete_grounding_binding`` and
``emlis_ai_grounding_judge``.  This module keeps a stable service-style import
surface for Step 9+ without changing public response shape.
"""

from dataclasses import asdict
from typing import Any, Mapping, Sequence

from emlis_ai_complete_grounding_binding import (
    COMPLETE_BINDING_AWARE_GROUNDING_IMPLEMENTATION_UNIT,
    COMPLETE_BINDING_AWARE_GROUNDING_STAGE,
    COMPLETE_BINDING_AWARE_GROUNDING_VERSION,
    build_complete_binding_aware_grounding_contract_meta,
    build_complete_grounding_binding_bundle,
    judge_complete_binding_aware_grounding as _judge_complete_binding_aware_grounding,
)
from emlis_ai_types import EvidenceSpan, GroundingReport, ObservationGraph

COMPLETE_GROUNDING_BINDING_VERSION = COMPLETE_BINDING_AWARE_GROUNDING_VERSION
COMPLETE_GROUNDING_BINDING_SERVICE_VERSION = COMPLETE_BINDING_AWARE_GROUNDING_VERSION
COMPLETE_GROUNDING_BINDING_STAGE = COMPLETE_BINDING_AWARE_GROUNDING_STAGE
COMPLETE_GROUNDING_BINDING_STEP = COMPLETE_BINDING_AWARE_GROUNDING_STAGE
COMPLETE_GROUNDING_BINDING_IMPLEMENTATION_UNIT = COMPLETE_BINDING_AWARE_GROUNDING_IMPLEMENTATION_UNIT


def build_complete_grounding_input(**kwargs: Any) -> dict[str, Any]:
    return build_complete_grounding_binding_bundle(**kwargs)


def build_complete_grounding_contract_meta() -> dict[str, Any]:
    meta = build_complete_binding_aware_grounding_contract_meta()
    meta.setdefault("binding_aware_grounding_strengthened", True)
    meta.setdefault("accepts_surface_realizer_grounding_input", True)
    meta.setdefault("requires_sentence_id", True)
    meta.setdefault("requires_used_evidence_span_ids", True)
    meta.setdefault("requires_used_phrase_unit_ids", True)
    meta.setdefault("requires_relation_type", True)
    return meta


def judge_complete_binding_aware_grounding(
    *,
    graph: ObservationGraph,
    evidence_spans: Sequence[EvidenceSpan],
    comment_text: str | None = None,
    grounding_input: Mapping[str, Any] | None = None,
    surface_realization: Any = None,
    sentence_plan: Any = None,
    allowed_evidence_span_ids: Sequence[str] | None = None,
    coverage_group: str | None = None,
    meta: Mapping[str, Any] | None = None,
) -> GroundingReport:
    return _judge_complete_binding_aware_grounding(
        graph=graph,
        evidence_spans=evidence_spans,
        comment_text=comment_text,
        grounding_input=grounding_input,
        surface_realization=surface_realization,
        sentence_plan=sentence_plan,
        allowed_evidence_span_ids=allowed_evidence_span_ids,
        coverage_group=coverage_group,
        meta=meta,
    )


def build_complete_grounding_report_meta(report: GroundingReport) -> dict[str, Any]:
    return {
        **build_complete_grounding_contract_meta(),
        "passed": report.passed,
        "coverage_ratio": report.coverage_ratio,
        "confidence": report.confidence,
        "rejection_reasons": list(report.rejection_reasons),
        "binding_present": report.binding_present,
        "binding_used": report.binding_used,
        "binding_missing": report.binding_missing,
        "binding_count": report.binding_count,
        "expected_binding_count": report.expected_binding_count,
        "binding_supported_sentence_count": report.binding_supported_sentence_count,
        "binding_rejection_reasons": list(report.binding_rejection_reasons),
        "declared_relation_types": list(report.declared_relation_types),
        "declared_phrase_unit_ids": list(report.declared_phrase_unit_ids),
        "binding_diagnostics": dict(report.binding_diagnostics),
        "sentence_claims": [asdict(claim) for claim in report.sentence_claims],
        "raw_input_included": False,
        "response_shape_changed": False,
    }


def build_complete_grounding_meta(**kwargs: Any) -> dict[str, Any]:
    return build_complete_grounding_report_meta(judge_complete_binding_aware_grounding(**kwargs))


judge_complete_grounding = judge_complete_binding_aware_grounding
build_complete_binding_grounding_meta = build_complete_grounding_meta

__all__ = [
    "COMPLETE_GROUNDING_BINDING_IMPLEMENTATION_UNIT",
    "COMPLETE_GROUNDING_BINDING_SERVICE_VERSION",
    "COMPLETE_GROUNDING_BINDING_STAGE",
    "COMPLETE_GROUNDING_BINDING_STEP",
    "COMPLETE_GROUNDING_BINDING_VERSION",
    "build_complete_binding_grounding_meta",
    "build_complete_grounding_contract_meta",
    "build_complete_grounding_input",
    "build_complete_grounding_meta",
    "build_complete_grounding_report_meta",
    "judge_complete_binding_aware_grounding",
    "judge_complete_grounding",
]
