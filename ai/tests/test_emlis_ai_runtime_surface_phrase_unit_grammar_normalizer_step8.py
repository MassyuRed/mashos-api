# -*- coding: utf-8 -*-
from __future__ import annotations

from emlis_ai_complete_material_service import build_complete_material_bundle
from emlis_ai_complete_surface_quality_signature import (
    build_surface_quality_signature,
    normalize_surface_signature_to_scorecard_event,
)
from emlis_ai_phrase_shaping_service import shape_user_phrase
from emlis_ai_phrase_unit_grammar_normalizer import (
    DEFER,
    DROP,
    PHRASE_UNIT_GRAMMAR_NORMALIZER_VERSION,
    REPHRASE,
    build_phrase_unit_grammar_normalizer_contract_meta,
    normalize_phrase_unit_grammar,
)
from emlis_ai_types import UserWordAnchor


def test_step8_normalizer_rephrases_safe_stem_koto_without_unsupported_completion() -> None:
    result = normalize_phrase_unit_grammar("私から離れこと", role="self_protection", must_keep=True)

    assert result.action == REPHRASE
    assert result.normalized_text == "私から離れること"
    assert "stem_koto_hanareru" in result.warning_codes
    assert "malformed_nominalization_missing_ru" in result.warning_codes

    meta = result.as_meta()
    assert meta["phrase_unit_grammar_normalizer_version"] == PHRASE_UNIT_GRAMMAR_NORMALIZER_VERSION
    assert meta["unsupported_completion_added"] is False
    assert meta["meaning_added"] is False
    assert meta["raw_input_included"] is False
    assert meta["comment_text_body_included"] is False


def test_step8_must_keep_unsafe_nominal_fragment_is_deferred_not_dropped() -> None:
    result = normalize_phrase_unit_grammar("自分のことをこと", role="self_view", must_keep=True)

    assert result.action == DEFER
    assert result.normalized_text == ""
    assert result.usable is False
    assert "malformed_nominalization_particle_before_koto" in result.warning_codes

    meta = result.as_meta()
    assert meta["must_keep_deferred"] is True
    assert meta["must_keep_dropped"] is False
    assert meta["grammar_warning_major"] is True
    assert meta["unsupported_completion_added"] is False
    assert meta["meaning_added"] is False


def test_step8_non_must_keep_unsafe_fragment_is_dropped_without_contract_changes() -> None:
    result = normalize_phrase_unit_grammar("でも", role="current_expression", must_keep=False)

    assert result.action == DROP
    assert result.normalized_text == ""
    assert "connector_only_material" in result.warning_codes

    meta = result.as_meta()
    assert meta["drop_allowed"] is True
    assert meta["gate_relaxed"] is False
    assert meta["public_response_key_change"] is False
    assert meta["db_physical_name_changed"] is False
    assert meta["rn_visible_contract_changed"] is False


def test_step8_material_service_rephrases_phrase_unit_before_sentence_plan() -> None:
    bundle = build_complete_material_bundle(
        evidence_spans=[
            {
                "span_id": "s1",
                "raw_text": "最近仲良くなった人から離れたい気持ちもある",
                "source_field": "memo",
                "detected_type": "event",
            }
        ],
        phrase_units=[
            {
                "phrase_unit_id": "pu1",
                "evidence_span_id": "s1",
                "compressed_text": "私から離れこと",
                "role": "avoidance_wish",
                "must_keep": True,
                "relation_type": "approach_avoidance",
            }
        ],
        coverage_group="relationship",
    )

    assert bundle.usable is True
    assert bundle.usable_materials[0].material_text == "私から離れること"

    meta = bundle.as_meta()
    assert "stem_koto_hanareru" in meta["grammar_warning_codes"]
    assert meta["phrase_unit_grammar_rephrase_count"] >= 1
    assert meta["phrase_unit_grammar_drop_count"] == 0
    assert meta["unsupported_completion_added"] is False
    assert meta["meaning_added_by_phrase_unit_grammar_normalizer"] is False


def test_step8_material_service_defers_must_keep_malformed_phrase_unit() -> None:
    bundle = build_complete_material_bundle(
        evidence_spans=[
            {
                "span_id": "s1",
                "raw_text": "自分のことをうまく扱えない感覚がある",
                "source_field": "memo",
                "detected_type": "event",
            }
        ],
        phrase_units=[
            {
                "phrase_unit_id": "pu2",
                "evidence_span_id": "s1",
                "compressed_text": "自分のことをこと",
                "role": "self_view",
                "must_keep": True,
                "relation_type": "residue",
            }
        ],
        coverage_group="self_view",
    )

    assert bundle.usable is False
    assert bundle.rejected_rows
    rejection = bundle.rejected_rows[0].as_meta()
    assert rejection["phrase_unit_grammar_action"] == DEFER
    assert rejection["must_keep_dropped"] is False
    assert "malformed_nominalization_particle_before_koto" in rejection["grammar_warning_codes"]


def test_step8_phrase_shaping_nominalizes_safe_attributive_koto() -> None:
    shaped = shape_user_phrase(
        UserWordAnchor(
            anchor_key="a1",
            text="私から離れ",
            role="self_protection",
            source_field="memo",
        )
    )

    assert shaped.nominal == "私から離れること"
    assert shaped.usability == "safe"


def test_step8_surface_signature_and_scorecard_event_carry_grammar_codes() -> None:
    signature = build_surface_quality_signature(
        comment_text="Emlisです。\nその中でも、私から離れことも見えています。",
    )

    assert signature["step8_phrase_unit_grammar_normalizer_connected"] is True
    assert "stem_koto_hanareru" in signature["grammar_warning_codes"]

    event = normalize_surface_signature_to_scorecard_event(signature)
    assert event["phrase_unit_grammar_normalizer_version"] == PHRASE_UNIT_GRAMMAR_NORMALIZER_VERSION
    assert "stem_koto_hanareru" in event["phrase_unit_grammar_warning_codes"]
    assert event["comment_text_body_included"] is False


def test_step8_contract_meta_does_not_relax_gate_or_public_contract() -> None:
    meta = build_phrase_unit_grammar_normalizer_contract_meta()

    assert meta["step8_phrase_unit_grammar_normalizer_ready"] is True
    assert meta["runs_before_sentence_plan"] is True
    assert meta["unsupported_completion_added"] is False
    assert meta["meaning_added"] is False
    assert meta["gate_relaxed"] is False
    assert meta["public_response_key_change"] is False
    assert meta["db_physical_name_changed"] is False
    assert meta["rn_visible_contract_changed"] is False
    assert meta["product_gate_achieved"] is False
    assert meta["public_release_applied"] is False
