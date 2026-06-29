# -*- coding: utf-8 -*-
"""R54-AHR-CR22 current received actual local review operation tests."""

from __future__ import annotations

from copy import deepcopy

import pytest

import emlis_ai_p7_r54_ahr_current_received_snapshot_actual_local_review_operation_20260628 as cr


def _assert_bodyfree_no_touch(material: dict[str, object], *, allowed_true_flags: tuple[str, ...] = ()) -> None:
    assert material["body_free"] is True
    allowed = set(allowed_true_flags)
    for key in cr.P7_R54_AHR_CR_FALSE_FLAG_REFS:
        if key in allowed:
            assert material[key] in (False, True), key
            continue
        assert material[key] is False, key
    for flag_map_key in ("public_contract", "r54_ahr_cr_no_touch_contract", "body_free_markers"):
        assert material[flag_map_key]
        assert all(value is False for value in material[flag_map_key].values()), flag_map_key
    for forbidden_key in (
        "raw_input",
        "raw_body",
        "current_input_body",
        "returned_emlis_body",
        "history_surface",
        "comment_text",
        "reviewer_free_text",
        "reviewer_notes_body",
        "question_text",
        "draft_question_text",
        "packet_content",
        "body_full_packet_content",
        "local_path",
        "local_absolute_path",
        "body_hash",
        "terminal_output_body",
        "stdout_body",
        "stderr_body",
        "traceback_body",
    ):
        assert forbidden_key not in material


def _selection_rows() -> list[dict[str, object]]:
    return cr.build_p7_r54_ahr_cr10_bodyfree_selection_result_rows_input()


def _p8_candidate_rows() -> list[dict[str, object]]:
    rows = _selection_rows()
    rows[0]["question_need_primary_class"] = "question_may_reduce_overread_risk"
    rows[0]["one_question_fit_ref"] = "fits_one_question"
    rows[0]["plan_candidate_flags"]["p8_design_material_candidate"] = True
    return rows


def _ready_chain(rows: list[dict[str, object]] | None = None) -> dict[str, dict[str, object]]:
    cr00_material = cr.build_p7_r54_ahr_cr00_scope_no_touch_boundary_freeze()
    cr01_material = cr.build_p7_r54_ahr_cr01_current_received_basis_envelope(
        scope_no_touch_boundary_freeze=cr00_material,
    )
    cr02_material = cr.build_p7_r54_ahr_cr02_historical_helper_refs_separation(
        current_received_basis_envelope=cr01_material,
    )
    cr03_material = cr.build_p7_r54_ahr_cr03_basis_impact_assessment(
        historical_helper_refs_separation=cr02_material,
    )
    cr04_material = cr.build_p7_r54_ahr_cr04_current_24_case_manifest_refreeze(
        basis_impact_assessment=cr03_material,
    )
    cr05_material = cr.build_p7_r54_ahr_cr05_local_only_preflight(
        explicit_allow_ref=cr.P7_R54_AHR_CR05_DEFAULT_EXPLICIT_ALLOW_REF,
    )
    cr06_material = cr.build_p7_r54_ahr_cr06_packet_generation_request_bridge(
        local_only_preflight=cr05_material,
    )
    cr07_material = cr.build_p7_r54_ahr_cr07_packet_generation_receipt_and_scan(
        packet_generation_request_bridge=cr06_material,
        receipt_input=cr.build_p7_r54_ahr_cr07_bodyfree_receipt_input(),
    )
    cr08_material = cr.build_p7_r54_ahr_cr08_reviewer_selection_form(
        packet_generation_receipt_scan=cr07_material,
        reviewer_person_ref=cr.P7_R54_AHR_CR08_DEFAULT_REVIEWER_PERSON_REF,
        reviewer_is_person=True,
        reviewer_person_confirmed=True,
    )
    cr09_material = cr.build_p7_r54_ahr_cr09_actual_local_human_review_operation_receipt(
        reviewer_selection_form=cr08_material,
        operation_receipt_input=cr.build_p7_r54_ahr_cr09_bodyfree_operation_receipt_input(),
    )
    cr10_material = cr.build_p7_r54_ahr_cr10_sanitized_selection_only_result_rows_intake(
        actual_local_human_review_operation_receipt=cr09_material,
        selection_result_rows=rows or _selection_rows(),
    )
    cr11_material = cr.build_p7_r54_ahr_cr11_rating_row_normalization(
        sanitized_selection_only_result_rows_intake=cr10_material,
    )
    cr12_material = cr.build_p7_r54_ahr_cr12_readfeel_execution_blocker_normalization(
        rating_row_normalization=cr11_material,
    )
    cr13_material = cr.build_p7_r54_ahr_cr13_question_need_observation_normalization(
        sanitized_selection_only_result_rows_intake=cr10_material,
        rating_row_normalization=cr11_material,
        readfeel_execution_blocker_normalization=cr12_material,
    )
    cr14_material = cr.build_p7_r54_ahr_cr14_rating_question_consistency_guard(
        rating_row_normalization=cr11_material,
        readfeel_execution_blocker_normalization=cr12_material,
        question_need_observation_normalization=cr13_material,
    )
    cr15_material = cr.build_p7_r54_ahr_cr15_pause_abort_expiration_disposal_receipt(
        rating_question_consistency_guard=cr14_material,
        disposal_receipt_input=cr.build_p7_r54_ahr_cr15_bodyfree_disposal_receipt_input(),
    )
    cr16_material = cr.build_p7_r54_ahr_cr16_post_review_summary_evidence_complete_predicate(
        actual_local_human_review_operation_receipt=cr09_material,
        sanitized_selection_only_result_rows_intake=cr10_material,
        rating_row_normalization=cr11_material,
        readfeel_execution_blocker_normalization=cr12_material,
        question_need_observation_normalization=cr13_material,
        rating_question_consistency_guard=cr14_material,
        disposal_receipt=cr15_material,
    )
    cr17_material = cr.build_p7_r54_ahr_cr17_p5_decision_candidate_repair_separation(
        post_review_summary=cr16_material,
    )
    cr18_material = cr.build_p7_r54_ahr_cr18_p6_candidate_only_handoff(
        p5_decision_candidate_repair_separation=cr17_material,
    )
    cr19_material = cr.build_p7_r54_ahr_cr19_p8_material_candidate_only_handoff(
        question_need_observation_normalization=cr13_material,
        rating_question_consistency_guard=cr14_material,
        p5_decision_candidate_repair_separation=cr17_material,
    )
    cr20_material = cr.build_p7_r54_ahr_cr20_r52_handoff_candidate_envelope(
        cr16_summary=cr16_material,
        cr17_p5_decision=cr17_material,
        cr18_p6_candidate=cr18_material,
        cr19_p8_candidate=cr19_material,
    )
    materials = [
        cr00_material,
        cr01_material,
        cr02_material,
        cr03_material,
        cr04_material,
        cr05_material,
        cr06_material,
        cr07_material,
        cr08_material,
        cr09_material,
        cr10_material,
        cr11_material,
        cr12_material,
        cr13_material,
        cr14_material,
        cr15_material,
        cr16_material,
        cr17_material,
        cr18_material,
        cr19_material,
        cr20_material,
    ]
    cr21_material = cr.build_p7_r54_ahr_cr21_final_no_body_leak_no_question_text_no_touch_validation(
        materials,
    )
    return {
        "cr00": cr00_material,
        "cr01": cr01_material,
        "cr02": cr02_material,
        "cr03": cr03_material,
        "cr04": cr04_material,
        "cr05": cr05_material,
        "cr06": cr06_material,
        "cr07": cr07_material,
        "cr08": cr08_material,
        "cr09": cr09_material,
        "cr10": cr10_material,
        "cr11": cr11_material,
        "cr12": cr12_material,
        "cr13": cr13_material,
        "cr14": cr14_material,
        "cr15": cr15_material,
        "cr16": cr16_material,
        "cr17": cr17_material,
        "cr18": cr18_material,
        "cr19": cr19_material,
        "cr20": cr20_material,
        "cr21": cr21_material,
    }


def _command_rows() -> list[dict[str, object]]:
    return cr.build_p7_r54_ahr_cr22_bodyfree_validation_command_rows_input()


def test_cr22_blocks_by_default_without_cr21_or_command_matrix() -> None:
    material = cr.build_p7_r54_ahr_cr22_validation_command_matrix_documentation_output()

    assert set(material) == set(cr.P7_R54_AHR_CR22_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cr.P7_R54_AHR_CR22_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION
    assert material["operation_step_ref"] == cr.P7_R54_AHR_CR22_STEP_REF
    assert material["documentation_output_status_ref"] == cr.P7_R54_AHR_CR22_BLOCKED_STATUS_REF
    assert material["documentation_output_ready"] is False
    assert cr.P7_R54_AHR_CR22_CR21_NOT_READY_BLOCKER_REF in material["documentation_output_step_blocker_refs"]
    assert cr.P7_R54_AHR_CR22_MISSING_COMMAND_BLOCKER_REF in material["documentation_output_step_blocker_refs"]
    assert material["result_memo_ref"] == cr.P7_R54_AHR_CR22_DEFAULT_RESULT_MEMO_REF
    assert material["result_memo_materialized_here"] is False
    assert material["validation_matrix_materialized_here"] is False
    assert material["release_allowed"] is False
    _assert_bodyfree_no_touch(material, allowed_true_flags=cr.P7_R54_AHR_CR22_ALLOWED_TRUE_OPERATION_FLAG_REFS)
    assert cr.assert_p7_r54_ahr_cr22_validation_command_matrix_documentation_output_contract(material) is True


def test_cr22_documents_validation_matrix_without_promoting_release() -> None:
    chain = _ready_chain(_p8_candidate_rows())
    material = cr.build_p7_r54_ahr_cr22_validation_command_matrix_documentation_output(
        cr21_validation=chain["cr21"],
        command_rows=_command_rows(),
    )

    assert material["documentation_output_status_ref"] == cr.P7_R54_AHR_CR22_READY_STATUS_REF
    assert material["documentation_output_ready"] is True
    assert material["documentation_output_step_blocker_refs"] == []
    assert material["validation_command_row_count"] == len(cr.P7_R54_AHR_CR22_REQUIRED_COMMAND_REFS)
    assert material["missing_validation_command_refs"] == []
    assert material["duplicate_validation_command_refs"] == []
    assert material["nonpassed_required_validation_command_refs"] == []
    assert material["claimed_required_not_claimed_command_refs"] == []
    assert material["unallowed_green_claim_refs"] == []
    assert material["forbidden_command_row_key_refs"] == []
    assert material["target_tests_documented"] is True
    assert material["selected_regression_documented"] is True
    assert material["compileall_documented"] is True
    assert material["claim_boundary_documented"] is True
    assert material["result_memo_ref"] == cr.P7_R54_AHR_CR22_DEFAULT_RESULT_MEMO_REF
    assert material["result_memo_materialized_here"] is True
    assert material["validation_matrix_materialized_here"] is True
    assert material["actual_review_evidence_complete"] is True
    assert material["actual_human_review_newly_run_here"] is False
    assert material["full_backend_suite_green_confirmed"] is False
    assert material["rn_contract_green_confirmed"] is False
    assert material["rn_real_device_modal_verified"] is False
    assert material["p5_confirmed_final"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == cr.P7_R54_AHR_CR22_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cr.P7_R54_AHR_CR22_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cr.P7_R54_AHR_CR22_COMPLETE_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material, allowed_true_flags=cr.P7_R54_AHR_CR22_ALLOWED_TRUE_OPERATION_FLAG_REFS)
    assert cr.assert_p7_r54_ahr_cr22_validation_command_matrix_documentation_output_contract(material) is True


@pytest.mark.parametrize(
    "removed_ref",
    (
        cr.P7_R54_AHR_CR22_TARGET_CR00_TO_CR22_COMMAND_REF,
        cr.P7_R54_AHR_CR22_SELECTED_CS_COMMAND_REF,
        cr.P7_R54_AHR_CR22_COMPILEALL_COMMAND_REF,
        cr.P7_R54_AHR_CR22_FULL_BACKEND_NOT_CLAIMED_COMMAND_REF,
    ),
)
def test_cr22_blocks_when_required_command_row_is_missing(removed_ref: str) -> None:
    chain = _ready_chain(_p8_candidate_rows())
    rows = [row for row in _command_rows() if row["command_ref"] != removed_ref]
    material = cr.build_p7_r54_ahr_cr22_validation_command_matrix_documentation_output(
        cr21_validation=chain["cr21"],
        command_rows=rows,
    )

    assert material["documentation_output_ready"] is False
    assert removed_ref in material["missing_validation_command_refs"]
    assert cr.P7_R54_AHR_CR22_MISSING_COMMAND_BLOCKER_REF in material["documentation_output_step_blocker_refs"]
    assert material["release_allowed"] is False
    assert cr.assert_p7_r54_ahr_cr22_validation_command_matrix_documentation_output_contract(material) is True


def test_cr22_blocks_when_pass_required_command_is_not_passed() -> None:
    chain = _ready_chain(_p8_candidate_rows())
    rows = _command_rows()
    rows[0]["command_status_ref"] = cr.P7_R54_AHR_CR22_COMMAND_STATUS_FAILED_RECORDED_REF
    rows[0]["passed"] = False
    material = cr.build_p7_r54_ahr_cr22_validation_command_matrix_documentation_output(
        cr21_validation=chain["cr21"],
        command_rows=rows,
    )

    assert material["documentation_output_ready"] is False
    assert cr.P7_R54_AHR_CR22_TARGET_CR00_TO_CR22_COMMAND_REF in material["nonpassed_required_validation_command_refs"]
    assert cr.P7_R54_AHR_CR22_REQUIRED_PASS_COMMAND_NOT_PASSED_BLOCKER_REF in material["documentation_output_step_blocker_refs"]
    assert material["release_allowed"] is False
    assert cr.assert_p7_r54_ahr_cr22_validation_command_matrix_documentation_output_contract(material) is True


def test_cr22_blocks_unallowed_full_backend_or_rn_green_claims() -> None:
    chain = _ready_chain(_p8_candidate_rows())
    rows = _command_rows()
    for row in rows:
        if row["command_ref"] == cr.P7_R54_AHR_CR22_FULL_BACKEND_NOT_CLAIMED_COMMAND_REF:
            row["command_status_ref"] = cr.P7_R54_AHR_CR22_COMMAND_STATUS_PASSED_REF
            row["passed"] = True
            row["green_claimed"] = True
            row["full_backend_suite_green_claimed"] = True
        if row["command_ref"] == cr.P7_R54_AHR_CR22_RN_REAL_DEVICE_NOT_CLAIMED_COMMAND_REF:
            row["rn_real_device_modal_claimed"] = True
    material = cr.build_p7_r54_ahr_cr22_validation_command_matrix_documentation_output(
        cr21_validation=chain["cr21"],
        command_rows=rows,
    )

    assert material["documentation_output_ready"] is False
    assert cr.P7_R54_AHR_CR22_FULL_BACKEND_NOT_CLAIMED_COMMAND_REF in material["claimed_required_not_claimed_command_refs"]
    assert material["unallowed_green_claim_refs"]
    assert cr.P7_R54_AHR_CR22_REQUIRED_NOT_CLAIMED_COMMAND_CLAIMED_BLOCKER_REF in material["documentation_output_step_blocker_refs"]
    assert cr.P7_R54_AHR_CR22_UNALLOWED_GREEN_CLAIM_BLOCKER_REF in material["documentation_output_step_blocker_refs"]
    assert material["full_backend_suite_green_confirmed"] is False
    assert material["rn_real_device_modal_verified"] is False
    assert material["release_allowed"] is False
    assert cr.assert_p7_r54_ahr_cr22_validation_command_matrix_documentation_output_contract(material) is True


def test_cr22_blocks_forbidden_command_row_leak_without_exporting_body() -> None:
    chain = _ready_chain(_p8_candidate_rows())
    rows = _command_rows()
    rows[0]["stdout_body_included"] = True
    rows[0]["terminal_output_body_included"] = True
    rows[0]["local_absolute_path_included"] = True
    material = cr.build_p7_r54_ahr_cr22_validation_command_matrix_documentation_output(
        cr21_validation=chain["cr21"],
        command_rows=rows,
    )

    assert material["documentation_output_ready"] is False
    assert material["forbidden_command_row_key_refs"]
    assert cr.P7_R54_AHR_CR22_FORBIDDEN_KEY_BLOCKER_REF in material["documentation_output_step_blocker_refs"]
    assert "stdout_body" not in material
    assert "terminal_output_body" not in material
    assert "local_absolute_path" not in material
    assert material["release_allowed"] is False
    for row in material["validation_command_rows"]:
        assert row["stdout_body_included"] is False
        assert row["terminal_output_body_included"] is False
        assert row["local_absolute_path_included"] is False
    assert cr.assert_p7_r54_ahr_cr22_validation_command_matrix_documentation_output_contract(material) is True


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("actual_human_review_run_here", True),
        ("actual_human_review_operation_run", True),
        ("actual_r52_reintake_execution_confirmed", True),
        ("p5_confirmed_final", True),
        ("p6_start_allowed", True),
        ("p8_start_allowed", True),
        ("p7_complete", True),
        ("release_allowed", True),
        ("full_backend_suite_green_confirmed", True),
        ("rn_contract_green_confirmed", True),
        ("rn_real_device_modal_verified", True),
        ("next_required_step", "mutated_next_step"),
    ),
)
def test_cr22_contract_rejects_completion_or_release_promotion_mutations(field: str, value: object) -> None:
    chain = _ready_chain(_p8_candidate_rows())
    material = deepcopy(
        cr.build_p7_r54_ahr_cr22_validation_command_matrix_documentation_output(
            cr21_validation=chain["cr21"],
            command_rows=_command_rows(),
        )
    )
    material[field] = value

    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr22_validation_command_matrix_documentation_output_contract(material)


def test_cr22_alias_functions_match_primary_builder_and_contract() -> None:
    chain = _ready_chain(_p8_candidate_rows())
    primary = cr.build_p7_r54_ahr_cr22_validation_command_matrix_documentation_output(
        cr21_validation=chain["cr21"],
        command_rows=_command_rows(),
    )
    alias = cr.build_p7_r54_ahr_current_received_actual_local_review_operation_validation_command_matrix_documentation_output_bodyfree(
        cr21_validation=chain["cr21"],
        command_rows=_command_rows(),
    )

    assert alias == primary
    assert (
        cr.assert_p7_r54_ahr_current_received_actual_local_review_operation_validation_command_matrix_documentation_output_bodyfree_contract(
            alias
        )
        is True
    )
