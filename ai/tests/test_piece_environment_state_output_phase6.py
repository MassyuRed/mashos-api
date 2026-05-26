# -*- coding: utf-8 -*-
from __future__ import annotations

from cocolon_environment_state_output_frame import build_environment_state_output_frame
from cocolon_text_generation_core.adapters.piece_composer import (
    build_runtime_piece_plan,
    evaluate_piece_composer,
)
from cocolon_text_generation_core.adapters.piece_environment_state_output_guard import (
    build_piece_environment_state_output_guard,
)
from emotion_piece_generation_service import generate_emotion_reflection_preview


_CURRENT_INPUT = {
    "emotion_details": [{"type": "不安", "strength": "medium"}],
    "memo": "この職場でやっていけるか不安",
    "memo_action": "職場で新しい仕事を任された",
    "category": ["仕事"],
}


def _frame() -> dict:
    return build_environment_state_output_frame(
        _CURRENT_INPUT,
        observation_structure_relation_ids=[],
    )


def test_phase6_piece_preview_keeps_environment_state_output_conditions() -> None:
    preview = generate_emotion_reflection_preview(
        emotion_details=[{"type": "不安", "strength": "medium"}],
        memo="この職場でやっていけるか不安",
        memo_action="職場で新しい仕事を任された",
        categories=["仕事"],
    )

    answer = preview["answer_display_text"]
    piece_core = preview["piece_core"]
    text_generation_core = piece_core["text_generation_core"]
    input_contract = text_generation_core["input_contract"]

    assert preview["answer_display_state"] == "ready"
    assert "仕事" in answer
    assert "不安" in answer
    assert "やっていける" in answer
    assert answer != "不安です。"
    assert piece_core["environment_state_output_frame_connected"] is True
    assert piece_core["environment_state_output_must_keep_applied"] is True
    assert "eso_environment:仕事" in piece_core["environment_state_output_must_keep_signal_keys"]
    assert "eso_state:不安" in piece_core["environment_state_output_must_keep_signal_keys"]
    assert "eso_output:continuation_concern" in piece_core["environment_state_output_must_keep_signal_keys"]
    assert input_contract["environment_state_output_must_keep_applied"] is True
    assert input_contract["environment_state_output_overcompression_risk"] is True


def test_phase6_piece_composer_rejects_state_only_overcompression() -> None:
    frame = _frame()
    source_texts = [
        "この職場でやっていけるか不安",
        "職場で新しい仕事を任された",
        "仕事",
        "不安",
    ]
    plan = build_runtime_piece_plan(
        question="仕事で気にしていることは？",
        answer="不安です。",
        source_texts=source_texts,
        environment_state_output_frame=frame,
    )

    evaluation = evaluate_piece_composer(
        plan,
        question_text="仕事で気にしていることは？",
        answer_text="不安です。",
        source_texts=source_texts,
    )

    assert evaluation.passed is False
    assert any("must_keep_text_missing" in reason for reason in evaluation.rejection_reasons)
    assert evaluation.as_meta()["environment_state_output_must_keep_applied"] is True


def test_phase6_piece_guard_is_text_free_and_internal_only() -> None:
    guard = build_piece_environment_state_output_guard(_frame())
    dumped = str(guard)

    assert guard["connected"] is True
    assert guard["must_keep_signal_keys_applied"] is True
    assert guard["raw_text_included"] is False
    assert guard["public_response_key_added"] is False
    assert "この職場でやっていけるか不安" not in dumped
    assert "職場で新しい仕事を任された" not in dumped
    assert "仕事" in guard["category_labels"]
    assert "不安" in guard["emotion_labels"]
    assert "continuation_concern" in guard["output_theme_ids"]


def test_phase6_piece_guard_does_not_apply_without_output_theme() -> None:
    frame = build_environment_state_output_frame(
        {
            "emotion_details": [{"type": "不安", "strength": "strong"}],
            "memo": "なんとなく怖い",
            "memo_action": "",
            "category": ["仕事"],
        },
        observation_structure_relation_ids=[],
    )
    guard = build_piece_environment_state_output_guard(frame)

    assert guard["connected"] is True
    assert guard["must_keep_signal_keys_applied"] is False
    assert guard["must_keep_signal_keys"] == []
    assert guard["overcompression_risk"] is False
    assert guard["raw_text_included"] is False
