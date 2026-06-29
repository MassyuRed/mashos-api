# -*- coding: utf-8 -*-
from __future__ import annotations

import pytest

import emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution as r49

SECRET_INPUT = "R49 R16 raw input leak must not enter body-free material"
SECRET_REVIEWER = "R49 R16 reviewer free text leak must not enter body-free material"
SECRET_QUESTION = "R49 R16 question text leak must not enter body-free material"


def _compact_r14_r15_reference(**extra: object) -> dict[str, object]:
    material: dict[str, object] = {
        "schema_version": r49.P7_R49_R14_R15_P6_P8_CANDIDATE_HANDOFF_FREEZE_SCHEMA_VERSION,
        "material_id": "test_r49_r14_r15_reference_bodyfree",
        "review_session_id": r49.P7_R49_DEFAULT_REVIEW_SESSION_ID,
        "p5_human_blind_qa_confirmed_candidate": False,
        "p6_limited_human_readfeel_start_allowed_candidate": False,
        "p8_question_design_material_candidate": False,
        "body_free": True,
        "body_removed": True,
        "reviewer_free_text_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
    }
    material.update(extra)
    return material


def test_r49_r16_builds_no_body_leak_no_question_text_guard_without_promotion() -> None:
    guard = r49.build_p7_r49_no_body_leak_no_question_text_guard(
        r49_r14_r15_p6_p8_candidate_handoff_freeze=_compact_r14_r15_reference()
    )
    assert r49.assert_p7_r49_no_body_leak_no_question_text_guard_contract(guard) is True

    assert guard["schema_version"] == r49.P7_R49_NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_SCHEMA_VERSION
    assert set(guard) == set(r49.P7_R49_NO_BODY_LEAK_NO_QUESTION_TEXT_GUARD_REQUIRED_FIELD_REFS)
    assert guard["policy_section"] == "R49-16_no_body_leak_no_question_text_guard"
    assert guard["body_free_material_guard_passed"] is True
    assert guard["no_body_leak_guard_passed"] is True
    assert guard["no_question_text_guard_passed"] is True
    assert guard["no_reviewer_free_text_guard_passed"] is True
    assert guard["forbidden_key_path_refs"] == []
    assert guard["forbidden_marker_true_path_refs"] == []
    assert tuple(guard["forbidden_field_refs"]) == r49.P7_R49_BODY_FREE_FORBIDDEN_FIELD_REFS
    assert tuple(guard["question_text_forbidden_field_refs"]) == r49.P7_R49_QUESTION_TEXT_FORBIDDEN_FIELD_REFS
    assert tuple(guard["guard_marker_false_key_refs"]) == r49.P7_R49_NO_BODY_LEAK_GUARD_MARKER_FALSE_KEY_REFS
    assert guard["question_text_included"] is False
    assert guard["draft_question_text_included"] is False
    assert guard["reviewer_free_text_included"] is False
    assert guard["raw_input_or_comment_text_included"] is False
    assert guard["returned_surface_included"] is False
    assert guard["local_path_or_body_hash_included"] is False
    assert guard["question_trigger_logic_implemented_here"] is False
    assert guard["api_db_rn_response_key_changed_here"] is False
    assert guard["p6_limited_human_readfeel_start_allowed"] is False
    assert guard["p8_detail_design_allowed_here"] is False
    assert guard["p8_start_allowed"] is False
    assert guard["release_allowed"] is False
    assert tuple(guard["implemented_steps"]) == r49.P7_R49_R16_IMPLEMENTED_STEPS
    assert tuple(guard["not_yet_implemented_steps"]) == r49.P7_R49_R16_NOT_YET_IMPLEMENTED_STEPS
    assert guard["next_required_step"] == r49.P7_R49_R16_NEXT_REQUIRED_STEP_REF
    assert "r49_r14_r15_p6_p8_candidate_handoff_freeze" not in guard


@pytest.mark.parametrize(
    "leaky_key,secret",
    [
        ("raw_input", SECRET_INPUT),
        ("reviewer_free_text", SECRET_REVIEWER),
        ("question_text", SECRET_QUESTION),
    ],
)
def test_r49_r16_rejects_body_reviewer_or_question_text_leak(leaky_key: str, secret: str) -> None:
    material = _compact_r14_r15_reference(leaky_nested_payload={leaky_key: secret})

    with pytest.raises(ValueError):
        r49.build_p7_r49_no_body_leak_no_question_text_guard(
            r49_r14_r15_p6_p8_candidate_handoff_freeze=material,
        )


def test_r49_r16_rejects_true_question_marker_even_without_question_body() -> None:
    with pytest.raises(ValueError):
        r49.build_p7_r49_no_body_leak_no_question_text_guard(
            r49_r14_r15_p6_p8_candidate_handoff_freeze=_compact_r14_r15_reference(question_text_included=True),
        )


def test_r49_r17_builds_validation_command_matrix_as_reference_only() -> None:
    guard = r49.build_p7_r49_no_body_leak_no_question_text_guard(
        r49_r14_r15_p6_p8_candidate_handoff_freeze=_compact_r14_r15_reference()
    )
    matrix = r49.build_p7_r49_validation_command_matrix(r49_no_body_leak_no_question_text_guard=guard)
    assert r49.assert_p7_r49_validation_command_matrix_contract(matrix) is True

    assert matrix["schema_version"] == r49.P7_R49_VALIDATION_COMMAND_MATRIX_SCHEMA_VERSION
    assert set(matrix) == set(r49.P7_R49_VALIDATION_COMMAND_MATRIX_REQUIRED_FIELD_REFS)
    assert matrix["policy_section"] == "R49-17_validation_command_matrix"
    assert matrix["validation_command_group_refs"] == list(r49.P7_R49_VALIDATION_COMMAND_GROUP_REFS)
    assert [row["command_group_ref"] for row in matrix["validation_command_matrix_rows"]] == list(
        r49.P7_R49_VALIDATION_COMMAND_GROUP_REFS
    )
    assert matrix["validation_command_count"] == len(r49.P7_R49_VALIDATION_COMMAND_GROUP_REFS)
    assert matrix["r49_target_test_file_refs"] == list(r49.P7_R49_VALIDATION_R49_TARGET_TEST_FILE_REFS)
    assert "tests/test_emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution_r16_r17_20260619.py" in matrix["r49_target_test_file_refs"]
    assert matrix["r48_regression_test_file_refs"] == list(r49.P7_R49_VALIDATION_R48_REGRESSION_TEST_FILE_REFS)
    assert matrix["r47_regression_test_file_refs"] == list(r49.P7_R49_VALIDATION_R47_REGRESSION_TEST_FILE_REFS)
    assert matrix["r46_handoff_regression_test_file_refs"] == list(r49.P7_R49_VALIDATION_R46_HANDOFF_TEST_FILE_REFS)
    assert matrix["validation_commands_reference_only"] is True
    assert matrix["validation_commands_executed_here"] is False
    assert matrix["command_output_stored_here"] is False
    assert matrix["terminal_output_stored_here"] is False
    assert matrix["full_backend_suite_execution_claimed_here"] is False
    assert matrix["collect_only_claimed_as_full_backend_green"] is False
    assert matrix["rn_contract_claimed_as_real_device_modal_readfeel"] is False
    assert matrix["release_readiness_claim_allowed"] is False
    assert matrix["p5_human_blind_qa_confirmed"] is False
    assert matrix["p6_limited_human_readfeel_start_allowed"] is False
    assert matrix["p8_start_allowed"] is False
    assert matrix["release_allowed"] is False
    assert "r49_no_body_leak_no_question_text_guard" not in matrix
    for row in matrix["validation_command_matrix_rows"]:
        assert row["commands_executed_here"] is False
        assert row["command_output_stored_here"] is False
        assert row["terminal_output_stored_here"] is False
        assert row["body_free"] is True
    assert tuple(matrix["implemented_steps"]) == r49.P7_R49_R17_IMPLEMENTED_STEPS
    assert tuple(matrix["not_yet_implemented_steps"]) == r49.P7_R49_R17_NOT_YET_IMPLEMENTED_STEPS
    assert matrix["next_required_step"] == r49.P7_R49_R17_NEXT_REQUIRED_STEP_REF


def test_r49_r17_contract_rejects_execution_or_release_claim() -> None:
    guard = r49.build_p7_r49_no_body_leak_no_question_text_guard(
        r49_r14_r15_p6_p8_candidate_handoff_freeze=_compact_r14_r15_reference()
    )
    matrix = r49.build_p7_r49_validation_command_matrix(r49_no_body_leak_no_question_text_guard=guard)
    matrix["validation_commands_executed_here"] = True

    with pytest.raises(ValueError):
        r49.assert_p7_r49_validation_command_matrix_contract(matrix)


def test_r49_r16_r17_freeze_combines_guard_and_matrix_without_claiming_execution() -> None:
    guard = r49.build_p7_r49_no_body_leak_no_question_text_guard(
        r49_r14_r15_p6_p8_candidate_handoff_freeze=_compact_r14_r15_reference()
    )
    matrix = r49.build_p7_r49_validation_command_matrix(r49_no_body_leak_no_question_text_guard=guard)
    freeze = r49.build_p7_r49_r16_r17_no_body_leak_validation_command_matrix_freeze(
        r49_no_body_leak_no_question_text_guard=guard,
        r49_validation_command_matrix=matrix,
    )
    assert r49.assert_p7_r49_r16_r17_no_body_leak_validation_command_matrix_freeze_contract(freeze) is True

    assert freeze["schema_version"] == r49.P7_R49_R16_R17_NO_BODY_LEAK_VALIDATION_COMMAND_MATRIX_FREEZE_SCHEMA_VERSION
    assert set(freeze) == set(r49.P7_R49_R16_R17_NO_BODY_LEAK_VALIDATION_COMMAND_MATRIX_FREEZE_REQUIRED_FIELD_REFS)
    assert freeze["policy_section"] == "R49-16_R49-17_no_body_leak_validation_command_matrix_freeze"
    assert freeze["r16_no_body_leak_no_question_text_guard_ref"] == guard["material_id"]
    assert freeze["r17_validation_command_matrix_ref"] == matrix["material_id"]
    assert freeze["body_free_material_guard_passed"] is True
    assert freeze["validation_command_matrix_built"] is True
    assert freeze["validation_commands_executed_here"] is False
    assert freeze["command_output_stored_here"] is False
    assert freeze["terminal_output_stored_here"] is False
    assert freeze["p6_limited_human_readfeel_start_allowed"] is False
    assert freeze["p6_limited_human_readfeel_confirmed"] is False
    assert freeze["p7_complete"] is False
    assert freeze["p8_start_allowed"] is False
    assert freeze["release_allowed"] is False
    assert "r16_no_body_leak_no_question_text_guard" not in freeze
    assert "r17_validation_command_matrix" not in freeze
    assert tuple(freeze["implemented_steps"]) == r49.P7_R49_R17_IMPLEMENTED_STEPS
    assert tuple(freeze["not_yet_implemented_steps"]) == r49.P7_R49_R17_NOT_YET_IMPLEMENTED_STEPS
    assert freeze["next_required_step"] == r49.P7_R49_R17_NEXT_REQUIRED_STEP_REF
