from __future__ import annotations

import json

from cocolon_text_generation_core.adapters.analysis_environment_state_output_material import (
    ANALYSIS_ENVIRONMENT_STATE_OUTPUT_MATERIAL_ID,
    ANALYSIS_ENVIRONMENT_STATE_OUTPUT_PHASE,
    ANALYSIS_ENVIRONMENT_STATE_OUTPUT_MATERIAL_SCHEMA_VERSION,
    CONDITIONAL_OUTPUT_TENDENCY_MATERIAL_ID,
    RECOVERY_LABEL_PATH_MATERIAL_ID,
    build_analysis_environment_state_output_material,
    summarize_analysis_environment_state_output_material,
)


def test_phase7_builds_conditional_output_tendency_internal_material_without_public_surface() -> None:
    records = [
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

    material = build_analysis_environment_state_output_material(
        records,
        period_kind="weekly",
        period_label="2026-05-18/2026-05-24",
        start_at="2026-05-18T00:00:00Z",
        end_at="2026-05-24T23:59:59Z",
    )
    encoded = json.dumps(material, ensure_ascii=False, sort_keys=True)

    assert material["schema_version"] == ANALYSIS_ENVIRONMENT_STATE_OUTPUT_MATERIAL_SCHEMA_VERSION
    assert material["material_id"] == ANALYSIS_ENVIRONMENT_STATE_OUTPUT_MATERIAL_ID
    assert material["phase"] == ANALYSIS_ENVIRONMENT_STATE_OUTPUT_PHASE
    assert material["surface_policy"]["internal_material_only"] is True
    assert material["surface_policy"]["public_analysis_text_connected"] is False
    assert material["surface_policy"]["analysis_content_payload_changed"] is False
    assert material["surface_policy"]["cause_from_category"] is False
    assert material["surface_policy"]["cause_from_emotion_strength"] is False
    assert material["domain_boundary"]["emotion_self_structure_material_mixing_allowed"] is False
    assert material["source_summary"]["usable_frame_count"] == 3

    tendencies = material["conditional_output_tendencies"]
    assert len(tendencies) == 1
    tendency = tendencies[0]
    assert tendency["material_id"] == CONDITIONAL_OUTPUT_TENDENCY_MATERIAL_ID
    assert tendency["query_key"] == {
        "environment_key": "仕事",
        "state_key": "不安",
        "output_theme_key": "continuation_concern",
    }
    assert tendency["record_count"] == 3
    assert tendency["distinct_day_count"] == 3
    assert tendency["recurrence_level"] == "period_tendency_candidate"
    assert tendency["allowed_surface"]["scope_marker"] == "この期間の記録では"
    assert tendency["allowed_surface"]["public_analysis_text_connected"] is False
    assert tendency["cause_from_category"] is False
    assert tendency["cause_from_emotion_strength"] is False
    assert tendency["diagnosis_allowed"] is False

    assert "あなたは仕事継続不安タイプ" not in encoded
    assert "仕事が原因" not in encoded
    assert "この職場でやっていけるか不安" not in encoded
    assert "ここにいていいか不安" not in encoded
    assert "このまま続けられるか分からない" not in encoded
    assert '"raw_text"' not in encoded


def test_phase7_single_record_does_not_become_period_tendency() -> None:
    material = build_analysis_environment_state_output_material(
        [
            {
                "id": "single-1",
                "created_at": "2026-05-18T09:00:00Z",
                "category": ["仕事"],
                "emotion_details": [{"type": "不安", "strength": "medium"}],
                "memo": "この職場でやっていけるか不安",
            }
        ],
        period_kind="weekly",
    )

    assert material["source_summary"]["input_record_count"] == 1
    assert material["source_summary"]["usable_frame_count"] == 1
    assert material["conditional_output_tendencies"] == []
    assert material["surface_policy"]["diagnosis_allowed"] is False
    assert "cause_from_category" in material["surface_policy"]["forbidden_claims"]


def test_phase7_recovery_label_path_is_sequence_observation_not_prescription() -> None:
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

    paths = material["recovery_label_paths"]
    assert len(paths) == 1
    path = paths[0]
    assert path["material_id"] == RECOVERY_LABEL_PATH_MATERIAL_ID
    assert path["recurrence_level"] == "single_path_observation"
    assert path["allowed_surface"]["max_claim_strength"] == "sequence_observation"
    assert path["allowed_surface"]["must_not_call_cure"] is True
    assert path["allowed_surface"]["must_not_prescribe"] is True
    assert path["allowed_surface"]["public_analysis_text_connected"] is False
    assert path["diagnosis_allowed"] is False
    assert path["treatment_claim_allowed"] is False
    assert path["recovery_prescription_allowed"] is False
    assert "cured" in path["forbidden_claims"]
    assert "this_is_the_solution" in path["forbidden_claims"]


def test_phase7_rejects_self_structure_material_mixing_internally() -> None:
    material = build_analysis_environment_state_output_material(
        [
            {
                "id": "self-only-1",
                "text_primary": "人との距離を取りたい記録。",
                "role_hint": "対人距離",
                "target_hint": "関係性",
            }
        ],
        period_kind="weekly",
    )

    assert material["source_summary"]["input_record_count"] == 1
    assert material["source_summary"]["usable_frame_count"] == 0
    assert material["conditional_output_tendencies"] == []
    assert material["recovery_label_paths"] == []
    assert material["domain_boundary"]["source_domain_separated"] is False
    assert material["domain_boundary"]["rejected_source_count"] == 1
    assert material["domain_boundary"]["emotion_self_structure_material_mixing_allowed"] is False
    assert material["domain_boundary"]["public_analysis_text_connected"] is False


def test_phase7_summary_is_meta_only_and_text_free() -> None:
    material = build_analysis_environment_state_output_material(
        [
            {
                "id": "r1",
                "created_at": "2026-05-18T09:00:00Z",
                "category": ["仕事"],
                "emotion_details": [{"type": "不安", "strength": "medium"}],
                "memo": "この職場でやっていけるか不安",
            },
            {
                "id": "r2",
                "created_at": "2026-05-19T09:00:00Z",
                "category": ["仕事"],
                "emotion_details": [{"type": "不安", "strength": "medium"}],
                "memo": "ここにいていいか不安",
            },
        ],
        period_kind="weekly",
    )

    summary = summarize_analysis_environment_state_output_material(material)
    encoded = json.dumps(summary, ensure_ascii=False, sort_keys=True)

    assert summary["material_id"] == ANALYSIS_ENVIRONMENT_STATE_OUTPUT_MATERIAL_ID
    assert summary["conditional_output_tendency_count"] == 1
    assert summary["public_analysis_text_connected"] is False
    assert summary["raw_text_included"] is False
    assert "この職場でやっていけるか不安" not in encoded
    assert "ここにいていいか不安" not in encoded
