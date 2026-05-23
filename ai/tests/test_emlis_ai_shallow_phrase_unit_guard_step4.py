from __future__ import annotations

from emlis_ai_limited_composer_client import (
    _build_current_input_core_phrase_units,
    _build_current_input_core_phrase_units_with_guard_meta,
    _generic_shallow_phrase,
)


_MALFORMED_SURFACES = (
    "今までこと",
    "大丈夫こと",
    "まだないかこと",
    "しれないどれこと",
    "上手になせなくてこと",
)


def test_step4_shallow_guard_blocks_malformed_units_before_realizer() -> None:
    evidence_items = [
        {"span_id": "bad_temporal", "raw_text": "今まで", "detected_type": "event"},
        {"span_id": "bad_adjective", "raw_text": "大丈夫", "detected_type": "event"},
        {"span_id": "bad_question", "raw_text": "まだないか", "detected_type": "event"},
        {"span_id": "bad_unknown", "raw_text": "しれないどれ", "detected_type": "event"},
        {"span_id": "bad_te_form", "raw_text": "好きでやってるやつが多いから上手になせなくて", "detected_type": "event"},
        {"span_id": "good_fatigue", "raw_text": "今日は仕事で疲れた。", "detected_type": "event"},
        {"span_id": "good_repair", "raw_text": "お茶を飲んで少し落ち着いた。", "detected_type": "event"},
    ]

    units, guard_meta = _build_current_input_core_phrase_units_with_guard_meta(evidence_items)
    rendered_material = "\n".join(unit.compressed_text for unit in units)

    assert units
    assert "good_fatigue" in {unit.evidence_span_id for unit in units}
    assert "good_repair" in {unit.evidence_span_id for unit in units}
    for surface in _MALFORMED_SURFACES:
        assert surface not in rendered_material

    assert guard_meta["step4_shallow_phrase_unit_guard_applied"] is True
    assert guard_meta["runs_before_render_current_input_core_lines"] is True
    assert guard_meta["safe_phrase_units_only_for_realizer"] is True
    assert guard_meta["unsafe_candidates_reach_rendered_text"] is False
    assert guard_meta["malformed_phrase_unit_blocked_count"] >= 5
    assert guard_meta["must_keep_deferred_not_rendered"] is True
    assert guard_meta["raw_input_included"] is False
    assert guard_meta["comment_text_body_included"] is False


def test_step4_public_builder_returns_only_guarded_units() -> None:
    evidence_items = [
        {"span_id": "bad_temporal", "raw_text": "今まで", "detected_type": "event"},
        {"span_id": "bad_adjective", "raw_text": "大丈夫", "detected_type": "event"},
        {"span_id": "good_fatigue", "raw_text": "今日は仕事で疲れた。", "detected_type": "event"},
        {"span_id": "good_repair", "raw_text": "お茶を飲んで少し落ち着いた。", "detected_type": "event"},
    ]

    units = _build_current_input_core_phrase_units(evidence_items)
    rendered_material = "\n".join(unit.compressed_text for unit in units)

    assert units
    assert "仕事で疲れたこと" in rendered_material
    assert "お茶を飲んで落ち着いたこと" in rendered_material
    assert "今までこと" not in rendered_material
    assert "大丈夫こと" not in rendered_material


def test_step4_generic_phrase_keeps_safe_nominalizations_before_particle_trim() -> None:
    assert _generic_shallow_phrase("今まで続けてきたこと", "event") == "今まで続けてきたこと"
    assert _generic_shallow_phrase("好きなこと", "event") == "好きなこと"

    # The shallow builder may still produce an unsafe candidate, but Step 4's
    # phrase-unit guard must block it before it reaches rendered text.
    assert _generic_shallow_phrase("今まで", "event") == "今までこと"
