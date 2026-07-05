# -*- coding: utf-8 -*-
"""R54-AHR Post-DHR09 RSR-OP16 result memo/test/regression closure tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_20260704 as rsr
from test_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op02_op03_20260704 import (
    _assert_common_bodyfree_no_touch_no_promotion,
)
from test_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op14_op15_20260704 import (
    _rsr_op13_accepted,
    _rsr_op14_full_ready,
)


def _green_summary(status_ref: str, passed_count: int) -> dict[str, object]:
    return {
        "status_ref": status_ref,
        "passed_count": passed_count,
        "failed_count": 0,
        "timed_out": False,
        "body_free": True,
    }


def _compileall_ok() -> dict[str, object]:
    return {
        "status_ref": "services_ai_inference_compileall_ok",
        "passed_count": 0,
        "failed_count": 0,
        "timed_out": False,
        "ok": True,
        "body_free": True,
    }


def _op16_green_kwargs() -> dict[str, object]:
    return {
        "target_test_summary": _green_summary("rsr_op16_target_31_passed", 31),
        "rsr_accumulated_target_summary": _green_summary("rsr_op00_op16_accumulated_338_passed", 338),
        "dhr_selected_regression_summary": _green_summary("dhr_op00_op09_selected_regression_139_passed", 139),
        "elr_dmd_alr_selected_regression_summary": _green_summary("elr_dmd_alr_selected_regression_251_passed", 251),
        "compileall_summary": _compileall_ok(),
        "modified_file_refs": [
            "mashos-api/ai/services/ai_inference/emlis_ai_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_20260704.py",
        ],
        "new_file_refs": [
            "mashos-api/ai/tests/test_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op16_result_20260704.py",
            "mashos-api/ai/tests/R54_AHR_PostDHR09_ActualLocalReview_RetryStartDecision_RSR_OP00_OP16_Result_20260704.md",
        ],
    }


def _op15_complete_candidate() -> dict[str, object]:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op15_actual_evidence_complete_candidate_next_branch_resolver(
        final_validation=_rsr_op14_full_ready(),
    )
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op15_actual_evidence_complete_candidate_next_branch_resolver_contract(material) is True
    assert material["rsr_op15_branch_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_ACTUAL_REVIEW_EVIDENCE_READY_FOR_DHR_REINTAKE_NO_AUTO_EXECUTION_REF
    return material


def _op15_wait_for_allow() -> dict[str, object]:
    op14 = rsr.build_p7_r54_ahr_post_dhr09_rsr_op14_final_no_leak_no_promotion_source_kind_validation(
        disposal_purge_receipt_intake=_rsr_op13_accepted(),
    )
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op14_final_no_leak_no_promotion_source_kind_validation_contract(op14) is True
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op15_actual_evidence_complete_candidate_next_branch_resolver(final_validation=op14)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op15_actual_evidence_complete_candidate_next_branch_resolver_contract(material) is True
    assert material["rsr_op15_branch_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_WAIT_FOR_EXPLICIT_LOCAL_ONLY_ALLOW_REF
    return material


def _op16_closed(branch_resolution: dict[str, object] | None = None) -> dict[str, object]:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op16_result_memo_tests_selected_regression_closure(
        branch_resolution=branch_resolution or _op15_complete_candidate(),
        **_op16_green_kwargs(),
    )
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op16_result_memo_tests_selected_regression_closure_contract(material) is True
    assert material["rsr_op16_closed"] is True
    return material


def _assert_op16_no_execution_or_promotion(material: dict[str, object]) -> None:
    assert material["result_memo_created_here"] is False
    assert material["actual_review_evidence_complete_here"] is False
    assert material["downstream_auto_execution_allowed"] is False
    assert material["dmd_execution_started_here"] is False
    assert material["r52_actual_execution_started_here"] is False
    assert material["p5_final_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["p8_question_design_started"] is False
    assert material["p8_question_implementation_started"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert material["full_backend_suite_green_claimed_here"] is False
    assert material["rn_real_device_modal_verified_claimed_here"] is False
    assert material["rsr_op16_does_not_execute_actual_review"] is True
    assert material["rsr_op16_does_not_create_actual_receipts_or_rows"] is True
    assert material["rsr_op16_does_not_execute_disposal_purge"] is True
    assert material["rsr_op16_does_not_execute_dhr_reintake_dmd_or_r52"] is True
    assert material["rsr_op16_does_not_start_p5_p6_p8_p7_or_release"] is True
    assert material["rsr_op16_does_not_change_api_db_rn_runtime_response_key"] is True
    assert material["rsr_op16_does_not_materialize_p8_question_spec"] is True
    assert material["rsr_op16_does_not_claim_full_backend_or_rn_real_device_green"] is True


def test_rsr_op16_closes_result_memo_tests_and_selected_regression_bodyfree_for_complete_candidate_branch() -> None:
    material = _op16_closed()

    assert set(material) == set(rsr.P7_R54_AHR_POST_DHR09_RSR_OP16_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP16_SCHEMA_VERSION
    assert material["operation_step_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP16_STEP_REF
    assert material["rsr_op16_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_CLOSED_BODYFREE_REF
    assert material["op15_contract_valid"] is True
    assert material["op15_actual_evidence_complete_candidate"] is True
    assert material["selected_branch_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_ACTUAL_REVIEW_EVIDENCE_READY_FOR_DHR_REINTAKE_NO_AUTO_EXECUTION_REF
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_RETURN_TO_DHR_ACTUAL_SOURCE_CLAIM_REINTAKE_NO_AUTO_EXECUTION_REF
    assert material["result_memo_bodyfree_closed"] is True
    assert material["verification_all_required_summaries_green"] is True
    assert material["compileall_ok"] is True
    assert material["verification_total_passed_count"] == 759
    assert material["verification_total_failed_count"] == 0
    assert material["verification_summary_missing_refs"] == []
    assert material["verification_summary_non_green_refs"] == []
    assert material["implemented_steps"] == list(rsr.P7_R54_AHR_POST_DHR09_RSR_STEP_REFS)
    assert material["not_yet_implemented_steps"] == []
    _assert_common_bodyfree_no_touch_no_promotion(material)
    _assert_op16_no_execution_or_promotion(material)


def test_rsr_op16_closes_bodyfree_even_when_op15_selected_branch_waits_for_explicit_allow() -> None:
    material = _op16_closed(_op15_wait_for_allow())

    assert material["rsr_op16_closed"] is True
    assert material["op15_actual_evidence_complete_candidate"] is False
    assert material["selected_branch_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_WAIT_FOR_EXPLICIT_LOCAL_ONLY_ALLOW_REF
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_RETURN_TO_RSR_OP03_EXPLICIT_ALLOW_GATE_REF
    assert material["result_memo_bodyfree_closed"] is True
    assert material["actual_review_evidence_complete_here"] is False
    _assert_common_bodyfree_no_touch_no_promotion(material)
    _assert_op16_no_execution_or_promotion(material)


def test_rsr_op16_waits_when_op15_branch_resolution_is_missing() -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op16_result_memo_tests_selected_regression_closure(
        **_op16_green_kwargs(),
    )

    assert material["rsr_op16_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_WAITING_FOR_OP15_REF
    assert material["op15_contract_valid"] is False
    assert material["result_memo_bodyfree_closed"] is False
    assert "op15_branch_resolution_missing_or_invalid" in material["op16_blocker_refs"]
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_RSR_OP15_BRANCH_RESOLUTION_REF
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op16_result_memo_tests_selected_regression_closure_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)
    _assert_op16_no_execution_or_promotion(material)


@pytest.mark.parametrize(
    ("summary_key", "bad_summary", "expected_blocker"),
    [
        ("target_test_summary", {"status_ref": "rsr_op16_target_failed", "passed_count": 20, "failed_count": 1, "timed_out": False, "body_free": True}, "verification_failed_count_nonzero"),
        ("rsr_accumulated_target_summary", {"status_ref": "rsr_accumulated_timeout", "passed_count": 327, "failed_count": 0, "timed_out": True, "body_free": True}, "verification_timed_out"),
        ("compileall_summary", {"status_ref": "compileall_failed", "passed_count": 0, "failed_count": 1, "timed_out": False, "ok": False, "body_free": True}, "compileall_summary_not_green"),
    ],
)
def test_rsr_op16_repairs_when_target_or_regression_summary_is_not_green(summary_key: str, bad_summary: dict[str, object], expected_blocker: str) -> None:
    kwargs = _op16_green_kwargs()
    kwargs[summary_key] = bad_summary
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op16_result_memo_tests_selected_regression_closure(
        branch_resolution=_op15_complete_candidate(),
        **kwargs,
    )

    assert material["rsr_op16_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_REPAIR_REQUIRED_REF
    assert material["result_memo_bodyfree_closed"] is False
    assert expected_blocker in material["op16_blocker_refs"]
    assert "verification_summary_not_green" in material["op16_blocker_refs"]
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_RSR_OP16_TESTS_OR_REGRESSION_SUMMARY_REF
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op16_result_memo_tests_selected_regression_closure_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)
    _assert_op16_no_execution_or_promotion(material)


def test_rsr_op16_repairs_when_required_verification_summary_is_missing() -> None:
    kwargs = _op16_green_kwargs()
    kwargs["dhr_selected_regression_summary"] = None
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op16_result_memo_tests_selected_regression_closure(
        branch_resolution=_op15_complete_candidate(),
        **kwargs,
    )

    assert material["rsr_op16_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_REPAIR_REQUIRED_REF
    assert "dhr_op00_op09_selected_regression" in material["verification_summary_missing_refs"]
    assert "verification_summary_missing" in material["op16_blocker_refs"]
    assert material["result_memo_bodyfree_closed"] is False
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op16_result_memo_tests_selected_regression_closure_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)
    _assert_op16_no_execution_or_promotion(material)


@pytest.mark.parametrize(
    ("bad_summary", "expected_field"),
    [
        ({"status_ref": "bad", "passed_count": 1, "failed_count": 0, "question_text": "must not leak this question"}, "op16_forbidden_payload_key_path_refs"),
        ({"status_ref": "bad", "passed_count": 1, "failed_count": 0, "local_path": "/mnt/private/body-full-packet"}, "op16_forbidden_payload_key_path_refs"),
    ],
)
def test_rsr_op16_blocks_body_or_path_leak_in_result_memo_summaries_without_leaking_values(bad_summary: dict[str, object], expected_field: str) -> None:
    kwargs = _op16_green_kwargs()
    kwargs["target_test_summary"] = bad_summary
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op16_result_memo_tests_selected_regression_closure(
        branch_resolution=_op15_complete_candidate(),
        **kwargs,
    )

    assert material["rsr_op16_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_BODY_LEAK_OR_PROMOTION_BLOCKED_REF
    assert material[expected_field]
    assert "result_memo_body_leak_or_promotion_detected" in material["op16_blocker_refs"]
    assert "must not leak this question" not in repr(material)
    assert "/mnt/private/body-full-packet" not in repr(material)
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_RSR_OP16_BODY_LEAK_OR_PROMOTION_REF
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op16_result_memo_tests_selected_regression_closure_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)
    _assert_op16_no_execution_or_promotion(material)


@pytest.mark.parametrize(
    ("additional_material", "expected_ref"),
    [
        ({"release_allowed": True}, "release_allowed"),
        ({"p8_question_design_started": True}, "p8_question_design_started"),
        ({"dmd_execution_started_here": True}, "dmd_execution_started_here"),
    ],
)
def test_rsr_op16_blocks_downstream_promotion_claims_in_additional_material(additional_material: dict[str, object], expected_ref: str) -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op16_result_memo_tests_selected_regression_closure(
        branch_resolution=_op15_complete_candidate(),
        additional_bodyfree_materials={"bad_material": additional_material},
        **_op16_green_kwargs(),
    )

    assert material["rsr_op16_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_BODY_LEAK_OR_PROMOTION_BLOCKED_REF
    assert expected_ref in material["op16_promotion_claim_refs"]
    assert "result_memo_body_leak_or_promotion_detected" in material["op16_blocker_refs"]
    assert material["result_memo_bodyfree_closed"] is False
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op16_result_memo_tests_selected_regression_closure_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)
    _assert_op16_no_execution_or_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("result_memo_bodyfree_closed", False),
        ("verification_all_required_summaries_green", False),
        ("compileall_ok", False),
        ("verification_total_failed_count", 1),
        ("verification_summary_non_green_refs", ["rsr_op16_target_tests"]),
        ("next_required_step", rsr.P7_R54_AHR_POST_DHR09_RSR_OP16_STEP_REF),
    ],
)
def test_rsr_op16_contract_rejects_closed_branch_mutations(field: str, bad_value: object) -> None:
    material = _op16_closed()
    material[field] = bad_value

    with pytest.raises(ValueError):
        rsr.assert_p7_r54_ahr_post_dhr09_rsr_op16_result_memo_tests_selected_regression_closure_contract(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("result_memo_created_here", True),
        ("actual_review_evidence_complete_here", True),
        ("downstream_auto_execution_allowed", True),
        ("dmd_execution_started_here", True),
        ("r52_actual_execution_started_here", True),
        ("p8_start_allowed", True),
        ("p8_question_design_started", True),
        ("p7_complete", True),
        ("release_allowed", True),
        ("full_backend_suite_green_claimed_here", True),
        ("rn_real_device_modal_verified_claimed_here", True),
    ],
)
def test_rsr_op16_contract_rejects_execution_promotion_or_green_claim_mutations(field: str, bad_value: object) -> None:
    material = _op16_closed()
    material[field] = bad_value

    with pytest.raises(ValueError):
        rsr.assert_p7_r54_ahr_post_dhr09_rsr_op16_result_memo_tests_selected_regression_closure_contract(material)


def test_rsr_op16_contract_rejects_changed_file_ref_mismatch() -> None:
    material = _op16_closed()
    material["changed_file_refs"] = ["mashos-api/ai/services/ai_inference/only_modified.py"]
    material["changed_file_ref_count"] = 1

    with pytest.raises(ValueError):
        rsr.assert_p7_r54_ahr_post_dhr09_rsr_op16_result_memo_tests_selected_regression_closure_contract(material)


def test_rsr_op16_full_title_aliases_match_canonical_builders() -> None:
    kwargs = _op16_green_kwargs()
    branch_resolution = _op15_complete_candidate()
    canonical = rsr.build_p7_r54_ahr_post_dhr09_rsr_op16_result_memo_tests_selected_regression_closure(
        branch_resolution=branch_resolution,
        **kwargs,
    )
    alias = rsr.build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op16_result_memo_tests_selected_regression_closure(
        branch_resolution=branch_resolution,
        **kwargs,
    )

    assert alias == canonical
    assert rsr.assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op16_result_memo_tests_selected_regression_closure_contract(alias) is True
