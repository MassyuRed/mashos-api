# -*- coding: utf-8 -*-
"""Tests for R54-AHR20/AHR21 candidate-only handoff boundaries."""

from __future__ import annotations

from copy import deepcopy

import pytest

import emlis_ai_p7_r54_actual_human_review_execution_bodyfree_intake_20260627 as ahr
from test_r54_actual_human_review_execution_bodyfree_intake_ahr18_ahr19_20260627 import (
    assert_bodyfree_no_touch_no_final_promotion,
    build_valid_ahr15_guard,
    build_valid_ahr18_summary,
)


def build_valid_ahr19_decision(*, p8_candidate_index: int | None = None) -> dict[str, object]:
    summary = build_valid_ahr18_summary(p8_candidate_index=p8_candidate_index)
    decision = ahr.build_p7_r54_ahr19_p5_decision_candidate_separation(
        bodyfree_post_review_summary=summary,
        review_session_id=summary["review_session_id"],
    )
    assert ahr.assert_p7_r54_ahr19_p5_decision_candidate_separation_contract(decision) is True
    assert decision["decision_candidate_ref"] == ahr.P7_R54_AHR19_P5_CONFIRMED_CANDIDATE_REF
    return decision


def build_valid_ahr20_handoff(*, p8_candidate_index: int | None = None) -> dict[str, object]:
    decision = build_valid_ahr19_decision(p8_candidate_index=p8_candidate_index)
    handoff = ahr.build_p7_r54_ahr20_p6_candidate_only_handoff(
        p5_decision_candidate_separation=decision,
        review_session_id=decision["review_session_id"],
    )
    assert ahr.assert_p7_r54_ahr20_p6_candidate_only_handoff_contract(handoff) is True
    assert handoff["p6_candidate_only_handoff_status_ref"] == ahr.P7_R54_AHR20_READY_STATUS_REF
    return handoff


def build_valid_ahr14_and_ahr15(*, p8_candidate_index: int | None = None) -> tuple[dict[str, object], dict[str, object]]:
    _rating, _blockers, question, guard = build_valid_ahr15_guard(p8_candidate_index=p8_candidate_index)
    assert ahr.assert_p7_r54_ahr14_question_need_observation_normalization_contract(question) is True
    assert ahr.assert_p7_r54_ahr15_rating_question_consistency_guard_contract(guard) is True
    return question, guard


def test_r54_ahr20_default_blocks_without_valid_ahr19_p5_candidate() -> None:
    material = ahr.build_p7_r54_ahr20_p6_candidate_only_handoff()

    assert ahr.assert_p7_r54_ahr20_p6_candidate_only_handoff_contract(material) is True
    assert material["p6_candidate_only_handoff_status_ref"] == ahr.P7_R54_AHR20_BLOCKED_STATUS_REF
    assert material["execution_blocker_ids"]
    assert material["p6_limited_human_readfeel_candidate"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR20_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert_bodyfree_no_touch_no_final_promotion(material)


def test_r54_ahr20_hands_off_p6_candidate_only_without_start_permission() -> None:
    material = build_valid_ahr20_handoff()

    assert material["schema_version"] == ahr.P7_R54_AHR20_P6_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION
    assert material["operation_step_ref"] == ahr.P7_R54_AHR20_STEP_REF
    assert material["p6_candidate_only_handoff_status_ref"] == ahr.P7_R54_AHR20_READY_STATUS_REF
    assert material["p6_candidate_only_handoff_reason_refs"] == [ahr.P7_R54_AHR20_READY_REASON_REF]
    assert material["decision_candidate_ref"] == ahr.P7_R54_AHR19_P5_CONFIRMED_CANDIDATE_REF
    assert material["p5_human_blind_qa_confirmed_candidate"] is True
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["p6_limited_human_readfeel_candidate"] is True
    assert material["p6_limited_human_readfeel_candidate_only"] is True
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["p8_material_candidate_only_handoff_allowed_next"] is True
    assert material["next_required_step"] == ahr.P7_R54_AHR21_STEP_REF
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR20_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ahr.P7_R54_AHR20_NOT_YET_IMPLEMENTED_STEPS
    assert_bodyfree_no_touch_no_final_promotion(material)


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("p5_human_blind_qa_confirmed_final", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p6_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("actual_human_review_run_here", True),
    ],
)
def test_r54_ahr20_rejects_final_or_start_promotion_mutations(field: str, bad_value: object) -> None:
    material = build_valid_ahr20_handoff()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr20_p6_candidate_only_handoff_contract(mutated)


def test_r54_ahr21_default_blocks_without_ready_handoff_or_question_rows() -> None:
    material = ahr.build_p7_r54_ahr21_p8_material_candidate_only_handoff()

    assert ahr.assert_p7_r54_ahr21_p8_material_candidate_only_handoff_contract(material) is True
    assert material["p8_material_candidate_only_handoff_status_ref"] == ahr.P7_R54_AHR21_BLOCKED_STATUS_REF
    assert material["execution_blocker_ids"]
    assert material["p8_question_design_material_candidate"] is False
    assert material["p8_material_candidate_row_count"] == 0
    assert material["p8_material_candidate_rows"] == []
    assert material["p8_start_allowed"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR21_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert_bodyfree_no_touch_no_final_promotion(material)


def test_r54_ahr21_hands_off_zero_p8_candidates_without_starting_p8() -> None:
    p6 = build_valid_ahr20_handoff()
    question, guard = build_valid_ahr14_and_ahr15()
    material = ahr.build_p7_r54_ahr21_p8_material_candidate_only_handoff(
        p6_candidate_only_handoff=p6,
        question_need_observation_normalization=question,
        rating_question_consistency_guard=guard,
        review_session_id=p6["review_session_id"],
    )

    assert ahr.assert_p7_r54_ahr21_p8_material_candidate_only_handoff_contract(material) is True
    assert material["schema_version"] == ahr.P7_R54_AHR21_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION
    assert material["operation_step_ref"] == ahr.P7_R54_AHR21_STEP_REF
    assert material["p8_material_candidate_only_handoff_status_ref"] == ahr.P7_R54_AHR21_READY_STATUS_REF
    assert material["p8_material_candidate_row_count"] == 0
    assert material["p8_question_design_material_candidate"] is False
    assert material["p8_start_allowed"] is False
    assert material["p8_implementation_spec_finalized_here"] is False
    assert material["p8_question_text_created_here"] is False
    assert material["p8_trigger_logic_created_here"] is False
    assert material["question_text_materialized_here"] is False
    assert material["draft_question_text_materialized_here"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR22_STEP_REF
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR21_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ahr.P7_R54_AHR21_NOT_YET_IMPLEMENTED_STEPS
    assert_bodyfree_no_touch_no_final_promotion(material)


def test_r54_ahr21_filters_actual_review_p8_material_candidate_rows_bodyfree_only() -> None:
    p6 = build_valid_ahr20_handoff(p8_candidate_index=3)
    question, guard = build_valid_ahr14_and_ahr15(p8_candidate_index=3)
    material = ahr.build_p7_r54_ahr21_p8_material_candidate_only_handoff(
        p6_candidate_only_handoff=p6,
        question_need_observation_normalization=question,
        rating_question_consistency_guard=guard,
        review_session_id=p6["review_session_id"],
    )

    assert ahr.assert_p7_r54_ahr21_p8_material_candidate_only_handoff_contract(material) is True
    assert material["p8_material_candidate_only_handoff_status_ref"] == ahr.P7_R54_AHR21_READY_STATUS_REF
    assert material["p8_question_design_material_candidate"] is True
    assert material["p8_material_candidate_row_count"] == 1
    assert material["plus_single_question_candidate_row_count"] == 1
    assert material["premium_deep_dive_candidate_row_count"] == 0
    row = material["p8_material_candidate_rows"][0]
    assert row["schema_version"] == ahr.P7_R54_AHR21_P8_MATERIAL_CANDIDATE_ROW_SCHEMA_VERSION
    assert row["p8_design_material_candidate"] is True
    assert row["question_need_primary_class_ref"] == "plus_single_question_candidate_later"
    assert row["one_question_fit_ref"] == "fits_one_question"
    assert row["p5_repair_required"] is False
    assert row["p4_current_surface_repair_required"] is False
    assert row["execution_blocker_present"] is False
    assert row["readfeel_blocker_present"] is False
    assert row["question_text_included"] is False
    assert row["draft_question_text_included"] is False
    assert row["p8_implementation_spec_finalized_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["question_text_materialized_here"] is False
    assert material["draft_question_text_materialized_here"] is False
    assert_bodyfree_no_touch_no_final_promotion(material)


def test_r54_ahr21_blocks_candidate_flag_that_contains_p5_repair() -> None:
    p6 = build_valid_ahr20_handoff(p8_candidate_index=3)
    question, guard = build_valid_ahr14_and_ahr15(p8_candidate_index=3)
    mutated_question = deepcopy(question)
    mutated_question["question_need_observation_rows"][2]["p5_repair_required"] = True

    material = ahr.build_p7_r54_ahr21_p8_material_candidate_only_handoff(
        p6_candidate_only_handoff=p6,
        question_need_observation_normalization=mutated_question,
        rating_question_consistency_guard=guard,
    )

    assert ahr.assert_p7_r54_ahr21_p8_material_candidate_only_handoff_contract(material) is True
    assert material["p8_material_candidate_only_handoff_status_ref"] == ahr.P7_R54_AHR21_BLOCKED_STATUS_REF
    assert material["execution_blocker_ids"]
    assert material["p8_question_design_material_candidate"] is False
    assert material["p8_material_candidate_rows"] == []
    assert material["p8_start_allowed"] is False
    assert_bodyfree_no_touch_no_final_promotion(material)


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("p8_start_allowed", True),
        ("p8_implementation_spec_finalized_here", True),
        ("p8_question_text_created_here", True),
        ("p8_trigger_logic_created_here", True),
        ("question_text_materialized_here", True),
        ("draft_question_text_materialized_here", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_r54_ahr21_rejects_p8_or_p6_start_promotion_mutations(field: str, bad_value: object) -> None:
    p6 = build_valid_ahr20_handoff(p8_candidate_index=3)
    question, guard = build_valid_ahr14_and_ahr15(p8_candidate_index=3)
    material = ahr.build_p7_r54_ahr21_p8_material_candidate_only_handoff(
        p6_candidate_only_handoff=p6,
        question_need_observation_normalization=question,
        rating_question_consistency_guard=guard,
    )
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr21_p8_material_candidate_only_handoff_contract(mutated)


def test_r54_ahr20_ahr21_design_aliases_point_to_canonical_helpers() -> None:
    p6 = ahr.build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr20_p6_candidate_only_handoff()
    p8 = ahr.build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr21_p8_material_candidate_only_handoff(
        p6_candidate_only_handoff=p6,
    )

    assert p6["p6_candidate_only_handoff_status_ref"] == ahr.P7_R54_AHR20_BLOCKED_STATUS_REF
    assert p8["p8_material_candidate_only_handoff_status_ref"] == ahr.P7_R54_AHR21_BLOCKED_STATUS_REF
    assert ahr.assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr20_p6_candidate_only_handoff_contract(p6) is True
    assert ahr.assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr21_p8_material_candidate_only_handoff_contract(p8) is True
