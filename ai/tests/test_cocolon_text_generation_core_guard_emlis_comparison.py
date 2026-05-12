# -*- coding: utf-8 -*-
from __future__ import annotations

from cocolon_text_generation_core.guards.japanese_coherence import guard_japanese_coherence
from cocolon_text_generation_core.guards.template_echo import guard_template_echo as guard_common_template_echo
from emlis_ai_limited_sentence_quality_guard import judge_limited_sentence_quality
from emlis_ai_template_echo_guard import guard_template_echo as guard_emlis_template_echo
from emlis_ai_types import EvidenceSpan


def test_phase5_common_japanese_guard_is_not_weaker_than_emlis_phase8_for_known_bad_surface() -> None:
    text = "Emlisです。\n怒り。\nなんであがつながっています。"

    common = guard_japanese_coherence(text)
    emlis = judge_limited_sentence_quality(comment_text=text, evidence_spans=[])

    assert common.passed is False
    assert emlis["passed"] is False
    assert "emotion_label_body_line" in common.rejection_reasons
    assert "generic_relation_suffix" in common.rejection_reasons
    assert "phase8_emotion_label_body_line" in emlis["rejection_reasons"]
    assert "phase8_generic_relation_suffix" in emlis["rejection_reasons"]


def test_phase5_common_template_guard_matches_emlis_template_guard_for_fixed_surface_signature() -> None:
    text = "そこには、感覚もありました。"
    spans = [EvidenceSpan(span_id="s1", raw_text="感覚", source_field="memo", detected_type="event")]

    common = guard_common_template_echo(text)
    emlis = guard_emlis_template_echo(comment_text=text, evidence_spans=spans, composer_source="ai_generated")

    assert common.passed is False
    assert emlis.passed is False
    assert "fixed_template_surface" in common.rejection_reasons
    assert "banned_legacy_pattern" in emlis.rejection_reasons
