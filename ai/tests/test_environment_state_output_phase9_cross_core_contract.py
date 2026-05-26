# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path

from cocolon_environment_state_output_frame import build_environment_state_output_frame
from cocolon_text_generation_core.adapters.analysis_composer import (
    evaluate_analysis_environment_state_output_material,
    evaluate_analysis_report_text_safety,
)
from cocolon_text_generation_core.adapters.analysis_environment_state_output_material import (
    build_analysis_environment_state_output_material,
)
from cocolon_text_generation_core.adapters.analysis_environment_state_output_surface import (
    ANALYSIS_ENVIRONMENT_STATE_OUTPUT_SURFACE_MATERIAL_ID,
    build_analysis_environment_state_output_surface_material,
)
from cocolon_text_generation_core.adapters.piece_environment_state_output_guard import (
    build_piece_environment_state_output_guard,
)
from emlis_ai_observation_structure_material_service import build_observation_structure_material
from emlis_ai_state_answer_surface_contract import build_emlis_state_answer_surface_contract
from emlis_ai_public_feedback_meta import (
    build_public_emlis_input_feedback_meta,
    should_include_public_input_feedback,
)


_WORK_ANXIETY_INPUT = {
    "id": "phase9-eso-current-001",
    "created_at": "2026-05-25T06:00:00Z",
    "memo": "この職場でやっていけるか不安",
    "memo_action": "職場で新しい仕事を任された",
    "emotion_details": [{"type": "不安", "strength": "medium"}],
    "category": ["仕事"],
}


_PERIOD_RECORDS = [
    {
        "id": "phase9-period-001",
        "created_at": "2026-05-18T09:00:00Z",
        "category": ["仕事"],
        "emotion_details": [{"type": "不安", "strength": "medium"}],
        "memo": "この職場でやっていけるか不安",
        "memo_action": "新しい仕事を任された",
    },
    {
        "id": "phase9-period-002",
        "created_at": "2026-05-19T10:00:00Z",
        "category": ["仕事"],
        "emotion_details": [{"type": "不安", "strength": "strong"}],
        "memo": "ここにいていいか不安",
        "memo_action": "会議で役割が増えた",
    },
    {
        "id": "phase9-period-003",
        "created_at": "2026-05-20T11:00:00Z",
        "category": ["仕事"],
        "emotion_details": [{"type": "不安", "strength": "weak"}],
        "memo": "このまま続けられるか分からない",
        "memo_action": "締切の調整をした",
    },
]


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def test_phase9_cross_core_roles_are_separated_for_environment_state_output_material() -> None:
    frame = build_environment_state_output_frame(
        _WORK_ANXIETY_INPUT,
        observation_structure_relation_ids=[],
    )
    emlis_material = build_observation_structure_material(current_input=_WORK_ANXIETY_INPUT)
    emlis_meta = emlis_material.as_meta()
    piece_guard = build_piece_environment_state_output_guard(frame)
    analysis_material = build_analysis_environment_state_output_material(
        _PERIOD_RECORDS,
        period_kind="weekly",
        period_label="2026-05-18/2026-05-24",
        start_at="2026-05-18T00:00:00Z",
        end_at="2026-05-24T23:59:59Z",
    )
    analysis_surface = build_analysis_environment_state_output_surface_material(analysis_material)

    assert frame["time_axis"]["period_scope"] == "single_record"
    assert frame["surface_policy"]["single_record_only"] is True
    assert frame["surface_policy"]["must_use_scope_marker"] is True
    assert frame["surface_policy"]["scope_marker"] == "今回の入力では"

    assert emlis_meta["environment_state_output_frame_connected"] is True
    assert emlis_meta["environment_state_output_frame_single_record_only"] is True
    assert emlis_meta["period_tendency_from_single_record"] is False
    assert emlis_meta["cause_from_category"] is False
    assert emlis_meta["cause_from_emotion_strength"] is False
    assert emlis_meta["recovery_prescription_allowed"] is False
    assert "continuation_concern" in emlis_meta["environment_state_output_frame"]["output_axis"]["output_theme_ids"]

    assert piece_guard["connected"] is True
    assert piece_guard["must_keep_signal_keys_applied"] is True
    assert piece_guard["must_keep_signal_keys"] == [
        "eso_environment:仕事",
        "eso_state:不安",
        "eso_output:continuation_concern",
    ]
    assert piece_guard["overcompression_risk"] is True
    assert "emlis_voice" in piece_guard["forbidden_surface_claims"]
    assert "analysis_period_tendency" in piece_guard["forbidden_surface_claims"]

    assert analysis_surface["material_id"] == ANALYSIS_ENVIRONMENT_STATE_OUTPUT_SURFACE_MATERIAL_ID
    assert analysis_surface["status"] == "rendered"
    assert analysis_surface["surface_policy"]["must_include_period_scope"] is True
    assert analysis_surface["surface_policy"]["diagnosis_allowed"] is False
    assert analysis_surface["surface_policy"]["personality_type_allowed"] is False
    assert analysis_surface["surface_policy"]["cause_from_category"] is False
    assert analysis_surface["content_text"].startswith("この期間の記録では")
    assert "今回の入力では" not in analysis_surface["content_text"]
    assert analysis_surface["composer_domain"] == "emotion_structure"
    assert analysis_surface["source_claims"][0]["claim_kind"] == "conditional_output_tendency_period_observation"


def test_phase9_cross_core_materials_do_not_leak_raw_input_or_public_response_keys() -> None:
    frame = build_environment_state_output_frame(
        _WORK_ANXIETY_INPUT,
        observation_structure_relation_ids=[],
    )
    emlis_meta = build_observation_structure_material(current_input=_WORK_ANXIETY_INPUT).as_meta()
    piece_guard = build_piece_environment_state_output_guard(frame)
    analysis_material = build_analysis_environment_state_output_material(_PERIOD_RECORDS, period_kind="weekly")
    analysis_surface = build_analysis_environment_state_output_surface_material(analysis_material)

    dumped = _json(
        {
            "frame": frame,
            "emlis_meta": emlis_meta,
            "piece_guard": piece_guard,
            "analysis_material": analysis_material,
            "analysis_surface": analysis_surface,
        }
    )

    assert "この職場でやっていけるか不安" not in dumped
    assert "職場で新しい仕事を任された" not in dumped
    assert "ここにいていいか不安" not in dumped
    assert "このまま続けられるか分からない" not in dumped
    assert '"raw_text_included": true' not in dumped
    assert '"raw_input_included": true' not in dumped
    assert piece_guard["public_response_key_added"] is False
    assert analysis_surface["surface_policy"]["content_json_mutation_allowed_here"] is False
    assert analysis_surface["surface_policy"]["standardReport_contract_untouched"] is True
    assert analysis_surface["surface_policy"]["contentText_contract_untouched"] is True


def test_phase9_public_feedback_meta_keeps_rn_display_contract_and_hides_eso_internal_material() -> None:
    internal_frame = build_environment_state_output_frame(
        _WORK_ANXIETY_INPUT,
        observation_structure_relation_ids=[],
    )
    public_meta = build_public_emlis_input_feedback_meta(
        {
            "version": "emlis_ai_v3",
            "kernel_version": "multi_perspective_observation.v1",
            "observation_status": "passed",
            "observation_trace_id": "phase9-trace",
            "environment_state_output_frame": internal_frame,
            "memo": _WORK_ANXIETY_INPUT["memo"],
            "memo_action": _WORK_ANXIETY_INPUT["memo_action"],
            "comment_text": "今回の入力では、仕事という場面で不安が選ばれています。",
            "runtime_surface_pre_return_gate": {
                "passed": True,
                "action": "allow",
                "rejection_reasons": [],
            },
            "visible_surface_acceptance_gate": {
                "evaluated": True,
                "passed": True,
                "classification": "pass",
                "action": "allow",
                "rejection_reasons": [],
            },
        },
        comment_text_present=True,
    )
    dumped = _json(public_meta)

    assert public_meta["observation_status"] == "passed"
    assert public_meta["public_feedback_meta_boundary"]["raw_input_included"] is False
    assert public_meta["public_feedback_meta_boundary"]["comment_text_included"] is False
    assert "environment_state_output_frame" not in dumped
    assert "environment_state_output_surface" not in dumped
    assert "comment_text" not in public_meta
    assert _WORK_ANXIETY_INPUT["memo"] not in dumped
    assert _WORK_ANXIETY_INPUT["memo_action"] not in dumped
    assert should_include_public_input_feedback("表示する本文", public_meta) is True
    assert should_include_public_input_feedback("", public_meta) is False

    rejected_meta = dict(public_meta)
    rejected_meta["observation_status"] = "rejected"
    assert should_include_public_input_feedback("表示する本文", rejected_meta) is False


def test_phase9_analysis_safety_rejects_cross_core_or_diagnostic_surfaces() -> None:
    forbidden_texts = [
        "この期間の記録では、あなたはこういう人です。",
        "この期間の記録では、仕事が不安の原因です。",
        "この期間の記録では、自己理解へ戻りやすい回復方法が見えます。",
        "今回の入力では、仕事カテゴリで不安が選ばれた入力が複数回見えます。",
    ]

    for text in forbidden_texts:
        result = evaluate_analysis_report_text_safety(
            text,
            domain="emotion_structure",
            material_fields=["summary", "category", "emotion"],
            target_period="2026-05-18/2026-05-24",
        )
        assert result.passed is False, text

    analysis_material = build_analysis_environment_state_output_material(_PERIOD_RECORDS, period_kind="weekly")
    evaluation = evaluate_analysis_environment_state_output_material(
        analysis_material,
        target_period="2026-05-18/2026-05-24",
    )
    assert evaluation.passed is True
    assert evaluation.text.startswith("この期間の記録では")
    assert "あなたは" not in evaluation.text
    assert "原因" not in evaluation.text
    assert "戻りやすい" not in evaluation.text
    assert "回復方法" not in evaluation.text


def test_phase9_emotion_submit_public_route_response_and_db_name_contract_are_unchanged() -> None:
    ai_root = Path(__file__).resolve().parents[1]
    source = (ai_root / "services" / "ai_inference" / "api_emotion_submit.py").read_text(encoding="utf-8")

    assert '@app.post("/emotion/submit", response_model=EmotionSubmitResponse)' in source
    assert '"friend_emotion_feed"' in source
    assert "class EmotionSubmitInputFeedback" in source
    assert "comment_text: str" in source
    assert "emlis_ai: Optional[Dict[str, Any]]" in source
    assert "class EmotionSubmitResponse" in source
    assert "status: str" in source
    assert "id: Optional[Any]" in source
    assert "created_at: str" in source
    assert "input_feedback: Optional[EmotionSubmitInputFeedback]" in source
    assert "environment_state_output_frame" not in source
    assert "analysis_environment_state_output_surface" not in source
    assert "conditional_output_tendency" not in source
    assert "recovery_label_path" not in source



def test_phase10_state_answer_material_keeps_piece_and_analysis_temperature_boundaries() -> None:
    frame = build_environment_state_output_frame(
        _WORK_ANXIETY_INPUT,
        observation_structure_relation_ids=[],
    )
    state_answer_contract = build_emlis_state_answer_surface_contract(_WORK_ANXIETY_INPUT)
    piece_guard = build_piece_environment_state_output_guard(frame)
    analysis_material = build_analysis_environment_state_output_material(
        _PERIOD_RECORDS,
        period_kind="weekly",
        period_label="2026-05-18/2026-05-24",
    )
    analysis_surface = build_analysis_environment_state_output_surface_material(analysis_material)

    state_answer_dump = _json(state_answer_contract.composer_payload())
    cross_core_dump = _json({"piece_guard": piece_guard, "analysis_surface": analysis_surface})

    assert "human_follow_layer" in state_answer_dump
    assert "primary_follow_key" in state_answer_dump
    assert "state_answer_observation" in state_answer_dump

    for forbidden in (
        "emlis_state_answer_surface_contract",
        "emlis_state_answer_composer_role_plan",
        "human_follow_layer",
        "primary_follow_key",
        "secondary_follow_keys",
        "afterglow_follow_key",
        "emlis_impression_not_fact",
        "state_answer_observation",
        "human_follow_section",
        "Emlisには",
        "Emlisの感想",
    ):
        assert forbidden not in cross_core_dump

    assert "emlis_voice" in piece_guard["forbidden_surface_claims"]
    assert piece_guard["preview_publish_contract_untouched"] is True
    assert analysis_surface["composer_domain"] == "emotion_structure"
    assert analysis_surface["content_text"].startswith("この期間の記録では")
    assert "今回の入力では" not in analysis_surface["content_text"]


def test_phase10_state_answer_and_environment_materials_are_not_public_feedback_keys() -> None:
    frame = build_environment_state_output_frame(
        _WORK_ANXIETY_INPUT,
        observation_structure_relation_ids=[],
    )
    state_answer_contract = build_emlis_state_answer_surface_contract(_WORK_ANXIETY_INPUT)
    public_meta = build_public_emlis_input_feedback_meta(
        {
            "version": "emlis_ai_v3",
            "kernel_version": "multi_perspective_observation.v1",
            "observation_status": "passed",
            "observation_trace_id": "phase10-cross-contract",
            "environment_state_output_frame": frame,
            "emlis_state_answer_surface_contract": state_answer_contract.as_meta(),
            "state_answer_surface_contract": state_answer_contract.composer_payload(),
            "memo": _WORK_ANXIETY_INPUT["memo"],
            "memo_action": _WORK_ANXIETY_INPUT["memo_action"],
            "comment_text": "今回の入力では、仕事という場面で不安が選ばれています。",
            "runtime_surface_pre_return_gate": {
                "passed": True,
                "action": "allow",
                "rejection_reasons": [],
            },
            "visible_surface_acceptance_gate": {
                "evaluated": True,
                "passed": True,
                "classification": "pass",
                "action": "allow",
                "rejection_reasons": [],
            },
        },
        comment_text_present=True,
    )
    dumped = _json(public_meta)

    assert public_meta["observation_status"] == "passed"
    assert public_meta["public_feedback_meta_boundary"]["raw_input_included"] is False
    assert public_meta["public_feedback_meta_boundary"]["comment_text_included"] is False
    for forbidden in (
        "environment_state_output_frame",
        "emlis_state_answer_surface_contract",
        "state_answer_surface_contract",
        "human_follow_layer",
        "ratio_policy",
        "observation_layer",
        "special_handling",
        "metaphor_policy",
        "surface_policy",
    ):
        assert forbidden not in dumped
    assert _WORK_ANXIETY_INPUT["memo"] not in dumped
    assert _WORK_ANXIETY_INPUT["memo_action"] not in dumped
    assert should_include_public_input_feedback("表示する本文", public_meta) is True
