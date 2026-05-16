from __future__ import annotations

from emlis_ai_limited_composer_client import CocolonLimitedComposerClient, _build_phrase_units
from emlis_ai_limited_sentence_quality_guard import judge_phrase_unit_material_quality
from test_emlis_ai_limited_composer_client import _step04_payload


def test_step4_phrase_unit_material_quality_allows_completed_nominal_forms() -> None:
    report = judge_phrase_unit_material_quality(
        "家で落ち着けること",
        raw_text="ずっと家にいて、リラックスできる",
        role="safe_home",
        source_field="memo",
    )

    assert report["target_step"] == "4_PhraseUnit_material_improvement"
    assert report["passed"] is True
    assert "orphan_particle" not in report["rejection_reasons"]
    assert report["raw_text_included"] is False
    assert report["input_specific_template_used"] is False
    assert report["completion_sentence_templates_added"] is False


def test_step4_phrase_unit_material_quality_rejects_broken_material_before_sentence_plan() -> None:
    cases = {
        "不安": "emotion_label_only",
        "自分のことを": "orphan_particle",
        "考え始め": "unfinished_phrase",
        "考え始めこと": "unfinished_phrase",
        "普通にこと": "unfinished_phrase",
        "けどさこと": "unfinished_phrase",
    }

    for text, expected_reason in cases.items():
        report = judge_phrase_unit_material_quality(text, raw_text=text, role="current_expression", source_field="memo")
        assert report["passed"] is False, text
        assert expected_reason in report["rejection_reasons"], text
        assert report["raw_text_included"] is False


def test_step4_build_phrase_units_excludes_unsafe_material_and_keeps_safe_units() -> None:
    evidence = [
        {"span_id": "bad_label", "raw_text": "不安", "source_field": "memo", "detected_type": "state"},
        {"span_id": "bad_particle", "raw_text": "自分のことを", "source_field": "memo", "detected_type": "state"},
        {"span_id": "bad_unfinished", "raw_text": "考え始め", "source_field": "memo", "detected_type": "state"},
        {"span_id": "bad_residual", "raw_text": "普通に", "source_field": "memo", "detected_type": "event"},
        {"span_id": "good", "raw_text": "仕事で疲れて、何も手につかない。", "source_field": "memo", "detected_type": "event"},
    ]

    units = _build_phrase_units(evidence)

    assert {unit.evidence_span_id for unit in units} == {"good"}
    assert {unit.role for unit in units} >= {"fatigue_accumulation", "loss_of_control"}
    assert all(not unit.quality_flags for unit in units)


def test_step4_phrase_unit_material_meta_is_attached_without_raw_text_or_gate_relaxation() -> None:
    evidence = [
        {"span_id": "a", "raw_text": "今日は仕事で疲れた。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "b", "raw_text": "お茶を飲んで少し落ち着いた。", "detected_type": "event", "source_field": "memo"},
    ]

    result = CocolonLimitedComposerClient().generate(_step04_payload(evidence))

    assert result["composer_source"] == "ai_generated"
    meta = result["composer_meta"]["phrase_unit_material_quality"]
    assert meta["target_step"] == "4_PhraseUnit_material_improvement"
    assert meta["material_stage_filter_enabled"] is True
    assert meta["all_phrase_units_material_safe"] is True
    assert meta["unsafe_phrase_unit_count"] == 0
    assert meta["raw_text_included"] is False
    assert meta["completion_sentence_templates_added"] is False
    assert all(row["raw_text_included"] is False for row in meta["rows"])
    assert result["composer_meta"]["step4_phrase_unit_material_quality"] == meta
    diagnostic = result["composer_meta"]["composer_diagnostic"]
    assert diagnostic["phrase_unit_material_quality_enabled"] is True
    assert diagnostic["phrase_unit_material_safe"] is True


def test_step4_phrase_shaping_excludes_unsafe_material_before_safe_phrase_list() -> None:
    from emlis_ai_phrase_shaping_service import safe_phrases, shape_user_phrases
    from emlis_ai_types import EvidenceRef, UserWordAnchor

    evidence = [EvidenceRef(kind="emotion", ref_id="current", weight=1.0)]
    shaped = shape_user_phrases(
        anchors=[
            UserWordAnchor(anchor_key="a1", text="不安", source_field="memo", role="fear_or_disappointment", evidence=evidence),
            UserWordAnchor(anchor_key="a2", text="普通に", source_field="memo", role="current_expression", evidence=evidence),
            UserWordAnchor(anchor_key="a3", text="むかつくけどさ", source_field="memo", role="anger_or_frustration", evidence=evidence),
            UserWordAnchor(anchor_key="a4", text="今日は仕事で疲れた", source_field="memo", role="current_expression", evidence=evidence),
        ],
        current_input={},
    )
    unsafe_by_key = {item.anchor_key: item.unsafe_reasons for item in shaped if item.usability != "safe"}

    assert "emotion_label_only" in unsafe_by_key["a1"]
    assert "unfinished_phrase" in unsafe_by_key["a2"]
    assert any(item.anchor_key == "a3" and "けどさ" not in item.phrase for item in shaped)
    assert {item.anchor_key for item in safe_phrases(shaped)} == {"a3", "a4"}


def test_step4_phrase_unit_material_quality_rejects_long_raw_copy() -> None:
    long_copy = "今日は仕事の資料が多すぎて頭が回らず、集中も切れて、予定にも追いつけない状態が続いていて、さらに確認する項目も増え続けている"

    report = judge_phrase_unit_material_quality(long_copy, raw_text=long_copy, role="current_expression", source_field="memo")

    assert report["passed"] is False
    assert "too_long_quote" in report["rejection_reasons"]
    assert report["raw_input_required_for_debug"] is False
