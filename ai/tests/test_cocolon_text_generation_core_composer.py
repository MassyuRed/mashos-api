# -*- coding: utf-8 -*-
from __future__ import annotations

import json

from cocolon_text_generation_core import (
    CORE_ID_ANALYSIS,
    CORE_ID_EMLIS,
    CoreTextCandidate,
    CoreTextComposer,
    CoreTextPayload,
    PhraseUnit,
    SentencePlan,
    STATUS_GENERATED,
    STATUS_REJECTED,
    STATUS_UNAVAILABLE,
    generate_core_text,
)
from cocolon_text_generation_core.evidence import make_evidence_span_like
from cocolon_text_generation_core.guards.grounding import REJECTION_UNSUPPORTED_SENTENCE, REJECTION_USED_EVIDENCE_IDS_MISSING
from cocolon_text_generation_core.guards.japanese_coherence import REJECTION_EMOTION_LABEL_BODY, REJECTION_GENERIC_RELATION_SUFFIX
from cocolon_text_generation_core.guards.overclaim_diagnosis import REJECTION_ANALYSIS_STRICT_ASSERTION, REJECTION_DIAGNOSIS_SURFACE
from cocolon_text_generation_core.result import (
    QUALITY_FLAG_CANDIDATE_MISSING,
    QUALITY_FLAG_CORE_COMPOSER_REJECTED,
    QUALITY_FLAG_CORE_PAYLOAD_INVALID,
    QUALITY_FLAG_GUARD_REJECTED,
    REJECTION_CANDIDATE_TEXT_MISSING,
    REJECTION_PAYLOAD_MINIMUM_NOT_MET,
)


def _span(span_id: str, text: str, *, role: str):
    return make_evidence_span_like(
        span_id=span_id,
        source_id="input-1",
        field_name="current_input",
        raw_text=text,
        role=role,
    )


def _payload(*, core_id: str = CORE_ID_EMLIS, safety_policy=None, meta=None) -> CoreTextPayload:
    spans = (
        _span("s1", "家にいると少し整って落ち着ける", role="safe_home"),
        _span("s2", "現実に戻ると苦しくなって動けなくなる", role="reality_damage"),
    )
    phrases = (
        PhraseUnit(
            phrase_unit_id="pu1",
            evidence_span_id="s1",
            text="家にいると少し整って落ち着ける",
            role="safe_home",
            must_keep=True,
        ),
        PhraseUnit(
            phrase_unit_id="pu2",
            evidence_span_id="s2",
            text="現実に戻ると苦しくなる",
            role="reality_damage",
            must_keep=True,
        ),
    )
    plans = (
        SentencePlan(sentence_plan_id="sp1", phrase_unit_ids=("pu1",), relation_type="observation"),
        SentencePlan(sentence_plan_id="sp2", phrase_unit_ids=("pu2",), relation_type="observation"),
    )
    return CoreTextPayload(
        core_id=core_id,
        evidence_spans=spans,
        phrase_units=phrases,
        sentence_plans=plans,
        must_keep_roles=("safe_home", "reality_damage"),
        safety_policy=safety_policy or {},
        meta=meta or {},
    )


def _good_candidate() -> CoreTextCandidate:
    return CoreTextCandidate(
        text="Emlisです。\n家にいると少し整って落ち着ける感覚があります。\n現実に戻る時の苦しさも出ています。",
        used_evidence_span_ids=("s1", "s2"),
        used_phrase_unit_ids=("pu1", "pu2"),
    )


def test_phase6_composer_fails_closed_for_invalid_payload_object() -> None:
    result = CoreTextComposer().generate({"core_id": CORE_ID_EMLIS})

    assert result.status == STATUS_UNAVAILABLE
    assert result.text == ""
    assert "invalid_core_text_payload" in result.rejection_reasons
    assert QUALITY_FLAG_CORE_PAYLOAD_INVALID in result.quality_flags


def test_phase6_composer_fails_closed_for_payload_minimum_gap() -> None:
    result = CoreTextComposer().generate(CoreTextPayload(core_id=CORE_ID_EMLIS))

    assert result.status == STATUS_UNAVAILABLE
    assert result.text == ""
    assert REJECTION_PAYLOAD_MINIMUM_NOT_MET in result.rejection_reasons
    assert "source_evidence_missing" in result.rejection_reasons
    assert QUALITY_FLAG_CORE_PAYLOAD_INVALID in result.quality_flags


def test_phase6_composer_does_not_create_text_without_candidate() -> None:
    result = CoreTextComposer().generate(_payload())

    assert result.status == STATUS_UNAVAILABLE
    assert result.text == ""
    assert result.used_evidence_span_ids == ()
    assert REJECTION_CANDIDATE_TEXT_MISSING in result.rejection_reasons
    assert QUALITY_FLAG_CANDIDATE_MISSING in result.quality_flags


def test_phase6_composer_accepts_grounded_candidate_and_keeps_meta_json_safe() -> None:
    result = CoreTextComposer().generate(_payload(), _good_candidate())

    assert result.status == STATUS_GENERATED
    assert result.text
    assert result.used_evidence_span_ids == ("s1", "s2")
    assert result.rejection_reasons == ()
    assert result.meta["core_id"] == CORE_ID_EMLIS
    assert result.meta["declared_used_evidence_span_ids"] == ["s1", "s2"]
    json.dumps(result.as_dict(), ensure_ascii=False)


def test_phase6_composer_can_read_candidate_from_payload_meta() -> None:
    payload = _payload(
        meta={
            "candidate": {
                "text": "Emlisです。\n家にいると少し整って落ち着ける感覚があります。\n現実に戻る時の苦しさも出ています。",
                "used_evidence_span_ids": ["s1", "s2"],
                "used_phrase_unit_ids": ["pu1", "pu2"],
            }
        }
    )

    result = generate_core_text(payload)

    assert result.status == STATUS_GENERATED
    assert result.used_evidence_span_ids == ("s1", "s2")


def test_phase6_composer_rejects_candidate_without_declared_evidence_ids() -> None:
    no_evidence_candidate = CoreTextCandidate(
        text="Emlisです。\n家にいると少し整って落ち着ける感覚があります。",
        used_evidence_span_ids=(),
        used_phrase_unit_ids=("pu1",),
    )

    result = CoreTextComposer().generate(_payload(), no_evidence_candidate)

    assert result.status == STATUS_REJECTED
    assert result.text == ""
    assert result.used_evidence_span_ids == ()
    assert REJECTION_USED_EVIDENCE_IDS_MISSING in result.rejection_reasons


def test_phase6_composer_rejects_broken_japanese_candidate_and_clears_text() -> None:
    bad = CoreTextCandidate(
        text="Emlisです。\n不安。\n現実に戻ると苦しくなるがつながっています。",
        used_evidence_span_ids=("s2",),
        used_phrase_unit_ids=("pu2",),
    )

    result = CoreTextComposer().generate(_payload(), bad)

    assert result.status == STATUS_REJECTED
    assert result.text == ""
    assert REJECTION_EMOTION_LABEL_BODY in result.rejection_reasons
    assert REJECTION_GENERIC_RELATION_SUFFIX in result.rejection_reasons
    assert QUALITY_FLAG_CORE_COMPOSER_REJECTED in result.quality_flags
    assert QUALITY_FLAG_GUARD_REJECTED in result.quality_flags


def test_phase6_composer_rejects_unsupported_overclaim_candidate() -> None:
    overclaim = CoreTextCandidate(
        text="Emlisです。\n家にいると少し整って落ち着ける感覚があります。\n本当は誰かに頼りたい願いがあります。",
        used_evidence_span_ids=("s1",),
        used_phrase_unit_ids=("pu1",),
    )

    result = CoreTextComposer().generate(_payload(), overclaim)

    assert result.status == STATUS_REJECTED
    assert result.text == ""
    assert REJECTION_UNSUPPORTED_SENTENCE in result.rejection_reasons


def test_phase6_composer_rejects_analysis_diagnosis_and_strict_assertion() -> None:
    candidate = CoreTextCandidate(
        text="あなたは人との距離を避けているパターンです。心理学的にはトラウマの症状として説明できます。",
        used_evidence_span_ids=("s1", "s2"),
        used_phrase_unit_ids=("pu1", "pu2"),
    )

    result = CoreTextComposer().generate(
        _payload(core_id=CORE_ID_ANALYSIS, safety_policy={"strict": True}),
        candidate,
    )

    assert result.status == STATUS_REJECTED
    assert result.text == ""
    assert REJECTION_DIAGNOSIS_SURFACE in result.rejection_reasons
    assert REJECTION_ANALYSIS_STRICT_ASSERTION in result.rejection_reasons
