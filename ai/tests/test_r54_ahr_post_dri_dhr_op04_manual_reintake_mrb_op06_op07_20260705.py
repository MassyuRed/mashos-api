# -*- coding: utf-8 -*-
"""R54-AHR Post-DRI / DHR-OP04 manual re-intake MRB-OP06/OP07 tests."""

from __future__ import annotations

from pathlib import Path
import sys

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_20260705 as mrb
import emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704 as dhr
from test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op04_op05_20260705 import (
    _dhr_op03_waiting,
    _manual_request,
    _mrb_op02_ready,
    _mrb_op03_ready,
    _mrb_op04_ready,
    _op04_ready_with_mutated_envelope,
)


def _assert_common_bodyfree_no_touch_no_promotion(
    material: dict[str, object],
    *,
    allow_op04_called_by_mrb: bool = False,
    allow_confirmed: bool = False,
) -> None:
    assert material["source_mode"] == mrb.P7_R54_AHR_POST_DRI_MRB_SOURCE_MODE
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True
    assert all(value is False for value in material["public_contract"].values())
    assert all(value is False for value in material["mrb_no_touch_contract"].values())
    assert all(value is False for value in material["body_free_markers"].values())
    allowed_true = set()
    if allow_op04_called_by_mrb:
        allowed_true.add("dhr_op04_called_by_mrb")
    if allow_confirmed:
        allowed_true.add("actual_source_claim_confirmed_for_downstream_handoff")
    for key in mrb.P7_R54_AHR_POST_DRI_MRB_REQUIRED_FALSE_FLAG_REFS:
        if key not in allowed_true:
            assert material[key] is False, key


def _op05_confirmed() -> dict[str, object]:
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture(
        mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope=_mrb_op04_ready(),
    )
    assert material["mrb_op05_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_CONFIRMED_BODYFREE_STOPPED_REF
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture_contract(material) is True
    return material


def _op05_not_confirmed() -> dict[str, object]:
    op04 = _op04_ready_with_mutated_envelope(
        candidate_updates={
            "actual_local_only_human_review_by_person_confirmed": False,
            "actual_human_review_executed_by_person": False,
        }
    )
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture(
        mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope=op04,
    )
    assert material["mrb_op05_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_STOPPED_REF
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture_contract(material) is True
    return material


def _op05_waiting_result() -> dict[str, object]:
    op04 = _op04_ready_with_mutated_envelope(op03_material=_dhr_op03_waiting())
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture(
        mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope=op04,
    )
    assert material["mrb_op05_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_WAITING_EXTERNAL_CLAIM_STOPPED_REF
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture_contract(material) is True
    return material


def _op05_invalid_result() -> dict[str, object]:
    op04 = _op04_ready_with_mutated_envelope(
        candidate_updates={
            "source_kind_ref": "helper_generated_candidate_not_actual_source",
            "actual_source_claim_source_kind_ref": "helper_generated_candidate_not_actual_source",
        }
    )
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture(
        mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope=op04,
    )
    assert material["mrb_op05_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_INVALID_REPAIR_REQUIRED_STOPPED_REF
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture_contract(material) is True
    return material


def _op05_waiting_before_dhr_op04_call() -> dict[str, object]:
    op03_waiting = mrb.build_p7_r54_ahr_post_dri_mrb_op03_dhr_op03_ready_material_intake(
        mrb_op02_dri_op09_adapter_candidate_extraction_and_scan=_mrb_op02_ready(),
        dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction=_dhr_op03_waiting(),
    )
    op04_waiting = mrb.build_p7_r54_ahr_post_dri_mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope(
        mrb_op02_dri_op09_adapter_candidate_extraction_and_scan=_mrb_op02_ready(),
        mrb_op03_dhr_op03_ready_material_intake=op03_waiting,
        manual_reintake_request_bodyfree=_manual_request(),
    )
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture(
        mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope=op04_waiting,
    )
    assert material["mrb_op05_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP05_STATUS_WAITING_BEFORE_DHR_OP04_CALL_REF
    assert material["dhr_op04_result_captured"] is False
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture_contract(material) is True
    return material


def _op05_blocked_before_dhr_op04_call() -> dict[str, object]:
    request = _manual_request()
    request["raw_input"] = "blocked raw body must not be copied"
    op04_blocked = mrb.build_p7_r54_ahr_post_dri_mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope(
        mrb_op02_dri_op09_adapter_candidate_extraction_and_scan=_mrb_op02_ready(),
        mrb_op03_dhr_op03_ready_material_intake=_mrb_op03_ready(),
        manual_reintake_request_bodyfree=request,
    )
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture(
        mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope=op04_blocked,
    )
    assert material["mrb_op05_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP05_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
    assert material["dhr_op04_result_captured"] is False
    assert "blocked raw body must not be copied" not in repr(material)
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture_contract(material) is True
    return material


def _op06_from_op05(op05: dict[str, object]) -> dict[str, object]:
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op06_dhr_op04_result_classifier_stop_boundary(
        mrb_op05_explicit_manual_dhr_op04_call_and_result_capture=op05,
    )
    assert set(material) == set(mrb.P7_R54_AHR_POST_DRI_MRB_OP06_REQUIRED_FIELD_REFS)
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op06_dhr_op04_result_classifier_stop_boundary_contract(material) is True
    return material


def test_mrb_op06_maps_confirmed_result_to_confirmed_stopped_branch() -> None:
    material = _op06_from_op05(_op05_confirmed())

    assert material["schema_version"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP06_SCHEMA_VERSION
    assert material["operation_step_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP06_STEP_REF
    assert material["op05_contract_valid"] is True
    assert material["op05_dhr_op04_called_by_manual_reintake_boundary"] is True
    assert material["op05_dhr_op04_called_by_dri"] is False
    assert material["dhr_op04_result_captured"] is True
    assert material["dhr_op04_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_CONFIRMED_BODYFREE_REF
    assert material["mrb_branch_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_CONFIRMED_BODYFREE_STOPPED_REF
    assert material["mrb_op06_dhr_op04_confirmed_bodyfree_stopped"] is True
    assert material["exactly_one_mrb_result_branch"] is True
    assert material["actual_source_claim_confirmed_for_downstream_handoff"] is True
    assert material["mrb_next_required_step"] == mrb.P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_MANUAL_REVIEW_DHR_OP04_CONFIRMED_REF
    assert material["next_required_step"] == material["mrb_next_required_step"]
    assert material["mrb_op06_result_is_dhr_op04_only"] is True
    assert material["mrb_op06_does_not_call_dhr_op04_again"] is True
    assert material["mrb_op06_does_not_call_dhr_op05"] is True
    assert material["mrb_op06_does_not_call_dhr_op06"] is True
    assert material["dhr_op04_called_here"] is False
    assert material["dhr_op05_auto_call_allowed"] is False
    assert material["dhr_op06_auto_call_allowed"] is False
    assert material["downstream_auto_execution_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    _assert_common_bodyfree_no_touch_no_promotion(material, allow_op04_called_by_mrb=True, allow_confirmed=True)


def test_mrb_op06_maps_not_confirmed_result_to_retry_or_start_stopped_branch() -> None:
    material = _op06_from_op05(_op05_not_confirmed())

    assert material["dhr_op04_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_REF
    assert material["mrb_branch_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_STOPPED_REF
    assert material["mrb_op06_dhr_op04_not_confirmed_retry_or_start_required_stopped"] is True
    assert material["actual_source_claim_confirmed_for_downstream_handoff"] is False
    assert material["mrb_next_required_step"] == mrb.P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_MANUAL_REVIEW_DHR_OP04_NOT_CONFIRMED_REF
    assert material["dhr_op05_auto_call_allowed"] is False
    assert material["downstream_auto_execution_allowed"] is False
    _assert_common_bodyfree_no_touch_no_promotion(material, allow_op04_called_by_mrb=True)


def test_mrb_op06_maps_waiting_result_to_waiting_external_claim_stopped_branch() -> None:
    material = _op06_from_op05(_op05_waiting_result())

    assert material["dhr_op04_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_WAITING_FOR_EXTERNAL_BODYFREE_CLAIM_REF
    assert material["mrb_branch_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_WAITING_EXTERNAL_CLAIM_STOPPED_REF
    assert material["mrb_op06_dhr_op04_waiting_external_claim_stopped"] is True
    assert material["actual_source_claim_confirmed_for_downstream_handoff"] is False
    assert material["mrb_next_required_step"] == mrb.P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_WAIT_EXTERNAL_CLAIM_AFTER_DHR_OP04_REF
    assert material["dhr_op05_auto_call_allowed"] is False
    assert material["downstream_auto_execution_allowed"] is False
    _assert_common_bodyfree_no_touch_no_promotion(material, allow_op04_called_by_mrb=True)


def test_mrb_op06_maps_invalid_result_to_repair_stopped_branch() -> None:
    material = _op06_from_op05(_op05_invalid_result())

    assert material["dhr_op04_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_INVALID_REPAIR_REQUIRED_REF
    assert material["mrb_branch_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_INVALID_REPAIR_REQUIRED_STOPPED_REF
    assert material["mrb_op06_dhr_op04_invalid_repair_required_stopped"] is True
    assert material["actual_source_claim_confirmed_for_downstream_handoff"] is False
    assert material["mrb_next_required_step"] == mrb.P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_AFTER_DHR_OP04_REF
    assert material["dhr_op05_auto_call_allowed"] is False
    assert material["downstream_auto_execution_allowed"] is False
    _assert_common_bodyfree_no_touch_no_promotion(material, allow_op04_called_by_mrb=True)


def test_mrb_op06_waits_when_op05_stopped_before_dhr_op04_call() -> None:
    material = _op06_from_op05(_op05_waiting_before_dhr_op04_call())

    assert material["mrb_branch_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_WAITING_FOR_DRI_OR_DHR_OP03_MATERIAL_REF
    assert material["mrb_op06_waiting_before_dhr_op04_call_stopped"] is True
    assert material["dhr_op04_result_captured"] is False
    assert material["dhr_op04_result_bodyfree"] == {}
    assert "mrb_op05_waiting_before_dhr_op04_call" in material["mrb_op06_blocker_refs"]
    assert material["dhr_op04_called_here"] is False
    assert material["dhr_op05_auto_call_allowed"] is False
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_mrb_op06_blocks_bodyfree_leak_promotion_or_autorun_before_result() -> None:
    material = _op06_from_op05(_op05_blocked_before_dhr_op04_call())

    assert material["mrb_branch_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF
    assert material["mrb_op06_bodyfree_leak_promotion_or_autorun_blocked"] is True
    assert material["dhr_op04_result_captured"] is False
    assert material["dhr_op04_result_bodyfree"] == {}
    assert "mrb_op05_bodyfree_leak_promotion_or_autorun_blocked" in material["mrb_op06_blocker_refs"]
    assert "blocked raw body must not be copied" not in repr(material)
    assert material["dhr_op05_auto_call_allowed"] is False
    assert material["downstream_auto_execution_allowed"] is False
    _assert_common_bodyfree_no_touch_no_promotion(material)


def _op07_ready() -> dict[str, object]:
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op07_no_touch_selected_regression_guard(
        changed_file_refs=(
            "mashos-api/ai/services/ai_inference/emlis_ai_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_20260705.py",
            "mashos-api/ai/tests/test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op06_op07_20260705.py",
            "mashos-api/ai/tests/R54_AHR_PostDRI_DHROP04ManualReintake_MRB_OP06_OP07_Result_20260705.md",
        ),
        target_test_refs=mrb.P7_R54_AHR_POST_DRI_MRB_OP07_REQUIRED_TARGET_TEST_REFS,
        selected_regression_refs=mrb.P7_R54_AHR_POST_DRI_MRB_OP07_REQUIRED_SELECTED_REGRESSION_REFS,
        compileall_refs=mrb.P7_R54_AHR_POST_DRI_MRB_OP07_REQUIRED_COMPILEALL_REFS,
    )
    assert set(material) == set(mrb.P7_R54_AHR_POST_DRI_MRB_OP07_REQUIRED_FIELD_REFS)
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op07_no_touch_selected_regression_guard_contract(material) is True
    return material


def test_mrb_op07_allows_only_mrb_helper_tests_and_result_memo_changed_files() -> None:
    material = _op07_ready()

    assert material["schema_version"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP07_SCHEMA_VERSION
    assert material["operation_step_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP07_STEP_REF
    assert material["mrb_op07_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP07_STATUS_READY_FOR_OP08_REF
    assert material["changed_files_within_allowed_refs"] is True
    assert material["unexpected_changed_file_refs"] == []
    assert material["blocked_no_touch_change_refs"] == []
    assert material["target_tests_recorded"] is True
    assert material["selected_regression_recorded"] is True
    assert material["compileall_recorded"] is True
    assert material["missing_target_test_refs"] == []
    assert material["missing_selected_regression_refs"] == []
    assert material["missing_compileall_refs"] == []
    assert material["mrb_op07_does_not_change_api_db_rn_runtime_response_key"] is True
    assert material["mrb_op07_does_not_materialize_p8_question_spec"] is True
    assert material["next_required_step"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP08_STEP_REF
    assert material["dhr_op04_called_here"] is False
    assert material["dhr_op05_called_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_mrb_op07_blocks_cocolon_rn_api_db_response_key_runtime_or_p8_question_changes() -> None:
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op07_no_touch_selected_regression_guard(
        changed_file_refs=(
            "mashos-api/ai/services/ai_inference/emlis_ai_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_20260705.py",
            "Cocolon/src/screens/P8QuestionSurface.tsx",
            "mashos-api/ai/api/routes/response_key_question_route.py",
        ),
        target_test_refs=mrb.P7_R54_AHR_POST_DRI_MRB_OP07_REQUIRED_TARGET_TEST_REFS,
        selected_regression_refs=mrb.P7_R54_AHR_POST_DRI_MRB_OP07_REQUIRED_SELECTED_REGRESSION_REFS,
        compileall_refs=mrb.P7_R54_AHR_POST_DRI_MRB_OP07_REQUIRED_COMPILEALL_REFS,
    )

    assert material["mrb_op07_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP07_STATUS_BLOCKED_NO_TOUCH_CHANGE_REF
    assert material["mrb_op07_blocked_no_touch_change"] is True
    assert material["changed_files_within_allowed_refs"] is False
    assert material["api_db_rn_runtime_response_key_or_p8_question_touch_blocked"] is True
    assert material["unexpected_changed_file_refs"]
    assert material["blocked_no_touch_change_refs"]
    assert material["mrb_op07_blocker_refs"]
    assert material["dhr_op04_called_here"] is False
    assert material["dhr_op05_called_here"] is False
    assert material["p8_start_allowed"] is False
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op07_no_touch_selected_regression_guard_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_mrb_op07_waits_when_selected_regression_or_compileall_refs_are_missing() -> None:
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op07_no_touch_selected_regression_guard(
        changed_file_refs=(
            "services/ai_inference/emlis_ai_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_20260705.py",
            "tests/test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op06_op07_20260705.py",
        ),
        target_test_refs=mrb.P7_R54_AHR_POST_DRI_MRB_OP07_REQUIRED_TARGET_TEST_REFS[:-1],
        selected_regression_refs=mrb.P7_R54_AHR_POST_DRI_MRB_OP07_REQUIRED_SELECTED_REGRESSION_REFS[:-1],
        compileall_refs=mrb.P7_R54_AHR_POST_DRI_MRB_OP07_REQUIRED_COMPILEALL_REFS[:-1],
    )

    assert material["mrb_op07_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP07_STATUS_WAITING_FOR_VALIDATION_REFS_REF
    assert material["mrb_op07_waiting_for_validation_refs"] is True
    assert material["target_tests_recorded"] is False
    assert material["selected_regression_recorded"] is False
    assert material["compileall_recorded"] is False
    assert material["missing_target_test_refs"]
    assert material["missing_selected_regression_refs"]
    assert material["missing_compileall_refs"]
    assert "selected_regression_refs_missing" in material["mrb_op07_blocker_refs"]
    assert material["dhr_op05_called_here"] is False
    assert material["downstream_auto_execution_allowed"] is False
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op07_no_touch_selected_regression_guard_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_mrb_op06_op07_full_title_aliases_match_canonical_builders() -> None:
    op05 = _op05_confirmed()
    op06_a = mrb.build_p7_r54_ahr_post_dri_mrb_op06_dhr_op04_result_classifier_stop_boundary(
        mrb_op05_explicit_manual_dhr_op04_call_and_result_capture=op05,
    )
    op06_b = mrb.build_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op06_dhr_op04_result_classifier_stop_boundary(
        mrb_op05_explicit_manual_dhr_op04_call_and_result_capture=op05,
    )
    assert op06_a == op06_b

    op07_a = _op07_ready()
    op07_b = mrb.build_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op07_no_touch_selected_regression_guard(
        changed_file_refs=op07_a["changed_file_refs"],
        target_test_refs=op07_a["target_test_refs"],
        selected_regression_refs=op07_a["selected_regression_refs"],
        compileall_refs=op07_a["compileall_refs"],
        review_session_id=op07_a["review_session_id"],
    )
    assert op07_a == op07_b
