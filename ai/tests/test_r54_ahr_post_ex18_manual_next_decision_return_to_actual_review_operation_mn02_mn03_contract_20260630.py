# -*- coding: utf-8 -*-
"""R54-AHR Post-EX18 manual next-decision MN02-MN03 contract tests."""

from __future__ import annotations

from copy import deepcopy

import pytest

import emlis_ai_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_20260629 as ex
import emlis_ai_p7_r54_ahr_post_ex18_manual_next_decision_return_to_actual_review_operation_20260630 as mn


def _assert_bodyfree_no_touch_no_promotion(material: dict[str, object], *, allowed_true_false_flags: set[str] | None = None) -> None:
    allowed = allowed_true_false_flags or set()
    assert material["body_free"] is True
    for key in mn.P7_R54_AHR_POST_EX18_REQUIRED_FALSE_FLAG_REFS:
        if key in allowed:
            assert material[key] is True, key
        else:
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
        "body_free_markers": {key: False for key in ex.P7_R54_AHR_POST_CR22_BODY_FREE_MARKER_REFS},
        "public_contract": {key: False for key in ("rn_visible_contract_changed", "api_response_key_added", "db_schema_changed", "public_release_applied")},
    }


def _valid_mn01() -> dict[str, object]:
    mn00 = mn.build_p7_r54_ahr_post_ex18_mn00_scope_no_touch_no_promotion_boundary_freeze()
    return mn.build_p7_r54_ahr_post_ex18_mn01_ex18_result_memo_bodyfree_envelope_intake(
        scope_no_touch_no_promotion_boundary_freeze=mn00,
        ex18_result_memo_bodyfree_envelope=_valid_ex18_bodyfree_envelope(),
    )


def _valid_actual_review_evidence_bundle() -> dict[str, object]:
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


def test_mn02_normalizes_missing_actual_review_evidence_as_return_required_state() -> None:
    material = mn.build_p7_r54_ahr_post_ex18_mn02_actual_review_evidence_state_normalization(ex18_result_memo_bodyfree_envelope_intake=_valid_mn01())

    assert set(material) == set(mn.P7_R54_AHR_POST_EX18_MN02_REQUIRED_FIELD_REFS)
    assert material["operation_step_ref"] == mn.P7_R54_AHR_POST_EX18_MN02_STEP_REF
    assert material["mn02_status_ref"] == mn.P7_R54_AHR_POST_EX18_MN02_READY_STATUS_REF
    assert material["actual_review_evidence_status_ref"] == mn.P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_EVIDENCE_MISSING_REAL_REVIEW_REQUIRED_REF
    assert material["actual_review_evidence_intake_bundle_present"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert material["actual_review_evidence_complete_by_actual_person_review_bodyfree"] is False
    assert material["ex18_contract_green_promoted_to_actual_complete"] is False
    assert material["actual_human_review_newly_run_here"] is False
    assert material["actual_selection_rows_created_here"] is False
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["next_required_step"] == mn.P7_R54_AHR_POST_EX18_MN03_STEP_REF
    assert mn.assert_p7_r54_ahr_post_ex18_mn02_actual_review_evidence_state_normalization_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_mn02_complete_actual_person_bodyfree_bundle_can_be_normalized_without_downstream_promotion() -> None:
    material = mn.build_p7_r54_ahr_post_ex18_mn02_actual_review_evidence_state_normalization(
        ex18_result_memo_bodyfree_envelope_intake=_valid_mn01(),
        actual_review_evidence_intake_bundle=_valid_actual_review_evidence_bundle(),
    )

    assert material["actual_review_evidence_status_ref"] == mn.P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_EVIDENCE_COMPLETE_BY_ACTUAL_PERSON_REVIEW_BODYFREE_REF
    assert material["actual_review_evidence_complete"] is True
    assert material["actual_review_evidence_complete_from_real_review"] is True
    assert material["all_required_counts_are_24"] is True
    assert material["p8_start_allowed"] is False
    assert material["r52_actual_execution_confirmed"] is False
    assert material["release_allowed"] is False
    assert mn.assert_p7_r54_ahr_post_ex18_mn02_actual_review_evidence_state_normalization_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material, allowed_true_false_flags={"actual_review_evidence_complete", "actual_review_evidence_complete_from_real_review"})


@pytest.mark.parametrize(
    ("field", "expected_ref"),
    (
        ("row_created_by_helper", "mn02_helper_created_rows_cannot_be_actual_evidence"),
        ("row_created_for_unit_test", "mn02_unit_test_rows_cannot_be_actual_evidence"),
        ("row_is_synthetic_contract_fixture", "mn02_synthetic_contract_fixture_rows_cannot_be_actual_evidence"),
        ("historical_row_reused", "mn02_historical_rows_cannot_be_reused_as_current_actual_evidence"),
    ),
)
def test_mn02_rejects_helper_unit_synthetic_or_historical_rows_as_actual_evidence(field: str, expected_ref: str) -> None:
    bundle = _valid_actual_review_evidence_bundle()
    bundle[field] = True
    material = mn.build_p7_r54_ahr_post_ex18_mn02_actual_review_evidence_state_normalization(
        ex18_result_memo_bodyfree_envelope_intake=_valid_mn01(),
        actual_review_evidence_intake_bundle=bundle,
    )

    assert material["mn02_ready"] is False
    assert material["actual_review_evidence_status_ref"] == mn.P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_EVIDENCE_INVALID_SOURCE_DETECTED_REF
    assert expected_ref in material["actual_review_evidence_intake_bundle_invalid_source_refs"]
    assert material["actual_review_evidence_complete"] is False
    assert material["next_required_step"] == mn.P7_R54_AHR_POST_EX18_MN02_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert mn.assert_p7_r54_ahr_post_ex18_mn02_actual_review_evidence_state_normalization_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_mn02_flags_forbidden_body_question_path_hash_without_copying_payload() -> None:
    bundle = _valid_actual_review_evidence_bundle()
    bundle["question_text"] = "do not copy this"
    bundle["local_absolute_path"] = "/tmp/do-not-copy"
    material = mn.build_p7_r54_ahr_post_ex18_mn02_actual_review_evidence_state_normalization(
        ex18_result_memo_bodyfree_envelope_intake=_valid_mn01(),
        actual_review_evidence_intake_bundle=bundle,
    )

    assert material["mn02_ready"] is False
    assert material["actual_review_evidence_status_ref"] == mn.P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_EVIDENCE_INVALID_SOURCE_DETECTED_REF
    assert material["actual_review_evidence_intake_bundle_forbidden_payload_key_path_count"] == 2
    assert "question_text" not in material
    assert "local_absolute_path" not in material
    assert material["actual_review_evidence_complete"] is False
    assert mn.assert_p7_r54_ahr_post_ex18_mn02_actual_review_evidence_state_normalization_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_mn03_classifies_current_missing_evidence_as_return_to_actual_review_operation_required() -> None:
    mn02 = mn.build_p7_r54_ahr_post_ex18_mn02_actual_review_evidence_state_normalization(ex18_result_memo_bodyfree_envelope_intake=_valid_mn01())
    material = mn.build_p7_r54_ahr_post_ex18_mn03_manual_decision_classifier(actual_review_evidence_state_normalization=mn02)

    assert set(material) == set(mn.P7_R54_AHR_POST_EX18_MN03_REQUIRED_FIELD_REFS)
    assert material["manual_decision_ref"] == mn.P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_RETURN_OPERATION_REQUIRED_REF
    assert material["manual_decision_ready"] is True
    assert material["return_to_actual_review_operation_required"] is True
    assert material["manual_decision_classifier_run_here"] is True
    assert material["manual_decision_auto_executes_downstream"] is False
    assert material["next_decision_auto_execution_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == mn.P7_R54_AHR_POST_EX18_MN03_RETURN_NEXT_REQUIRED_STEP_REF
    assert mn.assert_p7_r54_ahr_post_ex18_mn03_manual_decision_classifier_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material, allowed_true_false_flags={"manual_decision_classifier_run_here"})


def test_mn03_classifies_body_leak_stop_before_return_operation() -> None:
    bundle = _valid_actual_review_evidence_bundle()
    bundle["raw_input"] = "do not copy this"
    mn02 = mn.build_p7_r54_ahr_post_ex18_mn02_actual_review_evidence_state_normalization(ex18_result_memo_bodyfree_envelope_intake=_valid_mn01(), actual_review_evidence_intake_bundle=bundle)
    material = mn.build_p7_r54_ahr_post_ex18_mn03_manual_decision_classifier(actual_review_evidence_state_normalization=mn02)

    assert material["manual_decision_ref"] == mn.P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_STOP_BODY_LEAK_REF
    assert material["manual_decision_ready"] is False
    assert material["return_to_actual_review_operation_required"] is False
    assert material["next_required_step"] == mn.P7_R54_AHR_POST_EX18_MN03_STOP_BODY_LEAK_NEXT_REQUIRED_STEP_REF
    assert "raw_input" not in material
    assert mn.assert_p7_r54_ahr_post_ex18_mn03_manual_decision_classifier_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material, allowed_true_false_flags={"manual_decision_classifier_run_here"})


def test_mn03_classifies_promotion_claim_stop() -> None:
    bundle = _valid_actual_review_evidence_bundle()
    bundle["p8_start_allowed"] = True
    mn02 = mn.build_p7_r54_ahr_post_ex18_mn02_actual_review_evidence_state_normalization(ex18_result_memo_bodyfree_envelope_intake=_valid_mn01(), actual_review_evidence_intake_bundle=bundle)
    material = mn.build_p7_r54_ahr_post_ex18_mn03_manual_decision_classifier(actual_review_evidence_state_normalization=mn02)

    assert material["manual_decision_ref"] == mn.P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_STOP_PROMOTION_CLAIM_REF
    assert material["manual_decision_ready"] is False
    assert material["return_to_actual_review_operation_required"] is False
    assert material["next_required_step"] == mn.P7_R54_AHR_POST_EX18_MN03_STOP_PROMOTION_NEXT_REQUIRED_STEP_REF
    assert material["p8_start_allowed"] is False
    assert mn.assert_p7_r54_ahr_post_ex18_mn03_manual_decision_classifier_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material, allowed_true_false_flags={"manual_decision_classifier_run_here"})


def test_mn03_classifies_ex18_or_mn02_invalid_as_hold() -> None:
    mn02 = mn.build_p7_r54_ahr_post_ex18_mn02_actual_review_evidence_state_normalization()
    material = mn.build_p7_r54_ahr_post_ex18_mn03_manual_decision_classifier(actual_review_evidence_state_normalization=mn02)

    assert material["manual_decision_ref"] == mn.P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_HOLD_EX18_INVALID_REF
    assert material["manual_decision_ready"] is False
    assert material["return_to_actual_review_operation_required"] is False
    assert material["next_required_step"] == mn.P7_R54_AHR_POST_EX18_MN03_HOLD_EX18_NEXT_REQUIRED_STEP_REF
    assert mn.assert_p7_r54_ahr_post_ex18_mn03_manual_decision_classifier_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material, allowed_true_false_flags={"manual_decision_classifier_run_here"})


def test_mn03_complete_evidence_requires_downstream_manual_decision_without_promotion() -> None:
    mn02 = mn.build_p7_r54_ahr_post_ex18_mn02_actual_review_evidence_state_normalization(
        ex18_result_memo_bodyfree_envelope_intake=_valid_mn01(),
        actual_review_evidence_intake_bundle=_valid_actual_review_evidence_bundle(),
    )
    material = mn.build_p7_r54_ahr_post_ex18_mn03_manual_decision_classifier(actual_review_evidence_state_normalization=mn02)

    assert material["manual_decision_ref"] == mn.P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_EVIDENCE_COMPLETE_DOWNSTREAM_MANUAL_REF
    assert material["manual_decision_ready"] is True
    assert material["return_to_actual_review_operation_required"] is False
    assert material["downstream_manual_decision_required"] is True
    assert material["actual_review_evidence_complete"] is True
    assert material["actual_review_evidence_complete_from_real_review"] is True
    assert material["manual_decision_auto_executes_downstream"] is False
    assert material["p5_final_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == mn.P7_R54_AHR_POST_EX18_MN03_DOWNSTREAM_MANUAL_NEXT_REQUIRED_STEP_REF
    assert mn.assert_p7_r54_ahr_post_ex18_mn03_manual_decision_classifier_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material, allowed_true_false_flags={"manual_decision_classifier_run_here", "actual_review_evidence_complete", "actual_review_evidence_complete_from_real_review"})


def test_mn02_mn03_aliases_match_primary_builders_and_contracts() -> None:
    mn01 = _valid_mn01()
    mn02 = mn.build_p7_r54_ahr_post_ex18_manual_next_decision_actual_review_evidence_state_normalization_bodyfree(ex18_result_memo_bodyfree_envelope_intake=mn01)
    primary_mn02 = mn.build_p7_r54_ahr_post_ex18_mn02_actual_review_evidence_state_normalization(ex18_result_memo_bodyfree_envelope_intake=mn01)
    assert mn02 == primary_mn02
    assert mn.assert_p7_r54_ahr_post_ex18_manual_next_decision_actual_review_evidence_state_normalization_bodyfree_contract(mn02) is True

    mn03 = mn.build_p7_r54_ahr_post_ex18_manual_next_decision_classifier_bodyfree(actual_review_evidence_state_normalization=mn02)
    primary_mn03 = mn.build_p7_r54_ahr_post_ex18_mn03_manual_decision_classifier(actual_review_evidence_state_normalization=mn02)
    assert mn03 == primary_mn03
    assert mn.assert_p7_r54_ahr_post_ex18_manual_next_decision_classifier_bodyfree_contract(mn03) is True


def test_mn03_contract_rejects_output_promotion_or_auto_execution_mutation() -> None:
    mn02 = mn.build_p7_r54_ahr_post_ex18_mn02_actual_review_evidence_state_normalization(ex18_result_memo_bodyfree_envelope_intake=_valid_mn01())
    material = mn.build_p7_r54_ahr_post_ex18_mn03_manual_decision_classifier(actual_review_evidence_state_normalization=mn02)

    mutated = deepcopy(material)
    mutated["p8_start_allowed"] = True
    with pytest.raises(ValueError):
        mn.assert_p7_r54_ahr_post_ex18_mn03_manual_decision_classifier_contract(mutated)

    mutated = deepcopy(material)
    mutated["manual_decision_auto_executes_downstream"] = True
    with pytest.raises(ValueError):
        mn.assert_p7_r54_ahr_post_ex18_mn03_manual_decision_classifier_contract(mutated)

    mutated = deepcopy(material)
    mutated["next_decision_auto_execution_allowed"] = True
    with pytest.raises(ValueError):
        mn.assert_p7_r54_ahr_post_ex18_mn03_manual_decision_classifier_contract(mutated)
