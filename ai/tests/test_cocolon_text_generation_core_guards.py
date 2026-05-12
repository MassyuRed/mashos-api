# -*- coding: utf-8 -*-
from __future__ import annotations

import json

from cocolon_text_generation_core import (
    CORE_ID_ANALYSIS,
    PhraseUnit,
    evaluate_grounding,
    evaluate_japanese_coherence,
    evaluate_must_keep_coverage,
    evaluate_overclaim_diagnosis,
    evaluate_template_echo,
)
from cocolon_text_generation_core.evidence import make_evidence_span_like
from cocolon_text_generation_core.guards.grounding import REJECTION_UNSUPPORTED_SENTENCE
from cocolon_text_generation_core.guards.japanese_coherence import (
    REJECTION_EMOTION_LABEL_BODY,
    REJECTION_GENERIC_RELATION_SUFFIX,
    REJECTION_UNFINISHED_PHRASE,
)
from cocolon_text_generation_core.guards.must_keep_coverage import REJECTION_MUST_KEEP_EVIDENCE_MISSING
from cocolon_text_generation_core.guards.overclaim_diagnosis import (
    REJECTION_ANALYSIS_STRICT_ASSERTION,
    REJECTION_DIAGNOSIS_SURFACE,
    REJECTION_PERSONALITY_ASSERTION,
)
from cocolon_text_generation_core.guards.template_echo import REJECTION_REPEATED_LIMITED_SURFACE_PATTERN
from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_template_echo_guard import guard_template_echo as guard_emlis_template_echo


def _span(span_id: str, text: str, *, role: str = "observed_role"):
    return make_evidence_span_like(
        span_id=span_id,
        source_id="input-1",
        field_name="current_input",
        raw_text=text,
        role=role,
    )


def test_common_japanese_coherence_rejects_phase8_broken_surfaces() -> None:
    bad = "Emlisです。\n不安。\nまた急に不安になったがつながっています。\n先のことを考え始めがつながっています。"

    result = evaluate_japanese_coherence(bad)

    assert result.passed is False
    assert REJECTION_EMOTION_LABEL_BODY in result.rejection_reasons
    assert REJECTION_GENERIC_RELATION_SUFFIX in result.rejection_reasons
    assert REJECTION_UNFINISHED_PHRASE in result.rejection_reasons
    assert "japanese_coherence_failed" in result.quality_flags
    json.dumps(result.as_meta(), ensure_ascii=False)


def test_common_japanese_coherence_allows_grounded_natural_lines() -> None:
    text = (
        "Emlisです。\n"
        "家にいることで少し落ち着ける感覚があります。\n"
        "でも、現実に戻る時の重さも同じ場面に出ています。"
    )

    result = evaluate_japanese_coherence(text)

    assert result.passed is True
    assert result.rejection_reasons == ()


def test_common_template_echo_matches_existing_emlis_guard_on_obvious_repeated_surface() -> None:
    evidence = build_evidence_ledger(
        {
            "id": "phase5-common-guard",
            "memo": "家にいると少し整って落ち着ける。現実に戻ると苦しくなる。普通に生活したい気持ちは残っている。",
            "memo_action": "",
            "emotion_details": [{"type": "自己理解", "strength": "medium"}],
            "emotions": ["自己理解"],
            "category": ["生活"],
        }
    )
    text = (
        "Mashさん、Emlisです。\n"
        "家にいると少し整う感覚が重なっています。\n"
        "現実に戻ると苦しくなる重さが重なっています。\n"
        "普通に生活したい願いが重なっています。"
    )

    emlis = guard_emlis_template_echo(
        comment_text=text,
        evidence_spans=evidence,
        composer_source="ai_generated",
        composer_model="cocolon_limited_composer.v1",
        generation_method="scoped_graph_evidence_composer",
        generation_scope="scoped_graph_only",
        composer_meta={"limited_composer": True},
    )
    common = evaluate_template_echo(text, evidence_spans=evidence, composer_meta={"limited_composer": True})

    assert emlis.passed is False
    assert common.passed is False
    assert REJECTION_REPEATED_LIMITED_SURFACE_PATTERN in common.rejection_reasons
    assert common.limited_surface_repetition_score >= 0.67


def test_common_grounding_requires_used_evidence_and_sentence_overlap() -> None:
    evidence = [
        _span("s1", "家にいると少し整って落ち着ける", role="safe_home"),
        _span("s2", "現実に戻ると苦しくなって動けなくなる", role="reality_damage"),
    ]
    grounded = "Emlisです。\n家にいると少し整って落ち着ける感覚があります。\n現実に戻る時の苦しさも出ています。"
    overclaim = grounded + "\n本当は誰かに頼りたい願いがあります。"

    passed = evaluate_grounding(grounded, evidence_spans=evidence, used_evidence_span_ids=("s1", "s2"))
    rejected = evaluate_grounding(overclaim, evidence_spans=evidence, used_evidence_span_ids=("s1", "s2"))

    assert passed.passed is True
    assert rejected.passed is False
    assert REJECTION_UNSUPPORTED_SENTENCE in rejected.rejection_reasons
    assert any(not claim["evidence_span_ids"] for claim in rejected.sentence_claims)


def test_common_overclaim_guard_rejects_diagnosis_personality_and_analysis_strict_assertion() -> None:
    diagnosis = "あなたは回避型の性格です。心理学的にはトラウマの症状として説明できます。"
    strict_analysis = "あなたは人との距離を避けているパターンです。"
    observation = "この期間は、不安に関する記録が増えています。生活場面の負荷も同じ時期に観測されています。"

    diagnosis_result = evaluate_overclaim_diagnosis(diagnosis)
    strict_result = evaluate_overclaim_diagnosis(strict_analysis, core_id=CORE_ID_ANALYSIS, policy={"strict": True})
    observation_result = evaluate_overclaim_diagnosis(observation, core_id=CORE_ID_ANALYSIS, policy={"strict": True})

    assert diagnosis_result.passed is False
    assert REJECTION_DIAGNOSIS_SURFACE in diagnosis_result.rejection_reasons
    assert REJECTION_PERSONALITY_ASSERTION in diagnosis_result.rejection_reasons
    assert strict_result.passed is False
    assert REJECTION_ANALYSIS_STRICT_ASSERTION in strict_result.rejection_reasons
    assert observation_result.passed is True


def test_common_must_keep_coverage_checks_required_roles_and_used_evidence_ids() -> None:
    units = (
        PhraseUnit(phrase_unit_id="pu1", evidence_span_id="s1", text="家で整えられる感覚", role="safe_home", must_keep=True),
        PhraseUnit(phrase_unit_id="pu2", evidence_span_id="s2", text="現実に戻る重さ", role="reality_damage", must_keep=True),
    )

    missing_evidence = evaluate_must_keep_coverage(
        phrase_units=units,
        must_keep_roles=("safe_home", "reality_damage"),
        used_evidence_span_ids=("s1",),
    )
    missing_role = evaluate_must_keep_coverage(
        phrase_units=units,
        must_keep_roles=("safe_home", "ordinary_life_wish"),
        used_evidence_span_ids=("s1", "s2"),
    )
    passed = evaluate_must_keep_coverage(
        phrase_units=units,
        must_keep_roles=("safe_home", "reality_damage"),
        used_evidence_span_ids=("s1", "s2"),
    )

    assert missing_evidence.passed is False
    assert any(reason.startswith(REJECTION_MUST_KEEP_EVIDENCE_MISSING) for reason in missing_evidence.rejection_reasons)
    assert missing_evidence.missing_evidence_span_ids == ("s2",)
    assert missing_role.passed is False
    assert "must_keep_role_missing:ordinary_life_wish" in missing_role.rejection_reasons
    assert passed.passed is True
