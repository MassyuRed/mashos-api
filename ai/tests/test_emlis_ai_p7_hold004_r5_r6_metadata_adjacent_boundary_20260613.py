# -*- coding: utf-8 -*-
from __future__ import annotations

import pytest

from emlis_ai_complete_composer_client import (
    _unavailable_response,
    build_complete_composer_body_free_metadata_summary,
)
from emlis_ai_p7_hold004_path_matrix import (
    P7_HOLD004_PHASE16_PUBLIC_ADJACENT_RED_REGISTRATION_SCHEMA_VERSION,
    assert_p7_hold004_phase16_public_adjacent_red_registration_contract,
    build_p7_hold004_phase16_adjacent_public_fixture_row,
    build_p7_hold004_phase16_public_adjacent_red_registration,
)
from emlis_ai_p7_hold004_phase16_composer_classification import (
    build_p7_hold004_phase16_composer_observation,
)


def _surface_unavailable_extra_meta() -> dict:
    return {
        "state_answer_two_stage_display_required": True,
        "state_answer_section_labels_required": True,
        "state_answer_expected_comment_text_shape": "labelled_two_stage_text",
        "two_stage_section_surface_plan_connected": True,
        "two_stage_section_surface_plan_required": True,
        "two_stage_section_surface_plan_section_ids": ["observation", "reception"],
        "surface_realizer": {
            "status": "ready",
            "ready": False,
            "validation_errors": ["tone_guard:ending_family_repetition"],
            "two_stage_surface_realization": {
                "required": True,
                "applied": True,
                "labels_present": True,
                "section_order_valid": True,
                "observation_section_non_empty": True,
                "reception_section_non_empty": True,
                "section_line_counts": {"observation": 1, "reception": 2},
                "validation_errors": [],
            },
        },
        "surface_candidate_boundary": {
            "surface_structural_ready": True,
            "surface_display_quality_blocked_before_display_gate": True,
            "display_quality_reason_codes": ["tone_guard:ending_family_repetition"],
        },
    }


def test_r5_unavailable_response_keeps_phase16_summary_at_top_level_without_body_payload() -> None:
    extra = _surface_unavailable_extra_meta()

    summary = build_complete_composer_body_free_metadata_summary(extra)
    assert summary["state_answer_two_stage_display_required"] is True
    assert summary["state_answer_section_labels_required"] is True
    assert summary["state_answer_expected_comment_text_shape"] == "labelled_two_stage_text"
    assert summary["two_stage_section_surface_plan_connected"] is True
    assert summary["two_stage_section_surface_plan_required"] is True
    assert summary["two_stage_section_surface_plan_section_ids"] == ["observation", "reception"]
    assert summary["two_stage_surface_realization_required"] is True
    assert summary["two_stage_surface_realization_applied"] is True
    assert summary["two_stage_surface_structural_ready"] is True
    assert summary["surface_display_quality_blocked_before_display_gate"] is True
    assert "tone_guard:ending_family_repetition" in summary["surface_display_quality_reason_codes_before_display_gate"]
    assert summary["comment_text_body_included"] is False
    assert summary["surface_body_included"] is False
    assert summary["candidate_body_included"] is False
    assert summary["raw_input_included"] is False
    assert summary["public_response_key_added"] is False

    response = _unavailable_response(
        "complete_initial_surface_unavailable",
        coverage_scope="daily_unpleasant",
        extra_meta=extra,
    )
    meta = response["composer_meta"]
    assert response["status"] == "unavailable"
    assert meta["state_answer_two_stage_display_required"] is True
    assert meta["two_stage_surface_realization_required"] is True
    assert meta["two_stage_surface_realization_applied"] is True
    assert meta["two_stage_surface_structural_ready"] is True
    assert meta["surface_display_quality_blocked_before_display_gate"] is True
    assert meta["comment_text_body_included"] is False
    assert meta["surface_body_included"] is False
    assert meta["candidate_body_included"] is False
    assert meta["raw_input_included"] is False
    assert "comment_text" not in meta


def test_r5_phase16_observation_can_classify_from_top_level_summary_only() -> None:
    meta = build_complete_composer_body_free_metadata_summary(_surface_unavailable_extra_meta())
    meta.update(
        {
            "status": "unavailable",
            "primary_reason": "complete_initial_surface_unavailable",
            "phase17_7_unavailable_reason_codes": ["phase17_surface_mode_policy_missing"],
            "phase17_7_self_repair_handoff_reason_codes": ["template_like"],
        }
    )

    observation = build_p7_hold004_phase16_composer_observation(
        path_id="complete_composer_direct_daily_unpleasant_A",
        test_ref="tests/test_emlis_ai_complete_composer_two_stage_surface_connection.py::summary_only",
        fixture_family="daily_unpleasant_encounter_A",
        composer_meta=meta,
        observed_status="unavailable",
    )

    assert observation["two_stage_surface_summary"]["required"] is True
    assert observation["two_stage_surface_summary"]["applied"] is True
    assert observation["two_stage_surface_summary"]["labels_present"] is True
    assert observation["two_stage_surface_summary"]["observation_section_non_empty"] is True
    assert observation["two_stage_surface_summary"]["reception_section_non_empty"] is True
    assert observation["surface_quality_summary"]["surface_structural_ready"] is True
    assert observation["surface_quality_summary"]["surface_display_quality_blocked"] is True
    assert observation["owner_layer"] == "complete_surface_realizer_tone_boundary"
    assert observation["body_free_markers"]["comment_text_body_included"] is False


def test_r6_adjacent_public_red_registration_is_separate_unresolved_and_not_closure() -> None:
    adjacent_row = build_p7_hold004_phase16_adjacent_public_fixture_row()
    registration = build_p7_hold004_phase16_public_adjacent_red_registration(
        adjacent_row=adjacent_row,
        primary_target_paths_repaired=True,
    )

    assert registration["schema_version"] == P7_HOLD004_PHASE16_PUBLIC_ADJACENT_RED_REGISTRATION_SCHEMA_VERSION
    assert_p7_hold004_phase16_public_adjacent_red_registration_contract(registration)
    assert registration["status"] == "ADJACENT_PUBLIC_RED_REGISTERED_UNRESOLVED"
    assert registration["classification"] == "positive_public_fixture_shape_boundary"
    assert registration["primary_target_paths_repaired"] is True
    assert registration["primary_target_repair_does_not_close_adjacent_red"] is True
    assert registration["daily_A_direct_red_not_merged_with_positive_public_red"] is True
    assert registration["adjacent_public_red_registered"] is True
    assert registration["adjacent_public_red_path_id"] == "emotion_submit_public_product_visible_fixture_suite"
    assert registration["adjacent_public_red_fixture_family"] == "positive_change_after_work_streaming"
    assert registration["next_split_target"] == "positive_public_fixture_shape_boundary"
    assert registration["full_backend_suite_green_confirmed"] is False
    assert registration["hold004_close_allowed"] is False
    assert registration["p8_start_allowed"] is False
    assert registration["release_allowed"] is False


def test_r6_adjacent_red_registration_rejects_closure_and_body_payload() -> None:
    registration = build_p7_hold004_phase16_public_adjacent_red_registration(
        primary_target_paths_repaired=True,
    )

    closure = dict(registration)
    closure["hold004_close_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_phase16_public_adjacent_red_registration_contract(closure)

    payload = dict(registration)
    payload["comment_text"] = "forbidden public body"
    with pytest.raises(ValueError):
        assert_p7_hold004_phase16_public_adjacent_red_registration_contract(payload)
