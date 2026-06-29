# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy

import pytest

import emlis_ai_p7_r54_p5_human_blind_qa_actual_local_review_result_handoff as r54
from test_emlis_ai_p7_r54_p5_human_blind_qa_actual_local_review_result_handoff_r18_r19_20260623 import (
    _assert_body_free_no_runtime_promotion,
    _ready_summary,
    _repair_summary,
    _yellow_summary,
)
from test_emlis_ai_p7_r54_p5_human_blind_qa_actual_local_review_result_handoff_r20_r21_20260623 import (
    _p8_material_candidate_summary,
    _r20_from_summary,
)


def _r21_from_summary(summary: dict[str, object]) -> dict[str, object]:
    return r54.build_p7_r54_final_no_body_leak_no_question_text_no_touch_validation_bodyfree(
        p8_question_design_material_candidate_handoff=_r20_from_summary(summary),
    )


def _r22_from_summary(summary: dict[str, object]) -> dict[str, object]:
    return r54.build_p7_r54_r52_reintake_handoff_bodyfree(
        final_no_body_leak_no_question_text_no_touch_validation=_r21_from_summary(summary),
    )


def test_r54_r22_default_blocks_until_r21_final_validation_is_ready() -> None:
    handoff = r54.build_p7_r54_r52_reintake_handoff_bodyfree()

    assert set(handoff) == set(r54.P7_R54_R52_REINTAKE_HANDOFF_REQUIRED_FIELD_REFS)
    assert handoff["schema_version"] == r54.P7_R54_R52_REINTAKE_HANDOFF_SCHEMA_VERSION
    assert handoff["policy_section"] == r54.P7_R54_R22_STEP_REF
    assert handoff["r52_reintake_handoff_status"] == "R54_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING"
    assert handoff["r52_reintake_handoff_materialized_here"] is False
    assert handoff["r52_reintake_ready"] is False
    assert handoff["actual_review_evidence_complete"] is False
    assert handoff["disposal_safety_complete"] is False
    assert handoff["p6_start_allowed_true_passed_to_r52"] is False
    assert handoff["p8_start_allowed_true_passed_to_r52"] is False
    assert handoff["r54_22_r52_reintake_handoff_built"] is False
    assert handoff["next_required_step"] == r54.P7_R54_R22_BLOCKED_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_r52_reintake_handoff_bodyfree_contract(handoff) is True
    _assert_body_free_no_runtime_promotion(handoff)


def test_r54_r22_ready_handoff_keeps_r52_decision_material_body_free(tmp_path) -> None:
    handoff = _r22_from_summary(_p8_material_candidate_summary(tmp_path))

    assert handoff["r52_reintake_handoff_status"] == "R54_R52_REINTAKE_HANDOFF_READY"
    assert handoff["r52_reintake_ready"] is True
    assert handoff["actual_review_evidence_complete"] is True
    assert handoff["disposal_safety_complete"] is True
    assert handoff["rating_question_consistency_complete"] is True
    assert handoff["p5_decision_recheck_available"] is True
    assert handoff["no_body_leak_validation_complete"] is True
    assert handoff["no_question_text_validation_complete"] is True
    assert handoff["no_touch_validation_complete"] is True
    assert handoff["p5_decision_candidate_ref"] == "P5_CONFIRMED_CANDIDATE"
    assert handoff["p5_human_blind_qa_confirmed_candidate"] is True
    assert handoff["p5_human_blind_qa_confirmed_final"] is False
    assert handoff["p6_limited_human_readfeel_candidate"] is True
    assert handoff["p6_limited_human_readfeel_start_allowed"] is False
    assert handoff["p6_start_allowed_true_passed_to_r52"] is False
    assert handoff["p8_question_design_material_candidate"] is True
    assert handoff["p8_start_allowed"] is False
    assert handoff["p8_start_allowed_true_passed_to_r52"] is False
    assert handoff["p7_complete"] is False
    assert handoff["release_allowed"] is False
    assert handoff["next_required_step"] == r54.P7_R54_R22_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_r52_reintake_handoff_bodyfree_contract(handoff) is True
    _assert_body_free_no_runtime_promotion(handoff)


def test_r54_r22_p5_repair_is_r52_reintake_ready_but_inconclusive_blocks(tmp_path) -> None:
    repair = _r22_from_summary(_repair_summary(tmp_path))
    yellow = _r22_from_summary(_yellow_summary(tmp_path))

    assert repair["r52_reintake_handoff_status"] == "R54_R52_REINTAKE_HANDOFF_READY"
    assert repair["p5_repair_return_candidate"] is True
    assert repair["p5_human_blind_qa_confirmed_candidate"] is False
    assert repair["p6_limited_human_readfeel_start_allowed"] is False
    assert repair["p8_start_allowed"] is False

    assert yellow["r52_reintake_handoff_status"] == "R54_R52_REINTAKE_BLOCKED_BY_INCONCLUSIVE"
    assert yellow["r52_reintake_ready"] is False
    assert yellow["p5_review_inconclusive"] is True
    assert yellow["p6_limited_human_readfeel_start_allowed"] is False
    assert yellow["p8_start_allowed"] is False

    assert r54.assert_p7_r54_r52_reintake_handoff_bodyfree_contract(repair) is True
    assert r54.assert_p7_r54_r52_reintake_handoff_bodyfree_contract(yellow) is True
    _assert_body_free_no_runtime_promotion(repair)
    _assert_body_free_no_runtime_promotion(yellow)


def test_r54_r22_blocks_body_leak_question_text_no_touch_and_disposal_gap(tmp_path) -> None:
    r20 = _r20_from_summary(_p8_material_candidate_summary(tmp_path))

    question_r21 = r54.build_p7_r54_final_no_body_leak_no_question_text_no_touch_validation_bodyfree(
        p8_question_design_material_candidate_handoff=r20,
        additional_bodyfree_materials_to_scan=(
            {"material_id": "question_text_violation", "question_text": "must not be retained"},
        ),
    )
    question_handoff = r54.build_p7_r54_r52_reintake_handoff_bodyfree(
        final_no_body_leak_no_question_text_no_touch_validation=question_r21,
    )
    assert question_handoff["r52_reintake_handoff_status"] == "R54_R52_REINTAKE_BLOCKED_BY_BODY_LEAK_OR_QUESTION_TEXT"
    assert question_handoff["question_text_detected"] is True

    no_touch_r21 = r54.build_p7_r54_final_no_body_leak_no_question_text_no_touch_validation_bodyfree(
        p8_question_design_material_candidate_handoff=r20,
        additional_bodyfree_materials_to_scan=(
            {"material_id": "runtime_violation", "runtime_changed_here": True},
        ),
    )
    no_touch_handoff = r54.build_p7_r54_r52_reintake_handoff_bodyfree(
        final_no_body_leak_no_question_text_no_touch_validation=no_touch_r21,
    )
    assert no_touch_handoff["r52_reintake_handoff_status"] == "R54_R52_REINTAKE_BLOCKED_BY_NO_TOUCH_VIOLATION"
    assert no_touch_handoff["no_touch_violation_detected"] is True

    disposal_gap_r21 = deepcopy(_r21_from_summary(_ready_summary(tmp_path)))
    disposal_gap_r21["actual_disposal_receipt_materialized_here"] = False
    disposal_gap = r54.build_p7_r54_r52_reintake_handoff_bodyfree(
        final_no_body_leak_no_question_text_no_touch_validation=disposal_gap_r21,
    )
    assert disposal_gap["r52_reintake_handoff_status"] == "R54_R52_REINTAKE_BLOCKED_BY_DISPOSAL_SAFETY"
    assert disposal_gap["r52_reintake_ready"] is False


def test_r54_r22_contract_rejects_start_allowed_or_body_question_leak(tmp_path) -> None:
    handoff = _r22_from_summary(_ready_summary(tmp_path))
    for key in (
        "p5_human_blind_qa_confirmed_final",
        "p5_decision_finalized_here",
        "p6_limited_human_readfeel_start_allowed",
        "p6_start_allowed_true_passed_to_r52",
        "p8_start_allowed",
        "p8_start_allowed_true_passed_to_r52",
        "p7_complete",
        "release_allowed",
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "question_text_included",
        "draft_question_text_included",
        "comment_text_included",
        "local_absolute_path_included",
        "runtime_changed_here",
        "question_api_implemented",
    ):
        mutated = deepcopy(handoff)
        mutated[key] = True
        with pytest.raises(ValueError):
            r54.assert_p7_r54_r52_reintake_handoff_bodyfree_contract(mutated)


def test_r54_r23_default_blocks_until_r22_is_ready() -> None:
    matrix = r54.build_p7_r54_validation_command_matrix_documentation_output_bodyfree()

    assert set(matrix) == set(r54.P7_R54_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS)
    assert matrix["schema_version"] == r54.P7_R54_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION
    assert matrix["policy_section"] == r54.P7_R54_R23_STEP_REF
    assert matrix["validation_documentation_status"] == "VALIDATION_DOCUMENTATION_BLOCKED_BY_R54_22_R52_REINTAKE_HANDOFF"
    assert matrix["validation_command_matrix_materialized_here"] is False
    assert matrix["documentation_output_materialized_here"] is False
    assert matrix["command_matrix_rows"] == []
    assert matrix["command_matrix_row_count"] == 0
    assert matrix["command_matrix_claims_full_backend_green"] is False
    assert matrix["backend_collect_only_is_full_suite_green"] is False
    assert matrix["next_required_step"] == r54.P7_R54_R23_BLOCKED_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_validation_command_matrix_documentation_output_bodyfree_contract(matrix) is True
    _assert_body_free_no_runtime_promotion(matrix)


def test_r54_r23_materializes_target_regression_collect_only_and_rn_no_touch_matrix(tmp_path) -> None:
    matrix = r54.build_p7_r54_validation_command_matrix_documentation_output_bodyfree(
        r52_reintake_handoff=_r22_from_summary(_ready_summary(tmp_path)),
    )

    assert matrix["validation_documentation_status"] == "VALIDATION_COMMAND_MATRIX_DOCUMENTATION_READY"
    assert matrix["validation_command_matrix_materialized_here"] is True
    assert matrix["documentation_output_materialized_here"] is True
    assert matrix["command_matrix_body_free"] is True
    assert matrix["command_matrix_contains_local_absolute_path"] is False
    assert matrix["command_matrix_claims_full_backend_green"] is False
    assert matrix["validation_commands_ran_here"] is False
    assert matrix["actual_validation_execution_completed_here"] is False
    assert matrix["required_command_groups_present"] is True
    assert matrix["r54_target_tests_present"] is True
    assert matrix["r53_regression_split_present"] is True
    assert matrix["r52_r51_r50_r49_regression_present"] is True
    assert matrix["rn_contract_no_touch_present"] is True
    assert matrix["backend_collect_only_present"] is True
    assert matrix["backend_collect_only_is_full_suite_green"] is False
    assert matrix["rn_no_touch_is_real_device_readfeel"] is False
    assert matrix["full_backend_suite_green_confirmed"] is False
    assert matrix["p6_limited_human_readfeel_start_allowed"] is False
    assert matrix["p8_start_allowed"] is False
    assert matrix["release_allowed"] is False
    assert tuple(matrix["implemented_steps"]) == r54.P7_R54_R23_IMPLEMENTED_STEPS
    assert matrix["next_required_step"] == r54.P7_R54_R23_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_validation_command_matrix_documentation_output_bodyfree_contract(matrix) is True
    _assert_body_free_no_runtime_promotion(matrix)


def test_r54_r23_command_rows_do_not_claim_full_backend_green_or_local_paths(tmp_path) -> None:
    matrix = r54.build_p7_r54_validation_command_matrix_documentation_output_bodyfree(
        r52_reintake_handoff=_r22_from_summary(_ready_summary(tmp_path)),
    )

    assert matrix["command_matrix_row_count"] == len(matrix["command_matrix_rows"])
    assert matrix["command_matrix_row_count"] >= 20
    assert any(row["command_group_ref"] == "backend_collect_only" for row in matrix["command_matrix_rows"])
    assert any(row["command_group_ref"] == "rn_contract_no_touch" for row in matrix["command_matrix_rows"])
    for row in matrix["command_matrix_rows"]:
        assert row["body_free"] is True
        assert row["local_absolute_path_included"] is False
        assert row["terminal_output_included"] is False
        assert row["full_backend_suite_green_claimed"] is False
        assert row["validation_executed_here"] is False
    collect_only_rows = [row for row in matrix["command_matrix_rows"] if row["command_group_ref"] == "backend_collect_only"]
    assert collect_only_rows and collect_only_rows[0]["collect_only"] is True


def test_r54_r23_contract_rejects_execution_claims_start_allowed_or_command_inflation(tmp_path) -> None:
    matrix = r54.build_p7_r54_validation_command_matrix_documentation_output_bodyfree(
        r52_reintake_handoff=_r22_from_summary(_ready_summary(tmp_path)),
    )
    for key in (
        "validation_commands_ran_here",
        "actual_validation_execution_completed_here",
        "full_backend_suite_green_confirmed",
        "backend_collect_only_claimed_as_full_backend_green",
        "rn_contract_claimed_as_real_device_modal_readfeel",
        "p5_human_blind_qa_confirmed_final",
        "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "question_text_included",
        "draft_question_text_included",
        "local_absolute_path_included",
        "runtime_changed_here",
    ):
        mutated = deepcopy(matrix)
        mutated[key] = True
        with pytest.raises(ValueError):
            r54.assert_p7_r54_validation_command_matrix_documentation_output_bodyfree_contract(mutated)
