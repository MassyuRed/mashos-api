# -*- coding: utf-8 -*-
"""R54-AHR Post-NCI selected handoff-or-stop decision triage PNT-OP08 tests."""

from __future__ import annotations

from copy import deepcopy

import pytest

import emlis_ai_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_20260707 as pnt


PNT_R6_FORBIDDEN_EXECUTION_KEYS = (
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
    "bodyfree_post_nci_triage_result_memo_closure_execution_allowed_here",
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


def _op06_from_nci_op08(nci_op08: dict[str, object]) -> dict[str, object]:
    from test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op06_op07_20260707 import (  # noqa: WPS433
        _op06_from_nci_op08 as r5_op06_from_nci_op08,
    )

    return r5_op06_from_nci_op08(nci_op08)


def _op07_from_nci_op08(nci_op08: dict[str, object]) -> dict[str, object]:
    return pnt.build_p7_r54_ahr_post_nci_pnt_op07_post_nci_triage_result_memo_draft_material(
        _op06_from_nci_op08(nci_op08),
    )


def _op08_from_nci_op08(nci_op08: dict[str, object]) -> dict[str, object]:
    return pnt.build_p7_r54_ahr_post_nci_pnt_op08_bodyfree_post_nci_triage_result_memo_closure(
        _op07_from_nci_op08(nci_op08),
        nci_op08_bodyfree_selected_candidate_intake_result_memo_closure=nci_op08,
    )


def _assert_r6_no_downstream_execution(material: dict[str, object]) -> None:
    for key in PNT_R6_FORBIDDEN_EXECUTION_KEYS:
        if key in material:
            assert material[key] is False, key
    assert material["selected_handoff_or_stop_execution_allowed_here"] is False
    assert material["selected_post_nci_next_boundary_execution_allowed_here"] is False
    assert material["dhr_op05_call_allowed_here"] is False
    assert material["dhr_op05_builder_call_allowed_here"] is False
    assert material["p8_question_design_allowed_here"] is False
    assert material["api_db_rn_response_key_change_allowed_here"] is False
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True
    assert material["full_backend_suite_green_confirmed"] is False
    assert material["rn_contract_green_confirmed"] is False
    assert material["rn_real_device_modal_verified_claimed_here"] is False


def test_pnt_op08_closes_all_valid_outcomes_bodyfree_without_executing_selected_boundary() -> None:
    for nci_op08, expected_lane, expected_ref, expected_kind, expected_status, _expected_flag in _six_lane_cases():
        op08 = _op08_from_nci_op08(nci_op08)

        assert pnt.assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op08_bodyfree_post_nci_triage_result_memo_closure_contract(op08) is True
        assert set(op08) == set(pnt.P7_R54_AHR_POST_NCI_PNT_OP08_REQUIRED_FIELD_REFS)
        assert op08["pnt_op08_status_ref"] == pnt.P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_CLOSED_STOPPED_REF
        assert op08["pnt_op08_bodyfree_post_nci_triage_closed_stopped"] is True
        assert op08["bodyfree_post_nci_triage_result_memo_closure_bodyfree"] is True
        assert op08["bodyfree_post_nci_triage_result_memo_closure_materialized_here"] is True
        assert op08["selected_pnt_status_ref"] == expected_status
        assert op08["selected_pnt_lane_ref"] == expected_lane
        assert op08["selected_post_nci_next_boundary_ref"] == expected_ref
        assert op08["selected_post_nci_next_boundary_kind_ref"] == pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_OR_STOP_KIND_REF_MAP[expected_lane]
        assert op08["selected_post_nci_next_boundary_not_executed"] is True
        assert op08["selected_handoff_or_stop_ref"] == nci_op08["selected_handoff_or_stop_ref"]
        assert op08["selected_handoff_or_stop_kind_ref"] == nci_op08["selected_handoff_or_stop_kind_ref"]
        assert op08["selected_handoff_or_stop_not_executed"] is True
        assert op08["next_required_step"] == expected_ref
        assert op08["pnt_op08_blocker_refs"] == []
        _assert_r6_no_downstream_execution(op08)


def test_pnt_op08_keeps_validation_refs_as_recorded_material_not_execution_claim() -> None:
    op08 = _op08_from_nci_op08(_six_lane_cases()[0][0])

    assert pnt.assert_p7_r54_ahr_post_nci_pnt_op08_bodyfree_post_nci_triage_result_memo_closure_contract(op08) is True
    assert op08["validation_plan_recorded"] is True
    assert op08["validation_command_summary_refs"] == list(pnt.P7_R54_AHR_POST_NCI_PNT_VALIDATION_COMMAND_SUMMARY_REFS)
    assert op08["target_test_ref_refs"] == list(pnt.P7_R54_AHR_POST_NCI_PNT_TARGET_TEST_REF_REFS)
    assert op08["selected_regression_test_ref_refs"] == list(pnt.P7_R54_AHR_POST_NCI_PNT_SELECTED_REGRESSION_TEST_REF_REFS)
    assert op08["compileall_target_ref_refs"] == list(pnt.P7_R54_AHR_POST_NCI_PNT_COMPILEALL_TARGET_REF_REFS)
    assert op08["target_test_result_status_ref"] == "pnt_op06_target_test_plan_recorded_not_executed_here"
    assert op08["selected_regression_result_status_ref"] == "pnt_op06_selected_regression_plan_recorded_not_executed_here"
    assert op08["compileall_result_status_ref"] == "pnt_op06_compileall_plan_recorded_not_executed_here"
    _assert_r6_no_downstream_execution(op08)


@pytest.mark.parametrize(
    ("op07_material", "nci_material", "expected_blocker"),
    [
        (None, "valid_nci", "pnt_op07_result_memo_draft_missing_for_op08_closure"),
        ("valid_op07", None, "nci_op08_bodyfree_result_memo_closure_missing_for_pnt_op08_closure"),
    ],
)
def test_pnt_op08_waits_when_required_nci_or_pnt_inputs_are_missing(
    op07_material: str | None,
    nci_material: str | None,
    expected_blocker: str,
) -> None:
    nci_op08 = _six_lane_cases()[0][0]
    op07 = _op07_from_nci_op08(nci_op08) if op07_material == "valid_op07" else None
    nci_input = nci_op08 if nci_material == "valid_nci" else None

    op08 = pnt.build_p7_r54_ahr_post_nci_pnt_op08_bodyfree_post_nci_triage_result_memo_closure(
        op07,
        nci_op08_bodyfree_selected_candidate_intake_result_memo_closure=nci_input,
    )

    assert pnt.assert_p7_r54_ahr_post_nci_pnt_op08_bodyfree_post_nci_triage_result_memo_closure_contract(op08) is True
    assert op08["pnt_op08_status_ref"] == pnt.P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_WAITING_FOR_INPUT_REFS_REF
    assert expected_blocker in op08["pnt_op08_blocker_refs"]
    assert op08["bodyfree_post_nci_triage_result_memo_closure_materialized_here"] is False
    assert op08["selected_post_nci_next_boundary_not_executed"] is False
    assert op08["next_required_step"] == pnt.P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_WAIT_FOR_OP08_INPUT_REFS_REF
    _assert_r6_no_downstream_execution(op08)


def test_pnt_op08_repairs_when_op07_draft_is_not_ready_for_closure() -> None:
    nci_op08 = _six_lane_cases()[0][0]
    repair_op07 = pnt.build_p7_r54_ahr_post_nci_pnt_op07_post_nci_triage_result_memo_draft_material(None)

    op08 = pnt.build_p7_r54_ahr_post_nci_pnt_op08_bodyfree_post_nci_triage_result_memo_closure(
        repair_op07,
        nci_op08_bodyfree_selected_candidate_intake_result_memo_closure=nci_op08,
    )

    assert pnt.assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op08_bodyfree_post_nci_triage_result_memo_closure_contract(op08) is True
    assert op08["pnt_op08_status_ref"] == pnt.P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_REPAIR_REQUIRED_REF
    assert "pnt_op07_result_memo_draft_not_ready_for_op08_closure" in op08["pnt_op08_blocker_refs"]
    assert "pnt_op07_result_memo_draft_repair_required_before_op08_closure" in op08["pnt_op08_blocker_refs"]
    assert op08["next_required_step"] == pnt.P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_OP08_CLOSURE_INPUTS_REF
    _assert_r6_no_downstream_execution(op08)


@pytest.mark.parametrize(
    ("target", "mutation_key", "mutation_value", "expected_blocker"),
    [
        ("op07", "question_text", "blocked_question", "op08_result_memo_closure_op07_forbidden_payload_key_detected"),
        ("op07", "stdout", "terminal body leak", "op08_result_memo_closure_op07_body_like_value_detected"),
        ("op07", "dhr_op05_called_here", True, "op08_result_memo_closure_op07_promotion_or_autorun_claim_detected"),
        ("op07", "response_key_changed", True, "op08_result_memo_closure_op07_api_db_rn_runtime_response_key_or_p8_question_touch_detected"),
        ("nci", "raw_evidence", "blocked_raw", "op08_result_memo_closure_nci_op08_forbidden_payload_key_detected"),
        ("nci", "release_allowed", True, "op08_result_memo_closure_nci_op08_promotion_or_autorun_claim_detected"),
        ("nci", "api_changed", True, "op08_result_memo_closure_nci_op08_api_db_rn_runtime_response_key_or_p8_question_touch_detected"),
    ],
)
def test_pnt_op08_blocks_body_payload_promotion_and_no_touch_mutation_before_closure(
    target: str,
    mutation_key: str,
    mutation_value: object,
    expected_blocker: str,
) -> None:
    nci_op08 = _six_lane_cases()[0][0]
    op07 = _op07_from_nci_op08(nci_op08)
    mutated_op07 = deepcopy(op07)
    mutated_nci = deepcopy(nci_op08)
    if target == "op07":
        mutated_op07[mutation_key] = mutation_value
    else:
        mutated_nci[mutation_key] = mutation_value

    op08 = pnt.build_p7_r54_ahr_post_nci_pnt_op08_bodyfree_post_nci_triage_result_memo_closure(
        mutated_op07,
        nci_op08_bodyfree_selected_candidate_intake_result_memo_closure=mutated_nci,
    )

    assert pnt.assert_p7_r54_ahr_post_nci_pnt_op08_bodyfree_post_nci_triage_result_memo_closure_contract(op08) is True
    assert op08["pnt_op08_status_ref"] == pnt.P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_BLOCKED_REF
    assert expected_blocker in op08["pnt_op08_blocker_refs"]
    assert op08["bodyfree_post_nci_triage_result_memo_closure_materialized_here"] is False
    assert op08["next_required_step"] == pnt.P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_OP08_CLOSURE_REF
    _assert_r6_no_downstream_execution(op08)


def test_pnt_op08_contract_rejects_downstream_execution_or_green_claim_mutation() -> None:
    op08 = _op08_from_nci_op08(_six_lane_cases()[0][0])

    for mutation_key in (
        "selected_post_nci_next_boundary_execution_allowed_here",
        "dhr_op05_call_allowed_here",
        "p8_question_design_allowed_here",
        "release_allowed",
        "full_backend_suite_green_confirmed",
        "rn_contract_green_confirmed",
        "rn_real_device_modal_verified_claimed_here",
    ):
        mutated = deepcopy(op08)
        mutated[mutation_key] = True
        with pytest.raises(ValueError):
            pnt.assert_p7_r54_ahr_post_nci_pnt_op08_bodyfree_post_nci_triage_result_memo_closure_contract(mutated)


def test_pnt_op08_full_title_aliases_match_short_builders_and_asserts() -> None:
    assert (
        pnt.build_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op08_bodyfree_post_nci_triage_result_memo_closure
        is pnt.build_p7_r54_ahr_post_nci_pnt_op08_bodyfree_post_nci_triage_result_memo_closure
    )
    assert (
        pnt.assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op08_bodyfree_post_nci_triage_result_memo_closure_contract
        is pnt.assert_p7_r54_ahr_post_nci_pnt_op08_bodyfree_post_nci_triage_result_memo_closure_contract
    )
