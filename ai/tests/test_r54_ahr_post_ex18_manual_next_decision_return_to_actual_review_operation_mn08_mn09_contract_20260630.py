# -*- coding: utf-8 -*-
"""R54-AHR Post-EX18 manual next-decision MN08-MN09 contract tests."""

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


def _return_required_mn03() -> dict[str, object]:
    mn02 = mn.build_p7_r54_ahr_post_ex18_mn02_actual_review_evidence_state_normalization(
        ex18_result_memo_bodyfree_envelope_intake=_valid_mn01()
    )
    return mn.build_p7_r54_ahr_post_ex18_mn03_manual_decision_classifier(
        actual_review_evidence_state_normalization=mn02
    )


def _ready_mn04() -> dict[str, object]:
    return mn.build_p7_r54_ahr_post_ex18_mn04_return_to_actual_review_operation_plan(
        manual_decision_classifier=_return_required_mn03()
    )


def _ready_mn05() -> dict[str, object]:
    return mn.build_p7_r54_ahr_post_ex18_mn05_expected_bodyfree_evidence_intake_bundle_boundary(
        return_to_actual_review_operation_plan=_ready_mn04()
    )


def _ready_mn06() -> dict[str, object]:
    return mn.build_p7_r54_ahr_post_ex18_mn06_no_body_no_question_no_path_no_hash_scan(
        expected_bodyfree_evidence_intake_bundle_boundary=_ready_mn05(),
        manual_decision_material=_return_required_mn03(),
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


def test_mn08_maps_future_bodyfree_evidence_bundle_to_existing_postcr22_ex07_ex18_without_reimplementation() -> None:
    material = _ready_mn08()

    assert set(material) == set(mn.P7_R54_AHR_POST_EX18_MN08_REQUIRED_FIELD_REFS)
    assert material["operation_step_ref"] == mn.P7_R54_AHR_POST_EX18_MN08_STEP_REF
    assert material["mn08_status_ref"] == mn.P7_R54_AHR_POST_EX18_MN08_READY_STATUS_REF
    assert material["mn08_ready"] is True
    assert material["reentry_mapping_bodyfree_ready"] is True
    assert tuple(material["existing_postcr22_reentry_step_refs"]) == mn.P7_R54_AHR_POST_EX18_MN08_EXISTING_POSTCR22_REENTRY_STEP_REFS
    assert material["existing_postcr22_reentry_step_ref_count"] == 12
    assert material["reentry_mapping_row_count"] == 12
    assert material["reentry_mapping_rows"][0]["existing_postcr22_step_ref"] == ex.P7_R54_AHR_POST_CR22_EX07_STEP_REF
    assert material["reentry_mapping_rows"][-1]["existing_postcr22_step_ref"] == ex.P7_R54_AHR_POST_CR22_EX18_STEP_REF
    assert all(row["postex18_helper_reimplements_existing_step"] is False for row in material["reentry_mapping_rows"])
    assert all(row["actual_execution_claimed_by_mapping"] is False for row in material["reentry_mapping_rows"])
    assert material["reentry_mapping_requires_future_actual_review_evidence_bundle"] is True
    assert material["actual_review_evidence_bundle_not_created_by_mapping"] is True
    assert material["actual_review_operation_not_run_by_mapping"] is True
    assert material["actual_rows_not_created_by_mapping"] is True
    assert material["post_ex18_helper_does_not_reimplement_postcr22_ex08_ex18"] is True
    assert material["reentry_mapping_is_not_actual_execution_claim"] is True
    assert material["reentry_mapping_is_not_r52_actual_execution_claim"] is True
    assert material["next_required_step"] == mn.P7_R54_AHR_POST_EX18_MN09_STEP_REF
    assert mn.assert_p7_r54_ahr_post_ex18_mn08_reentry_mapping_to_existing_postcr22_ex07_ex18_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_mn08_blocks_when_mn07_no_promotion_boundary_is_not_ready() -> None:
    blocked_mn06 = mn.build_p7_r54_ahr_post_ex18_mn06_no_body_no_question_no_path_no_hash_scan(
        expected_bodyfree_evidence_intake_bundle_boundary=_ready_mn05(),
        additional_bodyfree_scan_targets={"draft_question_text": "do not copy draft"},
    )
    blocked_mn07 = mn.build_p7_r54_ahr_post_ex18_mn07_downstream_no_promotion_boundary_materialization(
        no_body_no_question_no_path_no_hash_scan=blocked_mn06
    )
    material = mn.build_p7_r54_ahr_post_ex18_mn08_reentry_mapping_to_existing_postcr22_ex07_ex18(
        downstream_no_promotion_boundary_materialization=blocked_mn07
    )

    assert material["mn08_status_ref"] == mn.P7_R54_AHR_POST_EX18_MN08_BLOCKED_STATUS_REF
    assert material["mn08_ready"] is False
    assert "mn07_downstream_no_promotion_boundary_materialization_not_ready" in material["mn08_blocker_refs"]
    assert material["reentry_mapping_bodyfree_ready"] is False
    assert material["next_required_step"] == mn.P7_R54_AHR_POST_EX18_MN08_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert "do not copy draft" not in str(material)
    assert mn.assert_p7_r54_ahr_post_ex18_mn08_reentry_mapping_to_existing_postcr22_ex07_ex18_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_mn08_contract_rejects_reentry_mapping_or_promotion_mutation() -> None:
    material = _ready_mn08()

    mutated = deepcopy(material)
    mutated["reentry_mapping_rows"][0]["existing_postcr22_step_ref"] = ex.P7_R54_AHR_POST_CR22_EX18_STEP_REF
    with pytest.raises(ValueError):
        mn.assert_p7_r54_ahr_post_ex18_mn08_reentry_mapping_to_existing_postcr22_ex07_ex18_contract(mutated)

    mutated = deepcopy(material)
    mutated["reentry_mapping_is_not_r52_actual_execution_claim"] = False
    with pytest.raises(ValueError):
        mn.assert_p7_r54_ahr_post_ex18_mn08_reentry_mapping_to_existing_postcr22_ex07_ex18_contract(mutated)

    mutated = deepcopy(material)
    mutated["p8_start_allowed"] = True
    with pytest.raises(ValueError):
        mn.assert_p7_r54_ahr_post_ex18_mn08_reentry_mapping_to_existing_postcr22_ex07_ex18_contract(mutated)


def test_mn09_builds_bodyfree_validation_command_matrix_and_result_memo_envelope_without_green_claims() -> None:
    material = mn.build_p7_r54_ahr_post_ex18_mn09_validation_command_matrix_result_memo_envelope(
        reentry_mapping_to_existing_postcr22_ex07_ex18=_ready_mn08()
    )

    assert set(material) == set(mn.P7_R54_AHR_POST_EX18_MN09_REQUIRED_FIELD_REFS)
    assert material["operation_step_ref"] == mn.P7_R54_AHR_POST_EX18_MN09_STEP_REF
    assert material["mn09_status_ref"] == mn.P7_R54_AHR_POST_EX18_MN09_READY_STATUS_REF
    assert material["mn09_ready"] is True
    assert material["validation_command_matrix_ready"] is True
    assert material["result_memo_envelope_ready"] is True
    assert tuple(material["validation_command_refs"]) == mn.P7_R54_AHR_POST_EX18_MN09_VALIDATION_COMMAND_REFS
    assert tuple(material["target_test_command_refs"]) == mn.P7_R54_AHR_POST_EX18_MN09_TARGET_TEST_COMMAND_REFS
    assert tuple(material["selected_regression_command_refs"]) == mn.P7_R54_AHR_POST_EX18_MN09_SELECTED_REGRESSION_COMMAND_REFS
    assert tuple(material["compileall_command_refs"]) == mn.P7_R54_AHR_POST_EX18_MN09_COMPILEALL_COMMAND_REFS
    assert tuple(material["result_memo_required_section_refs"]) == mn.P7_R54_AHR_POST_EX18_MN09_RESULT_MEMO_REQUIRED_SECTION_REFS
    assert tuple(material["not_claimed_boundary_refs_for_result_memo"]) == mn.P7_R54_AHR_POST_EX18_MN09_NOT_CLAIMED_BOUNDARY_REFS
    assert tuple(material["no_green_to_product_claim_refs"]) == mn.P7_R54_AHR_POST_EX18_MN09_NO_GREEN_TO_PRODUCT_CLAIM_REFS
    for row in material["validation_command_rows"]:
        assert row["ran_here"] is False
        assert row["green_claimed_by_helper"] is False
        assert row["actual_human_review_complete_claimed"] is False
        assert row["p8_start_claimed"] is False
        assert row["r52_actual_execution_claimed"] is False
        assert row["release_allowed_claimed"] is False
        assert row["body_free"] is True
    assert material["validation_matrix_does_not_claim_actual_human_review_complete"] is True
    assert material["validation_matrix_does_not_claim_actual_review_operation_executed"] is True
    assert material["validation_matrix_does_not_claim_actual_rows_created"] is True
    assert material["validation_matrix_does_not_claim_full_backend_suite_green"] is True
    assert material["validation_matrix_does_not_claim_p5_p6_p8_r52_p7_release"] is True
    assert material["result_memo_envelope_does_not_copy_body_or_question_text"] is True
    assert material["next_required_step"] == mn.P7_R54_AHR_POST_EX18_MN10_STEP_REF
    assert mn.assert_p7_r54_ahr_post_ex18_mn09_validation_command_matrix_result_memo_envelope_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_mn09_blocks_when_mn08_reentry_mapping_is_not_ready() -> None:
    blocked_mn08 = mn.build_p7_r54_ahr_post_ex18_mn08_reentry_mapping_to_existing_postcr22_ex07_ex18(
        downstream_no_promotion_boundary_materialization=None
    )
    material = mn.build_p7_r54_ahr_post_ex18_mn09_validation_command_matrix_result_memo_envelope(
        reentry_mapping_to_existing_postcr22_ex07_ex18=blocked_mn08
    )

    assert material["mn09_status_ref"] == mn.P7_R54_AHR_POST_EX18_MN09_BLOCKED_STATUS_REF
    assert material["mn09_ready"] is False
    assert "mn08_reentry_mapping_not_ready" in material["mn09_blocker_refs"]
    assert material["validation_command_matrix_ready"] is False
    assert material["result_memo_envelope_ready"] is False
    assert material["next_required_step"] == mn.P7_R54_AHR_POST_EX18_MN09_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert mn.assert_p7_r54_ahr_post_ex18_mn09_validation_command_matrix_result_memo_envelope_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_mn09_contract_rejects_validation_green_or_body_question_key_mutation() -> None:
    material = mn.build_p7_r54_ahr_post_ex18_mn09_validation_command_matrix_result_memo_envelope(
        reentry_mapping_to_existing_postcr22_ex07_ex18=_ready_mn08()
    )

    mutated = deepcopy(material)
    mutated["validation_command_rows"][0]["green_claimed_by_helper"] = True
    with pytest.raises(ValueError):
        mn.assert_p7_r54_ahr_post_ex18_mn09_validation_command_matrix_result_memo_envelope_contract(mutated)

    mutated = deepcopy(material)
    mutated["validation_command_rows"][1]["actual_human_review_complete_claimed"] = True
    with pytest.raises(ValueError):
        mn.assert_p7_r54_ahr_post_ex18_mn09_validation_command_matrix_result_memo_envelope_contract(mutated)

    mutated = deepcopy(material)
    mutated["question_text"] = "mutated question"
    with pytest.raises(ValueError):
        mn.assert_p7_r54_ahr_post_ex18_mn09_validation_command_matrix_result_memo_envelope_contract(mutated)


def test_mn08_mn09_aliases_match_primary_builders_and_contracts() -> None:
    mn07 = _ready_mn07()
    primary_mn08 = mn.build_p7_r54_ahr_post_ex18_mn08_reentry_mapping_to_existing_postcr22_ex07_ex18(
        downstream_no_promotion_boundary_materialization=mn07
    )
    alias_mn08 = mn.build_p7_r54_ahr_post_ex18_manual_next_decision_reentry_mapping_to_existing_postcr22_ex07_ex18_bodyfree(
        downstream_no_promotion_boundary_materialization=mn07
    )
    assert alias_mn08 == primary_mn08
    assert mn.assert_p7_r54_ahr_post_ex18_manual_next_decision_reentry_mapping_to_existing_postcr22_ex07_ex18_bodyfree_contract(alias_mn08) is True

    primary_mn09 = mn.build_p7_r54_ahr_post_ex18_mn09_validation_command_matrix_result_memo_envelope(
        reentry_mapping_to_existing_postcr22_ex07_ex18=primary_mn08
    )
    alias_mn09 = mn.build_p7_r54_ahr_post_ex18_manual_next_decision_validation_command_matrix_result_memo_envelope_bodyfree(
        reentry_mapping_to_existing_postcr22_ex07_ex18=primary_mn08
    )
    assert alias_mn09 == primary_mn09
    assert mn.assert_p7_r54_ahr_post_ex18_manual_next_decision_validation_command_matrix_result_memo_envelope_bodyfree_contract(alias_mn09) is True
