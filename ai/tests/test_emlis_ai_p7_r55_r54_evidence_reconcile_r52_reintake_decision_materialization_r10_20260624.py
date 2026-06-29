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
FORBIDDEN_PROMOTION_TRUE_TOKENS = (
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
    '"final_summary_claimed_as_actual_review_completion": true',
    '"final_summary_claimed_as_p5_confirmed_final": true',
    '"final_summary_claimed_as_p6_start_allowed": true',
    '"final_summary_claimed_as_p8_start_allowed": true',
    '"final_summary_claimed_as_p7_complete": true',
    '"final_summary_claimed_as_release_allowed": true',
    '"r54_actual_review_operation_run_here": true',
    '"r52_decision_written_here": true',
    '"p8_question_design_started_here": true',
    '"p8_question_implementation_started_here": true',
    '"body_full_packet_generated_from_summary": true',
)


def _assert_no_body_touch_or_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for token in FORBIDDEN_BODY_KEY_TOKENS:
        assert token not in dumped
    for token in FORBIDDEN_PROMOTION_TRUE_TOKENS:
        assert token not in dumped


@lru_cache(maxsize=1)
def _cached_r9() -> tuple[dict[str, object]]:
    material = r55.build_p7_r55_validation_command_matrix_bodyfree()
    assert r55.assert_p7_r55_validation_command_matrix_bodyfree_contract(material) is True
    return (material,)


def _r9() -> dict[str, object]:
    return deepcopy(_cached_r9()[0])


@lru_cache(maxsize=1)
def _cached_r10() -> tuple[dict[str, object]]:
    material = r55.build_p7_r55_final_summary_bodyfree(validation_command_matrix=_r9())
    assert r55.assert_p7_r55_final_summary_bodyfree_contract(material) is True
    return (material,)


def _r10() -> dict[str, object]:
    return deepcopy(_cached_r10()[0])


def test_r55_r10_builds_bodyfree_final_summary_for_r54_actual_review_return() -> None:
    material = _r10()

    assert material["schema_version"] == r55.P7_R55_FINAL_SUMMARY_SCHEMA_VERSION
    assert set(material) == set(r55.P7_R55_FINAL_SUMMARY_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == r55.P7_R55_R10_STEP_REF
    assert material["source_mode"] == "local_snapshot"
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True
    assert material["current_received_snapshot_refs"] == r55.P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["actual_review_basis_ref"] == "R55_CURRENT_RECEIVED_SNAPSHOT_20260623"
    assert material["actual_review_basis_allowed"] == "current_received_snapshot_only"

    assert material["r9_validation_command_matrix_schema_version"] == r55.P7_R55_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION
    assert material["final_status"] == r55.P7_R55_FINAL_SUMMARY_READY_REF
    assert material["final_decision_summary_ref"] == r55.P7_R55_FINAL_DECISION_SUMMARY_REF
    assert material["final_no_promotion_policy_ref"] == r55.P7_R55_FINAL_NO_PROMOTION_POLICY_REF
    assert material["r55_decision_ref"] == r55.P7_R55_DEFAULT_R52_REINTAKE_DECISION_REF
    assert material["r52_existing_decision_equivalent"] == r55.P7_R55_DEFAULT_R52_EXISTING_DECISION_EQUIVALENT_REF
    assert material["r52_equivalent_reason_ref"] == r55.P7_R55_DEFAULT_R52_EQUIVALENT_REASON_REF
    assert material["decision_status"] == r55.P7_R55_DEFAULT_DECISION_STATUS_REF
    assert tuple(material["decision_reason_refs"]) == r55.P7_R55_DEFAULT_DECISION_REASON_REFS
    assert material["decision_reason_ref_count"] == len(r55.P7_R55_DEFAULT_DECISION_REASON_REFS)
    assert material["next_required_step"] == r55.P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF
    assert material["r55_next_implementation_step_ref"] == r55.P7_R55_R10_NEXT_IMPLEMENTATION_STEP_REF

    assert tuple(material["recommended_next_work_refs"]) == r55.P7_R55_FINAL_SUMMARY_RECOMMENDED_NEXT_WORK_REFS
    assert material["recommended_next_work_ref_count"] == len(r55.P7_R55_FINAL_SUMMARY_RECOMMENDED_NEXT_WORK_REFS)
    assert tuple(material["hold_reason_refs"]) == r55.P7_R55_FINAL_SUMMARY_HOLD_REASON_REFS
    assert material["hold_reason_ref_count"] == len(r55.P7_R55_FINAL_SUMMARY_HOLD_REASON_REFS)
    assert tuple(material["summary_reason_refs"]) == r55.P7_R55_FINAL_SUMMARY_REASON_REFS
    assert material["summary_reason_ref_count"] == len(r55.P7_R55_FINAL_SUMMARY_REASON_REFS)
    assert tuple(material["validation_limitation_refs"]) == r55.P7_R55_FINAL_SUMMARY_VALIDATION_LIMITATION_REFS
    assert material["validation_limitation_ref_count"] == len(r55.P7_R55_FINAL_SUMMARY_VALIDATION_LIMITATION_REFS)
    assert tuple(material["missing_evidence_refs"]) == r55.P7_R55_DEFAULT_MISSING_EVIDENCE_REFS
    assert material["missing_evidence_ref_count"] == len(r55.P7_R55_DEFAULT_MISSING_EVIDENCE_REFS)

    assert material["actual_review_evidence_complete"] is False
    assert material["actual_review_evidence_gap_status_ref"] == r55.P7_R55_ACTUAL_REVIEW_EVIDENCE_MISSING_GAP_STATUS_REF
    assert material["required_case_count"] == r55.P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
    assert material["rating_row_count"] == 0
    assert material["question_observation_row_count"] == 0
    assert material["disposal_verified"] is False
    assert material["p5_decision_status_ref"] == r55.P7_R55_P5_DECISION_STATUS_NOT_REVIEWED_REF
    assert material["p5_decision_candidate_ref"] == r55.P7_R55_R54_DEFAULT_P5_DECISION_CANDIDATE_REF

    assert material["p6_hold"] is True
    assert material["p8_hold"] is True
    assert material["release_hold"] is True
    assert material["p6_hold_reason_ref"] == r55.P7_R55_FINAL_P6_HOLD_REASON_REF
    assert material["p8_hold_reason_ref"] == r55.P7_R55_FINAL_P8_HOLD_REASON_REF
    assert material["release_hold_reason_ref"] == r55.P7_R55_FINAL_RELEASE_HOLD_REASON_REF
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_question_design_material_candidate"] is False
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False

    assert material["validation_documentation_status_ref"] == r55.P7_R55_VALIDATION_COMMAND_MATRIX_DOCUMENTED_REF
    assert material["validation_result_evidence_status_ref"] == r55.P7_R55_COMMAND_MATRIX_RESULT_EVIDENCE_STATUS_REF
    assert material["green_claim_rule_ref"] == r55.P7_R55_COMMAND_MATRIX_GREEN_CLAIM_RULE_REF
    assert material["validation_command_row_count"] == len(r55.P7_R55_COMMAND_MATRIX_GROUP_REFS)
    assert material["full_backend_suite_green_confirmed"] is False
    assert material["rn_real_device_modal_readfeel_confirmed"] is False
    assert material["question_implementation_status_ref"] == "P8_QUESTION_IMPLEMENTATION_NOT_STARTED_IN_R55"
    assert material["no_touch_boundary_status_ref"] == r55.P7_R55_NO_TOUCH_BOUNDARY_VALIDATED_REF
    assert material["no_touch_touched_refs"] == []
    assert material["no_touch_touched_ref_count"] == 0
    assert material["no_touch_touched_refs_empty_ref"] == r55.P7_R55_NO_TOUCH_TOUCHED_REFS_EMPTY_REF

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
    assert material["r55_10_final_summary_ready"] is True
    assert tuple(material["implemented_steps"]) == r55.P7_R55_R10_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == r55.P7_R55_R10_NOT_YET_IMPLEMENTED_STEPS

    _assert_no_body_touch_or_promotion(material)


def test_r55_r10_keeps_public_contract_no_touch_and_bodyfree_markers_closed() -> None:
    material = _r10()

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
    assert all(value is False for value in material["public_contract"].values())
    assert all(value is False for value in material["r55_public_no_touch_contract"].values())
    assert all(value is False for value in material["body_free_markers"].values())
    _assert_no_body_touch_or_promotion(material)


@pytest.mark.parametrize(
    "key",
    [
        *r55.P7_R55_FINAL_SUMMARY_FALSE_FIELD_REFS,
        *r55.P7_R55_FINAL_NO_TOUCH_BOUNDARY_FLAG_REFS,
        *r55.P7_R55_VALIDATION_COMMAND_MATRIX_FALSE_FIELD_REFS,
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
def test_r55_r10_rejects_false_field_true(key: str) -> None:
    material = _r10()
    material[key] = True
    with pytest.raises(ValueError):
        r55.assert_p7_r55_final_summary_bodyfree_contract(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("final_status", "R55_FINAL_SUMMARY_RELEASE_READY"),
        ("r55_decision_ref", "R55_R52_P5_CONFIRMED_CANDIDATE_ONLY"),
        ("r52_existing_decision_equivalent", "R52_GO_P5_CONFIRMED_CANDIDATE_REVIEWED_BUT_NOT_RELEASE"),
        ("r52_equivalent_reason_ref", "p5_confirmed_candidate"),
        ("decision_status", "CANDIDATE_ONLY"),
        ("decision_reason_refs", ["p8_ready"]),
        ("decision_reason_ref_count", 999),
        ("next_required_step", "P8_question_design_start"),
        ("r55_next_implementation_step_ref", "P8_question_design_start"),
        ("recommended_next_work_refs", ["start_P8_question_design"]),
        ("recommended_next_work_ref_count", 999),
        ("final_decision_summary_ref", "R55_FINAL_DECISION_RELEASE_READY"),
        ("final_no_promotion_policy_ref", "PROMOTION_ALLOWED"),
        ("hold_reason_refs", ["none"]),
        ("hold_reason_ref_count", 999),
        ("actual_review_evidence_gap_status_ref", "ACTUAL_REVIEW_EVIDENCE_COMPLETE"),
        ("required_case_count", 0),
        ("rating_row_count", 1),
        ("question_observation_row_count", 1),
        ("disposal_verified", True),
        ("p5_decision_status_ref", "R55_P5_CONFIRMED"),
        ("p5_decision_candidate_ref", "P5_CONFIRMED_CANDIDATE"),
        ("p6_hold", False),
        ("p8_hold", False),
        ("release_hold", False),
        ("validation_documentation_status_ref", "VALIDATION_EXECUTED_GREEN"),
        ("validation_result_evidence_status_ref", "COMMAND_MATRIX_RESULT_EVIDENCE_GREEN"),
        ("validation_command_row_count", 999),
        ("green_claim_rule_ref", "TARGET_GREEN_MEANS_PRODUCT_READY"),
        ("question_implementation_status_ref", "P8_QUESTION_IMPLEMENTATION_STARTED"),
        ("no_touch_boundary_status_ref", "NO_TOUCH_BYPASSED"),
        ("no_touch_touched_refs", ["api_route_changed_here"]),
        ("no_touch_touched_ref_count", 1),
        ("no_touch_touched_refs_empty_ref", "TOUCHED_REFS_PRESENT"),
        ("r55_10_final_summary_ready", False),
        ("implemented_steps", r55.P7_R55_R9_IMPLEMENTED_STEPS),
        ("not_yet_implemented_steps", ("P8_question_design",)),
    ],
)
def test_r55_r10_rejects_summary_decision_hold_or_step_rewrite(key: str, value: object) -> None:
    material = _r10()
    material[key] = value
    with pytest.raises(ValueError):
        r55.assert_p7_r55_final_summary_bodyfree_contract(material)


@pytest.mark.parametrize(
    "chain_flag",
    [
        "r55_0_scope_current_received_snapshot_refrozen",
        "r55_1_prior_helper_source_reconciled",
        "r55_2_validation_evidence_reconciled",
        "r55_3_r54_default_handoff_intake_done",
        "r55_4_bodyfree_forbidden_payload_scan_done",
        "r55_5_actual_review_evidence_gap_assessed",
        "r55_6_r52_reintake_decision_materialized",
        "r55_7_p5_p6_p8_release_separated",
        "r55_8_final_no_touch_boundary_validated",
        "r55_9_validation_command_matrix_documented",
        "r55_10_final_summary_ready",
    ],
)
def test_r55_r10_rejects_missing_material_chain_flag(chain_flag: str) -> None:
    material = _r10()
    material[chain_flag] = False
    with pytest.raises(ValueError):
        r55.assert_p7_r55_final_summary_bodyfree_contract(material)


@pytest.mark.parametrize(
    "forbidden_key",
    [
        "raw_input",
        "comment_text",
        "returned_surface",
        "history_body",
        "reviewer_free_text",
        "reviewer_notes",
        "question_text",
        "draft_question_text",
        "local_absolute_path",
        "body_content_hash",
        "packet_content_hash",
        "terminal_output",
        "command_full_output",
        "stdout",
        "stderr",
        "traceback",
    ],
)
def test_r55_r10_rejects_forbidden_body_or_question_payload_keys(forbidden_key: str) -> None:
    material = _r10()
    material[forbidden_key] = "forbidden"
    with pytest.raises(ValueError):
        r55.assert_p7_r55_final_summary_bodyfree_contract(material)


def test_r55_r10_builder_rejects_rewritten_r9_input() -> None:
    r9 = _r9()
    r9["p8_start_allowed"] = True
    with pytest.raises(ValueError):
        r55.build_p7_r55_final_summary_bodyfree(validation_command_matrix=r9)


def test_r55_r10_builder_rejects_r9_that_does_not_point_to_final_summary() -> None:
    r9 = _r9()
    r9["r55_next_implementation_step_ref"] = r55.P7_R55_R10_NEXT_IMPLEMENTATION_STEP_REF
    with pytest.raises(ValueError):
        r55.build_p7_r55_final_summary_bodyfree(validation_command_matrix=r9)
