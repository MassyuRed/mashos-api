# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from emlis_ai_complete_reply_diagnostics_service import build_complete_scorecard_event
from emlis_ai_complete_scorecard_service import aggregate_complete_scorecard_events, normalize_complete_scorecard_event
from emlis_ai_complete_surface_realizer import build_complete_surface_realization_v2, build_complete_surface_realizer_contract_meta
from emlis_ai_complete_tone_policy import (
    COMPLETE_PRODUCT_QUALITY_TONE_ENGINE_VERSION,
    COMPLETE_TONE_ENGINE_STAGE,
    COMPLETE_TONE_ENGINE_VERSION,
    COMPLETE_TONE_POLICY_VERSION,
    build_complete_tone_guard_report,
    build_complete_tone_policy,
    build_complete_tone_policy_contract_meta,
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


def test_step5_tone_engine_contract_is_surface_constraint_not_post_decoration() -> None:
    contract = build_complete_tone_policy_contract_meta()
    surface_contract = build_complete_surface_realizer_contract_meta()

    assert contract["product_quality_step"] == COMPLETE_TONE_ENGINE_STAGE
    assert contract["tone_engine_version"] == COMPLETE_TONE_ENGINE_VERSION
    assert contract["product_quality_tone_engine_version"] == COMPLETE_PRODUCT_QUALITY_TONE_ENGINE_VERSION
    assert contract["tone_policy_added"] is True
    assert contract["tone_is_surface_constraint_not_post_decoration"] is True
    assert contract["surface_realizer_constraint"] is True
    assert contract["post_gate_decoration"] is False
    assert contract["meaning_added"] is False
    assert contract["meaning_added_allowed"] is False
    assert contract["fixed_comfort_sentence_added"] is False
    assert contract["comment_text_contract"] == "passed_only"
    assert contract["comment_text_key_written"] is False
    assert contract["display_gate_relaxed"] is False
    assert contract["response_shape_changed"] is False
    assert contract["raw_input_included"] is False
    assert surface_contract["tone_engine_added"] is True
    assert surface_contract["tone_policy_contract"]["tone_policy_added"] is True


def test_step5_policy_maps_desire_fear_to_non_advice_distance_and_guards() -> None:
    realization = build_complete_surface_realization_v2(sentence_plan_seed=_desire_fear_seed())
    policy = build_complete_tone_policy(
        sentence_plan=realization.source_sentence_plan,
        coverage_group="desire_fear",
        relation_types=realization.relation_types,
    )
    meta = policy.as_meta()

    assert meta["coverage_group"] == "desire_fear"
    assert meta["tone_policy_applies_to_sentence_plan"] is True
    assert meta["non_diagnostic_policy_enabled"] is True
    assert meta["non_advice_policy_enabled"] is True
    assert "approach_avoidance" in meta["relation_types"]
    assert "advice_like" in meta["guard_keys"]
    assert "action_instruction" in meta["guard_keys"]
    assert all(line["non_advice"] is True for line in meta["line_constraints"])
    assert all(line["non_diagnostic"] is True for line in meta["line_constraints"])
    assert all(line["meaning_added"] is False for line in meta["line_constraints"])
    assert any(line["distance_policy_key"] == "hold_approach_and_avoidance_without_advice" for line in meta["line_constraints"])


def test_step5_surface_realizer_applies_tone_policy_without_meaning_addition() -> None:
    realization = build_complete_surface_realization_v2(sentence_plan_seed=_desire_fear_seed())
    meta = realization.as_meta()

    assert realization.ready is True
    assert meta["tone_engine_version"] == COMPLETE_TONE_ENGINE_VERSION
    assert meta["tone_policy_version"] == COMPLETE_TONE_POLICY_VERSION
    assert meta["product_quality_tone_engine_version"] == COMPLETE_PRODUCT_QUALITY_TONE_ENGINE_VERSION
    assert meta["tone_policy_applied"] is True
    assert meta["tone_guard_major_count"] == 0
    assert meta["tone_guard_passed"] is True
    assert meta["over_empathy_guard_passed"] is True
    assert meta["diagnostic_tone_guard_passed"] is True
    assert meta["advice_like_guard_passed"] is True
    assert meta["generic_comfort_guard_passed"] is True
    assert meta["meaning_added_by_tone_policy"] is False
    assert meta["tone_is_surface_constraint_not_post_decoration"] is True
    assert "あなた" not in realization.realized_text
    assert "してください" not in realization.realized_text
    assert "もう大丈夫" not in realization.realized_text
    assert "診断" not in realization.realized_text
    for line in realization.surface_lines:
        row = line.as_meta()
        assert row["tone_policy_key"]
        assert row["temperature_key"]
        assert row["tone_engine_version"] == COMPLETE_TONE_ENGINE_VERSION
        assert row["tone_meaning_added"] is False
        assert row["surface_signature"]["tone_policy_key"] == row["tone_policy_key"]


def test_step5_tone_guard_blocks_diagnostic_advice_and_over_empathy() -> None:
    policy = build_complete_tone_policy(coverage_group="pressure", relation_types=["pressure"])
    report = build_complete_tone_guard_report(
        comment_text="診断として、まずは行動しましょう。もう大丈夫です。",
        tone_policy=policy,
    )

    assert report["release_blocker"] is True
    assert report["passed"] is False
    assert report["tone_guard_major_count"] >= 3
    assert report["diagnostic_tone_count"] >= 1
    assert report["advice_like_count"] >= 1
    assert report["over_empathy_count"] >= 1
    assert "diagnostic_tone" in report["tone_guard_reasons"]
    assert "advice_like" in report["tone_guard_reasons"]
    assert report["meaning_added_by_tone_policy"] is False
    assert report["display_gate_relaxed"] is False


def test_step5_template_guard_consumes_tone_guard_report_fail_closed() -> None:
    tone_report = build_complete_tone_guard_report(
        comment_text="診断として、まずは行動しましょう。もう大丈夫です。",
        tone_policy=build_complete_tone_policy(coverage_group="pressure", relation_types=["pressure"]),
    )

    report = guard_template_echo(
        comment_text="根拠のある範囲で、圧力が残っています。",
        evidence_spans=[_span("span-pressure", "圧力が残っている")],
        composer_source="ai_generated",
        composer_model="cocolon_emlis_observation_composer.a1.v1",
        generation_method="complete_initial_binding_first_composer",
        composer_meta={"tone_guard_report": tone_report},
        used_evidence_span_ids=["span-pressure"],
    )

    assert report.passed is False
    assert "tone_guard_major" in report.rejection_reasons
    assert "tone_guard:diagnostic_tone" in report.rejection_reasons
    assert "tone_guard:advice_like" in report.rejection_reasons


def test_step5_scorecard_event_and_aggregate_track_tone_guard_metrics() -> None:
    realization = build_complete_surface_realization_v2(sentence_plan_seed=_desire_fear_seed())
    runtime_meta = realization.as_meta()
    candidate = {
        "status": "generated",
        "composer_source": "ai_generated",
        "composer_model": "cocolon_emlis_observation_composer.a1.v1",
        "generation_method": "complete_initial_binding_first_composer",
        "coverage_scope": "desire_fear",
        "used_evidence_span_ids": list(realization.used_evidence_span_ids),
        "used_relation_ids": list(realization.relation_types),
        "composer_meta": {
            "complete_composer_client_added": True,
            "coverage_group": "desire_fear",
            "used_phrase_unit_ids": list(realization.used_phrase_unit_ids),
            "binding_meta": {"binding_count": len(tuple(realization.surface_lines))},
            "final_grounding_report": {
                "binding_used": True,
                "binding_supported_sentence_count": len(tuple(realization.surface_lines)),
                "expected_binding_count": len(tuple(realization.surface_lines)),
            },
            "tone_engine_version": runtime_meta["tone_engine_version"],
            "product_quality_tone_engine_version": runtime_meta["product_quality_tone_engine_version"],
            "tone_policy_applied": True,
            "tone_guard_report": runtime_meta["tone_guard_report"],
        },
    }
    display = {"observation_status": "passed", "rejection_reasons": []}

    event = build_complete_scorecard_event(composer_candidate=candidate, display_decision=display)
    normalized = normalize_complete_scorecard_event(event)
    aggregate = aggregate_complete_scorecard_events([event])

    assert event["tone_guard_major_count"] == 0
    assert event["tone_guard_passed"] is True
    assert event["tone_policy_applied"] is True
    assert normalized["tone_guard_major_count"] == 0
    assert normalized["tone_guard_passed"] is True
    assert normalized["tone_meaning_added"] is False
    assert aggregate["tone_guard_major_count"] == 0
    assert aggregate["tone_meaning_added_count"] == 0
    assert "tone_guard_major_detected" not in aggregate["release_blockers"]

    rejected = normalize_complete_scorecard_event(
        {
            "version": "emlis.complete_scorecard_event.v1",
            "event_kind": "complete_composer_initial_reply_attempt",
            "complete_candidate_seen": True,
            "complete_candidate_generated": True,
            "eligible_count": 1,
            "candidate_generated_count": 1,
            "observation_status": "rejected",
            "coverage_group": "pressure",
            "tone_guard_major_count": 1,
            "tone_guard_reasons": ["advice_like"],
            "tone_meaning_added": False,
        }
    )
    assert rejected["tone_guard_major_count"] == 1
    assert rejected["safety_major_count"] >= 1
    assert "advice_like" in rejected["top_rejection_reasons"]
