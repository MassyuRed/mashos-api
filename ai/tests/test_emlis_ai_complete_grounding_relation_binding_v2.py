# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy

from emlis_ai_complete_grounding_service import (
    COMPLETE_PRODUCT_QUALITY_GROUNDING_VERSION,
    GATE_BINDING_CONTRACT_VERSION,
    build_complete_product_quality_grounding_contract_meta,
    build_complete_product_quality_grounding_report_v2,
    judge_complete_product_quality_grounding,
)
from emlis_ai_types import EvidenceSpan, GraphClaim, ObservationGraph, RelationEdge


def _span(span_id: str, raw_text: str) -> EvidenceSpan:
    return EvidenceSpan(span_id=span_id, raw_text=raw_text, detected_type="feeling", source_field="memo")


def _graph() -> ObservationGraph:
    return ObservationGraph(
        primary_state=GraphClaim(
            claim_id="claim-primary",
            claim_type="coexistence",
            text="近づきたい気持ちと止まりたい怖さが同居している",
            evidence_span_ids=["span-wish", "span-fear"],
            confidence=0.9,
        ),
        core_tensions=[
            RelationEdge(
                edge_id="rel-approach-fear",
                from_claim_id="claim-wish",
                to_claim_id="claim-fear",
                relation_type="approach_avoidance",
                evidence_span_ids=["span-wish", "span-fear"],
                confidence=0.87,
            )
        ],
    )


def _grounding_input() -> dict:
    return {
        "coverage_group": "desire_fear",
        "realized_text": "同時に、近づきたい気持ちと止まりたい怖さが同じ中にあります。近づく動きと止まる動きの両方が、一方向に決まりきっていません。",
        "surface_lines": [
            {
                "sentence_id": "complete-s1",
                "surface_text": "同時に、近づきたい気持ちと止まりたい怖さが同じ中にあります。",
                "line_role": "relation",
                "relation_type": "coexistence",
                "used_evidence_span_ids": ["span-wish"],
                "used_phrase_unit_ids": ["pu-wish"],
                "phrase_unit_roles": ["wish"],
                "phrase_unit_polarities": ["approach"],
                "relation_expression_required": True,
            },
            {
                "sentence_id": "complete-s2",
                "surface_text": "近づく動きと止まる動きの両方が、一方向に決まりきっていません。",
                "line_role": "relation",
                "relation_type": "approach_avoidance",
                "used_evidence_span_ids": ["span-fear"],
                "used_phrase_unit_ids": ["pu-fear"],
                "phrase_unit_roles": ["fear"],
                "phrase_unit_polarities": ["avoidance"],
                "relation_expression_required": True,
            },
        ],
    }


def _evidence() -> list[EvidenceSpan]:
    # The surface lines intentionally do not depend on raw-text substring match.
    # Step2 should pass through declared evidence / phrase / relation binding.
    return [_span("span-wish", "anchor alpha"), _span("span-fear", "anchor beta")]


def test_product_quality_grounding_contract_exposes_relation_binding_v2_fields():
    meta = build_complete_product_quality_grounding_contract_meta()

    assert meta["version"] == COMPLETE_PRODUCT_QUALITY_GROUNDING_VERSION
    assert meta["gate_binding_contract_version"] == GATE_BINDING_CONTRACT_VERSION
    assert meta["relation_expression_checker"] is True
    assert meta["phrase_unit_role_or_polarity_required"] is True
    assert meta["grounding_gate_relaxed"] is False
    assert meta["raw_input_included"] is False


def test_product_quality_grounding_uses_declared_relation_binding_without_surface_overlap():
    report = judge_complete_product_quality_grounding(
        graph=_graph(),
        evidence_spans=_evidence(),
        grounding_input=_grounding_input(),
        coverage_group="desire_fear",
    )
    report_v2 = build_complete_product_quality_grounding_report_v2(report)

    assert report.passed is True
    assert report.binding_used is True
    assert report_v2["binding_used"] is True
    assert report_v2["binding_supported_sentence_count"] == 2
    assert report_v2["binding_pass_rate"] == 1.0
    assert report_v2["binding_support_source"] == "declared_relation_binding"
    assert report_v2["unsupported_sentence_ids"] == []
    assert report_v2["relation_not_expressed_sentence_ids"] == []
    assert report_v2["release_blocker"] is False


def test_product_quality_grounding_fails_when_relation_is_not_expressed():
    grounding_input = deepcopy(_grounding_input())
    grounding_input["realized_text"] = "近づきたい気持ちがあります。近づく動きと止まる動きの両方が、一方向に決まりきっていません。"
    grounding_input["surface_lines"][0]["surface_text"] = "近づきたい気持ちがあります。"
    grounding_input["surface_lines"][0]["relation_type"] = "coexistence"

    report = judge_complete_product_quality_grounding(
        graph=_graph(),
        evidence_spans=_evidence(),
        grounding_input=grounding_input,
        coverage_group="desire_fear",
    )
    report_v2 = build_complete_product_quality_grounding_report_v2(report)

    assert report.passed is False
    assert "relation_not_expressed" in report.rejection_reasons
    assert report_v2["relation_not_expressed_sentence_ids"] == ["complete-s1"]
    assert report_v2["repair_handoff"]["relation_not_expressed"]["operation"] == "make_relation_line_explicit_or_rewrite_connector"


def test_product_quality_grounding_reports_phrase_unit_missing():
    grounding_input = deepcopy(_grounding_input())
    grounding_input["surface_lines"][0]["used_phrase_unit_ids"] = []
    grounding_input["surface_lines"][0]["phrase_unit_roles"] = []
    grounding_input["surface_lines"][0]["phrase_unit_polarities"] = []

    report = judge_complete_product_quality_grounding(
        graph=_graph(),
        evidence_spans=_evidence(),
        grounding_input=grounding_input,
        coverage_group="desire_fear",
    )
    report_v2 = build_complete_product_quality_grounding_report_v2(report)

    assert report.passed is False
    assert "complete_binding_phrase_unit_ids_missing" in report.rejection_reasons
    assert report_v2["phrase_unit_missing_sentence_ids"] == ["complete-s1"]
    assert report_v2["repair_handoff"]["phrase_unit_missing"]["return_step"] == "material_service"


def test_product_quality_grounding_keeps_overclaim_and_raw_echo_as_release_blockers():
    overclaim_input = deepcopy(_grounding_input())
    overclaim_input["realized_text"] = "同時に、本当は誰かに頼りたい本当の願いが同じ中にあります。近づく動きと止まる動きの両方が、一方向に決まりきっていません。"
    overclaim_input["surface_lines"][0]["surface_text"] = "同時に、本当は誰かに頼りたい本当の願いが同じ中にあります。"
    overclaim_report = judge_complete_product_quality_grounding(
        graph=_graph(),
        evidence_spans=_evidence(),
        grounding_input=overclaim_input,
        coverage_group="desire_fear",
    )
    overclaim_v2 = build_complete_product_quality_grounding_report_v2(overclaim_report)

    assert overclaim_report.passed is False
    assert overclaim_v2["overclaim_sentence_ids"] == ["complete-s1"]
    assert overclaim_v2["release_blocker"] is True

    raw_echo_input = deepcopy(_grounding_input())
    raw_echo_input["realized_text"] = "同時に、近づきたい気持ちと止まりたい怖さが同じ中にあります。近づく動きと止まる動きの両方が、一方向に決まりきっていません。"
    raw_echo_report = judge_complete_product_quality_grounding(
        graph=_graph(),
        evidence_spans=[
            _span("span-wish", "同時に、近づきたい気持ちと止まりたい怖さが同じ中にあります。"),
            _span("span-fear", "anchor beta"),
        ],
        grounding_input=raw_echo_input,
        coverage_group="desire_fear",
    )
    raw_echo_v2 = build_complete_product_quality_grounding_report_v2(raw_echo_report)

    assert raw_echo_report.passed is False
    assert raw_echo_v2["raw_echo_sentence_ids"] == ["complete-s1"]
    assert raw_echo_v2["release_blocker"] is True
