# -*- coding: utf-8 -*-
"""R54-AHR Post-PNT closed material next boundary confirmation PCM-OP02/OP03 tests."""

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


PCM_R3_FORBIDDEN_EXECUTION_KEYS = (
    "pnt_op08_default_builder_called_here",
    "pnt_op08_default_material_synthesized_here",
    "pnt_op08_builder_called_here",
    "pnt_op08_material_synthesized_here",
    "pnt_r11_decision_table_used_as_single_lane_here",
    "selected_post_nci_next_boundary_executed_here",
    "selected_pcm_next_boundary_executed_here",
    "selected_pcm_next_boundary_execution_allowed_here",
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


PCM_R3_SIX_LANE_EXPECTED_LANE_REFS = (
    pcm.P7_R54_AHR_POST_PNT_PCM_LANE_DHR_OP05_MANUAL_HANDOFF_BOUNDARY_DESIGN_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_LANE_RETRY_OR_START_ACTUAL_LOCAL_ONLY_REVIEW_ROUTE_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REINTAKE_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_LANE_REPAIR_RDB_CANDIDATE_OR_UPSTREAM_RESULT_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_LANE_MANUAL_HOLD_UNRESOLVED_POST_RDB08_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_LANE_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_CANDIDATE_REF,
)


def _closed_pnt_op08(index: int = 0) -> dict[str, object]:
    return compact_closed_pnt_op08_for_pcm_regression(index)


def _pcm_op01_from_closed(index: int = 0) -> dict[str, object]:
    return pcm.build_p7_r54_ahr_post_pnt_pcm_op01_explicit_closed_pnt_op08_material_intake(
        pnt_op08_bodyfree_result_memo_closure_material=_closed_pnt_op08(index),
    )


def _pcm_op02_from_closed(index: int = 0) -> dict[str, object]:
    op01 = _pcm_op01_from_closed(index)
    return pcm.build_p7_r54_ahr_post_pnt_pcm_op02_closed_material_contract_validation(op01)


def _assert_pcm_r3_no_downstream_execution(material: dict[str, object]) -> None:
    for key in PCM_R3_FORBIDDEN_EXECUTION_KEYS:
        if key in material:
            assert material[key] is False, key
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True


@pytest.mark.parametrize(
    ("case_index", "expected_lane"),
    [(index, expected_lane) for index, expected_lane in enumerate(PCM_R3_SIX_LANE_EXPECTED_LANE_REFS)],
)
def test_pcm_op02_validates_all_six_closed_pnt_op08_material_contracts_without_classifying_next_work(
    case_index: int,
    expected_lane: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    op01 = _pcm_op01_from_closed(case_index)

    def _unexpected_pnt_op08_builder_call(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise AssertionError("PCM-OP02 must not call the PNT-OP08 builder")

    monkeypatch.setattr(
        pcm.pnt,
        "build_p7_r54_ahr_post_nci_pnt_op08_bodyfree_post_nci_triage_result_memo_closure",
        _unexpected_pnt_op08_builder_call,
    )

    op02 = pcm.build_p7_r54_ahr_post_pnt_pcm_op02_closed_material_contract_validation(op01)

    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op02_closed_material_contract_validation_contract(op02) is True
    assert op02["pcm_op02_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP02_STATUS_CONTRACT_VALID_STOPPED_REF
    assert op02["closed_pnt_op08_material_contract_valid"] is True
    assert op02["selected_pnt_lane_ref"] == expected_lane
    assert op02["selected_pnt_lane_ref_allowed"] is True
    assert op02["selected_pnt_status_ref_matches_lane"] is True
    assert op02["selected_post_nci_outcome_group_ref_matches_lane"] is True
    assert op02["selected_post_nci_next_boundary_ref_matches_lane"] is True
    assert op02["selected_handoff_or_stop_ref_matches_lane"] is True
    assert op02["next_design_document_candidate_ref_matches_lane"] is True
    assert op02["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP03_STEP_REF
    assert op02["pcm_op02_does_not_confirm_single_selected_lane"] is True
    assert op02["pcm_op02_does_not_resolve_next_work_class"] is True
    assert op02["pcm_op02_blocker_refs"] == []
    _assert_pcm_r3_no_downstream_execution(op02)


@pytest.mark.parametrize(
    ("case_index", "expected_lane"),
    [(index, expected_lane) for index, expected_lane in enumerate(PCM_R3_SIX_LANE_EXPECTED_LANE_REFS)],
)
def test_pcm_op03_confirms_each_single_selected_lane_without_resolving_next_work_class(
    case_index: int,
    expected_lane: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    op02 = _pcm_op02_from_closed(case_index)

    def _unexpected_pnt_op08_builder_call(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise AssertionError("PCM-OP03 must not synthesize PNT-OP08 material")

    monkeypatch.setattr(
        pcm.pnt,
        "build_p7_r54_ahr_post_nci_pnt_op08_bodyfree_post_nci_triage_result_memo_closure",
        _unexpected_pnt_op08_builder_call,
    )

    op03 = pcm.build_p7_r54_ahr_post_pnt_pcm_op03_single_selected_lane_confirmation(op02)

    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op03_single_selected_lane_confirmation_contract(op03) is True
    assert op03["pcm_op03_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP03_STATUS_SINGLE_SELECTED_LANE_CONFIRMED_STOPPED_REF
    assert op03["single_selected_pnt_lane_confirmed"] is True
    assert op03["single_selected_pnt_lane_material_present"] is True
    assert op03["selected_pnt_lane_ref"] == expected_lane
    assert op03["selected_pnt_lane_ref_allowed"] is True
    assert op03["single_lane_flag_count"] == 1
    assert op03["selected_post_nci_next_boundary_not_executed"] is True
    assert op03["selected_pcm_next_work_class_not_resolved_here"] is True
    assert op03["selected_pcm_next_boundary_not_materialized_here"] is True
    assert op03["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP04_STEP_REF
    assert op03["pcm_op03_blocker_refs"] == []
    _assert_pcm_r3_no_downstream_execution(op03)


def test_pcm_op02_repairs_missing_selected_pnt_lane_without_lane_synthesis() -> None:
    op01 = _pcm_op01_from_closed()
    del op01["selected_pnt_lane_ref"]

    op02 = pcm.build_p7_r54_ahr_post_pnt_pcm_op02_closed_material_contract_validation(op01)

    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op02_closed_material_contract_validation_contract(op02) is True
    assert op02["pcm_op02_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP02_STATUS_REPAIR_REQUIRED_FOR_CONTRACT_REF
    assert op02["pcm_op02_repair_required"] is True
    assert "selected_pnt_lane_ref_missing" in op02["pcm_op02_blocker_refs"]
    assert op02["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_CLOSED_PNT_OP08_MATERIAL_CONTRACT_REF
    _assert_pcm_r3_no_downstream_execution(op02)


@pytest.mark.parametrize(
    ("mutation_key", "mutation_value", "expected_blocker"),
    [
        ("selected_pnt_lane_ref", "unknown_lane", "selected_pnt_lane_ref_unknown_or_not_allowed"),
        ("selected_post_nci_outcome_group_ref", "unknown_outcome_group", "selected_post_nci_outcome_group_ref_unknown_or_not_allowed"),
        ("selected_post_nci_next_boundary_ref", "unexpected_boundary", "selected_post_nci_next_boundary_ref_does_not_match_lane"),
        ("next_design_document_candidate_ref", "unexpected_design_doc", "next_design_document_candidate_ref_does_not_match_lane"),
    ],
)
def test_pcm_op02_repairs_unknown_or_mismatched_closed_material_contract_refs(
    mutation_key: str,
    mutation_value: object,
    expected_blocker: str,
) -> None:
    op01 = _pcm_op01_from_closed()
    op01[mutation_key] = mutation_value

    op02 = pcm.build_p7_r54_ahr_post_pnt_pcm_op02_closed_material_contract_validation(op01)

    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op02_closed_material_contract_validation_contract(op02) is True
    assert op02["pcm_op02_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP02_STATUS_REPAIR_REQUIRED_FOR_CONTRACT_REF
    assert expected_blocker in op02["pcm_op02_blocker_refs"]
    assert op02["closed_pnt_op08_material_contract_valid"] is False
    _assert_pcm_r3_no_downstream_execution(op02)


@pytest.mark.parametrize(
    ("mutation_key", "mutation_value", "expected_blocker"),
    [
        ("selected_post_nci_next_boundary_not_executed", False, "selected_post_nci_next_boundary_not_executed_false"),
        ("selected_handoff_or_stop_not_executed", False, "selected_handoff_or_stop_not_executed_false"),
        ("question_text", "blocked_question", "op02_input_forbidden_payload_key_detected"),
        ("dhr_op05_called_here", True, "op02_input_promotion_or_autorun_claim_detected"),
        ("response_key_changed", True, "op02_input_api_db_rn_runtime_response_key_or_p8_question_touch_detected"),
        ("p8_question_design_not_started", False, "p8_question_design_not_started_not_true"),
    ],
)
def test_pcm_op02_blocks_not_executed_false_body_payload_promotion_and_no_touch_claims(
    mutation_key: str,
    mutation_value: object,
    expected_blocker: str,
) -> None:
    op01 = _pcm_op01_from_closed()
    op01[mutation_key] = mutation_value

    op02 = pcm.build_p7_r54_ahr_post_pnt_pcm_op02_closed_material_contract_validation(op01)

    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op02_closed_material_contract_validation_contract(op02) is True
    assert op02["pcm_op02_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP02_STATUS_BLOCKED_LEAK_PROMOTION_OR_AUTORUN_REF
    assert op02["pcm_op02_bodyfree_leak_promotion_or_autorun_blocked"] is True
    assert expected_blocker in op02["pcm_op02_blocker_refs"]
    assert op02["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_CLOSED_PNT_OP08_MATERIAL_CONTRACT_REF
    _assert_pcm_r3_no_downstream_execution(op02)


def test_pcm_op03_waits_when_op02_material_is_missing_without_building_a_lane() -> None:
    op03 = pcm.build_p7_r54_ahr_post_pnt_pcm_op03_single_selected_lane_confirmation()

    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op03_single_selected_lane_confirmation_contract(op03) is True
    assert op03["pcm_op03_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP03_STATUS_WAITING_FOR_SINGLE_SELECTED_LANE_MATERIAL_REF
    assert op03["pcm_op03_waiting_for_single_selected_lane_material"] is True
    assert op03["single_selected_pnt_lane_confirmed"] is False
    assert op03["selected_pnt_lane_ref"] == "missing"
    assert op03["single_lane_flag_count"] == 0
    assert op03["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_WAIT_FOR_SINGLE_SELECTED_PNT_LANE_MATERIAL_REF
    _assert_pcm_r3_no_downstream_execution(op03)


@pytest.mark.parametrize(
    ("mutation_key", "mutation_value", "expected_blocker"),
    [
        ("decision_table", {"all_lanes": True}, "decision_table_or_multi_lane_material_present"),
        ("six_outcome_summary", ["dhr", "retry", "wait", "repair", "hold", "blocked"], "decision_table_or_multi_lane_material_present"),
    ],
)
def test_pcm_op03_repairs_decision_table_or_six_outcome_summary_as_ambiguous_not_single_lane(
    mutation_key: str,
    mutation_value: object,
    expected_blocker: str,
) -> None:
    op02 = _pcm_op02_from_closed()
    op02[mutation_key] = mutation_value

    op03 = pcm.build_p7_r54_ahr_post_pnt_pcm_op03_single_selected_lane_confirmation(op02)

    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op03_single_selected_lane_confirmation_contract(op03) is True
    assert op03["pcm_op03_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP03_STATUS_REPAIR_REQUIRED_FOR_MULTI_OR_AMBIGUOUS_LANE_REF
    assert op03["pcm_op03_repair_required_for_multi_or_ambiguous_lane"] is True
    assert op03["multi_lane_material_rejected"] is True
    assert expected_blocker in op03["pcm_op03_blocker_refs"]
    assert op03["single_selected_pnt_lane_confirmed"] is False
    assert op03["single_lane_flag_count"] == 0
    assert op03["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_MULTI_OR_AMBIGUOUS_PNT_LANE_MATERIAL_REF
    _assert_pcm_r3_no_downstream_execution(op03)


def test_pcm_op03_repairs_multiple_lane_flags_true_as_ambiguous_material() -> None:
    op02 = _pcm_op02_from_closed()
    op02[pcm.P7_R54_AHR_POST_PNT_PCM_OP03_LANE_FLAG_REFS[0]] = True
    op02[pcm.P7_R54_AHR_POST_PNT_PCM_OP03_LANE_FLAG_REFS[1]] = True

    op03 = pcm.build_p7_r54_ahr_post_pnt_pcm_op03_single_selected_lane_confirmation(op02)

    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op03_single_selected_lane_confirmation_contract(op03) is True
    assert op03["pcm_op03_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP03_STATUS_REPAIR_REQUIRED_FOR_MULTI_OR_AMBIGUOUS_LANE_REF
    assert "multiple_selected_lane_flags_true" in op03["pcm_op03_blocker_refs"]
    assert len(op03["ambiguous_lane_flag_refs"]) == 2
    assert op03["multi_lane_material_rejected"] is True
    assert op03["single_lane_flag_count"] == 0
    _assert_pcm_r3_no_downstream_execution(op03)


@pytest.mark.parametrize(
    ("mutation_key", "mutation_value", "expected_blocker"),
    [
        ("comment_text", "body leak", "op03_input_forbidden_payload_key_detected"),
        ("dhr_op05_called_here", True, "op03_input_promotion_or_autorun_claim_detected"),
        ("api_changed", True, "op03_input_api_db_rn_runtime_response_key_or_p8_question_touch_detected"),
    ],
)
def test_pcm_op03_blocks_body_payload_promotion_and_no_touch_claims(
    mutation_key: str,
    mutation_value: object,
    expected_blocker: str,
) -> None:
    op02 = _pcm_op02_from_closed()
    op02[mutation_key] = mutation_value

    op03 = pcm.build_p7_r54_ahr_post_pnt_pcm_op03_single_selected_lane_confirmation(op02)

    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op03_single_selected_lane_confirmation_contract(op03) is True
    assert op03["pcm_op03_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP03_STATUS_BLOCKED_PROMOTION_OR_AUTORUN_REF
    assert op03["pcm_op03_bodyfree_leak_promotion_or_autorun_blocked"] is True
    assert expected_blocker in op03["pcm_op03_blocker_refs"]
    assert op03["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_SINGLE_LANE_CONFIRMATION_REF
    _assert_pcm_r3_no_downstream_execution(op03)
