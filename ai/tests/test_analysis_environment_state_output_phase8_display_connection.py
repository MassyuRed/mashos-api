from __future__ import annotations

import json

from cocolon_text_generation_core.adapters.analysis_composer import (
    evaluate_analysis_composer,
    evaluate_analysis_environment_state_output_material,
    evaluate_analysis_report_text_safety,
)
from cocolon_text_generation_core.adapters.analysis_environment_state_output_material import (
    build_analysis_environment_state_output_material,
)
from cocolon_text_generation_core.adapters.analysis_environment_state_output_surface import (
    ANALYSIS_ENVIRONMENT_STATE_OUTPUT_SURFACE_MATERIAL_ID,
    ANALYSIS_ENVIRONMENT_STATE_OUTPUT_SURFACE_PHASE,
    SURFACE_STATUS_NO_DISPLAYABLE_MATERIAL,
    SURFACE_STATUS_RENDERED,
    build_analysis_environment_state_output_surface_material,
)


def _period_material(record_count: int = 3) -> dict:
    base = [
        {
            "id": "r1",
            "created_at": "2026-05-18T09:00:00Z",
            "category": ["仕事"],
            "emotion_details": [{"type": "不安", "strength": "medium"}],
            "memo": "この職場でやっていけるか不安",
            "memo_action": "新しい仕事を任された",
        },
        {
            "id": "r2",
            "created_at": "2026-05-19T10:00:00Z",
            "category": ["仕事"],
            "emotion_details": [{"type": "不安", "strength": "strong"}],
            "memo": "ここにいていいか不安",
            "memo_action": "会議で役割が増えた",
        },
        {
            "id": "r3",
            "created_at": "2026-05-20T11:00:00Z",
            "category": ["仕事"],
            "emotion_details": [{"type": "不安", "strength": "weak"}],
            "memo": "このまま続けられるか分からない",
            "memo_action": "締切の調整をした",
        },
    ]
    return build_analysis_environment_state_output_material(
        base[:record_count],
        period_kind="weekly",
        period_label="2026-05-18/2026-05-24",
        start_at="2026-05-18T00:00:00Z",
        end_at="2026-05-24T23:59:59Z",
    )


def test_phase8_builds_period_scoped_analysis_surface_without_raw_memo_text() -> None:
    material = _period_material()
    surface = build_analysis_environment_state_output_surface_material(material)
    encoded = json.dumps(surface, ensure_ascii=False, sort_keys=True)

    assert surface["schema_version"] == "cocolon.analysis.environment_state_output_surface.v1"
    assert surface["material_id"] == ANALYSIS_ENVIRONMENT_STATE_OUTPUT_SURFACE_MATERIAL_ID
    assert surface["phase"] == ANALYSIS_ENVIRONMENT_STATE_OUTPUT_SURFACE_PHASE
    assert surface["status"] == SURFACE_STATUS_RENDERED
    assert surface["surface_policy"]["public_analysis_text_connected"] is True
    assert surface["surface_policy"]["required_scope_marker"] == "この期間の記録では"
    assert surface["surface_policy"]["diagnosis_allowed"] is False
    assert surface["surface_policy"]["personality_type_allowed"] is False
    assert surface["surface_policy"]["cause_from_category"] is False
    assert surface["surface_policy"]["cause_from_emotion_strength"] is False
    assert surface["surface_policy"]["raw_text_included"] is False
    assert surface["surface_policy"]["standardReport_contract_untouched"] is True
    assert surface["surface_policy"]["contentText_contract_untouched"] is True

    assert "この期間の記録では" in surface["content_text"]
    assert "仕事カテゴリで不安が選ばれた入力" in surface["content_text"]
    assert "継続できるかへの心配" in surface["content_text"]
    assert "3件" in surface["content_text"]
    assert "3日分" in surface["content_text"]

    assert len(surface["composer_material_sources"]) == 1
    assert surface["composer_material_fields"] == ["summary", "category", "emotion"]
    assert surface["source_claims"][0]["record_count"] == 3
    assert surface["source_claims"][0]["distinct_day_count"] == 3
    assert surface["source_claims"][0]["must_include_period_scope"] is True

    assert "この職場でやっていけるか不安" not in encoded
    assert "ここにいていいか不安" not in encoded
    assert "このまま続けられるか分からない" not in encoded
    assert "あなたはこういう人" not in surface["content_text"]
    assert "戻りやすい" not in surface["content_text"]
    assert "回復方法" not in surface["content_text"]


def test_phase8_analysis_composer_accepts_phase7_material_directly_and_keeps_contracts() -> None:
    material = _period_material()
    evaluation = evaluate_analysis_environment_state_output_material(
        material,
        target_period="2026-05-18/2026-05-24",
    )

    assert evaluation.passed is True
    assert evaluation.text.startswith("この期間の記録では")
    assert "継続できるかへの心配" in evaluation.text
    assert "あなたは" not in evaluation.text
    assert "原因" not in evaluation.text
    assert "戻りやすい" not in evaluation.text

    meta = evaluation.as_meta()
    surface_meta = meta["meta"]["environment_state_output_surface"]
    assert surface_meta["material_id"] == ANALYSIS_ENVIRONMENT_STATE_OUTPUT_SURFACE_MATERIAL_ID
    assert surface_meta["analysis_composer_surface_connected"] is True
    assert surface_meta["content_text_in_meta"] is False
    assert surface_meta["raw_text_included"] is False
    assert meta["standardReport_contract_untouched"] is True
    assert meta["contentText_contract_untouched"] is True
    assert meta["content_json_contract_touched"] is False
    assert meta["analysis_composer_connected"] is True
    assert meta["runtime_connected"] is True


def test_phase8_direct_analysis_composer_connection_converts_phase7_material_to_safe_sources() -> None:
    material = _period_material(record_count=2)
    evaluation = evaluate_analysis_composer(
        material_sources=material,
        target_period="2026-05-18/2026-05-24",
    )

    assert evaluation.passed is True
    assert evaluation.domain == "emotion_structure"
    assert "この期間の記録では" in evaluation.text
    assert "2件" in evaluation.text
    assert evaluation.contract.meta["matching_material_count"] == 1
    assert "summary" in evaluation.contract.meta["material_fields"]
    assert "category" in evaluation.contract.meta["material_fields"]
    assert "emotion" in evaluation.contract.meta["material_fields"]
    assert not evaluation.rejection_reasons


def test_phase8_single_record_material_does_not_become_display_tendency() -> None:
    material = _period_material(record_count=1)
    surface = build_analysis_environment_state_output_surface_material(material)
    evaluation = evaluate_analysis_environment_state_output_material(material)

    assert surface["status"] == SURFACE_STATUS_NO_DISPLAYABLE_MATERIAL
    assert surface["content_text"] == ""
    assert surface["composer_material_sources"] == []
    assert surface["surface_policy"]["record_count_required_for_tendency"] == 2
    assert evaluation.passed is False
    assert evaluation.text == ""


def test_phase8_recovery_label_path_surface_is_sequence_observation_not_recovery_prescription() -> None:
    material = build_analysis_environment_state_output_material(
        [
            {
                "id": "path-1",
                "created_at": "2026-05-18T09:00:00Z",
                "category": ["仕事"],
                "emotion_details": [{"type": "不安", "strength": "strong"}],
                "memo": "この職場でやっていけるか不安",
            },
            {
                "id": "path-2",
                "created_at": "2026-05-18T12:00:00Z",
                "category": ["自己理解"],
                "emotion_details": [{"type": "自己理解", "strength": "medium"}],
                "memo": "不安だった理由が少し見えた",
            },
        ],
        period_kind="weekly",
    )
    surface = build_analysis_environment_state_output_surface_material(material)
    evaluation = evaluate_analysis_environment_state_output_material(material)

    assert surface["status"] == SURFACE_STATUS_RENDERED
    assert "その後の記録では" in surface["content_text"]
    assert "戻りやすい" not in surface["content_text"]
    assert "回復方法" not in surface["content_text"]
    assert "治る" not in surface["content_text"]
    assert surface["source_claims"][0]["claim_kind"] == "recovery_label_path_sequence_observation"
    assert surface["source_claims"][0]["must_not_call_cure"] is True
    assert surface["source_claims"][0]["must_not_prescribe"] is True
    assert evaluation.passed is True
    assert "その後の記録では" in evaluation.text


def test_phase8_analysis_text_safety_rejects_recovery_prescription_surface() -> None:
    result = evaluate_analysis_report_text_safety(
        "この期間の記録では、仕事の不安のあと自己理解へ戻りやすい回復方法が見えます。",
        domain="emotion_structure",
        material_fields=["summary", "category", "emotion"],
        target_period="2026-05-18/2026-05-24",
    )

    assert result.passed is False
    assert "戻りやすい" in result.matched_texts or "回復方法" in result.matched_texts
