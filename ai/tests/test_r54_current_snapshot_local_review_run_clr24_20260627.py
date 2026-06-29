# -*- coding: utf-8 -*-
"""R54 current snapshot local review run CLR24 contract tests."""

from __future__ import annotations

import os
import sys
from typing import Any

import pytest

sys.path.insert(0, os.path.dirname(__file__))

import emlis_ai_p7_r54_current_snapshot_local_review_run_20260627 as clr03
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr22_clr23_20260627 as clr23
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr24_20260627 as clr
from test_r54_current_snapshot_local_review_run_clr22_clr23_20260627 import (  # noqa: E402
    _assert_bodyfree_no_touch,
    _ready_clr22,
)


def _ready_clr23() -> dict[str, Any]:
    material = clr23.build_p7_r54_clr23_r52_reintake_handoff(final_validation=_ready_clr22())
    assert clr23.assert_p7_r54_clr23_r52_reintake_handoff_contract(material) is True
    return material


def _ready_command_rows() -> list[dict[str, Any]]:
    return [
        clr.build_p7_r54_clr24_validation_command_matrix_row(
            command_ref="backend_compileall_services_ai_inference_tests",
            command_group_ref="backend_compileall",
            command_kind_ref="compileall",
            result_status_ref=clr.P7_R54_CLR24_COMMAND_RESULT_PASSED_REF,
            result_scope_ref="syntax_import_target_compileall_only",
            passed_count=1,
            result_summary_ref="compileall_passed_bodyfree",
        ),
        clr.build_p7_r54_clr24_validation_command_matrix_row(
            command_ref="clr00_to_clr23_split_chain",
            command_group_ref="clr_contract_chain_split",
            command_kind_ref="pytest_selected_target",
            result_status_ref=clr.P7_R54_CLR24_COMMAND_RESULT_PASSED_REF,
            result_scope_ref="clr00_to_clr23_split_chain_selected_target",
            passed_count=247,
            result_summary_ref="clr00_to_clr23_split_chain_passed_bodyfree",
        ),
        clr.build_p7_r54_clr24_validation_command_matrix_row(
            command_ref="selected_regression_split",
            command_group_ref="selected_regression",
            command_kind_ref="pytest_selected_regression",
            result_status_ref=clr.P7_R54_CLR24_COMMAND_RESULT_COLLECTED_ONLY_REF,
            result_scope_ref="selected_regression_collected_only_not_full_suite",
            collected_count=1696,
            result_summary_ref="selected_regression_collected_only_bodyfree",
        ),
    ]


def test_r54_clr00_to_clr23_are_present_before_clr24() -> None:
    handoff = _ready_clr23()

    assert tuple(handoff["implemented_steps"]) == clr23.P7_R54_CLR23_IMPLEMENTED_STEPS
    assert handoff["handoff_status"] == clr23.P7_R54_CLR23_R52_REINTAKE_HANDOFF_READY_STATUS_REF
    assert handoff["r52_reintake_handoff_ready"] is True
    assert handoff["actual_review_evidence_complete"] is True
    assert handoff["next_required_step"] == clr.P7_R54_CLR24_STEP_REF


def test_r54_clr24_default_blocks_without_ready_clr23_handoff() -> None:
    material = clr.build_p7_r54_clr24_validation_command_matrix_documentation_output()

    assert set(material) == set(clr.P7_R54_CLR24_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == clr.P7_R54_CLR24_SCHEMA_VERSION
    assert material["policy_section"] == clr.P7_R54_CLR24_STEP_REF
    assert material["documentation_output_status"] == clr.P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_BY_CLR23_STATUS_REF
    assert material["documentation_output_materialized_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["r52_reintake_handoff_ready"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR24_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr24_validation_command_matrix_documentation_output_contract(material) is True


def test_r54_clr24_ready_documentation_output_is_bodyfree_and_not_full_suite_or_release() -> None:
    material = clr.build_p7_r54_clr24_validation_command_matrix_documentation_output(
        r52_reintake_handoff=_ready_clr23(),
        validation_command_rows=_ready_command_rows(),
    )

    assert set(material) == set(clr.P7_R54_CLR24_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS)
    assert material["documentation_output_status"] == clr.P7_R54_CLR24_DOCUMENTATION_OUTPUT_READY_STATUS_REF
    assert material["documentation_output_materialized_here"] is True
    assert material["documentation_output_file_ref"] == clr.P7_R54_CLR24_DOCUMENTATION_OUTPUT_FILE_REF
    assert material["actual_review_evidence_complete"] is True
    assert material["r52_reintake_handoff_ready"] is True
    assert material["reviewed_case_count"] == 24
    assert material["rating_row_count"] == 24
    assert material["question_observation_row_count"] == 24
    assert material["validation_command_row_count"] == 3
    assert material["executed_validation_command_count"] == 3
    assert material["passed_validation_command_count"] == 2
    assert material["collected_only_validation_command_count"] == 1
    assert material["failed_validation_command_count"] == 0
    assert material["full_backend_suite_green_confirmed"] is False
    assert material["real_device_modal_verified"] is False
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR24_NEXT_WORK_AFTER_CLR24_REF
    _assert_bodyfree_no_touch(
        material,
        allowed_true_false_flags={key for key in clr03.P7_R54_CLR_FALSE_FLAG_REFS if material.get(key) is True},
    )
    assert clr.assert_p7_r54_clr24_validation_command_matrix_documentation_output_contract(material) is True


def test_r54_clr24_collect_only_and_rn_contract_do_not_become_overclaims() -> None:
    rows = _ready_command_rows() + [
        clr.build_p7_r54_clr24_validation_command_matrix_row(
            command_ref="rn_contract_passed_contract_only",
            command_group_ref="rn_contract",
            command_kind_ref="rn_contract",
            result_status_ref=clr.P7_R54_CLR24_COMMAND_RESULT_PASSED_REF,
            result_scope_ref="rn_contract_not_real_device_modal_verification",
            passed_count=36,
            result_summary_ref="rn_contract_passed_not_real_device_bodyfree",
        )
    ]
    material = clr.build_p7_r54_clr24_validation_command_matrix_documentation_output(
        r52_reintake_handoff=_ready_clr23(),
        validation_command_rows=rows,
    )

    assert material["documentation_output_status"] == clr.P7_R54_CLR24_DOCUMENTATION_OUTPUT_READY_STATUS_REF
    assert "selected_regression_collected_only_not_full_suite" in material["collection_only_scope_refs"]
    assert "rn_contract_passed_contract_only" in material["green_claim_scope_refs"]
    assert material["collect_only_claimed_as_full_suite_green"] is False
    assert material["rn_contract_claimed_as_real_device_modal_verified"] is False
    assert material["real_device_modal_verified"] is False
    assert material["full_backend_suite_green_confirmed"] is False
    assert clr.assert_p7_r54_clr24_validation_command_matrix_documentation_output_contract(material) is True


def test_r54_clr24_failed_command_blocks_documentation_output() -> None:
    rows = _ready_command_rows() + [
        clr.build_p7_r54_clr24_validation_command_matrix_row(
            command_ref="selected_regression_failed_ref",
            result_status_ref=clr.P7_R54_CLR24_COMMAND_RESULT_FAILED_REF,
            result_scope_ref="selected_regression_not_full_backend_suite",
            failure_count=1,
            result_summary_ref="selected_regression_failed_bodyfree",
        )
    ]
    material = clr.build_p7_r54_clr24_validation_command_matrix_documentation_output(
        r52_reintake_handoff=_ready_clr23(),
        validation_command_rows=rows,
    )

    assert material["documentation_output_status"] == clr.P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_BY_COMMAND_MATRIX_STATUS_REF
    assert material["documentation_output_materialized_here"] is False
    assert material["failed_validation_command_count"] == 1
    assert material["actual_review_evidence_complete"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR24_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr24_validation_command_matrix_documentation_output_contract(material) is True


def test_r54_clr24_precondition_blocked_command_blocks_documentation_output() -> None:
    rows = _ready_command_rows() + [
        clr.build_p7_r54_clr24_validation_command_matrix_row(
            command_ref="full_backend_suite_timeout_or_precondition_blocked",
            result_status_ref=clr.P7_R54_CLR24_COMMAND_RESULT_BLOCKED_BY_PRECONDITION_REF,
            result_scope_ref="full_backend_suite_not_claimed_green",
            result_summary_ref="full_backend_suite_blocked_by_precondition_bodyfree",
        )
    ]
    material = clr.build_p7_r54_clr24_validation_command_matrix_documentation_output(
        r52_reintake_handoff=_ready_clr23(),
        validation_command_rows=rows,
    )

    assert material["documentation_output_status"] == clr.P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_BY_COMMAND_MATRIX_STATUS_REF
    assert material["blocked_by_precondition_validation_command_count"] == 1
    assert material["documentation_output_materialized_here"] is False
    assert material["release_allowed"] is False
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr24_validation_command_matrix_documentation_output_contract(material) is True


def test_r54_clr24_green_claim_overreach_blocks_documentation_output() -> None:
    rows = _ready_command_rows() + [
        clr.build_p7_r54_clr24_validation_command_matrix_row(
            command_ref="selected_regression_as_full_backend_suite_green",
            result_status_ref=clr.P7_R54_CLR24_COMMAND_RESULT_PASSED_REF,
            result_scope_ref="selected_regression_as_full_backend_suite_green",
            passed_count=1,
            result_summary_ref="overclaim_scope_bodyfree",
        )
    ]
    material = clr.build_p7_r54_clr24_validation_command_matrix_documentation_output(
        r52_reintake_handoff=_ready_clr23(),
        validation_command_rows=rows,
    )

    assert material["documentation_output_status"] == clr.P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_BY_CLAIM_OVERREACH_STATUS_REF
    assert material["blocked_green_claim_count"] >= 1
    assert material["documentation_output_materialized_here"] is False
    assert material["full_backend_suite_green_confirmed"] is False
    assert material["release_allowed"] is False
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr24_validation_command_matrix_documentation_output_contract(material) is True


def test_r54_clr24_forbidden_command_matrix_fields_block_without_exporting_body() -> None:
    rows = [
        {
            "command_ref": "bad_row_with_forbidden_fields",
            "result_status_ref": clr.P7_R54_CLR24_COMMAND_RESULT_PASSED_REF,
            "result_scope_ref": "selected_target_only",
            "passed_count": 1,
            "terminal_output_body": "do-not-export",
            "local_absolute_path": "forbidden_local_path_redacted_ref",
        }
    ]
    material = clr.build_p7_r54_clr24_validation_command_matrix_documentation_output(
        r52_reintake_handoff=_ready_clr23(),
        validation_command_rows=rows,
    )

    assert material["documentation_output_status"] == clr.P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_BY_BODYFREE_LEAK_STATUS_REF
    assert material["bodyfree_leak_violation_count"] >= 2
    assert material["documentation_output_materialized_here"] is False
    assert "terminal_output_body" not in material
    assert "local_absolute_path" not in material
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr24_validation_command_matrix_documentation_output_contract(material) is True


def test_r54_clr24_keeps_historical_op24_ev22_separate_from_current_basis() -> None:
    material = clr.build_p7_r54_clr24_validation_command_matrix_documentation_output(
        r52_reintake_handoff=_ready_clr23(),
        validation_command_rows=_ready_command_rows(),
    )

    assert material["operation_current_refs"] == clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["operation_current_refs_are_actual_review_basis"] is True
    assert material["existing_op24_current_refs_are_historical_here"] is True
    assert material["existing_ev22_current_refs_are_historical_here"] is True
    assert material["existing_op24_reused_as_actual_documentation_output_basis"] is False
    assert material["existing_ev22_reused_as_actual_documentation_output_basis"] is False
    assert material["implemented_steps"] == list(clr.P7_R54_CLR24_IMPLEMENTED_STEPS)
    assert material["not_yet_implemented_steps"] == []
    assert clr.assert_p7_r54_clr24_validation_command_matrix_documentation_output_contract(material) is True


def test_r54_clr24_row_contract_rejects_command_string_storage_flag() -> None:
    row = clr.build_p7_r54_clr24_validation_command_matrix_row(command_ref="safe_ref")
    row["command_string_included"] = True
    with pytest.raises(ValueError):
        clr.assert_p7_r54_clr24_validation_command_matrix_row_contract(row)
