from __future__ import annotations

from analysis_report_validity_gate import evaluate_analysis_report_validity


def test_self_structure_domain_accepts_value_observation_material():
    result = evaluate_analysis_report_validity(
        domain="self_structure",
        material_count=2,
        output_text="この期間には、整理したい理想と目の前の処理へ切り替わる流れが見えました。",
        output_payload={"value_observation_signal_keys": ["ideal_capacity_switch_gap"]},
        material_fields=["value_observation_signals", "memo_action"],
    )

    assert result.save_allowed is True
    assert result.value_observation_domain_ok is True
    assert "ideal_capacity_switch_gap" in result.value_observation_signal_keys


def test_emotion_domain_blocks_self_structure_value_observation_material():
    result = evaluate_analysis_report_validity(
        domain="emotion",
        material_count=2,
        output_text="この期間は不安が強く出ていました。",
        output_payload={"value_observation_signal_keys": ["ideal_capacity_switch_gap"]},
        material_fields=["emotion_details"],
    )

    assert result.save_allowed is False
    assert result.value_observation_domain_ok is False
    assert "emotion_domain_contains_self_structure_material" in result.blocked_reasons
