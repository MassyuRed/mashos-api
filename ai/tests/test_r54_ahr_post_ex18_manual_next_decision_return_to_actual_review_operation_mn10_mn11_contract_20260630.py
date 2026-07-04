# -*- coding: utf-8 -*-
"""R54-AHR Post-EX18 manual next-decision MN10-MN11 contract tests."""

from __future__ import annotations

from copy import deepcopy

import pytest

import emlis_ai_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_20260629 as ex
import emlis_ai_p7_r54_ahr_post_ex18_manual_next_decision_return_to_actual_review_operation_20260630 as mn


def _assert_bodyfree_no_touch_no_promotion(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    for key in mn.P7_R54_AHR_POST_EX18_REQUIRED_FALSE_FLAG_REFS:
        assert material[key] is False, key
    assert material["next_decision_auto_execution_allowed"] is False
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


def _ready_mn03() -> dict[str, object]:
    mn02 = mn.build_p7_r54_ahr_post_ex18_mn02_actual_review_evidence_state_normalization(
        ex18_result_memo_bodyfree_envelope_intake=_valid_mn01()
    )
    return mn.build_p7_r54_ahr_post_ex18_mn03_manual_decision_classifier(
        actual_review_evidence_state_normalization=mn02
    )


def _ready_mn04() -> dict[str, object]:
    return mn.build_p7_r54_ahr_post_ex18_mn04_return_to_actual_review_operation_plan(
        manual_decision_classifier=_ready_mn03()
    )


def _ready_mn05() -> dict[str, object]:
    return mn.build_p7_r54_ahr_post_ex18_mn05_expected_bodyfree_evidence_intake_bundle_boundary(
        return_to_actual_review_operation_plan=_ready_mn04()
    )


def _ready_mn06() -> dict[str, object]:
    return mn.build_p7_r54_ahr_post_ex18_mn06_no_body_no_question_no_path_no_hash_scan(
        expected_bodyfree_evidence_intake_bundle_boundary=_ready_mn05(),
        manual_decision_material=_ready_mn03(),
        return_to_actual_review_operation_plan=_ready_mn04(),
    )


def _ready_mn07() -> dict[str, object]:
    return mn.build_p7_r54_ahr_post_ex18_mn07_downstream_no_promotion_boundary_materialization(
        no_body_no_question_no_path_no_hash_scan=_ready_mn06()
    )


def _ready_mn08() -> dict[str, object]:
    return mn.build_p7_r54_ahr_post_ex18_mn08_reentry_mapping_to_existing_postcr22_ex07_ex18(
        downstream_no_promotion_boundary_materialization=_ready_mn07()
    )


def _ready_mn09() -> dict[str, object]:
    return mn.build_p7_r54_ahr_post_ex18_mn09_validation_command_matrix_result_memo_envelope(
        reentry_mapping_to_existing_postcr22_ex07_ex18=_ready_mn08()
    )


def _ready_mn10() -> dict[str, object]:
    return mn.build_p7_r54_ahr_post_ex18_mn10_alias_contract_function_boundary(
        validation_command_matrix_result_memo_envelope=_ready_mn09()
    )


def test_mn10_materializes_alias_contract_function_boundary_without_touching_existing_postcr22_or_runtime() -> None:
    material = _ready_mn10()

    assert set(material) == set(mn.P7_R54_AHR_POST_EX18_MN10_REQUIRED_FIELD_REFS)
    assert material["operation_step_ref"] == mn.P7_R54_AHR_POST_EX18_MN10_STEP_REF
    assert material["mn10_status_ref"] == mn.P7_R54_AHR_POST_EX18_MN10_READY_STATUS_REF
    assert material["mn10_ready"] is True
    assert material["mn09_ready"] is True
    assert material["mn09_next_required_step"] == mn.P7_R54_AHR_POST_EX18_MN10_STEP_REF
    assert tuple(material["primary_builder_function_refs"]) == mn.P7_R54_AHR_POST_EX18_MN10_PRIMARY_BUILDER_FUNCTION_REFS
    assert tuple(material["primary_assert_function_refs"]) == mn.P7_R54_AHR_POST_EX18_MN10_PRIMARY_ASSERT_FUNCTION_REFS
    assert tuple(material["alias_builder_function_refs"]) == mn.P7_R54_AHR_POST_EX18_MN10_ALIAS_BUILDER_FUNCTION_REFS
    assert tuple(material["alias_assert_function_refs"]) == mn.P7_R54_AHR_POST_EX18_MN10_ALIAS_ASSERT_FUNCTION_REFS
    assert material["function_boundary_row_count"] == 50
    assert material["function_refs_resolved_in_module"] is True
    assert material["contract_assertion_refs_resolved_in_module"] is True
    assert all(row["postcr22_existing_function_renamed"] is False for row in material["function_boundary_rows"])
    assert all(row["cr_cs_ex_prefix_changed"] is False for row in material["function_boundary_rows"])
    assert all(row["executes_actual_review"] is False for row in material["function_boundary_rows"])
    assert all(row["allows_downstream_promotion"] is False for row in material["function_boundary_rows"])
    assert material["existing_postcr22_helper_rename_forbidden"] is True
    assert material["existing_postcr22_helper_function_boundary_preserved"] is True
    assert material["existing_cr_cs_ex_prefix_boundary_preserved"] is True
    assert material["mn_prefix_internal_to_postex18_manual_next_decision_only"] is True
    assert material["function_boundary_does_not_change_api_db_rn_runtime_response_keys"] is True
    assert material["function_boundary_does_not_allow_downstream_promotion"] is True
    assert material["next_required_step"] == mn.P7_R54_AHR_POST_EX18_MN11_STEP_REF
    assert mn.assert_p7_r54_ahr_post_ex18_mn10_alias_contract_function_boundary_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_mn10_blocks_when_mn09_validation_envelope_is_not_ready() -> None:
    material = mn.build_p7_r54_ahr_post_ex18_mn10_alias_contract_function_boundary(
        validation_command_matrix_result_memo_envelope=None
    )

    assert material["mn10_status_ref"] == mn.P7_R54_AHR_POST_EX18_MN10_BLOCKED_STATUS_REF
    assert material["mn10_ready"] is False
    assert "mn09_validation_command_matrix_result_memo_envelope_not_ready" in material["mn10_blocker_refs"]
    assert material["next_required_step"] == mn.P7_R54_AHR_POST_EX18_MN10_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert mn.assert_p7_r54_ahr_post_ex18_mn10_alias_contract_function_boundary_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_mn10_contract_rejects_alias_or_prefix_or_promotion_mutation() -> None:
    material = _ready_mn10()

    mutated = deepcopy(material)
    mutated["function_boundary_rows"][0]["postcr22_existing_function_renamed"] = True
    with pytest.raises(ValueError):
        mn.assert_p7_r54_ahr_post_ex18_mn10_alias_contract_function_boundary_contract(mutated)

    mutated = deepcopy(material)
    mutated["existing_cr_cs_ex_prefix_boundary_preserved"] = False
    with pytest.raises(ValueError):
        mn.assert_p7_r54_ahr_post_ex18_mn10_alias_contract_function_boundary_contract(mutated)

    mutated = deepcopy(material)
    mutated["p8_start_allowed"] = True
    with pytest.raises(ValueError):
        mn.assert_p7_r54_ahr_post_ex18_mn10_alias_contract_function_boundary_contract(mutated)


def test_mn11_finalizes_acceptance_as_return_to_actual_review_operation_required_fail_closed_hold() -> None:
    material = mn.build_p7_r54_ahr_post_ex18_mn11_acceptance_fail_closed_finalizer(
        alias_contract_function_boundary=_ready_mn10()
    )

    assert set(material) == set(mn.P7_R54_AHR_POST_EX18_MN11_REQUIRED_FIELD_REFS)
    assert material["operation_step_ref"] == mn.P7_R54_AHR_POST_EX18_MN11_STEP_REF
    assert material["mn11_status_ref"] == mn.P7_R54_AHR_POST_EX18_MN11_READY_STATUS_REF
    assert material["mn11_ready"] is True
    assert material["acceptance_ready"] is True
    assert material["finalizer_ready_for_result_memo"] is True
    assert material["manual_decision_ref"] == mn.P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_RETURN_OPERATION_REQUIRED_REF
    assert material["final_manual_decision_ref"] == mn.P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_RETURN_OPERATION_REQUIRED_REF
    assert material["manual_decision_status_ref"] == mn.P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_READY_STATUS_REF
    assert material["return_to_actual_review_operation_required"] is True
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert material["actual_review_evidence_complete_from_real_review_false"] is True
    assert material["actual_review_evidence_complete_from_real_review_accepted_false"] is True
    assert material["final_next_required_step_ref"] == mn.P7_R54_AHR_POST_EX18_MN03_RETURN_NEXT_REQUIRED_STEP_REF
    assert material["next_required_step"] == mn.P7_R54_AHR_POST_EX18_MN03_RETURN_NEXT_REQUIRED_STEP_REF
    assert material["no_body_leak_validation_passed"] is True
    assert material["no_question_text_validation_passed"] is True
    assert material["no_path_hash_validation_passed"] is True
    assert material["no_touch_boundary_confirmed"] is True
    assert material["no_promotion_boundary_confirmed"] is True
    assert all(row["satisfied"] is True for row in material["acceptance_condition_rows"])
    assert material["finalizer_does_not_execute_actual_review"] is True
    assert material["finalizer_does_not_generate_bodyfull_packet"] is True
    assert material["finalizer_does_not_create_actual_rows"] is True
    assert material["finalizer_does_not_create_question_text"] is True
    assert material["finalizer_does_not_allow_downstream_promotion"] is True
    assert material["p5_p6_p8_r52_p7_release_remain_false"] is True
    assert tuple(material["implemented_steps"]) == mn.P7_R54_AHR_POST_EX18_MN11_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == mn.P7_R54_AHR_POST_EX18_MN11_NOT_YET_IMPLEMENTED_STEPS
    assert mn.assert_p7_r54_ahr_post_ex18_mn11_acceptance_fail_closed_finalizer_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_mn11_blocks_when_mn10_alias_contract_boundary_is_not_ready() -> None:
    blocked_mn10 = mn.build_p7_r54_ahr_post_ex18_mn10_alias_contract_function_boundary(
        validation_command_matrix_result_memo_envelope=None
    )
    material = mn.build_p7_r54_ahr_post_ex18_mn11_acceptance_fail_closed_finalizer(
        alias_contract_function_boundary=blocked_mn10
    )

    assert material["mn11_status_ref"] == mn.P7_R54_AHR_POST_EX18_MN11_BLOCKED_STATUS_REF
    assert material["mn11_ready"] is False
    assert "mn10_alias_contract_function_boundary_not_ready" in material["mn11_blocker_refs"]
    assert material["manual_decision_ref"] == mn.P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_HOLD_EX18_INVALID_REF
    assert material["return_to_actual_review_operation_required"] is False
    assert material["acceptance_ready"] is False
    assert all(row["satisfied"] is False for row in material["acceptance_condition_rows"])
    assert material["next_required_step"] == mn.P7_R54_AHR_POST_EX18_MN11_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert mn.assert_p7_r54_ahr_post_ex18_mn11_acceptance_fail_closed_finalizer_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_mn11_contract_rejects_completion_promotion_or_question_text_mutation() -> None:
    material = mn.build_p7_r54_ahr_post_ex18_mn11_acceptance_fail_closed_finalizer(
        alias_contract_function_boundary=_ready_mn10()
    )

    mutated = deepcopy(material)
    mutated["actual_review_evidence_complete_from_real_review"] = True
    with pytest.raises(ValueError):
        mn.assert_p7_r54_ahr_post_ex18_mn11_acceptance_fail_closed_finalizer_contract(mutated)

    mutated = deepcopy(material)
    mutated["release_allowed"] = True
    with pytest.raises(ValueError):
        mn.assert_p7_r54_ahr_post_ex18_mn11_acceptance_fail_closed_finalizer_contract(mutated)

    mutated = deepcopy(material)
    mutated["question_text"] = "must not be copied"
    with pytest.raises(ValueError):
        mn.assert_p7_r54_ahr_post_ex18_mn11_acceptance_fail_closed_finalizer_contract(mutated)


def test_mn10_mn11_aliases_and_final_bodyfree_alias_match_primary_builders() -> None:
    mn09 = _ready_mn09()
    primary_mn10 = mn.build_p7_r54_ahr_post_ex18_mn10_alias_contract_function_boundary(
        validation_command_matrix_result_memo_envelope=mn09
    )
    alias_mn10 = mn.build_p7_r54_ahr_post_ex18_manual_next_decision_alias_contract_function_boundary_bodyfree(
        validation_command_matrix_result_memo_envelope=mn09
    )
    assert alias_mn10 == primary_mn10
    assert mn.assert_p7_r54_ahr_post_ex18_manual_next_decision_alias_contract_function_boundary_bodyfree_contract(alias_mn10) is True

    primary_mn11 = mn.build_p7_r54_ahr_post_ex18_mn11_acceptance_fail_closed_finalizer(
        alias_contract_function_boundary=primary_mn10
    )
    alias_mn11 = mn.build_p7_r54_ahr_post_ex18_manual_next_decision_acceptance_fail_closed_finalizer_bodyfree(
        alias_contract_function_boundary=primary_mn10
    )
    final_alias = mn.build_p7_r54_ahr_post_ex18_manual_next_decision_return_to_actual_review_operation_bodyfree(
        validation_command_matrix_result_memo_envelope=mn09
    )
    assert alias_mn11 == primary_mn11
    assert final_alias == primary_mn11
    assert mn.assert_p7_r54_ahr_post_ex18_manual_next_decision_acceptance_fail_closed_finalizer_bodyfree_contract(alias_mn11) is True
    assert mn.assert_p7_r54_ahr_post_ex18_manual_next_decision_return_to_actual_review_operation_bodyfree_contract(final_alias) is True
