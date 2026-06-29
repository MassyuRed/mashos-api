# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r55_r54_evidence_reconcile_r52_reintake_decision_materialization as r55


FORBIDDEN_BODY_KEY_TOKENS = (
    '"raw_input":',
    '"comment_text":',
    '"returned_surface":',
    '"history_body":',
    '"reviewer_free_text":',
    '"reviewer_notes":',
    '"question_text":',
    '"draft_question_text":',
    '"local_absolute_path":',
    '"body_content_hash":',
    '"packet_content_hash":',
    '"terminal_output":',
    '"command_full_text":',
    '"command_full_output":',
    '"stdout":',
    '"stderr":',
    '"traceback":',
)
FORBIDDEN_TRUE_TOKENS = (
    '"actual_review_evidence_complete": true',
    '"actual_review_evidence_claimed": true',
    '"p5_human_blind_qa_confirmed": true',
    '"p5_human_blind_qa_confirmed_candidate": true',
    '"p5_human_blind_qa_confirmed_final": true',
    '"p5_repair_return_candidate": true',
    '"p6_limited_human_readfeel_candidate": true',
    '"p6_limited_human_readfeel_start_allowed": true',
    '"p8_question_design_material_candidate": true',
    '"p8_start_allowed": true',
    '"p7_complete": true',
    '"release_allowed": true',
    '"api_route_changed_here": true',
    '"db_schema_changed_here": true',
    '"db_migration_changed_here": true',
    '"rn_visible_contract_changed_here": true',
    '"public_response_top_level_key_added_here": true',
    '"public_response_key_changed_here": true',
    '"runtime_changed_here": true',
    '"question_api_implemented": true',
    '"question_db_schema_implemented": true',
    '"question_rn_ui_implemented": true',
    '"question_response_key_implemented": true',
    '"question_trigger_logic_implemented": true',
    '"question_storage_schema_implemented": true',
    '"question_answer_persistence_implemented": true',
    '"question_plan_guard_implemented": true',
    '"p8_question_implementation_spec_finalized_here": true',
    '"command_full_text_included": true',
    '"command_full_output_included": true',
    '"timeout_one_shot_claimed_as_green": true',
    '"collect_only_claimed_as_green": true',
    '"rn_contract_green_claimed_as_real_device_modal_readfeel": true',
    '"r55_target_green_claimed_as_actual_review_completion": true',
    '"r55_target_green_claimed_as_p8_start_allowed": true',
    '"r55_target_green_claimed_as_release_allowed": true',
    '"full_backend_suite_green_claimed_here": true',
    '"actual_review_execution_claimed_here": true',
    '"p5_actual_review_completion_claimed_here": true',
    '"p8_start_allowed_claimed_here": true',
    '"release_allowed_claimed_here": true',
)


def _assert_no_body_touch_or_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for token in FORBIDDEN_BODY_KEY_TOKENS:
        assert token not in dumped
    for token in FORBIDDEN_TRUE_TOKENS:
        assert token not in dumped


@lru_cache(maxsize=1)
def _cached_r7() -> tuple[dict[str, object]]:
    material = r55.build_p7_r55_p5_p6_p8_release_separation_bodyfree()
    assert r55.assert_p7_r55_p5_p6_p8_release_separation_bodyfree_contract(material) is True
    return (material,)


def _r7() -> dict[str, object]:
    return deepcopy(_cached_r7()[0])


@lru_cache(maxsize=1)
def _cached_r8() -> tuple[dict[str, object]]:
    material = r55.build_p7_r55_final_no_touch_boundary_validation_bodyfree(
        p5_p6_p8_release_separation=_r7(),
    )
    assert r55.assert_p7_r55_final_no_touch_boundary_validation_bodyfree_contract(material) is True
    return (material,)


def _r8() -> dict[str, object]:
    return deepcopy(_cached_r8()[0])


@lru_cache(maxsize=1)
def _cached_r9() -> tuple[dict[str, object]]:
    material = r55.build_p7_r55_validation_command_matrix_bodyfree(
        final_no_touch_boundary_validation=_r8(),
    )
    assert r55.assert_p7_r55_validation_command_matrix_bodyfree_contract(material) is True
    return (material,)


def _r9() -> dict[str, object]:
    return deepcopy(_cached_r9()[0])


def test_r55_r8_validates_final_no_touch_boundary_without_api_db_rn_runtime_or_question_touch() -> None:
    material = _r8()

    assert material["schema_version"] == r55.P7_R55_FINAL_NO_TOUCH_BOUNDARY_VALIDATION_SCHEMA_VERSION
    assert set(material) == set(r55.P7_R55_FINAL_NO_TOUCH_BOUNDARY_VALIDATION_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == r55.P7_R55_R8_STEP_REF
    assert material["source_mode"] == "local_snapshot"
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True
    assert material["current_received_snapshot_refs"] == r55.P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["actual_review_basis_ref"] == "R55_CURRENT_RECEIVED_SNAPSHOT_20260623"
    assert material["actual_review_basis_allowed"] == "current_received_snapshot_only"

    assert material["r7_p5_p6_p8_release_separation_schema_version"] == r55.P7_R55_P5_P6_P8_RELEASE_SEPARATION_SCHEMA_VERSION
    assert material["r55_decision_ref"] == r55.P7_R55_DEFAULT_R52_REINTAKE_DECISION_REF
    assert material["r52_existing_decision_equivalent"] == r55.P7_R55_DEFAULT_R52_EXISTING_DECISION_EQUIVALENT_REF
    assert material["decision_status"] == r55.P7_R55_DEFAULT_DECISION_STATUS_REF
    assert material["decision_next_required_step"] == r55.P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF
    assert material["next_required_step"] == r55.P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF
    assert material["r55_next_implementation_step_ref"] == r55.P7_R55_R8_NEXT_IMPLEMENTATION_STEP_REF

    assert material["no_touch_boundary_status_ref"] == r55.P7_R55_NO_TOUCH_BOUNDARY_VALIDATED_REF
    assert material["no_touch_touched_refs"] == []
    assert material["no_touch_touched_ref_count"] == 0
    assert material["no_touch_touched_refs_empty_ref"] == r55.P7_R55_NO_TOUCH_TOUCHED_REFS_EMPTY_REF
    assert material["question_implementation_status_ref"] == "P8_QUESTION_IMPLEMENTATION_NOT_STARTED_IN_R55"
    assert material["p8_hold_reason_ref"] == "P8_HOLD_BY_ACTUAL_REVIEW_EVIDENCE_MISSING_AND_P7_P8_BRIDGE"

    for false_key in r55.P7_R55_FINAL_NO_TOUCH_BOUNDARY_FLAG_REFS:
        assert material[false_key] is False
    for false_key in (
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "body_full_packet_generated_here",
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_review_evidence_complete",
        "actual_review_evidence_claimed",
        "p5_human_blind_qa_confirmed",
        "p5_human_blind_qa_confirmed_candidate",
        "p5_human_blind_qa_confirmed_final",
        "p6_limited_human_readfeel_start_allowed",
        "p8_question_design_material_candidate",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
        "json_schema_file_created_here",
        "schema_files_materialized_here",
        "body_full_packet_zip_inclusion_allowed",
    ):
        assert material[false_key] is False

    assert material["r55_0_scope_current_received_snapshot_refrozen"] is True
    assert material["r55_1_prior_helper_source_reconciled"] is True
    assert material["r55_2_validation_evidence_reconciled"] is True
    assert material["r55_3_r54_default_handoff_intake_done"] is True
    assert material["r55_4_bodyfree_forbidden_payload_scan_done"] is True
    assert material["r55_5_actual_review_evidence_gap_assessed"] is True
    assert material["r55_6_r52_reintake_decision_materialized"] is True
    assert material["r55_7_p5_p6_p8_release_separated"] is True
    assert material["r55_8_final_no_touch_boundary_validated"] is True
    assert material["r55_9_validation_command_matrix_documented"] is False
    assert tuple(material["implemented_steps"]) == r55.P7_R55_R8_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == r55.P7_R55_R8_NOT_YET_IMPLEMENTED_STEPS

    assert material["public_contract"] == {
        "api_response_key_added": False,
        "db_schema_changed": False,
        "public_release_applied": False,
        "rn_visible_contract_changed": False,
    }
    assert material["r55_public_no_touch_contract"] == {
        "api_route_changed_here": False,
        "db_migration_changed_here": False,
        "db_schema_changed_here": False,
        "gate_threshold_changed_here": False,
        "public_response_key_changed_here": False,
        "public_response_top_level_key_added_here": False,
        "question_implementation_changed_here": False,
        "release_material_changed_here": False,
        "rn_visible_contract_changed_here": False,
        "runtime_changed_here": False,
    }

    _assert_no_body_touch_or_promotion(material)


@pytest.mark.parametrize(
    "key",
    [
        *r55.P7_R55_FINAL_NO_TOUCH_BOUNDARY_FLAG_REFS,
        "question_implementation_started_here",
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "body_full_packet_generated_here",
        "actual_body_full_packet_generated_here",
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_review_evidence_complete",
        "actual_review_evidence_claimed",
        "p5_human_blind_qa_confirmed",
        "p5_human_blind_qa_confirmed_candidate",
        "p5_human_blind_qa_confirmed_final",
        "p6_limited_human_readfeel_start_allowed",
        "p8_question_design_material_candidate",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
        "json_schema_file_created_here",
        "schema_files_materialized_here",
        "raw_input_included",
        "returned_surface_included",
        "comment_text_included",
        "history_body_included",
        "reviewer_free_text_included",
        "question_text_included",
        "draft_question_text_included",
        "local_absolute_path_included",
        "terminal_output_included",
        "command_full_output_included",
    ],
)
def test_r55_r8_rejects_no_touch_or_bodyfree_false_field_true(key: str) -> None:
    material = _r8()
    material[key] = True
    with pytest.raises(ValueError):
        r55.assert_p7_r55_final_no_touch_boundary_validation_bodyfree_contract(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("r55_decision_ref", "R55_R52_P5_CONFIRMED_CANDIDATE_ONLY"),
        ("r52_existing_decision_equivalent", "R52_GO_P5_CONFIRMED_CANDIDATE_REVIEWED_BUT_NOT_RELEASE"),
        ("decision_status", "CANDIDATE_ONLY"),
        ("decision_next_required_step", "P8_question_design_start"),
        ("next_required_step", "P8_question_design_start"),
        ("r55_next_implementation_step_ref", "R55-10_final_summary"),
        ("no_touch_boundary_status_ref", "R55_NO_TOUCH_BOUNDARY_BYPASSED"),
        ("no_touch_touched_refs", ["api_route_changed_here"]),
        ("no_touch_touched_ref_count", 1),
        ("no_touch_touched_refs_empty_ref", "TOUCHED_REFS_PRESENT"),
        ("question_implementation_status_ref", "P8_QUESTION_IMPLEMENTATION_STARTED"),
        ("p8_hold_reason_ref", "P8_READY"),
        ("r55_8_final_no_touch_boundary_validated", False),
        ("r55_9_validation_command_matrix_documented", True),
        ("implemented_steps", r55.P7_R55_R9_IMPLEMENTED_STEPS),
        ("not_yet_implemented_steps", ("R55-10_final_summary",)),
    ],
)
def test_r55_r8_rejects_boundary_decision_or_step_rewrite(key: str, value: object) -> None:
    material = _r8()
    material[key] = value
    with pytest.raises(ValueError):
        r55.assert_p7_r55_final_no_touch_boundary_validation_bodyfree_contract(material)


def test_r55_r8_builder_rejects_promoted_or_rewritten_r7_input() -> None:
    r7 = _r7()
    r7["p8_start_allowed"] = True
    with pytest.raises(ValueError):
        r55.build_p7_r55_final_no_touch_boundary_validation_bodyfree(
            p5_p6_p8_release_separation=r7,
        )


def test_r55_r9_documents_validation_command_matrix_without_claiming_execution_or_product_progress() -> None:
    material = _r9()

    assert material["schema_version"] == r55.P7_R55_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION
    assert set(material) == set(r55.P7_R55_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == r55.P7_R55_R9_STEP_REF
    assert material["source_mode"] == "local_snapshot"
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True
    assert material["current_received_snapshot_refs"] == r55.P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["actual_review_basis_ref"] == "R55_CURRENT_RECEIVED_SNAPSHOT_20260623"
    assert material["actual_review_basis_allowed"] == "current_received_snapshot_only"

    assert material["r8_final_no_touch_boundary_validation_schema_version"] == r55.P7_R55_FINAL_NO_TOUCH_BOUNDARY_VALIDATION_SCHEMA_VERSION
    assert material["documentation_status_ref"] == r55.P7_R55_VALIDATION_COMMAND_MATRIX_DOCUMENTED_REF
    assert material["result_evidence_status_ref"] == r55.P7_R55_COMMAND_MATRIX_RESULT_EVIDENCE_STATUS_REF
    assert material["green_claim_rule_ref"] == r55.P7_R55_COMMAND_MATRIX_GREEN_CLAIM_RULE_REF

    rows = material["validation_command_rows"]
    assert isinstance(rows, list)
    assert material["validation_command_row_count"] == len(rows) == len(r55.P7_R55_COMMAND_MATRIX_GROUP_REFS)
    assert tuple(material["validation_command_group_refs"]) == r55.P7_R55_COMMAND_MATRIX_GROUP_REFS
    assert tuple(row["command_group_ref"] for row in rows) == r55.P7_R55_COMMAND_MATRIX_GROUP_REFS
    assert material["all_required_command_groups_documented"] is True
    assert tuple(row["command_ref"] for row in rows) == (
        "py_compile_r55_helper",
        "pytest_r55_r0_r1_r2_r3_target_split",
        "pytest_r55_r4_r5_r6_r7_target_split",
        "pytest_r55_r8_r9_target",
        "pytest_r54_result_handoff_regression_split",
        "pytest_r52_r53_targeted_regression",
        "npm_run_test_rn_screens_silent",
    )

    for false_key in r55.P7_R55_VALIDATION_COMMAND_MATRIX_FALSE_FIELD_REFS:
        assert material[false_key] is False
    for false_key in (
        "actual_review_evidence_complete",
        "actual_review_evidence_claimed",
        "p5_human_blind_qa_confirmed",
        "p5_human_blind_qa_confirmed_candidate",
        "p5_human_blind_qa_confirmed_final",
        "p6_limited_human_readfeel_start_allowed",
        "p8_question_design_material_candidate",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
        "question_api_implemented",
        "question_db_schema_implemented",
        "question_rn_ui_implemented",
        "question_response_key_implemented",
        "question_trigger_logic_implemented",
        "question_storage_schema_implemented",
        "question_answer_persistence_implemented",
        "question_plan_guard_implemented",
        "api_db_rn_response_key_changed_here",
        "runtime_changed_here",
        "api_route_changed_here",
        "db_schema_changed_here",
        "db_migration_changed_here",
        "rn_visible_contract_changed_here",
        "public_response_top_level_key_added_here",
        "public_response_key_changed_here",
        "gate_threshold_changed_here",
        "user_label_connection_runtime_changed_here",
        "emlis_runtime_changed_here",
    ):
        assert material[false_key] is False

    assert material["r55_0_scope_current_received_snapshot_refrozen"] is True
    assert material["r55_1_prior_helper_source_reconciled"] is True
    assert material["r55_2_validation_evidence_reconciled"] is True
    assert material["r55_3_r54_default_handoff_intake_done"] is True
    assert material["r55_4_bodyfree_forbidden_payload_scan_done"] is True
    assert material["r55_5_actual_review_evidence_gap_assessed"] is True
    assert material["r55_6_r52_reintake_decision_materialized"] is True
    assert material["r55_7_p5_p6_p8_release_separated"] is True
    assert material["r55_8_final_no_touch_boundary_validated"] is True
    assert material["r55_9_validation_command_matrix_documented"] is True
    assert tuple(material["implemented_steps"]) == r55.P7_R55_R9_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == r55.P7_R55_R9_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == r55.P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF
    assert material["r55_next_implementation_step_ref"] == r55.P7_R55_R9_NEXT_IMPLEMENTATION_STEP_REF

    _assert_no_body_touch_or_promotion(material)


def test_r55_r9_command_rows_are_bodyfree_refs_not_terminal_or_local_command_output() -> None:
    material = _r9()

    for row in material["validation_command_rows"]:
        assert set(row) == set(r55.P7_R55_VALIDATION_COMMAND_MATRIX_ROW_REQUIRED_FIELD_REFS)
        assert row["schema_version"] == r55.P7_R55_VALIDATION_COMMAND_MATRIX_ROW_SCHEMA_VERSION
        assert row["command_group_ref"] in r55.P7_R55_COMMAND_MATRIX_GROUP_REFS
        assert row["command_kind_ref"] in r55.P7_R55_COMMAND_MATRIX_KIND_REFS
        assert row["expected_claim_level_when_passed_ref"] in r55.P7_R55_COMMAND_MATRIX_REQUIRED_CLAIM_LEVEL_REFS
        assert row["result_evidence_status_ref"] == r55.P7_R55_COMMAND_MATRIX_RESULT_EVIDENCE_STATUS_REF
        assert row["target_file_refs"]
        assert row["target_file_ref_count"] == len(row["target_file_refs"])
        assert row["green_claim_allowed_if_passed"] is True
        assert row["body_free"] is True
        for false_key in (
            "command_full_text_included",
            "local_absolute_path_included",
            "terminal_output_included",
            "command_full_output_included",
            "timeout_one_shot_claimed_as_green",
            "collect_only_claimed_as_green",
            "rn_contract_green_claimed_as_real_device_modal_readfeel",
            "r55_target_green_claimed_as_actual_review_completion",
            "r55_target_green_claimed_as_p8_start_allowed",
            "r55_target_green_claimed_as_release_allowed",
            "actual_review_execution_claimed_here",
            "p8_start_allowed_claimed_here",
            "release_allowed_claimed_here",
        ):
            assert row[false_key] is False
        _assert_no_body_touch_or_promotion(row)


@pytest.mark.parametrize("key", r55.P7_R55_VALIDATION_COMMAND_MATRIX_FALSE_FIELD_REFS)
def test_r55_r9_rejects_command_matrix_false_field_true(key: str) -> None:
    material = _r9()
    material[key] = True
    with pytest.raises(ValueError):
        r55.assert_p7_r55_validation_command_matrix_bodyfree_contract(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("documentation_status_ref", "R55_VALIDATION_COMMAND_MATRIX_EXECUTED"),
        ("result_evidence_status_ref", "COMMAND_MATRIX_EXECUTED_AND_GREEN"),
        ("green_claim_rule_ref", "GREEN_MEANS_PRODUCT_READY"),
        ("validation_command_row_count", 0),
        ("validation_command_group_refs", ["r55_r8_r9_target"]),
        ("all_required_command_groups_documented", False),
        ("r55_8_final_no_touch_boundary_validated", False),
        ("r55_9_validation_command_matrix_documented", False),
        ("implemented_steps", r55.P7_R55_R8_IMPLEMENTED_STEPS),
        ("not_yet_implemented_steps", r55.P7_R55_R8_NOT_YET_IMPLEMENTED_STEPS),
        ("next_required_step", "P8_question_design_start"),
        ("r55_next_implementation_step_ref", "P8_question_design_start"),
    ],
)
def test_r55_r9_rejects_documentation_status_group_or_step_rewrite(key: str, value: object) -> None:
    material = _r9()
    material[key] = value
    with pytest.raises(ValueError):
        r55.assert_p7_r55_validation_command_matrix_bodyfree_contract(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("command_group_ref", "unknown_group"),
        ("command_kind_ref", "SHELL_FULL_COMMAND"),
        ("expected_claim_level_when_passed_ref", "FULL_BACKEND_GREEN"),
        ("result_evidence_status_ref", "COMMAND_ALREADY_GREEN"),
        ("target_file_refs", []),
        ("target_file_ref_count", 999),
        ("body_free", False),
        ("command_full_text_included", True),
        ("local_absolute_path_included", True),
        ("terminal_output_included", True),
        ("command_full_output_included", True),
        ("timeout_one_shot_claimed_as_green", True),
        ("collect_only_claimed_as_green", True),
        ("rn_contract_green_claimed_as_real_device_modal_readfeel", True),
        ("r55_target_green_claimed_as_actual_review_completion", True),
        ("r55_target_green_claimed_as_p8_start_allowed", True),
        ("r55_target_green_claimed_as_release_allowed", True),
        ("actual_review_execution_claimed_here", True),
        ("p8_start_allowed_claimed_here", True),
        ("release_allowed_claimed_here", True),
    ],
)
def test_r55_r9_rejects_command_row_body_or_green_claim_rewrite(key: str, value: object) -> None:
    row = deepcopy(_r9()["validation_command_rows"][0])
    row[key] = value
    with pytest.raises(ValueError):
        r55.assert_p7_r55_validation_command_matrix_row_bodyfree_contract(row)


@pytest.mark.parametrize(
    "forbidden_key",
    [
        "raw_input",
        "comment_text",
        "returned_surface",
        "history_body",
        "reviewer_free_text",
        "question_text",
        "draft_question_text",
        "local_absolute_path",
        "body_content_hash",
        "packet_content_hash",
        "terminal_output",
        "command_full_output",
    ],
)
def test_r55_r8_r9_reject_forbidden_payload_keys(forbidden_key: str) -> None:
    r8 = _r8()
    r8[forbidden_key] = "forbidden"
    with pytest.raises(ValueError):
        r55.assert_p7_r55_final_no_touch_boundary_validation_bodyfree_contract(r8)

    r9 = _r9()
    r9[forbidden_key] = "forbidden"
    with pytest.raises(ValueError):
        r55.assert_p7_r55_validation_command_matrix_bodyfree_contract(r9)

    row = deepcopy(_r9()["validation_command_rows"][0])
    row[forbidden_key] = "forbidden"
    with pytest.raises(ValueError):
        r55.assert_p7_r55_validation_command_matrix_row_bodyfree_contract(row)


def test_r55_r9_builder_rejects_rewritten_r8_input() -> None:
    r8 = _r8()
    r8["api_route_changed_here"] = True
    with pytest.raises(ValueError):
        r55.build_p7_r55_validation_command_matrix_bodyfree(
            final_no_touch_boundary_validation=r8,
        )
