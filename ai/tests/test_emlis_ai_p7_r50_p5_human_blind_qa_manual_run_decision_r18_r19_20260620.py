# -*- coding: utf-8 -*-
"""R50-18/R50-19 tests for P5 human Blind QA manual-run decision.

These tests stop at body-free no-leak guard and validation command matrix.
They do not execute validation commands, do not store terminal output, do not
write files, do not generate body-full packets, do not run human review, and do
not touch API/DB/RN/release contracts.
"""

from __future__ import annotations

import copy

import pytest

import emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision as r50


_BODY_LEAK_KEY_REFS = (
    "raw_input",
    "raw_answer",
    "comment_text",
    "comment_text_body",
    "returned_emlis_surface",
    "bounded_owned_history_review_surface",
    "current_input_review_surface",
    "reviewer_free_text",
    "reviewer_note",
    "reviewer_notes",
    "question_text",
    "draft_question_text",
    "question_body",
    "local_absolute_path",
    "body_content_hash",
    "packet_content_hash",
    "terminal_output",
    "stdout",
    "stderr",
    "traceback",
)

_ALWAYS_FALSE_REFS = (
    "p7_complete",
    "p8_start_allowed",
    "release_allowed",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
)


def _walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _walk_keys(child)


def _assert_no_forbidden_body_keys(value):
    keys = set(_walk_keys(value))
    assert not (keys & set(_BODY_LEAK_KEY_REFS))


def _assert_closed_flags(material):
    for key in _ALWAYS_FALSE_REFS:
        if key in material:
            assert material[key] is False
    assert material["body_free"] is True
    _assert_no_forbidden_body_keys(material)


def test_r50_18_no_body_leak_guard_is_ready_without_copying_scanned_material():
    guard = r50.build_p7_r50_no_body_leak_no_question_text_guard_bodyfree()

    assert guard["schema_version"] == r50.P7_R50_NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_BODYFREE_SCHEMA_VERSION
    assert guard["guard_status"] == "NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_READY"
    assert guard["source_material_contract_checked"] is True
    assert guard["source_material_embedded_here"] is False
    assert guard["forbidden_field_refs_detected"] == []
    assert guard["forbidden_true_flag_refs_detected"] == []
    assert guard["no_body_leak_guard_passed"] is True
    assert guard["no_question_text_guard_passed"] is True
    assert guard["next_required_step"] == r50.P7_R50_R18_NEXT_REQUIRED_STEP_REF
    assert tuple(guard["implemented_steps"]) == r50.P7_R50_R18_IMPLEMENTED_STEPS
    assert tuple(guard["not_yet_implemented_steps"]) == r50.P7_R50_R18_NOT_YET_IMPLEMENTED_STEPS
    _assert_closed_flags(guard)


def test_r50_18_blocks_question_text_without_echoing_the_leaky_source():
    source = r50.build_p7_r50_r16_r17_p6_p8_candidate_handoff_freeze()
    leaky_source = copy.deepcopy(source)
    leaky_source["question_text"] = "これはbody-free成果物へ残してはいけない質問本文"

    guard = r50.build_p7_r50_no_body_leak_no_question_text_guard_bodyfree(
        source_material_bodyfree=leaky_source
    )

    assert guard["guard_status"] == "BLOCKED_BY_BODY_FREE_LEAK_OR_QUESTION_TEXT"
    assert guard["source_material_embedded_here"] is False
    assert guard["source_material_contract_checked"] is False
    assert "question_text" not in guard
    assert "question_text" in guard["forbidden_field_refs_detected"]
    assert guard["question_text_or_draft_question_text_detected"] is True
    assert guard["no_body_leak_guard_passed"] is False
    assert guard["no_question_text_guard_passed"] is False
    assert guard["next_required_step"] == r50.P7_R50_R18_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_closed_flags(guard)


def test_r50_18_blocks_question_flag_or_reviewer_free_text_flag_drift():
    source = r50.build_p7_r50_r16_r17_p6_p8_candidate_handoff_freeze()
    drift = copy.deepcopy(source)
    drift["draft_question_text_included"] = True
    drift["reviewer_free_text_included"] = True

    guard = r50.build_p7_r50_no_body_leak_no_question_text_guard_bodyfree(
        source_material_bodyfree=drift
    )

    assert guard["guard_status"] == "BLOCKED_BY_BODY_FREE_LEAK_OR_QUESTION_TEXT"
    assert "draft_question_text_included" in guard["forbidden_true_flag_refs_detected"]
    assert "reviewer_free_text_included" in guard["forbidden_true_flag_refs_detected"]
    assert guard["question_text_or_draft_question_text_detected"] is True
    assert guard["reviewer_free_text_detected"] is True
    _assert_closed_flags(guard)


def test_r50_18_contract_rejects_ready_guard_with_detected_body_or_embedded_source():
    guard = r50.build_p7_r50_no_body_leak_no_question_text_guard_bodyfree()

    drift = copy.deepcopy(guard)
    drift["forbidden_field_refs_detected"] = ["question_text"]
    drift["forbidden_field_detected_count"] = 1
    with pytest.raises(ValueError):
        r50.assert_p7_r50_no_body_leak_no_question_text_guard_bodyfree_contract(drift)

    drift = copy.deepcopy(guard)
    drift["source_material_embedded_here"] = True
    with pytest.raises(ValueError):
        r50.assert_p7_r50_no_body_leak_no_question_text_guard_bodyfree_contract(drift)


# ---------------------------------------------------------------------------
# R50-19 validation command matrix
# ---------------------------------------------------------------------------


def test_r50_19_validation_command_matrix_separates_target_regression_collect_only_and_rn_optional():
    matrix = r50.build_p7_r50_validation_command_matrix_bodyfree()

    assert matrix["schema_version"] == r50.P7_R50_VALIDATION_COMMAND_MATRIX_BODYFREE_SCHEMA_VERSION
    assert matrix["validation_matrix_status"] == "VALIDATION_COMMAND_MATRIX_READY"
    assert matrix["guard_status"] == "NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_READY"
    assert matrix["validation_command_group_refs"] == list(r50.P7_R50_VALIDATION_COMMAND_GROUP_REFS)
    assert matrix["required_validation_group_refs"] == list(r50.P7_R50_VALIDATION_COMMAND_REQUIRED_GROUP_REFS)
    assert matrix["optional_validation_group_refs"] == list(r50.P7_R50_VALIDATION_COMMAND_OPTIONAL_GROUP_REFS)
    assert matrix["validation_command_row_count"] == len(r50.P7_R50_VALIDATION_COMMAND_GROUP_REFS)
    assert "tests/test_emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision_r18_r19_20260620.py" in matrix["r50_target_test_file_refs"]
    assert matrix["validation_commands_reference_only"] is True
    assert matrix["validation_commands_executed_here"] is False
    assert matrix["terminal_output_stored_here"] is False
    assert matrix["full_backend_suite_green_confirmed"] is False
    assert matrix["collect_only_claimed_as_full_backend_green"] is False
    assert matrix["rn_contract_claimed_as_real_device_modal_readfeel"] is False
    assert matrix["r50_target_green_claimed_as_p5_product_quality_pass"] is False
    assert matrix["next_required_step"] == r50.P7_R50_R19_NEXT_REQUIRED_STEP_REF

    rows_by_group = {row["validation_group_ref"]: row for row in matrix["validation_command_rows"]}
    assert rows_by_group["backend_collect_only"]["claim_boundary_ref"] == "collect-only is not full backend suite execution green"
    assert rows_by_group["backend_collect_only"]["required_for_r50_validation"] is True
    assert rows_by_group["backend_collect_only"]["optional"] is False
    assert rows_by_group["rn_no_touch_optional"]["optional"] is True
    for row in matrix["validation_command_rows"]:
        assert row["command_executed_here"] is False
        assert row["command_result_body_stored_here"] is False
        assert row["terminal_output_stored_here"] is False
        assert row["body_free"] is True
    _assert_closed_flags(matrix)


def test_r50_19_blocks_matrix_when_r18_guard_is_blocked_but_does_not_execute_commands():
    source = r50.build_p7_r50_r16_r17_p6_p8_candidate_handoff_freeze()
    leaky_source = copy.deepcopy(source)
    leaky_source["local_absolute_path"] = "/tmp/cocolon-local-only/body_full_packet.json"
    guard = r50.build_p7_r50_no_body_leak_no_question_text_guard_bodyfree(
        source_material_bodyfree=leaky_source
    )
    matrix = r50.build_p7_r50_validation_command_matrix_bodyfree(
        no_body_leak_no_question_text_guard_bodyfree=guard
    )

    assert guard["guard_status"] == "BLOCKED_BY_BODY_FREE_LEAK_OR_QUESTION_TEXT"
    assert matrix["validation_matrix_status"] == "BLOCKED_BY_R50_18_NO_BODY_LEAK_GUARD"
    assert matrix["next_required_step"] == r50.P7_R50_R19_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert matrix["validation_commands_executed_here"] is False
    assert matrix["terminal_output_stored_here"] is False
    _assert_closed_flags(matrix)


def test_r50_19_contract_rejects_collect_only_or_rn_overclaim():
    matrix = r50.build_p7_r50_validation_command_matrix_bodyfree()

    drift = copy.deepcopy(matrix)
    drift["collect_only_claimed_as_full_backend_green"] = True
    with pytest.raises(ValueError):
        r50.assert_p7_r50_validation_command_matrix_bodyfree_contract(drift)

    drift = copy.deepcopy(matrix)
    drift["rn_contract_claimed_as_real_device_modal_readfeel"] = True
    with pytest.raises(ValueError):
        r50.assert_p7_r50_validation_command_matrix_bodyfree_contract(drift)

    drift = copy.deepcopy(matrix)
    drift["validation_command_rows"][0]["terminal_output_stored_here"] = True
    with pytest.raises(ValueError):
        r50.assert_p7_r50_validation_command_matrix_bodyfree_contract(drift)


def test_r50_r18_r19_freeze_keeps_no_leak_guard_and_validation_matrix_separate_from_p7_p8_release():
    freeze = r50.build_p7_r50_r18_r19_no_leak_validation_matrix_freeze()

    assert freeze["schema_version"] == r50.P7_R50_R18_R19_NO_LEAK_VALIDATION_MATRIX_FREEZE_SCHEMA_VERSION
    assert freeze["guard_status"] == "NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_READY"
    assert freeze["validation_matrix_status"] == "VALIDATION_COMMAND_MATRIX_READY"
    assert tuple(freeze["implemented_steps"]) == r50.P7_R50_R19_IMPLEMENTED_STEPS
    assert tuple(freeze["not_yet_implemented_steps"]) == r50.P7_R50_R19_NOT_YET_IMPLEMENTED_STEPS
    assert freeze["next_required_step"] == r50.P7_R50_R19_NEXT_REQUIRED_STEP_REF
    assert freeze["p7_complete"] is False
    assert freeze["p8_start_allowed"] is False
    assert freeze["release_allowed"] is False
    assert freeze["actual_manual_review_run_here"] is False
    assert freeze["body_full_packet_generated_here"] is False
    _assert_closed_flags(freeze)


def test_r50_r18_r19_new_exports_are_available_via_star_import():
    namespace: dict[str, object] = {}
    exec("from emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision import *", namespace)

    assert "build_p7_r50_no_body_leak_no_question_text_guard_bodyfree" in namespace
    assert "build_p7_r50_validation_command_matrix_bodyfree" in namespace
    assert "build_p7_r50_r18_r19_no_leak_validation_matrix_freeze" in namespace
    assert "assert_p7_r50_validation_command_matrix_bodyfree_contract" in namespace
