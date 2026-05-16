from __future__ import annotations

from emlis_ai_limited_composer_client import CocolonLimitedComposerClient
from test_emlis_ai_limited_composer_client import _payload_for, _step04_payload


def _body_lines(comment_text: str) -> list[str]:
    lines = [line.strip() for line in str(comment_text or "").splitlines() if line.strip()]
    if lines and "Emlis" in lines[0]:
        return lines[1:]
    return lines


def _assert_step3_sentence_binding_contract(result: dict) -> None:
    body_lines = _body_lines(result["comment_text"])
    bundle = result["sentence_binding_bundle"]
    meta = result["composer_meta"]
    step3 = meta["step3_sentence_binding_type"]
    diagnostic = meta["composer_diagnostic"]

    assert bundle["target_step"] == "3_SentenceBinding_type_addition"
    assert bundle["binding_version"] == "emlis.sentence_binding.v1"
    assert bundle["binding_present"] is True
    assert bundle["binding_missing"] is False
    assert bundle["binding_count"] == len(body_lines)
    assert bundle["sentence_binding_count"] == len(body_lines)
    assert bundle["expected_binding_count"] == len(body_lines)
    assert len(bundle["bindings"]) == len(body_lines)
    assert {binding["text"] for binding in bundle["bindings"]} == set(body_lines)

    assert step3["sentence_binding_type_added"] is True
    assert step3["sentence_binding_contract_attached"] is True
    assert step3["binding_count_matches_body"] is True
    assert step3["binding_count"] == len(body_lines)
    assert step3["expected_binding_count"] == len(body_lines)
    assert step3["binding_missing"] is False

    assert diagnostic["sentence_binding_contract_attached"] is True
    assert diagnostic["binding_present"] is True
    assert diagnostic["binding_missing"] is False
    assert diagnostic["binding_count"] == len(body_lines)
    assert diagnostic["sentence_binding_count"] == len(body_lines)
    assert diagnostic["relation_types"] == bundle["relation_types"]

    for index, binding in enumerate(bundle["bindings"], start=1):
        assert binding["sentence_id"] == f"s{index}"
        assert binding["text"] == body_lines[index - 1]
        assert binding["used_evidence_span_ids"]
        assert binding["used_phrase_unit_ids"]
        assert binding["relation_type"]
        assert binding["line_role"]
        assert binding["coverage_scope"] == result["coverage_scope"]
        assert binding["raw_input_included"] is False
        assert binding["meta"]["raw_input_included"] is False

    core = meta["text_generation_core"]
    assert core["payload"]["sentence_binding_count"] == len(body_lines)
    assert len(core["sentence_bindings"]) == len(body_lines)
    assert all("text" not in binding for binding in core["sentence_bindings"])


def test_step3_sentence_binding_is_created_with_full_profile_candidate():
    payload, _evidence, _scope = _payload_for()

    result = CocolonLimitedComposerClient().generate(payload)

    assert result["composer_source"] == "ai_generated"
    assert result["coverage_scope"] == "partial_observation"
    _assert_step3_sentence_binding_contract(result)
    bundle = result["sentence_binding_bundle"]
    assert set(bundle["used_phrase_unit_ids"]) == set(result["used_phrase_unit_ids"])
    assert len(bundle["relation_types"]) >= 2


def test_step3_sentence_binding_is_created_with_current_input_core_candidate():
    evidence = [
        {"span_id": "a", "raw_text": "今日は仕事で疲れた。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "b", "raw_text": "お茶を飲んで少し落ち着いた。", "detected_type": "event", "source_field": "memo"},
    ]

    result = CocolonLimitedComposerClient().generate(_step04_payload(evidence))

    assert result["composer_source"] == "ai_generated"
    assert result["coverage_scope"] == "current_input_core"
    _assert_step3_sentence_binding_contract(result)
    bundle = result["sentence_binding_bundle"]
    assert bundle["profile_key"] == "current_input_core"
    assert set(bundle["relation_types"]) >= {"center"}
    assert set(bundle["used_evidence_span_ids"]) == {"a", "b"}
