# -*- coding: utf-8 -*-
"""R54-AHR Post-PNT closed material next boundary confirmation PCM-OP00/OP01 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_20260707 as pnt
import emlis_ai_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_20260707 as pcm
from r54_ahr_post_pnt_pcm_compact_pnt_op08_fixture_20260708 import (
    compact_closed_pnt_op08_for_pcm_regression,
)


PCM_R2_SIX_LANE_EXPECTED_LANE_REFS = (
    pcm.P7_R54_AHR_POST_PNT_PCM_LANE_DHR_OP05_MANUAL_HANDOFF_BOUNDARY_DESIGN_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_LANE_RETRY_OR_START_ACTUAL_LOCAL_ONLY_REVIEW_ROUTE_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REINTAKE_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_LANE_REPAIR_RDB_CANDIDATE_OR_UPSTREAM_RESULT_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_LANE_MANUAL_HOLD_UNRESOLVED_POST_RDB08_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_LANE_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_CANDIDATE_REF,
)


PCM_R2_FORBIDDEN_EXECUTION_KEYS = (
    "pnt_op08_default_builder_called_here",
    "pnt_op08_default_material_synthesized_here",
    "pnt_r11_decision_table_used_as_single_lane_here",
    "selected_post_nci_next_boundary_executed_here",
    "selected_pcm_next_boundary_executed_here",
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
    "raw_evidence_request_created_here",
    "repair_executed_here",
    "p8_start_allowed",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "question_text_materialized",
    "api_changed",
    "db_changed",
    "rn_changed",
    "runtime_changed",
    "response_key_changed",
    "json_schema_file_created_here",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_confirmed",
    "rn_contract_green_confirmed",
    "rn_real_device_modal_verified_claimed_here",
)


def _closed_pnt_op08(index: int = 0) -> dict[str, object]:
    return compact_closed_pnt_op08_for_pcm_regression(index)


def _assert_pcm_r2_no_downstream_execution(material: dict[str, object]) -> None:
    for key in PCM_R2_FORBIDDEN_EXECUTION_KEYS:
        if key in material:
            assert material[key] is False, key
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True


def test_pcm_r0_r1_summary_is_present_before_r2_and_still_points_to_op00() -> None:
    summary = pcm.build_p7_r54_ahr_post_pnt_pcm_r1_helper_skeleton_constants_summary()

    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_r1_helper_skeleton_constants_summary_contract(summary) is True
    assert summary["operation_step_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_R1_STEP_REF
    assert summary["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP00_STEP_REF
    assert summary["pcm_op00_implemented"] is False
    assert summary["pcm_op01_implemented"] is False
    assert summary["explicit_pnt_op08_closed_material_required"] is True
    assert summary["pnt_op08_default_builder_call_allowed"] is False
    assert summary["pnt_op08_default_material_synthesis_allowed"] is False
    assert summary["pnt_op08_decision_table_as_single_lane_allowed"] is False
    assert tuple(summary["allowed_lane_refs"]) == pcm.P7_R54_AHR_POST_PNT_PCM_ALLOWED_LANE_REFS
    _assert_pcm_r2_no_downstream_execution(summary)


def test_pcm_op00_refreezes_scope_explicit_closed_material_and_no_execution_without_pnt_builder(monkeypatch: pytest.MonkeyPatch) -> None:
    def _unexpected_pnt_op08_builder_call(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise AssertionError("PCM-OP00 must not call the PNT-OP08 builder")

    monkeypatch.setattr(
        pcm.pnt,
        "build_p7_r54_ahr_post_nci_pnt_op08_bodyfree_post_nci_triage_result_memo_closure",
        _unexpected_pnt_op08_builder_call,
    )

    op00 = pcm.build_p7_r54_ahr_post_pnt_pcm_op00_scope_explicit_closed_material_no_execution_refreeze_after_pnt_op08()

    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op00_scope_explicit_closed_material_no_execution_refreeze_after_pnt_op08_contract(op00) is True
    assert op00["operation_step_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP00_STEP_REF
    assert op00["pcm_scope_refrozen"] is True
    assert op00["pcm_op00_implemented"] is True
    assert op00["pcm_op01_implemented"] is False
    assert op00["explicit_pnt_op08_closed_material_required"] is True
    assert op00["pnt_op08_default_builder_call_allowed"] is False
    assert op00["pnt_op08_default_material_synthesis_allowed"] is False
    assert op00["pnt_op08_decision_table_as_single_lane_allowed"] is False
    assert op00["selected_post_nci_next_boundary_execution_allowed_here"] is False
    assert op00["selected_pcm_next_boundary_execution_allowed_here"] is False
    assert op00["dhr_op05_call_allowed_here"] is False
    assert op00["p8_question_design_allowed_here"] is False
    assert op00["api_db_rn_response_key_change_allowed_here"] is False
    assert op00["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP01_STEP_REF
    _assert_pcm_r2_no_downstream_execution(op00)


@pytest.mark.parametrize(
    ("case_index", "expected_lane"),
    [(index, expected_lane) for index, expected_lane in enumerate(PCM_R2_SIX_LANE_EXPECTED_LANE_REFS)],
)
def test_pcm_op01_intakes_explicit_closed_pnt_op08_ready_for_op02_without_classifying_next_work(
    case_index: int,
    expected_lane: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _unexpected_pnt_op08_builder_call(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise AssertionError("PCM-OP01 must not call the PNT-OP08 builder")

    monkeypatch.setattr(
        pcm.pnt,
        "build_p7_r54_ahr_post_nci_pnt_op08_bodyfree_post_nci_triage_result_memo_closure",
        _unexpected_pnt_op08_builder_call,
    )

    op01 = pcm.build_p7_r54_ahr_post_pnt_pcm_op01_explicit_closed_pnt_op08_material_intake(
        pnt_op08_bodyfree_result_memo_closure_material=_closed_pnt_op08(case_index),
    )

    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op01_explicit_closed_pnt_op08_material_intake_contract(op01) is True
    assert op01["pcm_op01_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_READY_FOR_OP02_REF
    assert op01["pcm_op00_implemented"] is True
    assert op01["pcm_op01_implemented"] is True
    assert op01["pcm_op01_ready_for_contract_validation"] is True
    assert op01["pnt_op08_material_present"] is True
    assert op01["pnt_op08_contract_valid"] is True
    assert op01["pnt_op08_closed_bodyfree_stopped"] is True
    assert op01["selected_pnt_lane_ref"] == expected_lane
    assert op01["selected_pnt_lane_ref_present"] is True
    assert op01["selected_post_nci_next_boundary_not_executed"] is True
    assert op01["selected_handoff_or_stop_not_executed"] is True
    assert op01["pcm_op01_does_not_validate_closed_material_contract"] is True
    assert op01["pcm_op01_does_not_confirm_single_selected_lane"] is True
    assert op01["pcm_op01_does_not_resolve_next_work_class"] is True
    assert op01["pcm_op01_does_not_materialize_next_design_candidate"] is True
    assert op01["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP02_STEP_REF
    assert op01["pcm_op01_blocker_refs"] == []
    _assert_pcm_r2_no_downstream_execution(op01)


def test_pcm_op01_waits_when_explicit_pnt_op08_material_is_missing_without_pnt_builder(monkeypatch: pytest.MonkeyPatch) -> None:
    def _unexpected_pnt_op08_builder_call(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise AssertionError("PCM-OP01 must not synthesize missing PNT-OP08 material")

    monkeypatch.setattr(
        pcm.pnt,
        "build_p7_r54_ahr_post_nci_pnt_op08_bodyfree_post_nci_triage_result_memo_closure",
        _unexpected_pnt_op08_builder_call,
    )

    op01 = pcm.build_p7_r54_ahr_post_pnt_pcm_op01_explicit_closed_pnt_op08_material_intake()

    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op01_explicit_closed_pnt_op08_material_intake_contract(op01) is True
    assert op01["pcm_op01_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_WAITING_FOR_EXPLICIT_PNT_OP08_CLOSED_MATERIAL_REF
    assert op01["pcm_op01_waiting_for_explicit_pnt_op08_closed_material"] is True
    assert op01["pnt_op08_material_present"] is False
    assert op01["pnt_op08_default_builder_called_here"] is False
    assert op01["pnt_op08_default_material_synthesized_here"] is False
    assert op01["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_WAIT_FOR_EXPLICIT_PNT_OP08_CLOSED_MATERIAL_REF
    _assert_pcm_r2_no_downstream_execution(op01)


def test_pcm_op01_waits_when_pnt_op08_material_has_not_closed_yet() -> None:
    waiting_material = {
        "schema_version": pnt.P7_R54_AHR_POST_NCI_PNT_OP08_SCHEMA_VERSION,
        "operation_step_ref": pnt.P7_R54_AHR_POST_NCI_PNT_OP08_STEP_REF,
        "pnt_op08_status_ref": pnt.P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_WAITING_FOR_INPUT_REFS_REF,
        "bodyfree_post_nci_triage_result_memo_closure_status_ref": pnt.P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_WAITING_FOR_INPUT_REFS_REF,
        "pnt_op08_waiting_for_input_refs": True,
        "body_free": True,
    }

    op01 = pcm.build_p7_r54_ahr_post_pnt_pcm_op01_explicit_closed_pnt_op08_material_intake(
        pnt_op08_bodyfree_result_memo_closure_material=waiting_material,
    )

    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op01_explicit_closed_pnt_op08_material_intake_contract(op01) is True
    assert op01["pcm_op01_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_WAITING_FOR_PNT_OP08_TO_CLOSE_REF
    assert op01["pcm_op01_waiting_for_pnt_op08_to_close"] is True
    assert op01["pnt_op08_contract_valid"] is False
    assert op01["pnt_op08_closed_bodyfree_stopped"] is False
    assert op01["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_WAIT_FOR_PNT_OP08_CLOSURE_REF
    _assert_pcm_r2_no_downstream_execution(op01)


def test_pcm_op01_repairs_when_closed_pnt_op08_contract_is_incomplete() -> None:
    incomplete_closed_material = {
        "schema_version": pnt.P7_R54_AHR_POST_NCI_PNT_OP08_SCHEMA_VERSION,
        "operation_step_ref": pnt.P7_R54_AHR_POST_NCI_PNT_OP08_STEP_REF,
        "pnt_op08_status_ref": pnt.P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_CLOSED_STOPPED_REF,
        "bodyfree_post_nci_triage_result_memo_closure_status_ref": pnt.P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_CLOSED_STOPPED_REF,
        "pnt_op08_bodyfree_post_nci_triage_closed_stopped": True,
        "selected_pnt_lane_ref": pcm.P7_R54_AHR_POST_PNT_PCM_LANE_DHR_OP05_MANUAL_HANDOFF_BOUNDARY_DESIGN_CANDIDATE_REF,
        "body_free": True,
    }

    op01 = pcm.build_p7_r54_ahr_post_pnt_pcm_op01_explicit_closed_pnt_op08_material_intake(
        pnt_op08_bodyfree_result_memo_closure_material=incomplete_closed_material,
    )

    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op01_explicit_closed_pnt_op08_material_intake_contract(op01) is True
    assert op01["pcm_op01_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_REPAIR_REQUIRED_FOR_PNT_OP08_CLOSED_MATERIAL_REF
    assert op01["pcm_op01_repair_required"] is True
    assert "pnt_op08_result_memo_closure_contract_invalid" in op01["pcm_op01_blocker_refs"]
    assert op01["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_PNT_OP08_CLOSED_MATERIAL_REF
    _assert_pcm_r2_no_downstream_execution(op01)


@pytest.mark.parametrize(
    ("mutation_key", "mutation_value", "expected_blocker"),
    [
        ("question_text", "blocked_question", "pnt_op08_input_forbidden_payload_key_detected"),
        ("stdout", "terminal body leak", "pnt_op08_input_forbidden_payload_key_detected"),
        ("dhr_op05_called_here", True, "pnt_op08_input_promotion_or_autorun_claim_detected"),
        ("response_key_changed", True, "pnt_op08_input_api_db_rn_runtime_response_key_or_p8_question_touch_detected"),
        ("dhr_op05_not_called", False, "pnt_op08_dhr_op05_not_called_not_true"),
    ],
)
def test_pcm_op01_blocks_body_payload_promotion_and_no_touch_claims_before_contract_validation(
    mutation_key: str,
    mutation_value: object,
    expected_blocker: str,
) -> None:
    mutated = deepcopy(_closed_pnt_op08())
    mutated[mutation_key] = mutation_value

    op01 = pcm.build_p7_r54_ahr_post_pnt_pcm_op01_explicit_closed_pnt_op08_material_intake(
        pnt_op08_bodyfree_result_memo_closure_material=mutated,
    )

    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op01_explicit_closed_pnt_op08_material_intake_contract(op01) is True
    assert op01["pcm_op01_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_BLOCKED_PNT_OP08_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF
    assert op01["pcm_op01_bodyfree_leak_promotion_or_autorun_blocked"] is True
    assert expected_blocker in op01["pcm_op01_blocker_refs"]
    assert op01["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_PNT_OP08_CLOSED_MATERIAL_REF
    _assert_pcm_r2_no_downstream_execution(op01)
