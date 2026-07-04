# -*- coding: utf-8 -*-
"""R54-AHR Post-MN11 actual local-only human review operation PMN-OP22/OP23 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_mn11_actual_local_only_human_review_operation_20260630 as pmn
import test_r54_ahr_post_mn11_actual_local_only_human_review_operation_pmn_op20_op21_20260630 as prev


def _assert_bodyfree_no_touch_no_promotion(
    material: dict[str, object],
    *,
    allowed_true_false_flags: tuple[str, ...] = (),
) -> None:
    assert material["body_free"] is True
    allowed_true = set(allowed_true_false_flags)
    for key in pmn.P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS:
        if key in allowed_true:
            assert material[key] in (False, True), key
        else:
            assert material[key] is False, key
    for marker_map_key in ("public_contract", "post_mn11_no_touch_contract", "body_free_markers"):
        assert material[marker_map_key]
        assert all(value is False for value in material[marker_map_key].values()), marker_map_key
    for forbidden_key in pmn.P7_R54_AHR_POST_MN11_FORBIDDEN_PAYLOAD_KEY_REFS:
        assert forbidden_key not in material, forbidden_key
    if "not_claimed_boundary" in material:
        assert all(value is False for value in material["not_claimed_boundary"].values())


def _ready_op21() -> dict[str, object]:
    material = prev._ready_op21()
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op21_existing_postcr22_ex07_ex18_reentry_mapping_contract(material) is True
    return material


def _ready_op22(op21: dict[str, object] | None = None) -> dict[str, object]:
    return pmn.build_p7_r54_ahr_post_mn11_pmn_op22_validation_command_matrix_result_memo_envelope(
        existing_postcr22_ex07_ex18_reentry_mapping=op21 or _ready_op21(),
        target_test_status_refs=tuple("passed_bodyfree_" + ref for ref in pmn.P7_R54_AHR_POST_MN11_PMN_OP22_TARGET_TEST_COMMAND_REFS),
        selected_regression_status_refs=(
            "passed_bodyfree_pytest_post_ex18_mn00_mn11_selected_regression",
            "passed_bodyfree_pytest_postcr22_ex00_ex18_selected_regression",
        ),
        compileall_status_ref="passed_bodyfree_compileall_post_mn11_helper",
    )


def _ready_op23(op22: dict[str, object] | None = None) -> dict[str, object]:
    return pmn.build_p7_r54_ahr_post_mn11_pmn_op23_acceptance_fail_closed_finalizer(
        validation_command_matrix_result_memo_envelope=op22 or _ready_op22()
    )


def test_pmn_op00_to_op21_implementation_is_present_before_op22_op23() -> None:
    op21 = _ready_op21()

    assert op21["existing_postcr22_ex07_ex18_reentry_mapping_ready"] is True
    assert op21["reentry_executed_here"] is False
    assert op21["actual_review_evidence_complete"] is True
    assert op21["actual_review_evidence_complete_from_real_review"] is True
    assert op21["p5_final_allowed"] is False
    assert op21["p6_start_allowed"] is False
    assert op21["p8_start_allowed"] is False
    assert op21["actual_r52_reintake_execution_confirmed"] is False
    assert op21["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP22_STEP_REF
    assert tuple(op21["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP21_IMPLEMENTED_STEPS
    assert tuple(op21["not_yet_implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP21_NOT_YET_IMPLEMENTED_STEPS
    _assert_bodyfree_no_touch_no_promotion(
        op21,
        allowed_true_false_flags=pmn.P7_R54_AHR_POST_MN11_PMN_OP21_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )


def test_pmn_op22_blocks_until_op21_reentry_mapping_is_ready() -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op22_validation_command_matrix_result_memo_envelope()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP22_REQUIRED_FIELD_REFS)
    assert material["validation_command_matrix_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP22_BLOCKED_STATUS_REF
    assert material["validation_command_matrix_ready"] is False
    assert "pmn_op22_op21_existing_postcr22_ex07_ex18_reentry_mapping_missing" in material["validation_command_matrix_blocker_refs"]
    assert material["actual_review_evidence_complete"] is False
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP22_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op22_validation_command_matrix_result_memo_envelope_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(
        material,
        allowed_true_false_flags=pmn.P7_R54_AHR_POST_MN11_PMN_OP22_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )


def test_pmn_op22_builds_validation_command_matrix_and_result_memo_envelope_without_claiming_execution() -> None:
    material = _ready_op22()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP22_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP22_VALIDATION_COMMAND_MATRIX_RESULT_MEMO_ENVELOPE_SCHEMA_VERSION
    assert material["operation_step_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP22_STEP_REF
    assert material["validation_command_matrix_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP22_READY_STATUS_REF
    assert material["validation_command_matrix_ready"] is True
    assert material["validation_command_matrix_blocker_refs"] == []
    assert tuple(material["target_test_command_refs"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP22_TARGET_TEST_COMMAND_REFS
    assert material["target_test_command_ref_count"] == 12
    assert material["target_test_status_ref_count"] == 12
    assert tuple(material["selected_regression_command_refs"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP22_SELECTED_REGRESSION_COMMAND_REFS
    assert material["selected_regression_status_ref_count"] == 2
    assert material["compileall_command_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP22_COMPILEALL_COMMAND_REF
    assert tuple(material["result_memo_required_section_refs"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP22_RESULT_MEMO_REQUIRED_SECTION_REFS
    assert material["result_memo_missing_section_refs"] == []
    assert material["result_memo_is_bodyfree_envelope"] is True
    assert material["result_memo_file_materialized_here"] is False
    assert material["result_memo_does_not_include_forbidden_payload"] is True
    assert material["result_memo_records_actual_operation_status"] is True
    assert material["result_memo_records_actual_evidence_status"] is True
    assert material["result_memo_records_not_claimed_boundary"] is True
    assert material["result_memo_records_next_required_step"] is True
    assert material["validation_commands_executed_here"] is False
    assert material["target_tests_green_claimed_here"] is False
    assert material["selected_regression_green_claimed_here"] is False
    assert material["full_backend_suite_green_claimed_here"] is False
    assert material["compileall_result_claimed_here"] is False
    assert material["zip_overlay_verification_claimed_here"] is False
    assert material["actual_review_evidence_complete"] is True
    assert material["actual_review_evidence_complete_from_real_review"] is True
    assert material["actual_review_evidence_complete_from_real_operation_claimed_here"] is False
    assert material["actual_body_full_packet_generation_run_here"] is False
    assert material["actual_24_case_local_only_human_review_run_here"] is False
    assert material["actual_operation_receipt_created_here_by_helper"] is False
    assert material["actual_rows_created_here_by_helper"] is False
    assert material["actual_disposal_purge_executed_here"] is False
    assert material["p5_final_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP22_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP22_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP23_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op22_validation_command_matrix_result_memo_envelope_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(
        material,
        allowed_true_false_flags=pmn.P7_R54_AHR_POST_MN11_PMN_OP22_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )


def test_pmn_op22_blocks_if_result_memo_required_sections_are_missing() -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op22_validation_command_matrix_result_memo_envelope(
        existing_postcr22_ex07_ex18_reentry_mapping=_ready_op21(),
        result_memo_section_refs=("implementation_scope", "changed_files"),
    )

    assert material["validation_command_matrix_ready"] is False
    assert "pmn_op22_result_memo_required_sections_missing" in material["validation_command_matrix_blocker_refs"]
    assert material["result_memo_missing_section_ref_count"] > 0
    assert material["actual_review_evidence_complete"] is False
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP22_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op22_validation_command_matrix_result_memo_envelope_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("validation_command_matrix_ready", False),
        ("result_memo_is_bodyfree_envelope", False),
        ("result_memo_does_not_include_forbidden_payload", False),
        ("validation_commands_executed_here", True),
        ("target_tests_green_claimed_here", True),
        ("full_backend_suite_green_claimed_here", True),
        ("actual_review_evidence_complete", False),
        ("actual_review_evidence_complete_from_real_review", False),
        ("actual_review_evidence_complete_from_real_operation_claimed_here", True),
        ("actual_24_case_local_only_human_review_run_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_pmn_op22_contract_rejects_validation_memo_claim_or_promotion_mutation(field: str, bad_value: object) -> None:
    material = _ready_op22()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op22_validation_command_matrix_result_memo_envelope_contract(mutated)


def test_pmn_op23_blocks_until_op22_validation_memo_envelope_is_ready() -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op23_acceptance_fail_closed_finalizer()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP23_REQUIRED_FIELD_REFS)
    assert material["acceptance_finalizer_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP23_BLOCKED_STATUS_REF
    assert material["acceptance_finalizer_ready"] is False
    assert "pmn_op23_op22_validation_command_matrix_result_memo_envelope_missing" in material["acceptance_finalizer_blocker_refs"]
    assert material["actual_review_evidence_complete"] is False
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert material["post_mn11_actual_operation_acceptance_ready"] is False
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP23_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op23_acceptance_fail_closed_finalizer_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(
        material,
        allowed_true_false_flags=pmn.P7_R54_AHR_POST_MN11_PMN_OP23_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )


def test_pmn_op23_finalizes_acceptance_fail_closed_status_without_downstream_promotion() -> None:
    material = _ready_op23()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP23_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP23_ACCEPTANCE_FAIL_CLOSED_FINALIZER_SCHEMA_VERSION
    assert material["operation_step_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP23_STEP_REF
    assert material["acceptance_finalizer_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP23_READY_STATUS_REF
    assert material["acceptance_finalizer_ready"] is True
    assert material["acceptance_finalizer_blocker_refs"] == []
    assert tuple(material["ready_condition_refs"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP23_READY_CONDITION_REFS
    assert all(material["ready_condition_pass_flags"].values())
    assert material["ready_condition_pass_count"] == len(pmn.P7_R54_AHR_POST_MN11_PMN_OP23_READY_CONDITION_REFS)
    assert tuple(material["fail_closed_condition_refs"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP23_FAIL_CLOSED_CONDITION_REFS
    assert material["observed_fail_closed_condition_refs"] == []
    assert material["scope_confirmed"] is True
    assert material["mn11_return_operation_required_intake_passed"] is True
    assert material["local_only_preflight_passed"] is True
    assert material["actual_source_guard_passed"] is True
    assert material["no_body_leak_validation_passed"] is True
    assert material["no_question_text_validation_passed"] is True
    assert material["no_path_hash_validation_passed"] is True
    assert material["no_touch_validation_passed"] is True
    assert material["no_promotion_boundary_confirmed"] is True
    assert material["actual_review_evidence_complete"] is True
    assert material["actual_review_evidence_complete_from_real_review"] is True
    assert material["actual_review_evidence_complete_from_real_operation_claimed_here"] is False
    assert material["post_mn11_actual_operation_acceptance_ready"] is True
    assert material["post_mn11_actual_operation_ready_for_downstream_manual_decision_hold"] is True
    assert material["acceptance_ready_without_downstream_promotion"] is True
    assert material["fail_closed_finalizer_does_not_generate_body_full_packet"] is True
    assert material["fail_closed_finalizer_does_not_run_actual_human_review"] is True
    assert material["fail_closed_finalizer_does_not_create_actual_rows"] is True
    assert material["fail_closed_finalizer_does_not_execute_validation_commands"] is True
    assert material["fail_closed_finalizer_does_not_execute_postcr22_reentry"] is True
    assert material["manual_decision_auto_executes_downstream"] is False
    assert material["p5_final_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert material["full_backend_suite_green_claimed_here"] is False
    assert material["rn_contract_green_claimed_here"] is False
    assert material["rn_real_device_modal_verified_claimed_here"] is False
    assert tuple(material["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP23_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP23_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP23_DOWNSTREAM_MANUAL_DECISION_HOLD_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op23_acceptance_fail_closed_finalizer_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(
        material,
        allowed_true_false_flags=pmn.P7_R54_AHR_POST_MN11_PMN_OP23_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("acceptance_finalizer_ready", False),
        ("scope_confirmed", False),
        ("mn11_return_operation_required_intake_passed", False),
        ("actual_source_guard_passed", False),
        ("no_body_leak_validation_passed", False),
        ("no_question_text_validation_passed", False),
        ("no_path_hash_validation_passed", False),
        ("no_touch_validation_passed", False),
        ("no_promotion_boundary_confirmed", False),
        ("actual_review_evidence_complete", False),
        ("actual_review_evidence_complete_from_real_review", False),
        ("actual_review_evidence_complete_from_real_operation_claimed_here", True),
        ("manual_decision_auto_executes_downstream", True),
        ("p5_final_allowed", True),
        ("p8_start_allowed", True),
        ("actual_r52_reintake_execution_confirmed", True),
        ("release_allowed", True),
        ("full_backend_suite_green_claimed_here", True),
    ],
)
def test_pmn_op23_contract_rejects_acceptance_ready_condition_or_promotion_mutation(field: str, bad_value: object) -> None:
    material = _ready_op23()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op23_acceptance_fail_closed_finalizer_contract(mutated)


def test_pmn_op22_op23_aliases_match_primary_builders_and_contracts() -> None:
    op21 = _ready_op21()
    primary_op22 = _ready_op22(op21)
    alias_op22 = pmn.build_p7_r54_ahr_post_mn11_actual_operation_validation_command_matrix_result_memo_envelope_bodyfree(
        existing_postcr22_ex07_ex18_reentry_mapping=op21,
        target_test_status_refs=tuple("passed_bodyfree_" + ref for ref in pmn.P7_R54_AHR_POST_MN11_PMN_OP22_TARGET_TEST_COMMAND_REFS),
        selected_regression_status_refs=(
            "passed_bodyfree_pytest_post_ex18_mn00_mn11_selected_regression",
            "passed_bodyfree_pytest_postcr22_ex00_ex18_selected_regression",
        ),
        compileall_status_ref="passed_bodyfree_compileall_post_mn11_helper",
    )
    assert alias_op22 == primary_op22
    assert pmn.assert_p7_r54_ahr_post_mn11_actual_operation_validation_command_matrix_result_memo_envelope_bodyfree_contract(alias_op22) is True

    primary_op23 = _ready_op23(primary_op22)
    alias_op23 = pmn.build_p7_r54_ahr_post_mn11_actual_operation_acceptance_fail_closed_finalizer_bodyfree(
        validation_command_matrix_result_memo_envelope=primary_op22
    )
    assert alias_op23 == primary_op23
    assert pmn.assert_p7_r54_ahr_post_mn11_actual_operation_acceptance_fail_closed_finalizer_bodyfree_contract(alias_op23) is True
