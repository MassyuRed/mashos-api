# -*- coding: utf-8 -*-
"""Tests for R54-AHR22/AHR23 final validation and R52 handoff envelope."""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r54_actual_human_review_execution_bodyfree_intake_20260627 as ahr
from test_r54_actual_human_review_execution_bodyfree_intake_ahr18_ahr19_20260627 import (
    assert_bodyfree_no_touch_no_final_promotion,
    build_valid_ahr18_summary,
)
from test_r54_actual_human_review_execution_bodyfree_intake_ahr20_ahr21_20260627 import (
    build_valid_ahr14_and_ahr15,
    build_valid_ahr19_decision,
    build_valid_ahr20_handoff,
)


def build_valid_ahr21_handoff(*, p8_candidate_index: int | None = None) -> dict[str, object]:
    p6_handoff = build_valid_ahr20_handoff(p8_candidate_index=p8_candidate_index)
    question, guard = build_valid_ahr14_and_ahr15(p8_candidate_index=p8_candidate_index)
    p8_handoff = ahr.build_p7_r54_ahr21_p8_material_candidate_only_handoff(
        p6_candidate_only_handoff=p6_handoff,
        question_need_observation_normalization=question,
        rating_question_consistency_guard=guard,
        review_session_id=p6_handoff["review_session_id"],
    )
    assert ahr.assert_p7_r54_ahr21_p8_material_candidate_only_handoff_contract(p8_handoff) is True
    assert p8_handoff["p8_material_candidate_only_handoff_status_ref"] == ahr.P7_R54_AHR21_READY_STATUS_REF
    return p8_handoff


@lru_cache(maxsize=None)
def _cached_valid_ahr22_validation(p8_candidate_index: int | None = None) -> tuple[tuple[str, object], ...]:
    summary = build_valid_ahr18_summary(p8_candidate_index=p8_candidate_index)
    decision = build_valid_ahr19_decision(p8_candidate_index=p8_candidate_index)
    p6_handoff = build_valid_ahr20_handoff(p8_candidate_index=p8_candidate_index)
    p8_handoff = build_valid_ahr21_handoff(p8_candidate_index=p8_candidate_index)
    validation = ahr.build_p7_r54_ahr22_final_no_body_leak_no_question_text_no_touch_validation(
        bodyfree_post_review_summary=summary,
        p5_decision_candidate_separation=decision,
        p6_candidate_only_handoff=p6_handoff,
        p8_material_candidate_only_handoff=p8_handoff,
        review_session_id=summary["review_session_id"],
    )
    assert ahr.assert_p7_r54_ahr22_final_no_body_leak_no_question_text_no_touch_validation_contract(validation) is True
    assert validation["final_validation_status_ref"] == ahr.P7_R54_AHR22_READY_STATUS_REF
    return tuple(sorted(validation.items()))


def build_valid_ahr22_validation(*, p8_candidate_index: int | None = None) -> dict[str, object]:
    return dict(_cached_valid_ahr22_validation(p8_candidate_index))


@lru_cache(maxsize=None)
def _cached_valid_ahr23_handoff(p8_candidate_index: int | None = None) -> tuple[tuple[str, object], ...]:
    validation = build_valid_ahr22_validation(p8_candidate_index=p8_candidate_index)
    handoff = ahr.build_p7_r54_ahr23_r52_reintake_handoff_envelope(
        final_validation=validation,
        review_session_id=validation["review_session_id"],
    )
    assert ahr.assert_p7_r54_ahr23_r52_reintake_handoff_envelope_contract(handoff) is True
    assert handoff["r52_reintake_handoff_status_ref"] == ahr.P7_R54_AHR23_READY_STATUS_REF
    return tuple(sorted(handoff.items()))


def build_valid_ahr23_handoff(*, p8_candidate_index: int | None = None) -> dict[str, object]:
    return dict(_cached_valid_ahr23_handoff(p8_candidate_index))


def test_r54_ahr22_default_blocks_without_ready_sources() -> None:
    material = ahr.build_p7_r54_ahr22_final_no_body_leak_no_question_text_no_touch_validation()

    assert ahr.assert_p7_r54_ahr22_final_no_body_leak_no_question_text_no_touch_validation_contract(material) is True
    assert material["final_validation_status_ref"] == ahr.P7_R54_AHR22_BLOCKED_STATUS_REF
    assert material["execution_blocker_ids"]
    assert material["r52_reintake_handoff_envelope_allowed_next"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR22_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert_bodyfree_no_touch_no_final_promotion(material)


def test_r54_ahr22_passes_final_bodyfree_validation_without_r52_execution() -> None:
    material = build_valid_ahr22_validation(p8_candidate_index=3)

    assert material["schema_version"] == ahr.P7_R54_AHR22_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION
    assert material["operation_step_ref"] == ahr.P7_R54_AHR22_STEP_REF
    assert material["final_validation_reason_refs"] == [ahr.P7_R54_AHR22_READY_REASON_REF]
    assert material["reviewed_case_count"] == 24
    assert material["sanitized_review_result_row_count"] == 24
    assert material["rating_row_count"] == 24
    assert material["question_observation_row_count"] == 24
    assert material["p8_material_candidate_row_count"] == 1
    assert material["forbidden_exact_key_finding_count"] == 0
    assert material["bodyfree_true_flag_finding_count"] == 0
    assert material["body_path_hash_leak_finding_count"] == 0
    assert material["question_text_leak_finding_count"] == 0
    assert material["no_touch_violation_finding_count"] == 0
    assert material["no_body_leak_validation_passed"] is True
    assert material["no_question_text_validation_passed"] is True
    assert material["no_touch_validation_passed"] is True
    assert material["r52_reintake_handoff_envelope_allowed_next"] is True
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR23_STEP_REF
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR22_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ahr.P7_R54_AHR22_NOT_YET_IMPLEMENTED_STEPS
    assert_bodyfree_no_touch_no_final_promotion(material)


def test_r54_ahr22_blocks_source_with_forbidden_question_text_key() -> None:
    summary = build_valid_ahr18_summary()
    decision = build_valid_ahr19_decision()
    p6_handoff = build_valid_ahr20_handoff()
    p8_handoff = build_valid_ahr21_handoff()
    mutated = deepcopy(p8_handoff)
    mutated["p8_material_candidate_rows"] = [
        {
            "p8_material_candidate_row_ref": "mutated_row_with_question_key",
            "question_text": "must_not_be_exported",
        }
    ]

    material = ahr.build_p7_r54_ahr22_final_no_body_leak_no_question_text_no_touch_validation(
        bodyfree_post_review_summary=summary,
        p5_decision_candidate_separation=decision,
        p6_candidate_only_handoff=p6_handoff,
        p8_material_candidate_only_handoff=mutated,
    )

    assert ahr.assert_p7_r54_ahr22_final_no_body_leak_no_question_text_no_touch_validation_contract(material) is True
    assert material["final_validation_status_ref"] == ahr.P7_R54_AHR22_BLOCKED_STATUS_REF
    assert "forbidden_exact_key_found_in_bodyfree_sources" in material["execution_blocker_ids"]
    assert material["question_text_leak_finding_count"] > 0
    assert material["r52_reintake_handoff_envelope_allowed_next"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR22_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert_bodyfree_no_touch_no_final_promotion(material)


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("p5_human_blind_qa_confirmed_final", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p6_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("actual_r52_reintake_execution_confirmed", True),
        ("p8_implementation_spec_finalized_here", True),
    ],
)
def test_r54_ahr22_rejects_final_or_start_or_r52_execution_mutations(field: str, bad_value: object) -> None:
    material = build_valid_ahr22_validation()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr22_final_no_body_leak_no_question_text_no_touch_validation_contract(mutated)


def test_r54_ahr23_default_blocks_without_final_validation() -> None:
    material = ahr.build_p7_r54_ahr23_r52_reintake_handoff_envelope()

    assert ahr.assert_p7_r54_ahr23_r52_reintake_handoff_envelope_contract(material) is True
    assert material["r52_reintake_handoff_status_ref"] == ahr.P7_R54_AHR23_BLOCKED_STATUS_REF
    assert material["r52_reintake_handoff_envelope_status_ref"] == ahr.P7_R54_AHR23_BLOCKED_STATUS_REF
    assert material["execution_blocker_ids"]
    assert material["r52_reintake_handoff_ready"] is False
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR23_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert_bodyfree_no_touch_no_final_promotion(material)


def test_r54_ahr23_materializes_r52_handoff_envelope_without_executing_r52() -> None:
    material = build_valid_ahr23_handoff(p8_candidate_index=3)

    assert material["schema_version"] == ahr.P7_R54_AHR23_R52_REINTAKE_HANDOFF_ENVELOPE_SCHEMA_VERSION
    assert material["operation_step_ref"] == ahr.P7_R54_AHR23_STEP_REF
    assert material["r52_reintake_handoff_reason_refs"] == [ahr.P7_R54_AHR23_READY_REASON_REF]
    assert material["r52_reintake_handoff_envelope_ref"] == ahr.P7_R54_AHR23_R52_HANDOFF_ENVELOPE_REF
    assert material["r52_reintake_handoff_ready"] is True
    assert material["r52_reintake_handoff_envelope_bodyfree_only"] is True
    assert material["r52_reintake_handoff_envelope_materialized_here"] is True
    assert material["r52_reintake_execution_not_run_here"] is True
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["reviewed_case_count"] == 24
    assert material["sanitized_review_result_row_count"] == 24
    assert material["rating_row_count"] == 24
    assert material["question_observation_row_count"] == 24
    assert material["p8_material_candidate_row_count"] == 1
    assert material["actual_human_review_executed_by_person"] is True
    assert material["actual_review_evidence_complete"] is True
    assert material["no_body_leak_validation_passed"] is True
    assert material["no_question_text_validation_passed"] is True
    assert material["no_touch_validation_passed"] is True
    assert material["p5_human_blind_qa_confirmed_candidate"] is True
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["p6_limited_human_readfeel_candidate"] is True
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR24_STEP_REF
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR23_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ahr.P7_R54_AHR23_NOT_YET_IMPLEMENTED_STEPS
    assert all(row["satisfied"] is True for row in material["r52_reintake_handoff_ready_conditions"])
    assert_bodyfree_no_touch_no_final_promotion(material)


def test_r54_ahr23_blocks_when_final_validation_is_not_passed() -> None:
    validation = build_valid_ahr22_validation()
    mutated = deepcopy(validation)
    mutated["final_validation_status_ref"] = ahr.P7_R54_AHR22_BLOCKED_STATUS_REF
    mutated["final_no_body_leak_no_question_text_no_touch_validation_status_ref"] = ahr.P7_R54_AHR22_BLOCKED_STATUS_REF
    mutated["r52_reintake_handoff_envelope_allowed_next"] = False
    mutated["execution_blocker_ids"] = ["injected_final_validation_blocker"]
    mutated["open_execution_blocker_ids"] = ["injected_final_validation_blocker"]
    mutated["next_required_step"] = ahr.P7_R54_AHR22_BLOCKED_NEXT_REQUIRED_STEP_REF
    material = ahr.build_p7_r54_ahr23_r52_reintake_handoff_envelope(final_validation=mutated)

    assert ahr.assert_p7_r54_ahr23_r52_reintake_handoff_envelope_contract(material) is True
    assert material["r52_reintake_handoff_status_ref"] == ahr.P7_R54_AHR23_BLOCKED_STATUS_REF
    assert material["execution_blocker_ids"]
    assert material["r52_reintake_handoff_ready"] is False
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR23_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert_bodyfree_no_touch_no_final_promotion(material)


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("p5_human_blind_qa_confirmed_final", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p6_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("actual_r52_reintake_execution_confirmed", True),
        ("p8_implementation_spec_finalized_here", True),
    ],
)
def test_r54_ahr23_rejects_final_or_start_or_r52_execution_mutations(field: str, bad_value: object) -> None:
    material = build_valid_ahr23_handoff()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr23_r52_reintake_handoff_envelope_contract(mutated)


def test_r54_ahr22_ahr23_design_aliases_point_to_canonical_helpers() -> None:
    validation = ahr.build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr22_final_no_body_leak_no_question_text_no_touch_validation()
    handoff = ahr.build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr23_r52_reintake_handoff_envelope(
        final_validation=validation,
    )

    assert validation["final_validation_status_ref"] == ahr.P7_R54_AHR22_BLOCKED_STATUS_REF
    assert handoff["r52_reintake_handoff_status_ref"] == ahr.P7_R54_AHR23_BLOCKED_STATUS_REF
    assert ahr.assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr22_final_no_body_leak_no_question_text_no_touch_validation_contract(validation) is True
    assert ahr.assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr23_r52_reintake_handoff_envelope_contract(handoff) is True
