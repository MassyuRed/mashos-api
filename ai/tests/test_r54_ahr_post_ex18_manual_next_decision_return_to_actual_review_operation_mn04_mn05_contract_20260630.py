# -*- coding: utf-8 -*-
"""R54-AHR Post-EX18 manual next-decision MN04-MN05 contract tests."""

from __future__ import annotations

from copy import deepcopy

import pytest

import emlis_ai_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_20260629 as ex
import emlis_ai_p7_r54_ahr_post_ex18_manual_next_decision_return_to_actual_review_operation_20260630 as mn


def _assert_bodyfree_no_touch_no_promotion(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    for key in mn.P7_R54_AHR_POST_EX18_REQUIRED_FALSE_FLAG_REFS:
        assert material[key] is False, key
    for marker_map_key in ("public_contract", "post_ex18_no_touch_contract", "body_free_markers"):
        assert material[marker_map_key]
        assert all(value is False for value in material[marker_map_key].values()), marker_map_key
    for forbidden_key in mn.P7_R54_AHR_POST_EX18_FORBIDDEN_PAYLOAD_KEY_REFS:
        assert forbidden_key not in material, forbidden_key


def _valid_ex18_bodyfree_envelope() -> dict[str, object]:
    return {
        "schema_version": ex.P7_R54_AHR_POST_CR22_EX18_VALIDATION_COMMAND_MATRIX_RESULT_MEMO_NEXT_DECISION_HOLD_SCHEMA_VERSION,
        "operation_step_ref": ex.P7_R54_AHR_POST_CR22_EX18_STEP_REF,
        "body_free": True,
        "next_required_step": ex.P7_R54_AHR_POST_CR22_EX18_NEXT_DECISION_HOLD_REF,
        "next_decision_hold_required": True,
        "next_decision_auto_execution_allowed": False,
        "result_memo_ready": True,
        "validation_command_matrix_ready": True,
        "actual_review_evidence_complete": True,
        "actual_human_review_run_here": False,
        "actual_human_review_operation_run": False,
        "actual_human_review_newly_run_here": False,
        "actual_human_review_complete": False,
        "actual_selection_rows_created_here": False,
        "actual_rating_rows_materialized_here": True,
        "actual_question_need_observation_rows_materialized_here": True,
        "actual_disposal_receipt_materialized_here": True,
        "disposal_verified": True,
        "row_counts": {
            "reviewed_case_count": 24,
            "sanitized_review_result_row_count": 24,
            "rating_row_count": 24,
            "question_need_observation_row_count": 24,
        },
        "candidate_only_decisions": [
            "P5_CONFIRMED_CANDIDATE_BODYFREE_ONLY",
            "P6_LIMITED_HUMAN_READFEEL_CANDIDATE_ONLY",
            "P8_QUESTION_NEED_OBSERVATION_MATERIAL_CANDIDATE_ONLY",
            "R52_REINTAKE_HANDOFF_CANDIDATE_ONLY",
        ],
        "not_claimed_boundary": {key: False for key in mn.P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS},
    }


def _valid_mn01() -> dict[str, object]:
    mn00 = mn.build_p7_r54_ahr_post_ex18_mn00_scope_no_touch_no_promotion_boundary_freeze()
    return mn.build_p7_r54_ahr_post_ex18_mn01_ex18_result_memo_bodyfree_envelope_intake(
        scope_no_touch_no_promotion_boundary_freeze=mn00,
        ex18_result_memo_bodyfree_envelope=_valid_ex18_bodyfree_envelope(),
    )


def _return_required_mn03() -> dict[str, object]:
    mn02 = mn.build_p7_r54_ahr_post_ex18_mn02_actual_review_evidence_state_normalization(
        ex18_result_memo_bodyfree_envelope_intake=_valid_mn01()
    )
    return mn.build_p7_r54_ahr_post_ex18_mn03_manual_decision_classifier(
        actual_review_evidence_state_normalization=mn02
    )


def _actual_review_complete_bundle() -> dict[str, object]:
    return {
        "body_free": True,
        "actual_source_ref": mn.P7_R54_AHR_POST_EX18_ACTUAL_PERSON_LOCAL_ONLY_REVIEW_SOURCE_REF,
        "actual_source_guard_passed": True,
        "actual_human_review_executed_by_person": True,
        "reviewer_local_only_read_receipt_present": True,
        "actual_operation_receipt_ref": "actual_operation_receipt_ref",
        "disposal_receipt_ref": "actual_disposal_receipt_ref",
        "row_counts": {
            "reviewed_case_count": 24,
            "sanitized_review_result_row_count": 24,
            "rating_row_count": 24,
            "question_need_observation_row_count": 24,
        },
        "disposal_verified": True,
        "no_body_leak_validation_passed": True,
        "no_question_text_validation_passed": True,
        "no_path_hash_validation_passed": True,
        "row_created_by_helper": False,
        "row_created_for_unit_test": False,
        "row_is_synthetic_contract_fixture": False,
        "historical_row_reused": False,
    }


def _downstream_manual_mn03() -> dict[str, object]:
    mn02 = mn.build_p7_r54_ahr_post_ex18_mn02_actual_review_evidence_state_normalization(
        ex18_result_memo_bodyfree_envelope_intake=_valid_mn01(),
        actual_review_evidence_intake_bundle=_actual_review_complete_bundle(),
    )
    return mn.build_p7_r54_ahr_post_ex18_mn03_manual_decision_classifier(
        actual_review_evidence_state_normalization=mn02
    )


def _ready_mn04() -> dict[str, object]:
    return mn.build_p7_r54_ahr_post_ex18_mn04_return_to_actual_review_operation_plan(
        manual_decision_classifier=_return_required_mn03()
    )


def test_mn04_builds_bodyfree_return_operation_plan_only_after_return_required_decision() -> None:
    material = _ready_mn04()

    assert set(material) == set(mn.P7_R54_AHR_POST_EX18_MN04_REQUIRED_FIELD_REFS)
    assert material["operation_step_ref"] == mn.P7_R54_AHR_POST_EX18_MN04_STEP_REF
    assert material["mn04_status_ref"] == mn.P7_R54_AHR_POST_EX18_MN04_READY_STATUS_REF
    assert material["mn04_ready"] is True
    assert material["mn03_manual_decision_ref"] == mn.P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_RETURN_OPERATION_REQUIRED_REF
    assert material["actual_operation_plan_ref"] == mn.P7_R54_AHR_POST_EX18_OPERATION_PLAN_REF
    assert material["operation_basis_ref"] == mn.P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_REF
    assert material["required_case_count"] == 24
    assert tuple(material["required_bodyfree_artifact_refs"]) == mn.P7_R54_AHR_POST_EX18_REQUIRED_BODYFREE_ARTIFACT_REFS
    assert tuple(material["forbidden_artifact_refs"]) == mn.P7_R54_AHR_POST_EX18_FORBIDDEN_ARTIFACT_REFS
    assert material["local_only_required"] is True
    assert material["explicit_allow_required"] is True
    assert material["purge_plan_required"] is True
    assert material["actual_review_operation_not_executed_here"] is True
    assert material["actual_rows_not_created_by_plan_builder"] is True
    assert material["mn04_passes_to_expected_bodyfree_evidence_intake_bundle_boundary"] is True
    assert material["actual_human_review_run_here"] is False
    assert material["actual_selection_rows_created_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == mn.P7_R54_AHR_POST_EX18_MN05_STEP_REF
    assert mn.assert_p7_r54_ahr_post_ex18_mn04_return_to_actual_review_operation_plan_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_mn04_blocks_when_mn03_is_not_return_operation_required() -> None:
    material = mn.build_p7_r54_ahr_post_ex18_mn04_return_to_actual_review_operation_plan(
        manual_decision_classifier=_downstream_manual_mn03()
    )

    assert material["mn04_status_ref"] == mn.P7_R54_AHR_POST_EX18_MN04_BLOCKED_STATUS_REF
    assert material["mn04_ready"] is False
    assert "mn04_manual_decision_is_not_return_to_actual_review_operation_required" in material["mn04_blocker_refs"]
    assert material["actual_operation_plan_ref"] == ""
    assert material["mn04_passes_to_expected_bodyfree_evidence_intake_bundle_boundary"] is False
    assert material["next_required_step"] == mn.P7_R54_AHR_POST_EX18_MN04_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert mn.assert_p7_r54_ahr_post_ex18_mn04_return_to_actual_review_operation_plan_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_mn04_contract_rejects_artifact_or_execution_mutation() -> None:
    material = _ready_mn04()

    mutated = deepcopy(material)
    mutated["required_bodyfree_artifact_refs"] = list(mutated["required_bodyfree_artifact_refs"][:-1])
    mutated["required_bodyfree_artifact_ref_count"] = len(mutated["required_bodyfree_artifact_refs"])
    with pytest.raises(ValueError):
        mn.assert_p7_r54_ahr_post_ex18_mn04_return_to_actual_review_operation_plan_contract(mutated)

    mutated = deepcopy(material)
    mutated["actual_human_review_run_here"] = True
    with pytest.raises(ValueError):
        mn.assert_p7_r54_ahr_post_ex18_mn04_return_to_actual_review_operation_plan_contract(mutated)


def test_mn05_defines_expected_bodyfree_evidence_bundle_boundary_without_materializing_it() -> None:
    material = mn.build_p7_r54_ahr_post_ex18_mn05_expected_bodyfree_evidence_intake_bundle_boundary(
        return_to_actual_review_operation_plan=_ready_mn04()
    )

    assert set(material) == set(mn.P7_R54_AHR_POST_EX18_MN05_REQUIRED_FIELD_REFS)
    assert material["operation_step_ref"] == mn.P7_R54_AHR_POST_EX18_MN05_STEP_REF
    assert material["mn05_status_ref"] == mn.P7_R54_AHR_POST_EX18_MN05_READY_STATUS_REF
    assert material["mn05_ready"] is True
    assert material["expected_actual_review_evidence_intake_bundle_ref"] == mn.P7_R54_AHR_POST_EX18_EXPECTED_EVIDENCE_INTAKE_BUNDLE_BOUNDARY_REF
    assert material["expected_bundle_template_only"] is True
    assert material["actual_review_evidence_intake_bundle_materialized_here"] is False
    assert material["expected_actual_source_ref"] == mn.P7_R54_AHR_POST_EX18_ACTUAL_PERSON_LOCAL_ONLY_REVIEW_SOURCE_REF
    assert material["expected_reviewed_case_count"] == 24
    assert material["expected_sanitized_review_result_row_count"] == 24
    assert material["expected_rating_row_count"] == 24
    assert material["expected_question_need_observation_row_count"] == 24
    assert tuple(material["expected_bundle_required_bodyfree_artifact_refs"]) == mn.P7_R54_AHR_POST_EX18_REQUIRED_BODYFREE_ARTIFACT_REFS
    assert tuple(material["expected_bundle_forbidden_artifact_refs"]) == mn.P7_R54_AHR_POST_EX18_FORBIDDEN_ARTIFACT_REFS
    assert material["question_need_observation_rows_expectation"]["question_text_included"] is False
    assert material["question_need_observation_rows_expectation"]["draft_question_text_included"] is False
    assert material["disposal_receipt_expectation"]["body_hash_stored_allowed"] is False
    assert material["disposal_receipt_expectation"]["local_absolute_path_included_allowed"] is False
    assert material["actual_review_evidence_not_completed_by_boundary"] is True
    assert material["actual_review_operation_not_run_by_boundary"] is True
    assert material["actual_rows_not_created_by_boundary"] is True
    assert material["bodyfull_packet_not_generated_by_boundary"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["actual_human_review_run_here"] is False
    assert material["actual_selection_rows_created_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == mn.P7_R54_AHR_POST_EX18_MN06_STEP_REF
    assert mn.assert_p7_r54_ahr_post_ex18_mn05_expected_bodyfree_evidence_intake_bundle_boundary_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_mn05_blocks_without_ready_mn04_plan() -> None:
    blocked_mn04 = mn.build_p7_r54_ahr_post_ex18_mn04_return_to_actual_review_operation_plan(
        manual_decision_classifier=_downstream_manual_mn03()
    )
    material = mn.build_p7_r54_ahr_post_ex18_mn05_expected_bodyfree_evidence_intake_bundle_boundary(
        return_to_actual_review_operation_plan=blocked_mn04
    )

    assert material["mn05_status_ref"] == mn.P7_R54_AHR_POST_EX18_MN05_BLOCKED_STATUS_REF
    assert material["mn05_ready"] is False
    assert "mn05_return_to_actual_review_operation_plan_not_ready" in material["mn05_blocker_refs"]
    assert material["expected_actual_review_evidence_intake_bundle_ref"] == ""
    assert material["actual_review_evidence_intake_bundle_materialized_here"] is False
    assert material["next_required_step"] == mn.P7_R54_AHR_POST_EX18_MN05_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert mn.assert_p7_r54_ahr_post_ex18_mn05_expected_bodyfree_evidence_intake_bundle_boundary_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_mn05_contract_rejects_question_text_or_path_hash_boundary_mutation() -> None:
    material = mn.build_p7_r54_ahr_post_ex18_mn05_expected_bodyfree_evidence_intake_bundle_boundary(
        return_to_actual_review_operation_plan=_ready_mn04()
    )

    mutated = deepcopy(material)
    mutated["question_need_observation_rows_expectation"]["question_text_included"] = True
    with pytest.raises(ValueError):
        mn.assert_p7_r54_ahr_post_ex18_mn05_expected_bodyfree_evidence_intake_bundle_boundary_contract(mutated)

    mutated = deepcopy(material)
    mutated["disposal_receipt_expectation"]["body_hash_stored_allowed"] = True
    with pytest.raises(ValueError):
        mn.assert_p7_r54_ahr_post_ex18_mn05_expected_bodyfree_evidence_intake_bundle_boundary_contract(mutated)


def test_mn04_mn05_aliases_match_primary_builders_and_contracts() -> None:
    mn03 = _return_required_mn03()
    mn04 = mn.build_p7_r54_ahr_post_ex18_manual_next_decision_return_to_actual_review_operation_plan_bodyfree(
        manual_decision_classifier=mn03
    )
    primary_mn04 = mn.build_p7_r54_ahr_post_ex18_mn04_return_to_actual_review_operation_plan(
        manual_decision_classifier=mn03
    )
    assert mn04 == primary_mn04
    assert mn.assert_p7_r54_ahr_post_ex18_manual_next_decision_return_to_actual_review_operation_plan_bodyfree_contract(mn04) is True

    mn05 = mn.build_p7_r54_ahr_post_ex18_manual_next_decision_expected_bodyfree_evidence_intake_bundle_boundary_bodyfree(
        return_to_actual_review_operation_plan=mn04
    )
    primary_mn05 = mn.build_p7_r54_ahr_post_ex18_mn05_expected_bodyfree_evidence_intake_bundle_boundary(
        return_to_actual_review_operation_plan=mn04
    )
    assert mn05 == primary_mn05
    assert mn.assert_p7_r54_ahr_post_ex18_manual_next_decision_expected_bodyfree_evidence_intake_bundle_boundary_bodyfree_contract(mn05) is True
