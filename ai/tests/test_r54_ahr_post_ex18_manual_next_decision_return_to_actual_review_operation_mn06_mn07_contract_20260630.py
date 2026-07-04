# -*- coding: utf-8 -*-
"""R54-AHR Post-EX18 manual next-decision MN06-MN07 contract tests."""

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


def test_mn06_scans_bodyfree_materials_without_copying_payload_values() -> None:
    material = _ready_mn06()

    assert set(material) == set(mn.P7_R54_AHR_POST_EX18_MN06_REQUIRED_FIELD_REFS)
    assert material["operation_step_ref"] == mn.P7_R54_AHR_POST_EX18_MN06_STEP_REF
    assert material["mn06_status_ref"] == mn.P7_R54_AHR_POST_EX18_MN06_READY_STATUS_REF
    assert material["mn06_ready"] is True
    assert material["detected_forbidden_payload_key_path_refs"] == []
    assert material["no_body_payload_key_detected"] is True
    assert material["no_question_payload_key_detected"] is True
    assert material["no_local_path_payload_key_detected"] is True
    assert material["no_hash_payload_key_detected"] is True
    assert material["no_body_no_question_no_path_no_hash_scan_passed"] is True
    assert material["no_payload_value_copied_to_scan_result"] is True
    assert material["scan_reports_key_paths_only"] is True
    assert material["actual_review_evidence_not_completed_by_scan"] is True
    assert material["actual_review_operation_not_run_by_scan"] is True
    assert material["actual_rows_not_created_by_scan"] is True
    assert material["next_required_step"] == mn.P7_R54_AHR_POST_EX18_MN07_STEP_REF
    assert mn.assert_p7_r54_ahr_post_ex18_mn06_no_body_no_question_no_path_no_hash_scan_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_mn06_blocks_for_body_question_path_hash_key_paths_without_copying_values() -> None:
    material = mn.build_p7_r54_ahr_post_ex18_mn06_no_body_no_question_no_path_no_hash_scan(
        expected_bodyfree_evidence_intake_bundle_boundary=_ready_mn05(),
        return_to_actual_review_operation_plan=_ready_mn04(),
        additional_bodyfree_scan_targets={
            "question_text": "do not copy this question",
            "body_hash": "do-not-copy-body-hash",
            "nested": {
                "local_path": "/tmp/do-not-copy-local-path",
                "returned_body": "do not copy returned body",
            },
        },
    )

    assert material["mn06_status_ref"] == mn.P7_R54_AHR_POST_EX18_MN06_BLOCKED_STATUS_REF
    assert material["mn06_ready"] is False
    assert "mn06_forbidden_body_question_path_hash_or_terminal_key_detected" in material["mn06_blocker_refs"]
    assert material["no_question_payload_key_detected"] is False
    assert material["no_local_path_payload_key_detected"] is False
    assert material["no_hash_payload_key_detected"] is False
    assert material["no_body_no_question_no_path_no_hash_scan_passed"] is False
    assert any(path.endswith(".question_text") for path in material["detected_forbidden_payload_key_path_refs"])
    assert any(path.endswith(".body_hash") for path in material["detected_forbidden_payload_key_path_refs"])
    assert any(path.endswith(".nested.local_path") for path in material["detected_forbidden_payload_key_path_refs"])
    material_text = str(material)
    assert "do not copy this question" not in material_text
    assert "do-not-copy-body-hash" not in material_text
    assert "/tmp/do-not-copy-local-path" not in material_text
    assert "do not copy returned body" not in material_text
    assert mn.assert_p7_r54_ahr_post_ex18_mn06_no_body_no_question_no_path_no_hash_scan_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_mn06_contract_rejects_top_level_forbidden_payload_key_mutation() -> None:
    material = _ready_mn06()

    mutated = deepcopy(material)
    mutated["question_text"] = "mutated question"
    with pytest.raises(ValueError):
        mn.assert_p7_r54_ahr_post_ex18_mn06_no_body_no_question_no_path_no_hash_scan_contract(mutated)

    mutated = deepcopy(material)
    mutated["next_decision_auto_execution_allowed"] = True
    with pytest.raises(ValueError):
        mn.assert_p7_r54_ahr_post_ex18_mn06_no_body_no_question_no_path_no_hash_scan_contract(mutated)


def test_mn07_materializes_downstream_no_promotion_boundary_from_ready_mn06() -> None:
    material = mn.build_p7_r54_ahr_post_ex18_mn07_downstream_no_promotion_boundary_materialization(
        no_body_no_question_no_path_no_hash_scan=_ready_mn06()
    )

    assert set(material) == set(mn.P7_R54_AHR_POST_EX18_MN07_REQUIRED_FIELD_REFS)
    assert material["operation_step_ref"] == mn.P7_R54_AHR_POST_EX18_MN07_STEP_REF
    assert material["mn07_status_ref"] == mn.P7_R54_AHR_POST_EX18_MN07_READY_STATUS_REF
    assert material["mn07_ready"] is True
    assert material["downstream_no_promotion_boundary_materialized"] is True
    assert material["no_promotion_boundary_confirmed"] is True
    assert material["p5_p6_p8_r52_release_auto_execution_blocked"] is True
    assert tuple(material["downstream_no_promotion_flag_refs"]) == mn.P7_R54_AHR_POST_EX18_MN07_NO_PROMOTION_FLAG_REFS
    assert all(value is False for value in material["downstream_no_promotion_boundary"].values())
    for flag in mn.P7_R54_AHR_POST_EX18_MN07_NO_PROMOTION_FLAG_REFS:
        assert material[flag] is False, flag
    assert material["p8_material_candidate_only_is_not_p8_start_allowed"] is True
    assert material["r52_handoff_candidate_is_not_r52_actual_execution"] is True
    assert material["p5_confirmed_candidate_is_not_p5_final"] is True
    assert material["selected_regression_green_is_not_full_backend_suite_green"] is True
    assert material["rn_contract_green_is_not_rn_real_device_modal_verified"] is True
    assert material["next_required_step"] == mn.P7_R54_AHR_POST_EX18_MN08_STEP_REF
    assert mn.assert_p7_r54_ahr_post_ex18_mn07_downstream_no_promotion_boundary_materialization_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_mn07_blocks_when_mn06_scan_is_blocked() -> None:
    blocked_mn06 = mn.build_p7_r54_ahr_post_ex18_mn06_no_body_no_question_no_path_no_hash_scan(
        expected_bodyfree_evidence_intake_bundle_boundary=_ready_mn05(),
        additional_bodyfree_scan_targets={"draft_question_text": "do not copy draft"},
    )
    material = mn.build_p7_r54_ahr_post_ex18_mn07_downstream_no_promotion_boundary_materialization(
        no_body_no_question_no_path_no_hash_scan=blocked_mn06
    )

    assert material["mn07_status_ref"] == mn.P7_R54_AHR_POST_EX18_MN07_BLOCKED_STATUS_REF
    assert material["mn07_ready"] is False
    assert "mn06_no_body_no_question_no_path_no_hash_scan_not_ready" in material["mn07_blocker_refs"]
    assert material["downstream_no_promotion_boundary_materialized"] is False
    assert material["no_promotion_boundary_confirmed"] is False
    assert material["next_required_step"] == mn.P7_R54_AHR_POST_EX18_MN07_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert "do not copy draft" not in str(material)
    assert mn.assert_p7_r54_ahr_post_ex18_mn07_downstream_no_promotion_boundary_materialization_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_mn07_blocks_explicit_downstream_promotion_claims_without_promoting_output_flags() -> None:
    material = mn.build_p7_r54_ahr_post_ex18_mn07_downstream_no_promotion_boundary_materialization(
        no_body_no_question_no_path_no_hash_scan=_ready_mn06(),
        downstream_promotion_claims={"p8_start_allowed": True, "release_allowed": True},
    )

    assert material["mn07_status_ref"] == mn.P7_R54_AHR_POST_EX18_MN07_BLOCKED_STATUS_REF
    assert "mn07_downstream_promotion_claim_detected" in material["mn07_blocker_refs"]
    assert tuple(material["promotion_claim_refs"]) == ("p8_start_allowed", "release_allowed")
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == mn.P7_R54_AHR_POST_EX18_MN07_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert mn.assert_p7_r54_ahr_post_ex18_mn07_downstream_no_promotion_boundary_materialization_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_mn07_contract_rejects_p8_or_release_promotion_mutation() -> None:
    material = mn.build_p7_r54_ahr_post_ex18_mn07_downstream_no_promotion_boundary_materialization(
        no_body_no_question_no_path_no_hash_scan=_ready_mn06()
    )

    mutated = deepcopy(material)
    mutated["p8_start_allowed"] = True
    with pytest.raises(ValueError):
        mn.assert_p7_r54_ahr_post_ex18_mn07_downstream_no_promotion_boundary_materialization_contract(mutated)

    mutated = deepcopy(material)
    mutated["release_allowed"] = True
    with pytest.raises(ValueError):
        mn.assert_p7_r54_ahr_post_ex18_mn07_downstream_no_promotion_boundary_materialization_contract(mutated)


def test_mn06_mn07_aliases_match_primary_builders_and_contracts() -> None:
    mn05 = _ready_mn05()
    primary_mn06 = mn.build_p7_r54_ahr_post_ex18_mn06_no_body_no_question_no_path_no_hash_scan(
        expected_bodyfree_evidence_intake_bundle_boundary=mn05
    )
    alias_mn06 = mn.build_p7_r54_ahr_post_ex18_manual_next_decision_no_body_no_question_no_path_no_hash_scan_bodyfree(
        expected_bodyfree_evidence_intake_bundle_boundary=mn05
    )
    assert alias_mn06 == primary_mn06
    assert mn.assert_p7_r54_ahr_post_ex18_manual_next_decision_no_body_no_question_no_path_no_hash_scan_bodyfree_contract(alias_mn06) is True

    primary_mn07 = mn.build_p7_r54_ahr_post_ex18_mn07_downstream_no_promotion_boundary_materialization(
        no_body_no_question_no_path_no_hash_scan=primary_mn06
    )
    alias_mn07 = mn.build_p7_r54_ahr_post_ex18_manual_next_decision_downstream_no_promotion_boundary_materialization_bodyfree(
        no_body_no_question_no_path_no_hash_scan=primary_mn06
    )
    assert alias_mn07 == primary_mn07
    assert mn.assert_p7_r54_ahr_post_ex18_manual_next_decision_downstream_no_promotion_boundary_materialization_bodyfree_contract(alias_mn07) is True
