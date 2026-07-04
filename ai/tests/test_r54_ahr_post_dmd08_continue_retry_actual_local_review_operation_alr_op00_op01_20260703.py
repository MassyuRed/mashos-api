# -*- coding: utf-8 -*-
"""R54-AHR Post-DMD08 actual local review operation ALR-OP00/OP01 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_20260703 as alr
import emlis_ai_p7_r54_ahr_post_dmh18_downstream_manual_decision_triage_20260703 as dmd

_EVIDENCE_INCOMPLETE_DMD08_CACHE: dict[str, object] | None = None
_REPAIR_DMD08_CACHE: dict[str, object] | None = None
_COMPLETE_DMD08_CACHE: dict[str, object] | None = None


def _dmd08_pass_status_refs() -> dict[str, str]:
    return {
        key: dmd.P7_R54_AHR_POST_DMH18_DMD_OP08_PASS_STATUS_REF
        for key in dmd.P7_R54_AHR_POST_DMH18_DMD_OP08_TARGET_TEST_GROUP_REFS
    }


def _dmd08_pass_count_refs() -> dict[str, int]:
    return {key: 1 for key in dmd.P7_R54_AHR_POST_DMH18_DMD_OP08_TARGET_TEST_GROUP_REFS}


def _dmd08_regression_pass_status_refs() -> dict[str, str]:
    return {
        key: dmd.P7_R54_AHR_POST_DMH18_DMD_OP08_PASS_STATUS_REF
        for key in dmd.P7_R54_AHR_POST_DMH18_DMD_OP08_SELECTED_REGRESSION_GROUP_REFS
    }


def _dmd08_regression_pass_count_refs() -> dict[str, int]:
    return {key: 1 for key in dmd.P7_R54_AHR_POST_DMH18_DMD_OP08_SELECTED_REGRESSION_GROUP_REFS}


def _closed_dmd08_kwargs() -> dict[str, object]:
    return {
        "target_test_result_status_refs": _dmd08_pass_status_refs(),
        "target_test_result_count_refs": _dmd08_pass_count_refs(),
        "selected_regression_result_status_refs": _dmd08_regression_pass_status_refs(),
        "selected_regression_result_count_refs": _dmd08_regression_pass_count_refs(),
        "compileall_result_status_ref": dmd.P7_R54_AHR_POST_DMH18_DMD_OP08_PASS_STATUS_REF,
        "compileall_result_count_ref": "passed",
    }


def _evidence_incomplete_dmd08() -> dict[str, object]:
    global _EVIDENCE_INCOMPLETE_DMD08_CACHE
    if _EVIDENCE_INCOMPLETE_DMD08_CACHE is None:
        material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op08_bodyfree_result_memo_target_tests_regression_closure(
            **_closed_dmd08_kwargs()
        )
        assert material["branch_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_INCOMPLETE_REF
        assert material["next_required_step"] == dmd.P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_CONTINUE_OR_RETRY_ACTUAL_REVIEW_REF
        assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op08_bodyfree_result_memo_target_tests_regression_closure_contract(material) is True
        _EVIDENCE_INCOMPLETE_DMD08_CACHE = material
    return deepcopy(_EVIDENCE_INCOMPLETE_DMD08_CACHE)


def _repair_dmd08() -> dict[str, object]:
    global _REPAIR_DMD08_CACHE
    if _REPAIR_DMD08_CACHE is None:
        material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op08_bodyfree_result_memo_target_tests_regression_closure(
            manual_decision_materialization={"raw_input": "must not leak from DMD OP08"},
            **_closed_dmd08_kwargs(),
        )
        assert material["branch_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF
        assert material["next_required_step"] == dmd.P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_STOP_AND_REPAIR_BODYFREE_REF
        assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op08_bodyfree_result_memo_target_tests_regression_closure_contract(material) is True
        _REPAIR_DMD08_CACHE = material
    return deepcopy(_REPAIR_DMD08_CACHE)


def _complete_receipt() -> dict[str, object]:
    return {
        "schema_version": dmd.P7_R54_AHR_POST_DMH18_DMD_ACTUAL_OPERATION_EVIDENCE_RECEIPT_SCHEMA_VERSION,
        "operation_receipt_ref": "actual_receipt_bodyfree_fixture",
        "review_session_id": dmd.P7_R54_AHR_POST_DMH18_DMD_DEFAULT_REVIEW_SESSION_ID,
        "source_kind_ref": dmd.P7_R54_AHR_POST_DMH18_DMD_ACTUAL_OPERATION_SOURCE_KIND_REF,
        "created_from_real_operation": True,
        "actual_source_guard_passed": True,
        "actual_human_review_executed_by_person": True,
        "reviewed_case_count": dmd.P7_R54_AHR_POST_DMH18_DMD_REQUIRED_EVIDENCE_COUNT,
        "selection_row_count": dmd.P7_R54_AHR_POST_DMH18_DMD_REQUIRED_EVIDENCE_COUNT,
        "sanitized_review_result_row_count": dmd.P7_R54_AHR_POST_DMH18_DMD_REQUIRED_EVIDENCE_COUNT,
        "rating_row_count": dmd.P7_R54_AHR_POST_DMH18_DMD_REQUIRED_EVIDENCE_COUNT,
        "question_need_observation_row_count": dmd.P7_R54_AHR_POST_DMH18_DMD_REQUIRED_EVIDENCE_COUNT,
        "disposal_purge_receipt_accepted": True,
        "no_body_leak_validation_passed": True,
        "no_question_text_validation_passed": True,
        "no_path_hash_validation_passed": True,
        "no_terminal_output_body_validation_passed": True,
        "no_touch_validation_passed": True,
        "body_free": True,
    }


def _complete_manual_decision_dmd08() -> dict[str, object]:
    global _COMPLETE_DMD08_CACHE
    if _COMPLETE_DMD08_CACHE is None:
        op07 = dmd.build_p7_r54_ahr_post_dmh18_dmd_op07_manual_decision_materialization(
            actual_operation_evidence_receipt_bodyfree_optional=_complete_receipt()
        )
        assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op07_manual_decision_materialization_contract(op07) is True
        material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op08_bodyfree_result_memo_target_tests_regression_closure(
            manual_decision_materialization=op07,
            **_closed_dmd08_kwargs(),
        )
        assert material["branch_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_COMPLETE_MANUAL_DECISION_NO_AUTO_EXEC_REF
        assert material["next_required_step"] == dmd.P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_DOWNSTREAM_MANUAL_DECISION_NO_AUTO_EXEC_REF
        assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op08_bodyfree_result_memo_target_tests_regression_closure_contract(material) is True
        _COMPLETE_DMD08_CACHE = material
    return deepcopy(_COMPLETE_DMD08_CACHE)


def _assert_common_bodyfree_no_touch_no_promotion(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    for field in alr.P7_R54_AHR_POST_DMD08_ALR_REQUIRED_FALSE_FLAG_REFS:
        assert material[field] is False, field
    for marker_map_key in ("public_contract", "post_dmd08_no_touch_contract", "body_free_markers"):
        assert material[marker_map_key]
        assert all(value is False for value in material[marker_map_key].values()), marker_map_key
    assert all(value is False for value in material["not_claimed_boundary"].values())


def test_alr_op00_refreezes_scope_no_touch_no_promotion_after_dmd_op08() -> None:
    material = alr.build_p7_r54_ahr_post_dmd08_alr_op00_scope_no_touch_no_promotion_refreeze()

    assert set(material) == set(alr.P7_R54_AHR_POST_DMD08_ALR_OP00_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP00_SCHEMA_VERSION
    assert material["phase"] == alr.P7_R54_AHR_POST_DMD08_ALR_PHASE
    assert material["source_mode"] == alr.P7_R54_AHR_POST_DMD08_ALR_SOURCE_MODE
    assert material["selected_stage_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_SELECTED_STAGE_REF
    assert material["selected_step_prefix_ref"] == "ALR-OP"
    assert material["expected_current_dmd_branch_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_INCOMPLETE_REF
    assert material["expected_current_dmd_next_required_step_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_CONTINUE_OR_RETRY_ACTUAL_REVIEW_REF
    assert material["expected_current_alr_action_if_no_external_receipt_ref"] == "ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED"
    assert material["alr_op00_scope_confirmed"] is True
    assert material["alr_op00_no_touch_boundary_confirmed"] is True
    assert material["alr_op00_no_promotion_boundary_confirmed"] is True
    assert material["alr_op00_does_not_intake_dmd_op08_result_memo"] is True
    assert material["alr_op00_does_not_generate_body_full_packet"] is True
    assert material["alr_op00_does_not_run_actual_local_human_review"] is True
    assert tuple(material["implemented_steps"]) == alr.P7_R54_AHR_POST_DMD08_ALR_OP00_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == alr.P7_R54_AHR_POST_DMD08_ALR_OP00_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP01_STEP_REF
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op00_scope_no_touch_no_promotion_refreeze_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("body_free", False),
        ("git_checked", True),
        ("alr_op00_no_touch_boundary_confirmed", False),
        ("alr_op00_no_promotion_boundary_confirmed", False),
        ("alr_op00_does_not_start_p8_p6_r52_or_release", False),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("manual_decision_auto_executes_downstream", True),
        ("next_required_step", alr.P7_R54_AHR_POST_DMD08_ALR_OP02_STEP_REF),
    ],
)
def test_alr_op00_contract_rejects_scope_or_promotion_mutations(field: str, bad_value: object) -> None:
    material = alr.build_p7_r54_ahr_post_dmd08_alr_op00_scope_no_touch_no_promotion_refreeze()
    material[field] = bad_value

    with pytest.raises(ValueError):
        alr.assert_p7_r54_ahr_post_dmd08_alr_op00_scope_no_touch_no_promotion_refreeze_contract(material)


def test_alr_op00_contract_rejects_public_contract_marker_mutation() -> None:
    material = alr.build_p7_r54_ahr_post_dmd08_alr_op00_scope_no_touch_no_promotion_refreeze()
    material["public_contract"]["api_response_key_added"] = True

    with pytest.raises(ValueError):
        alr.assert_p7_r54_ahr_post_dmd08_alr_op00_scope_no_touch_no_promotion_refreeze_contract(material)


def test_alr_op00_contract_rejects_forbidden_top_level_payload_key() -> None:
    material = alr.build_p7_r54_ahr_post_dmd08_alr_op00_scope_no_touch_no_promotion_refreeze()
    material["raw_input"] = "must never pass"

    with pytest.raises(ValueError):
        alr.assert_p7_r54_ahr_post_dmd08_alr_op00_scope_no_touch_no_promotion_refreeze_contract(material)


def test_alr_op01_accepts_current_dmd08_evidence_incomplete_branch_and_passes_to_op02() -> None:
    material = alr.build_p7_r54_ahr_post_dmd08_alr_op01_dmd_op08_result_memo_branch_intake(
        dmd_op08_bodyfree_result_memo_target_tests_regression_closure=_evidence_incomplete_dmd08(),
    )

    assert set(material) == set(alr.P7_R54_AHR_POST_DMD08_ALR_OP01_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP01_SCHEMA_VERSION
    assert material["alr_op01_intake_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP01_STATUS_ACCEPTED_EVIDENCE_INCOMPLETE_REF
    assert material["alr_op01_ready"] is True
    assert material["dmd_op08_contract_valid"] is True
    assert material["dmd_op08_branch_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_INCOMPLETE_REF
    assert material["dmd_op08_next_required_step"] == dmd.P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_CONTINUE_OR_RETRY_ACTUAL_REVIEW_REF
    assert material["dmd_op08_evidence_incomplete_continue_or_retry_required"] is True
    assert material["alr_op01_route_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP01_ROUTE_CONTINUE_RETRY_RESOLVER_REQUIRED_REF
    assert material["alr_op01_does_not_resolve_continue_retry_final_action"] is True
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP02_STEP_REF
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op01_dmd_op08_result_memo_branch_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op01_accepts_dmd08_repair_branch_without_running_actual_review() -> None:
    material = alr.build_p7_r54_ahr_post_dmd08_alr_op01_dmd_op08_result_memo_branch_intake(
        dmd_op08_bodyfree_result_memo_target_tests_regression_closure=_repair_dmd08(),
    )

    assert material["alr_op01_intake_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP01_STATUS_ACCEPTED_REPAIR_REQUIRED_REF
    assert material["alr_op01_ready"] is True
    assert material["dmd_op08_branch_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF
    assert material["dmd_op08_bodyfree_evidence_boundary_repair_required"] is True
    assert material["alr_op01_route_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP01_ROUTE_REPAIR_STOP_CANDIDATE_REF
    assert material["actual_local_human_review_executed_here"] is False
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP02_STEP_REF
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op01_dmd_op08_result_memo_branch_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op01_accepts_dmd08_complete_manual_decision_branch_without_auto_execution() -> None:
    material = alr.build_p7_r54_ahr_post_dmd08_alr_op01_dmd_op08_result_memo_branch_intake(
        dmd_op08_bodyfree_result_memo_target_tests_regression_closure=_complete_manual_decision_dmd08(),
    )

    assert material["alr_op01_intake_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP01_STATUS_ACCEPTED_COMPLETE_MANUAL_DECISION_REF
    assert material["alr_op01_ready"] is True
    assert material["dmd_op08_branch_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_COMPLETE_MANUAL_DECISION_NO_AUTO_EXEC_REF
    assert material["dmd_op08_downstream_manual_decision_required_without_auto_execution"] is True
    assert material["alr_op01_route_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP01_ROUTE_COMPLETE_RECEIPT_MANUAL_DECISION_CANDIDATE_REF
    assert material["manual_decision_auto_executes_downstream"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP02_STEP_REF
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op01_dmd_op08_result_memo_branch_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op01_missing_dmd08_result_memo_goes_to_repair_without_claiming_review() -> None:
    material = alr.build_p7_r54_ahr_post_dmd08_alr_op01_dmd_op08_result_memo_branch_intake()

    assert material["alr_op01_intake_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP01_STATUS_INVALID_OR_MISSING_REF
    assert material["alr_op01_ready"] is False
    assert material["dmd_op08_result_memo_present"] is False
    assert material["dmd_op08_contract_valid"] is False
    assert material["alr_op01_route_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP01_ROUTE_INVALID_INTAKE_REPAIR_REQUIRED_REF
    assert "alr_op01_dmd_op08_result_memo_missing" in material["alr_op01_blocker_refs"]
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF
    assert material["actual_local_human_review_executed_here"] is False
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op01_dmd_op08_result_memo_branch_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op01_forbidden_payload_in_dmd08_goes_to_repair_without_leaking_body_value() -> None:
    dmd08 = _evidence_incomplete_dmd08()
    dmd08["raw_input"] = "this body must not appear in ALR output"
    material = alr.build_p7_r54_ahr_post_dmd08_alr_op01_dmd_op08_result_memo_branch_intake(
        dmd_op08_bodyfree_result_memo_target_tests_regression_closure=dmd08,
    )

    assert material["alr_op01_intake_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP01_STATUS_INVALID_OR_MISSING_REF
    assert material["alr_op01_route_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP01_ROUTE_INVALID_INTAKE_REPAIR_REQUIRED_REF
    assert material["dmd_op08_forbidden_payload_key_path_count"] == 1
    assert material["dmd_op08_forbidden_payload_key_paths"] == ["dmd_op08.raw_input"]
    assert "this body must not appear" not in repr(material)
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op01_dmd_op08_result_memo_branch_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op01_promotion_claim_in_dmd08_goes_to_repair_without_downstream_execution() -> None:
    dmd08 = _evidence_incomplete_dmd08()
    dmd08["p8_start_allowed"] = True
    material = alr.build_p7_r54_ahr_post_dmd08_alr_op01_dmd_op08_result_memo_branch_intake(
        dmd_op08_bodyfree_result_memo_target_tests_regression_closure=dmd08,
    )

    assert material["alr_op01_intake_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP01_STATUS_INVALID_OR_MISSING_REF
    assert "p8_start_allowed" in material["dmd_op08_promotion_claim_refs"]
    assert material["p8_start_allowed"] is False
    assert material["manual_decision_auto_executes_downstream"] is False
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op01_dmd_op08_result_memo_branch_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op01_contract_rejects_dmd_not_executed_boundary_mutation() -> None:
    material = alr.build_p7_r54_ahr_post_dmd08_alr_op01_dmd_op08_result_memo_branch_intake(
        dmd_op08_bodyfree_result_memo_target_tests_regression_closure=_evidence_incomplete_dmd08(),
    )
    material["dmd_op08_not_executed_boundary_preserves_actual_review_unexecuted"] = False

    with pytest.raises(ValueError):
        alr.assert_p7_r54_ahr_post_dmd08_alr_op01_dmd_op08_result_memo_branch_intake_contract(material)


def test_alr_op01_contract_rejects_actual_review_execution_promotion_mutation() -> None:
    material = alr.build_p7_r54_ahr_post_dmd08_alr_op01_dmd_op08_result_memo_branch_intake(
        dmd_op08_bodyfree_result_memo_target_tests_regression_closure=_evidence_incomplete_dmd08(),
    )
    material["actual_local_human_review_executed_here"] = True

    with pytest.raises(ValueError):
        alr.assert_p7_r54_ahr_post_dmd08_alr_op01_dmd_op08_result_memo_branch_intake_contract(material)


def test_alr_op00_op01_alias_builders_and_contracts_match_canonical_functions() -> None:
    op00 = alr.build_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op00_scope_no_touch_no_promotion_refreeze()
    assert alr.assert_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op00_scope_no_touch_no_promotion_refreeze_contract(op00) is True

    op01 = alr.build_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op01_dmd_op08_result_memo_branch_intake(
        dmd_op08_bodyfree_result_memo_target_tests_regression_closure=_evidence_incomplete_dmd08(),
    )
    assert op01["alr_op01_intake_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP01_STATUS_ACCEPTED_EVIDENCE_INCOMPLETE_REF
    assert alr.assert_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op01_dmd_op08_result_memo_branch_intake_contract(op01) is True


def test_alr_op00_op01_result_memo_is_bodyfree_and_limited_to_current_scope() -> None:
    result_memo = TEST_DIR / "R54_AHR_PostDMD08_ContinueRetryActualLocalOnlyHumanReviewOperation_ALR_OP00_OP01_Result_20260703.md"
    text = result_memo.read_text(encoding="utf-8")

    for heading in (
        "## 1. Implementation scope",
        "## 2. Changed files",
        "## 3. ALR-OP00",
        "## 4. ALR-OP01",
        "## 5. Test results",
        "## 6. Not claimed",
        "## 7. Next required step",
    ):
        assert heading in text
    assert "ALR-OP02" in text
    assert "not implemented" in text
    forbidden_literals = (
        "raw_input:",
        "comment_text:",
        "question_text:",
        "draft_question_text:",
        "terminal output body",
    )
    for literal in forbidden_literals:
        assert literal not in text
