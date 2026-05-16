# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from emlis_ai_complete_scorecard_service import normalize_complete_scorecard_event
from emlis_ai_complete_surface_realizer import (
    COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_SCHEMA_VERSION,
    COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_STEP,
    COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_VERSION,
    build_complete_product_quality_surface_variation_report,
    build_complete_surface_realization_v2,
    build_complete_surface_realizer_contract_meta,
)
from emlis_ai_template_echo_guard import guard_template_echo
from emlis_ai_types import EvidenceSpan


def _span(span_id: str, raw_text: str = "anchor material") -> EvidenceSpan:
    return EvidenceSpan(span_id=span_id, raw_text=raw_text, detected_type="feeling", source_field="memo")


def _desire_fear_seed() -> dict[str, Any]:
    return {
        "coverage_group": "desire_fear",
        "sentence_budget": 3,
        "graph_nodes": [
            {
                "node_id": "n-wish",
                "material_id": "m-wish",
                "phrase_unit_id": "pu-wish",
                "evidence_span_id": "span-wish",
                "role": "value_wish",
                "relation_type": "approach_avoidance",
                "must_keep": True,
                "source_anchor_present": True,
            },
            {
                "node_id": "n-fear",
                "material_id": "m-fear",
                "phrase_unit_id": "pu-fear",
                "evidence_span_id": "span-fear",
                "role": "avoidance_wish",
                "relation_type": "approach_avoidance",
                "must_keep": True,
                "source_anchor_present": True,
            },
        ],
    }


def test_step3_surface_variation_contract_is_additive_and_not_fallback() -> None:
    meta = build_complete_surface_realizer_contract_meta()

    assert meta["product_quality_surface_variation_added"] is True
    assert meta["product_quality_surface_variation_version"] == COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_VERSION
    assert meta["product_quality_surface_variation_step"] == COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_STEP
    assert meta["surface_variation_strengthened"] is True
    assert meta["surface_signature_to_template_guard"] is True
    assert meta["same_ending_guard_enabled"] is True
    assert meta["surface_signature_repeat_guard_enabled"] is True
    assert meta["comment_text_generated"] is False
    assert meta["comment_text_key_written"] is False
    assert meta["fixed_sentence_template_added"] is False
    assert meta["external_ai_used"] is False
    assert meta["local_llm_used"] is False
    assert meta["response_shape_changed"] is False
    assert meta["raw_input_included"] is False


def test_step3_desire_fear_surface_keeps_plan_binding_and_variation_report() -> None:
    realization = build_complete_surface_realization_v2(sentence_plan_seed=_desire_fear_seed())
    report = build_complete_product_quality_surface_variation_report(realization)

    assert realization.ready is True
    assert realization.coverage_group == "desire_fear"
    assert report["version"] == COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_SCHEMA_VERSION
    assert report["surface_variation_version"] == COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_VERSION
    assert report["surface_variation_step"] == COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_STEP
    assert report["coverage_group"] == "desire_fear"
    assert report["surface_line_count"] == len(tuple(realization.surface_lines))
    assert report["surface_signature_count"] == len(tuple(realization.surface_lines))
    assert report["same_ending_major_count"] == 0
    assert report["surface_signature_repeat_count"] == 0
    assert report["release_blocker"] is False
    assert report["passed"] is True
    assert report["comment_text_key_written"] is False
    assert report["public_comment_text_assigned"] is False
    assert report["fixed_sentence_template_used"] is False
    assert report["raw_input_included"] is False
    assert set(report["used_evidence_span_ids"]) == {"span-wish", "span-fear"}
    assert set(report["used_phrase_unit_ids"]) == {"pu-wish", "pu-fear"}
    assert set(report["relation_types"]) == {"approach_avoidance"}
    assert "あなた" not in realization.realized_text
    assert "かもしれません" not in realization.realized_text


def test_step3_template_guard_rejects_surface_signature_repeat_and_same_ending() -> None:
    rows = [
        {
            "sentence_id": "s1",
            "signature": "core:pressure:load:core_inside:が:pressure_foreground:aru:observe",
            "connector_key": "core_inside",
            "ending_key": "aru",
            "completion_sentence_template_used": False,
            "raw_input_included": False,
        },
        {
            "sentence_id": "s2",
            "signature": "core:pressure:load:core_inside:が:pressure_foreground:aru:observe",
            "connector_key": "core_inside",
            "ending_key": "aru",
            "completion_sentence_template_used": False,
            "raw_input_included": False,
        },
        {
            "sentence_id": "s3",
            "signature": "relation:pressure:load:core_inside:が:pressure_remain:aru:observe",
            "connector_key": "core_inside",
            "ending_key": "aru",
            "completion_sentence_template_used": False,
            "raw_input_included": False,
        },
    ]
    report = guard_template_echo(
        comment_text="根拠のある範囲で一文目を置いています。別の根拠に沿って二文目を置いています。関係だけを三文目に置いています。",
        evidence_spans=[_span("span-a", "alpha anchor"), _span("span-b", "beta anchor")],
        composer_source="ai_generated",
        composer_model="cocolon_emlis_observation_composer.a1.v1",
        generation_method="complete_initial_binding_first_composer",
        composer_meta={"surface_signature": {"surface_signature_rows": rows}},
        used_evidence_span_ids=["span-a", "span-b"],
    )

    assert report.passed is False
    assert report.surface_signature_row_count == 3
    assert report.surface_signature_repeat_count == 1
    assert report.same_ending_major_count == 1
    assert report.surface_connector_repetition_count == 1
    assert "surface_signature_repeat" in report.rejection_reasons
    assert "same_ending_major" in report.rejection_reasons
    assert "surface_connector_repetition" in report.rejection_reasons


def test_step3_scorecard_counts_surface_signature_repeat_as_template_major() -> None:
    normalized = normalize_complete_scorecard_event(
        {
            "version": "emlis.complete_scorecard_event.v1",
            "event_kind": "complete_composer_initial_reply_attempt",
            "complete_candidate_seen": True,
            "complete_candidate_generated": True,
            "complete_candidate_displayed": False,
            "eligible_count": 1,
            "passed_display_count": 0,
            "candidate_generated_count": 1,
            "observation_status": "rejected",
            "coverage_group": "desire_fear",
            "binding_pass": False,
            "binding_count": 2,
            "relation_types": ["approach_avoidance"],
            "gate_rejection_reasons": ["surface_signature_repeat"],
            "raw_input_included": False,
            "comment_text_included": False,
        }
    )

    assert normalized["coverage_group"] == "desire_fear"
    assert normalized["template_major_count"] >= 1
    assert "surface_signature_repeat" in normalized["top_rejection_reasons"]
    assert normalized["raw_input_included"] is False
