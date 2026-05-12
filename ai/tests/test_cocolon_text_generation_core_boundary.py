# -*- coding: utf-8 -*-
from __future__ import annotations

from cocolon_text_generation_core.composer import CoreTextComposer
from cocolon_text_generation_core.policies import CORE_ID_ANALYSIS, CORE_ID_EMLIS
from cocolon_text_generation_core.result import CoreTextCandidate
from cocolon_text_generation_core.types import CoreTextPayload, EvidenceSpanLike, PhraseUnit, SentencePlan, SourceAnchor


def _single_span_payload(*, core_id: str, role: str, raw_text: str) -> tuple[CoreTextPayload, str, str]:
    anchor = SourceAnchor(source_id=f"{core_id}-source", field="memo", raw_text=raw_text)
    span = EvidenceSpanLike(span_id=f"{core_id}-span-1", source_anchor=anchor, raw_text=raw_text, role=role)
    unit = PhraseUnit(
        phrase_unit_id=f"{core_id}-unit-1",
        evidence_span_id=span.span_id,
        text=raw_text,
        role=role,
        must_keep=True,
    )
    plan = SentencePlan(
        sentence_plan_id=f"{core_id}-plan-1",
        phrase_unit_ids=(unit.phrase_unit_id,),
        relation_type="boundary_contract",
        line_role=role,
        must_include=True,
    )
    payload = CoreTextPayload(
        core_id=core_id,
        source_anchors=(anchor,),
        evidence_spans=(span,),
        phrase_units=(unit,),
        sentence_plans=(plan,),
        must_keep_roles=(role,),
        safety_policy={"core_id": core_id},
        composer_model="cocolon_text_generation_core.boundary_test.v1",
    )
    return payload, span.span_id, unit.phrase_unit_id


def test_core_boundary_contract_registry_keeps_three_outputs_separated() -> None:
    import core_contract_registry as registry

    contracts = {entry.core_id: entry for entry in registry.iter_core_contracts()}

    assert set(contracts) == {"emlis_ai", "piece", "analysis"}
    assert contracts["emlis_ai"].primary_route == "POST /emotion/submit"
    assert "input_feedback.comment_text" in (contracts["emlis_ai"].notes or "")
    assert contracts["piece"].primary_route == "POST /emotion/piece/preview + POST /emotion/piece/publish"
    assert contracts["piece"].publish_policy == "preview_ready_to_published_status_only"
    assert "mymodel_reflections" in contracts["piece"].storage_owner
    assert contracts["analysis"].primary_route == "/analysis/* + /self-structure/*"
    assert "content_json" in contracts["analysis"].storage_owner
    assert contracts["analysis"].quality_gate == "analysis_report_validity_gate"


def test_emlis_boundary_rejects_ungrounded_supplementation() -> None:
    payload, span_id, unit_id = _single_span_payload(core_id=CORE_ID_EMLIS, role="current_input", raw_text="今日は疲れた")
    candidate = CoreTextCandidate(
        text="今日は疲れた記録があります。将来は必ず良くなります。",
        used_evidence_span_ids=(span_id,),
        used_phrase_unit_ids=(unit_id,),
        composer_model="cocolon_text_generation_core.boundary_test.v1",
        meta={"composer_source": "ai_generated", "fixed_string_renderer_used": False},
    )

    result = CoreTextComposer().generate(payload, candidate)

    assert result.status == "rejected"
    assert result.text == ""
    assert "unsupported_sentence" in result.rejection_reasons


def test_piece_boundary_rejects_overcompression_when_must_keep_claims_disappear() -> None:
    from cocolon_text_generation_core.adapters.piece_composer import build_runtime_piece_plan, evaluate_piece_composer

    plan = build_runtime_piece_plan(
        question="整理したい気持ちをどう扱いたい？",
        answer="全部整理しようとする気持ちがあります。",
        source_claims=["全部整理しようとする", "量が多すぎて嫌になる", "目についたものから手をつける"],
        must_keep_signal_keys=["ideal_capacity_switch_gap", "overwhelmed_amount", "small_visible_start"],
        coverage_roles=["ideal_capacity_switch_gap", "overwhelmed_amount", "small_visible_start"],
        answer_preservation_policy="preserve_user_claims",
        overcompression_risk=True,
    )
    evaluation = evaluate_piece_composer(
        plan,
        question_text=plan["question"],
        answer_text=plan["answer"],
        source_texts=plan["source_claims"],
    )

    assert evaluation.passed is False
    assert evaluation.question_result.status == "generated"
    assert evaluation.answer_result.status == "rejected"
    assert evaluation.answer_result.text == ""
    assert any(reason.startswith("must_keep_text_missing") for reason in evaluation.answer_result.rejection_reasons)
    assert evaluation.as_meta()["results"]["answer"]["meta"]["combined_guard_result"]["coverage_ratio"] < 1.0


def test_analysis_boundary_rejects_emlis_temperature_and_diagnostic_surface() -> None:
    from cocolon_text_generation_core.adapters.analysis_composer import evaluate_analysis_composer

    evaluation = evaluate_analysis_composer(
        domain="self_structure",
        materials=[{"id": "self-1", "text_primary": "距離を取りたい記録。", "role_hint": "対人距離"}],
        output_text="Emlisです。あなたはこういう人です。心理診断ではトラウマの症状です。",
        material_fields=["text_primary", "role_hint"],
    )

    assert evaluation.passed is False
    assert evaluation.text == ""
    assert "forbidden_surface_pattern" in evaluation.rejection_reasons
    assert "diagnosis_surface" in evaluation.rejection_reasons
    assert evaluation.as_meta()["cross_core_enabled"] is False
    assert evaluation.as_meta()["content_json_shape_changed"] is False


def test_common_analysis_payload_rejects_piece_voice_at_core_boundary() -> None:
    payload, span_id, unit_id = _single_span_payload(
        core_id=CORE_ID_ANALYSIS,
        role="analysis_observation",
        raw_text="不安が続いた記録が観測されています",
    )
    payload = CoreTextPayload(
        core_id=payload.core_id,
        source_anchors=payload.source_anchors,
        evidence_spans=payload.evidence_spans,
        phrase_units=payload.phrase_units,
        sentence_plans=payload.sentence_plans,
        tone_policy={"voice_distance": "distant_observation_report", "piece_public_qna_voice_allowed": False},
        safety_policy={"core_id": CORE_ID_ANALYSIS, "strict": True, "analysis_strict": True},
        must_keep_roles=payload.must_keep_roles,
        forbidden_surface_patterns=("Pieceの問い", "Pieceの答え", "Emlisです"),
        composer_model=payload.composer_model,
    )
    candidate = CoreTextCandidate(
        text="Pieceの問いとして、不安が続いた記録が観測されています。",
        used_evidence_span_ids=(span_id,),
        used_phrase_unit_ids=(unit_id,),
        composer_model="cocolon_text_generation_core.boundary_test.v1",
        meta={"composer_source": "analysis_composer", "fixed_string_renderer_used": False, "core_id": CORE_ID_ANALYSIS},
    )

    result = CoreTextComposer().generate(payload, candidate)

    assert result.status == "rejected"
    assert result.text == ""
    assert "forbidden_surface_pattern" in result.rejection_reasons
