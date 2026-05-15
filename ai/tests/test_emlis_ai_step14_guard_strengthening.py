from __future__ import annotations

from cocolon_text_generation_core import evaluate_grounding, evaluate_japanese_coherence, evaluate_overclaim_diagnosis, evaluate_template_echo
from cocolon_text_generation_core.evidence import make_evidence_span_like
from cocolon_text_generation_core.guards.grounding import REJECTION_UNSUPPORTED_GENERAL_KNOWLEDGE_COMPLETION
from cocolon_text_generation_core.guards.japanese_coherence import REJECTION_REPEATED_SURFACE
from cocolon_text_generation_core.guards.overclaim_diagnosis import (
    REJECTION_DIAGNOSIS_LIKE,
    REJECTION_GENERAL_KNOWLEDGE_COMPLETION,
    REJECTION_PERSONALITY_LABEL,
)
from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_grounding_judge import judge_grounding
from emlis_ai_limited_sentence_quality_guard import judge_limited_sentence_quality
from emlis_ai_template_echo_guard import guard_template_echo
from emlis_ai_types import GraphClaim, ObservationGraph


def _emlis_evidence():
    return build_evidence_ledger(
        {
            "id": "step14-guard-input",
            "created_at": "2026-05-14T00:00:00Z",
            "memo": "朝から疲れが溜まっていて、予定も詰まっていて頭が回らない。少し休みたい気持ちもある。",
            "memo_action": "",
            "emotion_details": [{"type": "不安", "strength": "medium"}],
            "emotions": ["不安"],
            "category": ["生活"],
        }
    )


def _emlis_graph(evidence):
    span_ids = [span.span_id for span in evidence if span.span_id]
    return ObservationGraph(
        primary_state=GraphClaim(
            claim_id="c1",
            claim_type="primary_state",
            text="疲れと休みたい気持ちがある",
            evidence_span_ids=span_ids,
            confidence=0.9,
        )
    )


def _limited_kwargs():
    return {
        "composer_source": "ai_generated",
        "composer_model": "cocolon_limited_composer.v1",
        "generation_method": "scoped_graph_evidence_composer",
        "generation_scope": "scoped_graph_only",
        "composer_meta": {"limited_composer": True, "profile_key": "current_input_core", "coverage_scope": "current_input_core"},
    }


def test_step14_grounding_rejects_general_knowledge_completion_not_in_scoped_evidence() -> None:
    evidence = _emlis_evidence()
    text = (
        "Mashさん、Emlisです。\n"
        "疲れが溜まっていて、頭が回らない状態が出ています。\n"
        "一般的に、疲れている人は集中力が落ちるものです。"
    )

    report = judge_grounding(
        comment_text=text,
        graph=_emlis_graph(evidence),
        evidence_spans=evidence,
        allowed_evidence_span_ids=[span.span_id for span in evidence if span.span_id],
        grounding_scope="limited_scoped_graph",
    )

    assert report.passed is False
    assert "unsupported_sentence" in report.rejection_reasons
    assert "unsupported_general_knowledge_completion" in report.rejection_reasons
    assert any(claim.unsupported_reason == "unsupported_general_knowledge_completion" for claim in report.sentence_claims)


def test_step14_quality_guard_rejects_diagnosis_personality_general_knowledge_and_advice() -> None:
    evidence = _emlis_evidence()
    text = (
        "Mashさん、Emlisです。\n"
        "あなたは無理を抱え込みやすいタイプです。\n"
        "心理学的には、これはトラウマの症状として説明できます。\n"
        "一般的に、疲れている人は集中力が落ちるものです。\n"
        "休む必要があります。"
    )

    report = judge_limited_sentence_quality(
        comment_text=text,
        evidence_spans=evidence,
        used_evidence_span_ids=[span.span_id for span in evidence if span.span_id],
        composer_meta={"limited_composer": True, "profile_key": "current_input_core", "coverage_scope": "current_input_core"},
    )

    assert report["passed"] is False
    assert "diagnosis_like" in report["rejection_reasons"]
    assert "personality_label" in report["rejection_reasons"]
    assert "general_knowledge_completion" in report["rejection_reasons"]
    assert "phase14_causal_or_advice_assertion" in report["rejection_reasons"]
    assert report["step14_guard_strengthening"]["guard_threshold_relaxed"] is False


def test_step14_template_guard_exposes_overclaim_and_repeated_surface_reasons() -> None:
    evidence = _emlis_evidence()
    text = (
        "Mashさん、Emlisです。\n"
        "疲れが溜まっていることが重なっています。\n"
        "予定が詰まっていることが重なっています。\n"
        "休みたい気持ちが重なっています。\n"
        "一般的に、疲れている人は集中力が落ちるものです。"
    )

    report = guard_template_echo(
        comment_text=text,
        evidence_spans=evidence,
        used_evidence_span_ids=[span.span_id for span in evidence if span.span_id],
        **_limited_kwargs(),
    )

    assert report.passed is False
    assert "general_knowledge_completion" in report.rejection_reasons
    assert "limited_composer_general_knowledge_completion" in report.rejection_reasons
    assert "repeated_limited_surface_pattern" in report.rejection_reasons
    assert "limited_composer_repeated_surface" in report.rejection_reasons
    assert "general_knowledge_completion" in report.phase8_quality_rejection_reasons


def _core_span(span_id: str, text: str):
    return make_evidence_span_like(
        span_id=span_id,
        source_id="input-1",
        field_name="current_input",
        raw_text=text,
        role="current_input_core",
    )


def test_step14_common_core_grounding_blocks_general_knowledge_completion() -> None:
    evidence = [_core_span("s1", "朝から疲れが溜まっていて、頭が回らない")]
    text = "疲れが溜まっていて頭が回らない状態です。一般的に、疲れている人は集中力が落ちるものです。"

    result = evaluate_grounding(text, evidence_spans=evidence, used_evidence_span_ids=("s1",))

    assert result.passed is False
    assert REJECTION_UNSUPPORTED_GENERAL_KNOWLEDGE_COMPLETION in result.rejection_reasons
    assert "unsupported_sentence" in result.rejection_reasons


def test_step14_common_core_overclaim_guard_uses_a_plan_reason_codes() -> None:
    text = "あなたは無理を抱え込みやすいタイプです。一般的に、疲れている人は集中力が落ちるものです。心理学的には症状として説明できます。"

    result = evaluate_overclaim_diagnosis(text)

    assert result.passed is False
    assert REJECTION_DIAGNOSIS_LIKE in result.rejection_reasons
    assert REJECTION_PERSONALITY_LABEL in result.rejection_reasons
    assert REJECTION_GENERAL_KNOWLEDGE_COMPLETION in result.rejection_reasons


def test_step14_common_core_repeated_surface_is_structural_not_answer_text_match() -> None:
    text = (
        "疲れが表に出ています。\n"
        "予定が表に出ています。\n"
        "不安が表に出ています。\n"
        "休みたい気持ちが表に出ています。"
    )

    jp = evaluate_japanese_coherence(text)
    template = evaluate_template_echo(text, evidence_spans=[_core_span("s1", "疲れと不安がある")], composer_meta={"limited_composer": True})

    assert jp.passed is False
    assert REJECTION_REPEATED_SURFACE in jp.rejection_reasons
    assert template.passed is False
    assert "repeated_limited_surface_pattern" in template.rejection_reasons
