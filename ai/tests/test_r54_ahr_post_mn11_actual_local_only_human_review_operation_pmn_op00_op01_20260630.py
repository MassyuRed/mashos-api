# -*- coding: utf-8 -*-
"""R54-AHR Post-MN11 actual local-only human review operation PMN-OP00/OP01 tests."""

from __future__ import annotations

from copy import deepcopy

import pytest

import emlis_ai_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_20260629 as ex
import emlis_ai_p7_r54_ahr_post_ex18_manual_next_decision_return_to_actual_review_operation_20260630 as mn
import emlis_ai_p7_r54_ahr_post_mn11_actual_local_only_human_review_operation_20260630 as pmn


def _assert_bodyfree_no_touch_no_promotion(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    for key in pmn.P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS:
        assert material[key] is False, key
    for marker_map_key in ("public_contract", "post_mn11_no_touch_contract", "body_free_markers"):
        assert material[marker_map_key]
        assert all(value is False for value in material[marker_map_key].values()), marker_map_key
    for forbidden_key in pmn.P7_R54_AHR_POST_MN11_FORBIDDEN_PAYLOAD_KEY_REFS:
        assert forbidden_key not in material, forbidden_key
    assert all(value is False for value in material["not_claimed_boundary"].values())


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


def _ready_mn11() -> dict[str, object]:
    return mn.build_p7_r54_ahr_post_ex18_mn11_acceptance_fail_closed_finalizer(
        alias_contract_function_boundary=_ready_mn10()
    )


def test_pmn_op00_freezes_post_mn11_scope_no_touch_and_no_promotion_boundary() -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op00_scope_no_touch_no_promotion_boundary_freeze()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP00_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP00_SCOPE_NO_TOUCH_NO_PROMOTION_BOUNDARY_FREEZE_SCHEMA_VERSION
    assert material["phase"].startswith("P7_")
    assert material["operation_step_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP00_STEP_REF
    assert material["source_mode"] == "local_snapshot"
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["chosen_stage_ref"] == pmn.P7_R54_AHR_POST_MN11_CHOSEN_STAGE_REF
    assert tuple(material["not_stage_refs"]) == pmn.P7_R54_AHR_POST_MN11_NOT_STAGE_REFS
    assert material["post_mn11_actual_operation_scope_confirmed"] is True
    assert material["post_mn11_actual_operation_evidence_intake_reentry_scope"] is True
    assert material["no_touch_boundary_confirmed"] is True
    assert material["no_promotion_boundary_confirmed"] is True
    assert material["p8_question_design_out_of_scope"] is True
    assert material["p8_question_implementation_out_of_scope"] is True
    assert material["p6_start_out_of_scope"] is True
    assert material["r52_actual_execution_out_of_scope"] is True
    assert material["p5_finalization_out_of_scope"] is True
    assert material["p7_complete_out_of_scope"] is True
    assert material["release_decision_out_of_scope"] is True
    assert material["required_case_count"] == 24
    assert material["actual_review_basis_ref"] == "current_received_snapshot_264_85_258_171"
    assert material["local_received_zip_refs_are_actual_review_basis"] is False
    assert material["local_received_zip_refs_used_to_rewrite_current_actual_review_basis"] is False
    assert material["local_received_zip_refs"]["backend_zip_ref"] == "mashos-api(174).zip"
    assert tuple(material["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP00_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP00_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP01_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op00_scope_no_touch_no_promotion_boundary_freeze_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    (
        ("api_changed", True),
        ("p8_question_design_started", True),
        ("p8_question_implementation_started", True),
        ("actual_body_full_packet_generated_here", True),
        ("actual_human_review_run_here", True),
        ("actual_review_evidence_complete_from_real_review", True),
        ("p5_final_allowed", True),
        ("p6_start_allowed", True),
        ("p8_start_allowed", True),
        ("r52_actual_execution_confirmed", True),
        ("p7_complete", True),
        ("release_allowed", True),
    ),
)
def test_pmn_op00_contract_rejects_touch_actual_review_or_promotion_mutation(field: str, bad_value: object) -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op00_scope_no_touch_no_promotion_boundary_freeze()
    material[field] = bad_value
    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op00_scope_no_touch_no_promotion_boundary_freeze_contract(material)


def test_pmn_op00_contract_rejects_basis_rewrite_to_latest_zip_label() -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op00_scope_no_touch_no_promotion_boundary_freeze()
    material["local_received_zip_refs_are_actual_review_basis"] = True
    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op00_scope_no_touch_no_promotion_boundary_freeze_contract(material)

    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op00_scope_no_touch_no_promotion_boundary_freeze()
    material["actual_review_basis_ref"] = "mashos-api(174).zip"
    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op00_scope_no_touch_no_promotion_boundary_freeze_contract(material)


def test_pmn_op01_blocks_without_mn11_manual_decision_material_and_keeps_op00_boundary() -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op01_mn11_manual_decision_intake_basis_confirmation()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP01_REQUIRED_FIELD_REFS)
    assert material["pmn_op01_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP01_BLOCKED_STATUS_REF
    assert material["pmn_op01_ready"] is False
    assert "pmn_op01_mn11_manual_decision_envelope_missing" in material["pmn_op01_blocker_refs"]
    assert material["pmn_op01_passes_to_existing_support_material_inventory"] is False
    assert material["actual_local_only_human_review_operation_required_before_downstream_decision"] is False
    assert tuple(material["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP00_IMPLEMENTED_STEPS
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP01_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op01_mn11_manual_decision_intake_basis_confirmation_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op01_accepts_ready_mn11_return_operation_required_without_promoting_to_actual_review_complete() -> None:
    op00 = pmn.build_p7_r54_ahr_post_mn11_pmn_op00_scope_no_touch_no_promotion_boundary_freeze()
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op01_mn11_manual_decision_intake_basis_confirmation(
        scope_no_touch_no_promotion_boundary_freeze=op00,
        mn11_manual_decision_material=_ready_mn11(),
    )

    assert material["schema_version"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP01_MN11_MANUAL_DECISION_INTAKE_BASIS_CONFIRMATION_SCHEMA_VERSION
    assert material["operation_step_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP01_STEP_REF
    assert material["pmn_op01_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP01_READY_STATUS_REF
    assert material["pmn_op01_ready"] is True
    assert material["pmn_op01_blocker_refs"] == []
    assert material["op00_next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP01_STEP_REF
    assert material["mn11_result_memo_ref"] == pmn.P7_R54_AHR_POST_MN11_MN11_RESULT_MEMO_REF
    assert material["mn11_bodyfree_envelope_present"] is True
    assert material["mn11_operation_step_ref"] == mn.P7_R54_AHR_POST_EX18_MN11_STEP_REF
    assert material["mn11_ready"] is True
    assert material["mn11_manual_decision_ref"] == "RETURN_TO_ACTUAL_REVIEW_OPERATION_REQUIRED"
    assert material["mn11_final_manual_decision_ref"] == "RETURN_TO_ACTUAL_REVIEW_OPERATION_REQUIRED"
    assert material["mn11_actual_review_evidence_status_ref"] == "actual_review_evidence_missing_real_review_required"
    assert material["mn11_next_required_step"] == "actual_local_only_human_review_operation_required_before_p5_p6_p8_r52_decision"
    assert material["mn11_actual_review_evidence_complete_from_real_review"] is False
    assert material["mn11_actual_review_evidence_complete_from_real_review_false_confirmed"] is True
    assert material["mn11_actual_review_basis_ref"] == "current_received_snapshot_264_85_258_171"
    assert material["mn11_actual_review_basis_ref_confirmed"] is True
    assert material["mn11_green_is_not_actual_human_review_complete"] is True
    assert material["mn11_manual_decision_is_not_actual_operation_receipt"] is True
    assert material["pmn_op01_does_not_treat_mn11_green_as_real_review_complete"] is True
    assert material["pmn_op01_passes_to_existing_support_material_inventory"] is True
    assert material["actual_local_only_human_review_operation_required_before_downstream_decision"] is True
    assert material["basis_rewritten_here"] is False
    assert material["local_received_zip_refs_are_actual_review_basis"] is False
    assert tuple(material["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP01_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP01_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP02_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op01_mn11_manual_decision_intake_basis_confirmation_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value", "expected_blocker"),
    (
        ("manual_decision_ref", "EVIDENCE_COMPLETE_BUT_DOWNSTREAM_MANUAL_DECISION_REQUIRED", "pmn_op01_manual_decision_ref_not_return_to_actual_review_operation_required"),
        ("actual_review_evidence_status_ref", "actual_review_evidence_complete_by_actual_person_review_bodyfree", "pmn_op01_actual_review_evidence_status_not_missing_real_review_required"),
        ("next_required_step", "downstream_manual_decision_required_without_auto_execution", "pmn_op01_next_required_step_not_actual_local_only_human_review_operation"),
        ("actual_review_evidence_complete_from_real_review", True, "pmn_op01_actual_review_evidence_complete_from_real_review_not_false"),
        ("actual_review_basis_ref", "mashos-api(174).zip", "pmn_op01_actual_review_basis_ref_mismatch"),
        ("local_received_zip_refs_are_actual_review_basis", True, "pmn_op01_local_zip_refs_claimed_as_actual_review_basis"),
        ("local_received_zip_refs_used_to_rewrite_current_actual_review_basis", True, "pmn_op01_current_actual_review_basis_rewrite_claim_detected"),
        ("release_allowed", True, "pmn_op01_mn11_promotion_or_completion_claim_detected"),
    ),
)
def test_pmn_op01_blocks_invalid_mn11_basis_decision_or_promotion_claim(
    field: str, bad_value: object, expected_blocker: str
) -> None:
    mn11_material = _ready_mn11()
    mn11_material[field] = bad_value
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op01_mn11_manual_decision_intake_basis_confirmation(
        mn11_manual_decision_material=mn11_material,
    )

    assert material["pmn_op01_ready"] is False
    assert expected_blocker in material["pmn_op01_blocker_refs"]
    assert material["pmn_op01_passes_to_existing_support_material_inventory"] is False
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP01_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op01_mn11_manual_decision_intake_basis_confirmation_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op01_blocks_forbidden_body_question_path_hash_keys_without_copying_payload() -> None:
    mn11_material = _ready_mn11()
    mn11_material["question_text"] = "do not copy this"
    mn11_material["local_absolute_path"] = "/tmp/do-not-copy"
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op01_mn11_manual_decision_intake_basis_confirmation(
        mn11_manual_decision_material=mn11_material,
    )

    assert material["pmn_op01_ready"] is False
    assert "pmn_op01_mn11_forbidden_body_question_path_hash_key_detected" in material["pmn_op01_blocker_refs"]
    assert material["mn11_forbidden_payload_key_path_count"] == 2
    assert "question_text" not in material
    assert "local_absolute_path" not in material
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op01_mn11_manual_decision_intake_basis_confirmation_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op01_contract_rejects_output_completion_or_promotion_mutation() -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op01_mn11_manual_decision_intake_basis_confirmation(
        mn11_manual_decision_material=_ready_mn11(),
    )

    mutated = deepcopy(material)
    mutated["actual_review_evidence_complete_from_real_review"] = True
    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op01_mn11_manual_decision_intake_basis_confirmation_contract(mutated)

    mutated = deepcopy(material)
    mutated["p8_start_allowed"] = True
    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op01_mn11_manual_decision_intake_basis_confirmation_contract(mutated)

    mutated = deepcopy(material)
    mutated["mn11_next_required_step"] = "downstream_manual_decision_required_without_auto_execution"
    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op01_mn11_manual_decision_intake_basis_confirmation_contract(mutated)


def test_pmn_op00_op01_aliases_match_primary_builders_and_contracts() -> None:
    op00 = pmn.build_p7_r54_ahr_post_mn11_actual_operation_scope_no_touch_no_promotion_boundary_freeze_bodyfree()
    assert op00 == pmn.build_p7_r54_ahr_post_mn11_pmn_op00_scope_no_touch_no_promotion_boundary_freeze()
    assert pmn.assert_p7_r54_ahr_post_mn11_actual_operation_scope_no_touch_no_promotion_boundary_freeze_bodyfree_contract(op00) is True

    primary = pmn.build_p7_r54_ahr_post_mn11_pmn_op01_mn11_manual_decision_intake_basis_confirmation(
        scope_no_touch_no_promotion_boundary_freeze=op00,
        mn11_manual_decision_material=_ready_mn11(),
    )
    alias = pmn.build_p7_r54_ahr_post_mn11_actual_operation_mn11_manual_decision_intake_basis_confirmation_bodyfree(
        scope_no_touch_no_promotion_boundary_freeze=op00,
        mn11_manual_decision_material=_ready_mn11(),
    )
    assert alias == primary
    assert pmn.assert_p7_r54_ahr_post_mn11_actual_operation_mn11_manual_decision_intake_basis_confirmation_bodyfree_contract(alias) is True
