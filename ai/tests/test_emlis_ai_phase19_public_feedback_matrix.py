# -*- coding: utf-8 -*-
from __future__ import annotations

import pytest

from helpers.emlis_ai_phase19_public_feedback_matrix import (
    PHASE19_PUBLIC_FEEDBACK_MATRIX_ID,
    PHASE19_PUBLIC_FEEDBACK_MATRIX_SCHEMA_VERSION,
    PHASE19_PUBLIC_FEEDBACK_MATRIX_SOURCE_PHASE,
    VISIBLE_SURFACE_GATE_FAILED,
    VISIBLE_SURFACE_GATE_NOT_REACHED,
    VISIBLE_SURFACE_GATE_PASSED,
    assert_phase19_public_feedback_matrix_meta_only,
    build_phase19_public_feedback_recovery_matrix,
    validate_phase19_public_feedback_recovery_matrix,
)


def test_phase19_1_public_feedback_recovery_matrix_records_backend_blocker_without_public_body_leak() -> None:
    matrix = build_phase19_public_feedback_recovery_matrix(
        case_id="phase19_real_device_C_self_understanding_learning_shift",
        expected_public_feedback=True,
        current_input={
            "memo": "これはmatrixに含めてはいけない入力本文です。",
            "memo_action": "これはmatrixに含めてはいけない行動本文です。",
            "emotions": ["自己理解"],
            "category": ["学習"],
        },
        public_meta={
            "observation_status": "rejected",
            "diagnostic_summary": {
                "composer_status": "generated",
                "complete_initial_candidate_generation_path": {
                    "candidate_status_before_display_gate": "generated",
                    "candidate_source": "complete_initial",
                },
            },
            "visible_surface_acceptance_gate": {
                "passed": False,
                "rejection_reasons": [
                    "surface_relation_skeleton_major",
                    "limited_composer_repeated_surface",
                ],
            },
        },
        diagnostic_meta={
            "diagnostic_summary": {
                "gate_results": {
                    "visible_surface_acceptance": {
                        "passed": False,
                        "rejection_reasons": ["phase8_repeated_sentence_tail"],
                    }
                }
            }
        },
        reply_comment_text="",
        response_body={"status": "ok", "input_feedback": None},
    )

    assert matrix["schema_version"] == PHASE19_PUBLIC_FEEDBACK_MATRIX_SCHEMA_VERSION
    assert matrix["source_phase"] == PHASE19_PUBLIC_FEEDBACK_MATRIX_SOURCE_PHASE
    assert matrix["matrix_id"] == PHASE19_PUBLIC_FEEDBACK_MATRIX_ID
    assert matrix["expected_public_feedback"] is True
    assert matrix["current_input"] == {
        "memo_present": True,
        "memo_action_present": True,
        "emotions_present": True,
        "categories_present": True,
        "memo_text_len": len("これはmatrixに含めてはいけない入力本文です。"),
        "memo_action_text_len": len("これはmatrixに含めてはいけない行動本文です。"),
    }
    assert matrix["safety"] == {"safety_blocked": False, "safety_reason": None}
    assert matrix["candidate"] == {
        "generation_attempted": True,
        "generated_before_display_gate": True,
        "source": "complete_initial",
        "first_failure_reason": "limited_composer_repeated_surface",
    }
    assert matrix["surface_gate"]["visible_surface_acceptance_gate"] == VISIBLE_SURFACE_GATE_FAILED
    assert matrix["surface_gate"]["rejection_reasons"] == [
        "limited_composer_repeated_surface",
        "phase8_repeated_sentence_tail",
        "surface_relation_skeleton_major",
    ]
    assert matrix["public_feedback"] == {
        "comment_text_present": False,
        "public_observation_status": "rejected",
        "input_feedback_included": False,
        "first_backend_blocker": "surface_relation_skeleton_major",
    }
    assert matrix["rn_contract"] == {"modal_should_open": False, "modal_title": "Emlisの観測"}
    assert_phase19_public_feedback_matrix_meta_only(
        matrix,
        forbidden_text_fragments=(
            "これはmatrixに含めてはいけない入力本文です。",
            "これはmatrixに含めてはいけない行動本文です。",
        ),
    )


def test_phase19_1_public_feedback_recovery_matrix_records_passed_public_contract() -> None:
    matrix = build_phase19_public_feedback_recovery_matrix(
        case_id="phase19_green_contract_sample",
        expected_public_feedback=True,
        current_input={"memo": "本文はmatrixへ出さない", "emotions": ["喜び"], "category": ["生活"]},
        public_meta={
            "observation_status": "passed",
            "diagnostic_summary": {
                "composer_status": "generated",
                "complete_initial_candidate_generation_path": {
                    "candidate_status": "generated",
                    "candidate_source": "complete_initial",
                },
                "gate_results": {"visible_surface_acceptance": {"passed": True}},
            },
        },
        diagnostic_meta={},
        reply_comment_text="Emlisです。表示できる商品文です。",
        response_body={
            "status": "ok",
            "input_feedback": {
                "comment_text": "Emlisです。表示できる商品文です。",
                "emlis_ai": {"observation_status": "passed"},
            },
        },
    )

    assert matrix["candidate"]["generated_before_display_gate"] is True
    assert matrix["surface_gate"]["visible_surface_acceptance_gate"] == VISIBLE_SURFACE_GATE_PASSED
    assert matrix["public_feedback"] == {
        "comment_text_present": True,
        "public_observation_status": "passed",
        "input_feedback_included": True,
        "first_backend_blocker": None,
    }
    assert matrix["rn_contract"]["modal_should_open"] is True
    assert_phase19_public_feedback_matrix_meta_only(matrix, forbidden_text_fragments=("本文はmatrixへ出さない",))


def test_phase19_1_public_feedback_recovery_matrix_records_not_reached_candidate_failure() -> None:
    matrix = build_phase19_public_feedback_recovery_matrix(
        case_id="phase19_real_device_D_relationship_gratitude_recovery",
        expected_public_feedback=True,
        current_input={"memo": "D raw memo", "memo_action": "D raw action", "emotions": ["喜び"], "category": ["恋愛"]},
        public_meta={
            "observation_status": "unavailable",
            "diagnostic_summary": {
                "composer_status": "unavailable",
                "complete_initial_candidate_generation_path": {
                    "candidate_status": "unavailable",
                    "first_failure_reason": "empty_comment_text_without_candidate",
                },
            },
        },
        diagnostic_meta={},
        reply_comment_text="",
        response_body={"status": "ok", "input_feedback": None},
    )

    assert matrix["candidate"] == {
        "generation_attempted": True,
        "generated_before_display_gate": False,
        "source": None,
        "first_failure_reason": "empty_comment_text_without_candidate",
    }
    assert matrix["surface_gate"]["visible_surface_acceptance_gate"] == VISIBLE_SURFACE_GATE_NOT_REACHED
    assert matrix["public_feedback"]["first_backend_blocker"] == "empty_comment_text_without_candidate"
    assert matrix["rn_contract"]["modal_should_open"] is False
    assert_phase19_public_feedback_matrix_meta_only(matrix, forbidden_text_fragments=("D raw memo", "D raw action"))


def test_phase19_1_public_feedback_recovery_matrix_validation_rejects_shape_drift() -> None:
    matrix = build_phase19_public_feedback_recovery_matrix(
        case_id="phase19_shape_guard",
        expected_public_feedback=False,
        current_input={},
        public_meta={"observation_status": "safety_blocked"},
        response_body={"input_feedback": None},
    )
    matrix["public_feedback"]["extra_public_key"] = True

    with pytest.raises(AssertionError, match="public_feedback"):
        validate_phase19_public_feedback_recovery_matrix(matrix)
