# -*- coding: utf-8 -*-
"""R54-AHR Post-EX18 manual next-decision MN00-MN01 tests."""

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
        "body_free_markers": {key: False for key in ex.P7_R54_AHR_POST_CR22_BODY_FREE_MARKER_REFS},
        "public_contract": {key: False for key in ("rn_visible_contract_changed", "api_response_key_added", "db_schema_changed", "public_release_applied")},
    }


def test_mn00_freezes_scope_no_touch_and_no_promotion_boundary() -> None:
    material = mn.build_p7_r54_ahr_post_ex18_mn00_scope_no_touch_no_promotion_boundary_freeze()

    assert set(material) == set(mn.P7_R54_AHR_POST_EX18_MN00_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == mn.P7_R54_AHR_POST_EX18_MN00_SCOPE_NO_TOUCH_NO_PROMOTION_BOUNDARY_FREEZE_SCHEMA_VERSION
    assert material["operation_step_ref"] == mn.P7_R54_AHR_POST_EX18_MN00_STEP_REF
    assert material["post_ex18_manual_next_decision_scope_confirmed"] is True
    assert material["return_to_actual_review_operation_design_scope"] is True
    assert material["no_touch_boundary_confirmed"] is True
    assert material["no_promotion_boundary_confirmed"] is True
    assert material["p8_question_design_out_of_scope"] is True
    assert material["p8_question_implementation_out_of_scope"] is True
    assert material["r52_actual_execution_out_of_scope"] is True
    assert material["p5_finalization_out_of_scope"] is True
    assert material["p6_start_out_of_scope"] is True
    assert material["p7_completion_out_of_scope"] is True
    assert material["release_decision_out_of_scope"] is True
    assert material["local_received_zip_refs_are_actual_review_basis"] is False
    assert material["local_received_zip_refs_used_to_rewrite_current_actual_review_basis"] is False
    assert material["actual_review_basis_ref"] == "current_received_snapshot_264_85_258_171"
    assert tuple(material["implemented_steps"]) == mn.P7_R54_AHR_POST_EX18_MN00_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == mn.P7_R54_AHR_POST_EX18_MN00_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == mn.P7_R54_AHR_POST_EX18_MN01_STEP_REF
    assert mn.assert_p7_r54_ahr_post_ex18_mn00_scope_no_touch_no_promotion_boundary_freeze_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    (
        ("api_changed", True),
        ("p8_question_design_started", True),
        ("p8_start_allowed", True),
        ("actual_r52_reintake_execution_confirmed", True),
        ("release_allowed", True),
    ),
)
def test_mn00_contract_rejects_touch_or_promotion_mutation(field: str, bad_value: object) -> None:
    material = mn.build_p7_r54_ahr_post_ex18_mn00_scope_no_touch_no_promotion_boundary_freeze()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        mn.assert_p7_r54_ahr_post_ex18_mn00_scope_no_touch_no_promotion_boundary_freeze_contract(mutated)

    mutated = deepcopy(material)
    mutated["post_ex18_no_touch_contract"] = dict(mutated["post_ex18_no_touch_contract"])
    mutated["post_ex18_no_touch_contract"]["db_schema_changed"] = True
    with pytest.raises(ValueError):
        mn.assert_p7_r54_ahr_post_ex18_mn00_scope_no_touch_no_promotion_boundary_freeze_contract(mutated)


def test_mn01_blocks_without_ex18_bodyfree_envelope_and_keeps_boundary() -> None:
    material = mn.build_p7_r54_ahr_post_ex18_mn01_ex18_result_memo_bodyfree_envelope_intake()

    assert set(material) == set(mn.P7_R54_AHR_POST_EX18_MN01_REQUIRED_FIELD_REFS)
    assert material["mn01_status_ref"] == mn.P7_R54_AHR_POST_EX18_MN01_BLOCKED_STATUS_REF
    assert material["mn01_ready"] is False
    assert "mn01_ex18_bodyfree_envelope_missing" in material["mn01_blocker_refs"]
    assert material["mn01_passes_to_actual_review_evidence_state_normalization"] is False
    assert material["mn01_return_to_actual_review_operation_candidate_only"] is False
    assert tuple(material["implemented_steps"]) == mn.P7_R54_AHR_POST_EX18_MN00_IMPLEMENTED_STEPS
    assert material["next_required_step"] == mn.P7_R54_AHR_POST_EX18_MN01_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert mn.assert_p7_r54_ahr_post_ex18_mn01_ex18_result_memo_bodyfree_envelope_intake_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_mn01_accepts_ex18_manual_hold_envelope_without_downstream_promotion() -> None:
    mn00 = mn.build_p7_r54_ahr_post_ex18_mn00_scope_no_touch_no_promotion_boundary_freeze()
    material = mn.build_p7_r54_ahr_post_ex18_mn01_ex18_result_memo_bodyfree_envelope_intake(
        scope_no_touch_no_promotion_boundary_freeze=mn00,
        ex18_result_memo_bodyfree_envelope=_valid_ex18_bodyfree_envelope(),
    )

    assert material["mn01_status_ref"] == mn.P7_R54_AHR_POST_EX18_MN01_READY_STATUS_REF
    assert material["mn01_ready"] is True
    assert material["mn01_blocker_refs"] == []
    assert material["ex18_result_memo_ref"] == mn.P7_R54_AHR_POST_EX18_EX18_RESULT_MEMO_REF
    assert material["ex18_bodyfree_envelope_present"] is True
    assert material["ex18_envelope_operation_step_ref"] == ex.P7_R54_AHR_POST_CR22_EX18_STEP_REF
    assert material["ex18_next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX18_NEXT_DECISION_HOLD_REF
    assert material["ex18_next_decision_hold_required"] is True
    assert material["ex18_actual_review_evidence_complete_reported_by_contract"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert material["ex18_actual_human_review_run_here_reported"] is False
    assert material["ex18_actual_human_review_complete_reported"] is False
    assert material["mn01_return_to_actual_review_operation_candidate_only"] is True
    assert material["mn01_return_to_actual_review_operation_candidate_ref"] == mn.P7_R54_AHR_POST_EX18_MN01_RETURN_OPERATION_CANDIDATE_REF
    assert material["mn01_does_not_normalize_actual_review_evidence_state"] is True
    assert material["mn01_does_not_run_manual_decision_classifier"] is True
    assert material["manual_decision_classifier_run_here"] is False
    assert tuple(material["implemented_steps"]) == mn.P7_R54_AHR_POST_EX18_MN01_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == mn.P7_R54_AHR_POST_EX18_MN01_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == mn.P7_R54_AHR_POST_EX18_MN02_STEP_REF
    assert mn.assert_p7_r54_ahr_post_ex18_mn01_ex18_result_memo_bodyfree_envelope_intake_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value", "expected_blocker"),
    (
        ("next_required_step", ex.P7_R54_AHR_POST_CR22_EX17_STEP_REF, "mn01_ex18_next_required_step_is_not_manual_hold"),
        ("next_decision_hold_required", False, "mn01_ex18_next_decision_hold_not_required"),
        ("next_decision_auto_execution_allowed", True, "mn01_ex18_next_decision_auto_execution_claimed"),
        ("actual_human_review_run_here", True, "mn01_ex18_actual_human_review_run_claim_detected"),
        ("actual_human_review_complete", True, "mn01_ex18_actual_human_review_complete_claim_detected"),
        ("actual_selection_rows_created_here", True, "mn01_ex18_actual_selection_rows_created_here_claim_detected"),
        ("p8_start_allowed", True, "mn01_ex18_promotion_or_downstream_claim_detected"),
        ("release_allowed", True, "mn01_ex18_promotion_or_downstream_claim_detected"),
    ),
)
def test_mn01_blocks_invalid_ex18_hold_or_promotion_claims(field: str, bad_value: object, expected_blocker: str) -> None:
    envelope = _valid_ex18_bodyfree_envelope()
    envelope[field] = bad_value
    material = mn.build_p7_r54_ahr_post_ex18_mn01_ex18_result_memo_bodyfree_envelope_intake(
        ex18_result_memo_bodyfree_envelope=envelope,
    )

    assert material["mn01_ready"] is False
    assert expected_blocker in material["mn01_blocker_refs"]
    assert material["mn01_passes_to_actual_review_evidence_state_normalization"] is False
    assert material["next_required_step"] == mn.P7_R54_AHR_POST_EX18_MN01_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert mn.assert_p7_r54_ahr_post_ex18_mn01_ex18_result_memo_bodyfree_envelope_intake_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_mn01_blocks_forbidden_body_question_path_hash_keys_without_copying_payload() -> None:
    envelope = _valid_ex18_bodyfree_envelope()
    envelope["question_text"] = "do not copy this"
    envelope["local_absolute_path"] = "/tmp/do-not-copy"
    material = mn.build_p7_r54_ahr_post_ex18_mn01_ex18_result_memo_bodyfree_envelope_intake(
        ex18_result_memo_bodyfree_envelope=envelope,
    )

    assert material["mn01_ready"] is False
    assert "mn01_ex18_envelope_forbidden_body_question_path_hash_key_detected" in material["mn01_blocker_refs"]
    assert material["ex18_forbidden_payload_key_path_count"] == 2
    assert "question_text" not in material
    assert "local_absolute_path" not in material
    assert mn.assert_p7_r54_ahr_post_ex18_mn01_ex18_result_memo_bodyfree_envelope_intake_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_mn01_contract_rejects_output_promotion_mutation() -> None:
    material = mn.build_p7_r54_ahr_post_ex18_mn01_ex18_result_memo_bodyfree_envelope_intake(
        ex18_result_memo_bodyfree_envelope=_valid_ex18_bodyfree_envelope(),
    )

    mutated = deepcopy(material)
    mutated["p8_start_allowed"] = True
    with pytest.raises(ValueError):
        mn.assert_p7_r54_ahr_post_ex18_mn01_ex18_result_memo_bodyfree_envelope_intake_contract(mutated)

    mutated = deepcopy(material)
    mutated["ex18_next_decision_auto_execution_allowed"] = True
    with pytest.raises(ValueError):
        mn.assert_p7_r54_ahr_post_ex18_mn01_ex18_result_memo_bodyfree_envelope_intake_contract(mutated)

    mutated = deepcopy(material)
    mutated["actual_review_evidence_complete"] = True
    with pytest.raises(ValueError):
        mn.assert_p7_r54_ahr_post_ex18_mn01_ex18_result_memo_bodyfree_envelope_intake_contract(mutated)


def test_mn00_mn01_aliases_match_primary_builders_and_contracts() -> None:
    mn00 = mn.build_p7_r54_ahr_post_ex18_manual_next_decision_scope_no_touch_no_promotion_boundary_freeze_bodyfree()
    assert mn00 == mn.build_p7_r54_ahr_post_ex18_mn00_scope_no_touch_no_promotion_boundary_freeze()
    assert mn.assert_p7_r54_ahr_post_ex18_manual_next_decision_scope_no_touch_no_promotion_boundary_freeze_bodyfree_contract(mn00) is True

    mn01 = mn.build_p7_r54_ahr_post_ex18_manual_next_decision_ex18_result_memo_bodyfree_envelope_intake_bodyfree(
        scope_no_touch_no_promotion_boundary_freeze=mn00,
        ex18_result_memo_bodyfree_envelope=_valid_ex18_bodyfree_envelope(),
    )
    primary = mn.build_p7_r54_ahr_post_ex18_mn01_ex18_result_memo_bodyfree_envelope_intake(
        scope_no_touch_no_promotion_boundary_freeze=mn00,
        ex18_result_memo_bodyfree_envelope=_valid_ex18_bodyfree_envelope(),
    )
    assert mn01 == primary
    assert mn.assert_p7_r54_ahr_post_ex18_manual_next_decision_ex18_result_memo_bodyfree_envelope_intake_bodyfree_contract(mn01) is True
