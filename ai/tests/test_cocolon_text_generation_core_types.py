# -*- coding: utf-8 -*-
from __future__ import annotations

import json

from cocolon_text_generation_core import (
    CORE_ID_EMLIS,
    CoreTextPayload,
    EvidenceSpanLike,
    PhraseUnit,
    SentencePlan,
    SourceAnchor,
    STATUS_GENERATED,
    STATUS_UNAVAILABLE,
    TextGenerationResult,
)


def test_source_anchor_generates_stable_json_meta() -> None:
    anchor = SourceAnchor(source_id="input-1", field="memo", raw_text="  楽しかったけど、不安も戻った。  ")
    same_anchor = SourceAnchor(source_id="input-1", field="memo", raw_text="楽しかったけど、不安も戻った。")

    assert anchor.usable is True
    assert anchor.source_hash == same_anchor.source_hash

    meta = anchor.as_meta()
    assert meta["source_id"] == "input-1"
    assert meta["field"] == "memo"
    assert meta["raw_text"] == "楽しかったけど、不安も戻った"
    json.dumps(meta, ensure_ascii=False)


def test_core_text_payload_validates_minimum_contract_and_jsonizes() -> None:
    anchor = SourceAnchor(source_id="input-1", field="memo", raw_text="友達と話せて楽しかったけど、一人になって不安になった。")
    evidence = EvidenceSpanLike(span_id="s1", source_anchor=anchor, role="positive_state")
    phrase = PhraseUnit(
        phrase_unit_id="pu1",
        evidence_span_id="s1",
        text="友達と話せた楽しさ",
        role="positive_state",
        must_keep=True,
    )
    plan = SentencePlan(
        sentence_plan_id="sp1",
        phrase_unit_ids=("pu1",),
        relation_type="grounded_statement",
        line_role="receive",
    )
    payload = CoreTextPayload(
        core_id=CORE_ID_EMLIS,
        source_anchors=(anchor,),
        evidence_spans=(evidence,),
        phrase_units=(phrase,),
        sentence_plans=(plan,),
        must_keep_roles=("positive_state",),
        tone_policy={"distance": "core_specific"},
        safety_policy={"no_overclaim": True},
    )

    assert payload.valid_minimum is True
    assert payload.validate_minimum() == ()
    json.dumps(payload.as_meta(), ensure_ascii=False)


def test_core_text_payload_fails_closed_when_empty() -> None:
    payload = CoreTextPayload(core_id="")
    reasons = payload.validate_minimum()
    result = payload.to_fail_closed_result()

    assert "core_id_missing" in reasons
    assert "source_evidence_missing" in reasons
    assert result.status == STATUS_UNAVAILABLE
    assert result.text == ""
    assert result.used_evidence_span_ids == ()
    assert "payload_minimum_not_met" in result.quality_flags


def test_core_text_payload_rejects_missing_must_keep_role() -> None:
    anchor = SourceAnchor(source_id="input-1", field="memo", raw_text="怒りの下に傷つきがある。")
    evidence = EvidenceSpanLike(span_id="s1", source_anchor=anchor, role="anger_surface")
    phrase = PhraseUnit(phrase_unit_id="pu1", evidence_span_id="s1", text="怒り", role="anger_surface")
    plan = SentencePlan(sentence_plan_id="sp1", phrase_unit_ids=("pu1",), relation_type="grounded_statement")
    payload = CoreTextPayload(
        core_id=CORE_ID_EMLIS,
        source_anchors=(anchor,),
        evidence_spans=(evidence,),
        phrase_units=(phrase,),
        sentence_plans=(plan,),
        must_keep_roles=("hurt_core",),
    )

    assert payload.valid_minimum is False
    assert "must_keep_role_missing:hurt_core" in payload.validate_minimum()


def test_text_generation_result_clears_text_on_fail_closed_status() -> None:
    result = TextGenerationResult(
        status="rejected",
        text="表示してはいけない本文",
        used_evidence_span_ids=("s1",),
        coverage_scope="partial_observation",
        rejection_reasons=("guard_rejected",),
    )

    assert result.status == "rejected"
    assert result.text == ""
    assert result.used_evidence_span_ids == ()
    assert "guard_rejected" in result.rejection_reasons
    json.dumps(result.as_dict(), ensure_ascii=False)


def test_text_generation_result_requires_text_and_evidence_for_generated_status() -> None:
    missing_text = TextGenerationResult(status=STATUS_GENERATED, used_evidence_span_ids=("s1",))
    missing_evidence = TextGenerationResult(status=STATUS_GENERATED, text="根拠がある範囲だけを扱います。")
    passed = TextGenerationResult(
        status=STATUS_GENERATED,
        text="根拠がある範囲だけを扱います。",
        used_evidence_span_ids=("s1",),
        coverage_scope="partial_observation",
    )

    assert missing_text.status == STATUS_UNAVAILABLE
    assert "result_text_missing" in missing_text.rejection_reasons
    assert missing_evidence.status == STATUS_UNAVAILABLE
    assert "result_used_evidence_missing" in missing_evidence.rejection_reasons
    assert passed.passed is True
    assert passed.text == "根拠がある範囲だけを扱います"
