# -*- coding: utf-8 -*-
"""R54 actual local-only review operation re-entry OP24 contract tests."""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import json

import pytest

import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as op
from test_emlis_ai_p7_r54_actual_local_review_operation_reentry_op22_op23_20260625 import (
    _op22_ready_without_p8_material,
    _op22_ready_with_p8_material,
)


def _assert_bodyfree_no_terminal_output_or_claim_overreach(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    forbidden_tokens = (
        '"raw_input"',
        '"comment_text":',
        '"returned_emlis_body"',
        '"bounded_history_surface"',
        '"reviewer_free_text":',
        '"reviewer_notes_body"',
        '"local_path":',
        '"body_hash"',
        '"body_full_packet_content"',
        '"question_text":',
        '"draft_question_text":',
        '"terminal_output":',
        '"stdout":',
        '"stderr":',
        '"command_string_included": true',
        '"command_result_body_stored_here": true',
        '"terminal_output_stored_here": true',
        '"full_backend_suite_green_claimed": true',
        '"real_device_modal_verified_claimed": true',
        '"actual_human_review_complete_claimed_by_helper": true',
        '"p8_start_allowed": true',
        '"p6_limited_human_readfeel_start_allowed": true',
        '"release_allowed": true',
    )
    for token in forbidden_tokens:
        assert token not in dumped
    assert material["body_free"] is True
    assert material["raw_body_included"] is False
    assert material["question_text_included"] is False
    assert material["draft_question_text_included"] is False
    assert material["local_path_included"] is False
    assert material["command_result_body_stored_here"] is False
    assert material["terminal_output_stored_here"] is False
    assert material["command_string_included"] is False


@lru_cache(maxsize=1)
def _cached_op23_ready_without_p8_material() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op23_r52_reintake_handoff(
        final_validation=_op22_ready_without_p8_material()
    )
    assert op.assert_p7_r54_op23_r52_reintake_handoff_contract(material) is True
    return (material,)


def _op23_ready_without_p8_material() -> dict[str, object]:
    return deepcopy(_cached_op23_ready_without_p8_material()[0])


@lru_cache(maxsize=1)
def _cached_op23_ready_with_p8_material() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op23_r52_reintake_handoff(
        final_validation=_op22_ready_with_p8_material()
    )
    assert op.assert_p7_r54_op23_r52_reintake_handoff_contract(material) is True
    assert material["p8_question_design_material_candidate"] is True
    return (material,)


def _op23_ready_with_p8_material() -> dict[str, object]:
    return deepcopy(_cached_op23_ready_with_p8_material()[0])


def _validation_rows() -> list[dict[str, object]]:
    return [
        {
            "command_ref": "op00_op23_target",
            "command_group_ref": "r54_operation_reentry_target",
            "command_kind_ref": "pytest_target",
            "result_status_ref": op.P7_R54_OP24_COMMAND_RESULT_PASSED_REF,
            "result_scope_ref": "r54_op00_op23_target_only",
            "passed_count": 460,
            "result_summary_ref": "op00_op23_target_passed_bodyfree_count_only",
        },
        {
            "command_ref": "backend_compileall",
            "command_group_ref": "backend_static_validation",
            "command_kind_ref": "compileall",
            "result_status_ref": op.P7_R54_OP24_COMMAND_RESULT_PASSED_REF,
            "result_scope_ref": "backend_compileall_only",
            "result_summary_ref": "backend_compileall_passed_bodyfree_status_only",
        },
        {
            "command_ref": "backend_collect_only",
            "command_group_ref": "backend_collection_validation",
            "command_kind_ref": "pytest_collect_only",
            "result_status_ref": op.P7_R54_OP24_COMMAND_RESULT_COLLECTED_ONLY_REF,
            "result_scope_ref": "collect_only_not_full_suite",
            "collected_count": 5571,
            "warning_count": 1,
            "result_summary_ref": "backend_collect_only_collected_bodyfree_count_only",
        },
    ]


def test_op24_symbols_are_exported() -> None:
    expected = {
        "P7_R54_OPERATION_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION",
        "P7_R54_OPERATION_VALIDATION_COMMAND_MATRIX_ROW_SCHEMA_VERSION",
        "P7_R54_OP24_DOCUMENTATION_OUTPUT_READY_STATUS_REF",
        "P7_R54_OP24_DOCUMENTATION_OUTPUT_BLOCKED_BY_OP23_STATUS_REF",
        "P7_R54_OP24_DOCUMENTATION_OUTPUT_BLOCKED_BY_COMMAND_MATRIX_STATUS_REF",
        "P7_R54_OP24_DOCUMENTATION_OUTPUT_BLOCKED_BY_CLAIM_OVERREACH_STATUS_REF",
        "P7_R54_OP24_COMMAND_RESULT_COLLECTED_ONLY_REF",
        "build_p7_r54_op24_validation_command_matrix_row",
        "assert_p7_r54_op24_validation_command_matrix_row_contract",
        "build_p7_r54_op24_validation_command_matrix_documentation_output",
        "assert_p7_r54_op24_validation_command_matrix_documentation_output_contract",
        "build_p7_r54_operation_validation_command_matrix_documentation_output_bodyfree",
    }
    assert expected.issubset(set(op.__all__))


def test_op24_default_blocks_until_op23_r52_handoff_ready() -> None:
    material = op.build_p7_r54_op24_validation_command_matrix_documentation_output(
        validation_command_rows=_validation_rows()
    )

    assert op.assert_p7_r54_op24_validation_command_matrix_documentation_output_contract(material) is True
    assert material["documentation_output_status"] == op.P7_R54_OP24_DOCUMENTATION_OUTPUT_BLOCKED_BY_OP23_STATUS_REF
    assert material["documentation_output_materialized_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["r52_reintake_handoff_ready"] is False
    assert material["next_required_step"] == op.P7_R54_OP24_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert material["open_execution_blocker_ids"]
    assert op.P7_R54_OP24_STEP_REF in tuple(material["not_yet_implemented_steps"])
    _assert_bodyfree_no_terminal_output_or_claim_overreach(material)


def test_op24_blocks_ready_op23_without_command_matrix_rows() -> None:
    material = op.build_p7_r54_op24_validation_command_matrix_documentation_output(
        r52_reintake_handoff=_op23_ready_without_p8_material(),
        validation_command_rows=[],
    )

    assert material["documentation_output_status"] == op.P7_R54_OP24_DOCUMENTATION_OUTPUT_BLOCKED_BY_COMMAND_MATRIX_STATUS_REF
    assert material["documentation_output_reason_refs"] == [op.P7_R54_OP24_COMMAND_MATRIX_MISSING_REASON_REF]
    assert material["documentation_output_materialized_here"] is False
    assert material["validation_command_row_count"] == 0
    assert material["executed_validation_command_count"] == 0
    assert material["actual_review_evidence_complete"] is False
    assert material["next_required_step"] == op.P7_R54_OP24_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_terminal_output_or_claim_overreach(material)


def test_op24_ready_materializes_validation_documentation_output_bodyfree() -> None:
    material = op.build_p7_r54_op24_validation_command_matrix_documentation_output(
        r52_reintake_handoff=_op23_ready_without_p8_material(),
        validation_command_rows=_validation_rows(),
        not_executed_validation_refs=(
            "full_backend_suite_not_executed_in_op24",
            "rn_contract_not_executed_in_op24",
            "real_device_modal_not_executed_in_op24",
            "actual_human_review_operation_not_executed_in_op24",
        ),
    )

    assert material["documentation_output_status"] == op.P7_R54_OP24_DOCUMENTATION_OUTPUT_READY_STATUS_REF
    assert material["documentation_output_ref"] == op.P7_R54_OP24_DOCUMENTATION_OUTPUT_REF
    assert material["documentation_output_reason_refs"] == [op.P7_R54_OP24_READY_REASON_REF]
    assert material["documentation_output_issue_refs"] == []
    assert material["documentation_output_materialized_here"] is True
    assert material["actual_review_evidence_complete"] is True
    assert material["r52_reintake_handoff_ready"] is True
    assert material["r52_reintake_required"] is True
    assert material["reviewed_case_count"] == op.P7_R51_REQUIRED_CASE_COUNT
    assert material["rating_row_count"] == op.P7_R51_REQUIRED_CASE_COUNT
    assert material["question_observation_row_count"] == op.P7_R51_REQUIRED_CASE_COUNT
    assert material["validation_command_row_count"] == 3
    assert material["executed_validation_command_count"] == 3
    assert material["passed_validation_command_count"] == 2
    assert material["collected_only_validation_command_count"] == 1
    assert material["failed_validation_command_count"] == 0
    assert material["green_claim_scope_count"] == 2
    assert material["collection_only_scope_count"] == 1
    assert material["blocked_green_claim_refs"] == []
    assert material["not_executed_validation_ref_count"] == 4
    assert material["p5_human_blind_qa_confirmed_candidate"] is True
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["p6_limited_human_readfeel_candidate"] is True
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == op.P7_R54_OP24_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == op.P7_R54_OP24_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == op.P7_R54_OP_NEXT_WORK_AFTER_OP24_REF
    assert material["open_execution_blocker_ids"] == []
    _assert_bodyfree_no_terminal_output_or_claim_overreach(material)


def test_op24_preserves_p8_material_candidate_as_candidate_only() -> None:
    material = op.build_p7_r54_op24_validation_command_matrix_documentation_output(
        r52_reintake_handoff=_op23_ready_with_p8_material(),
        validation_command_rows=_validation_rows(),
    )

    assert material["documentation_output_status"] == op.P7_R54_OP24_DOCUMENTATION_OUTPUT_READY_STATUS_REF
    assert material["p8_question_design_material_candidate"] is True
    assert material["p8_start_allowed"] is False
    assert material["question_implementation_started_here"] is False
    assert material["p8_implementation_spec_finalized_here"] is False
    assert material["question_text_included"] is False
    assert material["draft_question_text_included"] is False
    _assert_bodyfree_no_terminal_output_or_claim_overreach(material)


def test_op24_collect_only_row_is_collection_only_not_full_suite_green() -> None:
    row = op.build_p7_r54_op24_validation_command_matrix_row(
        command_ref="backend_collect_only",
        command_kind_ref="pytest_collect_only",
        result_status_ref=op.P7_R54_OP24_COMMAND_RESULT_COLLECTED_ONLY_REF,
        result_scope_ref="collect_only_not_full_suite",
        collected_count=5571,
        warning_count=1,
    )

    assert row["collection_only_claim_allowed"] is True
    assert row["green_claim_allowed"] is False
    assert row["full_suite_claim_allowed"] is False
    assert row["real_device_claim_allowed"] is False
    assert row["actual_human_review_claim_allowed"] is False
    assert row["terminal_output_stored_here"] is False
    assert row["command_result_body_stored_here"] is False
    assert op.assert_p7_r54_op24_validation_command_matrix_row_contract(row) is True


def test_op24_blocks_green_claim_overreach_without_changing_flags() -> None:
    material = op.build_p7_r54_op24_validation_command_matrix_documentation_output(
        r52_reintake_handoff=_op23_ready_without_p8_material(),
        validation_command_rows=_validation_rows(),
        green_claim_scope_refs=(
            "full_backend_suite_green",
            "real_device_modal_verified",
            "actual_human_review_complete",
        ),
    )

    assert material["documentation_output_status"] == op.P7_R54_OP24_DOCUMENTATION_OUTPUT_BLOCKED_BY_CLAIM_OVERREACH_STATUS_REF
    assert material["documentation_output_materialized_here"] is False
    assert material["blocked_green_claim_count"] == 3
    assert material["green_claim_scope_refs"] == []
    assert material["actual_review_evidence_complete"] is False
    assert material["full_backend_suite_green_claimed"] is False
    assert material["real_device_modal_verified_claimed"] is False
    assert material["actual_human_review_complete_claimed_by_helper"] is False
    assert material["release_allowed"] is False
    assert material["open_execution_blocker_ids"]
    _assert_bodyfree_no_terminal_output_or_claim_overreach(material)


def test_op24_contract_rejects_terminal_output_or_command_body_claims() -> None:
    material = op.build_p7_r54_op24_validation_command_matrix_documentation_output(
        r52_reintake_handoff=_op23_ready_without_p8_material(),
        validation_command_rows=_validation_rows(),
    )

    bad = deepcopy(material)
    bad["terminal_output_stored_here"] = True
    with pytest.raises(ValueError, match="terminal_output_stored_here"):
        op.assert_p7_r54_op24_validation_command_matrix_documentation_output_contract(bad)

    bad = deepcopy(material)
    bad["command_result_body_stored_here"] = True
    with pytest.raises(ValueError, match="command_result_body_stored_here"):
        op.assert_p7_r54_op24_validation_command_matrix_documentation_output_contract(bad)


def test_op24_contract_rejects_helper_green_to_human_review_completion_claim() -> None:
    material = op.build_p7_r54_op24_validation_command_matrix_documentation_output(
        r52_reintake_handoff=_op23_ready_without_p8_material(),
        validation_command_rows=_validation_rows(),
    )

    bad = deepcopy(material)
    bad["actual_human_review_complete_claimed_by_helper"] = True
    with pytest.raises(ValueError, match="actual_human_review_complete_claimed_by_helper"):
        op.assert_p7_r54_op24_validation_command_matrix_documentation_output_contract(bad)

    bad = deepcopy(material)
    bad["p8_start_allowed"] = True
    with pytest.raises(ValueError, match="p8_start_allowed"):
        op.assert_p7_r54_op24_validation_command_matrix_documentation_output_contract(bad)


def test_op24_failed_command_row_blocks_documentation_readiness() -> None:
    rows = [
        *_validation_rows(),
        {
            "command_ref": "selected_regression_failed",
            "command_kind_ref": "pytest_target",
            "result_status_ref": op.P7_R54_OP24_COMMAND_RESULT_FAILED_REF,
            "result_scope_ref": "r54_r55_selected_regression_only",
            "failure_count": 1,
            "result_summary_ref": "selected_regression_failed_bodyfree_count_only",
        },
    ]
    material = op.build_p7_r54_op24_validation_command_matrix_documentation_output(
        r52_reintake_handoff=_op23_ready_without_p8_material(),
        validation_command_rows=rows,
    )

    assert material["documentation_output_status"] == op.P7_R54_OP24_DOCUMENTATION_OUTPUT_BLOCKED_BY_COMMAND_MATRIX_STATUS_REF
    assert material["failed_validation_command_count"] == 1
    assert material["documentation_output_materialized_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["open_execution_blocker_ids"]
    _assert_bodyfree_no_terminal_output_or_claim_overreach(material)


def test_op24_aliases_match_primary_builder() -> None:
    op23 = _op23_ready_without_p8_material()
    primary = op.build_p7_r54_op24_validation_command_matrix_documentation_output(
        r52_reintake_handoff=op23,
        validation_command_rows=_validation_rows(),
    )
    alias = op.build_p7_r54_operation_validation_command_matrix_documentation_output_bodyfree(
        r52_reintake_handoff=op23,
        validation_command_rows=_validation_rows(),
    )
    assert primary == alias
