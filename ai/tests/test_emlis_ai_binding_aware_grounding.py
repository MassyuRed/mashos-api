from __future__ import annotations

from cocolon_text_generation_core import PhraseUnit, evaluate_grounding
from cocolon_text_generation_core.evidence import make_evidence_span_like
from emlis_ai_grounding_judge import judge_grounding
from emlis_ai_types import EvidenceSpan, GraphClaim, ObservationGraph


def _emlis_span(span_id: str = "e1", text: str = "会議と資料修正が朝から並んだ。") -> EvidenceSpan:
    return EvidenceSpan(
        span_id=span_id,
        raw_text=text,
        start_index=0,
        end_index=len(text),
        detected_type="event",
        confidence=1.0,
        source_field="memo",
    )


def _emlis_graph(span_id: str = "e1") -> ObservationGraph:
    return ObservationGraph(
        primary_state=GraphClaim(
            claim_id="c1",
            claim_type="primary_state",
            text="負荷がある",
            evidence_span_ids=[span_id],
            confidence=0.9,
        )
    )


def _binding(sentence: str, *, span_id: str = "e1", phrase_id: str = "pu1", relation: str = "pressure") -> dict:
    return {
        "sentence_id": "s1",
        "text": sentence,
        "used_evidence_span_ids": [span_id],
        "used_phrase_unit_ids": [phrase_id],
        "relation_type": relation,
        "line_role": "state",
        "coverage_scope": "partial_observation",
    }


def test_step6_emlis_grounding_uses_sentence_binding_without_relaxing_surface_threshold() -> None:
    evidence = [_emlis_span()]
    graph = _emlis_graph()
    sentence = "負荷が続く中で、余力が細くなっています。"
    text = f"Mashさん、Emlisです。\n{sentence}"

    without_binding = judge_grounding(
        comment_text=text,
        graph=graph,
        evidence_spans=evidence,
        allowed_evidence_span_ids=["e1"],
        grounding_scope="limited_scoped_graph",
    )
    with_binding = judge_grounding(
        comment_text=text,
        graph=graph,
        evidence_spans=evidence,
        allowed_evidence_span_ids=["e1"],
        grounding_scope="limited_scoped_graph",
        sentence_bindings=[_binding(sentence)],
    )

    assert without_binding.passed is False
    assert "unsupported_sentence" in without_binding.rejection_reasons
    assert with_binding.passed is True
    assert with_binding.binding_present is True
    assert with_binding.binding_used is True
    assert with_binding.binding_count == 1
    assert with_binding.binding_supported_sentence_count == 1
    assert with_binding.binding_diagnostics["target_step"] == "6_binding_aware_grounding"
    assert with_binding.binding_diagnostics["surface_threshold_relaxed"] is False
    assert with_binding.binding_diagnostics["raw_input_included"] is False

    claim = [claim for claim in with_binding.sentence_claims if claim.sentence == sentence][0]
    assert claim.evidence_span_ids == ["e1"]
    assert claim.binding_used is True
    assert claim.binding_evidence_span_ids == ["e1"]
    assert claim.binding_phrase_unit_ids == ["pu1"]
    assert claim.binding_relation_type == "pressure"
    assert claim.grounding_support_source.startswith("declared_")


def test_step6_emlis_grounding_still_rejects_unbacked_overclaim_with_binding() -> None:
    evidence = [_emlis_span(text="会議と資料修正が朝から並んだ。")]  # no "頼りたい" evidence
    graph = _emlis_graph()
    sentence = "本当は誰かに頼りたい願いがあります。"
    text = f"Mashさん、Emlisです。\n{sentence}"

    report = judge_grounding(
        comment_text=text,
        graph=graph,
        evidence_spans=evidence,
        allowed_evidence_span_ids=["e1"],
        grounding_scope="limited_scoped_graph",
        sentence_bindings=[_binding(sentence, relation="approach")],
    )

    assert report.passed is False
    assert "unsupported_sentence" in report.rejection_reasons
    assert any(claim.unsupported_reason == "unsupported_overclaim" for claim in report.sentence_claims)
    assert report.binding_present is True
    assert report.binding_diagnostics["guard_threshold_relaxed"] is False


def test_step6_common_core_grounding_uses_sentence_bindings() -> None:
    evidence = [
        make_evidence_span_like(
            span_id="e1",
            source_id="input-1",
            field_name="memo",
            raw_text="会議と資料修正が朝から並んだ。",
            role="pressure",
        )
    ]
    phrase_units = [PhraseUnit(phrase_unit_id="pu1", evidence_span_id="e1", text="会議と資料修正", role="pressure")]
    sentence = "負荷が続く中で、余力が細くなっています。"
    text = f"Emlisです。\n{sentence}"

    without_binding = evaluate_grounding(text, evidence_spans=evidence, used_evidence_span_ids=("e1",))
    with_binding = evaluate_grounding(
        text,
        evidence_spans=evidence,
        used_evidence_span_ids=("e1",),
        phrase_units=phrase_units,
        used_phrase_unit_ids=("pu1",),
        sentence_bindings=[_binding(sentence)],
    )

    assert without_binding.passed is False
    assert with_binding.passed is True
    assert with_binding.meta["binding_used"] is True
    assert with_binding.meta["step6_binding_aware_grounding"]["binding_used"] is True
    assert with_binding.meta["step6_binding_aware_grounding"]["surface_threshold_relaxed"] is False
    assert with_binding.meta["raw_input_included"] is False
    claim = with_binding.meta["sentence_claims"][0]
    assert claim["binding_used"] is True
    assert claim["binding_evidence_span_ids"] == ["e1"]
    assert claim["binding_phrase_unit_ids"] == ["pu1"]
    assert claim["binding_relation_type"] == "pressure"
