# -*- coding: utf-8 -*-
from __future__ import annotations

import pytest

from emlis_ai_complete_material_service import build_complete_material_bundle
from emlis_ai_limited_sentence_quality_guard import (
    judge_phrase_unit_material_quality,
    phrase_unit_material_quality_policy_meta,
)
from emlis_ai_phrase_unit_grammar_normalizer import (
    DEFER,
    DROP,
    KEEP,
    REPHRASE,
    build_phrase_unit_grammar_normalizer_contract_meta,
    normalize_phrase_unit_grammar,
)


_MALFORMED_CASES = (
    ("今までこと", "malformed_nominalization_temporal_fragment"),
    ("大丈夫こと", "malformed_nominalization_adjective_fragment"),
    ("まだないかこと", "malformed_nominalization_question_fragment"),
    ("しれないどれこと", "malformed_nominalization_question_fragment"),
    ("上手になせなくてこと", "malformed_nominalization_te_form_fragment"),
    ("好きこと", "malformed_nominalization_adjective_fragment"),
    ("見えこと", "malformed_nominalization_auxiliary_fragment"),
    ("変えようとしたりこと", "malformed_nominalization_tari_fragment"),
    ("考えたりこと", "malformed_nominalization_tari_fragment"),
    ("見たりこと", "malformed_nominalization_tari_fragment"),
    ("無理に変えようとしたりこともあり", "malformed_nominalization_tari_fragment"),
    ("やろうとしたりこと", "malformed_nominalization_tari_fragment"),
)


@pytest.mark.parametrize(("phrase", "expected_code"), _MALFORMED_CASES)
def test_step3_phrase_unit_material_guard_blocks_malformed_nominalization(phrase: str, expected_code: str) -> None:
    report = judge_phrase_unit_material_quality(
        phrase,
        raw_text=phrase,
        role="current_expression",
        source_field="memo",
    )

    assert report["passed"] is False
    assert expected_code in report["quality_flags"]
    assert expected_code in report["rejection_reasons"]
    assert report["malformed_nominalization_blocked"] is True
    assert report["malformed_phrase_unit_guard_enabled"] is True
    assert report["raw_text_included"] is False
    assert report["completion_sentence_templates_added"] is False


@pytest.mark.parametrize(("phrase", "expected_code"), _MALFORMED_CASES)
def test_step3_grammar_normalizer_drops_non_must_keep_malformed_nominalization(phrase: str, expected_code: str) -> None:
    result = normalize_phrase_unit_grammar(
        phrase,
        role="current_expression",
        must_keep=False,
        source="step3_malformed_nominalization_guard_test",
    )

    assert result.action == DROP
    assert result.normalized_text == ""
    assert result.usable is False
    assert expected_code in result.warning_codes

    meta = result.as_meta()
    assert meta["malformed_nominalization_guard_enabled"] is True
    assert meta["malformed_phrase_unit_count"] >= 1
    assert meta["drop_allowed"] is True
    assert meta["must_keep_dropped"] is False
    assert meta["unsupported_completion_added"] is False
    assert meta["meaning_added"] is False
    assert meta["raw_input_included"] is False
    assert meta["comment_text_body_included"] is False


@pytest.mark.parametrize(("phrase", "expected_code"), _MALFORMED_CASES)
def test_step3_grammar_normalizer_defers_must_keep_malformed_nominalization(phrase: str, expected_code: str) -> None:
    result = normalize_phrase_unit_grammar(
        phrase,
        role="current_expression",
        must_keep=True,
        source="step3_malformed_nominalization_guard_test",
    )

    assert result.action == DEFER
    assert result.normalized_text == ""
    assert result.usable is False
    assert expected_code in result.warning_codes

    meta = result.as_meta()
    assert meta["must_keep_deferred"] is True
    assert meta["must_keep_dropped"] is False
    assert meta["defer_allowed"] is True
    assert meta["unsupported_completion_added"] is False
    assert meta["meaning_added"] is False
    assert meta["raw_input_included"] is False
    assert meta["comment_text_body_included"] is False


def test_step3_guard_keeps_safe_nominalizations_and_safe_stem_repair() -> None:
    safe_keep = normalize_phrase_unit_grammar("好きなこと", role="current_expression", must_keep=False)
    safe_repair = normalize_phrase_unit_grammar("私から離れこと", role="self_protection", must_keep=True)
    material_report = judge_phrase_unit_material_quality("今まで続けてきたこと", raw_text="今まで続けてきたこと", role="current_expression", source_field="memo")
    safe_tari_action = normalize_phrase_unit_grammar("考えたりすること", role="current_expression", must_keep=False)
    safe_tari_pair = judge_phrase_unit_material_quality("見たり聞いたりすること", raw_text="見たり聞いたりすること", role="current_expression", source_field="memo")
    safe_non_tari_nominalization = judge_phrase_unit_material_quality("無理に変えようとしたこと", raw_text="無理に変えようとしたこと", role="current_expression", source_field="memo")

    assert safe_keep.action == KEEP
    assert safe_keep.normalized_text == "好きなこと"
    assert safe_repair.action == REPHRASE
    assert safe_repair.normalized_text == "私から離れること"
    assert material_report["passed"] is True
    assert safe_tari_action.action == KEEP
    assert safe_tari_action.normalized_text == "考えたりすること"
    assert safe_tari_pair["passed"] is True
    assert safe_non_tari_nominalization["passed"] is True


def test_step3_complete_material_service_defers_must_keep_malformed_phrase_unit_without_dropping_contract() -> None:
    bundle = build_complete_material_bundle(
        evidence_spans=[
            {
                "span_id": "s1",
                "raw_text": "自分の特技がまだ見えていない",
                "source_field": "memo",
                "detected_type": "event",
            }
        ],
        phrase_units=[
            {
                "phrase_unit_id": "pu1",
                "evidence_span_id": "s1",
                "compressed_text": "今までこと",
                "role": "current_expression",
                "must_keep": True,
                "relation_type": "residue",
            }
        ],
        coverage_group="current_input_core",
    )

    assert bundle.usable is False
    assert bundle.rejected_rows
    rejection = bundle.rejected_rows[0].as_meta()
    assert rejection["phrase_unit_grammar_action"] == DEFER
    assert rejection["must_keep_dropped"] is False
    assert "malformed_nominalization_temporal_fragment" in rejection["grammar_warning_codes"]
    assert "phrase_unit_grammar_deferred" in rejection["rejection_reasons"]
    assert rejection["raw_input_included"] is False


def test_step3_contract_meta_reports_guard_without_public_contract_changes() -> None:
    material_meta = phrase_unit_material_quality_policy_meta()
    normalizer_meta = build_phrase_unit_grammar_normalizer_contract_meta()

    assert material_meta["malformed_nominalization_guard_enabled"] is True
    assert material_meta["malformed_nominalization_tari_fragment_guarded"] is True
    assert normalizer_meta["malformed_nominalization_guard_enabled"] is True
    assert normalizer_meta["malformed_nominalization_tari_fragment_guard_enabled"] is True
    assert normalizer_meta["safe_nominalization_guard_enabled"] is True
    assert normalizer_meta["gate_relaxed"] is False
    assert normalizer_meta["public_response_key_change"] is False
    assert normalizer_meta["db_physical_name_changed"] is False
    assert normalizer_meta["rn_visible_contract_changed"] is False
    assert normalizer_meta["product_gate_achieved"] is False
    assert normalizer_meta["public_release_applied"] is False
