# -*- coding: utf-8 -*-
"""R54-AHR-CS16/CS17 current snapshot actual review re-entry contract tests."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

import emlis_ai_p7_r54_ahr_current_snapshot_actual_review_reentry_20260628 as cs
from test_r54_ahr_current_snapshot_actual_review_reentry_cs14_cs15_20260628 import (
    _assert_bodyfree_no_touch_allowing,
    _build_ready_cs15,
)


def _build_ready_cs16(**kwargs: Any) -> dict[str, Any]:
    material = cs.build_p7_r54_ahr_cs16_p5_decision_candidate_separation(
        bodyfree_post_review_summary=_build_ready_cs15(),
        **kwargs,
    )
    assert cs.assert_p7_r54_ahr_cs16_p5_decision_candidate_separation_contract(material) is True
    return material


def _build_ready_cs17(**kwargs: Any) -> dict[str, Any]:
    material = cs.build_p7_r54_ahr_cs17_p6_p8_candidate_only_r52_handoff_envelope(
        p5_decision_candidate_separation=_build_ready_cs16(),
        **kwargs,
    )
    assert cs.assert_p7_r54_ahr_cs17_p6_p8_candidate_only_r52_handoff_envelope_contract(material) is True
    return material


def test_cs00_to_cs15_ready_path_is_present_before_cs16_cs17() -> None:
    cs15 = _build_ready_cs15()
    assert cs15["post_review_summary_status_ref"] == cs.P7_R54_AHR_CS15_COMPLETE_STATUS_REF
    assert cs15["actual_review_evidence_complete"] is True
    assert cs15["reviewed_case_count"] == cs.P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
    assert cs15["rating_row_count"] == cs.P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
    assert cs15["question_observation_row_count"] == cs.P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
    assert cs15["p5_decision_candidate_separation_allowed_next"] is True
    assert cs15["p5_human_blind_qa_confirmed_final"] is False
    assert cs15["p6_limited_human_readfeel_start_allowed"] is False
    assert cs15["p8_start_allowed"] is False
    assert cs15["p7_complete"] is False
    assert cs15["release_allowed"] is False
    assert cs15["next_required_step"] == cs.P7_R54_AHR_CS16_STEP_REF


def test_cs16_default_is_fail_closed_without_complete_cs15() -> None:
    material = cs.build_p7_r54_ahr_cs16_p5_decision_candidate_separation()
    assert material["p5_decision_candidate_status_ref"] == cs.P7_R54_AHR_CS16_DECISION_R54_OPERATION_BLOCKED_DISPOSAL_REF
    assert "cs14_disposal_receipt_not_verified_for_post_review_summary" in material["execution_blocker_ids"]
    assert material["cs15_ready_for_p5_decision_candidate_separation"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["p5_confirmed_candidate"] is False
    assert material["p6_p8_candidate_only_r52_handoff_allowed_next"] is False
    assert material["next_required_step"] == cs.P7_R54_AHR_CS15_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch_allowing(material, ())
    assert cs.assert_p7_r54_ahr_cs16_p5_decision_candidate_separation_contract(material) is True


def test_cs16_ready_separates_p5_confirmed_candidate_without_finalizing() -> None:
    material = _build_ready_cs16()
    assert set(material) == set(cs.P7_R54_AHR_CS16_P5_DECISION_CANDIDATE_SEPARATION_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cs.P7_R54_AHR_CS16_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION
    assert material["policy_section"] == cs.P7_R54_AHR_CS16_STEP_REF
    assert material["operation_step_ref"] == cs.P7_R54_AHR_CS16_STEP_REF
    assert material["cs15_next_required_step"] == cs.P7_R54_AHR_CS16_STEP_REF
    assert material["current_basis_ref"] == cs.P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF
    assert material["historical_basis_ref"] == cs.P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF
    assert material["p5_decision_candidate_status_ref"] == cs.P7_R54_AHR_CS16_DECISION_P5_CONFIRMED_CANDIDATE_REF
    assert material["p5_decision_candidate_reason_refs"] == [cs.P7_R54_AHR_CS16_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["open_execution_blocker_ids"] == []
    assert material["cs15_ready_for_p5_decision_candidate_separation"] is True
    assert material["reviewed_case_count"] == 24
    assert material["rating_row_count"] == 24
    assert material["question_observation_row_count"] == 24
    assert material["actual_review_evidence_complete"] is True
    assert material["actual_human_review_operation_run"] is True
    assert material["actual_human_review_executed_by_person"] is True
    assert material["actual_human_review_run_here"] is False
    assert material["actual_human_review_complete"] is False
    assert material["p5_decision_candidate_separated_here"] is True
    assert material["p5_confirmed_candidate"] is True
    assert material["p5_confirmed_candidate_not_finalized_here"] is True
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["p5_confirmed_final"] is False
    assert material["p5_final_allowed"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["r52_reintake_handoff_ready_here"] is False
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert material["p6_p8_candidate_only_r52_handoff_allowed_next"] is True
    assert tuple(material["implemented_steps"]) == cs.P7_R54_AHR_CS16_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cs.P7_R54_AHR_CS16_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cs.P7_R54_AHR_CS17_STEP_REF
    _assert_bodyfree_no_touch_allowing(material, cs.P7_R54_AHR_CS16_ALLOWED_TRUE_FALSE_FLAG_REFS)


@pytest.mark.parametrize(
    "flag_name, expected_decision, expected_next",
    (
        (
            "p5_repair_return_required",
            cs.P7_R54_AHR_CS16_DECISION_P5_REPAIR_RETURN_REQUIRED_REF,
            cs.P7_R54_AHR_CS16_P5_REPAIR_NEXT_REQUIRED_STEP_REF,
        ),
        (
            "p4_current_only_repair_required",
            cs.P7_R54_AHR_CS16_DECISION_P4_CURRENT_ONLY_REPAIR_REQUIRED_REF,
            cs.P7_R54_AHR_CS16_P4_REPAIR_NEXT_REQUIRED_STEP_REF,
        ),
        (
            "r54_operation_inconclusive",
            cs.P7_R54_AHR_CS16_DECISION_R54_OPERATION_INCONCLUSIVE_REF,
            cs.P7_R54_AHR_CS16_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF,
        ),
        (
            "operation_blocked_preflight_or_execution",
            cs.P7_R54_AHR_CS16_DECISION_R54_OPERATION_BLOCKED_PREFLIGHT_OR_EXECUTION_REF,
            cs.P7_R54_AHR_CS16_BLOCKED_NEXT_REQUIRED_STEP_REF,
        ),
        (
            "operation_blocked_disposal",
            cs.P7_R54_AHR_CS16_DECISION_R54_OPERATION_BLOCKED_DISPOSAL_REF,
            cs.P7_R54_AHR_CS16_BLOCKED_NEXT_REQUIRED_STEP_REF,
        ),
        (
            "operation_blocked_body_leak_or_question_text",
            cs.P7_R54_AHR_CS16_DECISION_R54_OPERATION_BLOCKED_BODY_LEAK_OR_QUESTION_TEXT_REF,
            cs.P7_R54_AHR_CS16_BLOCKED_NEXT_REQUIRED_STEP_REF,
        ),
        (
            "operation_blocked_no_touch",
            cs.P7_R54_AHR_CS16_DECISION_R54_OPERATION_BLOCKED_NO_TOUCH_REF,
            cs.P7_R54_AHR_CS16_BLOCKED_NEXT_REQUIRED_STEP_REF,
        ),
    ),
)
def test_cs16_separates_repair_inconclusive_and_blocked_outcomes(
    flag_name: str,
    expected_decision: str,
    expected_next: str,
) -> None:
    material = _build_ready_cs16(**{flag_name: True})
    assert material["p5_decision_candidate_status_ref"] == expected_decision
    assert material["p5_confirmed_candidate"] is False
    assert material["p6_p8_candidate_only_r52_handoff_allowed_next"] is False
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["p8_start_allowed"] is False
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["next_required_step"] == expected_next
    assert cs.assert_p7_r54_ahr_cs16_p5_decision_candidate_separation_contract(material) is True


def test_cs16_rejects_mutated_final_or_start_flags() -> None:
    for flag in (
        "p5_human_blind_qa_confirmed_final",
        "p5_confirmed_final",
        "p5_final_allowed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "actual_r52_reintake_execution_confirmed",
        "p7_complete",
        "release_allowed",
    ):
        material = deepcopy(_build_ready_cs16())
        material[flag] = True
        with pytest.raises(ValueError):
            cs.assert_p7_r54_ahr_cs16_p5_decision_candidate_separation_contract(material)


def test_cs16_aliases_match_primary_builder_and_contract() -> None:
    primary = _build_ready_cs16()
    alias = cs.build_p7_r54_ahr_current_snapshot_actual_review_reentry_p5_decision_candidate_separation_bodyfree(
        bodyfree_post_review_summary=_build_ready_cs15()
    )
    assert alias == primary
    assert cs.assert_p7_r54_ahr_current_snapshot_actual_review_reentry_p5_decision_candidate_separation_bodyfree_contract(alias) is True
    assert cs.assert_p7_r54_ahr_cs16_p5_decision_candidate_separation_bodyfree_contract(alias) is True


def test_cs17_default_is_fail_closed_without_ready_cs16() -> None:
    material = cs.build_p7_r54_ahr_cs17_p6_p8_candidate_only_r52_handoff_envelope()
    assert material["candidate_handoff_status_ref"] == cs.P7_R54_AHR_CS17_BLOCKED_STATUS_REF
    assert "cs16_p5_confirmed_candidate_not_ready_for_candidate_only_handoff" in material["execution_blocker_ids"]
    assert material["actual_review_evidence_complete"] is False
    assert material["p5_confirmed_candidate"] is False
    assert material["p6_candidate_only_handoff_built"] is False
    assert material["p6_limited_human_readfeel_start_allowed_candidate"] is False
    assert material["p8_question_design_material_candidate"] is False
    assert material["p8_material_candidate_refs"] == []
    assert material["p8_material_candidate_ref_count"] == 0
    assert material["r52_reintake_handoff_envelope_built"] is False
    assert material["r52_reintake_handoff_ready"] is False
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["next_required_step"] == cs.P7_R54_AHR_CS17_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch_allowing(material, ())
    assert cs.assert_p7_r54_ahr_cs17_p6_p8_candidate_only_r52_handoff_envelope_contract(material) is True


def test_cs17_ready_builds_candidate_only_handoff_without_start_or_execution() -> None:
    material = _build_ready_cs17(
        p8_material_candidate_refs=(
            "question_may_reduce_overread_risk",
            "plus_single_question_candidate_later",
            "premium_deep_dive_candidate_later",
        )
    )
    assert set(material) == set(cs.P7_R54_AHR_CS17_P6_P8_CANDIDATE_ONLY_R52_HANDOFF_ENVELOPE_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cs.P7_R54_AHR_CS17_P6_P8_CANDIDATE_ONLY_R52_HANDOFF_ENVELOPE_SCHEMA_VERSION
    assert material["policy_section"] == cs.P7_R54_AHR_CS17_STEP_REF
    assert material["operation_step_ref"] == cs.P7_R54_AHR_CS17_STEP_REF
    assert material["cs16_next_required_step"] == cs.P7_R54_AHR_CS17_STEP_REF
    assert material["candidate_handoff_status_ref"] == cs.P7_R54_AHR_CS17_READY_STATUS_REF
    assert material["candidate_handoff_reason_refs"] == [cs.P7_R54_AHR_CS17_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["open_execution_blocker_ids"] == []
    assert material["required_case_count"] == 24
    assert material["reviewed_case_count"] == 24
    assert material["rating_row_count"] == 24
    assert material["question_observation_row_count"] == 24
    assert material["actual_review_evidence_complete"] is True
    assert material["actual_human_review_operation_run"] is True
    assert material["actual_human_review_executed_by_person"] is True
    assert material["actual_human_review_run_here"] is False
    assert material["actual_human_review_complete"] is False
    assert material["p5_confirmed_candidate"] is True
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["p5_confirmed_final"] is False
    assert material["p5_final_allowed"] is False
    assert material["p6_candidate_only_handoff_built"] is True
    assert material["p6_limited_human_readfeel_start_allowed_candidate"] is True
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_material_candidate_only_handoff_built"] is True
    assert material["p8_question_design_material_candidate"] is True
    assert material["p8_material_candidate_refs"] == [
        "question_may_reduce_overread_risk",
        "plus_single_question_candidate_later",
        "premium_deep_dive_candidate_later",
    ]
    assert material["p8_material_candidate_ref_count"] == 3
    assert material["p8_material_candidate_source_observation_row_count"] == 24
    assert material["p8_material_candidate_classes_are_allowed"] is True
    assert material["p8_material_candidate_question_text_included"] is False
    assert material["p8_material_candidate_draft_question_text_included"] is False
    assert material["p8_material_candidate_question_answer_persistence_started"] is False
    assert material["p8_start_allowed"] is False
    assert material["r52_reintake_handoff_envelope_built"] is True
    assert material["r52_reintake_handoff_ref"] == cs.P7_R54_AHR_CS17_R52_HANDOFF_REF_DEFAULT
    assert material["r52_reintake_handoff_ready"] is True
    assert material["r52_reintake_handoff_ready_here"] is True
    assert material["r52_reintake_execution_requested_here"] is False
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == cs.P7_R54_AHR_CS17_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cs.P7_R54_AHR_CS17_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cs.P7_R54_AHR_CS18_STEP_REF
    _assert_bodyfree_no_touch_allowing(material, cs.P7_R54_AHR_CS17_ALLOWED_TRUE_FALSE_FLAG_REFS)


@pytest.mark.parametrize(
    "flag_name",
    (
        "p5_repair_return_required",
        "p4_current_only_repair_required",
        "r54_operation_inconclusive",
        "operation_blocked_preflight_or_execution",
        "operation_blocked_disposal",
        "operation_blocked_body_leak_or_question_text",
        "operation_blocked_no_touch",
    ),
)
def test_cs17_blocks_when_cs16_is_not_confirmed_candidate(flag_name: str) -> None:
    cs16 = _build_ready_cs16(**{flag_name: True})
    material = cs.build_p7_r54_ahr_cs17_p6_p8_candidate_only_r52_handoff_envelope(
        p5_decision_candidate_separation=cs16,
        p8_material_candidate_refs=("question_may_reduce_overread_risk",),
    )
    assert material["candidate_handoff_status_ref"] == cs.P7_R54_AHR_CS17_BLOCKED_STATUS_REF
    assert material["r52_reintake_handoff_ready"] is False
    assert material["p6_candidate_only_handoff_built"] is False
    assert material["p8_material_candidate_only_handoff_built"] is False
    assert material["p8_material_candidate_refs"] == []
    assert material["p8_start_allowed"] is False
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["next_required_step"] == cs.P7_R54_AHR_CS17_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert cs.assert_p7_r54_ahr_cs17_p6_p8_candidate_only_r52_handoff_envelope_contract(material) is True


def test_cs17_rejects_unallowed_p8_material_candidate_class() -> None:
    material = cs.build_p7_r54_ahr_cs17_p6_p8_candidate_only_r52_handoff_envelope(
        p5_decision_candidate_separation=_build_ready_cs16(),
        p8_material_candidate_refs=("not_question_p5_surface_repair_required",),
    )
    assert material["p8_material_candidate_classes_are_allowed"] is False
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs17_p6_p8_candidate_only_r52_handoff_envelope_contract(material)


def test_cs17_rejects_mutated_start_execution_or_question_text_flags() -> None:
    for flag in (
        "p5_human_blind_qa_confirmed_final",
        "p5_confirmed_final",
        "p5_final_allowed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "p8_material_candidate_question_text_included",
        "p8_material_candidate_draft_question_text_included",
        "p8_material_candidate_question_answer_persistence_started",
        "r52_reintake_execution_requested_here",
        "actual_r52_reintake_execution_confirmed",
        "p7_complete",
        "release_allowed",
    ):
        material = deepcopy(_build_ready_cs17(p8_material_candidate_refs=("question_may_reduce_overread_risk",)))
        material[flag] = True
        with pytest.raises(ValueError):
            cs.assert_p7_r54_ahr_cs17_p6_p8_candidate_only_r52_handoff_envelope_contract(material)


def test_cs17_aliases_match_primary_builder_and_contract() -> None:
    cs16 = _build_ready_cs16()
    primary = cs.build_p7_r54_ahr_cs17_p6_p8_candidate_only_r52_handoff_envelope(
        p5_decision_candidate_separation=cs16,
        p8_material_candidate_refs=("question_may_reduce_overread_risk",),
    )
    alias = cs.build_p7_r54_ahr_current_snapshot_actual_review_reentry_candidate_handoff_bodyfree(
        p5_decision_candidate_separation=cs16,
        p8_material_candidate_refs=("question_may_reduce_overread_risk",),
    )
    assert alias == primary
    assert cs.assert_p7_r54_ahr_current_snapshot_actual_review_reentry_candidate_handoff_bodyfree_contract(alias) is True
    assert cs.assert_p7_r54_ahr_cs17_candidate_handoff_contract(alias) is True
    assert cs.assert_p7_r54_ahr_cs17_p6_candidate_only_handoff_contract(alias) is True
    assert cs.assert_p7_r54_ahr_cs17_p8_material_candidate_only_handoff_contract(alias) is True
    assert cs.assert_p7_r54_ahr_cs17_r52_reintake_handoff_envelope_contract(alias) is True
