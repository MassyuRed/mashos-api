# -*- coding: utf-8 -*-
from __future__ import annotations

from analysis_report_validity_gate import attach_report_validity_meta, evaluate_analysis_report_validity
from cocolon_text_generation_core.adapters.analysis_composer import (
    ANALYSIS_COMPOSER_MODEL,
    REJECTION_ANALYSIS_COMMON_TEXT_SAFETY_REJECTED,
    evaluate_analysis_composer,
)


def test_analysis_composer_generates_non_diagnostic_observation_report() -> None:
    evaluation = evaluate_analysis_composer(
        domain="emotion_structure",
        materials=[{"id": "emotion-1", "memo": "不安が続いた記録。眠る前の揺れ。", "emotion": "不安"}],
        output_text="この期間は、不安が続いた記録が観測されています。眠る前の揺れも観測されています。",
        material_fields=["memo", "emotion"],
        target_period="2026-05-01/2026-05-07",
    )

    assert evaluation.passed is True
    assert evaluation.text
    assert evaluation.result.composer_model == ANALYSIS_COMPOSER_MODEL
    meta = evaluation.as_meta()
    assert meta["analysis_composer_connected"] is True
    assert meta["runtime_connected"] is True
    assert meta["validity_gate_connected"] is True
    assert meta["non_diagnostic_gate_passed"] is True
    assert meta["observation_report_only"] is True
    assert meta["content_json_shape_changed"] is False
    assert meta["standardReport_contract_untouched"] is True
    assert meta["contentText_contract_untouched"] is True


def test_analysis_composer_rejects_diagnosis_and_assertive_personality_text() -> None:
    evaluation = evaluate_analysis_composer(
        domain="self_structure",
        materials=[
            {
                "id": "self-1",
                "text_primary": "人との距離を取りたい記録。",
                "role_hint": "対人距離",
                "target_hint": "関係性",
            }
        ],
        output_text="あなたはこういう人です。心理診断ではトラウマの症状です。",
        material_fields=["text_primary", "role_hint", "target_hint"],
    )

    assert evaluation.passed is False
    assert evaluation.text == ""
    assert evaluation.result.text == ""
    assert REJECTION_ANALYSIS_COMMON_TEXT_SAFETY_REJECTED in evaluation.rejection_reasons
    assert any("diagnosis" in reason or "personality" in reason or "analysis_strict" in reason for reason in evaluation.rejection_reasons)
    assert evaluation.as_meta()["non_diagnostic_gate_passed"] is False


def test_report_validity_gate_attaches_phase12_meta_without_changing_payload_shape() -> None:
    content_json = {
        "metrics": {"totalAll": 2},
        "standardReport": {"contentText": "この期間は、不安が続いた記録が観測されています。"},
    }
    result = evaluate_analysis_report_validity(
        domain="emotion_structure",
        material_count=1,
        output_text="この期間は、不安が続いた記録が観測されています。",
        material_fields=["memo", "emotion"],
        material_sources=[{"id": "emotion-2", "memo": "不安が続いた記録。", "emotion": "不安"}],
        target_period="2026-05-01/2026-05-07",
        enforce_text_generation_core=True,
    )

    assert result.save_allowed is True
    assert result.text_generation_core_checked is True
    assert result.text_generation_core_passed is True
    assert result.analysis_composer_connected is True

    updated = attach_report_validity_meta(content_json, result)
    assert updated["metrics"] == content_json["metrics"]
    assert updated["standardReport"] == content_json["standardReport"]
    assert updated["reportValidity"]["text_generation_core_passed"] is True
    assert updated["textGenerationCore"]["analysis_composer_connected"] is True
    assert updated["textGenerationCore"]["cross_core_enabled"] is False
    assert "reportValidity" not in content_json
    assert "textGenerationCore" not in content_json


def test_report_validity_gate_blocks_self_structure_material_mixed_into_emotion_domain() -> None:
    result = evaluate_analysis_report_validity(
        domain="emotion_structure",
        material_count=1,
        output_text="この期間は、不安が観測されています。",
        material_fields=["memo", "memo_action"],
        material_sources=[{"id": "mixed-1", "memo": "不安。", "memo_action": "相手に言い返したい。"}],
        enforce_text_generation_core=True,
    )

    assert result.save_allowed is False
    assert result.domain_separated is False
    assert "emotion_domain_contains_self_structure_material" in result.blocked_reasons
    assert result.text_generation_core_checked is True
