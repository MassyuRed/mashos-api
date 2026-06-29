# -*- coding: utf-8 -*-
"""R54-AHR Post-CR22 actual local review evidence completion EX00-EX01 tests."""

from __future__ import annotations

from copy import deepcopy

import pytest

import emlis_ai_p7_r54_ahr_current_received_snapshot_actual_local_review_operation_20260628 as cr
import emlis_ai_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_20260629 as ex


def _assert_bodyfree_no_touch_nonpromotion(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    for key in ex.P7_R54_AHR_POST_CR22_REQUIRED_FALSE_FLAG_REFS:
        assert material[key] is False, key
    for marker_map_key in ("public_contract", "postcr22_no_touch_contract", "body_free_markers"):
        assert material[marker_map_key]
        assert all(value is False for value in material[marker_map_key].values()), marker_map_key
    for forbidden_key in ex.P7_R54_AHR_POST_CR22_FORBIDDEN_PAYLOAD_KEY_REFS:
        assert forbidden_key not in material, forbidden_key


def _command_rows() -> list[dict[str, object]]:
    return cr.build_p7_r54_ahr_cr22_bodyfree_validation_command_rows_input()


def test_ex00_freezes_post_cr22_scope_no_touch_and_non_promotion_boundary() -> None:
    material = ex.build_p7_r54_ahr_post_cr22_ex00_scope_no_touch_non_promotion_boundary_freeze()

    assert set(material) == set(ex.P7_R54_AHR_POST_CR22_EX00_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == ex.P7_R54_AHR_POST_CR22_EX00_SCOPE_NO_TOUCH_NON_PROMOTION_BOUNDARY_FREEZE_SCHEMA_VERSION
    assert material["operation_step_ref"] == ex.P7_R54_AHR_POST_CR22_EX00_STEP_REF
    assert material["postcr22_scope_confirmed"] is True
    assert material["no_touch_boundary_confirmed"] is True
    assert material["non_promotion_boundary_confirmed"] is True
    assert material["actual_local_review_execution_evidence_completion_selected"] is True
    assert material["p8_question_implementation_out_of_scope"] is True
    assert material["r52_actual_execution_out_of_scope"] is True
    assert material["p5_finalization_out_of_scope"] is True
    assert material["p6_start_out_of_scope"] is True
    assert material["p7_completion_out_of_scope"] is True
    assert material["release_decision_out_of_scope"] is True
    assert material["local_received_zip_refs"] == ex.P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS
    assert material["local_received_zip_refs_are_actual_review_basis"] is False
    assert material["local_received_zip_refs_used_to_rewrite_current_cr_basis"] is False
    assert material["actual_review_basis_ref"] == "current_received_snapshot_264_85_258_171"
    assert material["actual_review_basis_allowed_ref"] == "current_received_snapshot_264_85_258_171_only"
    assert tuple(material["implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX00_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX00_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX01_STEP_REF
    _assert_bodyfree_no_touch_nonpromotion(material)
    assert ex.assert_p7_r54_ahr_post_cr22_ex00_scope_no_touch_non_promotion_boundary_freeze_contract(material) is True


def test_ex01_accepts_cr22_support_material_and_confirms_current_cr_basis_without_promotion() -> None:
    ex00 = ex.build_p7_r54_ahr_post_cr22_ex00_scope_no_touch_non_promotion_boundary_freeze()
    material = ex.build_p7_r54_ahr_post_cr22_ex01_cr22_support_material_intake_current_cr_basis_confirmation(
        scope_no_touch_non_promotion_boundary=ex00,
    )

    assert set(material) == set(ex.P7_R54_AHR_POST_CR22_EX01_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == (
        ex.P7_R54_AHR_POST_CR22_EX01_CR22_SUPPORT_MATERIAL_INTAKE_CURRENT_CR_BASIS_CONFIRMATION_SCHEMA_VERSION
    )
    assert material["operation_step_ref"] == ex.P7_R54_AHR_POST_CR22_EX01_STEP_REF
    assert material["cr22_support_material_status_ref"] == ex.P7_R54_AHR_POST_CR22_EX01_READY_STATUS_REF
    assert material["cr22_support_material_accepted"] is True
    assert material["cr22_support_material_step_blocker_refs"] == []
    assert material["cr22_result_memo_ref"] == cr.P7_R54_AHR_CR22_DEFAULT_RESULT_MEMO_REF
    assert material["current_cr_helper_ref"] == ex.P7_R54_AHR_POST_CR22_CURRENT_CR_HELPER_REF
    assert material["cr22_validation_command_row_count"] == len(cr.P7_R54_AHR_CR22_REQUIRED_COMMAND_REFS)
    assert material["cr22_missing_required_command_refs"] == []
    assert material["cr22_duplicate_command_refs"] == []
    assert material["cr22_nonpassed_required_command_refs"] == []
    assert material["cr22_claimed_required_not_claimed_command_refs"] == []
    assert material["cr22_forbidden_command_row_refs"] == []
    assert material["cr22_promotion_claim_command_refs"] == []
    assert material["cr22_target_recorded_22_passed"] is True
    assert material["cr00_cr22_combined_recorded_837_passed"] is True
    assert material["cs00_cs18_selected_recorded_450_passed"] is True
    assert material["compileall_recorded_passed"] is True
    assert material["cr22_green_is_not_actual_review_complete"] is True
    assert material["cr22_green_is_not_actual_review_evidence_complete"] is True
    assert material["actual_basis_confirmed"] is True
    assert material["basis_rewrite_required_here"] is False
    assert material["basis_rewritten_here"] is False
    assert material["local_received_zip_refs_are_actual_review_basis"] is False
    assert material["local_received_zip_refs_used_to_rewrite_current_cr_basis"] is False
    assert material["current_cr_basis_remains_264_85_258_171"] is True
    assert material["full_backend_suite_green_unclaimed"] is True
    assert material["rn_contract_green_unclaimed_unless_actually_run"] is True
    assert material["rn_real_device_modal_verified_unclaimed"] is True
    assert material["p8_start_allowed"] is False
    assert material["r52_actual_execution_confirmed"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX01_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX01_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX02_STEP_REF
    _assert_bodyfree_no_touch_nonpromotion(material)
    assert ex.assert_p7_r54_ahr_post_cr22_ex01_cr22_support_material_intake_current_cr_basis_confirmation_contract(material) is True


def test_ex01_keeps_current_local_zip_labels_separate_from_current_cr_basis() -> None:
    material = ex.build_p7_r54_ahr_post_cr22_ex01_cr22_support_material_intake_current_cr_basis_confirmation()

    assert material["local_received_zip_refs"]["premise_zip_ref"] == "Cocolon_前提資料(266).zip"
    assert material["local_received_zip_refs"]["implemented_materials_zip_ref"] == "EmlisAIの実装済み資料(86).zip"
    assert material["local_received_zip_refs"]["rn_zip_ref"] == "Cocolon(259).zip"
    assert material["local_received_zip_refs"]["backend_zip_ref"] == "mashos-api(172).zip"
    assert material["current_cr_actual_review_basis_ref"] == "current_received_snapshot_264_85_258_171"
    assert material["current_cr_actual_review_basis_allowed_ref"] == "current_received_snapshot_264_85_258_171_only"
    assert material["outer_received_zip_label_difference_recorded_bodyfree"] is True
    assert material["local_received_zip_refs_are_actual_review_basis"] is False
    assert material["local_received_zip_refs_used_to_rewrite_current_cr_basis"] is False
    assert ex.assert_p7_r54_ahr_post_cr22_ex01_cr22_support_material_intake_current_cr_basis_confirmation_contract(material) is True


def test_ex01_blocks_when_required_cr22_command_row_is_missing_without_promoting_step() -> None:
    rows = [row for row in _command_rows() if row["command_ref"] != cr.P7_R54_AHR_CR22_TARGET_CR00_TO_CR22_COMMAND_REF]
    material = ex.build_p7_r54_ahr_post_cr22_ex01_cr22_support_material_intake_current_cr_basis_confirmation(
        cr22_validation_command_rows=rows,
    )

    assert material["cr22_support_material_accepted"] is False
    assert material["cr22_support_material_status_ref"] == ex.P7_R54_AHR_POST_CR22_EX01_BLOCKED_STATUS_REF
    assert cr.P7_R54_AHR_CR22_TARGET_CR00_TO_CR22_COMMAND_REF in material["cr22_missing_required_command_refs"]
    assert "ex01_cr22_required_validation_command_row_missing" in material["cr22_support_material_step_blocker_refs"]
    assert tuple(material["implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX00_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX00_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX01_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert material["release_allowed"] is False
    assert ex.assert_p7_r54_ahr_post_cr22_ex01_cr22_support_material_intake_current_cr_basis_confirmation_contract(material) is True


def test_ex01_blocks_when_pass_required_cr22_command_is_not_passed() -> None:
    rows = _command_rows()
    rows[0]["command_status_ref"] = cr.P7_R54_AHR_CR22_COMMAND_STATUS_FAILED_RECORDED_REF
    rows[0]["passed"] = False
    material = ex.build_p7_r54_ahr_post_cr22_ex01_cr22_support_material_intake_current_cr_basis_confirmation(
        cr22_validation_command_rows=rows,
    )

    assert material["cr22_support_material_accepted"] is False
    assert cr.P7_R54_AHR_CR22_TARGET_CR00_TO_CR22_COMMAND_REF in material["cr22_nonpassed_required_command_refs"]
    assert "ex01_cr22_required_pass_command_not_passed" in material["cr22_support_material_step_blocker_refs"]
    assert material["actual_review_evidence_complete"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert ex.assert_p7_r54_ahr_post_cr22_ex01_cr22_support_material_intake_current_cr_basis_confirmation_contract(material) is True


def test_ex01_blocks_unallowed_green_claim_on_not_claimed_cr22_rows() -> None:
    rows = _command_rows()
    for row in rows:
        if row["command_ref"] == cr.P7_R54_AHR_CR22_FULL_BACKEND_NOT_CLAIMED_COMMAND_REF:
            row["command_status_ref"] = cr.P7_R54_AHR_CR22_COMMAND_STATUS_PASSED_REF
            row["green_claimed"] = True
            row["full_backend_suite_green_claimed"] = True
    material = ex.build_p7_r54_ahr_post_cr22_ex01_cr22_support_material_intake_current_cr_basis_confirmation(
        cr22_validation_command_rows=rows,
    )

    assert material["cr22_support_material_accepted"] is False
    assert cr.P7_R54_AHR_CR22_FULL_BACKEND_NOT_CLAIMED_COMMAND_REF in material[
        "cr22_claimed_required_not_claimed_command_refs"
    ]
    assert "ex01_cr22_required_not_claimed_command_claimed" in material["cr22_support_material_step_blocker_refs"]
    assert material["full_backend_suite_green_confirmed"] is False
    assert material["release_allowed"] is False
    assert ex.assert_p7_r54_ahr_post_cr22_ex01_cr22_support_material_intake_current_cr_basis_confirmation_contract(material) is True


def test_ex01_blocks_cr22_row_leak_or_promotion_claim_and_exports_only_sanitized_command_rows() -> None:
    rows = _command_rows()
    rows[0]["stdout_body_included"] = True
    rows[0]["local_absolute_path_included"] = True
    rows[0]["actual_human_review_complete_claimed_by_command"] = True
    rows[0]["question_text"] = "forbidden_extra_key_fixture_ref"
    material = ex.build_p7_r54_ahr_post_cr22_ex01_cr22_support_material_intake_current_cr_basis_confirmation(
        cr22_validation_command_rows=rows,
    )

    assert material["cr22_support_material_accepted"] is False
    assert cr.P7_R54_AHR_CR22_TARGET_CR00_TO_CR22_COMMAND_REF in material["cr22_forbidden_command_row_refs"]
    assert cr.P7_R54_AHR_CR22_TARGET_CR00_TO_CR22_COMMAND_REF in material["cr22_promotion_claim_command_refs"]
    assert "ex01_cr22_command_matrix_forbidden_body_question_path_hash_key" in material[
        "cr22_support_material_step_blocker_refs"
    ]
    assert "ex01_cr22_command_matrix_promotion_claim_detected" in material["cr22_support_material_step_blocker_refs"]
    assert "question_text" not in material
    for row in material["cr22_validation_command_rows"]:
        assert "question_text" not in row
        assert row["stdout_body_included"] is False
        assert row["local_absolute_path_included"] is False
        assert row["actual_human_review_complete_claimed_by_command"] is False
    assert material["actual_human_review_complete"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert ex.assert_p7_r54_ahr_post_cr22_ex01_cr22_support_material_intake_current_cr_basis_confirmation_contract(material) is True


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("release_allowed", True),
        ("p8_start_allowed", True),
        ("actual_review_evidence_complete", True),
        ("local_received_zip_refs_are_actual_review_basis", True),
        ("local_received_zip_refs_used_to_rewrite_current_cr_basis", True),
        ("next_required_step", "mutated_next_step"),
    ),
)
def test_ex00_contract_rejects_promotion_or_basis_rewrite_mutations(field: str, value: object) -> None:
    material = deepcopy(ex.build_p7_r54_ahr_post_cr22_ex00_scope_no_touch_non_promotion_boundary_freeze())
    material[field] = value

    with pytest.raises(ValueError):
        ex.assert_p7_r54_ahr_post_cr22_ex00_scope_no_touch_non_promotion_boundary_freeze_contract(material)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("release_allowed", True),
        ("p8_start_allowed", True),
        ("r52_actual_execution_confirmed", True),
        ("actual_review_evidence_complete", True),
        ("basis_rewritten_here", True),
        ("local_received_zip_refs_are_actual_review_basis", True),
        ("actual_basis_confirmed", False),
        ("current_cr_basis_remains_264_85_258_171", False),
        ("next_required_step", "mutated_next_step"),
    ),
)
def test_ex01_contract_rejects_promotion_basis_or_next_step_mutations(field: str, value: object) -> None:
    material = deepcopy(
        ex.build_p7_r54_ahr_post_cr22_ex01_cr22_support_material_intake_current_cr_basis_confirmation()
    )
    material[field] = value

    with pytest.raises(ValueError):
        ex.assert_p7_r54_ahr_post_cr22_ex01_cr22_support_material_intake_current_cr_basis_confirmation_contract(material)


def test_ex01_alias_functions_match_primary_builder_and_contract() -> None:
    primary = ex.build_p7_r54_ahr_post_cr22_ex01_cr22_support_material_intake_current_cr_basis_confirmation()
    alias = (
        ex.build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_cr22_support_material_intake_current_cr_basis_confirmation_bodyfree()
    )

    assert alias == primary
    assert (
        ex.assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_cr22_support_material_intake_current_cr_basis_confirmation_bodyfree_contract(
            alias
        )
        is True
    )
