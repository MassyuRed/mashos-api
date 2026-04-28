from __future__ import annotations


def test_analysis_capability_profiles_keep_gate_required_and_cross_core_reserved():
    from analysis_capability import resolve_analysis_capability_for_tier

    free = resolve_analysis_capability_for_tier("free")
    plus = resolve_analysis_capability_for_tier("plus")
    premium = resolve_analysis_capability_for_tier("premium")

    assert free.report_validity_gate_required is True
    assert plus.report_validity_gate_required is True
    assert premium.report_validity_gate_required is True
    assert free.cross_core_enabled is False
    assert plus.cross_core_enabled is False
    assert premium.cross_core_enabled is False
    assert free.self_structure_report_enabled is False
    assert plus.self_structure_report_enabled is True
    assert premium.deep_analysis_enabled is True


def test_report_validity_gate_allows_emotion_report_without_memo_action():
    from analysis_report_validity_gate import evaluate_analysis_report_validity

    result = evaluate_analysis_report_validity(
        domain="emotion_structure",
        material_count=3,
        output_text="今週は不安と平穏の揺れが見えました。",
        material_fields=["emotion_details", "created_at", "memo"],
        target_period="2026-04-20/2026-04-27",
    )

    assert result.save_allowed is True
    assert result.material_sufficient is True
    assert result.domain_separated is True
    assert result.as_meta()["schema_version"] == "analysis.validity.v1"


def test_report_validity_gate_blocks_emotion_report_when_action_material_mixed():
    from analysis_report_validity_gate import evaluate_analysis_report_validity

    result = evaluate_analysis_report_validity(
        domain="emotion_structure",
        material_count=2,
        output_text="怒りの波がありました。",
        material_fields=["emotion_details", "memo_action"],
    )

    assert result.domain_separated is False
    assert result.save_allowed is False
    assert "emotion_domain_contains_self_structure_material" in result.blocked_reasons


def test_report_validity_gate_blocks_diagnosis_and_overclaim():
    from analysis_report_validity_gate import evaluate_analysis_report_validity

    result = evaluate_analysis_report_validity(
        domain="self_structure",
        material_count=2,
        output_text="あなたの本質は完全にうつ病です。",
        material_fields=["text_primary", "text_secondary", "role_hint"],
    )

    assert result.diagnosis_checked is False
    assert result.overclaim_checked is False
    assert result.save_allowed is False


def test_report_validity_meta_is_additive():
    from analysis_report_validity_gate import attach_report_validity_meta, evaluate_analysis_report_validity

    content_json = {"metrics": {"totalAll": 3}, "standardReport": {"contentText": "観測できました。"}}
    result = evaluate_analysis_report_validity(
        domain="emotion_structure",
        material_count=3,
        output_text="観測できました。",
        output_payload=content_json,
        material_fields=["emotion_details", "memo"],
    )
    updated = attach_report_validity_meta(content_json, result)

    assert updated["metrics"] == content_json["metrics"]
    assert updated["standardReport"] == content_json["standardReport"]
    assert updated["reportValidity"]["save_allowed"] is True
    assert "reportValidity" not in content_json


def test_emotion_analysis_adapter_does_not_use_memo_action():
    from analysis_engine_adapter import build_emotion_entries_from_rows

    entries = build_emotion_entries_from_rows(
        [
            {
                "id": "row-1",
                "created_at": "2026-04-27T00:00:00Z",
                "emotion_details": [{"type": "怒り", "strength": "strong"}],
                "memo": "怒りがあった",
                "memo_action": "相手に言い返した",
            }
        ]
    )

    assert len(entries) == 1
    assert entries[0].memo == "怒りがあった"
    assert "言い返した" not in str(entries[0])
