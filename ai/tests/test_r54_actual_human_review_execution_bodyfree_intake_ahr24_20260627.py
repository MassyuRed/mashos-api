# -*- coding: utf-8 -*-
"""Tests for R54-AHR24 validation command matrix / documentation output."""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r54_actual_human_review_execution_bodyfree_intake_20260627 as ahr
from test_r54_actual_human_review_execution_bodyfree_intake_ahr18_ahr19_20260627 import (
    assert_bodyfree_no_touch_no_final_promotion,
)
from test_r54_actual_human_review_execution_bodyfree_intake_ahr22_ahr23_20260627 import (
    build_valid_ahr23_handoff,
)


def build_valid_ahr24_command_rows(*, rn_contract_passed: bool = False) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for command_ref in ahr.P7_R54_AHR24_COMMAND_REF_REFS:
        if command_ref in ahr.P7_R54_AHR24_REQUIRED_EXECUTED_PASSED_COMMAND_REFS:
            rows.append(
                {
                    "command_ref": command_ref,
                    "executed": True,
                    "result_status_ref": ahr.P7_R54_AHR24_RESULT_STATUS_PASSED_REF,
                    "pass_count": 1,
                }
            )
        elif command_ref == "rn_contract" and rn_contract_passed:
            rows.append(
                {
                    "command_ref": command_ref,
                    "executed": True,
                    "result_status_ref": ahr.P7_R54_AHR24_RESULT_STATUS_PASSED_REF,
                    "pass_count": 1,
                    "claim_forbidden_refs": ["rn_real_device_modal_verified"],
                }
            )
        else:
            rows.append(
                {
                    "command_ref": command_ref,
                    "executed": False,
                    "result_status_ref": ahr.P7_R54_AHR24_RESULT_STATUS_NOT_EXECUTED_REF,
                    "pass_count": 0,
                }
            )
    return rows


@lru_cache(maxsize=None)
def _cached_valid_ahr24_documentation_output(
    p8_candidate_index: int | None = None,
    rn_contract_passed: bool = False,
) -> tuple[tuple[str, object], ...]:
    handoff = build_valid_ahr23_handoff(p8_candidate_index=p8_candidate_index)
    material = ahr.build_p7_r54_ahr24_validation_command_matrix_documentation_output(
        r52_reintake_handoff_envelope=handoff,
        command_rows=build_valid_ahr24_command_rows(rn_contract_passed=rn_contract_passed),
        review_session_id=handoff["review_session_id"],
    )
    assert ahr.assert_p7_r54_ahr24_validation_command_matrix_documentation_output_contract(material) is True
    assert material["validation_command_matrix_status_ref"] == ahr.P7_R54_AHR24_READY_STATUS_REF
    return tuple(sorted(material.items()))


def build_valid_ahr24_documentation_output(
    *,
    p8_candidate_index: int | None = None,
    rn_contract_passed: bool = False,
) -> dict[str, object]:
    return dict(_cached_valid_ahr24_documentation_output(p8_candidate_index, rn_contract_passed))


def test_r54_ahr24_default_blocks_without_handoff_or_commands() -> None:
    material = ahr.build_p7_r54_ahr24_validation_command_matrix_documentation_output()

    assert ahr.assert_p7_r54_ahr24_validation_command_matrix_documentation_output_contract(material) is True
    assert material["validation_command_matrix_status_ref"] == ahr.P7_R54_AHR24_BLOCKED_STATUS_REF
    assert material["documentation_output_status_ref"] == ahr.P7_R54_AHR24_BLOCKED_STATUS_REF
    assert material["execution_blocker_ids"]
    assert material["result_memo_bodyfree_only"] is False
    assert material["result_memo_materialized_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR24_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert_bodyfree_no_touch_no_final_promotion(material)


def test_r54_ahr24_records_command_matrix_and_documentation_without_promoting_release() -> None:
    material = build_valid_ahr24_documentation_output(p8_candidate_index=3, rn_contract_passed=True)

    assert material["schema_version"] == ahr.P7_R54_AHR24_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION
    assert material["operation_step_ref"] == ahr.P7_R54_AHR24_STEP_REF
    assert material["validation_command_matrix_reason_refs"] == [ahr.P7_R54_AHR24_READY_REASON_REF]
    assert material["command_row_count"] == len(ahr.P7_R54_AHR24_COMMAND_REF_REFS)
    assert material["required_executed_passed_command_refs_passed"] is True
    assert set(ahr.P7_R54_AHR24_REQUIRED_EXECUTED_PASSED_COMMAND_REFS).issubset(set(material["passed_command_refs"]))
    assert "full_backend_suite" in material["not_executed_command_refs"]
    assert "rn_real_device_modal" in material["not_executed_command_refs"]
    assert material["rn_contract_green_confirmed"] is True
    assert material["rn_real_device_modal_verified"] is False
    assert material["full_backend_suite_green_confirmed"] is False
    assert material["result_memo_bodyfree_only"] is True
    assert material["result_memo_materialized_here"] is True
    assert material["terminal_output_body_recorded"] is False
    assert material["stdout_body_recorded"] is False
    assert material["stderr_body_recorded"] is False
    assert material["traceback_body_recorded"] is False
    assert material["raw_body_recorded"] is False
    assert material["question_text_recorded"] is False
    assert material["local_absolute_path_recorded"] is False
    assert material["helper_green_is_not_actual_human_review_complete"] is True
    assert material["selected_regression_green_is_not_full_backend_suite_green"] is True
    assert material["rn_contract_green_is_not_rn_real_device_modal_verified"] is True
    assert material["r52_handoff_ready_is_not_p5_final_p6_start_p8_start_release"] is True
    assert material["actual_review_evidence_complete"] is True
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["p5_human_blind_qa_confirmed_candidate"] is True
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR24_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ahr.P7_R54_AHR24_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ahr.P7_R54_AHR24_NEXT_REQUIRED_STEP_REF
    assert_bodyfree_no_touch_no_final_promotion(material)


def test_r54_ahr24_blocks_failed_required_command_without_terminal_body() -> None:
    handoff = build_valid_ahr23_handoff()
    rows = build_valid_ahr24_command_rows()
    for row in rows:
        if row["command_ref"] == "selected_r55_regression":
            row["result_status_ref"] = ahr.P7_R54_AHR24_RESULT_STATUS_FAILED_REF
            row["executed"] = True
            row["pass_count"] = 0
            row["failure_summary_ref"] = "selected_r55_regression_failed_summary_ref"
    material = ahr.build_p7_r54_ahr24_validation_command_matrix_documentation_output(
        r52_reintake_handoff_envelope=handoff,
        command_rows=rows,
    )

    assert ahr.assert_p7_r54_ahr24_validation_command_matrix_documentation_output_contract(material) is True
    assert material["validation_command_matrix_status_ref"] == ahr.P7_R54_AHR24_BLOCKED_STATUS_REF
    assert "required_command_selected_r55_regression_not_passed" in material["execution_blocker_ids"]
    assert material["failed_command_refs"] == ["selected_r55_regression"]
    assert material["terminal_output_body_recorded"] is False
    assert material["result_memo_materialized_here"] is False
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert_bodyfree_no_touch_no_final_promotion(material)


def test_r54_ahr24_blocks_full_backend_suite_green_claim_even_when_other_commands_pass() -> None:
    handoff = build_valid_ahr23_handoff()
    rows = build_valid_ahr24_command_rows()
    for row in rows:
        if row["command_ref"] == "full_backend_suite":
            row["executed"] = True
            row["result_status_ref"] = ahr.P7_R54_AHR24_RESULT_STATUS_PASSED_REF
            row["pass_count"] = 9999
    material = ahr.build_p7_r54_ahr24_validation_command_matrix_documentation_output(
        r52_reintake_handoff_envelope=handoff,
        command_rows=rows,
    )

    assert ahr.assert_p7_r54_ahr24_validation_command_matrix_documentation_output_contract(material) is True
    assert material["validation_command_matrix_status_ref"] == ahr.P7_R54_AHR24_BLOCKED_STATUS_REF
    assert "full_backend_suite_passed_but_must_not_be_claimed_here" in material["execution_blocker_ids"]
    assert material["full_backend_suite_green_confirmed"] is False
    assert material["release_allowed"] is False
    assert_bodyfree_no_touch_no_final_promotion(material)


def test_r54_ahr24_blocks_command_row_with_forbidden_output_body_key() -> None:
    handoff = build_valid_ahr23_handoff()
    rows = build_valid_ahr24_command_rows()
    rows[0]["stdout_body"] = "must_not_be_recorded"
    material = ahr.build_p7_r54_ahr24_validation_command_matrix_documentation_output(
        r52_reintake_handoff_envelope=handoff,
        command_rows=rows,
    )

    assert ahr.assert_p7_r54_ahr24_validation_command_matrix_documentation_output_contract(material) is True
    assert material["validation_command_matrix_status_ref"] == ahr.P7_R54_AHR24_BLOCKED_STATUS_REF
    assert "command_row_01_contains_forbidden_body_question_path_hash_key" in material["execution_blocker_ids"]
    assert material["stdout_body_recorded"] is False
    assert material["result_memo_bodyfree_only"] is False
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
        ("full_backend_suite_green_confirmed", True),
        ("rn_real_device_modal_verified", True),
        ("terminal_output_body_recorded", True),
        ("question_text_materialized_here", True),
    ],
)
def test_r54_ahr24_rejects_final_or_leak_or_claim_mutations(field: str, bad_value: object) -> None:
    material = build_valid_ahr24_documentation_output()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr24_validation_command_matrix_documentation_output_contract(mutated)


def test_r54_ahr24_design_aliases_point_to_canonical_helper() -> None:
    handoff = build_valid_ahr23_handoff()
    material = ahr.build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr24_validation_command_matrix_documentation_output(
        r52_reintake_handoff_envelope=handoff,
        command_rows=build_valid_ahr24_command_rows(),
    )

    assert material["validation_command_matrix_status_ref"] == ahr.P7_R54_AHR24_READY_STATUS_REF
    assert ahr.assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr24_validation_command_matrix_documentation_output_contract(material) is True
