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
    COMPLETE_PRODUCT_QUALITY_GROUNDING_STEP,
    COMPLETE_PRODUCT_QUALITY_GROUNDING_VERSION,
    GATE_BINDING_CONTRACT_VERSION,
    build_complete_binding_aware_grounding_contract_meta,
    build_complete_grounding_binding_bundle,
    judge_complete_binding_aware_grounding as _judge_complete_binding_aware_grounding,
)
from emlis_ai_types import EvidenceSpan, GroundingReport, ObservationGraph

COMPLETE_GROUNDING_BINDING_VERSION = COMPLETE_BINDING_AWARE_GROUNDING_VERSION
COMPLETE_GROUNDING_BINDING_SERVICE_VERSION = COMPLETE_BINDING_AWARE_GROUNDING_VERSION
COMPLETE_PRODUCT_QUALITY_GROUNDING_SERVICE_VERSION = COMPLETE_PRODUCT_QUALITY_GROUNDING_VERSION
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
    meta.setdefault("product_quality_grounding_version", COMPLETE_PRODUCT_QUALITY_GROUNDING_VERSION)
    meta.setdefault("product_quality_grounding_step", COMPLETE_PRODUCT_QUALITY_GROUNDING_STEP)
    meta.setdefault("grounding_report_contract_version", COMPLETE_PRODUCT_QUALITY_GROUNDING_VERSION)
    meta.setdefault("binding_contract_version", GATE_BINDING_CONTRACT_VERSION)
    meta.setdefault("gate_binding_contract_version", GATE_BINDING_CONTRACT_VERSION)
    meta.setdefault("relation_expression_checker", True)
    meta.setdefault("binding_support_source_required", True)
    meta.setdefault("unsupported_sentence_ids_reported", True)
    meta.setdefault("relation_not_expressed_sentence_ids_reported", True)
    return meta


def build_complete_product_quality_grounding_contract_meta() -> dict[str, Any]:
    """Return the Step2 product-quality Grounding contract meta.

    This remains additive: it describes the stronger Grounding checks without
    changing the public response shape or RN passed-only contract.
    """

    meta = build_complete_grounding_contract_meta()
    meta.update(
        {
            "version": COMPLETE_PRODUCT_QUALITY_GROUNDING_VERSION,
            "service_version": COMPLETE_PRODUCT_QUALITY_GROUNDING_SERVICE_VERSION,
            "target_step": COMPLETE_PRODUCT_QUALITY_GROUNDING_STEP,
            "step": COMPLETE_PRODUCT_QUALITY_GROUNDING_STEP,
            "stage": "complete_product_quality_connection_grounding",
            "binding_contract_version": GATE_BINDING_CONTRACT_VERSION,
            "gate_binding_contract_version": GATE_BINDING_CONTRACT_VERSION,
            "binding_used_contract": "binding_used_means_gate_judgment_used_binding",
            "sentence_evidence_required": True,
            "phrase_unit_role_or_polarity_required": True,
            "relation_expression_checker": True,
            "relation_expression_checked": True,
            "binding_support_source_required": True,
            "unsupported_sentence_ids_reported": True,
            "relation_not_expressed_sentence_ids_reported": True,
            "release_blocker_reported": True,
            "grounding_gate_relaxed": False,
            "display_gate_relaxed": False,
            "response_shape_changed": False,
            "raw_input_included": False,
        }
    )
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


def judge_complete_product_quality_grounding(
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
    product_meta = {"product_quality_grounding": True, "grounding_relation_binding_v2": True}
    if isinstance(meta, Mapping):
        product_meta.update(dict(meta))
    return _judge_complete_binding_aware_grounding(
        graph=graph,
        evidence_spans=evidence_spans,
        comment_text=comment_text,
        grounding_input=grounding_input,
        surface_realization=surface_realization,
        sentence_plan=sentence_plan,
        allowed_evidence_span_ids=allowed_evidence_span_ids,
        coverage_group=coverage_group,
        meta=product_meta,
    )


def build_complete_product_quality_grounding_report_v2(report: GroundingReport) -> dict[str, Any]:
    payload = dict(report.grounding_report_v2 or {})
    if not payload:
        payload = dict(report.binding_diagnostics.get("grounding_report_v2") or {})
    if not payload:
        payload = {
            "version": COMPLETE_PRODUCT_QUALITY_GROUNDING_VERSION,
            "target_step": COMPLETE_PRODUCT_QUALITY_GROUNDING_STEP,
            "binding_contract_version": GATE_BINDING_CONTRACT_VERSION,
            "gate_binding_contract_version": GATE_BINDING_CONTRACT_VERSION,
            "binding_used": bool(report.binding_used),
            "binding_present": bool(report.binding_present),
            "binding_missing": bool(report.binding_missing),
            "binding_count": int(report.binding_count),
            "expected_binding_count": int(report.expected_binding_count),
            "binding_supported_sentence_count": int(report.binding_supported_sentence_count),
            "binding_pass_rate": float(report.binding_pass_rate or 0.0),
            "binding_support_source": str(report.binding_support_source or "none"),
            "unsupported_sentence_ids": list(report.unsupported_sentence_ids),
            "relation_not_expressed_sentence_ids": list(report.relation_not_expressed_sentence_ids),
            "phrase_unit_missing_sentence_ids": list(report.phrase_unit_missing_sentence_ids),
            "weak_material_sentence_ids": list(report.weak_material_sentence_ids),
            "raw_echo_sentence_ids": list(report.raw_echo_sentence_ids),
            "overclaim_sentence_ids": list(report.overclaim_sentence_ids),
            "release_blocker": bool(report.release_blocker or report.rejection_reasons),
        }
    payload.setdefault("version", COMPLETE_PRODUCT_QUALITY_GROUNDING_VERSION)
    payload.setdefault("target_step", COMPLETE_PRODUCT_QUALITY_GROUNDING_STEP)
    payload.setdefault("binding_contract_version", GATE_BINDING_CONTRACT_VERSION)
    payload.setdefault("gate_binding_contract_version", GATE_BINDING_CONTRACT_VERSION)
    payload.setdefault("response_shape_changed", False)
    payload.setdefault("raw_input_included", False)
    payload.setdefault("grounding_gate_relaxed", False)
    payload.setdefault("display_gate_relaxed", False)
    return payload


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
        "binding_pass_rate": report.binding_pass_rate,
        "binding_support_source": report.binding_support_source,
        "unsupported_sentence_ids": list(report.unsupported_sentence_ids),
        "relation_not_expressed_sentence_ids": list(report.relation_not_expressed_sentence_ids),
        "phrase_unit_missing_sentence_ids": list(report.phrase_unit_missing_sentence_ids),
        "weak_material_sentence_ids": list(report.weak_material_sentence_ids),
        "raw_echo_sentence_ids": list(report.raw_echo_sentence_ids),
        "overclaim_sentence_ids": list(report.overclaim_sentence_ids),
        "release_blocker": report.release_blocker,
        "grounding_report_v2": dict(report.grounding_report_v2),
        "product_quality_grounding_report": build_complete_product_quality_grounding_report_v2(report),
        "grounding_report_contract_version": report.grounding_report_contract_version or COMPLETE_PRODUCT_QUALITY_GROUNDING_VERSION,
        "binding_contract_version": report.binding_contract_version or GATE_BINDING_CONTRACT_VERSION,
        "gate_binding_contract_version": report.gate_binding_contract_version or GATE_BINDING_CONTRACT_VERSION,
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
    "COMPLETE_PRODUCT_QUALITY_GROUNDING_SERVICE_VERSION",
    "COMPLETE_PRODUCT_QUALITY_GROUNDING_STEP",
    "COMPLETE_PRODUCT_QUALITY_GROUNDING_VERSION",
    "GATE_BINDING_CONTRACT_VERSION",
    "COMPLETE_GROUNDING_BINDING_STAGE",
    "COMPLETE_GROUNDING_BINDING_STEP",
    "COMPLETE_GROUNDING_BINDING_VERSION",
    "build_complete_binding_grounding_meta",
    "build_complete_grounding_contract_meta",
    "build_complete_product_quality_grounding_contract_meta",
    "build_complete_product_quality_grounding_report_v2",
    "build_complete_grounding_input",
    "build_complete_grounding_meta",
    "build_complete_grounding_report_meta",
    "judge_complete_binding_aware_grounding",
    "judge_complete_grounding",
    "judge_complete_product_quality_grounding",
]
