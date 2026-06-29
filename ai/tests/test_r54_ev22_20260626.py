# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy

import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as r54op
import emlis_ai_p7_r54_actual_review_execution_evidence_materialization_20260626 as ev
import test_r54_ev20_ev21_20260626 as prev21


FORBIDDEN_DUMP_TOKENS = (
    '"raw_input":',
    '"raw_answer":',
    '"comment_text":',
    '"comment_text_body":',
    '"returned_emlis_surface":',
    '"current_input_review_surface":',
    '"bounded_owned_history_review_surface":',
    '"reviewer_free_text":',
    '"reviewer_note":',
    '"reviewer_notes":',
    '"question_text": "',
    '"draft_question_text": "',
    '"question_body":',
    '"local_absolute_path":',
    '"body_content_hash":',
    '"packet_content_hash":',
    '"terminal_output": "',
    '"stdout":',
    '"stderr":',
    '"traceback":',
)
FORBIDDEN_TRUE_TOKENS = (
    '"api_changed": true',
    '"db_changed": true',
    '"rn_changed": true',
    '"runtime_changed": true',
    '"api_route_changed": true',
    '"db_schema_changed": true',
    '"rn_visible_contract_changed": true',
    '"public_response_top_level_key_added": true',
    '"release_allowed": true',
    '"p7_complete": true',
    '"p8_start_allowed": true',
    '"p6_limited_human_readfeel_start_allowed": true',
    '"question_trigger_logic_implemented": true',
    '"question_api_implemented": true',
    '"question_db_schema_implemented": true',
    '"question_rn_ui_implemented": true',
    '"question_response_key_implemented": true',
    '"question_storage_schema_implemented": true',
    '"question_answer_persistence_implemented": true',
    '"question_plan_guard_implemented": true',
    '"question_implementation_started_here": true',
    '"question_text_materialized_here": true',
    '"draft_question_text_materialized_here": true',
    '"p8_question_implementation_spec_finalized_here": true',
    '"actual_human_review_run_here": true',
    '"actual_manual_review_run_here": true',
    '"body_full_packet_generated_here": true',
    '"p5_human_blind_qa_confirmed_final": true',
    '"full_backend_suite_green_claimed": true',
    '"real_device_modal_verified_claimed": true',
    '"actual_human_review_complete_claimed_by_helper": true',
    '"p5_final_confirmation_claimed_from_validation_matrix": true',
    '"release_claimed_from_validation_matrix": true',
    '"command_result_body_stored_here": true',
    '"terminal_output_stored_here": true',
    '"command_string_included": true',
    '"existing_op24_reused_as_actual_documentation_output_basis": true',
)


def _assert_bodyfree(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for token in FORBIDDEN_DUMP_TOKENS:
        assert token not in dumped
    for token in FORBIDDEN_TRUE_TOKENS:
        assert token not in dumped


def _ev21_ready() -> dict[str, object]:
    return prev21._ev21_ready()


def _validation_rows() -> list[dict[str, object]]:
    return [
        {
            "command_ref": "r54_ev22_target",
            "command_group_ref": "r54_ev22_validation",
            "command_kind_ref": "pytest_target",
            "result_status_ref": ev.P7_R54_EV22_COMMAND_RESULT_PASSED_REF,
            "result_scope_ref": "ev22_target_green",
            "passed_count": 1,
            "result_summary_ref": "ev22_target_passed_bodyfree_summary",
        },
        {
            "command_ref": "backend_compileall",
            "command_group_ref": "r54_ev22_validation",
            "command_kind_ref": "compileall",
            "result_status_ref": ev.P7_R54_EV22_COMMAND_RESULT_PASSED_REF,
            "result_scope_ref": "compileall_syntax_import_only_not_runtime_readfeel",
            "passed_count": 1,
            "result_summary_ref": "compileall_passed_bodyfree_summary",
        },
        {
            "command_ref": "backend_collect_only",
            "command_group_ref": "r54_ev22_validation",
            "command_kind_ref": "pytest_collect_only",
            "result_status_ref": ev.P7_R54_EV22_COMMAND_RESULT_COLLECTED_ONLY_REF,
            "result_scope_ref": "backend_collect_only_not_full_suite",
            "collected_count": 6384,
            "warning_count": 1,
            "result_summary_ref": "collect_only_completed_not_full_suite_green_bodyfree_summary",
        },
        {
            "command_ref": "real_device_modal_check",
            "command_group_ref": "r54_ev22_validation",
            "command_kind_ref": "manual_scope",
            "result_status_ref": ev.P7_R54_EV22_COMMAND_RESULT_NOT_EXECUTED_REF,
            "result_scope_ref": "real_device_modal_not_executed",
            "result_summary_ref": "not_executed_bodyfree_summary",
        },
    ]


def _ev22_ready(rows: list[dict[str, object]] | None = None) -> dict[str, object]:
    material = ev.build_p7_r54_ev22_validation_command_matrix_documentation_output(
        r52_reintake_handoff=_ev21_ready(),
        validation_command_rows=rows or _validation_rows(),
    )
    assert ev.assert_p7_r54_ev22_validation_command_matrix_documentation_output_contract(material) is True
    return material


def test_r54_ev22_validation_command_row_is_bodyfree_and_does_not_store_command_or_terminal_output() -> None:
    row = ev.build_p7_r54_ev22_validation_command_matrix_row(
        command_ref="backend_collect_only",
        command_kind_ref="pytest_collect_only",
        result_status_ref=ev.P7_R54_EV22_COMMAND_RESULT_COLLECTED_ONLY_REF,
        result_scope_ref="backend_collect_only_not_full_suite",
        collected_count=6384,
        warning_count=1,
    )
    assert row["schema_version"] == ev.P7_R54_EV22_VALIDATION_COMMAND_MATRIX_ROW_SCHEMA_VERSION
    assert set(row) == set(ev.P7_R54_EV22_VALIDATION_COMMAND_MATRIX_ROW_REQUIRED_FIELD_REFS)
    assert row["green_claim_allowed"] is False
    assert row["collection_only_claim_allowed"] is True
    for key in (
        "full_suite_claim_allowed",
        "real_device_claim_allowed",
        "actual_human_review_claim_allowed",
        "command_result_body_stored_here",
        "terminal_output_stored_here",
        "command_string_included",
        "raw_body_included",
        "question_text_included",
        "draft_question_text_included",
        "local_path_included",
    ):
        assert row[key] is False
    assert ev.assert_p7_r54_ev22_validation_command_matrix_row_contract(row) is True
    _assert_bodyfree(row)


def test_r54_ev22_documentation_output_ready_records_matrix_but_does_not_promote_claims() -> None:
    material = _ev22_ready()
    assert material["schema_version"] == ev.P7_R54_EV22_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION
    assert set(material) == set(ev.P7_R54_EV22_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS)
    assert material["documentation_output_status"] == ev.P7_R54_EV22_DOCUMENTATION_OUTPUT_READY_STATUS_REF
    assert material["documentation_output_ref"] == ev.P7_R54_EV22_DOCUMENTATION_OUTPUT_REF
    assert material["validation_command_row_count"] == 4
    assert material["executed_validation_command_count"] == 3
    assert material["passed_validation_command_count"] == 2
    assert material["collected_only_validation_command_count"] == 1
    assert material["failed_validation_command_count"] == 0
    assert material["not_executed_validation_command_count"] == 1
    assert material["green_claim_scope_count"] == 2
    assert material["collection_only_scope_count"] == 1
    assert material["blocked_green_claim_count"] == 0
    assert material["actual_review_evidence_complete"] is True
    assert material["r52_reintake_handoff_ready"] is True
    assert material["p5_human_blind_qa_confirmed_candidate"] is True
    for key in (
        "p5_human_blind_qa_confirmed_final",
        "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed",
        "release_allowed",
        "p7_complete",
        "collect_only_claimed_as_full_suite_green",
        "rn_contract_claimed_as_real_device_modal_verified",
        "r54_helper_green_claimed_as_actual_human_review_complete",
        "full_backend_suite_green_claimed",
        "real_device_modal_verified_claimed",
        "actual_human_review_complete_claimed_by_helper",
        "release_claimed_from_validation_matrix",
    ):
        assert material[key] is False
    assert material["existing_op24_operation_current_refs"] == r54op.P7_R54_OPERATION_CURRENT_REFS
    assert material["existing_op24_current_refs_are_historical_here"] is True
    assert material["existing_op24_reused_as_actual_documentation_output_basis"] is False
    assert material["existing_op24_structural_contract_reused"] is True
    assert tuple(material["implemented_steps"]) == ev.P7_R54_EV22_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ev.P7_R54_EV22_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ev.P7_R54_EV_NEXT_WORK_AFTER_EV22_REF
    _assert_bodyfree(material)


def test_r54_ev22_ready_allows_collect_only_scope_only_as_collection_not_full_suite_green() -> None:
    material = _ev22_ready()
    assert material["collection_only_scope_refs"] == [
        "backend_collect_only__backend_collect_only_not_full_suite__collection_only_not_full_suite"
    ]
    assert all("full_suite_green" not in ref for ref in material["green_claim_scope_refs"])
    assert material["full_backend_suite_green_claimed"] is False


def test_r54_ev22_missing_matrix_blocks_without_exposing_evidence_complete() -> None:
    material = ev.build_p7_r54_ev22_validation_command_matrix_documentation_output(
        r52_reintake_handoff=_ev21_ready(),
        validation_command_rows=[],
    )
    assert material["documentation_output_status"] == ev.P7_R54_EV22_DOCUMENTATION_OUTPUT_BLOCKED_BY_COMMAND_MATRIX_STATUS_REF
    assert material["actual_review_evidence_complete"] is False
    assert material["r52_reintake_handoff_ready"] is False
    assert material["open_execution_blocker_ids"] == [ev.P7_R54_EV22_COMMAND_MATRIX_MISSING_REASON_REF]
    assert material["next_required_step"] == ev.P7_R54_EV22_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert ev.assert_p7_r54_ev22_validation_command_matrix_documentation_output_contract(material) is True
    _assert_bodyfree(material)


def test_r54_ev22_failed_command_blocks_documentation_output() -> None:
    rows = _validation_rows()
    rows[0] = dict(rows[0])
    rows[0]["result_status_ref"] = ev.P7_R54_EV22_COMMAND_RESULT_FAILED_REF
    rows[0]["failure_count"] = 1
    material = ev.build_p7_r54_ev22_validation_command_matrix_documentation_output(
        r52_reintake_handoff=_ev21_ready(),
        validation_command_rows=rows,
    )
    assert material["documentation_output_status"] == ev.P7_R54_EV22_DOCUMENTATION_OUTPUT_BLOCKED_BY_COMMAND_MATRIX_STATUS_REF
    assert material["failed_validation_command_count"] == 1
    assert ev.P7_R54_EV22_COMMAND_MATRIX_FAILED_REASON_REF in material["open_execution_blocker_ids"]
    assert "r54_ev22_target" in material["open_execution_blocker_ids"]
    assert material["actual_review_evidence_complete"] is False
    assert ev.assert_p7_r54_ev22_validation_command_matrix_documentation_output_contract(material) is True
    _assert_bodyfree(material)


def test_r54_ev22_blocks_green_claim_overreach() -> None:
    material = ev.build_p7_r54_ev22_validation_command_matrix_documentation_output(
        r52_reintake_handoff=_ev21_ready(),
        validation_command_rows=_validation_rows(),
        green_claim_scope_refs=["full_backend_suite_green"],
    )
    assert material["documentation_output_status"] == ev.P7_R54_EV22_DOCUMENTATION_OUTPUT_BLOCKED_BY_CLAIM_OVERREACH_STATUS_REF
    assert material["blocked_green_claim_refs"] == ["full_backend_suite_green"]
    assert ev.P7_R54_EV22_GREEN_CLAIM_OVERREACH_REASON_REF in material["open_execution_blocker_ids"]
    assert material["actual_review_evidence_complete"] is False
    assert ev.assert_p7_r54_ev22_validation_command_matrix_documentation_output_contract(material) is True
    _assert_bodyfree(material)


def test_r54_ev22_blocks_when_ev21_handoff_not_ready() -> None:
    ev21 = deepcopy(_ev21_ready())
    ev21["handoff_status"] = ev.P7_R54_EV21_R52_REINTAKE_BLOCKED_BY_INCONCLUSIVE_STATUS_REF
    ev21["r52_reintake_handoff_status"] = ev.P7_R54_EV21_R52_REINTAKE_BLOCKED_BY_INCONCLUSIVE_STATUS_REF
    ev21["actual_review_evidence_complete"] = False
    ev21["r52_reintake_handoff_ready"] = False
    ev21["body_free_evidence_handoff_materialized_here"] = False
    ev21["r52_reintake_required"] = False
    ev21["open_execution_blocker_ids"] = ["ev21_inconclusive_fixture"]
    ev21["execution_blocker_ids"] = ["ev21_inconclusive_fixture"]
    ev21["handoff_reason_refs"] = ["ev21_inconclusive_fixture"]
    ev21["r52_reintake_handoff_reason_refs"] = ["ev21_inconclusive_fixture"]
    ev21["handoff_evidence_refs"] = []
    ev21["handoff_evidence_ref_count"] = 0
    ev21["next_required_step"] = ev.P7_R54_EV21_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF
    assert ev.assert_p7_r54_ev21_r52_reintake_handoff_contract(ev21) is True

    material = ev.build_p7_r54_ev22_validation_command_matrix_documentation_output(
        r52_reintake_handoff=ev21,
        validation_command_rows=_validation_rows(),
    )
    assert material["documentation_output_status"] == ev.P7_R54_EV22_DOCUMENTATION_OUTPUT_BLOCKED_BY_EV21_STATUS_REF
    assert ev.P7_R54_EV22_BLOCKED_BY_EV21_REASON_REF in material["open_execution_blocker_ids"]
    assert "ev21_inconclusive_fixture" in material["open_execution_blocker_ids"]
    assert material["actual_review_evidence_complete"] is False
    assert ev.assert_p7_r54_ev22_validation_command_matrix_documentation_output_contract(material) is True
    _assert_bodyfree(material)
