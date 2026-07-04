# -*- coding: utf-8 -*-
"""R54-AHR Post-DMH18 downstream manual decision triage DMD-OP08 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_dmh18_downstream_manual_decision_triage_20260703 as dmd


def _target_statuses(status: str = "passed") -> dict[str, str]:
    return {key: status for key in dmd.P7_R54_AHR_POST_DMH18_DMD_OP08_TARGET_TEST_GROUP_REFS}


def _target_counts() -> dict[str, int]:
    return {
        "dmd_op00_op01_target": 20,
        "dmd_op02_op03_target": 17,
        "dmd_op04_op05_target": 20,
        "dmd_op06_op07_target": 8,
        "dmd_op08_target": 9,
    }


def _regression_statuses(status: str = "passed") -> dict[str, str]:
    return {key: status for key in dmd.P7_R54_AHR_POST_DMH18_DMD_OP08_SELECTED_REGRESSION_GROUP_REFS}


def _regression_counts() -> dict[str, int]:
    return {
        "dmh_op18_selected_regression": 42,
        "dmh_op16_op17_selected_regression": 79,
        "pmn_op22_op23_selected_regression": 37,
    }


def _closed_material() -> dict[str, object]:
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op08_bodyfree_result_memo_target_tests_regression_closure(
        target_test_result_status_refs=_target_statuses(),
        target_test_result_count_refs=_target_counts(),
        selected_regression_result_status_refs=_regression_statuses(),
        selected_regression_result_count_refs=_regression_counts(),
        compileall_result_status_ref="passed",
        compileall_result_count_ref="passed",
    )
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op08_bodyfree_result_memo_target_tests_regression_closure_contract(material) is True
    return material


def _assert_common_bodyfree_no_touch_no_promotion(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    for field in dmd.P7_R54_AHR_POST_DMH18_DMD_REQUIRED_FALSE_FLAG_REFS:
        assert material[field] is False, field
    for marker_map_key in ("public_contract", "post_dmh18_no_touch_contract", "body_free_markers"):
        assert material[marker_map_key]
        assert all(value is False for value in material[marker_map_key].values()), marker_map_key
    assert all(value is False for value in material["not_claimed_boundary"].values())
    assert all(value is False for value in material["not_executed_boundary"].values())
    assert all(value is False for value in material["unverified_boundary"].values())


def test_dmd_op08_without_external_validation_status_is_bodyfree_but_unverified() -> None:
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op08_bodyfree_result_memo_target_tests_regression_closure()

    assert set(material) == set(dmd.P7_R54_AHR_POST_DMH18_DMD_OP08_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP08_SCHEMA_VERSION
    assert material["dmd_op08_status_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP08_STATUS_INCOMPLETE_OR_UNVERIFIED_REF
    assert material["dmd_op08_ready"] is False
    assert material["target_tests_closed_by_external_status_summary"] is False
    assert material["selected_regression_closed_by_external_status_summary"] is False
    assert material["compileall_closed_by_external_status_summary"] is False
    assert material["branch_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_INCOMPLETE_REF
    assert material["next_required_step"] == dmd.P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_CONTINUE_OR_RETRY_ACTUAL_REVIEW_REF
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op08_bodyfree_result_memo_target_tests_regression_closure_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dmd_op08_closes_bodyfree_result_memo_when_external_status_summaries_are_passed() -> None:
    material = _closed_material()

    assert material["dmd_op08_status_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP08_STATUS_CLOSED_REF
    assert material["dmd_op08_ready"] is True
    assert material["result_memo_bodyfree_closed"] is True
    assert material["result_memo_sections_fixed"] is True
    assert tuple(material["result_memo_section_refs"]) == dmd.P7_R54_AHR_POST_DMH18_DMD_OP08_RESULT_MEMO_SECTION_REFS
    assert material["target_tests_closed_by_external_status_summary"] is True
    assert material["selected_regression_closed_by_external_status_summary"] is True
    assert material["compileall_closed_by_external_status_summary"] is True
    assert material["target_test_result_count_refs"]["dmd_op00_op01_target"] == 20
    assert material["selected_regression_result_count_refs"]["dmh_op18_selected_regression"] == 42
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dmd_op08_preserves_current_branch_a_and_does_not_promote_downstream() -> None:
    material = _closed_material()

    assert isinstance(material["candidate_supported"], bool)
    assert material["claimed_from_real_operation"] is False
    assert material["branch_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_INCOMPLETE_REF
    assert material["evidence_incomplete_continue_or_retry_required"] is True
    assert material["downstream_manual_decision_required_without_auto_execution"] is False
    assert material["manual_decision_auto_executes_downstream"] is False
    assert material["postcr22_ex07_ex18_reentry_executed_here"] is False
    assert material["r52_actual_execution_started_here"] is False
    assert material["p5_final_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False


def test_dmd_op08_records_only_bodyfree_validation_summaries_not_command_execution() -> None:
    material = _closed_material()

    assert material["dmd_op08_helper_does_not_run_pytest_or_compileall"] is True
    assert material["target_tests"]["pytest_execution_run_by_helper"] is False
    assert material["selected_regression"]["pytest_execution_run_by_helper"] is False
    assert material["compileall"]["compileall_execution_run_by_helper"] is False
    assert material["compileall"]["terminal_output_body_included"] is False


def test_dmd_op08_repair_branch_when_op07_material_is_invalid() -> None:
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op08_bodyfree_result_memo_target_tests_regression_closure(
        manual_decision_materialization={"schema_version": "invalid_op07_material"},
        target_test_result_status_refs=_target_statuses(),
        selected_regression_result_status_refs=_regression_statuses(),
        compileall_result_status_ref="passed",
    )

    assert material["dmd_op08_status_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP08_STATUS_REPAIR_REQUIRED_REF
    assert material["dmd_op08_ready"] is False
    assert material["branch_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF
    assert material["bodyfree_evidence_boundary_repair_required"] is True
    assert material["next_required_step"] == dmd.P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_STOP_AND_REPAIR_BODYFREE_REF
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op08_bodyfree_result_memo_target_tests_regression_closure_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dmd_op08_rejects_result_memo_section_tampering() -> None:
    material = _closed_material()
    material["result_memo_section_refs"] = list(material["result_memo_section_refs"][:-1])
    material["result_memo_section_ref_count"] = len(material["result_memo_section_refs"])

    with pytest.raises(ValueError):
        dmd.assert_p7_r54_ahr_post_dmh18_dmd_op08_bodyfree_result_memo_target_tests_regression_closure_contract(material)


def test_dmd_op08_rejects_status_count_tampering() -> None:
    material = _closed_material()
    material["target_test_result_status_ref_count"] = 0

    with pytest.raises(ValueError):
        dmd.assert_p7_r54_ahr_post_dmh18_dmd_op08_bodyfree_result_memo_target_tests_regression_closure_contract(material)


def test_dmd_op08_rejects_forbidden_payload_key_or_downstream_promotion_tampering() -> None:
    material = _closed_material()
    forbidden = deepcopy(material)
    forbidden["target_tests"]["stdout"] = "not body-free"
    with pytest.raises(ValueError):
        dmd.assert_p7_r54_ahr_post_dmh18_dmd_op08_bodyfree_result_memo_target_tests_regression_closure_contract(forbidden)

    promoted = deepcopy(material)
    promoted["p8_start_allowed"] = True
    with pytest.raises(ValueError):
        dmd.assert_p7_r54_ahr_post_dmh18_dmd_op08_bodyfree_result_memo_target_tests_regression_closure_contract(promoted)


def test_dmd_op08_public_aliases_match_canonical_helpers() -> None:
    material = dmd.build_p7_r54_ahr_post_dmh18_downstream_manual_decision_bodyfree_result_memo_target_tests_regression_closure(
        target_test_result_status_refs=_target_statuses(),
        selected_regression_result_status_refs=_regression_statuses(),
        compileall_result_status_ref="passed",
    )

    assert dmd.assert_p7_r54_ahr_post_dmh18_downstream_manual_decision_bodyfree_result_memo_target_tests_regression_closure_contract(material) is True
    assert material["schema_version"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP08_SCHEMA_VERSION
