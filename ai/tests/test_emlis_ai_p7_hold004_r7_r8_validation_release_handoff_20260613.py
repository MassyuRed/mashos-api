# -*- coding: utf-8 -*-
from __future__ import annotations

import copy

import pytest

from emlis_ai_p7_hold004_phase16_composer_classification import (
    P7_HOLD004_PHASE16_COMPOSER_CLASSIFICATION_SCHEMA_VERSION,
    build_p7_hold004_phase16_composer_classification,
    build_p7_hold004_phase16_composer_observation,
)
from emlis_ai_p7_hold004_path_matrix import (
    P7_HOLD004_PHASE16_DECISION_RULE_SCHEMA_VERSION,
    P7_HOLD004_PHASE16_PATH_MATRIX_SCHEMA_VERSION,
    P7_HOLD004_PHASE16_PUBLIC_ADJACENT_RED_REGISTRATION_SCHEMA_VERSION,
    build_p7_hold004_phase16_adjacent_public_fixture_row,
    build_p7_hold004_phase16_decision_rule,
    build_p7_hold004_phase16_path_matrix,
    build_p7_hold004_phase16_public_adjacent_red_registration,
)
from emlis_ai_p7_hold_matrix import (
    assert_p7_backend_suite_split_matrix_contract,
    assert_p7_r10_hold_matrix_contract,
    build_p7_backend_suite_split_matrix,
    build_p7_r10_hold_matrix,
)
from emlis_ai_p7_release_handoff import (
    assert_p7_release_decision_handoff_contract,
    build_p7_release_decision_handoff,
)
from emlis_ai_p7_validation_matrix import (
    assert_p7_validation_regression_matrix_contract,
    build_p7_validation_regression_matrix,
)


DAILY_A_CASE_ID = "daily_unpleasant_encounter_A"


def _phase16_boundary_meta() -> dict[str, object]:
    return {
        "primary_reason": "complete_initial_surface_unavailable",
        "phase17_7_unavailable_reason_codes": [
            "phase17_surface_mode_policy_missing",
            "phase17_product_visible_fixture_not_reached",
        ],
        "phase17_7_self_repair_handoff_reason_codes": [
            "phase17_surface_mode_policy_missing",
            "template_like",
        ],
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
                "daily_unpleasant_surface_quality_applied": True,
                "two_stage_mode_specific_surface_applied": True,
            },
        },
    }


def _direct_observation() -> dict[str, object]:
    return build_p7_hold004_phase16_composer_observation(
        path_id="complete_composer_direct_daily_unpleasant_A",
        test_ref=(
            "tests/test_emlis_ai_complete_composer_two_stage_surface_connection.py::"
            "test_phase16_6_complete_composer_direct_output_reaches_labelled_two_stage_text"
        ),
        fixture_family=DAILY_A_CASE_ID,
        composer_meta=_phase16_boundary_meta(),
        observed_status="unavailable",
        expected_status_kind="generated_candidate_before_display_gate",
    )


def _conversation_observation() -> dict[str, object]:
    return build_p7_hold004_phase16_composer_observation(
        path_id="conversation_composer_daily_unpleasant_A",
        test_ref=(
            "tests/test_emlis_ai_complete_composer_two_stage_surface_connection.py::"
            "test_phase16_6_conversation_composer_path_reaches_labelled_two_stage_text"
        ),
        fixture_family=DAILY_A_CASE_ID,
        composer_meta=_phase16_boundary_meta(),
        observed_status="unavailable",
        expected_status_kind="generated_candidate_before_display_gate",
    )


def _public_daily_observation() -> dict[str, object]:
    return build_p7_hold004_phase16_composer_observation(
        path_id="emotion_submit_public_daily_unpleasant_A",
        test_ref=(
            "tests/test_emotion_submit_two_stage_reception_e2e.py::"
            "test_phase16_8_emotion_submit_path_returns_public_two_stage_input_feedback"
        ),
        fixture_family=DAILY_A_CASE_ID,
        observed_status="public_feedback_labelled",
        expected_status_kind="public_labelled_two_stage_input_feedback",
        public_reached=True,
        labelled_two_stage_reached=True,
        candidate_generated_before_display_gate=False,
    )


def _hold004_materials() -> dict[str, dict[str, object]]:
    observations = [_direct_observation(), _conversation_observation(), _public_daily_observation()]
    classification = build_p7_hold004_phase16_composer_classification(observations=observations)
    path_matrix = build_p7_hold004_phase16_path_matrix(
        observations=observations,
        extra_rows=[build_p7_hold004_phase16_adjacent_public_fixture_row()],
        include_default_adjacent_public_red=False,
    )
    decision_rule = build_p7_hold004_phase16_decision_rule(path_matrix=path_matrix)
    adjacent_registration = build_p7_hold004_phase16_public_adjacent_red_registration(
        path_matrix=path_matrix,
        primary_target_paths_repaired=True,
    )
    return {
        "hold004_phase16_classification": classification,
        "hold004_path_matrix": path_matrix,
        "hold004_decision_rule": decision_rule,
        "hold004_adjacent_public_red_registration": adjacent_registration,
    }


def _rows_by_kind(matrix: dict[str, object]) -> dict[str, dict[str, object]]:
    return {str(row["check_kind"]): row for row in matrix["matrix_rows"]}  # type: ignore[index]


def test_r7_backend_split_and_hold_matrix_receive_hold004_material_without_closing_p7() -> None:
    materials = _hold004_materials()
    backend_split = build_p7_backend_suite_split_matrix(**materials)
    r10 = build_p7_r10_hold_matrix(backend_suite_split_matrix=backend_split, **materials)

    assert_p7_backend_suite_split_matrix_contract(backend_split)
    assert_p7_r10_hold_matrix_contract(r10)

    assert backend_split["hold004_phase16_classification_schema_version"] == P7_HOLD004_PHASE16_COMPOSER_CLASSIFICATION_SCHEMA_VERSION
    assert backend_split["hold004_phase16_path_matrix_schema_version"] == P7_HOLD004_PHASE16_PATH_MATRIX_SCHEMA_VERSION
    assert backend_split["hold004_phase16_decision_rule_schema_version"] == P7_HOLD004_PHASE16_DECISION_RULE_SCHEMA_VERSION
    assert (
        backend_split["hold004_phase16_adjacent_registration_schema_version"]
        == P7_HOLD004_PHASE16_PUBLIC_ADJACENT_RED_REGISTRATION_SCHEMA_VERSION
    )
    assert backend_split["hold004_phase16_classified_red_present"] is True
    assert backend_split["hold004_phase16_candidate_boundary_registered"] is True
    assert backend_split["hold004_public_adjacent_red_registered"] is True
    assert "phase16_complete_composer_candidate_boundary" in backend_split["hold004_required_followup_fixes"]
    assert "positive_public_fixture_shape_boundary" in backend_split["hold004_required_followup_fixes"]
    assert "P7-HOLD-004" in backend_split["unresolved_hold_refs"]
    assert backend_split["full_backend_suite_green_confirmed"] is False
    assert backend_split["split_green_can_close_p7_hold004"] is False
    assert backend_split["release_allowed"] is False

    assert r10["hold004_phase16_classified_red_present"] is True
    assert r10["hold004_phase16_candidate_boundary_registered"] is True
    assert "phase16_complete_composer_candidate_boundary" in r10["hold004_required_followup_fixes"]
    assert "P7-HOLD-004" in r10["unresolved_hold_refs"]
    assert r10["full_backend_suite_green_confirmed"] is False
    assert r10["release_allowed"] is False


def test_r7_validation_matrix_and_release_handoff_carry_hold004_blockers_body_free() -> None:
    materials = _hold004_materials()
    backend_split = build_p7_backend_suite_split_matrix(**materials)
    r10 = build_p7_r10_hold_matrix(backend_suite_split_matrix=backend_split, **materials)
    handoff = build_p7_release_decision_handoff(
        backend_suite_split_matrix=backend_split,
        r10_hold_matrix=r10,
        **materials,
    )
    validation = build_p7_validation_regression_matrix(
        backend_suite_split_matrix=backend_split,
        r10_hold_matrix=r10,
        release_handoff=handoff,
        **materials,
    )

    assert_p7_release_decision_handoff_contract(handoff)
    assert_p7_validation_regression_matrix_contract(validation)

    assert handoff["manual_hold_status"]["hold004_phase16_classified_red_present"] is True
    assert handoff["manual_hold_status"]["hold004_phase16_candidate_boundary_registered"] is True
    assert "phase16_complete_composer_candidate_boundary" in handoff["required_followup_fixes"]
    assert "positive_public_fixture_shape_boundary" in handoff["required_followup_fixes"]
    assert "P7-HOLD-004" in handoff["unresolved_hold_refs"]
    assert handoff["release_decision_input_ready"] is False
    assert handoff["release_allowed"] is False

    rows = _rows_by_kind(validation)
    hold004_row = rows["hold004_phase16_classified_red"]
    assert hold004_row["observed_status"] == "HOLD_UNCONFIRMED"
    assert hold004_row["green_claim_allowed"] is False
    assert hold004_row["release_blocking"] is True
    assert "P7-HOLD-004" in hold004_row["hold_refs"]
    assert validation["summary"]["hold004_phase16_classified_red_present"] is True
    assert validation["summary"]["hold004_phase16_candidate_boundary_registered"] is True
    assert validation["summary"]["hold004_public_adjacent_red_registered"] is True
    assert "phase16_complete_composer_candidate_boundary" in validation["summary"]["hold004_required_followup_fixes"]
    assert validation["summary"]["full_backend_suite_green_confirmed"] is False
    assert validation["summary"]["p8_start_allowed"] is False
    assert validation["summary"]["release_allowed"] is False


def test_r7_r8_contracts_reject_hold004_green_release_or_body_payload_promotion() -> None:
    materials = _hold004_materials()
    backend_split = build_p7_backend_suite_split_matrix(**materials)
    r10 = build_p7_r10_hold_matrix(backend_suite_split_matrix=backend_split, **materials)
    validation = build_p7_validation_regression_matrix(
        backend_suite_split_matrix=backend_split,
        r10_hold_matrix=r10,
        **materials,
    )

    backend_promoted = copy.deepcopy(backend_split)
    backend_promoted["full_backend_suite_green_confirmed"] = True
    with pytest.raises(ValueError):
        assert_p7_backend_suite_split_matrix_contract(backend_promoted)

    r10_promoted = copy.deepcopy(r10)
    r10_promoted["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_r10_hold_matrix_contract(r10_promoted)

    validation_promoted = copy.deepcopy(validation)
    validation_promoted["summary"]["p8_start_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_validation_regression_matrix_contract(validation_promoted)

    validation_body = copy.deepcopy(validation)
    validation_body["comment_text"] = "forbidden body payload"
    with pytest.raises(ValueError):
        assert_p7_validation_regression_matrix_contract(validation_body)
