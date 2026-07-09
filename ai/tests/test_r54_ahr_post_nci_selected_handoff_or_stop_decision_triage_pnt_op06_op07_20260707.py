# -*- coding: utf-8 -*-
"""R54-AHR Post-NCI selected handoff-or-stop decision triage PNT-OP06/OP07 tests."""

from __future__ import annotations

from copy import deepcopy

import pytest

import emlis_ai_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_20260707 as pnt


PNT_R5_FORBIDDEN_EXECUTION_KEYS = (
    "selected_handoff_or_stop_executed_here",
    "handoff_or_stop_envelope_executed_here",
    "selected_post_nci_next_boundary_executed_here",
    "nci_op08_default_builder_called_here",
    "nci_op08_default_material_synthesized_here",
    "dhr_op05_called_here",
    "dhr_op05_builder_called_here",
    "dhr_op06_called_here",
    "dhr_op07_materialized_here",
    "dmd_execution_started_here",
    "r52_actual_execution_started_here",
    "actual_body_full_packet_generated_here",
    "actual_review_started_here",
    "actual_rows_created_here",
    "actual_question_need_observation_rows_created_here",
    "actual_disposal_or_purge_executed_here",
    "p8_start_allowed",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "question_text_materialized",
    "api_changed",
    "db_changed",
    "rn_changed",
    "runtime_changed",
    "response_key_changed",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_confirmed",
    "rn_contract_green_confirmed",
    "rn_real_device_modal_verified_claimed_here",
    "validation_commands_executed_here",
    "pytest_executed_here",
    "pnt_target_tests_executed_here",
    "selected_regression_executed_here",
    "compileall_executed_here",
    "post_nci_triage_result_memo_draft_execution_allowed_here",
)

_SIX_LANE_CASES_CACHE: tuple[tuple[dict[str, object], str, str, str, str, str], ...] | None = None


def _six_lane_cases() -> tuple[tuple[dict[str, object], str, str, str, str, str], ...]:
    global _SIX_LANE_CASES_CACHE
    if _SIX_LANE_CASES_CACHE is None:
        from test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op02_op03_20260707 import (  # noqa: WPS433
            _six_lane_cases as r3_six_lane_cases,
        )

        _SIX_LANE_CASES_CACHE = r3_six_lane_cases()
    return _SIX_LANE_CASES_CACHE


def _op04_from_nci_op08(nci_op08: dict[str, object]) -> dict[str, object]:
    from test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op04_op05_20260707 import (  # noqa: WPS433
        _op04_from_nci_op08 as r4_op04_from_nci_op08,
    )

    return r4_op04_from_nci_op08(nci_op08)


def _op05_from_nci_op08(nci_op08: dict[str, object]) -> dict[str, object]:
    op04 = _op04_from_nci_op08(nci_op08)
    return pnt.build_p7_r54_ahr_post_nci_pnt_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard(op04)


def _op06_from_nci_op08(nci_op08: dict[str, object]) -> dict[str, object]:
    return pnt.build_p7_r54_ahr_post_nci_pnt_op06_selected_regression_compileall_validation_plan(
        _op05_from_nci_op08(nci_op08),
    )


def _assert_r5_no_downstream_execution(material: dict[str, object]) -> None:
    for key in PNT_R5_FORBIDDEN_EXECUTION_KEYS:
        if key in material:
            assert material[key] is False, key
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True
    assert material["full_backend_suite_green_confirmed"] is False
    assert material["rn_contract_green_confirmed"] is False
    assert material["rn_real_device_modal_verified_claimed_here"] is False


def test_pnt_op06_records_validation_plan_refs_for_all_valid_outcomes_without_running_commands() -> None:
    for nci_op08, expected_lane, expected_ref, _expected_kind, _expected_status, _expected_flag in _six_lane_cases():
        op06 = _op06_from_nci_op08(nci_op08)

        assert pnt.assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op06_selected_regression_compileall_validation_plan_contract(op06) is True
        assert op06["pnt_op06_status_ref"] == pnt.P7_R54_AHR_POST_NCI_PNT_OP06_STATUS_VALIDATION_PLAN_RECORDED_REF
        assert op06["pnt_op06_validation_plan_recorded"] is True
        assert op06["validation_plan_recorded"] is True
        assert op06["selected_pnt_lane_ref"] == expected_lane
        assert op06["selected_post_nci_next_boundary_ref"] == expected_ref
        assert op06["selected_post_nci_next_boundary_not_executed"] is True
        assert op06["selected_post_nci_next_boundary_execution_allowed_here"] is False
        assert op06["target_test_ref_refs"] == list(pnt.P7_R54_AHR_POST_NCI_PNT_TARGET_TEST_REF_REFS)
        assert op06["selected_regression_test_ref_refs"] == list(pnt.P7_R54_AHR_POST_NCI_PNT_SELECTED_REGRESSION_TEST_REF_REFS)
        assert op06["compileall_target_ref_refs"] == list(pnt.P7_R54_AHR_POST_NCI_PNT_COMPILEALL_TARGET_REF_REFS)
        assert op06["validation_command_summary_refs"] == list(pnt.P7_R54_AHR_POST_NCI_PNT_VALIDATION_COMMAND_SUMMARY_REFS)
        assert op06["next_required_step"] == pnt.P7_R54_AHR_POST_NCI_PNT_OP07_STEP_REF
        assert op06["pnt_op06_blocker_refs"] == []
        _assert_r5_no_downstream_execution(op06)


def test_pnt_op07_materializes_bodyfree_result_memo_draft_for_all_outcomes_without_closing_op08() -> None:
    for nci_op08, expected_lane, expected_ref, _expected_kind, _expected_status, _expected_flag in _six_lane_cases():
        op06 = _op06_from_nci_op08(nci_op08)
        op07 = pnt.build_p7_r54_ahr_post_nci_pnt_op07_post_nci_triage_result_memo_draft_material(op06)

        assert pnt.assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op07_post_nci_triage_result_memo_draft_material_contract(op07) is True
        assert op07["selected_pnt_lane_ref"] == expected_lane
        assert op07["selected_post_nci_next_boundary_ref"] == expected_ref
        assert op07["selected_post_nci_next_boundary_not_executed"] is True
        assert op07["post_nci_triage_result_memo_draft_bodyfree"] is True
        assert op07["post_nci_triage_result_memo_draft_materialized_here"] is True
        assert op07["post_nci_triage_result_memo_draft_execution_allowed_here"] is False
        assert op07["pnt_op07_ready_for_op08"] is True
        expected_status = (
            pnt.P7_R54_AHR_POST_NCI_PNT_OP07_STATUS_STOP_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED_REF
            if pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_OUTCOME_GROUP_REF_MAP[expected_lane] == pnt.P7_R54_AHR_POST_NCI_PNT_OUTCOME_GROUP_STOP_REF
            else pnt.P7_R54_AHR_POST_NCI_PNT_OP07_STATUS_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED_REF
        )
        assert op07["pnt_op07_status_ref"] == expected_status
        assert op07["next_required_step"] == pnt.P7_R54_AHR_POST_NCI_PNT_OP08_STEP_REF
        assert op07["pnt_op07_blocker_refs"] == []
        _assert_r5_no_downstream_execution(op07)


def test_pnt_op06_waits_when_op05_guard_material_is_missing_before_validation_plan() -> None:
    op06 = pnt.build_p7_r54_ahr_post_nci_pnt_op06_selected_regression_compileall_validation_plan(None)

    assert pnt.assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op06_selected_regression_compileall_validation_plan_contract(op06) is True
    assert op06["pnt_op06_status_ref"] == pnt.P7_R54_AHR_POST_NCI_PNT_OP06_STATUS_WAITING_FOR_OP05_GUARD_REF
    assert "pnt_op05_guard_material_missing" in op06["pnt_op06_blocker_refs"]
    assert op06["validation_plan_recorded"] is False
    assert op06["next_required_step"] == pnt.P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_WAIT_FOR_OP05_GUARD_REF
    _assert_r5_no_downstream_execution(op06)


def test_pnt_op06_repairs_when_op05_guard_contract_is_not_valid() -> None:
    op05 = _op05_from_nci_op08(_six_lane_cases()[0][0])
    mutated = deepcopy(op05)
    mutated["pnt_op05_guard_passed"] = False

    op06 = pnt.build_p7_r54_ahr_post_nci_pnt_op06_selected_regression_compileall_validation_plan(mutated)

    assert pnt.assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op06_selected_regression_compileall_validation_plan_contract(op06) is True
    assert op06["pnt_op06_status_ref"] == pnt.P7_R54_AHR_POST_NCI_PNT_OP06_STATUS_REPAIR_REQUIRED_REF
    assert "pnt_op05_guard_contract_invalid" in op06["pnt_op06_blocker_refs"]
    assert op06["validation_plan_recorded"] is False
    assert op06["next_required_step"] == pnt.P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_OP06_VALIDATION_PLAN_INPUTS_REF
    _assert_r5_no_downstream_execution(op06)


@pytest.mark.parametrize(
    ("mutation_key", "mutation_value", "expected_blocker"),
    [
        ("question_text", "blocked_question", "op06_validation_plan_forbidden_payload_key_detected"),
        ("raw_evidence", "blocked_raw_evidence", "op06_validation_plan_forbidden_payload_key_detected"),
        ("local_path", "/tmp/not_allowed", "op06_validation_plan_forbidden_payload_key_detected"),
        ("hash", "blocked_hash", "op06_validation_plan_forbidden_payload_key_detected"),
        ("stdout", "terminal body leak", "op06_validation_plan_body_like_value_detected"),
        ("dhr_op05_called_here", True, "op06_validation_plan_promotion_or_autorun_claim_detected"),
        ("p8_question_design_started", True, "op06_validation_plan_promotion_or_autorun_claim_detected"),
        ("release_allowed", True, "op06_validation_plan_promotion_or_autorun_claim_detected"),
        ("api_changed", True, "op06_validation_plan_api_db_rn_runtime_response_key_or_p8_question_touch_detected"),
        ("response_key_changed", True, "op06_validation_plan_api_db_rn_runtime_response_key_or_p8_question_touch_detected"),
    ],
)
def test_pnt_op06_blocks_body_payload_promotion_and_no_touch_mutation_before_validation_plan(
    mutation_key: str,
    mutation_value: object,
    expected_blocker: str,
) -> None:
    op05 = _op05_from_nci_op08(_six_lane_cases()[0][0])
    mutated = deepcopy(op05)
    mutated[mutation_key] = mutation_value

    op06 = pnt.build_p7_r54_ahr_post_nci_pnt_op06_selected_regression_compileall_validation_plan(mutated)

    assert pnt.assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op06_selected_regression_compileall_validation_plan_contract(op06) is True
    assert op06["pnt_op06_status_ref"] == pnt.P7_R54_AHR_POST_NCI_PNT_OP06_STATUS_BLOCKED_REF
    assert expected_blocker in op06["pnt_op06_blocker_refs"]
    assert op06["validation_plan_recorded"] is False
    assert op06["next_required_step"] == pnt.P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_OP06_VALIDATION_PLAN_REF
    _assert_r5_no_downstream_execution(op06)


def test_pnt_op07_repairs_when_op06_plan_material_is_missing_or_not_recorded() -> None:
    missing = pnt.build_p7_r54_ahr_post_nci_pnt_op07_post_nci_triage_result_memo_draft_material(None)

    assert pnt.assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op07_post_nci_triage_result_memo_draft_material_contract(missing) is True
    assert missing["pnt_op07_status_ref"] == pnt.P7_R54_AHR_POST_NCI_PNT_OP07_STATUS_REPAIR_REQUIRED_REF
    assert "pnt_op06_validation_plan_material_missing" in missing["pnt_op07_blocker_refs"]
    assert missing["pnt_op07_ready_for_op08"] is False
    assert missing["next_required_step"] == pnt.P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_OP07_RESULT_MEMO_DRAFT_INPUTS_REF
    _assert_r5_no_downstream_execution(missing)


@pytest.mark.parametrize(
    ("mutation_key", "mutation_value", "expected_blocker"),
    [
        ("question_text", "blocked_question", "op07_result_memo_draft_forbidden_payload_key_detected"),
        ("raw_input", "blocked_raw", "op07_result_memo_draft_forbidden_payload_key_detected"),
        ("stdout", "terminal body leak", "op07_result_memo_draft_body_like_value_detected"),
        ("dhr_op05_called_here", True, "op07_result_memo_draft_promotion_or_autorun_claim_detected"),
        ("p8_question_design_started", True, "op07_result_memo_draft_promotion_or_autorun_claim_detected"),
        ("release_allowed", True, "op07_result_memo_draft_promotion_or_autorun_claim_detected"),
        ("api_changed", True, "op07_result_memo_draft_api_db_rn_runtime_response_key_or_p8_question_touch_detected"),
        ("rn_changed", True, "op07_result_memo_draft_api_db_rn_runtime_response_key_or_p8_question_touch_detected"),
    ],
)
def test_pnt_op07_blocks_body_payload_promotion_and_no_touch_mutation_before_result_memo_draft(
    mutation_key: str,
    mutation_value: object,
    expected_blocker: str,
) -> None:
    op06 = _op06_from_nci_op08(_six_lane_cases()[0][0])
    mutated = deepcopy(op06)
    mutated[mutation_key] = mutation_value

    op07 = pnt.build_p7_r54_ahr_post_nci_pnt_op07_post_nci_triage_result_memo_draft_material(mutated)

    assert pnt.assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op07_post_nci_triage_result_memo_draft_material_contract(op07) is True
    assert op07["pnt_op07_status_ref"] == pnt.P7_R54_AHR_POST_NCI_PNT_OP07_STATUS_BLOCKED_REF
    assert expected_blocker in op07["pnt_op07_blocker_refs"]
    assert op07["pnt_op07_ready_for_op08"] is False
    assert op07["next_required_step"] == pnt.P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_OP07_RESULT_MEMO_DRAFT_REF
    _assert_r5_no_downstream_execution(op07)


def test_pnt_op06_op07_full_title_aliases_match_short_builders_and_asserts() -> None:
    assert (
        pnt.build_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op06_selected_regression_compileall_validation_plan
        is pnt.build_p7_r54_ahr_post_nci_pnt_op06_selected_regression_compileall_validation_plan
    )
    assert (
        pnt.assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op06_selected_regression_compileall_validation_plan_contract
        is pnt.assert_p7_r54_ahr_post_nci_pnt_op06_selected_regression_compileall_validation_plan_contract
    )
    assert (
        pnt.build_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op07_post_nci_triage_result_memo_draft_material
        is pnt.build_p7_r54_ahr_post_nci_pnt_op07_post_nci_triage_result_memo_draft_material
    )
    assert (
        pnt.assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op07_post_nci_triage_result_memo_draft_material_contract
        is pnt.assert_p7_r54_ahr_post_nci_pnt_op07_post_nci_triage_result_memo_draft_material_contract
    )
