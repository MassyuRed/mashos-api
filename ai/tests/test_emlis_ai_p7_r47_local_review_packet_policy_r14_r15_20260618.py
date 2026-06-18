# -*- coding: utf-8 -*-
"""P7-R47 R14/R15 validation matrix and touch/no-touch boundary freeze."""

from __future__ import annotations

import json

import pytest

from emlis_ai_p7_r47_local_review_packet_policy import (
    P7_R47_DISPLAY_CONTRACT_REGRESSION_TEST_MODULE_REFS,
    P7_R47_R14_DESIGN_SINGLE_FILE_TARGET_REF,
    P7_R47_R14_R15_IMPLEMENTED_STEPS,
    P7_R47_R14_R15_NEXT_REQUIRED_STEP_REF,
    P7_R47_R14_R15_NOT_YET_IMPLEMENTED_STEPS,
    P7_R47_R14_R15_TARGET_TEST_MODULE_REFS,
    P7_R47_R14_R15_VALIDATION_TOUCH_BOUNDARY_SCHEMA_VERSION,
    P7_R47_R14_REQUIRED_VALIDATION_COMMAND_IDS,
    P7_R47_R14_VALIDATION_COMMAND_IDS,
    P7_R47_R15_ACTUAL_TOUCH_CANDIDATE_FILE_REFS,
    P7_R47_R15_DESIGN_TOUCH_CANDIDATE_FILE_REFS,
    P7_R47_R15_NO_TOUCH_FILE_REFS,
    P7_R47_R15_OPTIONAL_TOUCH_CANDIDATE_FILE_REFS,
    P7_R47_R46_REGRESSION_TEST_MODULE_REFS,
    P7_R47_TARGET_VALIDATION_COMMAND_MATRIX_SCHEMA_VERSION,
    P7_R47_TOUCH_NO_TOUCH_BOUNDARY_SCHEMA_VERSION,
    assert_p7_r47_r14_r15_validation_touch_boundary_freeze_contract,
    assert_p7_r47_target_validation_command_matrix_contract,
    assert_p7_r47_touch_candidate_no_touch_boundary_contract,
    build_p7_r47_r14_r15_validation_touch_boundary_freeze,
    build_p7_r47_target_validation_command_matrix,
    build_p7_r47_touch_candidate_no_touch_boundary,
    p7_r47_touch_candidate_deny_reasons,
)

SECRET_INPUT = "R47 R14/R15 raw input must never enter body-free policy material"
SECRET_COMMENT = "R47 R14/R15 comment text body must remain local-only"
SECRET_SURFACE = "R47 R14/R15 reviewer surface must remain local-only"
SECRET_NOTE = "R47 R14/R15 reviewer note must remain local-only"


def _dumped(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _assert_no_body_or_release_promotion(value: object) -> None:
    dumped = _dumped(value)
    assert SECRET_INPUT not in dumped
    assert SECRET_COMMENT not in dumped
    assert SECRET_SURFACE not in dumped
    assert SECRET_NOTE not in dumped
    assert '"raw_input":' not in dumped
    assert '"comment_text":' not in dumped
    assert '"candidate_body":' not in dumped
    assert '"surface_body":' not in dumped
    assert '"surface_for_reviewer":' not in dumped
    assert '"reviewer_free_text":' not in dumped
    assert '"reviewer_notes":' not in dumped
    assert '"terminal_output":' not in dumped
    assert '"body_content_hash":' not in dumped
    assert '"release_allowed": true' not in dumped.lower()
    assert '"p7_complete": true' not in dumped.lower()
    assert '"p8_start_allowed": true' not in dumped.lower()
    assert '"hold004_close_allowed": true' not in dumped.lower()


def test_r47_r14_target_validation_command_matrix_freezes_required_optional_commands_without_green_claims() -> None:
    matrix = build_p7_r47_target_validation_command_matrix()
    assert_p7_r47_target_validation_command_matrix_contract(matrix)

    assert matrix["schema_version"] == P7_R47_TARGET_VALIDATION_COMMAND_MATRIX_SCHEMA_VERSION
    assert tuple(matrix["validation_command_ids"]) == P7_R47_R14_VALIDATION_COMMAND_IDS
    assert tuple(matrix["required_validation_command_ids"]) == P7_R47_R14_REQUIRED_VALIDATION_COMMAND_IDS
    assert tuple(matrix["r47_target_test_module_refs"]) == P7_R47_R14_R15_TARGET_TEST_MODULE_REFS
    assert matrix["r47_target_test_module_refs"][-1] == (
        "tests/test_emlis_ai_p7_r47_local_review_packet_policy_r14_r15_20260618.py"
    )
    assert tuple(matrix["r46_regression_test_module_refs"]) == P7_R47_R46_REGRESSION_TEST_MODULE_REFS
    assert tuple(matrix["display_contract_regression_test_module_refs"]) == P7_R47_DISPLAY_CONTRACT_REGRESSION_TEST_MODULE_REFS
    assert matrix["design_single_file_target_ref"] == P7_R47_R14_DESIGN_SINGLE_FILE_TARGET_REF
    assert matrix["design_single_file_materialized_in_this_snapshot"] is False

    rows = matrix["command_rows"]
    assert [row["command_id"] for row in rows] == list(P7_R47_R14_VALIDATION_COMMAND_IDS)
    assert rows[0]["command"] == (
        "PYTHONPATH=services/ai_inference python -m py_compile "
        "services/ai_inference/emlis_ai_p7_r47_local_review_packet_policy.py"
    )
    assert rows[1]["required_for_patch_zip"] is True
    assert rows[1]["optional"] is False
    assert rows[1]["target_refs"] == list(P7_R47_R14_R15_TARGET_TEST_MODULE_REFS)
    assert rows[-1]["command_id"] == "rn_contract_optional_no_touch_confirmation"
    assert rows[-1]["optional"] is True
    assert rows[-1]["required_for_patch_zip"] is False

    for row in rows:
        assert row["claims_execution_green_here"] is False
        assert row["body_free"] is True

    assert matrix["r47_policy_ready"] is True
    assert matrix["p5_human_blind_qa_start_allowed_after_policy"] is True
    assert matrix["p5_human_blind_qa_confirmed"] is False
    assert matrix["p6_limited_human_readfeel_start_allowed"] is False
    assert matrix["real_device_modal_review_start_allowed"] is False
    assert matrix["actual_validation_execution_claimed_here"] is False
    assert matrix["actual_contract_test_execution_claimed_here"] is False
    assert matrix["full_backend_suite_execution_green_confirmed"] is False
    assert matrix["release_allowed"] is False
    assert matrix["p7_complete"] is False
    assert matrix["p8_start_allowed"] is False
    assert matrix["hold004_close_allowed"] is False
    assert matrix["next_required_step"] == "R15_touch_candidate_and_no_touch_boundary"
    _assert_no_body_or_release_promotion(matrix)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("raw_input", SECRET_INPUT),
        ("comment_text", SECRET_COMMENT),
        ("surface_for_reviewer", SECRET_SURFACE),
        ("reviewer_free_text", SECRET_NOTE),
        ("terminal_output", "terminal output must not enter R14"),
        ("body_content_hash", "hash-of-body-must-not-enter-r14"),
        ("release_allowed", True),
        ("p7_complete", True),
        ("p8_start_allowed", True),
        ("hold004_close_allowed", True),
        ("p5_human_blind_qa_confirmed", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("real_device_modal_review_start_allowed", True),
        ("actual_validation_execution_claimed_here", True),
        ("actual_contract_test_execution_claimed_here", True),
        ("full_backend_suite_green_claimed_here", True),
    ],
)
def test_r47_r14_rejects_body_keys_release_review_or_execution_claims(key: str, value: object) -> None:
    matrix = build_p7_r47_target_validation_command_matrix()
    matrix[key] = value
    with pytest.raises(ValueError):
        assert_p7_r47_target_validation_command_matrix_contract(matrix)


def test_r47_r15_touch_boundary_freezes_candidates_and_explicit_no_touch_refs() -> None:
    boundary = build_p7_r47_touch_candidate_no_touch_boundary()
    assert_p7_r47_touch_candidate_no_touch_boundary_contract(boundary)

    assert boundary["schema_version"] == P7_R47_TOUCH_NO_TOUCH_BOUNDARY_SCHEMA_VERSION
    assert tuple(boundary["design_touch_candidate_file_refs"]) == P7_R47_R15_DESIGN_TOUCH_CANDIDATE_FILE_REFS
    assert tuple(boundary["actual_touch_candidate_file_refs"]) == P7_R47_R15_ACTUAL_TOUCH_CANDIDATE_FILE_REFS
    assert tuple(boundary["actual_touched_file_refs"]) == P7_R47_R15_ACTUAL_TOUCH_CANDIDATE_FILE_REFS
    assert tuple(boundary["optional_touch_candidate_file_refs"]) == P7_R47_R15_OPTIONAL_TOUCH_CANDIDATE_FILE_REFS
    assert tuple(boundary["no_touch_file_refs"]) == P7_R47_R15_NO_TOUCH_FILE_REFS
    assert boundary["denied_actual_touched_file_refs"] == {}

    assert p7_r47_touch_candidate_deny_reasons(
        "mashos-api/ai/services/ai_inference/emlis_ai_p7_r47_local_review_packet_policy.py"
    ) == ()
    assert p7_r47_touch_candidate_deny_reasons(
        "mashos-api/ai/tests/test_emlis_ai_p7_r47_local_review_packet_policy_r14_r15_20260618.py"
    ) == ()
    assert "r47_explicit_no_touch_file_ref" in p7_r47_touch_candidate_deny_reasons(
        "Cocolon/screens/InputScreen.js"
    )
    assert "r47_emlis_reply_runtime_no_touch_boundary" in p7_r47_touch_candidate_deny_reasons(
        "mashos-api/ai/services/ai_inference/emlis_ai_reply_service.py"
    )
    assert "r47_public_feedback_meta_no_touch_boundary" in p7_r47_touch_candidate_deny_reasons(
        "mashos-api/ai/services/ai_inference/emlis_ai_public_feedback_meta.py"
    )

    assert boundary["r47_manifest_module_touch_candidate_fixed_but_not_created_here"] is True
    assert boundary["r47_docs_touch_candidate_optional_but_not_created_here"] is True
    assert boundary["rn_production_files_touched_here"] is False
    assert boundary["rn_contract_test_touched_here"] is False
    assert boundary["emlis_reply_runtime_touched_here"] is False
    assert boundary["public_feedback_meta_runtime_touched_here"] is False
    assert boundary["public_source_lineage_runtime_touched_here"] is False
    assert boundary["db_schema_or_migration_touched_here"] is False
    assert boundary["api_route_or_public_response_shape_touched_here"] is False
    assert boundary["runtime_gate_threshold_touched_here"] is False
    assert boundary["rn_visible_contract_changed"] is False
    assert boundary["api_response_key_added"] is False
    assert boundary["db_schema_changed"] is False
    assert boundary["gate_relaxed"] is False
    assert boundary["actual_body_full_packet_generated_here"] is False
    assert boundary["actual_human_review_run_here"] is False
    assert boundary["actual_real_device_review_run_here"] is False
    assert boundary["next_required_step"] == P7_R47_R14_R15_NEXT_REQUIRED_STEP_REF
    _assert_no_body_or_release_promotion(boundary)


@pytest.mark.parametrize(
    "forbidden_ref",
    [
        "Cocolon/screens/InputScreen.js",
        "Cocolon/tests/rn-screen-contracts.test.js",
        "mashos-api/ai/services/ai_inference/emlis_ai_reply_service.py",
        "mashos-api/ai/services/ai_inference/emlis_ai_public_feedback_meta.py",
        "mashos-api/ai/services/ai_inference/emlis_ai_body_free_public_source_lineage.py",
        "mashos-api/ai/services/ai_inference/api_emotion_submit.py",
        "mashos-api/ai/docs/emlis_ai_user_models.sql",
        "mashos-api/ai/services/ai_inference/runtime_gate_thresholds.py",
    ],
)
def test_r47_r15_rejects_forbidden_actual_touch_refs(forbidden_ref: str) -> None:
    with pytest.raises(ValueError):
        build_p7_r47_touch_candidate_no_touch_boundary(
            actual_touched_file_refs=[
                "mashos-api/ai/services/ai_inference/emlis_ai_p7_r47_local_review_packet_policy.py",
                forbidden_ref,
            ]
        )


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("raw_input", SECRET_INPUT),
        ("comment_text", SECRET_COMMENT),
        ("surface_for_reviewer", SECRET_SURFACE),
        ("reviewer_free_text", SECRET_NOTE),
        ("terminal_output", "terminal output must not enter R15"),
        ("body_content_hash", "hash-of-body-must-not-enter-r15"),
        ("release_allowed", True),
        ("p7_complete", True),
        ("p8_start_allowed", True),
        ("hold004_close_allowed", True),
        ("rn_production_files_touched_here", True),
        ("rn_contract_test_touched_here", True),
        ("emlis_reply_runtime_touched_here", True),
        ("db_schema_or_migration_touched_here", True),
        ("api_route_or_public_response_shape_touched_here", True),
        ("runtime_gate_threshold_touched_here", True),
        ("rn_visible_contract_changed", True),
        ("api_response_key_added", True),
        ("db_schema_changed", True),
        ("gate_relaxed", True),
        ("p5_human_blind_qa_confirmed", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("real_device_modal_review_start_allowed", True),
    ],
)
def test_r47_r15_rejects_body_keys_no_touch_breaks_release_or_review_promotion(key: str, value: object) -> None:
    boundary = build_p7_r47_touch_candidate_no_touch_boundary()
    boundary[key] = value
    with pytest.raises(ValueError):
        assert_p7_r47_touch_candidate_no_touch_boundary_contract(boundary)


def test_r47_r14_r15_combined_freeze_completes_policy_sequence_and_points_next_to_p5_without_claiming_review_or_release() -> None:
    freeze = build_p7_r47_r14_r15_validation_touch_boundary_freeze()
    assert_p7_r47_r14_r15_validation_touch_boundary_freeze_contract(freeze)

    assert freeze["schema_version"] == P7_R47_R14_R15_VALIDATION_TOUCH_BOUNDARY_SCHEMA_VERSION
    assert tuple(freeze["implemented_steps"]) == P7_R47_R14_R15_IMPLEMENTED_STEPS
    assert freeze["implemented_steps"][-2:] == [
        "R14_target_validation_command_matrix",
        "R15_touch_candidate_and_no_touch_boundary",
    ]
    assert tuple(freeze["not_yet_implemented_steps"]) == P7_R47_R14_R15_NOT_YET_IMPLEMENTED_STEPS
    assert freeze["not_yet_implemented_steps"] == []
    assert freeze["target_validation_command_matrix_fixed"] is True
    assert freeze["touch_candidate_no_touch_boundary_fixed"] is True
    assert freeze["r47_policy_ready"] is True
    assert freeze["local_review_packet_policy_ready"] is True
    assert freeze["policy_ready"] is True
    assert freeze["p5_human_blind_qa_start_allowed_after_policy"] is True
    assert freeze["p5_human_blind_qa_start_allowed_after_r14_r15"] is True
    assert freeze["p5_human_blind_qa_confirmed"] is False
    assert freeze["p6_limited_human_readfeel_start_allowed"] is False
    assert freeze["real_device_modal_review_start_allowed"] is False
    assert freeze["real_device_modal_review_queued_after_p5_p6"] is True
    assert freeze["actual_validation_execution_claimed_here"] is False
    assert freeze["actual_contract_test_execution_claimed_here"] is False
    assert freeze["actual_human_review_run_here"] is False
    assert freeze["actual_real_device_review_run_here"] is False
    assert freeze["actual_body_full_packet_generated_here"] is False
    assert freeze["full_backend_suite_execution_green_confirmed"] is False
    assert freeze["release_allowed"] is False
    assert freeze["p7_complete"] is False
    assert freeze["p8_start_allowed"] is False
    assert freeze["hold004_close_allowed"] is False
    assert freeze["next_required_step"] == P7_R47_R14_R15_NEXT_REQUIRED_STEP_REF
    assert freeze["next_recommended_work_ref"] == "p5_human_blind_qa_material_generation_and_review"
    assert tuple(freeze["r47_target_test_module_refs"]) == P7_R47_R14_R15_TARGET_TEST_MODULE_REFS
    assert tuple(freeze["actual_touched_file_refs"]) == P7_R47_R15_ACTUAL_TOUCH_CANDIDATE_FILE_REFS
    _assert_no_body_or_release_promotion(freeze)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("raw_input", SECRET_INPUT),
        ("comment_text", SECRET_COMMENT),
        ("surface_for_reviewer", SECRET_SURFACE),
        ("reviewer_free_text", SECRET_NOTE),
        ("terminal_output", "terminal output must not enter combined R14/R15"),
        ("body_content_hash", "hash-of-body-must-not-enter-combined-r14-r15"),
        ("release_allowed", True),
        ("p7_complete", True),
        ("p8_start_allowed", True),
        ("hold004_close_allowed", True),
        ("p5_human_blind_qa_confirmed", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("real_device_modal_review_start_allowed", True),
        ("actual_human_review_run_here", True),
        ("actual_real_device_review_run_here", True),
        ("actual_contract_test_execution_claimed_here", True),
        ("actual_validation_execution_claimed_here", True),
        ("full_backend_suite_green_claimed_here", True),
    ],
)
def test_r47_r14_r15_combined_freeze_rejects_body_keys_release_review_or_execution_claims(key: str, value: object) -> None:
    freeze = build_p7_r47_r14_r15_validation_touch_boundary_freeze()
    freeze[key] = value
    with pytest.raises(ValueError):
        assert_p7_r47_r14_r15_validation_touch_boundary_freeze_contract(freeze)
