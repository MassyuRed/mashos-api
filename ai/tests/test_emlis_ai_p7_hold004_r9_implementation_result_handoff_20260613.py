# -*- coding: utf-8 -*-
"""P7-HOLD-004 R9 implementation-result document and handoff boundary."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from emlis_ai_p7_hold004_phase16_composer_classification import (
    build_p7_hold004_phase16_composer_classification,
    build_p7_hold004_phase16_composer_observation,
)
from emlis_ai_p7_hold004_path_matrix import (
    P7_HOLD004_PHASE16_PUBLIC_ADJACENT_RED_REGISTRATION_SCHEMA_VERSION,
    build_p7_hold004_phase16_adjacent_public_fixture_row,
    build_p7_hold004_phase16_decision_rule,
    build_p7_hold004_phase16_path_matrix,
    build_p7_hold004_phase16_public_adjacent_red_registration,
)
from emlis_ai_p7_hold_matrix import build_p7_backend_suite_split_matrix, build_p7_r10_hold_matrix
from emlis_ai_p7_release_handoff import (
    P7_HOLD004_PHASE16_IMPLEMENTATION_RESULT_DOC_PATH,
    P7_HOLD004_PHASE16_IMPLEMENTATION_RESULT_DOC_REF,
    assert_p7_release_decision_handoff_contract,
    build_p7_release_decision_handoff,
)
from emlis_ai_p7_validation_matrix import assert_p7_validation_regression_matrix_contract, build_p7_validation_regression_matrix


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


def _hold004_materials() -> dict[str, dict[str, object]]:
    observations = [
        build_p7_hold004_phase16_composer_observation(
            path_id="complete_composer_direct_daily_unpleasant_A",
            test_ref=(
                "tests/test_emlis_ai_complete_composer_two_stage_surface_connection.py::"
                "test_phase16_6_complete_composer_direct_output_reaches_labelled_two_stage_text"
            ),
            fixture_family=DAILY_A_CASE_ID,
            composer_meta=_phase16_boundary_meta(),
            observed_status="unavailable",
            expected_status_kind="generated_candidate_before_display_gate",
            candidate_generated_before_display_gate=False,
        ),
        build_p7_hold004_phase16_composer_observation(
            path_id="conversation_composer_daily_unpleasant_A",
            test_ref=(
                "tests/test_emlis_ai_complete_composer_two_stage_surface_connection.py::"
                "test_phase16_6_conversation_composer_path_reaches_labelled_two_stage_text"
            ),
            fixture_family=DAILY_A_CASE_ID,
            composer_meta=_phase16_boundary_meta(),
            observed_status="unavailable",
            expected_status_kind="generated_candidate_before_display_gate",
            candidate_generated_before_display_gate=False,
        ),
        build_p7_hold004_phase16_composer_observation(
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
        ),
    ]
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


def test_r9_implementation_result_document_exists_and_keeps_non_release_boundary() -> None:
    doc_path = Path(__file__).resolve().parents[1] / P7_HOLD004_PHASE16_IMPLEMENTATION_RESULT_DOC_PATH
    text = doc_path.read_text(encoding="utf-8")

    assert doc_path.exists()
    assert "R9 実装結果document / handoff更新" in text
    assert "P7-HOLD-004" in text
    assert "full_backend_suite_green_confirmed: false" in text
    assert "p7_complete: false" in text
    assert "p8_start_allowed: false" in text
    assert "release_allowed: false" in text
    assert "Gate緩和: なし" in text
    assert "fixed commentText追加: なし" in text
    assert "case専用branch追加: なし" in text


def test_r9_release_handoff_and_validation_matrix_reference_result_doc_without_closing_hold() -> None:
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

    assert handoff["hold004_phase16_implementation_result_doc_path"] == P7_HOLD004_PHASE16_IMPLEMENTATION_RESULT_DOC_PATH
    assert handoff["hold004_phase16_implementation_result_doc_ref"] == P7_HOLD004_PHASE16_IMPLEMENTATION_RESULT_DOC_REF
    assert P7_HOLD004_PHASE16_IMPLEMENTATION_RESULT_DOC_PATH in handoff["implementation_result_doc_refs"]
    assert handoff["manual_hold_status"]["hold004_phase16_implementation_result_documented"] is True
    assert handoff["manual_hold_status"]["hold004_phase16_implementation_result_doc_ref"] == P7_HOLD004_PHASE16_IMPLEMENTATION_RESULT_DOC_REF
    assert "P7-HOLD-004" in handoff["unresolved_hold_refs"]
    assert handoff["full_backend_suite_green_confirmed"] is False
    assert handoff["release_allowed"] is False

    assert validation["hold004_phase16_implementation_result_doc_path"] == P7_HOLD004_PHASE16_IMPLEMENTATION_RESULT_DOC_PATH
    assert validation["hold004_phase16_implementation_result_doc_ref"] == P7_HOLD004_PHASE16_IMPLEMENTATION_RESULT_DOC_REF
    assert validation["summary"]["hold004_phase16_implementation_result_documented"] is True
    assert validation["summary"]["hold004_phase16_implementation_result_doc_ref"] == P7_HOLD004_PHASE16_IMPLEMENTATION_RESULT_DOC_REF
    assert validation["summary"]["full_backend_suite_green_confirmed"] is False
    assert validation["summary"]["p8_start_allowed"] is False
    assert validation["summary"]["release_allowed"] is False


def test_r9_contracts_reject_missing_doc_ref_or_release_promotion() -> None:
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

    missing_doc_ref = copy.deepcopy(handoff)
    missing_doc_ref["implementation_result_doc_refs"] = []
    with pytest.raises(ValueError):
        assert_p7_release_decision_handoff_contract(missing_doc_ref)

    missing_validation_ref = copy.deepcopy(validation)
    missing_validation_ref["summary"]["hold004_phase16_implementation_result_documented"] = False
    with pytest.raises(ValueError):
        assert_p7_validation_regression_matrix_contract(missing_validation_ref)

    promoted = copy.deepcopy(handoff)
    promoted["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_release_decision_handoff_contract(promoted)

    assert P7_HOLD004_PHASE16_PUBLIC_ADJACENT_RED_REGISTRATION_SCHEMA_VERSION
